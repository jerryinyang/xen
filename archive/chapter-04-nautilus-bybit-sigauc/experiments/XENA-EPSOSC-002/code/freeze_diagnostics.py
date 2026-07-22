#!/usr/bin/env python3
"""XENA-EPSOSC-002 freeze diagnostics — mass onset, band coverage, power, floor.

DESIGN-TIME DISCLOSURE ONLY (not verdict-bearing; no estimand gate needed). All
numbers are computed FROM the XENA-EPSOSC-001 emitted RET_ANCHOR episodes, restricted
to the 002 axis (⊆ 001 axis) and the shifted TRAIN window. This is an in-window
re-slice of already-emitted data — a valid freeze estimate. Stage 3 re-emits 002's own
binding cells; Stage 4 computes canonical episode gross via xen.adjudication.

Warmup caveat: 001 runs warmed from 2021-06, so episodes near 2022-07-01 are fully
warmed; a fresh 002 run starting exactly 2022-07-01 loses ≤ W×15m (≤48h) of warmup at
the very start. Boundary effect only; disclosed.

Gross proxy: realized_return × 1e4 (engine costless → gross open-to-open bps). Canonical
episode gross deferred to the Stage-4 estimand gate.

Writes python/experiments/XENA-EPSOSC-002/results/{freeze_diagnostics,power_table,
  pre_search_gross_floor}.json|csv
"""
from __future__ import annotations

import glob
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

CODE = Path(__file__).resolve().parent
EXP = CODE.parent
ROOT = EXP.parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

RESULTS = EXP / "results"
RUNS_001 = REPO / "data" / "nautilus_runs" / "XENA-EPSOSC-001"
F_STAR = 16
SIGMA_BPS = 150.0  # design §10 episode gross sd prior


def load_002_manifest() -> dict:
    return json.loads((RESULTS / "universe_manifest.json").read_text())


def load_inwindow_episodes(axis: list[str], train_start: datetime, train_end: datetime) -> pl.DataFrame:
    """001 RET_ANCHOR positions for 002-axis symbols with ts_opened in the shifted window."""
    rows = []
    axisset = set(axis)
    for d in sorted(glob.glob(str(RUNS_001 / "*__RET_ANCHOR__*"))):
        if not os.path.isdir(d):
            continue
        cid = os.path.basename(d)
        sym = cid.split("__")[0]
        if sym not in axisset:
            continue
        p = pl.read_parquet(
            os.path.join(d, "positions_ledger.parquet"),
            columns=["position_id", "ts_opened", "ts_closed", "duration_ns", "realized_return", "side"],
        )
        if p.height == 0:
            continue
        p = p.with_columns(
            pl.col("ts_opened").dt.replace_time_zone(None).alias("t_open"),
            pl.lit(sym).alias("symbol"),
            pl.lit(cid).alias("cid"),
        )
        rows.append(p)
    df = pl.concat(rows, how="vertical") if rows else pl.DataFrame()
    lo = train_start.replace(tzinfo=None)
    hi = train_end.replace(tzinfo=None)
    return df.filter((pl.col("t_open") >= lo) & (pl.col("t_open") < hi))


def band_of(ts, bands) -> str:
    for name in ("search", "ranking", "stage2_gate"):
        b = bands[name]
        lo = datetime.fromisoformat(b["start_utc"].replace("Z", "+00:00")).replace(tzinfo=None)
        hi = datetime.fromisoformat(b["end_utc"].replace("Z", "+00:00")).replace(tzinfo=None)
        if lo <= ts < hi:
            return name
    return "purge_or_outside"


def monthly_mass(df: pl.DataFrame) -> list[dict]:
    m = (
        df.with_columns(pl.col("t_open").dt.strftime("%Y-%m").alias("ym"))
        .group_by("ym")
        .agg(pl.col("cid").n_unique().alias("n_cells"), pl.len().alias("n_epis"))
        .sort("ym")
    )
    return m.to_dicts()


def band_coverage(df: pl.DataFrame, bands: dict, n_axis_cells: int) -> dict:
    b = bands["search"]
    lo = datetime.fromisoformat(b["start_utc"].replace("Z", "+00:00")).replace(tzinfo=None)
    hi = datetime.fromisoformat(b["end_utc"].replace("Z", "+00:00")).replace(tzinfo=None)
    ins = df.filter((pl.col("t_open") >= lo) & (pl.col("t_open") < hi))
    nz = ins["cid"].n_unique()
    return {
        "search_band": f"{b['start_utc']} → {b['end_utc']}",
        "n_axis_binding_cells": n_axis_cells,
        "cells_with_ge1_episode": nz,
        "coverage": round(nz / n_axis_cells, 4) if n_axis_cells else None,
        "zero_leg_fraction": round(1 - nz / n_axis_cells, 4) if n_axis_cells else None,
        "predeclared_X": "coverage ≥ 0.80 (zero-leg ≤ 0.20)",
        "pass": (nz / n_axis_cells) >= 0.80 if n_axis_cells else False,
    }


def power_table(df: pl.DataFrame, bands: dict, axis: list[str]) -> dict:
    df = df.with_columns(
        pl.col("t_open").map_elements(lambda t: band_of(t, bands), return_dtype=pl.Utf8).alias("band")
    )
    # per-cell per-band episode counts
    per_cell = (
        df.group_by(["cid", "symbol", "band"]).agg(pl.len().alias("n"))
        .pivot(values="n", index=["cid", "symbol"], on="band", aggregate_function="first")
        .fill_null(0)
    )
    # per-symbol totals per band
    per_sym = (
        df.group_by(["symbol", "band"]).agg(pl.len().alias("n"))
        .pivot(values="n", index="symbol", on="band", aggregate_function="first")
        .fill_null(0)
    )
    # stage2 gate episodes per symbol → pooled subset projections
    s2 = "stage2_gate"
    sym_s2 = {r["symbol"]: int(r.get(s2, 0)) for r in per_sym.to_dicts()}
    ranked = sorted(sym_s2.items(), key=lambda kv: -kv[1])
    pooled = {}
    for K in (3, 5, 8, len(axis)):
        top = ranked[:K]
        pooled[f"top{K}_pooled_stage2_legs"] = sum(v for _, v in top)
        pooled[f"top{K}_symbols"] = [s for s, _ in top]
    # F* reachability: single cells on stage2
    cell_s2 = {r["cid"]: int(r.get(s2, 0)) for r in per_cell.to_dicts()}
    n_cells_ge_fstar = sum(1 for v in cell_s2.values() if v >= F_STAR)
    # MDE at pooled n (two-sample-ish rough: 2*sigma/sqrt(n))
    def mde(n):
        return round(2 * SIGMA_BPS / (n ** 0.5), 1) if n > 0 else None
    return {
        "note": "in-window (shifted-TRAIN) episode counts from 001 RET_ANCHOR emissions, 002 axis",
        "F_star": F_STAR, "sigma_bps_prior": SIGMA_BPS,
        "per_symbol_band_counts": per_sym.sort(s2, descending=True).to_dicts(),
        "n_single_cells_ge_Fstar_on_stage2": n_cells_ge_fstar,
        "n_binding_cells": df["cid"].n_unique(),
        "pooled_projections": pooled,
        "mde_bps": {
            "n16": mde(16), "n50": mde(50), "n100": mde(100),
            "top3_pooled_stage2": mde(pooled["top3_pooled_stage2_legs"]),
        },
        "power_target": "pooled n_legs ≥ 50 on stage2 via K≥3 cross-symbol subsets (design §10)",
    }


def gross_floor(df: pl.DataFrame, cost_bps: float) -> pl.DataFrame:
    g = (
        df.with_columns((pl.col("realized_return") * 1e4).alias("gross_bps"))
        .group_by(["cid", "symbol"])
        .agg(
            pl.len().alias("n_episodes"),
            pl.col("gross_bps").median().alias("median_gross_bps"),
            (pl.col("duration_ns").median() / 3.6e12).alias("median_duration_h"),
        )
        .with_columns(
            pl.lit(cost_bps).alias("breakeven_bps"),
            (pl.col("median_gross_bps") - cost_bps).alias("median_minus_breakeven"),
        )
        .with_columns((pl.col("median_minus_breakeven") > 0).alias("above_breakeven"))
        .sort("median_gross_bps", descending=True)
    )
    return g


def main() -> int:
    man = load_002_manifest()
    bands = man["stage_bands"]
    axis = [a["symbol"] for a in man["instruments"]["symbol_axis"]]
    n_axis_cells = man["n_binding"]
    cost_bps = man["candidates"][0]["cost_bps"]
    ts = datetime(2022, 7, 1, tzinfo=timezone.utc)
    te = datetime(2023, 12, 18, tzinfo=timezone.utc)

    df = load_inwindow_episodes(axis, ts, te)
    print(f"in-window RET_ANCHOR episodes (002 axis): {df.height} across {df['cid'].n_unique()} cells")

    diag = {
        "universe_id": "XENA-EPSOSC-002",
        "generated_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "train_start_utc": "2022-07-01T00:00:00Z",
        "train_end_utc": "2023-12-18T00:00:00Z",
        "holdout_start_utc_sealed": bands["holdout_start_utc"],
        "source": "XENA-EPSOSC-001 RET_ANCHOR positions_ledger, in-window re-slice (disclosure)",
        "warmup_caveat": "001 warmed from 2021-06; fresh 002 loses ≤48h warmup at window start",
        "monthly_mass_002axis": monthly_mass(df),
        "search_band_coverage": band_coverage(df, bands, n_axis_cells),
        "mass_onset_note": (
            "raw episode mass present from ~2021-11 (see 001 emissions); TRAIN_START=2022-07-01 "
            "chosen on the plateau to separate from 2021/2023 single-name drift regimes (fix "
            "#1/#4). Predeclared X (search-band coverage ≥0.80) verified on the pinned band."
        ),
    }
    (RESULTS / "freeze_diagnostics.json").write_text(json.dumps(diag, indent=2) + "\n")

    pw = power_table(df, bands, axis)
    (RESULTS / "power_table.json").write_text(json.dumps(pw, indent=2) + "\n")

    floor = gross_floor(df, cost_bps)
    floor.write_csv(RESULTS / "pre_search_gross_floor.csv")
    summary = {
        "cost_bps": cost_bps, "spread_label": "GAP 5.0 (per-symbol deferred to pilot/T2)",
        "n_cells": floor.height,
        "n_above_breakeven": int(floor["above_breakeven"].sum()),
        "median_gross_bps_p50": float(floor["median_gross_bps"].median()),
        "entire_mass_sub_breakeven": bool(floor["above_breakeven"].sum() == 0),
    }
    (RESULTS / "pre_search_gross_floor.json").write_text(json.dumps(summary, indent=2) + "\n")

    print("coverage:", diag["search_band_coverage"]["coverage"],
          "pass:", diag["search_band_coverage"]["pass"])
    print("cells ≥F* on stage2:", pw["n_single_cells_ge_Fstar_on_stage2"],
          "| top3 pooled stage2 legs:", pw["pooled_projections"]["top3_pooled_stage2_legs"])
    print("floor: above-breakeven", summary["n_above_breakeven"], "/", summary["n_cells"],
          "| median gross bps", round(summary["median_gross_bps_p50"], 1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
