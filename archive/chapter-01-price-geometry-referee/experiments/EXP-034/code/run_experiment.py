"""Experiment EXP-034: Per-Instrument Cost-Bearing Tradability Screen (with Financing).

Implements analysis-plan.md / scope.md (Phase 008, Tier A1). A deterministic overlay on
the EXP-030 substrate: the EXP-028 PRIMARY event set (EXP-022 ``lifetime_observations``,
``role=event``, pyramids included) bears the frozen CONSERVATIVE round-trip costs PLUS a
predeclared per-event financing charge

    financing_e = rate_i * elapsed_calendar_days(trigger_close_time, completion_close_time)

with fractional calendar days from the rebuilt domain-bar timestamps. The binding test is
the D0-fixed FIXED-SEQUENCE walk over the declared family — EURUSD-4h (primary) ->
USTEC-4h -> XAUUSD-1h, each at one-sided alpha = 0.05, stop at first failure (FWER 0.05;
replaces Holm per D0 §1.2). Cell PASS requires the dual rule: bootstrap p <= alpha AND
net CI_low > 0. All 12 instrument x domain cells get descriptive CIs (non-binding).

Integrity guards (all hard-fail before any verdict):
  * frozen EXP-027 inference tail matches the PINNED hash (e50873d12a9f68d9);
  * per-cell event counts reproduce EXP-030 ``net_by_instrument.csv`` exactly;
  * the NO-financing per-cell net reproduces EXP-030 ``net_cons_bps`` to <= 0.01 bps
    (proves the only new computation is the financing layer);
  * rebuilt domain bars reproduce EXP-020 analysis metadata (timestamp provenance);
  * ``start_close`` reproduces the rebuilt base bar (index->timestamp alignment);
  * financing helper self-check (hand-computed cases incl. a weekend span).

The final 30% global holdout is never loaded (fence inside the lazy loader). No cost or
financing constant may be revisited after this run. Zero-baseline: absolute bps vs 0.

Run:
    cd <project-root> && python python/experiments/EXP-034/code/run_experiment.py
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
EXPERIMENT_ID = "EXP-034"
DATA_DIR = PROJECT_ROOT / "data"
EXP_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"

EXP020_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-020" / "results"
EXP022_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-022" / "results"
EXP028_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-028" / "results"
EXP030_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-030" / "results"

DOMAINS: tuple[str, ...] = ("5m", "1h", "4h")
INSTRUMENTS: tuple[str, ...] = ("BTCUSD", "EURUSD", "USTEC", "XAUUSD")

# FROZEN EXP-030 CONSERVATIVE round-trip costs (bps; binding variant).
RT_CONS_BPS: dict[str, float] = {"EURUSD": 3.0, "USTEC": 5.0, "XAUUSD": 6.0, "BTCUSD": 16.0}

# PREDECLARED financing rates (bps per calendar day, adverse-side; frozen at scope
# approval — operator-amendable only before this run, never after a result is read).
FINANCING_RATE_BPS_PER_DAY: dict[str, float] = {
    "EURUSD": 0.6, "USTEC": 1.2, "XAUUSD": 1.2, "BTCUSD": 10.0,
}

# D0 §1.1-1.2: declared family in FIXED-SEQUENCE testing order (FWER = ALPHA).
DECLARED_SEQUENCE: tuple[tuple[str, str], ...] = (
    ("EURUSD", "4h"), ("USTEC", "4h"), ("XAUUSD", "1h"),
)
# Exact expected populations (EXP-030 reconciliation; drift = hard stop).
EXPECTED_N: dict[tuple[str, str], int] = {
    ("EURUSD", "4h"): 39, ("USTEC", "4h"): 36, ("XAUUSD", "1h"): 207,
}

# EXP-028 PRIMARY population construction (identical to EXP-030).
COMPLETED_OUTCOMES = ("favorable", "adverse", "trend_change")
JOIN_KEYS = ("instrument", "domain", "regime_id", "direction", "event_trigger_idx")
MIN_CONTROLS = EM.MIN_CONTROLS

# Inference convention (matches EXP-030).
N_BOOT = 1000
CHUNK = 200
ALPHA = 0.05
CI_PERCENTILES = (2.5, 97.5)
N_SEEDS_ROBUST = 8

# Tolerances.
RECON_NET_TOL_BPS = 0.01           # no-financing net vs EXP-030 net_cons_bps
RECON_CI_TOL_BPS = 1e-6            # no-financing CI vs EXP-030 (same seed => same draws)
START_CLOSE_RTOL = 1e-9            # start_close vs rebuilt base bar
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
    """Assert EXP-028 EVAL_SUPPORTED and the EXP-030/EXP-022 artifacts exist."""
    exp028 = load_json(EXP028_RESULTS / "run_metadata.json")
    v028 = str(exp028.get("overall_verdict", ""))
    if v028 != "EVAL_SUPPORTED":
        raise ValueError(f"EXP-028 overall_verdict must be EVAL_SUPPORTED, got {v028!r}")
    for artifact in (EXP022_RESULTS / "lifetime_observations.csv",
                     EXP030_RESULTS / "net_by_instrument.csv",
                     EXP020_RESULTS / "analysis_metadata.csv"):
        if not artifact.exists():
            raise FileNotFoundError(f"missing dependency artifact: {artifact}")
    LOGGER.info("Dependency gate PASS (EXP-028=%s; EXP-030/EXP-022 artifacts present)", v028)
    return {"EXP-028": v028, "EXP-030": "present", "EXP-022": "present"}


# --------------------------------------------------------------------------- #
# Domain rebuild (Close + CloseTime) + holdout-safe metadata guard
# --------------------------------------------------------------------------- #
def expected_timebar_sources() -> set[str]:
    """Canonical source Parquet filenames recorded by EXP-020 metadata (mirrors EXP-031)."""
    expected = pl.read_csv(EXP020_RESULTS / "analysis_metadata.csv")
    return set(expected.get_column("source_file").unique().to_list())


def build_cell_series() -> tuple[dict[tuple[str, str], dict[str, np.ndarray]], list[dict[str, Any]]]:
    """Rebuild first-70% 5m/1h/4h domain bars; return per-cell Close + CloseTime arrays.

    Same loader/fence as EXP-020/022/031 (``xen.referee_calibration``), so domain-bar
    indices align with ``start_idx``/``completion_idx`` by construction. CloseTime is
    needed here (unlike EXP-031) because financing duration is calendar time.
    """
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
            series[(data.instrument, domain)] = {"close": close, "close_time": ct}
            metadata_rows.append({
                "instrument": data.instrument, "domain": domain,
                "source_file": data.source_file, "source_total_rows": data.total_rows,
                "analysis_rows_1m": data.analysis_rows, "analysis_start_1m": data.analysis_start,
                "analysis_end_1m": data.analysis_end, "domain_bars": frame.height,
                "domain_min_close_time": str(frame.get_column("CloseTime").min()),
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
# Event table (EXP-030 construction, verbatim semantics) + cost/financing overlay
# --------------------------------------------------------------------------- #
def build_event_table(lifetime: pl.DataFrame) -> pl.DataFrame:
    """EXP-028/030 PRIMARY event set: completed reportable events, >= MIN_CONTROLS controls.

    Identical filtering to EXP-030 ``build_event_table``; additionally retains
    ``start_idx``/``completion_idx``/``start_close`` for the financing timestamps.
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
    out = merged.select(
        "instrument", "domain", "regime_id", "direction", "is_pyramid_bounce",
        "start_idx", "completion_idx", "start_close", "lifetime_bps", "n_controls_finite",
    )
    LOGGER.info("Event set: %d rows (EXP-028 PRIMARY population)", out.height)
    return out


def attach_costs_and_financing(
    table: pl.DataFrame, series: dict[tuple[str, str], dict[str, np.ndarray]],
) -> pl.DataFrame:
    """Attach RT costs, per-event financing from rebuilt timestamps, and net columns.

    Per event: entry = CloseTime[start_idx], exit = CloseTime[completion_idx] on the
    rebuilt series (fractional calendar days, weekends included). Hard-fails if any
    index is out of range or ``start_close`` does not reproduce the rebuilt base bar
    (index->timestamp alignment integrity).
    """
    si = table.get_column("start_idx").to_numpy().astype(np.int64)
    ci = table.get_column("completion_idx").to_numpy().astype(np.int64)
    sc = table.get_column("start_close").to_numpy().astype(float)
    inst = table.get_column("instrument").to_numpy()
    dom = table.get_column("domain").to_numpy()
    n = table.height
    entry_dt = np.full(n, np.datetime64("NaT"), dtype="datetime64[ns]")
    exit_dt = np.full(n, np.datetime64("NaT"), dtype="datetime64[ns]")
    base_bad = 0
    for (i, dm), arrs in series.items():
        rows = np.flatnonzero((inst == i) & (dom == dm))
        if rows.size == 0:
            continue
        close, ct = arrs["close"], arrs["close_time"]
        s, c = si[rows], ci[rows]
        if (s < 0).any() or (s >= close.size).any() or (c < 0).any() or (c >= close.size).any():
            raise ValueError(f"index out of analysis-slice range for {i}/{dm}")
        tol = START_CLOSE_RTOL * sc[rows]
        base_bad += int(np.sum(np.abs(close[s] - sc[rows]) > tol))
        entry_dt[rows] = ct[s]
        exit_dt[rows] = ct[c]
    if base_bad:
        raise ValueError(f"start_close mismatch vs rebuilt base bar in {base_bad} rows")
    if np.isnat(entry_dt).any() or np.isnat(exit_dt).any():
        missing = int(np.isnat(entry_dt).sum() + np.isnat(exit_dt).sum())
        raise ValueError(f"holding timestamps unresolved for {missing} rows (missing cell series)")
    rates = np.array([FINANCING_RATE_BPS_PER_DAY[i] for i in inst], dtype=float)
    # Shared live path (F03): the same helper verify_financing() exercises.
    holding_days = elapsed_calendar_days(entry_dt, exit_dt)
    fin = financing_bps(rates, entry_dt, exit_dt)
    out = table.with_columns([
        pl.Series("holding_days", holding_days),
        pl.Series("financing_bps", fin),
        pl.Series("rt_cons", np.array([RT_CONS_BPS[i] for i in inst], dtype=float)),
    ]).with_columns([
        (pl.col("lifetime_bps") - pl.col("rt_cons")).alias("net_nofin"),
        (pl.col("lifetime_bps") - pl.col("rt_cons") - pl.col("financing_bps")).alias("net"),
    ])
    LOGGER.info("Cost + financing overlay attached (%d rows)", out.height)
    return out


# --------------------------------------------------------------------------- #
# Reconciliation vs EXP-030 (hard gate)
# --------------------------------------------------------------------------- #
def reconcile_vs_exp030(table: pl.DataFrame) -> list[dict[str, Any]]:
    """All 12 cells: counts exact + no-financing net <= 0.01 bps; declared cells: CI too.

    F04 extension: for the declared cells, the verdict-bearing quantity is a
    regime-cluster bootstrap CI. EXP-034's no-financing bootstrap, run with
    EXP-030's own seed payload (``seed_for("EXP-030", "perinst", domain, inst)``),
    must reproduce EXP-030 ``net_cons_ci_low/high`` to RECON_CI_TOL_BPS — proving
    this script's single-instrument estimator is the same construction whose
    half-widths the predeclared power statement borrowed. Hard-fail otherwise.
    """
    ref = pl.read_csv(EXP030_RESULTS / "net_by_instrument.csv")
    ref_by_cell = {(str(r["instrument"]), str(r["domain"])): r for r in ref.to_dicts()}
    rows: list[dict[str, Any]] = []
    for inst in INSTRUMENTS:
        for domain in DOMAINS:
            sub = table.filter((pl.col("instrument") == inst) & (pl.col("domain") == domain))
            exp = ref_by_cell.get((inst, domain))
            if exp is None:
                raise ValueError(f"cell {inst}/{domain} missing from EXP-030 net_by_instrument")
            n_ok = sub.height == int(exp["n_events"])
            net_nofin = float(sub.get_column("net_nofin").mean()) if sub.height else float("nan")
            net_ok = abs(net_nofin - float(exp["net_cons_bps"])) <= RECON_NET_TOL_BPS
            row: dict[str, Any] = {
                "instrument": inst, "domain": domain, "n_events": sub.height,
                "exp030_n_events": int(exp["n_events"]), "count_match": n_ok,
                "net_nofin_bps": net_nofin, "exp030_net_cons_bps": float(exp["net_cons_bps"]),
                "abs_diff_bps": abs(net_nofin - float(exp["net_cons_bps"])),
                "net_match": net_ok, "ci_match": None,
            }
            if (inst, domain) in EXPECTED_N and sub.height:
                diffs = sub.get_column("net_nofin").to_numpy().astype(float)
                inst_labels = sub.get_column("instrument").to_numpy()
                dir_labels = sub.get_column("direction").to_numpy().astype(int)
                regime_labels = sub.get_column("regime_id").to_numpy().astype(int)
                strata = build_strata(diffs, inst_labels, dir_labels, regime_labels, [inst])
                rng = np.random.default_rng(seed_for("EXP-030", "perinst", domain, inst))
                boot = bootstrap_effect_distribution(strata, [inst], rng, N_BOOT, CHUNK)
                ci_low = float(np.percentile(boot, CI_PERCENTILES[0]))
                ci_high = float(np.percentile(boot, CI_PERCENTILES[1]))
                ci_dev = max(abs(ci_low - float(exp["net_cons_ci_low"])),
                             abs(ci_high - float(exp["net_cons_ci_high"])))
                row.update({"nofin_ci_low": ci_low, "nofin_ci_high": ci_high,
                            "exp030_ci_low": float(exp["net_cons_ci_low"]),
                            "exp030_ci_high": float(exp["net_cons_ci_high"]),
                            "ci_abs_dev_bps": ci_dev,
                            "ci_match": bool(ci_dev <= RECON_CI_TOL_BPS)})
            row["passed"] = bool(n_ok and net_ok and (row["ci_match"] is not False))
            rows.append(row)
    failures = [f"{r['instrument']}/{r['domain']}" for r in rows if not r["passed"]]
    if failures:
        raise ValueError(f"EXP-030 RECONCILIATION FAILED for cells: {failures}")
    LOGGER.info("Reconciliation PASS: 12 cells reproduce EXP-030 (counts exact, net <= "
                "%.2f bps; declared-cell CIs <= %.2g bps)", RECON_NET_TOL_BPS, RECON_CI_TOL_BPS)
    return rows


# --------------------------------------------------------------------------- #
# Pure computation: single-cell frozen-tail inference (absolute estimand)
# --------------------------------------------------------------------------- #
def infer_single_cell(sub: pl.DataFrame, inst: str, rng: np.random.Generator) -> dict[str, Any]:
    """Effect, regime-cluster bootstrap CIs, and one-sided bootstrap p for one cell.

    Single-instrument specialization of the frozen tail: ``domain_effect`` with one
    instrument is the event-weighted mean; strata are that instrument's two direction
    strata with regime clusters as resampling units. Bootstrap p tests ``mean > 0``
    via ``(1 + #{boot <= 0}) / (1 + N_BOOT)`` (the EXP-030 absolute-estimand
    substitution; sign-permutation is invalid for a non-paired mean).

    Two lower bounds are reported (F01): ``ci_low_1s`` — the ONE-SIDED 95% lower
    confidence bound (5th bootstrap percentile) — is the BINDING bound matching the
    declared one-sided alpha = 0.05 (``ci_low_1s > 0`` and ``boot_p <= 0.05`` agree
    up to percentile interpolation); ``ci_low`` — the two-sided 95% bound (2.5th
    percentile) — is descriptive, for comparability with the EXP-030 record.
    """
    diffs = sub.get_column("net").to_numpy().astype(float)
    inst_labels = sub.get_column("instrument").to_numpy()
    dir_labels = sub.get_column("direction").to_numpy().astype(int)
    regime_labels = sub.get_column("regime_id").to_numpy().astype(int)
    effect = domain_effect(diffs, inst_labels, [inst])
    strata = build_strata(diffs, inst_labels, dir_labels, regime_labels, [inst])
    boot = bootstrap_effect_distribution(strata, [inst], rng, N_BOOT, CHUNK)
    ci_low = float(np.percentile(boot, CI_PERCENTILES[0]))
    ci_high = float(np.percentile(boot, CI_PERCENTILES[1]))
    ci_low_1s = float(np.percentile(boot, 100.0 * ALPHA))
    boot_p = float((1 + int(np.sum(boot <= 0.0))) / (1 + N_BOOT))
    return {
        "n_events": sub.height,
        "n_bull": sub.filter(pl.col("direction") == 1).height,
        "n_bear": sub.filter(pl.col("direction") == -1).height,
        "effect_bps": effect, "ci_low": ci_low, "ci_high": ci_high,
        "ci_low_1s": ci_low_1s,
        "ci_half_width": (ci_high - ci_low) / 2.0, "boot_p": boot_p,
    }


def run_all_cells(table: pl.DataFrame) -> dict[tuple[str, str], dict[str, Any]]:
    """Per-cell inference on net for all 12 cells (declared = binding; rest descriptive)."""
    results: dict[tuple[str, str], dict[str, Any]] = {}
    cells = [(i, d) for i in INSTRUMENTS for d in DOMAINS]
    for inst, domain in tqdm(cells, desc="per-cell inference"):
        sub = table.filter((pl.col("instrument") == inst) & (pl.col("domain") == domain))
        if sub.height == 0:
            continue
        rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "cell", domain, inst))
        res = infer_single_cell(sub, inst, rng)
        res["declared"] = (inst, domain) in EXPECTED_N
        res["gross_abs_bps"] = float(sub.get_column("lifetime_bps").mean())
        res["mean_financing_bps"] = float(sub.get_column("financing_bps").mean())
        res["net_nofin_bps"] = float(sub.get_column("net_nofin").mean())
        results[(inst, domain)] = res
    return results


# --------------------------------------------------------------------------- #
# Fixed-sequence verdict walk (D0 §1.2, LOCKED)
# --------------------------------------------------------------------------- #
def fixed_sequence_walk(
    cell_results: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    """Walk the declared family in order; stop at first failure; label every cell.

    BINDING PASS (F01): ``boot_p <= ALPHA AND ci_low_1s > 0`` — a genuine one-sided
    alpha = 0.05 test via the one-sided 95% lower bootstrap bound (5th percentile),
    matching the declared level and the D0 §1.2 test-choice rationale. The two-sided
    95% CI drives the DESCRIPTIVE label only (EXP-030 comparability):
    EVIDENCE_FOR (ci_low > 0), EVIDENCE_AGAINST (ci_high < 0),
    INCONCLUSIVE_SPANS_ZERO otherwise. A tested cell's verdict is
    SEQUENCE_PASS_ALPHA05 when the binding rule passes, else its descriptive label;
    unreached cells -> NOT_TESTED_SEQUENCE. The lenient G1 continuation flag
    (point > 0 AND CI not entirely below 0) is independent of sequence position.
    """
    rows: list[dict[str, Any]] = []
    sequence_alive = True
    for order, (inst, domain) in enumerate(DECLARED_SEQUENCE, start=1):
        res = cell_results[(inst, domain)]
        if res["n_events"] != EXPECTED_N[(inst, domain)]:
            raise ValueError(f"declared cell {inst}/{domain} population drifted: "
                             f"{res['n_events']} != {EXPECTED_N[(inst, domain)]}")
        dual_pass = bool(res["boot_p"] <= ALPHA and res["ci_low_1s"] > 0.0)
        if res["ci_low"] > 0.0:
            descriptive = "EVIDENCE_FOR"
        elif res["ci_high"] < 0.0:
            descriptive = "EVIDENCE_AGAINST"
        else:
            descriptive = "INCONCLUSIVE_SPANS_ZERO"
        tested = sequence_alive
        sequence_pass = bool(tested and dual_pass)
        verdict = ("SEQUENCE_PASS_ALPHA05" if sequence_pass
                   else descriptive if tested else "NOT_TESTED_SEQUENCE")
        rows.append({
            "sequence_order": order, "instrument": inst, "domain": domain,
            "tested_in_sequence": tested,
            "verdict": verdict,
            "descriptive_label": descriptive,
            "sequence_pass": sequence_pass,
            "effect_bps": res["effect_bps"], "ci_low": res["ci_low"],
            "ci_high": res["ci_high"], "ci_low_1s": res["ci_low_1s"],
            "boot_p": res["boot_p"],
            "n_events": res["n_events"],
            "g1_lenient_continuation": bool(res["effect_bps"] > 0 and res["ci_high"] > 0),
        })
        if sequence_alive and not dual_pass:
            sequence_alive = False
    return rows


# --------------------------------------------------------------------------- #
# Disclosures: financing context + seed robustness
# --------------------------------------------------------------------------- #
def financing_disclosure(table: pl.DataFrame) -> list[dict[str, Any]]:
    """Per-cell holding-duration and financing context (descriptive)."""
    rows: list[dict[str, Any]] = []
    for inst in INSTRUMENTS:
        for domain in DOMAINS:
            sub = table.filter((pl.col("instrument") == inst) & (pl.col("domain") == domain))
            if sub.height == 0:
                continue
            hd = sub.get_column("holding_days").to_numpy()
            fin = sub.get_column("financing_bps").to_numpy()
            total_cost = RT_CONS_BPS[inst] + float(fin.mean())
            rows.append({
                "instrument": inst, "domain": domain, "n_events": sub.height,
                "median_holding_days": float(np.median(hd)),
                "p25_holding_days": float(np.percentile(hd, 25)),
                "p75_holding_days": float(np.percentile(hd, 75)),
                "mean_financing_bps": float(fin.mean()),
                "max_financing_bps": float(fin.max()),
                "financing_share_of_cost": float(fin.mean()) / total_cost if total_cost else 0.0,
            })
    return rows


def seed_robustness(table: pl.DataFrame) -> list[dict[str, Any]]:
    """CI-boundary stability across N_SEEDS_ROBUST seeds for the declared cells."""
    rows: list[dict[str, Any]] = []
    for inst, domain in tqdm(DECLARED_SEQUENCE, desc="seed robustness"):
        sub = table.filter((pl.col("instrument") == inst) & (pl.col("domain") == domain))
        lows, highs = [], []
        lows_1s = []
        for k in range(N_SEEDS_ROBUST):
            rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "robust", domain, inst, k))
            res = infer_single_cell(sub, inst, rng)
            lows.append(res["ci_low"])
            highs.append(res["ci_high"])
            lows_1s.append(res["ci_low_1s"])
        rows.append({
            "instrument": inst, "domain": domain, "n_seeds": N_SEEDS_ROBUST,
            "ci_low_min": min(lows), "ci_low_max": max(lows),
            "ci_high_min": min(highs), "ci_high_max": max(highs),
            "ci_low_1s_min": min(lows_1s), "ci_low_1s_max": max(lows_1s),
            "ci_low_sign_stable": bool(all(v > 0 for v in lows) or all(v <= 0 for v in lows)),
            "ci_low_1s_sign_stable": bool(all(v > 0 for v in lows_1s)
                                          or all(v <= 0 for v in lows_1s)),
        })
    return rows


def determinism_replay(table: pl.DataFrame,
                       cell_results: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    """Re-run the primary declared cell with its original seed; assert exact identity."""
    inst, domain = DECLARED_SEQUENCE[0]
    sub = table.filter((pl.col("instrument") == inst) & (pl.col("domain") == domain))
    rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "cell", domain, inst))
    replay = infer_single_cell(sub, inst, rng)
    ref = cell_results[(inst, domain)]
    max_drift = max(abs(replay[k] - ref[k])
                    for k in ("effect_bps", "ci_low", "ci_high", "ci_low_1s", "boot_p"))
    return {"cell": f"{inst}/{domain}", "max_drift": max_drift,
            "passed": bool(max_drift <= DETERMINISM_TOL)}


# --------------------------------------------------------------------------- #
# Plotting (3)
# --------------------------------------------------------------------------- #
def plot_declared_cells(seq_rows: list[dict[str, Any]], path: Path) -> None:
    """Declared-cell net with 95% CI vs the zero line, in sequence order."""
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(seq_rows))
    for k, row in enumerate(seq_rows):
        color = "#2e7d32" if row["sequence_pass"] else (
            "#c0392b" if row["descriptive_label"] == "EVIDENCE_AGAINST" else "#7f8c8d")
        ax.errorbar(k, row["effect_bps"],
                    yerr=[[row["effect_bps"] - row["ci_low"]], [row["ci_high"] - row["effect_bps"]]],
                    fmt="o", capsize=5, color=color, markersize=8)
        note = row["verdict"]
        ax.annotate(f"p={row['boot_p']:.3f}\n{note}", (k, row["ci_high"]),
                    textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{r['sequence_order']}. {r['instrument']}-{r['domain']}"
                        for r in seq_rows])
    ax.set_ylabel("Net per-event expectancy (bps; CONS costs + financing)")
    ax.set_title("EXP-034 declared family — fixed-sequence walk (alpha=0.05 one-sided)")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_waterfalls(cell_results: dict[tuple[str, str], dict[str, Any]], path: Path) -> None:
    """Gross -> -RT -> -financing -> net waterfall per declared cell."""
    fig, axes = plt.subplots(1, len(DECLARED_SEQUENCE), figsize=(5 * len(DECLARED_SEQUENCE), 4.5))
    for ax, (inst, domain) in zip(np.atleast_1d(axes), DECLARED_SEQUENCE):
        res = cell_results[(inst, domain)]
        gross = res["gross_abs_bps"]
        rt = RT_CONS_BPS[inst]
        fin = res["mean_financing_bps"]
        net = res["effect_bps"]
        stages = ["gross", "-RT", "-financing", "net"]
        starts = [0.0, gross, gross - rt, 0.0]
        heights = [gross, -rt, -fin, net]
        colors = ["#3498db", "#e67e22", "#e74c3c", "#2e7d32" if net > 0 else "#c0392b"]
        for k, (s, h, c) in enumerate(zip(starts, heights, colors)):
            ax.bar(k, h, bottom=s if k < 3 else 0.0, color=c, width=0.6)
        ax.axhline(0, color="black", lw=0.8)
        ax.set_xticks(range(4))
        ax.set_xticklabels(stages)
        ax.set_title(f"{inst}-{domain} (n={res['n_events']})")
        ax.set_ylabel("bps")
    fig.suptitle("EXP-034 cost decomposition (declared cells)", fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_all_cells_map(cell_results: dict[tuple[str, str], dict[str, Any]], path: Path) -> None:
    """All-12-cell descriptive net + CI map (declared highlighted; NON-BINDING)."""
    fig, ax = plt.subplots(figsize=(11, 5.5))
    labels, k = [], 0
    for domain in DOMAINS:
        for inst in INSTRUMENTS:
            res = cell_results.get((inst, domain))
            if res is None:
                continue
            declared = res["declared"]
            color = "#2e7d32" if declared else "#7f8c8d"
            ax.errorbar(k, res["effect_bps"],
                        yerr=[[res["effect_bps"] - res["ci_low"]],
                              [res["ci_high"] - res["effect_bps"]]],
                        fmt="o" if declared else "s", capsize=4, color=color,
                        markersize=8 if declared else 5)
            labels.append(f"{inst}\n{domain}")
            k += 1
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(range(k))
    ax.set_xticklabels(labels, fontsize=7)
    ax.set_ylabel("Net per-event expectancy (bps)")
    ax.set_title("EXP-034 all cells — descriptive map (declared cells green; "
                 "non-declared cells are NON-BINDING disclosure)")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    """Run the EXP-034 per-instrument tradability screen end to end."""
    configure_logging()
    ensure_output_dirs()
    LOGGER.info("=== %s: per-instrument cost-bearing tradability screen ===", EXPERIMENT_ID)

    frozen_hash = verify_frozen_inference()
    verify_financing()
    LOGGER.info("Financing helper self-check PASS")
    deps = check_dependencies()

    series, metadata_rows = build_cell_series()
    rebuild_checks = validate_analysis_metadata(metadata_rows)

    lifetime = pl.read_csv(EXP022_RESULTS / "lifetime_observations.csv")
    table = build_event_table(lifetime)
    table = attach_costs_and_financing(table, series)

    recon_rows = reconcile_vs_exp030(table)
    cell_results = run_all_cells(table)
    seq_rows = fixed_sequence_walk(cell_results)
    fin_rows = financing_disclosure(table)
    robust_rows = seed_robustness(table)
    replay = determinism_replay(table, cell_results)
    if not replay["passed"]:
        raise ValueError(f"DETERMINISM REPLAY FAILED: {replay}")

    # F02 / design §8.4 amendment (2026-06-10): an A1 strict pass is
    # NECESSARY-BUT-NOT-SUFFICIENT for holdout release. A1 selects and tests on the
    # same analysis data (the declared family derives from EXP-030 disclosures), so
    # a pass here routes the passing cell into a one-shot TEST-stratum confirmation
    # (Tier B); only that TEST result can satisfy G2.
    a1_strict_pass = bool(any(r["sequence_pass"] for r in seq_rows))

    # ---- persist results ----------------------------------------------------
    write_rows(RESULTS_DIR / "reconciliation.csv", recon_rows)
    write_rows(RESULTS_DIR / "sequence_verdicts.csv", seq_rows)
    write_rows(RESULTS_DIR / "financing_disclosure.csv", fin_rows)
    write_rows(RESULTS_DIR / "seed_robustness.csv", robust_rows)
    write_rows(RESULTS_DIR / "cell_inference.csv", [
        {"instrument": i, "domain": d, "binding": res["declared"], **{
            k: res[k] for k in ("n_events", "n_bull", "n_bear", "gross_abs_bps",
                                "net_nofin_bps", "mean_financing_bps", "effect_bps",
                                "ci_low", "ci_high", "ci_low_1s", "ci_half_width",
                                "boot_p")}}
        for (i, d), res in sorted(cell_results.items())
    ])
    metadata = {
        "experiment_id": EXPERIMENT_ID,
        "frozen_tail_hash": frozen_hash,
        "dependencies": deps,
        "rt_cons_bps": RT_CONS_BPS,
        "financing_rate_bps_per_day": FINANCING_RATE_BPS_PER_DAY,
        "declared_sequence": [f"{i}/{d}" for i, d in DECLARED_SEQUENCE],
        "alpha_one_sided": ALPHA,
        "binding_rule": "boot_p <= 0.05 AND one-sided 95% lower bound (5th pctile) > 0",
        "n_boot": N_BOOT,
        "rebuild_cells_validated": len(rebuild_checks),
        "determinism_replay": replay,
        "a1_strict_pass": a1_strict_pass,
        "g2_admissible": False,
        "g2_note": ("Design §8.4 as amended 2026-06-10: A1 strict pass is "
                    "necessary-but-not-sufficient (in-sample selection+test); G2 "
                    "requires a Tier-B TEST-stratum confirmation of the passing cell."),
        "sequence_verdicts": {f"{r['instrument']}/{r['domain']}": r["verdict"]
                              for r in seq_rows},
        "overall_outcome": ("A1_STRICT_PASS_TEST_CONFIRMATION_REQUIRED"
                            if a1_strict_pass else "A1_NO_STRICT_PASS"),
    }
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(metadata, indent=2, default=str))

    # ---- plots ---------------------------------------------------------------
    plot_declared_cells(seq_rows, PLOTS_DIR / "declared_cells_net.png")
    plot_waterfalls(cell_results, PLOTS_DIR / "financing_waterfall.png")
    plot_all_cells_map(cell_results, PLOTS_DIR / "all_cells_map.png")

    # ---- console summary -----------------------------------------------------
    LOGGER.info("--- fixed-sequence walk (binding: one-sided alpha=0.05) ---")
    for r in seq_rows:
        LOGGER.info("%d. %s-%s: net=%.2f bps 1s-low=%.2f CI=[%.2f, %.2f] p=%.4f -> %s",
                    r["sequence_order"], r["instrument"], r["domain"], r["effect_bps"],
                    r["ci_low_1s"], r["ci_low"], r["ci_high"], r["boot_p"], r["verdict"])
    LOGGER.info("A1 strict pass: %s (G2 additionally requires a Tier-B TEST "
                "confirmation — design §8.4 as amended 2026-06-10)",
                "YES" if a1_strict_pass else "NO")
    LOGGER.info("Results in %s, plots in %s", RESULTS_DIR, PLOTS_DIR)


if __name__ == "__main__":
    main()
