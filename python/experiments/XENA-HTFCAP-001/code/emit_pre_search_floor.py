#!/usr/bin/env python3
"""XENA-HTFCAP-001 pre-search gross-floor table (design §6 / XENA-003 lesson).

Per-cell TRAIN median gross bps/trade vs bybit_round_trip_cost_bps_v1 breakeven
(with funding). Disclosure + park rule only — no per-cell quality gate.

Sources (priority):
  1. Nautilus emission legs via xen.nautilus.adjudication_shim → RealizedBps
     (no local accounting).
  2. Else feature-replay on fenced TRAIN using frozen SPDR-006 defs (no retune)
     — labelled source=feature_replay_pre_emission; replaced when emissions land.

Park rule: if ENTIRE binding-cell mass is sub-breakeven → recommend park before
search. Individual sub-floor cells still enter the universe.

Usage (from python/):
  uv run python experiments/XENA-HTFCAP-001/code/build_universe.py
  uv run python experiments/XENA-HTFCAP-001/code/emit_pre_search_floor.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from tqdm import tqdm

CODE = Path(__file__).resolve().parent
EXP = CODE.parent
ROOT = EXP.parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(CODE))

from features import (  # noqa: E402
    ATR_PERIOD,
    VOL_MEDIAN_W,
    htf_features,
    map_htf_to_ltf,
)
from xen.bar_aggregator import aggregate_ohlc  # noqa: E402
from xen.evaluation import (  # noqa: E402
    BYBIT_FUNDING_CONSERVATIVE_BPS_PER_8H,
    bybit_round_trip_cost_bps,
)
from xen.nautilus.adjudication_shim import emission_to_adjudication_frames  # noqa: E402
from xen.nautilus.catalog_fence import fenced_bar_query, load_fence_manifest  # noqa: E402

UNIVERSE_ID = "XENA-HTFCAP-001"
RUNS_ROOT = REPO / "data" / "nautilus_runs" / UNIVERSE_ID
MANIFEST_PATH = RUNS_ROOT / "universe_manifest.json"
RESULTS = EXP / "results"
CATALOG_PATH = REPO / "data" / "catalog"
GAP_SPREAD_BPS = 5.0
NS_PER_MIN = 60_000_000_000


def load_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"run build_universe.py first — missing {MANIFEST_PATH}")
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def median_gross_from_emission(emission_dir: Path) -> tuple[float, int, str]:
    """Return (median_gross_bps, n_legs, source) via adjudication shim."""
    if not (emission_dir / "run_metadata.json").exists():
        return float("nan"), 0, "missing"
    try:
        _pos, cis, _meta = emission_to_adjudication_frames(emission_dir)
    except Exception as e:  # noqa: BLE001
        return float("nan"), 0, f"error:{e}"
    live = cis.filter(
        pl.col("Censored").cast(pl.Boolean).not_() & pl.col("RealizedBps").is_finite()
    )
    if live.height == 0:
        return float("nan"), 0, "emission_empty"
    r = live.get_column("RealizedBps").to_numpy().astype(float)
    return float(np.median(r)), int(r.size), "nautilus_emission"


def load_train_1m(symbol: str, fence) -> pl.DataFrame:
    catalog = ParquetDataCatalog(str(CATALOG_PATH))
    bars = fenced_bar_query(
        catalog,
        [f"{symbol}-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL"],
        start=fence.analysis_start_utc,
        end=fence.train_end_utc,
        band="TRAIN",
        manifest=fence,
    )
    if not bars:
        return pl.DataFrame()
    close_ns = np.array([b.ts_event for b in bars], dtype=np.int64)
    open_ns = close_ns - NS_PER_MIN
    return pl.DataFrame(
        {
            "Symbol": [symbol] * len(bars),
            "OpenTime": open_ns,
            "CloseTime": close_ns,
            "Open": [float(b.open) for b in bars],
            "High": [float(b.high) for b in bars],
            "Low": [float(b.low) for b in bars],
            "Close": [float(b.close) for b in bars],
            "TickVolume": [float(b.volume) for b in bars],
        }
    ).with_columns(
        pl.from_epoch("OpenTime", time_unit="ns").dt.replace_time_zone("UTC").alias("OpenTime"),
        pl.from_epoch("CloseTime", time_unit="ns").dt.replace_time_zone("UTC").alias("CloseTime"),
    ).sort("CloseTime")


def feature_replay_returns(
    train_1m: pl.DataFrame,
    *,
    filter_model: str,
    vol_thr: float,
    adx_min: float | None,
    hold_bars: int,
) -> np.ndarray:
    """Gross open-to-open bps via frozen SPDR-006 feature defs (floor disclosure only)."""
    if train_1m.is_empty() or train_1m.height < 240 * 3:
        return np.array([], dtype=np.float64)
    htf = aggregate_ohlc(train_1m, period_minutes=240, min_coverage=0.90).sort("CloseTime")
    ltf = aggregate_ohlc(train_1m, period_minutes=15, min_coverage=0.90).sort("CloseTime")
    if htf.height < ATR_PERIOD + VOL_MEDIAN_W or ltf.height < hold_bars + 5:
        return np.array([], dtype=np.float64)

    h_high = htf["High"].to_numpy().astype(np.float64)
    h_low = htf["Low"].to_numpy().astype(np.float64)
    h_close = htf["Close"].to_numpy().astype(np.float64)
    pack = htf_features(h_high, h_low, h_close)
    htf_dir = pack["htf_dir"]
    adx = pack["adx"]
    vol_ratio = pack["vol_ratio"]

    ltf_open = ltf["Open"].to_numpy().astype(np.float64)
    ltf_open_ns = ltf.select(pl.col("OpenTime").dt.epoch("ns")).to_series().to_numpy()
    htf_close_ns = htf.select(pl.col("CloseTime").dt.epoch("ns")).to_series().to_numpy()
    m = map_htf_to_ltf(ltf_open_ns, htf_close_ns)
    valid = m >= 0
    mm = np.where(valid, m, 0)
    dir_ltf = np.where(valid, htf_dir[mm], 0).astype(np.int8)
    adx_ltf = np.where(valid, adx[mm], np.nan)
    vol_ltf = np.where(valid, vol_ratio[mm], np.nan)

    n = len(ltf_open)
    room = np.arange(n) + hold_bars < n
    dgate = valid & (dir_ltf != 0) & np.isfinite(vol_ltf) & (vol_ltf >= vol_thr)
    dgate &= np.isfinite(ltf_open) & (ltf_open > 0)
    if filter_model == "DI_ADX×VOL_HI":
        dgate = dgate & np.isfinite(adx_ltf) & (adx_ltf >= float(adx_min or 0.0))
    elig = dgate & room
    elig_idx = np.nonzero(elig)[0]
    if elig_idx.size == 0:
        return np.array([], dtype=np.float64)

    # greedy non-overlapping (SPDR greedy_entries)
    entries: list[int] = []
    cursor = 0
    while cursor < len(elig_idx):
        i = int(elig_idx[cursor])
        entries.append(i)
        cursor = int(np.searchsorted(elig_idx, i + hold_bars, side="left"))
    ent = np.asarray(entries, dtype=np.int64)
    s = dir_ltf[ent].astype(np.float64)
    o0 = ltf_open[ent]
    o1 = ltf_open[ent + hold_bars]
    r = s * (o1 - o0) / o0 * 1e4
    return r[np.isfinite(r)].astype(np.float64)


def breakeven_bps(hold_bars: int) -> dict[str, float]:
    hold_hours = hold_bars * 0.25
    d = bybit_round_trip_cost_bps(
        "BTCUSDT",
        1.0,
        liquidity="taker",
        spread_bps=GAP_SPREAD_BPS,
        funding_bps_per_8h=BYBIT_FUNDING_CONSERVATIVE_BPS_PER_8H,
        hold_hours=hold_hours,
        funding_coverage="GAP",
    )
    return {
        "breakeven_bps": float(d["total_bps"]),
        "fee_rt_bps": float(d["fee_rt_bps"]),
        "spread_rt_bps": float(d["spread_rt_bps"]),
        "funding_rt_bps": float(d["funding_rt_bps"]),
        "hold_hours": hold_hours,
    }


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    fence = load_fence_manifest()
    manifest = load_manifest()
    candidates = manifest["candidates"]

    # Cache 1m TRAIN per symbol for feature-replay fallback
    train_cache: dict[str, pl.DataFrame] = {}
    rows: list[dict[str, Any]] = []

    for cell in tqdm(candidates, desc="floor"):
        cid = cell["candidate_id"]
        symbol = cell["symbol"]
        hold = int(cell["hold_bars"])
        be = breakeven_bps(hold)
        emission_dir = RUNS_ROOT / cid
        med, n_legs, source = median_gross_from_emission(emission_dir)

        if source in ("missing", "emission_empty") or (
            isinstance(source, str) and source.startswith("error")
        ):
            if symbol not in train_cache:
                train_cache[symbol] = load_train_1m(symbol, fence)
            r = feature_replay_returns(
                train_cache[symbol],
                filter_model=cell["filter_model"],
                vol_thr=float(cell["vol_thr"]),
                adx_min=cell["adx_min"],
                hold_bars=hold,
            )
            n_legs = int(r.size)
            med = float(np.median(r)) if n_legs else float("nan")
            source = "feature_replay_pre_emission"

        above = bool(np.isfinite(med) and med >= be["breakeven_bps"])
        rows.append(
            {
                "candidate_id": cid,
                "symbol": symbol,
                "role": cell["role"],
                "filter_model": cell["filter_model"],
                "vol_thr": cell["vol_thr"],
                "adx_min": cell["adx_min"],
                "hold_bars": hold,
                "hold_mult": cell["hold_mult"],
                "n_legs": n_legs,
                "median_gross_bps": med,
                "breakeven_bps": be["breakeven_bps"],
                "fee_rt_bps": be["fee_rt_bps"],
                "spread_rt_bps": be["spread_rt_bps"],
                "funding_rt_bps": be["funding_rt_bps"],
                "hold_hours": be["hold_hours"],
                "median_minus_breakeven": (
                    med - be["breakeven_bps"] if np.isfinite(med) else float("nan")
                ),
                "above_breakeven": above,
                "source": source,
                "cost_stack": "bybit_round_trip_cost_bps_v1",
                "spread_label": "GAP",
            }
        )

    df = pl.DataFrame(rows)
    out_pq = RESULTS / "pre_search_gross_floor.parquet"
    out_csv = RESULTS / "pre_search_gross_floor.csv"
    df.write_parquet(out_pq)
    df.write_csv(out_csv)

    bind = df.filter(pl.col("role") == "binding")
    n_bind = bind.height
    n_above = bind.filter(pl.col("above_breakeven")).height
    n_sub = n_bind - n_above
    all_sub = n_bind > 0 and n_above == 0
    summary = {
        "universe_id": UNIVERSE_ID,
        "generated_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "n_cells": df.height,
        "n_binding": n_bind,
        "n_binding_above_breakeven": n_above,
        "n_binding_sub_breakeven": n_sub,
        "entire_binding_mass_sub_breakeven": all_sub,
        "park_recommendation": (
            "PARK before search — entire binding mass sub-breakeven (design §6 / family kill row)"
            if all_sub
            else "PROCEED — at least one binding cell ≥ breakeven (individual sub-floor cells still enter)"
        ),
        "cost_stack": "bybit_round_trip_cost_bps_v1",
        "funding": "included (GAP conservative 1.0 bps/8h)",
        "spread_label": "GAP 5.0 bps (per-symbol pin deferred)",
        "sources": df.group_by("source").len().to_dicts(),
        "binding_median_gross_bps_p50": (
            float(bind["median_gross_bps"].median()) if n_bind else None
        ),
        "paths": {
            "parquet": str(out_pq.relative_to(REPO)),
            "csv": str(out_csv.relative_to(REPO)),
        },
    }
    out_sum = RESULTS / "pre_search_gross_floor_summary.json"
    out_sum.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"WROTE {out_pq}")
    print(f"WROTE {out_csv}")
    print(f"WROTE {out_sum}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
