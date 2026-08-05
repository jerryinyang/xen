from __future__ import annotations

import gc
import hashlib
import importlib.util
import json
import time
import tracemalloc
from datetime import datetime, timedelta, timezone
from pathlib import Path

import polars as pl
import pytest

from xen.adaptive_management.contracts import experiment_spec
from xen.nautilus.catalog_fence import FenceViolation


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
REQUIRED_RAW = {
    "config.json",
    "fence_attestation.json",
    "calibration.parquet",
    "features.parquet",
    "origins.parquet",
    "native_parameter_schedule.parquet",
    "episodes.parquet",
    "policy_schedule.parquet",
    "orders.parquet",
    "fills.parquet",
    "positions.parquet",
    "episode_results.parquet",
    "run_summary.json",
}


def _load_wrapper(experiment_id: str):
    path = ROOT / "experiments" / experiment_id / "screen_code" / "run_screen.py"
    module_spec = importlib.util.spec_from_file_location(
        f"run_{experiment_id.lower().replace('-', '')}", path
    )
    assert module_spec is not None and module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def test_runner_refuses_non_train_band(tmp_path):
    from xen.adaptive_management.runner import run_experiment

    with pytest.raises(FenceViolation, match="TRAIN"):
        run_experiment(
            experiment_spec("SPDR-021"),
            "crypto",
            tmp_path / "out",
            band="TEST",
            dry_run=True,
        )


@pytest.mark.parametrize("experiment_id", ["SPDR-021", "SPDR-022", "SPDR-023"])
def test_wrapper_invokes_only_its_own_experiment(monkeypatch, tmp_path, experiment_id):
    from xen.adaptive_management import runner

    seen = []

    def fake_run(spec, universe, output, **kwargs):
        seen.append((spec.experiment_id, universe, Path(output), kwargs))
        return {"dry_run": True}

    monkeypatch.setattr(runner, "run_experiment", fake_run)
    wrapper = _load_wrapper(experiment_id)
    wrapper.main(
        [
            "--universe",
            "crypto",
            "--output",
            str(tmp_path),
            "--jobs",
            "3",
            "--dry-run",
        ]
    )
    assert len(seen) == 1
    seen_id, seen_universe, seen_output, kwargs = seen[0]
    assert (seen_id, seen_universe, seen_output) == (experiment_id, "crypto", tmp_path)
    assert kwargs["jobs"] == 3
    assert kwargs["dry_run"] is True
    assert kwargs["resume"] is False


def test_dry_run_reads_metadata_only_and_creates_no_results(monkeypatch, tmp_path):
    from xen.adaptive_management import runner

    monkeypatch.setattr(
        runner,
        "_catalog_metadata",
        lambda config: {
            "available_instruments": list(config.instrument_ids),
            "catalog_path": str(config.catalog_path),
        },
    )
    output = tmp_path / "never-created"
    plan = runner.run_experiment(
        experiment_spec("SPDR-021"),
        "ctrader",
        output,
        dry_run=True,
    )
    assert plan["dry_run"] is True
    assert plan["universe"] == "ctrader"
    assert plan["native_adaptive_arms"] == 64
    assert plan["symbols"] == ["EURUSD", "XAUUSD", "USTEC"]
    assert not output.exists()


def test_universe_configs_never_cross_catalogs_or_manifests():
    from xen.adaptive_management.runner import universe_config

    crypto = universe_config("crypto")
    ctrader = universe_config("ctrader")
    assert crypto.catalog_path == REPO / "data" / "catalog"
    assert ctrader.catalog_path == REPO / "data" / "catalog_ctrader"
    assert "INFR-011" in crypto.manifest_path.as_posix()
    assert "INFR-021" in ctrader.manifest_path.as_posix()
    assert all(iid.endswith("-LINEAR.BYBIT") for iid in crypto.instrument_ids)
    assert ctrader.instrument_ids == (
        "EURUSD.CTrader",
        "XAUUSD.CTrader",
        "USTEC.CTrader",
    )


def test_completed_run_is_atomic_complete_and_refuses_overwrite(
    monkeypatch, tmp_path
):
    from xen.adaptive_management import runner

    frame = pl.DataFrame({"row_id": ["one"]})

    def fake_execute(plan, workspace, **kwargs):
        unit = workspace / "units" / "EURUSD"
        unit.mkdir(parents=True, exist_ok=True)
        for name in runner.UNIT_FRAMES:
            frame.write_parquet(unit / f"{name}.parquet")
        return runner.RunBundle(
            unit_dirs={"EURUSD": unit},
            instrument_id_map={"EURUSD": "EURUSD.CTrader"},
            summary={"work_units": 1, "completed_work_units": 1},
        )

    monkeypatch.setattr(runner, "_catalog_metadata", lambda config: {})
    monkeypatch.setattr(runner, "_execute_plan", fake_execute)
    output = tmp_path / "run"
    runner.run_experiment(
        experiment_spec("SPDR-021"),
        "ctrader",
        output,
    )
    assert REQUIRED_RAW.issubset({path.name for path in output.iterdir()})
    assert json.loads((output / "fence_attestation.json").read_text())["status"] == "PINNED"
    assert json.loads((output / "config.json").read_text())["band"] == "TRAIN"
    cell = output / "cells" / "EURUSD"
    assert {
        "run_metadata.json",
        "bar_marks.parquet",
        "positions_ledger.parquet",
        "orders.parquet",
        "fills.parquet",
        "event_log.jsonl",
        "instrument_id_map.json",
        "fence_attestation.json",
    }.issubset({path.name for path in cell.iterdir()})
    with pytest.raises(FileExistsError):
        runner.run_experiment(
            experiment_spec("SPDR-021"),
            "ctrader",
            output,
        )


def test_wrapper_rejects_research_parameter_flags():
    wrapper = _load_wrapper("SPDR-021")
    with pytest.raises(SystemExit):
        wrapper.main(["--threshold", "0.75"])


def _h1_fixture(rows: int = 820) -> pl.DataFrame:
    start = datetime(2021, 1, 1, tzinfo=timezone.utc)
    index = list(range(rows))
    close = [100.0 + (i % 11 - 5) * 0.15 + i * 0.002 for i in index]
    return pl.DataFrame(
        {
            "symbol": ["SYN"] * rows,
            "ts": [start + timedelta(hours=i) for i in index],
            "open": [value - 0.03 for value in close],
            "high": [value + 0.4 + (i % 3) * 0.02 for i, value in zip(index, close)],
            "low": [value - 0.4 - (i % 4) * 0.02 for i, value in zip(index, close)],
            "close": close,
            "volume": [1000.0 + i for i in index],
        }
    ).with_columns(pl.col("ts").cast(pl.Datetime("ns", "UTC")))


@pytest.mark.parametrize(
    ("experiment_id", "expected_adaptive", "expected_fixed"),
    [("SPDR-021", 64, 1), ("SPDR-022", 128, 2)],
)
def test_real_scheduler_materialises_complete_native_grid(
    experiment_id, expected_adaptive, expected_fixed
):
    from xen.adaptive_management.runner import _materialise_symbol
    from xen.adaptive_management.strategy import SCHEDULE_COLUMNS

    tables, schedule = _materialise_symbol(
        experiment_spec(experiment_id),
        _h1_fixture(),
    )
    native = tables["native_parameter_schedule"]
    assert native.filter(pl.col("arm_class") != "FIXED_NATIVE")[
        "arm_id"
    ].n_unique() == expected_adaptive
    assert native.filter(pl.col("arm_class") == "FIXED_NATIVE")[
        "arm_id"
    ].n_unique() == expected_fixed
    assert set(SCHEDULE_COLUMNS) == set(schedule.columns)
    management = tables["policy_schedule"]
    assert management.filter(pl.col("native_arm_id").is_not_null()).is_empty()
    assert management["policy_id"].n_unique() > 1
    ineligible = management.filter(~pl.col("eligible"))
    assert ineligible.height > 0
    assert set(ineligible["state"]) == {"NO_FEATURE"}
    execution_ineligible = schedule.join(
        ineligible.select("episode_id", "arm_id", "policy_id"),
        on=["episode_id", "arm_id", "policy_id"],
        how="inner",
    )
    assert set(execution_ineligible["state"]) == {"NO_FEATURE"}


class _StubInstrument:
    def __init__(self, instrument_id: str) -> None:
        self.id = instrument_id
        self.size_increment = "0.01"


class _StubCatalog:
    instrument_ids: tuple[str, ...] = ()

    def __init__(self, path: str) -> None:
        self.path = path

    def instruments(self):
        return [_StubInstrument(iid) for iid in _StubCatalog.instrument_ids]


def _stub_execution(monkeypatch, *, fail_on: set[str] | None = None, calls: list | None = None):
    """Replace catalog, materialisation and engine with deterministic synthetic work."""
    from xen.adaptive_management import runner

    _StubCatalog.instrument_ids = runner.universe_config("ctrader").instrument_ids
    monkeypatch.setattr(runner, "_catalog_metadata", lambda config: {})
    monkeypatch.setattr(runner, "ParquetDataCatalog", _StubCatalog)
    monkeypatch.setattr(
        runner,
        "fenced_bar_query",
        lambda *args, **kwargs: ["bar"],
    )
    monkeypatch.setattr(
        runner,
        "_bars_frame",
        lambda symbol, bars: pl.DataFrame({"symbol": [symbol], "ts": [0]}),
    )
    monkeypatch.setattr(runner, "_hourly_frame", lambda minute: minute)
    monkeypatch.setattr(
        runner,
        "_bar_marks",
        lambda symbol, instrument_id, frame: pl.DataFrame(
            {"symbol": [symbol], "instrument_id": [instrument_id]}
        ),
    )
    monkeypatch.setattr(
        runner,
        "_instrument_spec",
        lambda symbol, instrument: symbol,
    )

    def fake_materialise(spec, h1):
        symbol = h1["symbol"][0]
        tables = {
            name: pl.DataFrame({"symbol": [symbol], "table": [name]})
            for name in runner.TABLE_ARTIFACTS
        }
        return tables, pl.DataFrame({"symbol": [symbol]})

    def fake_engine(unit):
        symbol = unit.unit_id.rsplit("-", 1)[-1]
        if calls is not None:
            calls.append(symbol)
        if fail_on and symbol in fail_on:
            raise RuntimeError(f"synthetic interruption on {symbol}")
        return {
            "orders": pl.DataFrame({"symbol": [symbol], "instrument_id": [f"{symbol}.CTrader"]}),
            "fills": pl.DataFrame({"symbol": [symbol], "instrument_id": [f"{symbol}.CTrader"]}),
            "positions": pl.DataFrame(
                {"symbol": [symbol], "instrument_id": [f"{symbol}.CTrader"]}
            ),
            "state_ledger": pl.DataFrame({"symbol": [symbol], "ledger": [1]}),
        }

    monkeypatch.setattr(runner, "_materialise_symbol", fake_materialise)
    monkeypatch.setattr(runner, "run_work_unit_subprocess", fake_engine)
    return runner


def _canonical_hashes(output: Path) -> dict[str, str]:
    from xen.adaptive_management import runner

    return {
        name: hashlib.sha256((output / name).read_bytes()).hexdigest()
        for name in sorted(runner.RAW_ARTIFACTS)
    }


def test_resume_refuses_changed_config(monkeypatch, tmp_path):
    runner = _stub_execution(monkeypatch, fail_on={"USTEC"})
    output = tmp_path / "run"
    with pytest.raises(RuntimeError, match="synthetic interruption"):
        runner.run_experiment(experiment_spec("SPDR-021"), "ctrader", output)
    assert (tmp_path / ".run.inprogress").is_dir()

    with pytest.raises(ValueError, match="resume configuration mismatch"):
        runner.run_experiment(
            experiment_spec("SPDR-022"), "ctrader", output, resume=True
        )


def test_complete_unit_hash_validation_has_bounded_python_memory(tmp_path):
    """A large Parquet artifact must be hashed as a stream, not one Python bytes object."""
    from xen.adaptive_management import runner

    unit = tmp_path / "unit"
    unit.mkdir()
    config_hash = "config"
    large_payload = b"x" * 20_000_000
    digest = hashlib.sha256()
    for index, name in enumerate(runner.UNIT_FRAMES):
        payload = large_payload if index == 0 else b"small"
        (unit / f"{name}.parquet").write_bytes(payload)
        digest.update(name.encode("utf-8"))
        digest.update(hashlib.sha256(payload).digest())
    (unit / runner.UNIT_COMPLETION_FILE).write_text(
        json.dumps(
            {
                "config_hash": config_hash,
                "content_hash": digest.hexdigest(),
                "rows": {},
            }
        )
    )
    del large_payload
    gc.collect()

    tracemalloc.start()
    assert runner._unit_is_complete(unit, config_hash)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert peak < 4_000_000


def test_default_mode_refuses_existing_in_progress_directory(monkeypatch, tmp_path):
    runner = _stub_execution(monkeypatch, fail_on={"USTEC"})
    output = tmp_path / "run"
    with pytest.raises(RuntimeError, match="synthetic interruption"):
        runner.run_experiment(experiment_spec("SPDR-021"), "ctrader", output)
    with pytest.raises(FileExistsError, match="in-progress"):
        runner.run_experiment(experiment_spec("SPDR-021"), "ctrader", output)


def test_resume_reuses_only_hash_valid_complete_units(monkeypatch, tmp_path):
    calls: list[str] = []
    runner = _stub_execution(monkeypatch, fail_on={"USTEC"}, calls=calls)
    output = tmp_path / "run"
    with pytest.raises(RuntimeError):
        runner.run_experiment(experiment_spec("SPDR-021"), "ctrader", output)
    assert calls == ["EURUSD", "XAUUSD", "USTEC"]

    calls.clear()
    _stub_execution(monkeypatch, calls=calls)
    resumed = runner.run_experiment(
        experiment_spec("SPDR-021"), "ctrader", output, resume=True
    )
    assert resumed["reused_units"] == 2
    assert resumed["rerun_units"] == 1
    assert calls == ["USTEC"]
    assert not (tmp_path / ".run.inprogress").exists()


def test_resume_reruns_a_unit_whose_stored_bytes_changed(monkeypatch, tmp_path):
    runner = _stub_execution(monkeypatch, fail_on={"USTEC"})
    output = tmp_path / "run"
    with pytest.raises(RuntimeError):
        runner.run_experiment(experiment_spec("SPDR-021"), "ctrader", output)
    corrupted = tmp_path / ".run.inprogress" / "units" / "EURUSD" / "orders.parquet"
    corrupted.write_bytes(b"corrupted")

    calls: list[str] = []
    _stub_execution(monkeypatch, calls=calls)
    resumed = runner.run_experiment(
        experiment_spec("SPDR-021"), "ctrader", output, resume=True
    )
    assert resumed["reused_units"] == 1
    assert sorted(calls) == ["EURUSD", "USTEC"]


def test_clean_parallel_and_resumed_outputs_are_byte_identical(monkeypatch, tmp_path):
    runner = _stub_execution(monkeypatch)
    clean = tmp_path / "clean"
    runner.run_experiment(experiment_spec("SPDR-021"), "ctrader", clean)

    parallel = tmp_path / "parallel"
    runner.run_experiment(experiment_spec("SPDR-021"), "ctrader", parallel, jobs=2)

    interrupted = tmp_path / "resumed"
    _stub_execution(monkeypatch, fail_on={"XAUUSD"})
    with pytest.raises(RuntimeError):
        runner.run_experiment(experiment_spec("SPDR-021"), "ctrader", interrupted)
    _stub_execution(monkeypatch)
    runner.run_experiment(
        experiment_spec("SPDR-021"), "ctrader", interrupted, resume=True
    )

    assert _canonical_hashes(clean) == _canonical_hashes(parallel)
    assert _canonical_hashes(clean) == _canonical_hashes(interrupted)


def test_progress_emits_first_per_unit_and_final_events(monkeypatch, tmp_path):
    runner = _stub_execution(monkeypatch)
    events: list[dict] = []
    runner.run_experiment(
        experiment_spec("SPDR-021"),
        "ctrader",
        tmp_path / "run",
        progress=events.append,
    )
    assert len(events) == 5  # first + 3 units + final
    assert events[0]["completed_units"] == 0
    assert [event["completed_units"] for event in events] == [0, 1, 2, 3, 3]
    assert all(event["total_units"] == 3 for event in events)
    assert events[-1]["eta_seconds"] is None
    assert events[1]["eta_seconds"] is not None
    assert events[-1]["rows_processed"] > 0
    assert set(events[0]) == {
        "experiment_id",
        "universe",
        "completed_units",
        "total_units",
        "elapsed_seconds",
        "rows_processed",
        "throughput_rows_per_second",
        "eta_seconds",
    }


def test_progress_heartbeats_without_completed_units(monkeypatch):
    from xen.adaptive_management.runner import _ProgressReporter

    events: list[dict] = []
    reporter = _ProgressReporter(
        events.append,
        experiment_id="SPDR-021",
        universe="ctrader",
        total_units=3,
        heartbeat_seconds=0.01,
    )
    reporter.start()
    deadline = time.monotonic() + 2.0
    while len(events) < 4 and time.monotonic() < deadline:
        time.sleep(0.01)
    reporter.stop()
    assert len(events) >= 4
    assert all(event["completed_units"] == 0 for event in events)


def test_base_trade_size_keeps_every_risk_multiple_on_the_instrument_grid():
    # A flat base of 1 is below the size increment of some crypto instruments, where a 0.5x
    # SIZE arm rounds to zero and the venue rejects the order mid-run.
    from decimal import Decimal

    from nautilus_trader.persistence.catalog import ParquetDataCatalog

    from xen.adaptive_management.runner import _base_trade_size, universe_config

    for universe in ("crypto", "ctrader"):
        config = universe_config(universe)
        catalog = ParquetDataCatalog(str(config.catalog_path))
        instruments = {str(item.id): item for item in catalog.instruments()}
        for instrument_id in config.instrument_ids:
            instrument = instruments[instrument_id]
            base = Decimal(_base_trade_size(instrument))
            increment = Decimal(str(instrument.size_increment))
            assert base % increment == 0
            for multiple in (Decimal("0.5"), Decimal("1"), Decimal("2")):
                quantity = instrument.make_qty(float(base * multiple))
                assert float(quantity) > 0


def test_base_size_is_part_of_the_run_identity(monkeypatch, tmp_path):
    from xen.adaptive_management import runner

    monkeypatch.setattr(runner, "_catalog_metadata", lambda config: {})
    payload = runner.run_experiment(
        experiment_spec("SPDR-021"), "ctrader", tmp_path / "plan", dry_run=True
    )
    assert payload["base_size_increments"] == runner.BASE_SIZE_INCREMENTS
    changed = {**payload, "base_size_increments": payload["base_size_increments"] + 1}
    assert runner._config_hash(changed) != runner._config_hash(payload)


def test_ctrader_instrument_adapter_preserves_currency_pair_and_cfd_types():
    from nautilus_trader.persistence.catalog import ParquetDataCatalog

    from xen.adaptive_management.engine import _make_instrument
    from xen.adaptive_management.runner import _instrument_spec, universe_config

    config = universe_config("ctrader")
    catalog = ParquetDataCatalog(str(config.catalog_path))
    instruments = {str(item.id): item for item in catalog.instruments()}
    rebuilt = {
        instrument_id: _make_instrument(
            _instrument_spec(symbol, instruments[instrument_id])
        )
        for symbol, instrument_id in zip(
            config.symbols, config.instrument_ids, strict=True
        )
    }
    assert type(rebuilt["EURUSD.CTrader"]).__name__ == "CurrencyPair"
    assert type(rebuilt["XAUUSD.CTrader"]).__name__ == "Cfd"
    assert type(rebuilt["USTEC.CTrader"]).__name__ == "Cfd"
