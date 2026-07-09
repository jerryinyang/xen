"""
Experiment EXP-007 (E6): P*-capable Referee Variant — calibration harness.

Implements python/experiments/EXP-007/design.md (GATE: APPROVE). ANALYSIS-ONLY: synthetic position
substrates + the engine-realized-fill analog (`referee_pstar.make_realized_fill`) on the frozen E0
primitives (open-to-open <=t-1 returns, 17-instrument cost map). No price->signal. First-70% slice;
global holdout never loaded. 0 reads / 0 slots.

Three arms per stratum (instrument x {1h,4h}, the EXP-002 32-cell grid), per-stratum binding (L-03):
  R  regression anchor — realized := strategy_return_bps_turnover(returns, positions): the P*-capable
     gate (gate_stack_pstar + adaptive_row) must reproduce §10.3a (gate_stack_adaptive + adaptive_row)
     BIT-IDENTICALLY, and the frozen modules' byte-hashes must be unchanged. (T3)
  N  realized-fill FPR nulls — N1 symmetric bracket (fav=adv) on block-permuted no-edge returns (T1,
     must REJECT); N2 future-destroyed realized (T2, must collapse); N3 dogfood-negative routed through
     the realized path. FPR Wilson-bounded + draw counts; success: FPR <= §10.3a dogfood FPR.
  P  synthetic-positive — a planted directional edge realized through a wide favourable bracket; the
     gate must keep FINITE POWER (MDE). NOTE (honest caveat): in returns-space the bracket CAPS, it
     cannot capture an intrabar excursion the close misses, so realized <= position-state magnitude;
     Arm P validates the new PATH's finite power on a realized series — true intrabar capture is
     exercised by the real cTrader engine in EXP-006, not here.
"""
from __future__ import annotations

import hashlib
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
    adaptive_row,
    gate_stack_adaptive,
    next_open_to_open_returns_from_bars,
    strategy_return_bps_turnover,
)
from xen.referee_calibration import (
    EDGE_GRID_BPS,
    donchian_breakout_positions,
    ma_crossover_positions,
    permuted_returns,
    wilson_interval,
)
from xen.referee_pstar import (
    gate_stack_pstar,
    gate_stack_pstar_reduces_to_adaptive,
    make_realized_fill,
)
from xen.incremental_referee import EPISODE_LENGTHS

# EXP-002 edge-shape substrate (reused verbatim — the frozen synthetic battery).
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "EXP-002" / "code"))
from edge_shapes import (  # noqa: E402
    dense_planted,
    persistent_positions,
    sparse_positions,
    state_dependent_planted,
    state_positions,
)

logger = logging.getLogger("EXP-007")

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
DATA_DIR = Path("data")
EXP_DIR = Path("python/experiments/EXP-007")
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"
FROZEN_MODULES = (
    Path("python/src/xen/referee_adaptive.py"),
    Path("python/src/xen/referee_calibration.py"),
)

ANALYSIS_FRACTION = 0.70
ERA_GLOB = "20210602_*"           # 2021-era files = the EXP-002/E3a/E4/E5 32-strata grid
PERIOD_MINUTES = {"1h": 60, "4h": 240}
DOMAIN_MIN_COVERAGE = 0.90

ALPHA = 0.05
N_BOOTSTRAP = 500
N_NULL = 80                       # null draws per realized-fill null substrate (per stratum)
N_PLANT = 20                      # planted-positive seeds per edge level
POWER_TARGET = 0.50
BRACKET_FAV_NULL_BPS = 15.0       # N1 symmetric bracket half-width (fav=adv); calibration constant
BRACKET_FAV_POS_BPS = 60.0        # Arm-P wide favourable bracket (passes planted drift; caps tails)
BRACKET_ADV_POS_BPS = 60.0
# §10.3a dogfood-negative FPR anchor (E2/E4): 0/32 -> the per-stratum success bound is 0 passes.
DOGFOOD_FPR_ANCHOR = 0.0


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
    """Open-to-open <=t-1 returns + the aligned fenced domain frame (real OHLC for dogfood)."""
    dom = aggregate_ohlc(minutes, period_minutes=PERIOD_MINUTES[domain],
                         min_coverage=DOMAIN_MIN_COVERAGE)
    dom = dom.filter(pl.col("CloseTime") <= minutes.get_column("CloseTime").max())
    return next_open_to_open_returns_from_bars(dom)


def module_hashes() -> dict[str, str]:
    """SHA-256 of the frozen referee modules — must be unchanged across the run (T3 byte-freeze)."""
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in FROZEN_MODULES}


# --------------------------------------------------------------------------- #
# Pure helpers
# --------------------------------------------------------------------------- #
def lag_open_to_open(positions: np.ndarray) -> np.ndarray:
    """Lag a close-indexed signal one bar so it acts at the NEXT bar's open (confirmed <=t-1)."""
    pos = np.asarray(positions, dtype=float)
    return np.concatenate(([0.0], pos[:-1]))


def pstar_passes(returns: np.ndarray, positions: np.ndarray, realized_bps: np.ndarray, *,
                 domain: str, cost_bps: float, seed: int) -> bool:
    """True iff the P*-capable gate (gate_stack_pstar + adaptive_row) PASSES one draw."""
    core = gate_stack_pstar(returns, positions, realized_bps, domain=domain, cost_bps=cost_bps,
                            n_bootstrap=N_BOOTSTRAP, seed=seed)
    return bool(adaptive_row(core, alpha=ALPHA)["passed"])


def planted_reversion_realized(returns: np.ndarray, *, episode_length: int, net_edge_bps: float,
                               cost_bps: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Arm-P substrate: a planted directional edge realized through a wide favourable bracket.

    Positions = persistent fade states; the planted drift (dense_planted) gives held bars positive
    directional expectancy; make_realized_fill passes the drift through a wide bracket (caps only
    extreme tails). Returns (positions, realized_bps).
    """
    pos = persistent_positions(len(returns), episode_length, seed)
    planted = dense_planted(returns, pos, net_edge_bps=net_edge_bps, cost_bps=cost_bps)
    realized = make_realized_fill(planted, pos, fav_limit_bps=BRACKET_FAV_POS_BPS,
                                  adv_limit_bps=BRACKET_ADV_POS_BPS, cost_bps=cost_bps)
    return pos, realized


# --------------------------------------------------------------------------- #
# Arm R — regression anchor (reduction identity + verdict agreement + byte-freeze)
# --------------------------------------------------------------------------- #
def arm_r(returns: np.ndarray, *, domain: str, cost_bps: float) -> dict[str, object]:
    """Per-stratum reduction identity: pstar(realized:=turnover) == §10.3a, core + verdict."""
    pos = persistent_positions(len(returns), EPISODE_LENGTHS[domain], seed=101)
    core_identical = gate_stack_pstar_reduces_to_adaptive(
        returns, pos, domain=domain, cost_bps=cost_bps, n_bootstrap=N_BOOTSTRAP, seed=202)
    a = adaptive_row(gate_stack_adaptive(returns, pos, domain=domain, cost_bps=cost_bps,
                                         n_bootstrap=N_BOOTSTRAP, seed=202), alpha=ALPHA)
    realized = strategy_return_bps_turnover(returns, pos, cost_bps=cost_bps)
    b = adaptive_row(gate_stack_pstar(returns, pos, realized, domain=domain, cost_bps=cost_bps,
                                      n_bootstrap=N_BOOTSTRAP, seed=202), alpha=ALPHA)
    return {"core_identical": bool(core_identical), "verdict_identical": bool(a == b),
            "verdict_adaptive": a["verdict"], "verdict_pstar": b["verdict"]}


# --------------------------------------------------------------------------- #
# Arm N — realized-fill FPR nulls (T1 symmetric, T2 future-destroy, N3 dogfood)
# --------------------------------------------------------------------------- #
def _fpr(passes: int, draws: int) -> tuple[float, float, int]:
    _, lo, hi = wilson_interval(passes, draws)
    return passes / draws, (hi - lo) / 2.0, draws


def arm_n_symmetric(returns: np.ndarray, *, domain: str, cost_bps: float) -> tuple[float, float, int]:
    """N1 (T1): matched fav=adv bracket on block-permuted no-edge returns -> gate must REJECT."""
    n, L = len(returns), EPISODE_LENGTHS[domain]
    passes = 0
    for k in range(N_NULL):
        pr = permuted_returns(returns, seed=1100 + k)
        pos = persistent_positions(n, L, 2100 + k)
        realized = make_realized_fill(pr, pos, fav_limit_bps=BRACKET_FAV_NULL_BPS,
                                      adv_limit_bps=BRACKET_FAV_NULL_BPS, cost_bps=cost_bps)
        passes += pstar_passes(pr, pos, realized, domain=domain, cost_bps=cost_bps, seed=3100 + k)
    return _fpr(passes, N_NULL)


def arm_n_future_destroyed(returns: np.ndarray, *, domain: str, cost_bps: float
                           ) -> tuple[float, float, int]:
    """N2 (T2): plant a positive edge, BLOCK-PERMUTE the market returns (destroy position<->return
    alignment, L-07), THEN realize the fill on the destroyed returns -> must collapse to FPR.

    Destroying at the *input* (returns) is the correct future-destroy: a resting bracket on
    misaligned returns has no systematic edge. (Permuting the realized P&L series instead would
    preserve its mean and never collapse — not a valid control.)
    """
    n, L = len(returns), EPISODE_LENGTHS[domain]
    passes = 0
    for k in range(N_NULL):
        pos = persistent_positions(n, L, seed=6100 + k)
        planted = dense_planted(returns, pos, net_edge_bps=EDGE_GRID_BPS[-1], cost_bps=cost_bps)
        destroyed_ret = permuted_returns(planted, seed=8100 + k)   # break position<->return alignment
        realized = make_realized_fill(destroyed_ret, pos, fav_limit_bps=BRACKET_FAV_POS_BPS,
                                      adv_limit_bps=BRACKET_ADV_POS_BPS, cost_bps=cost_bps)
        passes += pstar_passes(destroyed_ret, pos, realized, domain=domain, cost_bps=cost_bps,
                               seed=3300 + k)
    return _fpr(passes, N_NULL)


def arm_n_dogfood(returns: np.ndarray, aligned: pl.DataFrame, *, domain: str, cost_bps: float
                  ) -> tuple[float, float, int]:
    """N3: real known-null signals (Donchian R, MA 20/50) routed through the realized path -> reject."""
    close = aligned.get_column("Close").to_numpy()
    high = aligned.get_column("High").to_numpy()
    low = aligned.get_column("Low").to_numpy()
    passes, draws = 0, 0
    for tag, raw in (("don", donchian_breakout_positions(high, low, close, lookback=20)),
                     ("ma", ma_crossover_positions(close, fast=20, slow=50))):
        pos = lag_open_to_open(raw)
        # Donchian drops its last bar (no next return); align market-returns + positions to the
        # common length before the exact-alignment realized fill (same truncation the gate applies).
        m = min(len(returns), len(pos))
        ret_m, pos_m = returns[:m], pos[:m]
        realized = make_realized_fill(ret_m, pos_m, fav_limit_bps=BRACKET_FAV_NULL_BPS,
                                      adv_limit_bps=BRACKET_FAV_NULL_BPS, cost_bps=cost_bps)
        passes += pstar_passes(ret_m, pos_m, realized, domain=domain, cost_bps=cost_bps,
                               seed=9100 + (0 if tag == "don" else 1))
        draws += 1
    return _fpr(passes, draws)


# --------------------------------------------------------------------------- #
# Arm P — synthetic-positive realized power (MDE curve)
# --------------------------------------------------------------------------- #
def arm_p_mde(returns: np.ndarray, *, domain: str, cost_bps: float) -> tuple[float, dict[float, float]]:
    """DETECTED_FLOOR MDE for the realized-fill positive (first e>0 with power>=POWER_TARGET)."""
    L = EPISODE_LENGTHS[domain]
    curve: dict[float, float] = {}
    mde = math.inf
    for edge in EDGE_GRID_BPS:
        passes = 0
        for k in range(N_PLANT):
            pos, realized = planted_reversion_realized(returns, episode_length=L, net_edge_bps=edge,
                                                       cost_bps=cost_bps, seed=6500 + k)
            passes += pstar_passes(returns, pos, realized, domain=domain, cost_bps=cost_bps,
                                   seed=7500 + k)
        rate = passes / N_PLANT
        curve[edge] = rate
        if math.isinf(mde) and edge > 0.0 and rate >= POWER_TARGET:
            mde = edge
    return mde, curve


# --------------------------------------------------------------------------- #
# Per-stratum orchestration
# --------------------------------------------------------------------------- #
def run_stratum(returns: np.ndarray, aligned: pl.DataFrame, instrument: str, domain: str
                ) -> dict[str, object]:
    """All three arms for one instrument x domain stratum."""
    cost = adaptive_cost_bps_for(instrument, domain)
    r = arm_r(returns, domain=domain, cost_bps=cost)
    n1_fpr, n1_hw, n1_d = arm_n_symmetric(returns, domain=domain, cost_bps=cost)
    n2_fpr, n2_hw, n2_d = arm_n_future_destroyed(returns, domain=domain, cost_bps=cost)
    n3_fpr, n3_hw, n3_d = arm_n_dogfood(returns, aligned, domain=domain, cost_bps=cost)
    p_mde, p_curve = arm_p_mde(returns, domain=domain, cost_bps=cost)
    return {
        "instrument": instrument, "domain": domain, "cost_bps": cost, "n_returns": len(returns),
        "R_core_identical": r["core_identical"], "R_verdict_identical": r["verdict_identical"],
        "R_verdict_adaptive": r["verdict_adaptive"], "R_verdict_pstar": r["verdict_pstar"],
        "N1_sym_fpr": n1_fpr, "N1_sym_hw": n1_hw, "N1_draws": n1_d,
        "N2_futuredestroy_fpr": n2_fpr, "N2_hw": n2_hw, "N2_draws": n2_d,
        "N3_dogfood_fpr": n3_fpr, "N3_hw": n3_hw, "N3_draws": n3_d,
        "P_mde_bps": p_mde, "P_curve": p_curve,
    }


# --------------------------------------------------------------------------- #
# Plotting (bounded inputs)
# --------------------------------------------------------------------------- #
def plot_arm_r(rows: list[dict], save_path: Path) -> None:
    """Arm-R agreement: count of strata with bit-identical core + verdict (target = all)."""
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(6, 4))
    n = len(rows)
    core = sum(r["R_core_identical"] for r in rows)
    verdict = sum(r["R_verdict_identical"] for r in rows)
    ax.bar(["core identical", "verdict identical"], [core, verdict], color=["#2c7", "#27c"])
    ax.axhline(n, color="red", ls="--", lw=1, label=f"all strata ({n})")
    ax.set_ylim(0, n + 1)
    ax.set_title(f"Arm R — reduction identity to §10.3a ({n} strata)")
    ax.set_ylabel("strata")
    ax.legend()
    fig.tight_layout(); fig.savefig(save_path, dpi=150, bbox_inches="tight"); plt.close(fig)


def plot_arm_n_fpr(rows: list[dict], save_path: Path) -> None:
    """Arm-N FPR per stratum (N1/N2/N3) with Wilson half-width; success bound = §10.3a dogfood 0."""
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(11, 5))
    labels = [f"{r['instrument']}/{r['domain']}" for r in rows]
    x = np.arange(len(labels))
    for off, key, hw, lab in ((-0.2, "N1_sym_fpr", "N1_sym_hw", "N1 symmetric"),
                              (0.0, "N2_futuredestroy_fpr", "N2_hw", "N2 future-destroy"),
                              (0.2, "N3_dogfood_fpr", "N3_hw", "N3 dogfood")):
        ax.errorbar(x + off, [r[key] for r in rows], yerr=[r[hw] for r in rows], fmt="o",
                    capsize=2, label=lab, markersize=4)
    ax.axhline(2 * ALPHA, color="red", ls="--", lw=1, label=f"control bound {2*ALPHA}")
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=90, fontsize=7)
    ax.set_title("Arm N — realized-fill null FPR per stratum (Wilson)")
    ax.set_ylabel("FPR"); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(save_path, dpi=150, bbox_inches="tight"); plt.close(fig)


def plot_arm_p(rows: list[dict], save_path: Path) -> None:
    """Arm-P MDE distribution across strata (UNPOWERED annotated)."""
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(7, 5))
    by_dom = {d: [r["P_mde_bps"] for r in rows if r["domain"] == d] for d in ADAPTIVE_DOMAINS}
    data = [[v for v in by_dom[d] if math.isfinite(v)] for d in ADAPTIVE_DOMAINS]
    unp = [sum(math.isinf(v) for v in by_dom[d]) for d in ADAPTIVE_DOMAINS]
    ax.boxplot(data, labels=[f"{d}\n(UNPWR {u})" for d, u in zip(ADAPTIVE_DOMAINS, unp)])
    ax.set_title("Arm P — realized-fill positive MDE by domain (finite = powered)")
    ax.set_ylabel("MDE (bps)")
    fig.tight_layout(); fig.savefig(save_path, dpi=150, bbox_inches="tight"); plt.close(fig)


# --------------------------------------------------------------------------- #
# Serialisation
# --------------------------------------------------------------------------- #
def write_results(rows: list[dict], hashes_before: dict, hashes_after: dict) -> None:
    """Persist per-stratum table (CSV flat + JSON full) + the byte-freeze record."""
    flat = ["instrument", "domain", "cost_bps", "n_returns", "R_core_identical",
            "R_verdict_identical", "N1_sym_fpr", "N2_futuredestroy_fpr", "N3_dogfood_fpr", "P_mde_bps"]
    pl.DataFrame([{c: r[c] for c in flat} for r in rows]).write_csv(RESULTS_DIR / "per_stratum.csv")
    (RESULTS_DIR / "per_stratum_full.json").write_text(json.dumps(rows, indent=2, default=str))
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
    strata = [(ins, dom) for ins in instruments if available[ins] for dom in ADAPTIVE_DOMAINS]
    if smoke:
        strata = strata[:2]
        logger.info("SMOKE: %d strata", len(strata))

    rows: list[dict] = []
    minutes_cache: dict[str, pl.DataFrame] = {}
    for instrument, domain in tqdm(strata, desc="strata"):
        if instrument not in minutes_cache:
            minutes_cache[instrument] = load_analysis_minutes(available[instrument])
        returns, aligned = build_domain(minutes_cache[instrument], domain)
        if len(returns) < 200:
            logger.info("SKIP %s/%s: only %d domain returns", instrument, domain, len(returns))
            continue
        rows.append(run_stratum(returns, aligned, instrument, domain))

    if not rows:
        logger.error("No strata produced results — check data availability.")
        return

    hashes_after = module_hashes()
    write_results(rows, hashes_before, hashes_after)
    plot_arm_r(rows, PLOTS_DIR / "arm_r_agreement.png")
    plot_arm_n_fpr(rows, PLOTS_DIR / "arm_n_fpr.png")
    plot_arm_p(rows, PLOTS_DIR / "arm_p_mde.png")

    # --- Adoption summary + leak tripwires (blocking) ---
    n = len(rows)
    r_core = sum(r["R_core_identical"] for r in rows)
    r_verd = sum(r["R_verdict_identical"] for r in rows)
    n1_max = max(r["N1_sym_fpr"] for r in rows)
    n2_max = max(r["N2_futuredestroy_fpr"] for r in rows)
    n3_max = max(r["N3_dogfood_fpr"] for r in rows)
    p_powered = sum(math.isfinite(r["P_mde_bps"]) for r in rows)
    bound = 2 * ALPHA
    logger.info("\n=== EXP-007 E6 summary (%d strata) ===", n)
    logger.info("Arm R  core_identical=%d/%d  verdict_identical=%d/%d  (target %d/%d)",
                r_core, n, r_verd, n, n, n)
    logger.info("Arm R  frozen modules unchanged: %s", hashes_before == hashes_after)
    logger.info("Arm N  FPR max: N1_sym=%.3f  N2_futuredestroy=%.3f  N3_dogfood=%.3f (bound %.2f)",
                n1_max, n2_max, n3_max, bound)
    logger.info("Arm P  powered strata (finite MDE): %d/%d", p_powered, n)

    tripwires: list[str] = []
    if r_core != n or r_verd != n:
        tripwires.append(f"Arm-R reduction identity NOT 32/32 (core {r_core}, verdict {r_verd})")
    if hashes_before != hashes_after:
        tripwires.append("frozen referee module byte-hash CHANGED during run")
    for r in rows:
        for key, lab in (("N1_sym_fpr", "N1 symmetric"), ("N2_futuredestroy_fpr", "N2 future-destroy"),
                         ("N3_dogfood_fpr", "N3 dogfood")):
            if r[key] - r.get(key.replace("_fpr", "_hw"), 0.0) > bound:
                tripwires.append(f"{r['instrument']}/{r['domain']}: {lab} FPR {r[key]:.3f} > {bound}")
    if tripwires:
        logger.error("LEAK-TRIPWIRE / IDENTITY FAILURES (%d) — verdict-material, fix+rerun:",
                     len(tripwires))
        for t in tripwires:
            logger.error("  - %s", t)
    else:
        logger.info("All tripwires held: reduction identity 32/32, byte-freeze intact, "
                    "realized-fill nulls FPR-controlled.")
    logger.info("results -> %s", RESULTS_DIR / "per_stratum.csv")


if __name__ == "__main__":
    main()
