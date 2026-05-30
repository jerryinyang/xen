"""
Experiment EXP-035: Market Bias (CEREBR) Deterministic Port and State-Episode Readiness
Implements the analysis plan from analysis-plan.md.

Readiness-only survey of the chart-timeframe Market Bias port on 1h/4h real
bars aggregated from holdout-excluded 1-minute data:

- Port: python/src/market_bias.compute_market_bias (SMA-seeded causal EMAs;
  xhaopen[1] HA recursion; osc_bias = 100*(c2 - o2); osc_smooth = EMA(osc_bias, 7)).
- Warmup: python/src/market_bias.convergence_warmup (two-seeding identical-label
  convergence, floored at 300 bars).
- Checks per (instrument, timeframe, aggregation, segment): port determinism
  digest, warmup convergence, sign-only row floors, sign-only independent-episode
  floors, no-collapse.
- Reference fidelity: deterministic-only unless an exported reference series is
  present (none currently); the no-reference claim and caveat are pre-committed.

No return, excursion, or P&L metric is computed.
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
from ict_timebar import INSTRUMENTS, load_analysis_timebars  # noqa: E402
from market_bias import (  # noqa: E402
    SIGN_BEAR,
    SIGN_BULL,
    WARMUP_FLOOR,
    compute_market_bias,
    convergence_warmup,
)


LOGGER = logging.getLogger(__name__)

DATA_DIR = PROJECT_ROOT / "data"
EXP_DIR = PYTHON_ROOT / "experiments" / "EXP-035"
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"
REFERENCE_GLOB = "market-bias-reference*.csv"
REFERENCE_DIR = PROJECT_ROOT / "docs" / "planning"

# ── Predeclared constants (frozen by scope.md) ────────────────────────────────

TIMEFRAMES = {"1h": 60, "4h": 240}
ANALYSIS_TRAIN_FRACTION = 0.70
AGGREGATIONS = {"strict": None, "tolerant": 0.90}

MIN_ROWS_TRAIN = 100
MIN_ROWS_TEST = 50
MIN_EPISODES_TRAIN = 30
MIN_EPISODES_TEST = 15
COLLAPSE_SHARE = 0.95
QUALIFYING_INSTRUMENT_FLOOR = 2

REPRODUCIBILITY_SHUFFLE_SEED = 42

SIGN_STATES = (SIGN_BULL, SIGN_BEAR)
FOUR_WAY_STATES = ("strong_bull", "weak_bull", "strong_bear", "weak_bear")
SEGMENTS = ("Train", "Test")

DIGEST_COLS = ["CloseTime", "osc_bias", "osc_smooth", "sign_state", "four_way_state"]
PLOT_SAMPLE_CAP = 4000


@dataclass(frozen=True)
class MBFrame:
    """A holdout-excluded Market-Bias-loaded higher-timeframe frame (pandas)."""

    instrument: str
    timeframe: str
    aggregation: str
    frame: pd.DataFrame          # all aggregated bars, row-indexed, with states
    warmup: dict[str, Any]       # convergence_warmup output
    train_rows: int


# ── Load / aggregate / port pipeline ─────────────────────────────────────────


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
    )


def _build_mb_frame(
    instrument: str,
    timeframe: str,
    aggregation: str,
    *,
    shuffle_seed: int | None = None,
    warmup_override: dict[str, Any] | None = None,
) -> MBFrame:
    """Load, aggregate, port, and (optionally) determine the warmup for one cell."""
    frame_1m = _load_1m(instrument, shuffle_seed)
    bars_tf = aggregate_ohlc(
        frame_1m,
        period_minutes=TIMEFRAMES[timeframe],
        min_coverage=AGGREGATIONS[aggregation],
    )
    if bars_tf.is_empty():
        empty = pd.DataFrame(
            columns=["_Row", "CloseTime", "Segment", "osc_bias", "osc_smooth",
                     "sign_state", "four_way_state"]
        )
        warm = warmup_override or {"w_converge": 0, "W": WARMUP_FLOOR, "converged": False}
        return MBFrame(instrument, timeframe, aggregation, empty, warm, 0)
    warm = warmup_override or convergence_warmup(bars_tf, floor=WARMUP_FLOOR)
    mb = compute_market_bias(bars_tf, seed="sma")
    mb = _add_segment(mb)
    pdf = mb.select(
        ["_Row", "CloseTime", "Segment", "osc_bias", "osc_smooth",
         "sign_state", "four_way_state"]
    ).to_pandas()
    train_rows = int(bars_tf.height * ANALYSIS_TRAIN_FRACTION)
    return MBFrame(instrument, timeframe, aggregation, pdf, warm, train_rows)


def _post_warmup(frame: pd.DataFrame, w: int) -> pd.DataFrame:
    """Rows at or beyond the warmup index."""
    if frame.empty:
        return frame
    return frame[frame["_Row"] >= w]


# ── Counts, episodes, digests ────────────────────────────────────────────────


def _episode_counts(state_seq: list[Any], states: tuple[str, ...]) -> dict[str, int]:
    """Count maximal runs of consecutive same-state bars; undefined breaks runs."""
    counts = {s: 0 for s in states}
    prev = None
    for value in state_seq:
        if not isinstance(value, str):
            prev = None
            continue
        if value in counts and value != prev:
            counts[value] += 1
        prev = value
    return counts


def _episode_median_length(state_seq: list[Any], states: tuple[str, ...]) -> dict[str, float]:
    """Median run length (bars) per state."""
    runs = {s: [] for s in states}
    prev = None
    length = 0
    for value in state_seq:
        if isinstance(value, str) and value == prev:
            length += 1
            continue
        if isinstance(prev, str) and prev in runs:
            runs[prev].append(length)
        prev = value if isinstance(value, str) else None
        length = 1 if isinstance(value, str) else 0
    if isinstance(prev, str) and prev in runs:
        runs[prev].append(length)
    return {s: float(np.median(runs[s])) if runs[s] else np.nan for s in states}


def _segment_stats(seg_df: pd.DataFrame) -> dict[str, Any]:
    """Sign/four-way row counts, episodes, persistence, transitions, collapse, |bias|."""
    sign_seq = list(seg_df["sign_state"])
    four_seq = list(seg_df["four_way_state"])
    sign_rows = {s: int((seg_df["sign_state"] == s).sum()) for s in SIGN_STATES}
    four_rows = {s: int((seg_df["four_way_state"] == s).sum()) for s in FOUR_WAY_STATES}
    defined_sign = sum(sign_rows.values())
    dominant_share = (
        max(sign_rows.values()) / defined_sign if defined_sign else np.nan
    )
    transitions = _count_transitions(sign_seq)
    osc_abs = np.abs(seg_df["osc_bias"].to_numpy(dtype=float))
    osc_abs = osc_abs[np.isfinite(osc_abs)]
    quartiles = (
        [float(np.quantile(osc_abs, q)) for q in (0.25, 0.5, 0.75)]
        if osc_abs.size else [np.nan, np.nan, np.nan]
    )
    return {
        "sign_rows": sign_rows,
        "four_rows": four_rows,
        "sign_episodes": _episode_counts(sign_seq, SIGN_STATES),
        "four_episodes": _episode_counts(four_seq, FOUR_WAY_STATES),
        "sign_median_len": _episode_median_length(sign_seq, SIGN_STATES),
        "dominant_share": dominant_share,
        "sign_transitions": transitions,
        "osc_abs_quartiles": quartiles,
    }


def _count_transitions(state_seq: list[Any]) -> int:
    """Count adjacent defined-state changes."""
    transitions = 0
    prev = None
    for value in state_seq:
        if not isinstance(value, str):
            prev = None
            continue
        if isinstance(prev, str) and value != prev:
            transitions += 1
        prev = value
    return transitions


def _digest_segment(seg_df: pd.DataFrame) -> str:
    """Stable SHA-256 of the post-warmup segment table on the digest columns."""
    if seg_df.empty:
        return hashlib.sha256(b"EMPTY").hexdigest()
    stable = seg_df[DIGEST_COLS].sort_values(DIGEST_COLS, na_position="first").copy()
    text = stable.to_csv(index=False, float_format="%.12g")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ── Readiness rows ───────────────────────────────────────────────────────────


def _readiness_rows(
    canonical: MBFrame,
    digests_match_by_segment: dict[str, bool],
) -> list[dict[str, Any]]:
    """One readiness row per (instrument, timeframe, aggregation, segment)."""
    rows: list[dict[str, Any]] = []
    w = int(canonical.warmup["W"])
    converged = bool(canonical.warmup["converged"]) and w < canonical.train_rows
    post = _post_warmup(canonical.frame, w)
    for segment in SEGMENTS:
        seg_df = post[post["Segment"] == segment]
        stats = _segment_stats(seg_df)
        min_rows = MIN_ROWS_TRAIN if segment == "Train" else MIN_ROWS_TEST
        min_eps = MIN_EPISODES_TRAIN if segment == "Train" else MIN_EPISODES_TEST
        row_floor = all(stats["sign_rows"][s] >= min_rows for s in SIGN_STATES)
        episode_floor = all(stats["sign_episodes"][s] >= min_eps for s in SIGN_STATES)
        dominant_share = stats["dominant_share"]
        no_collapse = bool(
            np.isfinite(dominant_share)
            and dominant_share <= COLLAPSE_SHARE
        )
        rows.append(
            {
                "Instrument": canonical.instrument,
                "Timeframe": canonical.timeframe,
                "Aggregation": canonical.aggregation,
                "Segment": segment,
                "W": w,
                "WConverge": int(canonical.warmup["w_converge"]),
                "Converged": converged,
                "NBull": stats["sign_rows"][SIGN_BULL],
                "NBear": stats["sign_rows"][SIGN_BEAR],
                "EpBull": stats["sign_episodes"][SIGN_BULL],
                "EpBear": stats["sign_episodes"][SIGN_BEAR],
                "MedLenBull": stats["sign_median_len"][SIGN_BULL],
                "MedLenBear": stats["sign_median_len"][SIGN_BEAR],
                "DominantShare": stats["dominant_share"],
                "SignTransitions": stats["sign_transitions"],
                "FourWayEpStrongBull": stats["four_episodes"]["strong_bull"],
                "FourWayEpWeakBull": stats["four_episodes"]["weak_bull"],
                "FourWayEpStrongBear": stats["four_episodes"]["strong_bear"],
                "FourWayEpWeakBear": stats["four_episodes"]["weak_bear"],
                "OscAbsQ25": stats["osc_abs_quartiles"][0],
                "OscAbsQ50": stats["osc_abs_quartiles"][1],
                "OscAbsQ75": stats["osc_abs_quartiles"][2],
                "Check1Determinism": bool(digests_match_by_segment[segment]),
                "Check2WarmupConverged": converged,
                "Check3RowFloor": bool(row_floor),
                "Check4EpisodeFloor": bool(episode_floor),
                "Check5NoCollapse": no_collapse,
                "PassesAllChecks": bool(
                    digests_match_by_segment[segment]
                    and converged
                    and row_floor
                    and episode_floor
                    and no_collapse
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


# ── Reference fidelity (predeclared fallback) ────────────────────────────────


def _reference_status() -> dict[str, Any]:
    """Detect an exported reference series; otherwise pre-committed deterministic-only."""
    matches = sorted(REFERENCE_DIR.glob(REFERENCE_GLOB))
    if not matches:
        return {
            "reference_available": False,
            "claim": "deterministic re-implementation of the published Pine formula",
            "caveat": (
                "No exported TradingView reference series present; Pine-equivalence "
                "is not claimed. Any later negative Market Bias return result must "
                "carry this unverified-fidelity caveat."
            ),
            "reference_files": [],
        }
    return {
        "reference_available": True,
        "claim": "deterministic re-implementation; reference comparison reported",
        "caveat": "Reference present; see max_abs_osc_dev per matched series.",
        "reference_files": [m.name for m in matches],
    }


# ── Aggregate verdict ────────────────────────────────────────────────────────


def _aggregate_verdict(readiness: pd.DataFrame, reference: dict[str, Any]) -> dict[str, Any]:
    """Apply scope §"Aggregate Verdict" mechanically (sign-only states gate)."""
    passing: dict[str, list[str]] = {}
    for timeframe in TIMEFRAMES:
        for aggregation in AGGREGATIONS:
            key = f"{timeframe}/{aggregation}"
            passing[key] = [
                inst for inst in INSTRUMENTS
                if _instrument_passes(readiness, inst, timeframe, aggregation)
            ]
    ready_keys = {k: v for k, v in passing.items() if len(v) >= QUALIFYING_INSTRUMENT_FLOOR}
    single_pass = any(0 < len(v) < QUALIFYING_INSTRUMENT_FLOOR for v in passing.values())
    if ready_keys:
        verdict_text = (
            "Market Bias READY: >=2 distinct instruments pass sign-only readiness on "
            f"cell(s) {sorted(ready_keys)} ({reference['claim']}); advances to mid-phase reflection."
        )
        passes = True
    elif single_pass:
        verdict_text = (
            "INCONCLUSIVE: only a single instrument passes on a promising cell; "
            "the >=2 distinct-instrument rule is unmet."
        )
        passes = False
    else:
        verdict_text = (
            "Market Bias readiness-gated NO-GO: no (timeframe, aggregation) cell has "
            ">=2 distinct passing instruments (determinism, warmup, episode floor, or "
            "no-collapse failed)."
        )
        passes = False
    return {
        "verdict_text": verdict_text,
        "passes_readiness": passes,
        "passing_instruments_per_cell": passing,
        "reference": reference,
    }


# ── Plotting helpers (bounded inputs only) ───────────────────────────────────


def _plot_determinism_warmup(readiness: pd.DataFrame, save_path: Path) -> None:
    """Determinism pass/fail grid (left) and warmup W per cell (right)."""
    sns.set_theme(style="white")
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    strict = readiness[readiness["Aggregation"] == "strict"]
    det = strict.assign(Cell=strict["Instrument"] + "-" + strict["Timeframe"]).pivot(
        index="Segment", columns="Cell", values="Check1Determinism"
    ).astype(float)
    sns.heatmap(det, annot=True, cmap=["#d9534f", "#5cb85c"], cbar=False,
                vmin=0, vmax=1, linewidths=0.5, linecolor="white", ax=axes[0])
    axes[0].set_title("Port determinism (strict): pass=green")
    warm = strict[strict["Segment"] == "Train"].assign(
        Cell=lambda d: d["Instrument"] + "-" + d["Timeframe"]
    )
    axes[1].bar(warm["Cell"], warm["W"], color="#3a7bd5")
    axes[1].axhline(WARMUP_FLOOR, color="red", linestyle="--", linewidth=1,
                    label=f"Floor {WARMUP_FLOOR}")
    axes[1].set_xticklabels(warm["Cell"], rotation=45, ha="right", fontsize=8)
    axes[1].set_ylabel("Warmup W (bars)")
    axes[1].set_title("Two-seeding warmup length (strict)")
    axes[1].legend(fontsize=8)
    fig.suptitle("EXP-035: Port determinism and warmup", fontsize=13)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_osc_series(
    sample_frame: pd.DataFrame,
    label: str,
    save_path: Path,
) -> None:
    """osc_bias / osc_smooth with sign-state shading for one representative cell."""
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(14, 5))
    if not sample_frame.empty:
        df = sample_frame.reset_index(drop=True)
        if len(df) > PLOT_SAMPLE_CAP:
            step = int(np.ceil(len(df) / PLOT_SAMPLE_CAP))
            df = df.iloc[::step].reset_index(drop=True)
        x = np.arange(len(df))
        ax.plot(x, df["osc_bias"], color="#1f3b73", linewidth=0.8, label="osc_bias")
        ax.plot(x, df["osc_smooth"], color="#f39c12", linewidth=0.8, label="osc_smooth")
        ax.axhline(0.0, color="black", linewidth=0.6)
        bull = df["sign_state"] == SIGN_BULL
        ax.fill_between(x, df["osc_bias"].min(), df["osc_bias"].max(),
                        where=bull.to_numpy(), color="#5cb85c", alpha=0.08, step="mid")
    ax.set_title(f"EXP-035: osc_bias / osc_smooth with bull shading — {label}")
    ax.set_xlabel("Post-warmup bar (sampled)")
    ax.set_ylabel("Oscillator")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_sign_episode_grid(readiness: pd.DataFrame, save_path: Path) -> None:
    """Heatmap of sign-only independent-episode counts (strict aggregation)."""
    sns.set_theme(style="white")
    strict = readiness[readiness["Aggregation"] == "strict"].copy()
    strict["Cell"] = strict["Instrument"] + "-" + strict["Timeframe"] + "-" + strict["Segment"]
    matrix = pd.DataFrame(index=["bull", "bear"], columns=strict["Cell"].tolist(), dtype=float)
    for r in strict.itertuples(index=False):
        col = f"{r.Instrument}-{r.Timeframe}-{r.Segment}"
        matrix.loc["bull", col] = r.EpBull
        matrix.loc["bear", col] = r.EpBear
    fig, ax = plt.subplots(figsize=(15, 3.5))
    sns.heatmap(matrix.astype(float), annot=True, fmt=".0f", cmap="Greens",
                cbar_kws={"label": "Independent episodes"}, annot_kws={"size": 7}, ax=ax)
    ax.set_title("EXP-035: Sign-only episode counts (strict) — floors 30 train / 15 test")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right", fontsize=7)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_persistence_fourway(readiness: pd.DataFrame, save_path: Path) -> None:
    """Median sign-state episode length (left) and four-way episode counts (right)."""
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    strict = readiness[readiness["Aggregation"] == "strict"].copy()
    train = strict[strict["Segment"] == "Train"].assign(
        Cell=lambda d: d["Instrument"] + "-" + d["Timeframe"]
    )
    x = np.arange(len(train))
    width = 0.4
    axes[0].bar(x - width / 2, train["MedLenBull"], width, color="#5cb85c", label="bull")
    axes[0].bar(x + width / 2, train["MedLenBear"], width, color="#d9534f", label="bear")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(train["Cell"], rotation=45, ha="right", fontsize=8)
    axes[0].set_ylabel("Median episode length (bars)")
    axes[0].set_title("Sign-state persistence (train, strict)")
    axes[0].legend(fontsize=8)
    four_cols = ["FourWayEpStrongBull", "FourWayEpWeakBull",
                 "FourWayEpStrongBear", "FourWayEpWeakBear"]
    bottom = np.zeros(len(train))
    palette = ["#2e7d32", "#a5d6a7", "#b71c1c", "#ef9a9a"]
    for col, color in zip(four_cols, palette):
        axes[1].bar(train["Cell"], train[col], bottom=bottom, color=color,
                    label=col.replace("FourWayEp", ""))
        bottom = bottom + train[col].to_numpy(dtype=float)
    axes[1].set_xticklabels(train["Cell"], rotation=45, ha="right", fontsize=8)
    axes[1].set_ylabel("Four-way episodes (train)")
    axes[1].set_title("Four-way state churn (secondary diagnostic)")
    axes[1].legend(fontsize=7)
    fig.suptitle("EXP-035: Persistence and four-way diagnostics", fontsize=13)
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
    """Execute the EXP-035 readiness survey end to end."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    readiness_rows: list[dict[str, Any]] = []
    sample_for_plot: pd.DataFrame | None = None
    sample_label = ""

    for instrument in INSTRUMENTS:
        for timeframe in TIMEFRAMES:
            for aggregation in AGGREGATIONS:
                LOGGER.info("EXP-035: %s %s %s — port + warmup + determinism",
                            instrument, timeframe, aggregation)
                canonical = _build_mb_frame(instrument, timeframe, aggregation)
                shuffled = _build_mb_frame(
                    instrument, timeframe, aggregation,
                    shuffle_seed=REPRODUCIBILITY_SHUFFLE_SEED,
                    warmup_override=canonical.warmup,
                )
                w = int(canonical.warmup["W"])
                post_c = _post_warmup(canonical.frame, w)
                post_s = _post_warmup(shuffled.frame, w)
                digests_match = {
                    seg: (
                        _digest_segment(post_c[post_c["Segment"] == seg])
                        == _digest_segment(post_s[post_s["Segment"] == seg])
                    )
                    for seg in SEGMENTS
                }
                readiness_rows.extend(_readiness_rows(canonical, digests_match))
                if (sample_for_plot is None and aggregation == "strict"
                        and not post_c.empty):
                    sample_for_plot = post_c[post_c["Segment"] == "Train"].copy()
                    sample_label = f"{instrument} {timeframe} (train)"

    readiness = pd.DataFrame(readiness_rows)
    reference = _reference_status()
    verdict = _aggregate_verdict(readiness, reference)

    LOGGER.info("EXP-035: writing outputs")
    readiness.to_csv(RESULTS_DIR / "readiness_table.csv", index=False)
    (RESULTS_DIR / "verdict.json").write_text(
        json.dumps(
            {
                "verdict_text": verdict["verdict_text"],
                "passes_readiness": verdict["passes_readiness"],
                "passing_instruments_per_cell": verdict["passing_instruments_per_cell"],
                "reference": verdict["reference"],
                "thresholds": {
                    "warmup_floor": WARMUP_FLOOR,
                    "min_rows_train": MIN_ROWS_TRAIN,
                    "min_rows_test": MIN_ROWS_TEST,
                    "min_episodes_train": MIN_EPISODES_TRAIN,
                    "min_episodes_test": MIN_EPISODES_TEST,
                    "collapse_share": COLLAPSE_SHARE,
                },
            },
            indent=2,
            default=_json_safe,
        )
    )

    LOGGER.info("EXP-035: rendering plots")
    _plot_determinism_warmup(readiness, PLOTS_DIR / "01_determinism_warmup.png")
    _plot_osc_series(
        sample_for_plot if sample_for_plot is not None else pd.DataFrame(),
        sample_label or "n/a",
        PLOTS_DIR / "02_osc_series.png",
    )
    _plot_sign_episode_grid(readiness, PLOTS_DIR / "03_sign_episode_grid.png")
    _plot_persistence_fourway(readiness, PLOTS_DIR / "04_persistence_fourway.png")

    _print_summary(readiness, verdict)


def _print_summary(readiness: pd.DataFrame, verdict: dict[str, Any]) -> None:
    """Concise manual-run summary."""
    print("\n=== EXP-035 readiness (strict aggregation, sign-only) ===")
    strict = readiness[readiness["Aggregation"] == "strict"][
        ["Instrument", "Timeframe", "Segment", "W", "Converged",
         "NBull", "NBear", "EpBull", "EpBear", "DominantShare", "PassesAllChecks"]
    ]
    print(strict.to_string(index=False))
    print("\n=== EXP-035 reference fidelity ===")
    print(f"reference_available: {verdict['reference']['reference_available']}")
    print(f"claim: {verdict['reference']['claim']}")
    print("\n=== EXP-035 verdict ===")
    print(verdict["verdict_text"])


def main() -> None:
    """Configure logging and run the experiment."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run_experiment()


if __name__ == "__main__":
    main()
