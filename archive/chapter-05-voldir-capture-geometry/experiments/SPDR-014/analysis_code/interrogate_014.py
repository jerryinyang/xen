#!/usr/bin/env python3
"""SPDR-014 data-analyst interrogation — independent of screen_code.

Re-derives verdict-bearing magnitudes from raw emissions under
python/experiments/SPDR-014/results/. Writes analysis_code/interrogation_tables.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
OUT = Path(__file__).resolve().parent / "interrogation_tables.json"

DEADBAND = 5.0  # bps FLAT
MDE_CAP = 10.0  # design §8.1


def load() -> dict[str, pd.DataFrame | dict]:
    exp = pd.read_parquet(RES / "expectancy_by_cell.parquet")
    post = pd.read_parquet(RES / "post_event.parquet")
    events = pd.read_parquet(RES / "events.parquet")
    zones = pd.read_parquet(RES / "zones.parquet")
    money = pd.read_parquet(RES / "money_episodes.parquet")
    straddle = pd.read_parquet(RES / "straddle.parquet")
    h4 = pd.read_parquet(RES / "h4_coreport.parquet")
    controls = json.loads((RES / "controls.json").read_text())
    integrity = json.loads((RES / "integrity_selfcheck.json").read_text())
    pin = json.loads((RES / "014_residual_pin.json").read_text())
    golden = json.loads((RES / "golden_traces.json").read_text())
    return {
        "exp": exp,
        "post": post,
        "events": events,
        "zones": zones,
        "money": money,
        "straddle": straddle,
        "h4": h4,
        "controls": controls,
        "integrity": integrity,
        "pin": pin,
        "golden": golden,
    }


def mde_bps(r: pd.Series, n_dates: int) -> float:
    """Design §8.2: MDE residual ~ 2.8 * σ_r / sqrt(n_dates)."""
    if n_dates < 2 or r.isna().all():
        return float("nan")
    sigma = float(np.nanstd(r.values, ddof=1))
    if not np.isfinite(sigma) or sigma <= 0:
        return float("nan")
    return 2.8 * sigma / np.sqrt(n_dates)


def label_momo_mr(r_h: float, c: float = DEADBAND) -> str:
    if r_h > c:
        return "MOMO"
    if r_h < -c:
        return "MR"
    return "FLAT"


def recompute_from_post(post: pd.DataFrame) -> pd.DataFrame:
    """Recompute cell stats from post_event rows (decided side only for residual)."""
    p = post.copy()
    # Require decided side for residual estimands
    if "side" in p.columns:
        p = p[p["side"].notna() & (p["side"] != 0)]
    if "r_h" not in p.columns:
        raise RuntimeError("post_event missing r_h")
    p = p[p["r_h"].notna()]

    # event_date for n_dates
    ts_col = None
    for c in ("event_ts", "breach_entry_ts", "event_time", "ts", "decision_ts"):
        if c in p.columns:
            ts_col = c
            break
    if ts_col is not None:
        p["_date"] = pd.to_datetime(p[ts_col], utc=True).dt.floor("D")
    else:
        p["_date"] = np.arange(len(p))  # fallback: each row a date proxy

    group_cols = [c for c in ("symbol", "source", "z", "H", "event", "h", "band") if c in p.columns]
    rows = []
    for keys, g in p.groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        rec = dict(zip(group_cols, keys))
        r = g["r_h"].astype(float)
        n = len(r)
        n_dates = int(g["_date"].nunique())
        labels = r.map(label_momo_mr)
        rec.update(
            {
                "n_decided": n,
                "n_dates": n_dates,
                "mean_r_h": float(r.mean()) if n else float("nan"),
                "median_r_h": float(r.median()) if n else float("nan"),
                "std_r_h": float(r.std(ddof=1)) if n > 1 else float("nan"),
                "p_momo": float((labels == "MOMO").mean()) if n else float("nan"),
                "p_mr": float((labels == "MR").mean()) if n else float("nan"),
                "p_flat": float((labels == "FLAT").mean()) if n else float("nan"),
                "mde_bps": mde_bps(r, n_dates),
                "q05": float(r.quantile(0.05)) if n else float("nan"),
                "q95": float(r.quantile(0.95)) if n else float("nan"),
            }
        )
        rec["unpowered"] = bool(
            n < 80
            or n_dates < 30
            or (np.isfinite(rec["mde_bps"]) and rec["mde_bps"] > MDE_CAP)
            or not np.isfinite(rec["mde_bps"])
        )
        rows.append(rec)
    return pd.DataFrame(rows)


def event_rates(zones: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """p_event from zone origins vs events that fired."""
    zcols = [c for c in ("symbol", "source", "z", "H", "band") if c in zones.columns]
    # zones are origins; events may have event_id / event_type
    e = events.copy()
    event_col = "event" if "event" in e.columns else ("event_type" if "event_type" in e.columns else None)
    fired_col = None
    for c in ("event_flag", "event_1", "fired", "evented"):
        if c in e.columns:
            fired_col = c
            break

    # Prefer expectancy cell if available; else join
    if "event" not in zones.columns and event_col:
        # events has one row per zone×event definition
        gcols = [c for c in ("symbol", "source", "z", "H", "band", event_col) if c in e.columns]
        if fired_col is None:
            # if row exists only when fired, need zones count
            n_events = e.groupby(gcols).size().rename("n_events")
        else:
            n_events = e.groupby(gcols)[fired_col].sum().rename("n_events")
        n_origins = zones.groupby([c for c in zcols if c in zones.columns]).size().rename("n_origins")
        return pd.DataFrame({"note": ["event_rates deferred to expectancy"]})

    return pd.DataFrame()


def primary_slice(df: pd.DataFrame) -> pd.DataFrame:
    q = df.copy()
    if "source" in q.columns:
        q = q[q["source"] == "Z-VOL"]
    if "z" in q.columns:
        q = q[q["z"] == 1.5]
    if "H" in q.columns:
        q = q[q["H"] == 12]
    if "event" in q.columns:
        q = q[q["event"] == "E-TOUCH"]
    if "h" in q.columns:
        q = q[q["h"] == 12]
    if "band" in q.columns:
        q = q[q["band"] == "DESIGN"]
    return q


def summarise_medians(cell_df: pd.DataFrame, mask: pd.Series | None = None) -> dict:
    d = cell_df if mask is None else cell_df[mask]
    d = d[d["n_decided"] > 0] if "n_decided" in d.columns else d
    out = {"n_symbols": int(d["symbol"].nunique()) if "symbol" in d.columns else len(d)}
    for col in ("mean_r_h", "median_r_h", "p_momo", "p_mr", "p_flat", "p_event", "mde_bps", "n_decided"):
        if col in d.columns:
            s = pd.to_numeric(d[col], errors="coerce").dropna()
            out[f"med_{col}"] = float(s.median()) if len(s) else None
            out[f"mean_{col}"] = float(s.mean()) if len(s) else None
    if "mean_r_h" in d.columns:
        s = pd.to_numeric(d["mean_r_h"], errors="coerce").dropna()
        out["n_mean_pos"] = int((s > 0).sum())
        out["n_mean_neg"] = int((s < 0).sum())
        out["n_mean_total"] = int(len(s))
    if "p_momo" in d.columns and "p_mr" in d.columns:
        m = pd.to_numeric(d["p_momo"], errors="coerce")
        r = pd.to_numeric(d["p_mr"], errors="coerce")
        both = m.notna() & r.notna()
        out["frac_momo_gt_mr"] = float((m[both] > r[both]).mean()) if both.any() else None
        out["frac_mr_gt_momo"] = float((r[both] > m[both]).mean()) if both.any() else None
        out["med_p_momo_minus_p_mr"] = float((m[both] - r[both]).median()) if both.any() else None
    if "unpowered" in d.columns:
        out["n_unpowered"] = int(d["unpowered"].sum())
        out["n_powered"] = int((~d["unpowered"]).sum())
    return out


def controls_summary(controls: dict) -> dict:
    rows_mr = []
    rows_ts = []
    rows_uc = []
    rows_tw = []
    by = controls.get("by_symbol", controls)
    for sym, blk in by.items():
        if not isinstance(blk, dict):
            continue
        mr = blk.get("matched_random") or {}
        ts = blk.get("time_shuffle") or {}
        uc = blk.get("uncond") or {}
        tw = blk.get("tripwire") or {}
        if mr:
            rows_mr.append(
                {
                    "symbol": sym,
                    "live_mean_r_h": mr.get("live_mean_r_h"),
                    "null_mean_mean": mr.get("null_mean_mean"),
                    "live_percentile": mr.get("live_percentile"),
                    "delta": (None if mr.get("live_mean_r_h") is None or mr.get("null_mean_mean") is None
                              else mr["live_mean_r_h"] - mr["null_mean_mean"]),
                }
            )
        if ts:
            rows_ts.append(
                {
                    "symbol": sym,
                    "live_mean_r_h": ts.get("live_mean_r_h"),
                    "null_mean_mean": ts.get("null_mean_mean"),
                    "live_percentile": ts.get("live_percentile"),
                    "collapse": ts.get("collapse"),
                }
            )
        if uc:
            rows_uc.append(
                {
                    "symbol": sym,
                    "delta_mean_r_h": uc.get("delta_mean_r_h"),
                    "delta_p_event": uc.get("delta_p_event"),
                    "live_mean": (uc.get("live") or {}).get("mean_r_h"),
                    "ctrl_mean": (uc.get("control_arm") or {}).get("mean_r_h"),
                    "live_p_event": (uc.get("live") or {}).get("p_event"),
                }
            )
        if tw:
            rows_tw.append(
                {
                    "symbol": sym,
                    "live_mean_partial_net": tw.get("live_mean_partial_net"),
                    "null_p95": tw.get("null_p95"),
                    "positive_edge_claimed": tw.get("positive_edge_claimed"),
                    "survives_above_p95": tw.get("survives_above_p95"),
                    "integrity_concern": tw.get("integrity_concern"),
                }
            )
    def med(rows, key):
        s = pd.Series([r[key] for r in rows if r.get(key) is not None and np.isfinite(r[key])])
        return float(s.median()) if len(s) else None

    return {
        "matched_random": {
            "n": len(rows_mr),
            "med_live": med(rows_mr, "live_mean_r_h"),
            "med_null": med(rows_mr, "null_mean_mean"),
            "med_delta": med(rows_mr, "delta"),
            "med_live_pct": med(rows_mr, "live_percentile"),
            "per_symbol": rows_mr,
        },
        "time_shuffle": {
            "n": len(rows_ts),
            "med_live_pct": med(rows_ts, "live_percentile"),
            "med_live": med(rows_ts, "live_mean_r_h"),
            "med_null": med(rows_ts, "null_mean_mean"),
            "per_symbol": rows_ts,
        },
        "uncond": {
            "n": len(rows_uc),
            "med_delta_mean_r_h": med(rows_uc, "delta_mean_r_h"),
            "med_delta_p_event": med(rows_uc, "delta_p_event"),
            "per_symbol": rows_uc,
        },
        "tripwire": {
            "n": len(rows_tw),
            "n_positive_claimed": sum(1 for r in rows_tw if r.get("positive_edge_claimed")),
            "n_survives_p95": sum(1 for r in rows_tw if r.get("survives_above_p95")),
            "n_integrity_concern": sum(1 for r in rows_tw if r.get("integrity_concern")),
            "per_symbol": rows_tw,
        },
    }


def money_summary(money: pd.DataFrame, exp: pd.DataFrame) -> dict:
    out = {}
    # Prefer money_episodes if has partial_net
    m = money.copy()
    if len(m) and "partial_net" in m.columns:
        gcols = [c for c in ("symbol", "source", "policy", "band", "z", "H", "h", "event") if c in m.columns]
        agg = m.groupby(gcols, dropna=False)["partial_net"].agg(["mean", "median", "count"]).reset_index()
        out["from_episodes"] = True
        out["n_episode_rows"] = len(m)
        # filter DESIGN Z-VOL z=1.5 H=12 h=12 E-TOUCH
        q = agg
        for col, val in (("band", "DESIGN"), ("source", "Z-VOL"), ("z", 1.5), ("H", 12), ("h", 12), ("event", "E-TOUCH")):
            if col in q.columns:
                q = q[q[col] == val]
        by_pol = {}
        if "policy" in q.columns:
            for pol, g in q.groupby("policy"):
                s = g["mean"]
                by_pol[str(pol)] = {
                    "med_mean_partial_net": float(s.median()),
                    "n_symbols": int(len(g)),
                    "n_mean_pos": int((s > 0).sum()),
                    "max_mean": float(s.max()),
                    "min_mean": float(s.min()),
                    "per_symbol": g[["symbol", "mean", "median", "count"]].to_dict(orient="records")
                    if "symbol" in g.columns else [],
                }
        out["policies"] = by_pol
    # also from expectancy cells
    if "mean_partial_net" in exp.columns or "partial_net_mean" in exp.columns:
        col = "mean_partial_net" if "mean_partial_net" in exp.columns else "partial_net_mean"
        e = exp.copy()
        for c, v in (("band", "DESIGN"), ("source", "Z-VOL"), ("z", 1.5), ("H", 12), ("h", 12), ("event", "E-TOUCH")):
            if c in e.columns:
                e = e[e[c] == v]
        pol_col = "policy" if "policy" in e.columns else None
        if pol_col:
            e = e[e[pol_col].isin(["P-MOMO", "P-MR"])]
            by_pol = {}
            for pol, g in e.groupby(pol_col):
                s = pd.to_numeric(g[col], errors="coerce").dropna()
                by_pol[str(pol)] = {
                    "med_mean_partial_net": float(s.median()) if len(s) else None,
                    "n_symbols": int(g["symbol"].nunique()) if "symbol" in g.columns else len(s),
                    "n_mean_pos": int((s > 0).sum()),
                }
            out["from_expectancy"] = by_pol
    return out


def main() -> None:
    data = load()
    exp = data["exp"]
    post = data["post"]
    zones = data["zones"]
    events = data["events"]
    money = data["money"]
    straddle = data["straddle"]
    h4 = data["h4"]

    schema = {
        "expectancy_cols": list(exp.columns),
        "post_cols": list(post.columns),
        "zones_cols": list(zones.columns),
        "events_cols": list(events.columns),
        "money_cols": list(money.columns),
        "straddle_cols": list(straddle.columns),
        "h4_cols": list(h4.columns),
        "n_exp": len(exp),
        "n_post": len(post),
        "n_zones": len(zones),
        "n_events": len(events),
        "n_money": len(money),
    }

    # Recompute from post_event
    recomputed = recompute_from_post(post)

    # Also use expectancy if it has the aggregates
    exp_work = exp.copy()
    # normalise column names
    rename = {}
    for a, b in (
        ("event_type", "event"),
        ("band_name", "band"),
        ("mean_rh", "mean_r_h"),
        ("median_rh", "median_r_h"),
    ):
        if a in exp_work.columns and b not in exp_work.columns:
            rename[a] = b
    exp_work = exp_work.rename(columns=rename)

    results: dict = {
        "schema": schema,
        "integrity": data["integrity"],
        "golden_all_pass": data["golden"].get("all_pass"),
        "pin_residual_status": data["pin"].get("residual_status"),
        "pin_016_start_allowed": data["pin"].get("016_start_allowed"),
        "pin_n_powered_momo": data["pin"].get("n_powered_momo"),
        "pin_n_powered_mr": data["pin"].get("n_powered_mr"),
        "pin_notes": data["pin"].get("notes"),
    }

    # Primary cell from recompute
    for band in ("DESIGN", "CONFIRM"):
        for H in (4, 12, 24):
            for event in ("E-TOUCH", "E-CLOSE", "E-HORIZON"):
                for source in ("Z-VOL", "Z-MAG"):
                    q = recomputed[
                        (recomputed["source"] == source)
                        & (recomputed["z"] == 1.5)
                        & (recomputed["H"] == H)
                        & (recomputed["event"] == event)
                        & (recomputed["h"] == 12)
                        & (recomputed["band"] == band)
                    ]
                    key = f"recomp_{band}_{source}_z1.5_H{H}_{event}_h12"
                    results[key] = {
                        "summary": summarise_medians(q),
                        "per_symbol": q.sort_values("symbol").to_dict(orient="records"),
                    }

    # p_event from expectancy if present
    if "p_event" in exp_work.columns:
        for band in ("DESIGN", "CONFIRM"):
            q = exp_work[
                (exp_work.get("source", pd.Series(dtype=str)) == "Z-VOL")
                if "source" in exp_work.columns
                else True
            ]
            # safer:
            q = exp_work.copy()
            if "source" in q.columns:
                q = q[q["source"] == "Z-VOL"]
            if "z" in q.columns:
                q = q[q["z"] == 1.5]
            if "H" in q.columns:
                q = q[q["H"] == 12]
            if "event" in q.columns:
                q = q[q["event"] == "E-TOUCH"]
            if "h" in q.columns:
                q = q[q["h"] == 12]
            if "band" in q.columns:
                q = q[q["band"] == band]
            # drop money policies if present
            if "policy" in q.columns:
                q = q[q["policy"].isin(["P-NONE", "NONE", None]) | q["policy"].isna()]
            results[f"expectancy_p_event_{band}"] = summarise_medians(q)
            results[f"expectancy_primary_{band}_per_symbol"] = (
                q.sort_values("symbol")[
                    [c for c in ("symbol", "mean_r_h", "median_r_h", "p_momo", "p_mr", "p_event",
                                 "n_decided", "n_dates", "mde_bps", "ci_low", "ci_high",
                                 "unpowered", "band_label_raw", "label")
                     if c in q.columns]
                ].to_dict(orient="records")
            )

    # Cross-check recompute vs expectancy for DESIGN primary
    key = "recomp_DESIGN_Z-VOL_z1.5_H12_E-TOUCH_h12"
    if key in results and f"expectancy_primary_DESIGN_per_symbol" in results:
        re = {r["symbol"]: r for r in results[key]["per_symbol"]}
        cross = []
        for row in results["expectancy_primary_DESIGN_per_symbol"]:
            sym = row.get("symbol")
            rr = re.get(sym, {})
            if not rr:
                continue
            cross.append(
                {
                    "symbol": sym,
                    "mean_r_h_post": rr.get("mean_r_h"),
                    "mean_r_h_exp": row.get("mean_r_h"),
                    "delta_mean": (None if rr.get("mean_r_h") is None or row.get("mean_r_h") is None
                                  else rr["mean_r_h"] - row["mean_r_h"]),
                    "p_momo_post": rr.get("p_momo"),
                    "p_momo_exp": row.get("p_momo"),
                    "n_post": rr.get("n_decided"),
                    "n_exp": row.get("n_decided"),
                }
            )
        results["crosscheck_post_vs_exp"] = cross

    results["controls"] = controls_summary(data["controls"])
    results["money"] = money_summary(money, exp_work)

    # Straddle
    if len(straddle):
        s = straddle.copy()
        if "band" in s.columns:
            s = s[s["band"] == "DESIGN"]
        col = "mean_partial_net" if "mean_partial_net" in s.columns else (
            "partial_net" if "partial_net" in s.columns else None
        )
        if col and "symbol" in s.columns:
            # per symbol mean
            if col == "partial_net":
                g = s.groupby("symbol")[col].mean()
            else:
                g = s.set_index("symbol")[col] if s["symbol"].is_unique else s.groupby("symbol")[col].mean()
            results["straddle_design"] = {
                "med_mean_partial_net": float(pd.to_numeric(g, errors="coerce").median()),
                "n": int(len(g)),
                "per_symbol": {str(k): float(v) for k, v in g.items() if pd.notna(v)},
            }

    # H4
    if len(h4):
        results["h4_n_rows"] = len(h4)
        results["h4_sample"] = h4.head(5).to_dict(orient="records")
        if "mean_r_h" in h4.columns and "symbol" in h4.columns:
            results["h4_per_symbol"] = h4[["symbol"] + [c for c in ("mean_r_h", "p_momo", "p_mr", "n_decided", "p_event") if c in h4.columns]].to_dict(orient="records")

    # Power audit on primary residual cells (DESIGN, z=1.5, E-TOUCH, h=12, both sources all H)
    power_rows = recomputed[
        (recomputed["z"] == 1.5)
        & (recomputed["event"] == "E-TOUCH")
        & (recomputed["h"] == 12)
        & (recomputed["band"] == "DESIGN")
    ]
    results["power_audit_primary"] = {
        "n_cells": int(len(power_rows)),
        "n_unpowered": int(power_rows["unpowered"].sum()),
        "n_powered": int((~power_rows["unpowered"]).sum()),
        "mde_min": float(power_rows["mde_bps"].min(skipna=True)),
        "mde_med": float(power_rows["mde_bps"].median(skipna=True)),
        "mde_max": float(power_rows["mde_bps"].max(skipna=True)),
        "n_n_decided_ge_80": int((power_rows["n_decided"] >= 80).sum()),
        "n_n_dates_ge_30": int((power_rows["n_dates"] >= 30).sum()),
    }

    # Pin primary cells power from pin file
    pin_cells = data["pin"].get("primary_cells") or []
    results["pin_power"] = {
        "n_primary_cells": len(pin_cells),
        "n_unpowered": sum(1 for c in pin_cells if c.get("unpowered")),
        "n_powered": sum(1 for c in pin_cells if not c.get("unpowered")),
        "n_with_label": sum(1 for c in pin_cells if c.get("label")),
        "labels": sorted({c.get("label") for c in pin_cells if c.get("label")}),
        "n_rate_momo": sum(1 for c in pin_cells if c.get("label") == "MOMO_RATE"),
        "n_rate_mr": sum(1 for c in pin_cells if c.get("label") == "MR_RATE"),
    }

    # Causality construction checks from golden + integrity
    results["causality"] = {
        "train_fence": data["integrity"]["checks"].get("train_fence_asserted"),
        "G1_band_match": data["golden"].get("G1", {}).get("band_match"),
        "G2_entry_next_open": data["golden"].get("G2", {}).get("entry_next_open"),
        "G2_r_h_match": data["golden"].get("G2", {}).get("match"),
        "G4_cost_match": data["golden"].get("G4", {}).get("match"),
        "no_signed_product": data["integrity"]["checks"].get("no_signed_product"),
        "shock_not_regime": data["integrity"]["checks"].get("shock_not_regime"),
        "both_momo_mr": data["integrity"]["checks"].get("both_momo_mr_emitted"),
        "tripwire_hard_fail": data["integrity"]["checks"].get("tripwire_hard_fail"),
        "tripwire_positive_survivors": data["integrity"]["checks"].get("tripwire_positive_survivors"),
    }

    # CONFIRM flip for primary
    d_des = results.get("recomp_DESIGN_Z-VOL_z1.5_H12_E-TOUCH_h12", {}).get("summary", {})
    d_con = results.get("recomp_CONFIRM_Z-VOL_z1.5_H12_E-TOUCH_h12", {}).get("summary", {})
    results["confirm_flip"] = {
        "design_med_mean_r_h": d_des.get("med_mean_r_h"),
        "confirm_med_mean_r_h": d_con.get("med_mean_r_h"),
        "design_med_p_momo": d_des.get("med_p_momo"),
        "confirm_med_p_momo": d_con.get("med_p_momo"),
        "design_med_p_mr": d_des.get("med_p_mr"),
        "confirm_med_p_mr": d_con.get("med_p_mr"),
        "sign_flip": (
            d_des.get("med_mean_r_h") is not None
            and d_con.get("med_mean_r_h") is not None
            and d_des["med_mean_r_h"] * d_con["med_mean_r_h"] < 0
        ),
    }

    # Event definition disagreement
    results["event_def_compare_DESIGN"] = {
        ev: results.get(f"recomp_DESIGN_Z-VOL_z1.5_H12_{ev}_h12", {}).get("summary", {})
        for ev in ("E-TOUCH", "E-CLOSE", "E-HORIZON")
    }

    # Z-MAG sparsity
    zm = results.get("recomp_DESIGN_Z-MAG_z1.5_H12_E-TOUCH_h12", {}).get("summary", {})
    zv = results.get("recomp_DESIGN_Z-VOL_z1.5_H12_E-TOUCH_h12", {}).get("summary", {})
    results["zmag_vs_zvol"] = {"zmag": zm, "zvol": zv}

    # Per-symbol primary table (compact for analysis.md)
    prim = recomputed[
        (recomputed["source"] == "Z-VOL")
        & (recomputed["z"] == 1.5)
        & (recomputed["H"] == 12)
        & (recomputed["event"] == "E-TOUCH")
        & (recomputed["h"] == 12)
        & (recomputed["band"] == "DESIGN")
    ].sort_values("symbol")
    results["primary_table_design"] = prim.to_dict(orient="records")

    prim_c = recomputed[
        (recomputed["source"] == "Z-VOL")
        & (recomputed["z"] == 1.5)
        & (recomputed["H"] == 12)
        & (recomputed["event"] == "E-TOUCH")
        & (recomputed["h"] == 12)
        & (recomputed["band"] == "CONFIRM")
    ].sort_values("symbol")
    results["primary_table_confirm"] = prim_c.to_dict(orient="records")

    # Full primary cells all H for p_momo/p_mr tables
    for band in ("DESIGN", "CONFIRM"):
        for H in (4, 12, 24):
            q = recomputed[
                (recomputed["source"] == "Z-VOL")
                & (recomputed["z"] == 1.5)
                & (recomputed["H"] == H)
                & (recomputed["event"] == "E-TOUCH")
                & (recomputed["h"] == 12)
                & (recomputed["band"] == band)
            ].sort_values("symbol")
            results[f"table_{band}_H{H}"] = q[
                ["symbol", "n_decided", "n_dates", "mean_r_h", "median_r_h", "p_momo", "p_mr", "p_flat", "mde_bps", "unpowered"]
            ].to_dict(orient="records")

    # JSON-safe
    def sanitize(obj):
        if isinstance(obj, dict):
            return {str(k): sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [sanitize(v) for v in obj]
        if isinstance(obj, (np.floating, float)):
            if not np.isfinite(obj):
                return None
            return float(obj)
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        if obj is pd.NA:
            return None
        if isinstance(obj, (pd.Timestamp,)):
            return str(obj)
        return obj

    OUT.write_text(json.dumps(sanitize(results), indent=2, default=str))
    print(f"Wrote {OUT}")
    print("schema post_cols:", schema["post_cols"])
    print("schema exp_cols:", schema["expectancy_cols"][:40])
    print("primary DESIGN summary:", results.get("recomp_DESIGN_Z-VOL_z1.5_H12_E-TOUCH_h12", {}).get("summary"))
    print("confirm flip:", results.get("confirm_flip"))
    print("controls MR med_delta:", results["controls"]["matched_random"].get("med_delta"))
    print("power audit:", results["power_audit_primary"])
    print("money:", results.get("money"))


if __name__ == "__main__":
    main()
