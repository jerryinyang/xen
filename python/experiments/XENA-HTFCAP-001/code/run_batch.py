#!/usr/bin/env python3
"""XENA-HTFCAP-001 BacktestNode batch runner — contract v1 emissions.

Topology (design §5 + INFR-014 S1):
  multi_instrument_single_node — one BacktestNode / process, BTC+SOL+ETH strategies
  for a shared parameter cell (filter × vol_thr × adx_min × H).
  dispose_on_completion=False (L-30); one node per process (L-31).

Per candidate: emission contract v1 under
  data/nautilus_runs/XENA-HTFCAP-001/<candidate_id>/
plus XENA-facing positions.parquet + cis_trades.parquet (with finite SlPrice)
written alongside in a sibling ``xena/`` subdir so estimand gate still sees
pure Nautilus v1 (positions.parquet absent at emission root).

Usage (from python/):
  uv run python experiments/XENA-HTFCAP-001/code/build_universe.py
  uv run python experiments/XENA-HTFCAP-001/code/run_batch.py --smoke
  uv run python experiments/XENA-HTFCAP-001/code/run_batch.py --all
  uv run python experiments/XENA-HTFCAP-001/code/run_batch.py --candidate BTCUSDT__DI_VOL_HI__v1.25__adxna__H16

Does NOT run search or final gate (operator-gated).
"""
from __future__ import annotations

import argparse
import json
import platform as _platform
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import polars as pl

CODE = Path(__file__).resolve().parent
EXP = CODE.parent
ROOT = EXP.parents[1]  # python/
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(CODE))

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

from xen.nautilus.adjudication_shim import positions_ledger_to_cis_trades  # noqa: E402
from xen.nautilus.catalog_fence import (  # noqa: E402
    FenceViolation,
    assert_within_fence,
    fence_attestation_payload,
    fenced_bar_query,
    load_fence_manifest,
)
from xen.nautilus.emission import write_emission_v1  # noqa: E402

UNIVERSE_ID = "XENA-HTFCAP-001"
CATALOG_PATH = REPO / "data" / "catalog"
# AMENDMENT-4 (operator 2026-07-18): TRAIN+TEST exploratory window. Majors' local catalog
# starts 2022-07-14 (trailing-4y cap); TRAIN-only (~1.4y) is below the LOW n_legs floor, so
# the window is extended across TRAIN+TEST up to holdout_start. HOLDOUT stays sealed.
BAND_TRAIN_TEST = "TRAIN_TEST"
MAJORS_START = datetime(2022, 7, 14, tzinfo=timezone.utc)
MAX_PARALLEL = 6  # fan-out pool width; bounded by RAM (~1.4-2 GB/worker) on a 16 GB / 10-core box


def _bands_for_window(fence, start: datetime, end: datetime) -> list[tuple[str, datetime, datetime]]:
    """Split [start,end] into sanctioned TRAIN/TEST sub-reads. HOLDOUT is refused (AMENDMENT-4).

    Holdout protection is absolute: any end past ``holdout_start`` raises, and each sub-window
    is validated by ``assert_within_fence`` in its own band (TEST caps at holdout_start).
    """
    te = fence.train_end_utc
    hs = fence.holdout_start_utc
    s = start if start.tzinfo else start.replace(tzinfo=timezone.utc)
    e = end if end.tzinfo else end.replace(tzinfo=timezone.utc)
    if e > hs:
        raise FenceViolation(
            f"AMENDMENT-4 extend-test: end {e} past holdout_start {hs} — HOLDOUT is sealed"
        )
    # TRAIN read is inclusive up to train_end; TEST starts one bar (1m) AFTER so the
    # boundary bar (== train_end) is not double-counted (strict-monotonic emission).
    # The TEST read also caps one bar BEFORE holdout_start: bar closes sit on the 1m grid
    # and the fenced query end is inclusive, so ending at hs would emit a mark whose
    # SourceCloseTime == holdout_start. AnalysisEndUtc (fence) == holdout_start and the
    # candidate-gate fence is strict (< AnalysisEndUtc), so that boundary mark is out of
    # domain. Cap at hs-1m → last emitted close = hs-1m, strictly pre-holdout.
    hs_read_cap = hs - timedelta(minutes=1)
    subs: list[tuple[str, datetime, datetime]] = []
    if s < te:
        subs.append(("TRAIN", s, min(e, te)))
    if e > te:
        subs.append(("TEST", max(s, te + timedelta(minutes=1)), min(e, hs_read_cap)))
    for band, ss, ee in subs:
        assert_within_fence(fence, ss, ee, band=band)  # per-band holdout-safe validation
    return subs
RUNS_ROOT = REPO / "data" / "nautilus_runs" / UNIVERSE_ID
MANIFEST_PATH = RUNS_ROOT / "universe_manifest.json"
RESULTS = EXP / "results"
CATALOG_VERSION = "INFR-011-A4-2026-07-16"

TRADE_SIZE = {"BTCUSDT": "0.01", "ETHUSDT": "0.1", "SOLUSDT": "1"}

# Smoke: short TRAIN window (still inside fence)
SMOKE_START = datetime(2023, 6, 1, tzinfo=timezone.utc)
SMOKE_END = datetime(2023, 8, 1, tzinfo=timezone.utc)


def _pandas_to_polars(df: Any) -> pl.DataFrame:
    if df is None or len(df) == 0:
        return pl.DataFrame()
    return pl.from_pandas(df.reset_index() if hasattr(df, "reset_index") else df)


def load_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(
            f"missing {MANIFEST_PATH} — run build_universe.py first"
        )
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def bar_marks_for(
    symbol: str,
    fence,
    start: datetime,
    end: datetime,
    band: str = "TRAIN",
) -> pl.DataFrame:
    catalog = ParquetDataCatalog(str(CATALOG_PATH))
    bar_types = [f"{symbol}-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL"]
    if band == BAND_TRAIN_TEST:
        bars = []
        for sub_band, ss, ee in _bands_for_window(fence, start, end):
            bars.extend(
                fenced_bar_query(catalog, bar_types, start=ss, end=ee,
                                 band=sub_band, manifest=fence)
            )
    else:
        bars = fenced_bar_query(
            catalog, bar_types, start=start, end=end, band=band, manifest=fence,
        )
    if not bars:
        return pl.DataFrame(
            schema={
                "SourceCloseTime": pl.Datetime("ns"),
                "RealOpen": pl.Float64,
                "RealHigh": pl.Float64,
                "RealLow": pl.Float64,
                "RealClose": pl.Float64,
                "Volume": pl.Float64,
            }
        )
    return (
        pl.DataFrame(
            {
                "SourceCloseTime": [b.ts_event for b in bars],
                "RealOpen": [float(b.open) for b in bars],
                "RealHigh": [float(b.high) for b in bars],
                "RealLow": [float(b.low) for b in bars],
                "RealClose": [float(b.close) for b in bars],
                "Volume": [float(b.volume) for b in bars],
            }
        )
        .with_columns(pl.from_epoch("SourceCloseTime", time_unit="ns").alias("SourceCloseTime"))
        .sort("SourceCloseTime")
    )


def _filter_instr(df: pl.DataFrame, iid: str) -> pl.DataFrame:
    if df is None or df.height == 0 or "instrument_id" not in df.columns:
        return df if df is not None else pl.DataFrame()
    return df.filter(pl.col("instrument_id").cast(pl.Utf8) == iid)


def strategy_importable(cell: dict[str, Any]) -> ImportableStrategyConfig:
    symbol = cell["symbol"]
    iid = cell["instrument_id"]
    return ImportableStrategyConfig(
        strategy_path="htfcap_strategy:HtfCapStrategy",
        config_path="htfcap_strategy:HtfCapConfig",
        config={
            "instrument_id": iid,
            "bar_type": f"{iid}-1-MINUTE-LAST-EXTERNAL",
            "trade_size": TRADE_SIZE[symbol],
            "filter_model": cell["filter_model"],
            "vol_thr": float(cell["vol_thr"]),
            "adx_min": float(cell["adx_min"] or 0.0),
            "hold_bars": int(cell["hold_bars"]),
            "candidate_id": cell["candidate_id"],
        },
    )


def param_key(cell: dict[str, Any]) -> tuple:
    return (
        cell["filter_model"],
        float(cell["vol_thr"]),
        None if cell["adx_min"] is None else float(cell["adx_min"]),
        int(cell["hold_bars"]),
    )


def group_param_cells(candidates: list[dict[str, Any]]) -> dict[tuple, list[dict]]:
    groups: dict[tuple, list[dict]] = {}
    for c in candidates:
        groups.setdefault(param_key(c), []).append(c)
    return groups


LTF_NS = 15 * 60_000_000_000
NS_PER_MIN = 60_000_000_000


def _dir_from_entry(v: object) -> int:
    s = str(v).upper()
    return 1 if "BUY" in s else (-1 if "SELL" in s else 0)


def anchor_ledger_open_to_open(
    ledger: pl.DataFrame,
    bar_marks: pl.DataFrame,
    leg_sl_records: list,
    hold_bars: int,
) -> pl.DataFrame:
    """L-29: rewrite ledger open/close prices+times to 15m RealOpen (open-to-open).

    Nautilus L1 bar matching fills market orders at bar close (VAL-008 same). The
    schedule/causality remain engine-driven; here the ledger's ``avg_px_open``/
    ``avg_px_close`` are re-anchored to catalog RealOpen and ``ts_opened``/``ts_closed``
    to the 15m grid (entry floored, exit = entry + H·15m). RealizedBps is NOT computed
    here — it is derived downstream by ``positions_ledger_to_cis_trades`` (canonical
    adjudication; QA-2 #13). Ledger sorted chronological to align with ``leg_sl_records``.
    """
    if ledger is None or ledger.height == 0 or bar_marks is None or bar_marks.height == 0:
        return ledger

    ledger = ledger.sort("ts_opened")
    marks = bar_marks.sort("SourceCloseTime")
    if marks.get_column("SourceCloseTime").dtype != pl.Datetime("ns"):
        marks = marks.with_columns(pl.col("SourceCloseTime").cast(pl.Datetime("ns")))
    m_ns = marks.get_column("SourceCloseTime").cast(pl.Int64).to_list()
    m_open = marks.get_column("RealOpen").to_list()
    open_by_close = {int(ns): float(o) for ns, o in zip(m_ns, m_open)}

    def real_open_at(open_ns: int) -> float | None:
        # 1m LAST bar closing at open_ns+1m opens at open_ns
        return open_by_close.get(int(open_ns) + NS_PER_MIN)

    for col in ("ts_opened", "ts_closed"):
        if col in ledger.columns and ledger.get_column(col).dtype != pl.Datetime("ns"):
            ledger = ledger.with_columns(pl.col(col).cast(pl.Datetime("ns")))
    open_ns_list = ledger.get_column("ts_opened").cast(pl.Int64).to_list()
    close_ns_list = (
        ledger.get_column("ts_closed").cast(pl.Int64).to_list()
        if "ts_closed" in ledger.columns
        else [None] * ledger.height
    )
    entries = (
        ledger.get_column("entry").to_list()
        if "entry" in ledger.columns
        else [None] * ledger.height
    )
    px_open0 = (
        ledger.get_column("avg_px_open").to_list()
        if "avg_px_open" in ledger.columns
        else [None] * ledger.height
    )
    px_close0 = (
        ledger.get_column("avg_px_close").to_list()
        if "avg_px_close" in ledger.columns
        else [None] * ledger.height
    )
    atrs = [float(r.atr_htf) for r in leg_sl_records]
    while len(atrs) < len(open_ns_list):
        atrs.append(float("nan"))

    new_to, new_tc, new_po, new_pc, new_sl = [], [], [], [], []
    for i, ens in enumerate(open_ns_list):
        e_open = (int(ens) // LTF_NS) * LTF_NS
        x_open = e_open + int(hold_bars) * LTF_NS
        ep = real_open_at(e_open)
        xp = real_open_at(x_open)
        side = _dir_from_entry(entries[i]) or 1
        atr = atrs[i]
        if ep is None or ep <= 0:
            # fallback: keep engine values (as int ns)
            new_to.append(int(ens))
            new_tc.append(close_ns_list[i])
            po = float(px_open0[i]) if px_open0[i] is not None else float("nan")
            new_po.append(po)
            new_pc.append(float(px_close0[i]) if px_close0[i] is not None else None)
            new_sl.append(po - side * 1.0 * atr if atr == atr else float("nan"))
            continue
        new_to.append(e_open)
        new_tc.append(x_open if xp is not None else None)
        new_po.append(float(ep))
        new_pc.append(float(xp) if xp is not None else None)
        new_sl.append(ep - side * 1.0 * atr if atr == atr and atr > 0 else float("nan"))

    return ledger.with_columns(
        pl.Series("ts_opened", new_to, dtype=pl.Int64).cast(pl.Datetime("ns")),
        pl.Series("ts_closed", new_tc, dtype=pl.Int64).cast(pl.Datetime("ns")),
        pl.Series("avg_px_open", new_po, dtype=pl.Float64),
        pl.Series("avg_px_close", new_pc, dtype=pl.Float64),
        pl.Series("SlPrice", new_sl, dtype=pl.Float64),
    )


def attach_sl_to_cis(cis: pl.DataFrame, ledger: pl.DataFrame) -> pl.DataFrame:
    """Copy row-aligned SlPrice from the anchored ledger onto shim cis legs."""
    if cis is None or cis.height == 0:
        if cis is not None and "SlPrice" not in cis.columns:
            return cis.with_columns(pl.lit(None).cast(pl.Float64).alias("SlPrice"))
        return cis
    if "SlPrice" in ledger.columns:
        sls = ledger.get_column("SlPrice").to_list()[: cis.height]
        sls = sls + [float("nan")] * (cis.height - len(sls))
        return cis.with_columns(pl.Series("SlPrice", sls, dtype=pl.Float64))
    return cis.with_columns(pl.lit(None).cast(pl.Float64).alias("SlPrice"))


def materialize_xena(
    emission_dir: Path,
    positions_ledger: pl.DataFrame,
    bar_marks: pl.DataFrame,
    cis: pl.DataFrame,
    *,
    analysis_end_utc: str,
    candidate_id: str,
    symbol: str,
) -> Path:
    """Write XENA ingest layout under emission_dir/xena/ (positions + cis + SlPrice)."""
    xena_dir = emission_dir / "xena"
    xena_dir.mkdir(parents=True, exist_ok=True)
    # positions.parquet = mark grid
    pos = bar_marks.select(
        [c for c in ("SourceCloseTime", "RealOpen", "RealHigh", "RealLow", "RealClose")
         if c in bar_marks.columns]
    )
    pos.write_parquet(xena_dir / "positions.parquet")
    # ensure required cis cols
    if "SlPrice" not in cis.columns:
        cis = cis.with_columns(pl.lit(float("nan")).alias("SlPrice"))
    cis.write_parquet(xena_dir / "cis_trades.parquet")
    meta = {
        "candidate_id": candidate_id,
        "symbol": symbol,
        "AnalysisEndUtc": analysis_end_utc,
        "analysis_end_utc": analysis_end_utc,
        "emission_root": str(emission_dir),
        "sl_price_contract": "synthetic finite EntryFill - side * HTF_ATR14",
        "fill_price_contract": "open_to_open_RealOpen_anchor_L29",
    }
    (xena_dir / "run_metadata.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )
    return xena_dir


def run_param_group(
    cells: list[dict[str, Any]],
    fence,
    *,
    start: datetime,
    end: datetime,
    band: str = "TRAIN",
) -> list[dict[str, Any]]:
    """One BacktestNode, multi-instrument (all symbols in ``cells``), L-30/L-31."""
    if band == BAND_TRAIN_TEST:
        _bands_for_window(fence, start, end)  # AMENDMENT-4: TRAIN+TEST span, holdout-refused
    else:
        assert_within_fence(fence, start, end, band=band)
    symbols = sorted({c["symbol"] for c in cells})
    strategies = [strategy_importable(c) for c in cells]
    data_cfgs = [
        BacktestDataConfig(
            catalog_path=str(CATALOG_PATH),
            data_cls=Bar,
            instrument_id=f"{sym}-LINEAR.BYBIT",
            start_time=start.isoformat(),
            end_time=end.isoformat(),
        )
        for sym in symbols
    ]
    run_config = BacktestRunConfig(
        dispose_on_completion=False,  # L-30
        engine=BacktestEngineConfig(
            logging=LoggingConfig(log_level="ERROR", log_colors=False, print_config=False),
            strategies=strategies,
        ),
        venues=[
            BacktestVenueConfig(
                name="BYBIT",
                oms_type="HEDGING",  # D3 (QA-2 #11): greedy back-to-back legs need
                # distinct position ids so leg_{k+1} opens where leg_k closes (no netting).
                account_type="MARGIN",
                base_currency="USDT",
                starting_balances=["1000000 USDT"],
                book_type="L1_MBP",
            )
        ],
        data=data_cfgs,
    )
    # L-31: exactly one node in this process
    node = BacktestNode(configs=[run_config])
    results = node.run()
    engine = node.get_engine(run_config.id)
    fills_all = _pandas_to_polars(engine.trader.generate_order_fills_report()) if engine else pl.DataFrame()
    orders_all = _pandas_to_polars(engine.trader.generate_orders_report()) if engine else pl.DataFrame()
    positions_all = (
        _pandas_to_polars(engine.trader.generate_positions_report()) if engine else pl.DataFrame()
    )

    # Collect SlPrice records from strategy instances
    sl_by_candidate: dict[str, list] = {c["candidate_id"]: [] for c in cells}
    if engine is not None:
        for strat in engine.trader.strategies():
            cid = getattr(getattr(strat, "config", None), "candidate_id", None)
            recs = getattr(strat, "leg_sl_records", None)
            if cid and recs is not None:
                sl_by_candidate[cid] = list(recs)

    node.dispose()

    fence_payload = fence_attestation_payload(fence)
    analysis_end = fence_payload["analysis_end_utc"]
    summaries: list[dict[str, Any]] = []

    for cell in cells:
        symbol = cell["symbol"]
        iid = cell["instrument_id"]
        cid = cell["candidate_id"]
        marks = bar_marks_for(symbol, fence, start, end, band=band)
        fills = _filter_instr(fills_all, iid)
        orders = _filter_instr(orders_all, iid)
        positions = _filter_instr(positions_all, iid)

        # L-29 open-to-open RealOpen anchor on the LEDGER (design §2–§3); RealizedBps is
        # then shim-derived from the anchored ledger (QA-2 #13 — no local accounting).
        positions = anchor_ledger_open_to_open(
            positions, marks, sl_by_candidate.get(cid, []), int(cell["hold_bars"])
        )
        cis = positions_ledger_to_cis_trades(positions)
        cis = attach_sl_to_cis(cis, positions)

        run_dir = RUNS_ROOT / cid
        run_cfg = {
            "experiment": UNIVERSE_ID,
            "candidate_id": cid,
            "symbol": symbol,
            "filter_model": cell["filter_model"],
            "vol_thr": cell["vol_thr"],
            "adx_min": cell["adx_min"],
            "hold_bars": cell["hold_bars"],
            "window_start_utc": start.isoformat(),
            "window_end_utc": end.isoformat(),
            "band": band,
            "venue": "BYBIT",
            "oms_type": "HEDGING",
            "book_type": "L1_MBP",
            "dispose_on_completion": False,
            "topology": "multi_instrument_single_node",
            "n_instruments_engine": len(symbols),
            "cost_stack": cell.get("cost_stack"),
            "cost_bps_manifest": cell.get("cost_bps"),
        }
        write_emission_v1(
            run_dir,
            fills=fills,
            orders=orders,
            positions_ledger=positions,
            bar_marks=marks,
            instrument_id_map={symbol: iid},
            run_config=run_cfg,
            catalog_version=CATALOG_VERSION,
            catalog_path=str(CATALOG_PATH),
            fence=fence_payload,
            nautilus_version=nautilus_trader.__version__,
            platform=_platform.platform(),
            extra_metadata={
                "symbol": symbol,
                "candidate_id": cid,
                "role": cell.get("role"),
            },
        )
        xena_dir = materialize_xena(
            run_dir,
            positions,
            marks,
            cis,
            analysis_end_utc=analysis_end,
            candidate_id=cid,
            symbol=symbol,
        )
        # Persist SlPrice sidecar for audit
        sl_rows = [
            {
                "entry_ts_ns": r.entry_ts_ns,
                "side": r.side,
                "entry_px": r.entry_px,
                "sl_price": r.sl_price,
                "atr_htf": r.atr_htf,
                "hold_bars": r.hold_bars,
            }
            for r in sl_by_candidate.get(cid, [])
        ]
        (run_dir / "sl_price_records.json").write_text(
            json.dumps(sl_rows, indent=2) + "\n", encoding="utf-8"
        )
        summary = {
            "candidate_id": cid,
            "symbol": symbol,
            "run_dir": str(run_dir),
            "xena_dir": str(xena_dir),
            "n_fills": fills.height,
            "n_positions": positions.height,
            "n_cis": cis.height,
            "n_sl_records": len(sl_rows),
            "iterations": results[0].iterations if results else None,
        }
        print(
            f"EMIT {cid}: positions={positions.height} fills={fills.height} "
            f"sl={len(sl_rows)}"
        )
        summaries.append(summary)
    return summaries


def rewrite_manifest_xena_paths(
    manifest: dict[str, Any], emitted_ids: set[str]
) -> None:
    """Point emitted candidates' run_dir at xena/ for xen.xena.ingest.

    Non-emitted cells keep run_dir = candidate_id (emission root placeholder).
    """
    for c in manifest["candidates"]:
        cid = c["candidate_id"]
        c["emission_dir"] = cid
        if cid in emitted_ids and (RUNS_ROOT / cid / "xena").exists():
            c["run_dir"] = f"{cid}/xena"
            c["emitted"] = True
        else:
            c.setdefault("emitted", False)
    text = json.dumps(manifest, indent=2) + "\n"
    MANIFEST_PATH.write_text(text, encoding="utf-8")
    (RESULTS / "universe_manifest.json").write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="XENA-HTFCAP-001 batch runner")
    parser.add_argument("--smoke", action="store_true", help="short TRAIN window, one param cell")
    parser.add_argument("--all", action="store_true", help="full TRAIN, all 108 cells")
    parser.add_argument("--candidate", type=str, default=None, help="single candidate_id")
    parser.add_argument(
        "--band",
        type=str,
        default="TRAIN",
        choices=("TRAIN",),
        help="catalog band (TRAIN only at implementation; TEST is operator-gated)",
    )
    parser.add_argument(
        "--extend-test",
        action="store_true",
        help="AMENDMENT-4 (operator 2026-07-18): extend --all window across TRAIN+TEST "
        "(2022-07-14 → holdout_start) — EXPLORATORY, no reserved OOS; holdout stays sealed",
    )
    parser.add_argument(
        "--param-group-index",
        type=int,
        default=None,
        help="fan-out worker: run ONLY the Nth sorted param group (one node/process, L-31)",
    )
    args = parser.parse_args()
    if not (args.smoke or args.all or args.candidate or args.param_group_index is not None):
        parser.error("specify --smoke, --all, --candidate, or --param-group-index")
    if args.extend_test and not (args.all or args.param_group_index is not None):
        parser.error("--extend-test applies to --all / --param-group-index only")

    fence = load_fence_manifest()
    manifest = load_manifest()
    candidates = manifest["candidates"]

    if args.smoke:
        # One param cell × all 3 symbols (or whichever present)
        key = ("DI×VOL_HI", 1.25, None, 16)
        groups = group_param_cells(candidates)
        cells = groups.get(key)
        if not cells:
            # fallback first group
            cells = next(iter(groups.values()))
        start, end = SMOKE_START, SMOKE_END
        print(f"SMOKE param={param_key(cells[0])} symbols={[c['symbol'] for c in cells]}")
        summaries = run_param_group(cells, fence, start=start, end=end, band=args.band)
    elif args.candidate:
        cells = [c for c in candidates if c["candidate_id"] == args.candidate]
        if not cells:
            raise SystemExit(f"candidate not in manifest: {args.candidate}")
        start, end = fence.analysis_start_utc, fence.train_end_utc
        summaries = run_param_group(cells, fence, start=start, end=end, band=args.band)
    elif args.param_group_index is not None:
        # fan-out worker: exactly ONE param group → one BacktestNode (L-31 one node/process)
        if args.extend_test:
            start, end, run_band = MAJORS_START, fence.holdout_start_utc, BAND_TRAIN_TEST
        else:
            start, end, run_band = fence.analysis_start_utc, fence.train_end_utc, args.band
        groups = sorted(group_param_cells(candidates).items(), key=lambda x: str(x[0]))
        if not 0 <= args.param_group_index < len(groups):
            raise SystemExit(f"param-group-index out of range 0..{len(groups) - 1}")
        pk, cells = groups[args.param_group_index]
        print(f"GROUP {args.param_group_index + 1}/{len(groups)} {pk} n_sym={len(cells)}")
        summaries = run_param_group(cells, fence, start=start, end=end, band=run_band)
        # per-group log only (driver merges); no shared-file append, no manifest rewrite here
        glog_dir = RESULTS / "_group_logs"
        glog_dir.mkdir(parents=True, exist_ok=True)
        with (glog_dir / f"group_{args.param_group_index}.jsonl").open("w", encoding="utf-8") as f:
            for s in summaries:
                s["finished_utc"] = datetime.now(timezone.utc).isoformat()
                f.write(json.dumps(s, default=str) + "\n")
        print(f"GROUP {args.param_group_index} wrote {len(summaries)} cells")
        return 0
    else:
        # --all DRIVER: fan out one subprocess per param group, run a BOUNDED PARALLEL pool.
        # L-31 = one node per PROCESS (not one process total): separate processes each own
        # their Rust logger, so concurrency is safe. In-process looping panics on the 2nd node.
        groups = sorted(group_param_cells(candidates).items(), key=lambda x: str(x[0]))
        n_groups = len(groups)
        max_par = min(MAX_PARALLEL, n_groups)
        glog_dir = RESULTS / "_group_logs"
        glog_dir.mkdir(parents=True, exist_ok=True)
        for p in glog_dir.glob("group_*.jsonl"):
            p.unlink()
        worker = [sys.executable, str(Path(__file__).resolve())]
        extra = (["--extend-test"] if args.extend_test else [])
        print(f"FAN-OUT --all: {n_groups} groups, {max_par}-wide parallel"
              + (" (EXTEND-TEST AMENDMENT-4: TRAIN+TEST, holdout sealed)" if args.extend_test else ""),
              flush=True)
        running: dict[int, tuple[int, subprocess.Popen]] = {}
        nxt, failed = 0, []
        while nxt < n_groups or running:
            while len(running) < max_par and nxt < n_groups:
                proc = subprocess.Popen(worker + ["--param-group-index", str(nxt)] + extra)
                running[proc.pid] = (nxt, proc)
                print(f"== spawned group {nxt + 1}/{n_groups} (pid {proc.pid}) ==", flush=True)
                nxt += 1
            done = [(pid, gi, pr) for pid, (gi, pr) in running.items() if pr.poll() is not None]
            for pid, gi, pr in done:
                rc = pr.returncode
                if rc != 0:
                    failed.append((gi, rc))
                print(f"== group {gi + 1}/{n_groups} finished rc={rc} "
                      f"({nxt - len(running) + len(done)}/{n_groups} launched) ==", flush=True)
                running.pop(pid)
            if not done:
                time.sleep(5)
        # merge per-group logs → shared batch_run_log; rewrite manifest once (no races)
        RESULTS.mkdir(parents=True, exist_ok=True)
        all_summaries = []
        for gf in sorted(glog_dir.glob("group_*.jsonl")):
            all_summaries.extend(json.loads(ln) for ln in gf.read_text().splitlines() if ln.strip())
        with (RESULTS / "batch_run_log.jsonl").open("a", encoding="utf-8") as f:
            for s in all_summaries:
                f.write(json.dumps(s, default=str) + "\n")
        rewrite_manifest_xena_paths(manifest, {s["candidate_id"] for s in all_summaries})
        print(f"FAN-OUT complete: {n_groups - len(failed)}/{n_groups} groups ok, "
              f"{len(all_summaries)} cells emitted; failures={failed}")
        print("NOTE: search / gate_universe / final_gate NOT run (operator-gated).")
        return 1 if failed else 0

    RESULTS.mkdir(parents=True, exist_ok=True)
    log_path = RESULTS / "batch_run_log.jsonl"
    with log_path.open("a", encoding="utf-8") as f:
        for s in summaries:
            s["finished_utc"] = datetime.now(timezone.utc).isoformat()
            f.write(json.dumps(s, default=str) + "\n")

    emitted_ids = {s["candidate_id"] for s in summaries}
    rewrite_manifest_xena_paths(manifest, emitted_ids)
    print(f"LOG {log_path}  n={len(summaries)}")
    print("NOTE: search / gate_universe / final_gate NOT run (operator-gated).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
