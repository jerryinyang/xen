"""Full-universe DESIGN-band coverage, gap-day excision, activity conditioning.

COUNT ONLY — no forward return, excursion, or outcome.

Produced for INFR-020 QA run 3 residuals S-2 / S-3 / S-4:
  - gap days derived from staging (UTC day with zero bars in the instrument's
    own DESIGN span), not from ledger timestamps (ledger has none)
  - retention distribution over all 194 A5-fitted instruments
  - COMPLETE-vs-partial median volume ratio (activity conditioning)

The zero-fill path is NOT used here; raw strict retention is the operative
object after AMENDMENT-6 withdrawal.
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
BASELINES = (
    Path(__file__).resolve().parents[2]
    / "INFR-017"
    / "results"
    / "seasonal_baselines.parquet"
)
LEDGER = (
    Path(__file__).resolve().parents[2]
    / "INFR-011"
    / "artifacts"
    / "admission-ledger.jsonl"
)


def retention_and_vol(bars: pl.DataFrame, period: int) -> dict:
    g = (
        bars.sort("OpenTime")
        .group_by_dynamic("OpenTime", every=f"{period}m", closed="left", label="left")
        .agg(pl.len().alias("n"), pl.col("Volume").sum().alias("vol"))
    )
    if g.height == 0:
        return {
            "retention": 0.0,
            "n_complete": 0,
            "n_partial": 0,
            "vol_ratio": None,
        }
    complete = g.filter(pl.col("n") == period)
    partial = g.filter(pl.col("n") < period)
    med_c = float(complete["vol"].median()) if complete.height else None
    med_p = float(partial["vol"].median()) if partial.height else None
    ratio = (
        (med_c / med_p)
        if (med_c is not None and med_p is not None and med_p > 0)
        else None
    )
    return {
        "retention": round(float((g["n"] == period).mean()), 4),
        "n_complete": complete.height,
        "n_partial": partial.height,
        "vol_ratio": round(ratio, 2) if ratio is not None else None,
    }


def gap_days_in_design(bars: pl.DataFrame) -> tuple[int, int]:
    """UTC days with zero bars inside the instrument's observed DESIGN span."""
    if bars.height == 0:
        return 0, 0
    t0d = bars["OpenTime"].min()
    t1d = bars["OpenTime"].max()
    span = pl.DataFrame(
        {"OpenTime": pl.datetime_range(t0d, t1d, interval="1d", eager=True)}
    ).with_columns(pl.col("OpenTime").dt.date().alias("d"))
    present = set(
        bars.select(pl.col("OpenTime").dt.date()).unique()["OpenTime"].to_list()
    )
    all_days = set(span["d"].to_list())
    return len(all_days - present), len(all_days)


def main() -> None:
    syms = sorted(
        pl.read_parquet(BASELINES)["symbol"].unique().to_list()
    )
    ledger: dict[str, dict] = {}
    for line in LEDGER.read_text().splitlines():
        r = json.loads(line)
        ledger[r["symbol"]] = r

    rows: list[dict] = []
    for i, s in enumerate(syms):
        bars = load_bars(s, "DESIGN")
        if bars.height == 0:
            rows.append({"symbol": s, "empty": True})
            continue
        n_gap, n_span = gap_days_in_design(bars)
        led = ledger.get(s, {})
        row = {
            "symbol": s,
            "empty": False,
            "n_bars": bars.height,
            "span_days": (bars["OpenTime"].max() - bars["OpenTime"].min()).days,
            "gap_days_in_band": n_gap,
            "span_days_calendar": n_span,
            "ledger_unresolved_error_days": led.get("unresolved_error_days"),
            "ledger_collection_gap_minutes": led.get("collection_gap_minutes"),
            "ledger_max_gap_run_min": led.get("max_gap_run_min"),
            "periods": {f"{p}m": retention_and_vol(bars, p) for p in PERIODS},
        }
        rows.append(row)
        if (i + 1) % 20 == 0:
            print(f"... {i + 1}/{len(syms)}", flush=True)

    out = Path(__file__).parent / "diag_universe_coverage.json"
    out.write_text(json.dumps(rows, indent=1))
    print(f"wrote {out} n={len(rows)}")


if __name__ == "__main__":
    main()
