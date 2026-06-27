"""EXP-052 -- Phase 014-A Signal-Interpretation Characterisation (direct vs /CONFIRM).

`CF-HA-HARAMI-001` / HYP-005. TRAIN-only, gross, descriptive; 0 candidate slots,
0 TEST reads; NO viability gate. For each EXP-048-READY cell (instrument x domain),
on the TRAIN analysis stratum only, this script compares two entry interpretations of
the same HA harami signal:

  DIRECT  -- enter at the harami signal bar (real close);
  CONFIRM -- a stop at the signal bar's real extreme in the predicted reversal
             direction, filled only if a later real bar trades through it before the
             next ZigZag confirmation (capped at the P4 adaptive horizon).

Per cell it measures (gross, real prices): frequency (fill_rate = n_fills/n_signals),
timing (lead in bars over the ZigZag trend-change confirmation), and the subsequent
outcome distribution -- direction-signed ATR-normalized MFE/MAE (primary) and the
EXP-049 symmetric fav-before-adv `r` reusing `xen.capture_barriers` (secondary,
disclosed) -- and emits a NON-BINDING paired CONFIRM-DIRECT shift readout with a P11
composition count. Detection on HA candles; every outcome on real prices.

Pipeline per cell: F01 first-49% (TRAIN) 1-minute prefix (no full-file sort/collect;
TEST + final-30% holdout never read) -> domain aggregate (5m strict; others
min_coverage=0.90) fenced to train_end_ts -> Wilder-ATR ZigZag (`xen.zigzag`) confirmed
moves + Wilder ATR -> HA candles + harami detector -> causal reversal-direction
context + per-signal P4 cap + CONFIRM fill + per-arm MFE/MAE (`xen.confirm_entry`) ->
secondary barriers (`xen.capture_barriers.resolve_first_touch`/`summarize_geometry`) ->
moving-block bootstrap CIs (per-arm + paired) -> invariant battery + determinism replay.

Outputs (results/): per_cell_confirm.parquet, outcome_primary.csv,
outcome_secondary_r.csv, timing.csv, comparison_readout.csv, excluded_fractions.csv,
composition_readout.json, run_metadata.json. Plots (plots/): fill_rate heatmap,
lead DIRECT vs CONFIRM, per-arm MFE/MAE summary, paired-delta vs fill_rate scatter.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from math import ceil
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import polars as pl
import seaborn as sns
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
from xen.capture_barriers import (  # noqa: E402
    FAVOURABLE_FRACTION,
    NULL_R,
    RESOLVED_FLOOR,
    resolve_first_touch,
    summarize_geometry,
)
from xen.confirm_entry import (  # noqa: E402
    assign_reversal_context,
    evaluate_events,
    exact_bar_indices,
    signal_time_caps,
)
from xen.ha_harami import detect_ha_harami  # noqa: E402
from xen.heiken_ashi_generator import generate_heiken_ashi  # noqa: E402
from xen.zigzag import generate_zigzag, wilder_atr  # noqa: E402

# --------------------------------------------------------------------------- #
# Constants (Phase 014 D0 frozen; conventions from EXP-048..051)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-052"
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
POWER_FLOOR = 30           # reportability floor (events; mirrors RESOLVED_FLOOR)
N_BOOT = 10_000            # MBB resamples (non-binding CIs)
BOOT_MAX_ELEMS = 2_000_000  # batch sizing bound for bootstrap matrices
BASE_SEED = 20260615       # frozen bootstrap seed (no tuning)
P11_CELLS = 5              # P11: composition cell floor
P11_INSTRUMENTS = 3        # P11: composition instrument floor
MEMBER_STATUSES = ("READY", "READY_FLAGGED")
TOTAL_CELLS = len(INSTRUMENTS) * len(DOMAINS)
EXCLUDED_FILE_MARKERS = ("analysis70", "analysis_slice", "first70")

# Independent bootstrap RNG slots per cell.
BOOT_SLOTS = {"direct_mmm": 0, "confirm_mmm": 1, "paired": 2, "direct_r": 3, "confirm_r": 4}
N_SLOTS = len(BOOT_SLOTS)
# Battery items (1-4) that drive CHARACTERISATION_REFUTED on >=3 instruments.
INVARIANT_NAMES: list[str] = [
    "inv_event_wellformed", "inv_stop_fill", "inv_mfe_mae", "inv_fence",
]
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
    # F01 prefix convention: the TRAIN boundary is the first `train_rows` rows in FILE
    # ORDER. We intentionally do NOT sort before slicing -- sorting would change which
    # rows fall inside the 49% TRAIN prefix and corrupt the holdout boundary (the
    # established EXP-043/048..051 convention). A non-chronological slice means the
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
            f"EXP-048 readiness map not found at {READINESS_MAP}; EXP-052 is gated on "
            "EXP-048 READINESS_DELIVERED + audit PASS."
        )
    rows = pl.read_csv(READINESS_MAP).select("instrument", "domain", "status").to_dicts()
    return {(r["instrument"], r["domain"]): r["status"] for r in rows}


# --------------------------------------------------------------------------- #
# Bootstrap helpers (moving-block; non-binding disclosed CIs)
# --------------------------------------------------------------------------- #
def _cell_rng(cell_index: int, slot: str) -> np.random.Generator:
    """Deterministic, independent per-(cell, statistic) RNG (SeedSequence spawn)."""
    child = np.random.SeedSequence(BASE_SEED).spawn(N_SLOTS * TOTAL_CELLS)[
        N_SLOTS * cell_index + BOOT_SLOTS[slot]]
    return np.random.default_rng(child)


def _block_index_matrix(
    n: int, rng: np.random.Generator, k: int,
) -> tuple[np.ndarray, int]:
    """A (k, n) moving-block resample index matrix; returns (idx, block_len)."""
    b = max(1, int(round(n ** (1.0 / 3.0))))
    n_blocks = int(ceil(n / b))
    max_start = max(0, n - b)
    offsets = np.arange(b, dtype=np.int64)
    starts = rng.integers(0, max_start + 1, size=(k, n_blocks))
    idx = (starts[:, :, None] + offsets[None, None, :]).reshape(k, n_blocks * b)[:, :n]
    return idx, b


def mbb_ci_median(
    values: np.ndarray, rng: np.random.Generator, n_boot: int = N_BOOT,
) -> tuple[float | None, float | None]:
    """Two-sided 95% moving-block bootstrap CI of the median of a 1-D array."""
    v = values[np.isfinite(values)].astype(np.float64)
    n = int(v.shape[0])
    if n == 0:
        return None, None
    batch = max(1, BOOT_MAX_ELEMS // max(1, n))
    meds: list[np.ndarray] = []
    done = 0
    while done < n_boot:
        k = min(batch, n_boot - done)
        idx, _ = _block_index_matrix(n, rng, k)
        meds.append(np.median(v[idx], axis=1))
        done += k
    allm = np.concatenate(meds)
    lo, hi = np.percentile(allm, [2.5, 97.5])
    return float(lo), float(hi)


def mbb_ci_paired_diff(
    arm_a: np.ndarray, arm_b: np.ndarray, rng: np.random.Generator,
    n_boot: int = N_BOOT,
) -> tuple[float | None, float | None, float | None]:
    """MBB CI of ``median(arm_b) - median(arm_a)`` over a paired event sequence.

    Resamples paired event indices in contiguous blocks (preserving serial
    dependence). Returns ``(ci_low_1s, ci_lo_2s, ci_hi_2s)`` (5th / 2.5th / 97.5th).
    """
    a = arm_a.astype(np.float64)
    b = arm_b.astype(np.float64)
    n = int(a.shape[0])
    if n == 0:
        return None, None, None
    batch = max(1, BOOT_MAX_ELEMS // max(1, n))
    diffs: list[np.ndarray] = []
    done = 0
    while done < n_boot:
        k = min(batch, n_boot - done)
        idx, _ = _block_index_matrix(n, rng, k)
        diffs.append(np.median(b[idx], axis=1) - np.median(a[idx], axis=1))
        done += k
    alld = np.concatenate(diffs)
    lo1, lo2, hi2 = np.percentile(alld, [5.0, 2.5, 97.5])
    return float(lo1), float(lo2), float(hi2)


# --------------------------------------------------------------------------- #
# Pure computation -- small summaries
# --------------------------------------------------------------------------- #
def _med_iqr(values: np.ndarray) -> tuple[float | None, float | None, int]:
    """Median, IQR, and count of the finite entries of a 1-D array."""
    v = values[np.isfinite(values)]
    n = int(v.shape[0])
    if n == 0:
        return None, None, 0
    return (float(np.median(v)),
            float(np.percentile(v, 75) - np.percentile(v, 25)), n)


def _secondary_r(
    entry_idx: np.ndarray, entry_price: np.ndarray, rd: np.ndarray,
    ref_mag: np.ndarray, n_event: np.ndarray, defined: np.ndarray,
    high: np.ndarray, low: np.ndarray, n_bars: int, rng: np.random.Generator,
) -> dict[str, Any]:
    """EXP-049 symmetric fav-before-adv `r` from a set of arm entries (disclosed)."""
    if entry_idx.shape[0] == 0 or not bool(defined.any()):
        return {"fav": 0, "adv": 0, "timecap": 0, "censored": 0, "resolved": 0,
                "r": None, "ci_low_1s": None, "ci_lo_2s": None, "ci_hi_2s": None,
                "reportable": False}
    fav_dist = FAVOURABLE_FRACTION * ref_mag
    fav_target = entry_price + rd * fav_dist
    adv_target = entry_price - rd * fav_dist
    classes = resolve_first_touch(
        high, low, entry_idx.astype(np.int64), fav_target, adv_target,
        rd.astype(np.int64), n_event.astype(np.int64), defined, n_bars)
    res = summarize_geometry(classes, defined, rng)
    return {"fav": res.fav, "adv": res.adv, "timecap": res.timecap,
            "censored": res.data_censored, "resolved": res.resolved, "r": res.r,
            "ci_low_1s": res.ci_low_1s, "ci_lo_2s": res.ci_lo_2s,
            "ci_hi_2s": res.ci_hi_2s, "reportable": res.resolved >= RESOLVED_FLOOR}


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


def compute_core(
    train_1m: pl.DataFrame, period_minutes: int, min_coverage: float | None,
    train_end_epoch: int, cell_index: int,
) -> dict[str, Any]:
    """Build domain, moves, haramis, both arms, outcomes, CIs, invariants.

    Pure given identical inputs/seeds. Returns a flat dict of Python scalars only
    (no numpy arrays) so the determinism replay can compare with ``==``.
    """
    bars = build_domain(train_1m, period_minutes, min_coverage, train_end_epoch)
    n_bars = int(bars.height)
    bar_epoch = bars.get_column("CloseTime").dt.epoch("s").to_numpy()
    high = bars.get_column("High").to_numpy().astype(np.float64)
    low = bars.get_column("Low").to_numpy().astype(np.float64)
    close = bars.get_column("Close").to_numpy().astype(np.float64)
    atr = wilder_atr(high, low, close, ATR_PERIOD)

    moves = generate_zigzag(bars, atr_period=ATR_PERIOD, atr_mult=ATR_MULT)
    n_moves = int(moves.height)
    haramis = detect_ha_harami(generate_heiken_ashi(bars))
    n_haramis_total = int(haramis.height)

    empty = _empty_core(n_bars, n_moves, n_haramis_total)
    if n_moves == 0 or n_haramis_total == 0:
        return empty

    confirm_epoch = moves.get_column("ConfirmTime").dt.epoch("s").to_numpy()
    confirm_idx = exact_bar_indices(bar_epoch, confirm_epoch)
    move_dir = moves.get_column("Direction").to_numpy().astype(np.int64)
    move_start = moves.get_column("StartPrice").to_numpy().astype(np.float64)
    move_end = moves.get_column("EndPrice").to_numpy().astype(np.float64)

    harami_epoch = haramis.get_column("HA0Time").dt.epoch("s").to_numpy()
    s_all = exact_bar_indices(bar_epoch, harami_epoch)
    j_idx, rd_all, ref_mag_all, has_ctx = assign_reversal_context(
        harami_epoch, confirm_epoch, move_dir, move_start, move_end)
    n_event_all, p4_ok = signal_time_caps(j_idx, confirm_idx, has_ctx)

    # next ZigZag confirmation strictly after each harami (bounds the CONFIRM window).
    nj = np.searchsorted(confirm_epoch, harami_epoch, side="right")
    has_next = nj < n_moves
    next_confirm_bar = np.where(
        has_next, confirm_idx[np.minimum(nj, n_moves - 1)],
        n_bars + n_event_all + 2)            # sentinel -> window_end = s + n_event

    direct_noncensored = (s_all + n_event_all) <= (n_bars - 1)
    qualifying = has_ctx & p4_ok & direct_noncensored
    n_signals = int(qualifying.sum())
    counts = {
        "n_bars": n_bars, "n_moves": n_moves, "n_haramis_total": n_haramis_total,
        "n_no_trend_context": int((~has_ctx).sum()),
        "n_p4_warmup": int((has_ctx & ~p4_ok).sum()),
        "n_direct_censored": int((has_ctx & p4_ok & ~direct_noncensored).sum()),
        "n_degenerate_ref": int((has_ctx & (ref_mag_all <= 0.0)).sum()),
        "n_signals": n_signals,
    }
    if n_signals == 0:
        return {**empty, **counts}

    # Qualifying-event arrays.
    s = s_all[qualifying]
    rd = rd_all[qualifying]
    ne = n_event_all[qualifying]
    ref_mag = ref_mag_all[qualifying]
    nxt = next_confirm_bar[qualifying]
    has_nxt = has_next[qualifying]
    stop_level = np.where(rd == 1, high[s], low[s]).astype(np.float64)

    ev = evaluate_events(s, rd, ne, stop_level, nxt, high, low, close, n_bars)
    fill = ev["fill"]
    trigger = ev["trigger_idx"]

    # ATR at entries (real-price normalization).
    atr_d = atr[s]
    atr_c = np.where(fill, atr[np.where(fill, trigger, 0)], np.nan)

    # Per-event direction-signed (MFE-MAE)/ATR for each arm.
    with np.errstate(invalid="ignore", divide="ignore"):
        d_mmm = (ev["direct_mfe"] - ev["direct_mae"]) / atr_d
        c_mmm = np.where(
            fill & ~ev["confirm_censored"],
            (ev["confirm_mfe"] - ev["confirm_mae"]) / np.where(fill, atr_c, np.nan), np.nan)
    d_ok = ~ev["direct_censored"] & np.isfinite(d_mmm)
    c_ok = fill & ~ev["confirm_censored"] & np.isfinite(c_mmm)

    fill_rate = float(fill.sum() / n_signals)
    outcome = _outcome_block(ev, atr_d, atr_c, d_mmm, d_ok, c_mmm, c_ok, cell_index)
    timing = _timing_block(s, trigger, nxt, fill, has_nxt)

    # Paired CONFIRM-DIRECT shift (events filled & non-censored in both arms).
    paired = d_ok & c_ok
    n_paired = int(paired.sum())
    paired_block = _paired_block(d_mmm[paired], c_mmm[paired], n_paired, cell_index)

    # Secondary fav-before-adv r (disclosed), per arm.
    sec_def_d = ref_mag > 0.0
    sec_d = _secondary_r(s, ev["direct_entry_price"], rd, ref_mag, ne, sec_def_d,
                         high, low, n_bars, _cell_rng(cell_index, "direct_r"))
    sec_def_c = fill & (ref_mag > 0.0)
    sec_c = _secondary_r(np.where(fill, trigger, 0), ev["confirm_entry_price"], rd,
                         ref_mag, ne, sec_def_c, high, low, n_bars,
                         _cell_rng(cell_index, "confirm_r"))

    invariants = _invariants(
        s, rd, ne, stop_level, nxt, has_nxt, ev, atr_d, atr_c, high, low,
        bar_epoch, train_end_epoch, counts)
    return {
        **counts, "fill_rate": fill_rate, "n_fills": int(fill.sum()),
        "n_confirm_censored": int((fill & ev["confirm_censored"]).sum()),
        "n_fills_noncensored": int(c_ok.sum()), "n_paired": n_paired,
        **outcome, **timing, **paired_block,
        "secondary_direct": sec_d, "secondary_confirm": sec_c, **invariants,
    }


def _empty_core(n_bars: int, n_moves: int, n_haramis_total: int) -> dict[str, Any]:
    """Zero/None-filled core for cells with no moves or no haramis."""
    none_outcome = {f"{arm}_{k}": None
                    for arm in ("direct", "confirm")
                    for k in ("mfe_atr_med", "mfe_atr_iqr", "mae_atr_med", "mae_atr_iqr",
                              "mmm_med", "mmm_ci_low", "mmm_ci_high")}
    none_outcome.update({"direct_reportable": False, "confirm_reportable": False,
                         "n_direct_used": 0, "n_confirm_used": 0})
    timing = {"lead_direct_med": None, "lead_direct_iqr": None, "lead_confirm_med": None,
              "lead_confirm_iqr": None, "time_to_fill_med": None, "time_to_fill_iqr": None,
              "n_lead_defined": 0}
    paired = {"paired_delta_mmm": None, "paired_delta_ci_low1s": None,
              "paired_delta_ci_low": None, "paired_delta_ci_high": None,
              "shift_sign": None, "paired_reportable": False}
    sec_none = {"fav": 0, "adv": 0, "timecap": 0, "censored": 0, "resolved": 0,
                "r": None, "ci_low_1s": None, "ci_lo_2s": None, "ci_hi_2s": None,
                "reportable": False}
    base = {
        "n_bars": n_bars, "n_moves": n_moves, "n_haramis_total": n_haramis_total,
        "n_no_trend_context": 0, "n_p4_warmup": 0, "n_direct_censored": 0,
        "n_degenerate_ref": 0, "n_signals": 0, "fill_rate": None, "n_fills": 0,
        "n_confirm_censored": 0, "n_fills_noncensored": 0, "n_paired": 0,
        "secondary_direct": dict(sec_none), "secondary_confirm": dict(sec_none),
        **none_outcome, **timing, **paired,
    }
    for name in INVARIANT_NAMES:
        base[name] = 0
    return base


def _outcome_block(
    ev: dict[str, np.ndarray], atr_d: np.ndarray, atr_c: np.ndarray,
    d_mmm: np.ndarray, d_ok: np.ndarray, c_mmm: np.ndarray, c_ok: np.ndarray,
    cell_index: int,
) -> dict[str, Any]:
    """Per-arm MFE/MAE medians + non-binding median(MFE-MAE) CI."""
    out: dict[str, Any] = {}
    for arm, mfe, mae, atr_e, mmm, ok, slot in (
        ("direct", ev["direct_mfe"], ev["direct_mae"], atr_d, d_mmm, d_ok, "direct_mmm"),
        ("confirm", ev["confirm_mfe"], ev["confirm_mae"], atr_c, c_mmm, c_ok, "confirm_mmm"),
    ):
        with np.errstate(invalid="ignore", divide="ignore"):
            mfe_atr = np.where(ok, mfe / atr_e, np.nan)
            mae_atr = np.where(ok, mae / atr_e, np.nan)
        mfe_med, mfe_iqr, _ = _med_iqr(mfe_atr)
        mae_med, mae_iqr, n_used = _med_iqr(mae_atr)
        mmm_vals = mmm[ok]
        mmm_med = float(np.median(mmm_vals)) if n_used else None
        reportable = n_used >= POWER_FLOOR
        ci_low = ci_high = None
        if reportable:
            ci_low, ci_high = mbb_ci_median(mmm_vals, _cell_rng(cell_index, slot))
        out.update({
            f"{arm}_mfe_atr_med": mfe_med, f"{arm}_mfe_atr_iqr": mfe_iqr,
            f"{arm}_mae_atr_med": mae_med, f"{arm}_mae_atr_iqr": mae_iqr,
            f"{arm}_mmm_med": mmm_med, f"{arm}_mmm_ci_low": ci_low,
            f"{arm}_mmm_ci_high": ci_high, f"{arm}_reportable": reportable,
            f"n_{arm}_used": n_used,
        })
    return out


def _timing_block(
    s: np.ndarray, trigger: np.ndarray, nxt: np.ndarray, fill: np.ndarray,
    has_nxt: np.ndarray,
) -> dict[str, Any]:
    """Lead (DIRECT/CONFIRM) and time-to-fill summaries (bars)."""
    lead_direct = np.where(has_nxt, nxt - s, np.nan).astype(np.float64)
    lead_confirm = np.where(has_nxt & fill, nxt - trigger, np.nan).astype(np.float64)
    ttf = np.where(fill, trigger - s, np.nan).astype(np.float64)
    ld_med, ld_iqr, n_lead = _med_iqr(lead_direct)
    lc_med, lc_iqr, _ = _med_iqr(lead_confirm)
    ttf_med, ttf_iqr, _ = _med_iqr(ttf)
    return {"lead_direct_med": ld_med, "lead_direct_iqr": ld_iqr,
            "lead_confirm_med": lc_med, "lead_confirm_iqr": lc_iqr,
            "time_to_fill_med": ttf_med, "time_to_fill_iqr": ttf_iqr,
            "n_lead_defined": n_lead}


def _paired_block(
    a: np.ndarray, b: np.ndarray, n_paired: int, cell_index: int,
) -> dict[str, Any]:
    """Paired CONFIRM-DIRECT median(MFE-MAE) shift with MBB CI and a sign flag."""
    reportable = n_paired >= POWER_FLOOR
    delta = (float(np.median(b) - np.median(a)) if n_paired else None)
    lo1 = lo2 = hi2 = None
    sign = None
    if reportable:
        lo1, lo2, hi2 = mbb_ci_paired_diff(a, b, _cell_rng(cell_index, "paired"))
        if lo2 is not None and lo2 > 0.0:
            sign = "positive"
        elif hi2 is not None and hi2 < 0.0:
            sign = "negative"
        else:
            sign = "flat"
    return {"paired_delta_mmm": delta, "paired_delta_ci_low1s": lo1,
            "paired_delta_ci_low": lo2, "paired_delta_ci_high": hi2,
            "shift_sign": sign, "paired_reportable": reportable}


def _invariants(
    s: np.ndarray, rd: np.ndarray, ne: np.ndarray, stop_level: np.ndarray,
    nxt: np.ndarray, has_nxt: np.ndarray, ev: dict[str, np.ndarray],
    atr_d: np.ndarray, atr_c: np.ndarray, high: np.ndarray, low: np.ndarray,
    bar_epoch: np.ndarray, train_end_epoch: int, counts: dict[str, int],
) -> dict[str, int]:
    """Event / stop-fill / MFE-MAE / causality-fence invariants (all must be 0)."""
    fill = ev["fill"]
    trigger = ev["trigger_idx"]
    n_sig = counts["n_signals"]
    # 1. Event well-formedness: exclusion trichotomy + qualifying sum to total;
    #    fills are a subset of signals; DIRECT events are all non-censored.
    inv_event = abs(
        counts["n_no_trend_context"] + counts["n_p4_warmup"]
        + counts["n_direct_censored"] + n_sig - counts["n_haramis_total"])
    inv_event += int((fill.sum() > n_sig))
    inv_event += int(ev["direct_censored"].sum())          # qualifying => non-censored
    # 2. Stop / fill validity on every fill.
    fi = np.where(fill)[0]
    if fi.shape[0]:
        tr = trigger[fi]
        up_ok = (rd[fi] == 1) & (high[tr] >= stop_level[fi])
        dn_ok = (rd[fi] == -1) & (low[tr] <= stop_level[fi])
        window_end = np.minimum(nxt[fi] - 1, s[fi] + ne[fi])
        inv_stop = int((~(up_ok | dn_ok)).sum())
        inv_stop += int(((tr <= s[fi]) | (tr > window_end)).sum())
        # Lead validity where a subsequent ZigZag confirmation exists:
        # 1 <= lead_confirm <= lead_direct (confirmation can only spend lead).
        hn = has_nxt[fi]
        if bool(hn.any()):
            lead_d = (nxt[fi] - s[fi])[hn]
            lead_c = (nxt[fi] - tr)[hn]
            inv_stop += int(((lead_d < 1) | (lead_c < 1) | (lead_c > lead_d)).sum())
    else:
        inv_stop = 0
    # 3. MFE/MAE validity on used events; ATR positive at used entries.
    d_used = ~ev["direct_censored"]
    inv_mfe = int((ev["direct_mfe"][d_used] < 0).sum() + (ev["direct_mae"][d_used] < 0).sum())
    inv_mfe += int((~np.isfinite(atr_d)).sum() + (atr_d <= 0).sum())
    c_used = fill & ~ev["confirm_censored"]
    if c_used.any():
        inv_mfe += int((ev["confirm_mfe"][c_used] < 0).sum()
                       + (ev["confirm_mae"][c_used] < 0).sum())
        inv_mfe += int((atr_c[c_used] <= 0).sum() + (~np.isfinite(atr_c[c_used])).sum())
    # 4. Causality / TRAIN fence: every used bar index is within TRAIN and fenced.
    fence = int((s + ne > len(bar_epoch) - 1).sum())
    fence += int((bar_epoch[s] > train_end_epoch).sum())
    if fi.shape[0]:
        fence += int((bar_epoch[trigger[fi]] > train_end_epoch).sum())
    return {"inv_event_wellformed": int(inv_event), "inv_stop_fill": int(inv_stop),
            "inv_mfe_mae": int(inv_mfe), "inv_fence": int(fence)}


# --------------------------------------------------------------------------- #
# Per-cell orchestration
# --------------------------------------------------------------------------- #
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
        "member": True, "determinism_ok": core1 == core2,
        "instrument_note": DE30_DISCLOSURE if instrument == "DE30" else None, **core1,
    }


def excluded_cell(instrument: str, domain: str, status_048: str) -> dict[str, Any]:
    """Record for a non-member (not EXP-048-READY) cell -- unmeasured."""
    rec = excluded_template()
    rec.update({"instrument": instrument, "domain": domain,
                "exp048_status": status_048, "member": False, "determinism_ok": None,
                "instrument_note": DE30_DISCLOSURE if instrument == "DE30" else None})
    for name in INVARIANT_NAMES:
        rec[name] = None
    return rec


def excluded_template() -> dict[str, Any]:
    """None-filled scalar fields for an excluded cell (matches member columns)."""
    base = _empty_core(0, 0, 0)
    for k in list(base.keys()):
        if k in ("secondary_direct", "secondary_confirm"):
            base[k] = {kk: None for kk in base[k]}
        else:
            base[k] = None
    return base


# --------------------------------------------------------------------------- #
# Verdict, composition, readout
# --------------------------------------------------------------------------- #
def compute_verdict(records: list[dict[str, Any]]) -> dict[str, Any]:
    """CHARACTERISATION_REFUTED iff non-determinism on any cell, or a battery (1-4)
    invariant fails on >=3 instruments. Else CONFIRM_CHARACTERISATION_DELIVERED."""
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
                    else "CONFIRM_CHARACTERISATION_DELIVERED"),
        "non_deterministic_cells": non_det,
        "systematic_invariant_failures": systematic,
    }


def composition_readout(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Non-binding P11 composition on the paired CONFIRM-DIRECT shift sign."""
    members = [r for r in records if r["member"]]
    reportable = [r for r in members if r.get("paired_reportable")]
    pos = [r for r in reportable if r.get("shift_sign") == "positive"]
    neg = [r for r in reportable if r.get("shift_sign") == "negative"]
    pos_inst = sorted({r["instrument"] for r in pos})
    neg_inst = sorted({r["instrument"] for r in neg})
    per_domain = {
        d: {"positive": sum(1 for r in pos if r["domain"] == d),
            "negative": sum(1 for r in neg if r["domain"] == d),
            "flat": sum(1 for r in reportable
                        if r["domain"] == d and r.get("shift_sign") == "flat")}
        for d in DOMAINS}
    return {
        "n_reportable": len(reportable),
        "n_pos": len(pos), "n_pos_instruments": len(pos_inst),
        "pos_instruments": pos_inst, "pos_cells": [f"{r['instrument']}-{r['domain']}" for r in pos],
        "p11_pos_readout": len(pos) >= P11_CELLS and len(pos_inst) >= P11_INSTRUMENTS,
        "n_neg": len(neg), "n_neg_instruments": len(neg_inst),
        "neg_instruments": neg_inst, "neg_cells": [f"{r['instrument']}-{r['domain']}" for r in neg],
        "p11_neg_readout": len(neg) >= P11_CELLS and len(neg_inst) >= P11_INSTRUMENTS,
        "per_domain_shift": per_domain,
        "fill_rate_summary": _dist_summary([r["fill_rate"] for r in members]),
        "lead_direct_summary": _dist_summary([r["lead_direct_med"] for r in members]),
        "lead_confirm_summary": _dist_summary([r["lead_confirm_med"] for r in members]),
        "paired_delta_summary": _dist_summary([r["paired_delta_mmm"] for r in reportable]),
        "rule": ("NON-BINDING readout: a cell shows a positive (negative) confirmation "
                 "shift iff its paired median((MFE-MAE)/ATR) CONFIRM-DIRECT difference "
                 "has two-sided 95% CI_low>0 (CI_high<0). Composition readout iff >=5 "
                 "such cells over >=3 instruments (P11). Selects/routes nothing; HYP-005 "
                 "has no viability gate."),
    }


def _dist_summary(values: list[Any]) -> dict[str, float | int | None]:
    """Median / IQR / min / max of the finite entries of a value list."""
    arr = np.asarray([v for v in values if v is not None], dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    if arr.shape[0] == 0:
        return {"n": 0, "median": None, "q25": None, "q75": None, "min": None, "max": None}
    return {"n": int(arr.shape[0]), "median": float(np.median(arr)),
            "q25": float(np.percentile(arr, 25)), "q75": float(np.percentile(arr, 75)),
            "min": float(arr.min()), "max": float(arr.max())}


# --------------------------------------------------------------------------- #
# Plotting (bounded; from the collected per-cell summary only)
# --------------------------------------------------------------------------- #
def _cell_matrix(records: list[dict[str, Any]], key: str) -> np.ndarray:
    """instrument x domain matrix of a per-cell scalar (NaN where missing)."""
    domains = list(DOMAINS.keys())
    matrix = np.full((len(INSTRUMENTS), len(domains)), np.nan)
    lookup = {(r["instrument"], r["domain"]): r for r in records}
    for i, inst in enumerate(INSTRUMENTS):
        for j, dom in enumerate(domains):
            rec = lookup.get((inst, dom))
            if rec is not None and rec.get("member") and rec.get(key) is not None:
                matrix[i, j] = float(rec[key])
    return matrix


def plot_fill_rate_heatmap(records: list[dict[str, Any]], save_path: Path) -> None:
    """Per-cell CONFIRM fill_rate heatmap (17x6)."""
    matrix = _cell_matrix(records, "fill_rate")
    fig, ax = plt.subplots(figsize=(7, 9))
    sns.heatmap(matrix, ax=ax, cmap="viridis", vmin=0.0, vmax=1.0, annot=True, fmt=".2f",
                xticklabels=list(DOMAINS.keys()), yticklabels=INSTRUMENTS,
                cbar_kws={"label": "fill_rate = n_fills / n_signals"}, annot_kws={"size": 6})
    ax.set_title(f"{EXPERIMENT_ID}: /CONFIRM fill rate by cell")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _box(ax: plt.Axes, series: list[tuple[str, list[float]]], ylabel: str, title: str) -> None:
    """Box plot of several per-cell value series."""
    data = [np.asarray([v for v in vals if v is not None], dtype=np.float64) for _, vals in series]
    data = [d[np.isfinite(d)] for d in data]
    ax.boxplot(data, labels=[name for name, _ in series], showfliers=False)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, axis="y", alpha=0.3)


def plot_lead(records: list[dict[str, Any]], save_path: Path) -> None:
    """Per-cell median lead (DIRECT vs CONFIRM) and time-to-fill box plot."""
    members = [r for r in records if r.get("member")]
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(8, 6))
    _box(ax, [("lead_direct", [r["lead_direct_med"] for r in members]),
              ("lead_confirm", [r["lead_confirm_med"] for r in members]),
              ("time_to_fill", [r["time_to_fill_med"] for r in members])],
         "bars", f"{EXPERIMENT_ID}: per-cell median lead & time-to-fill (DIRECT vs CONFIRM)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_outcome(records: list[dict[str, Any]], save_path: Path) -> None:
    """Per-cell median MFE/MAE (ATR units) by arm box plot."""
    members = [r for r in records if r.get("member")]
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(9, 6))
    _box(ax, [("DIRECT MFE", [r["direct_mfe_atr_med"] for r in members]),
              ("DIRECT MAE", [r["direct_mae_atr_med"] for r in members]),
              ("CONFIRM MFE", [r["confirm_mfe_atr_med"] for r in members]),
              ("CONFIRM MAE", [r["confirm_mae_atr_med"] for r in members])],
         "excursion / ATR(14) at entry",
         f"{EXPERIMENT_ID}: per-cell median MFE/MAE by arm (ATR units)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_shift_scatter(records: list[dict[str, Any]], readout: dict[str, Any],
                       save_path: Path) -> None:
    """Paired CONFIRM-DIRECT shift vs fill_rate, per reportable cell."""
    rep = [r for r in records if r.get("member") and r.get("paired_reportable")]
    colors = {"positive": "#1a9850", "negative": "#d73027", "flat": "#999999"}
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(8, 6))
    for sign in ("positive", "negative", "flat"):
        pts = [r for r in rep if r.get("shift_sign") == sign]
        if not pts:
            continue
        x = [r["fill_rate"] for r in pts]
        y = [r["paired_delta_mmm"] for r in pts]
        lo = [r["paired_delta_mmm"] - r["paired_delta_ci_low"] for r in pts]
        hi = [r["paired_delta_ci_high"] - r["paired_delta_mmm"] for r in pts]
        ax.errorbar(x, y, yerr=[lo, hi], fmt="o", color=colors[sign], label=sign,
                    alpha=0.8, capsize=2, markersize=5, elinewidth=0.8)
    ax.axhline(0.0, color="black", lw=1)
    ax.set_xlabel("fill_rate")
    ax.set_ylabel("paired delta median((MFE-MAE)/ATR), CONFIRM - DIRECT")
    ax.set_title(f"{EXPERIMENT_ID}: paired shift vs fill_rate "
                 f"(pos={readout['n_pos']}/{readout['n_pos_instruments']}i, "
                 f"neg={readout['n_neg']}/{readout['n_neg_instruments']}i; "
                 f"P11 pos={readout['p11_pos_readout']})")
    ax.legend()
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def make_plots(records: list[dict[str, Any]], readout: dict[str, Any]) -> None:
    """Render the four bounded plots from the collected per-cell summary."""
    plot_fill_rate_heatmap(records, PLOTS_DIR / "fill_rate_heatmap.png")
    plot_lead(records, PLOTS_DIR / "lead_direct_vs_confirm.png")
    plot_outcome(records, PLOTS_DIR / "mfe_mae_by_arm.png")
    plot_shift_scatter(records, readout, PLOTS_DIR / "paired_shift_vs_fillrate.png")


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #
def _flat_cell_row(r: dict[str, Any]) -> dict[str, Any]:
    """Flatten one per-cell record (nested secondary dicts -> prefixed columns)."""
    row = {k: v for k, v in r.items() if k not in ("secondary_direct", "secondary_confirm")}
    for arm in ("direct", "confirm"):
        sec = r.get(f"secondary_{arm}") or {}
        for k, v in sec.items():
            row[f"{arm}_r_{k}"] = v
    return row


def write_outputs(
    records: list[dict[str, Any]], verdict: dict[str, Any],
    readout: dict[str, Any], instrument_meta: dict[str, Any],
) -> None:
    """Persist the per-cell parquet, the CSV disclosures, and the JSON files."""
    rows = [_flat_cell_row(r) for r in records]
    df = pl.DataFrame(rows, strict=False)
    df.write_parquet(RESULTS_DIR / "per_cell_confirm.parquet")

    members = df.filter(pl.col("member"))

    primary_rows: list[dict[str, Any]] = []
    for r in records:
        if not r["member"]:
            continue
        for arm in ("direct", "confirm"):
            primary_rows.append({
                "instrument": r["instrument"], "domain": r["domain"], "arm": arm,
                "mfe_atr_med": r[f"{arm}_mfe_atr_med"], "mfe_atr_iqr": r[f"{arm}_mfe_atr_iqr"],
                "mae_atr_med": r[f"{arm}_mae_atr_med"], "mae_atr_iqr": r[f"{arm}_mae_atr_iqr"],
                "mmm_med": r[f"{arm}_mmm_med"], "mmm_ci_low": r[f"{arm}_mmm_ci_low"],
                "mmm_ci_high": r[f"{arm}_mmm_ci_high"], "n_used": r[f"n_{arm}_used"],
                "reportable": r[f"{arm}_reportable"]})
    pl.DataFrame(primary_rows, strict=False).write_csv(RESULTS_DIR / "outcome_primary.csv")

    sec_rows: list[dict[str, Any]] = []
    for r in records:
        if not r["member"]:
            continue
        for arm in ("direct", "confirm"):
            sec = r[f"secondary_{arm}"]
            sec_rows.append({"instrument": r["instrument"], "domain": r["domain"], "arm": arm,
                             **sec, "null_r": NULL_R})
    pl.DataFrame(sec_rows, strict=False).write_csv(RESULTS_DIR / "outcome_secondary_r.csv")

    members.select(
        "instrument", "domain", "n_signals", "n_fills", "fill_rate", "n_lead_defined",
        "lead_direct_med", "lead_direct_iqr", "lead_confirm_med", "lead_confirm_iqr",
        "time_to_fill_med", "time_to_fill_iqr").write_csv(RESULTS_DIR / "timing.csv")

    members.select(
        "instrument", "domain", "n_paired", "paired_reportable", "paired_delta_mmm",
        "paired_delta_ci_low1s", "paired_delta_ci_low", "paired_delta_ci_high",
        "shift_sign").write_csv(RESULTS_DIR / "comparison_readout.csv")

    members.select(
        "instrument", "domain", "n_haramis_total", "n_no_trend_context", "n_p4_warmup",
        "n_direct_censored", "n_confirm_censored", "n_degenerate_ref", "n_signals",
        "n_fills", "n_fills_noncensored").write_csv(RESULTS_DIR / "excluded_fractions.csv")

    with open(RESULTS_DIR / "composition_readout.json", "w") as fh:
        json.dump(readout, fh, indent=2, default=str)

    meta = {
        "experiment_id": EXPERIMENT_ID,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "014-A", "hypothesis": "HYP-005", "family": "CF-HA-HARAMI-001",
        "variant": "CF-HA-HARAMI-001/CONFIRM",
        "stratum": "TRAIN-only (first 49%); nested TEST + final-30% holdout sealed",
        "arms": {
            "DIRECT": "enter at harami signal bar; entry price = RealClose[signal]",
            "CONFIRM": ("stop at signal bar real extreme (RealHigh if rd=+1 else RealLow); "
                        "fills on first later bar trading through it within (s, "
                        "min(next_confirm-1, s+N_event)]; entry price = stop level"),
        },
        "reversal_direction": ("rd = Direction(most recent move ConfirmTime <= HA0Time); "
                               "+1 buy-stop bull reversal, -1 sell-stop bear reversal"),
        "outcome_primary": ("direction-signed MFE/MAE over [entry+1, entry+N_event] on real "
                            "High/Low, normalized by Wilder ATR(14) at entry; "
                            "median((MFE-MAE)/ATR) per arm"),
        "outcome_secondary": ("EXP-049 symmetric fav-before-adv r from each arm entry "
                              "(fav_dist=0.50*|preceding confirmed move|, 1:1 adverse); "
                              "reuse capture_barriers; NULL_R=0.50"),
        "comparison": ("paired median((MFE-MAE)/ATR) CONFIRM-DIRECT on events filled & "
                       "non-censored in both arms; MBB CI; NON-BINDING readout"),
        "params": {
            "atr_period": ATR_PERIOD, "atr_mult": ATR_MULT, "atr_estimator": "Wilder",
            "favourable_fraction": FAVOURABLE_FRACTION,
            "p4_cap": "max(6, round(1.5*median(trailing<=20 confirmed-move durations))); <5 warmup",
            "power_floor": POWER_FLOOR, "n_boot": N_BOOT, "base_seed": BASE_SEED,
            "boot_max_elems": BOOT_MAX_ELEMS, "p11": [P11_CELLS, P11_INSTRUMENTS],
            "ci_form": ("moving-block bootstrap, block=max(1,round(n**(1/3))), B=10000, "
                        "fixed per-(cell,statistic) seed; two-sided 95% (per-arm/paired), "
                        "one-sided 95% lower also recorded for paired; NON-BINDING"),
        },
        "denominators": {
            "n_signals": "qualifying haramis (defined rd, defined N_event, DIRECT non-censored)",
            "fill_rate": "n_fills / n_signals (n_fills=0 -> 0, never 0/0)",
            "outcome": "per arm over non-censored events; <30 -> NOT_REPORTABLE_BY_POWER",
            "secondary_r": "fav/(fav+adv) over resolved>=30; symmetric null 0.50",
            "paired": "median diff over events filled & non-censored in both arms; <30 -> not reportable",
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
            "ConfirmTime, HA0Time, fill trigger, and forward-window-end fenced to "
            "CloseTime <= train_end_ts; TEST and final-30% holdout never read."),
        "note": ("HYP-005 is descriptive: the verdict is delivery, not 'confirmation "
                 "helps'. The P11 shift readout is mechanical and NON-BINDING; any 014-B "
                 "routing is checkpoint desk work, not self-declared here."),
    }
    with open(RESULTS_DIR / "run_metadata.json", "w") as fh:
        json.dump(meta, fh, indent=2, default=str)


def _summarize(
    records: list[dict[str, Any]], verdict: dict[str, Any], readout: dict[str, Any],
) -> dict[str, Any]:
    """Concise stdout summary."""
    members = [r for r in records if r["member"]]
    return {
        "verdict": verdict["verdict"],
        "n_member_cells": len(members),
        "non_deterministic_cells": verdict["non_deterministic_cells"],
        "systematic_invariant_failures": verdict["systematic_invariant_failures"],
        "fill_rate_median": readout["fill_rate_summary"]["median"],
        "n_paired_reportable": readout["n_reportable"],
        "shift_pos": f"{readout['n_pos']} cells / {readout['n_pos_instruments']} instruments",
        "shift_neg": f"{readout['n_neg']} cells / {readout['n_neg_instruments']} instruments",
        "p11_pos_readout": readout["p11_pos_readout"],
        "p11_neg_readout": readout["p11_neg_readout"],
    }


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
        members = [d for d in DOMAINS if membership.get((instrument, d)) in MEMBER_STATUSES]
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
    make_plots(records, readout)
    return _summarize(records, verdict, readout)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    summary = run()
    LOGGER.info("\n=== %s complete ===", EXPERIMENT_ID)
    LOGGER.info("verdict: %s", summary["verdict"])
    LOGGER.info("member cells: %s", summary["n_member_cells"])
    LOGGER.info("median fill_rate: %s", summary["fill_rate_median"])
    LOGGER.info("paired-reportable cells: %s", summary["n_paired_reportable"])
    LOGGER.info("positive shift: %s (P11=%s)", summary["shift_pos"], summary["p11_pos_readout"])
    LOGGER.info("negative shift: %s (P11=%s)", summary["shift_neg"], summary["p11_neg_readout"])
    if summary["non_deterministic_cells"]:
        LOGGER.info("NON-DETERMINISTIC: %s", summary["non_deterministic_cells"])
    if summary["systematic_invariant_failures"]:
        LOGGER.info("SYSTEMATIC INVARIANT FAILURES: %s",
                    json.dumps(summary["systematic_invariant_failures"]))
    LOGGER.info("artifacts -> %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
