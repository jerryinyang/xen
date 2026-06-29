"""
Experiment EXP-005 (E5): DET-adjudicate the Q4 composite form, then FREEZE the renewed referee.

Implements python/experiments/EXP-005/design.md (GATE APPROVE). Analysis-only. At the SINGLE
E4-validated operating point (q*=0.75, N_BOOTSTRAP=500, seed_off=0, standard nulls), runs a 3-FORM
DET comparison on the E2/E3a substrate and adjudicates which composite form to FREEZE:

  frozen        : gate_stack_core_costfn(strategy_return_bps) + gate_stack_row  (per-held DET reference
                  + regression anchor target — reproduces EXP-003/EXP-004)
  adaptive_103a : gate_stack_adaptive + adaptive_row                            (§10.3a validity->economics
                  — L1 admissibility ∧ power-aware L3 ∧ studentized-subpop L5; the FREEZE candidate)
  variant_c     : gate_stack_adaptive + adaptive_row_variant_c                  (single-statistic form —
                  L1 admissibility ∧ vs-naive incremental-net CI-lower>0; L5/sub-pop demoted to
                  diagnostics; the REJECTED-alternative candidate)

Binding (per stratum, L-03): the §10.3a-vs-variant-c adjudication.
  10.3a_MATCHES_OR_BEATS : MDE_103a <= MDE_vc on EVERY shape AND 103a FPR-acceptable wherever vc is
                           -> FREEZE §10.3a; record variant-c as the rejected alternative.
  VARIANT_C_DOMINATES    : MDE_vc <= MDE_103a every shape, strictly < on >=1 shape, vc FPR-acceptable,
                           103a not better elsewhere -> FREEZE variant-c instead.
  MIXED                  : neither -> freeze the predeclared primary §10.3a (D0 Q4), trade recorded.

E4-derived less-brittle freeze-adjudication FPR rule (candidate-blind; in this harness's classify ONLY,
the gate `adaptive_row` is byte-unchanged): a form's dogfood-FPR is FPR-ACCEPTABLE iff
`passes < MIN_FPR_PASSES` OR `wilson_lower(passes,draws) <= FPR_CONTROL_BOUND` with MIN_FPR_PASSES=2 and
FPR_CONTROL_BOUND=2*ALPHA. Retires the single-1/162 labeling artifact E4 flagged.

Leak tripwires retained from E3a/E4, applied to BOTH adaptive forms: future-destroy collapse,
no-plant guard, dogfood-FPR control. A future-destroyed pass surviving in either form is REJECT-class.

On a clean, anchor-reproducing, leak-clean adjudication the harness FREEZES + hash-pins the renewed
referee (results/freeze_manifest.json: form, all frozen constants, sha256(referee_adaptive.py), git
commit, rejected alternative). Not tuned on CF-MR-002 (absent). Global holdout sealed.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from statistics import NormalDist

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
import seaborn as sns
from tqdm.auto import tqdm

import xen.referee_adaptive as ra
from xen.bar_aggregator import aggregate_ohlc
from xen.referee_adaptive import (
    ADAPTIVE_DOMAINS,
    MIN_EPISODES_SUBPOP,
    ROUND_TRIP_COST_BPS_17,
    SUBPOP_QUANTILE,
    adaptive_cost_bps_for,
    adaptive_row,
    adaptive_row_variant_c,
    gate_stack_adaptive,
    gate_stack_core_costfn,
    next_open_to_open_returns_from_bars,
)
from xen.referee_calibration import (
    EDGE_GRID_BPS,
    donchian_breakout_positions,
    gate_stack_row,
    ma_crossover_positions,
    materiality_bps_for,
    permuted_returns,
    random_state_positions,
    strategy_return_bps,
    wilson_interval,
)
from xen.referee_substrate import (
    dense_planted,
    persistent_positions,
    sparse_positions,
    state_dependent_planted,
    state_positions,
    tail_only_planted,
)
from xen.incremental_referee import EPISODE_LENGTHS

logger = logging.getLogger("EXP-005")

# --------------------------------------------------------------------------- #
# Constants (substrate / draw budget reused from EXP-003/EXP-004 — anchor-identical)
# --------------------------------------------------------------------------- #
DATA_DIR = Path("data")
EXP_DIR = Path("python/experiments/EXP-005")
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"
EXP003_STRATUM_CSV = Path("python/experiments/EXP-003/results/det_dominance_per_stratum.csv")
REFEREE_ADAPTIVE_SRC = Path("python/src/xen/referee_adaptive.py")

ANALYSIS_FRACTION = 0.70
ERA_GLOB = "20210602_*"
PERIOD_MINUTES = {"1h": 60, "4h": 240}
DOMAIN_MIN_COVERAGE = 0.90

ALPHA = 0.05
N_NULL = 80
N_PLANT = 20
POWER_TARGET = 0.50
N_BOOTSTRAP = 500
SEED_OFF = 0

# The single E4-validated operating point — E5 is the FREEZE, not a sweep.
Q_STAR = 0.75

SHAPES: tuple[str, ...] = ("dense", "tail", "sparse", "state")
FORMS: tuple[str, ...] = ("frozen", "adaptive_103a", "variant_c")
ADAPTIVE_FORMS: tuple[str, ...] = ("adaptive_103a", "variant_c")

# E4-derived less-brittle freeze-adjudication FPR rule (candidate-blind; classify-only).
FPR_CONTROL_BOUND = 2 * ALPHA      # 0.10 — the pre-existing control budget (compare to this, not 0)
MIN_FPR_PASSES = 2                 # retire the single-1/162 labeling artifact (>= 2 passes to "break")

N_WORKERS = min(os.cpu_count() or 1, 16)


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Job:
    """One instrument's analysis-set file path."""
    instrument: str
    path: str


# --------------------------------------------------------------------------- #
# I/O helpers
# --------------------------------------------------------------------------- #
def era_file_for(instrument: str) -> Path | None:
    """Newest 5-year-era 1-minute file for an instrument, or None if absent."""
    matches = sorted(DATA_DIR.glob(f"timebars/timebars_{instrument.lower()}_{ERA_GLOB}.parquet"))
    return matches[-1] if matches else None


def load_analysis_minutes(path: Path) -> pl.DataFrame:
    """First-70% (CloseTime-ordered) 1-minute slice. Global holdout never collected."""
    scan = pl.scan_parquet(path).sort("CloseTime")
    total = int(scan.select(pl.len()).collect().item())
    return scan.slice(0, int(total * ANALYSIS_FRACTION)).collect()


def build_domain(minutes: pl.DataFrame, domain: str) -> tuple[np.ndarray, pl.DataFrame]:
    """Open-to-open <=t-1 returns + aligned fenced domain frame (for the dogfood OHLC signals)."""
    dom = aggregate_ohlc(minutes, period_minutes=PERIOD_MINUTES[domain],
                         min_coverage=DOMAIN_MIN_COVERAGE)
    dom = dom.filter(pl.col("CloseTime") <= minutes.get_column("CloseTime").max())
    return next_open_to_open_returns_from_bars(dom)


# --------------------------------------------------------------------------- #
# Pure helpers — substrate, nulls, gate forms (mirror EXP-003/EXP-004)
# --------------------------------------------------------------------------- #
def reblocked_random_positions(n: int, episode_length: int, seed: int) -> np.ndarray:
    """random_state_positions re-blocked to length L (mirrors EXP-003/EXP-004)."""
    n_episodes = (n + episode_length - 1) // episode_length
    return np.repeat(random_state_positions(n_episodes, seed), episode_length)[:n]


def lag_open_to_open(positions: np.ndarray) -> np.ndarray:
    """Lag a close-indexed signal one bar so it acts at the next bar's open on confirmed bars <=t-1."""
    pos = np.asarray(positions, dtype=float)
    return np.concatenate(([0.0], pos[:-1]))


def make_shape(shape: str, returns: np.ndarray, *, net_edge_bps: float, cost_bps: float,
               episode_length: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """(planted_returns, positions) for one shape draw (matched-magnitude; mirrors EXP-003/EXP-004)."""
    n = len(returns)
    if shape == "dense":
        pos = persistent_positions(n, episode_length, seed)
        return dense_planted(returns, pos, net_edge_bps=net_edge_bps, cost_bps=cost_bps), pos
    if shape == "tail":
        pos = persistent_positions(n, episode_length, seed)
        return tail_only_planted(returns, pos, net_edge_bps=net_edge_bps, cost_bps=cost_bps,
                                 seed=seed + 50_000), pos
    if shape == "sparse":
        pos = sparse_positions(n, episode_length, seed)
        return dense_planted(returns, pos, net_edge_bps=net_edge_bps, cost_bps=cost_bps), pos
    if shape == "state":
        pos, mask = state_positions(n, episode_length, seed)
        return state_dependent_planted(returns, pos, mask, net_edge_bps=net_edge_bps,
                                       cost_bps=cost_bps), pos
    raise ValueError(f"unknown shape: {shape}")


def gate_passes(form: str, returns: np.ndarray, positions: np.ndarray, *, domain: str,
                cost_bps: float, seed: int) -> bool:
    """True iff the named gate FORM PASSES for one draw (q*=0.75, N_BOOTSTRAP fixed).

    `adaptive_103a`/`variant_c` share the SAME `gate_stack_adaptive` core (identical draws/seeds);
    only the verdict assembly (`adaptive_row` vs `adaptive_row_variant_c`) differs. `frozen` is the
    per-held DET reference. The coupled `Q_STUD_MIN=Phi^-1(q*)` is set on `referee_adaptive` per
    worker (the default already equals it at q*=0.75).
    """
    if form in ADAPTIVE_FORMS:
        core = gate_stack_adaptive(returns, positions, domain=domain, cost_bps=cost_bps,
                                   n_bootstrap=N_BOOTSTRAP, seed=seed, q=Q_STAR)
        row_fn = adaptive_row if form == "adaptive_103a" else adaptive_row_variant_c
        return bool(row_fn(core, alpha=ALPHA)["passed"])
    core = gate_stack_core_costfn(returns, positions, domain=domain, cost_bps=cost_bps,
                                  n_bootstrap=N_BOOTSTRAP, seed=seed, strategy_fn=strategy_return_bps)
    return bool(gate_stack_row(core, alpha=ALPHA)["passed"])


def detection_rate(form: str, shape: str, returns: np.ndarray, *, domain: str, episode_length: int,
                   cost_bps: float, net_edge_bps: float) -> float:
    """Fraction of planted draws the form PASSES (early-stop at the POWER_TARGET binomial boundary).

    Denominator stays N_PLANT so the rate lands on the same side of POWER_TARGET as a full run
    (the MDE decision is bit-identical; mirrors EXP-003/EXP-004).
    """
    need = math.ceil(POWER_TARGET * N_PLANT)
    passes = 0
    for k in range(N_PLANT):
        planted, pos = make_shape(shape, returns, net_edge_bps=net_edge_bps, cost_bps=cost_bps,
                                  episode_length=episode_length, seed=6000 + k + SEED_OFF)
        passes += gate_passes(form, planted, pos, domain=domain, cost_bps=cost_bps,
                              seed=7000 + k + SEED_OFF)
        remaining = N_PLANT - (k + 1)
        if passes >= need or passes + remaining < need:
            break
    return passes / N_PLANT


def mde_of(form: str, shape: str, returns: np.ndarray, *, domain: str, episode_length: int,
           cost_bps: float) -> float:
    """DETECTED_FLOOR MDE for a form x shape (inf = UNPOWERED)."""
    for edge in EDGE_GRID_BPS:
        if edge <= 0.0:
            continue
        if detection_rate(form, shape, returns, domain=domain, episode_length=episode_length,
                          cost_bps=cost_bps, net_edge_bps=edge) >= POWER_TARGET:
            return edge
    return math.inf


def no_plant_passrate(form: str, shape: str, returns: np.ndarray, *, domain: str,
                      episode_length: int, cost_bps: float) -> float:
    """No-real-edge guard: form PASS rate on the shape's positions with NO planted drift."""
    passes = 0
    for k in range(N_PLANT):
        _, pos = make_shape(shape, returns, net_edge_bps=0.0, cost_bps=cost_bps,
                            episode_length=episode_length, seed=6000 + k + SEED_OFF)
        passes += gate_passes(form, returns, pos, domain=domain, cost_bps=cost_bps,
                              seed=7000 + k + SEED_OFF)
    return passes / N_PLANT


def future_destroyed_passrate(form: str, shape: str, returns: np.ndarray, *, domain: str,
                              episode_length: int, cost_bps: float, net_edge_bps: float) -> float:
    """Leak control: plant edge, permute returns (destroy alignment) -> must collapse to FPR."""
    passes = 0
    for k in range(N_PLANT):
        planted, pos = make_shape(shape, returns, net_edge_bps=net_edge_bps, cost_bps=cost_bps,
                                  episode_length=episode_length, seed=6000 + k + SEED_OFF)
        destroyed = permuted_returns(planted, seed=8000 + k + SEED_OFF)
        passes += gate_passes(form, destroyed, pos, domain=domain, cost_bps=cost_bps,
                              seed=7000 + k + SEED_OFF)
    return passes / N_PLANT


def dogfood_fpr(form: str, returns: np.ndarray, aligned: pl.DataFrame, *, domain: str,
                episode_length: int, cost_bps: float) -> tuple[float, float, int, int]:
    """Per-stratum FPR for a form over 3 null families (abstract x2 + real dogfood Donchian/MA).

    Mirrors EXP-003/EXP-004 `dogfood_fpr` at standard nulls / seed_off=0 (the regression anchor).
    Returns (rate, wilson_halfwidth, draws, passes) — `passes`/`draws` feed the E5 FPR rule.
    """
    n = len(returns)
    passes, draws = 0, 0
    for k in range(N_NULL):
        pr = permuted_returns(returns, seed=1000 + k + SEED_OFF)
        passes += gate_passes(form, pr, persistent_positions(n, episode_length, 2000 + k + SEED_OFF),
                              domain=domain, cost_bps=cost_bps, seed=3000 + k + SEED_OFF)
        passes += gate_passes(form, returns,
                              reblocked_random_positions(n, episode_length, 4000 + k + SEED_OFF),
                              domain=domain, cost_bps=cost_bps, seed=5000 + k + SEED_OFF)
        draws += 2
    high = aligned.get_column("High").to_numpy()
    low = aligned.get_column("Low").to_numpy()
    close = aligned.get_column("Close").to_numpy()
    don = lag_open_to_open(donchian_breakout_positions(high, low, close, lookback=20))
    ma = lag_open_to_open(ma_crossover_positions(close, fast=20, slow=50))
    for sig, sd in ((don, 9001 + SEED_OFF), (ma, 9002 + SEED_OFF)):
        passes += gate_passes(form, returns, sig, domain=domain, cost_bps=cost_bps, seed=sd)
        draws += 1
    _, lo, hi = wilson_interval(passes, draws)
    return passes / draws, (hi - lo) / 2.0, draws, passes


# --------------------------------------------------------------------------- #
# Pure comparison helpers (inf-aware MDE ordering; the E5 FPR rule)
# --------------------------------------------------------------------------- #
def mde_le(a: float, b: float) -> bool:
    """`a <= b` for MDEs with inf=UNPOWERED (inf<=inf True; finite<=inf True; inf<=finite False)."""
    if math.isinf(a):
        return math.isinf(b)
    return math.isinf(b) or a <= b


def mde_lt(a: float, b: float) -> bool:
    """`a < b` for MDEs with inf=UNPOWERED (finite<inf True; inf<anything False)."""
    if math.isinf(a):
        return False
    return math.isinf(b) or a < b


def fpr_acceptable(passes: int, draws: int) -> bool:
    """E5 less-brittle rule: ACCEPTABLE iff < MIN_FPR_PASSES OR wilson_lower <= FPR_CONTROL_BOUND."""
    if passes < MIN_FPR_PASSES:
        return True
    _, lo, _ = wilson_interval(passes, draws)
    return lo <= FPR_CONTROL_BOUND


# --------------------------------------------------------------------------- #
# Per-stratum orchestration
# --------------------------------------------------------------------------- #
def verdict_vs_frozen(mde: dict, form: str, frozen_acc: bool, form_acc: bool) -> str:
    """DET verdict of an adaptive form vs frozen (E3a-style, E5 FPR rule). For the anchor + disclosure."""
    if frozen_acc and not form_acc:
        return "FPR_BROKEN"
    no_regression = all(mde_le(mde[(form, s)], mde[("frozen", s)]) for s in SHAPES)
    strict = any(mde_lt(mde[(form, s)], mde[("frozen", s)]) for s in SHAPES)
    return "DET_DOMINANT" if (no_regression and strict) else "NOT_IMPROVED"


def adjudicate(mde: dict, eligible: dict) -> str:
    """Binding §10.3a-vs-variant-c adjudication for one stratum (L-03).

    DET-dominance is "lower MDE at **equal-or-better FPR**": a form that is **not leak-clean**
    (DET-INELIGIBLE — FPR-unacceptable, survives future-destroy, or no-plant breach) is **off the DET
    curve**, so its leak-inflated MDE cannot win — the other form matches-or-beats it by default. MDEs
    are compared only when **both** forms are DET-eligible.
    """
    a, c = "adaptive_103a", "variant_c"
    if eligible[a] and not eligible[c]:
        return "10.3a_MATCHES_OR_BEATS"          # variant-c off the curve (DET-ineligible)
    if eligible[c] and not eligible[a]:
        return "VARIANT_C_DOMINATES"             # §10.3a off the curve (not expected — it is clean)
    if not eligible[a] and not eligible[c]:
        return "MIXED"                            # both off the curve
    a_le_c = all(mde_le(mde[(a, s)], mde[(c, s)]) for s in SHAPES)
    c_le_a = all(mde_le(mde[(c, s)], mde[(a, s)]) for s in SHAPES)
    c_strict = any(mde_lt(mde[(c, s)], mde[(a, s)]) for s in SHAPES)
    a_strict = any(mde_lt(mde[(a, s)], mde[(c, s)]) for s in SHAPES)
    if c_le_a and c_strict and not a_strict:
        return "VARIANT_C_DOMINATES"
    if a_le_c:
        return "10.3a_MATCHES_OR_BEATS"
    return "MIXED"


def run_stratum(returns: np.ndarray, aligned: pl.DataFrame, instrument: str, domain: str) -> dict:
    """Per stratum: MDE x shape x form, dogfood FPR, adjudication, anchor disclosure, tripwires."""
    L = EPISODE_LENGTHS[domain]
    cost = adaptive_cost_bps_for(instrument, domain)
    kw = dict(domain=domain, episode_length=L, cost_bps=cost)
    failures: list[str] = []

    dogfood = {f: dogfood_fpr(f, returns, aligned, **kw) for f in FORMS}
    acc = {f: fpr_acceptable(dogfood[f][3], dogfood[f][2]) for f in FORMS}

    mde: dict = {}
    for shape in SHAPES:
        for form in FORMS:
            mde[(form, shape)] = mde_of(form, shape, returns, **kw)

    # Leak tripwires on BOTH adaptive forms (no-plant + future-destroy), tracked PER FORM so the
    # freeze gate can distinguish a §10.3a leak (REJECT-class blocker) from variant-c's leak (its
    # expected, informative refutation).
    fd_max = {f: 0.0 for f in ADAPTIVE_FORMS}
    form_failures: dict[str, list[str]] = {f: [] for f in ADAPTIVE_FORMS}
    for form in ADAPTIVE_FORMS:
        guard = max(dogfood[form][0] + 2 * dogfood[form][1], FPR_CONTROL_BOUND)
        for shape in SHAPES:
            npr = no_plant_passrate(form, shape, returns, **kw)
            if npr > guard:
                form_failures[form].append(f"{instrument}/{domain}/{shape}: no-plant({form}) {npr:.3f} > guard")
            levels = sorted({lvl for lvl in (mde[(form, shape)], EDGE_GRID_BPS[-1]) if math.isfinite(lvl)})
            for lvl in levels:
                rate = future_destroyed_passrate(form, shape, returns, net_edge_bps=lvl, **kw)
                fd_max[form] = max(fd_max[form], rate)
                if rate > guard:
                    form_failures[form].append(f"{instrument}/{domain}/{shape}: {form} SURVIVED "
                                               f"future-destroy (e={lvl}) pass={rate:.3f} -> LEAK")
        if dogfood[form][0] - dogfood[form][1] > FPR_CONTROL_BOUND:
            form_failures[form].append(f"{instrument}/{domain}: dogfood FPR({form}) "
                                       f"{dogfood[form][0]:.3f} > control")

    # Leak-clean (DET-eligible) per form: FPR-acceptable AND no future-destroy/no-plant breach.
    leak_clean = {f: bool(acc[f] and not form_failures[f]) for f in ADAPTIVE_FORMS}
    failures = [m for f in ADAPTIVE_FORMS for m in form_failures[f]]

    def state_delta(ref: str, form: str) -> float:
        f, a = mde[(ref, "state")], mde[(form, "state")]
        return (f - a) if math.isfinite(f) and math.isfinite(a) else math.nan

    summary = {
        "instrument": instrument, "domain": domain, "cost_bps": cost,
        "adjudication": adjudicate(mde, leak_clean),
        # §10.3a-vs-frozen disclosure (= the EXP-003/EXP-004 regression-anchor leg)
        "verdict": verdict_vs_frozen(mde, "adaptive_103a", acc["frozen"], acc["adaptive_103a"]),
        "verdict_variant_c_vs_frozen": verdict_vs_frozen(mde, "variant_c", acc["frozen"], acc["variant_c"]),
        "state_delta_mde": state_delta("frozen", "adaptive_103a"),
        # STATE-shape MDE gap (variant_c − §10.3a) — VALID ONLY when BOTH forms are DET-eligible
        # (leak-clean). A leaking form's MDE is meaningless (it "detects" at the lowest edge by
        # passing ~everything), so this gap is NaN wherever variant-c is off the DET curve — it is
        # never a power/recovery comparison there. Disclosure-only; the verdict is FPR-gated.
        "state_mde_gap_both_eligible_bps": (mde[("variant_c", "state")] - mde[("adaptive_103a", "state")])
        if (leak_clean["variant_c"] and leak_clean["adaptive_103a"]
            and math.isfinite(mde[("variant_c", "state")])
            and math.isfinite(mde[("adaptive_103a", "state")]))
        else math.nan,
        "both_det_eligible": bool(leak_clean["variant_c"] and leak_clean["adaptive_103a"]),
        **{f"mde_{f}_{s}": mde[(f, s)] for f in FORMS for s in SHAPES},
        **{f"dogfood_fpr_{f}": dogfood[f][0] for f in FORMS},
        **{f"dogfood_fpr_{f}_hw": dogfood[f][1] for f in FORMS},
        **{f"dogfood_passes_{f}": dogfood[f][3] for f in FORMS},
        "dogfood_draws": dogfood["adaptive_103a"][2],
        "dogfood_fpr_adaptive": dogfood["adaptive_103a"][0],   # anchor-name alias
        **{f"fpr_acceptable_{f}": acc[f] for f in FORMS},
        **{f"future_destroy_max_{f}": fd_max[f] for f in ADAPTIVE_FORMS},
        **{f"leak_clean_{f}": leak_clean[f] for f in ADAPTIVE_FORMS},
        **{f"tripwire_failures_{f}": "; ".join(form_failures[f]) for f in ADAPTIVE_FORMS},
        "tripwire_failures": "; ".join(failures),
    }
    return summary


def run_job(job: Job) -> list[dict]:
    """Worker: set the coupled Q_STUD_MIN, run both domains for one instrument. Seed-deterministic."""
    ra.Q_STUD_MIN = NormalDist().inv_cdf(Q_STAR)        # candidate-blind, from q* alone (Q5)
    minutes = load_analysis_minutes(Path(job.path))
    out: list[dict] = []
    for domain in ADAPTIVE_DOMAINS:
        returns, aligned = build_domain(minutes, domain)
        if len(returns) < 200:
            continue
        out.append(run_stratum(returns, aligned, job.instrument, domain))
    return out


# --------------------------------------------------------------------------- #
# Regression anchor
# --------------------------------------------------------------------------- #
def check_regression_anchor(rows: list[dict]) -> dict:
    """Verify the §10.3a form reproduces EXP-003 per stratum (verdict + STATE ΔMDE + adaptive FPR).

    A mismatch ⇒ adding `adaptive_row_variant_c` perturbed the §10.3a path or the harness is mis-wired
    ⇒ the adjudication is uninterpretable (fix + rerun). Proves the variant addition is purely additive.
    """
    if not EXP003_STRATUM_CSV.exists():
        return {"status": "MISSING_REFERENCE", "csv": str(EXP003_STRATUM_CSV)}
    ref = {(r["instrument"], r["domain"]): r for r in pl.read_csv(EXP003_STRATUM_CSV).to_dicts()}
    mismatches = []
    for r in rows:
        key = (r["instrument"], r["domain"])
        if key not in ref:
            mismatches.append({"stratum": "/".join(key), "issue": "absent in EXP-003"})
            continue
        e = ref[key]
        same_v = r["verdict"] == e["verdict"]
        d_now, d_ref = r["state_delta_mde"], e.get("state_delta_mde")
        same_d = (math.isnan(d_now) and (d_ref is None or (isinstance(d_ref, float) and math.isnan(d_ref)))) \
            or (isinstance(d_ref, (int, float)) and math.isfinite(d_now) and abs(d_now - float(d_ref)) < 1e-9)
        same_fpr = abs(r["dogfood_fpr_adaptive"] - float(e["dogfood_fpr_adaptive"])) < 1e-9
        if not (same_v and same_d and same_fpr):
            mismatches.append({"stratum": "/".join(key), "verdict": [r["verdict"], e["verdict"]],
                               "state_delta": [d_now, d_ref],
                               "fpr_adaptive": [r["dogfood_fpr_adaptive"], e["dogfood_fpr_adaptive"]]})
    return {"status": "PASS" if not mismatches else "FAIL", "n_strata": len(rows),
            "n_mismatch": len(mismatches), "mismatches": mismatches}


# --------------------------------------------------------------------------- #
# FREEZE manifest
# --------------------------------------------------------------------------- #
def _git_commit() -> str:
    """Short git HEAD (best-effort; 'UNKNOWN' if unavailable)."""
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "UNKNOWN"


def build_freeze_manifest(adjudication_summary: dict, anchor: dict, *, s103a_leak_clean: bool,
                          vc_leak_clean: bool) -> dict:
    """Assemble the freeze manifest IF the freeze conditions hold (else FREEZE_BLOCKED).

    Freeze decision (predeclared, DET-dominance "at equal-or-better FPR"):
      * The freeze CANDIDATE is §10.3a. It is BLOCKED (REJECT-class) only if the anchor fails OR
        §10.3a itself fails a leak tripwire — a variant-c leak is variant-c's refutation, never a
        §10.3a blocker.
      * variant-c can be frozen instead only if it is **itself leak-clean** AND strictly DET-dominates
        §10.3a on ≥1 stratum with no §10.3a counter-win (a real DET winner).
      * Otherwise freeze §10.3a; record variant-c as the rejected alternative (refuted if not
        leak-clean; out-DET'd otherwise).
    """
    n = adjudication_summary["n_strata"]
    a_wins = adjudication_summary["n_103a_matches_or_beats"]
    c_dom = adjudication_summary["n_variant_c_dominates"]
    blocked: list[str] = []
    if anchor.get("status") != "PASS":
        blocked.append(f"regression anchor {anchor.get('status')}")
    if not s103a_leak_clean:
        blocked.append("§10.3a (freeze candidate) failed a leak tripwire — REJECT-class")
    freeze_variant_c = bool(vc_leak_clean and c_dom > 0 and a_wins + c_dom == n)
    if blocked:
        frozen_form, rejected = "(none — blocked)", "(none — blocked)"
    elif freeze_variant_c:
        frozen_form = "variant_c (gate_stack_adaptive/adaptive_row_variant_c)"
        rejected = "10.3a (adaptive_row)"
    else:
        frozen_form = "10.3a (gate_stack_adaptive/adaptive_row)"
        rejected = "variant_c (adaptive_row_variant_c)"
    src_hash = hashlib.sha256(REFEREE_ADAPTIVE_SRC.read_bytes()).hexdigest()
    return {
        "status": "FREEZE_BLOCKED" if blocked else "FROZEN",
        "blocked_reasons": blocked,
        "frozen_referee": frozen_form,
        "rejected_alternative": rejected,
        "variant_c_leak_clean": vc_leak_clean,
        "variant_c_refuted_no_fpr_control": not vc_leak_clean,
        "s103a_leak_clean": s103a_leak_clean,
        "operating_point": {"q_star": Q_STAR, "Q_STUD_MIN": NormalDist().inv_cdf(Q_STAR),
                            "N_BOOTSTRAP": N_BOOTSTRAP, "alpha": ALPHA,
                            "MIN_EPISODES_SUBPOP": MIN_EPISODES_SUBPOP,
                            "subpop_quantile_module_default": SUBPOP_QUANTILE,
                            "return_basis": "open_to_open_le_t_minus_1"},
        "materiality_bps": {"1h": materiality_bps_for("1h"), "4h": materiality_bps_for("4h")},
        "cost_map": ROUND_TRIP_COST_BPS_17,
        "adjudication_fpr_rule": {"MIN_FPR_PASSES": MIN_FPR_PASSES,
                                  "FPR_CONTROL_BOUND": FPR_CONTROL_BOUND,
                                  "note": "adjudication-harness only; gate adaptive_row byte-unchanged"},
        "provenance": {"referee_adaptive_sha256": src_hash, "git_commit": _git_commit(),
                       "referee_calibration": "byte-frozen (Chapter-01 suite untouched)"},
        "adjudication": adjudication_summary,
        "regression_anchor": {"status": anchor.get("status"), "n_mismatch": anchor.get("n_mismatch")},
    }


# --------------------------------------------------------------------------- #
# Plotting (bounded inputs)
# --------------------------------------------------------------------------- #
_ADJ_CODE = {"10.3a_MATCHES_OR_BEATS": 2.0, "MIXED": 1.0, "VARIANT_C_DOMINATES": 0.0}


def plot_form_det_map(rows: list[dict], save_path: Path) -> None:
    """§10.3a-vs-variant-c DET map: per stratum, ΔMDE = MDE_vc − MDE_103a by shape (>0 => 103a better)."""
    strata = sorted({(r["instrument"], r["domain"]) for r in rows})
    labels = [f"{i}/{d}" for i, d in strata]
    sidx = {s: k for k, s in enumerate(strata)}
    grid = np.full((len(strata), len(SHAPES)), np.nan)
    for r in rows:
        i = sidx[(r["instrument"], r["domain"])]
        for j, s in enumerate(SHAPES):
            a, c = r[f"mde_adaptive_103a_{s}"], r[f"mde_variant_c_{s}"]
            if math.isfinite(a) and math.isfinite(c):
                grid[i, j] = c - a
    sns.set_theme(style="white")
    fig, ax = plt.subplots(figsize=(7, 10))
    vmax = float(np.nanmax(np.abs(grid))) if np.isfinite(grid).any() else 1.0
    sns.heatmap(grid, ax=ax, cmap="RdYlGn", center=0.0, vmin=-vmax, vmax=vmax, annot=True, fmt=".1f",
                xticklabels=list(SHAPES), yticklabels=labels,
                cbar_kws={"label": "MDE_variant_c − MDE_§10.3a (bps); >0 => §10.3a lower MDE"},
                linewidths=0.4, linecolor="lightgrey")
    ax.set_title("§10.3a vs variant-c: ΔMDE per stratum × shape (green = §10.3a beats variant-c)")
    ax.set_xlabel("edge shape")
    ax.set_ylabel("instrument / domain")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_state_mde(rows: list[dict], save_path: Path) -> None:
    """STATE MDE per stratum: §10.3a (sub-pop recovery) vs variant-c (single-stat) — the discriminator."""
    strata = sorted({(r["instrument"], r["domain"]) for r in rows})
    labels = [f"{i}/{d}" for i, d in strata]
    by = {(r["instrument"], r["domain"]): r for r in rows}
    cap = max(EDGE_GRID_BPS) * 1.15

    def cap_inf(v: float) -> float:
        return cap if math.isinf(v) else v

    x = np.arange(len(strata))
    a = [cap_inf(by[s]["mde_adaptive_103a_state"]) for s in strata]
    c = [cap_inf(by[s]["mde_variant_c_state"]) for s in strata]
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(x - 0.2, a, width=0.4, label="§10.3a (adaptive_row)")
    ax.bar(x + 0.2, c, width=0.4, label="variant-c (single-statistic)")
    ax.axhline(cap, color="grey", ls=":", lw=1, label=f"UNPOWERED (>{max(EDGE_GRID_BPS)} bps)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=90, fontsize=7)
    ax.set_title("STATE-shape MDE per stratum: §10.3a sub-pop recovery vs variant-c single-statistic")
    ax.set_ylabel("STATE MDE (bps; lower = better)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_dogfood_fpr(rows: list[dict], save_path: Path) -> None:
    """Dogfood FPR per stratum for both adaptive forms vs the 2α control (E5 less-brittle rule)."""
    strata = sorted({(r["instrument"], r["domain"]) for r in rows})
    labels = [f"{i}/{d}" for i, d in strata]
    by = {(r["instrument"], r["domain"]): r for r in rows}
    x = np.arange(len(strata))
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.errorbar(x - 0.1, [by[s]["dogfood_fpr_adaptive_103a"] for s in strata],
                yerr=[by[s]["dogfood_fpr_adaptive_103a_hw"] for s in strata], fmt="o",
                label="§10.3a", capsize=2)
    ax.errorbar(x + 0.1, [by[s]["dogfood_fpr_variant_c"] for s in strata],
                yerr=[by[s]["dogfood_fpr_variant_c_hw"] for s in strata], fmt="^",
                label="variant-c", capsize=2)
    ax.axhline(FPR_CONTROL_BOUND, color="red", ls="--", lw=1, label=f"control 2α={FPR_CONTROL_BOUND}")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=90, fontsize=7)
    ax.set_title("Dogfood FPR per stratum: §10.3a vs variant-c (E5 less-brittle rule; Wilson bars)")
    ax.set_ylabel("dogfood FPR")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Serialisation / summary
# --------------------------------------------------------------------------- #
def summarise_adjudication(rows: list[dict], anchor: dict) -> dict:
    """Programme-level adjudication tally (disclosure-only; the binding endpoint is per stratum)."""
    n = len(rows)
    a = sum(r["adjudication"] == "10.3a_MATCHES_OR_BEATS" for r in rows)
    c = sum(r["adjudication"] == "VARIANT_C_DOMINATES" for r in rows)
    m = sum(r["adjudication"] == "MIXED" for r in rows)
    n_both = sum(r["both_det_eligible"] for r in rows)
    gap = [r["state_mde_gap_both_eligible_bps"] for r in rows
           if math.isfinite(r["state_mde_gap_both_eligible_bps"])]
    return {"n_strata": n, "n_103a_matches_or_beats": a, "n_variant_c_dominates": c, "n_mixed": m,
            "n_strata_both_det_eligible": n_both,
            "state_mde_gap_vc_minus_103a_both_eligible_median_bps": float(np.median(gap)) if gap else math.nan,
            "state_mde_gap_vc_minus_103a_both_eligible_max_bps": float(np.max(gap)) if gap else math.nan,
            "state_mde_gap_note": "valid only where BOTH forms DET-eligible; NaN if n_both==0 "
                                  "(a leaking form's MDE is not a valid comparison)",
            "regression_anchor": anchor.get("status")}


def write_results(rows: list[dict], anchor: dict, adj: dict, manifest: dict) -> None:
    """Persist the per-stratum form table, the anchor check, the adjudication summary, the manifest."""
    pl.DataFrame(rows).write_csv(RESULTS_DIR / "form_adjudication_per_stratum.csv")
    (RESULTS_DIR / "regression_anchor_check.json").write_text(json.dumps(anchor, indent=2, default=str))
    (RESULTS_DIR / "adjudication_summary.json").write_text(json.dumps(adj, indent=2, default=str))
    (RESULTS_DIR / "freeze_manifest.json").write_text(json.dumps(manifest, indent=2, default=str))


def summarise(rows: list[dict], adj: dict, manifest: dict) -> None:
    """Concise stdout: adjudication tally + freeze status + leak summary."""
    logger.info("\n=== EXP-005 E5 adjudication summary ===")
    logger.info("  strata: %d | §10.3a matches-or-beats: %d | variant-c dominates: %d | mixed: %d",
                adj["n_strata"], adj["n_103a_matches_or_beats"], adj["n_variant_c_dominates"],
                adj["n_mixed"])
    logger.info("  STATE-MDE gap (vc−§10.3a, valid only where BOTH DET-eligible): n_both=%d, "
                "median %.2f / max %.2f bps", adj["n_strata_both_det_eligible"],
                adj["state_mde_gap_vc_minus_103a_both_eligible_median_bps"],
                adj["state_mde_gap_vc_minus_103a_both_eligible_max_bps"])
    for form in ADAPTIVE_FORMS:
        fd = max((r[f"future_destroy_max_{form}"] for r in rows), default=0.0)
        unacc = sum(not r[f"fpr_acceptable_{form}"] for r in rows)
        not_clean = sum(not r[f"leak_clean_{form}"] for r in rows)
        logger.info("  %-14s future-destroy max %.3f | FPR-unacceptable %d/%d | NOT-leak-clean %d/%d",
                    form, fd, unacc, len(rows), not_clean, len(rows))
    # §10.3a is the freeze candidate: its tripwire failures are REJECT-class. variant-c's are its
    # expected refutation (no FPR control) — informative, not a fix+rerun.
    s103a_trip = [r for r in rows if r["tripwire_failures_adaptive_103a"]]
    vc_trip = [r for r in rows if r["tripwire_failures_variant_c"]]
    if s103a_trip:
        logger.error("  §10.3a LEAK-TRIPWIRE FAILURES (%d) — REJECT-class, fix+rerun:", len(s103a_trip))
        for r in s103a_trip:
            logger.error("    - %s", r["tripwire_failures_adaptive_103a"])
    else:
        logger.info("  §10.3a leak-clean on all %d strata (freeze candidate intact).", len(rows))
    logger.info("  variant-c leak-tripwire failures on %d/%d strata = its REFUTATION (no FPR control), "
                "expected/informative.", len(vc_trip), len(rows))
    logger.info("  FREEZE: %s -> %s (rejected: %s)", manifest["status"],
                manifest["frozen_referee"], manifest["rejected_alternative"])
    if manifest["blocked_reasons"]:
        logger.error("  FREEZE BLOCKED: %s", "; ".join(manifest["blocked_reasons"]))


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    instruments = sorted(ROUND_TRIP_COST_BPS_17)
    available = {ins: era_file_for(ins) for ins in instruments}
    missing = [ins for ins, p in available.items() if p is None]
    if missing:
        logger.info("SKIP (no 5-year-era file): %s", ", ".join(missing))
    jobs = [Job(ins, str(available[ins])) for ins in instruments if available[ins]]
    logger.info("running %d instruments x 2 domains x 3 forms over %d workers", len(jobs), N_WORKERS)

    rows: list[dict] = []
    with ProcessPoolExecutor(max_workers=N_WORKERS) as pool:
        futures = {pool.submit(run_job, job): job.instrument for job in jobs}
        for fut in tqdm(as_completed(futures), total=len(futures), desc="instrument"):
            rows.extend(fut.result())

    if not rows:
        logger.error("No strata produced results — check data availability.")
        return

    rows.sort(key=lambda r: (r["instrument"], r["domain"]))
    anchor = check_regression_anchor(rows)
    logger.info("regression anchor (§10.3a vs EXP-003): %s (mismatch %s/%s)",
                anchor.get("status"), anchor.get("n_mismatch"), anchor.get("n_strata"))

    adj = summarise_adjudication(rows, anchor)
    s103a_leak_clean = all(r["leak_clean_adaptive_103a"] for r in rows)
    vc_leak_clean = all(r["leak_clean_variant_c"] for r in rows)
    manifest = build_freeze_manifest(adj, anchor, s103a_leak_clean=s103a_leak_clean,
                                     vc_leak_clean=vc_leak_clean)

    write_results(rows, anchor, adj, manifest)
    plot_form_det_map(rows, PLOTS_DIR / "form_det_map.png")
    plot_state_mde(rows, PLOTS_DIR / "state_mde_103a_vs_variant_c.png")
    plot_dogfood_fpr(rows, PLOTS_DIR / "dogfood_fpr_forms.png")
    summarise(rows, adj, manifest)
    logger.info("results -> %s", RESULTS_DIR / "form_adjudication_per_stratum.csv")
    if anchor.get("status") != "PASS":
        logger.error("REGRESSION ANCHOR NOT PASS (%s) — adjudication uninterpretable until fixed.",
                     anchor.get("status"))


if __name__ == "__main__":
    main()
