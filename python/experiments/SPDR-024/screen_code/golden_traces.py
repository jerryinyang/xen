#!/usr/bin/env python3
"""SPDR-024 golden traces - design section 14, hand-derived, not generated from this code.

Three traces, each with its expected value written down in the design before any code existed:

1. **Capital normalisation makes sizing visible.** Per-notional bps delta must be exactly `0.0`
   while the PRIMARY capital-normalised delta is non-zero. If both are zero, E6 is not
   implemented and the sizing question is dead again.
2. **Rejected-origin counterfactual.** A rejected origin must emit `+25 bps`, not `0.0`. A
   `0.0` here means E2 is not implemented and every selection read is void.
3. **Safety ceiling and censoring.** A position reaching the ceiling closes with
   `exit_reason = SAFETY_CEILING` and its bind flag set; a position still open at the TRAIN
   fence is CENSORED and excluded from paired reads, never silently closed at the fence price.

Traces 1 and 2 run the real emission builder over a synthetic run directory. Trace 3 runs the
real Nautilus engine, because the behaviour it checks is the engine's, not the analyser's.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys

PYTHON_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PYTHON_ROOT / "src"))

import polars as pl  # noqa: E402

from xen.adaptive_management.contracts import (  # noqa: E402
    SAFETY_CEILING_BARS,
    UNCAPPED_ARM_ID,
)
from xen.adaptive_management.engine import (  # noqa: E402
    InstrumentSpec,
    WorkUnit,
    run_work_unit_subprocess,
)
from xen.adaptive_management.spdr024_emission import build_episode_table  # noqa: E402
from xen.adaptive_management.strategy import (  # noqa: E402
    OPTIONAL_SCHEDULE_COLUMNS,
    SCHEDULE_COLUMNS,
)

NS_PER_HOUR = 3_600_000_000_000
TOLERANCE = 1e-9

SPREAD_COST_DISCLOSURE = {
    "spread_cost_status": "UNAVAILABLE_NOT_CHARGED",
    "spread_rt_bps": None,
    "cost_scope": "PARTIAL_FEES_FUNDING_ONLY",
}


def _utc(text: str) -> datetime:
    return datetime.fromisoformat(text).replace(tzinfo=timezone.utc)


def _schedule_row(**overrides) -> dict:
    row = {
        "experiment_id": "SPDR-024",
        "universe": "synthetic",
        "symbol": "SYN",
        "entry_variant": "BREAKOUT",
        "arm_id": "",
        "arm_class": "MANAGEMENT",
        "policy_id": "NONE",
        "native_arm_id": None,
        "component": None,
        "device": "NONE",
        "setting": None,
        "comparator_id": None,
        "origin_id": "",
        "episode_id": "",
        "decision_ts": None,
        "actionable_ts": None,
        "state": "ORDER_CREATED",
        "entry_order_type": "STOP",
        "side": 1,
        "stop_price": 100.0,
        "expiry_bars": 2,
        "hold_bars": 1,
        "hold_cap_bars": None,
        "hold_cap_binds": False,
        "hold_exit_reason": None,
        "target_distance_bps": None,
        "stop_distance_bps": None,
        "trail_distance_bps": None,
        "trail_activation_bps": None,
        "risk_size": 1.0,
        "exit_reason": None,
        "regime_state": "HIGH",
        "regime_episode_id": "SYN-R000000",
    }
    row.update(overrides)
    return row


def _ledger_row(**overrides) -> dict:
    row = {
        "episode_id": "",
        "origin_id": "",
        "arm_id": "",
        "arm_class": "MANAGEMENT",
        "experiment_id": "SPDR-024",
        "native_arm_id": None,
        "policy_id": "NONE",
        "device": "NONE",
        "entry_variant": "BREAKOUT",
        "state": "FILLED",
        "ts_ns": 0,
        "price": None,
        "exit_reason": None,
    }
    row.update(overrides)
    return row


def _write_synthetic_run(root: Path) -> Path:
    """A two-origin run directory carrying exactly the design's two hand-derived cases."""
    root.mkdir(parents=True, exist_ok=True)
    t1 = _utc("2023-01-01T02:00:00")
    t2 = _utc("2023-01-02T02:00:00")
    t1_ns = int(t1.timestamp() * 1e9)
    t2_ns = int(t2.timestamp() * 1e9)

    policy_rows = [
        # Trace 1: same price path, two position sizes.
        _schedule_row(
            arm_id="FIXED_SIZE_UNIT",
            policy_id="FIXED_SIZE_UNIT",
            device="SIZE",
            setting="UNIT",
            comparator_id="FIXED_SIZE_UNIT",
            arm_class="FIXED_MANAGEMENT",
            origin_id="O1",
            episode_id="E1-FIXED",
            decision_ts=t1,
            actionable_ts=t1,
            risk_size=1.0,
        ),
        _schedule_row(
            arm_id="ADP_TAIL_RISK_SIZE_STATE_HALVE_HIGH",
            policy_id="ADP_TAIL_RISK_SIZE_STATE_HALVE_HIGH",
            device="SIZE",
            setting="STATE_HALVE_HIGH",
            comparator_id="FIXED_SIZE_UNIT",
            component="TAIL_RISK",
            origin_id="O1",
            episode_id="E1-HALVE",
            decision_ts=t1,
            actionable_ts=t1,
            risk_size=0.5,
        ),
    ]
    native_rows = [
        # Trace 2: the fixed arm admits and manages; the component arm rejects.
        _schedule_row(
            arm_id="FIXED_NATIVE_BREAKOUT",
            arm_class="FIXED_NATIVE",
            native_arm_id="FIXED_NATIVE_BREAKOUT",
            origin_id="O2",
            episode_id="E2-FIXED",
            decision_ts=t2,
            actionable_ts=t2,
        ),
        _schedule_row(
            arm_id="NAT_BREAKOUT_TAIL_RISK_BREAKOUT_THRESHOLD_DIRECT",
            arm_class="NATIVE",
            native_arm_id="NAT_BREAKOUT_TAIL_RISK_BREAKOUT_THRESHOLD_DIRECT",
            component="TAIL_RISK",
            origin_id="O2",
            episode_id="E2-REJECT",
            decision_ts=t2,
            actionable_ts=t2,
            state="NO_EVENT",
            entry_order_type="NONE",
            stop_price=None,
        ),
    ]
    ledger_rows = [
        _ledger_row(
            episode_id="E1-FIXED", origin_id="O1", arm_id="FIXED_SIZE_UNIT",
            policy_id="FIXED_SIZE_UNIT", device="SIZE", state="FILLED",
            ts_ns=t1_ns, price=100.0,
        ),
        _ledger_row(
            episode_id="E1-FIXED", origin_id="O1", arm_id="FIXED_SIZE_UNIT",
            policy_id="FIXED_SIZE_UNIT", device="SIZE", state="CLOSED",
            ts_ns=t1_ns + NS_PER_HOUR, price=101.0, exit_reason="HOLD",
        ),
        _ledger_row(
            episode_id="E1-HALVE", origin_id="O1",
            arm_id="ADP_TAIL_RISK_SIZE_STATE_HALVE_HIGH",
            policy_id="ADP_TAIL_RISK_SIZE_STATE_HALVE_HIGH", device="SIZE",
            state="FILLED", ts_ns=t1_ns, price=100.0,
        ),
        _ledger_row(
            episode_id="E1-HALVE", origin_id="O1",
            arm_id="ADP_TAIL_RISK_SIZE_STATE_HALVE_HIGH",
            policy_id="ADP_TAIL_RISK_SIZE_STATE_HALVE_HIGH", device="SIZE",
            state="CLOSED", ts_ns=t1_ns + NS_PER_HOUR, price=101.0, exit_reason="HOLD",
        ),
        _ledger_row(
            episode_id="E2-FIXED", origin_id="O2", arm_id="FIXED_NATIVE_BREAKOUT",
            arm_class="FIXED_NATIVE", native_arm_id="FIXED_NATIVE_BREAKOUT",
            state="FILLED", ts_ns=t2_ns, price=100.0,
        ),
        _ledger_row(
            episode_id="E2-FIXED", origin_id="O2", arm_id="FIXED_NATIVE_BREAKOUT",
            arm_class="FIXED_NATIVE", native_arm_id="FIXED_NATIVE_BREAKOUT",
            state="CLOSED", ts_ns=t2_ns + NS_PER_HOUR, price=100.25, exit_reason="HOLD",
        ),
    ]
    pl.DataFrame(policy_rows).write_parquet(root / "policy_schedule.parquet")
    pl.DataFrame(native_rows).write_parquet(root / "native_parameter_schedule.parquet")
    pl.DataFrame(ledger_rows).write_parquet(root / "episode_results.parquet")
    (root / "config.json").write_text(
        json.dumps(
            {
                "experiment_id": "SPDR-024",
                "universe": "synthetic",
                "band": "TRAIN",
                "signal_domain": "H1",
                "spread_cost_disclosure": SPREAD_COST_DISCLOSURE,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return root


def trace_1_and_2(workspace: Path) -> list[dict]:
    episodes = build_episode_table(_write_synthetic_run(workspace / "synthetic_run"))

    def value(arm: str, column: str):
        rows = episodes.filter(pl.col("arm_id") == arm)
        return None if rows.is_empty() else rows[column][0]

    fixed_bps = value("FIXED_SIZE_UNIT", "outcome_bps")
    halve_bps = value("ADP_TAIL_RISK_SIZE_STATE_HALVE_HIGH", "outcome_bps")
    fixed_cap = value("FIXED_SIZE_UNIT", "capital_normalised_return_bps")
    halve_cap = value("ADP_TAIL_RISK_SIZE_STATE_HALVE_HIGH", "capital_normalised_return_bps")
    counterfactual = value(
        "NAT_BREAKOUT_TAIL_RISK_BREAKOUT_THRESHOLD_DIRECT", "counterfactual_outcome_bps"
    )
    bps_delta = None if None in (fixed_bps, halve_bps) else halve_bps - fixed_bps
    capital_delta = None if None in (fixed_cap, halve_cap) else halve_cap - fixed_cap

    return [
        {
            "trace": "1_capital_normalisation_makes_sizing_visible",
            "design_reference": "design.md section 14 item 1",
            "expected": {
                "outcome_bps_delta": 0.0,
                "capital_normalised_delta": -50.0,
                "per_notional_both_sides_bps": 100.0,
            },
            "observed": {
                "outcome_bps_delta": bps_delta,
                "capital_normalised_delta": capital_delta,
                "fixed_outcome_bps": fixed_bps,
                "halved_outcome_bps": halve_bps,
                "fixed_capital_bps": fixed_cap,
                "halved_capital_bps": halve_cap,
            },
            "pass": bool(
                fixed_bps is not None
                and abs(fixed_bps - 100.0) < TOLERANCE
                and bps_delta is not None
                and bps_delta == 0.0
                and capital_delta is not None
                and abs(capital_delta - (-50.0)) < TOLERANCE
            ),
            "meaning_if_failed": "E6 is not implemented; the sizing question is unreadable",
        },
        {
            "trace": "2_rejected_origin_counterfactual",
            "design_reference": "design.md section 14 item 2",
            "expected": {"counterfactual_outcome_bps": 25.0, "must_not_be": 0.0},
            "observed": {
                "counterfactual_outcome_bps": counterfactual,
                "counterfactual_source": value(
                    "NAT_BREAKOUT_TAIL_RISK_BREAKOUT_THRESHOLD_DIRECT",
                    "counterfactual_source",
                ),
            },
            "pass": bool(
                counterfactual is not None and abs(counterfactual - 25.0) < TOLERANCE
            ),
            "meaning_if_failed": "E2 is not implemented; every selection read is void",
        },
    ]


def _minute_bars(start: datetime, minutes: int, symbol: str = "SYN") -> pl.DataFrame:
    times = [start + timedelta(minutes=index) for index in range(minutes)]
    return pl.DataFrame(
        {
            "symbol": [symbol] * minutes,
            "ts": times,
            "open": [100.0] * minutes,
            "high": [100.5] * minutes,
            "low": [99.5] * minutes,
            "close": [100.0] * minutes,
            "volume": [1000.0] * minutes,
        }
    ).with_columns(pl.col("ts").cast(pl.Datetime("ns", "UTC")))


def trace_3(workspace: Path) -> list[dict]:
    """Run the real engine: one ceiling exit, one position still open at the fence."""
    root = workspace / "trace3"
    root.mkdir(parents=True, exist_ok=True)
    start = _utc("2023-03-01T00:00:00")
    # 121 domain bars of one-minute data, so a position opened at bar 0 reaches bar 120.
    minutes = (SAFETY_CEILING_BARS + 2) * 60
    bars = _minute_bars(start, minutes)
    bars_path = root / "bars.parquet"
    bars.write_parquet(bars_path)
    fence_start_ns = int(start.timestamp() * 1e9)
    fence_end_ns = int(bars["ts"].max().timestamp() * 1e9)

    ceiling_entry = start
    censored_entry = start + timedelta(hours=SAFETY_CEILING_BARS - 1)
    rows = [
        _schedule_row(
            arm_id=UNCAPPED_ARM_ID,
            policy_id=UNCAPPED_ARM_ID,
            arm_class="FIXED_MANAGEMENT",
            origin_id="OC",
            episode_id="EC",
            decision_ts=ceiling_entry,
            actionable_ts=ceiling_entry,
            hold_bars=SAFETY_CEILING_BARS,
            hold_exit_reason="SAFETY_CEILING",
            entry_order_type="MARKET",
            stop_price=None,
            expiry_bars=None,
        ),
        _schedule_row(
            arm_id="CENSORED_PROBE",
            policy_id="CENSORED_PROBE",
            arm_class="FIXED_MANAGEMENT",
            origin_id="OZ",
            episode_id="EZ",
            decision_ts=censored_entry,
            actionable_ts=censored_entry,
            hold_bars=SAFETY_CEILING_BARS,
            hold_exit_reason="SAFETY_CEILING",
            entry_order_type="MARKET",
            stop_price=None,
            expiry_bars=None,
        ),
    ]
    columns = list(SCHEDULE_COLUMNS) + list(OPTIONAL_SCHEDULE_COLUMNS)
    schedule = pl.DataFrame(rows).select(columns)
    schedule_path = root / "schedule.parquet"
    schedule.write_parquet(schedule_path)

    unit = WorkUnit(
        unit_id="SPDR-024-golden-trace-3",
        instrument=InstrumentSpec(
            symbol="SYN",
            instrument_id="SYN.SIM",
            venue="SIM",
            price_precision=2,
            size_precision=0,
            price_increment="0.01",
            size_increment="1",
            quote_currency="USD",
            base_currency="USD",
            instrument_kind="currencypair",
        ),
        bars_path=str(bars_path),
        schedule_path=str(schedule_path),
        output_dir=str(root / "engine"),
        base_trade_size="1000",
        fence_start_ns=fence_start_ns,
        fence_end_ns=fence_end_ns,
        domain_ns=NS_PER_HOUR,
    )
    report = run_work_unit_subprocess(unit)
    ledger = report["state_ledger"]
    ceiling = ledger.filter(pl.col("episode_id") == "EC")
    censored = ledger.filter(pl.col("episode_id") == "EZ")
    ceiling_close = ceiling.filter(pl.col("state") == "CLOSED")
    ceiling_reason = (
        None if ceiling_close.is_empty() else ceiling_close["exit_reason"].to_list()[-1]
    )
    ceiling_bars = None
    if not ceiling_close.is_empty():
        filled = ceiling.filter(pl.col("state") == "FILLED")
        if not filled.is_empty():
            ceiling_bars = (
                int(ceiling_close["ts_ns"].to_list()[-1]) - int(filled["ts_ns"].to_list()[0])
            ) / NS_PER_HOUR
    censored_states = censored["state"].to_list()

    return [
        {
            "trace": "3_safety_ceiling_and_censoring",
            "design_reference": "design.md section 14 item 3",
            "expected": {
                "ceiling_exit_reason": "SAFETY_CEILING",
                "ceiling_hold_bars": float(SAFETY_CEILING_BARS),
                "fence_position_state": "OPEN_AT_FENCE_END (censored, never closed at fence)",
            },
            "observed": {
                "ceiling_exit_reason": ceiling_reason,
                "ceiling_hold_bars": ceiling_bars,
                "censored_states": censored_states,
                "censored_has_close": "CLOSED" in censored_states,
            },
            "pass": bool(
                ceiling_reason == "SAFETY_CEILING"
                and ceiling_bars is not None
                and abs(ceiling_bars - SAFETY_CEILING_BARS) < TOLERANCE
                and "CLOSED" not in censored_states
                and "OPEN_AT_FENCE_END" in censored_states
            ),
            "meaning_if_failed": (
                "the ceiling is acting as an ordinary hold, or a fenced position was "
                "silently closed at the fence price"
            ),
        }
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--workspace", type=Path, default=None)
    args = parser.parse_args(argv)
    workspace = args.workspace or args.out.parent / "_golden_workspace"
    traces = trace_1_and_2(workspace) + trace_3(workspace)
    payload = {
        "experiment_id": "SPDR-024",
        "source": "design.md section 14 - hand-derived, not generated from the implementation",
        "traces": traces,
        "n_traces": len(traces),
        "n_passed": sum(bool(item["pass"]) for item in traces),
        "blocking_pass": all(bool(item["pass"]) for item in traces),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    return 0 if payload["blocking_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
