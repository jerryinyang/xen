"""Designer-side verification trace for INFR-020 W2 (signed LTF aggregation).

Emits hand-checkable 1m -> 5m/15m/1h aggregations from real DESIGN-band bars,
including the taker split, so QA can diff the implementation against numbers the
designer derived independently of it.

The taker split is ADDITIVE across bars — BuyVolume and SellVolume are measured
counts, not estimates (A8 CONFIRMED) — so an aggregated bar's Delta is exact,
not inferred. That is the property this trace pins.

Run:  python/.venv/bin/python python/experiments/INFR-020/design_derivations/agg_trace.py
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


def aggregate_signed(bars: pl.DataFrame, period_minutes: int) -> pl.DataFrame:
    """Clock-aligned N-minute aggregation carrying the taker split.

    Strict retention: a window is kept only if it holds exactly
    ``period_minutes`` 1-minute bars, so an aggregated bar can never have an
    understated High/Low or a partial volume sum.
    """
    every = f"{period_minutes}m"
    return (
        bars.sort("OpenTime")
        .group_by_dynamic("OpenTime", every=every, closed="left", label="left")
        .agg(
            pl.col("Open").first(),
            pl.col("High").max(),
            pl.col("Low").min(),
            pl.col("Close").last(),
            pl.col("Volume").sum(),
            pl.col("BuyVolume").sum(),
            pl.col("SellVolume").sum(),
            pl.col("NTrades").sum(),
            pl.len().alias("SourceBars"),
        )
        .filter(pl.col("SourceBars") == period_minutes)
        .with_columns((pl.col("BuyVolume") - pl.col("SellVolume")).alias("Delta"))
    )


def main() -> None:
    symbol = "BTCUSDT"
    bars = load_bars(symbol, "DESIGN")
    # one pinned, fully-covered window
    window_start = pl.datetime(2022, 7, 15, 13, 0)
    out: dict = {"symbol": symbol, "band": "DESIGN", "traces": {}}

    for p in PERIODS:
        agg = aggregate_signed(bars, p)
        row = agg.filter(pl.col("OpenTime") == window_start)
        if row.height == 0:
            continue
        r = row.to_dicts()[0]
        src = bars.filter(
            (pl.col("OpenTime") >= window_start)
            & (pl.col("OpenTime") < window_start + pl.duration(minutes=p))
        )
        # independent re-derivation from the source minutes
        check = {
            "Open": float(src["Open"][0]),
            "High": float(src["High"].max()),
            "Low": float(src["Low"].min()),
            "Close": float(src["Close"][-1]),
            "Volume": float(src["Volume"].sum()),
            "BuyVolume": float(src["BuyVolume"].sum()),
            "SellVolume": float(src["SellVolume"].sum()),
            "Delta": float(src["BuyVolume"].sum() - src["SellVolume"].sum()),
            "n_source_bars": src.height,
        }
        agrees = all(
            abs(float(r[k]) - v) < 1e-9 for k, v in check.items() if k != "n_source_bars"
        )
        # the split must reconcile to total volume (A8 provenance property)
        split_gap = abs(float(r["BuyVolume"]) + float(r["SellVolume"]) - float(r["Volume"]))
        out["traces"][f"{p}m"] = {
            "OpenTime": str(r["OpenTime"]),
            "aggregated": {k: float(r[k]) for k in
                           ("Open", "High", "Low", "Close", "Volume",
                            "BuyVolume", "SellVolume", "Delta")},
            "SourceBars": int(r["SourceBars"]),
            "independent_recheck": check,
            "recheck_agrees": agrees,
            "buy_plus_sell_minus_volume": split_gap,
        }
        print(f"--- {p}m window {r['OpenTime']} ---")
        print(json.dumps(out["traces"][f"{p}m"], indent=1))

    Path(__file__).parent.joinpath("agg_trace.json").write_text(
        json.dumps(out, indent=1, default=str)
    )


if __name__ == "__main__":
    main()
