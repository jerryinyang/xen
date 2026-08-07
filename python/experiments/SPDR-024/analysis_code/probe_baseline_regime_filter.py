"""SPDR-024 operator probe: baseline FIXED_SIZE_UNIT by vol regime.

Does not import experiment-local analysis modules for numbers.
Writes CSVs under results/analysis/probes/.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results" / "analysis"
OUT = BASE / "probes"
CELLS = ["ctrader_H1", "ctrader_H4", "crypto_H1", "crypto_H4"]
N_BOOT = 2000
MDE_Z = 2.8


def block_bootstrap_mean_ci(x, n_boot=N_BOOT, seed=42):
    x = np.asarray(x, dtype=float)
    n = len(x)
    if n < 2:
        return dict(
            mean=float(np.mean(x)) if n else np.nan,
            ci_low=np.nan,
            ci_high=np.nan,
            se=np.nan,
            n=n,
            block=1,
        )
    block = max(1, min(n, int(round(np.sqrt(n)))))
    n_blocks = int(np.ceil(n / block))
    rng = np.random.default_rng(seed)
    means = np.empty(n_boot)
    for i in range(n_boot):
        starts = rng.integers(0, n - block + 1, size=n_blocks)
        samp = np.concatenate([x[s : s + block] for s in starts])[:n]
        means[i] = samp.mean()
    lo, hi = np.quantile(means, [0.025, 0.975])
    return dict(
        mean=float(x.mean()),
        ci_low=float(lo),
        ci_high=float(hi),
        se=float(means.std(ddof=1)),
        n=n,
        block=block,
    )


def block_bootstrap_diff_ci(a, b, n_boot=N_BOOT, seed=42):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return dict(
            diff=float(a.mean() - b.mean()) if na and nb else np.nan,
            ci_low=np.nan,
            ci_high=np.nan,
            se=np.nan,
            n_a=na,
            n_b=nb,
            block_a=1,
            block_b=1,
        )
    ba = max(1, min(na, int(round(np.sqrt(na)))))
    bb = max(1, min(nb, int(round(np.sqrt(nb)))))
    n_blocks_a = int(np.ceil(na / ba))
    n_blocks_b = int(np.ceil(nb / bb))
    rng = np.random.default_rng(seed)
    diffs = np.empty(n_boot)
    for i in range(n_boot):
        sa = np.concatenate(
            [a[s : s + ba] for s in rng.integers(0, na - ba + 1, size=n_blocks_a)]
        )[:na]
        sb = np.concatenate(
            [b[s : s + bb] for s in rng.integers(0, nb - bb + 1, size=n_blocks_b)]
        )[:nb]
        diffs[i] = sa.mean() - sb.mean()
    lo, hi = np.quantile(diffs, [0.025, 0.975])
    return dict(
        diff=float(a.mean() - b.mean()),
        ci_low=float(lo),
        ci_high=float(hi),
        se=float(diffs.std(ddof=1)),
        n_a=na,
        n_b=nb,
        block_a=ba,
        block_b=bb,
    )


def ci_tag(lo, hi):
    if not np.isfinite(lo) or not np.isfinite(hi):
        return "na"
    if lo > 0:
        return "ci+"
    if hi < 0:
        return "ci-"
    return "cross0"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows_cell, rows_symbol, rows_origin, rows_filter = [], [], [], []

    for cell in CELLS:
        ep = pd.read_parquet(BASE / cell / "episodes.parquet")
        b = ep[ep.arm_id == "FIXED_SIZE_UNIT"].copy()
        b = b.sort_values(["symbol", "decision_ts", "origin_id"]).reset_index(drop=True)
        b["regime"] = b["regime_state"].astype(str).fillna("UNKNOWN")

        for reg, g in b.groupby("regime", dropna=False):
            origins = len(g)
            orders = int(g.order_created.fillna(False).astype(bool).sum())
            fills = int(g.admitted.fillna(False).astype(bool).sum())
            rows_origin.append(
                dict(
                    cell=cell,
                    scope="POOLED",
                    symbol=None,
                    regime=reg,
                    n_origins=origins,
                    n_orders=orders,
                    n_fills=fills,
                    order_rate=orders / origins if origins else np.nan,
                    fill_rate_per_origin=fills / origins if origins else np.nan,
                    fill_rate_per_order=(fills / orders) if orders else np.nan,
                )
            )
        origins = len(b)
        orders = int(b.order_created.fillna(False).astype(bool).sum())
        fills = int(b.admitted.sum())
        rows_origin.append(
            dict(
                cell=cell,
                scope="POOLED",
                symbol=None,
                regime="ALL",
                n_origins=origins,
                n_orders=orders,
                n_fills=fills,
                order_rate=orders / origins if origins else np.nan,
                fill_rate_per_origin=fills / origins if origins else np.nan,
                fill_rate_per_order=(fills / orders) if orders else np.nan,
            )
        )

        for (sym, reg), g in b.groupby(["symbol", "regime"]):
            origins = len(g)
            orders = int(g.order_created.fillna(False).astype(bool).sum())
            fills = int(g.admitted.sum())
            rows_origin.append(
                dict(
                    cell=cell,
                    scope="PER_SYMBOL",
                    symbol=sym,
                    regime=reg,
                    n_origins=origins,
                    n_orders=orders,
                    n_fills=fills,
                    order_rate=orders / origins if origins else np.nan,
                    fill_rate_per_origin=fills / origins if origins else np.nan,
                    fill_rate_per_order=(fills / orders) if orders else np.nan,
                )
            )

        fills_df = b[b.admitted & b.outcome_bps.notna() & b.entry_ts.notna()].copy()
        fills_df = fills_df.sort_values(["symbol", "entry_ts", "origin_id"]).reset_index(
            drop=True
        )

        def summarize_perf(df, scope, symbol, regime):
            y = df["outcome_bps"].to_numpy(dtype=float)
            if len(y) == 0:
                return None
            seed = hash((cell, scope, str(symbol), regime)) % (2**31 - 1) or 1
            boot = block_bootstrap_mean_ci(y, seed=seed)
            return dict(
                cell=cell,
                scope=scope,
                symbol=symbol,
                regime=regime,
                n_fills=len(y),
                mean_bps=boot["mean"],
                ci_low=boot["ci_low"],
                ci_high=boot["ci_high"],
                se=boot["se"],
                mde_bps=MDE_Z * boot["se"] if np.isfinite(boot["se"]) else np.nan,
                ci_tag=ci_tag(boot["ci_low"], boot["ci_high"]),
                median_bps=float(np.median(y)),
                win_share=float((y > 0).mean()),
                p10=float(np.quantile(y, 0.1)),
                p90=float(np.quantile(y, 0.9)),
                sigma=float(np.std(y, ddof=1)) if len(y) > 1 else np.nan,
                block=boot.get("block"),
            )

        for reg in ["ALL", "HIGH", "LOW", "UNKNOWN"]:
            sub = fills_df if reg == "ALL" else fills_df[fills_df.regime == reg]
            r = summarize_perf(sub, "POOLED", None, reg)
            if r:
                rows_cell.append(r)

        hi = fills_df[fills_df.regime == "HIGH"]["outcome_bps"].to_numpy(float)
        lo = fills_df[fills_df.regime == "LOW"]["outcome_bps"].to_numpy(float)
        d = block_bootstrap_diff_ci(hi, lo, seed=hash((cell, "diff")) % (2**31 - 1) or 2)
        rows_filter.append(
            dict(
                cell=cell,
                scope="POOLED",
                symbol=None,
                contrast="HIGH_minus_LOW_mean_bps",
                **d,
                ci_tag=ci_tag(d["ci_low"], d["ci_high"]),
                mde_bps=MDE_Z * d["se"] if np.isfinite(d.get("se", np.nan)) else np.nan,
                high_mean=float(hi.mean()) if len(hi) else np.nan,
                low_mean=float(lo.mean()) if len(lo) else np.nan,
                high_win=float((hi > 0).mean()) if len(hi) else np.nan,
                low_win=float((lo > 0).mean()) if len(lo) else np.nan,
                only_high_vs_all=float(hi.mean() - fills_df.outcome_bps.mean())
                if len(hi)
                else np.nan,
                only_low_vs_all=float(lo.mean() - fills_df.outcome_bps.mean())
                if len(lo)
                else np.nan,
                high_share_of_fills=len(hi) / len(fills_df) if len(fills_df) else np.nan,
                trade_retention_if_only_HIGH=len(hi) / len(fills_df) if len(fills_df) else np.nan,
                trade_retention_if_only_LOW=len(lo) / len(fills_df) if len(fills_df) else np.nan,
            )
        )

        for sym, sg in fills_df.groupby("symbol"):
            for reg in ["ALL", "HIGH", "LOW"]:
                sub = sg if reg == "ALL" else sg[sg.regime == reg]
                r = summarize_perf(sub, "PER_SYMBOL", sym, reg)
                if r:
                    rows_symbol.append(r)
            hi = sg[sg.regime == "HIGH"]["outcome_bps"].to_numpy(float)
            lo = sg[sg.regime == "LOW"]["outcome_bps"].to_numpy(float)
            if len(hi) >= 5 and len(lo) >= 5:
                d = block_bootstrap_diff_ci(
                    hi, lo, seed=hash((cell, sym)) % (2**31 - 1) or 3
                )
                rows_filter.append(
                    dict(
                        cell=cell,
                        scope="PER_SYMBOL",
                        symbol=sym,
                        contrast="HIGH_minus_LOW_mean_bps",
                        **d,
                        ci_tag=ci_tag(d["ci_low"], d["ci_high"]),
                        mde_bps=MDE_Z * d["se"]
                        if np.isfinite(d.get("se", np.nan))
                        else np.nan,
                        high_mean=float(hi.mean()),
                        low_mean=float(lo.mean()),
                        high_win=float((hi > 0).mean()),
                        low_win=float((lo > 0).mean()),
                        only_high_vs_all=float(hi.mean() - sg.outcome_bps.mean()),
                        only_low_vs_all=float(lo.mean() - sg.outcome_bps.mean()),
                        high_share_of_fills=len(hi) / len(sg),
                        trade_retention_if_only_HIGH=len(hi) / len(sg),
                        trade_retention_if_only_LOW=len(lo) / len(sg),
                    )
                )

    pd.DataFrame(rows_cell).to_csv(OUT / "baseline_regime_performance_pooled.csv", index=False)
    pd.DataFrame(rows_symbol).to_csv(
        OUT / "baseline_regime_performance_persymbol.csv", index=False
    )
    pd.DataFrame(rows_origin).to_csv(OUT / "baseline_regime_origin_rates.csv", index=False)
    pd.DataFrame(rows_filter).to_csv(OUT / "baseline_regime_filter_contrasts.csv", index=False)
    print(f"wrote CSVs under {OUT}")


if __name__ == "__main__":
    main()
