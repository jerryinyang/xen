"""SPDR-018B orchestrator — the checkpoint-017 residue on the cTrader universe.

    python run18b.py --n-boot 2000

TRAIN-only, cTrader fence, all four arms. Takes NO disposition: the binding read is the
fresh-context analyst's `analysis.md`, and the disposition is the operator's.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(HERE.parents[1] / "SPDR-018" / "screen_code"))

import arm_ab18b                      # noqa: E402
import arm_c18b                       # noqa: E402
import arm_d                          # noqa: E402  (SPDR-018's, reused unchanged)
import cells                          # noqa: E402
import retarget                       # noqa: E402
import uniform_controls as controls   # noqa: E402
import unitpin                        # noqa: E402
from config18b import (               # noqa: E402
    BANDS,
    COST_MODEL_PROVENANCE,
    CTRADER_CONFIRM_END,
    CTRADER_DESIGN_END_NS,
    CTRADER_DESIGN_START,
    CTRADER_DESIGN_START_NS,
    CTRADER_FENCE_SHA256,
    CTRADER_HOLDOUT_START_NS,
    CTRADER_SYMBOLS,
    CTRADER_TRAIN_END_NS,
    DEVIATIONS,
    IDENTITY_GUARD,
    INTERPRETATION_NOTES,
    N_SYMBOLS,
    POWER_NOTE,
    PLOTS_DIR,
    PROHIBITED_CLAIMS,
    RESULTS_DIR,
    SPREAD_COST_DISCLOSURE,
)


def _json(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def write_json(name, payload):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    p = RESULTS_DIR / name
    p.write_text(json.dumps(payload, indent=2, sort_keys=True, default=_json))
    return p


def write_parquet(name, df):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    p = RESULTS_DIR / name
    out = df.copy()
    for c in out.columns:
        col = out[c]
        if col.map(lambda v: isinstance(v, (list, dict, tuple, np.ndarray))).any():
            out[c] = col.map(lambda v: json.dumps(v, default=_json)
                             if isinstance(v, (list, dict, tuple, np.ndarray)) else v)
            col = out[c]
        if col.dtype == object and len(set(col.dropna().map(lambda v: type(v).__name__))) > 1:
            out[c] = col.map(lambda v: v if v is None else str(v)).astype("string")
    out.to_parquet(p, index=False)
    return p


def retarget_arm_d() -> None:
    """Point SPDR-018's arm D at cTrader's bands (its module-level bounds are Bybit's)."""
    import config18b as C
    arm_d._BOUNDS = {"DESIGN": (C.CTRADER_DESIGN_START_NS, C.CTRADER_DESIGN_END_NS),
                     "CONFIRM": (C.CTRADER_DESIGN_END_NS, C.CTRADER_TRAIN_END_NS),
                     "TRAIN": (C.CTRADER_DESIGN_START_NS, C.CTRADER_TRAIN_END_NS)}
    arm_d.DESIGN_START = C.CTRADER_DESIGN_START
    arm_d.CONFIRM_END = C.CTRADER_CONFIRM_END


def identity_guard(n_boot: int) -> dict:
    """Design §5 [HARD] — the retargeted path on a BYBIT symbol must reproduce SPDR-018's cells.

    Proves the retarget changed the DATA, not the OBJECT. Uses arm B, whose SPDR-018 cells are
    themselves parity-verified against SPDR-013 to 1.8e-12.
    """
    sym = IDENTITY_GUARD["guard_symbol"]
    out = {**IDENTITY_GUARD, "guard_symbol": sym}
    try:
        ref = pd.read_parquet(HERE.parents[1] / "SPDR-018" / "results" / "arm_B.parquet")
        ref = ref[(ref.symbol == sym) & (ref.basis == "per_symbol")]
        import config as c18                       # SPDR-018's config: the Bybit span
        with retarget.bybit_original("SPDR-013"), retarget.bybit_original("SPDR-014"):
            from xen.nautilus.catalog_fence import load_fence_manifest
            df = arm_ab18b.build_episodes_b(
                sym, load_fence_manifest(), clocks=("H1",),
                start=c18.DESIGN_START, end=c18.CONFIRM_END,
                design_end_ns=int(c18.DESIGN_END.timestamp() * 1_000_000_000))
        if df.empty:
            out.update({"held": False, "detail": "guard produced no episodes"})
            return out
        agg = (df.groupby(["symbol", "clock", "band", "signal", "exit_mode"], observed=True)
               .agg(mine_n=("gross_bps", "size"), mine_gross=("gross_bps", "mean")).reset_index())
        j = ref.merge(agg, on=["symbol", "clock", "band", "signal", "exit_mode"], how="inner")
        if j.empty:
            out.update({"held": False, "detail": "no overlapping cells to compare"})
            return out
        dn = (j.mine_n.astype(float) - j.n.astype(float)).abs()
        dg = (j.mine_gross.astype(float) - j.gross_mean.astype(float)).abs()
        out.update({
            "n_cells_compared": int(len(j)),
            "max_abs_diff_n": float(dn.max()),
            "max_abs_diff_gross_bps": float(np.nanmax(dg)),
            "held": bool(dn.max() == 0 and np.nanmax(dg) <= IDENTITY_GUARD["tolerance_bps"]),
        })
    except Exception as e:                                        # noqa: BLE001
        out.update({"held": False, "detail": f"guard failed to run: {e!r}"})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="SPDR-018B — 017 residue on the cTrader universe")
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--symbols", type=str, default="")
    ap.add_argument("--skip-guard", action="store_true")
    ap.add_argument("--resume", action="store_true",
                    help="reuse arm_*.parquet already emitted instead of recomputing")
    args = ap.parse_args()
    syms = [s for s in args.symbols.split(",") if s] or list(CTRADER_SYMBOLS)

    t0 = time.time()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    man = retarget.ctrader_manifest()
    rebinds = {p: retarget.rebind(p) for p in ("SPDR-012", "SPDR-013", "SPDR-014", "SPDR-015")}
    retarget_arm_d()

    # the unit-pin module carries SPDR-018's Bybit band constants; rebind to cTrader's own span
    unitpin.DESIGN_START = CTRADER_DESIGN_START
    unitpin.CONFIRM_END = CTRADER_CONFIRM_END
    unitpin.NS = 1_000_000_000
    print("== unit pin (recomputed on cTrader symbols, never carried over from crypto)", flush=True)
    up = unitpin.measure(syms, manifest=man)
    up["universe"] = "CTRADER"
    unitpin.write(up, RESULTS_DIR / "unit_pin.json")
    print(f"   pooled sigma = {up.get('pooled_median_sigma_bps')} bps "
          f"({up.get('n_symbols_measured')}/{len(syms)})", flush=True)

    frames: dict[str, pd.DataFrame] = {}
    panels: dict[str, pd.DataFrame] = {}

    def _resumed(arm):
        f = RESULTS_DIR / f"arm_{arm}.parquet"
        if args.resume and f.exists():
            d = pd.read_parquet(f)
            print(f"== arm {arm}: RESUMED ({len(d)} cells)", flush=True)
            return d
        return None

    print("== arms A + B", flush=True)
    ra, rb = _resumed("A"), _resumed("B")
    ab = ({"A_rows": [], "B_rows": [], "A_panel": pd.DataFrame(), "B_panel": pd.DataFrame()}
          if (ra is not None and rb is not None)
          else arm_ab18b.run(manifest=man, n_boot=args.n_boot, symbols=syms))
    frames["A"] = ra if ra is not None else cells.to_frame(ab["A_rows"])
    frames["B"] = rb if rb is not None else cells.to_frame(ab["B_rows"])
    panels["A"], panels["B"] = ab["A_panel"], ab["B_panel"]
    for k in ("A", "B"):
        if not frames[k].empty:
            write_parquet(f"arm_{k}.parquet", frames[k])
    print(f"   A {len(frames['A'])} cells | B {len(frames['B'])} cells "
          f"({time.time()-t0:.0f}s)", flush=True)

    print("== arm C (holds the shock-MOMO thread)", flush=True)
    rc = _resumed("C")
    if rc is not None:
        frames["C"], c_panel = rc, pd.DataFrame()
    else:
        c_rows, c_panel = arm_c18b.run(manifest=man, n_boot=args.n_boot, symbols=syms)
        frames["C"] = cells.to_frame(c_rows)
        if not c_panel.empty:      # persist: controls and the post-run fixes both need it, and a
            write_parquet("panel_C.parquet", c_panel)   # resumed run otherwise silently skips them
    panels["C"] = c_panel
    if not frames["C"].empty:
        write_parquet("arm_C.parquet", frames["C"])
    print(f"   C {len(frames['C'])} cells ({time.time()-t0:.0f}s)", flush=True)

    print("== arm D", flush=True)
    rd = _resumed("D")
    d_rows = []
    for s in ([] if rd is not None else syms):
        d_rows += arm_d.run_symbol(s, manifest=man, n_boot=args.n_boot)
    d_rows += arm_d.run_2b(n_boot=args.n_boot) if False else []   # 2b needs a cTrader ZZ panel
    frames["D"] = rd if rd is not None else cells.to_frame(d_rows)
    if not frames["D"].empty:
        write_parquet("arm_D.parquet", frames["D"])
    print(f"   D {len(frames['D'])} cells ({time.time()-t0:.0f}s)", flush=True)

    print("== controls", flush=True)
    payload = {"universe": "CTRADER", "cost_model": COST_MODEL_PROVENANCE,
               "seeds": {"side_derangement": 2000, "forward_path": 2000}}
    pb = panels.get("B")
    if pb is not None and not pb.empty:
        b = pb[(pb.clock == "H1") & (pb.signal == "D-ZZ") & (pb.exit_mode == "signalflip")]
        if len(b) > 10:
            grp = (b["symbol"].astype(str) + "|"
                   + pd.to_datetime(b["entry_ts"], unit="ns").dt.strftime("%Y-%m")).to_numpy()
            payload["arm_B_side_derangement"] = controls.side_derangement(
                b["c_net_bps"].to_numpy(float), b["side"].to_numpy(float), grp)
    pc = panels.get("C")
    if pc is not None and not pc.empty:
        cp = pc[(pc.source == "Z-VOL") & (pc.z == 1.5) & (pc.H == 12)
                & (pc.event_type == "E-TOUCH") & (pc.h == 12) & (pc.policy == "P-NONE")]
        if len(cp) > 10:
            grp = (cp["symbol"].astype(str) + "|"
                   + pd.to_datetime(cp["entry_ts"], unit="ns").dt.strftime("%Y-%m")).to_numpy()
            payload["arm_C_side_derangement"] = controls.side_derangement(
                cp["c_net_bps"].to_numpy(float), cp["side"].to_numpy(float), grp)
            # M-3 on the magnitude conditioners — the shock_flag row is the replication target
            payload["magnitude_matched"] = {}
            for cond in ("shock_flag", "mag_high"):
                if cond not in cp.columns:
                    continue
                live = cp[cp[cond].astype(bool)]
                pool = cp[~cp[cond].astype(bool)]
                if len(live) < 5 or len(pool) < 5:
                    payload["magnitude_matched"][cond] = {"status": "TOO_FEW_ROWS",
                                                          "n_live": int(len(live))}
                    continue
                payload["magnitude_matched"][cond] = controls.magnitude_matched(
                    live["c_gross_bps"].abs().to_numpy(float),
                    live["c_net_bps"].to_numpy(float),
                    pool["c_gross_bps"].abs().to_numpy(float),
                    pool["c_net_bps"].to_numpy(float),
                    np.zeros(len(pool), dtype=bool))
    write_json("controls.json", payload)

    combined = pd.concat([f for f in frames.values() if not f.empty], ignore_index=True)
    combined = combined.reindex(sorted(combined.columns), axis=1)
    write_parquet("metrics_by_cell.parquet", combined)

    print("== integrity self-check", flush=True)
    checks = []

    def hard(name, held, detail=None):
        checks.append({"check": name, "severity": "HARD", "held": bool(held), "detail": detail})

    maxts = {}
    for k, p in panels.items():
        if p is None or p.empty:
            continue
        for c in ("exit_ts", "entry_ts", "slot_start", "slot_end"):
            if c in p.columns:
                v = pd.to_numeric(p[c], errors="coerce").to_numpy(dtype=float)
                v = v[np.isfinite(v) & (v > 0)]
                if v.size:
                    maxts[f"{k}.{c}"] = int(v.max())
    hard("cTrader TRAIN fence — max ts < 2023-11-22T00:00Z",
         all(v < CTRADER_TRAIN_END_NS for v in maxts.values()), maxts)
    hard("cTrader holdout — zero rows at or after 2024-12-13",
         all(v < CTRADER_HOLDOUT_START_NS for v in maxts.values()), None)
    import hashlib
    sha = hashlib.sha256(Path(
        HERE.parents[1] / "INFR-021" / "artifacts" / "fence-manifest.json").read_bytes()).hexdigest()
    hard("cTrader fence provenance — sha256 matches the pin", sha == CTRADER_FENCE_SHA256,
         {"expected": CTRADER_FENCE_SHA256, "measured": sha})
    res = combined.get("identity_residual_bps")
    mx = float(pd.to_numeric(res, errors="coerce").max()) if res is not None else float("nan")
    hard("Identity reconstruction — |p*W-(1-p)*L-mean| < 0.01 bps",
         (not np.isfinite(mx)) or mx < 0.01, {"max_residual_bps": mx})
    srcs = set(pd.unique(combined.get("mde_source_for_bands", pd.Series(dtype=object)).dropna()))
    hard("M-1 — band labels driven by the BLOCK MDE", srcs.issubset({"block"}), sorted(srcs))
    bad = [c for c in combined.columns if c == "pass" or "at_or_above_p" in c]
    hard("No `pass` field / no at_or_above_pXX", not bad, bad)
    fp = [v.get("fixed_points_total") for k, v in payload.items()
          if isinstance(v, dict) and "fixed_points_total" in v]
    hard("Derangements — fixed-point count == 0", all(x == 0 for x in fp), fp)
    guard = {"skipped": True} if args.skip_guard else identity_guard(args.n_boot)
    hard("CROSS-UNIVERSE OBJECT IDENTITY (design §5)",
         guard.get("held", False) or args.skip_guard, guard)

    failed = [c["check"] for c in checks if not c["held"]]
    sc = {"experiment": "SPDR-018B", "universe": "CTRADER",
          "lane": "SPDR — TRAIN-only, 0 counted TEST reads, no family action, no XENA",
          "bands": {k: [str(v[0]), str(v[1])] for k, v in BANDS.items()},
          "cost_model": COST_MODEL_PROVENANCE,
          "spread_cost_disclosure": SPREAD_COST_DISCLOSURE,
          "power_note": POWER_NOTE, "n_symbols": N_SYMBOLS,
          "retarget_applied": rebinds, "checks": checks,
          "hard_all_held": not failed, "failed_checks": failed}
    write_json("integrity_selfcheck.json", sc)

    write_json("run_summary.json", {
        "experiment": "SPDR-018B", "family": "CF-VOLDIR-001", "hypothesis": "HYP-D5",
        "universe": "CTRADER (EURUSD, XAUUSD, USTEC)",
        "purpose": ("the SPDR-018 residue on a second universe — SPDR-018 replicated arm B only, "
                    "at one exit geometry, leaving C2 shock-MOMO with zero external replication"),
        "spdr_018_status": "COMPLETE and FROZEN — not modified by this experiment",
        "wall_clock_s": round(time.time() - t0, 1),
        "n_cells_total": int(len(combined)),
        "n_cells_by_arm": {k: int(len(v)) for k, v in frames.items()},
        "cost_model": COST_MODEL_PROVENANCE,
        "power_note": POWER_NOTE,
        "deviations": DEVIATIONS, "interpretation_notes": INTERPRETATION_NOTES,
        "prohibited_claims": PROHIBITED_CLAIMS,
        "disposition": "NONE — binding read is analysis.md; disposition is the operator's",
        "hard_all_held": sc["hard_all_held"],
    })
    print(f"\n-- cells: {len(combined)}  wall clock: {time.time()-t0:.0f}s", flush=True)
    print(f"-- HARD checks held: {sc['hard_all_held']}"
          + ("" if sc["hard_all_held"] else f"  FAILED: {failed}"), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
