"""Experiment EXP-009 — CF-MR-003/HYP-001 native re-screen: does price return to the anchor?

Implements the APPROVED design (python/experiments/EXP-009/design.md). Native, target-based re-screen of
CF-MR-003 after EXP-008's evaluation-vehicle mismatch (L-13). Same 2-leg VR∧HL selector; the ESTIMAND and
NULL change:

  * Estimands (target-based, real intrabar prices, event-specific horizon H_i = min(48, 3*half_life_i)):
      E1 anchor-hit rate (primary), E2 fraction-of-dislocation recovered, E3 time-to-anchor / half-life.
  * Null (operator-ratified): the SCREEN-FAIL extreme population {|z|>=2 AND VR∧HL fail}, dislocation-
    (|z|-bin) + ATR-regime matched, count-balanced, each control measured over its paired conditioned
    event's H_i (horizon-matched pairing — the window is never a pass-vs-fail confound). Random-timing and
    random-within-bin are disclosure-only.

ANALYSIS-ONLY, TRAIN-only, 0 reads, holdout sealed. Leak tripwires: time-reversal + pass/fail-label
permutation. Reuses EXP-008 infrastructure (data load, domain build, anchors, baskets) via `run_experiment`.

Run (from repo root): python python/experiments/EXP-009/code/run_experiment.py [--quick]
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
import seaborn as sns
from tqdm.auto import tqdm

from xen import availability_gate as ag
from xen import cross_domain_mr as cdm
from xen import reversion_targets as rt

# Reuse EXP-008 infrastructure (data load / domain build / anchors / baskets / constants).
_E8 = Path(__file__).resolve().parents[2] / "EXP-008" / "code"
sys.path.insert(0, str(_E8))
import run_experiment as R  # noqa: E402

logger = logging.getLogger("EXP-009")

# --------------------------------------------------------------------------- #
# Constants (design §4–§7; frozen before outcome contact)
# --------------------------------------------------------------------------- #
EXP_DIR = Path("python/experiments/EXP-009")
RESULTS_DIR = EXP_DIR / "results"
PLOTS_DIR = EXP_DIR / "plots"

SEED = 20260701
M_HORIZON = 3
H_CAP = 48
N_MIN = 100
# Endpoint-specific economic floors (Amendment B2, 2026-07-01): the single 0.03 floor was
# unit-inconsistent across endpoints. E1 anchor-hit = +3pp more likely to reach the mean; E2
# fraction-recovered = +5% more of the dislocation closed (noisier variable → larger floor).
DELTA_STAR_HIT = 0.03
DELTA_STAR_FRAC = 0.05
MIN_POWERED_CELLS = 4
MAJORITY = 0.50
N_BOOT_CI = 10_000
POOL_TOTAL = 4_000
N_TRIPWIRE_PERM = 20

# Binding admission endpoints (E3 time-to-anchor is descriptive/supportive, §7).
ENDPOINTS = (("hit", ag.STAT_MEAN, DELTA_STAR_HIT), ("frac", ag.STAT_MEDIAN, DELTA_STAR_FRAC))


@dataclass
class CellDiag:
    axis: str
    instrument: str
    n_events: int
    n_ctrl: int
    # E1 anchor-hit (primary)
    delta: float
    ci_low: float
    mde: float
    powered: bool
    passes_floor: bool
    hit_disposition: str
    # E2 fraction-recovered
    frac_delta: float
    frac_ci_low: float
    frac_mde: float
    frac_powered: bool
    frac_passes: bool
    frac_disposition: str
    # cell-level: powered/pass on EITHER binding endpoint (design §7 "E1 or E2")
    any_powered: bool
    any_pass: bool
    # leak + disclosure (hit)
    delta_timerev: float
    delta_labelperm: float
    delta_hit_vs_randtiming: float
    delta_hit_vs_randbin: float
    e3_cond_median: float
    e3_ctrl_median: float


def _disposition(n_ctrl: int, powered: bool, delta: float, ci_low: float, floor: float) -> str:
    """Precision-aware per-endpoint disposition (separates 'can't tell' from 'no signal')."""
    if n_ctrl < 2:
        return "UNTESTABLE"
    if powered and delta >= floor and np.isfinite(ci_low) and ci_low > 0.0:
        return "POWERED_PASS"
    if powered:
        return "POWERED_FAIL"                 # resolved: no edge >= floor
    if delta >= floor:
        return "UNPOWERED_HINT"               # point estimate clears floor, CI can't confirm
    return "UNPOWERED_NULL"                    # underpowered AND no hint of an edge


# --------------------------------------------------------------------------- #
# Pure helpers — extreme detection, screen pass/fail + per-event half-life
# --------------------------------------------------------------------------- #
def extreme_screen(ed: "R.ExecDomain", dev: np.ndarray, z: np.ndarray
                   ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Extreme bars (|z[i-1]|>=z*, regime defined) + per-bar screen-pass bool + fitted half-life."""
    n = ed.close.shape[0]
    z_lag = np.concatenate([[np.nan], z[:-1]])
    extreme = np.flatnonzero(
        (np.arange(n) >= cdm.W_S) & np.isfinite(z_lag) & (np.abs(z_lag) >= cdm.Z_STAR)
        & (ed.regime_lag >= 0))
    screen = np.zeros(n, dtype=bool)
    hl = np.full(n, np.nan, dtype=np.float64)
    for i in extreme:
        w = dev[i - cdm.W_S:i]
        screen[i] = cdm.mr_screen_pass(w)
        hl[i] = cdm.half_life(w)
    return extreme, screen, hl


def measure_set(idxs: np.ndarray, horizons: np.ndarray, hls: np.ndarray, ed: "R.ExecDomain",
                a_lag: np.ndarray, dev_lag: np.ndarray, reverse: bool = False) -> np.ndarray:
    """(k,3) array of (hit, frac, ttime) for entries measured over their given horizon/half-life."""
    out = []
    for c, H, hls in zip(idxs, horizons, hls):
        r = rt.measure_entry(int(c), ed.open, ed.low, ed.high, a_lag[c], dev_lag[c], int(H), hls,
                             reverse=reverse)
        out.append((np.nan, np.nan, np.nan) if r is None else r)
    return np.asarray(out, dtype=np.float64).reshape(-1, 3)


# --------------------------------------------------------------------------- #
# Cell assembly — conditioned vs screen-fail control (horizon-matched pairing)
# --------------------------------------------------------------------------- #
def build_cell(axis: str, sym: str, ed: "R.ExecDomain", dev: np.ndarray, z: np.ndarray,
               a_lag: np.ndarray, dev_lag: np.ndarray, rng: np.random.Generator
               ) -> tuple[dict, CellDiag] | None:
    """Assemble per-endpoint (cond, ctrl, pool) arrays + diagnostics for one instrument cell."""
    extreme, screen, hl = extreme_screen(ed, dev, z)
    horizon = rt.event_horizon(hl, M_HORIZON, H_CAP)
    z_lag = np.concatenate([[np.nan], z[:-1]])
    cond_all = extreme[screen[extreme] & (horizon[extreme] > 0)]
    fail_all = extreme[~screen[extreme]]
    if cond_all.shape[0] < N_MIN or fail_all.shape[0] < 2:
        return None

    cond = measure_set(cond_all, horizon[cond_all], hl[cond_all], ed, a_lag, dev_lag)
    keep = np.isfinite(cond[:, 0])
    cond_idx, cond = cond_all[keep], cond[keep]
    if cond_idx.shape[0] < N_MIN:
        return None

    # Fail population indexed by (|z|-bin, regime) for matched pairing.
    fbin = np.array([rt.dislocation_bin(abs(z_lag[c])) for c in fail_all])
    freg = ed.regime_lag[fail_all]
    groups: dict[tuple[int, int], np.ndarray] = {}
    for b in range(len(rt.ZBIN_EDGES) - 1):
        for rg in (0, 1, 2):
            sel = fail_all[(fbin == b) & (freg == rg)]
            if sel.shape[0]:
                groups[(b, rg)] = sel

    # 1:1 horizon-matched screen-fail control (each control uses the paired cond event's H, hl_scale).
    c_idx, c_H, c_hl = [], [], []
    for j in cond_idx:
        key = (rt.dislocation_bin(abs(z_lag[j])), int(ed.regime_lag[j]))
        pool = groups.get(key)
        if pool is None:
            continue
        c_idx.append(int(rng.choice(pool)))
        c_H.append(int(horizon[j]))
        c_hl.append(float(hl[j]))
    if len(c_idx) < N_MIN:
        return None
    ctrl = measure_set(np.array(c_idx), np.array(c_H), np.array(c_hl), ed, a_lag, dev_lag)
    ctrl = ctrl[np.isfinite(ctrl[:, 0])]

    # Permutation pool — fail bars, each measured over a random cond event's (H, hl_scale).
    pk = rng.integers(0, cond_idx.shape[0], size=POOL_TOTAL)
    pf = rng.choice(fail_all, size=POOL_TOTAL)
    pool_m = measure_set(pf, horizon[cond_idx][pk], hl[cond_idx][pk], ed, a_lag, dev_lag)
    pool_m = pool_m[np.isfinite(pool_m[:, 0])]

    col = {"hit": 0, "frac": 1, "ttime": 2}
    cells_in: dict[str, ag.CellReadInput] = {}
    ep: dict[str, dict] = {}
    for (name, kind, dstar) in ENDPOINTS:
        k = col[name]
        cv, tv, pv = cond[:, k], ctrl[:, k], pool_m[:, k]
        cv, tv, pv = cv[np.isfinite(cv)], tv[np.isfinite(tv)], pv[np.isfinite(pv)]
        delta = ag._stat_1d(cv, kind) - ag._stat_1d(tv, kind)
        s_cell = ag.cell_se(cv, tv, kind, rng, n_boot=N_BOOT_CI)
        mde = ag.Z_ONE_SIDED * s_cell if np.isfinite(s_cell) else float("nan")
        ci_low = delta - mde if np.isfinite(mde) else float("nan")
        powered = bool(cond_idx.shape[0] >= N_MIN and np.isfinite(mde) and mde <= dstar)
        passes = bool(powered and np.isfinite(ci_low) and delta >= dstar and ci_low > 0.0)
        cells_in[name] = ag.CellReadInput(cell_id=f"{sym}", cond_values=cv, ctrl_values=tv,
                                          pool_values=pv, n_cond=int(cv.shape[0]),
                                          underpowered=not powered)
        ep[name] = dict(delta=float(delta), ci_low=float(ci_low), mde=float(mde), powered=powered,
                        passes=passes, n_ctrl=int(tv.shape[0]),
                        disp=_disposition(int(tv.shape[0]), powered, delta, ci_low, dstar))

    # Leak tripwires on E1 (hit).
    cond_rev = measure_set(cond_idx, horizon[cond_idx], hl[cond_idx], ed, a_lag, dev_lag, reverse=True)
    ctrl_rev = measure_set(np.array(c_idx), np.array(c_H), np.array(c_hl), ed, a_lag, dev_lag,
                           reverse=True)
    d_timerev = (np.nanmean(cond_rev[:, 0]) - np.nanmean(ctrl_rev[:, 0]))
    union = np.concatenate([cond_idx, fail_all])
    lp = []
    for _ in range(N_TRIPWIRE_PERM):
        perm = rng.permutation(union.shape[0])
        pc = union[perm[:cond_idx.shape[0]]]
        pf2 = union[perm[cond_idx.shape[0]:cond_idx.shape[0] * 2]]
        hh = horizon[cond_idx]
        hs = hl[cond_idx]
        mc = measure_set(pc, hh, hs, ed, a_lag, dev_lag)
        mf = measure_set(pf2, hh[:pf2.shape[0]], hs[:pf2.shape[0]], ed, a_lag, dev_lag)
        lp.append(np.nanmean(mc[:, 0]) - np.nanmean(mf[:, 0]))
    d_labelperm = float(np.nanmean(lp)) if lp else float("nan")

    # Disclosure nulls (E1 hit): random-timing + random-within-|z|-bin.
    counts = R._regime_counts(ed.regime_lag, cond_idx)
    rt_idx = R.matched_random_idx(ed.regime_lag, counts, cond_idx.shape[0], rng)
    rt_hit = measure_set(rt_idx, horizon[cond_idx][:rt_idx.shape[0]], hl[cond_idx][:rt_idx.shape[0]],
                         ed, a_lag, dev_lag)
    d_randtiming = np.nanmean(cond[:, 0]) - np.nanmean(rt_hit[:, 0])
    all_ext = extreme
    rb_idx = rng.choice(all_ext, size=min(cond_idx.shape[0], all_ext.shape[0]), replace=False)
    rb_hit = measure_set(rb_idx, horizon[cond_idx][:rb_idx.shape[0]], hl[cond_idx][:rb_idx.shape[0]],
                         ed, a_lag, dev_lag)
    d_randbin = np.nanmean(cond[:, 0]) - np.nanmean(rb_hit[:, 0])

    h, f = ep["hit"], ep["frac"]
    diag = CellDiag(
        axis=axis, instrument=sym, n_events=int(cond_idx.shape[0]), n_ctrl=h["n_ctrl"],
        delta=h["delta"], ci_low=h["ci_low"], mde=h["mde"], powered=h["powered"],
        passes_floor=h["passes"], hit_disposition=h["disp"],
        frac_delta=f["delta"], frac_ci_low=f["ci_low"], frac_mde=f["mde"], frac_powered=f["powered"],
        frac_passes=f["passes"], frac_disposition=f["disp"],
        any_powered=bool(h["powered"] or f["powered"]), any_pass=bool(h["passes"] or f["passes"]),
        delta_timerev=float(d_timerev), delta_labelperm=d_labelperm,
        delta_hit_vs_randtiming=float(d_randtiming), delta_hit_vs_randbin=float(d_randbin),
        e3_cond_median=float(np.nanmedian(cond[:, 2])), e3_ctrl_median=float(np.nanmedian(ctrl[:, 2])))
    return cells_in, diag


# --------------------------------------------------------------------------- #
# Axis screening + verdict
# --------------------------------------------------------------------------- #
def run_axis(axis: str, gate_cells: dict[str, list[ag.CellReadInput]],
             diags: list[CellDiag], rng: np.random.Generator) -> dict:
    """Frozen-gate max-statistic admission over the two binding endpoints + §7 majority read."""
    subs = []
    for (name, kind, _dstar) in ENDPOINTS:
        subs.append(ag.run_sub_screen(name, name, kind, gate_cells[name], rng))
    max_powered = max((s.n_powered_cells for s in subs), default=0)
    combined = ag.combine_axis(axis, subs, null_band=(0, 1)) if max_powered else None
    # Powered / pass on EITHER binding endpoint (design §7 "E1 or E2").
    n_pow = sum(d.any_powered for d in diags)
    n_pass = sum(d.any_pass for d in diags)
    # Per-endpoint pass counts (per-stratum disclosure, L-03 — no axis-majority gate imposed here).
    hit_pass = sum(d.passes_floor for d in diags)
    frac_pass = sum(d.frac_passes for d in diags)
    return {"axis": axis, "perm_p": float(combined.perm_p) if combined else float("nan"),
            "s_m": int(combined.s_m) if combined else 0,
            "disposition": combined.disposition if combined else "UNPOWERED",
            "n_powered": int(n_pow), "n_pass_floor": int(n_pass),
            "hit_pass": int(hit_pass), "frac_pass": int(frac_pass),
            "eligible": bool(n_pow >= MIN_POWERED_CELLS),
            "majority": bool(n_pow and n_pass / n_pow >= MAJORITY)}


def adjudicate(axis_results: list[dict], per_cell: list[CellDiag]) -> dict:
    """§7 verdict: ADMIT-TO-EXPLORE / EXONERATE / INCONCLUSIVE (leak-gated on E1)."""
    admitting = []
    for a in axis_results:
        if not (a["holm_admit"] and a["eligible"] and a["majority"]):
            continue
        cells = [d for d in per_cell if d.axis == a["axis"] and d.any_pass]
        # Binding leak control = pass/fail LABEL PERMUTATION (must collapse: the screen, not a random
        # split of the same extreme bars, carries the edge). Time-reversal is NOT a valid future-destroyer
        # for the reach-anchor estimand (target-touch on a stationary MR deviation is time-symmetric —
        # non-collapse is expected, not a leak); reported as a diagnostic only (smoke-caught, Amendment B1).
        lp_ok = all(abs(d.delta_labelperm) < DELTA_STAR_HIT for d in cells
                    if np.isfinite(d.delta_labelperm))
        admitting.append({"axis": a["axis"], "leak_clean": bool(lp_ok)})
    clean = [x for x in admitting if x["leak_clean"]]
    n_elig = sum(a["eligible"] for a in axis_results)
    # Per-stratum tally (L-03): leak-clean per-instrument passes across the whole family, independent of
    # the axis-majority rule (the operator's point — partial pass across a family is legitimate).
    stratum_pass = [{"axis": d.axis, "instrument": d.instrument,
                     "hit_delta": d.delta, "frac_delta": d.frac_delta,
                     "endpoint": ("hit" if d.passes_floor else "frac")}
                    for d in per_cell if d.any_pass and np.isfinite(d.delta_labelperm)
                    and abs(d.delta_labelperm) < DELTA_STAR_HIT]
    # Disposition tallies across all cells (precision vs no-signal).
    disp = {}
    for d in per_cell:
        for lab in (d.hit_disposition, d.frac_disposition):
            disp[lab] = disp.get(lab, 0) + 1
    if clean:
        outcome = "ADMIT-TO-EXPLORE"
    elif n_elig < 0.5 * len(axis_results):
        outcome = "INCONCLUSIVE"
    else:
        outcome = "EXONERATE"
    return {"outcome": outcome, "admitting_axes": admitting, "n_eligible_axes": int(n_elig),
            "n_axes": len(axis_results), "n_stratum_pass": len(stratum_pass),
            "stratum_pass": stratum_pass, "disposition_tally": disp}


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def screen(instruments: tuple[str, ...]) -> dict:
    rng = np.random.default_rng(SEED)
    train = {s: R.load_train_1m(s) for s in tqdm(instruments, desc="load 1m TRAIN")}
    exec_mins = sorted({e for (_, e) in cdm.DOMAIN_PAIRS.values()})
    baskets = {e: R.build_baskets(train, e, instruments) for e in exec_mins}

    per_cell: list[CellDiag] = []
    axis_gate: dict[str, dict[str, list[ag.CellReadInput]]] = {}
    axis_diag: dict[str, list[CellDiag]] = {}
    for series in tqdm(cdm.SERIES, desc="series"):
        for pair, (a_min, e_min) in cdm.DOMAIN_PAIRS.items():
            axis = f"{series}|{pair}"
            axis_gate[axis] = {n: [] for (n, _k, _d) in ENDPOINTS}
            axis_diag[axis] = []
            for sym in instruments:
                ed = R.build_exec_domain(train[sym], e_min)
                anc = R.anchor_arrays(train[sym], a_min)
                basket = baskets[e_min][sym] if series == "S5_SPREAD" else None
                asr = cdm.anchor_series(series, ed.close, ed.ct, anc, basket)
                if not np.any(np.isfinite(asr.dev)):
                    continue
                a_level = rt.anchor_price_level(series, ed.close, asr.dev)
                a_lag = np.concatenate([[np.nan], a_level[:-1]])
                dev_lag = np.concatenate([[np.nan], asr.dev[:-1]])
                res = build_cell(axis, sym, ed, asr.dev, asr.z, a_lag, dev_lag, rng)
                if res is None:
                    continue
                cells_in, diag = res
                for name in axis_gate[axis]:
                    axis_gate[axis][name].append(cells_in[name])
                axis_diag[axis].append(diag)
                per_cell.append(diag)

    axis_results = [run_axis(ax, axis_gate[ax], axis_diag[ax], rng) for ax in axis_gate]
    pvals = [a["perm_p"] if np.isfinite(a["perm_p"]) else 1.0 for a in axis_results]
    for a, hp in zip(axis_results, ag.holm_adjust(pvals)):
        a["holm_p"] = float(hp)
        a["holm_admit"] = bool(hp <= ag.FWER)
    verdict = adjudicate(axis_results, per_cell)
    return {"axis_results": axis_results, "verdict": verdict, "per_cell": [asdict(d) for d in per_cell]}


# --------------------------------------------------------------------------- #
# Plots
# --------------------------------------------------------------------------- #
def _frame(per_cell: list[dict]) -> pl.DataFrame:
    return pl.DataFrame(per_cell) if per_cell else pl.DataFrame(
        schema={"axis": pl.Utf8, "instrument": pl.Utf8})


def plot_hit_heatmap(df: pl.DataFrame, path: Path) -> None:
    sns.set_theme(style="white")
    fig, ax = plt.subplots(figsize=(10, 7))
    if df.height:
        piv = df.pivot(values="delta", index="instrument", on="axis", aggregate_function="first")
        sns.heatmap(piv.drop("instrument").to_pandas(), ax=ax, cmap="RdBu_r", center=0, vmin=-0.1,
                    vmax=0.1, yticklabels=piv["instrument"].to_list(),
                    cbar_kws={"label": "Δ anchor-hit (cond − screen-fail)"})
        ax.set_xticklabels(ax.get_xticklabels(), fontsize=6, rotation=90)
    ax.set_title("EXP-009 P1 — Δ anchor-hit rate vs screen-fail control (per axis×instrument)")
    fig.tight_layout(); fig.savefig(path, dpi=150, bbox_inches="tight"); plt.close(fig)


def plot_null_contrast(df: pl.DataFrame, path: Path) -> None:
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(8, 5))
    if df.height:
        pw = df.filter(pl.col("powered"))
        data = [pw["delta"].to_numpy(), pw["delta_hit_vs_randbin"].to_numpy(),
                pw["delta_hit_vs_randtiming"].to_numpy()]
        ax.boxplot([d[np.isfinite(d)] for d in data],
                   labels=["screen-fail\n(binding)", "random-in-bin", "random-timing"])
        ax.axhline(0, color="k", lw=0.8); ax.axhline(DELTA_STAR_HIT, color="red", ls=":", label="Δ*")
    ax.set_ylabel("Δ anchor-hit (powered cells)")
    ax.set_title("EXP-009 P2 — null-choice contrast (binding vs disclosure nulls)")
    ax.legend()
    fig.tight_layout(); fig.savefig(path, dpi=150, bbox_inches="tight"); plt.close(fig)


def plot_tripwires(df: pl.DataFrame, path: Path) -> None:
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(8, 6))
    if df.height:
        pw = df.filter(pl.col("powered"))
        ax.scatter(pw["delta"], pw["delta_timerev"], s=14, alpha=0.6, label="time-reversal")
        ax.scatter(pw["delta"], pw["delta_labelperm"], s=14, alpha=0.6, marker="^", label="label-perm")
        ax.axhline(0, color="k", lw=0.8); ax.axvline(DELTA_STAR_HIT, color="red", ls=":", label="Δ*")
    ax.set_xlabel("real Δ hit"); ax.set_ylabel("tripwire Δ hit")
    ax.set_title("EXP-009 P3 — leak tripwires must collapse")
    ax.legend()
    fig.tight_layout(); fig.savefig(path, dpi=150, bbox_inches="tight"); plt.close(fig)


def plot_power(df: pl.DataFrame, path: Path) -> None:
    sns.set_theme(style="white")
    fig, ax = plt.subplots(figsize=(10, 7))
    if df.height:
        piv = df.pivot(values="mde", index="instrument", on="axis", aggregate_function="first")
        sns.heatmap(piv.drop("instrument").to_pandas(), ax=ax, cmap="viridis_r", vmin=0, vmax=0.1,
                    yticklabels=piv["instrument"].to_list(), cbar_kws={"label": "MDE (hit)"})
        ax.set_xticklabels(ax.get_xticklabels(), fontsize=6, rotation=90)
    ax.set_title(f"EXP-009 P4 — per-cell MDE (Δ*={DELTA_STAR_HIT})")
    fig.tight_layout(); fig.savefig(path, dpi=150, bbox_inches="tight"); plt.close(fig)


def plot_e3(df: pl.DataFrame, path: Path) -> None:
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(7, 6))
    if df.height:
        pw = df.filter(pl.col("powered"))
        ax.scatter(pw["e3_ctrl_median"], pw["e3_cond_median"], s=16, alpha=0.6)
        lim = 4.0
        ax.plot([0, lim], [0, lim], "k--", lw=0.8)
    ax.set_xlabel("time-to-anchor / half-life (control)")
    ax.set_ylabel("... (conditioned)")
    ax.set_title("EXP-009 P5 — E3 time-to-anchor (below diagonal = faster reversion)")
    fig.tight_layout(); fig.savefig(path, dpi=150, bbox_inches="tight"); plt.close(fig)


def plot_events(df: pl.DataFrame, path: Path) -> None:
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(9, 6))
    if df.height:
        for series in cdm.SERIES:
            s = df.filter(pl.col("axis").str.starts_with(series))
            if s.height:
                ax.scatter([series] * s.height, s["n_events"], s=14, alpha=0.5)
        ax.axhline(N_MIN, color="red", ls=":", label=f"N_min={N_MIN}")
    ax.set_yscale("symlog"); ax.set_ylabel("conditioned events / cell")
    ax.set_title("EXP-009 P6 — conditioned-event availability by series")
    ax.legend()
    fig.tight_layout(); fig.savefig(path, dpi=150, bbox_inches="tight"); plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="EXP-009 native reversion-to-anchor screen")
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    instruments = R.QUICK_INSTRUMENTS if args.quick else R.ALL_INSTRUMENTS
    out = screen(instruments)
    df = _frame(out["per_cell"])
    df.write_parquet(RESULTS_DIR / "per_cell.parquet")
    (RESULTS_DIR / "axis_results.json").write_text(json.dumps(out["axis_results"], indent=2))
    (RESULTS_DIR / "verdict.json").write_text(json.dumps(
        {"verdict": out["verdict"], "instruments": list(instruments), "quick": args.quick,
         "delta_star_hit": DELTA_STAR_HIT}, indent=2))

    plot_hit_heatmap(df, PLOTS_DIR / "P1_hit_heatmap.png")
    plot_null_contrast(df, PLOTS_DIR / "P2_null_contrast.png")
    plot_tripwires(df, PLOTS_DIR / "P3_tripwires.png")
    plot_power(df, PLOTS_DIR / "P4_power.png")
    plot_e3(df, PLOTS_DIR / "P5_time_to_anchor.png")
    plot_events(df, PLOTS_DIR / "P6_event_counts.png")

    v = out["verdict"]
    logger.info("VERDICT: %s | admitting=%d | eligible=%d/%d",
                v["outcome"], len(v["admitting_axes"]), v["n_eligible_axes"], v["n_axes"])
    print(json.dumps(v, indent=2))


if __name__ == "__main__":
    main()
