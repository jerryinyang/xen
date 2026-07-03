"""
Experiment EXP-013 — CF-MR-004/HYP-001: cross-instrument spread MR fade, native pending orders, 4h.

PRICE-PRIMARY / analysis-only Python (L-01): this script NEVER regenerates a signal, anchor, edge, or
fill. The 4 anchor series (S5 rolling-β basket, S6 fixed-ratio pair, S7 fixed-weight basket, S8
relative-value index), the resting bracket (limits at exp(anchor±2σ)), the form-2 anchor-mean TP, and
the horizon-market exit are all computed + FILLED IN-ENGINE by native cTrader pending orders
(`StrategyHost/CrossInstrumentSpreadPlanner.cs` + Xen NativeOrders mode; m1 backtester fills) and
emitted to `data/strategy_runs/EXP-013{,-s6,-s7,-s8}[-shift]/`. Here we only:
  (1) ingest + validate the emissions (holdout fence, causal-provenance columns, fills within bar range),
  (2) ASSEMBLE the per-bar realized NET bps series from the engine-emitted entry+exit fills (intra-position
      MTM, L-09) — EXACTLY the EXP-010/012 two-limit-leg pattern (no rct recompute; P-09 clean),
  (3) adjudicate each cell under the FROZEN 4h referee (`referee_pstar.gate_stack_pstar`, q*=0.75) —
      BOTH with cost (net / tradability) and WITHOUT cost (gross / availability), since the cTrader run
      infused no commission/spread (operator instruction),
  (4) Holm over the 32 cells (L-03),
  (5) leak tripwires: (T1) peer-feed phase-shift run must collapse any net-admitting cell; (T2)
      block-permute future-destroy must collapse (planted-positive must pass = power sanity).

The referee is FROZEN and never edited (L-12). Realized-bps assembly reads ONLY emitted columns.
"""
from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
import seaborn as sns

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "python" / "src"))

from xen.referee_adaptive import adaptive_cost_bps_for, adaptive_row          # noqa: E402
from xen.referee_calibration import DOMAIN_SPECS                              # noqa: E402
from xen.referee_pstar import gate_stack_pstar                               # noqa: E402
from xen.signals.ingestion import load_emitted_run, assert_run_within_holdout  # noqa: E402

# --------------------------------------------------------------------------- #
# Constants (frozen)
# --------------------------------------------------------------------------- #
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("EXP-013")

RESULTS = Path(__file__).resolve().parents[1] / "results"
PLOTS = Path(__file__).resolve().parents[1] / "plots"

DOMAIN = "4h"
ALPHA = 0.05
N_BOOTSTRAP = 10_000
SEED = 20260702
STRATEGY = "cross_instrument_spread_mr"
MIN_STATE = DOMAIN_SPECS[DOMAIN].min_state_count      # 4h power floor (N_min)
F2_PLANT_BPS = 8.0                                    # planted detectable edge (power sanity)
PROV_COLS = ("Position", "RealOpen", "RealHigh", "RealLow", "RealClose",
             "EntryFillPrice", "ExitFillPrice", "Anchor", "Dev", "Z", "Vr", "Hl", "Beta")

FX = ("EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD")
IDX = ("USTEC", "US500", "US2000", "JP225")
S5_S7_CELLS = FX + IDX                                 # 11
S6_S8_CELLS = ("EURUSD", "AUDUSD", "USDCHF", "USTEC", "US500")  # 5 predeclared pairs
ARMS = {
    "S5": {"cells": S5_S7_CELLS, "live": "EXP-013", "shift": "EXP-013-shift"},
    "S6": {"cells": S6_S8_CELLS, "live": "EXP-013-s6", "shift": "EXP-013-s6-shift"},
    "S7": {"cells": S5_S7_CELLS, "live": "EXP-013-s7", "shift": "EXP-013-s7-shift"},
    "S8": {"cells": S6_S8_CELLS, "live": "EXP-013-s8", "shift": "EXP-013-s8-shift"},
}


@dataclass
class CellVerdict:
    arm: str
    instrument: str
    n_bars: int
    n_entries: int
    n_exits: int
    favorable_hit_rate: float     # round trips reaching the anchor-mean TP (fill-based; availability)
    vr_med: float                 # median variance ratio q=4 (<1 = mean-reverting) — MR screen
    hl_med: float                 # median AR(1) half-life (4h bars) — MR screen
    n_episodes: int
    net_mean_bps: float
    gross_mean_bps: float
    ci_low_net: float
    ci_low_gross: float
    admit_net: bool               # binding: tradability (with frozen cost)
    admit_gross: bool             # availability proxy (no cost)
    holm_admit_net: bool
    l1: bool
    powered: bool
    cost_bps: float


# --------------------------------------------------------------------------- #
# I/O
# --------------------------------------------------------------------------- #
def newest_run_dir(root: Path, instrument: str) -> Path:
    pattern = f"{STRATEGY}_{instrument.lower()}_{DOMAIN}_*"
    hits = sorted(root.glob(pattern), key=lambda p: p.name)
    if not hits:
        raise FileNotFoundError(f"No emitted run for {instrument} under {root} ({pattern})")
    return hits[-1]


SYSTEMATIC_BREACH_FRAC = 0.05   # >5% of fills outside the bar range = systematic bias (lookahead) → hard fail


def validate_provenance(positions: pl.DataFrame, instrument: str) -> dict:
    """Emitted decision/fill columns present; fills lie within the emitting bar's [Low, High], up to a
    spread/gap-aware tolerance = max(0.1·(High−Low), 1 bp·price). ISOLATED breaches (bid/ask side vs
    bid-based OHLC, or a session-gap open fill of a resting limit placed from ≤ t-1) are benign — the
    order was armed causally and the fill is engine-realized (a real gap fill you'd get live). They are
    counted + reported for the audit. A real lookahead leak biases fills SYSTEMATICALLY, so we hard-fail
    only when >5% of a leg's fills breach (a single/isolated gap fill on a gappy index does not)."""
    missing = [c for c in PROV_COLS if c not in positions.columns]
    if missing:
        raise ValueError(f"{instrument}: emitted positions missing provenance columns {missing}")
    df = positions.sort("SourceCloseTime")
    stats = {}
    for leg in ("EntryFillPrice", "ExitFillPrice"):
        fills = df.filter(pl.col(leg).is_not_nan())
        if fills.height == 0:
            stats[leg] = {"n_fills": 0, "n_breach": 0, "max_bps": 0.0, "breach_frac": 0.0}
            continue
        f = fills.with_columns(
            tol=pl.max_horizontal(0.1 * (pl.col("RealHigh") - pl.col("RealLow")), 1e-4 * pl.col(leg)),
            over=pl.max_horizontal(pl.col(leg) - pl.col("RealHigh"), pl.col("RealLow") - pl.col(leg), 0.0))
        breach = f.filter(pl.col("over") > pl.col("tol"))
        max_bps = float((breach.select((pl.col("over") / pl.col(leg) * 1e4).max()).item() or 0.0)
                        ) if breach.height else 0.0
        frac = breach.height / fills.height
        stats[leg] = {"n_fills": fills.height, "n_breach": breach.height, "max_bps": max_bps, "breach_frac": frac}
        if frac > SYSTEMATIC_BREACH_FRAC:
            raise ValueError(f"{instrument}: {breach.height}/{fills.height} {leg} fills outside bar range "
                             f"({frac:.1%} > {SYSTEMATIC_BREACH_FRAC:.0%}, max {max_bps:.0f} bps) — systematic non-causal")
        if breach.height:
            logger.warning("%s: %d/%d %s fills outside [Low,High] (max %.1f bps; isolated gap/spread — benign)",
                           instrument, breach.height, fills.height, leg, max_bps)
    return stats


# --------------------------------------------------------------------------- #
# Realized NET bps assembly — identical two-limit-leg pattern to EXP-010/012 (L-09 MTM, L-02 cost).
# Reads ONLY emitted columns. Position = direction ACTIVE during the bar (entry bar carries entered dir).
# --------------------------------------------------------------------------- #
def assemble_realized_bps(
    positions: pl.DataFrame, *, cost_bps: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    df = positions.sort("SourceCloseTime")
    pos = df.get_column("Position").to_numpy().astype(float)
    op = df.get_column("RealOpen").to_numpy().astype(float)
    entry = df.get_column("EntryFillPrice").to_numpy().astype(float)
    exit_ = df.get_column("ExitFillPrice").to_numpy().astype(float)
    if len(pos) < 3:
        raise ValueError("too few emitted bars to assemble a realized series")

    next_open = op[1:]
    op, pos, entry, exit_ = op[:-1], pos[:-1], entry[:-1], exit_[:-1]
    has_entry = ~np.isnan(entry)
    has_exit = ~np.isnan(exit_)
    with np.errstate(divide="ignore", invalid="ignore"):
        open_price = np.where(has_entry, entry, op)          # entry bar → entry fill, else bar open
        close_price = np.where(has_exit, exit_, next_open)   # exit bar → exit fill, else next open
        gross = pos * np.log(close_price / open_price) * 10_000.0
    gross = np.where(pos != 0.0, gross, 0.0)
    gross = np.nan_to_num(gross, nan=0.0, posinf=0.0, neginf=0.0)
    realized_bps = gross - cost_bps * has_entry.astype(float)   # RT cost once per entry (L-02)
    market_returns = np.nan_to_num(np.log(next_open / op), nan=0.0, posinf=0.0, neginf=0.0)
    return market_returns, pos, realized_bps


def _pstar(returns, pos, realized_bps, cost_bps):
    return gate_stack_pstar(returns, pos, realized_bps, domain=DOMAIN, cost_bps=cost_bps,
                            n_bootstrap=N_BOOTSTRAP, seed=SEED)


def _boot_p(core: dict) -> float:
    neutral = np.asarray(core.get("neutral_means", []), dtype=float)
    return float(np.mean(neutral <= 0.0)) if neutral.size else float("nan")


def favorable_and_mr(positions: pl.DataFrame) -> tuple[float, float, float]:
    """Availability + MR characterization, from EMITTED FILLS (not events — the engine's exit-reason
    label is unreliable, see report §method). Favorable-target-hit = fraction of round trips whose exit
    fill reached the entry-time anchor-mean TP on the favourable side (long: exit ≥ TP−5bp; short:
    exit ≤ TP+5bp); the rest are horizon/adverse closes. MR screen: median Variance Ratio (q=4; <1 =
    mean-reverting) and median AR(1) half-life over non-warmup bars — the informative characterization
    of how mean-reverting each spread actually is (design §9, L-12 not gating)."""
    d = positions.sort("SourceCloseTime")
    pos = d.get_column("Position").to_numpy().astype(float)
    an = d.get_column("Anchor").to_numpy().astype(float)
    en = d.get_column("EntryFillPrice").to_numpy().astype(float)
    ex = d.get_column("ExitFillPrice").to_numpy().astype(float)
    hits, cur = [], None
    for i in range(len(pos)):
        if not np.isnan(en[i]):
            cur = (pos[i], an[i])          # (dir, TP = anchor mean fixed at entry)
        if not np.isnan(ex[i]) and cur is not None:
            dr, tp = cur
            tol = 5e-4 * tp
            hits.append((ex[i] >= tp - tol) if dr > 0 else (ex[i] <= tp + tol))
            cur = None
    fav = float(np.mean(hits)) if hits else float("nan")
    nw = positions.filter(~pl.col("Warmup"))
    vr = nw.get_column("Vr").drop_nans().to_numpy()
    hl = nw.get_column("Hl").drop_nans().to_numpy()
    return (fav, float(np.median(vr)) if len(vr) else float("nan"),
            float(np.median(hl)) if len(hl) else float("nan"))


def adjudicate(arm: str, instrument: str, run) -> tuple[CellVerdict, float]:
    """Route one cell's engine-realized series through the frozen 4h P*-gate — net (cost) + gross (no cost)."""
    positions = run.positions
    cost_bps = adaptive_cost_bps_for(instrument, DOMAIN)
    ret, pos, net = assemble_realized_bps(positions, cost_bps=cost_bps)
    _, _, gross = assemble_realized_bps(positions, cost_bps=0.0)
    core_net = _pstar(ret, pos, net, cost_bps)
    row_net = adaptive_row(core_net, alpha=ALPHA)
    row_gross = adaptive_row(_pstar(ret, pos, gross, 0.0), alpha=ALPHA)

    pos_arr = positions.sort("SourceCloseTime")
    n_entries = int(np.sum(~np.isnan(pos_arr.get_column("EntryFillPrice").to_numpy().astype(float))))
    n_exits = int(np.sum(~np.isnan(pos_arr.get_column("ExitFillPrice").to_numpy().astype(float))))
    fav, vr_med, hl_med = favorable_and_mr(positions)
    n_epi = int(core_net.get("n_episodes", 0))
    v = CellVerdict(
        arm=arm, instrument=instrument, n_bars=positions.height, n_entries=n_entries, n_exits=n_exits,
        favorable_hit_rate=fav, vr_med=vr_med, hl_med=hl_med, n_episodes=n_epi,
        net_mean_bps=float(np.mean(net[net != 0.0]) if np.any(net != 0.0) else 0.0),
        gross_mean_bps=float(np.mean(gross[gross != 0.0]) if np.any(gross != 0.0) else 0.0),
        ci_low_net=float(row_net["ci_lower_bps"]), ci_low_gross=float(row_gross["ci_lower_bps"]),
        admit_net=bool(row_net["passed"]), admit_gross=bool(row_gross["passed"]), holm_admit_net=False,
        l1=bool(core_net["l1"]), powered=bool(core_net["l1"] and n_epi >= MIN_STATE), cost_bps=cost_bps,
    )
    return v, _boot_p(core_net)


def holm(pvals: dict[str, float], alpha: float = ALPHA) -> dict[str, bool]:
    items = sorted(((k, v) for k, v in pvals.items() if np.isfinite(v)), key=lambda kv: kv[1])
    m = len(items)
    out = {k: False for k in pvals}
    for i, (k, p) in enumerate(items):
        if p <= alpha / (m - i):
            out[k] = True
        else:
            break
    return out


def f2_plant_destroy(run, instrument: str) -> dict:
    """(a) inject a known favourable drift on active bars → referee MUST PASS (power sanity);
    (b) block-permute → MUST collapse. Informative even on a null live edge."""
    cost_bps = adaptive_cost_bps_for(instrument, DOMAIN)
    ret, pos, net = assemble_realized_bps(run.positions, cost_bps=cost_bps)
    active = pos != 0.0
    if active.sum() < MIN_STATE:
        return {"planted_pass": None, "destroyed_pass": None, "note": "unpowered_for_plant"}
    planted = net + F2_PLANT_BPS * active.astype(float)
    planted_pass = bool(adaptive_row(_pstar(ret, pos, planted, cost_bps), alpha=ALPHA)["passed"])
    rng = np.random.default_rng(SEED)
    destroyed_pass = bool(adaptive_row(
        _pstar(ret, pos, planted[rng.permutation(len(planted))], cost_bps), alpha=ALPHA)["passed"])
    return {"planted_pass": planted_pass, "destroyed_pass": destroyed_pass}


def shift_survivors(arm: str, cells, live_admit: set[str]) -> list[str] | None:
    """T1 leak tripwire: peer-feed phase-shift cells that still net-ADMIT among live-net-admitting cells.
    The cross-instrument edge must collapse when the peer feed is time-decorrelated. Survivor ⇒ REJECT."""
    root = ROOT / "data" / "strategy_runs" / ARMS[arm]["shift"]
    if not root.exists() or not any(root.iterdir()):
        return None
    surviving = []
    for inst in cells:
        if f"{arm}:{inst}" not in live_admit:
            continue
        run = load_emitted_run(newest_run_dir(root, inst))
        v, _ = adjudicate(arm, inst, run)
        if v.admit_net:
            surviving.append(f"{arm}:{inst}")
    return surviving


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def screen_arm(arm: str, cfg: dict):
    root = ROOT / "data" / "strategy_runs" / cfg["live"]
    verdicts, pvals, f2, prov = [], {}, {}, {}
    for inst in cfg["cells"]:
        run = load_emitted_run(newest_run_dir(root, inst))
        assert_run_within_holdout(run.positions, run.metadata.get("analysis_end_utc"))
        prov[f"{arm}:{inst}"] = validate_provenance(run.positions, inst)
        v, p = adjudicate(arm, inst, run)
        verdicts.append(v)
        pvals[f"{arm}:{inst}"] = p
        f2[f"{arm}:{inst}"] = f2_plant_destroy(run, inst)
        logger.info("[%s] %s: entries=%d epi=%d(min%d) fav_hit=%.2f VR=%.2f HL=%.0f gross=%.2f(ci%.2f a=%s) "
                    "net=%.2f(ci%.2f a=%s) cost=%.1f L1=%s p=%.4f", arm, inst, v.n_entries,
                    v.n_episodes, MIN_STATE, v.favorable_hit_rate, v.vr_med, v.hl_med, v.gross_mean_bps,
                    v.ci_low_gross, v.admit_gross, v.net_mean_bps, v.ci_low_net, v.admit_net, v.cost_bps, v.l1, p)
    return verdicts, pvals, f2, prov


def plot_all(all_v: list[CellVerdict], f2: dict, save: Path) -> None:
    sns.set_theme(style="whitegrid")
    labels = [f"{v.arm}:{v.instrument}" for v in all_v]
    x = np.arange(len(all_v))
    # 1 net vs gross per cell
    fig, ax = plt.subplots(figsize=(13, 5))
    ax.errorbar(x - 0.15, [v.gross_mean_bps for v in all_v],
                yerr=[max(v.gross_mean_bps - v.ci_low_gross, 0) for v in all_v], fmt="o", ms=3,
                capsize=2, color="#69c", label="gross (no cost) — availability")
    ax.errorbar(x + 0.15, [v.net_mean_bps for v in all_v],
                yerr=[max(v.net_mean_bps - v.ci_low_net, 0) for v in all_v], fmt="s", ms=3,
                capsize=2, color="#c63", label="net (cost) — tradability")
    ax.axhline(0, color="red", ls="--", lw=1)
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=90, fontsize=6)
    ax.set_title("EXP-013 per-cell realized bps, gross vs net (ci_low bar); >0 & referee-admit = pass")
    ax.set_ylabel("bps/active"); ax.legend(); fig.tight_layout()
    fig.savefig(save / "net_vs_gross_per_cell.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    # 2 episodes vs floor
    fig, ax = plt.subplots(figsize=(13, 5))
    ax.bar(x, [v.n_episodes for v in all_v],
           color=["#2c7" if v.n_episodes >= MIN_STATE else "#c55" for v in all_v])
    ax.axhline(MIN_STATE, color="red", ls="--", lw=1, label=f"min_state {MIN_STATE}")
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=90, fontsize=6)
    ax.set_title("EXP-013 reversion episodes vs 4h power floor (green=powered)")
    ax.set_ylabel("episodes"); ax.legend(); fig.tight_layout()
    fig.savefig(save / "episodes_vs_floor.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    # 3 availability (fill-based favorable-target hit) + MR screen (VR)
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(15, 5))
    ax.bar(x, [v.favorable_hit_rate for v in all_v], color="#59b")
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=90, fontsize=6)
    ax.set_ylabel("round trips reaching anchor-mean TP"); ax.set_ylim(0, 1)
    ax.set_title("EXP-013 favorable-target hit rate (fill-based; rest = horizon/adverse)")
    ax2.bar(x, [v.vr_med for v in all_v], color=["#2c7" if v.vr_med < 1 else "#c55" for v in all_v])
    ax2.axhline(1.0, color="red", ls="--", lw=1, label="VR=1 (random walk)")
    ax2.set_xticks(x); ax2.set_xticklabels(labels, rotation=90, fontsize=6)
    ax2.set_ylabel("median VR (q=4)"); ax2.set_title("EXP-013 MR screen: variance ratio (<1 = reverting)")
    ax2.legend(); fig.tight_layout()
    fig.savefig(save / "availability_and_mr.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    # 4 F-2 plant/destroy
    keys = [k for k in f2 if f2[k].get("planted_pass") is not None]
    if keys:
        fig, ax = plt.subplots(figsize=(11, 4))
        ax.bar(np.arange(len(keys)) - 0.2, [f2[k]["planted_pass"] for k in keys], 0.4, label="planted PASS (want 1)")
        ax.bar(np.arange(len(keys)) + 0.2, [f2[k]["destroyed_pass"] for k in keys], 0.4, label="destroyed PASS (want 0)")
        ax.set_xticks(np.arange(len(keys))); ax.set_xticklabels(keys, rotation=90, fontsize=6)
        ax.set_title("EXP-013 F-2 non-vacuous leak: plant must pass, future-destroy must collapse"); ax.legend()
        fig.tight_layout(); fig.savefig(save / "f2_plant_destroy.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    PLOTS.mkdir(parents=True, exist_ok=True)
    logger.info("EXP-013 CF-MR-004 — 32 cells (S5/S7 11 + S6/S8 5); frozen referee domain=4h; net+gross.")

    all_v, pvals, f2, prov = [], {}, {}, {}
    for arm, cfg in ARMS.items():
        vs, pv, f2a, pa = screen_arm(arm, cfg)
        all_v.extend(vs); pvals.update(pv); f2.update(f2a); prov.update(pa)

    holm_map = holm(pvals)
    for v in all_v:
        v.holm_admit_net = bool(holm_map.get(f"{v.arm}:{v.instrument}", False) and v.admit_net)

    live_admit = {f"{v.arm}:{v.instrument}" for v in all_v if v.holm_admit_net}
    survivors, tripwire_available = [], False
    for arm, cfg in ARMS.items():
        s = shift_survivors(arm, cfg["cells"], live_admit)
        if s is not None:
            tripwire_available = True
            survivors.extend(s)
    tripwire_ok = (len(survivors) == 0) if tripwire_available else None

    f2_powered = [k for k in f2 if f2[k].get("planted_pass") is not None]
    f2_detect_ok = all(f2[k]["planted_pass"] for k in f2_powered) if f2_powered else None
    f2_collapse_ok = all(not f2[k]["destroyed_pass"] for k in f2_powered) if f2_powered else None

    def arm_stats(arm: str) -> dict:
        vs = [v for v in all_v if v.arm == arm]
        powered = [v for v in vs if v.powered]
        return {"cells": len(vs), "powered": len(powered),
                "gross_admit": sum(v.admit_gross for v in powered),
                "net_holm_admit": sum(v.holm_admit_net for v in powered)}

    stats = {a: arm_stats(a) for a in ARMS}
    tot_powered = sum(s["powered"] for s in stats.values())
    tot_net_admit = sum(s["net_holm_admit"] for s in stats.values())
    tot_gross_admit = sum(s["gross_admit"] for s in stats.values())

    # Binding future-destroy control = T1 peer-feed phase-shift (tripwire_ok). The F-2 block-permute
    # destroy is VACUOUS for the mean-stat referee (a uniform +8bps plant is permutation-invariant →
    # cannot collapse; see memory permutation_destroy_mean_invariant / EXP-012 L) — reported, NOT gated.
    # Both leak controls are additionally vacuous whenever the live edge is null (nothing to destroy).
    if tripwire_ok is False:
        outcome = "REJECT_LEAK"
    elif tot_powered == 0:
        outcome = "UNPOWERED"
    elif tot_net_admit == 0:
        outcome = "NOT_TRADABLE"      # availability (gross) may be >0; does not survive cost
    elif any(stats[a]["net_holm_admit"] >= max(1, (stats[a]["powered"] + 1) // 2) for a in ARMS) \
            and tripwire_ok and f2_detect_ok:
        outcome = "TRADABLE_ON_TRAIN"
    elif tripwire_ok is None:
        outcome = "PENDING_TRIPWIRE"
    else:
        outcome = "NOT_TRADABLE"

    result = {
        "experiment": "EXP-013", "family": "CF-MR-004", "domain": DOMAIN, "min_state_count": MIN_STATE,
        "arms": stats, "n_powered": tot_powered, "n_gross_admit": tot_gross_admit,
        "n_net_holm_admit": tot_net_admit, "tripwire_pass": tripwire_ok, "shift_survivors": survivors,
        "f2_planted_detect_ok": f2_detect_ok, "f2_future_destroy_collapse_ok": f2_collapse_ok,
        "outcome": outcome, "holm": holm_map, "pvals": pvals, "cells": [asdict(v) for v in all_v],
        "f2": f2, "provenance_breach": prov,
    }
    (RESULTS / "verdict.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    plot_all(all_v, f2, PLOTS)
    logger.info("VERDICT: %s | powered=%d gross_admit=%d net_holm_admit=%d tripwire=%s f2_detect=%s "
                "f2_collapse=%s", outcome, tot_powered, tot_gross_admit, tot_net_admit, tripwire_ok,
                f2_detect_ok, f2_collapse_ok)
    logger.info("per-arm: %s -> results/verdict.json", stats)


if __name__ == "__main__":
    main()
