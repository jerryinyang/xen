#!/usr/bin/env python3
"""Stdlib-only interrogation of residual_pin + controls + integrity (JSON).

Also attempts parquet re-derivation if pandas/pyarrow available.
Writes interrogation_tables.json next to this script.
"""
from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
OUT = Path(__file__).resolve().parent / "interrogation_tables.json"


def med(xs):
    xs = [x for x in xs if x is not None and isinstance(x, (int, float)) and math.isfinite(x)]
    if not xs:
        return None
    return float(statistics.median(xs))


def mean(xs):
    xs = [x for x in xs if x is not None and isinstance(x, (int, float)) and math.isfinite(x)]
    if not xs:
        return None
    return float(statistics.mean(xs))


def main():
    pin = json.loads((RES / "014_residual_pin.json").read_text())
    controls = json.loads((RES / "controls.json").read_text())
    integrity = json.loads((RES / "integrity_selfcheck.json").read_text())
    golden = json.loads((RES / "golden_traces.json").read_text())

    cells = pin["primary_cells"]

    # Filter helpers
    def filt(source=None, H=None, n_min=1):
        out = []
        for c in cells:
            if source and c.get("source") != source:
                continue
            if H is not None and c.get("H") != H:
                continue
            if (c.get("n_decided") or 0) < n_min:
                continue
            if c.get("mean_r_h") is None:
                continue
            out.append(c)
        return out

    tables = {}
    for source in ("Z-VOL", "Z-MAG"):
        for H in (4, 12, 24):
            rows = filt(source=source, H=H, n_min=1)
            means = [c["mean_r_h"] for c in rows]
            deltas = [c["mean_r_h_delta"] for c in rows]
            pmo = [c["p_momo"] for c in rows]
            pmr = [c["p_mr"] for c in rows]
            mdes = [c["mde_bps"] for c in rows]
            unp = sum(1 for c in rows if c.get("unpowered"))
            momo_gt = sum(1 for c in rows if c["p_momo"] is not None and c["p_mr"] is not None and c["p_momo"] > c["p_mr"])
            mr_gt = sum(1 for c in rows if c["p_momo"] is not None and c["p_mr"] is not None and c["p_mr"] > c["p_momo"])
            tables[f"{source}_H{H}"] = {
                "n_symbols_with_data": len(rows),
                "med_mean_r_h": med(means),
                "med_mean_r_h_delta": med(deltas),
                "med_p_momo": med(pmo),
                "med_p_mr": med(pmr),
                "med_mde_bps": med(mdes),
                "min_mde_bps": min((m for m in mdes if m is not None and math.isfinite(m)), default=None),
                "max_mde_bps": max((m for m in mdes if m is not None and math.isfinite(m)), default=None),
                "n_unpowered": unp,
                "n_powered": len(rows) - unp,
                "n_mean_pos": sum(1 for m in means if m is not None and m > 0),
                "n_mean_neg": sum(1 for m in means if m is not None and m < 0),
                "frac_momo_gt_mr": momo_gt / len(rows) if rows else None,
                "frac_mr_gt_momo": mr_gt / len(rows) if rows else None,
                "med_p_momo_minus_p_mr": med([a - b for a, b in zip(pmo, pmr) if a is not None and b is not None]),
                "per_symbol": [
                    {
                        "symbol": c["symbol"],
                        "mean_r_h": c["mean_r_h"],
                        "median_r_h": c.get("median_r_h"),
                        "mean_r_h_delta": c.get("mean_r_h_delta"),
                        "p_momo": c["p_momo"],
                        "p_mr": c["p_mr"],
                        "n_decided": c["n_decided"],
                        "n_dates": c.get("n_dates"),
                        "mde_bps": c.get("mde_bps"),
                        "ci_low": c.get("ci_low"),
                        "ci_high": c.get("ci_high"),
                        "unpowered": c.get("unpowered"),
                        "label": c.get("label"),
                    }
                    for c in sorted(rows, key=lambda x: x["symbol"])
                ],
            }

    # Primary H=12 Z-VOL full table including zeros
    primary_all = [c for c in cells if c["source"] == "Z-VOL" and c["H"] == 12]
    primary_data = [c for c in primary_all if (c.get("n_decided") or 0) > 0 and c.get("mean_r_h") is not None]

    # Controls
    by = controls.get("by_symbol", {})
    mr_rows, ts_rows, uc_rows, tw_rows = [], [], [], []
    for sym, blk in by.items():
        if not isinstance(blk, dict):
            continue
        mr = blk.get("matched_random") or {}
        ts = blk.get("time_shuffle") or {}
        uc = blk.get("uncond") or {}
        tw = blk.get("tripwire") or {}
        live = mr.get("live_mean_r_h")
        null = mr.get("null_mean_mean")
        if live is not None and null is not None and math.isfinite(live) and math.isfinite(null):
            mr_rows.append({
                "symbol": sym, "live": live, "null": null, "delta": live - null,
                "pct": mr.get("live_percentile"),
            })
        live_ts = ts.get("live_mean_r_h")
        null_ts = ts.get("null_mean_mean")
        if live_ts is not None and null_ts is not None and math.isfinite(live_ts) and math.isfinite(null_ts):
            ts_rows.append({
                "symbol": sym, "live": live_ts, "null": null_ts,
                "pct": ts.get("live_percentile"), "collapse": ts.get("collapse"),
            })
        d = uc.get("delta_mean_r_h")
        if d is not None and isinstance(d, (int, float)) and math.isfinite(d):
            uc_rows.append({
                "symbol": sym, "delta_mean_r_h": d,
                "delta_p_event": uc.get("delta_p_event"),
                "live_p_event": (uc.get("live") or {}).get("p_event"),
                "live_mean": (uc.get("live") or {}).get("mean_r_h"),
            })
        pn = tw.get("live_mean_partial_net")
        if pn is not None and isinstance(pn, (int, float)) and math.isfinite(pn):
            tw_rows.append({
                "symbol": sym, "live_mean_partial_net": pn,
                "null_p95": tw.get("null_p95"),
                "positive_edge_claimed": tw.get("positive_edge_claimed"),
                "survives_above_p95": tw.get("survives_above_p95"),
                "integrity_concern": tw.get("integrity_concern"),
            })

    # Power audit
    all_primary = [c for c in cells if c.get("mean_r_h") is not None or (c.get("n_decided") or 0) == 0]
    n_all = len(cells)
    n_unp = sum(1 for c in cells if c.get("unpowered"))
    mdes_all = [c["mde_bps"] for c in cells if isinstance(c.get("mde_bps"), (int, float)) and math.isfinite(c["mde_bps"])]

    # Labels
    labels = [c.get("label") for c in cells if c.get("label")]
    n_momo_rate = sum(1 for L in labels if L == "MOMO_RATE")
    n_mr_rate = sum(1 for L in labels if L == "MR_RATE")
    n_momo = sum(1 for L in labels if L == "MOMO")
    n_mr = sum(1 for L in labels if L == "MR")

    # Parquet attempt
    parquet_block = {"available": False}
    try:
        import pandas as pd  # type: ignore
        exp = pd.read_parquet(RES / "expectancy_by_cell.parquet")
        post = pd.read_parquet(RES / "post_event.parquet")
        money = pd.read_parquet(RES / "money_episodes.parquet")
        straddle = pd.read_parquet(RES / "straddle.parquet")
        h4 = pd.read_parquet(RES / "h4_coreport.parquet")
        parquet_block = {
            "available": True,
            "exp_cols": list(exp.columns),
            "post_cols": list(post.columns),
            "n_exp": len(exp),
            "n_post": len(post),
            "n_money": len(money),
            "n_straddle": len(straddle),
            "n_h4": len(h4),
        }

        def cell_summ(df, band, source, z, H, event, h, policy=None):
            q = df.copy()
            for col, val in (("band", band), ("source", source), ("z", z), ("H", H),
                             ("event", event), ("h", h)):
                if col in q.columns:
                    q = q[q[col] == val]
            if policy is not None and "policy" in q.columns:
                q = q[q["policy"] == policy]
            elif "policy" in q.columns:
                q = q[q["policy"].isin(["P-NONE", "NONE"]) | q["policy"].isna()]
            q = q[q["n_decided"] > 0] if "n_decided" in q.columns else q
            out = {"n": int(len(q))}
            for col in ("mean_r_h", "median_r_h", "p_momo", "p_mr", "p_flat", "p_event",
                        "mde_bps", "mean_partial_net", "n_decided"):
                if col in q.columns:
                    s = pd.to_numeric(q[col], errors="coerce").dropna()
                    out[f"med_{col}"] = float(s.median()) if len(s) else None
            if "mean_r_h" in q.columns:
                s = pd.to_numeric(q["mean_r_h"], errors="coerce").dropna()
                out["n_mean_pos"] = int((s > 0).sum())
                out["n_mean_neg"] = int((s < 0).sum())
            if "p_momo" in q.columns and "p_mr" in q.columns:
                m = pd.to_numeric(q["p_momo"], errors="coerce")
                r = pd.to_numeric(q["p_mr"], errors="coerce")
                both = m.notna() & r.notna()
                out["frac_momo_gt_mr"] = float((m[both] > r[both]).mean()) if both.any() else None
                out["med_pdiff"] = float((m[both] - r[both]).median()) if both.any() else None
            # per-symbol
            cols = [c for c in ("symbol", "mean_r_h", "median_r_h", "p_momo", "p_mr", "p_flat",
                                "p_event", "n_decided", "n_dates", "mde_bps", "ci_low", "ci_high",
                                "mean_partial_net", "median_partial_net", "band_label_raw", "unpowered")
                    if c in q.columns]
            out["per_symbol"] = q[cols].sort_values("symbol").to_dict(orient="records") if cols else []
            return out

        for band in ("DESIGN", "CONFIRM"):
            for event in ("E-TOUCH", "E-CLOSE", "E-HORIZON"):
                for H in (4, 12, 24):
                    key = f"exp_{band}_ZVOL_H{H}_{event}"
                    parquet_block[key] = cell_summ(exp, band, "Z-VOL", 1.5, H, event, 12, "P-NONE")
                parquet_block[f"exp_{band}_ZMAG_H12_ETOUCH"] = cell_summ(
                    exp, band, "Z-MAG", 1.5, 12, "E-TOUCH", 12, "P-NONE"
                )

        # Money
        money_out = {}
        for pol in ("P-MOMO", "P-MR"):
            q = exp.copy()
            for col, val in (("band", "DESIGN"), ("source", "Z-VOL"), ("z", 1.5), ("H", 12),
                             ("event", "E-TOUCH"), ("h", 12), ("policy", pol)):
                if col in q.columns:
                    q = q[q[col] == val]
            col = "mean_partial_net" if "mean_partial_net" in q.columns else None
            if col:
                s = pd.to_numeric(q[col], errors="coerce").dropna()
                money_out[pol] = {
                    "med_mean_partial_net": float(s.median()) if len(s) else None,
                    "n_symbols": int(len(s)),
                    "n_mean_pos": int((s > 0).sum()),
                    "max_mean": float(s.max()) if len(s) else None,
                    "min_mean": float(s.min()) if len(s) else None,
                    "per_symbol": q[["symbol", col] + (["median_partial_net"] if "median_partial_net" in q.columns else [])]
                    .sort_values("symbol").to_dict(orient="records") if "symbol" in q.columns else [],
                }
        parquet_block["money"] = money_out

        # Straddle
        if len(straddle) and "mean_partial_net" in straddle.columns:
            s = straddle
            if "band" in s.columns:
                s = s[s["band"] == "DESIGN"]
            if "source" in s.columns:
                s = s[s["source"] == "Z-VOL"]
            g = s.groupby("symbol")["mean_partial_net"].mean() if "symbol" in s.columns else s["mean_partial_net"]
            parquet_block["straddle_design_med"] = float(pd.to_numeric(g, errors="coerce").median())
            parquet_block["straddle_n"] = int(len(g))

        # Recompute from post_event for primary DESIGN
        if "r_h" in post.columns:
            p = post.copy()
            for col, val in (("band", "DESIGN"), ("source", "Z-VOL"), ("z", 1.5), ("H", 12),
                             ("event_type", "E-TOUCH"), ("h", 12)):
                # event may be event or event_type
                if col == "event_type":
                    if "event_type" in p.columns:
                        p = p[p["event_type"] == "E-TOUCH"]
                    elif "event" in p.columns and p["event"].dtype == object:
                        p = p[p["event"] == "E-TOUCH"]
                    continue
                if col in p.columns:
                    p = p[p[col] == val]
            if "policy" in p.columns:
                p = p[p["policy"].isin(["P-NONE", "NONE"]) | p["policy"].isna()]
            if "side" in p.columns:
                p = p[p["side"].notna() & (p["side"] != 0)]
            p = p[p["r_h"].notna()]
            # group by symbol
            recomp = []
            for sym, g in p.groupby("symbol"):
                r = g["r_h"].astype(float)
                n = len(r)
                labels = r.apply(lambda x: "MOMO" if x > 5 else ("MR" if x < -5 else "FLAT"))
                recomp.append({
                    "symbol": sym,
                    "n_decided": n,
                    "mean_r_h": float(r.mean()),
                    "median_r_h": float(r.median()),
                    "p_momo": float((labels == "MOMO").mean()),
                    "p_mr": float((labels == "MR").mean()),
                    "p_flat": float((labels == "FLAT").mean()),
                    "std_r_h": float(r.std(ddof=1)) if n > 1 else None,
                })
            parquet_block["post_recomp_DESIGN_primary"] = {
                "med_mean_r_h": med([r["mean_r_h"] for r in recomp]),
                "med_p_momo": med([r["p_momo"] for r in recomp]),
                "med_p_mr": med([r["p_mr"] for r in recomp]),
                "n_symbols": len(recomp),
                "per_symbol": sorted(recomp, key=lambda x: x["symbol"]),
            }

            # CONFIRM recompute
            p2 = post.copy()
            for col, val in (("band", "CONFIRM"), ("source", "Z-VOL"), ("z", 1.5), ("H", 12), ("h", 12)):
                if col in p2.columns:
                    p2 = p2[p2[col] == val]
            if "event_type" in p2.columns:
                p2 = p2[p2["event_type"] == "E-TOUCH"]
            elif "event" in p2.columns and p2["event"].dtype == object:
                p2 = p2[p2["event"] == "E-TOUCH"]
            if "policy" in p2.columns:
                p2 = p2[p2["policy"].isin(["P-NONE", "NONE"]) | p2["policy"].isna()]
            if "side" in p2.columns:
                p2 = p2[p2["side"].notna() & (p2["side"] != 0)]
            p2 = p2[p2["r_h"].notna()]
            recomp2 = []
            for sym, g in p2.groupby("symbol"):
                r = g["r_h"].astype(float)
                labels = r.apply(lambda x: "MOMO" if x > 5 else ("MR" if x < -5 else "FLAT"))
                recomp2.append({
                    "symbol": sym,
                    "n_decided": len(r),
                    "mean_r_h": float(r.mean()),
                    "median_r_h": float(r.median()),
                    "p_momo": float((labels == "MOMO").mean()),
                    "p_mr": float((labels == "MR").mean()),
                })
            parquet_block["post_recomp_CONFIRM_primary"] = {
                "med_mean_r_h": med([r["mean_r_h"] for r in recomp2]),
                "med_p_momo": med([r["p_momo"] for r in recomp2]),
                "med_p_mr": med([r["p_mr"] for r in recomp2]),
                "n_symbols": len(recomp2),
                "n_mean_pos": sum(1 for r in recomp2 if r["mean_r_h"] > 0),
                "n_mean_neg": sum(1 for r in recomp2 if r["mean_r_h"] < 0),
                "per_symbol": sorted(recomp2, key=lambda x: x["symbol"]),
            }

            # E-CLOSE vs E-TOUCH DESIGN
            for et in ("E-CLOSE", "E-HORIZON"):
                pe = post.copy()
                for col, val in (("band", "DESIGN"), ("source", "Z-VOL"), ("z", 1.5), ("H", 12), ("h", 12)):
                    if col in pe.columns:
                        pe = pe[pe[col] == val]
                if "event_type" in pe.columns:
                    pe = pe[pe["event_type"] == et]
                elif "event" in pe.columns and pe["event"].dtype == object:
                    pe = pe[pe["event"] == et]
                if "side" in pe.columns:
                    pe = pe[pe["side"].notna() & (pe["side"] != 0)]
                pe = pe[pe["r_h"].notna()]
                rows_e = []
                for sym, g in pe.groupby("symbol"):
                    r = g["r_h"].astype(float)
                    labels = r.apply(lambda x: "MOMO" if x > 5 else ("MR" if x < -5 else "FLAT"))
                    rows_e.append({
                        "symbol": sym, "mean_r_h": float(r.mean()),
                        "p_momo": float((labels == "MOMO").mean()),
                        "p_mr": float((labels == "MR").mean()),
                        "n": len(r),
                    })
                parquet_block[f"post_recomp_DESIGN_{et}"] = {
                    "med_mean_r_h": med([r["mean_r_h"] for r in rows_e]),
                    "med_p_momo": med([r["p_momo"] for r in rows_e]),
                    "med_p_mr": med([r["p_mr"] for r in rows_e]),
                    "n_symbols": len(rows_e),
                }

        # H4
        if len(h4):
            h4d = h4[h4["band"] == "DESIGN"] if "band" in h4.columns else h4
            if "mean_r_h" in h4d.columns:
                parquet_block["h4_design"] = {
                    "med_mean_r_h": float(pd.to_numeric(h4d["mean_r_h"], errors="coerce").median()),
                    "per_symbol": h4d[[c for c in ("symbol", "mean_r_h", "p_momo", "p_mr", "n_decided", "p_event") if c in h4d.columns]]
                    .to_dict(orient="records"),
                }

    except Exception as e:
        parquet_block = {"available": False, "error": repr(e)}

    result = {
        "integrity": integrity,
        "golden_all_pass": golden.get("all_pass"),
        "causality": {
            "train_fence": integrity["checks"].get("train_fence_asserted"),
            "G1_band_match": golden.get("G1", {}).get("band_match"),
            "G2_entry_next_open": golden.get("G2", {}).get("entry_next_open"),
            "G2_match": golden.get("G2", {}).get("match"),
            "G4_match": golden.get("G4", {}).get("match"),
            "no_signed_product": integrity["checks"].get("no_signed_product"),
            "shock_not_regime": integrity["checks"].get("shock_not_regime"),
            "both_momo_mr": integrity["checks"].get("both_momo_mr_emitted"),
            "tripwire_hard_fail": integrity["checks"].get("tripwire_hard_fail"),
            "tripwire_positive_survivors": integrity["checks"].get("tripwire_positive_survivors"),
        },
        "pin": {
            "residual_status": pin.get("residual_status"),
            "016_start_allowed": pin.get("016_start_allowed"),
            "policy_for_016": pin.get("policy_for_016"),
            "n_powered_momo": pin.get("n_powered_momo"),
            "n_powered_mr": pin.get("n_powered_mr"),
            "n_rate_momo_suggestive": pin.get("n_rate_momo_suggestive"),
            "n_rate_mr_suggestive": pin.get("n_rate_mr_suggestive"),
            "notes": pin.get("notes"),
            "correction": pin.get("correction"),
        },
        "power_audit": {
            "n_primary_cells": n_all,
            "n_unpowered": n_unp,
            "n_powered": n_all - n_unp,
            "mde_min": min(mdes_all) if mdes_all else None,
            "mde_med": med(mdes_all),
            "mde_max": max(mdes_all) if mdes_all else None,
            "n_momo_rate_labels": n_momo_rate,
            "n_mr_rate_labels": n_mr_rate,
            "n_momo_residual_labels": n_momo,
            "n_mr_residual_labels": n_mr,
        },
        "tables_from_pin": tables,
        "primary_H12_ZVOL": tables.get("Z-VOL_H12"),
        "controls": {
            "matched_random": {
                "n": len(mr_rows),
                "med_live": med([r["live"] for r in mr_rows]),
                "med_null": med([r["null"] for r in mr_rows]),
                "med_delta": med([r["delta"] for r in mr_rows]),
                "med_pct": med([r["pct"] for r in mr_rows]),
                "n_delta_pos": sum(1 for r in mr_rows if r["delta"] > 0),
                "n_delta_neg": sum(1 for r in mr_rows if r["delta"] < 0),
                "per_symbol": sorted(mr_rows, key=lambda x: x["symbol"]),
            },
            "time_shuffle": {
                "n": len(ts_rows),
                "med_live": med([r["live"] for r in ts_rows]),
                "med_null": med([r["null"] for r in ts_rows]),
                "med_pct": med([r["pct"] for r in ts_rows]),
                "per_symbol": sorted(ts_rows, key=lambda x: x["symbol"]),
            },
            "uncond": {
                "n": len(uc_rows),
                "med_delta_mean_r_h": med([r["delta_mean_r_h"] for r in uc_rows]),
                "med_delta_p_event": med([r["delta_p_event"] for r in uc_rows if r.get("delta_p_event") is not None]),
                "med_live_p_event": med([r["live_p_event"] for r in uc_rows if r.get("live_p_event") is not None]),
                "per_symbol": sorted(uc_rows, key=lambda x: x["symbol"]),
            },
            "tripwire": {
                "n": len(tw_rows),
                "med_partial_net": med([r["live_mean_partial_net"] for r in tw_rows]),
                "n_positive_claimed": sum(1 for r in tw_rows if r.get("positive_edge_claimed")),
                "n_survives_p95": sum(1 for r in tw_rows if r.get("survives_above_p95")),
                "n_integrity_concern": sum(1 for r in tw_rows if r.get("integrity_concern")),
                "per_symbol": sorted(tw_rows, key=lambda x: x["symbol"]),
            },
        },
        "parquet": parquet_block,
    }

    def sanitize(obj):
        if isinstance(obj, dict):
            return {str(k): sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [sanitize(v) for v in obj]
        if isinstance(obj, float):
            if not math.isfinite(obj):
                return None
            return obj
        if isinstance(obj, (bool, int, str)) or obj is None:
            return obj
        return str(obj)

    OUT.write_text(json.dumps(sanitize(result), indent=2))
    print("Wrote", OUT)
    print("primary Z-VOL H12:", tables.get("Z-VOL_H12"))
    print("controls MR med_delta:", result["controls"]["matched_random"]["med_delta"])
    print("power:", result["power_audit"])
    print("parquet available:", parquet_block.get("available"))
    if parquet_block.get("available"):
        print("post DESIGN:", parquet_block.get("post_recomp_DESIGN_primary"))
        print("post CONFIRM:", parquet_block.get("post_recomp_CONFIRM_primary"))
        print("money:", parquet_block.get("money"))
        print("event compare E-CLOSE:", parquet_block.get("post_recomp_DESIGN_E-CLOSE"))


if __name__ == "__main__":
    main()
