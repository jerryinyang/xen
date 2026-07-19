"""XENA-EPSOSC-002 leak tripwire + drift-twin PAIR (design §7/§8, analyst-owned).

Extends 001's episode-label derangement with the drift-twin pair that isolates and
subtracts the unconditional single-name directional drift pedestal (001's AKRO defect).

Per subset read from search_certify_package.json (certified K≥3 + disclosure finalists):
  live   = equal-weight mean gross bps/episode on gate-band legs (recon, L-29 anchored).
  DERANGE (200 seeds, zero fixed points L-28): permute entry SLOTS, own duration+side.
  MATCHED-DRIFT twin (a, 200 seeds): RANDOM entry times decoupled from the arm, same
    symbols/side/count/duration. E[gross] ≠ 0 by design = the drift-carry benchmark.
  COIN-FLIP twin (b, 200 seeds): real schedule, side randomized per leg. E[gross] = 0 null.

HARD (design §8/§14) — REJECT unless BOTH hold, no override:
  raw collapse            = 1 − deranged_med / live                    ≥ 0.5
  drift-adjusted collapse = 1 − (deranged_med − drift_med)/(live − drift_med) ≥ 0.5
Also requires anchor_ok (L-29) and ≥3 distinct symbols (AMENDMENT-1).
Informative bite (§7 SUPPORTED): live ≥ P95 of BOTH twins; (live − drift_med) ci_low>0.
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path("/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen")
RUNS = ROOT / "data/nautilus_runs/XENA-EPSOSC-002"
EXP = ROOT / "python/experiments/XENA-EPSOSC-002"
PACKAGE = EXP / "results/search_certify_package.json"
OUT = EXP / "results/derangement_tripwire.json"

N_DERANGE = 200
N_TWIN = 200
BASE_SEED = 20260718


def make_derangement(n: int, rng: np.random.Generator) -> np.ndarray:
    if n < 2:
        return np.arange(n)
    while True:
        p = rng.permutation(n)
        if not np.any(p == np.arange(n)):
            return p


def load_cell(cell: str, lo: int, hi: int):
    d = RUNS / cell
    cis = pl.read_parquet(d / "xena" / "cis_trades.parquet")
    px = pl.read_parquet(d / "xena" / "positions.parquet").sort("SourceCloseTime")
    cis = cis.with_columns(
        pl.col("EntryTime").cast(pl.Int64).alias("entry_ns"),
        pl.col("ExitTime").cast(pl.Int64).alias("exit_ns"),
    )
    cis = cis.filter(
        pl.col("RealizedBps").is_finite()
        & (~pl.col("Censored").cast(pl.Boolean))
        & (pl.col("entry_ns") >= lo)
        & (pl.col("entry_ns") < hi)
    )
    cis = cis.with_columns((pl.col("exit_ns") - pl.col("entry_ns")).alias("dur_ns"))
    t = px.get_column("SourceCloseTime").cast(pl.Int64).to_numpy()
    o = px.get_column("RealOpen").to_numpy()
    # gate-band bar indices for random-entry twin (need next-open marks inside band)
    band_idx = np.where((t >= lo) & (t < hi))[0]
    return cis, t, o, band_idx


def mark_at(t_ns: np.ndarray, o: np.ndarray, when_ns: int) -> float:
    i = int(np.searchsorted(t_ns, when_ns, side="right"))
    if i >= len(t_ns):
        return float("nan")
    return float(o[i])


def leg_bps(direction: int, px_in: float, px_out: float) -> float:
    if not (np.isfinite(px_in) and np.isfinite(px_out)) or px_in <= 0:
        return float("nan")
    return float(direction) * (px_out - px_in) / px_in * 1e4


def recon_bps(entry_fill: float, exit_ns: int, direction: int, t, o) -> float:
    return leg_bps(direction, entry_fill, mark_at(t, o, exit_ns))


def validate_anchor(cis: pl.DataFrame, t, o) -> dict:
    ext = cis.get_column("exit_ns").to_numpy()
    dirn = cis.get_column("Direction").to_numpy()
    emit_in = cis.get_column("EntryFillPrice").to_numpy()
    emit_bps = cis.get_column("RealizedBps").to_numpy()
    n = len(ext)
    d_bps = np.array(
        [abs(recon_bps(emit_in[i], int(ext[i]), dirn[i], t, o) - emit_bps[i]) for i in range(n)],
        dtype=float,
    )
    return {
        "n": n,
        "median_bps_absdiff": float(np.nanmedian(d_bps)) if n else 0.0,
        "p90_bps_absdiff": float(np.nanpercentile(d_bps, 90)) if n else 0.0,
    }


def distinct_symbols(cells: list[str]) -> int:
    return len({c.split("__")[0] for c in cells})


def run_subset(name: str, cells: list[str], lo: int, hi: int) -> dict:
    per_cell, anchors, real_recon_all, real_emit_all = [], {}, [], []
    for c in cells:
        cis, t, o, band_idx = load_cell(c, lo, hi)
        anchors[c] = validate_anchor(cis, t, o)
        ent = cis.get_column("entry_ns").to_numpy()
        ext = cis.get_column("exit_ns").to_numpy()
        dur = cis.get_column("dur_ns").to_numpy()
        dirn = cis.get_column("Direction").to_numpy()
        fill = cis.get_column("EntryFillPrice").to_numpy()
        emit = cis.get_column("RealizedBps").to_numpy()
        per_cell.append(dict(ent=ent, ext=ext, dur=dur, dirn=dirn, fill=fill,
                             t=t, o=o, band_idx=band_idx, n=len(ent)))
        real_emit_all.append(emit)
        real_recon_all.append(np.array(
            [recon_bps(fill[i], int(ext[i]), dirn[i], t, o) for i in range(len(ent))]))
    real_emit_all = np.concatenate(real_emit_all)
    real_recon_all = np.concatenate(real_recon_all)
    live = float(np.nanmean(real_recon_all))

    anchor_ok = all(a["median_bps_absdiff"] < 15.0 and a["p90_bps_absdiff"] < 60.0
                    for a in anchors.values())

    rng_master = np.random.default_rng(BASE_SEED + abs(hash(name)) % 100000)

    def seed_means(kind: str, n_seeds: int) -> np.ndarray:
        out = []
        for _ in range(n_seeds):
            rng = np.random.default_rng(int(rng_master.integers(0, 2**31)))
            vals = []
            for cc in per_cell:
                n = cc["n"]
                if n == 0:
                    continue
                if kind == "derange":
                    perm = make_derangement(n, rng) if n >= 2 else np.array([0])
                    for i in range(n):
                        ef = cc["fill"][perm[i]]
                        nx = int(cc["ent"][perm[i]]) + int(cc["dur"][i])
                        vals.append(recon_bps(ef, nx, int(cc["dirn"][i]), cc["t"], cc["o"]))
                elif kind == "drift":  # matched-drift twin (a): random entry times
                    bi = cc["band_idx"]
                    if bi.size == 0:
                        continue
                    pick = rng.integers(0, bi.size, size=n)
                    for i in range(n):
                        j = int(bi[pick[i]])
                        ef = float(cc["o"][j])          # entry = that bar's open (L-29 self-mark)
                        entry_ns = int(cc["t"][j])
                        nx = entry_ns + int(cc["dur"][i])
                        vals.append(recon_bps(ef, nx, int(cc["dirn"][i]), cc["t"], cc["o"]))
                elif kind == "coinflip":  # coin-flip twin (b): real schedule, random side
                    flips = rng.choice([-1, 1], size=n)
                    for i in range(n):
                        vals.append(recon_bps(cc["fill"][i], int(cc["ext"][i]),
                                              int(flips[i]), cc["t"], cc["o"]))
            v = np.array(vals, dtype=float)
            v = v[np.isfinite(v)]
            out.append(float(np.mean(v)) if v.size else np.nan)
        a = np.array(out, dtype=float)
        return a[np.isfinite(a)]

    dm = seed_means("derange", N_DERANGE)
    drift = seed_means("drift", N_TWIN)
    coin = seed_means("coinflip", N_TWIN)

    deranged_med = float(np.median(dm)) if dm.size else float("nan")
    drift_med = float(np.median(drift)) if drift.size else float("nan")
    coin_med = float(np.median(coin)) if coin.size else float("nan")

    raw_collapse = 1.0 - deranged_med / live if live else float("nan")
    signal_live = live - drift_med
    signal_deranged = deranged_med - drift_med
    drift_adj_collapse = (1.0 - signal_deranged / signal_live
                          if np.isfinite(signal_live) and signal_live > 0 else float("nan"))

    drift_p95 = float(np.percentile(drift, 95)) if drift.size else float("nan")
    coin_p95 = float(np.percentile(coin, 95)) if coin.size else float("nan")
    bite_gt_both = bool(live > drift_p95 and live > coin_p95)

    nsym = distinct_symbols(cells)
    singleton = any(cc["n"] < 2 for cc in per_cell)
    hard_pass = bool(
        np.isfinite(raw_collapse) and raw_collapse >= 0.5
        and np.isfinite(drift_adj_collapse) and drift_adj_collapse >= 0.5
        and anchor_ok and not singleton and nsym >= 3
    )

    return {
        "cells": cells,
        "n_distinct_symbols": nsym,
        "n_real_legs": int(real_emit_all.size),
        "live_mean_gross_bps": live,
        "live_mean_gross_bps_emitted": float(np.nanmean(real_emit_all)),
        "deranged_mean_median": deranged_med,
        "matched_drift_twin_median": drift_med,
        "coin_flip_twin_median": coin_med,
        "matched_drift_twin_p95": drift_p95,
        "coin_flip_twin_p95": coin_p95,
        "signal_component_live_minus_drift": signal_live,
        "raw_collapse_fraction": raw_collapse,
        "drift_adjusted_collapse_fraction": drift_adj_collapse,
        "bite_live_gt_p95_both_twins": bite_gt_both,
        "anchor_ok_L29": anchor_ok,
        "single_symbol_or_singleton": bool(singleton or nsym < 3),
        "n_seeds": {"derange": int(dm.size), "drift": int(drift.size), "coin": int(coin.size)},
        "HARD_pass_raw_and_drift_adjusted_ge_0.5": hard_pass,
    }


def subsets_from_package() -> tuple[dict, tuple[int, int]]:
    pkg = json.loads(PACKAGE.read_text())
    lo, hi = (int(pkg["segments"]["gate"][0]), int(pkg["segments"]["gate"][1]))
    subsets = {}
    s2 = pkg.get("stage2_gate_band") or {}
    if not s2.get("empty") and s2.get("top"):
        subsets["certified_top1_K3"] = list(s2["top"])
    # disclosure finalists (higher-ranked, <3 symbols) + a few top ranked for context
    am = pkg.get("amendment_1_distinct_symbol_filter") or {}
    for d in (am.get("disclosure_skipped") or [])[:3]:
        subsets[f"disclosure_rank{d['rank']}_{d['distinct_symbols']}sym"] = list(d["subset"])
    for i, r in enumerate((pkg.get("certify") or {}).get("ranked", [])[:3]):
        subsets.setdefault(f"ranked{i}_{distinct_symbols(list(r['subset']))}sym", list(r["subset"]))
    return subsets, (lo, hi)


def main():
    subsets, (lo, hi) = subsets_from_package()
    if not subsets:
        raise SystemExit("no subsets in package to test")
    results = {name: run_subset(name, cells, lo, hi) for name, cells in subsets.items()}
    out = {
        "universe_id": "XENA-EPSOSC-002",
        "tripwire": "episode-label derangement + drift-twin pair (design §7/§8)",
        "metric": "equal-weight mean gross bps/episode on gate-band legs (recon, L-29)",
        "gate_band_ns": [lo, hi],
        "hard_rule": ("raw_collapse >= 0.5 AND drift_adjusted_collapse >= 0.5 AND anchor_ok "
                      "AND >=3 distinct symbols; else REJECT (no override)"),
        "n_derange_seeds": N_DERANGE, "n_twin_seeds": N_TWIN,
        "subsets": results,
    }
    OUT.write_text(json.dumps(out, indent=2))
    print(json.dumps({k: {
        "nsym": v["n_distinct_symbols"], "n_legs": v["n_real_legs"],
        "live": round(v["live_mean_gross_bps"], 1),
        "drift_twin": round(v["matched_drift_twin_median"], 1),
        "coin_twin": round(v["coin_flip_twin_median"], 1),
        "raw_collapse": round(v["raw_collapse_fraction"], 3),
        "drift_adj_collapse": (round(v["drift_adjusted_collapse_fraction"], 3)
                               if np.isfinite(v["drift_adjusted_collapse_fraction"]) else None),
        "bite": v["bite_live_gt_p95_both_twins"],
        "HARD_pass": v["HARD_pass_raw_and_drift_adjusted_ge_0.5"],
    } for k, v in results.items()}, indent=2))
    print("written", OUT)


if __name__ == "__main__":
    main()
