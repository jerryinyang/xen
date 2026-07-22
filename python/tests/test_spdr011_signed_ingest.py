from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path

import polars as pl


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = PROJECT_ROOT / "python/experiments/SPDR-011/signed_ingest.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("spdr011_signed_ingest", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_readiness_separates_raw_source_from_verified_train_catalog(tmp_path: Path) -> None:
    ingest = _load_module()
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    for symbol in ingest.SYMBOLS:
        pl.DataFrame({"OpenTime": [1]}).write_parquet(source_dir / f"{symbol}.parquet")

    readiness = ingest.assess_readiness(
        source_dir=source_dir,
        catalog_root=tmp_path / "catalog",
        attestation_path=tmp_path / "attestation.json",
    )

    assert readiness["raw_source"]["readable"] is True
    assert readiness["train_catalog"]["verified"] is False
    assert readiness["ready"] is False


def test_validate_train_frame_checks_split_and_derives_delta() -> None:
    ingest = _load_module()
    frame = pl.DataFrame(
        {
            "OpenTime": [datetime(2023, 1, 1, tzinfo=timezone.utc).replace(tzinfo=None)],
            "CloseTime": [
                datetime(2023, 1, 1, 0, 0, 59, tzinfo=timezone.utc).replace(tzinfo=None)
            ],
            "Open": [100.0],
            "High": [101.0],
            "Low": [99.0],
            "Close": [100.5],
            "Volume": [10.0],
            "BuyVolume": [6.0],
            "SellVolume": [4.0],
            "NTrades": [3],
            "SpreadBps": [0.1],
        }
    )

    checked, audit = ingest.validate_train_frame(frame)

    assert checked["Delta"].to_list() == [2.0]
    assert audit["split_invariant_violations"] == 0
    assert audit["delta_mapping_violations"] == 0


def test_train_attestation_declares_zero_test_and_holdout_rows() -> None:
    ingest = _load_module()

    bands = ingest.zero_forbidden_band_attestation()

    assert bands == {"test_rows_read": 0, "holdout_rows_read": 0}


def test_signed_bar_roundtrip_preserves_source_mapping(tmp_path: Path) -> None:
    ingest = _load_module()
    frame = pl.DataFrame(
        {
            "OpenTime": [datetime(2023, 1, 1, tzinfo=timezone.utc).replace(tzinfo=None)],
            "CloseTime": [
                datetime(2023, 1, 1, 0, 0, 59, tzinfo=timezone.utc).replace(tzinfo=None)
            ],
            "Open": [100.0],
            "High": [101.0],
            "Low": [99.0],
            "Close": [100.5],
            "Volume": [10.0],
            "BuyVolume": [6.0],
            "SellVolume": [4.0],
            "NTrades": [3],
            "SpreadBps": [0.1],
        }
    )
    checked, _ = ingest.validate_train_frame(frame)
    catalog = ingest.ParquetDataCatalog(tmp_path / "catalog")

    catalog.write_data(ingest._to_signed_bars(checked, "BTCUSDT", "config-hash"))

    ingest._verify_chunk(catalog, checked, "BTCUSDT")
