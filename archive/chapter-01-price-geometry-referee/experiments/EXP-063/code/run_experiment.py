"""EXP-063 — MA(20,50)-Substrate Adverse Geometry & the Mean Investigation (dual-object).

``CF-HA-HARAMI-001`` / HYP-016 — Phase 015 **lead L3** (**dual conditioning object**).
Governing design/D0: ``docs/experiments-docs/checkpoints/2026-06-17-015-ma-substrate-
conditioned-harami-full-surface/`` (``design.md`` §3/§4/§5/§7; ``D0-predeclarations.md`` P1-P12;
``D0-amendment-001-dual-parallel-substrate.md``). TRAIN-only, gross; **0 candidate slots,
0 TEST reads**.

**Re-run under D0 Amendment 001 (2026-06-17).** The prior EXP-063 measured a single MA adverse
surface labelled *hybrid* but actually conditioning on MA-segment ``/STRONG-STAT`` -- the **native**
object. The genuine **hybrid** object (ZigZag-``/STRONG-STAT`` mask x MA adverse geometry) was never
computed. This re-run emits the full 4-variant adverse axis **for both objects individually**
(separate variant arms, separate matched-random nulls, separate mean decomposition, separate
readout -- never pooled) and supersedes the prior result in place.

**The two coupled questions (scope §Hypothesis), per object.**
(1) *Median lever* — does varying **only the adverse target** (benchmark **1:1** -> the
extreme-anchored >=1:1 **``/ADV-EXTREME-rr1``**) keep a median-viable, signal-attributable edge on
the MA(20,50) substrate (variant median CI_low>0, >=30 events, beats its **own object's**
matched-random-on-MA null, clears **P11 with the P6 non-4h rule**)?
(2) *The mean investigation (decisive, P4)* — EXP-060B found the MA edge is **median-only**
(mean ~0/negative, skew gap 1.20 ATR from the uncapped ``/ADV-NONE`` downside). EXP-063 asks **why
the mean is negative and whether bounding the downside fixes it**, per object: per variant the
**raw mean + 10% trimmed mean + worst-5% tail-share**, and the **bounded-downside recovery
contrast** ``mean(bounded) - mean(/ADV-NONE)``.

The two conditioning objects share the **same** frozen HA-harami detection and the **same** MA
outcome geometry (``rd`` / ``M_sofar`` / fav / cap / ``/ADV-EXTREME`` MA-segment extreme, all from
the shared MA in-progress state); they differ **only** in the ``/STRONG-STAT`` conditioning filter
(P2):

  * **native** (``M-*``) -- ``/STRONG-STAT`` p75 on the in-progress confirmed **MA segment**;
    population byte-identical to EXP-061 ``M0`` / EXP-060B BENCH-MA; the ``M-BENCH`` variant
    **reproduces EXP-061 M0** per-cell median + m (P12).
  * **hybrid** (``H-*``) -- ``/STRONG-STAT`` p75 on the in-progress confirmed **ZigZag move** (mask
    byte-identical to EXP-053/060/061 ``H0``), applied through the **same** MA geometry; the
    ``H-BENCH`` variant **reproduces EXP-061 H0** per-cell median + m (P12). Genuinely new for the
    adverse axis; no EXP-060B/057 outcome anchor.

Each object has its **own** matched-random-on-MA null per variant, matched to its own qualifying
count and excluding its own signal entries, on disjoint dedicated RNG streams. Binding endpoint =
per-event **median** gross ATR-normalised return (P3/P14, P15 fills), per object. The **mean** is
the P4 diagnostic co-primary -- the decisive content of this read -- but **never a blind
disqualifier** (P4 closure-on-mean rule). ``/ADV-NONE`` is the **disclosed unbounded reference**
(the skew source under study), not a viability candidate; ``/ADV-EXTREME-raw`` is a disclosed
secondary.

Adverse-leg primitives reuse ``xen.adverse_targets`` wholesale (substrate-generic). The favourable
target (0.50*M_sofar), the MA-defined adaptive cap, the P15 resolver, the realised returns, the
median/mean/trim/tail bootstrap, and the matched-random selector are reused from the EXP-061
dual-object MA pipeline. ``/ADV-NONE``'s MAE/tail is cross-checked vs **EXP-062**'s per-object
``mae_tail_decomposition.csv`` (disclosed L2->L3 hand-off).

Detection on HA candles; every outcome metric on real prices; MA(20,50) on real close. Outputs
under ``results/`` and ``plots/``; created in orchestration. Output is byte-identical for any
``--workers`` value (order-independent per-cell RNG + fixed merge order). The two objects are never
pooled. **Do not adjudicate G-015** -- single terminal gate after the full Phase 015 slate.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Pin per-process native thread pools to 1 BEFORE importing polars/numpy:
# parallelism is process-level (one worker per instrument), so N workers x M
# library threads would oversubscribe the CPU. Aggregation/bootstrap stay
# byte-identical single-threaded (OHLC aggregation is first/max/min/last/integer-
# sum -- order-independent; the bootstrap is numpy resampling, not BLAS).
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
DATA_DIR = PROJECT_ROOT / "data" / "timebars"
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
# P12 reconciliation anchor: EXP-061's per-cell parquet carries the BENCH arms (labels M0/H0).
EXP061_PARQUET = EXPERIMENTS_ROOT / "EXP-061" / "results" / "per_cell_expectancy.parquet"
# Disclosed L2->L3 cross-check: EXP-062's per-object MAE tail decomposition.
EXP062_TAIL_CSV = EXPERIMENTS_ROOT / "EXP-062" / "results" / "mae_tail_decomposition.csv"

from xen.adverse_targets import (  # noqa: E402
    ADV_BUFFER_FRAC,
    ADV_FLOOR_FRAC,
    adverse_extreme_raw,
    adverse_extreme_rr1,
    adverse_none_sentinel,
    faded_move_extreme,
)
from xen.bar_aggregator import aggregate_ohlc  # noqa: E402
from xen.capture_barriers import (  # noqa: E402
    CLASS_ADV,
    CLASS_DATA_CENSORED,
    CLASS_FAV,
)
from xen.expectancy import (  # noqa: E402
    InProgressState,
    adaptive_time_caps_by_epoch,
    benchmark_barriers,
    bootstrap_median_distribution,
    contrast_ci,
    live_in_progress_state,
    live_strong_stat,
    median_ci,
    qualifying_mask,
    realised_returns,
    resolve_path_ordered,
)
from xen.favourable_targets import paired_median_contrast_ci  # noqa: E402
from xen.ha_harami import detect_ha_harami  # noqa: E402
from xen.heiken_ashi_generator import generate_heiken_ashi  # noqa: E402
from xen.position_exits import PX_CLASS_LABELS, exit_reason_weights  # noqa: E402
from xen.zigzag import generate_zigzag, wilder_atr  # noqa: E402

# --------------------------------------------------------------------------- #
# Constants (Phase 014-B / 015 D0 frozen + EXP-057/060/061 inherited; no tuning)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-063"
INSTRUMENTS: list[str] = [
    "BTCUSD", "EURUSD", "USTEC", "XAUUSD", "GBPUSD", "USDJPY", "USDCHF",
    "USDCAD", "AUDUSD", "NZDUSD", "EURJPY", "GBPJPY", "AUDJPY", "US500",
    "US2000", "DE30", "JP225",
]
DOMAINS: dict[str, tuple[int, float | None]] = {
    "5m": (5, None), "15m": (15, 0.90), "30m": (30, 0.90),
    "1h": (60, 0.90), "2h": (120, 0.90), "4h": (240, 0.90),
}
EXCLUDED_CELLS: set[tuple[str, str]] = {("US500", "4h"), ("JP225", "2h"), ("JP225", "4h")}
ANALYSIS_FRACTION = 0.7
TRAIN_FRACTION = 0.7
ATR_PERIOD = 14
ATR_MULT = 1.0                     # P1 ZigZag (hybrid conditioning + disclosed contrast)
MA_FAST, MA_SLOW = 20, 50          # P1 MA-segmentation substrate (fixed, not swept)
POWER_FLOOR = 30                   # P10/P14: minimum qualifying events to report
P11_MIN_CELLS, P11_MIN_INSTR = 5, 3
P6_MIN_NON_4H = 3                  # P6: >=3 qualifying cells outside the 4h domain
LOW_N_4H = 60                      # P4 concentration: a 4h cell with m<60 is low-n (EXP-060B 8/14)
TRIM_FRAC = 0.10                   # P4: 10% symmetric trimmed mean
TAIL_FRAC = 0.05                   # P4: worst-5% tail-share
RECON_TOL = 1e-9                   # P12 EXP-061/060B reproduction tolerance
N_BOOT = 10_000                    # P14 bootstrap resamples
BOOT_BATCH = 2_000                 # bounded bootstrap memory batch
BASE_SEED = 20260616               # frozen master seed (identical to EXP-060/061)
EXCLUDED_FILE_MARKERS = ("analysis70", "analysis_slice", "first70")
DE30_DISCLOSURE = (
    "DE30 truncated history: broker m1 history ends 2026-01-16; counts derive "
    "from its own realized timeline and are not span-comparable (VAL-003).")
LOGGER = logging.getLogger(EXPERIMENT_ID)

# --------------------------------------------------------------------------- #
# Conditioning objects (D0 Amendment 001; reported individually, never pooled)
# --------------------------------------------------------------------------- #
# Each object resolves the full 4-variant adverse axis on the SAME MA geometry; only
# the /STRONG-STAT conditioning mask differs. The native M-BENCH reproduces EXP-061 M0
# and the hybrid H-BENCH reproduces EXP-061 H0 (P12); the median/m are RNG-independent.
OBJECTS: tuple[str, ...] = ("nat", "hyb")
OBJECT_NAME: dict[str, str] = {
    "nat": "native (MA-segment /STRONG-STAT; reconciles EXP-061 M0)",
    "hyb": "hybrid (ZigZag /STRONG-STAT x MA geometry; reconciles EXP-061 H0, NEW adverse axis)",
}
OBJECT_BENCH_LABEL: dict[str, str] = {"nat": "M0", "hyb": "H0"}     # EXP-061 reconciliation label

# --------------------------------------------------------------------------- #
# Adverse-target variant set (OAT on the adverse leg; MA substrate)
# --------------------------------------------------------------------------- #
# V-BENCH (1:1) and V-RR1 are the BINDING bounded-downside axis (P7). V-NONE is the
# disclosed unbounded reference (the skew source). V-RAW is the disclosed tight-stop
# secondary. Favourable target + MA adaptive cap held at benchmark for every variant.
VARIANTS: tuple[str, ...] = ("V-BENCH", "V-RR1", "V-NONE", "V-RAW")
BOUNDED: tuple[str, ...] = ("V-BENCH", "V-RR1")          # binding bounded-downside axis
ADV_MODEL: dict[str, str] = {
    "V-BENCH": "benchmark 1:1", "V-RR1": "/ADV-EXTREME-rr1 (extreme-anchored, >=1:1)",
    "V-NONE": "/ADV-NONE (unbounded reference; skew source)",
    "V-RAW": "/ADV-EXTREME-raw (buffered extreme, R:R free)",
}

# Per-object, per-variant, per-purpose RNG offset blocks (distinct deterministic streams
# per cell/object/variant/purpose). Native V-BENCH reuses EXP-061's M0 + RM0 purposes;
# hybrid V-BENCH reuses EXP-061's H0 + RH0 purposes -- so each reproduces its EXP-061
# anchor's median/mean exactly. Every other (object, variant) uses a fresh block far from
# EXP-061's (which used <= 85000), so no existing stream shifts and the two objects' nulls
# are disjoint.
VARIANT_PB: dict[str, dict[str, dict[str, int]]] = {
    "nat": {
        "V-BENCH": {"med": 9000, "mean": 23000, "trim": 43000,
                    "rm_draw": 61000, "rm_med": 62000, "rm_mean": 63000, "rm_trim": 64000,
                    "paired": 0},
        "V-RR1": {"med": 210000, "mean": 211000, "trim": 212000,
                  "rm_draw": 213000, "rm_med": 214000, "rm_mean": 215000, "rm_trim": 216000,
                  "paired": 217000},
        "V-NONE": {"med": 220000, "mean": 221000, "trim": 222000,
                   "rm_draw": 223000, "rm_med": 224000, "rm_mean": 225000, "rm_trim": 226000,
                   "paired": 227000},
        "V-RAW": {"med": 230000, "mean": 231000, "trim": 232000,
                  "rm_draw": 233000, "rm_med": 234000, "rm_mean": 235000, "rm_trim": 236000,
                  "paired": 237000},
    },
    "hyb": {
        "V-BENCH": {"med": 81000, "mean": 83000, "trim": 85000,
                    "rm_draw": 71000, "rm_med": 72000, "rm_mean": 73000, "rm_trim": 74000,
                    "paired": 0},
        "V-RR1": {"med": 310000, "mean": 311000, "trim": 312000,
                  "rm_draw": 313000, "rm_med": 314000, "rm_mean": 315000, "rm_trim": 316000,
                  "paired": 317000},
        "V-NONE": {"med": 320000, "mean": 321000, "trim": 322000,
                   "rm_draw": 323000, "rm_med": 324000, "rm_mean": 325000, "rm_trim": 326000,
                   "paired": 327000},
        "V-RAW": {"med": 330000, "mean": 331000, "trim": 332000,
                  "rm_draw": 333000, "rm_med": 334000, "rm_mean": 335000, "rm_trim": 336000,
                  "paired": 337000},
    },
}

# Per-cell §4 mean verdict -> integer code (the P4 closure-rule readout).
MEAN_STATUS_CODES: dict[str, int] = {
    "EVIDENCE_FOR": 0, "MEDIAN_ONLY": 1, "EVIDENCE_AGAINST": 2,
    "NOT_POWERED": 3, "EXCLUDED": 4,
}


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ArmSpec:
    """The single-leg favourable capture geometry (exact EXP-053/060B BENCH leg)."""

    aid: str
    weights: tuple[float, ...]


# Single favourable leg at 0.50*M_sofar; only the adverse level varies across variants.
BENCH = ArmSpec("BENCH", (1.0,))


@dataclass(frozen=True)
class ArmResult:
    """One arm's per-cell resolved population summary + qualifying returns.

    Carries the median (binding), mean + 10% trimmed mean + worst-5% tail-share
    (P4 diagnostic) point estimates and CIs, the per-event arrays (``r_full`` and
    ``qual`` over the arm's own entry order, used for the variant-vs-benchmark
    paired contrast on the common qualifying subset), and the median/mean bootstrap
    distributions used by the independent signal-vs-null and recovery contrasts.
    """

    m: int
    median: float | None
    mean: float | None
    trimmed_mean: float | None
    tail_share_worst5: float | None
    ci_low_1s: float | None
    ci_lo_2s: float | None
    ci_hi_2s: float | None
    mean_ci_low_1s: float | None
    mean_ci_lo_2s: float | None
    mean_ci_hi_2s: float | None
    trim_ci_low_1s: float | None
    trim_ci_lo_2s: float | None
    trim_ci_hi_2s: float | None
    r_firsthit: float | None       # FAV/(FAV+ADV) over qualifying events; disclosed
    win_rate: float | None
    data_censored: int
    exit_weights: dict[str, float]
    population: int                # built-barrier population (pre-resolution)
    adv_count: int                 # qualifying events resolving to the ADV stop (V-NONE invariant)
    block_len: int
    r_e: np.ndarray                # qualifying weighted returns in entry order
    r_full: np.ndarray            # per-entry returns over the arm's entry order (NaN-free; raw)
    qual: np.ndarray               # qualifying mask aligned to the arm's entry order
    dist: np.ndarray               # bootstrap median distribution (may be empty)
    mean_dist: np.ndarray          # bootstrap mean distribution (may be empty)
    draw_count: int = 0            # matched-random arms: the matched draw target


# --------------------------------------------------------------------------- #
# I/O helpers (TRAIN-only loader; never sorts/collects the full file)
# --------------------------------------------------------------------------- #
def find_source_file(instrument: str) -> Path:
    """Return the newest full (non-derivative) 1-minute Parquet for one symbol."""
    matches = sorted(
        p for p in DATA_DIR.glob(f"timebars_{instrument.lower()}_*.parquet")
        if not any(marker in p.name for marker in EXCLUDED_FILE_MARKERS)
    )
    if not matches:
        raise FileNotFoundError(f"no 1-minute source file for {instrument} under {DATA_DIR}")
    return matches[-1]


def load_train_1m(instrument: str) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Load exactly the TRAIN 1-minute rows (first 49%) by file-order prefix (F01)."""
    path = find_source_file(instrument)
    total_rows = int(pl.scan_parquet(path).select(pl.len()).collect().item())
    analysis_rows = int(total_rows * ANALYSIS_FRACTION)
    train_rows = int(analysis_rows * TRAIN_FRACTION)
    cols = ["Symbol", "OpenTime", "CloseTime", "Open", "High", "Low", "Close", "TickVolume"]
    train = pl.scan_parquet(path).select(cols).slice(0, train_rows).collect()
    if not train.get_column("CloseTime").is_sorted():
        raise RuntimeError(f"{instrument}: TRAIN slice not chronological by CloseTime")
    meta = {
        "source_file": path.name, "total_rows_1m": total_rows,
        "analysis_rows_1m": analysis_rows, "train_rows_1m": train_rows,
        "train_end_ts": str(train.get_column("CloseTime")[-1]),
        "train_end_epoch_s": int(train.get_column("CloseTime").dt.epoch("s")[-1]),
    }
    return train, meta


def load_exp061_bench() -> dict[tuple[str, str], dict[str, Any]]:
    """Load EXP-061's per-cell M0 (native) + H0 (hybrid) arms for the P12 anchors.

    Returns, per (instrument, domain), ``{"M0": {m, median}, "H0": {m, median}}``.
    The native ``M-BENCH`` arm reconciles to ``M0`` and the hybrid ``H-BENCH`` to ``H0``.
    """
    if not EXP061_PARQUET.exists():
        return {}
    df = pl.read_parquet(EXP061_PARQUET)
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for row in df.filter(pl.col("label").is_in(["M0", "H0"])).iter_rows(named=True):
        if not row.get("member"):
            continue
        cell = out.setdefault((row["instrument"], row["domain"]), {})
        cell[row["label"]] = {"m": row.get("m"), "median": row.get("median")}
    return out


def load_exp062_tail() -> dict[tuple[str, str], dict[str, Any]]:
    """Load EXP-062's per-object MAE tail decomposition for the disclosed V-NONE cross-check.

    Returns, per (instrument, domain), the full EXP-062 tail row (per-object ``ama_nat_*``
    / ``ama_hyb_*`` MAE median + worst-5% tail-share where available; column names tolerated
    flexibly). A missing file/column yields an empty/partial map -- the cross-check is
    disclosed, not a hard gate.
    """
    if not EXP062_TAIL_CSV.exists():
        return {}
    df = pl.read_csv(EXP062_TAIL_CSV)
    cols = set(df.columns)
    if not ({"instrument", "domain"} <= cols):
        return {}
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for row in df.iter_rows(named=True):
        out[(row["instrument"], row["domain"])] = dict(row)
    return out


# --------------------------------------------------------------------------- #
# Pure computation -- domain / substrate / harami alignment
# --------------------------------------------------------------------------- #
def build_domain(
    train_1m: pl.DataFrame, period_minutes: int, min_coverage: float | None,
    train_end_epoch: int,
) -> pl.DataFrame:
    """Aggregate one domain on the TRAIN slice and fence to the TRAIN edge."""
    bars = aggregate_ohlc(train_1m, period_minutes=period_minutes, min_coverage=min_coverage)
    return bars.filter(pl.col("CloseTime").dt.epoch("s") <= train_end_epoch)


def real_ohlc(bars: pl.DataFrame) -> dict[str, np.ndarray]:
    """Real-bar OHLC + CloseTime epochs (real prices only)."""
    return {
        "open": bars.get_column("Open").to_numpy().astype(np.float64),
        "high": bars.get_column("High").to_numpy().astype(np.float64),
        "low": bars.get_column("Low").to_numpy().astype(np.float64),
        "close": bars.get_column("Close").to_numpy().astype(np.float64),
        "epoch": bars.get_column("CloseTime").dt.epoch("s").to_numpy().astype(np.int64),
    }


def harami_entry_indices(bars: pl.DataFrame, bar_epoch: np.ndarray) -> np.ndarray:
    """Detect HA haramis and map each to its real domain-bar index (exact match)."""
    ha = generate_heiken_ashi(bars)
    haramis = detect_ha_harami(ha)
    if haramis.height == 0:
        return np.empty(0, dtype=np.int64)
    harami_epoch = haramis.get_column("HA0Time").dt.epoch("s").to_numpy().astype(np.int64)
    return _map_to_grid(bar_epoch, harami_epoch, "harami HA0Time")


def _map_to_grid(bar_epoch: np.ndarray, times: np.ndarray, label: str) -> np.ndarray:
    """Exact CloseTime->bar-index map (raises on any mismatch)."""
    idx = np.searchsorted(bar_epoch, times)
    if np.any(idx >= bar_epoch.shape[0]) or np.any(bar_epoch[np.minimum(
            idx, bar_epoch.shape[0] - 1)] != times):
        raise ValueError(f"{label} not found on the domain-bar grid")
    return idx.astype(np.int64)


def _epochs_to_idx(bar_epoch: np.ndarray, epochs: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Map confirmed-segment-start epochs to bar indices (-1 where invalid/unmatched).

    Used for the ``/ADV-EXTREME`` faded-move extreme start index. Only ``valid``
    entries are mapped; every confirmed MA crossover epoch is a real bar close, so a
    valid entry's start epoch matches the grid exactly. Causal: the start crossover
    is confirmed at/before entry (P7 Q5).
    """
    out = np.full(epochs.shape[0], -1, dtype=np.int64)
    if not valid.any():
        return out
    sel = valid & (epochs >= 0)
    if not sel.any():
        return out
    e = epochs[sel]
    idx = np.searchsorted(bar_epoch, e)
    ok = (idx < bar_epoch.shape[0]) & (bar_epoch[np.minimum(idx, bar_epoch.shape[0] - 1)] == e)
    mapped = np.full(e.shape[0], -1, dtype=np.int64)
    mapped[ok] = idx[ok]
    out[sel] = mapped
    return out


def move_arrays(moves: pl.DataFrame, bar_epoch: np.ndarray) -> dict[str, np.ndarray]:
    """Confirmed ZigZag-move arrays + confirm bar indices (for the hybrid mask)."""
    if moves.height == 0:
        ei, ef = np.empty(0, dtype=np.int64), np.empty(0, dtype=np.float64)
        return {"confirm_epoch": ei, "end_epoch": ei, "end_price": ef, "start_price": ef,
                "direction": ei, "confirm_idx": ei, "magnitude": ef}
    confirm_epoch = moves.get_column("ConfirmTime").dt.epoch("s").to_numpy().astype(np.int64)
    start = moves.get_column("StartPrice").to_numpy().astype(np.float64)
    end = moves.get_column("EndPrice").to_numpy().astype(np.float64)
    return {
        "confirm_epoch": confirm_epoch,
        "end_epoch": moves.get_column("EndTime").dt.epoch("s").to_numpy().astype(np.int64),
        "end_price": end, "start_price": start,
        "direction": moves.get_column("Direction").to_numpy().astype(np.int64),
        "confirm_idx": _map_to_grid(bar_epoch, confirm_epoch, "ConfirmTime"),
        "magnitude": np.abs(end - start),
    }


def ma_segment_moves(ohlc: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """MA(20,50)-crossover segmentation as a ZigZag-shaped confirmed-move set.

    Identical to EXP-060/060B/061's ``ma_segment_moves``: segments bounded by
    consecutive crossovers on the **real close**; the partial pre-first-crossover
    stretch is excluded by construction. MA(20,50) is the registered Phase 015
    substrate (P1), fixed and not swept.
    """
    close, epoch = ohlc["close"], ohlc["epoch"]
    n = close.shape[0]
    empty = {k: np.empty(0, dtype=t) for k, t in (
        ("confirm_epoch", np.int64), ("end_epoch", np.int64), ("end_price", np.float64),
        ("start_price", np.float64), ("direction", np.int64), ("confirm_idx", np.int64),
        ("start_idx", np.int64), ("end_idx", np.int64), ("magnitude", np.float64))}
    if n <= MA_SLOW:
        return empty
    diff = _sma(close, MA_FAST) - _sma(close, MA_SLOW)
    sign = np.sign(diff)
    defined = np.isfinite(diff) & (sign != 0.0)
    cross = np.zeros(n, dtype=bool)
    cross[1:] = defined[1:] & defined[:-1] & (sign[1:] != sign[:-1])
    cidx = np.flatnonzero(cross)
    if cidx.shape[0] < 2:
        return empty
    s, e = cidx[:-1], cidx[1:]
    return {
        "confirm_epoch": epoch[e], "end_epoch": epoch[e], "end_price": close[e],
        "start_price": close[s], "direction": sign[s].astype(np.int64),
        "confirm_idx": e.astype(np.int64), "start_idx": s.astype(np.int64),
        "end_idx": e.astype(np.int64), "magnitude": np.abs(close[e] - close[s]),
    }


def _sma(values: np.ndarray, window: int) -> np.ndarray:
    """Trailing simple moving average; ``NaN`` until ``window`` values exist."""
    out = np.full(values.shape[0], np.nan, dtype=np.float64)
    if values.shape[0] < window:
        return out
    cs = np.cumsum(np.insert(values, 0, 0.0))
    out[window - 1:] = (cs[window:] - cs[:-window]) / window
    return out


def _subset_state(state: InProgressState, idx: np.ndarray) -> InProgressState:
    """Index every per-entry field of an InProgressState by ``idx``."""
    return InProgressState(
        valid=state.valid[idx], k=state.k[idx], rd=state.rd[idx],
        start_price=state.start_price[idx], start_epoch=state.start_epoch[idx],
        m_sofar=state.m_sofar[idx])


def _rng(cell_index: int, purpose: int) -> np.random.Generator:
    """Deterministic, independent per-cell-per-purpose RNG (reproducible)."""
    return np.random.default_rng([BASE_SEED, cell_index, purpose])


# --------------------------------------------------------------------------- #
# Pure computation -- mean / trimmed-mean moving-block bootstrap (block == median)
# --------------------------------------------------------------------------- #
def bootstrap_stat_distribution(
    values: np.ndarray, rng: np.random.Generator, statistic: str,
    n_boot: int = N_BOOT, batch: int = BOOT_BATCH,
) -> tuple[np.ndarray, int]:
    """Moving-block bootstrap distribution of the mean or 10% trimmed mean.

    Block construction is byte-identical to
    :func:`xen.expectancy.bootstrap_median_distribution` (``b = max(1,
    round(m**(1/3)))``; ``ceil(m/b)`` contiguous blocks per resample, truncated to
    ``m``); only the statistic changes. ``statistic`` is ``"mean"`` (raw mean) or
    ``"trim"`` (10% symmetric trimmed mean). Mean/trimmed-mean are tail-sensitive, so
    their CIs are wider than the median's -- that width quantifies the skew (the P4
    object under study), not a defect. Dedicated RNG so the median path is untouched.
    """
    m = int(values.shape[0])
    if m == 0:
        return np.empty(0, dtype=np.float64), 1
    b = max(1, int(round(m ** (1.0 / 3.0))))
    n_blocks = int(np.ceil(m / b))
    max_start = max(0, m - b)
    offsets = np.arange(b, dtype=np.int64)
    out = np.empty(n_boot, dtype=np.float64)
    done = 0
    while done < n_boot:
        k = min(batch, n_boot - done)
        starts = rng.integers(0, max_start + 1, size=(k, n_blocks))
        idx = (starts[:, :, None] + offsets[None, None, :]).reshape(k, n_blocks * b)[:, :m]
        sample = values[idx]
        if statistic == "mean":
            out[done:done + k] = np.mean(sample, axis=1)
        else:                                         # 10% symmetric trimmed mean
            out[done:done + k] = _trimmed_mean_rows(sample)
        done += k
    return out, b


def _trimmed_mean_rows(sample: np.ndarray) -> np.ndarray:
    """Row-wise 10% symmetric trimmed mean of a (k, m) resample matrix (vectorised)."""
    m = sample.shape[1]
    cut = int(np.floor(TRIM_FRAC * m))
    if cut == 0:
        return np.mean(sample, axis=1)
    ordered = np.sort(sample, axis=1)[:, cut:m - cut]
    return np.mean(ordered, axis=1)


def _trimmed_mean(values: np.ndarray) -> float | None:
    """10% symmetric trimmed-mean point estimate (None on empty)."""
    m = int(values.shape[0])
    if m == 0:
        return None
    cut = int(np.floor(TRIM_FRAC * m))
    ordered = np.sort(values)
    core = ordered[cut:m - cut] if cut > 0 else ordered
    return float(np.mean(core)) if core.shape[0] > 0 else float(np.mean(ordered))


def _tail_share_worst5(values: np.ndarray) -> float | None:
    """Fraction of total negative return contributed by the worst 5% of events.

    Worst 5% = the ``ceil(0.05*m)`` most-negative returns. Returns the ratio of their
    summed (negative) contribution to the total negative contribution -- a finite value
    in ``[0, 1]``. Zero when the cell has no negative return mass (never NaN/inf).
    """
    m = int(values.shape[0])
    if m == 0:
        return None
    total_neg = float(values[values < 0.0].sum())
    if total_neg >= 0.0:                              # no negative mass -> finite zero
        return 0.0
    k = max(1, int(np.ceil(TAIL_FRAC * m)))
    worst = np.sort(values)[:k]                       # k most-negative
    worst_neg = float(worst[worst < 0.0].sum())
    return float(worst_neg / total_neg)


# --------------------------------------------------------------------------- #
# Pure computation -- adverse-level build (dispatch over the variant set)
# --------------------------------------------------------------------------- #
def build_adverse(
    variant: str, ohlc: dict[str, np.ndarray], entry_idx: np.ndarray,
    entry_close: np.ndarray, rd: np.ndarray, m_sofar: np.ndarray, fav_dist: np.ndarray,
    atr_entry: np.ndarray, ma_start_idx: np.ndarray, valid: np.ndarray,
) -> dict[str, np.ndarray]:
    """Build (fav, adv, adv_dist, ok) for one adverse variant over a set of entries.

    Favourable target held at benchmark (``fav = C + rd*0.50*M_sofar``). Only the
    adverse leg varies. ``ok`` is the per-event built-barrier validity mask (before the
    buildable/conditioning intersection the caller applies). For the extreme variants
    the faded-move running extreme is the in-progress **MA segment** extreme over real
    bars ``[ma_start_idx+1 .. entry_idx]`` (P7 Q5), via
    :func:`xen.adverse_targets.faded_move_extreme`. Real prices only. The MA geometry
    (rd / m_sofar / ma_start_idx) is shared by both objects; only the entry population
    differs.
    """
    if variant == "V-NONE":
        res = adverse_none_sentinel(entry_close, rd, fav_dist)
        return {"fav": res["fav"], "adv": res["adv"], "adv_dist": res["adv_dist"],
                "ok": res["ok"]}
    if variant in ("V-RR1", "V-RAW"):
        faded, ext_avail = faded_move_extreme(
            ohlc["low"], ohlc["high"], ma_start_idx, entry_idx, rd, valid)
        builder = adverse_extreme_rr1 if variant == "V-RR1" else adverse_extreme_raw
        res = builder(entry_close, rd, fav_dist, faded, atr_entry, ext_avail)
        return {"fav": res["fav"], "adv": res["adv"], "adv_dist": res["adv_dist"],
                "ok": res["ok"]}
    raise ValueError(f"build_adverse received non-dispatched variant {variant!r}")


# --------------------------------------------------------------------------- #
# Pure computation -- resolve one arm on one population -> ArmResult
# --------------------------------------------------------------------------- #
def resolve_arm(
    ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, entry_close: np.ndarray,
    rd: np.ndarray, atr_entry: np.ndarray, fav: np.ndarray, adv: np.ndarray,
    n_event: np.ndarray, population: np.ndarray, rng: np.random.Generator,
    mean_rng: np.random.Generator, trim_rng: np.random.Generator, draw_count: int = 0,
) -> ArmResult:
    """Resolve the single favourable leg + one adverse level over ``population``.

    Reuses :func:`resolve_path_ordered` (the exact EXP-053 path: single favourable
    level at ``0.50*M_sofar``, the supplied adverse level, the benchmark adaptive cap
    floor=6). The median path (``rng``) reproduces EXP-061 M0/H0 for V-BENCH; the mean
    CI (``mean_rng``) and the 10% trimmed-mean CI (``trim_rng``) use dedicated streams.
    """
    n_bars = ohlc["close"].shape[0]
    classes, exit_px = resolve_path_ordered(
        ohlc["open"], ohlc["high"], ohlc["low"], ohlc["close"], entry_idx,
        fav, adv, rd, n_event, population, n_bars)
    r_all = realised_returns(classes, exit_px, entry_close, rd, atr_entry)
    qual = population & qualifying_mask(classes, exit_px, atr_entry)
    r_firsthit = _firsthit(classes, qual, CLASS_FAV, CLASS_ADV)
    censored = int((population & (classes == CLASS_DATA_CENSORED)).sum())
    adv_count = int((qual & (classes == CLASS_ADV)).sum())
    order = np.argsort(entry_idx[qual], kind="stable")
    r_e = r_all[qual][order]
    exit_w = exit_reason_weights(classes[:, None], np.asarray(BENCH.weights), qual)
    return _summarize_arm(r_e, r_all, qual, exit_w, r_firsthit, censored, adv_count,
                          int(population.sum()), rng, mean_rng, trim_rng, draw_count)


def _firsthit(
    classes: np.ndarray, qual: np.ndarray, fav_code: int, other_code: int,
) -> float | None:
    """First-hit ratio FAV/(FAV+other) over qualifying events (disclosed)."""
    fav_n = int((qual & (classes == fav_code)).sum())
    other_n = int((qual & (classes == other_code)).sum())
    resolved = fav_n + other_n
    return (fav_n / resolved) if resolved > 0 else None


def _summarize_arm(
    r_e: np.ndarray, r_full: np.ndarray, qual: np.ndarray, exit_w: dict[str, float],
    r_firsthit: float | None, censored: int, adv_count: int, population: int,
    rng: np.random.Generator, mean_rng: np.random.Generator,
    trim_rng: np.random.Generator, draw_count: int = 0,
) -> ArmResult:
    """Assemble an ``ArmResult``; (if powered) bootstrap the median + mean + trim CIs."""
    m = int(r_e.shape[0])
    dist = np.empty(0, dtype=np.float64)
    mean_dist = np.empty(0, dtype=np.float64)
    block_len = max(1, int(round(max(m, 1) ** (1.0 / 3.0))))
    median = mean = trimmed = tail = None
    ci_low = ci_lo = ci_hi = None
    mean_low = mean_lo = mean_hi = None
    trim_low = trim_lo = trim_hi = None
    if m > 0:
        median = float(np.median(r_e))
        mean = float(np.mean(r_e))
        trimmed = _trimmed_mean(r_e)
        tail = _tail_share_worst5(r_e)
    if m >= POWER_FLOOR:
        dist, block_len = bootstrap_median_distribution(r_e, rng, n_boot=N_BOOT, batch=BOOT_BATCH)
        ci_low, ci_lo, ci_hi = median_ci(dist)
        mean_dist, _ = bootstrap_stat_distribution(r_e, mean_rng, "mean",
                                                    n_boot=N_BOOT, batch=BOOT_BATCH)
        mean_low, mean_lo, mean_hi = median_ci(mean_dist)        # generic percentile CI
        trim_dist, _ = bootstrap_stat_distribution(r_e, trim_rng, "trim",
                                                    n_boot=N_BOOT, batch=BOOT_BATCH)
        trim_low, trim_lo, trim_hi = median_ci(trim_dist)
    return ArmResult(
        m=m, median=median, mean=mean, trimmed_mean=trimmed, tail_share_worst5=tail,
        ci_low_1s=ci_low, ci_lo_2s=ci_lo, ci_hi_2s=ci_hi,
        mean_ci_low_1s=mean_low, mean_ci_lo_2s=mean_lo, mean_ci_hi_2s=mean_hi,
        trim_ci_low_1s=trim_low, trim_ci_lo_2s=trim_lo, trim_ci_hi_2s=trim_hi,
        r_firsthit=r_firsthit, win_rate=(float((r_e > 0).mean()) if m > 0 else None),
        data_censored=censored, exit_weights=exit_w, population=population,
        adv_count=adv_count, block_len=block_len, r_e=r_e, r_full=r_full, qual=qual,
        dist=dist, mean_dist=mean_dist, draw_count=draw_count)


def _empty_arm() -> ArmResult:
    return ArmResult(0, None, None, None, None, None, None, None, None, None, None,
                     None, None, None, None, None, 0,
                     {label: 0.0 for label in PX_CLASS_LABELS.values()}, 0, 0, 1,
                     np.empty(0), np.empty(0), np.empty(0, dtype=bool),
                     np.empty(0), np.empty(0), 0)


# --------------------------------------------------------------------------- #
# Pure computation -- signal arm + matched-random-on-MA null, per object/variant
# --------------------------------------------------------------------------- #
def signal_arm(
    obj: str, variant: str, ohlc: dict[str, np.ndarray], ma: dict[str, Any],
    cond_mask: np.ndarray, ma_start_idx: np.ndarray, entry_idx: np.ndarray, cell_index: int,
) -> tuple[ArmResult, np.ndarray]:
    """Resolve one (object, variant) MA signal arm on the object's conditioned population.

    ``cond_mask`` is the object's ``/STRONG-STAT`` retained mask over the shared harami
    entries (native = ma-segment mask; hybrid = ZigZag mask). The MA geometry
    (fav/adv/cap/ma_start_idx) is shared. Returns the ``ArmResult`` and the per-event
    ``adv_dist`` (used by the V-RAW <= V-RR1 invariant). The (object, V-BENCH) arm reuses
    the precomputed benchmark fav/adv + its object's M0/H0 RNG purposes so it reproduces
    EXP-061 M0 (native) / H0 (hybrid) exactly.
    """
    pb = VARIANT_PB[obj][variant]
    state = ma["state"]
    if variant == "V-BENCH":
        fav, adv = ma["fav"], ma["adv"]
        adv_dist = ma["fav_dist"]                     # 1:1 -> adv_dist == fav_dist
        ok = ma["fav_dist"] > 0.0
    else:
        bld = build_adverse(variant, ohlc, entry_idx, ma["entry_close"], state.rd,
                            state.m_sofar, ma["fav_dist"], ma["atr_entry"], ma_start_idx,
                            state.valid)
        fav, adv, adv_dist, ok = bld["fav"], bld["adv"], bld["adv_dist"], bld["ok"]
    pop = ma["buildable"] & cond_mask & ok
    arm = resolve_arm(ohlc, entry_idx, ma["entry_close"], state.rd, ma["atr_entry"],
                      fav, adv, ma["bench_n"], pop, _rng(cell_index, pb["med"]),
                      _rng(cell_index, pb["mean"]), _rng(cell_index, pb["trim"]))
    return arm, adv_dist


def matched_random_arm(
    obj: str, variant: str, ohlc: dict[str, np.ndarray], state_all: InProgressState,
    seg: dict[str, np.ndarray], warmup_all: np.ndarray, atr_all: np.ndarray,
    signal_idx: np.ndarray, draw_count: int, cell_index: int,
) -> ArmResult:
    """Matched-count random-in-MA-regime control through one variant's pipeline (P5).

    The eligible pool is every in-MA-regime bar (valid live state, positive ``m_sofar``,
    finite positive ATR, not in warmup) **excluding** the object's own conditioned-harami
    entries; ``draw_count`` matched entries are drawn without replacement and resolved
    through the **identical** per-variant adverse + favourable + cap + P15 pipeline. Fresh
    dedicated RNG purposes per (object, variant) so the two objects' nulls are disjoint and
    no existing stream shifts.
    """
    pb = VARIANT_PB[obj][variant]
    eligible = (state_all.valid & (state_all.m_sofar > 0.0) & np.isfinite(atr_all)
                & (atr_all > 0.0) & (~warmup_all))
    is_signal = np.zeros(ohlc["close"].shape[0], dtype=bool)
    is_signal[signal_idx] = True
    pool = np.flatnonzero(eligible & ~is_signal)
    if draw_count <= 0 or pool.shape[0] == 0:
        return _empty_arm()
    k = min(draw_count, pool.shape[0])
    drawn = np.sort(_rng(cell_index, pb["rm_draw"]).choice(pool, size=k, replace=False))
    sub = _subset_state(state_all, drawn)
    bar = benchmark_barriers(ohlc["close"][drawn], sub.rd, sub.m_sofar)
    bench_n, bench_warmup = adaptive_time_caps_by_epoch(
        ohlc["epoch"][drawn], seg["confirm_epoch"], seg["confirm_idx"])
    base_pop = (sub.valid & (sub.m_sofar > 0.0) & np.isfinite(atr_all[drawn])
                & (atr_all[drawn] > 0.0) & ~bench_warmup)
    if variant == "V-BENCH":
        fav, adv, ok = bar["fav"], bar["adv"], bar["fav_dist"] > 0.0
    else:
        ma_start_idx = _epochs_to_idx(ohlc["epoch"], sub.start_epoch, sub.valid)
        bld = build_adverse(variant, ohlc, drawn, ohlc["close"][drawn], sub.rd,
                            sub.m_sofar, bar["fav_dist"], atr_all[drawn], ma_start_idx,
                            sub.valid)
        fav, adv, ok = bld["fav"], bld["adv"], bld["ok"]
    pop = base_pop & ok
    return resolve_arm(ohlc, drawn, ohlc["close"][drawn], sub.rd, atr_all[drawn], fav, adv,
                       bench_n, pop, _rng(cell_index, pb["rm_med"]),
                       _rng(cell_index, pb["rm_mean"]), _rng(cell_index, pb["rm_trim"]),
                       draw_count=draw_count)


def contrast(variant: ArmResult, null: ArmResult) -> dict[str, Any]:
    """Independent bootstrap contrast ``variant - null`` (median binding, mean disclosed).

    The signal arm (indexed over haramis) and its matched-random control (indexed over
    disjoint random in-regime draws) are **independent** -- no common per-event subset to
    pair (EXP-060B I2) -- so :func:`xen.expectancy.contrast_ci` on the stored bootstrap
    distributions is the correct test, mirroring EXP-060/060B champion-vs-random.
    """
    med_low, med_lo, med_hi = contrast_ci(variant.dist, null.dist)
    mean_low, mean_lo, mean_hi = contrast_ci(variant.mean_dist, null.mean_dist)
    return {"median_low_1s": med_low, "median_lo_2s": med_lo, "median_hi_2s": med_hi,
            "mean_low_1s": mean_low, "mean_lo_2s": mean_lo, "mean_hi_2s": mean_hi}


def recovery_contrast(bounded: ArmResult, none: ArmResult) -> dict[str, Any]:
    """Bounded-downside recovery ``mean(bounded) - mean(/ADV-NONE)`` (the 'can we fix it' read).

    Independent contrast on the stored per-variant **mean** bootstrap distributions of the
    same object: a positive lower bound means bounding the downside lifts the average trade
    (removable tail / mean-recoverable); a null/negative one is consistent with structural
    negativity.
    """
    low, lo, hi = contrast_ci(bounded.mean_dist, none.mean_dist)
    return {"mean_low_1s": low, "mean_lo_2s": lo, "mean_hi_2s": hi}


def paired_vs_bench(variant: ArmResult, bench: ArmResult, cell_index: int,
                    purpose: int) -> dict[str, Any]:
    """Variant - benchmark paired-median contrast on the common qualifying subset (one object).

    Both arms resolve on the same harami entry order, so the common subset is
    ``qual_variant & qual_bench`` and the per-event returns pair element-wise. Empty
    intersection -> NaN bounds (disclosed, never defaulted).
    """
    if variant.qual.shape[0] == 0 or bench.qual.shape[0] == 0:
        return {"paired_low_1s": float("nan"), "paired_lo_2s": float("nan"),
                "paired_hi_2s": float("nan"), "n_common": 0}
    common = variant.qual & bench.qual
    n_common = int(common.sum())
    if n_common < POWER_FLOOR:
        return {"paired_low_1s": float("nan"), "paired_lo_2s": float("nan"),
                "paired_hi_2s": float("nan"), "n_common": n_common}
    low, lo, hi, _ = paired_median_contrast_ci(
        variant.r_full[common], bench.r_full[common], _rng(cell_index, purpose))
    return {"paired_low_1s": low, "paired_lo_2s": lo, "paired_hi_2s": hi,
            "n_common": n_common}


# --------------------------------------------------------------------------- #
# Per-cell signal contexts (MA geometry shared; ZigZag mask for the hybrid object)
# --------------------------------------------------------------------------- #
def _ma_context(
    ohlc: dict[str, np.ndarray], atr: np.ndarray, entry_idx: np.ndarray,
    entry_epoch: np.ndarray,
) -> dict[str, Any]:
    """MA(20,50) geometry context at the harami entries + the RM-null arrays.

    Shared by both objects: ``rd`` / ``M_sofar`` / fav / cap / buildable come from the MA
    in-progress state. The native conditioning mask is ``stat["retained_p75"]``.
    """
    seg = ma_segment_moves(ohlc)
    if seg["confirm_epoch"].shape[0] == 0:
        return {"empty": True, "seg": seg}
    entry_close = ohlc["close"][entry_idx]
    atr_entry = atr[entry_idx]
    state = live_in_progress_state(entry_epoch, entry_close, seg["confirm_epoch"],
                                   seg["end_price"], seg["end_epoch"], seg["direction"])
    bench_n, bench_warmup = adaptive_time_caps_by_epoch(
        entry_epoch, seg["confirm_epoch"], seg["confirm_idx"])
    buildable = (state.valid & (state.m_sofar > 0.0) & np.isfinite(atr_entry)
                 & (atr_entry > 0.0) & ~bench_warmup)
    stat = live_strong_stat(state.k, state.m_sofar, seg["magnitude"])
    bar = benchmark_barriers(entry_close, state.rd, state.m_sofar)
    return {"empty": False, "seg": seg, "entry_close": entry_close, "state": state,
            "atr": atr, "atr_entry": atr_entry, "bench_n": bench_n, "buildable": buildable,
            "stat": stat, "fav_dist": bar["fav_dist"], "fav": bar["fav"], "adv": bar["adv"]}


def _zz_context(
    bars: pl.DataFrame, ohlc: dict[str, np.ndarray], atr: np.ndarray,
    entry_idx: np.ndarray, entry_epoch: np.ndarray,
) -> dict[str, Any]:
    """ZigZag conditioned-signal context: the **hybrid** object's /STRONG-STAT mask.

    Mirrors EXP-061's ``_zz_context``: the ZigZag in-progress state at each harami entry,
    its ``live_strong_stat`` p75 retained mask (== EXP-061 H0's conditioning mask), and the
    ZigZag reference-move end epochs for the hybrid causality gate.
    """
    moves = generate_zigzag(bars, atr_period=ATR_PERIOD, atr_mult=ATR_MULT)
    mv = move_arrays(moves, ohlc["epoch"])
    if mv["confirm_epoch"].shape[0] == 0:
        n = int(entry_idx.shape[0])
        return {"empty": True, "retained_p75": np.zeros(n, dtype=bool),
                "state": None, "end_epoch": np.empty(0, dtype=np.int64)}
    entry_close = ohlc["close"][entry_idx]
    state = live_in_progress_state(entry_epoch, entry_close, mv["confirm_epoch"],
                                   mv["end_price"], mv["end_epoch"], mv["direction"])
    stat = live_strong_stat(state.k, state.m_sofar, mv["magnitude"])
    return {"empty": False, "retained_p75": stat["retained_p75"], "state": state,
            "end_epoch": mv["end_epoch"]}


# --------------------------------------------------------------------------- #
# Per-cell orchestration
# --------------------------------------------------------------------------- #
def compute_cell(
    train_1m: pl.DataFrame, domain: str, train_end_epoch: int, cell_index: int,
) -> dict[str, Any]:
    """Full pipeline for one cell. Pure given identical inputs/seeds."""
    period_minutes, min_coverage = DOMAINS[domain]
    bars = build_domain(train_1m, period_minutes, min_coverage, train_end_epoch)
    ohlc = real_ohlc(bars)
    atr = wilder_atr(ohlc["high"], ohlc["low"], ohlc["close"], ATR_PERIOD)
    entry_idx = harami_entry_indices(bars, ohlc["epoch"])
    base = {"domain": domain, "n_bars": int(bars.height), "n_harami": int(entry_idx.shape[0])}
    entry_epoch = ohlc["epoch"][entry_idx]
    ma = _ma_context(ohlc, atr, entry_idx, entry_epoch) if entry_idx.shape[0] \
        else {"empty": True}
    if entry_idx.shape[0] == 0 or ma.get("empty"):
        return {**base, "empty": True}

    zz = _zz_context(bars, ohlc, atr, entry_idx, entry_epoch)
    # Object conditioning masks over the SAME harami entry array (shared MA geometry).
    cond_masks = {"nat": ma["stat"]["retained_p75"], "hyb": zz["retained_p75"]}
    # In-progress (faded) MA-segment start bar index for the /ADV-EXTREME running extreme.
    ma_start_idx = _epochs_to_idx(ohlc["epoch"], ma["state"].start_epoch, ma["state"].valid)
    arms, adv_dists = _resolve_objects(ohlc, ma, cond_masks, ma_start_idx, entry_idx, cell_index)
    n_conditioned = {o: int((ma["buildable"] & cond_masks[o]).sum()) for o in OBJECTS}
    return {
        **base, "empty": False, "arms": arms, "n_conditioned": n_conditioned,
        "causality_ok": _causality_ok(ohlc, entry_idx, entry_epoch, ma, zz),
        "invariants": {o: _cell_invariants(arms[o], adv_dists[o]) for o in OBJECTS},
    }


def _resolve_objects(
    ohlc: dict[str, np.ndarray], ma: dict[str, Any], cond_masks: dict[str, np.ndarray],
    ma_start_idx: np.ndarray, entry_idx: np.ndarray, cell_index: int,
) -> tuple[dict[str, Any], dict[str, dict[str, np.ndarray]]]:
    """Resolve the 4 adverse variants (signal + matched-random) + contrasts, per object."""
    seg = ma["seg"]
    state_all = live_in_progress_state(ohlc["epoch"], ohlc["close"], seg["confirm_epoch"],
                                       seg["end_price"], seg["end_epoch"], seg["direction"])
    _, warmup_all = adaptive_time_caps_by_epoch(
        ohlc["epoch"], seg["confirm_epoch"], seg["confirm_idx"])
    arms: dict[str, Any] = {}
    adv_dists: dict[str, dict[str, np.ndarray]] = {}
    for obj in OBJECTS:
        cond = cond_masks[obj]
        signal_idx = entry_idx[cond]                  # object's own signal entries (excluded from null)
        signals: dict[str, ArmResult] = {}
        nulls: dict[str, ArmResult] = {}
        obj_adv: dict[str, np.ndarray] = {}
        for variant in VARIANTS:
            arm, adv_dist = signal_arm(obj, variant, ohlc, ma, cond, ma_start_idx,
                                       entry_idx, cell_index)
            signals[variant] = arm
            obj_adv[variant] = adv_dist
            nulls[variant] = matched_random_arm(obj, variant, ohlc, state_all, seg, warmup_all,
                                                 ma["atr"], signal_idx, arm.m, cell_index)
        var_rm = {v: contrast(signals[v], nulls[v]) for v in VARIANTS}
        recovery = {v: recovery_contrast(signals[v], signals["V-NONE"]) for v in BOUNDED}
        paired = {v: paired_vs_bench(signals[v], signals["V-BENCH"], cell_index,
                                     VARIANT_PB[obj][v]["paired"]) for v in VARIANTS
                  if v != "V-BENCH"}
        arms[obj] = {"signals": signals, "nulls": nulls, "var_rm": var_rm,
                     "recovery": recovery, "paired": paired}
        adv_dists[obj] = obj_adv
    return arms, adv_dists


# --------------------------------------------------------------------------- #
# Per-cell causality / invariant gate
# --------------------------------------------------------------------------- #
def _causality_ok(
    ohlc: dict[str, np.ndarray], entry_idx: np.ndarray, entry_epoch: np.ndarray,
    ma: dict[str, Any], zz: dict[str, Any],
) -> bool:
    """Strict grid + causal MA reference segments + causal ZigZag reference (hybrid mask)."""
    epoch = ohlc["epoch"]
    if epoch.shape[0] >= 2 and not bool(np.all(np.diff(epoch) > 0)):
        return False                                   # duplicate/disordered CloseTime
    state = ma["state"]
    valid = state.valid & (state.k >= 0)
    if valid.any():
        kk = state.k[valid]
        if not bool(np.all(ma["seg"]["end_epoch"][kk] <= entry_epoch[valid])):
            return False                               # MA reference ends at/before entry
        if not bool(np.all(epoch[entry_idx[valid]] <= entry_epoch[valid])):
            return False                               # entry bar is itself (<= t_i)
        # faded-extreme span start (in-progress MA segment start) is at/before entry
        if not bool(np.all(state.start_epoch[valid] <= entry_epoch[valid])):
            return False
    # Hybrid conditioning references confirmed ZigZag moves -- they must end at/before entry.
    if not zz.get("empty") and zz["state"] is not None:
        zs = zz["state"]
        zvalid = zs.valid & (zs.k >= 0)
        if zvalid.any():
            zk = zs.k[zvalid]
            if not bool(np.all(zz["end_epoch"][zk] <= entry_epoch[zvalid])):
                return False                           # ZigZag reference ends at/before entry
    return True


def _cell_invariants(arms_obj: dict[str, Any], adv_dists: dict[str, np.ndarray]) -> dict[str, bool]:
    """Predeclared structural invariants for one object (scope §Success/Failure (ii)-(vi))."""
    signals, nulls = arms_obj["signals"], arms_obj["nulls"]
    # (ii) V-RAW adv_dist <= V-RR1 adv_dist event-wise where both are finite (rr1 widens).
    raw, rr1 = adv_dists["V-RAW"], adv_dists["V-RR1"]
    both = np.isfinite(raw) & np.isfinite(rr1)
    raw_le_rr1 = bool(np.all(raw[both] <= rr1[both] + 1e-12)) if both.any() else True
    # (iii) V-NONE produces 0 ADV outcomes (the unbounded reference has no stop).
    none_zero_adv = (signals["V-NONE"].adv_count == 0 and nulls["V-NONE"].adv_count == 0)
    # exit-reason weights well-formed (finite real-bar P15 resolution) on each arm.
    exit_ok = all(
        (res.m == 0) or abs(sum(res.exit_weights.values()) - 1.0) <= 1e-9
        for res in list(signals.values()) + list(nulls.values()))
    # (v) matched-count holds: each null's draw target == its variant's signal qualifying m.
    matched_ok = all(nulls[v].draw_count == signals[v].m for v in VARIANTS)
    return {"raw_le_rr1": bool(raw_le_rr1), "none_zero_adv": bool(none_zero_adv),
            "exit_ok": bool(exit_ok), "matched_count_ok": bool(matched_ok)}


# --------------------------------------------------------------------------- #
# Per-cell record flattening (one long row per cell x object x variant)
# --------------------------------------------------------------------------- #
def _viable(res: ArmResult) -> bool:
    """Median CI_low(1s) > 0 AND m >= power floor (binding viability)."""
    return bool(res.m >= POWER_FLOOR and res.ci_low_1s is not None
                and np.isfinite(res.ci_low_1s) and res.ci_low_1s > 0.0)


def _mean_viable(res: ArmResult) -> bool:
    """Disclosed P4 flag (raw-mean CI_low > 0); never a viability gate."""
    return bool(res.m >= POWER_FLOOR and res.mean_ci_low_1s is not None
                and np.isfinite(res.mean_ci_low_1s) and res.mean_ci_low_1s > 0.0)


def _beats_rm(c: dict[str, Any]) -> bool:
    return bool(np.isfinite(c["median_low_1s"]) and c["median_low_1s"] > 0.0)


def variant_rows(instrument: str, cell: dict[str, Any]) -> list[dict[str, Any]]:
    """One long row per (cell, object, variant): signal stats, RM null, contrasts, mean §4."""
    rows: list[dict[str, Any]] = []
    for obj in OBJECTS:
        arms = cell["arms"][obj]
        for variant in VARIANTS:
            sig, null = arms["signals"][variant], arms["nulls"][variant]
            c = arms["var_rm"][variant]
            rec = arms["recovery"].get(variant, {})
            pair = arms["paired"].get(variant, {})
            viable = _viable(sig)
            beats = _beats_rm(c)
            gap = (sig.median - sig.mean) if (sig.median is not None
                                              and sig.mean is not None) else None
            low_n_4h = bool(cell["domain"] == "4h" and sig.m < LOW_N_4H)
            rows.append({
                "instrument": instrument, "domain": cell["domain"], "object": obj,
                "variant": variant, "adv_model": ADV_MODEL[variant], "binding": variant in BOUNDED,
                "member": True, "excluded": False, "n_harami": cell["n_harami"],
                "n_conditioned": cell["n_conditioned"][obj], "m": sig.m,
                "population": sig.population, "data_censored": sig.data_censored,
                "adv_count": sig.adv_count, "median": sig.median, "ci_low_1s": sig.ci_low_1s,
                "ci_lo_2s": sig.ci_lo_2s, "ci_hi_2s": sig.ci_hi_2s, "mean": sig.mean,
                "mean_ci_low_1s": sig.mean_ci_low_1s, "mean_ci_lo_2s": sig.mean_ci_lo_2s,
                "mean_ci_hi_2s": sig.mean_ci_hi_2s, "trimmed_mean": sig.trimmed_mean,
                "trim_ci_low_1s": sig.trim_ci_low_1s, "trim_ci_lo_2s": sig.trim_ci_lo_2s,
                "trim_ci_hi_2s": sig.trim_ci_hi_2s, "tail_share_worst5": sig.tail_share_worst5,
                "gap_median_minus_mean": gap, "r_firsthit": sig.r_firsthit,
                "win_rate": sig.win_rate, "rm_m": null.m, "rm_draw_count": null.draw_count,
                "rm_median": null.median, "rm_mean": null.mean,
                "var_rm_median_low_1s": c["median_low_1s"],
                "var_rm_median_hi_2s": c["median_hi_2s"], "var_rm_mean_low_1s": c["mean_low_1s"],
                "recovery_mean_low_1s": rec.get("mean_low_1s"),
                "recovery_mean_hi_2s": rec.get("mean_hi_2s"),
                "paired_vs_bench_low_1s": pair.get("paired_low_1s"),
                "paired_n_common": pair.get("n_common"),
                "median_viable": viable, "mean_viable": _mean_viable(sig),
                "beats_rm": beats, "generalises": bool(viable and beats),
                "recovery_positive": bool(rec and np.isfinite(rec.get("mean_low_1s", np.nan))
                                          and rec.get("mean_low_1s", 0.0) > 0.0),
                "low_n_4h": low_n_4h,
                **{f"ew_{label}": sig.exit_weights[label] for label in PX_CLASS_LABELS.values()},
            })
    return rows


def excluded_rows(instrument: str, domain: str) -> list[dict[str, Any]]:
    """COVERAGE_EXCLUDED / empty-cell placeholder rows (one per object x variant)."""
    rows = []
    for obj in OBJECTS:
        for variant in VARIANTS:
            rows.append({
                "instrument": instrument, "domain": domain, "object": obj, "variant": variant,
                "adv_model": ADV_MODEL[variant], "binding": variant in BOUNDED,
                "member": False, "excluded": True, "n_harami": None, "n_conditioned": None,
                "m": 0, "median": None, "mean": None, "trimmed_mean": None,
                "tail_share_worst5": None, "median_viable": False, "mean_viable": False,
                "beats_rm": False, "generalises": False, "recovery_positive": False,
                "low_n_4h": False,
            })
    return rows


def readiness_row(instrument: str, cell: dict[str, Any]) -> dict[str, Any]:
    """Per-cell readiness/construction row (causality + per-object invariant flags)."""
    inv = cell.get("invariants", {})
    row = {
        "instrument": instrument, "domain": cell["domain"], "n_bars": cell["n_bars"],
        "n_harami": cell["n_harami"],
        "n_conditioned_nat": cell["n_conditioned"].get("nat"),
        "n_conditioned_hyb": cell["n_conditioned"].get("hyb"),
        "causality_ok": cell.get("causality_ok", True),
    }
    all_ok = cell.get("causality_ok", True)
    for obj in OBJECTS:
        io = inv.get(obj, {})
        for k in ("raw_le_rr1", "none_zero_adv", "exit_ok", "matched_count_ok"):
            row[f"{obj}_{k}"] = io.get(k, True)
            all_ok = all_ok and io.get(k, True)
    row["construction_pass"] = bool(all_ok)
    return row


# --------------------------------------------------------------------------- #
# Composition + the P4 closure-rule verdict (P11 with the P6 non-4h rule), per object
# --------------------------------------------------------------------------- #
def _p11(rows: list[dict[str, Any]], flag: str) -> dict[str, Any]:
    """P11 + P6 tally: >=5 cells over >=3 instruments with >=3 cells outside 4h."""
    hit = [r for r in rows if r.get(flag)]
    instruments = sorted({r["instrument"] for r in hit})
    non_4h = [r for r in hit if r["domain"] != "4h"]
    n_cells, n_instr, n_non_4h = len(hit), len(instruments), len(non_4h)
    composes = (n_cells >= P11_MIN_CELLS and n_instr >= P11_MIN_INSTR
                and n_non_4h >= P6_MIN_NON_4H)
    fragile = composes and (n_cells == P11_MIN_CELLS or n_instr == P11_MIN_INSTR
                            or n_non_4h == P6_MIN_NON_4H)
    return {"n_cells": n_cells, "n_instruments": n_instr, "n_non_4h": n_non_4h,
            "composes": composes, "fragile": fragile,
            "cells": [f"{r['instrument']}-{r['domain']}" for r in hit]}


def _object_readout(member: list[dict[str, Any]], defect: dict[str, Any], obj: str) -> dict[str, Any]:
    """One object's per-variant P11/P6 tallies + the §4 closure-rule verdict."""
    obj_rows = [r for r in member if r["object"] == obj]
    per_variant: dict[str, Any] = {}
    for variant in VARIANTS:
        vr = [r for r in obj_rows if r["variant"] == variant]
        powered = _p11([r for r in vr if r["m"] >= POWER_FLOOR
                        and (r.get("rm_m") or 0) >= POWER_FLOOR], "median_viable")
        per_variant[variant] = {
            "median_viable": _p11(vr, "median_viable"), "beats_rm": _p11(vr, "beats_rm"),
            "generalises": _p11(vr, "generalises"), "mean_viable": _p11(vr, "mean_viable"),
            "recovery_positive": _p11(vr, "recovery_positive"), "powered": powered,
        }
    verdict = _verdict(defect, per_variant)
    return {"object": OBJECT_NAME[obj], "verdict": verdict, "per_variant": per_variant}


def composition_readout(rows: list[dict[str, Any]], defect: dict[str, Any]) -> dict[str, Any]:
    """Per-object per-variant P11/P6 tallies + the §4 verdict (never pooled)."""
    member = [r for r in rows if not r.get("excluded")]
    nat = _object_readout(member, defect, "nat")
    hyb = _object_readout(member, defect, "hyb")
    rank = {"EVIDENCE_FOR": 4, "MEDIAN_ONLY": 3, "EVIDENCE_AGAINST": 2,
            "INCONCLUSIVE_POWER_LIMITED": 1, "SUBSTRATE_METHOD_DEFECT": 0}
    phase = nat if rank.get(nat["verdict"], 0) >= rank.get(hyb["verdict"], 0) else hyb
    return {
        "phase_verdict": phase["verdict"], "phase_stronger_object": phase["object"],
        "native": nat, "hybrid": hyb,
        "binding_axis": "bounded-downside: V-BENCH (1:1), V-RR1 (/ADV-EXTREME-rr1) on MA(20,50)",
        "disclosed_reference": ("V-NONE (/ADV-NONE unbounded; skew source); "
                                "V-RAW (/ADV-EXTREME-raw)"),
        "binding_endpoint": "median (P14); mean+10%trim+worst-5% tail-share = P4 diagnostic",
        "rule": _rule_text(), "g015_routing": _routing_text(), "defect": defect,
    }


def _verdict(defect: dict[str, Any], per_variant: dict[str, Any]) -> str:
    """Mechanical §4 verdict per the P4 closure rule, for one object."""
    if defect["is_defect"]:
        return "SUBSTRATE_METHOD_DEFECT"
    powered = any(per_variant[v]["powered"]["composes"] for v in BOUNDED)
    if not powered:
        return "INCONCLUSIVE_POWER_LIMITED"
    generalises = [v for v in BOUNDED if per_variant[v]["generalises"]["composes"]]
    if not generalises:
        return "EVIDENCE_AGAINST"
    # A bounded variant generalises. EVIDENCE_FOR iff the mean is materially lifted:
    # recovery contrast composes positive, or the bounded variant's raw mean clears P11.
    mean_lifted = any(per_variant[v]["recovery_positive"]["composes"]
                      or per_variant[v]["mean_viable"]["composes"] for v in generalises)
    return "EVIDENCE_FOR" if mean_lifted else "MEDIAN_ONLY"


def _rule_text() -> str:
    return ("Per object, never pooled. Binding endpoint = median (P14); mean + 10% trimmed mean + "
            "worst-5% tail-share disclosed (P4, never a blind disqualifier). Per cell (m>=30): "
            "median_viable = variant median CI_low(1s)>0; beats_rm = (variant - own-object "
            "RM-on-MA) independent-contrast median CI_low(1s)>0; generalises = both; "
            "recovery_positive = mean(bounded)-mean(/ADV-NONE) CI_low(1s)>0. EVIDENCE_FOR iff a "
            "bounded-downside variant (V-BENCH/V-RR1) generalises (P11 + P6 non-4h: >=5 cells / >=3 "
            "instruments / >=3 cells outside 4h) AND the mean is materially lifted (recovery_positive "
            "or mean_viable composes). MEDIAN_ONLY iff a bounded variant generalises but the mean is "
            "not lifted (structural negativity). EVIDENCE_AGAINST iff the powered grid composes but "
            "no bounded variant generalises. INCONCLUSIVE iff <P11 quorum powered. "
            "SUBSTRATE_METHOD_DEFECT on any reconciliation / determinism / causality / invariant "
            "failure. Phase reading = the stronger object's verdict.")


def _routing_text() -> str:
    return ("Feeds the single terminal G-015 after the full Phase 015 slate (no closure or "
            "candidate registration here, P9), judged per object. EVIDENCE_FOR (an object): a "
            "bounded MA geometry preserves the median edge AND repairs the EXP-060B skew -> "
            "strongest input to PROCEED/MEAN_RECOVERABLE (tagged with the object). MEDIAN_ONLY: "
            "structural-irrecoverability on the bounded axis -> well-supported "
            "CHARACTERISED_NOT_VIABLE. EVIDENCE_AGAINST: that object's MA edge may require the "
            "/ADV-NONE asymmetry; family stays OPEN, surface (S1-S3, combined champions EXP-067 "
            "hybrid / EXP-068 native) runs regardless (P9).")


# --------------------------------------------------------------------------- #
# Determinism replay + reconciliation (DEFECT guards)
# --------------------------------------------------------------------------- #
def determinism_replay(train_1m: pl.DataFrame, domain: str, train_end_epoch: int,
                       cell_index: int) -> bool:
    """Re-run one cell end-to-end and assert byte-identical binding outputs (both objects)."""
    a = compute_cell(train_1m, domain, train_end_epoch, cell_index)
    b = compute_cell(train_1m, domain, train_end_epoch, cell_index)
    if a.get("empty") or b.get("empty"):
        return a.get("empty") == b.get("empty")
    for obj in OBJECTS:
        for variant in VARIANTS:
            for side in ("signals", "nulls"):
                sa, sb = a["arms"][obj][side][variant], b["arms"][obj][side][variant]
                if not (np.array_equal(sa.r_e, sb.r_e)
                        and (sa.median, sa.ci_low_1s, sa.mean_ci_low_1s, sa.trim_ci_low_1s)
                        == (sb.median, sb.ci_low_1s, sb.mean_ci_low_1s, sb.trim_ci_low_1s)):
                    return False
            ca, cb = a["arms"][obj]["var_rm"][variant], b["arms"][obj]["var_rm"][variant]
            if not (_nan_eq(ca["median_low_1s"], cb["median_low_1s"])
                    and _nan_eq(ca["mean_low_1s"], cb["mean_low_1s"])):
                return False
    return True


def _nan_eq(a: float | None, b: float | None) -> bool:
    """Float equality that treats NaN == NaN as True (for power-limited contrasts)."""
    if a is None or b is None:
        return a is b
    return bool(a == b or (np.isnan(a) and np.isnan(b)))


def exp061_reconciliation(
    instrument: str, cell: dict[str, Any], anchor: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    """P12 reproduction guard: native V-BENCH ↔ EXP-061 M0; hybrid V-BENCH ↔ EXP-061 H0.

    Each object's ``V-BENCH`` arm reproduces its EXP-061 BENCH anchor (per-cell median + m
    to ``RECON_TOL``). A missing/empty anchor or any divergence is SUBSTRATE/METHOD_DEFECT.
    """
    key = (instrument, cell["domain"])
    if not anchor or key not in anchor or cell.get("empty"):
        return {"checked": False, "cell": f"{instrument}-{cell.get('domain')}"}
    src = anchor[key]
    out: dict[str, Any] = {"checked": True, "cell": f"{instrument}-{cell['domain']}"}
    consistent = True
    for obj in OBJECTS:
        label = OBJECT_BENCH_LABEL[obj]
        anc = src.get(label)
        bench = cell["arms"][obj]["signals"]["V-BENCH"]
        if anc is None:
            out[f"{obj}_checked"] = False
            consistent = False                          # P12: missing per-object anchor is a defect
            continue
        m_ok = bench.m == (int(anc["m"]) if anc.get("m") is not None else 0)
        med_ok = _float_match(bench.median, anc.get("median"))
        out.update({f"{obj}_checked": True, f"{obj}_vbench_m": bench.m,
                    f"{obj}_exp061_m": anc.get("m"), f"{obj}_vbench_median": bench.median,
                    f"{obj}_exp061_median": anc.get("median"),
                    f"{obj}_m_match": bool(m_ok), f"{obj}_median_match": bool(med_ok)})
        consistent = consistent and m_ok and med_ok
    out["consistent"] = bool(consistent)
    return out


def exp062_tail_crosscheck(
    instrument: str, cell: dict[str, Any], tail_map: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    """Disclosed L2->L3 cross-check of each object's V-NONE tail-share vs EXP-062 (not a gate)."""
    key = (instrument, cell["domain"])
    if not tail_map or key not in tail_map or cell.get("empty"):
        return {"checked": False, "cell": f"{instrument}-{cell.get('domain')}"}
    out: dict[str, Any] = {"checked": True, "cell": f"{instrument}-{cell['domain']}",
                           "exp062_row": {k: tail_map[key].get(k) for k in tail_map[key]
                                          if k not in ("instrument", "domain")}}
    for obj in OBJECTS:
        none = cell["arms"][obj]["signals"]["V-NONE"]
        out[f"{obj}_vnone_tail_share_worst5"] = none.tail_share_worst5
        out[f"{obj}_vnone_m"] = none.m
    return out


def _float_match(a: float | None, b: float | None) -> bool:
    """Two optional floats agree to RECON_TOL (both None counts as a match)."""
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return abs(float(a) - float(b)) <= RECON_TOL


# --------------------------------------------------------------------------- #
# Plotting (bounded; from collected per-cell summaries -- no reloads), per object
# --------------------------------------------------------------------------- #
def _placeholder(ax: plt.Axes, message: str) -> None:
    ax.text(0.5, 0.5, message, ha="center", va="center")
    ax.axis("off")


def _ov_cells(rows: list[dict[str, Any]], obj: str, variant: str) -> list[dict[str, Any]]:
    return [r for r in rows if not r.get("excluded") and r["object"] == obj
            and r["variant"] == variant]


def plot_median_forest(rows: list[dict[str, Any]], save_path: Path) -> None:
    """Per-object per-variant per-cell median expectancy (bounded binding, /ADV-NONE disclosed)."""
    fig, axes = plt.subplots(1, len(OBJECTS), figsize=(15, 7), sharey=True)
    colours = {"V-BENCH": "#1a9850", "V-RR1": "#4575b4", "V-NONE": "#999999", "V-RAW": "#d73027"}
    for ax, obj in zip(np.atleast_1d(axes), OBJECTS):
        any_data = False
        for variant in VARIANTS:
            cells = sorted([r for r in _ov_cells(rows, obj, variant) if r.get("median") is not None],
                           key=lambda r: (r["instrument"], r["domain"]))
            if not cells:
                continue
            any_data = True
            x = np.arange(len(cells))
            ax.scatter(x, [r["median"] for r in cells], s=12, c=colours[variant],
                       label=variant, alpha=0.7 if variant in BOUNDED else 0.4,
                       marker="o" if variant in BOUNDED else "x")
        if not any_data:
            _placeholder(ax, f"{obj}: no powered cells")
        else:
            ax.axhline(0.0, color="k", lw=0.8, ls="--")
            ax.set_xlabel("cell index (sorted by instrument-domain)")
            ax.legend(fontsize=8)
        ax.set_title(OBJECT_NAME[obj].split(" (")[0])
    axes[0].set_ylabel("per-cell median expectancy (ATR units)")
    fig.suptitle(f"{EXPERIMENT_ID}: per-variant median expectancy on MA (native | hybrid; never pooled)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_signal_attribution(rows: list[dict[str, Any]], save_path: Path) -> None:
    """Per-object per-bounded-variant variant-RM median contrast CI_low (binding discriminator)."""
    fig, axes = plt.subplots(len(OBJECTS), len(BOUNDED), figsize=(13, 9), sharey=True)
    for oi, obj in enumerate(OBJECTS):
        for vi, variant in enumerate(BOUNDED):
            ax = axes[oi, vi]
            cells = sorted([r for r in _ov_cells(rows, obj, variant)
                            if r.get("var_rm_median_low_1s") is not None
                            and np.isfinite(r.get("var_rm_median_low_1s", np.nan))],
                           key=lambda r: r["var_rm_median_low_1s"])
            if not cells:
                _placeholder(ax, f"{obj}/{variant}: no powered cells")
                continue
            x = np.arange(len(cells))
            vals = [r["var_rm_median_low_1s"] for r in cells]
            cols = ["#1a9850" if r["beats_rm"] else "#d73027" for r in cells]
            marks = ["*" if r["domain"] != "4h" else "" for r in cells]
            ax.scatter(x, vals, c=cols, s=16, zorder=3)
            ax.axhline(0.0, color="k", lw=0.8, ls="--")
            ax.set_xticks(x, [f"{m}{r['instrument']}-{r['domain']}"
                              for m, r in zip(marks, cells)], rotation=90, fontsize=4)
            ax.set_title(f"{obj} : {variant} - RM-on-MA (* = non-4h)")
            if vi == 0:
                ax.set_ylabel("contrast median CI_low(1s)")
    fig.suptitle(f"{EXPERIMENT_ID}: signal attribution per object "
                 "(does the variant beat its own matched-random on MA?)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_mean_investigation(rows: list[dict[str, Any]], save_path: Path) -> None:
    """Headline P4: per-object raw vs trimmed mean, /ADV-NONE vs V-BENCH side-by-side."""
    fig, axes = plt.subplots(len(OBJECTS), 2, figsize=(14, 9), sharey=True)
    panels = [("V-NONE", "/ADV-NONE (unbounded reference)"),
              ("V-BENCH", "benchmark 1:1 (bounded)")]
    for oi, obj in enumerate(OBJECTS):
        for pi, (variant, title) in enumerate(panels):
            ax = axes[oi, pi]
            cells = sorted([r for r in _ov_cells(rows, obj, variant) if r.get("mean") is not None],
                           key=lambda r: r["mean"])
            if not cells:
                _placeholder(ax, f"{obj}/{variant}: no powered cells")
                continue
            x = np.arange(len(cells))
            ax.scatter(x, [r["mean"] for r in cells], c="#d73027", s=14, label="raw mean", zorder=3)
            ax.scatter(x, [r.get("trimmed_mean") if r.get("trimmed_mean") is not None else np.nan
                           for r in cells], facecolors="none", edgecolors="#4575b4", s=14,
                       label="10% trimmed mean", zorder=2)
            ax.scatter(x, [r.get("median") if r.get("median") is not None else np.nan
                           for r in cells], c="#1a9850", s=8, marker="_", label="median", zorder=1)
            ax.axhline(0.0, color="k", lw=0.8, ls="--")
            ax.set_title(f"{obj} : {title}")
            if pi == 0:
                ax.set_ylabel("per-cell expectancy (ATR units)")
            ax.legend(fontsize=7)
    fig.suptitle(f"{EXPERIMENT_ID} P4: /ADV-NONE mean negativity -- removable-tail or structural, "
                 "and does bounding lift it? (per object)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_recovery_map(rows: list[dict[str, Any]], save_path: Path) -> None:
    """Bounded-downside recovery mean(bounded)-mean(/ADV-NONE) CI_low, per object."""
    fig, axes = plt.subplots(1, len(OBJECTS), figsize=(15, 6), sharey=True)
    colours = {"V-BENCH": "#1a9850", "V-RR1": "#4575b4"}
    for ax, obj in zip(np.atleast_1d(axes), OBJECTS):
        any_data = False
        for variant in BOUNDED:
            cells = sorted([r for r in _ov_cells(rows, obj, variant)
                            if r.get("recovery_mean_low_1s") is not None
                            and np.isfinite(r.get("recovery_mean_low_1s", np.nan))],
                           key=lambda r: r["recovery_mean_low_1s"])
            if not cells:
                continue
            any_data = True
            x = np.arange(len(cells))
            ax.scatter(x, [r["recovery_mean_low_1s"] for r in cells], s=14, c=colours[variant],
                       label=f"{variant} - /ADV-NONE",
                       marker="o" if variant == "V-BENCH" else "s")
            for i, r in enumerate(cells):
                if r.get("low_n_4h"):
                    ax.scatter([i], [r["recovery_mean_low_1s"]], facecolors="none",
                               edgecolors="#d73027", s=42, lw=1.0)
        if not any_data:
            _placeholder(ax, f"{obj}: no powered recovery contrasts")
        else:
            ax.axhline(0.0, color="k", lw=0.8, ls="--")
            ax.set_xlabel("cell (sorted by recovery CI_low)")
            ax.legend(fontsize=9)
        ax.set_title(f"{obj} (red ring = low-n 4h)")
    axes[0].set_ylabel("mean(bounded) - mean(/ADV-NONE) CI_low(1s) (ATR units)")
    fig.suptitle(f"{EXPERIMENT_ID}: bounded-downside recovery (per object)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_composition_map(rows: list[dict[str, Any]], save_path: Path) -> None:
    """P11/verdict map (V-BENCH flags) per cell, native + hybrid panels."""
    flags = ["median_viable", "beats_rm", "generalises", "recovery_positive", "mean_viable"]
    fig, axes = plt.subplots(len(OBJECTS), 1, figsize=(max(9, 0.16 * 99), 8))
    for ax, obj in zip(np.atleast_1d(axes), OBJECTS):
        cells = sorted(_ov_cells(rows, obj, "V-BENCH"), key=lambda r: (r["instrument"], r["domain"]))
        if not cells:
            _placeholder(ax, f"{obj}: no member cells")
            continue
        matrix = np.array([[1.0 if r.get(f) else 0.0 for r in cells] for f in flags])
        ax.imshow(matrix, cmap="Greens", vmin=0.0, vmax=1.0, aspect="auto")
        ax.set_yticks(range(len(flags)), flags, fontsize=8)
        labels = [f"{'*' if r['domain'] != '4h' else ''}{r['instrument']}-{r['domain']}"
                  for r in cells]
        ax.set_xticks(range(len(cells)), labels, rotation=90, fontsize=3)
        ax.set_title(f"{obj}: V-BENCH per-cell composition (* = non-4h)")
    fig.suptitle(f"{EXPERIMENT_ID}: per-object composition map (never pooled)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def make_plots(rows: list[dict[str, Any]]) -> None:
    """Render the five bounded plots from collected per-cell summaries (both objects)."""
    plot_median_forest(rows, PLOTS_DIR / "per_variant_median_forest.png")
    plot_signal_attribution(rows, PLOTS_DIR / "variant_rm_attribution_forest.png")
    plot_mean_investigation(rows, PLOTS_DIR / "mean_investigation.png")
    plot_recovery_map(rows, PLOTS_DIR / "bounded_downside_recovery_map.png")
    plot_composition_map(rows, PLOTS_DIR / "composition_verdict_map.png")


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def _cell_index_map() -> dict[tuple[str, str], int]:
    """Stable (instrument, domain) -> int index (identical to EXP-060/061)."""
    return {(inst, dom): i for i, (inst, dom) in enumerate(
        (inst, dom) for inst in INSTRUMENTS for dom in DOMAINS)}


def process_instrument(
    instrument: str, anchor: dict[tuple[str, str], dict[str, Any]],
    tail_map: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    """Worker: resolve every member cell of one instrument (the parallel unit).

    Self-contained and pure given identical inputs/seeds: each cell's RNG is seeded by
    ``(BASE_SEED, cell_index, purpose)`` (order-independent), so the per-instrument
    result is identical regardless of worker count or finish order. The parent merges
    these in ``INSTRUMENTS`` order for byte-identical output.
    """
    cell_index = _cell_index_map()
    out: dict[str, Any] = {
        "rows": [], "readiness": [], "recon_rows": [], "tail_rows": [], "meta": None,
        "causality_violations": [], "invariant_violations": [],
        "determinism_checked": [], "non_deterministic": []}
    members = [d for d in DOMAINS if (instrument, d) not in EXCLUDED_CELLS]
    if not members:
        for domain in DOMAINS:
            out["rows"].extend(excluded_rows(instrument, domain))
        return out
    train_1m, meta = load_train_1m(instrument)
    out["meta"] = meta
    replayed = False
    for domain in DOMAINS:
        if (instrument, domain) in EXCLUDED_CELLS:
            out["rows"].extend(excluded_rows(instrument, domain))
            continue
        ci = cell_index[(instrument, domain)]
        cell = compute_cell(train_1m, domain, meta["train_end_epoch_s"], ci)
        if cell.get("empty"):
            out["rows"].extend(excluded_rows(instrument, domain))   # no signal -> placeholder
            out["recon_rows"].append(exp061_reconciliation(instrument, cell, anchor))
            continue
        out["rows"].extend(variant_rows(instrument, cell))
        out["readiness"].append(readiness_row(instrument, cell))
        out["recon_rows"].append(exp061_reconciliation(instrument, cell, anchor))
        out["tail_rows"].append(exp062_tail_crosscheck(instrument, cell, tail_map))
        _record_cell_defects(cell, instrument, domain, out)
        if not replayed and cell["arms"]["nat"]["signals"]["V-BENCH"].m > 0:
            ok = determinism_replay(train_1m, domain, meta["train_end_epoch_s"], ci)
            out["determinism_checked"].append(f"{instrument}-{domain}#{ci}")
            if not ok:
                out["non_deterministic"].append(f"{instrument}-{domain}#{ci}")
            replayed = True
        del cell
    del train_1m
    return out


def _record_cell_defects(cell: dict[str, Any], instrument: str, domain: str,
                         out: dict[str, Any]) -> None:
    """Accumulate per-cell causality / invariant violations (any object)."""
    label = f"{instrument}-{domain}"
    if not cell.get("causality_ok", True):
        out["causality_violations"].append(label)
    inv = cell.get("invariants", {})
    bad = any(not all(inv.get(o, {}).get(k, True) for k in
                      ("raw_le_rr1", "none_zero_adv", "exit_ok", "matched_count_ok"))
              for o in OBJECTS)
    if bad:
        out["invariant_violations"].append(label)


def _run_grid(
    anchor: dict[tuple[str, str], dict[str, Any]],
    tail_map: dict[tuple[str, str], dict[str, Any]], workers: int,
) -> list[dict[str, Any]]:
    """Resolve all instruments (process pool if workers>1) in fixed order."""
    if workers <= 1:
        return [process_instrument(inst, anchor, tail_map)
                for inst in tqdm(INSTRUMENTS, desc="instruments")]
    by_inst: dict[str, dict[str, Any]] = {}
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(process_instrument, inst, anchor, tail_map): inst
                   for inst in INSTRUMENTS}
        for fut in tqdm(as_completed(futures), total=len(futures), desc="instruments"):
            by_inst[futures[fut]] = fut.result()
    return [by_inst[inst] for inst in INSTRUMENTS]     # deterministic reassembly order


def run(workers: int = 1) -> dict[str, Any]:
    """Run all member cells and write artifacts. Returns the run summary.

    Output is byte-identical for any ``workers`` value (order-independent per-cell RNG
    + fixed merge order).
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    anchor = load_exp061_bench()
    tail_map = load_exp062_tail()
    workers = max(1, min(workers, len(INSTRUMENTS)))
    grid = _run_grid(anchor, tail_map, workers)
    rows: list[dict[str, Any]] = []
    readiness: list[dict[str, Any]] = []
    recon_rows: list[dict[str, Any]] = []
    tail_rows: list[dict[str, Any]] = []
    instrument_meta: dict[str, Any] = {}
    defect = {"is_defect": False, "non_deterministic": [], "exp061_mismatch": [],
              "causality_violations": [], "determinism_checked": [],
              "invariant_violations": [], "exp061_available": bool(anchor),
              "exp061_checked_cells": 0, "exp062_available": bool(tail_map), "workers": workers}
    for instrument, res in zip(INSTRUMENTS, grid):     # fixed INSTRUMENTS order
        rows.extend(res["rows"])
        readiness.extend(res["readiness"])
        recon_rows.extend(res["recon_rows"])
        tail_rows.extend(res["tail_rows"])
        if res["meta"] is not None:
            instrument_meta[instrument] = res["meta"]
        for key in ("causality_violations", "invariant_violations",
                    "determinism_checked", "non_deterministic"):
            defect[key].extend(res[key])

    _finalize_defects(defect, recon_rows)
    readout = composition_readout(rows, defect)
    write_outputs(rows, readiness, recon_rows, tail_rows, readout, instrument_meta, defect)
    make_plots(rows)
    return _summarize(rows, readout)


def _finalize_defects(defect: dict[str, Any], recon_rows: list[dict[str, Any]]) -> None:
    """Aggregate defect gates into the binding is_defect flag."""
    defect["exp061_mismatch"] = [r["cell"] for r in recon_rows
                                 if r.get("checked") and not r["consistent"]]
    if defect["exp061_mismatch"]:
        defect["is_defect"] = True
    defect["exp061_checked_cells"] = sum(1 for r in recon_rows if r.get("checked"))
    if not defect["exp061_available"] or defect["exp061_checked_cells"] == 0:
        defect["is_defect"] = True                     # P12: missing anchor is a defect
    causal_instr = {c.split("-")[0] for c in defect["causality_violations"]}
    if len(causal_instr) >= P11_MIN_INSTR:
        defect["is_defect"] = True
    if defect["invariant_violations"]:                 # exact structural checks
        defect["is_defect"] = True
    if defect["non_deterministic"]:                    # byte-identical replay failed
        defect["is_defect"] = True


def write_outputs(
    rows: list[dict[str, Any]], readiness: list[dict[str, Any]],
    recon_rows: list[dict[str, Any]], tail_rows: list[dict[str, Any]],
    readout: dict[str, Any], instrument_meta: dict[str, Any], defect: dict[str, Any],
) -> None:
    """Persist the per-cell parquet, the adverse / mean / attribution maps, and JSON."""
    pl.DataFrame(rows, strict=False).write_parquet(RESULTS_DIR / "per_cell_expectancy.parquet")
    member = [r for r in rows if not r.get("excluded")]
    adverse_cols = ["instrument", "domain", "object", "variant", "adv_model", "binding", "m",
                    "median", "ci_low_1s", "median_viable", "beats_rm", "generalises",
                    "var_rm_median_low_1s", "data_censored", "adv_count", "r_firsthit"]
    _write_csv([{k: r.get(k) for k in adverse_cols} for r in member],
               RESULTS_DIR / "adverse_map.csv")
    mean_cols = ["instrument", "domain", "object", "variant", "binding", "low_n_4h", "m",
                 "median", "mean", "mean_ci_low_1s", "mean_ci_hi_2s", "trimmed_mean",
                 "trim_ci_low_1s", "tail_share_worst5", "gap_median_minus_mean",
                 "recovery_mean_low_1s", "recovery_mean_hi_2s", "recovery_positive",
                 "mean_viable", "win_rate"]
    _write_csv([{k: r.get(k) for k in mean_cols} for r in member],
               RESULTS_DIR / "mean_investigation.csv")
    attr_cols = ["instrument", "domain", "object", "variant", "binding", "m", "rm_m",
                 "rm_draw_count", "rm_median", "var_rm_median_low_1s", "var_rm_median_hi_2s",
                 "var_rm_mean_low_1s", "beats_rm", "paired_vs_bench_low_1s", "paired_n_common"]
    _write_csv([{k: r.get(k) for k in attr_cols} for r in member],
               RESULTS_DIR / "signal_attribution.csv")
    sec_cols = ["instrument", "domain", "object", "variant", "r_firsthit", "win_rate",
                "data_censored", "adv_count", "population", "m"] + \
        [f"ew_{lbl}" for lbl in PX_CLASS_LABELS.values()]
    _write_csv([{k: r.get(k) for k in sec_cols} for r in member],
               RESULTS_DIR / "secondary_map.csv")
    _write_csv(readiness, RESULTS_DIR / "readiness.csv")
    recon_clean = [r for r in recon_rows if r.get("checked")]
    tail_clean = [r for r in tail_rows if r.get("checked")]
    _write_csv(recon_clean, RESULTS_DIR / "reconciliation.csv")
    with open(RESULTS_DIR / "composition_readout.json", "w") as fh:
        json.dump(readout, fh, indent=2, default=str)
    _write_metadata(instrument_meta, defect, recon_clean, tail_clean, readout)


def _write_csv(records: list[dict[str, Any]], path: Path) -> None:
    """Write a CSV (an empty-but-headed frame when there are no records)."""
    frame = pl.DataFrame(records, strict=False) if records else pl.DataFrame({"empty": []})
    frame.write_csv(path)


def _write_metadata(
    instrument_meta: dict[str, Any], defect: dict[str, Any],
    recon_clean: list[dict[str, Any]], tail_clean: list[dict[str, Any]],
    readout: dict[str, Any],
) -> None:
    meta = {
        "experiment_id": EXPERIMENT_ID,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "015", "lead": "L3", "hypothesis": "HYP-016", "family": "CF-HA-HARAMI-001",
        "checkpoint": "2026-06-17-015-ma-substrate-conditioned-harami-full-surface",
        "amendment": "D0-amendment-001-dual-parallel-substrate (2026-06-17); supersedes prior EXP-063",
        "conditioning_objects": OBJECT_NAME,
        "stratum": "TRAIN-only (first 49%); nested TEST + final-30% holdout sealed",
        "population": ("native byte-identical to EXP-060/061 M0; hybrid mask byte-identical to "
                       "EXP-053/060/061 H0; never pooled"),
        "entry_anchor": "harami confirmation-bar real close (every signal arm, both objects)",
        "binding_endpoint": ("per object: median per-event gross ATR-normalised return (P3/P14, "
                             "P15 fills); mean + 10% trimmed mean + worst-5% tail-share = P4 "
                             "diagnostic (decisive co-primary, never a blind disqualifier; P4 "
                             "closure rule)"),
        "variants": {v: ADV_MODEL[v] for v in VARIANTS},
        "binding_axis": list(BOUNDED),
        "disclosed_reference": ["V-NONE (/ADV-NONE; skew source)", "V-RAW (/ADV-EXTREME-raw)"],
        "favourable_held_at_benchmark": "fav = C + rd*0.50*M_sofar (MA-defined M_sofar; shared)",
        "third_barrier": "MA-defined adaptive cap (k=1.5, window=20, floor=6, median, min_moves=5)",
        "adv_extreme_construction": ("faded-move running extreme of the in-progress MA segment "
                                     "over [ma_start_idx+1 .. entry_idx]; buffer 0.25*ATR_entry; "
                                     "rr1 widens adv_dist to >= fav_dist; raw floor 0.10*ATR_entry "
                                     "(P7 Q5: last confirmed MA segment, no look-ahead). MA geometry "
                                     "shared by both objects; only the entry population differs."),
        "params": {
            "atr_period": ATR_PERIOD, "atr_mult": ATR_MULT,
            "favourable_fraction_bench": 0.50, "ma_segmentation": [MA_FAST, MA_SLOW],
            "stat_window": 20, "stat_min_window": 5, "stat_q": 0.75,
            "adv_buffer_frac": ADV_BUFFER_FRAC, "adv_floor_frac": ADV_FLOOR_FRAC,
            "timecap_floor_bench": 6, "timecap_k": 1.5, "timecap_window": 20,
            "timecap_min_moves": 5, "power_floor": POWER_FLOOR, "low_n_4h_threshold": LOW_N_4H,
            "trim_frac": TRIM_FRAC, "tail_frac": TAIL_FRAC, "n_boot": N_BOOT,
            "boot_batch": BOOT_BATCH, "base_seed": BASE_SEED,
            "p11": [P11_MIN_CELLS, P11_MIN_INSTR], "p6_min_non_4h": P6_MIN_NON_4H,
        },
        "statistical_methods": [
            "per-cell median CI (bootstrap_median_distribution + median_ci) -- binding, per "
            "variant per object",
            "per-cell raw mean + 10% trimmed mean CI (bootstrap_stat_distribution) + worst-5% "
            "tail-share -- P4 diagnostic, per variant per object",
            "independent bootstrap contrast variant - own-object RM-on-MA median (contrast_ci) -- "
            "binding signal attribution, per variant per object",
            "bounded-downside recovery contrast mean(bounded)-mean(/ADV-NONE) (contrast_ci) + "
            "variant-benchmark paired-median contrast (paired_median_contrast_ci, common subset), "
            "per object",
        ],
        "phase_verdict": readout["phase_verdict"],
        "phase_stronger_object": readout["phase_stronger_object"],
        "native_verdict": readout["native"]["verdict"],
        "hybrid_verdict": readout["hybrid"]["verdict"],
        "per_object_variant_composition": {
            obj: {v: {
                "median_viable": readout[key]["per_variant"][v]["median_viable"]["composes"],
                "beats_rm": readout[key]["per_variant"][v]["beats_rm"]["composes"],
                "generalises": readout[key]["per_variant"][v]["generalises"]["composes"],
                "mean_viable": readout[key]["per_variant"][v]["mean_viable"]["composes"],
                "recovery_positive": readout[key]["per_variant"][v]["recovery_positive"]["composes"],
            } for v in VARIANTS}
            for obj, key in (("nat", "native"), ("hyb", "hybrid"))
        },
        "parallelism": {
            "workers": defect.get("workers", 1),
            "model": ("per-instrument ProcessPoolExecutor; results reassembled in fixed "
                      "INSTRUMENTS order; per-process native threads pinned to 1 to avoid CPU "
                      "oversubscription. Output is byte-identical across worker counts: every "
                      "RNG is seeded by (BASE_SEED, cell_index, purpose) so draws are "
                      "order-independent, OHLC aggregation is order-independent, and the merge "
                      "order is fixed. The first usable cell per instrument is replayed "
                      "byte-identically in its worker."),
        },
        "determinism_ok": not defect["non_deterministic"],
        "determinism_checked": defect["determinism_checked"],
        "determinism_gate": ("byte-identical re-run of the first usable cell per instrument across "
                             "every object's every variant signal/null returns/median/CIs and the "
                             "variant-RM independent contrast (median + mean)."),
        "causality_ok": not defect["causality_violations"],
        "causality_violations": defect["causality_violations"],
        "invariant_violations": defect["invariant_violations"],
        "invariant_gates": ("per object: V-RAW adv_dist <= V-RR1 adv_dist event-wise (rr1 widens); "
                            "V-NONE produces 0 ADV outcomes (signal + null); each arm's exit-reason "
                            "weights sum to 1.0 (finite real-bar P15 resolution); matched-count "
                            "holds (each null draw target == its variant's signal qualifying m). "
                            "Reconciliation (SUBSTRATE/METHOD_DEFECT): native V-BENCH reproduces "
                            "EXP-061 M0 and hybrid V-BENCH reproduces EXP-061 H0 per-cell m + median "
                            "to 1e-9; a missing anchor is a defect."),
        "exp061_reconciliation": recon_clean,
        "exp061_mismatch": defect["exp061_mismatch"],
        "exp061_available": defect["exp061_available"],
        "exp061_checked_cells": defect["exp061_checked_cells"],
        "exp061_anchor": str(EXP061_PARQUET),
        "exp062_tail_crosscheck": tail_clean,
        "exp062_available": defect["exp062_available"],
        "exp062_anchor": str(EXP062_TAIL_CSV),
        "reproduction_safety": ("native V-BENCH reuses EXP-061 M0/RM0 RNG purposes and hybrid "
                                "V-BENCH reuses EXP-061 H0/RH0 purposes so each reproduces its "
                                "EXP-061 anchor exactly; every other (object, variant) + its RM "
                                "null uses fresh dedicated RNG purpose blocks (>=210000) so no "
                                "EXP-061 stream shifts and the two objects' nulls are disjoint; "
                                "contrasts are deterministic contrast_ci on stored distributions; "
                                "the variant-vs-benchmark paired contrast uses its own per-object "
                                "per-variant RNG purpose."),
        "disclosed_secondaries_not_computed": (
            "With the adverse axis now run on two conditioning objects, the /STRONG-HA arm, the "
            "MAD /STRONG-STAT sensitivity arm, and a separate ZigZag adverse surface are NOT "
            "computed here (runtime/budget); this read focuses on the binding 4-variant MA adverse "
            "axis + the §4 mean investigation, per object. First-hit r, win rate, and exit "
            "composition are emitted per variant per object in secondary_map.csv."),
        "is_defect": defect["is_defect"],
        "de30_disclosure": DE30_DISCLOSURE,
        "fill_approximation": ("P15 path is a documented approximation of unobserved intrabar "
                               "motion; 1-minute base bars are not replayed (EXP-054 bounds it)."),
        "holdout_fence": ("Only Parquet metadata + first train_rows file-order rows read per "
                          "instrument; full file never sorted/collected; every domain bar fenced "
                          "CloseTime <= train_end_ts; forward scans clipped to the data edge -> "
                          "DATA_CENSORED; TEST and final-30% holdout never read."),
        "registry": ("CF-HA-HARAMI-001/HYP-016 (EXP-063); composes the registered MA-SUBSTRATE "
                     "(hybrid + native modes), the benchmark favourable/cap geometry, the registered "
                     "/ADV-EXTREME and /ADV-NONE branches (MA reuse, both objects), and the "
                     "per-object matched-random baselines (nulls). 0 candidate slots, 0 TEST reads; "
                     "characterisation readout feeds the single terminal G-015 (no closure or "
                     "registration here)."),
        "instrument_meta": instrument_meta,
    }
    with open(RESULTS_DIR / "run_metadata.json", "w") as fh:
        json.dump(meta, fh, indent=2, default=str)


def _summarize(rows: list[dict[str, Any]], readout: dict[str, Any]) -> dict[str, Any]:
    """Concise stdout summary."""
    out: dict[str, Any] = {"phase_verdict": readout["phase_verdict"],
                           "phase_stronger_object": readout["phase_stronger_object"],
                           "defect": readout["defect"], "objects": {}}
    for obj, key in (("nat", "native"), ("hyb", "hybrid")):
        pv = readout[key]["per_variant"]
        out["objects"][obj] = {
            "verdict": readout[key]["verdict"],
            "per_variant": {v: {
                "median_viable": pv[v]["median_viable"]["n_cells"],
                "generalises": pv[v]["generalises"]["n_cells"],
                "generalises_composes": pv[v]["generalises"]["composes"],
                "mean_viable": pv[v]["mean_viable"]["n_cells"],
                "recovery_positive": pv[v]["recovery_positive"]["n_cells"],
            } for v in VARIANTS}}
    return out


def _parse_args() -> argparse.Namespace:
    """CLI: --workers controls per-instrument parallelism (default = all CPUs)."""
    parser = argparse.ArgumentParser(
        description=f"{EXPERIMENT_ID} MA adverse geometry + mean (dual-object)")
    parser.add_argument(
        "--workers", type=int, default=(os.cpu_count() or 1),
        help="per-instrument process workers (default: all CPUs; 1 = sequential). "
             "Output is byte-identical for any value.")
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = _parse_args()
    workers = max(1, min(args.workers, len(INSTRUMENTS)))
    LOGGER.info("%s: running %s instruments on %s worker(s)", EXPERIMENT_ID,
                len(INSTRUMENTS), workers)
    summary = run(workers=workers)
    LOGGER.info("\n=== %s complete (dual-object) ===", EXPERIMENT_ID)
    LOGGER.info("phase verdict: %s (stronger object: %s)", summary["phase_verdict"],
                summary["phase_stronger_object"])
    for obj, name in (("nat", "NATIVE"), ("hyb", "HYBRID")):
        o = summary["objects"][obj]
        LOGGER.info("[%s] verdict=%s", name, o["verdict"])
        for variant in VARIANTS:
            s = o["per_variant"][variant]
            LOGGER.info("  %-8s median-viable %s | generalises %s (P11+P6=%s) | mean-viable %s | "
                        "recovery+ %s", variant, s["median_viable"], s["generalises"],
                        s["generalises_composes"], s["mean_viable"], s["recovery_positive"])
    if summary["defect"]["is_defect"]:
        LOGGER.info("DEFECT: %s", json.dumps(summary["defect"], default=str))
    LOGGER.info("artifacts -> %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
