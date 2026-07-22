#!/usr/bin/env python3
"""XENA-EPSOSC-001 universe manifest builder — ~224 binding cells + STRETCH probe.

Writes:
  data/nautilus_runs/XENA-EPSOSC-001/universe_manifest.json
  data/nautilus_runs/XENA-EPSOSC-001/membership.parquet
  python/experiments/XENA-EPSOSC-001/results/{universe_manifest,stage_bands,
    membership_days,selection_rule}.json|parquet|csv

Symbol axis (design §4.1): all ADMITTED instruments (listed + delisted) with
≥90 TRAIN membership-days under the pin selection rule
(``xen.nautilus.universe_selection`` rule_hash ``0dd53037…`` — top-10 trailing
24h volume, daily 00:00 UTC, lex tie-break).

Grid (design §4.2):
  Binding: VOLARM × 15m × W{96,192} × k{2.5,3.0} × clear{RET_ANCHOR,HYBRID}
           × side{L,S} = 16 / symbol
  Disclosure: STRETCH × 1h × RET_ANCHOR × W{96,192} × k{2.5,3.0} × side{L,S}
              = 8 / symbol

Band boundaries: frozen INFR-015 / calibration_pc fracs on TRAIN calendar
  search_frac=0.5, ranking_frac=0.25, embargo_frac=0.2
  via ``xen.xena.calibration.SegmentLayout.from_span``.

Usage (from python/):
  uv run python experiments/XENA-EPSOSC-001/code/build_universe.py
  uv run python experiments/XENA-EPSOSC-001/code/build_universe.py --reuse-spdr-membership
"""
from __future__ import annotations

import argparse
import hashlib
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
ROOT = EXP.parents[1]  # python/
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from xen.evaluation import (  # noqa: E402
    BYBIT_FUNDING_CONSERVATIVE_BPS_PER_8H,
    bybit_round_trip_cost_bps,
)
from xen.nautilus.catalog_fence import fenced_bar_query, load_fence_manifest  # noqa: E402
from xen.nautilus.universe_selection import (  # noqa: E402
    SelectionRule,
    rebalance_schedule,
    rule_hash,
)
from xen.xena.calibration import SegmentLayout  # noqa: E402
from xen.xena.calibration_pc import (  # noqa: E402
    EMBARGO_FRAC,
    STAGE_RANKING_FRAC,
    STAGE_SEARCH_FRAC,
)

UNIVERSE_ID = "XENA-EPSOSC-001"
FAMILY = "CF-EPSOSC-001"
RUNS_ROOT = REPO / "data" / "nautilus_runs" / UNIVERSE_ID
RESULTS = EXP / "results"
REGISTRY_PATH = REPO / "python/experiments/INFR-015/results/bybit_pc_frozen_registry.json"
ADMISSION = REPO / "python/experiments/INFR-011/artifacts/admission-ledger.jsonl"
CATALOG_PATH = REPO / "data" / "catalog"
SPDR_MEMBERSHIP = REPO / "python/experiments/SPDR-005/results/membership.parquet"
DESIGN_PIN_CLAIMED = "abbb184229236a75f624537ca605668a73f6f85138c150e14a3609c4191bf786"
PIN_RULE_HASH = "0dd530374fd3283ba9a82796d719c7bbd019d759e62c6987e0162ba5bcfc5ad2"

MIN_MEMBERSHIP_DAYS = 90
W_LEVELS = (96, 192)
K_LEVELS = (2.5, 3.0)
CLEARS_BINDING = ("RET_ANCHOR", "HYBRID")
SIDES = ("LONG_ONLY", "SHORT_ONLY")
VOLARM_RATIO = 1.25

# GAP spread pin until per-symbol pseudo-quote series wired (INFR-014 cost_pins)
GAP_SPREAD_BPS = 5.0
COST_STACK = "bybit_round_trip_cost_bps_v1"
CATALOG_VERSION = "INFR-011-A4-2026-07-16"
NS_PER_MIN = 60_000_000_000
NS_PER_DAY = 86_400_000_000_000

# Episode duration prior for cost (SPDR-005 med ~19–20h on VOLARM 15m)
DEFAULT_HOLD_HOURS = 20.0


def _utc_iso(ns: int) -> str:
    return datetime.fromtimestamp(ns / 1e9, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    """Raw file-bytes digest (audit only — not the XENA content pin)."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def content_pin_sha256(path: Path) -> str:
    """Binding pin identity: sha256 of ``json.dumps(registry, sort_keys=True)``.

    Matches ``xen.xena.calibration_bybit.verify_bybit_registry`` / artifact[\"sha256\"].
    File-bytes hash is a different object and must not be used as pin identity (QA #2).
    """
    artifact = json.loads(path.read_text(encoding="utf-8"))
    if "registry" not in artifact or "sha256" not in artifact:
        raise RuntimeError(f"registry artifact missing registry/sha256: {path}")
    blob = json.dumps(artifact["registry"], sort_keys=True).encode("utf-8")
    digest = hashlib.sha256(blob).hexdigest()
    if digest != artifact["sha256"]:
        raise RuntimeError(
            f"content pin mismatch: recomputed {digest} != artifact {artifact['sha256']}"
        )
    return digest


def pin_selection_rule() -> SelectionRule:
    """Pin SelectionRule — must hash to ``0dd53037…``."""
    rule = SelectionRule(
        n=10,
        metric="trailing_volume",
        window_bars=1440,
        rebalance="1d",
        rebalance_tz="UTC",
        rebalance_time="00:00",
        hysteresis_rank=0,
        pool="admitted_listed",  # pin field; ranking pool still includes delisted bars
        causal=True,
        tie_break="lexicographic_id",
    )
    rh = rule_hash(rule)
    if rh != PIN_RULE_HASH:
        raise RuntimeError(f"selection rule hash drift: {rh} != {PIN_RULE_HASH}")
    return rule


def stage_bands_from_fence(fence) -> dict[str, Any]:
    """Immutable stage bands on TRAIN calendar (frozen pin fracs)."""
    start_ns = int(fence.analysis_start_utc.timestamp() * 1e9)
    end_ns = int(fence.train_end_utc.timestamp() * 1e9)
    span = end_ns - start_ns
    purge_ns = int(EMBARGO_FRAC * span)
    layout = SegmentLayout.from_span(
        start_ns,
        end_ns,
        search_frac=STAGE_SEARCH_FRAC,
        ranking_frac=STAGE_RANKING_FRAC,
        purge_ns=purge_ns,
    )
    return {
        "source": "xen.xena.calibration_pc frozen fracs on INFR-011 TRAIN fence",
        "search_frac": STAGE_SEARCH_FRAC,
        "ranking_frac": STAGE_RANKING_FRAC,
        "embargo_frac": EMBARGO_FRAC,
        "purge_ns": layout.purge_ns,
        "train_start_utc": fence.analysis_start_utc.isoformat().replace("+00:00", "Z"),
        "train_end_utc": fence.train_end_utc.isoformat().replace("+00:00", "Z"),
        "holdout_start_utc": fence.holdout_start_utc.isoformat().replace("+00:00", "Z"),
        "search": {
            "start_ns": layout.search[0],
            "end_ns": layout.search[1],
            "start_utc": _utc_iso(layout.search[0]),
            "end_utc": _utc_iso(layout.search[1]),
        },
        "ranking": {
            "start_ns": layout.ranking[0],
            "end_ns": layout.ranking[1],
            "start_utc": _utc_iso(layout.ranking[0]),
            "end_utc": _utc_iso(layout.ranking[1]),
        },
        "stage2_gate": {
            "start_ns": layout.gate[0],
            "end_ns": layout.gate[1],
            "start_utc": _utc_iso(layout.gate[0]),
            "end_utc": _utc_iso(layout.gate[1]),
        },
        "note": "immutable once written; search may only read TRAIN search band",
    }


def load_admitted_pool(*, include_delisted: bool = True) -> list[str]:
    """ADMITTED instruments with catalog bars (delisted included when flag set)."""
    if not ADMISSION.exists():
        raise FileNotFoundError(ADMISSION)
    pool: list[str] = []
    with ADMISSION.open() as f:
        for line in f:
            r = json.loads(line)
            if r.get("admission") != "ADMITTED":
                continue
            if not include_delisted and r.get("listed") is not True:
                continue
            sym = r["symbol"]
            bar_dir = (
                CATALOG_PATH / "data" / "bar" / f"{sym}-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL"
            )
            if bar_dir.exists():
                pool.append(sym)
    pool = sorted(set(pool))
    if len(pool) < 10:
        raise RuntimeError(f"admitted pool too small: {len(pool)}")
    return pool


def load_train_volume_arrays(
    symbol: str, fence, catalog: ParquetDataCatalog
) -> tuple[np.ndarray, np.ndarray] | None:
    """TRAIN 1m (ts_event ns, volume) for trailing-volume membership; None if empty."""
    bars = fenced_bar_query(
        catalog,
        [f"{symbol}-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL"],
        start=fence.analysis_start_utc,
        end=fence.train_end_utc,
        band="TRAIN",
        manifest=fence,
    )
    if not bars:
        return None
    ts = np.array([int(b.ts_event) for b in bars], dtype=np.int64)
    vol = np.array([float(b.volume) for b in bars], dtype=np.float64)
    order = np.argsort(ts)
    return ts[order], vol[order]


def trailing_volume_at_rebalances(
    ts_event: np.ndarray,
    volume: np.ndarray,
    rebalance_ns: np.ndarray,
    *,
    window_bars: int = 1440,
) -> np.ndarray:
    """Trailing sum of 1m volume ending ≤ asof−1ns (universe_selection ε), per rebalance.

    Equivalent to ``rank_from_volume_panel`` window metric at each 00:00 UTC asof
    without materialising a full multi-symbol 1m panel in memory.
    """
    if ts_event.size == 0 or rebalance_ns.size == 0:
        return np.zeros(len(rebalance_ns), dtype=np.float64)
    window_ns = int(window_bars) * 60 * NS_PER_MIN
    # asof cutoff = rebalance − 1 ns (universe_selection._ASOF_EPS_NS)
    cutoffs = rebalance_ns.astype(np.int64) - 1
    window_starts = cutoffs - window_ns + 1
    csum = np.concatenate([[0.0], np.cumsum(volume)])
    right = np.searchsorted(ts_event, cutoffs, side="right")
    left = np.searchsorted(ts_event, window_starts, side="left")
    return csum[right] - csum[left]


def build_membership_delisted_inclusive(
    pool: list[str],
    rule: SelectionRule,
    fence,
) -> pl.DataFrame:
    """Daily top-10 via pin rule on ADMITTED pool incl. delisted (QA #1).

    Metric = pin ``trailing_volume`` (sum of 1m volume over 1440 bars ≤ asof−ε).
    Ranking uses the same sort/tie-break as ``rank_from_volume_panel``
    (metric desc, instrument_id lex asc). rule_hash must remain ``0dd53037…``.
    """
    schedule = rebalance_schedule(fence.analysis_start_utc, fence.train_end_utc, rule)
    if not schedule:
        raise RuntimeError("empty rebalance schedule on TRAIN fence")
    reb_ns = np.array([int(ts.timestamp() * 1e9) for ts in schedule], dtype=np.int64)
    # metric matrix: n_reb × filled per symbol sparsely via list of arrays
    # Collect per-rebalance (metric, iid) then rank — memory O(n_reb * n_pool) floats
    n_reb = len(reb_ns)
    # symbol -> array length n_reb of trailing volume
    metrics: dict[str, np.ndarray] = {}
    catalog = ParquetDataCatalog(str(CATALOG_PATH))
    for sym in tqdm(pool, desc="volume→trail"):
        loaded = load_train_volume_arrays(sym, fence, catalog)
        if loaded is None:
            continue
        ts, vol = loaded
        trail = trailing_volume_at_rebalances(
            ts, vol, reb_ns, window_bars=int(rule.window_bars)
        )
        if np.any(trail > 0):
            metrics[sym] = trail

    if not metrics:
        raise RuntimeError("no symbols with positive TRAIN trailing volume")

    rh = rule_hash(rule)
    rows: list[dict[str, Any]] = []
    syms = sorted(metrics.keys())  # stable for debugging; rank order is metric+lex
    for i, reb in enumerate(reb_ns):
        scored: list[tuple[float, str]] = []
        for sym in syms:
            m = float(metrics[sym][i])
            if m > 0 and m == m:
                scored.append((m, f"{sym}-LINEAR.BYBIT"))
        if not scored:
            continue
        # metric desc, instrument_id lex asc — same as rank_from_volume_panel
        scored.sort(key=lambda x: (-x[0], x[1]))
        top = scored[: int(rule.n)]
        for rank, (mval, iid) in enumerate(top, start=1):
            sym = iid.replace("-LINEAR.BYBIT", "")
            rows.append(
                {
                    "rebalance_ts": int(reb),
                    "symbol": sym,
                    "instrument_id": iid,
                    "rank": int(rank),
                    "metric_value": float(mval),
                    "rule_hash": rh,
                }
            )
    if not rows:
        return pl.DataFrame(
            schema={
                "rebalance_ts": pl.Int64,
                "symbol": pl.Utf8,
                "instrument_id": pl.Utf8,
                "rank": pl.Int64,
                "metric_value": pl.Float64,
                "rule_hash": pl.Utf8,
            }
        )
    return pl.DataFrame(rows)


def membership_from_spdr(rule: SelectionRule) -> pl.DataFrame:
    """Reuse SPDR-005 membership (same top-10 base-volume rule; listed pool).

    Note: SPDR used listed-only base volume; pin rule is trailing_volume. Acceptable
    bootstrap for symbol-axis discovery when full recompute is deferred — flag in
    manifest as source=spdr005_reuse.
    """
    if not SPDR_MEMBERSHIP.exists():
        raise FileNotFoundError(SPDR_MEMBERSHIP)
    df = pl.read_parquet(SPDR_MEMBERSHIP)
    rh = rule_hash(rule)
    # rebalance_ts is datetime
    out = df.with_columns(
        pl.col("rebalance_ts").dt.epoch("ns").alias("rebalance_ts_ns"),
        pl.col("symbol").alias("symbol"),
        (pl.col("symbol") + "-LINEAR.BYBIT").alias("instrument_id"),
        pl.col("rank").cast(pl.Int64),
        pl.col("trailing_24h_base_volume").alias("metric_value"),
        pl.lit(rh).alias("rule_hash"),
    ).select(
        pl.col("rebalance_ts_ns").alias("rebalance_ts"),
        "symbol",
        "instrument_id",
        "rank",
        "metric_value",
        "rule_hash",
        pl.col("rebalance_ts").alias("rebalance_ts_dt"),
    )
    return out


def symbol_axis(membership: pl.DataFrame, min_days: int = MIN_MEMBERSHIP_DAYS) -> list[dict[str, Any]]:
    """Symbols with ≥min_days TRAIN membership-days (delisted included if present)."""
    days = (
        membership.group_by("symbol")
        .agg(pl.col("rebalance_ts").n_unique().alias("n_days"))
        .sort("n_days", descending=True)
    )
    axis = days.filter(pl.col("n_days") >= min_days)
    return [
        {"symbol": r["symbol"], "n_membership_days": int(r["n_days"])}
        for r in axis.iter_rows(named=True)
    ]


def candidate_id(
    symbol: str,
    object_type: str,
    ltf_min: int,
    w: int,
    k: float,
    clear: str,
    side: str,
) -> str:
    side_s = "L" if side == "LONG_ONLY" else "S"
    return f"{symbol}__{object_type}__{ltf_min}m__W{w}__k{k:g}__{clear}__{side_s}"


def cost_bps_for_hold_hours(hold_hours: float) -> dict[str, Any]:
    """bybit_round_trip_cost_bps_v1 with funding × episode duration."""
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
        "cost_bps": float(d["total_bps"]),
        "hold_hours": hold_hours,
        "fee_rt_bps": d["fee_rt_bps"],
        "spread_rt_bps": d["spread_rt_bps"],
        "funding_rt_bps": d["funding_rt_bps"],
        "funding_coverage": d["funding_coverage"],
        "spread_label": "GAP",
        "spread_bps": GAP_SPREAD_BPS,
    }


def build_candidates(symbols: list[str]) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    # Prior hold hours: VOLARM med ~20h; STRETCH/1h similar order
    cost_volarm = cost_bps_for_hold_hours(DEFAULT_HOLD_HOURS)
    cost_stretch = cost_bps_for_hold_hours(DEFAULT_HOLD_HOURS)

    for symbol in symbols:
        # Binding VOLARM × 15m × 16
        for w in W_LEVELS:
            for k in K_LEVELS:
                for clear in CLEARS_BINDING:
                    for side in SIDES:
                        cid = candidate_id(symbol, "VOLARM", 15, w, k, clear, side)
                        cells.append(
                            {
                                "candidate_id": cid,
                                "run_dir": cid,
                                "symbol": symbol,
                                "instrument_id": f"{symbol}-LINEAR.BYBIT",
                                "role": "binding",
                                "object_type": "VOLARM",
                                "ltf_minutes": 15,
                                "domain": "15m",
                                "w": w,
                                "k": k,
                                "clear_policy": clear,
                                "side_mode": side,
                                "volarm_ratio": VOLARM_RATIO,
                                "cost_bps": cost_volarm["cost_bps"],
                                "cost_breakdown": cost_volarm,
                                "money_per_unit": 1.0,
                                "cost_stack": COST_STACK,
                            }
                        )
        # Disclosure STRETCH × 1h × RET_ANCHOR × 8
        for w in W_LEVELS:
            for k in K_LEVELS:
                for side in SIDES:
                    clear = "RET_ANCHOR"
                    cid = candidate_id(symbol, "STRETCH", 60, w, k, clear, side)
                    cells.append(
                        {
                            "candidate_id": cid,
                            "run_dir": cid,
                            "symbol": symbol,
                            "instrument_id": f"{symbol}-LINEAR.BYBIT",
                            "role": "disclosure",
                            "object_type": "STRETCH",
                            "ltf_minutes": 60,
                            "domain": "1h",
                            "w": w,
                            "k": k,
                            "clear_policy": clear,
                            "side_mode": side,
                            "volarm_ratio": None,
                            "cost_bps": cost_stretch["cost_bps"],
                            "cost_breakdown": cost_stretch,
                            "money_per_unit": 1.0,
                            "cost_stack": COST_STACK,
                        }
                    )
    return cells


def trade_size_for(symbol: str) -> str:
    """Fixed contract qty — bps estimand is size-invariant; keep fills valid."""
    # High-unit memes need larger lots; majors smaller.
    if symbol in ("BTCUSDT",):
        return "0.01"
    if symbol in ("ETHUSDT",):
        return "0.1"
    if symbol in ("SOLUSDT", "XRPUSDT", "DOGEUSDT"):
        return "1"
    if "1000" in symbol or "SHIB" in symbol or "PEPE" in symbol or "BONK" in symbol:
        return "100"
    return "10"


def build_manifest(
    *,
    reuse_spdr_membership: bool = False,
    max_pool: int | None = None,
) -> dict[str, Any]:
    fence = load_fence_manifest()
    bands = stage_bands_from_fence(fence)
    rule = pin_selection_rule()
    rh = rule_hash(rule)

    RESULTS.mkdir(parents=True, exist_ok=True)
    RUNS_ROOT.mkdir(parents=True, exist_ok=True)
    mem_path = RUNS_ROOT / "membership.parquet"
    mem_res = RESULTS / "membership.parquet"

    if reuse_spdr_membership:
        # Escape hatch only — violates design §4.1 delisted-inclusive (QA D2).
        # Must not be used for production universe without operator written approval.
        membership = membership_from_spdr(rule)
        mem_source = "spdr005_reuse"
        delisted_included = False
    else:
        pool = load_admitted_pool(include_delisted=True)
        if max_pool is not None:
            pool = pool[:max_pool]
        print(
            f"Building delisted-inclusive membership for {len(pool)} ADMITTED "
            f"symbols (pin trailing_volume, rule_hash={rh[:12]}…)…"
        )
        membership = build_membership_delisted_inclusive(pool, rule, fence)
        mem_source = "universe_selection_trailing_volume_delisted_inclusive"
        delisted_included = True

    # Persist membership (ns for strategy day-set lookup)
    mem_write = membership.select(
        [
            c
            for c in (
                "rebalance_ts",
                "symbol",
                "instrument_id",
                "rank",
                "metric_value",
                "rule_hash",
            )
            if c in membership.columns
        ]
    )
    if mem_write["rebalance_ts"].dtype != pl.Int64:
        mem_write = mem_write.with_columns(
            pl.col("rebalance_ts").dt.epoch("ns").cast(pl.Int64).alias("rebalance_ts")
        )
    mem_write.write_parquet(mem_path)
    mem_write.write_parquet(mem_res)

    axis = symbol_axis(membership, MIN_MEMBERSHIP_DAYS)
    symbols = [a["symbol"] for a in axis]
    if not symbols:
        raise RuntimeError("no symbols with ≥90 membership-days")

    days_df = pl.DataFrame(axis)
    days_df.write_parquet(RESULTS / "membership_days.parquet")
    days_df.write_csv(RESULTS / "membership_days.csv")

    candidates = build_candidates(symbols)
    n_bind = sum(1 for c in candidates if c["role"] == "binding")
    n_disc = sum(1 for c in candidates if c["role"] == "disclosure")
    expected_bind = 16 * len(symbols)
    expected_disc = 8 * len(symbols)
    if n_bind != expected_bind or n_disc != expected_disc:
        raise RuntimeError(
            f"grid size wrong: bind={n_bind}/{expected_bind} disc={n_disc}/{expected_disc}"
        )

    # Binding pin identity = content sha (abbb1842…), not file-bytes (QA #2)
    content_sha = content_pin_sha256(REGISTRY_PATH) if REGISTRY_PATH.exists() else None
    file_bytes_sha = _sha256_file(REGISTRY_PATH) if REGISTRY_PATH.exists() else None
    pin_match = content_sha == DESIGN_PIN_CLAIMED

    (RESULTS / "selection_rule.json").write_text(
        json.dumps(
            {
                "rule": {
                    "n": rule.n,
                    "metric": rule.metric,
                    "window_bars": rule.window_bars,
                    "rebalance": rule.rebalance,
                    "rebalance_tz": rule.rebalance_tz,
                    "rebalance_time": rule.rebalance_time,
                    "hysteresis_rank": rule.hysteresis_rank,
                    "pool": rule.pool,
                    "causal": rule.causal,
                    "tie_break": rule.tie_break,
                },
                "rule_hash": rh,
                "pin_match": rh == PIN_RULE_HASH,
                "membership_source": mem_source,
                "include_delisted_in_ranking_pool": delisted_included,
                "metric_note": (
                    "pin metric trailing_volume = sum of 1m volume over window_bars; "
                    "not USDT-notional (design text corrected to pin metric)"
                ),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return {
        "universe_id": UNIVERSE_ID,
        "family": FAMILY,
        "lane": "XENA",
        "schema": "xena.universe_manifest.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "n_candidates": len(candidates),
        "n_binding": n_bind,
        "n_disclosure": n_disc,
        "n_symbols": len(symbols),
        "grid": {
            "binding": {
                "object": "VOLARM",
                "domain": "15m",
                "volarm_ratio": VOLARM_RATIO,
                "w": list(W_LEVELS),
                "k": list(K_LEVELS),
                "clear": list(CLEARS_BINDING),
                "side": list(SIDES),
                "variants_per_symbol": 16,
            },
            "disclosure": {
                "object": "STRETCH",
                "domain": "1h",
                "clear": ["RET_ANCHOR"],
                "w": list(W_LEVELS),
                "k": list(K_LEVELS),
                "side": list(SIDES),
                "variants_per_symbol": 8,
                "note": "disclosure-only; never centre a claim (design §4.2 / caveat 2)",
            },
        },
        "instruments": {
            "symbol_axis": axis,
            "min_membership_days": MIN_MEMBERSHIP_DAYS,
            "membership_path": str(mem_path.relative_to(REPO)),
            "membership_source": mem_source,
            "selection_rule_hash": rh,
            "delisted_included": delisted_included,
            "note": (
                "causal online top-10 via xen.nautilus.universe_selection pin rule; "
                "trailing_volume metric; open episodes may run to clear after membership exit"
            ),
        },
        "feature_pin": {
            "source": "python/experiments/SPDR-005/screen_code/spdr005_screen.py",
            "atr_period": 14,
            "atr_slow": 56,
            "volarm_ratio": VOLARM_RATIO,
            "ret_clear_frac": 0.25,
            "retune": False,
        },
        "stage_bands": bands,
        "registry": {
            "path": str(REGISTRY_PATH.relative_to(REPO)),
            "sha256_content_pin": content_sha,
            "sha256_file_bytes_audit_only": file_bytes_sha,
            "sha256_design_claimed": DESIGN_PIN_CLAIMED,
            "sha256_match_design": pin_match,
            "class_id": "CLS-EPISODE",
            "cadence": "LOW_ONLY_CERTIFY",
            "binder": "two_stage_sample_split",
            "cost_stack": COST_STACK,
            "stage1_score_kind": "g_net",
            "stage1_charge_costs": True,
            "e2e_pass_event": "stage2_gross_lcb_positive",
            "n_legs_floor": 16,
            "block_legs": "episode_overlap_rule_v1",
            "selection_rule_default_hash": PIN_RULE_HASH,
            "true_alpha_priced_le": 0.06,
            "pin_verify_method": (
                "sha256(json.dumps(registry, sort_keys=True)) == artifact['sha256'] "
                "(verify_bybit_registry); file-bytes hash is audit-only"
            ),
        },
        "topology": {
            "batch": "multi_instrument_single_node",
            "dispose_on_completion": False,
            "one_node_per_process": True,
            "lessons": ["L-30", "L-31"],
            "s1_smoke": "INFR-014 S1 PASS multi_instrument_single_node admissible",
            "episode_grouping": "adjudication_shim L-16 episode-native (no local accounting)",
            "segment_end_censoring": True,
            "censored_fraction_disclosure": True,
        },
        "emission": {
            "contract": "nautilus-emission-v1",
            "sl_price": "synthetic finite EntryFill - side * 1.0 * k * ATR14[t-1]",
            "live_stop_order": False,
            "catalog_version": CATALOG_VERSION,
            "runs_root": str(RUNS_ROOT.relative_to(REPO)),
        },
        "trade_sizes": {s: trade_size_for(s) for s in symbols},
        "candidates": candidates,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="XENA-EPSOSC-001 universe builder")
    parser.add_argument(
        "--reuse-spdr-membership",
        action="store_true",
        help=(
            "ESCAPE HATCH only: SPDR-005 listed-only membership (violates design §4.1 "
            "delisted-inclusive). Requires operator written approval for production."
        ),
    )
    parser.add_argument(
        "--max-pool",
        type=int,
        default=None,
        help="cap admitted pool size (debug only)",
    )
    args = parser.parse_args()

    reuse = args.reuse_spdr_membership
    if reuse:
        print(
            "WARNING: --reuse-spdr-membership is an escape hatch (listed-only). "
            "Design §4.1 requires delisted-inclusive recompute for production."
        )
    else:
        print(
            "Full ADMITTED+delisted membership recompute "
            "(pin trailing_volume via universe_selection semantics)…"
        )

    manifest = build_manifest(
        reuse_spdr_membership=reuse,
        max_pool=args.max_pool,
    )
    text = json.dumps(manifest, indent=2, sort_keys=False) + "\n"
    out_runs = RUNS_ROOT / "universe_manifest.json"
    out_res = RESULTS / "universe_manifest.json"
    out_bands = RESULTS / "stage_bands.json"
    out_runs.write_text(text, encoding="utf-8")
    out_res.write_text(text, encoding="utf-8")
    out_bands.write_text(
        json.dumps(manifest["stage_bands"], indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"WROTE {out_runs}  n={manifest['n_candidates']} "
        f"binding={manifest['n_binding']} disclosure={manifest['n_disclosure']} "
        f"symbols={manifest['n_symbols']}"
    )
    print(f"  symbols: {[a['symbol'] for a in manifest['instruments']['symbol_axis']]}")
    print(
        f"  content_pin={manifest['registry']['sha256_content_pin']} "
        f"match_design={manifest['registry']['sha256_match_design']} "
        f"delisted_included={manifest['instruments']['delisted_included']}"
    )
    sb = manifest["stage_bands"]
    print(f"  search  {sb['search']['start_utc']} → {sb['search']['end_utc']}")
    print(f"  ranking {sb['ranking']['start_utc']} → {sb['ranking']['end_utc']}")
    print(f"  stage2  {sb['stage2_gate']['start_utc']} → {sb['stage2_gate']['end_utc']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
