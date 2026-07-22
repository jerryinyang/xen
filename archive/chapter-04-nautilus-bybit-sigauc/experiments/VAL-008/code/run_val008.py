"""VAL-008 runner — 39 BacktestNode runs → emission contract v1 (PINNED attestation).

Usage (from python/):
    uv run python experiments/VAL-008/code/run_val008.py --all
    uv run python experiments/VAL-008/code/run_val008.py --symbols BTCUSDT --arms BASELINE
    uv run python experiments/VAL-008/code/run_val008.py --stubcheck   # STUB negative gate test

Arms: BASELINE, LEAK, LEAK-LAG1, LEAK-SHUF-s{0..4}, BASELINE-SHUF-s{0..4}.
Run dirs: data/nautilus_runs/VAL-008/<SYMBOL>__<ARM>/ (flat, validate_family layout).

DEVIATIONS: none.
"""
from __future__ import annotations

import argparse
import json
import platform as _platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

CODE_DIR = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]  # python/
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(CODE_DIR))

import nautilus_trader  # noqa: E402
from nautilus_trader.backtest.node import BacktestNode  # noqa: E402
from nautilus_trader.config import (  # noqa: E402
    BacktestDataConfig,
    BacktestEngineConfig,
    BacktestRunConfig,
    BacktestVenueConfig,
    ImportableStrategyConfig,
    LoggingConfig,
)
from nautilus_trader.model.data import Bar  # noqa: E402
from nautilus_trader.persistence.catalog import ParquetDataCatalog  # noqa: E402

from xen.nautilus.catalog_fence import (  # noqa: E402
    assert_within_fence,
    fence_attestation_payload,
    fenced_bar_query,
    load_fence_manifest,
)
from xen.nautilus.emission import write_emission_v1  # noqa: E402

SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
TRADE_SIZE = {"BTCUSDT": "0.1", "ETHUSDT": "1", "SOLUSDT": "10"}
WIN_START = datetime(2023, 6, 1, tzinfo=timezone.utc)
FAST, SLOW = 20, 100
SEEDS = (0, 1, 2, 3, 4)
ARMS = (
    ["BASELINE", "LEAK", "LEAK-LAG1"]
    + [f"LEAK-SHUF-s{s}" for s in SEEDS]
    + [f"BASELINE-SHUF-s{s}" for s in SEEDS]
)
CATALOG_PATH = REPO / "data" / "catalog"
RUNS_ROOT = REPO / "data" / "nautilus_runs" / "VAL-008"
STUB_DIR = REPO / "data" / "nautilus_runs" / "VAL-008-stubcheck"
SCHEDULES = CODE_DIR / "schedules"
RESULTS = CODE_DIR.parent / "results"
CATALOG_VERSION = "INFR-011-A4-2026-07-16"


def _pandas_to_polars(df) -> pl.DataFrame:
    if df is None or len(df) == 0:
        return pl.DataFrame()
    return pl.from_pandas(df.reset_index() if hasattr(df, "reset_index") else df)


def bar_marks_for(symbol: str, fence) -> pl.DataFrame:
    """Fenced TRAIN read → bar_marks frame (SourceCloseTime = ts_event, RealOpen = bar open)."""
    catalog = ParquetDataCatalog(str(CATALOG_PATH))
    bars = fenced_bar_query(
        catalog,
        [f"{symbol}-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL"],
        start=WIN_START,
        end=fence.train_end_utc,
        band="TRAIN",
    )
    return pl.DataFrame(
        {
            "SourceCloseTime": [b.ts_event for b in bars],
            "RealOpen": [float(b.open) for b in bars],
            "RealHigh": [float(b.high) for b in bars],
            "RealLow": [float(b.low) for b in bars],
            "RealClose": [float(b.close) for b in bars],
            "Volume": [float(b.volume) for b in bars],
        }
    ).with_columns(pl.from_epoch("SourceCloseTime", time_unit="ns").alias("SourceCloseTime")).sort(
        "SourceCloseTime"
    )


def strategy_config(symbol: str, arm: str) -> tuple[ImportableStrategyConfig, dict]:
    iid = f"{symbol}-LINEAR.BYBIT"
    bar_type = f"{iid}-1-MINUTE-LAST-EXTERNAL"
    if arm == "BASELINE":
        cfg = {
            "instrument_id": iid,
            "bar_type": bar_type,
            "trade_size": TRADE_SIZE[symbol],
            "fast_period": FAST,
            "slow_period": SLOW,
        }
        imp = ImportableStrategyConfig(
            strategy_path="val008_strategies:MACrossFlip",
            config_path="val008_strategies:MACrossFlipConfig",
            config=cfg,
        )
        extra = {"strategy": "MACrossFlip", **cfg}
    else:
        sched = SCHEDULES / f"{symbol}__{arm}.parquet"
        if not sched.exists():
            raise FileNotFoundError(f"schedule missing: {sched} — run gen_schedules.py first")
        manifest = json.loads((SCHEDULES / "manifest.json").read_text())
        sha = manifest["files"][sched.name]["sha256"]
        cfg = {
            "instrument_id": iid,
            "bar_type": bar_type,
            "trade_size": TRADE_SIZE[symbol],
            "schedule_path": str(sched),
        }
        imp = ImportableStrategyConfig(
            strategy_path="val008_strategies:ScheduleExecutor",
            config_path="val008_strategies:ScheduleExecutorConfig",
            config=cfg,
        )
        extra = {"strategy": "ScheduleExecutor", "schedule_sha256": sha, **cfg}
    return imp, extra


def run_cell(symbol: str, arm: str, fence, bar_marks: pl.DataFrame) -> dict:
    iid = f"{symbol}-LINEAR.BYBIT"
    strat_cfg, cfg_extra = strategy_config(symbol, arm)
    assert_within_fence(fence, WIN_START, fence.train_end_utc, band="TRAIN")
    run_config = BacktestRunConfig(
        dispose_on_completion=False,  # keep engine cache alive for report capture
        engine=BacktestEngineConfig(
            logging=LoggingConfig(log_level="ERROR", log_colors=False, print_config=False),
            strategies=[strat_cfg],
        ),
        venues=[
            BacktestVenueConfig(
                name="BYBIT",
                oms_type="NETTING",
                account_type="MARGIN",
                base_currency="USDT",
                starting_balances=["1000000 USDT"],
                book_type="L1_MBP",
            )
        ],
        data=[
            BacktestDataConfig(
                catalog_path=str(CATALOG_PATH),
                data_cls=Bar,
                instrument_id=iid,
                start_time=WIN_START.isoformat(),
                end_time=fence.train_end_utc.isoformat(),
            )
        ],
    )
    node = BacktestNode(configs=[run_config])
    results = node.run()
    result = results[0]
    engine = node.get_engine(run_config.id)
    fills = _pandas_to_polars(engine.trader.generate_order_fills_report())
    orders = _pandas_to_polars(engine.trader.generate_orders_report())
    positions = _pandas_to_polars(engine.trader.generate_positions_report())
    node.dispose()

    run_cfg = {
        "experiment": "VAL-008",
        "symbol": symbol,
        "arm": arm,
        "window_start_utc": WIN_START.isoformat(),
        "window_end_utc": fence.train_end_utc.isoformat(),
        "band": "TRAIN",
        "venue": "BYBIT",
        "oms_type": "NETTING",
        "book_type": "L1_MBP",
        **cfg_extra,
    }
    run_dir = RUNS_ROOT / f"{symbol}__{arm}"
    write_emission_v1(
        run_dir,
        fills=fills,
        orders=orders,
        positions_ledger=positions,
        bar_marks=bar_marks,
        instrument_id_map={symbol: iid},
        run_config=run_cfg,
        catalog_version=CATALOG_VERSION,
        catalog_path=str(CATALOG_PATH),
        fence=fence_attestation_payload(fence),
        nautilus_version=nautilus_trader.__version__,
        platform=_platform.platform(),
        extra_metadata={"symbol": symbol, "arm": arm},
    )
    summary = {
        "symbol": symbol,
        "arm": arm,
        "run_dir": str(run_dir),
        "iterations": result.iterations,
        "n_fills": fills.height,
        "n_positions": positions.height,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
    }
    print(
        f"RUN {symbol}__{arm}: iters={result.iterations} fills={fills.height} "
        f"positions={positions.height}"
    )
    return summary


def stubcheck(fence) -> None:
    """Deliberate STUB emission (copy of BASELINE BTC tables) — gate v2 must FAIL it."""
    src = RUNS_ROOT / "BTCUSDT__BASELINE"
    if not src.exists():
        raise FileNotFoundError("run BTCUSDT BASELINE first")
    write_emission_v1(
        STUB_DIR,
        fills=pl.read_parquet(src / "fills.parquet"),
        orders=pl.read_parquet(src / "orders.parquet"),
        positions_ledger=pl.read_parquet(src / "positions_ledger.parquet"),
        bar_marks=pl.read_parquet(src / "bar_marks.parquet"),
        instrument_id_map={"BTCUSDT": "BTCUSDT-LINEAR.BYBIT"},
        run_config={"experiment": "VAL-008", "purpose": "stub-negative-gate-check"},
        catalog_version=CATALOG_VERSION,
        catalog_path=str(CATALOG_PATH),
        fence=None,  # default STUB payload — the point of the negative test
        nautilus_version=nautilus_trader.__version__,
        platform=_platform.platform(),
        extra_metadata={"symbol": "BTCUSDT", "arm": "STUBCHECK"},
    )
    from xen.estimand_validation import validate_run

    report = validate_run(STUB_DIR)
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "stub_negative_check.json").write_text(
        json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(f"STUBCHECK blocking_pass={report['blocking_pass']} (must be False)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default=",".join(SYMBOLS))
    ap.add_argument("--arms", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--stubcheck", action="store_true")
    args = ap.parse_args()

    fence = load_fence_manifest()
    if args.stubcheck:
        stubcheck(fence)
        return 0

    symbols = [s.strip() for s in args.symbols.split(",")]
    arms = ARMS if (args.all or not args.arms) else [a.strip() for a in args.arms.split(",")]
    RUNS_ROOT.mkdir(parents=True, exist_ok=True)
    log_path = RESULTS / "run_log.jsonl"
    RESULTS.mkdir(parents=True, exist_ok=True)

    cells = [(s, a) for s in symbols for a in arms]
    if len(cells) > 1:
        # Nautilus Rust logging initializes once per process — one BacktestNode per process.
        import subprocess

        for symbol, arm in cells:
            proc = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()),
                 "--symbols", symbol, "--arms", arm],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                check=False,
            )
            sys.stdout.write(proc.stdout)
            sys.stdout.flush()
            if proc.returncode != 0:
                print(f"FAILED {symbol}__{arm} (rc={proc.returncode}):\n{proc.stderr[-2000:]}")
                return 1
        return 0

    for symbol in symbols:
        marks = bar_marks_for(symbol, fence)
        for arm in arms:
            summary = run_cell(symbol, arm, fence, marks)
            with log_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(summary, default=str) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
