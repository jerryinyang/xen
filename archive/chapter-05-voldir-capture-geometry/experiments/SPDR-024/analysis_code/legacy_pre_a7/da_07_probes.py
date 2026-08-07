"""QUARANTINED pre-AMENDMENT-7. Do not use for emission or analysis.md."""
raise RuntimeError(
    "AMENDMENT_7_QUARANTINE: this script is legacy (pre R1-R5 floor fix). "
    "Use analysis_code/analyse.py emission only; see legacy_pre_a7/README.md."
)

"""Falsification probes on the two selection reads whose CI clears zero, plus
concentration ladders, dose-response on the continuous arms, and break-even spread."""
from __future__ import annotations
import json
import sys
import numpy as np
import polars as pl
sys.path.insert(0, "experiments/SPDR-024/analysis_code")
from da_boot import two_stage_boot_mean

ROOT = "experiments/SPDR-024/results/analysis"


def bm(df, col, seed=1):
    v = df[col].to_numpy()
    _, s = np.unique(df["symbol"].to_numpy(), return_inverse=True)
    return two_stage_boot_mean(v, s, np.arange(len(v)), n_boot=2000, seed=seed)


def cid(a, acol, r, rcol, seed=1):
    d = bm(a, acol, seed) - bm(r, rcol, seed + 50)
    return [float(np.quantile(d, .025)), float(np.quantile(d, .975))]


out = {}
# --- Probe 1: the two crypto_H1 selection reads, stratified by regime -----------------
d = pl.read_parquet(f"{ROOT}/crypto_H1/episodes.parquet")
probe = {}
for arm in ["NAT_BREAKOUT_LEVEL_FORECAST_K12_PENDING_EXPIRY_DIRECT",
            "NAT_BREAKOUT_LEVEL_FORECAST_K4_BREAKOUT_THRESHOLD_DIRECT",
            "NAT_BREAKOUT_LEVEL_FORECAST_K4_PENDING_EXPIRY_DIRECT"]:
    a = d.filter(pl.col("arm_id") == arm)
    adm = a.filter(pl.col("admitted") & pl.col("exit_ts").is_not_null())
    rej = a.filter(pl.col("counterfactual_source") == "FIXED_ARM_REALISED_OUTCOME")
    r = {"overall": {"n_a": adm.height, "n_r": rej.height,
                     "contrast": float(adm["outcome_bps"].mean() - rej["counterfactual_outcome_bps"].mean()),
                     "ci": cid(adm, "outcome_bps", rej, "counterfactual_outcome_bps")}}
    # regime composition of admitted vs rejected
    r["admitted_high_share"] = float((adm["regime_state"] == "HIGH").mean())
    r["rejected_high_share"] = float((rej["regime_state"] == "HIGH").mean())
    for st in ["HIGH", "LOW"]:
        aa = adm.filter(pl.col("regime_state") == st)
        rr = rej.filter(pl.col("regime_state") == st)
        if aa.height > 30 and rr.height > 30:
            r[st] = {"n_a": aa.height, "n_r": rr.height,
                     "contrast": float(aa["outcome_bps"].mean() - rr["counterfactual_outcome_bps"].mean()),
                     "ci": cid(aa, "outcome_bps", rr, "counterfactual_outcome_bps", seed=5)}
    # per-symbol ladder on the contrast
    per = []
    for sym in sorted(set(adm["symbol"].unique().to_list())):
        aa = adm.filter(pl.col("symbol") == sym)
        rr = rej.filter(pl.col("symbol") == sym)
        if aa.height >= 10 and rr.height >= 10:
            per.append({"symbol": sym, "n_a": aa.height, "n_r": rr.height,
                        "contrast": float(aa["outcome_bps"].mean() - rr["counterfactual_outcome_bps"].mean())})
    per.sort(key=lambda x: x["contrast"])
    r["per_symbol"] = per
    vals = [p["contrast"] for p in per]
    r["ladder"] = {"pooled_mean_of_symbol_means": float(np.mean(vals)),
                   "drop_worst": float(np.mean(vals[1:])), "drop_best": float(np.mean(vals[:-1])),
                   "drop_both": float(np.mean(vals[1:-1])),
                   "n_symbols_positive": int(sum(v > 0 for v in vals)), "n_symbols": len(vals)}
    # per-year stability
    yr = adm.with_columns(pl.col("entry_ts").dt.year().alias("y")).group_by("y").agg(
        pl.len(), pl.col("outcome_bps").mean().alias("m"))
    yr2 = rej.with_columns(pl.col("decision_ts").dt.year().alias("y")).group_by("y").agg(
        pl.len().alias("nr"), pl.col("counterfactual_outcome_bps").mean().alias("mr"))
    r["per_year"] = yr.join(yr2, on="y", how="full").sort("y").to_dicts()
    probe[arm] = r
out["selection_probes_crypto_H1"] = probe

# --- Probe 2: dose-response on the continuous SIZE arms ------------------------------
dose = {}
for cell in ["ctrader_H1", "ctrader_H4", "crypto_H1", "crypto_H4"]:
    dd = pl.read_parquet(f"{ROOT}/{cell}/episodes.parquet")
    b = dd.filter((pl.col("arm_id") == "FIXED_SIZE_UNIT") & pl.col("exit_ts").is_not_null()).select(
        ["origin_id", "symbol", "outcome_bps"])
    cd = {}
    for arm in [a for a in dd["arm_id"].unique().to_list() if a.endswith("SCALE_NORMALISED")]:
        a = dd.filter((pl.col("arm_id") == arm) & pl.col("exit_ts").is_not_null()).select(["origin_id", "risk_size"])
        j = b.join(a, on="origin_id")
        rs = j["risk_size"].to_numpy()
        o = j["outcome_bps"].to_numpy()
        qs = np.quantile(rs, [0, .2, .4, .6, .8, 1.0])
        bins = []
        for i in range(5):
            m = (rs >= qs[i]) & (rs <= qs[i + 1] if i == 4 else rs < qs[i + 1])
            if m.sum() > 5:
                bins.append({"q": i + 1, "risk_size_mid": float(np.median(rs[m])), "n": int(m.sum()),
                             "baseline_mean_bps": float(o[m].mean())})
        # rank correlation between committed size and realised return
        from scipy.stats import spearmanr
        rho, p = spearmanr(rs, o)
        cd[arm] = {"bins": bins, "spearman_rho_size_vs_return": float(rho), "p": float(p),
                   "risk_size_q": [float(x) for x in qs]}
    dose[cell] = cd
out["dose_response_continuous"] = dose

# --- Probe 3: break-even spread for the SIZE arms (NON-EMITTED SCENARIO) --------------
be = {}
for cell in ["ctrader_H1", "ctrader_H4", "crypto_H1", "crypto_H4"]:
    dd = pl.read_parquet(f"{ROOT}/{cell}/episodes.parquet")
    b = dd.filter((pl.col("arm_id") == "FIXED_SIZE_UNIT") & pl.col("exit_ts").is_not_null())
    be[cell] = {"baseline_mean_bps": float(b["outcome_bps"].mean()),
                "baseline_breakeven_spread_rt_bps_NON_EMITTED_SCENARIO": abs(float(b["outcome_bps"].mean())),
                "n_round_trips": b.height}
out["breakeven_scenarios"] = be

json.dump(out, open(sys.argv[1], "w"), indent=1, default=str)
