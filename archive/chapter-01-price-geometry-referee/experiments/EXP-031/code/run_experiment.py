"""Experiment EXP-031: AVWAP Edge Isolation (Entry-Timing vs Exit-Rule).

Implements analysis-plan.md / scope.md (Phase 007). Decomposes the EXP-028 PRIMARY
per-event matched-control excess (band-target/trend-change "BTC" lifetime exit) into an
entry-timing leg and an exit-rule leg, per domain, and assigns each domain a predeclared
sign-complete attribution label.

Construction (frozen before reading results — see scope "Decomposition Construction"):
  For each event/control row (EXP-022 ``lifetime_observations.csv``; the EXP-028 PRIMARY
  population, pyramids included) carrying ``start_idx``, ``direction`` and BTC
  ``lifetime_bps``, recompute a neutral fixed-horizon return on the rebuilt domain Close
  series:

      fh_bps(row, H) = 10000 * direction * (log_close[start_idx + H] - log_close[start_idx])

  reportable only when ``start_idx + H`` lies in the first-70% analysis slice. On the
  common-control intersection (controls valid for BOTH the BTC and the H legs), three
  matched-control-differenced per-event legs are formed:

      X_full*(H)  = event_BTC  - mean_cc(control_BTC)     (~ EXP-028 PRIMARY)
      X_entry(H)  = event_FH(H) - mean_cc(control_FH(H))  (entry timing, neutral exit)
      X_exit(H)   = X_full*(H) - X_entry(H)               (exit rule's differential value)

  so ``X_full* = X_entry + X_exit`` exactly per event (additive, exhaustive).

Inference is the FROZEN EXP-027/028 tail (``event_method``), unchanged: regime-cluster
bootstrap CI + stratified paired sign-permutation + Holm. A leg is leg-significant iff
bootstrap ``CI_low > 0`` AND Holm-adjusted ``p <= alpha`` (the EXP-028 dual rule). The
attribution classifier is a predeclared threshold map (NOT an additional NHST).

Frozen horizons H in {1, 6}; H=6 PRIMARY, H=1 robustness companion. Primary domain 5m.
This is a GROSS mechanism decomposition; costs/slippage are EXP-030's separate question
and are out of scope here. The final 30% global holdout is never loaded. No tuning, no
horizon sweep, no post-result leg reselection.

Run:
    cd <project-root> && python python/experiments/EXP-031/code/run_experiment.py
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
EXP031_CODE = Path(__file__).resolve().parent
if str(EXP031_CODE) not in sys.path:
    sys.path.insert(0, str(EXP031_CODE))

from xen.referee_calibration import (  # noqa: E402
    build_domain_frames,
    list_timebar_files,
    load_analysis_data,
    seed_for,
)

# Frozen EXP-027 inference tail (local md5-verified copy of event_method.py).
import event_method as EM  # noqa: E402
from event_method import (  # noqa: E402
    bootstrap_effect_distribution,
    build_strata,
    domain_effect,
    holm_adjust,
    permutation_p,
)

LOGGER = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-031"
DATA_DIR = PROJECT_ROOT / "data"
EXP_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"

EXP020_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-020" / "results"
EXP021_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-021" / "results"
EXP022_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-022" / "results"
EXP028_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-028" / "results"
EXP029_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-029" / "results"
EXP027_METHOD = PROJECT_ROOT / "python" / "experiments" / "EXP-027" / "code" / "event_method.py"

DOMAINS: tuple[str, ...] = ("5m", "1h", "4h")
INSTRUMENTS: tuple[str, ...] = ("BTCUSD", "EURUSD", "USTEC", "XAUUSD")
PRIMARY_DOMAIN = "5m"

# Neutral fixed-horizon exits (the EXP-027 secondary-horizon slots). H=6 PRIMARY.
HORIZONS: tuple[int, ...] = (1, 6)
PRIMARY_HORIZON = 6
COMPANION_HORIZON = 1

# Reportability (EXP-021/027/028 thresholds).
MIN_REPORTABLE_EVENTS = 30
MIN_DIRECTION_EVENTS = 8
DOMAIN_MIN_INSTRUMENTS = 3
MIN_CONTROLS = EM.MIN_CONTROLS

# Inference (calibration convention; matches EXP-027/028).
N_BOOT = 1000
N_PERM = 1000
CHUNK = 200
ALPHA = 0.05
CI_PERCENTILES = (2.5, 97.5)

# Predeclared dominance cut (two-thirds), frozen before any leg result is read.
DOMINANCE_CUT = 0.67

# Pairing key: a control shares its parent event's (instrument, domain, regime, dir,
# event_trigger_idx). Identical to EXP-028 PRIMARY pairing.
PAIR_KEYS = ["instrument", "domain", "regime_id", "direction", "event_trigger_idx"]

# EXP-022 exit-rule completion outcomes that count as a realized (non-censored) exit.
COMPLETED_OUTCOMES = ("favorable", "adverse", "trend_change")

# X_full reconciliation tolerances against EXP-028 PRIMARY (anchor; EXP-029 tol class).
RECON_ABS_TOL_BPS = 0.05
RECON_REL_TOL = 0.005
# start_close vs rebuilt log_close base-bar integrity tolerance.
START_CLOSE_RTOL = 1e-9

# Frozen inference functions whose source must byte-match EXP-027.
FROZEN_FUNCTIONS: tuple[str, ...] = (
    "domain_effect", "build_strata", "bootstrap_effect_distribution",
    "permutation_p", "holm_adjust", "decide_label", "sortino_ratio",
    "wilson_interval", "nearest_controls", "equity_advantage",
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


def load_csv(path: Path) -> pl.DataFrame:
    """Read a results CSV (raises if absent)."""
    if not path.exists():
        raise FileNotFoundError(f"missing upstream artifact: {path}")
    return pl.read_csv(path, try_parse_dates=True)


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


def _load_module(name: str, path: Path):
    """Import a module by file path without executing any ``main`` (introspection only)."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------- #
# Integrity guards (frozen inference + dependency gate)
# --------------------------------------------------------------------------- #
def verify_frozen_inference() -> str:
    """Assert the local frozen inference functions byte-match the EXP-027 source.

    Hashes the source of only the named inference-tail functions and aborts with
    FROZEN_INFERENCE_MODIFIED on any mismatch.

    Returns
    -------
    str
        The 16-char hash prefix of the concatenated frozen-function source.
    """
    ref_mod = _load_module("exp027_event_method", EXP027_METHOD)
    local_src, ref_src = [], []
    for name in FROZEN_FUNCTIONS:
        local_fn = getattr(EM, name, None)
        ref_fn = getattr(ref_mod, name, None)
        if local_fn is None or ref_fn is None:
            raise ValueError(
                f"FROZEN_INFERENCE_MODIFIED: function {name} missing in local or EXP-027 module")
        local_src.append(inspect.getsource(local_fn))
        ref_src.append(inspect.getsource(ref_fn))
    h_local = hashlib.sha256("".join(local_src).encode()).hexdigest()
    h_ref = hashlib.sha256("".join(ref_src).encode()).hexdigest()
    if h_local != h_ref:
        raise ValueError(
            "FROZEN_INFERENCE_MODIFIED: local inference tail diverges from EXP-027 "
            f"(local={h_local[:16]} != ref={h_ref[:16]}). Re-copy event_method.py."
        )
    LOGGER.info("Frozen inference tail verified against EXP-027 (hash=%s)", h_local[:16])
    return h_local[:16]


def check_dependencies() -> dict[str, str]:
    """Assert EXP-028 EVAL_SUPPORTED and EXP-029 CONSISTENT, plus EXP-020/021/022 present."""
    exp028 = load_json(EXP028_RESULTS / "run_metadata.json")
    exp029 = load_json(EXP029_RESULTS / "run_metadata.json")
    v028 = str(exp028.get("overall_verdict", ""))
    v029 = str(exp029.get("overall_parity_disposition", ""))
    if v028 != "EVAL_SUPPORTED":
        raise ValueError(f"EXP-028 overall_verdict must be EVAL_SUPPORTED, got {v028!r}")
    if v029 != "CONSISTENT":
        raise ValueError(f"EXP-029 overall_parity_disposition must be CONSISTENT, got {v029!r}")
    for artifact in (EXP022_RESULTS / "lifetime_observations.csv",
                     EXP021_RESULTS / "reaction_observations.csv",
                     EXP020_RESULTS / "avwap_events.csv",
                     EXP020_RESULTS / "analysis_metadata.csv",
                     EXP028_RESULTS / "event_level_results.csv"):
        if not artifact.exists():
            raise FileNotFoundError(f"missing dependency artifact: {artifact}")
    LOGGER.info("Dependency gate PASS (EXP-028=%s, EXP-029=%s)", v028, v029)
    return {"EXP-028": v028, "EXP-029": v029, "EXP-022": "present",
            "EXP-021": "present", "EXP-020": "present"}


# --------------------------------------------------------------------------- #
# Domain reconstruction + holdout-safe metadata guard (EXP-020/022/024 convention)
# --------------------------------------------------------------------------- #
def expected_timebar_sources() -> set[str]:
    """Return the canonical source Parquet filenames recorded by EXP-020 metadata.

    The ``data/timebars/`` directory may also contain pre-sliced ``analysis70``
    derivative files (holdout physically removed); rebuilding the EXP-020/022 substrate
    requires the original full base files (``load_analysis_data`` applies the 70% fence
    itself), so we pin to exactly the filenames EXP-020 ran on. Mirrors EXP-024.
    """
    expected = pl.read_csv(EXP020_RESULTS / "analysis_metadata.csv")
    return set(expected.get_column("source_file").unique().to_list())


def build_cell_log_close() -> tuple[dict[tuple[str, str], np.ndarray], list[dict[str, Any]]]:
    """Rebuild first-70% 5m/1h/4h domain bars per instrument; return log(Close) + metadata.

    Uses ``xen.referee_calibration`` (the EXP-020/022 loader) with the holdout fence in
    the lazy plan, so domain-bar indices align with ``start_idx`` by construction. Files
    are pinned to the EXP-020 source set so any ``analysis70`` derivative files present in
    ``data/timebars/`` are not double-sliced.
    """
    expected_sources = expected_timebar_sources()
    files = [path for path in list_timebar_files(DATA_DIR) if path.name in expected_sources]
    missing = sorted(expected_sources.difference({path.name for path in files}))
    if missing:
        raise FileNotFoundError(f"missing EXP-020 source files under data/timebars: {missing}")
    if not files:
        raise FileNotFoundError(f"no EXP-020 source timebar files under {DATA_DIR / 'timebars'}")
    log_close: dict[tuple[str, str], np.ndarray] = {}
    metadata_rows: list[dict[str, Any]] = []
    for path in tqdm(files, desc="rebuild domain bars"):
        data = load_analysis_data(path)
        for domain, frame in build_domain_frames(data.frame).items():
            close = frame.get_column("Close").to_numpy().astype(float)
            log_close[(data.instrument, domain)] = np.log(close)
            ct = frame.get_column("CloseTime") if frame.height else None
            metadata_rows.append({
                "instrument": data.instrument, "domain": domain,
                "source_file": data.source_file, "source_total_rows": data.total_rows,
                "analysis_rows_1m": data.analysis_rows, "analysis_start_1m": data.analysis_start,
                "analysis_end_1m": data.analysis_end, "domain_bars": frame.height,
                "domain_min_close_time": str(ct.min()) if ct is not None else None,
                "domain_max_close_time": str(ct.max()) if ct is not None else None,
            })
    return log_close, metadata_rows


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
            "analysis_end_1m_match": str(row["analysis_end_1m"]) == str(exp["analysis_end_1m"]),
            "domain_bars_match": int(row["domain_bars"]) == int(exp["domain_bars"]),
            "domain_max_close_time_match":
                str(row["domain_max_close_time"]) == str(exp["domain_max_close_time"]),
        }
        check_rows.append(
            {"instrument": cell[0], "domain": cell[1], "passed": all(checks.values()), **checks})
    failures = [f"{r['instrument']}/{r['domain']}" for r in check_rows if not r["passed"]]
    if failures:
        raise ValueError(
            f"EXP-020 analysis metadata mismatch (domain rebuild diverged): {failures}")
    LOGGER.info("Domain rebuild matches EXP-020 metadata for %d cells", len(check_rows))
    return check_rows


# --------------------------------------------------------------------------- #
# Fixed-horizon recompute (pure, deterministic, look-ahead- and holdout-safe)
# --------------------------------------------------------------------------- #
def add_fixed_horizon_returns(
    frame: pl.DataFrame, log_close: dict[tuple[str, str], np.ndarray],
) -> tuple[pl.DataFrame, int]:
    """Attach ``fh_<H>`` direction-signed log-return columns (bps) keyed on ``start_idx``.

    ``fh_H[row] = 10000 * direction * (log_close[start_idx + H] - log_close[start_idx])``,
    or NaN when ``start_idx + H`` exceeds the analysis-set end (non-reportable at that
    horizon — the holdout is never indexed). Also re-validates that ``start_close``
    reproduces the rebuilt base bar (alignment integrity for the FH base). Returns the
    augmented frame and the count of base-close mismatches (must be 0).
    """
    si = frame.get_column("start_idx").to_numpy().astype(np.int64)
    d = frame.get_column("direction").to_numpy().astype(float)
    sc = frame.get_column("start_close").to_numpy().astype(float)
    inst = frame.get_column("instrument").to_numpy()
    dom = frame.get_column("domain").to_numpy()
    n_rows = frame.height
    out = {h: np.full(n_rows, np.nan) for h in HORIZONS}
    base_bad = 0
    for (i, dm), lc in log_close.items():
        rows = np.flatnonzero((inst == i) & (dom == dm))
        if rows.size == 0:
            continue
        base_idx = si[rows]
        in_range = (base_idx >= 0) & (base_idx < lc.size)
        valid_rows = rows[in_range]
        b = base_idx[in_range]
        base_bad += int((~in_range).sum())
        tol = START_CLOSE_RTOL * sc[valid_rows]
        base_bad += int(np.sum(np.abs(np.exp(lc[b]) - sc[valid_rows]) > tol))
        for h in HORIZONS:
            tgt = b + h
            ok = tgt <= lc.size - 1
            sel = valid_rows[ok]
            out[h][sel] = 10_000.0 * d[sel] * (lc[tgt[ok]] - lc[b[ok]])
    frame = frame.with_columns([pl.Series(f"fh_{h}", out[h]) for h in HORIZONS])
    return frame, base_bad


# --------------------------------------------------------------------------- #
# Population split (EXP-028 PRIMARY population, pyramids included)
# --------------------------------------------------------------------------- #
def split_population(lifetime: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Return (events, controls): completed, finite-lifetime rows; events reportable.

    Mirrors EXP-028 ``build_primary_excess`` filtering: completed (non-censored) outcome,
    finite ``lifetime_bps``; events additionally require ``reportable_event``.
    """
    lt = ensure_bool(lifetime, ("reportable_event", "is_pyramid_bounce"))
    lt = lt.filter(
        pl.col("outcome").is_in(COMPLETED_OUTCOMES) & pl.col("lifetime_bps").is_not_null())
    events = lt.filter((pl.col("role") == "event") & pl.col("reportable_event"))
    controls = lt.filter(pl.col("role") == "control")
    return events, controls


# --------------------------------------------------------------------------- #
# X_full reconciliation anchor (full population; ~ EXP-028 PRIMARY)
# --------------------------------------------------------------------------- #
def full_xfull_excess(events: pl.DataFrame, controls: pl.DataFrame) -> pl.DataFrame:
    """Per-event X_full on the FULL lifetime control set (EXP-028 PRIMARY replication).

    X_full = event ``lifetime_bps`` - mean(matched controls' ``lifetime_bps``), controls
    paired by ``PAIR_KEYS``, requiring >= MIN_CONTROLS finite controls.
    """
    ctrl_mean = (
        controls.group_by(PAIR_KEYS)
        .agg(pl.col("lifetime_bps").mean().alias("mean_control_btc"),
             pl.len().alias("n_controls_finite"))
    )
    merged = events.join(ctrl_mean, on=PAIR_KEYS, how="inner")
    merged = merged.filter(pl.col("n_controls_finite") >= MIN_CONTROLS)
    return merged.with_columns(
        (pl.col("lifetime_bps") - pl.col("mean_control_btc")).alias("x_full")
    ).select("instrument", "domain", "regime_id", "direction", "is_pyramid_bounce", "x_full")


def reconcile_xfull(full_excess: pl.DataFrame) -> tuple[list[dict[str, Any]], bool]:
    """Reconcile rebuilt X_full domain effects against EXP-028 ``event_level_results.csv``.

    Hard validation anchor: the substrate is mis-wired (REVISE-blocked) unless the rebuilt
    instrument-averaged effect reproduces EXP-028 within (abs OR rel) tolerance.
    """
    exp028 = load_csv(EXP028_RESULTS / "event_level_results.csv")
    exp028_by_domain = {str(r["domain"]): r for r in exp028.to_dicts()}
    rows: list[dict[str, Any]] = []
    all_pass = True
    for domain in DOMAINS:
        cell = full_excess.filter(pl.col("domain") == domain)
        insts = reportable_instruments(cell)
        if len(insts) < DOMAIN_MIN_INSTRUMENTS:
            rows.append({"domain": domain, "rebuilt_effect_bps": None, "exp028_effect_bps": None,
                         "abs_diff_bps": None, "rel_diff": None, "n_rebuilt": cell.height,
                         "n_exp028": exp028_by_domain.get(domain, {}).get("n_events"),
                         "passed": False})
            all_pass = False
            continue
        sub = cell.filter(pl.col("instrument").is_in(insts))
        diffs = sub.get_column("x_full").to_numpy().astype(float)
        inst_labels = sub.get_column("instrument").to_numpy()
        effect = domain_effect(diffs, inst_labels, insts)
        ref = float(exp028_by_domain[domain]["effect_bps"])
        abs_diff = abs(effect - ref)
        rel_diff = abs_diff / abs(ref) if ref != 0 else float("inf")
        passed = (abs_diff <= RECON_ABS_TOL_BPS) or (rel_diff <= RECON_REL_TOL)
        all_pass = all_pass and passed
        rows.append({"domain": domain, "rebuilt_effect_bps": effect, "exp028_effect_bps": ref,
                     "abs_diff_bps": abs_diff, "rel_diff": rel_diff, "n_rebuilt": cell.height,
                     "n_exp028": int(exp028_by_domain[domain]["n_events"]), "passed": passed})
    return rows, all_pass


# --------------------------------------------------------------------------- #
# Decomposition on the common-control intersection (exact additivity)
# --------------------------------------------------------------------------- #
def build_legs(events: pl.DataFrame, controls: pl.DataFrame, horizon: int) -> pl.DataFrame:
    """Per-event X_full*/X_entry/X_exit on the common-control intersection at ``horizon``.

    Common controls (per event): finite ``lifetime_bps`` AND reportable ``fh_<H>``. Event:
    reportable ``fh_<H>`` AND >= MIN_CONTROLS common controls. By construction
    ``x_full_star = x_entry + x_exit`` per event (additive, exhaustive).
    """
    fh = f"fh_{horizon}"
    # NOTE: use is_finite(), NOT is_not_null(): Polars treats float NaN as not-null, so
    # is_not_null() would keep rows whose start_idx+H falls past the analysis-slice end
    # (fh = NaN). Those are non-reportable at this horizon and must drop out.
    ctrl_h = controls.filter(pl.col(fh).is_finite())
    ctrl_grp = (
        ctrl_h.group_by(PAIR_KEYS)
        .agg(pl.col("lifetime_bps").mean().alias("mean_control_btc"),
             pl.col(fh).mean().alias("mean_control_fh"),
             pl.len().alias("n_common_controls"))
    )
    ev_h = events.filter(pl.col(fh).is_finite())
    merged = ev_h.join(ctrl_grp, on=PAIR_KEYS, how="inner").filter(
        pl.col("n_common_controls") >= MIN_CONTROLS
    )
    legs = merged.with_columns([
        (pl.col("lifetime_bps") - pl.col("mean_control_btc")).alias("x_full_star"),
        (pl.col(fh) - pl.col("mean_control_fh")).alias("x_entry"),
    ]).with_columns(
        (pl.col("x_full_star") - pl.col("x_entry")).alias("x_exit")
    )
    return legs.select("instrument", "domain", "regime_id", "direction", "is_pyramid_bounce",
                       "n_common_controls", "x_full_star", "x_entry", "x_exit")


# --------------------------------------------------------------------------- #
# Frozen-tail inference on a per-event paired-diff column
# --------------------------------------------------------------------------- #
def reportable_instruments(cell: pl.DataFrame) -> list[str]:
    """Instruments in a domain meeting per-instrument reportability thresholds (EXP-028)."""
    out = []
    for inst in INSTRUMENTS:
        sub = cell.filter(pl.col("instrument") == inst)
        n_bull = sub.filter(pl.col("direction") == 1).height
        n_bear = sub.filter(pl.col("direction") == -1).height
        if (sub.height >= MIN_REPORTABLE_EVENTS and n_bull >= MIN_DIRECTION_EVENTS
                and n_bear >= MIN_DIRECTION_EVENTS):
            out.append(inst)
    return out


def infer_leg(
    cell: pl.DataFrame, value_col: str, insts: list[str], rng: np.random.Generator,
) -> dict[str, Any]:
    """Frozen-tail inference (effect, regime-cluster bootstrap CI, permutation p) for one leg.

    ``insts`` is the shared reportable-instrument set for the domain (identical across the
    three legs at a given horizon, since they share one population) so domain effects stay
    additive: ``effect(x_full_star) == effect(x_entry) + effect(x_exit)``.
    """
    cell = cell.filter(pl.col("instrument").is_in(insts))
    diffs = cell.get_column(value_col).to_numpy().astype(float)
    inst_labels = cell.get_column("instrument").to_numpy()
    dir_labels = cell.get_column("direction").to_numpy().astype(int)
    regime_labels = cell.get_column("regime_id").to_numpy().astype(int)

    effect = domain_effect(diffs, inst_labels, insts)
    strata = build_strata(diffs, inst_labels, dir_labels, regime_labels, insts)
    boot = bootstrap_effect_distribution(strata, insts, rng, N_BOOT, CHUNK)
    ci_low = float(np.percentile(boot, CI_PERCENTILES[0]))
    ci_high = float(np.percentile(boot, CI_PERCENTILES[1]))
    counts = np.array([int((inst_labels == i).sum()) for i in insts], dtype=float)
    inst_index = np.array([insts.index(i) for i in inst_labels], dtype=np.int64)
    raw_p = permutation_p(diffs, inst_index, counts, effect, rng, N_PERM, CHUNK)
    return {"effect_bps": effect, "ci_low": ci_low, "ci_high": ci_high,
            "ci_half_width": (ci_high - ci_low) / 2.0, "raw_p": raw_p}


def infer_horizon(legs: pl.DataFrame, horizon: int) -> dict[str, dict[str, Any]]:
    """Run the three legs through the frozen tail per domain; Holm over {entry,exit}×domains.

    Returns ``{domain: {n_events, n_bull, n_bear, n_instruments, full/entry/exit blocks,
    additivity_residual}}`` for the given horizon. X_full* is NOT entered into the Holm
    family (it is the EXP-028 anchor); only entry/exit legs are multiplicity-adjusted.
    """
    per_domain: dict[str, dict[str, Any]] = {}
    entry_raw_p: dict[str, float] = {}
    exit_raw_p: dict[str, float] = {}
    for domain in DOMAINS:
        cell = legs.filter(pl.col("domain") == domain)
        insts = reportable_instruments(cell)
        rec: dict[str, Any] = {
            "n_events": cell.height,
            "n_bull": cell.filter(pl.col("direction") == 1).height,
            "n_bear": cell.filter(pl.col("direction") == -1).height,
            "n_instruments": len(insts), "reportable_instruments": insts,
        }
        if len(insts) < DOMAIN_MIN_INSTRUMENTS:
            rec["powered"] = False
            per_domain[domain] = rec
            continue
        rec["powered"] = True
        rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "infer", horizon, domain))
        rec["full"] = infer_leg(cell, "x_full_star", insts, rng)
        rec["entry"] = infer_leg(cell, "x_entry", insts, rng)
        rec["exit"] = infer_leg(cell, "x_exit", insts, rng)
        rec["additivity_residual"] = abs(
            rec["full"]["effect_bps"] - (rec["entry"]["effect_bps"] + rec["exit"]["effect_bps"])
        )
        entry_raw_p[domain] = rec["entry"]["raw_p"]
        exit_raw_p[domain] = rec["exit"]["raw_p"]
        per_domain[domain] = rec

    # Holm over the joint {entry, exit} × reportable-domains family.
    family = {f"{d}::entry": p for d, p in entry_raw_p.items()}
    family.update({f"{d}::exit": p for d, p in exit_raw_p.items()})
    adjusted = holm_adjust(family) if family else {}
    for domain, rec in per_domain.items():
        if not rec.get("powered"):
            continue
        rec["entry"]["holm_p"] = adjusted.get(f"{domain}::entry")
        rec["exit"]["holm_p"] = adjusted.get(f"{domain}::exit")
        rec["entry"]["leg_significant"] = _leg_significant(rec["entry"])
        rec["exit"]["leg_significant"] = _leg_significant(rec["exit"])
    return per_domain


def _leg_significant(leg: dict[str, Any]) -> bool:
    """Leg-significant iff bootstrap CI_low > 0 AND Holm-adjusted p <= alpha (EXP-028 dual rule)."""
    hp = leg.get("holm_p")
    return bool(leg["ci_low"] > 0 and hp is not None and hp <= ALPHA)


# --------------------------------------------------------------------------- #
# Predeclared sign-complete attribution classifier (threshold map, NOT an NHST)
# --------------------------------------------------------------------------- #
def classify_domain(rec: dict[str, Any], xfull_for: bool) -> dict[str, Any]:
    """Apply the predeclared sign-complete attribution rule for one domain/horizon.

    ``xfull_for`` is the EXP-028 X_full EVIDENCE_FOR flag for the domain; combined with the
    rebuilt X_full* ``CI_low > 0`` it gates whether a real total exists to attribute. Shares
    are computed ONLY when that total is significant and nonzero (no zero-baseline division).
    """
    if not rec.get("powered"):
        return {"label": "INCONCLUSIVE", "note": "below reportable power",
                "s_entry": None, "s_exit": None}
    full, entry, exit_ = rec["full"], rec["entry"], rec["exit"]
    if not (xfull_for and full["ci_low"] > 0):
        return {"label": "INCONCLUSIVE", "note": "no significant total to attribute",
                "s_entry": None, "s_exit": None}

    total = full["effect_bps"]
    s_entry = entry["effect_bps"] / total
    s_exit = exit_["effect_bps"] / total
    e_sig, x_sig = entry["leg_significant"], exit_["leg_significant"]
    shares = {"s_entry": s_entry, "s_exit": s_exit}

    def labelled(label: str, note: str) -> dict[str, Any]:
        return {"label": label, "note": note, **shares}

    if e_sig and x_sig:
        if s_entry >= DOMINANCE_CUT:
            return labelled("ENTRY_DOMINANT", "both significant; entry share >= cut")
        if s_exit >= DOMINANCE_CUT:
            return labelled("EXIT_DOMINANT", "both significant; exit share >= cut")
        return labelled("MIXED", "both significant; neither share >= cut")
    if e_sig and not x_sig:
        return labelled("ENTRY_DOMINANT", "exit contribution indistinguishable from 0")
    if x_sig and not e_sig:
        return labelled("EXIT_DOMINANT", "entry contribution indistinguishable from 0")
    # Neither leg leg-significant though X_full is FOR: resolve sign-complete edge cases.
    if entry["effect_bps"] < 0:
        return labelled("EXIT_DOMINANT", "entry leg negative; exit carries >100%")
    if exit_["effect_bps"] < 0:
        return labelled("ENTRY_DOMINANT", "exit rule a differential drag; entry >100%")
    return labelled("MIXED_UNRESOLVED", "real total, split below resolution")


# --------------------------------------------------------------------------- #
# Soft anchors + phase outcome
# --------------------------------------------------------------------------- #
def xfull_for_flags() -> dict[str, bool]:
    """Per-domain EXP-028 X_full EVIDENCE_FOR flag (the total being attributed)."""
    exp028 = load_csv(EXP028_RESULTS / "event_level_results.csv")
    return {str(r["domain"]): str(r["verdict"]) == "EVIDENCE_FOR" for r in exp028.to_dicts()}


def entry_soft_anchor(horizon_recs: dict[int, dict[str, dict[str, Any]]]) -> list[dict[str, Any]]:
    """Compare X_entry(H) effects against EXP-028 secondary sec_h{1,6}_bps (non-gating)."""
    exp028 = load_csv(EXP028_RESULTS / "event_level_results.csv")
    sec = {str(r["domain"]): r for r in exp028.to_dicts()}
    col = {1: "sec_h1_bps", 6: "sec_h6_bps"}
    rows: list[dict[str, Any]] = []
    for h in HORIZONS:
        for domain in DOMAINS:
            rec = horizon_recs[h].get(domain, {})
            if not rec.get("powered"):
                continue
            ref = sec.get(domain, {}).get(col[h])
            x_entry = rec["entry"]["effect_bps"]
            rows.append({"horizon": h, "domain": domain, "x_entry_bps": x_entry,
                         "exp028_sec_bps": ref,
                         "abs_diff_bps": abs(x_entry - float(ref)) if ref is not None else None})
    return rows


def determinism_replay(
    events: pl.DataFrame, controls: pl.DataFrame,
    horizon_recs: dict[int, dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    """Bounded in-process replay: re-run the PRIMARY (5m, H=6) cell and assert identity.

    Fixed ``seed_for`` seeds make the stochastic inference reproducible; this re-builds the
    primary-horizon legs and re-runs the frozen tail for the primary domain, then compares
    leg effect / CI / raw-p against the first pass. Any drift (> 1e-12 bps) flags hidden
    non-determinism. One extra cell of inference — bounded relative to the full run.
    """
    legs = build_legs(events, controls, PRIMARY_HORIZON)
    cell = legs.filter(pl.col("domain") == PRIMARY_DOMAIN)
    insts = reportable_instruments(cell)
    rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "infer", PRIMARY_HORIZON, PRIMARY_DOMAIN))
    replay = {leg: infer_leg(cell, col, insts, rng)
              for leg, col in (("full", "x_full_star"), ("entry", "x_entry"), ("exit", "x_exit"))}
    ref = horizon_recs[PRIMARY_HORIZON][PRIMARY_DOMAIN]
    max_drift = 0.0
    for leg in ("full", "entry", "exit"):
        for key in ("effect_bps", "ci_low", "ci_high", "raw_p"):
            max_drift = max(max_drift, abs(replay[leg][key] - ref[leg][key]))
    return {"cell": f"{PRIMARY_DOMAIN}/H={PRIMARY_HORIZON}", "max_drift_bps": max_drift,
            "passed": bool(max_drift <= 1e-12)}


def phase_outcome(labels_primary: dict[str, str], agreement: dict[str, bool]) -> str:
    """Bind the phase outcome on the primary-domain (5m) resolution + H agreement."""
    primary_label = labels_primary.get(PRIMARY_DOMAIN, "INCONCLUSIVE")
    resolved = primary_label in ("ENTRY_DOMINANT", "EXIT_DOMINANT", "MIXED")
    if resolved and agreement.get(PRIMARY_DOMAIN, False):
        return "ISOLATION_READ_RESOLVED"
    return "ISOLATION_READ_UNRESOLVED"


# --------------------------------------------------------------------------- #
# Plotting (4)
# --------------------------------------------------------------------------- #
def plot_decomposition_stacked(
    horizon_recs: dict[int, dict[str, dict[str, Any]]], path: Path,
) -> None:
    """Per-domain X_full = X_entry + X_exit with CI whiskers, H=6 (primary) vs H=1."""
    fig, axes = plt.subplots(1, len(HORIZONS), figsize=(6 * len(HORIZONS), 5), squeeze=False)
    for col, h in enumerate(sorted(HORIZONS, reverse=True)):
        ax = axes[0, col]
        x = np.arange(len(DOMAINS))
        for k, leg_name, color in ((0, "entry", "#3498db"), (1, "exit", "#e67e22")):
            effs, los, his = [], [], []
            for domain in DOMAINS:
                rec = horizon_recs[h].get(domain, {})
                leg = rec.get(leg_name) if rec.get("powered") else None
                effs.append(leg["effect_bps"] if leg else np.nan)
                los.append((leg["effect_bps"] - leg["ci_low"]) if leg else 0.0)
                his.append((leg["ci_high"] - leg["effect_bps"]) if leg else 0.0)
            ax.bar(x + (k - 0.5) * 0.35, effs, 0.35, yerr=[los, his], capsize=3,
                   label=f"X_{leg_name}", color=color)
        full_eff = [horizon_recs[h][d]["full"]["effect_bps"]
                    if horizon_recs[h].get(d, {}).get("powered") else np.nan for d in DOMAINS]
        ax.scatter(x, full_eff, color="black", marker="D", zorder=5, label="X_full*")
        ax.axhline(0, color="black", lw=0.6)
        ax.set_xticks(x)
        ax.set_xticklabels(DOMAINS)
        ax.set_ylabel("Matched-control excess (bps)")
        ax.set_title(f"H={h}" + (" (PRIMARY)" if h == PRIMARY_HORIZON else " (companion)"))
        ax.legend(fontsize=8)
    fig.suptitle("EXP-031 decomposition: X_full* = X_entry + X_exit", fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_attribution_shares(class_recs: dict[int, dict[str, dict[str, Any]]], path: Path) -> None:
    """Per-domain s_entry / s_exit with the 0.67 dominance band, H=6 vs H=1."""
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(DOMAINS))
    for k, h in enumerate(sorted(HORIZONS, reverse=True)):
        s_entry = [class_recs[h].get(d, {}).get("s_entry") for d in DOMAINS]
        s_entry = [s if s is not None else np.nan for s in s_entry]
        ax.bar(x + (k - 0.5) * 0.35, s_entry, 0.35, label=f"s_entry (H={h})",
               color="#3498db" if h == PRIMARY_HORIZON else "#85c1e9")
    for cut in (DOMINANCE_CUT, 1 - DOMINANCE_CUT):
        ax.axhline(cut, color="#c0392b", ls="--", lw=0.8)
    ax.axhline(1.0, color="black", lw=0.5)
    ax.axhline(0.0, color="black", lw=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(DOMAINS)
    ax.set_ylabel("Entry share of X_full*  (s_exit = 1 - s_entry)")
    ax.set_title("EXP-031 attribution shares (dominance band 0.67 / 0.33)", fontweight="bold")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_exit_substitution(subst_rows: list[dict[str, Any]], path: Path) -> None:
    """Event vs control mean exit-substitution effect dH = BTC - FH(H), per domain (H=6)."""
    by_domain = {r["domain"]: r for r in subst_rows if r["horizon"] == PRIMARY_HORIZON}
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(DOMAINS))
    ev = [by_domain.get(d, {}).get("event_mean_dH_bps", np.nan) for d in DOMAINS]
    ct = [by_domain.get(d, {}).get("control_mean_dH_bps", np.nan) for d in DOMAINS]
    ax.bar(x - 0.2, ev, 0.4, label="Event dH = BTC - FH", color="#9b59b6")
    ax.bar(x + 0.2, ct, 0.4, label="Control dH = BTC - FH", color="#95a5a6")
    ax.axhline(0, color="black", lw=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels(DOMAINS)
    ax.set_ylabel(f"Mean exit-substitution effect (bps), H={PRIMARY_HORIZON}")
    ax.set_title("EXP-031 exit-substitution: how much the BTC exit adds over neutral exit",
                 fontweight="bold")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_attribution_summary(
    class_recs: dict[int, dict[str, dict[str, Any]]], agreement: dict[str, bool], path: Path,
) -> None:
    """Per-domain label dashboard: H=6 label, H=1 label, agreement flag."""
    fig, ax = plt.subplots(figsize=(11, 0.9 * len(DOMAINS) + 1.5))
    ax.axis("off")
    rows = [["Domain", f"H={PRIMARY_HORIZON} (PRIMARY)", f"H={COMPANION_HORIZON}", "Agree"]]
    for d in DOMAINS:
        p = class_recs[PRIMARY_HORIZON].get(d, {})
        c = class_recs[COMPANION_HORIZON].get(d, {})
        rows.append([d + (" *" if d == PRIMARY_DOMAIN else ""),
                     p.get("label", "n/a"), c.get("label", "n/a"),
                     "yes" if agreement.get(d) else "no"])
    table = ax.table(cellText=rows, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.6)
    for j in range(len(rows[0])):
        table[(0, j)].set_facecolor("#34495e")
        table[(0, j)].set_text_props(color="white", fontweight="bold")
    ax.set_title("EXP-031 attribution summary (primary domain marked *)", fontweight="bold", pad=20)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Exit-substitution diagnostic (mechanism behind X_exit)
# --------------------------------------------------------------------------- #
def exit_substitution_rows(events: pl.DataFrame, controls: pl.DataFrame) -> list[dict[str, Any]]:
    """Per-domain mean dH = BTC - FH(H) for events vs controls (instrument-averaged)."""
    rows: list[dict[str, Any]] = []
    for h in HORIZONS:
        fh = f"fh_{h}"
        ev = events.filter(pl.col(fh).is_finite()).with_columns(
            (pl.col("lifetime_bps") - pl.col(fh)).alias("dH"))
        ct = controls.filter(pl.col(fh).is_finite()).with_columns(
            (pl.col("lifetime_bps") - pl.col(fh)).alias("dH"))
        for domain in DOMAINS:
            ev_d = ev.filter(pl.col("domain") == domain)
            ct_d = ct.filter(pl.col("domain") == domain)
            rows.append({
                "horizon": h, "domain": domain,
                "event_mean_dH_bps": _inst_avg(ev_d, "dH"),
                "control_mean_dH_bps": _inst_avg(ct_d, "dH"),
                "n_event": ev_d.height, "n_control": ct_d.height,
            })
    return rows


def _inst_avg(cell: pl.DataFrame, col: str) -> float:
    """Equal-weight mean across instruments of each instrument's mean of ``col``."""
    if cell.height == 0:
        return float("nan")
    vals = cell.get_column(col).to_numpy().astype(float)
    insts = cell.get_column("instrument").to_numpy()
    return domain_effect(vals, insts, [i for i in INSTRUMENTS if (insts == i).any()])


# --------------------------------------------------------------------------- #
# Save outputs
# --------------------------------------------------------------------------- #
def _leg_cols(leg: dict[str, Any] | None) -> dict[str, Any]:
    """Flatten a leg block into prefixed CSV columns."""
    if not leg:
        return {k: None for k in ("effect_bps", "ci_low", "ci_high", "ci_half_width",
                                  "raw_p", "holm_p", "leg_significant")}
    return {k: leg.get(k) for k in ("effect_bps", "ci_low", "ci_high", "ci_half_width",
                                    "raw_p", "holm_p", "leg_significant")}


def save_outputs(horizon_recs, class_recs, agreement, recon_rows, subst_rows,
                 by_inst_rows, soft_rows, metadata) -> None:
    """Write all result CSVs, plots, and run metadata."""
    ensure_output_dirs()
    decomp_rows: list[dict[str, Any]] = []
    for h in HORIZONS:
        for domain in DOMAINS:
            rec = horizon_recs[h].get(domain, {})
            cls = class_recs[h].get(domain, {})
            base = {"horizon": h, "domain": domain, "powered": rec.get("powered", False),
                    "n_events": rec.get("n_events"), "n_bull": rec.get("n_bull"),
                    "n_bear": rec.get("n_bear"), "n_instruments": rec.get("n_instruments"),
                    "additivity_residual_bps": rec.get("additivity_residual"),
                    "label": cls.get("label"), "note": cls.get("note"),
                    "s_entry": cls.get("s_entry"), "s_exit": cls.get("s_exit")}
            for leg_name in ("full", "entry", "exit"):
                for k, v in _leg_cols(rec.get(leg_name)).items():
                    base[f"{leg_name}_{k}"] = v
            decomp_rows.append(base)
    write_rows(RESULTS_DIR / "decomposition_results.csv", decomp_rows)
    write_rows(RESULTS_DIR / "decomposition_by_instrument.csv", by_inst_rows)
    write_rows(RESULTS_DIR / "xfull_reconciliation.csv", recon_rows)
    write_rows(RESULTS_DIR / "exit_substitution.csv", subst_rows)
    write_rows(RESULTS_DIR / "entry_soft_anchor.csv", soft_rows)
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(metadata, indent=2, default=str))

    plot_decomposition_stacked(horizon_recs, PLOTS_DIR / "decomposition_stacked.png")
    plot_attribution_shares(class_recs, PLOTS_DIR / "attribution_shares.png")
    plot_exit_substitution(subst_rows, PLOTS_DIR / "exit_substitution.png")
    plot_attribution_summary(class_recs, agreement, PLOTS_DIR / "attribution_summary.png")
    LOGGER.info("Wrote results to %s and plots to %s", RESULTS_DIR, PLOTS_DIR)


def by_instrument_rows(horizon: int, legs: pl.DataFrame) -> list[dict[str, Any]]:
    """Instrument-level leg point effects (no inference) for the given horizon."""
    rows: list[dict[str, Any]] = []
    for domain in DOMAINS:
        for inst in INSTRUMENTS:
            sub = legs.filter((pl.col("domain") == domain) & (pl.col("instrument") == inst))
            if sub.height == 0:
                continue
            rows.append({
                "horizon": horizon, "domain": domain, "instrument": inst, "n_events": sub.height,
                "x_full_star_bps": float(sub.get_column("x_full_star").mean()),
                "x_entry_bps": float(sub.get_column("x_entry").mean()),
                "x_exit_bps": float(sub.get_column("x_exit").mean()),
            })
    return rows


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    configure_logging()
    LOGGER.info("=" * 70)
    LOGGER.info("EXP-031: AVWAP Edge Isolation (Entry-Timing vs Exit-Rule)")
    LOGGER.info("=" * 70)
    ensure_output_dirs()

    frozen_hash = verify_frozen_inference()
    deps = check_dependencies()

    LOGGER.info("Rebuilding domain frames (EXP-020 convention, holdout-fenced)")
    log_close, metadata_rows = build_cell_log_close()
    metadata_checks = validate_analysis_metadata(metadata_rows)

    LOGGER.info("Loading EXP-022 lifetime population (EXP-028 PRIMARY set, pyramids included)")
    lifetime = load_csv(EXP022_RESULTS / "lifetime_observations.csv")
    events, controls = split_population(lifetime)
    events, ev_base_bad = add_fixed_horizon_returns(events, log_close)
    controls, ct_base_bad = add_fixed_horizon_returns(controls, log_close)
    if ev_base_bad or ct_base_bad:
        raise ValueError(
            f"start_close/base-bar misalignment: events={ev_base_bad}, controls={ct_base_bad} "
            "(domain rebuild does not reproduce the EXP-020/022 substrate)."
        )

    LOGGER.info("Reconciling X_full against EXP-028 PRIMARY (hard anchor)")
    full_excess = full_xfull_excess(events, controls)
    recon_rows, recon_pass = reconcile_xfull(full_excess)
    for r in recon_rows:
        LOGGER.info("  %s X_full rebuilt=%.4f exp028=%.4f abs=%.4f rel=%.5f -> %s", r["domain"],
                    r["rebuilt_effect_bps"] or float("nan"), r["exp028_effect_bps"] or float("nan"),
                    r["abs_diff_bps"] or float("nan"), r["rel_diff"] or float("nan"),
                    "PASS" if r["passed"] else "FAIL")
    if not recon_pass:
        raise ValueError(
            "X_FULL_RECONCILIATION_FAILED: rebuilt X_full does not reproduce EXP-028 PRIMARY "
            "within tolerance; decomposition substrate is mis-wired (REVISE-blocked)."
        )

    LOGGER.info("Building legs + frozen-tail inference per horizon")
    for_flags = xfull_for_flags()
    horizon_recs: dict[int, dict[str, dict[str, Any]]] = {}
    class_recs: dict[int, dict[str, dict[str, Any]]] = {}
    by_inst_all: list[dict[str, Any]] = []
    max_residual = 0.0
    for h in tqdm(HORIZONS, desc="horizons"):
        legs = build_legs(events, controls, h)
        horizon_recs[h] = infer_horizon(legs, h)
        class_recs[h] = {d: classify_domain(horizon_recs[h].get(d, {}), for_flags.get(d, False))
                         for d in DOMAINS}
        by_inst_all.extend(by_instrument_rows(h, legs))
        for d in DOMAINS:
            res = horizon_recs[h][d].get("additivity_residual")
            if res is not None:
                max_residual = max(max_residual, res)
    if max_residual > 1e-6:
        raise ValueError(
            f"ADDITIVITY_VIOLATION: domain residual {max_residual:.2e} bps exceeds 1e-6.")

    LOGGER.info("Determinism replay (primary cell)")
    replay = determinism_replay(events, controls, horizon_recs)
    LOGGER.info("  replay %s max_drift=%.2e bps -> %s", replay["cell"], replay["max_drift_bps"],
                "PASS" if replay["passed"] else "FAIL")
    if not replay["passed"]:
        raise ValueError(
            f"DETERMINISM_REPLAY_FAILED: {replay['cell']} drifted "
            f"{replay['max_drift_bps']:.2e} bps between identical-seed passes.")

    LOGGER.info("Exit-substitution diagnostic + soft anchors")
    subst_rows = exit_substitution_rows(events, controls)
    soft_rows = entry_soft_anchor(horizon_recs)

    # H=1 vs H=6 label agreement (resolved labels must coincide to count as resolved).
    agreement = {d: class_recs[PRIMARY_HORIZON].get(d, {}).get("label")
                 == class_recs[COMPANION_HORIZON].get(d, {}).get("label") for d in DOMAINS}
    labels_primary = {d: class_recs[PRIMARY_HORIZON].get(d, {}).get("label") for d in DOMAINS}
    outcome = phase_outcome(labels_primary, agreement)

    metadata = {
        "experiment": EXPERIMENT_ID,
        "title": "AVWAP Edge Isolation (Entry-Timing vs Exit-Rule)",
        "phase_outcome": outcome,
        "primary_domain": PRIMARY_DOMAIN,
        "primary_horizon": PRIMARY_HORIZON,
        "companion_horizon": COMPANION_HORIZON,
        "labels_primary_horizon": labels_primary,
        "labels_companion_horizon": {
            d: class_recs[COMPANION_HORIZON].get(d, {}).get("label") for d in DOMAINS},
        "h_agreement": agreement,
        "shares_primary_horizon": {
            d: {"s_entry": class_recs[PRIMARY_HORIZON].get(d, {}).get("s_entry"),
                "s_exit": class_recs[PRIMARY_HORIZON].get(d, {}).get("s_exit")}
            for d in DOMAINS},
        "xfull_reconciliation_pass": recon_pass,
        "determinism_replay": replay,
        "max_additivity_residual_bps": max_residual,
        "base_close_mismatches": {"events": ev_base_bad, "controls": ct_base_bad},
        "domain_metadata_cells_checked": len(metadata_checks),
        "dependencies": deps,
        "frozen_inference_hash": frozen_hash,
        "dominance_cut": DOMINANCE_CUT,
        "parameters": {"domains": list(DOMAINS), "instruments": list(INSTRUMENTS),
                       "horizons": list(HORIZONS), "alpha": ALPHA, "n_boot": N_BOOT,
                       "n_perm": N_PERM, "chunk": CHUNK, "min_controls": MIN_CONTROLS,
                       "min_reportable_events": MIN_REPORTABLE_EVENTS,
                       "min_direction_events": MIN_DIRECTION_EVENTS,
                       "recon_abs_tol_bps": RECON_ABS_TOL_BPS, "recon_rel_tol": RECON_REL_TOL},
        "scope_bounds": ("GROSS mechanism decomposition; costs/slippage out of scope (EXP-030). "
                         "No horizon sweep; H in {1,6} frozen a priori; H=6 PRIMARY. "
                         "Holdout never loaded."),
    }
    save_outputs(horizon_recs, class_recs, agreement, recon_rows, subst_rows,
                 by_inst_all, soft_rows, metadata)

    LOGGER.info("=" * 70)
    LOGGER.info("Phase outcome: %s", outcome)
    for d in DOMAINS:
        LOGGER.info("  %s  H=%d label=%s (s_entry=%s)  | H=%d label=%s | agree=%s",
                    d, PRIMARY_HORIZON, labels_primary[d],
                    class_recs[PRIMARY_HORIZON].get(d, {}).get("s_entry"),
                    COMPANION_HORIZON, class_recs[COMPANION_HORIZON].get(d, {}).get("label"),
                    agreement[d])
    LOGGER.info("=" * 70)


if __name__ == "__main__":
    main()
