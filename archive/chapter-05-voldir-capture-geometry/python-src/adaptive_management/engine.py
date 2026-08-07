"""One BacktestNode per process (L-31), driven by a frozen work unit.

A work unit is one instrument's one-minute bars plus one arm schedule. The parent process does
all fenced catalog reading and writes the bars parquet; this module only replays it, so the
engine process can never widen a fence.

Nautilus panics if a second engine is created in the same process (L-31), therefore every unit
runs in a spawned subprocess and returns its reports as parquet files.
"""

from __future__ import annotations

import json
import multiprocessing as mp
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
import shutil

import polars as pl

FILL_CAPACITY_MULTIPLE = 1_000  # bar volume floor, in units of the work unit trade size
MAX_ORDER_SUBMIT_RATE = "100000/00:00:01"  # independent research arms may act together
# Per-event UUIDs are regenerated on every run, so they make otherwise identical emissions
# differ. `xen.nautilus.emission` already strips them from the event log for the same reason.
EPHEMERAL_ID_COLUMNS = ("init_id",)
REPORT_FILES = ("orders.parquet", "fills.parquet", "positions.parquet", "state_ledger.parquet")


@dataclass(frozen=True)
class InstrumentSpec:
    """The minimum instrument definition needed to replay bars deterministically."""

    symbol: str
    instrument_id: str
    venue: str
    price_precision: int
    size_precision: int
    price_increment: str
    size_increment: str
    quote_currency: str = "USDT"
    base_currency: str = "BTC"
    instrument_kind: str = "cryptoperpetual"
    asset_class: str = ""


@dataclass(frozen=True)
class WorkUnit:
    unit_id: str
    instrument: InstrumentSpec
    bars_path: str
    schedule_path: str
    output_dir: str
    base_trade_size: str = "1"
    ledger_batch_rows: int = 250_000  # operational only: the emitted ledger cannot depend on it
    fence_start_ns: int | None = None
    fence_end_ns: int | None = None
    domain_ns: int = 3_600_000_000_000


def _make_instrument(spec: InstrumentSpec):
    from nautilus_trader.model.currencies import USD, USDT
    from nautilus_trader.model.enums import AssetClass
    from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue
    from nautilus_trader.model.instruments import Cfd, CryptoPerpetual, CurrencyPair
    from nautilus_trader.model.objects import Currency, Price, Quantity

    instrument_id = InstrumentId(Symbol(spec.symbol), Venue(spec.venue))
    price_increment = Price.from_str(spec.price_increment)
    size_increment = Quantity.from_str(spec.size_increment)
    quote = USDT if spec.quote_currency == "USDT" else USD
    if spec.venue == "BYBIT":
        base = Currency.from_str(spec.base_currency)
        return CryptoPerpetual(
            instrument_id=instrument_id,
            raw_symbol=Symbol(spec.symbol),
            base_currency=base,
            quote_currency=quote,
            settlement_currency=quote,
            is_inverse=False,
            price_precision=spec.price_precision,
            size_precision=spec.size_precision,
            price_increment=price_increment,
            size_increment=size_increment,
            ts_event=0,
            ts_init=0,
        )
    common = dict(
        instrument_id=instrument_id,
        raw_symbol=Symbol(spec.symbol),
        price_precision=spec.price_precision,
        size_precision=spec.size_precision,
        price_increment=price_increment,
        size_increment=size_increment,
        lot_size=None,
        max_quantity=None,
        min_quantity=None,
        max_notional=None,
        min_notional=None,
        max_price=None,
        min_price=None,
        margin_init=Decimal("0.03"),
        margin_maint=Decimal("0.03"),
        maker_fee=Decimal("0"),
        taker_fee=Decimal("0"),
        ts_event=0,
        ts_init=0,
    )
    if spec.instrument_kind == "cfd":
        return Cfd(
            asset_class=getattr(AssetClass, spec.asset_class),
            quote_currency=quote,
            **common,
        )
    return CurrencyPair(
        base_currency=Currency.from_str(spec.base_currency),
        quote_currency=quote,
        **common,
    )


def _disable_portfolio_statistics() -> None:
    """Stop the portfolio analyzer accumulating per-trade PnL series.

    The analyzer appends each closed trade to a pandas Series with `pd.concat`, copying the
    whole series every time, which is quadratic in trade count and dominated the run: a 360-day
    symbol spent 106 s of 167 s inside those copies. Nothing this package emits, validates or
    analyses reads those statistics - they exist for post-run performance logging - so the
    accumulation is disabled and `_assert_portfolio_statistics_disabled` checks it stayed off.
    """
    from nautilus_trader.analysis.analyzer import PortfolioAnalyzer

    def _skip(self, *args, **kwargs) -> None:
        return None

    # Both accumulators grow by copy: `_append_pnl_record` concatenates a Series per trade,
    # `add_position_return` enlarges one by `.loc` per closed position.
    PortfolioAnalyzer._append_pnl_record = _skip
    PortfolioAnalyzer.add_trade = _skip
    PortfolioAnalyzer.record_trade = _skip
    PortfolioAnalyzer.add_position_return = _skip
    PortfolioAnalyzer.add_return = _skip


def _assert_portfolio_statistics_disabled(engine) -> None:
    """Fail loudly if a future Nautilus version accumulates per-trade statistics anyway.

    Only the per-trade accumulators are checked. The post-run portfolio return buckets are
    computed once at the end from account state and are cheap, so they are left alone.
    """
    analyzer = getattr(engine.portfolio, "analyzer", None)
    if analyzer is None:
        return
    for name in ("_realized_pnls", "_recorded_realized_pnls", "_position_returns"):
        value = getattr(analyzer, name, None)
        if value is None:
            continue
        populated = (
            any(len(item) for item in value.values())
            if isinstance(value, dict)
            else bool(len(value))
        )
        if populated:
            raise RuntimeError(
                f"per-trade portfolio statistics were accumulated in {name}: the quadratic "
                "recorder is active again and must be disabled before a full run"
            )


def run_work_unit(unit: WorkUnit) -> dict[str, int]:
    """Replay one instrument's bars against one arm schedule. One engine per process."""
    from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
    from nautilus_trader.config import LoggingConfig, RiskEngineConfig
    from nautilus_trader.model.currencies import USD, USDT
    from nautilus_trader.model.data import Bar, BarType
    from nautilus_trader.model.enums import AccountType, OmsType
    from nautilus_trader.model.identifiers import Venue
    from nautilus_trader.model.objects import Money

    from xen.adaptive_management.strategy import (
        AdaptiveManagementConfig,
        AdaptiveManagementStrategy,
    )

    _disable_portfolio_statistics()
    instrument = _make_instrument(unit.instrument)
    bar_type = BarType.from_str(f"{instrument.id}-1-MINUTE-LAST-EXTERNAL")
    # Bar volume is a venue tick count, not tradable size, and the simulated exchange caps a
    # fill by it. Left raw it slices one entry order into several fills purely as an artifact.
    # No liquidity claim is made or implied by this floor.
    fill_capacity = float(unit.base_trade_size) * FILL_CAPACITY_MULTIPLE
    frame = pl.read_parquet(unit.bars_path).sort("ts")
    ts_ns = frame["ts"].cast(pl.Datetime("ns", "UTC")).dt.epoch("ns").to_list()
    bars = [
        Bar(
            bar_type=bar_type,
            open=instrument.make_price(o),
            high=instrument.make_price(h),
            low=instrument.make_price(low),
            close=instrument.make_price(c),
            volume=instrument.make_qty(max(float(v), fill_capacity)),
            ts_event=int(t),
            ts_init=int(t),
        )
        for o, h, low, c, v, t in zip(
            frame["open"], frame["high"], frame["low"], frame["close"],
            frame["volume"] if "volume" in frame.columns else [1] * frame.height,
            ts_ns,
            strict=True,
        )
    ]

    currency = USDT if unit.instrument.quote_currency == "USDT" else USD
    engine = BacktestEngine(
        config=BacktestEngineConfig(
            logging=LoggingConfig(log_level="ERROR", log_colors=False, print_config=False),
            risk_engine=RiskEngineConfig(
                max_order_submit_rate=MAX_ORDER_SUBMIT_RATE
            ),
            # Canonical reports come directly from the trader and strategy ledgers below.
            # Nautilus post-run performance statistics are neither emitted nor consumed.
            run_analysis=False,
        )
    )
    engine.add_venue(
        venue=Venue(unit.instrument.venue),
        oms_type=OmsType.HEDGING,  # one position per arm episode
        account_type=AccountType.MARGIN,
        base_currency=currency,
        starting_balances=[Money(10_000_000, currency)],
        # Arms are independent research paths, not a shared-capital portfolio. Recalculating
        # one aggregate account after every fill is therefore unused work; the emitted order,
        # fill, position and state ledgers remain the engine's native records.
        frozen_account=True,
    )
    engine.add_instrument(instrument)
    engine.add_data(bars)
    out = Path(unit.output_dir)
    ledger_dir = out / "_ledger_parts"
    shutil.rmtree(ledger_dir, ignore_errors=True)
    strategy = AdaptiveManagementStrategy(
        AdaptiveManagementConfig(
            instrument_id=instrument.id,
            bar_type=str(bar_type),
            schedule_path=unit.schedule_path,
            base_trade_size=Decimal(unit.base_trade_size),
            fence_start_ns=(
                int(unit.fence_start_ns)
                if unit.fence_start_ns is not None
                else int(min(ts_ns))
            ),
            fence_end_ns=(
                int(unit.fence_end_ns)
                if unit.fence_end_ns is not None
                else int(max(ts_ns))
            ),
            domain_ns=int(unit.domain_ns),
            ledger_dir=str(ledger_dir),
            ledger_batch_rows=int(unit.ledger_batch_rows),
        )
    )
    engine.add_strategy(strategy)
    engine.run()
    _assert_portfolio_statistics_disabled(engine)

    out.mkdir(parents=True, exist_ok=True)
    reports = {
        "orders.parquet": engine.trader.generate_orders_report(),
        "fills.parquet": engine.trader.generate_order_fills_report(),
        "positions.parquet": engine.trader.generate_positions_report(),
    }
    counts: dict[str, int] = {}
    for name, report in reports.items():
        frame = _report_frame(report) if len(report) else pl.DataFrame()
        _atomic_write(frame, out / name)
        counts[name] = frame.height
    counts["state_ledger.parquet"] = _write_state_ledger(
        strategy, ledger_dir, out / "state_ledger.parquet"
    )
    engine.dispose()
    (out / "unit.json").write_text(json.dumps({"unit": asdict(unit), "counts": counts}, indent=2))
    return counts


def _write_state_ledger(strategy, ledger_dir: Path, target: Path) -> int:
    """Stream the batched ledger parts into one file without holding every row in memory."""
    strategy.flush_ledger()
    parts = sorted(ledger_dir.glob("part-*.parquet")) if ledger_dir.exists() else []
    if not parts:
        _atomic_write(pl.DataFrame(), target)
        return 0
    temporary = target.with_suffix(".parquet.tmp")
    frame = pl.scan_parquet(parts)
    frame.sink_parquet(temporary)
    temporary.replace(target)
    rows = pl.scan_parquet(target).select(pl.len()).collect().item()
    shutil.rmtree(ledger_dir, ignore_errors=True)
    return int(rows)


def _report_frame(report) -> pl.DataFrame:
    """Nautilus reports, with timestamps kept as timestamps.

    Everything else is stringified so mixed object columns stay loadable, but stringifying a
    timestamp makes the emission unparseable by the adjudication shim, which needs a datetime.
    """
    import pandas as pd

    frame = report.reset_index()
    # ts_closed is object dtype whenever any position is still open, so sniffing the dtype is
    # not enough: coerce every ts_* column, leaving the integer ts_init/duration_ns alone.
    time_columns = [
        column
        for column in frame.columns
        if pd.api.types.is_datetime64_any_dtype(frame[column])
        or column in ("ts_opened", "ts_closed", "ts_last", "ts_event", "expire_time")
    ]
    for column in time_columns:
        frame[column] = pd.to_datetime(frame[column], errors="coerce", utc=True)
    frame = frame.drop(columns=[c for c in EPHEMERAL_ID_COLUMNS if c in frame.columns])
    time_columns = [c for c in time_columns if c in frame.columns]
    other = [column for column in frame.columns if column not in time_columns]
    frame[other] = frame[other].astype(str)
    return pl.from_pandas(frame)


def _atomic_write(frame: pl.DataFrame, path: Path) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.write_parquet(temporary)
    temporary.replace(path)


def _child(unit_dict: dict) -> None:
    unit = WorkUnit(instrument=InstrumentSpec(**unit_dict.pop("instrument")), **unit_dict)
    run_work_unit(unit)


def run_work_unit_subprocess(unit: WorkUnit, timeout: float = 3600.0) -> dict[str, pl.DataFrame]:
    """Run one work unit in a spawned process (L-31) and read its reports back."""
    context = mp.get_context("spawn")
    process = context.Process(target=_child, args=(asdict(unit),))
    process.start()
    process.join(timeout)
    if process.exitcode != 0:
        raise RuntimeError(f"work unit {unit.unit_id} failed with exit code {process.exitcode}")
    out = Path(unit.output_dir)
    return {
        name.removesuffix(".parquet"): pl.read_parquet(out / name)
        if (out / name).stat().st_size
        else pl.DataFrame()
        for name in REPORT_FILES
    }
