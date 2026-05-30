"""
Experiment EXP-036: Prior-Range Location Executable State-Aligned Return Test
Implements the analysis plan from analysis-plan.md.

First Phase 005 return test of the highest-priority readiness-passing directional
descriptor. On holdout-excluded 1h/4h real bars (strict aggregation, the canonical
Phase 005 rule), it tests whether the Prior-Range Location extreme states, traded
in their predeclared continuation direction (top -> long, bottom -> short), earn a
higher executable next-bar log return than:

  (a) the *measured* mean return of the neutral middle bucket (mu_mid), via the
      direction-adjusted excess  Delta_neutral = mean( d * (r - mu_mid) ); and
  (b) a matched prior-bar-momentum-sign control, via the paired head-to-head
      Delta_control = mean( (d - c) * r ) on the descriptor's own traded bars.

Inference is episode-level (resample independent state episodes, never rows). The
neutral CI uses a two-sample episode bootstrap (extreme + middle episodes drawn
independently) so the mu_mid baseline's sampling error is propagated. A single
predeclared 4-bar hold is co-tested under asymmetric gate semantics. The verdict
requires train/test sign preservation on >= 2 distinct instruments. All returns
use real OHLC; no synthetic price is used anywhere.
"""
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import polars as pl
import seaborn as sns

PYTHON_ROOT = Path(__file__).resolve().parents[3]
PROJECT_ROOT = PYTHON_ROOT.parent
SRC_DIR = PYTHON_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from bar_aggregator import aggregate_ohlc  # noqa: E402
from ict_timebar import INSTRUMENTS, load_analysis_timebars  # noqa: E402


LOGGER = logging.getLogger(__name__)

DATA_DIR = PROJECT_ROOT / "data"
EXP_DIR = PYTHON_ROOT / "experiments" / "EXP-036"
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"

# ── Predeclared constants (frozen by scope.md) ────────────────────────────────

TIMEFRAMES = {"1h": 60, "4h": 240}
PERIOD_TO_TF = {v: k for k, v in TIMEFRAMES.items()}
LOOKBACK_BARS = 20
BUCKET_BOTTOM_MAX = 0.20
BUCKET_TOP_MIN = 0.80
ANALYSIS_TRAIN_FRACTION = 0.70
STRICT_MIN_COVERAGE = None  # canonical Phase 005 aggregation (mid-phase reflection)

SECONDARY_HOLD = 4  # single predeclared longer horizon (fixed a priori)
HORIZONS = ("next_bar", "four_bar")

MIN_ROWS_TRAIN = 100
MIN_ROWS_TEST = 50
MIN_EPISODES_TRAIN = 30
MIN_EPISODES_TEST = 15
QUALIFYING_INSTRUMENT_FLOOR = 2

BOOTSTRAP_N = 10_000
BOOTSTRAP_SEED = 42
BOOTSTRAP_CELL_BUDGET = 2_000_000  # cap on (chunk x n_episodes) index cells

SEGMENTS = ("Train", "Test")
EXTREME_BUCKETS = ("top", "bottom")
CONTRASTS = ("neutral", "control")


@dataclass(frozen=True)
class CellFeature:
    """Holdout-excluded, feature- and return-loaded higher-timeframe frame."""

    instrument: str
    timeframe: str
    frame: pd.DataFrame  # one row per aggregated bar, both segments


# ── Load / aggregate / feature / return pipeline ─────────────────────────────


def _add_segment(bars_tf: pl.DataFrame) -> pl.DataFrame:
    """Label Train/Test by chronological position on the aggregated series."""
    train_rows = int(bars_tf.height * ANALYSIS_TRAIN_FRACTION)
    return (
        bars_tf.with_row_index("_Row")
        .with_columns(
            pl.when(pl.col("_Row") < train_rows)
            .then(pl.lit("Train"))
            .otherwise(pl.lit("Test"))
            .alias("Segment")
        )
        .drop("_Row")
    )


def _add_range_location(bars_tf: pl.DataFrame) -> pl.DataFrame:
    """Attach prior-range location, bucket, and directional implication d.

    Reuses the EXP-034 feature construction bit-for-bit (shifted 20-bar range,
    clip with degenerate exclusion), then maps buckets to d in {+1, -1, 0}.
    """
    with_prior = bars_tf.with_columns(
        pl.col("High")
        .rolling_max(window_size=LOOKBACK_BARS, min_samples=LOOKBACK_BARS)
        .shift(1)
        .alias("PriorHigh"),
        pl.col("Low")
        .rolling_min(window_size=LOOKBACK_BARS, min_samples=LOOKBACK_BARS)
        .shift(1)
        .alias("PriorLow"),
    ).with_columns((pl.col("PriorHigh") - pl.col("PriorLow")).alias("Denom"))
    with_loc = with_prior.with_columns(
        (pl.col("Denom").is_null() | (pl.col("Denom") <= 0.0)).alias("Degenerate")
    ).with_columns(
        pl.when(pl.col("Denom").is_null() | (pl.col("Denom") <= 0.0))
        .then(None)
        .otherwise((pl.col("Close") - pl.col("PriorLow")) / pl.col("Denom"))
        .alias("RawLocation")
    )
    with_bucket = with_loc.with_columns(
        pl.col("RawLocation").clip(0.0, 1.0).alias("ClippedLocation"),
    ).with_columns(
        pl.when(pl.col("RawLocation").is_null())
        .then(None)
        .when(pl.col("ClippedLocation") <= BUCKET_BOTTOM_MAX)
        .then(pl.lit("bottom"))
        .when(pl.col("ClippedLocation") >= BUCKET_TOP_MIN)
        .then(pl.lit("top"))
        .otherwise(pl.lit("middle"))
        .alias("Bucket")
    )
    return with_bucket.with_columns(
        pl.when(pl.col("Bucket") == "top")
        .then(1)
        .when(pl.col("Bucket") == "bottom")
        .then(-1)
        .when(pl.col("Bucket") == "middle")
        .then(0)
        .otherwise(None)
        .alias("D")
    )


def _add_returns_and_control(featured: pl.DataFrame) -> pl.DataFrame:
    """Attach executable returns (next-bar, 4-bar), control sign, and entry gap.

    Returns enter at the next same-timeframe bar open and exit at that bar's
    close (next-bar) or at the close of the 4th subsequent bar (4-bar). Forward
    bars are taken within the same Segment, so the boundary bars of each segment
    are return-ineligible by construction (no in-segment forward bar). The
    control momentum sign uses the prior bar's close (information at bar i).
    """
    nxt_open = pl.col("Open").shift(-1).over("Segment")
    nxt_close = pl.col("Close").shift(-1).over("Segment")
    close_4 = pl.col("Close").shift(-SECONDARY_HOLD).over("Segment")
    nxt_time = pl.col("CloseTime").shift(-1).over("Segment")
    time_4 = pl.col("CloseTime").shift(-SECONDARY_HOLD).over("Segment")
    prior_close = pl.col("Close").shift(1)
    return featured.with_columns(
        pl.when(nxt_open.is_null() | nxt_close.is_null() | (nxt_open <= 0))
        .then(None)
        .otherwise((nxt_close / nxt_open).log())
        .alias("RetNextBar"),
        pl.when(nxt_open.is_null() | close_4.is_null() | (nxt_open <= 0))
        .then(None)
        .otherwise((close_4 / nxt_open).log())
        .alias("RetFourBar"),
        pl.when(prior_close.is_null())
        .then(0)
        .otherwise(pl.col("Close").sub(prior_close).sign().cast(pl.Int64))
        .alias("Control"),
        ((nxt_time - pl.col("CloseTime")).dt.total_minutes()).alias("EntryGapMin"),
        ((time_4 - nxt_time).dt.total_minutes()).alias("HoldSpanMin"),
    )


def _build_cell(instrument: str, period_minutes: int) -> CellFeature:
    """Load holdout-excluded 1m, strict-aggregate, feature, and add returns."""
    frame_1m = load_analysis_timebars(DATA_DIR, instrument).frame
    bars_tf = aggregate_ohlc(
        frame_1m, period_minutes=period_minutes, min_coverage=STRICT_MIN_COVERAGE
    )
    timeframe = PERIOD_TO_TF[period_minutes]
    cols = [
        "CloseTime", "Segment", "Bucket", "D", "Control",
        "RetNextBar", "RetFourBar", "EntryGapMin", "HoldSpanMin",
    ]
    if bars_tf.is_empty():
        return CellFeature(instrument, timeframe, pd.DataFrame(columns=cols))
    featured = _add_returns_and_control(_add_range_location(_add_segment(bars_tf)))
    return CellFeature(instrument, timeframe, featured.select(cols).to_pandas())


# ── Episode aggregation (independent state episodes) ─────────────────────────


@dataclass(frozen=True)
class EpisodeAgg:
    """Per-episode aggregates for one state group within one segment/horizon."""

    cnt: np.ndarray      # bars per episode (return-eligible only)
    sum_r: np.ndarray    # sum of returns
    sum_cr: np.ndarray   # sum of control_sign * return
    sign: np.ndarray     # +1 (top) / -1 (bottom); zeros for middle (unused)


def _episode_ids(buckets: pd.Series) -> np.ndarray:
    """Maximal runs of consecutive equal, non-null buckets; null breaks a run."""
    vals = buckets.to_numpy(dtype=object)
    ids = np.full(len(vals), -1, dtype=np.int64)
    current = -1
    prev = None
    for i, b in enumerate(vals):
        if b is None or (isinstance(b, float) and np.isnan(b)):
            prev = None
            continue
        if b != prev:
            current += 1
        ids[i] = current
        prev = b
    return ids


def _aggregate_episodes(
    seg: pd.DataFrame, ret_col: str, mask: np.ndarray
) -> EpisodeAgg:
    """Aggregate return-eligible bars under `mask` into per-episode sums."""
    ep = _episode_ids(seg["Bucket"])
    eligible = mask & seg[ret_col].notna().to_numpy() & (ep >= 0)
    if not eligible.any():
        empty = np.zeros(0)
        return EpisodeAgg(empty, empty, empty, empty)
    df = pd.DataFrame(
        {
            "ep": ep[eligible],
            "r": seg[ret_col].to_numpy()[eligible],
            "cr": (seg["Control"].to_numpy()[eligible] * seg[ret_col].to_numpy()[eligible]),
            "d": seg["D"].to_numpy()[eligible],
        }
    )
    grouped = df.groupby("ep", sort=True)
    return EpisodeAgg(
        cnt=grouped.size().to_numpy().astype(float),
        sum_r=grouped["r"].sum().to_numpy(),
        sum_cr=grouped["cr"].sum().to_numpy(),
        sign=grouped["d"].first().to_numpy().astype(float),
    )


def _state_counts(seg: pd.DataFrame, ret_col: str) -> dict[str, dict[str, int]]:
    """Return-eligible row and independent-episode counts per state."""
    ep = _episode_ids(seg["Bucket"])
    eligible = seg[ret_col].notna().to_numpy() & (ep >= 0)
    out: dict[str, dict[str, int]] = {}
    for state in ("top", "bottom", "middle"):
        mask = eligible & (seg["Bucket"].to_numpy(dtype=object) == state)
        n_rows = int(mask.sum())
        n_eps = int(len(np.unique(ep[mask]))) if n_rows else 0
        out[state] = {"rows": n_rows, "episodes": n_eps}
    return out


# ── Two-sample episode bootstrap (extreme vs middle baseline) ────────────────


def _episode_bootstrap(
    extreme: EpisodeAgg, middle: EpisodeAgg, seed: int
) -> dict[str, dict[str, float]]:
    """Episode-resampled point estimates and 95% CIs for the four statistics.

    Resamples extreme episodes and middle episodes independently with
    replacement (same episode count as observed), recomputing mu_mid each draw,
    so the baseline's sampling error enters the neutral CI. Returns Delta_neutral,
    Delta_control, and the two per-side excesses.
    """
    stats = ("neutral", "control", "top_excess", "bottom_excess")
    n_ext, n_mid = len(extreme.cnt), len(middle.cnt)
    if n_ext == 0 or n_mid == 0:
        nan = {"point": float("nan"), "ci_lower": float("nan"), "ci_upper": float("nan")}
        return {s: dict(nan) for s in stats}

    sum_dr = extreme.sign * extreme.sum_r
    sum_d = extreme.sign * extreme.cnt
    sum_dmcr = sum_dr - extreme.sum_cr
    is_top, is_bot = extreme.sign > 0, extreme.sign < 0
    cnt_top, sum_r_top = extreme.cnt * is_top, extreme.sum_r * is_top
    cnt_bot, sum_r_bot = extreme.cnt * is_bot, extreme.sum_r * is_bot

    point = _stat_values(
        sum_dr.sum(), sum_d.sum(), sum_dmcr.sum(), extreme.cnt.sum(),
        sum_r_top.sum(), cnt_top.sum(), sum_r_bot.sum(), cnt_bot.sum(),
        middle.sum_r.sum(), middle.cnt.sum(),
    )

    rng = np.random.default_rng(seed)
    draws: dict[str, list[np.ndarray]] = {s: [] for s in stats}
    chunk = max(1, BOOTSTRAP_CELL_BUDGET // max(n_ext, n_mid, 1))
    for start in range(0, BOOTSTRAP_N, chunk):
        size = min(chunk, BOOTSTRAP_N - start)
        ei = rng.integers(0, n_ext, size=(size, n_ext))
        mi = rng.integers(0, n_mid, size=(size, n_mid))
        vals = _stat_values(
            sum_dr[ei].sum(1), sum_d[ei].sum(1), sum_dmcr[ei].sum(1),
            extreme.cnt[ei].sum(1), sum_r_top[ei].sum(1), cnt_top[ei].sum(1),
            sum_r_bot[ei].sum(1), cnt_bot[ei].sum(1),
            middle.sum_r[mi].sum(1), middle.cnt[mi].sum(1),
        )
        for s in stats:
            draws[s].append(np.atleast_1d(vals[s]))

    out: dict[str, dict[str, float]] = {}
    for s in stats:
        dist = np.concatenate(draws[s])
        dist = dist[np.isfinite(dist)]
        out[s] = {
            "point": float(point[s]),
            "ci_lower": float(np.quantile(dist, 0.025)) if dist.size else float("nan"),
            "ci_upper": float(np.quantile(dist, 0.975)) if dist.size else float("nan"),
        }
    return out


def _stat_values(
    sum_dr: Any, sum_d: Any, sum_dmcr: Any, n_ext: Any,
    sum_r_top: Any, n_top: Any, sum_r_bot: Any, n_bot: Any,
    sum_mid_r: Any, n_mid: Any,
) -> dict[str, Any]:
    """Vectorized four statistics from resampled (or observed) episode sums."""
    with np.errstate(invalid="ignore", divide="ignore"):
        mu_mid = sum_mid_r / n_mid
        neutral = sum_dr / n_ext - mu_mid * (sum_d / n_ext)
        control = sum_dmcr / n_ext
        top_excess = np.where(np.asarray(n_top) > 0, sum_r_top / n_top - mu_mid, np.nan)
        bottom_excess = np.where(np.asarray(n_bot) > 0, mu_mid - sum_r_bot / n_bot, np.nan)
    return {
        "neutral": neutral,
        "control": control,
        "top_excess": top_excess,
        "bottom_excess": bottom_excess,
    }


# ── Per-cell metrics assembly ────────────────────────────────────────────────


def _bar_level_agg(seg: pd.DataFrame, ret_col: str, mask: np.ndarray) -> EpisodeAgg:
    """One unit per eligible bar (cnt=1). Feeding these to the bootstrap gives a
    genuine naive row-level resample (ignores serial dependence) for diagnosis."""
    eligible = mask & seg[ret_col].notna().to_numpy()
    if not eligible.any():
        empty = np.zeros(0)
        return EpisodeAgg(empty, empty, empty, empty)
    r = seg[ret_col].to_numpy()[eligible]
    c = seg["Control"].to_numpy()[eligible].astype(float)
    d = seg["D"].to_numpy()[eligible].astype(float)
    return EpisodeAgg(cnt=np.ones(r.size), sum_r=r, sum_cr=c * r, sign=d)


def _segment_metrics(
    seg: pd.DataFrame, ret_col: str, seed: int
) -> dict[str, Any]:
    """Counts, mu_mid, episode-bootstrap contrasts, and row-level diagnostic."""
    counts = _state_counts(seg, ret_col)
    bucket = seg["Bucket"].to_numpy(dtype=object)
    extreme_mask = np.isin(bucket, EXTREME_BUCKETS)
    middle_mask = bucket == "middle"
    extreme = _aggregate_episodes(seg, ret_col, extreme_mask)
    middle = _aggregate_episodes(seg, ret_col, middle_mask)
    mid_r = seg[ret_col].to_numpy()[middle_mask & seg[ret_col].notna().to_numpy()]
    mu_mid = float(np.mean(mid_r)) if mid_r.size else float("nan")
    boot = _episode_bootstrap(extreme, middle, seed)
    row_diag = _episode_bootstrap(
        _bar_level_agg(seg, ret_col, extreme_mask),
        _bar_level_agg(seg, ret_col, middle_mask),
        seed + 7919,
    )
    return {"counts": counts, "mu_mid": mu_mid, "boot": boot, "row_diag": row_diag}


def _floor_ok(counts: dict[str, dict[str, int]], state: str, segment: str) -> bool:
    """True iff the state clears row and episode floors for the segment."""
    min_rows = MIN_ROWS_TRAIN if segment == "Train" else MIN_ROWS_TEST
    min_eps = MIN_EPISODES_TRAIN if segment == "Train" else MIN_EPISODES_TEST
    return counts[state]["rows"] >= min_rows and counts[state]["episodes"] >= min_eps


def _contrast_adjudicable(counts: dict[str, dict[str, int]], contrast: str, segment: str) -> bool:
    """vs-neutral needs both extremes + middle; vs-control needs both extremes."""
    extremes_ok = all(_floor_ok(counts, s, segment) for s in EXTREME_BUCKETS)
    if contrast == "neutral":
        return extremes_ok and _floor_ok(counts, "middle", segment)
    return extremes_ok


def _cell_metrics(cell: CellFeature) -> dict[str, Any]:
    """All metrics, counts, and gap diagnostics for one (instrument, timeframe)."""
    frame = cell.frame
    seg_horizon: dict[tuple[str, str], dict[str, Any]] = {}
    for segment in SEGMENTS:
        seg = frame[frame["Segment"] == segment].reset_index(drop=True)
        for horizon, ret_col in (("next_bar", "RetNextBar"), ("four_bar", "RetFourBar")):
            seed = BOOTSTRAP_SEED + _cell_seed_offset(cell, segment, horizon)
            seg_horizon[(segment, horizon)] = _segment_metrics(seg, ret_col, seed)
    gap = _gap_summary(frame, TIMEFRAMES[cell.timeframe])
    return {"seg_horizon": seg_horizon, "gap": gap}


def _cell_seed_offset(cell: CellFeature, segment: str, horizon: str) -> int:
    """Deterministic per-cell bootstrap seed offset (no overlap across cells)."""
    inst_idx = INSTRUMENTS.index(cell.instrument)
    tf_idx = list(TIMEFRAMES).index(cell.timeframe)
    seg_idx = SEGMENTS.index(segment)
    hor_idx = HORIZONS.index(horizon)
    return ((inst_idx * 2 + tf_idx) * 2 + seg_idx) * 2 + hor_idx


def _gap_summary(frame: pd.DataFrame, period_minutes: int) -> dict[str, float]:
    """Entry-gap executability diagnostic over return-eligible next-bar rows.

    A gap-spanning entry is one whose next-bar entry is later than the nominal
    period (i.e., one or more clock windows were dropped between observation and
    entry); the single-bar return itself is still intrabar, so the gap delays
    entry rather than contaminating the return.
    """
    eligible = frame["RetNextBar"].notna()
    gaps = frame.loc[eligible, "EntryGapMin"].to_numpy(dtype=float)
    gaps = gaps[np.isfinite(gaps)]
    if gaps.size == 0:
        return {"median_gap_min": float("nan"), "max_gap_min": float("nan"),
                "gap_spanning_share": float("nan")}
    return {
        "median_gap_min": float(np.median(gaps)),
        "max_gap_min": float(np.max(gaps)),
        "gap_spanning_share": float(np.mean(gaps > period_minutes)),
    }


# ── Tables and verdict ───────────────────────────────────────────────────────


def _metrics_rows(metrics: dict[tuple[str, str], dict[str, Any]]) -> pd.DataFrame:
    """Flatten per-cell metrics into a long table for results/."""
    rows: list[dict[str, Any]] = []
    for (instrument, timeframe), cell in metrics.items():
        for (segment, horizon), m in cell["seg_horizon"].items():
            row: dict[str, Any] = {
                "Instrument": instrument, "Timeframe": timeframe,
                "Segment": segment, "Horizon": horizon, "MuMid": m["mu_mid"],
            }
            for state in ("top", "bottom", "middle"):
                row[f"Rows_{state}"] = m["counts"][state]["rows"]
                row[f"Eps_{state}"] = m["counts"][state]["episodes"]
            for stat, vals in m["boot"].items():
                row[f"{stat}_pt"] = vals["point"]
                row[f"{stat}_lo"] = vals["ci_lower"]
                row[f"{stat}_hi"] = vals["ci_upper"]
            for contrast in CONTRASTS:  # diagnostic naive row-level CI (not gating)
                row[f"{contrast}_rowdiag_lo"] = m["row_diag"][contrast]["ci_lower"]
                row[f"{contrast}_rowdiag_hi"] = m["row_diag"][contrast]["ci_upper"]
            for contrast in CONTRASTS:
                row[f"{contrast}_adjudicable"] = _contrast_adjudicable(
                    m["counts"], contrast, segment
                )
            rows.append(row)
    return pd.DataFrame(rows)


def _replicates(metrics: dict[tuple[str, str], dict[str, Any]],
                instrument: str, timeframe: str, contrast: str, horizon: str) -> bool | None:
    """Replication: test CI excludes 0 positively AND train point positive.

    Returns None when the contrast is not adjudicable in either segment
    (sub-floor), so it is excluded from the >=2-instrument tally rather than
    counted as a failure.
    """
    cell = metrics[(instrument, timeframe)]
    train = cell["seg_horizon"][("Train", horizon)]
    test = cell["seg_horizon"][("Test", horizon)]
    if not (_contrast_adjudicable(train["counts"], contrast, "Train")
            and _contrast_adjudicable(test["counts"], contrast, "Test")):
        return None
    train_pt = train["boot"][contrast]["point"]
    test_lo = test["boot"][contrast]["ci_lower"]
    if not (np.isfinite(train_pt) and np.isfinite(test_lo)):
        return None
    return bool(test_lo > 0.0 and train_pt > 0.0)


def _passing_instruments(metrics: dict[tuple[str, str], dict[str, Any]],
                         contrasts: tuple[str, ...], horizon: str) -> dict[str, list[str]]:
    """Per timeframe, instruments replicating *all* listed contrasts at horizon."""
    out: dict[str, list[str]] = {}
    for timeframe in TIMEFRAMES:
        passing = []
        for instrument in INSTRUMENTS:
            flags = [_replicates(metrics, instrument, timeframe, c, horizon) for c in contrasts]
            if all(f is True for f in flags):
                passing.append(instrument)
        out[timeframe] = passing
    return out


def _adjudicable_instruments(metrics: dict[tuple[str, str], dict[str, Any]],
                             contrast: str, horizon: str) -> dict[str, list[str]]:
    """Per timeframe, instruments whose contrast is adjudicable in both segments."""
    out: dict[str, list[str]] = {}
    for timeframe in TIMEFRAMES:
        out[timeframe] = [
            inst for inst in INSTRUMENTS
            if _replicates(metrics, inst, timeframe, contrast, horizon) is not None
        ]
    return out


def _verdict(metrics: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    """Apply the predeclared FOR / state-diff / AGAINST / horizon-dep / inconclusive table."""
    nb_both = _passing_instruments(metrics, ("neutral", "control"), "next_bar")
    nb_neutral = _passing_instruments(metrics, ("neutral",), "next_bar")
    fb_both = _passing_instruments(metrics, ("neutral", "control"), "four_bar")
    nb_control_adj = _adjudicable_instruments(metrics, "control", "next_bar")

    def _max_count(passing: dict[str, list[str]]) -> int:
        return max((len(v) for v in passing.values()), default=0)

    nb_both_max, nb_neutral_max = _max_count(nb_both), _max_count(nb_neutral)
    fb_both_max, nb_control_adj_max = _max_count(fb_both), _max_count(nb_control_adj)

    if nb_both_max >= QUALIFYING_INSTRUMENT_FLOOR:
        text = ("FOR (edge candidate): next-bar Delta_neutral AND Delta_control "
                f"replicate on >=2 distinct instruments {nb_both}. Advances to EXP-038.")
        outcome = "FOR"
    elif nb_neutral_max >= QUALIFYING_INSTRUMENT_FLOOR:
        text = ("STATE-DIFFERENTIATION-ONLY: next-bar Delta_neutral replicates on "
                f">=2 instruments {nb_neutral} but Delta_control does not (Gate 4).")
        outcome = "STATE_DIFFERENTIATION_ONLY"
    elif fb_both_max >= QUALIFYING_INSTRUMENT_FLOOR:
        text = ("HORIZON-DEPENDENT STATE DIFFERENTIATION: next-bar control gate "
                f"fails but 4-bar Delta_neutral AND Delta_control replicate {fb_both}. "
                "Reopen at the longer horizon via a new experiment; not refutation.")
        outcome = "HORIZON_DEPENDENT"
    elif nb_both_max == 1 or nb_control_adj_max < QUALIFYING_INSTRUMENT_FLOOR:
        text = ("INCONCLUSIVE: the >=2 distinct-instrument rule cannot be cleanly "
                f"adjudicated (best next-bar both-contrast pass = {nb_both_max}; "
                f"max instruments adjudicable for the control gate at a timeframe = "
                f"{nb_control_adj_max}). Not a clean refutation.")
        outcome = "INCONCLUSIVE"
    else:
        text = ("AGAINST (refuted): with >=2 instruments adjudicable for the control "
                "gate at a timeframe, <2 replicate it at either horizon. "
                "State-descriptor thesis refuted for the cleanest candidate, holdout intact.")
        outcome = "AGAINST"
    return {
        "verdict_text": text, "outcome": outcome,
        "next_bar_neutral_and_control": nb_both,
        "next_bar_neutral_only": nb_neutral,
        "four_bar_neutral_and_control": fb_both,
        "next_bar_control_adjudicable": nb_control_adj,
    }


# ── Plotting helpers (bounded summary inputs only) ───────────────────────────


def _bucket_mean_with_ci(seg_metrics: dict[str, Any], state: str) -> tuple[float, float, float]:
    """Mean return and 95% CI for a single bucket (excess + mu_mid back-out)."""
    mu = seg_metrics["mu_mid"]
    if state == "middle":
        return mu, np.nan, np.nan
    key = "top_excess" if state == "top" else "bottom_excess"
    vals = seg_metrics["boot"][key]
    sign = 1.0 if state == "top" else -1.0
    # excess(top)=mean_top-mu ; excess(bottom)=mu-mean_bottom -> recover mean
    mean = mu + sign * vals["point"]
    lo = mu + sign * (vals["ci_lower"] if sign > 0 else vals["ci_upper"])
    hi = mu + sign * (vals["ci_upper"] if sign > 0 else vals["ci_lower"])
    return mean, lo, hi


def _plot_bucket_means(metrics: dict[tuple[str, str], dict[str, Any]], save_path: Path) -> None:
    """2x4 grid: top/middle/bottom test-segment mean returns vs the mu_mid line."""
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 4, figsize=(18, 8), sharex=True)
    states = ["bottom", "middle", "top"]
    for col, instrument in enumerate(INSTRUMENTS):
        for row, timeframe in enumerate(TIMEFRAMES):
            ax = axes[row, col]
            m = metrics[(instrument, timeframe)]["seg_horizon"][("Test", "next_bar")]
            means, los, his = zip(*(_bucket_mean_with_ci(m, s) for s in states))
            x = np.arange(len(states))
            errs = [np.array(means) - np.array(los), np.array(his) - np.array(means)]
            errs = np.where(np.isfinite(errs), errs, 0.0)
            ax.bar(x, means, color=["#d9534f", "#999999", "#5cb85c"])
            ax.errorbar(x, means, yerr=errs, fmt="none", ecolor="black", capsize=3)
            ax.axhline(m["mu_mid"], color="#3a7bd5", linestyle="--", linewidth=1,
                       label="mu_mid baseline")
            ax.axhline(0.0, color="black", linewidth=0.6)
            ax.set_xticks(x)
            ax.set_xticklabels(states, fontsize=8)
            ax.set_title(f"{instrument} {timeframe}", fontsize=9)
            if col == 0:
                ax.set_ylabel("Mean next-bar log return (Test)")
            if row == 0 and col == 0:
                ax.legend(fontsize=7)
    fig.suptitle("EXP-036: Bucket mean returns vs measured middle baseline (Test, next-bar)",
                 fontsize=13)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_contrast(metrics: dict[tuple[str, str], dict[str, Any]], contrast: str,
                   horizon: str, title: str, save_path: Path) -> None:
    """Grouped Train/Test point + CI of one contrast per (instrument, timeframe)."""
    sns.set_theme(style="whitegrid")
    labels, train_pt, test_pt, test_err = [], [], [], [[], []]
    for instrument in INSTRUMENTS:
        for timeframe in TIMEFRAMES:
            m = metrics[(instrument, timeframe)]["seg_horizon"]
            labels.append(f"{instrument}-{timeframe}")
            tr = m[("Train", horizon)]["boot"][contrast]["point"]
            te = m[("Test", horizon)]["boot"][contrast]
            train_pt.append(tr)
            test_pt.append(te["point"])
            test_err[0].append(te["point"] - te["ci_lower"])
            test_err[1].append(te["ci_upper"] - te["point"])
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.errorbar(x, test_pt, yerr=np.where(np.isfinite(test_err), test_err, 0.0),
                fmt="o", color="#3a7bd5", capsize=3, label="Test (95% CI)")
    ax.scatter(x, train_pt, marker="x", color="#f39c12", label="Train point")
    ax.axhline(0.0, color="red", linestyle="--", linewidth=1)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Return difference (log)")
    ax.set_title(title)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_replication_grid(metrics: dict[tuple[str, str], dict[str, Any]],
                           save_path: Path) -> None:
    """Pass/fail replication grid across contrasts and horizons."""
    sns.set_theme(style="white")
    cols = [("neutral", "next_bar"), ("control", "next_bar"),
            ("neutral", "four_bar"), ("control", "four_bar")]
    col_labels = ["neutral·NB", "control·NB", "neutral·4B", "control·4B"]
    rows = [(i, tf) for i in INSTRUMENTS for tf in TIMEFRAMES]
    grid = np.full((len(rows), len(cols)), np.nan)
    for r, (inst, tf) in enumerate(rows):
        for c, (contrast, horizon) in enumerate(cols):
            rep = _replicates(metrics, inst, tf, contrast, horizon)
            grid[r, c] = np.nan if rep is None else float(rep)
    fig, ax = plt.subplots(figsize=(8, 7))
    sns.heatmap(grid, annot=True, fmt=".0f", cmap="RdYlGn", vmin=0, vmax=1,
                cbar=False, linewidths=0.5, linecolor="#dddddd",
                xticklabels=col_labels,
                yticklabels=[f"{i}-{tf}" for i, tf in rows], ax=ax)
    ax.set_title("EXP-036: replication (1=test CI>0 & train>0; blank=not adjudicable)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ── Orchestration ────────────────────────────────────────────────────────────


def _json_safe(value: Any) -> Any:
    """Convert numpy scalars to plain Python for JSON; NaN/inf -> None."""
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    return value


def run_experiment() -> None:
    """Execute the EXP-036 return test end to end."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    metrics: dict[tuple[str, str], dict[str, Any]] = {}
    gap_rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        for timeframe, period in TIMEFRAMES.items():
            LOGGER.info("EXP-036: building + bootstrapping %s %s", instrument, timeframe)
            cell = _build_cell(instrument, period)
            metrics[(instrument, timeframe)] = _cell_metrics(cell)
            gap_rows.append(
                {"Instrument": instrument, "Timeframe": timeframe,
                 **metrics[(instrument, timeframe)]["gap"]}
            )

    metrics_df = _metrics_rows(metrics)
    verdict = _verdict(metrics)

    LOGGER.info("EXP-036: writing outputs")
    metrics_df.to_csv(RESULTS_DIR / "metrics_table.csv", index=False)
    pd.DataFrame(gap_rows).to_csv(RESULTS_DIR / "gap_diagnostics.csv", index=False)
    (RESULTS_DIR / "verdict.json").write_text(
        json.dumps(
            {
                **verdict,
                "thresholds": {
                    "lookback_bars": LOOKBACK_BARS,
                    "bucket_bottom_max": BUCKET_BOTTOM_MAX,
                    "bucket_top_min": BUCKET_TOP_MIN,
                    "secondary_hold_bars": SECONDARY_HOLD,
                    "min_rows_train": MIN_ROWS_TRAIN, "min_rows_test": MIN_ROWS_TEST,
                    "min_episodes_train": MIN_EPISODES_TRAIN,
                    "min_episodes_test": MIN_EPISODES_TEST,
                    "bootstrap_n": BOOTSTRAP_N, "bootstrap_seed": BOOTSTRAP_SEED,
                    "aggregation": "strict",
                },
            },
            indent=2,
            default=_json_safe,
        )
    )

    LOGGER.info("EXP-036: rendering plots")
    _plot_bucket_means(metrics, PLOTS_DIR / "01_bucket_means_vs_baseline.png")
    _plot_contrast(metrics, "control", "next_bar",
                   "EXP-036: Delta_control (next-bar) — descriptor minus momentum-sign control",
                   PLOTS_DIR / "02_delta_control_nextbar.png")
    _plot_replication_grid(metrics, PLOTS_DIR / "03_replication_grid.png")
    _plot_contrast(metrics, "neutral", "four_bar",
                   "EXP-036: Delta_neutral (4-bar secondary) — excess over middle baseline",
                   PLOTS_DIR / "04_secondary_4bar_neutral.png")

    _print_summary(metrics_df, verdict)


def _print_summary(metrics_df: pd.DataFrame, verdict: dict[str, Any]) -> None:
    """Concise manual-run summary."""
    print("\n=== EXP-036 next-bar contrasts (point estimates) ===")
    nb = metrics_df[metrics_df["Horizon"] == "next_bar"][
        ["Instrument", "Timeframe", "Segment", "MuMid", "neutral_pt",
         "neutral_lo", "control_pt", "control_lo",
         "neutral_adjudicable", "control_adjudicable"]
    ]
    print(nb.to_string(index=False))
    print("\n=== EXP-036 verdict ===")
    print(verdict["verdict_text"])
    print(f"  next-bar neutral+control passing: {verdict['next_bar_neutral_and_control']}")
    print(f"  next-bar neutral-only passing:    {verdict['next_bar_neutral_only']}")
    print(f"  4-bar neutral+control passing:    {verdict['four_bar_neutral_and_control']}")


def main() -> None:
    """Configure logging and run the experiment."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run_experiment()


if __name__ == "__main__":
    main()
