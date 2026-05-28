"""
Experiment EXP-029: 15-Minute FVG IFVG Selectivity Check
Implements the analysis plan from analysis-plan.md.

Applies the EXP-020 three-candle FVG and 120-bar close-through IFVG rules
unchanged to synthetic 15-minute bars resampled from holdout-excluded 1-minute
base bars. Primary lifecycle window is 120 15-minute bars (direct EXP-020
transfer); secondary 8 15-minute bars approximates the original 120-minute
elapsed window and separates timeframe-transfer effects from lifecycle-duration
effects.
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

from bar_aggregator import aggregate_ohlc, coverage_summary  # noqa: E402
from ict_timebar import (  # noqa: E402
    INSTRUMENTS,
    compute_price_precision_step,
    load_analysis_timebars,
)


LOGGER = logging.getLogger(__name__)

DATA_DIR = PROJECT_ROOT / "data"
EXP_DIR = PYTHON_ROOT / "experiments" / "EXP-029"
EXP018_RESULTS_DIR = PYTHON_ROOT / "experiments" / "EXP-018" / "results"

PERIOD_MINUTES = 15
ATR_PERIOD = 14
ATR_SIZE_COEFF = 0.02
LIFECYCLE_PRIMARY_BARS = 120
LIFECYCLE_SENSITIVITY_BARS = 8
MIN_FVG_PER_SEGMENT = 100
MIN_IFVG_PER_SEGMENT = 50
PHASE003_BASELINE_IFVG_RATE_LOW = 0.84
PHASE003_BASELINE_IFVG_RATE_HIGH = 0.85
SELECTIVITY_MATERIAL_THRESHOLD = 0.50
BOOTSTRAP_REPS = 2_000
BOOTSTRAP_BLOCK = 50
BOOTSTRAP_SEED = 42
REPRODUCIBILITY_SHUFFLE_SEED = 42
PLOT_SIZE_QUANTILE = 0.99

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
    """Column arrays needed for FVG detection on a 15-minute frame."""

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


# ── 1m -> 15m loading ────────────────────────────────────────────────────────


def _segment_15m_frame(frame_15m: pl.DataFrame, train_rows: int) -> pl.DataFrame:
    """Add a Train/Test label by chronological row position."""
    return frame_15m.with_row_index("_Row").with_columns(
        pl.when(pl.col("_Row") < train_rows)
        .then(pl.lit("Train"))
        .otherwise(pl.lit("Test"))
        .alias("Segment")
    )


def _add_atr_15m(frame_15m: pl.DataFrame) -> pl.DataFrame:
    """Add ATR14Prior recomputed on the 15-minute series.

    ATR uses only completed bars at or before the current bar; the shift(1)
    enforces that the value is knowable strictly before the current bar close.
    """
    prev_close = pl.col("Close").shift(1)
    true_range = pl.max_horizontal(
        pl.col("High") - pl.col("Low"),
        (pl.col("High") - prev_close).abs(),
        (pl.col("Low") - prev_close).abs(),
    ).fill_null(pl.col("High") - pl.col("Low"))
    return frame_15m.with_columns(true_range.alias("TrueRange")).with_columns(
        pl.col("TrueRange")
        .rolling_mean(window_size=ATR_PERIOD, min_samples=ATR_PERIOD)
        .shift(1)
        .alias("ATR14Prior")
    )


def load_instrument_15m_bars(
    instrument: str,
) -> tuple[PreparedBars, float, dict[str, int]]:
    """Load holdout-excluded 1m bars, aggregate to 15m, return PreparedBars.

    Holdout is excluded on the 1-minute series before aggregation; the 15-minute
    frame is generated only from the analysis-set 1-minute slice. The 70/30
    train/test split is applied chronologically inside the 15-minute series.
    """
    loaded = load_analysis_timebars(DATA_DIR, instrument)
    frame_1m = loaded.frame
    aggregated = aggregate_ohlc(frame_1m, period_minutes=PERIOD_MINUTES)
    coverage = coverage_summary(frame_1m, aggregated, period_minutes=PERIOD_MINUTES)

    if aggregated.is_empty():
        empty = pd.DataFrame(
            columns=["CloseTime", "High", "Low", "Close", "Segment", "ATR14Prior"]
        )
        return PreparedBars.from_frame(empty), 1e-5, coverage

    train_rows_15m = int(aggregated.height * 0.70)
    frame_15m = _add_atr_15m(_segment_15m_frame(aggregated, train_rows_15m))
    precision_step = compute_price_precision_step(frame_15m)
    bars_pd = (
        frame_15m.select(["CloseTime", "High", "Low", "Close", "Segment", "ATR14Prior"])
        .to_pandas()
        .reset_index(drop=True)
    )
    return PreparedBars.from_frame(bars_pd), precision_step, coverage


# ── FVG detection (EXP-020 logic, applied to 15m) ─────────────────────────────


def _candidate_arrays(
    bars: PreparedBars,
    precision_step: float,
) -> tuple[
    np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray
]:
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
    lifecycle_bars: int,
) -> dict[str, Any]:
    """Classify lifecycle and first IFVG close-through for one FVG.

    The same EXP-020 lifecycle definition is applied with a configurable
    `lifecycle_bars` window so that the same FVG set can be tested under the
    primary 120-bar and the secondary 8-bar sensitivity.
    """
    start = creation_idx + 1
    end = min(start + lifecycle_bars, len(bars))
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

    observation_complete = end - start >= lifecycle_bars
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
    lifecycle_bars: int,
) -> pd.DataFrame:
    """Detect scoped FVGs and classify lifecycle states for one instrument."""
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
                    lifecycle_bars,
                ),
            }
        )
    return pd.DataFrame(rows)


# ── Reproducibility ──────────────────────────────────────────────────────────


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
    """Return bars with rows shuffled and then re-sorted by CloseTime.

    Tests determinism of the (CloseTime, OHLC, ATR) -> FVG mapping. A failure
    here indicates the detector depends on source row order rather than on
    sorted bar values.
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
    """Verify detection invariance under fresh-reload and shuffled-resort.

    Both checks rerun the 1m -> 15m -> detection pipeline end to end so that
    the determinism guarantee covers aggregation as well as detection.
    """
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        first_subset = first_pass[first_pass["Instrument"] == instrument]
        first_digest = digest_events(first_subset)

        fresh_bars, fresh_step, _ = load_instrument_15m_bars(instrument)
        fresh = detect_fvgs(fresh_bars, instrument, fresh_step, LIFECYCLE_PRIMARY_BARS)
        fresh_digest = digest_events(fresh)

        shuffled_bars = _shuffle_then_resort(
            bars_by_instrument[instrument], REPRODUCIBILITY_SHUFFLE_SEED
        )
        shuffled = detect_fvgs(
            shuffled_bars,
            instrument,
            precision_steps[instrument],
            LIFECYCLE_PRIMARY_BARS,
        )
        shuffled_digest = digest_events(shuffled)

        rows.append(
            {
                "Instrument": instrument,
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


# ── Summaries, bootstrap, and verdict ────────────────────────────────────────


def summarize_counts(events: pd.DataFrame) -> pd.DataFrame:
    """Summarize FVG/IFVG counts, primary inversion rate, and readiness flags."""
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
            selective = bool(
                np.isfinite(ifvg_rate) and ifvg_rate < SELECTIVITY_MATERIAL_THRESHOLD
            )
            rows.append(
                {
                    "Instrument": instrument,
                    "Segment": segment,
                    "FVG_N": fvg_n,
                    "IFVG_N": ifvg_n,
                    "IFVGRate": ifvg_rate,
                    "FVGFloorMet": fvg_n >= MIN_FVG_PER_SEGMENT,
                    "IFVGFloorMet": ifvg_n >= MIN_IFVG_PER_SEGMENT,
                    "Selective": selective,
                    "ReadyForIFVGStudy": (
                        fvg_n >= MIN_FVG_PER_SEGMENT
                        and ifvg_n >= MIN_IFVG_PER_SEGMENT
                        and selective
                    ),
                }
            )
    return pd.DataFrame(rows)


def summarize_sensitivity(events_120: pd.DataFrame, events_8: pd.DataFrame) -> pd.DataFrame:
    """Compare primary 120-bar and secondary 8-bar IFVG rates per instrument."""
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        primary = events_120[events_120["Instrument"] == instrument]
        sensitivity = events_8[events_8["Instrument"] == instrument]
        prim_rate = (
            primary["IsIFVG"].sum() / len(primary) if len(primary) else np.nan
        )
        sens_rate = (
            sensitivity["IsIFVG"].sum() / len(sensitivity)
            if len(sensitivity)
            else np.nan
        )
        diff_pp = (
            (prim_rate - sens_rate) * 100.0
            if np.isfinite(prim_rate) and np.isfinite(sens_rate)
            else np.nan
        )
        rows.append(
            {
                "Instrument": instrument,
                "Primary120BarIFVGRate": prim_rate,
                "Sensitivity8BarIFVGRate": sens_rate,
                "DifferencePP": diff_pp,
            }
        )
    return pd.DataFrame(rows)


def block_bootstrap_inversion_rate(
    is_ifvg: np.ndarray,
    n_reps: int,
    block: int,
    seed: int,
) -> tuple[float, float, float]:
    """Block bootstrap the IFVG rate; return point and 95% CI.

    Non-parametric block bootstrap preserves local temporal dependence in the
    FVG outcome sequence. Block size is fixed by scope; no return outcomes are
    involved here, so this is a pure detection-rate diagnostic.
    """
    n = len(is_ifvg)
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    point = float(is_ifvg.mean())
    if n < block:
        return point, float("nan"), float("nan")
    n_blocks = int(np.ceil(n / block))
    samples = np.empty(n_reps, dtype=float)
    for rep in range(n_reps):
        starts = rng.integers(0, n - block + 1, size=n_blocks)
        idx = (starts[:, None] + np.arange(block)).reshape(-1)[:n]
        samples[rep] = is_ifvg[idx].mean()
    ci_low = float(np.quantile(samples, 0.025))
    ci_high = float(np.quantile(samples, 0.975))
    return point, ci_low, ci_high


def bootstrap_per_instrument(events: pd.DataFrame) -> pd.DataFrame:
    """Run the block bootstrap diagnostic on the primary 120-bar IFVG rate."""
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        is_ifvg = (
            events[events["Instrument"] == instrument]["IsIFVG"]
            .astype(float)
            .to_numpy()
        )
        point, ci_low, ci_high = block_bootstrap_inversion_rate(
            is_ifvg, BOOTSTRAP_REPS, BOOTSTRAP_BLOCK, BOOTSTRAP_SEED
        )
        rows.append(
            {
                "Instrument": instrument,
                "PrimaryIFVGRate": point,
                "CILow": ci_low,
                "CIHigh": ci_high,
                "N": int(len(is_ifvg)),
            }
        )
    return pd.DataFrame(rows)


# ── Displacement overlap diagnostic ──────────────────────────────────────────


def load_displacement_events_1m() -> pd.DataFrame:
    """Load EXP-018 displacement-confirmed events if available; empty otherwise.

    The overlap diagnostic is soft: when EXP-018 results are missing we record
    that and continue; reflection consumes the diagnostic only when present.
    """
    path = EXP018_RESULTS_DIR / "entry_proxy_events.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if df.empty or "EntryProxy" not in df.columns:
        return pd.DataFrame()
    df = df[df["EntryProxy"] == "DisplacementClose"].copy()
    df["DisplacementTime"] = pd.to_datetime(df["DisplacementTime"])
    return df.reset_index(drop=True)


def _window_end_for_1m_close(ts: pd.Timestamp) -> pd.Timestamp:
    """Return the 15-minute window-end CloseTime that encloses a 1-minute close.

    A 1-minute bar closing exactly on a 15-minute boundary is the LAST bar
    inside the window ending at that boundary, so the mapping must use `ceil`
    rather than `floor + period`.
    """
    return pd.Timestamp(ts).ceil(f"{PERIOD_MINUTES}min")


def displacement_overlap_share(
    events: pd.DataFrame,
    displacements: pd.DataFrame,
) -> pd.DataFrame:
    """Share of 15m FVG/IFVG events whose 15m CloseTime contains a 1m displacement."""
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        inst_events = events[events["Instrument"] == instrument]
        fvg_total = len(inst_events)
        ifvg_total = int(inst_events["IsIFVG"].sum()) if fvg_total else 0
        if displacements.empty or fvg_total == 0:
            rows.append(
                {
                    "Instrument": instrument,
                    "FVGOverlapShare": np.nan,
                    "IFVGOverlapShare": np.nan,
                    "DisplacementEvents": (
                        0
                        if displacements.empty
                        else int(
                            (displacements["Instrument"] == instrument).sum()
                        )
                    ),
                }
            )
            continue
        inst_disp = displacements[displacements["Instrument"] == instrument]
        floored = inst_disp["DisplacementTime"].apply(_window_end_for_1m_close).to_numpy()
        floored_set = set(floored.tolist())
        fvg_hits = sum(
            ts in floored_set for ts in inst_events["CreationTime"].to_numpy()
        )
        ifvg_subset = inst_events[inst_events["IsIFVG"]]
        ifvg_hits = sum(
            ts in floored_set for ts in ifvg_subset["InversionTime"].to_numpy()
        )
        rows.append(
            {
                "Instrument": instrument,
                "FVGOverlapShare": fvg_hits / fvg_total,
                "IFVGOverlapShare": (ifvg_hits / ifvg_total) if ifvg_total else np.nan,
                "DisplacementEvents": int(len(inst_disp)),
            }
        )
    return pd.DataFrame(rows)


# ── Verdict ──────────────────────────────────────────────────────────────────


def evaluate_verdict(
    counts: pd.DataFrame,
    reproducibility: pd.DataFrame,
    sensitivity: pd.DataFrame,
) -> dict[str, Any]:
    """Map count floors, selectivity, reproducibility, and sensitivity to a verdict.

    Decision rule from the scope:
        FOR  if primary 120-bar IFVGRate < 0.50 on >= 2 instruments AND both
             segments meet FVG/IFVG floors on those instruments AND detection
             is reproducible on all instruments.
        AGAINST if primary 120-bar IFVGRate is within 5pp of the 84-85%
             baseline on >= 3 instruments, OR detection is non-reproducible
             on any instrument.
        INCONCLUSIVE otherwise, including the case where 120-bar and 8-bar
             windows disagree by more than 10pp without clear attribution.
    """
    per_instrument: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        inst_counts = counts[counts["Instrument"] == instrument]
        reproducible = bool(
            reproducibility[reproducibility["Instrument"] == instrument][
                "Reproducible"
            ].all()
        )
        train_row = inst_counts[inst_counts["Segment"] == "Train"]
        test_row = inst_counts[inst_counts["Segment"] == "Test"]
        train_ready = bool(train_row["ReadyForIFVGStudy"].any())
        test_ready = bool(test_row["ReadyForIFVGStudy"].any())
        train_rate = (
            float(train_row["IFVGRate"].iloc[0]) if not train_row.empty else np.nan
        )
        test_rate = (
            float(test_row["IFVGRate"].iloc[0]) if not test_row.empty else np.nan
        )
        any_selective = bool(inst_counts["Selective"].any())
        per_instrument.append(
            {
                "Instrument": instrument,
                "Reproducible": reproducible,
                "TrainReady": train_ready,
                "TestReady": test_ready,
                "AnySegmentSelective": any_selective,
                "TrainIFVGRate": train_rate,
                "TestIFVGRate": test_rate,
                "Pass": (
                    reproducible
                    and train_ready
                    and test_ready
                    and any_selective
                ),
            }
        )
    verdict_df = pd.DataFrame(per_instrument)
    passing = int(verdict_df["Pass"].sum())
    reproducible_count = int(verdict_df["Reproducible"].sum())

    near_baseline_count = 0
    for row in verdict_df.itertuples(index=False):
        for rate in (row.TrainIFVGRate, row.TestIFVGRate):
            if np.isfinite(rate) and rate >= (PHASE003_BASELINE_IFVG_RATE_LOW - 0.05):
                near_baseline_count += 1
                break

    big_disagreement = bool(
        (sensitivity["DifferencePP"].abs() > 10.0).fillna(False).any()
    )

    if passing >= 2:
        verdict = "FOR"
    elif reproducible_count < 4:
        verdict = "AGAINST"
    elif near_baseline_count >= 3:
        verdict = "AGAINST"
    elif big_disagreement:
        verdict = "INCONCLUSIVE"
    else:
        verdict = "INCONCLUSIVE"
    return {
        "verdict": verdict,
        "instruments_passing": passing,
        "reproducible_instruments": reproducible_count,
        "near_baseline_instruments": near_baseline_count,
        "lifecycle_disagreement_over_10pp": big_disagreement,
        "per_instrument": per_instrument,
    }


# ── JSON sanitization ────────────────────────────────────────────────────────


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


# ── Plotting ─────────────────────────────────────────────────────────────────


def plot_inversion_rate_comparison(
    sensitivity: pd.DataFrame,
    save_path: Path,
) -> None:
    """Plot primary 120-bar vs 8-bar sensitivity IFVG rate by instrument."""
    plot_df = sensitivity.melt(
        id_vars=["Instrument"],
        value_vars=["Primary120BarIFVGRate", "Sensitivity8BarIFVGRate"],
        var_name="Window",
        value_name="IFVGRate",
    )
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(
        data=plot_df, x="Instrument", y="IFVGRate", hue="Window", order=INSTRUMENTS, ax=ax
    )
    ax.axhline(SELECTIVITY_MATERIAL_THRESHOLD, color="red", linestyle="--", linewidth=1)
    ax.axhline(
        PHASE003_BASELINE_IFVG_RATE_LOW, color="steelblue", linestyle=":", linewidth=1
    )
    ax.axhline(
        PHASE003_BASELINE_IFVG_RATE_HIGH, color="steelblue", linestyle=":", linewidth=1
    )
    ax.set_title("EXP-029 15m IFVG Inversion Rate vs Phase 003 1m Baseline")
    ax.set_ylabel("IFVG inversion rate")
    ax.set_xlabel("")
    ax.set_ylim(0, 1)
    ax.legend(title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_count_bars(counts: pd.DataFrame, save_path: Path) -> None:
    """Plot FVG and IFVG counts by instrument and segment with floor lines."""
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
        sns.barplot(
            data=sub,
            x="Instrument",
            y="Count",
            hue="EventType",
            order=INSTRUMENTS,
            ax=ax,
        )
        ax.axhline(MIN_FVG_PER_SEGMENT, color="steelblue", linestyle="--", linewidth=1)
        ax.axhline(MIN_IFVG_PER_SEGMENT, color="darkorange", linestyle="--", linewidth=1)
        ax.set_title(f"EXP-029 FVG/IFVG Counts - {segment} (15m)")
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
    ax.set_title(f"EXP-029 15m FVG Size Distribution (capped at p{PLOT_SIZE_QUANTILE:.2f})")
    ax.set_xlabel("")
    ax.set_ylabel("FVG size")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_displacement_overlap(overlap: pd.DataFrame, save_path: Path) -> None:
    """Plot share of 15m FVG/IFVG events overlapping 1m displacement events."""
    if overlap.empty or overlap["FVGOverlapShare"].isna().all():
        return
    plot_df = overlap.melt(
        id_vars=["Instrument"],
        value_vars=["FVGOverlapShare", "IFVGOverlapShare"],
        var_name="EventType",
        value_name="OverlapShare",
    )
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(
        data=plot_df,
        x="Instrument",
        y="OverlapShare",
        hue="EventType",
        order=INSTRUMENTS,
        ax=ax,
    )
    ax.set_title("EXP-029 Share of 15m FVG/IFVG Events Overlapping 1m Displacement")
    ax.set_xlabel("")
    ax.set_ylabel("Overlap share")
    ax.set_ylim(0, 1)
    ax.legend(title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ── Output orchestration ─────────────────────────────────────────────────────


def write_outputs(
    events_primary: pd.DataFrame,
    events_sensitivity: pd.DataFrame,
    counts: pd.DataFrame,
    sensitivity: pd.DataFrame,
    bootstrap: pd.DataFrame,
    overlap: pd.DataFrame,
    reproducibility: pd.DataFrame,
    coverage: dict[str, dict[str, int]],
    precision_steps: dict[str, float],
    verdict: dict[str, Any],
    plots_dir: Path,
    results_dir: Path,
) -> None:
    """Write tables, JSON, text summary, and plots."""
    events_primary.to_csv(results_dir / "fvg_lifecycle_events_120bar.csv", index=False)
    events_sensitivity.to_csv(results_dir / "fvg_lifecycle_events_8bar.csv", index=False)
    counts.to_csv(results_dir / "count_readiness.csv", index=False)
    sensitivity.to_csv(results_dir / "lifecycle_sensitivity.csv", index=False)
    bootstrap.to_csv(results_dir / "bootstrap_inversion_rate.csv", index=False)
    overlap.to_csv(results_dir / "displacement_overlap.csv", index=False)
    reproducibility.to_csv(results_dir / "reproducibility_digest.csv", index=False)

    payload = {
        "experiment_id": "EXP-029",
        "title": "15-Minute FVG IFVG Selectivity Check",
        "period_minutes": PERIOD_MINUTES,
        "atr_period": ATR_PERIOD,
        "atr_size_coefficient": ATR_SIZE_COEFF,
        "lifecycle_primary_bars": LIFECYCLE_PRIMARY_BARS,
        "lifecycle_sensitivity_bars": LIFECYCLE_SENSITIVITY_BARS,
        "selectivity_threshold": SELECTIVITY_MATERIAL_THRESHOLD,
        "phase003_baseline_ifvg_rate_low": PHASE003_BASELINE_IFVG_RATE_LOW,
        "phase003_baseline_ifvg_rate_high": PHASE003_BASELINE_IFVG_RATE_HIGH,
        "price_precision_steps": precision_steps,
        "coverage_diagnostics": coverage,
        "verdict_summary": verdict,
        "count_readiness": counts.to_dict(orient="records"),
        "lifecycle_sensitivity": sensitivity.to_dict(orient="records"),
        "bootstrap_inversion_rate": bootstrap.to_dict(orient="records"),
        "displacement_overlap": overlap.to_dict(orient="records"),
        "reproducibility": reproducibility.to_dict(orient="records"),
    }
    with (results_dir / "results.json").open("w", encoding="utf-8") as handle:
        json.dump(_json_safe(payload), handle, indent=2, default=str, allow_nan=False)

    with (results_dir / "numerical_summary.txt").open("w", encoding="utf-8") as handle:
        handle.write("EXP-029 15-Minute FVG IFVG Selectivity Check\n")
        handle.write(f"Verdict: {verdict['verdict']}\n")
        handle.write(
            f"Instruments passing: {verdict['instruments_passing']}/4; "
            f"reproducible: {verdict['reproducible_instruments']}/4\n\n"
        )
        handle.write(
            f"Phase 003 1m baseline IFVGRate band: "
            f"[{PHASE003_BASELINE_IFVG_RATE_LOW:.2f}, "
            f"{PHASE003_BASELINE_IFVG_RATE_HIGH:.2f}]\n"
        )
        handle.write(
            f"15m primary lifecycle: {LIFECYCLE_PRIMARY_BARS} bars; "
            f"sensitivity lifecycle: {LIFECYCLE_SENSITIVITY_BARS} bars\n\n"
        )
        for row in sensitivity.itertuples(index=False):
            prim = (
                f"{row.Primary120BarIFVGRate:.3f}"
                if np.isfinite(row.Primary120BarIFVGRate)
                else "n/a"
            )
            sens = (
                f"{row.Sensitivity8BarIFVGRate:.3f}"
                if np.isfinite(row.Sensitivity8BarIFVGRate)
                else "n/a"
            )
            handle.write(
                f"- {row.Instrument}: primary={prim}, 8bar={sens}, "
                f"diff_pp={row.DifferencePP:.2f}\n"
            )

    plot_inversion_rate_comparison(sensitivity, plots_dir / "01_inversion_rate.png")
    plot_count_bars(counts, plots_dir / "02_fvg_ifvg_counts.png")
    plot_size_distribution(events_primary, plots_dir / "03_fvg_size_distribution.png")
    plot_displacement_overlap(overlap, plots_dir / "04_displacement_overlap.png")


def run_experiment() -> None:
    """Execute the EXP-029 15m FVG/IFVG selectivity workflow."""
    plots_dir = EXP_DIR / "plots"
    results_dir = EXP_DIR / "results"
    plots_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    bars_by_instrument: dict[str, PreparedBars] = {}
    precision_steps: dict[str, float] = {}
    coverage_by_instrument: dict[str, dict[str, int]] = {}
    events_primary_parts: list[pd.DataFrame] = []
    events_sensitivity_parts: list[pd.DataFrame] = []

    for instrument in INSTRUMENTS:
        bars, precision_step, coverage = load_instrument_15m_bars(instrument)
        bars_by_instrument[instrument] = bars
        precision_steps[instrument] = precision_step
        coverage_by_instrument[instrument] = coverage
        LOGGER.info(
            "%s: 1m=%d, 15m=%d (dropped=%d)",
            instrument,
            coverage["source_bars_in"],
            coverage["aggregated_bars_out"],
            coverage["dropped_partial_window_bars"],
        )

        primary = detect_fvgs(bars, instrument, precision_step, LIFECYCLE_PRIMARY_BARS)
        sensitivity = detect_fvgs(
            bars, instrument, precision_step, LIFECYCLE_SENSITIVITY_BARS
        )
        events_primary_parts.append(primary)
        events_sensitivity_parts.append(sensitivity)
        LOGGER.info(
            "%s: 120-bar FVGs=%d IFVGs=%d; 8-bar FVGs=%d IFVGs=%d",
            instrument,
            len(primary),
            int(primary["IsIFVG"].sum()) if not primary.empty else 0,
            len(sensitivity),
            int(sensitivity["IsIFVG"].sum()) if not sensitivity.empty else 0,
        )

    events_primary = (
        pd.concat(events_primary_parts, ignore_index=True)
        if events_primary_parts
        else pd.DataFrame()
    )
    events_sensitivity = (
        pd.concat(events_sensitivity_parts, ignore_index=True)
        if events_sensitivity_parts
        else pd.DataFrame()
    )
    if events_primary.empty:
        raise ValueError("No FVG events were detected on the 15-minute series.")

    reproducibility = verify_reproducibility(
        bars_by_instrument, precision_steps, events_primary
    )
    counts = summarize_counts(events_primary)
    sensitivity_summary = summarize_sensitivity(events_primary, events_sensitivity)
    bootstrap = bootstrap_per_instrument(events_primary)
    overlap = displacement_overlap_share(events_primary, load_displacement_events_1m())
    verdict = evaluate_verdict(counts, reproducibility, sensitivity_summary)

    write_outputs(
        events_primary,
        events_sensitivity,
        counts,
        sensitivity_summary,
        bootstrap,
        overlap,
        reproducibility,
        coverage_by_instrument,
        precision_steps,
        verdict,
        plots_dir,
        results_dir,
    )

    print("EXP-029 complete.")
    print(f"Verdict: {verdict['verdict']} ({verdict['instruments_passing']}/4 instruments)")
    print(f"Plots:   {plots_dir}")
    print(f"Results: {results_dir}")


def main() -> None:
    """Entry point for manual execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_experiment()


if __name__ == "__main__":
    main()
