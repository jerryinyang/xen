"""
Experiment VAL-001: Data Architecture Temporal Integrity Validation.

Implements the validation plan from ``analysis-plan.md``. The script checks
timestamp alignment, resampling correctness against an independent oracle, and
row-level no-look-ahead via prefix stability over the analysis slice only. It
does not compute returns, signals, P&L, or strategy metrics.

Every positive check is paired with negative controls: deliberately corrupted
inputs that the same check functions must flag. A negative control that is *not*
detected is itself a FAIL, so a clean run demonstrates the checks have real
detection power rather than passing by construction.
"""
from __future__ import annotations

import json
import logging
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

import matplotlib.pyplot as plt
import polars as pl
from tqdm.auto import tqdm

from xen.bar_aggregator import aggregate_ohlc
from xen.heiken_ashi_generator import HA_COLUMNS, generate_heiken_ashi
from xen.linebreak_generator import LINEBREAK_COLUMNS, generate_linebreak
from xen.renko_generator import RENKO_COLUMNS, generate_renko


LOGGER = logging.getLogger(__name__)

EXPERIMENT_ID = "VAL-001"
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
SOURCE_TIMEFRAMES = [1, 15, 60]
LINEBREAK_LEVEL = 3
RENKO_ATR_PERIOD = 14

# Engineering bounds for the look-ahead / determinism probes. No-look-ahead and
# determinism are *structural* properties of a sequential generator, so bounded
# windows are representative and keep cost finite on multi-million-row inputs.
# rev. 3 places probe windows at several positions across the slice (not only the
# head) and uses more cut points. These are harness bounds, not data-derived
# thresholds.
PREFIX_WINDOW_ROWS = 150_000
PREFIX_WINDOW_POSITIONS = ("head", "middle", "tail")
PREFIX_FRACTIONS = (0.34, 0.67, 0.95)
DETERMINISM_ROWS = 50_000

# Chart generators build output from Python ``datetime`` objects, so their
# timestamp columns are microsecond-precision, while Parquet time bars load as
# nanosecond-precision. Joins/filters across mismatched time units raise in
# Polars, so every frame that participates in a cross-frame timestamp comparison
# is normalised to one canonical unit. Minute bars are exact in microseconds, so
# this conversion is lossless for this data.
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


def independent_resample_oracle(source: pl.DataFrame, period_minutes: int) -> pl.DataFrame:
    """Resample 1-minute bars to N-minute bars using pandas.

    This is an *independent* implementation (pandas right-closed/right-labelled
    resampling) used as ground truth for ``xen.aggregate_ohlc``. Clock-aligned
    windows that do not contain exactly ``period_minutes`` source bars are
    dropped, matching the production strict mode. OHLC values are direct source
    selections (first/max/min/last), so equality is exact, not approximate.
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
    aggregated = aggregated[aggregated["SourceBars"] == period_minutes].reset_index()
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
    timeframe: pl.DataFrame, period_minutes: int, source_max: Any
) -> dict[str, int]:
    """Output-side resample integrity: no future close, strict source-bar count, unique close."""
    duplicate = timeframe.height - int(timeframe.select(pl.col("CloseTime").n_unique()).item())
    return {
        "future_timestamp": timeframe.filter(pl.col("CloseTime") > source_max).height,
        "wrong_sourcebars": timeframe.filter(pl.col("SourceBars") != period_minutes).height,
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

    When the slice fits within ``window_rows`` the whole slice is a single
    ``full`` window (positions would be identical, so they are not duplicated).
    Otherwise one window per requested position gives coverage across the slice
    (head/middle/tail) rather than only its leading rows.
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

    For a generator that uses only past/current bars, ``generate(source[:k])``
    must be an *exact prefix* of ``generate(source)``. If a generator consults
    future rows, the rows it emits near the cut differ between the prefix run and
    the full run. Returns the number of prefix cuts that diverged.
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


def aggregate_timeframe(source: pl.DataFrame, period_minutes: int) -> pl.DataFrame:
    if period_minutes == 1:
        return source
    return aggregate_ohlc(source, period_minutes=period_minutes)


def validate_timeframe(
    data: AnalysisData,
    source_1m: pl.DataFrame,
    timeframe: pl.DataFrame,
    period_minutes: int,
    checks: list[ValidationCheck],
) -> None:
    label = f"{period_minutes}m"
    if period_minutes == 1:
        add_check(
            checks, instrument=data.instrument, source_file=data.source_file,
            source_timeframe=label, view="timeframe", check="timeframe_source_is_base",
            failures=0, denominator=source_1m.height,
            detail="1m timeframe uses base analysis rows directly",
        )
        return

    oracle = independent_resample_oracle(source_1m, period_minutes)
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
    out = resample_output_failures(timeframe, period_minutes, source_max)
    add_check(
        checks, instrument=data.instrument, source_file=data.source_file, source_timeframe=label,
        view="timeframe", check="resample_no_future_timestamp",
        failures=out["future_timestamp"],
        denominator=timeframe.height, detail="rows_after_source_analysis_max",
    )
    add_check(
        checks, instrument=data.instrument, source_file=data.source_file, source_timeframe=label,
        view="timeframe", check="resample_strict_sourcebars",
        failures=out["wrong_sourcebars"],
        denominator=timeframe.height, detail=f"rows_with_sourcebars_not_{period_minutes}",
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

    Used only as a negative control to confirm prefix stability detects
    look-ahead. The last-row fill makes the prefix run diverge from the full run
    exactly at the cut, which is the signature of look-ahead.
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
    """Inject a fault for every data-integrity / alignment check (see analysis plan Step 6).

    Each control corrupts a deterministic synthetic input and routes it through the
    same check function used on real data, requiring that function to report a
    failure. A control whose fault is not detected is a FAIL. Pure availability/IO
    defensive checks (Parquet readability, file presence, non-empty slice) are
    exercised by their own construction and are not assigned controls.
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

    # Resample oracle detection
    production15 = aggregate_ohlc(src, 15)
    oracle15 = independent_resample_oracle(src, 15)
    bad_value = production15.with_columns(_override_first("High", 1.0e9))
    fails = resample_failures(bad_value, oracle15)
    _record_nc(checks, results, "resample_value_corruption", "resample_matches_independent_oracle",
               fails["ohlc_mismatch"])
    fails = resample_failures(production15.slice(1), oracle15)
    _record_nc(checks, results, "resample_dropped_row", "resample_matches_independent_oracle",
               fails["rows_only_in_oracle"])

    # Resample output-side detection (via resample_output_failures)
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

    # Determinism: an ACTUALLY non-deterministic generator must be flagged. A
    # mutable call counter guarantees the two regenerations differ, so this tests
    # determinism_failures itself, not the `equals` primitive.
    call_state = {"calls": 0}

    def nondeterministic_generator(frame: pl.DataFrame) -> pl.DataFrame:
        call_state["calls"] += 1
        return frame.with_columns(pl.lit(call_state["calls"]).cast(pl.Int64).alias("_call"))

    _record_nc(checks, results, "determinism_sensitivity", "deterministic_regeneration",
               determinism_failures(src, nondeterministic_generator))


def validate_resample_golden(checks: list[ValidationCheck]) -> None:
    """Hand-anchored fixture: aggregate_ohlc's first window must equal a plain-Python window."""
    src = synthetic_source(30)
    window = src.head(15)
    expected = {
        "Open": window["Open"][0],
        "High": max(window["High"].to_list()),
        "Low": min(window["Low"].to_list()),
        "Close": window["Close"][14],
        "CloseTime": window["CloseTime"][14],
        "SourceBars": 15,
    }
    produced = aggregate_ohlc(src, 15).row(0, named=True)
    mismatches = sum(1 for key, value in expected.items() if produced[key] != value)
    add_check(
        checks, instrument="SYNTHETIC", source_file="golden_fixture", source_timeframe="15m",
        view="timeframe", check="resample_golden_fixture", failures=mismatches, denominator=6,
        detail=f"expected_first_window={expected}",
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
    metadata: dict[str, Any],
) -> None:
    checks_df.write_csv(RESULTS_DIR / "validation_checks.csv")
    densities_df.write_csv(RESULTS_DIR / "chart_view_summary.csv")
    negatives_df.write_csv(RESULTS_DIR / "negative_controls.csv")
    summarize_status(checks_df, ["instrument"]).write_csv(RESULTS_DIR / "instrument_summary.csv")
    summarize_status(checks_df, ["instrument", "source_timeframe", "view"]).write_csv(
        RESULTS_DIR / "timeframe_summary.csv"
    )
    (RESULTS_DIR / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    plot_validation_status(checks_df, PLOTS_DIR / "validation_status_by_view.png")
    plot_event_density(densities_df, PLOTS_DIR / "chart_event_density.png")


def status_color(status: str) -> str:
    return {"PASS": "#3a7d44", "FAIL": "#b23a48", "INCONCLUSIVE": "#c98c2b"}.get(status, "#777777")


def plot_validation_status(checks_df: pl.DataFrame, output_path: Path) -> None:
    status_order = {"PASS": 0, "FAIL": 1, "INCONCLUSIVE": 2}
    rows = (
        checks_df.group_by(["view", "status"]).agg(pl.len().alias("count")).to_dicts()
        if not checks_df.is_empty()
        else []
    )
    rows = sorted(rows, key=lambda row: (row["view"], status_order.get(row["status"], 99)))
    fig, ax = plt.subplots(figsize=(11, 5))
    if rows:
        ax.bar(
            [f"{row['view']}\n{row['status']}" for row in rows],
            [row["count"] for row in rows],
            color=[status_color(row["status"]) for row in rows],
        )
        ax.set_ylabel("Validation checks")
        ax.set_title("VAL-001 Validation Status by View (incl. negative controls)")
        ax.tick_params(axis="x", labelrotation=45)
    else:
        ax.text(0.5, 0.5, "No validation checks", ha="center", va="center")
        ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_event_density(densities_df: pl.DataFrame, output_path: Path) -> None:
    rows = densities_df.sort(["instrument", "source_timeframe", "chart_type"]).to_dicts()
    fig_height = max(5, min(14, 0.32 * max(len(rows), 1)))
    fig, ax = plt.subplots(figsize=(10, fig_height))
    if rows:
        ax.barh(
            [f"{r['instrument']} {r['source_timeframe']} {r['chart_type']}" for r in rows],
            [r["event_density"] or 0.0 for r in rows],
            color="#4c78a8",
        )
        ax.set_xlabel("Event rows / source rows")
        ax.set_title("VAL-001 Chart Event Density")
        ax.invert_yaxis()
    else:
        ax.text(0.5, 0.5, "No chart event records", ha="center", va="center")
        ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Run
# --------------------------------------------------------------------------- #
def run_validation() -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    checks: list[ValidationCheck] = []
    densities: list[EventDensity] = []
    negatives: list[NegativeControl] = []
    metadata: dict[str, Any] = {
        "experiment_id": EXPERIMENT_ID,
        "data_dir": str(DATA_DIR),
        "source_timeframes": SOURCE_TIMEFRAMES,
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
    validate_resample_golden(checks)
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
            negative_controls_to_frame(negatives), metadata,
        )

    for path in tqdm(files, desc="Instruments", unit="file", dynamic_ncols=True):
        data = load_analysis_data(path, checks)
        if data is None:
            continue
        tqdm.write(
            f"{data.instrument}: {data.analysis_rows:,} analysis rows "
            f"({data.analysis_start} -> {data.analysis_end})"
        )
        validate_base_timebars(data, checks)

        timeframe_frames: dict[int, pl.DataFrame] = {}
        for period_minutes in tqdm(
            SOURCE_TIMEFRAMES,
            desc=f"{data.instrument} timeframes",
            unit="tf",
            leave=False,
            dynamic_ncols=True,
        ):
            timeframe = aggregate_timeframe(data.frame, period_minutes)
            timeframe_frames[period_minutes] = timeframe
            validate_timeframe(data, data.frame, timeframe, period_minutes, checks)

        with tqdm(
            total=len(timeframe_frames) * len(chart_specs()),
            desc=f"{data.instrument} chart views",
            unit="view",
            leave=False,
            dynamic_ncols=True,
        ) as chart_progress:
            for period_minutes, source in timeframe_frames.items():
                for chart in chart_specs():
                    validate_chart_view(data, source, f"{period_minutes}m", chart, checks, densities)
                    chart_progress.update(1)

    return (
        checks_to_frame(checks), densities_to_frame(densities),
        negative_controls_to_frame(negatives), metadata,
    )


def main() -> None:
    configure_logging()
    ensure_output_dirs()
    log_section("VAL-001 Data Architecture Validation")
    log_kv("Data directory", DATA_DIR)
    log_kv("Results", RESULTS_DIR)
    log_kv("Plots", PLOTS_DIR)
    log_kv("Holdout rule", "first 70 percent analysis slice only")

    checks_df, densities_df, negatives_df, metadata = run_validation()

    log_subsection("Writing artifacts")
    write_outputs(checks_df, densities_df, negatives_df, metadata)

    failures = checks_df.filter(pl.col("status") == "FAIL").height
    inconclusive = checks_df.filter(pl.col("status") == "INCONCLUSIVE").height
    missed_controls = negatives_df.filter(~pl.col("detected")).height if negatives_df.height else 0

    log_subsection("Run summary")
    log_kv("Output directory", RESULTS_DIR)
    log_kv("Validation checks", checks_df.height)
    log_kv("Failures", failures)
    log_kv("Inconclusive", inconclusive)
    log_kv("Negative controls", negatives_df.height)
    log_kv("Missed controls", missed_controls)

    if failures:
        log_kv("Exit status", "FAIL")
        raise SystemExit(1)
    if inconclusive:
        log_kv("Exit status", "INCONCLUSIVE")
        raise SystemExit(2)
    log_kv("Exit status", "PASS")


if __name__ == "__main__":
    main()
