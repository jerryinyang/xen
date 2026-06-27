"""EXP-091 — RSI-2 Fade Exit / Capture-Geometry Screen (TRAIN-only, gross + EXP-085 cost).

Phase 021 / ``CF-MR-001`` / HYP-002 — the TRAIN-only exit/capture-geometry screen (design §4 EXP-091).
Governing design/D0: ``docs/experiments-docs/checkpoints/2026-06-23-021-mr-fade-capture-geometry/``
(``design.md`` §3-4; ``D0-predeclarations.md`` D2-D6; ``D0-amendment-001`` ATR-barrier time-barrier +
counted-read clarifications; ``D0-amendment-002`` 1m fill-engine + Null-B fixes; ``D0-amendment-003`` the
Phase-021 cost table). TRAIN sub-split only (first 49% per file); **0 candidate slots, 0 counted TEST
reads, holdout never loaded**.

What this is. The first Phase-021 experiment to **resolve the real bare-fade exit outcomes** (EXP-090 never
read them). For each of the **20 EXP-090 MEMBER cells** and each frozen exit arm it computes gross and net
(post-EXP-085-cost) per-event expectancy in ATR(14) units on real prices, applies the frozen D6 net-clear +
quorum rule, and reports the native-vs-contrast attribution.

Binding screen rule (D6/4a). An (exit x cell) **net-clears** iff its net per-event expectancy moving-block
bootstrap one-sided lower bound (``ci_low_1s``, Z=1.645) > 0. An exit **PASSES** iff it net-clears in >= 5
cells over >= 3 instruments. Empty screen => ``SCREEN_EMPTY`` -> routes G-021 NOT_TRADABLE at 0 TEST reads.

Substrate reuse (verbatim). The per-cell context build, the per-arm favourable-level construction, and the
1-minute intrabar resolution are imported **unchanged** from the validated EXP-090 module (``build_cell_context``,
``resolve_arm``, ``CellContext``) so the entry/exit substrate is byte-identical to EXP-090's readiness pass.
Only the additions here read the **real** resolved gross return, overlay cost, and compute the binding net
lower bound + quorum. The favourable partial/trail arm uses ``xen.capgeo_cost.partial_two_leg_exit`` (a
domain-bar two-leg resolver, not the 1m intrabar engine — disclosed fill-model caveat; non-primary contrast).

Cost (D3 + D0-amendment-003). Phase-021-local CONSERVATIVE round-trip ``RT_i`` (bps) + financing ``F_i = 0``
(operator decision; immaterial at the ~3-bar hold). The shared ``xen.capgeo_cost.COST_CONSTANTS`` is NOT
edited (Phase-018 integrity); only ``event_costs`` / ``holding_days`` mechanics are imported and called with
the Phase-021 ``RT_i`` and ``fin_bps_day=0.0``.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

for _thread_var in ("POLARS_MAX_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                    "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_thread_var, "1")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import polars as pl  # noqa: E402
from tqdm.auto import tqdm  # noqa: E402

from xen.ass import moving_block_bootstrap_cis  # noqa: E402
from xen.capgeo_cost import event_costs, holding_days, partial_two_leg_exit  # noqa: E402
from xen.intrabar_fill import net_return_atr  # noqa: E402
from xen.mean_reversion import mr_tempo_caps  # noqa: E402
from xen.referee_calibration import seed_for  # noqa: E402

# --------------------------------------------------------------------------- #
# Path setup + EXP-090 substrate reuse (build_cell_context / resolve_arm verbatim)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-091"
CODE_DIR = Path(__file__).resolve().parent
EXPERIMENT_DIR = CODE_DIR.parent
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
EXP090_CODE = EXPERIMENT_DIR.parent / "EXP-090" / "code" / "run_experiment.py"
EXP090_MEMBER_MAP = EXPERIMENT_DIR.parent / "EXP-090" / "results" / "member_map.csv"
EXP090_META = EXPERIMENT_DIR.parent / "EXP-090" / "results" / "run_metadata.json"


def _load_exp090() -> Any:
    """Import the validated EXP-090 module (import-safe: ``main`` guarded; reuses its substrate)."""
    if not EXP090_CODE.exists():
        raise FileNotFoundError(f"EXP-090 module missing: {EXP090_CODE}")
    spec = importlib.util.spec_from_file_location("exp090_mr_readiness", EXP090_CODE)
    if spec is None or spec.loader is None:                       # pragma: no cover - defensive
        raise ImportError(f"Could not load EXP-090 from {EXP090_CODE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


E90 = _load_exp090()

# --------------------------------------------------------------------------- #
# Constants (frozen at D0/G0 + D0-amendment-003; never tuned here)
# --------------------------------------------------------------------------- #
MASTER_SEED = E90.MASTER_SEED                            # 20260623 (shared)
DOMAINS: dict[str, int] = E90.DOMAINS                   # {"15m": 15, "1h": 60}
ATR_BARRIER_FAV_MULT = E90.ATR_BARRIER_FAV_MULT         # 1.0 x ATR (partial leg-1 favourable)
ADV_ATR_MULT = E90.ADV_ATR_MULT                         # 2.0 x ATR (partial adverse)

ENGINE_ARMS = E90.ARMS                                  # ("RCT","ERT","ATR-BARRIER","RSI-REVERT","FIXED-BAR")
PARTIAL_ARM = "PARTIAL-TRAIL"                           # EXP-059 V2A two-leg (capgeo_cost; bar-level)
ARMS = tuple(ENGINE_ARMS) + (PARTIAL_ARM,)
NATIVE_ARMS = ("RCT", "ERT")
PARTIAL_LEG_FRAC = 0.5                                  # V2A scale-out fraction (frozen)

# Phase-021 cost table (D0-amendment-003, FROZEN 2026-06-24). RT_i (bps) = CONSERVATIVE round-trip
# = 4*c_i; F_i = 0 for all (operator decision; not in the price data, immaterial at ~3-bar hold).
# Phase-021-LOCAL — the shared xen.capgeo_cost.COST_CONSTANTS is NOT mutated (Phase-018 integrity).
MR_COST_RT_BPS: dict[str, float] = {
    "EURUSD": 3.0, "GBPUSD": 4.0, "USDJPY": 4.0, "USDCHF": 4.0, "AUDUSD": 4.0, "NZDUSD": 4.5,
    "EURJPY": 6.0, "GBPJPY": 6.0, "AUDJPY": 6.0, "XAUUSD": 6.0, "USTEC": 5.0, "US2000": 6.0,
    "JP225": 6.0,
}
FIN_BPS_DAY = 0.0                                       # F = 0 (D0-amendment-003)

# Binding net-clear / quorum (D6/4a).
N_BOOT = 10_000                                         # moving-block bootstrap resamples
BOOT_ALPHA = 0.10                                       # 90% CI -> 5th pct = one-sided 95% lower (Z=1.645)
QUORUM_CELLS = 5                                        # exit passes iff net-clears in >= 5 cells ...
QUORUM_INSTRUMENTS = 3                                  # ... over >= 3 instruments
DETERMINISM_CELLS = (("USTEC", "15m"), ("EURUSD", "1h"))  # high-count 15m + 1h replay

HEADLINE_OUTPUTS = ("screen_per_cell_arm.csv", "quorum_per_arm.csv", "native_vs_contrast.csv",
                    "cost_decomposition.csv", "cost_sensitivity_faster.csv")
LOGGER = logging.getLogger(EXPERIMENT_ID)


# --------------------------------------------------------------------------- #
# Dataclasses / types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ArmResult:
    """Per (cell, arm) screen result (resolved-event statistics; ATR units, real prices)."""

    arm: str
    n_events: int
    n_resolved: int
    resolved_frac: float
    tie_break_frac: float
    terminal_mix: dict[str, float]
    holding_days_mean: float
    gross_mean: float
    gross_median: float
    net_mean: float
    net_median: float
    gross_ci_low: float
    net_ci_low: float
    net_clear: bool
    cost_txn_mean: float
    cost_fin_mean: float
    net_ci_low_faster: float
    net_per_event: np.ndarray            # resolved-event net series (for paired native-vs-contrast)


# --------------------------------------------------------------------------- #
# I/O helpers (read-only upstream dependency)
# --------------------------------------------------------------------------- #
def load_member_cells() -> list[tuple[str, str]]:
    """The 20 EXP-090 MEMBER cells (dependency gate). Hard-fail if EXP-090 is not delivered."""
    if not EXP090_MEMBER_MAP.exists() or not EXP090_META.exists():
        raise FileNotFoundError(f"dependency gate: missing EXP-090 artifacts ({EXP090_MEMBER_MAP})")
    meta = json.loads(EXP090_META.read_text())
    if "READINESS_CALIBRATION_DELIVERED" not in json.dumps(meta):
        raise ValueError("dependency gate: EXP-090 not READINESS_CALIBRATION_DELIVERED")
    mm = pl.read_csv(EXP090_MEMBER_MAP)
    members = mm.filter(pl.col("verdict") == "MEMBER")
    cells = [(r["instrument"], r["domain"]) for r in members.iter_rows(named=True)]
    missing = [c for c in cells if c[0] not in MR_COST_RT_BPS]
    if missing:                                          # fail loudly: cost table must price every member
        raise ValueError(f"cost table (D0-amendment-003) missing instruments: {sorted(set(missing))}")
    return cells


# --------------------------------------------------------------------------- #
# Pure computation — resolve real fade exits, overlay cost, net lower bound
# --------------------------------------------------------------------------- #
def _engine_arm_paths(ctx: Any, arm: str) -> tuple[np.ndarray, np.ndarray, Any]:
    """Resolve real CORE entries through an engine arm; return (gross_atr, holding_days, resolution).

    Uses the EXP-090 substrate verbatim (``resolve_arm`` -> the 1m intrabar engine). Gross is the
    direction-signed real-price ATR return off the touched fill level; holding days from the exit
    domain bar (operator-ratified bar-count proxy).
    """
    idx = ctx.core_entry_idx
    direction = ctx.core_direction
    res = E90.resolve_arm(ctx, idx, direction, arm, ctx.minute_high, ctx.minute_low, ctx.minute_open)
    gross = net_return_atr(res.fill_price, ctx.close[idx], direction, ctx.atr[idx])
    hd = holding_days(idx, res.exit_domain_idx, DOMAINS[ctx.domain])
    return gross, hd, res


def _partial_arm_paths(ctx: Any) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Resolve real CORE entries through the EXP-059 V2A two-leg partial/trail (bar-level resolver).

    Disclosed fill-model caveat: ``partial_two_leg_exit`` resolves on domain-bar high/low first-touch
    (not the 1m intrabar engine) — coarser than the other five arms, by D2.4 "as the primitive
    allows". leg-1 scale-out at 1.0xATR favourable, remainder to the shared 2.0xATR stop / MR-tempo
    cap; ``leg_frac=0.5``. Returns (gross_atr, holding_days, resolved_mask, terminal_class).
    """
    idx = ctx.core_entry_idx
    direction = ctx.core_direction
    cap, _ = mr_tempo_caps(idx, ctx.ep_close_idx, ctx.ep_durations)
    m = idx.shape[0]
    t_fav = np.full(m, ATR_BARRIER_FAV_MULT, dtype=np.float64)
    s_adv = np.full(m, ADV_ATR_MULT, dtype=np.float64)
    path = partial_two_leg_exit(ctx.high, ctx.low, ctx.close, ctx.atr[idx], idx, direction,
                                t_fav, s_adv, cap.astype(np.int64), ctx.n_domain,
                                leg_frac=PARTIAL_LEG_FRAC)
    gross = path.ret_mirror                              # already ATR units
    hd = holding_days(idx, path.exit_idx, DOMAINS[ctx.domain])
    resolved = np.isfinite(gross)
    return gross, hd, resolved, path.cls_mirror


def _net_lower_bound(series: np.ndarray, seed: int) -> tuple[float, float]:
    """(expectancy_lo, median_lo) of the moving-block bootstrap (Z=1.645 one-sided lower bound)."""
    if series.shape[0] < 2:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    ci = moving_block_bootstrap_cis(series, rng, n_boot=N_BOOT, alpha=BOOT_ALPHA)
    return float(ci.expectancy_lo), float(ci.median_lo)


def _cost_net(gross: np.ndarray, p_entry: np.ndarray, atr_entry: np.ndarray, hd: np.ndarray,
              rt_bps: float) -> Any:
    """EXP-085 conservative cost overlay -> EventCosts (net = gross - txn; F=0 so cost_fin=0)."""
    return event_costs(gross, p_entry, atr_entry, hd, rt_bps=rt_bps, fin_bps_day=FIN_BPS_DAY)


def screen_arm(ctx: Any, arm: str, rt_bps: float) -> ArmResult:
    """Resolve real fade exits for one arm, overlay cost, compute the binding net lower bound."""
    idx = ctx.core_entry_idx
    p_entry, atr_entry = ctx.close[idx], ctx.atr[idx]
    if arm == PARTIAL_ARM:
        gross, hd, resolved, cls = _partial_arm_paths(ctx)
        tie_frac = float("nan")                          # bar-level resolver: no 1m tie-break notion
        terminal = _partial_terminal_mix(cls, resolved)
    else:
        gross, hd, res = _engine_arm_paths(ctx, arm)
        resolved = res.resolved
        tie = res.tie_break[resolved]
        tie_frac = float(np.mean(tie)) if tie.shape[0] else 0.0
        terminal = _engine_terminal_mix(res.kind, resolved)
    keep = resolved & np.isfinite(gross) & np.isfinite(atr_entry) & (atr_entry > 0.0) \
        & np.isfinite(hd) & (hd >= 0.0)
    n_events, n_resolved = int(idx.shape[0]), int(np.count_nonzero(keep))
    if n_resolved < 2:                                   # cannot bootstrap -> not a net-clear
        return _empty_arm_result(arm, n_events, n_resolved, tie_frac, terminal)
    g = gross[keep]
    costs = _cost_net(g, p_entry[keep], atr_entry[keep], hd[keep], rt_bps)
    costs_fast = _cost_net(g, p_entry[keep], atr_entry[keep], hd[keep], rt_bps / 2.0)  # 1xBASE companion
    net = costs.net
    gross_lo, _ = _net_lower_bound(g, seed_for(EXPERIMENT_ID, ctx.instrument, ctx.domain, arm, "gross"))
    net_lo, net_med_lo = _net_lower_bound(
        net, seed_for(EXPERIMENT_ID, ctx.instrument, ctx.domain, arm, "net"))
    net_fast_lo, _ = _net_lower_bound(
        costs_fast.net, seed_for(EXPERIMENT_ID, ctx.instrument, ctx.domain, arm, "net_faster"))
    return ArmResult(
        arm=arm, n_events=n_events, n_resolved=n_resolved,
        resolved_frac=float(np.mean(resolved)), tie_break_frac=tie_frac, terminal_mix=terminal,
        holding_days_mean=float(np.mean(hd[keep])), gross_mean=float(np.mean(g)),
        gross_median=float(np.median(g)), net_mean=float(np.mean(net)),
        net_median=float(np.median(net)), gross_ci_low=gross_lo, net_ci_low=net_lo,
        net_clear=bool(net_lo > 0.0), cost_txn_mean=float(np.mean(costs.cost_txn)),
        cost_fin_mean=float(np.mean(costs.cost_fin)), net_ci_low_faster=net_fast_lo,
        net_per_event=net)


def _empty_arm_result(arm: str, n_events: int, n_resolved: int, tie_frac: float,
                      terminal: dict[str, float]) -> ArmResult:
    """UNRESOLVED_EMPTY / too-thin arm: reported with denominators, never a net-clear."""
    nan = float("nan")
    return ArmResult(arm=arm, n_events=n_events, n_resolved=n_resolved,
                     resolved_frac=(n_resolved / n_events if n_events else nan),
                     tie_break_frac=tie_frac, terminal_mix=terminal, holding_days_mean=nan,
                     gross_mean=nan, gross_median=nan, net_mean=nan, net_median=nan,
                     gross_ci_low=nan, net_ci_low=nan, net_clear=False, cost_txn_mean=nan,
                     cost_fin_mean=nan, net_ci_low_faster=nan, net_per_event=np.empty(0))


def _engine_terminal_mix(kind: np.ndarray, resolved: np.ndarray) -> dict[str, float]:
    """Fraction of resolved events ending FAV / ADV / CAP (1m engine kinds)."""
    k = kind[resolved]
    n = int(k.shape[0])
    if n == 0:
        return {"fav": float("nan"), "adv": float("nan"), "cap": float("nan")}
    from xen.intrabar_fill import KIND_ADV, KIND_CAP, KIND_FAV
    return {"fav": float(np.mean(k == KIND_FAV)), "adv": float(np.mean(k == KIND_ADV)),
            "cap": float(np.mean(k == KIND_CAP))}


def _partial_terminal_mix(cls: np.ndarray, resolved: np.ndarray) -> dict[str, float]:
    """Fraction of resolved partial events FAV (leg-1 taken) vs TIMECAP (capgeo classes)."""
    from xen.capgeo_screen import CLASS_FAV, CLASS_TIMECAP
    c = cls[resolved]
    n = int(c.shape[0])
    if n == 0:
        return {"fav": float("nan"), "timecap": float("nan")}
    return {"fav": float(np.mean(c == CLASS_FAV)), "timecap": float(np.mean(c == CLASS_TIMECAP))}


# --------------------------------------------------------------------------- #
# Per-cell orchestration
# --------------------------------------------------------------------------- #
def compute_cell(cell: tuple[str, str], path: Path) -> dict[str, Any]:
    """Resolve + cost + net-lower-bound every arm on one member cell."""
    instrument, domain = cell
    train_1m, meta = E90.load_train_1m(instrument, path)
    ctx, dropped, status = E90.build_cell_context(train_1m, instrument, domain)
    base = {"cell": f"{instrument}-{domain}", "instrument": instrument, "domain": domain}
    if ctx is None:                                      # a member cell must build (EXP-090 guarantee)
        raise RuntimeError(f"{instrument}-{domain}: member cell failed to build ({status})")
    rt = MR_COST_RT_BPS[instrument]
    arms = {arm: screen_arm(ctx, arm, rt) for arm in ARMS}
    return {**base, "rt_bps": rt, "n_core": int(ctx.core_entry_idx.shape[0]), "arms": arms}


# --------------------------------------------------------------------------- #
# Aggregation — quorum, native-vs-contrast attribution
# --------------------------------------------------------------------------- #
def quorum_per_arm(results: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Per arm: net-clearing cell count + distinct instruments; PASS iff >=5 cells / >=3 instruments."""
    out: dict[str, dict[str, Any]] = {}
    for arm in ARMS:
        clearing = [(r["instrument"], r["cell"]) for r in results if r["arms"][arm].net_clear]
        n_cells = len(clearing)
        n_instr = len({i for i, _ in clearing})
        out[arm] = {"n_clearing_cells": n_cells, "n_clearing_instruments": n_instr,
                    "passes": bool(n_cells >= QUORUM_CELLS and n_instr >= QUORUM_INSTRUMENTS),
                    "clearing_cells": sorted(c for _, c in clearing)}
    return out


def native_vs_contrast(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Descriptive (non-binding): per-cell paired net-mean deltas, native vs reactive contrast.

    Headline A/B = RCT vs RSI-revert-on-close (proactive intrabar resting vs reactive exit-on-close),
    paired by cell. Wilcoxon signed-rank if SciPy is present, else a deterministic sign-test fallback;
    both are disclosure only and never gate the verdict.
    """
    rows = []
    for r in results:
        rct, rsi = r["arms"]["RCT"], r["arms"]["RSI-REVERT"]
        if np.isfinite(rct.net_mean) and np.isfinite(rsi.net_mean):
            rows.append({"cell": r["cell"], "instrument": r["instrument"],
                         "net_RCT": rct.net_mean, "net_RSIREVERT": rsi.net_mean,
                         "delta_RCT_minus_RSIREVERT": rct.net_mean - rsi.net_mean})
    deltas = np.array([x["delta_RCT_minus_RSIREVERT"] for x in rows], dtype=np.float64)
    summary: dict[str, Any] = {"n_paired": int(deltas.shape[0]),
                               "median_delta": float(np.median(deltas)) if deltas.size else float("nan"),
                               "n_RCT_gt_RSIREVERT": int(np.count_nonzero(deltas > 0))}
    if deltas.size >= 2:
        try:
            from scipy.stats import wilcoxon
            stat, p = wilcoxon(deltas)
            summary["wilcoxon_stat"], summary["wilcoxon_p"] = float(stat), float(p)
            summary["test"] = "wilcoxon_signed_rank"
        except Exception:                                # deterministic sign-test fallback
            k, n = int(np.count_nonzero(deltas > 0)), int(np.count_nonzero(deltas != 0))
            summary["sign_test_k"], summary["sign_test_n"] = k, n
            summary["test"] = "sign_test (scipy unavailable)"
    # native vs contrast net-clear counts (descriptive)
    summary["native_clear_cells"] = {a: sum(1 for r in results if r["arms"][a].net_clear)
                                      for a in NATIVE_ARMS}
    summary["contrast_clear_cells"] = {a: sum(1 for r in results if r["arms"][a].net_clear)
                                       for a in ARMS if a not in NATIVE_ARMS}
    return {"rows": rows, "summary": summary}


# --------------------------------------------------------------------------- #
# Determinism + hashing
# --------------------------------------------------------------------------- #
def determinism_replay(results: dict[tuple[str, str], dict[str, Any]],
                       files: dict[str, Path]) -> dict[str, Any]:
    """Re-run two member cells; assert net_ci_low / net_clear frame-identical (D9)."""
    checked, mismatches = [], []
    for cell in DETERMINISM_CELLS:
        if cell not in results:
            continue
        checked.append(f"{cell[0]}-{cell[1]}")
        b = compute_cell(cell, files[cell[0]])
        a = results[cell]
        for arm in ARMS:
            if not _arm_equal(a["arms"][arm], b["arms"][arm]):
                mismatches.append(f"{cell[0]}-{cell[1]}/{arm}")
    return {"determinism_pass": not mismatches, "cells_checked": checked,
            "non_deterministic": mismatches}


def _arm_equal(a: ArmResult, b: ArmResult) -> bool:
    return (a.net_clear == b.net_clear and _eq(a.net_ci_low, b.net_ci_low)
            and _eq(a.gross_ci_low, b.gross_ci_low) and a.n_resolved == b.n_resolved)


def _eq(a: float, b: float) -> bool:
    return bool(a == b or (np.isnan(a) and np.isnan(b)))


def hash_outputs() -> dict[str, str]:
    """SHA-256 of each headline output (byte-identical second-pass pin)."""
    out: dict[str, str] = {}
    for name in HEADLINE_OUTPUTS:
        p = RESULTS_DIR / name
        if p.exists():
            out[name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def cost_table_hash() -> str:
    """Provenance hash of the Phase-021 cost table (D0-amendment-003)."""
    payload = json.dumps({"RT": MR_COST_RT_BPS, "F": FIN_BPS_DAY}, sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()


# --------------------------------------------------------------------------- #
# Output writers
# --------------------------------------------------------------------------- #
def write_outputs(results: list[dict[str, Any]], quorum: dict[str, dict[str, Any]],
                  nvc: dict[str, Any]) -> None:
    """Flatten to the headline CSV tables."""
    screen_rows, cost_rows, faster_rows = [], [], []
    for r in results:
        for arm in ARMS:
            a = r["arms"][arm]
            screen_rows.append({
                "cell": r["cell"], "instrument": r["instrument"], "domain": r["domain"], "arm": arm,
                "n_events": a.n_events, "n_resolved": a.n_resolved, "resolved_frac": a.resolved_frac,
                "tie_break_frac": a.tie_break_frac, "holding_days_mean": a.holding_days_mean,
                "gross_mean": a.gross_mean, "gross_median": a.gross_median, "net_mean": a.net_mean,
                "net_median": a.net_median, "gross_ci_low": a.gross_ci_low,
                "net_ci_low": a.net_ci_low, "net_clear": a.net_clear,
                **{f"terminal_{k}": v for k, v in a.terminal_mix.items()}})
            cost_rows.append({"cell": r["cell"], "instrument": r["instrument"], "arm": arm,
                              "rt_bps": r["rt_bps"], "cost_txn_mean": a.cost_txn_mean,
                              "cost_fin_mean": a.cost_fin_mean, "gross_mean": a.gross_mean,
                              "net_mean": a.net_mean})
            faster_rows.append({"cell": r["cell"], "instrument": r["instrument"], "arm": arm,
                                "net_ci_low": a.net_ci_low, "net_ci_low_faster": a.net_ci_low_faster,
                                "net_clear": a.net_clear,
                                "net_clear_faster": bool(a.net_ci_low_faster > 0.0)})
    pl.DataFrame(screen_rows).write_csv(RESULTS_DIR / "screen_per_cell_arm.csv")
    pl.DataFrame([{"arm": a, **quorum[a]} for a in ARMS]).with_columns(
        pl.col("clearing_cells").list.join("|")).write_csv(RESULTS_DIR / "quorum_per_arm.csv")
    pl.DataFrame(cost_rows).write_csv(RESULTS_DIR / "cost_decomposition.csv")
    pl.DataFrame(faster_rows).write_csv(RESULTS_DIR / "cost_sensitivity_faster.csv")
    nvc_rows = nvc["rows"] or [{"cell": None, "instrument": None, "net_RCT": None,
                                "net_RSIREVERT": None, "delta_RCT_minus_RSIREVERT": None}]
    pl.DataFrame(nvc_rows).write_csv(RESULTS_DIR / "native_vs_contrast.csv")


# --------------------------------------------------------------------------- #
# Plotting (<=4 bounded plots from collected summaries; no reloads)
# --------------------------------------------------------------------------- #
def make_plots(results: list[dict[str, Any]], quorum: dict[str, dict[str, Any]],
               nvc: dict[str, Any]) -> None:
    _plot_quorum(quorum)
    _plot_net_ci_heatmap(results)
    _plot_cost_decomposition(results)
    _plot_rct_vs_rsirevert(nvc)


def _plot_quorum(quorum: dict[str, dict[str, Any]]) -> None:
    arms = list(ARMS)
    cells = [quorum[a]["n_clearing_cells"] for a in arms]
    instr = [quorum[a]["n_clearing_instruments"] for a in arms]
    x = np.arange(len(arms))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(x - 0.2, cells, 0.4, label="net-clearing cells", color="steelblue")
    ax.bar(x + 0.2, instr, 0.4, label="distinct instruments", color="darkorange")
    ax.axhline(QUORUM_CELLS, color="steelblue", ls="--", lw=1, label=f"cell quorum={QUORUM_CELLS}")
    ax.axhline(QUORUM_INSTRUMENTS, color="darkorange", ls="--", lw=1,
               label=f"instr quorum={QUORUM_INSTRUMENTS}")
    ax.set_xticks(x, arms, rotation=30, ha="right", fontsize=8)
    ax.set_title("EXP-091 per-arm net-clear quorum (net ci_low>0)", fontsize=10)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "quorum_per_arm.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_net_ci_heatmap(results: list[dict[str, Any]]) -> None:
    cells = [r["cell"] for r in results]
    arr = np.full((len(cells), len(ARMS)), np.nan)
    for ci, r in enumerate(results):
        for ai, arm in enumerate(ARMS):
            arr[ci, ai] = r["arms"][arm].net_ci_low
    vmax = float(np.nanmax(np.abs(arr))) if np.isfinite(arr).any() else 1.0
    fig, ax = plt.subplots(figsize=(7, 9))
    im = ax.imshow(arr, aspect="auto", cmap="RdYlGn", vmin=-vmax, vmax=vmax)
    ax.set_xticks(range(len(ARMS)), ARMS, rotation=30, ha="right", fontsize=8)
    ax.set_yticks(range(len(cells)), cells, fontsize=6)
    ax.set_title("EXP-091 net ci_low_1s (ATR); green>0=net-clear", fontsize=9)
    fig.colorbar(im, ax=ax, fraction=0.04)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "net_ci_low_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_cost_decomposition(results: list[dict[str, Any]]) -> None:
    arms = list(ARMS)
    gross = [np.nanmean([r["arms"][a].gross_mean for r in results]) for a in arms]
    net = [np.nanmean([r["arms"][a].net_mean for r in results]) for a in arms]
    txn = [np.nanmean([r["arms"][a].cost_txn_mean for r in results]) for a in arms]
    x = np.arange(len(arms))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(x - 0.2, gross, 0.4, label="gross mean (ATR)", color="seagreen")
    ax.bar(x + 0.2, net, 0.4, label="net mean (ATR)", color="indianred")
    ax.plot(x, txn, "k.", label="mean txn cost (ATR)")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x, arms, rotation=30, ha="right", fontsize=8)
    ax.set_title("EXP-091 gross->net per-arm (cell-averaged; F=0)", fontsize=10)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "cost_decomposition.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_rct_vs_rsirevert(nvc: dict[str, Any]) -> None:
    rows = nvc["rows"]
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    if rows:
        xr = np.array([x["net_RSIREVERT"] for x in rows])
        yr = np.array([x["net_RCT"] for x in rows])
        ax.scatter(xr, yr, color="purple", s=25)
        lim = [float(np.nanmin([xr.min(), yr.min(), 0])), float(np.nanmax([xr.max(), yr.max(), 0]))]
        ax.plot(lim, lim, "k--", lw=1, label="y=x")
        ax.axhline(0, color="grey", lw=0.6)
        ax.axvline(0, color="grey", lw=0.6)
    ax.set_xlabel("net mean — RSI-revert-on-close (ATR)")
    ax.set_ylabel("net mean — RCT (ATR)")
    ax.set_title("EXP-091 RCT vs RSI-revert (intrabar A/B)", fontsize=10)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "rct_vs_rsirevert.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def experiment_verdict(quorum: dict[str, dict[str, Any]], determinism: dict[str, Any]) -> str:
    """SCREEN_DELIVERED (+ SCREEN_EMPTY if no arm passes); HALT on non-determinism."""
    if not determinism["determinism_pass"]:
        return "HALT_NON_DETERMINISM"
    any_pass = any(q["passes"] for q in quorum.values())
    return "SCREEN_DELIVERED" if any_pass else "SCREEN_DELIVERED_EMPTY"


def run(limit: int | None = None) -> dict[str, Any]:
    """Screen the frozen exit slate on the 20 EXP-090 member cells (TRAIN-only, gross + cost)."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    cells = load_member_cells()
    if limit:
        cells = cells[:limit]
    files, _ = E90.VAL005.discover_infr003_files()
    files = {k.upper(): v for k, v in files.items()}
    for cell in cells:
        if cell[0] not in files:
            raise FileNotFoundError(f"no INFR-003 file for {cell[0]}")
    by_cell: dict[tuple[str, str], dict[str, Any]] = {}
    for cell in tqdm(cells, desc="member cells", unit="cell", dynamic_ncols=True):
        t0 = time.perf_counter()
        by_cell[cell] = compute_cell(cell, files[cell[0]])
        LOGGER.info("cell %s-%s done in %.1fs", cell[0], cell[1], time.perf_counter() - t0)
    results = [by_cell[c] for c in cells]
    quorum = quorum_per_arm(results)
    nvc = native_vs_contrast(results)
    determinism = determinism_replay(by_cell, files)
    verdict = experiment_verdict(quorum, determinism)
    write_outputs(results, quorum, nvc)
    make_plots(results, quorum, nvc)
    meta = _build_metadata(cells, quorum, nvc, determinism, verdict)
    meta["output_hashes"] = hash_outputs()
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(meta, indent=2, default=str))
    _log_summary(quorum, nvc, verdict, determinism)
    return meta


def _build_metadata(cells: list[tuple[str, str]], quorum: dict[str, dict[str, Any]],
                    nvc: dict[str, Any], determinism: dict[str, Any], verdict: str) -> dict[str, Any]:
    return {
        "experiment_id": EXPERIMENT_ID, "phase": "021", "family": "CF-MR-001", "hyp": "HYP-002",
        "generated_utc": datetime.now(timezone.utc).isoformat(), "experiment_verdict": verdict,
        "master_seed": MASTER_SEED, "n_member_cells": len(cells),
        "member_cells": [f"{i}-{d}" for i, d in cells], "arms": list(ARMS),
        "native_arms": list(NATIVE_ARMS), "n_boot": N_BOOT, "boot_alpha": BOOT_ALPHA,
        "z_one_sided": 1.645, "quorum_cells": QUORUM_CELLS, "quorum_instruments": QUORUM_INSTRUMENTS,
        "cost_model": "EXP-085 CONSERVATIVE RT (D0-amendment-003 Phase-021 table); F=0",
        "cost_rt_bps": MR_COST_RT_BPS, "fin_bps_day": FIN_BPS_DAY,
        "cost_table_hash": cost_table_hash(),
        "cost_table_note": ("Phase-021-LOCAL (D0-amendment-003, FROZEN 2026-06-24); shared "
                            "xen.capgeo_cost.COST_CONSTANTS NOT mutated (Phase-018 integrity). "
                            "Global OHLC-spread RT rule attempted + empirically refuted (see amendment)."),
        "partial_arm_note": ("PARTIAL-TRAIL uses xen.capgeo_cost.partial_two_leg_exit (domain-bar "
                             "two-leg resolver), NOT the 1m intrabar engine — disclosed coarser "
                             "fill model for this non-primary contrast arm (D2.4 'as the primitive allows')."),
        "quorum_per_arm": {a: {k: v for k, v in quorum[a].items() if k != "clearing_cells"}
                           for a in ARMS},
        "any_arm_passes": any(q["passes"] for q in quorum.values()),
        "native_vs_contrast_summary": nvc["summary"], "determinism": determinism,
        "real_fade_outcomes_resolved": True, "holdout_untouched": True,
        "counted_test_reads": 0, "candidate_slots": 0,
        "exp090_member_map": str(EXP090_MEMBER_MAP),
    }


def _log_summary(quorum: dict[str, dict[str, Any]], nvc: dict[str, Any], verdict: str,
                 determinism: dict[str, Any]) -> None:
    passes = [a for a in ARMS if quorum[a]["passes"]]
    LOGGER.info("EXP-091 verdict=%s | passing arms=%s | det=%s", verdict, passes or "NONE",
                determinism["determinism_pass"])
    for a in ARMS:
        q = quorum[a]
        LOGGER.info("  %-13s net-clear %2d cells / %d instr  -> %s", a, q["n_clearing_cells"],
                    q["n_clearing_instruments"], "PASS" if q["passes"] else "fail")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description="EXP-091 exit/capture-geometry screen (TRAIN-only)")
    ap.add_argument("--limit", type=int, default=None, help="limit member cells (smoke test)")
    args = ap.parse_args()
    meta = run(limit=args.limit)
    print(f"EXP-091 complete: verdict={meta['experiment_verdict']} "
          f"passing_arms={[a for a in ARMS if meta['quorum_per_arm'][a]['passes']]} "
          f"determinism={meta['determinism']['determinism_pass']}")


if __name__ == "__main__":
    main()
