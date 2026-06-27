"""Experiment EXP-025: AVWAP Line Support/Resistance Direct Test.

Implements the approved analysis plan from ``analysis-plan.md``. EXP-025 tests
whether EXP-020 AVWAP bounce trigger bars show direct event-bar rejection at the
AVWAP line versus matched same-regime, line-proximate non-event controls.

The experiment is diagnostic only. It does not run a candidate screen, does not
compute strategy P&L, does not use future-return horizons, and does not touch
the final 30 percent global holdout.

Run:
    cd <project-root> && python python/experiments/EXP-025/code/run_experiment.py
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402  (backend must be set first)
import numpy as np  # noqa: E402
import polars as pl  # noqa: E402
from tqdm.auto import tqdm  # noqa: E402

from xen.avwap import BAND_MULTIPLIER, compute_band_trace  # noqa: E402
from xen.referee_calibration import (  # noqa: E402
    DOMAIN_SPECS,
    build_domain_frames,
    load_analysis_data,
    seed_for,
)


LOGGER = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-025"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = PROJECT_ROOT / "data"
EXPERIMENT_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
DEP_EXP020_RESULTS_DIR = PROJECT_ROOT / "python" / "experiments" / "EXP-020" / "results"
DEP_EXP024_DIR = PROJECT_ROOT / "python" / "experiments" / "EXP-024"

DOMAINS: tuple[str, ...] = ("5m", "1h", "4h")

# Control construction (scope Matched-control dimensions).
MAX_CONTROLS = 5
MIN_CONTROLS = 3
EXCLUSION_BARS = 6
LINE_PROXIMITY_FLOOR_BPS = 1.0

# Reportability thresholds (scope Success / Failure Criteria).
MIN_REPORTABLE_EVENTS = 30
MIN_DIRECTION_EVENTS = 8
DOMAIN_MIN_INSTRUMENTS = 3
BALANCE_FAIL_THRESHOLD_BPS = 2.0

# Inference.
N_BOOT = 10_000
N_PERM = 10_000
BOOT_CHUNK = 2_000
PERM_CHUNK = 1_000
CI_PERCENTILES = (2.5, 97.5)
ALPHA = 0.05

# Expected dependency state.
DEP_REQUIRED_STATUS = "SUPPORTED_FULL"
DEP_REQUIRED_DOMAINS = {"5m", "1h", "4h"}
REQUIRED_EXP020_ARTIFACTS: tuple[str, ...] = (
    "run_metadata.json",
    "analysis_metadata.csv",
    "avwap_events.csv",
    "avwap_state_summary.csv",
    "domain_readiness.csv",
    "invariant_checks.csv",
    "determinism_check.csv",
)

TIME_COLUMNS = ("anchor_time", "armed_time", "trigger_time")
REGIME_TIME_COLUMNS = ("confirm_time", "anchor_time")
METADATA_TIME_COLUMNS = (
    "analysis_start_1m",
    "analysis_end_1m",
    "domain_min_close_time",
    "domain_max_close_time",
)

REGISTRY_REFS = {
    "candidate_family": "CF-AVWAP-001",
    "branch": "CF-AVWAP-001/DIAG-002",
    "multiplicity_registry": "docs/signal-registry/multiplicity-registry.md",
    "checkpoint": "docs/experiments-docs/checkpoints/2026-06-08-005-avwap-exit-and-branch-exploration",
}


# --------------------------------------------------------------------------- #
# Data containers
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class RegimeReplay:
    """Per-regime causal AVWAP replay arrays, indexed from ``anchor_idx``."""

    regime_id: int
    direction: int
    confirm_idx: int
    end_idx: int
    anchor_idx: int
    avwap: np.ndarray
    band_spread: np.ndarray
    band_spread_bps: np.ndarray
    close_to_avwap_bps: np.ndarray
    anchor_age_bars: np.ndarray
    finite: np.ndarray

    def offset(self, idx: int | np.ndarray) -> int | np.ndarray:
        """Translate domain-bar index/indices to replay-array offset(s)."""
        return idx - self.anchor_idx


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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write a JSON payload with stable formatting."""
    path.write_text(json.dumps(payload, indent=2, default=str))


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write result dict rows to ``path`` as CSV (empty-safe)."""
    if not rows:
        path.write_text("")
        return
    pl.DataFrame(rows).write_csv(path)


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


# --------------------------------------------------------------------------- #
# Dependency gate
# --------------------------------------------------------------------------- #
def load_dependency_metadata() -> dict[str, Any]:
    """Load EXP-020 run metadata."""
    path = DEP_EXP020_RESULTS_DIR / "run_metadata.json"
    if not path.exists():
        raise FileNotFoundError(f"EXP-020 dependency metadata not found: {path}")
    return json.loads(path.read_text())


def check_exp020_gate(meta: dict[str, Any]) -> tuple[bool, list[str]]:
    """Assert the EXP-020 substrate gate from metadata."""
    reasons: list[str] = []
    if meta.get("overall_status") != DEP_REQUIRED_STATUS:
        reasons.append(f"EXP-020 overall_status={meta.get('overall_status')} != {DEP_REQUIRED_STATUS}")
    if set(meta.get("ready_domains", [])) != DEP_REQUIRED_DOMAINS:
        reasons.append(f"EXP-020 ready_domains={meta.get('ready_domains')} != {sorted(DEP_REQUIRED_DOMAINS)}")
    if int(meta.get("invariant_failure_count", -1)) != 0:
        reasons.append(f"EXP-020 invariant_failure_count={meta.get('invariant_failure_count')} != 0")
    if not bool(meta.get("determinism_pass", False)):
        reasons.append("EXP-020 determinism_pass is not true")
    return len(reasons) == 0, reasons


def check_exp020_artifacts() -> tuple[bool, list[str]]:
    """Verify required EXP-020 artifact files and their direct gate fields."""
    reasons: list[str] = []
    missing_files = [name for name in REQUIRED_EXP020_ARTIFACTS if not (DEP_EXP020_RESULTS_DIR / name).exists()]
    if missing_files:
        return False, [f"missing EXP-020 artifacts: {missing_files}"]

    readiness = pl.read_csv(DEP_EXP020_RESULTS_DIR / "domain_readiness.csv")
    invariant = pl.read_csv(DEP_EXP020_RESULTS_DIR / "invariant_checks.csv")
    determinism = pl.read_csv(DEP_EXP020_RESULTS_DIR / "determinism_check.csv")

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


def check_exp024_documented() -> tuple[bool, list[str]]:
    """Verify EXP-024 is complete and post-governance approved."""
    reasons: list[str] = []
    results = DEP_EXP024_DIR / "results.md"
    review = DEP_EXP024_DIR / "governance" / "post-experiment-review.md"
    if not results.exists():
        reasons.append(f"missing EXP-024 results document: {results}")
    if not review.exists():
        reasons.append(f"missing EXP-024 post-governance review: {review}")
    elif "VERDICT: APPROVE" not in review.read_text().splitlines()[:3]:
        reasons.append("EXP-024 post-experiment review is not APPROVE")
    if results.exists() and "MIXED_OR_INCONCLUSIVE" not in results.read_text():
        reasons.append("EXP-024 results.md does not record MIXED_OR_INCONCLUSIVE context")
    return len(reasons) == 0, reasons


def write_dependency_blocked_metadata(reasons: list[str], dep_meta: dict[str, Any]) -> None:
    """Persist an Evidence-AGAINST outcome when dependencies fail."""
    write_json(
        RESULTS_DIR / "run_metadata.json",
        {
            "experiment_id": EXPERIMENT_ID,
            "title": "AVWAP Line Support/Resistance Direct Test",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "overall_status": "EVIDENCE_AGAINST_DEPENDENCY_GATE",
            "dependency_gate": {
                "passed": False,
                "reasons": reasons,
                "exp020_status": dep_meta.get("overall_status"),
            },
            "registry": REGISTRY_REFS,
        },
    )
    LOGGER.info("EXP-025 dependency gate failed: %s", "; ".join(reasons))


# --------------------------------------------------------------------------- #
# Source reconstruction + EXP-020 metadata equality
# --------------------------------------------------------------------------- #
def load_exp020_tables() -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """Load EXP-020 events, regimes, and reconstruction metadata."""
    events = pl.read_csv(DEP_EXP020_RESULTS_DIR / "avwap_events.csv", try_parse_dates=True)
    regimes = pl.read_csv(DEP_EXP020_RESULTS_DIR / "avwap_state_summary.csv", try_parse_dates=True)
    metadata = pl.read_csv(DEP_EXP020_RESULTS_DIR / "analysis_metadata.csv", try_parse_dates=True)
    return (
        cast_time_columns(events, TIME_COLUMNS),
        cast_time_columns(regimes, REGIME_TIME_COLUMNS),
        cast_time_columns(metadata, METADATA_TIME_COLUMNS),
    )


def _unique_source_files(metadata: pl.DataFrame) -> dict[str, str]:
    """Return the exact EXP-020 source file per instrument, raising on ambiguity."""
    out: dict[str, set[str]] = {}
    for row in metadata.select(["instrument", "source_file"]).iter_rows(named=True):
        out.setdefault(str(row["instrument"]), set()).add(str(row["source_file"]))
    ambiguous = {inst: files for inst, files in out.items() if len(files) != 1}
    if ambiguous:
        raise ValueError(f"EXP-020 metadata has ambiguous source files: {ambiguous}")
    return {inst: next(iter(files)) for inst, files in out.items()}


def build_scoped_cell_frames(
    metadata: pl.DataFrame,
) -> tuple[dict[tuple[str, str], pl.DataFrame], dict[str, str], list[dict[str, Any]]]:
    """Rebuild domain bars from exact EXP-020 source files and validate metadata."""
    source_files = _unique_source_files(metadata)
    expected_rows = {
        (str(row["instrument"]), str(row["domain"])): row
        for row in metadata.iter_rows(named=True)
        if str(row["domain"]) in DOMAINS
    }
    cell_frames: dict[tuple[str, str], pl.DataFrame] = {}
    analysis_end: dict[str, str] = {}
    check_rows: list[dict[str, Any]] = []

    for instrument in tqdm(sorted(source_files), desc="rebuild exact source files"):
        path = DATA_DIR / "timebars" / source_files[instrument]
        if not path.exists():
            raise FileNotFoundError(f"EXP-020 source file not found: {path}")
        data = load_analysis_data(path)
        if data.instrument != instrument:
            raise ValueError(f"{path.name}: loaded instrument={data.instrument} != metadata {instrument}")
        analysis_end[instrument] = data.analysis_end
        domains = build_domain_frames(data.frame)

        for domain in DOMAINS:
            frame = domains[domain]
            expected = expected_rows.get((instrument, domain))
            if expected is None:
                raise ValueError(f"EXP-020 metadata missing {instrument}/{domain}")
            actual_min = None if frame.is_empty() else frame.select(pl.min("CloseTime")).item()
            actual_max = None if frame.is_empty() else frame.select(pl.max("CloseTime")).item()
            row = {
                "instrument": instrument,
                "domain": domain,
                "source_file": path.name,
                "source_total_rows_expected": int(expected["source_total_rows"]),
                "source_total_rows_actual": int(data.total_rows),
                "analysis_rows_1m_expected": int(expected["analysis_rows_1m"]),
                "analysis_rows_1m_actual": int(data.analysis_rows),
                "domain_bars_expected": int(expected["domain_bars"]),
                "domain_bars_actual": int(frame.height),
                "domain_min_close_time_expected": expected["domain_min_close_time"],
                "domain_min_close_time_actual": actual_min,
                "domain_max_close_time_expected": expected["domain_max_close_time"],
                "domain_max_close_time_actual": actual_max,
            }
            row["passed"] = (
                row["source_total_rows_expected"] == row["source_total_rows_actual"]
                and row["analysis_rows_1m_expected"] == row["analysis_rows_1m_actual"]
                and row["domain_bars_expected"] == row["domain_bars_actual"]
                and row["domain_min_close_time_expected"] == row["domain_min_close_time_actual"]
                and row["domain_max_close_time_expected"] == row["domain_max_close_time_actual"]
            )
            check_rows.append(row)
            if not row["passed"]:
                raise ValueError(f"domain reconstruction mismatch: {row}")
            cell_frames[(instrument, domain)] = frame

    return cell_frames, analysis_end, check_rows


def validate_event_join(events_cell: pl.DataFrame, frame: pl.DataFrame, label: str) -> None:
    """Hard-fail if EXP-020 event trigger index/time/close does not match bars."""
    if events_cell.is_empty():
        return
    n = frame.height
    idx = events_cell.get_column("trigger_idx").to_numpy().astype(np.int64)
    if idx.min() < 0 or idx.max() >= n:
        raise ValueError(f"{label}: trigger_idx out of domain range [0,{n}) (holdout fence breach).")
    close_arr = frame.get_column("Close").to_numpy().astype(float)
    time_list = frame.get_column("CloseTime").to_list()
    ev_close = events_cell.get_column("trigger_close").to_numpy().astype(float)
    ev_time = events_cell.get_column("trigger_time").to_list()
    close_bad = int(np.sum(~np.isclose(close_arr[idx], ev_close, rtol=1e-9, atol=1e-9)))
    time_bad = sum(1 for k, t_idx in enumerate(idx) if time_list[t_idx] != ev_time[k])
    if close_bad or time_bad:
        raise ValueError(f"{label}: event/domain mismatch (close_bad={close_bad}, time_bad={time_bad})")


# --------------------------------------------------------------------------- #
# Causal AVWAP replay + scoring
# --------------------------------------------------------------------------- #
def replay_regime(frame: pl.DataFrame, regime: dict[str, Any]) -> RegimeReplay:
    """Replay per-bar AVWAP and MAD band values for one regime."""
    anchor_idx = int(regime["anchor_idx"])
    end_idx = int(regime["regime_end_idx"])
    trace = compute_band_trace(frame, anchor_idx, end_idx)
    avwap = trace["avwap"].astype(float)
    band_spread = (trace["upper"].astype(float) - avwap) / BAND_MULTIPLIER
    close = trace["close"].astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        band_spread_bps = 10_000.0 * np.log((avwap + band_spread) / avwap)
        close_to_avwap_bps = 10_000.0 * np.log(close / avwap)
    finite = (
        np.isfinite(avwap)
        & np.isfinite(band_spread)
        & np.isfinite(band_spread_bps)
        & np.isfinite(close_to_avwap_bps)
        & (avwap > 0.0)
        & (band_spread >= 0.0)
    )
    return RegimeReplay(
        regime_id=int(regime["regime_id"]),
        direction=int(regime["direction"]),
        confirm_idx=int(regime["confirm_idx"]),
        end_idx=end_idx,
        anchor_idx=anchor_idx,
        avwap=avwap,
        band_spread=band_spread,
        band_spread_bps=band_spread_bps,
        close_to_avwap_bps=close_to_avwap_bps,
        anchor_age_bars=np.arange(anchor_idx, end_idx + 1, dtype=np.int64) - anchor_idx,
        finite=finite,
    )


def valid_ohlc(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
    """Return finite, positive, internally valid OHLC masks."""
    return (
        np.isfinite(high)
        & np.isfinite(low)
        & np.isfinite(close)
        & (high > 0.0)
        & (low > 0.0)
        & (close > 0.0)
        & (high >= low)
    )


def line_rejection_components(
    direction: int,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    avwap: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute close rebound, adverse penetration, and line-rejection score."""
    valid = valid_ohlc(high, low, close) & np.isfinite(avwap) & (avwap > 0.0)
    rebound = np.full(close.size, np.nan, dtype=float)
    adverse = np.full(close.size, np.nan, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        if direction == 1:
            rebound[valid] = 10_000.0 * np.log(close[valid] / avwap[valid])
            adverse[valid] = np.maximum(0.0, 10_000.0 * np.log(avwap[valid] / low[valid]))
        elif direction == -1:
            rebound[valid] = 10_000.0 * np.log(avwap[valid] / close[valid])
            adverse[valid] = np.maximum(0.0, 10_000.0 * np.log(high[valid] / avwap[valid]))
        else:
            raise ValueError(f"direction must be +1 or -1, got {direction}")
    score = rebound - adverse
    return rebound, adverse, score


def build_exclusion_masks(n: int, trigger_idx: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return ``is_trigger`` and ``near_trigger`` masks over domain-bar indices."""
    is_trigger = np.zeros(n, dtype=bool)
    near_trigger = np.zeros(n, dtype=bool)
    for t_raw in trigger_idx:
        t = int(t_raw)
        is_trigger[t] = True
        lo = max(0, t - EXCLUSION_BARS)
        hi = min(n - 1, t + EXCLUSION_BARS)
        near_trigger[lo : hi + 1] = True
    return is_trigger, near_trigger


def regime_candidate_base(
    replay: RegimeReplay,
    is_trigger: np.ndarray,
    near_trigger: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
) -> np.ndarray:
    """Eligible line-proximate non-event controls for one regime."""
    if replay.end_idx <= replay.confirm_idx:
        return np.empty(0, dtype=np.int64)
    cand = np.arange(replay.confirm_idx + 1, replay.end_idx + 1, dtype=np.int64)
    offsets = replay.offset(cand)
    proximity_limit = np.maximum(LINE_PROXIMITY_FLOOR_BPS, replay.band_spread_bps[offsets])
    keep = (
        ~is_trigger[cand]
        & ~near_trigger[cand]
        & replay.finite[offsets]
        & valid_ohlc(high[cand], low[cand], close[cand])
        & (np.abs(replay.close_to_avwap_bps[offsets]) <= proximity_limit)
    )
    return cand[keep]


def select_controls(
    base: np.ndarray,
    replay: RegimeReplay,
    event_abs_distance_bps: float,
    event_anchor_age_bars: int,
    trigger_idx: int,
) -> list[int]:
    """Deterministically pick up to ``MAX_CONTROLS`` controls for one event."""
    if base.size == 0:
        return []
    offsets = replay.offset(base)
    control_abs_distance = np.abs(replay.close_to_avwap_bps[offsets])
    control_anchor_age = replay.anchor_age_bars[offsets]
    keys = [
        (
            abs(float(control_abs_distance[k]) - event_abs_distance_bps),
            abs(int(control_anchor_age[k]) - event_anchor_age_bars),
            abs(int(base[k]) - trigger_idx),
            int(base[k]),
        )
        for k in range(base.size)
    ]
    order = sorted(range(base.size), key=lambda k: keys[k])
    return [int(base[k]) for k in order[:MAX_CONTROLS]]


# --------------------------------------------------------------------------- #
# Per-cell processing
# --------------------------------------------------------------------------- #
def process_cell(
    instrument: str,
    domain: str,
    events_cell: pl.DataFrame,
    regimes_cell: pl.DataFrame,
    frame: pl.DataFrame,
) -> list[dict[str, Any]]:
    """Build EXP-025 matched line-rejection records for one cell."""
    if events_cell.is_empty():
        return []
    n = frame.height
    high = frame.get_column("High").to_numpy().astype(float)
    low = frame.get_column("Low").to_numpy().astype(float)
    close = frame.get_column("Close").to_numpy().astype(float)
    trigger_idx = events_cell.get_column("trigger_idx").to_numpy().astype(np.int64)
    is_trigger, near_trigger = build_exclusion_masks(n, trigger_idx)
    regime_rows = {int(row["regime_id"]): row for row in regimes_cell.iter_rows(named=True)}
    replay_cache: dict[int, RegimeReplay] = {}
    base_cache: dict[int, np.ndarray] = {}

    records: list[dict[str, Any]] = []
    for event in events_cell.sort(["regime_id", "trigger_idx"]).iter_rows(named=True):
        rid = int(event["regime_id"])
        if rid not in regime_rows:
            raise ValueError(f"{instrument}/{domain}: event regime_id={rid} absent from state summary")
        if rid not in replay_cache:
            replay_cache[rid] = replay_regime(frame, regime_rows[rid])
        replay = replay_cache[rid]
        if rid not in base_cache:
            base_cache[rid] = regime_candidate_base(replay, is_trigger, near_trigger, high, low, close)
        records.append(_event_record(instrument, domain, event, replay, base_cache[rid], high, low, close))
    return records


def _event_record(
    instrument: str,
    domain: str,
    event: dict[str, Any],
    replay: RegimeReplay,
    base: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
) -> dict[str, Any]:
    """Compute one event-level matched record and control aggregate."""
    direction = int(event["direction"])
    trigger_idx = int(event["trigger_idx"])
    offset = replay.offset(trigger_idx)
    rec: dict[str, Any] = {
        "instrument": instrument,
        "domain": domain,
        "regime_id": int(event["regime_id"]),
        "direction": direction,
        "bounce_index_in_regime": int(event["bounce_index_in_regime"]),
        "is_pyramid_bounce": _truthy(event["is_pyramid_bounce"]),
        "trigger_idx": trigger_idx,
        "trigger_time": event["trigger_time"],
        "anchor_idx": int(event["anchor_idx"]),
        "anchor_age_bars": int(event["anchor_age_bars"]),
        "event_close_to_avwap_bps": None,
        "event_abs_close_to_avwap_bps": None,
        "event_close_rebound_bps": None,
        "event_adverse_penetration_bps": None,
        "event_line_rejection_score_bps": None,
        "control_mean_abs_close_to_avwap_bps": None,
        "control_mean_anchor_age_bars": None,
        "control_mean_close_rebound_bps": None,
        "control_mean_adverse_penetration_bps": None,
        "control_mean_line_rejection_score_bps": None,
        "paired_diff_bps": None,
        "n_controls": 0,
        "control_indices": "",
        "control_scores_bps": "",
        "control_abs_close_to_avwap_bps": "",
        "control_anchor_ages": "",
        "reportable": False,
        "reason": "ok",
    }
    if offset < 0 or offset >= replay.avwap.size:
        rec["reason"] = "trigger_outside_regime_replay"
        return rec
    if not np.isclose(replay.avwap[offset], float(event["avwap_at_trigger"]), rtol=1e-9, atol=1e-9):
        raise ValueError(f"{instrument}/{domain}: AVWAP replay mismatch at trigger_idx={trigger_idx}")
    if "band_spread_at_trigger" in event and not np.isclose(
        replay.band_spread[offset],
        float(event["band_spread_at_trigger"]),
        rtol=1e-9,
        atol=1e-9,
    ):
        raise ValueError(f"{instrument}/{domain}: band replay mismatch at trigger_idx={trigger_idx}")
    if not replay.finite[offset]:
        rec["reason"] = "invalid_event_avwap"
        return rec

    ev_rebound, ev_adverse, ev_score = line_rejection_components(
        direction,
        high=np.asarray([high[trigger_idx]], dtype=float),
        low=np.asarray([low[trigger_idx]], dtype=float),
        close=np.asarray([close[trigger_idx]], dtype=float),
        avwap=np.asarray([replay.avwap[offset]], dtype=float),
    )
    if not (np.isfinite(ev_rebound[0]) and np.isfinite(ev_adverse[0]) and np.isfinite(ev_score[0])):
        rec["reason"] = "invalid_event_score"
        return rec

    event_abs_distance = float(abs(replay.close_to_avwap_bps[offset]))
    event_anchor_age = int(replay.anchor_age_bars[offset])
    rec.update(
        {
            "event_close_to_avwap_bps": float(replay.close_to_avwap_bps[offset]),
            "event_abs_close_to_avwap_bps": event_abs_distance,
            "event_close_rebound_bps": float(ev_rebound[0]),
            "event_adverse_penetration_bps": float(ev_adverse[0]),
            "event_line_rejection_score_bps": float(ev_score[0]),
        }
    )

    controls = select_controls(base, replay, event_abs_distance, event_anchor_age, trigger_idx)
    rec["n_controls"] = len(controls)
    if controls:
        idx = np.asarray(controls, dtype=np.int64)
        offsets = replay.offset(idx)
        c_rebound, c_adverse, c_score = line_rejection_components(
            direction,
            high=high[idx],
            low=low[idx],
            close=close[idx],
            avwap=replay.avwap[offsets],
        )
        if not (np.isfinite(c_rebound).all() and np.isfinite(c_adverse).all() and np.isfinite(c_score).all()):
            raise ValueError(f"{instrument}/{domain}: invalid control score after eligibility filtering")
        c_abs = np.abs(replay.close_to_avwap_bps[offsets])
        c_age = replay.anchor_age_bars[offsets]
        rec.update(
            {
                "control_indices": "|".join(str(c) for c in controls),
                "control_scores_bps": "|".join(f"{x:.12g}" for x in c_score),
                "control_abs_close_to_avwap_bps": "|".join(f"{x:.12g}" for x in c_abs),
                "control_anchor_ages": "|".join(str(int(x)) for x in c_age),
                "control_mean_abs_close_to_avwap_bps": float(np.mean(c_abs)),
                "control_mean_anchor_age_bars": float(np.mean(c_age)),
                "control_mean_close_rebound_bps": float(np.mean(c_rebound)),
                "control_mean_adverse_penetration_bps": float(np.mean(c_adverse)),
                "control_mean_line_rejection_score_bps": float(np.mean(c_score)),
                "paired_diff_bps": float(ev_score[0] - np.mean(c_score)),
            }
        )
    if len(controls) >= MIN_CONTROLS:
        rec["reportable"] = True
    else:
        rec["reason"] = "insufficient_line_proximate_controls"
    return rec


# --------------------------------------------------------------------------- #
# Reportability, inference, and decisions
# --------------------------------------------------------------------------- #
def reportable_cells(records: list[dict[str, Any]], instruments: list[str]) -> dict[str, list[str]]:
    """Map each domain to reportable instruments under EXP-025 denominators."""
    out: dict[str, list[str]] = {}
    for domain in DOMAINS:
        reportable: list[str] = []
        for inst in instruments:
            sub = [r for r in records if r["instrument"] == inst and r["domain"] == domain and r["reportable"]]
            bull = sum(r["direction"] == 1 for r in sub)
            bear = sum(r["direction"] == -1 for r in sub)
            if len(sub) >= MIN_REPORTABLE_EVENTS and bull >= MIN_DIRECTION_EVENTS and bear >= MIN_DIRECTION_EVENTS:
                reportable.append(inst)
        out[domain] = reportable
    return out


def domain_effect(diffs: np.ndarray, inst_labels: np.ndarray, instruments: list[str]) -> tuple[float, dict[str, float]]:
    """Equal-weight mean of per-instrument event-weighted paired differences."""
    per_inst: dict[str, float] = {}
    for inst in instruments:
        vals = diffs[inst_labels == inst]
        if vals.size:
            per_inst[inst] = float(vals.mean())
    effect = float(np.mean(list(per_inst.values()))) if per_inst else float("nan")
    return effect, per_inst


def arrays_for_domain(
    records: list[dict[str, Any]],
    domain: str,
    instruments: list[str],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Reportable paired diffs + instrument/regime labels for one domain."""
    diffs, inst_labels, regime_labels = [], [], []
    inst_set = set(instruments)
    for row in records:
        if row["domain"] == domain and row["reportable"] and row["instrument"] in inst_set:
            diffs.append(row["paired_diff_bps"])
            inst_labels.append(row["instrument"])
            regime_labels.append(row["regime_id"])
    return np.asarray(diffs, dtype=float), np.asarray(inst_labels), np.asarray(regime_labels, dtype=np.int64)


def build_strata(
    records: list[dict[str, Any]],
    domain: str,
    instruments: list[str],
) -> dict[tuple[str, int], tuple[np.ndarray, np.ndarray]]:
    """Per-(instrument, direction) regime-level sum/count of paired diffs."""
    grouped: dict[tuple[str, int], dict[int, list[float]]] = {}
    inst_set = set(instruments)
    for row in records:
        if not (row["domain"] == domain and row["reportable"] and row["instrument"] in inst_set):
            continue
        key = (row["instrument"], int(row["direction"]))
        grouped.setdefault(key, {}).setdefault(int(row["regime_id"]), []).append(float(row["paired_diff_bps"]))
    strata: dict[tuple[str, int], tuple[np.ndarray, np.ndarray]] = {}
    for key, regimes in grouped.items():
        sums = np.array([float(np.sum(vals)) for vals in regimes.values()])
        counts = np.array([float(len(vals)) for vals in regimes.values()])
        strata[key] = (sums, counts)
    return strata


def bootstrap_ci(
    strata: dict[tuple[str, int], tuple[np.ndarray, np.ndarray]],
    instruments: list[str],
    rng: np.random.Generator,
) -> tuple[float, float]:
    """Regime-cluster bootstrap CI of the instrument-averaged effect."""
    num = {inst: np.zeros(N_BOOT) for inst in instruments}
    den = {inst: np.zeros(N_BOOT) for inst in instruments}
    for (inst, _direction), (reg_sum, reg_cnt) in strata.items():
        r = reg_sum.size
        if r == 0:
            continue
        for start in range(0, N_BOOT, BOOT_CHUNK):
            size = min(BOOT_CHUNK, N_BOOT - start)
            idx = rng.integers(0, r, size=(size, r))
            num[inst][start : start + size] += reg_sum[idx].sum(axis=1)
            den[inst][start : start + size] += reg_cnt[idx].sum(axis=1)
    means = [np.divide(num[i], den[i], out=np.full(N_BOOT, np.nan), where=den[i] > 0) for i in instruments]
    boot = np.nanmean(np.vstack(means), axis=0)
    lo, hi = np.percentile(boot, CI_PERCENTILES)
    return float(lo), float(hi)


def permutation_p(
    diffs: np.ndarray,
    inst_index: np.ndarray,
    counts: np.ndarray,
    observed: float,
    rng: np.random.Generator,
) -> float:
    """One-sided stratified paired sign-permutation p-value for 0 advantage."""
    k = counts.size
    masks = [inst_index == j for j in range(k)]
    ge = 0
    for start in range(0, N_PERM, PERM_CHUNK):
        size = min(PERM_CHUNK, N_PERM - start)
        signs = rng.integers(0, 2, size=(size, diffs.size)).astype(np.int8) * 2 - 1
        signed = signs * diffs
        per_inst = np.empty((size, k))
        for j, mask in enumerate(masks):
            per_inst[:, j] = signed[:, mask].sum(axis=1) / counts[j]
        ge += int(np.sum(per_inst.mean(axis=1) >= observed))
    return (1 + ge) / (1 + N_PERM)


def holm_adjust(pvalues: dict[str, float]) -> dict[str, float]:
    """Holm step-down adjustment over domain primary p-values."""
    items = sorted(pvalues.items(), key=lambda kv: kv[1])
    adjusted: dict[str, float] = {}
    running = 0.0
    m = len(items)
    for rank, (domain, pvalue) in enumerate(items):
        running = max(running, min(1.0, (m - rank) * pvalue))
        adjusted[domain] = running
    return adjusted


def domain_balance(
    records: list[dict[str, Any]],
    reportable_map: dict[str, list[str]],
) -> dict[str, dict[str, Any]]:
    """Compute reportable-domain event/control proximity balance diagnostics."""
    out: dict[str, dict[str, Any]] = {}
    for domain in DOMAINS:
        inst_set = set(reportable_map.get(domain, []))
        sub = [r for r in records if r["domain"] == domain and r["instrument"] in inst_set and r["reportable"]]
        if not sub:
            out[domain] = {
                "median_event_abs_close_to_avwap_bps": None,
                "median_control_abs_close_to_avwap_bps": None,
                "median_abs_proximity_diff_bps": None,
                "balance_broken": None,
            }
            continue
        event_abs = np.asarray([r["event_abs_close_to_avwap_bps"] for r in sub], dtype=float)
        control_abs = np.asarray([r["control_mean_abs_close_to_avwap_bps"] for r in sub], dtype=float)
        diff = abs(float(np.median(event_abs)) - float(np.median(control_abs)))
        out[domain] = {
            "median_event_abs_close_to_avwap_bps": float(np.median(event_abs)),
            "median_control_abs_close_to_avwap_bps": float(np.median(control_abs)),
            "median_abs_proximity_diff_bps": diff,
            "balance_broken": diff > BALANCE_FAIL_THRESHOLD_BPS,
        }
    return out


def evaluate_domain(records: list[dict[str, Any]], domain: str, instruments: list[str]) -> dict[str, Any]:
    """Compute primary effect, CI, p-value, and per-instrument effects."""
    inst_sorted = sorted(instruments)
    diffs, inst_labels, _regimes = arrays_for_domain(records, domain, inst_sorted)
    if diffs.size == 0:
        return {
            "effect": float("nan"),
            "ci_low": float("nan"),
            "ci_high": float("nan"),
            "n_events": 0,
            "per_instrument": {},
            "raw_p": None,
        }
    effect, per_inst = domain_effect(diffs, inst_labels, inst_sorted)
    strata = build_strata(records, domain, inst_sorted)
    boot_rng = np.random.default_rng(seed_for(EXPERIMENT_ID, domain, "bootstrap"))
    ci_low, ci_high = bootstrap_ci(strata, inst_sorted, boot_rng)
    index_lut = {inst: idx for idx, inst in enumerate(inst_sorted)}
    inst_index = np.array([index_lut[i] for i in inst_labels])
    counts = np.array([int(np.sum(inst_index == j)) for j in range(len(inst_sorted))], dtype=float)
    perm_rng = np.random.default_rng(seed_for(EXPERIMENT_ID, domain, "permutation"))
    raw_p = permutation_p(diffs, inst_index, counts, effect, perm_rng)
    return {
        "effect": effect,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "n_events": int(diffs.size),
        "per_instrument": per_inst,
        "raw_p": raw_p,
    }


def decide_verdict(
    domain_stats: dict[str, dict[str, Any]],
    holm: dict[str, float],
    reportable_domains: list[str],
    balance: dict[str, dict[str, Any]],
) -> tuple[str, dict[str, str]]:
    """Apply scope Evidence FOR/AGAINST/Inconclusive rules."""
    labels: dict[str, str] = {}
    for domain in reportable_domains:
        stat = domain_stats[domain]
        for_flag = stat["effect"] > 0.0 and stat["ci_low"] > 0.0 and holm.get(domain, 1.0) <= ALPHA
        if for_flag:
            labels[domain] = "EVIDENCE_FOR"
        elif stat["ci_high"] <= 0.0:
            labels[domain] = "EVIDENCE_AGAINST"
        else:
            labels[domain] = "INCONCLUSIVE_SPANS_ZERO"

    if not reportable_domains:
        return "REFUTED", labels
    if any(label == "EVIDENCE_FOR" for label in labels.values()):
        return "SUPPORTED", labels
    balance_broken_all = all(bool(balance[d]["balance_broken"]) for d in reportable_domains)
    if balance_broken_all:
        return "INCONCLUSIVE_MATCHING_BALANCE", labels
    if all(labels[d] == "EVIDENCE_AGAINST" for d in reportable_domains):
        return "REFUTED", labels
    return "INCONCLUSIVE", labels


# --------------------------------------------------------------------------- #
# Result-table builders
# --------------------------------------------------------------------------- #
def line_rejection_summary_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Score-component summaries by instrument/domain/direction/role."""
    rows: list[dict[str, Any]] = []
    keys = sorted({(r["instrument"], r["domain"], r["direction"]) for r in records})
    for inst, domain, direction in keys:
        sub = [r for r in records if r["instrument"] == inst and r["domain"] == domain and r["direction"] == direction]
        reportable = [r for r in sub if r["reportable"]]
        for role in ("event", "control"):
            if not reportable:
                rows.append(
                    {
                        "instrument": inst,
                        "domain": domain,
                        "direction": direction,
                        "role": role,
                        "n_reportable_events": 0,
                        "mean_close_rebound_bps": None,
                        "mean_adverse_penetration_bps": None,
                        "mean_line_rejection_score_bps": None,
                        "n_pyramid_events": 0,
                    }
                )
                continue
            prefix = "event" if role == "event" else "control_mean"
            rows.append(
                {
                    "instrument": inst,
                    "domain": domain,
                    "direction": direction,
                    "role": role,
                    "n_reportable_events": len(reportable),
                    "mean_close_rebound_bps": float(np.mean([r[f"{prefix}_close_rebound_bps"] for r in reportable])),
                    "mean_adverse_penetration_bps": float(
                        np.mean([r[f"{prefix}_adverse_penetration_bps"] for r in reportable])
                    ),
                    "mean_line_rejection_score_bps": float(
                        np.mean([r[f"{prefix}_line_rejection_score_bps"] for r in reportable])
                    ),
                    "n_pyramid_events": int(sum(bool(r["is_pyramid_bounce"]) for r in reportable)),
                }
            )
    return rows


def control_diagnostic_rows(
    records: list[dict[str, Any]],
    balance: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Control-match diagnostics by cell/direction plus domain balance rows."""
    rows: list[dict[str, Any]] = []
    keys = sorted({(r["instrument"], r["domain"], r["direction"]) for r in records})
    for inst, domain, direction in keys:
        sub = [r for r in records if r["instrument"] == inst and r["domain"] == domain and r["direction"] == direction]
        reportable = [r for r in sub if r["reportable"]]
        event_abs = np.asarray([r["event_abs_close_to_avwap_bps"] for r in reportable], dtype=float)
        control_abs = np.asarray([r["control_mean_abs_close_to_avwap_bps"] for r in reportable], dtype=float)
        rows.append(
            {
                "level": "instrument_direction",
                "instrument": inst,
                "domain": domain,
                "direction": direction,
                "n_events_total": len(sub),
                "n_reportable_matched": len(reportable),
                "n_controls_reportable": int(sum(r["n_controls"] for r in reportable)),
                "n_invalid_event_avwap": sum(r["reason"] == "invalid_event_avwap" for r in sub),
                "n_invalid_event_score": sum(r["reason"] == "invalid_event_score" for r in sub),
                "n_insufficient_line_proximate_controls": sum(
                    r["reason"] == "insufficient_line_proximate_controls" for r in sub
                ),
                "mean_n_controls_reportable": float(np.mean([r["n_controls"] for r in reportable]))
                if reportable
                else None,
                "median_event_abs_close_to_avwap_bps": float(np.median(event_abs)) if event_abs.size else None,
                "median_control_abs_close_to_avwap_bps": float(np.median(control_abs)) if control_abs.size else None,
                "median_abs_proximity_diff_bps": float(abs(np.median(event_abs) - np.median(control_abs)))
                if event_abs.size
                else None,
                "balance_broken": bool(abs(np.median(event_abs) - np.median(control_abs)) > BALANCE_FAIL_THRESHOLD_BPS)
                if event_abs.size
                else None,
            }
        )

    for domain in DOMAINS:
        b = balance[domain]
        rows.append(
            {
                "level": "domain_reportable_instruments",
                "instrument": "",
                "domain": domain,
                "direction": 0,
                "n_events_total": None,
                "n_reportable_matched": None,
                "n_controls_reportable": None,
                "n_invalid_event_avwap": None,
                "n_invalid_event_score": None,
                "n_insufficient_line_proximate_controls": None,
                "mean_n_controls_reportable": None,
                "median_event_abs_close_to_avwap_bps": b["median_event_abs_close_to_avwap_bps"],
                "median_control_abs_close_to_avwap_bps": b["median_control_abs_close_to_avwap_bps"],
                "median_abs_proximity_diff_bps": b["median_abs_proximity_diff_bps"],
                "balance_broken": b["balance_broken"],
            }
        )
    return rows


def domain_test_rows(
    domain_stats: dict[str, dict[str, Any]],
    holm: dict[str, float],
    labels: dict[str, str],
    reportable_map: dict[str, list[str]],
    balance: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Flatten domain effects, CIs, p-values, decisions, and balance flags."""
    rows: list[dict[str, Any]] = []
    for domain in DOMAINS:
        reportable = reportable_map[domain]
        stat = domain_stats.get(domain)
        rows.append(
            {
                "domain": domain,
                "n_reportable_instruments": len(reportable),
                "reportable_instruments": ",".join(sorted(reportable)),
                "effect_bps": None if stat is None else stat["effect"],
                "ci_low_bps": None if stat is None else stat["ci_low"],
                "ci_high_bps": None if stat is None else stat["ci_high"],
                "n_events": None if stat is None else stat["n_events"],
                "raw_p": None if stat is None else stat["raw_p"],
                "holm_p": holm.get(domain),
                "decision": labels.get(domain),
                "median_abs_proximity_diff_bps": balance[domain]["median_abs_proximity_diff_bps"],
                "balance_broken": balance[domain]["balance_broken"],
            }
        )
    return rows


# --------------------------------------------------------------------------- #
# Plotting helpers (bounded records/summaries only)
# --------------------------------------------------------------------------- #
def plot_domain_forest(
    domain_stats: dict[str, dict[str, Any]],
    reportable_domains: list[str],
    labels: dict[str, str],
    save_path: Path,
) -> None:
    """Forest plot of domain line-rejection effects with 95% CIs."""
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ylabels: list[str] = []
    for y, domain in enumerate(reportable_domains):
        stat = domain_stats[domain]
        effect = stat["effect"]
        ax.errorbar(
            effect,
            y,
            xerr=[[effect - stat["ci_low"]], [stat["ci_high"] - effect]],
            fmt="o",
            capsize=3,
            color="#2f5597",
        )
        ylabels.append(f"{domain}  {labels.get(domain, '')}")
    if not reportable_domains:
        ax.text(0.5, 0.5, "No reportable domain", ha="center", va="center", transform=ax.transAxes)
    ax.axvline(0.0, ls="--", lw=0.8, color="grey")
    ax.set_yticks(range(len(ylabels)))
    ax.set_yticklabels(ylabels, fontsize=8)
    ax.set_xlabel("event - matched-control line-rejection score (bps)")
    ax.set_title("EXP-025 AVWAP line-rejection effect (95% regime-cluster bootstrap CI)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _finite(values: list[Any]) -> np.ndarray:
    """Return finite float array from nullable record values."""
    arr = np.asarray([v for v in values if v is not None], dtype=float)
    return arr[np.isfinite(arr)]


def plot_score_distributions(records: list[dict[str, Any]], reportable_domains: list[str], save_path: Path) -> None:
    """Event vs matched-control score distributions by domain."""
    panels = reportable_domains or list(DOMAINS)
    fig, axes = plt.subplots(1, len(panels), figsize=(4 * len(panels), 4), squeeze=False)
    for j, domain in enumerate(panels):
        sub = [r for r in records if r["domain"] == domain and r["reportable"]]
        ax = axes[0][j]
        event_scores = _finite([r["event_line_rejection_score_bps"] for r in sub])
        control_scores = _finite([r["control_mean_line_rejection_score_bps"] for r in sub])
        if event_scores.size and control_scores.size:
            rng = float(np.percentile(np.abs(np.concatenate([event_scores, control_scores])), 99)) or 1.0
            bins = np.linspace(-rng, rng, 60)
            ax.hist(event_scores, bins=bins, alpha=0.6, label="event", color="#bf4e30")
            ax.hist(control_scores, bins=bins, alpha=0.6, label="control mean", color="#2f5597")
            ax.axvline(0.0, ls="--", lw=0.8, color="grey")
            ax.legend(fontsize=8)
        else:
            ax.text(0.5, 0.5, "not reportable", ha="center", va="center", transform=ax.transAxes)
        ax.set_title(f"{domain} (n={len(sub)})")
        ax.set_xlabel("line-rejection score (bps)")
    fig.suptitle("EXP-025 event vs matched-control score distributions")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_matching_proximity(records: list[dict[str, Any]], reportable_domains: list[str], save_path: Path) -> None:
    """Event/control absolute close-to-AVWAP proximity diagnostics."""
    panels = reportable_domains or list(DOMAINS)
    fig, axes = plt.subplots(1, len(panels), figsize=(4 * len(panels), 4), squeeze=False)
    for j, domain in enumerate(panels):
        sub = [r for r in records if r["domain"] == domain and r["reportable"]]
        ax = axes[0][j]
        event_abs = _finite([r["event_abs_close_to_avwap_bps"] for r in sub])
        control_abs = _finite([r["control_mean_abs_close_to_avwap_bps"] for r in sub])
        if event_abs.size and control_abs.size:
            ax.boxplot([event_abs, control_abs], labels=["event", "control"], showfliers=False)
            ax.axhline(BALANCE_FAIL_THRESHOLD_BPS, ls="--", lw=0.8, color="grey")
        else:
            ax.text(0.5, 0.5, "not reportable", ha="center", va="center", transform=ax.transAxes)
        ax.set_title(domain)
        ax.set_ylabel("abs close-to-AVWAP distance (bps)")
    fig.suptitle("EXP-025 line-proximity balance")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_component_decomposition(records: list[dict[str, Any]], reportable_domains: list[str], save_path: Path) -> None:
    """Mean rebound and adverse-penetration components by role/domain."""
    domains = reportable_domains or list(DOMAINS)
    x = np.arange(len(domains))
    width = 0.2
    fig, ax = plt.subplots(figsize=(8, 4.5))
    series = [
        ("event rebound", "event_close_rebound_bps", "#bf4e30", -1.5 * width),
        ("event adverse", "event_adverse_penetration_bps", "#d98f45", -0.5 * width),
        ("control rebound", "control_mean_close_rebound_bps", "#2f5597", 0.5 * width),
        ("control adverse", "control_mean_adverse_penetration_bps", "#86a3c3", 1.5 * width),
    ]
    for label, column, color, offset in series:
        vals = []
        for domain in domains:
            arr = _finite([r[column] for r in records if r["domain"] == domain and r["reportable"]])
            vals.append(float(np.mean(arr)) if arr.size else np.nan)
        ax.bar(x + offset, vals, width, label=label, color=color)
    ax.axhline(0.0, ls="--", lw=0.8, color="grey")
    ax.set_xticks(x)
    ax.set_xticklabels(domains)
    ax.set_ylabel("bps")
    ax.set_title("EXP-025 score component decomposition")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def run() -> None:
    """Execute EXP-025 end to end and write all result artifacts."""
    ensure_output_dirs()
    dep_meta = load_dependency_metadata()
    gate_ok, reasons = check_exp020_gate(dep_meta)
    artifacts_ok, artifact_reasons = check_exp020_artifacts()
    exp024_ok, exp024_reasons = check_exp024_documented()
    reasons.extend(artifact_reasons)
    reasons.extend(exp024_reasons)
    if not gate_ok or not artifacts_ok or not exp024_ok:
        write_dependency_blocked_metadata(reasons, dep_meta)
        return
    LOGGER.info("Dependency gate PASSED (EXP-020 %s; EXP-024 documented).", dep_meta.get("overall_status"))

    events, regimes, metadata = load_exp020_tables()
    cell_frames, analysis_end, reconstruction_rows = build_scoped_cell_frames(metadata)
    instruments = sorted({inst for inst, _domain in cell_frames} & set(events.get_column("instrument").unique().to_list()))

    records: list[dict[str, Any]] = []
    for inst in tqdm(instruments, desc="cells: replay + match"):
        for domain in DOMAINS:
            frame = cell_frames[(inst, domain)]
            ev_cell = events.filter((pl.col("instrument") == inst) & (pl.col("domain") == domain))
            rg_cell = regimes.filter((pl.col("instrument") == inst) & (pl.col("domain") == domain))
            validate_event_join(ev_cell, frame, f"{inst}/{domain}")
            records.extend(process_cell(inst, domain, ev_cell, rg_cell, frame))

    reportable_map = reportable_cells(records, instruments)
    reportable_domains = [d for d in DOMAINS if len(reportable_map[d]) >= DOMAIN_MIN_INSTRUMENTS]
    balance = domain_balance(records, reportable_map)

    domain_stats: dict[str, dict[str, Any]] = {}
    primary_pvals: dict[str, float] = {}
    for domain in tqdm(reportable_domains, desc="domain inference"):
        domain_stats[domain] = evaluate_domain(records, domain, reportable_map[domain])
        primary_pvals[domain] = domain_stats[domain]["raw_p"]
    holm = holm_adjust(primary_pvals) if primary_pvals else {}
    verdict, labels = decide_verdict(domain_stats, holm, reportable_domains, balance)

    _write_outputs(
        records=records,
        reconstruction_rows=reconstruction_rows,
        domain_stats=domain_stats,
        holm=holm,
        labels=labels,
        reportable_map=reportable_map,
        reportable_domains=reportable_domains,
        balance=balance,
        instruments=instruments,
        verdict=verdict,
        dep_meta=dep_meta,
        analysis_end=analysis_end,
    )
    LOGGER.info("EXP-025 verdict: %s | reportable domains: %s", verdict, reportable_domains or "none")


def _write_outputs(
    *,
    records: list[dict[str, Any]],
    reconstruction_rows: list[dict[str, Any]],
    domain_stats: dict[str, dict[str, Any]],
    holm: dict[str, float],
    labels: dict[str, str],
    reportable_map: dict[str, list[str]],
    reportable_domains: list[str],
    balance: dict[str, dict[str, Any]],
    instruments: list[str],
    verdict: str,
    dep_meta: dict[str, Any],
    analysis_end: dict[str, str],
) -> None:
    """Write every EXP-025 result table, plot, and metadata artifact."""
    observation_cols = [
        "instrument",
        "domain",
        "regime_id",
        "direction",
        "bounce_index_in_regime",
        "is_pyramid_bounce",
        "trigger_idx",
        "trigger_time",
        "anchor_idx",
        "anchor_age_bars",
        "event_close_to_avwap_bps",
        "event_abs_close_to_avwap_bps",
        "event_close_rebound_bps",
        "event_adverse_penetration_bps",
        "event_line_rejection_score_bps",
        "control_mean_abs_close_to_avwap_bps",
        "control_mean_anchor_age_bars",
        "control_mean_close_rebound_bps",
        "control_mean_adverse_penetration_bps",
        "control_mean_line_rejection_score_bps",
        "paired_diff_bps",
        "n_controls",
        "control_indices",
        "control_scores_bps",
        "control_abs_close_to_avwap_bps",
        "control_anchor_ages",
        "reportable",
        "reason",
    ]
    pl.DataFrame(records).select(observation_cols).write_csv(RESULTS_DIR / "line_rejection_observations.csv")
    write_rows(RESULTS_DIR / "line_rejection_summary.csv", line_rejection_summary_rows(records))
    write_rows(RESULTS_DIR / "domain_reconstruction_check.csv", reconstruction_rows)
    write_rows(
        RESULTS_DIR / "domain_line_rejection_tests.csv",
        domain_test_rows(domain_stats, holm, labels, reportable_map, balance),
    )
    write_rows(RESULTS_DIR / "control_match_diagnostics.csv", control_diagnostic_rows(records, balance))

    plot_domain_forest(domain_stats, reportable_domains, labels, PLOTS_DIR / "domain_effect_forest.png")
    plot_score_distributions(records, reportable_domains, PLOTS_DIR / "event_control_score_distributions.png")
    plot_matching_proximity(records, reportable_domains, PLOTS_DIR / "matching_proximity_diagnostics.png")
    plot_component_decomposition(records, reportable_domains, PLOTS_DIR / "score_component_decomposition.png")

    write_json(
        RESULTS_DIR / "run_metadata.json",
        {
            "experiment_id": EXPERIMENT_ID,
            "title": "AVWAP Line Support/Resistance Direct Test",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "overall_status": verdict,
            "dependency_gate": {
                "passed": True,
                "exp020_status": dep_meta.get("overall_status"),
                "exp024_documented": True,
            },
            "instruments": instruments,
            "domains": list(DOMAINS),
            "reportable_instruments_by_domain": reportable_map,
            "reportable_domains": reportable_domains,
            "domain_decisions": labels,
            "holm_adjusted_primary_p": holm,
            "domain_primary_effects": {d: domain_stats[d]["effect"] for d in reportable_domains},
            "domain_balance": balance,
            "analysis_end_by_instrument": analysis_end,
            "parameters": {
                "line_rejection_horizon": "event_bar_h0",
                "max_controls": MAX_CONTROLS,
                "min_controls": MIN_CONTROLS,
                "exclusion_bars": EXCLUSION_BARS,
                "line_proximity_floor_bps": LINE_PROXIMITY_FLOOR_BPS,
                "balance_fail_threshold_bps": BALANCE_FAIL_THRESHOLD_BPS,
                "domain_estimator": "equal_weight_instrument_mean_of_event_weighted_cell_means",
                "min_reportable_events": MIN_REPORTABLE_EVENTS,
                "min_direction_events": MIN_DIRECTION_EVENTS,
                "domain_min_instruments": DOMAIN_MIN_INSTRUMENTS,
                "n_bootstrap": N_BOOT,
                "n_permutation": N_PERM,
                "alpha": ALPHA,
                "ci_percentiles": list(CI_PERCENTILES),
                "domain_specs": {
                    label: {
                        "period_minutes": spec.period_minutes,
                        "min_coverage": spec.min_coverage,
                    }
                    for label, spec in DOMAIN_SPECS.items()
                    if label in DOMAINS
                },
            },
            "registry": REGISTRY_REFS,
        },
    )


def main() -> None:
    """Configure logging and run the experiment (manual execution entry point)."""
    configure_logging()
    run()


if __name__ == "__main__":
    main()
