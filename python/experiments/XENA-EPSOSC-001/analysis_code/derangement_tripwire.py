"""XENA-EPSOSC-001 leak tripwire (design §8): episode-label DERANGEMENT alignment-destroy.

Analyst-owned. Uses ONLY raw emissions (xena/cis_trades.parquet + price series) — no
experiment-local code, no summaries. For each certified finalist subset:

  - take its gate-band legs (the certified read),
  - preserve each leg's DURATION + SIDE,
  - derange the ENTRY TIMES across the schedule (zero fixed points, L-28),
  - re-price entry/exit from the REAL price series at the deranged times,
  - recompute mean gross bps/episode.

HARD (design §8/§14): a finalist whose edge does NOT collapse (deranged mean >= 0.5x real
mean) under derangement is a leak/artifact => REJECT, no operator override.
collapse_fraction = 1 - deranged_mean / real_mean ; require median collapse >= 0.5.

Self-validation anchor (L-29): before any collapse number, the price lookup must reproduce
the emitted EntryFillPrice on the ORIGINAL (non-deranged) legs within 1 tick. If not, STOP.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import polars as pl

ROOT = Path("/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen")
RUNS = ROOT / "data/nautilus_runs/XENA-EPSOSC-001"
OUT = ROOT / "python/experiments/XENA-EPSOSC-001/results/derangement_tripwire.json"

# gate/stage-2 band (search_certify_package.json segments.gate), ns
GATE_LO, GATE_HI = 1687275996000000000, 1702857600000000000
N_SEEDS = 200
BASE_SEED = 20260718

FINALISTS = {
    "rank1_AKRO_W192_k3_HYBRID_S": [
        "AKROUSDT__VOLARM__15m__W192__k3__HYBRID__S",
    ],
    "rank3_AKRO_dual_RET_S": [
        "AKROUSDT__VOLARM__15m__W192__k2.5__RET_ANCHOR__S",
        "AKROUSDT__VOLARM__15m__W192__k3__RET_ANCHOR__S",
    ],
    "rank5_AKRO_RET_S__RSR_HYB_L": [
        "AKROUSDT__VOLARM__15m__W192__k3__RET_ANCHOR__S",
        "RSRUSDT__VOLARM__15m__W96__k3__HYBRID__L",
    ],
}


def make_derangement(n: int, rng: np.random.Generator) -> np.ndarray:
    """Permutation with zero fixed points (L-28). n>=2."""
    if n < 2:
        return np.arange(n)
    while True:
        p = rng.permutation(n)
        if not np.any(p == np.arange(n)):
            return p


def load_cell(cell: str):
    """Return (legs_df, price_times_ns, price_open) for a cell's gate-band legs.

    legs: EntryTime, ExitTime, Direction, EntryFillPrice (exact emitted), RealizedBps (gross),
    dur_ns (own holding time). Filtered to finite, non-censored, entry in gate band.
    """
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
        & (pl.col("entry_ns") >= GATE_LO)
        & (pl.col("entry_ns") < GATE_HI)
    )
    cis = cis.with_columns((pl.col("exit_ns") - pl.col("entry_ns")).alias("dur_ns"))
    t = px.get_column("SourceCloseTime").cast(pl.Int64).to_numpy()
    o = px.get_column("RealOpen").to_numpy()
    return cis, t, o


def mark_at(t_ns: np.ndarray, o: np.ndarray, when_ns: int) -> float:
    """Marks price = RealOpen of the first bar with close-time > when (next-bar open, L-29).
    Out of range -> nan."""
    i = int(np.searchsorted(t_ns, when_ns, side="right"))
    if i >= len(t_ns):
        return float("nan")
    return float(o[i])


def leg_bps(direction: int, px_in: float, px_out: float) -> float:
    if not (np.isfinite(px_in) and np.isfinite(px_out)) or px_in <= 0:
        return float("nan")
    return float(direction) * (px_out - px_in) / px_in * 1e4


def recon_bps(entry_fill: float, exit_ns: int, direction: int, t, o) -> float:
    """Re-adjudicated gross bps: EXACT emitted entry fill + marks exit at exit_ns."""
    return leg_bps(direction, entry_fill, mark_at(t, o, exit_ns))


def validate_anchor(cis: pl.DataFrame, t, o) -> dict:
    """L-29: recon (exact entry fill + marks exit at OWN exit_ns) must reproduce emitted
    RealizedBps. Exit is marks-approximated, so tolerance is median/p90 bps error."""
    ext = cis.get_column("exit_ns").to_numpy()
    dirn = cis.get_column("Direction").to_numpy()
    emit_in = cis.get_column("EntryFillPrice").to_numpy()
    emit_bps = cis.get_column("RealizedBps").to_numpy()
    n = len(ext)
    d_bps = [abs(recon_bps(emit_in[i], int(ext[i]), dirn[i], t, o) - emit_bps[i])
             for i in range(n)]
    d_bps = np.array(d_bps, dtype=float)
    return {
        "n": n,
        "median_bps_absdiff": float(np.nanmedian(d_bps)) if n else 0.0,
        "p90_bps_absdiff": float(np.nanpercentile(d_bps, 90)) if n else 0.0,
    }


def run_subset(name: str, cells: list[str]) -> dict:
    per_cell = []
    anchors = {}
    real_recon_all = []
    real_emit_all = []
    for c in cells:
        cis, t, o = load_cell(c)
        anchors[c] = validate_anchor(cis, t, o)
        ent = cis.get_column("entry_ns").to_numpy()
        ext = cis.get_column("exit_ns").to_numpy()
        dur = cis.get_column("dur_ns").to_numpy()
        dirn = cis.get_column("Direction").to_numpy()
        fill = cis.get_column("EntryFillPrice").to_numpy()
        emit = cis.get_column("RealizedBps").to_numpy()
        per_cell.append(dict(ent=ent, ext=ext, dur=dur, dirn=dirn, fill=fill, t=t, o=o, n=len(ent)))
        real_emit_all.append(emit)
        # apples-to-apples real: same recon method, own (identity) slot
        real_recon_all.append(np.array(
            [recon_bps(fill[i], int(ext[i]), dirn[i], t, o) for i in range(len(ent))]))
    real_emit_all = np.concatenate(real_emit_all)
    real_recon_all = np.concatenate(real_recon_all)
    real_recon_mean = float(np.nanmean(real_recon_all))

    # anchor gate (L-29): recon must reproduce emitted bps (marks-exit tolerance)
    anchor_ok = all(
        (a["median_bps_absdiff"] < 15.0 and a["p90_bps_absdiff"] < 60.0)
        for a in anchors.values()
    )

    deranged_means = []
    rng_master = np.random.default_rng(BASE_SEED + abs(hash(name)) % 100000)
    for _ in range(N_SEEDS):
        rng = np.random.default_rng(int(rng_master.integers(0, 2**31)))
        seed_bps = []
        for cc in per_cell:
            n = cc["n"]
            perm = make_derangement(n, rng) if n >= 2 else np.array([0])
            for i in range(n):
                # deranged entry SLOT (exact emitted fill of slot perm[i]); OWN duration + side
                entry_fill = cc["fill"][perm[i]]
                new_exit = int(cc["ent"][perm[i]]) + int(cc["dur"][i])
                seed_bps.append(recon_bps(entry_fill, new_exit, int(cc["dirn"][i]), cc["t"], cc["o"]))
        seed_bps = np.array(seed_bps, dtype=float)
        seed_bps = seed_bps[np.isfinite(seed_bps)]
        deranged_means.append(float(np.mean(seed_bps)) if seed_bps.size else np.nan)

    dm = np.array(deranged_means, dtype=float)
    dm = dm[np.isfinite(dm)]
    med_deranged = float(np.median(dm)) if dm.size else float("nan")
    collapse = 1.0 - (med_deranged / real_recon_mean) if real_recon_mean else float("nan")
    survival_rate = float(np.mean(dm >= 0.5 * real_recon_mean)) if dm.size and real_recon_mean > 0 else float("nan")
    singleton_cell = any(cc["n"] < 2 for cc in per_cell)
    hard_pass = bool(np.isfinite(collapse) and collapse >= 0.5 and anchor_ok and not singleton_cell)

    return {
        "cells": cells,
        "n_real_legs": int(real_emit_all.size),
        "real_mean_gross_bps_emitted": float(np.nanmean(real_emit_all)),
        "real_mean_gross_bps_recon": real_recon_mean,
        "deranged_mean_gross_bps_median": med_deranged,
        "deranged_mean_p05": float(np.percentile(dm, 5)) if dm.size else None,
        "deranged_mean_p95": float(np.percentile(dm, 95)) if dm.size else None,
        "collapse_fraction_median": collapse,
        "survival_rate_ge_half": survival_rate,
        "n_seeds": N_SEEDS,
        "anchor_ok_L29": anchor_ok,
        "anchor_detail": anchors,
        "single_cell_of_1_symbol": singleton_cell,
        "hard_pass_collapse_ge_0.5": hard_pass,
    }


def main():
    results = {}
    for name, cells in FINALISTS.items():
        results[name] = run_subset(name, cells)
    out = {
        "universe_id": "XENA-EPSOSC-001",
        "tripwire": "episode-label derangement (design §8), alignment-destroy",
        "metric": "equal-weight mean gross bps/episode on gate-band legs",
        "gate_band_ns": [GATE_LO, GATE_HI],
        "hard_rule": "collapse_fraction_median >= 0.5 AND anchor_ok; else REJECT (no override)",
        "n_seeds": N_SEEDS,
        "finalists": results,
    }
    OUT.write_text(json.dumps(out, indent=2))
    print(json.dumps({k: {"real_recon": round(v["real_mean_gross_bps_recon"], 1),
                          "deranged_med": round(v["deranged_mean_gross_bps_median"], 1),
                          "collapse": round(v["collapse_fraction_median"], 3),
                          "survival": round(v["survival_rate_ge_half"], 3),
                          "anchor_ok": v["anchor_ok_L29"],
                          "n_legs": v["n_real_legs"],
                          "single_cell_1sym": v["single_cell_of_1_symbol"],
                          "hard_pass": v["hard_pass_collapse_ge_0.5"]}
                       for k, v in results.items()}, indent=2))
    print("written", OUT)


if __name__ == "__main__":
    main()
