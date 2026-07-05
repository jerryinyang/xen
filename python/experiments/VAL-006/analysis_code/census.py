"""VAL-006 Phase 2 — corrected multi-leg census from canonical per-leg/episode estimands.

Per (root, instrument) cell, computed ONLY via xen.adjudication (never experiment-local code):
  per-leg net (frozen 4h cost), episode table, moving-block bootstrap CIs over episodes,
  exposure stats, physicality. Both-leg (bllim/blmkt) ledgers mix mate symbols, so per-bar
  path stats (MAE/drawdown/occupancy) are marked invalid there; totals still telescope
  exactly to per-leg fills.

Outputs: results/census.parquet + results/census_summary.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import polars as pl
from tqdm.auto import tqdm

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "python" / "src"))

from xen.adjudication import assemble_multileg_bps, build_episodes, per_leg_net  # noqa: E402
from xen.referee_adaptive import adaptive_cost_bps_for  # noqa: E402

DATA = ROOT / "data" / "strategy_runs"
RESULTS = ROOT / "python" / "experiments" / "VAL-006" / "results"

SEED, N_BOOT, BLOCK, ALPHA = 20260704, 10_000, 5, 0.05

ROOTS = [  # (root, exit, arm, z, shift)
    ("EXP-014b-4h-s8-allow-z15", "e0", "allow", "z15", False),
    ("EXP-014b-4h-s8-allow-z20", "e0", "allow", "z20", False),
    ("EXP-014b-4h-s8-extend-z15", "e0", "extend", "z15", False),
    ("EXP-014b-4h-s8-extend-z20", "e0", "extend", "z20", False),
    ("EXP-014b-4h-s8-extend-z15-shift", "e0", "extend", "z15", True),
    ("EXP-014b-4h-s8-extend-z20-shift", "e0", "extend", "z20", True),
    ("EXP-014b-4h-s8-bllim-z15", "e0", "bllim", "z15", False),
    ("EXP-014b-4h-s8-bllim-z20", "e0", "bllim", "z20", False),
    ("EXP-014b-4h-s8-blmkt-z15", "e0", "blmkt", "z15", False),
    ("EXP-014b-4h-s8-blmkt-z20", "e0", "blmkt", "z20", False),
    ("EXP-014c-4h-s8-e1-allow-z15", "e1", "allow", "z15", False),
    ("EXP-014c-4h-s8-e1-allow-z20", "e1", "allow", "z20", False),
    ("EXP-014c-4h-s8-e1-extend-z15", "e1", "extend", "z15", False),
    ("EXP-014c-4h-s8-e1-extend-z20", "e1", "extend", "z20", False),
    ("EXP-014c-4h-s8-e2-allow-z15", "e2", "allow", "z15", False),
    ("EXP-014c-4h-s8-e2-extend-z15", "e2", "extend", "z15", False),
    ("EXP-014c-4h-s8-e2-extend-z15-shift", "e2", "extend", "z15", True),
    ("EXP-014c-4h-s8-e2-extend-z20", "e2", "extend", "z20", False),
    ("EXP-014c-4h-s8-e3-allow-z15", "e3", "allow", "z15", False),
    ("EXP-014c-4h-s8-e3-allow-z20", "e3", "allow", "z20", False),
    ("EXP-014c-4h-s8-e3-extend-z15", "e3", "extend", "z15", False),
    ("EXP-014c-4h-s8-e3-extend-z15-shift", "e3", "extend", "z15", True),
    ("EXP-014c-4h-s8-e3-extend-z20", "e3", "extend", "z20", False),
]
BOTH_LEG_ARMS = ("bllim", "blmkt")


def block_boot_mean_ci(x: np.ndarray, seed: int = SEED) -> tuple[float, float, float]:
    """(mean, lo, hi): moving-block bootstrap over time-ordered values (block=BLOCK)."""
    n = len(x)
    if n == 0:
        return (float("nan"),) * 3
    if n == 1:
        return float(x[0]), float(x[0]), float(x[0])
    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(n / BLOCK))
    starts = rng.integers(0, max(n - BLOCK, 1), size=(N_BOOT, n_blocks))
    means = np.empty(N_BOOT)
    for b in range(N_BOOT):
        idx = (starts[b][:, None] + np.arange(BLOCK)[None, :]).ravel()[:n] % n
        means[b] = x[idx].mean()
    return (float(x.mean()), float(np.quantile(means, ALPHA / 2)),
            float(np.quantile(means, 1 - ALPHA / 2)))


def census_cell(root_name: str, exit_: str, arm: str, z: str, shift: bool,
                run_dir: Path) -> dict:
    inst = run_dir.name.split("_")[4].upper() if False else None  # (metadata is canonical)
    meta = json.loads((run_dir / "run_metadata.json").read_text())
    inst = meta["symbol"]
    cost = adaptive_cost_bps_for(inst, "4h")
    pos = pl.read_parquet(run_dir / "positions.parquet")
    cis = pl.read_parquet(run_dir / "cis_trades.parquet")

    series = assemble_multileg_bps(pos, cis, cost_bps=cost)
    eps = build_episodes(pos, cis, cost_bps=cost)
    live = cis.filter(pl.col("RealizedBps").is_finite()
                      & pl.col("Censored").cast(pl.Boolean).not_())
    legs = per_leg_net(live, cost_bps=cost)
    leg_net = legs.get_column("NetBps").to_numpy()
    # legs ordered by exit attribution time — block-bootstrap over that order
    leg_ci = block_boot_mean_ci(leg_net)
    comp = eps.filter(~pl.col("censored")) if eps.height else eps
    epi_net = comp.get_column("net_bps").to_numpy() if comp.height else np.array([])
    epi_ci = block_boot_mean_ci(epi_net)

    path_valid = arm not in BOTH_LEG_ARMS
    t = series.times.astype("datetime64[s]").astype("int64")
    years = max(float(t[-1] - t[0]) / (365.25 * 24 * 3600), 1e-9)
    net = series.net_bps
    active = series.open_legs > 0
    cum = np.cumsum(net)
    row = {
        "root": root_name, "exit": exit_, "arm": arm, "z": z, "shift": shift,
        "instrument": inst, "cost_bps": cost,
        "n_legs": int(legs.height), "n_aborted": int(series.n_aborted),
        "n_censored": int(series.n_censored),
        "total_net_bps": float(leg_net.sum()),
        "leg_net_mean": leg_ci[0], "leg_net_lo": leg_ci[1], "leg_net_hi": leg_ci[2],
        "leg_net_median": float(np.median(leg_net)) if len(leg_net) else float("nan"),
        "n_episodes": int(comp.height),
        "epi_net_mean": epi_ci[0], "epi_net_lo": epi_ci[1], "epi_net_hi": epi_ci[2],
        "epi_bars_mean": float(comp.get_column("n_bars").mean()) if comp.height else float("nan"),
        "epi_legs_mean": float(comp.get_column("n_legs").mean()) if comp.height else float("nan"),
        "max_open_legs": int(series.open_legs.max()),
        "path_valid": path_valid,
        "occupancy": float(active.mean()) if path_valid else float("nan"),
        "net_per_active_bar": float(net[active].mean()) if path_valid and active.any()
        else float("nan"),
        "ann_return_pct": float(net.sum() / 1e4 / years * 100) if path_valid else float("nan"),
        "max_dd_bps": float((cum - np.maximum.accumulate(cum)).min()) if path_valid
        else float("nan"),
        "worst_epi_mae_bps": float(comp.get_column("mae_bps").min())
        if path_valid and comp.height else float("nan"),
        "years": years,
    }
    return row


def main() -> None:
    rows = []
    for root_name, exit_, arm, z, shift in tqdm(ROOTS, desc="roots"):
        root = DATA / root_name
        for rd in sorted(d for d in root.iterdir()
                         if d.is_dir() and (d / "positions.parquet").exists()):
            rows.append(census_cell(root_name, exit_, arm, z, shift, rd))
    df = pl.DataFrame(rows)
    RESULTS.mkdir(parents=True, exist_ok=True)
    df.write_parquet(RESULTS / "census.parquet")

    raw = df.filter(~pl.col("shift"))
    summary = {
        "n_cells": raw.height,
        "cells_leg_ci_positive": raw.filter(pl.col("leg_net_lo") > 0).height,
        "cells_epi_ci_positive": raw.filter(pl.col("epi_net_lo") > 0).height,
        "cells_leg_ci_negative": raw.filter(pl.col("leg_net_hi") < 0).height,
        "cells_total_net_negative": raw.filter(pl.col("total_net_bps") < 0).height,
    }
    (RESULTS / "census_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    pos_cells = raw.filter(pl.col("leg_net_lo") > 0).sort("leg_net_mean", descending=True)
    print("\nCELLS WITH per-leg net CI_low > 0 (corrected estimand):")
    print(pos_cells.select(["exit", "arm", "z", "instrument", "n_legs", "leg_net_mean",
                            "leg_net_lo", "leg_net_hi", "total_net_bps", "n_episodes",
                            "epi_net_mean", "epi_net_lo"]))


if __name__ == "__main__":
    main()
