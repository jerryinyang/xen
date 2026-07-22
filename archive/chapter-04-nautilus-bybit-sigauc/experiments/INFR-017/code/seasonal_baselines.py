"""INFR-017 W6/W7 — fit + freeze the A5 seasonal baselines; reconcile admission.

Source ``SIGNAL-SIGNED.md`` Phase 0: *"Seasonal baselines fitted per instrument
for volume, range, |Δ|, Δ/V, and spread (A5)."* A5 requires a fitted
**minute-of-day x day-of-week** baseline per instrument, never a flat rolling
mean, and requires ``|Δ|`` and ``Δ/V`` to be normalised **separately**.

Fitted on the **DESIGN bank only** (checkpoint-014 §5) so the CONFIRM bank stays
untouched through all Stage I tuning. Code-asserted, not merely intended.

Outputs are frozen apparatus: a parquet of per-instrument cells plus a manifest
carrying the sha256. Refitting after a downstream result is seen is a
governance violation (L-23).

Usage
-----
    python python/experiments/INFR-017/code/seasonal_baselines.py            # all admitted
    python python/experiments/INFR-017/code/seasonal_baselines.py --limit 20 # smoke
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import polars as pl
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from xen.sigbar.baselines import BASELINE_METRICS, MIN_CELL_OBS, fit_seasonal_baseline

# ---------------------------------------------------------------------------
# Constants — frozen (design.md §5)
# ---------------------------------------------------------------------------

# DESIGN bank upper bound. CONFIRM bank (>= this) is untouched by this item.
DESIGN_BANK_END = datetime(2023, 3, 1, tzinfo=timezone.utc).replace(tzinfo=None)
TRAIN_END = datetime(2023, 12, 18, tzinfo=timezone.utc).replace(tzinfo=None)
ANALYSIS_START = datetime(2021, 6, 29, 6, 53, tzinfo=timezone.utc).replace(tzinfo=None)

STAGING_DIR = "python/experiments/INFR-011/data/staging/bars"
ADMISSION_LEDGER = "python/experiments/INFR-011/artifacts/admission-ledger.jsonl"
RESULTS_DIR = "python/experiments/INFR-017/results"


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------


def _repo_root() -> Path:
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("repo root not found")


def load_admission(root: Path) -> dict[str, dict[str, Any]]:
    """Read the INFR-011 admission ledger keyed by symbol."""
    out: dict[str, dict[str, Any]] = {}
    with (root / ADMISSION_LEDGER).open() as fh:
        for line in fh:
            rec = json.loads(line)
            out[rec["symbol"]] = rec
    return out


def sha256_file(path: Path) -> str:
    """Stream a file's sha256 (artifacts are large; do not slurp)."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Pure computation
# ---------------------------------------------------------------------------


def load_design_bank_bars(path: Path) -> pl.DataFrame:
    """Load one symbol's DESIGN-bank bars with the A5 metrics derived.

    Fence assertion is code-level: the filter bounds the read, and the caller
    re-asserts the realised max timestamp.
    """
    df = (
        pl.scan_parquet(path)
        .select(
            ["OpenTime", "Open", "High", "Low", "Close", "Volume",
             "BuyVolume", "SellVolume", "NTrades", "SpreadBps"]
        )
        .filter(
            (pl.col("OpenTime") >= ANALYSIS_START) & (pl.col("OpenTime") < DESIGN_BANK_END)
        )
        .collect()
    )
    if df.is_empty():
        return df
    return df.with_columns(
        (pl.col("High") - pl.col("Low")).alias("range"),
        (pl.col("BuyVolume") - pl.col("SellVolume")).alias("delta"),
        pl.col("Volume").alias("volume"),
        pl.col("SpreadBps").alias("spread"),
    ).with_columns(
        pl.col("delta").abs().alias("delta_abs"),
        # Δ/V is bounded in [-1, 1] and is a DIFFERENT object from |Δ| (A5).
        pl.when(pl.col("Volume") > 0)
        .then(pl.col("delta") / pl.col("Volume"))
        .otherwise(None)
        .alias("delta_ratio"),
    )


def fit_symbol(symbol: str, path: Path) -> tuple[pl.DataFrame | None, dict[str, Any]]:
    """Fit all A5 baselines for one instrument; return cells + a coverage record."""
    bars = load_design_bank_bars(path)
    if bars.is_empty():
        return None, {"symbol": symbol, "status": "NO_DESIGN_BANK_BARS", "n_bars": 0}

    realised_max = bars["OpenTime"].max()
    if realised_max >= DESIGN_BANK_END:
        raise RuntimeError(
            f"FENCE VIOLATION: {symbol} max OpenTime {realised_max} >= DESIGN bank end"
        )

    frames, sparse_rates = [], {}
    for metric in BASELINE_METRICS:
        cells = fit_seasonal_baseline(bars, metric)
        if cells.is_empty():
            sparse_rates[metric] = None
            continue
        sparse_rates[metric] = {
            "fallback_rate": round(float(cells["sparse"].mean()), 4),
            "empty_cell_rate": round(float((cells["n"] == 0).mean()), 4),
            "thin_but_nonempty_rate": round(
                float(((cells["n"] > 0) & cells["sparse"]).mean()), 4
            ),
        }
        frames.append(cells.with_columns(pl.lit(symbol).alias("symbol")))

    if not frames:
        return None, {"symbol": symbol, "status": "NO_CELLS", "n_bars": bars.height}

    record = {
        "symbol": symbol,
        "status": "OK",
        "n_bars": bars.height,
        "first_bar": str(bars["OpenTime"].min()),
        "last_bar": str(realised_max),
        "cell_coverage": sparse_rates,  # fallback / empty / thin-but-nonempty, on the FULL grid
        "spread_null_rate": round(float(bars["spread"].is_null().mean()), 4),
    }
    return pl.concat(frames), record


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="fit only the first N symbols")
    args = ap.parse_args()

    root = _repo_root()
    staging = root / STAGING_DIR
    results = root / RESULTS_DIR
    results.mkdir(parents=True, exist_ok=True)

    admission = load_admission(root)
    staged = sorted(p.stem for p in staging.glob("*.parquet"))

    # ---- W7: admission reconciliation (staging files vs admitted ledger) ----
    admitted = {s for s, r in admission.items() if r.get("admission") == "ADMITTED"}
    recon = {
        "item": "INFR-017",
        "work_item": "W7",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "n_staging_files": len(staged),
        "n_ledger_rows": len(admission),
        "n_admitted": len(admitted),
        "staged_not_admitted": sorted(set(staged) - admitted),
        "admitted_not_staged": sorted(admitted - set(staged)),
        "admission_values": {},
        "rule": "the signed lane inherits ADMITTED status; non-ADMITTED symbols are excluded with a reason",
    }
    vals: dict[str, int] = {}
    for r in admission.values():
        vals[str(r.get("admission"))] = vals.get(str(r.get("admission")), 0) + 1
    recon["admission_values"] = vals
    # Band coverage of the admitted cross-section. These numbers drive the
    # checkpoint-014 §6 universe wording and the SPDR-008 breadth claim, so they
    # are emitted here rather than asserted in prose (QA run 2, Issue 3).
    def _first_bar(sym: str):
        fb = admission[sym].get("first_bar")
        return datetime.fromisoformat(str(fb)) if fb else None

    design_ok = [s_ for s_ in admitted if (_fb := _first_bar(s_)) and _fb < DESIGN_BANK_END]
    train_ok = [s_ for s_ in admitted if (_fb := _first_bar(s_)) and _fb < TRAIN_END]
    recon["band_coverage"] = {
        "note": (
            "the 4-year trailing history cap plus late listings mean most admitted "
            "instruments have no readable TRAIN data; breadth is bounded by these counts, "
            "not by the admitted total"
        ),
        "n_admitted": len(admitted),
        "n_with_bars_before_train_end": len(train_ok),
        "train_end_utc": TRAIN_END.isoformat() + "Z",
        "n_with_bars_before_design_bank_end": len(design_ok),
        "design_bank_end_utc": DESIGN_BANK_END.isoformat() + "Z",
        "survivorship_caveat": (
            "instruments with DESIGN-bank data are precisely those listed before the "
            "bank end — a survivorship-shaped subset of the cross-section"
        ),
    }
    recon["excluded_with_reason"] = [
        {"symbol": s, "admission": admission[s].get("admission"),
         "spec_source": admission[s].get("spec_source"),
         "invariants_pass": admission[s].get("invariants_pass")}
        for s in sorted(set(staged) - admitted)
    ]
    (results / "admission_reconciliation.json").write_text(json.dumps(recon, indent=2))
    print(f"W7 admission: {len(staged)} staged, {len(admitted)} admitted, "
          f"{len(recon['staged_not_admitted'])} staged-not-admitted")

    # ---- W6: seasonal baselines over the admitted set ----
    targets = [s for s in staged if s in admitted]
    if args.limit:
        targets = targets[: args.limit]

    all_cells, records = [], []
    for symbol in tqdm(targets, desc="A5 baselines", unit="symbol"):
        try:
            cells, rec = fit_symbol(symbol, staging / f"{symbol}.parquet")
        except Exception as exc:  # noqa: BLE001 - recorded, never silently dropped
            records.append({"symbol": symbol, "status": "ERROR", "error": str(exc)})
            continue
        records.append(rec)
        if cells is not None:
            all_cells.append(
                cells.select(
                    pl.col("symbol"),
                    pl.col("metric"),
                    pl.col("mod").cast(pl.Int16),
                    pl.col("dow").cast(pl.Int8),
                    pl.col("loc").cast(pl.Float32),
                    pl.col("scale").cast(pl.Float32),
                    pl.col("n").cast(pl.Int32),
                    pl.col("sparse"),
                )
            )

    if not all_cells:
        print("no baselines fitted", file=sys.stderr)
        return 1

    out_parquet = results / "seasonal_baselines.parquet"
    pl.concat(all_cells).write_parquet(out_parquet, compression="zstd")

    manifest = {
        "item": "INFR-017",
        "work_item": "W6",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source": "SIGNAL-SIGNED.md A5 / Phase 0",
        "frozen_parameters": {
            "metrics": list(BASELINE_METRICS),
            "grid": "1440 minute-of-day x 7 day-of-week = 10080 cells per instrument per metric",
            "location": "median",
            "scale": "1.4826 * MAD",
            "min_cell_obs": MIN_CELL_OBS,
            "sparse_fallback": "day-of-week marginal",
            "fit_band": {
                "name": "DESIGN bank",
                "start_utc": ANALYSIS_START.isoformat() + "Z",
                "end_utc_exclusive": DESIGN_BANK_END.isoformat() + "Z",
            },
            "delta_note": "|delta| and delta/V fitted SEPARATELY per A5",
        },
        "n_symbols_fitted": sum(r.get("status") == "OK" for r in records),
        "n_symbols_attempted": len(targets),
        "artifact": str(out_parquet.relative_to(root)),
        "artifact_sha256": sha256_file(out_parquet),
        "per_symbol": records,
    }
    (results / "seasonal_baselines_manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"\nW6 baselines -> {out_parquet.relative_to(root)}")
    print(f"  symbols fitted: {manifest['n_symbols_fitted']} / {len(targets)}")
    print(f"  sha256: {manifest['artifact_sha256'][:16]}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
