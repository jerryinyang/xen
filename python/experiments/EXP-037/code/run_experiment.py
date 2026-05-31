"""
Experiment EXP-037: Null Calibration of Frozen Reference Stack
Implements the analysis plan from analysis-plan.md.

This script builds the Phase 006 Part A calibration harness around the frozen
EXP-036 reference stack. It excludes the final 30% global holdout before
aggregation, generates dependence-preserving null realizations, runs the
unchanged stack, and writes FPR/per-leg summaries. It does not plant effects,
estimate power, alter thresholds, or access the holdout.
"""
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

PYTHON_ROOT = Path(__file__).resolve().parents[3]
PROJECT_ROOT = PYTHON_ROOT.parent
SRC_DIR = PYTHON_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

import referee_calibration as rc  # noqa: E402


LOGGER = logging.getLogger(__name__)

DATA_DIR = PROJECT_ROOT / "data"
EXP_DIR = PYTHON_ROOT / "experiments" / "EXP-037"
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"

PHASE_SPEC = (
    "docs/experiments-docs/checkpoints/"
    "2026-05-31-006-thesis-qualification-referee-calibration/reference-stack-spec.md"
)


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(_clean_json(payload), indent=2, default=rc.json_safe, allow_nan=False)
    )


def _clean_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _clean_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean_json(item) for item in value]
    if isinstance(value, np.ndarray):
        return [_clean_json(item) for item in value.tolist()]
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    return value


def _stringify_keys(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _stringify_keys(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_stringify_keys(item) for item in value]
    return value


def _run_one(
    observed_cells: dict[tuple[str, str], rc.CellFeature],
    observed_diag: dict[str, Any],
    block_length: int,
    seed_index: int,
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    start = time.perf_counter()
    result = rc.run_null_realization(observed_cells, observed_diag, block_length, seed_index)
    elapsed = time.perf_counter() - start
    battery = rc.battery_partition(seed_index)
    row = rc.realization_row(
        block_length, seed_index, result.diagnostics, result.verdict, elapsed
    )
    metrics = rc.metrics_rows(
        result.metrics, block_length, seed_index, battery, row["Trusted"]
    )
    cell_passes = rc.cell_pass_rows(
        result.metrics, block_length, seed_index, battery, row["Trusted"]
    )
    diagnostics = pd.DataFrame([{**row, "RateUse": "realization"}])
    return row, metrics, cell_passes, diagnostics


def _profile_execution(
    observed_cells: dict[tuple[str, str], rc.CellFeature],
    observed_diag: dict[str, Any],
) -> tuple[list[tuple[int, int]], list[dict[str, Any]], list[pd.DataFrame], list[pd.DataFrame], bool, int]:
    LOGGER.info("EXP-037: profiling first %s FSE", rc.PROFILE_FSE_COUNT)
    completed: list[tuple[int, int]] = []
    rows: list[dict[str, Any]] = []
    metric_frames: list[pd.DataFrame] = []
    cell_frames: list[pd.DataFrame] = []
    profile_block = rc.NULL_BLOCK_LENGTHS[0]
    for seed_index in range(rc.PROFILE_FSE_COUNT):
        row, metrics, cell_passes, _ = _run_one(
            observed_cells, observed_diag, profile_block, seed_index
        )
        completed.append((profile_block, seed_index))
        rows.append(row)
        metric_frames.append(metrics)
        cell_frames.append(cell_passes)
        LOGGER.info(
            "EXP-037: profile L=%s seed=%s outcome=%s runtime=%.2fs",
            profile_block, seed_index, row["Outcome"], row["RuntimeSeconds"],
        )

    median_runtime = float(np.median([row["RuntimeSeconds"] for row in rows]))
    use_downscale = median_runtime > rc.FSE_RUNTIME_TARGET_SECONDS
    realization_count = (
        rc.PART_A_DOWNSCALED_REALIZATIONS if use_downscale else rc.PART_A_REALIZATIONS
    )
    estimated_seconds = median_runtime * realization_count * len(rc.NULL_BLOCK_LENGTHS)
    stop_for_compute = estimated_seconds > 30 * 60 * 60
    return completed, rows, metric_frames, cell_frames, stop_for_compute, realization_count


def _run_remaining(
    observed_cells: dict[tuple[str, str], rc.CellFeature],
    observed_diag: dict[str, Any],
    completed: set[tuple[int, int]],
    realization_count: int,
) -> tuple[list[dict[str, Any]], list[pd.DataFrame], list[pd.DataFrame]]:
    rows: list[dict[str, Any]] = []
    metric_frames: list[pd.DataFrame] = []
    cell_frames: list[pd.DataFrame] = []
    for block_length in rc.NULL_BLOCK_LENGTHS:
        for seed_index in range(realization_count):
            if (block_length, seed_index) in completed:
                continue
            row, metrics, cell_passes, _ = _run_one(
                observed_cells, observed_diag, block_length, seed_index
            )
            rows.append(row)
            metric_frames.append(metrics)
            cell_frames.append(cell_passes)
            LOGGER.info(
                "EXP-037: L=%s seed=%s battery=%s trusted=%s outcome=%s runtime=%.2fs",
                block_length,
                seed_index,
                row["Battery"],
                row["Trusted"],
                row["Outcome"],
                row["RuntimeSeconds"],
            )
    return rows, metric_frames, cell_frames


def _fpr_envelope(realizations: pd.DataFrame) -> dict[str, Any]:
    envelope: dict[str, Any] = {}
    for block_length in rc.NULL_BLOCK_LENGTHS:
        block = realizations[
            (realizations["BlockLength"] == block_length)
            & (realizations["Battery"] == "second_order")
            & (realizations["Trusted"])
        ]
        successes = int(block["FullStackFOR"].sum()) if not block.empty else 0
        total = int(len(block))
        lo, hi = rc.wilson_interval(successes, total)
        envelope[str(block_length)] = {
            "trusted_denominator": total,
            "for_count": successes,
            "fpr": None if total == 0 else successes / total,
            "wilson95_lower": lo,
            "wilson95_upper": hi,
            "valid": total > 0,
        }
    valid_rates = [
        item["fpr"] for item in envelope.values() if item["valid"] and item["fpr"] is not None
    ]
    envelope["headline"] = {
        "valid_block_lengths": [
            int(key) for key, item in envelope.items() if key.isdigit() and item["valid"]
        ],
        "fpr_min": None if not valid_rates else min(valid_rates),
        "fpr_max": None if not valid_rates else max(valid_rates),
    }
    return envelope


def _write_outputs(
    observed_metrics: dict[tuple[str, str], dict[str, Any]],
    observed_verdict: dict[str, Any],
    observed_diag: dict[str, Any],
    realizations: pd.DataFrame,
    metrics: pd.DataFrame,
    cell_passes: pd.DataFrame,
    realization_count: int,
    compute_stopped: bool,
) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    rc.metrics_rows(observed_metrics).to_csv(RESULTS_DIR / "observed_metrics.csv", index=False)
    _write_json(RESULTS_DIR / "observed_verdict.json", observed_verdict)
    _write_json(RESULTS_DIR / "observed_diagnostics.json", _stringify_keys(observed_diag))

    realizations.to_csv(RESULTS_DIR / "realization_summary.csv", index=False)
    metrics.to_csv(RESULTS_DIR / "metrics_table.csv", index=False)
    cell_passes.to_csv(RESULTS_DIR / "cell_passes.csv", index=False)
    _profile_rows(realizations).to_csv(RESULTS_DIR / "profile_summary.csv", index=False)
    _diagnostic_rows(realizations).to_csv(RESULTS_DIR / "null_diagnostics.csv", index=False)
    _leg_count_rows(metrics).to_csv(RESULTS_DIR / "leg_counts.csv", index=False)

    verdict_rates = rc.summarize_verdict_rates(realizations)
    cell_rates = rc.summarize_cell_pass_rates(cell_passes)
    verdict_rates.to_csv(RESULTS_DIR / "rate_summary.csv", index=False)
    verdict_rates.to_csv(RESULTS_DIR / "verdict_ladder_rates.csv", index=False)
    cell_rates.to_csv(RESULTS_DIR / "leg_rate_summary.csv", index=False)
    _write_json(RESULTS_DIR / "fpr_envelope.json", _fpr_envelope(realizations))
    _write_json(
        RESULTS_DIR / "manifest.json",
        {
            "experiment": "EXP-037",
            "phase_spec": PHASE_SPEC,
            "block_lengths": list(rc.NULL_BLOCK_LENGTHS),
            "realizations_per_block": realization_count,
            "compute_stopped": compute_stopped,
            "battery_partition": "even seed indices = development; odd seed indices = second_order",
            "bootstrap_n": rc.BOOTSTRAP_N,
            "bootstrap_seed": rc.BOOTSTRAP_SEED,
            "holdout_rule": "first 70% only; final 30% global holdout excluded before aggregation",
        },
    )
    _render_plots(realizations, verdict_rates, cell_rates)


def _profile_rows(realizations: pd.DataFrame) -> pd.DataFrame:
    if realizations.empty:
        return pd.DataFrame()
    return realizations[
        (realizations["BlockLength"] == rc.NULL_BLOCK_LENGTHS[0])
        & (realizations["SeedIndex"] < rc.PROFILE_FSE_COUNT)
    ].copy()


def _diagnostic_rows(realizations: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "BlockLength",
        "SeedIndex",
        "Battery",
        "Trusted",
        "DiagnosticsPass",
        "DescriptorPass",
        "ReturnAutocorrPass",
        "CrossCorrPass",
        "descriptor_failed_cells",
        "descriptor_max_count_rel_diff",
        "descriptor_max_median_rel_diff",
        "descriptor_max_p90_rel_diff",
        "autocorr_sign_mismatches",
        "autocorr_sign_match_rate",
        "cross_corr_failed_matrices",
        "cross_corr_max_frobenius",
    ]
    return realizations[[col for col in cols if col in realizations.columns]].copy()


def _leg_count_rows(metrics: pd.DataFrame) -> pd.DataFrame:
    id_cols = ["BlockLength", "SeedIndex", "Battery", "Trusted", "Instrument", "Timeframe", "Segment", "Horizon"]
    count_cols = [col for col in metrics.columns if col.startswith("Rows_") or col.startswith("Eps_")]
    flag_cols = [col for col in metrics.columns if col.endswith("_adjudicable")]
    return metrics[[col for col in [*id_cols, *count_cols, *flag_cols] if col in metrics.columns]].copy()


def _render_plots(
    realizations: pd.DataFrame,
    verdict_rates: pd.DataFrame,
    cell_rates: pd.DataFrame,
) -> None:
    _plot_fpr_envelope(verdict_rates, PLOTS_DIR / "01_fpr_envelope.png")
    _plot_verdict_ladder(verdict_rates, PLOTS_DIR / "02_verdict_ladder.png")
    _plot_leg_rates(cell_rates, PLOTS_DIR / "03_leg_false_pass_rates.png")
    _plot_diagnostics(realizations, PLOTS_DIR / "04_null_diagnostics.png")


def _plot_fpr_envelope(verdict_rates: pd.DataFrame, save_path: Path) -> None:
    data = verdict_rates[
        (verdict_rates["Metric"] == "full_stack_fpr")
        & (verdict_rates["RateSet"].isin(["trusted_second_order", "all_realizations"]))
    ].copy()
    if data.empty:
        return
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(8, 5))
    for rate_set, marker in (("trusted_second_order", "o"), ("all_realizations", "x")):
        subset = data[data["RateSet"] == rate_set]
        if subset.empty:
            continue
        ax.errorbar(
            subset["BlockLength"],
            subset["Rate"],
            yerr=[
                subset["Rate"] - subset["Wilson95Lower"],
                subset["Wilson95Upper"] - subset["Rate"],
            ],
            marker=marker,
            capsize=3,
            label=rate_set,
        )
    ax.set_xlabel("Return-stream block length L")
    ax.set_ylabel("Full-stack FPR")
    ax.set_title("EXP-037: FPR envelope by null block length")
    ax.set_ylim(bottom=0)
    ax.legend()
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_verdict_ladder(verdict_rates: pd.DataFrame, save_path: Path) -> None:
    data = verdict_rates[
        (verdict_rates["RateSet"] == "trusted_second_order")
        & (verdict_rates["Metric"].str.startswith("verdict_"))
    ].copy()
    if data.empty:
        data = verdict_rates[
            (verdict_rates["RateSet"] == "all_realizations")
            & (verdict_rates["Metric"].str.startswith("verdict_"))
        ].copy()
    if data.empty:
        return
    data["Outcome"] = data["Metric"].str.replace("verdict_", "", regex=False)
    pivot = data.pivot(index="BlockLength", columns="Outcome", values="Rate").fillna(0.0)
    fig, ax = plt.subplots(figsize=(9, 5))
    pivot.plot(kind="bar", stacked=True, ax=ax)
    ax.set_ylabel("Rate")
    ax.set_title("EXP-037: verdict ladder distribution")
    ax.legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_leg_rates(cell_rates: pd.DataFrame, save_path: Path) -> None:
    data = cell_rates[
        (cell_rates["RateSet"] == "trusted_second_order")
        & (cell_rates["Horizon"] == "next_bar")
        & (cell_rates["Contrast"].isin(["neutral", "control", "both"]))
    ].copy()
    if data.empty:
        data = cell_rates[
            (cell_rates["RateSet"] == "all_realizations")
            & (cell_rates["Horizon"] == "next_bar")
            & (cell_rates["Contrast"].isin(["neutral", "control", "both"]))
        ].copy()
    if data.empty:
        return
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=data, x="BlockLength", y="Rate", hue="Contrast", ax=ax)
    ax.set_ylabel("Cell false-pass rate")
    ax.set_title("EXP-037: next-bar per-leg false-pass rates")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_diagnostics(realizations: pd.DataFrame, save_path: Path) -> None:
    if realizations.empty:
        return
    grouped = (
        realizations.groupby("BlockLength")
        .agg(
            DiagnosticsPass=("DiagnosticsPass", "mean"),
            DescriptorPass=("DescriptorPass", "mean"),
            ReturnAutocorrPass=("ReturnAutocorrPass", "mean"),
            CrossCorrPass=("CrossCorrPass", "mean"),
        )
        .reset_index()
        .melt(id_vars="BlockLength", var_name="Diagnostic", value_name="PassShare")
    )
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=grouped, x="BlockLength", y="PassShare", hue="Diagnostic", ax=ax)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Pass share")
    ax.set_title("EXP-037: null-validity diagnostic pass share")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def run_experiment() -> None:
    """Execute EXP-037 null calibration end to end."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    LOGGER.info("EXP-037: loading holdout-excluded observed cells")
    observed_cells = rc.build_observed_cells(DATA_DIR)
    observed_diag = rc.observed_diagnostics(observed_cells)
    observed_metrics = rc.stack_metrics(observed_cells, seed_index=0)
    observed_verdict = rc.frozen_stack_verdict(observed_metrics)

    completed, rows, metric_frames, cell_frames, stop_for_compute, realization_count = (
        _profile_execution(observed_cells, observed_diag)
    )
    if not stop_for_compute:
        more_rows, more_metrics, more_cells = _run_remaining(
            observed_cells, observed_diag, set(completed), realization_count
        )
        rows.extend(more_rows)
        metric_frames.extend(more_metrics)
        cell_frames.extend(more_cells)

    realizations = pd.DataFrame(rows)
    metrics = pd.concat(metric_frames, ignore_index=True) if metric_frames else pd.DataFrame()
    cell_passes = pd.concat(cell_frames, ignore_index=True) if cell_frames else pd.DataFrame()
    _write_outputs(
        observed_metrics,
        observed_verdict,
        observed_diag,
        realizations,
        metrics,
        cell_passes,
        realization_count,
        stop_for_compute,
    )
    _print_summary(realizations, stop_for_compute)


def _print_summary(realizations: pd.DataFrame, stop_for_compute: bool) -> None:
    print("\n=== EXP-037 calibration run ===")
    if stop_for_compute:
        print("Compute profile exceeded the predeclared stop rule; no long run executed.")
    print(f"Realizations completed: {len(realizations):,}")
    if not realizations.empty:
        trusted = realizations[realizations["Trusted"]]
        print(f"Trusted second-order valid realizations: {len(trusted):,}")
        if not trusted.empty:
            fpr = trusted.groupby("BlockLength")["FullStackFOR"].mean()
            print("\nTrusted FPR by block length:")
            print(fpr.to_string())


def main() -> None:
    """Configure logging and run the experiment."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run_experiment()


if __name__ == "__main__":
    main()
