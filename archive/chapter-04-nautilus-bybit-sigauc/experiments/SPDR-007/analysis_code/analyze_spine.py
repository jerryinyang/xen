#!/usr/bin/env python3
"""SPDR-007 stage-5 independent interrogation.

Recomputes integrity + R0–R5 magnitudes from raw emissions.
Does NOT import screen_code for any verdict-bearing number.
Uses xen.evaluation bootstrap helpers only.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from xen.estimand_validation import check_no_local_accounting
from xen.evaluation import block_bootstrap_ci, block_sensitivity

ROOT = Path(__file__).resolve().parents[4]  # .../Xen
EXP = Path(__file__).resolve().parents[1]
RESULTS = EXP / "results"
OUT = RESULTS / "analysis_recompute.json"

MAJORS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT"]
P65, P70 = 0.65, 0.70
Q65, Q70 = 1.0 - P65, 1.0 - P70  # 0.35, 0.30
DESIGN_END = pd.Timestamp("2023-03-01")
CONFIRM_END = pd.Timestamp("2023-12-18")  # TEST starts here
HOLDOUT = pd.Timestamp("2025-01-08")
GROSS_P0 = 1.0 / 3.0


def _hash_freeze_payload(obj: dict) -> str:
    payload = {k: v for k, v in obj.items() if k != "pin_sha256"}
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode()
    ).hexdigest()


def load() -> dict:
    des = pd.read_parquet(RESULTS / "spine_events_DESIGN.parquet")
    conf = pd.read_parquet(RESULTS / "spine_events_CONFIRM.parquet")
    ctrl = pd.read_parquet(RESULTS / "spine_control_DESIGN.parquet")
    freeze = json.loads((RESULTS / "protection_freeze.json").read_text())
    trip = json.loads((RESULTS / "tripwire.json").read_text())
    floor = json.loads((RESULTS / "floor_table.json").read_text())
    layers = json.loads((RESULTS / "layers.json").read_text())
    diag = pd.read_parquet(RESULTS / "event_diagnostics_DESIGN.parquet")
    uni_d = pd.read_parquet(RESULTS / "universe_membership_DESIGN.parquet")
    uni_c = pd.read_parquet(RESULTS / "universe_membership_CONFIRM.parquet")
    for df in (des, conf, ctrl):
        for c in ("entry_ts", "anchor_ts", "session_end", "day"):
            if c in df.columns:
                df[c] = pd.to_datetime(df[c])
    return dict(
        des=des,
        conf=conf,
        ctrl=ctrl,
        freeze=freeze,
        trip=trip,
        floor=floor,
        layers=layers,
        diag=diag,
        uni_d=uni_d,
        uni_c=uni_c,
    )


# --------------------------------------------------------------------------- #
# Integrity
# --------------------------------------------------------------------------- #
def integrity(data: dict) -> dict:
    des, conf, ctrl, freeze = data["des"], data["conf"], data["ctrl"], data["freeze"]
    trip, layers = data["trip"], data["layers"]

    acc_screen = check_no_local_accounting(str(EXP / "screen_code"))
    acc_analysis = check_no_local_accounting(str(EXP / "analysis_code"))
    acc_sigbar = check_no_local_accounting(str(ROOT / "python/src/xen/sigbar"))

    freeze_pin_ok = freeze.get("pin_sha256") == _hash_freeze_payload(freeze)
    layers_pin_match = layers.get("protection_freeze_pin") == freeze.get("pin_sha256")

    # recompute DESIGN quantiles vs freeze
    mfe = des["mfe_norm"].to_numpy()
    q_p65 = float(np.quantile(mfe, Q65))
    q_p70 = float(np.quantile(mfe, Q70))
    freeze_q_match = (
        abs(q_p65 - freeze["pooled"]["p65"]["protection_ibw"]) < 1e-12
        and abs(q_p70 - freeze["pooled"]["p70"]["protection_ibw"]) < 1e-9
    )

    # band fences from raw timestamps
    des_max = des["entry_ts"].max()
    conf_min, conf_max = conf["entry_ts"].min(), conf["entry_ts"].max()
    band_ok = (
        des_max < DESIGN_END
        and conf_min >= DESIGN_END
        and conf_max < CONFIRM_END
    )
    holdout_ok = (
        des["entry_ts"].max() < HOLDOUT
        and conf["entry_ts"].max() < HOLDOUT
        and (not layers.get("holdout_touched", True))
        and (not layers.get("test_touched", True))
    )

    # tripwire
    bite = trip["positive_control_bite"]
    bite_ok = bool(bite.get("bite")) and float(bite.get("corr", 0)) > 0.5
    any_material = bool(trip.get("any_material_edge", False))
    survives = bool(trip.get("survives", True))
    trip_status = trip.get("status")
    # HARD fail only if material edge survives
    trip_hard_fail = any_material and survives
    trip_uninformative = (not any_material) and (not trip_hard_fail)

    # control horizon match
    sig_h = des["remaining_horizon"].median()
    ctrl_h = ctrl["remaining_horizon"].median()
    horizon_match = abs(float(sig_h) - float(ctrl_h)) <= 1.0

    # control disjoint: control entry must not share (symbol, day) event session?
    # D-1: donor session ≠ event session. We check remaining_horizon match + n≈30×.
    n_ratio = len(ctrl) / max(len(des), 1)

    # causal entry: entry_ts == qualify_end
    causal_entry = bool((des["entry_ts"] == des["qualify_end"]).all()) and bool(
        (conf["entry_ts"] == conf["qualify_end"]).all()
    )

    # population diagnostics
    diag = data["diag"]
    n_pokes = int(diag["n_pokes"].sum())
    n_accepts = int(diag["n_accepts"].sum())
    n_missing = int(diag["n_missing_entry"].sum())

    return {
        "check_no_local_accounting": {
            "screen_code": acc_screen,
            "analysis_code": acc_analysis,
            "xen_sigbar": acc_sigbar,
            "all_ok": acc_screen["ok"] and acc_analysis["ok"] and acc_sigbar["ok"],
        },
        "freeze": {
            "pin_ok": freeze_pin_ok,
            "layers_pin_match": layers_pin_match,
            "pin": freeze.get("pin_sha256"),
            "n_events": freeze.get("n_events"),
            "q_p65_freeze": freeze["pooled"]["p65"]["protection_ibw"],
            "q_p70_freeze": freeze["pooled"]["p70"]["protection_ibw"],
            "q_p65_recomputed": q_p65,
            "q_p70_recomputed": q_p70,
            "quantile_match": freeze_q_match,
            "band": freeze.get("band"),
        },
        "bands": {
            "design_entry_max": str(des_max),
            "confirm_entry_min": str(conf_min),
            "confirm_entry_max": str(conf_max),
            "design_before_confirm": band_ok,
            "holdout_untouched": holdout_ok,
            "test_touched_flag": layers.get("test_touched"),
            "holdout_touched_flag": layers.get("holdout_touched"),
        },
        "tripwire": {
            "status": trip_status,
            "any_material_edge": any_material,
            "survives": survives,
            "hard_fail": trip_hard_fail,
            "uninformative_under_D2": trip_uninformative,
            "bite_corr": float(bite.get("corr")),
            "bite_n": int(bite.get("n")),
            "bite_ok": bite_ok,
            "per_read_material": {
                k: v.get("material_edge") for k, v in trip.get("per_read", {}).items()
            },
            "per_read_collapse": {
                k: v.get("collapse_fraction") for k, v in trip.get("per_read", {}).items()
            },
        },
        "horizon_match": {
            "signal_median_min": float(sig_h),
            "control_median_min": float(ctrl_h),
            "match": horizon_match,
            "control_n": len(ctrl),
            "signal_n": len(des),
            "n_ratio": n_ratio,
        },
        "causal_entry_ts_eq_qualify_end": causal_entry,
        "population": {
            "design_evaluable": len(des),
            "confirm_evaluable": len(conf),
            "design_pokes": n_pokes,
            "design_accepts": n_accepts,
            "design_missing_entry": n_missing,
            "accepts_minus_missing": n_accepts - n_missing,
        },
    }


# --------------------------------------------------------------------------- #
# R0 money floor
# --------------------------------------------------------------------------- #
def r0_money_floor(data: dict) -> dict:
    freeze, floor = data["freeze"], data["floor"]
    q70 = freeze["pooled"]["p70"]["protection_ibw"]
    q65 = freeze["pooled"]["p65"]["protection_ibw"]
    out = {"q70_ibw": q70, "q65_ibw": q65, "majors": {}, "n_above_floor_majors": 0}
    for sym in MAJORS:
        row = floor["per_symbol"][sym]
        cost = row["cost_floor_bps"]
        ibw = row["median_ib_width_bps"]
        tp1_bps_70 = q70 * ibw
        tp1_bps_65 = q65 * ibw
        # also per-symbol q if available
        ps = freeze["per_symbol"].get(sym, {})
        ps_q70 = ps.get("p70")
        ps_tp1 = (ps_q70 * ibw) if ps_q70 is not None else None
        band = "ABOVE_FLOOR" if tp1_bps_70 > cost else "AT_OR_BELOW_FLOOR"
        out["majors"][sym] = {
            "cost_floor_bps": cost,
            "median_ib_width_bps": ibw,
            "tp1_must_exceed_ibw": row["tp1_must_exceed_ibw"],
            "tp1_bps_pooled_p70": tp1_bps_70,
            "tp1_bps_pooled_p65": tp1_bps_65,
            "tp1_bps_per_symbol_p70": ps_tp1,
            "margin_vs_floor_bps_p70": tp1_bps_70 - cost,
            "floor_band": band,
            "spread_source": row.get("spread_source"),
        }
        if band == "ABOVE_FLOOR":
            out["n_above_floor_majors"] += 1
    out["all_majors_above_floor"] = out["n_above_floor_majors"] == len(MAJORS)
    return out


# --------------------------------------------------------------------------- #
# R1 calibration + control self-hit (P-01)
# --------------------------------------------------------------------------- #
def r1_calibration(data: dict) -> dict:
    des, conf, ctrl, freeze = data["des"], data["conf"], data["ctrl"], data["freeze"]
    q65 = freeze["pooled"]["p65"]["protection_ibw"]
    q70 = freeze["pooled"]["p70"]["protection_ibw"]

    def hit_rate(df, q):
        m = df["mfe_norm"].to_numpy()
        m = m[np.isfinite(m)]
        return float(np.mean(m >= q)), int(len(m))

    # CONFIRM vs frozen DESIGN q
    hr65, n65 = hit_rate(conf, q65)
    hr70, n70 = hit_rate(conf, q70)

    # DESIGN self-hit (in-sample calibration disclosure)
    dhr65, _ = hit_rate(des, q65)
    dhr70, _ = hit_rate(des, q70)

    # CONTROL arm: estimate its own DESIGN quantile, measure self-hit on DESIGN
    # and also apply signal q to control (does unconditional also hit ~p?)
    cmfe = ctrl["mfe_norm"].to_numpy()
    cmfe = cmfe[np.isfinite(cmfe)]
    cq65 = float(np.quantile(cmfe, Q65))
    cq70 = float(np.quantile(cmfe, Q70))
    ctrl_self_65 = float(np.mean(cmfe >= cq65))
    ctrl_self_70 = float(np.mean(cmfe >= cq70))
    # control hit rate at SIGNAL frozen q (same q applied to control paths)
    ctrl_at_sig_q65 = float(np.mean(cmfe >= q65))
    ctrl_at_sig_q70 = float(np.mean(cmfe >= q70))

    # per-major CONFIRM
    majors = {}
    for sym in MAJORS:
        sc = conf[conf["symbol"] == sym]
        sd = des[des["symbol"] == sym]
        ps = freeze["per_symbol"].get(sym, {})
        pq65 = ps.get("p65", q65)
        pq70 = ps.get("p70", q70)
        # per-symbol q on CONFIRM
        if len(sc) == 0:
            continue
        hr_s65 = float(np.mean(sc["mfe_norm"] >= pq65))
        hr_s70 = float(np.mean(sc["mfe_norm"] >= pq70))
        # also pooled q on major
        hr_p65 = float(np.mean(sc["mfe_norm"] >= q65))
        hr_p70 = float(np.mean(sc["mfe_norm"] >= q70))

        def label(err):
            a = abs(err)
            if a <= 0.05:
                return "REPRODUCES"
            if a <= 0.10:
                return "DRIFTED"
            return "BROKEN"

        majors[sym] = {
            "n_design": int(len(sd)),
            "n_confirm": int(len(sc)),
            "q_hat_p65": pq65,
            "q_hat_p70": pq70,
            "calib_err_p65_per_sym_q": hr_s65 - P65,
            "calib_err_p70_per_sym_q": hr_s70 - P70,
            "label_p65": label(hr_s65 - P65),
            "label_p70": label(hr_s70 - P70),
            "calib_err_p70_pooled_q": hr_p70 - P70,
            "realised_hit_p70": hr_s70,
        }

    # full per-symbol label census (CONFIRM symbols with freeze q)
    freeze_syms = set(freeze["per_symbol"].keys())
    conf_syms = set(conf["symbol"].unique())
    covered = sorted(freeze_syms & conf_syms)
    labels_p70 = []
    per_sym_rows = []
    for sym in covered:
        sc = conf[conf["symbol"] == sym]
        pq70 = freeze["per_symbol"][sym]["p70"]
        hr = float(np.mean(sc["mfe_norm"] >= pq70))
        err = hr - P70
        a = abs(err)
        lab = "REPRODUCES" if a <= 0.05 else ("DRIFTED" if a <= 0.10 else "BROKEN")
        labels_p70.append(lab)
        per_sym_rows.append(
            {"symbol": sym, "n": int(len(sc)), "calib_err_p70": err, "label": lab, "hit": hr}
        )

    # bootstrap CI on pooled calib_err via day-clustered hit rates on CONFIRM
    conf = conf.copy()
    conf["hit70"] = (conf["mfe_norm"] >= q70).astype(float)
    conf["hit65"] = (conf["mfe_norm"] >= q65).astype(float)
    day70 = conf.groupby("day", sort=True)["hit70"].mean().to_numpy()
    day65 = conf.groupby("day", sort=True)["hit65"].mean().to_numpy()
    # contrast from nominal: day_hit - p
    ci70 = block_bootstrap_ci(day70 - P70, np.mean, block=5, seed=7)
    ci65 = block_bootstrap_ci(day65 - P65, np.mean, block=5, seed=7)

    return {
        "pooled": {
            "p65": {
                "q_hat_ibw": q65,
                "nominal_p": P65,
                "confirm_hit": hr65,
                "calib_err": hr65 - P65,
                "n": n65,
                "design_self_hit": dhr65,
                "design_self_err": dhr65 - P65,
                "day_clustered_calib_err_ci": ci65,
            },
            "p70": {
                "q_hat_ibw": q70,
                "nominal_p": P70,
                "confirm_hit": hr70,
                "calib_err": hr70 - P70,
                "n": n70,
                "design_self_hit": dhr70,
                "design_self_err": dhr70 - P70,
                "day_clustered_calib_err_ci": ci70,
            },
        },
        "majors": majors,
        "label_census_p70": dict(Counter(labels_p70)),
        "n_symbols_covered": len(covered),
        "worst_broken_p70": sorted(
            [r for r in per_sym_rows if r["label"] == "BROKEN"],
            key=lambda r: -abs(r["calib_err_p70"]),
        )[:10],
        "control_P01": {
            "note": (
                "If control's own DESIGN quantile self-hits ~p, quantile reproduction "
                "is a property of price paths generally (P-01), not acceptance conditioning."
            ),
            "control_own_q65": cq65,
            "control_own_q70": cq70,
            "control_self_hit_p65": ctrl_self_65,
            "control_self_hit_p70": ctrl_self_70,
            "control_hit_at_signal_q65": ctrl_at_sig_q65,
            "control_hit_at_signal_q70": ctrl_at_sig_q70,
            "signal_design_self_hit_p70": dhr70,
            "signal_confirm_hit_p70": hr70,
            "signal_q70": q70,
            "control_q70": cq70,
            "q_ratio_control_over_signal_p70": cq70 / q70 if q70 else None,
        },
    }


# --------------------------------------------------------------------------- #
# R2 race
# --------------------------------------------------------------------------- #
def race_w(outcomes: pd.Series) -> tuple[float, int]:
    """TP rate among resolved (TP or STOP); TIMEOUT excluded from denominator."""
    resolved = outcomes.isin(["TP", "STOP"])
    n = int(resolved.sum())
    if n == 0:
        return float("nan"), 0
    return float((outcomes[resolved] == "TP").mean()), n


def r2_race(data: dict) -> dict:
    des, ctrl, freeze, floor = data["des"], data["ctrl"], data["freeze"], data["floor"]
    q70 = freeze["pooled"]["p70"]["protection_ibw"]
    q65 = freeze["pooled"]["p65"]["protection_ibw"]

    out = {"pooled": {}, "majors": {}, "gross_p0": GROSS_P0}

    for tag, q, col in [("p65", q65, "outcome_p65"), ("p70", q70, "outcome_p70")]:
        ws, ns = race_w(des[col])
        wc, nc = race_w(ctrl[col])
        out["pooled"][tag] = {
            "tp1_ibw": q,
            "w_signal": ws,
            "w_control": wc,
            "w_contrast": ws - wc,
            "n_resolved_signal": ns,
            "n_resolved_control": nc,
            "vs_gross_p0": ws - GROSS_P0,
        }

    # day-clustered w contrast p70
    # per day: mean TP rate signal - mean TP rate control
    def day_w(df, col):
        rows = []
        for day, g in df.groupby("day"):
            w, n = race_w(g[col])
            if n > 0:
                rows.append((day, w, n))
        return pd.DataFrame(rows, columns=["day", "w", "n"]).set_index("day")

    ds = day_w(des, "outcome_p70")
    dc = day_w(ctrl, "outcome_p70")
    joined = ds.join(dc, lsuffix="_s", rsuffix="_c", how="inner")
    contrast = (joined["w_s"] - joined["w_c"]).to_numpy()
    ci = block_bootstrap_ci(contrast, np.median, block=5, seed=0)
    sens = block_sensitivity(contrast, [2, 5, 10], stat=np.median, seed=0)
    # MDE: smallest constant shift that makes CI exclude 0 (approx half-width from plant)
    # Use published screen MDE as reference; recompute half-width style
    half = abs(ci["stat"] - ci["ci"][0]) if ci["n"] >= 2 else float("nan")

    out["day_clustered_p70"] = {
        "n_days": int(ci["n"]),
        "contrast_median": ci["stat"],
        "ci": ci["ci"],
        "ci_excludes_zero": bool(ci["ci"][0] > 0 or ci["ci"][1] < 0),
        "ci_low_seed_range": ci["ci_low_seed_range"],
        "block_sensitivity": [
            {"block_req": s["block_req"], "ci": s["ci"]} for s in sens
        ],
        "approx_mde_halfwidth": half,
        "screen_mde_w_units": data["layers"]["R2_race"]["mde_curve_w_units"]["mde"],
    }

    # majors p70 + cost p0
    for sym in MAJORS:
        sd = des[des["symbol"] == sym]
        sc = ctrl[ctrl["symbol"] == sym]
        ws, ns = race_w(sd["outcome_p70"])
        wc, nc = race_w(sc["outcome_p70"])
        cost = floor["per_symbol"][sym]["cost_floor_bps"]
        ibw = floor["per_symbol"][sym]["median_ib_width_bps"]
        # STOP = TP1/2; cost_rt in IB widths = cost/ibw
        tp1 = q70
        stop = tp1 / 2.0
        cost_ibw = cost / ibw
        p0c = (stop + cost_ibw) / (tp1 + stop)
        out["majors"][sym] = {
            "w_signal": ws,
            "w_control": wc,
            "w_contrast": ws - wc,
            "n_resolved_signal": ns,
            "n_resolved_control": nc,
            "p0_gross": GROSS_P0,
            "p0_cost": p0c,
            "w_vs_p0_cost": ws - p0c,
            "w_vs_p0_gross": ws - GROSS_P0,
        }
    return out


# --------------------------------------------------------------------------- #
# R5 paired day asym contrast
# --------------------------------------------------------------------------- #
def r5_asym(data: dict) -> dict:
    des, ctrl = data["des"], data["ctrl"]

    def day_med_asym(df):
        return df.groupby("day", sort=True)["asym"].median()

    s = day_med_asym(des)
    c = day_med_asym(ctrl)
    j = pd.concat([s.rename("s"), c.rename("c")], axis=1).dropna()
    contrast = (j["s"] - j["c"]).to_numpy()
    ci = block_bootstrap_ci(contrast, np.median, block=5, seed=3)
    sens = block_sensitivity(contrast, [2, 5, 10], stat=np.median, seed=3)
    half = abs(ci["stat"] - ci["ci"][0]) if ci["n"] >= 2 else float("nan")

    # collapse fraction: control / signal level (not contrast)
    sig_level = float(s.mean())
    ctrl_level = float(c.mean())
    collapse = (ctrl_level / sig_level) if sig_level != 0 else float("nan")

    majors = {}
    for sym in MAJORS:
        sd = des[des["symbol"] == sym]
        sc = ctrl[ctrl["symbol"] == sym]
        ss = day_med_asym(sd)
        cc = day_med_asym(sc)
        jj = pd.concat([ss.rename("s"), cc.rename("c")], axis=1).dropna()
        if len(jj) < 5:
            majors[sym] = {"n_days": int(len(jj)), "note": "thin"}
            continue
        contr = (jj["s"] - jj["c"]).to_numpy()
        cim = block_bootstrap_ci(contr, np.median, block=5, seed=3)
        majors[sym] = {
            "n_days": int(cim["n"]),
            "contrast_median": cim["stat"],
            "ci": cim["ci"],
            "ci_excludes_zero": bool(cim["ci"][0] > 0 or cim["ci"][1] < 0),
            "signal_asym_day_mean": float(ss.mean()),
            "control_asym_day_mean": float(cc.mean()),
        }

    return {
        "pooled": {
            "n_days": int(ci["n"]),
            "contrast_median": ci["stat"],
            "ci": ci["ci"],
            "ci_excludes_zero": bool(ci["ci"][0] > 0 or ci["ci"][1] < 0),
            "ci_low_seed_range": ci["ci_low_seed_range"],
            "block_sensitivity": [
                {"block_req": s["block_req"], "ci": s["ci"]} for s in sens
            ],
            "approx_halfwidth_mde": half,
            "screen_mde": data["layers"]["R5_matched_control"]["mde_curve"]["mde"],
            "signal_asym_day_mean": sig_level,
            "control_asym_day_mean": ctrl_level,
            "collapse_fraction_control_over_signal_level": collapse,
            "note": "collapse on LEVELS is ill-defined when signal level ≈ 0; prefer contrast CI",
        },
        "majors": majors,
    }


# --------------------------------------------------------------------------- #
# R3 regime ρ contrast
# --------------------------------------------------------------------------- #
def spearman(x, y):
    """Finite-only Spearman (NaN dropped). Polars corr ranks NaN and attenuates |ρ|."""
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 10:
        return float("nan"), int(m.sum())
    r, _ = stats.spearmanr(x[m], y[m])
    return float(r), int(m.sum())


def r3_regime(data: dict) -> dict:
    des, ctrl = data["des"], data["ctrl"]
    # finite-only (preferred)
    rho_s, ns = spearman(
        des["ib_width_pctl"].to_numpy(), des["mfe_norm"].to_numpy()
    )
    rho_c, nc = spearman(
        ctrl["ib_width_pctl"].to_numpy(), ctrl["mfe_norm"].to_numpy()
    )
    # screen emission used polars.corr which keeps float NaN rows → different ρ
    # reproduce that for audit (not preferred)
    try:
        import polars as pl

        def _pl_rho(df_pd, x, y):
            d = pl.from_pandas(df_pd[[x, y]])
            return float(d.select(pl.corr(x, y, method="spearman")).item())

        rho_s_polars = _pl_rho(des, "ib_width_pctl", "mfe_norm")
        rho_c_polars = _pl_rho(ctrl, "ib_width_pctl", "mfe_norm")
        polars_contrast = rho_s_polars - rho_c_polars
    except Exception as e:
        rho_s_polars = rho_c_polars = polars_contrast = None
        _pl_err = str(e)
    else:
        _pl_err = None

    mfe_bps = (
        des["mfe"].abs() / ((des["ib_high"] + des["ib_low"]) / 2.0) * 1e4
    ).to_numpy()
    rho_raw, nr = spearman(des["ib_width_pctl"].to_numpy(), mfe_bps)

    majors = {}
    for sym in MAJORS:
        sd = des[des["symbol"] == sym]
        sc = ctrl[ctrl["symbol"] == sym]
        rs, nss = spearman(sd["ib_width_pctl"].to_numpy(), sd["mfe_norm"].to_numpy())
        rc, nsc = spearman(sc["ib_width_pctl"].to_numpy(), sc["mfe_norm"].to_numpy())
        majors[sym] = {
            "rho_signal": rs,
            "rho_control": rc,
            "rho_contrast": (rs - rc) if np.isfinite(rs) and np.isfinite(rc) else float("nan"),
            "n_signal": nss,
            "n_control": nsc,
        }

    nan_frac_s = float((~np.isfinite(des["ib_width_pctl"].to_numpy())).mean())
    nan_frac_c = float((~np.isfinite(ctrl["ib_width_pctl"].to_numpy())).mean())

    return {
        "preferred_finite_only": {
            "rho_signal_normalised": rho_s,
            "rho_control_normalised": rho_c,
            "rho_contrast": rho_s - rho_c if np.isfinite(rho_s) and np.isfinite(rho_c) else float("nan"),
            "n_signal": ns,
            "n_control": nc,
        },
        "screen_polars_nan_inclusive": {
            "rho_signal_normalised": rho_s_polars,
            "rho_control_normalised": rho_c_polars,
            "rho_contrast": polars_contrast,
            "note": "matches layers.json; NaN rows ranked by polars — attenuated |ρ_signal|",
            "error": _pl_err,
        },
        "raw_mfe_bps_rho_finite": rho_raw,
        "n_raw": nr,
        "nan_ib_width_pctl_frac_signal": nan_frac_s,
        "nan_ib_width_pctl_frac_control": nan_frac_c,
        "majors_finite_only": majors,
        "note": "binding = rho_contrast (finite-only preferred); raw signal ρ carries normaliser mechanic",
    }


# --------------------------------------------------------------------------- #
# R4 coherence terciles
# --------------------------------------------------------------------------- #
def r4_coherence(data: dict) -> dict:
    des = data["des"].copy()
    # DESIGN tercile edges on coh (finite only)
    coh = des["coh"]
    finite = coh.notna()
    edges = np.quantile(coh[finite], [1 / 3, 2 / 3])
    des["coh_terc"] = np.where(
        ~finite,
        -1,
        np.where(coh <= edges[0], 0, np.where(coh <= edges[1], 1, 2)),
    )
    bot = des[des["coh_terc"] == 0]
    top = des[des["coh_terc"] == 2]
    mfe_top = float(top["mfe_norm"].median())
    mfe_bot = float(bot["mfe_norm"].median())
    w_top, n_top = race_w(top["outcome_p70"])
    w_bot, n_bot = race_w(bot["outcome_p70"])

    # control: apply same DESIGN edges
    ctrl = data["ctrl"].copy()
    # control may not have coh — check
    if "coh" not in ctrl.columns:
        ctrl_contrast = None
        ctrl_note = "control parquet has no coh; R4 control contrast not recomputable from emission alone"
    else:
        ccoh = ctrl["coh"]
        ctrl["coh_terc"] = np.where(
            ccoh.isna(),
            -1,
            np.where(ccoh <= edges[0], 0, np.where(ccoh <= edges[1], 1, 2)),
        )
        cbot = ctrl[ctrl["coh_terc"] == 0]
        ctop = ctrl[ctrl["coh_terc"] == 2]
        ctrl_contrast = float(ctop["mfe_norm"].median() - cbot["mfe_norm"].median())
        ctrl_note = None

    majors = {}
    for sym in MAJORS:
        sd = des[des["symbol"] == sym]
        if sd["coh"].notna().sum() < 30:
            majors[sym] = {"n_finite_coh": int(sd["coh"].notna().sum()), "note": "thin"}
            continue
        e = np.quantile(sd["coh"].dropna(), [1 / 3, 2 / 3])
        terc = np.where(
            sd["coh"].isna(),
            -1,
            np.where(sd["coh"] <= e[0], 0, np.where(sd["coh"] <= e[1], 1, 2)),
        )
        t = sd[terc == 2]
        b = sd[terc == 0]
        majors[sym] = {
            "mfe_contrast": float(t["mfe_norm"].median() - b["mfe_norm"].median()),
            "n_top": int(len(t)),
            "n_bottom": int(len(b)),
            "w_contrast": race_w(t["outcome_p70"])[0] - race_w(b["outcome_p70"])[0],
        }

    return {
        "tercile_edges": [float(edges[0]), float(edges[1])],
        "n_finite": int(finite.sum()),
        "mfe_norm_top_median": mfe_top,
        "mfe_norm_bottom_median": mfe_bot,
        "mfe_norm_contrast": mfe_top - mfe_bot,
        "w_top": w_top,
        "w_bottom": w_bot,
        "w_contrast": w_top - w_bot,
        "n_resolved_top": n_top,
        "n_resolved_bottom": n_bot,
        "control_mfe_contrast": ctrl_contrast,
        "control_note": ctrl_note,
        "majors": majors,
    }


# --------------------------------------------------------------------------- #
# Time stability thirds
# --------------------------------------------------------------------------- #
def time_thirds(data: dict) -> dict:
    des = data["des"].sort_values("entry_ts").reset_index(drop=True)
    n = len(des)
    cuts = [0, n // 3, 2 * n // 3, n]
    q70 = data["freeze"]["pooled"]["p70"]["protection_ibw"]
    thirds = []
    for i in range(3):
        sl = des.iloc[cuts[i] : cuts[i + 1]]
        # control filtered to same day set
        days = set(sl["day"])
        cl = data["ctrl"][data["ctrl"]["day"].isin(days)]
        hr = float(np.mean(sl["mfe_norm"] >= q70))
        ws, _ = race_w(sl["outcome_p70"])
        wc, _ = race_w(cl["outcome_p70"]) if len(cl) else (float("nan"), 0)
        # day asym contrast
        s = sl.groupby("day")["asym"].median()
        c = cl.groupby("day")["asym"].median()
        j = pd.concat([s.rename("s"), c.rename("c")], axis=1).dropna()
        contr = float((j["s"] - j["c"]).median()) if len(j) else float("nan")
        thirds.append(
            {
                "third": i + 1,
                "n": int(len(sl)),
                "entry_start": str(sl["entry_ts"].min()),
                "entry_end": str(sl["entry_ts"].max()),
                "R1_self_hit_p70": hr,
                "R1_self_err_p70": hr - P70,
                "R2_w_signal": ws,
                "R2_w_control": wc,
                "R2_w_contrast": ws - wc if np.isfinite(wc) else float("nan"),
                "R5_asym_contrast_median": contr,
            }
        )
    signs_r5 = [np.sign(t["R5_asym_contrast_median"]) for t in thirds if np.isfinite(t["R5_asym_contrast_median"])]
    signs_r2 = [np.sign(t["R2_w_contrast"]) for t in thirds if np.isfinite(t["R2_w_contrast"])]
    return {
        "thirds": thirds,
        "R5_sign_consistent": len(set(signs_r5)) == 1,
        "R2_sign_consistent": len(set(signs_r2)) == 1,
        "R5_signs": signs_r5,
        "R2_signs": signs_r2,
    }


# --------------------------------------------------------------------------- #
# Spread-scale routing (recompute majors + count)
# --------------------------------------------------------------------------- #
def spread_scale(data: dict) -> dict:
    # recompute gross edge as median mfe_norm contrast × median ib_width_bps
    des, ctrl, floor = data["des"], data["ctrl"], data["floor"]
    rows = []
    undec = []
    for sym, g in des.groupby("symbol"):
        if sym not in floor["per_symbol"]:
            continue
        sc = ctrl[ctrl["symbol"] == sym]
        if len(sc) == 0:
            continue
        contrast = float(g["mfe_norm"].median() - sc["mfe_norm"].median())
        ibw = floor["per_symbol"][sym]["median_ib_width_bps"]
        rt = floor["per_symbol"][sym]["spread_rt_bps"]
        gross = contrast * ibw
        thr = 3.0 * rt
        und = abs(gross) < thr and abs(gross) > 0  # undecidable if edge < 3× spread
        # actual xen.evaluation rule: typically |gross| < 3 * rt_spread
        try:
            from xen.evaluation import spread_scale_route

            route = spread_scale_route(gross, rt)
            t1_und = bool(route.get("t1_undecidable", abs(gross) < thr))
        except Exception:
            t1_und = bool(abs(gross) < thr)
            route = {"t1_undecidable": t1_und}
        rows.append(
            {
                "symbol": sym,
                "contrast_mfe_norm": contrast,
                "gross_edge_bps": gross,
                "rt_spread_bps": rt,
                "t1_undecidable": t1_und,
            }
        )
        if t1_und:
            undec.append(sym)
    majors = {r["symbol"]: r for r in rows if r["symbol"] in MAJORS}
    return {
        "n_symbols": len(rows),
        "n_t1_undecidable": len(undec),
        "undecidable_symbols": undec,
        "majors": majors,
    }


# --------------------------------------------------------------------------- #
# Side derangement power note (from layers; cannot re-derange without bars)
# --------------------------------------------------------------------------- #
def side_derange_note(data: dict) -> dict:
    sd = data["layers"]["side_derangement"]
    return {
        "n_input": sd["n_input"],
        "n_deranged": sd["n_deranged"],
        "n_dropped_singleton": sd["n_dropped_singleton"],
        "n_dropped_infeasible": sd["n_dropped_infeasible"],
        "fixed_point_rate": sd["fixed_point_rate"],
        "derangeable_frac": sd["n_deranged"] / sd["n_input"] if sd["n_input"] else 0,
        "power_status": "UNPOWERED" if sd["n_deranged"] < 200 else "REPORTABLE",
        "note": "re-derangement needs bar paths; coverage stats taken from emission attestation",
    }


# --------------------------------------------------------------------------- #
# Falsification: control quantile reproduction is mechanical
# --------------------------------------------------------------------------- #
def falsification_p01(data: dict) -> dict:
    """Framework falsifier #1 context + P-01.

    Falsifier #1: 'no anchor reproduces ~65–70% Protection' — here Protection
    DOES hit ~p on CONFIRM for the signal arm. But P-01 asks whether that is
    distinctive of acceptance conditioning.
    """
    r1 = r1_calibration(data)
    p01 = r1["control_P01"]
    # Also: CONFIRM control is not emitted; DESIGN control self-hit only
    # Compare signal DESIGN self-hit to control self-hit at own quantiles
    return {
        "signal_confirm_calib_err_p70": r1["pooled"]["p70"]["calib_err"],
        "signal_design_self_err_p70": r1["pooled"]["p70"]["design_self_err"],
        "control_design_self_hit_p70": p01["control_self_hit_p70"],
        "control_own_q70_vs_signal_q70": {
            "control_q": p01["control_own_q70"],
            "signal_q": p01["signal_q70"],
            "ratio": p01["q_ratio_control_over_signal_p70"],
        },
        "control_hit_rate_at_signal_protection_p70": p01["control_hit_at_signal_q70"],
        "interpretation_anchor": (
            "Control at its own (1-p) quantile self-hits ≈ p by construction of order statistics. "
            "Signal CONFIRM hit ≈ p is therefore NOT evidence of acceptance-specific protection "
            "unless the LEVEL of q̂ (IB widths) or the race/asym CONTRAST vs control separates."
        ),
        "level_comparison": {
            "signal_protection_p70_ibw": p01["signal_q70"],
            "control_protection_p70_ibw": p01["control_own_q70"],
            "delta_ibw": p01["signal_q70"] - p01["control_own_q70"],
        },
    }


def main():
    data = load()
    report = {
        "item": "SPDR-007",
        "integrity": integrity(data),
        "R0_money_floor": r0_money_floor(data),
        "R1_calibration": r1_calibration(data),
        "R2_race": r2_race(data),
        "R3_regime": r3_regime(data),
        "R4_coherence": r4_coherence(data),
        "R5_asym": r5_asym(data),
        "time_thirds": time_thirds(data),
        "spread_scale": spread_scale(data),
        "side_derangement": side_derange_note(data),
        "falsification_P01": falsification_p01(data),
    }

    def _default(o):
        if isinstance(o, (np.floating, np.integer)):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, (pd.Timestamp,)):
            return str(o)
        raise TypeError(type(o))

    OUT.write_text(json.dumps(report, indent=2, default=_default))
    print(f"wrote {OUT}")
    # concise console summary
    i = report["integrity"]
    print("INTEGRITY freeze_pin_ok", i["freeze"]["pin_ok"], "bands", i["bands"]["design_before_confirm"],
          "trip_hard_fail", i["tripwire"]["hard_fail"], "bite", i["tripwire"]["bite_corr"])
    print("R0 all majors above floor", report["R0_money_floor"]["all_majors_above_floor"])
    print("R1 pooled p70 calib_err", report["R1_calibration"]["pooled"]["p70"]["calib_err"])
    print("R1 majors", {k: v["label_p70"] for k, v in report["R1_calibration"]["majors"].items()})
    print("R2 p70 w_contrast", report["R2_race"]["pooled"]["p70"]["w_contrast"],
          "CI", report["R2_race"]["day_clustered_p70"]["ci"])
    print("R5 contrast", report["R5_asym"]["pooled"]["contrast_median"],
          "CI", report["R5_asym"]["pooled"]["ci"], "mde", report["R5_asym"]["pooled"]["screen_mde"])
    print(
        "R3 rho_contrast finite",
        report["R3_regime"]["preferred_finite_only"]["rho_contrast"],
        "polars",
        report["R3_regime"]["screen_polars_nan_inclusive"]["rho_contrast"],
    )
    print("R4 mfe_contrast", report["R4_coherence"]["mfe_norm_contrast"])
    print("P01 control self-hit p70", report["falsification_P01"]["control_design_self_hit_p70"])
    print("P01 signal q vs control q", report["falsification_P01"]["level_comparison"])
    print("thirds R5 signs", report["time_thirds"]["R5_signs"], "consistent",
          report["time_thirds"]["R5_sign_consistent"])


if __name__ == "__main__":
    main()
