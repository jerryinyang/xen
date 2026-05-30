"""
Experiment EXP-034: Prior-Range Location Readiness and Shared Aggregation-Coverage Rule
Implements the analysis plan from analysis-plan.md.

Readiness-only survey of the Prior-Range Location descriptor on 1h/4h real
bars aggregated from holdout-excluded 1-minute data:

- Feature: range_location = (Close - prior_low) / (prior_high - prior_low) over
  the prior 20 completed same-timeframe bars; buckets bottom <= 0.20,
  middle (0.20, 0.80), top >= 0.80 (fixed thresholds).
- Checks per (instrument, timeframe, aggregation, segment): determinism digest,
  row floors, independent-episode floors, denominator validity.
- Coverage: strict vs tolerant (min_coverage=0.90) dropped-window rate and the
  matched-window identical-bucket stability share (amendment 3).
- Canonical aggregation is selected mechanically from coverage/stability
  evidence only; no return, excursion, or P&L metric is computed.
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

from bar_aggregator import aggregate_ohlc  # noqa: E402
from ict_timebar import (  # noqa: E402
    INSTRUMENTS,
    load_analysis_timebars,
)


LOGGER = logging.getLogger(__name__)

DATA_DIR = PROJECT_ROOT / "data"
EXP_DIR = PYTHON_ROOT / "experiments" / "EXP-034"
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"

# ── Predeclared constants (frozen by scope.md) ────────────────────────────────

TIMEFRAMES = {"1h": 60, "4h": 240}
LOOKBACK_BARS = 20
BUCKET_BOTTOM_MAX = 0.20
BUCKET_TOP_MIN = 0.80
ANALYSIS_TRAIN_FRACTION = 0.70

AGGREGATIONS = {"strict": None, "tolerant": 0.90}
TOLERANT_COVERAGE = 0.90

MIN_ROWS_TRAIN = 100
MIN_ROWS_TEST = 50
MIN_EPISODES_TRAIN = 30
MIN_EPISODES_TEST = 15
STABILITY_THRESHOLD = 0.95
QUALIFYING_INSTRUMENT_FLOOR = 2

REPRODUCIBILITY_SHUFFLE_SEED = 42

BUCKETS = ("bottom", "middle", "top")
SEGMENTS = ("Train", "Test")

DIGEST_COLS = ["CloseTime", "RawLocation", "Bucket", "OutsideRange"]


@dataclass(frozen=True)
class FeatureFrame:
    """A holdout-excluded, feature-loaded higher-timeframe frame (pandas)."""

    instrument: str
    timeframe: str
    aggregation: str
    frame: pd.DataFrame
    source_1m_rows: int
    retained_windows: int


# ── Load / aggregate / feature pipeline ──────────────────────────────────────


def _load_1m(instrument: str, shuffle_seed: int | None) -> pl.DataFrame:
    """Load holdout-excluded 1-minute bars, optionally shuffled then resorted."""
    frame_1m = load_analysis_timebars(DATA_DIR, instrument).frame
    if shuffle_seed is not None and not frame_1m.is_empty():
        rng = np.random.default_rng(shuffle_seed)
        perm = rng.permutation(frame_1m.height).astype(np.int64)
        frame_1m = (
            frame_1m.with_columns(pl.Series("_PermKey", perm))
            .sort("_PermKey")
            .drop("_PermKey")
            .sort("CloseTime")
        )
    return frame_1m


def _add_segment(bars_tf: pl.DataFrame) -> pl.DataFrame:
    """Label Train/Test by chronological row on the aggregated series."""
    train_rows = int(bars_tf.height * ANALYSIS_TRAIN_FRACTION)
    return bars_tf.with_row_index("_Row").with_columns(
        pl.when(pl.col("_Row") < train_rows)
        .then(pl.lit("Train"))
        .otherwise(pl.lit("Test"))
        .alias("Segment")
    ).drop("_Row")


def _add_range_location(bars_tf: pl.DataFrame) -> pl.DataFrame:
    """Attach prior-range location feature, outside-range flag, and bucket."""
    with_prior = bars_tf.with_columns(
        pl.col("High")
        .rolling_max(window_size=LOOKBACK_BARS, min_samples=LOOKBACK_BARS)
        .shift(1)
        .alias("PriorHigh"),
        pl.col("Low")
        .rolling_min(window_size=LOOKBACK_BARS, min_samples=LOOKBACK_BARS)
        .shift(1)
        .alias("PriorLow"),
    ).with_columns(
        (pl.col("PriorHigh") - pl.col("PriorLow")).alias("Denom")
    )
    with_flags = with_prior.with_columns(
        (pl.col("Denom").is_null() | (pl.col("Denom") <= 0.0)).alias("Degenerate")
    ).with_columns(
        pl.when(pl.col("Degenerate"))
        .then(None)
        .otherwise((pl.col("Close") - pl.col("PriorLow")) / pl.col("Denom"))
        .alias("RawLocation")
    )
    return with_flags.with_columns(
        pl.when(pl.col("RawLocation").is_null())
        .then(False)
        .otherwise((pl.col("RawLocation") < 0.0) | (pl.col("RawLocation") > 1.0))
        .alias("OutsideRange"),
        pl.col("RawLocation").clip(0.0, 1.0).alias("ClippedLocation"),
    ).with_columns(
        pl.when(pl.col("RawLocation").is_null())
        .then(None)
        .when(pl.col("ClippedLocation") <= BUCKET_BOTTOM_MAX)
        .then(pl.lit("bottom"))
        .when(pl.col("ClippedLocation") >= BUCKET_TOP_MIN)
        .then(pl.lit("top"))
        .otherwise(pl.lit("middle"))
        .alias("Bucket")
    )


def _build_feature_frame(
    instrument: str,
    timeframe: str,
    aggregation: str,
    *,
    shuffle_seed: int | None = None,
) -> FeatureFrame:
    """Load, aggregate, and feature one (instrument, timeframe, aggregation)."""
    frame_1m = _load_1m(instrument, shuffle_seed)
    source_rows = int(frame_1m.height)
    bars_tf = aggregate_ohlc(
        frame_1m,
        period_minutes=TIMEFRAMES[timeframe],
        min_coverage=AGGREGATIONS[aggregation],
    )
    retained = int(bars_tf.height)
    if bars_tf.is_empty():
        empty = pd.DataFrame(
            columns=["CloseTime", "Segment", "RawLocation", "ClippedLocation",
                     "OutsideRange", "Degenerate", "Bucket"]
        )
        return FeatureFrame(instrument, timeframe, aggregation, empty, source_rows, 0)
    featured = _add_range_location(_add_segment(bars_tf))
    pdf = featured.select(
        ["CloseTime", "Segment", "RawLocation", "ClippedLocation",
         "OutsideRange", "Degenerate", "Bucket"]
    ).to_pandas()
    return FeatureFrame(instrument, timeframe, aggregation, pdf, source_rows, retained)


# ── Counts, episodes, digests ────────────────────────────────────────────────


def _episode_counts(bucket_seq: list[Any]) -> dict[str, int]:
    """Count maximal runs of consecutive same-bucket bars; None breaks runs."""
    counts = {b: 0 for b in BUCKETS}
    prev = None
    for bucket in bucket_seq:
        if bucket is None or (isinstance(bucket, float) and np.isnan(bucket)):
            prev = None
            continue
        if bucket != prev:
            counts[bucket] += 1
        prev = bucket
    return counts


def _segment_stats(seg_df: pd.DataFrame) -> dict[str, Any]:
    """Row counts, episode counts, outside-range and degenerate shares."""
    eligible = seg_df[seg_df["Bucket"].notna()]
    row_counts = {b: int((eligible["Bucket"] == b).sum()) for b in BUCKETS}
    episodes = _episode_counts(list(seg_df["Bucket"]))
    non_finite_eligible = int(
        (~np.isfinite(eligible["RawLocation"].to_numpy(dtype=float))).sum()
    ) if len(eligible) else 0
    outside_rate = (
        float(eligible["OutsideRange"].mean()) if len(eligible) else np.nan
    )
    denom_defined = seg_df["Degenerate"].notna()
    flat_count = int((seg_df["Degenerate"] & denom_defined).sum())
    degenerate_share = (
        flat_count / int(denom_defined.sum()) if int(denom_defined.sum()) else np.nan
    )
    return {
        "row_counts": row_counts,
        "episodes": episodes,
        "outside_rate": outside_rate,
        "degenerate_share": degenerate_share,
        "non_finite_eligible": non_finite_eligible,
    }


def _digest_segment(seg_df: pd.DataFrame) -> str:
    """Stable SHA-256 of the segment feature table on the digest columns."""
    if seg_df.empty:
        return hashlib.sha256(b"EMPTY").hexdigest()
    stable = seg_df[DIGEST_COLS].sort_values(DIGEST_COLS, na_position="first").copy()
    text = stable.to_csv(index=False, float_format="%.12g")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ── Coverage diagnostics and strict-vs-tolerant stability ────────────────────


def _coverage_row(
    instrument: str,
    timeframe: str,
    strict: FeatureFrame,
    tolerant: FeatureFrame,
) -> dict[str, Any]:
    """Dropped-window rates and matched-window identical-bucket share."""
    period = TIMEFRAMES[timeframe]
    expected = strict.source_1m_rows // period if strict.source_1m_rows else 0
    strict_dropped = (
        1.0 - strict.retained_windows / expected if expected else np.nan
    )
    tolerant_dropped = (
        1.0 - tolerant.retained_windows / expected if expected else np.nan
    )
    merged = strict.frame[["CloseTime", "Bucket"]].merge(
        tolerant.frame[["CloseTime", "Bucket"]],
        on="CloseTime", how="inner", suffixes=("_strict", "_tol"),
    )
    both_bucketed = merged[
        merged["Bucket_strict"].notna() & merged["Bucket_tol"].notna()
    ]
    identical_share = (
        float((both_bucketed["Bucket_strict"] == both_bucketed["Bucket_tol"]).mean())
        if len(both_bucketed)
        else np.nan
    )
    return {
        "Instrument": instrument,
        "Timeframe": timeframe,
        "ExpectedWindows": int(expected),
        "StrictRetained": strict.retained_windows,
        "TolerantRetained": tolerant.retained_windows,
        "StrictDroppedRate": strict_dropped,
        "TolerantDroppedRate": tolerant_dropped,
        "MatchedWindows": int(len(both_bucketed)),
        "IdenticalBucketShare": identical_share,
        "ToleranceStable": bool(
            np.isfinite(identical_share) and identical_share >= STABILITY_THRESHOLD
        ),
    }


# ── Readiness table ──────────────────────────────────────────────────────────


def _readiness_rows(
    feature: FeatureFrame,
    digests_match_by_segment: dict[str, bool],
) -> list[dict[str, Any]]:
    """One readiness row per (instrument, timeframe, aggregation, segment)."""
    rows: list[dict[str, Any]] = []
    for segment in SEGMENTS:
        seg_df = feature.frame[feature.frame["Segment"] == segment]
        stats = _segment_stats(seg_df)
        min_rows = MIN_ROWS_TRAIN if segment == "Train" else MIN_ROWS_TEST
        min_eps = MIN_EPISODES_TRAIN if segment == "Train" else MIN_EPISODES_TEST
        row_floor = all(stats["row_counts"][b] >= min_rows for b in BUCKETS)
        episode_floor = all(stats["episodes"][b] >= min_eps for b in BUCKETS)
        denom_valid = stats["non_finite_eligible"] == 0
        rows.append(
            {
                "Instrument": feature.instrument,
                "Timeframe": feature.timeframe,
                "Aggregation": feature.aggregation,
                "Segment": segment,
                "NBottom": stats["row_counts"]["bottom"],
                "NMiddle": stats["row_counts"]["middle"],
                "NTop": stats["row_counts"]["top"],
                "EpBottom": stats["episodes"]["bottom"],
                "EpMiddle": stats["episodes"]["middle"],
                "EpTop": stats["episodes"]["top"],
                "OutsideRangeRate": stats["outside_rate"],
                "DegenerateShare": stats["degenerate_share"],
                "Check1Determinism": bool(digests_match_by_segment[segment]),
                "Check2RowFloor": bool(row_floor),
                "Check3EpisodeFloor": bool(episode_floor),
                "Check4DenominatorValid": bool(denom_valid),
                "PassesAllChecks": bool(
                    digests_match_by_segment[segment]
                    and row_floor
                    and episode_floor
                    and denom_valid
                ),
            }
        )
    return rows


def _instrument_passes(
    readiness: pd.DataFrame,
    instrument: str,
    timeframe: str,
    aggregation: str,
) -> bool:
    """True iff both segments pass all checks for this cell."""
    cells = readiness[
        (readiness["Instrument"] == instrument)
        & (readiness["Timeframe"] == timeframe)
        & (readiness["Aggregation"] == aggregation)
    ]
    if len(cells) != len(SEGMENTS):
        return False
    return bool(cells["PassesAllChecks"].all())


# ── Canonical aggregation selection and aggregate verdict ────────────────────


def _select_and_verdict(
    readiness: pd.DataFrame,
    coverage: pd.DataFrame,
) -> dict[str, Any]:
    """Pick canonical aggregation per timeframe, then apply the aggregate verdict."""
    canonical: dict[str, dict[str, Any]] = {}
    for timeframe in TIMEFRAMES:
        strict_pass = [
            inst for inst in INSTRUMENTS
            if _instrument_passes(readiness, inst, timeframe, "strict")
        ]
        if len(strict_pass) >= QUALIFYING_INSTRUMENT_FLOOR:
            canonical[timeframe] = {
                "aggregation": "strict",
                "passing_instruments": strict_pass,
                "status": "ready",
            }
            continue
        cov_tf = coverage[coverage["Timeframe"] == timeframe]
        stable_instruments = list(
            cov_tf[cov_tf["ToleranceStable"]]["Instrument"]
        )
        tolerant_pass = [
            inst for inst in INSTRUMENTS
            if _instrument_passes(readiness, inst, timeframe, "tolerant")
        ]
        tolerant_admissible = len(stable_instruments) >= QUALIFYING_INSTRUMENT_FLOOR
        tolerant_ready = [i for i in tolerant_pass if i in stable_instruments]
        if tolerant_admissible and len(tolerant_ready) >= QUALIFYING_INSTRUMENT_FLOOR:
            canonical[timeframe] = {
                "aggregation": "tolerant",
                "passing_instruments": tolerant_ready,
                "status": "ready",
            }
        elif not tolerant_admissible:
            canonical[timeframe] = {
                "aggregation": "strict",
                "passing_instruments": strict_pass,
                "status": "coverage_blocked",
            }
        else:
            canonical[timeframe] = {
                "aggregation": "strict",
                "passing_instruments": strict_pass,
                "status": "insufficient_instruments",
            }

    ready_timeframes = {
        tf: info for tf, info in canonical.items()
        if info["status"] == "ready"
        and len(info["passing_instruments"]) >= QUALIFYING_INSTRUMENT_FLOOR
    }
    single_pass = any(
        0 < len(info["passing_instruments"]) < QUALIFYING_INSTRUMENT_FLOOR
        for info in canonical.values()
    )
    if ready_timeframes:
        verdict_text = (
            "Prior-Range Location READY: >=2 distinct instruments pass on "
            f"timeframe(s) {sorted(ready_timeframes)}; advances to mid-phase reflection."
        )
        passes = True
    elif single_pass:
        verdict_text = (
            "INCONCLUSIVE: only a single instrument passes on a promising "
            "timeframe; the >=2 distinct-instrument rule is unmet."
        )
        passes = False
    else:
        verdict_text = (
            "Prior-Range Location readiness-gated NO-GO: no timeframe has >=2 "
            "distinct passing instruments under an admissible aggregation."
        )
        passes = False
    return {
        "verdict_text": verdict_text,
        "passes_readiness": passes,
        "canonical_aggregation_per_timeframe": canonical,
    }


# ── Plotting helpers (bounded inputs only) ───────────────────────────────────


def _plot_coverage_stability(coverage: pd.DataFrame, save_path: Path) -> None:
    """Dropped-window rates (left) and matched-bucket stability share (right)."""
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    labels = [f"{r.Instrument}-{r.Timeframe}" for r in coverage.itertuples(index=False)]
    x = np.arange(len(labels))
    width = 0.4
    axes[0].bar(x - width / 2, coverage["StrictDroppedRate"], width, color="#3a7bd5", label="Strict")
    axes[0].bar(x + width / 2, coverage["TolerantDroppedRate"], width, color="#f39c12", label="Tolerant 0.90")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    axes[0].set_ylabel("Dropped-window rate")
    axes[0].set_title("Aggregation coverage loss")
    axes[0].legend(fontsize=8)
    axes[1].bar(x, coverage["IdenticalBucketShare"], width=0.6, color="#5cb85c")
    axes[1].axhline(STABILITY_THRESHOLD, color="red", linestyle="--", linewidth=1,
                    label=f"Admissibility {STABILITY_THRESHOLD}")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    axes[1].set_ylabel("Matched-window identical-bucket share")
    axes[1].set_ylim(0.0, 1.02)
    axes[1].set_title("Strict-vs-tolerant feature stability")
    axes[1].legend(fontsize=8)
    fig.suptitle("EXP-034: Coverage and feature-stability (canonical-aggregation inputs)", fontsize=13)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_location_distribution(
    features: dict[tuple[str, str], FeatureFrame],
    save_path: Path,
) -> None:
    """2x4 grid of clipped range-location histograms (strict aggregation)."""
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 4, figsize=(18, 8), sharex=True)
    for col, instrument in enumerate(INSTRUMENTS):
        for row, timeframe in enumerate(TIMEFRAMES):
            ax = axes[row, col]
            feature = features[(instrument, timeframe)]
            vals = feature.frame["ClippedLocation"].dropna().to_numpy(dtype=float)
            if vals.size:
                ax.hist(vals, bins=40, color="#3a7bd5", alpha=0.8)
            ax.axvline(BUCKET_BOTTOM_MAX, color="red", linestyle="--", linewidth=1)
            ax.axvline(BUCKET_TOP_MIN, color="red", linestyle="--", linewidth=1)
            ax.set_title(f"{instrument} {timeframe} (n={vals.size:,})", fontsize=9)
            if row == 1:
                ax.set_xlabel("Clipped range-location")
            if col == 0:
                ax.set_ylabel("Bars")
    fig.suptitle("EXP-034: Range-location distribution (strict aggregation, buckets 0.20/0.80)", fontsize=13)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _count_matrix(readiness: pd.DataFrame, aggregation: str, prefix: str) -> pd.DataFrame:
    """Pivot bucket counts into a (bucket x instrument-timeframe-segment) matrix."""
    cols = [f"{i}-{tf}-{s}" for i in INSTRUMENTS for tf in TIMEFRAMES for s in SEGMENTS]
    matrix = pd.DataFrame(index=list(BUCKETS), columns=cols, dtype=float)
    subset = readiness[readiness["Aggregation"] == aggregation]
    for r in subset.itertuples(index=False):
        col = f"{r.Instrument}-{r.Timeframe}-{r.Segment}"
        matrix.loc["bottom", col] = getattr(r, f"{prefix}Bottom")
        matrix.loc["middle", col] = getattr(r, f"{prefix}Middle")
        matrix.loc["top", col] = getattr(r, f"{prefix}Top")
    return matrix


def _plot_count_matrix(readiness: pd.DataFrame, save_path: Path) -> None:
    """Heatmap of per-bucket row counts (strict aggregation)."""
    sns.set_theme(style="white")
    matrix = _count_matrix(readiness, "strict", "N")
    fig, ax = plt.subplots(figsize=(15, 4))
    sns.heatmap(matrix.astype(float), annot=True, fmt=".0f", cmap="Blues",
                cbar_kws={"label": "Row count"}, annot_kws={"size": 7}, ax=ax)
    ax.set_title("EXP-034: Bucket row counts (strict) — floors 100 train / 50 test")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right", fontsize=7)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_episode_grid(readiness: pd.DataFrame, save_path: Path) -> None:
    """Heatmap of per-bucket independent-episode counts (strict aggregation)."""
    sns.set_theme(style="white")
    matrix = _count_matrix(readiness, "strict", "Ep")
    fig, ax = plt.subplots(figsize=(15, 4))
    sns.heatmap(matrix.astype(float), annot=True, fmt=".0f", cmap="Greens",
                cbar_kws={"label": "Independent episodes"}, annot_kws={"size": 7}, ax=ax)
    ax.set_title("EXP-034: Bucket independent-episode counts (strict) — floors 30 train / 15 test")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right", fontsize=7)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ── Orchestration ────────────────────────────────────────────────────────────


def _json_safe(value: Any) -> Any:
    """Convert numpy/pandas scalars to plain Python for JSON."""
    if value is None:
        return None
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    return value


def run_experiment() -> None:
    """Execute the EXP-034 readiness survey end to end."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    readiness_rows: list[dict[str, Any]] = []
    coverage_rows: list[dict[str, Any]] = []
    strict_features: dict[tuple[str, str], FeatureFrame] = {}

    for instrument in INSTRUMENTS:
        for timeframe in TIMEFRAMES:
            feats: dict[str, FeatureFrame] = {}
            for aggregation in AGGREGATIONS:
                LOGGER.info(
                    "EXP-034: %s %s %s — canonical + shuffled passes",
                    instrument, timeframe, aggregation,
                )
                canonical = _build_feature_frame(instrument, timeframe, aggregation)
                shuffled = _build_feature_frame(
                    instrument, timeframe, aggregation,
                    shuffle_seed=REPRODUCIBILITY_SHUFFLE_SEED,
                )
                digests_match = {
                    seg: (
                        _digest_segment(canonical.frame[canonical.frame["Segment"] == seg])
                        == _digest_segment(shuffled.frame[shuffled.frame["Segment"] == seg])
                    )
                    for seg in SEGMENTS
                }
                readiness_rows.extend(_readiness_rows(canonical, digests_match))
                feats[aggregation] = canonical
            strict_features[(instrument, timeframe)] = feats["strict"]
            coverage_rows.append(
                _coverage_row(instrument, timeframe, feats["strict"], feats["tolerant"])
            )

    readiness = pd.DataFrame(readiness_rows)
    coverage = pd.DataFrame(coverage_rows)
    verdict = _select_and_verdict(readiness, coverage)

    LOGGER.info("EXP-034: writing outputs")
    readiness.to_csv(RESULTS_DIR / "readiness_table.csv", index=False)
    coverage.to_csv(RESULTS_DIR / "coverage_stability.csv", index=False)
    (RESULTS_DIR / "verdict.json").write_text(
        json.dumps(
            {
                "verdict_text": verdict["verdict_text"],
                "passes_readiness": verdict["passes_readiness"],
                "canonical_aggregation_per_timeframe": verdict[
                    "canonical_aggregation_per_timeframe"
                ],
                "thresholds": {
                    "lookback_bars": LOOKBACK_BARS,
                    "bucket_bottom_max": BUCKET_BOTTOM_MAX,
                    "bucket_top_min": BUCKET_TOP_MIN,
                    "min_rows_train": MIN_ROWS_TRAIN,
                    "min_rows_test": MIN_ROWS_TEST,
                    "min_episodes_train": MIN_EPISODES_TRAIN,
                    "min_episodes_test": MIN_EPISODES_TEST,
                    "stability_threshold": STABILITY_THRESHOLD,
                    "tolerant_coverage": TOLERANT_COVERAGE,
                },
            },
            indent=2,
            default=_json_safe,
        )
    )

    LOGGER.info("EXP-034: rendering plots")
    _plot_coverage_stability(coverage, PLOTS_DIR / "01_coverage_stability.png")
    _plot_location_distribution(strict_features, PLOTS_DIR / "02_location_distribution.png")
    _plot_count_matrix(readiness, PLOTS_DIR / "03_bucket_count_matrix.png")
    _plot_episode_grid(readiness, PLOTS_DIR / "04_episode_count_grid.png")

    _print_summary(readiness, coverage, verdict)


def _print_summary(
    readiness: pd.DataFrame,
    coverage: pd.DataFrame,
    verdict: dict[str, Any],
) -> None:
    """Concise manual-run summary."""
    print("\n=== EXP-034 coverage and stability ===")
    print(coverage.to_string(index=False))
    print("\n=== EXP-034 readiness (strict aggregation) ===")
    strict = readiness[readiness["Aggregation"] == "strict"][
        ["Instrument", "Timeframe", "Segment", "NBottom", "NMiddle", "NTop",
         "EpBottom", "EpMiddle", "EpTop", "PassesAllChecks"]
    ]
    print(strict.to_string(index=False))
    print("\n=== EXP-034 verdict ===")
    print(verdict["verdict_text"])
    for tf, info in verdict["canonical_aggregation_per_timeframe"].items():
        print(f"  {tf}: {info['status']} via {info['aggregation']} "
              f"-> passing {info['passing_instruments']}")


def main() -> None:
    """Configure logging and run the experiment."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run_experiment()


if __name__ == "__main__":
    main()
