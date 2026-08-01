"""SPDR-023 fresh-context analyst — X2: independent per-stratum paired native estimates.

The emitted `paired_outcome_delta_bps` = adaptive `outcome_bps` - fixed-comparator
`outcome_bps` on the SAME origin and SAME entry variant. Both sides are imputed 0.0 when the
arm's episode never became a Nautilus position (engine allows one open episode per instrument
per entry variant, so most arm-origin candidates end BLOCKED_ACTIVE in the ledger).

Therefore three lenses are computed for every stratum, never one:
  L1_ALL          - every shared row, as emitted (occupancy-inclusive; blocked scored 0)
  L2_EITHER       - rows where at least one of the two arms actually traded
  L3_BOTH         - rows where BOTH arms traded (like-for-like paired trade comparison)

Dependence-matched circular-block bootstrap, block = 24 H1 bars >= max native horizon 24.
Full per-stratum emission; no pruning, no verdict.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path("/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen")
ART = ROOT / "python/experiments/SPDR-023/results/analysis"
RUNS = {
    "ctrader": ROOT / "data/nautilus_runs/SPDR-023-ctrader-train-20260731T004708Z",
    "crypto": ROOT / "data/nautilus_runs/SPDR-023-crypto-train-20260731T004708Z",
}
OUT = ROOT / "python/experiments/SPDR-023/results/analyst"

BLOCK = 24
N_BOOT = 400
N_SEEDS = 5
Z = 2.8  # programme MDE convention 2.8 sigma


def block_ci_mean(x: np.ndarray, block: int = BLOCK, n_boot: int = N_BOOT,
                  n_seeds: int = N_SEEDS, seed: int = 0) -> dict:
    """Circular moving-block bootstrap CI for the MEAN.

    For stat=mean a resample of n_blocks circular blocks has mean equal to the mean of the
    drawn circular block-means, so it is computed on the precomputed block-mean vector.
    For n < 500 the canonical xen.evaluation.block_bootstrap_ci is called directly (it
    truncates the partial trailing block, which only matters when n_blocks is small).
    """
    n = len(x)
    if n == 0:
        return dict(n=0, block=0, stat=np.nan, ci_low=np.nan, ci_high=np.nan,
                    ci_low_seed_min=np.nan, ci_low_seed_max=np.nan, n_eff=0)
    if n == 1:
        return dict(n=1, block=1, stat=float(x[0]), ci_low=float(x[0]), ci_high=float(x[0]),
                    ci_low_seed_min=float(x[0]), ci_low_seed_max=float(x[0]), n_eff=1)
    b = max(1, min(int(block), n - 1))
    n_blocks = int(np.ceil(n / b))
    if n < 500:
        from xen.evaluation import block_bootstrap_ci
        r = block_bootstrap_ci(x, block=block, n_boot=n_boot, n_seeds=n_seeds, seed=seed)
        return dict(n=n, block=r["block"], stat=r["stat"], ci_low=r["ci"][0], ci_high=r["ci"][1],
                    ci_low_seed_min=r["ci_low_seed_range"][0],
                    ci_low_seed_max=r["ci_low_seed_range"][1], n_eff=n_blocks)
    xc = np.concatenate([x, x[: b - 1]]) if b > 1 else x
    cs = np.concatenate([[0.0], np.cumsum(xc)])
    bm = (cs[b:][:n] - cs[:n]) / b
    lo = np.empty(n_seeds)
    hi = np.empty(n_seeds)
    for s in range(n_seeds):
        rng = np.random.default_rng(seed + s)
        idx = rng.integers(0, n, size=(n_boot, n_blocks))
        stats = bm[idx].mean(axis=1)
        lo[s] = np.quantile(stats, 0.025)
        hi[s] = np.quantile(stats, 0.975)
    return dict(n=n, block=b, stat=float(x.mean()),
                ci_low=float(np.median(lo)), ci_high=float(np.median(hi)),
                ci_low_seed_min=float(lo.min()), ci_low_seed_max=float(lo.max()),
                n_eff=n_blocks)


def summarise(d: np.ndarray, lens: str) -> dict:
    if len(d) == 0:
        return {f"{lens}_n": 0, f"{lens}_estimate_bps": float("nan"),
                f"{lens}_ci_low": float("nan"), f"{lens}_ci_high": float("nan"),
                f"{lens}_effective_n": 0, f"{lens}_mde_bps": float("nan"),
                f"{lens}_median_bps": float("nan"),
                f"{lens}_ci_low_seed_min": float("nan"),
                f"{lens}_ci_low_seed_max": float("nan"),
                f"{lens}_ci_excludes_zero": False,
                f"{lens}_sd_bps": float("nan")}
    r = block_ci_mean(d)
    sd = float(np.std(d, ddof=1)) if len(d) > 1 else float("nan")
    return {
        f"{lens}_n": int(len(d)),
        f"{lens}_estimate_bps": r["stat"],
        f"{lens}_median_bps": float(np.median(d)),
        f"{lens}_ci_low": r["ci_low"],
        f"{lens}_ci_high": r["ci_high"],
        f"{lens}_ci_low_seed_min": r["ci_low_seed_min"],
        f"{lens}_ci_low_seed_max": r["ci_low_seed_max"],
        f"{lens}_ci_excludes_zero": bool(r["ci_low"] > 0 or r["ci_high"] < 0),
        f"{lens}_effective_n": r["n_eff"],
        f"{lens}_sd_bps": sd,
        f"{lens}_mde_bps": float(Z * sd / np.sqrt(r["n_eff"])) if r["n_eff"] else float("nan"),
    }


KEYS = ["symbol", "entry_variant", "component", "parameter", "orientation",
        "orientation_pair", "arm_id", "arm_class", "comparator_id"]


def run(universe: str) -> None:
    o = OUT / universe
    o.mkdir(parents=True, exist_ok=True)
    er = pl.scan_parquet(RUNS[universe] / "episode_results.parquet")
    fixed_filled = (
        er.filter((pl.col("arm_class") == "FIXED_NATIVE") & (pl.col("state") == "FILLED"))
        .select("origin_id", "entry_variant").unique()
        .with_columns(fixed_filled=pl.lit(True)).collect()
    )
    print(universe, "fixed-filled (origin,variant) pairs:", fixed_filled.height)

    lf = pl.scan_parquet(ART / universe / "native_parameter_shared_trades.parquet")
    symbols = sorted(lf.select(pl.col("symbol").unique()).collect().to_series().to_list())
    rows = []
    for sym in symbols:
        cols = KEYS + ["decision_ts", "origin_id", "paired_outcome_delta_bps",
                       "outcome_bps", "fixed_outcome_bps", "_exit_reason"]
        df = (lf.filter(pl.col("symbol") == sym).select(cols)
              .join(fixed_filled.lazy(), on=["origin_id", "entry_variant"], how="left")
              .with_columns(
                  fixed_filled=pl.col("fixed_filled").fill_null(False),
                  adaptive_filled=pl.col("_exit_reason").is_not_null())
              .sort("decision_ts").collect())
        for key, g in df.group_by(KEYS, maintain_order=True):
            af = g["adaptive_filled"].to_numpy()
            ff = g["fixed_filled"].to_numpy()
            d = g["paired_outcome_delta_bps"].to_numpy()
            rec = dict(zip(KEYS, key))
            rec.update(
                universe=universe,
                estimand="paired_adaptive_minus_fixed_outcome_bps",
                shared_rows=int(len(d)),
                distinct_origins=int(g["origin_id"].n_unique()),
                adaptive_traded=int(af.sum()),
                fixed_traded=int(ff.sum()),
                both_traded=int((af & ff).sum()),
                neither_traded=int((~af & ~ff).sum()),
                adaptive_trade_rate=float(af.mean()),
                fixed_trade_rate=float(ff.mean()),
                adaptive_mean_bps_all=float(g["outcome_bps"].mean()),
                fixed_mean_bps_all=float(g["fixed_outcome_bps"].mean()),
                adaptive_mean_bps_when_traded=float(g["outcome_bps"].to_numpy()[af].mean())
                if af.any() else float("nan"),
                fixed_mean_bps_when_traded=float(g["fixed_outcome_bps"].to_numpy()[ff].mean())
                if ff.any() else float("nan"),
            )
            rec.update(summarise(d, "L1_ALL"))
            rec.update(summarise(d[af | ff], "L2_EITHER"))
            rec.update(summarise(d[af & ff], "L3_BOTH"))
            rows.append(rec)
        del df
    out = pl.DataFrame(rows).sort(KEYS)
    out.write_parquet(o / "native_paired_per_stratum.parquet")
    out.write_csv(o / "native_paired_per_stratum.csv")
    print(universe, "strata", out.height,
          "L1 ci!=0", int(out["L1_ALL_ci_excludes_zero"].sum()),
          "L3 ci!=0", int(out["L3_BOTH_ci_excludes_zero"].sum()))


if __name__ == "__main__":
    for u in sys.argv[1:] or ["ctrader", "crypto"]:
        run(u)
