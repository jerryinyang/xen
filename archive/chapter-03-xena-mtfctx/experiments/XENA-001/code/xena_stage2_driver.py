"""XENA stage-2 driver (c8g.12xlarge, single adjudication platform — 2026-07-12 addendum).

Per universe, unattended, in order:
  smoke   — 3 smoke restarts (rids 100-102), geometric budget ladder (×1.25, shared
            per-rid EvalCache so each rung replays the prefix bitwise and only the tail
            is new). §6 pre-registered budget read: first rung B_k where best-F
            improvement over the trailing 20% of iterations (i.e. vs the 0.8·B_k rung)
            is < 1%. Universe budget = max over the 3 smoke rids (conservative),
            recorded in results/search_budget.json.
  prod    — 12 production restarts (ids 0-11) at the pinned budget, ThreadPoolExecutor
            (kernel GIL-free, INFR-008; thread-parallel ≡ sequential bitwise).
            One search_restart_XX.json per restart (schema of run_search.py full-one).
  certify — certify_and_rank against frozen registry v3 (pinned folds, purge 14d AFTER
            each interior boundary only — XENA-001 run_certify.py convention).
  battery — permutation-null battery (design §7 TRIPWIRE): causal alignment-breaking
            entry-time block rotation per candidate within symbol×domain (whole-stream
            rotation, minute-aligned, wraparound within the search band; per-leg prices,
            durations, P&L untouched — NEVER P&L permutation, L-14). K_PERM permutations
            × 3 restarts each at the pinned budget; live-vs-permuted best-F read.
  evidence— evidence_package.json assembling all stages + platform provenance.

Usage: python xena_stage2_driver.py <XENA-001|XENA-002|XENA-003> [stage]
       stage in {all, smoke, prod, certify, battery, evidence}; default all.
"""

from __future__ import annotations

import json
import math
import platform
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl

HOME = Path.home()
ROOT = HOME / "xen"
sys.path.insert(0, str(ROOT / "python" / "src"))

from xen.xena.certify import certify_and_rank  # noqa: E402
from xen.xena.oracle import (CandidateStream, OracleConfig,  # noqa: E402
                             clear_prepared_cache)
from xen.xena.search import EvalCache, RestartResult, run_restart  # noqa: E402

EXP = sys.argv[1]
STAGE = sys.argv[2] if len(sys.argv) > 2 else "all"
CODE = ROOT / "python" / "experiments" / EXP / "code"
RESULTS = ROOT / "python" / "experiments" / EXP / "results"
REGISTRY = ROOT / "python" / "experiments" / "INFR-006" / "results" / "xena_frozen_registry.json"
sys.path.insert(0, str(CODE))
from run_search import SEARCH_BAND, load_streams  # noqa: E402

NS_MIN = 60_000_000_000
SMOKE_RIDS = (100, 101, 102)
SMOKE_CAP = 34_000
K_PERM = 10                 # operational battery size (informative read, no threshold)
PERM_RIDS = (0, 1)          # restarts per permutation (compute-budget bound, 2026-07-12)
PERM_CHUNK = 2              # perms in flight at once (prep-cache memory bound)

CONFIG = OracleConfig(charge_costs=False)   # A-1: gross selection


def _ns(y: int, m: int, d: int) -> int:
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp() * 1e9)


# Pinned folds (binding band table; purge 14 calendar days AFTER each interior
# boundary only — identical to XENA-001 run_certify.py).
FOLDS = [
    (_ns(2023, 3, 8), _ns(2023, 6, 12)),
    (_ns(2023, 6, 26), _ns(2023, 9, 16)),
    (_ns(2023, 9, 30), _ns(2023, 12, 22)),
    (_ns(2024, 1, 5), _ns(2024, 3, 28)),
]


def platform_meta() -> dict:
    itype = "unknown"
    try:
        itype = subprocess.run(
            ["curl", "-s", "-m", "2", "http://169.254.169.254/latest/meta-data/instance-type"],
            capture_output=True, text=True).stdout.strip() or "unknown"
    except Exception:
        pass
    return {"instance_type": itype, "machine": platform.machine(),
            "python": platform.python_version(),
            "platform": platform.platform(),
            "utc": datetime.now(timezone.utc).isoformat()}


def ladder() -> list[int]:
    out, b = [], 250
    while b < SMOKE_CAP:
        out.append(b)
        b = math.ceil(b * 1.25)
    out.append(SMOKE_CAP)
    return out


def stage_smoke(streams: list[CandidateStream]) -> None:
    rungs = ladder()

    def one(rid: int) -> list[dict]:
        cache = EvalCache()
        rows = []
        for budget in rungs:
            t = time.time()
            r = run_restart(streams, CONFIG, budget=budget, restart_id=rid,
                            segment=SEARCH_BAND, cache=cache)
            rows.append({"restart_id": rid, "budget": budget,
                         "best_F_hat": r.best_F_hat, "n_iter": r.n_iterations,
                         "n_kicks": r.n_kicks, "acc": r.acceptance_rate,
                         "subset_size": len(r.best_subset),
                         "seconds": round(time.time() - t, 1)})
            print(f"[{EXP} smoke] {rows[-1]}", flush=True)
        (RESULTS / f"search_smoke_budget_r{rid}.json").write_text(json.dumps(rows, indent=1))
        return rows

    with ThreadPoolExecutor(len(SMOKE_RIDS)) as ex:
        list(ex.map(one, SMOKE_RIDS))
    stage_budget()


def stage_budget() -> None:
    """Operator-approved curve read (2026-07-12): per rid, budget = smallest ladder rung
    whose best-F is within 1% of that rid's cap-budget best-F (i.e. the walk has captured
    >=99% of its 34k-cap value); universe budget = max over the 3 smoke rids. Supersedes
    the literal trailing-20% read, which fired on transient stalls (run-1 defect)."""
    per_rid = {}
    for rid in SMOKE_RIDS:
        rows = json.loads((RESULTS / f"search_smoke_budget_r{rid}.json").read_text())
        f_cap = rows[-1]["best_F_hat"]
        pick = next(r["budget"] for r in rows
                    if r["best_F_hat"] >= 0.99 * f_cap)
        per_rid[str(rid)] = pick
    budget = max(per_rid.values())
    (RESULTS / "search_budget.json").write_text(json.dumps({
        "experiment": EXP,
        "procedure": ("2026-07-12 operator-approved curve read: 3 smoke restarts, full "
                      "x1.25 ladder to cap; per rid budget = smallest rung with best-F "
                      ">= 99% of the cap-rung best-F; universe budget = max over rids. "
                      "Supersedes the literal trailing-20% read (fired on transient "
                      "stalls, run-1)."),
        "flatten_budget_per_rid": per_rid, "budget": budget,
        "smoke_cap": SMOKE_CAP}, indent=1))
    print(f"[{EXP}] pinned budget = {budget} (per-rid {per_rid})", flush=True)


def warm_prep_cache(streams: list[CandidateStream]) -> None:
    """Build the per-(stream, segment) prepared arrays sequentially BEFORE any thread
    pool: 12 threads lazily preparing 2736 candidates at once transiently duplicates
    the big arrays (OOM-killed XENA-002 run-2 at launch, 52GB RSS in 13s)."""
    from xen.xena.oracle import _prepare_candidate
    t = time.time()
    for s in streams:
        _prepare_candidate(s, SEARCH_BAND)
    print(f"[{EXP}] prep cache warmed in {time.time()-t:.1f}s", flush=True)


def stage_prod(streams: list[CandidateStream]) -> None:
    budget = json.loads((RESULTS / "search_budget.json").read_text())["budget"]
    warm_prep_cache(streams)
    meta = platform_meta()

    def one(rid: int) -> None:
        t = time.time()
        r = run_restart(streams, CONFIG, budget=budget, restart_id=rid,
                        segment=SEARCH_BAND)
        out = {"restart_id": rid, "budget": budget, "best_F_hat": r.best_F_hat,
               "best_subset": sorted(r.best_subset),
               "n_iterations": r.n_iterations, "n_kicks": r.n_kicks,
               "acceptance_rate": r.acceptance_rate,
               "gate_rejection_rate": r.gate_rejection_rate,
               "n_evaluations": r.cache.evaluation_count,
               "distinct_subsets": len(r.cache.subsets()),
               "band_ns": list(SEARCH_BAND), "charge_costs": False,
               "seconds": round(time.time() - t, 1), "platform": meta}
        (RESULTS / f"search_restart_{rid:02d}.json").write_text(json.dumps(out, indent=1))
        print(f"[{EXP} prod] rid={rid} F={r.best_F_hat:.4f} "
              f"{out['seconds']}s", flush=True)

    with ThreadPoolExecutor(12) as ex:
        list(ex.map(one, range(12)))


def stage_certify(streams: list[CandidateStream]) -> None:
    registry = json.loads(REGISTRY.read_text())
    finalists, search_evals = [], 0
    for p in sorted(RESULTS.glob("search_restart_*.json")):
        d = json.loads(p.read_text())
        assert tuple(d["band_ns"]) == SEARCH_BAND and d["charge_costs"] is False
        search_evals += d["n_evaluations"]
        finalists.append(RestartResult(
            best_subset=frozenset(d["best_subset"]), best_F_hat=d["best_F_hat"],
            restart_id=d["restart_id"], n_iterations=d["n_iterations"],
            n_kicks=d["n_kicks"], acceptance_rate=d["acceptance_rate"],
            gate_rejection_rate=d["gate_rejection_rate"], cache=EvalCache()))
    assert len(finalists) == 12, f"expected 12 restart files, got {len(finalists)}"
    t0 = time.time()
    out = certify_and_rank(
        finalists, streams, CONFIG,
        plateau_threshold=float(registry["registry"]["plateau_threshold"]),
        f_floor=float(registry["registry"]["f_floor"]),
        folds=FOLDS, search_segment=SEARCH_BAND, registry_path=str(REGISTRY))
    claim = {frozenset(f.best_subset): f.best_F_hat for f in finalists}
    mismatch = [len(rep.subset) for rep in out["plateau"]
                if not np.isclose(rep.F_hat, claim[rep.subset], rtol=1e-9)]
    artifact = {
        "universe": EXP, "stage": "certification",
        "search_band_ns": list(SEARCH_BAND),
        "folds_ns": [list(f) for f in FOLDS],
        "search_stage_evaluations": search_evals,
        "certify_stage_evaluations": out["evaluation_count"],
        "dispersion": out["dispersion"],
        "n_finalists": out["n_finalists"], "n_certified": out["n_certified"],
        "plateau_threshold": out["plateau_threshold"], "f_floor": out["f_floor"],
        "registry_sha256": out["registry_sha256"],
        "plateau": [dict(asdict(p), subset=sorted(p.subset)) for p in out["plateau"]],
        "keystones": out["keystones"],
        "ranked": [dict(asdict(r), subset=sorted(r.subset)) for r in out["ranked"]],
        "fold_diagnostics": out["fold_diagnostics"],
        "resim_divergence": out["resim_divergence"],
        "recompute_mismatch_subset_sizes": mismatch,
        "platform": platform_meta(),
        "seconds": round(time.time() - t0, 1),
    }
    (RESULTS / "certification.json").write_text(json.dumps(artifact, indent=1))
    print(f"[{EXP}] n_certified={out['n_certified']}/{out['n_finalists']} "
          f"({artifact['seconds']}s)", flush=True)


def rotate_streams(streams: list[CandidateStream], perm: int) -> list[CandidateStream]:
    """Battery v2 (operator-approved 2026-07-12): price-coherent re-marking rotation.

    Per candidate, rotate the whole trade stream in time (minute-aligned wraparound
    within the search band — breaks cross-candidate alignment, preserves cadence,
    durations, directions, stop distances), then SNAP entry/exit to the feed's mark grid
    and RE-MARK entry/exit prices from the grid opens at the new times. Per-leg P&L is
    re-derived causally at the rotated times — random re-timing matched-hold control
    (EXP-018 lineage), never a P&L permutation (L-14). Fixes run-1 confound where stale
    prices at rotated times garbled the MTM path and biased permuted F down."""
    import hashlib as _hl
    a, b = SEARCH_BAND
    span_min = (b - a) // NS_MIN
    grids: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    out = []
    for s in streams:
        gk = id(s.marks)
        if gk not in grids:
            grids[gk] = (s.marks.get_column("CloseTime").to_numpy(),
                         s.marks.get_column("Open").to_numpy())
        mt, mo = grids[gk]
        seed = int.from_bytes(
            _hl.sha256(f"{perm}:{s.candidate_id}".encode()).digest()[:8], "big")
        rng = np.random.default_rng(seed)
        delta = int(rng.integers(1, span_min)) * NS_MIN
        t = s.trades
        e = t.get_column("EntryTime").to_numpy()
        x = t.get_column("ExitTime").to_numpy()
        dur = x - e
        in_band = (e >= a) & (e < b)
        e_new = np.where(in_band, a + (e - a + delta) % (b - a), e)
        x_new = e_new + dur
        ie = np.minimum(np.searchsorted(mt, e_new, side="left"), len(mt) - 1)
        ix = np.searchsorted(mt, x_new, side="left")
        wrapped = ix >= len(mt)
        ix = np.minimum(ix, len(mt) - 1)
        censored = t.get_column("Censored").to_numpy() | wrapped
        t2 = (pl.DataFrame({
                "EntryTime": mt[ie], "ExitTime": np.maximum(mt[ix], mt[ie]),
                "Direction": t.get_column("Direction"),
                "EntryPrice": mo[ie], "ExitPrice": mo[ix],
                "StopDistance": t.get_column("StopDistance"),
                "Censored": censored})
              .sort("EntryTime"))
        out.append(CandidateStream(s.candidate_id, s.symbol, t2, s.marks,
                                   s.cost_bps, s.money_per_unit))
    return out


def stage_battery(streams: list[CandidateStream]) -> None:
    budget = json.loads((RESULTS / "search_budget.json").read_text())["budget"]
    live = [json.loads(p.read_text())["best_F_hat"]
            for p in sorted(RESULTS.glob("search_restart_*.json"))]
    perms = []
    for chunk_start in range(0, K_PERM, PERM_CHUNK):
        chunk = range(chunk_start, min(chunk_start + PERM_CHUNK, K_PERM))
        pstreams = {perm: rotate_streams(streams, perm) for perm in chunk}
        for ps in pstreams.values():
            warm_prep_cache(ps)

        def one(job: tuple[int, int]) -> tuple[int, int, float]:
            perm, rid = job
            r = run_restart(pstreams[perm], CONFIG, budget=budget, restart_id=rid,
                            segment=SEARCH_BAND)
            return perm, rid, r.best_F_hat
        t = time.time()
        jobs = [(perm, rid) for perm in chunk for rid in PERM_RIDS]
        with ThreadPoolExecutor(len(jobs)) as ex:
            res = list(ex.map(one, jobs))
        clear_prepared_cache()
        for perm in chunk:
            fs = [f for p, _, f in res if p == perm]
            perms.append({"perm": perm, "best_F_hats": fs,
                          "seconds": round(time.time() - t, 1)})
            print(f"[{EXP} battery] perm={perm} F={[round(f, 4) for f in fs]}",
                  flush=True)
    flat = [f for p in perms for f in p["best_F_hats"]]
    artifact = {
        "universe": EXP, "stage": "permutation_null_battery",
        "design": ("battery v2 (operator-approved 2026-07-12): price-coherent "
                   "re-marking rotation — whole-stream minute-aligned wraparound "
                   "rotation per candidate within the search band, entry/exit snapped "
                   "to the feed mark grid and re-priced from grid opens at the new "
                   "times (random re-timing matched-hold control, EXP-018 lineage; "
                   "never P&L permutation, L-14). "
                   f"K={K_PERM} permutations x {len(PERM_RIDS)} restarts at the pinned "
                   "budget. Informative read: live-vs-permuted best-F gap; a LARGE gap "
                   "= leak/artifact alarm -> HARD STOP, operator."),
        "budget": budget, "k_perm": K_PERM, "restarts_per_perm": len(PERM_RIDS),
        "live_best_F_hats": live,
        "permuted": perms,
        "summary": {
            "live_median": float(np.median(live)), "live_max": float(max(live)),
            "perm_median": float(np.median(flat)), "perm_max": float(max(flat)),
            "perm_p95": float(np.quantile(flat, 0.95)),
            "live_median_pctile_in_perm": float((np.array(flat) <
                                                 np.median(live)).mean()),
            "live_max_pctile_in_perm": float((np.array(flat) < max(live)).mean()),
        },
        "platform": platform_meta(),
    }
    (RESULTS / "permutation_battery.json").write_text(json.dumps(artifact, indent=1))
    print(f"[{EXP}] battery summary {artifact['summary']}", flush=True)


def stage_evidence() -> None:
    def load(name: str):
        p = RESULTS / name
        return json.loads(p.read_text()) if p.exists() else None
    restarts = [json.loads(p.read_text())
                for p in sorted(RESULTS.glob("search_restart_*.json"))]
    bundle_manifest = ROOT / "data" / "strategy_runs" / EXP / "sha256_manifest.json"
    import hashlib
    pkg = {
        "universe": EXP, "stage": "evidence_package",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform_meta(),
        "adjudication_platform_note": (
            "sole adjudication platform for this universe's lifetime (search -> "
            "certification -> permutation battery -> final-gate computation); "
            "never mix platforms (1-ULP libm caveat, INFR-007)"),
        "parity": load("../../XENA-001/results/parity_remote.json") or "see parity_remote.json",
        "bundle_sha256_manifest_digest": hashlib.sha256(
            bundle_manifest.read_bytes()).hexdigest() if bundle_manifest.exists() else None,
        "budget": load("search_budget.json"),
        "search": [{k: r[k] for k in ("restart_id", "budget", "best_F_hat",
                                      "n_iterations", "n_kicks", "acceptance_rate",
                                      "gate_rejection_rate", "n_evaluations",
                                      "distinct_subsets", "seconds")}
                   for r in restarts],
        "best_subsets": {str(r["restart_id"]): r["best_subset"] for r in restarts},
        "certification": load("certification.json"),
        "permutation_battery": load("permutation_battery.json"),
        "gate_status": "NOT RUN — counted TEST read, operator-only (cap 2/universe)",
    }
    (RESULTS / "evidence_package.json").write_text(json.dumps(pkg, indent=1))
    print(f"[{EXP}] evidence package written", flush=True)


def main() -> None:
    t0 = time.time()
    stages = ("smoke", "prod", "certify", "battery", "evidence") if STAGE == "all" \
        else tuple(STAGE.split(","))
    streams = load_streams() if set(stages) - {"evidence", "budget"} else []
    if streams:
        print(f"[{EXP}] loaded {len(streams)} streams in {time.time()-t0:.1f}s",
              flush=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    for st in stages:
        if st == "smoke":
            stage_smoke(streams)
        elif st == "budget":
            stage_budget()
        elif st == "prod":
            stage_prod(streams)
        elif st == "certify":
            stage_certify(streams)
        elif st == "battery":
            stage_battery(streams)
        elif st == "evidence":
            stage_evidence()
    print(f"[{EXP}] ALL DONE in {(time.time()-t0)/3600:.2f}h", flush=True)


if __name__ == "__main__":
    main()
