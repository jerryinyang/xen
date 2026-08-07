"""Nautilus execution tests: pending expiry, competing exits and one slot per arm.

Golden trace 3 (SPDR-021 design): long fill 100, target 102, stop 98; the target is reached in
the 10:02Z minute and a later fall through 98 cannot rewrite that exit.

Every engine runs in its own spawned process (L-31: a second BacktestNode in one process
aborts the Rust runtime).
"""

import gc
import hashlib
import tracemalloc
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import polars as pl
import pytest

from xen.adaptive_management.engine import (
    InstrumentSpec, WorkUnit, _make_instrument, run_work_unit, run_work_unit_subprocess,
)
from xen.adaptive_management.contracts import build_native_lattice
from xen.adaptive_management.entries import breach_origins
from xen.adaptive_management.native_parameters import materialise_native_arm
from xen.adaptive_management.strategy import AdaptiveManagementConfig, AdaptiveManagementStrategy
from nautilus_trader.model.identifiers import ClientOrderId, InstrumentId
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from xen.nautilus.catalog_fence import FenceManifest, fenced_bar_query

START = datetime(2023, 1, 1, 10, 0, tzinfo=UTC)
SPEC = InstrumentSpec(
    symbol="XRPUSDT-LINEAR",
    instrument_id="XRPUSDT-LINEAR.BYBIT",
    venue="BYBIT",
    price_precision=4,
    size_precision=0,
    price_increment="0.0001",
    size_increment="1",
    base_currency="XRP",
)


def _schedule(tmp_path, rows: list[dict]) -> str:
    defaults = {
        "experiment_id": "SPDR-021",
        "native_arm_id": "FIXED_NATIVE_BREAKOUT",
        "policy_id": "FIXED_BASELINE_PLAIN",
        "device": "NONE",
        "entry_variant": "BREAKOUT",
        "exit_reason": None,
        "arm_class": "NATIVE",
        "hold_bars": None,
        "target_distance_bps": None,
        "stop_distance_bps": None,
        "trail_distance_bps": None,
        "trail_activation_bps": None,
        "risk_size": 1.0,
        "state": "ORDER_CREATED",
        "entry_order_type": "STOP",
    }
    records = []
    for row in rows:
        record = {**defaults, **row}
        record.setdefault("actionable_ts", record["decision_ts"])
        records.append(record)
    frame = pl.DataFrame(records)
    path = tmp_path / "schedule.parquet"
    frame.write_parquet(path)
    return str(path)


def _bars_parquet(tmp_path, ohlc) -> str:
    frame = pl.DataFrame(
        {
            "ts": [START + timedelta(minutes=i) for i in range(len(ohlc))],
            "open": [r[0] for r in ohlc],
            "high": [r[1] for r in ohlc],
            "low": [r[2] for r in ohlc],
            "close": [r[3] for r in ohlc],
            "volume": [1000.0] * len(ohlc),
        }
    )
    path = tmp_path / "bars.parquet"
    frame.write_parquet(path)
    return str(path)


def _run(tmp_path, ohlc, rows):
    unit = WorkUnit(
        unit_id="TEST",
        instrument=SPEC,
        bars_path=_bars_parquet(tmp_path, ohlc),
        schedule_path=_schedule(tmp_path, rows),
        output_dir=str(tmp_path / "out"),
        base_trade_size="100",
    )
    reports = run_work_unit_subprocess(unit, timeout=300)
    return reports["state_ledger"], reports["fills"], reports["positions"]


def _run_reports(tmp_path, ohlc, rows):
    unit = WorkUnit(
        unit_id="REPORT",
        instrument=SPEC,
        bars_path=_bars_parquet(tmp_path, ohlc),
        schedule_path=_schedule(tmp_path, rows),
        output_dir=str(tmp_path / "report-out"),
        base_trade_size="100",
    )
    return run_work_unit_subprocess(unit, timeout=300)


def _row(**overrides) -> dict:
    base = {
        "arm_id": "ARM",
        "origin_id": "O1",
        "episode_id": "E1",
        "decision_ts": START,
        "side": 1,
        "stop_price": 100.0,
        "expiry_bars": 2,
    }
    base.update(overrides)
    return base


def _strategy_without_engine(tmp_path, row):
    strategy = AdaptiveManagementStrategy(
        AdaptiveManagementConfig(
            instrument_id=InstrumentId.from_str("XRPUSDT-LINEAR.BYBIT"),
            bar_type="XRPUSDT-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL",
            schedule_path=_schedule(tmp_path, [row]),
            base_trade_size=Decimal("100"),
            fence_start_ns=int(START.timestamp() * 1e9),
            fence_end_ns=int((START + timedelta(hours=8)).timestamp() * 1e9),
        )
    )
    scheduled = strategy._next_schedule_row
    assert scheduled is not None
    strategy._execution_rows[(str(scheduled["episode_id"]), str(scheduled["policy_id"]))] = scheduled
    return strategy, scheduled


def test_strategy_initialisation_does_not_retain_one_python_object_per_schedule_row(
    tmp_path,
):
    """A larger frozen schedule may grow columnar storage, not Python heap per row."""

    def peak_python_bytes(root: Path, count: int) -> int:
        root.mkdir()
        rows = [
            _row(
                arm_id=f"ARM-{index}",
                origin_id=f"O-{index}",
                episode_id=f"E-{index}",
                state="NO_EVENT",
                entry_order_type="NONE",
                stop_price=None,
            )
            for index in range(count)
        ]
        schedule_path = _schedule(root, rows)
        del rows
        gc.collect()
        tracemalloc.start()
        strategy = AdaptiveManagementStrategy(
            AdaptiveManagementConfig(
                instrument_id=InstrumentId.from_str("XRPUSDT-LINEAR.BYBIT"),
                bar_type="XRPUSDT-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL",
                schedule_path=schedule_path,
                base_trade_size=Decimal("100"),
                fence_start_ns=int(START.timestamp() * 1e9),
                fence_end_ns=int((START + timedelta(hours=8)).timestamp() * 1e9),
            )
        )
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        del strategy
        gc.collect()
        return peak

    small_peak = peak_python_bytes(tmp_path / "small", 100)
    large_peak = peak_python_bytes(tmp_path / "large", 20_000)
    assert large_peak < small_peak + 8_000_000


def test_forget_releases_client_order_state_but_keeps_idempotency_guards(tmp_path):
    strategy, row = _strategy_without_engine(tmp_path, _row())
    key = ("E1", "FIXED_BASELINE_PLAIN")
    client_order_id = "O-19700101-000000-001-001-1"
    strategy._execution_rows[key] = row
    strategy._orders_by_execution[key].append(client_order_id)
    strategy._by_client_order[client_order_id] = row
    strategy._entry_orders.add(client_order_id)
    strategy._entry_terminal.add(key)
    strategy._closed.add(key)

    strategy._forget(key)

    assert client_order_id not in strategy._by_client_order
    assert client_order_id not in strategy._entry_orders
    assert key in strategy._entry_terminal
    assert key in strategy._closed


def test_protective_exits_wait_until_the_filled_position_is_visible(
    monkeypatch, tmp_path
):
    strategy, row = _strategy_without_engine(
        tmp_path,
        _row(
            experiment_id="SPDR-022",
            entry_order_type="MARKET",
            stop_price=None,
            expiry_bars=None,
            target_distance_bps=100.0,
            stop_distance_bps=100.0,
            trail_distance_bps=100.0,
            trail_activation_bps=50.0,
        ),
    )
    submitted = []
    visible = {"position": None}

    def capture_exit(self, row, device, distance, entry_price, exit_side, quantity):
        submitted.append((device, quantity, self._episode_position[("E1", "FIXED_BASELINE_PLAIN")]))

    monkeypatch.setattr(AdaptiveManagementStrategy, "_submit_exit", capture_exit)
    monkeypatch.setattr(
        AdaptiveManagementStrategy,
        "_confirmed_position",
        lambda self, key: visible["position"],
        raising=False,
    )
    fill = SimpleNamespace(last_px=Decimal("100"), last_qty=Decimal("40"), ts_event=1)
    strategy._on_entry_filled(row, fill)
    assert submitted == []

    key = ("E1", "FIXED_BASELINE_PLAIN")
    visible["position"] = SimpleNamespace(
        id=strategy._episode_position[key], is_closed=False, quantity=Decimal("40")
    )
    strategy.on_position_opened(
        SimpleNamespace(position_id=strategy._episode_position[key])
    )
    assert [device for device, _, _ in submitted] == ["TARGET", "STOP", "TRAIL"]
    assert all(position_id == strategy._episode_position[key] for _, _, position_id in submitted)


@pytest.mark.parametrize(
    ("device", "distances", "ohlc"),
    [
        (
            "TARGET",
            {"target_distance_bps": 200.0},
            [(100.0, 100.1, 99.9, 100.0), (100.0, 103.0, 99.9, 102.5)],
        ),
        (
            "STOP",
            {"stop_distance_bps": 200.0},
            [(100.0, 100.1, 99.9, 100.0), (100.0, 100.1, 97.0, 97.5)],
        ),
        (
            "TRAIL",
            {"trail_distance_bps": 200.0, "trail_activation_bps": 100.0},
            [
                (100.0, 100.1, 99.9, 100.0),
                (100.0, 102.5, 99.9, 102.0),
                (102.0, 102.1, 99.0, 99.5),
            ],
        ),
    ],
)
def test_protective_orders_use_the_confirmed_entry_position_id(
    tmp_path, device, distances, ohlc
):
    reports = _run_reports(
        tmp_path,
        ohlc,
        [
            _row(
                experiment_id="SPDR-022",
                entry_order_type="MARKET",
                stop_price=None,
                expiry_bars=None,
                **distances,
            )
        ],
    )
    orders = reports["orders"]
    entry = orders.filter(pl.col("tags").str.contains("leg=ENTRY")).row(0, named=True)
    protective = orders.filter(
        pl.col("tags").str.contains(f"device={device}")
    ).row(0, named=True)
    assert protective["position_id"] == entry["position_id"]
    assert protective["position_id"] is not None


@pytest.mark.parametrize(
    ("experiment_id", "entry_variant", "entry_order_type", "size_hold"),
    [
        ("SPDR-021", "BREAKOUT", "STOP", 1),
        ("SPDR-022", "E_TOUCH", "MARKET", 4),
        ("SPDR-022", "E_CLOSE", "MARKET", 4),
        ("SPDR-023", "E_TOUCH", "MARKET", 4),
        ("SPDR-023", "E_CLOSE", "MARKET", 4),
    ],
)
def test_amended_synthetic_trace_covers_each_experiment_and_entry_variant(
    tmp_path, experiment_id, entry_variant, entry_order_type, size_hold
):
    entry_fields = {
        "experiment_id": experiment_id,
        "entry_variant": entry_variant,
        "entry_order_type": entry_order_type,
        "stop_price": 100.0 if entry_order_type == "STOP" else None,
        "expiry_bars": 2 if entry_order_type == "STOP" else None,
    }
    rows = [
        _row(
            **entry_fields,
            arm_id="PROTECTIVE",
            policy_id="PROTECTIVE",
            device="TARGET+STOP+TRAIL",
            target_distance_bps=500.0,
            stop_distance_bps=500.0,
            trail_distance_bps=500.0,
            trail_activation_bps=500.0,
        ),
        _row(
            **entry_fields,
            arm_id="ADAPTIVE-HOLD",
            policy_id="ADAPTIVE-HOLD",
            device="HOLD",
            hold_bars=2,
        ),
        _row(
            **entry_fields,
            arm_id="ADAPTIVE-SIZE",
            policy_id="ADAPTIVE-SIZE",
            device="SIZE",
            hold_bars=size_hold,
            risk_size=0.5,
        ),
    ]
    opening = (
        [(99.5, 99.6, 99.4, 99.5), (99.5, 101.0, 99.0, 100.5)]
        if entry_order_type == "STOP"
        else [(100.0, 100.1, 99.9, 100.0)]
    )
    flat = 100.5 if entry_order_type == "STOP" else 100.0
    ohlc = opening + [(flat, flat + 0.1, flat - 0.1, flat)] * (
        max(size_hold, 2) * 60 + 5
    )
    reports = _run_reports(tmp_path, ohlc, rows)
    ledger = reports["state_ledger"]
    expected = {
        "PROTECTIVE": ["ORDER_CREATED", "FILLED", "OPEN_AT_FENCE_END"],
        "ADAPTIVE-HOLD": ["ORDER_CREATED", "FILLED", "HOLD_DUE", "CLOSED"],
        "ADAPTIVE-SIZE": ["ORDER_CREATED", "FILLED", "HOLD_DUE", "CLOSED"],
    }
    for policy_id, states in expected.items():
        observed = ledger.filter(pl.col("policy_id") == policy_id)["state"].to_list()
        assert observed == states
    protective = reports["orders"].filter(
        pl.col("tags").str.contains("policy_id=PROTECTIVE")
        & pl.col("tags").str.contains("leg=(TARGET|STOP|TRAIL)")
    )
    assert set(protective["status"]) == {"ACCEPTED"}
    assert set(
        protective["tags"].str.extract(r"device=(TARGET|STOP|TRAIL)", 1)
    ) == {"TARGET", "STOP", "TRAIL"}
    for policy_id, hold_bars in (
        ("ADAPTIVE-HOLD", 2),
        ("ADAPTIVE-SIZE", size_hold),
    ):
        states = ledger.filter(pl.col("policy_id") == policy_id)
        filled_ns = states.filter(pl.col("state") == "FILLED")["ts_ns"][0]
        due_ns = states.filter(pl.col("state") == "HOLD_DUE")["ts_ns"][0]
        assert due_ns - filled_ns == hold_bars * 3_600_000_000_000


def test_denied_protective_leg_submits_one_failsafe(monkeypatch, tmp_path):
    strategy, row = _strategy_without_engine(tmp_path, _row(stop_distance_bps=100.0))
    key = ("E1", "FIXED_BASELINE_PLAIN")
    strategy._episode_position[key] = SimpleNamespace(value="P1")
    strategy._busy[("ARM", "BREAKOUT")] = "E1"
    strategy._by_client_order["PROTECT"] = row
    strategy._open_exits[key].append(
        SimpleNamespace(client_order_id="PROTECT", tags=["device=STOP"], is_open=True)
    )
    created = []
    submitted = []

    def market(**kwargs):
        created.append(kwargs)
        return SimpleNamespace(client_order_id="FAILSAFE", is_open=True)

    monkeypatch.setattr(
        AdaptiveManagementStrategy,
        "order_factory",
        SimpleNamespace(market=market),
    )
    monkeypatch.setattr(
        AdaptiveManagementStrategy,
        "_confirmed_position",
        lambda self, execution: SimpleNamespace(
            is_closed=False, is_long=True, quantity=Decimal("100")
        ),
    )
    monkeypatch.setattr(
        AdaptiveManagementStrategy,
        "submit_order",
        lambda self, order, position_id=None: submitted.append(
            (str(order.client_order_id), position_id)
        ),
    )
    event = SimpleNamespace(client_order_id="PROTECT", ts_event=10)
    strategy.on_order_denied(event)
    strategy.on_order_denied(event)
    assert len(created) == 1
    assert created[0]["reduce_only"] is True
    assert created[0]["quantity"] == Decimal("100")
    assert submitted == [("FAILSAFE", strategy._episode_position[key])]
    assert ("ARM", "BREAKOUT") in strategy._busy


def test_exit_failure_keeps_the_typed_client_order_id_for_cache_lookup(
    monkeypatch, tmp_path
):
    strategy, row = _strategy_without_engine(tmp_path, _row(stop_distance_bps=100.0))
    strategy._by_client_order["PROTECT"] = row
    seen = []
    monkeypatch.setattr(
        AdaptiveManagementStrategy,
        "_order_for_client",
        lambda self, client_order_id, key: seen.append(client_order_id)
        or SimpleNamespace(tags=["device=STOP"]),
    )
    monkeypatch.setattr(
        AdaptiveManagementStrategy,
        "_submit_failsafe",
        lambda self, key, ts_event: None,
    )
    client_order_id = ClientOrderId("PROTECT")
    strategy.on_order_rejected(
        SimpleNamespace(client_order_id=client_order_id, ts_event=10)
    )
    assert seen == [client_order_id]


def test_successful_failsafe_closes_cancels_and_releases(monkeypatch, tmp_path):
    strategy, row = _strategy_without_engine(tmp_path, _row(stop_distance_bps=100.0))
    key = ("E1", "FIXED_BASELINE_PLAIN")
    slot = ("ARM", "BREAKOUT")
    strategy._busy[slot] = "E1"
    strategy._episode_position[key] = SimpleNamespace(value="P1")
    sibling = SimpleNamespace(client_order_id="STOP", is_open=True)
    failsafe = SimpleNamespace(
        client_order_id="FAILSAFE", tags=["device=FAILSAFE"], is_open=False
    )
    strategy._open_exits[key].extend([sibling, failsafe])
    canceled = []
    monkeypatch.setattr(
        AdaptiveManagementStrategy,
        "cancel_order",
        lambda self, order: canceled.append(str(order.client_order_id)),
    )
    strategy._on_exit_filled(
        row,
        SimpleNamespace(client_order_id="FAILSAFE", ts_event=20, last_px=Decimal("99")),
        failsafe,
    )
    assert strategy.state_ledger[-1]["state"] == "CLOSED"
    assert strategy.state_ledger[-1]["exit_reason"] == "FAILSAFE"
    assert canceled == ["STOP"]
    assert slot not in strategy._busy

    submitted = []
    later = {
        **row,
        "episode_id": "E2",
        "origin_id": "O2",
        "entry_order_type": "MARKET",
    }
    strategy.instrument = SimpleNamespace(make_qty=lambda quantity: quantity)
    monkeypatch.setattr(
        AdaptiveManagementStrategy,
        "order_factory",
        SimpleNamespace(
            market=lambda **kwargs: SimpleNamespace(client_order_id="ENTRY-2")
        ),
    )
    monkeypatch.setattr(
        AdaptiveManagementStrategy,
        "submit_order",
        lambda self, order, position_id=None: submitted.append(str(order.client_order_id)),
    )
    strategy._act_on_origin(later, SimpleNamespace(ts_event=30))
    assert submitted == ["ENTRY-2"]
    assert strategy._busy[slot] == "E2"


def test_denied_failsafe_aborts_the_work_unit(tmp_path):
    strategy, row = _strategy_without_engine(tmp_path, _row(stop_distance_bps=100.0))
    strategy._by_client_order["FAILSAFE"] = row
    strategy._failsafe_orders = {"FAILSAFE"}
    with pytest.raises(RuntimeError, match="fail-safe"):
        strategy.on_order_denied(
            SimpleNamespace(client_order_id="FAILSAFE", ts_event=30)
        )


def test_partial_entry_fills_keep_one_terminal_row_and_exact_exit_quantity(
    monkeypatch, tmp_path
):
    strategy, row = _strategy_without_engine(
        tmp_path, _row(target_distance_bps=100.0)
    )
    visible = {"position": None}
    quantities = []
    monkeypatch.setattr(
        AdaptiveManagementStrategy,
        "_confirmed_position",
        lambda self, key: visible["position"],
        raising=False,
    )
    monkeypatch.setattr(
        AdaptiveManagementStrategy,
        "_submit_exit",
        lambda self, row, device, distance, entry_price, exit_side, quantity: quantities.append(quantity),
    )
    strategy._on_entry_filled(
        row, SimpleNamespace(last_px=Decimal("100"), last_qty=Decimal("40"), ts_event=1)
    )
    key = ("E1", "FIXED_BASELINE_PLAIN")
    visible["position"] = SimpleNamespace(
        id=strategy._episode_position[key], is_closed=False, quantity=Decimal("40")
    )
    strategy.on_position_opened(SimpleNamespace(position_id=strategy._episode_position[key]))
    strategy._on_entry_filled(
        row, SimpleNamespace(last_px=Decimal("100"), last_qty=Decimal("60"), ts_event=2)
    )
    assert [record["state"] for record in strategy.state_ledger].count("FILLED") == 1
    assert sum(quantities, Decimal("0")) == Decimal("100")


@pytest.mark.parametrize("device", ["TARGET"])
def test_target_before_later_stop_is_not_rewritten(tmp_path, device):
    ohlc = [
        (99.5, 99.6, 99.4, 99.5),  # decision minute; entry stop at 100 becomes live next minute
        (99.5, 101.0, 99.0, 100.5),  # 10:01 - entry triggers at 100
        (100.5, 102.2, 99.5, 102.0),  # 10:02 - target 102 reached
        (102.0, 102.0, 97.0, 97.5),  # later fall through 98 must not rewrite the exit
    ]
    rows = [_row(target_distance_bps=200.0, stop_distance_bps=200.0, hold_bars=None)]
    ledger, fills, positions = _run(tmp_path, ohlc, rows)
    closed = ledger.filter(pl.col("state") == "CLOSED")
    assert closed.height == 1
    assert closed.row(0, named=True)["exit_reason"] == "TARGET"
    assert float(positions.row(0, named=True)["avg_px_close"]) == pytest.approx(102.0, abs=0.05)


def test_pending_order_expires_after_two_h1_bars(tmp_path):
    ohlc = [(99.5, 99.6, 99.4, 99.5)] + [(99.5, 99.7, 99.3, 99.5)] * 200
    ledger, fills, _ = _run(tmp_path, ohlc, [_row(stop_price=105.0, expiry_bars=2)])
    states = set(ledger["state"])
    assert "EXPIRED" in states
    assert "FILLED" not in states
    assert len(fills) == 0


def test_shorter_expiry_expires_where_longer_expiry_fills(tmp_path):
    # touch of 105 happens in the third H1 bar: expiry 1 and 2 expire, expiry 4 fills.
    ohlc = [(99.5, 99.6, 99.4, 99.5)] * 130 + [(99.5, 106.0, 99.4, 105.5)] + [
        (105.5, 105.6, 105.4, 105.5)
    ] * 60
    rows = [
        _row(arm_id="SHORT_EXPIRY", episode_id="E_SHORT", stop_price=105.0, expiry_bars=1),
        _row(arm_id="LONG_EXPIRY", episode_id="E_LONG", stop_price=105.0, expiry_bars=4),
    ]
    ledger, _, _ = _run(tmp_path, ohlc, rows)
    by_arm = {
        arm: set(group["state"])
        for arm, group in ledger.group_by("arm_id")
        for arm in [arm[0] if isinstance(arm, tuple) else arm]
    }
    assert "EXPIRED" in by_arm["SHORT_EXPIRY"]
    assert "FILLED" not in by_arm["SHORT_EXPIRY"]
    assert "FILLED" in by_arm["LONG_EXPIRY"]


def test_no_event_origin_is_recorded_not_dropped(tmp_path):
    ohlc = [(99.5, 99.6, 99.4, 99.5)] * 5
    ledger, fills, _ = _run(
        tmp_path,
        ohlc,
        [_row(stop_price=None, state="NO_EVENT", entry_order_type="NONE")],
    )
    assert ledger.row(0, named=True)["state"] == "NO_EVENT"
    assert len(fills) == 0


def test_second_origin_while_arm_is_active_is_blocked_not_dropped(tmp_path):
    ohlc = [
        (99.5, 99.6, 99.4, 99.5),
        (99.5, 101.0, 99.0, 100.5),
    ] + [(100.5, 100.6, 100.4, 100.5)] * 5
    rows = [
        _row(episode_id="E1", origin_id="O1", decision_ts=START, hold_bars=4),
        _row(episode_id="E2", origin_id="O2", decision_ts=START + timedelta(minutes=2), hold_bars=4),
    ]
    ledger, _, _ = _run(tmp_path, ohlc, rows)
    states = dict(zip(ledger["episode_id"], ledger["state"], strict=False))
    assert "BLOCKED_ACTIVE" in set(ledger.filter(pl.col("episode_id") == "E2")["state"])
    assert states  # every scheduled origin appears in the ledger
    assert set(ledger["episode_id"]) == {"E1", "E2"}


def test_batched_ledger_matches_an_unbatched_one_byte_for_byte(tmp_path):
    # The ledger is millions of rows on a full span, so it is flushed to disk in batches.
    # Batch size must be an operational knob only: the emitted file cannot depend on it.
    from xen.adaptive_management import strategy as strategy_module

    ohlc = [
        (99.5, 99.6, 99.4, 99.5),
        (99.5, 101.0, 99.0, 100.5),
        (100.5, 102.2, 99.5, 102.0),
    ] + [(102.0, 102.1, 101.9, 102.0)] * 40
    rows = [
        _row(arm_id=f"ARM{i}", episode_id=f"E{i}", origin_id=f"O{i}", hold_bars=1,
             target_distance_bps=200.0, stop_distance_bps=200.0)
        for i in range(12)
    ]
    schedule_path = _schedule(tmp_path, rows)
    bars_path = _bars_parquet(tmp_path, ohlc)
    assert strategy_module.LEDGER_BATCH_ROWS > 0
    digests = []
    for index, batch in enumerate((3, 10_000_000)):
        out = tmp_path / f"batch-{index}"
        run_work_unit_subprocess(
            WorkUnit(
                unit_id=f"BATCH{index}",
                instrument=SPEC,
                bars_path=bars_path,
                schedule_path=schedule_path,
                output_dir=str(out),
                base_trade_size="100",
                ledger_batch_rows=batch,
            ),
            timeout=300,
        )
        assert not (out / "_ledger_parts").exists()
        digests.append(
            hashlib.sha256((out / "state_ledger.parquet").read_bytes()).hexdigest()
        )
    assert digests[0] == digests[1]
    assert pl.read_parquet(tmp_path / "batch-0" / "state_ledger.parquet").height > 12


def test_two_runs_of_one_work_unit_are_byte_identical(tmp_path):
    # Nautilus stamps every event with a fresh UUID. Left in the emission it makes two runs of
    # the same input differ, which would make any replay comparison meaningless.
    from xen.adaptive_management.engine import EPHEMERAL_ID_COLUMNS

    ohlc = [
        (99.5, 99.6, 99.4, 99.5),
        (99.5, 101.0, 99.0, 100.5),
        (100.5, 102.2, 99.5, 102.0),
    ] + [(102.0, 102.1, 101.9, 102.0)] * 60
    rows = [_row(target_distance_bps=200.0, stop_distance_bps=200.0, hold_bars=1)]
    schedule_path = _schedule(tmp_path, rows)
    bars_path = _bars_parquet(tmp_path, ohlc)

    digests = []
    for index in (1, 2):
        out = tmp_path / f"replay-{index}"
        run_work_unit_subprocess(
            WorkUnit(
                unit_id=f"REPLAY{index}",
                instrument=SPEC,
                bars_path=bars_path,
                schedule_path=schedule_path,
                output_dir=str(out),
                base_trade_size="100",
            ),
            timeout=300,
        )
        digests.append(
            {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(out.glob("*.parquet"))
            }
        )
    assert digests[0] == digests[1]
    assert set(digests[0]) == {
        "orders.parquet", "fills.parquet", "positions.parquet", "state_ledger.parquet",
    }
    orders = pl.read_parquet(tmp_path / "replay-1" / "orders.parquet")
    assert not set(EPHEMERAL_ID_COLUMNS) & set(orders.columns)


def test_high_turnover_emission_matches_the_pinned_accounting_reference(tmp_path):
    """Skipping shared-account arithmetic must not change any emitted engine report."""
    rows = [
        _row(
            experiment_id="SPDR-022",
            entry_variant="E_TOUCH",
            entry_order_type="MARKET",
            stop_price=None,
            expiry_bars=None,
            arm_id=f"ARM-{index}",
            policy_id=f"POLICY-{index}",
            episode_id=f"E-{index}",
            origin_id=f"O-{index}",
            hold_bars=1,
        )
        for index in range(100)
    ]
    reports = _run_reports(
        tmp_path,
        [(100.0, 100.1, 99.9, 100.0)] * 63,
        rows,
    )
    assert {name: frame.height for name, frame in reports.items()} == {
        "fills": 200,
        "orders": 200,
        "positions": 100,
        "state_ledger": 400,
    }
    output = tmp_path / "report-out"
    assert {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(output.glob("*.parquet"))
    } == {
        "fills.parquet": "91b8cc1b084334f9a4f14f36511a11033c07db72f2a50c98a359ce6eab9341d1",
        "orders.parquet": "bb65debc498d44eaf98e653694e89efb08295e159f48a396a1a341c98f4ba85e",
        "positions.parquet": "80cb17863a12f587d0e81b52b1ef460b87c0790b0381393012b48b164f55a0d8",
        "state_ledger.parquet": "9accc3604e61c781b19cf7acdb5bd2d80f36fafe64aa23faedbdcca56fdd0237",
    }


def test_engine_freezes_the_shared_account_for_independent_research_arms(
    monkeypatch,
    tmp_path,
):
    """Shared-account PnL is not an emitted estimand and must not be recalculated per fill."""
    captured = {}
    captured_config = {}

    class VenueConfigured(Exception):
        pass

    class ProbeEngine:
        def __init__(self, *, config):
            captured_config["value"] = config

        def add_venue(self, **kwargs):
            captured.update(kwargs)
            raise VenueConfigured

    monkeypatch.setattr(
        "nautilus_trader.backtest.engine.BacktestEngine",
        ProbeEngine,
    )
    unit = WorkUnit(
        unit_id="FROZEN-ACCOUNT-PROBE",
        instrument=SPEC,
        bars_path=_bars_parquet(tmp_path, [(100.0, 100.1, 99.9, 100.0)]),
        schedule_path=_schedule(
            tmp_path,
            [
                _row(
                    state="NO_EVENT",
                    entry_order_type="NONE",
                    stop_price=None,
                )
            ],
        ),
        output_dir=str(tmp_path / "unused-output"),
        base_trade_size="100",
    )
    with pytest.raises(VenueConfigured):
        run_work_unit(unit)
    assert captured.get("frozen_account") is True
    assert captured_config["value"].run_analysis is False


def test_portfolio_statistics_stay_disabled_during_a_run(tmp_path):
    # The analyzer's per-trade pandas concat is quadratic and nothing we emit reads it. If a
    # future Nautilus version accumulates anyway, the run must fail rather than crawl.
    from xen.adaptive_management.engine import (
        _assert_portfolio_statistics_disabled,
        _disable_portfolio_statistics,
    )

    _disable_portfolio_statistics()
    from nautilus_trader.analysis.analyzer import PortfolioAnalyzer

    analyzer = PortfolioAnalyzer()
    from nautilus_trader.model.identifiers import PositionId
    from nautilus_trader.model.objects import Money
    from nautilus_trader.model.currencies import USD

    analyzer.add_trade(PositionId("P-1"), Money(10, USD), 1)
    analyzer.record_trade(PositionId("P-2"), Money(20, USD), 2)
    analyzer.add_return(datetime(2023, 1, 1, tzinfo=UTC), 0.01)
    assert analyzer.realized_pnls() is None
    assert not len(analyzer._position_returns)

    _assert_portfolio_statistics_disabled(
        SimpleNamespace(portfolio=SimpleNamespace(analyzer=analyzer))
    )


def test_actionable_time_without_a_traded_minute_acts_on_the_next_bar(tmp_path):
    # Real H1 labels can fall on a minute the venue never traded (session close, weekend).
    # The row must act on the first minute after it, and must not be dropped.
    times = [START, START + timedelta(minutes=5), START + timedelta(minutes=6)]
    ohlc = [(99.5, 99.6, 99.4, 99.5), (99.5, 101.0, 99.0, 100.5), (100.5, 102.0, 100.4, 101.9)]
    frame = pl.DataFrame(
        {
            "ts": times,
            "open": [r[0] for r in ohlc],
            "high": [r[1] for r in ohlc],
            "low": [r[2] for r in ohlc],
            "close": [r[3] for r in ohlc],
            "volume": [1000.0] * len(ohlc),
        }
    )
    bars_path = tmp_path / "gap_bars.parquet"
    frame.write_parquet(bars_path)
    rows = [_row(decision_ts=START + timedelta(minutes=2), stop_price=101.5, hold_bars=None,
                 target_distance_bps=200.0)]
    unit = WorkUnit(
        unit_id="GAP",
        instrument=SPEC,
        bars_path=str(bars_path),
        schedule_path=_schedule(tmp_path, rows),
        output_dir=str(tmp_path / "gap-out"),
        base_trade_size="100",
    )
    ledger = run_work_unit_subprocess(unit, timeout=300)["state_ledger"]
    assert ledger.height >= 1
    assert set(ledger["episode_id"]) == {"E1"}
    assert "FILLED" in set(ledger["state"])


def test_schedule_after_the_last_traded_minute_is_censored_inside_declared_fence(
    tmp_path,
):
    bars_path = _bars_parquet(tmp_path, [(99.5, 99.6, 99.4, 99.5)])
    schedule_path = _schedule(
        tmp_path,
        [
            _row(
                actionable_ts=START + timedelta(minutes=10),
                state="NO_EVENT",
                entry_order_type="NONE",
                stop_price=None,
            )
        ],
    )
    reports = run_work_unit_subprocess(
        WorkUnit(
            unit_id="FENCE-CENSOR",
            instrument=SPEC,
            bars_path=bars_path,
            schedule_path=schedule_path,
            output_dir=str(tmp_path / "fence-censor-out"),
            base_trade_size="100",
            fence_start_ns=int(START.timestamp() * 1e9),
            fence_end_ns=int((START + timedelta(hours=1)).timestamp() * 1e9),
        ),
        timeout=300,
    )
    assert reports["state_ledger"]["state"].to_list() == ["CENSORED"]


def test_thin_bar_volume_does_not_slice_one_entry_into_several_episodes(tmp_path):
    # Bar volume is a tick count, not tradable size. Raw, the venue caps a fill by it and one
    # entry order fills in slices, which used to re-arm the hold timer and abort the run.
    from xen.adaptive_management.engine import FILL_CAPACITY_MULTIPLE

    assert FILL_CAPACITY_MULTIPLE >= 1
    ohlc = [
        (99.5, 99.6, 99.4, 99.5),
        (99.5, 101.0, 99.0, 100.5),
    ] + [(100.5, 100.6, 100.4, 100.5)] * 130
    frame = pl.DataFrame(
        {
            "ts": [START + timedelta(minutes=i) for i in range(len(ohlc))],
            "open": [r[0] for r in ohlc],
            "high": [r[1] for r in ohlc],
            "low": [r[2] for r in ohlc],
            "close": [r[3] for r in ohlc],
            "volume": [0.01] * len(ohlc),  # thinner than one traded unit
        }
    )
    bars_path = tmp_path / "thin_bars.parquet"
    frame.write_parquet(bars_path)
    unit = WorkUnit(
        unit_id="THIN",
        instrument=SPEC,
        bars_path=str(bars_path),
        schedule_path=_schedule(tmp_path, [_row(hold_bars=1)]),
        output_dir=str(tmp_path / "thin-out"),
        base_trade_size="100",
    )
    reports = run_work_unit_subprocess(unit, timeout=300)
    ledger = reports["state_ledger"]
    assert ledger.filter(pl.col("state") == "FILLED").height == 1
    assert ledger.filter(pl.col("state") == "CLOSED").height == 1
    assert reports["positions"].height == 1


def test_nan_distance_in_a_schedule_is_rejected_before_the_run(tmp_path):
    path = _schedule(tmp_path, [_row(target_distance_bps=float("nan"))])
    with pytest.raises(ValueError, match="NaN"):
        AdaptiveManagementStrategy(
            AdaptiveManagementConfig(
                instrument_id=InstrumentId.from_str("XRPUSDT-LINEAR.BYBIT"),
                bar_type="XRPUSDT-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL",
                schedule_path=path,
                base_trade_size=100,
                fence_start_ns=int(START.timestamp() * 1e9),
                fence_end_ns=int((START + timedelta(hours=1)).timestamp() * 1e9),
            )
        )


def test_two_sided_origins_on_one_bar_are_scheduled_and_resolved_by_the_slot_rule(tmp_path):
    # A real H1 bar can qualify on both the long and the short shape, so one arm can carry two
    # distinct origins with the same actionable timestamp. That is legal input; the arm's single
    # slot resolves it. The same arm acting twice on one origin stays rejected.
    ohlc = [
        (99.5, 99.6, 99.4, 99.5),
        (99.5, 101.0, 99.0, 100.5),
    ] + [(100.5, 100.6, 100.4, 100.5)] * 5
    rows = [
        _row(episode_id="E1", origin_id="O_LONG", side=1, stop_price=100.0, hold_bars=4),
        _row(episode_id="E2", origin_id="O_SHORT", side=-1, stop_price=99.0, hold_bars=4),
    ]
    ledger, _, _ = _run(tmp_path, ohlc, rows)
    assert set(ledger["episode_id"]) == {"E1", "E2"}
    assert "BLOCKED_ACTIVE" in set(ledger.filter(pl.col("episode_id") == "E2")["state"])

    path = _schedule(
        tmp_path,
        [
            _row(episode_id="E1", origin_id="O_SAME"),
            _row(episode_id="E2", origin_id="O_SAME", decision_ts=START + timedelta(minutes=2)),
        ],
    )
    with pytest.raises(ValueError, match="overlapping schedule rows"):
        AdaptiveManagementStrategy(
            AdaptiveManagementConfig(
                instrument_id=InstrumentId.from_str("XRPUSDT-LINEAR.BYBIT"),
                bar_type="XRPUSDT-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL",
                schedule_path=path,
                base_trade_size=100,
                fence_start_ns=int(START.timestamp() * 1e9),
                fence_end_ns=int((START + timedelta(hours=1)).timestamp() * 1e9),
            )
        )


def test_holding_cap_closes_the_position(tmp_path):
    ohlc = [
        (99.5, 99.6, 99.4, 99.5),
        (99.5, 101.0, 99.0, 100.5),
    ] + [(100.5, 100.6, 100.4, 100.5)] * 130
    ledger, _, positions = _run(tmp_path, ohlc, [_row(hold_bars=1)])
    closed = ledger.filter(pl.col("state") == "CLOSED")
    assert closed.height == 1
    assert closed.row(0, named=True)["exit_reason"] == "HOLD"
    assert len(positions) == 1


def test_touch_and_close_variants_do_not_block_each_other(tmp_path):
    ohlc = [
        (99.5, 99.6, 99.4, 99.5),
        (99.5, 101.0, 99.0, 100.5),
    ] + [(100.5, 100.6, 100.4, 100.5)] * 5
    rows = [
        _row(
            episode_id="E_TOUCH", entry_variant="E_TOUCH", arm_id="ARM",
            experiment_id="SPDR-022", hold_bars=4,
        ),
        _row(
            episode_id="E_CLOSE", entry_variant="E_CLOSE", arm_id="ARM",
            experiment_id="SPDR-022", hold_bars=4,
        ),
    ]
    ledger, fills, positions = _run(tmp_path, ohlc, rows)
    assert ledger.filter(pl.col("state") == "FILLED").height == 2
    assert "BLOCKED_ACTIVE" not in set(ledger["state"])
    assert len(positions) == 2


def test_engine_rate_limit_keeps_all_declared_parallel_arms(tmp_path):
    rows = [
        _row(
            experiment_id="SPDR-022",
            entry_variant="E_TOUCH",
            entry_order_type="MARKET",
            stop_price=None,
            expiry_bars=None,
            arm_id=f"ARM-{index}",
            policy_id=f"POLICY-{index}",
            episode_id=f"E-{index}",
            origin_id=f"O-{index}",
        )
        for index in range(150)
    ]
    reports = _run_reports(
        tmp_path,
        [(100.0, 100.1, 99.9, 100.0)] * 2,
        rows,
    )
    ledger = reports["state_ledger"]
    assert ledger.filter(pl.col("state") == "FILLED").height == 150
    assert not set(ledger["state"]) & {"DENIED", "REJECTED"}


def test_two_policies_on_one_episode_keep_two_terminal_rows_and_positions(tmp_path):
    ohlc = [
        (99.5, 99.6, 99.4, 99.5),
        (99.5, 101.0, 99.0, 100.5),
        (100.5, 100.6, 100.4, 100.5),
    ]
    shared = {
        "episode_id": "SHARED_EPISODE",
        "origin_id": "SHARED_ORIGIN",
        "position_id": "AM-SHARED-EPISODE-POSITION",
    }
    rows = [
        _row(**shared, arm_id="ARM-P1", policy_id="POLICY-1"),
        _row(**shared, arm_id="ARM-P2", policy_id="POLICY-2"),
    ]
    ledger, _, positions = _run(tmp_path, ohlc, rows)
    terminal = ledger.filter(pl.col("state") == "FILLED").sort("policy_id")
    assert terminal.select("episode_id", "policy_id").rows() == [
        ("SHARED_EPISODE", "POLICY-1"),
        ("SHARED_EPISODE", "POLICY-2"),
    ]
    assert positions.height == 2
    assert positions["position_id"].n_unique() == 2


@pytest.mark.parametrize("entry_variant", ["E_TOUCH", "E_CLOSE"])
def test_generated_breach_episode_enters_with_native_market_order(
    tmp_path, entry_variant
):
    rows = 14
    h1 = pl.DataFrame(
        {
            "symbol": ["XRPUSDT-LINEAR"] * rows,
            "ts": [START + timedelta(hours=i) for i in range(rows)],
            "open": [100.0, 101.0, *([101.0] * (rows - 2))],
            "high": [101.6, *([101.2] * (rows - 1))],
            "low": [99.8] * rows,
            "close": [
                101.6 if entry_variant == "E_CLOSE" else 100.0,
                *([101.0] * (rows - 1)),
            ],
        }
    )
    features = h1.select("symbol", "ts").with_columns(
        pl.lit(100.0).alias("range_scale_bps")
    )
    spec = next(
        arm for arm in build_native_lattice("SPDR-022")
        if not arm.is_adaptive and arm.entry_variant == entry_variant
    )
    episode = materialise_native_arm(
        breach_origins(h1, features),
        features,
        {"range": {"XRPUSDT-LINEAR": 100.0}},
        spec,
    ).row(0, named=True)
    assert episode["z"] == 1.5
    assert episode["horizon"] == 12
    assert episode["state"] == "ORDER_CREATED"
    assert episode["entry_order_type"] == "MARKET"
    assert episode["actionable_ts"] == episode["entry_ts"] == h1["ts"][1]

    schedule_row = _row(
        arm_id=f"ARM-{entry_variant}",
        experiment_id="SPDR-022",
        native_arm_id=episode["native_arm_id"],
        origin_id=episode["origin_id"],
        episode_id=episode["episode_id"],
        decision_ts=episode["decision_ts"],
        actionable_ts=episode["actionable_ts"],
        entry_variant=episode["entry_variant"],
        side=episode["side"],
        state=episode["state"],
        entry_order_type=episode["entry_order_type"],
        stop_price=None,
        expiry_bars=None,
    )
    minute_ohlc = [(100.0, 100.1, 99.9, 100.0)] * 60 + [
        (101.0, 101.1, 100.9, 101.0),
        (101.0, 101.1, 100.9, 101.0),
    ]
    reports = _run_reports(tmp_path, minute_ohlc, [schedule_row])
    assert reports["state_ledger"].filter(pl.col("state") == "FILLED").height == 1
    assert set(reports["orders"]["type"]) == {"MARKET"}
    assert float(reports["positions"]["avg_px_open"][0]) == pytest.approx(101.0)


def test_duplicate_and_out_of_fence_schedules_are_rejected(tmp_path):
    path = _schedule(tmp_path, [_row(), _row()])
    with pytest.raises(ValueError, match="duplicate"):
        AdaptiveManagementStrategy(
            AdaptiveManagementConfig(
                instrument_id=InstrumentId.from_str("XRPUSDT-LINEAR.BYBIT"),
                bar_type="XRPUSDT-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL",
                schedule_path=path,
                base_trade_size=100,
                fence_start_ns=int(START.timestamp() * 1e9),
                fence_end_ns=int((START + timedelta(hours=1)).timestamp() * 1e9),
            )
        )
    path = _schedule(tmp_path, [_row(decision_ts=START - timedelta(minutes=1))])
    with pytest.raises(ValueError, match="outside fence"):
        AdaptiveManagementStrategy(
            AdaptiveManagementConfig(
                instrument_id=InstrumentId.from_str("XRPUSDT-LINEAR.BYBIT"),
                bar_type="XRPUSDT-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL",
                schedule_path=path,
                base_trade_size=100,
                fence_start_ns=int(START.timestamp() * 1e9),
                fence_end_ns=int((START + timedelta(hours=1)).timestamp() * 1e9),
            )
        )


def test_each_episode_has_one_terminal_entry_outcome_and_at_most_one_close(tmp_path):
    ohlc = [
        (99.5, 99.6, 99.4, 99.5),
        (99.5, 101.0, 99.0, 100.5),
        (100.5, 102.2, 97.8, 100.0),
    ]
    ledger, _, _ = _run(
        tmp_path, ohlc,
        [_row(target_distance_bps=200.0, stop_distance_bps=200.0)],
    )
    terminal = ledger.filter(
        pl.col("state").is_in(["NO_EVENT", "BLOCKED_ACTIVE", "EXPIRED", "FILLED", "REJECTED", "DENIED"])
    )
    assert terminal.filter(pl.col("episode_id") == "E1").height == 1
    assert ledger.filter((pl.col("episode_id") == "E1") & (pl.col("state") == "CLOSED")).height <= 1


def test_hold_timer_fires_at_wall_clock_deadline_across_missing_minutes(tmp_path):
    # The market has no bars for 70 minutes after entry. The timer becomes due at the exact
    # one-hour deadline; the market exit fills on the first available bar after the gap.
    times = [START, START + timedelta(minutes=1), START + timedelta(minutes=71)]
    frame = pl.DataFrame(
        {
            "ts": times,
            "open": [99.5, 99.5, 100.5],
            "high": [99.6, 101.0, 100.6],
            "low": [99.4, 99.0, 100.4],
            "close": [99.5, 100.5, 100.5],
            "volume": [1000.0] * 3,
        }
    )
    bars_path = tmp_path / "gap-bars.parquet"
    frame.write_parquet(bars_path)
    unit = WorkUnit(
        unit_id="GAP",
        instrument=SPEC,
        bars_path=str(bars_path),
        schedule_path=_schedule(tmp_path, [_row(hold_bars=1)]),
        output_dir=str(tmp_path / "gap-out"),
        base_trade_size="100",
    )
    reports = run_work_unit_subprocess(unit, timeout=300)
    due = reports["state_ledger"].filter(pl.col("state") == "HOLD_DUE")
    assert due.height == 1
    assert due["ts_ns"][0] == int((START + timedelta(minutes=61)).timestamp() * 1e9)


def test_expiry_has_no_position_pnl_row(tmp_path):
    ohlc = [(99.5, 99.6, 99.4, 99.5)] * 130
    _, _, positions = _run(tmp_path, ohlc, [_row(stop_price=105.0, expiry_bars=1)])
    assert positions.is_empty()


def test_trail_activates_then_closes_reduce_only(tmp_path):
    ohlc = [
        (99.5, 99.6, 99.4, 99.5),
        (99.5, 100.2, 99.0, 100.0),
        (100.0, 101.3, 100.0, 101.1),
        (101.1, 101.2, 99.8, 100.0),
    ]
    reports = _run_reports(
        tmp_path,
        ohlc,
        [_row(trail_distance_bps=100.0, trail_activation_bps=100.0)],
    )
    closed = reports["state_ledger"].filter(pl.col("state") == "CLOSED")
    assert closed.height == 1
    assert closed["exit_reason"][0] == "TRAIL"
    assert reports["orders"].filter(pl.col("is_reduce_only") == "True").height >= 1


def test_every_order_report_carries_full_identity_tags(tmp_path):
    ohlc = [
        (99.5, 99.6, 99.4, 99.5),
        (99.5, 101.0, 99.0, 100.5),
        (100.5, 102.2, 100.0, 102.0),
    ]
    reports = _run_reports(tmp_path, ohlc, [_row(target_distance_bps=200.0)])
    tags = " ".join(reports["orders"]["tags"].to_list())
    for key in (
        "native_arm_id=", "policy_id=", "device=", "entry_variant=",
        "exit_reason=", "episode_id=", "origin_id=",
    ):
        assert key in tags


def test_unconsumed_schedule_rows_fail_at_stop(tmp_path):
    path = _schedule(tmp_path, [_row(decision_ts=START + timedelta(minutes=10))])
    strategy = AdaptiveManagementStrategy(
        AdaptiveManagementConfig(
            instrument_id=InstrumentId.from_str("XRPUSDT-LINEAR.BYBIT"),
            bar_type="XRPUSDT-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL",
            schedule_path=path,
            base_trade_size=100,
            fence_start_ns=int(START.timestamp() * 1e9),
            fence_end_ns=int((START + timedelta(hours=1)).timestamp() * 1e9),
        )
    )
    with pytest.raises(RuntimeError, match="unconsumed"):
        strategy.on_stop()


def test_fenced_synthetic_catalog_timestamps_feed_engine_schedule(tmp_path):
    instrument = _make_instrument(SPEC)
    bar_type = BarType.from_str(f"{instrument.id}-1-MINUTE-LAST-EXTERNAL")
    bars = [
        Bar(
            bar_type=bar_type,
            open=instrument.make_price(row[0]),
            high=instrument.make_price(row[1]),
            low=instrument.make_price(row[2]),
            close=instrument.make_price(row[3]),
            volume=instrument.make_qty(1000),
            ts_event=int((START + timedelta(minutes=i)).timestamp() * 1e9),
            ts_init=int((START + timedelta(minutes=i)).timestamp() * 1e9),
        )
        for i, row in enumerate(
            [(99.5, 99.6, 99.4, 99.5), (99.5, 101.0, 99.0, 100.5)]
        )
    ]
    catalog = ParquetDataCatalog(str(tmp_path / "catalog"))
    catalog.write_data(bars)
    manifest = FenceManifest(
        analysis_start_utc=START,
        train_end_utc=START + timedelta(hours=1),
        holdout_start_utc=START + timedelta(hours=2),
        data_end_utc=START + timedelta(hours=3),
        path=Path(tmp_path / "manifest.json"),
        sha256="synthetic",
        raw={},
    )
    loaded = fenced_bar_query(
        catalog,
        [str(bar_type)],
        START,
        START + timedelta(minutes=1),
        band="TRAIN",
        manifest=manifest,
    )
    assert [bar.ts_event for bar in loaded] == [bar.ts_event for bar in bars]
    replay = [
        (float(bar.open), float(bar.high), float(bar.low), float(bar.close))
        for bar in loaded
    ]
    ledger, _, _ = _run(tmp_path, replay, [_row(hold_bars=4)])
    assert ledger.filter(pl.col("state") == "FILLED").height == 1


@pytest.mark.parametrize(
    ("handler", "expected"), [("on_order_rejected", "REJECTED"), ("on_order_denied", "DENIED")]
)
def test_failed_entry_order_has_one_terminal_outcome_and_releases_slot(
    tmp_path, handler, expected
):
    path = _schedule(tmp_path, [_row()])
    strategy = AdaptiveManagementStrategy(
        AdaptiveManagementConfig(
            instrument_id=InstrumentId.from_str("XRPUSDT-LINEAR.BYBIT"),
            bar_type="XRPUSDT-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL",
            schedule_path=path,
            base_trade_size=100,
            fence_start_ns=int(START.timestamp() * 1e9),
            fence_end_ns=int((START + timedelta(hours=1)).timestamp() * 1e9),
        )
    )
    row = pl.read_parquet(path).row(0, named=True)
    strategy._busy[("ARM", "BREAKOUT")] = "E1"
    strategy._by_client_order["C1"] = row
    strategy._entry_orders.add("C1")
    event = SimpleNamespace(client_order_id="C1", ts_event=123)
    getattr(strategy, handler)(event)
    getattr(strategy, handler)(event)
    assert [item["state"] for item in strategy.state_ledger] == [expected]
    assert ("ARM", "BREAKOUT") not in strategy._busy
