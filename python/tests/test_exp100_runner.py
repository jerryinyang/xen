"""Task 4 tests for the EXP-100 Nautilus adapter and one-cell runner."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import polars as pl

from nautilus_trader.core.datetime import dt_to_unix_nanos
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.test_kit.providers import TestInstrumentProvider

CODE_DIR = Path(__file__).resolve().parents[1] / "experiments" / "EXP-100" / "code"
sys.path.insert(0, str(CODE_DIR))

import run_experiment  # noqa: E402
from run_experiment import build_backtest_run_config  # noqa: E402
from xen.exp100 import Exp100CellConfig  # noqa: E402
from xen.exp100.strategy import _raid_schema  # noqa: E402
from xen.nautilus.backtest_util import synthetic_bars  # noqa: E402


START = datetime(2023, 1, 1, tzinfo=UTC)
END = START + timedelta(minutes=31)
INSTRUMENT_ID = "XRPUSDT-LINEAR.BYBIT"


def test_raid_schema_exposes_both_duration_clocks() -> None:
    """The Parquet boundary must not silently discard either duration field."""
    names = _raid_schema().names
    assert "excursion_duration_ns" in names
    assert "swing_duration_ns" in names
    assert "duration_ns" in names


def test_raid_schema_exposes_single_structured_pre_mfe_retrace_column() -> None:
    """The path price and ordering status stay atomic at the Parquet boundary."""
    schema = _raid_schema()
    field = schema.field("pre_mfe_retrace")
    assert field.type.names == ["price", "status"]


def make_cell() -> Exp100CellConfig:
    return Exp100CellConfig(
        venue="BYBIT",
        archive_symbol="XRPUSDT",
        instrument_id=INSTRUMENT_ID,
        observation_minutes=15,
        confirmation_method="LEVEL_CLOSE",
        confirmation_reference="1H",
        level_config="PREVIOUS_1H",
    )


def write_synthetic_catalog(path: Path) -> None:
    instrument = TestInstrumentProvider.xrpusdt_linear_bybit()
    _, bars, _ = synthetic_bars(instrument, n=32, start=START)
    catalog = ParquetDataCatalog(str(path))
    catalog.write_data([instrument])
    catalog.write_data(bars)


def output_hashes(run_dir: Path) -> dict[str, str]:
    names = (
        "bar_marks.parquet",
        "fills.parquet",
        "orders.parquet",
        "positions_ledger.parquet",
        "event_log.jsonl",
        "levels.parquet",
        "raids.parquet",
        "tpo_profiles.parquet",
    )
    hashes: dict[str, str] = {}
    for name in names:
        digest = hashlib.sha256()
        with (run_dir / name).open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        hashes[name] = digest.hexdigest()
    return hashes


def run_synthetic_cell(
    root: Path,
    *,
    chunk_size: int,
    rss_limit_bytes: int = 10_000_000_000,
    destroy_control: bool = False,
) -> Path:
    catalog_path = root / "catalog"
    run_dir = root / "run"
    root.mkdir(parents=True, exist_ok=True)
    write_synthetic_catalog(catalog_path)
    command = [
        sys.executable,
        str(CODE_DIR / "run_experiment.py"),
        "--catalog-path",
        str(catalog_path),
        "--run-dir",
        str(run_dir),
        "--instrument-id",
        INSTRUMENT_ID,
        "--archive-symbol",
        "XRPUSDT",
        "--venue",
        "BYBIT",
        "--observation-minutes",
        "15",
        "--confirmation-method",
        "LEVEL_CLOSE",
        "--confirmation-reference",
        "1H",
        "--level-config",
        "PREVIOUS_1H",
        "--start",
        START.isoformat(),
        "--end",
        END.isoformat(),
        "--chunk-size",
        str(chunk_size),
        "--rss-limit-bytes",
        str(rss_limit_bytes),
    ]
    if destroy_control:
        command.append("--destroy-control")
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    assert result.returncode == 0, f"stdout={result.stdout}\nstderr={result.stderr}"
    return run_dir


def test_backtest_config_is_streaming_and_one_cell() -> None:
    cfg = build_backtest_run_config(
        make_cell(),
        catalog_path=Path("catalog"),
        start_time=START,
        end_time=END,
        staging_path=Path("stage"),
        chunk_size=128,
    )

    assert cfg.chunk_size == 128
    assert cfg.dispose_on_completion is False
    assert cfg.engine is not None
    assert cfg.engine.run_analysis is False
    assert len(cfg.data) == 1
    assert len(cfg.venues) == 1
    assert cfg.venues[0].frozen_account is True
    assert len(cfg.engine.strategies) == 1


def test_ctrader_execution_pin_is_independent() -> None:
    assert hasattr(run_experiment, "execution_pin")
    pin = run_experiment.execution_pin("CTRADER")

    assert pin.catalog_path == Path("data/catalog_ctrader")
    assert pin.fence_sha256 == (
        "4cdc7b01dd47200710d0d961639d55d52e1129ca89096e841eafd816b6061de0"
    )
    assert pin.train_start == datetime(2021, 6, 2, 0, 1, tzinfo=UTC)
    assert pin.train_end == datetime(2023, 11, 22, tzinfo=UTC)


def test_ctrader_backtest_venue_matches_instrument_case() -> None:
    cell = Exp100CellConfig(
        venue="CTRADER",
        archive_symbol="EURUSD",
        instrument_id="EURUSD.CTrader",
        observation_minutes=15,
        confirmation_method="BREAKOUT_BAR",
        confirmation_reference="1H",
        level_config="PREVIOUS_1H",
    )

    cfg = build_backtest_run_config(
        cell,
        catalog_path=Path("data/catalog_ctrader"),
        start_time=datetime(2023, 11, 18, tzinfo=UTC),
        end_time=datetime(2023, 11, 19, tzinfo=UTC),
        staging_path=Path("stage"),
        chunk_size=128,
    )

    assert cfg.venues[0].name == "CTrader"


def test_chunked_synthetic_replay_has_same_hash(tmp_path: Path) -> None:
    one = run_synthetic_cell(tmp_path / "one", chunk_size=1)
    many = run_synthetic_cell(tmp_path / "many", chunk_size=128)

    assert output_hashes(one) == output_hashes(many)
    metadata = json.loads((one / "run_metadata.json").read_text(encoding="utf-8"))
    assert metadata["cost_model"] == "NO_COST_CHARGED"
    assert metadata["run_config"]["chunk_size"] == 1
    assert json.loads((one / "fence_attestation.json").read_text())[
        "status"
    ] == "PINNED"
    assert pl.read_parquet(one / "fills.parquet").height == 0
    assert pl.read_parquet(one / "orders.parquet").height == 0
    assert pl.read_parquet(one / "positions_ledger.parquet").height == 0


def test_memory_abort_leaves_marker_and_does_not_publish(tmp_path: Path) -> None:
    catalog_path = tmp_path / "catalog"
    run_dir = tmp_path / "run"
    write_synthetic_catalog(catalog_path)

    result = subprocess.run(
        [
            sys.executable,
            str(CODE_DIR / "run_experiment.py"),
            "--catalog-path",
            str(catalog_path),
            "--run-dir",
            str(run_dir),
            "--instrument-id",
            INSTRUMENT_ID,
            "--archive-symbol",
            "XRPUSDT",
            "--venue",
            "BYBIT",
            "--observation-minutes",
            "15",
            "--confirmation-method",
            "LEVEL_CLOSE",
            "--confirmation-reference",
            "1H",
            "--level-config",
            "PREVIOUS_1H",
            "--start",
            START.isoformat(),
            "--end",
            END.isoformat(),
            "--chunk-size",
            "128",
            "--rss-limit-bytes",
            "1",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "RSS limit" in result.stderr
    assert not run_dir.exists()
    markers = list(tmp_path.rglob("*.incomplete.json"))
    assert len(markers) == 1
    marker = json.loads(markers[0].read_text(encoding="utf-8"))
    assert marker["limit_bytes"] == 1
    assert marker["last_timestamp"] == dt_to_unix_nanos(START)


def test_destroy_control_is_separate_and_recorded(tmp_path: Path) -> None:
    run_dir = run_synthetic_cell(tmp_path / "destroy", chunk_size=128, destroy_control=True)

    assert (run_dir / "raids.parquet").exists()
    assert (run_dir / "raids_destroyed.parquet").exists()
    metadata = json.loads((run_dir / "run_metadata.json").read_text(encoding="utf-8"))
    assert metadata["destroy_control"]["path"] == "raids_destroyed.parquet"
    assert metadata["destroy_control"]["fixed_points"] == 0
