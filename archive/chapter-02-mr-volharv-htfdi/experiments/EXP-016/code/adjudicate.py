"""
EXP-016 — CF-MR-005 one-shot TEST persistence read (ANALYSIS-ONLY on EXP-016 emissions).

Frozen per design.md §4 BEFORE result contact:
  TEST band = train_fence < SourceCloseTime <= test_fence (20230103-era row cutoffs).
  Binding: frozen 4h referee on the TEST-band per-bar NET per cell; Holm over 3 cells; bite.
  Carryover legs (entered pre-band) contribute MTM without entry cost (count disclosed).
  Shift twins: disclosure collapse fractions only (W3/L-15), not a binary gate.
  TRAIN-band figures = reproduction check vs EXP-014c (must match closely).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "python" / "src"))
sys.path.insert(0, str(ROOT / "python" / "experiments" / "EXP-014c" / "code"))

import lib as lib14c                                                    # noqa: E402
from xen.referee_pstar import gate_stack_pstar                          # noqa: E402
from xen.referee_adaptive import adaptive_row, adaptive_cost_bps_for    # noqa: E402
from xen.signals.ingestion import load_emitted_run, assert_run_within_holdout  # noqa: E402

RESULTS = ROOT / "python" / "experiments" / "EXP-016" / "results"
DATA = ROOT / "data" / "strategy_runs"
CELLS = ("AUDUSD", "NZDUSD", "US2000")
TRAIN_FENCE = {"AUDUSD": "2024-09-06T14:40:00", "NZDUSD": "2024-09-06T05:42:00",
               "US2000": "2024-09-10T09:33:00"}
TEST_FENCE = {"AUDUSD": "2025-05-29T14:08:00", "NZDUSD": "2025-05-29T05:14:00",
              "US2000": "2025-06-02T07:30:00"}
SEED, NBOOT, ALPHA, PLANT = 20260703, 10_000, 0.05, 8.0
TRAIN_REF = {"AUDUSD": (3.98, 1.06), "NZDUSD": (4.00, 1.53), "US2000": (10.90, 3.17)}  # 014c


def load(inst: str, shift: bool) -> tuple[pl.DataFrame, pl.DataFrame]:
    root = DATA / ("EXP-016-4h-s8-e3-extend-z15" + ("-shift" if shift else ""))
    rd = sorted(root.glob(f"cross_instrument_spread_mr_{inst.lower()}_4h_*"))[-1]
    run = load_emitted_run(rd)
    assert_run_within_holdout(run.positions, run.metadata.get("analysis_end_utc"))
    cis_p = rd / "cis_trades.parquet"
    cis = pl.read_parquet(cis_p) if cis_p.exists() else pl.DataFrame()
    return run.positions.sort("SourceCloseTime"), cis


def band_series(pos: pl.DataFrame, cis: pl.DataFrame, inst: str, lo: str | None, hi: str,
                cost: float) -> dict:
    """Per-bar NET on bars in (lo, hi]; entry cost only for entries inside the band."""
    lo_dt = datetime.fromisoformat(lo) if lo else None
    hi_dt = datetime.fromisoformat(hi)
    df = pos.filter(pl.col("SourceCloseTime") <= hi_dt)
    ret, p, net = lib14c.assemble_realized_bps(df, cost_bps=cost)
    sct = df.get_column("SourceCloseTime").to_numpy()[:-1]        # aligns with series
    mask = np.ones(len(net), dtype=bool) if lo_dt is None else (sct > np.datetime64(lo_dt))
    core = gate_stack_pstar(ret[mask], p[mask], net[mask], domain="4h", cost_bps=cost,
                            n_bootstrap=NBOOT, seed=SEED)
    row = adaptive_row(core, alpha=ALPHA)
    active = p[mask] != 0.0
    planted = net[mask] + PLANT * active.astype(float)
    bite = bool(adaptive_row(gate_stack_pstar(ret[mask], p[mask], planted, domain="4h",
                                              cost_bps=cost, n_bootstrap=NBOOT, seed=SEED),
                             alpha=ALPHA)["passed"]) \
        if active.sum() >= lib14c.min_state() else None
    n_epi = int(core.get("n_episodes", 0))
    nz = net[mask][net[mask] != 0.0]
    band_trades = 0
    carry = 0
    if cis.height:
        ent = cis.get_column("EntryTime")
        band_trades = int(cis.filter((ent > lo_dt) & (ent <= hi_dt)).height) if lo_dt \
            else int(cis.filter(ent <= hi_dt).height)
        if lo_dt is not None:
            open_at_lo = cis.filter((pl.col("EntryTime") <= lo_dt)
                                    & ((pl.col("ExitTime") > lo_dt) | (pl.col("Censored") == 1)))
            carry = int(open_at_lo.height)
    neutral = np.asarray(core.get("neutral_means", []), dtype=float)
    boot_p = float(np.mean(neutral <= 0.0)) if neutral.size else float("nan")
    return {"n_bars": int(mask.sum()), "n_trades": band_trades, "carryover_legs": carry,
            "net_mean_bps": float(np.mean(nz)) if nz.size else 0.0,
            "ci_low": float(row["ci_lower_bps"]), "effect_bps": float(row["effect_bps"]),
            "passed": bool(row["passed"]), "n_episodes": n_epi, "boot_p": boot_p,
            "bite": bite, "powered": bool(core["l1"] and n_epi >= lib14c.min_state())}


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    out: dict = {"experiment": "EXP-016", "family": "CF-MR-005",
                 "variant": "e3/extend/z15", "cells": {}}
    pvals: dict[str, float] = {}
    for inst in CELLS:
        cost = adaptive_cost_bps_for(inst, "4h")
        pos, cis = load(inst, shift=False)
        train = band_series(pos, cis, inst, None, TRAIN_FENCE[inst], cost)
        test = band_series(pos, cis, inst, TRAIN_FENCE[inst], TEST_FENCE[inst], cost)
        spos, scis = load(inst, shift=True)
        stest = band_series(spos, scis, inst, TRAIN_FENCE[inst], TEST_FENCE[inst], cost)
        collapse = (stest["net_mean_bps"] / test["net_mean_bps"]
                    if abs(test["net_mean_bps"]) > 1e-9 else float("nan"))
        r014c = TRAIN_REF[inst]
        out["cells"][inst] = {
            "cost_bps": cost,
            "train_repro": {**train, "exp014c_net": r014c[0], "exp014c_ci_low": r014c[1]},
            "test": test,
            "shift_test": stest,
            "collapse_fraction_test": float(collapse)}
        pvals[inst] = test["boot_p"]
        print(f"{inst}: TRAIN net {train['net_mean_bps']:.2f} (014c {r014c[0]:.2f}) | "
              f"TEST net {test['net_mean_bps']:.2f} ci_low {test['ci_low']:.2f} "
              f"passed={test['passed']} epi={test['n_episodes']} bite={test['bite']} | "
              f"shift TEST net {stest['net_mean_bps']:.2f} collapse={collapse:.2f}")
    holm = lib14c.holm(pvals)
    for inst in CELLS:
        c = out["cells"][inst]
        t = c["test"]
        c["holm_admit"] = bool(holm.get(inst, False) and t["passed"])
        if c["holm_admit"] and t["bite"] is True:
            c["verdict"] = "RETAINED"
        elif t["powered"] and t["bite"] is True and not t["passed"]:
            c["verdict"] = "NOT_RETAINED"
        else:
            c["verdict"] = "UNPOWERED"
    verdicts = [out["cells"][i]["verdict"] for i in CELLS]
    out["family_routing"] = ("RETIRE_IMMEDIATELY" if all(v == "NOT_RETAINED" for v in verdicts)
                             else "HARNESS_FORENSICS" if any(v == "RETAINED" for v in verdicts)
                             else "OPERATOR_ROUTING_MIXED")
    (RESULTS / "test_read.json").write_text(json.dumps(out, indent=2, default=str))
    print("verdicts:", dict(zip(CELLS, verdicts)), "->", out["family_routing"])


if __name__ == "__main__":
    main()
