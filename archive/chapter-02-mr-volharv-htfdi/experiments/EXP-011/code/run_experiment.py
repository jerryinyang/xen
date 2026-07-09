"""
Experiment EXP-011 (E7): Referee 15m-Domain Extension — calibration + freeze-license harness.

Implements python/experiments/EXP-011/design.md (GATE: APPROVE). ANALYSIS-ONLY: synthetic position
substrates + the frozen §10.3a (`gate_stack_adaptive`) + E6 P*-gate (`gate_stack_pstar`) primitives on
aggregated 15m timebar extracts. No price->signal; generates no edge — it CALIBRATES a gate domain.
First-70% slice; dogfood on first-49% TRAIN; global holdout never loaded. 0 reads / 0 slots.

E7 adds ONE trading domain ("15m") to the frozen referee. No gate leg is added/removed/re-thresholded:
the extension is four additive DICT ROWS, injected at runtime (candidate-blind, from mechanical rules),
so the frozen module SOURCE is byte-unchanged during the battery (== E5/E6 hashes):
  referee_calibration.DOMAIN_SPECS["15m"]     = DomainSpec("15m", 15, 0.90, N15, S15)
  referee_calibration.MATERIALITY_BPS["15m"]  = M15
  referee_adaptive.ROUND_TRIP_COST_BPS_17[i]["15m"] = <inherit i's 1h round-trip>   (per-trade cost)
  incremental_referee.EPISODE_LENGTHS["15m"]  = EP15
(the permanent source edit + freeze_manifest are emitted ONLY after the battery LICENSES the freeze.)

Two passes, per-stratum binding (L-03):
  ANCHOR (16x{1h,4h}=32) — with the 15m rows injected, the §10.3a 3-arm DET must reproduce EXP-003
    bit-for-bit AND the E6 P*-gate Arm-R reduction identity must hold 32/32 AND frozen source hashes
    unchanged. Proof that "adds a domain, changes nothing else."
  15m BATTERY (16 strata x sensitivity band) — the E2/E3a battery at domain="15m": per-stratum dogfood
    FPR (4 null families + skew guard, Wilson + MIN_FPR_PASSES=2/2a rule), MDE per shape (DENSE +
    the §10.3a STATE/SPARSE recovery), future-destroy collapse, no-plant guard, P*-gate Arm-R-15m
    identity. FREEZE LICENSED iff FPR controlled + finite power + tripwires hold + verdict invariant
    across the band.

Constants are the mechanical priors (design "Derivation rule"): M15=0.75 (0.1936*sqrt(15), reproduces
frozen 1h=1.5/4h=3.0), N15=90 / S15=25 / EP15=17 (log-period interpolation between 5m and 1h). The band
is the binding calibration — the prior is the anchor, not an assumed pass.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
import seaborn as sns
from tqdm.auto import tqdm

import xen.referee_adaptive as ra
import xen.referee_calibration as rc
import xen.incremental_referee as ir
from xen.bar_aggregator import aggregate_ohlc
from xen.referee_adaptive import (
    ROUND_TRIP_COST_BPS_17,
    adaptive_cost_bps_for,
    adaptive_row,
    gate_stack_adaptive,
    gate_stack_core_costfn,
    next_open_to_open_returns_from_bars,
    strategy_return_bps_turnover,
)
from xen.referee_calibration import (
    DomainSpec,
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
from xen.referee_pstar import gate_stack_pstar_reduces_to_adaptive
from xen.referee_substrate import (
    dense_planted,
    persistent_positions,
    sparse_positions,
    state_dependent_planted,
    state_positions,
    tail_only_planted,
)

logger = logging.getLogger("EXP-011")

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
DATA_DIR = Path("data")
EXP_DIR = Path("python/experiments/EXP-011")
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"
EXP003_STRATUM_CSV = Path("python/experiments/EXP-003/results/det_dominance_per_stratum.csv")
FROZEN_MODULES = (
    Path("python/src/xen/referee_adaptive.py"),
    Path("python/src/xen/referee_calibration.py"),
    Path("python/src/xen/referee_pstar.py"),
    Path("python/src/xen/incremental_referee.py"),
)

ANALYSIS_FRACTION = 0.70
TRAIN_FRACTION = 0.70          # dogfood restricted to first-49% TRAIN = int(int(N*0.7)*0.7)
ERA_GLOB = "20210602_*"
PERIOD_MINUTES = {"15m": 15, "1h": 60, "4h": 240}
DOMAIN_MIN_COVERAGE = 0.90

ALPHA = 0.05
N_BOOTSTRAP = 500
N_NULL = 80
N_PLANT = 20
POWER_TARGET = 0.50
FPR_CONTROL_BOUND = 2 * ALPHA
MIN_FPR_PASSES = 2             # E4/E5 candidate-blind freeze-FPR rule (a single 1/N artifact != break)
SKEW_LAMBDA = 1.0             # E4 R3 skew-null stress (predeclared, not tuned)

SHAPES: tuple[str, ...] = ("dense", "tail", "sparse", "state")
ARMS: tuple[str, ...] = ("frozen", "frozen_amortized", "adaptive")
ANCHOR_DOMAINS: tuple[str, ...] = ("1h", "4h")
NEW_DOMAIN = "15m"
N_WORKERS = min(os.cpu_count() or 1, 16)

# --- Mechanical 15m constant priors (design "Derivation rule"; candidate-blind) --------------------- #
M15_PRIOR = round(0.19365 * math.sqrt(15.0), 2)   # sqrt-period materiality = 0.75 (reproduces 1h/4h)
N15_PRIOR = 90                                     # log-interp(5m 120, 1h 60) ~= 93.5 -> 90
S15_PRIOR = 25                                     # log-interp(5m 30,  1h 20) ~= 25.6 -> 25
EP15_DERIVED = 17                                  # log-interp(5m 24,  1h 8)  ~= 16.9 -> 17 (substrate L)


# --------------------------------------------------------------------------- #
# Types — sensitivity-band configs
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class BandConfig:
    """One 15m calibration point. `role="prior"` is the anchor; band members vary one knob (OAT)."""
    name: str
    role: str                  # "prior" | "materiality" | "min_effective_n" | "min_state_count"
    materiality: float
    min_effective_n: int
    min_state_count: int


def build_band_configs() -> list[BandConfig]:
    """Prior + one-at-a-time sensitivity band (design: M15 {0.5,0.75,1.0}, N15 {75,90,105}, S15 {20,25,30})."""
    cfgs = [BandConfig("prior", "prior", M15_PRIOR, N15_PRIOR, S15_PRIOR)]
    for m in (0.5, 1.0):
        cfgs.append(BandConfig(f"M{m}", "materiality", m, N15_PRIOR, S15_PRIOR))
    for n in (75, 105):
        cfgs.append(BandConfig(f"N{n}", "min_effective_n", M15_PRIOR, n, S15_PRIOR))
    for s in (20, 30):
        cfgs.append(BandConfig(f"S{s}", "min_state_count", M15_PRIOR, s, S15_PRIOR))
    return cfgs


# --------------------------------------------------------------------------- #
# Candidate-blind 15m injection (runtime dict rows; frozen SOURCE untouched)
# --------------------------------------------------------------------------- #
def inject_15m(materiality: float, min_effective_n: int, min_state_count: int) -> None:
    """Add the four additive 15m domain rows to the imported (mutable) frozen dicts, in-process.

    Mirrors the E4 candidate-blind knob-injection pattern (mutate module state per config). Only ADDS a
    "15m" key to each dict; every 1h/4h/5m entry is left byte-identical, so the frozen gate LOGIC and
    the on-disk module SOURCE are unchanged (asserted by the byte-freeze check). No CF-MR-003 input is
    ever read — the constants come from the mechanical priors / band only.
    """
    rc.DOMAIN_SPECS[NEW_DOMAIN] = DomainSpec(NEW_DOMAIN, 15, DOMAIN_MIN_COVERAGE,
                                             min_effective_n, min_state_count)
    rc.MATERIALITY_BPS[NEW_DOMAIN] = materiality
    ir.EPISODE_LENGTHS[NEW_DOMAIN] = EP15_DERIVED
    for inst in ROUND_TRIP_COST_BPS_17:                       # per-trade round-trip is domain-invariant
        ROUND_TRIP_COST_BPS_17[inst][NEW_DOMAIN] = ROUND_TRIP_COST_BPS_17[inst]["1h"]


# --------------------------------------------------------------------------- #
# I/O helpers
# --------------------------------------------------------------------------- #
def era_file_for(instrument: str) -> Path | None:
    """Newest 5-year-era 1-minute file for an instrument, or None if absent."""
    matches = sorted(DATA_DIR.glob(f"timebars/timebars_{instrument.lower()}_{ERA_GLOB}.parquet"))
    return matches[-1] if matches else None


def load_slice_minutes(path: Path, *, train_only: bool) -> pl.DataFrame:
    """First-70% analysis (or first-49% TRAIN) CloseTime-ordered 1-minute slice. Holdout never collected."""
    scan = pl.scan_parquet(path).sort("CloseTime")
    total = int(scan.select(pl.len()).collect().item())
    cutoff = int(total * ANALYSIS_FRACTION)
    if train_only:
        cutoff = int(cutoff * TRAIN_FRACTION)
    return scan.slice(0, cutoff).collect()


def build_domain(minutes: pl.DataFrame, domain: str) -> tuple[np.ndarray, pl.DataFrame]:
    """Open-to-open <=t-1 returns + aligned fenced domain frame (real OHLC for the dogfood signals)."""
    dom = aggregate_ohlc(minutes, period_minutes=PERIOD_MINUTES[domain], min_coverage=DOMAIN_MIN_COVERAGE)
    dom = dom.filter(pl.col("CloseTime") <= minutes.get_column("CloseTime").max())
    return next_open_to_open_returns_from_bars(dom)


def module_hashes() -> dict[str, str]:
    """SHA-256 of the frozen referee modules (must be unchanged across the battery)."""
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in FROZEN_MODULES}


# --------------------------------------------------------------------------- #
# Pure helpers — substrate, nulls, gate arms (mirror EXP-003/004 seeds exactly)
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
    """Right-skew, ~mean-0 elementwise marginal transform of a no-edge null series (E4 R3 stress)."""
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
                cost_bps: float, seed: int) -> bool:
    """True iff the named gate arm PASSES one draw (frozen legs unchanged; adaptive = §10.3a; E3a seeds)."""
    if arm == "adaptive":
        core = gate_stack_adaptive(returns, positions, domain=domain, cost_bps=cost_bps,
                                   n_bootstrap=N_BOOTSTRAP, seed=seed)
        return bool(adaptive_row(core, alpha=ALPHA)["passed"])
    fn = strategy_return_bps_turnover if arm == "frozen_amortized" else strategy_return_bps
    core = gate_stack_core_costfn(returns, positions, domain=domain, cost_bps=cost_bps,
                                  n_bootstrap=N_BOOTSTRAP, seed=seed, strategy_fn=fn)
    return bool(gate_stack_row(core, alpha=ALPHA)["passed"])


def detection_rate(arm: str, shape: str, returns: np.ndarray, *, domain: str, episode_length: int,
                   cost_bps: float, net_edge_bps: float) -> float:
    """Fraction of planted draws the arm PASSES (early-stop at the POWER_TARGET boundary; MDE bit-exact)."""
    need = math.ceil(POWER_TARGET * N_PLANT)
    passes = 0
    for k in range(N_PLANT):
        planted, pos = make_shape(shape, returns, net_edge_bps=net_edge_bps, cost_bps=cost_bps,
                                  episode_length=episode_length, seed=6000 + k)
        passes += gate_passes(arm, planted, pos, domain=domain, cost_bps=cost_bps, seed=7000 + k)
        if passes >= need or passes + (N_PLANT - (k + 1)) < need:
            break
    return passes / N_PLANT


def mde_of(arm: str, shape: str, returns: np.ndarray, *, domain: str, episode_length: int,
           cost_bps: float) -> float:
    """DETECTED_FLOOR MDE for an arm x shape (inf = UNPOWERED)."""
    for edge in EDGE_GRID_BPS:
        if edge <= 0.0:
            continue
        if detection_rate(arm, shape, returns, domain=domain, episode_length=episode_length,
                          cost_bps=cost_bps, net_edge_bps=edge) >= POWER_TARGET:
            return edge
    return math.inf


def no_plant_passrate(arm: str, shape: str, returns: np.ndarray, *, domain: str,
                      episode_length: int, cost_bps: float) -> float:
    """No-real-edge guard: arm PASS rate on the shape's positions with NO planted drift."""
    passes = 0
    for k in range(N_PLANT):
        _, pos = make_shape(shape, returns, net_edge_bps=0.0, cost_bps=cost_bps,
                            episode_length=episode_length, seed=6000 + k)
        passes += gate_passes(arm, returns, pos, domain=domain, cost_bps=cost_bps, seed=7000 + k)
    return passes / N_PLANT


def future_destroyed_passrate(arm: str, shape: str, returns: np.ndarray, *, domain: str,
                              episode_length: int, cost_bps: float, net_edge_bps: float) -> float:
    """Leak control: plant edge, block-permute returns (destroy alignment) -> must collapse to FPR."""
    passes = 0
    for k in range(N_PLANT):
        planted, pos = make_shape(shape, returns, net_edge_bps=net_edge_bps, cost_bps=cost_bps,
                                  episode_length=episode_length, seed=6000 + k)
        destroyed = permuted_returns(planted, seed=8000 + k)
        passes += gate_passes(arm, destroyed, pos, domain=domain, cost_bps=cost_bps, seed=7000 + k)
    return passes / N_PLANT


def dogfood_fpr(arm: str, returns: np.ndarray, aligned: pl.DataFrame, *, domain: str,
                episode_length: int, cost_bps: float, skew: bool = False
                ) -> tuple[float, float, int, int]:
    """Per-stratum FPR for an arm over 4 null families (block-permute, reblock-random, Donchian, MA).

    Mirrors EXP-003 exactly at skew=False. `skew=True` applies the E4 right-skew marginal transform to
    each null RETURNS series (positions/signals held fixed) — a genuine no-edge stress. Returns
    ``(rate, wilson_halfwidth, draws, passes)`` (passes threaded out for the Wilson-resolved verdict).
    """
    n = len(returns)
    base = skew_returns(returns, lam=SKEW_LAMBDA) if skew else returns
    passes, draws = 0, 0
    for k in range(N_NULL):
        pr = permuted_returns(returns, seed=1000 + k)
        if skew:
            pr = skew_returns(pr, lam=SKEW_LAMBDA)
        passes += gate_passes(arm, pr, persistent_positions(n, episode_length, 2000 + k),
                              domain=domain, cost_bps=cost_bps, seed=3000 + k)
        passes += gate_passes(arm, base, reblocked_random_positions(n, episode_length, 4000 + k),
                              domain=domain, cost_bps=cost_bps, seed=5000 + k)
        draws += 2
    high = aligned.get_column("High").to_numpy()
    low = aligned.get_column("Low").to_numpy()
    close = aligned.get_column("Close").to_numpy()
    don = lag_open_to_open(donchian_breakout_positions(high, low, close, lookback=20))
    ma = lag_open_to_open(ma_crossover_positions(close, fast=20, slow=50))
    for sig, sd in ((don, 9001), (ma, 9002)):
        passes += gate_passes(arm, base, sig, domain=domain, cost_bps=cost_bps, seed=sd)
        draws += 1
    _, lo, hi = wilson_interval(passes, draws)
    return passes / draws, (hi - lo) / 2.0, draws, passes


def pstar_identity(returns: np.ndarray, *, domain: str, cost_bps: float) -> bool:
    """E6 Arm-R: the P*-gate reduces bit-identically to §10.3a when realized := turnover series."""
    pos = persistent_positions(len(returns), ir.EPISODE_LENGTHS[domain], seed=101)
    return bool(gate_stack_pstar_reduces_to_adaptive(
        returns, pos, domain=domain, cost_bps=cost_bps, n_bootstrap=N_BOOTSTRAP, seed=202))


# --------------------------------------------------------------------------- #
# Per-stratum orchestration
# --------------------------------------------------------------------------- #
def classify_stratum(mde: dict, dogfood: dict) -> str:
    """DET_DOMINANT / NOT_IMPROVED / FPR_BROKEN (binding, L-03; E3a/E4 Wilson-resolved rule)."""
    _, _, draws_a, passes_a = dogfood["adaptive"]
    _, adaptive_lo, _ = wilson_interval(passes_a, draws_a)
    if adaptive_lo > dogfood["frozen"][0]:
        return "FPR_BROKEN"
    no_regression = all(mde[("adaptive", s)] <= mde[("frozen", s)] for s in SHAPES)
    strict = any(mde[("adaptive", s)] < mde[("frozen", s)] for s in SHAPES)
    return "DET_DOMINANT" if (no_regression and strict) else "NOT_IMPROVED"


def fpr_controlled(dogfood_adaptive: tuple[float, float, int, int]) -> bool:
    """E4/E5 freeze-FPR rule: controlled unless >=MIN_FPR_PASSES passes AND rate resolved above 2a."""
    rate, hw, _, passes = dogfood_adaptive
    if passes < MIN_FPR_PASSES:
        return True
    return (rate - hw) <= FPR_CONTROL_BOUND


def run_stratum(returns: np.ndarray, aligned: pl.DataFrame, instrument: str, domain: str,
                cfg: BandConfig) -> dict:
    """One (config, instrument, domain): 3-arm DET + FPR (+skew) + tripwires + P*-identity."""
    L = ir.EPISODE_LENGTHS[domain]
    cost = adaptive_cost_bps_for(instrument, domain)
    failures: list[str] = []

    dogfood = {arm: dogfood_fpr(arm, returns, aligned, domain=domain, episode_length=L, cost_bps=cost)
               for arm in ARMS}
    skew_adaptive = dogfood_fpr("adaptive", returns, aligned, domain=domain, episode_length=L,
                                cost_bps=cost, skew=True)
    mde: dict = {}
    fd_max = 0.0
    for shape in SHAPES:
        for arm in ARMS:
            mde[(arm, shape)] = mde_of(arm, shape, returns, domain=domain, episode_length=L, cost_bps=cost)
        npr = no_plant_passrate("adaptive", shape, returns, domain=domain, episode_length=L, cost_bps=cost)
        guard = max(dogfood["adaptive"][0] + 2 * dogfood["adaptive"][1], FPR_CONTROL_BOUND)
        if npr > guard:
            failures.append(f"{instrument}/{domain}/{shape}: no-plant(adaptive) {npr:.3f} > guard")
        levels = sorted({lvl for lvl in (mde[("adaptive", shape)], EDGE_GRID_BPS[-1]) if math.isfinite(lvl)})
        for lvl in levels:
            rate = future_destroyed_passrate("adaptive", shape, returns, domain=domain,
                                             episode_length=L, cost_bps=cost, net_edge_bps=lvl)
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

    return {
        "config": cfg.name, "role": cfg.role, "instrument": instrument, "domain": domain,
        "materiality": rc.MATERIALITY_BPS[domain], "min_effective_n": rc.DOMAIN_SPECS[domain].min_effective_n,
        "min_state_count": rc.DOMAIN_SPECS[domain].min_state_count, "cost_bps": cost, "episode_length": L,
        "verdict": classify_stratum(mde, dogfood),
        "fpr_controlled": fpr_controlled(dogfood["adaptive"]),
        "state_delta_mde": delta("state"), "sparse_delta_mde": delta("sparse"),
        **{f"mde_adaptive_{s}": mde[("adaptive", s)] for s in SHAPES},
        **{f"mde_frozen_{s}": mde[("frozen", s)] for s in SHAPES},
        "dense_powered": math.isfinite(mde[("adaptive", "dense")]),
        "dogfood_fpr_frozen": dogfood["frozen"][0], "dogfood_fpr_adaptive": dogfood["adaptive"][0],
        "dogfood_fpr_adaptive_hw": dogfood["adaptive"][1], "dogfood_passes_adaptive": dogfood["adaptive"][3],
        "dogfood_draws_adaptive": dogfood["adaptive"][2],
        "skew_fpr_adaptive": skew_adaptive[0], "skew_fpr_adaptive_hw": skew_adaptive[1],
        "skew_passes_adaptive": skew_adaptive[3], "future_destroy_max_adaptive": fd_max,
        "pstar_identity": pstar_identity(returns, domain=domain, cost_bps=cost),
        "tripwire_failures": "; ".join(failures),
    }


def run_job(task: tuple[str, BandConfig, str, str]) -> list[dict]:
    """Worker: inject the config's 15m rows, run the requested domains for one instrument.

    Picklable + seed-deterministic. mode="anchor" -> {1h,4h} under the PRIOR injection (proves the 15m
    rows do not perturb 1h/4h); mode="15m" -> the 15m battery under the band config. Dogfood uses the
    first-49% TRAIN slice; MDE/tripwire substrate uses the first-70% analysis returns (no holdout).
    """
    mode, cfg, instrument, path_str = task
    inject_15m(cfg.materiality, cfg.min_effective_n, cfg.min_state_count)
    domains = ANCHOR_DOMAINS if mode == "anchor" else (NEW_DOMAIN,)
    minutes = load_slice_minutes(Path(path_str), train_only=(mode == "15m"))
    out: list[dict] = []
    for domain in domains:
        returns, aligned = build_domain(minutes, domain)
        if len(returns) < 200:
            continue
        out.append(run_stratum(returns, aligned, instrument, domain, cfg))
    return out


# --------------------------------------------------------------------------- #
# Regression anchor + license adjudication
# --------------------------------------------------------------------------- #
def check_regression_anchor(anchor_rows: list[dict]) -> dict:
    """Verify the 1h/4h anchor reproduces EXP-003 per stratum (verdict + STATE ΔMDE + adaptive FPR)."""
    if not EXP003_STRATUM_CSV.exists():
        return {"status": "MISSING_REFERENCE", "csv": str(EXP003_STRATUM_CSV)}
    ref = {(r["instrument"], r["domain"]): r for r in pl.read_csv(EXP003_STRATUM_CSV).to_dicts()}
    mism = []
    for r in anchor_rows:
        key = (r["instrument"], r["domain"])
        if key not in ref:
            mism.append({"stratum": "/".join(key), "issue": "absent in EXP-003"})
            continue
        e = ref[key]
        d_now, d_ref = r["state_delta_mde"], e.get("state_delta_mde")
        same_d = (math.isnan(d_now) and (d_ref is None or (isinstance(d_ref, float) and math.isnan(d_ref)))) \
            or (isinstance(d_ref, (int, float)) and math.isfinite(d_now) and abs(d_now - float(d_ref)) < 1e-9)
        same_fpr = abs(r["dogfood_fpr_adaptive"] - float(e["dogfood_fpr_adaptive"])) < 1e-9
        if not (r["verdict"] == e["verdict"] and same_d and same_fpr and r["pstar_identity"]):
            mism.append({"stratum": "/".join(key), "verdict": [r["verdict"], e["verdict"]],
                         "state_delta": [d_now, d_ref], "pstar_identity": r["pstar_identity"]})
    n_pstar = sum(r["pstar_identity"] for r in anchor_rows)
    return {"status": "PASS" if not mism else "FAIL", "n_strata": len(anchor_rows),
            "n_mismatch": len(mism), "pstar_identity_count": n_pstar, "mismatches": mism}


def adjudicate_license(anchor: dict, rows_15m: list[dict]) -> dict:
    """FREEZE_LICENSED / RANGE_BOUNDED / FREEZE_NOT_LICENSED / INCONCLUSIVE (design interpretation)."""
    prior = [r for r in rows_15m if r["role"] == "prior"]
    band = [r for r in rows_15m if r["role"] != "prior"]
    trip = [r for r in rows_15m if r["tripwire_failures"]]
    fd_max = max((r["future_destroy_max_adaptive"] for r in rows_15m), default=0.0)
    prior_fpr_ok = all(r["fpr_controlled"] for r in prior)
    prior_dense_ok = all(r["dense_powered"] for r in prior)
    prior_recovery = sum(math.isfinite(r["mde_adaptive_state"]) or math.isfinite(r["mde_adaptive_sparse"])
                         for r in prior)
    # verdict invariance: does any band member flip fpr_controlled / dense_powered vs the prior?
    prior_ok_cells = {(r["instrument"], r["domain"]): (r["fpr_controlled"] and r["dense_powered"])
                      for r in prior}
    band_flips = [r for r in band if not (r["fpr_controlled"] and r["dense_powered"])
                  and prior_ok_cells.get((r["instrument"], r["domain"]), False)]

    anchor_ok = anchor.get("status") == "PASS"
    tripwires_ok = not trip and fd_max <= FPR_CONTROL_BOUND
    prior_ok = prior_fpr_ok and prior_dense_ok and prior_recovery > 0

    if not anchor_ok or not tripwires_ok or not prior_fpr_ok or not prior_dense_ok:
        verdict = "FREEZE_NOT_LICENSED"
    elif band_flips:
        verdict = "RANGE_BOUNDED"
    elif prior_ok:
        verdict = "FREEZE_LICENSED"
    else:
        verdict = "INCONCLUSIVE"
    return {
        "verdict": verdict, "anchor_status": anchor.get("status"),
        "anchor_pstar_identity": anchor.get("pstar_identity_count"),
        "prior_fpr_controlled": prior_fpr_ok, "prior_dense_powered": prior_dense_ok,
        "prior_recovery_strata": prior_recovery, "prior_strata": len(prior),
        "band_flip_strata": ["/".join((r["instrument"], r["config"])) for r in band_flips],
        "pstar_identity_15m": sum(r["pstar_identity"] for r in rows_15m), "n_15m_rows": len(rows_15m),
        "future_destroy_max": fd_max, "tripwire_failures": [r["tripwire_failures"] for r in trip],
        "min_fpr_passes_rule": MIN_FPR_PASSES,
        "constants": {"materiality_bps": M15_PRIOR, "min_effective_n": N15_PRIOR,
                      "min_state_count": S15_PRIOR, "episode_length": EP15_DERIVED,
                      "min_coverage": DOMAIN_MIN_COVERAGE, "cost_rule": "inherit_per_instrument_1h"},
    }


# --------------------------------------------------------------------------- #
# Plotting (bounded inputs) — design's 3 plots
# --------------------------------------------------------------------------- #
def plot_recovery_map(rows_prior: list[dict], save_path: Path) -> None:
    """15m DET map: strata x shape ΔMDE (frozen - adaptive); >0 = §10.3a recovers at 15m."""
    strata = sorted({r["instrument"] for r in rows_prior})
    mat = np.full((len(strata), len(SHAPES)), np.nan)
    idx = {s: k for k, s in enumerate(strata)}
    for r in rows_prior:
        for j, s in enumerate(SHAPES):
            f, a = r[f"mde_frozen_{s}"], r[f"mde_adaptive_{s}"]
            mat[idx[r["instrument"]], j] = (f - a) if math.isfinite(f) and math.isfinite(a) else np.nan
    sns.set_theme(style="white")
    fig, ax = plt.subplots(figsize=(7, 9))
    sns.heatmap(mat, ax=ax, cmap="RdBu_r", center=0, annot=True, fmt=".1f", xticklabels=list(SHAPES),
                yticklabels=strata, mask=np.isnan(mat), linewidths=0.4, linecolor="lightgrey",
                cbar_kws={"label": "ΔMDE = frozen - adaptive (bps)"})
    ax.set_title("15m recovery map: ΔMDE frozen - adaptive (>0 = §10.3a recovers; blank = UNPOWERED)")
    ax.set_xlabel("edge shape"); ax.set_ylabel("instrument (15m)")
    fig.tight_layout(); fig.savefig(save_path, dpi=150, bbox_inches="tight"); plt.close(fig)


def plot_fpr_by_stratum(rows_prior: list[dict], save_path: Path) -> None:
    """15m dogfood + skew FPR per stratum (Wilson bars, control line)."""
    labels = [r["instrument"] for r in rows_prior]
    x = np.arange(len(labels))
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.errorbar(x - 0.1, [r["dogfood_fpr_adaptive"] for r in rows_prior],
                yerr=[r["dogfood_fpr_adaptive_hw"] for r in rows_prior], fmt="o", label="dogfood (4 nulls)",
                capsize=2)
    ax.errorbar(x + 0.1, [r["skew_fpr_adaptive"] for r in rows_prior],
                yerr=[r["skew_fpr_adaptive_hw"] for r in rows_prior], fmt="^", label="skew-stressed",
                capsize=2)
    ax.axhline(FPR_CONTROL_BOUND, color="red", ls="--", lw=1, label=f"control {FPR_CONTROL_BOUND}")
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=90, fontsize=7)
    ax.set_title("15m adaptive dogfood FPR per stratum (Wilson; control = 2α)")
    ax.set_ylabel("FPR"); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(save_path, dpi=150, bbox_inches="tight"); plt.close(fig)


def plot_band_surface(rows_15m: list[dict], save_path: Path) -> None:
    """Sensitivity band: per-config count of FPR-controlled ∧ DENSE-powered strata (verdict invariance)."""
    configs = sorted({r["config"] for r in rows_15m}, key=lambda c: (c != "prior", c))
    ok = [sum(r["fpr_controlled"] and r["dense_powered"] for r in rows_15m if r["config"] == c)
          for c in configs]
    tot = [sum(1 for r in rows_15m if r["config"] == c) for c in configs]
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(configs, ok, color=["#2c7" if c == "prior" else "#59d" for c in configs])
    for i, (o, t) in enumerate(zip(ok, tot)):
        ax.text(i, o + 0.1, f"{o}/{t}", ha="center", fontsize=8)
    ax.set_title("15m sensitivity band: FPR-controlled and DENSE-powered strata per config")
    ax.set_ylabel("strata"); ax.set_xlabel("band config (prior = anchor)")
    plt.xticks(rotation=45, ha="right", fontsize=8)
    fig.tight_layout(); fig.savefig(save_path, dpi=150, bbox_inches="tight"); plt.close(fig)


# --------------------------------------------------------------------------- #
# Serialisation
# --------------------------------------------------------------------------- #
def write_results(anchor_rows: list[dict], rows_15m: list[dict], anchor: dict, license_: dict,
                  hashes_before: dict, hashes_after: dict) -> None:
    """Persist per-stratum tables, regression anchor, license verdict, byte-freeze record."""
    flat = ["config", "role", "instrument", "domain", "materiality", "min_effective_n", "min_state_count",
            "cost_bps", "verdict", "fpr_controlled", "dense_powered", "state_delta_mde", "sparse_delta_mde",
            "dogfood_fpr_adaptive", "skew_fpr_adaptive", "future_destroy_max_adaptive", "pstar_identity",
            "tripwire_failures"]
    pl.DataFrame([{c: r[c] for c in flat} for r in rows_15m]).write_csv(RESULTS_DIR / "battery_15m.csv")
    pl.DataFrame([{c: r.get(c) for c in flat} for r in anchor_rows]).write_csv(
        RESULTS_DIR / "regression_anchor.csv")
    (RESULTS_DIR / "battery_15m_full.json").write_text(json.dumps(rows_15m, indent=2, default=str))
    (RESULTS_DIR / "regression_anchor_check.json").write_text(json.dumps(anchor, indent=2, default=str))
    (RESULTS_DIR / "license_verdict.json").write_text(json.dumps(license_, indent=2, default=str))
    (RESULTS_DIR / "byte_freeze_check.json").write_text(json.dumps(
        {"frozen_modules_before": hashes_before, "frozen_modules_after": hashes_after,
         "unchanged": hashes_before == hashes_after}, indent=2))


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    smoke = "--smoke" in sys.argv

    hashes_before = module_hashes()
    instruments = sorted(ROUND_TRIP_COST_BPS_17)
    available = {ins: era_file_for(ins) for ins in instruments}
    missing = [ins for ins, p in available.items() if p is None]
    if missing:
        logger.info("SKIP (no 5-year-era file): %s", ", ".join(missing))
    inst_jobs = [(ins, str(available[ins])) for ins in instruments if available[ins]]
    if smoke:
        inst_jobs = inst_jobs[:2]
        logger.info("SMOKE: %d instruments", len(inst_jobs))

    prior = build_band_configs()[0]
    band_cfgs = build_band_configs() if not smoke else build_band_configs()[:1]
    tasks = [("anchor", prior, ins, p) for ins, p in inst_jobs]
    tasks += [("15m", cfg, ins, p) for cfg in band_cfgs for ins, p in inst_jobs]
    logger.info("running %d tasks (anchor + %d band configs x %d instruments) over %d workers",
                len(tasks), len(band_cfgs), len(inst_jobs), N_WORKERS)

    anchor_rows: list[dict] = []
    rows_15m: list[dict] = []
    with ProcessPoolExecutor(max_workers=N_WORKERS) as pool:
        futures = {pool.submit(run_job, t): t for t in tasks}
        for fut in tqdm(as_completed(futures), total=len(futures), desc="tasks"):
            for r in fut.result():
                (anchor_rows if r["domain"] in ANCHOR_DOMAINS else rows_15m).append(r)

    if not rows_15m:
        logger.error("No 15m strata produced results — check data availability.")
        return

    anchor = check_regression_anchor(anchor_rows)
    license_ = adjudicate_license(anchor, rows_15m)
    hashes_after = module_hashes()

    write_results(anchor_rows, rows_15m, anchor, license_, hashes_before, hashes_after)
    prior_rows = [r for r in rows_15m if r["role"] == "prior"]
    plot_recovery_map(prior_rows, PLOTS_DIR / "recovery_map_15m.png")
    plot_fpr_by_stratum(prior_rows, PLOTS_DIR / "fpr_by_stratum_15m.png")
    plot_band_surface(rows_15m, PLOTS_DIR / "band_surface_15m.png")

    logger.info("\n=== EXP-011 E7 summary ===")
    logger.info("regression anchor vs EXP-003: %s (mismatch %s/%s; P*-identity %s/%s)",
                anchor.get("status"), anchor.get("n_mismatch"), anchor.get("n_strata"),
                anchor.get("pstar_identity_count"), anchor.get("n_strata"))
    logger.info("frozen module SOURCE unchanged during battery: %s", hashes_before == hashes_after)
    logger.info("15m prior: %d strata | FPR-controlled %d | DENSE-powered %d | recovery %d",
                len(prior_rows), sum(r["fpr_controlled"] for r in prior_rows),
                sum(r["dense_powered"] for r in prior_rows), license_["prior_recovery_strata"])
    logger.info("15m future-destroy max (adaptive): %.3f | P*-identity %d/%d",
                license_["future_destroy_max"], license_["pstar_identity_15m"], license_["n_15m_rows"])
    logger.info("LICENSE VERDICT: %s", license_["verdict"])
    if license_["tripwire_failures"]:
        logger.error("LEAK-TRIPWIRE FAILURES — verdict-material, fix+rerun:")
        for t in license_["tripwire_failures"]:
            logger.error("  - %s", t)
    if hashes_before != hashes_after:
        logger.error("FROZEN MODULE SOURCE CHANGED during battery — byte-freeze VIOLATED.")
    logger.info("results -> %s", RESULTS_DIR / "license_verdict.json")
    logger.info("NOTE: freeze mechanics (source edits + freeze_manifest.json) are emitted by "
                "apply_freeze.py ONLY after LICENSE VERDICT == FREEZE_LICENSED.")


if __name__ == "__main__":
    main()
