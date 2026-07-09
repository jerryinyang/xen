"""
EXP-014c — CF-MR-004/HYP-004 lean bracket exit-set adjudication + characterisation (ANALYSIS-ONLY).

Reads engine emissions only (E0 = reused EXP-014b 4h runs; E1-E3 = EXP-014c runs). Per design.md:
  BINDING   — frozen 4h referee per (cell, exit, arm, z*), cross-cell Holm per family; PRIMARY =
              (e3, none, z20) on JP225+EURUSD; per-cell phase-shift net-collapse (C1b discipline);
              per-admitting-cell bite (+8bps plant). Availability NOT re-run — merged from the
              audited EXP-014b mr_characterisation.json (4h cells).
  M2  — attribution table E0→E1→E2→E3 (none/z20), descriptive.
  M3  — E3 TP-share vs 014b p_inward consistency (decided legs = tp_anchor|sl_outward).
  M4  — session-hour characterisation (all cells; JP225 4-slot concentration flag).
  M4b — same-bar TP+SL race disclosure (BarsHeld==0 exits; both-barriers-in-entry-bar count).
  M5  — per-exit-reason P&L split.  M6 — with-trend/vol_low slices (informative).
Statuses use the audited post-C1 label logic (per-cell tripwire; NOT_TRADABLE only when powered
AND bite-non-vacuous; absent binding control ⇒ UNVERIFIED, never a pass — L-01).
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
logger = logging.getLogger("EXP-014c")

RESULTS = lib.ROOT / "python" / "experiments" / "EXP-014c" / "results"
PLOTS = lib.ROOT / "python" / "experiments" / "EXP-014c" / "plots"
AVAIL_014B = lib.ROOT / "python" / "experiments" / "EXP-014b" / "results" / "mr_characterisation.json"
BARS_PER_DAY = 6                     # 4h slots per day (session window = 4 consecutive slots)


# --------------------------------------------------------------------------- #
# Verdict dataclass + adjudication (frozen referee).
# --------------------------------------------------------------------------- #
@dataclass
class CellVerdict:
    etag: str
    arm: str
    ztag: str
    instrument: str
    n_bars: int
    n_trades: int
    n_censored: int
    exit_mix: dict
    net_mean_bps: float
    gross_mean_bps: float
    ci_low_net: float
    ci_low_gross: float
    n_episodes: int
    min_state: int
    admit_net: bool
    holm_admit_net: bool
    powered: bool
    bite_planted: bool | None
    shift_leak: bool | None          # own-cell net shift verdict (True=survived, None=missing)
    avail_p_inward: float
    avail_ci_low: float
    avail_confirmed: bool
    status: str
    cost_bps: float
    prov_breach_frac: float


def adjudicate(cell: lib.Cell) -> tuple[CellVerdict, float]:
    cost = lib.cost_for(cell.instrument)
    ret, pos, net = lib.assemble_realized_bps(cell.positions, cost_bps=cost)
    _, _, gross = lib.assemble_realized_bps(cell.positions, cost_bps=0.0)
    core_net = lib.pstar_core(ret, pos, net, cost)
    row_net = lib.referee_row(core_net)
    row_gross = lib.referee_row(lib.pstar_core(ret, pos, gross, 0.0))
    cis = cell.cis_trades
    n_cens = int(cis.filter(pl.col("Censored") == 1).height) if cis.height else 0
    mix = ({r["ExitReason"]: int(r["n"]) for r in
            cis.group_by("ExitReason").agg(n=pl.len()).iter_rows(named=True)}
           if cis.height else {})
    prov = lib.validate_provenance(cell.positions, cell.instrument)   # audit I2: wired in
    breach = max(prov["EntryFillPrice"]["breach_frac"], prov["ExitFillPrice"]["breach_frac"])
    n_epi = int(core_net.get("n_episodes", 0))
    v = CellVerdict(
        etag=cell.etag, arm=cell.arm, ztag=cell.ztag, instrument=cell.instrument,
        n_bars=cell.positions.height, n_trades=int(cis.height), n_censored=n_cens, exit_mix=mix,
        net_mean_bps=float(np.mean(net[net != 0.0]) if np.any(net != 0.0) else 0.0),
        gross_mean_bps=float(np.mean(gross[gross != 0.0]) if np.any(gross != 0.0) else 0.0),
        ci_low_net=float(row_net["ci_lower_bps"]), ci_low_gross=float(row_gross["ci_lower_bps"]),
        n_episodes=n_epi, min_state=lib.min_state(),
        admit_net=bool(row_net["passed"]), holm_admit_net=False,
        powered=bool(core_net["l1"] and n_epi >= lib.min_state()),
        bite_planted=None, shift_leak=None,
        avail_p_inward=float("nan"), avail_ci_low=float("nan"), avail_confirmed=False,
        status="", cost_bps=cost, prov_breach_frac=float(breach))
    return v, lib.boot_p(core_net)


def bite_check(cell: lib.Cell) -> bool | None:
    """Per-cell non-vacuity: a +8bps/active-bar plant must clear the frozen referee (F2 scope)."""
    cost = lib.cost_for(cell.instrument)
    ret, pos, net = lib.assemble_realized_bps(cell.positions, cost_bps=cost)
    active = pos != 0.0
    if active.sum() < lib.min_state():
        return None
    planted = net + lib.F2_PLANT_BPS * active.astype(float)
    return bool(lib.referee_row(lib.pstar_core(ret, pos, planted, cost))["passed"])


def shift_result(etag: str, arm: str, ztag: str, inst: str) -> bool | None:
    """Own-cell net phase-shift verdict (True=still admits ⇒ leak; None=control missing, L-01)."""
    root = lib.run_root(etag, arm, ztag, shift=True)
    if not root.exists() or not any(root.iterdir()):
        return None
    try:
        cell = lib.load_cell(etag, arm, inst, ztag=ztag, shift=True)
    except FileNotFoundError:
        return None
    v, _ = adjudicate(cell)
    return bool(v.admit_net)


def cell_status(v: CellVerdict) -> str:
    """Audited post-C1 per-stratum label logic (per-cell tripwire; UNPOWERED never FAIL)."""
    trad_credible = v.powered and v.bite_planted is True
    if v.holm_admit_net and v.shift_leak is True:
        return "REJECT_LEAK"
    if v.holm_admit_net and v.avail_confirmed and v.shift_leak is False and v.bite_planted:
        return "TRADABLE"
    if v.holm_admit_net and v.shift_leak is None:
        return "TRADABILITY_UNVERIFIED"
    if v.holm_admit_net and v.shift_leak is False:
        return "NET_ADMIT_AVAIL_NULL"     # net real+specific but availability was NULL in 014b
    if v.avail_confirmed:
        return "NOT_TRADABLE" if trad_credible else "UNPOWERED_TRADABILITY"
    if np.isfinite(v.avail_ci_low) and not v.avail_confirmed:
        return "AVAILABILITY_NULL"
    if not trad_credible:
        return "UNPOWERED"
    return "NOT_TRADABLE"


def load_avail_014b() -> dict:
    """Merged audited 014b availability (4h symmetry two-barrier), keyed inst:z_trigger."""
    if not AVAIL_014B.exists():
        return {}
    data = json.loads(AVAIL_014B.read_text(encoding="utf-8"))
    out = {}
    for c in data.get("cells", []):
        if c["domain"] != "4h":
            continue
        allsl = c.get("slices", {}).get("all", {})
        shift_lo = c.get("ci_low_shift", float("nan"))
        raw = allsl.get("ci_low", 0.0) > 0.5
        confirmed = bool(raw and np.isfinite(shift_lo) and shift_lo <= 0.5)
        out[f"{c['instrument']}:z{float(c['z_trigger']):.1f}"] = {
            "p_inward": allsl.get("p_inward", float("nan")),
            "ci_low": allsl.get("ci_low", float("nan")), "confirmed": confirmed}
    return out


# --------------------------------------------------------------------------- #
# Characterisation reads (M2-M6) — descriptive, disclosure-only.
# --------------------------------------------------------------------------- #
def entry_hour_and_pnl(cis: pl.DataFrame) -> pl.DataFrame:
    comp = cis.filter(pl.col("Censored") == 0)
    if comp.height == 0:
        return pl.DataFrame()
    return comp.with_columns(hour=pl.col("EntryTime").dt.hour())


def session_read(cis: pl.DataFrame) -> dict:
    """M4: per-4h-slot counts + net-P&L share; best wrapping 4-slot window P&L share."""
    d = entry_hour_and_pnl(cis)
    if d.height == 0:
        return {"n": 0}
    slots = (d["hour"].to_numpy() // 4).astype(int)          # 6 slots/day
    pnl = d["RealizedBps"].to_numpy().astype(float)
    slot_n = [int((slots == s).sum()) for s in range(BARS_PER_DAY)]
    slot_pnl = [float(pnl[slots == s].sum()) for s in range(BARS_PER_DAY)]
    tot = float(np.nansum(pnl))
    best_share, best_w = 0.0, -1
    if abs(tot) > 1e-9:
        for w in range(BARS_PER_DAY):
            share = sum(slot_pnl[(w + k) % BARS_PER_DAY] for k in range(4)) / tot
            if share > best_share:
                best_share, best_w = share, w
    return {"n": int(d.height), "slot_n": slot_n, "slot_pnl_bps": slot_pnl,
            "total_pnl_bps": tot, "best4_window_start_slot": best_w,
            "best4_pnl_share": float(best_share),
            "session_flag": bool(best_share > 0.5 and tot > 0)}


def same_bar_race_read(cell: lib.Cell) -> dict:
    """M4b: legs whose frozen TP and SL both lie inside the entry bar's [Low,High] (the availability
    read's 'ambiguous' class) — kept and m1-resolved by the engine; disclose count + outcome split."""
    cis = cell.cis_trades
    if cis.height == 0 or "SlPrice" not in cis.columns:
        return {"n_checked": 0}
    comp = cis.filter((pl.col("Censored") == 0) & pl.col("SlPrice").is_not_nan())
    if comp.height == 0:
        return {"n_checked": 0}
    posn = cell.positions.sort("SourceCloseTime")
    sct = posn["SourceCloseTime"].to_numpy()
    lo = posn["RealLow"].to_numpy().astype(float)
    hi = posn["RealHigh"].to_numpy().astype(float)
    ent = comp["EntryTime"].to_numpy()
    idx = np.searchsorted(sct, ent, side="left")             # entry bar = first bar closing > EntryTime
    idx = np.clip(idx, 0, len(sct) - 1)
    tp = comp["FixedExitPrice"].to_numpy().astype(float)
    sl = comp["SlPrice"].to_numpy().astype(float)
    both_in = (np.minimum(tp, sl) >= lo[idx]) & (np.maximum(tp, sl) <= hi[idx])
    rsn = comp["ExitReason"].to_list()
    bh = comp["BarsHeld"].to_numpy()
    race = both_in
    return {"n_checked": int(comp.height), "n_same_bar_race": int(race.sum()),
            "race_tp_first": int(sum(1 for i in np.flatnonzero(race) if rsn[i] == "tp_anchor")),
            "race_sl_first": int(sum(1 for i in np.flatnonzero(race) if rsn[i] == "sl_outward")),
            "n_barsheld0_exits": int((bh == 0).sum())}


def reason_pnl_split(cis: pl.DataFrame) -> dict:
    """M5: per-exit-reason n / mean bps / median bars held."""
    if cis.height == 0:
        return {}
    comp = cis.filter(pl.col("Censored") == 0)
    g = comp.group_by("ExitReason").agg(n=pl.len(), mean_bps=pl.col("RealizedBps").mean(),
                                        med_bars=pl.col("BarsHeld").median())
    out = {r["ExitReason"]: {"n": int(r["n"]), "mean_bps": float(r["mean_bps"] or 0.0),
                             "med_bars": float(r["med_bars"] or 0.0)}
           for r in g.iter_rows(named=True)}
    out["open_at_end"] = {"n": int(cis.height - comp.height), "mean_bps": float("nan"), "med_bars": float("nan")}
    return out


def slice_pnl(cis: pl.DataFrame) -> dict:
    """M6: entry-time conditioner slices (informative)."""
    if cis.height == 0:
        return {}
    comp = cis.filter(pl.col("Censored") == 0)
    out = {}
    for name, expr in (("with_trend", pl.col("Direction") * pl.col("EntryTrendDir") > 0),
                       ("counter_trend", pl.col("Direction") * pl.col("EntryTrendDir") < 0),
                       ("vol_low", pl.col("EntryVolRegime") == 0),
                       ("vol_high", pl.col("EntryVolRegime") == 2)):
        s = comp.filter(expr)
        out[name] = {"n": int(s.height),
                     "mean_bps": float(s["RealizedBps"].mean()) if s.height else float("nan")}
    return out


def consistency_read(v: CellVerdict, avail: dict) -> dict:
    """M3: E3 decided-leg TP share vs the 014b p_inward for this cell (binomial CI overlap)."""
    tp = v.exit_mix.get("tp_anchor", 0)
    sl = v.exit_mix.get("sl_outward", 0)
    p, lo, hi = lib.binom_ci(tp, tp + sl)
    key = f"{v.instrument}:z{lib.ZSTARS[v.ztag]:.1f}"
    p_in = avail.get(key, {}).get("p_inward", float("nan"))
    return {"tp": tp, "sl": sl, "tp_share": p, "ci": [lo, hi], "p_inward_014b": p_in,
            "consistent": bool(np.isfinite(p_in) and lo <= p_in <= hi) if tp + sl > 0 else None}


# --------------------------------------------------------------------------- #
# Plots.
# --------------------------------------------------------------------------- #
def plot_attribution(rows: list[CellVerdict], save) -> None:
    sns.set_theme(style="whitegrid")
    insts = list(lib.S8_CELLS)
    x = np.arange(len(insts))
    fig, ax = plt.subplots(figsize=(14, 5))
    colors = {"e0": "#999", "e1": "#69c", "e2": "#2a7", "e3": "#c63"}
    for j, e in enumerate(lib.EXITS):
        vals = []
        for inst in insts:
            v = next((r for r in rows if r.etag == e and r.instrument == inst), None)
            vals.append(v.net_mean_bps if v else np.nan)
        ax.bar(x + (j - 1.5) * 0.2, vals, width=0.18, color=colors[e], label=e.upper())
    ax.axhline(0, color="red", ls="--", lw=1)
    ax.set_xticks(x); ax.set_xticklabels(insts, rotation=45, fontsize=8)
    ax.set_ylabel("net bps/active"); ax.set_title("EXP-014c attribution: exit-set E0→E3 (none, z*=2.0)")
    ax.legend(); fig.tight_layout()
    fig.savefig(save / "attribution_exit_sets.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def plot_consistency(cons: dict, save) -> None:
    items = [(k, c) for k, c in cons.items() if c.get("tp", 0) + c.get("sl", 0) > 0]
    if not items:
        return
    fig, ax = plt.subplots(figsize=(10, 4.5))
    x = np.arange(len(items))
    ax.errorbar(x, [c["tp_share"] for _, c in items],
                yerr=[[c["tp_share"] - c["ci"][0] for _, c in items],
                      [c["ci"][1] - c["tp_share"] for _, c in items]],
                fmt="o", ms=4, capsize=3, color="#59b", label="E3 TP share (engine)")
    ax.scatter(x, [c["p_inward_014b"] for _, c in items], marker="x", color="#c33",
               label="p_inward (014b two-barrier)")
    ax.axhline(0.5, color="grey", ls=":", lw=1)
    ax.set_xticks(x); ax.set_xticklabels([k for k, _ in items], rotation=45, fontsize=8)
    ax.set_title("EXP-014c M3: traded object vs measured object (e3/none/z20)")
    ax.legend(); fig.tight_layout()
    fig.savefig(save / "tp_share_vs_p_inward.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def plot_primary(rows: list[CellVerdict], save) -> None:
    prim = [r for r in rows if (r.etag, r.arm, r.ztag) == lib.PRIMARY]
    if not prim:
        return
    fig, ax = plt.subplots(figsize=(10, 4.5))
    x = np.arange(len(prim))
    ax.errorbar(x - 0.12, [v.gross_mean_bps for v in prim],
                yerr=[max(v.gross_mean_bps - v.ci_low_gross, 0) for v in prim],
                fmt="o", ms=4, capsize=3, color="#69c", label="gross")
    ax.errorbar(x + 0.12, [v.net_mean_bps for v in prim],
                yerr=[max(v.net_mean_bps - v.ci_low_net, 0) for v in prim],
                fmt="s", ms=4, capsize=3, color="#c63", label="net")
    ax.axhline(0, color="red", ls="--", lw=1)
    ax.set_xticks(x); ax.set_xticklabels([v.instrument for v in prim], rotation=45, fontsize=8)
    ax.set_title("EXP-014c PRIMARY family (e3/none/z20): net vs gross per cell")
    ax.legend(); fig.tight_layout()
    fig.savefig(save / "primary_net_vs_gross.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def plot_session_jp225(session: dict, save) -> None:
    s = session.get("e3/none/z20:JP225")
    if not s or s.get("n", 0) == 0:
        return
    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.arange(BARS_PER_DAY)
    ax.bar(x - 0.15, s["slot_n"], width=0.3, color="#69c", label="entries")
    ax2 = ax.twinx()
    ax2.bar(x + 0.15, s["slot_pnl_bps"], width=0.3, color="#c63", label="net P&L (bps)")
    ax.set_xticks(x); ax.set_xticklabels([f"{4*i:02d}h" for i in range(BARS_PER_DAY)])
    ax.set_title(f"JP225 e3/none/z20 session profile (best-4 P&L share={s['best4_pnl_share']:.2f})")
    fig.tight_layout()
    fig.savefig(save / "jp225_session_profile.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def plot_reason_split(reason: dict, save) -> None:
    prim = {k.split(":")[1]: v for k, v in reason.items() if k.startswith("e3/none/z20:")}
    if not prim:
        return
    reasons = ("tp_anchor", "sl_outward", "time_stop")
    fig, ax = plt.subplots(figsize=(12, 4.5))
    x = np.arange(len(prim))
    colors = {"tp_anchor": "#2a7", "sl_outward": "#c33", "time_stop": "#888"}
    for j, rsn in enumerate(reasons):
        ax.bar(x + (j - 1) * 0.25, [prim[i].get(rsn, {}).get("mean_bps", np.nan) for i in prim],
               width=0.22, color=colors[rsn], label=rsn)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x); ax.set_xticklabels(list(prim), rotation=45, fontsize=8)
    ax.set_ylabel("mean bps/leg"); ax.set_title("EXP-014c M5: per-exit-reason P&L (e3/none/z20)")
    ax.legend(); fig.tight_layout()
    fig.savefig(save / "exit_reason_pnl.png", dpi=150, bbox_inches="tight"); plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration.
# --------------------------------------------------------------------------- #
def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    PLOTS.mkdir(parents=True, exist_ok=True)
    avail = load_avail_014b()
    if not avail:
        logger.warning("014b mr_characterisation.json missing — availability merge empty.")

    all_v: list[CellVerdict] = []
    sessions, reasons, races, slices, consistency = {}, {}, {}, {}, {}
    for etag in lib.EXITS:
        for arm in lib.ARMS:
            for ztag in lib.ZSTARS:
                pvals, vs = {}, []
                for inst in lib.S8_CELLS:
                    try:
                        cell = lib.load_cell(etag, arm, inst, ztag=ztag)
                    except FileNotFoundError as exc:
                        logger.warning("NO_DATA %s/%s/%s:%s — %s", etag, arm, ztag, inst, exc)
                        continue
                    v, p = adjudicate(cell)
                    key = f"{etag}/{arm}/{ztag}:{inst}"
                    av = avail.get(f"{inst}:z{lib.ZSTARS[ztag]:.1f}", {})
                    v.avail_p_inward = av.get("p_inward", float("nan"))
                    v.avail_ci_low = av.get("ci_low", float("nan"))
                    v.avail_confirmed = bool(av.get("confirmed", False))
                    v.bite_planted = bite_check(cell)
                    vs.append(v)
                    pvals[inst] = p
                    reasons[key] = reason_pnl_split(cell.cis_trades)
                    slices[key] = slice_pnl(cell.cis_trades)
                    if etag == "e3":
                        sessions[key] = session_read(cell.cis_trades)
                        races[key] = same_bar_race_read(cell)
                holm_map = lib.holm(pvals)
                for v in vs:
                    v.holm_admit_net = bool(holm_map.get(v.instrument, False) and v.admit_net)
                    if v.holm_admit_net:
                        v.shift_leak = shift_result(etag, arm, ztag, v.instrument)
                    v.status = cell_status(v)
                    logger.info("[%s/%s/%s] %s: epi=%d pow=%s net=%.2f(ci%.2f a=%s holm=%s) "
                                "bite=%s shift=%s avail(ci%.3f conf=%s) => %s",
                                etag, arm, ztag, v.instrument, v.n_episodes, v.powered,
                                v.net_mean_bps, v.ci_low_net, v.admit_net, v.holm_admit_net,
                                v.bite_planted, v.shift_leak, v.avail_ci_low, v.avail_confirmed,
                                v.status)
                    if (etag, arm, ztag) == lib.PRIMARY:
                        consistency[v.instrument] = consistency_read(v, avail)
                all_v.extend(vs)

    n_tradable = sum(v.status == "TRADABLE" for v in all_v)
    prim_v = [v for v in all_v if (v.etag, v.arm, v.ztag) == lib.PRIMARY
              and v.instrument in lib.PRIMARY_CELLS]
    n_leak = sum(v.status == "REJECT_LEAK" for v in all_v)
    if any(v.status == "TRADABLE" and v.instrument in lib.PRIMARY_CELLS
           and (v.etag, v.arm, v.ztag) == lib.PRIMARY for v in all_v):
        outcome = "TRADABLE_ON_TRAIN"
    elif n_leak:
        outcome = "REJECT_LEAK_DISCLOSURE" if not any(
            v.status == "REJECT_LEAK" for v in prim_v) else "REJECT_LEAK"
    elif all(v.status in ("NOT_TRADABLE",) for v in prim_v) and prim_v:
        outcome = "CREDIBLE_NEGATIVE_RETIRE"
    elif prim_v and all(not v.powered or v.bite_planted is not True for v in prim_v):
        outcome = "UNPOWERED_PRIMARY"
    else:
        outcome = "MIXED_SEE_CELLS"

    summary = {}
    for etag in lib.EXITS:
        for arm in lib.ARMS:
            for ztag in lib.ZSTARS:
                fam = [v for v in all_v if (v.etag, v.arm, v.ztag) == (etag, arm, ztag)]
                if fam:
                    summary[f"{etag}/{arm}/{ztag}"] = {
                        "cells": len(fam), "powered": sum(v.powered for v in fam),
                        "holm_admit": sum(v.holm_admit_net for v in fam),
                        "status": {s: sum(v.status == s for v in fam)
                                   for s in sorted({v.status for v in fam})}}

    result = {"experiment": "EXP-014c", "family": "CF-MR-004", "hypothesis": "HYP-004",
              "primary": "/".join(lib.PRIMARY), "primary_cells": lib.PRIMARY_CELLS,
              "outcome": outcome, "n_tradable": n_tradable, "summary": summary,
              "cells": [asdict(v) for v in all_v],
              "consistency_m3": consistency, "session_m4": sessions,
              "same_bar_races_m4b": races, "reason_split_m5": reasons, "slices_m6": slices}
    (RESULTS / "verdict.json").write_text(json.dumps(result, indent=2, default=str),
                                          encoding="utf-8")

    attr_rows = [v for v in all_v if v.arm == "none" and v.ztag == "z20"]
    plot_attribution(attr_rows, PLOTS)
    plot_consistency(consistency, PLOTS)
    plot_primary(all_v, PLOTS)
    plot_session_jp225(sessions, PLOTS)
    plot_reason_split(reasons, PLOTS)
    logger.info("VERDICT: %s | tradable=%d cells=%d -> results/verdict.json",
                outcome, n_tradable, len(all_v))


if __name__ == "__main__":
    main()
