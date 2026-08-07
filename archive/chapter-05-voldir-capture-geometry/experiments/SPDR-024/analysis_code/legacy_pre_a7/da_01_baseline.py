"""QUARANTINED pre-AMENDMENT-7. Do not use for emission or analysis.md."""
raise RuntimeError(
    "AMENDMENT_7_QUARANTINE: this script is legacy (pre R1-R5 floor fix). "
    "Use analysis_code/analyse.py emission only; see legacy_pre_a7/README.md."
)

"""Data-analyst (fresh context) — baseline characterisation, OD-3.

Independent of experiments/SPDR-024/analysis_code/analyse.py.
Reads only episodes.parquet emissions.
"""
from __future__ import annotations
import json
import numpy as np
import polars as pl

CELLS = ["ctrader_H1", "ctrader_H4", "crypto_H1", "crypto_H4"]
ROOT = "experiments/SPDR-024/results/analysis"


def load(cell: str) -> pl.DataFrame:
    return pl.read_parquet(f"{ROOT}/{cell}/episodes.parquet")


def q(x, p):
    return float(np.quantile(x, p)) if len(x) else float("nan")


out = {}
for cell in CELLS:
    d = load(cell)
    b = d.filter(pl.col("arm_id") == "FIXED_BASELINE_PLAIN")
    su = d.filter(pl.col("arm_id") == "FIXED_SIZE_UNIT")
    filled = su.filter(pl.col("exit_ts").is_not_null())
    o = filled["outcome_bps"].to_numpy()
    cn = filled["capital_normalised_return_bps"].to_numpy()
    rec = {
        "origins": su.height,
        "orders_created": su.filter(pl.col("state") == "ORDER_CREATED").height,
        "filled_trades": filled.height,
        "censored": int(su["censored"].sum()),
        "fill_rate_of_orders": filled.height / max(su.filter(pl.col("state") == "ORDER_CREATED").height, 1),
        "order_rate_of_origins": su.filter(pl.col("state") == "ORDER_CREATED").height / su.height,
        "gross_mean_bps": float(o.mean()),
        "gross_median_bps": float(np.median(o)),
        "gross_sd_bps": float(o.std(ddof=1)),
        "gross_total_bps": float(o.sum()),
        "win_share": float((o > 0).mean()),
        "zero_share": float((o == 0).mean()),
        "q01": q(o, 0.01), "q05": q(o, 0.05), "q25": q(o, 0.25),
        "q75": q(o, 0.75), "q95": q(o, 0.95), "q99": q(o, 0.99),
        "skew": float(((o - o.mean()) ** 3).mean() / o.std() ** 3),
        "kurt": float(((o - o.mean()) ** 4).mean() / o.std() ** 4),
        "mean_win_bps": float(o[o > 0].mean()) if (o > 0).any() else None,
        "mean_loss_bps": float(o[o < 0].mean()) if (o < 0).any() else None,
        "cn_equals_outcome_share": float(np.mean(np.isclose(o, cn))),
        "risk_size_unique": sorted(set(np.round(filled["risk_size"].to_numpy(), 6)))[:5],
        "hold_bars_realised": {
            "min": float(filled["hold_bars_realised"].min()),
            "median": float(filled["hold_bars_realised"].median()),
            "max": float(filled["hold_bars_realised"].max()),
        },
        "exit_reason": filled["exit_reason"].value_counts().to_dicts(),
        "regime_state": filled["regime_state"].value_counts().to_dicts(),
        "state_counts": su["state"].value_counts().to_dicts(),
    }
    # break-even win share (gross, no cost): W/L ratio
    w = o[o > 0]
    losses = o[o < 0]
    if len(w) and len(losses):
        rec["breakeven_win_share_gross"] = float(abs(losses.mean()) / (w.mean() + abs(losses.mean())))
    # per symbol
    per = []
    for sym, g in filled.group_by("symbol"):
        oo = g["outcome_bps"].to_numpy()
        per.append({"symbol": sym[0], "n": len(oo), "mean_bps": float(oo.mean()),
                    "median_bps": float(np.median(oo)), "win_share": float((oo > 0).mean()),
                    "sd": float(oo.std(ddof=1)), "total_bps": float(oo.sum())})
    rec["per_symbol"] = sorted(per, key=lambda r: -r["mean_bps"])
    # concentration: drop top-k winners
    srt = np.sort(o)[::-1]
    tot = o.sum()
    rec["concentration"] = {f"total_without_top_{k}": float(tot - srt[:k].sum()) for k in (1, 3, 5, 10)}
    rec["concentration"]["total"] = float(tot)
    # per-year
    yr = filled.with_columns(pl.col("entry_ts").dt.year().alias("y")).group_by("y").agg(
        pl.len(), pl.col("outcome_bps").mean().alias("mean"), pl.col("outcome_bps").sum().alias("tot"))
    rec["per_year"] = sorted(yr.to_dicts(), key=lambda r: r["y"])
    # exposure: fraction of domain bars occupied by the baseline
    dom_ns = 3600e9 if cell.endswith("H1") else 4 * 3600e9
    span = (filled["exit_ts"].max() - filled["entry_ts"].min()).total_seconds() * 1e9
    nsym = filled["symbol"].n_unique()
    held_bars = float(filled["hold_bars_realised"].sum())
    rec["occupancy_baseline"] = held_bars * dom_ns / (span * nsym)
    # arm B (uncapped) for the hold/decay question
    ab = d.filter(pl.col("arm_id") == "UNCAPPED_HOLD_SAFETY_CEILING").filter(pl.col("exit_ts").is_not_null())
    rec["armB"] = {
        "closed": ab.height,
        "hold_bars_realised_dist": {p: q(ab["hold_bars_realised"].to_numpy(), v)
                                    for p, v in [("p01", .01), ("p50", .5), ("p99", .99)]},
        "max": float(ab["hold_bars_realised"].max()),
        "exit_reason": ab["exit_reason"].value_counts().to_dicts(),
        "cap_binds_share": float(ab["hold_cap_binds"].mean()),
        "mean_outcome_bps": float(ab["outcome_bps"].mean()),
        "win_share": float((ab["outcome_bps"].to_numpy() > 0).mean()),
    }
    out[cell] = rec

print(json.dumps(out, indent=1, default=str))
