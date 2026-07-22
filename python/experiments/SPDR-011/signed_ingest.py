"""Prepare and attest the five-name signed-volume TRAIN catalog for SPDR-011.

This module performs data preparation only. It never reads TEST/holdout rows and
does not compute an event outcome, return, cost, or strategy result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

import polars as pl
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from tqdm.auto import tqdm


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "python/src"))

from xen.nautilus.catalog_fence import (  # noqa: E402
    assert_within_fence,
    load_fence_manifest,
)
from xen.nautilus.instrument_ids import archive_symbol_to_instrument_id  # noqa: E402
from xen.sigbar.data_types import (  # noqa: E402
    SIGBAR_PIPELINE_VERSION,
    SPREAD_MISSING,
    SPREAD_UNUSABLE,
    SignedBar,
)


SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT")
SOURCE_DIR = (
    ROOT
    / "archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-011"
    / "data/staging/bars"
)
CATALOG_ROOT = ROOT / "data/catalog_sigbar/train"
BUILD_ROOT = ROOT / "data/catalog_sigbar/.spdr011_train_building"
ATTESTATION_PATH = Path(__file__).resolve().parent / "results/signed_train_attestation.json"
COLUMN_PINS_PATH = (
    ROOT
    / "archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-017"
    / "results/column_pins.json"
)
CHUNK_DAYS = 31
NS_PER_SECOND = 1_000_000_000
REQUIRED_COLUMNS = (
    "OpenTime",
    "CloseTime",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
    "BuyVolume",
    "SellVolume",
    "NTrades",
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _catalog_tree_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    files = sorted(item for item in path.rglob("*") if item.is_file())
    for item in files:
        digest.update(item.relative_to(path).as_posix().encode())
        digest.update(bytes.fromhex(_sha256_file(item)))
    return digest.hexdigest()


def _source_probe(path: Path) -> dict[str, Any]:
    try:
        display_path = path.relative_to(ROOT)
    except ValueError:
        display_path = path
    record: dict[str, Any] = {"path": str(display_path), "readable": False}
    if not path.exists():
        record["reason"] = "missing or dangling source path"
        return record
    try:
        record["columns"] = sorted(pl.scan_parquet(path).collect_schema().names())
        with path.open("rb") as stream:
            stream.read(1)
    except (OSError, pl.exceptions.PolarsError) as error:
        record["reason"] = f"{type(error).__name__}: {error}"
        return record
    record["readable"] = True
    return record


def assess_readiness(
    *,
    source_dir: Path = SOURCE_DIR,
    catalog_root: Path = CATALOG_ROOT,
    attestation_path: Path = ATTESTATION_PATH,
) -> dict[str, Any]:
    """Report raw-source access and verified catalog state independently."""
    sources = {symbol: _source_probe(source_dir / f"{symbol}.parquet") for symbol in SYMBOLS}
    raw_readable = all(record["readable"] for record in sources.values())
    catalog_files = sorted(item for item in catalog_root.rglob("*") if item.is_file()) \
        if catalog_root.exists() else []
    verified = False
    attestation_reason = "attestation missing"
    if attestation_path.exists():
        try:
            attestation = json.loads(attestation_path.read_text())
            verified = (
                attestation.get("status") == "VERIFIED"
                and tuple(attestation.get("symbols", ())) == SYMBOLS
                and all(
                    attestation.get("per_symbol", {}).get(symbol, {}).get("status")
                    == "VERIFIED"
                    for symbol in SYMBOLS
                )
                and bool(catalog_files)
            )
            attestation_reason = "verified" if verified else "attestation/catalog incomplete"
        except (OSError, json.JSONDecodeError) as error:
            attestation_reason = f"invalid attestation: {error}"
    return {
        "raw_source": {"readable": raw_readable, "per_symbol": sources},
        "train_catalog": {
            "verified": verified,
            "catalog_root": str(catalog_root),
            "catalog_file_count": len(catalog_files),
            "reason": attestation_reason,
        },
        "ready": raw_readable and verified,
    }


def validate_train_frame(frame: pl.DataFrame) -> tuple[pl.DataFrame, dict[str, int]]:
    """Derive exact delta and reject a broken taker-side volume partition."""
    missing = sorted(set(REQUIRED_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"signed source missing required columns: {missing}")
    checked = frame.with_columns(
        (pl.col("BuyVolume") - pl.col("SellVolume")).alias("Delta")
    )
    scale = pl.max_horizontal(pl.col("Volume").abs(), pl.lit(1.0))
    split_bad = int(
        checked.select(
            (
                (pl.col("BuyVolume") + pl.col("SellVolume") - pl.col("Volume")).abs()
                > 1e-9 * scale
            ).sum()
        ).item()
    )
    delta_bad = int(
        checked.select(
            (
                pl.col("Delta") != pl.col("BuyVolume") - pl.col("SellVolume")
            ).sum()
        ).item()
    )
    if split_bad or delta_bad:
        raise ValueError(
            f"signed mapping invalid: split={split_bad}, delta={delta_bad}"
        )
    return checked, {
        "split_invariant_violations": split_bad,
        "delta_mapping_violations": delta_bad,
    }


def zero_forbidden_band_attestation() -> dict[str, int]:
    """The ingest has no code path accepting a band other than TRAIN."""
    return {"test_rows_read": 0, "holdout_rows_read": 0}


def _load_config_pin() -> tuple[str, str]:
    pin = json.loads(COLUMN_PINS_PATH.read_text())
    status = pin["W2_decision"]["stored_column_status"]
    if status != "UNUSABLE":
        raise RuntimeError(f"expected accepted INFR-017 status UNUSABLE, got {status}")
    return str(pin["pin_sha256"]), status


def _chunk_bounds(start: datetime, end: datetime) -> Iterator[tuple[datetime, datetime]]:
    cursor = start
    while cursor < end:
        next_cursor = min(cursor + timedelta(days=CHUNK_DAYS), end)
        yield cursor, next_cursor
        cursor = next_cursor


def _load_train_chunk(path: Path, start: datetime, end: datetime) -> pl.DataFrame:
    start_naive = start.astimezone(timezone.utc).replace(tzinfo=None)
    end_naive = end.astimezone(timezone.utc).replace(tzinfo=None)
    optional = ["SpreadBps"] if "SpreadBps" in pl.scan_parquet(path).collect_schema() else []
    return (
        pl.scan_parquet(path)
        .select([*REQUIRED_COLUMNS, *optional])
        .filter(
            (pl.col("OpenTime") >= start_naive)
            & (pl.col("OpenTime") < end_naive)
        )
        .sort("OpenTime")
        .collect()
    )


def _source_train_stats(path: Path, start: datetime, end: datetime) -> dict[str, Any]:
    """Independently count the fenced source rows before catalog mutation."""
    start_naive = start.astimezone(timezone.utc).replace(tzinfo=None)
    end_naive = end.astimezone(timezone.utc).replace(tzinfo=None)
    row = (
        pl.scan_parquet(path)
        .filter(
            (pl.col("OpenTime") >= start_naive)
            & (pl.col("OpenTime") < end_naive)
        )
        .select(
            pl.len().alias("train_rows"),
            pl.col("OpenTime").min().alias("first_open_time"),
            pl.col("OpenTime").max().alias("last_open_time"),
            pl.col("CloseTime").min().alias("first_close_time"),
            pl.col("CloseTime").max().alias("last_close_time"),
            (
                (pl.col("BuyVolume") + pl.col("SellVolume") - pl.col("Volume")).abs()
                > 1e-9 * pl.max_horizontal(pl.col("Volume").abs(), pl.lit(1.0))
            ).sum().alias("split_invariant_violations"),
        )
        .collect()
        .row(0, named=True)
    )
    return {
        key: value.isoformat() if isinstance(value, datetime) else int(value)
        for key, value in row.items()
    }


def _catalog_symbol_audit(
    catalog_root: Path,
    symbol: str,
    expected: dict[str, Any],
    config_hash: str,
) -> dict[str, Any]:
    """Prove the completed catalog contains every independently counted TRAIN row."""
    instrument = str(archive_symbol_to_instrument_id(symbol))
    symbol_dir = catalog_root / "data/custom_signed_bar" / instrument
    files = sorted(symbol_dir.glob("*.parquet"))
    if not files:
        return {"complete": False, "reason": "no catalog parquet files"}
    row = (
        pl.scan_parquet(files)
        .select(
            pl.len().alias("catalog_rows"),
            pl.col("ts_event").min().alias("first_ts_event"),
            pl.col("ts_event").max().alias("last_ts_event"),
            (
                (pl.col("buy_volume") + pl.col("sell_volume") - pl.col("volume")).abs()
                > 1e-9 * pl.max_horizontal(pl.col("volume").abs(), pl.lit(1.0))
            ).sum().alias("split_invariant_violations"),
            (pl.col("delta") != pl.col("buy_volume") - pl.col("sell_volume"))
            .sum()
            .alias("delta_mapping_violations"),
            (pl.col("config_hash") != config_hash).sum().alias("config_hash_violations"),
            (pl.col("pipeline_version") != SIGBAR_PIPELINE_VERSION)
            .sum()
            .alias("pipeline_version_violations"),
        )
        .collect()
        .row(0, named=True)
    )
    expected_first_ns = int(
        datetime.fromisoformat(expected["first_close_time"])
        .replace(tzinfo=timezone.utc)
        .timestamp()
        * NS_PER_SECOND
    )
    expected_last_ns = int(
        datetime.fromisoformat(expected["last_close_time"])
        .replace(tzinfo=timezone.utc)
        .timestamp()
        * NS_PER_SECOND
    )
    complete = (
        row["catalog_rows"] == expected["train_rows"]
        and row["first_ts_event"] == expected_first_ns
        and row["last_ts_event"] == expected_last_ns
        and all(
            row[key] == 0
            for key in (
                "split_invariant_violations",
                "delta_mapping_violations",
                "config_hash_violations",
                "pipeline_version_violations",
            )
        )
    )
    return {"complete": complete, "catalog_file_count": len(files), **row}


def _to_signed_bars(
    frame: pl.DataFrame,
    symbol: str,
    config_hash: str,
) -> list[SignedBar]:
    instrument_id = archive_symbol_to_instrument_id(symbol)
    has_legacy_skew = "SpreadBps" in frame.columns
    bars: list[SignedBar] = []
    for row in frame.iter_rows(named=True):
        close_time = row["CloseTime"].replace(tzinfo=timezone.utc)
        ts_ns = int(close_time.timestamp() * NS_PER_SECOND)
        skew = row.get("SpreadBps") if has_legacy_skew else None
        bars.append(
            SignedBar(
                instrument_id=instrument_id,
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=float(row["Volume"]),
                buy_volume=float(row["BuyVolume"]),
                sell_volume=float(row["SellVolume"]),
                delta=float(row["Delta"]),
                n_trades=int(row["NTrades"]),
                spread_feature=float(skew) if skew is not None else 0.0,
                spread_status=SPREAD_UNUSABLE if skew is not None else SPREAD_MISSING,
                pipeline_version=SIGBAR_PIPELINE_VERSION,
                config_hash=config_hash,
                ts_event=ts_ns,
                ts_init=ts_ns,
            )
        )
    return bars


def _verify_chunk(
    catalog: ParquetDataCatalog,
    source: pl.DataFrame,
    symbol: str,
) -> None:
    if source.is_empty():
        return
    instrument_id = str(archive_symbol_to_instrument_id(symbol))
    start_ns = int(source["CloseTime"].min().replace(tzinfo=timezone.utc).timestamp() * NS_PER_SECOND)
    end_ns = int(source["CloseTime"].max().replace(tzinfo=timezone.utc).timestamp() * NS_PER_SECOND)
    read = [
        getattr(item, "data", item)
        for item in catalog.query(
            data_cls=SignedBar,
            identifiers=[instrument_id],
            start=start_ns,
            end=end_ns,
        )
    ]
    if len(read) != source.height:
        raise RuntimeError(
            f"{symbol} catalog round-trip count {len(read)} != source {source.height}"
        )
    expected = source.select(
        ["Open", "High", "Low", "Close", "Volume", "BuyVolume", "SellVolume", "Delta", "NTrades"]
    ).rows()
    actual = [
        (
            bar.open,
            bar.high,
            bar.low,
            bar.close,
            bar.volume,
            bar.buy_volume,
            bar.sell_volume,
            bar.delta,
            bar.n_trades,
        )
        for bar in read
    ]
    if actual != expected:
        raise RuntimeError(f"{symbol} signed fields changed during catalog round-trip")


def prepare_signed_train() -> dict[str, Any]:
    """Build a fresh catalog atomically after all five sources pass preflight."""
    readiness = assess_readiness()
    if not readiness["raw_source"]["readable"]:
        missing = {
            symbol: record.get("reason", "unreadable")
            for symbol, record in readiness["raw_source"]["per_symbol"].items()
            if not record["readable"]
        }
        raise RuntimeError(f"signed TRAIN source unavailable: {missing}")
    if CATALOG_ROOT.exists() and any(CATALOG_ROOT.iterdir()):
        raise RuntimeError(f"refusing to overwrite existing catalog at {CATALOG_ROOT}")
    if BUILD_ROOT.exists():
        raise RuntimeError(f"stale build root exists; inspect before retry: {BUILD_ROOT}")

    fence = load_fence_manifest()
    assert_within_fence(
        fence,
        fence.analysis_start_utc,
        fence.train_end_utc,
        band="TRAIN",
    )
    config_hash, stored_status = _load_config_pin()

    source_meta: dict[str, Any] = {}
    for symbol in tqdm(SYMBOLS, desc="hash signed sources", unit="symbol"):
        path = SOURCE_DIR / f"{symbol}.parquet"
        source_meta[symbol] = {
            "path": str(path.relative_to(ROOT)),
            "source_file_sha256": _sha256_file(path),
            **_source_train_stats(path, fence.analysis_start_utc, fence.train_end_utc),
        }

    BUILD_ROOT.mkdir(parents=True)
    catalog = ParquetDataCatalog(BUILD_ROOT)
    per_symbol: dict[str, Any] = {}
    for symbol in tqdm(SYMBOLS, desc="ingest signed TRAIN", unit="symbol"):
        path = SOURCE_DIR / f"{symbol}.parquet"
        n_rows = 0
        first_open: datetime | None = None
        last_open: datetime | None = None
        for start, end in _chunk_bounds(fence.analysis_start_utc, fence.train_end_utc):
            chunk = _load_train_chunk(path, start, end)
            if chunk.is_empty():
                continue
            chunk, audit = validate_train_frame(chunk)
            if audit["split_invariant_violations"] or audit["delta_mapping_violations"]:
                raise RuntimeError(f"{symbol} signed invariant failure")
            bars = _to_signed_bars(chunk, symbol, config_hash)
            catalog.write_data(bars)
            _verify_chunk(catalog, chunk, symbol)
            n_rows += chunk.height
            first_open = first_open or chunk["OpenTime"].min()
            last_open = chunk["OpenTime"].max()
        if n_rows == 0:
            raise RuntimeError(f"{symbol} has zero TRAIN rows")
        if n_rows != source_meta[symbol]["train_rows"]:
            raise RuntimeError(
                f"{symbol} chunked ingest counted {n_rows}, source preflight counted "
                f"{source_meta[symbol]['train_rows']}"
            )
        if last_open is None or last_open >= fence.train_end_utc.replace(tzinfo=None):
            raise RuntimeError(f"{symbol} crossed the TRAIN fence")
        catalog_audit = _catalog_symbol_audit(
            BUILD_ROOT,
            symbol,
            source_meta[symbol],
            config_hash,
        )
        if not catalog_audit["complete"]:
            raise RuntimeError(f"{symbol} incomplete catalog: {catalog_audit}")
        per_symbol[symbol] = {
            **source_meta[symbol],
            "status": "VERIFIED",
            "chunked_ingest_rows": n_rows,
            "delta_mapping_violations": 0,
            "catalog_audit": catalog_audit,
        }

    CATALOG_ROOT.parent.mkdir(parents=True, exist_ok=True)
    BUILD_ROOT.rename(CATALOG_ROOT)
    payload = {
        "schema": "spdr011-signed-train-attestation/v1",
        "status": "VERIFIED",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "symbols": list(SYMBOLS),
        "catalog_root": str(CATALOG_ROOT.relative_to(ROOT)),
        "catalog_tree_sha256": _catalog_tree_sha256(CATALOG_ROOT),
        "pipeline_version": SIGBAR_PIPELINE_VERSION,
        "accepted_infr017_config_hash": config_hash,
        "legacy_mean_price_skew_status": stored_status,
        "fence": {
            "manifest_sha256": fence.sha256,
            "band": "TRAIN",
            "start_utc": fence.analysis_start_utc.isoformat(),
            "end_utc_exclusive": fence.train_end_utc.isoformat(),
            **zero_forbidden_band_attestation(),
        },
        "mapping": {
            "buy_volume": "BuyVolume",
            "sell_volume": "SellVolume",
            "delta": "BuyVolume - SellVolume",
            "split_invariant": "BuyVolume + SellVolume == Volume (rtol 1e-9)",
        },
        "source_hash_scope": (
            "full parquet container bytes; hash-only, with no non-TRAIN row or column decoded"
        ),
        "train_selection_timestamp": "OpenTime",
        "boundary_note": (
            "OpenTime < train_end_utc; the final admitted one-minute bar may have "
            "CloseTime/ts_event exactly equal to train_end_utc"
        ),
        "per_symbol": per_symbol,
    }
    ATTESTATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    ATTESTATION_PATH.write_text(json.dumps(payload, indent=2) + "\n")
    return payload


def write_blocked_attestation(readiness: dict[str, Any]) -> dict[str, Any]:
    status = (
        "BLOCKED_TRAIN_CATALOG_UNMATERIALIZED"
        if readiness["raw_source"]["readable"]
        else "BLOCKED_RAW_SOURCE_UNREADABLE"
    )
    payload = {
        "schema": "spdr011-signed-train-attestation/v1",
        "status": status,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "symbols": list(SYMBOLS),
        "catalog_root": str(CATALOG_ROOT.relative_to(ROOT)),
        "readiness": readiness,
        "fence": {"band": "TRAIN", **zero_forbidden_band_attestation()},
    }
    ATTESTATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    ATTESTATION_PATH.write_text(json.dumps(payload, indent=2) + "\n")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--prepare",
        action="store_true",
        help="atomically build and verify the fixed five-symbol TRAIN catalog",
    )
    args = parser.parse_args()
    if args.prepare:
        payload = prepare_signed_train()
    else:
        readiness = assess_readiness()
        payload = readiness if readiness["ready"] else write_blocked_attestation(readiness)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
