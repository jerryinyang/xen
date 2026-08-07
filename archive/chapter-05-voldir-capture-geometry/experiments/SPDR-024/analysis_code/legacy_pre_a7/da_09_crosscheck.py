"""QUARANTINED pre-AMENDMENT-7. Do not use for emission or analysis.md."""
raise RuntimeError(
    "AMENDMENT_7_QUARANTINE: this script is legacy (pre R1-R5 floor fix). "
    "Use analysis_code/analyse.py emission only; see legacy_pre_a7/README.md."
)

"""Cross-check the shipped decompose() and gate-permutation control against my own
independent computation from episodes.parquet. Trust mine on disagreement."""
from __future__ import annotations
import json
import sys
import numpy as np
import polars as pl

CELLS = ["ctrader_H1", "ctrader_H4", "crypto_H1", "crypto_H4"]
ROOT = "experiments/SPDR-024/results/analysis"
NDRAW = 2000

rows = []
for cell in CELLS:
    d = pl.read_parquet(f"{ROOT}/{cell}/episodes.parquet")
    em = pl.read_parquet(f"{ROOT}/{cell}/scale_channel_estimates.parquet").filter(
        (pl.col("scope") == "POOLED") & (pl.col("lens") == "PRIMARY_capital_normalised")
        & (pl.col("regime") == "ALL") & pl.col("governs"))
    b = d.filter((pl.col("arm_id") == "FIXED_SIZE_UNIT") & pl.col("exit_ts").is_not_null()).select(
        ["origin_id", "symbol", "outcome_bps", "capital_normalised_return_bps"])
    for r in em.iter_rows(named=True):
        a = d.filter((pl.col("arm_id") == r["arm_id"]) & pl.col("exit_ts").is_not_null()).select(
            ["origin_id", "risk_size", "capital_normalised_return_bps"])
        j = b.join(a, on="origin_id", suffix="_a")
        s = j["risk_size"].to_numpy()
        ret = j["outcome_bps"].to_numpy()
        delta = (j["capital_normalised_return_bps_a"] - j["capital_normalised_return_bps"]).to_numpy()
        # my decomposition: E[(s-1)r] = (E[s]-1)E[r] + Cov(s,r)   (population cov, ddof=0)
        exp_term = (s.mean() - 1.0) * ret.mean()
        sel_term = ((s - s.mean()) * (ret - ret.mean())).mean()
        # my gate-permutation control (within symbol), sigma-hat normalised like the estimate
        _, sy = np.unique(j["symbol"].to_numpy(), return_inverse=True)
        def est(dl):
            z = np.empty_like(dl)
            for k in range(sy.max() + 1):
                m = sy == k
                sd = dl[m].std(ddof=1)
                z[m] = dl[m] / sd if sd > 0 else 0.0
            return float(z.mean())
        obs = est(delta)
        rng = np.random.default_rng(4242)
        w = s - 1.0
        null = np.empty(NDRAW)
        for t in range(NDRAW):
            wp = np.empty_like(w)
            for k in range(sy.max() + 1):
                m = np.where(sy == k)[0]
                wp[m] = rng.permutation(w[m])
            null[t] = est(wp * ret)
        pct = float((null <= obs).mean())
        rows.append({
            "cell": cell, "arm": r["arm_id"], "component": r["component"], "setting": r["setting"],
            "my_n": j.height, "emitted_n_trades": r["n_trades"],
            "my_mean_delta": float(delta.mean()), "emitted_mean_delta": r["mean_delta_raw"],
            "my_exposure": exp_term, "emitted_exposure": r["exposure_term_bps"],
            "my_selectivity": sel_term, "emitted_selectivity": r["selectivity_term_bps"],
            "identity_residual": float(delta.mean() - (exp_term + sel_term)),
            "my_est_sigma": obs, "emitted_est_sigma": r["estimate_sigma"],
            "my_null_mean": float(null.mean()), "emitted_null_mean": r["control_null_mean_sigma"],
            "my_component_specific": obs - float(null.mean()),
            "emitted_component_specific": r["control_component_specific_sigma"],
            "my_p": float(2 * min(pct, 1 - pct)), "emitted_p": r["control_two_sided_p"],
            "mde_sigma": r["mde_sigma"], "band": r["band"],
            "component_specific_band": r["component_specific_band"],
            "emitted_exposure_share": r["exposure_share_of_effect"],
            "my_abs_share": abs(exp_term) / (abs(exp_term) + abs(sel_term)),
            "signs_oppose": bool(np.sign(exp_term) != np.sign(sel_term)),
            "exposure_over_net": exp_term / delta.mean() if delta.mean() != 0 else None,
        })
        print(cell, r["arm_id"], "done", file=sys.stderr)
json.dump(rows, open(sys.argv[1], "w"), indent=1)
