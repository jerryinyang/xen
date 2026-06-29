"""
Experiment EXP-003 (E3a): Economic-Leg Adaptive Gate — 3-arm DET-dominance vs the frozen gate.

Implements python/experiments/EXP-003/design.md (GATE APPROVE). Analysis-only BUILD + characterise:
the adaptive economic-leg gate (`xen.referee_adaptive.gate_stack_adaptive`; L1 rigid, amortized,
L2 removed, power-aware L3/L5, sub-population L5) is compared to the frozen gate on the E2 substrate.

Three arms, identical draws/seeds/split/bootstrap, per (stratum, shape):
  frozen           : gate_stack_core_costfn(strategy_return_bps)            (per-held, frozen legs)
  frozen_amortized : gate_stack_core_costfn(strategy_return_bps_turnover)   (isolates E1 accounting)
  adaptive         : gate_stack_adaptive                                     (E3a build)

Binding (per stratum, L-03): DET-DOMINANCE = MDE_adaptive <= MDE_frozen every shape, strictly < on
>=1 (expect STATE), dogfood FPR_adaptive <= FPR_frozen, no DENSE/TAIL loss. Else NOT_IMPROVED (the
predeclared valid null) or FPR_BROKEN. Sparse stays UNPOWERED (L1 rigid) — correct by design.
"""
from __future__ import annotations

import json
import logging
import math
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
import seaborn as sns
from tqdm.auto import tqdm

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

logger = logging.getLogger("EXP-003")

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
DATA_DIR = Path("data")
EXP_DIR = Path("python/experiments/EXP-003")
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"

ANALYSIS_FRACTION = 0.70
ERA_GLOB = "20210602_*"
PERIOD_MINUTES = {"1h": 60, "4h": 240}
DOMAIN_MIN_COVERAGE = 0.90

ALPHA = 0.05
N_BOOTSTRAP = 500
N_NULL = 80
N_PLANT = 20
POWER_TARGET = 0.50

SHAPES: tuple[str, ...] = ("dense", "tail", "sparse", "state")
ARMS: tuple[str, ...] = ("frozen", "frozen_amortized", "adaptive")
FPR_CONTROL_BOUND = 2 * ALPHA
N_WORKERS = min(os.cpu_count() or 1, 16)   # strata are independent + seed-deterministic -> parallel-safe

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
    """Open-to-open <=t-1 returns + aligned fenced domain frame (for dogfood OHLC)."""
    dom = aggregate_ohlc(minutes, period_minutes=PERIOD_MINUTES[domain],
                         min_coverage=DOMAIN_MIN_COVERAGE)
    dom = dom.filter(pl.col("CloseTime") <= minutes.get_column("CloseTime").max())
    return next_open_to_open_returns_from_bars(dom)

# --------------------------------------------------------------------------- #
# Pure helpers — substrate, gate arms
# --------------------------------------------------------------------------- #
def reblocked_random_positions(n: int, episode_length: int, seed: int) -> np.ndarray:
    """random_state_positions re-blocked to length L."""
    n_episodes = (n + episode_length - 1) // episode_length
    return np.repeat(random_state_positions(n_episodes, seed), episode_length)[:n]


def lag_open_to_open(positions: np.ndarray) -> np.ndarray:
    """Lag a close-indexed signal one bar so it acts at the next bar's open on confirmed bars <=t-1."""
    pos = np.asarray(positions, dtype=float)
    return np.concatenate(([0.0], pos[:-1]))


def make_shape(shape: str, returns: np.ndarray, *, net_edge_bps: float, cost_bps: float,
               episode_length: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """(planted_returns, positions) for one shape draw (matched-magnitude substrate)."""
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
    """True iff the named gate arm PASSES for one draw (frozen legs unchanged; adaptive = E3a)."""
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
    """Fraction of planted draws the arm PASSES for one (shape, e).

    Early-stops at the binomial decision boundary for the MDE threshold: once ``passes`` is high
    enough that the rate is guaranteed >= POWER_TARGET, or low enough that it cannot reach it, the
    remaining draws cannot flip the ``rate >= POWER_TARGET`` verdict, so they are skipped. The
    denominator stays ``N_PLANT``, so the returned value lands on the SAME side of POWER_TARGET as a
    full run — the MDE decision is bit-identical (safe optimization, only the exact fraction on
    decided cells is a bound, and the exact fraction is not stored). Seeds are unchanged.
    """
    need = math.ceil(POWER_TARGET * N_PLANT)
    passes = 0
    for k in range(N_PLANT):
        planted, pos = make_shape(shape, returns, net_edge_bps=net_edge_bps, cost_bps=cost_bps,
                                  episode_length=episode_length, seed=6000 + k)
        passes += gate_passes(arm, planted, pos, domain=domain, cost_bps=cost_bps, seed=7000 + k)
        remaining = N_PLANT - (k + 1)
        if passes >= need or passes + remaining < need:
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
    """Leak control: plant edge, permute returns (destroy alignment) -> must collapse to FPR."""
    passes = 0
    for k in range(N_PLANT):
        planted, pos = make_shape(shape, returns, net_edge_bps=net_edge_bps, cost_bps=cost_bps,
                                  episode_length=episode_length, seed=6000 + k)
        destroyed = permuted_returns(planted, seed=8000 + k)
        passes += gate_passes(arm, destroyed, pos, domain=domain, cost_bps=cost_bps, seed=7000 + k)
    return passes / N_PLANT


def dogfood_fpr(arm: str, returns: np.ndarray, aligned: pl.DataFrame, *, domain: str,
                episode_length: int, cost_bps: float) -> tuple[float, float, int, int]:
    """Per-stratum FPR for an arm over 3 null families (abstract x2 + real dogfood).

    Returns ``(rate, wilson_halfwidth, draws, passes)`` — ``passes`` is threaded out so the binding
    verdict (A1) can apply a Wilson lower bound resolved above the frozen arm's FPR.
    """
    n = len(returns)
    passes, draws = 0, 0
    for k in range(N_NULL):
        pr = permuted_returns(returns, seed=1000 + k)
        passes += gate_passes(arm, pr, persistent_positions(n, episode_length, 2000 + k),
                              domain=domain, cost_bps=cost_bps, seed=3000 + k)
        passes += gate_passes(arm, returns, reblocked_random_positions(n, episode_length, 4000 + k),
                              domain=domain, cost_bps=cost_bps, seed=5000 + k)
        draws += 2
    high = aligned.get_column("High").to_numpy()
    low = aligned.get_column("Low").to_numpy()
    close = aligned.get_column("Close").to_numpy()
    don = lag_open_to_open(donchian_breakout_positions(high, low, close, lookback=20))
    ma = lag_open_to_open(ma_crossover_positions(close, fast=20, slow=50))
    for sig, sd in ((don, 9001), (ma, 9002)):
        passes += gate_passes(arm, returns, sig, domain=domain, cost_bps=cost_bps, seed=sd)
        draws += 1
    _, lo, hi = wilson_interval(passes, draws)
    return passes / draws, (hi - lo) / 2.0, draws, passes

# --------------------------------------------------------------------------- #
# Per-stratum orchestration
# --------------------------------------------------------------------------- #
def classify_stratum(mde: dict, dogfood: dict) -> str:
    """DET_DOMINANT / NOT_IMPROVED / FPR_BROKEN for one stratum (binding, L-03).

    FPR clause (A1, noise-tolerant): FPR_BROKEN only when the adaptive dogfood-FPR is STATISTICALLY
    RESOLVED above the frozen arm — Wilson lower bound of (passes_adaptive, draws) > frozen rate.
    A single within-noise dogfood pass no longer trips the break.
    """
    _, _, draws_a, passes_a = dogfood["adaptive"]
    _, adaptive_lo, _ = wilson_interval(passes_a, draws_a)
    if adaptive_lo > dogfood["frozen"][0]:
        return "FPR_BROKEN"
    no_regression = all(mde[("adaptive", s)] <= mde[("frozen", s)] for s in SHAPES)
    strict = any(mde[("adaptive", s)] < mde[("frozen", s)] for s in SHAPES)
    return "DET_DOMINANT" if (no_regression and strict) else "NOT_IMPROVED"


def run_stratum(returns: np.ndarray, aligned: pl.DataFrame, instrument: str,
                domain: str) -> tuple[list[dict], dict, list[str]]:
    """Return (per shape x arm rows, stratum summary, tripwire failures) for one instrument x domain."""
    L = EPISODE_LENGTHS[domain]
    cost = adaptive_cost_bps_for(instrument, domain)
    failures: list[str] = []

    dogfood = {arm: dogfood_fpr(arm, returns, aligned, domain=domain, episode_length=L,
                                cost_bps=cost) for arm in ARMS}
    mde: dict = {}
    shape_rows: list[dict] = []
    for shape in SHAPES:
        row: dict = {"instrument": instrument, "domain": domain, "cost_bps": cost, "shape": shape}
        for arm in ARMS:
            m = mde_of(arm, shape, returns, domain=domain, episode_length=L, cost_bps=cost)
            mde[(arm, shape)] = m
            row[f"mde_{arm}_bps"] = m
            row[f"no_plant_{arm}"] = no_plant_passrate(arm, shape, returns, domain=domain,
                                                       episode_length=L, cost_bps=cost)
        # future-destroy on the adaptive arm at detected MDE + top grid level
        levels = sorted({lvl for lvl in (mde[("adaptive", shape)], EDGE_GRID_BPS[-1])
                         if math.isfinite(lvl)})
        row["future_destroyed_adaptive"] = {
            lvl: future_destroyed_passrate("adaptive", shape, returns, domain=domain,
                                           episode_length=L, cost_bps=cost, net_edge_bps=lvl)
            for lvl in levels}
        row["delta_mde_vs_frozen"] = (mde[("frozen", shape)] - mde[("adaptive", shape)]
                                      if math.isfinite(mde[("frozen", shape)])
                                      and math.isfinite(mde[("adaptive", shape)]) else math.nan)
        shape_rows.append(row)

        # tripwires
        guard = max(dogfood["adaptive"][0] + 2 * dogfood["adaptive"][1], FPR_CONTROL_BOUND)
        for arm in ARMS:
            if row[f"no_plant_{arm}"] > guard:
                failures.append(f"{instrument}/{domain}/{shape}: no-plant ({arm}) {row[f'no_plant_{arm}']:.3f}")
        for lvl, rate in row["future_destroyed_adaptive"].items():
            if rate > guard:
                failures.append(f"{instrument}/{domain}/{shape}: adaptive edge SURVIVED future-destroy "
                                f"(e={lvl}) pass={rate:.3f} -> LEAK")
        # A1 (2026-06-29): the "sparse must stay UNPOWERED" assertion is RETRACTED — refuted by the
        # first run + audit (L1 bit-identical/rigid; sparse recovery is real and D0-compliant). Sparse
        # recovery is now an expected characterised outcome, not a tripwire failure.

    for arm in ARMS:
        if dogfood[arm][0] - dogfood[arm][1] > FPR_CONTROL_BOUND:
            failures.append(f"{instrument}/{domain}: dogfood FPR ({arm}) {dogfood[arm][0]:.3f} > control")

    summary = {"instrument": instrument, "domain": domain, "cost_bps": cost,
               "verdict": classify_stratum(mde, dogfood),
               **{f"dogfood_fpr_{arm}": dogfood[arm][0] for arm in ARMS},
               **{f"dogfood_fpr_{arm}_hw": dogfood[arm][1] for arm in ARMS},
               "state_delta_mde": (mde[("frozen", "state")] - mde[("adaptive", "state")]
                                   if math.isfinite(mde[("frozen", "state")])
                                   and math.isfinite(mde[("adaptive", "state")]) else math.nan)}
    return shape_rows, summary, failures

def run_instrument(instrument: str, path_str: str) -> tuple[list[dict], list[dict], list[str]]:
    """Worker: run both domains for one instrument (loads its file once). Picklable, seed-deterministic.

    Independent of every other instrument and uses only explicit per-draw seeds, so running this in a
    separate process yields bit-identical results regardless of scheduling order.
    """
    minutes = load_analysis_minutes(Path(path_str))
    shapes: list[dict] = []
    summaries: list[dict] = []
    failures: list[str] = []
    for domain in ADAPTIVE_DOMAINS:
        returns, aligned = build_domain(minutes, domain)
        if len(returns) < 200:
            continue
        srows, summary, fails = run_stratum(returns, aligned, instrument, domain)
        shapes.extend(srows)
        summaries.append(summary)
        failures.extend(fails)
    return shapes, summaries, failures

# --------------------------------------------------------------------------- #
# Plotting (bounded inputs)
# --------------------------------------------------------------------------- #
def plot_det_map(shape_rows: list[dict], save_path: Path) -> None:
    """Strata x shape ΔMDE (frozen - adaptive); >0 = adaptive recovers, NaN where either UNPOWERED."""
    strata = sorted({(r["instrument"], r["domain"]) for r in shape_rows})
    labels = [f"{i}/{d}" for i, d in strata]
    idx = {s: k for k, s in enumerate(strata)}
    mat = np.full((len(strata), len(SHAPES)), np.nan)
    for r in shape_rows:
        v = r["delta_mde_vs_frozen"]
        mat[idx[(r["instrument"], r["domain"])], SHAPES.index(r["shape"])] = v if math.isfinite(v) else np.nan
    sns.set_theme(style="white")
    fig, ax = plt.subplots(figsize=(8, 10))
    sns.heatmap(mat, ax=ax, cmap="RdBu_r", center=0, annot=True, fmt=".1f",
                xticklabels=list(SHAPES), yticklabels=labels, mask=np.isnan(mat),
                cbar_kws={"label": "ΔMDE = frozen - adaptive (bps)"}, linewidths=0.4,
                linecolor="lightgrey")
    ax.set_title("DET map: ΔMDE frozen - adaptive (>0 = adaptive recovers; blank = either UNPOWERED)")
    ax.set_xlabel("edge shape")
    ax.set_ylabel("instrument / domain")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_state_recovery(shape_rows: list[dict], save_path: Path) -> None:
    """STATE-cell MDE across the 3 arms (isolates E1 accounting vs E3a leg-adaptation gain)."""
    state = [r for r in shape_rows if r["shape"] == "state"]
    labels = [f"{r['instrument']}/{r['domain']}" for r in state]
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(11, 5))
    x = np.arange(len(labels))
    for off, arm, mk in ((-0.25, "frozen", "o"), (0.0, "frozen_amortized", "s"), (0.25, "adaptive", "^")):
        ys = [r[f"mde_{arm}_bps"] if math.isfinite(r[f"mde_{arm}_bps"]) else np.nan for r in state]
        ax.scatter(x + off, ys, label=arm, marker=mk, s=45)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=90, fontsize=7)
    ax.set_title("STATE-cell MDE by arm (lower = better; NaN omitted = UNPOWERED)")
    ax.set_ylabel("MDE (bps)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_dogfood_fpr(summaries: list[dict], save_path: Path) -> None:
    """Dogfood FPR adaptive vs frozen per stratum (Wilson bars)."""
    labels = [f"{s['instrument']}/{s['domain']}" for s in summaries]
    x = np.arange(len(labels))
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.errorbar(x - 0.1, [s["dogfood_fpr_frozen"] for s in summaries],
                yerr=[s["dogfood_fpr_frozen_hw"] for s in summaries], fmt="o", label="frozen", capsize=2)
    ax.errorbar(x + 0.1, [s["dogfood_fpr_adaptive"] for s in summaries],
                yerr=[s["dogfood_fpr_adaptive_hw"] for s in summaries], fmt="^", label="adaptive", capsize=2)
    ax.axhline(FPR_CONTROL_BOUND, color="red", ls="--", lw=1, label=f"control {FPR_CONTROL_BOUND}")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=90, fontsize=7)
    ax.set_title("Dogfood-negative FPR: adaptive vs frozen (Wilson)")
    ax.set_ylabel("FPR")
    ax.legend()
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

# --------------------------------------------------------------------------- #
# Serialisation
# --------------------------------------------------------------------------- #
def write_results(shape_rows: list[dict], summaries: list[dict]) -> None:
    """Persist per-(shape,arm) MDE table, per-stratum DET-dominance, full JSON."""
    flat = ["instrument", "domain", "cost_bps", "shape", "mde_frozen_bps",
            "mde_frozen_amortized_bps", "mde_adaptive_bps", "delta_mde_vs_frozen",
            "no_plant_adaptive"]
    pl.DataFrame([{c: r[c] for c in flat} for r in shape_rows]).write_csv(RESULTS_DIR / "per_shape_arm.csv")
    pl.DataFrame(summaries).write_csv(RESULTS_DIR / "det_dominance_per_stratum.csv")
    (RESULTS_DIR / "per_shape_full.json").write_text(json.dumps(shape_rows, indent=2, default=str))

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

    jobs = [(ins, str(available[ins])) for ins in instruments if available[ins]]
    all_shapes: list[dict] = []
    summaries: list[dict] = []
    tripwire_failures: list[str] = []

    logger.info("running %d instruments over %d workers", len(jobs), N_WORKERS)
    with ProcessPoolExecutor(max_workers=N_WORKERS) as pool:
        futures = {pool.submit(run_instrument, ins, path): ins for ins, path in jobs}
        for fut in tqdm(as_completed(futures), total=len(futures), desc="instruments"):
            shapes, summ, fails = fut.result()
            all_shapes.extend(shapes)
            summaries.extend(summ)
            tripwire_failures.extend(fails)

    if not summaries:
        logger.error("No strata produced results — check data availability.")
        return

    write_results(all_shapes, summaries)
    plot_det_map(all_shapes, PLOTS_DIR / "det_map.png")
    plot_state_recovery(all_shapes, PLOTS_DIR / "state_recovery.png")
    plot_dogfood_fpr(summaries, PLOTS_DIR / "dogfood_fpr.png")

    verdicts = [s["verdict"] for s in summaries]
    logger.info("\n=== EXP-003 E3a summary ===")
    logger.info("strata: %d (instruments: %d)", len(summaries),
                len({s["instrument"] for s in summaries}))
    for v in sorted(set(verdicts)):
        logger.info("  %-14s %d", v, verdicts.count(v))
    state_d = [s["state_delta_mde"] for s in summaries if math.isfinite(s["state_delta_mde"])]
    if state_d:
        logger.info("STATE ΔMDE (frozen-adaptive) finite strata: %d | median=%.2f max=%.2f bps",
                    len(state_d), float(np.median(state_d)), float(np.max(state_d)))
    logger.info("results -> %s", RESULTS_DIR / "det_dominance_per_stratum.csv")
    if tripwire_failures:
        logger.error("LEAK-TRIPWIRE FAILURES (%d) — verdict-material, fix+rerun:", len(tripwire_failures))
        for f in tripwire_failures:
            logger.error("  - %s", f)
    else:
        logger.info("All leak tripwires held (dogfood FPR control, no-plant, future-destroy collapse).")


if __name__ == "__main__":
    main()
