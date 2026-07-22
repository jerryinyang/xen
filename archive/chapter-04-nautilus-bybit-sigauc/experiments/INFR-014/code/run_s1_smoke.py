#!/usr/bin/env python3
"""INFR-014 WP5 — S1 multi-instrument single-engine smoke (design §8).

Path A: one BacktestNode, multi-instrument engine (BTC/ETH/SOL ADMITTED catalog),
        dispose_on_completion=False (L-30).
Path B: subprocess-per-instrument (L-31 baseline).
Criterion: bitwise identity of canonicalised overlapping emission columns for each
instrument Path A vs Path B (or FAIL → batch topology = subprocess-per-cell).
Fence: TRAIN PINNED; estimand gate v2 blocking_pass per cell emission.

Writes results/s1_smoke.json + data/nautilus_runs/INFR-014-S1/* emissions.
"""
from __future__ import annotations

import hashlib
import json
import platform as _platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[3]  # python/
REPO = ROOT.parent
EXP = Path(__file__).resolve().parents[1]
RESULTS = EXP / "results"
CODE = Path(__file__).resolve().parent
CATALOG_PATH = REPO / "data" / "catalog"
RUNS_ROOT = REPO / "data" / "nautilus_runs" / "INFR-014-S1"
CATALOG_VERSION = "INFR-011-A4-2026-07-16"

sys.path.insert(0, str(ROOT / "src"))

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

from xen.estimand_validation import validate_run  # noqa: E402
from xen.nautilus.catalog_fence import (  # noqa: E402
    assert_within_fence,
    fence_attestation_payload,
    fenced_bar_query,
    load_fence_manifest,
)
from xen.nautilus.emission import write_emission_v1  # noqa: E402

SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
TRADE_SIZE = {"BTCUSDT": "0.1", "ETHUSDT": "1", "SOLUSDT": "10"}
# Short TRAIN window (smoke); fully inside fence TRAIN band
WIN_START = datetime(2023, 6, 1, tzinfo=timezone.utc)
WIN_END = datetime(2023, 7, 1, tzinfo=timezone.utc)  # 1 month smoke
FAST, SLOW = 10, 30

_CANON_FILL_COLS = (
    "instrument_id", "side", "quantity", "filled_qty", "avg_px", "slippage",
    "liquidity_side", "status", "type", "time_in_force", "ts_last",
)
_CANON_ORDER_COLS = (
    "instrument_id", "side", "quantity", "filled_qty", "avg_px", "status",
    "type", "time_in_force", "ts_last",
)
_CANON_POS_COLS = (
    "instrument_id", "entry", "side", "quantity", "peak_qty", "ts_opened",
    "ts_closed", "avg_px_open", "avg_px_close", "realized_pnl",
)


def _pandas_to_polars(df: Any) -> pl.DataFrame:
    if df is None or len(df) == 0:
        return pl.DataFrame()
    return pl.from_pandas(df.reset_index() if hasattr(df, "reset_index") else df)


def _canonical_cols(df: pl.DataFrame, kind: str) -> pl.DataFrame:
    wanted = {
        "fills": _CANON_FILL_COLS,
        "orders": _CANON_ORDER_COLS,
        "positions": _CANON_POS_COLS,
    }[kind]
    keep = [c for c in wanted if c in df.columns]
    if not keep or df.height == 0:
        return pl.DataFrame()
    out = df.select(keep)
    # filter to one instrument if present
    sort_keys = [c for c in ("ts_last", "ts_opened", "instrument_id", "side", "avg_px") if c in out.columns]
    if sort_keys:
        out = out.sort(sort_keys)
    return out


def _df_digest(df: pl.DataFrame) -> str:
    if df is None or df.height == 0:
        return hashlib.sha256(b"empty").hexdigest()
    raw = json.dumps(df.to_dicts(), sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _filter_instr(df: pl.DataFrame, iid: str) -> pl.DataFrame:
    if df is None or df.height == 0 or "instrument_id" not in df.columns:
        return df if df is not None else pl.DataFrame()
    return df.filter(pl.col("instrument_id").cast(pl.Utf8) == iid)


def bar_marks_for(symbol: str, fence) -> pl.DataFrame:
    catalog = ParquetDataCatalog(str(CATALOG_PATH))
    bars = fenced_bar_query(
        catalog,
        [f"{symbol}-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL"],
        start=WIN_START,
        end=WIN_END,
        band="TRAIN",
        manifest=fence,
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
    ).with_columns(
        pl.from_epoch("SourceCloseTime", time_unit="ns").alias("SourceCloseTime")
    ).sort("SourceCloseTime")


def _strategy_cfg(symbol: str) -> ImportableStrategyConfig:
    iid = f"{symbol}-LINEAR.BYBIT"
    return ImportableStrategyConfig(
        strategy_path="nautilus_trader.examples.strategies.ema_cross:EMACross",
        config_path="nautilus_trader.examples.strategies.ema_cross:EMACrossConfig",
        config={
            "instrument_id": iid,
            "bar_type": f"{iid}-1-MINUTE-LAST-EXTERNAL",
            "trade_size": TRADE_SIZE[symbol],
            "fast_ema_period": FAST,
            "slow_ema_period": SLOW,
            "request_bars": False,
        },
    )


def _fill_ts_anchor_check(fills: pl.DataFrame, marks: pl.DataFrame) -> dict[str, Any]:
    """L-29 sample: fill price near bar open scale on ADMITTED bars."""
    if fills is None or fills.height == 0 or marks is None or marks.height < 2:
        return {"checked": False, "reason": "empty", "pass": False}
    price_col = next(
        (c for c in ("avg_px", "last_px", "price") if c in fills.columns), None
    )
    if price_col is None or "RealOpen" not in marks.columns:
        return {"checked": False, "reason": "missing cols", "pass": False}
    px = float(fills.get_column(price_col).to_list()[0])
    opens = marks.get_column("RealOpen").to_numpy().astype(float)
    nearest = float(opens[np.argmin(np.abs(opens - px))])
    rel = abs(px - nearest) / max(abs(nearest), 1e-12)
    return {
        "checked": True,
        "sample_fill_px": px,
        "nearest_open": nearest,
        "rel_err": rel,
        "pass": bool(rel < 0.05),
        "note": "L-29 sample: fill near catalog open scale",
    }


def run_path_a(fence) -> dict[str, Any]:
    """One node, multi-instrument, multi-strategy; dispose_on_completion=False."""
    assert_within_fence(fence, WIN_START, WIN_END, band="TRAIN")
    data_cfgs = [
        BacktestDataConfig(
            catalog_path=str(CATALOG_PATH),
            data_cls=Bar,
            instrument_id=f"{sym}-LINEAR.BYBIT",
            start_time=WIN_START.isoformat(),
            end_time=WIN_END.isoformat(),
        )
        for sym in SYMBOLS
    ]
    strategies = [_strategy_cfg(sym) for sym in SYMBOLS]
    run_config = BacktestRunConfig(
        dispose_on_completion=False,
        engine=BacktestEngineConfig(
            logging=LoggingConfig(log_level="ERROR", log_colors=False, print_config=False),
            strategies=strategies,
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
        data=data_cfgs,
    )
    node = BacktestNode(configs=[run_config])
    results = node.run()
    engine = node.get_engine(run_config.id)
    fills = _pandas_to_polars(engine.trader.generate_order_fills_report()) if engine else pl.DataFrame()
    orders = _pandas_to_polars(engine.trader.generate_orders_report()) if engine else pl.DataFrame()
    positions = (
        _pandas_to_polars(engine.trader.generate_positions_report()) if engine else pl.DataFrame()
    )
    node.dispose()

    per_sym: dict[str, Any] = {}
    gate_reports: dict[str, Any] = {}
    for sym in SYMBOLS:
        iid = f"{sym}-LINEAR.BYBIT"
        marks = bar_marks_for(sym, fence)
        f = _filter_instr(fills, iid)
        o = _filter_instr(orders, iid)
        p = _filter_instr(positions, iid)
        run_dir = RUNS_ROOT / f"pathA__{sym}"
        write_emission_v1(
            run_dir,
            fills=f,
            orders=o,
            positions_ledger=p,
            bar_marks=marks,
            instrument_id_map={sym: iid},
            run_config={
                "experiment": "INFR-014",
                "path": "A",
                "symbol": sym,
                "window_start_utc": WIN_START.isoformat(),
                "window_end_utc": WIN_END.isoformat(),
                "band": "TRAIN",
                "n_instruments_engine": len(SYMBOLS),
                "dispose_on_completion": False,
            },
            catalog_version=CATALOG_VERSION,
            catalog_path=str(CATALOG_PATH),
            fence=fence_attestation_payload(fence),
            nautilus_version=nautilus_trader.__version__,
            platform=_platform.platform(),
            extra_metadata={"symbol": sym, "path": "A"},
        )
        gate = validate_run(run_dir, expected_instruments=[sym])
        gate_reports[sym] = {
            "blocking_pass": gate.get("blocking_pass"),
            "gate_version": gate.get("gate_version"),
            "run_dir": str(run_dir),
        }
        per_sym[sym] = {
            "fills_digest": _df_digest(_canonical_cols(f, "fills")),
            "orders_digest": _df_digest(_canonical_cols(o, "orders")),
            "positions_digest": _df_digest(_canonical_cols(p, "positions")),
            "fills_n": f.height,
            "orders_n": o.height,
            "positions_n": p.height,
            "fill_ts_anchor": _fill_ts_anchor_check(f, marks),
            "gate_blocking_pass": bool(gate.get("blocking_pass")),
        }
    return {
        "path": "A",
        "n_instruments": len(SYMBOLS),
        "instrument_ids": [f"{s}-LINEAR.BYBIT" for s in SYMBOLS],
        "dispose_on_completion": False,
        "n_nodes_in_process": 1,
        "n_results": len(results),
        "per_symbol": per_sym,
        "gate_reports": gate_reports,
        "admitted_catalog": True,
        "window": {"start": WIN_START.isoformat(), "end": WIN_END.isoformat(), "band": "TRAIN"},
    }


def run_path_b_symbol(symbol: str, fence) -> dict[str, Any]:
    """One instrument, one node (Path B cell)."""
    assert_within_fence(fence, WIN_START, WIN_END, band="TRAIN")
    iid = f"{symbol}-LINEAR.BYBIT"
    run_config = BacktestRunConfig(
        dispose_on_completion=False,
        engine=BacktestEngineConfig(
            logging=LoggingConfig(log_level="ERROR", log_colors=False, print_config=False),
            strategies=[_strategy_cfg(symbol)],
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
                end_time=WIN_END.isoformat(),
            )
        ],
    )
    node = BacktestNode(configs=[run_config])
    node.run()
    engine = node.get_engine(run_config.id)
    fills = _pandas_to_polars(engine.trader.generate_order_fills_report()) if engine else pl.DataFrame()
    orders = _pandas_to_polars(engine.trader.generate_orders_report()) if engine else pl.DataFrame()
    positions = (
        _pandas_to_polars(engine.trader.generate_positions_report()) if engine else pl.DataFrame()
    )
    node.dispose()
    marks = bar_marks_for(symbol, fence)
    run_dir = RUNS_ROOT / f"pathB__{symbol}"
    write_emission_v1(
        run_dir,
        fills=fills,
        orders=orders,
        positions_ledger=positions,
        bar_marks=marks,
        instrument_id_map={symbol: iid},
        run_config={
            "experiment": "INFR-014",
            "path": "B",
            "symbol": symbol,
            "window_start_utc": WIN_START.isoformat(),
            "window_end_utc": WIN_END.isoformat(),
            "band": "TRAIN",
            "dispose_on_completion": False,
        },
        catalog_version=CATALOG_VERSION,
        catalog_path=str(CATALOG_PATH),
        fence=fence_attestation_payload(fence),
        nautilus_version=nautilus_trader.__version__,
        platform=_platform.platform(),
        extra_metadata={"symbol": symbol, "path": "B"},
    )
    gate = validate_run(run_dir, expected_instruments=[symbol])
    return {
        "symbol": symbol,
        "fills_digest": _df_digest(_canonical_cols(fills, "fills")),
        "orders_digest": _df_digest(_canonical_cols(orders, "orders")),
        "positions_digest": _df_digest(_canonical_cols(positions, "positions")),
        "fills_n": fills.height,
        "orders_n": orders.height,
        "positions_n": positions.height,
        "fill_ts_anchor": _fill_ts_anchor_check(fills, marks),
        "gate_blocking_pass": bool(gate.get("blocking_pass")),
        "run_dir": str(run_dir),
    }


def run_path_b(fence) -> dict[str, Any]:
    """N subprocesses (fresh process each — L-31 logging)."""
    reports = []
    for sym in SYMBOLS:
        code = f"""
import sys, json
sys.path.insert(0, {str(ROOT / 'src')!r})
sys.path.insert(0, {str(CODE)!r})
from run_s1_smoke import run_path_b_symbol
from xen.nautilus.catalog_fence import load_fence_manifest
fence = load_fence_manifest()
out = run_path_b_symbol({sym!r}, fence)
print(json.dumps(out, default=str))
"""
        proc = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            reports.append({
                "symbol": sym,
                "error": proc.stderr[-1200:],
                "rc": proc.returncode,
            })
        else:
            line = [ln for ln in proc.stdout.strip().splitlines() if ln.startswith("{")][-1]
            reports.append(json.loads(line))
    return {
        "path": "B",
        "n_instruments": len(SYMBOLS),
        "n_processes": len(SYMBOLS),
        "per_instrument": reports,
    }


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    RUNS_ROOT.mkdir(parents=True, exist_ok=True)
    fence = load_fence_manifest()

    # Verify catalog instruments exist (ADMITTED)
    catalog = ParquetDataCatalog(str(CATALOG_PATH))
    inst_ids = {str(i.id) for i in (catalog.instruments() or [])}
    for sym in SYMBOLS:
        iid = f"{sym}-LINEAR.BYBIT"
        if iid not in inst_ids:
            raise SystemExit(f"ADMITTED instrument missing from catalog: {iid}")

    print("[S1] Path A multi-instrument ADMITTED catalog...", flush=True)
    try:
        a = run_path_a(fence)
        a_ok = True
        a_err = None
        print(
            f"  A: per_sym fills={[a['per_symbol'][s]['fills_n'] for s in SYMBOLS]} "
            f"gates={[a['per_symbol'][s]['gate_blocking_pass'] for s in SYMBOLS]}",
            flush=True,
        )
    except Exception as e:
        a, a_ok, a_err = {}, False, f"{type(e).__name__}: {e}"
        print(f"  Path A FAIL: {a_err}", flush=True)

    print("[S1] Path B subprocess-per-instrument...", flush=True)
    try:
        b = run_path_b(fence)
        b_ok = True
        b_err = None
        print(f"  B: {[{k: r.get(k) for k in ('symbol','fills_n','gate_blocking_pass','error') if k in r or True} for r in b.get('per_instrument', [])]}", flush=True)
    except Exception as e:
        b, b_ok, b_err = {}, False, f"{type(e).__name__}: {e}"
        print(f"  Path B FAIL: {b_err}", flush=True)

    # A-vs-B bitwise on canonical digests per symbol (design §8 criterion)
    a_vs_b: dict[str, Any] = {}
    bitwise_all = True
    if a_ok and b_ok:
        b_by = {r.get("symbol"): r for r in b.get("per_instrument", []) if "symbol" in r}
        for sym in SYMBOLS:
            pa = a["per_symbol"][sym]
            pb = b_by.get(sym) or {}
            match = (
                pa.get("fills_digest") == pb.get("fills_digest")
                and pa.get("orders_digest") == pb.get("orders_digest")
                and pa.get("positions_digest") == pb.get("positions_digest")
            )
            a_vs_b[sym] = {
                "match": match,
                "a_fills_digest": pa.get("fills_digest"),
                "b_fills_digest": pb.get("fills_digest"),
                "a_fills_n": pa.get("fills_n"),
                "b_fills_n": pb.get("fills_n"),
            }
            if not match:
                bitwise_all = False
                # document root cause hint
                a_vs_b[sym]["root_cause_hint"] = (
                    "non-identity after UUID strip — multi-engine interaction or "
                    "report ordering; FAIL → subprocess topology"
                )
    else:
        bitwise_all = False

    gate_all = bool(
        a_ok
        and all(a["per_symbol"][s]["gate_blocking_pass"] for s in SYMBOLS)
        and b_ok
        and all(
            (r.get("gate_blocking_pass") is True)
            for r in b.get("per_instrument", [])
            if "error" not in r
        )
    )
    pass_dispose = bool(a_ok and a.get("dispose_on_completion") is False)
    pass_one_node = bool(a_ok and a.get("n_nodes_in_process") == 1)
    pass_admitted = bool(a_ok and a.get("admitted_catalog"))
    pass_n = bool(a_ok and a.get("n_instruments", 0) >= 3)
    pass_anchor = bool(
        a_ok and any(a["per_symbol"][s]["fill_ts_anchor"].get("pass") for s in SYMBOLS)
    )
    pass_reports = bool(
        a_ok and any(a["per_symbol"][s]["fills_n"] > 0 for s in SYMBOLS)
    )

    overall = "PASS" if (
        a_ok and b_ok and bitwise_all and gate_all and pass_dispose
        and pass_one_node and pass_admitted and pass_n and pass_reports
    ) else "FAIL"
    topology = (
        "multi_instrument_single_node" if overall == "PASS" else "subprocess_per_instrument"
    )

    payload = {
        "experiment": "INFR-014",
        "wp": "WP5",
        "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "outcome": overall,
        "batch_topology": topology,
        "path_a": a if a_ok else {"error": a_err},
        "path_b": b if b_ok else {"error": b_err},
        "a_vs_b_identity": a_vs_b,
        "criteria": {
            "dispose_on_completion_false": pass_dispose,
            "one_node_per_process": pass_one_node,
            "reports_nonempty": pass_reports,
            "a_vs_b_bitwise_canonical": bitwise_all,
            "estimand_v2_blocking_pass_all_cells": gate_all,
            "admitted_catalog_btc_eth_sol": pass_admitted,
            "fill_ts_anchor_l29": pass_anchor,
            "n_instruments_ge_3": pass_n,
            "note": (
                "PASS → XENA batch may use multi-instrument single-node. "
                "FAIL → subprocess-per-cell (L-31)."
            ),
        },
        "deviations": [],  # filled only if intentional amendments remain
    }
    out_path = RESULTS / "s1_smoke.json"
    out_path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"[S1] outcome={overall} topology={topology} bitwise_AvsB={bitwise_all} gate={gate_all}", flush=True)
    print(f"  → {out_path}", flush=True)
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
