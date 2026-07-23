"""SPDR-011 TRAIN-only Nautilus emission orchestrator.

DEVIATIONS: none.

No command-line entry point is intentionally supplied before fresh QA and explicit operator
execution authority. Import and call :func:`run_train_emission` only after both gates. The
module itself performs no catalog query, outcome read, directory creation, or execution.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import platform
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import polars as pl

import nautilus_trader
from nautilus_trader.backtest.node import BacktestNode
from nautilus_trader.config import (
    BacktestDataConfig,
    BacktestEngineConfig,
    BacktestRunConfig,
    BacktestVenueConfig,
    ImportableLatencyModelConfig,
    ImportableStrategyConfig,
    LoggingConfig,
)
from nautilus_trader.model.data import Bar, TradeTick
from nautilus_trader.model.enums import AggressorSide
from nautilus_trader.model.identifiers import TradeId
from nautilus_trader.persistence.catalog import ParquetDataCatalog

from xen.estimand_validation import validate_run
from xen.nautilus.catalog_fence import (
    assert_within_fence,
    fence_attestation_payload,
    fenced_bar_query,
    load_fence_manifest,
)
from xen.nautilus.emission import write_emission_v1
from xen.sigbar.data_types import SignedBar

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from bundle import write_bundle  # noqa: E402
from controls import (  # noqa: E402
    calibrate_future_destroy_sentinel,
    conversion_control_batteries,
    adjudicate_future_destroy,
    l3_date_block_ci,
    matched_timing_battery,
    random_top2_cluster_matches,
)
from runner_contract import (  # noqa: E402
    attach_open_to_open_outcomes,
    attach_partial_costs,
    attach_signed_flow,
    reconcile_event_fills,
)
from spdr011_strategy import build_target_schedule  # noqa: E402


ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT.parent
EXP = Path(__file__).resolve().parents[1]
CATALOG = REPO / "data/catalog"
SIGNED_CATALOG = REPO / "data/catalog_sigbar/train"
CENSUS = EXP / "results/census_event_keys.parquet"
CENSUS_JSON = EXP / "results/census.json"
CENSUS_DERIVATION = EXP / "design_derivations/census.py"
SIGNED_ATTESTATION = EXP / "results/signed_train_attestation.json"
RUN_ROOT = REPO / "data/nautilus_runs/SPDR-011"
BUNDLE_ROOT = RUN_ROOT / "artifact-bundle"
SCHEDULE_ROOT = RUN_ROOT / "schedules"
EXECUTION_CATALOG = RUN_ROOT / "execution_catalog"

CENSUS_SHA256 = "d1299a08c98461468447289622ac979a6450fc04171c1547ccf950af850c7dfd"
CENSUS_JSON_SHA256 = "94faab2ec9b752c8621ea6dac2f1df6988d97650cb17a5ba2d80b25f1db13681"
CENSUS_DERIVATION_SHA256 = (
    "9fae1731a3afe39a64abb7cbda58b870932b9ea52ae6c83a38ccb470ee802bdc"
)
SIGNED_ATTESTATION_SHA256 = (
    "bdfe839c4f6ae61b75a3ec2bca270cd9ba23a1bdff90bcbb8351970d9b180d29"
)
SIGNED_CATALOG_TREE_SHA256 = (
    "d4b7bbed7e0c039cc8c74a05e0f8747796c75016957d1e7c5f7c2feb20f7d2b9"
)
EXPECTED_EVENTS = 3_606
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT")
TRADE_SIZE = {
    "BTCUSDT": "0.01",
    "ETHUSDT": "0.1",
    "SOLUSDT": "1",
    "DOGEUSDT": "100",
    "XRPUSDT": "100",
}
CATALOG_VERSION = "INFR-011-A4-2026-07-16"
RUN1_END_UTC = datetime(2023, 3, 1, tzinfo=timezone.utc)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def catalog_tree_sha256(path: Path) -> str:
    """Hash relative paths plus file digests using the signed-ingest tree contract."""
    digest = hashlib.sha256()
    files = sorted(item for item in path.rglob("*") if item.is_file())
    for item in files:
        digest.update(item.relative_to(path).as_posix().encode())
        digest.update(bytes.fromhex(_sha256(item)))
    return digest.hexdigest()


def assert_signed_catalog_tree(
    path: Path,
    attested_sha256: str,
    frozen_sha256: str = SIGNED_CATALOG_TREE_SHA256,
) -> str:
    """Re-hash live signed bytes and require both attested and frozen identities."""
    actual = catalog_tree_sha256(path)
    if actual != attested_sha256 or actual != frozen_sha256:
        raise RuntimeError(
            "signed catalog tree hash mismatch: "
            f"actual={actual} attested={attested_sha256} frozen={frozen_sha256}"
        )
    return actual


def assert_causal_provenance(events: pl.DataFrame) -> None:
    """Require every conditioning source to be known no later than the trigger."""
    required = {"event_id", "trigger_ts", "state_known_ts", "range_known_ts"}
    missing = sorted(required - set(events.columns))
    if missing:
        raise ValueError(f"census provenance columns missing: {missing}")
    breaches = events.filter(
        (pl.col("state_known_ts") > pl.col("trigger_ts"))
        | (pl.col("range_known_ts") > pl.col("trigger_ts"))
    )
    if breaches.height:
        raise RuntimeError(f"causal provenance breach on {breaches.height} census events")


def assert_preexecution_inputs() -> tuple[pl.DataFrame, dict[str, Any]]:
    """Validate frozen census and signed TRAIN attestation without reading any outcome."""
    if (
        _sha256(CENSUS) != CENSUS_SHA256
        or _sha256(CENSUS_JSON) != CENSUS_JSON_SHA256
        or _sha256(CENSUS_DERIVATION) != CENSUS_DERIVATION_SHA256
    ):
        raise RuntimeError("frozen SPDR-011 census hash mismatch")
    events = pl.read_parquet(CENSUS)
    if events.height != EXPECTED_EVENTS or events["event_id"].n_unique() != EXPECTED_EVENTS:
        raise RuntimeError("SPDR-011 census must contain exactly 3,606 unique event IDs")
    if set(events["symbol"].unique().to_list()) != set(SYMBOLS):
        raise RuntimeError("SPDR-011 census symbol set changed")
    assert_causal_provenance(events)

    if not SIGNED_ATTESTATION.exists():
        raise RuntimeError("signed TRAIN attestation missing")
    if _sha256(SIGNED_ATTESTATION) != SIGNED_ATTESTATION_SHA256:
        raise RuntimeError("signed TRAIN attestation hash mismatch")
    signed = json.loads(SIGNED_ATTESTATION.read_text(encoding="utf-8"))
    if signed.get("status") != "VERIFIED":
        raise RuntimeError("signed TRAIN attestation is not VERIFIED")
    if tuple(signed.get("symbols", ())) != SYMBOLS:
        raise RuntimeError("signed TRAIN attestation symbol set changed")
    fence = signed.get("fence", {})
    if fence.get("test_rows_read") != 0 or fence.get("holdout_rows_read") != 0:
        raise RuntimeError("signed TRAIN attestation records forbidden-band reads")
    if not SIGNED_CATALOG.is_dir():
        raise RuntimeError("signed TRAIN catalog missing")
    return events.sort("event_id"), signed


def _pandas_to_polars(frame: Any) -> pl.DataFrame:
    if frame is None or len(frame) == 0:
        return pl.DataFrame()
    return pl.from_pandas(frame.reset_index() if hasattr(frame, "reset_index") else frame)


def _for_instrument(frame: pl.DataFrame, instrument_id: str) -> pl.DataFrame:
    if frame.is_empty() or "instrument_id" not in frame.columns:
        return frame
    return frame.filter(pl.col("instrument_id").cast(pl.Utf8) == instrument_id)


def _run1_events(events: pl.DataFrame) -> pl.DataFrame:
    """Return the DESIGN population authorised for Run 1."""
    if "band" not in events.columns:
        raise ValueError("census events require band")
    selected = events.filter(pl.col("band") == "DESIGN").sort("event_id")
    if selected.is_empty() or set(selected["band"].unique().to_list()) != {"DESIGN"}:
        raise RuntimeError("Run 1 requires a non-empty DESIGN-only population")
    if selected["entry_ts"].max() >= RUN1_END_UTC:
        raise RuntimeError("Run-1 DESIGN event reaches the CONFIRM boundary")
    return selected


def _run1_data_end(events: pl.DataFrame) -> datetime:
    """Return the last source-bar close needed for the final DESIGN exit open."""
    if events.is_empty() or "exit_ts" not in events.columns:
        raise ValueError("Run-1 events require exit_ts")
    end = events["exit_ts"].max() + timedelta(minutes=1)
    latest_allowed = RUN1_END_UTC + timedelta(minutes=1)
    if end > latest_allowed:
        raise RuntimeError("Run-1 data end reaches beyond the DESIGN exit seam")
    return end


def _executable_events(artifact: pl.DataFrame) -> pl.DataFrame:
    """Select events with both real-open marks while retaining all artifact rows."""
    if "4h_available" not in artifact.columns:
        raise ValueError("artifact requires 4h_available")
    return artifact.filter(pl.col("4h_available")).sort("event_id")


def _execution_tick_frame(schedule: pl.DataFrame, marks: pl.DataFrame) -> pl.DataFrame:
    """Map scheduled actions to their real next-minute open and engine sequence time."""
    required_schedule = {"client_order_id", "symbol", "decision_ts"}
    required_marks = {"symbol", "SourceCloseTime", "RealOpen", "Volume"}
    if missing := sorted(required_schedule - set(schedule.columns)):
        raise ValueError(f"schedule missing execution columns: {missing}")
    if missing := sorted(required_marks - set(marks.columns)):
        raise ValueError(f"marks missing execution columns: {missing}")
    datetime_ns = pl.Datetime("ns", "UTC")
    actions = schedule.select(
        "client_order_id",
        "symbol",
        pl.col("decision_ts").cast(datetime_ns),
    ).with_columns(
        (pl.col("decision_ts") + pl.duration(minutes=1))
        .cast(datetime_ns)
        .alias("source_close_ts")
    )
    source = marks.select(
        "symbol",
        pl.col("SourceCloseTime").cast(datetime_ns).alias("source_close_ts"),
        pl.col("RealOpen").alias("price"),
        pl.col("Volume").alias("size"),
    )
    joined = actions.join(source, on=["symbol", "source_close_ts"], how="left")
    missing = joined.filter(pl.col("price").is_null() | (pl.col("size") <= 0))
    if missing.height:
        raise RuntimeError(f"missing real-open execution marks for {missing.height} actions")
    return joined.select(
        "client_order_id",
        "symbol",
        "source_close_ts",
        pl.col("decision_ts").alias("ts_event"),
        (pl.col("decision_ts").dt.epoch("ns") + 1).alias("ts_init_ns"),
        "price",
        "size",
    ).sort(["ts_init_ns", "symbol", "client_order_id"])


def _execution_ticks(frame: pl.DataFrame, instruments: dict[str, Any]) -> list[TradeTick]:
    """Construct real-price execution ticks from the audited mapping frame."""
    ticks = []
    for row in frame.iter_rows(named=True):
        instrument = instruments.get(row["symbol"])
        if instrument is None:
            raise RuntimeError(f"execution instrument missing for {row['symbol']}")
        ticks.append(
            TradeTick(
                instrument_id=instrument.id,
                price=instrument.make_price(row["price"]),
                size=instrument.make_qty(row["size"]),
                aggressor_side=AggressorSide.NO_AGGRESSOR,
                trade_id=TradeId(f"OPEN-{row['client_order_id']}"),
                ts_event=int(row["ts_event"].timestamp() * 1_000_000_000),
                ts_init=int(row["ts_init_ns"]),
            )
        )
    return ticks


def _execution_latency_config() -> ImportableLatencyModelConfig:
    """Delay order insertion until the sequenced real-open execution event."""
    return ImportableLatencyModelConfig(
        latency_model_path="nautilus_trader.backtest.models:LatencyModel",
        config_path="nautilus_trader.backtest.config:LatencyModelConfig",
        config={
            "base_latency_nanos": 0,
            "insert_latency_nanos": 1,
            "update_latency_nanos": 0,
            "cancel_latency_nanos": 0,
        },
    )


def _strategy_config(symbol: str, schedule_path: Path) -> ImportableStrategyConfig:
    instrument_id = f"{symbol}-LINEAR.BYBIT"
    return ImportableStrategyConfig(
        strategy_path="spdr011_strategy:Spdr011ScheduleStrategy",
        config_path="spdr011_strategy:Spdr011ScheduleConfig",
        config={
            "instrument_id": instrument_id,
            "trade_size": TRADE_SIZE[symbol],
            "schedule_path": str(schedule_path),
        },
    )


def _write_schedules(events: pl.DataFrame) -> dict[str, Path]:
    SCHEDULE_ROOT.mkdir(parents=True, exist_ok=False)
    paths: dict[str, Path] = {}
    for symbol in SYMBOLS:
        path = SCHEDULE_ROOT / f"{symbol}.parquet"
        build_target_schedule(events.filter(pl.col("symbol") == symbol)).write_parquet(path)
        paths[symbol] = path
    return paths


def _bar_marks(events: pl.DataFrame, fence: Any) -> pl.DataFrame:
    catalog = ParquetDataCatalog(str(CATALOG))
    start = fence.analysis_start_utc
    end = _run1_data_end(events)
    frames = []
    for symbol in SYMBOLS:
        bars = fenced_bar_query(
            catalog,
            [f"{symbol}-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL"],
            start=start,
            end=end,
            band="TRAIN",
            manifest=fence,
        )
        frames.append(
            pl.DataFrame(
                {
                    "symbol": [symbol] * len(bars),
                    "SourceCloseTime": [bar.ts_event for bar in bars],
                    "RealOpen": [float(bar.open) for bar in bars],
                    "RealHigh": [float(bar.high) for bar in bars],
                    "RealLow": [float(bar.low) for bar in bars],
                    "RealClose": [float(bar.close) for bar in bars],
                    "Volume": [float(bar.volume) for bar in bars],
                }
            ).with_columns(
                pl.from_epoch("SourceCloseTime", time_unit="ns")
                .dt.replace_time_zone("UTC")
                .alias("SourceCloseTime")
            )
        )
    return pl.concat(frames).sort(["SourceCloseTime", "symbol"])


def _load_census_derivation() -> Any:
    path = EXP / "design_derivations/census.py"
    spec = importlib.util.spec_from_file_location("spdr011_census_runtime", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load census derivation: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _matched_timing_candidates(
    marks: pl.DataFrame,
    events: pl.DataFrame,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Recreate causal non-breakout boundaries; exclude every signal episode overlap."""
    census = _load_census_derivation()
    daily_by_symbol: dict[str, pl.DataFrame] = {}
    four_hour = []
    for symbol in SYMBOLS:
        minutes = (
            marks.filter(pl.col("symbol") == symbol)
            .select(
                "symbol",
                pl.col("SourceCloseTime").alias("ts_event"),
                pl.col("RealOpen").alias("open"),
                pl.col("RealHigh").alias("high"),
                pl.col("RealLow").alias("low"),
                pl.col("RealClose").alias("close"),
            )
        )
        daily, slots = census.aggregate_inputs(minutes, coverage_attested=True)
        daily_by_symbol[symbol] = daily
        four_hour.append(slots)
    states = census.build_states(daily_by_symbol)
    top2_pairs = (
        states.filter(pl.col("cross_rank") <= 2)
        .sort(["trade_day", "cross_rank"])
        .group_by("trade_day", maintain_order=True)
        .agg(pl.col("symbol"))
        .filter(pl.col("symbol").list.len() == 2)
        .select(
            "trade_day",
            pl.col("symbol").list.get(0).alias("symbol_1"),
            pl.col("symbol").list.get(1).alias("symbol_2"),
        )
    )
    boundaries = (
        pl.concat(four_hour)
        .with_columns(pl.col("slot_start").dt.date().alias("trade_day"))
        .join(states, on=["symbol", "trade_day"], how="inner", validate="m:1")
        .filter(
            (pl.col("close") <= pl.col("prior_day_high"))
            & (pl.col("close") >= pl.col("prior_day_low"))
        )
        .filter(
            (pl.col("slot_end") >= events["entry_ts"].min())
            & (pl.col("slot_end") < events["exit_ts"].max())
        )
        .sort(["symbol", "slot_end"])
    )
    signal_intervals = {
        symbol: events.filter(pl.col("symbol") == symbol)
        .select("entry_ts", "exit_ts")
        .iter_rows()
        for symbol in SYMBOLS
    }
    records: list[dict[str, Any]] = []
    for row in boundaries.iter_rows(named=True):
        entry = row["slot_end"]
        exit_ = entry + census.timedelta(hours=4)
        if any(
            entry < signal_exit and exit_ > signal_entry
            for signal_entry, signal_exit in signal_intervals[row["symbol"]]
        ):
            continue
        band = "DESIGN" if entry < census.DESIGN_END else "CONFIRM"
        third = census._calendar_third(entry, band)
        for direction in (-1, 1):
            records.append(
                {
                    "candidate_id": (
                        f"{row['symbol']}::{entry.isoformat()}::{direction:+d}::NONBREAKOUT"
                    ),
                    "event_id": (
                        f"{row['symbol']}::{entry.isoformat()}::{direction:+d}::NONBREAKOUT"
                    ),
                    "band": band,
                    "symbol": row["symbol"],
                    "trigger_ts": entry,
                    "entry_ts": entry,
                    "exit_ts": exit_,
                    "trade_day": row["trade_day"],
                    "utc_slot": row["slot_start"].hour,
                    "calendar_third": third,
                    "direction": direction,
                    "vol_tercile": row["vol_tercile"],
                    "beta60": row["beta60"],
                    "occupancy": 1,
                }
            )
    return pl.DataFrame(records, infer_schema_length=None).sort("candidate_id"), top2_pairs


def _signed_slot_frame(fence: Any, start: datetime, end: datetime) -> pl.DataFrame:
    catalog = ParquetDataCatalog(str(SIGNED_CATALOG))
    rows: list[dict[str, Any]] = []
    start_ns = int(start.timestamp() * 1_000_000_000)
    end_ns = int(end.timestamp() * 1_000_000_000)
    for symbol in SYMBOLS:
        instrument_id = f"{symbol}-LINEAR.BYBIT"
        records = catalog.query(
            data_cls=SignedBar,
            identifiers=[instrument_id],
            start=start_ns,
            end=end_ns,
        )
        for wrapped in records:
            bar = getattr(wrapped, "data", wrapped)
            rows.append(
                {
                    "symbol": symbol,
                    "signed_known_ts": datetime.fromtimestamp(
                        bar.ts_event / 1_000_000_000,
                        tz=timezone.utc,
                    ),
                    "BuyVolume": float(bar.buy_volume),
                    "SellVolume": float(bar.sell_volume),
                    "Volume": float(bar.volume),
                }
            )
    minutes = pl.DataFrame(rows, infer_schema_length=None).with_columns(
        (pl.col("signed_known_ts") - pl.duration(minutes=1))
        .dt.truncate("4h")
        .alias("slot_start")
    )
    slots = (
        minutes.group_by("symbol", "slot_start")
        .agg(
            pl.col("signed_known_ts").max(),
            pl.col("BuyVolume").sum(),
            pl.col("SellVolume").sum(),
            pl.col("Volume").sum(),
        )
        .with_columns(
            (pl.col("slot_start") + pl.duration(hours=4)).alias("trigger_ts"),
            pl.col("slot_start").dt.hour().alias("utc_slot"),
        )
        .sort(["symbol", "utc_slot", "trigger_ts"])
    )
    enriched = []
    for group in slots.partition_by(["symbol", "utc_slot"], maintain_order=True):
        prior: list[float] = []
        for row in group.iter_rows(named=True):
            total = float(row["BuyVolume"] + row["SellVolume"])
            imbalance = (float(row["BuyVolume"]) - float(row["SellVolume"])) / total if total else None
            if imbalance is None or len(prior) < 60:
                percentile_long = None
                percentile_short = None
            else:
                values = prior[-60:]
                below = sum(value < imbalance for value in values)
                equal = sum(value == imbalance for value in values)
                percentile_long = (below + 0.5 * equal) / len(values)
                above = sum(value > imbalance for value in values)
                percentile_short = (above + 0.5 * equal) / len(values)
            enriched.append(
                {
                    **row,
                    "flow_pct_long": percentile_long,
                    "flow_pct_short": percentile_short,
                }
            )
            if imbalance is not None:
                prior.append(imbalance)
    return pl.DataFrame(enriched, infer_schema_length=None).drop("slot_start", "utc_slot")


def run_train_emission(*, operator_execution_authority: str) -> dict[str, Any]:
    """Run the approved DESIGN emission after QA and operator authority.

    This function is deliberately not exposed through a CLI. It calibrates the synthetic
    future-path sentinel before the engine or any real outcome is opened.
    """
    if not operator_execution_authority.strip():
        raise PermissionError("explicit operator execution authority is required")
    census_events, signed_attestation = assert_preexecution_inputs()
    events = _run1_events(census_events)
    sentinel = calibrate_future_destroy_sentinel(events, n_seeds=2000, seed0=31_000)
    fence = load_fence_manifest()
    start = events["entry_ts"].min()
    end = _run1_data_end(events)
    assert_within_fence(fence, start, end, band="TRAIN")
    marks = _bar_marks(events, fence)
    artifact = attach_open_to_open_outcomes(events, marks)
    executable = _executable_events(artifact)
    schedule_paths = _write_schedules(executable)
    schedule = pl.concat(
        [pl.read_parquet(schedule_paths[symbol]) for symbol in SYMBOLS]
    ).sort(["decision_ts", "symbol", "action"])
    tick_frame = _execution_tick_frame(schedule, marks)
    primary_catalog = ParquetDataCatalog(str(CATALOG))
    instrument_list = primary_catalog.instruments(
        instrument_ids=[f"{symbol}-LINEAR.BYBIT" for symbol in SYMBOLS]
    )
    instruments = {
        str(instrument.id).split("-LINEAR.", maxsplit=1)[0]: instrument
        for instrument in instrument_list
    }
    if set(instruments) != set(SYMBOLS):
        raise RuntimeError("execution instrument set does not match Run-1 symbols")
    execution_ticks = _execution_ticks(tick_frame, instruments)
    execution_catalog = ParquetDataCatalog(str(EXECUTION_CATALOG))
    execution_catalog.write_data(instrument_list)
    execution_catalog.write_data(execution_ticks)
    # A6: this must be the last signed-catalog operation before constructing the engine.
    live_signed_tree_sha256 = assert_signed_catalog_tree(
        SIGNED_CATALOG,
        signed_attestation["catalog_tree_sha256"],
    )

    run_config = BacktestRunConfig(
        dispose_on_completion=False,
        engine=BacktestEngineConfig(
            logging=LoggingConfig(log_level="ERROR", log_colors=False, print_config=False),
            strategies=[_strategy_config(symbol, schedule_paths[symbol]) for symbol in SYMBOLS],
        ),
        venues=[
            BacktestVenueConfig(
                name="BYBIT",
                oms_type="NETTING",
                account_type="MARGIN",
                base_currency="USDT",
                starting_balances=["1000000 USDT"],
                book_type="L1_MBP",
                latency_model=_execution_latency_config(),
            )
        ],
        data=[
            BacktestDataConfig(
                catalog_path=str(CATALOG),
                data_cls=Bar,
                instrument_id=f"{symbol}-LINEAR.BYBIT",
                start_time=start.isoformat(),
                end_time=end.isoformat(),
            )
            for symbol in SYMBOLS
        ]
        + [
            BacktestDataConfig(
                catalog_path=str(EXECUTION_CATALOG),
                data_cls=TradeTick,
                instrument_id=f"{symbol}-LINEAR.BYBIT",
                start_time=start.isoformat(),
                end_time=end.isoformat(),
            )
            for symbol in SYMBOLS
        ],
    )
    node = BacktestNode(configs=[run_config])
    results = node.run()
    engine = node.get_engine(run_config.id)
    fills = _pandas_to_polars(engine.trader.generate_order_fills_report())
    orders = _pandas_to_polars(engine.trader.generate_orders_report())
    positions = _pandas_to_polars(engine.trader.generate_positions_report())
    node.dispose()

    run_payload = {
        "experiment": "SPDR-011",
        "band": "DESIGN",
        "symbols": list(SYMBOLS),
        "census_sha256": CENSUS_SHA256,
        "signed_catalog_tree_sha256": live_signed_tree_sha256,
        "schedule_sha256": {
            symbol: _sha256(schedule_paths[symbol]) for symbol in SYMBOLS
        },
        "operator_execution_authority": operator_execution_authority,
        "window_start_utc": start.isoformat(),
        "window_end_utc": end.isoformat(),
        "execution_basis": "REAL_OPEN_TRADE_TICK_AT_DECISION_PLUS_1NS",
        "dispose_on_completion": False,
    }
    gate_cells: dict[str, dict[str, Any]] = {}
    for symbol in SYMBOLS:
        instrument_id = f"{symbol}-LINEAR.BYBIT"
        cell = RUN_ROOT / symbol
        write_emission_v1(
            cell,
            fills=_for_instrument(fills, instrument_id),
            orders=_for_instrument(orders, instrument_id),
            positions_ledger=_for_instrument(positions, instrument_id),
            bar_marks=marks.filter(pl.col("symbol") == symbol),
            instrument_id_map={symbol: instrument_id},
            run_config={**run_payload, "symbol": symbol},
            catalog_version=CATALOG_VERSION,
            catalog_path=str(CATALOG),
            fence=fence_attestation_payload(fence),
            nautilus_version=nautilus_trader.__version__,
            platform=platform.platform(),
            extra_metadata={
                "symbol": symbol,
                "signed_attestation": str(SIGNED_ATTESTATION),
            },
        )
        gate_cells[symbol] = validate_run(cell, expected_instruments=[symbol])
    gate = {
        "gate_version": "v2",
        "cells": gate_cells,
        "blocking_pass": all(report.get("blocking_pass") for report in gate_cells.values()),
    }
    if not gate["blocking_pass"]:
        raise RuntimeError("estimand validation failed; artifact assembly blocked")

    fill_reconciliation = reconcile_event_fills(
        artifact,
        schedule,
        fills,
        orders,
        marks,
    )
    artifact = artifact.join(
        fill_reconciliation["events"],
        on="event_id",
        how="left",
        validate="1:1",
    )
    for symbol in SYMBOLS:
        fill_reconciliation["actions"].filter(pl.col("symbol") == symbol).write_parquet(
            RUN_ROOT / symbol / "event_fill_reconciliation.parquet"
        )
    artifact = attach_partial_costs(artifact)
    assert_signed_catalog_tree(
        SIGNED_CATALOG,
        signed_attestation["catalog_tree_sha256"],
    )
    signed_slots = _signed_slot_frame(fence, fence.analysis_start_utc, end)
    artifact = attach_signed_flow(artifact, signed_slots)
    raw_sentinel = float(sentinel["raw_sentinel_bps"])
    sentinel_low, sentinel_high = sentinel["synthetic_null_envelope_99"]
    post_sentinel = float(sentinel["post_destroy_sentinel_bps"])
    if (
        not sentinel["derangement_zero_fixed_points"]
        or abs(raw_sentinel - 50.0) > 0.5
        or not (sentinel_low <= post_sentinel <= sentinel_high)
    ):
        raise RuntimeError("future-path synthetic sentinel integrity rule failed")
    design_artifact = artifact.filter(pl.col("band") == "DESIGN")
    conversion_controls = conversion_control_batteries(
        design_artifact,
        n_seeds=2000,
        seed0=31_000,
    )
    l3_ci = l3_date_block_ci(design_artifact)
    future_integrity = adjudicate_future_destroy(
        raw_effect_bps=conversion_controls["raw_high_minus_other_residue_bps"],
        date_block_ci_lower_by_seed=l3_ci["ci95_lower_by_seed"],
        destroyed_effect_bps=conversion_controls["future_path_derangement"][
            "seed_effect_bps"
        ],
    )
    if future_integrity["integrity_status"] == "INVALID":
        raise RuntimeError("real future-path destroy integrity rule failed")
    timing_candidates, realised_top2_pairs = _matched_timing_candidates(marks, events)
    timing_candidates = attach_partial_costs(
        attach_open_to_open_outcomes(timing_candidates, marks)
    )
    timing_control = matched_timing_battery(
        design_artifact,
        timing_candidates,
        n_seeds=2000,
        seed0=41_000,
    )
    l4_matches = random_top2_cluster_matches(
        design_artifact.filter(
            pl.col("4h_available") & (pl.col("vol_tercile") == "HIGH")
        ),
        symbols=SYMBOLS,
        realised_pairs=realised_top2_pairs.join(
            design_artifact.select("trade_day").unique(),
            on="trade_day",
            how="semi",
        ),
        n_seeds=2000,
        seed0=51_000,
    )
    l4_matched = l4_matches.filter(pl.col("match_reason").is_null())
    l4_summary = {
        "seed_range": [51_000, 52_999],
        "n_rows": l4_matches.height,
        "matched_rows": l4_matched.height,
        "null_match_rows": l4_matches.height - l4_matched.height,
        "beta_distance_quantiles": (
            l4_matched.select(
                pl.col("beta_distance").quantile(0.05).alias("p05"),
                pl.col("beta_distance").median().alias("p50"),
                pl.col("beta_distance").quantile(0.95).alias("p95"),
            ).row(0, named=True)
            if l4_matched.height
            else {"p05": None, "p50": None, "p95": None}
        ),
    }
    manifest = write_bundle(
        BUNDLE_ROOT,
        artifact,
        metadata={
            "experiment": "SPDR-011",
            "run_config": run_payload,
            "estimand_validation": gate,
            "future_destroy_sentinel": sentinel,
            "control_analysis_band": "DESIGN_ONLY",
            "conversion_controls": conversion_controls,
            "l3_date_block_ci": l3_ci,
            "future_destroy_integrity": future_integrity,
            "matched_random_timing": timing_control,
            "l4_random_top2_matching": l4_summary,
        },
    )
    return {
        "run_dir": str(RUN_ROOT),
        "bundle_dir": str(BUNDLE_ROOT),
        "bundle_sha256": manifest["bundle_sha256"],
        "n_events": artifact.height,
        "n_engine_results": len(results),
        "estimand_validation": gate,
    }
