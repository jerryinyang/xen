"""Experiment EXP-043: Phase 011 Track A Substrate Readiness (Baseline Entry, 51 Cells).

Implements the analysis plan from analysis-plan.md (descriptive/readiness; 0 tests).

For each of 51 instrument×domain cells (17 instruments × {1h, 2h, 4h}), on the
TRAIN stratum only (first 70% of the first-70% analysis slice, R1.3 1-minute
file-order rows; F01 pattern — no full-file sort):

1. construction integrity of the clock-aligned domain bars (2h is first-ever,
   P7 ``min_coverage=0.90``; 1h/4h use the same established 0.90 convention);
2. frozen-baseline AVWAP event generation — ``generate_avwap_events`` with
   defaults only (``band_multiplier=1.0``, ``arm_at_adverse_band=False``);
3. exact invariant battery over the event and regime tables;
4. full second regeneration with frame-identical comparison (determinism);
5. TRAIN event rates and the predeclared projected TEST count
   ``TRAIN_count * (30/70)`` — no TEST or holdout contact of any kind.

Outputs: ``results/readiness_map.csv``, ``results/power_statement.csv``,
``results/per_cell_checks.parquet``, ``results/run_metadata.json``, and three
plots drawn from the aggregated per-cell summary only (no reloads).
"""
from __future__ import annotations

import json
import logging
import math
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from tqdm.auto import tqdm

# --------------------------------------------------------------------------- #
# Path setup
# --------------------------------------------------------------------------- #
EXP_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = EXP_DIR.parents[2]
SRC_DIR = PROJECT_ROOT / "python" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from xen.avwap import EVENT_SCHEMA, SLOW_MA, generate_avwap_events  # noqa: E402
from xen.bar_aggregator import aggregate_ohlc  # noqa: E402

# --------------------------------------------------------------------------- #
# Constants (all frozen by scope / D0 predeclarations — no tuning levers)
# --------------------------------------------------------------------------- #
DATA_DIR = PROJECT_ROOT / "data" / "timebars"
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"

INSTRUMENTS: tuple[str, ...] = (
    "BTCUSD", "EURUSD", "USTEC", "XAUUSD",
    "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD",
    "EURJPY", "GBPJPY", "AUDJPY",
    "US500", "US2000", "DE30", "JP225",
)
DOMAINS: dict[str, int] = {"1h": 60, "2h": 120, "4h": 240}
MIN_COVERAGE = 0.90          # P7 (2h) — same value as the established 1h/4h convention
ANALYSIS_FRACTION = 0.7      # first 70% = analysis slice (holdout fence)
TRAIN_FRACTION = 0.7         # first 70% of analysis slice = TRAIN (R1.3)
TEST_PROJECTION_FACTOR = 30.0 / 70.0   # predeclared projection rule — no TEST contact
EVENT_FLOOR = 30             # descriptive reporting floor (not a READY criterion)
RATIO_BAND = (0.45, 0.55)    # 2h/1h bar-count plausibility flag band (disclosure-only)
DROPPED_2H_CLEAN = 0.10      # frozen: 2h dropped fraction < 10% = clean PASS
DROPPED_2H_FAIL = 0.25       # frozen: 2h dropped fraction > 25% = construction FAIL
DROPPED_GATED_PERIOD = 120   # the dropped-fraction gate applies to the 2h domain only
SYSTEMATIC_INSTRUMENTS = 3   # frozen: same invariant violated on >= 3 instruments
TRUNCATED_INSTRUMENTS = ("DE30",)  # P8 disclosure, carried verbatim
DE30_POWER_NOTE = ("DE30 truncated history (ends 2026-01-16, ~5 months short): "
                   "projected counts optimistic by ~15-20% vs full-span instruments; "
                   "Track B power planning must use its realized span")
# Pre-sliced derivative exports that must never match the source-file glob.
EXCLUDED_FILE_MARKERS = ("analysis70", "analysis_slice", "first70")

CONSTRUCTION_CHECKS = ("ohlc_consistency", "strictly_increasing", "clock_alignment",
                       "coverage_bounds", "train_fence", "dropped_fraction")
INVARIANT_CHECKS = ("arm_before_trigger", "timestamps_in_train", "trigger_regime_side",
                    "targets_finite_correct_side", "trigger_time_monotone",
                    "no_null_event_columns", "regimes_well_formed")

LOGGER = logging.getLogger("EXP-043")


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class TrainSlice:
    """One instrument's TRAIN-only 1-minute slice plus boundary metadata."""

    instrument: str
    source_file: str
    total_rows_1m: int
    analysis_rows_1m: int
    train_rows_1m: int
    train_end_ts: datetime
    frame_1m: pl.DataFrame


# --------------------------------------------------------------------------- #
# I/O helpers
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


def load_train_slice(instrument: str) -> TrainSlice:
    """Load exactly the TRAIN 1-minute rows for one instrument (F01/R1.3 pattern).

    Boundary arithmetic on chronologically ordered file rows:
    ``analysis = floor(0.7 * total)``; ``train = floor(0.7 * analysis)``.
    Only the first ``train`` file-order rows are collected (row count from
    Parquet metadata; no full-file sort — source chronological order was
    validated by VAL-001 rev. 3 / VAL-003 and is re-asserted on the collected
    slice). TEST and holdout rows never enter the scan engine.
    """
    path = find_source_file(instrument)
    total = int(pl.scan_parquet(path).select(pl.len()).collect().item())
    analysis_rows = int(math.floor(ANALYSIS_FRACTION * total))
    train_rows = int(math.floor(TRAIN_FRACTION * analysis_rows))
    frame = (
        pl.scan_parquet(path)
        .select("Symbol", "OpenTime", "CloseTime", "Open", "High", "Low", "Close", "TickVolume")
        .head(train_rows)
        .collect()
    )
    if frame.height != train_rows:
        raise RuntimeError(f"{instrument}: collected {frame.height} != train_rows {train_rows}")
    close_time = frame.get_column("CloseTime")
    if not close_time.is_sorted() or close_time.n_unique() != frame.height:
        raise RuntimeError(
            f"{instrument}: TRAIN slice not strictly chronological — source file order "
            f"violates the VAL-validated premise; refusing to proceed."
        )
    return TrainSlice(
        instrument=instrument,
        source_file=path.name,
        total_rows_1m=total,
        analysis_rows_1m=analysis_rows,
        train_rows_1m=train_rows,
        train_end_ts=close_time.max(),
        frame_1m=frame,
    )


# --------------------------------------------------------------------------- #
# Pure checks — construction integrity
# --------------------------------------------------------------------------- #
def candidate_window_count(frame_1m: pl.DataFrame, period_minutes: int) -> int:
    """Number of distinct clock-grid windows the TRAIN source rows touch."""
    period_seconds = period_minutes * 60
    return int(
        frame_1m.select(
            ((pl.col("CloseTime").dt.epoch("s") - 1) // period_seconds).n_unique()
        ).item()
    )


def construction_checks(
    bars: pl.DataFrame,
    period_minutes: int,
    n_candidate_windows: int,
    train_end_ts: datetime,
) -> dict:
    """Exact construction-integrity predicates for one cell's domain bars.

    Returns per-check pass booleans plus the dropped-window fraction
    (denominator = candidate grid windows touched by TRAIN source rows).
    The dropped fraction is gated only on the 2h domain (frozen scope
    thresholds: <10% clean, 10-25% flagged disclosure, >25% FAIL); clock
    alignment is bucket membership — the aggregator's domain-bar CloseTime is
    the last observed source close, so coverage-tolerant windows may close
    before the grid boundary (a modulo predicate would false-fail them).
    """
    period_seconds = period_minutes * 60
    min_bars = max(2, math.ceil(MIN_COVERAGE * period_minutes))
    n = bars.height
    dropped_fraction = (
        1.0 - n / n_candidate_windows if n_candidate_windows > 0 else float("nan")
    )
    if n == 0:
        # Vacuous construction; the cell will be CONSTRUCTED_EMPTY downstream.
        return {f"construction_{c}": True for c in CONSTRUCTION_CHECKS} | {
            "n_domain_bars": 0, "n_candidate_windows": n_candidate_windows,
            "dropped_window_fraction": dropped_fraction,
            "dropped_fraction_flagged": False,
        }
    checks = bars.select(
        ohlc=((pl.col("High") >= pl.max_horizontal("Open", "Close"))
              & (pl.col("Low") <= pl.min_horizontal("Open", "Close"))).all(),
        strict=(pl.col("CloseTime").diff().dt.total_seconds() > 0).fill_null(True).all(),
        bucket_strict=(((pl.col("CloseTime").dt.epoch("s") - 1) // period_seconds)
                       .diff().fill_null(1) > 0).all(),
        open_in_window=(pl.col("OpenTime").dt.epoch("s")
                        >= ((pl.col("CloseTime").dt.epoch("s") - 1) // period_seconds)
                        * period_seconds).all(),
        close_in_window=(pl.col("CloseTime").dt.epoch("s")
                         <= (((pl.col("CloseTime").dt.epoch("s") - 1) // period_seconds) + 1)
                         * period_seconds).all(),
        coverage=((pl.col("SourceBars") >= min_bars)
                  & (pl.col("SourceBars") <= period_minutes)).all(),
        fence=(pl.col("CloseTime") <= pl.lit(train_end_ts)).all(),
    ).row(0, named=True)
    # Frozen 2h dropped-fraction gate (scope thresholds; other domains report only).
    gated = period_minutes == DROPPED_GATED_PERIOD and math.isfinite(dropped_fraction)
    dropped_fail = gated and dropped_fraction > DROPPED_2H_FAIL
    dropped_flag = gated and DROPPED_2H_CLEAN <= dropped_fraction <= DROPPED_2H_FAIL
    return {
        "construction_ohlc_consistency": bool(checks["ohlc"]),
        "construction_strictly_increasing": bool(checks["strict"]),
        "construction_clock_alignment": bool(checks["bucket_strict"] and checks["open_in_window"]
                                             and checks["close_in_window"]),
        "construction_coverage_bounds": bool(checks["coverage"]),
        "construction_train_fence": bool(checks["fence"]),
        "construction_dropped_fraction": not dropped_fail,
        "dropped_fraction_flagged": dropped_flag,
        "n_domain_bars": n,
        "n_candidate_windows": n_candidate_windows,
        "dropped_window_fraction": dropped_fraction,
    }


# --------------------------------------------------------------------------- #
# Pure checks — invariant battery
# --------------------------------------------------------------------------- #
def event_invariant_violations(events: pl.DataFrame, train_end_ts: datetime) -> dict[str, int]:
    """Violation counts for the event-table invariants (0 rows -> all zero)."""
    if events.height == 0:
        return {
            "arm_before_trigger": 0, "timestamps_in_train": 0, "trigger_regime_side": 0,
            "targets_finite_correct_side": 0, "trigger_time_monotone": 0,
            "no_null_event_columns": 0,
        }
    float_cols = [c for c, t in EVENT_SCHEMA.items() if t == pl.Float64]
    end = pl.lit(train_end_ts)
    d = pl.col("direction")
    counts = events.select(
        arm=(pl.col("armed_time") >= pl.col("trigger_time")).sum(),
        span=((pl.col("anchor_time") > end) | (pl.col("armed_time") > end)
              | (pl.col("trigger_time") > end)).sum(),
        side=(d * (pl.col("trigger_close") - pl.col("avwap_at_trigger")) < 0).sum(),
        targets=(
            (d * (pl.col("favorable_target_at_trigger") - pl.col("avwap_at_trigger")) <= 0)
            | (d * (pl.col("adverse_target_at_trigger") - pl.col("avwap_at_trigger")) >= 0)
            | pl.any_horizontal([~pl.col(c).is_finite() for c in float_cols])
        ).sum(),
        monotone=(pl.col("trigger_time").diff().dt.total_seconds() < 0).sum(),
        nulls=pl.sum_horizontal([
            (pl.col(c).is_null() | (pl.col(c).is_nan() if c in float_cols else pl.lit(False)))
            .sum() for c in events.columns
        ]),
    ).row(0, named=True)
    return {
        "arm_before_trigger": int(counts["arm"]),
        "timestamps_in_train": int(counts["span"]),
        "trigger_regime_side": int(counts["side"]),
        "targets_finite_correct_side": int(counts["targets"]),
        "trigger_time_monotone": int(counts["monotone"]),
        "no_null_event_columns": int(counts["nulls"]),
    }


def regime_invariant_violations(regimes: pl.DataFrame) -> int:
    """Violation count for regime well-formedness (segments, anchors, alternation)."""
    if regimes.height == 0:
        return 0
    counts = regimes.select(
        seg=(pl.col("regime_start_idx") > pl.col("regime_end_idx")).sum(),
        overlap=(pl.col("regime_start_idx").shift(-1) <= pl.col("regime_end_idx"))
        .fill_null(False).sum(),
        anchor=((pl.col("anchor_idx") > pl.col("confirm_idx"))
                | ~pl.col("anchor_price").is_finite()).sum(),
        alt=((pl.col("direction") * pl.col("direction").shift(1)) != -1)
        .fill_null(False).sum(),
        dir_valid=(~pl.col("direction").is_in([1, -1])).sum(),
    ).row(0, named=True)
    return int(sum(counts.values()))


# --------------------------------------------------------------------------- #
# Per-cell verdict
# --------------------------------------------------------------------------- #
def cell_verdict(record: dict) -> tuple[str, str]:
    """(verdict, failing_checks) per the predeclared interpretation guide."""
    if record["n_domain_bars"] < SLOW_MA:
        return "CONSTRUCTED_EMPTY", ""
    failing = [c for c in CONSTRUCTION_CHECKS if not record[f"construction_{c}"]]
    failing += [c for c in INVARIANT_CHECKS if record[f"violations_{c}"] > 0]
    if not record["determinism_pass"]:
        failing.append("determinism")
    return ("READY", "") if not failing else ("NOT_READY", ";".join(failing))


# --------------------------------------------------------------------------- #
# Orchestration — one instrument (3 cells x 2 passes)
# --------------------------------------------------------------------------- #
def generate_cell(ts: TrainSlice, domain: str, minutes: int) -> tuple[pl.DataFrame, object]:
    """Aggregate one cell's domain bars and run the frozen baseline generator."""
    bars = aggregate_ohlc(ts.frame_1m, period_minutes=minutes, min_coverage=MIN_COVERAGE)
    result = generate_avwap_events(
        bars.select("CloseTime", "Open", "High", "Low", "Close", "TickVolume"),
        instrument=ts.instrument, domain=domain,
    )
    return bars, result


def process_cell(ts: TrainSlice, domain: str, minutes: int) -> dict:
    """Full per-cell record: construction, invariants, determinism, rates."""
    bars, result = generate_cell(ts, domain, minutes)
    record: dict = {"instrument": ts.instrument, "domain": domain}
    record |= construction_checks(
        bars, minutes, candidate_window_count(ts.frame_1m, minutes), ts.train_end_ts
    )
    ev_viol = event_invariant_violations(result.events, ts.train_end_ts)
    record |= {f"violations_{k}": v for k, v in ev_viol.items()}
    record["violations_regimes_well_formed"] = regime_invariant_violations(result.regimes)

    # Determinism: full second regeneration, frame-identical comparison.
    bars2, result2 = generate_cell(ts, domain, minutes)
    record["determinism_pass"] = bool(
        bars.equals(bars2)
        and result.events.equals(result2.events)
        and result.regimes.equals(result2.regimes)
        and result.n_domain_bars == result2.n_domain_bars
        and result.analysis_end == result2.analysis_end
    )

    # Event rates / power reporting (denominator = the cell's TRAIN domain bars;
    # a 0-event cell reports rate 0.0 with the denominator disclosed).
    n_events = result.events.height
    n_bars = record["n_domain_bars"]
    record |= {
        "train_events": n_events,
        "events_per_1k_train_bars": 1000.0 * n_events / n_bars if n_bars > 0 else float("nan"),
        "projected_test_events_heuristic": n_events * TEST_PROJECTION_FACTOR,
        "below_30_event_floor": n_events < EVENT_FLOOR,
        "bull_events": int((result.events.get_column("direction") == 1).sum()) if n_events else 0,
        "bear_events": int((result.events.get_column("direction") == -1).sum()) if n_events else 0,
        "n_regimes": result.regimes.height,
        "de30_truncated": ts.instrument in TRUNCATED_INSTRUMENTS,
        "power_note": DE30_POWER_NOTE if ts.instrument in TRUNCATED_INSTRUMENTS else "",
    }
    record["verdict"], record["failing_checks"] = cell_verdict(record)
    return record


def process_instrument(ts: TrainSlice, progress: tqdm) -> list[dict]:
    """All three domain cells for one instrument, with the 2h/1h ratio flag."""
    records = []
    for domain, minutes in DOMAINS.items():
        records.append(process_cell(ts, domain, minutes))
        progress.update(1)
    by_domain = {r["domain"]: r for r in records}
    n_1h, n_2h = by_domain["1h"]["n_domain_bars"], by_domain["2h"]["n_domain_bars"]
    ratio = n_2h / n_1h if n_1h > 0 else float("nan")
    flagged = not (RATIO_BAND[0] <= ratio <= RATIO_BAND[1]) if n_1h > 0 else True
    for r in records:
        r["bar_ratio_2h_over_1h"] = ratio
        r["bar_ratio_flagged"] = flagged
    return records


# --------------------------------------------------------------------------- #
# Plotting (inputs: the 51-row per-cell summary only — no reloads)
# --------------------------------------------------------------------------- #
def plot_event_count_heatmap(summary: pl.DataFrame, path: Path) -> None:
    """17x3 TRAIN event-count heatmap, annotated with counts."""
    domains = list(DOMAINS)
    matrix = np.full((len(INSTRUMENTS), len(domains)), np.nan)
    for row in summary.to_dicts():
        matrix[INSTRUMENTS.index(row["instrument"]), domains.index(row["domain"])] = (
            row["train_events"]
        )
    fig, ax = plt.subplots(figsize=(6, 10))
    im = ax.imshow(matrix, aspect="auto", cmap="viridis")
    ax.set_xticks(range(len(domains)), domains)
    labels = [f"{i} (truncated)" if i in TRUNCATED_INSTRUMENTS else i for i in INSTRUMENTS]
    ax.set_yticks(range(len(INSTRUMENTS)), labels, fontsize=7)
    for i in range(len(INSTRUMENTS)):
        for j in range(len(domains)):
            ax.text(j, i, f"{int(matrix[i, j])}", ha="center", va="center",
                    color="white", fontsize=7)
    ax.set_title("EXP-043 TRAIN event count per cell (baseline entry)")
    fig.colorbar(im, ax=ax, label="TRAIN events")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_event_rates_by_domain(summary: pl.DataFrame, path: Path) -> None:
    """Events per 1,000 TRAIN domain bars: per-instrument points by domain."""
    fig, ax = plt.subplots(figsize=(8, 5))
    domains = list(DOMAINS)
    rng = np.random.default_rng(43)  # fixed seed — jitter only, no analysis effect
    for j, domain in enumerate(domains):
        sub = summary.filter(pl.col("domain") == domain)
        x = j + rng.uniform(-0.12, 0.12, sub.height)
        ax.scatter(x, sub["events_per_1k_train_bars"], s=18, alpha=0.8)
        for xi, yi, inst in zip(x, sub["events_per_1k_train_bars"], sub["instrument"]):
            label = f"{inst} (truncated)" if inst in TRUNCATED_INSTRUMENTS else inst
            ax.annotate(label, (xi, yi), fontsize=4.5, alpha=0.7)
    ax.set_xticks(range(len(domains)), domains)
    ax.set_ylabel("events per 1,000 TRAIN domain bars")
    ax.set_title("EXP-043 TRAIN event rate by domain (17 instruments)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_2h_dropped_fraction(summary: pl.DataFrame, path: Path) -> None:
    """2h dropped-window fraction per instrument (first-ever 2h construction)."""
    sub = summary.filter(pl.col("domain") == "2h")
    by_inst = {r["instrument"]: r["dropped_window_fraction"] for r in sub.to_dicts()}
    values = [by_inst.get(i, float("nan")) for i in INSTRUMENTS]
    labels = [f"{i}\n(truncated)" if i in TRUNCATED_INSTRUMENTS else i for i in INSTRUMENTS]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.bar(range(len(INSTRUMENTS)), values, color="steelblue")
    ax.set_xticks(range(len(INSTRUMENTS)), labels, fontsize=6, rotation=45)
    ax.set_ylabel("dropped-window fraction")
    ax.set_title(f"EXP-043 2h dropped-window fraction (min_coverage={MIN_COVERAGE})")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> None:
    """Run the 51-cell readiness battery end to end (TRAIN-only)."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    records: list[dict] = []
    boundaries: dict[str, dict] = {}
    n_cells = len(INSTRUMENTS) * len(DOMAINS)
    with tqdm(total=n_cells, desc="EXP-043 readiness (51 cells)") as progress:
        for inst in INSTRUMENTS:
            ts = load_train_slice(inst)
            boundaries[inst] = {
                "source_file": ts.source_file, "total_rows_1m": ts.total_rows_1m,
                "analysis_rows_1m": ts.analysis_rows_1m, "train_rows_1m": ts.train_rows_1m,
                "train_end_ts": str(ts.train_end_ts),
            }
            records.extend(process_instrument(ts, progress))
            del ts  # drop the 1m frame before the next instrument

    summary = pl.DataFrame(records).sort(["instrument", "domain"])
    summary.write_parquet(RESULTS_DIR / "per_cell_checks.parquet")
    summary.select(
        "instrument", "domain", "verdict", "failing_checks",
        "n_domain_bars", "determinism_pass", "de30_truncated",
    ).write_csv(RESULTS_DIR / "readiness_map.csv")
    summary.select(
        "instrument", "domain", "verdict", "train_events", "n_domain_bars",
        "events_per_1k_train_bars", "projected_test_events_heuristic",
        "below_30_event_floor", "bull_events", "bear_events", "n_regimes",
        "dropped_window_fraction", "dropped_fraction_flagged",
        "bar_ratio_2h_over_1h", "bar_ratio_flagged", "de30_truncated", "power_note",
    ).write_csv(RESULTS_DIR / "power_statement.csv")

    verdict_counts = {
        v: int((summary.get_column("verdict") == v).sum())
        for v in ("READY", "NOT_READY", "CONSTRUCTED_EMPTY")
    }
    determinism_failures = int((~summary.get_column("determinism_pass")).sum())
    # Substrate-level alert (frozen scope threshold): non-determinism anywhere,
    # or the same invariant violated on >= SYSTEMATIC_INSTRUMENTS instruments.
    recurring = [
        c for c in INVARIANT_CHECKS
        if summary.filter(pl.col(f"violations_{c}") > 0).get_column("instrument").n_unique()
        >= SYSTEMATIC_INSTRUMENTS
    ]
    substrate_alert = determinism_failures > 0 or bool(recurring)

    metadata = {
        "experiment": "EXP-043",
        "verdict": "READINESS_DELIVERED",
        "substrate_alert": substrate_alert,
        "substrate_alert_detail": {
            "determinism_failures": determinism_failures,
            "recurring_invariant_violations": recurring,
            "systematic_instrument_threshold": SYSTEMATIC_INSTRUMENTS,
        },
        "cell_verdict_counts": verdict_counts,
        "entry_rule": "frozen baseline arm/trigger at the AVWAP line "
                      "(generate_avwap_events defaults; Phases 004-010)",
        "band_multiplier": 1.0, "arm_at_adverse_band": False,
        "domains": DOMAINS, "min_coverage": MIN_COVERAGE,
        "analysis_fraction": ANALYSIS_FRACTION, "train_fraction": TRAIN_FRACTION,
        "test_projection_rule": "projected_test_events_heuristic = train_events * (30/70); "
                                "uniformity HEURISTIC, not an estimate — regime-dependent "
                                "events do not distribute uniformly, realized TEST counts "
                                "depend on the TEST stratum's regime distribution; "
                                "no TEST data contact, including row counts",
        "timestamp_convention": "domain-bar CloseTime = last observed source close within "
                                "its clock-grid window; coverage-tolerant windows may close "
                                "before the grid boundary",
        "frozen_thresholds": {
            "dropped_2h_clean": DROPPED_2H_CLEAN, "dropped_2h_fail": DROPPED_2H_FAIL,
            "systematic_instruments": SYSTEMATIC_INSTRUMENTS,
            "bar_ratio_band_disclosure_only": list(RATIO_BAND),
        },
        "event_floor_descriptive": EVENT_FLOOR,
        "boundaries": boundaries,
        "de30_disclosure": "DE30 coverage truncated (history ends 2026-01-16); "
                           "boundaries derive from its own realized timeline (D0 P8).",
    }
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(metadata, indent=2))

    plot_event_count_heatmap(summary, PLOTS_DIR / "train_event_count_heatmap.png")
    plot_event_rates_by_domain(summary, PLOTS_DIR / "event_rate_by_domain.png")
    plot_2h_dropped_fraction(summary, PLOTS_DIR / "dropped_fraction_2h.png")

    LOGGER.info("cell verdicts: %s", verdict_counts)
    if substrate_alert:
        LOGGER.warning("SUBSTRATE ALERT: determinism failures=%d, recurring violations=%s "
                       "— Track A halts pending a fix cycle.", determinism_failures, recurring)
    not_ready = summary.filter(pl.col("verdict") == "NOT_READY")
    for row in not_ready.to_dicts():
        LOGGER.info("NOT_READY %s-%s: %s", row["instrument"], row["domain"],
                    row["failing_checks"])
    LOGGER.info("outputs written under %s and %s", RESULTS_DIR, PLOTS_DIR)


if __name__ == "__main__":
    main()
