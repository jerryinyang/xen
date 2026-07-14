"""XENA-003 controls: (a) precise cost breakeven, (b) entry-price-basis control
(the discriminator the permutation battery cannot supply), (c) Amendment-4 grid-seam audit.

(b) ARM-OPEN: identical trade streams (same entry TIMES, same exit fills, same
    StopDistance/sizing) with the entry price replaced by the LTF grid OPEN of the bar the
    fill occurred in — i.e. the passive-limit print premium is removed, the temporal
    alignment and forward price path are untouched. The permutation battery destroys BOTH
    (it re-times AND re-prices from grid opens); ARM-OPEN destroys only the price basis, so
    live vs ARM-OPEN vs permuted separates "entry at an extreme print" from "entry at a
    predictive moment".
    ARM-NEXTOPEN: entry price = open of the NEXT LTF bar (the oracle's first mark) — the
    strictly-implementable market-order analogue.

Canonical accounting only (xen.xena.oracle / xen.xena.search). Streams are rebuilt from raw
emissions; no accounting primitive is redefined.

Outputs: results_analyst/controls.json
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

SEARCH_NS = (1622592060000000000, 1678233600000000000)
PARAMS = SearchParams()
N_ARM_RESTART_SEEDS = (0, 1, 2)


def load_streams(cids: set[str]) -> list[CandidateStream]:
    man = json.loads((RUNS / "universe_manifest.json").read_text())
    return [load_candidate(RUNS / r["run_dir"], candidate_id=r["candidate_id"],
                           symbol=r["symbol"], cost_bps=r["cost_bps"],
                           money_per_unit=r["money_per_unit"])
            for r in tqdm([c for c in man["candidates"] if c["candidate_id"] in cids],
                          desc="load")]


def reprice_entry(s: CandidateStream, *, offset: int) -> CandidateStream:
    """Entry price := grid open of (fill bar + offset). StopDistance kept (sizing isolated)."""
    mt = s.marks.get_column("CloseTime").to_numpy()
    mo = s.marks.get_column("Open").to_numpy()
    et = s.trades.get_column("EntryTime").to_numpy()
    i0 = np.minimum(np.searchsorted(mt, et, side="left") + offset, len(mt) - 1)
    tr = s.trades.with_columns(pl.Series("EntryPrice", mo[i0]))
    return replace(s, trades=tr)


def f_reads(subset: set[str], streams: list[CandidateStream], grid: np.ndarray,
            *, charge: bool = False) -> dict:
    cfg = OracleConfig(charge_costs=charge)
    res = evaluate(subset, streams, cfg, segment=SEARCH_NS)
    inc = grid_increments(res, grid)
    out = {"F_point": res.F_point, "n_admitted": res.n_admitted,
           "n_rejected": res.n_rejected}
    hats = []
    for sd in N_ARM_RESTART_SEEDS:
        starts = bootstrap_block_starts(len(grid), block=PARAMS.block_bars,
                                        n_boot=PARAMS.n_boot, seed=1_000_003 * sd + 17)
        boot = bootstrap_F(inc, starts, block=PARAMS.block_bars,
                           initial_equity=cfg.initial_equity)
        hats.append(float(np.quantile(boot, PARAMS.quantile)))
    out["F_hat_p25_seeds"] = hats
    out["F_hat_p25_median"] = float(np.median(hats))
    return out, inc


def breakeven(subset: set[str], streams: list[CandidateStream], grid: np.ndarray) -> float:
    """Additional round-trip spread (bps, on top of the pinned commissions) at which the
    subset's gross log-wealth F_point crosses zero. Bisection, 1e-3 bps resolution."""
    def f(sp: float) -> float:
        st = [replace(s, cost_bps=s.cost_bps + sp) for s in streams]
        return evaluate(subset, st, OracleConfig(charge_costs=True),
                        segment=SEARCH_NS).F_point
    lo, hi = 0.0, 4.0
    if f(lo) <= 0:
        return 0.0
    for _ in range(16):
        mid = 0.5 * (lo + hi)
        if f(mid) > 0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def main() -> None:
    cert = json.loads((RES / "certification.json").read_text())
    ranked = cert["ranked"]
    subsets = [set(r["subset"]) for r in ranked]
    union = set().union(*subsets)
    streams = load_streams(union)
    by_id = {s.candidate_id: s for s in streams}

    grid = clip_grid_covering(universe_grid(streams), SEARCH_NS, streams)
    interior = universe_grid(streams)
    interior = interior[(interior >= SEARCH_NS[0]) & (interior < SEARCH_NS[1])]
    seam = {"grid_bars": len(grid), "interior_bars": len(interior),
            "appended_terminal_bar": bool(len(grid) > len(interior)),
            "last_interior_close_ns": int(interior[-1]),
            "grid_last_ns": int(grid[-1]),
            "segment_end_ns": SEARCH_NS[1]}

    arms_open = [reprice_entry(s, offset=0) for s in streams]
    arms_next = [reprice_entry(s, offset=1) for s in streams]

    rows = []
    for i, sub in enumerate(tqdm(subsets, desc="arms")):
        live, inc_live = f_reads(sub, streams, grid)
        a_open, _ = f_reads(sub, arms_open, grid)
        a_next, _ = f_reads(sub, arms_next, grid)
        be = breakeven(sub, streams, grid)
        # seam: share of total money in the appended terminal bin
        tot = float(inc_live.sum())
        last_bin = float(inc_live[-1])
        rows.append({
            "rank": i, "size": len(sub),
            "live": live, "arm_open_entry": a_open, "arm_next_open_entry": a_next,
            "collapse_frac_arm_open": (live["F_point"] - a_open["F_point"])
            / live["F_point"],
            "breakeven_extra_spread_bps": be,
            "terminal_bin_money": last_bin, "total_money": tot,
            "terminal_bin_share": last_bin / tot if tot else float("nan"),
        })
        print(f"rank{i:2d} live F={live['F_point']:6.2f} "
              f"ARM-OPEN F={a_open['F_point']:7.2f} "
              f"ARM-NEXTOPEN F={a_next['F_point']:7.2f} "
              f"breakeven={be:.3f}bps terminal_bin_share={rows[-1]['terminal_bin_share']:.5f}")

    # seam: legs of the top subset with exit after the last interior close
    top = subsets[0]
    n_late_exit = n_late_entry = 0
    for cid in top:
        s = by_id[cid]
        t = s.trades
        et = t.get_column("EntryTime").to_numpy()
        xt = t.get_column("ExitTime").to_numpy()
        insg = (et >= SEARCH_NS[0]) & (et < SEARCH_NS[1])
        n_late_entry += int(((et > interior[-1]) & insg).sum())
        n_late_exit += int(((xt > interior[-1]) & insg).sum())
    seam.update({"top_subset_entries_after_last_interior_close": n_late_entry,
                 "top_subset_legs_with_exit_after_last_interior_close": n_late_exit})

    (OUT / "controls.json").write_text(json.dumps(
        {"seam": seam, "subsets": rows}, indent=1))
    print(json.dumps(seam, indent=1))


if __name__ == "__main__":
    main()
