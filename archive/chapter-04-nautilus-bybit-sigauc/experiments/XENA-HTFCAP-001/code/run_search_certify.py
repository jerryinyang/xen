#!/usr/bin/env python3
"""XENA-HTFCAP-001 stage-1 search + certify (CLS-FILTER / INFR-015 pin abbb1842…).

Operator-authorized EXPLORATORY run (AMENDMENT-4/5, 2026-07-18). Mirrors the EPSOSC
search/certify sibling; CLS-FILTER deltas:
  * search universe = BINDING cells only (BTC+SOL); ETH is disclosure-only (never here).
  * stage-2 = lcb_g_leg_studentized(g_gross) with block_legs=1 (design §5) — NOT the
    episode-overlap variant.
  * AMENDMENT-5: n_legs_floor(16) is INFORMATIVE, not gating. pass_positive reflects the
    raw machinery LCB>0; the floor is reported as `in_domain_16` alongside, never forced.
  * NO reserved OOS; stage-2 gate band lands in TEST (spent). Results are informative-only,
    NOT a certification / deployability claim. Does NOT run the counted final TEST gate.

Usage (from python/):
  uv run python experiments/XENA-HTFCAP-001/code/run_search_certify.py
  uv run python experiments/XENA-HTFCAP-001/code/run_search_certify.py --n-restarts 12 --budget 200
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CODE = Path(__file__).resolve().parent
EXP = CODE.parent
ROOT = EXP.parents[1]  # python/
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from xen.xena.calibration_bybit import (  # noqa: E402
    assert_stage1_net_binding,
    verify_bybit_registry,
)
from xen.xena.calibration_p3d import eval_lcb_legs  # noqa: E402  CLS-FILTER stage-2
from xen.xena.calibration_pc import (  # noqa: E402
    EMBARGO_FRAC,
    STAGE_RANKING_FRAC,
    STAGE_SEARCH_FRAC,
)
from xen.xena.certify import certify_and_rank, contiguous_purged_folds  # noqa: E402
from xen.xena.economics import economics_disclosure  # noqa: E402
from xen.xena.ingest import gate_universe, load_universe  # noqa: E402
from xen.xena.oracle import OracleConfig  # noqa: E402
from xen.xena.search import SearchParams, run_restart  # noqa: E402

UNIVERSE_ID = "XENA-HTFCAP-001"
RUNS_ROOT = REPO / "data" / "nautilus_runs" / UNIVERSE_ID
FULL_MANIFEST = RUNS_ROOT / "universe_manifest.json"
SEARCH_MANIFEST = RUNS_ROOT / "search_manifest_binding.json"
RESULTS = EXP / "results"
REGISTRY = REPO / "python/experiments/INFR-015/results/bybit_pc_frozen_registry.json"
STAGE_BANDS = RESULTS / "stage_bands.json"
XENA_RUNS_LEDGER = REPO / "docs/signal-registry/xena-runs.md"

PIN_SHA_EXPECTED = "abbb184229236a75f624537ca605668a73f6f85138c150e14a3609c4191bf786"

# Design §5: 10–15 restarts; pin n_boot=200; stage-2 block_legs=1; g_net stage-1
DEFAULT_N_RESTARTS = 12
DEFAULT_BUDGET = 200
N_LEGS_FLOOR = 16          # INFORMATIVE only (AMENDMENT-5)
N_BOOT = 200
STAGE2_BLOCK_LEGS = 1      # CLS-FILTER leg bootstrap (design §5)
# Max hold H = 64×15m = 16h → purge ranking folds by max hold
PURGE_NS = int(16 * 3600 * 1e9)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_binding_search_manifest() -> dict[str, Any]:
    """Subset full manifest to emitted BINDING cells (BTC+SOL); run_dir → <cid>/xena."""
    full = json.loads(FULL_MANIFEST.read_text(encoding="utf-8"))
    cands = []
    for c in full["candidates"]:
        if c.get("role") != "binding":
            continue
        cid = c["candidate_id"]
        xena = RUNS_ROOT / cid / "xena"
        if not (xena / "cis_trades.parquet").exists():
            continue
        row = dict(c)
        row["run_dir"] = f"{cid}/xena"
        row["emission_dir"] = cid
        row["emitted"] = True
        cands.append(row)
    if not cands:
        raise RuntimeError("no emitted binding candidates for search manifest")
    out = {
        "universe_id": UNIVERSE_ID,
        "family": full.get("family"),
        "lane": "XENA",
        "schema": "xena.universe_manifest.v1.search_binding",
        "generated_utc": _utc_now(),
        "n_candidates": len(cands),
        "role_filter": "binding",
        "stage_bands": full.get("stage_bands"),
        "registry": full.get("registry"),
        "candidates": cands,
        "note": (
            "Search/certify universe: BINDING cells only (BTC+SOL); ETH disclosure "
            "excluded (never verdict-bearing; 12 ETH v1.1 cells also fail oracle_smoke "
            "NaN — disclosure caveat, off the binding path)."
        ),
    }
    SEARCH_MANIFEST.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    (RESULTS / "search_manifest_binding.json").write_text(
        json.dumps(out, indent=2) + "\n", encoding="utf-8"
    )
    return out


def load_segments() -> dict[str, tuple[int, int]]:
    bands = json.loads(STAGE_BANDS.read_text(encoding="utf-8"))
    return {
        "search": (int(bands["search"]["start_ns"]), int(bands["search"]["end_ns"])),
        "ranking": (int(bands["ranking"]["start_ns"]), int(bands["ranking"]["end_ns"])),
        "gate": (
            int(bands["stage2_gate"]["start_ns"]),
            int(bands["stage2_gate"]["end_ns"]),
        ),
    }


def append_xena_runs_registration(*, n_cands: int, pin_sha: str, search_band: str) -> None:
    """Idempotent: HTFCAP already registered (AMENDMENT-4 TEST-spend row). Skip if present."""
    if not XENA_RUNS_LEDGER.exists():
        return
    text = XENA_RUNS_LEDGER.read_text(encoding="utf-8")
    if "| XENA-HTFCAP-001 |" in text or "XENA-HTFCAP-001" in text:
        return
    row = (
        f"| XENA-HTFCAP-001 | {_utc_now()[:10]} | CF-HTFCAP-001 binding "
        f"({n_cands}) | {pin_sha[:8]} | {search_band} | *(exploratory)* | "
        f"*(informative)* | — | **1/2** | search/certify EXPLORATORY (AMENDMENT-4/5); "
        f"no reserved OOS; no final gate | pending |\n"
    )
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    inserted = False
    for i, ln in enumerate(lines):
        out.append(ln)
        if (not inserted and ln.startswith("|---") and i > 0
                and lines[i - 1].startswith("| Run |")):
            out.append(row)
            inserted = True
    if not inserted:
        out.append("\n" + row)
    XENA_RUNS_LEDGER.write_text("".join(out), encoding="utf-8")


def serialize_restart(r: Any) -> dict[str, Any]:
    return {
        "restart_id": int(r.restart_id),
        "best_subset": sorted(r.best_subset),
        "best_F_hat": float(r.best_F_hat),
        "n_iterations": int(r.n_iterations),
        "n_kicks": int(r.n_kicks),
        "acceptance_rate": float(r.acceptance_rate),
        "gate_rejection_rate": float(r.gate_rejection_rate),
        "cache_size": int(len(r.cache._store)) if hasattr(r.cache, "_store") else None,
    }


def stage2_filter(top: frozenset, streams, config, gate_seg) -> dict[str, Any]:
    """CLS-FILTER stage-2: leg-studentized LCB (block_legs=1) on the embargoed gate band.

    AMENDMENT-5: n_legs_floor is INFORMATIVE. pass_positive is the raw machinery verdict
    (lcb>0); the 16-leg floor is reported as `in_domain_16`, never forced onto the verdict.
    """
    lcb_g = eval_lcb_legs(top, streams, config, gate_seg, n_boot=N_BOOT, seed=42,
                          block_legs=STAGE2_BLOCK_LEGS, net=False)
    lcb_n = eval_lcb_legs(top, streams, config, gate_seg, n_boot=N_BOOT, seed=42 + 17,
                          block_legs=STAGE2_BLOCK_LEGS, net=True)
    n_legs = int(lcb_g.get("n_legs") or 0)
    in_domain_16 = n_legs >= N_LEGS_FLOOR
    return {
        "empty": False,
        "top": sorted(top),
        "gross": lcb_g,
        "net": lcb_n,
        "stage2_gross_lcb_positive": bool(lcb_g.get("pass_positive")),
        "stage2_net_lcb_positive": bool(lcb_n.get("pass_positive")),
        "n_legs": n_legs,
        "n_legs_floor_informative": N_LEGS_FLOOR,
        "in_domain_16": in_domain_16,
        "floor_note": (
            "AMENDMENT-5: floor informative only; verdict language void — reads are "
            "exploratory evidence, not a pin-backed certification"
        ),
        "block_legs": STAGE2_BLOCK_LEGS,
        "e2e_pass_event": "stage2_gross_lcb_positive",
        "deployability_binding": "stage2_net_lcb_positive",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="XENA-HTFCAP-001 search + certify (exploratory)")
    ap.add_argument("--n-restarts", type=int, default=DEFAULT_N_RESTARTS)
    ap.add_argument("--budget", type=int, default=DEFAULT_BUDGET)
    ap.add_argument("--skip-gate", action="store_true", help="reuse existing gate artifact")
    ap.add_argument("--skip-economics", action="store_true")
    args = ap.parse_args()

    RESULTS.mkdir(parents=True, exist_ok=True)
    assert_stage1_net_binding(charge_costs=True, score_kind="g_net")

    verify_bybit_registry(REGISTRY)
    pin_sha = json.loads(REGISTRY.read_text(encoding="utf-8"))["sha256"]
    if pin_sha != PIN_SHA_EXPECTED:
        raise SystemExit(f"pin sha mismatch: {pin_sha} != {PIN_SHA_EXPECTED}")
    print(f"PIN content_sha={pin_sha} class=CLS-FILTER verified")

    print("Writing binding search manifest…")
    sm = write_binding_search_manifest()
    n_cands = sm["n_candidates"]
    print(f"  n_binding_candidates={n_cands}")

    segs = load_segments()
    search_seg, ranking_seg, gate_seg = segs["search"], segs["ranking"], segs["gate"]
    search_band_str = (
        f"{datetime.fromtimestamp(search_seg[0]/1e9, tz=timezone.utc).isoformat()} → "
        f"{datetime.fromtimestamp(search_seg[1]/1e9, tz=timezone.utc).isoformat()}"
    )
    append_xena_runs_registration(n_cands=n_cands, pin_sha=pin_sha,
                                  search_band=search_band_str)
    print(f"  search band {search_band_str}")

    # Q1 economics (writes artifact required by run_restart economics precondition)
    if not args.skip_economics:
        print("economics_disclosure (Q1)…")
        econ = economics_disclosure(
            SEARCH_MANIFEST, segment=search_seg, max_workers=4, write_artifact=True,
            operator_routing="proceed_deployability_search",
            routing_reason="operator-approved exploratory search/certify 2026-07-18",
        )
        (RESULTS / "economics_disclosure.json").write_text(
            json.dumps({k: v for k, v in econ.items() if not str(k).startswith("_")},
                       indent=2, allow_nan=True) + "\n", encoding="utf-8")
        print(f"  search_allowed={econ.get('search_allowed')} "
              f"gross_p50={econ.get('gross_economics', {}).get('p50')}")
        if not econ.get("search_allowed"):
            raise SystemExit("search refused by economics_disclosure")

    # Candidate gate on binding manifest
    if not args.skip_gate:
        print("gate_universe (binding)…")
        gate = gate_universe(SEARCH_MANIFEST, write_artifact=True)
        (RESULTS / "xena_candidate_gate_binding.json").write_text(
            json.dumps(gate, indent=2) + "\n", encoding="utf-8")
        print(f"  blocking_pass={gate['blocking_pass']} "
              f"n_pass={gate['n_pass']}/{gate['n_candidates']}")
        if not gate["blocking_pass"]:
            fails = [c["candidate_id"] for c in gate["candidates"]
                     if not c["blocking_pass"]]
            raise SystemExit(f"binding candidate gate FAILED: {fails[:5]}")

    print("load_universe…")
    uni = load_universe(SEARCH_MANIFEST)
    streams = uni.streams
    print(f"  streams={len(streams)}")

    # Search engine params — CAL LOW cadence shape (pin class); not chapter-03 extensive-F
    params = SearchParams(L=40, n_boot=80, block_bars=64, init_size=4)
    config = OracleConfig(charge_costs=True)
    print(f"LAHC search: restarts={args.n_restarts} budget={args.budget} "
          f"score=g_net charge_costs=True segment=search")

    finalists = []
    eval_count = 0
    for r in range(args.n_restarts):
        print(f"  restart {r + 1}/{args.n_restarts}…", flush=True)
        fr = run_restart(
            streams, config, budget=args.budget, restart_id=r + 1, params=params,
            segment=search_seg, universe_root=str(RUNS_ROOT),
            skip_economics_precondition=False, score_kind="g_net",
        )
        finalists.append(fr)
        cs = len(fr.cache._store) if hasattr(fr.cache, "_store") else 0
        eval_count += cs
        print(f"    F_hat={fr.best_F_hat:.6g} |S|={len(fr.best_subset)} "
              f"cache={cs} accept={fr.acceptance_rate:.3f}", flush=True)

    # Certification / ranking on ranking band folds
    folds = contiguous_purged_folds(ranking_seg[0], ranking_seg[1], n_folds=3,
                                    purge_ns=PURGE_NS)
    print(f"certify_and_rank: {len(folds)} folds on ranking band…")
    pkg = certify_and_rank(
        finalists, streams, config, folds=folds, params=params,
        search_segment=search_seg, include_random_ref=True, include_fill_basis=False,
        score_kind="g_net", registry_path=None, n_random_ref=32,
    )

    ranked_ser = []
    for fr in pkg.get("ranked") or []:
        ranked_ser.append({
            "subset": sorted(fr.subset),
            "fold_F": [float(x) for x in fr.fold_F],
            "median_F": float(fr.median_F),
            "worst_F": float(fr.worst_F),
            "search_F_hat": float(fr.search_F_hat),
            "score_kind": fr.score_kind,
        })

    # Stage-2 gate band: top-1 only (pin one_subset), CLS-FILTER leg-studentized LCB
    stage2: dict[str, Any] = {"empty": True}
    if ranked_ser:
        top = frozenset(ranked_ser[0]["subset"])
        print(f"stage-2 LCB (CLS-FILTER, block_legs=1) on gate band, top-1 |S|={len(top)}…")
        stage2 = stage2_filter(top, streams, config, gate_seg)
        print(f"  n_legs={stage2['n_legs']} in_domain_16={stage2['in_domain_16']} "
              f"gross_lcb_pos={stage2['stage2_gross_lcb_positive']} "
              f"gross_lcb={(stage2['gross'] or {}).get('lcb')} "
              f"net_lcb_pos={stage2['stage2_net_lcb_positive']}")

    distinct = {frozenset(serialize_restart(r)["best_subset"]) for r in finalists}
    out = {
        "universe_id": UNIVERSE_ID,
        "generated_utc": _utc_now(),
        "class_id": "CLS-FILTER",
        "run_mode": "EXPLORATORY (AMENDMENT-4/5) — informative only, NOT certification",
        "pin_path": str(REGISTRY.relative_to(REPO)),
        "pin_sha256": pin_sha,
        "pin_verified": True,
        "stage1": {
            "score_kind": "g_net", "charge_costs": True,
            "n_restarts": args.n_restarts, "budget": args.budget,
            "search_params": asdict(params),
            "search_segment_ns": list(search_seg),
            "eval_count": eval_count,
            "distinct_restart_terminals": len(distinct),
            "finalists": [serialize_restart(r) for r in finalists],
        },
        "certify": {
            "score_kind": "g_net", "ranking_segment_ns": list(ranking_seg),
            "folds_ns": [list(f) for f in folds], "ranked": ranked_ser,
            "n_ranked": len(ranked_ser), "dispersion": pkg.get("dispersion"),
            "fold_diag": pkg.get("fold_diag") or pkg.get("folds"),
            "purge_ns": PURGE_NS,
        },
        "stage2_gate_band": stage2,
        "segments": {
            "search": list(search_seg), "ranking": list(ranking_seg),
            "gate": list(gate_seg),
            "fracs": {"search": STAGE_SEARCH_FRAC, "ranking": STAGE_RANKING_FRAC,
                      "embargo": EMBARGO_FRAC},
            "note": "AMENDMENT-4: gate band lands in TEST (spent); NO reserved OOS",
        },
        "n_candidates": n_cands,
        "final_gate": {
            "run": False,
            "note": "counted TEST final gate NOT run — exploratory; no deployability claim",
        },
    }
    out_path = RESULTS / "search_certify_package.json"
    out_path.write_text(json.dumps(out, indent=2, default=str) + "\n", encoding="utf-8")
    summary = {
        "universe_id": UNIVERSE_ID, "generated_utc": out["generated_utc"],
        "run_mode": out["run_mode"], "n_candidates": n_cands,
        "n_restarts": args.n_restarts, "eval_count": eval_count,
        "distinct_restart_terminals": len(distinct),
        "top1": stage2.get("top"),
        "stage2_gross_lcb_positive": stage2.get("stage2_gross_lcb_positive"),
        "stage2_net_lcb_positive": stage2.get("stage2_net_lcb_positive"),
        "n_legs": stage2.get("n_legs"), "in_domain_16": stage2.get("in_domain_16"),
        "gross_lcb": (stage2.get("gross") or {}).get("lcb"),
        "net_lcb": (stage2.get("net") or {}).get("lcb"),
        "pin_sha256": pin_sha, "final_gate_run": False,
        "paths": {"package": str(out_path.relative_to(REPO))},
    }
    (RESULTS / "search_certify_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"WROTE {out_path}")
    print("NOTE: run_final_gate NOT executed (exploratory; no counted TEST gate).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
