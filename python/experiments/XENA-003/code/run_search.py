"""XENA-003 LAHC search execution (lane machinery, design.md §5/§6).

Not analysis code: this drives the canonical ``xen.xena.search`` on the gated
universe. Selection is COST-FREE (gross amendment A-1: ``charge_costs=False``);
all search parameters come from the frozen-registry ``SearchParams()`` defaults.

Band (design §5, binding table): search = 2021-06-02T00:01Z -> 2023-03-08T00:00Z.

Memory note: ``load_universe`` would duplicate each feed's mark grid 76x
(~350M rows). The loader here reads each feed's grid ONCE and shares the
polars frame across that feed's 76 ``CandidateStream``s (read-only), matching
``load_candidate`` semantics exactly. The blocking gate has already passed
against the real per-candidate dirs (xena_candidate_gate.json, 2736/2736).

Usage:
    python run_search.py smoke   # timing + budget-flattening probe (restarts 100-102)
    python run_search.py full    # 12 restarts, ids 0-11, pinned budget
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from xen.xena.ingest import REQUIRED_CIS_COLS, REQUIRED_POS_COLS  # noqa: E402
from xen.xena.oracle import CandidateStream, OracleConfig  # noqa: E402
from xen.xena.search import run_restart  # noqa: E402

ROOT = Path(__file__).resolve().parents[4]
UNIVERSE = ROOT / "data" / "strategy_runs" / "XENA-003"
RESULTS = ROOT / "python" / "experiments" / "XENA-003" / "results"

SEARCH_START_NS = int(datetime(2021, 6, 2, 0, 1, tzinfo=timezone.utc).timestamp() * 1e9)
SEARCH_END_NS = int(datetime(2023, 3, 8, 0, 0, tzinfo=timezone.utc).timestamp() * 1e9)
SEARCH_BAND = (SEARCH_START_NS, SEARCH_END_NS)


def _to_ns(col: pl.Expr) -> pl.Expr:
    return col.dt.cast_time_unit("ns").cast(pl.Int64)


def load_streams() -> list[CandidateStream]:
    manifest = json.loads((UNIVERSE / "universe_manifest.json").read_text())
    gate = json.loads((UNIVERSE / "xena_candidate_gate.json").read_text())
    if not gate.get("blocking_pass"):
        raise RuntimeError("universe gate not passing")
    by_feed: dict[str, pl.DataFrame] = {}
    streams: list[CandidateStream] = []
    for c in manifest["candidates"]:
        run_dir = UNIVERSE / c["run_dir"]
        feed_key = "-".join(c["run_dir"].split("-")[1:3])  # sym-dompair
        if feed_key not in by_feed:
            pos = pl.read_parquet(run_dir / "positions.parquet",
                                  columns=list(REQUIRED_POS_COLS))
            by_feed[feed_key] = (pos.sort("SourceCloseTime")
                                 .select(_to_ns(pl.col("SourceCloseTime")).alias("CloseTime"),
                                         pl.col("RealOpen").cast(pl.Float64).alias("Open")))
        cis = pl.read_parquet(run_dir / "cis_trades.parquet",
                              columns=[col for col in REQUIRED_CIS_COLS])
        trades = (cis.sort("EntryTime")
                  .select(_to_ns(pl.col("EntryTime")).alias("EntryTime"),
                          _to_ns(pl.col("ExitTime")).alias("ExitTime"),
                          pl.col("Direction").cast(pl.Float64),
                          pl.col("EntryFillPrice").cast(pl.Float64).alias("EntryPrice"),
                          pl.col("ExitFillPrice").cast(pl.Float64).alias("ExitPrice"),
                          (pl.col("EntryFillPrice") - pl.col("SlPrice")).abs()
                          .cast(pl.Float64).alias("StopDistance"),
                          pl.col("Censored").cast(pl.Boolean)))
        streams.append(CandidateStream(c["candidate_id"], c["symbol"], trades,
                                       by_feed[feed_key], float(c["cost_bps"]),
                                       float(c.get("money_per_unit", 1.0))))
    return streams


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "smoke"
    t0 = time.time()
    streams = load_streams()
    print(f"loaded {len(streams)} streams in {time.time()-t0:.1f}s", flush=True)
    config = OracleConfig(charge_costs=False)  # A-1: gross selection
    RESULTS.mkdir(parents=True, exist_ok=True)

    if mode == "smoke-one":
        # One smoke restart in its own process (safe parallel axis: restarts are
        # deterministic-independent; within-restart LAHC stays sequential).
        from xen.xena.search import EvalCache
        rid = int(sys.argv[2])
        cache = EvalCache()
        rows = []
        for budget in (250, 500, 1000, 2000, 4000, 8000):
            t = time.time()
            r = run_restart(streams, config, budget=budget, restart_id=rid,
                            segment=SEARCH_BAND, cache=cache)
            rows.append({"restart_id": rid, "budget": budget,
                         "best_F_hat": r.best_F_hat, "n_iter": r.n_iterations,
                         "n_kicks": r.n_kicks, "acc": r.acceptance_rate,
                         "subset_size": len(r.best_subset),
                         "seconds": round(time.time() - t, 1)})
            print(rows[-1], flush=True)
        (RESULTS / f"search_smoke_budget_r{rid}.json").write_text(json.dumps(rows, indent=1))
    elif mode == "full-one":
        # One production restart in its own process.
        rid = int(sys.argv[2]); budget = int(sys.argv[3])
        t = time.time()
        r = run_restart(streams, config, budget=budget, restart_id=rid,
                        segment=SEARCH_BAND)
        out = {"restart_id": rid, "budget": budget, "best_F_hat": r.best_F_hat,
               "best_subset": sorted(r.best_subset),
               "n_iterations": r.n_iterations, "n_kicks": r.n_kicks,
               "acceptance_rate": r.acceptance_rate,
               "gate_rejection_rate": r.gate_rejection_rate,
               "n_evaluations": r.cache.evaluation_count,
               "distinct_subsets": len(r.cache.subsets()),
               "band_ns": SEARCH_BAND, "charge_costs": False,
               "seconds": round(time.time() - t, 1)}
        (RESULTS / f"search_restart_{rid:02d}.json").write_text(json.dumps(out, indent=1))
        print({k: out[k] for k in ("restart_id", "best_F_hat", "seconds", "n_iterations")},
              flush=True)
    elif mode == "smoke":
        from xen.xena.search import EvalCache
        rows = []
        for rid in (100, 101, 102):
            # One shared cache per restart: the walk prefix is budget-invariant, so
            # ascending budgets replay cached evaluations and only the tail is new.
            cache = EvalCache()
            for budget in (250, 500, 1000, 2000, 4000, 8000):
                t = time.time()
                r = run_restart(streams, config, budget=budget, restart_id=rid,
                                segment=SEARCH_BAND, cache=cache)
                rows.append({"restart_id": rid, "budget": budget,
                             "best_F_hat": r.best_F_hat, "n_iter": r.n_iterations,
                             "n_kicks": r.n_kicks, "acc": r.acceptance_rate,
                             "subset_size": len(r.best_subset),
                             "seconds": round(time.time() - t, 1)})
                print(rows[-1], flush=True)
        (RESULTS / "search_smoke_budget.json").write_text(json.dumps(rows, indent=1))
    elif mode == "full":
        budget = int(sys.argv[2])
        out = []
        for rid in range(12):
            t = time.time()
            r = run_restart(streams, config, budget=budget, restart_id=rid,
                            segment=SEARCH_BAND)
            out.append({"restart_id": rid, "budget": budget,
                        "best_F_hat": r.best_F_hat,
                        "best_subset": sorted(r.best_subset),
                        "n_iterations": r.n_iterations, "n_kicks": r.n_kicks,
                        "acceptance_rate": r.acceptance_rate,
                        "gate_rejection_rate": r.gate_rejection_rate,
                        "n_evaluations": r.cache.evaluation_count,
                        "distinct_subsets": len(r.cache.subsets()),
                        "seconds": round(time.time() - t, 1)})
            print({k: out[-1][k] for k in ("restart_id", "best_F_hat", "seconds",
                                           "n_iterations")}, flush=True)
        (RESULTS / "search_restarts.json").write_text(json.dumps(
            {"band_ns": SEARCH_BAND, "budget": budget, "charge_costs": False,
             "restarts": out}, indent=1))
    else:
        raise SystemExit(f"unknown mode {mode}")
    print(f"done in {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
