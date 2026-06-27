"""Experiment EXP-028: Faithful Selective AVWAP Strategy Re-Screen (corrected).

Implements the corrected analysis-plan.md / scope.md (Phase 006). Evaluates the
faithful selective AVWAP strategy under a **dual** event-level gate that keeps the
binding verdict inside the construction EXP-027 actually calibrated:

  * PRIMARY (binding): the EXP-022 **symmetric own-exit** matched-control lifetime
    excess. Event and control lifetimes are both completed under the same
    band-target / trend-change exit, so the null paired-excess is mean-zero /
    sign-symmetric and the frozen EXP-027 inference's FPR control transfers.
  * SECONDARY (non-binding, calibrated): the endogenous-exit-event vs.
    fixed-window-control construction, which carries weight only if a predeclared
    in-experiment placebo-null check shows FPR <= a0 and null-excess ~ 0.

Reuse (no re-derivation of validated machinery):
  * domain frames + holdout fence: ``xen.referee_calibration`` (EXP-020 convention,
    keyed per instrument by Symbol -> indices align with EXP-020/022);
  * frozen inference tail: ``event_method`` (md5-verified copy of EXP-027);
  * symmetric primary excess: EXP-022 ``lifetime_observations.csv`` (role=event vs
    role=control, both own-exit);
  * fixed-horizon {1,3,6} secondary-stability slots: EXP-021
    ``reaction_observations.csv`` (validated symmetric fixed-horizon excess);
  * placebo-null exit rule for the secondary: EXP-022 ``scan_lifetime`` /
    ``transfer_targets`` (imported, unchanged).

Pyramids are INCLUDED (faithful to the original concept and to EXP-020/021/022);
``is_pyramid_bounce`` is a reported diagnostic split, not a gate. The final 30%
global holdout is never loaded.

Run:
    cd <project-root> && python python/experiments/EXP-028/code/run_experiment.py
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
EXP028_CODE = Path(__file__).resolve().parent
if str(EXP028_CODE) not in sys.path:
    sys.path.insert(0, str(EXP028_CODE))

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
    decide_label,
    domain_effect,
    holm_adjust,
    permutation_p,
    sortino_ratio,
    verify_control_matching,
)

LOGGER = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-028"
DATA_DIR = PROJECT_ROOT / "data"
EXP_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"

EXP020_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-020" / "results"
EXP021_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-021" / "results"
EXP022_RESULTS = PROJECT_ROOT / "python" / "experiments" / "EXP-022" / "results"
EXP021_CODE = PROJECT_ROOT / "python" / "experiments" / "EXP-021" / "code" / "run_experiment.py"
EXP022_CODE = PROJECT_ROOT / "python" / "experiments" / "EXP-022" / "code" / "run_experiment.py"
EXP027_METHOD = PROJECT_ROOT / "python" / "experiments" / "EXP-027" / "code" / "event_method.py"

DOMAINS: tuple[str, ...] = ("5m", "1h", "4h")
INSTRUMENTS: tuple[str, ...] = ("BTCUSD", "EURUSD", "USTEC", "XAUUSD")

# Reportability (EXP-021/027 thresholds).
MIN_REPORTABLE_EVENTS = 30
MIN_DIRECTION_EVENTS = 8
DOMAIN_MIN_INSTRUMENTS = 3

# Inference (calibration convention; matches EXP-027).
N_BOOT = 1000
N_PERM = 1000
CHUNK = 200
ALPHA = 0.05
CI_PERCENTILES = (2.5, 97.5)

# Fixed-horizon secondary-stability family (EXP-021/027).
HORIZONS: tuple[int, ...] = EM.HORIZONS
SEC_LOW_HORIZON = 1
SEC_HIGH_HORIZON = 6

# Reconciliation tolerance for event lifetime_bps vs frame-recomputed bps.
RECON_TOL_BPS = 1e-3

# Secondary placebo-null calibration (bounded diagnostic; non-binding).
# Per-placebo EXP-022 exit-rule scan over realistic event counts is the cost driver;
# 100 draws bounds runtime while giving usable FPR precision for a non-gating check.
N_PLACEBO_DRAWS = 100

# Names of the frozen inference functions whose source must match EXP-027.
FROZEN_FUNCTIONS: tuple[str, ...] = (
    "domain_effect", "build_strata", "bootstrap_effect_distribution",
    "permutation_p", "holm_adjust", "decide_label", "sortino_ratio",
    "wilson_interval", "nearest_controls", "equity_advantage",
)

# EXP-022 exit-rule completion outcomes that count as a realized exit.
COMPLETED_OUTCOMES = ("favorable", "adverse", "trend_change")


# --------------------------------------------------------------------------- #
# Upstream helper modules (validated, side-effect-free at import)
# --------------------------------------------------------------------------- #
def _load_module(name: str, path: Path):
    """Import a validated upstream experiment module by file path (no execution of main)."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    # Register before exec so @dataclass introspection (sys.modules[__module__]) resolves.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


EXP021 = _load_module("exp021_helpers", EXP021_CODE)
EXP022 = _load_module("exp022_helpers", EXP022_CODE)


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


def load_csv(path: Path, time_cols: tuple[str, ...] = ()) -> pl.DataFrame:
    """Read a results CSV (raises if absent)."""
    if not path.exists():
        raise FileNotFoundError(f"missing upstream artifact: {path}")
    frame = pl.read_csv(path, try_parse_dates=True)
    return frame


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
# Frozen-inference integrity guard (Finding 3 — scoped to named functions)
# --------------------------------------------------------------------------- #
def verify_frozen_inference() -> str:
    """Assert the local frozen inference functions match the EXP-027 source.

    Hashes the source of only the named inference-tail functions (not the whole
    file, since EXP-028 legitimately adds new return/eligibility code elsewhere).
    Aborts with FROZEN_INFERENCE_MODIFIED on any mismatch.

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
            raise ValueError(f"FROZEN_INFERENCE_MODIFIED: function {name} missing in local or EXP-027 module")
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


# --------------------------------------------------------------------------- #
# Dependency gate
# --------------------------------------------------------------------------- #
def check_dependencies() -> dict[str, str]:
    """Assert EXP-020 SUPPORTED_FULL, EXP-027 METHOD_VALID, EXP-022 + EXP-021 present."""
    exp020 = load_json(EXP020_RESULTS / "run_metadata.json")
    exp027 = load_json(EXP027_RESULTS_META())
    status020 = str(exp020.get("overall_status", ""))
    # EXP-027 stores method_verdict either as a plain string or a nested dict.
    mv = exp027.get("method_verdict", "")
    verdict027 = str(mv.get("verdict", "")) if isinstance(mv, dict) else str(mv)
    if status020 != "SUPPORTED_FULL":
        raise ValueError(f"EXP-020 overall_status must be SUPPORTED_FULL, got {status020!r}")
    if verdict027 != "METHOD_VALID":
        raise ValueError(f"EXP-027 method_verdict must be METHOD_VALID, got {verdict027!r}")
    for artifact in (EXP022_RESULTS / "lifetime_observations.csv",
                     EXP021_RESULTS / "reaction_observations.csv",
                     EXP020_RESULTS / "avwap_events.csv",
                     EXP020_RESULTS / "avwap_state_summary.csv"):
        if not artifact.exists():
            raise FileNotFoundError(f"missing dependency artifact: {artifact}")
    LOGGER.info("Dependency gate PASS (EXP-020=%s, EXP-027=%s)", status020, verdict027)
    return {"EXP-020": status020, "EXP-027": verdict027, "EXP-022": "present", "EXP-021": "present"}


def EXP027_RESULTS_META() -> Path:
    return PROJECT_ROOT / "python" / "experiments" / "EXP-027" / "results" / "run_metadata.json"


# --------------------------------------------------------------------------- #
# Domain frames + alignment guard (Finding 6)
# --------------------------------------------------------------------------- #
def build_frames() -> tuple[dict[tuple[str, str], pl.DataFrame], dict[str, str]]:
    """Rebuild first-70% 5m/1h/4h domain bars per instrument (EXP-020 convention).

    Uses ``xen.referee_calibration`` (the same loader EXP-020/022 used), keyed per
    instrument by the Symbol column with the holdout fence applied in the lazy
    plan, so domain-bar indices align with EXP-020/022 by construction.
    """
    files = list_timebar_files(DATA_DIR)
    if not files:
        raise FileNotFoundError(f"no timebar files under {DATA_DIR / 'timebars'}")
    frames: dict[tuple[str, str], pl.DataFrame] = {}
    analysis_end: dict[str, str] = {}
    for path in tqdm(files, desc="rebuild domain bars"):
        data = load_analysis_data(path)
        analysis_end[data.instrument] = data.analysis_end
        for domain, frame in build_domain_frames(data.frame).items():
            frames[(data.instrument, domain)] = frame.with_row_index("bar_idx")
    return frames, analysis_end


def validate_alignment(events: pl.DataFrame, frames: dict[tuple[str, str], pl.DataFrame]) -> int:
    """Hard-fail if any event trigger row disagrees with the rebuilt domain bar.

    Reuses EXP-022's value-level guard (CloseTime/Close at trigger_idx must match
    the EXP-020 event exactly). Returns the number of (instrument, domain) cells
    checked.
    """
    checked = 0
    for (inst, domain), frame in frames.items():
        cell = events.filter((pl.col("instrument") == inst) & (pl.col("domain") == domain))
        if cell.height == 0:
            continue
        EXP022.validate_event_join(cell, frame.drop("bar_idx"), f"{inst}/{domain}")
        checked += 1
    LOGGER.info("Alignment guard PASS for %d instrument/domain cells", checked)
    return checked


def frame_log_close(frames: dict[tuple[str, str], pl.DataFrame]) -> dict[tuple[str, str], np.ndarray]:
    """Precompute log(Close) per cell for reconciliation and control returns."""
    return {key: np.log(f.get_column("Close").to_numpy().astype(float)) for key, f in frames.items()}


# --------------------------------------------------------------------------- #
# PRIMARY excess: EXP-022 symmetric own-exit lifetime (Finding 1, binding)
# --------------------------------------------------------------------------- #
def build_primary_excess(
    lifetime: pl.DataFrame, log_close: dict[tuple[str, str], np.ndarray],
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Per-event symmetric own-exit paired excess from EXP-022 lifetime rows.

    Excess = event ``lifetime_bps`` - mean(matched control ``lifetime_bps``), where
    event and control completed under the SAME band-target/trend-change exit. Only
    completed (non right-censored) rows contribute. Reconciles the event lifetime
    against the rebuilt frame to guard index alignment.
    """
    diag: dict[str, Any] = {}
    lifetime = ensure_bool(lifetime, ("reportable_event", "is_pyramid_bounce"))
    lt = lifetime.filter(pl.col("outcome").is_in(COMPLETED_OUTCOMES))  # drop right-censored
    lt = lt.filter(pl.col("lifetime_bps").is_not_null())
    keys = ["instrument", "domain", "regime_id", "direction", "event_trigger_idx"]

    events = lt.filter((pl.col("role") == "event") & (pl.col("reportable_event")))
    controls = lt.filter(pl.col("role") == "control")
    ctrl_mean = (
        controls.group_by(keys)
        .agg(pl.col("lifetime_bps").mean().alias("mean_control_lifetime_bps"),
             pl.len().alias("n_controls_finite"))
    )
    merged = events.join(ctrl_mean, on=keys, how="inner")
    merged = merged.filter(pl.col("n_controls_finite") >= EM.MIN_CONTROLS)

    # Reconcile event lifetime_bps against the rebuilt frame (alignment integrity),
    # vectorized per (instrument, domain) cell — no per-row Python loop.
    recon_bad = 0
    for (inst, domain), lc in log_close.items():
        sub = merged.filter((pl.col("instrument") == inst) & (pl.col("domain") == domain))
        if sub.height == 0:
            continue
        si = sub.get_column("start_idx").to_numpy().astype(np.int64)
        ci = sub.get_column("completion_idx").to_numpy().astype(np.int64)
        d = sub.get_column("direction").to_numpy().astype(float)
        lb = sub.get_column("lifetime_bps").to_numpy().astype(float)
        oob = (ci >= lc.size) | (si >= lc.size) | (ci < 0) | (si < 0)
        safe = ~oob
        recomputed = 10_000.0 * d[safe] * (lc[ci[safe]] - lc[si[safe]])
        recon_bad += int(oob.sum() + np.sum(np.abs(recomputed - lb[safe]) > RECON_TOL_BPS))
    if recon_bad:
        raise ValueError(
            f"PRIMARY reconciliation failed for {recon_bad} events: EXP-022 lifetime_bps "
            "does not match frame-recomputed bps (index misalignment)."
        )

    out = merged.with_columns(
        (pl.col("lifetime_bps") - pl.col("mean_control_lifetime_bps")).alias("paired_excess_bps")
    ).select(
        "instrument", "domain", "regime_id", "direction", "is_pyramid_bounce",
        "event_trigger_idx", "lifetime_bps", "mean_control_lifetime_bps",
        "paired_excess_bps", "n_controls_finite",
    )
    diag["n_primary_events"] = out.height
    diag["reconciliation_bad"] = recon_bad
    diag["n_pyramid"] = int(out.filter(pl.col("is_pyramid_bounce")).height)
    diag["n_nonpyramid"] = int(out.filter(~pl.col("is_pyramid_bounce")).height)
    LOGGER.info("PRIMARY events: %d (pyramid=%d, non-pyramid=%d); reconciliation clean",
                out.height, diag["n_pyramid"], diag["n_nonpyramid"])
    return out, diag


# --------------------------------------------------------------------------- #
# Fixed-horizon {1,3,6} secondary-stability effects (Finding 5; EXP-021 reuse)
# --------------------------------------------------------------------------- #
def fixed_horizon_effects(reaction: pl.DataFrame) -> dict[str, dict[int, float]]:
    """Per-domain fixed-horizon excess effect from EXP-021 reaction observations.

    Uses the validated EXP-021 symmetric fixed-horizon paired excess (the exact
    EXP-027-calibrated construction). Returns {domain: {horizon: domain_effect_bps}}
    using the frozen ``domain_effect`` estimator on reportable rows.
    """
    rep = ensure_bool(reaction, ("reportable",)).filter(pl.col("reportable"))
    out: dict[str, dict[int, float]] = {}
    for domain in DOMAINS:
        out[domain] = {}
        for h in HORIZONS:
            sub = rep.filter((pl.col("domain") == domain) & (pl.col("horizon") == h))
            if sub.height == 0:
                out[domain][h] = float("nan")
                continue
            diffs = sub.get_column("paired_diff_bps").to_numpy().astype(float)
            insts = sub.get_column("instrument").to_numpy()
            present = [i for i in INSTRUMENTS if (insts == i).any()]
            out[domain][h] = domain_effect(diffs, insts, present)
    return out


# --------------------------------------------------------------------------- #
# Frozen-tail inference on a per-event excess table (Finding 1)
# --------------------------------------------------------------------------- #
def reportable_instruments(cell: pl.DataFrame) -> list[str]:
    """Instruments in a domain meeting per-instrument reportability thresholds."""
    out = []
    for inst in INSTRUMENTS:
        sub = cell.filter(pl.col("instrument") == inst)
        n_bull = sub.filter(pl.col("direction") == 1).height
        n_bear = sub.filter(pl.col("direction") == -1).height
        if sub.height >= MIN_REPORTABLE_EVENTS and n_bull >= MIN_DIRECTION_EVENTS and n_bear >= MIN_DIRECTION_EVENTS:
            out.append(inst)
    return out


def infer_domain(cell: pl.DataFrame, rng: np.random.Generator) -> dict[str, Any]:
    """Frozen-tail inference (effect, regime-cluster bootstrap CI, permutation p) on one domain."""
    insts = reportable_instruments(cell)
    total = cell.height
    n_bull = cell.filter(pl.col("direction") == 1).height
    n_bear = cell.filter(pl.col("direction") == -1).height
    base = {"n_events": total, "n_bull": n_bull, "n_bear": n_bear,
            "n_instruments": len(insts), "reportable_instruments": insts}
    if len(insts) < DOMAIN_MIN_INSTRUMENTS:
        return {**base, "effect_bps": None, "ci_low": None, "ci_high": None,
                "ci_half_width": None, "raw_p": None}

    cell = cell.filter(pl.col("instrument").is_in(insts))
    diffs = cell.get_column("paired_excess_bps").to_numpy().astype(float)
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
    return {**base, "effect_bps": effect, "ci_low": ci_low, "ci_high": ci_high,
            "ci_half_width": (ci_high - ci_low) / 2.0, "raw_p": raw_p}


def run_primary(primary: pl.DataFrame, fixedh: dict[str, dict[int, float]]) -> dict[str, dict[str, Any]]:
    """PRIMARY per-domain verdicts via the frozen tail + Holm + secondary-horizon stability."""
    results: dict[str, dict[str, Any]] = {}
    raw_p: dict[str, float] = {}
    for domain in DOMAINS:
        cell = primary.filter(pl.col("domain") == domain)
        rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "primary", domain))
        res = infer_domain(cell, rng)
        results[domain] = res
        if res["raw_p"] is not None:
            raw_p[domain] = res["raw_p"]

    adjusted = holm_adjust(raw_p) if raw_p else {}
    for domain, res in results.items():
        hp = adjusted.get(domain)
        res["holm_p"] = hp
        if res["effect_bps"] is None or hp is None:
            res["verdict"] = "UNDER_POWERED"
            continue
        eff_h1 = fixedh.get(domain, {}).get(SEC_LOW_HORIZON, res["effect_bps"])
        eff_h6 = fixedh.get(domain, {}).get(SEC_HIGH_HORIZON, res["effect_bps"])
        res["sec_h1_bps"], res["sec_h6_bps"] = eff_h1, eff_h6
        res["verdict"] = decide_label(res["effect_bps"], res["ci_low"], res["ci_high"],
                                      hp, ALPHA, eff_h1, eff_h6)
    return results


# --------------------------------------------------------------------------- #
# SECONDARY (non-binding): endogenous-exit event vs fixed-window control
# --------------------------------------------------------------------------- #
def _regime_lut_and_base(state_cell: pl.DataFrame, trig: np.ndarray, n: int):
    """Regime LUT + per-regime eligible control base (reuses EXP-022 helpers)."""
    lut = EXP022.build_regime_lut(state_cell)
    is_trig, near = EXP022.build_exclusion_masks(n, trig)
    base = {rid: EXP022.regime_candidate_base(m["start_idx"], m["end_idx"], is_trig, near)
            for rid, m in lut.items()}
    return lut, base


def build_secondary_excess(
    primary: pl.DataFrame, events: pl.DataFrame, state: pl.DataFrame,
    frames: dict[tuple[str, str], pl.DataFrame], log_close: dict[tuple[str, str], np.ndarray],
) -> pl.DataFrame:
    """Asymmetric excess: event own-exit lifetime - mean fixed-window control of equal hold.

    The control window length equals the event's realized hold (bars_to_completion),
    an outcome — hence this construction is non-binding and gated by a placebo-null.
    Controls are selected by the EXP-021 nearest-anchor-age rule at that horizon.
    """
    ev_meta = events.select("instrument", "domain", "regime_id", "direction",
                            "trigger_idx", "anchor_idx", "anchor_age_bars", "is_pyramid_bounce")
    # event hold + own-exit lifetime come from the PRIMARY (EXP-022) table via join key.
    lt = pl.read_csv(EXP022_RESULTS / "lifetime_observations.csv")
    ev_life = lt.filter((pl.col("role") == "event") & pl.col("outcome").is_in(COMPLETED_OUTCOMES)).select(
        "instrument", "domain", "regime_id", "direction", "event_trigger_idx",
        "bars_to_completion", "lifetime_bps")
    joined = ev_meta.join(
        ev_life, left_on=["instrument", "domain", "regime_id", "direction", "trigger_idx"],
        right_on=["instrument", "domain", "regime_id", "direction", "event_trigger_idx"], how="inner")

    rows: list[dict[str, Any]] = []
    for (inst, domain), frame in frames.items():
        cell = joined.filter((pl.col("instrument") == inst) & (pl.col("domain") == domain))
        if cell.height == 0:
            continue
        lc = log_close[(inst, domain)]
        n = lc.size
        state_cell = state.filter((pl.col("instrument") == inst) & (pl.col("domain") == domain))
        trig = cell.get_column("trigger_idx").to_numpy().astype(np.int64)
        lut, base = _regime_lut_and_base(state_cell, trig, n)
        for ev in cell.iter_rows(named=True):
            rid, d, t = int(ev["regime_id"]), int(ev["direction"]), int(ev["trigger_idx"])
            hold = int(ev["bars_to_completion"])
            if rid not in base or hold < 1:
                continue
            controls = EXP021.select_controls(base[rid], lut[rid]["anchor_idx"],
                                               int(ev["anchor_age_bars"]), t, hold, n)
            if len(controls) < EM.MIN_CONTROLS:
                continue
            c_idx = np.array(controls, dtype=np.int64)
            ctrl_ret = 10_000.0 * d * (lc[c_idx + hold] - lc[c_idx])
            excess = float(ev["lifetime_bps"]) - float(np.mean(ctrl_ret))
            rows.append({"instrument": inst, "domain": domain, "regime_id": rid,
                         "direction": d, "is_pyramid_bounce": ev["is_pyramid_bounce"],
                         "event_trigger_idx": t, "paired_excess_bps": excess,
                         "n_controls": len(controls)})
    return pl.DataFrame(rows)


def calibrate_secondary_null(
    events: pl.DataFrame, state: pl.DataFrame,
    frames: dict[tuple[str, str], pl.DataFrame], log_close: dict[tuple[str, str], np.ndarray],
) -> dict[str, dict[str, Any]]:
    """Predeclared placebo-null for the asymmetric construction (bounded draws).

    Places placebo events at random same-regime non-trigger bars, transfers a real
    event's target distances, resolves the endogenous hold via the EXP-022 exit
    rule, builds the fixed-window control of that hold, and measures FPR + mean
    null-excess per domain. Calibrated iff FPR <= ALPHA and |null-excess| small.
    Reuses EXP-022 ``scan_lifetime`` / ``transfer_targets`` unchanged.
    """
    per_domain: dict[str, list[dict[str, float]]] = {d: [] for d in DOMAINS}
    for draw in tqdm(range(N_PLACEBO_DRAWS), desc="secondary placebo-null"):
        draw_rows = {d: [] for d in DOMAINS}
        for (inst, domain), frame in frames.items():
            close = frame.get_column("Close").to_numpy().astype(float)
            lc = log_close[(inst, domain)]
            n = lc.size
            ev_cell = events.filter((pl.col("instrument") == inst) & (pl.col("domain") == domain))
            if ev_cell.height < MIN_REPORTABLE_EVENTS:
                continue
            state_cell = state.filter((pl.col("instrument") == inst) & (pl.col("domain") == domain))
            lut = EXP022.build_regime_lut(state_cell)
            tc_map = EXP022.build_trend_change_map(state_cell)
            trig = ev_cell.get_column("trigger_idx").to_numpy().astype(np.int64)
            is_trig, near = EXP022.build_exclusion_masks(n, trig)
            rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "secnull", domain, inst, draw))
            _placebo_cell(ev_cell, lut, tc_map, is_trig, near, close, lc, n, rng, draw_rows[domain], inst, domain)
        for domain in DOMAINS:
            if draw_rows[domain]:
                per_domain[domain].append(_draw_effect(pl.DataFrame(draw_rows[domain])))
    return _summarize_null(per_domain)


def _placebo_cell(ev_cell, lut, tc_map, is_trig, near, close, lc, n, rng, sink, inst, domain) -> None:
    """Place placebo events in one cell/draw and append their asymmetric excesses to ``sink``."""
    targets = ev_cell.select("regime_id", "direction", "favorable_target_at_trigger",
                             "adverse_target_at_trigger", "trigger_close", "anchor_age_bars")
    by_regime: dict[int, int] = {}
    for rid in ev_cell.get_column("regime_id").to_list():
        by_regime[int(rid)] = by_regime.get(int(rid), 0) + 1
    for rid, k in by_regime.items():
        if rid not in lut:
            continue
        m = lut[rid]
        base = EXP022.regime_candidate_base(m["start_idx"], m["end_idx"], is_trig, near)
        if base.size == 0:
            continue
        placebos = rng.choice(base, size=min(k, base.size), replace=False)
        sample = targets.filter(pl.col("regime_id") == rid)
        if sample.height == 0:
            continue
        tgt = sample.row(rng.integers(0, sample.height), named=True)
        d = int(m["direction"])
        for p in placebos:
            p = int(p)
            f_bps, a_bps, c_fav, c_adv = EXP022.transfer_targets(
                d, float(tgt["favorable_target_at_trigger"]), float(tgt["adverse_target_at_trigger"]),
                float(tgt["trigger_close"]), float(close[p]))
            if not (f_bps > 0 and a_bps < 0):
                continue
            outcome, comp_idx, hold, life_bps, _ = EXP022.scan_lifetime(
                close, lc, p, d, c_fav, c_adv, tc_map.get(rid), n - 1)
            if outcome not in COMPLETED_OUTCOMES or hold is None or hold < 1 or p + hold > n - 1:
                continue
            controls = EXP021.select_controls(base, m["anchor_idx"], int(tgt["anchor_age_bars"]), p, hold, n)
            if len(controls) < EM.MIN_CONTROLS:
                continue
            c_idx = np.array(controls, dtype=np.int64)
            ctrl_ret = 10_000.0 * d * (lc[c_idx + hold] - lc[c_idx])
            sink.append({"instrument": inst, "domain": domain, "regime_id": rid,
                         "direction": d, "paired_excess_bps": float(life_bps) - float(np.mean(ctrl_ret))})


def _draw_effect(cell: pl.DataFrame) -> dict[str, float]:
    """One placebo draw's domain effect + FOR flag (frozen tail, single-domain)."""
    insts = [i for i in INSTRUMENTS if cell.filter(pl.col("instrument") == i).height >= MIN_REPORTABLE_EVENTS]
    if len(insts) < DOMAIN_MIN_INSTRUMENTS:
        return {"effect": float("nan"), "for_flag": 0.0, "powered": 0.0}
    cell = cell.filter(pl.col("instrument").is_in(insts))
    diffs = cell.get_column("paired_excess_bps").to_numpy().astype(float)
    inst_labels = cell.get_column("instrument").to_numpy()
    dir_labels = cell.get_column("direction").to_numpy().astype(int)
    regime_labels = cell.get_column("regime_id").to_numpy().astype(int)
    rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "secnull_inf", int(diffs.size)))
    effect = domain_effect(diffs, inst_labels, insts)
    strata = build_strata(diffs, inst_labels, dir_labels, regime_labels, insts)
    boot = bootstrap_effect_distribution(strata, insts, rng, N_BOOT, CHUNK)
    ci_low = float(np.percentile(boot, CI_PERCENTILES[0]))
    counts = np.array([int((inst_labels == i).sum()) for i in insts], dtype=float)
    inst_index = np.array([insts.index(i) for i in inst_labels], dtype=np.int64)
    p = permutation_p(diffs, inst_index, counts, effect, rng, N_PERM, CHUNK)
    for_flag = float(effect > 0 and ci_low > 0 and p <= ALPHA)
    return {"effect": effect, "for_flag": for_flag, "powered": 1.0}


def _summarize_null(per_domain: dict[str, list[dict[str, float]]]) -> dict[str, dict[str, Any]]:
    """FPR + mean null-excess + calibrated flag per domain."""
    out: dict[str, dict[str, Any]] = {}
    for domain, draws in per_domain.items():
        powered = [d for d in draws if d["powered"] > 0]
        if not powered:
            out[domain] = {"n_draws": len(draws), "fpr": None, "null_excess_bps": None, "calibrated": False}
            continue
        fpr = float(np.mean([d["for_flag"] for d in powered]))
        null_excess = float(np.nanmean([d["effect"] for d in powered]))
        out[domain] = {"n_draws": len(powered), "fpr": fpr, "null_excess_bps": null_excess,
                       "calibrated": bool(fpr <= ALPHA)}
    return out


def run_secondary(sec_excess: pl.DataFrame, calibration: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """SECONDARY per-domain effects (non-binding); verdict gated by the placebo-null calibration."""
    results: dict[str, dict[str, Any]] = {}
    raw_p: dict[str, float] = {}
    for domain in DOMAINS:
        cell = sec_excess.filter(pl.col("domain") == domain) if sec_excess.height else pl.DataFrame()
        rng = np.random.default_rng(seed_for(EXPERIMENT_ID, "secondary", domain))
        res = infer_domain(cell, rng) if cell.height else {"effect_bps": None}
        results[domain] = res
        if res.get("raw_p") is not None:
            raw_p[domain] = res["raw_p"]
    adjusted = holm_adjust(raw_p) if raw_p else {}
    for domain, res in results.items():
        cal = calibration.get(domain, {})
        res["holm_p"] = adjusted.get(domain)
        if not cal.get("calibrated", False):
            res["verdict"] = "NOT_CALIBRATED"
        elif res.get("effect_bps") is None or res.get("holm_p") is None:
            res["verdict"] = "UNDER_POWERED"
        else:
            res["verdict"] = decide_label(res["effect_bps"], res["ci_low"], res["ci_high"],
                                          res["holm_p"], ALPHA, res["effect_bps"], res["effect_bps"])
    return results


# --------------------------------------------------------------------------- #
# Equity companion (non-gating) — PRIMARY symmetric trades
# --------------------------------------------------------------------------- #
def equity_companion(primary: pl.DataFrame) -> dict[str, dict[str, Any]]:
    """Exposure-matched equity companion on PRIMARY own-exit trades (non-gating)."""
    out: dict[str, dict[str, Any]] = {}
    for domain in DOMAINS:
        cell = primary.filter(pl.col("domain") == domain)
        adv, sortino_diff = [], []
        for inst in INSTRUMENTS:
            sub = cell.filter(pl.col("instrument") == inst)
            if sub.height == 0:
                continue
            strat = sub.get_column("lifetime_bps").to_numpy().astype(float)
            base = sub.get_column("mean_control_lifetime_bps").to_numpy().astype(float)
            adv.append(float(np.nansum(strat) - np.nansum(base)))
            sortino_diff.append(sortino_ratio(strat) - sortino_ratio(base))
        if not adv:
            out[domain] = {"strategy_terminal_bps": float("nan"), "baseline_terminal_bps": float("nan"),
                           "advantage_bps": float("nan"), "advantage_rate": float("nan"),
                           "sortino_diff": float("nan")}
            continue
        cell_strat = float(np.mean([
            float(np.nansum(cell.filter(pl.col("instrument") == i).get_column("lifetime_bps").to_numpy()))
            for i in INSTRUMENTS if cell.filter(pl.col("instrument") == i).height]))
        cell_base = float(np.mean([
            float(np.nansum(cell.filter(pl.col("instrument") == i).get_column("mean_control_lifetime_bps").to_numpy()))
            for i in INSTRUMENTS if cell.filter(pl.col("instrument") == i).height]))
        out[domain] = {"strategy_terminal_bps": cell_strat, "baseline_terminal_bps": cell_base,
                       "advantage_bps": float(np.mean(adv)),
                       "advantage_rate": float(np.mean([a > 0 for a in adv])),
                       "sortino_diff": float(np.nanmean(sortino_diff))}
    return out


# --------------------------------------------------------------------------- #
# Plotting (4)
# --------------------------------------------------------------------------- #
def _verdict_color(verdict: str | None) -> str:
    if verdict == "EVIDENCE_FOR":
        return "#2ecc71"
    if verdict and "AGAINST" in verdict:
        return "#e74c3c"
    return "#95a5a6"


def plot_expectancy(primary_res: dict[str, dict[str, Any]], primary: pl.DataFrame, path: Path) -> None:
    """Forest plot of PRIMARY per-domain effect with 95% CI + pyramid split inset."""
    fig, ax = plt.subplots(figsize=(10, 5))
    for i, domain in enumerate(DOMAINS):
        r = primary_res[domain]
        if r.get("effect_bps") is None:
            ax.text(0, i, f"{domain}: {r.get('verdict')}", va="center")
            continue
        ax.errorbar(r["effect_bps"], i, xerr=[[r["effect_bps"] - r["ci_low"]], [r["ci_high"] - r["effect_bps"]]],
                    fmt="o", color=_verdict_color(r.get("verdict")), capsize=4, markersize=8)
        ax.annotate(f"n={r['n_events']}  p={r.get('holm_p')}  {r.get('verdict')}",
                    xy=(r["ci_high"], i), xytext=(6, 0), textcoords="offset points", fontsize=8, va="center")
    ax.axvline(0, color="black", ls="--", lw=0.8, alpha=0.6)
    ax.set_yticks(range(len(DOMAINS)))
    ax.set_yticklabels(DOMAINS)
    ax.set_xlabel("PRIMARY own-exit matched-control excess (bps), 95% CI")
    ax.set_title("EXP-028 PRIMARY per-domain event-level expectancy", fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_equity(equity: dict[str, dict[str, Any]], path: Path) -> None:
    """Strategy vs exposure-matched baseline terminal equity per domain."""
    fig, axes = plt.subplots(1, len(DOMAINS), figsize=(5 * len(DOMAINS), 4), squeeze=False)
    for j, domain in enumerate(DOMAINS):
        ax = axes[0, j]
        e = equity[domain]
        ax.bar([0, 1], [e["strategy_terminal_bps"], e["baseline_terminal_bps"]],
               color=["#3498db", "#e67e22"], width=0.5)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["Strategy", "Exposure-matched\nbaseline"], fontsize=8)
        ax.axhline(0, color="black", lw=0.5)
        ax.set_title(f"{domain}  (adv={e['advantage_bps']:.1f} bps)", fontsize=10)
        ax.set_ylabel("Cumulative own-exit log return (bps)")
    fig.suptitle("EXP-028 equity companion (exposure-matched, non-gating)")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_diagnostics(primary: pl.DataFrame, path: Path) -> None:
    """Event count by domain/direction and pyramid split."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    x = range(len(DOMAINS))
    bull = [primary.filter((pl.col("domain") == d) & (pl.col("direction") == 1)).height for d in DOMAINS]
    bear = [primary.filter((pl.col("domain") == d) & (pl.col("direction") == -1)).height for d in DOMAINS]
    axes[0].bar([i - 0.2 for i in x], bull, 0.4, label="Bull", color="#2ecc71")
    axes[0].bar([i + 0.2 for i in x], bear, 0.4, label="Bear", color="#e74c3c")
    axes[0].axhline(MIN_REPORTABLE_EVENTS, color="black", ls="--", lw=0.8, label=f"min {MIN_REPORTABLE_EVENTS}")
    axes[0].set_xticks(list(x))
    axes[0].set_xticklabels(DOMAINS)
    axes[0].set_ylabel("PRIMARY event count")
    axes[0].set_title("Events by domain × direction")
    axes[0].legend(fontsize=8)

    pyr = [primary.filter((pl.col("domain") == d) & (pl.col("is_pyramid_bounce"))).height for d in DOMAINS]
    nonpyr = [primary.filter((pl.col("domain") == d) & (~pl.col("is_pyramid_bounce"))).height for d in DOMAINS]
    axes[1].bar([i - 0.2 for i in x], nonpyr, 0.4, label="Non-pyramid", color="#34495e")
    axes[1].bar([i + 0.2 for i in x], pyr, 0.4, label="Pyramid", color="#9b59b6")
    axes[1].set_xticks(list(x))
    axes[1].set_xticklabels(DOMAINS)
    axes[1].set_title("Pyramid split (included as diagnostic)")
    axes[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_verdict_summary(primary_res: dict, secondary_res: dict, calibration: dict, path: Path) -> None:
    """PRIMARY (binding) vs SECONDARY (calibrated flag) per-domain verdicts."""
    fig, ax = plt.subplots(figsize=(11, 4))
    for i, domain in enumerate(DOMAINS):
        pr, sr = primary_res[domain], secondary_res.get(domain, {})
        if pr.get("effect_bps") is not None:
            ax.errorbar(pr["effect_bps"], i, xerr=[[pr["effect_bps"] - pr["ci_low"]], [pr["ci_high"] - pr["effect_bps"]]],
                        fmt="o", color=_verdict_color(pr.get("verdict")), capsize=4, markersize=10)
        cal = calibration.get(domain, {}).get("calibrated", False)
        sec_txt = f"sec={sr.get('verdict')}" + ("" if cal else " (NOT_CALIBRATED)")
        ax.text(-0.02, i, domain, ha="right", va="center", fontweight="bold", transform=ax.get_yaxis_transform())
        txt = f"PRIMARY {pr.get('verdict')}  p={pr.get('holm_p')}  n={pr.get('n_events')}   |   {sec_txt}"
        ax.text(1.02, i, txt, va="center", fontsize=8, transform=ax.get_yaxis_transform())
    ax.axvline(0, color="black", ls="--", lw=0.8, alpha=0.5)
    ax.set_yticks([])
    ax.set_xlabel("PRIMARY effect (bps) with 95% CI")
    ax.set_title("EXP-028 verdict summary — PRIMARY binding vs SECONDARY diagnostic", fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Phase outcome + save
# --------------------------------------------------------------------------- #
def phase_outcome(primary_res: dict[str, dict[str, Any]]) -> str:
    """Bind the phase outcome on the PRIMARY gate only."""
    verdicts = [primary_res[d].get("verdict") for d in DOMAINS]
    if any(v == "EVIDENCE_FOR" for v in verdicts):
        return "EVAL_SUPPORTED"
    if any(v in (None, "UNDER_POWERED") or (v and "INCONCLUSIVE" in v) for v in verdicts):
        return "INCONCLUSIVE"
    return "EVAL_REFUTED"


def save_outputs(primary_res, secondary_res, calibration, equity, fixedh, primary, sec_excess,
                 metadata) -> None:
    """Write all result CSVs, plots, and run metadata."""
    ensure_output_dirs()
    write_rows(RESULTS_DIR / "event_level_results.csv", [
        {"domain": d, **{k: primary_res[d].get(k) for k in
         ("effect_bps", "ci_low", "ci_high", "ci_half_width", "raw_p", "holm_p",
          "sec_h1_bps", "sec_h6_bps", "n_events", "n_bull", "n_bear", "n_instruments", "verdict")}}
        for d in DOMAINS])
    write_rows(RESULTS_DIR / "secondary_results.csv", [
        {"domain": d, **{k: secondary_res[d].get(k) for k in
         ("effect_bps", "ci_low", "ci_high", "raw_p", "holm_p", "n_events", "verdict")}}
        for d in DOMAINS])
    write_rows(RESULTS_DIR / "secondary_calibration.csv", [
        {"domain": d, **calibration.get(d, {})} for d in DOMAINS])
    write_rows(RESULTS_DIR / "equity_companion.csv", [{"domain": d, **equity[d]} for d in DOMAINS])
    write_rows(RESULTS_DIR / "event_diagnostics.csv", [
        {"domain": d, "n_events": primary.filter(pl.col("domain") == d).height,
         "n_bull": primary.filter((pl.col("domain") == d) & (pl.col("direction") == 1)).height,
         "n_bear": primary.filter((pl.col("domain") == d) & (pl.col("direction") == -1)).height,
         "n_pyramid": primary.filter((pl.col("domain") == d) & pl.col("is_pyramid_bounce")).height,
         "n_nonpyramid": primary.filter((pl.col("domain") == d) & ~pl.col("is_pyramid_bounce")).height,
         "fixedh_h1_bps": fixedh.get(d, {}).get(SEC_LOW_HORIZON),
         "fixedh_h3_bps": fixedh.get(d, {}).get(3),
         "fixedh_h6_bps": fixedh.get(d, {}).get(SEC_HIGH_HORIZON)}
        for d in DOMAINS])
    (RESULTS_DIR / "run_metadata.json").write_text(json.dumps(metadata, indent=2, default=str))

    plot_expectancy(primary_res, primary, PLOTS_DIR / "event_expectancy.png")
    plot_equity(equity, PLOTS_DIR / "equity_companion.png")
    plot_diagnostics(primary, PLOTS_DIR / "event_diagnostics.png")
    plot_verdict_summary(primary_res, secondary_res, calibration, PLOTS_DIR / "verdict_summary.png")
    LOGGER.info("Wrote results to %s and plots to %s", RESULTS_DIR, PLOTS_DIR)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    configure_logging()
    LOGGER.info("=" * 70)
    LOGGER.info("EXP-028: Faithful Selective AVWAP Strategy Re-Screen (dual gate)")
    LOGGER.info("=" * 70)
    ensure_output_dirs()

    frozen_hash = verify_frozen_inference()
    cm_pass = verify_control_matching()
    deps = check_dependencies()

    LOGGER.info("Building domain frames (EXP-020 convention, holdout-fenced)")
    frames, analysis_end = build_frames()
    events = EXP022.cast_time_columns(load_csv(EXP020_RESULTS / "avwap_events.csv"),
                                      ("anchor_time", "armed_time", "trigger_time"))
    state = load_csv(EXP020_RESULTS / "avwap_state_summary.csv")
    align_cells = validate_alignment(events, frames)
    log_close = frame_log_close(frames)

    LOGGER.info("PRIMARY: symmetric own-exit lifetime excess (EXP-022)")
    lifetime = load_csv(EXP022_RESULTS / "lifetime_observations.csv")
    primary, primary_diag = build_primary_excess(lifetime, log_close)

    LOGGER.info("Fixed-horizon {1,3,6} secondary-stability effects (EXP-021)")
    reaction = load_csv(EXP021_RESULTS / "reaction_observations.csv")
    fixedh = fixed_horizon_effects(reaction)

    primary_res = run_primary(primary, fixedh)

    LOGGER.info("SECONDARY: asymmetric construction + predeclared placebo-null")
    calibration = calibrate_secondary_null(events, state, frames, log_close)
    sec_excess = build_secondary_excess(primary, events, state, frames, log_close)
    secondary_res = run_secondary(sec_excess, calibration)

    LOGGER.info("Equity companion (non-gating)")
    equity = equity_companion(primary)

    outcome = phase_outcome(primary_res)
    metadata = {
        "experiment": EXPERIMENT_ID,
        "title": "Faithful Selective AVWAP Strategy Re-Screen",
        "overall_verdict": outcome,
        "binding_gate": "PRIMARY_symmetric_own_exit_lifetime_excess",
        "primary_per_domain": {d: primary_res[d].get("verdict") for d in DOMAINS},
        "secondary_per_domain": {d: secondary_res[d].get("verdict") for d in DOMAINS},
        "secondary_calibrated": {d: calibration.get(d, {}).get("calibrated") for d in DOMAINS},
        "dependencies": deps,
        "frozen_inference_hash": frozen_hash,
        "control_matching_equivalence_pass": bool(cm_pass),
        "alignment_cells_checked": align_cells,
        "reconciliation_bad": primary_diag["reconciliation_bad"],
        "pyramids_included": True,
        "pyramid_split": {"pyramid": primary_diag["n_pyramid"], "non_pyramid": primary_diag["n_nonpyramid"]},
        "analysis_end_per_instrument": analysis_end,
        "parameters": {"domains": list(DOMAINS), "instruments": list(INSTRUMENTS),
                       "alpha": ALPHA, "n_boot": N_BOOT, "n_perm": N_PERM,
                       "n_placebo_draws": N_PLACEBO_DRAWS, "horizons": list(HORIZONS),
                       "min_reportable_events": MIN_REPORTABLE_EVENTS,
                       "min_direction_events": MIN_DIRECTION_EVENTS},
        "interpretation_bound": ("PRIMARY EVAL_REFUTED is about the strategy-with-EXP-022-exit, "
                                 "NOT 'the AVWAP bounce event has no edge' (EXP-021 shows a positive "
                                 "fixed-horizon reaction)."),
    }
    save_outputs(primary_res, secondary_res, calibration, equity, fixedh, primary, sec_excess, metadata)

    LOGGER.info("=" * 70)
    LOGGER.info("Phase outcome (PRIMARY-binding): %s", outcome)
    for d in DOMAINS:
        r = primary_res[d]
        LOGGER.info("  %s PRIMARY=%s effect=%s holm_p=%s n=%s | SECONDARY=%s",
                    d, r.get("verdict"), r.get("effect_bps"), r.get("holm_p"),
                    r.get("n_events"), secondary_res[d].get("verdict"))
    if outcome == "EVAL_REFUTED":
        LOGGER.info("  -> routes to FAMILY_REVIEW (Phase 006 §7); not a no-edge claim on the event")
    LOGGER.info("=" * 70)


if __name__ == "__main__":
    main()
