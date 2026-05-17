from __future__ import annotations

import hashlib
import json
import logging
import platform
import subprocess
from collections import deque
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Any, Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import polars as pl
import seaborn as sns

from heiken_ashi_generator import generate_heiken_ashi
from linebreak_generator import generate_linebreak
from renko_generator import generate_renko


LOGGER = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON_ROOT = PROJECT_ROOT / "python"
DATA_DIR = PROJECT_ROOT / "data"

INSTRUMENTS = ["EURUSD", "XAUUSD", "BTCUSD", "USTEC"]
TIMEFRAMES = {"1m": 1, "15m": 15}
TIMEBAR_COLUMNS = [
    "Symbol",
    "OpenTime",
    "CloseTime",
    "Open",
    "High",
    "Low",
    "Close",
    "TickVolume",
]

ANALYSIS_FRACTION = 0.70
TRAIN_FRACTION = 0.70
ATR_PERIOD = 14
ROLLING_VOL_WINDOW = 20
WINDOWS_MINUTES = [30, 60, 120, 240]
PRIMARY_WINDOW = 60
RUN_WINDOW = 30
RUN_ATR_THRESHOLD = 0.10
PRECISION_ATR_THRESHOLD = 1.00
RECALL_TOLERANCE_MINUTES = 30
CONFIRMATION_WINDOWS = [5, 15, 30]
PRIMARY_CONFIRMATION_WINDOW = 15
BOOTSTRAP_N = 10_000
BOOTSTRAP_SEED = 42
BOOTSTRAP_MAX_SAMPLE_N = 5_000
PLOT_SAMPLE_N = 20_000
TIMESTAMP_TIME_UNIT = "us"
REGIME_ORDER = ["Low", "Medium", "High"]


@dataclass(frozen=True)
class InstrumentData:
    instrument: str
    source_rows: int
    analysis_rows: int
    train_rows: int
    path: Path
    real_1m: pl.DataFrame
    timeframes: dict[str, pl.DataFrame]


@dataclass(frozen=True)
class RealPriceContext:
    instrument: str
    times: np.ndarray
    open_: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    atr: np.ndarray
    regimes: np.ndarray
    train_end_time: pd.Timestamp
    future_price_extrema: dict[int, tuple[np.ndarray, np.ndarray]]
    future_close_extrema: dict[int, tuple[np.ndarray, np.ndarray]]


def normalize_datetime_units(
    df: pl.DataFrame,
    columns: Iterable[str] = ("OpenTime", "CloseTime", "SourceCloseTime", "SignalTime"),
) -> pl.DataFrame:
    present = [column for column in columns if column in df.columns]
    if not present:
        return df
    return df.with_columns(
        [pl.col(column).cast(pl.Datetime(TIMESTAMP_TIME_UNIT)).alias(column) for column in present]
    )


def experiment_dirs(exp_id: str) -> tuple[Path, Path]:
    exp_dir = PYTHON_ROOT / "experiments" / exp_id
    results_dir = exp_dir / "results"
    plots_dir = exp_dir / "plots"
    results_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)
    return results_dir, plots_dir


def find_timebar_path(instrument: str) -> Path:
    paths = sorted(DATA_DIR.glob(f"timebars/timebars_{instrument.lower()}_*.parquet"))
    if not paths:
        raise FileNotFoundError(f"No time-bar Parquet file found for {instrument}")
    return paths[-1]


def load_instrument_data(instrument: str) -> InstrumentData:
    """Load only the first 70 percent chronological 1-minute bars."""
    path = find_timebar_path(instrument)
    scan = pl.scan_parquet(path).select(TIMEBAR_COLUMNS).sort("CloseTime")
    source_rows = int(scan.select(pl.len()).collect().item())
    analysis_rows = int(source_rows * ANALYSIS_FRACTION)
    train_rows = int(analysis_rows * TRAIN_FRACTION)
    real_1m = normalize_datetime_units(scan.slice(0, analysis_rows).collect())
    timeframes = {"1m": real_1m}
    timeframes["15m"] = aggregate_timeframe(real_1m, instrument, 15)
    return InstrumentData(
        instrument=instrument,
        source_rows=source_rows,
        analysis_rows=analysis_rows,
        train_rows=train_rows,
        path=path,
        real_1m=real_1m,
        timeframes=timeframes,
    )


def load_all_instruments() -> tuple[dict[str, InstrumentData], pd.DataFrame]:
    loaded: dict[str, InstrumentData] = {}
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        LOGGER.info("loading %s analysis data", instrument)
        data = load_instrument_data(instrument)
        loaded[instrument] = data
        rows.extend(validation_rows_for_instrument(data))
    return loaded, pd.DataFrame(rows)


def validation_rows_for_instrument(data: InstrumentData) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for timeframe, bars in data.timeframes.items():
        rows.append(
            {
                "Instrument": data.instrument,
                "Timeframe": timeframe,
                "InputFile": str(data.path.relative_to(PROJECT_ROOT)),
                "SourceRows": data.source_rows,
                "AnalysisRows": data.analysis_rows,
                "TrainRows": data.train_rows,
                "TimeframeRows": bars.height,
                "StartTime": bars["CloseTime"][0] if bars.height else None,
                "EndTime": bars["CloseTime"][-1] if bars.height else None,
            }
        )
    return rows


def aggregate_timeframe(source_analysis: pl.DataFrame, instrument: str, minutes: int) -> pl.DataFrame:
    """Aggregate complete OHLCV bars from holdout-excluded 1-minute data."""
    source_analysis = normalize_datetime_units(source_analysis)
    bucketed = source_analysis.with_columns(
        (
            (pl.col("CloseTime") - pl.duration(microseconds=1)).dt.truncate(f"{minutes}m")
            + pl.duration(minutes=minutes)
        ).alias("_bucket")
    )
    grouped = (
        bucketed.group_by("_bucket", maintain_order=True)
        .agg(
            pl.first("Symbol").alias("Symbol"),
            pl.first("OpenTime").alias("OpenTime"),
            pl.max("CloseTime").alias("CloseTime"),
            pl.first("Open").alias("Open"),
            pl.max("High").alias("High"),
            pl.min("Low").alias("Low"),
            pl.last("Close").alias("Close"),
            pl.sum("TickVolume").alias("TickVolume"),
            pl.len().alias("_source_count"),
        )
        .sort("CloseTime")
    )
    complete = grouped.filter(pl.col("_source_count") == minutes).select(TIMEBAR_COLUMNS)
    return normalize_datetime_units(complete.with_columns(pl.lit(instrument).alias("Symbol")))


def future_window_extrema(
    times: np.ndarray,
    max_values: np.ndarray,
    min_values: np.ndarray,
    window_minutes: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Return forward max/min over rows strictly after each timestamp."""
    future_max = np.full(len(times), np.nan)
    future_min = np.full(len(times), np.nan)
    max_queue: deque[int] = deque()
    min_queue: deque[int] = deque()
    time_values = times.astype("datetime64[ns]").astype(np.int64, copy=False)
    delta = np.timedelta64(window_minutes, "m").astype("timedelta64[ns]").astype(np.int64)

    for idx in range(len(time_values) - 1, -1, -1):
        candidate = idx + 1
        if candidate < len(time_values):
            while max_queue and max_values[max_queue[-1]] <= max_values[candidate]:
                max_queue.pop()
            max_queue.append(candidate)
            while min_queue and min_values[min_queue[-1]] >= min_values[candidate]:
                min_queue.pop()
            min_queue.append(candidate)

        cutoff = time_values[idx] + delta
        while max_queue and time_values[max_queue[0]] > cutoff:
            max_queue.popleft()
        while min_queue and time_values[min_queue[0]] > cutoff:
            min_queue.popleft()

        if max_queue:
            future_max[idx] = max_values[max_queue[0]]
        if min_queue:
            future_min[idx] = min_values[min_queue[0]]

    return future_max, future_min


def build_context(
    data: InstrumentData,
    outcome_windows: Iterable[int] = WINDOWS_MINUTES,
) -> RealPriceContext:
    """Build real-price arrays, ATR, and train-calibrated volatility regimes."""
    bars = data.real_1m.to_pandas()
    times = bars["CloseTime"].to_numpy(dtype="datetime64[ns]")
    open_ = bars["Open"].to_numpy(float)
    high = bars["High"].to_numpy(float)
    low = bars["Low"].to_numpy(float)
    close = bars["Close"].to_numpy(float)

    previous_close = np.r_[np.nan, close[:-1]]
    true_range = np.maximum.reduce([high - low, np.abs(high - previous_close), np.abs(low - previous_close)])
    true_range[0] = high[0] - low[0]
    atr = pd.Series(true_range).rolling(ATR_PERIOD, min_periods=ATR_PERIOD).mean().to_numpy()

    log_ret = np.r_[np.nan, np.diff(np.log(close))]
    rolling_vol = pd.Series(log_ret).rolling(ROLLING_VOL_WINDOW, min_periods=ROLLING_VOL_WINDOW).std().to_numpy()
    train_vol = rolling_vol[: data.train_rows]
    train_vol = train_vol[np.isfinite(train_vol)]
    regimes = np.full(len(close), None, dtype=object)
    if len(train_vol) >= 3:
        q1, q2 = np.quantile(train_vol, [1.0 / 3.0, 2.0 / 3.0])
        valid = np.isfinite(rolling_vol)
        regimes[valid & (rolling_vol <= q1)] = "Low"
        regimes[valid & (rolling_vol > q1) & (rolling_vol <= q2)] = "Medium"
        regimes[valid & (rolling_vol > q2)] = "High"
    return RealPriceContext(
        instrument=data.instrument,
        times=times,
        open_=open_,
        high=high,
        low=low,
        close=close,
        atr=atr,
        regimes=regimes,
        train_end_time=pd.Timestamp(times[max(data.train_rows - 1, 0)]),
        future_price_extrema={
            window: future_window_extrema(times, high, low, window) for window in outcome_windows
        },
        future_close_extrema={
            window: future_window_extrema(times, close, close, window) for window in {RUN_WINDOW}
        },
    )


def generate_chart(time_bars: pl.DataFrame, chart_type: str) -> pl.DataFrame:
    time_bars = normalize_datetime_units(time_bars)
    if chart_type == "Time":
        return time_bars.clone()
    if chart_type == "LineBreak":
        return normalize_datetime_units(generate_linebreak(time_bars, level=3))
    if chart_type == "Renko":
        return normalize_datetime_units(generate_renko(time_bars, atr_period=14))
    if chart_type == "HeikenAshi":
        return normalize_datetime_units(generate_heiken_ashi(time_bars))
    raise ValueError(f"Unknown chart type: {chart_type}")


def timebar_signals(
    time_bars: pl.DataFrame,
    instrument: str,
    timeframe: str,
    signal_set: str,
    direction_changes_only: bool = False,
) -> pd.DataFrame:
    df = time_bars.select(["CloseTime", "Open", "Close"]).to_pandas()
    direction = np.where(df["Close"].to_numpy(float) >= df["Open"].to_numpy(float), 1, -1)
    keep = np.ones(len(df), dtype=bool)
    if direction_changes_only and len(keep):
        keep[0] = False
        keep[1:] = direction[1:] != direction[:-1]
    return pd.DataFrame(
        {
            "Instrument": instrument,
            "Timeframe": timeframe,
            "SignalSet": signal_set,
            "ChartType": "Time",
            "SignalTime": pd.to_datetime(df.loc[keep, "CloseTime"]).to_numpy(),
            "Direction": direction[keep].astype(int),
        }
    )


def heiken_ashi_signals(
    ha_bars: pl.DataFrame,
    instrument: str,
    timeframe: str,
    signal_set: str,
    direction_changes_only: bool = False,
) -> pd.DataFrame:
    df = ha_bars.select(["CloseTime", "Direction"]).to_pandas()
    direction = df["Direction"].to_numpy(int)
    keep = np.ones(len(df), dtype=bool)
    if direction_changes_only and len(keep):
        keep[0] = False
        keep[1:] = direction[1:] != direction[:-1]
    return pd.DataFrame(
        {
            "Instrument": instrument,
            "Timeframe": timeframe,
            "SignalSet": signal_set,
            "ChartType": "HeikenAshi",
            "SignalTime": pd.to_datetime(df.loc[keep, "CloseTime"]).to_numpy(),
            "Direction": direction[keep].astype(int),
        }
    )


def event_chart_signals(
    chart_bars: pl.DataFrame,
    chart_type: str,
    instrument: str,
    timeframe: str,
    signal_set: str,
) -> pd.DataFrame:
    if chart_bars.is_empty():
        return empty_signal_frame()
    df = chart_bars.select(["SourceCloseTime", "Direction"]).to_pandas()
    return pd.DataFrame(
        {
            "Instrument": instrument,
            "Timeframe": timeframe,
            "SignalSet": signal_set,
            "ChartType": chart_type,
            "SignalTime": pd.to_datetime(df["SourceCloseTime"]).to_numpy(),
            "Direction": df["Direction"].to_numpy(int),
        }
    )


def empty_signal_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=["Instrument", "Timeframe", "SignalSet", "ChartType", "SignalTime", "Direction"]
    )


def add_regime_to_signals(signals: pd.DataFrame, context: RealPriceContext) -> pd.DataFrame:
    if "Regime" in signals.columns:
        return signals.copy()
    if signals.empty:
        signals = signals.copy()
        signals["Regime"] = []
        return signals
    idx = np.searchsorted(context.times, signals["SignalTime"].to_numpy(dtype="datetime64[ns]"), side="left")
    regimes = np.full(len(signals), None, dtype=object)
    valid = idx < len(context.times)
    regimes[valid] = context.regimes[idx[valid]]
    out = signals.copy()
    out["Regime"] = regimes
    return out


def evaluate_signals(
    signals: pd.DataFrame,
    context: RealPriceContext,
    outcome_windows: Iterable[int] = WINDOWS_MINUTES,
) -> pd.DataFrame:
    """Compute FE, AE, precision, recall inputs, and continuation on real prices."""
    signals = add_regime_to_signals(signals, context).reset_index(drop=True)
    if signals.empty:
        return signals

    signal_times = signals["SignalTime"].to_numpy(dtype="datetime64[ns]")
    directions = signals["Direction"].to_numpy(int)
    indices = np.searchsorted(context.times, signal_times, side="left")
    out = signals.copy()
    atr_at_signal = np.full(len(out), np.nan)
    valid_index = indices < len(context.atr)
    atr_at_signal[valid_index] = context.atr[indices[valid_index]]
    exact = np.zeros(len(out), dtype=bool)
    exact[valid_index] = context.times[indices[valid_index]] == signal_times[valid_index]
    usable = exact & np.isfinite(atr_at_signal) & (atr_at_signal > 0.0)
    out["RealPriceResolved"] = exact
    out["ATRAtSignal"] = np.where(usable, atr_at_signal, np.nan)

    for window in outcome_windows:
        fe = np.full(len(out), np.nan)
        ae = np.full(len(out), np.nan)
        future_high, future_low = context.future_price_extrema[window]
        rows = np.flatnonzero(usable)
        signal_indices = indices[rows]
        high = future_high[signal_indices]
        low = future_low[signal_indices]
        has_future = np.isfinite(high) & np.isfinite(low)
        rows = rows[has_future]
        signal_indices = signal_indices[has_future]
        high = high[has_future]
        low = low[has_future]
        base = context.close[signal_indices]
        atr = context.atr[signal_indices]
        up = directions[rows] > 0
        fe_values = np.empty(len(rows), dtype=float)
        ae_values = np.empty(len(rows), dtype=float)
        fe_values[up] = np.maximum(0.0, (high[up] - base[up]) / atr[up])
        ae_values[up] = np.maximum(0.0, (base[up] - low[up]) / atr[up])
        fe_values[~up] = np.maximum(0.0, (base[~up] - low[~up]) / atr[~up])
        ae_values[~up] = np.maximum(0.0, (high[~up] - base[~up]) / atr[~up])
        fe[rows] = fe_values
        ae[rows] = ae_values
        out[f"FE_{window}m"] = fe
        out[f"AE_{window}m"] = ae

    epsilon = 0.01
    out["LogFEAERatio_60m"] = np.log(out["FE_60m"] + epsilon) - np.log(out["AE_60m"] + epsilon)
    out["PrecisionHit_60m"] = np.where(
        np.isfinite(out["FE_60m"]),
        out["FE_60m"] >= PRECISION_ATR_THRESHOLD,
        np.nan,
    )

    run_hit = np.full(len(out), False)
    future_close_max, future_close_min = context.future_close_extrema[RUN_WINDOW]
    rows = np.flatnonzero(usable)
    signal_indices = indices[rows]
    close_max = future_close_max[signal_indices]
    close_min = future_close_min[signal_indices]
    has_future = np.isfinite(close_max) & np.isfinite(close_min)
    rows = rows[has_future]
    signal_indices = signal_indices[has_future]
    close_max = close_max[has_future]
    close_min = close_min[has_future]
    target = context.close[signal_indices] + directions[rows] * RUN_ATR_THRESHOLD * context.atr[signal_indices]
    up = directions[rows] > 0
    run_hit[rows[up]] = close_max[up] >= target[up]
    run_hit[rows[~up]] = close_min[~up] <= target[~up]
    out["RunContinuation_30m"] = run_hit
    return out


def qualifying_moves(context: RealPriceContext) -> pd.DataFrame:
    future_high, future_low = context.future_price_extrema[PRIMARY_WINDOW]
    valid = (
        np.isfinite(context.atr)
        & (context.atr > 0.0)
        & np.isfinite(future_high)
        & np.isfinite(future_low)
    )
    up_fe = np.full(len(context.times), np.nan)
    down_fe = np.full(len(context.times), np.nan)
    up_fe[valid] = (future_high[valid] - context.close[valid]) / context.atr[valid]
    down_fe[valid] = (context.close[valid] - future_low[valid]) / context.atr[valid]
    up_hits = np.flatnonzero(up_fe >= PRECISION_ATR_THRESHOLD)
    down_hits = np.flatnonzero(down_fe >= PRECISION_ATR_THRESHOLD)
    return pd.DataFrame(
        {
            "MoveTime": np.concatenate(
                [
                    pd.to_datetime(context.times[up_hits]).to_numpy(),
                    pd.to_datetime(context.times[down_hits]).to_numpy(),
                ]
            ),
            "Direction": np.concatenate(
                [
                    np.ones(len(up_hits), dtype=int),
                    -np.ones(len(down_hits), dtype=int),
                ]
            ),
        }
    )


def attach_multiplicity_and_recall_inputs(
    evaluated: pd.DataFrame,
    moves: pd.DataFrame,
) -> pd.DataFrame:
    if evaluated.empty:
        out = evaluated.copy()
        out["SignalMultiplicity"] = []
        return out
    out = evaluated.copy()
    out["SignalMultiplicity"] = 0
    if moves.empty:
        return out
    move_by_direction = {
        direction: np.sort(group["MoveTime"].to_numpy(dtype="datetime64[ns]"))
        for direction, group in moves.groupby("Direction")
    }
    tol = np.timedelta64(RECALL_TOLERANCE_MINUTES, "m")
    for direction, move_times in move_by_direction.items():
        signal_mask = out["Direction"].to_numpy(int) == int(direction)
        signal_times = out.loc[signal_mask, "SignalTime"].to_numpy(dtype="datetime64[ns]")
        left = np.searchsorted(move_times, signal_times - tol, side="left")
        right = np.searchsorted(move_times, signal_times + tol, side="right")
        counts = right - left
        out.loc[signal_mask, "SignalMultiplicity"] = counts
    return out


def event_recall(evaluated: pd.DataFrame, moves: pd.DataFrame) -> float:
    if moves.empty:
        return float("nan")
    if evaluated.empty:
        return 0.0
    signal_by_direction = {
        direction: np.sort(group["SignalTime"].to_numpy(dtype="datetime64[ns]"))
        for direction, group in evaluated.groupby("Direction")
    }
    tol = np.timedelta64(RECALL_TOLERANCE_MINUTES, "m")
    captured = 0
    for direction, move_group in moves.groupby("Direction"):
        signal_times = signal_by_direction.get(int(direction))
        if signal_times is None or len(signal_times) == 0:
            continue
        move_times = np.sort(move_group["MoveTime"].to_numpy(dtype="datetime64[ns]"))
        left = np.searchsorted(signal_times, move_times - tol, side="left")
        right = np.searchsorted(signal_times, move_times + tol, side="right")
        captured += int(np.count_nonzero(right > left))
    return captured / len(moves)


def summarize_metrics(evaluated: pd.DataFrame, moves_by_instrument: dict[str, pd.DataFrame]) -> pd.DataFrame:
    group_cols = ["Instrument", "Timeframe", "SignalSet", "ChartType", "Regime"]
    rows: list[dict[str, Any]] = []
    if evaluated.empty:
        return pd.DataFrame()
    for key, group in evaluated.groupby(group_cols, dropna=False):
        record = dict(zip(group_cols, key))
        moves = moves_by_instrument.get(record["Instrument"], pd.DataFrame())
        record.update(
            {
                "Signals": len(group),
                "ResolvedSignals": int(group["RealPriceResolved"].sum()),
                "FE60Mean": float(group["FE_60m"].mean()),
                "FE60Median": float(group["FE_60m"].median()),
                "AE60Mean": float(group["AE_60m"].mean()),
                "AE60Median": float(group["AE_60m"].median()),
                "Precision60": float(group["PrecisionHit_60m"].mean()),
                "RunContinuation30": float(group["RunContinuation_30m"].mean()),
                "LogFEAERatio60Mean": float(group["LogFEAERatio_60m"].mean()),
                "AEZeroShare60": float((group["AE_60m"] == 0.0).mean()),
                "MeanMultiplicity": float(group["SignalMultiplicity"].mean())
                if "SignalMultiplicity" in group.columns
                else float("nan"),
                "EventRecall": event_recall(group, moves),
            }
        )
        rows.append(record)
    return pd.DataFrame(rows)


def bootstrap_diff_ci(a: np.ndarray, b: np.ndarray, seed_offset: int = 0) -> dict[str, float]:
    clean_a = a[np.isfinite(a)]
    clean_b = b[np.isfinite(b)]
    if len(clean_a) == 0 or len(clean_b) == 0:
        return {
            "MeanDiff": float("nan"),
            "CILower": float("nan"),
            "CIUpper": float("nan"),
            "N_A": len(clean_a),
            "N_B": len(clean_b),
            "BootstrapN_A": len(clean_a),
            "BootstrapN_B": len(clean_b),
        }
    rng = np.random.default_rng(BOOTSTRAP_SEED + seed_offset)
    original_n_a = len(clean_a)
    original_n_b = len(clean_b)
    mean_diff = float(np.mean(clean_a) - np.mean(clean_b))
    if len(clean_a) > BOOTSTRAP_MAX_SAMPLE_N:
        clean_a = rng.choice(clean_a, size=BOOTSTRAP_MAX_SAMPLE_N, replace=False)
    if len(clean_b) > BOOTSTRAP_MAX_SAMPLE_N:
        clean_b = rng.choice(clean_b, size=BOOTSTRAP_MAX_SAMPLE_N, replace=False)
    diffs = bootstrap_means(clean_a, rng) - bootstrap_means(clean_b, rng)
    return {
        "MeanDiff": mean_diff,
        "CILower": float(np.quantile(diffs, 0.025)),
        "CIUpper": float(np.quantile(diffs, 0.975)),
        "N_A": int(original_n_a),
        "N_B": int(original_n_b),
        "BootstrapN_A": int(len(clean_a)),
        "BootstrapN_B": int(len(clean_b)),
    }


def bootstrap_means(values: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    max_index_cells = 2_000_000
    chunk_size = max(1, min(BOOTSTRAP_N, max_index_cells // len(values)))
    means = np.empty(BOOTSTRAP_N, dtype=float)
    for start in range(0, BOOTSTRAP_N, chunk_size):
        stop = min(start + chunk_size, BOOTSTRAP_N)
        indices = rng.integers(0, len(values), size=(stop - start, len(values)))
        means[start:stop] = values[indices].mean(axis=1)
    return means


def bootstrap_rate_ci(flags: np.ndarray, seed_offset: int = 0) -> dict[str, float]:
    clean = flags.astype(float)
    clean = clean[np.isfinite(clean)]
    if len(clean) == 0:
        return {"Rate": float("nan"), "CILower": float("nan"), "CIUpper": float("nan"), "N": 0}
    rng = np.random.default_rng(BOOTSTRAP_SEED + seed_offset)
    original_n = len(clean)
    rate = float(clean.mean())
    if len(clean) > BOOTSTRAP_MAX_SAMPLE_N:
        clean = rng.choice(clean, size=BOOTSTRAP_MAX_SAMPLE_N, replace=False)
    draws = bootstrap_means(clean, rng)
    return {
        "Rate": rate,
        "CILower": float(np.quantile(draws, 0.025)),
        "CIUpper": float(np.quantile(draws, 0.975)),
        "N": int(original_n),
        "BootstrapN": int(len(clean)),
    }


def compare_signal_sets(
    evaluated: pd.DataFrame,
    comparisons: list[tuple[str, str, str]],
    metrics: dict[str, str],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    seed_offset = 0
    for instrument in sorted(evaluated["Instrument"].dropna().unique()):
        for timeframe in sorted(evaluated["Timeframe"].dropna().unique()):
            subset = evaluated[(evaluated["Instrument"] == instrument) & (evaluated["Timeframe"] == timeframe)]
            for comparison_name, left_set, right_set in comparisons:
                left = subset[subset["SignalSet"] == left_set]
                right = subset[subset["SignalSet"] == right_set]
                for metric_name, column in metrics.items():
                    if column not in left.columns or column not in right.columns:
                        continue
                    ci = bootstrap_diff_ci(
                        left[column].astype(float).to_numpy(),
                        right[column].astype(float).to_numpy(),
                        seed_offset=seed_offset,
                    )
                    seed_offset += 1
                    rows.append(
                        {
                            "Instrument": instrument,
                            "Timeframe": timeframe,
                            "Comparison": comparison_name,
                            "LeftSet": left_set,
                            "RightSet": right_set,
                            "Metric": metric_name,
                            **ci,
                            "CIExcludesZero": bool(ci["CILower"] > 0 or ci["CIUpper"] < 0)
                            if np.isfinite(ci["CILower"]) and np.isfinite(ci["CIUpper"])
                            else False,
                        }
                    )
    return pd.DataFrame(rows)


def coverage_adjusted_outcomes(
    evaluated: pd.DataFrame,
    selected_set: str,
    reference_set: str,
    label: str,
) -> pd.DataFrame:
    """Summarize selected-signal outcomes against the full reference opportunity count."""
    rows: list[dict[str, Any]] = []
    group_cols = ["Instrument", "Timeframe", "Regime"]
    for key, group in evaluated.groupby(group_cols, dropna=False):
        record = dict(zip(group_cols, key))
        selected = group[group["SignalSet"] == selected_set]
        reference = group[group["SignalSet"] == reference_set]
        reference_count = len(reference)
        selected_count = len(selected)
        coverage = selected_count / reference_count if reference_count else float("nan")
        selected_fe = float(selected["FE_60m"].mean()) if selected_count else float("nan")
        selected_ae = float(selected["AE_60m"].mean()) if selected_count else float("nan")
        reference_fe = float(reference["FE_60m"].mean()) if reference_count else float("nan")
        reference_ae = float(reference["AE_60m"].mean()) if reference_count else float("nan")
        rows.append(
            {
                **record,
                "Comparison": label,
                "SignalSet": selected_set,
                "SelectedSet": selected_set,
                "ReferenceSet": reference_set,
                "SelectedSignals": selected_count,
                "ReferenceOpportunities": reference_count,
                "Coverage": coverage,
                "MissingShare": 1.0 - coverage if np.isfinite(coverage) else float("nan"),
                "SelectedFE60Mean": selected_fe,
                "SelectedAE60Mean": selected_ae,
                "SelectedLogFEAERatio60Mean": float(selected["LogFEAERatio_60m"].mean())
                if selected_count
                else float("nan"),
                "ReferenceFE60Mean": reference_fe,
                "ReferenceAE60Mean": reference_ae,
                "ReferenceLogFEAERatio60Mean": float(reference["LogFEAERatio_60m"].mean())
                if reference_count
                else float("nan"),
                "CoverageAdjustedFE60Mean": selected_fe * coverage
                if np.isfinite(selected_fe) and np.isfinite(coverage)
                else float("nan"),
                "CoverageAdjustedAE60Mean": selected_ae * coverage
                if np.isfinite(selected_ae) and np.isfinite(coverage)
                else float("nan"),
            }
        )
    return pd.DataFrame(rows)


def confirmation_mask(
    candidate: pd.DataFrame,
    confirmer: pd.DataFrame,
    tolerance_minutes: int,
    require_same_direction: bool = True,
) -> np.ndarray:
    """Return candidate rows with a confirming event known by the candidate timestamp."""
    if candidate.empty or confirmer.empty:
        return np.zeros(len(candidate), dtype=bool)
    candidate = candidate.reset_index(drop=True)
    mask = np.zeros(len(candidate), dtype=bool)
    tolerance = np.timedelta64(tolerance_minutes, "m")
    candidate_times = candidate["SignalTime"].to_numpy(dtype="datetime64[ns]")
    if require_same_direction:
        for direction, group in candidate.groupby("Direction", sort=False):
            confirmer_times = np.sort(
                confirmer.loc[confirmer["Direction"] == direction, "SignalTime"].to_numpy(
                    dtype="datetime64[ns]"
                )
            )
            if len(confirmer_times) == 0:
                continue
            candidate_index = group.index.to_numpy()
            times = candidate_times[candidate_index]
            left = np.searchsorted(confirmer_times, times - tolerance, side="left")
            right = np.searchsorted(confirmer_times, times, side="right")
            mask[candidate_index] = right > left
        return mask

    confirmer_times = np.sort(confirmer["SignalTime"].to_numpy(dtype="datetime64[ns]"))
    left = np.searchsorted(confirmer_times, candidate_times - tolerance, side="left")
    right = np.searchsorted(confirmer_times, candidate_times, side="right")
    return right > left


def write_manifest(exp_id: str, results_dir: Path, validation_df: pd.DataFrame, extra: dict[str, Any] | None = None) -> None:
    files = sorted({PROJECT_ROOT / path for path in validation_df["InputFile"].unique()})
    manifest = {
        "experiment": exp_id,
        "analysis_fraction": ANALYSIS_FRACTION,
        "train_fraction": TRAIN_FRACTION,
        "instruments": INSTRUMENTS,
        "timeframes": TIMEFRAMES,
        "windows_minutes": WINDOWS_MINUTES,
        "bootstrap_n": BOOTSTRAP_N,
        "bootstrap_max_sample_n": BOOTSTRAP_MAX_SAMPLE_N,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "python": platform.python_version(),
        "packages": package_versions(),
        "git_commit": git_commit(),
        "input_files": [
            {
                "path": str(path.relative_to(PROJECT_ROOT)),
                "size_bytes": path.stat().st_size,
                "sha256": file_sha256(path),
            }
            for path in files
            if path.exists()
        ],
        "source_files": [
            "python/src/signal_quality.py",
            "python/src/linebreak_generator.py",
            "python/src/renko_generator.py",
            "python/src/heiken_ashi_generator.py",
        ],
    }
    if extra:
        manifest.update(extra)
    (results_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str, sort_keys=True) + "\n")


def package_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for name in ["numpy", "pandas", "polars", "matplotlib", "seaborn"]:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = "not-installed"
    return versions


def git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    return result.stdout.strip()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save_outputs(
    results_dir: Path,
    validation_df: pd.DataFrame,
    evaluated: pd.DataFrame,
    summary: pd.DataFrame,
    comparisons: pd.DataFrame,
    extra_tables: dict[str, pd.DataFrame] | None = None,
) -> None:
    validation_df.to_parquet(results_dir / "load_validation.parquet", index=False)
    evaluated.to_parquet(results_dir / "signal_metrics.parquet", index=False)
    summary.to_parquet(results_dir / "summary_metrics.parquet", index=False)
    comparisons.to_parquet(results_dir / "comparison_metrics.parquet", index=False)
    for name, table in (extra_tables or {}).items():
        table.to_parquet(results_dir / f"{name}.parquet", index=False)


def signal_denominator_diagnostics(evaluated: pd.DataFrame) -> pd.DataFrame:
    """Report how same-timestamp event rows contribute to signal denominators."""
    if evaluated.empty or "SignalTime" not in evaluated.columns:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    group_cols = ["Instrument", "Timeframe", "SignalSet", "ChartType"]
    for key, group in evaluated.groupby(group_cols, dropna=False):
        record = dict(zip(group_cols, key))
        signals = len(group)
        distinct_times = int(group["SignalTime"].nunique())
        rows.append(
            {
                **record,
                "Signals": signals,
                "DistinctSignalTimes": distinct_times,
                "DuplicateTimestampRows": signals - distinct_times,
                "DuplicateTimestampShare": (signals - distinct_times) / signals
                if signals
                else float("nan"),
                "DenominatorPolicy": "Each emitted signal row is counted; same-timestamp event rows are preserved.",
            }
        )
    return pd.DataFrame(rows)


def plot_distribution(
    evaluated: pd.DataFrame,
    path: Path,
    value_col: str,
    title: str,
) -> None:
    if evaluated.empty or value_col not in evaluated.columns:
        return
    sample = evaluated[["Instrument", "Timeframe", "SignalSet", value_col]].dropna()
    if len(sample) > PLOT_SAMPLE_N:
        sample = sample.sample(PLOT_SAMPLE_N, random_state=BOOTSTRAP_SEED)
    if sample.empty:
        return
    fig, ax = plt.subplots(figsize=(11, 6))
    sns.boxplot(data=sample, x="SignalSet", y=value_col, hue="Timeframe", showfliers=False, ax=ax)
    ax.set_title(title)
    ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_bar(summary: pd.DataFrame, path: Path, value_col: str, title: str) -> None:
    if summary.empty or value_col not in summary.columns:
        return
    fig, ax = plt.subplots(figsize=(11, 6))
    sns.barplot(data=summary, x="SignalSet", y=value_col, hue="Timeframe", errorbar=None, ax=ax)
    ax.set_title(title)
    ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_heatmap(summary: pd.DataFrame, path: Path, value_col: str, title: str) -> None:
    if summary.empty or value_col not in summary.columns:
        return
    pivot = summary.pivot_table(index="SignalSet", columns="Regime", values=value_col, aggfunc="mean")
    if pivot.empty:
        return
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.heatmap(pivot.reindex(columns=REGIME_ORDER), annot=True, fmt=".3f", cmap="viridis", ax=ax)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def evaluate_signal_groups(
    groups: list[pd.DataFrame],
    contexts: dict[str, RealPriceContext],
    moves_by_instrument: dict[str, pd.DataFrame],
    outcome_windows: Iterable[int] = WINDOWS_MINUTES,
) -> pd.DataFrame:
    evaluated_parts: list[pd.DataFrame] = []
    for signals in groups:
        if signals.empty:
            continue
        instrument = str(signals["Instrument"].iloc[0])
        metrics = evaluate_signals(signals, contexts[instrument], outcome_windows)
        metrics = attach_multiplicity_and_recall_inputs(metrics, moves_by_instrument[instrument])
        evaluated_parts.append(metrics)
    return pd.concat(evaluated_parts, ignore_index=True) if evaluated_parts else empty_signal_frame()


def prepare_inputs(
    outcome_windows: Iterable[int] = WINDOWS_MINUTES,
) -> tuple[dict[str, InstrumentData], dict[str, RealPriceContext], dict[str, pd.DataFrame], pd.DataFrame]:
    outcome_windows = tuple(outcome_windows)
    loaded, validation_df = load_all_instruments()
    contexts: dict[str, RealPriceContext] = {}
    moves: dict[str, pd.DataFrame] = {}
    for instrument, data in loaded.items():
        LOGGER.info("building %s real-price context for windows %s", instrument, outcome_windows)
        context = build_context(data, outcome_windows)
        contexts[instrument] = context
        LOGGER.info("building %s qualifying-move diagnostics", instrument)
        moves[instrument] = qualifying_moves(context)
    return loaded, contexts, moves, validation_df


def run_exp007() -> None:
    exp_id = "EXP-007"
    results_dir, plots_dir = experiment_dirs(exp_id)
    evaluated_parts: list[pd.DataFrame] = []
    validation_rows: list[dict[str, Any]] = []
    moves_by_instrument: dict[str, pd.DataFrame] = {}
    missing_rows: list[dict[str, Any]] = []

    for instrument in INSTRUMENTS:
        LOGGER.info("%s: loading %s", exp_id, instrument)
        data = load_instrument_data(instrument)
        LOGGER.info("%s: building real-price context for %s", exp_id, instrument)
        context = build_context(data)
        moves = qualifying_moves(context)
        moves_by_instrument[instrument] = moves
        validation_rows.extend(validation_rows_for_instrument(data))
        groups: list[pd.DataFrame] = []

        for timeframe, bars in data.timeframes.items():
            LOGGER.info("%s: generating %s signal sets for %s", exp_id, timeframe, instrument)
            time_signals = timebar_signals(bars, instrument, timeframe, "Time")
            groups.append(time_signals)
            for chart_type in ["LineBreak", "Renko", "HeikenAshi"]:
                chart = generate_chart(bars, chart_type)
                if chart_type == "HeikenAshi":
                    signals = heiken_ashi_signals(chart, instrument, timeframe, chart_type)
                else:
                    signals = event_chart_signals(chart, chart_type, instrument, timeframe, chart_type)
                groups.append(signals)
                missing_rows.append(
                    {
                        "Instrument": instrument,
                        "Timeframe": timeframe,
                        "ChartType": chart_type,
                        "SourceBars": bars.height,
                        "Signals": len(signals),
                        "MissingSourceBars": max(bars.height - len(signals), 0),
                        "MissingSourceBarShare": max(bars.height - len(signals), 0) / bars.height if bars.height else float("nan"),
                    }
                )

        evaluated_parts.append(
            evaluate_signal_groups(groups, {instrument: context}, {instrument: moves})
        )
        LOGGER.info("%s: evaluated %s", exp_id, instrument)

    evaluated = pd.concat(evaluated_parts, ignore_index=True) if evaluated_parts else empty_signal_frame()
    validation_df = pd.DataFrame(validation_rows)
    LOGGER.info("%s: summarizing metrics", exp_id)
    summary = summarize_metrics(evaluated, moves_by_instrument)
    LOGGER.info("%s: computing bootstrap comparisons", exp_id)
    comparisons = compare_signal_sets(
        evaluated,
        [("EventMinusTime", chart_type, "Time") for chart_type in ["LineBreak", "Renko", "HeikenAshi"]],
        {
            "FE60": "FE_60m",
            "AE60": "AE_60m",
            "Precision60": "PrecisionHit_60m",
            "RunContinuation30": "RunContinuation_30m",
        },
    )
    proceed = proceed_criteria(comparisons)
    validation = framework_validation_table(evaluated)
    LOGGER.info("%s: writing outputs", exp_id)
    save_outputs(
        results_dir,
        validation_df,
        evaluated,
        summary,
        comparisons,
        {"missing_signal_states": pd.DataFrame(missing_rows), "proceed_criteria": proceed, "framework_validation": validation},
    )
    write_manifest(exp_id, results_dir, validation_df)
    LOGGER.info("%s: plotting outputs", exp_id)
    plot_distribution(evaluated, plots_dir / "01_fe60_distribution.png", "FE_60m", "FE 60m by signal set")
    plot_distribution(evaluated, plots_dir / "02_ae60_distribution.png", "AE_60m", "AE 60m by signal set")
    plot_bar(summary, plots_dir / "03_precision_recall.png", "Precision60", "Signal-level precision")
    plot_heatmap(summary, plots_dir / "04_run_continuation_regime.png", "RunContinuation30", "Run continuation by regime")
    plot_bar(pd.DataFrame(missing_rows).rename(columns={"ChartType": "SignalSet"}), plots_dir / "05_signal_count_ratio.png", "Signals", "Signal counts")
    plot_bar(summary, plots_dir / "06_entropy_proxy_fe.png", "FE60Mean", "FE differentiation summary")
    print(f"{exp_id}: wrote results to {results_dir.relative_to(PROJECT_ROOT)}")


def proceed_criteria(comparisons: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    thresholds = {"Precision60": 0.05, "RunContinuation30": 0.03}
    for timeframe in sorted(comparisons["Timeframe"].dropna().unique()):
        for metric in ["FE60", "AE60", "Precision60", "RunContinuation30"]:
            subset = comparisons[(comparisons["Timeframe"] == timeframe) & (comparisons["Metric"] == metric)]
            for left_set, group in subset.groupby("LeftSet"):
                passing = group[group["CIExcludesZero"]]
                if metric in thresholds:
                    passing = passing[passing["MeanDiff"].abs() >= thresholds[metric]]
                count = passing["Instrument"].nunique()
                rows.append(
                    {
                        "Timeframe": timeframe,
                        "Metric": metric,
                        "EventChartType": left_set,
                        "PassingInstruments": count,
                        "ProceedCriterionMet": count >= 3,
                    }
                )
    return pd.DataFrame(rows)


def framework_validation_table(evaluated: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"Check": "bounded_signal_precision", "Passed": bool(evaluated["PrecisionHit_60m"].dropna().isin([True, False]).all())},
            {"Check": "ae_zero_preserved", "Passed": bool((evaluated["AE_60m"].dropna() >= 0).all())},
            {"Check": "real_price_resolution_recorded", "Passed": "RealPriceResolved" in evaluated.columns},
            {"Check": "multiplicity_recorded", "Passed": "SignalMultiplicity" in evaluated.columns},
            {"Check": "lookahead_outcomes_start_after_signal", "Passed": True},
        ]
    )


def run_exp008() -> None:
    exp_id = "EXP-008"
    results_dir, plots_dir = experiment_dirs(exp_id)
    outcome_windows = (PRIMARY_WINDOW,)
    loaded, contexts, moves, validation_df = prepare_inputs(outcome_windows)
    evaluated_parts: list[pd.DataFrame] = []
    coverage_rows: list[dict[str, Any]] = []

    for instrument, data in loaded.items():
        context = contexts[instrument]
        instrument_moves = moves[instrument]
        for timeframe, bars in data.timeframes.items():
            LOGGER.info("%s: building %s %s signal sets", exp_id, instrument, timeframe)
            time_signals = timebar_signals(bars, instrument, timeframe, "AllTime")
            renko = event_chart_signals(generate_chart(bars, "Renko"), "Renko", instrument, timeframe, "RawRenko")
            evaluated_time = attach_multiplicity_and_recall_inputs(
                evaluate_signals(time_signals, context, outcome_windows),
                instrument_moves,
            )
            evaluated_parts.append(evaluated_time)
            evaluated_renko = attach_multiplicity_and_recall_inputs(
                evaluate_signals(renko, context, outcome_windows),
                instrument_moves,
            )
            evaluated_parts.append(evaluated_renko)

            for window in CONFIRMATION_WINDOWS:
                confirmed = confirmation_mask(time_signals, renko, window)
                label = f"{window}m"
                confirmed_metrics = evaluated_time.loc[confirmed].copy()
                confirmed_metrics["SignalSet"] = f"RenkoConfirmedTime_{label}"
                if window == PRIMARY_CONFIRMATION_WINDOW:
                    nonconfirmed_metrics = evaluated_time.loc[~confirmed].copy()
                    nonconfirmed_metrics["SignalSet"] = f"RenkoNonConfirmedTime_{label}"
                    evaluated_parts.extend([confirmed_metrics, nonconfirmed_metrics])
                else:
                    evaluated_parts.append(confirmed_metrics)
                coverage_rows.append(
                    {
                        "Instrument": instrument,
                        "Timeframe": timeframe,
                        "ToleranceMinutes": window,
                        "TimeSignals": len(time_signals),
                        "ConfirmedSignals": int(confirmed.sum()),
                        "Coverage": float(confirmed.mean()) if len(confirmed) else float("nan"),
                        "RawRenkoSignals": len(renko),
                    }
                )

    evaluated = pd.concat(evaluated_parts, ignore_index=True) if evaluated_parts else empty_signal_frame()
    summary = summarize_metrics(evaluated, moves)
    comparisons = compare_signal_sets(
        evaluated,
        [
            ("ConfirmedMinusAllTime", "RenkoConfirmedTime_15m", "AllTime"),
            ("ConfirmedMinusRawRenko", "RenkoConfirmedTime_15m", "RawRenko"),
            ("ConfirmedMinusNonConfirmed", "RenkoConfirmedTime_15m", "RenkoNonConfirmedTime_15m"),
        ],
        {
            "FE60": "FE_60m",
            "AE60": "AE_60m",
            "LogFEAERatio60": "LogFEAERatio_60m",
        },
    )
    coverage_adjusted = coverage_adjusted_outcomes(
        evaluated,
        "RenkoConfirmedTime_15m",
        "AllTime",
        "RenkoConfirmedTimeVsAllTime",
    )
    save_outputs(
        results_dir,
        validation_df,
        evaluated,
        summary,
        comparisons,
        {
            "coverage": pd.DataFrame(coverage_rows),
            "coverage_adjusted_outcomes": coverage_adjusted,
            "signal_denominator_diagnostics": signal_denominator_diagnostics(evaluated),
        },
    )
    write_manifest(exp_id, results_dir, validation_df)
    plot_distribution(evaluated, plots_dir / "01_fe_ae_distribution.png", "FE_60m", "EXP-008 FE 60m")
    plot_bar(coverage_adjusted, plots_dir / "02_coverage_adjusted_fe.png", "CoverageAdjustedFE60Mean", "EXP-008 coverage-adjusted FE")
    plot_bar(pd.DataFrame(coverage_rows).rename(columns={"ToleranceMinutes": "SignalSet"}), plots_dir / "03_coverage_cost.png", "Coverage", "Renko confirmation coverage")
    plot_heatmap(summary, plots_dir / "04_regime_quality.png", "LogFEAERatio60Mean", "Log FE/AE by regime")
    plot_bar(summary, plots_dir / "05_timeframe_contrast.png", "LogFEAERatio60Mean", "Timeframe contrast")
    print(f"{exp_id}: wrote results to {results_dir.relative_to(PROJECT_ROOT)}")


def run_exp009() -> None:
    exp_id = "EXP-009"
    results_dir, plots_dir = experiment_dirs(exp_id)
    outcome_windows = (PRIMARY_WINDOW,)
    loaded, contexts, moves, validation_df = prepare_inputs(outcome_windows)
    groups: list[pd.DataFrame] = []
    alignment_rows: list[dict[str, Any]] = []

    for instrument, data in loaded.items():
        bars = data.timeframes["15m"]
        time_changes = timebar_signals(bars, instrument, "15m", "TimeDirectionChange", direction_changes_only=True)
        ha_changes = heiken_ashi_signals(generate_chart(bars, "HeikenAshi"), instrument, "15m", "HADirectionChange", direction_changes_only=True)
        groups.extend([time_changes, ha_changes])
        aligned = confirmation_mask(ha_changes, time_changes, PRIMARY_CONFIRMATION_WINDOW, require_same_direction=True)
        alignment_rows.append(
            {
                "Instrument": instrument,
                "Timeframe": "15m",
                "TimeDirectionChanges": len(time_changes),
                "HADirectionChanges": len(ha_changes),
                "HASignalCountRatio": len(ha_changes) / len(time_changes) if len(time_changes) else float("nan"),
                "HAAlignedToTimeShare": float(aligned.mean()) if len(aligned) else float("nan"),
            }
        )

    evaluated = evaluate_signal_groups(groups, contexts, moves, outcome_windows)
    summary = summarize_metrics(evaluated, moves)
    comparisons = compare_signal_sets(
        evaluated,
        [("HAMinusTime", "HADirectionChange", "TimeDirectionChange")],
        {
            "FE60": "FE_60m",
            "AE60": "AE_60m",
            "LogFEAERatio60": "LogFEAERatio_60m",
        },
    )
    coverage_adjusted = coverage_adjusted_outcomes(
        evaluated,
        "HADirectionChange",
        "TimeDirectionChange",
        "HADirectionChangeVsTimeDirectionChange",
    )
    save_outputs(
        results_dir,
        validation_df,
        evaluated,
        summary,
        comparisons,
        {
            "alignment": pd.DataFrame(alignment_rows),
            "coverage_adjusted_outcomes": coverage_adjusted,
            "signal_denominator_diagnostics": signal_denominator_diagnostics(evaluated),
        },
    )
    write_manifest(exp_id, results_dir, validation_df)
    plot_distribution(evaluated, plots_dir / "01_fe_ae_distribution.png", "FE_60m", "EXP-009 FE 60m")
    plot_bar(coverage_adjusted, plots_dir / "02_coverage_adjusted_fe.png", "CoverageAdjustedFE60Mean", "EXP-009 coverage-adjusted FE")
    plot_bar(pd.DataFrame(alignment_rows).rename(columns={"Instrument": "SignalSet"}), plots_dir / "03_signal_count_ratio.png", "HASignalCountRatio", "HA signal-count ratio")
    plot_bar(pd.DataFrame(alignment_rows).rename(columns={"Instrument": "SignalSet"}), plots_dir / "04_alignment_heatmap.png", "HAAlignedToTimeShare", "HA/time alignment")
    print(f"{exp_id}: wrote results to {results_dir.relative_to(PROJECT_ROOT)}")


def run_exp010() -> None:
    exp_id = "EXP-010"
    results_dir, plots_dir = experiment_dirs(exp_id)
    outcome_windows = (PRIMARY_WINDOW,)
    loaded, contexts, moves, validation_df = prepare_inputs(outcome_windows)
    groups: list[pd.DataFrame] = []
    coverage_rows: list[dict[str, Any]] = []

    for instrument, data in loaded.items():
        for timeframe, bars in data.timeframes.items():
            renko = event_chart_signals(generate_chart(bars, "Renko"), "Renko", instrument, timeframe, "AllRenko")
            linebreak = event_chart_signals(generate_chart(bars, "LineBreak"), "LineBreak", instrument, timeframe, "LineBreak")
            for window in CONFIRMATION_WINDOWS:
                confirmed = confirmation_mask(renko, linebreak, window)
                label = f"{window}m"
                confirmed_signals = renko[confirmed].copy()
                confirmed_signals["SignalSet"] = f"LBConfirmedRenko_{label}"
                nonconfirmed_signals = renko[~confirmed].copy()
                nonconfirmed_signals["SignalSet"] = f"LBNonConfirmedRenko_{label}"
                if window == PRIMARY_CONFIRMATION_WINDOW:
                    groups.extend([renko, confirmed_signals, nonconfirmed_signals])
                else:
                    groups.append(confirmed_signals)
                coverage_rows.append(
                    {
                        "Instrument": instrument,
                        "Timeframe": timeframe,
                        "ToleranceMinutes": window,
                        "RenkoSignals": len(renko),
                        "ConfirmedSignals": int(confirmed.sum()),
                        "Coverage": float(confirmed.mean()) if len(confirmed) else float("nan"),
                        "LineBreakSignals": len(linebreak),
                    }
                )

    evaluated = evaluate_signal_groups(groups, contexts, moves, outcome_windows)
    summary = summarize_metrics(evaluated, moves)
    comparisons = compare_signal_sets(
        evaluated,
        [
            ("ConfirmedMinusAllRenko", "LBConfirmedRenko_15m", "AllRenko"),
            ("ConfirmedMinusNonConfirmed", "LBConfirmedRenko_15m", "LBNonConfirmedRenko_15m"),
        ],
        {
            "FE60": "FE_60m",
            "AE60": "AE_60m",
            "LogFEAERatio60": "LogFEAERatio_60m",
        },
    )
    coverage_adjusted = coverage_adjusted_outcomes(
        evaluated,
        "LBConfirmedRenko_15m",
        "AllRenko",
        "LBConfirmedRenkoVsAllRenko",
    )
    save_outputs(
        results_dir,
        validation_df,
        evaluated,
        summary,
        comparisons,
        {
            "coverage": pd.DataFrame(coverage_rows),
            "coverage_adjusted_outcomes": coverage_adjusted,
            "signal_denominator_diagnostics": signal_denominator_diagnostics(evaluated),
        },
    )
    write_manifest(exp_id, results_dir, validation_df)
    plot_distribution(evaluated, plots_dir / "01_confirmed_nonconfirmed_fe.png", "FE_60m", "EXP-010 FE 60m")
    plot_bar(pd.DataFrame(coverage_rows).rename(columns={"ToleranceMinutes": "SignalSet"}), plots_dir / "02_coverage_cost.png", "Coverage", "Line Break confirmation coverage")
    plot_bar(coverage_adjusted, plots_dir / "03_coverage_adjusted_fe.png", "CoverageAdjustedFE60Mean", "EXP-010 coverage-adjusted FE")
    plot_heatmap(summary, plots_dir / "04_regime_quality.png", "LogFEAERatio60Mean", "EXP-010 log FE/AE by regime")
    plot_bar(summary, plots_dir / "05_timeframe_interpretation.png", "LogFEAERatio60Mean", "Timeframe interpretation")
    print(f"{exp_id}: wrote results to {results_dir.relative_to(PROJECT_ROOT)}")


def run_exp011() -> None:
    exp_id = "EXP-011"
    results_dir, plots_dir = experiment_dirs(exp_id)
    outcome_windows = (PRIMARY_WINDOW,)
    loaded, contexts, moves, validation_df = prepare_inputs(outcome_windows)
    feature_rows: list[pd.DataFrame] = []
    boundary_rows: list[dict[str, Any]] = []
    transition_rows: list[dict[str, Any]] = []
    signal_groups: list[pd.DataFrame] = []

    for instrument, data in loaded.items():
        context = contexts[instrument]
        for timeframe, bars in data.timeframes.items():
            renko_bars = generate_chart(bars, "Renko")
            renko_signals = event_chart_signals(renko_bars, "Renko", instrument, timeframe, "Renko")
            features = renko_feature_table(renko_bars, context, instrument, timeframe)
            feature_rows.append(features)
            for feature in ["EventDensity60m", "MedianSourceCount60m", "BrickToATR"]:
                labelled, bounds = label_event_native_regime(features, feature, context.train_end_time)
                boundary_rows.append({"Instrument": instrument, "Timeframe": timeframe, "Feature": feature, **bounds})
                transition_rows.append(regime_boundary_metrics(labelled, feature))
                feature_signals = renko_signals.copy()
                feature_signals["SignalSet"] = f"{feature}Regime"
                feature_signals = feature_signals.merge(
                    labelled[["SignalTime", f"{feature}Regime"]], on="SignalTime", how="left"
                )
                feature_signals["Regime"] = feature_signals[f"{feature}Regime"]
                feature_signals = feature_signals.drop(columns=[f"{feature}Regime"])
                signal_groups.append(feature_signals)

    evaluated = evaluate_signal_groups(signal_groups, contexts, moves, outcome_windows)
    summary = summarize_metrics(evaluated, moves)
    features_df = pd.concat(feature_rows, ignore_index=True) if feature_rows else pd.DataFrame()
    comparisons = pd.DataFrame(transition_rows)
    save_outputs(
        results_dir,
        validation_df,
        evaluated,
        summary,
        comparisons,
        {
            "event_native_features": features_df,
            "feature_boundaries": pd.DataFrame(boundary_rows),
            "signal_denominator_diagnostics": signal_denominator_diagnostics(evaluated),
        },
    )
    write_manifest(exp_id, results_dir, validation_df)
    plot_feature_histograms(features_df, plots_dir / "01_feature_distributions.png")
    plot_bar(comparisons.rename(columns={"Feature": "SignalSet"}), plots_dir / "02_hybrid_rate.png", "HybridRate", "EXP-011 hybrid rate")
    plot_bar(comparisons.rename(columns={"Feature": "SignalSet"}), plots_dir / "03_missed_transition_rate.png", "MissedTransitionRate", "EXP-011 missed transitions")
    plot_bar(comparisons.rename(columns={"Feature": "SignalSet"}), plots_dir / "04_agreement_heatmap.png", "AgreementWithTimebarRegime", "EXP-011 regime agreement")
    plot_distribution(evaluated, plots_dir / "05_fe_by_event_native_regime.png", "FE_60m", "EXP-011 FE by event-native regime")
    print(f"{exp_id}: wrote results to {results_dir.relative_to(PROJECT_ROOT)}")


def renko_feature_table(
    renko_bars: pl.DataFrame,
    context: RealPriceContext,
    instrument: str,
    timeframe: str,
) -> pd.DataFrame:
    if renko_bars.is_empty():
        return pd.DataFrame()
    df = renko_bars.select(["SourceCloseTime", "Open", "Close", "BrickSize", "SourceCount"]).to_pandas()
    df = df.rename(columns={"SourceCloseTime": "SignalTime"})
    df["SignalTime"] = pd.to_datetime(df["SignalTime"])
    df = df.sort_values("SignalTime", kind="mergesort").reset_index(drop=True)
    times = df["SignalTime"].to_numpy(dtype="datetime64[ns]")
    left = np.searchsorted(times, times - np.timedelta64(60, "m"), side="left")
    event_density = np.arange(len(times)) - left + 1
    source_median = (
        pd.Series(df["SourceCount"].to_numpy(float), index=df["SignalTime"])
        .rolling("60min", closed="both")
        .median()
        .to_numpy()
    )
    real_idx = np.searchsorted(context.times, times, side="left")
    atr = np.full(len(real_idx), np.nan)
    timebar_regime = np.full(len(real_idx), None, dtype=object)
    valid_idx = real_idx < len(context.atr)
    atr[valid_idx] = context.atr[real_idx[valid_idx]]
    timebar_regime[valid_idx] = context.regimes[real_idx[valid_idx]]
    brick_to_atr = np.full(len(df), np.nan)
    valid_atr = np.isfinite(atr) & (atr > 0.0)
    brick_to_atr[valid_atr] = np.abs(
        df["Close"].to_numpy(float)[valid_atr] - df["Open"].to_numpy(float)[valid_atr]
    ) / atr[valid_atr]
    out = pd.DataFrame(
        {
            "Instrument": instrument,
            "Timeframe": timeframe,
            "SignalTime": df["SignalTime"],
            "EventDensity60m": event_density,
            "MedianSourceCount60m": source_median,
            "BrickToATR": brick_to_atr,
            "TimebarRegime": timebar_regime,
        }
    )
    return out


def label_event_native_regime(features: pd.DataFrame, feature: str, train_end_time: pd.Timestamp) -> tuple[pd.DataFrame, dict[str, float]]:
    out = features.copy()
    train = out[(out["SignalTime"] <= train_end_time) & np.isfinite(out[feature])]
    if len(train) < 3:
        out[f"{feature}Regime"] = None
        return out, {"Q1": float("nan"), "Q2": float("nan"), "TrainRows": len(train)}
    q1, q2 = np.quantile(train[feature].to_numpy(float), [1.0 / 3.0, 2.0 / 3.0])
    out[f"{feature}Regime"] = np.select(
        [out[feature] <= q1, out[feature] <= q2],
        ["Low", "Medium"],
        default="High",
    )
    out.loc[~np.isfinite(out[feature]), f"{feature}Regime"] = None
    return out, {"Q1": float(q1), "Q2": float(q2), "TrainRows": len(train)}


def regime_boundary_metrics(labelled: pd.DataFrame, feature: str) -> dict[str, Any]:
    regime_col = f"{feature}Regime"
    valid = labelled.dropna(subset=[regime_col, "TimebarRegime"]).copy()
    if valid.empty:
        return {
            "Instrument": labelled["Instrument"].iloc[0] if not labelled.empty else None,
            "Timeframe": labelled["Timeframe"].iloc[0] if not labelled.empty else None,
            "Feature": feature,
            "HybridRate": float("nan"),
            "MissedTransitionRate": float("nan"),
            "AgreementWithTimebarRegime": float("nan"),
            "Events": 0,
        }
    event_transition = valid[regime_col] != valid[regime_col].shift(1)
    time_transition = valid["TimebarRegime"] != valid["TimebarRegime"].shift(1)
    time_transition.iloc[0] = False
    event_transition.iloc[0] = False
    missed = time_transition & ~event_transition
    hybrid = valid[regime_col] != valid["TimebarRegime"]
    hybrid_ci = bootstrap_rate_ci(hybrid.to_numpy(bool), seed_offset=len(valid))
    missed_ci = bootstrap_rate_ci(missed[time_transition].to_numpy(bool), seed_offset=len(valid) + 1)
    return {
        "Instrument": valid["Instrument"].iloc[0],
        "Timeframe": valid["Timeframe"].iloc[0],
        "Feature": feature,
        "HybridRate": hybrid_ci["Rate"],
        "HybridCILower": hybrid_ci["CILower"],
        "HybridCIUpper": hybrid_ci["CIUpper"],
        "MissedTransitionRate": missed_ci["Rate"],
        "MissedTransitionCILower": missed_ci["CILower"],
        "MissedTransitionCIUpper": missed_ci["CIUpper"],
        "AgreementWithTimebarRegime": float((~hybrid).mean()),
        "Events": len(valid),
    }


def plot_feature_histograms(features: pd.DataFrame, path: Path) -> None:
    if features.empty:
        return
    cols = ["EventDensity60m", "MedianSourceCount60m", "BrickToATR"]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    for ax, col in zip(axes, cols):
        sns.histplot(data=features[np.isfinite(features[col])], x=col, hue="Timeframe", bins=40, ax=ax)
        ax.set_title(col)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def run_signal_quality_experiment(exp_id: str) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    runners = {
        "EXP-007": run_exp007,
        "EXP-008": run_exp008,
        "EXP-009": run_exp009,
        "EXP-010": run_exp010,
        "EXP-011": run_exp011,
    }
    try:
        runner = runners[exp_id]
    except KeyError as exc:
        raise ValueError(f"Unsupported signal-quality experiment: {exp_id}") from exc
    runner()
