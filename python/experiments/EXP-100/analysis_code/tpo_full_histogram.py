"""Prototype: rebuild the full per-bin TPO histogram from catalog 1m bars.

Goal: verify the emitted ``tpo_total`` is reproducible from the raw 1-minute
catalog (conservation), then compute the "emptiest 30% of the ENTIRE TPO" — a
quantity the emission does not store (the emitted gap is the emptiest 30% of the
*value area* only).

Analysis-only: reads the same 1m catalog the engine consumed, TRAIN-bounded.
No experiment-local code imported; no strategy re-run.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_FLOOR
from pathlib import Path

import numpy as np
import polars as pl
from nautilus_trader.persistence.catalog import ParquetDataCatalog

REPO = Path(__file__).resolve().parents[4]
CELL = "ctrader-eurusd-15m-breakout_bar-1h-previous_1d"
CELL_DIR = REPO / "data/nautilus_runs/EXP-100/full" / CELL
OUT_DIR = REPO / "python/experiments/EXP-100/results/analysis"
CATALOG = REPO / "data/catalog_ctrader"
BAR_TYPE = "EURUSD.CTrader-1-MINUTE-LAST-EXTERNAL"
MINUTE_NS = 60_000_000_000


def _bin_index(price: float, bin_width: float) -> int:
    """Exact replica of ``TPOProfileStore._bin_index`` (Decimal ROUND_FLOOR)."""
    return int(
        (Decimal(str(price)) / Decimal(str(bin_width))).to_integral_value(
            rounding=ROUND_FLOOR
        )
    )


def load_catalog_bars() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    fence = json.loads((CELL_DIR / "fence_attestation.json").read_text())
    train_end = datetime.fromisoformat(
        fence["train_end_utc"].replace("Z", "+00:00")
    )
    start = datetime(2021, 6, 2, 0, 1, tzinfo=timezone.utc)
    catalog = ParquetDataCatalog(str(CATALOG))
    bars = catalog.bars(bar_types=[BAR_TYPE], start=start, end=train_end)
    ts = np.array([int(b.ts_event) for b in bars], dtype=np.int64)
    low = np.array([float(b.low) for b in bars], dtype=np.float64)
    high = np.array([float(b.high) for b in bars], dtype=np.float64)
    order = np.argsort(ts, kind="stable")
    return ts[order], low[order], high[order]


def _histogram_for_window(
    low: np.ndarray, high: np.ndarray, i0: int, i1: int, bin_width: float
) -> dict[int, int]:
    hist: dict[int, int] = defaultdict(int)
    for i in range(i0, i1):
        lo = _bin_index(float(low[i]), bin_width)
        hi = _bin_index(float(high[i]), bin_width)
        for b in range(lo, hi + 1):
            hist[b] += 1
    return dict(hist)


def emptiest_30pct_entire(hist: dict[int, int], total: int) -> dict:
    """Lowest-count bins across the WHOLE profile accumulating to 30% of mass."""
    target = 0.30 * total
    acc = 0
    n_bins = 0
    selected_min = None
    selected_max = None
    for bin_index, count in sorted(hist.items(), key=lambda kv: (kv[1], kv[0])):
        acc += count
        n_bins += 1
        selected_min = bin_index if selected_min is None else min(selected_min, bin_index)
        selected_max = bin_index if selected_max is None else max(selected_max, bin_index)
        if acc >= target:
            break
    return {
        "selected_count": n_bins,
        "outer_low_bin": selected_min,
        "outer_high_bin": selected_max,
        "mass": acc,
    }


def main() -> None:
    ts, low, high = load_catalog_bars()
    print(f"catalog 1m bars (TRAIN): {ts.size}")

    tpo = pl.read_parquet(CELL_DIR / "tpo_profiles.parquet")
    defined = tpo.filter(pl.col("profile_status") == "DEFINED")
    print(f"defined profiles: {defined.height}")

    # --- Conservation check over ALL profiles (exact Decimal binning) ---
    n_exact = 0
    n_mismatch = 0
    mismatches: list[dict] = []
    for row in defined.iter_rows(named=True):
        s = int(row["profile_start_ts_ns"])
        e = int(row["profile_end_ts_ns"])
        bw = float(row["bin_width"])
        i0 = int(np.searchsorted(ts, s, side="left"))
        i1 = int(np.searchsorted(ts, e, side="right"))
        total = 0
        for i in range(i0, i1):
            lo = _bin_index(float(low[i]), bw)
            hi = _bin_index(float(high[i]), bw)
            total += hi - lo + 1
        if total == int(row["tpo_total"]):
            n_exact += 1
        else:
            n_mismatch += 1
            if len(mismatches) < 10:
                mismatches.append(
                    {
                        "raid_id": row["raid_id"],
                        "recomputed": total,
                        "emitted": int(row["tpo_total"]),
                        "n_bars": i1 - i0,
                    }
                )

    conservation = {
        "cell": CELL,
        "n_profiles": defined.height,
        "n_exact": n_exact,
        "n_mismatch": n_mismatch,
        "exact_frac": n_exact / defined.height,
        "sample_mismatches": mismatches,
    }
    (OUT_DIR / "tpo_histogram_conservation.json").write_text(
        json.dumps(conservation, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(conservation, indent=2))

    # --- Sample: emptiest 30% of ENTIRE TPO vs emitted gap (30% of VA) ---
    sample = defined.sample(n=20, seed=7, with_replacement=False)
    rows: list[dict] = []
    for row in sample.iter_rows(named=True):
        s = int(row["profile_start_ts_ns"])
        e = int(row["profile_end_ts_ns"])
        bw = float(row["bin_width"])
        i0 = int(np.searchsorted(ts, s, side="left"))
        i1 = int(np.searchsorted(ts, e, side="right"))
        hist = _histogram_for_window(low, high, i0, i1, bw)
        total = sum(hist.values())
        e30 = emptiest_30pct_entire(hist, total)
        gap_mask = json.loads(row["gap_mask"]) if row["gap_mask"] else {}
        rows.append(
            {
                "raid_id": row["raid_id"],
                "tpo_total_recomputed": total,
                "tpo_total_emitted": int(row["tpo_total"]),
                "bin_width": bw,
                "atr_unit": float(row["atr_unit"]),
                "n_bins_full_profile": len(hist),
                "entire_30pct_selected_bins": e30["selected_count"],
                "entire_30pct_span_atr": (
                    (e30["outer_high_bin"] - e30["outer_low_bin"] + 1) * bw
                )
                / float(row["atr_unit"]),
                "entire_30pct_span_va": (
                    (e30["outer_high_bin"] - e30["outer_low_bin"] + 1) * bw
                )
                / float(row["va_width"])
                if float(row["va_width"]) > 0
                else None,
                "emitted_gap_span_atr": row["gap_span_atr"],
                "emitted_gap_span_va": row["gap_span_va"],
                "emitted_gap_selected_count": gap_mask.get("selected_count"),
                "tight_gap": row["tight_gap"],
            }
        )
    pl.DataFrame(rows).write_csv(OUT_DIR / "tpo_entire_30pct_sample.csv")
    print("\n=== emptiest-30%-of-ENTIRE-TPO vs emitted gap (20 profiles) ===")
    print(pl.DataFrame(rows))


if __name__ == "__main__":
    main()
