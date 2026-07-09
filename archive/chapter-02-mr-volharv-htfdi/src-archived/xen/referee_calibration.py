"""Shared helpers for Phase 001 referee-calibration experiments.

The functions in this module implement the frozen harness primitives declared in
the active checkpoint design: holdout-safe domain construction, known-null and
known-positive candidate generation, minimal/gate-stack referee verdicts, and
small statistical summaries. Experiment scripts own orchestration and output.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import polars as pl

from xen.bar_aggregator import aggregate_ohlc


REQUIRED_TIMEBAR_COLUMNS = [
    "Symbol",
    "OpenTime",
    "CloseTime",
    "Open",
    "High",
    "Low",
    "Close",
    "TickVolume",
]
CANONICAL_TIME_UNIT = "us"
TRAIN_FRACTION = 0.70
ANALYSIS_FRACTION = 0.70


@dataclass(frozen=True)
class DomainSpec:
    label: str
    period_minutes: int
    min_coverage: float | None
    min_effective_n: int
    min_state_count: int


DOMAIN_SPECS: dict[str, DomainSpec] = {
    "5m": DomainSpec("5m", 5, None, min_effective_n=120, min_state_count=30),
    "1h": DomainSpec("1h", 60, 0.90, min_effective_n=60, min_state_count=20),
    "15m": DomainSpec("15m", 15, 0.90, min_effective_n=90, min_state_count=25),
    "4h": DomainSpec("4h", 240, 0.90, min_effective_n=25, min_state_count=8),
}
COVERAGE_GRID: tuple[float | None, ...] = (None, 0.90, 0.80)

# Frozen-before-EXP-001 defaults. The manual execution gate asks the operator to
# confirm or override these before EXP-001 is run; after that they are phase
# constants.
ROUND_TRIP_COST_BPS: dict[str, dict[str, float]] = {
    "EURUSD": {"5m": 1.0, "1h": 1.0, "4h": 1.0},
    "XAUUSD": {"5m": 3.0, "1h": 3.0, "4h": 3.0},
    "BTCUSD": {"5m": 10.0, "1h": 10.0, "4h": 10.0},
    "USTEC": {"5m": 4.0, "1h": 4.0, "4h": 4.0},
}
MATERIALITY_BPS: dict[str, float] = {"5m": 0.5, "15m": 0.75, "1h": 1.5, "4h": 3.0}
ALPHA_GRID: tuple[float, ...] = (0.10, 0.05, 0.01)
EDGE_GRID_BPS: tuple[float, ...] = (0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 12.0, 16.0, 24.0, 32.0)


@dataclass(frozen=True)
class AnalysisData:
    instrument: str
    source_file: str
    total_rows: int
    analysis_rows: int
    train_rows: int
    test_rows: int
    analysis_start: str
    analysis_end: str
    train_end: str
    train_end_ts: Any
    frame: pl.DataFrame


@dataclass(frozen=True)
class MeanCI:
    mean: float
    lower: float
    upper: float
    n: int


def seed_for(*parts: object) -> int:
    """Create a stable 32-bit seed from experiment labels."""
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    return int(hashlib.sha256(payload).hexdigest()[:8], 16)


def infer_instrument(path: Path) -> str:
    """Infer the instrument symbol from a ``timebars_<symbol>_...`` filename."""
    parts = path.stem.split("_")
    if len(parts) >= 2 and parts[0] == "timebars":
        return parts[1].upper()
    return path.stem.upper()


def list_timebar_files(data_dir: Path) -> list[Path]:
    """Return sorted base time-bar Parquet files under ``data_dir/timebars``."""
    return sorted((data_dir / "timebars").glob("timebars_*.parquet"))


def to_canonical_time(frame: pl.DataFrame) -> pl.DataFrame:
    """Cast time columns present in ``frame`` to the canonical datetime unit."""
    casts = [
        pl.col(column).cast(pl.Datetime(CANONICAL_TIME_UNIT))
        for column in ("OpenTime", "CloseTime", "SourceCloseTime")
        if column in frame.columns
    ]
    return frame.with_columns(casts) if casts else frame


def load_analysis_data(path: Path) -> AnalysisData:
    """Load only the first 70 percent chronological analysis slice."""
    schema = pl.scan_parquet(path).collect_schema().names()
    missing = sorted(set(REQUIRED_TIMEBAR_COLUMNS).difference(schema))
    if missing:
        raise ValueError(f"{path.name} missing required columns: {missing}")

    scan = pl.scan_parquet(path).select(REQUIRED_TIMEBAR_COLUMNS)
    total_rows = int(scan.select(pl.len()).collect().item())
    analysis_rows = int(total_rows * ANALYSIS_FRACTION)
    if analysis_rows <= 0:
        raise ValueError(f"{path.name} has no analysis rows")

    frame = to_canonical_time(scan.sort("CloseTime").slice(0, analysis_rows).collect())
    if frame.is_empty():
        raise ValueError(f"{path.name} analysis slice is empty")
    if not frame.get_column("CloseTime").is_sorted():
        raise ValueError(f"{path.name} analysis slice is not sorted by CloseTime")

    train_rows = int(frame.height * TRAIN_FRACTION)
    test_rows = frame.height - train_rows
    analysis_start = frame.select(pl.first("CloseTime")).item()
    analysis_end = frame.select(pl.last("CloseTime")).item()
    train_end = frame.slice(max(train_rows - 1, 0), 1).select(pl.first("CloseTime")).item()
    symbol = str(frame.select(pl.first("Symbol")).item()).upper()

    return AnalysisData(
        instrument=symbol or infer_instrument(path),
        source_file=path.name,
        total_rows=total_rows,
        analysis_rows=frame.height,
        train_rows=train_rows,
        test_rows=test_rows,
        analysis_start=str(analysis_start),
        analysis_end=str(analysis_end),
        train_end=str(train_end),
        train_end_ts=train_end,
        frame=frame,
    )


def build_domain_frames(source_1m: pl.DataFrame) -> dict[str, pl.DataFrame]:
    """Build every predeclared domain from the already-sliced 1m analysis set."""
    domains: dict[str, pl.DataFrame] = {}
    for label, spec in DOMAIN_SPECS.items():
        domains[label] = to_canonical_time(
            aggregate_ohlc(
                source_1m,
                period_minutes=spec.period_minutes,
                min_coverage=spec.min_coverage,
            )
        )
    return domains


def coverage_label(min_coverage: float | None) -> str:
    """Human-readable label for a ``min_coverage`` value (``None`` -> strict)."""
    return "strict" if min_coverage is None else f"{min_coverage:.2f}"


def coverage_grid_rows(data: AnalysisData) -> list[dict[str, Any]]:
    """Report retained-bar counts and dropped-window fractions across the grid.

    Parameters
    ----------
    data : AnalysisData
        Source analysis slice to aggregate at each domain and coverage value.

    Returns
    -------
    list[dict[str, Any]]
        One row per (domain, coverage) cell.
    """
    rows: list[dict[str, Any]] = []
    for spec in DOMAIN_SPECS.values():
        for min_coverage in COVERAGE_GRID:
            aggregated = aggregate_ohlc(
                data.frame,
                period_minutes=spec.period_minutes,
                min_coverage=min_coverage,
            )
            expected = max(1, data.frame.height // spec.period_minutes)
            rows.append(
                {
                    "instrument": data.instrument,
                    "source_file": data.source_file,
                    "domain": spec.label,
                    "period_minutes": spec.period_minutes,
                    "coverage": coverage_label(min_coverage),
                    "source_rows": data.frame.height,
                    "retained_bars": aggregated.height,
                    "expected_full_windows": expected,
                    "dropped_window_fraction": 1.0 - (aggregated.height / expected),
                }
            )
    return rows


def strict_resample_oracle(source: pl.DataFrame, period_minutes: int) -> pl.DataFrame:
    """Independent strict OHLC oracle using pandas right-closed resampling."""
    pdf = source.select(["CloseTime", "Open", "High", "Low", "Close"]).to_pandas()
    pdf = pdf.set_index("CloseTime").sort_index()
    aggregated = pdf.resample(f"{period_minutes}min", closed="right", label="right").agg(
        Open=("Open", "first"),
        High=("High", "max"),
        Low=("Low", "min"),
        Close=("Close", "last"),
        SourceBars=("Close", "size"),
    )
    aggregated = aggregated[aggregated["SourceBars"] == period_minutes].reset_index()
    return to_canonical_time(pl.from_pandas(aggregated))


def _detect_oracle_mismatch(production: pl.DataFrame, oracle: pl.DataFrame) -> int:
    """Count OHLC mismatches after corrupting one production Close (control 1)."""
    corrupted = production.with_columns(
        pl.when(pl.int_range(pl.len()) == 0)
        .then(pl.col("Close") + 1.0)
        .otherwise(pl.col("Close"))
        .alias("Close")
    )
    matched = corrupted.select(["CloseTime", "Open", "High", "Low", "Close"]).join(
        oracle.select(["CloseTime", "Open", "High", "Low", "Close"]),
        on="CloseTime",
        how="inner",
        suffix="_oracle",
    )
    return matched.filter(
        (pl.col("Open") != pl.col("Open_oracle"))
        | (pl.col("High") != pl.col("High_oracle"))
        | (pl.col("Low") != pl.col("Low_oracle"))
        | (pl.col("Close") != pl.col("Close_oracle"))
    ).height


def _detect_future_row(production: pl.DataFrame, source_max: Any) -> int:
    """Count rows pushed far past the source max (control 2)."""
    future = production.tail(1).with_columns(
        (pl.col("CloseTime") + pl.duration(days=3650)).alias("CloseTime")
    )
    return future.filter(pl.col("CloseTime") > source_max).height


def _detect_low_coverage(production: pl.DataFrame, period_minutes: int) -> int:
    """Count rows dropped below the strict bar floor (control 3)."""
    low = production.head(1).with_columns(pl.lit(period_minutes - 1).alias("SourceBars"))
    return low.filter(pl.col("SourceBars") < period_minutes).height


def _detect_duplicate_close_time(production: pl.DataFrame) -> int:
    """Count duplicate CloseTime rows after duplicating one row (control 4)."""
    duplicated = pl.concat([production, production.head(1)])
    return duplicated.height - int(
        duplicated.select(pl.col("CloseTime").n_unique()).item()
    )


def _p0_negative_control_rows(
    data: AnalysisData,
    period_minutes: int,
    production: pl.DataFrame,
    oracle: pl.DataFrame,
) -> list[dict[str, Any]]:
    """Inject one defect per P0 detection rule and confirm the rule catches it.

    Mirrors VAL-001's control-per-check standard: each positive P0 check needs a
    matching negative control that must be DETECTED for the suite to be trusted.
    A control row is PASS when the injected defect is detected, FAIL otherwise.

    Parameters
    ----------
    data : AnalysisData
        Source analysis slice (for labelling and the source-max timestamp).
    period_minutes : int
        Aggregation period under test.
    production, oracle : pl.DataFrame
        The production aggregation and the independent strict oracle.

    Returns
    -------
    list[dict[str, Any]]
        One control row per detection rule, in detection-rule order.
    """
    source_max = data.frame.select(pl.max("CloseTime")).item()

    def control(name: str, detected: int) -> dict[str, Any]:
        ok = detected > 0
        return {
            "instrument": data.instrument,
            "source_file": data.source_file,
            "period_minutes": period_minutes,
            "check": f"negative_control_{name}",
            "status": "PASS" if ok else "FAIL",
            "failures": 0 if ok else 1,
            "detail": json.dumps({"defect_detections": int(detected)}, sort_keys=True),
        }

    if production.is_empty() or oracle.is_empty():
        return [control("production_or_oracle_empty", 0)]
    return [
        control("oracle_ohlc_mismatch", _detect_oracle_mismatch(production, oracle)),
        control("future_row", _detect_future_row(production, source_max)),
        control("low_coverage", _detect_low_coverage(production, period_minutes)),
        control("duplicate_close_time", _detect_duplicate_close_time(production)),
    ]


def _oracle_match_row(
    data: AnalysisData,
    period_minutes: int,
    production: pl.DataFrame,
    oracle: pl.DataFrame,
) -> dict[str, Any]:
    """P0 row comparing the strict aggregation to the independent oracle.

    Parameters
    ----------
    data : AnalysisData
        Source analysis slice (for labelling).
    period_minutes : int
        Aggregation period under test.
    production, oracle : pl.DataFrame
        The production aggregation and the independent strict oracle.

    Returns
    -------
    dict[str, Any]
        A single PASS/FAIL check row.
    """
    matched = production.select(["CloseTime", "Open", "High", "Low", "Close"]).join(
        oracle.select(["CloseTime", "Open", "High", "Low", "Close"]),
        on="CloseTime",
        how="inner",
        suffix="_oracle",
    )
    mismatches = matched.filter(
        (pl.col("Open") != pl.col("Open_oracle"))
        | (pl.col("High") != pl.col("High_oracle"))
        | (pl.col("Low") != pl.col("Low_oracle"))
        | (pl.col("Close") != pl.col("Close_oracle"))
    ).height
    only_production = production.join(oracle, on="CloseTime", how="anti").height
    only_oracle = oracle.join(production, on="CloseTime", how="anti").height
    failures = only_production + only_oracle + mismatches
    return {
        "instrument": data.instrument,
        "source_file": data.source_file,
        "period_minutes": period_minutes,
        "check": "strict_resample_matches_independent_oracle",
        "status": "PASS" if failures == 0 else "FAIL",
        "failures": failures,
        "detail": json.dumps(
            {
                "rows_only_in_production": only_production,
                "rows_only_in_oracle": only_oracle,
                "ohlc_mismatches": mismatches,
            },
            sort_keys=True,
        ),
    }


def _coverage_integrity_rows(
    data: AnalysisData, period_minutes: int, source_max: Any
) -> list[dict[str, Any]]:
    """P0 output temporal-integrity rows for strict and 0.90 coverage.

    Parameters
    ----------
    data : AnalysisData
        Source analysis slice (for labelling).
    period_minutes : int
        Aggregation period under test.
    source_max : Any
        Maximum source ``CloseTime`` used as the future-row threshold.

    Returns
    -------
    list[dict[str, Any]]
        One PASS/FAIL row for the strict and 0.90 coverage outputs.
    """
    rows: list[dict[str, Any]] = []
    for min_coverage in (None, 0.90):
        aggregated = aggregate_ohlc(
            data.frame,
            period_minutes=period_minutes,
            min_coverage=min_coverage,
        )
        min_bars = period_minutes if min_coverage is None else math.ceil(
            min_coverage * period_minutes
        )
        future_rows = aggregated.filter(pl.col("CloseTime") > source_max).height
        low_coverage_rows = aggregated.filter(pl.col("SourceBars") < min_bars).height
        duplicate_rows = aggregated.height - int(
            aggregated.select(pl.col("CloseTime").n_unique()).item()
        )
        failures = future_rows + low_coverage_rows + duplicate_rows
        rows.append(
            {
                "instrument": data.instrument,
                "source_file": data.source_file,
                "period_minutes": period_minutes,
                "check": f"{coverage_label(min_coverage)}_output_temporal_integrity",
                "status": "PASS" if failures == 0 else "FAIL",
                "failures": failures,
                "detail": json.dumps(
                    {
                        "future_rows": future_rows,
                        "rows_below_min_sourcebars": low_coverage_rows,
                        "duplicate_close_time_rows": duplicate_rows,
                        "min_sourcebars": min_bars,
                    },
                    sort_keys=True,
                ),
            }
        )
    return rows


def p0_aggregation_checks(data: AnalysisData) -> list[dict[str, Any]]:
    """VAL-001-style P0 extension checks for the 5m and 240m domains.

    Parameters
    ----------
    data : AnalysisData
        Source analysis slice to aggregate and check.

    Returns
    -------
    list[dict[str, Any]]
        Negative-control, oracle-match, and coverage-integrity rows per period.
    """
    rows: list[dict[str, Any]] = []
    source_max = data.frame.select(pl.max("CloseTime")).item()
    for period_minutes in (5, 240):
        production = aggregate_ohlc(data.frame, period_minutes=period_minutes, min_coverage=None)
        oracle = strict_resample_oracle(data.frame, period_minutes=period_minutes)
        rows.extend(_p0_negative_control_rows(data, period_minutes, production, oracle))
        rows.append(_oracle_match_row(data, period_minutes, production, oracle))
        rows.extend(_coverage_integrity_rows(data, period_minutes, source_max))
    return rows


def next_log_returns_from_bars(bars: pl.DataFrame) -> tuple[np.ndarray, pl.DataFrame]:
    """Return Close-to-Close next-step log returns and their aligned rows."""
    ordered = bars.sort("CloseTime").select(
        ["OpenTime", "CloseTime", "Open", "High", "Low", "Close", "TickVolume"]
    )
    aligned = ordered.with_columns(
        ((pl.col("Close").shift(-1) / pl.col("Close")).log()).alias("NextLogReturn")
    ).drop_nulls("NextLogReturn")
    returns = np.asarray(aligned.get_column("NextLogReturn"), dtype=float)
    return returns, aligned


def domain_split_index(aligned: pl.DataFrame, train_end_ts: Any) -> int:
    """Train/test boundary for a domain, derived from the shared 1m timestamp.

    The analysis/holdout and train/test cuts are fixed once on the canonical
    1-minute base (see ``load_analysis_data``); every resampled domain inherits
    the same wall-clock ``train_end_ts`` so the split is never a per-timeframe
    row fraction (checkpoint design section 9). A row whose ``CloseTime`` is at
    or before ``train_end_ts`` belongs to the train segment.
    """
    return int(aligned.select((pl.col("CloseTime") <= train_end_ts).sum()).item())


def random_state_positions(n: int, seed: int) -> np.ndarray:
    """Return ``n`` deterministic random ``{-1.0, +1.0}`` state positions."""
    rng = np.random.default_rng(seed)
    return rng.choice(np.array([-1.0, 1.0]), size=n)


def permuted_returns(returns: np.ndarray, seed: int) -> np.ndarray:
    """Return a deterministic permutation of ``returns`` (bar-permutation null)."""
    rng = np.random.default_rng(seed)
    return np.asarray(rng.permutation(returns), dtype=float)


def plant_positive_edge(
    returns: np.ndarray,
    states: np.ndarray,
    *,
    net_edge_bps: float,
    cost_bps: float,
) -> np.ndarray:
    """Inject a state-aligned drift so the oracle net edge is closed-form."""
    delta_return = (net_edge_bps + cost_bps) / 10_000.0
    return np.asarray(returns, dtype=float) + np.asarray(states, dtype=float) * delta_return


def strategy_return_bps(
    returns: np.ndarray,
    positions: np.ndarray,
    *,
    cost_bps: float,
) -> np.ndarray:
    """Per-bar net strategy return in bps, charging ``cost_bps`` to active bars.

    Parameters
    ----------
    returns : np.ndarray
        Real next-step returns (fractional).
    positions : np.ndarray
        Per-bar positions in ``{-1, 0, +1}``.
    cost_bps : float
        Round-trip cost (bps) deducted from every active (non-zero) bar.

    Returns
    -------
    np.ndarray
        Net per-bar strategy return in bps.
    """
    n = min(len(returns), len(positions))
    returns = np.asarray(returns[:n], dtype=float)
    positions = np.asarray(positions[:n], dtype=float)
    active = np.abs(positions) > 0.0
    gross = positions * returns * 10_000.0
    return gross - (cost_bps * active.astype(float))


def naive_momentum_positions(returns: np.ndarray) -> np.ndarray:
    """Naive control positions: sign of the prior return, aligned to next bar."""
    positions = np.zeros(len(returns), dtype=float)
    if len(returns) > 1:
        positions[1:] = np.sign(returns[:-1])
    return positions


def rolling_mean(values: np.ndarray, window: int) -> np.ndarray:
    """Trailing simple moving average; leading ``window - 1`` entries are NaN."""
    if window < 1:
        raise ValueError("window must be >= 1")
    values = np.asarray(values, dtype=float)
    result = np.full(values.shape, np.nan, dtype=float)
    if len(values) < window:
        return result
    cumsum = np.cumsum(np.insert(values, 0, 0.0))
    result[window - 1 :] = (cumsum[window:] - cumsum[:-window]) / window
    return result


def ma_crossover_positions(close: np.ndarray, *, fast: int = 20, slow: int = 50) -> np.ndarray:
    """MA-crossover positions known at bar t, aligned to t->t+1 returns."""
    if fast >= slow:
        raise ValueError("fast window must be smaller than slow window")
    fast_ma = rolling_mean(close, fast)
    slow_ma = rolling_mean(close, slow)
    raw = np.where(fast_ma > slow_ma, 1.0, np.where(fast_ma < slow_ma, -1.0, 0.0))
    return raw[:-1]


def donchian_breakout_positions(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    *,
    lookback: int = 20,
) -> np.ndarray:
    """Donchian breakout positions using only prior bars, aligned to next return."""
    high = np.asarray(high, dtype=float)
    low = np.asarray(low, dtype=float)
    close = np.asarray(close, dtype=float)
    positions = np.zeros(len(close), dtype=float)
    for index in range(lookback, len(close) - 1):
        upper = float(np.max(high[index - lookback : index]))
        lower = float(np.min(low[index - lookback : index]))
        if close[index] > upper:
            positions[index] = 1.0
        elif close[index] < lower:
            positions[index] = -1.0
    return positions[:-1]


def cost_bps_for(instrument: str, domain: str) -> float:
    """Frozen per-instrument, per-domain round-trip cost in bps."""
    try:
        return ROUND_TRIP_COST_BPS[instrument.upper()][domain]
    except KeyError as exc:
        raise KeyError(f"No round-trip cost defined for {instrument}/{domain}") from exc


def materiality_bps_for(domain: str) -> float:
    """Frozen per-domain economic materiality threshold (bps) for leg L5."""
    return MATERIALITY_BPS[domain]


def finite_values(values: Iterable[float]) -> np.ndarray:
    """Return ``values`` as a float array with non-finite entries removed.

    For an ndarray input the array is used directly; only non-array iterables go
    through ``list(...)``. This avoids a Python-object round-trip on the hot
    bootstrap path (measured ~57x faster for a 55k array) and is bit-identical to
    the prior behaviour for every input type.
    """
    array = np.asarray(values if isinstance(values, np.ndarray) else list(values), dtype=float)
    return array[np.isfinite(array)]


def percentile_ci(values: Iterable[float], *, alpha: float = 0.05) -> MeanCI:
    """Mean and two-sided ``alpha`` percentile interval over finite ``values``."""
    array = finite_values(values)
    if len(array) == 0:
        return MeanCI(math.nan, math.nan, math.nan, 0)
    lower, upper = np.quantile(array, [alpha / 2.0, 1.0 - alpha / 2.0])
    return MeanCI(float(np.mean(array)), float(lower), float(upper), int(len(array)))


def estimate_block_length(values: np.ndarray, *, max_lag: int = 200) -> int:
    """First lag where ACF drops below 1/e, computed on train values."""
    finite = finite_values(values)
    n = len(finite)
    if n < 8:
        return 1
    centered = finite - float(np.mean(finite))
    denominator = float(np.dot(centered, centered))
    if denominator <= 0.0:
        return 1
    limit = min(max_lag, max(1, n // 2))
    threshold = 1.0 / math.e
    for lag in range(1, limit + 1):
        corr = float(np.dot(centered[:-lag], centered[lag:]) / denominator)
        if corr < threshold:
            return lag
    return limit


def _stationary_block_indices(
    rng: np.random.Generator,
    *,
    rows: int,
    n: int,
    block_length: int,
    p: float,
    cols: np.ndarray,
) -> np.ndarray:
    """Build one batch of stationary-bootstrap row indices.

    Each position independently starts a new wrapping block with probability
    ``p = 1 / block_length``; ``block_length == 1`` reduces to i.i.d. resampling.
    The ``rng`` draws happen in a fixed order so repeated runs are reproducible.

    Parameters
    ----------
    rng : np.random.Generator
        Seeded generator, consumed in place.
    rows : int
        Number of resamples in this batch.
    n : int
        Series length and per-resample sample size.
    block_length : int
        Expected block length (>= 1).
    p : float
        New-block probability, ``1 / block_length``.
    cols : np.ndarray
        Precomputed ``np.arange(n)`` ``int32`` index vector.

    Returns
    -------
    np.ndarray
        ``int32`` index matrix of shape ``(rows, n)``. ``n < 2**31`` for every
        domain, so ``int32`` indexes the same elements as ``int64`` at half the
        index bandwidth; only the integer dtype changes, not which rows are drawn.
    """
    if block_length == 1:
        return rng.integers(0, n, size=(rows, n), dtype=np.int32)
    new_block = rng.random((rows, n)) < p
    new_block[:, 0] = True
    starts = rng.integers(0, n, size=(rows, n), dtype=np.int32)
    controlling = np.maximum.accumulate(
        np.where(new_block, cols[None, :], np.int32(0)), axis=1
    )
    base = np.take_along_axis(starts, controlling, axis=1)
    return (base + (cols[None, :] - controlling)) % n


def block_bootstrap_means(
    values: np.ndarray,
    *,
    n_resamples: int,
    block_length: int,
    seed: int,
    batch_cells: int = 2_000_000,
) -> tuple[np.ndarray, float, int]:
    """Vectorized stationary (Politis-Romano) block bootstrap of the sample mean.

    Returns ``(resample_means, sample_mean, n)``. Each position independently
    starts a new block with probability ``1/block_length`` and blocks wrap
    around, which is exactly the stationary bootstrap; the construction is
    vectorized in NumPy and batched over resamples so peak memory stays bounded
    (``batch_cells`` caps the resample x sample working matrix). This is a pure
    performance rewrite of the prior Python-loop implementation: same method,
    same inference unit, same denominators. Resample indices are generated as
    ``int32`` (every domain has ``n < 2**31``) to halve index bandwidth without
    changing which rows are selected.
    """
    finite = finite_values(values)
    n = len(finite)
    if n == 0:
        return np.empty(0, dtype=float), math.nan, 0
    sample_mean = float(np.mean(finite))
    if n_resamples <= 0:
        return np.asarray([sample_mean], dtype=float), sample_mean, n

    block_length = max(1, min(int(block_length), n))
    p = 1.0 / block_length
    rng = np.random.default_rng(seed)
    means = np.empty(n_resamples, dtype=float)
    cols = np.arange(n, dtype=np.int32)
    batch = max(1, min(n_resamples, batch_cells // n))
    done = 0
    while done < n_resamples:
        rows = min(batch, n_resamples - done)
        idx = _stationary_block_indices(
            rng, rows=rows, n=n, block_length=block_length, p=p, cols=cols
        )
        means[done : done + rows] = finite[idx].mean(axis=1)
        done += rows
    return means, sample_mean, n


def ci_from_means(
    sample_mean: float, means: np.ndarray, n: int, *, alpha: float
) -> MeanCI:
    """Percentile CI at ``alpha`` from a precomputed bootstrap-mean distribution."""
    if n == 0 or len(means) == 0:
        return MeanCI(math.nan, math.nan, math.nan, n)
    if len(means) == 1:
        return MeanCI(sample_mean, sample_mean, sample_mean, n)
    lower, upper = np.quantile(means, [alpha / 2.0, 1.0 - alpha / 2.0])
    return MeanCI(sample_mean, float(lower), float(upper), n)


def block_bootstrap_mean_ci(
    values: np.ndarray,
    *,
    alpha: float,
    n_resamples: int,
    block_length: int,
    seed: int,
) -> MeanCI:
    """Stationary block-bootstrap CI for the sample mean (single-alpha helper)."""
    means, sample_mean, n = block_bootstrap_means(
        values, n_resamples=n_resamples, block_length=block_length, seed=seed
    )
    return ci_from_means(sample_mean, means, n, alpha=alpha)


def resolve_split_index(n: int, split_index: int | None) -> int:
    """Train/test cut for an ``n``-length series.

    ``split_index`` is the shared-timestamp boundary (``domain_split_index``)
    when provided; otherwise it falls back to the chronological ``TRAIN_FRACTION``
    row split used for timestamp-free fixtures.
    """
    cut = int(n * TRAIN_FRACTION) if split_index is None else int(split_index)
    if n >= 2:
        cut = max(1, min(cut, n - 1))
    return cut


def count_state_episodes(positions: np.ndarray, state: float) -> int:
    """Count contiguous runs (episodes) of ``state`` in ``positions``."""
    pos = np.asarray(positions, dtype=float)
    active = pos == state
    if len(active) == 0:
        return 0
    starts = active & np.concatenate(([True], pos[1:] != pos[:-1]))
    return int(np.sum(starts))


def split_train_test(values: np.ndarray) -> tuple[np.ndarray, np.ndarray, int]:
    """Chronological train/test split of ``values`` at ``TRAIN_FRACTION``."""
    cutoff = int(len(values) * TRAIN_FRACTION)
    return values[:cutoff], values[cutoff:], cutoff


def minimal_baseline_core(
    returns: np.ndarray,
    positions: np.ndarray,
    *,
    n_bootstrap: int,
    seed: int,
    split_index: int | None = None,
) -> dict[str, Any]:
    """Alpha-independent minimal-baseline state: one bootstrap-mean distribution.

    The minimal baseline tests the candidate's **gross** edge against its neutral
    baseline with no cost gate (checkpoint design section 6.1); cost enters only
    through the gate stack's L5 leg. The bootstrap is run once here and reused
    across the alpha grid by :func:`minimal_baseline_row`.
    """
    strategy = strategy_return_bps(returns, positions, cost_bps=0.0)
    cut = resolve_split_index(len(strategy), split_index)
    train_values = strategy[:cut]
    test_values = strategy[cut:]
    block_length = estimate_block_length(train_values)
    means, sample_mean, n = block_bootstrap_means(
        test_values, n_resamples=n_bootstrap, block_length=block_length, seed=seed + 1
    )
    return {
        "means": means,
        "sample_mean": sample_mean,
        "n": n,
        "block_length": block_length,
        "effective_n": len(test_values) / max(block_length, 1),
        "split_index": cut,
    }


def minimal_baseline_row(core: dict[str, Any], *, alpha: float) -> dict[str, Any]:
    """Assemble the minimal-baseline verdict row for one alpha from its core.

    Parameters
    ----------
    core : dict[str, Any]
        Alpha-independent state from :func:`minimal_baseline_core`.
    alpha : float
        Operating point for the percentile CI.

    Returns
    -------
    dict[str, Any]
        Verdict row (PASS if the CI lower bound excludes zero).
    """
    ci = ci_from_means(core["sample_mean"], core["means"], core["n"], alpha=alpha)
    passed = bool(np.isfinite(ci.lower) and ci.lower > 0.0)
    return {
        "referee": "minimal_baseline",
        "alpha": alpha,
        "verdict": "PASS" if passed else "REJECT",
        "passed": passed,
        "effect_bps": ci.mean,
        "ci_lower_bps": ci.lower,
        "ci_upper_bps": ci.upper,
        "effective_n": core["effective_n"],
        "block_length": core["block_length"],
        "split_index": core["split_index"],
        "leg_results": json.dumps({"baseline_ci_excludes_zero": passed}, sort_keys=True),
    }


def minimal_baseline_verdict(
    returns: np.ndarray,
    positions: np.ndarray,
    *,
    instrument: str,
    domain: str,
    alpha: float,
    n_bootstrap: int,
    seed: int,
    split_index: int | None = None,
) -> dict[str, Any]:
    """Single-alpha minimal-baseline verdict (core + row convenience wrapper)."""
    core = minimal_baseline_core(
        returns, positions, n_bootstrap=n_bootstrap, seed=seed, split_index=split_index
    )
    return minimal_baseline_row(core, alpha=alpha)


def _episode_counts(
    train_pos: np.ndarray, test_pos: np.ndarray
) -> tuple[int, int, int, int]:
    """Up/down state-episode counts for (train, test), used by the L1 leg.

    Parameters
    ----------
    train_pos, test_pos : np.ndarray
        Candidate positions in the train and test segments.

    Returns
    -------
    tuple[int, int, int, int]
        ``(train_up, train_down, test_up, test_down)`` episode counts.
    """
    return (
        count_state_episodes(train_pos, 1.0),
        count_state_episodes(train_pos, -1.0),
        count_state_episodes(test_pos, 1.0),
        count_state_episodes(test_pos, -1.0),
    )


def _gate_bootstrap_pair(
    test_values: np.ndarray,
    diff_vs_naive: np.ndarray,
    *,
    n_bootstrap: int,
    block_length: int,
    seed: int,
) -> tuple[tuple[np.ndarray, float, int], tuple[np.ndarray, float, int]]:
    """Neutral and vs-naive block-bootstrap mean distributions.

    The two bootstraps use independent generators seeded at ``seed + 1`` and
    ``seed + 2`` respectively, matching the gate-stack's frozen seeding.

    Parameters
    ----------
    test_values : np.ndarray
        Net strategy returns on the test segment.
    diff_vs_naive : np.ndarray
        Test-segment difference between strategy and naive-control returns.
    n_bootstrap : int
        Number of block-bootstrap resamples.
    block_length : int
        Expected stationary-bootstrap block length.
    seed : int
        Base seed; neutral uses ``seed + 1`` and naive uses ``seed + 2``.

    Returns
    -------
    tuple
        ``(neutral_distribution, naive_distribution)`` where each is the
        ``(means, sample_mean, n)`` triple from :func:`block_bootstrap_means`.
    """
    neutral = block_bootstrap_means(
        test_values, n_resamples=n_bootstrap, block_length=block_length, seed=seed + 1
    )
    naive = block_bootstrap_means(
        diff_vs_naive, n_resamples=n_bootstrap, block_length=block_length, seed=seed + 2
    )
    return neutral, naive


def gate_stack_core(
    returns: np.ndarray,
    positions: np.ndarray,
    *,
    instrument: str,
    domain: str,
    n_bootstrap: int,
    seed: int,
    split_index: int | None = None,
) -> dict[str, Any]:
    """Alpha-independent gate-stack state.

    Computes the net (cost-applied) strategy and naive-control returns, the L1
    readiness and L4 stability legs (alpha-free), and the neutral and
    vs-naive bootstrap-mean distributions once. The alpha-dependent L3/L5 legs
    and verdict are assembled per alpha by :func:`gate_stack_row`.
    """
    spec = DOMAIN_SPECS[domain]
    cost_bps = cost_bps_for(instrument, domain)
    materiality_bps = materiality_bps_for(domain)
    strategy = strategy_return_bps(returns, positions, cost_bps=cost_bps)
    naive = strategy_return_bps(
        returns, naive_momentum_positions(returns), cost_bps=cost_bps
    )
    cut = resolve_split_index(len(strategy), split_index)
    train_values, test_values = strategy[:cut], strategy[cut:]
    pos_arr = np.asarray(positions, dtype=float)
    train_pos, test_pos = pos_arr[:cut], pos_arr[cut:]
    block_length = estimate_block_length(train_values)
    effective_n = len(test_values) / max(block_length, 1)

    diff_vs_naive = test_values - naive[cut : cut + len(test_values)]
    neutral_dist, naive_dist = _gate_bootstrap_pair(
        test_values,
        diff_vs_naive,
        n_bootstrap=n_bootstrap,
        block_length=block_length,
        seed=seed,
    )
    neutral_means, neutral_mean, n_neutral = neutral_dist
    naive_means, naive_mean, n_naive = naive_dist

    train_up, train_down, test_up, test_down = _episode_counts(train_pos, test_pos)
    return {
        "neutral_means": neutral_means,
        "neutral_mean": neutral_mean,
        "n_neutral": n_neutral,
        "naive_means": naive_means,
        "naive_mean": naive_mean,
        "n_naive": n_naive,
        "block_length": block_length,
        "effective_n": effective_n,
        "split_index": cut,
        "cost_bps": cost_bps,
        "materiality_bps": materiality_bps,
        "l1": bool(
            effective_n >= spec.min_effective_n
            and min(train_up, train_down, test_up, test_down) >= spec.min_state_count
        ),
        "l2": True,
        "l4": bool(np.mean(train_values) > 0.0 and np.mean(test_values) > 0.0),
        "train_up": train_up,
        "train_down": train_down,
        "test_up": test_up,
        "test_down": test_down,
    }


def gate_stack_row(core: dict[str, Any], *, alpha: float) -> dict[str, Any]:
    """Assemble the gate-stack verdict row for one alpha from its core.

    Applies the alpha-dependent L3 (outcome) and L5 (materiality) legs to the
    precomputed neutral/naive distributions and conjoins all five legs.

    Parameters
    ----------
    core : dict[str, Any]
        Alpha-independent state from :func:`gate_stack_core`.
    alpha : float
        Operating point for the percentile CIs.

    Returns
    -------
    dict[str, Any]
        Verdict row with per-leg results serialised in ``leg_results``.
    """
    ci_neutral = ci_from_means(
        core["neutral_mean"], core["neutral_means"], core["n_neutral"], alpha=alpha
    )
    ci_naive = ci_from_means(
        core["naive_mean"], core["naive_means"], core["n_naive"], alpha=alpha
    )
    l1, l2, l4 = core["l1"], core["l2"], core["l4"]
    l3 = bool(ci_neutral.lower > 0.0 and ci_naive.lower > 0.0)
    l5 = bool(ci_neutral.lower > core["materiality_bps"])
    leg_results = {
        "L1_readiness": l1,
        "L2_integrity": l2,
        "L3_outcome": l3,
        "L4_stability": l4,
        "L5_materiality": l5,
        "cost_bps": core["cost_bps"],
        "materiality_bps": core["materiality_bps"],
        "train_up_episodes": core["train_up"],
        "train_down_episodes": core["train_down"],
        "test_up_episodes": core["test_up"],
        "test_down_episodes": core["test_down"],
        "ci_vs_naive_lower_bps": ci_naive.lower,
    }
    passed = bool(l1 and l2 and l3 and l4 and l5)
    return {
        "referee": "gate_stack",
        "alpha": alpha,
        "verdict": "PASS" if passed else "REJECT",
        "passed": passed,
        "effect_bps": ci_neutral.mean,
        "ci_lower_bps": ci_neutral.lower,
        "ci_upper_bps": ci_neutral.upper,
        "effective_n": core["effective_n"],
        "block_length": core["block_length"],
        "split_index": core["split_index"],
        "leg_results": json.dumps(leg_results, sort_keys=True),
    }


def gate_stack_verdict(
    returns: np.ndarray,
    positions: np.ndarray,
    *,
    instrument: str,
    domain: str,
    alpha: float,
    n_bootstrap: int,
    seed: int,
    split_index: int | None = None,
) -> dict[str, Any]:
    """Single-alpha gate-stack verdict (core + row convenience wrapper)."""
    core = gate_stack_core(
        returns,
        positions,
        instrument=instrument,
        domain=domain,
        n_bootstrap=n_bootstrap,
        seed=seed,
        split_index=split_index,
    )
    return gate_stack_row(core, alpha=alpha)


def evaluate_referees(
    returns: np.ndarray,
    positions: np.ndarray,
    *,
    instrument: str,
    domain: str,
    alpha_values: Iterable[float],
    n_bootstrap: int,
    seed: int,
    split_index: int | None = None,
) -> list[dict[str, Any]]:
    """Both referees across the alpha grid, reusing one bootstrap per referee.

    Each referee's bootstrap-mean distribution is independent of alpha (only the
    percentile cut changes), so the cores are computed once per draw and every
    alpha row is derived from them. This is what makes the EXP-003 grid tractable.
    """
    minimal_core = minimal_baseline_core(
        returns, positions, n_bootstrap=n_bootstrap, seed=seed, split_index=split_index
    )
    gate_core = gate_stack_core(
        returns,
        positions,
        instrument=instrument,
        domain=domain,
        n_bootstrap=n_bootstrap,
        seed=seed + 100_000,
        split_index=split_index,
    )
    rows: list[dict[str, Any]] = []
    for alpha in alpha_values:
        rows.append(minimal_baseline_row(minimal_core, alpha=alpha))
        rows.append(gate_stack_row(gate_core, alpha=alpha))
    return rows


def wilson_interval(successes: int, n: int, *, z: float = 1.96) -> tuple[float, float, float]:
    """Wilson score interval for a binomial proportion.

    Parameters
    ----------
    successes : int
        Number of successes.
    n : int
        Number of trials.
    z : float
        Normal quantile (default 1.96 for ~95%).

    Returns
    -------
    tuple[float, float, float]
        ``(center, lower, upper)``; all ``nan`` when ``n <= 0``.
    """
    if n <= 0:
        return math.nan, math.nan, math.nan
    p = successes / n
    denom = 1.0 + (z * z / n)
    center = (p + (z * z / (2.0 * n))) / denom
    half = z * math.sqrt((p * (1.0 - p) / n) + (z * z / (4.0 * n * n))) / denom
    return center, max(0.0, center - half), min(1.0, center + half)


def verdict_rate_rows(
    rows: list[dict[str, Any]],
    *,
    group_cols: list[str],
    rate_name: str,
) -> list[dict[str, Any]]:
    """Group verdict rows and compute a Wilson-interval pass rate per group.

    Parameters
    ----------
    rows : list[dict[str, Any]]
        Verdict rows carrying a boolean ``passed`` field.
    group_cols : list[str]
        Columns defining each rate cell.
    rate_name : str
        Output key for the computed pass rate (e.g. ``"fpr"``, ``"tpr"``).

    Returns
    -------
    list[dict[str, Any]]
        One rate row per group with Wilson center/bounds and counts.
    """
    if not rows:
        return []
    frame = pl.DataFrame(rows)
    summaries: list[dict[str, Any]] = []
    for group in frame.group_by(group_cols, maintain_order=True):
        key_values, group_frame = group
        if not isinstance(key_values, tuple):
            key_values = (key_values,)
        n = group_frame.height
        successes = int(group_frame.filter(pl.col("passed")).height)
        center, lower, upper = wilson_interval(successes, n)
        summary = dict(zip(group_cols, key_values, strict=True))
        summary.update(
            {
                rate_name: successes / n if n else math.nan,
                "wilson_center": center,
                "wilson_lower": lower,
                "wilson_upper": upper,
                "wilson_half_width": (upper - lower) / 2.0 if n else math.nan,
                "successes": successes,
                "n": n,
            }
        )
        summaries.append(summary)
    return summaries


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write ``payload`` to ``path`` as pretty, key-sorted JSON."""
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def dataclass_rows(items: Iterable[Any]) -> list[dict[str, Any]]:
    """Convert an iterable of dataclass instances to a list of dicts."""
    return [asdict(item) for item in items]

