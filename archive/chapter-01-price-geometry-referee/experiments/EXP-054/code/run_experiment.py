"""EXP-054 — Intrabar Fill-Model Correction (benchmark capture re-read vs EXP-049).

`CF-HA-HARAMI-001` / HYP-007 (Phase 014-B, Lead 2). TRAIN-only, gross,
exit-agnostic; 0 candidate slots, 0 TEST reads. This script re-reads the **exact
EXP-049 benchmark** (every confirmed ZigZag trend-change as one capture event,
P1-P5 benchmark barriers, the 99-cell member grid) and resolves each event
**twice in one pass** on real OHLC:

1. the EXP-049 **worst-case** same-bar tie-break (double-touch -> ADVERSE),
   reproduced for an apples-to-apples reconciliation; and
2. the **P15 path-ordered** intrabar fill model (bullish bar `Close >= Open`:
   `Open->Low->High->Close`; bearish bar: `Open->High->Low->Close`).

For each EXP-048-READY cell, on the TRAIN analysis stratum only, it: slices the
first-49% (TRAIN) 1-minute rows by the F01 file-order prefix (TEST and the
final-30% global holdout are never read); aggregates the domain (5m strict;
15m/30m/1h/2h/4h at min_coverage=0.90), fenced to `CloseTime <= train_end_ts`;
runs the frozen Wilder-ATR ZigZag substrate and builds the benchmark 3-barrier
system (both geometries G1/G2) with `xen.capture_barriers`; resolves the forward
window under both fill rules; estimates `r = FAV/(FAV+ADV)` and its
regime-clustered moving-block bootstrap CI per rule (`xen.capture_barriers`);
discloses the P14 **median per-event gross ATR-normalised expectancy** under both
rules (`xen.expectancy`); reconciles the worst-case leg against
`EXP-049/results/per_cell_capture.parquet`; checks monotonicity (`r_P15 >=
r_EXP049` by construction) and runs a determinism replay.

The only change from EXP-049 is the same-bar resolution rule; everything else is
byte-identical machinery. Outputs (results/): per_cell_fill_compare.parquet,
fill_compare_map.csv (G1), fill_compare_secondary.csv (G2),
expectancy_dual_fill.csv, reconciliation.csv, composition_readout.json,
run_metadata.json. Plots (plots/): delta-r heatmap, same-bar double-touch
fraction heatmap, P15 viability-status heatmap (TIE_BREAK_SENSITIVE marked), and
the paired EXP-049-vs-P15 r scatter. Real prices throughout; no HA price enters
any metric (the harami detector is not used in EXP-054).
"""
from __future__ import annotations

import json
import logging
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
EXP049_PER_CELL = (
    PROJECT_ROOT / "python" / "experiments" / "EXP-049" / "results" / "per_cell_capture.parquet"
)

from xen.bar_aggregator import aggregate_ohlc  # noqa: E402
from xen.capture_barriers import (  # noqa: E402
    CLASS_ADV,
    CLASS_FAV,
    CLASS_TIMECAP,
    GeometryResult,
    build_barriers,
    confirm_indices,
    resolve_first_touch,
    summarize_geometry,
    time_caps,
    viable_status,
)
from xen.expectancy import (  # noqa: E402
    bootstrap_median_distribution,
    median_ci,
    qualifying_mask,
    realised_returns,
    resolve_path_ordered,
)
from xen.zigzag import generate_zigzag  # noqa: E402

# --------------------------------------------------------------------------- #
# Constants (Phase 014 D0 + 014-B P14/P15 frozen; conventions identical to EXP-049)
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-054"
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
MEMBER_STATUSES = ("READY", "READY_FLAGGED")
BASE_SEED = 20260614       # frozen bootstrap seed (identical to EXP-049; no tuning)
GEOM_G1, GEOM_G2 = 1, 2
P15_STREAM = 15            # P15 leg RNG tag (independent of the worst-case leg)
EXP_STREAM = 99            # expectancy RNG tag; per-rule sub-tag below
RULE_WC, RULE_P15 = 0, 15  # expectancy per-rule RNG sub-tags
RESOLVED_FLOOR = 30        # P12: minimum resolved/qualifying events to report
TIE_BREAK_DELTA = 0.05     # per-cell TIE_BREAK_SENSITIVE gradation on delta_r
COMPOSE_CELLS, COMPOSE_INSTRUMENTS = 5, 3  # P11 composition (>=5 cells, >=3 instruments)
RECON_TOL = 1e-12          # float reconciliation tolerance (expect exact match)
EXCLUDED_FILE_MARKERS = ("analysis70", "analysis_slice", "first70")
DE30_DISCLOSURE = (
    "DE30 truncated history: broker m1 history ends 2026-01-16; counts/rates "
    "derive from its own realized timeline and are not span-comparable (VAL-003)."
)
# Holdout-safe tripwire for the disclosure above: the broker-end date is the end
# of DE30's *full* file, which lies inside the sealed final-30% global holdout and
# cannot be read directly. The necessary, holdout-safe condition we *can* assert
# is that DE30's TRAIN edge (first 49%) falls strictly before this date; if a data
# refresh pushes TRAIN past it, the disclosure is stale and we warn loudly.
DE30_BROKER_END_EPOCH = int(datetime(2026, 1, 16, tzinfo=timezone.utc).timestamp())
# F04 disclosure: P15 path order presumes session-based microstructure.
CONTINUOUS_MARKET_INSTRUMENTS = ("BTCUSD",)
SESSION_MODEL_CAVEAT = (
    "P15 path order (bullish O->L->H->C; bearish O->H->L->C) presumes session-based "
    "microstructure (auction open -> continuous trading -> close). For 24/7 "
    f"instruments {list(CONTINUOUS_MARKET_INSTRUMENTS)} bar Open/Close are arbitrary "
    "1-minute boundaries, not session prints, so the path-order premise has lower "
    "fidelity; treat such cells as method-characterisation, not a realistic intrabar "
    "estimate of actual fills."
)
P15_APPROXIMATION_NOTE = (
    "P15 path-ordered fills are a documented approximation of unobserved intrabar "
    "motion (1-minute base bars are not replayed inside the domain bar). The "
    "same-bar double-touch fraction (dt_frac) bounds the maximum possible delta_r."
)
# Viability status -> integer code (for heatmaps; EXCLUDED for non-members).
VSTATUS_CODES: dict[str, int] = {
    "VIABLE": 0, "BELOW_R": 1, "CI_SPANS_050": 2,
    "NOT_VIABLE_BY_POWER": 3, "EXCLUDED": 4,
}
VSTATUS_COLORS: list[str] = ["#1a9850", "#fee08b", "#f46d43", "#cccccc", "#7b3294"]
INVARIANT_NAMES: list[str] = [
    "inv_causality", "inv_nevent_floor", "inv_nan_barrier",
    "inv_window_fence", "inv_g1_favdist",
]
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
    if not train.get_column("CloseTime").is_sorted():
        raise RuntimeError(f"{instrument}: TRAIN slice not chronological by CloseTime")
    meta = {
        "source_file": path.name, "total_rows_1m": total_rows,
        "analysis_rows_1m": analysis_rows, "train_rows_1m": train_rows,
        "train_end_ts": str(train.get_column("CloseTime")[-1]),
        "train_end_epoch_s": int(train.get_column("CloseTime").dt.epoch("s")[-1]),
    }
    return train, meta


def verify_de30_disclosure(meta: dict[str, Any]) -> None:
    """Holdout-safe staleness tripwire for the DE30 truncated-history disclosure.

    Records the observed (TRAIN-edge) timestamp next to the static claim and warns
    if DE30's TRAIN edge already reaches/exceeds the claimed broker-history end
    (impossible while the claim holds, since TRAIN ends strictly before the full
    file). Does not read the holdout: the full-file end is sealed.
    """
    if meta["train_end_epoch_s"] >= DE30_BROKER_END_EPOCH:
        LOGGER.warning(
            "DE30 disclosure STALE: TRAIN edge %s reaches/exceeds the claimed broker "
            "history end 2026-01-16; refresh DE30_DISCLOSURE (the full-file end lies in "
            "the sealed holdout and cannot be read directly).", meta["train_end_ts"])
        meta["de30_disclosure_stale"] = True
    else:
        meta["de30_disclosure_stale"] = False
    meta["de30_disclosure_train_edge"] = meta["train_end_ts"]


def load_membership() -> dict[tuple[str, str], str]:
    """Map (instrument, domain) -> EXP-048 readiness status."""
    if not READINESS_MAP.exists():
        raise FileNotFoundError(
            f"EXP-048 readiness map not found at {READINESS_MAP}; EXP-054 inherits the "
            "EXP-049 member grid, which is gated on EXP-048 READINESS_DELIVERED."
        )
    rows = pl.read_csv(READINESS_MAP).select("instrument", "domain", "status").to_dicts()
    return {(r["instrument"], r["domain"]): r["status"] for r in rows}


def load_exp049_baseline() -> dict[tuple[str, str], dict[str, Any]]:
    """Load EXP-049 per-cell capture for the reconciliation gate (fixed anchor)."""
    if not EXP049_PER_CELL.exists():
        raise FileNotFoundError(
            f"EXP-049 per_cell_capture.parquet not found at {EXP049_PER_CELL}; EXP-054 "
            "reconciles its worst-case leg against EXP-049 (CAPTURE_READINESS_DELIVERED)."
        )
    keep = [
        "instrument", "domain", "member", "g1_viable_status",
        "g1_fav", "g1_adv", "g1_resolved", "g1_r", "g1_ci_low_1s", "g1_ci_lo_2s", "g1_ci_hi_2s",
        "g2_fav", "g2_adv", "g2_resolved", "g2_r", "g2_ci_low_1s", "g2_ci_lo_2s", "g2_ci_hi_2s",
    ]
    df = pl.read_parquet(EXP049_PER_CELL).select(keep)
    return {(r["instrument"], r["domain"]): r for r in df.to_dicts()}


# --------------------------------------------------------------------------- #
# Pure computation — orchestration-local helpers (scope-allowed, bounded)
# --------------------------------------------------------------------------- #
def worstcase_exit_prices(
    classes_wc: np.ndarray, fav_target: np.ndarray, adv_target: np.ndarray,
    confirm_idx: np.ndarray, n_event: np.ndarray, close: np.ndarray, n_bars: int,
) -> np.ndarray:
    """Exit price per event for the worst-case leg under the P15 fill convention.

    Maps the worst-case class array to exit levels so the worst-case expectancy
    leg uses the identical fill convention as P15: ``FAV -> fav_target``,
    ``ADV -> adv_target``, ``TIMECAP -> close`` at the cap bar
    ``min(confirm_idx + N, n_bars - 1)``, ``DATA_CENSORED -> NaN``. A pure
    per-event lookup (no sequential dependence), so it is vectorized safely.
    """
    exit_price = np.full(classes_wc.shape[0], np.nan, dtype=np.float64)
    exit_price = np.where(classes_wc == CLASS_FAV, fav_target, exit_price)
    exit_price = np.where(classes_wc == CLASS_ADV, adv_target, exit_price)
    is_timecap = classes_wc == CLASS_TIMECAP
    if is_timecap.any():
        cap_end = np.minimum(confirm_idx + n_event, n_bars - 1)
        exit_price[is_timecap] = close[cap_end[is_timecap]]
    return exit_price


def first_touch_tie_flags(
    open_: np.ndarray, high: np.ndarray, low: np.ndarray, close: np.ndarray,
    confirm_idx: np.ndarray, fav_target: np.ndarray, adv_target: np.ndarray,
    rd: np.ndarray, n_event: np.ndarray, defined: np.ndarray, n_bars: int,
) -> np.ndarray:
    """Per-event diagnostic: ``True`` iff the resolving (first-hit) bar was a
    same-bar fav-and-adv double-touch.

    Diagnostic only — it does NOT decide outcomes (the resolvers already did). It
    is a bounded causal scan over each event's forward window (a few hundred
    events per cell), kept explicit because the first-hit bar is genuinely
    sequential. ``close`` is unused here but kept in the signature for symmetry
    with the resolvers (audit cross-check: ``was_tie ⟹ event resolved``).
    """
    flags = np.zeros(confirm_idx.shape[0], dtype=bool)
    for e in range(confirm_idx.shape[0]):
        if not defined[e]:
            continue
        start = int(confirm_idx[e]) + 1
        end = min(int(confirm_idx[e]) + int(n_event[e]), n_bars - 1)
        ft, at, r = float(fav_target[e]), float(adv_target[e]), int(rd[e])
        flags[e] = _scan_tie(high, low, start, end, ft, at, r)
    return flags


def _scan_tie(
    high: np.ndarray, low: np.ndarray, start: int, end: int,
    fav_t: float, adv_t: float, rd: int,
) -> bool:
    """Bounded sequential scan: was the first bar with any hit a double-touch?"""
    for i in range(start, end + 1):
        if rd == 1:
            fav_hit, adv_hit = high[i] >= fav_t, low[i] <= adv_t
        else:
            fav_hit, adv_hit = low[i] <= fav_t, high[i] >= adv_t
        if fav_hit or adv_hit:
            return bool(fav_hit and adv_hit)
    return False


def cell_expectancy(
    classes: np.ndarray, exit_price: np.ndarray, entry_close: np.ndarray,
    rd: np.ndarray, atr_entry: np.ndarray, rng: np.random.Generator,
) -> dict[str, Any]:
    """P14 median per-event gross ATR-normalised expectancy over qualifying events.

    Qualifying = built-barrier FAV/ADV/TIMECAP with finite exit and positive ATR
    (:func:`xen.expectancy.qualifying_mask`). Fewer than ``RESOLVED_FLOOR``
    qualifying events -> NOT_VIABLE-by-power (``e_median = None``). The median is
    binding (P14); the mean is a disclosed secondary.
    """
    rets = realised_returns(classes, exit_price, entry_close, rd, atr_entry)
    mask = qualifying_mask(classes, exit_price, atr_entry)
    q = rets[mask]
    n_qual = int(q.shape[0])
    if n_qual < RESOLVED_FLOOR:
        return {"n_qual": n_qual, "e_median": None, "e_mean": None,
                "e_ci_low_1s": None, "e_ci_lo_2s": None, "e_ci_hi_2s": None}
    dist, _ = bootstrap_median_distribution(q, rng)
    lo1, lo2, hi2 = median_ci(dist)
    return {"n_qual": n_qual, "e_median": float(np.median(q)), "e_mean": float(np.mean(q)),
            "e_ci_low_1s": lo1, "e_ci_lo_2s": lo2, "e_ci_hi_2s": hi2}


# --------------------------------------------------------------------------- #
# Pure computation — per-cell dual-fill capture core
# --------------------------------------------------------------------------- #
def build_domain(
    train_1m: pl.DataFrame, period_minutes: int, min_coverage: float | None,
    train_end_epoch: int,
) -> pl.DataFrame:
    """Aggregate one domain on the TRAIN slice and fence to the TRAIN edge."""
    bars = aggregate_ohlc(train_1m, period_minutes=period_minutes, min_coverage=min_coverage)
    return bars.filter(pl.col("CloseTime").dt.epoch("s") <= train_end_epoch)


def _cell_rng(*key: int) -> np.random.Generator:
    """Deterministic, independent per-cell RNG from a documented integer key."""
    return np.random.default_rng([BASE_SEED, *key])


def _resolve_geometry(
    ohlc: dict[str, np.ndarray], confirm_idx: np.ndarray, fav: np.ndarray,
    adv: np.ndarray, rd: np.ndarray, n_event: np.ndarray, defined: np.ndarray,
    n_bars: int, cell_index: int, geom_id: int,
) -> dict[str, Any]:
    """Resolve one geometry under both fill rules + tie diagnostics + stats."""
    cls_wc = resolve_first_touch(ohlc["high"], ohlc["low"], confirm_idx, fav, adv,
                                 rd, n_event, defined, n_bars)
    cls_p15, exit_p15 = resolve_path_ordered(ohlc["open"], ohlc["high"], ohlc["low"],
                                             ohlc["close"], confirm_idx, fav, adv, rd,
                                             n_event, defined, n_bars)
    was_tie = first_touch_tie_flags(ohlc["open"], ohlc["high"], ohlc["low"], ohlc["close"],
                                    confirm_idx, fav, adv, rd, n_event, defined, n_bars)
    exit_wc = worstcase_exit_prices(cls_wc, fav, adv, confirm_idx, n_event,
                                    ohlc["close"], n_bars)
    g_wc = summarize_geometry(cls_wc, defined, _cell_rng(cell_index, geom_id))
    g_p15 = summarize_geometry(cls_p15, defined, _cell_rng(cell_index, geom_id, P15_STREAM))
    cw, cp, wt = cls_wc[defined], cls_p15[defined], was_tie[defined]
    reassigned = int(((cw == CLASS_ADV) & (cp == CLASS_FAV)).sum())
    mismatch = int((cw != cp).sum())
    # Monotonicity / correctness invariants (all must hold; else METHOD_DEFECT):
    delta_r = ((g_p15.r - g_wc.r) if (g_wc.r is not None and g_p15.r is not None) else None)
    mono_ok = (
        g_p15.resolved == g_wc.resolved
        and g_p15.fav >= g_wc.fav
        and (delta_r is None or delta_r >= -RECON_TOL)
        and mismatch == reassigned
        and bool(np.all(~(cw != cp) | wt))          # reassigned set ⊆ tie set
    )
    return {
        "wc": g_wc, "p15": g_p15, "exit_wc": exit_wc, "exit_p15": exit_p15,
        "cls_wc": cls_wc, "cls_p15": cls_p15, "was_tie": was_tie,
        "dt_count": int(wt.sum()), "reassigned": reassigned, "delta_r": delta_r,
        "mono_ok": mono_ok,
    }


def compute_core(
    train_1m: pl.DataFrame, period_minutes: int, min_coverage: float | None,
    train_end_epoch: int, cell_index: int,
) -> dict[str, Any]:
    """Build the domain, ZigZag moves, both-geometry barriers, and dual-fill stats.

    Pure given identical inputs/seeds. Resolves each geometry under BOTH the
    worst-case tie-break (reconciliation leg) and the P15 path-ordered model
    (experimental leg) in one window pass, and discloses the G1 median expectancy
    under both rules.
    """
    bars = build_domain(train_1m, period_minutes, min_coverage, train_end_epoch)
    n_bars = bars.height
    moves = generate_zigzag(bars, atr_period=ATR_PERIOD, atr_mult=ATR_MULT)
    if moves.height == 0:
        return _empty_core(bars, n_bars)

    confirm_idx = confirm_indices(moves, bars)
    confirm_close = moves.get_column("ConfirmClose").to_numpy().astype(np.float64)
    atr_entry = moves.get_column("ATRAtConfirm").to_numpy().astype(np.float64)
    ohlc = {
        "open": bars.get_column("Open").to_numpy().astype(np.float64),
        "high": bars.get_column("High").to_numpy().astype(np.float64),
        "low": bars.get_column("Low").to_numpy().astype(np.float64),
        "close": bars.get_column("Close").to_numpy().astype(np.float64),
    }
    n_event, warmup = time_caps(confirm_idx)
    bar = build_barriers(moves, confirm_close)
    g1_defined = (~warmup) & (~bar["m0"])
    g2_defined = g1_defined & (~bar["g2_degenerate"])

    g1 = _resolve_geometry(ohlc, confirm_idx, bar["g1_fav"], bar["g1_adv"], bar["rd"],
                           n_event, g1_defined, n_bars, cell_index, GEOM_G1)
    g2 = _resolve_geometry(ohlc, confirm_idx, bar["g2_fav"], bar["g2_adv"], bar["rd"],
                           n_event, g2_defined, n_bars, cell_index, GEOM_G2)

    # P14 median expectancy on the binding G1 geometry, both fill rules.
    rng_wc = _cell_rng(cell_index, GEOM_G1, EXP_STREAM, RULE_WC)
    rng_p15 = _cell_rng(cell_index, GEOM_G1, EXP_STREAM, RULE_P15)
    g1["expect_wc"] = cell_expectancy(g1["cls_wc"], g1["exit_wc"], confirm_close,
                                      bar["rd"], atr_entry, rng_wc)
    g1["expect_p15"] = cell_expectancy(g1["cls_p15"], g1["exit_p15"], confirm_close,
                                       bar["rd"], atr_entry, rng_p15)

    invariants = _invariants(confirm_idx, n_event, warmup, bar, g1_defined,
                             bars, train_end_epoch, n_bars)
    median_cap = (float(np.median(n_event[~warmup])) if (~warmup).any() else None)
    return {"bars": bars, "n_bars": n_bars, "n_moves": int(moves.height),
            "g1": g1, "g2": g2, "invariants": invariants,
            "m0_excluded": int(bar["m0"].sum()), "warmup_excluded": int(warmup.sum()),
            "g2_degenerate_excluded": int((g1_defined & bar["g2_degenerate"]).sum()),
            "n_event_median": median_cap}


def _empty_geometry_dual() -> dict[str, Any]:
    """Zero-event dual-fill geometry (cells with no confirmed move)."""
    eg = _empty_geometry()
    z = np.empty(0, dtype=np.int64)
    return {"wc": eg, "p15": eg, "exit_wc": np.empty(0), "exit_p15": np.empty(0),
            "cls_wc": z, "cls_p15": z, "was_tie": np.empty(0, dtype=bool),
            "dt_count": 0, "reassigned": 0, "delta_r": None, "mono_ok": True,
            "expect_wc": {"n_qual": 0, "e_median": None, "e_mean": None,
                          "e_ci_low_1s": None, "e_ci_lo_2s": None, "e_ci_hi_2s": None},
            "expect_p15": {"n_qual": 0, "e_median": None, "e_mean": None,
                           "e_ci_low_1s": None, "e_ci_lo_2s": None, "e_ci_hi_2s": None}}


def _empty_core(bars: pl.DataFrame, n_bars: int) -> dict[str, Any]:
    """A zero-move core record."""
    return {"bars": bars, "n_bars": n_bars, "n_moves": 0,
            "g1": _empty_geometry_dual(), "g2": _empty_geometry_dual(),
            "invariants": {k: 0 for k in INVARIANT_NAMES},
            "m0_excluded": 0, "warmup_excluded": 0,
            "g2_degenerate_excluded": 0, "n_event_median": None}


def _invariants(
    confirm_idx: np.ndarray, n_event: np.ndarray, warmup: np.ndarray,
    bar: dict[str, np.ndarray], g1_defined: np.ndarray, bars: pl.DataFrame,
    train_end_epoch: int, n_bars: int,
) -> dict[str, int]:
    """Barrier-construction causality / fence invariant counts (all must be 0).

    Identical to EXP-049 (barriers are byte-identical); re-confirms the harness.
    """
    diffs = np.diff(confirm_idx)
    fence = int((bars.get_column("CloseTime").dt.epoch("s") > train_end_epoch).sum())
    nan_barrier = (
        np.isnan(bar["g1_fav"][g1_defined]).sum()
        + np.isnan(bar["g1_adv"][g1_defined]).sum()
        + np.isnan(bar["g2_fav"][g1_defined]).sum()
        + np.isnan(bar["g2_adv"][g1_defined]).sum()
    )
    nevent_bad = (n_event[~warmup] < 6).sum() + (n_event[warmup] != 0).sum()
    return {
        "inv_causality": int((diffs <= 0).sum()),
        "inv_nevent_floor": int(nevent_bad),
        "inv_nan_barrier": int(nan_barrier),
        "inv_window_fence": fence,
        "inv_g1_favdist": int((bar["m"][g1_defined] <= 0.0).sum()),
    }


def _empty_geometry() -> GeometryResult:
    """A zero-event GeometryResult (cells with no confirmed move)."""
    return GeometryResult(
        classes=np.empty(0, dtype=np.int64), defined=0, fav=0, adv=0, timecap=0,
        data_censored=0, resolved=0, r=None, ci_low_1s=None, ci_lo_2s=None,
        ci_hi_2s=None, boot_degenerate_frac=0.0, block_len=1)


def cores_equal(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """Frame-identical determinism comparison of two compute_core passes."""
    if not a["bars"].equals(b["bars"]):
        return False
    if a["n_moves"] != b["n_moves"] or a["invariants"] != b["invariants"]:
        return False
    for key in ("g1", "g2"):
        if not _geom_equal(a[key], b[key]):
            return False
    return _expect_equal(a["g1"]["expect_wc"], b["g1"]["expect_wc"]) and \
        _expect_equal(a["g1"]["expect_p15"], b["g1"]["expect_p15"])


def _geom_equal(ga: dict[str, Any], gb: dict[str, Any]) -> bool:
    """Compare two dual-fill geometry dicts frame-identically."""
    if not (np.array_equal(ga["cls_wc"], gb["cls_wc"])
            and np.array_equal(ga["cls_p15"], gb["cls_p15"])
            and np.array_equal(ga["was_tie"], gb["was_tie"])
            and np.array_equal(ga["exit_wc"], gb["exit_wc"], equal_nan=True)
            and np.array_equal(ga["exit_p15"], gb["exit_p15"], equal_nan=True)):
        return False
    if (ga["dt_count"], ga["reassigned"]) != (gb["dt_count"], gb["reassigned"]):
        return False
    for leg in ("wc", "p15"):
        x, y = ga[leg], gb[leg]
        if (x.r, x.ci_low_1s, x.ci_lo_2s, x.ci_hi_2s, x.resolved, x.fav, x.adv,
                x.boot_degenerate_frac, x.block_len) != (
                y.r, y.ci_low_1s, y.ci_lo_2s, y.ci_hi_2s, y.resolved, y.fav, y.adv,
                y.boot_degenerate_frac, y.block_len):
            return False
    return True


def _expect_equal(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """Compare two expectancy dicts frame-identically."""
    return all(a[k] == b[k] or (a[k] is None and b[k] is None) for k in a)


# --------------------------------------------------------------------------- #
# Per-cell orchestration & record assembly
# --------------------------------------------------------------------------- #
def process_member_cell(
    instrument: str, domain: str, status_048: str, train_1m: pl.DataFrame,
    train_end_epoch: int, cell_index: int,
) -> dict[str, Any]:
    """Process one member cell: dual-fill capture core + determinism replay."""
    period_minutes, min_coverage = DOMAINS[domain]
    core1 = compute_core(train_1m, period_minutes, min_coverage, train_end_epoch, cell_index)
    core2 = compute_core(train_1m, period_minutes, min_coverage, train_end_epoch, cell_index)
    determinism_ok = cores_equal(core1, core2)

    rec: dict[str, Any] = {
        "instrument": instrument, "domain": domain, "exp048_status": status_048,
        "member": True, "n_bars": core1["n_bars"], "n_moves": core1["n_moves"],
        "m0_excluded": core1["m0_excluded"], "warmup_excluded": core1["warmup_excluded"],
        "g2_degenerate_excluded": core1["g2_degenerate_excluded"],
        "n_event_median": core1["n_event_median"],
        "determinism_ok": determinism_ok,
        "monotonicity_ok": core1["g1"]["mono_ok"] and core1["g2"]["mono_ok"],
        **core1["invariants"],
    }
    rec.update(_dual_geometry_fields(core1["g1"], "g1"))
    rec.update(_dual_geometry_fields(core1["g2"], "g2"))
    rec["g1_status_code_p15"] = VSTATUS_CODES[rec["g1_viable_status_p15"]]
    g2_candidates = rec["g2_defined"] + rec["g2_degenerate_excluded"]
    rec["g2_degenerate_frac"] = (
        rec["g2_degenerate_excluded"] / g2_candidates if g2_candidates else None)
    rec.update(_expectancy_fields(core1["g1"]))
    return rec


def _dual_geometry_fields(g: dict[str, Any], prefix: str) -> dict[str, Any]:
    """Flatten one dual-fill geometry into per-cell record columns."""
    gwc, gp15 = g["wc"], g["p15"]
    resolved = gwc.resolved                          # == gp15.resolved by construction
    delta_r = g["delta_r"]
    dt_frac = (g["dt_count"] / resolved) if resolved > 0 else None
    reassigned_frac = (g["reassigned"] / resolved) if resolved > 0 else None
    swc, sp15 = viable_status(gwc), viable_status(gp15)
    sensitive = (swc != "VIABLE" and sp15 == "VIABLE") or (
        delta_r is not None and delta_r >= TIE_BREAK_DELTA)
    return {
        f"{prefix}_defined": gwc.defined, f"{prefix}_resolved": resolved,
        f"{prefix}_fav_wc": gwc.fav, f"{prefix}_adv_wc": gwc.adv, f"{prefix}_r_wc": gwc.r,
        f"{prefix}_ci_low_1s_wc": gwc.ci_low_1s, f"{prefix}_ci_lo_2s_wc": gwc.ci_lo_2s,
        f"{prefix}_ci_hi_2s_wc": gwc.ci_hi_2s, f"{prefix}_viable_status_wc": swc,
        f"{prefix}_fav_p15": gp15.fav, f"{prefix}_adv_p15": gp15.adv, f"{prefix}_r_p15": gp15.r,
        f"{prefix}_ci_low_1s_p15": gp15.ci_low_1s, f"{prefix}_ci_lo_2s_p15": gp15.ci_lo_2s,
        f"{prefix}_ci_hi_2s_p15": gp15.ci_hi_2s, f"{prefix}_viable_status_p15": sp15,
        f"{prefix}_delta_r": delta_r,
        f"{prefix}_dt_count": g["dt_count"], f"{prefix}_dt_frac": dt_frac,
        f"{prefix}_reassigned": g["reassigned"], f"{prefix}_reassigned_frac": reassigned_frac,
        f"{prefix}_tie_break_sensitive": sensitive,
        f"{prefix}_timecap_wc": gwc.timecap, f"{prefix}_datacensored_wc": gwc.data_censored,
    }


def _expectancy_fields(g: dict[str, Any]) -> dict[str, Any]:
    """Flatten the G1 dual-rule median-expectancy disclosure."""
    ewc, ep15 = g["expect_wc"], g["expect_p15"]
    e_delta = (ep15["e_median"] - ewc["e_median"]
               if (ewc["e_median"] is not None and ep15["e_median"] is not None) else None)
    return {
        "e_n_qual": ewc["n_qual"],
        "e_median_wc": ewc["e_median"], "e_mean_wc": ewc["e_mean"],
        "e_ci_low_1s_wc": ewc["e_ci_low_1s"], "e_ci_lo_2s_wc": ewc["e_ci_lo_2s"],
        "e_ci_hi_2s_wc": ewc["e_ci_hi_2s"],
        "e_median_p15": ep15["e_median"], "e_mean_p15": ep15["e_mean"],
        "e_ci_low_1s_p15": ep15["e_ci_low_1s"], "e_ci_lo_2s_p15": ep15["e_ci_lo_2s"],
        "e_ci_hi_2s_p15": ep15["e_ci_hi_2s"], "e_delta_median": e_delta,
    }


def excluded_cell(instrument: str, domain: str, status_048: str) -> dict[str, Any]:
    """Record for a non-member (not EXP-048-READY) cell — unmeasured."""
    rec: dict[str, Any] = {
        "instrument": instrument, "domain": domain, "exp048_status": status_048,
        "member": False, "n_bars": None, "n_moves": None, "m0_excluded": None,
        "warmup_excluded": None, "g2_degenerate_excluded": None, "g2_degenerate_frac": None,
        "n_event_median": None, "determinism_ok": None, "monotonicity_ok": None,
        "g1_viable_status_p15": "EXCLUDED", "g1_status_code_p15": VSTATUS_CODES["EXCLUDED"],
        "g1_viable_status_wc": "EXCLUDED", "g2_viable_status_p15": "EXCLUDED",
        "g2_viable_status_wc": "EXCLUDED",
        "g1_tie_break_sensitive": False, "g2_tie_break_sensitive": False,
    }
    for name in INVARIANT_NAMES:
        rec[name] = None
    return rec


# --------------------------------------------------------------------------- #
# Reconciliation, verdict, composition, readout
# --------------------------------------------------------------------------- #
def reconcile(
    records: list[dict[str, Any]], baseline: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    """Per-cell reconciliation of the worst-case leg against EXP-049.

    Counts (FAV/ADV/resolved) must match exactly; r and CI bounds to within
    ``RECON_TOL``. Annotates each member record with ``recon_ok`` /
    ``recon_max_abs_diff`` and returns the per-cell reconciliation rows.
    """
    rows: list[dict[str, Any]] = []
    wc_int_keys = ["fav", "adv"]          # stored with the _wc fill-leg suffix
    shared_int_keys = ["resolved"]        # leg-invariant (no suffix in the record)
    float_keys = ["r", "ci_low_1s", "ci_lo_2s", "ci_hi_2s"]
    for rec in records:
        if not rec["member"]:
            continue
        base = baseline.get((rec["instrument"], rec["domain"]))
        if base is None:
            rec["recon_ok"], rec["recon_max_abs_diff"] = False, None
            rows.append({"instrument": rec["instrument"], "domain": rec["domain"],
                         "recon_ok": False, "max_abs_diff": None, "note": "missing in EXP-049"})
            continue
        int_match, float_match, max_diff = True, True, 0.0
        for geom in ("g1", "g2"):
            for k in wc_int_keys:
                if rec[f"{geom}_{k}_wc"] != base[f"{geom}_{k}"]:
                    int_match = False
            for k in shared_int_keys:
                if rec[f"{geom}_{k}"] != base[f"{geom}_{k}"]:
                    int_match = False
            for k in float_keys:
                d = _abs_diff(rec[f"{geom}_{k}_wc"], base[f"{geom}_{k}"])
                if d is None:                        # one None, the other not
                    float_match = False
                else:
                    max_diff = max(max_diff, d)
        ok = int_match and float_match and max_diff <= RECON_TOL
        rec["recon_ok"], rec["recon_max_abs_diff"] = ok, max_diff
        rows.append({"instrument": rec["instrument"], "domain": rec["domain"],
                     "recon_ok": ok, "counts_exact": int_match,
                     "floats_match": float_match, "max_abs_diff": max_diff})
    return rows


def _abs_diff(a: float | None, b: float | None) -> float | None:
    """Absolute difference; 0.0 if both None; None if exactly one is None."""
    if a is None and b is None:
        return 0.0
    if a is None or b is None:
        return None
    return abs(float(a) - float(b))


def compute_verdict(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Mechanical SUBSTRATE_METHOD_DEFECT rule.

    Defect iff: non-determinism on any cell; OR a reconciliation mismatch on any
    cell; OR a monotonicity violation on any cell; OR a causality/fence invariant
    on >= 3 instruments. Otherwise FILL_MODEL_CHARACTERISED.
    """
    members = [r for r in records if r["member"]]
    non_det = [_cell(r) for r in members if not r.get("determinism_ok", True)]
    recon_fail = [_cell(r) for r in members if not r.get("recon_ok", True)]
    mono_fail = [_cell(r) for r in members if not r.get("monotonicity_ok", True)]
    systematic: dict[str, int] = {}
    for name in INVARIANT_NAMES:
        instruments = {r["instrument"] for r in members if (r.get(name) or 0) > 0}
        if len(instruments) >= 3:
            systematic[name] = len(instruments)
    defect = bool(non_det or recon_fail or mono_fail or systematic)
    return {
        "verdict": "SUBSTRATE_METHOD_DEFECT" if defect else "FILL_MODEL_CHARACTERISED",
        "non_deterministic_cells": non_det,
        "reconciliation_failures": recon_fail,
        "monotonicity_failures": mono_fail,
        "systematic_invariant_failures": systematic,
    }


def _cell(rec: dict[str, Any]) -> str:
    return f"{rec['instrument']}-{rec['domain']}"


def composition_readout(
    records: list[dict[str, Any]], baseline: dict[tuple[str, str], dict[str, Any]],
    verdict: dict[str, Any],
) -> dict[str, Any]:
    """Material readout: P15 G1 composition vs the EXP-049 baseline (emitted, not
    adjudicated)."""
    members = [r for r in records if r["member"]]
    member_keys = {(r["instrument"], r["domain"]) for r in members}
    g1_p15 = _compose(members, "g1_viable_status_p15")
    g1_wc = _compose(members, "g1_viable_status_wc")
    # Baseline denominator must match the current member grid (frozen by scope);
    # filtering to current members enforces that assumption rather than trusting it.
    exp049_viable = sum(1 for key, b in baseline.items()
                        if key in member_keys and b["member"]
                        and b["g1_viable_status"] == "VIABLE")
    sensitive = [_cell(r) for r in members if r.get("g1_tie_break_sensitive")]
    no_defect = verdict["verdict"] == "FILL_MODEL_CHARACTERISED"
    material = no_defect and g1_p15["composition_met"]
    deltas = [r["g1_delta_r"] for r in members if r.get("g1_delta_r") is not None]
    dtf = [r["g1_dt_frac"] for r in members if r.get("g1_dt_frac") is not None]
    return {
        "material_classification": ("MATERIAL" if material else
                                    ("IMMATERIAL" if no_defect else "N/A — defect")),
        "g1_p15_composition": g1_p15,
        "g1_worstcase_composition": g1_wc,
        "exp049_baseline": {"n_viable": exp049_viable, "n_member_cells": len(members),
                            "source": "EXP-049/results/per_cell_capture.parquet"},
        "tie_break_sensitive_cells": sensitive,
        "n_tie_break_sensitive": len(sensitive),
        "g1_delta_r_median": (float(np.median(deltas)) if deltas else None),
        "g1_delta_r_iqr": (_iqr(deltas) if deltas else None),
        "g1_dt_frac_median": (float(np.median(dtf)) if dtf else None),
        "g1_dt_frac_iqr": (_iqr(dtf) if dtf else None),
        "g2_p15_composition": _compose(members, "g2_viable_status_p15"),
        "rule": (
            "TIE_BREAK_SENSITIVE iff (NOT_VIABLE_wc -> VIABLE_p15) OR delta_r>=0.05. "
            "MATERIAL iff P15 G1 meets P11 (>=5 VIABLE cells over >=3 instruments) "
            "where EXP-049 had 0/99. Routing (re-baseline vs adopt-P15) is the §8 "
            "G2-area desk adjudication, not self-declared here."),
        "approximation_note": P15_APPROXIMATION_NOTE,
    }


def _compose(members: list[dict[str, Any]], status_key: str) -> dict[str, Any]:
    viable = [r for r in members if r[status_key] == "VIABLE"]
    instruments = sorted({r["instrument"] for r in viable})
    return {
        "n_viable": len(viable), "n_instruments": len(instruments),
        "instruments": ";".join(instruments),
        "viable_cells": [_cell(r) for r in viable],
        "composition_met": len(viable) >= COMPOSE_CELLS and len(instruments) >= COMPOSE_INSTRUMENTS,
    }


def _iqr(values: list[float]) -> float:
    arr = np.asarray(values, dtype=np.float64)
    return float(np.percentile(arr, 75.0) - np.percentile(arr, 25.0))


# --------------------------------------------------------------------------- #
# Plotting (bounded; from the collected per-cell summary only)
# --------------------------------------------------------------------------- #
def _matrix(records: list[dict[str, Any]], value: str) -> np.ndarray:
    """instrument x domain matrix (NaN where missing/None) for heatmaps."""
    domains = list(DOMAINS.keys())
    matrix = np.full((len(INSTRUMENTS), len(domains)), np.nan)
    lookup = {(r["instrument"], r["domain"]): r.get(value) for r in records}
    for i, inst in enumerate(INSTRUMENTS):
        for j, dom in enumerate(domains):
            val = lookup.get((inst, dom))
            if val is not None:
                matrix[i, j] = float(val)
    return matrix


def plot_delta_r_heatmap(records: list[dict[str, Any]], save_path: Path) -> None:
    """Per-cell delta_r = r_P15 - r_EXP049 (G1); NaN for non-member/low-power."""
    matrix = _matrix(records, "g1_delta_r")
    fig, ax = plt.subplots(figsize=(7, 9))
    vmax = float(np.nanmax(np.abs(matrix))) if np.isfinite(matrix).any() else 0.05
    vmax = max(vmax, 1e-6)
    sns.heatmap(matrix, ax=ax, cmap="RdYlGn", center=0.0, vmin=-vmax, vmax=vmax,
                annot=True, fmt=".3f", xticklabels=list(DOMAINS.keys()),
                yticklabels=INSTRUMENTS, cbar_kws={"label": "delta_r = r_P15 - r_EXP049"},
                annot_kws={"size": 6})
    ax.set_title(f"{EXPERIMENT_ID}: G1 fill-rule effect on r (>=0 by construction)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_dt_frac_heatmap(records: list[dict[str, Any]], save_path: Path) -> None:
    """Per-cell same-bar double-touch fraction among resolved events (G1)."""
    matrix = _matrix(records, "g1_dt_frac")
    fig, ax = plt.subplots(figsize=(7, 9))
    sns.heatmap(matrix, ax=ax, cmap="viridis", vmin=0.0, annot=True, fmt=".3f",
                xticklabels=list(DOMAINS.keys()), yticklabels=INSTRUMENTS,
                cbar_kws={"label": "dt_frac = same-bar double-touch / resolved"},
                annot_kws={"size": 6})
    ax.set_title(f"{EXPERIMENT_ID}: G1 tie-rule exposure (dt_frac)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_p15_status_heatmap(records: list[dict[str, Any]], save_path: Path) -> None:
    """P15 G1 viability-status heatmap; TIE_BREAK_SENSITIVE cells annotated '*'."""
    matrix = _matrix(records, "g1_status_code_p15")
    cmap = ListedColormap(VSTATUS_COLORS)
    norm = BoundaryNorm(np.arange(-0.5, len(VSTATUS_COLORS) + 0.5), cmap.N)
    fig, ax = plt.subplots(figsize=(7, 9))
    ax.imshow(matrix, cmap=cmap, norm=norm, aspect="auto")
    sens = {(r["instrument"], r["domain"]) for r in records
            if r.get("g1_tie_break_sensitive")}
    domains = list(DOMAINS.keys())
    for i, inst in enumerate(INSTRUMENTS):
        for j, dom in enumerate(domains):
            if (inst, dom) in sens:
                ax.text(j, i, "*", ha="center", va="center", color="black", fontsize=12)
    ax.set_xticks(range(len(DOMAINS)), domains)
    ax.set_yticks(range(len(INSTRUMENTS)), INSTRUMENTS)
    ax.set_title(f"{EXPERIMENT_ID}: P15 G1 viability ('*' = TIE_BREAK_SENSITIVE)")
    handles = [plt.Rectangle((0, 0), 1, 1, color=VSTATUS_COLORS[c])
               for c in VSTATUS_CODES.values()]
    ax.legend(handles, list(VSTATUS_CODES.keys()), bbox_to_anchor=(1.02, 1),
              loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_paired_scatter(records: list[dict[str, Any]], save_path: Path) -> None:
    """Paired EXP-049 (worst-case) vs P15 r scatter, one point per member cell."""
    domains = list(DOMAINS.keys())
    palette = sns.color_palette("tab10", len(domains))
    fig, ax = plt.subplots(figsize=(7, 7))
    for j, dom in enumerate(domains):
        xs = [r["g1_r_wc"] for r in records
              if r["domain"] == dom and r.get("g1_r_wc") is not None
              and r.get("g1_r_p15") is not None]
        ys = [r["g1_r_p15"] for r in records
              if r["domain"] == dom and r.get("g1_r_wc") is not None
              and r.get("g1_r_p15") is not None]
        if xs:
            ax.scatter(xs, ys, s=28, color=palette[j], label=dom, alpha=0.8,
                       edgecolor="white", linewidth=0.4)
    ax.plot([0.0, 1.0], [0.0, 1.0], "k--", linewidth=0.8, label="y = x")
    for ref in (0.50, 0.55):
        ax.axvline(ref, color="grey", linewidth=0.5, linestyle=":")
        ax.axhline(ref, color="grey", linewidth=0.5, linestyle=":")
    ax.set_xlim(0.3, 0.75)
    ax.set_ylim(0.3, 0.75)
    ax.set_xlabel("r_EXP049 (worst-case tie-break)")
    ax.set_ylabel("r_P15 (path-ordered fills)")
    ax.set_title(f"{EXPERIMENT_ID}: per-cell r shift (worst-case -> P15)")
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def make_plots(records: list[dict[str, Any]]) -> None:
    """Render the four bounded plots from the collected per-cell summary."""
    plot_delta_r_heatmap(records, PLOTS_DIR / "g1_delta_r_heatmap.png")
    plot_dt_frac_heatmap(records, PLOTS_DIR / "g1_dt_frac_heatmap.png")
    plot_p15_status_heatmap(records, PLOTS_DIR / "g1_p15_viability_status_heatmap.png")
    plot_paired_scatter(records, PLOTS_DIR / "g1_paired_r_scatter.png")


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def run() -> dict[str, Any]:
    """Run all member cells and write artifacts. Returns run metadata summary."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    membership = load_membership()
    baseline = load_exp049_baseline()
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
        if instrument == "DE30":
            verify_de30_disclosure(meta)
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

    recon_rows = reconcile(records, baseline)
    verdict = compute_verdict(records)
    readout = composition_readout(records, baseline, verdict)
    write_outputs(records, recon_rows, verdict, readout, instrument_meta)
    make_plots(records)
    return _summarize(records, verdict, readout)


def write_outputs(
    records: list[dict[str, Any]], recon_rows: list[dict[str, Any]],
    verdict: dict[str, Any], readout: dict[str, Any], instrument_meta: dict[str, Any],
) -> None:
    """Persist the per-cell parquet, the CSVs, and the two JSON files."""
    df = pl.DataFrame(records, strict=False)
    df.write_parquet(RESULTS_DIR / "per_cell_fill_compare.parquet")

    g1_cols = ["instrument", "domain", "member", "exp048_status", "n_moves",
               "g1_defined", "g1_resolved", "g1_fav_wc", "g1_adv_wc", "g1_r_wc",
               "g1_ci_low_1s_wc", "g1_viable_status_wc", "g1_fav_p15", "g1_adv_p15",
               "g1_r_p15", "g1_ci_low_1s_p15", "g1_viable_status_p15", "g1_delta_r",
               "g1_dt_count", "g1_dt_frac", "g1_reassigned", "g1_reassigned_frac",
               "g1_tie_break_sensitive", "recon_ok", "recon_max_abs_diff",
               "determinism_ok", "monotonicity_ok"]
    _write_csv(df, g1_cols, RESULTS_DIR / "fill_compare_map.csv")

    g2_cols = ["instrument", "domain", "member", "g2_defined", "g2_degenerate_excluded",
               "g2_degenerate_frac", "g2_resolved", "g2_fav_wc", "g2_adv_wc", "g2_r_wc",
               "g2_viable_status_wc", "g2_fav_p15", "g2_adv_p15", "g2_r_p15",
               "g2_viable_status_p15", "g2_delta_r", "g2_dt_count", "g2_dt_frac",
               "g2_reassigned", "g2_tie_break_sensitive"]
    _write_csv(df, g2_cols, RESULTS_DIR / "fill_compare_secondary.csv")

    exp_cols = ["instrument", "domain", "member", "e_n_qual", "e_median_wc", "e_mean_wc",
                "e_ci_low_1s_wc", "e_ci_lo_2s_wc", "e_ci_hi_2s_wc", "e_median_p15",
                "e_mean_p15", "e_ci_low_1s_p15", "e_ci_lo_2s_p15", "e_ci_hi_2s_p15",
                "e_delta_median"]
    _write_csv(df, exp_cols, RESULTS_DIR / "expectancy_dual_fill.csv")

    pl.DataFrame(recon_rows, strict=False).write_csv(RESULTS_DIR / "reconciliation.csv")

    with open(RESULTS_DIR / "composition_readout.json", "w") as fh:
        json.dump(readout, fh, indent=2, default=str)

    _write_metadata(records, verdict, readout, instrument_meta)


def _write_csv(df: pl.DataFrame, cols: list[str], path: Path) -> None:
    """Project the requested columns (in order) and write a CSV.

    Fails loudly on schema drift: every requested column must exist in ``df``
    (the per-cell record union always carries them), so a missing column signals
    a rename or a dropped code path rather than an intended omission.
    """
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"{path.name}: requested columns absent from DataFrame: {missing}")
    df.select(cols).write_csv(path)


def _write_metadata(
    records: list[dict[str, Any]], verdict: dict[str, Any],
    readout: dict[str, Any], instrument_meta: dict[str, Any],
) -> None:
    """Write run_metadata.json (frozen constants, fences, source anchors)."""
    meta = {
        "experiment_id": EXPERIMENT_ID,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "014-B", "hypothesis": "HYP-007", "family": "CF-HA-HARAMI-001",
        "lead_role": "Lead 2 of the 014-B slate (intrabar fill-rule method validation)",
        "stratum": "TRAIN-only (first 49%); nested TEST + final-30% holdout sealed",
        "barrier_anchor": "ZigZag trend-change confirmation (EXP-049 benchmark; NOT the harami)",
        "harami_detector_used": False,
        "params": {
            "atr_period": ATR_PERIOD, "atr_mult": ATR_MULT, "atr_estimator": "Wilder",
            "favourable_fraction": 0.50, "adverse": "1:1 R:R (P3)",
            "third_barrier": "N=max(6,round(1.5*median(trailing-20 confirmed-move durations)))",
            "lookback": 1, "n_boot": 10000, "base_seed": BASE_SEED,
            "fill_rules": {
                "worst_case": "same-bar double-touch -> ADVERSE (EXP-049 baseline)",
                "p15": "path-ordered: bullish O->L->H->C; bearish O->H->L->C",
            },
            "rng_streams": {
                "worst_case_leg": "[BASE_SEED, cell_index, geom_id]",
                "p15_leg": "[BASE_SEED, cell_index, geom_id, 15]",
                "expectancy_wc": "[BASE_SEED, cell_index, 1, 99, 0]",
                "expectancy_p15": "[BASE_SEED, cell_index, 1, 99, 15]",
            },
            "geometries": {"G1_primary": "distance-based (0.5*M)",
                           "G2_secondary": "retracement-level (move midpoint)"},
            "binding_comparison_metric": "first-hit r = FAV/(FAV+ADV) over resolved (G1)",
            "disclosed_secondary": "P14 median per-event gross ATR-normalised expectancy (G1)",
        },
        "membership": {
            "source": "EXP-048 readiness_map.csv (READY + READY_FLAGGED); EXP-049 99-cell grid",
            "n_member_cells": sum(1 for r in records if r["member"]),
            "n_excluded_cells": sum(1 for r in records if not r["member"]),
        },
        "reconciliation": {
            "anchor": str(EXP049_PER_CELL),
            "rule": ("worst-case leg must reproduce EXP-049 g1/g2 FAV/ADV/resolved "
                     "(exact) and r/CI bounds (within 1e-12); else SUBSTRATE_METHOD_DEFECT."),
            "all_cells_ok": all(r.get("recon_ok", True) for r in records if r["member"]),
        },
        "denominators": {
            "primary_r": "FAV / (FAV + ADV) over resolved; resolved<30 -> NOT_VIABLE_BY_POWER",
            "dt_frac": "same-bar double-touch / resolved; resolved==0 -> None",
            "reassigned_frac": "(FAV_p15 - FAV_wc) / resolved; resolved==0 -> None",
            "expectancy": "median over qualifying (FAV/ADV/TIMECAP, finite exit, ATR>0); "
                          "<30 qualifying -> NOT_VIABLE_BY_POWER",
            "g2_degenerate_frac": "g2_degenerate_excluded / (g2_defined + g2_degenerate_excluded)",
        },
        "verdict": verdict, "composition_readout": readout,
        "de30_disclosure": DE30_DISCLOSURE,
        "session_model_caveat": SESSION_MODEL_CAVEAT,
        "continuous_market_instruments": list(CONTINUOUS_MARKET_INSTRUMENTS),
        "instrument_meta": instrument_meta,
        "holdout_fence": (
            "Only Parquet metadata + first train_rows file-order rows read per "
            "instrument; full file never sorted/collected; every domain bar fenced "
            "to CloseTime <= train_end_ts; forward resolution windows clipped to the "
            "TRAIN edge; TEST and final-30% holdout never read."),
        "approximation_note": P15_APPROXIMATION_NOTE,
        "note": ("Routing (benchmark re-baseline on P15 vs adopt-P15-as-standard) is the "
                 "§8 G2-area desk adjudication on this readout, not self-declared here."),
    }
    with open(RESULTS_DIR / "run_metadata.json", "w") as fh:
        json.dump(meta, fh, indent=2, default=str)


def _summarize(
    records: list[dict[str, Any]], verdict: dict[str, Any], readout: dict[str, Any],
) -> dict[str, Any]:
    """Concise stdout summary."""
    status_counts: dict[str, int] = {}
    for r in records:
        s = r["g1_viable_status_p15"]
        status_counts[s] = status_counts.get(s, 0) + 1
    return {
        "verdict": verdict["verdict"],
        "material_classification": readout["material_classification"],
        "g1_p15_status_counts": status_counts,
        "g1_p15_composition_met": readout["g1_p15_composition"]["composition_met"],
        "g1_p15_n_viable": readout["g1_p15_composition"]["n_viable"],
        "exp049_n_viable": readout["exp049_baseline"]["n_viable"],
        "n_tie_break_sensitive": readout["n_tie_break_sensitive"],
        "g1_delta_r_median": readout["g1_delta_r_median"],
        "g1_dt_frac_median": readout["g1_dt_frac_median"],
        "non_deterministic_cells": verdict["non_deterministic_cells"],
        "reconciliation_failures": verdict["reconciliation_failures"],
        "monotonicity_failures": verdict["monotonicity_failures"],
        "systematic_invariant_failures": verdict["systematic_invariant_failures"],
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    summary = run()
    LOGGER.info("\n=== %s complete ===", EXPERIMENT_ID)
    LOGGER.info("verdict: %s (%s)", summary["verdict"], summary["material_classification"])
    LOGGER.info("P15 G1 viability counts: %s", json.dumps(summary["g1_p15_status_counts"]))
    LOGGER.info("P15 G1 composition: %s VIABLE (met=%s) vs EXP-049 %s VIABLE",
                summary["g1_p15_n_viable"], summary["g1_p15_composition_met"],
                summary["exp049_n_viable"])
    LOGGER.info("TIE_BREAK_SENSITIVE cells: %s; median delta_r=%s; median dt_frac=%s",
                summary["n_tie_break_sensitive"], summary["g1_delta_r_median"],
                summary["g1_dt_frac_median"])
    for label, key in (("NON-DETERMINISTIC", "non_deterministic_cells"),
                       ("RECONCILIATION FAIL", "reconciliation_failures"),
                       ("MONOTONICITY FAIL", "monotonicity_failures")):
        if summary[key]:
            LOGGER.info("%s: %s", label, summary[key])
    if summary["systematic_invariant_failures"]:
        LOGGER.info("SYSTEMATIC INVARIANT FAILURES: %s",
                    json.dumps(summary["systematic_invariant_failures"]))
    LOGGER.info("artifacts -> %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
