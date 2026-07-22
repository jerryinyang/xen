"""Measured coverage premise for INFR-020 W1/§5 — COUNT ONLY, no outcome.

QA run 1 (I-3) found the design's coverage premise ASSERTED and false: a
seasonal cell is (slot-of-day x day-of-week), which recurs once per WEEK at
every timeframe, so observations per cell are CONSTANT in bar size, not rising.
And under strict retention a coarse window needs every one of its N source
minutes, so retention falls as p^(N-1) — the reverse of what the design claimed.

This script measures both, before and after ZERO-FILLING no-trade minutes.

REVISION 3 (QA run 2): the zero-fill this script evaluates is WITHDRAWN from
every primary path — see diag_fill_bias.py, which shows it manufactures the
absorption signature on thin instruments. The "raw" columns are the operative
ones; the "zero_filled" columns are retained as the pinned evidence for the
withdrawal.

Two claims in the original version of this docstring were FALSE and are
corrected: `outage_minutes = 0` does hold for every instrument, but
`collection_gap_minutes = 0` holds for only 157 of the 194-instrument universe —
37 have real collection gaps, up to 138,240 minutes. A missing minute is
therefore NOT unconditionally a zero-trade minute.

No forward return, excursion or outcome is computed anywhere in this file.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from xen.sigbar.fences import load_bars  # noqa: E402

PERIODS = (5, 15, 60)


def zero_fill(bars: pl.DataFrame) -> pl.DataFrame:
    """Reconstruct no-trade minutes: flat at the prior close, zero flow.

    WITHDRAWN from every primary path at revision 3 (QA-2 R-2): on thin
    instruments this manufactures the absorption signature. Retained ONLY as the
    pinned evidence for that withdrawal — see diag_fill_bias.py. Delta/Turnover
    are set explicitly on filled rows (QA-2 R-8) so the artifact matches the
    spec it is refuting.
    """
    full = pl.DataFrame(
        {
            "OpenTime": pl.datetime_range(
                bars["OpenTime"].min(),
                bars["OpenTime"].max(),
                interval="1m",
                eager=True,
            )
        }
    )
    out = (
        full.join(bars, on="OpenTime", how="left")
        .sort("OpenTime")
        .with_columns(pl.col("Close").forward_fill())
        .with_columns(
            [pl.col(c).fill_null(pl.col("Close")) for c in ("Open", "High", "Low")]
            + [pl.col(c).fill_null(0.0) for c in
               ("Volume", "BuyVolume", "SellVolume", "NTrades")]
            + [pl.lit(0.0).alias("Delta"), pl.lit(0.0).alias("Turnover")]
        )
        .drop_nulls("Close")
    )
    return out


def retention(bars: pl.DataFrame, period: int) -> float:
    g = (
        bars.sort("OpenTime")
        .group_by_dynamic("OpenTime", every=f"{period}m", closed="left", label="left")
        .agg(pl.len().alias("n"))
    )
    if g.height == 0:
        return 0.0
    return float((g["n"] == period).mean())


def obs_per_cell(bars: pl.DataFrame, period: int) -> dict:
    """Observations per (slot-of-day x day-of-week) cell at this bar size."""
    agg = (
        bars.sort("OpenTime")
        .group_by_dynamic("OpenTime", every=f"{period}m", closed="left", label="left")
        .agg(pl.len().alias("n"))
        .filter(pl.col("n") == period)
    )
    if agg.height == 0:
        return {"cells": 0, "median_obs": 0, "frac_cells_below_8": 1.0}
    slots_per_day = 1440 // period
    c = (
        agg.with_columns(
            # The Int32 casts are load-bearing: polars returns hour()/minute()
            # as Int8, so hour*60 overflows for every hour >= 3 and the grid
            # collapses to aliased buckets. Same discipline as
            # baselines._with_seasonal_keys (INFR-017 QA run 1, Issue 1).
            (
                (
                    pl.col("OpenTime").dt.hour().cast(pl.Int32) * 60
                    + pl.col("OpenTime").dt.minute().cast(pl.Int32)
                )
                // period
            ).alias("slot"),
            pl.col("OpenTime").dt.weekday().cast(pl.Int32).alias("dow"),
        )
        .group_by("slot", "dow")
        .agg(pl.len().alias("obs"))
    )
    total_cells = slots_per_day * 7
    below = int((c["obs"] < 8).sum()) + (total_cells - c.height)
    return {
        "cells": total_cells,
        "cells_populated": c.height,
        "median_obs": float(c["obs"].median()),
        "frac_cells_below_8": round(below / total_cells, 4),
    }


def main() -> None:
    syms = sys.argv[1:] or ["BTCUSDT", "ETHUSDT", "SOLUSDT", "LTCUSDT", "CRVUSDT"]
    out = []
    for s in syms:
        bars = load_bars(s, "DESIGN")
        if bars.height == 0:
            continue
        filled = zero_fill(bars)
        span_days = (bars["OpenTime"].max() - bars["OpenTime"].min()).days
        row = {
            "symbol": s,
            "n_bars_raw": bars.height,
            "n_bars_zero_filled": filled.height,
            "no_trade_minutes_reconstructed": filled.height - bars.height,
            "span_days": span_days,
            "weeks": round(span_days / 7, 1),
            "raw": {}, "zero_filled": {},
        }
        for p in PERIODS:
            row["raw"][f"{p}m"] = {
                "retention": round(retention(bars, p), 4),
                **obs_per_cell(bars, p),
            }
            row["zero_filled"][f"{p}m"] = {
                "retention": round(retention(filled, p), 4),
                **obs_per_cell(filled, p),
            }
        out.append(row)
        print(json.dumps(row, indent=1))
    Path(__file__).parent.joinpath("diag_coverage.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
