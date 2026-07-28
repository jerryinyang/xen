"""SPDR-018 orchestrator — TRAIN-only, vectorised, disposition-free.

    python run_screen.py --jobs 8

Emits every artifact in design §15 and refuses to finish if a HARD integrity check fails.
This script takes NO disposition and writes NO verdict: the binding read is the fresh-context
analyst's ``analysis.md`` (SPDR lane stage 5), and the disposition is the operator's.

Parallelism note: ``--jobs`` partitions the cell grid into disjoint work units. No cell moves
between units and every unit is independently seeded, so the union is identical to a sequential
run — which ``--selfcheck-determinism`` asserts by actually running both and diffing them.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import arm_a           # noqa: E402
import arm_b           # noqa: E402
import arm_c           # noqa: E402
import arm_d           # noqa: E402
import cells           # noqa: E402
import uniform_controls as controls   # noqa: E402  (named to avoid shadowing the
#   parents' own `controls` modules, which SPDR-015 imports lazily from transitions/
#   zz_ordinal — a same-named module here would win in sys.modules and break arm D)
import ctrader         # noqa: E402
import metrics         # noqa: E402
import parents         # noqa: E402
import selfcheck       # noqa: E402
import unitpin         # noqa: E402
from config import (   # noqa: E402
    BOOT_RESAMPLES,
    DEVIATIONS,
    INTERPRETATION_NOTES,
    PLOTS_DIR,
    PROHIBITED_CLAIMS,
    RESULTS_DIR,
    SPREAD_COST_DISCLOSURE,
    TARGETS,
    UNIVERSE_PIN_FAMILY,
)

_UNIT_PIN: dict = {}


def _json(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, Path):
        return str(o)
    return str(o)


def write_json(name: str, payload) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    p = RESULTS_DIR / name
    p.write_text(json.dumps(payload, indent=2, sort_keys=True, default=_json))
    return p


def write_parquet(name: str, df: pd.DataFrame) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    p = RESULTS_DIR / name
    out = df.copy()
    for c in out.columns:
        col = out[c]
        if col.map(lambda v: isinstance(v, (list, dict, tuple, np.ndarray))).any():
            out[c] = col.map(lambda v: json.dumps(v, default=_json)
                             if isinstance(v, (list, dict, tuple, np.ndarray)) else v)
            col = out[c]
        # A conditioner axis legitimately carries mixed types across items — shock_flag is
        # boolean, last_k_state_* is a string, vol_tercile is categorical. Parquet needs one
        # type per column, so mixed object columns are written as strings. Values are unchanged;
        # only their storage type is.
        if col.dtype == object:
            kinds = set(col.dropna().map(lambda v: type(v).__name__))
            if len(kinds) > 1:
                out[c] = col.map(lambda v: v if v is None else str(v)).astype("string")
    out.to_parquet(p, index=False)
    return p


def universe() -> list[str]:
    pin = json.loads(Path(UNIVERSE_PIN_FAMILY).read_text())
    return list(pin["symbols"])


# --------------------------------------------------------------------------- workers
def _worker(task: dict) -> list[dict]:
    n_boot = task.get("n_boot", BOOT_RESAMPLES)
    arm = task["arm"]
    if arm == "B":
        return arm_b.run_task(task, _UNIT_PIN, n_boot=n_boot)
    if arm == "C":
        return arm_c.run_task(task, _UNIT_PIN, n_boot=n_boot)
    if arm == "D":
        if task["stage"] == "2b":
            return arm_d.run_2b(n_boot=n_boot)
        return arm_d.run_symbol(task["symbol"], n_boot=n_boot)
    if arm == "A":
        return arm_a.run(_UNIT_PIN, n_boot=n_boot)
    raise KeyError(arm)


def _sort_key(r: dict) -> str:
    return "|".join(str(r.get(k, "")) for k in
                    ("arm", "residue_item", "symbol", "clock", "band", "basis", "signal",
                     "exit_mode", "source", "z", "H", "h", "event_type", "policy",
                     "conditioner", "conditioner_value", "arm_name", "metric", "model",
                     "method", "target", "horizon_k", "leg", "variant", "straddle_arm"))


def run_tasks(tasks: list[dict], jobs: int, *, label: str,
              start_method: str = "fork") -> list[dict]:
    """Fan work units out across processes.

    ``start_method`` matters: arms A-C are pandas/numpy and fork cleanly, but arm D drives
    polars, whose Rust thread pool does NOT survive ``fork`` — the children inherit locks held by
    threads that do not exist in the child and deadlock at 0% CPU before touching any data. Arm D
    therefore uses ``spawn``, which builds a fresh interpreter per worker.
    """
    t0 = time.time()
    if jobs <= 1:
        out: list[dict] = []
        for i, t in enumerate(tasks, 1):
            out += _worker(t)
            print(f"  [{label}] {i}/{len(tasks)}  ({time.time() - t0:.0f}s)", flush=True)
    else:
        ctx = mp.get_context(start_method)
        with ctx.Pool(jobs) as pool:
            out = []
            for i, res in enumerate(pool.imap_unordered(_worker, tasks), 1):
                out += res
                print(f"  [{label}] {i}/{len(tasks)}  ({time.time() - t0:.0f}s)", flush=True)
    # deterministic order regardless of completion order
    return sorted(out, key=_sort_key)


# --------------------------------------------------------------------------- controls
def build_controls(n_boot: int) -> tuple[dict, list[dict]]:
    """The three uniform controls + the three tripwires, on each arm's DESIGNATED PRIMARY CELLS.

    Scope (config IN-2): the parents' own registered primary cell plus the pooled cell. The scope
    is emitted so nothing is hidden; no cell is dropped from the metrics table because of it.
    """
    payload: dict = {"scope": ("uniform controls run on each arm's designated primary cells — "
                               "the parent's own registered control cell plus the arm's pooled "
                               "cell (config IN-2); the full grid is in metrics_by_cell.parquet"),
                     "seeds": {"side_derangement": 2000, "magnitude_matched": 2000,
                               "forward_path": 2000, "plant_curve": 200},
                     "no_pass_field": True,
                     "collapse_fraction_status": "DISCLOSURE_ONLY (M-5)"}
    tripwires: list[dict] = []

    # ---------------- arm B primary cell: the ZZ structural leg, pooled ---------------------
    ep = arm_b.load_panel()
    b = ep[(ep.clock == "H1") & (ep.signal == "D-ZZ")
           & (ep.exit_mode == parents.const("SPDR-013", "ZZ_STRUCTURAL_EXIT_MODE"))]
    grp_b = (b["symbol"].astype(str) + "|"
             + pd.to_datetime(b["entry_ts"], unit="ns").dt.strftime("%Y-%m")).to_numpy()
    side_b = b["side"].to_numpy(dtype=float)
    net_b = b["partial_net_bps"].to_numpy(dtype=float)
    payload["arm_B_side_derangement"] = controls.side_derangement(net_b, side_b, grp_b)
    payload["arm_B_ambient_base"] = controls.ambient_base(
        net_b, ep[(ep.clock == "H1")]["partial_net_bps"].to_numpy(dtype=float),
        cost_bps=0.0, ts_live=b["entry_ts"].to_numpy(dtype=np.int64),
        ts_ambient=ep[(ep.clock == "H1")]["entry_ts"].to_numpy(dtype=np.int64))
    tripwires.append(controls.tripwire_3_forward_path(side_b, net_b * side_b, grp_b))
    tripwires.append(controls.tripwire_1_construction({
        "decision_idx": b["entry_idx"].to_numpy(dtype=np.int64) - 1,
        "entry_idx": b["entry_idx"].to_numpy(dtype=np.int64),
        "exit_idx": b["entry_idx"].to_numpy(dtype=np.int64)
        + b["hold_bars"].to_numpy(dtype=np.int64),
        "h": b["hold_bars"].to_numpy(dtype=np.int64)}))

    # ---------------- arm C primary cell: the parent's own CONTROL_PRIMARY_CELL --------------
    pe = arm_c.load_panel()
    cp = parents.const("SPDR-014", "CONTROL_PRIMARY_CELL")
    c = pe[(pe.source == cp["source"]) & (pe.z == cp["z"]) & (pe.H == cp["H"])
           & (pe.event_type == cp["event"]) & (pe.h == cp["h"]) & (pe.clock == "H1")
           & (pe.policy == "P-NONE")]
    grp_c = (c["symbol"].astype(str) + "|"
             + pd.to_datetime(c["entry_ts"], unit="ns").dt.strftime("%Y-%m")).to_numpy()
    side_c = c["side"].to_numpy(dtype=float)
    net_c = c["c_net_bps"].to_numpy(dtype=float)
    payload["arm_C_primary_cell"] = cp
    payload["arm_C_side_derangement"] = controls.side_derangement(net_c, side_c, grp_c)
    payload["arm_C_ambient_base"] = controls.ambient_base(
        net_c, pe[pe.clock == "H1"]["c_net_bps"].to_numpy(dtype=float), cost_bps=0.0,
        ts_live=c["entry_ts"].to_numpy(dtype=np.int64),
        ts_ambient=pe[pe.clock == "H1"]["entry_ts"].to_numpy(dtype=np.int64))
    tripwires.append(controls.tripwire_3_forward_path(side_c, net_c * side_c, grp_c))

    # ---------------- M-3: the magnitude-matched comparator, on the magnitude conditioners ----
    payload["magnitude_matched"] = {}
    for cond in ("shock_flag", "mag_high"):
        live = c[c[cond].astype(bool)]
        pool = c[~c[cond].astype(bool)]
        if live.empty or pool.empty:
            payload["magnitude_matched"][cond] = {"status": "NO_ROWS_ON_ONE_SIDE"}
            continue
        # |r_t| on the decision bar: the magnitude the conditioner is defined against
        live_abs = live["c_gross_bps"].abs().to_numpy(dtype=float)
        pool_abs = pool["c_gross_bps"].abs().to_numpy(dtype=float)
        payload["magnitude_matched"][cond] = controls.magnitude_matched(
            live_abs, live["c_net_bps"].to_numpy(dtype=float),
            pool_abs, pool["c_net_bps"].to_numpy(dtype=float),
            np.zeros(len(pool), dtype=bool))
    # ---------------- TRIPWIRE-2 [HARD]: legal variant vs the deliberately leaky twin ---------
    # Declared HARD in design §7.1 and, with TRIPWIRE-1, IS the causality claim. The contrast is
    # computed on the independent self-check side (golden.g6), which rebuilds both variants from
    # the fenced catalog rather than from any arm module.
    import golden as _golden
    g6 = _golden.g6()
    tripwires.append(controls.tripwire_2_leaky_twin(
        g6.get("legal_variant_mean_bps", float("nan")),
        g6.get("leaky_twin_mean_bps", float("nan")),
        n_matched=int(g6.get("n_selected_legal") or 0)))
    payload["tripwire_2_source"] = g6

    payload["magnitude_matched_note"] = (
        "M-3: a conditioner defined on move magnitude needs a magnitude-matched comparator, not "
        "just a side-matched one. Where the state IS the magnitude by definition, no disjoint "
        "matched pool exists in the upper deciles and the control reports "
        "MATCH_INFEASIBLE_STATE_IS_MAGNITUDE — that is the measured answer, not a gap.")
    return payload, tripwires


# --------------------------------------------------------------------------- not-resolvable
def not_resolvable(frames: dict[str, pd.DataFrame]) -> list[dict]:
    """Every cell that could not be powered, with the shortfall QUANTIFIED (design §5, §15).

    Only cells on which every §5 lever has been applied qualify: a per-symbol DESIGN cell that is
    short of power is UNPOWERED, not NOT_RESOLVABLE. NOT_RESOLVABLE means "pooled, sigma-
    normalised, on the full TRAIN span, and STILL short" — which is an answer to the 017 question.
    """
    out = []
    for arm, df in frames.items():
        if df.empty or "levers_exhausted" not in df.columns:
            continue
        sel = df[df["levers_exhausted"].fillna(False).astype(bool)]
        for _, r in sel.iterrows():
            labels = [r.get("band_label_mean"), r.get("band_label_edge"), r.get("band_label_gap"),
                      r.get("band_label_ic"), r.get("band_label_r2"), r.get("band_label")]
            if "NOT_RESOLVABLE" not in [x for x in labels if isinstance(x, str)]:
                continue
            mde = r.get("net_block_mde_mean_bps", r.get("block_mde", r.get("block_mde_gap_bps")))
            target = r.get("target_mde")
            n = r.get("n")
            mult = (float(mde) / float(target)
                    if all(isinstance(x, (int, float)) and np.isfinite(x) and x
                           for x in (mde, target)) else float("nan"))
            out.append({
                "arm": arm, "residue_item": r.get("residue_item"),
                "symbol": r.get("symbol"), "clock": r.get("clock"), "band": r.get("band"),
                "basis": r.get("basis"), "metric": r.get("metric"),
                "signal": r.get("signal"), "exit_mode": r.get("exit_mode"),
                "source": r.get("source"), "z": r.get("z"), "H": r.get("H"), "h": r.get("h"),
                "event_type": r.get("event_type"), "conditioner": r.get("conditioner"),
                "n": n, "n_dates": r.get("n_dates"),
                "block_mde": mde, "target_mde": target,
                "iid_mde__COMPANION_ONLY": r.get("iid_mde_bps__COMPANION_ONLY",
                                                 r.get("iid_mde__COMPANION_ONLY")),
                "multiple_short": mult,
                "n_required_for_target": (float(np.ceil(float(n) * mult ** 2))
                                          if isinstance(n, (int, float)) and np.isfinite(mult)
                                          else float("nan")),
                "target_rule": r.get("target_rule"),
                "statement": ("cannot reach its parent's own target precision in its original "
                              "form on this data, after pooling across symbols, sigma-"
                              "normalising and using the full TRAIN span. This ANSWERS the "
                              "checkpoint-017 open question; it is never evidence against the "
                              "hypothesis (B-5)."),
            })
    return out


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description="SPDR-018 powering sweep (TRAIN-only)")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--n-boot", type=int, default=BOOT_RESAMPLES)
    ap.add_argument("--symbols", type=str, default="", help="debug subset")
    ap.add_argument("--arms", type=str, default="ABCD")
    ap.add_argument("--skip-universe-recompute", action="store_true")
    ap.add_argument("--resume", action="store_true",
                    help="reuse any arm_*.parquet already emitted instead of recomputing it")
    ap.add_argument("--selfcheck-determinism", action="store_true",
                    help="run arm B twice (1 job vs --jobs) and assert bit-identical output")
    args = ap.parse_args()

    global _UNIT_PIN
    t0 = time.time()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    syms = ([s for s in args.symbols.split(",") if s] or universe())

    print("== unit pin (measured at run, never asserted)", flush=True)
    _UNIT_PIN = unitpin.measure(syms)
    unitpin.write(_UNIT_PIN)
    print(f"   pooled sigma = {_UNIT_PIN['pooled_median_sigma_bps']:.2f} bps over "
          f"{_UNIT_PIN['n_symbols_measured']}/{len(syms)} symbols", flush=True)

    frames: dict[str, pd.DataFrame] = {}
    seq_frame = par_frame = None

    def _resumed(arm: str) -> pd.DataFrame | None:
        f = RESULTS_DIR / f"arm_{arm}.parquet"
        if args.resume and f.exists():
            df = pd.read_parquet(f)
            print(f"== arm {arm}: RESUMED from {f.name} ({len(df)} cells)", flush=True)
            return df
        return None

    if "A" in args.arms:
        frames["A"] = _resumed("A")
        if frames["A"] is None:
            del frames["A"]
        print("== arm A (SPDR-012 residue)", flush=True) if "A" not in frames else None
        if "A" not in frames:
            frames["A"] = cells.to_frame(sorted(arm_a.run(_UNIT_PIN, n_boot=args.n_boot),
                                                key=_sort_key))
            write_parquet("arm_A.parquet", frames["A"])
    if "B" in args.arms and (_r := _resumed("B")) is not None:
        frames["B"] = _r
    elif "B" in args.arms:
        print("== arm B (SPDR-013 residue — where W and L get measured)", flush=True)
        tb = [{**t, "n_boot": args.n_boot} for t in arm_b.tasks(_UNIT_PIN)]
        recs = run_tasks(tb, args.jobs, label="B")
        frames["B"] = cells.to_frame(recs)
        write_parquet("arm_B.parquet", frames["B"])

    if "C" in args.arms and (_r := _resumed("C")) is not None:
        frames["C"] = _r
    elif "C" in args.arms:
        print("== arm C (SPDR-014 residue — event-nested, original form)", flush=True)
        tc = [{**t, "n_boot": args.n_boot} for t in arm_c.tasks(_UNIT_PIN)]
        frames["C"] = cells.to_frame(run_tasks(tc, args.jobs, label="C"))
        write_parquet("arm_C.parquet", frames["C"])
    if "D" in args.arms and (_r := _resumed("D")) is not None:
        frames["D"] = _r
    elif "D" in args.arms:
        print("== arm D (SPDR-015 residue — incl. the never-scored CONFIRM slice)", flush=True)
        td = ([{"arm": "D", "stage": "symbol", "symbol": s, "n_boot": args.n_boot} for s in syms]
              + [{"arm": "D", "stage": "2b", "n_boot": args.n_boot}])
        frames["D"] = cells.to_frame(run_tasks(td, args.jobs, label="D",
                                              start_method="spawn"))
        write_parquet("arm_D.parquet", frames["D"])

    # ---- determinism (§12 HARD): parallel must be bit-identical to sequential ---------------
    # Run unconditionally on a bounded arm-B subset, INDEPENDENT of --resume, so a resumed run can
    # never silently skip a HARD check.
    if args.jobs > 1:
        print("== determinism check (parallel vs sequential)", flush=True)
        det = [{"arm": "B", "stage": "per_symbol", "symbol": s_, "n_boot": args.n_boot}
               for s_ in syms[:3]]
        seq_frame = cells.to_frame(run_tasks(det, 1, label="det-seq"))
        par_frame = cells.to_frame(run_tasks(det, args.jobs, label="det-par"))

    print("== cTrader replication (separate fence, never pooled)", flush=True)
    crows, ctrader_max_ts = ctrader.run(n_boot=args.n_boot)
    write_parquet("ctrader_replication.parquet", cells.to_frame(crows))

    print("== controls + tripwires", flush=True)
    controls_payload, tripwires = build_controls(args.n_boot)
    write_json("controls.json", controls_payload)

    print("== combined metrics table", flush=True)
    combined = pd.concat([f for f in frames.values() if not f.empty], ignore_index=True)
    combined = combined.reindex(sorted(combined.columns), axis=1)
    write_parquet("metrics_by_cell.parquet", combined)

    write_json("not_resolvable.json", {
        "definition": ("UNPOWERED after every design §5 lever has been applied — pooled across "
                       "symbols, sigma-normalised, on the full TRAIN span"),
        "first_class_result": True,
        "cells": not_resolvable(frames),
    })

    print("== integrity self-check", flush=True)
    ep = arm_b.load_panel()
    day_idx, starts = metrics.day_index(ep["entry_ts"].to_numpy(dtype=np.int64)[:5000])
    suff = metrics.day_sufficient(ep["partial_net_bps"].to_numpy(dtype=float)[:5000],
                                  day_idx, starts.size)
    equivalence = metrics.assert_canonical_equivalence(suff, 13.5)

    panels = {"SPDR-013.episodes": ep,
              "SPDR-014.post_event": arm_c.load_panel(),
              "SPDR-012.vol_reliability": arm_a.load_panel(),
              "SPDR-015.zz_ordinal": arm_d.zz_panel()}
    sc = selfcheck.run(panels=panels, cell_frames=frames, controls_payload=controls_payload,
                       tripwires=tripwires, seq_frame=seq_frame, par_frame=par_frame,
                       ctrader_max_ts=ctrader_max_ts,
                       recompute_universe=not args.skip_universe_recompute,
                       equivalence=equivalence)
    sc["parent_parity_detail_is_in"] = "the PARENT PARITY check above"
    write_json("integrity_selfcheck.json", sc)
    write_json("parent_parity.json",
               next(c["detail"] for c in sc["checks"] if c["check"].startswith("Parent parity")))
    write_json("golden_traces.json",
               next(c["detail"] for c in sc["checks"] if c["check"].startswith("Golden traces")))

    write_json("run_summary.json", {
        "experiment": "SPDR-018", "family": "CF-VOLDIR-001", "hypothesis": "HYP-D5",
        "checkpoint": "2026-07-25-018-trade-opportunity-capture-geometry",
        "lane": "SPDR — TRAIN-only, 0 counted TEST reads, 0 multiplicity slots, no family action",
        "kind": "PRECISION experiment — proposes no new market regularity",
        "wall_clock_s": round(time.time() - t0, 1),
        "jobs": args.jobs, "n_boot": args.n_boot,
        "n_cells_total": int(len(combined)),
        "n_cells_by_arm": {k: int(len(v)) for k, v in frames.items()},
        "n_symbols": len(syms),
        "target_precision_inherited_per_arm": TARGETS,
        "spread_cost_disclosure": SPREAD_COST_DISCLOSURE,
        "deviations": DEVIATIONS,
        "interpretation_notes": INTERPRETATION_NOTES,
        "prohibited_claims": PROHIBITED_CLAIMS,
        "disposition": ("NONE — this script takes no disposition. The binding read is the "
                        "fresh-context analyst's analysis.md; the disposition is the operator's."),
        "hard_all_held": sc["hard_all_held"],
        "screen_code_sha256": sc["screen_code_sha256"],
    })

    print(f"\n-- cells: {len(combined)}  wall clock: {time.time() - t0:.0f}s", flush=True)
    print(f"-- HARD checks held: {sc['hard_all_held']}"
          + ("" if sc["hard_all_held"] else f"  FAILED: {sc.get('failed_checks')}"), flush=True)
    selfcheck.enforce(sc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
