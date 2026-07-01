"""
Experiment EXP-012 — CF-MR-003 CONC-1 Track 2: form-2 limit-at-anchor MR-fade tradability, exec-15m.

PRICE-PRIMARY / analysis-only Python (L-01): this script NEVER regenerates a signal, anchor, edge, or
fill. The S3_DETREND (single-symbol rolling-OLS trendline) and S5_SPREAD (multi-symbol basket) anchors,
the VR∧HL selector, the |z|≥2 extreme, the live-limit entry, and the form-2 limit / horizon-market
exits are all computed IN-ENGINE by `StrategyHost/CrossDomainMrLimitModel.cs` and emitted to
`data/strategy_runs/EXP-012-t2a|t2b[-shuffle]/`. Here we only: (1) ingest + validate the emissions
(holdout fence, causal-provenance columns), (2) ASSEMBLE the per-bar realized NET bps series from the
engine-emitted fills with intra-position MTM (L-09), (3) adjudicate each cell under the FROZEN 15m
referee (`referee_pstar.gate_stack_pstar`, domain="15m"; EXP-011 hash-pinned) with per-instrument cost
(L-02), (4) phase-Holm over the 24 cells with T2a/T2b sub-families (L-03), (5) discharge the gate-debt:
F-1 vehicle fidelity (in-engine z vs the reference screen z) + F-2 NON-VACUOUS leak-resistance
(planted-positive must PASS, future-destroy must collapse) + the T2b phase-shifted-basket shuffle run.

Realized-bps assembly reads ONLY emitted columns (Position, RealOpen, EntryFillPrice, ExitFillPrice) —
the sanctioned two-limit-leg pattern from EXP-010; no `rct`-style favourable-index recompute (P-09 clean).
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
import seaborn as sns

from xen.referee_adaptive import ROUND_TRIP_COST_BPS_17, adaptive_row
from xen.referee_calibration import DOMAIN_SPECS
from xen.referee_pstar import gate_stack_pstar
from xen.signals.ingestion import load_emitted_run, assert_run_within_holdout

# --------------------------------------------------------------------------- #
# Constants (frozen; member set = EXP-009 admitted exec-15m cells — design §2)
# --------------------------------------------------------------------------- #
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("EXP-012")

ROOT = Path(__file__).resolve().parents[4]
RESULTS = Path(__file__).resolve().parents[1] / "results"
PLOTS = Path(__file__).resolve().parents[1] / "plots"

DOMAIN = "15m"
ALPHA = 0.05
N_BOOTSTRAP = 10_000
SEED = 20260701
STRATEGY = "cross_domain_mr_limit"
MIN_STATE = DOMAIN_SPECS[DOMAIN].min_state_count      # 25 — the binding 15m power floor (EXP-011)

# T2a S3_DETREND (single-symbol) 14 cells; T2b S5_SPREAD (multi-symbol) 10 cells.
T2A_CELLS = ("AUDJPY", "AUDUSD", "BTCUSD", "EURJPY", "EURUSD", "GBPJPY", "GBPUSD",
             "NZDUSD", "US2000", "USDCAD", "USDCHF", "USDJPY", "USTEC", "XAUUSD")
T2B_CELLS = ("AUDUSD", "EURUSD", "GBPUSD", "NZDUSD", "US2000", "US500",
             "USDCAD", "USDCHF", "USDJPY", "USTEC")
ARMS = {
    "T2a": {"cells": T2A_CELLS, "live": "EXP-012-t2a", "shuffle": None},
    "T2b": {"cells": T2B_CELLS, "live": "EXP-012-t2b", "shuffle": "EXP-012-t2b-shuffle"},
}

# F-1 vehicle-fidelity tolerances (design §6; tightened from EXP-010's loose 0.67/0.30).
F1_Z_CORR_MIN = 0.90
F1_JACCARD_MIN = 0.70
Z_STAR = 2.0
# F-2 planted-positive drift level (bps/active bar) — a clearly-detectable edge for the power sanity.
F2_PLANT_BPS = 8.0

PROV_COLS = ("Position", "RealOpen", "RealHigh", "RealLow", "RealClose",
             "EntryFillPrice", "ExitFillPrice", "Anchor", "Dev", "Z", "Vr", "Hl", "Beta")


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass
class CellVerdict:
    arm: str
    instrument: str
    n_bars: int
    n_entries: int
    n_episodes: int
    realized_mean_bps: float
    ci_low: float
    l1: bool
    l3: str
    admit: bool
    holm_admit: bool
    powered: bool
    f1_z_corr: float
    f1_jaccard: float
    vehicle_unfit: bool


# --------------------------------------------------------------------------- #
# I/O helpers
# --------------------------------------------------------------------------- #
def newest_run_dir(root: Path, instrument: str) -> Path:
    """Newest emitted run dir for a cell (`{strategy}_{symbol}_{domain}_{stamp}`)."""
    pattern = f"{STRATEGY}_{instrument.lower()}_{DOMAIN}_*"
    hits = sorted(root.glob(pattern), key=lambda p: p.name)
    if not hits:
        raise FileNotFoundError(f"No emitted run for {instrument} under {root} ({pattern})")
    return hits[-1]


# --------------------------------------------------------------------------- #
# Pure checks — causal-provenance validation (design §7 T2; assembly-side mirror)
# --------------------------------------------------------------------------- #
def validate_provenance(positions: pl.DataFrame, instrument: str) -> None:
    """Assert emitted decision/fill columns are present and fills lie within the emitting bar's range."""
    missing = [c for c in PROV_COLS if c not in positions.columns]
    if missing:
        raise ValueError(f"{instrument}: emitted positions missing provenance columns {missing}")
    df = positions.sort("SourceCloseTime")
    for leg in ("EntryFillPrice", "ExitFillPrice"):
        fills = df.filter(pl.col(leg).is_not_nan())
        if fills.height == 0:
            continue
        bad = fills.filter(
            (pl.col(leg) < pl.col("RealLow") - 1e-9) | (pl.col(leg) > pl.col("RealHigh") + 1e-9))
        if bad.height:
            raise ValueError(f"{instrument}: {bad.height} {leg} fills outside [Low, High] (non-causal fill)")


# --------------------------------------------------------------------------- #
# Pure computation — realized NET bps assembly (L-09 MTM, L-02 cost); identical to EXP-010
# --------------------------------------------------------------------------- #
def assemble_realized_bps(
    positions: pl.DataFrame, *, cost_bps: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per-bar open-to-open realized NET bps with exact entry+exit limit fills + intra-position MTM.

    Reads ONLY engine-emitted columns. For bar t (dropping the last, no next open): held ->
    pos*log(Open[t+1]/Open[t]); entry -> pos*log(Open[t+1]/EntryFill); exit -> pos*log(ExitFill/Open[t]);
    entry==exit -> pos*log(ExitFill/EntryFill). Round-trip cost charged once per entry (L-02). Length n-1.
    """
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
        open_price = np.where(has_entry, entry, op)
        close_price = np.where(has_exit, exit_, next_open)
        gross = pos * np.log(close_price / open_price) * 10_000.0
    gross = np.where(pos != 0.0, gross, 0.0)
    gross = np.nan_to_num(gross, nan=0.0, posinf=0.0, neginf=0.0)
    realized_bps = gross - cost_bps * has_entry.astype(float)
    market_returns = np.nan_to_num(np.log(next_open / op), nan=0.0, posinf=0.0, neginf=0.0)
    return market_returns, pos, realized_bps


# --------------------------------------------------------------------------- #
# F-1 vehicle fidelity — in-engine z vs the reference screen z (design §6)
# --------------------------------------------------------------------------- #
def vehicle_fidelity(positions: pl.DataFrame, arm: str, instrument: str) -> tuple[float, float]:
    """Compare the in-engine emitted z (rested t-1) to the reference screen z, on matched bars.

    Reference: the emitted `Dev`/`Z` are the vehicle's own decision series; we cross-check internal
    consistency (finite-z correlation of Z vs Dev/rolling-sigma) and the |z|≥2 selection Jaccard between
    the engine's Z and a reference z rebuilt from the emitted `Dev` and its trailing std (the admitted
    robust-z construction, recomputed from emitted columns only — no new edge). Returns (z_corr, jaccard).
    """
    df = positions.sort("SourceCloseTime").filter(pl.col("Warmup") == False)  # noqa: E712
    z_eng = df.get_column("Z").to_numpy().astype(float)
    dev = df.get_column("Dev").to_numpy().astype(float)
    ok = np.isfinite(z_eng) & np.isfinite(dev)
    if ok.sum() < 50:
        return float("nan"), float("nan")
    # reference z: dev standardized by its own trailing-200 std (mirrors rolling_std_z on emitted dev)
    z_ref = np.full_like(dev, np.nan)
    w = 200
    for i in range(w, len(dev)):
        win = dev[i - w:i]
        win = win[np.isfinite(win)]
        s = win.std(ddof=1) if win.size > 1 else np.nan
        if np.isfinite(s) and s > 0:
            z_ref[i] = dev[i] / s
    both = np.isfinite(z_eng) & np.isfinite(z_ref)
    if both.sum() < 50:
        return float("nan"), float("nan")
    z_corr = float(np.corrcoef(z_eng[both], z_ref[both])[0, 1])
    sel_e = np.abs(z_eng[both]) >= Z_STAR
    sel_r = np.abs(z_ref[both]) >= Z_STAR
    inter = np.sum(sel_e & sel_r)
    union = np.sum(sel_e | sel_r)
    jaccard = float(inter / union) if union > 0 else float("nan")
    return z_corr, jaccard


# --------------------------------------------------------------------------- #
# Adjudication — frozen 15m referee (no referee module edited; L-12)
# --------------------------------------------------------------------------- #
def _pstar(returns, pos, realized_bps, cost_bps):
    return gate_stack_pstar(returns, pos, realized_bps, domain=DOMAIN, cost_bps=cost_bps,
                            n_bootstrap=N_BOOTSTRAP, seed=SEED)


def adjudicate(arm: str, instrument: str, positions: pl.DataFrame) -> tuple[CellVerdict, dict, float]:
    """Route one cell's emitted realized series through the frozen 15m P*-gate + adaptive row."""
    cost_bps = ROUND_TRIP_COST_BPS_17[instrument][DOMAIN]
    returns, pos, realized_bps = assemble_realized_bps(positions, cost_bps=cost_bps)
    core = _pstar(returns, pos, realized_bps, cost_bps)
    row = adaptive_row(core, alpha=ALPHA)
    legs = json.loads(row["leg_results"])
    neutral = np.asarray(core.get("neutral_means", []), dtype=float)
    p_boot = float(np.mean(neutral <= 0.0)) if neutral.size else float("nan")
    n_entries = int(np.sum(~np.isnan(
        positions.sort("SourceCloseTime").get_column("EntryFillPrice").to_numpy().astype(float))))
    z_corr, jaccard = vehicle_fidelity(positions, arm, instrument)
    n_epi = int(core.get("n_episodes", 0))
    verdict = CellVerdict(
        arm=arm, instrument=instrument, n_bars=positions.height, n_entries=n_entries,
        n_episodes=n_epi,
        realized_mean_bps=float(np.mean(realized_bps[realized_bps != 0.0])
                                if np.any(realized_bps != 0.0) else 0.0),
        ci_low=float(row["ci_lower_bps"]), l1=bool(core["l1"]),
        l3=str(legs.get("L3_outcome", "NA")), admit=bool(row["passed"]), holm_admit=False,
        powered=bool(core["l1"] and n_epi >= MIN_STATE),
        f1_z_corr=z_corr, f1_jaccard=jaccard,
        vehicle_unfit=bool(np.isfinite(z_corr) and (z_corr < F1_Z_CORR_MIN or
                           (np.isfinite(jaccard) and jaccard < F1_JACCARD_MIN))),
    )
    return verdict, row, p_boot


def holm(pvals: dict[str, float], alpha: float = ALPHA) -> dict[str, bool]:
    """Holm–Bonferroni over the 24 cells (L-03). Cells without a finite p abstain (False)."""
    items = sorted(((k, v) for k, v in pvals.items() if np.isfinite(v)), key=lambda kv: kv[1])
    m = len(items)
    out = {k: False for k in pvals}
    for i, (k, p) in enumerate(items):
        if p <= alpha / (m - i):
            out[k] = True
        else:
            break
    return out


# --------------------------------------------------------------------------- #
# F-2 non-vacuous leak-resistance (design §6): planted-positive must PASS, future-destroy must collapse
# --------------------------------------------------------------------------- #
def f2_plant_destroy(positions: pl.DataFrame, instrument: str) -> dict:
    """On a cell's realized series: (a) inject a known favourable drift on active bars -> referee MUST
    PASS (power sanity: the 15m vehicle CAN detect a real edge at this episode count); (b) block-permute
    the planted returns -> MUST collapse to REJECT. Informative even when the live edge is null."""
    cost_bps = ROUND_TRIP_COST_BPS_17[instrument][DOMAIN]
    returns, pos, realized_bps = assemble_realized_bps(positions, cost_bps=cost_bps)
    active = pos != 0.0
    if active.sum() < MIN_STATE:
        return {"planted_pass": None, "destroyed_pass": None, "note": "unpowered_for_plant"}
    planted = realized_bps + F2_PLANT_BPS * active.astype(float)
    planted_pass = bool(adaptive_row(_pstar(returns, pos, planted, cost_bps), alpha=ALPHA)["passed"])
    rng = np.random.default_rng(SEED)
    perm = rng.permutation(len(planted))
    destroyed_pass = bool(adaptive_row(_pstar(returns, pos, planted[perm], cost_bps), alpha=ALPHA)["passed"])
    return {"planted_pass": planted_pass, "destroyed_pass": destroyed_pass}


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def screen_arm(arm: str, cells: tuple[str, ...], live_id: str) -> tuple[list[CellVerdict], dict]:
    """Ingest + validate + adjudicate one arm's cells."""
    root = ROOT / "data" / "strategy_runs" / live_id
    verdicts, rows, pvals, f2 = [], {}, {}, {}
    for inst in cells:
        run = load_emitted_run(newest_run_dir(root, inst))
        assert_run_within_holdout(run.positions, run.metadata.get("analysis_end_utc"))
        validate_provenance(run.positions, inst)
        v, row, p = adjudicate(arm, inst, run.positions)
        verdicts.append(v)
        rows[f"{arm}:{inst}"] = row
        pvals[f"{arm}:{inst}"] = p
        f2[f"{arm}:{inst}"] = f2_plant_destroy(run.positions, inst)
        logger.info("[%s] %s: entries=%d epi=%d(min%d) net=%.2fbps ci_low=%.2f L1=%s p=%.4f "
                    "z_corr=%.2f jac=%.2f%s", arm, inst, v.n_entries, v.n_episodes, MIN_STATE,
                    v.realized_mean_bps, v.ci_low, v.l1, p, v.f1_z_corr, v.f1_jaccard,
                    " UNFIT" if v.vehicle_unfit else "")
    return verdicts, {"rows": rows, "pvals": pvals, "f2": f2}


def shuffle_survivors(shuffle_id: str, cells: tuple[str, ...], admit: set[str]) -> list[str]:
    """T2b leak tripwire: phase-shifted-basket cells that still ADMIT among the live-admitting set."""
    root = ROOT / "data" / "strategy_runs" / shuffle_id
    if not root.exists() or not any(root.iterdir()):
        return []
    surviving = []
    for inst in cells:
        if f"T2b:{inst}" not in admit:
            continue
        run = load_emitted_run(newest_run_dir(root, inst))
        v, _, _ = adjudicate("T2b", inst, run.positions)
        if v.admit:
            surviving.append(inst)
    return surviving


def plot_all(all_v: list[CellVerdict], detail: dict, save: Path) -> None:
    """4 plots: per-cell net+ci; episode-vs-floor; F-1 fidelity scatter; F-2 plant/destroy."""
    sns.set_theme(style="whitegrid")
    labels = [f"{v.arm}:{v.instrument}" for v in all_v]
    x = np.arange(len(all_v))
    # 1 net + ci
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.errorbar(x, [v.realized_mean_bps for v in all_v],
                yerr=[max(v.realized_mean_bps - v.ci_low, 0) for v in all_v], fmt="o", capsize=2)
    ax.axhline(0, color="red", ls="--", lw=1)
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=90, fontsize=6)
    ax.set_title("EXP-012 per-cell realized net bps (ci_low bar); >0 & referee-admit = tradable")
    ax.set_ylabel("net bps/active"); fig.tight_layout()
    fig.savefig(save / "net_per_cell.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    # 2 episode vs floor
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(x, [v.n_episodes for v in all_v],
           color=["#2c7" if v.n_episodes >= MIN_STATE else "#c55" for v in all_v])
    ax.axhline(MIN_STATE, color="red", ls="--", lw=1, label=f"min_state {MIN_STATE}")
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=90, fontsize=6)
    ax.set_title("EXP-012 reversion episodes vs 15m power floor (green=powered)")
    ax.set_ylabel("episodes"); ax.legend(); fig.tight_layout()
    fig.savefig(save / "episodes_vs_floor.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    # 3 F-1 fidelity scatter
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter([v.f1_z_corr for v in all_v], [v.f1_jaccard for v in all_v],
               c=["#c55" if v.vehicle_unfit else "#2c7" for v in all_v])
    ax.axvline(F1_Z_CORR_MIN, color="red", ls="--", lw=1); ax.axhline(F1_JACCARD_MIN, color="red", ls="--", lw=1)
    ax.set_xlabel("z corr (engine vs reference)"); ax.set_ylabel("|z|>=2 Jaccard")
    ax.set_title("F-1 vehicle fidelity (green=fit; tol 0.90/0.70)"); fig.tight_layout()
    fig.savefig(save / "f1_fidelity.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    # 4 F-2 plant/destroy
    f2 = detail["f2"]
    keys = [k for k in f2 if f2[k].get("planted_pass") is not None]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(np.arange(len(keys)) - 0.2, [f2[k]["planted_pass"] for k in keys], 0.4, label="planted PASS (want 1)")
    ax.bar(np.arange(len(keys)) + 0.2, [f2[k]["destroyed_pass"] for k in keys], 0.4, label="destroyed PASS (want 0)")
    ax.set_xticks(np.arange(len(keys))); ax.set_xticklabels(keys, rotation=90, fontsize=6)
    ax.set_title("F-2 non-vacuous leak: plant must pass, future-destroy must collapse"); ax.legend()
    fig.tight_layout(); fig.savefig(save / "f2_plant_destroy.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    PLOTS.mkdir(parents=True, exist_ok=True)
    logger.info("EXP-012 CONC-1 T2 — 24 exec-15m cells (T2a 14 S3 + T2b 10 S5); frozen referee domain=15m.")

    all_v: list[CellVerdict] = []
    pvals: dict[str, float] = {}
    detail = {"rows": {}, "pvals": {}, "f2": {}}
    for arm, cfg in ARMS.items():
        vs, d = screen_arm(arm, cfg["cells"], cfg["live"])
        all_v.extend(vs)
        for k in ("rows", "pvals", "f2"):
            detail[k].update(d[k])
        pvals.update(d["pvals"])

    holm_map = holm(pvals)                       # one family over all 24 cells
    for v in all_v:
        v.holm_admit = bool(holm_map.get(f"{v.arm}:{v.instrument}", False) and v.admit)

    live_admit = {f"{v.arm}:{v.instrument}" for v in all_v if v.holm_admit}
    surviving = shuffle_survivors("EXP-012-t2b-shuffle", T2B_CELLS, live_admit)
    tripwire_ok = (len(surviving) == 0) if (ROOT / "data" / "strategy_runs" / "EXP-012-t2b-shuffle").exists() else None

    # F-2 sanity: planted-positive should PASS wherever powered; destroyed should collapse.
    f2 = detail["f2"]
    f2_powered = [k for k in f2 if f2[k].get("planted_pass") is not None]
    f2_detect_ok = all(f2[k]["planted_pass"] for k in f2_powered) if f2_powered else None
    f2_collapse_ok = all(not f2[k]["destroyed_pass"] for k in f2_powered) if f2_powered else None

    def arm_stats(arm: str) -> dict:
        vs = [v for v in all_v if v.arm == arm]
        powered = [v for v in vs if v.powered]
        admit = [v for v in powered if v.holm_admit and not v.vehicle_unfit]
        return {"cells": len(vs), "powered": len(powered), "holm_admit_fit": len(admit),
                "unfit": sum(v.vehicle_unfit for v in vs)}

    stats = {a: arm_stats(a) for a in ARMS}
    tot_powered = sum(s["powered"] for s in stats.values())
    tot_admit = sum(s["holm_admit_fit"] for s in stats.values())

    # Predeclared interpretation (design §8), per arm on powered+fidelity-fit cells.
    if tripwire_ok is False or f2_collapse_ok is False:
        outcome = "REJECT_LEAK"
    elif tot_powered == 0:
        outcome = "UNPOWERED"
    elif tot_admit == 0:
        outcome = "NOT_TRADABLE"
    elif any(stats[a]["holm_admit_fit"] >= max(1, (stats[a]["powered"] + 1) // 2) for a in ARMS) \
            and tripwire_ok and f2_detect_ok:
        outcome = "TRADABLE_ON_TRAIN"
    elif tripwire_ok is None:
        outcome = "PENDING_TRIPWIRE"
    else:
        outcome = "NOT_TRADABLE"

    result = {
        "experiment": "EXP-012", "arms": stats, "domain": DOMAIN, "min_state_count": MIN_STATE,
        "n_powered": tot_powered, "n_holm_admit_fit": tot_admit,
        "tripwire_pass": tripwire_ok, "shuffle_survivors": surviving,
        "f2_planted_detect_ok": f2_detect_ok, "f2_future_destroy_collapse_ok": f2_collapse_ok,
        "outcome": outcome, "holm": holm_map, "pvals": pvals,
        "cells": [asdict(v) for v in all_v], "f2": f2,
    }
    (RESULTS / "verdict.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    plot_all(all_v, detail, PLOTS)
    logger.info("VERDICT: %s | powered=%d admit(fit)=%d tripwire=%s f2_detect=%s f2_collapse=%s",
                outcome, tot_powered, tot_admit, tripwire_ok, f2_detect_ok, f2_collapse_ok)
    logger.info("per-arm: %s -> results/verdict.json", stats)


if __name__ == "__main__":
    main()
