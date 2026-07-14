"""XENA-003 cost-sensitivity + magnitude decomposition on the certified finalists.

Canonical estimands only: xen.xena.oracle.evaluate (portfolio accounting) + the search
module's grid/bootstrap machinery (same F̂ definition the search used). No local accounting.

For each of the 12 certified finalist subsets, on the SEARCH band:
  * gross F_point (log-wealth) + F̂ (bootstrap P25) — reproduce the search claim
  * net F_point/F̂ at a sweep of round-trip spread assumptions (added to the design §4
    commission pins) → breakeven cost
  * ledger decomposition: n admitted, n rejected (R_max), notional/leverage, per-trade
    gross money, gross bps of notional

Outputs: results_analyst/cost_sweep.json
"""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import polars as pl
from tqdm import tqdm

from xen.xena.ingest import load_candidate
from xen.xena.oracle import CandidateStream, OracleConfig, evaluate
from xen.xena.search import (SearchParams, bootstrap_F, bootstrap_block_starts,
                             clip_grid_covering, grid_increments, universe_grid)

ROOT = Path(__file__).resolve().parents[4]
RUNS = ROOT / "data" / "strategy_runs" / "XENA-003"
RES = ROOT / "python" / "experiments" / "XENA-003" / "results"
OUT = ROOT / "python" / "experiments" / "XENA-003" / "results_analyst"

SEARCH_NS = (1622592060000000000, 1678233600000000000)  # design §5 pre-registered
SPREAD_SWEEP = [0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0]
PARAMS = SearchParams()


def load_streams(cids: set[str]) -> list[CandidateStream]:
    man = json.loads((RUNS / "universe_manifest.json").read_text())
    out = []
    for rec in tqdm([c for c in man["candidates"] if c["candidate_id"] in cids],
                    desc="load"):
        out.append(load_candidate(RUNS / rec["run_dir"], candidate_id=rec["candidate_id"],
                                  symbol=rec["symbol"], cost_bps=rec["cost_bps"],
                                  money_per_unit=rec["money_per_unit"]))
    return out


def bumped(streams: list[CandidateStream], spread_bps: float) -> list[CandidateStream]:
    return [replace(s, cost_bps=s.cost_bps + spread_bps) for s in streams]


def eval_subset(subset: set[str], streams: list[CandidateStream], grid: np.ndarray,
                starts: np.ndarray, *, charge: bool) -> dict:
    cfg = OracleConfig(charge_costs=charge)
    res = evaluate(subset, streams, cfg, segment=SEARCH_NS)
    inc = grid_increments(res, grid)
    boot = bootstrap_F(inc, starts, block=PARAMS.block_bars,
                       initial_equity=cfg.initial_equity)
    led = res.ledger
    notional = (led.get_column("Units") * led.get_column("EntryPrice")).to_numpy()
    mpu = {s.candidate_id: s.money_per_unit for s in streams}
    notional = notional * np.array([mpu[c] for c in led.get_column("CandidateId")])
    gross = led.get_column("GrossMoney").to_numpy()
    cost = led.get_column("CostMoney").to_numpy()
    return {
        "F_point": res.F_point,
        "F_hat_p25": float(np.quantile(boot, PARAMS.quantile)),
        "F_boot_median": float(np.median(boot)),
        "n_admitted": res.n_admitted, "n_rejected": res.n_rejected,
        "final_equity": float(res.equity[-1]),
        "gross_money_total": float(gross.sum()), "cost_money_total": float(cost.sum()),
        "notional_weighted_gross_bps": float(gross.sum() / notional.sum() * 1e4),
        "notional_weighted_cost_bps": float(cost.sum() / notional.sum() * 1e4),
        "mean_leverage_at_entry": float(np.mean(notional / (led.get_column("Risk")
                                                            .to_numpy() / 0.005))),
        "median_notional_per_risk": float(np.median(
            notional / led.get_column("Risk").to_numpy())),
    }


def main() -> None:
    cert = json.loads((RES / "certification.json").read_text())
    subsets = [set(r["subset"]) for r in cert["ranked"]]
    union = set().union(*subsets)
    print(f"{len(subsets)} finalists, union {len(union)} candidates")
    streams = load_streams(union)
    grid = clip_grid_covering(universe_grid(streams), SEARCH_NS, streams)
    starts = bootstrap_block_starts(len(grid), block=PARAMS.block_bars,
                                    n_boot=PARAMS.n_boot, seed=1_000_003 * 0 + 17)
    OUT.mkdir(parents=True, exist_ok=True)

    rows = []
    for i, sub in enumerate(tqdm(subsets, desc="subsets")):
        r = {"rank": i, "size": len(sub),
             "search_F_hat_reported": cert["ranked"][i]["search_F_hat"],
             "sweep": {}}
        r["gross"] = eval_subset(sub, streams, grid, starts, charge=False)
        for sp in SPREAD_SWEEP:
            st = bumped(streams, sp)
            r["sweep"][str(sp)] = eval_subset(sub, st, grid, starts, charge=True)
        rows.append(r)

    # composition read: how many finalist members are 1H5M / H05X / V00
    comp = {}
    for i, sub in enumerate(subsets):
        comp[i] = {
            "n_1H5M": sum("-1H5M-" in c for c in sub),
            "n_4H15M": sum("-4H15M-" in c for c in sub),
            "n_1D1H": sum("-1D1H-" in c for c in sub),
            "n_H05X": sum("-H05X-" in c for c in sub),
            "n_V00": sum(c.endswith("-V00") for c in sub),
        }
    (OUT / "cost_sweep.json").write_text(json.dumps(
        {"grid_bars": len(grid), "spread_sweep": SPREAD_SWEEP, "subsets": rows,
         "composition": comp}, indent=1))
    for r in rows:
        g = r["gross"]
        line = (f"rank{r['rank']:2d} n={r['size']:2d} Fpt={g['F_point']:6.2f} "
                f"F25={g['F_hat_p25']:6.2f} adm={g['n_admitted']:6d} "
                f"rej={g['n_rejected']:6d} wgross={g['notional_weighted_gross_bps']:6.3f}bps"
                " | net F25: " + " ".join(
                    f"{sp}={r['sweep'][str(sp)]['F_hat_p25']:.2f}" for sp in SPREAD_SWEEP))
        print(line)


if __name__ == "__main__":
    main()
