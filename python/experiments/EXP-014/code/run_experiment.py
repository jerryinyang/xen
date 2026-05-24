"""
Experiment EXP-014: PDH PDL ONH ONL Liquidity Level Reproducibility
Implements the approved scope and analysis plan.
"""
import sys
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[3]
PROJECT_ROOT = PYTHON_ROOT.parent
SRC_DIR = PYTHON_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

import json
import logging
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from ict_timebar import (
    INSTRUMENTS,
    add_ny_time_features,
    compute_liquidity_levels,
    load_analysis_timebars,
    train_cutoff_time,
)


LOGGER = logging.getLogger(__name__)

DATA_DIR = PROJECT_ROOT / "data"
EXP_DIR = PYTHON_ROOT / "experiments" / "EXP-014"
AVAILABILITY_THRESHOLD = 0.80
MIN_SEGMENT_DATES = 50


def summarize_availability(levels: pd.DataFrame) -> pd.DataFrame:
    """Summarize level availability by instrument and train/test segment."""
    if levels.empty:
        return pd.DataFrame()
    scoped = levels[levels["Segment"].isin(["Train", "Test"])].copy()
    summary = (
        scoped.groupby(["Instrument", "Segment"], as_index=False)
        .agg(
            EligibleDates=("NYDate", "nunique"),
            PDLevelDates=("HasPDLevels", "sum"),
            ONLevelDates=("HasONLevels", "sum"),
            AllLevelDates=("HasAllLevels", "sum"),
        )
        .sort_values(["Instrument", "Segment"])
        .reset_index(drop=True)
    )
    summary["AllLevelAvailability"] = (
        summary["AllLevelDates"] / summary["EligibleDates"]
    )
    summary["AvailabilityPass"] = (
        summary["AllLevelAvailability"] >= AVAILABILITY_THRESHOLD
    )
    summary["CountPass"] = summary["AllLevelDates"] >= MIN_SEGMENT_DATES
    summary["SegmentPass"] = summary["AvailabilityPass"] & summary["CountPass"]
    return summary


def summarize_missing_reasons(levels: pd.DataFrame) -> pd.DataFrame:
    """Count incomplete-level reasons."""
    if levels.empty:
        return pd.DataFrame()
    return (
        levels.groupby(["Instrument", "Segment", "MissingReason"], as_index=False)
        .agg(Dates=("NYDate", "nunique"))
        .sort_values(["Instrument", "Segment", "MissingReason"])
        .reset_index(drop=True)
    )


def summarize_value_ranges(levels: pd.DataFrame) -> pd.DataFrame:
    """Summarize level value ranges for anomaly screening."""
    if levels.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for column in ["PDH", "PDL", "ONH", "ONL"]:
        grouped = (
            levels.dropna(subset=[column])
            .groupby(["Instrument", "Segment"], as_index=False)
            .agg(
                Observations=(column, "count"),
                Minimum=(column, "min"),
                Median=(column, "median"),
                Maximum=(column, "max"),
            )
        )
        grouped["Level"] = column
        rows.extend(grouped.to_dict(orient="records"))
    return pd.DataFrame(rows).sort_values(
        ["Instrument", "Segment", "Level"]
    ).reset_index(drop=True)


def classify_readiness(
    availability: pd.DataFrame,
    deterministic_equal: bool,
) -> tuple[str, pd.DataFrame]:
    """Classify reproducibility readiness by instrument and overall."""
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        subset = availability[availability["Instrument"] == instrument]
        expected_segments = {"Train", "Test"}
        actual_segments = set(subset["Segment"].tolist())
        segment_complete = actual_segments == expected_segments
        segment_pass = bool(segment_complete and subset["SegmentPass"].all())
        rows.append(
            {
                "Instrument": instrument,
                "TrainTestRowsPresent": segment_complete,
                "SegmentThresholdsPass": segment_pass,
                "DeterministicRerunEqual": deterministic_equal,
                "InstrumentPass": segment_pass and deterministic_equal,
            }
        )
    readiness = pd.DataFrame(rows)
    pass_count = int(readiness["InstrumentPass"].sum())
    if pass_count == len(INSTRUMENTS):
        verdict = "SUPPORTED"
    elif pass_count == 0:
        verdict = "AGAINST"
    else:
        verdict = "INCONCLUSIVE"
    return verdict, readiness


def plot_availability(availability: pd.DataFrame, save_path: Path) -> None:
    """Plot all-level availability by instrument and segment."""
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(
        data=availability,
        x="Instrument",
        y="AllLevelAvailability",
        hue="Segment",
        order=INSTRUMENTS,
        ax=ax,
    )
    ax.axhline(AVAILABILITY_THRESHOLD, color="firebrick", linestyle="--", linewidth=1)
    ax.set_title("EXP-014 PDH/PDL/ONH/ONL Availability")
    ax.set_xlabel("")
    ax.set_ylabel("Dates with all four levels / eligible dates")
    ax.set_ylim(0.0, 1.05)
    ax.legend(title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_missing_reasons(missing: pd.DataFrame, save_path: Path) -> None:
    """Plot missing-level reason counts."""
    sns.set_theme(style="whitegrid")
    plot_df = missing[missing["MissingReason"] != "NONE"].copy()
    if plot_df.empty:
        plot_df = missing.copy()
    plot_df["Label"] = plot_df["Instrument"] + " " + plot_df["Segment"]
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(
        data=plot_df,
        x="Label",
        y="Dates",
        hue="MissingReason",
        ax=ax,
    )
    ax.set_title("EXP-014 Missing-Level Reason Counts")
    ax.set_xlabel("")
    ax.set_ylabel("NY dates")
    ax.tick_params(axis="x", rotation=45)
    ax.legend(title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def write_outputs(
    levels: pd.DataFrame,
    availability: pd.DataFrame,
    missing: pd.DataFrame,
    value_ranges: pd.DataFrame,
    readiness: pd.DataFrame,
    verdict: str,
    deterministic_equal: bool,
    plots_dir: Path,
    results_dir: Path,
) -> None:
    """Write scoped EXP-014 outputs."""
    levels.to_csv(results_dir / "liquidity_levels.csv", index=False)
    availability.to_csv(results_dir / "availability_summary.csv", index=False)
    missing.to_csv(results_dir / "missing_reason_counts.csv", index=False)
    value_ranges.to_csv(results_dir / "level_value_ranges.csv", index=False)
    readiness.to_csv(results_dir / "readiness_by_instrument.csv", index=False)

    payload = {
        "experiment_id": "EXP-014",
        "title": "PDH PDL ONH ONL Liquidity Level Reproducibility",
        "verdict": verdict,
        "availability_threshold": AVAILABILITY_THRESHOLD,
        "minimum_segment_dates": MIN_SEGMENT_DATES,
        "deterministic_rerun_equal": deterministic_equal,
        "level_definition_note": (
            "PDH/PDL use the previous observed weekday NY date. ONH/ONL use "
            "CloseTimeNY bars from 17:00 on the prior calendar date through "
            "09:30 on the event date. Continuous-instrument session caveats are "
            "recorded through missing reason counts rather than imputation."
        ),
        "readiness_by_instrument": readiness.to_dict(orient="records"),
        "availability_summary": availability.to_dict(orient="records"),
    }
    with (results_dir / "results.json").open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, default=str)

    with (results_dir / "numerical_summary.txt").open("w", encoding="utf-8") as handle:
        handle.write("EXP-014 PDH PDL ONH ONL Liquidity Level Reproducibility\n")
        handle.write(f"Verdict: {verdict}\n")
        handle.write(f"Deterministic rerun equality: {deterministic_equal}\n")
        handle.write(
            "Definitions: PDH/PDL = previous observed weekday NY-date high/low; "
            "ONH/ONL = 17:00 prior calendar date through 09:30 event date using "
            "CloseTimeNY bars.\n"
        )
        handle.write("\nAvailability by instrument and segment:\n")
        for row in availability.itertuples(index=False):
            handle.write(
                f"- {row.Instrument} {row.Segment}: "
                f"{row.AllLevelAvailability:.3f} all-level availability "
                f"({row.AllLevelDates}/{row.EligibleDates}), "
                f"count_pass={row.CountPass}, segment_pass={row.SegmentPass}\n"
            )
        handle.write("\nReadiness by instrument:\n")
        for row in readiness.itertuples(index=False):
            handle.write(
                f"- {row.Instrument}: pass={row.InstrumentPass}, "
                f"train_test_rows_present={row.TrainTestRowsPresent}, "
                f"deterministic={row.DeterministicRerunEqual}\n"
            )

    plot_availability(availability, plots_dir / "01_level_availability.png")
    plot_missing_reasons(missing, plots_dir / "02_missing_reason_counts.png")


def run_experiment() -> None:
    """Execute the EXP-014 reproducibility workflow."""
    plots_dir = EXP_DIR / "plots"
    results_dir = EXP_DIR / "results"
    plots_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    level_parts: list[pd.DataFrame] = []
    for instrument in INSTRUMENTS:
        LOGGER.info("loading %s analysis-set time bars", instrument)
        load = load_analysis_timebars(DATA_DIR, instrument)
        train_end = train_cutoff_time(load.frame, load.train_rows)
        ny_frame = add_ny_time_features(load.frame, train_end)
        level_parts.append(compute_liquidity_levels(ny_frame))

    if not level_parts:
        raise ValueError("No level rows were produced.")

    levels = pd.concat(level_parts, ignore_index=True)

    # F06: rerun with reversed instrument order to detect ordering-dependent
    # non-determinism (e.g., unsorted groupby, dict-ordering in pandas).
    rerun_parts: list[pd.DataFrame] = []
    for instrument in reversed(INSTRUMENTS):
        load = load_analysis_timebars(DATA_DIR, instrument)
        train_end = train_cutoff_time(load.frame, load.train_rows)
        ny_frame = add_ny_time_features(load.frame, train_end)
        rerun_parts.append(compute_liquidity_levels(ny_frame))

    rerun_levels = pd.concat(rerun_parts, ignore_index=True)

    sort_cols = ["Instrument", "NYDate"]
    levels_sorted = levels.sort_values(sort_cols).reset_index(drop=True)
    rerun_sorted = rerun_levels.sort_values(sort_cols).reset_index(drop=True)
    deterministic_equal = levels_sorted.equals(rerun_sorted)
    if not deterministic_equal:
        LOGGER.warning("Determinism check FAILED: reversed-order rerun produced different output.")
    availability = summarize_availability(levels)
    missing = summarize_missing_reasons(levels)
    value_ranges = summarize_value_ranges(levels)
    verdict, readiness = classify_readiness(availability, deterministic_equal)

    write_outputs(
        levels,
        availability,
        missing,
        value_ranges,
        readiness,
        verdict,
        deterministic_equal,
        plots_dir,
        results_dir,
    )

    print("EXP-014 complete.")
    print(f"Verdict: {verdict}")
    print(f"Plots: {plots_dir}")
    print(f"Results: {results_dir}")


def main() -> None:
    """Entry point for manual execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_experiment()


if __name__ == "__main__":
    main()
