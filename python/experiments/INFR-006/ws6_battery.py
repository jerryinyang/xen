"""INFR-006 WS-6 full-scale calibration battery (design §7 registered scale).

Phases:
  1. Pilot timing (2 universes, serial) — projection logged.
  2. Null battery: 300 zero-gross-edge universes (costed, 2 bps RT).
  3. Planted battery: 5 gross edges (10/20/30/40/60 bps) × 50 universes.
  4. §11 insensitivity sweep (L / block / move-probs) on one planted universe.
  5. Post-pass: derive X / F_floor / gate threshold by the REGISTERED RULES
     (design §7) from the recorded raw stats; write summary.

Battery protocol: the pipeline runs with a PERMISSIVE provisional screen
(X=0, F_floor=-inf) and a provisional gate threshold of 0.0, recording the raw
statistics (per-finalist F̂ + min_drop_ratio; top-portfolio gate bootstrap P25).
Threshold selection is a pure post-pass over recorded stats — the registered rules
applied to synthetic-truth outcomes, never to live ones (L-23-legitimate).

Checkpoints: results/ws6_battery_raw.jsonl (one line per universe, append-only).
Summary:     results/ws6_battery_summary.json
"""
from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

from xen.xena.calibration import (SegmentLayout, insensitivity_sweep, path_universe)
from xen.xena.certify import certify_and_rank, contiguous_purged_folds
from xen.xena.final_gate import run_final_gate
from xen.xena.oracle import OracleConfig
from xen.xena.search import SearchParams, run_restart

# ---------------------------------------------------------------------------- #
# Registered scale (design §7) — change only with a tagged amendment (L-23)
# ---------------------------------------------------------------------------- #
NS = 1_000_000_000
N_NULL_UNIVERSES = 300
PLANTED_EDGES_BPS = (10.0, 20.0, 30.0, 40.0, 60.0)   # GROSS; cost 2 bps charged in-sim
N_PER_EDGE = 50
N_CANDIDATES = 24            # per universe (planted: 5 planted + 19 null)
N_PLANTED = 5
N_RESTARTS = 10
BUDGET = 400
N_TRADES = 60
NOISE_BPS = 30.0
N_BARS = 4000
BAR_SECONDS = 60
HOLD_BARS = 20
N_FOLDS = 3
PURGE_NS = HOLD_BARS * BAR_SECONDS * NS              # purge ≥ holding horizon
PARAMS = SearchParams()                              # registry defaults, L=150 etc.
# Gross-selection amendment (operator, 2026-07-10): SELECTION stages run cost-free;
# the final gate forces charge_costs=True internally (L-22 binding verdict leg).
CFG = OracleConfig(charge_costs=False)               # r=0.5%, R_max=5%, gross selection
LAYOUT = SegmentLayout.from_span(0, N_BARS * BAR_SECONDS * NS)   # 50/30/20
PROVISIONAL_GATE_THRESHOLD = 0.0

EXP_DIR = Path(__file__).parent
RESULTS = EXP_DIR / "results"
RAW_PATH = RESULTS / "ws6_battery_raw.jsonl"
SUMMARY_PATH = RESULTS / "ws6_battery_summary.json"
GATE_WORK = RESULTS / "gate_ledgers"


# ---------------------------------------------------------------------------- #
# One universe through the full pipeline (permissive screen, raw stats recorded)
# ---------------------------------------------------------------------------- #
def run_one(task: tuple[str, float, int]) -> dict:
    kind, edge, seed = task
    t0 = time.time()
    # v2 generators (2026-07-10): shared regime-GBM path per universe, coin-flip nulls
    # (E[gross]=0 exact on any path), vol-clustered entries, vol-scaled stops.
    n_planted = 0 if kind == "null" else N_PLANTED
    streams = path_universe(n_planted=n_planted, n_null=N_CANDIDATES - n_planted,
                            edge_bps=edge, seed=seed, n_trades=N_TRADES,
                            n_bars=N_BARS, bar_seconds=BAR_SECONDS)
    finalists = [run_restart(streams, CFG, budget=BUDGET, restart_id=r + 1,
                             params=PARAMS, segment=LAYOUT.search)
                 for r in range(N_RESTARTS)]
    folds = contiguous_purged_folds(LAYOUT.ranking[0], LAYOUT.ranking[1],
                                    n_folds=N_FOLDS, purge_ns=PURGE_NS)
    out = certify_and_rank(finalists, streams, CFG, plateau_threshold=0.0,
                           f_floor=-1e18, folds=folds, params=PARAMS,
                           search_segment=LAYOUT.search)

    plateau_stats = [{"F_hat": p.F_hat,
                      "min_drop_ratio": (None if np.isnan(p.min_drop_ratio)
                                         else p.min_drop_ratio),
                      "size": len(p.subset),
                      "planted_frac": (sum(1 for c in p.subset
                                           if c.startswith("plant")) / len(p.subset)
                                       if p.subset else 0.0)}
                     for p in out["plateau"]]

    gate = None
    if out["ranked"]:
        top = out["ranked"][0]
        wd = GATE_WORK / f"{kind}_{int(edge)}_{seed}"
        wd.mkdir(parents=True, exist_ok=True)
        art = run_final_gate(top.subset, streams, CFG, gate_segment=LAYOUT.gate,
                             pass_threshold=PROVISIONAL_GATE_THRESHOLD,
                             search_F_claim=top.search_F_hat, universe_root=wd,
                             universe_id=f"CALIB-{kind}-{seed}",
                             evaluation_count=out["evaluation_count"], params=PARAMS)
        # A-4 dual gate: binding = GROSS block; net block recorded for FPR-under-net view
        gate = {"p25": art["gross"]["F_boot"]["p25"],
                "median": art["gross"]["F_boot"]["median"],
                "F_point": art["gross"]["F_point"],
                "dd_feasible": art["gross"]["dd_feasibility"]["feasible"],
                "net_p25": art["net_informational"]["F_boot"]["p25"],
                "top_planted_frac": (sum(1 for c in top.subset
                                         if c.startswith("plant")) / len(top.subset)
                                     if top.subset else 0.0),
                "top_median_fold_F": top.median_F}

    return {"kind": kind, "edge_bps": edge, "seed": seed,
            "top_subset": (sorted(out["ranked"][0].subset) if out["ranked"] else []),
            "plateau": plateau_stats, "gate": gate,
            "evaluation_count": out["evaluation_count"],
            "distinct_subsets": out["distinct_subsets"],
            "dispersion_F": out["dispersion"]["F_hat"],
            "wall_s": round(time.time() - t0, 1)}


# ---------------------------------------------------------------------------- #
# Post-pass: registered threshold rules over recorded raw stats (design §7)
# ---------------------------------------------------------------------------- #
def certified_under(rec: dict, X: float, f_floor: float) -> bool:
    return any(p["F_hat"] >= f_floor and p["F_hat"] > 0
               and p["min_drop_ratio"] is not None and p["min_drop_ratio"] >= X
               for p in rec["plateau"])


def derive_thresholds(raw: list[dict]) -> dict:
    nulls = [r for r in raw if r["kind"] == "null"]
    target = [r for r in raw if r["kind"] == "planted" and r["edge_bps"] == 30.0]

    # X: largest value on a 0.05 grid retaining >= 90% of target-edge certifications
    # (relative to X=0), then F_floor by the same rule at the chosen X.
    def cert_rate(univs, X, floor):
        return (sum(1 for r in univs if certified_under(r, X, floor)) / len(univs)
                if univs else float("nan"))

    base_rate = cert_rate(target, 0.0, -1e18)
    X_grid = np.round(np.arange(0.0, 1.0001, 0.05), 2)
    X_star = 0.0
    for X in X_grid:
        if base_rate > 0 and cert_rate(target, float(X), -1e18) >= 0.9 * base_rate:
            X_star = float(X)
    floor_candidates = sorted({p["F_hat"] for r in target for p in r["plateau"]
                               if p["F_hat"] > 0})
    F_floor_star = 0.0
    for fl in floor_candidates:
        if cert_rate(target, X_star, fl) >= 0.9 * base_rate:
            F_floor_star = float(fl)

    # gate threshold: max(0, P95 of GROSS null gate P25s) — registered rule, A-4 regime
    null_gate_p25 = [r["gate"]["p25"] for r in nulls if r["gate"]]
    gate_thr = max(0.0, float(np.quantile(null_gate_p25, 0.95))) if null_gate_p25 else 0.0

    def gate_passes(r) -> bool:   # A-4 binding legs: gross P25 + gross-path DD
        g = r["gate"]
        return (g is not None and g["p25"] >= gate_thr and g.get("dd_feasible", True)
                and certified_under(r, X_star, F_floor_star))

    # outcomes under the final thresholds
    null_cert = cert_rate(nulls, X_star, F_floor_star)
    null_gate_pass = (sum(1 for r in nulls if gate_passes(r)) / len(nulls)
                      if nulls else float("nan"))
    mde_curve = {}
    for e in PLANTED_EDGES_BPS:
        univs = [r for r in raw if r["kind"] == "planted" and r["edge_bps"] == e]
        cr = cert_rate(univs, X_star, F_floor_star)
        purity = [r["gate"]["top_planted_frac"] for r in univs if r["gate"]]
        gate_pass = (sum(1 for r in univs if gate_passes(r)) / len(univs)
                     if univs else float("nan"))
        passers = [r for r in univs if gate_passes(r)]
        net_ok = (sum(1 for r in passers if r["gate"].get("net_p25", 0) >= 0)
                  / len(passers) if passers else float("nan"))
        mde_curve[str(e)] = {"n": len(univs), "gross_edge_bps": e,
                             "net_edge_bps_for_deployability": e - 2.0,
                             "certification_rate": cr,
                             "end_to_end_pass_rate": gate_pass,
                             "net_p25_nonneg_among_passers": net_ok,   # informational
                             "top_planted_frac_mean": (float(np.mean(purity))
                                                       if purity else float("nan"))}

    n_null = len(nulls)
    n_false = sum(1 for r in nulls if gate_passes(r))
    return {"X": X_star, "F_floor": F_floor_star, "gate_pass_threshold": gate_thr,
            "gate_rule": "max(0, P95 of GROSS null gate bootstrap P25s) — A-4 regime",
            "null": {"n": n_null, "certification_rate": null_cert,
                     "end_to_end_false_pass_rate": null_gate_pass,
                     "n_end_to_end_false": n_false,
                     "rule_of_three_fpr_bound_95":
                         (3 / n_null if n_false == 0 and n_null else float("nan"))},
            "target_edge_base_cert_rate_X0": base_rate,
            "mde_curve": mde_curve}


# ---------------------------------------------------------------------------- #
def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    GATE_WORK.mkdir(parents=True, exist_ok=True)
    done: set[tuple[str, float, int]] = set()
    if RAW_PATH.exists():   # resume support
        for line in RAW_PATH.read_text().splitlines():
            r = json.loads(line)
            done.add((r["kind"], r["edge_bps"], r["seed"]))
        print(f"resuming: {len(done)} universes already recorded", flush=True)

    tasks = [("null", 0.0, s) for s in range(1, N_NULL_UNIVERSES + 1)]
    for e in PLANTED_EDGES_BPS:
        tasks += [("planted", e, 10_000 + int(e) * 100 + s)
                  for s in range(1, N_PER_EDGE + 1)]
    tasks = [t for t in tasks if t not in done]
    print(f"{len(tasks)} universes to run "
          f"(registered total {N_NULL_UNIVERSES + len(PLANTED_EDGES_BPS) * N_PER_EDGE})",
          flush=True)

    # phase 1: pilot timing
    if tasks:
        t0 = time.time()
        for t in tasks[:2]:
            rec = run_one(t)
            with RAW_PATH.open("a") as f:
                f.write(json.dumps(rec) + "\n")
        per_u = (time.time() - t0) / min(2, len(tasks))
        workers = max(2, (os.cpu_count() or 4) - 2)
        rem = len(tasks) - min(2, len(tasks))
        print(f"pilot: {per_u:.1f}s/universe serial; {workers} workers → "
              f"projected {rem * per_u / workers / 3600:.1f}h remaining", flush=True)
        tasks = tasks[2:]

    # phase 2+3: batteries, parallel, checkpointed
    workers = max(2, (os.cpu_count() or 4) - 2)
    n_done = 0
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(run_one, t): t for t in tasks}
        for fut in as_completed(futs):
            rec = fut.result()
            with RAW_PATH.open("a") as f:
                f.write(json.dumps(rec) + "\n")
            n_done += 1
            if n_done % 10 == 0:
                print(f"{n_done}/{len(tasks)} universes done", flush=True)

    # phase 4: insensitivity sweep (registered §11 axes) on one planted universe
    print("insensitivity sweep ...", flush=True)
    sweep_streams = path_universe(n_planted=N_PLANTED,
                                  n_null=N_CANDIDATES - N_PLANTED,
                                  edge_bps=30.0, seed=99_999, n_trades=N_TRADES,
                                  n_bars=N_BARS, bar_seconds=BAR_SECONDS)
    sweep = insensitivity_sweep(sweep_streams, CFG, budget=BUDGET, layout=LAYOUT,
                                base=PARAMS, n_seeds=3)

    # phase 5: post-pass under the registered rules
    raw = [json.loads(line) for line in RAW_PATH.read_text().splitlines()]
    summary = {"registered_scale": {
                   "n_null": N_NULL_UNIVERSES, "planted_edges_bps": PLANTED_EDGES_BPS,
                   "n_per_edge": N_PER_EDGE, "n_candidates": N_CANDIDATES,
                   "n_planted": N_PLANTED, "n_restarts": N_RESTARTS, "budget": BUDGET,
                   "layout": {"search": LAYOUT.search, "ranking": LAYOUT.ranking,
                              "gate": LAYOUT.gate},
                   "cost_bps": 2.0, "noise_bps": NOISE_BPS},
               "thresholds": derive_thresholds(raw),
               "insensitivity": sweep,
               "wall_stats": {"mean_s": float(np.mean([r["wall_s"] for r in raw])),
                              "total_universes": len(raw)}}
    SUMMARY_PATH.write_text(json.dumps(summary, indent=1))
    print(f"summary written: {SUMMARY_PATH}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
