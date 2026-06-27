"""Experiment EXP-033: TRAIN-Only Horizon Sweep (Attribution Crossover + FH(H) Net Curve).

Implements analysis-plan.md / scope.md (Phase 008, Tier A2; DIAG-004, 0 slots). Two
predeclared deliverables on TRAIN (first 70% of the analysis set):

1. **Attribution map**: the EXP-031 decomposition X_full* = X_entry(H) + X_exit(H)
   evaluated over the full grid H in {1,2,3,4,6,8,12,24} domain bars, with the frozen
   EXP-027 inference per leg (regime-cluster bootstrap CI; stratified sign-permutation
   p reported DESCRIPTIVELY — no Holm family, no leg-significance claims: this is a
   diagnostic map, not a verdict). A predeclared stable-crossover rule classifies each
   domain (H_cross / ENTRY_DOMINANT_THROUGHOUT / NO_STABLE_CROSSOVER).

2. **FH(H) net curve + B2 selections**: per-event absolute net expectancy of the
   fixed-horizon-exit variant, ``net_e(H) = fh_bps(e,H) - RT_cons_i - financing_i(e,H)``,
   aggregated equal-weight over EURUSD/USTEC/XAUUSD (BTCUSD excluded per D0 §4; all
   per-instrument curves disclosed). Mechanical selections, frozen on emission to
   ``results/b2_selection.json``:
   * H*_d = smallest H within one bootstrap SE of the grid maximum (one-SE rule);
     ``B2_ELIGIBLE_d = false`` if the grid maximum <= 0;
   * pyramid policy at H*_d: first of (all_legs, first_leg_only, pyramid_legs_only)
     within one SE of the best reportable policy.

**Fixed population across the grid (containment)**: a row (event or control) enters iff
``start_idx + 24 <= train_cutoff_idx`` AND ``completion_idx <= train_cutoff_idx``. The
second clause is a PREDECLARED CORRECTION (F08, scope/plan amended 2026-06-10, before
execution): the originally locked rule omitted it, but the BTC lifetime is an outcome
too, and a lifetime completing past the TRAIN boundary would leak TEST prices into
TRAIN characterisation (EXP-035's scope already carried the clause). With one fixed
population, every row has a reportable FH return at every grid H, the common-control
set is H-invariant, and additivity holds at every H. Exclusion counts are disclosed
per domain (``excluded_window`` / ``excluded_lifetime``).

Reconciliation anchors (hard gates, run before any sweep output): rebuilt domain bars ==
EXP-020 metadata; frozen tail == pinned hash (e50873d12a9f68d9); a one-time relaxed-rule
rebuild (EXP-031's per-H population on the FULL analysis set) must reproduce EXP-031's
published H in {1,6} leg effects to <= 0.01 bps.

The final 30% global holdout is never loaded; the TEST segment (last 30% of the analysis
set) is never read past the reconciliation anchor (which replicates EXP-031's published
full-analysis-set numbers only). Shared bootstrap resample indices across H per domain
(identical seed + identical strata structure => identical index draws) keep the one-SE
band internally coherent.

Run:
    cd <project-root> && python python/experiments/EXP-033/code/run_experiment.py
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

from xen.financing import (  # noqa: E402
    elapsed_calendar_days,
    financing_bps_from_days,
    verify_financing,
)
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
    permutation_p,
)

LOGGER = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-033"
DATA_DIR = PROJECT_ROOT / "data"
EXP_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"

EXP020_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-020" / "results"
EXP022_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-022" / "results"
EXP028_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-028" / "results"
EXP031_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-031" / "results"

DOMAINS: tuple[str, ...] = ("5m", "1h", "4h")
INSTRUMENTS: tuple[str, ...] = ("BTCUSD", "EURUSD", "USTEC", "XAUUSD")

# LOCKED horizon grid (domain bars). MAX_H bounds the containment rule.
H_GRID: tuple[int, ...] = (1, 2, 3, 4, 6, 8, 12, 24)
MAX_H: int = max(H_GRID)
RECON_HORIZONS: tuple[int, ...] = (1, 6)        # EXP-031 published horizons

TRAIN_FRACTION = 0.7

# D0 §4: BTCUSD excluded from the H*-selection objective (disclosed elsewhere).
OBJECTIVE_INSTRUMENTS: tuple[str, ...] = ("EURUSD", "USTEC", "XAUUSD")

# FROZEN EXP-030 CONSERVATIVE costs + predeclared financing (bps; bps/day).
RT_CONS_BPS: dict[str, float] = {"EURUSD": 3.0, "USTEC": 5.0, "XAUUSD": 6.0, "BTCUSD": 16.0}
FINANCING_RATE_BPS_PER_DAY: dict[str, float] = {
    "EURUSD": 0.6, "USTEC": 1.2, "XAUUSD": 1.2, "BTCUSD": 10.0,
}

# Pyramid-policy menu in the predeclared simplicity-preference order.
POLICIES: tuple[str, ...] = ("all_legs", "first_leg_only", "pyramid_legs_only")

# EXP-028 PRIMARY population construction (identical to EXP-030/031).
COMPLETED_OUTCOMES = ("favorable", "adverse", "trend_change")
PAIR_KEYS = ["instrument", "domain", "regime_id", "direction", "event_trigger_idx"]
MIN_CONTROLS = EM.MIN_CONTROLS

# Reportability (EXP-021/027/028 thresholds) for the attribution legs.
MIN_REPORTABLE_EVENTS = 30
MIN_DIRECTION_EVENTS = 8
DOMAIN_MIN_INSTRUMENTS = 3

# Per-instrument event floors for the FH net curve (scope zero-baseline guard).
CURVE_MIN_EVENTS: dict[str, int] = {"5m": 30, "1h": 30, "4h": 15}

# Inference convention.
N_BOOT = 1000
N_PERM = 1000
CHUNK = 200
CI_PERCENTILES = (2.5, 97.5)

# Predeclared crossover threshold (entry share).
CROSSOVER_SHARE = 0.5

# Tolerances.
RECON_TOL_BPS = 0.01            # relaxed-rule legs vs EXP-031 published effects
DETERMINISM_TOL = 1e-12

# Frozen inference functions + pinned hash (same tail and pin as EXP-030/031).
FROZEN_FUNCTIONS: tuple[str, ...] = (
    "domain_effect", "build_strata", "bootstrap_effect_distribution",
    "holm_adjust", "decide_label",
)
FROZEN_TAIL_EXPECTED_HASH = "e50873d12a9f68d9"


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
# Integrity guards
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
            f"EXP-027/028 source (got {h_used} != pinned {FROZEN_TAIL_EXPECTED_HASH})."
        )
    LOGGER.info("Frozen inference tail verified against pinned EXP-027 hash (%s)", h_used)
    return h_used


def check_dependencies() -> dict[str, str]:
    """Assert EXP-028 EVAL_SUPPORTED and the EXP-031/EXP-022/EXP-020 artifacts exist."""
    exp028 = load_json(EXP028_RESULTS / "run_metadata.json")
    v028 = str(exp028.get("overall_verdict", ""))
    if v028 != "EVAL_SUPPORTED":
        raise ValueError(f"EXP-028 overall_verdict must be EVAL_SUPPORTED, got {v028!r}")
    for artifact in (EXP022_RESULTS / "lifetime_observations.csv",
                     EXP031_RESULTS / "decomposition_results.csv",
                     EXP020_RESULTS / "analysis_metadata.csv"):
        if not artifact.exists():
            raise FileNotFoundError(f"missing dependency artifact: {artifact}")
    LOGGER.info("Dependency gate PASS (EXP-028=%s; EXP-031/EXP-022 artifacts present)", v028)
    return {"EXP-028": v028, "EXP-031": "present", "EXP-022": "present"}


# --------------------------------------------------------------------------- #
# Domain rebuild (Close + CloseTime) + holdout-safe metadata guard
# --------------------------------------------------------------------------- #
def expected_timebar_sources() -> set[str]:
    """Canonical source Parquet filenames recorded by EXP-020 metadata (mirrors EXP-031)."""
    expected = pl.read_csv(EXP020_RESULTS / "analysis_metadata.csv")
    return set(expected.get_column("source_file").unique().to_list())


def build_cell_series() -> tuple[dict[tuple[str, str], dict[str, np.ndarray]], list[dict[str, Any]]]:
    """Rebuild first-70% domain bars; return per-cell log(Close) + CloseTime arrays."""
    expected_sources = expected_timebar_sources()
    files = [path for path in list_timebar_files(DATA_DIR) if path.name in expected_sources]
    missing = sorted(expected_sources.difference({path.name for path in files}))
    if missing:
        raise FileNotFoundError(f"missing EXP-020 source files under data/timebars: {missing}")
    series: dict[tuple[str, str], dict[str, np.ndarray]] = {}
    metadata_rows: list[dict[str, Any]] = []
    for path in tqdm(files, desc="rebuild domain bars"):
        data = load_analysis_data(path)
        for domain, frame in build_domain_frames(data.frame).items():
            close = frame.get_column("Close").to_numpy().astype(float)
            ct = frame.get_column("CloseTime").to_numpy().astype("datetime64[ns]")
            series[(data.instrument, domain)] = {
                "log_close": np.log(close),
                "close_time": ct,
            }
            metadata_rows.append({
                "instrument": data.instrument, "domain": domain,
                "source_file": data.source_file, "source_total_rows": data.total_rows,
                "analysis_rows_1m": data.analysis_rows, "analysis_start_1m": data.analysis_start,
                "analysis_end_1m": data.analysis_end, "domain_bars": frame.height,
                "domain_max_close_time": str(frame.get_column("CloseTime").max()),
            })
    return series, metadata_rows


def validate_analysis_metadata(metadata_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Hard-fail if the reconstructed domain bars diverge from EXP-020 analysis metadata."""
    expected = pl.read_csv(EXP020_RESULTS / "analysis_metadata.csv")
    expected_by_cell = {(str(r["instrument"]), str(r["domain"])): r for r in expected.to_dicts()}
    check_rows: list[dict[str, Any]] = []
    for row in metadata_rows:
        cell = (str(row["instrument"]), str(row["domain"]))
        if cell not in expected_by_cell:
            raise ValueError(f"{cell[0]}/{cell[1]} missing from EXP-020 analysis_metadata.csv")
        exp = expected_by_cell[cell]
        checks = {
            "source_file_match": row["source_file"] == exp["source_file"],
            "analysis_rows_1m_match": int(row["analysis_rows_1m"]) == int(exp["analysis_rows_1m"]),
            "domain_bars_match": int(row["domain_bars"]) == int(exp["domain_bars"]),
            "domain_max_close_time_match":
                str(row["domain_max_close_time"]) == str(exp["domain_max_close_time"]),
        }
        check_rows.append(
            {"instrument": cell[0], "domain": cell[1], "passed": all(checks.values()), **checks})
    failures = [f"{r['instrument']}/{r['domain']}" for r in check_rows if not r["passed"]]
    if failures:
        raise ValueError(f"EXP-020 analysis metadata mismatch (domain rebuild diverged): {failures}")
    LOGGER.info("Domain rebuild matches EXP-020 metadata for %d cells", len(check_rows))
    return check_rows


# --------------------------------------------------------------------------- #
# Population: EXP-028 PRIMARY rows + FH grid columns + TRAIN containment
# --------------------------------------------------------------------------- #
def split_population(lifetime: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """(events, controls): completed, finite-lifetime rows; events reportable (EXP-031)."""
    lt = ensure_bool(lifetime, ("reportable_event", "is_pyramid_bounce"))
    lt = lt.filter(pl.col("outcome").is_in(COMPLETED_OUTCOMES)
                   & pl.col("lifetime_bps").is_not_null())
    events = lt.filter((pl.col("role") == "event") & pl.col("reportable_event"))
    controls = lt.filter(pl.col("role") == "control")
    return events, controls


def add_fh_columns(
    frame: pl.DataFrame, series: dict[tuple[str, str], dict[str, np.ndarray]],
) -> pl.DataFrame:
    """Attach ``fh_<H>`` (signed bps), ``fh_days_<H>``, and ``trigger_ns`` columns.

    ``fh_H = 10000 * direction * (log_close[start+H] - log_close[start])``; NaN where
    ``start+H`` exceeds the analysis slice (the holdout is never indexed).
    ``fh_days_H`` is the fractional calendar duration to the FH exit bar, via the
    shared ``xen.financing.elapsed_calendar_days`` live path (F03). ``trigger_ns``
    (entry-bar CloseTime) feeds the F07 split-half stability disclosure. Also
    asserts ``start_close`` reproduces the rebuilt base bar.
    """
    si = frame.get_column("start_idx").to_numpy().astype(np.int64)
    d = frame.get_column("direction").to_numpy().astype(float)
    sc = frame.get_column("start_close").to_numpy().astype(float)
    inst = frame.get_column("instrument").to_numpy()
    dom = frame.get_column("domain").to_numpy()
    n_rows = frame.height
    fh = {h: np.full(n_rows, np.nan) for h in H_GRID}
    fh_days = {h: np.full(n_rows, np.nan) for h in H_GRID}
    trigger_ns = np.full(n_rows, np.int64(0))
    base_bad = 0
    for (i, dm), arrs in series.items():
        rows = np.flatnonzero((inst == i) & (dom == dm))
        if rows.size == 0:
            continue
        lc, ct = arrs["log_close"], arrs["close_time"]
        b = si[rows]
        if (b < 0).any() or (b >= lc.size).any():
            raise ValueError(f"start_idx out of analysis-slice range for {i}/{dm}")
        tol = 1e-9 * sc[rows]
        base_bad += int(np.sum(np.abs(np.exp(lc[b]) - sc[rows]) > tol))
        trigger_ns[rows] = ct[b].astype(np.int64)
        for h in H_GRID:
            tgt = b + h
            ok = tgt <= lc.size - 1
            sel = rows[ok]
            fh[h][sel] = 10_000.0 * d[sel] * (lc[tgt[ok]] - lc[b[ok]])
            fh_days[h][sel] = elapsed_calendar_days(ct[b[ok]], ct[tgt[ok]])
    if base_bad:
        raise ValueError(f"start_close mismatch vs rebuilt base bar in {base_bad} rows")
    return frame.with_columns(
        [pl.Series(f"fh_{h}", fh[h]) for h in H_GRID]
        + [pl.Series(f"fh_days_{h}", fh_days[h]) for h in H_GRID]
        + [pl.Series("trigger_ns", trigger_ns)]
    )


def train_cutoffs(series: dict[tuple[str, str], dict[str, np.ndarray]]) -> dict[tuple[str, str], int]:
    """Per-cell TRAIN cutoff index: floor(TRAIN_FRACTION * n_domain_bars)."""
    return {cell: int(np.floor(TRAIN_FRACTION * arrs["log_close"].size))
            for cell, arrs in series.items()}


def half_split_ns(events: pl.DataFrame, domain: str) -> float:
    """Per-domain median trigger time (ns) for the F07 split-half disclosure."""
    sub = events.filter(pl.col("domain") == domain)
    return float(sub.get_column("trigger_ns").median()) if sub.height else float("nan")


def apply_containment(
    frame: pl.DataFrame, cutoffs: dict[tuple[str, str], int],
) -> tuple[pl.DataFrame, list[dict[str, Any]]]:
    """Fixed-population containment: ``start_idx + MAX_H <= cutoff AND completion_idx <= cutoff``.

    The completion clause is the strictness clarification documented in the module
    docstring (BTC lifetimes must also resolve inside TRAIN). Returns the contained
    frame plus per-(instrument, domain, role) exclusion accounting.
    """
    cut = pl.DataFrame({
        "instrument": [c[0] for c in cutoffs],
        "domain": [c[1] for c in cutoffs],
        "train_cutoff_idx": [cutoffs[c] for c in cutoffs],
    })
    joined = frame.join(cut, on=["instrument", "domain"], how="left")
    if joined.filter(pl.col("train_cutoff_idx").is_null()).height:
        raise ValueError("missing TRAIN cutoff for some (instrument, domain) cells")
    window_ok = (pl.col("start_idx") + MAX_H) <= pl.col("train_cutoff_idx")
    lifetime_ok = pl.col("completion_idx") <= pl.col("train_cutoff_idx")
    accounting: list[dict[str, Any]] = []
    for (inst, dom, role), grp in joined.group_by(
            ["instrument", "domain", "role"], maintain_order=True):
        n0 = grp.height
        n_window = grp.filter(~window_ok).height
        n_life = grp.filter(window_ok & ~lifetime_ok).height
        accounting.append({
            "instrument": inst, "domain": dom, "role": role, "n_before": n0,
            "excluded_window": n_window, "excluded_lifetime": n_life,
            "n_after": grp.filter(window_ok & lifetime_ok).height,
        })
    contained = joined.filter(window_ok & lifetime_ok)
    # Invariant: every contained row has finite FH at every grid horizon.
    for h in H_GRID:
        if contained.filter(~pl.col(f"fh_{h}").is_finite()).height:
            raise ValueError(f"containment invariant violated: non-finite fh_{h} present")
    return contained.drop("train_cutoff_idx"), accounting


# --------------------------------------------------------------------------- #
# Reconciliation anchor: relaxed-rule rebuild vs EXP-031 published effects
# --------------------------------------------------------------------------- #
def build_legs_relaxed(events: pl.DataFrame, controls: pl.DataFrame, horizon: int) -> pl.DataFrame:
    """EXP-031 ``build_legs`` semantics (per-H population, FULL analysis set).

    Used once, for the reconciliation anchor only. is_finite (not is_not_null) per the
    EXP-031 NaN note.
    """
    fh = f"fh_{horizon}"
    ctrl_h = controls.filter(pl.col(fh).is_finite())
    ctrl_grp = ctrl_h.group_by(PAIR_KEYS).agg(
        pl.col("lifetime_bps").mean().alias("mean_control_btc"),
        pl.col(fh).mean().alias("mean_control_fh"),
        pl.len().alias("n_common_controls"),
    )
    ev_h = events.filter(pl.col(fh).is_finite())
    merged = ev_h.join(ctrl_grp, on=PAIR_KEYS, how="inner").filter(
        pl.col("n_common_controls") >= MIN_CONTROLS)
    return merged.with_columns([
        (pl.col("lifetime_bps") - pl.col("mean_control_btc")).alias("x_full_star"),
        (pl.col(fh) - pl.col("mean_control_fh")).alias("x_entry"),
    ]).with_columns(
        (pl.col("x_full_star") - pl.col("x_entry")).alias("x_exit")
    ).select("instrument", "domain", "regime_id", "direction", "is_pyramid_bounce",
             "x_full_star", "x_entry", "x_exit")


def reportable_instruments(cell: pl.DataFrame) -> list[str]:
    """Instruments meeting per-instrument reportability thresholds (EXP-028 convention)."""
    out = []
    for inst in INSTRUMENTS:
        sub = cell.filter(pl.col("instrument") == inst)
        n_bull = sub.filter(pl.col("direction") == 1).height
        n_bear = sub.filter(pl.col("direction") == -1).height
        if (sub.height >= MIN_REPORTABLE_EVENTS and n_bull >= MIN_DIRECTION_EVENTS
                and n_bear >= MIN_DIRECTION_EVENTS):
            out.append(inst)
    return out


def reconcile_vs_exp031(events: pl.DataFrame, controls: pl.DataFrame) -> list[dict[str, Any]]:
    """Relaxed-rule leg effects at H in {1,6} must reproduce EXP-031 to <= RECON_TOL_BPS.

    Same code path the TRAIN sweep uses, evaluated under EXP-031's inclusion rule on the
    full analysis set — a divergence means the sweep is NOT the EXP-031 estimator.
    Point effects only (deterministic; no resampling involved).
    """
    ref = pl.read_csv(EXP031_RESULTS / "decomposition_results.csv")
    ref_by = {(int(r["horizon"]), str(r["domain"])): r for r in ref.to_dicts()}
    rows: list[dict[str, Any]] = []
    for h in RECON_HORIZONS:
        legs = build_legs_relaxed(events, controls, h)
        for domain in DOMAINS:
            cell = legs.filter(pl.col("domain") == domain)
            insts = reportable_instruments(cell)
            exp = ref_by.get((h, domain))
            if exp is None or not bool(exp["powered"]):
                continue
            cell = cell.filter(pl.col("instrument").is_in(insts))
            checks = {}
            ok = True
            for leg, col in (("full", "x_full_star"), ("entry", "x_entry"), ("exit", "x_exit")):
                eff = domain_effect(cell.get_column(col).to_numpy().astype(float),
                                    cell.get_column("instrument").to_numpy(), insts)
                ref_eff = float(exp[f"{leg}_effect_bps"])
                diff = abs(eff - ref_eff)
                checks[f"{leg}_rebuilt_bps"] = eff
                checks[f"{leg}_exp031_bps"] = ref_eff
                checks[f"{leg}_abs_diff_bps"] = diff
                ok = ok and (diff <= RECON_TOL_BPS)
            n_ok = cell.height == int(exp["n_events"])
            rows.append({"horizon": h, "domain": domain, "n_rebuilt": cell.height,
                         "n_exp031": int(exp["n_events"]), "count_match": n_ok,
                         **checks, "passed": bool(ok and n_ok)})
    failures = [f"H={r['horizon']}/{r['domain']}" for r in rows if not r["passed"]]
    if failures:
        raise ValueError(f"EXP-031 RECONCILIATION FAILED: {failures}")
    LOGGER.info("Reconciliation PASS: relaxed-rule legs reproduce EXP-031 at H in %s",
                RECON_HORIZONS)
    return rows


# --------------------------------------------------------------------------- #
# TRAIN legs (fixed population, H-invariant common-control set)
# --------------------------------------------------------------------------- #
def build_train_legs(events: pl.DataFrame, controls: pl.DataFrame) -> pl.DataFrame:
    """Per-event legs for ALL grid horizons on the contained TRAIN population.

    Common controls per event = contained matched controls (>= MIN_CONTROLS). Every
    contained row has finite FH at every H (containment invariant), so one control
    aggregation serves the whole grid: the common-control set is H-invariant and
    ``x_full_star`` is computed once.
    """
    aggs = [pl.col("lifetime_bps").mean().alias("mean_control_btc"),
            pl.len().alias("n_common_controls")]
    aggs += [pl.col(f"fh_{h}").mean().alias(f"mean_control_fh_{h}") for h in H_GRID]
    ctrl_grp = controls.group_by(PAIR_KEYS).agg(aggs)
    merged = events.join(ctrl_grp, on=PAIR_KEYS, how="inner").filter(
        pl.col("n_common_controls") >= MIN_CONTROLS)
    cols = [(pl.col("lifetime_bps") - pl.col("mean_control_btc")).alias("x_full_star")]
    cols += [(pl.col(f"fh_{h}") - pl.col(f"mean_control_fh_{h}")).alias(f"x_entry_{h}")
             for h in H_GRID]
    legs = merged.with_columns(cols).with_columns(
        [(pl.col("x_full_star") - pl.col(f"x_entry_{h}")).alias(f"x_exit_{h}") for h in H_GRID])
    keep = (["instrument", "domain", "regime_id", "direction", "is_pyramid_bounce",
             "start_idx", "trigger_ns", "n_common_controls", "lifetime_bps", "x_full_star"]
            + [f"x_entry_{h}" for h in H_GRID] + [f"x_exit_{h}" for h in H_GRID]
            + [f"fh_{h}" for h in H_GRID] + [f"fh_days_{h}" for h in H_GRID])
    return legs.select(keep)


# --------------------------------------------------------------------------- #
# Pure computation: leg inference with shared bootstrap indices
# --------------------------------------------------------------------------- #
def infer_value(cell: pl.DataFrame, value_col: str, insts: list[str],
                boot_seed: int, perm_seed: int) -> dict[str, Any]:
    """Frozen-tail inference on one value column.

    ``boot_seed`` is shared across legs/horizons within a domain: identical seed +
    identical strata structure (fixed population) => identical resample index draws,
    so curves and bands are internally coherent. The sign-permutation p is valid here
    (paired matched-control differences) and reported descriptively.
    """
    sub = cell.filter(pl.col("instrument").is_in(insts))
    diffs = sub.get_column(value_col).to_numpy().astype(float)
    inst_labels = sub.get_column("instrument").to_numpy()
    dir_labels = sub.get_column("direction").to_numpy().astype(int)
    regime_labels = sub.get_column("regime_id").to_numpy().astype(int)
    effect = domain_effect(diffs, inst_labels, insts)
    strata = build_strata(diffs, inst_labels, dir_labels, regime_labels, insts)
    boot = bootstrap_effect_distribution(
        strata, insts, np.random.default_rng(boot_seed), N_BOOT, CHUNK)
    counts = np.array([int((inst_labels == i).sum()) for i in insts], dtype=float)
    inst_index = np.array([insts.index(i) for i in inst_labels], dtype=np.int64)
    raw_p = permutation_p(diffs, inst_index, counts, effect,
                          np.random.default_rng(perm_seed), N_PERM, CHUNK)
    return {"effect_bps": effect,
            "ci_low": float(np.percentile(boot, CI_PERCENTILES[0])),
            "ci_high": float(np.percentile(boot, CI_PERCENTILES[1])),
            "se": float(np.std(boot)), "raw_p": raw_p, "n_events": sub.height}


def attribution_sweep(legs: pl.DataFrame) -> list[dict[str, Any]]:
    """Attribution legs at every grid H per domain (descriptive p; no Holm family)."""
    rows: list[dict[str, Any]] = []
    for domain in tqdm(DOMAINS, desc="attribution sweep"):
        cell = legs.filter(pl.col("domain") == domain)
        insts = reportable_instruments(cell)
        powered = len(insts) >= DOMAIN_MIN_INSTRUMENTS
        if not powered:
            rows.append({"domain": domain, "horizon": None, "leg": None, "powered": False,
                         "n_events": cell.height, "n_instruments": len(insts),
                         "effect_bps": None, "ci_low": None, "ci_high": None, "se": None,
                         "raw_p": None, "s_entry": None, "share_status": "unpowered"})
            continue
        boot_seed = seed_for(EXPERIMENT_ID, "sweep", domain)
        full = infer_value(cell, "x_full_star", insts, boot_seed,
                           seed_for(EXPERIMENT_ID, "perm", domain, "full", 0))
        for h in H_GRID:
            entry = infer_value(cell, f"x_entry_{h}", insts, boot_seed,
                                seed_for(EXPERIMENT_ID, "perm", domain, "entry", h))
            exit_ = infer_value(cell, f"x_exit_{h}", insts, boot_seed,
                                seed_for(EXPERIMENT_ID, "perm", domain, "exit", h))
            defined = abs(full["effect_bps"]) > full["se"]
            s_entry = entry["effect_bps"] / full["effect_bps"] if defined else None
            for leg, res in (("full", full), ("entry", entry), ("exit", exit_)):
                rows.append({
                    "domain": domain, "horizon": h, "leg": leg, "powered": True,
                    "n_events": res["n_events"], "n_instruments": len(insts),
                    "effect_bps": res["effect_bps"], "ci_low": res["ci_low"],
                    "ci_high": res["ci_high"], "se": res["se"], "raw_p": res["raw_p"],
                    "s_entry": s_entry if leg == "entry" else None,
                    "share_status": ("defined" if defined else "ill_defined")
                    if leg == "entry" else None,
                })
    return rows


def crossover_classification(sweep_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Predeclared stable-crossover rule per domain (mechanical, point estimates)."""
    out: list[dict[str, Any]] = []
    for domain in DOMAINS:
        entry_rows = {r["horizon"]: r for r in sweep_rows
                      if r["domain"] == domain and r["leg"] == "entry"}
        if not entry_rows:
            out.append({"domain": domain, "classification": "UNPOWERED", "h_cross": None})
            continue
        shares = {h: entry_rows[h]["s_entry"] for h in H_GRID if h in entry_rows}
        status = {h: entry_rows[h]["share_status"] for h in H_GRID if h in entry_rows}
        h_cross = None
        for h in H_GRID:
            tail = [hh for hh in H_GRID if hh >= h]
            if all(status.get(hh) == "defined" and shares.get(hh) is not None
                   and shares[hh] >= CROSSOVER_SHARE for hh in tail):
                h_cross = h
                break
        if h_cross == H_GRID[0]:
            cls = "ENTRY_DOMINANT_THROUGHOUT"
        elif h_cross is not None:
            cls = "STABLE_CROSSOVER"
        else:
            cls = "NO_STABLE_CROSSOVER"
        out.append({"domain": domain, "classification": cls, "h_cross": h_cross})
    return out


# --------------------------------------------------------------------------- #
# FH(H) net curve + mechanical B2 selections
# --------------------------------------------------------------------------- #
def add_net_columns(events: pl.DataFrame) -> pl.DataFrame:
    """Attach ``net_<H>`` columns: fh_H - RT_cons_i - rate_i * fh_days_H."""
    inst = events.get_column("instrument").to_numpy()
    rt = np.array([RT_CONS_BPS[i] for i in inst], dtype=float)
    rate = np.array([FINANCING_RATE_BPS_PER_DAY[i] for i in inst], dtype=float)
    cols = []
    for h in H_GRID:
        fh = events.get_column(f"fh_{h}").to_numpy().astype(float)
        days = events.get_column(f"fh_days_{h}").to_numpy().astype(float)
        # Shared live path (F03): financing via the verified xen.financing helper.
        cols.append(pl.Series(f"net_{h}", fh - rt - financing_bps_from_days(rate, days)))
    return events.with_columns(cols)


def apply_policy(events: pl.DataFrame, policy: str) -> pl.DataFrame:
    """Filter the event frame to a pyramid policy subset."""
    if policy == "all_legs":
        return events
    if policy == "first_leg_only":
        return events.filter(~pl.col("is_pyramid_bounce"))
    if policy == "pyramid_legs_only":
        return events.filter(pl.col("is_pyramid_bounce"))
    raise ValueError(f"unknown policy {policy!r}")


def curve_instruments(cell: pl.DataFrame, domain: str) -> tuple[list[str], list[str]]:
    """(reportable objective instruments, dropped objective instruments) under floors."""
    floor = CURVE_MIN_EVENTS[domain]
    keep, dropped = [], []
    for inst in OBJECTIVE_INSTRUMENTS:
        n = cell.filter(pl.col("instrument") == inst).height
        (keep if n >= floor else dropped).append(inst)
    return keep, dropped


def fh_net_curve(events_net: pl.DataFrame) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Objective + per-instrument FH(H) net curves with shared-seed bootstrap SEs.

    Returns (curve rows, per-domain objective summaries used by the H* rule).
    """
    rows: list[dict[str, Any]] = []
    summary: dict[str, Any] = {}
    for domain in tqdm(DOMAINS, desc="FH net curve"):
        cell = events_net.filter(pl.col("domain") == domain)
        insts, dropped = curve_instruments(cell, domain)
        summary[domain] = {"objective_instruments": insts, "dropped_instruments": dropped,
                           "points": {}}
        # Per-instrument disclosure (all four, point estimates only).
        for inst in INSTRUMENTS:
            sub = cell.filter(pl.col("instrument") == inst)
            for h in H_GRID:
                rows.append({"domain": domain, "horizon": h, "set": inst,
                             "policy": "all_legs", "n_events": sub.height,
                             "net_bps": float(sub.get_column(f"net_{h}").mean())
                             if sub.height else None, "se": None,
                             "reportable": sub.height >= CURVE_MIN_EVENTS[domain]})
        if not insts:
            continue
        boot_seed = seed_for(EXPERIMENT_ID, "fhnet", domain)
        for h in H_GRID:
            res = _net_point(cell, f"net_{h}", insts, boot_seed)
            summary[domain]["points"][h] = res
            rows.append({"domain": domain, "horizon": h, "set": "objective",
                         "policy": "all_legs", "n_events": res["n_events"],
                         "net_bps": res["effect_bps"], "se": res["se"], "reportable": True})
    return rows, summary


def _net_point(cell: pl.DataFrame, value_col: str, insts: list[str],
               boot_seed: int) -> dict[str, Any]:
    """Equal-weight net point + bootstrap SE on a net column (shared seed across H)."""
    sub = cell.filter(pl.col("instrument").is_in(insts))
    diffs = sub.get_column(value_col).to_numpy().astype(float)
    inst_labels = sub.get_column("instrument").to_numpy()
    dir_labels = sub.get_column("direction").to_numpy().astype(int)
    regime_labels = sub.get_column("regime_id").to_numpy().astype(int)
    effect = domain_effect(diffs, inst_labels, insts)
    strata = build_strata(diffs, inst_labels, dir_labels, regime_labels, insts)
    boot = bootstrap_effect_distribution(
        strata, insts, np.random.default_rng(boot_seed), N_BOOT, CHUNK)
    return {"effect_bps": effect, "se": float(np.std(boot)),
            "ci_low": float(np.percentile(boot, CI_PERCENTILES[0])),
            "ci_high": float(np.percentile(boot, CI_PERCENTILES[1])),
            "n_events": sub.height}


def select_h_star(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """One-SE rule per domain: smallest H with net >= max - SE(argmax); eligibility."""
    out: dict[str, dict[str, Any]] = {}
    for domain in DOMAINS:
        points = summary.get(domain, {}).get("points", {})
        if not points:
            out[domain] = {"b2_eligible": False, "h_star": None,
                           "reason": "no reportable objective instruments"}
            continue
        nets = {h: points[h]["effect_bps"] for h in H_GRID if h in points}
        h_max = max(nets, key=lambda h: nets[h])
        net_max = nets[h_max]
        se_max = points[h_max]["se"]
        if net_max <= 0.0:
            out[domain] = {"b2_eligible": False, "h_star": None, "h_argmax": h_max,
                           "net_max_bps": net_max, "se_at_argmax": se_max,
                           "reason": "grid maximum <= 0 (one-SE rule not applied)"}
            continue
        h_star = next(h for h in H_GRID if h in nets and nets[h] >= net_max - se_max)
        out[domain] = {"b2_eligible": True, "h_star": h_star, "h_argmax": h_max,
                       "net_max_bps": net_max, "se_at_argmax": se_max,
                       "net_at_h_star_bps": nets[h_star],
                       "reason": "smallest H within one SE of grid max"}
    return out


def select_pyramid_policy(
    events_net: pl.DataFrame, selection: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Per eligible domain: policy nets at H* and the one-SE preference-order pick."""
    rows: list[dict[str, Any]] = []
    for domain in DOMAINS:
        sel = selection[domain]
        if not sel.get("b2_eligible"):
            sel["pyramid_policy"] = None
            continue
        h_star = sel["h_star"]
        cell = events_net.filter(pl.col("domain") == domain)
        policy_res: dict[str, dict[str, Any]] = {}
        for policy in POLICIES:
            sub = apply_policy(cell, policy)
            insts, dropped = curve_instruments(sub, domain)
            reportable = len(insts) == len(OBJECTIVE_INSTRUMENTS)
            res: dict[str, Any] = {"reportable": reportable, "dropped": dropped}
            if insts:
                boot_seed = seed_for(EXPERIMENT_ID, "policy", domain, policy)
                res.update(_net_point(sub, f"net_{h_star}", insts, boot_seed))
            policy_res[policy] = res
            rows.append({"domain": domain, "h_star": h_star, "policy": policy,
                         "reportable": reportable,
                         "dropped_instruments": ",".join(dropped),
                         "n_events": res.get("n_events"),
                         "net_bps": res.get("effect_bps"), "se": res.get("se")})
        candidates = {p: r for p, r in policy_res.items() if r.get("reportable")}
        if not candidates:
            sel["pyramid_policy"] = None
            sel["policy_note"] = "no policy keeps all objective instruments above floor"
            continue
        best = max(candidates, key=lambda p: candidates[p]["effect_bps"])
        threshold = candidates[best]["effect_bps"] - candidates[best]["se"]
        sel["pyramid_policy"] = next(
            p for p in POLICIES if p in candidates and candidates[p]["effect_bps"] >= threshold)
        sel["policy_best"] = best
        sel["policy_net_bps"] = candidates[sel["pyramid_policy"]]["effect_bps"]
    return rows, selection


def selection_stability(
    events_net: pl.DataFrame, summary: dict[str, Any],
    selection: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Split-half stability DISCLOSURE for the H*/policy selection (F07).

    Chronological halves of the contained TRAIN events (per-domain median trigger
    time). Per half: the objective-set FH(H) net point curve (point estimates only;
    the full-TRAIN bootstrap SE at the argmax is reused as the comparison scale).
    Flags recorded per eligible domain:

      * ``eligibility_stable``  — both halves' grid maxima are > 0;
      * ``h_star_stable``       — the frozen H*'s net in each half is within one
                                  full-TRAIN SE of that half's own maximum;
      * ``policy_stable``       — the selected pyramid policy's net at H* in each
                                  half is within one full-TRAIN SE of that half's
                                  best reportable policy.

    DISCLOSURE ONLY: it does not alter the mechanical one-SE selection — it is
    recorded in ``b2_selection.json`` so the EXP-037 scope (and Stage-4 governance)
    can weigh selection fragility on power-thin domains (4h especially) before
    spending a Tier-B slot.
    """
    out: dict[str, dict[str, Any]] = {}
    for domain in DOMAINS:
        sel = selection[domain]
        if not sel.get("b2_eligible"):
            out[domain] = {"checked": False, "reason": "domain not B2-eligible"}
            continue
        insts = summary[domain]["objective_instruments"]
        se_full = sel["se_at_argmax"]
        h_star = sel["h_star"]
        policy = sel.get("pyramid_policy")
        cell = events_net.filter(pl.col("domain") == domain)
        med = half_split_ns(cell, domain)
        halves = {"h1": cell.filter(pl.col("trigger_ns") <= med),
                  "h2": cell.filter(pl.col("trigger_ns") > med)}
        rec: dict[str, Any] = {"checked": True, "split_median_ns": med,
                               "se_scale_bps": se_full}
        elig_ok, hstar_ok, policy_ok = True, True, True
        for name, half in halves.items():
            sub = half.filter(pl.col("instrument").is_in(insts))
            nets = {}
            for h in H_GRID:
                per_inst = [float(sub.filter(pl.col("instrument") == i)
                                  .get_column(f"net_{h}").mean())
                            for i in insts
                            if sub.filter(pl.col("instrument") == i).height > 0]
                if per_inst:
                    nets[h] = float(np.mean(per_inst))
            if not nets:
                rec[f"{name}_status"] = "empty"
                elig_ok = hstar_ok = policy_ok = False
                continue
            h_argmax = max(nets, key=lambda h: nets[h])
            rec[f"{name}_n_events"] = sub.height
            rec[f"{name}_h_argmax"] = h_argmax
            rec[f"{name}_net_max_bps"] = nets[h_argmax]
            rec[f"{name}_net_at_h_star_bps"] = nets.get(h_star)
            elig_ok = elig_ok and (nets[h_argmax] > 0.0)
            hstar_ok = hstar_ok and (nets.get(h_star) is not None
                                     and nets[h_star] >= nets[h_argmax] - se_full)
            if policy is not None:
                pol_nets = {}
                for p in POLICIES:
                    psub = apply_policy(sub, p)
                    per_inst = [float(psub.filter(pl.col("instrument") == i)
                                      .get_column(f"net_{h_star}").mean())
                                for i in insts
                                if psub.filter(pl.col("instrument") == i).height > 0]
                    if len(per_inst) == len(insts):
                        pol_nets[p] = float(np.mean(per_inst))
                rec[f"{name}_policy_nets"] = pol_nets
                if policy in pol_nets and pol_nets:
                    best = max(pol_nets.values())
                    policy_ok = policy_ok and (pol_nets[policy] >= best - se_full)
                else:
                    policy_ok = False
        rec.update({"eligibility_stable": bool(elig_ok),
                    "h_star_stable": bool(hstar_ok),
                    "policy_stable": bool(policy_ok if policy is not None else True)})
        out[domain] = rec
    return out


# --------------------------------------------------------------------------- #
# Determinism replay
# --------------------------------------------------------------------------- #
def determinism_replay(legs: pl.DataFrame, events_net: pl.DataFrame,
                       sweep_rows: list[dict[str, Any]],
                       summary: dict[str, Any]) -> dict[str, Any]:
    """Re-run the 5m H=6 entry leg + 5m H=6 objective net point; assert exact identity."""
    domain, h = "5m", 6
    cell = legs.filter(pl.col("domain") == domain)
    insts = reportable_instruments(cell)
    replay_leg = infer_value(cell, f"x_entry_{h}", insts,
                             seed_for(EXPERIMENT_ID, "sweep", domain),
                             seed_for(EXPERIMENT_ID, "perm", domain, "entry", h))
    ref_leg = next(r for r in sweep_rows
                   if r["domain"] == domain and r["horizon"] == h and r["leg"] == "entry")
    drift = max(abs(replay_leg[k] - ref_leg[k])
                for k in ("effect_bps", "ci_low", "ci_high", "raw_p"))
    point_ref = summary.get(domain, {}).get("points", {}).get(h)
    if point_ref is not None:
        cell_net = events_net.filter(pl.col("domain") == domain)
        insts_net = curve_instruments(cell_net, domain)[0]
        replay_net = _net_point(cell_net, f"net_{h}", insts_net,
                                seed_for(EXPERIMENT_ID, "fhnet", domain))
        drift = max(drift, abs(replay_net["effect_bps"] - point_ref["effect_bps"]),
                    abs(replay_net["se"] - point_ref["se"]))
    return {"cell": f"{domain}/H={h}", "max_drift": drift,
            "passed": bool(drift <= DETERMINISM_TOL)}


# --------------------------------------------------------------------------- #
# Plotting (4)
# --------------------------------------------------------------------------- #
def plot_s_entry(sweep_rows: list[dict[str, Any]],
                 crossover: list[dict[str, Any]], path: Path) -> None:
    """s_entry(H) per domain with the 0.5 line and H_cross markers."""
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = {"5m": "#3498db", "1h": "#e67e22", "4h": "#2e7d32"}
    cls_by_domain = {c["domain"]: c for c in crossover}
    for domain in DOMAINS:
        pts = [(r["horizon"], r["s_entry"]) for r in sweep_rows
               if r["domain"] == domain and r["leg"] == "entry" and r["s_entry"] is not None]
        if not pts:
            continue
        hs, ss = zip(*sorted(pts))
        ax.plot(hs, ss, "o-", color=colors[domain], label=f"{domain}")
        hc = cls_by_domain.get(domain, {}).get("h_cross")
        if hc is not None:
            ax.axvline(hc, color=colors[domain], ls=":", lw=1.0)
    ax.axhline(CROSSOVER_SHARE, color="#c0392b", ls="--", lw=0.9, label="crossover (0.5)")
    ax.axhline(1.0, color="black", lw=0.5)
    ax.axhline(0.0, color="black", lw=0.5)
    ax.set_xscale("log")
    ax.set_xticks(H_GRID)
    ax.set_xticklabels([str(h) for h in H_GRID])
    ax.set_xlabel("Neutral exit horizon H (domain bars)")
    ax.set_ylabel("Entry share s_entry(H)")
    ax.set_title("EXP-033 attribution sweep — entry share vs horizon (TRAIN)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_fh_net_curves(summary: dict[str, Any],
                       selection: dict[str, dict[str, Any]], path: Path) -> None:
    """Objective FH(H) net curve per domain with one-SE band of the max and H* marker."""
    fig, axes = plt.subplots(1, len(DOMAINS), figsize=(5.5 * len(DOMAINS), 4.5))
    for ax, domain in zip(np.atleast_1d(axes), DOMAINS):
        points = summary.get(domain, {}).get("points", {})
        if not points:
            ax.set_title(f"{domain}: no reportable objective instruments")
            continue
        hs = [h for h in H_GRID if h in points]
        nets = [points[h]["effect_bps"] for h in hs]
        ses = [points[h]["se"] for h in hs]
        ax.errorbar(hs, nets, yerr=ses, fmt="o-", color="#3498db", capsize=3)
        sel = selection[domain]
        if sel.get("h_star") is not None:
            thr = sel["net_max_bps"] - sel["se_at_argmax"]
            ax.axhline(thr, color="#7f8c8d", ls=":", lw=0.9, label="max - 1 SE")
            ax.axvline(sel["h_star"], color="#2e7d32", ls="--", lw=1.2,
                       label=f"H*={sel['h_star']}")
        ax.axhline(0, color="black", lw=0.8)
        ax.set_xscale("log")
        ax.set_xticks(H_GRID)
        ax.set_xticklabels([str(h) for h in H_GRID])
        ax.set_xlabel("H (domain bars)")
        ax.set_ylabel("Net per-event expectancy (bps)")
        eligible = "ELIGIBLE" if sel.get("b2_eligible") else "NOT ELIGIBLE"
        ax.set_title(f"{domain} — B2 {eligible}")
        ax.legend(fontsize=8)
    fig.suptitle("EXP-033 FH(H) net curve (objective = EURUSD/USTEC/XAUUSD; "
                 "CONS costs + financing)", fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_decomposition_at_hstar(sweep_rows: list[dict[str, Any]],
                                selection: dict[str, dict[str, Any]], path: Path) -> None:
    """Stacked entry/exit bars with CI whiskers at H* (fallback H=6) per domain."""
    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(DOMAINS))
    width = 0.35
    for k, leg, color in ((0, "entry", "#3498db"), (1, "exit", "#e67e22")):
        effs, lo_err, hi_err = [], [], []
        for domain in DOMAINS:
            h_sel = selection[domain].get("h_star") or 6
            row = next((r for r in sweep_rows if r["domain"] == domain
                        and r["horizon"] == h_sel and r["leg"] == leg), None)
            if row is None or row["effect_bps"] is None:
                effs.append(np.nan)
                lo_err.append(0.0)
                hi_err.append(0.0)
            else:
                effs.append(row["effect_bps"])
                lo_err.append(row["effect_bps"] - row["ci_low"])
                hi_err.append(row["ci_high"] - row["effect_bps"])
        ax.bar(x + (k - 0.5) * width, effs, width, yerr=[lo_err, hi_err], capsize=3,
               label=f"X_{leg}", color=color)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{d}\n(H={selection[d].get('h_star') or 6})" for d in DOMAINS])
    ax.set_ylabel("Matched-control excess (bps; gross)")
    ax.set_title("EXP-033 decomposition at the selected horizon (TRAIN)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_policy_comparison(policy_rows: list[dict[str, Any]],
                           selection: dict[str, dict[str, Any]], path: Path) -> None:
    """Pyramid-policy nets with SE whiskers at H* per eligible domain."""
    eligible = [d for d in DOMAINS if selection[d].get("b2_eligible")]
    if not eligible:
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.text(0.5, 0.5, "No B2-eligible domain (grid max <= 0 everywhere)",
                ha="center", va="center")
        ax.axis("off")
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return
    fig, axes = plt.subplots(1, len(eligible), figsize=(5 * len(eligible), 4.2), squeeze=False)
    for ax, domain in zip(axes[0], eligible):
        rows = [r for r in policy_rows if r["domain"] == domain]
        xs = np.arange(len(rows))
        for k, r in enumerate(rows):
            chosen = selection[domain].get("pyramid_policy") == r["policy"]
            color = "#2e7d32" if chosen else ("#7f8c8d" if r["reportable"] else "#c0392b")
            if r["net_bps"] is not None:
                ax.bar(k, r["net_bps"], yerr=r["se"] or 0.0, capsize=4, color=color)
        ax.axhline(0, color="black", lw=0.8)
        ax.set_xticks(xs)
        ax.set_xticklabels([r["policy"] for r in rows], fontsize=7)
        ax.set_title(f"{domain} @ H*={selection[domain]['h_star']} "
                     f"(chosen: {selection[domain].get('pyramid_policy')})")
        ax.set_ylabel("Net (bps)")
    fig.suptitle("EXP-033 pyramid-policy comparison (green = selected; red = below floor)",
                 fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    """Run the EXP-033 TRAIN-only horizon sweep end to end."""
    configure_logging()
    ensure_output_dirs()
    LOGGER.info("=== %s: TRAIN-only horizon sweep ===", EXPERIMENT_ID)

    frozen_hash = verify_frozen_inference()
    verify_financing()
    LOGGER.info("Financing helper self-check PASS")
    deps = check_dependencies()

    series, metadata_rows = build_cell_series()
    validate_analysis_metadata(metadata_rows)
    cutoffs = train_cutoffs(series)

    lifetime = pl.read_csv(EXP022_RESULTS / "lifetime_observations.csv")
    events_full, controls_full = split_population(lifetime)
    events_full = add_fh_columns(events_full, series)
    controls_full = add_fh_columns(controls_full, series)

    # Reconciliation anchor (full analysis set, EXP-031 inclusion rule) — one time.
    recon_rows = reconcile_vs_exp031(events_full, controls_full)

    # TRAIN-only from here on.
    events, ev_accounting = apply_containment(events_full, cutoffs)
    controls, ctrl_accounting = apply_containment(controls_full, cutoffs)
    legs = build_train_legs(events, controls)
    LOGGER.info("TRAIN legs population: %d events (%s)", legs.height,
                {d: legs.filter(pl.col('domain') == d).height for d in DOMAINS})

    sweep_rows = attribution_sweep(legs)
    crossover = crossover_classification(sweep_rows)

    # FH net curve is computed on the SAME contained event population carried in
    # ``legs`` (events with >= MIN_CONTROLS common controls), so the curve and the
    # attribution read describe one population.
    events_net = add_net_columns(legs)
    curve_rows, summary = fh_net_curve(events_net)
    selection = select_h_star(summary)
    policy_rows, selection = select_pyramid_policy(events_net, selection)
    stability = selection_stability(events_net, summary, selection)

    replay = determinism_replay(legs, events_net, sweep_rows, summary)
    if not replay["passed"]:
        raise ValueError(f"DETERMINISM REPLAY FAILED: {replay}")

    # ---- persist results (b2_selection.json frozen on emission, before plots) ----
    write_rows(RESULTS_DIR / "reconciliation.csv", recon_rows)
    write_rows(RESULTS_DIR / "population_accounting.csv", ev_accounting + ctrl_accounting)
    write_rows(RESULTS_DIR / "attribution_sweep.csv", sweep_rows)
    write_rows(RESULTS_DIR / "crossover.csv", crossover)
    write_rows(RESULTS_DIR / "fh_net_curve.csv", curve_rows)
    write_rows(RESULTS_DIR / "pyramid_policy.csv", policy_rows)
    b2_selection = {
        "experiment_id": EXPERIMENT_ID, "frozen_on_emission": True,
        "objective_instruments": list(OBJECTIVE_INSTRUMENTS),
        "h_grid": list(H_GRID),
        "per_domain": {d: selection[d] for d in DOMAINS},
        "selection_stability_disclosure": stability,
    }
    (RESULTS_DIR / "b2_selection.json").write_text(
        json.dumps(b2_selection, indent=2, default=str))
    metadata = {
        "experiment_id": EXPERIMENT_ID, "frozen_tail_hash": frozen_hash,
        "dependencies": deps, "train_fraction": TRAIN_FRACTION,
        "train_cutoffs": {f"{i}/{d}": c for (i, d), c in cutoffs.items()},
        "rt_cons_bps": RT_CONS_BPS,
        "financing_rate_bps_per_day": FINANCING_RATE_BPS_PER_DAY,
        "n_boot": N_BOOT, "n_perm": N_PERM,
        "crossover": {c["domain"]: c["classification"] for c in crossover},
        "b2_selection": {d: {"eligible": selection[d].get("b2_eligible"),
                             "h_star": selection[d].get("h_star"),
                             "pyramid_policy": selection[d].get("pyramid_policy"),
                             "h_star_stable": stability[d].get("h_star_stable"),
                             "policy_stable": stability[d].get("policy_stable")}
                         for d in DOMAINS},
        "determinism_replay": replay,
        "overall_status": "MEASUREMENT_COMPLETE",
    }
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(metadata, indent=2, default=str))

    # ---- plots ---------------------------------------------------------------
    plot_s_entry(sweep_rows, crossover, PLOTS_DIR / "s_entry_sweep.png")
    plot_fh_net_curves(summary, selection, PLOTS_DIR / "fh_net_curves.png")
    plot_decomposition_at_hstar(sweep_rows, selection, PLOTS_DIR / "decomposition_at_hstar.png")
    plot_policy_comparison(policy_rows, selection, PLOTS_DIR / "pyramid_policy.png")

    # ---- console summary -----------------------------------------------------
    for c in crossover:
        LOGGER.info("crossover %s: %s (H_cross=%s)", c["domain"], c["classification"],
                    c["h_cross"])
    for d in DOMAINS:
        sel = selection[d]
        st = stability[d]
        LOGGER.info("B2 %s: eligible=%s H*=%s policy=%s (stability: H*=%s policy=%s)",
                    d, sel.get("b2_eligible"), sel.get("h_star"),
                    sel.get("pyramid_policy"), st.get("h_star_stable"),
                    st.get("policy_stable"))
    LOGGER.info("Results in %s, plots in %s", RESULTS_DIR, PLOTS_DIR)


if __name__ == "__main__":
    main()
