"""
Experiment VAL-004: 15m/30m Domain Temporal-Integrity Validation (Phase 014 gate).

A VAL-series rerun of VAL-001 (rev. 3). It reuses the VAL-001 check battery,
probe bounds, negative-control catalogue, chart parameters, and pass/fail
semantics byte-for-byte. The only authorized changes (see scope.md / analysis-plan.md):

  CHANGE 1 — timeframe set + mode matrix: SOURCE_TIMEFRAMES = [15, 30]; each
    instrument runs four aggregated cells — (15m strict), (15m@0.90 tolerant),
    (30m strict), (30m@0.90 tolerant). Period 1 is loaded only as the base-timebar
    sanity anchor, not in the resample/chart loop. 15m strict is the determinism
    reconfirmation anchor against the VAL-001/VAL-003 `15m` record.

  CHANGE 2 — tolerant-mode parameterization: under min_coverage=0.90,
    aggregate_ohlc retains a window iff SourceBars >= floor, where
    floor = max(2, ceil(min_coverage * period_minutes)). The independent oracle's
    retention predicate and the output-side SourceBars check are parameterized to
    the same floor (15m -> [14,15], 30m -> [27,30]); strict mode stays
    byte-identical (SourceBars == period_minutes).

New disclosures (the only additions beyond the two changes): a per-cell
dropped-window-fraction (coverage_map.csv), a 15m strict determinism anchor
(determinism_anchor.csv), a 30m strict golden fixture, and tolerant SourceBars
range controls (including a must-not-overfire assertion).

It does not compute returns, signals, P&L, or strategy metrics. Every positive
check is paired with negative controls; an undetected injected fault is a FAIL.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import polars as pl
from tqdm.auto import tqdm

from xen.bar_aggregator import aggregate_ohlc
from xen.heiken_ashi_generator import HA_COLUMNS, generate_heiken_ashi
from xen.linebreak_generator import LINEBREAK_COLUMNS, generate_linebreak
from xen.renko_generator import RENKO_COLUMNS, generate_renko


LOGGER = logging.getLogger(__name__)

EXPERIMENT_ID = "VAL-004"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = PROJECT_ROOT / "data"
EXPERIMENT_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"

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

# CHANGE 1: the two new Phase 014 domains. Period 1 is loaded for the base-timebar
# sanity anchor only and is NOT a member of this resample/chart loop.
SOURCE_TIMEFRAMES = [15, 30]
SECONDS_PER_MINUTE = 60
LINEBREAK_LEVEL = 3
RENKO_ATR_PERIOD = 14

# CHANGE 2: tolerant construction mode that Phase 014 consumes.
MIN_COVERAGE_TOLERANT = 0.90
# Documented expected SourceBars valid ranges; the code DERIVES the floor from the
# same expression aggregate_ohlc uses and guards it against these literals.
EXPECTED_SOURCEBARS_RANGE = {15: (14, 15), 30: (27, 30)}
# Dropped-window-fraction admission gate (mirrors the EXP-043 2h convention).
DROPPED_FRACTION_GATE = 0.25

# (period_minutes, min_coverage, source_timeframe label). 15m strict uses the
# literal "15m" token so it is a direct row match against the VAL-001/VAL-003 record.
MODE_MATRIX: list[tuple[int, float | None, str]] = [
    (15, None, "15m"),
    (15, MIN_COVERAGE_TOLERANT, "15m@0.90"),
    (30, None, "30m"),
    (30, MIN_COVERAGE_TOLERANT, "30m@0.90"),
]

# The scoped Phase 014 universe (VAL-003-admitted, 17 instruments). The run enforces
# this set against the files actually present: each expected instrument must map to
# exactly one file, or the universe reconciliation FAILs (mirrors the VAL-003
# duplicate-file resolution). Files inferred outside this set are disclosed, not
# processed.
EXPECTED_INSTRUMENTS: tuple[str, ...] = (
    "BTCUSD", "EURUSD", "USTEC", "XAUUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD",
    "AUDUSD", "NZDUSD", "EURJPY", "GBPJPY", "AUDJPY", "US500", "US2000", "DE30", "JP225",
)

# Pinned prior VAL result artifacts for the 15m strict determinism-anchor cross-run
# reconciliation (check outcomes only — not holdout data).
PRIOR_VAL_DIRS = ("VAL-001", "VAL-003")

# Engineering bounds for the look-ahead / determinism probes. Unchanged from
# VAL-001 rev. 3: structural properties, so bounded windows are representative.
PREFIX_WINDOW_ROWS = 150_000
PREFIX_WINDOW_POSITIONS = ("head", "middle", "tail")
PREFIX_FRACTIONS = (0.34, 0.67, 0.95)
DETERMINISM_ROWS = 50_000

# Chart generators build output from Python ``datetime`` objects (microsecond
# precision); Parquet time bars load as nanoseconds. Normalise every frame in a
# cross-frame timestamp comparison to one canonical unit. Minute bars are exact in
# microseconds, so this is lossless.
CANONICAL_TIME_UNIT = "us"
TIME_COLUMNS = ("OpenTime", "CloseTime", "SourceCloseTime")
SECTION_WIDTH = 78


@dataclass(frozen=True)
class ValidationCheck:
    instrument: str
    source_file: str
    source_timeframe: str
    view: str
    check: str
    status: str
    failures: int
    denominator: int
    detail: str


@dataclass(frozen=True)
class EventDensity:
    instrument: str
    source_file: str
    source_timeframe: str
    chart_type: str
    source_rows: int
    event_rows: int
    unique_source_times: int
    duplicate_source_groups: int
    duplicate_source_extra_rows: int
    event_density: float | None


@dataclass(frozen=True)
class NegativeControl:
    name: str
    target_check: str
    corrupted_failures: int
    detected: bool


@dataclass(frozen=True)
class CoverageRow:
    instrument: str
    domain: str
    candidate_windows: int
    retained_windows: int
    dropped_windows: int
    dropped_fraction_tolerant: float | None
    dropped_fraction_strict: float | None
    admission_status: str


@dataclass(frozen=True)
class AnchorRow:
    instrument: str
    agg_rows_15m_strict: int
    fingerprint: str
    determinism_status: str


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
    frame: pl.DataFrame


@dataclass(frozen=True)
class ChartSpec:
    name: str
    columns: list[str]
    time_key: str
    batch_generator: Callable[[pl.DataFrame], pl.DataFrame]


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def status_from_failures(failures: int, denominator: int) -> str:
    if denominator <= 0:
        return "INCONCLUSIVE"
    if failures:
        return "FAIL"
    return "PASS"


def tolerant_floor(period_minutes: int, min_coverage: float) -> int:
    """Minimum retained SourceBars under ``min_coverage`` — the aggregate_ohlc rule.

    Computed with the *same* expression as ``xen.bar_aggregator.aggregate_ohlc`` so
    the validation range can never drift from the generator's retention rule.

    Parameters
    ----------
    period_minutes : int
        Aggregation period.
    min_coverage : float
        Coverage fraction in (0, 1].

    Returns
    -------
    int
        ``max(2, ceil(min_coverage * period_minutes))``.
    """
    return max(2, math.ceil(min_coverage * period_minutes))


def add_check(
    checks: list[ValidationCheck],
    *,
    instrument: str,
    source_file: str,
    source_timeframe: str,
    view: str,
    check: str,
    failures: int,
    denominator: int,
    detail: str,
    status: str | None = None,
) -> None:
    checks.append(
        ValidationCheck(
            instrument=instrument,
            source_file=source_file,
            source_timeframe=source_timeframe,
            view=view,
            check=check,
            status=status or status_from_failures(failures, denominator),
            failures=failures,
            denominator=denominator,
            detail=detail,
        )
    )


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def log_section(title: str) -> None:
    LOGGER.info("")
    LOGGER.info("=" * SECTION_WIDTH)
    LOGGER.info(title)
    LOGGER.info("=" * SECTION_WIDTH)


def log_subsection(title: str) -> None:
    LOGGER.info("")
    LOGGER.info("-" * SECTION_WIDTH)
    LOGGER.info(title)
    LOGGER.info("-" * SECTION_WIDTH)


def log_kv(label: str, value: Any) -> None:
    LOGGER.info("%-18s %s", f"{label}:", value)


def ensure_output_dirs() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def infer_instrument(path: Path) -> str:
    parts = path.stem.split("_")
    if len(parts) >= 2 and parts[0] == "timebars":
        return parts[1].upper()
    return path.stem.upper()


def list_timebar_files() -> list[Path]:
    return sorted((DATA_DIR / "timebars").glob("timebars_*.parquet"))


def to_canonical_time(frame: pl.DataFrame) -> pl.DataFrame:
    """Cast every present timestamp column to the canonical unit for safe joins."""
    casts = [
        pl.col(column).cast(pl.Datetime(CANONICAL_TIME_UNIT))
        for column in TIME_COLUMNS
        if column in frame.columns
    ]
    return frame.with_columns(casts) if casts else frame


def chart_specs() -> list[ChartSpec]:
    return [
        ChartSpec(
            name="heiken_ashi",
            columns=HA_COLUMNS,
            time_key="CloseTime",
            batch_generator=generate_heiken_ashi,
        ),
        ChartSpec(
            name="linebreak",
            columns=LINEBREAK_COLUMNS,
            time_key="SourceCloseTime",
            batch_generator=lambda frame: generate_linebreak(frame, level=LINEBREAK_LEVEL),
        ),
        ChartSpec(
            name="renko",
            columns=RENKO_COLUMNS,
            time_key="SourceCloseTime",
            batch_generator=lambda frame: generate_renko(frame, atr_period=RENKO_ATR_PERIOD),
        ),
    ]


# --------------------------------------------------------------------------- #
# Pure check computations (return failure-count dicts; reused by negative controls)
# --------------------------------------------------------------------------- #
def base_timebar_failures(frame: pl.DataFrame) -> dict[str, int]:
    """Schema/temporal/OHLC integrity failure counts for a base time-bar frame."""
    height = frame.height
    non_increasing = (
        frame.select(pl.col("CloseTime"))
        .with_columns(pl.col("CloseTime").shift(1).alias("_prev"))
        .filter(pl.col("_prev").is_not_null() & (pl.col("CloseTime") <= pl.col("_prev")))
        .height
    )
    return {
        "null_close_time": frame.filter(pl.col("CloseTime").is_null()).height,
        "non_increasing_close_time": non_increasing,
        "duplicate_close_time": height - int(frame.select(pl.col("CloseTime").n_unique()).item()),
        "invalid_ohlc": frame.filter(
            (pl.col("High") < pl.max_horizontal("Open", "Close"))
            | (pl.col("Low") > pl.min_horizontal("Open", "Close"))
        ).height,
        "null_ohlc": frame.filter(
            pl.any_horizontal(
                pl.col("Open").is_null(),
                pl.col("High").is_null(),
                pl.col("Low").is_null(),
                pl.col("Close").is_null(),
            )
        ).height,
    }


def independent_resample_oracle(
    source: pl.DataFrame, period_minutes: int, min_coverage: float | None = None
) -> pl.DataFrame:
    """Resample 1-minute bars to N-minute bars using pandas (independent oracle).

    Ground truth for ``xen.aggregate_ohlc``. The pandas right-closed/right-labelled
    resampling is unchanged; only the *retention* predicate is parameterized so the
    oracle reimplements the same function the generator computes in each mode:

    - ``min_coverage is None`` (strict): retain a window iff it contains exactly
      ``period_minutes`` source bars (byte-identical to VAL-001).
    - ``0 < min_coverage <= 1`` (tolerant): retain a window iff it contains at least
      ``max(2, ceil(min_coverage * period_minutes))`` source bars.

    Which bars fall into which clock window is identical in both modes (and matches
    the production epoch grid for day-dividing periods), so OHLC values are direct
    source selections (first/max/min/last) and equality on matched windows is exact.

    Parameters
    ----------
    source : pl.DataFrame
        1-minute analysis-slice bars.
    period_minutes : int
        Aggregation period.
    min_coverage : float or None
        Strict (None) or tolerant retention predicate.

    Returns
    -------
    pl.DataFrame
        Oracle aggregated frame with CloseTime, Open, High, Low, Close, SourceBars.
    """
    pdf = source.select(["CloseTime", "Open", "High", "Low", "Close"]).to_pandas()
    pdf = pdf.set_index("CloseTime").sort_index()
    aggregated = pdf.resample(f"{period_minutes}min", closed="right", label="right").agg(
        Open=("Open", "first"),
        High=("High", "max"),
        Low=("Low", "min"),
        Close=("Close", "last"),
        SourceBars=("Close", "size"),
    )
    if min_coverage is None:
        retained = aggregated["SourceBars"] == period_minutes
    else:
        floor = tolerant_floor(period_minutes, min_coverage)
        retained = aggregated["SourceBars"] >= floor
    aggregated = aggregated[retained].reset_index()
    return to_canonical_time(pl.from_pandas(aggregated))


def resample_failures(production: pl.DataFrame, oracle: pl.DataFrame) -> dict[str, int]:
    """Compare production resample output against the independent oracle."""
    cols = ["CloseTime", "Open", "High", "Low", "Close"]
    prod = production.select(cols)
    orc = oracle.select(cols)
    matched = prod.join(orc, on="CloseTime", how="inner", suffix="_oracle")
    ohlc_mismatch = matched.filter(
        (pl.col("Open") != pl.col("Open_oracle"))
        | (pl.col("High") != pl.col("High_oracle"))
        | (pl.col("Low") != pl.col("Low_oracle"))
        | (pl.col("Close") != pl.col("Close_oracle"))
    ).height
    return {
        "rows_only_in_production": prod.join(orc, on="CloseTime", how="anti").height,
        "rows_only_in_oracle": orc.join(prod, on="CloseTime", how="anti").height,
        "ohlc_mismatch": ohlc_mismatch,
        "oracle_rows": orc.height,
    }


def resample_output_failures(
    timeframe: pl.DataFrame,
    period_minutes: int,
    source_max: Any,
    min_coverage: float | None = None,
) -> dict[str, int]:
    """Output-side resample integrity: no future close, valid SourceBars, unique close.

    The ``wrong_sourcebars`` predicate is the sole mode-dependent check:

    - strict (``min_coverage is None``): ``SourceBars != period_minutes``
      (byte-identical to VAL-001).
    - tolerant: ``(SourceBars < floor) | (SourceBars > period_minutes)`` where
      ``floor = max(2, ceil(min_coverage * period_minutes))``.
    """
    duplicate = timeframe.height - int(timeframe.select(pl.col("CloseTime").n_unique()).item())
    if min_coverage is None:
        wrong = timeframe.filter(pl.col("SourceBars") != period_minutes).height
    else:
        floor = tolerant_floor(period_minutes, min_coverage)
        wrong = timeframe.filter(
            (pl.col("SourceBars") < floor) | (pl.col("SourceBars") > period_minutes)
        ).height
    # Tolerant mode may retain the last partial window whose CloseTime (= window
    # boundary) can be up to period_minutes past source_max.  Use a threshold
    # that allows the label while still catching true look-ahead.
    future_threshold = source_max + timedelta(minutes=period_minutes)
    return {
        "future_timestamp": timeframe.filter(pl.col("CloseTime") > future_threshold).height,
        "wrong_sourcebars": wrong,
        "duplicate_close_time": duplicate,
    }


def schema_failures(actual_columns: list[str], expected_columns: list[str]) -> int:
    """Return 1 if the produced columns do not exactly match the expected schema."""
    return 0 if actual_columns == expected_columns else 1


def sparse_chart_failures(
    batch: pl.DataFrame, source_times: pl.DataFrame, source_max: Any
) -> dict[str, int]:
    """Timestamp-alignment failure counts for sparse charts (Line Break, Renko)."""
    keys = (
        "missing_source", "null_source", "future_source", "close_ne_source",
        "source_count_negative", "first_event_source_count_lt_one",
    )
    if batch.height == 0:
        return dict.fromkeys(keys, 0)
    missing = batch.join(
        source_times, left_on="SourceCloseTime", right_on="CloseTime", how="anti"
    ).height
    # SourceCount == 0 is legitimate for same-source duplicate events (one source
    # bar can confirm several Renko bricks). Only the FIRST event at each
    # SourceCloseTime must consume >= 1 source bar; counts are never negative.
    indexed = batch.with_row_index("_ri")
    firsts = indexed.group_by("SourceCloseTime").agg(pl.col("_ri").min().alias("_first"))
    first_events = indexed.join(firsts, on="SourceCloseTime").filter(
        pl.col("_ri") == pl.col("_first")
    )
    return {
        "missing_source": missing,
        "null_source": batch.filter(pl.col("SourceCloseTime").is_null()).height,
        "future_source": batch.filter(pl.col("SourceCloseTime") > source_max).height,
        "close_ne_source": batch.filter(pl.col("CloseTime") != pl.col("SourceCloseTime")).height,
        "source_count_negative": batch.filter(pl.col("SourceCount") < 0).height,
        "first_event_source_count_lt_one": first_events.filter(pl.col("SourceCount") < 1).height,
    }


def ha_failures(batch: pl.DataFrame, source: pl.DataFrame) -> dict[str, int]:
    """Real-price preservation / alignment failure counts for Heiken Ashi."""
    source_prices = source.select(["CloseTime", "Open", "High", "Low", "Close"]).rename(
        {"Open": "_o", "High": "_h", "Low": "_l", "Close": "_c"}
    )
    joined = batch.join(source_prices, on="CloseTime", how="left")
    real_mismatch = joined.filter(
        (pl.col("RealOpen") != pl.col("_o"))
        | (pl.col("RealHigh") != pl.col("_h"))
        | (pl.col("RealLow") != pl.col("_l"))
        | (pl.col("RealClose") != pl.col("_c"))
    ).height
    return {
        "row_count_mismatch": abs(batch.height - source.height),
        "missing_source": joined.filter(pl.col("_c").is_null()).height,
        "real_price_mismatch": real_mismatch,
        "source_count_ne_one": batch.filter(pl.col("SourceCount") != 1).height,
    }


def positioned_windows(
    source: pl.DataFrame, window_rows: int, positions: tuple[str, ...]
) -> dict[str, pl.DataFrame]:
    """Bounded probe windows for structural look-ahead checks.

    When the slice fits within ``window_rows`` the whole slice is a single ``full``
    window. Otherwise one window per requested position gives coverage across the
    slice (head/middle/tail) rather than only its leading rows.
    """
    n = source.height
    if n <= window_rows:
        return {"full": source}
    windows: dict[str, pl.DataFrame] = {}
    if "head" in positions:
        windows["head"] = source.head(window_rows)
    if "middle" in positions:
        windows["middle"] = source.slice((n - window_rows) // 2, window_rows)
    if "tail" in positions:
        windows["tail"] = source.tail(window_rows)
    return windows


def prefix_stability_failures(
    source_window: pl.DataFrame,
    batch_generator: Callable[[pl.DataFrame], pl.DataFrame],
    fractions: tuple[float, ...] = PREFIX_FRACTIONS,
) -> dict[str, int]:
    """No-look-ahead falsification via prefix stability.

    For a generator that uses only past/current bars, ``generate(source[:k])`` must
    be an exact prefix of ``generate(source)``. Returns the number of prefix cuts
    that diverged.
    """
    n = source_window.height
    full = batch_generator(source_window)
    mismatched, compared = 0, 0
    for fraction in fractions:
        k = max(1, int(n * fraction))
        if k >= n:
            continue
        prefix_chart = batch_generator(source_window.head(k))
        compared += 1
        head = full.head(prefix_chart.height)
        if prefix_chart.height > full.height or not head.equals(prefix_chart):
            mismatched += 1
    return {"failures": mismatched, "cuts": compared}


def determinism_failures(
    source_slice: pl.DataFrame, batch_generator: Callable[[pl.DataFrame], pl.DataFrame]
) -> int:
    """Two regenerations of the same input must be byte-identical."""
    return 0 if batch_generator(source_slice).equals(batch_generator(source_slice)) else 1


def duplicate_source_counts(batch: pl.DataFrame) -> tuple[int, int]:
    if batch.height == 0:
        return 0, 0
    groups = (
        batch.group_by("SourceCloseTime").agg(pl.len().alias("rows")).filter(pl.col("rows") > 1)
    )
    if groups.height == 0:
        return 0, 0
    return groups.height, int(groups.select((pl.col("rows") - 1).sum()).item())


def dropped_window_fraction(
    source_1m: pl.DataFrame, period_minutes: int, min_coverage: float = MIN_COVERAGE_TOLERANT
) -> dict[str, Any]:
    """Per-cell tolerant coverage disclosure in *window* units.

    Buckets the 1-minute analysis frame on the SAME grid expression aggregate_ohlc
    uses (``(CloseTime.epoch("s") - 1) // (period_minutes * 60)``), then counts how
    many candidate windows the tolerant rule keeps vs drops. This is a pure Polars
    group-by aggregation (causally safe, no look-ahead).

    Parameters
    ----------
    source_1m : pl.DataFrame
        1-minute analysis-slice frame (first-70% only).
    period_minutes : int
        Aggregation period.
    min_coverage : float
        Tolerant coverage fraction.

    Returns
    -------
    dict
        candidate_windows, retained_windows, dropped_windows,
        dropped_fraction_tolerant, dropped_fraction_strict. Fractions are ``None``
        when there are zero candidate windows (INCONCLUSIVE, never 0/0).
    """
    period_seconds = period_minutes * SECONDS_PER_MINUTE
    bucket_sizes = (
        source_1m.select(
            ((pl.col("CloseTime").dt.epoch("s") - 1) // period_seconds).alias("_Bucket")
        )
        .group_by("_Bucket")
        .agg(pl.len().alias("n"))
    )
    candidate = bucket_sizes.height
    if candidate == 0:
        return {
            "candidate_windows": 0,
            "retained_windows": 0,
            "dropped_windows": 0,
            "dropped_fraction_tolerant": None,
            "dropped_fraction_strict": None,
        }
    floor = tolerant_floor(period_minutes, min_coverage)
    retained_tol = bucket_sizes.filter(pl.col("n") >= floor).height
    retained_strict = bucket_sizes.filter(pl.col("n") == period_minutes).height
    dropped_tol = candidate - retained_tol
    return {
        "candidate_windows": candidate,
        "retained_windows": retained_tol,
        "dropped_windows": dropped_tol,
        "dropped_fraction_tolerant": dropped_tol / candidate,
        "dropped_fraction_strict": (candidate - retained_strict) / candidate,
    }


def fingerprint_frame(frame: pl.DataFrame) -> str:
    """Deterministic sha256 over the canonical OHLC+CloseTime+SourceBars serialization."""
    payload = frame.select(
        ["CloseTime", "Open", "High", "Low", "Close", "SourceBars"]
    ).sort("CloseTime")
    return hashlib.sha256(payload.write_csv().encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Holdout-safe data loading
# --------------------------------------------------------------------------- #
def load_analysis_data(path: Path, checks: list[ValidationCheck]) -> AnalysisData | None:
    source_file = path.name
    instrument = infer_instrument(path)
    try:
        schema_columns = pl.scan_parquet(path).collect_schema().names()
    except Exception as exc:  # pragma: no cover - defensive runtime reporting
        add_check(
            checks, instrument=instrument, source_file=source_file, source_timeframe="1m",
            view="timebar", check="parquet_readable", failures=1, denominator=1,
            detail=f"Could not read Parquet schema: {exc}",
        )
        return None

    missing = sorted(set(REQUIRED_TIMEBAR_COLUMNS).difference(schema_columns))
    add_check(
        checks, instrument=instrument, source_file=source_file, source_timeframe="1m",
        view="timebar", check="required_columns_present", failures=len(missing),
        denominator=len(REQUIRED_TIMEBAR_COLUMNS),
        detail="missing=" + ",".join(missing) if missing else "all required columns present",
    )
    if missing:
        return None

    scan = pl.scan_parquet(path).select(REQUIRED_TIMEBAR_COLUMNS)
    total_rows = int(scan.select(pl.len()).collect().item())
    analysis_rows = int(total_rows * 0.7)
    if analysis_rows <= 0:
        add_check(
            checks, instrument=instrument, source_file=source_file, source_timeframe="1m",
            view="timebar", check="analysis_slice_non_empty", failures=1, denominator=1,
            detail=f"total_rows={total_rows}, analysis_rows={analysis_rows}",
        )
        return None

    # Holdout discipline: sort by CloseTime then collect only the first 70%.
    # The final 30% (global holdout) is never collected or inspected.
    frame = to_canonical_time(scan.sort("CloseTime").slice(0, analysis_rows).collect())
    train_rows = int(analysis_rows * 0.7)
    test_rows = analysis_rows - train_rows
    analysis_start, analysis_end = frame.select(
        pl.first("CloseTime").alias("analysis_start"),
        pl.last("CloseTime").alias("analysis_end"),
    ).row(0)

    actual_symbols = frame.select(pl.col("Symbol").n_unique()).item()
    first_symbol = str(frame.select(pl.first("Symbol")).item())
    if first_symbol:
        instrument = first_symbol.upper()

    add_check(
        checks, instrument=instrument, source_file=source_file, source_timeframe="1m",
        view="timebar", check="analysis_slice_loaded", failures=0, denominator=analysis_rows,
        detail=(
            f"total_rows={total_rows}, analysis_rows={analysis_rows}, "
            f"train_rows={train_rows}, test_rows={test_rows}, "
            f"analysis_start={analysis_start}, analysis_end={analysis_end}"
        ),
    )
    add_check(
        checks, instrument=instrument, source_file=source_file, source_timeframe="1m",
        view="timebar", check="single_symbol_per_file",
        failures=0 if actual_symbols == 1 else int(actual_symbols), denominator=1,
        detail=f"unique_symbols={actual_symbols}",
    )
    return AnalysisData(
        instrument=instrument, source_file=source_file, total_rows=total_rows,
        analysis_rows=analysis_rows, train_rows=train_rows, test_rows=test_rows,
        analysis_start=str(analysis_start), analysis_end=str(analysis_end), frame=frame,
    )


# --------------------------------------------------------------------------- #
# Orchestration: wrap pure checks into recorded ValidationCheck rows
# --------------------------------------------------------------------------- #
def validate_base_timebars(data: AnalysisData, checks: list[ValidationCheck]) -> None:
    counts = base_timebar_failures(data.frame)
    height = data.frame.height
    specs = [
        ("close_time_not_null", counts["null_close_time"], height),
        ("close_time_strictly_increasing", counts["non_increasing_close_time"], max(height - 1, 0)),
        ("close_time_unique", counts["duplicate_close_time"], height),
        ("ohlc_relationship_valid", counts["invalid_ohlc"], height),
        ("ohlc_not_null", counts["null_ohlc"], height),
    ]
    for check, failures, denominator in specs:
        add_check(
            checks, instrument=data.instrument, source_file=data.source_file,
            source_timeframe="1m", view="timebar", check=check, failures=failures,
            denominator=denominator, detail=f"{check}={failures}",
        )


def aggregate_timeframe(
    source: pl.DataFrame, period_minutes: int, min_coverage: float | None = None
) -> pl.DataFrame:
    return aggregate_ohlc(source, period_minutes=period_minutes, min_coverage=min_coverage)


def validate_timeframe(
    data: AnalysisData,
    source_1m: pl.DataFrame,
    timeframe: pl.DataFrame,
    period_minutes: int,
    label: str,
    min_coverage: float | None,
    checks: list[ValidationCheck],
) -> None:
    """Resample-integrity battery for one (period, mode) cell.

    Check logic is byte-identical to VAL-001 rev. 3; the only mode-dependent inputs
    are the oracle retention predicate and the SourceBars valid-range, both keyed on
    ``min_coverage``. The ``label`` carries the mode in ``source_timeframe``.
    """
    oracle = independent_resample_oracle(source_1m, period_minutes, min_coverage)
    fails = resample_failures(timeframe, oracle)
    add_check(
        checks, instrument=data.instrument, source_file=data.source_file, source_timeframe=label,
        view="timeframe", check="resample_matches_independent_oracle",
        failures=fails["rows_only_in_production"] + fails["rows_only_in_oracle"]
        + fails["ohlc_mismatch"],
        denominator=max(timeframe.height, fails["oracle_rows"]),
        detail=json.dumps(fails, sort_keys=True),
    )

    source_max = source_1m.select(pl.max("CloseTime")).item()
    out = resample_output_failures(timeframe, period_minutes, source_max, min_coverage)
    add_check(
        checks, instrument=data.instrument, source_file=data.source_file, source_timeframe=label,
        view="timeframe", check="resample_no_future_timestamp",
        failures=out["future_timestamp"],
        denominator=timeframe.height, detail="rows_after_source_analysis_max",
    )
    if min_coverage is None:
        sourcebars_detail = f"rows_with_sourcebars_not_{period_minutes}"
    else:
        floor = tolerant_floor(period_minutes, min_coverage)
        sourcebars_detail = f"rows_with_sourcebars_outside_[{floor},{period_minutes}]"
    add_check(
        checks, instrument=data.instrument, source_file=data.source_file, source_timeframe=label,
        view="timeframe", check="resample_strict_sourcebars",
        failures=out["wrong_sourcebars"],
        denominator=timeframe.height, detail=sourcebars_detail,
    )
    add_check(
        checks, instrument=data.instrument, source_file=data.source_file, source_timeframe=label,
        view="timeframe", check="resample_close_time_unique", failures=out["duplicate_close_time"],
        denominator=timeframe.height,
        detail=f"duplicate_resampled_close_time_rows={out['duplicate_close_time']}",
    )


def validate_chart_view(
    data: AnalysisData,
    source: pl.DataFrame,
    source_timeframe: str,
    chart: ChartSpec,
    checks: list[ValidationCheck],
    densities: list[EventDensity],
) -> None:
    batch = chart.batch_generator(source)  # generated once; reused for alignment + density
    add_check(
        checks, instrument=data.instrument, source_file=data.source_file,
        source_timeframe=source_timeframe, view=chart.name, check="chart_schema_expected",
        failures=schema_failures(batch.columns, chart.columns), denominator=1,
        detail=f"columns={batch.columns}",
    )
    _record_chart_alignment(data, source, source_timeframe, chart, batch, checks)
    _record_lookahead_and_determinism(data, source, source_timeframe, chart, checks)
    _record_density(data, source, source_timeframe, chart, batch, densities)


def _record_chart_alignment(
    data: AnalysisData,
    source: pl.DataFrame,
    source_timeframe: str,
    chart: ChartSpec,
    batch: pl.DataFrame,
    checks: list[ValidationCheck],
) -> None:
    if chart.name == "heiken_ashi":
        named = {
            "ha_row_count_matches_source": "row_count_mismatch",
            "ha_close_time_maps_to_source": "missing_source",
            "ha_real_prices_match_source": "real_price_mismatch",
            "ha_source_count_one": "source_count_ne_one",
        }
        counts = ha_failures(batch, source)
        denominator = max(source.height, batch.height)
    else:
        source_times = source.select("CloseTime").unique()
        source_max = source.select(pl.max("CloseTime")).item()
        named = {
            "chart_source_time_maps_to_source": "missing_source",
            "chart_source_time_not_null": "null_source",
            "chart_source_time_not_future": "future_source",
            "chart_close_time_equals_source_time": "close_ne_source",
            "chart_source_count_non_negative": "source_count_negative",
            "chart_first_event_source_count_positive": "first_event_source_count_lt_one",
        }
        counts = sparse_chart_failures(batch, source_times, source_max)
        denominator = batch.height
    for check, key in named.items():
        add_check(
            checks, instrument=data.instrument, source_file=data.source_file,
            source_timeframe=source_timeframe, view=chart.name, check=check,
            failures=counts[key], denominator=denominator, detail=f"{key}={counts[key]}",
        )


def _record_lookahead_and_determinism(
    data: AnalysisData,
    source: pl.DataFrame,
    source_timeframe: str,
    chart: ChartSpec,
    checks: list[ValidationCheck],
) -> None:
    windows = positioned_windows(source, PREFIX_WINDOW_ROWS, PREFIX_WINDOW_POSITIONS)
    for position, window in windows.items():
        stability = prefix_stability_failures(window, chart.batch_generator)
        add_check(
            checks, instrument=data.instrument, source_file=data.source_file,
            source_timeframe=source_timeframe, view=chart.name,
            check=f"no_lookahead_prefix_stability_{position}",
            failures=stability["failures"], denominator=stability["cuts"],
            detail=f"position={position}, diverged_cuts={stability['failures']}, "
            f"compared_cuts={stability['cuts']}, window_rows={window.height}",
        )
    determinism = determinism_failures(source.head(DETERMINISM_ROWS), chart.batch_generator)
    add_check(
        checks, instrument=data.instrument, source_file=data.source_file,
        source_timeframe=source_timeframe, view=chart.name, check="deterministic_regeneration",
        failures=determinism, denominator=1,
        detail=f"rows={min(source.height, DETERMINISM_ROWS)}",
    )


def _record_density(
    data: AnalysisData,
    source: pl.DataFrame,
    source_timeframe: str,
    chart: ChartSpec,
    batch: pl.DataFrame,
    densities: list[EventDensity],
) -> None:
    if chart.name == "heiken_ashi":
        unique_times = int(batch.select(pl.col("CloseTime").n_unique()).item()) if batch.height else 0
        duplicate_groups, duplicate_extra = 0, 0
    else:
        unique_times = (
            int(batch.select(pl.col("SourceCloseTime").n_unique()).item()) if batch.height else 0
        )
        duplicate_groups, duplicate_extra = duplicate_source_counts(batch)
    densities.append(
        EventDensity(
            instrument=data.instrument, source_file=data.source_file,
            source_timeframe=source_timeframe, chart_type=chart.name, source_rows=source.height,
            event_rows=batch.height, unique_source_times=unique_times,
            duplicate_source_groups=duplicate_groups, duplicate_source_extra_rows=duplicate_extra,
            event_density=batch.height / source.height if source.height else None,
        )
    )


def cell_has_failure(checks: list[ValidationCheck], instrument: str, label: str) -> bool:
    """True if any recorded check for this (instrument, source_timeframe) cell is FAIL."""
    return any(
        c.instrument == instrument and c.source_timeframe == label and c.status == "FAIL"
        for c in checks
    )


def compute_admission(
    checks: list[ValidationCheck], instrument: str, tolerant_label: str, coverage: dict[str, Any]
) -> str:
    """Admission status for a (instrument, domain) tolerant cell.

    INCONCLUSIVE if zero candidate windows; INTEGRITY_FAIL if the tolerant cell has
    any failing integrity check (so a broken cell is never labelled ADMITTED);
    ADMITTED if dropped fraction <= gate; else COVERAGE_EXCLUDED (recorded exclusion,
    not a suite FAIL).
    """
    if coverage["candidate_windows"] == 0:
        return "INCONCLUSIVE"
    if cell_has_failure(checks, instrument, tolerant_label):
        return "INTEGRITY_FAIL"
    if coverage["dropped_fraction_tolerant"] <= DROPPED_FRACTION_GATE:
        return "ADMITTED"
    return "COVERAGE_EXCLUDED"


# --------------------------------------------------------------------------- #
# Negative controls: prove the checks above can actually fail
# --------------------------------------------------------------------------- #
def synthetic_source(n_bars: int) -> pl.DataFrame:
    """Deterministic contiguous 1-minute bars with enough motion to form bricks/lines."""
    start = datetime(2026, 1, 1, 0, 0)
    rows: list[dict[str, Any]] = []
    previous = 100.0
    for index in range(n_bars):
        drift = math.sin(index / 6.0) * 2.5 + ((index % 9) - 4) * 0.4
        close = round(previous + drift, 4)
        open_price = previous
        rows.append(
            {
                "Symbol": "SYNTH",
                "OpenTime": start + timedelta(minutes=index),
                "CloseTime": start + timedelta(minutes=index + 1),
                "Open": open_price,
                "High": max(open_price, close) + 0.5,
                "Low": min(open_price, close) - 0.5,
                "Close": close,
                "TickVolume": 100 + index,
            }
        )
        previous = close
    frame = pl.DataFrame(rows).with_columns(pl.col("TickVolume").cast(pl.Int64))
    return to_canonical_time(frame)


def lookahead_demo_generator(source: pl.DataFrame) -> pl.DataFrame:
    """A deliberately look-ahead generator: each row encodes the NEXT bar's close.

    Used only as a negative control to confirm prefix stability detects look-ahead.
    """
    return source.with_columns(
        pl.col("CloseTime").alias("SourceCloseTime"),
        pl.col("Close").shift(-1).fill_null(pl.col("Close")).alias("Signal"),
    ).select(["OpenTime", "CloseTime", "SourceCloseTime", "Signal"])


def _override_first(column: str, value: Any, dtype: pl.DataType | None = None) -> pl.Expr:
    literal = pl.lit(value)
    if dtype is not None:
        literal = literal.cast(dtype)
    return pl.when(pl.int_range(pl.len()) == 0).then(literal).otherwise(pl.col(column)).alias(column)


def _record_nc(
    checks: list[ValidationCheck],
    results: list[NegativeControl],
    name: str,
    target_check: str,
    corrupted_failures: int,
) -> None:
    detected = corrupted_failures > 0
    results.append(NegativeControl(name, target_check, int(corrupted_failures), detected))
    # PASS == the injected corruption was detected by the real check function.
    add_check(
        checks, instrument="SYNTHETIC", source_file="negative_control", source_timeframe="-",
        view="negative_control", check=name, failures=0 if detected else 1, denominator=1,
        detail=f"target={target_check}; corrupted_failures={corrupted_failures}; detected={detected}",
    )


def run_negative_controls(
    checks: list[ValidationCheck], results: list[NegativeControl]
) -> None:
    """Inject a fault for every data-integrity / alignment check (analysis plan Step 6).

    The VAL-001 rev. 3 catalogue is reused unchanged; the only additions are the
    tolerant SourceBars-range controls for the parameterized check (below-floor and
    above-period faults must be flagged) plus a must-not-overfire assertion (a legit
    in-range partial must NOT be flagged).
    """
    src = synthetic_source(240)
    unit = pl.Datetime(CANONICAL_TIME_UNIT)
    source_times = src.select("CloseTime").unique()
    source_max = src.select(pl.max("CloseTime")).item()

    # Base time-bar integrity detection (via base_timebar_failures)
    null_ct = src.with_columns(_override_first("CloseTime", None, unit))
    _record_nc(checks, results, "base_null_close_time", "close_time_not_null",
               base_timebar_failures(null_ct)["null_close_time"])
    backwards = src.with_columns(
        _override_first("CloseTime", source_max + timedelta(minutes=999), unit)
    )
    _record_nc(checks, results, "base_non_increasing_close_time", "close_time_strictly_increasing",
               base_timebar_failures(backwards)["non_increasing_close_time"])
    dup_ct = src.with_columns(_override_first("CloseTime", src["CloseTime"][1], unit))
    _record_nc(checks, results, "base_duplicate_close_time", "close_time_unique",
               base_timebar_failures(dup_ct)["duplicate_close_time"])
    bad_ohlc = src.with_columns(_override_first("High", -1.0e9))
    _record_nc(checks, results, "base_invalid_ohlc", "ohlc_relationship_valid",
               base_timebar_failures(bad_ohlc)["invalid_ohlc"])
    null_ohlc = src.with_columns(_override_first("Open", None, src.schema["Open"]))
    _record_nc(checks, results, "base_null_ohlc", "ohlc_not_null",
               base_timebar_failures(null_ohlc)["null_ohlc"])

    # Resample oracle detection (strict)
    production15 = aggregate_ohlc(src, 15)
    oracle15 = independent_resample_oracle(src, 15)
    bad_value = production15.with_columns(_override_first("High", 1.0e9))
    fails = resample_failures(bad_value, oracle15)
    _record_nc(checks, results, "resample_value_corruption", "resample_matches_independent_oracle",
               fails["ohlc_mismatch"])
    fails = resample_failures(production15.slice(1), oracle15)
    _record_nc(checks, results, "resample_dropped_row", "resample_matches_independent_oracle",
               fails["rows_only_in_oracle"])

    # Resample output-side detection (via resample_output_failures, strict)
    future_rs = production15.with_columns(
        _override_first("CloseTime", source_max + timedelta(minutes=999), unit)
    )
    _record_nc(checks, results, "resample_future_timestamp", "resample_no_future_timestamp",
               resample_output_failures(future_rs, 15, source_max)["future_timestamp"])
    wrong_sb = production15.with_columns(
        _override_first("SourceBars", 99, production15.schema["SourceBars"])
    )
    _record_nc(checks, results, "resample_wrong_sourcebars", "resample_strict_sourcebars",
               resample_output_failures(wrong_sb, 15, source_max)["wrong_sourcebars"])
    dup_rs = production15.with_columns(_override_first("CloseTime", production15["CloseTime"][1], unit))
    _record_nc(checks, results, "resample_duplicate_close_time", "resample_close_time_unique",
               resample_output_failures(dup_rs, 15, source_max)["duplicate_close_time"])

    # Tolerant SourceBars-range detection (the parameterized check, both periods).
    # Exercises the lower boundary strict mode lacks, plus a must-not-overfire
    # assertion that a legitimate in-range partial is NOT flagged.
    for period in SOURCE_TIMEFRAMES:
        floor = tolerant_floor(period, MIN_COVERAGE_TOLERANT)
        prod_tol = aggregate_ohlc(src, period, min_coverage=MIN_COVERAGE_TOLERANT)
        sb_dtype = prod_tol.schema["SourceBars"]
        below = prod_tol.with_columns(_override_first("SourceBars", floor - 1, sb_dtype))
        _record_nc(
            checks, results, f"resample_tolerant_sourcebars_below_floor_{period}m",
            "resample_strict_sourcebars",
            resample_output_failures(below, period, source_max, MIN_COVERAGE_TOLERANT)[
                "wrong_sourcebars"
            ],
        )
        above = prod_tol.with_columns(_override_first("SourceBars", 99, sb_dtype))
        _record_nc(
            checks, results, f"resample_tolerant_sourcebars_above_period_{period}m",
            "resample_strict_sourcebars",
            resample_output_failures(above, period, source_max, MIN_COVERAGE_TOLERANT)[
                "wrong_sourcebars"
            ],
        )
        inrange = prod_tol.with_columns(_override_first("SourceBars", floor, sb_dtype))
        overfire = resample_output_failures(inrange, period, source_max, MIN_COVERAGE_TOLERANT)[
            "wrong_sourcebars"
        ]
        add_check(
            checks, instrument="SYNTHETIC", source_file="tolerant_range_assertion",
            source_timeframe=f"{period}m@0.90", view="timeframe",
            check="resample_tolerant_inrange_partial_not_flagged",
            failures=overfire, denominator=1,
            detail=f"in_range_partial_sourcebars={floor}; flagged={overfire}",
        )

    # Sparse-chart timestamp / source-count detection (use Renko output)
    renko = generate_renko(src, atr_period=RENKO_ATR_PERIOD)
    future = renko.with_columns(
        _override_first("SourceCloseTime", source_max + timedelta(minutes=9), unit)
    )
    _record_nc(checks, results, "chart_future_source_time", "chart_source_time_not_future",
               sparse_chart_failures(future, source_times, source_max)["future_source"])
    unmapped = renko.with_columns(
        _override_first("SourceCloseTime", source_max - timedelta(seconds=30), unit)
    )
    _record_nc(checks, results, "chart_unmapped_source_time", "chart_source_time_maps_to_source",
               sparse_chart_failures(unmapped, source_times, source_max)["missing_source"])
    null_src = renko.with_columns(_override_first("SourceCloseTime", None, unit))
    _record_nc(checks, results, "chart_null_source_time", "chart_source_time_not_null",
               sparse_chart_failures(null_src, source_times, source_max)["null_source"])
    shifted_close = renko.with_columns(
        _override_first("CloseTime", source_max - timedelta(minutes=1), unit)
    )
    _record_nc(checks, results, "chart_close_ne_source", "chart_close_time_equals_source_time",
               sparse_chart_failures(shifted_close, source_times, source_max)["close_ne_source"])
    neg_count = renko.with_columns(_override_first("SourceCount", -5, renko.schema["SourceCount"]))
    _record_nc(checks, results, "chart_source_count_negative", "chart_source_count_non_negative",
               sparse_chart_failures(neg_count, source_times, source_max)["source_count_negative"])
    zero_first = renko.with_columns(_override_first("SourceCount", 0, renko.schema["SourceCount"]))
    _record_nc(checks, results, "chart_first_event_source_count_zero",
               "chart_first_event_source_count_positive",
               sparse_chart_failures(zero_first, source_times, source_max)
               ["first_event_source_count_lt_one"])

    # Chart schema detection (via schema_failures)
    _record_nc(checks, results, "chart_schema_mismatch", "chart_schema_expected",
               schema_failures(renko.drop("BrickSize").columns, RENKO_COLUMNS))

    # Heiken Ashi real-price / alignment detection (via ha_failures)
    ha = generate_heiken_ashi(src)
    bad_real = ha.with_columns(_override_first("RealClose", -1.0))
    _record_nc(checks, results, "ha_real_price_corruption", "ha_real_prices_match_source",
               ha_failures(bad_real, src)["real_price_mismatch"])
    _record_nc(checks, results, "ha_dropped_row", "ha_row_count_matches_source",
               ha_failures(ha.slice(1), src)["row_count_mismatch"])
    ha_unmapped = ha.with_columns(
        _override_first("CloseTime", source_max + timedelta(minutes=999), unit)
    )
    _record_nc(checks, results, "ha_unmapped_close_time", "ha_close_time_maps_to_source",
               ha_failures(ha_unmapped, src)["missing_source"])
    ha_count = ha.with_columns(_override_first("SourceCount", 2, ha.schema["SourceCount"]))
    _record_nc(checks, results, "ha_source_count_ne_one", "ha_source_count_one",
               ha_failures(ha_count, src)["source_count_ne_one"])

    # Look-ahead generator caught by prefix stability (the headline control)
    _record_nc(checks, results, "lookahead_generator", "no_lookahead_prefix_stability",
               prefix_stability_failures(src, lookahead_demo_generator)["failures"])

    # Determinism: an ACTUALLY non-deterministic generator must be flagged.
    call_state = {"calls": 0}

    def nondeterministic_generator(frame: pl.DataFrame) -> pl.DataFrame:
        call_state["calls"] += 1
        return frame.with_columns(pl.lit(call_state["calls"]).cast(pl.Int64).alias("_call"))

    _record_nc(checks, results, "determinism_sensitivity", "deterministic_regeneration",
               determinism_failures(src, nondeterministic_generator))


def validate_resample_golden(checks: list[ValidationCheck], period_minutes: int) -> None:
    """Hand-anchored fixture: aggregate_ohlc's first window equals a plain-Python window.

    Parameterized over ``period_minutes`` so the 30m period gets its own anchor; for
    period 15 this reproduces the VAL-001 fixture exactly.
    """
    src = synthetic_source(2 * period_minutes)
    window = src.head(period_minutes)
    expected = {
        "Open": window["Open"][0],
        "High": max(window["High"].to_list()),
        "Low": min(window["Low"].to_list()),
        "Close": window["Close"][period_minutes - 1],
        "CloseTime": window["CloseTime"][period_minutes - 1],
        "SourceBars": period_minutes,
    }
    produced = aggregate_ohlc(src, period_minutes).row(0, named=True)
    mismatches = sum(1 for key, value in expected.items() if produced[key] != value)
    add_check(
        checks, instrument="SYNTHETIC", source_file="golden_fixture",
        source_timeframe=f"{period_minutes}m", view="timeframe", check="resample_golden_fixture",
        failures=mismatches, denominator=6, detail=f"expected_first_window={expected}",
    )


def validate_floor_guard(checks: list[ValidationCheck]) -> None:
    """Guard: the derived tolerant floors match the documented [14,15] / [27,30] ranges."""
    mismatches = 0
    detail_parts: list[str] = []
    for period, (expected_floor, expected_top) in EXPECTED_SOURCEBARS_RANGE.items():
        floor = tolerant_floor(period, MIN_COVERAGE_TOLERANT)
        ok = floor == expected_floor and period == expected_top
        mismatches += 0 if ok else 1
        detail_parts.append(f"{period}m=[{floor},{period}]")
    add_check(
        checks, instrument="SYNTHETIC", source_file="tolerant_range_guard", source_timeframe="-",
        view="timeframe", check="tolerant_sourcebars_range_guard", failures=mismatches,
        denominator=len(EXPECTED_SOURCEBARS_RANGE), detail="; ".join(detail_parts),
    )


# --------------------------------------------------------------------------- #
# Output and plots
# --------------------------------------------------------------------------- #
def checks_to_frame(checks: list[ValidationCheck]) -> pl.DataFrame:
    schema = {
        "instrument": pl.Utf8, "source_file": pl.Utf8, "source_timeframe": pl.Utf8,
        "view": pl.Utf8, "check": pl.Utf8, "status": pl.Utf8, "failures": pl.Int64,
        "denominator": pl.Int64, "detail": pl.Utf8,
    }
    if not checks:
        return pl.DataFrame(schema=schema)
    return pl.DataFrame([asdict(check) for check in checks])


def densities_to_frame(densities: list[EventDensity]) -> pl.DataFrame:
    schema = {
        "instrument": pl.Utf8, "source_file": pl.Utf8, "source_timeframe": pl.Utf8,
        "chart_type": pl.Utf8, "source_rows": pl.Int64, "event_rows": pl.Int64,
        "unique_source_times": pl.Int64, "duplicate_source_groups": pl.Int64,
        "duplicate_source_extra_rows": pl.Int64, "event_density": pl.Float64,
    }
    if not densities:
        return pl.DataFrame(schema=schema)
    return pl.DataFrame([asdict(density) for density in densities])


def negative_controls_to_frame(results: list[NegativeControl]) -> pl.DataFrame:
    schema = {
        "name": pl.Utf8, "target_check": pl.Utf8, "corrupted_failures": pl.Int64,
        "detected": pl.Boolean,
    }
    if not results:
        return pl.DataFrame(schema=schema)
    return pl.DataFrame([asdict(result) for result in results])


def coverage_to_frame(rows: list[CoverageRow]) -> pl.DataFrame:
    schema = {
        "instrument": pl.Utf8, "domain": pl.Utf8, "candidate_windows": pl.Int64,
        "retained_windows": pl.Int64, "dropped_windows": pl.Int64,
        "dropped_fraction_tolerant": pl.Float64, "dropped_fraction_strict": pl.Float64,
        "admission_status": pl.Utf8,
    }
    if not rows:
        return pl.DataFrame(schema=schema)
    return pl.DataFrame([asdict(row) for row in rows])


def anchor_to_frame(rows: list[AnchorRow]) -> pl.DataFrame:
    schema = {
        "instrument": pl.Utf8, "agg_rows_15m_strict": pl.Int64, "fingerprint": pl.Utf8,
        "determinism_status": pl.Utf8,
    }
    if not rows:
        return pl.DataFrame(schema=schema)
    return pl.DataFrame([asdict(row) for row in rows])


def summarize_status(checks_df: pl.DataFrame, group_cols: list[str]) -> pl.DataFrame:
    if checks_df.is_empty():
        return pl.DataFrame()
    return (
        checks_df.group_by(group_cols)
        .agg(
            pl.len().alias("checks"),
            (pl.col("status") == "PASS").sum().alias("passes"),
            (pl.col("status") == "FAIL").sum().alias("failures"),
            (pl.col("status") == "INCONCLUSIVE").sum().alias("inconclusive"),
        )
        .sort(group_cols)
    )


def write_outputs(
    checks_df: pl.DataFrame,
    densities_df: pl.DataFrame,
    negatives_df: pl.DataFrame,
    coverage_df: pl.DataFrame,
    anchor_df: pl.DataFrame,
    metadata: dict[str, Any],
) -> None:
    checks_df.write_csv(RESULTS_DIR / "validation_checks.csv")
    densities_df.write_csv(RESULTS_DIR / "chart_view_summary.csv")
    negatives_df.write_csv(RESULTS_DIR / "negative_controls.csv")
    coverage_df.write_csv(RESULTS_DIR / "coverage_map.csv")
    anchor_df.write_csv(RESULTS_DIR / "determinism_anchor.csv")
    summarize_status(checks_df, ["instrument"]).write_csv(RESULTS_DIR / "instrument_summary.csv")
    summarize_status(checks_df, ["instrument", "source_timeframe", "view"]).write_csv(
        RESULTS_DIR / "timeframe_summary.csv"
    )
    (RESULTS_DIR / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    plot_dropped_fraction_map(coverage_df, PLOTS_DIR / "dropped_fraction_map.png")
    plot_check_pass_heatmap(checks_df, PLOTS_DIR / "check_pass_heatmap.png")


def plot_dropped_fraction_map(coverage_df: pl.DataFrame, output_path: Path) -> None:
    """Per-cell tolerant dropped-window fraction by instrument x domain, with the gate."""
    rows = (
        coverage_df.sort(["instrument", "domain"]).to_dicts()
        if not coverage_df.is_empty()
        else []
    )
    fig_height = max(5, min(16, 0.32 * max(len(rows), 1)))
    fig, ax = plt.subplots(figsize=(10, fig_height))
    if rows:
        labels = [f"{r['instrument']} {r['domain']}" for r in rows]
        y = list(range(len(rows)))
        tol = [(r["dropped_fraction_tolerant"] if r["dropped_fraction_tolerant"] is not None else 0.0)
               for r in rows]
        strict = [(r["dropped_fraction_strict"] if r["dropped_fraction_strict"] is not None else 0.0)
                  for r in rows]
        colors = []
        for r in rows:
            status = r["admission_status"]
            colors.append(
                {"ADMITTED": "#3a7d44", "COVERAGE_EXCLUDED": "#b23a48",
                 "INCONCLUSIVE": "#c98c2b", "INTEGRITY_FAIL": "#6a1b9a"}.get(status, "#777777")
            )
        ax.barh(y, tol, color=colors, label="tolerant dropped fraction")
        ax.scatter(strict, y, color="#1f1f1f", marker="|", s=120, label="strict dropped fraction")
        ax.axvline(DROPPED_FRACTION_GATE, color="#b23a48", linestyle="--",
                   label=f"admission gate {DROPPED_FRACTION_GATE}")
        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=7)
        ax.invert_yaxis()
        ax.set_xlabel("Dropped windows / candidate windows")
        ax.set_title("VAL-004 Tolerant (0.90) Dropped-Window Fraction by Cell")
        ax.legend(loc="lower right", fontsize=8)
    else:
        ax.text(0.5, 0.5, "No coverage rows", ha="center", va="center")
        ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_check_pass_heatmap(checks_df: pl.DataFrame, output_path: Path) -> None:
    """Instrument x (source_timeframe|view) worst-status heatmap, incl. negative controls."""
    status_rank = {"PASS": 0, "INCONCLUSIVE": 1, "FAIL": 2}
    if checks_df.is_empty():
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "No validation checks", ha="center", va="center")
        ax.set_axis_off()
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return
    cell = (
        checks_df.with_columns(
            (pl.col("source_timeframe") + "|" + pl.col("view")).alias("col"),
            pl.col("status").replace_strict(status_rank, default=0).alias("rank"),
        )
        .group_by(["instrument", "col"])
        .agg(pl.col("rank").max().alias("rank"))
    )
    instruments = sorted(cell.select("instrument").unique().to_series().to_list())
    columns = sorted(cell.select("col").unique().to_series().to_list())
    rank_lookup = {(r["instrument"], r["col"]): r["rank"] for r in cell.to_dicts()}
    grid = [[rank_lookup.get((inst, col), -1) for col in columns] for inst in instruments]

    cmap = ListedColormap(["#dddddd", "#3a7d44", "#c98c2b", "#b23a48"])  # missing,pass,inc,fail
    fig_width = max(8, min(24, 0.55 * len(columns) + 4))
    fig_height = max(4, min(18, 0.42 * len(instruments) + 2))
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.imshow(grid, aspect="auto", cmap=cmap, vmin=-1, vmax=2)
    ax.set_xticks(range(len(columns)))
    ax.set_xticklabels(columns, rotation=90, fontsize=6)
    ax.set_yticks(range(len(instruments)))
    ax.set_yticklabels(instruments, fontsize=7)
    ax.set_title("VAL-004 Check Status (green=PASS, amber=INCONCLUSIVE, red=FAIL, grey=n/a)")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Universe & cross-run anchor reconciliation
# --------------------------------------------------------------------------- #
def reconcile_universe(
    files: list[Path], checks: list[ValidationCheck], metadata: dict[str, Any]
) -> list[Path]:
    """Enforce the scoped 17-instrument universe against the files present.

    Each expected instrument must map (by filename inference) to exactly one file;
    a missing or duplicated expected instrument is a FAIL. Files inferred outside
    the expected set are disclosed (non-failing) and not processed. Returns the
    deterministic list of files to validate.
    """
    by_inst: dict[str, list[Path]] = {}
    for path in files:
        by_inst.setdefault(infer_instrument(path), []).append(path)

    expected = set(EXPECTED_INSTRUMENTS)
    present = sorted(inst for inst in by_inst if inst in expected)
    missing = sorted(expected - set(by_inst))
    duplicates = sorted(inst for inst in present if len(by_inst[inst]) > 1)
    unexpected = sorted(inst for inst in by_inst if inst not in expected)

    for inst in sorted(expected):
        n_files = len(by_inst.get(inst, []))
        add_check(
            checks, instrument=inst, source_file="universe", source_timeframe="-",
            view="universe", check="universe_instrument_present_once",
            failures=0 if n_files == 1 else 1, denominator=1, detail=f"files={n_files}",
        )
    add_check(
        checks, instrument="ALL", source_file="universe", source_timeframe="-",
        view="universe", check="universe_reconciliation",
        failures=len(missing) + len(duplicates), denominator=len(expected),
        detail=f"present={len(present)}/{len(expected)}; missing={missing}; duplicates={duplicates}",
    )
    if unexpected:
        unexpected_files = [path.name for inst in unexpected for path in by_inst[inst]]
        add_check(
            checks, instrument="ALL", source_file="universe", source_timeframe="-",
            view="universe", check="universe_unexpected_files_disclosed",
            failures=0, denominator=1,
            detail=f"unexpected_inferred={unexpected}; files={unexpected_files}",
        )

    metadata["instrument_universe"] = {
        "expected": sorted(expected), "present": present, "missing": missing,
        "duplicates": duplicates, "unexpected_inferred": unexpected,
    }
    return [by_inst[inst][0] for inst in present if len(by_inst[inst]) == 1]


def load_prior_15m_status() -> dict[tuple[str, str, str], str]:
    """Load (instrument, view, check) -> status for 15m real-instrument rows from prior VALs."""
    prior: dict[tuple[str, str, str], str] = {}
    for rel in PRIOR_VAL_DIRS:
        path = PROJECT_ROOT / "python" / "experiments" / rel / "results" / "validation_checks.csv"
        if not path.exists():
            continue
        df = pl.read_csv(path).filter(
            (pl.col("source_timeframe") == "15m") & (pl.col("instrument") != "SYNTHETIC")
        )
        for row in df.select(["instrument", "view", "check", "status"]).to_dicts():
            prior[(row["instrument"], row["view"], row["check"])] = row["status"]
    return prior


def reconcile_15m_anchor(
    checks: list[ValidationCheck], anchor_rows: list[AnchorRow]
) -> dict[str, str]:
    """Cross-run reconcile VAL-004 15m strict rows against the pinned VAL-001/VAL-003 record.

    The 15m strict path must reproduce the historical record: every prior
    (instrument, view, check) key must be present and PASS in VAL-004, and every
    VAL-004 15m check must be PASS. A divergence emits a FAIL check (gating the run
    exit code). Instruments with no prior record reconcile as NO_PRIOR (INCONCLUSIVE).
    Returns {instrument: PASS|FAIL|NO_PRIOR} for the determinism-anchor table.
    """
    prior = load_prior_15m_status()
    current: dict[tuple[str, str, str], str] = {}
    for c in checks:
        if c.source_timeframe == "15m" and c.instrument != "SYNTHETIC" and c.view != "negative_control":
            current[(c.instrument, c.view, c.check)] = c.status

    result: dict[str, str] = {}
    for inst in sorted({a.instrument for a in anchor_rows}):
        prior_keys = {k: v for k, v in prior.items() if k[0] == inst}
        cur_keys = {k: v for k, v in current.items() if k[0] == inst}
        if not prior_keys:
            add_check(
                checks, instrument=inst, source_file="anchor_reconciliation",
                source_timeframe="15m", view="anchor", check="anchor_15m_reconciles_prior",
                failures=0, denominator=0, detail="no prior 15m record for instrument",
            )
            result[inst] = "NO_PRIOR"
            continue
        missing = [k for k in prior_keys if k not in cur_keys]
        mismatch = [k for k in prior_keys if k in cur_keys and cur_keys[k] != prior_keys[k]]
        not_pass = [k for k, v in cur_keys.items() if v != "PASS"]
        extra = [k for k in cur_keys if k not in prior_keys]
        failures = len(missing) + len(mismatch) + len(not_pass)
        add_check(
            checks, instrument=inst, source_file="anchor_reconciliation",
            source_timeframe="15m", view="anchor", check="anchor_15m_reconciles_prior",
            failures=failures, denominator=len(prior_keys),
            detail=(
                f"prior_keys={len(prior_keys)}, missing={len(missing)}, "
                f"mismatch={len(mismatch)}, not_pass={len(not_pass)}, extra_keys={len(extra)}"
            ),
        )
        result[inst] = "PASS" if failures == 0 else "FAIL"
    return result


# --------------------------------------------------------------------------- #
# Run
# --------------------------------------------------------------------------- #
def validate_instrument_cells(
    data: AnalysisData,
    checks: list[ValidationCheck],
    densities: list[EventDensity],
    coverage_rows: list[CoverageRow],
    anchor_rows: list[AnchorRow],
) -> None:
    """Run the four (period, mode) cells for one instrument, plus coverage + anchor."""
    validate_base_timebars(data, checks)

    agg_frames: dict[str, pl.DataFrame] = {}
    for period_minutes, min_coverage, label in MODE_MATRIX:
        timeframe = aggregate_timeframe(data.frame, period_minutes, min_coverage)
        agg_frames[label] = timeframe
        validate_timeframe(
            data, data.frame, timeframe, period_minutes, label, min_coverage, checks
        )

    with tqdm(
        total=len(MODE_MATRIX) * len(chart_specs()),
        desc=f"{data.instrument} chart views",
        unit="view",
        leave=False,
        dynamic_ncols=True,
    ) as chart_progress:
        for _period, _min_coverage, label in MODE_MATRIX:
            source = agg_frames[label]
            for chart in chart_specs():
                validate_chart_view(data, source, label, chart, checks, densities)
                chart_progress.update(1)

    # Per-domain tolerant coverage disclosure + admission.
    for period_minutes, domain_label in ((15, "15m"), (30, "30m")):
        tol_label = f"{period_minutes}m@0.90"
        coverage = dropped_window_fraction(data.frame, period_minutes, MIN_COVERAGE_TOLERANT)
        match = (
            0
            if coverage["candidate_windows"] == 0
            or coverage["retained_windows"] == agg_frames[tol_label].height
            else 1
        )
        add_check(
            checks, instrument=data.instrument, source_file=data.source_file,
            source_timeframe=tol_label, view="timeframe",
            check="dropped_fraction_retained_matches_agg", failures=match, denominator=1,
            detail=f"retained={coverage['retained_windows']}, agg_rows={agg_frames[tol_label].height}",
        )
        add_check(
            checks, instrument=data.instrument, source_file=data.source_file,
            source_timeframe=tol_label, view="timeframe", check="dropped_window_fraction_disclosed",
            failures=0, denominator=coverage["candidate_windows"],
            detail=(
                f"candidate={coverage['candidate_windows']}, "
                f"dropped_tolerant={coverage['dropped_windows']}, "
                f"frac_tolerant={coverage['dropped_fraction_tolerant']}, "
                f"frac_strict={coverage['dropped_fraction_strict']}"
            ),
        )
        admission = compute_admission(checks, data.instrument, tol_label, coverage)
        coverage_rows.append(
            CoverageRow(
                instrument=data.instrument, domain=domain_label,
                candidate_windows=coverage["candidate_windows"],
                retained_windows=coverage["retained_windows"],
                dropped_windows=coverage["dropped_windows"],
                dropped_fraction_tolerant=coverage["dropped_fraction_tolerant"],
                dropped_fraction_strict=coverage["dropped_fraction_strict"],
                admission_status=admission,
            )
        )

    # 15m strict determinism anchor: two regenerations byte-identical + fingerprint.
    agg15_strict = agg_frames["15m"]
    det_status = (
        "PASS" if aggregate_timeframe(data.frame, 15, None).equals(agg15_strict) else "FAIL"
    )
    anchor_rows.append(
        AnchorRow(
            instrument=data.instrument, agg_rows_15m_strict=agg15_strict.height,
            fingerprint=fingerprint_frame(agg15_strict), determinism_status=det_status,
        )
    )


def run_validation() -> tuple[
    pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame, dict[str, Any]
]:
    checks: list[ValidationCheck] = []
    densities: list[EventDensity] = []
    negatives: list[NegativeControl] = []
    coverage_rows: list[CoverageRow] = []
    anchor_rows: list[AnchorRow] = []
    metadata: dict[str, Any] = {
        "experiment_id": EXPERIMENT_ID,
        "data_dir": str(DATA_DIR),
        "source_timeframes": SOURCE_TIMEFRAMES,
        "min_coverage_modes": [None, MIN_COVERAGE_TOLERANT],
        "sourcebars_valid_range": {
            str(period): [tolerant_floor(period, MIN_COVERAGE_TOLERANT), period]
            for period in SOURCE_TIMEFRAMES
        },
        "dropped_fraction_gate": DROPPED_FRACTION_GATE,
        "linebreak_level": LINEBREAK_LEVEL,
        "renko_atr_period": RENKO_ATR_PERIOD,
        "prefix_window_rows": PREFIX_WINDOW_ROWS,
        "prefix_window_positions": list(PREFIX_WINDOW_POSITIONS),
        "prefix_fractions": list(PREFIX_FRACTIONS),
        "determinism_rows": DETERMINISM_ROWS,
        "holdout_rule": "first 70 percent analysis slice only",
    }

    # Detection-power evidence runs first so it is present even on an empty data dir.
    log_subsection("Detection-power controls")
    validate_floor_guard(checks)
    for period in SOURCE_TIMEFRAMES:
        validate_resample_golden(checks, period)
    run_negative_controls(checks, negatives)

    files = list_timebar_files()
    metadata["source_files"] = [path.name for path in files]
    log_subsection("Holdout-safe instrument validation")
    log_kv("Source files", len(files))
    if not files:
        add_check(
            checks, instrument="ALL", source_file="data/timebars", source_timeframe="1m",
            view="timebar", check="timebar_files_available", failures=1, denominator=1,
            detail="No files matched data/timebars/timebars_*.parquet",
        )
        return (
            checks_to_frame(checks), densities_to_frame(densities),
            negative_controls_to_frame(negatives), coverage_to_frame(coverage_rows),
            anchor_to_frame(anchor_rows), metadata,
        )

    # F01: enforce the scoped 17-instrument universe before validating anything.
    processable = reconcile_universe(files, checks, metadata)
    metadata["processed_files"] = [path.name for path in processable]
    log_kv("Universe present", f"{len(processable)}/{len(EXPECTED_INSTRUMENTS)} expected")

    seen_symbols: set[str] = set()
    for path in tqdm(processable, desc="Instruments", unit="file", dynamic_ncols=True):
        filename_instrument = infer_instrument(path)
        data = load_analysis_data(path, checks)
        if data is None:
            continue
        # Guard: loaded Symbol must match the filename-inferred instrument, and no
        # two processed files may carry the same Symbol (content-level duplicate).
        add_check(
            checks, instrument=data.instrument, source_file=data.source_file,
            source_timeframe="-", view="universe", check="loaded_symbol_matches_filename",
            failures=0 if data.instrument == filename_instrument else 1, denominator=1,
            detail=f"filename={filename_instrument}, symbol={data.instrument}",
        )
        add_check(
            checks, instrument=data.instrument, source_file=data.source_file,
            source_timeframe="-", view="universe", check="instrument_not_duplicated",
            failures=1 if data.instrument in seen_symbols else 0, denominator=1,
            detail=f"already_seen={data.instrument in seen_symbols}",
        )
        seen_symbols.add(data.instrument)
        tqdm.write(
            f"{data.instrument}: {data.analysis_rows:,} analysis rows "
            f"({data.analysis_start} -> {data.analysis_end})"
        )
        validate_instrument_cells(data, checks, densities, coverage_rows, anchor_rows)

    # F02: cross-run reconcile the 15m strict anchor against the pinned prior record.
    prior_map = reconcile_15m_anchor(checks, anchor_rows)
    anchor_df = anchor_to_frame(anchor_rows)
    if anchor_df.height:
        anchor_df = anchor_df.with_columns(
            pl.col("instrument").replace_strict(prior_map, default="NO_PRIOR").alias(
                "prior_reconciled"
            )
        )
    else:
        anchor_df = anchor_df.with_columns(pl.lit(None, dtype=pl.Utf8).alias("prior_reconciled"))

    return (
        checks_to_frame(checks), densities_to_frame(densities),
        negative_controls_to_frame(negatives), coverage_to_frame(coverage_rows),
        anchor_df, metadata,
    )


def main() -> None:
    configure_logging()
    ensure_output_dirs()
    log_section("VAL-004 15m/30m Domain Temporal-Integrity Validation")
    log_kv("Data directory", DATA_DIR)
    log_kv("Results", RESULTS_DIR)
    log_kv("Plots", PLOTS_DIR)
    log_kv("Source timeframes", SOURCE_TIMEFRAMES)
    log_kv("Coverage modes", ["strict", f"tolerant({MIN_COVERAGE_TOLERANT})"])
    log_kv("Holdout rule", "first 70 percent analysis slice only")

    checks_df, densities_df, negatives_df, coverage_df, anchor_df, metadata = run_validation()

    log_subsection("Writing artifacts")
    write_outputs(checks_df, densities_df, negatives_df, coverage_df, anchor_df, metadata)

    failures = checks_df.filter(pl.col("status") == "FAIL").height
    inconclusive = checks_df.filter(pl.col("status") == "INCONCLUSIVE").height
    missed_controls = negatives_df.filter(~pl.col("detected")).height if negatives_df.height else 0
    def _count(status: str) -> int:
        return (
            coverage_df.filter(pl.col("admission_status") == status).height
            if coverage_df.height
            else 0
        )

    admitted, coverage_excluded = _count("ADMITTED"), _count("COVERAGE_EXCLUDED")
    cells_inconclusive = _count("INCONCLUSIVE")

    log_subsection("Run summary")
    log_kv("Output directory", RESULTS_DIR)
    log_kv("Validation checks", checks_df.height)
    log_kv("Failures", failures)
    log_kv("Inconclusive checks", inconclusive)
    log_kv("Negative controls", negatives_df.height)
    log_kv("Missed controls", missed_controls)
    log_kv("Admitted cells", admitted)
    log_kv("Coverage-excluded cells", coverage_excluded)
    log_kv("Inconclusive cells", cells_inconclusive)

    # F03 — exit-code contract (one contract across scope/plan/code):
    #   FAIL (1): any integrity FAIL or missed control -> suite did not clear.
    #   INCONCLUSIVE (2): no FAIL but >=1 INCONCLUSIVE check -> PASS-with-deferrals;
    #     the deferred cell is NOT admitted, but ADMITTED cells remain individually
    #     valid for EXP-048.
    #   PASS (0): no FAIL and no INCONCLUSIVE -> full Suite PASS. A COVERAGE_EXCLUDED
    #     cell is a recorded exclusion (not a check FAIL), so it does not block exit 0.
    if failures:
        log_kv("Exit status", "FAIL")
        raise SystemExit(1)
    if inconclusive:
        log_kv("Exit status", "INCONCLUSIVE")
        raise SystemExit(2)
    log_kv("Exit status", "PASS")


if __name__ == "__main__":
    main()
