"""QUARANTINED pre-AMENDMENT-7. Do not use for emission or analysis.md."""
raise RuntimeError(
    "AMENDMENT_7_QUARANTINE: this script is legacy (pre R1-R5 floor fix). "
    "Use analysis_code/analyse.py emission only; see legacy_pre_a7/README.md."
)

"""Data-analyst: regime-conditional reads + the identity check on the SIZE arms.

(a) Is the paired SIZE delta exactly (risk_size - 1) x baseline outcome? If so the scale
    channel is an exact linear functional of the baseline's own returns and the component's
    gate, and 'does sizing move expectancy' == 'is the baseline's mean return different in
    the gated state'.
(b) Baseline expectancy conditional on realised regime_state.
(c) Paired SIZE delta conditional on regime_state.
(d) Regime-episode structure (count, length distribution) per cell.
"""
from __future__ import annotations
import json
import sys
import numpy as np
import polars as pl

sys.path.insert(0, "experiments/SPDR-024/analysis_code")
from da_boot import two_stage_boot_mean  # noqa: E402

CELLS = ["ctrader_H1", "ctrader_H4", "crypto_H1", "crypto_H4"]
ROOT = "experiments/SPDR-024/results/analysis"
N_BOOT = 2000


def ci(df: pl.DataFrame, col: str, seed=7):
    v = df[col].to_numpy()
    _, sym = np.unique(df["symbol"].to_numpy(), return_inverse=True)
    st = two_stage_boot_mean(v, sym, np.arange(len(v)), n_boot=N_BOOT, seed=seed)
    return [float(np.quantile(st, .025)), float(np.quantile(st, .975))]


out = {}
for cell in CELLS:
    d = pl.read_parquet(f"{ROOT}/{cell}/episodes.parquet")
    base = d.filter((pl.col("arm_id") == "FIXED_SIZE_UNIT") & pl.col("exit_ts").is_not_null())
    rec = {}
    # (d) regime episode structure over the baseline's traded origins
    allrows = d.filter(pl.col("arm_id") == "FIXED_SIZE_UNIT")
    ep = allrows.group_by(["symbol", "regime_episode_id"]).agg(pl.len().alias("n_origins"))
    rec["regime_episodes"] = {
        "n_episodes_over_origins": ep.height,
        "origins_per_episode": {k: float(np.quantile(ep["n_origins"].to_numpy(), v))
                                for k, v in [("p10", .1), ("p50", .5), ("p90", .9)]},
        "state_share_over_origins": allrows["regime_state"].value_counts().to_dicts(),
    }
    epf = base.group_by(["symbol", "regime_episode_id"]).agg(pl.len().alias("n_trades"))
    rec["regime_episodes"]["n_episodes_containing_a_trade"] = epf.height
    rec["regime_episodes"]["trades_per_episode_mean"] = float(epf["n_trades"].mean())

    # (b) baseline expectancy by realised regime
    bstrat = []
    for st_, g in base.group_by("regime_state"):
        o = g["outcome_bps"].to_numpy()
        bstrat.append({"regime": st_[0], "n": len(o), "mean_bps": float(o.mean()),
                       "median_bps": float(np.median(o)), "sd": float(o.std(ddof=1)),
                       "win_share": float((o > 0).mean()),
                       "ci": ci(g, "outcome_bps") if len(o) > 5 else None,
                       "total_bps": float(o.sum())})
    rec["baseline_by_regime"] = sorted(bstrat, key=lambda r: r["regime"])

    # (a)/(c) SIZE arms
    arms = (d.filter((pl.col("arm_class") == "MANAGEMENT") & (pl.col("device") == "SIZE"))
            ["arm_id"].unique().sort().to_list())
    ident, cond = [], []
    bsel = base.select(["origin_id", "symbol", "regime_state", "outcome_bps",
                        "capital_normalised_return_bps"])
    for arm in arms:
        a = d.filter((pl.col("arm_id") == arm) & pl.col("exit_ts").is_not_null()).select(
            ["origin_id", "risk_size", "capital_normalised_return_bps"])
        j = bsel.join(a, on="origin_id", suffix="_a")
        delta = (j["capital_normalised_return_bps_a"] - j["capital_normalised_return_bps"]).to_numpy()
        pred = ((j["risk_size"].to_numpy() - 1.0) * j["outcome_bps"].to_numpy())
        ident.append({"arm": arm, "max_abs_residual": float(np.abs(delta - pred).max()),
                      "n": len(delta),
                      "risk_size_values": sorted(set(np.round(j["risk_size"].to_numpy(), 4)))[:6],
                      "share_risk_size_lt_1": float((j["risk_size"].to_numpy() < 1).mean()),
                      "share_risk_size_gt_1": float((j["risk_size"].to_numpy() > 1).mean())})
        jj = j.with_columns(pl.Series("delta", delta))
        per = []
        for st_, g in jj.group_by("regime_state"):
            dv = g["delta"].to_numpy()
            per.append({"regime": st_[0], "n": len(dv), "mean_delta_bps": float(dv.mean()),
                        "ci": ci(g, "delta", seed=11) if len(dv) > 5 else None,
                        "mean_baseline_bps": float(g["outcome_bps"].mean()),
                        "mean_risk_size": float(g["risk_size"].mean())})
        cond.append({"arm": arm, "by_regime": sorted(per, key=lambda r: r["regime"])})
    rec["size_identity"] = ident
    rec["size_by_regime"] = cond
    out[cell] = rec
    print(cell, "done", file=sys.stderr)

json.dump(out, open(sys.argv[1], "w"), indent=1, default=str)
