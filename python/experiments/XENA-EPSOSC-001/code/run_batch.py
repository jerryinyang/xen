#!/usr/bin/env python3
"""XENA-EPSOSC-001 BacktestNode batch runner — contract v1 emissions.

Topology (design §5 + INFR-014 S1):
  multi_instrument_single_node — one BacktestNode / process, all symbols for a
  shared parameter cell (object × ltf × W × k × clear × side).
  dispose_on_completion=False (L-30); one node per process (L-31).

Per candidate: emission contract v1 under
  data/nautilus_runs/XENA-EPSOSC-001/<candidate_id>/
plus XENA-facing positions.parquet + cis_trades.parquet (with finite SlPrice)
written under ``xena/`` so estimand gate still sees pure Nautilus v1 at root.

Episode grouping: adjudication shim only (L-16 episode-native) — no local
accounting. Segment-end open legs → Censored via shim; censored-fraction
disclosed per cell in the batch log.

Usage (from python/):
  uv run python experiments/XENA-EPSOSC-001/code/build_universe.py --reuse-spdr-membership
  uv run python experiments/XENA-EPSOSC-001/code/run_batch.py --smoke
  uv run python experiments/XENA-EPSOSC-001/code/run_batch.py --all
  uv run python experiments/XENA-EPSOSC-001/code/run_batch.py --candidate <id>

Does NOT run search or final gate (operator-gated).
"""
from __future__ import annotations

import argparse
import json
import platform as _platform
import subprocess
import sys
from datetime import datetime, timezone
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
    assert_within_fence,
    fence_attestation_payload,
    fenced_bar_query,
    load_fence_manifest,
)
from xen.nautilus.emission import write_emission_v1  # noqa: E402

UNIVERSE_ID = "XENA-EPSOSC-001"
CATALOG_PATH = REPO / "data" / "catalog"
RUNS_ROOT = REPO / "data" / "nautilus_runs" / UNIVERSE_ID
MANIFEST_PATH = RUNS_ROOT / "universe_manifest.json"
MEMBERSHIP_PATH = RUNS_ROOT / "membership.parquet"
RESULTS = EXP / "results"
CATALOG_VERSION = "INFR-011-A4-2026-07-16"

# Smoke: short TRAIN window (still inside fence; post vol-mass start ~2022-07)
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


def trade_size(manifest: dict[str, Any], symbol: str) -> str:
    ts = (manifest.get("trade_sizes") or {}).get(symbol)
    if ts:
        return str(ts)
    if "1000" in symbol or "SHIB" in symbol:
        return "100"
    return "10"


def bar_marks_for(
    symbol: str,
    fence,
    start: datetime,
    end: datetime,
    band: str = "TRAIN",
) -> pl.DataFrame:
    catalog = ParquetDataCatalog(str(CATALOG_PATH))
    bars = fenced_bar_query(
        catalog,
        [f"{symbol}-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL"],
        start=start,
        end=end,
        band=band,
        manifest=fence,
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


def strategy_importable(
    cell: dict[str, Any], manifest: dict[str, Any]
) -> ImportableStrategyConfig:
    symbol = cell["symbol"]
    iid = cell["instrument_id"]
    mem = str(MEMBERSHIP_PATH)
    return ImportableStrategyConfig(
        strategy_path="epsosc_strategy:EpsoscStrategy",
        config_path="epsosc_strategy:EpsoscConfig",
        config={
            "instrument_id": iid,
            "bar_type": f"{iid}-1-MINUTE-LAST-EXTERNAL",
            "trade_size": trade_size(manifest, symbol),
            "object_type": cell["object_type"],
            "ltf_minutes": int(cell["ltf_minutes"]),
            "w": int(cell["w"]),
            "k": float(cell["k"]),
            "clear_policy": cell["clear_policy"],
            "side_mode": cell["side_mode"],
            "membership_path": mem,
            "symbol": symbol,
            "candidate_id": cell["candidate_id"],
        },
    )


def param_key(cell: dict[str, Any]) -> tuple:
    return (
        cell["object_type"],
        int(cell["ltf_minutes"]),
        int(cell["w"]),
        float(cell["k"]),
        cell["clear_policy"],
        cell["side_mode"],
    )


def group_param_cells(candidates: list[dict[str, Any]]) -> dict[tuple, list[dict]]:
    groups: dict[tuple, list[dict]] = {}
    for c in candidates:
        groups.setdefault(param_key(c), []).append(c)
    return groups


def attach_sl_price(
    positions_ledger: pl.DataFrame,
    leg_sl_records: list,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Attach synthetic finite SlPrice to ledger + cis (chronological leg order)."""
    if positions_ledger is None or positions_ledger.height == 0:
        empty = positions_ledger if positions_ledger is not None else pl.DataFrame()
        cis_empty = (
            positions_ledger_to_cis_trades(empty) if empty.height else pl.DataFrame()
        )
        return empty, cis_empty

    cis = positions_ledger_to_cis_trades(positions_ledger)
    sl_by_order = [float(r.sl_price) for r in leg_sl_records]
    if cis.height:
        n = min(cis.height, len(sl_by_order))
        sls = sl_by_order[:n] + [float("nan")] * (cis.height - n)
        cis = cis.with_columns(pl.Series("SlPrice", sls, dtype=pl.Float64))
    else:
        cis = cis.with_columns(pl.lit(None).cast(pl.Float64).alias("SlPrice"))

    n_pos = positions_ledger.height
    sl_pos = sl_by_order[:n_pos] + [float("nan")] * max(0, n_pos - len(sl_by_order))
    positions_ledger = positions_ledger.with_columns(
        pl.Series("SlPrice", sl_pos, dtype=pl.Float64)
    )
    return positions_ledger, cis


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
    """Write XENA ingest layout under emission_dir/xena/."""
    xena_dir = emission_dir / "xena"
    xena_dir.mkdir(parents=True, exist_ok=True)
    pos = bar_marks.select(
        [
            c
            for c in ("SourceCloseTime", "RealOpen", "RealHigh", "RealLow", "RealClose")
            if c in bar_marks.columns
        ]
    )
    pos.write_parquet(xena_dir / "positions.parquet")
    if "SlPrice" not in cis.columns:
        cis = cis.with_columns(pl.lit(float("nan")).alias("SlPrice"))
    cis.write_parquet(xena_dir / "cis_trades.parquet")
    meta = {
        "candidate_id": candidate_id,
        "symbol": symbol,
        "AnalysisEndUtc": analysis_end_utc,
        "analysis_end_utc": analysis_end_utc,
        "emission_root": str(emission_dir),
        "sl_price_contract": "synthetic finite EntryFill - side * k * ATR14[t-1]",
        "episode_grouping": "adjudication_shim L-16",
    }
    (xena_dir / "run_metadata.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )
    return xena_dir


def censored_fraction(cis: pl.DataFrame) -> dict[str, Any]:
    """Segment-end / fence censoring disclosure (design §3)."""
    if cis is None or cis.height == 0 or "Censored" not in cis.columns:
        return {
            "n_started": 0,
            "n_censored": 0,
            "censored_frac": 0.0,
            "censored_flag_gt20": False,
        }
    n = int(cis.height)
    n_c = int(cis.filter(pl.col("Censored").cast(pl.Boolean)).height)
    frac = float(n_c / n) if n else 0.0
    return {
        "n_started": n,
        "n_censored": n_c,
        "censored_frac": frac,
        "censored_flag_gt20": bool(frac > 0.20),
    }


def run_param_group(
    cells: list[dict[str, Any]],
    fence,
    manifest: dict[str, Any],
    *,
    start: datetime,
    end: datetime,
    band: str = "TRAIN",
) -> list[dict[str, Any]]:
    """One BacktestNode, multi-instrument (all symbols in ``cells``), L-30/L-31."""
    assert_within_fence(fence, start, end, band=band)
    if not MEMBERSHIP_PATH.exists():
        raise FileNotFoundError(f"missing {MEMBERSHIP_PATH} — run build_universe.py")

    symbols = sorted({c["symbol"] for c in cells})
    strategies = [strategy_importable(c, manifest) for c in cells]
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
                oms_type="NETTING",
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

    sl_by_candidate: dict[str, list] = {c["candidate_id"]: [] for c in cells}
    censored_open_by_cid: dict[str, int] = {}
    if engine is not None:
        for strat in engine.trader.strategies():
            cid = getattr(getattr(strat, "config", None), "candidate_id", None)
            recs = getattr(strat, "leg_sl_records", None)
            if cid and recs is not None:
                sl_by_candidate[cid] = list(recs)
            if cid:
                censored_open_by_cid[cid] = int(getattr(strat, "n_censored_open", 0))

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

        positions, cis = attach_sl_price(positions, sl_by_candidate.get(cid, []))
        cens = censored_fraction(cis)

        run_dir = RUNS_ROOT / cid
        run_cfg = {
            "experiment": UNIVERSE_ID,
            "candidate_id": cid,
            "symbol": symbol,
            "object_type": cell["object_type"],
            "ltf_minutes": cell["ltf_minutes"],
            "w": cell["w"],
            "k": cell["k"],
            "clear_policy": cell["clear_policy"],
            "side_mode": cell["side_mode"],
            "window_start_utc": start.isoformat(),
            "window_end_utc": end.isoformat(),
            "band": band,
            "venue": "BYBIT",
            "oms_type": "NETTING",
            "book_type": "L1_MBP",
            "dispose_on_completion": False,
            "topology": "multi_instrument_single_node",
            "n_instruments_engine": len(symbols),
            "cost_stack": cell.get("cost_stack"),
            "cost_bps_manifest": cell.get("cost_bps"),
            "lessons": ["L-30", "L-31", "L-16"],
            "segment_end_censoring": True,
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
                "censored_fraction": cens,
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
        sl_rows = [
            {
                "entry_ts_ns": r.entry_ts_ns,
                "side": r.side,
                "entry_px": r.entry_px,
                "sl_price": r.sl_price,
                "atr_ltf": r.atr_ltf,
                "k": r.k,
                "clear_policy": r.clear_policy,
                "w": r.w,
            }
            for r in sl_by_candidate.get(cid, [])
        ]
        (run_dir / "sl_price_records.json").write_text(
            json.dumps(sl_rows, indent=2) + "\n", encoding="utf-8"
        )
        (run_dir / "censoring.json").write_text(
            json.dumps(cens, indent=2) + "\n", encoding="utf-8"
        )
        summary = {
            "candidate_id": cid,
            "symbol": symbol,
            "role": cell.get("role"),
            "run_dir": str(run_dir),
            "xena_dir": str(xena_dir),
            "n_fills": fills.height,
            "n_positions": positions.height,
            "n_cis": cis.height,
            "n_sl_records": len(sl_rows),
            "n_censored_open_at_stop": censored_open_by_cid.get(cid, 0),
            **cens,
            "iterations": results[0].iterations if results else None,
        }
        flag = " FLAG>20%" if cens["censored_flag_gt20"] else ""
        print(
            f"EMIT {cid}: positions={positions.height} fills={fills.height} "
            f"sl={len(sl_rows)} censored_frac={cens['censored_frac']:.3f}{flag}"
        )
        summaries.append(summary)
    return summaries


def rewrite_manifest_xena_paths(
    manifest: dict[str, Any], emitted_ids: set[str]
) -> None:
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


def _already_emitted(cid: str) -> bool:
    """True if contract-v1 + xena cis exist for candidate."""
    d = RUNS_ROOT / cid
    return (d / "xena" / "cis_trades.parquet").exists() and (
        d / "positions_ledger.parquet"
    ).exists()


def _append_summaries(summaries: list[dict[str, Any]]) -> Path:
    RESULTS.mkdir(parents=True, exist_ok=True)
    log_path = RESULTS / "batch_run_log.jsonl"
    with log_path.open("a", encoding="utf-8") as f:
        for s in summaries:
            s = dict(s)
            s["finished_utc"] = datetime.now(timezone.utc).isoformat()
            f.write(json.dumps(s, default=str) + "\n")
    return log_path


def _write_censoring_from_disk() -> dict[str, Any]:
    """Rebuild aggregate censoring disclosure from per-cell censoring.json."""
    fracs: list[float] = []
    n_flag = 0
    for p in RUNS_ROOT.iterdir():
        if not p.is_dir():
            continue
        cj = p / "censoring.json"
        if not cj.exists():
            continue
        try:
            d = json.loads(cj.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        fracs.append(float(d.get("censored_frac") or 0.0))
        if d.get("censored_flag_gt20"):
            n_flag += 1
    cens_summary = {
        "n_cells": len(fracs),
        "n_censored_flag_gt20": n_flag,
        "mean_censored_frac": (sum(fracs) / len(fracs)) if fracs else 0.0,
        "note": (
            "episodes open at band/fence boundary are CENSORED; "
            ">20% flagged as clear-policy failure evidence (design §3)"
        ),
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "censoring_disclosure.json").write_text(
        json.dumps(cens_summary, indent=2) + "\n", encoding="utf-8"
    )
    return cens_summary


def _finalize_manifest() -> set[str]:
    """Mark all on-disk emissions in the universe manifest."""
    manifest = load_manifest()
    emitted = {
        c["candidate_id"]
        for c in manifest["candidates"]
        if _already_emitted(c["candidate_id"])
    }
    rewrite_manifest_xena_paths(manifest, emitted)
    return emitted


def _param_key_to_str(pk: tuple) -> str:
    return "|".join(str(x) for x in pk)


def _parse_param_key(s: str) -> tuple:
    """Parse ``object|ltf|w|k|clear|side`` from --group-key."""
    parts = s.split("|")
    if len(parts) != 6:
        raise ValueError(f"group-key must be 6 fields: {s!r}")
    return (
        parts[0],
        int(parts[1]),
        int(parts[2]),
        float(parts[3]),
        parts[4],
        parts[5],
    )


def _run_all_subprocess(
    *,
    binding_only: bool,
    band: str,
    skip_emitted: bool,
) -> int:
    """L-31: one BacktestNode per OS process — subprocess fan-out over param groups."""
    manifest = load_manifest()
    candidates = manifest["candidates"]
    if binding_only:
        candidates = [c for c in candidates if c.get("role") == "binding"]
    groups = group_param_cells(candidates)
    keys = sorted(groups.keys(), key=lambda x: str(x))
    n_ok = 0
    n_skip = 0
    n_fail = 0
    for i, pk in enumerate(keys):
        cells = groups[pk]
        if skip_emitted and all(_already_emitted(c["candidate_id"]) for c in cells):
            print(f"SKIP GROUP {i + 1}/{len(keys)} {pk} (all {len(cells)} emitted)")
            n_skip += 1
            continue
        # partial group: still run; run_param_group will overwrite cells
        if skip_emitted:
            pending = [c for c in cells if not _already_emitted(c["candidate_id"])]
            if not pending:
                n_skip += 1
                continue
            # if some exist, re-run whole param group (multi-instrument node needs all)
            # — cheaper correctness than splitting
        key_s = _param_key_to_str(pk)
        cmd = [
            sys.executable,
            str(CODE / "run_batch.py"),
            "--group-key",
            key_s,
            "--band",
            band,
        ]
        if binding_only:
            cmd.append("--binding-only")
        print(f"SUBPROCESS GROUP {i + 1}/{len(keys)} {pk} n_sym={len(cells)}")
        proc = subprocess.run(cmd, cwd=str(ROOT), check=False)
        if proc.returncode != 0:
            print(f"FAIL GROUP {i + 1}/{len(keys)} rc={proc.returncode}")
            n_fail += 1
            # continue remaining groups (resume-friendly)
            continue
        n_ok += 1

    emitted = _finalize_manifest()
    cens = _write_censoring_from_disk()
    print(
        f"DONE subprocess fan-out: ok={n_ok} skip={n_skip} fail={n_fail} "
        f"emitted_on_disk={len(emitted)}"
    )
    print(f"CENSORING {cens}")
    print("NOTE: search / gate_universe / final_gate NOT run (operator-gated).")
    return 1 if n_fail else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="XENA-EPSOSC-001 batch runner")
    parser.add_argument("--smoke", action="store_true", help="short TRAIN window, one param cell")
    parser.add_argument("--all", action="store_true", help="full TRAIN, all cells")
    parser.add_argument("--candidate", type=str, default=None, help="single candidate_id")
    parser.add_argument(
        "--group-key",
        type=str,
        default=None,
        help="single param group in THIS process (L-31 worker): object|ltf|w|k|clear|side",
    )
    parser.add_argument(
        "--band",
        type=str,
        default="TRAIN",
        choices=("TRAIN",),
        help="catalog band (TRAIN only at implementation; TEST is operator-gated)",
    )
    parser.add_argument(
        "--binding-only",
        action="store_true",
        help="skip STRETCH disclosure cells",
    )
    parser.add_argument(
        "--skip-emitted",
        action="store_true",
        help="with --all: skip param groups already fully on disk (resume)",
    )
    args = parser.parse_args()
    if not (args.smoke or args.all or args.candidate or args.group_key):
        parser.error("specify --smoke, --all, --candidate, or --group-key")

    fence = load_fence_manifest()
    manifest = load_manifest()
    candidates = manifest["candidates"]
    if args.binding_only:
        candidates = [c for c in candidates if c.get("role") == "binding"]

    # --all: orchestrate subprocesses (never a second BacktestNode in one process)
    if args.all and not args.group_key:
        return _run_all_subprocess(
            binding_only=args.binding_only,
            band=args.band,
            skip_emitted=args.skip_emitted,
        )

    if args.smoke:
        key = ("VOLARM", 15, 96, 2.5, "RET_ANCHOR", "SHORT_ONLY")
        groups = group_param_cells(candidates)
        cells = groups.get(key)
        if not cells:
            cells = next(iter(groups.values()))
        cells = cells[:3]
        start, end = SMOKE_START, SMOKE_END
        print(f"SMOKE param={param_key(cells[0])} symbols={[c['symbol'] for c in cells]}")
        summaries = run_param_group(
            cells, fence, manifest, start=start, end=end, band=args.band
        )
    elif args.candidate:
        cells = [c for c in candidates if c["candidate_id"] == args.candidate]
        if not cells:
            raise SystemExit(f"candidate not in manifest: {args.candidate}")
        start, end = fence.analysis_start_utc, fence.train_end_utc
        summaries = run_param_group(
            cells, fence, manifest, start=start, end=end, band=args.band
        )
    else:
        # --group-key worker: exactly one BacktestNode in this process (L-31)
        pk = _parse_param_key(args.group_key)
        groups = group_param_cells(candidates)
        cells = groups.get(pk)
        if not cells:
            raise SystemExit(f"group-key not in manifest: {args.group_key}")
        start, end = fence.analysis_start_utc, fence.train_end_utc
        print(f"GROUP-KEY {pk} n_sym={len(cells)}")
        summaries = run_param_group(
            cells, fence, manifest, start=start, end=end, band=args.band
        )

    log_path = _append_summaries(summaries)
    cens = _write_censoring_from_disk()
    emitted_ids = {s["candidate_id"] for s in summaries}
    # merge with already-on-disk so partial resumes do not un-mark prior groups
    emitted_ids |= {
        c["candidate_id"]
        for c in load_manifest()["candidates"]
        if _already_emitted(c["candidate_id"])
    }
    rewrite_manifest_xena_paths(load_manifest(), emitted_ids)
    print(f"CENSORING {cens}")
    print(f"LOG {log_path}  n={len(summaries)}")
    print("NOTE: search / gate_universe / final_gate NOT run (operator-gated).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
