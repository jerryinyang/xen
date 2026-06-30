"""
Experiment EXP-006 (D-benchmark): causal RSI-2 fade CF-MR-002/HYP-001 — adjudication harness.

PRICE-PRIMARY, ANALYSIS-ONLY SIDE. The edge is generated in the cTrader StrategyHost
(`StrategyHost/RsiFadeModel.cs`, strategy `rsi2_fade_causal`) and emitted to
`data/strategy_runs/EXP-006/<run>/positions.parquet` under the per-symbol AnalysisEndUtc fence. This
harness *only ingests + validates + adjudicates* those emissions — it never (re)generates a signal,
an entry, or a fill (a vectorized Python backtest of this fade is REJECT, L-01). The realized exit
fill is the engine's emitted `ExitFillPrice` (= P*_{t-1}); no Python `rct` recompute (P-09 clean).

Each instrument x domain stratum is adjudicated under THREE referees, side-by-side (parallel
disclosure, cf-mr-002 §referee; per-stratum binding, L-03):
  A  Frozen Chapter-01 suite  (referee_calibration.evaluate_referees) — close-to-close, position-
     state proxy (its native convention; has no fill channel — disclosed as-is).
  B  Renewed adaptive gate §10.3a (referee_adaptive.gate_stack_adaptive + adaptive_row) — open-to-
     open <=t-1, position-state proxy (`position * market-return`).
  C  E6 P*-capable gate (referee_pstar.gate_stack_pstar + adaptive_row, FROZEN
     EXP-007/results/freeze_manifest.json) — open-to-open <=t-1, signal leg = the ENGINE-REALIZED P*
     fill series (the faithful, binding adjudication). gate_stack_pstar is §10.3a with one source swap.

Leak tripwires (mandatory; blocking — L-01 layer 3):
  T1  entry/return future-destroy — block-permute the o2o market returns (L-07: permute the INPUT,
      not the P&L) and re-adjudicate the position-state edge; the gate MUST collapse (FPR ~ 0) on
      every cell. (gate_stack_pstar with realized:=turnover reduces to §10.3a, EXP-007 Arm R, so the
      realized gate inherits this collapse; the realized-fill-only leak class — favourable-only
      truncation — was certified by EXP-007 N1 symmetric 0/32.)
  T2  causal-provenance trace (structural) — the realized series derives only from emitted RealOpen +
      ExitFillPrice (a limit placed before the bar opened); no Python rct[di] favourable-index pass
      exists. Asserted by construction (the engine + HoldoutFence) and re-derived here.

Honest prior (cf-mr-002, L-01): NOT-TRADABLE — causalized, the bare fade is net-negative even gross.
0 counted TEST reads / 0 candidate slots; global holdout sealed (emissions fenced at AnalysisEndUtc).
A NET-TRADABLE surprise on any cell is an operator critical-decision (deployability-adjacent) before
any further step — this harness spends no read and makes no deployment claim.
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

from xen.referee_adaptive import (
    ADAPTIVE_DOMAINS,
    adaptive_cost_bps_for,
    adaptive_row,
    gate_stack_adaptive,
    strategy_return_bps_turnover,
)
from xen.referee_calibration import permuted_returns, seed_for, wilson_interval
from xen.referee_pstar import gate_stack_pstar
from xen.signals.ingestion import (
    assert_run_within_holdout,
    load_emitted_run,
    returns_and_positions,
    returns_and_positions_realized,
    screen_emitted_positions,
)

logger = logging.getLogger("EXP-006")

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
EXP_DIR = Path("python/experiments/EXP-006")
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"
STRATEGY_RUNS_DIR = Path("data/strategy_runs/EXP-006")
STRATEGY = "rsi2_fade_causal"

ALPHA = 0.05
N_BOOTSTRAP = 500              # frozen E-series operating point
N_PERM = 80                    # T1 future-destroy draws per cell
MIN_DOMAIN_RETURNS = 200       # below this a cell is UNPOWERED (too short to adjudicate)


# --------------------------------------------------------------------------- #
# I/O helpers (orchestration-only)
# --------------------------------------------------------------------------- #
def discover_runs(runs_dir: Path) -> list[Path]:
    """Strategy-host run directories (each holds positions.parquet) for this experiment."""
    if not runs_dir.exists():
        return []
    return sorted(p for p in runs_dir.iterdir() if p.is_dir() and (p / "positions.parquet").exists())


def run_identity(run) -> tuple[str, str]:
    """(instrument, domain) for a loaded run, from metadata + the emitted Domain column."""
    instrument = str(run.metadata.get("symbol", "")).upper()
    domain = str(run.positions.get_column("Domain")[0])
    return instrument, domain


# --------------------------------------------------------------------------- #
# Pure helpers
# --------------------------------------------------------------------------- #
def frozen_gate_row(positions: pl.DataFrame, *, instrument: str, domain: str, seed: int) -> dict:
    """Gate-A frozen Chapter-01 suite verdict (close-to-close, position-state proxy).

    The frozen suite's cost map (`referee_calibration.ROUND_TRIP_COST_BPS`) covers only its native
    4-core (EURUSD/XAUUSD/BTCUSD/USTEC); it is byte-frozen and cannot be extended. For the other 13
    instruments gate A is structurally UNAVAILABLE (cost-map gap) — recorded as `N/A_FROZEN_COSTMAP`,
    a disclosure, not a fail. Gates B/C (renewed §10.3a, E0 17-instrument map) cover all 17.
    """
    try:
        rows = screen_emitted_positions(positions, instrument=instrument, domain=domain, seed=seed,
                                        alpha_values=(ALPHA,), n_bootstrap=N_BOOTSTRAP)
        return next(r for r in rows if r["referee"] == "gate_stack")
    except KeyError:
        return {"referee": "gate_stack", "verdict": "N/A_FROZEN_COSTMAP", "passed": False,
                "ci_lower_bps": float("nan")}


def adaptive_proxy_row(returns: np.ndarray, positions: np.ndarray, *, domain: str, cost_bps: float,
                       seed: int) -> dict:
    """Gate-B §10.3a verdict on the position-state proxy (open-to-open, `position*market-return`)."""
    core = gate_stack_adaptive(returns, positions, domain=domain, cost_bps=cost_bps,
                               n_bootstrap=N_BOOTSTRAP, seed=seed)
    return adaptive_row(core, alpha=ALPHA)


def pstar_realized_row(returns: np.ndarray, positions: np.ndarray, realized_bps: np.ndarray, *,
                       domain: str, cost_bps: float, seed: int) -> dict:
    """Gate-C E6 P*-capable verdict on the ENGINE-REALIZED fill series (faithful, binding)."""
    core = gate_stack_pstar(returns, positions, realized_bps, domain=domain, cost_bps=cost_bps,
                            n_bootstrap=N_BOOTSTRAP, seed=seed)
    return adaptive_row(core, alpha=ALPHA)


def t1_future_destroy_fpr(returns: np.ndarray, positions: np.ndarray, *, domain: str, cost_bps: float,
                          seed: int) -> tuple[float, float, int]:
    """T1: block-permute the o2o market returns (L-07) and re-adjudicate the position-state edge.

    The gate MUST collapse — a permuted (signal<->outcome misaligned) series has no systematic edge.
    Returns ``(fpr, wilson_halfwidth, draws)``. gate_stack_pstar(realized:=turnover) == §10.3a
    (EXP-007 Arm R), so this binds the realized gate too.
    """
    passes = 0
    for k in range(N_PERM):
        perm = permuted_returns(returns, seed=seed + 1 + k)
        core = gate_stack_adaptive(perm, positions, domain=domain, cost_bps=cost_bps,
                                   n_bootstrap=N_BOOTSTRAP, seed=seed + 5000 + k)
        passes += bool(adaptive_row(core, alpha=ALPHA)["passed"])
    _, lo, hi = wilson_interval(passes, N_PERM)
    return passes / N_PERM, (hi - lo) / 2.0, N_PERM


def t2_provenance_ok(positions: pl.DataFrame, realized_bps: np.ndarray, returns: np.ndarray,
                     pos: np.ndarray, *, cost_bps: float) -> bool:
    """T2 (structural): the realized series departs from the position-state proxy ONLY on engine
    exit bars (ExitFillPrice non-NaN), and nowhere else. Confirms no Python favourable-index pass —
    every non-exit bar's realized value equals strategy_return_bps_turnover (the engine fill is the
    only extra information). A mismatch on a NON-exit bar would mean an injected Python fill (P-09).
    """
    proxy = strategy_return_bps_turnover(returns, pos, cost_bps=cost_bps)
    exit_fill = positions.sort("SourceCloseTime").get_column("ExitFillPrice").to_numpy()[: len(pos)]
    non_exit = np.isnan(exit_fill) | (pos == 0.0)
    return bool(np.allclose(realized_bps[non_exit], proxy[non_exit], equal_nan=True))


def classify(gate_c: dict, t1_fpr: float, t1_hw: float, t2_ok: bool, *, powered: bool) -> str:
    """Predeclared per-cell interpretation on the binding faithful gate (C), with the tripwires."""
    if not t2_ok:
        return "INVALID"                                   # provenance leak (P-09) -> REJECT-class
    if (t1_fpr - t1_hw) > 0.0:
        return "INVALID"                                   # T1 did not collapse -> leak -> REJECT
    if not powered or not gate_c["leg_results_l1"]:
        return "UNPOWERED"                                 # no finite power / L1 veto (L-04, not FAIL)
    if gate_c["passed"] and gate_c["ci_lower_bps"] > 0.0:
        return "NET-TRADABLE"                              # surprise vs prior -> operator pause
    return "NOT-TRADABLE"                                  # expected (honest prior)


# --------------------------------------------------------------------------- #
# Per-stratum orchestration
# --------------------------------------------------------------------------- #
def run_stratum(run, instrument: str, domain: str) -> dict:
    """All three gates + T1/T2 tripwires for one instrument x domain emitted run."""
    positions = run.positions
    assert_run_within_holdout(positions, run.metadata.get("analysis_end_utc"))
    cost = adaptive_cost_bps_for(instrument, domain)

    # Open-to-open <=t-1 returns + the engine-realized P* net series (faithful gate C).
    returns, pos, realized_bps, _ = returns_and_positions_realized(positions, cost_bps=cost)
    powered = len(returns) >= MIN_DOMAIN_RETURNS
    n_trades = int(np.count_nonzero((pos != 0.0) & (np.concatenate(([0.0], pos[:-1])) != pos)))

    seed_a = seed_for("EXP-006-frozen", instrument, domain, STRATEGY)
    seed_b = seed_for("EXP-006-adaptive", instrument, domain, STRATEGY)
    seed_c = seed_for("EXP-006-pstar", instrument, domain, STRATEGY)
    seed_t1 = seed_for("EXP-006-t1", instrument, domain, STRATEGY)

    gate_a = frozen_gate_row(positions, instrument=instrument, domain=domain, seed=seed_a)
    gate_b = adaptive_proxy_row(returns, pos, domain=domain, cost_bps=cost, seed=seed_b)
    gate_c = pstar_realized_row(returns, pos, realized_bps, domain=domain, cost_bps=cost, seed=seed_c)

    t1_fpr, t1_hw, t1_d = t1_future_destroy_fpr(returns, pos, domain=domain, cost_bps=cost,
                                                seed=seed_t1)
    t2_ok = t2_provenance_ok(positions, realized_bps, returns, pos, cost_bps=cost)

    gate_c_l1 = bool(json.loads(gate_c["leg_results"])["L1_readiness"])
    gate_c = {**gate_c, "leg_results_l1": gate_c_l1}
    net_pnl_bps = float(realized_bps[realized_bps != 0.0].mean()) if np.any(realized_bps != 0.0) \
        else 0.0

    verdict = classify(gate_c, t1_fpr, t1_hw, t2_ok, powered=powered)
    return {
        "instrument": instrument, "domain": domain, "cost_bps": cost,
        "n_returns": len(returns), "n_trades": n_trades, "net_pnl_bps_mean": net_pnl_bps,
        "A_frozen_verdict": gate_a["verdict"], "A_frozen_passed": gate_a["passed"],
        "A_frozen_ci_lower_bps": gate_a["ci_lower_bps"],
        "B_adaptive_proxy_verdict": gate_b["verdict"], "B_adaptive_proxy_passed": gate_b["passed"],
        "B_adaptive_proxy_ci_lower_bps": gate_b["ci_lower_bps"],
        "C_pstar_realized_verdict": gate_c["verdict"], "C_pstar_realized_passed": gate_c["passed"],
        "C_pstar_realized_ci_lower_bps": gate_c["ci_lower_bps"], "C_pstar_l1": gate_c_l1,
        "T1_futuredestroy_fpr": t1_fpr, "T1_hw": t1_hw, "T1_draws": t1_d, "T2_provenance_ok": t2_ok,
        "verdict": verdict,
    }


# --------------------------------------------------------------------------- #
# Plotting (bounded inputs)
# --------------------------------------------------------------------------- #
def plot_net_pnl(rows: list[dict], save_path: Path) -> None:
    """(1) Per-stratum realized net per-bar P&L mean (bps) — the honest-prior shape."""
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(11, 5))
    labels = [f"{r['instrument']}/{r['domain']}" for r in rows]
    vals = [r["net_pnl_bps_mean"] for r in rows]
    colors = ["#2c7" if v > 0 else "#c33" for v in vals]
    ax.bar(np.arange(len(rows)), vals, color=colors)
    ax.axhline(0.0, color="black", lw=1)
    ax.set_xticks(np.arange(len(rows))); ax.set_xticklabels(labels, rotation=90, fontsize=7)
    ax.set_title("Realized P* net per-bar P&L mean (bps) per stratum")
    ax.set_ylabel("net bps / active bar")
    fig.tight_layout(); fig.savefig(save_path, dpi=150, bbox_inches="tight"); plt.close(fig)


def plot_gate_map(rows: list[dict], save_path: Path) -> None:
    """(2) Frozen vs §10.3a-proxy vs P*-realized PASS map (PASS=1 / REJECT=0) per cell."""
    sns.set_theme(style="white")
    keys = ["A_frozen_passed", "B_adaptive_proxy_passed", "C_pstar_realized_passed"]
    names = ["frozen (cc)", "§10.3a proxy (oo)", "P* realized (oo)"]
    grid = np.array([[1 if r[k] else 0 for r in rows] for k in keys], dtype=float)
    labels = [f"{r['instrument']}/{r['domain']}" for r in rows]
    fig, ax = plt.subplots(figsize=(max(8, len(rows) * 0.35), 3.2))
    sns.heatmap(grid, ax=ax, cmap="RdYlGn", vmin=0, vmax=1, cbar=False,
                xticklabels=labels, yticklabels=names, linewidths=0.5, linecolor="#ccc")
    ax.set_xticklabels(labels, rotation=90, fontsize=7)
    ax.set_title("Referee PASS map (green=PASS, red=REJECT) — parallel disclosure")
    fig.tight_layout(); fig.savefig(save_path, dpi=150, bbox_inches="tight"); plt.close(fig)


def plot_t1_collapse(rows: list[dict], save_path: Path) -> None:
    """(3) T1 future-destroy FPR per cell with Wilson half-width — must collapse to ~0."""
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(11, 5))
    labels = [f"{r['instrument']}/{r['domain']}" for r in rows]
    x = np.arange(len(rows))
    ax.errorbar(x, [r["T1_futuredestroy_fpr"] for r in rows], yerr=[r["T1_hw"] for r in rows],
                fmt="o", capsize=2, markersize=4, color="#27c")
    ax.axhline(2 * ALPHA, color="red", ls="--", lw=1, label=f"control bound {2*ALPHA}")
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=90, fontsize=7)
    ax.set_title("T1 future-destroy FPR per stratum (block-permuted returns) — leak collapse")
    ax.set_ylabel("FPR"); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(save_path, dpi=150, bbox_inches="tight"); plt.close(fig)


def plot_margins(rows: list[dict], save_path: Path) -> None:
    """(4) Decision margin (gate CI-lower bps) across the 3 referees, per cell."""
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(11, 5))
    labels = [f"{r['instrument']}/{r['domain']}" for r in rows]
    x = np.arange(len(rows))
    for off, key, lab in ((-0.2, "A_frozen_ci_lower_bps", "frozen"),
                          (0.0, "B_adaptive_proxy_ci_lower_bps", "§10.3a proxy"),
                          (0.2, "C_pstar_realized_ci_lower_bps", "P* realized")):
        ax.bar(x + off, [r[key] for r in rows], width=0.2, label=lab)
    ax.axhline(0.0, color="black", lw=1)
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=90, fontsize=7)
    ax.set_title("Gate decision margin (CI-lower, bps) per stratum")
    ax.set_ylabel("CI-lower (bps)"); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(save_path, dpi=150, bbox_inches="tight"); plt.close(fig)


# --------------------------------------------------------------------------- #
# Serialisation
# --------------------------------------------------------------------------- #
def write_results(rows: list[dict]) -> None:
    """Per-stratum table (CSV flat) + full JSON."""
    flat = ["instrument", "domain", "cost_bps", "n_returns", "n_trades", "net_pnl_bps_mean",
            "A_frozen_verdict", "B_adaptive_proxy_verdict", "C_pstar_realized_verdict",
            "C_pstar_realized_ci_lower_bps", "T1_futuredestroy_fpr", "T2_provenance_ok", "verdict"]
    pl.DataFrame([{c: r[c] for c in flat} for r in rows]).write_csv(RESULTS_DIR / "per_stratum.csv")
    (RESULTS_DIR / "per_stratum_full.json").write_text(json.dumps(rows, indent=2, default=str))


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    run_dirs = discover_runs(STRATEGY_RUNS_DIR)
    if not run_dirs:
        logger.warning("No emissions in %s — run the cTrader StrategyHost (EXP-006.conf) first. "
                       "Harness ready; awaiting Stage-3 credentialed run.", STRATEGY_RUNS_DIR)
        return

    rows: list[dict] = []
    for run_dir in tqdm(run_dirs, desc="strata"):
        run = load_emitted_run(run_dir)
        instrument, domain = run_identity(run)
        if domain not in ADAPTIVE_DOMAINS:
            logger.info("SKIP %s: domain %s out of adaptive scope", run_dir.name, domain)
            continue
        rows.append(run_stratum(run, instrument, domain))

    if not rows:
        logger.error("Runs present but no adjudicable strata produced.")
        return
    rows.sort(key=lambda r: (r["instrument"], r["domain"]))

    write_results(rows)
    plot_net_pnl(rows, PLOTS_DIR / "net_pnl_per_stratum.png")
    plot_gate_map(rows, PLOTS_DIR / "gate_pass_map.png")
    plot_t1_collapse(rows, PLOTS_DIR / "t1_leak_collapse.png")
    plot_margins(rows, PLOTS_DIR / "gate_margins.png")

    # --- Summary + blocking leak-tripwire check ---
    n = len(rows)
    from collections import Counter
    verdicts = Counter(r["verdict"] for r in rows)
    t1_max = max(r["T1_futuredestroy_fpr"] for r in rows)
    t2_all = all(r["T2_provenance_ok"] for r in rows)
    bound = 2 * ALPHA
    logger.info("\n=== EXP-006 D-benchmark summary (%d strata) ===", n)
    logger.info("Verdicts: %s", dict(verdicts))
    logger.info("Frozen PASS=%d  §10.3a-proxy PASS=%d  P*-realized PASS=%d  (of %d)",
                sum(r["A_frozen_passed"] for r in rows), sum(r["B_adaptive_proxy_passed"] for r in rows),
                sum(r["C_pstar_realized_passed"] for r in rows), n)
    logger.info("T1 future-destroy FPR max=%.3f (bound %.2f)  T2 provenance clean=%s",
                t1_max, bound, t2_all)

    tripwires: list[str] = []
    if not t2_all:
        tripwires.append("T2 provenance: a NON-exit bar's realized value != position-state proxy "
                         "(injected Python fill, P-09) — REJECT-class")
    for r in rows:
        if (r["T1_futuredestroy_fpr"] - r["T1_hw"]) > bound:
            tripwires.append(f"{r['instrument']}/{r['domain']}: T1 FPR {r['T1_futuredestroy_fpr']:.3f}"
                             f" > {bound} — surviving edge under future-destroy -> REJECT")
    net_tradable = [f"{r['instrument']}/{r['domain']}" for r in rows if r["verdict"] == "NET-TRADABLE"]
    if tripwires:
        logger.error("LEAK-TRIPWIRE FAILURES (%d) — verdict-material, fix+rerun:", len(tripwires))
        for t in tripwires:
            logger.error("  - %s", t)
    else:
        logger.info("All tripwires held: T1 collapses on every cell, T2 provenance clean.")
    if net_tradable:
        logger.warning("NET-TRADABLE surprise (vs honest prior) on: %s — OPERATOR CRITICAL DECISION "
                       "(deployability-adjacent) before any further step; no read spent here.",
                       ", ".join(net_tradable))
    logger.info("results -> %s", RESULTS_DIR / "per_stratum.csv")


if __name__ == "__main__":
    sys.exit(main())
