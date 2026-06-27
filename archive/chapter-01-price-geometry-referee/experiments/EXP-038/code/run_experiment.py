"""Experiment EXP-038: EURUSD-4h A1-Cell TEST-Stratum Temporal-Stability Subsample Check (one-shot).

Implements analysis-plan.md / scope.md (Phase 008, Tier B per design §8.4 as amended
F02; revised R1 2026-06-10, pre-execution — design §11). One-shot TEST-stratum
**temporal-stability subsample check** (R1.7 relabel: NOT an independent
out-of-sample confirmation — the TEST events are a dependent subsample of the data
that both selected the cell and produced the EXP-034 pass) of the EXP-034 EURUSD-4h
A1 strict pass: the SAME registered baseline estimand (BTC exit, pyramids included,
frozen CONSERVATIVE RT 3.0 bps + 0.6 bps/calendar-day adverse-side financing, frozen
EXP-027 regime-cluster bootstrap, pinned hash e50873d12a9f68d9), restricted to the
TEST stratum — events whose entry-confirmation (trigger) close time falls after the
last TRAIN 1-minute analysis bar (first 70% of the analysis set is TRAIN; membership
key is the causal trigger bar; ties go to TRAIN).

Provisional TEST rule (this run; R1.1/R1.2):
    A1_CELL_TEST_PASS_PROVISIONAL  iff  ci_low_1s > m AND boot_p <= 0.05
where m is the calibrated margin from the pre-TEST synthetic-null calibration
(R1.2: R=2000 zero-mean Gaussian cluster-model replicates on the TEST stratum's
entry-attribute cluster layout, dispersion from TRAIN-stratum nets; m = max(0, Q95
of null ci_low_1s); persisted BEFORE the TEST bootstrap). The FINAL binding verdict
applies the phase-level Holm family (this raw p + EXP-037's realized p's, <= 4
members) in the checkpoint's ``G2-gate-review.md`` — this script NEVER emits
``g2_satisfied``. A LOCO (leave-one-cluster-out) fragility diagnostic accompanies
the read (R1.7; never gates), and the R1.7 nomination precondition
(TRAIN-stratum net point > 0) is recorded for the operator.

Integrity guards (all hard-fail; orchestration order is load-bearing):
  1. TRAIN+TEST EURUSD-4h counts reconcile EXACTLY to the EXP-030/034 cell (39);
  2. the per-event net definition reproduces EXP-034 (full-cell mean <= 0.01 bps AND
     full-cell bootstrap with EXP-034's own seed reproduces its CI/p to <= 1e-6);
  3. frozen-tail hash pin verified;
  4. same-seed determinism replay of the TEST inference;
  5. the TEST partition (member event IDs) AND the calibration margin are written to
     disk BEFORE any TEST-stratum outcome statistic or bootstrap is computed;
  6. no-second-read (R1.6): an existing ``test_inference.csv`` hard-stops the run
     before inference; an existing ``test_partition.csv`` from an interrupted run
     must match the recomputed partition byte-identically.

The final 30% global holdout is never loaded (fence inside the lazy loader). No cost
or financing constant is revisited. Zero-baseline: absolute bps vs 0. The TEST stratum
is read once; no re-read after the verdict (LOCO/seed-robustness are part of the
single predeclared read).

Run:
    cd <project-root> && python python/experiments/EXP-038/code/run_experiment.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
import logging
import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402  (backend must be set first)
import numpy as np  # noqa: E402
import polars as pl  # noqa: E402
from tqdm.auto import tqdm  # noqa: E402

# --------------------------------------------------------------------------- #
# Path setup
# --------------------------------------------------------------------------- #
PROJECT_ROOT = Path(__file__).resolve().parents[4]

from xen.financing import elapsed_calendar_days, financing_bps, verify_financing  # noqa: E402
from xen.referee_calibration import (  # noqa: E402
    build_domain_frames,
    list_timebar_files,
    load_analysis_data,
    seed_for,
)

# Frozen EXP-027 inference tail — imported directly from the canonical file.
EXP027_METHOD = PROJECT_ROOT / "python" / "experiments" / "EXP-027" / "code" / "event_method.py"


def _load_module(name: str, path: Path):
    """Import a module by file path without executing any ``main`` guard."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


EM = _load_module("exp027_event_method", EXP027_METHOD)
from exp027_event_method import (  # noqa: E402
    bootstrap_effect_distribution,
    build_strata,
    domain_effect,
)

LOGGER = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-038"
DATA_DIR = PROJECT_ROOT / "data"
EXP_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"

EXP020_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-020" / "results"
EXP022_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-022" / "results"
EXP030_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-030" / "results"
EXP034_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-034" / "results"

# Single declared cell (scope: EURUSD-4h only).
INSTRUMENT = "EURUSD"
DOMAIN = "4h"
EXPECTED_N_FULL = 39  # EXP-030/034 reconciled EURUSD-4h population; drift = hard stop.

# FROZEN cost layer (identical to EXP-034; never revisited).
RT_CONS_BPS = 3.0                    # EURUSD CONSERVATIVE round-trip, bps
FINANCING_RATE_BPS_PER_DAY = 0.6     # EURUSD adverse-side, bps per calendar day

# EXP-028 PRIMARY population construction (identical to EXP-030/034).
COMPLETED_OUTCOMES = ("favorable", "adverse", "trend_change")
JOIN_KEYS = ("instrument", "domain", "regime_id", "direction", "event_trigger_idx")
MIN_CONTROLS = EM.MIN_CONTROLS

# Inference convention (identical to EXP-030/034).
N_BOOT = 1000
CHUNK = 200
ALPHA = 0.05
CI_PERCENTILES = (2.5, 97.5)
N_SEEDS_ROBUST = 8

# R1.2 null calibration (synthetic data only; persisted before the TEST read).
N_NULL_CAL = 2000
MARGIN_QUANTILE = 95.0

# Tolerances.
RECON_NET_TOL_BPS = 0.01     # full-cell net mean vs EXP-034 effect_bps
RECON_CI_TOL = 1e-6          # full-cell bootstrap (EXP-034 seed) vs EXP-034 CI/p
START_CLOSE_RTOL = 1e-9      # start_close vs rebuilt base bar
DETERMINISM_TOL = 1e-12

# Frozen inference functions + pinned hash (same tail and pin as EXP-030/031/034).
FROZEN_FUNCTIONS: tuple[str, ...] = (
    "domain_effect", "build_strata", "bootstrap_effect_distribution",
    "holm_adjust", "decide_label",
)
FROZEN_TAIL_EXPECTED_HASH = "e50873d12a9f68d9"

# Partition columns persisted before any TEST outcome statistic (guard 5).
PARTITION_COLUMNS: tuple[str, ...] = (
    "instrument", "domain", "regime_id", "direction", "event_trigger_idx",
    "is_pyramid_bounce", "trigger_close_time", "stratum",
)


# --------------------------------------------------------------------------- #
# I/O helpers
# --------------------------------------------------------------------------- #
def configure_logging() -> None:
    """Configure concise INFO logging for the manual run."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                        datefmt="%H:%M:%S")


def ensure_output_dirs() -> None:
    """Create ``results/`` and ``plots/`` (orchestration-time only)."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> dict[str, Any]:
    """Read a JSON metadata file (raises if absent)."""
    if not path.exists():
        raise FileNotFoundError(f"missing run metadata: {path}")
    return json.loads(path.read_text())


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write dict rows to CSV (empty-safe)."""
    if not rows:
        path.write_text("")
        return
    pl.DataFrame(rows).write_csv(path)


def ensure_bool(frame: pl.DataFrame, columns: tuple[str, ...]) -> pl.DataFrame:
    """Cast CSV-loaded ``true``/``false`` columns to Boolean (Polars may infer Utf8)."""
    exprs = []
    for col in columns:
        if col not in frame.columns:
            continue
        if frame.schema[col] == pl.Utf8:
            exprs.append((pl.col(col).str.to_lowercase() == "true").alias(col))
        else:
            exprs.append(pl.col(col).cast(pl.Boolean))
    return frame.with_columns(exprs) if exprs else frame


# --------------------------------------------------------------------------- #
# Integrity guards: frozen tail, dependencies, EXP-034 reference row
# --------------------------------------------------------------------------- #
def verify_frozen_inference() -> str:
    """Assert the imported inference tail matches the PINNED EXP-027 source hash."""
    used_src = []
    for name in FROZEN_FUNCTIONS:
        used_fn = getattr(EM, name, None)
        if used_fn is None:
            raise ValueError(f"FROZEN_INFERENCE_MODIFIED: function {name} missing")
        used_src.append(inspect.getsource(used_fn))
    h_used = hashlib.sha256("".join(used_src).encode()).hexdigest()[:16]
    if h_used != FROZEN_TAIL_EXPECTED_HASH:
        raise ValueError(
            f"FROZEN_INFERENCE_MODIFIED: inference tail diverges from the pinned "
            f"EXP-027 source (got {h_used} != pinned {FROZEN_TAIL_EXPECTED_HASH})."
        )
    LOGGER.info("Frozen inference tail verified against pinned EXP-027 hash (%s)", h_used)
    return h_used


def check_dependencies() -> dict[str, Any]:
    """Assert the EXP-034 A1 strict pass (this experiment's mandate) and artifacts."""
    exp034 = load_json(EXP034_RESULTS / "run_metadata.json")
    if not bool(exp034.get("a1_strict_pass", False)):
        raise ValueError("EXP-034 a1_strict_pass must be true — EXP-038 has no mandate")
    verdict = str(exp034.get("sequence_verdicts", {}).get(f"{INSTRUMENT}/{DOMAIN}", ""))
    if verdict != "SEQUENCE_PASS_ALPHA05":
        raise ValueError(f"EXP-034 {INSTRUMENT}/{DOMAIN} verdict must be "
                         f"SEQUENCE_PASS_ALPHA05, got {verdict!r}")
    for artifact in (EXP022_RESULTS / "lifetime_observations.csv",
                     EXP034_RESULTS / "cell_inference.csv",
                     EXP020_RESULTS / "analysis_metadata.csv"):
        if not artifact.exists():
            raise FileNotFoundError(f"missing dependency artifact: {artifact}")
    LOGGER.info("Dependency gate PASS (EXP-034 %s/%s = %s)", INSTRUMENT, DOMAIN, verdict)
    return {"EXP-034_verdict": verdict, "EXP-034_a1_strict_pass": True}


def load_exp034_reference() -> dict[str, float]:
    """Return EXP-034's EURUSD-4h binding inference row (the reconciliation target)."""
    cells = pl.read_csv(EXP034_RESULTS / "cell_inference.csv")
    row = cells.filter((pl.col("instrument") == INSTRUMENT) & (pl.col("domain") == DOMAIN))
    if row.height != 1:
        raise ValueError(f"expected 1 EXP-034 row for {INSTRUMENT}/{DOMAIN}, got {row.height}")
    ref = row.to_dicts()[0]
    return {key: float(ref[key])
            for key in ("n_events", "effect_bps", "ci_low", "ci_high", "ci_low_1s", "boot_p")}


# --------------------------------------------------------------------------- #
# Domain rebuild (EURUSD only) + holdout-safe metadata guard
# --------------------------------------------------------------------------- #
def build_eurusd_series() -> dict[str, Any]:
    """Rebuild the first-70% EURUSD 4h domain bars and the TRAIN/TEST boundary.

    Same loader/fence as EXP-020/022/031/034 (``xen.referee_calibration``), so 4h
    domain-bar indices align with ``start_idx``/``completion_idx`` by construction.
    The boundary is the loader's ``train_end_ts`` — the CloseTime of the LAST TRAIN
    1-minute analysis row (``train_rows = int(analysis_rows * 0.7)``), matching the
    scope's predeclared rule: TEST iff trigger close time > boundary (ties = TRAIN).
    """
    expected = pl.read_csv(EXP020_RESULTS / "analysis_metadata.csv")
    exp_rows = expected.filter((pl.col("instrument") == INSTRUMENT)
                               & (pl.col("domain") == DOMAIN))
    if exp_rows.height != 1:
        raise ValueError(f"EXP-020 metadata must have 1 {INSTRUMENT}/{DOMAIN} row, "
                         f"got {exp_rows.height}")
    exp = exp_rows.to_dicts()[0]
    files = [p for p in list_timebar_files(DATA_DIR) if p.name == str(exp["source_file"])]
    if len(files) != 1:
        raise FileNotFoundError(f"EXP-020 source file not found: {exp['source_file']}")
    data = load_analysis_data(files[0])
    frame = build_domain_frames(data.frame)[DOMAIN]
    checks = {
        "source_file_match": data.source_file == exp["source_file"],
        "analysis_rows_1m_match": int(data.analysis_rows) == int(exp["analysis_rows_1m"]),
        "domain_bars_match": int(frame.height) == int(exp["domain_bars"]),
        "domain_max_close_time_match":
            str(frame.get_column("CloseTime").max()) == str(exp["domain_max_close_time"]),
    }
    if not all(checks.values()):
        raise ValueError(f"EXP-020 analysis metadata mismatch (rebuild diverged): {checks}")
    LOGGER.info("Domain rebuild matches EXP-020 metadata; TRAIN/TEST boundary = %s "
                "(last TRAIN 1m close; train_rows=%d of %d analysis rows)",
                data.train_end_ts, data.train_rows, data.analysis_rows)
    return {
        "close": frame.get_column("Close").to_numpy().astype(float),
        "close_time": frame.get_column("CloseTime").to_numpy().astype("datetime64[ns]"),
        "boundary_time": np.datetime64(data.train_end_ts, "ns"),
        "rebuild_checks": checks,
        "analysis_rows_1m": int(data.analysis_rows),
        "train_rows_1m": int(data.train_rows),
        "source_file": data.source_file,
    }


# --------------------------------------------------------------------------- #
# Event table (EXP-030/034 construction, EURUSD-4h) + cost/financing overlay
# --------------------------------------------------------------------------- #
def build_event_table(lifetime: pl.DataFrame) -> pl.DataFrame:
    """EXP-028/030/034 PRIMARY event set restricted to EURUSD-4h.

    Identical filtering to EXP-034 ``build_event_table`` (completed reportable
    events with >= MIN_CONTROLS finite controls), then the scope's single-cell
    restriction. No deduplication anywhere.
    """
    lifetime = ensure_bool(lifetime, ("reportable_event", "is_pyramid_bounce"))
    lt = lifetime.filter(pl.col("outcome").is_in(COMPLETED_OUTCOMES)
                         & pl.col("lifetime_bps").is_not_null())
    keys = list(JOIN_KEYS)
    events = lt.filter((pl.col("role") == "event") & pl.col("reportable_event"))
    controls = lt.filter(pl.col("role") == "control")
    ctrl_mean = controls.group_by(keys).agg(pl.len().alias("n_controls_finite"))
    merged = events.join(ctrl_mean, on=keys, how="inner")
    merged = merged.filter(pl.col("n_controls_finite") >= MIN_CONTROLS)
    out = merged.filter((pl.col("instrument") == INSTRUMENT)
                        & (pl.col("domain") == DOMAIN)).select(
        "instrument", "domain", "regime_id", "direction", "event_trigger_idx",
        "is_pyramid_bounce", "start_idx", "completion_idx", "start_close",
        "lifetime_bps", "n_controls_finite",
    )
    LOGGER.info("Event set: %d %s/%s rows (EXP-028 PRIMARY population)",
                out.height, INSTRUMENT, DOMAIN)
    return out


def attach_costs_and_financing(table: pl.DataFrame, series: dict[str, Any]) -> pl.DataFrame:
    """Attach trigger/exit timestamps, RT + financing costs, and the net column.

    Per event: trigger = CloseTime[start_idx], exit = CloseTime[completion_idx] on
    the rebuilt 4h series (fractional calendar days, weekends included). Hard-fails
    on out-of-range indices or ``start_close`` mismatch vs the rebuilt base bar.
    """
    si = table.get_column("start_idx").to_numpy().astype(np.int64)
    ci = table.get_column("completion_idx").to_numpy().astype(np.int64)
    sc = table.get_column("start_close").to_numpy().astype(float)
    close, ct = series["close"], series["close_time"]
    if (si < 0).any() or (si >= close.size).any() or (ci < 0).any() or (ci >= close.size).any():
        raise ValueError(f"index out of analysis-slice range for {INSTRUMENT}/{DOMAIN}")
    base_bad = int(np.sum(np.abs(close[si] - sc) > START_CLOSE_RTOL * sc))
    if base_bad:
        raise ValueError(f"start_close mismatch vs rebuilt base bar in {base_bad} rows")
    trigger_dt, exit_dt = ct[si], ct[ci]
    if np.isnat(trigger_dt).any() or np.isnat(exit_dt).any():
        raise ValueError("unresolved trigger/exit timestamps (NaT)")
    rates = np.full(table.height, FINANCING_RATE_BPS_PER_DAY, dtype=float)
    holding_days = elapsed_calendar_days(trigger_dt, exit_dt)
    fin = financing_bps(rates, trigger_dt, exit_dt)
    out = table.with_columns([
        pl.Series("trigger_close_time", trigger_dt),
        pl.Series("holding_days", holding_days),
        pl.Series("financing_bps", fin),
    ]).with_columns(
        (pl.col("lifetime_bps") - RT_CONS_BPS - pl.col("financing_bps")).alias("net"),
    )
    if out.get_column("net").null_count() or out.get_column("net").is_nan().any():
        raise ValueError("NaN/null net values — hard stop, never silently dropped")
    LOGGER.info("Cost + financing overlay attached (%d rows)", out.height)
    return out


# --------------------------------------------------------------------------- #
# Pure computation: single-cell frozen-tail inference (absolute estimand)
# --------------------------------------------------------------------------- #
def infer_cell(sub: pl.DataFrame, rng: np.random.Generator) -> dict[str, Any]:
    """Effect, regime-cluster bootstrap CIs, and one-sided bootstrap p for a subset.

    Single-instrument specialization of the frozen tail, verbatim EXP-034
    ``infer_single_cell``: ``domain_effect`` with one instrument is the
    event-weighted mean; strata are direction strata with regime clusters as
    resampling units. ``ci_low_1s`` (5th bootstrap percentile) and ``boot_p``
    ``(1 + #{boot <= 0}) / (1 + N_BOOT)`` form the BINDING one-sided alpha = 0.05
    rule; the two-sided 95% CI drives the descriptive label only.
    """
    if sub.height == 0:
        raise ValueError("empty event subset — cannot run inference")
    diffs = sub.get_column("net").to_numpy().astype(float)
    inst_labels = sub.get_column("instrument").to_numpy()
    dir_labels = sub.get_column("direction").to_numpy().astype(int)
    regime_labels = sub.get_column("regime_id").to_numpy().astype(int)
    effect = domain_effect(diffs, inst_labels, [INSTRUMENT])
    strata = build_strata(diffs, inst_labels, dir_labels, regime_labels, [INSTRUMENT])
    boot = bootstrap_effect_distribution(strata, [INSTRUMENT], rng, N_BOOT, CHUNK)
    return {
        "n_events": sub.height,
        "n_bull": sub.filter(pl.col("direction") == 1).height,
        "n_bear": sub.filter(pl.col("direction") == -1).height,
        "n_regimes": sub.get_column("regime_id").n_unique(),
        "effect_bps": effect,
        "ci_low": float(np.percentile(boot, CI_PERCENTILES[0])),
        "ci_high": float(np.percentile(boot, CI_PERCENTILES[1])),
        "ci_low_1s": float(np.percentile(boot, 100.0 * ALPHA)),
        "boot_p": float((1 + int(np.sum(boot <= 0.0))) / (1 + N_BOOT)),
    }


def reconcile_vs_exp034(table: pl.DataFrame, ref: dict[str, float]) -> list[dict[str, Any]]:
    """Guards 1-2: exact count + per-event net definition reproduces EXP-034.

    (a) the full-cell population is EXACTLY ``EXPECTED_N_FULL``; (b) the full-cell
    event-weighted net mean matches EXP-034 ``effect_bps`` to <= 0.01 bps; (c) the
    full-cell bootstrap re-run with EXP-034's OWN seed payload
    (``seed_for("EXP-034", "cell", domain, instrument)``) reproduces its
    ``ci_low/ci_high/ci_low_1s/boot_p`` to <= 1e-6 — pinning the whole estimator
    construction, not just the point. Hard-fail on any miss.
    """
    count_ok = table.height == EXPECTED_N_FULL and int(ref["n_events"]) == EXPECTED_N_FULL
    net_mean = float(table.get_column("net").mean())
    net_dev = abs(net_mean - ref["effect_bps"])
    rng = np.random.default_rng(seed_for("EXP-034", "cell", DOMAIN, INSTRUMENT))
    replay = infer_cell(table, rng)
    ci_dev = max(abs(replay[k] - ref[k]) for k in ("ci_low", "ci_high", "ci_low_1s", "boot_p"))
    rows = [
        {"guard": "G-count_full_cell", "value": table.height,
         "expected": EXPECTED_N_FULL, "deviation": abs(table.height - EXPECTED_N_FULL),
         "tolerance": 0, "passed": bool(count_ok)},
        {"guard": "G-net_full_cell_mean_bps", "value": net_mean,
         "expected": ref["effect_bps"], "deviation": net_dev,
         "tolerance": RECON_NET_TOL_BPS, "passed": bool(net_dev <= RECON_NET_TOL_BPS)},
        {"guard": "G-net_full_cell_ci_replay", "value": replay["ci_low_1s"],
         "expected": ref["ci_low_1s"], "deviation": ci_dev,
         "tolerance": RECON_CI_TOL, "passed": bool(ci_dev <= RECON_CI_TOL)},
    ]
    failures = [r["guard"] for r in rows if not r["passed"]]
    if failures:
        raise ValueError(f"EXP-034 RECONCILIATION FAILED: {failures}")
    LOGGER.info("Reconciliation PASS: count=%d exact; net dev=%.4g bps; CI replay dev=%.3g",
                table.height, net_dev, ci_dev)
    return rows


# --------------------------------------------------------------------------- #
# Trigger-time TRAIN/TEST partition (the single new computation)
# --------------------------------------------------------------------------- #
def partition_by_trigger_time(table: pl.DataFrame,
                              boundary_time: np.datetime64) -> pl.DataFrame:
    """Label every event TRAIN or TEST by its causal trigger close time.

    TEST iff ``trigger_close_time > boundary_time`` (the last TRAIN 1-minute
    analysis bar close); ties go to TRAIN — the scope's predeclared rule. The
    labeling is total and disjoint by construction; counts are re-asserted against
    the full-cell population (no dropped/duplicated events).
    """
    out = table.with_columns(
        pl.when(pl.col("trigger_close_time") > boundary_time)
        .then(pl.lit("TEST")).otherwise(pl.lit("TRAIN")).alias("stratum")
    )
    n_test = out.filter(pl.col("stratum") == "TEST").height
    n_train = out.filter(pl.col("stratum") == "TRAIN").height
    if n_train + n_test != EXPECTED_N_FULL:
        raise ValueError(f"partition not total/disjoint: {n_train}+{n_test} != "
                         f"{EXPECTED_N_FULL}")
    if n_test == 0:
        raise ValueError("TEST stratum is empty — cannot run the confirmation")
    LOGGER.info("Partition: TRAIN=%d, TEST=%d (boundary %s, ties->TRAIN)",
                n_train, n_test, boundary_time)
    return out


def stratum_summary(sub: pl.DataFrame, label: str,
                    inference: dict[str, Any] | None) -> dict[str, Any]:
    """Descriptive per-stratum row (gross/financing/net, holding-day quartiles)."""
    hd = sub.get_column("holding_days").to_numpy()
    row: dict[str, Any] = {
        "stratum": label, "n_events": sub.height,
        "n_pyramid": sub.filter(pl.col("is_pyramid_bounce")).height,
        "gross_mean_bps": float(sub.get_column("lifetime_bps").mean()),
        "mean_financing_bps": float(sub.get_column("financing_bps").mean()),
        "net_mean_bps": float(sub.get_column("net").mean()),
        "median_holding_days": float(np.median(hd)),
        "p25_holding_days": float(np.percentile(hd, 25)),
        "p75_holding_days": float(np.percentile(hd, 75)),
    }
    if inference is not None:
        row.update({k: inference[k] for k in
                    ("effect_bps", "ci_low", "ci_high", "ci_low_1s", "boot_p", "n_regimes")})
    return row


# --------------------------------------------------------------------------- #
# R1.2 null calibration + R1.7 LOCO diagnostic (frozen-family machinery)
# --------------------------------------------------------------------------- #
def estimate_variance_components(values: np.ndarray, clusters: np.ndarray) -> tuple[float, float]:
    """Method-of-moments (sigma_b, sigma_w) from demeaned TRAIN nets and cluster labels.

    sigma_w^2 = pooled within-cluster variance over clusters with >= 2 events
    (fallback: total variance if none); sigma_b^2 = max(0, var(cluster means) -
    sigma_w^2 * mean(1/n_c)). Predeclared in analysis-plan Step 2b.
    """
    demeaned = values - values.mean()
    uniq = np.unique(clusters)
    sizes = np.array([np.sum(clusters == u) for u in uniq], dtype=float)
    means = np.array([demeaned[clusters == u].mean() for u in uniq])
    multi = sizes >= 2
    if multi.any():
        ss = sum(float(np.sum((demeaned[clusters == u] - demeaned[clusters == u].mean()) ** 2))
                 for u in uniq[multi])
        dof = float(np.sum(sizes[multi] - 1))
        var_w = ss / dof if dof > 0 else float(np.var(demeaned, ddof=1))
    else:
        var_w = float(np.var(demeaned, ddof=1))
    var_means = float(np.var(means, ddof=1)) if uniq.size >= 2 else 0.0
    var_b = max(0.0, var_means - var_w * float(np.mean(1.0 / sizes)))
    return float(np.sqrt(var_b)), float(np.sqrt(var_w))


def null_calibration(train_sub: pl.DataFrame,
                     test_sub: pl.DataFrame) -> tuple[list[dict[str, Any]], float]:
    """R1.2: synthetic-null calibration of the frozen bootstrap at the TEST structure.

    Uses TEST **entry attributes** only (direction, regime-cluster sizes) and
    TRAIN-stratum dispersion (mechanical method-of-moments components). Draws
    ``N_NULL_CAL`` zero-mean Gaussian cluster-model replicates, scores each with the
    frozen 1000-resample bootstrap, and returns the disclosure row plus the binding
    margin ``m = max(0, Q95 of null ci_low_1s)``. No TEST outcome is touched.
    """
    if train_sub.height < 2 or test_sub.height == 0:
        raise ValueError(f"null calibration infeasible (train n={train_sub.height}, "
                         f"test n={test_sub.height})")
    tr_clusters = (train_sub.get_column("direction").cast(pl.Int64) * 1_000_000
                   + train_sub.get_column("regime_id").cast(pl.Int64)).to_numpy()
    sigma_b, sigma_w = estimate_variance_components(
        train_sub.get_column("net").to_numpy().astype(float), tr_clusters)
    layout = (test_sub.group_by(["direction", "regime_id"]).agg(pl.len().alias("n"))
              .sort(["direction", "regime_id"]).to_dicts())
    dir_labels = np.concatenate([np.full(r["n"], int(r["direction"]), dtype=int)
                                 for r in layout])
    regime_labels = np.concatenate([np.full(r["n"], j, dtype=int)
                                    for j, r in enumerate(layout)])
    inst_labels = np.full(dir_labels.size, INSTRUMENT)
    rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "nullcal", DOMAIN, INSTRUMENT))
    ci_lows = np.empty(N_NULL_CAL)
    boot_ps = np.empty(N_NULL_CAL)
    for k in tqdm(range(N_NULL_CAL), desc="null calibration"):
        cluster_fx = rng.normal(0.0, sigma_b, size=len(layout))
        diffs = cluster_fx[regime_labels] + rng.normal(0.0, sigma_w, size=dir_labels.size)
        strata = build_strata(diffs, inst_labels, dir_labels, regime_labels, [INSTRUMENT])
        boot = bootstrap_effect_distribution(strata, [INSTRUMENT], rng, N_BOOT, CHUNK)
        ci_lows[k] = np.percentile(boot, 100.0 * ALPHA)
        boot_ps[k] = (1 + int(np.sum(boot <= 0.0))) / (1 + N_BOOT)
    margin = max(0.0, float(np.percentile(ci_lows, MARGIN_QUANTILE)))
    fpr_raw = float(np.mean((boot_ps <= ALPHA) & (ci_lows > 0.0)))
    fpr_margin = float(np.mean((boot_ps <= ALPHA) & (ci_lows > margin)))
    rows = [{
        "instrument": INSTRUMENT, "domain": DOMAIN,
        "n_test_events": test_sub.height, "n_test_clusters": len(layout),
        "n_train_events": train_sub.height, "sigma_b_bps": sigma_b,
        "sigma_w_bps": sigma_w, "n_null_replicates": N_NULL_CAL,
        "fpr_uncorrected": fpr_raw, "margin_bps": margin,
        "fpr_with_margin": fpr_margin,
    }]
    LOGGER.info("Null calibration: FPR(raw)=%.4f -> margin=%.3f bps "
                "(FPR with margin=%.4f)", fpr_raw, margin, fpr_margin)
    return rows, margin


def loco_diagnostic(test_sub: pl.DataFrame, margin: float) -> list[dict[str, Any]]:
    """R1.7 leave-one-cluster-out fragility diagnostic (accompanies, never gates).

    Drops each distinct TEST (direction, regime_id) cluster, re-runs the frozen
    bootstrap on the remaining events with a deterministic per-drop seed, and
    discloses whether the margin-adjusted bound survives every removal.
    """
    clusters = (test_sub.select(["direction", "regime_id"]).unique()
                .sort(["direction", "regime_id"]).to_dicts())
    rows: list[dict[str, Any]] = []
    for k, c in enumerate(tqdm(clusters, desc="LOCO")):
        sub = test_sub.filter(~((pl.col("direction") == c["direction"])
                                & (pl.col("regime_id") == c["regime_id"])))
        if sub.height == 0:
            rows.append({"drop_direction": c["direction"], "drop_regime_id": c["regime_id"],
                         "n_remaining": 0, "effect_bps": None, "ci_low_1s": None,
                         "above_margin": None, "note": "degenerate: single cluster"})
            continue
        res = infer_cell(sub, np.random.default_rng(
            seed_for(EXPERIMENT_ID, "loco", DOMAIN, INSTRUMENT, k)))
        rows.append({"drop_direction": c["direction"], "drop_regime_id": c["regime_id"],
                     "n_remaining": sub.height, "effect_bps": res["effect_bps"],
                     "ci_low_1s": res["ci_low_1s"],
                     "above_margin": bool(res["ci_low_1s"] > margin), "note": None})
    return rows


# --------------------------------------------------------------------------- #
# Verdict, determinism, and seed robustness
# --------------------------------------------------------------------------- #
def decide_verdict(res: dict[str, Any], margin: float) -> dict[str, Any]:
    """Apply the provisional one-shot TEST rule and the descriptive label.

    PROVISIONAL (R1.1/R1.2): ``ci_low_1s > margin AND boot_p <= ALPHA`` ->
    ``A1_CELL_TEST_PASS_PROVISIONAL``; the final binding verdict applies the
    phase-level Holm family in ``G2-gate-review.md``. Otherwise the two-sided
    descriptive label, recorded as ``A1_STRICT_PASS_TEST_CONFIRMATION_FAILED``
    for phase bookkeeping.
    """
    provisional = bool(res["boot_p"] <= ALPHA and res["ci_low_1s"] > margin)
    if res["ci_low"] > 0.0:
        descriptive = "EVIDENCE_FOR"
    elif res["ci_high"] < 0.0:
        descriptive = "EVIDENCE_AGAINST"
    else:
        descriptive = "INCONCLUSIVE_SPANS_ZERO"
    return {
        "binding_pass_provisional": provisional,
        "margin_bps": margin,
        "verdict": "A1_CELL_TEST_PASS_PROVISIONAL" if provisional else descriptive,
        "descriptive_label": descriptive,
        "phase_outcome": ("A1_CELL_TEST_PASS_PROVISIONAL_PENDING_PHASE_HOLM"
                          if provisional
                          else "A1_STRICT_PASS_TEST_CONFIRMATION_FAILED"),
        "g2_adjudication": "PENDING_PHASE_FAMILY_HOLM (G2-gate-review.md)",
    }


def determinism_replay(test_sub: pl.DataFrame, ref: dict[str, Any]) -> dict[str, Any]:
    """Guard 4: re-run the TEST inference with its own seed; assert exact identity."""
    rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "test", DOMAIN, INSTRUMENT))
    replay = infer_cell(test_sub, rng)
    max_drift = max(abs(replay[k] - ref[k])
                    for k in ("effect_bps", "ci_low", "ci_high", "ci_low_1s", "boot_p"))
    result = {"cell": f"{INSTRUMENT}/{DOMAIN}/TEST", "max_drift": max_drift,
              "passed": bool(max_drift <= DETERMINISM_TOL)}
    if not result["passed"]:
        raise ValueError(f"DETERMINISM REPLAY FAILED: {result}")
    LOGGER.info("Determinism replay PASS (max drift %.3g)", max_drift)
    return result


def seed_robustness(test_sub: pl.DataFrame) -> list[dict[str, Any]]:
    """CI-boundary stability across N_SEEDS_ROBUST seeds for the TEST stratum.

    Standing EXP-030/034 disclosure practice, computed in the same run (no re-read
    after the verdict); disclosure only — the binding verdict uses the primary seed.
    """
    lows, highs, lows_1s = [], [], []
    for k in tqdm(range(N_SEEDS_ROBUST), desc="seed robustness"):
        rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "robust", DOMAIN, INSTRUMENT, k))
        res = infer_cell(test_sub, rng)
        lows.append(res["ci_low"])
        highs.append(res["ci_high"])
        lows_1s.append(res["ci_low_1s"])
    return [{
        "stratum": "TEST", "n_seeds": N_SEEDS_ROBUST,
        "ci_low_min": min(lows), "ci_low_max": max(lows),
        "ci_high_min": min(highs), "ci_high_max": max(highs),
        "ci_low_1s_min": min(lows_1s), "ci_low_1s_max": max(lows_1s),
        "ci_low_sign_stable": bool(all(v > 0 for v in lows) or all(v <= 0 for v in lows)),
        "ci_low_1s_sign_stable": bool(all(v > 0 for v in lows_1s)
                                      or all(v <= 0 for v in lows_1s)),
    }]


# --------------------------------------------------------------------------- #
# Plotting (2)
# --------------------------------------------------------------------------- #
def plot_test_distribution(test_sub: pl.DataFrame, res: dict[str, Any],
                           verdict: dict[str, Any], path: Path) -> None:
    """TEST-stratum per-event net dots with mean, 95% CI, and 1s lower bound vs 0."""
    nets = test_sub.get_column("net").to_numpy()
    pyramid = test_sub.get_column("is_pyramid_bounce").to_numpy()
    rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "plot_jitter"))
    x = rng.uniform(-0.12, 0.12, size=nets.size)
    fig, ax = plt.subplots(figsize=(7, 5.5))
    for mask, marker, label in ((~pyramid, "o", "base leg"), (pyramid, "^", "pyramid leg")):
        if mask.any():
            ax.scatter(x[mask], nets[mask], marker=marker, s=55, alpha=0.85,
                       color="#34495e", label=label)
    ax.errorbar(0.4, res["effect_bps"],
                yerr=[[res["effect_bps"] - res["ci_low"]],
                      [res["ci_high"] - res["effect_bps"]]],
                fmt="D", capsize=6,
                color="#2e7d32" if verdict["binding_pass_provisional"] else "#7f8c8d",
                markersize=9, label="TEST mean (2-sided 95% CI)")
    ax.scatter(0.4, res["ci_low_1s"], marker="_", s=300, color="#c0392b",
               label="one-sided 95% lower bound (BINDING)")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xlim(-0.3, 0.7)
    ax.set_xticks([])
    ax.set_ylabel("Per-event net (bps; CONS RT + financing)")
    ax.set_title(f"EXP-038 TEST stratum — {INSTRUMENT}-{DOMAIN} one-shot read\n"
                 f"n={res['n_events']}, p={res['boot_p']:.3f} -> {verdict['verdict']}")
    ax.legend(fontsize=8, loc="best")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_stratum_comparison(rows: list[dict[str, Any]], verdict: dict[str, Any],
                            path: Path) -> None:
    """Full-analysis vs TRAIN vs TEST net point + 95% CI vs zero (transparency)."""
    fig, ax = plt.subplots(figsize=(7.5, 5))
    for k, row in enumerate(rows):
        binding = row["stratum"] == "TEST"
        color = ("#2e7d32" if verdict["binding_pass_provisional"]
                 else "#c0392b") if binding else "#7f8c8d"
        ax.errorbar(k, row["effect_bps"],
                    yerr=[[row["effect_bps"] - row["ci_low"]],
                          [row["ci_high"] - row["effect_bps"]]],
                    fmt="o", capsize=5, color=color, markersize=9 if binding else 7)
        tag = "BINDING" if binding else "NON-BINDING"
        ax.annotate(f"n={row['n_events']}\n{tag}", (k, row["ci_high"]),
                    textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(range(len(rows)))
    ax.set_xticklabels([r["stratum"] for r in rows])
    ax.set_ylabel("Net per-event expectancy (bps)")
    ax.set_title(f"EXP-038 {INSTRUMENT}-{DOMAIN}: full vs TRAIN vs TEST "
                 f"(TRAIN/FULL are NON-BINDING transparency)")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    """Run the EXP-038 one-shot TEST-stratum confirmation end to end.

    Order is load-bearing (guard 5): integrity guards -> partition persisted to
    disk -> TEST inference. No TEST-stratum outcome statistic is computed before
    ``test_partition.csv`` is written.
    """
    configure_logging()
    ensure_output_dirs()
    LOGGER.info("=== %s: %s-%s A1-cell TEST-stratum confirmation (one-shot) ===",
                EXPERIMENT_ID, INSTRUMENT, DOMAIN)

    # ---- guards (pre-partition) ----------------------------------------------
    frozen_hash = verify_frozen_inference()                       # guard 3
    verify_financing()
    LOGGER.info("Financing helper self-check PASS")
    deps = check_dependencies()
    ref034 = load_exp034_reference()

    series = build_eurusd_series()
    lifetime = pl.read_csv(EXP022_RESULTS / "lifetime_observations.csv")
    table = build_event_table(lifetime)
    table = attach_costs_and_financing(table, series)
    recon_rows = reconcile_vs_exp034(table, ref034)               # guards 1-2

    # ---- partition persisted BEFORE any TEST outcome statistic (guard 5) -----
    table = partition_by_trigger_time(table, series["boundary_time"])
    partition = table.select(list(PARTITION_COLUMNS)).sort("trigger_close_time")
    partition_path = RESULTS_DIR / "test_partition.csv"
    partition_text = partition.write_csv()
    if partition_path.exists():
        # R1.6 recovery: a rerun after a post-partition crash must reproduce the
        # persisted partition exactly; mismatch is a hard stop.
        if partition_path.read_text() != partition_text:
            raise ValueError("PARTITION MISMATCH: existing test_partition.csv does "
                             "not reproduce under rerun — hard stop (R1.6)")
        LOGGER.info("Partition already on disk and byte-matched — rerun resume (R1.6)")
    else:
        partition_path.write_text(partition_text)
        LOGGER.info("TEST partition persisted to %s", partition_path)

    test_sub = table.filter(pl.col("stratum") == "TEST")
    train_sub = table.filter(pl.col("stratum") == "TRAIN")

    # ---- R1.2 null calibration persisted BEFORE the TEST bootstrap -------------
    # (TRAIN dispersion + TEST entry attributes only; no TEST outcome statistic.)
    calibration_rows, margin = null_calibration(train_sub, test_sub)
    write_rows(RESULTS_DIR / "null_calibration.csv", calibration_rows)

    # ---- one-shot TEST inference (R1.6 no-second-read guard) -------------------
    if (RESULTS_DIR / "test_inference.csv").exists():
        raise ValueError("NO-SECOND-READ: test_inference.csv already exists — the "
                         "TEST stratum has been read; refusing to recompute (R1.6)")
    rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "test", DOMAIN, INSTRUMENT))
    test_res = infer_cell(test_sub, rng)
    verdict = decide_verdict(test_res, margin)
    replay = determinism_replay(test_sub, test_res)               # guard 4

    # ---- descriptive disclosures + diagnostics (non-binding) -------------------
    loco_rows = loco_diagnostic(test_sub, margin)                 # R1.7, same read
    loco_ok = [r["above_margin"] for r in loco_rows if r["above_margin"] is not None]
    full_res = infer_cell(
        table, np.random.default_rng(seed_for(EXPERIMENT_ID, "full", DOMAIN, INSTRUMENT)))
    train_res = infer_cell(
        train_sub, np.random.default_rng(seed_for(EXPERIMENT_ID, "train", DOMAIN, INSTRUMENT)))
    train_consistent = bool(train_res["effect_bps"] > 0.0)        # R1.7 precondition
    stratum_rows = [
        stratum_summary(table, "FULL", full_res),
        stratum_summary(train_sub, "TRAIN", train_res),
        stratum_summary(test_sub, "TEST", test_res),
    ]
    robust_rows = seed_robustness(test_sub)

    # ---- persist results --------------------------------------------------------
    write_rows(RESULTS_DIR / "reconciliation.csv", recon_rows)
    write_rows(RESULTS_DIR / "test_inference.csv", [{
        "instrument": INSTRUMENT, "domain": DOMAIN, "stratum": "TEST",
        "binding": True, **test_res, **verdict,
    }])
    write_rows(RESULTS_DIR / "stratum_disclosure.csv", stratum_rows)
    write_rows(RESULTS_DIR / "seed_robustness.csv", robust_rows)
    write_rows(RESULTS_DIR / "loco_diagnostic.csv", loco_rows)
    metadata = {
        "experiment_id": EXPERIMENT_ID,
        "registry_id": "CF-AVWAP-001/HYP-004-TI-TEST",
        "route_label": "TEST-stratum temporal-stability subsample check (R1.7 — "
                       "dependent subsample, not independent out-of-sample)",
        "frozen_tail_hash": frozen_hash,
        "dependencies": deps,
        "rt_cons_bps": RT_CONS_BPS,
        "financing_rate_bps_per_day": FINANCING_RATE_BPS_PER_DAY,
        "alpha_one_sided": ALPHA,
        "n_boot": N_BOOT,
        "n_null_calibration": N_NULL_CAL,
        "binding_rule": ("ci_low_1s > margin (R1.2 calibrated) AND raw boot_p "
                         "surviving the phase-level Holm family (R1.1; <=4 members) "
                         "at alpha=0.05 — adjudicated in G2-gate-review.md; this "
                         "run's flag is PROVISIONAL"),
        "calibration": calibration_rows[0],
        "loco_summary": {"n_drops": len(loco_rows),
                         "all_above_margin": bool(all(loco_ok)) if loco_ok else None,
                         "min_ci_low_1s": min((r["ci_low_1s"] for r in loco_rows
                                               if r["ci_low_1s"] is not None),
                                              default=None)},
        "train_consistent": train_consistent,
        "nomination_precondition_met": train_consistent,
        "boundary_time": str(series["boundary_time"]),
        "boundary_rule": "TEST iff trigger close > last TRAIN 1m analysis bar close "
                         "(ties -> TRAIN)",
        "source_file": series["source_file"],
        "analysis_rows_1m": series["analysis_rows_1m"],
        "train_rows_1m": series["train_rows_1m"],
        "n_full": int(table.height),
        "n_train": int(train_sub.height),
        "n_test": int(test_sub.height),
        "determinism_replay": replay,
        "test_inference": test_res,
        **verdict,
    }
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(metadata, indent=2, default=str))

    # ---- plots ------------------------------------------------------------------
    plot_test_distribution(test_sub, test_res, verdict,
                           PLOTS_DIR / "test_stratum_distribution.png")
    plot_stratum_comparison(stratum_rows, verdict, PLOTS_DIR / "stratum_comparison.png")

    # ---- console summary ----------------------------------------------------------
    LOGGER.info("--- one-shot TEST read (provisional; binding = phase-family Holm) ---")
    LOGGER.info("%s-%s TEST: n=%d net=%.2f bps 1s-low=%.2f (margin=%.2f) "
                "CI=[%.2f, %.2f] raw_p=%.4f -> %s",
                INSTRUMENT, DOMAIN, test_res["n_events"], test_res["effect_bps"],
                test_res["ci_low_1s"], margin, test_res["ci_low"], test_res["ci_high"],
                test_res["boot_p"], verdict["verdict"])
    LOGGER.info("G2 adjudication: %s | phase outcome: %s | train_consistent: %s",
                verdict["g2_adjudication"], verdict["phase_outcome"], train_consistent)
    LOGGER.info("Results in %s, plots in %s", RESULTS_DIR, PLOTS_DIR)


if __name__ == "__main__":
    main()
