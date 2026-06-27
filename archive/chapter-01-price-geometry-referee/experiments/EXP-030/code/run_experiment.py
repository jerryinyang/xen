"""Experiment EXP-030: Cost-Bearing Tradability of the Faithful Selective AVWAP Strategy.

Implements analysis-plan.md / scope.md (Phase 007). A **pure, deterministic cost
overlay** on the EXP-028 PRIMARY event set (EXP-022 ``lifetime_observations.csv``,
``role=event`` & ``reportable_event=true`` rows; pyramids included), whose realized
positions were validated by EXP-028 (EVAL_SUPPORTED) and confirmed on the cTrader
production path by EXP-029 (CONSISTENT).

Binding question: under a predeclared event-level per-position cost model, does the
strategy retain positive **net per-event expectancy** on >=1 domain?

Binding metric (scope): **absolute** net per-event expectancy
``mean(lifetime_bps) - RT_i`` per instrument (event-weighted), equal-weighted across
reportable instruments per domain. This is NOT the EXP-028 matched-control *excess*
minus cost — costs are charged against the traded event leg, not against the uncosted
counterfactual control. The CONSERVATIVE cost variant is binding; BASE is diagnostic.
The matched-control "net excess" is computed only as a non-binding attribution
companion.

Inference: the EXP-027 regime-cluster bootstrap tail is imported UNCHANGED and
hash-guarded. Significance is a one-sided **bootstrap** p-value (the EXP-027
sign-permutation leg is invalid for an absolute, non-paired-symmetric estimand) plus
``CI_low > 0``, Holm-adjusted across the 3 domains.

Integrity guards (no domain frame is rebuilt — every input is an EXP-022 column):
  * dependency gate: EXP-028 EVAL_SUPPORTED, EXP-029 CONSISTENT;
  * frozen-tail hash guard over the 5 named EXP-027 functions;
  * reconciliation guard: the recomputed gross matched-control excess must reproduce
    EXP-028 event_level_results.csv to <= 0.01 bps before any net number is read;
  * commute check: BASE/CONSERVATIVE bootstrap distributions identical in shape,
    offset by exactly ``mean_inst(RT)``.

The final 30% global holdout is never loaded (inherited fence: all rows are EXP-022
first-70% outputs). No holdout release here (EXP-032 is deferred, out of phase).

Run:
    cd <project-root> && python python/experiments/EXP-030/code/run_experiment.py
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

# --------------------------------------------------------------------------- #
# Path setup
# --------------------------------------------------------------------------- #
PROJECT_ROOT = Path(__file__).resolve().parents[4]

from xen.referee_calibration import seed_for  # noqa: E402

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
    decide_label,
    domain_effect,
    holm_adjust,
)

LOGGER = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-030"
EXP_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"

EXP022_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-022" / "results"
EXP028_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-028" / "results"
EXP029_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-029" / "results"

DOMAINS: tuple[str, ...] = ("5m", "1h", "4h")
INSTRUMENTS: tuple[str, ...] = ("BTCUSD", "EURUSD", "USTEC", "XAUUSD")

# Reportability (EXP-027/028 thresholds).
MIN_REPORTABLE_EVENTS = 30
MIN_DIRECTION_EVENTS = 8
DOMAIN_MIN_INSTRUMENTS = 3

# Inference (EXP-028 convention).
N_BOOT = 1000
CHUNK = 200
ALPHA = 0.05
CI_PERCENTILES = (2.5, 97.5)

# EXP-022 completion outcomes that count as a realized exit.
COMPLETED_OUTCOMES = ("favorable", "adverse", "trend_change")
JOIN_KEYS = ("instrument", "domain", "regime_id", "direction", "event_trigger_idx")

# Frozen inference functions whose source must match the EXP-027 file.
FROZEN_FUNCTIONS: tuple[str, ...] = (
    "domain_effect", "build_strata", "bootstrap_effect_distribution",
    "holm_adjust", "decide_label",
)
# Pinned expected hash of the concatenated FROZEN_FUNCTIONS sources, computed from
# the EXP-027 file as committed for the EXP-027/028 close-out (git 5387a3b; the file
# has no later commits or working-tree edits). Comparing a fresh reload of the same
# file against itself cannot fail; this pin is the binding freeze check.
FROZEN_TAIL_EXPECTED_HASH = "e50873d12a9f68d9"

# Predeclared per-instrument cost table (scope §"Cost table"; FROZEN pending the
# single Stage-4 operator confirmation). c_i is one-way bps of price covering
# half-spread + per-side commission + per-side slippage. BASE round trip = 2*c_i;
# CONSERVATIVE round trip = 2*BASE = 4*c_i. CONSERVATIVE is binding.
COST_ONEWAY_BPS: dict[str, float] = {
    "EURUSD": 0.75,
    "USTEC": 1.25,
    "XAUUSD": 1.50,
    "BTCUSD": 4.00,
}
RT_BASE_BPS: dict[str, float] = {k: 2.0 * v for k, v in COST_ONEWAY_BPS.items()}
RT_CONS_BPS: dict[str, float] = {k: 4.0 * v for k, v in COST_ONEWAY_BPS.items()}

# Guard tolerances.
RECON_TOL_BPS = 1e-2     # gross-excess reconciliation vs EXP-028 (scope: <= 0.01 bps)
COMMUTE_TOL_BPS = 1e-6   # net = gross - RT_i must hold elementwise in the bootstrap

# decide_label secondary-horizon slots are disabled for the absolute estimand
# (no secondary-horizon concept); a positive sentinel keeps the
# INCONCLUSIVE_SECONDARY_UNSTABLE branch off, leaving the EXP-028 FOR/AGAINST rule.
SEC_SENTINEL = 1.0


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


def cost_table_hash() -> str:
    """Stable content hash of the frozen one-way cost table (provenance record)."""
    payload = json.dumps(COST_ONEWAY_BPS, sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()[:16]


# --------------------------------------------------------------------------- #
# Frozen-inference integrity guard
# --------------------------------------------------------------------------- #
def verify_frozen_inference() -> str:
    """Assert the imported inference tail matches the PINNED EXP-027 source hash.

    Hashes the source of only the named inference-tail functions (not the whole
    file) and compares against ``FROZEN_TAIL_EXPECTED_HASH``, pinned from the
    EXP-027/028-era file. A fresh-reload self-comparison alone is tautological
    (both sides read the same on-disk file); the pin is what makes an edit to
    ``event_method.py`` after EXP-028 detectable. Aborts
    ``FROZEN_INFERENCE_MODIFIED`` on any mismatch or missing symbol.

    Returns
    -------
    str
        16-char hash prefix of the concatenated frozen-function source.
    """
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


# --------------------------------------------------------------------------- #
# Dependency gate
# --------------------------------------------------------------------------- #
def check_dependencies() -> dict[str, str]:
    """Assert EXP-028 EVAL_SUPPORTED, EXP-029 CONSISTENT, EXP-022 lifetime present."""
    exp028 = load_json(EXP028_RESULTS / "run_metadata.json")
    exp029 = load_json(EXP029_RESULTS / "run_metadata.json")
    v028 = str(exp028.get("overall_verdict", ""))
    v029 = str(exp029.get("overall_parity_disposition", ""))
    if v028 != "EVAL_SUPPORTED":
        raise ValueError(f"EXP-028 overall_verdict must be EVAL_SUPPORTED, got {v028!r}")
    if v029 != "CONSISTENT":
        raise ValueError(f"EXP-029 parity disposition must be CONSISTENT, got {v029!r}")
    for artifact in (EXP022_RESULTS / "lifetime_observations.csv",
                     EXP028_RESULTS / "event_level_results.csv"):
        if not artifact.exists():
            raise FileNotFoundError(f"missing dependency artifact: {artifact}")
    LOGGER.info("Dependency gate PASS (EXP-028=%s, EXP-029=%s)", v028, v029)
    return {"EXP-028": v028, "EXP-029": v029, "EXP-022": "present"}


# --------------------------------------------------------------------------- #
# Event + matched-control table (EXP-028 PRIMARY construction; pure column overlay)
# --------------------------------------------------------------------------- #
def build_event_table(lifetime: pl.DataFrame) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Per-event table with own lifetime, matched-control mean, and gross excess.

    Reproduces the EXP-028 PRIMARY event set: completed ``role=event`` rows with
    ``reportable_event=true`` and >= MIN_CONTROLS finite matched controls (matched by
    JOIN_KEYS). No domain frame is rebuilt — values are taken from EXP-022 directly
    (validated by EXP-028/029). Right-censored (``unfinished``) rows are excluded.
    """
    lifetime = ensure_bool(lifetime, ("reportable_event", "is_pyramid_bounce"))
    lt = lifetime.filter(pl.col("outcome").is_in(COMPLETED_OUTCOMES))
    lt = lt.filter(pl.col("lifetime_bps").is_not_null())
    keys = list(JOIN_KEYS)

    events = lt.filter((pl.col("role") == "event") & pl.col("reportable_event"))
    controls = lt.filter(pl.col("role") == "control")
    ctrl_mean = controls.group_by(keys).agg(
        pl.col("lifetime_bps").mean().alias("mean_control_lifetime_bps"),
        pl.len().alias("n_controls_finite"),
    )
    merged = events.join(ctrl_mean, on=keys, how="inner")
    merged = merged.filter(pl.col("n_controls_finite") >= EM.MIN_CONTROLS)

    out = merged.with_columns(
        (pl.col("lifetime_bps") - pl.col("mean_control_lifetime_bps")).alias("paired_excess_bps")
    ).select(
        "instrument", "domain", "regime_id", "direction", "is_pyramid_bounce",
        "event_trigger_idx", "lifetime_bps", "mean_control_lifetime_bps",
        "paired_excess_bps", "n_controls_finite",
    )
    diag = {
        "n_events": out.height,
        "n_pyramid": int(out.filter(pl.col("is_pyramid_bounce")).height),
        "n_nonpyramid": int(out.filter(~pl.col("is_pyramid_bounce")).height),
        "right_censored_excluded": int(lifetime.filter(
            (pl.col("role") == "event") & (pl.col("outcome") == "unfinished")).height),
    }
    LOGGER.info("Event set: %d (pyramid=%d, non-pyramid=%d)",
                out.height, diag["n_pyramid"], diag["n_nonpyramid"])
    return out, diag


def attach_costs(table: pl.DataFrame) -> pl.DataFrame:
    """Join per-instrument round-trip costs and form net + net-excess columns.

    Each event row is one realized position (pyramids are independent positions /
    rows) and bears exactly one round trip; nothing is amortized across pyramid legs.
    ``net_*`` is the binding absolute metric base; ``net_excess_*`` is the non-binding
    attribution companion (gross excess shifted by RT; controls uncosted).
    """
    cost = pl.DataFrame({
        "instrument": list(COST_ONEWAY_BPS.keys()),
        "rt_base": [RT_BASE_BPS[i] for i in COST_ONEWAY_BPS],
        "rt_cons": [RT_CONS_BPS[i] for i in COST_ONEWAY_BPS],
    })
    joined = table.join(cost, on="instrument", how="left")
    if joined.filter(pl.col("rt_cons").is_null()).height:
        missing = joined.filter(pl.col("rt_cons").is_null())["instrument"].unique().to_list()
        raise ValueError(f"cost table missing instruments: {missing}")
    return joined.with_columns(
        (pl.col("lifetime_bps") - pl.col("rt_base")).alias("net_base"),
        (pl.col("lifetime_bps") - pl.col("rt_cons")).alias("net_cons"),
        (pl.col("paired_excess_bps") - pl.col("rt_base")).alias("net_excess_base"),
        (pl.col("paired_excess_bps") - pl.col("rt_cons")).alias("net_excess_cons"),
    )


# --------------------------------------------------------------------------- #
# Pure computation: reportability + frozen-tail inference on a value column
# --------------------------------------------------------------------------- #
def reportable_instruments(cell: pl.DataFrame) -> list[str]:
    """Instruments in a domain meeting per-instrument reportability thresholds."""
    out = []
    for inst in INSTRUMENTS:
        sub = cell.filter(pl.col("instrument") == inst)
        n_bull = sub.filter(pl.col("direction") == 1).height
        n_bear = sub.filter(pl.col("direction") == -1).height
        if (sub.height >= MIN_REPORTABLE_EVENTS and n_bull >= MIN_DIRECTION_EVENTS
                and n_bear >= MIN_DIRECTION_EVENTS):
            out.append(inst)
    return out


def _cell_arrays(cell: pl.DataFrame, value_col: str) -> tuple[np.ndarray, ...]:
    """Extract (value, instrument, direction, regime) arrays for the frozen tail."""
    return (
        cell.get_column(value_col).to_numpy().astype(float),
        cell.get_column("instrument").to_numpy(),
        cell.get_column("direction").to_numpy().astype(int),
        cell.get_column("regime_id").to_numpy().astype(int),
    )


def _bootstrap_distribution(cell: pl.DataFrame, value_col: str, insts: list[str],
                            rng: np.random.Generator) -> np.ndarray:
    """Regime-cluster bootstrap distribution of the instrument-averaged effect."""
    diffs, inst_labels, dir_labels, regime_labels = _cell_arrays(cell, value_col)
    strata = build_strata(diffs, inst_labels, dir_labels, regime_labels, insts)
    return bootstrap_effect_distribution(strata, insts, rng, N_BOOT, CHUNK)


def infer_cell(cell: pl.DataFrame, value_col: str, rng: np.random.Generator) -> dict[str, Any]:
    """Effect, regime-cluster bootstrap CI, and one-sided bootstrap p on a value column.

    The one-sided bootstrap p tests ``effect > 0`` via
    ``(1 + #{boot <= 0}) / (1 + N_BOOT)``. This replaces the EXP-027 sign-permutation
    leg, which is invalid for an absolute (non-paired-symmetric) estimand. The
    ``CI_low > 0`` requirement is unchanged.
    """
    insts = reportable_instruments(cell)
    base = {
        "n_events": cell.height,
        "n_bull": cell.filter(pl.col("direction") == 1).height,
        "n_bear": cell.filter(pl.col("direction") == -1).height,
        "n_instruments": len(insts),
        "reportable_instruments": insts,
    }
    if len(insts) < DOMAIN_MIN_INSTRUMENTS:
        return {**base, "effect_bps": None, "ci_low": None, "ci_high": None,
                "ci_half_width": None, "boot_p": None}
    cell = cell.filter(pl.col("instrument").is_in(insts))
    diffs, inst_labels, _dir, _reg = _cell_arrays(cell, value_col)
    effect = domain_effect(diffs, inst_labels, insts)
    boot = _bootstrap_distribution(cell, value_col, insts, rng)
    ci_low = float(np.percentile(boot, CI_PERCENTILES[0]))
    ci_high = float(np.percentile(boot, CI_PERCENTILES[1]))
    boot_p = float((1 + int(np.sum(boot <= 0.0))) / (1 + N_BOOT))
    return {**base, "effect_bps": effect, "ci_low": ci_low, "ci_high": ci_high,
            "ci_half_width": (ci_high - ci_low) / 2.0, "boot_p": boot_p}


def run_variant(table: pl.DataFrame, value_col: str, purpose: str) -> dict[str, dict[str, Any]]:
    """Per-domain inference on ``value_col`` with Holm across domains + verdict."""
    results: dict[str, dict[str, Any]] = {}
    raw_p: dict[str, float] = {}
    for domain in DOMAINS:
        cell = table.filter(pl.col("domain") == domain)
        rng = np.random.default_rng(seed_for(EXPERIMENT_ID, purpose, domain))
        res = infer_cell(cell, value_col, rng)
        results[domain] = res
        if res["boot_p"] is not None:
            raw_p[domain] = res["boot_p"]
    adjusted = holm_adjust(raw_p) if raw_p else {}
    for domain, res in results.items():
        hp = adjusted.get(domain)
        res["holm_p"] = hp
        if res["effect_bps"] is None or hp is None:
            res["verdict"] = "UNDER_POWERED"
            continue
        res["verdict"] = decide_label(res["effect_bps"], res["ci_low"], res["ci_high"],
                                      hp, ALPHA, SEC_SENTINEL, SEC_SENTINEL)
    return results


# --------------------------------------------------------------------------- #
# Integrity guards on the overlay
# --------------------------------------------------------------------------- #
def reconcile_gross_excess(table: pl.DataFrame) -> dict[str, dict[str, float]]:
    """Recomputed gross matched-control excess must reproduce EXP-028 (<= RECON_TOL).

    Proves the event set, control linkage, and aggregation are identical to the
    validated upstream, so the only change is the cost overlay. Hard-fail otherwise.
    """
    exp028 = pl.read_csv(EXP028_RESULTS / "event_level_results.csv")
    expected = {row["domain"]: float(row["effect_bps"]) for row in exp028.iter_rows(named=True)}
    expected_n = {row["domain"]: int(row["n_events"]) for row in exp028.iter_rows(named=True)}
    out: dict[str, dict[str, float]] = {}
    for domain in DOMAINS:
        cell = table.filter(pl.col("domain") == domain)
        insts = reportable_instruments(cell)
        cell = cell.filter(pl.col("instrument").is_in(insts))
        # Row-set / holdout fence: lifetime_observations.csv carries no timestamp column
        # (only bar indices), so the inherited "first-70% only" claim cannot be checked
        # against a time boundary directly. The available structural proof is the event
        # count: the reportable set must match the first-70% EXP-028 run exactly. A
        # silently regenerated (e.g. full-range) upstream CSV would change this count and
        # would also break the gross-excess match below.
        n_used = cell.height
        if n_used != expected_n[domain]:
            raise ValueError(
                f"ROW-SET FENCE FAILED {domain}: reportable event count {n_used} != "
                f"EXP-028 first-70% count {expected_n[domain]} — inherited holdout fence "
                f"cannot be trusted (upstream EXP-022 CSV may have been regenerated)."
            )
        diffs, inst_labels, _d, _r = _cell_arrays(cell, "paired_excess_bps")
        effect = domain_effect(diffs, inst_labels, insts)
        exp = expected[domain]
        if abs(effect - exp) > RECON_TOL_BPS:
            raise ValueError(
                f"RECONCILIATION FAILED {domain}: gross excess {effect:.6f} != "
                f"EXP-028 {exp:.6f} (tol {RECON_TOL_BPS})."
            )
        out[domain] = {"recomputed_excess_bps": effect, "exp028_excess_bps": exp,
                       "abs_diff_bps": abs(effect - exp), "n_events_reconciled": n_used,
                       "exp028_n_events": expected_n[domain]}
    LOGGER.info("Reconciliation PASS: gross excess + event counts reproduce EXP-028 "
                "in all domains")
    return out


def commute_check(table: pl.DataFrame) -> dict[str, float]:
    """Assert net bootstrap == gross bootstrap shifted by mean_inst(RT), elementwise.

    With an identical bootstrap seed the resample indices are shared, so
    ``net = gross - RT_i`` must hold exactly at the domain effect level for every
    bootstrap replicate. A mismatch indicates a join/aggregation bug.
    """
    out: dict[str, float] = {}
    for domain in DOMAINS:
        cell = table.filter(pl.col("domain") == domain)
        insts = reportable_instruments(cell)
        if len(insts) < DOMAIN_MIN_INSTRUMENTS:
            continue
        cell = cell.filter(pl.col("instrument").is_in(insts))
        seed = seed_for(EXPERIMENT_ID, "commute", domain)
        boot_g = _bootstrap_distribution(cell, "lifetime_bps", insts, np.random.default_rng(seed))
        boot_c = _bootstrap_distribution(cell, "net_cons", insts, np.random.default_rng(seed))
        boot_b = _bootstrap_distribution(cell, "net_base", insts, np.random.default_rng(seed))
        mean_rt_cons = float(np.mean([RT_CONS_BPS[i] for i in insts]))
        mean_rt_base = float(np.mean([RT_BASE_BPS[i] for i in insts]))
        dev = max(float(np.max(np.abs(boot_g - boot_c - mean_rt_cons))),
                  float(np.max(np.abs(boot_g - boot_b - mean_rt_base))))
        if dev > COMMUTE_TOL_BPS:
            raise ValueError(f"COMMUTE CHECK FAILED {domain}: max deviation {dev:.3e} bps")
        out[domain] = dev
    LOGGER.info("Commute check PASS: net == gross - mean_inst(RT) in all domains")
    return out


# --------------------------------------------------------------------------- #
# Per-instrument net + break-even diagnostic
# --------------------------------------------------------------------------- #
def per_instrument_net(table: pl.DataFrame) -> list[dict[str, Any]]:
    """Per (instrument, domain) gross-absolute, net (both variants), and break-even RT.

    Break-even RT = gross absolute per-event expectancy (the round trip at which net
    crosses zero). Descriptive only; computed from gross quantities so it cannot
    motivate any cost-model change. A single-instrument regime-cluster bootstrap CI on
    net_cons is reported for context only (the binding verdict is domain-level).

    ``headroom_cons_bps`` and ``net_cons_survives_nonbinding`` (F01 disclosure) expose
    which instrument x domain cells survive CONSERVATIVE costs *on their own* — the
    information the equal-weight domain aggregate (dominated by BTCUSD's 16 bps RT)
    masks. These are explicitly NON-BINDING: the phase verdict remains the equal-weight
    domain metric, and no single cell is promoted to TRADABLE here (uncontrolled
    multiplicity). They exist so a domain INCONCLUSIVE/AGAINST is not misread as
    "no instrument is tradable."
    """
    rows: list[dict[str, Any]] = []
    for inst in INSTRUMENTS:
        for domain in DOMAINS:
            sub = table.filter((pl.col("instrument") == inst) & (pl.col("domain") == domain))
            if sub.height == 0:
                continue
            gross_abs = float(sub.get_column("lifetime_bps").mean())
            rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "perinst", domain, inst))
            boot = _bootstrap_distribution(sub, "net_cons", [inst], rng)
            ci_low = float(np.percentile(boot, CI_PERCENTILES[0]))
            ci_high = float(np.percentile(boot, CI_PERCENTILES[1]))
            rows.append({
                "instrument": inst, "domain": domain, "n_events": sub.height,
                "gross_abs_bps": gross_abs,
                "net_base_bps": float(sub.get_column("net_base").mean()),
                "net_cons_bps": float(sub.get_column("net_cons").mean()),
                "net_cons_ci_low": ci_low,
                "net_cons_ci_high": ci_high,
                "breakeven_rt_bps": gross_abs,
                "rt_base_bps": RT_BASE_BPS[inst], "rt_cons_bps": RT_CONS_BPS[inst],
                "headroom_cons_bps": gross_abs - RT_CONS_BPS[inst],
                "net_cons_survives_nonbinding": bool(ci_low > 0.0),
            })
    return rows


# --------------------------------------------------------------------------- #
# Non-binding robustness / attribution diagnostics
# --------------------------------------------------------------------------- #
def pyramid_net_split(table: pl.DataFrame) -> dict[str, dict[str, Any]]:
    """Per-domain CONSERVATIVE net split: pyramid legs vs non-pyramid (F05 disclosure).

    Each pyramid bounce bears its own full round trip (nothing amortized across legs),
    a deliberately conservative charge. This non-binding split exposes how much of a
    domain's net drag is pyramid-leg cost — relevant on 5m, where pyramid legs are a
    large share of events. Event-weighted means over all instruments (a raw descriptive
    split, NOT the equal-weight binding aggregation); never decides the verdict.
    """
    out: dict[str, dict[str, Any]] = {}
    for domain in DOMAINS:
        cell = table.filter(pl.col("domain") == domain)
        if cell.height == 0:
            continue
        pyr = cell.filter(pl.col("is_pyramid_bounce"))
        non = cell.filter(~pl.col("is_pyramid_bounce"))
        out[domain] = {
            "n_pyramid": pyr.height,
            "n_nonpyramid": non.height,
            "pyramid_share": pyr.height / cell.height,
            "net_cons_pyramid_bps": float(pyr.get_column("net_cons").mean()) if pyr.height else None,
            "net_cons_nonpyramid_bps": float(non.get_column("net_cons").mean()) if non.height else None,
            "gross_abs_pyramid_bps": float(pyr.get_column("lifetime_bps").mean()) if pyr.height else None,
            "gross_abs_nonpyramid_bps": float(non.get_column("lifetime_bps").mean()) if non.height else None,
        }
    return out


def seed_robustness(table: pl.DataFrame, n_seeds: int = 8) -> dict[str, dict[str, Any]]:
    """Multi-seed stability of the binding CONSERVATIVE net CI per domain (F06).

    The point estimate is seed-independent (``domain_effect`` uses no RNG); only the
    regime-cluster bootstrap CI varies with the resample seed. The trivial determinism
    replay (identical seed) cannot detect CI sensitivity, so this re-runs the binding
    inference across ``n_seeds`` seeds and records the spread of ci_low/ci_high and
    whether the verdict-relevant bound keeps its sign. Diagnostic only — the canonical
    verdict still uses the single ``seed_for`` seed.
    """
    out: dict[str, dict[str, Any]] = {}
    for domain in DOMAINS:
        cell = table.filter(pl.col("domain") == domain)
        insts = reportable_instruments(cell)
        if len(insts) < DOMAIN_MIN_INSTRUMENTS:
            continue
        sub = cell.filter(pl.col("instrument").is_in(insts))
        lows: list[float] = []
        highs: list[float] = []
        for k in range(n_seeds):
            rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "robust", domain, str(k)))
            boot = _bootstrap_distribution(sub, "net_cons", insts, rng)
            lows.append(float(np.percentile(boot, CI_PERCENTILES[0])))
            highs.append(float(np.percentile(boot, CI_PERCENTILES[1])))
        out[domain] = {
            "n_seeds": n_seeds,
            "ci_low_min": min(lows), "ci_low_max": max(lows), "ci_low_range": max(lows) - min(lows),
            "ci_high_min": min(highs), "ci_high_max": max(highs), "ci_high_range": max(highs) - min(highs),
            "ci_low_sign_stable": bool(all(x > 0 for x in lows) or all(x <= 0 for x in lows)),
            "ci_high_sign_stable": bool(all(x > 0 for x in highs) or all(x <= 0 for x in highs)),
        }
    return out


# --------------------------------------------------------------------------- #
# Verdict assembly
# --------------------------------------------------------------------------- #
def phase_outcome(cons_res: dict[str, dict[str, Any]]) -> str:
    """Bind the phase outcome on the CONSERVATIVE net verdicts.

    TRADABLE if >=1 domain EVIDENCE_FOR; NOT_TRADABLE if every reportable domain is
    EVIDENCE_AGAINST; else INCONCLUSIVE. EVIDENCE_AGAINST is itself the power-bearing
    condition: ``decide_label`` returns it only when ``CI_high <= 0``, i.e. the
    regime-cluster bootstrap CI excludes *every* positive net effect; a wide CI that
    cannot rule out a material positive falls to INCONCLUSIVE_SPANS_ZERO, not AGAINST.
    Under-powered domains (<3 reportable instruments -> UNDER_POWERED) are excluded
    from the all-AGAINST test rather than being forced into NOT_TRADABLE.
    """
    verdicts = [cons_res[d].get("verdict") for d in DOMAINS]
    if any(v == "EVIDENCE_FOR" for v in verdicts):
        return "TRADABLE"
    reportable = [v for v in verdicts if v != "UNDER_POWERED"]
    if reportable and all(v == "EVIDENCE_AGAINST" for v in reportable):
        return "NOT_TRADABLE"
    return "INCONCLUSIVE"


# --------------------------------------------------------------------------- #
# Plotting (4)
# --------------------------------------------------------------------------- #
def _verdict_color(verdict: str | None) -> str:
    if verdict == "EVIDENCE_FOR":
        return "#2ecc71"
    if verdict and "AGAINST" in verdict:
        return "#e74c3c"
    return "#95a5a6"


def plot_net_expectancy(base_res: dict, cons_res: dict, path: Path) -> None:
    """Forest plot of net per-event expectancy: BASE vs CONSERVATIVE per domain."""
    fig, ax = plt.subplots(figsize=(10, 5))
    for i, domain in enumerate(DOMAINS):
        for res, off, label, marker in ((base_res, 0.15, "BASE", "s"),
                                        (cons_res, -0.15, "CONSERVATIVE", "o")):
            r = res[domain]
            if r.get("effect_bps") is None:
                continue
            color = _verdict_color(r.get("verdict")) if label == "CONSERVATIVE" else "#7f8c8d"
            ax.errorbar(r["effect_bps"], i + off,
                        xerr=[[r["effect_bps"] - r["ci_low"]], [r["ci_high"] - r["effect_bps"]]],
                        fmt=marker, color=color, capsize=4, markersize=8,
                        label=label if i == 0 else None)
        cr = cons_res[domain]
        if cr.get("effect_bps") is not None:
            ax.annotate(f"CONS {cr.get('verdict')}  p={cr.get('holm_p')}",
                        xy=(cr["ci_high"], i - 0.15), xytext=(6, 0),
                        textcoords="offset points", fontsize=8, va="center")
    ax.axvline(0, color="black", ls="--", lw=0.8, alpha=0.6)
    ax.set_yticks(range(len(DOMAINS)))
    ax.set_yticklabels(DOMAINS)
    ax.set_xlabel("Net per-event expectancy (bps), 95% regime-cluster bootstrap CI")
    ax.set_title("EXP-030 net per-event expectancy — BASE vs CONSERVATIVE (binding)",
                 fontweight="bold")
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_waterfall(gross_res: dict, base_res: dict, cons_res: dict, path: Path) -> None:
    """Per-domain gross-absolute -> net(BASE) -> net(CONSERVATIVE) bars."""
    fig, axes = plt.subplots(1, len(DOMAINS), figsize=(5 * len(DOMAINS), 4), squeeze=False)
    for j, domain in enumerate(DOMAINS):
        ax = axes[0, j]
        vals = [gross_res[domain].get("effect_bps"), base_res[domain].get("effect_bps"),
                cons_res[domain].get("effect_bps")]
        vals = [v if v is not None else np.nan for v in vals]
        colors = ["#34495e", "#7f8c8d", _verdict_color(cons_res[domain].get("verdict"))]
        ax.bar(["gross_abs", "net_base", "net_cons"], vals, color=colors, width=0.6)
        ax.axhline(0, color="black", lw=0.6)
        ax.set_title(f"{domain}", fontsize=11)
        ax.set_ylabel("bps / event")
        ax.tick_params(axis="x", labelrotation=20)
    fig.suptitle("EXP-030 gross absolute -> net waterfall (per-event expectancy)",
                 fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_breakeven_heatmap(per_inst: list[dict[str, Any]], path: Path) -> None:
    """Heatmap of break-even RT per instrument x domain; annotate headroom vs RT_cons."""
    grid = np.full((len(INSTRUMENTS), len(DOMAINS)), np.nan)
    lookup = {(r["instrument"], r["domain"]): r for r in per_inst}
    for a, inst in enumerate(INSTRUMENTS):
        for b, domain in enumerate(DOMAINS):
            r = lookup.get((inst, domain))
            if r is not None:
                grid[a, b] = r["breakeven_rt_bps"]
    fig, ax = plt.subplots(figsize=(7, 5))
    im = ax.imshow(grid, cmap="RdYlGn", aspect="auto")
    ax.set_xticks(range(len(DOMAINS)))
    ax.set_xticklabels(DOMAINS)
    ax.set_yticks(range(len(INSTRUMENTS)))
    ax.set_yticklabels(INSTRUMENTS)
    for a, inst in enumerate(INSTRUMENTS):
        for b, domain in enumerate(DOMAINS):
            r = lookup.get((inst, domain))
            if r is None:
                continue
            headroom = r["breakeven_rt_bps"] - r["rt_cons_bps"]
            ax.text(b, a, f"BE={r['breakeven_rt_bps']:.1f}\nRTc={r['rt_cons_bps']:.1f}\n"
                          f"hd={headroom:+.1f}", ha="center", va="center", fontsize=7)
    ax.set_title("EXP-030 break-even round-trip cost (bps); hd = BE - RT_cons",
                 fontweight="bold")
    fig.colorbar(im, ax=ax, label="break-even RT (bps)")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_verdict_summary(cons_res: dict, base_res: dict, attr_res: dict, path: Path) -> None:
    """Traffic-light CONSERVATIVE verdict per domain; BASE + attribution annotated."""
    fig, ax = plt.subplots(figsize=(11, 4))
    for i, domain in enumerate(DOMAINS):
        cr, br, ar = cons_res[domain], base_res[domain], attr_res[domain]
        if cr.get("effect_bps") is not None:
            xerr = [[cr["effect_bps"] - cr["ci_low"]], [cr["ci_high"] - cr["effect_bps"]]]
            ax.errorbar(cr["effect_bps"], i, xerr=xerr, fmt="o",
                        color=_verdict_color(cr.get("verdict")), capsize=4, markersize=10)
        ax.text(-0.02, i, domain, ha="right", va="center", fontweight="bold",
                transform=ax.get_yaxis_transform())
        txt = (f"CONS net={_fmt(cr.get('effect_bps'))} {cr.get('verdict')} p={cr.get('holm_p')}"
               f"  |  BASE net={_fmt(br.get('effect_bps'))} {br.get('verdict')}"
               f"  |  attr(net-excess)={_fmt(ar.get('effect_bps'))} (non-binding)")
        ax.text(1.02, i, txt, va="center", fontsize=7.5, transform=ax.get_yaxis_transform())
    ax.axvline(0, color="black", ls="--", lw=0.8, alpha=0.5)
    ax.set_yticks([])
    ax.set_xlabel("CONSERVATIVE net per-event expectancy (bps) with 95% CI")
    ax.set_title("EXP-030 verdict summary — CONSERVATIVE binding", fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _fmt(value: float | None) -> str:
    return "NA" if value is None else f"{value:.2f}"


# --------------------------------------------------------------------------- #
# Save
# --------------------------------------------------------------------------- #
def _variant_rows(res: dict[str, dict[str, Any]], variant: str) -> list[dict[str, Any]]:
    """Flatten a per-domain result dict into CSV rows tagged with the cost variant."""
    keys = ("effect_bps", "ci_low", "ci_high", "ci_half_width", "boot_p", "holm_p",
            "n_events", "n_bull", "n_bear", "n_instruments", "verdict")
    return [{"domain": d, "variant": variant, **{k: res[d].get(k) for k in keys}}
            for d in DOMAINS]


def save_outputs(cons_res, base_res, attr_cons, attr_base, per_inst, metadata) -> None:
    """Write all result CSVs, plots, and run metadata."""
    ensure_output_dirs()
    write_rows(RESULTS_DIR / "net_expectancy_results.csv",
               _variant_rows(cons_res, "CONSERVATIVE") + _variant_rows(base_res, "BASE"))
    write_rows(RESULTS_DIR / "net_by_instrument.csv", per_inst)
    # F07: the companion is NON-BINDING — label its decide_label output
    # ``companion_label`` (not ``verdict``) and carry an explicit binding=False flag
    # so a grep for EVIDENCE_FOR cannot be mistaken for a tradability verdict.
    write_rows(RESULTS_DIR / "attribution_companion.csv", [
        {"domain": d, "variant": "CONSERVATIVE", "binding": False,
         **{k: attr_cons[d].get(k) for k in ("effect_bps", "ci_low", "ci_high", "holm_p")},
         "companion_label": attr_cons[d].get("verdict")} for d in DOMAINS
    ] + [
        {"domain": d, "variant": "BASE", "binding": False,
         **{k: attr_base[d].get(k) for k in ("effect_bps", "ci_low", "ci_high", "holm_p")},
         "companion_label": attr_base[d].get("verdict")} for d in DOMAINS])
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(metadata, indent=2, default=str))
    LOGGER.info("Wrote results to %s", RESULTS_DIR)


def make_plots(cons_res, base_res, gross_res, attr_cons, per_inst) -> None:
    """Render the four scoped plots from already-computed inputs."""
    plot_net_expectancy(base_res, cons_res, PLOTS_DIR / "net_expectancy.png")
    plot_waterfall(gross_res, base_res, cons_res, PLOTS_DIR / "gross_to_net_waterfall.png")
    plot_breakeven_heatmap(per_inst, PLOTS_DIR / "breakeven_heatmap.png")
    plot_verdict_summary(cons_res, base_res, attr_cons, PLOTS_DIR / "verdict_summary.png")
    LOGGER.info("Wrote plots to %s", PLOTS_DIR)


# --------------------------------------------------------------------------- #
# Determinism replay (one domain)
# --------------------------------------------------------------------------- #
def replay_one_domain(table: pl.DataFrame, cons_res: dict[str, dict[str, Any]]) -> bool:
    """Re-run the binding inference for one domain and assert byte-identical effect/CI."""
    domain = DOMAINS[0]
    cell = table.filter(pl.col("domain") == domain)
    rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "net_cons", domain))
    res = infer_cell(cell, "net_cons", rng)
    ref = cons_res[domain]
    ok = (res["effect_bps"] == ref["effect_bps"] and res["ci_low"] == ref["ci_low"]
          and res["ci_high"] == ref["ci_high"] and res["boot_p"] == ref["boot_p"])
    LOGGER.info("Determinism replay (%s): %s", domain, "PASS" if ok else "FAIL")
    return bool(ok)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    configure_logging()
    LOGGER.info("=" * 70)
    LOGGER.info("EXP-030: Cost-Bearing Tradability of the Faithful Selective AVWAP Strategy")
    LOGGER.info("=" * 70)
    ensure_output_dirs()

    frozen_hash = verify_frozen_inference()
    deps = check_dependencies()

    LOGGER.info("Building event + matched-control table (EXP-022 overlay; no frame rebuild)")
    lifetime = pl.read_csv(EXP022_RESULTS / "lifetime_observations.csv")
    table, diag = build_event_table(lifetime)
    table = attach_costs(table)

    LOGGER.info("Reconciliation guard vs EXP-028 gross excess")
    reconciliation = reconcile_gross_excess(table)

    LOGGER.info("Commute check (net == gross - mean_inst(RT))")
    commute = commute_check(table)

    LOGGER.info("Binding inference: CONSERVATIVE net per-event expectancy")
    cons_res = run_variant(table, "net_cons", "net_cons")
    LOGGER.info("Diagnostic inference: BASE net + gross-absolute")
    base_res = run_variant(table, "net_base", "net_base")
    gross_res = run_variant(table, "lifetime_bps", "gross_abs")

    LOGGER.info("Attribution companion (non-binding net matched-control excess)")
    attr_cons = run_variant(table, "net_excess_cons", "attr_cons")
    attr_base = run_variant(table, "net_excess_base", "attr_base")

    per_inst = per_instrument_net(table)
    pyr_split = pyramid_net_split(table)
    seed_robust = seed_robustness(table)
    replay_ok = replay_one_domain(table, cons_res)
    outcome = phase_outcome(cons_res)

    metadata = {
        "experiment": EXPERIMENT_ID,
        "title": "Cost-Bearing Tradability of the Faithful Selective AVWAP Strategy",
        "phase_outcome": outcome,
        "binding_metric": "absolute_net_per_event_expectancy_CONSERVATIVE",
        "binding_variant": "CONSERVATIVE",
        "cons_per_domain": {d: cons_res[d].get("verdict") for d in DOMAINS},
        "base_per_domain": {d: base_res[d].get("verdict") for d in DOMAINS},
        "gross_abs_per_domain": {d: gross_res[d].get("effect_bps") for d in DOMAINS},
        "attribution_companion_note": ("net matched-control excess (controls uncosted) is "
                                       "NON-BINDING; never decides the verdict"),
        "dependencies": deps,
        "frozen_inference_hash": frozen_hash,
        "frozen_inference_expected_hash": FROZEN_TAIL_EXPECTED_HASH,
        "frozen_inference_evidence": ("pinned hash computed from event_method.py as "
                                      "committed in 5387a3b (EXP-027/028 close-out); "
                                      "git shows no later commit or working-tree edit "
                                      "to that file"),
        "frozen_functions": list(FROZEN_FUNCTIONS),
        "cost_table_oneway_bps": COST_ONEWAY_BPS,
        "cost_table_hash": cost_table_hash(),
        "rt_base_bps": RT_BASE_BPS,
        "rt_cons_bps": RT_CONS_BPS,
        "cost_table_operator_confirmation": "CONFIRMED_STAGE4_2026-06-09 — frozen as predeclared",
        "reconciliation": reconciliation,
        "commute_max_dev_bps": commute,
        "pyramids_included": True,
        "pyramid_split": {"pyramid": diag["n_pyramid"], "non_pyramid": diag["n_nonpyramid"]},
        "pyramid_net_split": pyr_split,
        "seed_robustness_net_cons": seed_robust,
        "right_censored_excluded": diag["right_censored_excluded"],
        "determinism_replay_pass": replay_ok,
        "determinism_replay_note": ("same-seed byte-identical re-run; across-seed CI "
                                    "stability is reported separately in "
                                    "seed_robustness_net_cons (F06)"),
        "holdout_fence": ("inherited — all rows are EXP-022 first-70% outputs; no new load. "
                          "Verified structurally: per-domain reportable event counts asserted "
                          "equal to the first-70% EXP-028 run (no timestamp column exists to "
                          "check a time boundary directly)."),
        "significance": ("FOR criterion is effectively the bootstrap 95% CI excluding "
                         "zero (one-sided ~0.025), Holm-screened; boot_p is the bootstrap "
                         "CDF at zero (CI-equivalent annotation, not a null-calibrated "
                         "p-value). Sign-permutation invalid for the absolute estimand."),
        "review_notes": {
            "binding_metric_caveat": (  # F01
                "Binding verdict is the EQUAL-WEIGHT cross-instrument domain net (faithful "
                "to EXP-028 PRIMARY aggregation). For an absolute-P&L question this is "
                "dominated by the highest-cost instrument: BTCUSD RT_cons=16 bps is 4.0 of "
                "the 7.5 bps mean drag. A domain INCONCLUSIVE/AGAINST does NOT mean no "
                "instrument is tradable — see net_by_instrument.csv "
                "net_cons_survives_nonbinding (e.g. EURUSD-4h net_cons CI excludes zero). "
                "No single cell is promoted to TRADABLE here (uncontrolled multiplicity); "
                "the per-instrument table is descriptive. A pre-registered per-cell test "
                "with multiplicity control is a future-experiment change, not a post-result "
                "edit (anti-tuning fence)."
            ),
            "power_note_4h": (  # F03
                "4h is power-limited for the absolute estimand (per-instrument n=36-70; "
                "CONSERVATIVE domain CI half-width ~17 bps). INCONCLUSIVE_SPANS_ZERO there "
                "reflects non-resolution, not a positive signal; the phase outcome turns on "
                "the weakest-powered domain. See seed_robustness_net_cons. A predeclared "
                "numeric resolvable-effect threshold for AGAINST is recorded as a "
                "future-experiment change (not retrofitted post-result)."
            ),
            "binding_vs_companion_warning": (  # F04
                "The NON-BINDING net matched-control excess (attribution_companion.csv) is "
                "EVIDENCE_FOR on 1h/4h CONSERVATIVE (holm_p~0.003) while the BINDING absolute "
                "net is AGAINST/INCONCLUSIVE. The verdict's direction rests on the predeclared "
                "absolute-vs-relative choice (controls are counterfactual, never traded). The "
                "companion's FOR must NOT be read as tradability."
            ),
            "for_gate_note": (  # F07
                "The binding FOR gate is effectively CI_low>0 at the 2.5th percentile "
                "(one-sided ~0.025), which subsumes boot_p<=0.05; boot_p is a redundant "
                "annotation and its percentile-bootstrap calibration is asserted, not "
                "validated. No FOR was reached this run, so it decided nothing."
            ),
        },
        "parameters": {"domains": list(DOMAINS), "instruments": list(INSTRUMENTS),
                       "alpha": ALPHA, "n_boot": N_BOOT, "ci_percentiles": list(CI_PERCENTILES),
                       "min_reportable_events": MIN_REPORTABLE_EVENTS,
                       "min_direction_events": MIN_DIRECTION_EVENTS,
                       "min_controls": EM.MIN_CONTROLS},
        "interpretation_bound": ("A NOT_TRADABLE result does not overturn the Phase-006 gross "
                                 "edge (different, non-substitutable estimand) and does not say "
                                 "the bounce event has no edge (EXP-021 fixed-horizon reaction is "
                                 "positive). A 5m net-negative is the expected stress case."),
    }
    save_outputs(cons_res, base_res, attr_cons, attr_base, per_inst, metadata)
    make_plots(cons_res, base_res, gross_res, attr_cons, per_inst)

    LOGGER.info("=" * 70)
    LOGGER.info("Phase outcome (CONSERVATIVE-binding): %s", outcome)
    for d in DOMAINS:
        r = cons_res[d]
        LOGGER.info("  %s CONS net=%s CI=[%s, %s] holm_p=%s n=%s -> %s",
                    d, _fmt(r.get("effect_bps")), _fmt(r.get("ci_low")), _fmt(r.get("ci_high")),
                    r.get("holm_p"), r.get("n_events"), r.get("verdict"))
    LOGGER.info("=" * 70)


if __name__ == "__main__":
    main()
