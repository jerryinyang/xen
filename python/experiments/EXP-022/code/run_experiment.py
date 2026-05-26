"""
Experiment EXP-022: Objective Breaker Candidate Reproducibility
Implements the analysis plan from analysis-plan.md.

Predeclared config (locked before results are inspected):
  displacement_prerequisite : EXP-018 (DisplacementClose confirmation)
  candidate_A               : last opposite-direction candle before displacement
                              (order-block proxy); breaker = later close through
                              the opposite boundary of that candle's range
  candidate_B               : causal swing-structure break (EXP-019 logic);
                              breaker = first close through the latest prior
                              swing in the displacement direction after displacement
  selection_criteria        : deterministic rerun equality AND
                              occurrence count >= MIN_EVENTS_PER_SEGMENT on
                              >= 3 instruments in both train and test;
                              ties broken by lower ambiguity rate
"""
import hashlib
import json
import logging
import sys
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

import polars as pl  # noqa: E402

from ict_timebar import (  # noqa: E402
    INSTRUMENTS,
    add_bar_diagnostics,
    load_analysis_timebars,
)

LOGGER = logging.getLogger(__name__)

DATA_DIR = PROJECT_ROOT / "data"
EXP_DIR = PYTHON_ROOT / "experiments" / "EXP-022"
EXP015_RESULTS_DIR = PYTHON_ROOT / "experiments" / "EXP-015" / "results"
EXP018_RESULTS_DIR = PYTHON_ROOT / "experiments" / "EXP-018" / "results"

DISPLACEMENT_PREREQUISITE = "EXP-018"

# Event-count floor per instrument/segment for candidate readiness
MIN_EVENTS_PER_SEGMENT = 50
# Ambiguity ceiling (fraction of events with ambiguous boundaries)
MAX_AMBIGUITY_RATE = 0.30
# Candidate A: look back at most this many bars for the last opposite candle
CAND_A_LOOKBACK_BARS = 30
# Candidate B: causal swing window (bars left and right of pivot)
SWING_LEFT_RIGHT = 2
# Maximum delay bars before a breaker confirmation is discarded as stale
MAX_BREAKER_DELAY = 120

DISP_REQUIRED = {
    "Instrument", "NYDate", "Segment", "LevelType", "Side",
    "SweepTime", "DisplacementTime", "EntryProxy", "EntryTime",
    "Entry", "Stop",
}
SWEEP_REQUIRED = {
    "Instrument", "NYDate", "Segment", "CloseTime",
    "LevelType", "Side", "EventType", "Stop",
}

CAND_A_KEY_COLS = [
    "CandidateID", "Instrument", "NYDate", "Segment", "LevelType", "Side",
    "SweepTime", "DisplacementTime", "OBLow", "OBHigh", "BreakerTime",
]
CAND_B_KEY_COLS = [
    "CandidateID", "Instrument", "NYDate", "Segment", "LevelType", "Side",
    "SweepTime", "DisplacementTime", "SwingPrice", "BreakerTime",
]


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def _require_columns(frame: pd.DataFrame, required: set[str], label: str) -> None:
    """Raise if a prerequisite artifact lacks required columns."""
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{label} is missing required columns: {missing}")


def load_sweep_events() -> pd.DataFrame:
    """Load EXP-015 failed-sweep events (Sweep rows only)."""
    path = EXP015_RESULTS_DIR / "sweep_events.csv"
    if not path.exists():
        raise FileNotFoundError(f"Required prerequisite not found: {path}")
    df = pd.read_csv(path)
    _require_columns(df, SWEEP_REQUIRED, "EXP-015 sweep_events.csv")
    df = df[df["EventType"] == "Sweep"].copy()
    df["CloseTime"] = pd.to_datetime(df["CloseTime"])
    return df.sort_values(["Instrument", "Segment", "CloseTime"]).reset_index(drop=True)


def load_displacement_events() -> pd.DataFrame:
    """Load EXP-018 displacement-confirmed events (DisplacementClose only)."""
    path = EXP018_RESULTS_DIR / "entry_proxy_events.csv"
    if not path.exists():
        raise FileNotFoundError(f"Required prerequisite not found: {path}")
    df = pd.read_csv(path)
    _require_columns(df, DISP_REQUIRED, "EXP-018 entry_proxy_events.csv")
    df = df[df["EntryProxy"] == "DisplacementClose"].copy()
    df["SweepTime"] = pd.to_datetime(df["SweepTime"])
    df["DisplacementTime"] = pd.to_datetime(df["DisplacementTime"])
    df["EntryTime"] = pd.to_datetime(df["EntryTime"])
    return df.reset_index(drop=True)


def load_instrument_bars(instrument: str) -> pd.DataFrame:
    """Load holdout-excluded analysis bars for one instrument."""
    loaded = load_analysis_timebars(DATA_DIR, instrument)
    frame = (
        add_bar_diagnostics(loaded.frame)
        .with_row_index("_Row")
        .with_columns(
            pl.when(pl.col("_Row") < loaded.train_rows)
            .then(pl.lit("Train"))
            .otherwise(pl.lit("Test"))
            .alias("Segment")
        )
    )
    bars = frame.sort("CloseTime").to_pandas()
    bars["CloseTime"] = pd.to_datetime(bars["CloseTime"])
    bars["OpenTime"] = pd.to_datetime(bars["OpenTime"])
    return bars.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Candidate A: last opposite-candle order-block proxy
# ---------------------------------------------------------------------------

def _find_last_opposite_candle(
    side: str,
    before_ns: int,
    close_ns: np.ndarray,
    bars: pd.DataFrame,
) -> tuple[float, float, pd.Timestamp] | None:
    """Return (OBLow, OBHigh, OBTime) of the last opposite candle before a timestamp."""
    before_idx = int(np.searchsorted(close_ns, before_ns, side="left"))
    search_start = max(0, before_idx - CAND_A_LOOKBACK_BARS)
    for i in range(before_idx - 1, search_start - 1, -1):
        bar = bars.iloc[i]
        is_bullish = float(bar["Close"]) > float(bar["Open"])
        is_bearish = float(bar["Close"]) < float(bar["Open"])
        # High sweep (bearish reversal): last BULLISH candle (opposite direction)
        # Low  sweep (bullish reversal): last BEARISH candle (opposite direction)
        if side == "High" and is_bullish:
            return float(bar["Low"]), float(bar["High"]), bar["CloseTime"]
        if side == "Low" and is_bearish:
            return float(bar["Low"]), float(bar["High"]), bar["CloseTime"]
    return None


def _close_invalidates_setup(side: str, close: float, stop: float) -> bool:
    """Return True when a close crosses the original sweep invalidation stop."""
    return close >= stop if side == "High" else close <= stop


def _find_cand_a_breaker(
    ob_low: float,
    ob_high: float,
    side: str,
    disp_ns: int,
    stop: float,
    close_ns: np.ndarray,
    bars: pd.DataFrame,
) -> dict[str, Any] | None:
    """Find first close through the order-block boundary after displacement."""
    start_idx = int(np.searchsorted(close_ns, disp_ns, side="right"))
    stop_idx = min(start_idx + MAX_BREAKER_DELAY, len(bars))
    for i in range(start_idx, stop_idx):
        bar = bars.iloc[i]
        close = float(bar["Close"])
        if _close_invalidates_setup(side, close, stop):
            return {
                "InvalidatedBeforeBreaker": True,
                "InvalidationTime": bar["CloseTime"],
                "DelayBars": i - start_idx + 1,
            }
        # High sweep (bearish): breaker = close below OB Low (through bullish OB)
        # Low  sweep (bullish): breaker = close above OB High (through bearish OB)
        if side == "High" and close < ob_low:
            return {
                "BreakerTime": bar["CloseTime"],
                "BreakerClose": close,
                "DelayBars": i - start_idx + 1,
                "InvalidatedBeforeBreaker": False,
                "InvalidationTime": pd.NaT,
            }
        if side == "Low" and close > ob_high:
            return {
                "BreakerTime": bar["CloseTime"],
                "BreakerClose": close,
                "DelayBars": i - start_idx + 1,
                "InvalidatedBeforeBreaker": False,
                "InvalidationTime": pd.NaT,
            }
    return None


def detect_candidate_a(
    displacements: pd.DataFrame,
    bars_by_instrument: dict[str, pd.DataFrame],
    instrument: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Detect Candidate A breaker events for one instrument."""
    events: list[dict[str, Any]] = []
    misses: list[dict[str, Any]] = []

    bars = bars_by_instrument[instrument]
    close_ns = bars["CloseTime"].values.astype(np.int64)
    inst_disps = displacements[displacements["Instrument"] == instrument]

    for _, disp in inst_disps.iterrows():
        disp_ns = int(pd.Timestamp(disp["DisplacementTime"]).value)
        side = str(disp["Side"])
        event_id = f"CandA-{instrument}-{disp['NYDate']}-{disp['LevelType']}-{disp['SweepTime']}-{side}"

        ob = _find_last_opposite_candle(side, disp_ns, close_ns, bars)
        if ob is None:
            misses.append({
                "CandidateID": event_id, "Instrument": instrument,
                "NYDate": disp["NYDate"], "Segment": disp["Segment"],
                "LevelType": disp["LevelType"], "Side": side,
                "SweepTime": disp["SweepTime"],
                "DisplacementTime": disp["DisplacementTime"],
                "Confirmed": False, "MissReason": "NO_OPPOSITE_CANDLE",
                "InvalidatedBeforeBreaker": False,
            })
            continue
        ob_low, ob_high, ob_time = ob
        breaker = _find_cand_a_breaker(
            ob_low, ob_high, side, disp_ns, float(disp["Stop"]), close_ns, bars
        )
        if breaker is not None and breaker.get("InvalidatedBeforeBreaker", False):
            misses.append({
                "CandidateID": event_id, "Instrument": instrument,
                "NYDate": disp["NYDate"], "Segment": disp["Segment"],
                "LevelType": disp["LevelType"], "Side": side,
                "SweepTime": disp["SweepTime"],
                "DisplacementTime": disp["DisplacementTime"],
                "Confirmed": False, "MissReason": "INVALIDATED_BEFORE_BREAKER",
                "OBLow": ob_low, "OBHigh": ob_high,
                "InvalidatedBeforeBreaker": True,
                "InvalidationTime": breaker["InvalidationTime"],
            })
            continue
        if breaker is None:
            misses.append({
                "CandidateID": event_id, "Instrument": instrument,
                "NYDate": disp["NYDate"], "Segment": disp["Segment"],
                "LevelType": disp["LevelType"], "Side": side,
                "SweepTime": disp["SweepTime"],
                "DisplacementTime": disp["DisplacementTime"],
                "Confirmed": False, "MissReason": "NO_BREAKER_WITHIN_WINDOW",
                "OBLow": ob_low, "OBHigh": ob_high,
                "InvalidatedBeforeBreaker": False,
            })
            continue
        events.append({
            "CandidateID": event_id, "Instrument": instrument,
            "NYDate": disp["NYDate"], "Segment": disp["Segment"],
            "LevelType": disp["LevelType"], "Side": side,
            "SweepTime": disp["SweepTime"],
            "DisplacementTime": disp["DisplacementTime"],
            "OBTime": ob_time, "OBLow": ob_low, "OBHigh": ob_high,
            "BreakerTime": breaker["BreakerTime"],
            "BreakerClose": breaker["BreakerClose"],
            "DelayBars": breaker["DelayBars"],
            "InvalidatedBeforeBreaker": breaker["InvalidatedBeforeBreaker"],
            "InvalidationTime": breaker["InvalidationTime"],
            "Confirmed": True, "MissReason": "NONE",
        })

    return events, misses


# ---------------------------------------------------------------------------
# Candidate B: causal swing-structure break (EXP-019 logic)
# ---------------------------------------------------------------------------

def detect_swings(bars: pd.DataFrame, instrument: str) -> pd.DataFrame:
    """Detect two-left/two-right swing pivots with causal confirmation timestamps."""
    rows: list[dict[str, Any]] = []
    highs = bars["High"].to_numpy(dtype=float)
    lows = bars["Low"].to_numpy(dtype=float)
    n = len(bars)
    for idx in range(SWING_LEFT_RIGHT, n - SWING_LEFT_RIGHT):
        left = slice(idx - SWING_LEFT_RIGHT, idx)
        right = slice(idx + 1, idx + SWING_LEFT_RIGHT + 1)
        usable_idx = idx + SWING_LEFT_RIGHT
        if highs[idx] > np.max(highs[left]) and highs[idx] > np.max(highs[right]):
            rows.append({
                "Instrument": instrument, "SwingType": "High",
                "PivotIndex": idx, "PivotTime": bars.iloc[idx]["CloseTime"],
                "UsableIndex": usable_idx,
                "UsableTime": bars.iloc[usable_idx]["CloseTime"],
                "SwingPrice": float(highs[idx]),
                "Segment": bars.iloc[usable_idx]["Segment"],
            })
        if lows[idx] < np.min(lows[left]) and lows[idx] < np.min(lows[right]):
            rows.append({
                "Instrument": instrument, "SwingType": "Low",
                "PivotIndex": idx, "PivotTime": bars.iloc[idx]["CloseTime"],
                "UsableIndex": usable_idx,
                "UsableTime": bars.iloc[usable_idx]["CloseTime"],
                "SwingPrice": float(lows[idx]),
                "Segment": bars.iloc[usable_idx]["Segment"],
            })
    return pd.DataFrame(rows)


def _latest_usable_swing(
    swings: pd.DataFrame,
    swing_type: str,
    before_ns: int,
) -> pd.Series | None:
    """Return the most recent swing of the given type whose UsableTime < before_ns."""
    sub = swings[swings["SwingType"] == swing_type]
    if sub.empty:
        return None
    sub_ns = sub["UsableTime"].values.astype(np.int64)
    idx = int(np.searchsorted(sub_ns, before_ns, side="left")) - 1
    if idx < 0:
        return None
    return sub.iloc[idx]


def _find_cand_b_breaker(
    side: str,
    disp_ns: int,
    stop: float,
    swings: pd.DataFrame,
    close_ns: np.ndarray,
    bars: pd.DataFrame,
) -> dict[str, Any] | None:
    """Find first close through the latest swing in displacement direction after displacement."""
    # High sweep (bearish): swing type = Low (we need to break below a swing Low)
    # Low  sweep (bullish): swing type = High (we need to break above a swing High)
    swing_type = "Low" if side == "High" else "High"

    start_idx = int(np.searchsorted(close_ns, disp_ns, side="right"))
    stop_idx = min(start_idx + MAX_BREAKER_DELAY, len(bars))
    for i in range(start_idx, stop_idx):
        bar = bars.iloc[i]
        bar_ns = int(bar["CloseTime"].value)
        swing = _latest_usable_swing(swings, swing_type, bar_ns)
        if swing is None:
            continue
        swing_price = float(swing["SwingPrice"])
        close = float(bar["Close"])
        if _close_invalidates_setup(side, close, stop):
            return {
                "InvalidatedBeforeBreaker": True,
                "InvalidationTime": bar["CloseTime"],
                "DelayBars": i - start_idx + 1,
            }
        if side == "High" and close < swing_price:
            return {
                "SwingType": swing_type,
                "SwingPivotTime": swing["PivotTime"],
                "SwingUsableTime": swing["UsableTime"],
                "SwingPrice": swing_price,
                "BreakerTime": bar["CloseTime"],
                "BreakerClose": close,
                "DelayBars": i - start_idx + 1,
                "InvalidatedBeforeBreaker": False,
                "InvalidationTime": pd.NaT,
            }
        if side == "Low" and close > swing_price:
            return {
                "SwingType": swing_type,
                "SwingPivotTime": swing["PivotTime"],
                "SwingUsableTime": swing["UsableTime"],
                "SwingPrice": swing_price,
                "BreakerTime": bar["CloseTime"],
                "BreakerClose": close,
                "DelayBars": i - start_idx + 1,
                "InvalidatedBeforeBreaker": False,
                "InvalidationTime": pd.NaT,
            }
    return None


def detect_candidate_b(
    displacements: pd.DataFrame,
    bars_by_instrument: dict[str, pd.DataFrame],
    swings_by_instrument: dict[str, pd.DataFrame],
    instrument: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Detect Candidate B breaker events for one instrument."""
    events: list[dict[str, Any]] = []
    misses: list[dict[str, Any]] = []

    bars = bars_by_instrument[instrument]
    swings = swings_by_instrument[instrument]
    close_ns = bars["CloseTime"].values.astype(np.int64)
    inst_disps = displacements[displacements["Instrument"] == instrument]

    for _, disp in inst_disps.iterrows():
        disp_ns = int(pd.Timestamp(disp["DisplacementTime"]).value)
        side = str(disp["Side"])
        event_id = f"CandB-{instrument}-{disp['NYDate']}-{disp['LevelType']}-{disp['SweepTime']}-{side}"

        breaker = _find_cand_b_breaker(
            side, disp_ns, float(disp["Stop"]), swings, close_ns, bars
        )
        if breaker is not None and breaker.get("InvalidatedBeforeBreaker", False):
            misses.append({
                "CandidateID": event_id, "Instrument": instrument,
                "NYDate": disp["NYDate"], "Segment": disp["Segment"],
                "LevelType": disp["LevelType"], "Side": side,
                "SweepTime": disp["SweepTime"],
                "DisplacementTime": disp["DisplacementTime"],
                "Confirmed": False, "MissReason": "INVALIDATED_BEFORE_BREAKER",
                "InvalidatedBeforeBreaker": True,
                "InvalidationTime": breaker["InvalidationTime"],
            })
            continue
        if breaker is None:
            misses.append({
                "CandidateID": event_id, "Instrument": instrument,
                "NYDate": disp["NYDate"], "Segment": disp["Segment"],
                "LevelType": disp["LevelType"], "Side": side,
                "SweepTime": disp["SweepTime"],
                "DisplacementTime": disp["DisplacementTime"],
                "Confirmed": False, "MissReason": "NO_SWING_BREAK_FOUND",
                "InvalidatedBeforeBreaker": False,
            })
            continue
        events.append({
            "CandidateID": event_id, "Instrument": instrument,
            "NYDate": disp["NYDate"], "Segment": disp["Segment"],
            "LevelType": disp["LevelType"], "Side": side,
            "SweepTime": disp["SweepTime"],
            "DisplacementTime": disp["DisplacementTime"],
            "SwingType": breaker["SwingType"],
            "SwingPivotTime": breaker["SwingPivotTime"],
            "SwingUsableTime": breaker["SwingUsableTime"],
            "SwingPrice": breaker["SwingPrice"],
            "BreakerTime": breaker["BreakerTime"],
            "BreakerClose": breaker["BreakerClose"],
            "DelayBars": breaker["DelayBars"],
            "InvalidatedBeforeBreaker": breaker["InvalidatedBeforeBreaker"],
            "InvalidationTime": breaker["InvalidationTime"],
            "Confirmed": True, "MissReason": "NONE",
        })

    return events, misses


# ---------------------------------------------------------------------------
# Ambiguity and duplicate-source accounting
# ---------------------------------------------------------------------------

def mark_duplicate_state(events: pd.DataFrame) -> pd.DataFrame:
    """Mark exact duplicate candidate identities as ambiguous."""
    if events.empty:
        return events.assign(
            DuplicateSourceCount=pd.Series(dtype="int64"),
            Ambiguous=pd.Series(dtype="bool"),
        )
    out = events.copy()
    key_cols = [
        "Instrument", "NYDate", "Segment", "LevelType", "Side",
        "SweepTime", "DisplacementTime",
    ]
    duplicate_counts = out.groupby(key_cols)["CandidateID"].transform("count")
    out["DuplicateSourceCount"] = duplicate_counts.astype(int)
    out["Ambiguous"] = out["DuplicateSourceCount"] > 1
    return out


# ---------------------------------------------------------------------------
# Reproducibility check
# ---------------------------------------------------------------------------

def _digest(df: pd.DataFrame, key_cols: list[str]) -> str:
    """Return a stable SHA-256 digest over identity columns."""
    if df.empty:
        return hashlib.sha256(b"EMPTY").hexdigest()
    stable = df[key_cols].sort_values(key_cols).copy()
    text = stable.to_csv(index=False, float_format="%.12g")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def verify_reproducibility(
    cand_a: pd.DataFrame,
    cand_b: pd.DataFrame,
    displacements: pd.DataFrame,
    bars_by_instrument: dict[str, pd.DataFrame],
    swings_by_instrument: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Verify both candidates reproduce identical events on a second pass."""
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        # Second pass for Candidate A
        a2_events, _ = detect_candidate_a(displacements, bars_by_instrument, instrument)
        a2 = pd.DataFrame(a2_events)
        a_first = (
            cand_a[cand_a["Instrument"] == instrument]
            if "Instrument" in cand_a.columns
            else pd.DataFrame()
        )
        a_digest_1 = _digest(a_first, CAND_A_KEY_COLS)
        a_digest_2 = _digest(a2, CAND_A_KEY_COLS)

        # Second pass for Candidate B
        b2_events, _ = detect_candidate_b(
            displacements, bars_by_instrument, swings_by_instrument, instrument
        )
        b2 = pd.DataFrame(b2_events)
        b_first = (
            cand_b[cand_b["Instrument"] == instrument]
            if "Instrument" in cand_b.columns
            else pd.DataFrame()
        )
        b_digest_1 = _digest(b_first, CAND_B_KEY_COLS)
        b_digest_2 = _digest(b2, CAND_B_KEY_COLS)

        rows.append({
            "Instrument": instrument,
            "CandA_Digest1": a_digest_1,
            "CandA_Digest2": a_digest_2,
            "CandA_Reproducible": a_digest_1 == a_digest_2,
            "CandB_Digest1": b_digest_1,
            "CandB_Digest2": b_digest_2,
            "CandB_Reproducible": b_digest_1 == b_digest_2,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Count and selection
# ---------------------------------------------------------------------------

def summarize_candidate_counts(
    cand_a: pd.DataFrame,
    cand_b: pd.DataFrame,
    displacements: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize occurrence counts and ambiguity rates per candidate and segment."""
    rows: list[dict[str, Any]] = []
    for instrument in INSTRUMENTS:
        inst_disps = displacements[displacements["Instrument"] == instrument]
        for segment in ("Train", "Test"):
            seg_disps = inst_disps[inst_disps["Segment"] == segment]
            n_disp = len(seg_disps)
            for label, df in (("CandidateA", cand_a), ("CandidateB", cand_b)):
                if df.empty or "Instrument" not in df.columns or "Segment" not in df.columns:
                    sub = pd.DataFrame()
                else:
                    sub = df[(df["Instrument"] == instrument) & (df["Segment"] == segment)]
                n = len(sub)
                ambig = int(sub["Ambiguous"].sum()) if not sub.empty and "Ambiguous" in sub.columns else 0
                rows.append({
                    "Candidate": label,
                    "Instrument": instrument,
                    "Segment": segment,
                    "DisplacementN": n_disp,
                    "BreakerN": n,
                    "AmbiguousN": ambig,
                    "RetentionPct": n / n_disp if n_disp else np.nan,
                    "AmbiguityRate": ambig / n if n else np.nan,
                    "EventFloorMet": n >= MIN_EVENTS_PER_SEGMENT,
                    "AmbiguityOk": (ambig / n if n else 1.0) <= MAX_AMBIGUITY_RATE,
                })
    return pd.DataFrame(rows)


def select_candidate(
    counts: pd.DataFrame,
    reproducibility: pd.DataFrame,
) -> dict[str, Any]:
    """Select a candidate for EXP-023 based on predeclared reproducibility and count criteria.

    Criterion (in order):
    1. Deterministic rerun equality for all 4 instruments.
    2. EventFloorMet on >= 3 instruments in both Train and Test segments.
    3. AmbiguityOk across all qualifying instruments.
    Ties broken by lower mean ambiguity rate.
    """
    results: dict[str, dict[str, Any]] = {}
    for cand in ("CandidateA", "CandidateB"):
        repro_col = "CandA_Reproducible" if cand == "CandidateA" else "CandB_Reproducible"
        reproducible = bool(reproducibility[repro_col].all())
        sub = counts[counts["Candidate"] == cand]
        instruments_train_ok = sub[sub["Segment"] == "Train"]["EventFloorMet"].sum()
        instruments_test_ok = sub[sub["Segment"] == "Test"]["EventFloorMet"].sum()
        ambiguity_ok = bool(sub["AmbiguityOk"].all())
        mean_ambig = float(sub["AmbiguityRate"].mean()) if not sub.empty else 1.0
        eligible = (
            reproducible
            and int(instruments_train_ok) >= 3
            and int(instruments_test_ok) >= 3
            and ambiguity_ok
        )
        results[cand] = {
            "reproducible": reproducible,
            "instruments_train_ok": int(instruments_train_ok),
            "instruments_test_ok": int(instruments_test_ok),
            "ambiguity_ok": ambiguity_ok,
            "mean_ambiguity_rate": mean_ambig,
            "eligible": eligible,
        }

    eligible_candidates = [c for c, r in results.items() if r["eligible"]]
    if len(eligible_candidates) == 0:
        selected = "None"
        reason = "No candidate meets all reproducibility, count, and ambiguity criteria"
    elif len(eligible_candidates) == 1:
        selected = eligible_candidates[0]
        reason = "Only eligible candidate"
    else:
        # Both eligible: pick lower ambiguity
        selected = min(
            eligible_candidates,
            key=lambda c: results[c]["mean_ambiguity_rate"],
        )
        reason = "Both eligible; selected lower mean ambiguity rate"

    return {
        "selected_candidate": selected,
        "selection_reason": reason,
        "per_candidate": results,
    }


# ---------------------------------------------------------------------------
# Plotting helpers
# ---------------------------------------------------------------------------

def plot_candidate_counts(counts: pd.DataFrame, save_path: Path) -> None:
    """Plot breaker occurrence counts by candidate and instrument/segment."""
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=False)
    for ax, segment in zip(axes, ("Train", "Test")):
        sub = counts[counts["Segment"] == segment]
        sns.barplot(
            data=sub, x="Instrument", y="BreakerN", hue="Candidate",
            order=INSTRUMENTS, ax=ax,
        )
        ax.axhline(MIN_EVENTS_PER_SEGMENT, color="red", linestyle="--", linewidth=1)
        ax.set_title(f"EXP-022 Breaker Occurrence Counts - {segment}")
        ax.set_xlabel("")
        ax.legend(title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_ambiguity_reasons(
    cand_a_misses: pd.DataFrame,
    cand_b_misses: pd.DataFrame,
    save_path: Path,
) -> None:
    """Plot miss-reason counts for each candidate."""
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=False)
    for ax, (label, df) in zip(axes, [("Candidate A", cand_a_misses), ("Candidate B", cand_b_misses)]):
        if df.empty:
            ax.set_title(f"EXP-022 Miss Reasons - {label} (no data)")
            continue
        reason_counts = (
            df.groupby("MissReason")["Instrument"].count()
            .reset_index(name="Count")
            .sort_values("Count", ascending=False)
        )
        sns.barplot(data=reason_counts, x="MissReason", y="Count", ax=ax)
        ax.set_title(f"EXP-022 Miss Reasons - {label}")
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_confirmation_delay(
    cand_a: pd.DataFrame,
    cand_b: pd.DataFrame,
    save_path: Path,
) -> None:
    """Plot confirmation delay distributions for each candidate."""
    frames = []
    for label, df in (("CandidateA", cand_a), ("CandidateB", cand_b)):
        if not df.empty and "DelayBars" in df.columns:
            tmp = df[["Instrument", "Segment", "DelayBars"]].copy()
            tmp["Candidate"] = label
            frames.append(tmp)
    if not frames:
        return
    plot_df = pd.concat(frames, ignore_index=True)
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.boxplot(data=plot_df, x="Instrument", y="DelayBars", hue="Candidate",
                order=INSTRUMENTS, showfliers=False, ax=ax)
    ax.set_title("EXP-022 Confirmation Delay Distribution by Candidate")
    ax.set_xlabel("")
    ax.legend(title="")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def _json_safe(value: Any) -> Any:
    """Convert numpy/pandas scalars to JSON-safe types."""
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if np.isfinite(value) else None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def write_outputs(
    cand_a: pd.DataFrame,
    cand_b: pd.DataFrame,
    cand_a_misses: pd.DataFrame,
    cand_b_misses: pd.DataFrame,
    counts: pd.DataFrame,
    reproducibility: pd.DataFrame,
    selection: dict[str, Any],
    plots_dir: Path,
    results_dir: Path,
) -> None:
    """Write all EXP-022 results, tables, and plots."""
    cand_a.to_csv(results_dir / "candidate_a_events.csv", index=False)
    cand_b.to_csv(results_dir / "candidate_b_events.csv", index=False)
    cand_a_misses.to_csv(results_dir / "candidate_a_misses.csv", index=False)
    cand_b_misses.to_csv(results_dir / "candidate_b_misses.csv", index=False)
    counts.to_csv(results_dir / "candidate_counts.csv", index=False)
    reproducibility.to_csv(results_dir / "reproducibility.csv", index=False)

    payload = {
        "experiment_id": "EXP-022",
        "title": "Objective Breaker Candidate Reproducibility",
        "predeclared_config": {
            "displacement_prerequisite": DISPLACEMENT_PREREQUISITE,
            "candidate_a_definition": (
                "Last bullish (for High sweep) or bearish (for Low sweep) candle "
                "within CAND_A_LOOKBACK_BARS before sweep; breaker = close through "
                "the opposite OB boundary within MAX_BREAKER_DELAY bars after displacement."
            ),
            "candidate_b_definition": (
                "Causal swing-break (EXP-019 logic, SWING_LEFT_RIGHT=2); "
                "first close through the latest usable swing in displacement direction "
                "within MAX_BREAKER_DELAY bars after displacement."
            ),
            "selection_criteria": (
                "Deterministic rerun equality AND >= 3 instruments meeting event "
                "floor in both Train and Test; ties by lower ambiguity rate."
            ),
        },
        "selection": selection,
        "counts": counts.to_dict(orient="records"),
        "reproducibility": reproducibility.to_dict(orient="records"),
    }
    with (results_dir / "selection.json").open("w", encoding="utf-8") as fh:
        json.dump(_json_safe(payload), fh, indent=2, default=str, allow_nan=False)

    with (results_dir / "numerical_summary.txt").open("w", encoding="utf-8") as fh:
        fh.write("EXP-022 Objective Breaker Candidate Reproducibility\n")
        fh.write(f"Selected candidate: {selection['selected_candidate']}\n")
        fh.write(f"Selection reason: {selection['selection_reason']}\n\n")
        fh.write("Counts by candidate, instrument, segment:\n")
        for r in counts.itertuples(index=False):
            fh.write(
                f"  {r.Candidate} {r.Instrument} {r.Segment}: "
                f"N={r.BreakerN} (floor={r.EventFloorMet}), "
                f"ambig={r.AmbiguousN} ({r.AmbiguityRate:.2%})\n"
            )
        fh.write("\nReproducibility:\n")
        for r in reproducibility.itertuples(index=False):
            fh.write(
                f"  {r.Instrument}: CandA={r.CandA_Reproducible}, "
                f"CandB={r.CandB_Reproducible}\n"
            )

    plot_candidate_counts(counts, plots_dir / "01_candidate_occurrence_counts.png")
    plot_ambiguity_reasons(cand_a_misses, cand_b_misses, plots_dir / "02_ambiguity_reasons.png")
    plot_confirmation_delay(cand_a, cand_b, plots_dir / "03_confirmation_delay.png")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_experiment() -> None:
    """Execute the EXP-022 breaker reproducibility workflow."""
    plots_dir = EXP_DIR / "plots"
    results_dir = EXP_DIR / "results"
    plots_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Loading prerequisite events …")
    sweeps = load_sweep_events()
    displacements = load_displacement_events()

    LOGGER.info("Loading instrument bars and detecting swings …")
    bars_by_instrument: dict[str, pd.DataFrame] = {}
    swings_by_instrument: dict[str, pd.DataFrame] = {}
    for instrument in INSTRUMENTS:
        bars = load_instrument_bars(instrument)
        bars_by_instrument[instrument] = bars
        swings_by_instrument[instrument] = detect_swings(bars, instrument)
        LOGGER.info(
            "%s: %d analysis bars, %d swings",
            instrument, len(bars), len(swings_by_instrument[instrument]),
        )

    LOGGER.info("Detecting Candidate A (order-block proxy) …")
    cand_a_parts: list[pd.DataFrame] = []
    cand_a_miss_parts: list[pd.DataFrame] = []
    for instrument in INSTRUMENTS:
        ev, ms = detect_candidate_a(displacements, bars_by_instrument, instrument)
        cand_a_parts.append(pd.DataFrame(ev))
        cand_a_miss_parts.append(pd.DataFrame(ms))
    cand_a = pd.concat(cand_a_parts, ignore_index=True) if cand_a_parts else pd.DataFrame()
    cand_a = mark_duplicate_state(cand_a)
    cand_a_misses = pd.concat(cand_a_miss_parts, ignore_index=True) if cand_a_miss_parts else pd.DataFrame()

    LOGGER.info("Detecting Candidate B (swing-break) …")
    cand_b_parts: list[pd.DataFrame] = []
    cand_b_miss_parts: list[pd.DataFrame] = []
    for instrument in INSTRUMENTS:
        ev, ms = detect_candidate_b(
            displacements, bars_by_instrument, swings_by_instrument, instrument
        )
        cand_b_parts.append(pd.DataFrame(ev))
        cand_b_miss_parts.append(pd.DataFrame(ms))
    cand_b = pd.concat(cand_b_parts, ignore_index=True) if cand_b_parts else pd.DataFrame()
    cand_b = mark_duplicate_state(cand_b)
    cand_b_misses = pd.concat(cand_b_miss_parts, ignore_index=True) if cand_b_miss_parts else pd.DataFrame()

    LOGGER.info(
        "Candidate A: %d events; Candidate B: %d events", len(cand_a), len(cand_b)
    )

    LOGGER.info("Verifying reproducibility …")
    reproducibility = verify_reproducibility(
        cand_a, cand_b, displacements, bars_by_instrument, swings_by_instrument
    )

    counts = summarize_candidate_counts(cand_a, cand_b, displacements)
    selection = select_candidate(counts, reproducibility)

    LOGGER.info("Selected candidate: %s", selection["selected_candidate"])

    write_outputs(
        cand_a, cand_b, cand_a_misses, cand_b_misses,
        counts, reproducibility, selection, plots_dir, results_dir,
    )

    print("EXP-022 complete.")
    print(f"Selected candidate: {selection['selected_candidate']}")
    print(f"Reason: {selection['selection_reason']}")
    print(f"Plots:   {plots_dir}")
    print(f"Results: {results_dir}")


def main() -> None:
    """Entry point for manual execution."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_experiment()


if __name__ == "__main__":
    main()
