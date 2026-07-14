"""XENA-001 certification stage (lane machinery, design.md §5 folds / §13 pipeline).

Reconstructs the 12 pulled EC2 restart results (search_restart_*.json) as
``RestartResult``s with fresh ``EvalCache``s — plateau_screen recomputes each
terminal F̂ deterministically (starts seeded by restart_id, oracle_seed 0), so
the recomputed base F̂ must match the pulled ``best_F_hat`` (asserted, rtol 1e-9).

Thresholds come from the hash-pinned frozen registry v3 (mandatory
``registry_path``); folds are the design §5 / QA run 4 pinned windows
(purge 14 calendar days AFTER each interior boundary only).

Usage: python run_certify.py
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from xen.xena.certify import certify_and_rank  # noqa: E402
from xen.xena.oracle import OracleConfig  # noqa: E402
from xen.xena.search import EvalCache, RestartResult  # noqa: E402

from run_search import SEARCH_BAND, load_streams  # noqa: E402

ROOT = Path(__file__).resolve().parents[4]
RESULTS = ROOT / "python" / "experiments" / "XENA-001" / "results"
REGISTRY = ROOT / "python" / "experiments" / "INFR-006" / "results" / "xena_frozen_registry.json"


def _ns(y: int, m: int, d: int) -> int:
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp() * 1e9)


# design §5 (Amendment-5) + QA run 4 check (b): pinned boundaries, 14-day purge
# applied AFTER each interior boundary only.
FOLDS = [
    (_ns(2023, 3, 8), _ns(2023, 6, 12)),
    (_ns(2023, 6, 26), _ns(2023, 9, 16)),
    (_ns(2023, 9, 30), _ns(2023, 12, 22)),
    (_ns(2024, 1, 5), _ns(2024, 3, 28)),
]


def main() -> None:
    t0 = time.time()
    registry = json.loads(REGISTRY.read_text())
    streams = load_streams()
    print(f"loaded {len(streams)} streams in {time.time()-t0:.1f}s", flush=True)
    config = OracleConfig(charge_costs=False)  # A-1: gross selection

    finalists = []
    search_evals = 0
    for p in sorted(RESULTS.glob("search_restart_*.json")):
        d = json.loads(p.read_text())
        assert tuple(d["band_ns"]) == SEARCH_BAND and d["charge_costs"] is False
        search_evals += d["n_evaluations"]
        finalists.append(RestartResult(
            best_subset=frozenset(d["best_subset"]), best_F_hat=d["best_F_hat"],
            restart_id=d["restart_id"], n_iterations=d["n_iterations"],
            n_kicks=d["n_kicks"], acceptance_rate=d["acceptance_rate"],
            gate_rejection_rate=d["gate_rejection_rate"], cache=EvalCache()))
    print(f"{len(finalists)} finalists; search-stage evals={search_evals}", flush=True)

    out = certify_and_rank(
        finalists, streams, config,
        plateau_threshold=float(registry["registry"]["plateau_threshold"]),
        f_floor=float(registry["registry"]["f_floor"]),
        folds=FOLDS, search_segment=SEARCH_BAND,
        registry_path=str(REGISTRY))

    # determinism cross-check: recomputed base F̂ (plateau report) vs pulled search claim
    claim = {frozenset(f.best_subset): f.best_F_hat for f in finalists}
    for rep in out["plateau"]:
        pulled = claim[rep.subset]
        if not np.isclose(rep.F_hat, pulled, rtol=1e-9):
            print(f"WARNING: recomputed F_hat {rep.F_hat} != pulled {pulled} "
                  f"for size-{len(rep.subset)} subset", flush=True)

    artifact = {
        "universe": "XENA-001",
        "stage": "certification",
        "search_band_ns": list(SEARCH_BAND),
        "folds_ns": [list(f) for f in FOLDS],
        "search_stage_evaluations": search_evals,
        "certify_stage_evaluations": out["evaluation_count"],
        "dispersion": out["dispersion"],
        "n_finalists": out["n_finalists"],
        "n_certified": out["n_certified"],
        "plateau_threshold": out["plateau_threshold"],
        "f_floor": out["f_floor"],
        "registry_sha256": out["registry_sha256"],
        "plateau": [dict(asdict(p), subset=sorted(p.subset)) for p in out["plateau"]],
        "keystones": out["keystones"],
        "ranked": [dict(asdict(r), subset=sorted(r.subset)) for r in out["ranked"]],
        "fold_diagnostics": out["fold_diagnostics"],
        "resim_divergence": out["resim_divergence"],
        "seconds": round(time.time() - t0, 1),
    }
    (RESULTS / "certification.json").write_text(json.dumps(artifact, indent=1))
    print(f"n_certified={out['n_certified']} / {out['n_finalists']}; "
          f"certify evals={out['evaluation_count']}; done in {time.time()-t0:.1f}s",
          flush=True)


if __name__ == "__main__":
    main()
