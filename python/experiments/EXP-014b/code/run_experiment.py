"""
EXP-014b — CF-MR-004/HYP-003 tradability + availability-merge (streamlined S8 rerun, amendment-003).

ANALYSIS-ONLY (L-01/P-09): reads only engine emissions under data/strategy_runs/EXP-014b-*/.
Run AFTER mr_characterisation.py (availability booked before net-verdict contact). Co-primary reads:

  AVAILABILITY  — symmetry two-barrier p_inward>0.5 (mr_characterisation.json), merged here per cell.
  TRADABILITY   — per-domain-bar engine-realized NET series → frozen referee (gate_stack_pstar,
                  domain∈{1h,4h}, q*=0.75 — never tuned, L-12), per stratum (cell,domain,arm),
                  cross-cell Holm per (domain,arm). Single-leg none = PRIMARY; allow/extend + both-leg
                  = disclosure. Both-leg uses the emitted aggregate per-bar series (grouped spread).

Fixes carried from audit.md: F1 (per-stratum UNPOWERED labeling — no global tot_powered shortcut);
F2 (bite-check scoped PER ADMITTING CELL, not a global all()). Leak tripwire: peer-feed phase-shift
must collapse net on any admit; per-cell planted bite-check gates non-vacuity.
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
logger = logging.getLogger("EXP-014b")

RESULTS = lib.ROOT / "python" / "experiments" / "EXP-014b" / "results"
PLOTS = lib.ROOT / "python" / "experiments" / "EXP-014b" / "plots"
F2_PLANT_BPS = 8.0
EXIT_REASONS = ("form1_reversion", "form2_favorable_limit", "open_at_end")


@dataclass
class CellVerdict:
    domain: str
    instrument: str
    arm: str
    ztag: str
    n_bars: int
    n_entries: int
    fill_rate: float
    exit_form1: int
    exit_form2: int
    exit_open_at_end: int
    net_mean_bps: float
    gross_mean_bps: float
    ci_low_net: float
    ci_low_gross: float
    n_episodes: int
    min_state: int
    admit_net: bool
    admit_gross: bool
    holm_admit_net: bool
    powered: bool
    avail_p_inward: float
    avail_ci_low: float
    avail_confirmed: bool
    status: str
    cost_bps: float
    avail_pass: bool = False           # raw two-barrier ci_low>0.5 (pre-tripwire)
    avail_tripwire_ran: bool = False   # the BINDING peer-feed phase-shift control was emitted
    avail_leak: bool = False           # raw passed AND survived the phase-shift (>0.5) → LEAK


# --------------------------------------------------------------------------- #
# Per-leg quantification (cis_trades).
# --------------------------------------------------------------------------- #
def reason_counts(cis: pl.DataFrame) -> tuple[int, int, int]:
    if cis.height == 0:
        return (0, 0, 0)
    c = {r["ExitReason"]: int(r["n"]) for r in
         cis.group_by("ExitReason").agg(n=pl.len()).iter_rows(named=True)}
    return (c.get("form1_reversion", 0), c.get("form2_favorable_limit", 0), c.get("open_at_end", 0))


def leg_breakdown(cis: pl.DataFrame) -> dict:
    if cis.height == 0:
        return {"n_trades": 0, "n_censored": 0, "by_reason": {}, "by_trend": {}, "by_vol": {},
                "mae_bps": float("nan"), "mfe_bps": float("nan")}
    comp = cis.filter(pl.col("Censored") == 0) if "Censored" in cis.columns else cis
    n_cens = cis.height - comp.height

    def agg(col: str) -> dict:
        if col not in comp.columns or comp.height == 0:
            return {}
        g = comp.group_by(col).agg(n=pl.len(), mean_bps=pl.col("RealizedBps").mean(),
                                   med_bars=pl.col("BarsHeld").median())
        return {str(r[col]): {"n": int(r["n"]), "mean_bps": float(r["mean_bps"] or 0.0)}
                for r in g.iter_rows(named=True)}
    by_reason = {rsn: {"n": 0, "mean_bps": float("nan")} for rsn in EXIT_REASONS}
    by_reason.update(agg("ExitReason"))
    by_reason["open_at_end"] = {"n": int(n_cens), "mean_bps": float("nan")}
    mae = float(comp.get_column("MaeBps").mean()) if "MaeBps" in comp.columns and comp.height else float("nan")
    mfe = float(comp.get_column("MfeBps").mean()) if "MfeBps" in comp.columns and comp.height else float("nan")
    return {"n_trades": cis.height, "n_censored": int(n_cens), "by_reason": by_reason,
            "by_trend": agg("EntryTrendDir"), "by_vol": agg("EntryVolRegime"), "mae_bps": mae, "mfe_bps": mfe}


# --------------------------------------------------------------------------- #
# Adjudication (binding referee) + availability merge.
# --------------------------------------------------------------------------- #
def no_data_verdict(domain: str, arm: str, ztag: str, inst: str, av: dict) -> "CellVerdict":
    """Explicit per-stratum placeholder for an incomplete/absent emission (L-03: counted, never
    dropped). Availability (if the PRIMARY emission produced it) is still attached; tradability is
    undefined. status='NO_DATA' — excluded from Holm/bite (no p-value), kept in the denominator."""
    return CellVerdict(
        domain=domain, instrument=inst, arm=arm, ztag=ztag, n_bars=0, n_entries=0,
        fill_rate=float("nan"), exit_form1=0, exit_form2=0, exit_open_at_end=0,
        net_mean_bps=float("nan"), gross_mean_bps=float("nan"),
        ci_low_net=float("nan"), ci_low_gross=float("nan"), n_episodes=0,
        min_state=lib.min_state_for(domain), admit_net=False, admit_gross=False,
        holm_admit_net=False, powered=False,
        avail_p_inward=av.get("p_inward", float("nan")), avail_ci_low=av.get("ci_low", float("nan")),
        avail_confirmed=bool(av.get("confirmed", False)), status="NO_DATA",
        cost_bps=lib.cost_for(inst, domain), avail_pass=bool(av.get("avail_pass", False)),
        avail_tripwire_ran=bool(av.get("shift_present", False)),
        avail_leak=bool(av.get("avail_leak", False)))


def fill_rate(positions: pl.DataFrame, n_entries: int) -> float:
    armable = positions.filter(~pl.col("Warmup"))
    if "MateGap" in armable.columns:
        armable = armable.filter(~pl.col("MateGap"))
    return float(n_entries / armable.height) if armable.height else float("nan")


def _realized_triple(cell: lib.Cell, *, gross: bool) -> tuple:
    """(returns, pos, realized_bps) for the referee — single-leg per-bar fills vs both-leg grouped
    spread. Both-leg routes to the faithful per-bar mirror (lib.both_leg_realized_series): the signal
    leg is the grouped-spread engine-realized net (Σ N+1 legs, per-leg RT cost via cost_for(LegSymbol,
    domain), L-02) settled at each group's exit bar; pos/returns stay real per-bar so the FROZEN
    referee's episode-count + naive-control legs are unchanged (L-12). cost_lookup raises loudly on a
    missing leg symbol (no silent 0). gross=True zeroes the cost."""
    if cell.arm in lib.BOTHLEG_ARMS:
        def cost_lookup(sym: str) -> float:
            return 0.0 if gross else lib.cost_for(sym, cell.domain)   # cost_for raises on unknown sym
        ret, pos, realized, _mask = lib.both_leg_realized_series(
            cell.positions, cell.cis_trades, instrument=cell.instrument, cost_lookup=cost_lookup)
        return ret, pos, realized
    cost = 0.0 if gross else lib.cost_for(cell.instrument, cell.domain)
    return lib.assemble_realized_bps(cell.positions, cost_bps=cost)


def adjudicate(cell: lib.Cell) -> tuple[CellVerdict, float]:
    positions, cis = cell.positions, cell.cis_trades
    domain = cell.domain
    cost_bps = lib.cost_for(cell.instrument, domain)
    min_state = lib.min_state_for(domain)
    ret, pos, net = _realized_triple(cell, gross=False)
    _, _, gross = _realized_triple(cell, gross=True)
    core_net = lib.pstar_core(ret, pos, net, cost_bps, domain)
    from xen.referee_adaptive import adaptive_row
    row_net = adaptive_row(core_net, alpha=lib.ALPHA)
    row_gross = adaptive_row(lib.pstar_core(ret, pos, gross, 0.0, domain), alpha=lib.ALPHA)
    if cell.arm in lib.BOTHLEG_ARMS:
        # both-leg entries = COMPLETED spread groups (one episode each), not leg rows (N+1 per group).
        comp = cis.filter((pl.col("Censored") == 0) & (pl.col("SpreadPositionId") > 0)) \
            if cis.height else cis
        n_entries = comp["SpreadPositionId"].n_unique() if comp.height else 0
    else:
        n_entries = cis.height if cis.height else int(
            np.sum(~np.isnan(positions.get_column("EntryFillPrice").to_numpy().astype(float))))
    f1, f2, f_oae = reason_counts(cis)
    n_epi = int(core_net.get("n_episodes", 0))
    v = CellVerdict(
        domain=domain, instrument=cell.instrument, arm=cell.arm, ztag=cell.ztag, n_bars=positions.height,
        n_entries=n_entries, fill_rate=fill_rate(positions, n_entries),
        exit_form1=f1, exit_form2=f2, exit_open_at_end=f_oae,
        net_mean_bps=float(np.mean(net[net != 0.0]) if np.any(net != 0.0) else 0.0),
        gross_mean_bps=float(np.mean(gross[gross != 0.0]) if np.any(gross != 0.0) else 0.0),
        ci_low_net=float(row_net["ci_lower_bps"]), ci_low_gross=float(row_gross["ci_lower_bps"]),
        n_episodes=n_epi, min_state=min_state,
        admit_net=bool(row_net["passed"]), admit_gross=bool(row_gross["passed"]),
        holm_admit_net=False, powered=bool(core_net["l1"] and n_epi >= min_state),
        avail_p_inward=float("nan"), avail_ci_low=float("nan"), avail_confirmed=False,
        status="", cost_bps=cost_bps)
    return v, lib.boot_p(core_net)


def bite_check(cell: lib.Cell) -> dict:
    """Non-vacuity: a planted +8bps/active edge MUST be detectable in this cell (else the referee is
    vacuous here → the cell cannot clear the leak gate). Computed per cell; GATED only on admitting
    cells (F2 fix — no global all())."""
    from xen.referee_adaptive import adaptive_row
    cost_bps = lib.cost_for(cell.instrument, cell.domain)
    if cell.arm in lib.BOTHLEG_ARMS:
        # Plant per EPISODE (per spread group) at the group's settlement bar — not per held bar —
        # so the non-vacuity check is on the grouped-spread object (one +Δ per group, mirroring the
        # single-leg per-episode plant). n_episodes = number of settlement bars.
        ret, pos, net, exit_mask = lib.both_leg_realized_series(
            cell.positions, cell.cis_trades, instrument=cell.instrument,
            cost_lookup=lambda s: lib.cost_for(s, cell.domain))
        n_plant = int(exit_mask.sum())
        if n_plant < lib.min_state_for(cell.domain):
            return {"planted_pass": None, "note": "unpowered_for_plant"}
        planted = net + F2_PLANT_BPS * exit_mask.astype(float)
    else:
        ret, pos, net = lib.assemble_realized_bps(cell.positions, cost_bps=cost_bps)
        active = pos != 0.0
        if active.sum() < lib.min_state_for(cell.domain):
            return {"planted_pass": None, "note": "unpowered_for_plant"}
        planted = net + F2_PLANT_BPS * active.astype(float)
    planted_pass = bool(adaptive_row(lib.pstar_core(ret, pos, planted, cost_bps, cell.domain),
                                     alpha=lib.ALPHA)["passed"])
    return {"planted_pass": planted_pass, "note": "ok"}


def load_availability() -> dict:
    """Merge availability (symmetry p_inward, all-slice) keyed by (domain, instrument, z_trigger)."""
    path = RESULTS / "mr_characterisation.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    out = {}
    for c in data.get("cells", []):
        allsl = c.get("slices", {}).get("all", {})
        shift_lo = c.get("ci_low_shift", float("nan"))
        avail_pass = allsl.get("ci_low", 0.0) > 0.5           # raw two-barrier ci_low > 0.5
        shift_present = bool(np.isfinite(shift_lo))            # the BINDING specificity control ran
        # CONFIRMED requires the peer-feed phase-shift tripwire to have RUN and COLLAPSED (≈0.5).
        # An ABSENT binding control is NOT a pass (L-01): raw-pass-without-tripwire = UNVERIFIED, not
        # confirmed. Availability CONFIRMED without the specificity control is exactly the false-
        # positive this programme exists to prevent.
        confirmed = bool(avail_pass and shift_present and shift_lo <= 0.5)
        # Raw two-barrier passed AND the phase-shift control RAN but did NOT collapse (>0.5) →
        # the "reversion" survives basket decorrelation ⇒ single-instrument auto-reversion, not the
        # cross-instrument S8 edge ⇒ availability LEAK (REJECT-class, design §4). Distinct from NULL.
        avail_leak = bool(avail_pass and shift_present and shift_lo > 0.5)
        out[f"{c['domain']}:{c['instrument']}:z{float(c['z_trigger']):.1f}"] = {
            "p_inward": allsl.get("p_inward", float("nan")),
            "ci_low": allsl.get("ci_low", float("nan")), "confirmed": confirmed,
            "avail_pass": bool(avail_pass), "shift_present": shift_present, "avail_leak": avail_leak}
    return out


def phase_shift_results(domain: str, arm: str, ztag: str, admits: set[str]) -> dict[str, bool | None]:
    """PER-CELL net phase-shift verdict for each admitting cell (audit C1b fix — the tripwire is
    per stratum, L-03; a family-wide any() splashed one survivor's REJECT onto collapsed peers).
    True = the cell's own shift net still admits (leak); False = collapsed; None = the binding
    shift emission is absent for that cell (UNVERIFIED — a missing control is never a pass, L-01)."""
    root = lib.run_root(domain, arm, ztag, shift=True)
    have_root = root.exists() and any(root.iterdir())
    out: dict[str, bool | None] = {}
    for inst in lib.S8_CELLS:
        key = f"{domain}:{inst}"
        if key not in admits:
            continue
        if not have_root:
            out[key] = None
            continue
        try:
            cell = lib.load_cell(domain, arm, inst, ztag=ztag, shift=True)
        except FileNotFoundError:
            out[key] = None
            continue
        v, _ = adjudicate(cell)
        out[key] = bool(v.admit_net)
    return out


# --------------------------------------------------------------------------- #
# Per-stratum status (F1 — per (cell,domain,arm), never a global shortcut).
# --------------------------------------------------------------------------- #
def cell_status(v: CellVerdict, bite_planted: bool | None, shift_leak: bool | None) -> str:
    """Per-stratum status. `shift_leak` = this cell's OWN net phase-shift result (True=survived
    ⇒ leak, False=collapsed, None=control missing) — per-cell, never family-wide (audit C1b).
    A tradability-unpowered or bite-blind cell is NEVER booked NOT_TRADABLE (audit C1a/C1c:
    UNPOWERED never FAIL; a referee that cannot detect a planted +8bps cannot certify a negative)."""
    avail_powered = np.isfinite(v.avail_ci_low)
    # Tradability is credible only when the frozen referee is powered (l1 + episode floor) AND
    # non-vacuous here (the planted edge is detectable; None = plant itself unpowered → not credible).
    trad_credible = v.powered and bite_planted is True
    if v.holm_admit_net and shift_leak is True:
        return "REJECT_LEAK"           # net survives basket decorrelation → not the S8 edge
    # Availability raw-passed but SURVIVED the peer-feed phase-shift → single-instrument auto-
    # reversion, not the cross-instrument S8 edge → leak (design §4). REJECT-class, not NULL.
    if v.avail_leak:
        return "REJECT_LEAK"
    if v.holm_admit_net and v.avail_confirmed and shift_leak is False and bite_planted:
        return "TRADABLE"
    # Net admits but the BINDING peer-feed phase-shift leak tripwire was never emitted → cannot
    # clear the leak gate; do NOT book NOT_TRADABLE (that implies a real negative read). Held.
    if v.holm_admit_net and shift_leak is None:
        return "TRADABILITY_UNVERIFIED"
    # Raw two-barrier passed but the binding specificity control is absent → availability UNVERIFIED,
    # not CONFIRMED and not NULL (L-01: absent control is not evidence either way).
    if v.avail_pass and not v.avail_tripwire_ran:
        return "AVAILABILITY_UNVERIFIED"
    if v.avail_confirmed:
        # availability real; the negative tradability read is bookable only if powered + non-vacuous
        return "NOT_TRADABLE" if trad_credible else "UNPOWERED_TRADABILITY"
    if avail_powered and not v.avail_confirmed:
        return "AVAILABILITY_NULL"     # outlier does not revert beyond chance
    if not trad_credible:
        return "UNPOWERED"
    return "NOT_TRADABLE"


# --------------------------------------------------------------------------- #
# Orchestration.
# --------------------------------------------------------------------------- #
def screen_stratum(domain: str, arm: str, ztag: str, avail: dict
                   ) -> tuple[list[CellVerdict], dict, dict, dict]:
    """Adjudicate one (domain, arm, ztag) family across all S8 cells. Availability is matched by the
    arm's traded magnitude z_trigger = ZSTARS[ztag] (read from the PRIMARY none z20 emission)."""
    z_trigger = lib.ZSTARS[ztag]
    verdicts, pvals, bite, legs = [], {}, {}, {}
    for inst in lib.S8_CELLS:
        av = avail.get(f"{domain}:{inst}:z{z_trigger:.1f}", {})
        try:
            cell = lib.load_cell(domain, arm, inst, ztag=ztag)
        except FileNotFoundError as exc:
            # Incomplete/absent emission (e.g. metadata-only stub from an interrupted run). Book an
            # explicit NO_DATA per-stratum verdict — never a silent drop from the denominator (L-03).
            logger.warning("NO_DATA %s/%s/%s:%s — %s", domain, arm, ztag, inst, exc)
            verdicts.append(no_data_verdict(domain, arm, ztag, inst, av))
            continue
        key = f"{domain}:{inst}"
        v, p = adjudicate(cell)
        av = avail.get(f"{domain}:{inst}:z{z_trigger:.1f}", {})
        v.avail_p_inward = av.get("p_inward", float("nan"))
        v.avail_ci_low = av.get("ci_low", float("nan"))
        v.avail_confirmed = bool(av.get("confirmed", False))
        v.avail_pass = bool(av.get("avail_pass", False))
        v.avail_tripwire_ran = bool(av.get("shift_present", False))
        v.avail_leak = bool(av.get("avail_leak", False))
        verdicts.append(v)
        pvals[key] = p
        bite[key] = bite_check(cell)
        legs[key] = leg_breakdown(cell.cis_trades)
    return verdicts, pvals, bite, legs


def summarise(all_verdicts: list[CellVerdict]) -> dict:
    def per(vs: list[CellVerdict]) -> dict:
        return {"cells": len(vs), "powered": sum(v.powered for v in vs),
                "avail_confirmed": sum(v.avail_confirmed for v in vs),
                "net_holm_admit": sum(v.holm_admit_net for v in vs),
                "status": {s: sum(v.status == s for v in vs)
                           for s in sorted({v.status for v in vs})}}
    keys = sorted({(v.domain, v.arm, v.ztag) for v in all_verdicts})
    return {f"{d}/{a}/{z}": per([v for v in all_verdicts
                                 if v.domain == d and v.arm == a and v.ztag == z])
            for d, a, z in keys}


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    PLOTS.mkdir(parents=True, exist_ok=True)
    logger.info("EXP-014b HYP-003 tradability + availability — S8, {1h,4h}, arms=%s, z*=%s.",
                lib.ARMS, tuple(lib.ZSTARS))
    avail = load_availability()
    if not avail:
        logger.warning("No mr_characterisation.json — run availability first (co-primary).")

    all_verdicts, all_pvals, all_bite, all_legs = [], {}, {}, {}
    for domain in lib.DOMAINS:
        for arm in lib.ARMS:
            for ztag in lib.ZSTARS:
                vs, pv, bt, lg = screen_stratum(domain, arm, ztag, avail)
                if not vs:
                    continue
                holm_map = lib.holm(pv)               # cross-cell Holm within (domain,arm,ztag)
                for v in vs:
                    v.holm_admit_net = bool(holm_map.get(f"{v.domain}:{v.instrument}", False) and v.admit_net)
                admits = {f"{v.domain}:{v.instrument}" for v in vs if v.holm_admit_net}
                shift_map = phase_shift_results(domain, arm, ztag, admits) if admits else {}
                for v in vs:
                    if v.status == "NO_DATA":
                        continue                       # incomplete emission — keep the L-03 placeholder
                    key = f"{v.domain}:{v.instrument}"
                    planted = bt.get(key, {}).get("planted_pass")
                    v.status = cell_status(v, planted, shift_map.get(key, False))
                    logger.info("[%s/%s/%s] %s: epi=%d(min%d) pow=%s fill=%.3f f1/f2/oae=%d/%d/%d "
                                "net=%.2f(ci%.2f a=%s) avail p_in=%.3f(ci%.3f conf=%s) => %s",
                                v.domain, v.arm, v.ztag, v.instrument, v.n_episodes, v.min_state,
                                v.powered, v.fill_rate, v.exit_form1, v.exit_form2, v.exit_open_at_end,
                                v.net_mean_bps, v.ci_low_net, v.admit_net, v.avail_p_inward,
                                v.avail_ci_low, v.avail_confirmed, v.status)
                all_verdicts.extend(vs)
                all_pvals.update({f"{arm}/{ztag}|{k}": p for k, p in pv.items()})
                all_bite.update({f"{domain}/{arm}/{ztag}:{k.split(':')[1]}": b for k, b in bt.items()})
                all_legs.update({f"{domain}/{arm}/{ztag}:{k.split(':')[1]}": l for k, l in lg.items()})

    if not all_verdicts:
        (RESULTS / "verdict.json").write_text(json.dumps(
            {"experiment": "EXP-014b", "outcome": "NO_EMISSIONS"}, indent=2), encoding="utf-8")
        logger.warning("No emissions under data/strategy_runs/EXP-014b-* — run Stage 3 first.")
        return

    summary = summarise(all_verdicts)
    n_tradable = sum(v.status == "TRADABLE" for v in all_verdicts)
    n_reject = sum(v.status == "REJECT_LEAK" for v in all_verdicts)
    n_unverified = sum(v.status in ("TRADABILITY_UNVERIFIED", "AVAILABILITY_UNVERIFIED")
                       for v in all_verdicts)
    if n_reject:
        outcome = "REJECT_LEAK"
    elif n_tradable:
        outcome = "TRADABLE_ON_TRAIN"       # → operator-gated counted TEST read
    elif n_unverified:
        # A raw availability pass or a net-admitting cell exists, but the BINDING peer-feed phase-
        # shift leak tripwire was never emitted → the run CANNOT conclude tradable/available. The
        # binding control must be emitted before any CONFIRMED/TRADABLE claim (L-01).
        outcome = "UNVERIFIED_TRIPWIRE_MISSING"
    elif any(v.avail_confirmed for v in all_verdicts):
        outcome = "NOT_TRADABLE_AVAILABILITY_REAL"
    elif any(v.status == "AVAILABILITY_NULL" for v in all_verdicts):
        outcome = "AVAILABILITY_NULL"
    else:
        outcome = "UNPOWERED"

    result = {"experiment": "EXP-014b", "family": "CF-MR-004", "hypothesis": "HYP-003",
              "domains": lib.DOMAINS, "arms": lib.ARMS, "zstars": lib.ZSTARS,
              "primary": f"{lib.PRIMARY_ARM}/{lib.PRIMARY_ZTAG}", "outcome": outcome,
              "n_tradable": n_tradable, "summary": summary,
              "cells": [asdict(v) for v in all_verdicts], "leg_breakdown": all_legs,
              "bite_check": all_bite, "availability": avail}
    (RESULTS / "verdict.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    plot_all(all_verdicts, PLOTS)
    logger.info("VERDICT: %s | tradable=%d cells=%d", outcome, n_tradable, len(all_verdicts))


def plot_all(verdicts: list[CellVerdict], save) -> None:
    prim = [v for v in verdicts if v.arm == lib.PRIMARY_ARM and v.ztag == lib.PRIMARY_ZTAG]
    if not prim:
        return
    sns.set_theme(style="whitegrid")
    labels = [f"{v.domain}:{v.instrument}" for v in prim]
    x = np.arange(len(prim))
    fig, ax = plt.subplots(figsize=(15, 5))
    ax.errorbar(x - 0.15, [v.gross_mean_bps for v in prim],
                yerr=[max(v.gross_mean_bps - v.ci_low_gross, 0) for v in prim], fmt="o", ms=3,
                capsize=2, color="#69c", label="gross")
    ax.errorbar(x + 0.15, [v.net_mean_bps for v in prim],
                yerr=[max(v.net_mean_bps - v.ci_low_net, 0) for v in prim], fmt="s", ms=3,
                capsize=2, color="#c63", label="net")
    ax.axhline(0, color="red", ls="--", lw=1)
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=90, fontsize=6)
    ax.set_title("EXP-014b PRIMARY (none) net vs gross per cell×domain")
    ax.set_ylabel("bps/active"); ax.legend(); fig.tight_layout()
    fig.savefig(save / "net_vs_gross_per_cell.png", dpi=150, bbox_inches="tight"); plt.close(fig)


if __name__ == "__main__":
    main()
