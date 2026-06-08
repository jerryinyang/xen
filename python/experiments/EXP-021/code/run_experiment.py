"""Experiment EXP-021: AVWAP Bounce Reaction Study (CF-AVWAP-001 / HYP-002).

Implements the approved analysis plan (analysis-plan.md). EXP-021 tests whether
EXP-020 AVWAP bounce events show better fixed-horizon, direction-signed real-price
reaction than matched non-event controls drawn from the *same regime*. The
primary confirmatory read is the matched event-control return advantage at 3
completed domain bars; horizons 1 and 6 are predeclared stability diagnostics.

Pipeline:
    1. Dependency gate on the EXP-020 substrate (SUPPORTED_FULL, ready 5m/1h/4h,
       0 invariant failures, deterministic replay). Load avwap_events.csv and
       avwap_state_summary.csv only after the gate passes.
    2. Holdout-safe domain reconstruction (first-70% slice, reused EXP-004/020
       domain convention) and a hard-fail event->domain-bar join.
    3. Same-regime matched non-event control construction (Item 2 predeclaration).
    4. Direction-signed log-bps reaction metrics and event-level paired diffs.
    5. Instrument-averaged domain primary test (Item 1 predeclaration): equal
       weight per reportable instrument; regime-cluster bootstrap CI and a
       stratified paired sign-permutation p-value with Holm across domains.
    6. Secondary-horizon diagnostics and four bounded visualisations.

The final 30% global holdout is never loaded: ``load_analysis_data`` slices the
first 70% in a lazy plan before collection, and every event is re-fenced to the
analysis-set end via the domain-bar join.

Run:
    cd <project-root> && python python/experiments/EXP-021/code/run_experiment.py
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
    DOMAIN_SPECS,
    build_domain_frames,
    list_timebar_files,
    load_analysis_data,
    seed_for,
)


LOGGER = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-021"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = PROJECT_ROOT / "data"
EXPERIMENT_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
DEP_RESULTS_DIR = PROJECT_ROOT / "python" / "experiments" / "EXP-020" / "results"

DOMAINS: tuple[str, ...] = ("5m", "1h", "4h")
HORIZONS: tuple[int, ...] = (1, 3, 6)
PRIMARY_HORIZON = 3

# Control construction (scope Fixed Control Definition, Item 2 predeclaration).
MAX_CONTROLS = 5
MIN_CONTROLS = 3
EXCLUSION_BARS = 6

# Reportability thresholds (scope Success / Failure Criteria).
MIN_REPORTABLE_EVENTS = 30
MIN_DIRECTION_EVENTS = 8
DOMAIN_MIN_INSTRUMENTS = 3

# Inference (methods catalog: >= 10,000 resamples; non-parametric).
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

TIME_COLUMNS = ("anchor_time", "armed_time", "trigger_time")

REGISTRY_REFS = {
    "candidate_family": "CF-AVWAP-001",
    "hypothesis": "HYP-002",
    "family_spec": "docs/signal-registry/candidate-families/avwap.md",
    "checkpoint": "docs/experiments-docs/checkpoints/2026-06-07-004-avwap-signal-exploration",
}


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
    return cast_time_columns(events, TIME_COLUMNS), cast_time_columns(regimes, ("confirm_time", "anchor_time"))


# --------------------------------------------------------------------------- #
# Domain reconstruction + holdout-safe join guard
# --------------------------------------------------------------------------- #
def build_cell_frames() -> tuple[dict[tuple[str, str], pl.DataFrame], dict[str, str]]:
    """Rebuild first-70% 5m/1h/4h domain bars per instrument (EXP-020 convention)."""
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
    """Hard-fail if any event's (trigger_idx) row disagrees with the domain bar.

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


# --------------------------------------------------------------------------- #
# Same-regime control construction (pure, deterministic)
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
    horizon: int,
    n: int,
) -> list[int]:
    """Deterministically pick up to ``MAX_CONTROLS`` same-regime controls.

    Eligibility additionally requires enough future bars for ``horizon``. Ranking
    is by nearest anchor age, then nearest timestamp (index proxy within a cell),
    then row index as a stable final tiebreak.
    """
    if base.size == 0:
        return []
    eligible = base[base + horizon <= n - 1]
    if eligible.size == 0:
        return []
    keys = [
        (abs((int(c) - anchor_idx) - event_anchor_age), abs(int(c) - trigger_idx), int(c))
        for c in eligible
    ]
    order = sorted(range(eligible.size), key=lambda k: keys[k])
    return [int(eligible[k]) for k in order[:MAX_CONTROLS]]


def signed_log_bps(log_close: np.ndarray, start: np.ndarray, horizon: int, direction: int) -> np.ndarray:
    """Direction-signed log return in bps over ``horizon`` completed bars."""
    return 10_000.0 * direction * (log_close[start + horizon] - log_close[start])


# --------------------------------------------------------------------------- #
# Per-cell processing: matched records + control diagnostics
# --------------------------------------------------------------------------- #
def process_cell(
    instrument: str,
    domain: str,
    events_cell: pl.DataFrame,
    regimes_cell: pl.DataFrame,
    frame: pl.DataFrame,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build per-(event, horizon) matched records and per-cell control diagnostics."""
    n = frame.height
    log_close = np.log(frame.get_column("Close").to_numpy().astype(float))
    trig = events_cell.get_column("trigger_idx").to_numpy().astype(np.int64)
    is_trigger, near_trigger = build_exclusion_masks(n, trig)
    regime_lut = {
        int(r["regime_id"]): (int(r["regime_start_idx"]), int(r["regime_end_idx"]), int(r["anchor_idx"]))
        for r in regimes_cell.iter_rows(named=True)
    }
    base_cache: dict[int, np.ndarray] = {}

    records: list[dict[str, Any]] = []
    for ev in events_cell.iter_rows(named=True):
        rid = int(ev["regime_id"])
        if rid not in regime_lut:
            raise ValueError(f"{instrument}/{domain}: event regime_id={rid} absent from state summary.")
        confirm_idx, end_idx, anchor_idx = regime_lut[rid]
        if rid not in base_cache:
            base_cache[rid] = regime_candidate_base(confirm_idx, end_idx, is_trigger, near_trigger)
        base = base_cache[rid]
        direction = int(ev["direction"])
        t = int(ev["trigger_idx"])
        event_anchor_age = int(ev["anchor_age_bars"])
        for h in HORIZONS:
            records.append(
                _matched_record(instrument, domain, rid, direction, t, event_anchor_age, h, n, base, anchor_idx, log_close)
            )
    return records, _diagnostic_rows(instrument, domain, records)


def _matched_record(
    instrument: str,
    domain: str,
    regime_id: int,
    direction: int,
    trigger_idx: int,
    event_anchor_age: int,
    horizon: int,
    n: int,
    base: np.ndarray,
    anchor_idx: int,
    log_close: np.ndarray,
) -> dict[str, Any]:
    """Compute one event/horizon matched record with its control aggregate."""
    rec: dict[str, Any] = {
        "instrument": instrument, "domain": domain, "regime_id": regime_id,
        "direction": direction, "trigger_idx": trigger_idx, "horizon": horizon,
        "event_return_bps": None, "control_mean_bps": None, "paired_diff_bps": None,
        "n_controls": 0, "control_indices": "", "control_returns_bps": "",
        "reportable": False, "reason": "ok",
    }
    if trigger_idx + horizon > n - 1:
        rec["reason"] = "insufficient_future_bars"
        return rec
    rec["event_return_bps"] = float(signed_log_bps(log_close, np.array([trigger_idx]), horizon, direction)[0])
    controls = select_controls(base, anchor_idx, event_anchor_age, trigger_idx, horizon, n)
    rec["n_controls"] = len(controls)
    if controls:
        c_arr = np.asarray(controls, dtype=np.int64)
        control_returns = signed_log_bps(log_close, c_arr, horizon, direction)
        rec["control_indices"] = "|".join(str(c) for c in controls)
        rec["control_returns_bps"] = "|".join(f"{x:.12g}" for x in control_returns)
        rec["control_mean_bps"] = float(np.mean(control_returns))
        rec["paired_diff_bps"] = rec["event_return_bps"] - rec["control_mean_bps"]
    if len(controls) >= MIN_CONTROLS:
        rec["reportable"] = True
    else:
        rec["reason"] = "insufficient_same_regime_controls"
    return rec


def _diagnostic_rows(instrument: str, domain: str, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate control-match diagnostics by (direction, horizon) for one cell."""
    rows: list[dict[str, Any]] = []
    for direction in (1, -1):
        for h in HORIZONS:
            sub = [r for r in records if r["direction"] == direction and r["horizon"] == h]
            valid_future = [r for r in sub if r["reason"] != "insufficient_future_bars"]
            reportable = [r for r in sub if r["reportable"]]
            total_controls_valid = int(sum(r["n_controls"] for r in valid_future))
            total_controls_reportable = int(sum(r["n_controls"] for r in reportable))
            mean_nc = float(np.mean([r["n_controls"] for r in reportable])) if reportable else None
            rows.append({
                "instrument": instrument, "domain": domain, "direction": direction, "horizon": h,
                "n_events_total": len(sub),
                "n_events_valid_future_close": len(valid_future),
                "n_reportable_matched": len(reportable),
                "n_controls_valid_future": total_controls_valid,
                "n_controls_reportable": total_controls_reportable,
                "n_insufficient_future_bars": sum(r["reason"] == "insufficient_future_bars" for r in sub),
                "n_insufficient_same_regime_controls": sum(
                    r["reason"] == "insufficient_same_regime_controls" for r in sub
                ),
                "mean_n_controls_reportable": mean_nc,
            })
    return rows


# --------------------------------------------------------------------------- #
# Reportability + instrument-averaged effect estimator
# --------------------------------------------------------------------------- #
def reportable_cells(records: list[dict[str, Any]], instruments: list[str]) -> dict[str, list[str]]:
    """Map each domain to the list of reaction-reportable instruments (primary horizon)."""
    out: dict[str, list[str]] = {}
    for domain in DOMAINS:
        reportable: list[str] = []
        for inst in instruments:
            sub = [
                r for r in records
                if r["instrument"] == inst and r["domain"] == domain
                and r["horizon"] == PRIMARY_HORIZON and r["reportable"]
            ]
            bull = sum(r["direction"] == 1 for r in sub)
            bear = sum(r["direction"] == -1 for r in sub)
            if len(sub) >= MIN_REPORTABLE_EVENTS and bull >= MIN_DIRECTION_EVENTS and bear >= MIN_DIRECTION_EVENTS:
                reportable.append(inst)
        out[domain] = reportable
    return out


def domain_effect(diffs: np.ndarray, inst_labels: np.ndarray, instruments: list[str]) -> tuple[float, dict[str, float]]:
    """Instrument-averaged effect: equal-weight mean of per-instrument event means."""
    per_inst: dict[str, float] = {}
    for inst in instruments:
        vals = diffs[inst_labels == inst]
        if vals.size:
            per_inst[inst] = float(vals.mean())
    effect = float(np.mean(list(per_inst.values()))) if per_inst else float("nan")
    return effect, per_inst


def bootstrap_ci(
    strata: dict[tuple[str, int], tuple[np.ndarray, np.ndarray]],
    instruments: list[str],
    rng: np.random.Generator,
) -> tuple[float, float]:
    """Regime-cluster bootstrap CI of the instrument-averaged effect.

    Resamples ``regime_id`` clusters with replacement within each
    (instrument, direction) stratum, recomputes each instrument's event-weighted
    mean, then averages across instruments. Clusters are exact (same-regime
    controls), so cross-cluster independence holds by construction.
    """
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
    """One-sided stratified paired sign-permutation p-value for the null of 0 advantage."""
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
# Domain test assembly (effects, inference, decisions)
# --------------------------------------------------------------------------- #
def horizon_arrays(
    records: list[dict[str, Any]], domain: str, horizon: int, instruments: list[str]
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Reportable paired diffs + instrument/regime labels for one domain/horizon."""
    diffs, inst_labels, regime_labels = [], [], []
    inst_set = set(instruments)
    for r in records:
        if r["domain"] == domain and r["horizon"] == horizon and r["reportable"] and r["instrument"] in inst_set:
            diffs.append(r["paired_diff_bps"])
            inst_labels.append(r["instrument"])
            regime_labels.append(r["regime_id"])
    return np.asarray(diffs, dtype=float), np.asarray(inst_labels), np.asarray(regime_labels, dtype=np.int64)


def build_strata(
    records: list[dict[str, Any]], domain: str, horizon: int, instruments: list[str]
) -> dict[tuple[str, int], tuple[np.ndarray, np.ndarray]]:
    """Per-(instrument, direction) regime-level (sum, count) of reportable paired diffs."""
    grouped: dict[tuple[str, int], dict[int, list[float]]] = {}
    inst_set = set(instruments)
    for r in records:
        if not (r["domain"] == domain and r["horizon"] == horizon and r["reportable"] and r["instrument"] in inst_set):
            continue
        key = (r["instrument"], r["direction"])
        grouped.setdefault(key, {}).setdefault(r["regime_id"], []).append(r["paired_diff_bps"])
    strata: dict[tuple[str, int], tuple[np.ndarray, np.ndarray]] = {}
    for key, regimes in grouped.items():
        sums = np.array([float(np.sum(v)) for v in regimes.values()])
        cnts = np.array([float(len(v)) for v in regimes.values()])
        strata[key] = (sums, cnts)
    return strata


def evaluate_domain(
    records: list[dict[str, Any]], domain: str, instruments: list[str]
) -> dict[int, dict[str, Any]]:
    """Compute effect + bootstrap CI for every horizon, and the permutation stat."""
    out: dict[int, dict[str, Any]] = {}
    inst_sorted = sorted(instruments)
    index_lut = {inst: j for j, inst in enumerate(inst_sorted)}
    for horizon in HORIZONS:
        diffs, inst_labels, _regimes = horizon_arrays(records, domain, horizon, inst_sorted)
        if diffs.size == 0:
            out[horizon] = {"effect": float("nan"), "ci_low": float("nan"), "ci_high": float("nan"),
                            "n_events": 0, "per_instrument": {}, "raw_p": None}
            continue
        effect, per_inst = domain_effect(diffs, inst_labels, inst_sorted)
        strata = build_strata(records, domain, horizon, inst_sorted)
        boot_rng = np.random.default_rng(seed_for(EXPERIMENT_ID, domain, horizon, "bootstrap"))
        ci_low, ci_high = bootstrap_ci(strata, inst_sorted, boot_rng)
        raw_p = None
        if horizon == PRIMARY_HORIZON:
            inst_index = np.array([index_lut[i] for i in inst_labels])
            counts = np.array([int(np.sum(inst_index == j)) for j in range(len(inst_sorted))], dtype=float)
            perm_rng = np.random.default_rng(seed_for(EXPERIMENT_ID, domain, horizon, "permutation"))
            raw_p = permutation_p(diffs, inst_index, counts, effect, perm_rng)
        out[horizon] = {"effect": effect, "ci_low": ci_low, "ci_high": ci_high,
                        "n_events": int(diffs.size), "per_instrument": per_inst, "raw_p": raw_p}
    return out


def decide_verdict(
    domain_stats: dict[str, dict[int, dict[str, Any]]],
    holm: dict[str, float],
    reportable_domains: list[str],
) -> tuple[str, dict[str, str]]:
    """Apply scope Evidence FOR/AGAINST/Inconclusive rules per domain and overall."""
    labels: dict[str, str] = {}
    for domain in reportable_domains:
        prim = domain_stats[domain][PRIMARY_HORIZON]
        for_flag = prim["effect"] > 0 and prim["ci_low"] > 0 and holm.get(domain, 1.0) <= ALPHA
        sec_neg = all(domain_stats[domain][h]["effect"] < 0 for h in (1, 6))
        if for_flag and not sec_neg:
            labels[domain] = "EVIDENCE_FOR"
        elif for_flag and sec_neg:
            labels[domain] = "INCONCLUSIVE_SECONDARY_UNSTABLE"
        elif prim["ci_high"] <= 0:
            labels[domain] = "EVIDENCE_AGAINST"
        else:
            labels[domain] = "INCONCLUSIVE_SPANS_ZERO"
    if not reportable_domains:
        return "EVIDENCE_AGAINST", labels
    if any(v == "EVIDENCE_FOR" for v in labels.values()):
        return "SUPPORTED", labels
    if all(labels[d] == "EVIDENCE_AGAINST" for d in reportable_domains):
        return "REFUTED", labels
    return "INCONCLUSIVE", labels


# --------------------------------------------------------------------------- #
# Result-table builders
# --------------------------------------------------------------------------- #
def reaction_summary_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Event/control return summary by instrument, domain, direction, horizon."""
    rows: list[dict[str, Any]] = []
    keys = sorted({(r["instrument"], r["domain"], r["direction"], r["horizon"]) for r in records})
    for inst, domain, direction, h in keys:
        sub = [r for r in records if r["instrument"] == inst and r["domain"] == domain
               and r["direction"] == direction and r["horizon"] == h and r["reportable"]]
        if not sub:
            rows.append({"instrument": inst, "domain": domain, "direction": direction, "horizon": h,
                         "n_reportable_events": 0, "mean_event_bps": None,
                         "mean_control_bps": None, "mean_paired_diff_bps": None})
            continue
        rows.append({
            "instrument": inst, "domain": domain, "direction": direction, "horizon": h,
            "n_reportable_events": len(sub),
            "mean_event_bps": float(np.mean([r["event_return_bps"] for r in sub])),
            "mean_control_bps": float(np.mean([r["control_mean_bps"] for r in sub])),
            "mean_paired_diff_bps": float(np.mean([r["paired_diff_bps"] for r in sub])),
        })
    return rows


def domain_test_rows(
    domain_stats: dict[str, dict[int, dict[str, Any]]],
    holm: dict[str, float],
    labels: dict[str, str],
    reportable_map: dict[str, list[str]],
) -> list[dict[str, Any]]:
    """Flatten per-domain/horizon effects, CIs, p-values, and primary decisions."""
    rows: list[dict[str, Any]] = []
    for domain in DOMAINS:
        reportable = reportable_map[domain]
        for h in HORIZONS:
            stat = domain_stats.get(domain, {}).get(h)
            is_primary = h == PRIMARY_HORIZON
            rows.append({
                "domain": domain, "horizon": h, "is_primary": is_primary,
                "n_reportable_instruments": len(reportable),
                "reportable_instruments": ",".join(sorted(reportable)),
                "effect_bps": None if stat is None else stat["effect"],
                "ci_low_bps": None if stat is None else stat["ci_low"],
                "ci_high_bps": None if stat is None else stat["ci_high"],
                "n_events": None if stat is None else stat["n_events"],
                "raw_p": (stat["raw_p"] if stat and is_primary else None),
                "holm_p": (holm.get(domain) if is_primary else None),
                "decision": (labels.get(domain) if is_primary else None),
            })
    return rows


# --------------------------------------------------------------------------- #
# Plotting helpers (bounded inputs only)
# --------------------------------------------------------------------------- #
def plot_domain_forest(domain_stats: dict[str, dict[int, dict[str, Any]]],
                       reportable_domains: list[str], save_path: Path) -> None:
    """Forest plot of event-control advantage at horizons 1/3/6 (3-bar highlighted)."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ypos, ylabels = [], []
    y = 0
    for domain in reportable_domains:
        for h in HORIZONS:
            stat = domain_stats[domain][h]
            color = "#d62728" if h == PRIMARY_HORIZON else "#1f77b4"
            ax.errorbar(stat["effect"], y,
                        xerr=[[stat["effect"] - stat["ci_low"]], [stat["ci_high"] - stat["effect"]]],
                        fmt="o", color=color, capsize=3)
            ypos.append(y)
            ylabels.append(f"{domain} h={h}{' (primary)' if h == PRIMARY_HORIZON else ''}")
            y += 1
        y += 1
    ax.axvline(0.0, ls="--", lw=0.8, color="grey")
    ax.set_yticks(ypos)
    ax.set_yticklabels(ylabels, fontsize=8)
    ax.set_xlabel("event - control advantage (bps)")
    ax.set_title("EXP-021 domain reaction advantage (95% regime-cluster bootstrap CI)")
    if not reportable_domains:
        ax.text(0.5, 0.5, "No reaction-reportable domain", ha="center", va="center", transform=ax.transAxes)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_event_control_distributions(records: list[dict[str, Any]],
                                     reportable_domains: list[str], save_path: Path) -> None:
    """Event vs matched-control return distributions at the primary horizon, by domain."""
    panels = reportable_domains or list(DOMAINS)
    fig, axes = plt.subplots(1, len(panels), figsize=(4 * len(panels), 4), squeeze=False)
    for j, domain in enumerate(panels):
        sub = [r for r in records if r["domain"] == domain and r["horizon"] == PRIMARY_HORIZON and r["reportable"]]
        ax = axes[0][j]
        if sub:
            ev = np.array([r["event_return_bps"] for r in sub])
            ct = np.array([r["control_mean_bps"] for r in sub])
            rng = float(np.percentile(np.abs(np.concatenate([ev, ct])), 99)) or 1.0
            bins = np.linspace(-rng, rng, 60)
            ax.hist(ev, bins=bins, alpha=0.6, label="event", color="#d62728")
            ax.hist(ct, bins=bins, alpha=0.6, label="control mean", color="#1f77b4")
            ax.axvline(0.0, ls="--", lw=0.8, color="grey")
            ax.legend(fontsize=8)
        else:
            ax.text(0.5, 0.5, "not reportable", ha="center", va="center", transform=ax.transAxes)
        ax.set_title(f"{domain} (n={len(sub)})")
        ax.set_xlabel("direction-signed bps")
    fig.suptitle(f"EXP-021 event vs control returns at h={PRIMARY_HORIZON}")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_instrument_direction_heatmap(records: list[dict[str, Any]], instruments: list[str],
                                      save_path: Path) -> None:
    """Heatmap of per-instrument/direction primary paired advantage across domains."""
    cols = [(d, dir_) for d in DOMAINS for dir_ in (1, -1)]
    mat = np.full((len(instruments), len(cols)), np.nan)
    for i, inst in enumerate(instruments):
        for jc, (domain, direction) in enumerate(cols):
            sub = [r for r in records if r["instrument"] == inst and r["domain"] == domain
                   and r["direction"] == direction and r["horizon"] == PRIMARY_HORIZON and r["reportable"]]
            if sub:
                mat[i, jc] = float(np.mean([r["paired_diff_bps"] for r in sub]))
    vmax = np.nanmax(np.abs(mat)) if np.isfinite(mat).any() else 1.0
    fig, ax = plt.subplots(figsize=(8, 4.5))
    im = ax.imshow(mat, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels([f"{d}\n{'bull' if s == 1 else 'bear'}" for d, s in cols], fontsize=8)
    ax.set_yticks(range(len(instruments)))
    ax.set_yticklabels(instruments)
    for i in range(len(instruments)):
        for jc in range(len(cols)):
            if np.isfinite(mat[i, jc]):
                ax.text(jc, i, f"{mat[i, jc]:.1f}", ha="center", va="center", fontsize=7)
    fig.colorbar(im, ax=ax, label="paired advantage (bps)")
    ax.set_title(f"EXP-021 instrument x direction paired advantage (h={PRIMARY_HORIZON})")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_control_match_diagnostics(diag_rows: list[dict[str, Any]], instruments: list[str],
                                   save_path: Path) -> None:
    """Reportable-event and non-reportable counts by instrument/domain at primary horizon."""
    fig, axes = plt.subplots(1, len(DOMAINS), figsize=(4 * len(DOMAINS), 4), squeeze=False)
    x = np.arange(len(instruments))
    width = 0.38
    for j, domain in enumerate(DOMAINS):
        rep, insuff = [], []
        for inst in instruments:
            sub = [d for d in diag_rows if d["instrument"] == inst and d["domain"] == domain
                   and d["horizon"] == PRIMARY_HORIZON]
            rep.append(sum(d["n_reportable_matched"] for d in sub))
            insuff.append(sum(d["n_insufficient_same_regime_controls"] for d in sub))
        ax = axes[0][j]
        ax.bar(x - width / 2, rep, width, label="reportable", color="#2ca02c")
        ax.bar(x + width / 2, insuff, width, label="insuff. controls", color="#ff7f0e")
        ax.axhline(MIN_REPORTABLE_EVENTS, ls="--", lw=0.8, color="grey")
        ax.set_xticks(x)
        ax.set_xticklabels(instruments, rotation=45, ha="right", fontsize=8)
        ax.set_title(domain)
        if j == 0:
            ax.legend(fontsize=8)
            ax.set_ylabel("events")
    fig.suptitle(f"EXP-021 control-match diagnostics (h={PRIMARY_HORIZON}, dashed = {MIN_REPORTABLE_EVENTS})")
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
        "title": "AVWAP Bounce Reaction Study",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": "EVIDENCE_AGAINST",
        "dependency_gate": {"passed": False, "reasons": reasons,
                            "exp020_status": dep_meta.get("overall_status")},
        "registry": REGISTRY_REFS,
    })
    LOGGER.info("EXP-021 BLOCKED — EXP-020 dependency gate failed: %s", "; ".join(reasons))


def run() -> None:
    """Execute EXP-021 end to end and write all result artifacts."""
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
    diag_rows: list[dict[str, Any]] = []
    for inst in tqdm(instruments, desc="cells: match + react"):
        for domain in DOMAINS:
            frame = cell_frames[(inst, domain)]
            ev_cell = events.filter((pl.col("instrument") == inst) & (pl.col("domain") == domain))
            rg_cell = regimes.filter((pl.col("instrument") == inst) & (pl.col("domain") == domain))
            validate_event_join(ev_cell, frame, f"{inst}/{domain}")
            cell_records, cell_diag = process_cell(inst, domain, ev_cell, rg_cell, frame)
            records.extend(cell_records)
            diag_rows.extend(cell_diag)

    reportable_map = reportable_cells(records, instruments)
    reportable_domains = [d for d in DOMAINS if len(reportable_map[d]) >= DOMAIN_MIN_INSTRUMENTS]

    domain_stats: dict[str, dict[int, dict[str, Any]]] = {}
    primary_pvals: dict[str, float] = {}
    for domain in tqdm(reportable_domains, desc="domain inference"):
        domain_stats[domain] = evaluate_domain(records, domain, reportable_map[domain])
        primary_pvals[domain] = domain_stats[domain][PRIMARY_HORIZON]["raw_p"]
    holm = holm_adjust(primary_pvals) if primary_pvals else {}
    verdict, labels = decide_verdict(domain_stats, holm, reportable_domains)

    _write_all_outputs(records, diag_rows, domain_stats, holm, labels, reportable_map,
                       reportable_domains, instruments, verdict, dep_meta, analysis_end)
    LOGGER.info("EXP-021 verdict: %s | reportable domains: %s", verdict, reportable_domains or "none")


def _write_all_outputs(records, diag_rows, domain_stats, holm, labels, reportable_map,
                       reportable_domains, instruments, verdict, dep_meta, analysis_end) -> None:
    """Write every result table, plot, and the run metadata."""
    obs_cols = ["instrument", "domain", "regime_id", "direction", "trigger_idx", "horizon",
                "event_return_bps", "control_mean_bps", "paired_diff_bps", "n_controls",
                "control_indices", "control_returns_bps", "reportable", "reason"]
    pl.DataFrame(records).select(obs_cols).write_csv(RESULTS_DIR / "reaction_observations.csv")
    write_rows(RESULTS_DIR / "reaction_summary.csv", reaction_summary_rows(records))
    write_rows(RESULTS_DIR / "domain_reaction_tests.csv",
               domain_test_rows(domain_stats, holm, labels, reportable_map))
    write_rows(RESULTS_DIR / "control_match_diagnostics.csv", diag_rows)

    plot_domain_forest(domain_stats, reportable_domains, PLOTS_DIR / "domain_reaction_forest.png")
    plot_event_control_distributions(records, reportable_domains, PLOTS_DIR / "event_control_distributions.png")
    plot_instrument_direction_heatmap(records, instruments, PLOTS_DIR / "instrument_direction_heatmap.png")
    plot_control_match_diagnostics(diag_rows, instruments, PLOTS_DIR / "control_match_diagnostics.png")

    write_json(RESULTS_DIR / "run_metadata.json", {
        "experiment_id": EXPERIMENT_ID,
        "title": "AVWAP Bounce Reaction Study",
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
        "parameters": {
            "horizons": list(HORIZONS), "primary_horizon": PRIMARY_HORIZON,
            "max_controls": MAX_CONTROLS, "min_controls": MIN_CONTROLS,
            "exclusion_bars": EXCLUSION_BARS, "control_scope": "same_regime_only",
            "domain_estimator": "instrument_averaged_equal_weight",
            "min_reportable_events": MIN_REPORTABLE_EVENTS,
            "min_direction_events": MIN_DIRECTION_EVENTS,
            "domain_min_instruments": DOMAIN_MIN_INSTRUMENTS,
            "n_bootstrap": N_BOOT, "n_permutation": N_PERM, "alpha": ALPHA,
            "ci_percentiles": list(CI_PERCENTILES),
        },
        "domain_primary_effects": {
            d: domain_stats[d][PRIMARY_HORIZON]["effect"] for d in reportable_domains
        },
        "registry": REGISTRY_REFS,
    })


def main() -> None:
    """Configure logging and run the experiment (manual execution entry point)."""
    configure_logging()
    run()


if __name__ == "__main__":
    main()
