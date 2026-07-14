"""A2 — is the frozen `gate_pass_threshold` (0.0558) binding at LIVE scale?

Diagnostic, not a gate. `xen.xena.final_gate.run_final_gate` is NEVER called here: it
would spend an irreversible counted ledger slot. This script *reconstructs* the gate
statistic — the GROSS-block bootstrap P25 of log-wealth F — exactly as
``run_final_gate``'s inner ``walk_forward_block(config_gross)`` computes it
(final_gate.py L211-224), reusing the library functions verbatim:

    res    = evaluate(subset, streams, config_gross, segment=SEG, seed=0)
    grid   = clip_grid_covering(universe_grid(streams), SEG, streams)
    inc    = grid_increments(res, grid)
    starts = bootstrap_block_starts(len(grid), block=params.block_bars,
                                    n_boot=max(params.n_boot, 200), seed=424243)
    boot   = bootstrap_F(inc, starts, block=params.block_bars,
                         initial_equity=cfg.initial_equity)
    p25    = np.quantile(boot, 0.25)          # <-- THE GATE STATISTIC

BAND — GOVERNANCE. The real gate band is TEST (2024-03-28T00:00Z -> 2024-12-11T08:19Z)
and is NOT read. All computation runs on SEG_PROXY, a TRAIN window of matched duration
immediately preceding TEST:

    SEG_PROXY = 2023-07-13T00:00Z -> 2024-03-28T00:00Z   (259d 00h00m)
    TEST      = 2024-03-28T00:00Z -> 2024-12-11T08:19Z   (258d 08h19m)
    duration delta = 15h41m  (< 1 day, as specified)

SEG_PROXY sits inside the TRAIN ranking band (search ends 2023-03-08; folds run to
2024-03-28). The final-30% global holdout is untouched.

One disclosed structural caveat: ``clip_grid_covering(..., streams)`` may append the
first universe bar-close >= segment end when the universe has within-segment fills
stamped after the last interior bar (XENA-003 native m1 fills, Amendment 4). That
appended element is a bar *timestamp* only — a bin for events that all occur strictly
inside SEG_PROXY (the oracle censors positions at the segment end, so no P&L event can
land outside). No TEST price and no TEST trade is read. We call the library function
unmodified (matching final_gate.py exactly, per instruction) and record
``grid_covering_append_fired`` per universe.

Experiment
----------
Step 1  XENA-001 (RANDOM-entry universe = genuine no-edge null on real prices, live
        scale) — N=200 *unselected* random subsets, sizes ~ Uniform{39..104} (the
        observed span of its 12 search finalists). Their gate-P25 distribution is the
        live-scale NULL distribution of the gate statistic. Re-derive the threshold
        under the registry's own rule: max(0, P95 of null gate P25s).
Step 2  Fraction of those 200 null subsets that clear the pinned 0.0558.
Step 3  Same random-subset draw for XENA-002 (34..68) and XENA-003 (24..37). These are
        NOT nulls (informed entries) — read as SCALE, i.e. how the location of the
        gate-statistic distribution moves with trade density / cadence.
Step 4  XENA-003's 12 certified finalist subsets, gate statistic on SEG_PROXY. A scale
        diagnostic on TRAIN — explicitly NOT a gate read.

Usage:  python a2_gate_threshold_scale_test.py [n_null]
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[3]          # .../python
REPO = ROOT.parent                                   # repo root
sys.path.insert(0, str(ROOT / "src"))

from xen.xena.final_gate import dd_feasibility                       # noqa: E402
from xen.xena.oracle import CandidateStream, OracleConfig, evaluate  # noqa: E402
from xen.xena.search import (SearchParams, bootstrap_F,              # noqa: E402
                             bootstrap_block_starts, clip_grid_covering,
                             grid_increments, universe_grid)

# --------------------------------------------------------------------------- #
# Frozen registry v3 — the pinned constants under scrutiny (read-only)
# --------------------------------------------------------------------------- #
REGISTRY_PATH = REPO / "python/experiments/INFR-006/results/xena_frozen_registry.json"
OUT_PATH = REPO / "python/experiments/INFR-006/results/a2_gate_threshold_live_scale.json"

BOOT_SEED = 424243                      # final_gate.run_final_gate default
ORACLE_SEED = 0                         # final_gate default oracle_seed
PARAMS = SearchParams()                 # registry defaults: block_bars=64, n_boot=150
CONFIG_GROSS = OracleConfig(charge_costs=False)     # A-4: the BINDING gate block
N_NULL_DEFAULT = 200

# TEST band — declared for the duration check ONLY. Never used as a segment.
TEST_BAND_NS = (
    int(datetime(2024, 3, 28, 0, 0, tzinfo=timezone.utc).timestamp() * 1e9),
    int(datetime(2024, 12, 11, 8, 19, tzinfo=timezone.utc).timestamp() * 1e9),
)
SEG_PROXY = (
    int(datetime(2023, 7, 13, 0, 0, tzinfo=timezone.utc).timestamp() * 1e9),
    int(datetime(2024, 3, 28, 0, 0, tzinfo=timezone.utc).timestamp() * 1e9),
)

# Observed span of each universe's 12 search finalists (search_restart_*.json).
FINALIST_SIZE_RANGE: dict[str, tuple[int, int]] = {
    "XENA-001": (39, 104),
    "XENA-002": (34, 68),
    "XENA-003": (24, 37),
}
DRAW_SEED: dict[str, int] = {"XENA-001": 20260713, "XENA-002": 20260714,
                             "XENA-003": 20260715}


def load_universe_streams(universe: str) -> list[CandidateStream]:
    """Load the universe exactly as its own driver does (same `run_search.load_streams`
    path `certify_and_rank` consumed) — no re-implementation of ingest."""
    code_dir = REPO / "python" / "experiments" / universe / "code"
    for stale in [m for m in list(sys.modules) if m == "run_search"]:
        del sys.modules[stale]
    sys.path.insert(0, str(code_dir))
    try:
        import run_search  # noqa: PLC0415
        return run_search.load_streams()
    finally:
        sys.path.remove(str(code_dir))
        sys.modules.pop("run_search", None)


def gate_statistic(subset: frozenset[str], streams: list[CandidateStream],
                   grid: np.ndarray, cfg: OracleConfig) -> dict[str, Any]:
    """The GROSS gate statistic, byte-for-byte the chain in
    `final_gate.walk_forward_block(config_gross)` (final_gate.py L214-247)."""
    res = evaluate(subset, streams, cfg, segment=SEG_PROXY, seed=ORACLE_SEED)
    inc = grid_increments(res, grid)
    starts = bootstrap_block_starts(len(grid), block=PARAMS.block_bars,
                                    n_boot=max(PARAMS.n_boot, 200), seed=BOOT_SEED)
    boot = bootstrap_F(inc, starts, block=PARAMS.block_bars,
                       initial_equity=cfg.initial_equity)
    p25, p50, p75 = (float(np.quantile(boot, q)) for q in (0.25, 0.5, 0.75))
    dd = dd_feasibility(res.equity_times, res.equity, initial_equity=cfg.initial_equity)
    return {"n_candidates": len(subset), "gate_p25": p25, "gate_median": p50,
            "gate_p75": p75, "F_point": float(res.F_point),
            "n_admitted": int(res.n_admitted), "n_rejected": int(res.n_rejected),
            "dd_feasible": bool(dd["feasible"]),
            "worst_total_dd": float(dd["worst_total_dd"]),
            "worst_daily_dd": float(dd["worst_daily_dd"])}


def summarize(p25s: np.ndarray, pinned: float) -> dict[str, Any]:
    q = {f"p{int(p * 100):02d}": float(np.quantile(p25s, p))
         for p in (0.05, 0.25, 0.50, 0.75, 0.95)}
    return {
        "n": int(len(p25s)), "min": float(p25s.min()), **q, "max": float(p25s.max()),
        "mean": float(p25s.mean()),
        "frac_ge_pinned_threshold": float((p25s >= pinned).mean()),
        "rederived_threshold_p95_rule": float(max(0.0, np.quantile(p25s, 0.95))),
    }


def run_universe(universe: str, n_null: int, pinned: float) -> dict[str, Any]:
    t0 = time.time()
    streams = load_universe_streams(universe)
    grid = clip_grid_covering(universe_grid(streams), SEG_PROXY, streams)
    append_fired = bool(int(grid[-1]) >= SEG_PROXY[1])
    ids = np.array(sorted(s.candidate_id for s in streams))
    lo, hi = FINALIST_SIZE_RANGE[universe]
    rng = np.random.default_rng(DRAW_SEED[universe])

    rows: list[dict[str, Any]] = []
    for _ in tqdm(range(n_null), desc=f"{universe} null subsets", unit="subset"):
        size = int(rng.integers(lo, hi + 1))            # Uniform{lo..hi}, inclusive
        subset = frozenset(rng.choice(ids, size=size, replace=False).tolist())
        rows.append(gate_statistic(subset, streams, grid, CONFIG_GROSS))

    p25s = np.array([r["gate_p25"] for r in rows], dtype=float)
    block: dict[str, Any] = {
        "universe": universe,
        "n_candidates_in_pool": len(ids),
        "subset_size_range": [lo, hi],
        "draw_seed": DRAW_SEED[universe],
        "grid_bars": int(len(grid)),
        "grid_first_ns": int(grid[0]), "grid_last_ns": int(grid[-1]),
        "grid_covering_append_fired": append_fired,
        "random_subsets": {"summary": summarize(p25s, pinned), "rows": rows},
        "seconds": round(time.time() - t0, 1),
    }

    # Step 4 — XENA-003's certified finalists (TRAIN scale diagnostic, NOT a gate read)
    if universe == "XENA-003":
        ev = json.loads((REPO / "python/experiments/XENA-003/results/"
                         "evidence_package.json").read_text(encoding="utf-8"))
        ranked = ev["certification"]["ranked"]
        cert: list[dict[str, Any]] = []
        for r in tqdm(ranked, desc="XENA-003 certified finalists", unit="subset"):
            row = gate_statistic(frozenset(r["subset"]), streams, grid, CONFIG_GROSS)
            row["search_F_hat_claim"] = float(r["search_F_hat"])
            row["ranking_median_F"] = float(r["median_F"])
            row["passes_pinned_0p0558"] = bool(row["gate_p25"] >= pinned)
            cert.append(row)
        block["certified_finalists_scale_diagnostic"] = {
            "note": ("SEG_PROXY (TRAIN) scale diagnostic — explicitly NOT a gate read. "
                     "The counted gate runs on TEST and is operator-only."),
            "n": len(cert),
            "n_passing_pinned": sum(c["passes_pinned_0p0558"] for c in cert),
            "rows": cert,
        }
    del streams
    return block


def main() -> None:
    n_null = int(sys.argv[1]) if len(sys.argv) > 1 else N_NULL_DEFAULT
    reg = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    pinned = float(reg["registry"]["gate_pass_threshold"])
    f_floor = float(reg["registry"]["f_floor"])

    test_dur = TEST_BAND_NS[1] - TEST_BAND_NS[0]
    proxy_dur = SEG_PROXY[1] - SEG_PROXY[0]
    assert abs(proxy_dur - test_dur) < 86_400 * 1_000_000_000, "proxy duration off by >1d"
    assert SEG_PROXY[1] <= TEST_BAND_NS[0], "SEG_PROXY must end at/before TEST start"

    out: dict[str, Any] = {
        "analysis": "INFR-006 A2 — gate_pass_threshold binding-ness at live scale",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "governance": {
            "run_final_gate_called": False,
            "test_band_read": False,
            "holdout_read": False,
            "note": ("Gate statistic RECONSTRUCTED from the library functions used by "
                     "final_gate.walk_forward_block(config_gross); no counted ledger "
                     "slot spent. All computation on TRAIN."),
        },
        "reconstruction": {
            "source": "python/src/xen/xena/final_gate.py L211-224 (gross block)",
            "charge_costs": False, "oracle_seed": ORACLE_SEED, "boot_seed": BOOT_SEED,
            "block_bars": PARAMS.block_bars,
            "n_boot_effective": max(PARAMS.n_boot, 200),
            "initial_equity": CONFIG_GROSS.initial_equity,
            "statistic": "np.quantile(bootstrap_F(...), 0.25)",
        },
        "bands": {
            "seg_proxy_ns": list(SEG_PROXY),
            "seg_proxy_utc": ["2023-07-13T00:00:00Z", "2024-03-28T00:00:00Z"],
            "seg_proxy_duration_days": proxy_dur / 86_400e9,
            "test_band_utc_NOT_READ": ["2024-03-28T00:00:00Z", "2024-12-11T08:19:00Z"],
            "test_band_duration_days": test_dur / 86_400e9,
            "duration_delta_hours": (proxy_dur - test_dur) / 3_600e9,
        },
        "registry": {"path": str(REGISTRY_PATH.relative_to(REPO)),
                     "sha256": reg.get("sha256"),
                     "gate_pass_threshold": pinned, "f_floor": f_floor,
                     "gate_rule": reg["registry"]["battery_summary"]["gate_rule"],
                     "calibration_scale": ("300 null universes x 24 candidates, budget "
                                           "400, short synthetic bands, F_hat median "
                                           "~0.19")},
        "n_null_subsets": n_null,
        "universes": {},
    }

    for universe in ("XENA-001", "XENA-002", "XENA-003"):
        out["universes"][universe] = run_universe(universe, n_null, pinned)

    null = out["universes"]["XENA-001"]["random_subsets"]["summary"]
    out["headline"] = {
        "null_universe": "XENA-001 (RANDOM-entry, no-edge null on real prices)",
        "pinned_gate_pass_threshold": pinned,
        "live_scale_rederived_threshold": null["rederived_threshold_p95_rule"],
        "ratio_rederived_over_pinned": (null["rederived_threshold_p95_rule"] / pinned
                                        if pinned else float("inf")),
        "null_pass_rate_at_pinned_threshold": null["frac_ge_pinned_threshold"],
        "target_fpr": 0.05,
        "gate_binding_at_live_scale": bool(null["frac_ge_pinned_threshold"] <= 0.05),
    }
    OUT_PATH.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out["headline"], indent=1))
    print(f"\nwritten -> {OUT_PATH}")


if __name__ == "__main__":
    main()
