"""XENA-EPSOSC-002 analyst canonical reads (Phase 2). Analyst-owned, xen-only.

Verdict-bearing gross bps/episode from the canonical adjudication-shim emission
(cis_trades RealizedBps = xen.adjudication episode gross; reconciliation validated by
the estimand gate). Independent of the developer's search/certify code. Block-bootstrap
CI + block sensitivity + trimmed mean (INFR-004 / L-20).
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path("/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen")
sys.path.insert(0, str(ROOT / "python/src"))
from xen.evaluation import block_bootstrap_ci, block_sensitivity  # noqa: E402

RUNS = ROOT / "data/nautilus_runs/XENA-EPSOSC-002"
PKG = json.loads((ROOT / "python/experiments/XENA-EPSOSC-002/results/search_certify_package.json").read_text())
GATE_LO, GATE_HI = int(PKG["segments"]["gate"][0]), int(PKG["segments"]["gate"][1])
CERTIFIED = PKG["stage2_gate_band"]["top"]
OUT = ROOT / "python/experiments/XENA-EPSOSC-002/results/analyst_canonical_reads.json"


def gate_legs(cell: str) -> pl.DataFrame:
    d = RUNS / cell
    cis = pl.read_parquet(d / "xena" / "cis_trades.parquet").with_columns(
        pl.col("EntryTime").cast(pl.Int64).alias("entry_ns"))
    return cis.filter(
        pl.col("RealizedBps").is_finite()
        & (~pl.col("Censored").cast(pl.Boolean))
        & (pl.col("entry_ns") >= GATE_LO) & (pl.col("entry_ns") < GATE_HI))


def ci_block(x: np.ndarray) -> dict:
    bb = block_bootstrap_ci(x, block=64, n_boot=200, n_seeds=5)
    tm = block_bootstrap_ci(x, stat=lambda a: float(np.mean(np.sort(a)[int(0.1*len(a)):len(a)-int(0.1*len(a))] if len(a) >= 10 else a)),
                            block=64, n_boot=200, n_seeds=5)
    sens = block_sensitivity(x, [32, 64, 128], n_boot=200, n_seeds=5)
    return {
        "n": int(x.size), "mean": float(np.mean(x)), "median": float(np.median(x)),
        "ci95_block64": bb["ci"], "ci_low_seed_range": bb["ci_low_seed_range"],
        "trimmed10_mean_ci95": tm["ci"],
        "block_sensitivity_ci_low": {str(r["block_req"]): r["ci"][0] for r in sens},
        "ci_excludes_zero": bool(bb["ci"][0] > 0 or bb["ci"][1] < 0),
        "sign_ci_low_stable_across_blocks": len({np.sign(r["ci"][0]) for r in sens}) == 1,
    }


def main():
    per_cell, per_sym, pooled = {}, {}, []
    for cell in CERTIFIED:
        df = gate_legs(cell)
        x = df["RealizedBps"].to_numpy()
        per_cell[cell] = ci_block(x) if x.size else {"n": 0}
        sym = cell.split("__")[0]
        per_sym.setdefault(sym, []).append(x)
        pooled.append(x)
    pooled = np.concatenate(pooled)
    per_sym_ci = {s: ci_block(np.concatenate(v)) for s, v in per_sym.items()}
    out = {
        "universe_id": "XENA-EPSOSC-002",
        "certified_subset": CERTIFIED,
        "gate_band_ns": [GATE_LO, GATE_HI],
        "estimand": "canonical episode gross bps (adjudication-shim RealizedBps); recon validated by estimand gate",
        "pooled_equal_weight_leg": ci_block(pooled),
        "per_symbol": per_sym_ci,
        "per_cell": per_cell,
    }
    OUT.write_text(json.dumps(out, indent=2))
    p = out["pooled_equal_weight_leg"]
    print(f"POOLED certified gate-band: n={p['n']} mean={p['mean']:.1f} median={p['median']:.1f} "
          f"CI95={[round(c,1) for c in p['ci95_block64']]} excludes0={p['ci_excludes_zero']}")
    print("per-symbol mean [CI95_low]:")
    for s, v in per_sym_ci.items():
        print(f"  {s:16s} n={v['n']:3d} mean={v['mean']:8.1f} CI95={[round(c,1) for c in v['ci95_block64']]}")
    print("written", OUT)


if __name__ == "__main__":
    main()
