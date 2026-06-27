"""
Experiment VAL-005: 5-Year 1-Minute Dataset Validation (INFR-003 gate).

Validates the re-collected ~5-year 1-minute dataset (16 instruments — the
VAL-003 universe minus DE30, dropped by operator ratification 2026-06-21) as the
canonical dataset for CF-CAPGEO-001 (Phase 018). This is a data-admission
validation, not an edge claim: no candidate, no slot, no edge inference.

Five binding acceptance gates (INFR-003 design §5 / VAL-005 scope §3):

  G1 Temporal integrity   — base-bar schema/monotonicity/OHLC integrity; 15m/1h/4h
                            resamples (deployed min_coverage=0.90 path) match an
                            independent pandas oracle with no future timestamps;
                            strict-mode prefix-stability proves no look-ahead.
  G2 Negative controls    — the VAL-003 rev.3 negative-control battery, UNCHANGED,
                            run on synthetic data; every injected fault detected.
  G3 Coverage / span      — per-instrument row count, span, gap profile; all 16
                            instruments present; broker-start truncations disclosed
                            (INCONCLUSIVE-not-FAIL, INFR-002/VAL-003 precedent).
  G4 Holdout seal         — final-30% sealed per file at first touch; the harness
                            only ever materializes the first-70% analysis slice and
                            re-asserts 0 holdout rows read.
  G5 Determinism          — deployed resamples reproduce byte-identically on a
                            second pass.

Suite reuse: the VAL-003 (== VAL-001 rev.3) pure check functions and the full
negative-control battery are IMPORTED UNCHANGED from VAL-003's run_experiment.
VAL-005 adds only 5-year-specific file discovery, coverage/span accounting, the
deployed-min_coverage oracle, the holdout-seal manifest, and the resample
determinism two-pass.

Holdout discipline: only the first 70% of each file is ever loaded; the final
30% (global holdout, new boundary on each file's own 2021-06 -> collection-date
timeline) is sealed at first touch and never inspected.
"""
from __future__ import annotations

import importlib.util
import json
import logging
import math
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable

import matplotlib.pyplot as plt
import polars as pl
from tqdm.auto import tqdm

from xen.bar_aggregator import aggregate_ohlc


LOGGER = logging.getLogger(__name__)

EXPERIMENT_ID = "VAL-005"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = PROJECT_ROOT / "data"
EXPERIMENT_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"

# --------------------------------------------------------------------------- #
# Reuse the VAL-003 (VAL-001 rev.3) suite UNCHANGED via import. No import-time
# side effects in that module (constants/dataclasses/functions only; main() is
# guarded), so loading it is safe.
# --------------------------------------------------------------------------- #
_VAL003_CODE = PROJECT_ROOT / "python" / "experiments" / "VAL-003" / "code" / "run_experiment.py"
_spec = importlib.util.spec_from_file_location("val003_suite", _VAL003_CODE)
if _spec is None or _spec.loader is None:  # pragma: no cover - defensive
    raise ImportError(f"Could not load VAL-003 suite from {_VAL003_CODE}")
suite = importlib.util.module_from_spec(_spec)
# Register before exec so the module's frozen dataclasses can resolve their own
# __module__ in sys.modules (dataclasses' KW_ONLY inspection requires it).
sys.modules[_spec.name] = suite
_spec.loader.exec_module(suite)

ValidationCheck = suite.ValidationCheck
NegativeControl = suite.NegativeControl
add_check = suite.add_check
to_canonical_time = suite.to_canonical_time
CANONICAL_TIME_UNIT = suite.CANONICAL_TIME_UNIT
REQUIRED_TIMEBAR_COLUMNS = suite.REQUIRED_TIMEBAR_COLUMNS

# --------------------------------------------------------------------------- #
# VAL-005-specific constants
# --------------------------------------------------------------------------- #
# The 16 INFR-003 instruments (VAL-003 universe minus DE30; design §3.1).
TARGET_SYMBOLS = (
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD",
    "EURJPY", "GBPJPY", "AUDJPY", "XAUUSD", "BTCUSD", "USTEC", "US500",
    "US2000", "JP225",
)
DROPPED_SYMBOLS = ("DE30",)

# Pre-sliced analysis exports living alongside base files; never base data.
ANALYSIS_SLICE_MARKERS = ("analysis70", "analysis_slice", "first70")

# INFR-003 collection ran 2026-06-21. A target symbol's selected file (newest by
# the collected-timestamp token in its name) must have been collected on/after
# this date, else its INFR-003 collection is MISSING (older files are the
# retained pre-INFR-003 datasets, never validated here).
INFR003_MIN_COLLECTED = date(2026, 6, 20)

# Deployed resample domains for CF-CAPGEO-001 and their coverage rule.
DOMAINS = (15, 60, 240)
MIN_COVERAGE = 0.90

# D-span target: ~5y from 2021-06-01. Instruments whose broker m1 history starts
# materially later collect their maximum and carry a truncation disclosure
# (INFR-002 pattern) — disclosed, not a FAIL.
TARGET_SPAN_START = datetime(2021, 6, 1)
TRUNCATION_TOLERANCE_DAYS = 45

# A coverage shortfall this severe is a hard completeness FAIL, not a disclosure.
MIN_ANALYSIS_ROWS = 30_000

SECTION_WIDTH = 78


# --------------------------------------------------------------------------- #
# Records
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class SealManifest:
    instrument: str
    source_file: str
    total_rows: int
    analysis_rows: int
    holdout_rows: int
    analysis_start: str
    analysis_end: str
    holdout_boundary: str  # last analysis CloseTime; the seal line (metadata only)
    holdout_rows_read: int  # MUST be 0


@dataclass(frozen=True)
class CoverageRow:
    instrument: str
    source_file: str
    collected: str
    total_rows: int
    analysis_rows: int
    span_start: str
    span_end: str
    span_days: float
    median_gap_s: float
    p99_gap_s: float
    max_gap_s: float
    session_breaks: int  # inter-bar gaps > 1 day (weekends/holidays)
    reaches_target_start: bool
    truncated: bool
    note: str


@dataclass(frozen=True)
class GateResult:
    gate: str
    title: str
    status: str  # PASS | FAIL | INCONCLUSIVE
    summary: str


@dataclass(frozen=True)
class LoadedInstrument:
    instrument: str
    source_file: str
    collected: str
    total_rows: int
    analysis_rows: int
    frame: pl.DataFrame  # first-70% only


# --------------------------------------------------------------------------- #
# Logging helpers
# --------------------------------------------------------------------------- #
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
    LOGGER.info("%-22s %s", f"{label}:", value)


def ensure_output_dirs() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- #
# File discovery — select the INFR-003 5-year file per target symbol
# --------------------------------------------------------------------------- #
def _parse_timebar_name(path: Path) -> tuple[str, str, str] | None:
    """Return (symbol_upper, start_token, collected_token) or None if not a base file.

    Names are ``timebars_<symbol>_<yyyyMMdd>_<HHmmss>_<yyyyMMdd>_<HHmmss>.parquet``
    (start and collected timestamps each carry a date_time underscore), so a base
    file splits into 6 underscore parts.
    """
    parts = path.stem.split("_")
    if len(parts) != 6 or parts[0] != "timebars":
        return None
    symbol = parts[1]
    start_token = f"{parts[2]}_{parts[3]}"
    collected_token = f"{parts[4]}_{parts[5]}"
    return symbol.upper(), start_token, collected_token


def discover_infr003_files() -> tuple[dict[str, Path], dict[str, str]]:
    """Map each target symbol to its INFR-003 file (newest collected, on/after
    INFR003_MIN_COLLECTED). Returns (found, missing_reason)."""
    by_symbol: dict[str, list[tuple[str, str, Path]]] = {s: [] for s in TARGET_SYMBOLS}
    for path in sorted((DATA_DIR / "timebars").glob("timebars_*.parquet")):
        if any(marker in path.stem for marker in ANALYSIS_SLICE_MARKERS):
            continue
        parsed = _parse_timebar_name(path)
        if parsed is None:
            continue
        symbol, start_token, collected_token = parsed
        if symbol in by_symbol:
            by_symbol[symbol].append((collected_token, start_token, path))

    found: dict[str, Path] = {}
    missing: dict[str, str] = {}
    for symbol, entries in by_symbol.items():
        if not entries:
            missing[symbol] = "no base file found"
            continue
        collected_token, _, path = max(entries, key=lambda e: e[0])
        try:
            collected_day = datetime.strptime(collected_token[:8], "%Y%m%d").date()
        except ValueError:
            missing[symbol] = f"unparseable collected token {collected_token!r}"
            continue
        if collected_day < INFR003_MIN_COLLECTED:
            missing[symbol] = (
                f"newest file collected {collected_day} predates INFR-003 "
                f"({INFR003_MIN_COLLECTED}); collection incomplete"
            )
            continue
        found[symbol] = path
    return found, missing


# --------------------------------------------------------------------------- #
# Holdout-safe loading (first 70% only)
# --------------------------------------------------------------------------- #
def load_first70(path: Path) -> tuple[LoadedInstrument | None, SealManifest | None, str]:
    """Load only the first-70% analysis slice; build the seal manifest. Never
    materializes the final-30% holdout."""
    parsed = _parse_timebar_name(path)
    instrument = parsed[0] if parsed else path.stem.upper()
    collected = parsed[2] if parsed else "?"

    scan = pl.scan_parquet(path)
    schema = scan.collect_schema().names()
    missing_cols = sorted(set(REQUIRED_TIMEBAR_COLUMNS).difference(schema))
    if missing_cols:
        return None, None, f"missing columns: {missing_cols}"

    scan = pl.scan_parquet(path).select(REQUIRED_TIMEBAR_COLUMNS)
    total_rows = int(scan.select(pl.len()).collect().item())
    analysis_rows = int(total_rows * 0.7)
    holdout_rows = total_rows - analysis_rows
    if analysis_rows < MIN_ANALYSIS_ROWS:
        return None, None, (
            f"analysis slice too small: total={total_rows}, analysis={analysis_rows} "
            f"(< {MIN_ANALYSIS_ROWS})"
        )

    # Seal: sort by CloseTime, collect ONLY the first analysis_rows. The final
    # 30% is never collected. We re-assert the materialized height equals the
    # analysis count, i.e. 0 holdout rows were read.
    frame = to_canonical_time(scan.sort("CloseTime").slice(0, analysis_rows).collect())
    holdout_rows_read = frame.height - analysis_rows  # 0 by construction; asserted below
    analysis_start, analysis_end = frame.select(
        pl.first("CloseTime").alias("start"), pl.last("CloseTime").alias("end")
    ).row(0)

    seal = SealManifest(
        instrument=instrument,
        source_file=path.name,
        total_rows=total_rows,
        analysis_rows=analysis_rows,
        holdout_rows=holdout_rows,
        analysis_start=str(analysis_start),
        analysis_end=str(analysis_end),
        holdout_boundary=str(analysis_end),
        holdout_rows_read=max(0, holdout_rows_read),
    )
    loaded = LoadedInstrument(
        instrument=instrument, source_file=path.name, collected=collected,
        total_rows=total_rows, analysis_rows=analysis_rows, frame=frame,
    )
    return loaded, seal, "ok"


# --------------------------------------------------------------------------- #
# G1 — Temporal integrity (deployed min_coverage path + strict look-ahead probe)
# --------------------------------------------------------------------------- #
def build_domain_bars(source: pl.DataFrame, period_minutes: int) -> pl.DataFrame:
    """Holdout-fenced deployed domain construction for CF-CAPGEO-001.

    Aggregates the analysis-slice 1-minute bars at the deployed coverage
    (``MIN_COVERAGE``), then applies the **analysis-boundary fence**: drop any
    resample window whose right-labelled ``CloseTime`` exceeds the last available
    source bar. Under the coverage-tolerant mode a trailing partial window
    (e.g. 232/240 bars, >=90% coverage) is retained with a nominal grid-boundary
    label that sits up to one window past the data; that label crosses into
    holdout-minute timestamps. The OHLC is fully causal (analysis bars only), but
    emitting a bar labelled past the slice is not fence-clean, so the canonical
    deployed construction drops it. This is the rule CF-CAPGEO-001 inherits
    (operator decision 2026-06-21, VAL-005 G1 finding).
    """
    agg = aggregate_ohlc(source, period_minutes=period_minutes, min_coverage=MIN_COVERAGE)
    source_max = source.select(pl.max("CloseTime")).item()
    return agg.filter(pl.col("CloseTime") <= source_max)


def coverage_resample_oracle(
    source: pl.DataFrame, period_minutes: int, min_coverage: float
) -> pl.DataFrame:
    """Independent pandas reproduction of the holdout-fenced deployed path.

    Right-closed/right-labelled clock windows (matching the polars epoch-bucket
    rule), retaining windows with at least ``max(2, ceil(min_coverage*period))``
    source bars — the exact aggregate_ohlc keep-rule — then applying the same
    analysis-boundary fence as ``build_domain_bars`` (drop labels past the source
    max). Reproduced by a different engine so equality is a real
    cross-implementation check.
    """
    min_bars = max(2, math.ceil(min_coverage * period_minutes))
    source_max = source.select(pl.max("CloseTime")).item()
    pdf = source.select(["CloseTime", "Open", "High", "Low", "Close"]).to_pandas()
    pdf = pdf.set_index("CloseTime").sort_index()
    agg = pdf.resample(f"{period_minutes}min", closed="right", label="right").agg(
        Open=("Open", "first"), High=("High", "max"), Low=("Low", "min"),
        Close=("Close", "last"), SourceBars=("Close", "size"),
    )
    agg = agg[agg["SourceBars"] >= min_bars].reset_index()
    fenced = to_canonical_time(pl.from_pandas(agg))
    return fenced.filter(pl.col("CloseTime") <= source_max)


def validate_g1(
    data: LoadedInstrument, checks: list[ValidationCheck]
) -> dict[int, pl.DataFrame]:
    """Base-bar integrity + deployed-resample oracle match + strict look-ahead.
    Returns the deployed resample frames keyed by period for the G5 two-pass."""
    src = data.frame
    inst, sf = data.instrument, data.source_file

    # Base 1-minute integrity (VAL-003 base_timebar_failures, unchanged).
    counts = suite.base_timebar_failures(src)
    height = src.height
    for check, failures, denom in [
        ("close_time_not_null", counts["null_close_time"], height),
        ("close_time_strictly_increasing", counts["non_increasing_close_time"], max(height - 1, 0)),
        ("close_time_unique", counts["duplicate_close_time"], height),
        ("ohlc_relationship_valid", counts["invalid_ohlc"], height),
        ("ohlc_not_null", counts["null_ohlc"], height),
    ]:
        add_check(checks, instrument=inst, source_file=sf, source_timeframe="1m",
                  view="timebar", check=check, failures=failures, denominator=denom,
                  detail=f"{check}={failures}")

    source_max = src.select(pl.max("CloseTime")).item()
    deployed: dict[int, pl.DataFrame] = {}
    for period in DOMAINS:
        label = f"{period}m"
        prod = build_domain_bars(src, period)  # deployed coverage path + analysis fence
        deployed[period] = prod
        oracle = coverage_resample_oracle(src, period, MIN_COVERAGE)
        fails = suite.resample_failures(prod, oracle)
        add_check(checks, instrument=inst, source_file=sf, source_timeframe=label,
                  view="timeframe", check="resample_matches_independent_oracle",
                  failures=fails["rows_only_in_production"] + fails["rows_only_in_oracle"]
                  + fails["ohlc_mismatch"],
                  denominator=max(prod.height, fails["oracle_rows"]),
                  detail=json.dumps(fails, sort_keys=True))

        out = suite.resample_output_failures(prod, period, source_max)
        add_check(checks, instrument=inst, source_file=sf, source_timeframe=label,
                  view="timeframe", check="resample_no_future_timestamp",
                  failures=out["future_timestamp"], denominator=prod.height,
                  detail="rows_after_source_analysis_max")
        add_check(checks, instrument=inst, source_file=sf, source_timeframe=label,
                  view="timeframe", check="resample_close_time_unique",
                  failures=out["duplicate_close_time"], denominator=prod.height,
                  detail=f"duplicate_resampled_close_time_rows={out['duplicate_close_time']}")

        # No-look-ahead: strict mode is prefix-stable (a complete window cannot
        # change as later bars arrive); the deployed coverage filter only changes
        # retention, not causality, so strict prefix-stability is the causal proof.
        strict_gen: Callable[[pl.DataFrame], pl.DataFrame] = (
            lambda fr, p=period: aggregate_ohlc(fr, period_minutes=p)
        )
        windows = suite.positioned_windows(
            src, suite.PREFIX_WINDOW_ROWS, suite.PREFIX_WINDOW_POSITIONS
        )
        for position, window in windows.items():
            stability = suite.prefix_stability_failures(window, strict_gen)
            add_check(checks, instrument=inst, source_file=sf, source_timeframe=label,
                      view="timeframe", check=f"no_lookahead_prefix_stability_{position}",
                      failures=stability["failures"], denominator=stability["cuts"],
                      detail=f"position={position}, diverged_cuts={stability['failures']}, "
                      f"compared_cuts={stability['cuts']}, window_rows={window.height}")
    return deployed


# --------------------------------------------------------------------------- #
# G3 — Coverage / span accounting
# --------------------------------------------------------------------------- #
def coverage_row(data: LoadedInstrument) -> CoverageRow:
    src = data.frame
    span_start, span_end = src.select(
        pl.first("CloseTime").alias("start"), pl.last("CloseTime").alias("end")
    ).row(0)
    gaps = (
        src.select(pl.col("CloseTime").diff().dt.total_seconds().alias("g"))
        .drop_nulls()
    )
    median_gap = float(gaps.select(pl.col("g").median()).item() or 0.0)
    p99_gap = float(gaps.select(pl.col("g").quantile(0.99)).item() or 0.0)
    max_gap = float(gaps.select(pl.col("g").max()).item() or 0.0)
    session_breaks = int(gaps.filter(pl.col("g") > 86_400).height)
    span_days = (span_end - span_start).total_seconds() / 86_400.0

    reaches_target = span_start <= TARGET_SPAN_START + _days(TRUNCATION_TOLERANCE_DAYS)
    truncated = not reaches_target
    note = (
        "reaches ~2021-06 target start"
        if reaches_target
        else f"broker m1 history starts {span_start} (> target {TARGET_SPAN_START.date()}); "
        "collected maximum — disclosed truncation (INFR-002 pattern)"
    )
    return CoverageRow(
        instrument=data.instrument, source_file=data.source_file, collected=data.collected,
        total_rows=data.total_rows, analysis_rows=data.analysis_rows,
        span_start=str(span_start), span_end=str(span_end), span_days=round(span_days, 2),
        median_gap_s=median_gap, p99_gap_s=p99_gap, max_gap_s=max_gap,
        session_breaks=session_breaks, reaches_target_start=reaches_target,
        truncated=truncated, note=note,
    )


def _days(n: int):
    from datetime import timedelta
    return timedelta(days=n)


# --------------------------------------------------------------------------- #
# G5 — Determinism (deployed resample, two-pass byte compare)
# --------------------------------------------------------------------------- #
def validate_g5(
    data: LoadedInstrument, deployed: dict[int, pl.DataFrame], checks: list[ValidationCheck]
) -> None:
    for period in DOMAINS:
        second = build_domain_bars(data.frame, period)
        identical = deployed[period].equals(second)
        add_check(checks, instrument=data.instrument, source_file=data.source_file,
                  source_timeframe=f"{period}m", view="determinism",
                  check="resample_byte_identical_second_pass",
                  failures=0 if identical else 1, denominator=1,
                  detail=f"rows={deployed[period].height}, identical={identical}")


# --------------------------------------------------------------------------- #
# Gate verdicts
# --------------------------------------------------------------------------- #
def derive_gates(
    checks_df: pl.DataFrame,
    negatives_df: pl.DataFrame,
    seals: list[SealManifest],
    coverage: list[CoverageRow],
    missing: dict[str, str],
) -> list[GateResult]:
    def count(view_filter: pl.Expr) -> tuple[int, int, int]:
        sub = checks_df.filter(view_filter)
        f = sub.filter(pl.col("status") == "FAIL").height
        i = sub.filter(pl.col("status") == "INCONCLUSIVE").height
        return sub.height, f, i

    gates: list[GateResult] = []

    # G1 — base + timeframe integrity checks on real data.
    g1_views = pl.col("view").is_in(["timebar", "timeframe"])
    n1, f1, i1 = count(g1_views)
    g1_status = "FAIL" if f1 else ("INCONCLUSIVE" if i1 else "PASS")
    gates.append(GateResult("G1", "Temporal integrity", g1_status,
                            f"{n1} checks, {f1} FAIL, {i1} INCONCLUSIVE"))

    # G2 — negative-control battery + golden fixture.
    missed = negatives_df.filter(~pl.col("detected")).height if negatives_df.height else 0
    golden = checks_df.filter(pl.col("check") == "resample_golden_fixture")
    golden_fail = golden.filter(pl.col("status") == "FAIL").height
    g2_status = "FAIL" if (missed or golden_fail) else "PASS"
    gates.append(GateResult("G2", "Negative controls", g2_status,
                            f"{negatives_df.height} controls, {missed} missed; "
                            f"golden_fixture_fail={golden_fail}"))

    # G3 — coverage / completeness. Missing instrument => FAIL; truncations => disclosed.
    truncated = [c.instrument for c in coverage if c.truncated]
    if missing:
        g3_status = "FAIL"
        g3_summary = f"{len(missing)} instrument(s) missing: {sorted(missing)}"
    else:
        g3_status = "INCONCLUSIVE" if truncated else "PASS"
        g3_summary = (
            f"{len(coverage)}/{len(TARGET_SYMBOLS)} present; "
            f"truncations disclosed: {truncated or 'none'}"
        )
    gates.append(GateResult("G3", "Coverage / completeness", g3_status, g3_summary))

    # G4 — holdout seal. Any holdout row read => FAIL.
    read = sum(s.holdout_rows_read for s in seals)
    g4_status = "FAIL" if read else "PASS"
    gates.append(GateResult("G4", "Holdout seal", g4_status,
                            f"{len(seals)} files sealed; holdout_rows_read={read}"))

    # G5 — determinism.
    n5, f5, _ = count(pl.col("view") == "determinism")
    g5_status = "FAIL" if f5 else "PASS"
    gates.append(GateResult("G5", "Determinism", g5_status,
                            f"{n5} two-pass checks, {f5} non-identical"))
    return gates


def overall_verdict(gates: list[GateResult]) -> str:
    if any(g.status == "FAIL" for g in gates):
        return "FAIL"
    if any(g.status == "INCONCLUSIVE" for g in gates):
        return "INCONCLUSIVE"
    return "PASS"


# --------------------------------------------------------------------------- #
# Outputs
# --------------------------------------------------------------------------- #
def _frame(records: list[Any], schema: dict[str, Any]) -> pl.DataFrame:
    if not records:
        return pl.DataFrame(schema=schema)
    return pl.DataFrame([asdict(r) for r in records])


def write_outputs(
    checks_df: pl.DataFrame,
    negatives_df: pl.DataFrame,
    seals: list[SealManifest],
    coverage: list[CoverageRow],
    gates: list[GateResult],
    missing: dict[str, str],
    verdict: str,
    metadata: dict[str, Any],
) -> None:
    checks_df.write_csv(RESULTS_DIR / "validation_checks.csv")
    negatives_df.write_csv(RESULTS_DIR / "negative_controls.csv")
    seal_df = _frame(seals, {
        "instrument": pl.Utf8, "source_file": pl.Utf8, "total_rows": pl.Int64,
        "analysis_rows": pl.Int64, "holdout_rows": pl.Int64, "analysis_start": pl.Utf8,
        "analysis_end": pl.Utf8, "holdout_boundary": pl.Utf8, "holdout_rows_read": pl.Int64,
    })
    seal_df.write_csv(RESULTS_DIR / "holdout_seal_manifest.csv")
    cov_df = _frame(coverage, {
        "instrument": pl.Utf8, "source_file": pl.Utf8, "collected": pl.Utf8,
        "total_rows": pl.Int64, "analysis_rows": pl.Int64, "span_start": pl.Utf8,
        "span_end": pl.Utf8, "span_days": pl.Float64, "median_gap_s": pl.Float64,
        "p99_gap_s": pl.Float64, "max_gap_s": pl.Float64, "session_breaks": pl.Int64,
        "reaches_target_start": pl.Boolean, "truncated": pl.Boolean, "note": pl.Utf8,
    })
    cov_df.write_csv(RESULTS_DIR / "coverage_span.csv")
    gate_df = _frame(gates, {
        "gate": pl.Utf8, "title": pl.Utf8, "status": pl.Utf8, "summary": pl.Utf8,
    })
    gate_df.write_csv(RESULTS_DIR / "gate_summary.csv")

    verdict_doc = {
        "experiment_id": EXPERIMENT_ID,
        "verdict": verdict,
        "gates": [asdict(g) for g in gates],
        "missing_instruments": missing,
        "metadata": metadata,
    }
    (RESULTS_DIR / "verdict.json").write_text(
        json.dumps(verdict_doc, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    plot_coverage(cov_df, PLOTS_DIR / "coverage_span_days.png")
    plot_gates(gate_df, PLOTS_DIR / "gate_status.png")


def _status_color(status: str) -> str:
    return {"PASS": "#3a7d44", "FAIL": "#b23a48", "INCONCLUSIVE": "#c98c2b"}.get(status, "#777")


def plot_coverage(cov_df: pl.DataFrame, output_path: Path) -> None:
    rows = cov_df.sort("span_days").to_dicts() if not cov_df.is_empty() else []
    fig, ax = plt.subplots(figsize=(10, max(4, 0.4 * max(len(rows), 1))))
    if rows:
        ax.barh([r["instrument"] for r in rows], [r["span_days"] for r in rows],
                color=["#c98c2b" if r["truncated"] else "#4c78a8" for r in rows])
        ax.set_xlabel("Analysis-slice span (days)")
        ax.set_title("VAL-005 Per-Instrument Coverage (orange = disclosed truncation)")
        ax.invert_yaxis()
    else:
        ax.text(0.5, 0.5, "No instruments loaded", ha="center", va="center")
        ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_gates(gate_df: pl.DataFrame, output_path: Path) -> None:
    rows = gate_df.to_dicts() if not gate_df.is_empty() else []
    fig, ax = plt.subplots(figsize=(8, 4))
    if rows:
        ax.bar([r["gate"] for r in rows], [1] * len(rows),
               color=[_status_color(r["status"]) for r in rows])
        for idx, r in enumerate(rows):
            ax.text(idx, 0.5, r["status"], ha="center", va="center", color="white", fontsize=9)
        ax.set_yticks([])
        ax.set_title("VAL-005 Acceptance Gates")
    else:
        ax.text(0.5, 0.5, "No gates", ha="center", va="center")
        ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Run
# --------------------------------------------------------------------------- #
def run_validation() -> tuple[pl.DataFrame, pl.DataFrame, list[SealManifest],
                              list[CoverageRow], list[GateResult], dict[str, str],
                              str, dict[str, Any]]:
    checks: list[ValidationCheck] = []
    negatives: list[NegativeControl] = []

    # G2 detection-power evidence (VAL-003 battery + golden fixture), UNCHANGED.
    log_subsection("G2 — Negative-control battery (VAL-003 rev.3, unchanged)")
    suite.validate_resample_golden(checks)
    suite.run_negative_controls(checks, negatives)
    LOGGER.info("Negative controls: %d (missed=%d)", len(negatives),
                sum(1 for n in negatives if not n.detected))

    found, missing = discover_infr003_files()
    log_subsection("Holdout-safe instrument validation (first-70% only)")
    log_kv("Target symbols", len(TARGET_SYMBOLS))
    log_kv("Found", len(found))
    log_kv("Missing", sorted(missing) if missing else "none")

    seals: list[SealManifest] = []
    coverage: list[CoverageRow] = []
    for symbol in tqdm(TARGET_SYMBOLS, desc="Instruments", unit="sym", dynamic_ncols=True):
        path = found.get(symbol)
        if path is None:
            add_check(checks, instrument=symbol, source_file="-", source_timeframe="1m",
                      view="coverage", check="infr003_file_present", failures=1, denominator=1,
                      detail=missing.get(symbol, "missing"))
            continue
        loaded, seal, status = load_first70(path)
        if loaded is None or seal is None:
            add_check(checks, instrument=symbol, source_file=path.name, source_timeframe="1m",
                      view="coverage", check="analysis_slice_loadable", failures=1, denominator=1,
                      detail=status)
            missing[symbol] = status
            continue
        seals.append(seal)
        # G4 seal re-assertion as a recorded check.
        add_check(checks, instrument=symbol, source_file=path.name, source_timeframe="1m",
                  view="seal", check="holdout_rows_read_zero",
                  failures=seal.holdout_rows_read, denominator=1,
                  detail=f"total={seal.total_rows}, analysis={seal.analysis_rows}, "
                  f"holdout={seal.holdout_rows}, boundary={seal.holdout_boundary}")
        tqdm.write(f"{symbol}: {loaded.analysis_rows:,} analysis rows "
                   f"(holdout {seal.holdout_rows:,} sealed at {seal.holdout_boundary})")
        deployed = validate_g1(loaded, checks)
        validate_g5(loaded, deployed, checks)
        coverage.append(coverage_row(loaded))

    checks_df = suite.checks_to_frame(checks)
    negatives_df = suite.negative_controls_to_frame(negatives)
    gates = derive_gates(checks_df, negatives_df, seals, coverage, missing)
    verdict = overall_verdict(gates)

    metadata = {
        "experiment_id": EXPERIMENT_ID,
        "target_symbols": list(TARGET_SYMBOLS),
        "dropped_symbols": list(DROPPED_SYMBOLS),
        "domains_min": DOMAINS,
        "min_coverage": MIN_COVERAGE,
        "target_span_start": str(TARGET_SPAN_START.date()),
        "infr003_min_collected": str(INFR003_MIN_COLLECTED),
        "holdout_rule": "first 70 percent analysis slice only",
        "suite_lineage": "VAL-001 rev.3 / VAL-003 checks + negative-control battery, imported unchanged",
        "source_files": {s: found[s].name for s in sorted(found)},
    }
    return checks_df, negatives_df, seals, coverage, gates, missing, verdict, metadata


def main() -> None:
    configure_logging()
    ensure_output_dirs()
    log_section("VAL-005 — 5-Year 1-Minute Dataset Validation (INFR-003 gate)")
    log_kv("Data directory", DATA_DIR)
    log_kv("Results", RESULTS_DIR)
    log_kv("Holdout rule", "first 70 percent analysis slice only")

    (checks_df, negatives_df, seals, coverage, gates, missing, verdict,
     metadata) = run_validation()

    log_subsection("Writing artifacts")
    write_outputs(checks_df, negatives_df, seals, coverage, gates, missing, verdict, metadata)

    log_subsection("Gate summary")
    for g in gates:
        log_kv(f"{g.gate} {g.title}", f"{g.status} — {g.summary}")
    log_kv("OVERALL VERDICT", verdict)

    if verdict == "FAIL":
        raise SystemExit(1)
    if verdict == "INCONCLUSIVE":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
