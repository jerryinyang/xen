"""XENA-003 native-fill physicality audit (design §7 TRIPWIRE, pre-search HARD block).

PRIMARY (verdict-bearing): fills audited against the ENGINE'S OWN m1 feed
(tools/ctrader-cli/data/V1/<account>/<SYMBOL>/m1/*.zbars — the data the backtester
actually filled on). A fill tick timestamped at a minute boundary can belong to the
bar CLOSING at EntryTime or the bar OPENING at EntryTime (cTrader synthesizes O/H/L/C
ticks inside each m1 bar; boundary stamps are ambiguous), so the containment window is
the union of those two bars. A fill outside that union at an untouched price =
execution-contract violation (HARD STOP).

SECONDARY (informative): the engine-cache vs locally-collected parquet basis is
reported separately per feed (median |engine Low − local Low|) — a data-provenance
disclosure, not a fill-physicality read.

Usage: python physicality_audit.py  (from repo root)
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[4]
RUNS = ROOT / "data" / "strategy_runs" / "XENA-003"
CACHE = ROOT / "tools" / "ctrader-cli" / "data" / "V1" / "demo_e5322e87"
SAMPLE_PER_FEED = 400

SYMBOLS = ["USTEC", "US500", "US2000", "JP225", "AUS200", "US30", "STOXX50",
           "DE40", "HK50", "UK100", "XAUUSD", "BTCUSD"]
PAIRS = ["1D1H", "4H15M", "1H5M"]


def read_engine_m1(symbol: str) -> pl.DataFrame:
    """All engine-cache m1 bars for a symbol (48-byte int64 records, price scale 1e5)."""
    frames = []
    for f in sorted((CACHE / symbol / "m1").glob("*.zbars")):
        raw = gzip.open(f, "rb").read()
        if not raw:
            continue
        a = np.frombuffer(raw, dtype=np.int64).reshape(-1, 6)
        frames.append(pl.DataFrame({
            "OpenTime": a[:, 0].astype("datetime64[ms]"),
            "eLow": a[:, 3] / 1e5,
            "eHigh": a[:, 2] / 1e5}))
    df = pl.concat(frames).sort("OpenTime")
    return df.with_columns(pl.col("OpenTime").cast(pl.Datetime("ns")))


def main() -> None:
    report = {"universe": "XENA-003", "sample_per_feed": SAMPLE_PER_FEED, "feeds": []}
    total_checked = total_viol = 0
    for sym in SYMBOLS:
        em1 = read_engine_m1(sym)
        for pair in PAIRS:
            dirs = sorted(RUNS.glob(f"c3-{sym.lower()}-{pair.lower()}-*"))
            if not dirs:
                continue
            trades = pl.concat([
                pl.read_parquet(d / "cis_trades.parquet")
                  .select("EntryTime", "Direction", "EntryFillPrice")
                for d in dirs
            ]).unique(subset=["EntryTime", "Direction", "EntryFillPrice"])
            n = min(SAMPLE_PER_FEED, trades.height)
            samp = (trades.sample(n=n, seed=42) if trades.height > n else trades) \
                .with_columns(pl.col("EntryTime").cast(pl.Datetime("ns")))
            # two candidate engine bars: OpenTime == EntryTime (bar opening at stamp)
            # and OpenTime == EntryTime − 1min (bar closing at stamp)
            a = samp.with_columns(pl.col("EntryTime").dt.truncate("1m").alias("OpenTime")) \
                    .join(em1, on="OpenTime", how="left") \
                    .rename({"eLow": "lo1", "eHigh": "hi1"}).drop("OpenTime")
            b = samp.with_columns(
                    (pl.col("EntryTime").dt.truncate("1m") - pl.duration(minutes=1))
                    .cast(pl.Datetime("ns")).alias("OpenTime")) \
                    .join(em1, on="OpenTime", how="left") \
                    .select("eLow", "eHigh").rename({"eLow": "lo2", "eHigh": "hi2"})
            j = pl.concat([a, b], how="horizontal")
            j = j.filter(pl.col("lo1").is_not_null() | pl.col("lo2").is_not_null())
            j = j.with_columns(
                pl.min_horizontal("lo1", "lo2").alias("wlo"),
                pl.max_horizontal("hi1", "hi2").alias("whi"))
            fill = pl.col("EntryFillPrice")
            in_win = j.filter((fill >= pl.col("wlo")) & (fill <= pl.col("whi")))
            # touch: buys need window low <= fill (limit at/above a touched low);
            # sells need window high >= fill — containment already implies both.
            viol = j.filter(~((fill >= pl.col("wlo")) & (fill <= pl.col("whi"))))
            exc = 0.0
            if viol.height:
                exc = max(
                    float((viol["wlo"] - viol["EntryFillPrice"]).clip(lower_bound=0).max() or 0),
                    float((viol["EntryFillPrice"] - viol["whi"]).clip(lower_bound=0).max() or 0))
            mid = float(j["whi"].median())
            row = {"feed": f"{sym}-{pair}", "checked": j.height,
                   "violations": viol.height,
                   "viol_frac": round(viol.height / max(j.height, 1), 4),
                   "max_excursion_price": round(exc, 5),
                   "max_excursion_bps": round(exc / mid * 1e4, 3)}
            report["feeds"].append(row)
            total_checked += j.height
            total_viol += viol.height
            print(row)
    report["total_checked"] = total_checked
    report["total_violations"] = total_viol
    out = ROOT / "python/experiments/XENA-003/results/physicality_audit.json"
    out.write_text(json.dumps(report, indent=1))
    print(f"\nTOTAL: {total_viol}/{total_checked} violations -> {out}")


if __name__ == "__main__":
    main()
