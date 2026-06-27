"""EXP-070 — Event-Level Method Calibration (EXP-027/044-analog, TRAIN-only).

``CF-HA-HARAMI-001`` / HYP-023 — Phase 016 **method calibration** before the first-ever
harami TEST contact (EXP-071). Governing design/D0:
``docs/experiments-docs/checkpoints/2026-06-18-016-harami-candidate-screening/``
(``design.md`` §5 EXP-070; ``D0-predeclarations.md`` P1/P5/P7/P12). Inherits the Phase 015
``D0-amendment-001`` (native object) and ``D0-amendment-002`` (EXP-067 drop). TRAIN-only
(first 49% per file); **0 TEST reads, 0 candidate slots**.

For each of the six **frozen P5 TEST-family cells** (D0 P5: GBPUSD-5m, GBPUSD-1h,
NZDUSD-1h, NZDUSD-2h, GBPJPY-30m, US2000-4h — ex-EURUSD) this measures whether the
**unchanged** EXP-068 ``N-PARTIAL-V2A`` event-level inference — per-event gross
ATR-normalised real-price return -> regime-clustered moving-block bootstrap median CI
(``ci_low_1s``), raw-mean co-primary, ``beats-RM-native`` contrast — applied standalone per
cell at the cell's realized TRAIN event count:

  * **Leg 1 (FPR)**  controls the per-cell false-positive rate on the **binding full
    conjunction** (empirical ``P(ci_low_1s>0 AND mean_ci_low_1s>0 AND beats_rm_low_1s>0)
    <= alpha0 = 0.05`` — the exact P4/P9 EXP-071 cell-acceptance event; D0-amendment-003)
    under **two structurally-different** matched-structure nulls. The median-leg FPR
    ``P(ci_low_1s > 0)`` is retained as a disclosed, non-binding diagnostic;
  * **Leg 2 (finite recovery)**  has a non-degenerate full-TRAIN bootstrap CI width AND a
    finite per-cell planted-edge MDE at TPR >= 0.80;
  * **Leg 3 (determinism)**  replays byte-identical;
  * **Leg 4 (temporal stability)**  classified ``DECAYING``/``STABLE``/``GROWING`` on a
    TRAIN-only 6-month walk-forward (disclosed, non-excluding).

**Reuse, not re-implementation.** The EXP-068 module is imported and its frozen functions
(``signal_arm``, ``matched_random_arm``, ``_summarize_arm``, ``contrast``, ``_ma_context``,
the ``xen.expectancy`` bootstrap/CI primitives, the ``xen.position_exits`` resolver) are
called **unchanged in semantics**. The only new logic here is (a) the two null generators
+ planted-edge substrate and (b) the FPR/TPR/MDE/walk-forward classifier.

**Two nulls (true harami edge = 0 under both):**

  * **Null A — matched-random placement** (the D0 P7 literal null / ``RM-native`` mechanism):
    per draw, replace the conditioned-harami entries with a matched-count random draw from
    the eligible MA-regime pool (excluding the real signal entries), resolved through the
    identical ``N-PARTIAL-V2A`` machinery on the **real** OHLC path. Permutes **placement**.
  * **Null B — block-rotated path** (the structurally-independent second null): per draw,
    keep the **real** harami entry positions/count/entry-time geometry, but resolve them
    against a **block-circular-rotated** OHLC path (contiguous blocks of length
    ``round(n_bars**(1/3))`` rotated as units, so each bar stays internally valid while the
    entry<->forward-path alignment breaks). Permutes **outcomes**. Its matched-random arm is
    **symmetric** (D0-amendment-003): real entry geometry resolved forward on the same
    rotated path, so the ``beats-RM`` contrast (now part of the binding conjunction) has true
    edge 0.

**Planted edge (recovery / MDE) via the translation-equivariance shortcut.** The bootstrap
median is translation-equivariant, so adding a known direction-signed ATR drift ``g`` to
every per-event return shifts every bootstrap median (hence ``ci_low_1s``) by exactly
``+g``. Therefore ``ci_low_1s(g) = ci_low_1s(0) + g`` and
``TPR(g) = mean(ci_low_1s(0) > -g)`` over Null-A draws — exact, computed by thresholding the
stored ``ci_low_1s(0)``; the bootstrap runs **once per draw at g = 0**.

Detection on HA candles; every per-event return is a direction-signed ATR-normalised
**real-price** excursion (no HA-price metric); gross only (no costs); the global final-30%
holdout and the nested TEST stratum are never loaded. **Does not screen, run, or interpret
any candidate, and produces no TEST read** — it is the D0 P7 gate verdict + the EXP-071
binding-family membership input + the EXP-071 power context.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import logging
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Pin per-process native thread pools to 1 BEFORE importing polars/numpy (parallelism is
# process-level, one worker per cell). Mirrors EXP-068; keeps the bootstrap byte-identical.
for _thread_var in ("POLARS_MAX_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                    "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_thread_var, "1")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import polars as pl  # noqa: E402
from tqdm.auto import tqdm  # noqa: E402

# --------------------------------------------------------------------------- #
# Path setup
# --------------------------------------------------------------------------- #
CODE_DIR = Path(__file__).resolve().parent
EXPERIMENT_DIR = CODE_DIR.parent
EXPERIMENTS_ROOT = EXPERIMENT_DIR.parent
PROJECT_ROOT = EXPERIMENT_DIR.parents[2]
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
EXP068_CODE = EXPERIMENTS_ROOT / "EXP-068" / "code" / "run_experiment.py"
EXP068_PARQUET = EXPERIMENTS_ROOT / "EXP-068" / "results" / "per_cell_expectancy.parquet"
EXP068_VERDICT = EXPERIMENTS_ROOT / "EXP-068" / "results" / "g015_verdict.json"
EXP068_METADATA = EXPERIMENTS_ROOT / "EXP-068" / "results" / "run_metadata.json"


def _load_exp068() -> Any:
    """Import the frozen EXP-068 machinery as a module (no side effects beyond its imports).

    EXP-068 has a hyphenated directory, so it is loaded by file location rather than a normal
    import. Loading executes only its module-level imports / thread-pin / Agg backend — never
    ``main()`` — so no data is read and no directory is created at import.
    """
    if not EXP068_CODE.exists():
        raise FileNotFoundError(f"EXP-068 machinery not found at {EXP068_CODE}")
    spec = importlib.util.spec_from_file_location("exp068_machinery", EXP068_CODE)
    module = importlib.util.module_from_spec(spec)
    # Register before exec so EXP-068's @dataclass(frozen=True) can resolve cls.__module__.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# The frozen inference under calibration. Every statistical object is taken from here so the
# method tested is byte-identical to EXP-068 (the "unchanged in semantics" guarantee).
EXP068 = _load_exp068()

# --------------------------------------------------------------------------- #
# Constants (EXP-070 calibration; all inference constants inherited from EXP-068, not tuned)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-070"
# Frozen P5 TEST-family cells (D0 P5; = EXP-068 g015 PARTIAL-V2A passes minus EURUSD).
P5_CELLS: list[tuple[str, str]] = [
    ("GBPUSD", "5m"), ("GBPUSD", "1h"), ("NZDUSD", "1h"),
    ("NZDUSD", "2h"), ("GBPJPY", "30m"), ("US2000", "4h"),
]
BINDING_ARM = "PARTIAL-V2A"          # D0 P2 lead arm (the inference under calibration)
BENCH_ARM = "BENCH"                  # disclosed signal-check anchor (P12 reconciliation)
OBJECT = "nat"                       # D0 P1 / Amendment-001 native object only (no hybrid)

# Inference constants — inherited from EXP-068 (never tuned; referenced, not redefined).
POWER_FLOOR = EXP068.POWER_FLOOR     # 30 reportable events
N_BOOT = EXP068.N_BOOT               # 10_000 bootstrap resamples
BOOT_BATCH = EXP068.BOOT_BATCH       # 2_000 bounded bootstrap batch
BASE_SEED = EXP068.BASE_SEED         # 20260616 frozen master seed
RECON_TOL = 1e-9                     # D0 P1 / P12 reconciliation tolerance

# Calibration design (fixed in Stage 2 / this file, before any measurement).
N_DRAWS = 1000                       # draws per (cell x null); Wilson hw ~0.0135 @ FPR=0.05
DRAW_CHUNK = 25                      # draws per parallel work unit (EXECUTION-ONLY: draws are
#                                      independently seeded, so output is byte-identical for any
#                                      chunk size / worker count; this only balances cores)
ALPHA0 = 0.05                        # D0 P7 binding FPR operating point
FPR_TOLERANCE = 0.06                 # D0 P7 Leg 1: FPR in (alpha0, 0.06] retained; >0.06 excluded
EDGE_GRID: tuple[float, ...] = (0.0, 0.025, 0.05, 0.10, 0.20, 0.40, 0.80)  # ATR units (geometric)
TPR_TARGET = 0.80                    # planted-edge MDE recovery target
DRAW_COMPLETION_FLOOR = 0.90         # a (cell x null) point needs >=90% reportable draws
FPR_WILSON_HW_MAX = 0.03             # precision gate (FPR)
TPR_WILSON_HW_MAX = 0.05             # precision gate (TPR)
METHOD_DEFECT_FPR_CELLS = 5          # >2/3 of 6 cells fail FPR control => METHOD_DEFECT
UNDERPOWERED_CELLS = 3               # >1/3 of 6 cells underpowered => INCONCLUSIVE
WALKFWD_MONTHS = 6                   # D0 P7 Leg 4 walk-forward window (calendar months)
DETERMINISM_CELLS = (("US2000", "4h"), ("GBPUSD", "1h"))  # thin 4h + high-count non-4h

# EXP-070 RNG purpose blocks — disjoint from every EXP-068 block (EXP-068 max is the
# V2A-ADVNONE block 300_000 + offsets; these start at 1_000_000 with 100_000 gaps, and
# draw indices stay < N_DRAWS=1000, so no stream collides with EXP-068 or with each other).
PB_NULLA_DRAW = 1_000_000            # Null A pseudo-signal placement draw
PB_NULLA_MED = 1_100_000            # Null A pseudo-signal median bootstrap
PB_NULLA_MEAN = 1_200_000            # Null A pseudo-signal mean bootstrap
PB_NULLA_RM_DRAW = 1_300_000        # Null A RM-null (beats-RM contrast) placement draw
PB_NULLA_RM_MED = 1_400_000         # Null A RM-null median bootstrap
PB_NULLB_ROT = 1_500_000            # Null B block-rotation offset
PB_NULLB_MED = 1_600_000            # Null B pseudo-signal median bootstrap
PB_NULLB_MEAN = 1_700_000           # Null B pseudo-signal mean bootstrap
PB_NULLB_RM_DRAW = 1_800_000        # Null B RM-null placement draw (on rotated path)
PB_NULLB_RM_MED = 1_900_000         # Null B RM-null median bootstrap

NULLS: tuple[str, ...] = ("A_matched_random_placement", "B_block_rotated_path")
HEADLINE_OUTPUTS = ("calibration_map.csv", "fpr_per_cell.csv", "tpr_mde_per_cell.csv",
                    "ci_width_per_cell.csv", "temporal_stability.csv", "reconciliation.csv",
                    "draw_verdicts.parquet")
LOGGER = logging.getLogger(EXPERIMENT_ID)


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CellContext:
    """Per-cell precomputed TRAIN-only context (all arrays inside the TRAIN frame)."""

    instrument: str
    domain: str
    cell_index: int
    ohlc: dict[str, np.ndarray]
    ma: dict[str, Any]
    cond: np.ndarray                 # native /STRONG-STAT conditioning mask over entry_idx
    entry_idx: np.ndarray
    state_all: Any                   # InProgressState over all bars (matched-random pool)
    warmup_all: np.ndarray
    pool: np.ndarray                 # eligible MA-regime bar indices excluding real signal
    last_train_idx: int
    block_len: int                   # Null-B block length = round(n_bars**(1/3))


@dataclass(frozen=True)
class RealArm:
    """Full-TRAIN real-signal summary for one arm (from the frozen EXP-068 functions)."""

    m: int
    median: float | None
    mean: float | None
    ci_low_1s: float | None
    ci_lo_2s: float | None
    ci_hi_2s: float | None
    mean_ci_low_1s: float | None
    beats_rm_low_1s: float
    ci_width: float | None           # ci_hi_2s - ci_lo_2s (Leg 2 finite check)
    boot_se: float | None            # std of the full-TRAIN median bootstrap dist (Leg 4 SE)
    r_e: np.ndarray                  # qualifying returns in sorted-entry order
    entry_epoch: np.ndarray          # entry epoch (s) aligned to r_e (Leg 4 walk-forward)


# --------------------------------------------------------------------------- #
# Pure computation — per-cell context build (reuses the frozen EXP-068 setup functions)
# --------------------------------------------------------------------------- #
def build_cell_context(train_1m: pl.DataFrame, instrument: str, domain: str,
                       train_end_epoch: int, cell_index: int) -> CellContext | None:
    """Rebuild EXP-068's per-cell TRAIN context, returning the arrays the nulls need.

    Mirrors :func:`exp068.compute_cell`'s setup exactly (same imported functions), then also
    exposes the matched-random eligible pool and per-bar MA state for the null generators.
    Returns ``None`` for an empty / unbuildable cell.
    """
    period_minutes, min_coverage = EXP068.DOMAINS[domain]
    bars = EXP068.build_domain(train_1m, period_minutes, min_coverage, train_end_epoch)
    ohlc = EXP068.real_ohlc(bars)
    atr = EXP068.wilder_atr(ohlc["high"], ohlc["low"], ohlc["close"], EXP068.ATR_PERIOD)
    entry_idx = EXP068.harami_entry_indices(bars, ohlc["epoch"])
    if entry_idx.shape[0] == 0:
        return None
    entry_epoch = ohlc["epoch"][entry_idx]
    ma = EXP068._ma_context(ohlc, atr, entry_idx, entry_epoch)
    if ma.get("empty"):
        return None
    seg = ma["seg"]
    state_all = EXP068.live_in_progress_state(
        ohlc["epoch"], ohlc["close"], seg["confirm_epoch"], seg["end_price"],
        seg["end_epoch"], seg["direction"])
    _, warmup_all = EXP068.adaptive_time_caps_by_epoch(
        ohlc["epoch"], seg["confirm_epoch"], seg["confirm_idx"])
    cond = ma["stat"]["retained_p75"]
    pool = _eligible_pool(state_all, atr, warmup_all, entry_idx[cond], ohlc["close"].shape[0])
    n_bars = int(ohlc["close"].shape[0])
    block_len = max(1, int(round(n_bars ** (1.0 / 3.0))))
    return CellContext(
        instrument=instrument, domain=domain, cell_index=cell_index, ohlc=ohlc, ma=ma,
        cond=cond, entry_idx=entry_idx, state_all=state_all, warmup_all=warmup_all,
        pool=pool, last_train_idx=n_bars - 1, block_len=block_len)


def _eligible_pool(state_all: Any, atr_all: np.ndarray, warmup_all: np.ndarray,
                   signal_idx: np.ndarray, n_bars: int) -> np.ndarray:
    """Eligible MA-regime bar indices excluding the real signal entries (EXP-068 P5 pool)."""
    eligible = (state_all.valid & (state_all.m_sofar > 0.0) & np.isfinite(atr_all)
                & (atr_all > 0.0) & (~warmup_all))
    is_signal = np.zeros(n_bars, dtype=bool)
    is_signal[signal_idx] = True
    return np.flatnonzero(eligible & ~is_signal)


def real_arm(ctx: CellContext, aid: str) -> RealArm:
    """Full-TRAIN real-signal arm via the frozen :func:`exp068.signal_arm` + RM contrast.

    Reproduces EXP-068 exactly (same functions, same ``cell_index`` seed), and additionally
    extracts the bootstrap SE (Leg 4) and the qualifying-event entry epochs (walk-forward).
    """
    arm = EXP068.ARM_BY_ID[aid]
    sig = EXP068.signal_arm(OBJECT, arm, ctx.ohlc, ctx.ma, ctx.cond, ctx.entry_idx,
                            ctx.last_train_idx, ctx.cell_index)
    null = EXP068.matched_random_arm(
        OBJECT, arm, ctx.ohlc, ctx.state_all, ctx.ma["seg"], ctx.warmup_all, ctx.ma["atr"],
        ctx.entry_idx[ctx.cond], sig.m, ctx.cell_index, ctx.last_train_idx)
    beats = EXP068.contrast(sig, null)["median_low_1s"]
    ci_width = (float(sig.ci_hi_2s - sig.ci_lo_2s)
                if sig.ci_hi_2s is not None and sig.ci_lo_2s is not None else None)
    boot_se = float(np.std(sig.dist)) if sig.dist.shape[0] > 0 else None
    entry_epoch = _qualifying_entry_epoch(ctx, sig.qual)
    return RealArm(
        m=sig.m, median=sig.median, mean=sig.mean, ci_low_1s=sig.ci_low_1s,
        ci_lo_2s=sig.ci_lo_2s, ci_hi_2s=sig.ci_hi_2s, mean_ci_low_1s=sig.mean_ci_low_1s,
        beats_rm_low_1s=float(beats), ci_width=ci_width, boot_se=boot_se,
        r_e=sig.r_e, entry_epoch=entry_epoch)


def _qualifying_entry_epoch(ctx: CellContext, qual: np.ndarray) -> np.ndarray:
    """Entry epoch (s) of qualifying events in the same sorted-entry order as ``r_e``."""
    qual_idx = ctx.entry_idx[qual]
    order = np.argsort(qual_idx, kind="stable")
    return ctx.ohlc["epoch"][qual_idx][order]


# --------------------------------------------------------------------------- #
# Pure computation — the two null resolvers (frozen exit machinery, new placement only)
# --------------------------------------------------------------------------- #
def _resolve_matched_draw(geom_ohlc: dict[str, np.ndarray], path_ohlc: dict[str, np.ndarray],
                          drawn: np.ndarray, state_all: Any, seg: dict[str, np.ndarray],
                          atr_all: np.ndarray, arm: Any, last_train_idx: int) -> np.ndarray:
    """Resolve ``drawn`` matched-random entries through PARTIAL-V2A.

    Entry geometry (entry close, time caps, barriers) is taken from ``geom_ohlc``; the legs
    are resolved **forward** on ``path_ohlc``. With ``geom_ohlc is path_ohlc`` (= the real
    path) this is byte-identical to :func:`exp068.matched_random_arm`'s non-bench branch
    (only the draw seed differs) — the Null-A use. Null B passes ``geom_ohlc`` = the **real**
    path and ``path_ohlc`` = the **block-rotated** path, so the RM arm uses real entry
    geometry resolved on the rotated forward path — symmetric with the Null-B signal arm
    (:func:`_resolve_real_entries`), which already does the same (D0-amendment-003)."""
    sub = EXP068._subset_state(state_all, drawn)
    bench_n, bench_warmup = EXP068.adaptive_time_caps_by_epoch(
        geom_ohlc["epoch"][drawn], seg["confirm_epoch"], seg["confirm_idx"])
    base_pop = (sub.valid & (sub.m_sofar > 0.0) & np.isfinite(atr_all[drawn])
                & (atr_all[drawn] > 0.0) & ~bench_warmup)
    bar = EXP068.benchmark_barriers(geom_ohlc["close"][drawn], sub.rd, sub.m_sofar)
    return _resolve_legs(path_ohlc, drawn, geom_ohlc["close"][drawn], sub.rd, bar["fav_dist"],
                         bar["adv"], bench_n, atr_all[drawn], base_pop, arm, last_train_idx)


def _resolve_real_entries(ohlc: dict[str, np.ndarray], ctx: CellContext, arm: Any,
                          ) -> np.ndarray:
    """Resolve the real conditioned-harami entries through PARTIAL-V2A on ``ohlc``.

    With ``ohlc`` = the real path this reproduces :func:`exp068.signal_arm`; with ``ohlc`` =
    a block-rotated path it is the Null-B pseudo-signal (real placement + entry geometry,
    permuted forward outcomes)."""
    ma = ctx.ma
    pop_arm = ma["buildable"] & ctx.cond
    return _resolve_legs(ohlc, ctx.entry_idx, ma["entry_close"], ma["state"].rd,
                         ma["fav_dist"], ma["adv"], ma["bench_n"], ma["atr_entry"],
                         pop_arm, arm, ctx.last_train_idx)


def _resolve_legs(ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, entry_close: np.ndarray,
                  rd: np.ndarray, fav_dist: np.ndarray, adv: np.ndarray, bench_n: np.ndarray,
                  atr_vals: np.ndarray, pop: np.ndarray, arm: Any,
                  last_train_idx: int) -> np.ndarray:
    """Shared frozen PARTIAL-V2A leg resolution -> qualifying returns in sorted-entry order."""
    levels = EXP068.leg_levels_from_fracs(entry_close, rd, fav_dist, arm.leg_fracs)
    reversal = np.full(int(entry_idx.shape[0]), -1, dtype=np.int64)
    leg_px, leg_cls = EXP068.resolve_legs(
        ohlc["open"], ohlc["high"], ohlc["low"], ohlc["close"], entry_idx, entry_close, rd,
        arm.leg_kinds, levels, reversal, adv, bench_n, pop, EXP068.ADV_FIXED, None,
        last_train_idx)
    weights = np.asarray(arm.weights, dtype=np.float64)
    r_all, qual = EXP068.weighted_returns(leg_px, leg_cls, weights, entry_close, rd,
                                          atr_vals, pop)
    order = np.argsort(entry_idx[qual], kind="stable")
    return r_all[qual][order]


def block_rotate(ohlc: dict[str, np.ndarray], block_len: int,
                 rng: np.random.Generator) -> dict[str, np.ndarray]:
    """Block-circular rotation: contiguous bars (O/H/L/C as a unit) rotated as whole blocks.

    Each bar's OHLC moves together, so ``High >= max(O,C)`` / ``Low <= min(O,C)`` is preserved
    (every bar stays internally valid). Block-local microstructure is kept; cross-block path
    continuity is broken — the Null-B mechanism. With few blocks (thin 4h) the distortion is
    larger (interpretation caveat 2)."""
    n = int(ohlc["close"].shape[0])
    n_blocks = int(np.ceil(n / block_len))
    if n_blocks <= 1:
        return ohlc
    offset = int(rng.integers(1, n_blocks))
    order = (np.arange(n_blocks) + offset) % n_blocks
    idx = np.concatenate([np.arange(b * block_len, min((b + 1) * block_len, n)) for b in order])
    return {k: v[idx] for k, v in ohlc.items()}


# --------------------------------------------------------------------------- #
# Pure computation — per-draw bootstrap verdict for one null (frozen bootstrap + CI)
# --------------------------------------------------------------------------- #
def _bootstrap_legs(r_sig: np.ndarray, r_rm: np.ndarray, cell_index: int, med_pb: int,
                    mean_pb: int, rm_med_pb: int, draw: int) -> dict[str, Any]:
    """Median + mean CI of ``r_sig`` and the beats-RM contrast vs ``r_rm`` (frozen primitives).

    A draw is reportable iff the pseudo-signal has ``>= POWER_FLOOR`` qualifying events. The
    stored ``ci_low_1s`` is ``ci_low_1s(g=0)``; the planted-edge grid is read off it by the
    translation shortcut (no re-bootstrap)."""
    m = int(r_sig.shape[0])
    if m < POWER_FLOOR:
        return {"m": m, "reportable": False, "median": float("nan"), "ci_low_1s": float("nan"),
                "mean_ci_low_1s": float("nan"), "beats_rm_low_1s": float("nan")}
    # Per-draw median point estimate (calibrated-margin input; not a bootstrap).
    median_pt = float(np.median(r_sig))
    dist, _ = EXP068.bootstrap_median_distribution(
        r_sig, EXP068._rng(cell_index, med_pb + draw), n_boot=N_BOOT, batch=BOOT_BATCH)
    ci_low_1s, _, _ = EXP068.median_ci(dist)
    mean_dist, _ = EXP068.bootstrap_stat_distribution(
        r_sig, EXP068._rng(cell_index, mean_pb + draw), "mean", n_boot=N_BOOT, batch=BOOT_BATCH)
    mean_low, _, _ = EXP068.median_ci(mean_dist)
    if r_rm.shape[0] >= POWER_FLOOR:
        rm_dist, _ = EXP068.bootstrap_median_distribution(
            r_rm, EXP068._rng(cell_index, rm_med_pb + draw), n_boot=N_BOOT, batch=BOOT_BATCH)
        beats_low, _, _ = EXP068.contrast_ci(dist, rm_dist)
    else:
        beats_low = float("nan")
    return {"m": m, "reportable": True, "median": median_pt, "ci_low_1s": float(ci_low_1s),
            "mean_ci_low_1s": float(mean_low), "beats_rm_low_1s": float(beats_low)}


def null_a_draw(ctx: CellContext, arm: Any, draw_count: int, draw: int) -> dict[str, Any]:
    """Null A (matched-random placement, real path): one pseudo-signal draw + its RM-null."""
    ci = ctx.cell_index
    pool = ctx.pool
    if draw_count <= 0 or pool.shape[0] == 0:
        return {"m": 0, "reportable": False, "median": float("nan"), "ci_low_1s": float("nan"),
                "mean_ci_low_1s": float("nan"), "beats_rm_low_1s": float("nan")}
    k = min(draw_count, pool.shape[0])
    drawn = np.sort(EXP068._rng(ci, PB_NULLA_DRAW + draw).choice(pool, size=k, replace=False))
    # Null A: real entry geometry resolved on the real path (geom_ohlc is path_ohlc).
    r_sig = _resolve_matched_draw(ctx.ohlc, ctx.ohlc, drawn, ctx.state_all, ctx.ma["seg"],
                                  ctx.ma["atr"], arm, ctx.last_train_idx)
    # RM-null for the disclosed beats-RM contrast: a second matched draw excluding `drawn`.
    rm_pool = np.setdiff1d(pool, drawn, assume_unique=False)
    if rm_pool.shape[0] > 0:
        k2 = min(draw_count, rm_pool.shape[0])
        drawn2 = np.sort(EXP068._rng(ci, PB_NULLA_RM_DRAW + draw).choice(
            rm_pool, size=k2, replace=False))
        r_rm = _resolve_matched_draw(ctx.ohlc, ctx.ohlc, drawn2, ctx.state_all, ctx.ma["seg"],
                                     ctx.ma["atr"], arm, ctx.last_train_idx)
    else:
        r_rm = np.empty(0, dtype=np.float64)
    return _bootstrap_legs(r_sig, r_rm, ci, PB_NULLA_MED, PB_NULLA_MEAN, PB_NULLA_RM_MED, draw)


def null_b_draw(ctx: CellContext, arm: Any, draw_count: int, draw: int) -> dict[str, Any]:
    """Null B (block-rotated path, real placement): one pseudo-signal draw + its RM-null."""
    ci = ctx.cell_index
    rot = block_rotate(ctx.ohlc, ctx.block_len, EXP068._rng(ci, PB_NULLB_ROT + draw))
    r_sig = _resolve_real_entries(rot, ctx, arm)
    # RM-null symmetric with the signal arm (D0-amendment-003): REAL entry geometry (geom =
    # ctx.ohlc) resolved FORWARD on the SAME rotated path (path = rot). Both Null-B arms then
    # differ only in placement, and from the real signal only in the permuted forward path.
    if ctx.pool.shape[0] > 0 and draw_count > 0:
        k = min(draw_count, ctx.pool.shape[0])
        drawn = np.sort(EXP068._rng(ci, PB_NULLB_RM_DRAW + draw).choice(
            ctx.pool, size=k, replace=False))
        r_rm = _resolve_matched_draw(ctx.ohlc, rot, drawn, ctx.state_all, ctx.ma["seg"],
                                     ctx.ma["atr"], arm, ctx.last_train_idx)
    else:
        r_rm = np.empty(0, dtype=np.float64)
    return _bootstrap_legs(r_sig, r_rm, ci, PB_NULLB_MED, PB_NULLB_MEAN, PB_NULLB_RM_MED, draw)


# --------------------------------------------------------------------------- #
# Pure computation — Wilson interval, FPR/TPR/MDE, temporal stability, verdicts
# --------------------------------------------------------------------------- #
def wilson(p: float, n: int, z: float = 1.959963984540054) -> tuple[float, float, float]:
    """Wilson score interval (centre, lo, hi) for a proportion ``p`` over ``n`` trials."""
    if n <= 0:
        return float("nan"), float("nan"), float("nan")
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2.0 * n)) / denom
    half = (z * np.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n))) / denom
    return float(centre), float(centre - half), float(centre + half)


def fpr_from_draws(draws: list[dict[str, Any]]) -> dict[str, Any]:
    """Binding conjunction-FPR + disclosed median-leg FPR over reportable draws, Wilson bounds.

    The **conjunction-FPR** (median ∧ raw-mean ∧ beats-RM) is the binding object
    (D0-amendment-003); the **median-leg** FPR is the disclosed, non-binding diagnostic. Both
    carry Wilson 95% bounds + half-widths."""
    n_total = len(draws)
    rep = [d for d in draws if d["reportable"]]
    n = len(rep)
    completion = n / n_total if n_total else 0.0
    if n == 0:
        return {"n_reportable": 0, "completion": completion, "fpr_median": float("nan"),
                "fpr_median_lo": float("nan"), "fpr_median_hi": float("nan"),
                "fpr_median_hw": float("nan"), "fpr_conj": float("nan"),
                "fpr_conj_lo": float("nan"), "fpr_conj_hi": float("nan"),
                "fpr_conj_hw": float("nan")}
    med_hits = sum(1 for d in rep if d["ci_low_1s"] > 0.0)
    conj_hits = sum(1 for d in rep if d["ci_low_1s"] > 0.0 and d["mean_ci_low_1s"] > 0.0
                    and d["beats_rm_low_1s"] > 0.0)
    p_med = med_hits / n
    p_conj = conj_hits / n
    med_centre, med_lo, med_hi = wilson(p_med, n)
    conj_centre, conj_lo, conj_hi = wilson(p_conj, n)
    return {"n_reportable": n, "completion": completion, "fpr_median": p_med,
            "fpr_median_lo": med_lo, "fpr_median_hi": med_hi,
            "fpr_median_hw": (med_hi - med_lo) / 2.0, "fpr_median_wilson_centre": med_centre,
            "fpr_conj": p_conj, "fpr_conj_lo": conj_lo, "fpr_conj_hi": conj_hi,
            "fpr_conj_hw": (conj_hi - conj_lo) / 2.0, "fpr_conj_wilson_centre": conj_centre}


def tpr_curve(null_a_draws: list[dict[str, Any]]) -> dict[float, dict[str, float]]:
    """TPR(g) for the planted-edge grid via the translation shortcut on Null-A draws.

    ``ci_low_1s(g) = ci_low_1s(0) + g`` (median translation-equivariance), so
    ``TPR(g) = mean(ci_low_1s(0) > -g)`` over reportable draws."""
    ci0 = np.array([d["ci_low_1s"] for d in null_a_draws if d["reportable"]], dtype=np.float64)
    out: dict[float, dict[str, float]] = {}
    n = int(ci0.shape[0])
    for g in EDGE_GRID:
        if n == 0:
            out[g] = {"tpr": float("nan"), "tpr_hw": float("nan")}
            continue
        tpr = float(np.mean(ci0 > -g))
        _, lo, hi = wilson(tpr, n)
        out[g] = {"tpr": tpr, "tpr_hw": (hi - lo) / 2.0}
    return out


def mde_from_tpr(tpr: dict[float, dict[str, float]], fpr_controlled: bool) -> float | None:
    """Smallest grid edge with TPR >= target (finite MDE); ``None`` if none / FPR uncontrolled."""
    if not fpr_controlled:
        return None
    for g in EDGE_GRID:
        if g <= 0.0:
            continue
        if np.isfinite(tpr[g]["tpr"]) and tpr[g]["tpr"] >= TPR_TARGET:
            return float(g)
    return None


def calibrated_margin(null_a_draws: list[dict[str, Any]]) -> float | None:
    """Per-cell calibrated margin (P9 condition 4 / R1.2 analog; D0-amendment-003).

    The empirical ``1 - ALPHA0`` quantile of the Null-A pseudo-signal **median point estimate**
    over reportable draws — the level a real per-event median must clear to sit in the top-α₀
    null tail. Read off already-computed draw statistics (no new bootstrap); ``None`` if no
    reportable Null-A draw exists."""
    meds = np.array([d["median"] for d in null_a_draws
                     if d["reportable"] and np.isfinite(d["median"])], dtype=np.float64)
    if meds.shape[0] == 0:
        return None
    return float(np.quantile(meds, 1.0 - ALPHA0))


def walk_forward(real: RealArm) -> dict[str, Any]:
    """6-month TRAIN-only walk-forward median point estimates + DECAYING/STABLE/GROWING flag."""
    if real.r_e.shape[0] == 0 or real.median is None or real.boot_se is None:
        return {"flag": "UNDEFINED", "windows": [], "final_window_median": None,
                "full_median": real.median, "boot_se": real.boot_se}
    months = _epoch_to_month_index(real.entry_epoch)
    buckets = months // WALKFWD_MONTHS
    windows: list[dict[str, Any]] = []
    for b in sorted(set(buckets.tolist())):
        sel = real.r_e[buckets == b]
        windows.append({"window": int(b), "n": int(sel.shape[0]),
                        "median": float(np.median(sel)) if sel.shape[0] else None,
                        "powered": bool(sel.shape[0] >= POWER_FLOOR)})
    powered = [w for w in windows if w["powered"]]
    final_median = powered[-1]["median"] if powered else None
    flag = "LOW_POWER"
    if final_median is not None:
        if final_median < real.median - real.boot_se:
            flag = "DECAYING"
        elif final_median > real.median + real.boot_se:
            flag = "GROWING"
        else:
            flag = "STABLE"
    return {"flag": flag, "windows": windows, "final_window_median": final_median,
            "full_median": real.median, "boot_se": real.boot_se}


def _epoch_to_month_index(epoch_s: np.ndarray) -> np.ndarray:
    """Map UTC epoch seconds to a 0-based absolute month index (year*12 + month)."""
    dt = epoch_s.astype("datetime64[s]")
    years = dt.astype("datetime64[Y]").astype(int) + 1970
    months = (dt.astype("datetime64[M]").astype(int) % 12) + 1
    abs_month = years * 12 + (months - 1)
    return abs_month - int(abs_month.min())


def classify_cell(fpr: dict[str, dict[str, Any]], real: RealArm, mde: float | None,
                  ) -> dict[str, Any]:
    """Per-cell calibration verdict from the two-null binding conjunction-FPR (D0-amendment-003),
    CI width (Leg 2), and MDE. The median-leg FPR is disclosed but does not gate."""
    completions = [fpr[n]["completion"] for n in NULLS]
    hws = [fpr[n]["fpr_conj_hw"] for n in NULLS]
    fprs = [fpr[n]["fpr_conj"] for n in NULLS]
    degenerate_ci = bool(real.ci_width is not None and real.ci_width <= 0.0)
    reason = ""
    if any(c < DRAW_COMPLETION_FLOOR for c in completions):
        verdict = "CALIBRATION_UNDERPOWERED"
        reason = f"draw completion < {DRAW_COMPLETION_FLOOR:.2f}"
    elif any(not np.isfinite(h) or h > FPR_WILSON_HW_MAX for h in hws):
        verdict = "CALIBRATION_UNDERPOWERED"
        reason = f"conjunction-FPR Wilson half-width > {FPR_WILSON_HW_MAX}"
    elif any(f > FPR_TOLERANCE for f in fprs):
        verdict = "FPR_EXCLUDED"
        material = any(fpr[n]["fpr_conj_lo"] > ALPHA0 for n in NULLS)
        reason = (f"conjunction-FPR > {FPR_TOLERANCE} under >=1 null"
                  + (" (material)" if material else ""))
    elif any(f > ALPHA0 for f in fprs):
        # D0 P7 Leg 1 tolerance band: (alpha0, 0.06] is RETAINED with record, not PASS-clean.
        verdict = "RETAINED_FPR_TOLERANCE"
        reason = f"conjunction-FPR in ({ALPHA0}, {FPR_TOLERANCE}] tolerance band (retained)"
    elif degenerate_ci:
        verdict = "FPR_EXCLUDED"
        reason = "degenerate (zero-width) full-TRAIN CI"
    elif mde is not None:
        verdict = "PASS"
        reason = f"conjunction-FPR<=alpha0 both nulls; finite CI; finite MDE={mde}"
    else:
        verdict = "MDE_UNRESOLVED"
        reason = ("conjunction-FPR controlled + finite CI but no finite planted-edge MDE "
                  "at TPR>=0.80")
    return {"verdict": verdict, "reason": reason, "degenerate_ci": degenerate_ci,
            "fpr_controlled_both": bool(all(f <= ALPHA0 for f in fprs)),
            "fpr_retained_both": bool(all(f <= FPR_TOLERANCE for f in fprs))}


# --------------------------------------------------------------------------- #
# Per-cell orchestration (context build, real arms, and the parallel draw unit)
# --------------------------------------------------------------------------- #
# Per-process size-1 context cache. Building a cell's TRAIN context (load + domain + MA +
# harami) is the only expensive setup step; draws reuse it read-only. With draw chunks
# submitted grouped by cell, each worker rebuilds a context at most once per cell it touches,
# so memory stays bounded to one context per worker. Caching is EXECUTION-ONLY — every draw is
# still seeded by (cell_index, purpose, draw), so output is byte-identical with or without it.
_CTX_CACHE: dict[str, Any] = {"cell": None, "ctx": None, "meta": None}


def _build_ctx_cached(cell: tuple[str, str]) -> tuple[CellContext | None, dict[str, Any]]:
    """Build (or fetch the cached) per-cell TRAIN context. Treated read-only by all callers."""
    if _CTX_CACHE["cell"] != cell:
        instrument, domain = cell
        cell_index = EXP068._cell_index_map()[(instrument, domain)]
        train_1m, meta = EXP068.load_train_1m(instrument)
        ctx = build_cell_context(train_1m, instrument, domain,
                                 meta["train_end_epoch_s"], cell_index)
        _CTX_CACHE.update(cell=cell, ctx=ctx, meta=meta)
    return _CTX_CACHE["ctx"], _CTX_CACHE["meta"]


def _cell_setup(cell: tuple[str, str]) -> dict[str, Any]:
    """Per-cell setup: context + the real PARTIAL-V2A / BENCH arms (hence ``draw_count``).

    Pure given identical inputs/seeds. ``draw_count`` = the real signal's qualifying-event
    count, which fixes the matched draw size for every null draw, so setup precedes draws."""
    instrument, domain = cell
    ctx, meta = _build_ctx_cached(cell)
    base = {"cell": f"{instrument}-{domain}", "instrument": instrument, "domain": domain}
    if ctx is None:
        return {**base, "empty": True, "source_meta": meta}
    real_partial = real_arm(ctx, BINDING_ARM)
    real_bench = real_arm(ctx, BENCH_ARM)
    return {**base, "empty": False, "cell_index": ctx.cell_index, "block_len": ctx.block_len,
            "draw_count": real_partial.m, "real_partial": real_partial, "real_bench": real_bench,
            "n_bars": int(ctx.ohlc["close"].shape[0]), "n_harami": int(ctx.entry_idx.shape[0]),
            "n_conditioned": int(ctx.cond.sum()), "pool_size": int(ctx.pool.shape[0]),
            "source_meta": meta}


def _draw_chunk(cell: tuple[str, str], null: str, lo: int, hi: int, draw_count: int,
                ) -> tuple[tuple[str, str], int, list[dict[str, Any]]]:
    """Resolve null draws ``[lo, hi)`` for one (cell, null). Each draw is independently seeded."""
    ctx, _ = _build_ctx_cached(cell)
    arm = EXP068.ARM_BY_ID[BINDING_ARM]
    draw_fn = null_a_draw if null == NULLS[0] else null_b_draw
    return (cell, null), lo, [draw_fn(ctx, arm, draw_count, d) for d in range(lo, hi)]


def _assemble_cell(cell: tuple[str, str], setup: dict[str, Any],
                   chunk_out: dict[tuple[str, str], list[tuple[int, list[dict[str, Any]]]]],
                   ) -> dict[str, Any]:
    """Reassemble a cell's draws in draw-index order and run the per-cell aggregation.

    Identical to a serial pass: ``draws[null]`` is its chunks concatenated by ascending ``lo``
    (= draw indices 0..N_DRAWS-1), and FPR/TPR/MDE/verdict/walk-forward are the unchanged pure
    functions of those draws + the real arm. The output dict matches the prior single-cell
    result key-for-key."""
    if setup.get("empty"):
        return setup
    draws: dict[str, list[dict[str, Any]]] = {}
    for n in NULLS:
        ordered = sorted(chunk_out[(cell, n)], key=lambda piece: piece[0])
        seq: list[dict[str, Any]] = []
        for _, res in ordered:
            seq.extend(res)
        draws[n] = seq
    real_partial = setup["real_partial"]
    fpr = {n: fpr_from_draws(draws[n]) for n in NULLS}
    tpr = tpr_curve(draws[NULLS[0]])
    # Binding object is the conjunction-FPR (D0-amendment-003), not the median leg.
    fpr_controlled = bool(all(fpr[n]["fpr_conj"] <= ALPHA0 for n in NULLS
                              if np.isfinite(fpr[n]["fpr_conj"])))
    mde = mde_from_tpr(tpr, fpr_controlled)
    cls = classify_cell(fpr, real_partial, mde)
    margin = calibrated_margin(draws[NULLS[0]])
    wf = walk_forward(real_partial)
    return {
        "cell": setup["cell"], "instrument": setup["instrument"], "domain": setup["domain"],
        "empty": False, "cell_index": setup["cell_index"], "block_len": setup["block_len"],
        "draw_count": setup["draw_count"], "real_partial": _real_arm_dict(real_partial),
        "real_bench": _real_arm_dict(setup["real_bench"]),
        "fpr": fpr, "tpr": {str(g): tpr[g] for g in EDGE_GRID}, "mde": mde,
        "calibrated_margin_atr": margin,
        "verdict": cls, "walk_forward": wf, "source_meta": setup["source_meta"],
        "n_bars": setup["n_bars"], "n_harami": setup["n_harami"],
        "n_conditioned": setup["n_conditioned"], "pool_size": setup["pool_size"],
        "draws": draws,
    }


def _real_arm_dict(arm: RealArm) -> dict[str, Any]:
    """Serialisable real-arm summary (arrays dropped)."""
    return {"m": arm.m, "median": arm.median, "mean": arm.mean, "ci_low_1s": arm.ci_low_1s,
            "ci_lo_2s": arm.ci_lo_2s, "ci_hi_2s": arm.ci_hi_2s,
            "mean_ci_low_1s": arm.mean_ci_low_1s, "beats_rm_low_1s": arm.beats_rm_low_1s,
            "ci_width": arm.ci_width, "boot_se": arm.boot_se}


# --------------------------------------------------------------------------- #
# Dependency gates + P12 reconciliation (DEFECT guards; fail fast)
# --------------------------------------------------------------------------- #
def check_dependencies() -> dict[str, Any]:
    """Hard-fail unless EXP-068 artifacts exist and the six P5 cells are exactly the
    g015 PARTIAL-V2A passes minus EURUSD (D0 P5 / Data Requirements gate)."""
    for path in (EXP068_PARQUET, EXP068_VERDICT, EXP068_METADATA):
        if not path.exists():
            raise FileNotFoundError(f"dependency gate: missing {path}")
    verdict = json.loads(EXP068_VERDICT.read_text())
    g015_cells = set(verdict["native_per_arm"][BINDING_ARM]["g015_passes"]["cells"])
    expected = {f"{i}-{d}" for i, d in P5_CELLS}
    derived = {c for c in g015_cells if not c.startswith("EURUSD")}
    if derived != expected:
        raise ValueError(f"P5 family gate: EXP-068 g015 passes ex-EURUSD {sorted(derived)} "
                         f"!= frozen D0 P5 {sorted(expected)}")
    meta = json.loads(EXP068_METADATA.read_text())
    return {"exp068_g015_passes": sorted(g015_cells), "p5_family": sorted(expected),
            "exp068_is_defect": bool(meta.get("is_defect", True)),
            "exp068_source_files": {k: v.get("source_file")
                                    for k, v in meta.get("instrument_meta", {}).items()
                                    if k in {i for i, _ in P5_CELLS}}}


def reconcile_cell(result: dict[str, Any], anchors: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """P12: assert the real PARTIAL-V2A + BENCH arms reproduce EXP-068 per_cell_expectancy
    (m, median, ci_low_1s, mean_ci_low_1s, beats-RM contrast low) at 1e-9 (D0 P1)."""
    row: dict[str, Any] = {"cell": result["cell"], "checked": False}
    for aid, rk in ((BINDING_ARM, "real_partial"), (BENCH_ARM, "real_bench")):
        key = f"{result['cell']}|{aid}"
        anc = anchors.get(key)
        got = result[rk]
        if anc is None:
            row[f"{aid}_checked"] = False
            continue
        diffs = {f: _abs_diff(got.get(f), anc.get(f)) for f in
                 ("median", "ci_low_1s", "mean_ci_low_1s", "beats_rm_low_1s")}
        m_ok = got["m"] == int(anc["m"])
        ok = m_ok and all((d is not None and d <= RECON_TOL) for d in diffs.values())
        row.update({"checked": True, f"{aid}_checked": True, f"{aid}_m": got["m"],
                    f"{aid}_m_exp068": int(anc["m"]), f"{aid}_m_match": bool(m_ok),
                    **{f"{aid}_{f}_absdiff": diffs[f] for f in diffs},
                    f"{aid}_consistent": bool(ok)})
    row["consistent"] = bool(all(row.get(f"{a}_consistent", False)
                                  for a in (BINDING_ARM, BENCH_ARM)))
    return row


def _abs_diff(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    return abs(float(a) - float(b))


def load_anchors() -> dict[str, dict[str, Any]]:
    """EXP-068 per-cell PARTIAL-V2A + BENCH anchor rows for the six P5 cells (P12)."""
    df = pl.read_parquet(EXP068_PARQUET)
    sub = df.filter((pl.col("object") == OBJECT) & pl.col("arm").is_in([BINDING_ARM, BENCH_ARM]))
    out: dict[str, dict[str, Any]] = {}
    for row in sub.iter_rows(named=True):
        if (row["instrument"], row["domain"]) not in P5_CELLS:
            continue
        out[f"{row['instrument']}-{row['domain']}|{row['arm']}"] = {
            "m": row["m"], "median": row["median"], "ci_low_1s": row["ci_low_1s"],
            "mean_ci_low_1s": row["mean_ci_low_1s"], "beats_rm_low_1s": row["var_rm_median_low_1s"]}
    return out


# --------------------------------------------------------------------------- #
# Determinism replay (Leg 3) + output hashing
# --------------------------------------------------------------------------- #
def determinism_replay(results: list[dict[str, Any]], workers: int = 1) -> dict[str, Any]:
    """Assert frame-identical replay for the two fixed determinism cells (Leg 3).

    The production result (already computed in :func:`run`) is reused as one of the two
    compared computations; only the independent recompute is run here (cross-process when
    ``workers > 1``). Determinism is still proven by two independent passes, but the two
    determinism cells are no longer computed three times each. Every per-draw / scalar value
    is seeded by ``(cell_index, purpose, draw)`` and is process-independent, so reusing the
    production pass cannot mask non-determinism — and when ``workers > 1`` the two passes run
    in different processes, so cross-process reproducibility is now exercised, not just
    within-process replay."""
    produced = {(r["instrument"], r["domain"]): r for r in results if not r.get("empty")}
    replay = compute_cells(list(DETERMINISM_CELLS), workers)
    recomputed = {(r["instrument"], r["domain"]): r for r in replay if not r.get("empty")}
    checked, mismatches = [], []
    for cell in DETERMINISM_CELLS:
        a, b = produced.get(cell), recomputed.get(cell)
        checked.append(f"{cell[0]}-{cell[1]}")
        if (a is None or b is None or a.get("empty") or b.get("empty")
                or not _draws_equal(a, b) or not _scalars_equal(a, b)):
            mismatches.append(f"{cell[0]}-{cell[1]}")
    return {"determinism_pass": not mismatches, "cells_checked": checked,
            "non_deterministic": mismatches}


def _draws_equal(a: dict[str, Any], b: dict[str, Any]) -> bool:
    for n in NULLS:
        da, db = a["draws"][n], b["draws"][n]
        if len(da) != len(db):
            return False
        for x, y in zip(da, db):
            if not (_nan_eq(x["ci_low_1s"], y["ci_low_1s"]) and x["m"] == y["m"]
                    and _nan_eq(x["mean_ci_low_1s"], y["mean_ci_low_1s"])
                    and _nan_eq(x["beats_rm_low_1s"], y["beats_rm_low_1s"])):
                return False
    return True


def _scalars_equal(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return (a["verdict"]["verdict"] == b["verdict"]["verdict"] and _nan_eq(a["mde"], b["mde"])
            and a["walk_forward"]["flag"] == b["walk_forward"]["flag"])


def _nan_eq(a: float | None, b: float | None) -> bool:
    if a is None or b is None:
        return a is b
    return bool(a == b or (np.isnan(a) and np.isnan(b)))


def hash_outputs() -> dict[str, str]:
    """SHA-256 of each headline output (Leg 3 hash-pin for the byte-identical second pass)."""
    out: dict[str, str] = {}
    for name in HEADLINE_OUTPUTS:
        path = RESULTS_DIR / name
        if path.exists():
            out[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


# --------------------------------------------------------------------------- #
# Output flattening + writers
# --------------------------------------------------------------------------- #
def calibration_rows(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for r in results:
        if r.get("empty"):
            rows.append({"cell": r["cell"], "instrument": r["instrument"],
                         "domain": r["domain"], "verdict": "EMPTY_CELL"})
            continue
        fa, fb = r["fpr"]["A_matched_random_placement"], r["fpr"]["B_block_rotated_path"]
        rows.append({
            "cell": r["cell"], "instrument": r["instrument"], "domain": r["domain"],
            "verdict": r["verdict"]["verdict"], "reason": r["verdict"]["reason"],
            "draw_count": r["draw_count"], "m_partial": r["real_partial"]["m"],
            "fpr_median_nullA": fa["fpr_median"], "fpr_median_nullB": fb["fpr_median"],
            "fpr_conj_nullA": fa["fpr_conj"], "fpr_conj_nullB": fb["fpr_conj"],
            "fpr_controlled_both": r["verdict"]["fpr_controlled_both"],
            "fpr_retained_both": r["verdict"]["fpr_retained_both"],
            "mde_atr": r["mde"], "calibrated_margin_atr": r["calibrated_margin_atr"],
            "ci_width": r["real_partial"]["ci_width"],
            "degenerate_ci": r["verdict"]["degenerate_ci"],
            "temporal_flag": r["walk_forward"]["flag"], "block_len": r["block_len"],
            "n_conditioned": r["n_conditioned"], "pool_size": r["pool_size"]})
    return rows


def fpr_rows(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for r in results:
        if r.get("empty"):
            continue
        for n in NULLS:
            f = r["fpr"][n]
            rows.append({"cell": r["cell"], "null": n, "alpha0": ALPHA0,
                         "n_reportable": f["n_reportable"], "completion": f["completion"],
                         # Binding object (D0-amendment-003): conjunction-FPR + Wilson bounds.
                         "fpr_conj": f["fpr_conj"], "fpr_conj_lo": f["fpr_conj_lo"],
                         "fpr_conj_hi": f["fpr_conj_hi"], "fpr_conj_hw": f["fpr_conj_hw"],
                         # Disclosed diagnostic: median-leg FPR + Wilson bounds.
                         "fpr_median": f["fpr_median"], "fpr_median_lo": f["fpr_median_lo"],
                         "fpr_median_hi": f["fpr_median_hi"], "fpr_median_hw": f["fpr_median_hw"]})
    return rows


def tpr_mde_rows(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for r in results:
        if r.get("empty"):
            continue
        for g in EDGE_GRID:
            t = r["tpr"][str(g)]
            rows.append({"cell": r["cell"], "edge_atr": g, "tpr": t["tpr"],
                         "tpr_hw": t["tpr_hw"], "cell_mde_atr": r["mde"],
                         "m_partial": r["real_partial"]["m"]})
    return rows


def ci_width_rows(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"cell": r["cell"], "m_partial": r["real_partial"]["m"],
             "median": r["real_partial"]["median"], "ci_lo_2s": r["real_partial"]["ci_lo_2s"],
             "ci_hi_2s": r["real_partial"]["ci_hi_2s"], "ci_width": r["real_partial"]["ci_width"],
             "boot_se": r["real_partial"]["boot_se"],
             "degenerate_ci": r["verdict"]["degenerate_ci"]}
            for r in results if not r.get("empty")]


def temporal_rows(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for r in results:
        if r.get("empty"):
            continue
        wf = r["walk_forward"]
        for w in wf["windows"]:
            rows.append({"cell": r["cell"], "window": w["window"], "n": w["n"],
                         "window_median": w["median"], "powered": w["powered"],
                         "full_median": wf["full_median"], "boot_se": wf["boot_se"],
                         "final_window_median": wf["final_window_median"], "flag": wf["flag"]})
    return rows


def draw_rows(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for r in results:
        if r.get("empty") or "draws" not in r:
            continue
        for n in NULLS:
            for d, rec in enumerate(r["draws"][n]):
                rows.append({"cell": r["cell"], "null": n, "draw": d, "m": rec["m"],
                             "reportable": rec["reportable"], "median": rec["median"],
                             "ci_low_1s": rec["ci_low_1s"],
                             "mean_ci_low_1s": rec["mean_ci_low_1s"],
                             "beats_rm_low_1s": rec["beats_rm_low_1s"]})
    return rows


def _write_csv(records: list[dict[str, Any]], path: Path) -> None:
    frame = pl.DataFrame(records, strict=False) if records else pl.DataFrame({"empty": []})
    frame.write_csv(path)


def experiment_verdict(results: list[dict[str, Any]],
                       determinism: dict[str, Any]) -> dict[str, Any]:
    """CALIBRATION_DELIVERED / METHOD_DEFECT / INCONCLUSIVE (scope Experiment-level outcomes)."""
    cells = [r for r in results if not r.get("empty")]
    # Binding object: conjunction-FPR (D0-amendment-003), not the disclosed median leg.
    fpr_fail = sum(1 for r in cells
                   if any(r["fpr"][n]["fpr_conj"] > FPR_TOLERANCE for n in NULLS
                          if np.isfinite(r["fpr"][n]["fpr_conj"])))
    degenerate = [r["cell"] for r in cells if r["verdict"]["degenerate_ci"]]
    underpowered = [r["cell"] for r in cells
                    if r["verdict"]["verdict"] == "CALIBRATION_UNDERPOWERED"]
    if (fpr_fail >= METHOD_DEFECT_FPR_CELLS or degenerate
            or not determinism["determinism_pass"]):
        verdict = "METHOD_DEFECT"
    elif len(underpowered) >= UNDERPOWERED_CELLS:
        verdict = "INCONCLUSIVE"
    else:
        verdict = "CALIBRATION_DELIVERED"
    return {"experiment_verdict": verdict, "n_fpr_fail_cells": fpr_fail,
            "degenerate_ci_cells": degenerate, "underpowered_cells": underpowered,
            "pass_cells": [r["cell"] for r in cells if r["verdict"]["verdict"] == "PASS"],
            "fpr_excluded_cells": [r["cell"] for r in cells
                                   if r["verdict"]["verdict"] == "FPR_EXCLUDED"],
            "retained_tolerance_cells": [r["cell"] for r in cells
                                         if r["verdict"]["verdict"] == "RETAINED_FPR_TOLERANCE"],
            "mde_unresolved_cells": [r["cell"] for r in cells
                                     if r["verdict"]["verdict"] == "MDE_UNRESOLVED"]}


# --------------------------------------------------------------------------- #
# Plotting (5/5; bounded inputs from collected per-cell summaries — no reloads)
# --------------------------------------------------------------------------- #
def _cells_sorted(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted((r for r in results if not r.get("empty")), key=lambda r: r["cell"])


def plot_fpr(results: list[dict[str, Any]], path: Path) -> None:
    cells = _cells_sorted(results)
    fig, ax = plt.subplots(figsize=(11, 6))
    x = np.arange(len(cells))
    for off, n, col in ((-0.15, "A_matched_random_placement", "#1f77b4"),
                        (0.15, "B_block_rotated_path", "#ff7f0e")):
        # Binding object (D0-amendment-003): conjunction-FPR with Wilson 95% bounds.
        p = np.array([r["fpr"][n]["fpr_conj"] for r in cells], dtype=float)
        lo = np.array([r["fpr"][n]["fpr_conj_lo"] for r in cells], dtype=float)
        hi = np.array([r["fpr"][n]["fpr_conj_hi"] for r in cells], dtype=float)
        yerr = np.vstack([np.clip(p - lo, 0, None), np.clip(hi - p, 0, None)])
        ax.errorbar(x + off, p, yerr=yerr, fmt="o", ms=5, color=col, capsize=3,
                    label=n.split("_")[0] + " null (conjunction, binding)")
        # Disclosed median-leg FPR as a faint reference (no error bars; non-binding).
        med = np.array([r["fpr"][n]["fpr_median"] for r in cells], dtype=float)
        ax.scatter(x + off, med, marker="x", s=22, color=col, alpha=0.35,
                   label=n.split("_")[0] + " null (median leg, disclosed)")
    ax.axhline(ALPHA0, color="k", ls="--", lw=0.9, label=f"alpha0 = {ALPHA0}")
    ax.axhline(FPR_TOLERANCE, color="r", ls=":", lw=0.9, label=f"exclusion = {FPR_TOLERANCE}")
    ax.set_xticks(x, [r["cell"] for r in cells], rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("FPR  (binding conjunction = solid; median leg = faint x)")
    ax.set_title(f"{EXPERIMENT_ID}: per-cell binding conjunction-FPR (Wilson 95%) under two nulls")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_recovery(results: list[dict[str, Any]], path: Path) -> None:
    cells = _cells_sorted(results)
    fig, axes = plt.subplots(2, 3, figsize=(15, 8), sharex=True, sharey=True)
    for ax, r in zip(axes.ravel(), cells):
        g = np.array(EDGE_GRID, dtype=float)
        tpr = np.array([r["tpr"][str(gg)]["tpr"] for gg in EDGE_GRID], dtype=float)
        ax.plot(g, tpr, "o-", color="#1f77b4")
        ax.axhline(TPR_TARGET, color="k", ls="--", lw=0.8)
        if r["mde"] is not None:
            ax.axvline(r["mde"], color="g", ls=":", lw=1.0, label=f"MDE={r['mde']}")
            ax.legend(fontsize=7)
        ax.set_title(f"{r['cell']} (m={r['real_partial']['m']})", fontsize=9)
        ax.set_xlabel("planted edge g (ATR)")
    for ax in axes[:, 0]:
        ax.set_ylabel("TPR")
    fig.suptitle(f"{EXPERIMENT_ID}: per-cell planted-edge recovery (TPR vs g; target {TPR_TARGET})")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_mde_vs_count(results: list[dict[str, Any]], path: Path) -> None:
    cells = _cells_sorted(results)
    fig, ax = plt.subplots(figsize=(9, 6))
    for r in cells:
        m = r["real_partial"]["m"]
        if r["mde"] is not None:
            ax.scatter(m, r["mde"], s=60, color="#1f77b4")
            ax.annotate(r["cell"], (m, r["mde"]), fontsize=7, xytext=(4, 4),
                        textcoords="offset points")
        else:
            ax.scatter(m, max(EDGE_GRID), s=60, marker="x", color="r")
            ax.annotate(f"{r['cell']} (MDE_UNRESOLVED)", (m, max(EDGE_GRID)), fontsize=7,
                        xytext=(4, 4), textcoords="offset points")
    ax.set_xscale("log")
    ax.set_xlabel("realized TRAIN event count m (log)")
    ax.set_ylabel("per-cell planted-edge MDE (ATR)")
    ax.set_title(f"{EXPERIMENT_ID}: MDE vs realized TRAIN event count")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_precision(results: list[dict[str, Any]], path: Path) -> None:
    cells = _cells_sorted(results)
    fig, ax = plt.subplots(figsize=(11, 6))
    x = np.arange(len(cells))
    width = 0.35
    for i, n in enumerate(NULLS):
        hw = [r["fpr"][n]["fpr_conj_hw"] for r in cells]
        ax.bar(x + (i - 0.5) * width, hw, width,
               label=n.split("_")[0] + " conjunction-FPR hw")
    ax.axhline(FPR_WILSON_HW_MAX, color="r", ls="--", lw=0.9,
               label=f"FPR hw target {FPR_WILSON_HW_MAX}")
    comp = [min(r["fpr"][n]["completion"] for n in NULLS) for r in cells]
    ax2 = ax.twinx()
    ax2.plot(x, comp, "k^-", label="min draw completion")
    ax2.axhline(DRAW_COMPLETION_FLOOR, color="grey", ls=":", lw=0.8)
    ax2.set_ylabel("draw completion")
    ax2.set_ylim(0.0, 1.05)
    ax.set_xticks(x, [r["cell"] for r in cells], rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("FPR Wilson half-width")
    ax.set_title(f"{EXPERIMENT_ID}: calibration precision + draw completion")
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_temporal(results: list[dict[str, Any]], path: Path) -> None:
    cells = _cells_sorted(results)
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    for ax, r in zip(axes.ravel(), cells):
        wf = r["walk_forward"]
        wins = [w for w in wf["windows"] if w["median"] is not None]
        if wins:
            xs = [w["window"] for w in wins]
            ys = [w["median"] for w in wins]
            cols = ["#1f77b4" if w["powered"] else "#cccccc" for w in wins]
            ax.scatter(xs, ys, c=cols, s=30, zorder=3)
            ax.plot(xs, ys, color="#1f77b4", lw=0.6, zorder=2)
        if wf["full_median"] is not None and wf["boot_se"] is not None:
            ax.axhline(wf["full_median"], color="k", ls="-", lw=0.8)
            ax.axhline(wf["full_median"] - wf["boot_se"], color="k", ls="--", lw=0.6)
            ax.axhline(wf["full_median"] + wf["boot_se"], color="k", ls="--", lw=0.6)
        ax.set_title(f"{r['cell']}: {wf['flag']}", fontsize=9)
        ax.set_xlabel(f"{WALKFWD_MONTHS}-month window")
    for ax in axes[:, 0]:
        ax.set_ylabel("window median (ATR)")
    fig.suptitle(f"{EXPERIMENT_ID}: TRAIN-only walk-forward temporal stability "
                 "(full median +/- 1 SE)")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def make_plots(results: list[dict[str, Any]]) -> None:
    plot_fpr(results, PLOTS_DIR / "fpr_per_cell.png")
    plot_recovery(results, PLOTS_DIR / "recovery_mde_curves.png")
    plot_mde_vs_count(results, PLOTS_DIR / "mde_vs_event_count.png")
    plot_precision(results, PLOTS_DIR / "calibration_precision.png")
    plot_temporal(results, PLOTS_DIR / "temporal_stability.png")


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def _chunk_specs(cells: list[tuple[str, str]],
                 setups: dict[tuple[str, str], dict[str, Any]]
                 ) -> list[tuple[tuple[str, str], str, int, int, int]]:
    """Draw-chunk work units (cell, null, lo, hi, draw_count), grouped by cell then null so a
    worker's size-1 context cache stays warm across a cell's consecutive chunks."""
    specs: list[tuple[tuple[str, str], str, int, int, int]] = []
    for c in cells:
        setup = setups[c]
        if setup.get("empty"):
            continue
        draw_count = setup["draw_count"]
        for null in NULLS:
            for lo in range(0, N_DRAWS, DRAW_CHUNK):
                specs.append((c, null, lo, min(lo + DRAW_CHUNK, N_DRAWS), draw_count))
    return specs


def compute_cells(cells: list[tuple[str, str]], workers: int) -> list[dict[str, Any]]:
    """Calibrate ``cells`` with draw-level parallelism; results returned in input order.

    Each cell's 2 x ``N_DRAWS`` draws are independent and seeded by
    ``(cell_index, purpose, draw)``, so they are computed as ``DRAW_CHUNK``-sized units spread
    across one pool and reassembled in draw-index order — byte-identical to a serial pass for
    any ``workers`` / chunk size. This lets the slow high-count cell (GBPUSD-5m) use every core
    instead of a single one. A single pool spans both phases so a worker's context cache from
    setup is reused by that cell's draw chunks; aggregation runs in the parent."""
    workers = max(1, workers)
    if workers <= 1:
        setups = {c: _cell_setup(c) for c in tqdm(cells, desc="cell setup")}
        chunk_out: dict[tuple[str, str], list[tuple[int, list[dict[str, Any]]]]] = {}
        for spec in tqdm(_chunk_specs(cells, setups), desc="draw chunks"):
            key, lo, res = _draw_chunk(*spec)
            chunk_out.setdefault(key, []).append((lo, res))
        return [_assemble_cell(c, setups[c], chunk_out) for c in cells]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        setup_futs = {ex.submit(_cell_setup, c): c for c in cells}
        setups = {}
        for fut in tqdm(as_completed(setup_futs), total=len(setup_futs), desc="cell setup"):
            setups[setup_futs[fut]] = fut.result()
        chunk_out = {}
        chunk_futs = {ex.submit(_draw_chunk, *spec): spec for spec in _chunk_specs(cells, setups)}
        for fut in tqdm(as_completed(chunk_futs), total=len(chunk_futs), desc="draw chunks"):
            key, lo, res = fut.result()
            chunk_out.setdefault(key, []).append((lo, res))
    return [_assemble_cell(c, setups[c], chunk_out) for c in cells]


def run(workers: int = 1) -> dict[str, Any]:
    """Run the six-cell calibration map and write artifacts. Byte-identical for any workers."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    deps = check_dependencies()
    anchors = load_anchors()
    workers = max(1, workers)
    results = compute_cells(list(P5_CELLS), workers)
    recon = [reconcile_cell(r, anchors) for r in results if not r.get("empty")]
    recon_ok = bool(recon) and all(r["consistent"] for r in recon)
    determinism = determinism_replay(results, workers)
    exp_verdict = experiment_verdict(results, determinism)
    write_outputs(results, recon, recon_ok, determinism, exp_verdict, deps)
    make_plots(results)
    return {**exp_verdict, "recon_ok": recon_ok, "determinism": determinism}


def write_outputs(results: list[dict[str, Any]], recon: list[dict[str, Any]], recon_ok: bool,
                  determinism: dict[str, Any], exp_verdict: dict[str, Any],
                  deps: dict[str, Any]) -> None:
    """Persist the calibration map, FPR/TPR/CI/temporal tables, per-draw parquet, and metadata."""
    _write_csv(calibration_rows(results), RESULTS_DIR / "calibration_map.csv")
    _write_csv(fpr_rows(results), RESULTS_DIR / "fpr_per_cell.csv")
    _write_csv(tpr_mde_rows(results), RESULTS_DIR / "tpr_mde_per_cell.csv")
    _write_csv(ci_width_rows(results), RESULTS_DIR / "ci_width_per_cell.csv")
    _write_csv(temporal_rows(results), RESULTS_DIR / "temporal_stability.csv")
    _write_csv(recon, RESULTS_DIR / "reconciliation.csv")
    pl.DataFrame(draw_rows(results), strict=False).write_parquet(
        RESULTS_DIR / "draw_verdicts.parquet")
    _write_metadata(results, recon, recon_ok, determinism, exp_verdict, deps)


def _write_metadata(results: list[dict[str, Any]], recon: list[dict[str, Any]], recon_ok: bool,
                    determinism: dict[str, Any], exp_verdict: dict[str, Any],
                    deps: dict[str, Any]) -> None:
    is_defect = (exp_verdict["experiment_verdict"] == "METHOD_DEFECT" or not recon_ok
                 or not determinism["determinism_pass"] or deps["exp068_is_defect"])
    meta = {
        "experiment_id": EXPERIMENT_ID,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "016", "hypothesis": "HYP-023", "family": "CF-HA-HARAMI-001",
        "candidate": "CF-HA-HARAMI-001/CAND-001",
        "checkpoint": "2026-06-18-016-harami-candidate-screening",
        "design_refs": "design.md §5 EXP-070; D0-predeclarations.md P1/P5/P7/P12",
        "amendments_inherited": ["D0-amendment-001-dual-parallel-substrate (native object)",
                                 "D0-amendment-002-drop-exp067"],
        "title": "Event-Level Method Calibration (EXP-027/044-analog, TRAIN-only)",
        "object": OBJECT, "binding_arm": BINDING_ARM,
        "stratum": ("TRAIN-only (first 49% per file); nested TEST (next 21%) + final-30% "
                    "holdout sealed"),
        "test_reads": 0, "candidate_slots": 0,
        "p5_family": [f"{i}-{d}" for i, d in P5_CELLS],
        "nulls": {"A_matched_random_placement": ("matched-count random draw from the eligible "
                  "MA-regime pool excluding real signal entries, resolved through PARTIAL-V2A on "
                  "the real OHLC path (the D0 P7 literal RM-native mechanism); permutes placement. "
                  "Both pseudo-signal and RM arms use real entry geometry on the real path"),
                  "B_block_rotated_path": ("real harami entries + entry geometry resolved "
                  "against a block-circular-rotated OHLC path (contiguous bars rotated as whole "
                  "blocks of length round(n_bars**(1/3))); permutes outcomes, holds placement. "
                  "Symmetric RM arm (D0-amendment-003): the matched-random arm uses REAL entry "
                  "geometry (entry close, time caps, barriers from the real path at the drawn "
                  "indices) resolved FORWARD on the same rotated path, so both Null-B arms differ "
                  "only in placement and from the real signal only in the permuted forward path — "
                  "the beats-RM contrast has true edge 0")},
        "binding_fpr_object": ("full conjunction (ci_low_1s>0 AND mean_ci_low_1s>0 AND "
                  "beats_rm_low_1s>0) — the exact P4/P9 EXP-071 cell-acceptance event "
                  "(D0-amendment-003). The median-leg FPR P(ci_low_1s>0) is computed and reported "
                  "as a disclosed, non-binding diagnostic (it inherits substrate drift on this "
                  "absolute-return population and does not gate). All thresholds (alpha0=0.05, "
                  "0.06 tolerance, >2/3 defect rule) carry over unchanged onto the conjunction"),
        "calibrated_margin": ("per-cell P9 condition-4 input (R1.2 analog; D0-amendment-003): the "
                  "empirical (1-alpha0) quantile of the Null-A pseudo-signal median point estimate "
                  "over reportable draws; recorded per cell in calibration_map.csv and per_cell "
                  "below for the EXP-071 freeze file (no new bootstrap/test/plot)"),
        "planted_edge": {"grid_atr": list(EDGE_GRID), "tpr_target": TPR_TARGET,
                         "method": ("translation-equivariance shortcut: ci_low_1s(g) = "
                                    "ci_low_1s(0) + g; TPR(g) = mean(ci_low_1s(0) > -g) over "
                                    "reportable Null-A draws; bootstrap once per draw at g=0")},
        "calibration_design": {"n_draws": N_DRAWS, "alpha0": ALPHA0,
                               "fpr_tolerance": FPR_TOLERANCE, "power_floor": POWER_FLOOR,
                               "draw_completion_floor": DRAW_COMPLETION_FLOOR,
                               "fpr_wilson_hw_max": FPR_WILSON_HW_MAX,
                               "tpr_wilson_hw_max": TPR_WILSON_HW_MAX,
                               "walkforward_months": WALKFWD_MONTHS},
        "inference_constants_inherited_from_exp068": {
            "n_boot": N_BOOT, "boot_batch": BOOT_BATCH, "base_seed": BASE_SEED,
            "recon_tol": RECON_TOL,
            "note": ("median CI (bootstrap_median_distribution + median_ci), raw-mean CI "
                     "(bootstrap_stat_distribution), beats-RM (contrast_ci), the PARTIAL-V2A "
                     "leg resolver (resolve_legs/weighted_returns), and the matched-random "
                     "mechanism are imported from EXP-068 and used unchanged in semantics")},
        "rng_purpose_blocks": {"nullA_draw": PB_NULLA_DRAW, "nullA_med": PB_NULLA_MED,
                               "nullA_mean": PB_NULLA_MEAN, "nullA_rm_draw": PB_NULLA_RM_DRAW,
                               "nullA_rm_med": PB_NULLA_RM_MED, "nullB_rot": PB_NULLB_ROT,
                               "nullB_med": PB_NULLB_MED, "nullB_mean": PB_NULLB_MEAN,
                               "nullB_rm_draw": PB_NULLB_RM_DRAW, "nullB_rm_med": PB_NULLB_RM_MED,
                               "disjoint_from_exp068": ("all blocks >= 1_000_000; EXP-068 max is "
                                "the V2A-ADVNONE block 300_000 + small offsets; draw index < "
                                "N_DRAWS=1000 < 100_000 gap, so no stream collides")},
        "dependency_gate": deps,
        "p12_reconciliation": {"ok": recon_ok, "tol": RECON_TOL,
                               "rows": recon,
                               "note": ("real PARTIAL-V2A + BENCH arms reproduce EXP-068 "
                                        "per_cell_expectancy (m, median, ci_low_1s, "
                                        "mean_ci_low_1s, beats-RM low) at 1e-9 — the byte-reuse "
                                        "proof before any null/planted measurement (D0 P1)")},
        "determinism": determinism,
        "experiment_verdict_block": exp_verdict,
        "per_cell": {r["cell"]: {"verdict": r["verdict"]["verdict"],
                                 "reason": r["verdict"]["reason"],
                                 "fpr_conj_nullA":
                                     r["fpr"]["A_matched_random_placement"]["fpr_conj"],
                                 "fpr_conj_nullB": r["fpr"]["B_block_rotated_path"]["fpr_conj"],
                                 "fpr_median_nullA":
                                     r["fpr"]["A_matched_random_placement"]["fpr_median"],
                                 "fpr_median_nullB": r["fpr"]["B_block_rotated_path"]["fpr_median"],
                                 "mde_atr": r["mde"],
                                 "calibrated_margin_atr": r["calibrated_margin_atr"],
                                 "ci_width": r["real_partial"]["ci_width"],
                                 "temporal_flag": r["walk_forward"]["flag"],
                                 "block_len": r["block_len"], "m_partial": r["real_partial"]["m"]}
                     for r in results if not r.get("empty")},
        "verdict_label_map": {
            "PASS": ("conjunction-FPR<=alpha0 both nulls + finite CI + finite MDE; "
                     "EXP-071 binding-family eligible"),
            "RETAINED_FPR_TOLERANCE": ("conjunction-FPR in (alpha0, 0.06] under >=1 null — D0 P7 "
                                       "Leg 1 / amendment-003 retained-with-record (not PASS)"),
            "FPR_EXCLUDED": ("conjunction-FPR > 0.06 under >=1 null OR degenerate CI; "
                             "dropped from family"),
            "MDE_UNRESOLVED": ("conjunction-FPR controlled + finite CI but no finite MDE at "
                               "TPR>=0.80 (disclosed)"),
            "CALIBRATION_UNDERPOWERED": ("conjunction-FPR precision / draw-completion shortfall "
                                         "(precision-only re-run)")},
        "real_price_discipline": ("every per-event return is a direction-signed ATR-normalised "
                                  "real-price excursion; HA candles used for harami detection "
                                  "only; no HA-price metric; gross only (no costs/financing)"),
        "holdout_fence": ("EXP-068 load_train_1m reads only the first floor(0.7*floor(0.7*total)) "
                          "file-order 1-minute rows per instrument; domain bars fenced to "
                          "train_end_epoch; TEST (next 21%) and final-30% holdout never read; "
                          "0 counted TEST reads (six P5 strata stay at 0 — test-read-ledger.md)"),
        "registry": ("CF-HA-HARAMI-001/HYP-023 (EXP-070); method calibration only — no candidate "
                     "screen, no registry verdict, 0 candidate slots, 0 TEST reads. Gates EXP-071 "
                     "(D0 P7/P8): the PASS set is the EXP-071 binding-family membership; "
                     "FPR_EXCLUDED cells are dropped with record into the EXP-071 freeze file"),
        "is_defect": bool(is_defect),
    }
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(meta, indent=2, default=str))
    # Hash-pin headline outputs after they are written (Leg 3 byte-identical second-pass anchor).
    meta["output_sha256"] = hash_outputs()
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(meta, indent=2, default=str))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=f"{EXPERIMENT_ID} event-level method calibration (TRAIN-only, 0 TEST reads)")
    parser.add_argument("--workers", type=int, default=os.cpu_count() or 1,
                        help="draw-level process workers (default: all cores). Draws are spread "
                             "across workers and reassembled in index order, so output is "
                             "byte-identical for any value.")
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = _parse_args()
    workers = max(1, args.workers)
    LOGGER.info("%s: calibrating %s P5 cells on %s worker(s)", EXPERIMENT_ID,
                len(P5_CELLS), workers)
    summary = run(workers=workers)
    LOGGER.info("\n=== %s complete (event-level method calibration) ===", EXPERIMENT_ID)
    LOGGER.info("experiment verdict: %s", summary["experiment_verdict"])
    LOGGER.info("P12 reconciliation ok: %s | determinism pass: %s", summary["recon_ok"],
                summary["determinism"]["determinism_pass"])
    LOGGER.info("PASS cells: %s", summary["pass_cells"])
    LOGGER.info("RETAINED(tol): %s | FPR_EXCLUDED: %s | MDE_UNRESOLVED: %s | underpowered: %s",
                summary["retained_tolerance_cells"], summary["fpr_excluded_cells"],
                summary["mde_unresolved_cells"], summary["underpowered_cells"])
    LOGGER.info("artifacts -> %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
