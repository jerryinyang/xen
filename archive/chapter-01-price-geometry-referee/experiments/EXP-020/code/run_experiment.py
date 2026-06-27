"""Experiment EXP-020: AVWAP Event-Substrate Readiness.

Implements the approved analysis plan (analysis-plan.md) for the Phase 004
CF-AVWAP-001 first branch. EXP-020 is a readiness / substrate experiment: it
verifies that the frozen AVWAP state machine is deterministic and
look-ahead-safe, and measures bounce-event coverage. It does NOT compute returns,
P&L, or run the frozen qualification suite.

Pipeline:
    1. Holdout-safe load (first-70% analysis slice) + 5m/1h/4h domain bars,
       reusing the EXP-004/009/VAL-002 domain convention.
    2. Sequential AVWAP generation per instrument/domain via ``xen.avwap``.
    3. Invariant + determinism (replay) checks.
    4. Event-coverage readiness classification.
    5. Four bounded visualisations.

The final 30% global holdout is never loaded (``load_analysis_data`` slices the
first 70% in a lazy plan before collection) and every emitted event is fenced to
the analysis-set end.

Run:
    cd <project-root> && python python/experiments/EXP-020/code/run_experiment.py
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402  (backend must be set first)
import numpy as np  # noqa: E402
import polars as pl  # noqa: E402
from tqdm.auto import tqdm  # noqa: E402

from xen.avwap import (  # noqa: E402
    BAND_MULTIPLIER,
    FAST_MA,
    SLOW_MA,
    VOLUME_EXPONENT,
    AvwapResult,
    compute_band_trace,
    generate_avwap_events,
)
from xen.referee_calibration import (  # noqa: E402
    DOMAIN_SPECS,
    AnalysisData,
    build_domain_frames,
    list_timebar_files,
    load_analysis_data,
)


LOGGER = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-020"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = PROJECT_ROOT / "data"
EXPERIMENT_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"

DOMAINS: tuple[str, ...] = ("5m", "1h", "4h")

# Readiness thresholds (scope Success / Failure Criteria).
MIN_TOTAL_EVENTS = 30
MIN_DIRECTION_EVENTS = 8
READY_MIN_INSTRUMENTS = 3

# Determinism + plotting bounds.
HASH_FLOAT_DECIMALS = 10
TRACE_MAX_BARS = 400

# Registry provenance (recorded in run_metadata.json).
REGISTRY_REFS = {
    "candidate_family": "CF-AVWAP-001",
    "multiplicity_registry": "docs/signal-registry/multiplicity-registry.md",
    "family_spec": "docs/signal-registry/candidate-families/avwap.md",
    "checkpoint": "docs/experiments-docs/checkpoints/2026-06-07-004-avwap-signal-exploration",
}

EVENT_SORT = ["instrument", "domain", "regime_id", "trigger_idx"]
REGIME_SORT = ["instrument", "domain", "regime_id"]


# --------------------------------------------------------------------------- #
# I/O helpers
# --------------------------------------------------------------------------- #
def configure_logging() -> None:
    """Configure concise INFO logging for the manual run."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def ensure_output_dirs() -> None:
    """Create ``results/`` and ``plots/`` (orchestration-time only)."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write result dict rows to ``path`` as CSV."""
    pl.DataFrame(rows).write_csv(path)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write a JSON payload with stable key ordering."""
    path.write_text(json.dumps(payload, indent=2, default=str))


# --------------------------------------------------------------------------- #
# Pure helpers: hashing, invariants, coverage, readiness, status
# --------------------------------------------------------------------------- #
def canonical_hash(frame: pl.DataFrame) -> str:
    """Order-and-precision-canonical SHA-256 of a result frame.

    Floats are rounded and rows sorted before serialisation so the hash depends
    only on content, supporting the deterministic-replay check.
    """
    if frame.height == 0:
        return hashlib.sha256(("EMPTY:" + ",".join(frame.columns)).encode()).hexdigest()
    float_cols = [c for c, t in zip(frame.columns, frame.dtypes) if t == pl.Float64]
    out = frame
    if float_cols:
        out = out.with_columns([pl.col(c).round(HASH_FLOAT_DECIMALS) for c in float_cols])
    sort_cols = [c for c in EVENT_SORT + ["confirm_idx"] if c in out.columns]
    out = out.sort(sort_cols)
    return hashlib.sha256(out.write_csv().encode()).hexdigest()


def _float_match(left: float, right: float) -> bool:
    """Return true when two generated floating-point values are equivalent."""
    return bool(np.isclose(float(left), float(right), rtol=1e-10, atol=1e-10))


def state_machine_invariant_rows(
    res: AvwapResult,
    frame: pl.DataFrame,
) -> list[dict[str, Any]]:
    """Independent anchor and arm/trigger checks against the source domain frame."""
    rows: list[dict[str, Any]] = []

    def add(name: str, violations: int, units: int) -> None:
        rows.append(
            {
                "instrument": res.instrument,
                "domain": res.domain,
                "check_name": name,
                "n_units": units,
                "n_violations": int(violations),
                "passed": int(violations) == 0,
            }
        )

    regimes = res.regimes.sort("regime_id")
    events = res.events.sort(["regime_id", "bounce_index_in_regime"])
    if regimes.is_empty():
        for name in (
            "anchor_selection",
            "event_timestamp_index",
            "arming_condition",
            "trigger_condition",
            "event_value_consistency",
            "rearm_sequence",
        ):
            add(name, 0, 0)
        return rows

    low = frame.get_column("Low").to_numpy().astype(float)
    high = frame.get_column("High").to_numpy().astype(float)
    close = frame.get_column("Close").to_numpy().astype(float)
    times = frame.get_column("CloseTime").to_list()
    time_to_idx = {ts: idx for idx, ts in enumerate(times)}

    anchor_bad = 0
    timestamp_bad = 0
    arming_bad = 0
    trigger_bad = 0
    value_bad = 0
    rearm_bad = 0
    event_units = events.height

    previous_confirm_idx = 0
    for regime in regimes.iter_rows(named=True):
        confirm_idx = int(regime["confirm_idx"])
        anchor_idx = int(regime["anchor_idx"])
        direction = int(regime["direction"])
        regime_events = events.filter(pl.col("regime_id") == regime["regime_id"])
        if not (0 <= confirm_idx < frame.height and 0 <= anchor_idx < frame.height):
            anchor_bad += 1
            timestamp_bad += 1 + regime_events.height
            arming_bad += regime_events.height
            trigger_bad += regime_events.height
            value_bad += regime_events.height
            rearm_bad += max(regime_events.height - 1, 0)
            continue

        start_idx = previous_confirm_idx
        window = slice(start_idx, confirm_idx + 1)

        if not (start_idx <= anchor_idx <= confirm_idx):
            anchor_bad += 1
        elif direction == 1:
            expected = float(np.min(low[window]))
            anchor_bad += int(
                not (
                    _float_match(low[anchor_idx], expected)
                    and _float_match(regime["anchor_price"], expected)
                )
            )
        elif direction == -1:
            expected = float(np.max(high[window]))
            anchor_bad += int(
                not (
                    _float_match(high[anchor_idx], expected)
                    and _float_match(regime["anchor_price"], expected)
                )
            )
        else:
            anchor_bad += 1

        timestamp_bad += int(regime["anchor_time"] != times[anchor_idx])

        if not regime_events.is_empty():
            valid_events = regime_events.filter(
                (pl.col("trigger_idx") >= anchor_idx)
                & (pl.col("trigger_idx") < frame.height)
            )
            invalid_trigger_idx = regime_events.height - valid_events.height
            if invalid_trigger_idx:
                timestamp_bad += invalid_trigger_idx
                arming_bad += invalid_trigger_idx
                trigger_bad += invalid_trigger_idx
                value_bad += invalid_trigger_idx
            if valid_events.is_empty():
                previous_confirm_idx = confirm_idx
                continue

            max_trigger_idx = int(valid_events.get_column("trigger_idx").max())
            trace = compute_band_trace(frame, anchor_idx, max_trigger_idx)
            previous_trigger_idx = -1
            for event in valid_events.iter_rows(named=True):
                armed_idx = time_to_idx.get(event["armed_time"])
                trigger_idx = int(event["trigger_idx"])
                trigger_time_idx = time_to_idx.get(event["trigger_time"])
                if (
                    armed_idx is None
                    or trigger_time_idx != trigger_idx
                    or not (anchor_idx <= armed_idx < trigger_idx)
                    or armed_idx <= confirm_idx
                ):
                    timestamp_bad += 1
                    continue

                armed_avwap = trace["avwap"][armed_idx - anchor_idx]
                trigger_avwap = trace["avwap"][trigger_idx - anchor_idx]
                if direction == 1:
                    arming_bad += int(not (close[armed_idx] < armed_avwap))
                    trigger_bad += int(not (close[trigger_idx] > trigger_avwap))
                else:
                    arming_bad += int(not (close[armed_idx] > armed_avwap))
                    trigger_bad += int(not (close[trigger_idx] < trigger_avwap))

                trigger_offset = trigger_idx - anchor_idx
                value_bad += int(
                    not (
                        _float_match(event["avwap_at_trigger"], trace["avwap"][trigger_offset])
                        and _float_match(event["upper_band_at_trigger"], trace["upper"][trigger_offset])
                        and _float_match(event["lower_band_at_trigger"], trace["lower"][trigger_offset])
                    )
                )
                rearm_bad += int(previous_trigger_idx >= 0 and armed_idx <= previous_trigger_idx)
                previous_trigger_idx = trigger_idx

        previous_confirm_idx = confirm_idx

    add("anchor_selection", anchor_bad, regimes.height)
    add("event_timestamp_index", timestamp_bad, regimes.height + event_units)
    add("arming_condition", arming_bad, event_units)
    add("trigger_condition", trigger_bad, event_units)
    add("event_value_consistency", value_bad, event_units)
    add("rearm_sequence", rearm_bad, event_units)
    return rows


def cell_invariant_rows(
    res: AvwapResult,
    frame: pl.DataFrame,
    fence_ts: Any,
) -> list[dict[str, Any]]:
    """Compute temporal/anchor/arming/weight/holdout invariant checks for a cell."""
    e = res.events
    n = e.height
    rows: list[dict[str, Any]] = []

    def add(name: str, violations: int, units: int) -> None:
        rows.append(
            {
                "instrument": res.instrument,
                "domain": res.domain,
                "check_name": name,
                "n_units": units,
                "n_violations": int(violations),
                "passed": int(violations) == 0,
            }
        )

    nulls = frame.get_column("TickVolume").null_count()
    negs = frame.filter(pl.col("TickVolume") < 0).height
    add("weight_nonneg", nulls + negs, res.n_domain_bars)
    rows.extend(state_machine_invariant_rows(res, frame))

    event_checks = (
        "temporal_order",
        "holdout_fence",
        "anchor_age_positive",
        "direction_valid",
        "band_nonneg",
        "target_consistency",
        "pyramid_flag",
        "finite_values",
        "rearm_monotonic",
    )
    if n == 0:
        for name in event_checks:
            add(name, 0, 0)
        return rows

    add(
        "temporal_order",
        e.filter(
            ~(
                (pl.col("anchor_time") <= pl.col("armed_time"))
                & (pl.col("armed_time") < pl.col("trigger_time"))
            )
        ).height,
        n,
    )
    add("holdout_fence", e.filter(pl.col("trigger_time") > fence_ts).height, n)
    add("anchor_age_positive", e.filter(pl.col("anchor_age_bars") <= 0).height, n)
    add("direction_valid", e.filter(~pl.col("direction").is_in([-1, 1])).height, n)
    add("band_nonneg", e.filter(pl.col("band_spread_at_trigger") < 0).height, n)

    target_bad = e.filter(
        (
            (pl.col("direction") == 1)
            & (
                (pl.col("favorable_target_at_trigger") != pl.col("upper_band_at_trigger"))
                | (pl.col("adverse_target_at_trigger") != pl.col("lower_band_at_trigger"))
            )
        )
        | (
            (pl.col("direction") == -1)
            & (
                (pl.col("favorable_target_at_trigger") != pl.col("lower_band_at_trigger"))
                | (pl.col("adverse_target_at_trigger") != pl.col("upper_band_at_trigger"))
            )
        )
    ).height
    add("target_consistency", target_bad, n)
    add(
        "pyramid_flag",
        e.filter(pl.col("is_pyramid_bounce") != (pl.col("bounce_index_in_regime") > 1)).height,
        n,
    )
    add(
        "finite_values",
        e.filter(
            pl.col("avwap_at_trigger").is_nan()
            | pl.col("band_spread_at_trigger").is_nan()
            | pl.col("trigger_close").is_nan()
        ).height,
        n,
    )

    grouped = e.group_by("regime_id").agg(
        pl.col("bounce_index_in_regime").min().alias("mn"),
        pl.col("bounce_index_in_regime").max().alias("mx"),
        pl.len().alias("cnt"),
        pl.col("bounce_index_in_regime").n_unique().alias("uniq"),
    )
    rearm_bad = grouped.filter(
        ~(
            (pl.col("mn") == 1)
            & (pl.col("mx") == pl.col("cnt"))
            & (pl.col("uniq") == pl.col("cnt"))
        )
    ).height
    add("rearm_monotonic", rearm_bad, grouped.height)
    return rows


def coverage_row(res: AvwapResult) -> dict[str, Any]:
    """Per-cell event-coverage summary."""
    e = res.events
    r = res.regimes
    total = e.height
    bull = e.filter(pl.col("direction") == 1).height
    bear = e.filter(pl.col("direction") == -1).height
    bars = res.n_domain_bars
    density = (total / bars * 10000.0) if bars > 0 else None
    median_regime_len = float(r.get_column("regime_length_bars").median()) if r.height else None
    median_anchor_age = float(e.get_column("anchor_age_bars").median()) if total else None
    reportable = total >= MIN_TOTAL_EVENTS and bull >= MIN_DIRECTION_EVENTS and bear >= MIN_DIRECTION_EVENTS
    return {
        "instrument": res.instrument,
        "domain": res.domain,
        "domain_bars": bars,
        "n_regimes": r.height,
        "total_events": total,
        "bull_events": bull,
        "bear_events": bear,
        "event_density_per_10k_bars": density,
        "median_regime_length_bars": median_regime_len,
        "median_anchor_age_bars_at_event": median_anchor_age,
        "reportable": reportable,
    }


def direction_balance_row(res: AvwapResult) -> dict[str, Any]:
    """Per-cell direction-balance summary; zero-denominator fractions are null."""
    e = res.events
    total = e.height
    bull = e.filter(pl.col("direction") == 1).height
    bear = e.filter(pl.col("direction") == -1).height
    return {
        "instrument": res.instrument,
        "domain": res.domain,
        "total_events": total,
        "bull_events": bull,
        "bear_events": bear,
        "bull_fraction": (bull / total) if total > 0 else None,
        "bear_fraction": (bear / total) if total > 0 else None,
        "min_direction_count": min(bull, bear),
        "direction_reportable": (
            total >= MIN_TOTAL_EVENTS
            and min(bull, bear) >= MIN_DIRECTION_EVENTS
        ),
    }


def readiness_rows(coverage_lut: dict[tuple[str, str], dict]) -> dict[str, dict[str, Any]]:
    """Classify ready domains (>= READY_MIN_INSTRUMENTS reportable instruments)."""
    instruments = sorted({inst for inst, _ in coverage_lut})
    out: dict[str, dict[str, Any]] = {}
    for d in DOMAINS:
        reportable = [inst for inst in instruments if coverage_lut[(inst, d)]["reportable"]]
        out[d] = {
            "domain": d,
            "n_instruments": len(instruments),
            "reportable_instruments": len(reportable),
            "reportable_list": ",".join(reportable),
            "ready": len(reportable) >= READY_MIN_INSTRUMENTS,
        }
    return out


def decide_status(
    readiness: dict[str, dict[str, Any]],
    coverage_lut: dict[tuple[str, str], dict],
    invariants_ok: bool,
    determinism_ok: bool,
    holdout_violations: int,
) -> tuple[str, list[str]]:
    """Map invariant/determinism/coverage results to the scope outcome label."""
    ready_domains = [d for d in DOMAINS if readiness[d]["ready"]]
    if not invariants_ok or not determinism_ok or holdout_violations > 0:
        return "REFUTED", ready_domains
    if len(ready_domains) == 3:
        return "SUPPORTED_FULL", ready_domains
    if len(ready_domains) >= 1:
        return "SUPPORTED_NARROW", ready_domains
    any_two = any(readiness[d]["reportable_instruments"] == 2 for d in DOMAINS)
    severe_imbalance = any(
        c["total_events"] >= MIN_TOTAL_EVENTS
        and min(c["bull_events"], c["bear_events"]) < MIN_DIRECTION_EVENTS
        for c in coverage_lut.values()
    )
    nonzero_unreportable = any(
        0 < c["total_events"] and not c["reportable"] for c in coverage_lut.values()
    )
    if any_two or severe_imbalance or nonzero_unreportable:
        return "INCONCLUSIVE", ready_domains
    return "REFUTED", ready_domains


# --------------------------------------------------------------------------- #
# Plotting helpers (bounded inputs only)
# --------------------------------------------------------------------------- #
def plot_event_density_heatmap(
    coverage_lut: dict[tuple[str, str], dict],
    instruments: list[str],
    save_path: Path,
) -> None:
    """Heatmap of bounce-event density (annotated with total counts)."""
    mat = np.full((len(instruments), len(DOMAINS)), np.nan)
    totals = np.zeros((len(instruments), len(DOMAINS)), dtype=int)
    for i, inst in enumerate(instruments):
        for j, d in enumerate(DOMAINS):
            c = coverage_lut[(inst, d)]
            dens = c["event_density_per_10k_bars"]
            mat[i, j] = dens if dens is not None else np.nan
            totals[i, j] = c["total_events"]
    fig, ax = plt.subplots(figsize=(7, 5))
    im = ax.imshow(mat, cmap="viridis", aspect="auto")
    ax.set_xticks(range(len(DOMAINS)))
    ax.set_xticklabels(DOMAINS)
    ax.set_yticks(range(len(instruments)))
    ax.set_yticklabels(instruments)
    for i in range(len(instruments)):
        for j in range(len(DOMAINS)):
            dens = mat[i, j]
            txt = f"{totals[i, j]}\n{dens:.1f}/10k" if not np.isnan(dens) else f"{totals[i, j]}\n—"
            ax.text(j, i, txt, ha="center", va="center", color="white", fontsize=8)
    fig.colorbar(im, ax=ax, label="bounce events per 10k domain bars")
    ax.set_title("EXP-020 AVWAP bounce-event density")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_direction_balance(
    direction_lut: dict[tuple[str, str], dict],
    instruments: list[str],
    save_path: Path,
) -> None:
    """Grouped bull/bear bounce counts per instrument, one subplot per domain."""
    fig, axes = plt.subplots(1, len(DOMAINS), figsize=(4 * len(DOMAINS), 4))
    if len(DOMAINS) == 1:
        axes = [axes]
    x = np.arange(len(instruments))
    width = 0.38
    for j, d in enumerate(DOMAINS):
        bull = [direction_lut[(inst, d)]["bull_events"] for inst in instruments]
        bear = [direction_lut[(inst, d)]["bear_events"] for inst in instruments]
        ax = axes[j]
        ax.bar(x - width / 2, bull, width, label="bull", color="#2c7fb8")
        ax.bar(x + width / 2, bear, width, label="bear", color="#de2d26")
        ax.axhline(MIN_DIRECTION_EVENTS, ls="--", lw=0.8, color="grey")
        ax.set_xticks(x)
        ax.set_xticklabels(instruments, rotation=45, ha="right", fontsize=8)
        ax.set_title(d)
        ax.set_ylabel("events")
        if j == 0:
            ax.legend(fontsize=8)
    fig.suptitle(f"EXP-020 direction balance (dashed = {MIN_DIRECTION_EVENTS}-event floor)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_regime_anchor_distributions(
    regime_lengths: np.ndarray,
    anchor_ages: np.ndarray,
    save_path: Path,
) -> None:
    """Histograms of regime length and anchor age at bounce events."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    if regime_lengths.size > 0:
        axes[0].hist(regime_lengths, bins=50, color="#3182bd")
    axes[0].set_title(f"Regime length (bars), n={regime_lengths.size}")
    axes[0].set_xlabel("bars")
    axes[0].set_ylabel("regimes")
    axes[0].set_yscale("log")
    if anchor_ages.size > 0:
        axes[1].hist(anchor_ages, bins=50, color="#31a354")
    axes[1].set_title(f"Anchor age at bounce (bars), n={anchor_ages.size}")
    axes[1].set_xlabel("bars")
    axes[1].set_ylabel("events")
    axes[1].set_yscale("log")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_avwap_sample_overlay(window: dict[str, Any] | None, save_path: Path) -> None:
    """AVWAP/band/anchor/bounce overlay for one bounded sample window."""
    fig, ax = plt.subplots(figsize=(11, 5))
    if window is None:
        ax.text(0.5, 0.5, "No AVWAP bounce events available for overlay", ha="center", va="center")
        ax.set_axis_off()
    else:
        trace = window["trace"]
        t = trace["time"]
        ax.plot(t, trace["close"], color="black", lw=0.9, label="Close")
        ax.plot(t, trace["avwap"], color="#1f78b4", lw=1.2, label="AVWAP")
        ax.plot(t, trace["upper"], color="#999999", lw=0.8, ls="--", label="Upper band")
        ax.plot(t, trace["lower"], color="#999999", lw=0.8, ls="--", label="Lower band")
        ax.scatter(
            [t[0]], [window["anchor_price"]], marker="o", color="green", zorder=5, label="Anchor"
        )
        triggers = window["triggers"]
        if triggers:
            ax.scatter(
                [x[0] for x in triggers],
                [x[1] for x in triggers],
                marker="^",
                color="red",
                zorder=6,
                label="Bounce trigger",
            )
        ax.legend(fontsize=8)
        ax.set_ylabel("price")
    ax.set_title(f"EXP-020 AVWAP sample overlay — {window['label'] if window else 'none'}")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Sample-window selection (bounded, deterministic)
# --------------------------------------------------------------------------- #
def select_sample_window(
    results: dict[tuple[str, str], AvwapResult],
    cell_frames: dict[tuple[str, str], pl.DataFrame],
    coverage_lut: dict[tuple[str, str], dict],
    readiness: dict[str, dict[str, Any]],
    instruments: list[str],
) -> dict[str, Any] | None:
    """Pick a bounded, reproducible AVWAP window for the overlay plot."""
    ready_domains = [d for d in DOMAINS if readiness[d]["ready"]]
    cell = _pick_overlay_cell(coverage_lut, instruments, ready_domains)
    if cell is None:
        return None
    res = results[cell]
    frame = cell_frames[cell]
    n_bars = frame.height
    cand = (
        res.events.group_by("regime_id")
        .agg(pl.col("trigger_idx").max().alias("last_t"))
        .sort("regime_id")
    )
    anchor_by_regime = {
        row["regime_id"]: row["anchor_idx"]
        for row in res.regimes.select("regime_id", "anchor_idx").iter_rows(named=True)
    }
    chosen_rid, anchor_idx, end_idx = None, None, None
    for row in cand.iter_rows(named=True):
        rid = row["regime_id"]
        a_idx = anchor_by_regime[rid]
        if row["last_t"] - a_idx <= TRACE_MAX_BARS:
            chosen_rid, anchor_idx, end_idx = rid, a_idx, min(row["last_t"] + 5, n_bars - 1)
            break
    if chosen_rid is None:
        first = cand.row(0, named=True)
        chosen_rid = first["regime_id"]
        anchor_idx = anchor_by_regime[chosen_rid]
        end_idx = min(anchor_idx + TRACE_MAX_BARS, n_bars - 1)
    anchor_price = float(
        res.regimes.filter(pl.col("regime_id") == chosen_rid).get_column("anchor_price")[0]
    )
    trace = compute_band_trace(frame, anchor_idx, end_idx)
    window_ev = res.events.filter(
        (pl.col("regime_id") == chosen_rid) & (pl.col("trigger_idx") <= end_idx)
    )
    triggers = list(
        zip(window_ev.get_column("trigger_time").to_list(), window_ev.get_column("trigger_close").to_list())
    )
    return {
        "cell": cell,
        "regime_id": chosen_rid,
        "anchor_idx": anchor_idx,
        "end_idx": end_idx,
        "anchor_price": anchor_price,
        "trace": trace,
        "triggers": triggers,
        "label": f"{cell[0]} {cell[1]} — regime {chosen_rid} (bars {anchor_idx}-{end_idx})",
    }


def _pick_overlay_cell(
    coverage_lut: dict[tuple[str, str], dict],
    instruments: list[str],
    ready_domains: list[str],
) -> tuple[str, str] | None:
    """Prefer a reportable cell in a ready domain; else any cell with events."""
    for d in ready_domains:
        for inst in instruments:
            if coverage_lut[(inst, d)]["reportable"]:
                return (inst, d)
    for d in DOMAINS:
        for inst in instruments:
            if coverage_lut[(inst, d)]["total_events"] > 0:
                return (inst, d)
    return None


# --------------------------------------------------------------------------- #
# Generation orchestration
# --------------------------------------------------------------------------- #
def generate_all_cells(
    cell_frames: dict[tuple[str, str], pl.DataFrame],
    order: list[tuple[str, str]],
    desc: str,
) -> dict[tuple[str, str], AvwapResult]:
    """Run the AVWAP generator over every (instrument, domain) cell."""
    results: dict[tuple[str, str], AvwapResult] = {}
    for inst, domain in tqdm(order, desc=desc):
        results[(inst, domain)] = generate_avwap_events(
            cell_frames[(inst, domain)], instrument=inst, domain=domain
        )
    return results


def load_instruments() -> list[AnalysisData]:
    """Load the first-70% analysis slice for every available instrument."""
    files = list_timebar_files(DATA_DIR)
    if not files:
        raise FileNotFoundError(f"no timebar files under {DATA_DIR / 'timebars'}")
    data = [load_analysis_data(p) for p in tqdm(files, desc="load analysis slices")]
    return sorted(data, key=lambda d: d.instrument)


def build_cells(
    instruments_data: list[AnalysisData],
) -> tuple[dict[tuple[str, str], pl.DataFrame], dict[str, Any], list[dict[str, Any]]]:
    """Build domain frames per instrument and per-cell analysis metadata."""
    cell_frames: dict[tuple[str, str], pl.DataFrame] = {}
    fence_ts: dict[str, Any] = {}
    meta_rows: list[dict[str, Any]] = []
    for data in instruments_data:
        fence_ts[data.instrument] = data.frame.get_column("CloseTime").max()
        domains = build_domain_frames(data.frame)
        for d in DOMAINS:
            frame = domains[d]
            cell_frames[(data.instrument, d)] = frame
            spec = DOMAIN_SPECS[d]
            meta_rows.append(
                {
                    "instrument": data.instrument,
                    "domain": d,
                    "source_file": data.source_file,
                    "source_total_rows": data.total_rows,
                    "analysis_rows_1m": data.analysis_rows,
                    "analysis_start_1m": data.analysis_start,
                    "analysis_end_1m": data.analysis_end,
                    "period_minutes": spec.period_minutes,
                    "min_coverage": spec.min_coverage,
                    "domain_bars": frame.height,
                    "domain_min_close_time": (
                        str(frame.get_column("CloseTime").min()) if frame.height else None
                    ),
                    "domain_max_close_time": (
                        str(frame.get_column("CloseTime").max()) if frame.height else None
                    ),
                }
            )
    return cell_frames, fence_ts, meta_rows


def determinism_rows(
    main: dict[tuple[str, str], AvwapResult],
    replay: dict[tuple[str, str], AvwapResult],
    order: list[tuple[str, str]],
) -> tuple[list[dict[str, Any]], bool]:
    """Compare main vs replay event/regime hashes for every cell."""
    rows: list[dict[str, Any]] = []
    all_match = True
    for cell in order:
        ev_a = canonical_hash(main[cell].events)
        ev_b = canonical_hash(replay[cell].events)
        rg_a = canonical_hash(main[cell].regimes)
        rg_b = canonical_hash(replay[cell].regimes)
        events_match = ev_a == ev_b
        regimes_match = rg_a == rg_b
        all_match = all_match and events_match and regimes_match
        rows.append(
            {
                "instrument": cell[0],
                "domain": cell[1],
                "events_hash": ev_a,
                "events_hash_replay": ev_b,
                "events_match": events_match,
                "regimes_hash": rg_a,
                "regimes_match": regimes_match,
            }
        )
    return rows, all_match


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    """Run EXP-020 end to end and write all result artifacts."""
    configure_logging()
    ensure_output_dirs()

    instruments_data = load_instruments()
    instruments = [d.instrument for d in instruments_data]
    LOGGER.info("Loaded %d instruments: %s", len(instruments), ", ".join(instruments))

    cell_frames, fence_ts, meta_rows = build_cells(instruments_data)
    order = [(inst, d) for inst in instruments for d in DOMAINS]

    results = generate_all_cells(cell_frames, order, "AVWAP generate")
    replay = generate_all_cells(cell_frames, order, "AVWAP replay")
    det_rows, determinism_ok = determinism_rows(results, replay, order)

    # Invariants.
    inv_rows: list[dict[str, Any]] = []
    for cell in order:
        inv_rows.extend(cell_invariant_rows(results[cell], cell_frames[cell], fence_ts[cell[0]]))
    failed_checks = [r for r in inv_rows if not r["passed"]]
    total_violations = sum(r["n_violations"] for r in inv_rows)
    holdout_violations = sum(
        r["n_violations"] for r in inv_rows if r["check_name"] == "holdout_fence"
    )
    invariants_ok = len(failed_checks) == 0

    # Coverage / direction / readiness.
    cov_rows = [coverage_row(results[cell]) for cell in order]
    dir_rows = [direction_balance_row(results[cell]) for cell in order]
    coverage_lut = {(r["instrument"], r["domain"]): r for r in cov_rows}
    direction_lut = {(r["instrument"], r["domain"]): r for r in dir_rows}
    readiness = readiness_rows(coverage_lut)
    status, ready_domains = decide_status(
        readiness, coverage_lut, invariants_ok, determinism_ok, holdout_violations
    )

    # Combined event / regime tables (sorted for stable output).
    events_all = pl.concat([results[c].events for c in order]).sort(EVENT_SORT)
    regimes_all = pl.concat([results[c].regimes for c in order]).sort(REGIME_SORT)

    # Plots (bounded inputs).
    window = select_sample_window(results, cell_frames, coverage_lut, readiness, instruments)
    plot_event_density_heatmap(coverage_lut, instruments, PLOTS_DIR / "event_density_heatmap.png")
    plot_direction_balance(direction_lut, instruments, PLOTS_DIR / "direction_balance.png")
    plot_regime_anchor_distributions(
        regimes_all.get_column("regime_length_bars").to_numpy(),
        events_all.get_column("anchor_age_bars").to_numpy(),
        PLOTS_DIR / "regime_anchor_distributions.png",
    )
    plot_avwap_sample_overlay(window, PLOTS_DIR / "avwap_sample_overlay.png")

    # Write result tables.
    write_rows(RESULTS_DIR / "analysis_metadata.csv", meta_rows)
    events_all.write_csv(RESULTS_DIR / "avwap_events.csv")
    regimes_all.write_csv(RESULTS_DIR / "avwap_state_summary.csv")
    write_rows(RESULTS_DIR / "invariant_checks.csv", inv_rows)
    write_rows(RESULTS_DIR / "determinism_check.csv", det_rows)
    write_rows(RESULTS_DIR / "event_coverage.csv", cov_rows)
    write_rows(RESULTS_DIR / "domain_readiness.csv", [readiness[d] for d in DOMAINS])
    write_rows(RESULTS_DIR / "direction_balance.csv", dir_rows)

    metadata = {
        "experiment_id": EXPERIMENT_ID,
        "title": "AVWAP Event-Substrate Readiness",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": status,
        "ready_domain_count": len(ready_domains),
        "ready_domains": ready_domains,
        "invariants_ok": invariants_ok,
        "invariant_failure_count": total_violations,
        "failed_invariant_checks": [
            {"instrument": r["instrument"], "domain": r["domain"], "check": r["check_name"],
             "n_violations": r["n_violations"]}
            for r in failed_checks
        ],
        "determinism_pass": determinism_ok,
        "holdout_violation_count": holdout_violations,
        "total_events": events_all.height,
        "total_regimes": regimes_all.height,
        "instruments": instruments,
        "domains": list(DOMAINS),
        "readiness": {d: readiness[d] for d in DOMAINS},
        "thresholds": {
            "min_total_events": MIN_TOTAL_EVENTS,
            "min_direction_events": MIN_DIRECTION_EVENTS,
            "ready_min_instruments": READY_MIN_INSTRUMENTS,
        },
        "parameters": {
            "fast_ma": FAST_MA,
            "slow_ma": SLOW_MA,
            "avwap_source": "typical_price=(High+Low+Close)/3",
            "volume_exponent": VOLUME_EXPONENT,
            "band_spread": "median_absolute_deviation_from_anchored_avwap_path",
            "band_multiplier": BAND_MULTIPLIER,
            "domain_specs": {
                d: {"period_minutes": DOMAIN_SPECS[d].period_minutes,
                    "min_coverage": DOMAIN_SPECS[d].min_coverage}
                for d in DOMAINS
            },
        },
        "registry": REGISTRY_REFS,
        "sample_plot_cell": (
            {"instrument": window["cell"][0], "domain": window["cell"][1],
             "regime_id": window["regime_id"]}
            if window else None
        ),
    }
    write_json(RESULTS_DIR / "run_metadata.json", metadata)

    LOGGER.info("EXP-020 status: %s | ready domains: %s", status, ready_domains or "none")
    LOGGER.info(
        "events=%d regimes=%d | invariants_ok=%s determinism_pass=%s holdout_violations=%d",
        events_all.height, regimes_all.height, invariants_ok, determinism_ok, holdout_violations,
    )
    if failed_checks:
        LOGGER.info("FAILED invariant checks: %d", len(failed_checks))


if __name__ == "__main__":
    main()
