"""SPDR-012 screen runner — TRAIN-only volatility characterisation (CF-VOLDIR-001 / HYP-A).

Executes the frozen design end to end:
universe recompute + pin assert -> per-cell causal feature/forecast build (25 symbols x
H1/H4/D1) -> 8 arms x DESIGN/CONFIRM -> V-XS cross-section -> controls + future-destroy
tripwire -> golden traces -> integrity self-check -> results/.

TRAIN only. The maximum timestamp any query may touch is ``train_end_utc``; TEST and the
global holdout are unreachable from this module.
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl
from tqdm import tqdm

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from arms import PRIMARY_MODEL_KEY, all_arm_rows, stability_rows  # noqa: E402
from config import (  # noqa: E402
    CLOCK_ORDER,
    CONFIRM_END,
    CONFIRM_START,
    DESIGN_END,
    DESIGN_START,
    DERANGE_SEEDS_FULL,
    DERANGE_SEEDS_MIN,
    HOLDOUT_START,
    DEVIATIONS,
    INTERPRETATION_NOTES,
    NS,
    PROHIBITED_CLAIMS,
    RESULTS_DIR,
    SHUFFLE_SEEDS,
    SPREAD_COST_DISCLOSURE,
    TEST_START,
    UNIT_PIN,
)
from controls import (  # noqa: E402
    bite_check,
    future_destroy_layer,
    target_derangement_control,
    time_shuffle_control,
)
from cross_section import xs_rows  # noqa: E402
from golden_traces import run_golden_traces  # noqa: E402
from pipeline import prepare_cell  # noqa: E402
from universe import assert_pin, recompute_universe  # noqa: E402
from xen.nautilus.catalog_fence import load_fence_manifest  # noqa: E402

EMIT_COLS = (
    "slot_start", "slot_end", "target_slot_start", "target_date",
    "open", "high", "low", "close",
    "r", "abs_r", "rv20", "ewma_vol", "parkinson", "gk",
    "rv20_mean_6", "rv20_mean_24",
    "oo_move", "target_abs_oo", "rv_next",
    "next_contiguous", "target_contiguous", "session", "dow",
    "regime_state", "hmm_state", "hmm_high_prob", "oos",
)


# ----------------------------------------------------------- per cell ----


def _control_block(cell, band: str, derange_seeds) -> dict:
    """Controls + tripwire on the V-LEVEL primary object for one band."""
    df = cell.design if band == "DESIGN" else cell.confirm
    pcol = f"pred__{PRIMARY_MODEL_KEY}"
    if df.height == 0 or pcol not in df.columns:
        return {"status": "NO_FORECAST"}
    d = df.filter(pl.col("oos")) if "oos" in df.columns else df
    pred = d[pcol].to_numpy()
    y = d["target_abs_oo"].to_numpy()
    dates = d["target_date"].to_numpy()
    m = np.isfinite(pred) & np.isfinite(y)
    if m.sum() < 30:
        return {"status": "UNPOWERED", "n_obs": int(m.sum())}
    pred, y, dates = pred[m], y[m], dates[m]

    shuffle = time_shuffle_control(pred, y, SHUFFLE_SEEDS)
    derangement = target_derangement_control(pred, y, dates, derange_seeds)
    global_derange = target_derangement_control(
        pred, y, dates, derange_seeds, unrestricted=True
    )
    return {
        "status": "OK",
        "metric": "V-LEVEL primary (ridge) OOS Spearman IC on next |open->open| move",
        "n_obs": int(pred.size),
        "TIME-SHUFFLE-PREDICTORS": shuffle,
        "TARGET-LABEL-DERANGEMENT": derangement,
        "TARGET-DERANGEMENT-UNRESTRICTED": global_derange | {
            "role": "full target destruction — the form the future-destroy tripwire adjudicates"
        },
        "TARGET-FUTURE-DESTROY_REPORT_LAYER": future_destroy_layer(derangement, global_derange),
        "BITE_PLANT": bite_check(y, dates, SHUFFLE_SEEDS, derange_seeds),
    }


ALL_ARMS = ("V-PERSIST", "V-LEVEL", "V-REGIME", "V-REGIME-HMM", "V-MEASURE",
            "V-CLOCK", "V-XS", "V-TAIL")


def _unpowered_placeholders(symbol: str, clock: str, reason: str) -> list[dict]:
    """Explicit UNPOWERED rows for a cell with no origins (QA F-9).

    Design §0.1 requires low-n cells to be labelled UNPOWERED, never silently dropped from
    reporting. Without these rows the §6.4 ">=10 of 25 symbols" denominator would quietly
    become the number of symbols that happened to produce data.
    """
    rows = []
    for band in ("DESIGN", "CONFIRM"):
        for arm in ALL_ARMS:
            rows.append({
                "symbol": symbol, "clock": clock, "band": band, "arm": arm,
                "metric": "cell_status", "model": "", "target": "",
                "value": None, "ci_low": None, "ci_high": None, "se": None,
                "se_median": None, "n_obs": 0, "n_dates": 0, "mde": None,
                "band_label": "UNPOWERED", "band_label_detected": "UNPOWERED",
                "target_overlaps_feature": False, "note": reason,
            })
    return rows


def run_cell(args) -> dict:
    """Worker: prepare one symbol x clock cell, run every arm, control and tripwire."""
    symbol, clock, derange_full = args
    manifest = load_fence_manifest()
    t0 = time.time()
    cell = prepare_cell(symbol, clock, manifest)
    seeds = DERANGE_SEEDS_FULL if derange_full else DERANGE_SEEDS_MIN

    rows: list[dict] = []
    controls: dict = {}
    emitted: list[pl.DataFrame] = []
    for band in ("DESIGN", "CONFIRM"):
        frame = cell.design if band == "DESIGN" else cell.confirm
        if frame.height:
            rows += all_arm_rows(cell, band)
            controls[band] = _control_block(cell, band, seeds)
            cols = [c for c in EMIT_COLS if c in frame.columns]
            keep = cols + [c for c in frame.columns if c.startswith(("pred__", "base__"))]
            emitted.append(
                frame.select(keep).with_columns(
                    pl.lit(symbol).alias("symbol"),
                    pl.lit(clock).alias("clock"),
                    pl.lit(band).alias("band"),
                )
            )
    rows += stability_rows(cell)
    if not rows:
        rows = _unpowered_placeholders(
            symbol, clock,
            f"no scored origin in either band (status={cell.diagnostics.get('status')}); "
            "symbol is pinned in the universe and is reported UNPOWERED, not dropped",
        )

    return {
        "symbol": symbol, "clock": clock,
        "rows": rows,
        "controls": controls,
        "diagnostics": cell.diagnostics | {"wall_s": round(time.time() - t0, 2)},
        "models": cell.models,
        "emission": pl.concat(emitted, how="diagonal") if emitted else None,
        "xs_input": {
            band: (cell.design if band == "DESIGN" else cell.confirm)
            .select(["slot_start", "rv20", "target_abs_oo", "target_date"])
            for band in ("DESIGN", "CONFIRM")
            if (cell.design if band == "DESIGN" else cell.confirm).height
        },
    }


# ------------------------------------------------------------ integrity ----


def integrity_selfcheck(
    emission: pl.DataFrame, manifest, universe_report: dict, controls: dict, models: dict
) -> dict:
    """Design §7 code-asserted integrity checklist -> results/integrity_selfcheck.json."""
    checks: list[dict] = []

    def add(cid: str, clause: str, passed: bool, detail) -> None:
        checks.append({"id": cid, "clause": clause, "pass": bool(passed), "detail": detail})

    train_end_ns = int(manifest.train_end_utc.timestamp() * NS)
    holdout_ns = int(manifest.holdout_start_utc.timestamp() * NS)
    test_ns = int(TEST_START.timestamp() * NS)
    span = {"H1": 60, "H4": 240, "D1": 1440}

    max_target_end = int(
        emission.with_columns(
            (pl.col("target_slot_start")
             + pl.col("clock").replace_strict(span, return_dtype=pl.Int64) * 60 * NS
             ).alias("t_end")
        )["t_end"].max()
    )
    add("7.1", "every catalog query band=TRAIN; max target timestamp < train_end_utc",
        max_target_end <= train_end_ns,
        {"max_target_end_utc": _iso(max_target_end), "train_end_utc": _iso(train_end_ns)})
    add("7.1b", "no observation at or after the TEST band start",
        max_target_end <= test_ns,
        {"test_start_utc": _iso(test_ns)})
    add("7.2", "no row with ts >= holdout_start_utc",
        int(emission["slot_end"].max()) < holdout_ns,
        {"max_slot_end_utc": _iso(int(emission["slot_end"].max())),
         "holdout_start_utc": _iso(holdout_ns)})

    # §7.3 CONFIRM never enters an estimated coefficient: every walk-forward fit ends inside
    # DESIGN, and CONFIRM is scored only by the model frozen at the DESIGN end.
    d_end_ns = int(DESIGN_END.timestamp() * NS)
    bad_fits = [
        (k, mk, m.get("final_fit_end_ts"))
        for k, cm in models.items()
        for mk, m in cm.items()
        if isinstance(m, dict) and m.get("final_fit_end_ts", 0) > d_end_ns
    ]
    add("7.3", "CONFIRM not used in estimation coefficients (CONFIRM = verify only)",
        not bad_fits, {"n_models_checked": sum(len(v) for v in models.values()),
                       "violations": bad_fits[:5]})

    # §7.4 features <= origin; target strictly the next bar
    bad_target = int(
        emission.filter(pl.col("target_slot_start") < pl.col("slot_end")).height
    )
    add("7.4", "feature timestamps <= origin; targets use the next bar only",
        bad_target == 0,
        {"rows_with_target_before_origin": bad_target,
         "rule": "target_slot_start >= slot_end for every origin"})

    # §7.3b the open-to-open target EXITS one bar after the target bar; that exit price must
    # also sit inside the origin's own band (QA F-7 — check 7.3 compares origins, not exits).
    d_end_ns2 = int(DESIGN_END.timestamp() * NS)
    exits = emission.with_columns(
        (pl.col("target_slot_start")
         + 2 * pl.col("clock").replace_strict(span, return_dtype=pl.Int64) * 60 * NS
         ).alias("exit_ts")
    )
    design_exit_leak = int(
        exits.filter((pl.col("band") == "DESIGN") & (pl.col("exit_ts") > d_end_ns2)).height
    )
    add("7.3b", "DESIGN target exit price is taken from inside the DESIGN band",
        design_exit_leak == 0,
        {"design_rows_whose_exit_price_falls_in_CONFIRM": design_exit_leak})

    # §7.5 derangements have zero fixed points — MEASURED across the whole seed battery
    fixed_total, seeds_total, batteries = 0, 0, 0
    for c in controls.values():
        for b, cc in c.items():
            if cc.get("status") != "OK":
                continue
            for key in ("TARGET-LABEL-DERANGEMENT", "TARGET-DERANGEMENT-UNRESTRICTED"):
                env = cc.get(key, {})
                if env.get("status") == "OK":
                    fixed_total += int(env.get("index_fixed_points", 0))
                    seeds_total += int(env.get("n_seeds", 0))
                    batteries += 1
    add("7.5", "derangements have 0 fixed points (measured, not asserted)",
        fixed_total == 0,
        {"index_fixed_points_observed": fixed_total, "seed_draws": seeds_total,
         "batteries": batteries})

    add("UNIVERSE", "top-25 recompute == frozen family pin (design §0.1)",
        universe_report.get("set_equal_all", False), universe_report.get("checks"))

    return {
        "experiment": "SPDR-012",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "fence_manifest_path": str(manifest.path),
        "fence_manifest_sha256": manifest.sha256,
        "bands": {
            "DESIGN": [DESIGN_START.isoformat(), DESIGN_END.isoformat()],
            "CONFIRM": [CONFIRM_START.isoformat(), CONFIRM_END.isoformat()],
            "TEST": "NEVER READ",
            "HOLDOUT": "NEVER READ",
        },
        "all_pass": all(c["pass"] for c in checks),
        "checks": checks,
        "report_layers": _report_layers(controls),
        "spread_cost_disclosure": SPREAD_COST_DISCLOSURE,
        "unit_pin": UNIT_PIN,
        "prohibited_claims": PROHIBITED_CLAIMS,
        "interpretation_notes": INTERPRETATION_NOTES,
        "deviations": DEVIATIONS,
        "code_sha256": _code_hashes(),
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "polars": pl.__version__,
            "platform": platform.platform(),
        },
    }


def _report_layers(controls: dict) -> dict:
    """Non-gating report layers (INFR-016 / L-32). Nothing here contributes to ``all_pass``.

    The future-destroy read sits here by operator decision 2026-07-23 (DEV-1): it cannot
    detect look-ahead, so a hard pass/fail on it would report absence of evidence as evidence
    of absence.
    """
    interps: dict[str, int] = {}
    shuffle_outside = 0
    shuffle_cells = 0
    for c in controls.values():
        for b, cc in c.items():
            if cc.get("status") != "OK":
                continue
            lay = cc.get("TARGET-FUTURE-DESTROY_REPORT_LAYER", {})
            k = lay.get("interpretation", "MISSING")
            interps[k] = interps.get(k, 0) + 1
            sh = cc.get("TIME-SHUFFLE-PREDICTORS", {})
            if sh.get("status") == "OK":
                shuffle_cells += 1
                if not sh.get("live_inside_central_90", True):
                    shuffle_outside += 1
    return {
        "future_destroy": {
            "class": "report_layer (no pass field)",
            "operator_decision": "2026-07-23 — demoted from hard tripwire (DEV-1)",
            "interpretation_counts": interps,
            "informative_power": (
                "cannot detect look-ahead; E[Spearman(pred, deranged y)] = 0 for any fixed "
                "predictor. The no-leak claim rests on the design §7.4 construction asserts "
                "(checks 7.3/7.3b/7.4 above), which ARE hard."
            ),
        },
        "predictor_side_time_shuffle": {
            "class": "report_layer (no pass field)",
            "role": "the operative non-vacuity device for this screen",
            "cells": shuffle_cells,
            "cells_with_live_outside_shuffle_central_90": shuffle_outside,
        },
    }


def _iso(ns: int) -> str:
    return datetime.fromtimestamp(ns / NS, tz=timezone.utc).isoformat()


def _code_hashes() -> dict:
    """sha256 of every screen module — pins the code that produced these artifacts (QA F-17)."""
    import hashlib

    return {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(CODE_DIR.glob("*.py"))
    }


# ------------------------------------------------------------------ main ----


def main() -> None:
    ap = argparse.ArgumentParser(description="SPDR-012 volatility characterisation screen")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--derange-full", action="store_true",
                    help="2000-seed derangement upgrade (design §5)")
    ap.add_argument("--symbols", type=str, default="", help="comma list (debug subset)")
    ap.add_argument("--clocks", type=str, default="", help="comma list (debug subset)")
    ap.add_argument("--tag", type=str, default="", help="output filename suffix (debug)")
    args = ap.parse_args()

    t0 = time.time()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_fence_manifest()

    print("[1/7] universe recompute + pin assert")
    uni = recompute_universe(manifest)
    uni_report = assert_pin(uni)
    (RESULTS_DIR / "universe_recomputed.json").write_text(
        json.dumps({"recomputed": uni, "pin_check": uni_report}, indent=2)
    )
    symbols = uni["symbols"]
    if args.symbols:
        symbols = [s for s in symbols if s in set(args.symbols.split(","))]
    clocks = list(CLOCK_ORDER)
    if args.clocks:
        clocks = [c for c in clocks if c in set(args.clocks.split(","))]

    tasks = [(s, c, args.derange_full) for s in symbols for c in clocks]
    print(f"[2/7] {len(tasks)} cells ({len(symbols)} symbols x {len(clocks)} clocks)")

    results: list[dict] = []
    if args.workers > 1:
        with ProcessPoolExecutor(max_workers=args.workers) as ex:
            for r in tqdm(ex.map(run_cell, tasks), total=len(tasks), desc="cells"):
                results.append(r)
    else:
        for t in tqdm(tasks, desc="cells"):
            results.append(run_cell(t))

    print("[3/7] assembling emissions + metrics")
    rows: list[dict] = []
    controls: dict = {}
    diagnostics: dict = {}
    models: dict = {}
    emissions: list[pl.DataFrame] = []
    xs_inputs: dict = {}
    for r in results:
        key = f"{r['symbol']}|{r['clock']}"
        rows += r["rows"]
        if r["controls"]:
            controls[key] = r["controls"]
        diagnostics[key] = r["diagnostics"]
        models[key] = r["models"]
        if r["emission"] is not None:
            emissions.append(r["emission"])
        for band, df in r["xs_input"].items():
            xs_inputs.setdefault((r["clock"], band), {})[r["symbol"]] = df

    print("[4/7] V-XS cross-section")
    xs_panels: list[pl.DataFrame] = []
    for clock in clocks:
        for band in ("DESIGN", "CONFIRM"):
            frames = xs_inputs.get((clock, band), {})
            if not frames:
                continue
            xr, panel = xs_rows(frames, clock, band)
            rows += xr
            if panel.height:
                xs_panels.append(
                    panel.with_columns(pl.lit(clock).alias("clock"), pl.lit(band).alias("band"))
                )

    print("[5/7] writing results")
    suffix = f"_{args.tag}" if args.tag else ""
    ci_grid: list[dict] = []
    for r in rows:
        g = r.pop("_ci_grid", None)
        if g:
            ci_grid.append({
                "key": "|".join(str(r[k]) for k in
                                ("arm", "symbol", "clock", "band", "metric", "model", "target")),
                "point": r["value"], "ci_low_envelope": r["ci_low"],
                "ci_high_envelope": r["ci_high"],
                "block_sensitivity": g,
            })
    metrics = pl.DataFrame(rows, infer_schema_length=None)
    metrics.write_parquet(RESULTS_DIR / f"metrics_by_cell{suffix}.parquet")
    (RESULTS_DIR / f"ci_grid{suffix}.json").write_text(json.dumps({
        "design_clause": "design §6.2 block lengths 1/3/7 x seeds 101/211/307/401/503",
        "envelope_rule": (
            "ci_low = min over the 15 cells, ci_high = max (IN-4). This is a conservative "
            "ENVELOPE of 95% CIs, not itself a 95% interval."
        ),
        "n_metrics": len(ci_grid),
        "grids": ci_grid,
    }, indent=2, default=_json_default))
    emission = pl.concat(emissions, how="diagonal")
    emission.write_parquet(RESULTS_DIR / f"vol_reliability{suffix}.parquet")
    if xs_panels:
        pl.concat(xs_panels, how="diagonal").write_parquet(
            RESULTS_DIR / f"xs_panel{suffix}.parquet"
        )
    (RESULTS_DIR / f"controls{suffix}.json").write_text(
        json.dumps({
            "design_clause": "SPDR-012 design §5",
            "seed_ranges": {
                "TIME-SHUFFLE-PREDICTORS": [int(min(SHUFFLE_SEEDS)), int(max(SHUFFLE_SEEDS))],
                "TARGET-LABEL-DERANGEMENT": [
                    int(min(DERANGE_SEEDS_FULL if args.derange_full else DERANGE_SEEDS_MIN)),
                    int(max(DERANGE_SEEDS_FULL if args.derange_full else DERANGE_SEEDS_MIN)),
                ],
            },
            "cells": controls,
        }, indent=2, default=_json_default)
    )
    (RESULTS_DIR / f"cell_diagnostics{suffix}.json").write_text(
        json.dumps({"cells": diagnostics, "models": models}, indent=2, default=_json_default)
    )

    print("[6/7] golden traces")
    traces = run_golden_traces(manifest)
    (RESULTS_DIR / f"golden_traces{suffix}.json").write_text(
        json.dumps(traces, indent=2, default=_json_default)
    )

    print("[7/7] integrity self-check")
    selfcheck = integrity_selfcheck(emission, manifest, uni_report, controls, models)
    selfcheck["golden_traces_all_pass"] = all(t.get("pass") for t in traces.values())
    selfcheck["checks"].append({
        "id": "GOLDEN", "clause": "design §8 hand-checkable traces",
        "pass": selfcheck["golden_traces_all_pass"],
        "detail": {k: v.get("pass") for k, v in traces.items()},
    })
    selfcheck["all_pass"] = all(c["pass"] for c in selfcheck["checks"])
    selfcheck["wall_seconds"] = round(time.time() - t0, 1)
    (RESULTS_DIR / f"integrity_selfcheck{suffix}.json").write_text(
        json.dumps(selfcheck, indent=2, default=_json_default)
    )

    print(f"\nintegrity all_pass = {selfcheck['all_pass']}  ({selfcheck['wall_seconds']}s)")
    for c in selfcheck["checks"]:
        print(f"  [{'PASS' if c['pass'] else 'FAIL'}] {c['id']}: {c['clause']}")


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        v = float(o)
        return v if np.isfinite(v) else None
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(f"not JSON serialisable: {type(o)}")


if __name__ == "__main__":
    main()
