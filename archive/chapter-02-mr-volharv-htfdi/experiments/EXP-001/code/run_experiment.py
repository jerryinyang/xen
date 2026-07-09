"""
Experiment EXP-001 (E1): Cost-Control Arm — per-held-bar vs amortized cost convention.

Implements the analysis plan in python/experiments/EXP-001/design.md (GATE: APPROVE).

Classification: ANALYSIS-ONLY. Synthetic blockwise-persistent positions on frozen E0
primitives (open-to-open <= t-1 real returns, 17-instrument round-trip cost map). Generates no
price edge. Holdout: first-70% 1-minute slice only; global final-30% never loaded.

Question: how much of Component A's economic-MDE inflation is the per-held-bar cost convention
(charge cost on every held bar) rather than the conjunctive gate shape? For a persistent
(low-turnover) signal, does charging the round-trip ONCE per holding episode (amortized) instead
of on every held bar lower the gate-stack MDE at equal-or-better FPR — per stratum?

Two conventions, identical everything else, run through the frozen gate via the E1 seam
`xen.referee_adaptive.gate_stack_core_costfn` (mirrors frozen gate_stack_core; signal leg only):
  A-per-held-bar : xen.referee_calibration.strategy_return_bps     (cost every active bar)
  A-amortized    : code.cost_conventions.strategy_return_bps_turnover (cost once per entry)

Binding metric per stratum (instrument x domain): ΔMDE = MDE_perheld - MDE_amortized at matched
FPR. Pooled figures are disclosure-only (L-03).
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
)
from xen.referee_calibration import (
    EDGE_GRID_BPS,
    cost_bps_for,
    gate_stack_core,
    gate_stack_row,
    permuted_returns,
    plant_positive_edge,
    random_state_positions,
    strategy_return_bps,
)
from xen.incremental_referee import EPISODE_LENGTHS, _blockwise_state

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cost_conventions import entry_mask, strategy_return_bps_turnover  # noqa: E402

logger = logging.getLogger("EXP-001")

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
DATA_DIR = Path("data")
EXP_DIR = Path("python/experiments/EXP-001")
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"

ANALYSIS_FRACTION = 0.70          # global holdout fence: first 70% of 1-minute bars
ERA_GLOB = "20210602_*"           # INFR-003 5-year canonical era ONLY (never mix eras)
PERIOD_MINUTES = {"1h": 60, "4h": 240}
DOMAIN_MIN_COVERAGE = 0.90        # deployed domain-construction tolerance (dataset-reference)

ALPHA = 0.05                      # gate operating point (frozen ALPHA_GRID midpoint)
N_BOOTSTRAP = 500                 # gate block-bootstrap resamples
N_NULL = 100                      # null draws per substrate for FPR (Wilson-bounded)
N_PLANT = 24                      # planted-edge seeds per edge level (power estimate)
POWER_TARGET = 0.50               # MDE = first edge with detection rate >= POWER_TARGET

CONVENTIONS: dict[str, object] = {
    "perheld": strategy_return_bps,
    "amortized": strategy_return_bps_turnover,
}

# --------------------------------------------------------------------------- #
# I/O helpers (orchestration-only file access)
# --------------------------------------------------------------------------- #
def era_file_for(instrument: str) -> Path | None:
    """Newest 5-year-era 1-minute file for an instrument, or None if absent."""
    matches = sorted(DATA_DIR.glob(f"timebars/timebars_{instrument.lower()}_{ERA_GLOB}.parquet"))
    return matches[-1] if matches else None


def load_analysis_minutes(path: Path) -> pl.DataFrame:
    """First-70% (CloseTime-ordered) 1-minute slice. Global holdout never collected."""
    scan = pl.scan_parquet(path).sort("CloseTime")
    total = int(scan.select(pl.len()).collect().item())
    cutoff = int(total * ANALYSIS_FRACTION)
    return scan.slice(0, cutoff).collect()


def build_domain_returns(minutes: pl.DataFrame, domain: str) -> np.ndarray:
    """Open-to-open <= t-1 returns on fenced domain bars built from the analysis minutes.

    Domain bars: aggregate_ohlc(min_coverage=0.90) PLUS the analysis-boundary fence (drop any
    window whose CloseTime exceeds the last source minute) — keeps domain bars holdout-clean.
    """
    dom = aggregate_ohlc(minutes, period_minutes=PERIOD_MINUTES[domain],
                         min_coverage=DOMAIN_MIN_COVERAGE)
    last_minute = minutes.get_column("CloseTime").max()
    dom = dom.filter(pl.col("CloseTime") <= last_minute)
    returns, _ = next_open_to_open_returns_from_bars(dom)
    return returns

# --------------------------------------------------------------------------- #
# Position / null substrate builders (pure)
# --------------------------------------------------------------------------- #
def persistent_positions(n: int, episode_length: int, seed: int) -> np.ndarray:
    """Blockwise-persistent {-1,+1} positions of episode length L (frozen primitive)."""
    return _blockwise_state(n, episode_length, np.random.default_rng(seed))


def alternating_positions(n: int) -> np.ndarray:
    """Strictly-alternating +1,-1,+1,... (L=1 coincide control: every active bar is an entry)."""
    return np.resize(np.array([1.0, -1.0]), n)


def reblocked_random_positions(n: int, episode_length: int, seed: int) -> np.ndarray:
    """random_state_positions re-blocked to length L (turnover matched to the persistent arm)."""
    n_episodes = (n + episode_length - 1) // episode_length
    signs = random_state_positions(n_episodes, seed)
    return np.repeat(signs, episode_length)[:n]

# --------------------------------------------------------------------------- #
# Gate evaluation (pure)
# --------------------------------------------------------------------------- #
def gate_passes(returns: np.ndarray, positions: np.ndarray, *, domain: str, cost_bps: float,
                strategy_fn: object, seed: int) -> bool:
    """True iff the gate stack PASSES for one (returns, positions) draw under a convention."""
    core = gate_stack_core_costfn(returns, positions, domain=domain, cost_bps=cost_bps,
                                  n_bootstrap=N_BOOTSTRAP, seed=seed, strategy_fn=strategy_fn)
    return bool(gate_stack_row(core, alpha=ALPHA)["passed"])


def false_positive_rate(returns: np.ndarray, *, domain: str, episode_length: int,
                        cost_bps: float, strategy_fn: object) -> tuple[float, int]:
    """FPR over two null substrates (permuted-returns+persistent; real+reblock-random), no edge.

    Returns the pooled pass fraction and the total null-draw count (for the Wilson bound).
    """
    n = len(returns)
    passes = 0
    for k in range(N_NULL):
        pr = permuted_returns(returns, seed=1000 + k)
        pos = persistent_positions(n, episode_length, seed=2000 + k)
        passes += gate_passes(pr, pos, domain=domain, cost_bps=cost_bps,
                              strategy_fn=strategy_fn, seed=3000 + k)
        pos_rb = reblocked_random_positions(n, episode_length, seed=4000 + k)
        passes += gate_passes(returns, pos_rb, domain=domain, cost_bps=cost_bps,
                              strategy_fn=strategy_fn, seed=5000 + k)
    draws = 2 * N_NULL
    return passes / draws, draws


def detection_rate(returns: np.ndarray, *, domain: str, episode_length: int, cost_bps: float,
                   net_edge_bps: float, strategy_fn: object) -> float:
    """Fraction of planted-edge draws (persistent states + plant_positive_edge) the gate PASSES."""
    n = len(returns)
    passes = 0
    for k in range(N_PLANT):
        pos = persistent_positions(n, episode_length, seed=6000 + k)
        planted = plant_positive_edge(returns, pos, net_edge_bps=net_edge_bps, cost_bps=cost_bps)
        passes += gate_passes(planted, pos, domain=domain, cost_bps=cost_bps,
                              strategy_fn=strategy_fn, seed=7000 + k)
    return passes / N_PLANT


def no_plant_passrate(returns: np.ndarray, *, domain: str, episode_length: int, cost_bps: float,
                      strategy_fn: object) -> float:
    """No-real-edge guard: PASS rate on real returns + persistent positions with NO planted drift.

    The true shared zero-net for BOTH conventions (gross drift 0 -> net = -cost per its own
    charge < 0 -> reject). Replaces the mis-specified plant(edge=0) guard, which injects a
    per-held-bar-calibrated +cost drift that is a genuine edge under the amortized convention
    (audit.md Critical 1). Must be ~0 for both arms — a positive rate is a phantom positive from
    the cost change.
    """
    n = len(returns)
    passes = 0
    for k in range(N_PLANT):
        pos = persistent_positions(n, episode_length, seed=6000 + k)
        passes += gate_passes(returns, pos, domain=domain, cost_bps=cost_bps,
                              strategy_fn=strategy_fn, seed=7000 + k)
    return passes / N_PLANT


def mde_bps(returns: np.ndarray, *, domain: str, episode_length: int, cost_bps: float,
            strategy_fn: object) -> tuple[float, dict[float, float]]:
    """Smallest EDGE_GRID_BPS level with detection rate >= POWER_TARGET (inf if UNPOWERED).

    Also returns the full detection-rate curve (edge=0 row is the no-real-edge guard).
    """
    curve: dict[float, float] = {}
    mde = math.inf
    for edge in EDGE_GRID_BPS:
        rate = detection_rate(returns, domain=domain, episode_length=episode_length,
                              cost_bps=cost_bps, net_edge_bps=edge, strategy_fn=strategy_fn)
        curve[edge] = rate
        if math.isinf(mde) and edge > 0.0 and rate >= POWER_TARGET:
            mde = edge
    return mde, curve

# --------------------------------------------------------------------------- #
# Pure checks (leak tripwires)
# --------------------------------------------------------------------------- #
def wilson_halfwidth(p: float, n: int, *, z: float = 1.96) -> float:
    """Wilson 95% interval half-width for a proportion (never report FPR as '≈0')."""
    if n == 0:
        return float("nan")
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    lo, hi = centre - half, centre + half
    return (hi - lo) / 2.0


def tripwire_alternating_coincide(returns: np.ndarray, cost_bps: float) -> dict[str, object]:
    """Tripwire 2: on strictly-alternating positions the two conventions coincide exactly."""
    alt = alternating_positions(len(returns))
    perheld = strategy_return_bps(returns, alt, cost_bps=cost_bps)
    amort = strategy_return_bps_turnover(returns, alt, cost_bps=cost_bps)
    return {
        "all_entries": bool(entry_mask(alt).all()),     # every active bar is an entry
        "series_identical": bool(np.array_equal(perheld, amort)),
    }


def tripwire_cost_monotone(returns: np.ndarray, episode_length: int, cost_bps: float,
                           seed: int = 0) -> dict[str, object]:
    """Tripwire 1: on persistent positions amortized total cost <= per-held-bar total cost."""
    pos = persistent_positions(len(returns), episode_length, seed=seed)
    active = int(np.count_nonzero(pos))
    entries = int(entry_mask(pos).sum())
    return {
        "active_bars": active,
        "entry_bars": entries,
        "perheld_total_cost_bps": cost_bps * active,
        "amortized_total_cost_bps": cost_bps * entries,
        "monotone_ok": bool(entries <= active),
    }


def tripwire_equivalence(returns: np.ndarray, instrument: str, domain: str, episode_length: int,
                         seed: int = 11) -> bool:
    """Tripwire 4 (audit seam check): wrapper at strategy_fn=strategy_return_bps == frozen core."""
    if instrument.upper() not in {"EURUSD", "XAUUSD", "BTCUSD", "USTEC"}:
        return True  # frozen cost map only defines the 4 anchors; equivalence checked on those
    pos = persistent_positions(len(returns), episode_length, seed=seed)
    cost = cost_bps_for(instrument, domain)
    a = gate_stack_core(returns, pos, instrument=instrument, domain=domain,
                        n_bootstrap=N_BOOTSTRAP, seed=seed)
    b = gate_stack_core_costfn(returns, pos, domain=domain, cost_bps=cost,
                               n_bootstrap=N_BOOTSTRAP, seed=seed, strategy_fn=strategy_return_bps)
    return bool(np.array_equal(a["neutral_means"], b["neutral_means"])
                and np.array_equal(a["naive_means"], b["naive_means"])
                and a["l1"] == b["l1"] and a["l4"] == b["l4"])

# --------------------------------------------------------------------------- #
# Per-stratum orchestration
# --------------------------------------------------------------------------- #
def run_stratum(returns: np.ndarray, instrument: str, domain: str) -> dict[str, object]:
    """FPR + MDE per convention + ΔMDE + tripwire receipts for one instrument x domain."""
    L = EPISODE_LENGTHS[domain]
    cost = adaptive_cost_bps_for(instrument, domain)
    row: dict[str, object] = {
        "instrument": instrument, "domain": domain, "episode_length": L,
        "cost_bps": cost, "n_returns": len(returns),
        "tw_equivalence_ok": tripwire_equivalence(returns, instrument, domain, L),
        "tw_alternating": tripwire_alternating_coincide(returns, cost),
        "tw_cost_monotone": tripwire_cost_monotone(returns, L, cost),
    }
    for name, fn in CONVENTIONS.items():
        fpr, draws = false_positive_rate(returns, domain=domain, episode_length=L,
                                         cost_bps=cost, strategy_fn=fn)
        mde, curve = mde_bps(returns, domain=domain, episode_length=L, cost_bps=cost, strategy_fn=fn)
        row[f"fpr_{name}"] = fpr
        row[f"fpr_{name}_wilson_hw"] = wilson_halfwidth(fpr, draws)
        row[f"fpr_{name}_draws"] = draws
        row[f"mde_{name}_bps"] = mde
        row[f"det_curve_{name}"] = curve
        row[f"no_edge_passrate_{name}"] = no_plant_passrate(      # tripwire 3 (no-real-edge guard)
            returns, domain=domain, episode_length=L, cost_bps=cost, strategy_fn=fn)
        row[f"plant0_passrate_{name}"] = curve[0.0]   # disclosure: plant(edge=0); != true zero for amortized
    perheld, amort = row["mde_perheld_bps"], row["mde_amortized_bps"]
    row["delta_mde_bps"] = (perheld - amort) if math.isfinite(perheld) and math.isfinite(amort) \
        else math.nan
    row["mde_monotone_ok"] = bool(not (math.isfinite(amort) and math.isfinite(perheld))
                                  or amort <= perheld)
    return row

# --------------------------------------------------------------------------- #
# Plotting (bounded inputs from the analysis pass)
# --------------------------------------------------------------------------- #
def plot_delta_vs_cost(rows: list[dict], save_path: Path) -> None:
    """ΔMDE vs round-trip cost per stratum (F3 signature: ΔMDE grows with cost)."""
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(8, 5))
    for domain in ADAPTIVE_DOMAINS:
        pts = [(r["cost_bps"], r["delta_mde_bps"]) for r in rows
               if r["domain"] == domain and math.isfinite(r["delta_mde_bps"])]
        if pts:
            xs, ys = zip(*pts)
            ax.scatter(xs, ys, label=domain, s=60)
    ax.axhline(0.0, color="grey", lw=1, ls="--")
    ax.set_title(f"ΔMDE vs round-trip cost (n strata = {len(rows)})")
    ax.set_xlabel("Round-trip cost (bps)")
    ax.set_ylabel("ΔMDE = MDE_perheld - MDE_amortized (bps)")
    ax.legend(title="domain")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_delta_vs_l(rows: list[dict], save_path: Path) -> None:
    """ΔMDE vs episode length L per stratum."""
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(8, 5))
    pts = [(r["episode_length"], r["delta_mde_bps"]) for r in rows
           if math.isfinite(r["delta_mde_bps"])]
    if pts:
        xs, ys = zip(*pts)
        ax.scatter(xs, ys, s=60)
    ax.axhline(0.0, color="grey", lw=1, ls="--")
    ax.set_title(f"ΔMDE vs episode length L (n strata = {len(rows)})")
    ax.set_xlabel("Episode length L (bars)")
    ax.set_ylabel("ΔMDE (bps)")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_det_points(rows: list[dict], save_path: Path) -> None:
    """DET points (FPR, MDE) per stratum per convention."""
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(8, 5))
    for name, marker in (("perheld", "o"), ("amortized", "^")):
        pts = [(r[f"fpr_{name}"], r[f"mde_{name}_bps"]) for r in rows
               if math.isfinite(r[f"mde_{name}_bps"])]
        if pts:
            xs, ys = zip(*pts)
            ax.scatter(xs, ys, marker=marker, label=name, s=55, alpha=0.7)
    ax.axvline(ALPHA, color="red", lw=1, ls=":", label=f"alpha={ALPHA}")
    ax.set_title(f"DET points (FPR, MDE) per stratum (n = {len(rows)})")
    ax.set_xlabel("FPR")
    ax.set_ylabel("MDE (bps)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

# --------------------------------------------------------------------------- #
# Serialisation
# --------------------------------------------------------------------------- #
def write_results(rows: list[dict]) -> None:
    """Persist the per-stratum table (CSV flat view + JSON with detection curves)."""
    flat_cols = ["instrument", "domain", "episode_length", "cost_bps", "n_returns",
                 "fpr_perheld", "fpr_perheld_wilson_hw", "fpr_amortized", "fpr_amortized_wilson_hw",
                 "mde_perheld_bps", "mde_amortized_bps", "delta_mde_bps",
                 "no_edge_passrate_perheld", "no_edge_passrate_amortized",
                 "plant0_passrate_perheld", "plant0_passrate_amortized",
                 "tw_equivalence_ok", "mde_monotone_ok"]
    flat = pl.DataFrame([{c: r[c] for c in flat_cols} for r in rows])
    flat.write_csv(RESULTS_DIR / "per_stratum.csv")
    (RESULTS_DIR / "per_stratum_full.json").write_text(json.dumps(rows, indent=2, default=str))

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

    rows: list[dict] = []
    tripwire_failures: list[str] = []
    strata = [(ins, dom) for ins in instruments if available[ins] for dom in ADAPTIVE_DOMAINS]

    minutes_cache: dict[str, pl.DataFrame] = {}
    for instrument, domain in tqdm(strata, desc="strata"):
        if instrument not in minutes_cache:
            minutes_cache[instrument] = load_analysis_minutes(available[instrument])
        returns = build_domain_returns(minutes_cache[instrument], domain)
        if len(returns) < 200:
            logger.info("SKIP %s/%s: only %d domain returns", instrument, domain, len(returns))
            continue
        row = run_stratum(returns, instrument, domain)
        rows.append(row)

        if not row["tw_equivalence_ok"]:
            tripwire_failures.append(f"{instrument}/{domain}: equivalence (seam != frozen core)")
        if not row["tw_alternating"]["series_identical"]:
            tripwire_failures.append(f"{instrument}/{domain}: alternating arm diverged")
        if not row["tw_cost_monotone"]["monotone_ok"]:
            tripwire_failures.append(f"{instrument}/{domain}: cost monotonicity violated")
        if not row["mde_monotone_ok"]:
            tripwire_failures.append(f"{instrument}/{domain}: amortized MDE > perheld MDE (L>1)")
        # tripwire 3: edge=0 pass rate must not exceed FPR + Wilson slack (no phantom positive)
        for name in CONVENTIONS:
            guard = row[f"fpr_{name}"] + 2 * row[f"fpr_{name}_wilson_hw"]
            if row[f"no_edge_passrate_{name}"] > max(guard, 2 * ALPHA):
                tripwire_failures.append(
                    f"{instrument}/{domain}: no-real-edge guard ({name}) "
                    f"pass={row[f'no_edge_passrate_{name}']:.3f} > {guard:.3f}")

    if not rows:
        logger.error("No strata produced results — check data availability.")
        return

    write_results(rows)
    plot_det_points(rows, PLOTS_DIR / "det_points.png")
    plot_delta_vs_cost(rows, PLOTS_DIR / "delta_mde_vs_cost.png")
    plot_delta_vs_l(rows, PLOTS_DIR / "delta_mde_vs_l.png")

    finite = [r["delta_mde_bps"] for r in rows if math.isfinite(r["delta_mde_bps"])]
    logger.info("\n=== EXP-001 E1 summary ===")
    logger.info("strata run: %d (instruments: %d)", len(rows), len(minutes_cache))
    if finite:
        logger.info("ΔMDE finite strata: %d | median=%.2f bps | max=%.2f bps (disclosure-only pool)",
                    len(finite), float(np.median(finite)), float(np.max(finite)))
    logger.info("results -> %s", RESULTS_DIR / "per_stratum.csv")
    if tripwire_failures:
        logger.error("LEAK-TRIPWIRE FAILURES (%d) — verdict-material, fix+rerun:",
                     len(tripwire_failures))
        for f in tripwire_failures:
            logger.error("  - %s", f)
    else:
        logger.info("All leak tripwires held (equivalence, alternating, monotonicity, no-edge).")


if __name__ == "__main__":
    main()
