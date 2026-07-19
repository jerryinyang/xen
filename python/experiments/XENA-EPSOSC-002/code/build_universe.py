#!/usr/bin/env python3
"""XENA-EPSOSC-002 universe manifest builder — mass-aligned, RET_ANCHOR-only.

Fix #1 (design §5): TRAIN_START shifted forward to the VOLARM mass plateau so the
pinned 0.5 search fraction lands ON populated data. Fix #2 (§4.2): RET_ANCHOR-only
grid (HYBRID + STRETCH disclosure dropped). Fixes #3/#4 (K≥3 distinct-symbol,
drift-twin) act at search/analysis stages, not here.

TRAIN_START = 2022-07-01 — frozen from data (freeze_diagnostics.json):
  * predeclared X = search-band binding-cell coverage ≥ 0.80 (zero-leg ≤ 0.20).
    At 2022-07-01 the pinned SegmentLayout search band [2022-07-01, 2023-01-31] covers 0.842
    of 002-axis RET_ANCHOR cells → PASS. (Raw episode mass is present from ~2021-11;
    2022-07-01 chosen on the plateau to separate from the 2021/2023 single-name drift
    regimes that produced 001's AKRO pedestal — see design §5 / freeze note.)
  * TRAIN_END = 2023-12-18 (fence train_end_utc; TRAIN/TEST split, UNCHANGED).
  * Global holdout 2025-01-08→ SEALED, never queried here.

Membership axis (design §4.1): re-slice of the XENA-EPSOSC-001 delisted-inclusive
membership (rule_hash 0dd53037…, window-independent daily top-10) to the shifted
window; symbols with ≥90 membership-days on [2022-07-01, 2023-12-18]. 002 axis ⊆ 001
axis by construction (shorter window ⇒ fewer membership-days). Verified: 19 symbols,
10 early-only 001 names drop (EOS/MATIC/LUNA/XEM/FTM/SRM/OMG/KEEP/CELR/10000NFT).

Writes:
  data/nautilus_runs/XENA-EPSOSC-002/{universe_manifest.json,membership.parquet}
  python/experiments/XENA-EPSOSC-002/results/{universe_manifest,stage_bands,
    membership_days,selection_rule}.json|parquet|csv

Usage (from python/):
  uv run python experiments/XENA-EPSOSC-002/code/build_universe.py
"""
from __future__ import annotations

import hashlib
import json
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

from xen.evaluation import (  # noqa: E402
    BYBIT_FUNDING_CONSERVATIVE_BPS_PER_8H,
    bybit_round_trip_cost_bps,
)
from xen.nautilus.catalog_fence import load_fence_manifest  # noqa: E402
from xen.nautilus.universe_selection import SelectionRule, rule_hash  # noqa: E402
from xen.xena.calibration import SegmentLayout  # noqa: E402
from xen.xena.calibration_pc import (  # noqa: E402
    EMBARGO_FRAC,
    STAGE_RANKING_FRAC,
    STAGE_SEARCH_FRAC,
)

UNIVERSE_ID = "XENA-EPSOSC-002"
FAMILY = "CF-EPSOSC-001"
RUNS_ROOT = REPO / "data" / "nautilus_runs" / UNIVERSE_ID
RESULTS = EXP / "results"
REGISTRY_PATH = REPO / "python/experiments/INFR-015/results/bybit_pc_frozen_registry.json"
CATALOG_PATH = REPO / "data" / "catalog"
# Source membership: 001 delisted-inclusive recompute (rule_hash 0dd53037…), window-
# independent daily top-10. Re-sliced to the 002 shifted window (design §4.1).
SRC_MEMBERSHIP = REPO / "python/experiments/XENA-EPSOSC-001/results/membership.parquet"
DESIGN_PIN_CLAIMED = "abbb184229236a75f624537ca605668a73f6f85138c150e14a3609c4191bf786"
PIN_RULE_HASH = "0dd530374fd3283ba9a82796d719c7bbd019d759e62c6987e0162ba5bcfc5ad2"

# Frozen TRAIN_START (design §5, freeze_diagnostics.json). TRAIN_END from fence.
TRAIN_START_002 = datetime(2022, 7, 1, tzinfo=timezone.utc)
PREDECLARED_X = "search_band_binding_cell_coverage_ge_0.80"
MEASURED_SEARCH_COVERAGE = 0.842  # freeze_diagnostics.json @ 2022-07-01

MIN_MEMBERSHIP_DAYS = 90
W_LEVELS = (96, 192)
K_LEVELS = (2.5, 3.0)
CLEARS_BINDING = ("RET_ANCHOR",)  # fix #2: HYBRID dropped
SIDES = ("LONG_ONLY", "SHORT_ONLY")
VOLARM_RATIO = 1.25

GAP_SPREAD_BPS = 5.0  # INFR-014 cost_pins pin; T1 OHLCV catalog has no per-symbol
#   pseudo-quote series → per-symbol spread NOT measurable on T1 (design §6/§11 note).
COST_STACK = "bybit_round_trip_cost_bps_v1"
CATALOG_VERSION = "INFR-011-A4-2026-07-16"
NS_PER_MIN = 60_000_000_000
DEFAULT_HOLD_HOURS = 20.0  # SPDR-005 VOLARM 15m median ~19–20h


def _utc_iso(ns: int) -> str:
    return datetime.fromtimestamp(ns / 1e9, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def content_pin_sha256(path: Path) -> str:
    """Binding pin identity: sha256 of json.dumps(registry, sort_keys=True)."""
    artifact = json.loads(path.read_text(encoding="utf-8"))
    if "registry" not in artifact or "sha256" not in artifact:
        raise RuntimeError(f"registry artifact missing registry/sha256: {path}")
    blob = json.dumps(artifact["registry"], sort_keys=True).encode("utf-8")
    digest = hashlib.sha256(blob).hexdigest()
    if digest != artifact["sha256"]:
        raise RuntimeError(f"content pin mismatch: {digest} != {artifact['sha256']}")
    return digest


def pin_selection_rule() -> SelectionRule:
    rule = SelectionRule(
        n=10,
        metric="trailing_volume",
        window_bars=1440,
        rebalance="1d",
        rebalance_tz="UTC",
        rebalance_time="00:00",
        hysteresis_rank=0,
        pool="admitted_listed",
        causal=True,
        tie_break="lexicographic_id",
    )
    rh = rule_hash(rule)
    if rh != PIN_RULE_HASH:
        raise RuntimeError(f"selection rule hash drift: {rh} != {PIN_RULE_HASH}")
    return rule


def stage_bands_shifted(fence) -> dict[str, Any]:
    """Immutable stage bands on the SHIFTED TRAIN window (pinned fracs, fix #1).

    start = TRAIN_START_002 (mass plateau); end = fence.train_end_utc (UNCHANGED).
    Holdout fence untouched.
    """
    start_ns = int(TRAIN_START_002.timestamp() * 1e9)
    end_ns = int(fence.train_end_utc.timestamp() * 1e9)
    if start_ns <= int(fence.analysis_start_utc.timestamp() * 1e9):
        raise RuntimeError("TRAIN_START_002 must be strictly after analysis_start (shift fwd)")
    if end_ns >= int(fence.holdout_start_utc.timestamp() * 1e9):
        raise RuntimeError("TRAIN_END must stay before holdout_start (sealed)")
    span = end_ns - start_ns
    purge_ns = int(EMBARGO_FRAC * span)
    layout = SegmentLayout.from_span(
        start_ns, end_ns,
        search_frac=STAGE_SEARCH_FRAC,
        ranking_frac=STAGE_RANKING_FRAC,
        purge_ns=purge_ns,
    )
    return {
        "source": "xen.xena.calibration_pc frozen fracs on SHIFTED TRAIN window (fix #1)",
        "search_frac": STAGE_SEARCH_FRAC,
        "ranking_frac": STAGE_RANKING_FRAC,
        "embargo_frac": EMBARGO_FRAC,
        "purge_ns": layout.purge_ns,
        "train_start_utc": TRAIN_START_002.isoformat().replace("+00:00", "Z"),
        "train_start_source": "frozen 2022-07-01 (design §5; predeclared X + plateau)",
        "predeclared_X": PREDECLARED_X,
        "measured_search_band_coverage": MEASURED_SEARCH_COVERAGE,
        "train_end_utc": fence.train_end_utc.isoformat().replace("+00:00", "Z"),
        "holdout_start_utc": fence.holdout_start_utc.isoformat().replace("+00:00", "Z"),
        "analysis_start_utc_fence": fence.analysis_start_utc.isoformat().replace("+00:00", "Z"),
        "search": {
            "start_ns": layout.search[0], "end_ns": layout.search[1],
            "start_utc": _utc_iso(layout.search[0]), "end_utc": _utc_iso(layout.search[1]),
        },
        "ranking": {
            "start_ns": layout.ranking[0], "end_ns": layout.ranking[1],
            "start_utc": _utc_iso(layout.ranking[0]), "end_utc": _utc_iso(layout.ranking[1]),
        },
        "stage2_gate": {
            "start_ns": layout.gate[0], "end_ns": layout.gate[1],
            "start_utc": _utc_iso(layout.gate[0]), "end_utc": _utc_iso(layout.gate[1]),
        },
        "note": "immutable once written; search may only read the shifted TRAIN search band",
    }


def reslice_membership(fence) -> pl.DataFrame:
    """Re-slice 001 membership to the shifted window (design §4.1).

    Daily causal top-10 is window-independent, so 001 rows with rebalance_ts in
    [TRAIN_START_002, train_end) ARE 002's membership on the shifted window.
    """
    if not SRC_MEMBERSHIP.exists():
        raise FileNotFoundError(SRC_MEMBERSHIP)
    src = pl.read_parquet(SRC_MEMBERSHIP)
    lo = int(TRAIN_START_002.timestamp() * 1e9)
    hi = int(fence.train_end_utc.timestamp() * 1e9)
    out = src.filter((pl.col("rebalance_ts") >= lo) & (pl.col("rebalance_ts") < hi))
    if out.height == 0:
        raise RuntimeError("empty membership after re-slice")
    return out


def symbol_axis(membership: pl.DataFrame, min_days: int = MIN_MEMBERSHIP_DAYS) -> list[dict[str, Any]]:
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


def candidate_id(symbol: str, w: int, k: float, clear: str, side: str) -> str:
    side_s = "L" if side == "LONG_ONLY" else "S"
    return f"{symbol}__VOLARM__15m__W{w}__k{k:g}__{clear}__{side_s}"


def cost_bps_for_hold_hours(hold_hours: float) -> dict[str, Any]:
    d = bybit_round_trip_cost_bps(
        "BTCUSDT", 1.0,
        liquidity="taker",
        spread_bps=GAP_SPREAD_BPS,
        funding_bps_per_8h=BYBIT_FUNDING_CONSERVATIVE_BPS_PER_8H,
        hold_hours=hold_hours,
        funding_coverage="GAP",
    )
    return {
        "cost_bps": float(d["total_bps"]), "hold_hours": hold_hours,
        "fee_rt_bps": d["fee_rt_bps"], "spread_rt_bps": d["spread_rt_bps"],
        "funding_rt_bps": d["funding_rt_bps"], "funding_coverage": d["funding_coverage"],
        "spread_label": "GAP", "spread_bps": GAP_SPREAD_BPS,
    }


def build_candidates(symbols: list[str]) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    cost = cost_bps_for_hold_hours(DEFAULT_HOLD_HOURS)
    for symbol in symbols:
        for w in W_LEVELS:
            for k in K_LEVELS:
                for clear in CLEARS_BINDING:
                    for side in SIDES:
                        cid = candidate_id(symbol, w, k, clear, side)
                        cells.append({
                            "candidate_id": cid, "run_dir": cid, "symbol": symbol,
                            "instrument_id": f"{symbol}-LINEAR.BYBIT", "role": "binding",
                            "object_type": "VOLARM", "ltf_minutes": 15, "domain": "15m",
                            "w": w, "k": k, "clear_policy": clear, "side_mode": side,
                            "volarm_ratio": VOLARM_RATIO, "cost_bps": cost["cost_bps"],
                            "cost_breakdown": cost, "money_per_unit": 1.0, "cost_stack": COST_STACK,
                        })
    return cells


def trade_size_for(symbol: str) -> str:
    if symbol in ("BTCUSDT",):
        return "0.01"
    if symbol in ("ETHUSDT",):
        return "0.1"
    if symbol in ("SOLUSDT", "XRPUSDT", "DOGEUSDT"):
        return "1"
    if "1000" in symbol or "SHIB" in symbol or "PEPE" in symbol or "BONK" in symbol:
        return "100"
    return "10"


def build_manifest() -> dict[str, Any]:
    fence = load_fence_manifest()
    bands = stage_bands_shifted(fence)
    rule = pin_selection_rule()
    rh = rule_hash(rule)

    RESULTS.mkdir(parents=True, exist_ok=True)
    RUNS_ROOT.mkdir(parents=True, exist_ok=True)

    membership = reslice_membership(fence)
    mem_write = membership.select(
        ["rebalance_ts", "symbol", "instrument_id", "rank", "metric_value", "rule_hash"]
    )
    mem_write.write_parquet(RUNS_ROOT / "membership.parquet")
    mem_write.write_parquet(RESULTS / "membership.parquet")

    axis = symbol_axis(membership, MIN_MEMBERSHIP_DAYS)
    symbols = [a["symbol"] for a in axis]
    if not symbols:
        raise RuntimeError("no symbols with ≥90 membership-days on shifted window")

    # axis ⊆ 001 axis invariant (shifted window ⊆ full window)
    axis001 = set(
        pl.read_csv(REPO / "python/experiments/XENA-EPSOSC-001/results/membership_days.csv")
        ["symbol"].to_list()
    )
    if not set(symbols).issubset(axis001):
        raise RuntimeError(f"002 axis not subset of 001 axis: {set(symbols) - axis001}")

    days_df = pl.DataFrame(axis)
    days_df.write_parquet(RESULTS / "membership_days.parquet")
    days_df.write_csv(RESULTS / "membership_days.csv")

    candidates = build_candidates(symbols)
    n_bind = len(candidates)
    expected_bind = 8 * len(symbols)
    if n_bind != expected_bind:
        raise RuntimeError(f"grid size wrong: bind={n_bind}/{expected_bind}")

    content_sha = content_pin_sha256(REGISTRY_PATH) if REGISTRY_PATH.exists() else None
    file_bytes_sha = _sha256_file(REGISTRY_PATH) if REGISTRY_PATH.exists() else None
    pin_match = content_sha == DESIGN_PIN_CLAIMED

    (RESULTS / "selection_rule.json").write_text(
        json.dumps({
            "rule": {
                "n": rule.n, "metric": rule.metric, "window_bars": rule.window_bars,
                "rebalance": rule.rebalance, "rebalance_tz": rule.rebalance_tz,
                "rebalance_time": rule.rebalance_time, "hysteresis_rank": rule.hysteresis_rank,
                "pool": rule.pool, "causal": rule.causal, "tie_break": rule.tie_break,
            },
            "rule_hash": rh, "pin_match": rh == PIN_RULE_HASH,
            "membership_source": "epsosc001_membership_reslice_shifted_window",
            "membership_source_note": (
                "001 delisted-inclusive trailing_volume recompute (rule_hash 0dd53037…), "
                "window-independent daily top-10, re-sliced to [2022-07-01, 2023-12-18]"
            ),
        }, indent=2) + "\n", encoding="utf-8")

    return {
        "universe_id": UNIVERSE_ID, "family": FAMILY, "lane": "XENA",
        "schema": "xena.universe_manifest.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "n_candidates": len(candidates), "n_binding": n_bind, "n_disclosure": 0,
        "n_symbols": len(symbols),
        "grid": {
            "binding": {
                "object": "VOLARM", "domain": "15m", "volarm_ratio": VOLARM_RATIO,
                "w": list(W_LEVELS), "k": list(K_LEVELS), "clear": list(CLEARS_BINDING),
                "side": list(SIDES), "variants_per_symbol": 8,
                "note": "RET_ANCHOR-only (fix #2: HYBRID + STRETCH disclosure dropped vs 001)",
            },
        },
        "instruments": {
            "symbol_axis": axis, "min_membership_days": MIN_MEMBERSHIP_DAYS,
            "membership_path": str((RUNS_ROOT / "membership.parquet").relative_to(REPO)),
            "membership_source": "epsosc001_membership_reslice_shifted_window",
            "selection_rule_hash": rh, "delisted_included": True,
            "axis_subset_of_001": True,
            "note": (
                "causal online top-10 (rule 0dd53037…); ≥90 membership-days on the "
                "SHIFTED window [2022-07-01, 2023-12-18]; 002 axis ⊆ 001 axis"
            ),
        },
        "feature_pin": {
            "source": "python/experiments/SPDR-005/screen_code/spdr005_screen.py",
            "atr_period": 14, "atr_slow": 56, "volarm_ratio": VOLARM_RATIO,
            "ret_clear_frac": 0.25, "retune": False,
        },
        "stage_bands": bands,
        "registry": {
            "path": str(REGISTRY_PATH.relative_to(REPO)),
            "sha256_content_pin": content_sha,
            "sha256_file_bytes_audit_only": file_bytes_sha,
            "sha256_design_claimed": DESIGN_PIN_CLAIMED,
            "sha256_match_design": pin_match,
            "class_id": "CLS-EPISODE", "cadence": "LOW_ONLY_CERTIFY",
            "binder": "two_stage_sample_split", "cost_stack": COST_STACK,
            "stage1_score_kind": "g_net", "stage1_charge_costs": True,
            "e2e_pass_event": "stage2_gross_lcb_positive",
            "n_legs_floor": 16, "block_legs": "episode_overlap_rule_v1",
            "selection_rule_default_hash": PIN_RULE_HASH, "true_alpha_priced_le": 0.06,
        },
        "certification": {
            "min_distinct_symbols_K": 3,
            "amendment": "AMENDMENT-1 TIGHTER (design §4.3/§16.2): certified one_subset must "
                         "contain ≥3 DISTINCT symbols; post-rank filter after certify_and_rank "
                         "unless the pin supports it natively; singletons disclosure-only",
            "target_pooled_n_legs": 50,
        },
        "topology": {
            "batch": "multi_instrument_single_node", "dispose_on_completion": False,
            "one_node_per_process": True, "lessons": ["L-30", "L-31"],
            "episode_grouping": "adjudication_shim L-16 episode-native (no local accounting)",
            "segment_end_censoring": True, "censored_fraction_disclosure": True,
        },
        "emission": {
            "contract": "nautilus-emission-v1",
            "sl_price": "synthetic finite EntryFill - side * 1.0 * k * ATR14[t-1]",
            "live_stop_order": False, "catalog_version": CATALOG_VERSION,
            "runs_root": str(RUNS_ROOT.relative_to(REPO)),
        },
        "cost_note": {
            "spread_label": "GAP", "spread_bps": GAP_SPREAD_BPS,
            "per_symbol_spread": "NOT_MEASURABLE_ON_T1 — OHLCV-only catalog has no pseudo-quote "
                                 "series; INFR-014 cost_pins pin GAP 5.0 for synthetic TRAIN "
                                 "banks; per-symbol medians deferred to pilot/T2 (design §6/§11)",
        },
        "trade_sizes": {s: trade_size_for(s) for s in symbols},
        "candidates": candidates,
    }


def main() -> int:
    manifest = build_manifest()
    text = json.dumps(manifest, indent=2, sort_keys=False) + "\n"
    (RUNS_ROOT / "universe_manifest.json").write_text(text, encoding="utf-8")
    (RESULTS / "universe_manifest.json").write_text(text, encoding="utf-8")
    (RESULTS / "stage_bands.json").write_text(
        json.dumps(manifest["stage_bands"], indent=2) + "\n", encoding="utf-8")
    print(
        f"WROTE universe_manifest  n={manifest['n_candidates']} "
        f"binding={manifest['n_binding']} symbols={manifest['n_symbols']}"
    )
    print(f"  symbols: {[a['symbol'] for a in manifest['instruments']['symbol_axis']]}")
    print(
        f"  content_pin={manifest['registry']['sha256_content_pin']} "
        f"match_design={manifest['registry']['sha256_match_design']}"
    )
    sb = manifest["stage_bands"]
    print(f"  TRAIN   {sb['train_start_utc']} → {sb['train_end_utc']}  (holdout {sb['holdout_start_utc']} SEALED)")
    print(f"  search  {sb['search']['start_utc']} → {sb['search']['end_utc']}")
    print(f"  ranking {sb['ranking']['start_utc']} → {sb['ranking']['end_utc']}")
    print(f"  stage2  {sb['stage2_gate']['start_utc']} → {sb['stage2_gate']['end_utc']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
