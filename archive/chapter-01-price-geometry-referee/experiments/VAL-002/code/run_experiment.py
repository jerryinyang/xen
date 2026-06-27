"""
Validation VAL-002: INFR-001 C# StrategyHost parity and suite reproduction.

Runs the C# StrategyHost parity exporter on fixed first-70% time-bar slices,
compares each C# port to the Python oracle, then routes C# MA(20/50) positions
through the unchanged frozen referee helpers. No AVWAP code or referee code is
modified here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
from tqdm.auto import tqdm

from xen.bar_aggregator import aggregate_ohlc
from xen.heiken_ashi_generator import generate_heiken_ashi
from xen.indicators.market_bias import compute_market_bias, convergence_warmup
from xen.linebreak_generator import generate_linebreak
from xen.referee_calibration import (
    ALPHA_GRID,
    build_domain_frames,
    domain_split_index,
    evaluate_referees,
    list_timebar_files,
    load_analysis_data,
    next_log_returns_from_bars,
    seed_for,
    write_json,
)
from xen.renko_generator import generate_renko


LOGGER = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
VALIDATION_ID = "VAL-002"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = PROJECT_ROOT / "data"
VALIDATION_DIR = PROJECT_ROOT / "python" / "experiments" / VALIDATION_ID
RESULTS_DIR = VALIDATION_DIR / "results"
CSHARP_EXPORT_DIR = RESULTS_DIR / "csharp_exports"
CSHARP_DETERMINISM_DIR = RESULTS_DIR / "csharp_exports_determinism"
CSHARP_TOOL = PROJECT_ROOT / "tools" / "StrategyHostParity" / "StrategyHostParity.csproj"
EXP003_MDE = PROJECT_ROOT / "python" / "experiments" / "EXP-003" / "results" / "mde_summary.csv"

MA_FAST = 20
MA_SLOW = 50
ALPHA0 = 0.05
BOOTSTRAP_RESAMPLES = 1000
NUMERIC_TOLERANCE = 1e-8


@dataclass(frozen=True)
class DomainConfig:
    label: str
    period_minutes: int
    min_coverage: float | None


DOMAINS: tuple[DomainConfig, ...] = (
    DomainConfig("5m", 5, None),
    DomainConfig("1h", 60, 0.90),
    DomainConfig("4h", 240, 0.90),
)


@dataclass(frozen=True)
class CheckResult:
    instrument: str
    module: str
    domain: str
    status: str
    expected_rows: int
    observed_rows: int
    max_abs_error: float | None
    detail: str


# --------------------------------------------------------------------------- #
# Output and command helpers
# --------------------------------------------------------------------------- #
def configure_logging() -> None:
    """Configure concise INFO-level logging for manual validation runs."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def ensure_output_dirs() -> None:
    """Create the VAL-002 results directory."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    CSHARP_EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def parse_args() -> argparse.Namespace:
    """Parse manual-run options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reuse-csharp-output",
        action="store_true",
        help="Use existing CSV exports instead of running the console exporter.",
    )
    parser.add_argument(
        "--csharp-export-root",
        type=Path,
        default=CSHARP_EXPORT_DIR,
        help=(
            "Root containing C# parity exports. With --reuse-csharp-output this may be "
            "results/csharp_exports or the cTrader Strategy Output Directory."
        ),
    )
    parser.add_argument(
        "--skip-suite",
        action="store_true",
        help="Run parity checks only; skip frozen-suite reproduction.",
    )
    parser.add_argument(
        "--determinism-rerun",
        action="store_true",
        help="Rerun the C# exporter and compare CSV hashes for determinism.",
    )
    parser.add_argument(
        "--keep-csharp-output",
        action="store_true",
        help="Retain console-generated intermediate C# CSV exports under results/.",
    )
    return parser.parse_args()


def run_csharp_export(source_path: Path, output_dir: Path, analysis_end_utc: str) -> None:
    """Run the C# parity exporter for one source file."""
    if not CSHARP_TOOL.exists():
        raise FileNotFoundError(f"C# parity tool not found: {CSHARP_TOOL}")
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        "dotnet",
        "run",
        "--configuration",
        "Release",
        "--project",
        str(CSHARP_TOOL),
        "--",
        "--input",
        str(source_path),
        "--output",
        str(output_dir),
        "--analysis-end",
        analysis_end_utc,
    ]
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def find_existing_export_dir(root: Path, source_path: Path, instrument: str) -> Path:
    """Find a C# parity export directory for ``source_path`` and ``instrument``."""
    direct = root / instrument.lower()
    if (direct / "export_metadata.json").exists():
        return direct

    candidates: list[tuple[str, Path]] = []
    for metadata_path in root.rglob("export_metadata.json"):
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        symbol = str(metadata.get("symbol") or "").upper()
        input_file = str(metadata.get("input_file") or Path(str(metadata.get("input_path", ""))).name)
        if symbol == instrument.upper() or input_file == source_path.name:
            generated = str(metadata.get("generated_utc") or "")
            candidates.append((generated, metadata_path.parent))

    if not candidates:
        raise FileNotFoundError(
            f"No C# parity export found for {instrument}/{source_path.name} under {root}"
        )
    return sorted(candidates, key=lambda item: item[0])[-1][1]


def csv_hashes(directory: Path) -> dict[str, str]:
    """Return SHA-256 hashes for deterministic CSV outputs in ``directory``."""
    hashes: dict[str, str] = {}
    for path in sorted(directory.glob("*.csv")):
        digest = hashlib.sha256()
        digest.update(path.read_bytes())
        hashes[path.name] = digest.hexdigest()
    return hashes


def analysis_end_after_slice(frame: pl.DataFrame) -> datetime:
    """Return a fence cutoff one microsecond after the last analysis bar."""
    close_time = frame.select(pl.max("CloseTime")).item()
    if not isinstance(close_time, datetime):
        raise TypeError(f"Unexpected CloseTime value: {close_time!r}")
    return close_time + timedelta(microseconds=1)


def iso_utc(value: datetime) -> str:
    """Serialize a naive UTC datetime for C# DateTime parsing."""
    return value.replace(tzinfo=None).isoformat(timespec="microseconds") + "Z"


# --------------------------------------------------------------------------- #
# Frame comparison helpers
# --------------------------------------------------------------------------- #
def read_csv(path: Path) -> pl.DataFrame:
    """Read a C# exporter CSV with stable null/date handling."""
    if not path.exists():
        raise FileNotFoundError(path)
    return pl.read_csv(path, try_parse_dates=True, null_values=[""])


def normalize_frame(
    frame: pl.DataFrame,
    *,
    columns: list[str],
    time_columns: set[str],
    int_columns: set[str],
    bool_columns: set[str],
    string_columns: set[str],
) -> pl.DataFrame:
    """Select and cast comparison columns into stable dtypes."""
    casts: list[pl.Expr] = []
    for column in columns:
        if column in time_columns:
            if frame.schema[column] == pl.String:
                casts.append(
                    pl.col(column)
                    .str.strptime(pl.Datetime("us", "UTC"), strict=False)
                    .dt.replace_time_zone(None)
                    .alias(column)
                )
            else:
                casts.append(pl.col(column).cast(pl.Datetime("us")).alias(column))
        elif column in int_columns:
            casts.append(pl.col(column).cast(pl.Int64).alias(column))
        elif column in bool_columns:
            casts.append(pl.col(column).cast(pl.Boolean).alias(column))
        elif column in string_columns:
            casts.append(pl.col(column).cast(pl.String).alias(column))
        else:
            casts.append(pl.col(column).cast(pl.Float64).alias(column))
    return frame.select(casts)


def compare_frames(
    *,
    instrument: str,
    module: str,
    domain: str,
    expected: pl.DataFrame,
    observed: pl.DataFrame,
    columns: list[str],
    exact_columns: set[str],
    numeric_columns: set[str],
    time_columns: set[str],
    int_columns: set[str] | None = None,
    bool_columns: set[str] | None = None,
    string_columns: set[str] | None = None,
    tolerance: float = NUMERIC_TOLERANCE,
) -> CheckResult:
    """Compare one C# output table against the Python oracle."""
    int_columns = int_columns or set()
    bool_columns = bool_columns or set()
    string_columns = string_columns or set()
    missing = sorted(set(columns).difference(observed.columns))
    if missing:
        return CheckResult(instrument, module, domain, "FAIL", expected.height, 0, None, f"missing columns {missing}")

    expected_norm = normalize_frame(
        expected,
        columns=columns,
        time_columns=time_columns,
        int_columns=int_columns,
        bool_columns=bool_columns,
        string_columns=string_columns,
    )
    observed_norm = normalize_frame(
        observed,
        columns=columns,
        time_columns=time_columns,
        int_columns=int_columns,
        bool_columns=bool_columns,
        string_columns=string_columns,
    )

    if expected_norm.height != observed_norm.height:
        return CheckResult(
            instrument,
            module,
            domain,
            "FAIL",
            expected_norm.height,
            observed_norm.height,
            None,
            "row count mismatch",
        )

    for column in sorted(exact_columns):
        if column in time_columns:
            expected_values = expected_norm.select(pl.col(column).dt.epoch("us")).to_series().to_list()
            observed_values = observed_norm.select(pl.col(column).dt.epoch("us")).to_series().to_list()
        else:
            expected_values = expected_norm[column].to_list()
            observed_values = observed_norm[column].to_list()
        if expected_values != observed_values:
            return CheckResult(
                instrument,
                module,
                domain,
                "FAIL",
                expected_norm.height,
                observed_norm.height,
                None,
                f"exact mismatch in {column}",
            )

    max_abs_error = 0.0
    for column in sorted(numeric_columns):
        expected_values = expected_norm[column].to_numpy()
        observed_values = observed_norm[column].to_numpy()
        both_nan = np.isnan(expected_values) & np.isnan(observed_values)
        diff = np.abs(expected_values - observed_values)
        diff[both_nan] = 0.0
        finite_or_nan_match = both_nan | (np.isfinite(expected_values) == np.isfinite(observed_values))
        if not bool(np.all(finite_or_nan_match)):
            return CheckResult(
                instrument,
                module,
                domain,
                "FAIL",
                expected_norm.height,
                observed_norm.height,
                None,
                f"finite/NaN mismatch in {column}",
            )
        column_max = float(np.nanmax(diff)) if diff.size else 0.0
        max_abs_error = max(max_abs_error, column_max)
        if np.any(diff > tolerance):
            return CheckResult(
                instrument,
                module,
                domain,
                "FAIL",
                expected_norm.height,
                observed_norm.height,
                column_max,
                f"numeric mismatch in {column} above tolerance {tolerance:g}",
            )

    return CheckResult(
        instrument,
        module,
        domain,
        "PASS",
        expected_norm.height,
        observed_norm.height,
        max_abs_error,
        "matched Python oracle",
    )


def check_before_cutoff(
    *,
    instrument: str,
    module: str,
    domain: str,
    frame: pl.DataFrame,
    time_column: str,
    analysis_end_utc: datetime,
) -> CheckResult:
    """Check that an observed C# table is strictly before ``AnalysisEndUtc``."""
    if frame.is_empty():
        return CheckResult(instrument, f"{module}_holdout", domain, "PASS", 0, 0, None, "empty table")
    normalized = normalize_frame(
        frame,
        columns=[time_column],
        time_columns={time_column},
        int_columns=set(),
        bool_columns=set(),
        string_columns=set(),
    )
    max_time = normalized.select(pl.max(time_column)).item()
    status = "PASS" if max_time < analysis_end_utc else "FAIL"
    detail = "max timestamp before AnalysisEndUtc" if status == "PASS" else "timestamp at or after AnalysisEndUtc"
    return CheckResult(instrument, f"{module}_holdout", domain, status, frame.height, frame.height, None, detail)


# --------------------------------------------------------------------------- #
# Oracle construction and validation
# --------------------------------------------------------------------------- #
def validate_export(
    *,
    analysis_frame: pl.DataFrame,
    export_dir: Path,
    analysis_end_utc: datetime,
) -> tuple[list[CheckResult], dict[str, pl.DataFrame]]:
    """Validate one C# export directory and return domain position tables."""
    instrument = str(analysis_frame.select(pl.first("Symbol")).item()).upper()
    checks: list[CheckResult] = []
    csharp_positions: dict[str, pl.DataFrame] = {}

    linebreak_columns = [
        "OpenTime",
        "CloseTime",
        "Open",
        "High",
        "Low",
        "Close",
        "Direction",
        "Level",
        "SourceCount",
        "SourceCloseTime",
    ]
    linebreak = read_csv(export_dir / "linebreak.csv")
    checks.append(
        compare_frames(
            instrument=instrument,
            module="linebreak",
            domain="1m",
            expected=generate_linebreak(analysis_frame, level=3),
            observed=linebreak,
            columns=linebreak_columns,
            exact_columns={"OpenTime", "CloseTime", "Direction", "Level", "SourceCount", "SourceCloseTime"},
            numeric_columns={"Open", "High", "Low", "Close"},
            time_columns={"OpenTime", "CloseTime", "SourceCloseTime"},
            int_columns={"Direction", "Level", "SourceCount"},
        )
    )
    checks.append(
        check_before_cutoff(
            instrument=instrument,
            module="linebreak",
            domain="1m",
            frame=linebreak,
            time_column="SourceCloseTime",
            analysis_end_utc=analysis_end_utc,
        )
    )

    renko_columns = [
        "OpenTime",
        "CloseTime",
        "Open",
        "High",
        "Low",
        "Close",
        "Direction",
        "BrickSize",
        "ATRPeriod",
        "SourceCount",
        "SourceCloseTime",
    ]
    renko = read_csv(export_dir / "renko.csv")
    checks.append(
        compare_frames(
            instrument=instrument,
            module="renko",
            domain="1m",
            expected=generate_renko(analysis_frame, atr_period=14),
            observed=renko,
            columns=renko_columns,
            exact_columns={"OpenTime", "CloseTime", "Direction", "ATRPeriod", "SourceCount", "SourceCloseTime"},
            numeric_columns={"Open", "High", "Low", "Close", "BrickSize"},
            time_columns={"OpenTime", "CloseTime", "SourceCloseTime"},
            int_columns={"Direction", "ATRPeriod", "SourceCount"},
        )
    )
    checks.append(
        check_before_cutoff(
            instrument=instrument,
            module="renko",
            domain="1m",
            frame=renko,
            time_column="SourceCloseTime",
            analysis_end_utc=analysis_end_utc,
        )
    )

    ha_columns = [
        "OpenTime",
        "CloseTime",
        "HAOpen",
        "HAHigh",
        "HALow",
        "HAClose",
        "RealOpen",
        "RealHigh",
        "RealLow",
        "RealClose",
        "Direction",
        "SourceCount",
    ]
    heiken_ashi = read_csv(export_dir / "heiken_ashi.csv")
    checks.append(
        compare_frames(
            instrument=instrument,
            module="heiken_ashi",
            domain="1m",
            expected=generate_heiken_ashi(analysis_frame),
            observed=heiken_ashi,
            columns=ha_columns,
            exact_columns={"OpenTime", "CloseTime", "Direction", "SourceCount"},
            numeric_columns={"HAOpen", "HAHigh", "HALow", "HAClose", "RealOpen", "RealHigh", "RealLow", "RealClose"},
            time_columns={"OpenTime", "CloseTime"},
            int_columns={"Direction", "SourceCount"},
        )
    )
    checks.append(
        check_before_cutoff(
            instrument=instrument,
            module="heiken_ashi",
            domain="1m",
            frame=heiken_ashi,
            time_column="CloseTime",
            analysis_end_utc=analysis_end_utc,
        )
    )

    for domain in DOMAINS:
        domain_frame = aggregate_ohlc(
            analysis_frame,
            period_minutes=domain.period_minutes,
            min_coverage=domain.min_coverage,
        )
        aggregator = read_csv(export_dir / f"bar_aggregator_{domain.label}.csv")
        aggregator_columns = ["Symbol", "OpenTime", "CloseTime", "Open", "High", "Low", "Close", "TickVolume", "SourceBars"]
        checks.append(
            compare_frames(
                instrument=instrument,
                module="bar_aggregator",
                domain=domain.label,
                expected=domain_frame,
                observed=aggregator,
                columns=aggregator_columns,
                exact_columns={"Symbol", "OpenTime", "CloseTime", "TickVolume", "SourceBars"},
                numeric_columns={"Open", "High", "Low", "Close"},
                time_columns={"OpenTime", "CloseTime"},
                int_columns={"TickVolume", "SourceBars"},
                string_columns={"Symbol"},
            )
        )
        checks.append(
            check_before_cutoff(
                instrument=instrument,
                module="bar_aggregator",
                domain=domain.label,
                frame=aggregator,
                time_column="CloseTime",
                analysis_end_utc=analysis_end_utc,
            )
        )

        market_bias = read_csv(export_dir / f"market_bias_{domain.label}.csv")
        expected_market_bias = compute_market_bias(domain_frame).select(
            ["CloseTime", "osc_bias", "osc_smooth", "sign_state", "four_way_state"]
        )
        checks.append(
            compare_frames(
                instrument=instrument,
                module="market_bias",
                domain=domain.label,
                expected=expected_market_bias,
                observed=market_bias,
                columns=["CloseTime", "osc_bias", "osc_smooth", "sign_state", "four_way_state"],
                exact_columns={"CloseTime", "sign_state", "four_way_state"},
                numeric_columns={"osc_bias", "osc_smooth"},
                time_columns={"CloseTime"},
                string_columns={"sign_state", "four_way_state"},
            )
        )
        checks.append(
            check_before_cutoff(
                instrument=instrument,
                module="market_bias",
                domain=domain.label,
                frame=market_bias,
                time_column="CloseTime",
                analysis_end_utc=analysis_end_utc,
            )
        )

        warmup = read_csv(export_dir / f"market_bias_warmup_{domain.label}.csv")
        expected_warmup = pl.DataFrame([convergence_warmup(domain_frame)])
        checks.append(
            compare_frames(
                instrument=instrument,
                module="market_bias_warmup",
                domain=domain.label,
                expected=expected_warmup,
                observed=warmup,
                columns=["w_converge", "W", "converged"],
                exact_columns={"w_converge", "W", "converged"},
                numeric_columns=set(),
                time_columns=set(),
                int_columns={"w_converge", "W"},
                bool_columns={"converged"},
            )
        )

        # MA strategy correctness is validated BEHAVIORALLY (suite reproduction
        # below), NOT by byte-parity against a Python generation engine
        # (design.md v2, D-parity). The binding v2 closure routes the cTrader
        # StrategyHost `positions.parquet` (with real OHLC) through
        # `xen.signals.screen_emitted_run`; this console path is a developer smoke.
        positions = read_csv(export_dir / f"ma_crossover_positions_{domain.label}.csv")
        csharp_positions[domain.label] = positions
        checks.append(
            check_before_cutoff(
                instrument=instrument,
                module="ma_crossover_positions",
                domain=domain.label,
                frame=positions,
                time_column="SourceCloseTime",
                analysis_end_utc=analysis_end_utc,
            )
        )

        events = read_csv(export_dir / f"ma_crossover_events_{domain.label}.csv")
        trades = read_csv(export_dir / f"ma_crossover_trades_{domain.label}.csv")
        checks.append(validate_trade_blotter(instrument, domain.label, events, trades))

    return checks, csharp_positions


def validate_trade_blotter(
    instrument: str,
    domain: str,
    events: pl.DataFrame,
    trades: pl.DataFrame,
) -> CheckResult:
    """Check that diagnostic trades mirror MA event transitions."""
    expected_rows = events.height
    if trades.height != expected_rows:
        return CheckResult(
            instrument,
            "ma_crossover_trades",
            domain,
            "FAIL",
            expected_rows,
            trades.height,
            None,
            "trade/event row count mismatch",
        )
    if expected_rows == 0:
        return CheckResult(instrument, "ma_crossover_trades", domain, "PASS", 0, 0, None, "empty transitions")

    event_norm = normalize_frame(
        events,
        columns=["SourceCloseTime", "PreviousPosition", "Position"],
        time_columns={"SourceCloseTime"},
        int_columns={"PreviousPosition", "Position"},
        bool_columns=set(),
        string_columns=set(),
    )
    trade_norm = normalize_frame(
        trades,
        columns=["SourceCloseTime", "PreviousPosition", "Position"],
        time_columns={"SourceCloseTime"},
        int_columns={"PreviousPosition", "Position"},
        bool_columns=set(),
        string_columns=set(),
    )
    if event_norm.to_dict(as_series=False) != trade_norm.to_dict(as_series=False):
        return CheckResult(
            instrument,
            "ma_crossover_trades",
            domain,
            "FAIL",
            expected_rows,
            trades.height,
            None,
            "trade transitions do not mirror event transitions",
        )
    return CheckResult(
        instrument,
        "ma_crossover_trades",
        domain,
        "PASS",
        expected_rows,
        trades.height,
        0.0,
        "diagnostic trades mirror events",
    )


# --------------------------------------------------------------------------- #
# Frozen-suite reproduction
# --------------------------------------------------------------------------- #
def load_mde_map() -> dict[tuple[str, str], dict[str, float]]:
    """Load EXP-003 alpha0 MDE rows by (domain, referee)."""
    frame = pl.read_csv(EXP003_MDE).filter(pl.col("alpha") == ALPHA0)
    output: dict[tuple[str, str], dict[str, float]] = {}
    for row in frame.iter_rows(named=True):
        output[(str(row["domain"]), str(row["referee"]))] = {
            "mde_bps": float(row["mde_bps"]) if row["mde_bps"] is not None else math.nan,
            "mde_grid_uncertainty_bps": (
                float(row["mde_grid_uncertainty_bps"])
                if row["mde_grid_uncertainty_bps"] is not None
                else math.nan
            ),
        }
    return output


def consistency_status(
    *,
    verdict: str,
    effect_bps: float,
    ci_lower_bps: float,
    mde_bps: float,
    uncertainty_bps: float,
) -> tuple[str, str]:
    """EXP-004 consistency rule for the known dogfood anchor."""
    if not math.isfinite(mde_bps):
        return "INCONCLUSIVE", "missing_mde"
    uncertainty = uncertainty_bps if math.isfinite(uncertainty_bps) else 0.0
    if ci_lower_bps >= mde_bps - uncertainty:
        expected = "PASS"
    elif effect_bps < mde_bps + uncertainty:
        expected = "REJECT"
    else:
        expected = "GREY"

    if expected == "GREY":
        return "INCONCLUSIVE", "grey_band"
    if verdict == expected:
        return "PASS", f"matched_{expected.lower()}"
    return "FAIL", f"expected_{expected.lower()}_got_{verdict.lower()}"


def classify_location(effect: float, ci_upper: float, mde: float, grid_unc: float) -> str:
    """EXP-009 MDE-location rule, reduced to the location label."""
    if not math.isfinite(mde):
        return "no_mde"
    band = grid_unc if math.isfinite(grid_unc) else 0.0
    if effect >= mde:
        return "at_or_above_MDE"
    if (mde - effect) <= band:
        return "near_MDE"
    if math.isfinite(ci_upper) and ci_upper < mde:
        return "below_MDE"
    return "near_MDE"


def evaluate_suite_reproduction(
    *,
    data: Any,
    csharp_positions: dict[str, pl.DataFrame],
    mde_map: dict[tuple[str, str], dict[str, float]],
) -> list[dict[str, Any]]:
    """Feed C# MA positions into the frozen referee helpers."""
    rows: list[dict[str, Any]] = []
    domain_frames = build_domain_frames(data.frame)
    for domain, domain_frame in domain_frames.items():
        returns, aligned = next_log_returns_from_bars(domain_frame)
        split_index = domain_split_index(aligned, data.train_end_ts)
        positions_frame = normalize_frame(
            csharp_positions[domain],
            columns=["Position"],
            time_columns=set(),
            int_columns={"Position"},
            bool_columns=set(),
            string_columns=set(),
        )
        positions = positions_frame["Position"].to_numpy().astype(float)[:-1]
        for verdict in evaluate_referees(
            returns,
            positions,
            instrument=data.instrument,
            domain=domain,
            alpha_values=(ALPHA0,),
            n_bootstrap=BOOTSTRAP_RESAMPLES,
            seed=seed_for("EXP-004", data.instrument, domain, "ma_20_50"),
            split_index=split_index,
        ):
            mde = mde_map.get((domain, str(verdict["referee"])), {})
            mde_bps = float(mde.get("mde_bps", math.nan))
            uncertainty_bps = float(mde.get("mde_grid_uncertainty_bps", math.nan))
            status, reason = consistency_status(
                verdict=str(verdict["verdict"]),
                effect_bps=float(verdict["effect_bps"]),
                ci_lower_bps=float(verdict["ci_lower_bps"]),
                mde_bps=mde_bps,
                uncertainty_bps=uncertainty_bps,
            )
            location = classify_location(
                float(verdict["effect_bps"]),
                float(verdict["ci_upper_bps"]),
                mde_bps,
                uncertainty_bps,
            )
            is_gate_stack = str(verdict["referee"]) == "gate_stack"
            suite_pass = (
                verdict["verdict"] == "REJECT"
                and status == "PASS"
                and reason == "matched_reject"
                and (not is_gate_stack or location == "below_MDE")
            )
            rows.append(
                {
                    "instrument": data.instrument,
                    "domain": domain,
                    "strategy": "ma_20_50",
                    "referee": verdict["referee"],
                    "alpha": verdict["alpha"],
                    "verdict": verdict["verdict"],
                    "effect_bps": verdict["effect_bps"],
                    "ci_lower_bps": verdict["ci_lower_bps"],
                    "ci_upper_bps": verdict["ci_upper_bps"],
                    "effective_n": verdict["effective_n"],
                    "block_length": verdict["block_length"],
                    "mde_bps": mde_bps,
                    "mde_grid_uncertainty_bps": uncertainty_bps,
                    "exp004_consistency_status": status,
                    "exp004_reason": reason,
                    "exp009_location_vs_mde": location,
                    "suite_reproduction_status": "PASS" if suite_pass else "FAIL",
                }
            )
    return rows


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write result rows to CSV, preserving empty-output headers where needed."""
    pl.DataFrame(rows).write_csv(path)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    configure_logging()
    args = parse_args()
    ensure_output_dirs()

    if not EXP003_MDE.exists():
        raise FileNotFoundError(f"EXP-003 MDE summary not found: {EXP003_MDE}")

    source_files = list_timebar_files(DATA_DIR)
    if not source_files:
        raise FileNotFoundError(f"No time-bar files found under {DATA_DIR / 'timebars'}")

    all_checks: list[CheckResult] = []
    suite_rows: list[dict[str, Any]] = []
    mde_map = load_mde_map()
    generated_export_dirs: list[Path] = []

    for source_path in tqdm(source_files, desc="VAL-002 parity files"):
        data = load_analysis_data(source_path)
        analysis_end_utc = analysis_end_after_slice(data.frame)
        analysis_end_iso = iso_utc(analysis_end_utc)
        export_dir = CSHARP_EXPORT_DIR / data.instrument.lower()

        if args.reuse_csharp_output:
            export_dir = find_existing_export_dir(
                args.csharp_export_root.resolve(),
                source_path,
                data.instrument,
            )
        else:
            shutil.rmtree(export_dir, ignore_errors=True)
            run_csharp_export(source_path, export_dir, analysis_end_iso)
            generated_export_dirs.append(export_dir)

        checks, csharp_positions = validate_export(
            analysis_frame=data.frame,
            export_dir=export_dir,
            analysis_end_utc=analysis_end_utc,
        )
        all_checks.extend(checks)

        if args.determinism_rerun and not args.reuse_csharp_output:
            determinism_dir = CSHARP_DETERMINISM_DIR / data.instrument.lower()
            shutil.rmtree(determinism_dir, ignore_errors=True)
            run_csharp_export(source_path, determinism_dir, analysis_end_iso)
            expected_hashes = csv_hashes(export_dir)
            observed_hashes = csv_hashes(determinism_dir)
            status = "PASS" if expected_hashes == observed_hashes else "FAIL"
            all_checks.append(
                CheckResult(
                    data.instrument,
                    "csharp_csv_determinism",
                    "all",
                    status,
                    len(expected_hashes),
                    len(observed_hashes),
                    None,
                    "CSV hashes match on rerun" if status == "PASS" else "CSV hash mismatch on rerun",
                )
            )
            shutil.rmtree(determinism_dir, ignore_errors=True)

        if not args.skip_suite:
            suite_rows.extend(
                evaluate_suite_reproduction(
                    data=data,
                    csharp_positions=csharp_positions,
                    mde_map=mde_map,
                )
            )

    parity_rows = [asdict(check) for check in all_checks]
    write_rows(RESULTS_DIR / "parity_checks.csv", parity_rows)
    if suite_rows:
        write_rows(RESULTS_DIR / "suite_reproduction.csv", suite_rows)

    parity_pass = all(row["status"] == "PASS" for row in parity_rows)
    suite_pass = args.skip_suite or all(
        row["suite_reproduction_status"] == "PASS" for row in suite_rows
    )
    overall_status = "PASS" if parity_pass and suite_pass else "FAIL"
    metadata = {
        "validation_id": VALIDATION_ID,
        "overall_status": overall_status,
        "source_files": [str(path.relative_to(PROJECT_ROOT)) for path in source_files],
        "numeric_tolerance": NUMERIC_TOLERANCE,
        "alpha_values": list(ALPHA_GRID),
        "alpha0": ALPHA0,
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "parity_checks": len(parity_rows),
        "parity_failures": sum(row["status"] != "PASS" for row in parity_rows),
        "suite_rows": len(suite_rows),
        "suite_failures": sum(
            row.get("suite_reproduction_status") != "PASS" for row in suite_rows
        ),
        "suite_skipped": bool(args.skip_suite),
        "determinism_rerun": bool(args.determinism_rerun and not args.reuse_csharp_output),
        "csharp_export_source": "existing" if args.reuse_csharp_output else "console",
        "csharp_export_root": str(args.csharp_export_root),
        "csharp_exports_retained": bool(args.reuse_csharp_output or args.keep_csharp_output),
    }
    write_json(RESULTS_DIR / "run_metadata.json", metadata)

    if not args.reuse_csharp_output and not args.keep_csharp_output:
        for export_dir in generated_export_dirs:
            shutil.rmtree(export_dir, ignore_errors=True)
        shutil.rmtree(CSHARP_DETERMINISM_DIR, ignore_errors=True)

    LOGGER.info("VAL-002 overall_status=%s", overall_status)
    LOGGER.info("Parity checks: %s failures / %s", metadata["parity_failures"], len(parity_rows))
    if not args.skip_suite:
        LOGGER.info("Suite rows: %s failures / %s", metadata["suite_failures"], len(suite_rows))

    if overall_status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
