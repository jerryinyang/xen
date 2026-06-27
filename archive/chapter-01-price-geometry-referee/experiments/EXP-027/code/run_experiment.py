"""Experiment EXP-027: Event-Level Evaluation Method — Definition + Sparse-Regime Calibration.

Implements the approved analysis plan (analysis-plan.md). EXP-027 is the event-level,
sparse-activity analog of EXP-003/005: it measures the FPR, TPR, and empirical
**event-level MDE** of the EXP-021/022 matched-control decision rule when that rule
is applied to a **sparse** (~3-12% trigger prevalence) synthetic event process, so a
fit-for-purpose yardstick exists for re-screening the faithful AVWAP strategy
(EXP-028). The frozen per-bar suite is never invoked — the prior-run defect was
applying a per-bar floor to a ~6%-active signal.

Pipeline:
    1. EXP-020 substrate dependency gate (regime scaffolding only; the real
       avwap_events.csv OUTCOMES are deliberately NOT read — anti-overfitting fence).
    2. Holdout-safe domain reconstruction (first-70% slice) + per-cell precompute.
    3. Sparse synthetic-event substrate: placebo placement in real regimes; two nulls
       (N1 placebo-on-real, N2 block-permuted); additive per-event planted drift.
    4. Per-draw decision pipeline reusing the EXP-021 inference unchanged in structure.
    5. Operating characteristics: FPR / TPR / event-level MDE with Wilson intervals.
    6. Exposure-matched equity-curve companion (non-gating).
    7. Determinism replay + METHOD_VALID/INVALID/INCONCLUSIVE verdict.

Run:
    cd <project-root> && python python/experiments/EXP-027/code/run_experiment.py

Compute note: this is a calibration run (many bootstrap/permutation verdicts over a
grid of draws). Expect a multi-minute to ~hour runtime depending on machine; tqdm
reports progress over the (null x activity x draw) loops.
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402  (backend must be set before pyplot)
import numpy as np  # noqa: E402
import polars as pl  # noqa: E402
from tqdm.auto import tqdm  # noqa: E402

from xen.referee_calibration import (  # noqa: E402
    build_domain_frames,
    estimate_block_length,
    list_timebar_files,
    load_analysis_data,
    seed_for,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import event_method as em  # noqa: E402  (experiment-local helper in the same code/ dir)


LOGGER = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
EXPERIMENT_ID = "EXP-027"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = PROJECT_ROOT / "data"
EXPERIMENT_DIR = PROJECT_ROOT / "python" / "experiments" / EXPERIMENT_ID
RESULTS_DIR = EXPERIMENT_DIR / "results"
PLOTS_DIR = EXPERIMENT_DIR / "plots"
DEP_RESULTS_DIR = PROJECT_ROOT / "python" / "experiments" / "EXP-020" / "results"

DOMAINS: tuple[str, ...] = ("5m", "1h", "4h")

# Calibration grid (analysis-plan.md). Decoupled from EXP-021's observed magnitudes.
P_TRIG_GRID: tuple[float, ...] = (0.03, 0.06, 0.12)   # brackets the real ~6% active rate
PRIMARY_PTRIG: float = 0.06
EDGE_GRID_BPS: tuple[float, ...] = (0.0, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0)
ALPHA_GRID: tuple[float, ...] = (0.10, 0.05, 0.01)
PRIMARY_ALPHA: float = 0.05
NULL_GENERATORS: tuple[str, ...] = ("placebo_on_real", "block_permuted")

N_DRAWS: int = 500
N_BOOT: int = 1_000
N_PERM: int = 1_000
BOOT_CHUNK: int = 2_000
PERM_CHUNK: int = 500           # bounds the (chunk x events) permutation matrix peak memory

# Clustered placement (predeclared structural null parameters; ~50% pyramids per
# the documented aggregate share, never real event locations).
PYRAMID_FRAC: float = 0.5
PYRAMID_SPAN: int = 6

# Recovery / precision (EXP-005 precedent).
TPR_TARGET: float = 0.80
FPR_HALFWIDTH_MAX: float = 0.03
TPR_HALFWIDTH_MAX: float = 0.05

REPLAY_DRAWS: int = 12          # determinism replay on a fast cell
EQUITY_PLOT_EDGE_BPS: float = 8.0

# EXP-020 dependency expectations (anti-overfitting: events file is NOT required/read).
DEP_REQUIRED_STATUS = "SUPPORTED_FULL"
DEP_REQUIRED_DOMAINS = {"5m", "1h", "4h"}
REQUIRED_DEP_ARTIFACTS: tuple[str, ...] = (
    "run_metadata.json",
    "avwap_state_summary.csv",
    "domain_readiness.csv",
    "invariant_checks.csv",
    "determinism_check.csv",
)

REGISTRY_REFS = {
    "candidate_family": "CF-AVWAP-001",
    "registration": "METHOD-001",
    "checkpoint": "docs/experiments-docs/checkpoints/2026-06-08-006-avwap-evaluation-correction",
    "anti_overfitting_fence": "real avwap_events.csv outcomes are not read; signal is synthetic",
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
    """Interpret CSV/JSON bool values consistently across parser versions."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return bool(value)


# --------------------------------------------------------------------------- #
# Dependency gate (regime scaffolding only — anti-overfitting fence)
# --------------------------------------------------------------------------- #
def check_dependency_gate() -> tuple[bool, list[str], dict[str, Any]]:
    """Assert the EXP-020 substrate gate using metadata + readiness/invariant/determinism.

    The real ``avwap_events.csv`` outcomes are deliberately excluded from the
    required artifacts and never loaded: EXP-027 is calibrated on synthetic events.
    """
    reasons: list[str] = []
    missing = [n for n in REQUIRED_DEP_ARTIFACTS if not (DEP_RESULTS_DIR / n).exists()]
    if missing:
        return False, [f"missing EXP-020 artifacts: {missing}"], {}
    meta = json.loads((DEP_RESULTS_DIR / "run_metadata.json").read_text())
    if meta.get("overall_status") != DEP_REQUIRED_STATUS:
        reasons.append(f"overall_status={meta.get('overall_status')} != {DEP_REQUIRED_STATUS}")
    if set(meta.get("ready_domains", [])) != DEP_REQUIRED_DOMAINS:
        reasons.append(f"ready_domains={meta.get('ready_domains')} != {sorted(DEP_REQUIRED_DOMAINS)}")
    if int(meta.get("invariant_failure_count", -1)) != 0:
        reasons.append(f"invariant_failure_count={meta.get('invariant_failure_count')} != 0")
    if not _truthy(meta.get("determinism_pass", False)):
        reasons.append("determinism_pass is not true")
    invariant = pl.read_csv(DEP_RESULTS_DIR / "invariant_checks.csv")
    if "n_violations" in invariant.columns and int(invariant.get_column("n_violations").sum()) != 0:
        reasons.append("invariant_checks total n_violations != 0")
    return len(reasons) == 0, reasons, meta


def load_regime_summary() -> pl.DataFrame:
    """Load ONLY the EXP-020 regime scaffolding (no event outcomes)."""
    return pl.read_csv(DEP_RESULTS_DIR / "avwap_state_summary.csv", try_parse_dates=True)


# --------------------------------------------------------------------------- #
# Holdout-safe precompute (first-70% slice; real Close only)
# --------------------------------------------------------------------------- #
def build_precomputes(regimes: pl.DataFrame) -> tuple[dict[tuple[str, str], em.CellPrecompute], dict[str, str]]:
    """Rebuild first-70% domain bars and per-cell precompute; re-assert the holdout fence."""
    files = list_timebar_files(DATA_DIR)
    if not files:
        raise FileNotFoundError(f"no timebar files under {DATA_DIR / 'timebars'}")
    # One source per instrument, keyed by the Symbol column with latest-sorted wins
    # (matches EXP-020/021 selection). Keying by Symbol — not the filename — is robust
    # to auxiliary files such as timebars_analysis70_xauusd_*, which carry XAUUSD data
    # but would mis-parse to a phantom instrument from the filename alone. The fence
    # check then runs only on the surviving (correct) frame per cell.
    selected: dict[str, Any] = {}
    for path in tqdm(files, desc="load timebars"):
        data = load_analysis_data(path)
        selected[data.instrument] = data
    cells: dict[tuple[str, str], em.CellPrecompute] = {}
    analysis_end: dict[str, str] = {}
    for inst, data in selected.items():
        analysis_end[inst] = data.analysis_end
        for domain, frame in build_domain_frames(data.frame).items():
            cells[(inst, domain)] = _precompute_cell(inst, domain, frame, regimes)
    return cells, analysis_end


def _precompute_cell(instrument: str, domain: str, frame: pl.DataFrame, regimes: pl.DataFrame) -> em.CellPrecompute:
    """Build one cell's draw-independent arrays and validate regime indices in-range."""
    close = frame.get_column("Close").to_numpy().astype(float)
    n = close.shape[0]
    log_close = np.log(close)
    bar_ret = np.diff(log_close)
    reg = regimes.filter((pl.col("instrument") == instrument) & (pl.col("domain") == domain))
    start = reg.get_column("regime_start_idx").to_numpy().astype(np.int64)
    end = reg.get_column("regime_end_idx").to_numpy().astype(np.int64)
    anchor = reg.get_column("anchor_idx").to_numpy().astype(np.int64)
    if reg.height and (int(end.max()) >= n or int(start.min()) < 0 or int(anchor.min()) < 0):
        raise ValueError(
            f"{instrument}/{domain}: regime index outside first-70% frame [0,{n}) "
            "(holdout fence breach / domain reconstruction mismatch)."
        )
    train_rows = int(bar_ret.shape[0] * 0.7)
    block_length = estimate_block_length(bar_ret[:train_rows]) if train_rows >= 8 else 1
    dlog_real = {h: em.forward_logdiff_from_close(log_close, h) for h in em.HORIZONS}
    return em.CellPrecompute(
        instrument=instrument, domain=domain, n=n, log_close=log_close, bar_log_returns=bar_ret,
        block_length=int(block_length),
        regime_id=reg.get_column("regime_id").to_numpy().astype(np.int64),
        regime_dir=reg.get_column("direction").to_numpy().astype(np.int64),
        regime_start=start, regime_end=end, regime_anchor=anchor, dlog_real=dlog_real,
    )


# --------------------------------------------------------------------------- #
# Per-draw evaluation (reused EXP-021 inference, unchanged in structure)
# --------------------------------------------------------------------------- #
def _cell_dlog(pre: em.CellPrecompute, null_label: str, p_trig: float, draw: int) -> dict[int, np.ndarray]:
    """Active forward-return arrays: real (N1) or block-permuted (N2)."""
    if null_label == "placebo_on_real":
        return pre.dlog_real
    seed = seed_for(EXPERIMENT_ID, pre.domain, pre.instrument, null_label, p_trig, draw, "blockperm")
    rng = np.random.default_rng(seed)
    perm = em.block_permute_returns(pre.bar_log_returns, pre.block_length, rng)
    return {h: em.forward_logdiff_from_returns(perm, h, pre.n) for h in em.HORIZONS}


def _simulate_domain(
    cells: dict[tuple[str, str], em.CellPrecompute], instruments: list[str], domain: str,
    null_label: str, p_trig: float, draw: int,
) -> dict[str, em.CellEvents]:
    """Simulate every instrument's events for one domain/draw."""
    out: dict[str, em.CellEvents] = {}
    for inst in instruments:
        pre = cells[(inst, domain)]
        dlog = _cell_dlog(pre, null_label, p_trig, draw)
        rng = np.random.default_rng(
            seed_for(EXPERIMENT_ID, domain, inst, null_label, p_trig, draw, "placement")
        )
        out[inst] = em.simulate_cell(pre, dlog, p_trig, rng, PYRAMID_FRAC, PYRAMID_SPAN)
    return out


def _reportable_instruments(events: dict[str, em.CellEvents], instruments: list[str]) -> list[str]:
    """Instruments meeting the EXP-021 reportability thresholds for this draw/domain."""
    ok = []
    for inst in instruments:
        ev = events[inst]
        if ev.idx.size >= em.MIN_REPORTABLE_EVENTS and ev.n_bull >= em.MIN_DIRECTION_EVENTS \
                and ev.n_bear >= em.MIN_DIRECTION_EVENTS:
            ok.append(inst)
    return ok


def _domain_edge_stats(
    events: dict[str, em.CellEvents], reportable: list[str], domain: str,
    null_label: str, p_trig: float, draw: int, edges: tuple[float, ...],
) -> dict[float, dict[str, float]]:
    """Per-edge effect/CI/raw_p for one reportable domain/draw (bootstrap once; edge shifts CI).

    A planted edge ``g`` adds a constant to every per-event return, hence a pure
    +g shift of the paired differences, the effect, and the percentile CI. The
    sign-permutation p-value is recomputed per ``g`` (sign-flips of shifted data are
    not a shift of the flips).
    """
    diffs = {h: np.concatenate([events[i].paired_diff[h] for i in reportable]) for h in em.HORIZONS}
    inst_labels = np.concatenate([np.full(events[i].idx.size, i) for i in reportable])
    dir_labels = np.concatenate([events[i].direction for i in reportable])
    regime_labels = np.concatenate([events[i].regime for i in reportable])
    inst_sorted = sorted(reportable)
    primary = diffs[em.PRIMARY_HORIZON]
    effect0 = em.domain_effect(primary, inst_labels, inst_sorted)
    eff_h1 = em.domain_effect(diffs[1], inst_labels, inst_sorted)
    eff_h6 = em.domain_effect(diffs[6], inst_labels, inst_sorted)
    strata = em.build_strata(primary, inst_labels, dir_labels, regime_labels, inst_sorted)
    boot_rng = np.random.default_rng(seed_for(EXPERIMENT_ID, domain, null_label, p_trig, draw, "bootstrap"))
    boot = em.bootstrap_effect_distribution(strata, inst_sorted, boot_rng, N_BOOT, BOOT_CHUNK)
    ci0_low, ci0_high = (float(np.percentile(boot, em.CI_PERCENTILES[0])),
                         float(np.percentile(boot, em.CI_PERCENTILES[1])))
    index_lut = {inst: j for j, inst in enumerate(inst_sorted)}
    inst_index = np.array([index_lut[i] for i in inst_labels])
    counts = np.array([int((inst_index == j).sum()) for j in range(len(inst_sorted))], dtype=float)
    stats: dict[float, dict[str, float]] = {}
    for g in edges:
        perm_rng = np.random.default_rng(
            seed_for(EXPERIMENT_ID, domain, null_label, p_trig, draw, g, "permutation")
        )
        raw_p = em.permutation_p(primary + g, inst_index, counts, effect0 + g, perm_rng, N_PERM, PERM_CHUNK)
        stats[g] = {
            "effect": effect0 + g, "ci_low": ci0_low + g, "ci_high": ci0_high + g,
            "raw_p": raw_p, "effect_h1": eff_h1 + g, "effect_h6": eff_h6 + g,
            "n_events": int(primary.size),
        }
    return stats


# --------------------------------------------------------------------------- #
# Calibration loops + accumulation
# --------------------------------------------------------------------------- #
def _new_counter() -> dict[str, int]:
    return {"reportable": 0, **{f"for_a{a}": 0 for a in ALPHA_GRID}}


def run_calibration(
    cells: dict[tuple[str, str], em.CellPrecompute], instruments: list[str],
) -> dict[str, Any]:
    """Run all FPR/TPR draws and accumulate verdict counts, equity, and verdict rows."""
    fpr: dict[tuple[str, float, str], dict[str, dict[str, int]]] = {}      # (domain,p_trig,null) -> counter
    familywise: dict[tuple[float, str], dict[str, int]] = {}               # (p_trig,null) -> {n, for_a*}
    tpr: dict[tuple[str, float], dict[str, dict[str, int]]] = {}           # (domain,g) -> counter
    equity_rows: list[dict[str, Any]] = []
    verdict_rows: list[dict[str, Any]] = []
    equity_curves: dict[str, Any] = {}

    for null_label in NULL_GENERATORS:
        for p_trig in P_TRIG_GRID:
            edges = EDGE_GRID_BPS if (null_label == "placebo_on_real" and p_trig == PRIMARY_PTRIG) else (0.0,)
            familywise.setdefault((p_trig, null_label), {"n": 0, **{f"for_a{a}": 0 for a in ALPHA_GRID}})
            desc = f"{null_label} p_trig={p_trig}"
            for draw in tqdm(range(N_DRAWS), desc=desc, leave=False):
                _evaluate_one_draw(
                    cells, instruments, null_label, p_trig, draw, edges,
                    fpr, familywise, tpr, equity_rows, verdict_rows, equity_curves,
                )
    return {
        "fpr": fpr, "familywise": familywise, "tpr": tpr,
        "equity_rows": equity_rows, "verdict_rows": verdict_rows, "equity_curves": equity_curves,
    }


def _evaluate_one_draw(
    cells, instruments, null_label, p_trig, draw, edges,
    fpr, familywise, tpr, equity_rows, verdict_rows, equity_curves,
) -> None:
    """Evaluate one draw across all domains: Holm within draw, then record verdicts."""
    per_domain: dict[str, dict[float, dict[str, float]]] = {}
    reportable_map: dict[str, list[str]] = {}
    events_by_domain: dict[str, dict[str, em.CellEvents]] = {}
    for domain in DOMAINS:
        events = _simulate_domain(cells, instruments, domain, null_label, p_trig, draw)
        events_by_domain[domain] = events
        reportable = _reportable_instruments(events, instruments)
        reportable_map[domain] = reportable
        fpr.setdefault((domain, p_trig, null_label), _new_counter())
        if len(reportable) >= em.DOMAIN_MIN_INSTRUMENTS:
            per_domain[domain] = _domain_edge_stats(
                events, reportable, domain, null_label, p_trig, draw, edges
            )
    is_tpr_family = null_label == "placebo_on_real" and p_trig == PRIMARY_PTRIG
    for g in edges:
        raw_ps = {d: per_domain[d][g]["raw_p"] for d in per_domain}
        holm = em.holm_adjust(raw_ps) if raw_ps else {}
        any_for = {a: False for a in ALPHA_GRID}
        for domain in DOMAINS:
            reportable_domain = domain in per_domain
            if g == 0.0:
                fpr[(domain, p_trig, null_label)]["reportable"] += int(reportable_domain)
            if is_tpr_family:
                tpr.setdefault((domain, g), _new_counter())
                tpr[(domain, g)]["reportable"] += int(reportable_domain)
            if not reportable_domain:
                continue
            st = per_domain[domain][g]
            for a in ALPHA_GRID:
                label = em.decide_label(st["effect"], st["ci_low"], st["ci_high"],
                                        holm[domain], a, st["effect_h1"], st["effect_h6"])
                is_for = label == "EVIDENCE_FOR"
                if is_for:
                    any_for[a] = True
                    if g == 0.0:
                        fpr[(domain, p_trig, null_label)][f"for_a{a}"] += 1
                    if is_tpr_family:
                        tpr[(domain, g)][f"for_a{a}"] += 1
            verdict_rows.append({
                "null": null_label, "p_trig": p_trig, "edge_bps": g, "draw": draw, "domain": domain,
                "effect_bps": st["effect"], "ci_low_bps": st["ci_low"], "ci_high_bps": st["ci_high"],
                "holm_p": holm[domain], "n_events": st["n_events"],
                "decision_a0.05": em.decide_label(st["effect"], st["ci_low"], st["ci_high"],
                                                  holm[domain], PRIMARY_ALPHA, st["effect_h1"], st["effect_h6"]),
            })
        if g == 0.0:
            familywise[(p_trig, null_label)]["n"] += 1
            for a in ALPHA_GRID:
                familywise[(p_trig, null_label)][f"for_a{a}"] += int(any_for[a])
    if is_tpr_family:
        _record_equity(events_by_domain, reportable_map, equity_rows, equity_curves, draw)


def _record_equity(events_by_domain, reportable_map, equity_rows, equity_curves, draw) -> None:
    """Exposure-matched equity companion (non-gating) for the primary N1/0.06 family."""
    for domain in DOMAINS:
        reportable = reportable_map[domain]
        if len(reportable) < em.DOMAIN_MIN_INSTRUMENTS:
            continue
        events = events_by_domain[domain]
        ev_bps = np.concatenate([events[i].event_primary_bps for i in reportable])
        ctrl_bps = np.concatenate([events[i].control_primary_bps for i in reportable])
        inst_labels = np.concatenate([np.full(events[i].idx.size, i) for i in reportable])
        for g in EDGE_GRID_BPS:
            adv, sortino_diff = em.equity_advantage(ev_bps, ctrl_bps, inst_labels, sorted(reportable), g)
            equity_rows.append({
                "domain": domain, "edge_bps": g, "draw": draw,
                "equity_adv_bps": adv, "sortino_diff": sortino_diff, "advantage_positive": adv > 0,
            })
        if draw == 0 and domain not in equity_curves:
            order = np.argsort(np.concatenate([events[i].idx for i in reportable]))
            equity_curves[domain] = {
                "strategy_null": np.cumsum(ev_bps[order]).tolist(),
                "baseline": np.cumsum(ctrl_bps[order]).tolist(),
                "strategy_edge": np.cumsum((ev_bps + EQUITY_PLOT_EDGE_BPS)[order]).tolist(),
            }


# --------------------------------------------------------------------------- #
# Determinism replay
# --------------------------------------------------------------------------- #
def determinism_replay(cells: dict[tuple[str, str], em.CellPrecompute], instruments: list[str]) -> bool:
    """Re-run REPLAY_DRAWS of the fast 4h N1/0.06 g=0 cell and assert identical stats."""
    domain, null_label, p_trig = "4h", "placebo_on_real", PRIMARY_PTRIG

    def stats() -> list[tuple[float, float, float]]:
        out = []
        for draw in range(REPLAY_DRAWS):
            events = _simulate_domain(cells, instruments, domain, null_label, p_trig, draw)
            reportable = _reportable_instruments(events, instruments)
            if len(reportable) < em.DOMAIN_MIN_INSTRUMENTS:
                out.append((float("nan"), float("nan"), float("nan")))
                continue
            st = _domain_edge_stats(events, reportable, domain, null_label, p_trig, draw, (0.0,))[0.0]
            out.append((st["effect"], st["ci_low"], st["raw_p"]))
        return out

    first, second = stats(), stats()
    return all(
        (np.isnan(a[k]) and np.isnan(b[k])) or a[k] == b[k]
        for a, b in zip(first, second) for k in range(3)
    )


# --------------------------------------------------------------------------- #
# Summaries: FPR / TPR / MDE / equity / verdict
# --------------------------------------------------------------------------- #
def summarize_fpr(fpr, familywise) -> list[dict[str, Any]]:
    """Per-domain and family-wise FPR rows with Wilson intervals."""
    rows: list[dict[str, Any]] = []
    for (domain, p_trig, null_label), c in sorted(fpr.items()):
        n = c["reportable"]
        for a in ALPHA_GRID:
            lo, hi, half = em.wilson_interval(c[f"for_a{a}"], n)
            rows.append({
                "scope": "per_domain", "domain": domain, "p_trig": p_trig, "null": null_label,
                "alpha": a, "n_reportable_draws": n, "n_for": c[f"for_a{a}"],
                "fpr": (c[f"for_a{a}"] / n) if n else None,
                "wilson_low": lo, "wilson_high": hi, "wilson_half_width": half,
                "precision_ok": (half <= FPR_HALFWIDTH_MAX) if n else False,
            })
    for (p_trig, null_label), c in sorted(familywise.items()):
        n = c["n"]
        for a in ALPHA_GRID:
            lo, hi, half = em.wilson_interval(c[f"for_a{a}"], n)
            rows.append({
                "scope": "family_wise", "domain": "ANY", "p_trig": p_trig, "null": null_label,
                "alpha": a, "n_reportable_draws": n, "n_for": c[f"for_a{a}"],
                "fpr": (c[f"for_a{a}"] / n) if n else None,
                "wilson_low": lo, "wilson_high": hi, "wilson_half_width": half,
                "precision_ok": (half <= FPR_HALFWIDTH_MAX) if n else False,
            })
    return rows


def summarize_tpr(tpr) -> list[dict[str, Any]]:
    """Per-domain TPR rows by planted edge with Wilson intervals (primary p_trig=0.06)."""
    rows: list[dict[str, Any]] = []
    for (domain, g), c in sorted(tpr.items()):
        n = c["reportable"]
        for a in ALPHA_GRID:
            lo, hi, half = em.wilson_interval(c[f"for_a{a}"], n)
            rows.append({
                "domain": domain, "edge_bps": g, "alpha": a, "p_trig": PRIMARY_PTRIG,
                "n_reportable_draws": n, "n_for": c[f"for_a{a}"],
                "tpr": (c[f"for_a{a}"] / n) if n else None,
                "wilson_low": lo, "wilson_high": hi, "wilson_half_width": half,
                "precision_ok": (half <= TPR_HALFWIDTH_MAX) if n else False,
            })
    return rows


def compute_mde(tpr_rows, fpr_rows) -> list[dict[str, Any]]:
    """Event-level MDE per domain/alpha: smallest edge with TPR>=0.80 at FPR<=0.05.

    Non-finite (no recovery) when no grid edge qualifies — reported as ``null``,
    never 0. FPR condition uses the matched N1/0.06 per-domain cell at alpha0=0.05.
    """
    fpr_at = {
        (r["domain"], r["alpha"]): r["fpr"]
        for r in fpr_rows
        if r["scope"] == "per_domain" and r["null"] == "placebo_on_real" and r["p_trig"] == PRIMARY_PTRIG
    }
    rows: list[dict[str, Any]] = []
    for domain in DOMAINS:
        for a in ALPHA_GRID:
            fpr_val = fpr_at.get((domain, PRIMARY_ALPHA))
            fpr_ok = fpr_val is not None and fpr_val <= PRIMARY_ALPHA
            mde = None
            if fpr_ok:
                for g in sorted(e for e in EDGE_GRID_BPS if e > 0):
                    hit = next((r for r in tpr_rows if r["domain"] == domain and r["edge_bps"] == g
                                and r["alpha"] == a), None)
                    if hit and hit["precision_ok"] and hit["tpr"] is not None and hit["tpr"] >= TPR_TARGET:
                        mde = g
                        break
            rows.append({
                "domain": domain, "alpha": a, "fpr_at_0.06": fpr_val, "fpr_controlled": fpr_ok,
                "event_level_mde_bps": mde, "recovered": mde is not None,
            })
    return rows


def summarize_equity(equity_rows) -> list[dict[str, Any]]:
    """Companion summary: null false-advantage rate + planted-edge sensitivity by domain/edge."""
    rows: list[dict[str, Any]] = []
    keys = sorted({(r["domain"], r["edge_bps"]) for r in equity_rows})
    for domain, g in keys:
        sub = [r for r in equity_rows if r["domain"] == domain and r["edge_bps"] == g]
        n = len(sub)
        adv = np.array([r["equity_adv_bps"] for r in sub], dtype=float)
        sortino = np.array([r["sortino_diff"] for r in sub], dtype=float)
        pos_rate = float(np.mean([r["advantage_positive"] for r in sub])) if n else None
        rows.append({
            "domain": domain, "edge_bps": g, "n_draws": n,
            "mean_equity_adv_bps": float(np.nanmean(adv)) if n else None,
            "mean_sortino_diff": float(np.nanmean(sortino)) if n else None,
            "advantage_positive_rate": pos_rate,
            "is_null_cell": g == 0.0,
        })
    return rows


def classify_method(fpr_rows, mde_rows, equity_rows, determinism_pass: bool) -> dict[str, Any]:
    """METHOD_VALID / METHOD_INVALID / INCONCLUSIVE per analysis-plan Step 7."""
    primary_fpr = [
        r for r in fpr_rows if r["scope"] == "per_domain" and r["p_trig"] == PRIMARY_PTRIG
        and r["alpha"] == PRIMARY_ALPHA and r["precision_ok"]
    ]
    fpr_controlled = all(r["fpr"] is not None and r["fpr"] <= PRIMARY_ALPHA for r in primary_fpr) and \
        len(primary_fpr) > 0
    mde_primary = [r for r in mde_rows if r["alpha"] == PRIMARY_ALPHA]
    recovered_domains = [r["domain"] for r in mde_primary if r["recovered"]]
    all_recovered = len(recovered_domains) == len(DOMAINS)
    any_recovered = len(recovered_domains) > 0
    # FPR not materially above alpha0 across the bracket (powered cells only)
    bracket = [r for r in fpr_rows if r["scope"] == "per_domain" and r["alpha"] == PRIMARY_ALPHA
               and r["precision_ok"]]
    bracket_ok = all(r["fpr"] is not None and r["fpr"] <= PRIMARY_ALPHA + FPR_HALFWIDTH_MAX for r in bracket)
    null_false_adv = [r["advantage_positive_rate"] for r in equity_rows
                      if r["edge_bps"] == 0.0 and r["advantage_positive_rate"] is not None]
    companion_sane = all(rate <= 0.5 + 0.1 for rate in null_false_adv) if null_false_adv else True

    if fpr_controlled and all_recovered and bracket_ok and determinism_pass:
        verdict = "METHOD_VALID"
    elif (not bracket_ok) or (not any_recovered):
        verdict = "METHOD_INVALID"
    else:
        verdict = "INCONCLUSIVE"
    return {
        "verdict": verdict, "fpr_controlled_primary": fpr_controlled, "bracket_fpr_ok": bracket_ok,
        "recovered_domains": recovered_domains, "all_domains_recovered": all_recovered,
        "determinism_pass": determinism_pass, "companion_null_sane": companion_sane,
    }


# --------------------------------------------------------------------------- #
# Plotting (bounded inputs only)
# --------------------------------------------------------------------------- #
def plot_fpr_by_activity(fpr_rows: list[dict[str, Any]], save_path: Path) -> None:
    """FPR vs activity by domain, one line per null generator (alpha0=0.05)."""
    fig, axes = plt.subplots(1, len(DOMAINS), figsize=(4 * len(DOMAINS), 4), squeeze=False)
    for j, domain in enumerate(DOMAINS):
        ax = axes[0][j]
        for null_label in NULL_GENERATORS:
            sub = sorted(
                [r for r in fpr_rows if r["scope"] == "per_domain" and r["domain"] == domain
                 and r["null"] == null_label and r["alpha"] == PRIMARY_ALPHA],
                key=lambda r: r["p_trig"],
            )
            xs = [r["p_trig"] for r in sub]
            ys = [r["fpr"] for r in sub]
            err = [r["wilson_half_width"] for r in sub]
            ax.errorbar(xs, ys, yerr=err, fmt="o-", capsize=3, label=null_label)
        ax.axhline(PRIMARY_ALPHA, ls="--", lw=0.8, color="grey", label="alpha0=0.05")
        ax.set_title(domain)
        ax.set_xlabel("placebo trigger prevalence")
        if j == 0:
            ax.set_ylabel("FPR (Evidence-FOR rate)")
            ax.legend(fontsize=8)
    fig.suptitle("EXP-027 gate FPR vs activity (Wilson 95%)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_recovery(tpr_rows: list[dict[str, Any]], mde_rows: list[dict[str, Any]], save_path: Path) -> None:
    """TPR vs planted edge by domain at p_trig=0.06, with the 0.80 line and MDE marker."""
    fig, axes = plt.subplots(1, len(DOMAINS), figsize=(4 * len(DOMAINS), 4), squeeze=False)
    for j, domain in enumerate(DOMAINS):
        ax = axes[0][j]
        sub = sorted([r for r in tpr_rows if r["domain"] == domain and r["alpha"] == PRIMARY_ALPHA],
                     key=lambda r: r["edge_bps"])
        xs = [r["edge_bps"] for r in sub]
        ys = [r["tpr"] for r in sub]
        err = [r["wilson_half_width"] for r in sub]
        ax.errorbar(xs, ys, yerr=err, fmt="o-", capsize=3, color="#1f77b4")
        ax.axhline(TPR_TARGET, ls="--", lw=0.8, color="grey")
        mde = next((r["event_level_mde_bps"] for r in mde_rows
                    if r["domain"] == domain and r["alpha"] == PRIMARY_ALPHA), None)
        if mde is not None:
            ax.axvline(mde, ls=":", lw=1.0, color="#d62728", label=f"MDE={mde:g} bps")
            ax.legend(fontsize=8)
        ax.set_title(domain)
        ax.set_xlabel("planted per-event edge (bps)")
        if j == 0:
            ax.set_ylabel("TPR (Evidence-FOR rate)")
    fig.suptitle("EXP-027 recovery curves at p_trig=0.06 (Wilson 95%)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_precision(fpr_rows, tpr_rows, save_path: Path) -> None:
    """Calibration-precision diagnostic: Wilson half-widths across FPR and TPR cells."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    fpr_sub = [r for r in fpr_rows if r["scope"] == "per_domain" and r["alpha"] == PRIMARY_ALPHA]
    labels = [f"{r['domain']}/{r['null'][:3]}/{r['p_trig']}" for r in fpr_sub]
    axes[0].bar(range(len(fpr_sub)), [r["wilson_half_width"] or 0 for r in fpr_sub], color="#2ca02c")
    axes[0].axhline(FPR_HALFWIDTH_MAX, ls="--", lw=0.8, color="grey")
    axes[0].set_xticks(range(len(fpr_sub)))
    axes[0].set_xticklabels(labels, rotation=90, fontsize=6)
    axes[0].set_title("FPR cell half-widths (<=0.03)")
    tpr_sub = [r for r in tpr_rows if r["alpha"] == PRIMARY_ALPHA]
    axes[1].scatter([r["edge_bps"] for r in tpr_sub], [r["wilson_half_width"] or 0 for r in tpr_sub],
                    c=["#1f77b4" if r["domain"] == "5m" else "#ff7f0e" if r["domain"] == "1h" else "#9467bd"
                       for r in tpr_sub], s=20)
    axes[1].axhline(TPR_HALFWIDTH_MAX, ls="--", lw=0.8, color="grey")
    axes[1].set_xlabel("planted edge (bps)")
    axes[1].set_title("TPR cell half-widths (<=0.05)")
    fig.suptitle("EXP-027 calibration precision")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_equity(equity_curves: dict[str, Any], save_path: Path) -> None:
    """Representative exposure-matched equity curves (strategy vs baseline; buy-hold context)."""
    panels = list(equity_curves.keys()) or list(DOMAINS)
    fig, axes = plt.subplots(1, len(panels), figsize=(4 * len(panels), 4), squeeze=False)
    for j, domain in enumerate(panels):
        ax = axes[0][j]
        cur = equity_curves.get(domain)
        if cur:
            ax.plot(cur["strategy_null"], label="strategy (null)", color="#1f77b4")
            ax.plot(cur["baseline"], label="exposure-matched baseline", color="#2ca02c")
            ax.plot(cur["strategy_edge"], label=f"strategy (+{EQUITY_PLOT_EDGE_BPS:g} bps)", color="#d62728")
            ax.axhline(0.0, ls="--", lw=0.8, color="grey")
        else:
            ax.text(0.5, 0.5, "not reportable", ha="center", va="center", transform=ax.transAxes)
        ax.set_title(f"{domain} (buy-hold = 100%-exposed context, not comparator)", fontsize=7)
        ax.set_xlabel("trade # (time order)")
        if j == 0:
            ax.set_ylabel("cumulative log return (bps)")
            ax.legend(fontsize=7)
    fig.suptitle("EXP-027 exposure-matched equity companion (non-gating)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_verdict_summary(fpr_rows, mde_rows, verdict: dict[str, Any], save_path: Path) -> None:
    """Per-domain primary FPR (both nulls) + event-level MDE with the method verdict."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(DOMAINS))
    width = 0.35
    for k, null_label in enumerate(NULL_GENERATORS):
        vals = []
        for domain in DOMAINS:
            r = next((rr for rr in fpr_rows if rr["scope"] == "per_domain" and rr["domain"] == domain
                      and rr["null"] == null_label and rr["p_trig"] == PRIMARY_PTRIG
                      and rr["alpha"] == PRIMARY_ALPHA), None)
            vals.append(r["fpr"] if r and r["fpr"] is not None else 0.0)
        ax.bar(x + (k - 0.5) * width, vals, width, label=f"FPR {null_label}")
    ax.axhline(PRIMARY_ALPHA, ls="--", lw=0.8, color="grey", label="alpha0=0.05")
    for j, domain in enumerate(DOMAINS):
        mde = next((r["event_level_mde_bps"] for r in mde_rows
                    if r["domain"] == domain and r["alpha"] == PRIMARY_ALPHA), None)
        ax.text(j, max(0.06, ax.get_ylim()[1] * 0.9),
                f"MDE={'∞' if mde is None else f'{mde:g}'}", ha="center", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(DOMAINS)
    ax.set_ylabel("FPR at p_trig=0.06")
    ax.set_title(f"EXP-027 method verdict: {verdict['verdict']}")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def write_blocked_metadata(reasons: list[str]) -> None:
    """Persist a blocked outcome when the EXP-020 dependency gate fails."""
    write_json(RESULTS_DIR / "run_metadata.json", {
        "experiment_id": EXPERIMENT_ID,
        "title": "Event-Level Evaluation Method: Definition and Sparse-Regime Calibration",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": "BLOCKED",
        "dependency_gate": {"passed": False, "reasons": reasons},
        "registry": REGISTRY_REFS,
    })
    LOGGER.info("EXP-027 BLOCKED — EXP-020 dependency gate failed: %s", "; ".join(reasons))


def run() -> None:
    """Execute EXP-027 end to end and write all result artifacts."""
    ensure_output_dirs()
    equivalence_pass = em.verify_control_matching()   # fail-fast linchpin guard, before any draw
    LOGGER.info("control-matching equivalence check PASSED (vectorized == EXP-021 reference).")
    gate_ok, reasons, dep_meta = check_dependency_gate()
    if not gate_ok:
        write_blocked_metadata(reasons)
        return
    LOGGER.info("EXP-020 dependency gate PASSED (%s); reading regime scaffolding only.",
                dep_meta.get("overall_status"))

    regimes = load_regime_summary()
    cells, analysis_end = build_precomputes(regimes)
    instruments = sorted({i for (i, _d) in cells} & set(regimes.get_column("instrument").unique().to_list()))
    LOGGER.info("instruments: %s | domains: %s", instruments, list(DOMAINS))

    acc = run_calibration(cells, instruments)
    LOGGER.info("determinism replay ...")
    determinism_pass = determinism_replay(cells, instruments)

    fpr_rows = summarize_fpr(acc["fpr"], acc["familywise"])
    tpr_rows = summarize_tpr(acc["tpr"])
    mde_rows = compute_mde(tpr_rows, fpr_rows)
    equity_summary_rows = summarize_equity(acc["equity_rows"])
    verdict = classify_method(fpr_rows, mde_rows, equity_summary_rows, determinism_pass)

    _write_all_outputs(acc, fpr_rows, tpr_rows, mde_rows, equity_summary_rows,
                       verdict, instruments, analysis_end, dep_meta, equivalence_pass)
    LOGGER.info("EXP-027 verdict: %s | recovered domains: %s | determinism: %s",
                verdict["verdict"], verdict["recovered_domains"], determinism_pass)


def _write_all_outputs(acc, fpr_rows, tpr_rows, mde_rows, equity_summary_rows,
                       verdict, instruments, analysis_end, dep_meta, equivalence_pass) -> None:
    """Write every result table, plot, and the run metadata."""
    write_rows(RESULTS_DIR / "draw_verdicts.csv", acc["verdict_rows"])
    write_rows(RESULTS_DIR / "fpr_summary.csv", fpr_rows)
    write_rows(RESULTS_DIR / "tpr_summary.csv", tpr_rows)
    write_rows(RESULTS_DIR / "mde_summary.csv", mde_rows)
    write_rows(RESULTS_DIR / "equity_companion_summary.csv", equity_summary_rows)

    plot_fpr_by_activity(fpr_rows, PLOTS_DIR / "fpr_by_activity.png")
    plot_recovery(tpr_rows, mde_rows, PLOTS_DIR / "recovery_mde_curves.png")
    plot_precision(fpr_rows, tpr_rows, PLOTS_DIR / "calibration_precision.png")
    plot_equity(acc["equity_curves"], PLOTS_DIR / "equity_companion.png")
    plot_verdict_summary(fpr_rows, mde_rows, verdict, PLOTS_DIR / "method_verdict_summary.png")

    write_json(RESULTS_DIR / "run_metadata.json", {
        "experiment_id": EXPERIMENT_ID,
        "title": "Event-Level Evaluation Method: Definition and Sparse-Regime Calibration",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": verdict["verdict"],
        "method_verdict": verdict,
        "control_matching_equivalence_pass": equivalence_pass,
        "dependency_gate": {"passed": True, "exp020_status": dep_meta.get("overall_status"),
                            "anti_overfitting_fence": "avwap_events.csv outcomes not read"},
        "instruments": instruments,
        "domains": list(DOMAINS),
        "analysis_end_by_instrument": analysis_end,
        "parameters": {
            "p_trig_grid": list(P_TRIG_GRID), "primary_p_trig": PRIMARY_PTRIG,
            "edge_grid_bps": list(EDGE_GRID_BPS), "alpha_grid": list(ALPHA_GRID),
            "primary_alpha": PRIMARY_ALPHA, "null_generators": list(NULL_GENERATORS),
            "n_draws": N_DRAWS, "n_bootstrap": N_BOOT, "n_permutation": N_PERM,
            "horizons": list(em.HORIZONS), "primary_horizon": em.PRIMARY_HORIZON,
            "max_controls": em.MAX_CONTROLS, "min_controls": em.MIN_CONTROLS,
            "exclusion_bars": em.EXCLUSION_BARS, "pyramid_frac": PYRAMID_FRAC,
            "pyramid_span": PYRAMID_SPAN, "tpr_target": TPR_TARGET,
            "fpr_halfwidth_max": FPR_HALFWIDTH_MAX, "tpr_halfwidth_max": TPR_HALFWIDTH_MAX,
            "domain_estimator": "instrument_averaged_equal_weight",
            "control_scope": "same_regime_only", "unit_of_analysis": "per_event",
        },
        "registry": REGISTRY_REFS,
    })


def main() -> None:
    """Configure logging and run the experiment (manual execution entry point)."""
    configure_logging()
    run()


if __name__ == "__main__":
    main()
