"""EXP-094 — 4h Readiness + Falsification Re-Screen (RSI-2 fade / EXIT-RCT).

Phase 021 (CF-MR-001 batch 2) / CF-MR-001/HYP-002 / governed by D0-amendment-004 (4h opened, gated)
and D0-amendment-005 (binding falsification null corrected to the matched-distance oscillation null).
TRAIN-only; 0 candidate slots; 0 counted TEST reads; holdout sealed; real OHLC; deterministic.

Three legs + positive control + bite-check (analysis-plan Steps a/b/c/d/e):
  (a) READINESS  — 4h member readiness + per-cell finite EXIT-RCT MDE under the frozen referee
                   (EXP-090 analog; reuses E90.compute_cell verbatim). MEMBER vs COVERAGE_EXCLUDED.
  (b) NET SCREEN — frozen 6-arm exit slate on members, D0-amendment-003 cost, net ci_low_1s, D6/4a
                   quorum (>=5 cells / >=3 instruments). EXP-091 analog.
  (c) FALSIFICATION (binding, D0-amendment-005) — matched favourable-target-distance OSCILLATION null:
                   a static favourable limit at a distance resampled from the real cell's RCT target
                   multiples {mu_k}, fired at random eligible bars / shuffled directions, same adverse
                   side + 1m fill + cost (favourable BY CONSTRUCTION -> no wrong-side instant-fill).
                   real EXIT-RCT must beat it (paired-Delta two-sample moving-block lower bound > 0)
                   in >=5 cells / >=3 instruments. Companion (NON-binding): SUB-RANDOM-entry RCT null
                   with the wrong-side guard (reports wrongside_frac).
  (d) POSITIVE CONTROL — the same matched-distance contrast on the EXP-091 1h clearing cells (power).
  (e) BITE-CHECK — GREEN/RED calibration of the matched-distance paired-Delta statistic (FPR under a
                   same-distribution null + power at the planted per-cell MDE). Must be GREEN at D0.

Substrate reuse (verbatim). The EXP-090 module (substrate build, RCT/ATR-BARRIER favourable-level
construction, the 1-minute intrabar fill engine, the readiness/MDE calibration) is imported unchanged;
4h is patched into a local DOMAINS reference (240-minute) exactly as the archived TEMP-091 hunch did.
The matched-random draw uses the EXP-090 ``eligible_pool`` (look-ahead-safe, real-CORE-entry-fenced) —
the SUB-RANDOM matched-random set the plan intends, cleaner than random_entries over all bars.
Cost: D0-amendment-003 Phase-021-local table (RT_i; F=0); shared xen.capgeo_cost.COST_CONSTANTS NOT mutated.
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

from xen.ass import default_block_length, moving_block_bootstrap_cis  # noqa: E402
from xen.capgeo_cost import event_costs, holding_days  # noqa: E402
from xen.intrabar_fill import (KIND_ADV, KIND_CAP, KIND_FAV, net_return_atr,  # noqa: E402
                               resolve_exit_paths)
from xen.mean_reversion import mr_tempo_caps  # noqa: E402
from xen.referee_calibration import seed_for  # noqa: E402

# --------------------------------------------------------------------------- #
# Path setup + EXP-090 substrate reuse (import the module directly; TEMP-091 archived)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-094"
CODE_DIR = Path(__file__).resolve().parent
EXPERIMENT_DIR = CODE_DIR.parent
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
READINESS_CACHE_DIR = RESULTS_DIR / "readiness_cache"
EXP090_CODE = EXPERIMENT_DIR.parent / "EXP-090" / "code" / "run_experiment.py"
READINESS_CONST_VERSION = "v1"                          # bump to invalidate the cache on a readiness-logic change


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
E90.DOMAINS["4h"] = 240                                  # patch 4h (240-min); not native (EXP-089 excl.)

# --------------------------------------------------------------------------- #
# Constants (frozen at D0 / G0 + D0-amendment-003/004/005; never tuned here)
# --------------------------------------------------------------------------- #
MASTER_SEED = E90.MASTER_SEED                            # 20260623 (shared)
LONG = E90.LONG                                          # +1
ADV_ATR_MULT = E90.ADV_ATR_MULT                          # 2.0 x ATR adverse stop (D2.3)
MR_CAP_MAX = E90.MR_CAP_MAX                              # max offset horizon
ENGINE_ARMS = E90.ARMS                                   # ("RCT","ERT","ATR-BARRIER","RSI-REVERT","FIXED-BAR")
ARMS = tuple(ENGINE_ARMS)                                # leg (b) screens the engine arms (no partial/trail)
PRIMARY_ARM = "RCT"                                      # the binding capture geometry

# Phase-021 cost table (D0-amendment-003, FROZEN 2026-06-24). RT_i (bps) CONSERVATIVE = 4*c_i; F_i=0.
MR_COST_RT_BPS: dict[str, float] = {
    "EURUSD": 3.0, "GBPUSD": 4.0, "USDJPY": 4.0, "USDCHF": 4.0, "AUDUSD": 4.0, "NZDUSD": 4.5,
    "EURJPY": 6.0, "GBPJPY": 6.0, "AUDJPY": 6.0, "XAUUSD": 6.0, "USTEC": 5.0, "US2000": 6.0,
    "JP225": 6.0,
}
FIN_BPS_DAY = 0.0                                        # F = 0 (D0-amendment-003)

# Binding net-clear / quorum (D6/4a) and falsification quorum (D0-amendment-004/005 §4).
N_BOOT = 10_000
BOOT_ALPHA = 0.10                                        # 90% CI -> 5th pct = one-sided 95% lower (Z=1.645)
QUORUM_CELLS = 5
QUORUM_INSTRUMENTS = 3
DOMAIN_4H = "4h"
CONTROL_1H_CELLS = ("EURUSD", "GBPUSD", "NZDUSD", "US2000", "USTEC")   # EXP-091 1h clearing cells
DETERMINISM_CELLS = (("EURUSD", "4h"), ("GBPUSD", "4h"))

# Bite-check (e) of the matched-distance paired-Delta statistic (calibration; no market verdict read).
# Corrected per audit §4 (D0-amendment-005 statistic): the power leg evaluates PER-CELL detection at a
# fixed material reference effect (not the sub-threshold single-arm MDE, and not quorum-compounded).
BITE_REPLICATES = 300                                    # synthetic ensemble reshuffles
BITE_NBOOT = 2_000                                       # reduced bootstrap for the calibration loop
BITE_FPR_MAX = 0.10                                      # quorum-fire FPR ceiling under same-dist null
BITE_FPR_CELL_MAX = 0.10                                 # per-cell FPR ceiling (one-sided alpha)
BITE_PLANT_GRID = (0.05, 0.10, 0.15, 0.20)               # planted real-over-null effects (ATR)
BITE_POWER_REF_ATR = 0.10                                # fixed material reference effect (a priori; no peek)
BITE_TPR_TARGET = 0.80                                   # per-cell detection floor at the reference effect

HEADLINE_OUTPUTS = ("readiness_4h.csv", "screen_per_cell_arm_4h.csv", "quorum_per_arm_4h.csv",
                    "falsification_paired_delta_4h.csv", "falsification_quorum.csv",
                    "positive_control_1h.csv", "cost_decomposition_4h.csv")
LOGGER = logging.getLogger(EXPERIMENT_ID)


# --------------------------------------------------------------------------- #
# Dataclasses / types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ArmNet:
    """Per (cell, arm) net-screen result (resolved-event statistics; ATR units, real prices)."""

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
    net_ci_low_faster: float
    net_per_event: np.ndarray


# --------------------------------------------------------------------------- #
# I/O helpers (read-only upstream dependency)
# --------------------------------------------------------------------------- #
def member_universe() -> list[str]:
    """Cost-table instruments (the 4h candidate universe; readiness leg (a) defines membership)."""
    return sorted(MR_COST_RT_BPS)


def discover_files() -> dict[str, Path]:
    """INFR-003 file map (upper-cased instrument keys), via the EXP-090/VAL-005 discovery."""
    files, _ = E90.VAL005.discover_infr003_files()
    return {k.upper(): v for k, v in files.items()}


# --------------------------------------------------------------------------- #
# Pure computation — cost overlay, bootstrap lower bounds, two-sample paired-Delta
# --------------------------------------------------------------------------- #
def _net_after_cost(gross: np.ndarray, p_entry: np.ndarray, atr_entry: np.ndarray,
                    hd: np.ndarray, rt_bps: float) -> np.ndarray:
    """EXP-085 conservative cost overlay -> net per-event (F=0 so cost is RT-only)."""
    return event_costs(gross, p_entry, atr_entry, hd, rt_bps=rt_bps, fin_bps_day=FIN_BPS_DAY).net


def _mblock_lower(series: np.ndarray, seed: int, *, n_boot: int = N_BOOT) -> float:
    """One-sided 5th-pct moving-block bootstrap lower bound of the mean (Z=1.645)."""
    if series.shape[0] < 2:
        return float("nan")
    ci = moving_block_bootstrap_cis(series, np.random.default_rng(seed), n_boot=n_boot,
                                    alpha=BOOT_ALPHA)
    return float(ci.expectancy_lo)


def _mblock_diff_lower(x_real: np.ndarray, x_rand: np.ndarray, seed: int,
                       *, n_boot: int = N_BOOT) -> float:
    """One-sided lower bound of (mean(x_real) - mean(x_rand)) by an independent two-sample moving-block
    bootstrap of the difference of means (5th pct, Z=1.645). Mirrors moving_block_bootstrap_cis: each
    arm resampled by overlapping length-b blocks (b = round(n**(1/3))), differences read from paired
    resamples. Fully determined by ``seed``. NaN when either arm has < 2 events.
    """
    nr, ns = x_real.shape[0], x_rand.shape[0]
    if nr < 2 or ns < 2:
        return float("nan")
    rng = np.random.default_rng(seed)
    dr = _block_means(x_real, n_boot, rng)
    ds = _block_means(x_rand, n_boot, rng)
    return float(np.percentile(dr - ds, 100.0 * BOOT_ALPHA / 2.0))


def _block_means(x: np.ndarray, n_boot: int, rng: np.random.Generator) -> np.ndarray:
    """Vector of ``n_boot`` moving-block resample means (programme block length b=round(n**(1/3)))."""
    x = np.asarray(x, dtype=np.float64)
    n = x.shape[0]
    b = int(min(max(1, default_block_length(n)), n))
    n_starts, n_blocks = n - b + 1, int(np.ceil(n / b))
    starts = rng.integers(0, n_starts, size=(n_boot, n_blocks))
    idx = (starts[:, :, None] + np.arange(b)[None, None, :]).reshape(n_boot, n_blocks * b)[:, :n]
    return x[idx].mean(axis=1)


# --------------------------------------------------------------------------- #
# Pure computation — arm resolution (real engine arms + the custom null arms)
# --------------------------------------------------------------------------- #
def _resolve_engine_arm(ctx: Any, idx: np.ndarray, direction: np.ndarray,
                        arm: str) -> tuple[np.ndarray, np.ndarray, Any]:
    """Resolve (idx, direction) through a frozen engine arm (EXP-090 resolve_arm). -> gross, hd, res."""
    res = E90.resolve_arm(ctx, idx, direction, arm, ctx.minute_high, ctx.minute_low, ctx.minute_open)
    gross = net_return_atr(res.fill_price, ctx.close[idx], direction, ctx.atr[idx])
    hd = holding_days(idx, res.exit_domain_idx, E90.DOMAINS[ctx.domain])
    return gross, hd, res


def _resolve_custom_fav(ctx: Any, idx: np.ndarray, direction: np.ndarray,
                        fav_level: np.ndarray) -> tuple[np.ndarray, np.ndarray, Any]:
    """Resolve (idx, direction) with a caller-supplied favourable-level array through the same engine.

    Adverse side (2*ATR stop + MR-tempo cap) and the 1m fill engine are identical to every frozen arm;
    only ``fav_level`` (shape (m, MR_CAP_MAX)) is supplied by the caller (matched-distance static limit
    or wrong-side-masked RCT). No domain-close favourable condition (``fav_close_fire`` all False).
    """
    cap, _ = mr_tempo_caps(idx, ctx.ep_close_idx, ctx.ep_durations)
    entry_close, atr_e = ctx.close[idx], ctx.atr[idx]
    adv_level = entry_close - direction.astype(np.float64) * ADV_ATR_MULT * atr_e
    fav_fire = np.zeros((idx.shape[0], MR_CAP_MAX), dtype=bool)
    res = resolve_exit_paths(
        minute_high=ctx.minute_high, minute_low=ctx.minute_low, minute_open=ctx.minute_open,
        minute_close_epoch=ctx.minute_close_epoch, domain_close_epoch=ctx.domain_close_epoch,
        domain_close_price=ctx.close, entry_idx=idx, direction=direction, adv_level=adv_level,
        cap=cap, fav_level=fav_level, fav_close_fire=fav_fire,
        train_edge_epoch=ctx.train_edge_epoch, period_s=E90.DOMAINS[ctx.domain] * 60)
    gross = net_return_atr(res.fill_price, entry_close, direction, atr_e)
    hd = holding_days(idx, res.exit_domain_idx, E90.DOMAINS[ctx.domain])
    return gross, hd, res


def _static_fav_level(ctx: Any, idx: np.ndarray, direction: np.ndarray,
                      mult: np.ndarray) -> np.ndarray:
    """(m, MR_CAP_MAX) static favourable limit ``entry_close + dir*mult*ATR`` (matched-distance null).

    Favourable by construction (mult > 0); NaN at offsets past the TRAIN frame. Mirrors the EXP-090
    ATR-BARRIER static branch but with a per-event resampled ``mult`` instead of the fixed 1.0xATR.
    """
    entry_close, atr_e = ctx.close[idx], ctx.atr[idx]
    static = entry_close + direction.astype(np.float64) * mult * atr_e        # (m,)
    off = np.arange(1, MR_CAP_MAX + 1)
    valid = (idx[:, None] + off[None, :]) < ctx.n_domain
    return np.where(valid, static[:, None], np.nan)


def _rct_fav_level_guarded(ctx: Any, idx: np.ndarray, direction: np.ndarray,
                           cap: np.ndarray) -> tuple[np.ndarray, float]:
    """RCT favourable levels with the wrong-side guard (companion null). -> (fav_level, wrongside_frac).

    A non-favourable trailing target (``sign(P*-entry_close) != direction``) is NOT a favourable target
    -> masked to NaN so the engine never instant-fills it (resolve via stop/cap only). wrongside_frac
    is the share of events whose first-offset target is wrong-side.
    """
    fav = E90.arm_levels(ctx, idx, direction, cap, "RCT")["fav_level"].copy()
    entry_close = ctx.close[idx][:, None]
    d = direction[:, None]
    favourable = np.where(d == LONG, fav > entry_close, fav < entry_close) & np.isfinite(fav)
    fav = np.where(favourable, fav, np.nan)
    first = favourable[:, 0] if favourable.shape[1] else np.zeros(idx.shape[0], dtype=bool)
    wrongside_frac = float(1.0 - np.mean(first)) if idx.shape[0] else float("nan")
    return fav, wrongside_frac


# --------------------------------------------------------------------------- #
# Pure computation — leg (b) net screen, leg (c) null arms
# --------------------------------------------------------------------------- #
def _keep_mask(idx: np.ndarray, resolved: np.ndarray, gross: np.ndarray, hd: np.ndarray,
               ctx: Any) -> np.ndarray:
    """Resolved-event keep mask (finite gross, ATR>0, valid holding) — the EXP-091 denominator."""
    atr_e = ctx.atr[idx]
    return (resolved & np.isfinite(gross) & np.isfinite(atr_e) & (atr_e > 0.0)
            & np.isfinite(hd) & (hd >= 0.0))


def _terminal_mix(kind: np.ndarray, resolved: np.ndarray) -> dict[str, float]:
    """Fraction of resolved events ending FAV / ADV / CAP."""
    k = kind[resolved]
    if k.shape[0] == 0:
        return {"fav": float("nan"), "adv": float("nan"), "cap": float("nan")}
    return {"fav": float(np.mean(k == KIND_FAV)), "adv": float(np.mean(k == KIND_ADV)),
            "cap": float(np.mean(k == KIND_CAP))}


def screen_arm(ctx: Any, arm: str, rt_bps: float) -> ArmNet:
    """Leg (b): resolve real CORE entries through ``arm``, overlay cost, net lower bound (EXP-091)."""
    idx, direction = ctx.core_entry_idx, ctx.core_direction
    gross, hd, res = _resolve_engine_arm(ctx, idx, direction, arm)
    keep = _keep_mask(idx, res.resolved, gross, hd, ctx)
    n_events, n_resolved = int(idx.shape[0]), int(np.count_nonzero(keep))
    terminal = _terminal_mix(res.kind, res.resolved)
    tie = res.tie_break[res.resolved]
    tie_frac = float(np.mean(tie)) if tie.shape[0] else 0.0
    if n_resolved < 2:
        return _empty_arm(arm, n_events, n_resolved, tie_frac, terminal)
    g, p, a, h = gross[keep], ctx.close[idx][keep], ctx.atr[idx][keep], hd[keep]
    net = _net_after_cost(g, p, a, h, rt_bps)
    net_fast = _net_after_cost(g, p, a, h, rt_bps / 2.0)
    gross_lo = _mblock_lower(g, seed_for(EXPERIMENT_ID, ctx.instrument, ctx.domain, arm, "g"))
    net_lo = _mblock_lower(net, seed_for(EXPERIMENT_ID, ctx.instrument, ctx.domain, arm, "n"))
    net_fast_lo = _mblock_lower(net_fast, seed_for(EXPERIMENT_ID, ctx.instrument, ctx.domain,
                                                   arm, "nf"))
    return ArmNet(
        arm=arm, n_events=n_events, n_resolved=n_resolved, resolved_frac=float(np.mean(res.resolved)),
        tie_break_frac=tie_frac, terminal_mix=terminal, holding_days_mean=float(np.mean(h)),
        gross_mean=float(np.mean(g)), gross_median=float(np.median(g)), net_mean=float(np.mean(net)),
        net_median=float(np.median(net)), gross_ci_low=gross_lo, net_ci_low=net_lo,
        net_clear=bool(net_lo > 0.0), cost_txn_mean=float(np.mean(g - net)),
        net_ci_low_faster=net_fast_lo, net_per_event=net)


def _empty_arm(arm: str, n_events: int, n_resolved: int, tie_frac: float,
               terminal: dict[str, float]) -> ArmNet:
    """Too-thin arm: reported with denominators, never a net-clear."""
    nan = float("nan")
    return ArmNet(arm=arm, n_events=n_events, n_resolved=n_resolved,
                  resolved_frac=(n_resolved / n_events if n_events else nan), tie_break_frac=tie_frac,
                  terminal_mix=terminal, holding_days_mean=nan, gross_mean=nan, gross_median=nan,
                  net_mean=nan, net_median=nan, gross_ci_low=nan, net_ci_low=nan, net_clear=False,
                  cost_txn_mean=nan, net_ci_low_faster=nan, net_per_event=np.empty(0))


def real_rct_profile(ctx: Any, rt_bps: float) -> dict[str, Any]:
    """Real EXIT-RCT resolved net series, direction multiset, and two favourable-distance distributions.

    ``mu`` = entry-bar RCT target multiples ``(P*-Close)/ATR`` (the BINDING matched distance, D0-amendment-005).
    ``kappa`` = realized favourable-capture multiples of the FAV-terminating events (the audit-§5 sensitivity
    distance; the distance the strategy actually captures, ~0.27 ATR < entry-bar target ~0.5 ATR).
    """
    idx, direction = ctx.core_entry_idx, ctx.core_direction
    gross, hd, res = _resolve_engine_arm(ctx, idx, direction, "RCT")
    keep = _keep_mask(idx, res.resolved, gross, hd, ctx)
    g, p, a, h = gross[keep], ctx.close[idx][keep], ctx.atr[idx][keep], hd[keep]
    net = _net_after_cost(g, p, a, h, rt_bps) if g.shape[0] else np.empty(0)
    kept_idx, kept_dir = idx[keep], direction[keep]
    mu = (ctx.rct_target[kept_idx] - ctx.close[kept_idx]) * kept_dir / ctx.atr[kept_idx]
    mu = mu[np.isfinite(mu) & (mu > 0.0)]                        # entry-bar favourable target multiples
    fav_kept = res.kind[keep] == KIND_FAV
    kappa = g[fav_kept]                                           # realized favourable capture (FAV exits)
    kappa = kappa[np.isfinite(kappa) & (kappa > 0.0)]
    return {"net": net, "direction": kept_dir, "mu": mu, "kappa": kappa, "n": int(net.shape[0])}


def matched_distance_null_net(ctx: Any, profile: dict[str, Any], rt_bps: float,
                              dist: str = "mu") -> np.ndarray:
    """Leg (c) matched-distance oscillation null (net per-event). ``dist``='mu' BINDING / 'kappa' sensitivity."""
    n, dists = profile["n"], profile[dist]
    if n < 2 or dists.shape[0] == 0 or ctx.eligible_pool.shape[0] < 2:
        return np.empty(0)
    rng = np.random.default_rng(seed_for(EXPERIMENT_ID, ctx.instrument, ctx.domain, "RCT", "mdnull", dist))
    k = int(min(n, ctx.eligible_pool.shape[0]))
    idx = np.sort(rng.choice(ctx.eligible_pool, size=k, replace=False)).astype(np.int64)
    direction = profile["direction"][:k].copy()
    rng.shuffle(direction)                                        # matched direction multiset
    mult = rng.choice(dists, size=k, replace=True)                # resample real favourable distances
    fav_level = _static_fav_level(ctx, idx, direction, mult)
    gross, hd, res = _resolve_custom_fav(ctx, idx, direction, fav_level)
    return _null_net(ctx, idx, res, gross, hd, rt_bps)


def subrandom_rct_null_net(ctx: Any, profile: dict[str, Any], rt_bps: float
                           ) -> tuple[np.ndarray, float, dict[str, float]]:
    """Companion null (NON-binding): SUB-RANDOM-entry RCT with the wrong-side guard."""
    n = profile["n"]
    if n < 2 or ctx.eligible_pool.shape[0] < 2:
        return np.empty(0), float("nan"), {"fav": float("nan")}
    rng = np.random.default_rng(seed_for(EXPERIMENT_ID, ctx.instrument, ctx.domain, "RCT", "srnull"))
    k = int(min(n, ctx.eligible_pool.shape[0]))
    idx = np.sort(rng.choice(ctx.eligible_pool, size=k, replace=False)).astype(np.int64)
    direction = profile["direction"][:k].copy()
    rng.shuffle(direction)
    cap, _ = mr_tempo_caps(idx, ctx.ep_close_idx, ctx.ep_durations)
    fav_level, wrongside_frac = _rct_fav_level_guarded(ctx, idx, direction, cap)
    gross, hd, res = _resolve_custom_fav(ctx, idx, direction, fav_level)
    return _null_net(ctx, idx, res, gross, hd, rt_bps), wrongside_frac, _terminal_mix(res.kind,
                                                                                      res.resolved)


def _null_net(ctx: Any, idx: np.ndarray, res: Any, gross: np.ndarray, hd: np.ndarray,
              rt_bps: float) -> np.ndarray:
    """Cost-overlaid net per-event series for a resolved null arm (shared by both null constructions)."""
    keep = _keep_mask(idx, res.resolved, gross, hd, ctx)
    if int(np.count_nonzero(keep)) < 2:
        return np.empty(0)
    g, p, a, h = gross[keep], ctx.close[idx][keep], ctx.atr[idx][keep], hd[keep]
    return _net_after_cost(g, p, a, h, rt_bps)


# --------------------------------------------------------------------------- #
# Aggregation — quorum, falsification, bite-check
# --------------------------------------------------------------------------- #
def quorum(clearing_cells: list[tuple[str, str]]) -> dict[str, Any]:
    """Pass iff >=QUORUM_CELLS cells over >=QUORUM_INSTRUMENTS instruments."""
    n_cells = len(clearing_cells)
    n_instr = len({i for i, _ in clearing_cells})
    return {"n_clearing_cells": n_cells, "n_clearing_instruments": n_instr,
            "passes": bool(n_cells >= QUORUM_CELLS and n_instr >= QUORUM_INSTRUMENTS),
            "clearing_cells": sorted(c for _, c in clearing_cells)}


def bite_check(profiles: dict[str, dict[str, Any]], observed_delta_med: float) -> dict[str, Any]:
    """Leg (e): GREEN/RED calibration of the matched-distance paired-Delta statistic (audit §4 corrected).

    Operates on the already-resolved null net arrays (validates the STATISTIC + decision rule, not the
    engine). Two legs, both PER-CELL (the original quorum-compounded power leg was structurally too
    stringent, and planting the sub-threshold single-arm MDE gave power 0 by construction):

    * FPR — two independent block-resamples of the same null net series (a true same-distribution null):
      mean per-cell beats-rate must be <= BITE_FPR_CELL_MAX AND the >=5/>=3 quorum-fire rate <= BITE_FPR_MAX.
    * POWER — plant a grid of real-over-null shifts on one arm; report the per-cell detection rate at each.
      GREEN-power iff per-cell detection at the FIXED material reference BITE_POWER_REF_ATR (0.10 ATR, set
      a priori — not the observed effect) reaches BITE_TPR_TARGET. The two-sample per-cell MDE (smallest
      planted g with detection >= target) and the observed median real-null Delta are reported for context.

    Bounded by BITE_REPLICATES x len(grid) x BITE_NBOOT; fully seeded.
    """
    cells = [c for c in profiles if profiles[c]["nullnet"].shape[0] >= 2]
    rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "BITE", "CHECK", "md", "seed"))
    fpr_cell = {c: 0 for c in cells}
    pow_cell = {g: {c: 0 for c in cells} for g in BITE_PLANT_GRID}
    fpr_quorum_fires = 0
    for _ in tqdm(range(BITE_REPLICATES), desc="(e) bite-check", unit="rep", leave=False):
        fpr_clear = []
        for c in cells:
            x = profiles[c]["nullnet"]
            n = x.shape[0]
            # Two independent block-resamples of the SAME null series = a same-distribution null.
            ra = x[np.random.default_rng(rng.integers(1 << 31)).integers(0, n, n)]
            rb = x[np.random.default_rng(rng.integers(1 << 31)).integers(0, n, n)]
            d = _mblock_diff_lower(ra, rb, int(rng.integers(1 << 31)), n_boot=BITE_NBOOT)
            # EXACT identity: planting a uniform +g on one arm shifts every moving-block resample mean
            # (hence every percentile) by g, so Δ_lo(null+g, null) = Δ_lo(null, null) + g = d + g.
            # The whole power grid + the FPR leg share this single diff bootstrap (no result change).
            if np.isfinite(d) and d > 0.0:
                fpr_cell[c] += 1
                fpr_clear.append((profiles[c]["instrument"], c))
            for g in BITE_PLANT_GRID:                       # planted real-over-null effect on one arm
                if np.isfinite(d) and d + g > 0.0:
                    pow_cell[g][c] += 1
        if quorum(fpr_clear)["passes"]:
            fpr_quorum_fires += 1
    fpr_quorum_rate = fpr_quorum_fires / BITE_REPLICATES
    fpr_cell_mean = float(np.mean([fpr_cell[c] / BITE_REPLICATES for c in cells])) if cells else 1.0
    power_by_g = {g: (float(np.mean([pow_cell[g][c] / BITE_REPLICATES for c in cells])) if cells else 0.0)
                  for g in BITE_PLANT_GRID}
    two_sample_mde = next((g for g in BITE_PLANT_GRID if power_by_g[g] >= BITE_TPR_TARGET), None)
    power_ref = power_by_g[BITE_POWER_REF_ATR]
    fpr_ok = fpr_cell_mean <= BITE_FPR_CELL_MAX and fpr_quorum_rate <= BITE_FPR_MAX
    power_ok = power_ref >= BITE_TPR_TARGET
    green = bool(fpr_ok and power_ok)
    return {"verdict": "GREEN" if green else "RED", "fpr_cell_mean": fpr_cell_mean,
            "fpr_quorum_rate": fpr_quorum_rate, "fpr_cell_max": BITE_FPR_CELL_MAX,
            "fpr_quorum_max": BITE_FPR_MAX, "power_by_g": power_by_g,
            "power_ref_atr": BITE_POWER_REF_ATR, "power_at_ref": power_ref,
            "tpr_target": BITE_TPR_TARGET, "two_sample_mde": two_sample_mde,
            "observed_delta_median": observed_delta_med, "fpr_ok": fpr_ok, "power_ok": power_ok,
            "n_replicates": BITE_REPLICATES, "n_boot": BITE_NBOOT, "n_cells": len(cells)}


# --------------------------------------------------------------------------- #
# Orchestration — per-cell legs
# --------------------------------------------------------------------------- #
def _json_default(o: Any) -> Any:
    """JSON encoder fallback for numpy scalars in the cached readiness record."""
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def _readiness_key(instrument: str, path: Path) -> str:
    """Content hash of every input that can change leg-(a) readiness for this cell (cache invalidation).

    Keyed on the EXP-090 substrate code bytes, the source-file identity (name/size/mtime), the 4h domain
    period, the master seed, and a readiness-const version. Any change ⇒ different key ⇒ cache miss ⇒
    recompute (biased toward recompute — never reuses a stale result). Holdout is never read either way.
    """
    st = path.stat()
    payload = json.dumps({
        "exp090_code_sha": hashlib.sha256(EXP090_CODE.read_bytes()).hexdigest(),
        "file": path.name, "size": st.st_size, "mtime_ns": st.st_mtime_ns,
        "domain": DOMAIN_4H, "period": E90.DOMAINS[DOMAIN_4H], "master_seed": MASTER_SEED,
        "const_version": READINESS_CONST_VERSION}, sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()


def load_or_compute_readiness(instrument: str, path: Path, use_cache: bool) -> dict[str, Any]:
    """Leg (a): EXP-090 readiness/MDE/member verdict for one instrument x 4h cell, with a content-keyed cache.

    A cache HIT returns the byte-identical previously-computed record (deterministic leg-a output keyed by
    :func:`_readiness_key`); a key mismatch or ``use_cache=False`` recomputes via the verbatim
    ``E90.compute_cell`` and rewrites the cache. ``_cache_hit`` records provenance for the audit.
    """
    key = _readiness_key(instrument, path)
    cache_file = READINESS_CACHE_DIR / f"{instrument}-{DOMAIN_4H}.json"
    if use_cache and cache_file.exists():
        cached = json.loads(cache_file.read_text())
        if cached.get("_cache_key") == key:
            cached["_cache_hit"] = True
            return cached
    rc = E90.compute_cell((instrument, DOMAIN_4H), path)
    rec = {**rc, "_cache_key": key, "_cache_hit": False}
    READINESS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(rec, indent=1, default=_json_default))
    return rec


def screen_cell(ctx: Any, rt_bps: float) -> dict[str, ArmNet]:
    """Leg (b): net-screen every engine arm on one member cell."""
    return {arm: screen_arm(ctx, arm, rt_bps) for arm in ARMS}


def falsify_cell(ctx: Any, real_rct: ArmNet, rt_bps: float) -> dict[str, Any]:
    """Leg (c): matched-distance binding null + SUB-RANDOM companion + paired-Delta lower bounds."""
    profile = real_rct_profile(ctx, rt_bps)
    md_net = matched_distance_null_net(ctx, profile, rt_bps, "mu")           # BINDING null
    md_net_realized = matched_distance_null_net(ctx, profile, rt_bps, "kappa")  # §5 sensitivity null
    sr_net, wrongside_frac, sr_terminal = subrandom_rct_null_net(ctx, profile, rt_bps)
    real_net = real_rct.net_per_event
    seed_md = seed_for(EXPERIMENT_ID, ctx.instrument, ctx.domain, "RCT", "delta_md")
    seed_kp = seed_for(EXPERIMENT_ID, ctx.instrument, ctx.domain, "RCT", "delta_kappa")
    seed_sr = seed_for(EXPERIMENT_ID, ctx.instrument, ctx.domain, "RCT", "delta_sr")
    delta_lo = _mblock_diff_lower(real_net, md_net, seed_md)
    delta_lo_realized = _mblock_diff_lower(real_net, md_net_realized, seed_kp)
    delta_lo_companion = _mblock_diff_lower(real_net, sr_net, seed_sr)
    return {
        "n_real": int(real_net.shape[0]), "n_rand": int(md_net.shape[0]),
        "real_net_mean": float(np.mean(real_net)) if real_net.shape[0] else float("nan"),
        "rand_net_mean": float(np.mean(md_net)) if md_net.shape[0] else float("nan"),
        "mu_mean": float(np.mean(profile["mu"])) if profile["mu"].shape[0] else float("nan"),
        "mu_median": float(np.median(profile["mu"])) if profile["mu"].shape[0] else float("nan"),
        "kappa_mean": float(np.mean(profile["kappa"])) if profile["kappa"].shape[0] else float("nan"),
        "delta_cell": (float(np.mean(real_net) - np.mean(md_net))
                       if real_net.shape[0] and md_net.shape[0] else float("nan")),
        "delta_lo": delta_lo, "beats_random": bool(np.isfinite(delta_lo) and delta_lo > 0.0),
        "rand_resolved_frac": (float(md_net.shape[0]) / profile["n"]) if profile["n"] else float("nan"),
        "rand_terminal_fav": sr_terminal.get("fav", float("nan")),
        "rand_realized_net_mean": (float(np.mean(md_net_realized)) if md_net_realized.shape[0]
                                   else float("nan")),
        "delta_lo_realized": delta_lo_realized,
        "beats_realized": bool(np.isfinite(delta_lo_realized) and delta_lo_realized > 0.0),
        "delta_lo_companion": delta_lo_companion, "wrongside_frac": wrongside_frac,
        "nullnet": md_net, "instrument": ctx.instrument}


# --------------------------------------------------------------------------- #
# Orchestration — full run
# --------------------------------------------------------------------------- #
def run(limit: int | None = None, use_cache: bool = True) -> dict[str, Any]:
    """Run legs (a)-(e) on the 4h candidate universe (+ 1h positive control).

    ``use_cache`` reuses the content-keyed leg-(a) readiness cache (deterministic; key-invalidated on any
    input change). ``--refresh-readiness`` (use_cache=False) forces a clean recompute for the official record.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    files = discover_files()
    universe = member_universe()
    if limit:
        universe = universe[:limit]

    # Leg (a) — readiness on the 4h universe (content-keyed cache; deterministic output).
    readiness, members, n_cache_hits = {}, [], 0
    for inst in tqdm(universe, desc="(a) readiness 4h", unit="cell"):
        if inst not in files:
            raise FileNotFoundError(f"no INFR-003 file for {inst}")
        rc = load_or_compute_readiness(inst, files[inst], use_cache)
        readiness[inst] = rc
        n_cache_hits += int(bool(rc.get("_cache_hit")))
        if rc.get("verdict") == "MEMBER":
            members.append(inst)
    LOGGER.info("(a) %d MEMBER / %d COVERAGE_EXCLUDED on 4h (%d/%d readiness cache hits)", len(members),
                len(universe) - len(members), n_cache_hits, len(universe))

    # Legs (b)+(c) — net screen + falsification on the 4h members.
    by_cell, falsi = {}, {}
    for inst in tqdm(members, desc="(b/c) screen+falsify 4h", unit="cell"):
        ctx, _, status = _build_ctx(inst, DOMAIN_4H, files[inst])
        if ctx is None:
            raise RuntimeError(f"{inst}-4h: member failed to build ({status})")
        arms = screen_cell(ctx, MR_COST_RT_BPS[inst])
        by_cell[inst] = arms
        falsi[inst] = falsify_cell(ctx, arms["RCT"], MR_COST_RT_BPS[inst])

    # Leg (d) — 1h positive control (same matched-distance contrast on EXP-091 clearing cells).
    control = {}
    for inst in tqdm(CONTROL_1H_CELLS, desc="(d) 1h positive control", unit="cell"):
        ctx, _, status = _build_ctx(inst, "1h", files[inst])
        if ctx is None:
            raise RuntimeError(f"{inst}-1h control failed to build ({status})")
        rct = screen_arm(ctx, "RCT", MR_COST_RT_BPS[inst])
        control[inst] = falsify_cell(ctx, rct, MR_COST_RT_BPS[inst])

    # Quorums (b net-clear; c falsification) + bite-check (e).
    net_clearing = [(i, f"{i}-4h") for i in members if by_cell[i]["RCT"].net_clear]
    beats_clearing = [(i, f"{i}-4h") for i in members if falsi[i]["beats_random"]]
    beats_realized = [(i, f"{i}-4h") for i in members if falsi[i]["beats_realized"]]
    screen_quorum = {a: quorum([(i, f"{i}-4h") for i in members if by_cell[i][a].net_clear])
                     for a in ARMS}
    falsi_quorum = quorum(beats_clearing)
    falsi_quorum_realized = quorum(beats_realized)              # §5 sensitivity (non-binding)
    observed_delta_med = (float(np.median([falsi[i]["delta_cell"] for i in members
                                           if np.isfinite(falsi[i]["delta_cell"])]))
                          if members else float("nan"))
    bite = bite_check(falsi, observed_delta_med)

    determinism = _determinism_replay(files)
    verdict = _verdict(screen_quorum, falsi_quorum, control, bite, determinism)
    _write_outputs(readiness, by_cell, falsi, control, screen_quorum, falsi_quorum, members)
    _make_plots(by_cell, falsi, control, screen_quorum, members)
    meta = _metadata(universe, members, screen_quorum, falsi_quorum, falsi_quorum_realized, control,
                     bite, determinism, verdict, n_cache_hits, use_cache)
    meta["output_hashes"] = _hash_outputs()
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(meta, indent=2, default=str))
    (RESULTS_DIR / "bite_check.json").write_text(json.dumps(bite, indent=2, default=str))
    _log_summary(screen_quorum, falsi_quorum, bite, verdict, determinism)
    return meta


def _build_ctx(instrument: str, domain: str, path: Path) -> tuple[Any, float, str]:
    """Load TRAIN 1m + build the per-cell context (EXP-090 substrate)."""
    train_1m, _ = E90.load_train_1m(instrument, path)
    return E90.build_cell_context(train_1m, instrument, domain)


def _rct_mde(rc: dict[str, Any]) -> float:
    """Per-cell EXIT-RCT MDE (the EXP-093 margin) from the EXP-090 readiness record (0.0 if absent).

    Reads the member ``margins`` map first (arm->finite MDE), then the raw ``calibration[RCT][mde]``.
    Returns 0.0 when RCT has no finite MDE (the cell would not carry RCT to TEST regardless).
    """
    mde = rc.get("margins", {}).get("RCT")
    if mde is None:
        mde = rc.get("calibration", {}).get("RCT", {}).get("mde")
    return float(mde) if mde is not None and np.isfinite(mde) else 0.0


def _verdict(screen_q: dict[str, Any], falsi_q: dict[str, Any], control: dict[str, Any],
             bite: dict[str, Any], determinism: dict[str, Any]) -> str:
    """ADMIT_4H / 4H_CLOSED_OSCILLATION / 4H_EMPTY / INCONCLUSIVE (analysis-plan §Interpretation)."""
    if not determinism["determinism_pass"]:
        return "HALT_NON_DETERMINISM"
    if bite["verdict"] != "GREEN":
        return "HALT_BITE_NOT_GREEN"
    control_beats = sum(1 for c in control.values() if c["beats_random"])
    if control_beats < 3:                                        # positive control underpowered
        return "INCONCLUSIVE_CONTROL"
    if not screen_q["RCT"]["passes"]:
        return "4H_EMPTY"
    return "ADMIT_4H" if falsi_q["passes"] else "4H_CLOSED_OSCILLATION"


# --------------------------------------------------------------------------- #
# Determinism + hashing
# --------------------------------------------------------------------------- #
def _determinism_replay(files: dict[str, Path]) -> dict[str, Any]:
    """Re-run two 4h cells (screen RCT + matched-distance delta_lo); assert frame-identical (D9)."""
    checked, mism = [], []
    for inst, domain in DETERMINISM_CELLS:
        if inst not in files:
            continue
        checked.append(f"{inst}-{domain}")
        ctx, _, _ = _build_ctx(inst, domain, files[inst])
        a1 = screen_arm(ctx, "RCT", MR_COST_RT_BPS[inst])
        a2 = screen_arm(ctx, "RCT", MR_COST_RT_BPS[inst])
        f1 = falsify_cell(ctx, a1, MR_COST_RT_BPS[inst])
        f2 = falsify_cell(ctx, a2, MR_COST_RT_BPS[inst])
        if not (_eq(a1.net_ci_low, a2.net_ci_low) and a1.net_clear == a2.net_clear
                and _eq(f1["delta_lo"], f2["delta_lo"]) and f1["beats_random"] == f2["beats_random"]):
            mism.append(f"{inst}-{domain}")
    return {"determinism_pass": not mism, "cells_checked": checked, "non_deterministic": mism}


def _eq(a: float, b: float) -> bool:
    return bool(a == b or (np.isnan(a) and np.isnan(b)))


def _hash_outputs() -> dict[str, str]:
    out = {}
    for name in HEADLINE_OUTPUTS:
        p = RESULTS_DIR / name
        if p.exists():
            out[name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def _cost_table_hash() -> str:
    payload = json.dumps({"RT": MR_COST_RT_BPS, "F": FIN_BPS_DAY}, sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()


# --------------------------------------------------------------------------- #
# Output writers
# --------------------------------------------------------------------------- #
def _write_outputs(readiness: dict[str, Any], by_cell: dict[str, dict[str, ArmNet]],
                   falsi: dict[str, Any], control: dict[str, Any], screen_q: dict[str, Any],
                   falsi_q: dict[str, Any], members: list[str]) -> None:
    """Flatten every leg to its headline CSV (analysis-plan 'Expected output')."""
    pl.DataFrame([{"instrument": i, "domain": DOMAIN_4H,
                   "verdict": readiness[i].get("verdict", "EMPTY"),
                   "reason": readiness[i].get("reason", readiness[i].get("status", "")),
                   "rct_mde": _rct_mde(readiness[i])} for i in readiness]
                 ).write_csv(RESULTS_DIR / "readiness_4h.csv")
    screen_rows, cost_rows = [], []
    for i in members:
        for arm in ARMS:
            a = by_cell[i][arm]
            screen_rows.append({
                "cell": f"{i}-4h", "instrument": i, "domain": DOMAIN_4H, "arm": arm,
                "n_events": a.n_events, "n_resolved": a.n_resolved, "resolved_frac": a.resolved_frac,
                "tie_break_frac": a.tie_break_frac, "holding_days_mean": a.holding_days_mean,
                "gross_mean": a.gross_mean, "gross_median": a.gross_median, "net_mean": a.net_mean,
                "net_median": a.net_median, "gross_ci_low": a.gross_ci_low,
                "net_ci_low": a.net_ci_low, "net_clear": a.net_clear,
                "net_ci_low_faster": a.net_ci_low_faster,
                **{f"terminal_{k}": v for k, v in a.terminal_mix.items()}})
            cost_rows.append({"cell": f"{i}-4h", "instrument": i, "arm": arm,
                              "rt_bps": MR_COST_RT_BPS[i], "cost_txn_mean": a.cost_txn_mean,
                              "gross_mean": a.gross_mean, "net_mean": a.net_mean})
    pl.DataFrame(screen_rows).write_csv(RESULTS_DIR / "screen_per_cell_arm_4h.csv")
    pl.DataFrame(cost_rows).write_csv(RESULTS_DIR / "cost_decomposition_4h.csv")
    pl.DataFrame([{"arm": a, **{k: v for k, v in screen_q[a].items() if k != "clearing_cells"},
                   "clearing_cells": "|".join(screen_q[a]["clearing_cells"])} for a in ARMS]
                 ).write_csv(RESULTS_DIR / "quorum_per_arm_4h.csv")
    pl.DataFrame([{"cell": f"{i}-4h", **{k: v for k, v in falsi[i].items()
                                         if k not in ("nullnet", "instrument")}} for i in members]
                 ).write_csv(RESULTS_DIR / "falsification_paired_delta_4h.csv")
    pl.DataFrame([{"scope": "4h_binding", **{k: v for k, v in falsi_q.items()
                                             if k != "clearing_cells"},
                   "clearing_cells": "|".join(falsi_q["clearing_cells"])}]
                 ).write_csv(RESULTS_DIR / "falsification_quorum.csv")
    pl.DataFrame([{"cell": f"{i}-1h", "instrument": i, "delta_cell": control[i]["delta_cell"],
                   "delta_lo": control[i]["delta_lo"], "beats_random": control[i]["beats_random"]}
                  for i in CONTROL_1H_CELLS]).write_csv(RESULTS_DIR / "positive_control_1h.csv")


# --------------------------------------------------------------------------- #
# Plotting (<=4 bounded plots from collected summaries; no reloads)
# --------------------------------------------------------------------------- #
def _make_plots(by_cell: dict[str, dict[str, ArmNet]], falsi: dict[str, Any],
                control: dict[str, Any], screen_q: dict[str, Any], members: list[str]) -> None:
    _plot_net_heatmap(by_cell, members)
    _plot_paired_delta(falsi, members)
    _plot_mechanism_quorum(by_cell, falsi, screen_q, members)
    _plot_positive_control(control)


def _plot_net_heatmap(by_cell: dict[str, dict[str, ArmNet]], members: list[str]) -> None:
    arr = np.array([[by_cell[i][a].net_ci_low for a in ARMS] for i in members], dtype=np.float64)
    vmax = float(np.nanmax(np.abs(arr))) if arr.size and np.isfinite(arr).any() else 1.0
    fig, ax = plt.subplots(figsize=(7, max(3, 0.4 * len(members) + 1)))
    im = ax.imshow(arr, aspect="auto", cmap="RdYlGn", vmin=-vmax, vmax=vmax)
    ax.set_xticks(range(len(ARMS)), ARMS, rotation=30, ha="right", fontsize=8)
    ax.set_yticks(range(len(members)), [f"{i}-4h" for i in members], fontsize=7)
    ax.set_title("EXP-094 (b) net ci_low_1s — 4h (green>0 = net-clear)", fontsize=10)
    fig.colorbar(im, ax=ax, fraction=0.04)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "net_ci_low_heatmap_4h.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_paired_delta(falsi: dict[str, Any], members: list[str]) -> None:
    cells = [f"{i}-4h" for i in members]
    delta = np.array([falsi[i]["delta_cell"] for i in members])
    lo = np.array([falsi[i]["delta_lo"] for i in members])
    y = np.arange(len(members))
    colours = ["seagreen" if falsi[i]["beats_random"] else "indianred" for i in members]
    fig, ax = plt.subplots(figsize=(7, max(3, 0.4 * len(members) + 1)))
    ax.barh(y, delta, color=colours, alpha=0.7)
    ax.scatter(lo, y, color="black", marker="|", s=80, label="delta_lo (one-sided)")
    ax.axvline(0, color="black", lw=0.9)
    ax.set_yticks(y, cells, fontsize=7)
    ax.set_xlabel("paired delta = real RCT net - matched-distance-null net (ATR)")
    ax.set_title("EXP-094 (c) real vs matched-distance null — beats iff delta_lo>0", fontsize=10)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "paired_delta_4h.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_mechanism_quorum(by_cell: dict[str, dict[str, ArmNet]], falsi: dict[str, Any],
                           screen_q: dict[str, Any], members: list[str]) -> None:
    real_clear = screen_q["RCT"]["n_clearing_cells"]
    beats = sum(1 for i in members if falsi[i]["beats_random"])
    rand_clear = sum(1 for i in members
                     if (n := falsi[i]["nullnet"]).shape[0] >= 2
                     and _mblock_lower(n, seed_for(EXPERIMENT_ID, falsi[i]["instrument"], "4h",
                                                   "MDNULL", "clear")) > 0.0)
    labels = ["real RCT\nnet-clear", "real beats\nmatched-dist null", "matched-dist\nnull net-clears"]
    vals = [real_clear, beats, rand_clear]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(labels, vals, color=["steelblue", "seagreen", "indianred"])
    ax.axhline(QUORUM_CELLS, color="black", ls="--", lw=1, label=f"cell quorum={QUORUM_CELLS}")
    ax.set_ylabel("cells")
    ax.set_title("EXP-094 mechanism — does the matched-distance null also net-clear?", fontsize=10)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "mechanism_quorum_4h.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_positive_control(control: dict[str, Any]) -> None:
    cells = list(CONTROL_1H_CELLS)
    delta = np.array([control[i]["delta_cell"] for i in cells])
    lo = np.array([control[i]["delta_lo"] for i in cells])
    x = np.arange(len(cells))
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.bar(x, delta, color="slateblue", alpha=0.7)
    ax.scatter(x, lo, color="black", marker="_", s=120, label="delta_lo")
    ax.axhline(0, color="black", lw=0.9)
    ax.set_xticks(x, [f"{i}-1h" for i in cells], rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("paired delta (ATR)")
    ax.set_title("EXP-094 (d) 1h positive control — real should beat the null", fontsize=10)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "positive_control_1h.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Metadata + logging
# --------------------------------------------------------------------------- #
def _metadata(universe: list[str], members: list[str], screen_q: dict[str, Any],
              falsi_q: dict[str, Any], falsi_q_realized: dict[str, Any], control: dict[str, Any],
              bite: dict[str, Any], determinism: dict[str, Any], verdict: str, n_cache_hits: int,
              use_cache: bool) -> dict[str, Any]:
    return {
        "experiment_id": EXPERIMENT_ID, "phase": "021", "family": "CF-MR-001", "hyp": "HYP-002",
        "amendments": ["D0-amendment-004", "D0-amendment-005"],
        "generated_utc": datetime.now(timezone.utc).isoformat(), "experiment_verdict": verdict,
        "master_seed": MASTER_SEED, "domain": DOMAIN_4H, "n_universe": len(universe),
        "n_members": len(members), "members": members, "arms": list(ARMS),
        "n_boot": N_BOOT, "boot_alpha": BOOT_ALPHA, "z_one_sided": 1.645,
        "quorum_cells": QUORUM_CELLS, "quorum_instruments": QUORUM_INSTRUMENTS,
        "binding_null": "matched_favourable_target_distance_oscillation (entry-bar target; D0-amendment-005)",
        "sensitivity_null": "matched_realized_capture_distance (audit §5; non-binding)",
        "companion_null": "sub_random_entry_rct_wrongside_guarded (non-binding)",
        "cost_model": "EXP-085 CONSERVATIVE RT (D0-amendment-003); F=0",
        "cost_rt_bps": MR_COST_RT_BPS, "fin_bps_day": FIN_BPS_DAY,
        "cost_table_hash": _cost_table_hash(),
        "screen_quorum_rct": {k: v for k, v in screen_q["RCT"].items() if k != "clearing_cells"},
        "falsification_quorum": {k: v for k, v in falsi_q.items() if k != "clearing_cells"},
        "falsification_quorum_realized_sensitivity": {k: v for k, v in falsi_q_realized.items()
                                                      if k != "clearing_cells"},
        "control_beats_random": sum(1 for c in control.values() if c["beats_random"]),
        "bite_check": bite, "determinism": determinism,
        "readiness_cache": {"use_cache": use_cache, "n_cache_hits": n_cache_hits,
                            "n_universe": len(universe)},
        "holdout_untouched": True, "counted_test_reads": 0, "candidate_slots": 0,
    }


def _log_summary(screen_q: dict[str, Any], falsi_q: dict[str, Any], bite: dict[str, Any],
                 verdict: str, determinism: dict[str, Any]) -> None:
    LOGGER.info("EXP-094 verdict=%s | det=%s | bite=%s", verdict, determinism["determinism_pass"],
                bite["verdict"])
    LOGGER.info("  (b) RCT net-clear %d cells / %d instr -> %s",
                screen_q["RCT"]["n_clearing_cells"], screen_q["RCT"]["n_clearing_instruments"],
                "PASS" if screen_q["RCT"]["passes"] else "fail")
    LOGGER.info("  (c) real-beats-matched-distance-null %d cells / %d instr -> %s",
                falsi_q["n_clearing_cells"], falsi_q["n_clearing_instruments"],
                "PASS" if falsi_q["passes"] else "fail")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description="EXP-094 4h readiness + falsification re-screen")
    ap.add_argument("--limit", type=int, default=None, help="limit universe (smoke test)")
    ap.add_argument("--refresh-readiness", action="store_true",
                    help="ignore the leg-(a) readiness cache and recompute (clean official-record run)")
    args = ap.parse_args()
    meta = run(limit=args.limit, use_cache=not args.refresh_readiness)
    cache = meta["readiness_cache"]
    print(f"EXP-094 complete: verdict={meta['experiment_verdict']} "
          f"members={meta['n_members']} bite={meta['bite_check']['verdict']} "
          f"determinism={meta['determinism']['determinism_pass']} "
          f"readiness_cache_hits={cache['n_cache_hits']}/{cache['n_universe']}")


if __name__ == "__main__":
    main()
