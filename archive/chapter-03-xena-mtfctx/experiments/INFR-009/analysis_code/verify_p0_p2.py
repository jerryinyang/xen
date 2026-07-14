"""INFR-009 verification harness (P0–P2).

* Q1 economics on XENA-001/002/003 (read-only fixtures; no search tuning)
* High-cadence null diagnostics (P0′)
* Synthetic g_gross + fill-basis smoke (P1/P2)

Writes python/experiments/INFR-009/results/verification.json
NEVER opens TEST/holdout; NEVER calls run_final_gate.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "python" / "src"))

from xen.xena.economics import economics_disclosure  # noqa: E402
from xen.xena.fill_basis import decompose_stream, summarize_decomposition  # noqa: E402
from xen.xena.high_cadence_null import (HighCadenceNullSpec,  # noqa: E402
                                        build_high_cadence_null, null_diagnostics)
from xen.xena.oracle import OracleConfig, evaluate  # noqa: E402
from xen.xena.score import g_gross_point  # noqa: E402
from xen.xena.search import SearchParams, run_restart  # noqa: E402
from xen.xena.certify import certify_and_rank, contiguous_purged_folds  # noqa: E402

OUT = ROOT / "python" / "experiments" / "INFR-009" / "results"
NS = 1_000_000_000

# Pre-registered search band (shared XENA-00x designs)
SEARCH = (1622592060000000000, 1678233600000000000)

# Binding acceptance targets (design.md §8) — honest INFR-009 recompute, not proposal sketch
EXPECTED_P50 = {
    "XENA-001": 0.043,
    "XENA-002": -0.284,
    "XENA-003": 1.91,
}
# Sampling noise tolerance for universe-level median of per-candidate mean gross bps
P50_TOL = {"XENA-001": 0.15, "XENA-002": 0.15, "XENA-003": 0.05}


def verify_q1() -> dict:
    rows = {}
    for uid, exp in EXPECTED_P50.items():
        man = ROOT / "data" / "strategy_runs" / uid / "universe_manifest.json"
        if not man.exists():
            rows[uid] = {"ok": False, "error": "manifest_missing"}
            continue
        art = economics_disclosure(man, segment=SEARCH, max_workers=8, write_artifact=True)
        p50 = art["gross_economics"]["p50"]
        tol = P50_TOL[uid] if isinstance(P50_TOL, dict) else P50_TOL
        rows[uid] = {
            "p50_gross_bps": p50,
            "expected": exp,
            "abs_err": abs(p50 - exp) if p50 == p50 else None,
            "within_tol": bool(abs(p50 - exp) <= tol) if p50 == p50 else False,
            "cost_map_complete": art["cost_map_integrity"]["complete"],
            "search_allowed": art["search_allowed"],
            "integrity_label": art["cost_map_integrity"]["status_label"],
            "n_with_legs": art["gross_economics"]["n_with_legs"],
        }
        # fixtures ship cost_bps=0 → must block search
        rows[uid]["incomplete_cost_blocks_search"] = (
            not art["cost_map_integrity"]["complete"] and not art["search_allowed"]
        )
    return rows


def verify_p0_prime() -> dict:
    spec = HighCadenceNullSpec(
        n_candidates=24, n_bars=20_000, target_legs_per_candidate=4_000,
        hold_bars=10, seed=42)
    streams = build_high_cadence_null(spec)
    return null_diagnostics(streams)


def verify_p1_p2_synthetic() -> dict:
    streams = build_high_cadence_null(HighCadenceNullSpec(
        n_candidates=8, n_bars=8_000, target_legs_per_candidate=800,
        hold_bars=8, edge_bps=0.0, seed=99))
    cfg = OracleConfig(charge_costs=False)
    params = SearchParams(L=20, n_boot=30, init_size=3)
    finals = [run_restart(streams, cfg, budget=40, restart_id=i, params=params)
              for i in (1, 2)]
    folds = contiguous_purged_folds(0, 8000 * 60 * NS, n_folds=2, purge_ns=60 * 60 * NS)
    pkg = certify_and_rank(finals, streams, cfg, folds=folds, params=params,
                           include_random_ref=False)
    fb = summarize_decomposition(decompose_stream(streams[0]))
    g = g_gross_point(evaluate({streams[0].candidate_id}, streams[:1], cfg), streams[:1])
    return {
        "package_kind": pkg["package_kind"],
        "score_kind": pkg["score_kind"],
        "retired_binders": pkg["retired_binders"],
        "n_shortlisted": pkg["n_shortlisted"],
        "hard_battery": pkg["hard_permutation_battery"],
        "sample_g_gross": g,
        "fill_basis_gridlike_or_ok": fb.get("identity_ok", False),
        "fill_basis_print_mean": fb.get("print_mean_bps"),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    report = {
        "redesign": "INFR-009",
        "scope": ["P0", "P0_prime", "P1", "P2"],
        "q1_fixtures": verify_q1(),
        "p0_prime_null": verify_p0_prime(),
        "p1_p2_synthetic": verify_p1_p2_synthetic(),
    }
    # overall flags
    q1 = report["q1_fixtures"]
    report["q1_all_within_tol"] = all(
        q1.get(u, {}).get("within_tol") for u in EXPECTED_P50)
    report["q1_all_block_incomplete_cost"] = all(
        q1.get(u, {}).get("incomplete_cost_blocks_search") for u in EXPECTED_P50)
    report["p0_prime_ok"] = bool(
        report["p0_prime_null"].get("zero_edge_ok")
        and report["p0_prime_null"].get("high_cadence_ok"))
    path = OUT / "verification.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report, indent=2, default=str))
    print("wrote", path)


if __name__ == "__main__":
    main()
