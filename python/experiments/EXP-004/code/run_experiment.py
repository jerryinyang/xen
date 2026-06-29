"""
Experiment EXP-004 (E4): Robustness pass for the E3a adaptive gate — license the E5 freeze.

Implements python/experiments/EXP-004/design.md (GATE APPROVE). Analysis-only. Maps the robustness
surface of the as-built `xen.referee_adaptive.gate_stack_adaptive` (studentized∧bps sub-pop L5, L1
rigid) over its PRE-REGISTERED knobs, reusing the EXP-003 3-arm DET orchestration with the swept
knobs threaded EXPLICITLY (referee_adaptive.py / referee_calibration.py stay byte-frozen):

  R1 q-sensitivity   : q* in {0.6, 0.7, 0.75*, 0.8}, Q_STUD_MIN = Phi^-1(q*) co-moving (candidate-blind)
  R2 bootstrap/seed  : q*=0.75, (N_BOOTSTRAP, seed_off) over {500,1000} x {0,+100000}
  R3 residual skew   : q*=0.75, abstract nulls right-skew-stressed (does skew push stud_q > Q_STUD_MIN?)
  D-CIwidth / D-regime: ride-along disclosures (4h sub-pop CI width; recent-third regime persistence)

Knob injection (deterministic, candidate-blind): `q` is passed to `gate_stack_adaptive`; the coupled
`Q_STUD_MIN = Phi^-1(q)` is set on the `referee_adaptive` module per config inside each worker (the
only consumer is `adaptive_row`); `n_bootstrap`/`seed_off` are explicit params. `materiality_bps`,
L1+coverage, the cost map are UNTOUCHED. At (q=0.75, N_BOOTSTRAP=500, seed_off=0, standard nulls) the
driver MUST reproduce EXP-003 (A1) per-stratum — the regression anchor; a mismatch is a harness bug.

Binding (per stratum, L-03): the verdict's STABILITY across the sweep. FREEZE LICENSED iff no stratum
flips (DET_DOMINANT held), STATE ΔMDE stays >0, adaptive skew-null FPR not Wilson-resolved above
control, future-destroy collapses at every sweep point. Pooled counts disclosure-only.
"""
from __future__ import annotations

import json
import logging
import math
import os
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
    ROUND_TRIP_COST_BPS_17,
    adaptive_cost_bps_for,
    adaptive_row,
    gate_stack_adaptive,
    gate_stack_core_costfn,
    next_open_to_open_returns_from_bars,
    strategy_return_bps_turnover,
)
from xen.referee_calibration import (
    EDGE_GRID_BPS,
    donchian_breakout_positions,
    finite_values,
    gate_stack_row,
    ma_crossover_positions,
    permuted_returns,
    random_state_positions,
    strategy_return_bps,
    wilson_interval,
)
from xen.referee_substrate import (
    dense_planted,
    sparse_positions,
    state_dependent_planted,
    state_positions,
    tail_only_planted,
    persistent_positions,
)
from xen.incremental_referee import EPISODE_LENGTHS

logger = logging.getLogger("EXP-004")

# --------------------------------------------------------------------------- #
# Constants  (substrate / draw budget reused from EXP-003 — bit-identical anchor)
# --------------------------------------------------------------------------- #
DATA_DIR = Path("data")
EXP_DIR = Path("python/experiments/EXP-004")
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"
EXP003_STRATUM_CSV = Path("python/experiments/EXP-003/results/det_dominance_per_stratum.csv")

ANALYSIS_FRACTION = 0.70
ERA_GLOB = "20210602_*"
PERIOD_MINUTES = {"1h": 60, "4h": 240}
DOMAIN_MIN_COVERAGE = 0.90

ALPHA = 0.05
N_NULL = 80
N_PLANT = 20
POWER_TARGET = 0.50
N_BOOTSTRAP_BASE = 500
N_BOOTSTRAP_HIGH = 1000
SEED_OFF_ALT = 100_000

SHAPES: tuple[str, ...] = ("dense", "tail", "sparse", "state")
ARMS: tuple[str, ...] = ("frozen", "frozen_amortized", "adaptive")
FPR_CONTROL_BOUND = 2 * ALPHA

# R1 sweep of the one adaptive free knob; 0.75 is the E3a baseline / regression anchor.
Q_STAR_SWEEP: tuple[float, ...] = (0.6, 0.7, 0.75, 0.8)
Q_STAR_BASELINE = 0.75
# R3: fixed right-skew stress strength for the lognormal-type marginal transform (predeclared, not
# tuned on outcomes). Larger => heavier right tail in the (no-edge) null returns.
SKEW_LAMBDA = 1.0
# D-regime: most-recent fraction of the (first-70%) analysis slice for the regime-persistence check.
RECENT_FRACTION = 1.0 / 3.0
RECENT_MID_EDGE_BPS = 8.0  # fixed mid-grid edge for the D-CIwidth probe (a disclosure, not a verdict)

N_WORKERS = min(os.cpu_count() or 1, 16)


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class SweepConfig:
    """One robustness sweep point. `q` drives `gate_stack_adaptive` + the coupled Q_STUD_MIN."""
    name: str
    probe: str                 # "R1" | "R2" | "R3" | "D-regime"
    q: float
    n_bootstrap: int
    seed_off: int
    null_mode: str = "standard"   # "standard" | "skew"
    recent_only: bool = False


def build_configs() -> list[SweepConfig]:
    """The pre-registered sweep grid (anchor = R1 q=0.75 = R2 (500,0))."""
    cfgs: list[SweepConfig] = []
    for q in Q_STAR_SWEEP:                                   # R1 (incl. anchor q=0.75)
        cfgs.append(SweepConfig(f"R1_q{q}", "R1", q, N_BOOTSTRAP_BASE, 0))
    for nb in (N_BOOTSTRAP_BASE, N_BOOTSTRAP_HIGH):          # R2 bootstrap x seed (skip (500,0)=anchor)
        for off in (0, SEED_OFF_ALT):
            if nb == N_BOOTSTRAP_BASE and off == 0:
                continue
            cfgs.append(SweepConfig(f"R2_nb{nb}_off{off}", "R2", Q_STAR_BASELINE, nb, off))
    cfgs.append(SweepConfig("R3_skew", "R3", Q_STAR_BASELINE, N_BOOTSTRAP_BASE, 0, null_mode="skew"))
    cfgs.append(SweepConfig("D-regime_recent", "D-regime", Q_STAR_BASELINE, N_BOOTSTRAP_BASE, 0,
                            recent_only=True))
    return cfgs


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


def build_domain(minutes: pl.DataFrame, domain: str,
                 *, recent_only: bool) -> tuple[np.ndarray, pl.DataFrame]:
    """Open-to-open <=t-1 returns + aligned fenced domain frame (for the dogfood OHLC signals).

    Optionally restricted to the most-recent `RECENT_FRACTION` of the (first-70%) analysis returns
    (D-regime disclosure) — still strictly inside the analysis set; the global holdout is untouched.
    """
    dom = aggregate_ohlc(minutes, period_minutes=PERIOD_MINUTES[domain],
                         min_coverage=DOMAIN_MIN_COVERAGE)
    dom = dom.filter(pl.col("CloseTime") <= minutes.get_column("CloseTime").max())
    returns, aligned = next_open_to_open_returns_from_bars(dom)
    if recent_only and len(returns) > 0:
        start = int(len(returns) * (1.0 - RECENT_FRACTION))
        returns, aligned = returns[start:], aligned.slice(start, len(returns) - start)
    return returns, aligned


# --------------------------------------------------------------------------- #
# Pure helpers — substrate, nulls, gate arms  (mirror EXP-003; knobs threaded)
# --------------------------------------------------------------------------- #
def reblocked_random_positions(n: int, episode_length: int, seed: int) -> np.ndarray:
    """random_state_positions re-blocked to length L (mirrors EXP-003)."""
    n_episodes = (n + episode_length - 1) // episode_length
    return np.repeat(random_state_positions(n_episodes, seed), episode_length)[:n]


def lag_open_to_open(positions: np.ndarray) -> np.ndarray:
    """Lag a close-indexed signal one bar so it acts at the next bar's open on confirmed bars <=t-1."""
    pos = np.asarray(positions, dtype=float)
    return np.concatenate(([0.0], pos[:-1]))


def skew_returns(returns: np.ndarray, *, lam: float) -> np.ndarray:
    """Right-skew, ~mean-0 marginal transform of a (no-edge) null returns series (R3 stress).

    Lognormal-type map of the standardized series: ``exp(lam * z)`` is right-skewed; recentred to
    sample-mean 0 and rescaled to the original dispersion. The transform is ELEMENTWISE (marginal) —
    it does not touch ordering or any return/position alignment, so a destroyed-alignment null stays
    a genuine no-edge null; only the marginal skewness changes. Provenance: reads the input series
    only (no future bar, no positions, no outcome). `lam` is a fixed predeclared stress level.
    """
    r = np.asarray(returns, dtype=float)
    fin = finite_values(r)
    sd = float(np.std(fin)) if len(fin) else 0.0
    if sd == 0.0 or lam <= 0.0:
        return r.copy()
    z = (r - float(np.mean(fin))) / sd
    raw = np.exp(lam * z)
    centred = raw - float(np.mean(finite_values(raw)))
    return centred * (sd / lam)


def make_shape(shape: str, returns: np.ndarray, *, net_edge_bps: float, cost_bps: float,
               episode_length: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """(planted_returns, positions) for one shape draw (matched-magnitude; mirrors EXP-003)."""
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


def gate_passes(arm: str, returns: np.ndarray, positions: np.ndarray, *, domain: str,
                cost_bps: float, seed: int, q: float, n_bootstrap: int) -> bool:
    """True iff the named gate arm PASSES for one draw. `q`/`n_bootstrap` threaded (E4 knobs).

    `adaptive` consumes the swept `q`; the coupled `Q_STUD_MIN = Phi^-1(q)` is set on the
    `referee_adaptive` module per config (see `apply_knob`) and read by `adaptive_row`. Frozen arms
    are q-invariant (a consistency check across the q-sweep).
    """
    if arm == "adaptive":
        core = gate_stack_adaptive(returns, positions, domain=domain, cost_bps=cost_bps,
                                   n_bootstrap=n_bootstrap, seed=seed, q=q)
        return bool(adaptive_row(core, alpha=ALPHA)["passed"])
    fn = strategy_return_bps_turnover if arm == "frozen_amortized" else strategy_return_bps
    core = gate_stack_core_costfn(returns, positions, domain=domain, cost_bps=cost_bps,
                                  n_bootstrap=n_bootstrap, seed=seed, strategy_fn=fn)
    return bool(gate_stack_row(core, alpha=ALPHA)["passed"])


def detection_rate(arm: str, shape: str, returns: np.ndarray, *, domain: str, episode_length: int,
                   cost_bps: float, net_edge_bps: float, q: float, n_bootstrap: int,
                   seed_off: int) -> float:
    """Fraction of planted draws the arm PASSES (early-stop at the POWER_TARGET binomial boundary).

    The denominator stays N_PLANT so the returned rate lands on the SAME side of POWER_TARGET as a
    full run — the MDE decision is bit-identical (mirrors EXP-003).
    """
    need = math.ceil(POWER_TARGET * N_PLANT)
    passes = 0
    for k in range(N_PLANT):
        planted, pos = make_shape(shape, returns, net_edge_bps=net_edge_bps, cost_bps=cost_bps,
                                  episode_length=episode_length, seed=6000 + k + seed_off)
        passes += gate_passes(arm, planted, pos, domain=domain, cost_bps=cost_bps,
                              seed=7000 + k + seed_off, q=q, n_bootstrap=n_bootstrap)
        remaining = N_PLANT - (k + 1)
        if passes >= need or passes + remaining < need:
            break
    return passes / N_PLANT


def mde_of(arm: str, shape: str, returns: np.ndarray, *, domain: str, episode_length: int,
           cost_bps: float, q: float, n_bootstrap: int, seed_off: int) -> float:
    """DETECTED_FLOOR MDE for an arm x shape (inf = UNPOWERED)."""
    for edge in EDGE_GRID_BPS:
        if edge <= 0.0:
            continue
        if detection_rate(arm, shape, returns, domain=domain, episode_length=episode_length,
                          cost_bps=cost_bps, net_edge_bps=edge, q=q, n_bootstrap=n_bootstrap,
                          seed_off=seed_off) >= POWER_TARGET:
            return edge
    return math.inf


def no_plant_passrate(arm: str, shape: str, returns: np.ndarray, *, domain: str,
                      episode_length: int, cost_bps: float, q: float, n_bootstrap: int,
                      seed_off: int) -> float:
    """No-real-edge guard: arm PASS rate on the shape's positions with NO planted drift."""
    passes = 0
    for k in range(N_PLANT):
        _, pos = make_shape(shape, returns, net_edge_bps=0.0, cost_bps=cost_bps,
                            episode_length=episode_length, seed=6000 + k + seed_off)
        passes += gate_passes(arm, returns, pos, domain=domain, cost_bps=cost_bps,
                              seed=7000 + k + seed_off, q=q, n_bootstrap=n_bootstrap)
    return passes / N_PLANT


def future_destroyed_passrate(arm: str, shape: str, returns: np.ndarray, *, domain: str,
                              episode_length: int, cost_bps: float, net_edge_bps: float, q: float,
                              n_bootstrap: int, seed_off: int) -> float:
    """Leak control: plant edge, permute returns (destroy alignment) -> must collapse to FPR."""
    passes = 0
    for k in range(N_PLANT):
        planted, pos = make_shape(shape, returns, net_edge_bps=net_edge_bps, cost_bps=cost_bps,
                                  episode_length=episode_length, seed=6000 + k + seed_off)
        destroyed = permuted_returns(planted, seed=8000 + k + seed_off)
        passes += gate_passes(arm, destroyed, pos, domain=domain, cost_bps=cost_bps,
                              seed=7000 + k + seed_off, q=q, n_bootstrap=n_bootstrap)
    return passes / N_PLANT


def dogfood_fpr(arm: str, returns: np.ndarray, aligned: pl.DataFrame, *, domain: str,
                episode_length: int, cost_bps: float, q: float, n_bootstrap: int, seed_off: int,
                null_mode: str) -> tuple[float, float, int, int]:
    """Per-stratum FPR for an arm over 3 null families (abstract x2 + real dogfood Donchian/MA).

    Mirrors EXP-003 `dogfood_fpr` EXACTLY at `null_mode="standard"`, `seed_off=0` (the regression
    anchor). `passes` is threaded out for the A1 Wilson-resolved verdict. `null_mode="skew"` (R3)
    applies the right-skew marginal transform to every null RETURNS series (positions/signals held
    fixed) — a genuine no-edge stress isolating whether marginal skew lifts the studentized sub-pop
    path's FPR. Donchian/MA positions come from REAL (un-skewed) OHLC — only the return distribution
    is stressed.
    """
    n = len(returns)
    skew = null_mode == "skew"
    base = skew_returns(returns, lam=SKEW_LAMBDA) if skew else returns
    passes, draws = 0, 0
    for k in range(N_NULL):
        pr = permuted_returns(returns, seed=1000 + k + seed_off)
        if skew:
            pr = skew_returns(pr, lam=SKEW_LAMBDA)
        passes += gate_passes(arm, pr, persistent_positions(n, episode_length, 2000 + k + seed_off),
                              domain=domain, cost_bps=cost_bps, seed=3000 + k + seed_off, q=q,
                              n_bootstrap=n_bootstrap)
        passes += gate_passes(arm, base,
                              reblocked_random_positions(n, episode_length, 4000 + k + seed_off),
                              domain=domain, cost_bps=cost_bps, seed=5000 + k + seed_off, q=q,
                              n_bootstrap=n_bootstrap)
        draws += 2
    high = aligned.get_column("High").to_numpy()
    low = aligned.get_column("Low").to_numpy()
    close = aligned.get_column("Close").to_numpy()
    don = lag_open_to_open(donchian_breakout_positions(high, low, close, lookback=20))
    ma = lag_open_to_open(ma_crossover_positions(close, fast=20, slow=50))
    for sig, sd in ((don, 9001 + seed_off), (ma, 9002 + seed_off)):
        passes += gate_passes(arm, base, sig, domain=domain, cost_bps=cost_bps, seed=sd, q=q,
                              n_bootstrap=n_bootstrap)
        draws += 1
    _, lo, hi = wilson_interval(passes, draws)
    return passes / draws, (hi - lo) / 2.0, draws, passes


# --------------------------------------------------------------------------- #
# Per-stratum orchestration
# --------------------------------------------------------------------------- #
def classify_stratum(mde: dict, dogfood: dict) -> str:
    """DET_DOMINANT / NOT_IMPROVED / FPR_BROKEN for one stratum (binding, L-03; A1 noise-tolerant).

    FPR_BROKEN only when the adaptive dogfood-FPR is Wilson-RESOLVED above the frozen arm
    (wilson_lower(adaptive) > frozen rate). Identical rule to EXP-003 `classify_stratum`.
    """
    _, _, draws_a, passes_a = dogfood["adaptive"]
    _, adaptive_lo, _ = wilson_interval(passes_a, draws_a)
    if adaptive_lo > dogfood["frozen"][0]:
        return "FPR_BROKEN"
    no_regression = all(mde[("adaptive", s)] <= mde[("frozen", s)] for s in SHAPES)
    strict = any(mde[("adaptive", s)] < mde[("frozen", s)] for s in SHAPES)
    return "DET_DOMINANT" if (no_regression and strict) else "NOT_IMPROVED"


def ci_width_probe(returns: np.ndarray, *, domain: str, episode_length: int, cost_bps: float,
                   q: float, n_bootstrap: int) -> dict:
    """D-CIwidth disclosure: sub-pop raw-quantile bootstrap CI half-width + n_episodes on a fixed
    mid-grid STATE plant (one adaptive call). Confirms CI width shrinks with episode count (L-06)."""
    planted, pos = make_shape("state", returns, net_edge_bps=RECENT_MID_EDGE_BPS, cost_bps=cost_bps,
                              episode_length=episode_length, seed=6000)
    core = gate_stack_adaptive(planted, pos, domain=domain, cost_bps=cost_bps,
                               n_bootstrap=n_bootstrap, seed=7000, q=q)
    row = json.loads(adaptive_row(core, alpha=ALPHA)["leg_results"])
    raw_lo = row["L5_subpop_raw_ci_lower_bps"]
    stat = row["subpop_stat_bps"]
    hw = (stat - raw_lo) if (isinstance(raw_lo, float) and math.isfinite(raw_lo)) else math.nan
    return {"n_episodes": int(core["n_episodes"]), "subpop_raw_ci_halfwidth_bps": hw}


def run_stratum(cfg: SweepConfig, returns: np.ndarray, aligned: pl.DataFrame, instrument: str,
                domain: str) -> dict:
    """Per (config, stratum): MDE x shape x arm, dogfood FPR, verdict, tripwires, ΔMDE (mirrors
    EXP-003 run_stratum with knobs threaded). Returns one summary dict."""
    L = EPISODE_LENGTHS[domain]
    cost = adaptive_cost_bps_for(instrument, domain)
    kw = dict(domain=domain, episode_length=L, cost_bps=cost, q=cfg.q, n_bootstrap=cfg.n_bootstrap,
              seed_off=cfg.seed_off)
    failures: list[str] = []

    dogfood = {arm: dogfood_fpr(arm, returns, aligned, null_mode=cfg.null_mode, **kw) for arm in ARMS}
    mde: dict = {}
    fd_max = 0.0
    for shape in SHAPES:
        for arm in ARMS:
            mde[(arm, shape)] = mde_of(arm, shape, returns, **kw)
        npr = no_plant_passrate("adaptive", shape, returns, **kw)
        guard = max(dogfood["adaptive"][0] + 2 * dogfood["adaptive"][1], FPR_CONTROL_BOUND)
        if npr > guard:
            failures.append(f"{instrument}/{domain}/{shape}: no-plant(adaptive) {npr:.3f} > guard")
        levels = sorted({lvl for lvl in (mde[("adaptive", shape)], EDGE_GRID_BPS[-1])
                         if math.isfinite(lvl)})
        for lvl in levels:
            rate = future_destroyed_passrate("adaptive", shape, returns, net_edge_bps=lvl, **kw)
            fd_max = max(fd_max, rate)
            if rate > guard:
                failures.append(f"{instrument}/{domain}/{shape}: adaptive SURVIVED future-destroy "
                                f"(e={lvl}) pass={rate:.3f} -> LEAK")

    def delta(s: str) -> float:
        f, a = mde[("frozen", s)], mde[("adaptive", s)]
        return (f - a) if math.isfinite(f) and math.isfinite(a) else math.nan

    for arm in ARMS:
        if dogfood[arm][0] - dogfood[arm][1] > FPR_CONTROL_BOUND:
            failures.append(f"{instrument}/{domain}: dogfood FPR({arm}) {dogfood[arm][0]:.3f} > control")

    summary = {
        "config": cfg.name, "probe": cfg.probe, "q": cfg.q, "n_bootstrap": cfg.n_bootstrap,
        "seed_off": cfg.seed_off, "null_mode": cfg.null_mode, "recent_only": cfg.recent_only,
        "instrument": instrument, "domain": domain, "cost_bps": cost,
        "verdict": classify_stratum(mde, dogfood),
        "state_delta_mde": delta("state"),
        **{f"mde_adaptive_{s}": mde[("adaptive", s)] for s in SHAPES},
        **{f"mde_frozen_{s}": mde[("frozen", s)] for s in SHAPES},
        "dogfood_fpr_frozen": dogfood["frozen"][0], "dogfood_fpr_adaptive": dogfood["adaptive"][0],
        "dogfood_fpr_adaptive_hw": dogfood["adaptive"][1],
        "dogfood_passes_adaptive": dogfood["adaptive"][3], "dogfood_draws_adaptive": dogfood["adaptive"][2],
        "future_destroy_max_adaptive": fd_max,
        "tripwire_failures": "; ".join(failures),
    }
    if cfg.probe == "R1" and cfg.q == Q_STAR_BASELINE and domain == "4h":
        summary.update(ci_width_probe(returns, domain=domain, episode_length=L, cost_bps=cost,
                                      q=cfg.q, n_bootstrap=cfg.n_bootstrap))
    return summary


def run_job(cfg: SweepConfig, instrument: str, path_str: str) -> list[dict]:
    """Worker: set the coupled Q_STUD_MIN for this config, then run both domains for one instrument.

    Picklable + seed-deterministic. `Q_STUD_MIN = Phi^-1(q)` is set on the `referee_adaptive` module
    (the only consumer is `adaptive_row`); `q` is also passed explicitly to `gate_stack_adaptive`.
    """
    ra.Q_STUD_MIN = NormalDist().inv_cdf(cfg.q)        # candidate-blind, derived from q alone (Q5)
    minutes = load_analysis_minutes(Path(path_str))
    out: list[dict] = []
    for domain in ADAPTIVE_DOMAINS:
        returns, aligned = build_domain(minutes, domain, recent_only=cfg.recent_only)
        if len(returns) < 200:
            continue
        out.append(run_stratum(cfg, returns, aligned, instrument, domain))
    return out


# --------------------------------------------------------------------------- #
# Regression anchor
# --------------------------------------------------------------------------- #
def check_regression_anchor(anchor_rows: list[dict]) -> dict:
    """Verify the (q=0.75, nb=500, off=0, standard) config reproduces EXP-003 per stratum.

    Compares verdict + STATE ΔMDE + adaptive dogfood FPR against EXP-003's frozen result table. A
    mismatch ⇒ the sweep harness is mis-wired ⇒ the sweep is uninterpretable (fix + rerun).
    """
    if not EXP003_STRATUM_CSV.exists():
        return {"status": "MISSING_REFERENCE", "csv": str(EXP003_STRATUM_CSV)}
    ref = {(r["instrument"], r["domain"]): r
           for r in pl.read_csv(EXP003_STRATUM_CSV).to_dicts()}
    mismatches = []
    for r in anchor_rows:
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
    return {"status": "PASS" if not mismatches else "FAIL", "n_strata": len(anchor_rows),
            "n_mismatch": len(mismatches), "mismatches": mismatches}


# --------------------------------------------------------------------------- #
# Plotting (bounded inputs)
# --------------------------------------------------------------------------- #
_VERDICT_CODE = {"DET_DOMINANT": 2.0, "NOT_IMPROVED": 1.0, "FPR_BROKEN": 0.0}


def plot_qsweep_surface(rows: list[dict], save_path: Path) -> None:
    """R1: strata x q* verdict surface (cell colour = verdict; annotation = STATE ΔMDE bps)."""
    r1 = [r for r in rows if r["probe"] == "R1"]
    strata = sorted({(r["instrument"], r["domain"]) for r in r1})
    qs = sorted({r["q"] for r in r1})
    labels = [f"{i}/{d}" for i, d in strata]
    sidx = {s: k for k, s in enumerate(strata)}
    qidx = {q: k for k, q in enumerate(qs)}
    code = np.full((len(strata), len(qs)), np.nan)
    ann = np.full((len(strata), len(qs)), np.nan)
    for r in r1:
        i, j = sidx[(r["instrument"], r["domain"])], qidx[r["q"]]
        code[i, j] = _VERDICT_CODE.get(r["verdict"], np.nan)
        ann[i, j] = r["state_delta_mde"]
    sns.set_theme(style="white")
    fig, ax = plt.subplots(figsize=(7, 10))
    sns.heatmap(code, ax=ax, cmap="RdYlGn", vmin=0, vmax=2, annot=ann, fmt=".1f",
                xticklabels=[f"q*={q}" for q in qs], yticklabels=labels,
                cbar_kws={"label": "verdict (2=DET_DOMINANT,1=NOT_IMPROVED,0=FPR_BROKEN)"},
                linewidths=0.4, linecolor="lightgrey")
    ax.set_title("R1 q*-sweep: verdict surface (annot = STATE ΔMDE bps; green=DET_DOMINANT)")
    ax.set_xlabel("sub-pop quantile q* (Q_STUD_MIN = Φ⁻¹(q*) co-moves)")
    ax.set_ylabel("instrument / domain")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_bootstrap_seed_stability(rows: list[dict], save_path: Path) -> None:
    """R2: STATE ΔMDE per stratum across the (N_BOOTSTRAP x seed) corners (anchor included)."""
    corners = [r for r in rows if (r["probe"] == "R2")
               or (r["probe"] == "R1" and r["q"] == Q_STAR_BASELINE)]
    cfgs = sorted({r["config"] for r in corners})
    strata = sorted({(r["instrument"], r["domain"]) for r in corners})
    labels = [f"{i}/{d}" for i, d in strata]
    by = {(r["config"], r["instrument"], r["domain"]): r["state_delta_mde"] for r in corners}
    x = np.arange(len(strata))
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(12, 5))
    offs = np.linspace(-0.3, 0.3, len(cfgs))
    for off, cfg in zip(offs, cfgs):
        ys = [by.get((cfg, i, d), np.nan) for i, d in strata]
        ax.scatter(x + off, ys, label=cfg, s=28)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=90, fontsize=7)
    ax.set_title("R2 bootstrap/seed stability: STATE ΔMDE per stratum across corners (q*=0.75)")
    ax.set_ylabel("STATE ΔMDE = frozen − adaptive (bps)")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_skew_fpr(rows: list[dict], save_path: Path) -> None:
    """R3: adaptive dogfood FPR — baseline (standard nulls) vs skew-stressed nulls, per stratum."""
    base = {(r["instrument"], r["domain"]): r for r in rows
            if r["probe"] == "R1" and r["q"] == Q_STAR_BASELINE}
    skew = {(r["instrument"], r["domain"]): r for r in rows if r["probe"] == "R3"}
    strata = sorted(skew)
    labels = [f"{i}/{d}" for i, d in strata]
    x = np.arange(len(strata))
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.errorbar(x - 0.1, [base[s]["dogfood_fpr_adaptive"] for s in strata],
                yerr=[base[s]["dogfood_fpr_adaptive_hw"] for s in strata], fmt="o",
                label="baseline nulls", capsize=2)
    ax.errorbar(x + 0.1, [skew[s]["dogfood_fpr_adaptive"] for s in strata],
                yerr=[skew[s]["dogfood_fpr_adaptive_hw"] for s in strata], fmt="^",
                label="skew-stressed nulls", capsize=2)
    ax.axhline(FPR_CONTROL_BOUND, color="red", ls="--", lw=1, label=f"control {FPR_CONTROL_BOUND}")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=90, fontsize=7)
    ax.set_title("R3 residual skew-FPR: adaptive dogfood FPR, baseline vs skew-stressed (Wilson)")
    ax.set_ylabel("adaptive dogfood FPR")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Serialisation
# --------------------------------------------------------------------------- #
def write_results(rows: list[dict], anchor: dict) -> None:
    """Persist the per-(config,stratum) table, the regression-anchor check, and disclosure tables."""
    pl.DataFrame(rows).write_csv(RESULTS_DIR / "robustness_per_config_stratum.csv")
    (RESULTS_DIR / "regression_anchor_check.json").write_text(json.dumps(anchor, indent=2, default=str))
    ci = [{"instrument": r["instrument"], "domain": r["domain"], "n_episodes": r["n_episodes"],
           "subpop_raw_ci_halfwidth_bps": r["subpop_raw_ci_halfwidth_bps"]}
          for r in rows if "n_episodes" in r]
    if ci:
        pl.DataFrame(ci).write_csv(RESULTS_DIR / "ci_width_4h_disclosure.csv")


def summarise(rows: list[dict]) -> None:
    """Concise stdout: per-probe verdict tallies + the binding stability reads."""
    logger.info("\n=== EXP-004 E4 robustness summary ===")
    for probe in ("R1", "R2", "R3", "D-regime"):
        prows = [r for r in rows if r["probe"] == probe]
        if not prows:
            continue
        verdicts = [r["verdict"] for r in prows]
        tally = {v: verdicts.count(v) for v in sorted(set(verdicts))}
        logger.info("  %-9s %d rows | verdicts %s", probe, len(prows), tally)
    # R1 per-q DET tally + STATE ΔMDE range
    for q in Q_STAR_SWEEP:
        qr = [r for r in rows if r["probe"] == "R1" and r["q"] == q]
        det = sum(r["verdict"] == "DET_DOMINANT" for r in qr)
        ds = [r["state_delta_mde"] for r in qr if math.isfinite(r["state_delta_mde"])]
        fb = sum(r["verdict"] == "FPR_BROKEN" for r in qr)
        logger.info("    q*=%-4s DET %d/%d | FPR_BROKEN %d | STATE ΔMDE median=%.2f min=%.2f",
                    q, det, len(qr), fb, float(np.median(ds)) if ds else math.nan,
                    float(np.min(ds)) if ds else math.nan)
    fd = max((r["future_destroy_max_adaptive"] for r in rows), default=0.0)
    logger.info("  future-destroy max (adaptive, all configs): %.3f", fd)
    trip = [r for r in rows if r["tripwire_failures"]]
    if trip:
        logger.error("  LEAK-TRIPWIRE FAILURES (%d) — verdict-material, fix+rerun:", len(trip))
        for r in trip:
            logger.error("    - %s", r["tripwire_failures"])
    else:
        logger.info("  All leak tripwires held across every sweep point.")


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
    jobs_inst = [(ins, str(available[ins])) for ins in instruments if available[ins]]

    configs = build_configs()
    logger.info("running %d configs x %d instruments over %d workers",
                len(configs), len(jobs_inst), N_WORKERS)

    rows: list[dict] = []
    with ProcessPoolExecutor(max_workers=N_WORKERS) as pool:
        futures = {pool.submit(run_job, cfg, ins, path): (cfg.name, ins)
                   for cfg in configs for ins, path in jobs_inst}
        for fut in tqdm(as_completed(futures), total=len(futures), desc="config x instrument"):
            rows.extend(fut.result())

    if not rows:
        logger.error("No strata produced results — check data availability.")
        return

    anchor_rows = [r for r in rows if r["probe"] == "R1" and r["q"] == Q_STAR_BASELINE
                   and r["null_mode"] == "standard" and not r["recent_only"]]
    anchor = check_regression_anchor(anchor_rows)
    logger.info("regression anchor (q=0.75,nb=500,off=0) vs EXP-003: %s (mismatch %s/%s)",
                anchor.get("status"), anchor.get("n_mismatch"), anchor.get("n_strata"))

    write_results(rows, anchor)
    plot_qsweep_surface(rows, PLOTS_DIR / "qsweep_surface.png")
    plot_bootstrap_seed_stability(rows, PLOTS_DIR / "bootstrap_seed_stability.png")
    plot_skew_fpr(rows, PLOTS_DIR / "skew_fpr.png")
    summarise(rows)
    logger.info("results -> %s", RESULTS_DIR / "robustness_per_config_stratum.csv")
    if anchor.get("status") != "PASS":
        logger.error("REGRESSION ANCHOR NOT PASS (%s) — sweep is uninterpretable until fixed.",
                     anchor.get("status"))


if __name__ == "__main__":
    main()
