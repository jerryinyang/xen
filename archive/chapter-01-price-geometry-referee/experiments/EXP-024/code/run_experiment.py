"""Experiment EXP-024: AVWAP Event-Edge Dissipation Decomposition (CF-AVWAP-001 diagnostic).

Implements the approved analysis plan (analysis-plan.md). EXP-024 is a **diagnostic**:
it runs no qualification suite and issues no pass/fail verdict. It decides, per domain,
whether the AVWAP bounce edge that EXP-021 measured (fixed-horizon reaction) but EXP-023
lost as an always-on strategy (~0 gross) is lost to:

    fork (a) -- a fixable holding/exit problem: a bounded max-hold horizon captures
               materially more gross edge than holding to lifetime completion AND
               clears the ratified-loose suite floor with usable precision; OR
    fork (b) -- entry/position dilution: no adequately powered bounded horizon
               reaches the loosest floor, so scoped /EXIT is not justified.

Pipeline:
    1. Dependency gate on EXP-020 substrate (SUPPORTED_FULL, ready 5m/1h/4h, 0 invariant
       failures, deterministic replay) and the presence of EXP-022 lifetime observations.
    2. Holdout-safe domain reconstruction (first-70% slice, EXP-020/021/022 convention),
       EXP-020 metadata equality, and a hard-fail event->domain-bar join.
    3. Horizon-decay curve: per-event direction-signed log-close gross returns over a
       fixed horizon grid (signed_log_bps convention), pooled by domain.
    4. Always-on lifetime reference (EXP-022 lifetime_bps over completed moves) and the
       bounded-vs-lifetime contrast on a common per-horizon completed event set.
    5. Per-domain fork verdict (gross primary) under the predeclared rule, with a
       regime-cluster bootstrap CI and Holm adjustment across the horizon grid.
    6. Secondary decompositions: trend-change-exit return distribution, holding-period
       and exposure descriptives, and a cost-attribution lens (per-event round-trip
       cost). Four bounded visualisations.

The final 30% global holdout is never loaded: domain frames are rebuilt from the
first-70% slice via ``load_analysis_data``, and every horizon contribution requires
``trigger_idx + h <= analysis_end_idx`` (never indexes the holdout).

Run:
    cd <project-root> && python python/experiments/EXP-024/code/run_experiment.py
"""
from __future__ import annotations

import json
import logging
from collections import defaultdict
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
    cost_bps_for,
    list_timebar_files,
    load_analysis_data,
    seed_for,
)


LOGGER = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-024"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = PROJECT_ROOT / "data"
EXPERIMENT_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
DEP020_DIR = PROJECT_ROOT / "python" / "experiments" / "EXP-020" / "results"
DEP021_DIR = PROJECT_ROOT / "python" / "experiments" / "EXP-021" / "results"
DEP022_DIR = PROJECT_ROOT / "python" / "experiments" / "EXP-022" / "results"

DOMAINS: tuple[str, ...] = ("5m", "1h", "4h")
PRIMARY_DOMAIN = "5m"

# Predeclared horizon grid (completed domain bars after the trigger). Fixed a priori;
# never selected from realized returns.
HORIZON_GRID: tuple[int, ...] = (1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24)
CROSSCHECK_HORIZONS: tuple[int, ...] = (1, 3, 6)  # EXP-021 external consistency points
CROSSCHECK_TOL_BPS = 1e-6
JOIN_KEYS: tuple[str, ...] = ("instrument", "domain", "regime_id", "trigger_idx")

# Frozen ratified-loose detection floors (bps) by domain -- reference thresholds only;
# the frozen suite is NOT run here.
LOOSE_FLOOR_BPS: dict[str, float] = {"5m": 0.5, "1h": 2.0, "4h": 8.0}

# Fork (a) material margin: bounded hold must beat the always-on lifetime hold by at
# least this many bps. margin_d = max(0.5, 0.25 * floor_d) -> 5m 0.5, 1h 0.5, 4h 2.0.
MARGIN_FLOOR_BPS = 0.5
MARGIN_FLOOR_FRACTION = 0.25

# Coverage rule: a domain (and the h* selection) needs at least this many common-set
# (reportable-at-h AND completed-lifetime) events to resolve a fork.
DOMAIN_MIN_COMPLETED = 100

# Inference (regime-cluster bootstrap; >= 10,000 resamples; non-parametric).
N_BOOT = 10_000
BOOT_CHUNK = 500
CI_PERCENTILES = (2.5, 97.5)
ALPHA = 0.05

# Outcome labels (match EXP-022).
OUT_FAVORABLE = "favorable"
OUT_ADVERSE = "adverse"
OUT_TREND = "trend_change"
OUT_UNFINISHED = "unfinished"

# Expected EXP-020 dependency state.
DEP_REQUIRED_STATUS = "SUPPORTED_FULL"
DEP_REQUIRED_DOMAINS = {"5m", "1h", "4h"}

REGISTRY_REFS = {
    "candidate_family": "CF-AVWAP-001",
    "diagnostic_id": "CF-AVWAP-001/DIAG-001",
    "registry": "docs/signal-registry/multiplicity-registry.md",
    "checkpoint": "docs/experiments-docs/checkpoints/2026-06-08-005-avwap-exit-and-branch-exploration",
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


def _truthy(value: Any) -> bool:
    """Interpret CSV/JSON bool values consistently."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return bool(value)


def check_dependency_gate() -> tuple[bool, list[str]]:
    """Assert EXP-020 substrate readiness and EXP-022 lifetime availability."""
    reasons: list[str] = []
    meta_path = DEP020_DIR / "run_metadata.json"
    if not meta_path.exists():
        return False, [f"missing EXP-020 metadata: {meta_path}"]
    meta = json.loads(meta_path.read_text())
    if meta.get("overall_status") != DEP_REQUIRED_STATUS:
        reasons.append(f"EXP-020 overall_status={meta.get('overall_status')} != {DEP_REQUIRED_STATUS}")
    if set(meta.get("ready_domains", [])) != DEP_REQUIRED_DOMAINS:
        reasons.append(f"EXP-020 ready_domains={meta.get('ready_domains')} != {sorted(DEP_REQUIRED_DOMAINS)}")
    if int(meta.get("invariant_failure_count", -1)) != 0:
        reasons.append(f"EXP-020 invariant_failure_count={meta.get('invariant_failure_count')} != 0")
    if not _truthy(meta.get("determinism_pass", False)):
        reasons.append("EXP-020 determinism_pass is not true")
    for name, directory in (("avwap_events.csv", DEP020_DIR),
                            ("lifetime_observations.csv", DEP022_DIR),
                            ("reaction_observations.csv", DEP021_DIR)):
        if not (directory / name).exists():
            reasons.append(f"missing dependency artifact: {directory / name}")
    return len(reasons) == 0, reasons


def expected_timebar_sources() -> set[str]:
    """Return the source Parquet filenames recorded by EXP-020 metadata."""
    expected_path = DEP020_DIR / "analysis_metadata.csv"
    if not expected_path.exists():
        raise FileNotFoundError(f"missing EXP-020 analysis metadata: {expected_path}")
    return set(
        pl.read_csv(expected_path)
        .get_column("source_file")
        .unique()
        .to_list()
    )


def duplicate_key_count(frame: pl.DataFrame, keys: tuple[str, ...]) -> int:
    """Count rows beyond the first occurrence for a compound key."""
    dupes = frame.group_by(list(keys)).len().filter(pl.col("len") > 1)
    if dupes.is_empty():
        return 0
    return int((dupes.get_column("len") - 1).sum())


def event_join_diagnostic_rows(
    events: pl.DataFrame, life: pl.DataFrame, joined: pl.DataFrame
) -> list[dict[str, Any]]:
    """Verify the EXP-020 event to EXP-022 lifetime left join preserves event rows."""
    event_dupes = duplicate_key_count(events, JOIN_KEYS)
    life_dupes = duplicate_key_count(life, JOIN_KEYS)
    if event_dupes or life_dupes:
        raise ValueError(
            "non-unique EXP-024 event join keys: "
            f"events duplicate rows beyond first={event_dupes}, lifetime={life_dupes}"
        )
    if joined.height != events.height:
        raise ValueError(
            f"EXP-020 -> EXP-022 left join changed row count: {events.height} -> {joined.height}"
        )

    rows: list[dict[str, Any]] = []
    for domain in DOMAINS:
        ev = events.filter(pl.col("domain") == domain)
        lf = life.filter(pl.col("domain") == domain)
        jo = joined.filter(pl.col("domain") == domain)
        matched = jo.filter(pl.col("lifetime_bps").is_not_null())
        rows.append({
            "domain": domain,
            "raw_event_rows": ev.height,
            "lifetime_event_rows": lf.height,
            "joined_rows": jo.height,
            "matched_lifetime_rows": matched.height,
            "unmatched_lifetime_rows": jo.height - matched.height,
            "row_count_preserved": jo.height == ev.height,
            "event_duplicate_rows_beyond_first": duplicate_key_count(ev, JOIN_KEYS),
            "lifetime_duplicate_rows_beyond_first": duplicate_key_count(lf, JOIN_KEYS),
        })
    return rows


def load_event_table() -> tuple[pl.DataFrame, list[dict[str, Any]]]:
    """Load EXP-020 events left-joined to EXP-022 event-role lifetime outcomes.

    Returns one row per EXP-020 bounce event with the columns needed for the
    horizon curve (``trigger_idx``, ``direction``, ``trigger_close``,
    ``is_pyramid_bounce``) and, where the event has an EXP-022 lifetime record,
    the completed-move outcome (``outcome``, ``bars_to_completion``,
    ``lifetime_bps``). Events absent from EXP-022 (invalid target geometry,
    dropped upstream) keep null lifetime fields and contribute only to the
    all-reportable horizon curve, never to the completed common set.
    """
    events = pl.read_csv(DEP020_DIR / "avwap_events.csv", try_parse_dates=True).select(
        "instrument", "domain", "regime_id", "direction", "trigger_idx",
        "trigger_close", "is_pyramid_bounce",
    )
    life = (
        pl.read_csv(DEP022_DIR / "lifetime_observations.csv", try_parse_dates=True)
        .filter(pl.col("role") == "event")
        .select(
            "instrument", "domain", "regime_id",
            pl.col("event_trigger_idx").alias("trigger_idx"),
            "outcome", "completion_idx", "bars_to_completion", "lifetime_bps",
        )
    )
    joined = events.join(life, on=JOIN_KEYS, how="left")
    return joined, event_join_diagnostic_rows(events, life, joined)


# --------------------------------------------------------------------------- #
# Domain reconstruction + holdout-safe join guard (EXP-022 convention)
# --------------------------------------------------------------------------- #
def build_cell_log_close() -> tuple[
    dict[tuple[str, str], np.ndarray],
    dict[tuple[str, str], pl.DataFrame],
    list[dict[str, Any]],
]:
    """Rebuild first-70% 5m/1h/4h domain bars and per-cell metadata."""
    expected_sources = expected_timebar_sources()
    files = [path for path in list_timebar_files(DATA_DIR) if path.name in expected_sources]
    if not files:
        raise FileNotFoundError(
            f"none of the EXP-020 source files are present under {DATA_DIR / 'timebars'}"
        )
    missing = sorted(expected_sources.difference({path.name for path in files}))
    if missing:
        raise FileNotFoundError(f"missing EXP-020 source files under data/timebars: {missing}")
    log_close: dict[tuple[str, str], np.ndarray] = {}
    frames: dict[tuple[str, str], pl.DataFrame] = {}
    metadata_rows: list[dict[str, Any]] = []
    for path in tqdm(files, desc="rebuild domain bars"):
        data = load_analysis_data(path)
        for domain, frame in build_domain_frames(data.frame).items():
            close = frame.get_column("Close").to_numpy().astype(float)
            log_close[(data.instrument, domain)] = np.log(close)
            frames[(data.instrument, domain)] = frame
            metadata_rows.append({
                "instrument": data.instrument,
                "domain": domain,
                "source_file": data.source_file,
                "source_total_rows": data.total_rows,
                "analysis_rows_1m": data.analysis_rows,
                "analysis_start_1m": data.analysis_start,
                "analysis_end_1m": data.analysis_end,
                "domain_bars": frame.height,
                "domain_min_close_time": str(frame.get_column("CloseTime").min()) if frame.height else None,
                "domain_max_close_time": str(frame.get_column("CloseTime").max()) if frame.height else None,
            })
    return log_close, frames, metadata_rows


def validate_analysis_metadata(metadata_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compare reconstructed domain metadata against EXP-020 analysis metadata."""
    expected_path = DEP020_DIR / "analysis_metadata.csv"
    if not expected_path.exists():
        raise FileNotFoundError(f"missing EXP-020 analysis metadata: {expected_path}")
    expected = pl.read_csv(expected_path)
    expected_by_cell = {
        (str(r["instrument"]), str(r["domain"])): r
        for r in expected.to_dicts()
    }
    check_rows: list[dict[str, Any]] = []
    for row in metadata_rows:
        cell = (str(row["instrument"]), str(row["domain"]))
        if cell not in expected_by_cell:
            raise ValueError(f"{cell[0]}/{cell[1]} missing from EXP-020 analysis_metadata.csv")
        exp = expected_by_cell[cell]
        checks = {
            "source_file_match": row["source_file"] == exp["source_file"],
            "source_total_rows_match": int(row["source_total_rows"]) == int(exp["source_total_rows"]),
            "analysis_rows_1m_match": int(row["analysis_rows_1m"]) == int(exp["analysis_rows_1m"]),
            "analysis_start_1m_match": str(row["analysis_start_1m"]) == str(exp["analysis_start_1m"]),
            "analysis_end_1m_match": str(row["analysis_end_1m"]) == str(exp["analysis_end_1m"]),
            "domain_bars_match": int(row["domain_bars"]) == int(exp["domain_bars"]),
            "domain_min_close_time_match": str(row["domain_min_close_time"]) == str(exp["domain_min_close_time"]),
            "domain_max_close_time_match": str(row["domain_max_close_time"]) == str(exp["domain_max_close_time"]),
        }
        passed = all(checks.values())
        check_rows.append({
            "instrument": cell[0],
            "domain": cell[1],
            "passed": passed,
            **checks,
        })
    failures = [r for r in check_rows if not r["passed"]]
    if failures:
        labels = [f"{r['instrument']}/{r['domain']}" for r in failures]
        raise ValueError(f"EXP-020 analysis metadata mismatch: {labels}")
    return check_rows


def validate_event_join(events_cell: pl.DataFrame, frame: pl.DataFrame, label: str) -> None:
    """Hard-fail if any event's ``trigger_idx`` disagrees with the domain bar close.

    Re-asserts the holdout fence: every ``trigger_idx`` indexes a real bar in the
    first-70% frame, and its ``Close`` matches the EXP-020 ``trigger_close`` exactly.
    """
    n = frame.height
    idx = events_cell.get_column("trigger_idx").to_numpy()
    if events_cell.height and (idx.min() < 0 or idx.max() >= n):
        raise ValueError(f"{label}: trigger_idx out of domain range [0,{n}) (holdout fence breach).")
    close_arr = frame.get_column("Close").to_numpy().astype(float)
    ev_close = events_cell.get_column("trigger_close").to_numpy().astype(float)
    bad = int(np.sum(~np.isclose(close_arr[idx], ev_close, rtol=1e-9, atol=1e-9)))
    if bad:
        raise ValueError(
            f"{label}: event/domain close mismatch on {bad} rows; "
            "domain reconstruction does not reproduce the EXP-020 substrate."
        )


# --------------------------------------------------------------------------- #
# Horizon returns (pure, deterministic, look-ahead-safe)
# --------------------------------------------------------------------------- #
def horizon_return_matrix(
    trigger_idx: np.ndarray, direction: np.ndarray, log_close: np.ndarray
) -> np.ndarray:
    """Direction-signed log-close gross return (bps) per event per horizon.

    ``out[e, j]`` is ``10_000 * direction_e * (log_close[t_e + h_j] - log_close[t_e])``
    for ``h_j`` in ``HORIZON_GRID``, or ``NaN`` when ``t_e + h_j`` exceeds the
    analysis-set end (non-reportable at that horizon; never indexes the holdout).
    """
    n = log_close.size
    base = log_close[trigger_idx]
    out = np.full((trigger_idx.size, len(HORIZON_GRID)), np.nan)
    for j, h in enumerate(HORIZON_GRID):
        target = trigger_idx + h
        ok = target <= n - 1
        out[ok, j] = 10_000.0 * direction[ok] * (log_close[target[ok]] - base[ok])
    return out


def point_mean_by_horizon(returns: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per-horizon mean and reportable count over events selected by ``mask``."""
    sub = returns[mask]
    finite = np.isfinite(sub)
    counts = finite.sum(axis=0)
    sums = np.where(finite, sub, 0.0).sum(axis=0)
    means = np.where(counts > 0, sums / np.where(counts > 0, counts, 1), np.nan)
    return means, counts.astype(int)


# --------------------------------------------------------------------------- #
# Regime-cluster bootstrap of a per-horizon mean (EXP-021/022 dependence model)
# --------------------------------------------------------------------------- #
def cluster_sums_counts(
    returns: np.ndarray, mask: np.ndarray, cluster_ids: np.ndarray
) -> tuple[dict[int, np.ndarray], np.ndarray, np.ndarray]:
    """Per-cluster (regime) finite-sum and finite-count of returns at each horizon.

    Returns ``(stratum_to_cluster_rows, cluster_sum, cluster_cnt)`` where
    ``cluster_sum``/``cluster_cnt`` are ``(n_clusters, n_horizons)`` arrays indexed
    by a dense cluster row, and the mapping groups cluster rows by stratum so the
    bootstrap resamples whole regime clusters within each stratum.
    """
    sel = np.where(mask)[0]
    cids = cluster_ids[sel]
    uniq = np.unique(cids)
    row_of = {int(c): i for i, c in enumerate(uniq)}
    cluster_sum = np.zeros((uniq.size, len(HORIZON_GRID)))
    cluster_cnt = np.zeros((uniq.size, len(HORIZON_GRID)))
    finite = np.isfinite(returns)
    for e in sel:
        r = row_of[int(cluster_ids[e])]
        f = finite[e]
        cluster_sum[r, f] += returns[e, f]
        cluster_cnt[r, f] += 1.0
    return row_of, cluster_sum, cluster_cnt


def cluster_bootstrap_mean(
    cluster_sum: np.ndarray, cluster_cnt: np.ndarray, stratum_rows: list[np.ndarray],
    rng: np.random.Generator,
) -> np.ndarray:
    """Bootstrap distribution (N_BOOT x n_horizons) of the pooled per-horizon mean.

    Resamples whole regime clusters with replacement within each stratum
    (instrument x direction), preserving per-stratum cluster counts, then forms the
    pooled mean = sum(resampled cluster sums) / sum(resampled cluster counts).
    """
    n_h = cluster_sum.shape[1]
    total_sum = np.zeros((N_BOOT, n_h))
    total_cnt = np.zeros((N_BOOT, n_h))
    for rows in stratum_rows:
        k = rows.size
        if k == 0:
            continue
        cs = cluster_sum[rows]
        cc = cluster_cnt[rows]
        for start in range(0, N_BOOT, BOOT_CHUNK):
            size = min(BOOT_CHUNK, N_BOOT - start)
            idx = rng.integers(0, k, size=(size, k))
            total_sum[start : start + size] += cs[idx].sum(axis=1)
            total_cnt[start : start + size] += cc[idx].sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        boot = np.where(total_cnt > 0, total_sum / total_cnt, np.nan)
    return boot


def cluster_bootstrap_scalar_mean(
    values: np.ndarray, cluster_ids: np.ndarray, stratum_keys: np.ndarray,
    rng: np.random.Generator,
) -> tuple[float | None, float | None, float | None, int]:
    """Regime-cluster bootstrap CI for one scalar event mean."""
    finite = np.isfinite(values)
    if not np.any(finite):
        return None, None, None, 0
    vals = values[finite]
    cids = cluster_ids[finite]
    strata = stratum_keys[finite]
    point = float(np.mean(vals))
    unique_clusters = np.unique(cids)
    row_of = {int(c): i for i, c in enumerate(unique_clusters)}
    cluster_sum = np.zeros(unique_clusters.size)
    cluster_cnt = np.zeros(unique_clusters.size)
    cluster_strata: dict[int, Any] = {}
    for value, cid, stratum in zip(vals, cids, strata):
        row = row_of[int(cid)]
        cluster_sum[row] += float(value)
        cluster_cnt[row] += 1.0
        cluster_strata[row] = stratum
    stratum_rows: dict[Any, list[int]] = defaultdict(list)
    for row, stratum in cluster_strata.items():
        stratum_rows[stratum].append(row)
    boot_sum = np.zeros(N_BOOT)
    boot_cnt = np.zeros(N_BOOT)
    for rows_raw in stratum_rows.values():
        rows = np.array(rows_raw, dtype=np.int64)
        k = rows.size
        if k == 0:
            continue
        sums = cluster_sum[rows]
        cnts = cluster_cnt[rows]
        for start in range(0, N_BOOT, BOOT_CHUNK):
            size = min(BOOT_CHUNK, N_BOOT - start)
            idx = rng.integers(0, k, size=(size, k))
            boot_sum[start : start + size] += sums[idx].sum(axis=1)
            boot_cnt[start : start + size] += cnts[idx].sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        boot = np.where(boot_cnt > 0, boot_sum / boot_cnt, np.nan)
    return point, float(np.nanpercentile(boot, 2.5)), float(np.nanpercentile(boot, 97.5)), int(vals.size)


def holm_adjust(pvalues: list[float]) -> list[float]:
    """Holm step-down adjustment over a family of one-sided p-values (index-aligned)."""
    order = sorted(range(len(pvalues)), key=lambda i: pvalues[i])
    m = len(pvalues)
    adjusted = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvalues[i]))
        adjusted[i] = running
    return adjusted


# --------------------------------------------------------------------------- #
# Per-domain fork evaluation
# --------------------------------------------------------------------------- #
def margin_for(domain: str) -> float:
    """Fork (a) material margin for a domain: max(0.5, 0.25 * loose floor)."""
    return max(MARGIN_FLOOR_BPS, MARGIN_FLOOR_FRACTION * LOOSE_FLOOR_BPS[domain])


def evaluate_domain_fork(
    domain: str, dom_events: pl.DataFrame, log_close: dict[tuple[str, str], np.ndarray]
) -> dict[str, Any]:
    """Compute the horizon curves, bootstrap CIs, and the predeclared fork verdict."""
    instrument = dom_events.get_column("instrument").to_numpy()
    direction = dom_events.get_column("direction").to_numpy().astype(float)
    regime = dom_events.get_column("regime_id").to_numpy().astype(int)
    trig = dom_events.get_column("trigger_idx").to_numpy().astype(np.int64)
    life = dom_events.get_column("lifetime_bps").to_numpy().astype(float)  # NaN if not completed

    # Horizon returns, computed per (instrument) cell against its own log-close array.
    returns = np.full((trig.size, len(HORIZON_GRID)), np.nan)
    for inst in np.unique(instrument):
        m = instrument == inst
        returns[m] = horizon_return_matrix(trig[m], direction[m], log_close[(inst, domain)])

    completed = np.isfinite(life)
    all_mask = np.ones(trig.size, dtype=bool)
    g_all, n_all = point_mean_by_horizon(returns, all_mask)
    g_common, n_common = point_mean_by_horizon(returns, completed)

    # Dense cluster ids and stratum groups over the common (completed) set.
    inst_codes = {inst: i for i, inst in enumerate(np.unique(instrument))}
    inst_idx = np.array([inst_codes[i] for i in instrument])
    cluster_ids = inst_idx.astype(np.int64) * 1_000_000 + regime  # unique per (instrument, regime)
    row_of, cluster_sum, cluster_cnt = cluster_sums_counts(returns, completed, cluster_ids)
    stratum_rows = _stratum_cluster_rows(inst_idx, direction, cluster_ids, completed, row_of)

    rng = np.random.default_rng(seed_for(EXPERIMENT_ID, domain, "horizon_bootstrap"))
    boot = cluster_bootstrap_mean(cluster_sum, cluster_cnt, stratum_rows, rng)
    ci_lo = np.nanpercentile(boot, CI_PERCENTILES[0], axis=0)
    ci_hi = np.nanpercentile(boot, CI_PERCENTILES[1], axis=0)
    p_raw = [float((1 + np.sum(boot[:, j] <= 0.0)) / (1 + np.sum(np.isfinite(boot[:, j]))))
             for j in range(len(HORIZON_GRID))]
    p_holm = holm_adjust(p_raw)

    # Lifetime always-on reference on the common set, recomputed per horizon.
    g_life = np.array([
        float(np.mean(life[completed & np.isfinite(returns[:, j])]))
        if np.any(completed & np.isfinite(returns[:, j])) else np.nan
        for j in range(len(HORIZON_GRID))
    ])
    delta_returns = returns - life[:, None]
    _, delta_sum, delta_cnt = cluster_sums_counts(delta_returns, completed, cluster_ids)
    delta_boot = cluster_bootstrap_mean(delta_sum, delta_cnt, stratum_rows, rng)
    delta_ci_lo = np.nanpercentile(delta_boot, CI_PERCENTILES[0], axis=0)
    delta_ci_hi = np.nanpercentile(delta_boot, CI_PERCENTILES[1], axis=0)
    delta_mean, _ = point_mean_by_horizon(delta_returns, completed)

    verdict = _decide_fork(domain, g_common, n_common, p_holm, ci_lo, ci_hi, g_life)
    verdict.update({
        "g_all": g_all, "n_all": n_all, "g_common": g_common, "n_common": n_common,
        "ci_lo": ci_lo, "ci_hi": ci_hi, "p_raw": p_raw, "p_holm": p_holm, "g_life": g_life,
        "delta_mean": delta_mean, "delta_ci_lo": delta_ci_lo, "delta_ci_hi": delta_ci_hi,
    })
    return verdict


def _stratum_cluster_rows(
    inst_idx: np.ndarray, direction: np.ndarray, cluster_ids: np.ndarray,
    mask: np.ndarray, row_of: dict[int, int],
) -> list[np.ndarray]:
    """Group dense cluster rows by (instrument, direction) stratum for resampling."""
    strata: dict[tuple[int, int], set[int]] = defaultdict(set)
    for e in np.where(mask)[0]:
        strata[(int(inst_idx[e]), int(direction[e]))].add(row_of[int(cluster_ids[e])])
    return [np.array(sorted(rows), dtype=np.int64) for rows in strata.values()]


def _decide_fork(
    domain: str, g_common: np.ndarray, n_common: np.ndarray, p_holm: list[float],
    ci_lo: np.ndarray, ci_hi: np.ndarray, g_life: np.ndarray,
) -> dict[str, Any]:
    """Apply the predeclared per-domain fork rule (gross primary)."""
    floor_d = LOOSE_FLOOR_BPS[domain]
    margin_d = margin_for(domain)
    # h* = max-g horizon among horizons with adequate common-set N.
    eligible = np.where(n_common >= DOMAIN_MIN_COMPLETED)[0]
    base = {"domain": domain, "floor_bps": floor_d, "margin_bps": margin_d}
    if eligible.size == 0:
        return {**base, "verdict": "INCONCLUSIVE_COVERAGE", "h_star": None,
                "g_star": None, "g_life_star": None, "delta_star": None,
                "p_holm_star": None, "ci_lo_star": None, "ci_hi_star": None, "n_star": 0}
    j_star = int(eligible[np.nanargmax(g_common[eligible])])
    g_star = float(g_common[j_star])
    g_life_star = float(g_life[j_star])
    delta_star = g_star - g_life_star
    holm_star = float(p_holm[j_star])
    holm_positive = holm_star < ALPHA
    floor_clear = float(ci_lo[j_star]) >= floor_d
    underpowered_floor_candidate = bool(
        np.any((n_common < DOMAIN_MIN_COMPLETED) & np.isfinite(g_common) & (g_common >= floor_d))
    )
    if g_star >= floor_d and floor_clear and holm_positive and delta_star >= margin_d:
        verdict = "FORK_A_FIXABLE_EXIT"
    elif g_star < floor_d and not underpowered_floor_candidate:
        verdict = "FORK_B_DILUTION"
    else:
        verdict = "INCONCLUSIVE_UNRESOLVED"
    return {**base, "verdict": verdict, "h_star": HORIZON_GRID[j_star], "g_star": g_star,
            "g_life_star": g_life_star, "delta_star": delta_star, "p_holm_star": holm_star,
            "ci_lo_star": float(ci_lo[j_star]), "ci_hi_star": float(ci_hi[j_star]),
            "n_star": int(n_common[j_star])}


def phase_level_fork(domain_verdicts: dict[str, str]) -> str:
    """Aggregate per-domain verdicts into the Stage-B gating decision."""
    vals = set(domain_verdicts.values())
    if domain_verdicts.get(PRIMARY_DOMAIN) == "FORK_A_FIXABLE_EXIT" or "FORK_A_FIXABLE_EXIT" in vals:
        return "FORK_A_STAGE_B_JUSTIFIED"
    if all(v == "FORK_B_DILUTION" for v in domain_verdicts.values()):
        return "FORK_B_SKIP_STAGE_B"
    return "MIXED_OR_INCONCLUSIVE"


# --------------------------------------------------------------------------- #
# Secondary decompositions (descriptive)
# --------------------------------------------------------------------------- #
def trend_change_rows(events: pl.DataFrame) -> list[dict[str, Any]]:
    """Per-domain trend-change-exit lifetime-return distribution + outcome context."""
    rows: list[dict[str, Any]] = []
    for domain in DOMAINS:
        dom = events.filter((pl.col("domain") == domain) & pl.col("lifetime_bps").is_not_null())
        trend = dom.filter(pl.col("outcome") == OUT_TREND)
        tc = trend.get_column("lifetime_bps").to_numpy().astype(float)
        if trend.height:
            inst = trend.get_column("instrument").to_numpy()
            inst_codes = {v: i for i, v in enumerate(np.unique(inst))}
            inst_idx = np.array([inst_codes[v] for v in inst], dtype=np.int64)
            direction = trend.get_column("direction").to_numpy().astype(np.int64)
            regime = trend.get_column("regime_id").to_numpy().astype(np.int64)
            cluster_ids = inst_idx * 1_000_000 + regime
            stratum_keys = inst_idx * 10 + direction
            tc_mean, tc_ci_lo, tc_ci_hi, tc_n = cluster_bootstrap_scalar_mean(
                tc, cluster_ids, stratum_keys,
                np.random.default_rng(seed_for(EXPERIMENT_ID, domain, "trend_change_bootstrap")),
            )
        else:
            tc_mean, tc_ci_lo, tc_ci_hi, tc_n = None, None, None, 0
        fav = dom.filter(pl.col("outcome") == OUT_FAVORABLE).get_column("lifetime_bps").to_numpy().astype(float)
        adv = dom.filter(pl.col("outcome") == OUT_ADVERSE).get_column("lifetime_bps").to_numpy().astype(float)
        rows.append({
            "domain": domain, "n_trend_change": tc_n,
            "tc_mean_bps": tc_mean,
            "tc_ci_lo_bps": tc_ci_lo,
            "tc_ci_hi_bps": tc_ci_hi,
            "tc_median_bps": float(np.median(tc)) if tc.size else None,
            "tc_q25_bps": float(np.percentile(tc, 25)) if tc.size else None,
            "tc_q75_bps": float(np.percentile(tc, 75)) if tc.size else None,
            "tc_frac_negative": float(np.mean(tc < 0)) if tc.size else None,
            "favorable_median_bps": float(np.median(fav)) if fav.size else None,
            "adverse_median_bps": float(np.median(adv)) if adv.size else None,
        })
    return rows


def reconstructed_exposure(events_cell: pl.DataFrame, domain_bars: int) -> tuple[int, int, float | None]:
    """Reconstruct non-pyramided entry count and active-bar fraction for one cell."""
    if domain_bars <= 0:
        return 0, 0, None
    active_until = -1
    active_bars = 0
    entries = 0
    for row in events_cell.sort("trigger_idx").iter_rows(named=True):
        completion = row.get("completion_idx")
        if completion is None:
            continue
        trigger = int(row["trigger_idx"])
        completion_idx = int(completion)
        if trigger <= active_until:
            continue
        entries += 1
        active_bars += max(0, completion_idx - trigger)
        active_until = max(active_until, completion_idx)
    return entries, active_bars, active_bars / domain_bars


def holding_exposure_rows(
    events: pl.DataFrame, frames: dict[tuple[str, str], pl.DataFrame]
) -> list[dict[str, Any]]:
    """Per-domain outcome composition, holding period, and exposure descriptives."""
    rows: list[dict[str, Any]] = []
    for domain in DOMAINS:
        dom = events.filter(pl.col("domain") == domain)
        n_events = dom.height
        n_pyramid = int(dom.get_column("is_pyramid_bounce").map_elements(_truthy, return_dtype=pl.Boolean).sum())
        comp = dom.filter(pl.col("bars_to_completion").is_not_null())
        bars = comp.get_column("bars_to_completion").to_numpy().astype(float)
        domain_bars_total = 0
        entry_count = 0
        active_bars_total = 0
        for (instrument, cell_domain), frame in frames.items():
            if cell_domain != domain:
                continue
            domain_bars_total += frame.height
            cell = dom.filter(pl.col("instrument") == instrument)
            entries, active_bars, _ = reconstructed_exposure(cell, frame.height)
            entry_count += entries
            active_bars_total += active_bars
        row = {"domain": domain, "n_events": n_events, "n_pyramid_bounce": n_pyramid,
               "n_completed": int(comp.height),
               "domain_bars_total": domain_bars_total,
               "event_prevalence_per_bar": (n_events / domain_bars_total) if domain_bars_total else None,
               "entry_count_reconstructed": entry_count,
               "active_bar_fraction_reconstructed": (
                   active_bars_total / domain_bars_total if domain_bars_total else None
               ),
               "bars_mean": float(np.mean(bars)) if bars.size else None,
               "bars_median": float(np.median(bars)) if bars.size else None,
               "bars_q90": float(np.percentile(bars, 90)) if bars.size else None}
        for outcome in (OUT_FAVORABLE, OUT_ADVERSE, OUT_TREND, OUT_UNFINISHED):
            row[f"n_{outcome}"] = int(dom.filter(pl.col("outcome") == outcome).height)
        rows.append(row)
    return rows


def cost_attribution_rows(
    domain_results: dict[str, dict[str, Any]], events: pl.DataFrame
) -> list[dict[str, Any]]:
    """Per-event round-trip cost lens: gross vs net at h* and over the lifetime hold."""
    rows: list[dict[str, Any]] = []
    for domain in DOMAINS:
        res = domain_results[domain]
        dom = events.filter((pl.col("domain") == domain) & pl.col("lifetime_bps").is_not_null())
        if dom.height:
            costs = np.array([cost_bps_for(inst, domain) for inst in dom.get_column("instrument").to_list()])
            cost = float(np.mean(costs))
        else:
            cost = float("nan")
        life_mean = float(dom.get_column("lifetime_bps").mean()) if dom.height else None
        g_star = res["g_star"]
        rows.append({
            "domain": domain, "mean_round_trip_cost_bps": cost,
            "g_star_gross_bps": g_star,
            "g_star_net_bps": (g_star - cost) if g_star is not None else None,
            "lifetime_gross_bps": life_mean,
            "lifetime_net_bps": (life_mean - cost) if life_mean is not None else None,
        })
    return rows


def bounded_vs_lifetime_rows(domain_results: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Flatten bounded-vs-lifetime contrasts with paired bootstrap CIs."""
    rows: list[dict[str, Any]] = []
    for domain in DOMAINS:
        res = domain_results[domain]
        for j, h in enumerate(HORIZON_GRID):
            rows.append({
                "domain": domain,
                "horizon": h,
                "g_common_bps": float(res["g_common"][j]),
                "g_life_bps": float(res["g_life"][j]),
                "delta_bps": float(res["delta_mean"][j]),
                "delta_ci_lo_bps": float(res["delta_ci_lo"][j]),
                "delta_ci_hi_bps": float(res["delta_ci_hi"][j]),
                "n_common": int(res["n_common"][j]),
            })
    return rows


def crosscheck_rows(
    events: pl.DataFrame,
    domain_results: dict[str, dict[str, Any]],
    log_close: dict[tuple[str, str], np.ndarray],
) -> list[dict[str, Any]]:
    """EXP-021 {1,3,6} consistency on the exact reportable event rows.

    EXP-021's reaction table is filtered by same-regime control reportability.
    Comparing it to EXP-024's all-event ``g_all`` is intentionally not an
    equality check. The reconstruction guardrail is whether EXP-024 recomputes
    EXP-021's per-event horizon return on the same event rows.
    """
    react = pl.read_csv(DEP021_DIR / "reaction_observations.csv", try_parse_dates=True)
    if "reportable" in react.columns:
        react = react.filter(pl.col("reportable").map_elements(_truthy, return_dtype=pl.Boolean))
    react = react.select(
        "instrument", "domain", "regime_id", "direction", "trigger_idx", "horizon",
        "event_return_bps", "control_mean_bps", "paired_diff_bps", "n_controls",
    )
    if duplicate_key_count(react, (*JOIN_KEYS, "direction", "horizon")):
        raise ValueError("EXP-021 reaction_observations.csv has duplicate reportable event/horizon keys")

    event_keys = events.select(
        "instrument", "domain", "regime_id", "direction", "trigger_idx"
    ).with_columns(pl.lit(True).alias("_event_key_match"))
    matched = react.join(event_keys, on=("instrument", "domain", "regime_id", "direction", "trigger_idx"), how="left")
    if matched.height != react.height:
        raise ValueError("EXP-021 cross-check join changed row count")
    missing = matched.filter(pl.col("_event_key_match").is_null()).height
    if missing:
        raise ValueError(f"EXP-021 cross-check has {missing} rows absent from EXP-020 event keys")

    calc_rows: list[dict[str, Any]] = []
    for row in matched.iter_rows(named=True):
        inst = str(row["instrument"])
        domain = str(row["domain"])
        trigger_idx = int(row["trigger_idx"])
        horizon = int(row["horizon"])
        direction = float(row["direction"])
        closes = log_close[(inst, domain)]
        if trigger_idx + horizon > closes.size - 1:
            raise ValueError(f"EXP-021 matched row exceeds EXP-024 analysis frame: {inst}/{domain}/{trigger_idx}+{horizon}")
        recomputed = 10_000.0 * direction * (closes[trigger_idx + horizon] - closes[trigger_idx])
        exp021_event = float(row["event_return_bps"])
        calc_rows.append({
            "instrument": inst,
            "domain": domain,
            "horizon": horizon,
            "exp021_event_bps": exp021_event,
            "exp024_matched_event_bps": float(recomputed),
            "row_abs_diff_bps": abs(exp021_event - float(recomputed)),
            "exp021_control_mean_bps": float(row["control_mean_bps"]),
            "exp021_paired_diff_bps": float(row["paired_diff_bps"]),
            "n_controls": int(row["n_controls"]),
        })

    calc = pl.DataFrame(calc_rows)
    grouped = calc.group_by("domain", "horizon").agg(
        pl.len().alias("n_matched_events"),
        pl.col("exp021_event_bps").mean().alias("exp021_matched_event_mean_bps"),
        pl.col("exp024_matched_event_bps").mean().alias("exp024_matched_event_mean_bps"),
        pl.col("row_abs_diff_bps").max().alias("max_row_abs_diff_bps"),
        pl.col("exp021_control_mean_bps").mean().alias("exp021_matched_control_mean_bps"),
        pl.col("exp021_paired_diff_bps").mean().alias("exp021_matched_paired_diff_bps"),
        pl.col("n_controls").mean().alias("mean_n_controls"),
    )
    rows: list[dict[str, Any]] = []
    for domain in DOMAINS:
        for h in CROSSCHECK_HORIZONS:
            j = HORIZON_GRID.index(h)
            sub = grouped.filter((pl.col("domain") == domain) & (pl.col("horizon") == h))
            if sub.is_empty():
                exp021 = recomputed = max_row = None
                n_matched = 0
                control_mean = paired_diff = mean_controls = None
            else:
                one = sub.row(0, named=True)
                exp021 = float(one["exp021_matched_event_mean_bps"])
                recomputed = float(one["exp024_matched_event_mean_bps"])
                max_row = float(one["max_row_abs_diff_bps"])
                n_matched = int(one["n_matched_events"])
                control_mean = float(one["exp021_matched_control_mean_bps"])
                paired_diff = float(one["exp021_matched_paired_diff_bps"])
                mean_controls = float(one["mean_n_controls"])
            rows.append({
                "domain": domain, "horizon": h, "n_matched_events": n_matched,
                "exp021_matched_event_mean_bps": exp021,
                "exp024_matched_event_mean_bps": recomputed,
                "abs_diff_bps": abs(exp021 - recomputed) if exp021 is not None else None,
                "max_row_abs_diff_bps": max_row,
                "exp021_matched_control_mean_bps": control_mean,
                "exp021_matched_paired_diff_bps": paired_diff,
                "mean_n_controls": mean_controls,
                "exp024_all_event_g_bps": float(domain_results[domain]["g_all"][j]),
                "all_event_minus_matched_bps": (
                    float(domain_results[domain]["g_all"][j]) - recomputed
                    if recomputed is not None else None
                ),
            })
    max_abs = max((r["abs_diff_bps"] for r in rows if r["abs_diff_bps"] is not None), default=0.0)
    max_row_abs = max((r["max_row_abs_diff_bps"] for r in rows if r["max_row_abs_diff_bps"] is not None), default=0.0)
    if max(max_abs, max_row_abs) > CROSSCHECK_TOL_BPS:
        raise ValueError(
            "EXP-021 matched-event cross-check failed: "
            f"max mean diff={max_abs:.12g} bps, max row diff={max_row_abs:.12g} bps"
        )
    return rows


# --------------------------------------------------------------------------- #
# Plotting (bounded inputs from the analysis pass)
# --------------------------------------------------------------------------- #
def plot_horizon_decay(domain_results: dict[str, dict[str, Any]], save_path: Path) -> None:
    """Per-domain horizon-decay curve with CI band, lifetime line, and loose floor."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), sharex=True)
    x = np.array(HORIZON_GRID)
    for ax, domain in zip(axes, DOMAINS):
        res = domain_results[domain]
        ax.axhline(0.0, color="gray", lw=0.8)
        floor = LOOSE_FLOOR_BPS[domain]
        ax.axhline(floor, color="crimson", ls="--", lw=1.0, label=f"loose floor {floor}")
        ax.fill_between(x, res["ci_lo"], res["ci_hi"], color="steelblue", alpha=0.2, label="95% CI (common)")
        ax.plot(x, res["g_common"], color="steelblue", marker="o", ms=3, label="g(h) common")
        ax.plot(x, res["g_all"], color="seagreen", ls=":", marker=".", ms=3, label="g(h) all")
        ax.plot(x, res["g_life"], color="darkorange", ls="-.", lw=1.0, label="always-on lifetime")
        if res["h_star"] is not None:
            ax.axvline(res["h_star"], color="purple", ls=":", lw=0.9)
        ax.set_title(f"{domain}: {res['verdict']}", fontsize=10)
        ax.set_xlabel("max-hold horizon (bars)")
    axes[0].set_ylabel("direction-signed gross return (bps)")
    axes[-1].legend(fontsize=7, loc="best")
    fig.suptitle("EXP-024 horizon-decay: bounded hold vs always-on lifetime vs loose floor", fontsize=11)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_outcome_holding(holding: list[dict[str, Any]], save_path: Path) -> None:
    """Per-domain outcome composition (share) and median holding period."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    outcomes = (OUT_FAVORABLE, OUT_ADVERSE, OUT_TREND, OUT_UNFINISHED)
    colors = ("seagreen", "crimson", "darkorange", "gray")
    bottoms = np.zeros(len(DOMAINS))
    x = np.arange(len(DOMAINS))
    by_domain = {r["domain"]: r for r in holding}
    for outcome, color in zip(outcomes, colors):
        vals = np.array([
            (by_domain[d][f"n_{outcome}"] / by_domain[d]["n_events"]) if by_domain[d]["n_events"] else 0.0
            for d in DOMAINS
        ])
        axes[0].bar(x, vals, bottom=bottoms, color=color, label=outcome)
        bottoms += vals
    axes[0].set_xticks(x); axes[0].set_xticklabels(DOMAINS)
    axes[0].set_ylabel("event share"); axes[0].set_title("Outcome composition"); axes[0].legend(fontsize=8)
    med = [next(r["bars_median"] for r in holding if r["domain"] == d) for d in DOMAINS]
    axes[1].bar(x, med, color="steelblue")
    axes[1].set_xticks(x); axes[1].set_xticklabels(DOMAINS)
    axes[1].set_ylabel("median bars to completion"); axes[1].set_title("Holding period")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_trend_change(tc_rows: list[dict[str, Any]], save_path: Path) -> None:
    """Per-domain trend-change-exit mean return vs favorable/adverse medians."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(DOMAINS))
    tc = [next(r["tc_mean_bps"] for r in tc_rows if r["domain"] == d) for d in DOMAINS]
    fav = [next(r["favorable_median_bps"] for r in tc_rows if r["domain"] == d) for d in DOMAINS]
    adv = [next(r["adverse_median_bps"] for r in tc_rows if r["domain"] == d) for d in DOMAINS]
    ax.axhline(0.0, color="gray", lw=0.8)
    ax.bar(x - 0.25, tc, width=0.25, color="darkorange", label="trend-change mean")
    ax.bar(x, fav, width=0.25, color="seagreen", label="favorable median")
    ax.bar(x + 0.25, adv, width=0.25, color="crimson", label="adverse median")
    ax.set_xticks(x); ax.set_xticklabels(DOMAINS)
    ax.set_ylabel("lifetime return (bps)")
    ax.set_title("Trend-change-exit returns vs favorable/adverse context")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_cost_attribution(cost_rows: list[dict[str, Any]], save_path: Path) -> None:
    """Per-domain gross vs net (round-trip cost) at h* and over the lifetime hold."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(DOMAINS))
    g_star = [next((r["g_star_gross_bps"] or np.nan) for r in cost_rows if r["domain"] == d) for d in DOMAINS]
    g_net = [next((r["g_star_net_bps"] or np.nan) for r in cost_rows if r["domain"] == d) for d in DOMAINS]
    l_gross = [next((r["lifetime_gross_bps"] or np.nan) for r in cost_rows if r["domain"] == d) for d in DOMAINS]
    l_net = [next((r["lifetime_net_bps"] or np.nan) for r in cost_rows if r["domain"] == d) for d in DOMAINS]
    ax.axhline(0.0, color="gray", lw=0.8)
    ax.bar(x - 0.3, g_star, width=0.2, color="steelblue", label="h* gross")
    ax.bar(x - 0.1, g_net, width=0.2, color="lightblue", label="h* net")
    ax.bar(x + 0.1, l_gross, width=0.2, color="darkorange", label="lifetime gross")
    ax.bar(x + 0.3, l_net, width=0.2, color="navajowhite", label="lifetime net")
    ax.set_xticks(x); ax.set_xticklabels(DOMAINS)
    ax.set_ylabel("return (bps)"); ax.set_title("Cost attribution (secondary lens)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Result-table builders
# --------------------------------------------------------------------------- #
def horizon_decay_rows(domain_results: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Flatten per-domain per-horizon curve, CI, p-values, and lifetime reference."""
    rows: list[dict[str, Any]] = []
    for domain in DOMAINS:
        res = domain_results[domain]
        for j, h in enumerate(HORIZON_GRID):
            rows.append({
                "domain": domain, "horizon": h,
                "g_all_bps": float(res["g_all"][j]), "n_all": int(res["n_all"][j]),
                "g_common_bps": float(res["g_common"][j]), "n_common": int(res["n_common"][j]),
                "ci_lo_bps": float(res["ci_lo"][j]), "ci_hi_bps": float(res["ci_hi"][j]),
                "p_raw": float(res["p_raw"][j]), "p_holm": float(res["p_holm"][j]),
                "g_life_bps": float(res["g_life"][j]),
                "loose_floor_bps": LOOSE_FLOOR_BPS[domain],
            })
    return rows


def fork_verdict_rows(domain_results: dict[str, dict[str, Any]], phase_verdict: str) -> list[dict[str, Any]]:
    """Per-domain fork verdict table plus the phase-level aggregation row."""
    rows: list[dict[str, Any]] = []
    for domain in DOMAINS:
        res = domain_results[domain]
        rows.append({
            "domain": domain, "verdict": res["verdict"], "h_star": res["h_star"],
            "g_star_bps": res["g_star"], "loose_floor_bps": res["floor_bps"],
            "p_holm_star": res["p_holm_star"], "ci_lo_star_bps": res["ci_lo_star"],
            "ci_hi_star_bps": res["ci_hi_star"], "g_life_star_bps": res["g_life_star"],
            "delta_star_bps": res["delta_star"], "margin_bps": res["margin_bps"],
            "n_star": res["n_star"],
        })
    rows.append({"domain": "PHASE", "verdict": phase_verdict, "h_star": None,
                 "g_star_bps": None, "loose_floor_bps": None, "p_holm_star": None,
                 "ci_lo_star_bps": None, "ci_hi_star_bps": None, "g_life_star_bps": None,
                 "delta_star_bps": None, "margin_bps": None, "n_star": None})
    return rows


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    """Run the EXP-024 dissipation decomposition and write results + plots."""
    configure_logging()
    ensure_output_dirs()
    started = datetime.now(timezone.utc)

    gate_ok, gate_reasons = check_dependency_gate()
    if not gate_ok:
        write_json(RESULTS_DIR / "run_metadata.json", {
            "experiment_id": EXPERIMENT_ID, "overall_status": "BLOCKED",
            "dependency_pass": False, "dependency_reasons": gate_reasons,
            "registry_refs": REGISTRY_REFS,
        })
        raise SystemExit(f"EXP-024 BLOCKED: dependency gate failed: {gate_reasons}")
    LOGGER.info("Dependency gate PASS (EXP-020 substrate, EXP-021/022 artifacts).")

    log_close, frames, metadata_rows = build_cell_log_close()
    metadata_check = validate_analysis_metadata(metadata_rows)
    events, join_diagnostics = load_event_table()

    # Holdout-safe join guard per (instrument, domain) cell.
    for (inst, domain), frame in frames.items():
        cell = events.filter((pl.col("instrument") == inst) & (pl.col("domain") == domain))
        if cell.height:
            validate_event_join(cell, frame, f"{inst}/{domain}")
    LOGGER.info("Event/domain join validated (holdout fence re-asserted).")

    domain_results: dict[str, dict[str, Any]] = {}
    for domain in tqdm(DOMAINS, desc="per-domain fork"):
        dom_events = events.filter(pl.col("domain") == domain)
        domain_results[domain] = evaluate_domain_fork(domain, dom_events, log_close)

    domain_verdicts = {d: domain_results[d]["verdict"] for d in DOMAINS}
    phase_verdict = phase_level_fork(domain_verdicts)

    # Result tables.
    write_rows(RESULTS_DIR / "domain_reconstruction_check.csv", metadata_check)
    write_rows(RESULTS_DIR / "event_join_diagnostics.csv", join_diagnostics)
    write_rows(RESULTS_DIR / "horizon_decay.csv", horizon_decay_rows(domain_results))
    write_rows(RESULTS_DIR / "bounded_vs_lifetime.csv", bounded_vs_lifetime_rows(domain_results))
    write_rows(RESULTS_DIR / "fork_verdict.csv", fork_verdict_rows(domain_results, phase_verdict))
    tc_rows = trend_change_rows(events)
    holding = holding_exposure_rows(events, frames)
    cost_rows = cost_attribution_rows(domain_results, events)
    cross = crosscheck_rows(events, domain_results, log_close)
    write_rows(RESULTS_DIR / "trend_change_returns.csv", tc_rows)
    write_rows(RESULTS_DIR / "holding_exposure.csv", holding)
    write_rows(RESULTS_DIR / "cost_attribution.csv", cost_rows)
    write_rows(RESULTS_DIR / "exp021_crosscheck.csv", cross)

    # Visualisations.
    plot_horizon_decay(domain_results, PLOTS_DIR / "horizon_decay.png")
    plot_outcome_holding(holding, PLOTS_DIR / "outcome_holding.png")
    plot_trend_change(tc_rows, PLOTS_DIR / "trend_change_returns.png")
    plot_cost_attribution(cost_rows, PLOTS_DIR / "cost_attribution.png")

    max_cross = max((r["abs_diff_bps"] for r in cross if r["abs_diff_bps"] is not None), default=None)
    write_json(RESULTS_DIR / "run_metadata.json", {
        "experiment_id": EXPERIMENT_ID, "title": "AVWAP Event-Edge Dissipation Decomposition",
        "overall_status": "COMPLETE", "diagnostic": True, "runs_frozen_suite": False,
        "dependency_pass": True, "primary_domain": PRIMARY_DOMAIN,
        "horizon_grid": list(HORIZON_GRID), "loose_floor_bps": LOOSE_FLOOR_BPS,
        "n_boot": N_BOOT, "domain_verdicts": domain_verdicts, "phase_verdict": phase_verdict,
        "event_join_row_count_preserved": all(r["row_count_preserved"] for r in join_diagnostics),
        "event_join_duplicate_rows_beyond_first": sum(
            r["event_duplicate_rows_beyond_first"] + r["lifetime_duplicate_rows_beyond_first"]
            for r in join_diagnostics
        ),
        "exp021_matched_crosscheck_max_abs_diff_bps": max_cross,
        "exp021_crosscheck_tolerance_bps": CROSSCHECK_TOL_BPS,
        "registry_refs": REGISTRY_REFS,
        "generated_utc": started.isoformat(), "completed_utc": datetime.now(timezone.utc).isoformat(),
    })

    LOGGER.info("Per-domain fork: %s", domain_verdicts)
    LOGGER.info("Phase-level fork: %s", phase_verdict)
    LOGGER.info("EXP-021 matched {1,3,6} cross-check max |diff|: %s bps", max_cross)
    LOGGER.info("EXP-024 COMPLETE. Results: %s", RESULTS_DIR)


if __name__ == "__main__":
    main()
