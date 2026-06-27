"""EXP-051 -- Phase 014-A Strong-Move Filter Characterisation (/STRONG-STAT, /STRONG-HA).

`CF-HA-HARAMI-001` / HYP-004. TRAIN-only, gross, descriptive; 0 candidate slots,
0 TEST reads. For each EXP-048-READY cell (instrument x domain) this script, on the
TRAIN analysis stratum only:

1. slices the first-49% (TRAIN) 1-minute rows by the F01 file-order prefix
   convention (no full-file sort/collect; TEST and the final-30% global holdout are
   never read);
2. aggregates the domain (5m strict; 15m/30m/1h/2h/4h at min_coverage=0.90) and
   fences every domain bar to `CloseTime <= train_end_ts`;
3. runs the frozen Wilder-ATR ZigZag substrate (`xen.zigzag`, real bars) -> confirmed
   moves; move magnitude = |EndPrice - StartPrice| on real prices (degenerate E==S
   excluded with record);
4. applies `/STRONG-STAT` (trailing min(20,available) move magnitudes, >=5 warmup
   floor; binding p75 + disclosed median+1*MAD) and `/STRONG-HA` (HA impulse runs of
   3 same-direction qualifying bars mapped into a move's span; binding same-direction
   + disclosed any-direction) via `xen.strong_move` -- HA prices used for detection
   only, never for any magnitude metric;
5. measures the per-cell P10 endpoint per form -- median-magnitude ratio
   rho = median(mag|retained)/median(mag|all defined), retained fraction f, and the
   mechanical materiality flag (rho>=1.5 AND f in [0.10,0.50] AND n_defined>=30) --
   with a non-binding moving-block bootstrap CI on rho for the two binding forms, and
   a disclosed harami<->retained-move overlap secondary (frozen detector +
   `xen.move_position` pivot tiling);
6. runs a determinism replay (second full recompute, identical seeds) and the
   filter/magnitude/HA-self-consistency/causality-fence invariant batteries, and
   applies the P10/P11 composition rules as a mechanical readout (not a gate).

Outputs (results/): per_cell_strong_move.parquet, p10_map.csv,
strong_stat_alt_disclosure.csv, strong_ha_sensitivity.csv, harami_overlap.csv,
excluded_fractions.csv, composition_readout.json, run_metadata.json. Plots (plots/):
STAT-p75 rho heatmap, HA-primary rho heatmap, retained-fraction small-multiple,
materiality composition map. Real prices throughout; no HA price enters any metric.
"""
from __future__ import annotations

import json
import logging
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import polars as pl
import seaborn as sns
from matplotlib.colors import BoundaryNorm, ListedColormap
from tqdm.auto import tqdm

# --------------------------------------------------------------------------- #
# Path setup
# --------------------------------------------------------------------------- #
CODE_DIR = Path(__file__).resolve().parent
EXPERIMENT_DIR = CODE_DIR.parent
PROJECT_ROOT = EXPERIMENT_DIR.parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "timebars"
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
READINESS_MAP = (
    PROJECT_ROOT / "python" / "experiments" / "EXP-048" / "results" / "readiness_map.csv"
)

from xen.bar_aggregator import aggregate_ohlc  # noqa: E402
from xen.ha_harami import detect_ha_harami  # noqa: E402
from xen.heiken_ashi_generator import generate_heiken_ashi  # noqa: E402
from xen.move_position import ASSIGNED, assign_to_moves  # noqa: E402
from xen.strong_move import (  # noqa: E402
    DEFAULT_MIN_WINDOW,
    DEFAULT_RUN_LEN,
    DEFAULT_WINDOW,
    annotate_ha_impulse,
    find_impulse_runs,
    ha_run_warmup_end_time,
    map_runs_to_moves,
    move_magnitudes,
    strong_stat_decisions,
)
from xen.zigzag import generate_zigzag  # noqa: E402

# --------------------------------------------------------------------------- #
# Constants (Phase 014 D0 frozen; conventions from EXP-048 / EXP-049 / EXP-050)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-051"
INSTRUMENTS: list[str] = [
    "BTCUSD", "EURUSD", "USTEC", "XAUUSD", "GBPUSD", "USDJPY", "USDCHF",
    "USDCAD", "AUDUSD", "NZDUSD", "EURJPY", "GBPJPY", "AUDJPY", "US500",
    "US2000", "DE30", "JP225",
]
DOMAINS: dict[str, tuple[int, float | None]] = {
    "5m": (5, None), "15m": (15, 0.90), "30m": (30, 0.90),
    "1h": (60, 0.90), "2h": (120, 0.90), "4h": (240, 0.90),
}
ANALYSIS_FRACTION = 0.7
TRAIN_FRACTION = 0.7
ATR_PERIOD = 14            # P1: Wilder ATR period
ATR_MULT = 1.0             # P1: ATR_MULT
WINDOW = DEFAULT_WINDOW            # P7/P8 trailing window (20)
MIN_WINDOW = DEFAULT_MIN_WINDOW    # P4-analog warmup floor (5)
RUN_LEN = DEFAULT_RUN_LEN          # P8 X = 3 consecutive HA bars
RHO_THRESHOLD = 1.5        # P10(a): median-magnitude ratio bar
F_LO, F_HI = 0.10, 0.50    # P10(b): retained-fraction admissible band
POWER_FLOOR = 30           # reportability floor (defined-decision moves)
N_BOOT = 10_000            # MBB resamples (non-binding CI on rho)
BOOT_MAX_ELEMS = 2_000_000 # batch sizing bound for the bootstrap matrices
BASE_SEED = 20260615       # frozen bootstrap seed (no tuning)
MEMBER_STATUSES = ("READY", "READY_FLAGGED")
TOTAL_CELLS = len(INSTRUMENTS) * len(DOMAINS)
EXCLUDED_FILE_MARKERS = ("analysis70", "analysis_slice", "first70")

# Filter forms: name -> (family, is_binding, seed_slot or None for non-binding).
BINDING_FORMS = ("stat_p75", "ha_primary")
ALL_FORMS = ("stat_p75", "stat_mad", "ha_primary", "ha_sensitivity")
FORM_SEED_SLOT = {"stat_p75": 0, "ha_primary": 1}  # only binding forms bootstrap
# Battery items (1-4) that drive CHARACTERISATION_REFUTED on >=3 instruments.
INVARIANT_NAMES: list[str] = [
    "inv_filter_wellformed", "inv_magnitude", "inv_ha_selfconsistent", "inv_fence",
]
# Per-form materiality status -> int code (composition map).
MSTATUS_CODES: dict[str, int] = {
    "MATERIAL": 0, "NOT_MATERIAL": 1, "NOT_REPORTABLE_BY_POWER": 2, "EXCLUDED": 3,
}
DE30_DISCLOSURE = (
    "DE30 truncated history: broker m1 history ends 2026-01-16; counts/rates derive "
    "from its own realized timeline and are not span-comparable (VAL-003)."
)
LOGGER = logging.getLogger(EXPERIMENT_ID)


# --------------------------------------------------------------------------- #
# I/O helpers (F01 TRAIN-only loader; never sorts/collects the full file)
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
    """Load exactly the TRAIN 1-minute rows (first 49%) by file-order prefix."""
    path = find_source_file(instrument)
    total_rows = int(pl.scan_parquet(path).select(pl.len()).collect().item())
    analysis_rows = int(total_rows * ANALYSIS_FRACTION)
    train_rows = int(analysis_rows * TRAIN_FRACTION)
    cols = ["Symbol", "OpenTime", "CloseTime", "Open", "High", "Low", "Close", "TickVolume"]
    train = pl.scan_parquet(path).select(cols).slice(0, train_rows).collect()
    # F01 prefix convention: the TRAIN boundary is the first `train_rows` rows in
    # FILE ORDER. We intentionally do NOT sort before slicing -- sorting would change
    # which rows fall inside the 49% TRAIN prefix and corrupt the holdout boundary
    # (this is the established EXP-043/048/050 convention, a deliberate divergence
    # from the generic sort-before-slice loader). A non-chronological slice means the
    # source file itself is out of order, so we hard-fail loudly rather than silently
    # repair and shift the boundary.
    if not train.get_column("CloseTime").is_sorted():
        raise RuntimeError(f"{instrument}: TRAIN slice not chronological by CloseTime")
    meta = {
        "source_file": path.name, "total_rows_1m": total_rows,
        "analysis_rows_1m": analysis_rows, "train_rows_1m": train_rows,
        "train_end_ts": str(train.get_column("CloseTime")[-1]),
        "train_end_epoch_s": int(train.get_column("CloseTime").dt.epoch("s")[-1]),
    }
    return train, meta


def load_membership() -> dict[tuple[str, str], str]:
    """Map (instrument, domain) -> EXP-048 readiness status."""
    if not READINESS_MAP.exists():
        raise FileNotFoundError(
            f"EXP-048 readiness map not found at {READINESS_MAP}; EXP-051 is gated on "
            "EXP-048 READINESS_DELIVERED + audit PASS."
        )
    rows = pl.read_csv(READINESS_MAP).select("instrument", "domain", "status").to_dicts()
    return {(r["instrument"], r["domain"]): r["status"] for r in rows}


# --------------------------------------------------------------------------- #
# Pure computation -- per-cell core
# --------------------------------------------------------------------------- #
def build_domain(
    train_1m: pl.DataFrame, period_minutes: int, min_coverage: float | None,
    train_end_epoch: int,
) -> pl.DataFrame:
    """Aggregate one domain on the TRAIN slice and fence to the TRAIN edge."""
    bars = aggregate_ohlc(train_1m, period_minutes=period_minutes, min_coverage=min_coverage)
    return bars.filter(pl.col("CloseTime").dt.epoch("s") <= train_end_epoch)


def _cell_form_rng(cell_index: int, form: str) -> np.random.Generator:
    """Deterministic, independent per-(cell, binding form) RNG (SeedSequence spawn)."""
    slot = 2 * cell_index + FORM_SEED_SLOT[form]
    child = np.random.SeedSequence(BASE_SEED).spawn(2 * TOTAL_CELLS)[slot]
    return np.random.default_rng(child)


def mbb_ci_rho(
    mag_defined: np.ndarray, retained_defined: np.ndarray, rng: np.random.Generator,
    n_boot: int = N_BOOT,
) -> tuple[float | None, float | None, int, int]:
    """Moving-block bootstrap CI on rho = median(mag|retained)/median(mag|all defined).

    Resamples the ConfirmTime-ordered (mag, retained_flag) tuples of the defined moves
    in contiguous blocks of length ``b = max(1, round(n**(1/3)))`` (``ceil(n/b)`` blocks
    per resample, truncated to ``n``). Resamples with zero retained yield ``rho* = NaN``
    and are dropped from the percentiles (count disclosed). Returns
    ``(ci_low, ci_high, n_nan_dropped, block_len)``; CIs are the 2.5/97.5 percentiles.
    Non-binding disclosed support -- never enters the P10/P11 decision.
    """
    n = int(mag_defined.shape[0])
    b = max(1, int(round(n ** (1.0 / 3.0))))
    n_blocks = int(np.ceil(n / b))
    max_start = max(0, n - b)
    offsets = np.arange(b, dtype=np.int64)
    batch = max(1, BOOT_MAX_ELEMS // max(1, n))
    ret = retained_defined.astype(bool)
    rho_stars: list[np.ndarray] = []
    done = 0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)  # all-NaN nanmedian rows
        while done < n_boot:
            k = min(batch, n_boot - done)
            starts = rng.integers(0, max_start + 1, size=(k, n_blocks))
            idx = (starts[:, :, None] + offsets[None, None, :]).reshape(k, n_blocks * b)[:, :n]
            mag_mat = mag_defined[idx]
            ret_mat = ret[idx]
            all_med = np.median(mag_mat, axis=1)
            masked = np.where(ret_mat, mag_mat, np.nan)
            ret_med = np.nanmedian(masked, axis=1)
            rho_stars.append(ret_med / all_med)
            done += k
    rho_all = np.concatenate(rho_stars)
    finite = rho_all[np.isfinite(rho_all)]
    n_dropped = int(rho_all.shape[0] - finite.shape[0])
    if finite.shape[0] == 0:
        return None, None, n_dropped, b
    lo, hi = np.percentile(finite, [2.5, 97.5])
    return float(lo), float(hi), n_dropped, b


def _form_stats(
    mag_all: np.ndarray, defined: np.ndarray, retained: np.ndarray,
    move_has_harami: np.ndarray, assigned_move_idx: np.ndarray, n_assigned_harami: int,
    is_binding: bool, rng: np.random.Generator | None,
) -> dict[str, Any]:
    """Per-form P10 statistics, bootstrap CI (binding only), and overlap (binding only)."""
    if not (mag_all.shape == defined.shape == retained.shape == move_has_harami.shape):
        raise ValueError(
            "length mismatch among mag_all/defined/retained/move_has_harami: "
            f"{mag_all.shape}, {defined.shape}, {retained.shape}, {move_has_harami.shape}")
    # Intentional masking: restrict retention to defined-decision moves. For /STRONG-STAT
    # retained is already a subset of defined (degenerate mag=0 never clears a positive
    # threshold; <min_window-prior moves are never retained). For /STRONG-HA the raw run
    # mapping may retain a move whose span fully contains a run but which is excluded as
    # DEGENERATE (E==S) -- a legitimate, rare exclusion, not a masked bug (the invariant
    # battery verifies no NON-degenerate move with a run is left undefined).
    retained = retained & defined
    n_defined = int(defined.sum())
    n_retained = int(retained.sum())
    mags_def = mag_all[defined]
    mags_ret = mag_all[retained]
    med_all = float(np.median(mags_def)) if n_defined else None
    iqr_all = (float(np.percentile(mags_def, 75) - np.percentile(mags_def, 25))
               if n_defined else None)
    med_ret = float(np.median(mags_ret)) if n_retained else None
    iqr_ret = (float(np.percentile(mags_ret, 75) - np.percentile(mags_ret, 25))
               if n_retained else None)
    f = (n_retained / n_defined) if n_defined else None
    rho = (med_ret / med_all) if (n_retained > 0 and med_all not in (None, 0.0)) else None
    reportable = n_defined >= POWER_FLOOR
    material = bool(
        reportable and rho is not None and rho >= RHO_THRESHOLD
        and f is not None and F_LO <= f <= F_HI)

    ci_low = ci_high = ci_nan = block_len = None
    overlap_a = overlap_b = None
    if is_binding:
        if reportable and rng is not None:
            ci_low, ci_high, ci_nan, block_len = mbb_ci_rho(
                mags_def, retained[defined], rng)
        overlap_a = (
            float((retained & move_has_harami).sum() / n_retained) if n_retained else None)
        if n_assigned_harami:
            overlap_b = float(retained[assigned_move_idx].sum() / n_assigned_harami)
    return {
        "n_defined": n_defined, "n_retained": n_retained, "f": f,
        "med_all": med_all, "iqr_all": iqr_all, "med_ret": med_ret, "iqr_ret": iqr_ret,
        "rho": rho, "reportable": reportable, "material": material,
        "ci_low": ci_low, "ci_high": ci_high, "ci_nan_dropped": ci_nan,
        "block_len": block_len, "overlap_A": overlap_a, "overlap_B": overlap_b,
    }


def compute_core(
    train_1m: pl.DataFrame, period_minutes: int, min_coverage: float | None,
    train_end_epoch: int, cell_index: int,
) -> dict[str, Any]:
    """Build domain, moves, both filters, P10 stats, CI, overlap, invariants.

    Pure given identical inputs/seeds. Returns a flat dict (nested per-form) of all
    measured fields used for the determinism replay and the long output frame.
    """
    bars = build_domain(train_1m, period_minutes, min_coverage, train_end_epoch)
    n_bars = int(bars.height)
    moves = generate_zigzag(bars, atr_period=ATR_PERIOD, atr_mult=ATR_MULT)
    n_moves = int(moves.height)

    mag_all = move_magnitudes(moves)
    non_degenerate = mag_all > 0.0
    n_degenerate = int((~non_degenerate).sum()) if n_moves else 0

    # /STRONG-STAT decisions (binding p75 + disclosed median+1*MAD).
    stat = strong_stat_decisions(mag_all, window=WINDOW, min_window=MIN_WINDOW)
    stat_defined = stat["defined"] & non_degenerate

    # /STRONG-HA: HA impulse runs mapped into move spans (primary + sensitivity).
    ha_candles = generate_heiken_ashi(bars)
    ha_annot = annotate_ha_impulse(ha_candles, window=WINDOW, min_window=MIN_WINDOW)
    runs = find_impulse_runs(ha_annot, run_len=RUN_LEN)
    warmup_end = ha_run_warmup_end_time(ha_annot, min_window=MIN_WINDOW, run_len=RUN_LEN)
    ha_defined, run_map = _ha_defined_and_runmap(moves, runs, non_degenerate, warmup_end)

    # Harami<->retained-move overlap inputs (frozen detector + pivot tiling).
    haramis = detect_ha_harami(ha_candles)
    n_haramis_total = int(haramis.height)
    move_has_harami, assigned_move_idx, n_assigned_harami = _harami_overlap_inputs(
        haramis, ha_candles, moves, n_moves)

    forms = {
        "stat_p75": _form_stats(
            mag_all, stat_defined, stat["retained_p75"], move_has_harami,
            assigned_move_idx, n_assigned_harami, True, _cell_form_rng(cell_index, "stat_p75")),
        "stat_mad": _form_stats(
            mag_all, stat_defined, stat["retained_mad"], move_has_harami,
            assigned_move_idx, n_assigned_harami, False, None),
        "ha_primary": _form_stats(
            mag_all, ha_defined, run_map["retained_primary"], move_has_harami,
            assigned_move_idx, n_assigned_harami, True, _cell_form_rng(cell_index, "ha_primary")),
        "ha_sensitivity": _form_stats(
            mag_all, ha_defined, run_map["retained_sensitivity"], move_has_harami,
            assigned_move_idx, n_assigned_harami, False, None),
    }

    invariants = _invariants(
        stat, stat_defined, ha_defined, non_degenerate, mag_all, run_map, ha_annot,
        moves, haramis, train_end_epoch)
    return {
        "n_bars": n_bars, "n_moves": n_moves, "n_degenerate": n_degenerate,
        "n_no_decision_stat": int((~stat["defined"] & non_degenerate).sum()) if n_moves else 0,
        "n_no_decision_ha": int((non_degenerate & ~ha_defined).sum()) if n_moves else 0,
        "ha_warmup_bars": int((~ha_annot.get_column("median_defined")).sum()),
        "n_haramis_total": n_haramis_total, "n_assigned_harami": n_assigned_harami,
        "forms": forms, **invariants,
    }


def _ha_defined_and_runmap(
    moves: pl.DataFrame, runs: pl.DataFrame, non_degenerate: np.ndarray,
    warmup_end: object | None,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Defined-decision mask and primary/sensitivity retention for /STRONG-HA."""
    n_moves = int(moves.height)
    if n_moves == 0:
        empty = np.zeros(0, dtype=bool)
        return empty, {"retained_primary": empty, "retained_sensitivity": empty}
    end_epoch = moves.get_column("EndTime").dt.epoch("s").to_numpy()
    start_epoch = moves.get_column("StartTime").dt.epoch("s").to_numpy()
    move_dir = moves.get_column("Direction").to_numpy().astype(np.int64)
    if warmup_end is None:
        ha_defined = np.zeros(n_moves, dtype=bool)
    else:
        warmup_epoch = int(pl.Series([warmup_end]).dt.epoch("s")[0])
        ha_defined = non_degenerate & (end_epoch >= warmup_epoch)
    if runs.height:
        run_map = map_runs_to_moves(
            runs.get_column("run_first_time").dt.epoch("s").to_numpy(),
            runs.get_column("run_last_time").dt.epoch("s").to_numpy(),
            runs.get_column("run_dir").to_numpy().astype(np.int64),
            start_epoch, end_epoch, move_dir)
    else:
        run_map = {"retained_primary": np.zeros(n_moves, dtype=bool),
                   "retained_sensitivity": np.zeros(n_moves, dtype=bool)}
    return ha_defined, run_map


def _harami_overlap_inputs(
    haramis: pl.DataFrame, ha_candles: pl.DataFrame, moves: pl.DataFrame, n_moves: int,
) -> tuple[np.ndarray, np.ndarray, int]:
    """Per-move 'contains an assigned harami' mask + assigned-harami move indices."""
    move_has_harami = np.zeros(n_moves, dtype=bool)
    if n_moves == 0 or haramis.height == 0:
        return move_has_harami, np.empty(0, dtype=np.int64), 0
    events = haramis.select("HA0Time").join(
        ha_candles.select(pl.col("CloseTime").alias("HA0Time"), "RealClose"),
        on="HA0Time", how="left")
    assigned = assign_to_moves(
        events, moves, event_time="HA0Time", event_price="RealClose", left_strict=True
    ).filter(pl.col("exclusion") == ASSIGNED)
    if assigned.height == 0:
        return move_has_harami, np.empty(0, dtype=np.int64), 0
    end_epoch = moves.get_column("EndTime").dt.epoch("s").to_numpy()
    target = assigned.get_column("move_end_time").dt.epoch("s").to_numpy()
    idx = np.searchsorted(end_epoch, target, side="left")  # exact match (unique EndTime)
    idx = idx[idx < n_moves]
    move_has_harami[idx] = True
    return move_has_harami, idx, int(idx.shape[0])


def _invariants(
    stat: dict[str, np.ndarray], stat_defined: np.ndarray, ha_defined: np.ndarray,
    non_degenerate: np.ndarray, mag_all: np.ndarray, run_map: dict[str, np.ndarray],
    ha_annot: pl.DataFrame, moves: pl.DataFrame, haramis: pl.DataFrame,
    train_end_epoch: int,
) -> dict[str, int]:
    """Filter / magnitude / HA-self-consistency / causality-fence invariants (all 0)."""
    n = int(mag_all.shape[0])
    # 1. Filter well-formedness: STAT warmup boundary is exactly 'i >= min_window'
    #    prior moves, and both STAT retained sets are a subset of the STAT defined set.
    expected_def = np.arange(n) >= MIN_WINDOW if n else np.zeros(0, dtype=bool)
    inv_filter = int((stat["defined"] != expected_def).sum()) if n else 0
    inv_filter += int((stat["retained_p75"] & ~stat_defined).sum())
    inv_filter += int((stat["retained_mad"] & ~stat_defined).sum())
    # 2. Magnitudes finite on all moves; non-degenerate magnitudes strictly positive.
    inv_mag = int((~np.isfinite(mag_all)).sum()) if n else 0
    inv_mag += int((mag_all[non_degenerate] <= 0.0).sum()) if n else 0
    # 3. HA self-consistency: primary subset of sensitivity; every NON-degenerate move
    #    retained by a run is HA-defined (the only retained-outside-defined moves are
    #    legitimately degenerate); the exact no-opposing-wick equality holds on every
    #    qualifying bar; and HALow/HAHigh reproduce min/max of (RealLow/High, HAOpen,
    #    HAClose) -- validating the exact-equality construction premise (no rounding,
    #    min/max select an operand verbatim) rather than re-asserting it tautologically.
    inv_ha = int((run_map["retained_primary"] & ~run_map["retained_sensitivity"]).sum())
    inv_ha += int((run_map["retained_primary"] & ~ha_defined & non_degenerate).sum())
    inv_ha += int((run_map["retained_sensitivity"] & ~ha_defined & non_degenerate).sum())
    qual = ha_annot.filter(pl.col("qualify"))
    if qual.height:
        inv_ha += int(qual.filter(
            ((pl.col("Direction") == 1) & (pl.col("HALow") != pl.col("HAOpen")))
            | ((pl.col("Direction") == -1) & (pl.col("HAHigh") != pl.col("HAOpen")))
        ).height)
    if ha_annot.height and {"RealLow", "RealHigh"}.issubset(ha_annot.columns):
        inv_ha += int(ha_annot.filter(
            (pl.col("HALow") != pl.min_horizontal("RealLow", "HAOpen", "HAClose"))
            | (pl.col("HAHigh") != pl.max_horizontal("RealHigh", "HAOpen", "HAClose"))
        ).height)
    # 4. Causality / TRAIN fence.
    fence = 0
    if moves.height:
        fence += int((moves.get_column("ConfirmTime").dt.epoch("s") > train_end_epoch).sum())
    if ha_annot.height:
        fence += int((ha_annot.get_column("CloseTime").dt.epoch("s") > train_end_epoch).sum())
    if haramis.height:
        fence += int((haramis.get_column("HA0Time").dt.epoch("s") > train_end_epoch).sum())
    return {"inv_filter_wellformed": inv_filter, "inv_magnitude": inv_mag,
            "inv_ha_selfconsistent": inv_ha, "inv_fence": fence}


# --------------------------------------------------------------------------- #
# Per-cell orchestration
# --------------------------------------------------------------------------- #
def form_status(member: bool, form_rec: dict[str, Any]) -> str:
    """Mechanical per-form materiality status."""
    if not member:
        return "EXCLUDED"
    if not form_rec["reportable"]:
        return "NOT_REPORTABLE_BY_POWER"
    return "MATERIAL" if form_rec["material"] else "NOT_MATERIAL"


def process_member_cell(
    instrument: str, domain: str, status_048: str, train_1m: pl.DataFrame,
    train_end_epoch: int, cell_index: int,
) -> dict[str, Any]:
    """Process one EXP-048-READY cell: core compute + determinism replay."""
    period_minutes, min_coverage = DOMAINS[domain]
    core1 = compute_core(train_1m, period_minutes, min_coverage, train_end_epoch, cell_index)
    core2 = compute_core(train_1m, period_minutes, min_coverage, train_end_epoch, cell_index)
    return {
        "instrument": instrument, "domain": domain, "exp048_status": status_048,
        "member": True, "determinism_ok": core1 == core2, **core1,
    }


def excluded_cell(instrument: str, domain: str, status_048: str) -> dict[str, Any]:
    """Record for a non-member (not EXP-048-READY) cell -- unmeasured."""
    forms = {name: {k: None for k in (
        "n_defined", "n_retained", "f", "med_all", "iqr_all", "med_ret", "iqr_ret",
        "rho", "reportable", "material", "ci_low", "ci_high", "ci_nan_dropped",
        "block_len", "overlap_A", "overlap_B")} for name in ALL_FORMS}
    for name in ALL_FORMS:
        forms[name]["reportable"] = False
        forms[name]["material"] = False
    rec: dict[str, Any] = {
        "instrument": instrument, "domain": domain, "exp048_status": status_048,
        "member": False, "determinism_ok": None, "n_bars": None, "n_moves": None,
        "n_degenerate": None, "n_no_decision_stat": None, "n_no_decision_ha": None,
        "ha_warmup_bars": None, "n_haramis_total": None, "n_assigned_harami": None,
        "forms": forms,
    }
    for name in INVARIANT_NAMES:
        rec[name] = None
    return rec


# --------------------------------------------------------------------------- #
# Verdict, composition, readout
# --------------------------------------------------------------------------- #
def compute_verdict(records: list[dict[str, Any]]) -> dict[str, Any]:
    """CHARACTERISATION_REFUTED iff non-determinism on any cell, or a battery (1-4)
    invariant fails on >= 3 instruments. Else STRONG_FILTER_CHARACTERISATION_DELIVERED."""
    members = [r for r in records if r["member"]]
    non_det = [f"{r['instrument']}-{r['domain']}" for r in members
               if not r.get("determinism_ok", True)]
    systematic: dict[str, int] = {}
    for name in INVARIANT_NAMES:
        instruments = {r["instrument"] for r in members if (r.get(name) or 0) > 0}
        if len(instruments) >= 3:
            systematic[name] = len(instruments)
    refuted = bool(non_det) or bool(systematic)
    return {
        "verdict": ("CHARACTERISATION_REFUTED" if refuted
                    else "STRONG_FILTER_CHARACTERISATION_DELIVERED"),
        "non_deterministic_cells": non_det,
        "systematic_invariant_failures": systematic,
    }


def _compose_form(records: list[dict[str, Any]], form: str) -> dict[str, Any]:
    """P11 composition + rho/f consistency summary for one filter form."""
    members = [r for r in records if r["member"]]
    reportable = [r for r in members if r["forms"][form]["reportable"]]
    material = [r for r in reportable if r["forms"][form]["material"]]
    instruments = sorted({r["instrument"] for r in material})
    rhos = [r["forms"][form]["rho"] for r in reportable if r["forms"][form]["rho"] is not None]
    fs = [r["forms"][form]["f"] for r in reportable if r["forms"][form]["f"] is not None]
    per_domain = {d: sum(1 for r in material if r["domain"] == d) for d in DOMAINS}
    # Failure-mode split among reportable-not-material (rho leg vs f leg).
    not_material = [r for r in reportable if not r["forms"][form]["material"]]
    fail_rho = sum(1 for r in not_material
                   if (r["forms"][form]["rho"] or 0) < RHO_THRESHOLD)
    fail_f = sum(1 for r in not_material
                 if not (F_LO <= (r["forms"][form]["f"] or -1) <= F_HI))
    return {
        "n_reportable": len(reportable), "n_material": len(material),
        "n_material_instruments": len(instruments), "material_instruments": instruments,
        "material_cells": [f"{r['instrument']}-{r['domain']}" for r in material],
        "p11_pass": len(material) >= 5 and len(instruments) >= 3,
        "rho_summary": _dist_summary(rhos), "f_summary": _dist_summary(fs),
        "material_per_domain": per_domain,
        "fail_rho_leg": fail_rho, "fail_f_leg": fail_f,
    }


def _dist_summary(values: list[float]) -> dict[str, float | None]:
    """Median / IQR / min / max of a value list (None when empty)."""
    if not values:
        return {"n": 0, "median": None, "q25": None, "q75": None, "min": None, "max": None}
    arr = np.asarray(values, dtype=np.float64)
    return {"n": int(arr.shape[0]), "median": float(np.median(arr)),
            "q25": float(np.percentile(arr, 25)), "q75": float(np.percentile(arr, 75)),
            "min": float(arr.min()), "max": float(arr.max())}


def composition_readout(records: list[dict[str, Any]]) -> dict[str, Any]:
    """P10/P11 composition per form + cross-form agreement (mechanical readout)."""
    by_form = {form: _compose_form(records, form) for form in ALL_FORMS}
    members = [r for r in records if r["member"]]
    agreement = {
        "stat_p75_vs_mad_flips": _flip_count(members, "stat_p75", "stat_mad"),
        "ha_primary_vs_sensitivity_flips": _flip_count(members, "ha_primary", "ha_sensitivity"),
    }
    return {
        "by_form": by_form,
        "binding_forms": {f: by_form[f]["p11_pass"] for f in BINDING_FORMS},
        "cross_form_agreement": agreement,
        "rule": ("MATERIAL iff rho = median(mag|retained)/median(mag|all defined) >= 1.5 "
                 "AND retained fraction f in [0.10, 0.50] AND n_defined >= 30 (P10). "
                 "p11_pass iff >=5 MATERIAL cells over >=3 instruments (P11). Binding "
                 "forms: stat_p75, ha_primary. stat_mad / ha_sensitivity disclosed."),
    }


def _flip_count(members: list[dict[str, Any]], form_a: str, form_b: str) -> int:
    """# reportable-in-both cells whose materiality differs between two forms."""
    n = 0
    for r in members:
        fa, fb = r["forms"][form_a], r["forms"][form_b]
        if fa["reportable"] and fb["reportable"] and fa["material"] != fb["material"]:
            n += 1
    return n


# --------------------------------------------------------------------------- #
# Plotting (bounded; from the collected per-cell summary only)
# --------------------------------------------------------------------------- #
def _matrix(records: list[dict[str, Any]], form: str, value: str) -> np.ndarray:
    """instrument x domain matrix of a per-form value (NaN where missing)."""
    domains = list(DOMAINS.keys())
    matrix = np.full((len(INSTRUMENTS), len(domains)), np.nan)
    lookup = {(r["instrument"], r["domain"]): r for r in records}
    for i, inst in enumerate(INSTRUMENTS):
        for j, dom in enumerate(domains):
            rec = lookup.get((inst, dom))
            if rec is None or not rec.get("member"):
                continue
            val = rec["forms"][form].get(value)
            if val is not None:
                matrix[i, j] = float(val)
    return matrix


def _mask_matrix(records: list[dict[str, Any]], form: str, key: str) -> np.ndarray:
    """Boolean instrument x domain mask for a per-form flag (False where missing)."""
    domains = list(DOMAINS.keys())
    mask = np.zeros((len(INSTRUMENTS), len(domains)), dtype=bool)
    lookup = {(r["instrument"], r["domain"]): r for r in records}
    for i, inst in enumerate(INSTRUMENTS):
        for j, dom in enumerate(domains):
            rec = lookup.get((inst, dom))
            if rec is not None and rec.get("member") and rec["forms"][form].get(key):
                mask[i, j] = True
    return mask


def _box_cells(ax: plt.Axes, mask: np.ndarray, color: str) -> None:
    """Outline matrix cells where ``mask`` is True."""
    for i, j in zip(*np.where(mask)):
        ax.add_patch(plt.Rectangle((j, i), 1, 1, fill=False, edgecolor=color, lw=2))


def plot_rho_heatmap(records: list[dict[str, Any]], form: str, title: str,
                     save_path: Path) -> None:
    """Per-cell rho heatmap (diverging at 1.5); MATERIAL cells boxed."""
    matrix = _matrix(records, form, "rho")
    finite = matrix[np.isfinite(matrix)]
    spread = float(np.nanmax(np.abs(finite - RHO_THRESHOLD))) if finite.size else 0.5
    spread = max(spread, 0.5)
    fig, ax = plt.subplots(figsize=(7, 9))
    sns.heatmap(matrix, ax=ax, cmap="RdBu_r", center=RHO_THRESHOLD,
                vmin=RHO_THRESHOLD - spread, vmax=RHO_THRESHOLD + spread, annot=True,
                fmt=".2f", xticklabels=list(DOMAINS.keys()), yticklabels=INSTRUMENTS,
                cbar_kws={"label": "rho = median(mag|retained)/median(mag|all)"},
                annot_kws={"size": 6})
    _box_cells(ax, _mask_matrix(records, form, "material"), "black")
    ax.set_title(f"{EXPERIMENT_ID}: {title} (boxed = MATERIAL, rho>=1.5 & f in [0.10,0.50])")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_f_smallmultiple(records: list[dict[str, Any]], save_path: Path) -> None:
    """Retained-fraction f heatmaps (binding forms); in-band [0.10,0.50] cells boxed."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 9))
    titles = {"stat_p75": "/STRONG-STAT (p75)", "ha_primary": "/STRONG-HA (primary)"}
    for ax, form in zip(axes, BINDING_FORMS):
        matrix = _matrix(records, form, "f")
        sns.heatmap(matrix, ax=ax, cmap="viridis", vmin=0.0, vmax=1.0, annot=True,
                    fmt=".2f", xticklabels=list(DOMAINS.keys()), yticklabels=INSTRUMENTS,
                    cbar_kws={"label": "retained fraction f"}, annot_kws={"size": 6})
        inband = np.isfinite(matrix) & (matrix >= F_LO) & (matrix <= F_HI)
        _box_cells(ax, inband, "red")
        ax.set_title(f"{titles[form]} (boxed = f in [{F_LO:.2f},{F_HI:.2f}])")
    fig.suptitle(f"{EXPERIMENT_ID}: retained fraction f by cell")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_materiality_map(records: list[dict[str, Any]], save_path: Path) -> None:
    """Materiality composition map (binding forms): MATERIAL / NOT_MATERIAL / power / excluded."""
    domains = list(DOMAINS.keys())
    cmap = ListedColormap(["#1a9850", "#fdae61", "#cccccc", "#666666"])
    norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], cmap.N)
    labels = ["MATERIAL", "NOT_MATERIAL", "NOT_REPORTABLE", "EXCLUDED"]
    fig, axes = plt.subplots(1, 2, figsize=(13, 9))
    titles = {"stat_p75": "/STRONG-STAT (p75)", "ha_primary": "/STRONG-HA (primary)"}
    lookup = {(r["instrument"], r["domain"]): r for r in records}
    for ax, form in zip(axes, BINDING_FORMS):
        codes = np.full((len(INSTRUMENTS), len(domains)), MSTATUS_CODES["EXCLUDED"])
        for i, inst in enumerate(INSTRUMENTS):
            for j, dom in enumerate(domains):
                rec = lookup.get((inst, dom))
                member = bool(rec and rec.get("member"))
                codes[i, j] = MSTATUS_CODES[form_status(member, rec["forms"][form])
                                            if member else "EXCLUDED"]
        sns.heatmap(codes, ax=ax, cmap=cmap, norm=norm, cbar=False,
                    xticklabels=domains, yticklabels=INSTRUMENTS, linewidths=0.5,
                    linecolor="white")
        ax.set_title(titles[form])
    handles = [plt.Rectangle((0, 0), 1, 1, color=cmap(i)) for i in range(len(labels))]
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False)
    fig.suptitle(f"{EXPERIMENT_ID}: P10 materiality by cell (binding forms)")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def make_plots(records: list[dict[str, Any]]) -> None:
    """Render the four bounded plots from the collected per-cell summary."""
    plot_rho_heatmap(records, "stat_p75", "/STRONG-STAT (p75) rho",
                     PLOTS_DIR / "strong_stat_rho_heatmap.png")
    plot_rho_heatmap(records, "ha_primary", "/STRONG-HA (primary) rho",
                     PLOTS_DIR / "strong_ha_rho_heatmap.png")
    plot_f_smallmultiple(records, PLOTS_DIR / "retained_fraction_heatmap.png")
    plot_materiality_map(records, PLOTS_DIR / "materiality_composition_map.png")


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #
def _long_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flatten per-cell records into one row per (cell, filter_form)."""
    rows: list[dict[str, Any]] = []
    for r in records:
        cell_fields = {
            "instrument": r["instrument"], "domain": r["domain"],
            "exp048_status": r["exp048_status"], "member": r["member"],
            "determinism_ok": r["determinism_ok"], "n_bars": r["n_bars"],
            "n_moves": r["n_moves"], "n_degenerate": r["n_degenerate"],
            "n_no_decision_stat": r["n_no_decision_stat"],
            "n_no_decision_ha": r["n_no_decision_ha"], "ha_warmup_bars": r["ha_warmup_bars"],
            "n_haramis_total": r["n_haramis_total"], "n_assigned_harami": r["n_assigned_harami"],
            **{name: r.get(name) for name in INVARIANT_NAMES},
        }
        for form in ALL_FORMS:
            fr = r["forms"][form]
            rows.append({
                **cell_fields, "filter_form": form,
                "is_binding": form in BINDING_FORMS,
                "status": form_status(r["member"], fr), **fr,
            })
    return rows


def write_outputs(
    records: list[dict[str, Any]], verdict: dict[str, Any],
    readout: dict[str, Any], instrument_meta: dict[str, Any],
) -> None:
    """Persist the long parquet, the CSV disclosures, and the JSON files."""
    long_rows = _long_rows(records)
    df = pl.DataFrame(long_rows, strict=False)
    df.write_parquet(RESULTS_DIR / "per_cell_strong_move.parquet")

    binding = df.filter(pl.col("is_binding"))
    p10_cols = ["instrument", "domain", "filter_form", "member", "exp048_status", "rho",
                "f", "med_all", "med_ret", "n_defined", "n_retained", "reportable",
                "material", "status", "ci_low", "ci_high", "ci_nan_dropped", "block_len",
                "determinism_ok"]
    binding.select([c for c in p10_cols if c in binding.columns]).write_csv(
        RESULTS_DIR / "p10_map.csv")

    disc_cols = ["instrument", "domain", "rho", "f", "med_all", "med_ret", "n_defined",
                 "n_retained", "reportable", "material", "status"]
    df.filter(pl.col("filter_form") == "stat_mad").select(disc_cols).write_csv(
        RESULTS_DIR / "strong_stat_alt_disclosure.csv")
    df.filter(pl.col("filter_form") == "ha_sensitivity").select(disc_cols).write_csv(
        RESULTS_DIR / "strong_ha_sensitivity.csv")

    binding.select(["instrument", "domain", "filter_form", "n_retained",
                    "overlap_A", "n_assigned_harami", "overlap_B"]).write_csv(
        RESULTS_DIR / "harami_overlap.csv")

    excl = pl.DataFrame(
        [{"instrument": r["instrument"], "domain": r["domain"], "member": r["member"],
          "n_moves": r["n_moves"], "n_degenerate": r["n_degenerate"],
          "degenerate_frac": (r["n_degenerate"] / r["n_moves"]
                              if (r["n_moves"] or 0) > 0 else None),
          "n_no_decision_stat": r["n_no_decision_stat"],
          "n_no_decision_ha": r["n_no_decision_ha"], "ha_warmup_bars": r["ha_warmup_bars"]}
         for r in records], strict=False)
    excl.write_csv(RESULTS_DIR / "excluded_fractions.csv")

    with open(RESULTS_DIR / "composition_readout.json", "w") as fh:
        json.dump(readout, fh, indent=2, default=str)

    meta = {
        "experiment_id": EXPERIMENT_ID,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "014-A", "hypothesis": "HYP-004", "family": "CF-HA-HARAMI-001",
        "variants": ["CF-HA-HARAMI-001/STRONG-STAT", "CF-HA-HARAMI-001/STRONG-HA"],
        "stratum": "TRAIN-only (first 49%); nested TEST + final-30% holdout sealed",
        "unit": "confirmed ZigZag move (real-bar segmentation)",
        "magnitude": "|EndPrice - StartPrice| on real prices; degenerate E==S excluded",
        "filters": {
            "STRONG-STAT": ("trailing min(20,available) confirmed-move magnitudes, "
                            ">=5 warmup floor; binding p75 (numpy linear/type-7), "
                            "disclosed median + 1*raw-MAD; retain on >="),
            "STRONG-HA": ("HA impulse run = 3 consecutive same-direction qualifying bars "
                          "(body >= trailing min(20,available) median HA body, no opposing "
                          "wick exact); binding same-direction run fully in (StartTime,"
                          "EndTime], disclosed any-direction; HA prices detection only"),
        },
        "params": {
            "atr_period": ATR_PERIOD, "atr_mult": ATR_MULT, "atr_estimator": "Wilder",
            "window": WINDOW, "min_window": MIN_WINDOW, "run_len": RUN_LEN,
            "rho_threshold": RHO_THRESHOLD, "f_band": [F_LO, F_HI],
            "power_floor": POWER_FLOOR, "n_boot": N_BOOT, "base_seed": BASE_SEED,
            "boot_max_elems": BOOT_MAX_ELEMS,
            "p75_interpolation": "linear (type-7)", "mad_form": "raw median abs dev (no 1.4826)",
            "ci_form": ("moving-block bootstrap on rho (block=max(1,round(n**(1/3))), "
                        "B=10000, fixed per-(cell,binding form) seed); NON-BINDING"),
        },
        "p10_rule": ("MATERIAL iff rho>=1.5 AND f in [0.10,0.50] AND n_defined>=30; "
                     "point criterion is binding, bootstrap CI is disclosed only"),
        "denominators": {
            "n_defined": "non-degenerate moves with a defined filter decision (per filter)",
            "rho": "median(mag|retained)/median(mag|all defined); n_retained=0 -> rho null",
            "f": "n_retained/n_defined; n_defined<30 -> NOT_REPORTABLE_BY_POWER (never 0/0)",
            "overlap_A": "(#retained moves with >=1 assigned harami)/n_retained (binding forms)",
            "overlap_B": "(#assigned haramis on a retained move)/n_assigned_harami",
        },
        "membership": {
            "source": "EXP-048 readiness_map.csv (READY + READY_FLAGGED)",
            "n_member_cells": sum(1 for r in records if r["member"]),
            "n_excluded_cells": sum(1 for r in records if not r["member"]),
        },
        "verdict": verdict, "composition_readout": readout,
        "de30_disclosure": DE30_DISCLOSURE, "instrument_meta": instrument_meta,
        "holdout_fence": (
            "Only Parquet metadata + first train_rows file-order rows read per "
            "instrument; full file never sorted/collected; every domain bar, move "
            "ConfirmTime, HA CloseTime, and harami HA0Time fenced to CloseTime <= "
            "train_end_ts; TEST and final-30% holdout never read."),
        "note": ("P10/P11 readout is mechanical; the 014-A G1 desk adjudication on this "
                 "readout is checkpoint work, not self-declared here."),
    }
    with open(RESULTS_DIR / "run_metadata.json", "w") as fh:
        json.dump(meta, fh, indent=2, default=str)


def _summarize(
    records: list[dict[str, Any]], verdict: dict[str, Any], readout: dict[str, Any],
) -> dict[str, Any]:
    """Concise stdout summary."""
    out = {"verdict": verdict["verdict"],
           "non_deterministic_cells": verdict["non_deterministic_cells"],
           "systematic_invariant_failures": verdict["systematic_invariant_failures"],
           "by_form": {}}
    for form in ALL_FORMS:
        c = readout["by_form"][form]
        out["by_form"][form] = {"n_material": c["n_material"],
                                "n_material_instruments": c["n_material_instruments"],
                                "p11_pass": c["p11_pass"], "n_reportable": c["n_reportable"]}
    return out


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def run() -> dict[str, Any]:
    """Run all member cells and write artifacts. Returns a run summary."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    membership = load_membership()
    cell_index = {(inst, dom): i for i, (inst, dom) in enumerate(
        (inst, dom) for inst in INSTRUMENTS for dom in DOMAINS)}

    records: list[dict[str, Any]] = []
    instrument_meta: dict[str, Any] = {}
    for instrument in tqdm(INSTRUMENTS, desc="instruments"):
        members = [d for d in DOMAINS
                   if membership.get((instrument, d)) in MEMBER_STATUSES]
        if not members:
            for domain in DOMAINS:
                records.append(excluded_cell(
                    instrument, domain, membership.get((instrument, domain), "UNKNOWN")))
            continue
        train_1m, meta = load_train_1m(instrument)
        instrument_meta[instrument] = meta
        for domain in DOMAINS:
            status_048 = membership.get((instrument, domain), "UNKNOWN")
            if status_048 in MEMBER_STATUSES:
                records.append(process_member_cell(
                    instrument, domain, status_048, train_1m,
                    meta["train_end_epoch_s"], cell_index[(instrument, domain)]))
            else:
                records.append(excluded_cell(instrument, domain, status_048))
        del train_1m

    verdict = compute_verdict(records)
    readout = composition_readout(records)
    write_outputs(records, verdict, readout, instrument_meta)
    make_plots(records)
    return _summarize(records, verdict, readout)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    summary = run()
    LOGGER.info("\n=== %s complete ===", EXPERIMENT_ID)
    LOGGER.info("verdict: %s", summary["verdict"])
    for form, c in summary["by_form"].items():
        LOGGER.info("  %-15s material=%s/%s reportable, instruments=%s, p11_pass=%s",
                    form, c["n_material"], c["n_reportable"],
                    c["n_material_instruments"], c["p11_pass"])
    if summary["non_deterministic_cells"]:
        LOGGER.info("NON-DETERMINISTIC: %s", summary["non_deterministic_cells"])
    if summary["systematic_invariant_failures"]:
        LOGGER.info("SYSTEMATIC INVARIANT FAILURES: %s",
                    json.dumps(summary["systematic_invariant_failures"]))
    LOGGER.info("artifacts -> %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
