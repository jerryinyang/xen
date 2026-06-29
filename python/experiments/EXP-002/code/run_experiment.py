"""
Experiment EXP-002 (E2): Synthetic-Positive Battery + Fresh Dogfood — frozen-gate shape blindness.

Implements python/experiments/EXP-002/design.md (GATE: APPROVE). Analysis-only: synthetic position
substrates + planted non-constant edges on frozen E0 primitives (open-to-open <=t-1 returns,
17-instrument cost map). No price->signal. First-70% slice; global holdout never loaded.

Question: does the frozen conjunctive 5-leg gate keep FINITE POWER on non-constant true edges
(tail-only / sparse / state-dependent), or is it structurally blind to shapes that are not
dense+location (L-12 §1/§2)? Per stratum x shape: MDE (DETECTED_FLOOR) or UNPOWERED.

Binds on the AMORTIZED (accounting-clean) convention via the E1 seam
`referee_adaptive.gate_stack_core_costfn`; reports PER-HELD in parallel (disclosure). The frozen gate
legs are UNCHANGED; only the signal-leg cost accounting differs.
"""
from __future__ import annotations

import json
import logging
import math
import sys
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
from xen.incremental_referee import EPISODE_LENGTHS

sys.path.insert(0, str(Path(__file__).resolve().parent))
from edge_shapes import (  # noqa: E402
    A_SPARSE,
    FRAC_A,
    dense_planted,
    mean_drift_over_denominator,
    persistent_positions,
    sparse_positions,
    state_dependent_planted,
    state_positions,
    tail_only_planted,
)

logger = logging.getLogger("EXP-002")

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
DATA_DIR = Path("data")
EXP_DIR = Path("python/experiments/EXP-002")
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"

ANALYSIS_FRACTION = 0.70
ERA_GLOB = "20210602_*"
PERIOD_MINUTES = {"1h": 60, "4h": 240}
DOMAIN_MIN_COVERAGE = 0.90

ALPHA = 0.05
N_BOOTSTRAP = 500
N_NULL = 80                       # abstract-null draws per substrate (per stratum)
N_PLANT = 20                      # planted-edge seeds per edge level
POWER_TARGET = 0.50
INFLATION_STEPS = 2               # MDE >= DENSE_MDE shifted up >= this many grid steps => inflated

SHAPES: tuple[str, ...] = ("dense", "tail", "sparse", "state")
CONVENTIONS: dict[str, object] = {
    "amortized": strategy_return_bps_turnover,   # BINDING
    "perheld": strategy_return_bps,              # disclosure
}
BINDING = "amortized"
FPR_CONTROL_BOUND = 2 * ALPHA     # frozen-suite control: null Wilson-upper must stay <= this

# --------------------------------------------------------------------------- #
# I/O helpers (orchestration-only)
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
    """Open-to-open <=t-1 returns + the aligned fenced domain frame (for dogfood OHLC)."""
    dom = aggregate_ohlc(minutes, period_minutes=PERIOD_MINUTES[domain],
                         min_coverage=DOMAIN_MIN_COVERAGE)
    dom = dom.filter(pl.col("CloseTime") <= minutes.get_column("CloseTime").max())
    returns, aligned = next_open_to_open_returns_from_bars(dom)
    return returns, aligned

# --------------------------------------------------------------------------- #
# Pure helpers
# --------------------------------------------------------------------------- #
def reblocked_random_positions(n: int, episode_length: int, seed: int) -> np.ndarray:
    """random_state_positions re-blocked to length L (turnover matched to the persistent arm)."""
    n_episodes = (n + episode_length - 1) // episode_length
    return np.repeat(random_state_positions(n_episodes, seed), episode_length)[:n]


def lag_open_to_open(positions: np.ndarray) -> np.ndarray:
    """Lag a close-indexed signal one bar so it acts at the NEXT bar's open on confirmed bars <=t-1.

    A dogfood signal computes its state from domain closes (bar i's close). Under the E0 open-to-open
    return basis (act at bar i's open, info <= i-1), the close-i state is live-actable only from bar
    i+1's open onward. Prepending a flat bar enforces that (the L-01 off-by-one discipline).
    """
    pos = np.asarray(positions, dtype=float)
    return np.concatenate(([0.0], pos[:-1]))


def make_shape(shape: str, returns: np.ndarray, *, net_edge_bps: float, cost_bps: float,
               episode_length: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Return (planted_returns, positions) for one shape draw. Matched-magnitude by construction."""
    n = len(returns)
    if shape == "dense":
        pos = persistent_positions(n, episode_length, seed)
        return dense_planted(returns, pos, net_edge_bps=net_edge_bps, cost_bps=cost_bps), pos
    if shape == "tail":
        pos = persistent_positions(n, episode_length, seed)
        planted = tail_only_planted(returns, pos, net_edge_bps=net_edge_bps, cost_bps=cost_bps,
                                    seed=seed + 50_000)
        return planted, pos
    if shape == "sparse":
        pos = sparse_positions(n, episode_length, seed)
        return dense_planted(returns, pos, net_edge_bps=net_edge_bps, cost_bps=cost_bps), pos
    if shape == "state":
        pos, mask = state_positions(n, episode_length, seed)
        planted = state_dependent_planted(returns, pos, mask, net_edge_bps=net_edge_bps,
                                          cost_bps=cost_bps)
        return planted, pos
    raise ValueError(f"unknown shape: {shape}")


def gate_passes(returns: np.ndarray, positions: np.ndarray, *, domain: str, cost_bps: float,
                strategy_fn: object, seed: int) -> bool:
    """True iff the frozen gate stack PASSES for one draw under a convention (seam, legs unchanged)."""
    core = gate_stack_core_costfn(returns, positions, domain=domain, cost_bps=cost_bps,
                                  n_bootstrap=N_BOOTSTRAP, seed=seed, strategy_fn=strategy_fn)
    return bool(gate_stack_row(core, alpha=ALPHA)["passed"])


def detection_rate(shape: str, returns: np.ndarray, *, domain: str, episode_length: int,
                   cost_bps: float, net_edge_bps: float, strategy_fn: object) -> float:
    """Fraction of planted draws the gate PASSES for one (shape, e, convention)."""
    passes = 0
    for k in range(N_PLANT):
        planted, pos = make_shape(shape, returns, net_edge_bps=net_edge_bps, cost_bps=cost_bps,
                                  episode_length=episode_length, seed=6000 + k)
        passes += gate_passes(planted, pos, domain=domain, cost_bps=cost_bps,
                              strategy_fn=strategy_fn, seed=7000 + k)
    return passes / N_PLANT


def mde_curve(shape: str, returns: np.ndarray, *, domain: str, episode_length: int, cost_bps: float,
              strategy_fn: object) -> tuple[float, dict[float, float]]:
    """DETECTED_FLOOR MDE (first e>0 with detection >= POWER_TARGET; inf=UNPOWERED) + the curve."""
    curve: dict[float, float] = {}
    mde = math.inf
    for edge in EDGE_GRID_BPS:
        rate = detection_rate(shape, returns, domain=domain, episode_length=episode_length,
                              cost_bps=cost_bps, net_edge_bps=edge, strategy_fn=strategy_fn)
        curve[edge] = rate
        if math.isinf(mde) and edge > 0.0 and rate >= POWER_TARGET:
            mde = edge
    return mde, curve


def classify(shape_mde: float, dense_mde: float) -> str:
    """Per-cell blindness label vs the DENSE anchor in the same stratum."""
    if math.isinf(shape_mde):
        return "DENSE_ONLY_BLIND" if math.isfinite(dense_mde) else "UNPOWERED"
    if math.isfinite(dense_mde):
        grid = list(EDGE_GRID_BPS)
        steps = grid.index(shape_mde) - grid.index(dense_mde)
        if steps >= INFLATION_STEPS:
            return "MDE_INFLATED"
    return "DETECTED"


def no_plant_passrate(shape: str, returns: np.ndarray, *, domain: str, episode_length: int,
                      cost_bps: float, strategy_fn: object) -> float:
    """No-real-edge guard: PASS rate on the shape's positions with NO planted drift (EXP-001 fix)."""
    passes = 0
    for k in range(N_PLANT):
        _, pos = make_shape(shape, returns, net_edge_bps=0.0, cost_bps=cost_bps,
                            episode_length=episode_length, seed=6000 + k)
        passes += gate_passes(returns, pos, domain=domain, cost_bps=cost_bps,
                              strategy_fn=strategy_fn, seed=7000 + k)
    return passes / N_PLANT


def future_destroyed_passrate(shape: str, returns: np.ndarray, *, domain: str, episode_length: int,
                              cost_bps: float, net_edge_bps: float, strategy_fn: object) -> float:
    """Leak control: plant the edge, then permute returns (destroy alignment) -> must collapse to FPR."""
    passes = 0
    for k in range(N_PLANT):
        planted, pos = make_shape(shape, returns, net_edge_bps=net_edge_bps, cost_bps=cost_bps,
                                  episode_length=episode_length, seed=6000 + k)
        destroyed = permuted_returns(planted, seed=8000 + k)
        passes += gate_passes(destroyed, pos, domain=domain, cost_bps=cost_bps,
                              strategy_fn=strategy_fn, seed=7000 + k)
    return passes / N_PLANT


def abstract_null_fpr(returns: np.ndarray, *, domain: str, episode_length: int, cost_bps: float,
                      strategy_fn: object) -> tuple[float, float, int]:
    """Per-stratum FPR over two abstract nulls (block-permuted returns; reblock-random positions)."""
    n = len(returns)
    passes = 0
    for k in range(N_NULL):
        pr = permuted_returns(returns, seed=1000 + k)
        pos = persistent_positions(n, episode_length, 2000 + k)
        passes += gate_passes(pr, pos, domain=domain, cost_bps=cost_bps, strategy_fn=strategy_fn,
                              seed=3000 + k)
        pos_rb = reblocked_random_positions(n, episode_length, 4000 + k)
        passes += gate_passes(returns, pos_rb, domain=domain, cost_bps=cost_bps,
                              strategy_fn=strategy_fn, seed=5000 + k)
    draws = 2 * N_NULL
    _, lo, hi = wilson_interval(passes, draws)
    return passes / draws, (hi - lo) / 2.0, draws


def dogfood_pass(returns: np.ndarray, aligned: pl.DataFrame, *, domain: str, cost_bps: float,
                 strategy_fn: object) -> dict[str, bool]:
    """Real known-null signals (Donchian R, MA 20/50), causally lagged, no plant -> should reject."""
    high = aligned.get_column("High").to_numpy()
    low = aligned.get_column("Low").to_numpy()
    close = aligned.get_column("Close").to_numpy()
    don = lag_open_to_open(donchian_breakout_positions(high, low, close, lookback=20))
    ma = lag_open_to_open(ma_crossover_positions(close, fast=20, slow=50))
    return {
        "donchian_20": gate_passes(returns, don, domain=domain, cost_bps=cost_bps,
                                   strategy_fn=strategy_fn, seed=9001),
        "ma_20_50": gate_passes(returns, ma, domain=domain, cost_bps=cost_bps,
                                strategy_fn=strategy_fn, seed=9002),
    }

# --------------------------------------------------------------------------- #
# Per-stratum orchestration
# --------------------------------------------------------------------------- #
def run_stratum(returns: np.ndarray, aligned: pl.DataFrame, instrument: str,
                domain: str) -> tuple[list[dict], dict, list[dict]]:
    """Return (per-shape rows, per-stratum FPR row, dogfood verdict rows) for one instrument x domain."""
    L = EPISODE_LENGTHS[domain]
    cost = adaptive_cost_bps_for(instrument, domain)

    fpr_row: dict[str, object] = {"instrument": instrument, "domain": domain, "cost_bps": cost,
                                  "n_returns": len(returns)}
    for cname, fn in CONVENTIONS.items():
        fpr, hw, draws = abstract_null_fpr(returns, domain=domain, episode_length=L,
                                           cost_bps=cost, strategy_fn=fn)
        fpr_row[f"fpr_{cname}"] = fpr
        fpr_row[f"fpr_{cname}_wilson_hw"] = hw
        fpr_row[f"fpr_{cname}_draws"] = draws

    dogfood_rows: list[dict] = []
    for cname, fn in CONVENTIONS.items():
        for gen, passed in dogfood_pass(returns, aligned, domain=domain, cost_bps=cost,
                                        strategy_fn=fn).items():
            dogfood_rows.append({"instrument": instrument, "domain": domain, "generator": gen,
                                 "convention": cname, "passed": bool(passed)})

    # DENSE MDE per convention first (the anchor for classification).
    dense_mde = {c: mde_curve("dense", returns, domain=domain, episode_length=L, cost_bps=cost,
                              strategy_fn=fn)[0] for c, fn in CONVENTIONS.items()}

    shape_rows: list[dict] = []
    for shape in SHAPES:
        row: dict[str, object] = {"instrument": instrument, "domain": domain, "episode_length": L,
                                  "cost_bps": cost, "shape": shape}
        for cname, fn in CONVENTIONS.items():
            mde, curve = mde_curve(shape, returns, domain=domain, episode_length=L, cost_bps=cost,
                                   strategy_fn=fn)
            row[f"mde_{cname}_bps"] = mde
            row[f"class_{cname}"] = classify(mde, dense_mde[cname])
            row[f"det_curve_{cname}"] = curve
            row[f"no_plant_passrate_{cname}"] = no_plant_passrate(
                shape, returns, domain=domain, episode_length=L, cost_bps=cost, strategy_fn=fn)
            # future-destroying control at the detected MDE (if any) + the top grid level
            levels = sorted({lvl for lvl in (mde, EDGE_GRID_BPS[-1]) if math.isfinite(lvl)})
            row[f"future_destroyed_{cname}"] = {
                lvl: future_destroyed_passrate(shape, returns, domain=domain, episode_length=L,
                                               cost_bps=cost, net_edge_bps=lvl, strategy_fn=fn)
                for lvl in levels}
        shape_rows.append(row)
    return shape_rows, fpr_row, dogfood_rows

# --------------------------------------------------------------------------- #
# Plotting (bounded inputs)
# --------------------------------------------------------------------------- #
def _mde_matrix(shape_rows: list[dict], convention: str) -> tuple[np.ndarray, list[str]]:
    """Strata x shape MDE matrix (inf -> nan) for the heatmap."""
    strata = sorted({(r["instrument"], r["domain"]) for r in shape_rows})
    labels = [f"{i}/{d}" for i, d in strata]
    mat = np.full((len(strata), len(SHAPES)), np.nan)
    index = {s: k for k, s in enumerate(strata)}
    for r in shape_rows:
        val = r[f"mde_{convention}_bps"]
        mat[index[(r["instrument"], r["domain"])], SHAPES.index(r["shape"])] = (
            val if math.isfinite(val) else np.nan)
    return mat, labels


def plot_blindness_map(shape_rows: list[dict], save_path: Path) -> None:
    """Strata x shape MDE heatmap (NaN = UNPOWERED) — amortized (binding) + per-held (disclosure)."""
    sns.set_theme(style="white")
    fig, axes = plt.subplots(1, 2, figsize=(13, 10), sharey=True)
    for ax, conv in zip(axes, (BINDING, "perheld")):
        mat, labels = _mde_matrix(shape_rows, conv)
        sns.heatmap(mat, ax=ax, cmap="viridis_r", annot=True, fmt=".1f", cbar_kws={"label": "MDE bps"},
                    xticklabels=list(SHAPES), yticklabels=labels,
                    mask=np.isnan(mat), linewidths=0.4, linecolor="lightgrey")
        ax.set_title(f"MDE by stratum x shape — {conv}{' (binding)' if conv == BINDING else ' (disclosure)'}\n"
                     "blank = UNPOWERED")
        ax.set_xlabel("edge shape")
    axes[0].set_ylabel("instrument / domain")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_mde_by_shape(shape_rows: list[dict], save_path: Path) -> None:
    """MDE distribution per shape across strata (binding convention; UNPOWERED count annotated)."""
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(8, 5))
    data, unpowered = [], []
    for shape in SHAPES:
        vals = [r[f"mde_{BINDING}_bps"] for r in shape_rows if r["shape"] == shape]
        finite = [v for v in vals if math.isfinite(v)]
        data.append(finite)
        unpowered.append(sum(math.isinf(v) for v in vals))
    ax.boxplot(data, labels=[f"{s}\n(UNPWR {u})" for s, u in zip(SHAPES, unpowered)])
    ax.set_title(f"MDE by shape across strata — {BINDING} (binding); UNPOWERED excluded")
    ax.set_xlabel("edge shape")
    ax.set_ylabel("MDE (bps)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_fpr_by_stratum(fpr_rows: list[dict], save_path: Path) -> None:
    """Abstract-null FPR per stratum with Wilson half-width error bars (binding convention)."""
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 5))
    labels = [f"{r['instrument']}/{r['domain']}" for r in fpr_rows]
    fpr = [r[f"fpr_{BINDING}"] for r in fpr_rows]
    hw = [r[f"fpr_{BINDING}_wilson_hw"] for r in fpr_rows]
    x = np.arange(len(labels))
    ax.errorbar(x, fpr, yerr=hw, fmt="o", capsize=3)
    ax.axhline(FPR_CONTROL_BOUND, color="red", ls="--", lw=1, label=f"control bound {FPR_CONTROL_BOUND}")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=90, fontsize=7)
    ax.set_title(f"Abstract-null FPR per stratum (Wilson) — {BINDING}")
    ax.set_ylabel("FPR")
    ax.legend()
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

# --------------------------------------------------------------------------- #
# Serialisation
# --------------------------------------------------------------------------- #
def write_results(shape_rows: list[dict], fpr_rows: list[dict], dogfood_rows: list[dict]) -> None:
    """Persist per-shape table (CSV flat + JSON full), FPR table, dogfood verdicts."""
    flat_cols = ["instrument", "domain", "episode_length", "cost_bps", "shape",
                 "mde_amortized_bps", "class_amortized", "mde_perheld_bps", "class_perheld",
                 "no_plant_passrate_amortized", "no_plant_passrate_perheld"]
    pl.DataFrame([{c: r[c] for c in flat_cols} for r in shape_rows]).write_csv(
        RESULTS_DIR / "per_shape.csv")
    pl.DataFrame(fpr_rows).write_csv(RESULTS_DIR / "fpr_per_stratum.csv")
    pl.DataFrame(dogfood_rows).write_csv(RESULTS_DIR / "dogfood_verdicts.csv")
    (RESULTS_DIR / "per_shape_full.json").write_text(
        json.dumps(shape_rows, indent=2, default=str))

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

    strata = [(ins, dom) for ins in instruments if available[ins] for dom in ADAPTIVE_DOMAINS]
    all_shapes: list[dict] = []
    all_fpr: list[dict] = []
    all_dogfood: list[dict] = []
    tripwire_failures: list[str] = []
    minutes_cache: dict[str, pl.DataFrame] = {}

    for instrument, domain in tqdm(strata, desc="strata"):
        if instrument not in minutes_cache:
            minutes_cache[instrument] = load_analysis_minutes(available[instrument])
        returns, aligned = build_domain(minutes_cache[instrument], domain)
        if len(returns) < 200:
            logger.info("SKIP %s/%s: only %d domain returns", instrument, domain, len(returns))
            continue
        shape_rows, fpr_row, dogfood_rows = run_stratum(returns, aligned, instrument, domain)
        all_shapes.extend(shape_rows)
        all_fpr.append(fpr_row)
        all_dogfood.extend(dogfood_rows)

        # Tripwire checks (blocking).
        for cname in CONVENTIONS:
            if fpr_row[f"fpr_{cname}"] - fpr_row[f"fpr_{cname}_wilson_hw"] > FPR_CONTROL_BOUND:
                tripwire_failures.append(
                    f"{instrument}/{domain}: abstract-null FPR ({cname}) "
                    f"{fpr_row[f'fpr_{cname}']:.3f} > control {FPR_CONTROL_BOUND}")
        for r in shape_rows:
            for cname in CONVENTIONS:
                guard = fpr_row[f"fpr_{cname}"] + 2 * fpr_row[f"fpr_{cname}_wilson_hw"]
                if r[f"no_plant_passrate_{cname}"] > max(guard, FPR_CONTROL_BOUND):
                    tripwire_failures.append(
                        f"{instrument}/{domain}/{r['shape']}: no-plant guard ({cname}) "
                        f"{r[f'no_plant_passrate_{cname}']:.3f}")
                for lvl, rate in r[f"future_destroyed_{cname}"].items():
                    if rate > max(guard, FPR_CONTROL_BOUND):
                        tripwire_failures.append(
                            f"{instrument}/{domain}/{r['shape']}: edge SURVIVED future-destroy "
                            f"({cname}, e={lvl}) pass={rate:.3f} -> LEAK")

    if not all_shapes:
        logger.error("No strata produced results — check data availability.")
        return

    write_results(all_shapes, all_fpr, all_dogfood)
    plot_blindness_map(all_shapes, PLOTS_DIR / "blindness_map.png")
    plot_mde_by_shape(all_shapes, PLOTS_DIR / "mde_by_shape.png")
    plot_fpr_by_stratum(all_fpr, PLOTS_DIR / "fpr_by_stratum.png")

    logger.info("\n=== EXP-002 E2 summary (binding: %s) ===", BINDING)
    logger.info("strata: %d (instruments: %d) x shapes: %d", len(all_fpr), len(minutes_cache),
                len(SHAPES))
    for shape in SHAPES:
        cls = [r[f"class_{BINDING}"] for r in all_shapes if r["shape"] == shape]
        counts = {c: cls.count(c) for c in sorted(set(cls))}
        logger.info("  %-7s %s", shape, counts)
    # dogfood program-level FPR per convention (Wilson)
    for cname in CONVENTIONS:
        rows = [d for d in all_dogfood if d["convention"] == cname]
        succ = sum(d["passed"] for d in rows)
        _, lo, hi = wilson_interval(succ, len(rows))
        logger.info("  dogfood FPR (%s): %d/%d wilson_hw=%.3f", cname, succ, len(rows),
                    (hi - lo) / 2.0 if rows else float("nan"))
    logger.info("results -> %s", RESULTS_DIR / "per_shape.csv")
    if tripwire_failures:
        logger.error("LEAK-TRIPWIRE FAILURES (%d) — verdict-material, fix+rerun:",
                     len(tripwire_failures))
        for f in tripwire_failures:
            logger.error("  - %s", f)
    else:
        logger.info("All leak tripwires held (FPR control, no-plant, future-destroy collapse).")


if __name__ == "__main__":
    main()
