"""QUARANTINED pre-AMENDMENT-7. Do not use for emission or analysis.md."""
raise RuntimeError(
    "AMENDMENT_7_QUARANTINE: this script is legacy (pre R1-R5 floor fix). "
    "Use analysis_code/analyse.py emission only; see legacy_pre_a7/README.md."
)

"""Random-gate control: is a component's sizing effect distinguishable from halving a
RANDOM subset of the same size? The paired delta is exactly (risk_size-1) x outcome, so any
gate on a positive-mean population produces a negative delta. This battery quantifies how
much of each component's effect is that mechanical consequence.

For each SIZE arm: draw N random gates matching the arm's own gate rate (per symbol, so the
per-symbol composition is preserved), recompute the sigma-hat-normalised paired estimate, and
report the observed effect's percentile within the random-gate null.
"""
from __future__ import annotations
import json
import sys
import numpy as np
import polars as pl

CELLS = ["ctrader_H1", "ctrader_H4", "crypto_H1", "crypto_H4"]
ROOT = "experiments/SPDR-024/results/analysis"
NDRAW = 2000

out = []
for cell in CELLS:
    d = pl.read_parquet(f"{ROOT}/{cell}/episodes.parquet")
    b = d.filter((pl.col("arm_id") == "FIXED_SIZE_UNIT") & pl.col("exit_ts").is_not_null()).select(
        ["origin_id", "symbol", "outcome_bps"])
    o = b["outcome_bps"].to_numpy()
    _, sym = np.unique(b["symbol"].to_numpy(), return_inverse=True)
    nsym = sym.max() + 1
    arms = d.filter((pl.col("arm_class") == "MANAGEMENT") & (pl.col("device") == "SIZE"))["arm_id"].unique().sort().to_list()
    for arm in arms:
        a = d.filter((pl.col("arm_id") == arm) & pl.col("exit_ts").is_not_null()).select(["origin_id", "risk_size"])
        j = b.join(a, on="origin_id")
        rs = j["risk_size"].to_numpy()
        oo = j["outcome_bps"].to_numpy()
        _, sy = np.unique(j["symbol"].to_numpy(), return_inverse=True)
        w = rs - 1.0
        obs_delta = w * oo

        def est(delta):
            z = np.empty_like(delta)
            for s in range(sy.max() + 1):
                m = sy == s
                sd = delta[m].std(ddof=1)
                z[m] = delta[m] / sd if sd > 0 else 0.0
            return float(z.mean())

        obs = est(obs_delta)
        rng = np.random.default_rng(42)
        null = np.empty(NDRAW)
        for k in range(NDRAW):
            wp = np.empty_like(w)
            for s in range(sy.max() + 1):
                m = np.where(sy == s)[0]
                wp[m] = rng.permutation(w[m])          # preserve per-symbol weight multiset
            null[k] = est(wp * oo)
        pct = float((null <= obs).mean())
        out.append({"cell": cell, "arm": arm,
                    "component": d.filter(pl.col("arm_id") == arm)["component"][0],
                    "setting": d.filter(pl.col("arm_id") == arm)["setting"][0],
                    "observed_sigma": obs,
                    "random_gate_mean": float(null.mean()),
                    "random_gate_sd": float(null.std(ddof=1)),
                    "random_gate_p05": float(np.quantile(null, .05)),
                    "random_gate_p95": float(np.quantile(null, .95)),
                    "observed_percentile_in_null": pct,
                    "two_sided_p": float(2 * min(pct, 1 - pct)),
                    "excess_over_random": obs - float(null.mean()),
                    "gate_rate": float((rs < 1).mean())})
        print(cell, arm, "done", file=sys.stderr)
json.dump(out, open(sys.argv[1], "w"), indent=1)
