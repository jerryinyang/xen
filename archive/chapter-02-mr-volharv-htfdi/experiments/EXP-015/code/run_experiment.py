"""
EXP-015 — CF-MR-005/HYP-001: mechanism characterisation of the 4h ladder scale-in own-price
MR harvest (ANALYSIS-ONLY). Implements design.md M1-M5 + §4 tripwires + §5 labels.

  M1  — per (cell, depth-bin, h): paired ΔR_h (event − matched-control median, L-15 #3) with
        moving-block bootstrap CI vs the vol-tercile x |ret|-decile matched-random control.
  M2  — depth gradient: median ΔR_24 per bin + bootstrap CI on the bin-slope; Part-A
        per-LadderLevel anatomy (disclosure companion).
  M3  — (a) Part-A extend vs shift twins: collapse fraction per ladder level (L-15);
        (b) with-drift vs against-drift ΔR_24 split; (c) ≥2-legs-open P&L overlap census.
  M4  — Part-A episode-level left tail (q01/q05, worst episode, top-k removal, deepest-decile
        P&L share); Part-B bin-4 never-recover-50%-in-48 census per year.
  M5  — Part-A net at {1,2,3}x frozen cost (disclosure only).
  Tripwire (binding, L-07): block-permuted-returns null on the full M1 pipeline; observed
        ΔR_24 must exceed the permuted 95% band; collapse fractions disclosed (W3/L-15).

Never simulates strategy P&L; never writes into data/strategy_runs/.
"""
from __future__ import annotations

import json
import logging

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
import seaborn as sns
from tqdm.auto import tqdm

import lib

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("EXP-015")

RESULTS = lib.ROOT / "python" / "experiments" / "EXP-015" / "results"
PLOTS = lib.ROOT / "python" / "experiments" / "EXP-015" / "plots"
TOP_K = (1, 3, 5)


# --------------------------------------------------------------------------- #
# Part B per-cell analysis (M1 / M2 / M3b / M4-census / tripwire)
# --------------------------------------------------------------------------- #
def deltas_by_bin(series: lib.CellSeries, ev: pl.DataFrame, controls: dict, h: int
                  ) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    """{bin: (paired deltas, event bar indices)} at horizon h."""
    out = {}
    for b in range(len(lib.DEPTH_BINS)):
        sub = ev.filter(pl.col("bin") == b)
        if sub.is_empty():
            continue
        d, ts = lib.paired_deltas(series, sub, controls, h)
        if len(d):
            out[b] = (d, ts)
    return out


def slope_ci(d_by_bin: dict[int, tuple[np.ndarray, np.ndarray]], seed: int
             ) -> tuple[float, float, float]:
    """Bootstrap CI on the depth-bin slope of median ΔR_24 (joint block resample, M2)."""
    obs = lib.bin_slope({b: float(np.median(d)) for b, (d, _) in d_by_bin.items()})
    if not np.isfinite(obs):
        return (obs, float("nan"), float("nan"))
    groups = {b: {int(u): d[(ts // lib.BLOCK) == u] for u in np.unique(ts // lib.BLOCK)}
              for b, (d, ts) in d_by_bin.items()}
    uniq = np.unique(np.concatenate([ts // lib.BLOCK for _, ts in d_by_bin.values()]))
    rng = np.random.default_rng(seed)
    stats = []
    for _ in range(lib.N_BOOTSTRAP):
        pick = uniq[rng.integers(0, len(uniq), size=len(uniq))]  # with multiplicity
        med = {}
        for b, g in groups.items():
            parts = [g[int(u)] for u in pick if int(u) in g]
            if parts:
                med[b] = float(np.median(np.concatenate(parts)))
        s = lib.bin_slope(med)
        if np.isfinite(s):
            stats.append(s)
    if len(stats) < 100:
        return (obs, float("nan"), float("nan"))
    return (obs, float(np.quantile(stats, lib.ALPHA / 2)),
            float(np.quantile(stats, 1 - lib.ALPHA / 2)))


def drift_split(series: lib.CellSeries, ev: pl.DataFrame, controls: dict, seed: int) -> dict:
    """M3b: ΔR_24 for with-drift vs against-drift events (drift = trailing 90-bar return)."""
    out = {}
    for name, expr in (("with_drift", pl.col("dir") * pl.col("drift").sign() > 0),
                       ("against_drift", pl.col("dir") * pl.col("drift").sign() < 0)):
        sub = ev.filter(expr)
        d, ts = lib.paired_deltas(series, sub, controls, lib.H_BIND)
        med, lo, hi = lib.block_boot_ci(d, ts, lib.N_BOOTSTRAP, seed)
        out[name] = {"n": int(len(d)), "delta_r24": med, "ci": [lo, hi]}
    return out


def bin4_census(series: lib.CellSeries, ev: pl.DataFrame) -> dict:
    """M4 Part-B: bin-4 (|z|>=3) events never recovering 50% within 48 bars, per year."""
    sub = ev.filter(pl.col("bin") == len(lib.DEPTH_BINS) - 1)
    per_year: dict[int, dict[str, int]] = {}
    for r in sub.iter_rows(named=True):
        mx = lib.running_max_recovery(series, r["t"], r["dir"], r["abs_s"], max(lib.HORIZONS))
        yr = int(series.year[r["t"]])
        slot = per_year.setdefault(yr, {"n": 0, "non_recovered": 0, "censored": 0})
        slot["n"] += 1
        if not np.isfinite(mx):
            slot["censored"] += 1
        elif mx < 0.5:
            slot["non_recovered"] += 1
    return per_year


def permute_null(series: lib.CellSeries, cell_idx: int) -> dict[int, dict]:
    """L-07 tripwire: per depth bin, the permuted-null band + collapse fraction of ΔR_24."""
    rng = np.random.default_rng([lib.SEED_PERM, cell_idx])
    per_bin: dict[int, list[float]] = {b: [] for b in range(len(lib.DEPTH_BINS))}
    for _ in tqdm(range(lib.N_PERM), desc=f"permute {series.symbol}", leave=False):
        perm = lib.permuted_series(series, rng)
        for b, v in lib.pipeline_delta_r(perm, rng).items():
            per_bin[b].append(v)
    out = {}
    for b, vals in per_bin.items():
        if len(vals) < 50:
            out[b] = {"n_replicates": len(vals)}
            continue
        arr = np.asarray(vals)
        out[b] = {"n_replicates": len(vals),
                  "null_median": float(np.median(arr)),
                  "null_band": [float(np.quantile(arr, 0.025)),
                                float(np.quantile(arr, 0.975))]}
    return out


def analyse_cell_b(symbol: str, cell_idx: int) -> dict:
    """Full Part-B read for one cell."""
    series = lib.build_series(symbol, lib.load_4h_bars(symbol))
    ev = lib.extract_events(series)
    stratum, valid = lib.build_strata(series, h_max=max(lib.HORIZONS))
    rng = np.random.default_rng([lib.SEED_BOOT, cell_idx])
    controls = lib.match_controls(ev, series, stratum, valid, rng)
    seed = lib.SEED_BOOT + cell_idx

    n_by_bin = {b: int(ev.filter(pl.col("bin") == b).height) for b in range(len(lib.DEPTH_BINS))}
    m1 = {}
    for h in lib.HORIZONS:
        dbb = deltas_by_bin(series, ev, controls, h)
        m1[h] = {b: dict(zip(("delta_r", "ci_lo", "ci_hi"),
                             lib.block_boot_ci(d, ts, lib.N_BOOTSTRAP, seed)),
                         n_measured=int(len(d)))
                 for b, (d, ts) in dbb.items()}
    d24 = deltas_by_bin(series, ev, controls, lib.H_BIND)
    slope, s_lo, s_hi = slope_ci(d24, seed)
    null = permute_null(series, cell_idx)
    return {
        "symbol": symbol,
        "n_bars_4h": int(len(series.z)),
        "fence": lib.FENCE_UTC[symbol],
        "events_by_bin": n_by_bin,
        "powered": n_by_bin.get(0, 0) >= lib.MIN_EVENTS,
        "m1": {str(h): {str(b): v for b, v in hb.items()} for h, hb in m1.items()},
        "m2_slope": {"slope": slope, "ci": [s_lo, s_hi]},
        "m3b": drift_split(series, ev, controls, seed),
        "m4_bin4_census": bin4_census(series, ev),
        "tripwire": {str(b): v for b, v in null.items()},
    }


# --------------------------------------------------------------------------- #
# §5 interpretation labels (frozen; UNPOWERED never FAIL)
# --------------------------------------------------------------------------- #
def cell_label(res: dict) -> str:
    """Mechanical per-cell label per design §5 (MECHANISM_SUPPORTED path + flags)."""
    if not res["powered"]:
        return "UNPOWERED"
    m1_24 = res["m1"][str(lib.H_BIND)]
    trip = res["tripwire"]
    qual = []
    for b in range(len(lib.DEPTH_BINS)):
        r = m1_24.get(str(b))
        t = trip.get(str(b), {})
        if (r and res["events_by_bin"].get(b, 0) >= lib.MIN_EVENTS
                and r["ci_lo"] > 0 and "null_band" in t
                and r["delta_r"] > t["null_band"][1]):
            qual.append(b)
    adjacent = any(b + 1 in qual for b in qual)
    against = res["m3b"]["against_drift"]
    drift_ok = np.isfinite(against["delta_r24"]) and against["delta_r24"] > 0
    if adjacent and drift_ok:
        return "MECHANISM_SUPPORTED"
    if adjacent and not drift_ok:
        return "DRIFT_EXCLUSIVE"
    any_sep = any(m1_24.get(str(b), {}).get("ci_lo", -1) > 0
                  for b in range(len(lib.DEPTH_BINS))
                  if res["events_by_bin"].get(b, 0) >= lib.MIN_EVENTS)
    return "INCONCLUSIVE" if any_sep else "NO_SEPARATION"


# --------------------------------------------------------------------------- #
# Part A per-cell anatomy (M2 companion / M3a / M3c / M4 / M5) — read-only
# --------------------------------------------------------------------------- #
def level_anatomy(cis: pl.DataFrame) -> dict:
    """Per-LadderLevel realized bps/leg, MAE/MFE, bars held, per-year split (M2 companion)."""
    comp = cis.filter(pl.col("Censored") == 0)
    out = {"n_censored": int(cis.height - comp.height)}
    for lv in lib.LADDER_LEVELS:
        s = comp.filter(pl.col("LadderLevel") == lv)
        if s.height == 0:
            out[f"L{lv}"] = {"n": 0}
            continue
        yearly = {str(r["year"]): float(r["mean_bps"]) for r in
                  s.with_columns(year=pl.col("EntryTime").dt.year())
                  .group_by("year").agg(mean_bps=pl.col("RealizedBps").mean())
                  .iter_rows(named=True)}
        out[f"L{lv}"] = {
            "n": int(s.height),
            "mean_bps": float(s["RealizedBps"].mean()),
            "sum_bps": float(s["RealizedBps"].sum()),
            "med_mae_bps": float(s["MaeBps"].median()),
            "med_mfe_bps": float(s["MfeBps"].median()),
            "med_bars_held": float(s["BarsHeld"].median()),
            "per_year_mean_bps": yearly,
        }
    return out


def shift_collapse(raw: dict, shifted: dict | None) -> dict:
    """M3a: per-level collapse fraction (shift net / raw net) — continuous, L-15 (never binary)."""
    if shifted is None:
        return {"available": False}
    out = {"available": True}
    for lv in lib.LADDER_LEVELS:
        r, s = raw.get(f"L{lv}", {}), shifted.get(f"L{lv}", {})
        rs, ss = r.get("sum_bps"), s.get("sum_bps")
        out[f"L{lv}"] = {
            "raw_sum_bps": rs, "shift_sum_bps": ss,
            "collapse_fraction": (float(ss / rs) if rs not in (None, 0.0) and ss is not None
                                  and abs(rs) > 1e-9 else None),
        }
    return out


def overlap_census(positions: pl.DataFrame, cost_bps: float) -> dict:
    """M3c: share of net P&L accrued while >=2 ladder legs are open."""
    bps, legs = lib.assemble_realized_bps(positions, cost_bps=cost_bps)
    total = float(bps.sum())
    multi = float(bps[legs >= 2].sum())
    return {"total_net_bps": total, "net_bps_while_ge2_legs": multi,
            "share_ge2_legs": (multi / total if abs(total) > 1e-9 else None),
            "n_bars_ge2_legs": int((legs >= 2).sum())}


def episode_tail(episodes: list[dict]) -> dict:
    """M4 Part-A: episode-level left tail + top-k sensitivity + deepest-decile P&L share."""
    if not episodes:
        return {"n_episodes": 0}
    pnl = np.array([e["pnl_bps"] for e in episodes])
    depth = np.array([e["max_abs_entry_z"] for e in episodes])
    total = float(pnl.sum())
    worst = episodes[int(np.argmin(pnl))]
    order = np.argsort(pnl)[::-1]
    topk = {str(k): float(total - pnl[order[:k]].sum()) for k in TOP_K}
    dec_edge = float(np.quantile(depth, 0.9))
    deep = pnl[depth >= dec_edge]
    return {
        "n_episodes": len(episodes),
        "total_pnl_bps": total,
        "q01_bps": float(np.quantile(pnl, 0.01)), "q05_bps": float(np.quantile(pnl, 0.05)),
        "worst_episode": {"start": str(worst["start"]), "pnl_bps": worst["pnl_bps"],
                          "max_abs_entry_z": worst["max_abs_entry_z"],
                          "n_legs": worst["n_legs"], "max_bars_held": worst["max_bars_held"],
                          "sum_leg_mae_bps": worst["sum_mae_bps"]},
        "net_after_topk_removed": topk,
        "deepest_decile": {"z_edge": dec_edge, "n": int(len(deep)),
                           "pnl_bps": float(deep.sum()),
                           "share_of_total": (float(deep.sum() / total)
                                              if abs(total) > 1e-9 else None)},
    }


def cost_stress(positions: pl.DataFrame, cost_bps: float) -> dict:
    """M5: net mean bps/active-bar at {1,2,3}x frozen cost (disclosure only, no gate)."""
    out = {}
    for m in lib.COST_MULTS:
        bps, _ = lib.assemble_realized_bps(positions, cost_bps=cost_bps * m)
        active = bps != 0.0
        out[f"{m:.0f}x"] = float(bps[active].mean()) if active.any() else 0.0
    return out


def analyse_cell_a(etag: str, ztag: str, symbol: str) -> dict | None:
    """Part-A anatomy for one (exit, extend, z*, cell); None when the emission is absent."""
    try:
        cell = lib.load_cell(etag, "extend", symbol, ztag)
    except FileNotFoundError:
        return None
    raw_levels = level_anatomy(cell.cis_trades)
    shifted_levels = None
    try:
        twin = lib.load_cell(etag, "extend", symbol, ztag, shift=True)
        shifted_levels = level_anatomy(twin.cis_trades)
    except FileNotFoundError:
        pass
    cost = lib.cost_for(symbol)
    return {
        "etag": etag, "ztag": ztag, "symbol": symbol, "cost_bps": cost,
        "n_legs": int(cell.cis_trades.height),
        "levels": raw_levels,
        "m3a_shift_collapse": shift_collapse(raw_levels, shifted_levels),
        "m3c_overlap": overlap_census(cell.positions, cost),
        "m4_episodes": episode_tail(lib.episodes_from_legs(cell.cis_trades)),
        "m5_cost_stress": cost_stress(cell.positions, cost),
    }


# --------------------------------------------------------------------------- #
# Plots (<=5, from analysis outputs only)
# --------------------------------------------------------------------------- #
def plot_delta_profiles(cells: dict, save) -> None:
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(3, 4, figsize=(18, 10), sharex=True)
    for ax, sym in zip(axes.flat, lib.CELLS):
        res = cells.get(sym)
        if not res:
            ax.axis("off")
            continue
        for b in range(len(lib.DEPTH_BINS)):
            xs, ys, lo, hi = [], [], [], []
            for h in lib.HORIZONS:
                r = res["m1"][str(h)].get(str(b))
                if r:
                    xs.append(h); ys.append(r["delta_r"])
                    lo.append(r["ci_lo"]); hi.append(r["ci_hi"])
            if xs:
                ax.plot(xs, ys, marker="o", ms=3, label=f"bin{b+1}")
                ax.fill_between(xs, lo, hi, alpha=0.15)
        ax.axhline(0, color="red", ls="--", lw=0.8)
        ax.set_title(sym, fontsize=9)
    axes.flat[0].legend(fontsize=7)
    axes.flat[-1].axis("off")
    fig.suptitle("EXP-015 M1: paired ΔR_h (event − matched control) per depth bin")
    fig.tight_layout()
    fig.savefig(save / "delta_r_profiles.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def plot_depth_gradient(cells: dict, save) -> None:
    fig, ax = plt.subplots(figsize=(14, 5))
    x = np.arange(len(lib.CELLS))
    width = 0.2
    for b in range(len(lib.DEPTH_BINS)):
        vals = [cells.get(s, {}).get("m1", {}).get(str(lib.H_BIND), {})
                .get(str(b), {}).get("delta_r", np.nan) for s in lib.CELLS]
        ax.bar(x + (b - 1.5) * width, vals, width=width * 0.9, label=f"bin{b+1}")
    slopes = [cells.get(s, {}).get("m2_slope", {}).get("slope", np.nan) for s in lib.CELLS]
    ax.plot(x, slopes, "k*", ms=8, label="bin-slope")
    ax.axhline(0, color="red", ls="--", lw=0.8)
    ax.set_xticks(x); ax.set_xticklabels(lib.CELLS, rotation=45, fontsize=8)
    ax.set_ylabel("median ΔR_24"); ax.set_title("EXP-015 M2: depth gradient of ΔR_24")
    ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(save / "depth_gradient.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def plot_ladder_anatomy(part_a: list[dict], save) -> None:
    rows = [r for r in part_a if r["etag"] == "e0"]
    if not rows:
        return
    fig, axes = plt.subplots(1, 2, figsize=(16, 5), sharey=True)
    for ax, ztag in zip(axes, lib.ZTAGS):
        sub = {r["symbol"]: r for r in rows if r["ztag"] == ztag}
        x = np.arange(len(lib.CELLS))
        for lv in lib.LADDER_LEVELS:
            vals = [sub.get(s, {}).get("levels", {}).get(f"L{lv}", {}).get("mean_bps", np.nan)
                    for s in lib.CELLS]
            ax.bar(x + (lv - 1) * 0.25, vals, width=0.22, label=f"L{lv}")
        ax.axhline(0, color="red", ls="--", lw=0.8)
        ax.set_xticks(x); ax.set_xticklabels(lib.CELLS, rotation=45, fontsize=8)
        ax.set_title(f"e0/extend/{ztag}")
    axes[0].set_ylabel("mean bps/leg"); axes[0].legend()
    fig.suptitle("EXP-015 M2 companion: engine-realized per-ladder-level P&L (read-only)")
    fig.tight_layout()
    fig.savefig(save / "ladder_anatomy.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def plot_episode_tail(part_a: list[dict], save) -> None:
    rows = [r for r in part_a if r["etag"] == "e0" and r["m4_episodes"].get("n_episodes")]
    if not rows:
        return
    fig, ax = plt.subplots(figsize=(14, 5))
    labels = [f"{r['symbol']}/{r['ztag']}" for r in rows]
    x = np.arange(len(rows))
    tot = [r["m4_episodes"]["total_pnl_bps"] for r in rows]
    top3 = [r["m4_episodes"]["net_after_topk_removed"]["3"] for r in rows]
    deep = [r["m4_episodes"]["deepest_decile"]["pnl_bps"] for r in rows]
    ax.bar(x - 0.25, tot, width=0.23, color="#69c", label="total episode P&L")
    ax.bar(x, top3, width=0.23, color="#c63", label="after top-3 removed")
    ax.bar(x + 0.25, deep, width=0.23, color="#2a7", label="deepest-decile episodes")
    ax.axhline(0, color="red", ls="--", lw=0.8)
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=60, fontsize=7)
    ax.set_ylabel("bps"); ax.set_title("EXP-015 M4: episode-level tail sensitivity (e0/extend)")
    ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(save / "episode_tail.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def plot_collapse(cells: dict, part_a: list[dict], save) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(16, 5))
    ax = axes[0]
    x = np.arange(len(lib.CELLS))
    for b in range(len(lib.DEPTH_BINS)):
        fr = []
        for s in lib.CELLS:
            res = cells.get(s, {})
            obs = res.get("m1", {}).get(str(lib.H_BIND), {}).get(str(b), {}).get("delta_r")
            t = res.get("tripwire", {}).get(str(b), {})
            fr.append(t.get("null_median", np.nan) / obs
                      if obs and abs(obs) > 1e-6 and "null_median" in t else np.nan)
        ax.plot(x, fr, marker="o", ms=4, label=f"bin{b+1}")
    ax.axhline(1, color="grey", ls=":"); ax.axhline(0, color="red", ls="--", lw=0.8)
    ax.set_xticks(x); ax.set_xticklabels(lib.CELLS, rotation=45, fontsize=8)
    ax.set_title("tripwire: permuted-null median ΔR / observed ΔR (collapse fraction)")
    ax.legend(fontsize=7)
    ax = axes[1]
    rows = [r for r in part_a if r["etag"] == "e0"
            and r["m3a_shift_collapse"].get("available")]
    labels = [f"{r['symbol']}/{r['ztag']}" for r in rows]
    xx = np.arange(len(rows))
    for lv in lib.LADDER_LEVELS:
        vals = [r["m3a_shift_collapse"].get(f"L{lv}", {}).get("collapse_fraction") for r in rows]
        ax.plot(xx, [v if v is not None else np.nan for v in vals], marker="s", ms=4,
                label=f"L{lv}")
    ax.axhline(1, color="grey", ls=":"); ax.axhline(0, color="red", ls="--", lw=0.8)
    ax.set_xticks(xx); ax.set_xticklabels(labels, rotation=60, fontsize=7)
    ax.set_title("M3a: shift-twin collapse fraction per ladder level (L-15)")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(save / "collapse_fractions.png", dpi=150, bbox_inches="tight"); plt.close(fig)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    PLOTS.mkdir(parents=True, exist_ok=True)

    # Part B — mechanism measurement
    cells: dict[str, dict] = {}
    for i, sym in enumerate(tqdm(lib.CELLS, desc="Part B cells")):
        res = analyse_cell_b(sym, i)
        res["label"] = cell_label(res)
        cells[sym] = res
        logger.info("[B] %s: events=%s powered=%s slope=%.3f label=%s",
                    sym, res["events_by_bin"], res["powered"],
                    res["m2_slope"]["slope"], res["label"])
    (RESULTS / "part_b_mechanism.json").write_text(
        json.dumps(cells, indent=2, default=str), encoding="utf-8")

    # Part A — read-only anatomy on extend arms (e0..e3, z15/z20)
    part_a: list[dict] = []
    for etag in tqdm(lib.EXITS, desc="Part A exits"):
        for ztag in lib.ZTAGS:
            for sym in lib.CELLS:
                row = analyse_cell_a(etag, ztag, sym)
                if row is None:
                    logger.warning("NO_DATA part-A %s/extend/%s:%s", etag, ztag, sym)
                    continue
                part_a.append(row)
    (RESULTS / "part_a_anatomy.json").write_text(
        json.dumps(part_a, indent=2, default=str), encoding="utf-8")

    # Family-level summary (§5 counts; per-cell labels stand independently, L-03)
    supported = [s for s in lib.CELLS if cells[s]["label"] == "MECHANISM_SUPPORTED"]
    classes = {("FX" if s in lib.FX else "IDX") for s in supported}
    summary = {
        "experiment": "EXP-015", "family": "CF-MR-005", "hypothesis": "HYP-001",
        "labels": {s: cells[s]["label"] for s in lib.CELLS},
        "n_supported": len(supported), "supported_cells": supported,
        "classes_covered": sorted(classes),
        "family_gate_supported": len(supported) >= 3 and len(classes) >= 2,
        "n_powered": sum(cells[s]["powered"] for s in lib.CELLS),
        "seeds": {"bootstrap": lib.SEED_BOOT, "permutation": lib.SEED_PERM},
        "params": {"median_w": lib.MEDIAN_W, "sigma_w": lib.SIGMA_W, "z_entry": lib.Z_ENTRY,
                   "z_exit": lib.Z_EXIT, "block": lib.BLOCK, "n_controls": lib.N_CONTROLS,
                   "n_bootstrap": lib.N_BOOTSTRAP, "n_perm": lib.N_PERM,
                   "min_events": lib.MIN_EVENTS},
    }
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    plot_delta_profiles(cells, PLOTS)
    plot_depth_gradient(cells, PLOTS)
    plot_ladder_anatomy(part_a, PLOTS)
    plot_episode_tail(part_a, PLOTS)
    plot_collapse(cells, part_a, PLOTS)
    logger.info("DONE: supported=%d/%d (%s) family_gate=%s -> results/",
                len(supported), len(lib.CELLS), ",".join(supported) or "-",
                summary["family_gate_supported"])


if __name__ == "__main__":
    main()
