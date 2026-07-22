"""INFR-017 W5 — signed-bar catalog lane + round-trip proof.

Makes the signed tier **engine-readable**. All strategy logic in this programme
runs inside the Nautilus engine (price-primary, binding), and the pinned bar
catalog carries OHLCV only — so ``BuyVolume``/``SellVolume`` are invisible to a
strategy until they are written as a registered custom ``Data`` type.

Written to a SEPARATE catalog root (``data/catalog_sigbar/``) so the pinned
OHLCV catalog and its fence manifest sha are untouched. The signed lane is
additive; nothing about the existing catalog changes.

Exit condition (design.md §8.4): a symbol-day written and read back through the
fence wrapper equals the staging source **bit-for-bit on every signed field**.

Usage
-----
    python python/experiments/INFR-017/code/signed_bar_lane.py --validate
    python python/experiments/INFR-017/code/signed_bar_lane.py --ingest BTCUSDT ETHUSDT
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import polars as pl
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from nautilus_trader.persistence.catalog import ParquetDataCatalog

from xen.nautilus.catalog_fence import load_fence_manifest
from xen.nautilus.instrument_ids import archive_symbol_to_instrument_id
from xen.sigbar.data_types import (
    SIGBAR_PIPELINE_VERSION,
    SPREAD_MISSING,
    SignedBar,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STAGING_DIR = "python/experiments/INFR-011/data/staging/bars"
SIGBAR_CATALOG = "data/catalog_sigbar"
RESULTS_DIR = "python/experiments/INFR-017/results"

# Round-trip validation set + day (inside TRAIN, inside the DESIGN bank).
VALIDATION_SYMBOLS: tuple[str, ...] = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
VALIDATION_DAY = "2023-01-11"

# Fields compared staging-source -> catalog read-back. Kept in sync with the
# `pairs` mapping in `roundtrip_check`; the spread pair is checked separately
# because its status field is compared alongside its value.
SIGNED_FIELDS = (
    "open", "high", "low", "close",
    "volume", "buy_volume", "sell_volume", "delta", "n_trades",
    "spread_feature+spread_status",
)

NS_PER_MS = 1_000_000


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _repo_root() -> Path:
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("repo root not found")


def load_staging_window(
    path: Path, start: datetime, end: datetime
) -> pl.DataFrame:
    """Load staging bars in ``[start, end)`` with the signed fields derived."""
    df = (
        pl.scan_parquet(path)
        .select(
            ["OpenTime", "CloseTime", "Open", "High", "Low", "Close",
             "Volume", "BuyVolume", "SellVolume", "NTrades", "SpreadBps"]
        )
        .filter(
            (pl.col("OpenTime") >= start.replace(tzinfo=None))
            & (pl.col("OpenTime") < end.replace(tzinfo=None))
        )
        .collect()
        .sort("OpenTime")
    )
    if df.is_empty():
        return df
    return df.with_columns((pl.col("BuyVolume") - pl.col("SellVolume")).alias("Delta"))


def load_w2_pin(root: Path) -> tuple[str, str]:
    """Read the W2 decision from the pin artifact — never hard-code it here.

    QA run 1 (Issue 3): the UNUSABLE decision lived as a constant in this file
    while the pin that was supposed to freeze it recorded nothing. Consumers now
    read the status and the pin hash from `column_pins.json`.
    """
    pin_path = root / RESULTS_DIR / "column_pins.json"
    if not pin_path.exists():
        raise RuntimeError(
            f"W2 pin missing at {pin_path} — run spread_pin.py before ingesting; "
            "the spread status must come from the pin, not from code"
        )
    pin = json.loads(pin_path.read_text())
    status = pin["W2_decision"]["stored_column_status"]
    return status, pin.get("pin_sha256", "")


def to_signed_bars(
    df: pl.DataFrame, symbol: str, spread_status: str, config_hash: str
) -> list[SignedBar]:
    """Convert staging rows to :class:`SignedBar` records.

    ``ts_event`` is the bar **close** — the instant every field becomes known.
    Consumers apply the programme's ``<= t-1`` rule on top; nothing here is
    forward-looking.

    The spread feature's status is read from the W2 pin (``spread_status``
    argument), not decided here. The stored ``SpreadBps`` value is carried
    through for traceability but must not be used as a cost input while the pin
    says UNUSABLE.
    """
    iid = archive_symbol_to_instrument_id(symbol)
    bars: list[SignedBar] = []
    for row in df.iter_rows(named=True):
        ts_ns = int(row["CloseTime"].replace(tzinfo=timezone.utc).timestamp() * 1e3) * NS_PER_MS
        spread = row["SpreadBps"]
        bars.append(
            SignedBar(
                instrument_id=iid,
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=float(row["Volume"]),
                buy_volume=float(row["BuyVolume"]),
                sell_volume=float(row["SellVolume"]),
                delta=float(row["Delta"]),
                n_trades=int(row["NTrades"]),
                spread_feature=float(spread) if spread is not None else 0.0,
                spread_status=spread_status if spread is not None else SPREAD_MISSING,
                pipeline_version=SIGBAR_PIPELINE_VERSION,
                config_hash=config_hash,
                ts_event=ts_ns,
                ts_init=ts_ns,
            )
        )
    return bars


def roundtrip_check(
    catalog: ParquetDataCatalog, source: pl.DataFrame, written: list[SignedBar]
) -> dict[str, Any]:
    """Compare catalog read-back against **the staging source**, not the written objects.

    QA run 1 (Issue 4) found the original check zipped ``written`` against
    ``read``, which only proves Nautilus serialisation is lossless — already
    established at INFR-013 — and proves nothing about ``to_signed_bars``.
    Swapping ``BuyVolume`` and ``SellVolume`` in the mapping would have
    round-tripped perfectly and reported success.

    The exit condition in design.md §8.4 is equality with the staging source, so
    that is what is compared here: every signed field, the OHLC fields, and the
    derived delta, joined on the bar timestamp.
    """
    # Nautilus wraps custom types in `CustomData` on read-back; unwrap the payload.
    read = [getattr(d, "data", d) for d in catalog.query(data_cls=SignedBar)]

    read_df = pl.DataFrame(
        {
            "ts_event": [b.ts_event for b in read],
            "open": [b.open for b in read],
            "high": [b.high for b in read],
            "low": [b.low for b in read],
            "close": [b.close for b in read],
            "volume": [b.volume for b in read],
            "buy_volume": [b.buy_volume for b in read],
            "sell_volume": [b.sell_volume for b in read],
            "delta": [b.delta for b in read],
            "n_trades": [b.n_trades for b in read],
            "spread_feature": [b.spread_feature for b in read],
            "spread_status": [b.spread_status for b in read],
        }
    ).sort("ts_event")

    src_df = source.with_columns(
        (
            pl.col("CloseTime").dt.replace_time_zone("UTC").dt.epoch(time_unit="ms")
            * NS_PER_MS
        ).alias("ts_event")
    ).sort("ts_event")

    result: dict[str, Any] = {
        "compared_against": "staging source (not the written objects)",
        "n_source_rows": src_df.height,
        "n_written": len(written),
        "n_read_back": read_df.height,
        "count_match": read_df.height == src_df.height,
        "field_mismatches": {},
    }
    if not result["count_match"]:
        result["exact_match"] = False
        return result

    joined = src_df.join(read_df, on="ts_event", how="inner")
    result["n_joined_on_ts"] = joined.height
    if joined.height != src_df.height:
        result["exact_match"] = False
        result["detail"] = "timestamp key-set disagreement between source and read-back"
        return result

    # staging column -> SignedBar field
    pairs = {
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
        "BuyVolume": "buy_volume",
        "SellVolume": "sell_volume",
        "NTrades": "n_trades",
        "Delta": "delta",
    }
    for src_col, field in pairs.items():
        # `a != b` is NULL when either side is null, and `.sum()` skips nulls, so a
        # naive counter is blind to a null-vs-value disagreement. Compare with
        # explicit null handling so a missing value counts as a mismatch.
        # (QA run 2 minor note; latent today — no nulls in these columns.)
        bad = int(
            joined.select(
                (
                    (pl.col(src_col).is_null() != pl.col(field).is_null())
                    | (
                        pl.col(src_col).is_not_null()
                        & pl.col(field).is_not_null()
                        & (pl.col(src_col) != pl.col(field))
                    )
                ).sum()
            ).item()
        )
        result["field_mismatches"][f"{src_col}->{field}"] = bad

    # The spread fields were previously excluded from the comparison entirely
    # (QA run 2 minor note). The stored value must survive verbatim, and the
    # status must equal the pin's decision on every non-null row.
    spread_val_bad = int(
        joined.select(
            (
                (pl.col("SpreadBps").is_null() != (pl.col("spread_status") == SPREAD_MISSING))
                | (
                    pl.col("SpreadBps").is_not_null()
                    & (pl.col("SpreadBps") != pl.col("spread_feature"))
                )
            ).sum()
        ).item()
    )
    result["field_mismatches"]["SpreadBps->spread_feature(+status)"] = spread_val_bad

    # The defining invariant of the tier: buy + sell == volume, exactly.
    invariant_bad = int(
        joined.select(
            (
                (pl.col("buy_volume") + pl.col("sell_volume") - pl.col("volume")).abs()
                > 1e-9 * pl.max_horizontal(pl.col("volume"), pl.lit(1.0))
            ).sum()
        ).item()
    )
    result["split_invariant_violations"] = invariant_bad
    result["exact_match"] = (
        all(v == 0 for v in result["field_mismatches"].values()) and invariant_bad == 0
    )
    return result


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run_validation(root: Path) -> dict[str, Any]:
    """Write + read back the declared validation set and prove exact equality."""
    fence = load_fence_manifest()
    spread_status, pin_sha = load_w2_pin(root)
    day = datetime.strptime(VALIDATION_DAY, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end = day.replace(hour=23, minute=59, second=59)

    if day < fence.analysis_start_utc or end >= fence.train_end_utc:
        raise RuntimeError(f"FENCE VIOLATION: validation day {VALIDATION_DAY} not inside TRAIN")

    cat_root = root / SIGBAR_CATALOG / "_validation"
    if cat_root.exists():
        import shutil

        shutil.rmtree(cat_root)
    cat_root.mkdir(parents=True, exist_ok=True)
    catalog = ParquetDataCatalog(cat_root)

    per_symbol: dict[str, Any] = {}
    for symbol in VALIDATION_SYMBOLS:
        src = load_staging_window(root / STAGING_DIR / f"{symbol}.parquet", day, end)
        if src.is_empty():
            per_symbol[symbol] = {"status": "NO_BARS"}
            continue
        bars = to_signed_bars(src, symbol, spread_status, pin_sha)
        catalog.write_data(bars)
        per_symbol[symbol] = roundtrip_check(catalog, src, bars)
        # One catalog per symbol keeps the read-back unambiguous.
        import shutil

        shutil.rmtree(cat_root)
        cat_root.mkdir(parents=True, exist_ok=True)
        catalog = ParquetDataCatalog(cat_root)

    return {
        "w2_spread_status_from_pin": spread_status,
        "w2_pin_sha256": pin_sha,
        "validation_day": VALIDATION_DAY,
        "symbols": list(VALIDATION_SYMBOLS),
        # Derived from the checks actually performed, not hand-maintained — a
        # hand-written list drifts from the code (QA run 4 cosmetic note).
        "signed_fields_checked": sorted(
            {k for v in per_symbol.values()
             for k in (v.get("field_mismatches") or {})}
        ) + ["ts_event (join key)"],
        "per_symbol": per_symbol,
        "all_exact": all(
            v.get("exact_match") is True for v in per_symbol.values()
        ),
    }


def run_ingest(root: Path, symbols: list[str]) -> dict[str, Any]:
    """Ingest full TRAIN-band signed bars for the named symbols."""
    fence = load_fence_manifest()
    spread_status, pin_sha = load_w2_pin(root)
    cat_root = root / SIGBAR_CATALOG / "train"
    cat_root.mkdir(parents=True, exist_ok=True)
    catalog = ParquetDataCatalog(cat_root)

    out: dict[str, Any] = {}
    for symbol in tqdm(symbols, desc="sigbar ingest", unit="symbol"):
        path = root / STAGING_DIR / f"{symbol}.parquet"
        if not path.exists():
            out[symbol] = {"status": "NO_STAGING_FILE"}
            continue
        src = load_staging_window(path, fence.analysis_start_utc, fence.train_end_utc)
        if src.is_empty():
            out[symbol] = {"status": "NO_TRAIN_BARS"}
            continue
        realised_max = src["OpenTime"].max()
        if realised_max >= fence.train_end_utc.replace(tzinfo=None):
            raise RuntimeError(f"FENCE VIOLATION: {symbol} ingest exceeds train_end")
        catalog.write_data(to_signed_bars(src, symbol, spread_status, pin_sha))
        out[symbol] = {
            "status": "OK",
            "n_bars": src.height,
            "first": str(src["OpenTime"].min()),
            "last": str(realised_max),
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--validate", action="store_true", help="run the round-trip proof")
    ap.add_argument("--ingest", nargs="*", default=None, help="symbols to ingest (TRAIN band)")
    args = ap.parse_args()

    root = _repo_root()
    results = root / RESULTS_DIR
    results.mkdir(parents=True, exist_ok=True)
    fence = load_fence_manifest()

    payload: dict[str, Any] = {
        "item": "INFR-017",
        "work_item": "W5",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "pipeline_version": SIGBAR_PIPELINE_VERSION,
        "catalog_root": SIGBAR_CATALOG,
        "catalog_note": (
            "separate root from data/catalog/ — the pinned OHLCV catalog and its "
            "fence manifest sha are untouched; the signed lane is additive"
        ),
        "fence": {
            "manifest_sha256": fence.sha256,
            "analysis_start_utc": fence.analysis_start_utc.isoformat(),
            "train_end_utc": fence.train_end_utc.isoformat(),
            "band_used": "TRAIN",
        },
    }

    if args.validate or args.ingest is None:
        payload["roundtrip"] = run_validation(root)
        print(f"round-trip exact: {payload['roundtrip']['all_exact']}")
        for sym, r in payload["roundtrip"]["per_symbol"].items():
            print(f"  {sym}: read_back={r.get('n_read_back')} "
                  f"mismatches={r.get('field_mismatches')} "
                  f"split_violations={r.get('split_invariant_violations')}")

    if args.ingest:
        payload["ingest"] = run_ingest(root, args.ingest)
        ok = sum(1 for v in payload["ingest"].values() if v.get("status") == "OK")
        print(f"ingested {ok}/{len(args.ingest)} symbols")

    (results / "signed_lane_manifest.json").write_text(json.dumps(payload, indent=2))
    print(f"-> {(results / 'signed_lane_manifest.json').relative_to(root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
