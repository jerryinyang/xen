"""Does the W2a zero-fill manufacture the absorption signature? COUNT ONLY.

QA run 2 (R-2, blocking) found the fill was measured on COVERAGE but never on
the EVENT POPULATION. A mostly-reconstructed window has near-zero range but
keeps the real volume of its few traded minutes, so it can residualise as
"heavy volume, no result" — the absorption signature itself, manufactured.

This script measures, per (symbol, timeframe), raw vs zero-filled:
  - the p10 range-residual cut and the fraction of bars with range == 0
  - candidate counts under the effort/no-result predicate
  - what fraction of candidates touch a reconstructed minute

No forward outcome is computed anywhere.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from diag_coverage import zero_fill  # noqa: E402

from xen.sigbar.baselines import fit_seasonal_baseline, residualise  # noqa: E402
from xen.sigbar.fences import load_bars  # noqa: E402

PERIODS = (5, 15)


def agg(bars: pl.DataFrame, period: int, *, track_fill: bool) -> pl.DataFrame:
    aggs = [
        pl.col("Open").first(), pl.col("High").max(), pl.col("Low").min(),
        pl.col("Close").last(), pl.col("Volume").sum(),
        pl.col("BuyVolume").sum(), pl.col("SellVolume").sum(),
        pl.len().alias("SourceBars"),
    ]
    if track_fill:
        aggs.append(pl.col("is_fill").sum().alias("n_reconstructed"))
    out = (
        bars.sort("OpenTime")
        .group_by_dynamic("OpenTime", every=f"{period}m", closed="left", label="left")
        .agg(aggs)
        .filter(pl.col("SourceBars") == period)
    )
    if not track_fill:
        out = out.with_columns(pl.lit(0).alias("n_reconstructed"))
    return out.with_columns(
        (pl.col("High") - pl.col("Low")).alias("range"),
        pl.col("Volume").alias("volume"),
        ((pl.col("SourceBars") - pl.col("n_reconstructed")) / pl.col("SourceBars"))
        .alias("traded_frac"),
    )


def probe(symbol: str) -> dict:
    raw = load_bars(symbol, "DESIGN")
    if raw.height == 0:
        return {}
    filled = zero_fill(raw).with_columns(
        (pl.col("Volume") == 0).alias("is_fill")
    )
    row: dict = {"symbol": symbol, "n_raw": raw.height, "n_filled": filled.height}
    for p in PERIODS:
        a_raw = agg(raw.with_columns(pl.lit(False).alias("is_fill")), p, track_fill=True)
        a_fil = agg(filled, p, track_fill=True)
        cell: dict = {}
        for label, a in (("raw", a_raw), ("filled", a_fil)):
            if a.height == 0:
                cell[label] = {"n_bars": 0}
                continue
            r = a
            for m in ("volume", "range"):
                bl = fit_seasonal_baseline(r, m, time_col="OpenTime")
                r = residualise(r, bl, m, time_col="OpenTime")
            v_hi = r["volume_resid"].drop_nulls().quantile(0.90)
            r_lo = r["range_resid"].drop_nulls().quantile(0.10)
            cand = r.filter(
                (pl.col("volume_resid") >= v_hi) & (pl.col("range_resid") <= r_lo)
            )
            n_touch = cand.filter(pl.col("n_reconstructed") > 0).height
            cell[label] = {
                "n_bars": a.height,
                "frac_range_zero": round(float((a["range"] == 0).mean()), 4),
                "p10_range_resid": round(float(r_lo), 6),
                "n_candidates": cand.height,
                "n_candidates_touching_fill": n_touch,
                "frac_candidates_touching_fill": (
                    round(n_touch / cand.height, 3) if cand.height else None
                ),
                "median_traded_frac_of_candidates": (
                    round(float(cand["traded_frac"].median()), 3) if cand.height else None
                ),
            }
        row[f"{p}m"] = cell
    return row


def main() -> None:
    syms = sys.argv[1:] or ["ALICEUSDT", "SKLUSDT", "CRVUSDT", "LTCUSDT", "SOLUSDT"]
    out = []
    for s in syms:
        try:
            r = probe(s)
        except Exception as exc:  # noqa: BLE001
            print(f"{s}: {type(exc).__name__}: {exc}")
            continue
        if r:
            out.append(r)
            print(json.dumps(r, indent=1))
    Path(__file__).parent.joinpath("diag_fill_bias.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
