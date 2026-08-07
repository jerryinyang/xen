from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import polars as pl
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = (
    PROJECT_ROOT
    / "python/experiments/SPDR-011/design_derivations/census.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("spdr011_census", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_midrank_percentile_excludes_current_observation() -> None:
    census = _load_module()

    assert census.midrank_percentile(2.0, [1.0, 2.0, 3.0]) == pytest.approx(0.5)
    assert census.midrank_percentile(4.0, [1.0, 2.0, 3.0]) == pytest.approx(1.0)


def test_outcome_isolation_rejects_forward_price_or_return_columns() -> None:
    census = _load_module()
    safe = pl.DataFrame(
        {
            "event_id": ["E1"],
            "symbol": ["BTCUSDT"],
            "trigger_ts": [datetime(2023, 1, 1, 4, tzinfo=timezone.utc)],
            "entry_ts": [datetime(2023, 1, 1, 4, tzinfo=timezone.utc)],
            "exit_ts": [datetime(2023, 1, 1, 8, tzinfo=timezone.utc)],
            "direction": [1],
            "vol_tercile": ["HIGH"],
        }
    )
    census.assert_outcome_isolated(safe)

    for forbidden in ("entry_price", "exit_price", "return_4h_bps", "mfe_bps"):
        with pytest.raises(ValueError, match="outcome-isolation"):
            census.assert_outcome_isolated(safe.with_columns(pl.lit(0.0).alias(forbidden)))


def test_completed_breakout_locates_event_without_reading_entry_or_exit_prices() -> None:
    census = _load_module()
    state = pl.DataFrame(
        {
            "symbol": ["BTCUSDT"],
            "trade_day": [datetime(2023, 1, 2).date()],
            "prior_day_high": [105.0],
            "prior_day_low": [95.0],
            "rv20": [0.02],
            "vol_pct": [0.8],
            "vol_tercile": ["HIGH"],
            "drift20": [0.01],
            "beta60": [1.0],
            "cross_rank": [1],
            "cross_eligible": [True],
        }
    )
    bars_4h = pl.DataFrame(
        {
            "symbol": ["BTCUSDT", "BTCUSDT"],
            "slot_start": [
                datetime(2023, 1, 2, 0, tzinfo=timezone.utc),
                datetime(2023, 1, 2, 4, tzinfo=timezone.utc),
            ],
            "slot_end": [
                datetime(2023, 1, 2, 4, tzinfo=timezone.utc),
                datetime(2023, 1, 2, 8, tzinfo=timezone.utc),
            ],
            "close": [106.0, 94.0],
            "boundary_complete": [True, True],
        }
    )

    events = census.locate_breakouts(bars_4h, state)

    assert events.select("direction").to_series().to_list() == [1, -1]
    assert events.select("entry_ts").to_series().to_list() == bars_4h["slot_end"].to_list()
    assert "entry_price" not in events.columns
    assert "exit_price" not in events.columns


def test_mde_curve_uses_independent_date_count_not_episode_count() -> None:
    census = _load_module()

    sparse_dates = census.one_sample_mde_bps(n_effective_dates=25, sigma_bps=100.0)
    dense_dates = census.one_sample_mde_bps(n_effective_dates=100, sigma_bps=100.0)

    assert sparse_dates == pytest.approx(56.0)
    assert dense_dates == pytest.approx(28.0)


def test_state_records_accept_rank_values_after_long_null_prefix() -> None:
    census = _load_module()
    records = [
        {"symbol": "BTCUSDT", "cross_rank": None}
        for _ in range(127)
    ] + [{"symbol": "BTCUSDT", "cross_rank": 2}]

    frame = census.state_records_frame(records)

    assert frame["cross_rank"][-1] == 2


def test_final_event_table_accepts_rank_after_long_null_prefix() -> None:
    census = _load_module()
    start = datetime(2022, 10, 1, tzinfo=timezone.utc)
    rows = []
    for index in range(128):
        entry = start + index * census.timedelta(hours=4)
        rows.append(
            {
                "symbol": "BTCUSDT",
                "trigger_ts": entry,
                "entry_ts": entry,
                "exit_ts": entry + census.timedelta(hours=4),
                "trade_day": entry.date(),
                "utc_slot": entry.hour,
                "direction": 1,
                "rv20": 0.02,
                "vol_pct": 0.8,
                "vol_tercile": "HIGH",
                "drift20": 0.01,
                "beta60": 1.0,
                "cross_rank": None if index < 127 else 2,
                "cross_eligible": index == 127,
                "state_source_day": entry.date() - census.timedelta(days=1),
                "state_known_ts": datetime.combine(entry.date(), census.time.min, tzinfo=timezone.utc),
                "range_source_day": entry.date() - census.timedelta(days=1),
                "range_known_ts": datetime.combine(entry.date(), census.time.min, tzinfo=timezone.utc),
            }
        )

    events = census.finalise_events(pl.DataFrame(rows, infer_schema_length=None))

    assert events.height == 128
    assert events["cross_rank"][-1] == 2


def test_attested_no_trade_minute_does_not_make_completed_interval_missing() -> None:
    census = _load_module()
    minutes = pl.DataFrame(
        {
            "symbol": ["BTCUSDT", "BTCUSDT"],
            "ts_event": [
                datetime(2023, 1, 1, 0, 1, tzinfo=timezone.utc),
                datetime(2023, 1, 1, 3, 59, tzinfo=timezone.utc),
            ],
            "open": [100.0, 101.0],
            "high": [101.0, 102.0],
            "low": [99.0, 100.0],
            "close": [100.5, 101.5],
        }
    )

    daily, bars_4h = census.aggregate_inputs(minutes, coverage_attested=True)

    assert daily["boundary_complete"].to_list() == [True]
    assert bars_4h["boundary_complete"].to_list() == [True]


def test_design_calendar_thirds_use_effective_eligible_interval() -> None:
    census = _load_module()

    assert census._calendar_third(
        datetime(2022, 10, 1, tzinfo=timezone.utc), "DESIGN"
    ) == 1
    assert census._calendar_third(
        datetime(2022, 12, 1, tzinfo=timezone.utc), "DESIGN"
    ) == 2
    assert census._calendar_third(
        datetime(2023, 2, 1, tzinfo=timezone.utc), "DESIGN"
    ) == 3


def test_signed_status_separates_raw_source_and_verified_catalog(tmp_path: Path) -> None:
    census = _load_module()
    census.ROOT = tmp_path
    census.OUT = tmp_path / "python/experiments/SPDR-011/results"
    source = (
        tmp_path
        / "archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-011/data/staging/bars"
    )
    source.mkdir(parents=True)
    for symbol in census.SYMBOLS:
        (source / f"{symbol}.parquet").write_bytes(b"source")
    catalog = tmp_path / "data/catalog_sigbar/train/data"
    catalog.mkdir(parents=True)
    (catalog / "part.parquet").write_bytes(b"catalog")
    census.OUT.mkdir(parents=True)
    (census.OUT / "signed_train_attestation.json").write_text(
        json.dumps(
            {
                "status": "VERIFIED",
                "symbols": list(census.SYMBOLS),
                "catalog_tree_sha256": "fixture",
                "per_symbol": {
                    symbol: {"status": "VERIFIED"} for symbol in census.SYMBOLS
                },
            }
        ),
        encoding="utf-8",
    )

    status = census._signed_data_status()

    assert status["raw_source_readable"] is True
    assert status["train_catalog_verified"] is True
    assert status["ready"] is True
    assert status["attestation_status"] == "VERIFIED"
