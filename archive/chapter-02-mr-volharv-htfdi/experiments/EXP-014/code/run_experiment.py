"""
EXP-014 — CF-MR-004/HYP-002: faithful full-exit cross-instrument MR, tradability + per-leg audit.

ANALYSIS-ONLY (L-01/P-09): reads only the engine emissions under data/strategy_runs/EXP-014-*/.
Run AFTER mr_characterisation.py (the MR read is booked before net-verdict contact, §7). Steps:
  (1) per-leg quantification (cis_trades): exit-reason split {form1/form2/horizon}, P&L by exit
      reason / trend bucket / vol regime / ladder level, across arms (none/R primary, none/S A/B,
      allow/R, extend/R) — a null must name exactly which leg fails where (design §9 exit-leg split).
  (2) availability E1 (entry fill rate) + E2 (gross P&L/filled RT). E3 reversion-completion is booked
      in mr_characterisation.py.
  (3) tradability (BINDING): the PRIMARY (none/R) engine-realized per-bar NET series → frozen 4h
      referee (referee_pstar.gate_stack_pstar, q*=0.75 — never tuned, L-12), per stratum (L-03),
      cross-axis Holm (L-08).
  (4) leak tripwires on any admitting cell: (T1 binding) peer-feed phase-shift future-destroy must
      collapse; (T2) label permutation — reported but mean-INVARIANT for the mean referee (vacuous,
      EXP-012/013 gate-debt). Non-vacuity BITE-CHECK: a planted synthetic edge must be detected in the
      cell (else the vehicle is vacuous → the cell cannot clear the leak gate, design §10 / L-08).
  (5) predeclared interpretation (design §12) → results/verdict.json + plots.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
import seaborn as sns

import lib

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("EXP-014")

RESULTS = lib.ROOT / "python" / "experiments" / "EXP-014" / "results"
PLOTS = lib.ROOT / "python" / "experiments" / "EXP-014" / "plots"
F2_PLANT_BPS = 8.0                 # planted detectable edge for the non-vacuity bite-check (power)
EXIT_REASONS = ("form1_reversion", "form2_favorable_limit", "horizon_time_stop")


@dataclass
class CellVerdict:
    series: str
    instrument: str
    arm: str
    n_bars: int
    n_entries: int
    fill_rate: float                # E1 availability: entries / armable (non-warmup, non-gap) bars
    exit_form1: int
    exit_form2: int
    exit_horizon: int
    net_mean_bps: float
    gross_mean_bps: float
    ci_low_net: float
    ci_low_gross: float
    n_episodes: int
    admit_net: bool
    admit_gross: bool
    holm_admit_net: bool
    powered: bool
    cost_bps: float


# --------------------------------------------------------------------------- #
# Per-leg quantification (cis_trades) — the exit-leg split (finding C / L-14).
# --------------------------------------------------------------------------- #
def leg_breakdown(cis: pl.DataFrame) -> dict:
    if cis.height == 0:
        return {"n_trades": 0, "by_reason": {}, "by_trend": {}, "by_vol": {}, "by_ladder": {}}

    def agg(col: str) -> dict:
        g = cis.group_by(col).agg(n=pl.len(), mean_bps=pl.col("RealizedBps").mean(),
                                  med_bars=pl.col("BarsHeld").median())
        return {str(r[col]): {"n": int(r["n"]), "mean_bps": float(r["mean_bps"] or 0.0),
                              "med_bars": float(r["med_bars"] or 0.0)} for r in g.iter_rows(named=True)}
    by_reason = {rsn: {"n": 0, "mean_bps": float("nan")} for rsn in EXIT_REASONS}
    by_reason.update(agg("ExitReason"))
    return {"n_trades": cis.height, "by_reason": by_reason, "by_trend": agg("EntryTrendDir"),
            "by_vol": agg("EntryVolRegime"), "by_ladder": agg("LadderLevel")}


def reason_counts(cis: pl.DataFrame) -> tuple[int, int, int]:
    if cis.height == 0:
        return (0, 0, 0)
    c = {r["ExitReason"]: int(r["n"]) for r in
         cis.group_by("ExitReason").agg(n=pl.len()).iter_rows(named=True)}
    return (c.get("form1_reversion", 0), c.get("form2_favorable_limit", 0), c.get("horizon_time_stop", 0))


# --------------------------------------------------------------------------- #
# Adjudication (binding referee) + availability E1/E2.
# --------------------------------------------------------------------------- #
def fill_rate(positions: pl.DataFrame, n_entries: int) -> float:
    armable = positions.filter(~pl.col("Warmup"))
    if "MateGap" in armable.columns:
        armable = armable.filter(~pl.col("MateGap"))
    return float(n_entries / armable.height) if armable.height else float("nan")


def adjudicate(cell: lib.Cell) -> tuple[CellVerdict, float]:
    positions, cis = cell.positions, cell.cis_trades
    cost_bps = lib.cost_for(cell.instrument)
    ret, pos, net = lib.assemble_realized_bps(positions, cost_bps=cost_bps)
    _, _, gross = lib.assemble_realized_bps(positions, cost_bps=0.0)
    core_net = lib.pstar_core(ret, pos, net, cost_bps)
    from xen.referee_adaptive import adaptive_row
    row_net = adaptive_row(core_net, alpha=lib.ALPHA)
    row_gross = adaptive_row(lib.pstar_core(ret, pos, gross, 0.0), alpha=lib.ALPHA)
    n_entries = cis.height if cis.height else int(
        np.sum(~np.isnan(positions.get_column("EntryFillPrice").to_numpy().astype(float))))
    f1, f2, fh = reason_counts(cis)
    n_epi = int(core_net.get("n_episodes", 0))
    v = CellVerdict(
        series=cell.series, instrument=cell.instrument, arm=cell.arm, n_bars=positions.height,
        n_entries=n_entries, fill_rate=fill_rate(positions, n_entries),
        exit_form1=f1, exit_form2=f2, exit_horizon=fh,
        net_mean_bps=float(np.mean(net[net != 0.0]) if np.any(net != 0.0) else 0.0),
        gross_mean_bps=float(np.mean(gross[gross != 0.0]) if np.any(gross != 0.0) else 0.0),
        ci_low_net=float(row_net["ci_lower_bps"]), ci_low_gross=float(row_gross["ci_lower_bps"]),
        n_episodes=n_epi, admit_net=bool(row_net["passed"]), admit_gross=bool(row_gross["passed"]),
        holm_admit_net=False, powered=bool(core_net["l1"] and n_epi >= lib.MIN_STATE), cost_bps=cost_bps)
    return v, lib.boot_p(core_net)


# --------------------------------------------------------------------------- #
# Leak tripwires + non-vacuity bite-check (design §10).
# --------------------------------------------------------------------------- #
def bite_check(cell: lib.Cell) -> dict:
    """Non-vacuity gate: a planted synthetic reversion edge MUST be detected in this cell (power),
    and block-permute MUST collapse it. A tripwire that cannot bite the plant is vacuous → the cell
    cannot clear the leak gate (forecloses the EXP-012/013 mean-invariant vacuity)."""
    from xen.referee_adaptive import adaptive_row
    cost_bps = lib.cost_for(cell.instrument)
    ret, pos, net = lib.assemble_realized_bps(cell.positions, cost_bps=cost_bps)
    active = pos != 0.0
    if active.sum() < lib.MIN_STATE:
        return {"planted_pass": None, "permute_collapse": None, "note": "unpowered_for_plant"}
    planted = net + F2_PLANT_BPS * active.astype(float)
    planted_pass = bool(adaptive_row(lib.pstar_core(ret, pos, planted, cost_bps), alpha=lib.ALPHA)["passed"])
    rng = np.random.default_rng(lib.SEED)
    permuted = planted[rng.permutation(len(planted))]
    permute_collapse = not bool(adaptive_row(lib.pstar_core(ret, pos, permuted, cost_bps),
                                             alpha=lib.ALPHA)["passed"])
    return {"planted_pass": planted_pass, "permute_collapse": permute_collapse,
            "note": "label_perm_mean_invariant_expected" if not permute_collapse else "ok"}


def phase_shift_survivors(series: str, admits: set[str]) -> list[str] | None:
    """T1 (binding): re-adjudicate the peer-feed phase-shift twin of each live-admitting cell; a
    surviving net-admit ⇒ the edge is not cross-instrument ⇒ leak ⇒ REJECT. None if no shift run."""
    root = lib.run_root(series, lib.PRIMARY_ARM, shift=True)
    if not root.exists() or not any(root.iterdir()):
        return None
    surviving = []
    for inst in lib.SERIES[series]["cells"]:
        if f"{series}:{inst}" not in admits:
            continue
        try:
            cell = lib.load_cell(series, lib.PRIMARY_ARM, inst, shift=True)
        except FileNotFoundError:
            continue
        v, _ = adjudicate(cell)
        if v.admit_net:
            surviving.append(f"{series}:{inst}")
    return surviving


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def screen_primary() -> tuple[list[CellVerdict], dict, dict, dict, dict]:
    """Binding tradability (PRIMARY none/R): per-cell referee + bite-check + provenance."""
    verdicts, pvals, bite, prov, legs = [], {}, {}, {}, {}
    for series, cfg in lib.SERIES.items():
        for inst in cfg["cells"]:
            try:
                cell = lib.load_cell(series, lib.PRIMARY_ARM, inst)
            except FileNotFoundError as exc:
                logger.warning("skip %s:%s — %s", series, inst, exc)
                continue
            key = f"{series}:{inst}"
            prov[key] = lib.validate_provenance(cell.positions, inst)
            v, p = adjudicate(cell)
            verdicts.append(v)
            pvals[key] = p
            bite[key] = bite_check(cell)
            legs[key] = leg_breakdown(cell.cis_trades)
            logger.info("[%s] %s: entries=%d fill=%.2f epi=%d(min%d) exit(f1/f2/h)=%d/%d/%d "
                        "gross=%.2f(ci%.2f a=%s) net=%.2f(ci%.2f a=%s) cost=%.1f p=%.4f", series, inst,
                        v.n_entries, v.fill_rate, v.n_episodes, lib.MIN_STATE, v.exit_form1, v.exit_form2,
                        v.exit_horizon, v.gross_mean_bps, v.ci_low_gross, v.admit_gross, v.net_mean_bps,
                        v.ci_low_net, v.admit_net, v.cost_bps, p)
    return verdicts, pvals, bite, prov, legs


def disclosure_legs() -> dict:
    """Per-leg breakdown for the disclosure arms (A/B static, allow, extend) — same emission family."""
    out: dict = {}
    for arm in lib.ARMS:
        if arm == lib.PRIMARY_ARM:
            continue
        for series, cfg in lib.SERIES.items():
            for inst in cfg["cells"]:
                try:
                    cell = lib.load_cell(series, arm, inst)
                except FileNotFoundError:
                    continue
                out[f"{arm}:{series}:{inst}"] = leg_breakdown(cell.cis_trades)
    return out


def plot_all(verdicts: list[CellVerdict], legs: dict, save) -> None:
    if not verdicts:
        return
    sns.set_theme(style="whitegrid")
    labels = [f"{v.series}:{v.instrument}" for v in verdicts]
    x = np.arange(len(verdicts))
    # 1 net vs gross per cell (binding tradability)
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.errorbar(x - 0.15, [v.gross_mean_bps for v in verdicts],
                yerr=[max(v.gross_mean_bps - v.ci_low_gross, 0) for v in verdicts], fmt="o", ms=3,
                capsize=2, color="#69c", label="gross (no cost) — availability")
    ax.errorbar(x + 0.15, [v.net_mean_bps for v in verdicts],
                yerr=[max(v.net_mean_bps - v.ci_low_net, 0) for v in verdicts], fmt="s", ms=3,
                capsize=2, color="#c63", label="net (cost) — tradability")
    ax.axhline(0, color="red", ls="--", lw=1)
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=90, fontsize=6)
    ax.set_title("EXP-014 PRIMARY (none/R) per-cell realized bps: gross vs net (ci_low bar)")
    ax.set_ylabel("bps/active"); ax.legend(); fig.tight_layout()
    fig.savefig(save / "net_vs_gross_per_cell.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    # 2 exit-reason split (stacked, fraction by reason)
    fig, ax = plt.subplots(figsize=(14, 5))
    tot = np.array([max(1, v.exit_form1 + v.exit_form2 + v.exit_horizon) for v in verdicts])
    f1 = np.array([v.exit_form1 for v in verdicts]) / tot
    f2 = np.array([v.exit_form2 for v in verdicts]) / tot
    fh = np.array([v.exit_horizon for v in verdicts]) / tot
    ax.bar(x, f1, label="form-1 event reversion", color="#2c7")
    ax.bar(x, f2, bottom=f1, label="form-2 favorable limit", color="#59b")
    ax.bar(x, fh, bottom=f1 + f2, label="horizon time stop", color="#c55")
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=90, fontsize=6)
    ax.set_ylabel("fraction of trades"); ax.set_ylim(0, 1)
    ax.set_title("EXP-014 exit-leg split (form-1 vs form-2 vs horizon) — which leg exits")
    ax.legend(); fig.tight_layout()
    fig.savefig(save / "exit_leg_split.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    # 3 episodes vs floor
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.bar(x, [v.n_episodes for v in verdicts],
           color=["#2c7" if v.n_episodes >= lib.MIN_STATE else "#c55" for v in verdicts])
    ax.axhline(lib.MIN_STATE, color="red", ls="--", lw=1, label=f"min_state {lib.MIN_STATE}")
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=90, fontsize=6)
    ax.set_title("EXP-014 episodes vs 4h power floor (green=powered)")
    ax.set_ylabel("episodes"); ax.legend(); fig.tight_layout()
    fig.savefig(save / "episodes_vs_floor.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    PLOTS.mkdir(parents=True, exist_ok=True)
    logger.info("EXP-014 CF-MR-004/HYP-002 tradability — 38 cells (S5/S7/S8 11 + S6 5); frozen 4h referee.")

    verdicts, pvals, bite, prov, legs = screen_primary()
    if not verdicts:
        logger.warning("No emissions found under data/strategy_runs/EXP-014-* — run Stage 3 first.")
        (RESULTS / "verdict.json").write_text(json.dumps(
            {"experiment": "EXP-014", "outcome": "NO_EMISSIONS"}, indent=2), encoding="utf-8")
        return

    holm_map = lib.holm(pvals)
    for v in verdicts:
        v.holm_admit_net = bool(holm_map.get(f"{v.series}:{v.instrument}", False) and v.admit_net)
    admits = {f"{v.series}:{v.instrument}" for v in verdicts if v.holm_admit_net}

    # T1 binding future-destroy (peer-feed phase-shift) on any admit; None if no shift run yet.
    survivors, tripwire_available = [], False
    for series in lib.SERIES:
        s = phase_shift_survivors(series, admits)
        if s is not None:
            tripwire_available = True
            survivors.extend(s)
    tripwire_ok = (len(survivors) == 0) if tripwire_available else None

    # Non-vacuity bite-check (per powered cell): planted edge must be detected.
    powered_bite = [k for k in bite if bite[k].get("planted_pass") is not None]
    bite_detect_ok = all(bite[k]["planted_pass"] for k in powered_bite) if powered_bite else None

    def arm_stats(series: str) -> dict:
        vs = [v for v in verdicts if v.series == series]
        powered = [v for v in vs if v.powered]
        return {"cells": len(vs), "powered": len(powered),
                "gross_admit": sum(v.admit_gross for v in powered),
                "net_holm_admit": sum(v.holm_admit_net for v in powered)}
    stats = {s: arm_stats(s) for s in lib.SERIES}
    tot_powered = sum(s["powered"] for s in stats.values())
    tot_net_admit = sum(s["net_holm_admit"] for s in stats.values())
    tot_gross_admit = sum(s["gross_admit"] for s in stats.values())

    # Predeclared interpretation (design §12). Binding future-destroy = T1; label-perm vacuous.
    if tripwire_ok is False:
        outcome = "REJECT_LEAK"
    elif tot_powered == 0:
        outcome = "UNPOWERED"
    elif tot_net_admit == 0:
        outcome = "NOT_TRADABLE"           # faithful full-exit: availability may be >0; net fails
    elif any(stats[s]["net_holm_admit"] >= max(1, (stats[s]["powered"] + 1) // 2) for s in lib.SERIES) \
            and tripwire_ok and bite_detect_ok:
        outcome = "TRADABLE_ON_TRAIN"      # → operator-gated counted TEST read (new D0)
    elif tripwire_ok is None:
        outcome = "PENDING_TRIPWIRE"
    else:
        outcome = "NOT_TRADABLE"

    result = {
        "experiment": "EXP-014", "family": "CF-MR-004", "hypothesis": "HYP-002", "domain": lib.DOMAIN,
        "primary_arm": lib.PRIMARY_ARM, "min_state_count": lib.MIN_STATE, "series": stats,
        "n_powered": tot_powered, "n_gross_admit": tot_gross_admit, "n_net_holm_admit": tot_net_admit,
        "tripwire_phase_shift_pass": tripwire_ok, "phase_shift_survivors": survivors,
        "bite_check_planted_detect_ok": bite_detect_ok,
        "label_perm_note": "mean-invariant for the mean referee (vacuous, EXP-012/013 gate-debt) — "
                           "binding future-destroy is T1 peer-feed phase-shift",
        "outcome": outcome, "holm": holm_map, "pvals": pvals,
        "cells": [asdict(v) for v in verdicts], "leg_breakdown": legs,
        "disclosure_legs": disclosure_legs(), "bite_check": bite, "provenance": prov,
    }
    (RESULTS / "verdict.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    plot_all(verdicts, legs, PLOTS)
    logger.info("VERDICT: %s | powered=%d gross_admit=%d net_holm_admit=%d tripwire=%s bite_detect=%s",
                outcome, tot_powered, tot_gross_admit, tot_net_admit, tripwire_ok, bite_detect_ok)


if __name__ == "__main__":
    main()
