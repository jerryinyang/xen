"""INFR-010 Phase B unit tests — instrument ids, emission, adjudication shim."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import polars as pl
import pytest

from xen.nautilus.adjudication_shim import (
    adjudicate_emission,
    bar_marks_to_positions,
    positions_ledger_to_cis_trades,
)
from xen.nautilus.emission import EMISSION_CONTRACT_VERSION, load_emission_v1, write_emission_v1
from xen.nautilus.instrument_ids import (
    archive_symbol_to_instrument_id_str,
    instrument_id_to_archive_symbol,
    parse_instrument_id_str,
)


def test_archive_symbol_mapping() -> None:
    assert archive_symbol_to_instrument_id_str("BTCUSDT") == "BTCUSDT-LINEAR.BYBIT"
    assert archive_symbol_to_instrument_id_str("ethusdt") == "ETHUSDT-LINEAR.BYBIT"
    assert instrument_id_to_archive_symbol("SOLUSDT-LINEAR.BYBIT") == "SOLUSDT"
    archive, product, venue = parse_instrument_id_str("XRPUSDT-LINEAR.BYBIT")
    assert (archive, product, venue) == ("XRPUSDT", "LINEAR", "BYBIT")


def test_archive_symbol_rejects_non_usdt() -> None:
    with pytest.raises(ValueError):
        archive_symbol_to_instrument_id_str("BTCPERP")  # USDC
    with pytest.raises(ValueError):
        archive_symbol_to_instrument_id_str("BTCUSD")  # inverse-ish


def test_emission_roundtrip_and_shim(tmp_path: Path) -> None:
    bars = pl.DataFrame(
        {
            "SourceCloseTime": [
                datetime(2024, 1, 1, 0, 0),
                datetime(2024, 1, 1, 0, 1),
                datetime(2024, 1, 1, 0, 2),
                datetime(2024, 1, 1, 0, 3),
            ],
            "RealOpen": [100.0, 101.0, 102.0, 103.0],
        }
    ).with_columns(pl.col("SourceCloseTime").cast(pl.Datetime("ns")))
    ledger = pl.DataFrame(
        {
            "instrument_id": ["BTCUSDT-LINEAR.BYBIT"],
            "entry": ["BUY"],
            "side": ["FLAT"],
            "quantity": [0.0],
            "peak_qty": [1.0],
            "avg_px_open": [100.5],
            "avg_px_close": [102.5],
            "realized_return": [0.0199],
            "realized_pnl": ["2.0 USDT"],
            "ts_opened": [datetime(2024, 1, 1, 0, 0, 30)],
            "ts_closed": [datetime(2024, 1, 1, 0, 2, 30)],
            "duration_ns": [120_000_000_000],
            "commissions": ["0.1 USDT"],
        }
    ).with_columns(
        pl.col("ts_opened").cast(pl.Datetime("ns")),
        pl.col("ts_closed").cast(pl.Datetime("ns")),
    )
    fills = pl.DataFrame(
        {
            "client_order_id": ["O-1", "O-2"],
            "instrument_id": ["BTCUSDT-LINEAR.BYBIT"] * 2,
            "side": ["BUY", "SELL"],
            "quantity": ["1", "1"],
            "filled_qty": ["1", "1"],
            "avg_px": [100.5, 102.5],
            "status": ["FILLED", "FILLED"],
            "liquidity_side": ["TAKER", "TAKER"],
            "ts_init": [1, 2],
            "ts_last": [1, 2],
            "commissions": ["0.05 USDT", "0.05 USDT"],
        }
    )
    run_dir = tmp_path / "run"
    paths = write_emission_v1(
        run_dir,
        fills=fills,
        orders=fills,
        positions_ledger=ledger,
        bar_marks=bars,
        instrument_id_map={"BTCUSDT": "BTCUSDT-LINEAR.BYBIT"},
        run_config={"strategy": "unit", "seed": 1},
        nautilus_version="1.230.0",
        platform="test",
    )
    assert paths.run_metadata.exists()
    loaded = load_emission_v1(run_dir)
    assert loaded.metadata["emission_contract_version"] == EMISSION_CONTRACT_VERSION
    assert loaded.metadata["event_log_sha256"]
    # second write of identical economic content → same event log hash
    paths2 = write_emission_v1(
        tmp_path / "run2",
        fills=fills,
        orders=fills,
        positions_ledger=ledger,
        bar_marks=bars,
        instrument_id_map={"BTCUSDT": "BTCUSDT-LINEAR.BYBIT"},
        run_config={"strategy": "unit", "seed": 1},
        nautilus_version="1.230.0",
        platform="test",
    )
    assert paths.event_log.read_text() == paths2.event_log.read_text()

    cis = positions_ledger_to_cis_trades(ledger)
    assert cis.height == 1
    assert cis["Direction"][0] == 1
    assert cis["RealizedBps"][0] == pytest.approx(1 * (102.5 - 100.5) / 100.5 * 1e4)

    pos = bar_marks_to_positions(bars)
    assert "SourceCloseTime" in pos.columns and "RealOpen" in pos.columns

    bundle = adjudicate_emission(run_dir, cost_bps=0.0)
    assert bundle.series is not None
    assert bundle.reconcile_report is not None
    assert bundle.reconcile_report.ok
