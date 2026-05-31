"""Frozen-stack calibration harness for Xen Phase 006.

This module supports EXP-037 null calibration and later Stage B power
experiments. It transcribes the EXP-036 reference stack and adds null resampling
utilities around it. The module performs no file I/O at import time and never
loads data unless called by experiment orchestration.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
import pandas as pd
import polars as pl

from bar_aggregator import aggregate_ohlc
from ict_timebar import INSTRUMENTS, load_analysis_timebars


TIMEFRAMES = {"1h": 60, "4h": 240}
PERIOD_TO_TF = {v: k for k, v in TIMEFRAMES.items()}
LOOKBACK_BARS = 20
BUCKET_BOTTOM_MAX = 0.20
BUCKET_TOP_MIN = 0.80
ANALYSIS_TRAIN_FRACTION = 0.70
STRICT_MIN_COVERAGE = None

SECONDARY_HOLD = 4
HORIZONS = ("next_bar", "four_bar")
SEGMENTS = ("Train", "Test")
EXTREME_BUCKETS = ("top", "bottom")
CONTRASTS = ("neutral", "control")

MIN_ROWS_TRAIN = 100
MIN_ROWS_TEST = 50
MIN_EPISODES_TRAIN = 30
MIN_EPISODES_TEST = 15
QUALIFYING_INSTRUMENT_FLOOR = 2

BOOTSTRAP_N = 10_000
BOOTSTRAP_SEED = 42
BOOTSTRAP_CELL_BUDGET = 2_000_000

NULL_BLOCK_LENGTHS = (20, 60, 240)
PART_A_REALIZATIONS = 150
PART_A_DOWNSCALED_REALIZATIONS = 100
PROFILE_FSE_COUNT = 10
FSE_RUNTIME_TARGET_SECONDS = 84.0

DESCRIPTOR_COUNT_TOL = 0.05
DESCRIPTOR_LENGTH_TOL = 0.10
CROSS_CORR_FROBENIUS_MAX = 0.20

CELL_COLUMNS = [
    "CloseTime",
    "Segment",
    "Bucket",
    "D",
    "Control",
    "RetNextBar",
    "RetFourBar",
    "EntryGapMin",
    "HoldSpanMin",
]


@dataclass(frozen=True)
class CellFeature:
    """Feature and return table for one instrument/timeframe cell."""

    instrument: str
    timeframe: str
    frame: pd.DataFrame


@dataclass(frozen=True)
class EpisodeAgg:
    """Per-episode aggregates for one state group within one segment/horizon."""

    cnt: np.ndarray
    sum_r: np.ndarray
    sum_cr: np.ndarray
    sign: np.ndarray


@dataclass(frozen=True)
class NullResult:
    """One null realization output."""

    cells: dict[tuple[str, str], CellFeature]
    diagnostics: dict[str, Any]
    metrics: dict[tuple[str, str], dict[str, Any]]
    verdict: dict[str, Any]


def build_observed_cells(
    data_dir: Path,
    instruments: Sequence[str] = tuple(INSTRUMENTS),
) -> dict[tuple[str, str], CellFeature]:
    """Load holdout-excluded data and build frozen-stack cell frames."""
    cells: dict[tuple[str, str], CellFeature] = {}
    for instrument in instruments:
        frame_1m = load_analysis_timebars(data_dir, instrument).frame
        for timeframe, period in TIMEFRAMES.items():
            cells[(instrument, timeframe)] = _build_cell(instrument, timeframe, period, frame_1m)
    return cells


def _build_cell(
    instrument: str,
    timeframe: str,
    period_minutes: int,
    frame_1m: pl.DataFrame,
) -> CellFeature:
    bars_tf = aggregate_ohlc(
        frame_1m, period_minutes=period_minutes, min_coverage=STRICT_MIN_COVERAGE
    )
    if bars_tf.is_empty():
        return CellFeature(instrument, timeframe, pd.DataFrame(columns=CELL_COLUMNS))
    featured = _add_returns_and_control(_add_range_location(_add_segment(bars_tf)))
    frame = featured.select(CELL_COLUMNS).to_pandas()
    return CellFeature(instrument, timeframe, frame)


def _add_segment(bars_tf: pl.DataFrame) -> pl.DataFrame:
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
        pl.when(pl.col("Degenerate"))
        .then(None)
        .otherwise((pl.col("Close") - pl.col("PriorLow")) / pl.col("Denom"))
        .alias("RawLocation")
    )
    return (
        with_loc.with_columns(pl.col("RawLocation").clip(0.0, 1.0).alias("ClippedLocation"))
        .with_columns(
            pl.when(pl.col("RawLocation").is_null())
            .then(None)
            .when(pl.col("ClippedLocation") <= BUCKET_BOTTOM_MAX)
            .then(pl.lit("bottom"))
            .when(pl.col("ClippedLocation") >= BUCKET_TOP_MIN)
            .then(pl.lit("top"))
            .otherwise(pl.lit("middle"))
            .alias("Bucket")
        )
        .with_columns(
            pl.when(pl.col("Bucket") == "top")
            .then(1)
            .when(pl.col("Bucket") == "bottom")
            .then(-1)
            .when(pl.col("Bucket") == "middle")
            .then(0)
            .otherwise(None)
            .alias("D")
        )
    )


def _add_returns_and_control(featured: pl.DataFrame) -> pl.DataFrame:
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


def stack_metrics(
    cells: dict[tuple[str, str], CellFeature],
    seed_index: int = 0,
) -> dict[tuple[str, str], dict[str, Any]]:
    """Run the frozen stack metrics on observed or null cells."""
    return {key: _cell_metrics(cell, seed_index) for key, cell in cells.items()}


def frozen_stack_verdict(metrics: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    """Apply the frozen EXP-036 verdict ladder."""
    nb_both = _passing_instruments(metrics, ("neutral", "control"), "next_bar")
    nb_neutral = _passing_instruments(metrics, ("neutral",), "next_bar")
    fb_both = _passing_instruments(metrics, ("neutral", "control"), "four_bar")
    nb_control_adj = _adjudicable_instruments(metrics, "control", "next_bar")

    nb_both_max = _max_count(nb_both)
    nb_neutral_max = _max_count(nb_neutral)
    fb_both_max = _max_count(fb_both)
    nb_control_adj_max = _max_count(nb_control_adj)
    if nb_both_max >= QUALIFYING_INSTRUMENT_FLOOR:
        outcome = "FOR"
    elif nb_neutral_max >= QUALIFYING_INSTRUMENT_FLOOR:
        outcome = "STATE_DIFFERENTIATION_ONLY"
    elif fb_both_max >= QUALIFYING_INSTRUMENT_FLOOR:
        outcome = "HORIZON_DEPENDENT"
    elif nb_both_max == 1 or nb_control_adj_max < QUALIFYING_INSTRUMENT_FLOOR:
        outcome = "INCONCLUSIVE"
    else:
        outcome = "AGAINST"
    return {
        "outcome": outcome,
        "next_bar_neutral_and_control": nb_both,
        "next_bar_neutral_only": nb_neutral,
        "four_bar_neutral_and_control": fb_both,
        "next_bar_control_adjudicable": nb_control_adj,
        "next_bar_both_max": nb_both_max,
        "next_bar_neutral_max": nb_neutral_max,
        "four_bar_both_max": fb_both_max,
        "next_bar_control_adjudicable_max": nb_control_adj_max,
        "full_stack_for": nb_both_max >= QUALIFYING_INSTRUMENT_FLOOR,
    }


def _max_count(passing: dict[str, list[str]]) -> int:
    return max((len(v) for v in passing.values()), default=0)


def _cell_metrics(cell: CellFeature, seed_index: int) -> dict[str, Any]:
    frame = cell.frame
    seg_horizon: dict[tuple[str, str], dict[str, Any]] = {}
    for segment in SEGMENTS:
        seg = frame[frame["Segment"] == segment].reset_index(drop=True)
        for horizon, ret_col in (("next_bar", "RetNextBar"), ("four_bar", "RetFourBar")):
            seed = BOOTSTRAP_SEED + seed_index * 10_000 + _cell_seed_offset(cell, segment, horizon)
            seg_horizon[(segment, horizon)] = _segment_metrics(seg, ret_col, seed)
    return {"seg_horizon": seg_horizon, "gap": _gap_summary(frame, TIMEFRAMES[cell.timeframe])}


def _cell_seed_offset(cell: CellFeature, segment: str, horizon: str) -> int:
    inst_idx = INSTRUMENTS.index(cell.instrument)
    tf_idx = list(TIMEFRAMES).index(cell.timeframe)
    seg_idx = SEGMENTS.index(segment)
    hor_idx = HORIZONS.index(horizon)
    return ((inst_idx * 2 + tf_idx) * 2 + seg_idx) * 2 + hor_idx


def _segment_metrics(seg: pd.DataFrame, ret_col: str, seed: int) -> dict[str, Any]:
    counts = _state_counts(seg, ret_col)
    bucket = seg["Bucket"].to_numpy(dtype=object)
    extreme_mask = np.isin(bucket, EXTREME_BUCKETS)
    middle_mask = bucket == "middle"
    extreme = _aggregate_episodes(seg, ret_col, extreme_mask)
    middle = _aggregate_episodes(seg, ret_col, middle_mask)
    mid_r = seg[ret_col].to_numpy()[middle_mask & seg[ret_col].notna().to_numpy()]
    mu_mid = float(np.mean(mid_r)) if mid_r.size else float("nan")
    boot = _episode_bootstrap(extreme, middle, seed)
    return {"counts": counts, "mu_mid": mu_mid, "boot": boot}


def _episode_ids(buckets: pd.Series) -> np.ndarray:
    vals = buckets.to_numpy(dtype=object)
    ids = np.full(len(vals), -1, dtype=np.int64)
    current = -1
    prev = object()
    for i, value in enumerate(vals):
        if _is_null_bucket(value):
            prev = object()
            continue
        if value != prev:
            current += 1
        ids[i] = current
        prev = value
    return ids


def _is_null_bucket(value: Any) -> bool:
    return value is None or (isinstance(value, float) and np.isnan(value))


def _aggregate_episodes(seg: pd.DataFrame, ret_col: str, mask: np.ndarray) -> EpisodeAgg:
    ep = _episode_ids(seg["Bucket"])
    eligible = mask & seg[ret_col].notna().to_numpy() & (ep >= 0)
    if not eligible.any():
        empty = np.zeros(0)
        return EpisodeAgg(empty, empty, empty, empty)
    returns = seg[ret_col].to_numpy()[eligible]
    frame = pd.DataFrame(
        {
            "ep": ep[eligible],
            "r": returns,
            "cr": seg["Control"].to_numpy()[eligible] * returns,
            "d": seg["D"].to_numpy()[eligible],
        }
    )
    grouped = frame.groupby("ep", sort=True)
    return EpisodeAgg(
        cnt=grouped.size().to_numpy().astype(float),
        sum_r=grouped["r"].sum().to_numpy(),
        sum_cr=grouped["cr"].sum().to_numpy(),
        sign=grouped["d"].first().to_numpy().astype(float),
    )


def _state_counts(seg: pd.DataFrame, ret_col: str) -> dict[str, dict[str, int]]:
    ep = _episode_ids(seg["Bucket"])
    eligible = seg[ret_col].notna().to_numpy() & (ep >= 0)
    out: dict[str, dict[str, int]] = {}
    for state in ("top", "bottom", "middle"):
        mask = eligible & (seg["Bucket"].to_numpy(dtype=object) == state)
        rows = int(mask.sum())
        episodes = int(len(np.unique(ep[mask]))) if rows else 0
        out[state] = {"rows": rows, "episodes": episodes}
    return out


def _episode_bootstrap(
    extreme: EpisodeAgg,
    middle: EpisodeAgg,
    seed: int,
) -> dict[str, dict[str, float]]:
    stats = ("neutral", "control", "top_excess", "bottom_excess")
    n_ext = len(extreme.cnt)
    n_mid = len(middle.cnt)
    if n_ext == 0 or n_mid == 0:
        nan = {"point": float("nan"), "ci_lower": float("nan"), "ci_upper": float("nan")}
        return {stat: dict(nan) for stat in stats}

    sums = _episode_stat_inputs(extreme)
    point = _stat_values(*(arr.sum() for arr in sums), middle.sum_r.sum(), middle.cnt.sum())
    rng = np.random.default_rng(seed)
    draws: dict[str, list[np.ndarray]] = {stat: [] for stat in stats}
    chunk = max(1, BOOTSTRAP_CELL_BUDGET // max(n_ext, n_mid, 1))
    for start in range(0, BOOTSTRAP_N, chunk):
        size = min(chunk, BOOTSTRAP_N - start)
        ei = rng.integers(0, n_ext, size=(size, n_ext))
        mi = rng.integers(0, n_mid, size=(size, n_mid))
        resampled_sums = [arr[ei].sum(1) for arr in sums]
        values = _stat_values(
            *resampled_sums,
            middle.sum_r[mi].sum(1),
            middle.cnt[mi].sum(1),
        )
        for stat in stats:
            draws[stat].append(np.atleast_1d(values[stat]))

    out: dict[str, dict[str, float]] = {}
    for stat in stats:
        dist = np.concatenate(draws[stat])
        dist = dist[np.isfinite(dist)]
        out[stat] = {
            "point": float(point[stat]),
            "ci_lower": float(np.quantile(dist, 0.025)) if dist.size else float("nan"),
            "ci_upper": float(np.quantile(dist, 0.975)) if dist.size else float("nan"),
        }
    return out


def _episode_stat_inputs(extreme: EpisodeAgg) -> tuple[np.ndarray, ...]:
    sum_dr = extreme.sign * extreme.sum_r
    sum_d = extreme.sign * extreme.cnt
    sum_dmcr = sum_dr - extreme.sum_cr
    is_top = extreme.sign > 0
    is_bottom = extreme.sign < 0
    return (
        sum_dr,
        sum_d,
        sum_dmcr,
        extreme.cnt,
        extreme.sum_r * is_top,
        extreme.cnt * is_top,
        extreme.sum_r * is_bottom,
        extreme.cnt * is_bottom,
    )


def _stat_values(
    sum_dr: Any,
    sum_d: Any,
    sum_dmcr: Any,
    n_ext: Any,
    sum_r_top: Any,
    n_top: Any,
    sum_r_bottom: Any,
    n_bottom: Any,
    sum_mid_r: Any,
    n_mid: Any,
) -> dict[str, Any]:
    with np.errstate(invalid="ignore", divide="ignore"):
        mu_mid = sum_mid_r / n_mid
        neutral = sum_dr / n_ext - mu_mid * (sum_d / n_ext)
        control = sum_dmcr / n_ext
        top_excess = np.where(np.asarray(n_top) > 0, sum_r_top / n_top - mu_mid, np.nan)
        bottom_excess = np.where(
            np.asarray(n_bottom) > 0, mu_mid - sum_r_bottom / n_bottom, np.nan
        )
    return {
        "neutral": neutral,
        "control": control,
        "top_excess": top_excess,
        "bottom_excess": bottom_excess,
    }


def _floor_ok(counts: dict[str, dict[str, int]], state: str, segment: str) -> bool:
    min_rows = MIN_ROWS_TRAIN if segment == "Train" else MIN_ROWS_TEST
    min_eps = MIN_EPISODES_TRAIN if segment == "Train" else MIN_EPISODES_TEST
    return counts[state]["rows"] >= min_rows and counts[state]["episodes"] >= min_eps


def _contrast_adjudicable(
    counts: dict[str, dict[str, int]],
    contrast: str,
    segment: str,
) -> bool:
    extremes_ok = all(_floor_ok(counts, state, segment) for state in EXTREME_BUCKETS)
    if contrast == "neutral":
        return extremes_ok and _floor_ok(counts, "middle", segment)
    return extremes_ok


def replicates(
    metrics: dict[tuple[str, str], dict[str, Any]],
    instrument: str,
    timeframe: str,
    contrast: str,
    horizon: str,
) -> bool | None:
    """Return the frozen E5 replication flag for one cell/contrast/horizon."""
    cell = metrics[(instrument, timeframe)]
    train = cell["seg_horizon"][("Train", horizon)]
    test = cell["seg_horizon"][("Test", horizon)]
    if not (
        _contrast_adjudicable(train["counts"], contrast, "Train")
        and _contrast_adjudicable(test["counts"], contrast, "Test")
    ):
        return None
    train_pt = train["boot"][contrast]["point"]
    test_lo = test["boot"][contrast]["ci_lower"]
    if not (np.isfinite(train_pt) and np.isfinite(test_lo)):
        return None
    return bool(test_lo > 0.0 and train_pt > 0.0)


def _passing_instruments(
    metrics: dict[tuple[str, str], dict[str, Any]],
    contrasts: tuple[str, ...],
    horizon: str,
) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for timeframe in TIMEFRAMES:
        passing = []
        for instrument in INSTRUMENTS:
            flags = [replicates(metrics, instrument, timeframe, c, horizon) for c in contrasts]
            if all(flag is True for flag in flags):
                passing.append(instrument)
        out[timeframe] = passing
    return out


def _adjudicable_instruments(
    metrics: dict[tuple[str, str], dict[str, Any]],
    contrast: str,
    horizon: str,
) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for timeframe in TIMEFRAMES:
        out[timeframe] = [
            instrument
            for instrument in INSTRUMENTS
            if replicates(metrics, instrument, timeframe, contrast, horizon) is not None
        ]
    return out


def _gap_summary(frame: pd.DataFrame, period_minutes: int) -> dict[str, float]:
    eligible = frame["RetNextBar"].notna()
    gaps = frame.loc[eligible, "EntryGapMin"].to_numpy(dtype=float)
    gaps = gaps[np.isfinite(gaps)]
    if gaps.size == 0:
        return {
            "median_gap_min": float("nan"),
            "max_gap_min": float("nan"),
            "gap_spanning_share": float("nan"),
        }
    return {
        "median_gap_min": float(np.median(gaps)),
        "max_gap_min": float(np.max(gaps)),
        "gap_spanning_share": float(np.mean(gaps > period_minutes)),
    }


def make_null_cells(
    observed_cells: dict[tuple[str, str], CellFeature],
    block_length: int,
    seed_index: int,
) -> dict[tuple[str, str], CellFeature]:
    """Create one null realization with independent descriptor/return streams."""
    plans = _return_sampling_plans(observed_cells, block_length, seed_index)
    null_cells: dict[tuple[str, str], CellFeature] = {}
    for key, cell in observed_cells.items():
        parts = []
        for segment in SEGMENTS:
            segment_frame = cell.frame[cell.frame["Segment"] == segment].reset_index(drop=True)
            if segment_frame.empty:
                continue
            desc_idx = _descriptor_indices(segment_frame, seed_index, key, segment)
            ret_idx = _apply_return_plan(len(segment_frame), plans[(cell.timeframe, segment)])
            parts.append(_pair_null_segment(segment_frame, desc_idx, ret_idx, segment))
        frame = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=CELL_COLUMNS)
        null_cells[key] = CellFeature(cell.instrument, cell.timeframe, frame[CELL_COLUMNS])
    return null_cells


def _return_sampling_plans(
    observed_cells: dict[tuple[str, str], CellFeature],
    block_length: int,
    seed_index: int,
) -> dict[tuple[str, str], tuple[np.ndarray, np.ndarray]]:
    rng = np.random.default_rng(880_000 + seed_index * 1009 + block_length * 17)
    plans: dict[tuple[str, str], tuple[np.ndarray, np.ndarray]] = {}
    for timeframe in TIMEFRAMES:
        for segment in SEGMENTS:
            max_len = max(
                len(cell.frame[cell.frame["Segment"] == segment])
                for key, cell in observed_cells.items()
                if key[1] == timeframe
            )
            restart = rng.random(max_len) < (1.0 / float(block_length))
            if max_len:
                restart[0] = True
            starts = rng.integers(0, max(max_len, 1), size=max_len)
            plans[(timeframe, segment)] = (restart, starts)
    return plans


def _apply_return_plan(n_rows: int, plan: tuple[np.ndarray, np.ndarray]) -> np.ndarray:
    restart, starts = plan
    if n_rows == 0:
        return np.zeros(0, dtype=np.int64)
    out = np.zeros(n_rows, dtype=np.int64)
    current = 0
    for i in range(n_rows):
        if i == 0 or bool(restart[i]):
            current = int(starts[i] % n_rows)
        out[i] = current
        current = (current + 1) % n_rows
    return out


def _descriptor_indices(
    segment_frame: pd.DataFrame,
    seed_index: int,
    key: tuple[str, str],
    segment: str,
) -> np.ndarray:
    blocks = _descriptor_blocks(segment_frame["Bucket"])
    if not blocks:
        return np.arange(len(segment_frame), dtype=np.int64)
    offset = (INSTRUMENTS.index(key[0]) * 101) + (list(TIMEFRAMES).index(key[1]) * 17)
    offset += SEGMENTS.index(segment) * 7
    rng = np.random.default_rng(440_000 + seed_index * 977 + offset)
    selected: list[int] = []
    while len(selected) < len(segment_frame):
        block = blocks[int(rng.integers(0, len(blocks)))]
        selected.extend(block.tolist())
    return np.asarray(selected[: len(segment_frame)], dtype=np.int64)


def _descriptor_blocks(buckets: pd.Series) -> list[np.ndarray]:
    values = buckets.to_numpy(dtype=object)
    blocks: list[list[int]] = []
    current: list[int] = []
    previous = object()
    for idx, value in enumerate(values):
        new_block = _is_null_bucket(value) or value != previous
        if new_block and current:
            blocks.append(current)
            current = []
        current.append(idx)
        previous = object() if _is_null_bucket(value) else value
    if current:
        blocks.append(current)
    return [np.asarray(block, dtype=np.int64) for block in blocks]


def _pair_null_segment(
    segment_frame: pd.DataFrame,
    desc_idx: np.ndarray,
    ret_idx: np.ndarray,
    segment: str,
) -> pd.DataFrame:
    desc = segment_frame.iloc[desc_idx][["Bucket", "D"]].reset_index(drop=True)
    ret = segment_frame.iloc[ret_idx][
        ["CloseTime", "Control", "RetNextBar", "RetFourBar", "EntryGapMin", "HoldSpanMin"]
    ].reset_index(drop=True)
    paired = pd.concat([ret, desc], axis=1)
    paired["Segment"] = segment
    return paired[CELL_COLUMNS]


def run_null_realization(
    observed_cells: dict[tuple[str, str], CellFeature],
    observed_diag: dict[str, Any],
    block_length: int,
    seed_index: int,
) -> NullResult:
    """Generate a null realization, run diagnostics, then run the frozen stack."""
    cells = make_null_cells(observed_cells, block_length, seed_index)
    diagnostics = null_diagnostics(observed_diag, cells, block_length, seed_index)
    metrics = stack_metrics(cells, seed_index=seed_index)
    verdict = frozen_stack_verdict(metrics)
    return NullResult(cells=cells, diagnostics=diagnostics, metrics=metrics, verdict=verdict)


def observed_diagnostics(cells: dict[tuple[str, str], CellFeature]) -> dict[str, Any]:
    """Compute observed structures used as null-diagnostic references."""
    descriptor = _descriptor_diagnostics(cells)
    autocorr = _return_autocorr_signs(cells)
    cross_corr = _cross_instrument_correlations(cells)
    return {"descriptor": descriptor, "autocorr": autocorr, "cross_corr": cross_corr}


def null_diagnostics(
    observed: dict[str, Any],
    null_cells: dict[tuple[str, str], CellFeature],
    block_length: int,
    seed_index: int,
) -> dict[str, Any]:
    descriptor = _descriptor_diagnostics(null_cells)
    autocorr = _return_autocorr_signs(null_cells)
    cross_corr = _cross_instrument_correlations(null_cells)
    desc_summary = _descriptor_diagnostic_compare(observed["descriptor"], descriptor)
    auto_summary = _autocorr_compare(observed["autocorr"], autocorr)
    corr_summary = _cross_corr_compare(observed["cross_corr"], cross_corr)
    return {
        "block_length": block_length,
        "seed_index": seed_index,
        "descriptor_pass": desc_summary["pass"],
        "return_autocorr_pass": auto_summary["pass"],
        "cross_corr_pass": corr_summary["pass"],
        "trusted": bool(desc_summary["pass"] and auto_summary["pass"] and corr_summary["pass"]),
        **desc_summary,
        **auto_summary,
        **corr_summary,
    }


def _descriptor_diagnostics(cells: dict[tuple[str, str], CellFeature]) -> dict[tuple[str, str, str], Any]:
    out: dict[tuple[str, str, str], Any] = {}
    for (instrument, timeframe), cell in cells.items():
        for segment in SEGMENTS:
            frame = cell.frame[cell.frame["Segment"] == segment].reset_index(drop=True)
            lengths = _episode_lengths(frame["Bucket"])
            out[(instrument, timeframe, segment)] = {
                "episode_count": int(len(lengths)),
                "median_length": float(np.median(lengths)) if lengths.size else float("nan"),
                "p90_length": float(np.quantile(lengths, 0.90)) if lengths.size else float("nan"),
            }
    return out


def _episode_lengths(buckets: pd.Series) -> np.ndarray:
    blocks = [block for block in _descriptor_blocks(buckets) if not _block_is_null(buckets, block)]
    return np.asarray([len(block) for block in blocks], dtype=float)


def _block_is_null(buckets: pd.Series, block: np.ndarray) -> bool:
    if len(block) == 0:
        return True
    return _is_null_bucket(buckets.iloc[int(block[0])])


def _descriptor_diagnostic_compare(
    observed: dict[tuple[str, str, str], Any],
    null: dict[tuple[str, str, str], Any],
) -> dict[str, Any]:
    max_count_rel = 0.0
    max_median_rel = 0.0
    max_p90_rel = 0.0
    failures = 0
    for key, obs in observed.items():
        cur = null[key]
        count_rel = _relative_diff(cur["episode_count"], obs["episode_count"])
        median_rel = _relative_diff(cur["median_length"], obs["median_length"])
        p90_rel = _relative_diff(cur["p90_length"], obs["p90_length"])
        max_count_rel = max(max_count_rel, count_rel)
        max_median_rel = max(max_median_rel, median_rel)
        max_p90_rel = max(max_p90_rel, p90_rel)
        if count_rel > DESCRIPTOR_COUNT_TOL or max(median_rel, p90_rel) > DESCRIPTOR_LENGTH_TOL:
            failures += 1
    return {
        "pass": failures == 0,
        "descriptor_failed_cells": failures,
        "descriptor_max_count_rel_diff": max_count_rel,
        "descriptor_max_median_rel_diff": max_median_rel,
        "descriptor_max_p90_rel_diff": max_p90_rel,
    }


def _relative_diff(value: float, baseline: float) -> float:
    if not np.isfinite(value) or not np.isfinite(baseline):
        return float("inf")
    if baseline == 0:
        return 0.0 if value == 0 else float("inf")
    return float(abs(value - baseline) / abs(baseline))


def _return_autocorr_signs(cells: dict[tuple[str, str], CellFeature]) -> dict[tuple[str, str, str, str, int], int]:
    out: dict[tuple[str, str, str, str, int], int] = {}
    for (instrument, timeframe), cell in cells.items():
        for segment in SEGMENTS:
            frame = cell.frame[cell.frame["Segment"] == segment]
            for horizon, ret_col in (("next_bar", "RetNextBar"), ("four_bar", "RetFourBar")):
                returns = frame[ret_col].to_numpy(dtype=float)
                for lag in (1, 5):
                    out[(instrument, timeframe, segment, horizon, lag)] = _autocorr_sign(returns, lag)
    return out


def _autocorr_sign(values: np.ndarray, lag: int) -> int:
    values = values[np.isfinite(values)]
    if values.size <= lag + 2:
        return 0
    corr = np.corrcoef(values[:-lag], values[lag:])[0, 1]
    if not np.isfinite(corr) or abs(corr) < 1e-12:
        return 0
    return 1 if corr > 0 else -1


def _autocorr_compare(
    observed: dict[tuple[str, str, str, str, int], int],
    null: dict[tuple[str, str, str, str, int], int],
) -> dict[str, Any]:
    mismatches = sum(1 for key, sign in observed.items() if null.get(key, 0) != sign)
    total = len(observed)
    return {
        "pass": mismatches == 0,
        "autocorr_sign_mismatches": mismatches,
        "autocorr_sign_match_rate": None if total == 0 else 1.0 - mismatches / total,
    }


def _cross_instrument_correlations(
    cells: dict[tuple[str, str], CellFeature],
) -> dict[tuple[str, str, str], np.ndarray]:
    out: dict[tuple[str, str, str], np.ndarray] = {}
    for timeframe in TIMEFRAMES:
        for segment in SEGMENTS:
            for horizon, ret_col in (("next_bar", "RetNextBar"), ("four_bar", "RetFourBar")):
                series = [
                    cells[(instrument, timeframe)]
                    .frame.query("Segment == @segment")[ret_col]
                    .to_numpy(dtype=float)
                    for instrument in INSTRUMENTS
                ]
                out[(timeframe, segment, horizon)] = _safe_corr_matrix(series)
    return out


def _safe_corr_matrix(series: list[np.ndarray]) -> np.ndarray:
    min_len = min((np.isfinite(x).sum() for x in series), default=0)
    if min_len < 3:
        return np.eye(len(series))
    trimmed = []
    for values in series:
        finite = values[np.isfinite(values)]
        trimmed.append(finite[:min_len])
    matrix = np.corrcoef(np.vstack(trimmed))
    return np.nan_to_num(matrix, nan=0.0, posinf=0.0, neginf=0.0)


def _cross_corr_compare(
    observed: dict[tuple[str, str, str], np.ndarray],
    null: dict[tuple[str, str, str], np.ndarray],
) -> dict[str, Any]:
    max_distance = 0.0
    failures = 0
    for key, obs in observed.items():
        distance = float(np.linalg.norm(null[key] - obs, ord="fro"))
        max_distance = max(max_distance, distance)
        if distance > CROSS_CORR_FROBENIUS_MAX:
            failures += 1
    return {
        "pass": failures == 0,
        "cross_corr_failed_matrices": failures,
        "cross_corr_max_frobenius": max_distance,
    }


def metrics_rows(
    metrics: dict[tuple[str, str], dict[str, Any]],
    block_length: int | None = None,
    seed_index: int | None = None,
    battery: str | None = None,
    trusted: bool | None = None,
) -> pd.DataFrame:
    """Flatten frozen-stack metrics into a long table."""
    rows: list[dict[str, Any]] = []
    for (instrument, timeframe), cell in metrics.items():
        for (segment, horizon), metric in cell["seg_horizon"].items():
            row: dict[str, Any] = {
                "Instrument": instrument,
                "Timeframe": timeframe,
                "Segment": segment,
                "Horizon": horizon,
                "MuMid": metric["mu_mid"],
                "BlockLength": block_length,
                "SeedIndex": seed_index,
                "Battery": battery,
                "Trusted": trusted,
            }
            for state in ("top", "bottom", "middle"):
                row[f"Rows_{state}"] = metric["counts"][state]["rows"]
                row[f"Eps_{state}"] = metric["counts"][state]["episodes"]
            for stat, values in metric["boot"].items():
                row[f"{stat}_pt"] = values["point"]
                row[f"{stat}_lo"] = values["ci_lower"]
                row[f"{stat}_hi"] = values["ci_upper"]
            for contrast in CONTRASTS:
                row[f"{contrast}_adjudicable"] = _contrast_adjudicable(
                    metric["counts"], contrast, segment
                )
            rows.append(row)
    return pd.DataFrame(rows)


def cell_pass_rows(
    metrics: dict[tuple[str, str], dict[str, Any]],
    block_length: int,
    seed_index: int,
    battery: str,
    trusted: bool,
) -> pd.DataFrame:
    """Return one row per cell/contrast/horizon replication decision."""
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        for timeframe in TIMEFRAMES:
            for horizon in HORIZONS:
                flags = {
                    contrast: replicates(metrics, instrument, timeframe, contrast, horizon)
                    for contrast in CONTRASTS
                }
                for contrast, flag in flags.items():
                    rows.append(
                        _cell_pass_row(
                            block_length, seed_index, battery, trusted,
                            instrument, timeframe, horizon, contrast, flag,
                        )
                    )
                both = None if any(flag is None for flag in flags.values()) else all(flags.values())
                rows.append(
                    _cell_pass_row(
                        block_length, seed_index, battery, trusted,
                        instrument, timeframe, horizon, "both", both,
                    )
                )
    return pd.DataFrame(rows)


def _cell_pass_row(
    block_length: int,
    seed_index: int,
    battery: str,
    trusted: bool,
    instrument: str,
    timeframe: str,
    horizon: str,
    contrast: str,
    flag: bool | None,
) -> dict[str, Any]:
    return {
        "BlockLength": block_length,
        "SeedIndex": seed_index,
        "Battery": battery,
        "Trusted": trusted,
        "Instrument": instrument,
        "Timeframe": timeframe,
        "Horizon": horizon,
        "Contrast": contrast,
        "Adjudicable": flag is not None,
        "FalsePass": bool(flag) if flag is not None else None,
    }


def realization_row(
    block_length: int,
    seed_index: int,
    diagnostics: dict[str, Any],
    verdict: dict[str, Any],
    runtime_seconds: float,
) -> dict[str, Any]:
    """Summarize one full-stack equivalent realization."""
    battery = battery_partition(seed_index)
    return {
        "BlockLength": block_length,
        "SeedIndex": seed_index,
        "Battery": battery,
        "Trusted": bool(diagnostics["trusted"] and battery == "second_order"),
        "DiagnosticsPass": bool(diagnostics["trusted"]),
        "DescriptorPass": bool(diagnostics["descriptor_pass"]),
        "ReturnAutocorrPass": bool(diagnostics["return_autocorr_pass"]),
        "CrossCorrPass": bool(diagnostics["cross_corr_pass"]),
        "Outcome": verdict["outcome"],
        "FullStackFOR": bool(verdict["full_stack_for"]),
        "NextBarBothMax": verdict["next_bar_both_max"],
        "NextBarNeutralMax": verdict["next_bar_neutral_max"],
        "FourBarBothMax": verdict["four_bar_both_max"],
        "NextBarControlAdjudicableMax": verdict["next_bar_control_adjudicable_max"],
        "RuntimeSeconds": runtime_seconds,
        **_diagnostic_scalar_subset(diagnostics),
    }


def _diagnostic_scalar_subset(diagnostics: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "descriptor_failed_cells",
        "descriptor_max_count_rel_diff",
        "descriptor_max_median_rel_diff",
        "descriptor_max_p90_rel_diff",
        "autocorr_sign_mismatches",
        "autocorr_sign_match_rate",
        "cross_corr_failed_matrices",
        "cross_corr_max_frobenius",
    ]
    return {key: diagnostics.get(key) for key in keys}


def battery_partition(seed_index: int) -> str:
    """Calibration battery partition fixed by reference-stack spec."""
    return "development" if seed_index % 2 == 0 else "second_order"


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float | None, float | None]:
    """Wilson interval for a binomial proportion."""
    if total <= 0:
        return None, None
    p = successes / total
    denom = 1.0 + z * z / total
    center = (p + z * z / (2.0 * total)) / denom
    half = z * np.sqrt((p * (1.0 - p) + z * z / (4.0 * total)) / total) / denom
    return float(max(0.0, center - half)), float(min(1.0, center + half))


def summarize_verdict_rates(realizations: pd.DataFrame) -> pd.DataFrame:
    """Aggregate verdict and full-stack FPR rates."""
    rows: list[dict[str, Any]] = []
    for (block_length, battery), group in realizations.groupby(["BlockLength", "Battery"]):
        for rate_set, data in _rate_sets(group):
            for outcome in ("FOR", "STATE_DIFFERENTIATION_ONLY", "HORIZON_DEPENDENT", "INCONCLUSIVE", "AGAINST"):
                rows.append(
                    _proportion_row(
                        block_length, battery, rate_set, f"verdict_{outcome}",
                        int((data["Outcome"] == outcome).sum()), len(data),
                    )
                )
            rows.append(
                _proportion_row(
                    block_length, battery, rate_set, "full_stack_fpr",
                    int(data["FullStackFOR"].sum()), len(data),
                )
            )
    return pd.DataFrame(rows)


def _rate_sets(group: pd.DataFrame) -> Iterable[tuple[str, pd.DataFrame]]:
    yield "all_realizations", group
    yield "diagnostic_pass", group[group["DiagnosticsPass"]]
    if (group["Battery"] == "second_order").all():
        yield "trusted_second_order", group[group["Trusted"]]


def summarize_cell_pass_rates(cell_passes: pd.DataFrame) -> pd.DataFrame:
    """Aggregate cell-level false-pass rates."""
    rows: list[dict[str, Any]] = []
    keys = ["BlockLength", "Battery", "Horizon", "Contrast"]
    for group_key, group in cell_passes.groupby(keys):
        block_length, battery, horizon, contrast = group_key
        for rate_set, data in _cell_rate_sets(group):
            adjudicable = data[data["Adjudicable"]]
            successes = int(adjudicable["FalsePass"].fillna(False).sum())
            total = int(len(adjudicable))
            row = _proportion_row(
                block_length, battery, rate_set, f"{horizon}_{contrast}_cell_false_pass",
                successes, total,
            )
            row.update({"Horizon": horizon, "Contrast": contrast})
            rows.append(row)
    return pd.DataFrame(rows)


def _cell_rate_sets(group: pd.DataFrame) -> Iterable[tuple[str, pd.DataFrame]]:
    yield "all_realizations", group
    yield "diagnostic_pass", group[group["Trusted"] | (group["Battery"] == "development")]
    if (group["Battery"] == "second_order").all():
        yield "trusted_second_order", group[group["Trusted"]]


def _proportion_row(
    block_length: int,
    battery: str,
    rate_set: str,
    metric: str,
    successes: int,
    total: int,
) -> dict[str, Any]:
    lo, hi = wilson_interval(successes, total)
    return {
        "BlockLength": block_length,
        "Battery": battery,
        "RateSet": rate_set,
        "Metric": metric,
        "Successes": successes,
        "Denominator": total,
        "Rate": None if total == 0 else successes / total,
        "Wilson95Lower": lo,
        "Wilson95Upper": hi,
    }


def json_safe(value: Any) -> Any:
    """Convert numpy/pandas scalars to JSON-safe Python values."""
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if pd.isna(value):
        return None
    return value
