"""
Experiment EXP-020: FVG IFVG Detection Reproducibility
Implements the analysis plan from analysis-plan.md.
"""
import hashlib
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import polars as pl
import seaborn as sns

PYTHON_ROOT = Path(__file__).resolve().parents[3]
PROJECT_ROOT = PYTHON_ROOT.parent
SRC_DIR = PYTHON_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from ict_timebar import (  # noqa: E402
    INSTRUMENTS,
    add_bar_diagnostics,
    compute_price_precision_step,
    load_analysis_timebars,
)


LOGGER = logging.getLogger(__name__)

DATA_DIR = PROJECT_ROOT / "data"
EXP_DIR = PYTHON_ROOT / "experiments" / "EXP-020"

ATR_SIZE_COEFF = 0.02
ATR_PERIOD = 14
LIFECYCLE_BARS = 120
MIN_FVG_PER_SEGMENT = 100
MIN_IFVG_PER_SEGMENT = 50
PLOT_SIZE_QUANTILE = 0.99
REPRODUCIBILITY_SHUFFLE_SEED = 42
# Cap the invariance check at this many bars per instrument. The
# reproducibility property is about deterministic mapping from sorted
# (CloseTime, OHLC, ATR14Prior) to FVG events; a representative slice is
# sufficient to exercise it and keeps the verification step bounded.
REPRODUCIBILITY_SAMPLE_BARS = 50_000
# An IFVG-to-FVG base rate above this threshold means the 'IFVG inversion'
# event is close to a tautology on 1-minute bars rather than a discriminating
# signal. EXP-021 relies on IFVG selectivity; downstream usage with a higher
# base rate should be flagged for parameter-tightening review.
IFVG_TAUTOLOGY_RATE = 0.5

FVG_KEY_COLS = [
    "EventID",
    "Instrument",
    "Segment",
    "Side",
    "CreationTime",
    "LowerBound",
    "UpperBound",
    "FVGSize",
]


@dataclass(frozen=True)
class PreparedBars:
    """Column arrays needed for FVG detection and lifecycle classification."""

    close_times: np.ndarray
    highs: np.ndarray
    lows: np.ndarray
    closes: np.ndarray
    segments: np.ndarray
    atr14_prior: np.ndarray

    @classmethod
    def from_frame(cls, frame: pd.DataFrame) -> "PreparedBars":
        """Create cached numpy arrays from a minimal bar frame."""
        return cls(
            close_times=pd.to_datetime(frame["CloseTime"]).to_numpy(),
            highs=frame["High"].to_numpy(dtype=float),
            lows=frame["Low"].to_numpy(dtype=float),
            closes=frame["Close"].to_numpy(dtype=float),
            segments=frame["Segment"].to_numpy(),
            atr14_prior=frame["ATR14Prior"].to_numpy(dtype=float),
        )

    def __len__(self) -> int:
        """Return the number of prepared bars."""
        return len(self.close_times)


def load_instrument_bars(instrument: str) -> tuple[PreparedBars, float]:
    """Load holdout-excluded analysis bars and precision step for one instrument."""
    loaded = load_analysis_timebars(DATA_DIR, instrument)
    frame = add_bar_diagnostics(loaded.frame)
    precision_step = compute_price_precision_step(frame)
    bars = (
        frame.with_row_index("_Row")
        .with_columns(
            pl.when(pl.col("_Row") < loaded.train_rows)
            .then(pl.lit("Train"))
            .otherwise(pl.lit("Test"))
            .alias("Segment")
        )
        .select(["CloseTime", "High", "Low", "Close", "Segment", "ATR14Prior"])
        .to_pandas()
        .reset_index(drop=True)
    )
    return PreparedBars.from_frame(bars), precision_step


def _candidate_arrays(
    bars: PreparedBars,
    precision_step: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return vectorized scoped FVG candidates at candle i."""
    if len(bars) < 3:
        empty_float = np.array([], dtype=float)
        empty_int = np.array([], dtype=int)
        empty_object = np.array([], dtype=object)
        return (
            empty_int,
            empty_object,
            empty_float,
            empty_float,
            empty_float,
            empty_float,
            empty_float,
        )

    candidate_idx = np.arange(2, len(bars))
    left_highs = bars.highs[:-2]
    left_lows = bars.lows[:-2]
    current_highs = bars.highs[2:]
    current_lows = bars.lows[2:]
    atr_prior = bars.atr14_prior[2:]

    bearish = current_highs < left_lows
    bullish = current_lows > left_highs
    side = np.where(bearish, "Bearish", "Bullish")
    lower = np.where(bearish, current_highs, left_highs)
    upper = np.where(bearish, left_lows, current_lows)
    size = upper - lower
    atr_component = np.where(np.isfinite(atr_prior), ATR_SIZE_COEFF * atr_prior, 0.0)
    min_size = np.maximum(precision_step, atr_component)
    keep = (bearish | bullish) & np.isfinite(size) & (size >= min_size)

    return (
        candidate_idx[keep],
        side[keep],
        lower[keep],
        upper[keep],
        size[keep],
        atr_prior[keep],
        min_size[keep],
    )


def _first_time(mask: np.ndarray, close_times: np.ndarray, start: int) -> pd.Timestamp:
    """Return the timestamp of the first true value in a forward mask."""
    positions = np.flatnonzero(mask)
    if positions.size == 0:
        return pd.NaT
    return pd.Timestamp(close_times[start + int(positions[0])])


def classify_lifecycle(
    bars: PreparedBars,
    creation_idx: int,
    side: str,
    lower: float,
    upper: float,
) -> dict[str, Any]:
    """Classify 120-bar FVG lifecycle and first IFVG close-through timestamp."""
    start = creation_idx + 1
    end = min(start + LIFECYCLE_BARS, len(bars))
    if start >= end:
        return {
            "LifecycleState": "formed",
            "PartialFillTime": pd.NaT,
            "FullFillTime": pd.NaT,
            "InversionTime": pd.NaT,
            "IsIFVG": False,
            "TrackingBars": 0,
            "ObservationComplete": False,
        }

    highs = bars.highs[start:end]
    lows = bars.lows[start:end]
    closes = bars.closes[start:end]
    if side == "Bullish":
        partial_mask = lows <= upper
        full_mask = lows <= lower
        inversion_mask = closes < lower
    else:
        partial_mask = highs >= lower
        full_mask = highs >= upper
        inversion_mask = closes > upper

    inversion_positions = np.flatnonzero(inversion_mask)
    inversion_pos = int(inversion_positions[0]) if inversion_positions.size else None
    scan_stop = inversion_pos + 1 if inversion_pos is not None else end - start

    partial_time = _first_time(partial_mask[:scan_stop], bars.close_times, start)
    full_time = _first_time(full_mask[:scan_stop], bars.close_times, start)
    inversion_time = (
        pd.Timestamp(bars.close_times[start + inversion_pos])
        if inversion_pos is not None
        else pd.NaT
    )

    observation_complete = end - start >= LIFECYCLE_BARS
    if not pd.isna(inversion_time):
        state = "inverted"
    elif not pd.isna(full_time):
        state = "fully_filled"
    elif not pd.isna(partial_time):
        state = "partially_filled"
    elif observation_complete:
        state = "expired"
    else:
        state = "formed"

    return {
        "LifecycleState": state,
        "PartialFillTime": partial_time,
        "FullFillTime": full_time,
        "InversionTime": inversion_time,
        "IsIFVG": not pd.isna(inversion_time),
        "TrackingBars": end - start,
        "ObservationComplete": observation_complete,
    }


def detect_fvgs(
    bars: PreparedBars,
    instrument: str,
    precision_step: float,
) -> pd.DataFrame:
    """Detect scoped FVGs and classify lifecycle states deterministically."""
    rows: list[dict[str, Any]] = []
    (
        candidate_idx,
        sides,
        lower_bounds,
        upper_bounds,
        sizes,
        atr_prior_values,
        min_sizes,
    ) = _candidate_arrays(bars, precision_step)
    for idx, side, lower, upper, size, atr_prior, min_size in zip(
        candidate_idx,
        sides,
        lower_bounds,
        upper_bounds,
        sizes,
        atr_prior_values,
        min_sizes,
    ):
        event = {
            "EventID": f"{instrument}-{idx:08d}-{side[0]}",
            "Instrument": instrument,
            "Segment": bars.segments[idx],
            "Side": side,
            "LeftCandleTime": pd.Timestamp(bars.close_times[idx - 2]),
            "CreationIndex": int(idx),
            "CreationTime": pd.Timestamp(bars.close_times[idx]),
            "LowerBound": float(lower),
            "UpperBound": float(upper),
            "FVGSize": float(size),
            "ATR14Prior": float(atr_prior) if np.isfinite(atr_prior) else np.nan,
            "MinSize": float(min_size),
            "PricePrecisionStep": precision_step,
        }
        rows.append(
            {
                **event,
                **classify_lifecycle(
                    bars,
                    int(idx),
                    str(side),
                    float(lower),
                    float(upper),
                ),
            }
        )
    return pd.DataFrame(rows)


def digest_events(events: pd.DataFrame) -> str:
    """Return a stable digest over deterministic FVG identity columns."""
    if events.empty:
        return hashlib.sha256(b"EMPTY").hexdigest()
    stable = events[FVG_KEY_COLS].sort_values(FVG_KEY_COLS).copy()
    text = stable.to_csv(index=False, float_format="%.12g")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _slice_prepared_bars(bars: PreparedBars, n: int) -> PreparedBars:
    """Return the first n bars as a new PreparedBars."""
    n = min(n, len(bars))
    return PreparedBars(
        close_times=bars.close_times[:n],
        highs=bars.highs[:n],
        lows=bars.lows[:n],
        closes=bars.closes[:n],
        segments=bars.segments[:n],
        atr14_prior=bars.atr14_prior[:n],
    )


def _shuffle_then_resort(bars: PreparedBars, seed: int) -> PreparedBars:
    """Return a PreparedBars with rows shuffled and then re-sorted by CloseTime.

    If detection depends only on the sorted-by-CloseTime data (it must), the
    shuffled-then-resorted frame should produce identical FVG events. This
    catches ordering-dependent bugs and silent reliance on row position.
    """
    n = len(bars)
    rng = np.random.default_rng(seed)
    perm = rng.permutation(n)
    shuffled = pd.DataFrame(
        {
            "CloseTime": bars.close_times[perm],
            "High": bars.highs[perm],
            "Low": bars.lows[perm],
            "Close": bars.closes[perm],
            "Segment": bars.segments[perm],
            "ATR14Prior": bars.atr14_prior[perm],
        }
    ).sort_values("CloseTime", kind="stable").reset_index(drop=True)
    return PreparedBars.from_frame(shuffled)


def verify_reproducibility(
    bars_by_instrument: dict[str, PreparedBars],
    precision_steps: dict[str, float],
    first_pass: pd.DataFrame,
) -> pd.DataFrame:
    """Verify detection invariance under (a) a fresh disk reload and (b) an
    input row-shuffle followed by re-sort.

    The previous version reran `detect_fvgs` on the same in-memory inputs,
    which is guaranteed to match and tests nothing. The two checks here
    actually exercise the determinism guarantee EXP-021 depends on: that
    FVG events are determined by the sorted (CloseTime, OHLC, ATR) data
    alone, not by source row order or by in-memory state from the first
    pass. A failure on either check would indicate a real reproducibility
    bug worth fixing before EXP-021 builds on these timestamps.
    """
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        sample_n = min(
            REPRODUCIBILITY_SAMPLE_BARS, len(bars_by_instrument[instrument])
        )

        # Subset the first-pass events to those originating within the
        # sampled bar range so digests can be compared like-for-like.
        first_full = first_pass[first_pass["Instrument"] == instrument]
        first_subset = first_full[first_full["CreationIndex"] < sample_n]
        first_digest = digest_events(first_subset)

        # (a) Fresh load from disk, then slice. Independent of in-memory state.
        fresh_full_bars, fresh_step = load_instrument_bars(instrument)
        fresh_bars = _slice_prepared_bars(fresh_full_bars, sample_n)
        fresh = detect_fvgs(fresh_bars, instrument, fresh_step)
        fresh_digest = digest_events(fresh)

        # (b) Shuffle rows of the sampled slice, re-sort by CloseTime, recompute.
        sampled_in_memory = _slice_prepared_bars(
            bars_by_instrument[instrument], sample_n
        )
        shuffled_bars = _shuffle_then_resort(
            sampled_in_memory, REPRODUCIBILITY_SHUFFLE_SEED
        )
        shuffled = detect_fvgs(shuffled_bars, instrument, precision_steps[instrument])
        shuffled_digest = digest_events(shuffled)

        rows.append(
            {
                "Instrument": instrument,
                "SampleBars": sample_n,
                "FirstPassN": len(first_subset),
                "FreshReloadN": len(fresh),
                "ShuffledResortN": len(shuffled),
                "FirstDigest": first_digest,
                "FreshReloadDigest": fresh_digest,
                "ShuffledResortDigest": shuffled_digest,
                "FreshReloadMatches": first_digest == fresh_digest,
                "ShuffledResortMatches": first_digest == shuffled_digest,
                "Reproducible": (
                    first_digest == fresh_digest and first_digest == shuffled_digest
                ),
            }
        )
    return pd.DataFrame(rows)


def summarize_counts(events: pd.DataFrame) -> pd.DataFrame:
    """Summarize FVG/IFVG counts, base rate, and readiness flags.

    `IFVGRate = IFVG_N / FVG_N` is the IFVG base rate. When it exceeds
    `IFVG_TAUTOLOGY_RATE`, almost every FVG eventually inverts within the
    120-bar lifecycle window, which means IFVG inversion is not a
    discriminating signal at this parameterisation and EXP-021 should
    treat that instrument/segment with tightened parameters before use.
    """
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        for segment in ("Train", "Test"):
            group = events[
                (events["Instrument"] == instrument)
                & (events["Segment"] == segment)
            ]
            fvg_n = len(group)
            ifvg_n = int(group["IsIFVG"].sum()) if not group.empty else 0
            ifvg_rate = ifvg_n / fvg_n if fvg_n else np.nan
            rows.append(
                {
                    "Instrument": instrument,
                    "Segment": segment,
                    "FVG_N": fvg_n,
                    "IFVG_N": ifvg_n,
                    "IFVGRate": ifvg_rate,
                    "FVGFloorMet": fvg_n >= MIN_FVG_PER_SEGMENT,
                    "IFVGFloorMet": ifvg_n >= MIN_IFVG_PER_SEGMENT,
                    "Tautological": bool(
                        np.isfinite(ifvg_rate) and ifvg_rate >= IFVG_TAUTOLOGY_RATE
                    ),
                    "ReadyForIFVGStudy": (
                        fvg_n >= MIN_FVG_PER_SEGMENT
                        and ifvg_n >= MIN_IFVG_PER_SEGMENT
                        and not (
                            np.isfinite(ifvg_rate)
                            and ifvg_rate >= IFVG_TAUTOLOGY_RATE
                        )
                    ),
                }
            )
    return pd.DataFrame(rows)


def summarize_lifecycle(events: pd.DataFrame) -> pd.DataFrame:
    """Count FVG lifecycle states by instrument and segment."""
    if events.empty:
        return pd.DataFrame()
    return (
        events.groupby(["Instrument", "Segment", "Side", "LifecycleState"], as_index=False)
        .agg(Count=("EventID", "count"))
        .sort_values(["Instrument", "Segment", "Side", "LifecycleState"])
        .reset_index(drop=True)
    )


def evaluate_verdict(
    counts: pd.DataFrame,
    reproducibility: pd.DataFrame,
) -> dict[str, Any]:
    """Map reproducibility, sample floors, and base-rate sanity to a verdict.

    An instrument cannot pass while any of its segments is flagged as
    tautological (IFVGRate >= IFVG_TAUTOLOGY_RATE); under that base rate,
    'IFVG inversion' is not a meaningful selective event and EXP-021 must
    not be built on it without parameter tightening.
    """
    per_instrument: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        inst_counts = counts[counts["Instrument"] == instrument]
        reproducible = bool(
            reproducibility[
                reproducibility["Instrument"] == instrument
            ]["Reproducible"].all()
        )
        train_ready = bool(
            inst_counts[
                inst_counts["Segment"] == "Train"
            ]["ReadyForIFVGStudy"].any()
        )
        test_ready = bool(
            inst_counts[
                inst_counts["Segment"] == "Test"
            ]["ReadyForIFVGStudy"].any()
        )
        tautological = bool(inst_counts["Tautological"].any())
        fvg_common = bool(inst_counts["FVGFloorMet"].all())
        ifvg_sparse = bool(fvg_common and not (train_ready and test_ready) and not tautological)
        per_instrument.append(
            {
                "Instrument": instrument,
                "Reproducible": reproducible,
                "TrainReady": train_ready,
                "TestReady": test_ready,
                "Tautological": tautological,
                "FVGCommonIFVGSparse": ifvg_sparse,
                "Pass": (
                    reproducible
                    and train_ready
                    and test_ready
                    and not tautological
                ),
            }
        )
    verdict_df = pd.DataFrame(per_instrument)
    passing = int(verdict_df["Pass"].sum())
    reproducible_count = int(verdict_df["Reproducible"].sum())
    sparse_count = int(verdict_df["FVGCommonIFVGSparse"].sum())
    tautology_count = int(verdict_df["Tautological"].sum())
    if passing >= 3:
        verdict = "FOR"
    elif reproducible_count < 4:
        verdict = "AGAINST"
    elif tautology_count >= 1:
        # Even one tautological instrument means the IFVG concept is not
        # behaving selectively under the current parameterisation. Mark
        # the readiness gate as not cleared.
        verdict = "INCONCLUSIVE"
    elif sparse_count > 0:
        verdict = "INCONCLUSIVE"
    else:
        verdict = "AGAINST"
    return {
        "verdict": verdict,
        "instruments_passing": passing,
        "reproducible_instruments": reproducible_count,
        "fvg_common_ifvg_sparse_instruments": sparse_count,
        "tautological_instruments": tautology_count,
        "per_instrument": per_instrument,
    }


def _json_safe(value: Any) -> Any:
    """Convert numpy/pandas values to JSON-safe scalars."""
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if np.isfinite(value) else None
    if pd.isna(value):
        return None
    return value


def plot_count_bars(counts: pd.DataFrame, save_path: Path) -> None:
    """Plot FVG and IFVG counts by instrument and segment."""
    plot_df = counts.melt(
        id_vars=["Instrument", "Segment"],
        value_vars=["FVG_N", "IFVG_N"],
        var_name="EventType",
        value_name="Count",
    )
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=False)
    for ax, segment in zip(axes, ("Train", "Test")):
        sub = plot_df[plot_df["Segment"] == segment]
        sns.barplot(data=sub, x="Instrument", y="Count", hue="EventType", order=INSTRUMENTS, ax=ax)
        ax.axhline(MIN_FVG_PER_SEGMENT, color="steelblue", linestyle="--", linewidth=1)
        ax.axhline(MIN_IFVG_PER_SEGMENT, color="darkorange", linestyle="--", linewidth=1)
        ax.set_title(f"EXP-020 FVG/IFVG Counts - {segment}")
        ax.set_xlabel("")
        ax.legend(title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_size_distribution(events: pd.DataFrame, save_path: Path) -> None:
    """Plot FVG size distribution after deterministic outlier capping."""
    if events.empty:
        return
    cap = float(events["FVGSize"].quantile(PLOT_SIZE_QUANTILE))
    plot_df = events.copy()
    plot_df["FVGSizeCapped"] = plot_df["FVGSize"].clip(upper=cap)
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.boxplot(
        data=plot_df,
        x="Instrument",
        y="FVGSizeCapped",
        hue="Side",
        order=INSTRUMENTS,
        showfliers=False,
        ax=ax,
    )
    ax.set_title(f"EXP-020 FVG Size Distribution (capped at p{PLOT_SIZE_QUANTILE:.2f})")
    ax.set_xlabel("")
    ax.set_ylabel("FVG size")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_lifecycle_distribution(lifecycle: pd.DataFrame, save_path: Path) -> None:
    """Plot lifecycle state counts."""
    if lifecycle.empty:
        return
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=False)
    for ax, segment in zip(axes, ("Train", "Test")):
        sub = lifecycle[lifecycle["Segment"] == segment]
        sns.barplot(
            data=sub,
            x="Instrument",
            y="Count",
            hue="LifecycleState",
            order=INSTRUMENTS,
            ax=ax,
        )
        ax.set_title(f"EXP-020 Lifecycle States - {segment}")
        ax.set_xlabel("")
        ax.legend(title="", fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_duration_distribution(events: pd.DataFrame, save_path: Path) -> None:
    """Plot lifecycle tracking duration distribution."""
    if events.empty:
        return
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.histplot(data=events, x="TrackingBars", hue="LifecycleState", bins=30, ax=ax)
    ax.set_title("EXP-020 FVG Lifecycle Tracking Duration")
    ax.set_xlabel("Bars tracked after FVG formation")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def write_outputs(
    events: pd.DataFrame,
    counts: pd.DataFrame,
    lifecycle: pd.DataFrame,
    reproducibility: pd.DataFrame,
    precision_steps: dict[str, float],
    verdict: dict[str, Any],
    plots_dir: Path,
    results_dir: Path,
) -> None:
    """Write EXP-020 result tables, JSON summary, text summary, and plots."""
    events.to_csv(results_dir / "fvg_lifecycle_events.csv", index=False)
    counts.to_csv(results_dir / "count_readiness.csv", index=False)
    lifecycle.to_csv(results_dir / "lifecycle_counts.csv", index=False)
    reproducibility.to_csv(results_dir / "reproducibility_digest.csv", index=False)

    payload = {
        "experiment_id": "EXP-020",
        "title": "FVG IFVG Detection Reproducibility",
        "atr_period": ATR_PERIOD,
        "atr_size_coefficient": ATR_SIZE_COEFF,
        "lifecycle_bars": LIFECYCLE_BARS,
        "price_precision_steps": precision_steps,
        "definition": (
            "Bearish FVG: High[i] < Low[i-2]. Bullish FVG: Low[i] > High[i-2]. "
            "Minimum size is max(price_precision_step, 0.02 * prior ATR14). "
            "IFVG requires a later close through the opposite side within the "
            "120-bar lifecycle window."
        ),
        "verdict_summary": verdict,
        "count_readiness": counts.to_dict(orient="records"),
        "reproducibility": reproducibility.to_dict(orient="records"),
    }
    with (results_dir / "results.json").open("w", encoding="utf-8") as handle:
        json.dump(_json_safe(payload), handle, indent=2, default=str, allow_nan=False)

    with (results_dir / "numerical_summary.txt").open("w", encoding="utf-8") as handle:
        handle.write("EXP-020 FVG IFVG Detection Reproducibility\n")
        handle.write(f"Verdict: {verdict['verdict']}\n")
        handle.write(
            f"Instruments passing: {verdict['instruments_passing']}/4; "
            f"reproducible: {verdict['reproducible_instruments']}/4\n\n"
        )
        handle.write(
            f"Tautological (IFVGRate >= {IFVG_TAUTOLOGY_RATE:.2f}) instruments: "
            f"{verdict['tautological_instruments']}/4\n\n"
        )
        handle.write("Readiness by instrument and segment:\n")
        for row in counts.itertuples(index=False):
            rate_str = (
                f"{row.IFVGRate:.2f}" if np.isfinite(row.IFVGRate) else "n/a"
            )
            handle.write(
                f"- {row.Instrument} {row.Segment}: FVG={row.FVG_N}, "
                f"IFVG={row.IFVG_N} (rate={rate_str}), "
                f"ready={row.ReadyForIFVGStudy}, "
                f"tautological={row.Tautological}\n"
            )

    plot_count_bars(counts, plots_dir / "01_fvg_ifvg_counts.png")
    plot_size_distribution(events, plots_dir / "02_fvg_size_distribution.png")
    plot_lifecycle_distribution(lifecycle, plots_dir / "03_lifecycle_state_distribution.png")
    plot_duration_distribution(events, plots_dir / "04_zone_duration_distribution.png")


def run_experiment() -> None:
    """Execute the EXP-020 FVG/IFVG reproducibility workflow."""
    plots_dir = EXP_DIR / "plots"
    results_dir = EXP_DIR / "results"
    plots_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    bars_by_instrument: dict[str, PreparedBars] = {}
    precision_steps: dict[str, float] = {}
    event_parts: list[pd.DataFrame] = []
    for instrument in INSTRUMENTS:
        bars, precision_step = load_instrument_bars(instrument)
        bars_by_instrument[instrument] = bars
        precision_steps[instrument] = precision_step
        detected = detect_fvgs(bars, instrument, precision_step)
        event_parts.append(detected)
        LOGGER.info("%s: detected %d FVGs", instrument, len(detected))

    events = pd.concat(event_parts, ignore_index=True) if event_parts else pd.DataFrame()
    if events.empty:
        raise ValueError("No FVG events were detected.")

    reproducibility = verify_reproducibility(bars_by_instrument, precision_steps, events)
    counts = summarize_counts(events)
    lifecycle = summarize_lifecycle(events)
    verdict = evaluate_verdict(counts, reproducibility)

    write_outputs(
        events,
        counts,
        lifecycle,
        reproducibility,
        precision_steps,
        verdict,
        plots_dir,
        results_dir,
    )

    print("EXP-020 complete.")
    print(f"Verdict: {verdict['verdict']} ({verdict['instruments_passing']}/4 instruments)")
    print(f"Plots:   {plots_dir}")
    print(f"Results: {results_dir}")


def main() -> None:
    """Entry point for manual execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_experiment()


if __name__ == "__main__":
    main()
