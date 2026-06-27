"""Experiment EXP-022: AVWAP Original Lifetime Move Study (CF-AVWAP-001 / HYP-003).

Implements the approved analysis plan (analysis-plan.md). EXP-022 tests whether
EXP-020 AVWAP bounce events resolve the *registered band-target / trend-change
lifetime method* more favorably than matched non-event lifetime analogs drawn
from the same regime. The primary confirmatory read is the domain-level,
instrument-averaged event-minus-control **favorable target-completion rate**
difference (percentage points).

Pipeline:
    1. Dependency gate on the EXP-020 substrate (SUPPORTED_FULL, ready 5m/1h/4h,
       0 invariant failures, deterministic replay). Load avwap_events.csv and
       avwap_state_summary.csv only after the gate passes.
    2. Holdout-safe domain reconstruction (first-70% slice, EXP-004/020/021
       convention) and a hard-fail event->domain-bar join.
    3. Lifetime completion scan on each event using the *frozen* EXP-020
       favorable/adverse target prices: favorable target, adverse target,
       trend-change (first opposite MA(20,50) regime confirmation), or unfinished.
    4. Same-regime matched non-event controls (EXP-021 rule). Each event's frozen
       target *distances* (log bps) are transferred to the control close, giving a
       like-for-like target challenge, then the control runs the same lifetime
       scan with the same trend-change boundary.
    5. Instrument-averaged domain primary test: equal weight per reportable
       instrument; regime-cluster bootstrap CI of the favorable-rate difference, a
       stratified paired permutation p-value, and Holm adjustment across domains.
       A regime-cluster bootstrap CI of the target-completion lifetime-expectancy
       advantage is a required consistency check.
    6. Censoring/stratification diagnostics incl. the matched-pair
       volatility-context ratio that drives the predeclared confound downgrade,
       and five bounded visualisations.

Methodology notes (recorded in run_metadata.json -> method_notes):
    * First completion is the first completed real domain ``Close`` by time.
      Intrabar highs/lows are deliberately excluded by scope. The scan is
      vectorized but preserves first-hit-by-time ordering; it is never a shortcut
      that changes tie or temporal-order semantics.
    * The paired permutation is the rate analog of the EXP-021 paired sign flip:
      under the null that an event outcome is exchangeable with its matched
      control outcomes, within each matched set the single event slot is
      reassigned uniformly at random among that set's completed moves. This
      preserves the observed event and control target-completion denominators
      exactly and is stratified because reassignment never crosses matched sets
      (hence never crosses instrument/direction).
    * Lifetime expectancy used in the FOR/AGAINST consistency check is the
      direction-signed real-close log return (bps) over *target completions*
      (favorable+adverse), aligned with the favorable-rate denominator.
      Trend-change expectancy is reported separately and is not part of the
      primary decision.

The final 30% global holdout is never loaded: ``load_analysis_data`` slices the
first 70% in a lazy plan before collection, and every event/control is re-fenced
to the analysis-set end via the domain-bar join and the completion scan.

Run:
    cd <project-root> && python python/experiments/EXP-022/code/run_experiment.py
"""
from __future__ import annotations

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

from xen.referee_calibration import (  # noqa: E402
    build_domain_frames,
    list_timebar_files,
    load_analysis_data,
    seed_for,
)


LOGGER = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-022"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = PROJECT_ROOT / "data"
EXPERIMENT_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
DEP_RESULTS_DIR = PROJECT_ROOT / "python" / "experiments" / "EXP-020" / "results"

DOMAINS: tuple[str, ...] = ("5m", "1h", "4h")

# Control construction (scope Matched Non-Event Lifetime Analog; EXP-021 rule).
MAX_CONTROLS = 5
MIN_CONTROLS = 3
EXCLUSION_BARS = 6

# Reportability (scope Success / Failure Criteria): per instrument, at least this
# many *target-completed* event moves AND matched-control analogs; a domain needs
# at least DOMAIN_MIN_INSTRUMENTS reportable instruments.
MIN_TARGET_COMPLETED = 30
DOMAIN_MIN_INSTRUMENTS = 3

# Local-volatility context diagnostic (scope/plan): 20-bar MAD of typical-price
# log returns ending at and including the reference bar; ratio bounds for the
# predeclared volatility-context confound downgrade.
LOCALVOL_WINDOW = 20
VOL_CONTEXT_BOUNDS = (0.5, 2.0)

# Censoring inconclusive trigger: >50% unfinished event moves.
UNFINISHED_MAJORITY = 0.5

# Inference (>= 10,000 resamples; non-parametric).
N_BOOT = 10_000
N_PERM = 10_000
BOOT_CHUNK = 2_000
PERM_CHUNK = 1_000
CI_PERCENTILES = (2.5, 97.5)
ALPHA = 0.05

# Expected EXP-020 dependency state.
DEP_REQUIRED_STATUS = "SUPPORTED_FULL"
DEP_REQUIRED_DOMAINS = {"5m", "1h", "4h"}
REQUIRED_DEP_ARTIFACTS: tuple[str, ...] = (
    "run_metadata.json",
    "avwap_events.csv",
    "avwap_state_summary.csv",
    "domain_readiness.csv",
    "invariant_checks.csv",
    "determinism_check.csv",
)

EVENT_TIME_COLUMNS = ("anchor_time", "armed_time", "trigger_time")
REGIME_TIME_COLUMNS = ("confirm_time", "anchor_time")

REGISTRY_REFS = {
    "candidate_family": "CF-AVWAP-001",
    "hypothesis": "HYP-003",
    "family_spec": "docs/signal-registry/candidate-families/avwap.md",
    "checkpoint": "docs/experiments-docs/checkpoints/2026-06-07-004-avwap-signal-exploration",
}

# Outcome labels.
OUT_FAVORABLE = "favorable"
OUT_ADVERSE = "adverse"
OUT_TREND = "trend_change"
OUT_UNFINISHED = "unfinished"
TARGET_OUTCOMES = (OUT_FAVORABLE, OUT_ADVERSE)


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
    """Write result dict rows to ``path`` as CSV (empty-safe)."""
    if not rows:
        path.write_text("")
        return
    pl.DataFrame(rows).write_csv(path)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write a JSON payload with stable formatting."""
    path.write_text(json.dumps(payload, indent=2, default=str))


def cast_time_columns(frame: pl.DataFrame, columns: tuple[str, ...]) -> pl.DataFrame:
    """Cast CSV-loaded timestamp columns to canonical ``Datetime('us')``."""
    exprs = []
    for col in columns:
        if col not in frame.columns:
            continue
        if frame.schema[col] == pl.Utf8:
            exprs.append(pl.col(col).str.to_datetime(time_unit="us"))
        else:
            exprs.append(pl.col(col).cast(pl.Datetime("us")))
    return frame.with_columns(exprs) if exprs else frame


def load_dependency_metadata() -> dict[str, Any]:
    """Load the EXP-020 run metadata (raises if the artifact is missing)."""
    path = DEP_RESULTS_DIR / "run_metadata.json"
    if not path.exists():
        raise FileNotFoundError(f"EXP-020 dependency metadata not found: {path}")
    return json.loads(path.read_text())


def _truthy(value: Any) -> bool:
    """Interpret CSV bool values consistently across Polars parser versions."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return bool(value)


def _missing_columns(frame: pl.DataFrame, columns: tuple[str, ...]) -> list[str]:
    """Return required columns absent from ``frame``."""
    return sorted(set(columns).difference(frame.columns))


def check_dependency_artifacts() -> tuple[bool, list[str]]:
    """Verify required EXP-020 artifacts directly, not only via metadata."""
    reasons: list[str] = []
    missing_files = [name for name in REQUIRED_DEP_ARTIFACTS if not (DEP_RESULTS_DIR / name).exists()]
    if missing_files:
        return False, [f"missing EXP-020 dependency artifacts: {missing_files}"]

    readiness = pl.read_csv(DEP_RESULTS_DIR / "domain_readiness.csv")
    invariant = pl.read_csv(DEP_RESULTS_DIR / "invariant_checks.csv")
    determinism = pl.read_csv(DEP_RESULTS_DIR / "determinism_check.csv")

    missing = _missing_columns(readiness, ("domain", "ready"))
    if missing:
        reasons.append(f"domain_readiness.csv missing columns: {missing}")
    else:
        ready_domains = {
            str(domain)
            for domain, ready in zip(readiness.get_column("domain"), readiness.get_column("ready"), strict=True)
            if _truthy(ready)
        }
        if ready_domains != DEP_REQUIRED_DOMAINS:
            reasons.append(f"domain_readiness ready domains={sorted(ready_domains)} != {sorted(DEP_REQUIRED_DOMAINS)}")

    missing = _missing_columns(invariant, ("n_violations", "passed"))
    if missing:
        reasons.append(f"invariant_checks.csv missing columns: {missing}")
    else:
        total_violations = int(invariant.get_column("n_violations").sum())
        if total_violations != 0:
            reasons.append(f"invariant_checks total n_violations={total_violations} != 0")
        if not all(_truthy(v) for v in invariant.get_column("passed").to_list()):
            reasons.append("invariant_checks.csv contains failed rows")

    missing = _missing_columns(determinism, ("events_match", "regimes_match"))
    if missing:
        reasons.append(f"determinism_check.csv missing columns: {missing}")
    else:
        events_ok = all(_truthy(v) for v in determinism.get_column("events_match").to_list())
        regimes_ok = all(_truthy(v) for v in determinism.get_column("regimes_match").to_list())
        if not events_ok or not regimes_ok:
            reasons.append(f"determinism_check failed rows (events_match={events_ok}, regimes_match={regimes_ok})")

    return len(reasons) == 0, reasons


def check_dependency_gate(meta: dict[str, Any]) -> tuple[bool, list[str]]:
    """Assert the EXP-020 substrate gate; return (passed, failure reasons)."""
    reasons: list[str] = []
    if meta.get("overall_status") != DEP_REQUIRED_STATUS:
        reasons.append(f"overall_status={meta.get('overall_status')} != {DEP_REQUIRED_STATUS}")
    if set(meta.get("ready_domains", [])) != DEP_REQUIRED_DOMAINS:
        reasons.append(f"ready_domains={meta.get('ready_domains')} != {sorted(DEP_REQUIRED_DOMAINS)}")
    if int(meta.get("invariant_failure_count", -1)) != 0:
        reasons.append(f"invariant_failure_count={meta.get('invariant_failure_count')} != 0")
    if not bool(meta.get("determinism_pass", False)):
        reasons.append("determinism_pass is not true")
    return (len(reasons) == 0, reasons)


def load_substrate_tables() -> tuple[pl.DataFrame, pl.DataFrame]:
    """Load EXP-020 events and regime summary, with canonical time dtypes."""
    events = pl.read_csv(DEP_RESULTS_DIR / "avwap_events.csv", try_parse_dates=True)
    regimes = pl.read_csv(DEP_RESULTS_DIR / "avwap_state_summary.csv", try_parse_dates=True)
    return cast_time_columns(events, EVENT_TIME_COLUMNS), cast_time_columns(regimes, REGIME_TIME_COLUMNS)


# --------------------------------------------------------------------------- #
# Domain reconstruction + holdout-safe join guard
# --------------------------------------------------------------------------- #
def build_cell_frames() -> tuple[dict[tuple[str, str], pl.DataFrame], dict[str, str]]:
    """Rebuild first-70% 5m/1h/4h domain bars per instrument (EXP-020 convention).

    Frames retain full OHLC (High/Low/Close) so the typical-price volatility
    context can be computed without a second data pass.
    """
    files = list_timebar_files(DATA_DIR)
    if not files:
        raise FileNotFoundError(f"no timebar files under {DATA_DIR / 'timebars'}")
    cell_frames: dict[tuple[str, str], pl.DataFrame] = {}
    analysis_end: dict[str, str] = {}
    for path in tqdm(files, desc="rebuild domain bars"):
        data = load_analysis_data(path)
        analysis_end[data.instrument] = data.analysis_end
        for domain, frame in build_domain_frames(data.frame).items():
            cell_frames[(data.instrument, domain)] = frame
    return cell_frames, analysis_end


def validate_event_join(events_cell: pl.DataFrame, frame: pl.DataFrame, label: str) -> None:
    """Hard-fail if any event's ``trigger_idx`` row disagrees with the domain bar.

    Re-asserts the holdout fence: every ``trigger_idx`` must index a real bar in
    the first-70% domain frame, and its ``CloseTime`` / ``Close`` must match the
    EXP-020 event exactly. Mismatches are implementation errors, not data to
    repair silently.
    """
    n = frame.height
    idx = events_cell.get_column("trigger_idx").to_numpy()
    if events_cell.height and (idx.min() < 0 or idx.max() >= n):
        raise ValueError(f"{label}: trigger_idx out of domain range [0,{n}) (holdout fence breach).")
    close_arr = frame.get_column("Close").to_numpy().astype(float)
    time_list = frame.get_column("CloseTime").to_list()
    ev_close = events_cell.get_column("trigger_close").to_numpy().astype(float)
    ev_time = events_cell.get_column("trigger_time").to_list()
    close_bad = int(np.sum(~np.isclose(close_arr[idx], ev_close, rtol=1e-9, atol=1e-9)))
    time_bad = sum(1 for k, t_idx in enumerate(idx) if time_list[t_idx] != ev_time[k])
    if close_bad or time_bad:
        raise ValueError(
            f"{label}: event/domain join mismatch (close_bad={close_bad}, time_bad={time_bad}); "
            "domain reconstruction does not reproduce the EXP-020 substrate."
        )


def validate_regime_join(regimes_cell: pl.DataFrame, frame: pl.DataFrame, label: str) -> None:
    """Hard-fail if any regime index falls outside the first-70% domain frame."""
    n = frame.height
    if not regimes_cell.height:
        return
    for col in ("regime_start_idx", "regime_end_idx", "confirm_idx", "anchor_idx"):
        arr = regimes_cell.get_column(col).to_numpy()
        if arr.min() < 0 or arr.max() >= n:
            raise ValueError(f"{label}: regime column {col} out of domain range [0,{n}) (holdout fence breach).")


# --------------------------------------------------------------------------- #
# Regime lookup + trend-change boundary (pure, deterministic)
# --------------------------------------------------------------------------- #
def build_regime_lut(regimes_cell: pl.DataFrame) -> dict[int, dict[str, int]]:
    """Map ``regime_id`` -> start/end/anchor index and direction for one cell."""
    lut: dict[int, dict[str, int]] = {}
    for r in regimes_cell.iter_rows(named=True):
        lut[int(r["regime_id"])] = {
            "start_idx": int(r["regime_start_idx"]),
            "end_idx": int(r["regime_end_idx"]),
            "anchor_idx": int(r["anchor_idx"]),
            "direction": int(r["direction"]),
        }
    return lut


def build_trend_change_map(regimes_cell: pl.DataFrame) -> dict[int, int]:
    """Map each ``regime_id`` to the next opposite-direction regime's confirm bar.

    The trend-change completion bar for any move inside a regime is the first
    later MA(20,50) regime confirmation of the opposite direction. A single
    right-to-left pass records, for each regime, the nearest later confirmation
    of the opposite direction (look-ahead-safe: a real confirmation timestamp).
    Regimes with no later opposite confirmation are absent from the map (no
    trend-change is reachable within the analysis set).
    """
    ordered = regimes_cell.sort("regime_start_idx")
    rid = ordered.get_column("regime_id").to_numpy().astype(int)
    direction = ordered.get_column("direction").to_numpy().astype(int)
    start = ordered.get_column("regime_start_idx").to_numpy().astype(int)
    next_start_for_dir: dict[int, int] = {}
    tc_map: dict[int, int] = {}
    for i in range(len(rid) - 1, -1, -1):
        opposite = -int(direction[i])
        if opposite in next_start_for_dir:
            tc_map[int(rid[i])] = next_start_for_dir[opposite]
        next_start_for_dir[int(direction[i])] = int(start[i])
    return tc_map


# --------------------------------------------------------------------------- #
# Same-regime control construction (pure, deterministic; EXP-021 rule)
# --------------------------------------------------------------------------- #
def build_exclusion_masks(n: int, trigger_idx: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return (is_trigger, near_trigger) boolean masks over domain-bar indices.

    ``near_trigger[c]`` is true when ``c`` is within ``EXCLUSION_BARS`` of any
    bounce trigger in the same instrument/domain cell.
    """
    is_trigger = np.zeros(n, dtype=bool)
    near_trigger = np.zeros(n, dtype=bool)
    for t in trigger_idx:
        is_trigger[t] = True
        lo = max(0, int(t) - EXCLUSION_BARS)
        hi = min(n - 1, int(t) + EXCLUSION_BARS)
        near_trigger[lo : hi + 1] = True
    return is_trigger, near_trigger


def regime_candidate_base(
    confirm_idx: int,
    end_idx: int,
    is_trigger: np.ndarray,
    near_trigger: np.ndarray,
) -> np.ndarray:
    """Eligible non-event control bars in ``(confirm_idx, end_idx]`` for one regime.

    Candidates are in the same regime's active AVWAP window, are not trigger
    bars, and lie outside the 6-bar window around any trigger in the cell.
    """
    if end_idx <= confirm_idx:
        return np.empty(0, dtype=np.int64)
    cand = np.arange(confirm_idx + 1, end_idx + 1, dtype=np.int64)
    keep = ~is_trigger[cand] & ~near_trigger[cand]
    return cand[keep]


def select_controls(
    base: np.ndarray,
    anchor_idx: int,
    event_anchor_age: int,
    trigger_idx: int,
    n: int,
) -> list[int]:
    """Deterministically pick up to ``MAX_CONTROLS`` same-regime controls.

    Lifetime eligibility requires at least one future completed bar to begin a
    scan (``base + 1 <= n - 1``); censoring then resolves short windows as
    trend-change/unfinished symmetrically with events. Ranking is by nearest
    anchor age, then nearest timestamp (index proxy within a cell), then row
    index as a stable final tiebreak.
    """
    if base.size == 0:
        return []
    eligible = base[base + 1 <= n - 1]
    if eligible.size == 0:
        return []
    keys = [
        (abs((int(c) - anchor_idx) - event_anchor_age), abs(int(c) - trigger_idx), int(c))
        for c in eligible
    ]
    order = sorted(range(eligible.size), key=lambda k: keys[k])
    return [int(eligible[k]) for k in order[:MAX_CONTROLS]]


# --------------------------------------------------------------------------- #
# Lifetime scan + local-volatility context (pure, deterministic)
# --------------------------------------------------------------------------- #
def frame_localvol_bps(typical_price: np.ndarray, window: int) -> np.ndarray:
    """Rolling MAD (bps) of typical-price log returns ending at each bar.

    ``localvol[r]`` is the median absolute deviation of the ``window`` log
    returns ending at and including bar ``r`` (look-ahead-safe), scaled to basis
    points. Bars without a full window are ``NaN``.
    """
    n = typical_price.size
    out = np.full(n, np.nan)
    if n < window + 1:
        return out
    log_ret = np.diff(np.log(typical_price))  # length n-1; log_ret[k] is return at bar k+1
    windows = np.lib.stride_tricks.sliding_window_view(log_ret, window)  # (n-window, window)
    med = np.median(windows, axis=1, keepdims=True)
    mad = np.median(np.abs(windows - med), axis=1)
    # Window starting at s covers returns at bars s+1..s+window, i.e. ends at bar s+window.
    out[window:] = mad * 10_000.0
    return out


def scan_lifetime(
    close: np.ndarray,
    log_close: np.ndarray,
    start_idx: int,
    direction: int,
    favorable_target: float,
    adverse_target: float,
    trend_change_idx: int | None,
    analysis_end_idx: int,
) -> tuple[str, int | None, int | None, float | None, bool]:
    """Resolve one move's lifetime outcome on real completed closes.

    Scans completed closes after ``start_idx``. The first close to satisfy a
    target (direction-signed, close-relative) completes the move; targets take
    precedence at the trend-change bar. If no target is hit through the
    trend-change bar, the move is a trend-change completion; if there is no
    reachable trend-change, it is unfinished at the analysis-set end.

    Returns ``(outcome, completion_idx, bars_to_completion, lifetime_bps, tie)``.
    ``tie`` flags the geometrically impossible simultaneous favorable+adverse
    close (an implementation error to be counted and reported).
    """
    has_tc = trend_change_idx is not None and trend_change_idx <= analysis_end_idx
    scan_end = int(trend_change_idx) if has_tc else int(analysis_end_idx)
    if scan_end <= start_idx:  # no future completed bar to scan
        return OUT_UNFINISHED, None, None, None, False

    seg = close[start_idx + 1 : scan_end + 1]
    fav_hits = direction * (seg - favorable_target) >= 0.0
    adv_hits = direction * (seg - adverse_target) <= 0.0
    fav_first = int(np.argmax(fav_hits)) if fav_hits.any() else None
    adv_first = int(np.argmax(adv_hits)) if adv_hits.any() else None

    tie = fav_first is not None and adv_first is not None and fav_first == adv_first
    if fav_first is None and adv_first is None:
        if has_tc:
            return OUT_TREND, scan_end, scan_end - start_idx, _signed_bps(log_close, start_idx, scan_end, direction), False
        return OUT_UNFINISHED, None, None, None, False

    fav_pos = fav_first if fav_first is not None else seg.size + 1
    adv_pos = adv_first if adv_first is not None else seg.size + 1
    if fav_pos <= adv_pos:  # favorable wins ties deterministically (impossible geometrically)
        outcome, hit = OUT_FAVORABLE, fav_pos
    else:
        outcome, hit = OUT_ADVERSE, adv_pos
    completion_idx = start_idx + 1 + hit
    return outcome, completion_idx, completion_idx - start_idx, _signed_bps(log_close, start_idx, completion_idx, direction), tie


def _signed_bps(log_close: np.ndarray, start_idx: int, end_idx: int, direction: int) -> float:
    """Direction-signed real-close log return in bps from ``start_idx`` to ``end_idx``."""
    return float(10_000.0 * direction * (log_close[end_idx] - log_close[start_idx]))


def transfer_targets(
    direction: int,
    event_favorable_target: float,
    event_adverse_target: float,
    event_trigger_close: float,
    control_close: float,
) -> tuple[float, float, float, float]:
    """Transfer the event's frozen target *distances* (log bps) to a control close.

    Returns ``(favorable_bps, adverse_bps, control_favorable_target,
    control_adverse_target)``. ``favorable_bps`` must be ``> 0`` and
    ``adverse_bps`` must be ``< 0`` for a valid event target geometry.
    """
    favorable_bps = direction * 10_000.0 * np.log(event_favorable_target / event_trigger_close)
    adverse_bps = direction * 10_000.0 * np.log(event_adverse_target / event_trigger_close)
    control_favorable_target = control_close * np.exp(direction * favorable_bps / 10_000.0)
    control_adverse_target = control_close * np.exp(direction * adverse_bps / 10_000.0)
    return float(favorable_bps), float(adverse_bps), float(control_favorable_target), float(control_adverse_target)


# --------------------------------------------------------------------------- #
# Per-cell processing: lifetime observations + control diagnostics
# --------------------------------------------------------------------------- #
def process_cell(
    instrument: str,
    domain: str,
    events_cell: pl.DataFrame,
    regimes_cell: pl.DataFrame,
    frame: pl.DataFrame,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Build event + matched-control lifetime records and cell-level counters."""
    n = frame.height
    close = frame.get_column("Close").to_numpy().astype(float)
    log_close = np.log(close)
    typical = (
        frame.get_column("High").to_numpy().astype(float)
        + frame.get_column("Low").to_numpy().astype(float)
        + close
    ) / 3.0
    localvol = frame_localvol_bps(typical, LOCALVOL_WINDOW)
    analysis_end_idx = n - 1

    regime_lut = build_regime_lut(regimes_cell)
    tc_map = build_trend_change_map(regimes_cell)
    trig = events_cell.get_column("trigger_idx").to_numpy().astype(np.int64)
    is_trigger, near_trigger = build_exclusion_masks(n, trig)
    base_cache: dict[int, np.ndarray] = {}

    records: list[dict[str, Any]] = []
    counters = {"invalid_target_events": 0, "tie_completions": 0, "events_no_future_bars": 0}
    for ev in events_cell.iter_rows(named=True):
        rid = int(ev["regime_id"])
        if rid not in regime_lut:
            raise ValueError(f"{instrument}/{domain}: event regime_id={rid} absent from state summary.")
        meta = regime_lut[rid]
        if rid not in base_cache:
            base_cache[rid] = regime_candidate_base(meta["start_idx"], meta["end_idx"], is_trigger, near_trigger)
        ev_records, ev_counts = _event_with_controls(
            instrument, domain, ev, meta, tc_map.get(rid), base_cache[rid],
            n, close, log_close, localvol, analysis_end_idx,
        )
        records.extend(ev_records)
        for key, val in ev_counts.items():
            counters[key] += val
    return records, counters


def _event_with_controls(
    instrument: str, domain: str, ev: dict[str, Any], meta: dict[str, int],
    trend_change_idx: int | None, base: np.ndarray, n: int,
    close: np.ndarray, log_close: np.ndarray, localvol: np.ndarray, analysis_end_idx: int,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Lifetime record for one event plus its matched-control analogs."""
    counts = {"invalid_target_events": 0, "tie_completions": 0, "events_no_future_bars": 0}
    rid = int(ev["regime_id"])
    direction = int(ev["direction"])
    t = int(ev["trigger_idx"])
    trigger_close = float(ev["trigger_close"])
    fav_target = float(ev["favorable_target_at_trigger"])
    adv_target = float(ev["adverse_target_at_trigger"])
    is_pyramid = _truthy(ev["is_pyramid_bounce"])

    favorable_bps, adverse_bps, *_ = transfer_targets(
        direction, fav_target, adv_target, trigger_close, trigger_close
    )
    if not (favorable_bps > 0.0 and adverse_bps < 0.0):
        counts["invalid_target_events"] = 1
        return [], counts  # invalid target geometry: counted, never silently scanned
    if t + 1 > analysis_end_idx:
        counts["events_no_future_bars"] = 1

    outcome, comp_idx, bars, life_bps, tie = scan_lifetime(
        close, log_close, t, direction, fav_target, adv_target, trend_change_idx, analysis_end_idx
    )
    counts["tie_completions"] += int(tie)
    controls = select_controls(base, meta["anchor_idx"], int(ev["anchor_age_bars"]), t, n)
    reportable = len(controls) >= MIN_CONTROLS
    reason = "ok" if reportable else "insufficient_same_regime_controls"

    records = [_lifetime_row(
        instrument, domain, rid, direction, is_pyramid, "event", t, t, float(close[t]),
        fav_target, adv_target, favorable_bps, adverse_bps, outcome, comp_idx, bars, life_bps,
        float(localvol[t]), len(controls), reportable, reason,
    )]
    for c in controls:
        f_bps, a_bps, c_fav, c_adv = transfer_targets(direction, fav_target, adv_target, trigger_close, float(close[c]))
        c_outcome, c_comp, c_bars, c_life, c_tie = scan_lifetime(
            close, log_close, c, direction, c_fav, c_adv, trend_change_idx, analysis_end_idx
        )
        counts["tie_completions"] += int(c_tie)
        records.append(_lifetime_row(
            instrument, domain, rid, direction, is_pyramid, "control", c, t, float(close[c]),
            c_fav, c_adv, f_bps, a_bps, c_outcome, c_comp, c_bars, c_life,
            float(localvol[c]), len(controls), reportable, reason,
        ))
    return records, counts


def _lifetime_row(
    instrument: str, domain: str, regime_id: int, direction: int, is_pyramid: bool, role: str,
    start_idx: int, event_trigger_idx: int, start_close: float, favorable_target: float,
    adverse_target: float, favorable_bps: float, adverse_bps: float, outcome: str,
    completion_idx: int | None, bars_to_completion: int | None, lifetime_bps: float | None,
    localvol_bps: float, n_controls: int, reportable: bool, reason: str,
) -> dict[str, Any]:
    """Assemble one lifetime observation row (event or matched control)."""
    return {
        "instrument": instrument, "domain": domain, "regime_id": regime_id,
        "direction": direction, "is_pyramid_bounce": is_pyramid, "role": role,
        "start_idx": start_idx, "event_trigger_idx": event_trigger_idx, "start_close": start_close,
        "favorable_target": favorable_target, "adverse_target": adverse_target,
        "favorable_bps": favorable_bps, "adverse_bps": adverse_bps,
        "outcome": outcome, "completion_idx": completion_idx,
        "bars_to_completion": bars_to_completion, "lifetime_bps": lifetime_bps,
        "localvol_bps": localvol_bps, "n_controls": n_controls,
        "reportable_event": reportable, "reason": reason,
        "is_target_completed": outcome in TARGET_OUTCOMES,
        "is_favorable": outcome == OUT_FAVORABLE,
    }


# --------------------------------------------------------------------------- #
# Reportability + instrument-averaged ratio-difference estimator
# --------------------------------------------------------------------------- #
def reportable_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Records belonging to events with enough same-regime controls."""
    return [r for r in records if r["reportable_event"]]


def reportable_instruments(records: list[dict[str, Any]], instruments: list[str]) -> dict[str, list[str]]:
    """Map each domain to instruments with >=30 target-completed events AND controls."""
    out: dict[str, list[str]] = {}
    for domain in DOMAINS:
        keep: list[str] = []
        for inst in instruments:
            ev_done = sum(
                1 for r in records
                if r["instrument"] == inst and r["domain"] == domain
                and r["role"] == "event" and r["is_target_completed"]
            )
            ct_done = sum(
                1 for r in records
                if r["instrument"] == inst and r["domain"] == domain
                and r["role"] == "control" and r["is_target_completed"]
            )
            if ev_done >= MIN_TARGET_COMPLETED and ct_done >= MIN_TARGET_COMPLETED:
                keep.append(inst)
        out[domain] = keep
    return out


def build_ratio_clusters(
    records: list[dict[str, Any]], domain: str, instruments: list[str], kind: str
) -> dict[tuple[str, int], dict[str, np.ndarray]]:
    """Per-(instrument, direction) regime-cluster (num_e, den_e, num_c, den_c) arrays.

    ``kind='rate'`` -> numerator is favorable count, denominator is
    target-completed count. ``kind='expectancy'`` -> numerator is summed
    target-completion lifetime bps, denominator is target-completed count.
    """
    inst_set = set(instruments)
    grouped: dict[tuple[str, int], dict[int, list[float]]] = {}
    for r in records:
        if not (r["domain"] == domain and r["instrument"] in inst_set and r["is_target_completed"]):
            continue
        key = (r["instrument"], r["direction"])
        regime = grouped.setdefault(key, {}).setdefault(r["regime_id"], [0.0, 0.0, 0.0, 0.0])
        value = (1.0 if r["is_favorable"] else 0.0) if kind == "rate" else float(r["lifetime_bps"])
        if r["role"] == "event":
            regime[0] += value
            regime[1] += 1.0
        else:
            regime[2] += value
            regime[3] += 1.0
    clusters: dict[tuple[str, int], dict[str, np.ndarray]] = {}
    for key, regimes in grouped.items():
        vals = np.array(list(regimes.values()), dtype=float)  # (n_regimes, 4)
        clusters[key] = {"num_e": vals[:, 0], "den_e": vals[:, 1], "num_c": vals[:, 2], "den_c": vals[:, 3]}
    return clusters


def observed_ratio_diff(
    clusters: dict[tuple[str, int], dict[str, np.ndarray]], instruments: list[str], scale: float
) -> tuple[float, dict[str, dict[str, float]]]:
    """Instrument-averaged event-minus-control ratio difference (observed)."""
    per_inst: dict[str, dict[str, float]] = {}
    for inst in instruments:
        num_e = den_e = num_c = den_c = 0.0
        for (i, _d), arr in clusters.items():
            if i != inst:
                continue
            num_e += float(arr["num_e"].sum())
            den_e += float(arr["den_e"].sum())
            num_c += float(arr["num_c"].sum())
            den_c += float(arr["den_c"].sum())
        if den_e > 0 and den_c > 0:
            rate_e = num_e / den_e
            rate_c = num_c / den_c
            per_inst[inst] = {
                "event": rate_e * scale, "control": rate_c * scale,
                "diff": (rate_e - rate_c) * scale,
                "den_e": den_e, "den_c": den_c,
            }
    effect = float(np.mean([v["diff"] for v in per_inst.values()])) if per_inst else float("nan")
    return effect, per_inst


def cluster_bootstrap_ci(
    clusters: dict[tuple[str, int], dict[str, np.ndarray]],
    instruments: list[str], scale: float, rng: np.random.Generator,
) -> tuple[float, float]:
    """Regime-cluster bootstrap CI of the instrument-averaged ratio difference.

    Resamples ``regime_id`` clusters with replacement within each
    (instrument, direction) stratum, recomputes each instrument's pooled ratio
    difference, then averages across instruments. Same-regime controls make the
    clusters exact, so cross-cluster independence holds by construction.
    """
    acc = {inst: {k: np.zeros(N_BOOT) for k in ("num_e", "den_e", "num_c", "den_c")} for inst in instruments}
    for (inst, _direction), arr in clusters.items():
        r = arr["num_e"].size
        if r == 0:
            continue
        for start in range(0, N_BOOT, BOOT_CHUNK):
            size = min(BOOT_CHUNK, N_BOOT - start)
            idx = rng.integers(0, r, size=(size, r))
            for k in ("num_e", "den_e", "num_c", "den_c"):
                acc[inst][k][start : start + size] += arr[k][idx].sum(axis=1)
    diffs = []
    for inst in instruments:
        a = acc[inst]
        rate_e = np.divide(a["num_e"], a["den_e"], out=np.full(N_BOOT, np.nan), where=a["den_e"] > 0)
        rate_c = np.divide(a["num_c"], a["den_c"], out=np.full(N_BOOT, np.nan), where=a["den_c"] > 0)
        diffs.append((rate_e - rate_c) * scale)
    boot = np.nanmean(np.vstack(diffs), axis=0)
    lo, hi = np.percentile(boot, CI_PERCENTILES)
    return float(lo), float(hi)


# --------------------------------------------------------------------------- #
# Stratified paired permutation on the favorable-rate difference
# --------------------------------------------------------------------------- #
def build_permutation_sets(
    records: list[dict[str, Any]], domain: str, instruments: list[str]
) -> dict[str, dict[str, Any]]:
    """Per-instrument matched-set pools for the favorable-rate permutation.

    For each matched set (an event and its controls) we record, when the event
    is target-completed, the pooled favorable count and pooled size over the
    completed moves in that set. Controls of non-completed events contribute a
    constant favorable count to the control pool. Event/control target-completion
    denominators are exactly the observed marginals and are held fixed.
    """
    inst_set = set(instruments)
    # Group records by matched set: (instrument, event_trigger_idx).
    sets: dict[tuple[str, int], dict[str, Any]] = {}
    for r in records:
        if r["domain"] != domain or r["instrument"] not in inst_set:
            continue
        key = (r["instrument"], r["event_trigger_idx"])
        s = sets.setdefault(key, {"instrument": r["instrument"], "event_done": False,
                                  "event_fav": 0, "ctrl_done": 0, "ctrl_fav": 0})
        if not r["is_target_completed"]:
            continue
        if r["role"] == "event":
            s["event_done"] = True
            s["event_fav"] = int(r["is_favorable"])
        else:
            s["ctrl_done"] += 1
            s["ctrl_fav"] += int(r["is_favorable"])

    out: dict[str, dict[str, Any]] = {}
    for inst in instruments:
        pool_size, pool_fav = [], []  # over event-completed sets
        event_completed = 0
        control_completed = 0
        const_control_fav = 0  # favorable controls in event-not-completed sets
        for (i, _t), s in sets.items():
            if i != inst:
                continue
            control_completed += s["ctrl_done"]
            if s["event_done"]:
                event_completed += 1
                pool_size.append(1 + s["ctrl_done"])
                pool_fav.append(s["event_fav"] + s["ctrl_fav"])
            else:
                const_control_fav += s["ctrl_fav"]
        out[inst] = {
            "pool_size": np.array(pool_size, dtype=float),
            "pool_fav": np.array(pool_fav, dtype=float),
            "event_completed": event_completed,
            "control_completed": control_completed,
            "const_control_fav": const_control_fav,
        }
    return out


def permutation_p_rate(
    perm_sets: dict[str, dict[str, Any]], instruments: list[str], observed: float,
    scale: float, rng: np.random.Generator,
) -> float:
    """One-sided stratified paired permutation p-value for the favorable-rate advantage."""
    ge = 0
    for start in range(0, N_PERM, PERM_CHUNK):
        size = min(PERM_CHUNK, N_PERM - start)
        per_inst_diff = np.empty((len(instruments), size))
        for j, inst in enumerate(instruments):
            s = perm_sets[inst]
            ps, pf = s["pool_size"], s["pool_fav"]
            if ps.size:
                u = rng.random((size, ps.size))
                pseudo_event_fav = ((u * ps) < pf).sum(axis=1).astype(float)
            else:
                pseudo_event_fav = np.zeros(size)
            pool_fav_total = float(pf.sum())
            pseudo_control_fav = pool_fav_total - pseudo_event_fav + s["const_control_fav"]
            rate_e = pseudo_event_fav / s["event_completed"] if s["event_completed"] else np.nan
            rate_c = pseudo_control_fav / s["control_completed"] if s["control_completed"] else np.nan
            per_inst_diff[j] = (rate_e - rate_c) * scale
        ge += int(np.sum(np.nanmean(per_inst_diff, axis=0) >= observed))
    return (1 + ge) / (1 + N_PERM)


def holm_adjust(pvalues: dict[str, float]) -> dict[str, float]:
    """Holm step-down adjustment over a family of domain primary p-values."""
    items = sorted(pvalues.items(), key=lambda kv: kv[1])
    m = len(items)
    adjusted: dict[str, float] = {}
    running = 0.0
    for rank, (domain, p) in enumerate(items):
        running = max(running, min(1.0, (m - rank) * p))
        adjusted[domain] = running
    return adjusted


# --------------------------------------------------------------------------- #
# Domain evaluation + decisions
# --------------------------------------------------------------------------- #
def domain_unfinished_fraction(records: list[dict[str, Any]], domain: str, instruments: list[str]) -> float:
    """Fraction of reportable event moves in the domain that are unfinished."""
    inst_set = set(instruments)
    evs = [r for r in records if r["domain"] == domain and r["role"] == "event" and r["instrument"] in inst_set]
    if not evs:
        return float("nan")
    return sum(r["outcome"] == OUT_UNFINISHED for r in evs) / len(evs)


def median_vol_context_ratio(records: list[dict[str, Any]], domain: str, instruments: list[str]) -> float:
    """Median matched-pair control/event local-volatility ratio for the domain.

    Computed over reportable matched sets, pairing the event's local volatility
    with the mean local volatility of its controls (both look-ahead-safe, fixed
    20-bar window).
    """
    inst_set = set(instruments)
    ratios = matched_vol_context_ratios(
        r for r in records if r["domain"] == domain and r["instrument"] in inst_set
    )
    return float(np.median(ratios)) if ratios.size else float("nan")


def matched_vol_context_ratios(records: Any) -> np.ndarray:
    """Matched-set control/event local-volatility ratios.

    Each event contributes at most one ratio: mean control local-volatility over
    the event's matched controls divided by the event local-volatility.
    """
    by_set: dict[tuple[str, int], dict[str, list[float]]] = {}
    for r in records:
        if not np.isfinite(r["localvol_bps"]):
            continue
        key = (r["instrument"], r["event_trigger_idx"])
        bucket = by_set.setdefault(key, {"event": [], "control": []})
        bucket[r["role"]].append(r["localvol_bps"])
    ratios = []
    for bucket in by_set.values():
        if bucket["event"] and bucket["control"]:
            ev = bucket["event"][0]
            ct = float(np.mean(bucket["control"]))
            if ev > 0:
                ratios.append(ct / ev)
    return np.array(ratios, dtype=float)


def evaluate_domain(
    records: list[dict[str, Any]], domain: str, instruments: list[str]
) -> dict[str, Any]:
    """Compute favorable-rate diff + CI, expectancy diff + CI, vol ratio, censoring."""
    rate_clusters = build_ratio_clusters(records, domain, instruments, "rate")
    exp_clusters = build_ratio_clusters(records, domain, instruments, "expectancy")
    rate_effect, rate_per_inst = observed_ratio_diff(rate_clusters, instruments, scale=100.0)
    exp_effect, exp_per_inst = observed_ratio_diff(exp_clusters, instruments, scale=1.0)

    rate_rng = np.random.default_rng(seed_for(EXPERIMENT_ID, domain, "bootstrap_rate"))
    exp_rng = np.random.default_rng(seed_for(EXPERIMENT_ID, domain, "bootstrap_expectancy"))
    rate_ci = cluster_bootstrap_ci(rate_clusters, instruments, 100.0, rate_rng)
    exp_ci = cluster_bootstrap_ci(exp_clusters, instruments, 1.0, exp_rng)

    perm_sets = build_permutation_sets(records, domain, instruments)
    perm_rng = np.random.default_rng(seed_for(EXPERIMENT_ID, domain, "permutation"))
    raw_p = permutation_p_rate(perm_sets, instruments, rate_effect, 100.0, perm_rng)

    event_fav_rate = float(np.mean([v["event"] for v in rate_per_inst.values()])) if rate_per_inst else float("nan")
    control_fav_rate = float(np.mean([v["control"] for v in rate_per_inst.values()])) if rate_per_inst else float("nan")
    return {
        "rate_effect_pp": rate_effect, "rate_ci_low": rate_ci[0], "rate_ci_high": rate_ci[1],
        "exp_effect_bps": exp_effect, "exp_ci_low": exp_ci[0], "exp_ci_high": exp_ci[1],
        "raw_p": raw_p, "event_fav_rate_pct": event_fav_rate, "control_fav_rate_pct": control_fav_rate,
        "rate_per_instrument": rate_per_inst, "exp_per_instrument": exp_per_inst,
        "median_vol_context_ratio": median_vol_context_ratio(records, domain, instruments),
        "event_unfinished_frac": domain_unfinished_fraction(records, domain, instruments),
        "n_reportable_instruments": len(instruments), "reportable_instruments": sorted(instruments),
    }


def decide_domain_label(stat: dict[str, Any], holm_p: float) -> str:
    """Apply the scope's per-domain Evidence FOR / AGAINST / Inconclusive rules."""
    rate, ci_lo, ci_hi = stat["rate_effect_pp"], stat["rate_ci_low"], stat["rate_ci_high"]
    exp = stat["exp_effect_bps"]
    vol = stat["median_vol_context_ratio"]
    vol_ok = np.isfinite(vol) and VOL_CONTEXT_BOUNDS[0] <= vol <= VOL_CONTEXT_BOUNDS[1]
    for_core = rate > 0 and ci_lo > 0 and holm_p <= ALPHA and exp >= 0
    if for_core and not vol_ok:
        return "INCONCLUSIVE_VOLATILITY_CONTEXT"
    if for_core and stat["event_unfinished_frac"] > UNFINISHED_MAJORITY:
        return "INCONCLUSIVE_CENSORED"
    if for_core:
        return "EVIDENCE_FOR"
    if ci_hi <= 0:
        return "EVIDENCE_AGAINST"
    if np.isfinite(rate) and np.isfinite(exp) and rate > 0 > exp:
        return "INCONCLUSIVE_RATE_EXPECTANCY_CONFLICT"
    return "INCONCLUSIVE_SPANS_ZERO"


def overall_verdict(
    domain_stats: dict[str, dict[str, Any]], labels: dict[str, str], reportable_domains: list[str]
) -> str:
    """Combine per-domain labels into the experiment verdict (scope rules)."""
    if not reportable_domains:
        return "REFUTED"  # Evidence AGAINST: no domain is lifetime-reportable
    if any(labels[d] == "EVIDENCE_FOR" for d in reportable_domains):
        return "SUPPORTED"
    if all(domain_stats[d]["rate_ci_high"] <= 0 for d in reportable_domains):
        return "REFUTED"
    if all(domain_stats[d]["exp_effect_bps"] < 0 for d in reportable_domains):
        return "REFUTED"
    if all(domain_stats[d]["event_unfinished_frac"] > UNFINISHED_MAJORITY for d in reportable_domains):
        return "INCONCLUSIVE"
    return "INCONCLUSIVE"


# --------------------------------------------------------------------------- #
# Result-table builders
# --------------------------------------------------------------------------- #
def completion_summary_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Outcome counts/rates by instrument, domain, direction, is_pyramid, role."""
    rows: list[dict[str, Any]] = []
    keys = sorted({
        (r["instrument"], r["domain"], r["direction"], bool(r["is_pyramid_bounce"]), r["role"])
        for r in records
    })
    for inst, domain, direction, pyramid, role in keys:
        sub = [r for r in records if r["instrument"] == inst and r["domain"] == domain
               and r["direction"] == direction and bool(r["is_pyramid_bounce"]) == pyramid and r["role"] == role]
        fav = sum(r["outcome"] == OUT_FAVORABLE for r in sub)
        adv = sum(r["outcome"] == OUT_ADVERSE for r in sub)
        trend = sum(r["outcome"] == OUT_TREND for r in sub)
        unfin = sum(r["outcome"] == OUT_UNFINISHED for r in sub)
        target_done = fav + adv
        target_life = [r["lifetime_bps"] for r in sub if r["is_target_completed"]]
        trend_life = [r["lifetime_bps"] for r in sub if r["outcome"] == OUT_TREND]
        rows.append({
            "instrument": inst, "domain": domain, "direction": direction,
            "is_pyramid_bounce": pyramid, "role": role, "n_total": len(sub),
            "favorable_count": fav, "adverse_count": adv,
            "trend_change_count": trend, "unfinished_count": unfin,
            "favorable_target_rate_pct": (100.0 * fav / target_done) if target_done else None,
            "mean_target_lifetime_bps": float(np.mean(target_life)) if target_life else None,
            "mean_trend_change_lifetime_bps": float(np.mean(trend_life)) if trend_life else None,
        })
    return rows


def domain_test_rows(
    domain_stats: dict[str, dict[str, Any]], holm: dict[str, float],
    labels: dict[str, str], reportable_map: dict[str, list[str]],
) -> list[dict[str, Any]]:
    """Flatten per-domain favorable-rate/expectancy comparisons and decisions."""
    rows: list[dict[str, Any]] = []
    for domain in DOMAINS:
        stat = domain_stats.get(domain)
        reportable = domain in domain_stats
        rows.append({
            "domain": domain, "lifetime_reportable": reportable,
            "n_reportable_instruments": len(reportable_map[domain]),
            "reportable_instruments": ",".join(sorted(reportable_map[domain])),
            "event_favorable_rate_pct": stat["event_fav_rate_pct"] if stat else None,
            "control_favorable_rate_pct": stat["control_fav_rate_pct"] if stat else None,
            "rate_diff_pp": stat["rate_effect_pp"] if stat else None,
            "rate_ci_low_pp": stat["rate_ci_low"] if stat else None,
            "rate_ci_high_pp": stat["rate_ci_high"] if stat else None,
            "expectancy_diff_bps": stat["exp_effect_bps"] if stat else None,
            "expectancy_ci_low_bps": stat["exp_ci_low"] if stat else None,
            "expectancy_ci_high_bps": stat["exp_ci_high"] if stat else None,
            "median_vol_context_ratio": stat["median_vol_context_ratio"] if stat else None,
            "event_unfinished_frac": stat["event_unfinished_frac"] if stat else None,
            "raw_p": stat["raw_p"] if stat else None,
            "holm_p": holm.get(domain) if reportable else None,
            "decision": labels.get(domain) if reportable else None,
        })
    return rows


def control_diagnostic_rows(
    records: list[dict[str, Any]], all_records: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Matching counts, censoring, target-distance, and vol-context diagnostics.

    ``records`` are reportable observations; ``all_records`` is the full set so
    non-reportable events can be counted under ``insufficient_same_regime_controls``.
    """
    rows: list[dict[str, Any]] = []
    keys = sorted({(r["instrument"], r["domain"], r["direction"]) for r in all_records})
    for inst, domain, direction in keys:
        all_sub = [r for r in all_records if r["instrument"] == inst and r["domain"] == domain
                   and r["direction"] == direction]
        rep_sub = [r for r in records if r["instrument"] == inst and r["domain"] == domain
                   and r["direction"] == direction]
        ev_all = [r for r in all_sub if r["role"] == "event"]
        ev_rep = [r for r in rep_sub if r["role"] == "event"]
        ct_rep = [r for r in rep_sub if r["role"] == "control"]
        ev_vol = np.array([r["localvol_bps"] for r in ev_rep if np.isfinite(r["localvol_bps"])])
        ct_vol = np.array([r["localvol_bps"] for r in ct_rep if np.isfinite(r["localvol_bps"])])
        vol_ratios = matched_vol_context_ratios(rep_sub)
        rows.append({
            "instrument": inst, "domain": domain, "direction": direction,
            "n_events_total": len(ev_all),
            "n_events_reportable": len(ev_rep),
            "n_insufficient_same_regime_controls": sum(
                r["reason"] == "insufficient_same_regime_controls" for r in ev_all
            ),
            "n_controls_reportable": len(ct_rep),
            "mean_n_controls_reportable": float(np.mean([r["n_controls"] for r in ev_rep])) if ev_rep else None,
            "event_target_completed": sum(r["is_target_completed"] for r in ev_rep),
            "control_target_completed": sum(r["is_target_completed"] for r in ct_rep),
            "event_trend_change": sum(r["outcome"] == OUT_TREND for r in ev_rep),
            "event_unfinished": sum(r["outcome"] == OUT_UNFINISHED for r in ev_rep),
            "control_trend_change": sum(r["outcome"] == OUT_TREND for r in ct_rep),
            "control_unfinished": sum(r["outcome"] == OUT_UNFINISHED for r in ct_rep),
            "mean_favorable_bps": float(np.mean([r["favorable_bps"] for r in ev_rep])) if ev_rep else None,
            "mean_adverse_bps": float(np.mean([r["adverse_bps"] for r in ev_rep])) if ev_rep else None,
            "median_event_localvol_bps": float(np.median(ev_vol)) if ev_vol.size else None,
            "median_control_localvol_bps": float(np.median(ct_vol)) if ct_vol.size else None,
            "median_vol_context_ratio": float(np.median(vol_ratios)) if vol_ratios.size else None,
            "p25_vol_context_ratio": float(np.percentile(vol_ratios, 25)) if vol_ratios.size else None,
            "p75_vol_context_ratio": float(np.percentile(vol_ratios, 75)) if vol_ratios.size else None,
            "n_vol_context_pairs": int(vol_ratios.size),
        })
    return rows


# --------------------------------------------------------------------------- #
# Plotting helpers (bounded inputs only)
# --------------------------------------------------------------------------- #
def plot_outcome_composition(records: list[dict[str, Any]], save_path: Path) -> None:
    """Stacked outcome shares by domain for events and controls."""
    outcomes = [OUT_FAVORABLE, OUT_ADVERSE, OUT_TREND, OUT_UNFINISHED]
    colors = {"favorable": "#2ca02c", "adverse": "#d62728", "trend_change": "#ff7f0e", "unfinished": "#7f7f7f"}
    fig, ax = plt.subplots(figsize=(9, 5))
    labels, bottoms = [], []
    bar_idx = 0
    for domain in DOMAINS:
        for role in ("event", "control"):
            sub = [r for r in records if r["domain"] == domain and r["role"] == role and r["reportable_event"]]
            total = len(sub) or 1
            bottom = 0.0
            for oc in outcomes:
                frac = sum(r["outcome"] == oc for r in sub) / total
                ax.bar(bar_idx, frac, bottom=bottom, color=colors[oc],
                       label=oc if bar_idx == 0 else None, width=0.8)
                bottom += frac
            labels.append(f"{domain}\n{role}")
            bottoms.append(bar_idx)
            bar_idx += 1
        bar_idx += 0.5
    ax.set_xticks(bottoms)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("outcome share")
    ax.set_title("EXP-022 lifetime outcome composition (reportable moves)")
    ax.legend(fontsize=8, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_favorable_forest(domain_stats: dict[str, dict[str, Any]], save_path: Path) -> None:
    """Forest plot of the event-control favorable target-completion rate diff (pp)."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ypos, ylabels = [], []
    for y, domain in enumerate(DOMAINS):
        stat = domain_stats.get(domain)
        if stat is None:
            ax.text(0.0, y, f"{domain}: not reportable", va="center", fontsize=8, color="grey")
        else:
            ax.errorbar(stat["rate_effect_pp"], y,
                        xerr=[[stat["rate_effect_pp"] - stat["rate_ci_low"]],
                              [stat["rate_ci_high"] - stat["rate_effect_pp"]]],
                        fmt="o", color="#d62728", capsize=3)
        ypos.append(y)
        ylabels.append(domain)
    ax.axvline(0.0, ls="--", lw=0.8, color="grey")
    ax.set_yticks(ypos)
    ax.set_yticklabels(ylabels)
    ax.set_xlabel("event - control favorable target-completion rate (pp)")
    ax.set_title("EXP-022 favorable target-completion advantage (95% regime-cluster bootstrap CI)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_expectancy_forest(domain_stats: dict[str, dict[str, Any]],
                           summary_rows: list[dict[str, Any]], save_path: Path) -> None:
    """Expectancy forest: target-completion advantage (CI) plus trend-change means."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ypos, ylabels = [], []
    for y, domain in enumerate(DOMAINS):
        stat = domain_stats.get(domain)
        if stat is not None:
            ax.errorbar(stat["exp_effect_bps"], y,
                        xerr=[[stat["exp_effect_bps"] - stat["exp_ci_low"]],
                              [stat["exp_ci_high"] - stat["exp_effect_bps"]]],
                        fmt="s", color="#1f77b4", capsize=3, label="target adv." if y == 0 else None)
        else:
            ax.text(0.0, y, f"{domain}: not reportable", va="center", fontsize=8, color="grey")
        ypos.append(y)
        ylabels.append(domain)
    ax.axvline(0.0, ls="--", lw=0.8, color="grey")
    ax.set_yticks(ypos)
    ax.set_yticklabels(ylabels)
    ax.set_xlabel("event - control target-completion lifetime expectancy (bps)")
    ax.set_title("EXP-022 lifetime expectancy advantage (95% regime-cluster bootstrap CI)")
    if any(domain in domain_stats for domain in DOMAINS):
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_bars_to_completion(records: list[dict[str, Any]], save_path: Path) -> None:
    """Bars-to-completion distribution for event vs control target completions."""
    fig, axes = plt.subplots(1, len(DOMAINS), figsize=(4 * len(DOMAINS), 4), squeeze=False)
    for j, domain in enumerate(DOMAINS):
        ax = axes[0][j]
        ev = [r["bars_to_completion"] for r in records
              if r["domain"] == domain and r["role"] == "event" and r["is_target_completed"] and r["reportable_event"]]
        ct = [r["bars_to_completion"] for r in records
              if r["domain"] == domain and r["role"] == "control" and r["is_target_completed"] and r["reportable_event"]]
        if ev or ct:
            hi = float(np.percentile(np.array(ev + ct), 99)) or 1.0
            bins = np.linspace(0, hi, 40)
            if ev:
                ax.hist(ev, bins=bins, alpha=0.6, label="event", color="#d62728", density=True)
            if ct:
                ax.hist(ct, bins=bins, alpha=0.6, label="control", color="#1f77b4", density=True)
            ax.legend(fontsize=8)
        else:
            ax.text(0.5, 0.5, "not reportable", ha="center", va="center", transform=ax.transAxes)
        ax.set_title(f"{domain}")
        ax.set_xlabel("bars to target completion")
    fig.suptitle("EXP-022 bars-to-completion (target completions)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_direction_pyramid(records: list[dict[str, Any]], instruments: list[str], save_path: Path) -> None:
    """Heatmap of event favorable target-completion rate by direction x pyramid."""
    cols = [(d, dir_, pyr) for d in DOMAINS for dir_ in (1, -1) for pyr in (False, True)]
    mat = np.full((len(instruments), len(cols)), np.nan)
    for i, inst in enumerate(instruments):
        for jc, (domain, direction, pyr) in enumerate(cols):
            sub = [r for r in records if r["instrument"] == inst and r["domain"] == domain
                   and r["role"] == "event" and r["direction"] == direction
                   and bool(r["is_pyramid_bounce"]) == pyr and r["is_target_completed"] and r["reportable_event"]]
            if sub:
                mat[i, jc] = 100.0 * sum(r["is_favorable"] for r in sub) / len(sub)
    fig, ax = plt.subplots(figsize=(11, 4.5))
    im = ax.imshow(mat, cmap="RdYlGn", vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels([f"{d}\n{'bull' if s == 1 else 'bear'}\n{'pyr' if p else 'first'}" for d, s, p in cols],
                       fontsize=7)
    ax.set_yticks(range(len(instruments)))
    ax.set_yticklabels(instruments)
    for i in range(len(instruments)):
        for jc in range(len(cols)):
            if np.isfinite(mat[i, jc]):
                ax.text(jc, i, f"{mat[i, jc]:.0f}", ha="center", va="center", fontsize=6)
    fig.colorbar(im, ax=ax, label="event favorable target-completion rate (%)")
    ax.set_title("EXP-022 event favorable rate by direction x pyramid-bounce")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def write_blocked_metadata(reasons: list[str], dep_meta: dict[str, Any]) -> None:
    """Persist the Evidence-AGAINST/blocked outcome when the dependency gate fails."""
    write_json(RESULTS_DIR / "run_metadata.json", {
        "experiment_id": EXPERIMENT_ID,
        "title": "AVWAP Original Lifetime Move Study",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": "EVIDENCE_AGAINST",
        "dependency_gate": {"passed": False, "reasons": reasons,
                            "exp020_status": dep_meta.get("overall_status")},
        "registry": REGISTRY_REFS,
    })
    LOGGER.info("EXP-022 BLOCKED — EXP-020 dependency gate failed: %s", "; ".join(reasons))


def run() -> None:
    """Execute EXP-022 end to end and write all result artifacts."""
    ensure_output_dirs()
    dep_meta = load_dependency_metadata()
    gate_ok, reasons = check_dependency_gate(dep_meta)
    artifacts_ok, artifact_reasons = check_dependency_artifacts()
    reasons.extend(artifact_reasons)
    if not gate_ok or not artifacts_ok:
        write_blocked_metadata(reasons, dep_meta)
        return
    LOGGER.info("EXP-020 dependency gate PASSED (%s).", dep_meta.get("overall_status"))

    events, regimes = load_substrate_tables()
    cell_frames, analysis_end = build_cell_frames()
    instruments = sorted({i for (i, _d) in cell_frames} & set(events.get_column("instrument").unique().to_list()))

    records: list[dict[str, Any]] = []
    counters = {"invalid_target_events": 0, "tie_completions": 0, "events_no_future_bars": 0}
    for inst in tqdm(instruments, desc="cells: lifetime scan"):
        for domain in DOMAINS:
            frame = cell_frames[(inst, domain)]
            ev_cell = events.filter((pl.col("instrument") == inst) & (pl.col("domain") == domain))
            rg_cell = regimes.filter((pl.col("instrument") == inst) & (pl.col("domain") == domain))
            validate_event_join(ev_cell, frame, f"{inst}/{domain}")
            validate_regime_join(rg_cell, frame, f"{inst}/{domain}")
            cell_records, cell_counts = process_cell(inst, domain, ev_cell, rg_cell, frame)
            records.extend(cell_records)
            for key, val in cell_counts.items():
                counters[key] += val

    rep_records = reportable_records(records)
    reportable_map = reportable_instruments(records, instruments)
    reportable_domains = [d for d in DOMAINS if len(reportable_map[d]) >= DOMAIN_MIN_INSTRUMENTS]

    domain_stats: dict[str, dict[str, Any]] = {}
    primary_pvals: dict[str, float] = {}
    for domain in tqdm(reportable_domains, desc="domain inference"):
        domain_stats[domain] = evaluate_domain(rep_records, domain, reportable_map[domain])
        primary_pvals[domain] = domain_stats[domain]["raw_p"]
    holm = holm_adjust(primary_pvals) if primary_pvals else {}
    labels = {d: decide_domain_label(domain_stats[d], holm[d]) for d in reportable_domains}
    verdict = overall_verdict(domain_stats, labels, reportable_domains)

    _write_all_outputs(records, rep_records, domain_stats, holm, labels, reportable_map,
                       reportable_domains, instruments, verdict, dep_meta, analysis_end, counters)
    LOGGER.info("EXP-022 verdict: %s | reportable domains: %s", verdict, reportable_domains or "none")
    LOGGER.info("counters: %s", counters)


def _write_all_outputs(records, rep_records, domain_stats, holm, labels, reportable_map,
                       reportable_domains, instruments, verdict, dep_meta, analysis_end, counters) -> None:
    """Write every result table, plot, and the run metadata."""
    obs_cols = ["instrument", "domain", "regime_id", "direction", "is_pyramid_bounce", "role",
                "start_idx", "event_trigger_idx", "start_close", "favorable_target", "adverse_target",
                "favorable_bps", "adverse_bps", "outcome", "completion_idx", "bars_to_completion",
                "lifetime_bps", "localvol_bps", "n_controls", "reportable_event", "reason",
                "is_target_completed", "is_favorable"]
    pl.DataFrame(records).select(obs_cols).write_csv(RESULTS_DIR / "lifetime_observations.csv")
    write_rows(RESULTS_DIR / "lifetime_completion_summary.csv", completion_summary_rows(records))
    write_rows(RESULTS_DIR / "domain_lifetime_tests.csv",
               domain_test_rows(domain_stats, holm, labels, reportable_map))
    write_rows(RESULTS_DIR / "control_lifetime_diagnostics.csv",
               control_diagnostic_rows(rep_records, records))

    summary_rows = completion_summary_rows(records)
    plot_outcome_composition(records, PLOTS_DIR / "lifetime_outcome_composition.png")
    plot_favorable_forest(domain_stats, PLOTS_DIR / "favorable_completion_forest.png")
    plot_expectancy_forest(domain_stats, summary_rows, PLOTS_DIR / "lifetime_expectancy_forest.png")
    plot_bars_to_completion(records, PLOTS_DIR / "bars_to_completion_distribution.png")
    plot_direction_pyramid(records, instruments, PLOTS_DIR / "direction_pyramid_diagnostics.png")

    write_json(RESULTS_DIR / "run_metadata.json", {
        "experiment_id": EXPERIMENT_ID,
        "title": "AVWAP Original Lifetime Move Study",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": verdict,
        "dependency_gate": {"passed": True, "exp020_status": dep_meta.get("overall_status")},
        "instruments": instruments,
        "domains": list(DOMAINS),
        "reportable_instruments_by_domain": reportable_map,
        "reportable_domains": reportable_domains,
        "domain_decisions": labels,
        "holm_adjusted_primary_p": holm,
        "analysis_end_by_instrument": analysis_end,
        "integrity_counters": counters,
        "parameters": {
            "max_controls": MAX_CONTROLS, "min_controls": MIN_CONTROLS,
            "exclusion_bars": EXCLUSION_BARS, "control_scope": "same_regime_only",
            "min_target_completed": MIN_TARGET_COMPLETED,
            "domain_min_instruments": DOMAIN_MIN_INSTRUMENTS,
            "localvol_window": LOCALVOL_WINDOW, "vol_context_bounds": list(VOL_CONTEXT_BOUNDS),
            "unfinished_majority": UNFINISHED_MAJORITY,
            "n_bootstrap": N_BOOT, "n_permutation": N_PERM, "alpha": ALPHA,
            "ci_percentiles": list(CI_PERCENTILES),
            "domain_estimator": "instrument_averaged_equal_weight",
            "primary_statistic": "favorable_target_completion_rate_diff_pp",
        },
        "method_notes": {
            "first_completion": "first completed real domain Close by time; intrabar excluded; "
                                "vectorized first-hit preserves temporal ordering.",
            "trend_change": "nearest later opposite-direction MA(20,50) regime confirmation; "
                            "shared by an event and its same-regime controls.",
            "control_target_transfer": "event frozen favorable/adverse target distances (log bps) "
                                       "applied to the control close in the same direction.",
            "permutation": "rate analog of EXP-021 paired sign flip: within each matched set the "
                           "single event slot is reassigned uniformly among completed moves; "
                           "preserves observed event/control target-completion denominators; "
                           "stratified because reassignment never crosses matched sets.",
            "expectancy_consistency": "target-completion lifetime expectancy (favorable+adverse) "
                                      "drives the FOR/AGAINST consistency check; trend-change "
                                      "expectancy reported separately, not in the decision.",
            "holdout": "first-70% slice before collection; events/controls re-fenced to the "
                       "analysis-set end; final 30% global holdout never loaded.",
        },
        "domain_primary": {
            d: {
                "rate_diff_pp": domain_stats[d]["rate_effect_pp"],
                "rate_ci": [domain_stats[d]["rate_ci_low"], domain_stats[d]["rate_ci_high"]],
                "expectancy_diff_bps": domain_stats[d]["exp_effect_bps"],
                "median_vol_context_ratio": domain_stats[d]["median_vol_context_ratio"],
            }
            for d in reportable_domains
        },
        "registry": REGISTRY_REFS,
    })


def main() -> None:
    """Configure logging and run the experiment (manual execution entry point)."""
    configure_logging()
    run()


if __name__ == "__main__":
    main()
