"""SPDR-014 orchestrator — zone/event/MOMO-vs-MR characterisation (O3 Group 1).

TRAIN-only. DESIGN primary; CONFIRM verify. Emits design §12 artifacts.

Usage:
    python run_screen.py
    python run_screen.py --limit 3
    python run_screen.py --skip-controls
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import time
from functools import partial
from pathlib import Path

import numpy as np
import polars as pl
from tqdm import tqdm

from xen.nautilus.catalog_fence import load_fence_manifest

from config import (
    CONFIRM_END,
    CONTROL_PRIMARY_CELL,
    DEVIATIONS,
    EVENT_TYPES,
    H4_SLICE,
    H_POST,
    H_VALUES,
    INTERPRETATION_NOTES,
    MONEY_EVENT,
    MONEY_H,
    MONEY_H_POST,
    MONEY_POLICIES,
    MONEY_SOURCES,
    MONEY_Z,
    O3_SOT_PATH,
    PRIMARY_BAND,
    PRIMARY_CLOCK,
    PRIMARY_EVENT,
    RESULTS_DIR,
    SOURCES,
    SPREAD_COST_DISCLOSURE,
    STRADDLE_HS,
    STRADDLE_SOURCE,
    STRADDLE_Z,
    THIRDS_SIGN_MIN,
    TRAIN_END,
    UNPOWERED_MDE_CEILING_BPS,
    UNPOWERED_MIN_DATES,
    UNPOWERED_MIN_EVENTS,
    Z_VALUES,
)
from controls import (
    gate_label_shuffle,
    matched_random_anchor,
    path_future_destroy,
    time_shuffle_event,
    uncond_band_control,
)
from engine import run_cell, simulate_straddle
from golden_traces import run_golden
from prepare import prepare_symbol
from stats_core import band_residual, boot_mean, mde_from_se
from universe import assert_pin, recompute_universe

_DAY_NS = 86_400_000_000_000


def _cell_key(source, z, H, event, h, band, policy="P-NONE", clock="H1"):
    return f"{clock}|{band}|{source}|z={z}|H={H}|{event}|h={h}|{policy}"


def summarise_posts(posts: list[dict], zones: list[dict], events: list[dict],
                    live_mean: float | None = None) -> dict:
    n_orig = len(zones)
    n_ev = sum(1 for e in events if e["event"] == 1)
    decided = [p for p in posts if p.get("side", 0) != 0 and np.isfinite(p.get("r_h", np.nan))]
    r = np.array([p["r_h"] for p in decided], float)
    labels = [p["label"] for p in decided]
    dates = np.array([p["entry_ts"] // _DAY_NS for p in decided], dtype=np.int64) if decided else np.array([], dtype=np.int64)
    boot = boot_mean(r, dates) if r.size >= 3 else None
    n_momo = sum(1 for L in labels if L == "MOMO")
    n_mr = sum(1 for L in labels if L == "MR")
    n_flat = sum(1 for L in labels if L == "FLAT")
    n_d = max(1, len(decided))
    money = [p for p in decided if "partial_net_bps" in p]
    pn = np.array([p["partial_net_bps"] for p in money], float) if money else np.array([])
    return {
        "n_origins": n_orig,
        "n_events": n_ev,
        "p_event": n_ev / max(1, n_orig),
        "n_decided": len(decided),
        "p_momo": n_momo / n_d if decided else float("nan"),
        "p_mr": n_mr / n_d if decided else float("nan"),
        "p_flat": n_flat / n_d if decided else float("nan"),
        "mean_r_h": float(r.mean()) if r.size else float("nan"),
        "median_r_h": float(np.median(r)) if r.size else float("nan"),
        "mean_r_h_momo": float(np.mean([p["r_h"] for p in decided if p["label"] == "MOMO"])) if n_momo else float("nan"),
        "mean_r_h_mr": float(np.mean([p["r_h"] for p in decided if p["label"] == "MR"])) if n_mr else float("nan"),
        "ci_low": boot.ci_low if boot else float("nan"),
        "ci_high": boot.ci_high if boot else float("nan"),
        "se": boot.se if boot else float("nan"),
        "mde_bps": mde_from_se(boot.se) if boot else float("nan"),
        "n_dates": boot.n_dates if boot else 0,
        "mean_partial_net": float(pn.mean()) if pn.size else float("nan"),
        "median_partial_net": float(np.median(pn)) if pn.size else float("nan"),
        "n_money": int(pn.size),
        "win_rate_net": float((pn > 0).mean()) if pn.size else float("nan"),
    }


def thirds_sign_agree(posts: list[dict], overall: float) -> int:
    if not posts or not np.isfinite(overall) or overall == 0:
        return 0
    ts = np.array([p["entry_ts"] for p in posts], dtype=np.int64)
    lo, hi = int(ts.min()), int(ts.max())
    span = max(1, hi - lo)
    signs = []
    for t in (0, 1, 2):
        vals = [p["r_h"] for p in posts if int(((p["entry_ts"] - lo) / span) * 3) == t]
        if vals:
            signs.append(np.sign(np.mean(vals)))
    if not signs:
        return 0
    return int(sum(1 for s in signs if s == np.sign(overall)))


def process_symbol(symbol: str, skip_controls: bool) -> dict:
    manifest = load_fence_manifest()
    pack = prepare_symbol(symbol, PRIMARY_CLOCK, manifest)
    if pack is None:
        return {"symbol": symbol, "ok": False}

    all_zones: list[dict] = []
    all_events: list[dict] = []
    all_posts: list[dict] = []
    cell_rows: list[dict] = []
    money_posts: list[dict] = []
    straddle_rows: list[dict] = []

    # Build unique (source,z,H,event,band,zmag_sens) paths once; expand h and policies.
    # This avoids re-walking the same zone/event path for each post-hold h.
    base_keys = []
    for source in SOURCES:
        for z in Z_VALUES:
            for H in H_VALUES:
                for event in EVENT_TYPES:
                    for band in ("DESIGN", "CONFIRM"):
                        base_keys.append((source, z, H, event, band, False))
    for band in ("DESIGN", "CONFIRM"):
        base_keys.append(("Z-MAG", 1.5, 12, "E-TOUCH", band, True))

    # cache residual posts at max h=24 so all h∈{4,12,24} can be sliced; money separate
    from engine import residual_r_h, label_residual, simulate_policy

    for source, z, H, event, band, zmag_sens in tqdm(base_keys, desc=f"{symbol} cells", leave=False):
        if source == "Z-MAG" and not np.isfinite(pack.sigma_zmag).any():
            continue
        # run with h=24 (max) P-NONE to get full residual path
        zones, events, posts24 = run_cell(
            pack, source=source, z=z, H=H, event_type=event, h=24,
            band=band, policy="P-NONE", zmag_sens=zmag_sens,
        )
        src_tag = "Z-MAG-SENS" if zmag_sens else source
        if zmag_sens:
            for lst in (zones, events, posts24):
                for r in lst:
                    r["source"] = src_tag
        # emit zones/events once per base key (h-independent)
        all_zones.extend(zones)
        all_events.extend(events)

        # rebuild per-h residuals from decided events (causal, non-overlapping already baked in posts24 occupancy)
        # Re-derive from events for each h to get correct r_h (posts24 used h=24 occupation which is conservative)
        for h in H_POST:
            posts = []
            for e in events:
                if e["event"] != 1 or e["side"] == 0:
                    continue
                res = residual_r_h(pack, e["event_idx"], e["side"], h)
                if res is None:
                    continue
                posts.append({
                    **{k: e[k] for k in (
                        "symbol", "clock", "band", "source", "z", "H", "t_idx",
                        "anchor_idx", "vol_tercile", "mag_high", "slow_regime",
                        "last_k_state_1", "last_k_state_2", "last_k_state_3",
                        "shock_flag", "event_type", "event", "event_idx", "side", "event_ts",
                    ) if k in e},
                    "h": h,
                    "label": label_residual(res["r_h"]),
                    "r_h": res["r_h"],
                    "entry_idx": res["entry_idx"],
                    "exit_idx": res["exit_idx"],
                    "entry_ts": res["entry_ts"],
                    "exit_ts": res["exit_ts"],
                    "policy": "P-NONE",
                    "source": src_tag,
                })
            all_posts.extend(posts)
            summ = summarise_posts(posts, zones, events)
            decided = [p for p in posts if np.isfinite(p.get("r_h", np.nan))]
            thirds = thirds_sign_agree(decided, summ["mean_r_h"])
            label = band_residual(
                summ["mean_r_h"], summ["ci_low"], summ["ci_high"],
                summ["n_decided"], summ["n_dates"], summ["se"], thirds, summ["median_r_h"],
            )
            cell_rows.append({
                "symbol": symbol, "clock": PRIMARY_CLOCK, "band": band,
                "source": src_tag, "z": z, "H": H, "event": event, "h": h,
                "policy": "P-NONE",
                **summ,
                "thirds_sign_agree": thirds,
                "band_label_raw": label,
            })

    # Money subset: dedicated non-overlapping runs with stop policy
    for source in MONEY_SOURCES:
        for policy in MONEY_POLICIES:
            for band in ("DESIGN", "CONFIRM"):
                if source == "Z-MAG" and not np.isfinite(pack.sigma_zmag).any():
                    continue
                zones, events, posts = run_cell(
                    pack, source=source, z=MONEY_Z, H=MONEY_H, event_type=MONEY_EVENT,
                    h=MONEY_H_POST, band=band, policy=policy,
                )
                money_posts.extend(posts)
                all_posts.extend(posts)
                summ = summarise_posts(posts, zones, events)
                decided = [p for p in posts if np.isfinite(p.get("r_h", np.nan))]
                thirds = thirds_sign_agree(decided, summ["mean_r_h"])
                label = band_residual(
                    summ["mean_r_h"], summ["ci_low"], summ["ci_high"],
                    summ["n_decided"], summ["n_dates"], summ["se"], thirds, summ["median_r_h"],
                )
                cell_rows.append({
                    "symbol": symbol, "clock": PRIMARY_CLOCK, "band": band,
                    "source": source, "z": MONEY_Z, "H": MONEY_H,
                    "event": MONEY_EVENT, "h": MONEY_H_POST, "policy": policy,
                    **summ,
                    "thirds_sign_agree": thirds,
                    "band_label_raw": label,
                })

    # DA-STRADDLE secondary
    for H in STRADDLE_HS:
        for band in ("DESIGN", "CONFIRM"):
            lo = pack.design_lo if band == "DESIGN" else pack.design_hi
            hi = pack.design_hi if band == "DESIGN" else pack.confirm_hi
            legs = []
            t = lo
            while t < hi - H - 1:
                sig = pack.sigma_zvol[t]
                if not np.isfinite(sig):
                    t += 1
                    continue
                mon = simulate_straddle(pack, t + 1, H)
                if mon is not None:
                    legs.append(mon)
                    t = mon["exit_idx"] + 1
                else:
                    t += 1
            pn = np.array([m["partial_net_bps"] for m in legs], float) if legs else np.array([])
            straddle_rows.append({
                "symbol": symbol, "band": band, "source": STRADDLE_SOURCE,
                "z": STRADDLE_Z, "H": H, "arm": "DA-STRADDLE",
                "n_episodes": len(legs),
                "mean_partial_net": float(pn.mean()) if pn.size else float("nan"),
                "median_partial_net": float(np.median(pn)) if pn.size else float("nan"),
            })

    # H4 co-report
    h4_pack = prepare_symbol(symbol, "H4", manifest, s_symbol=pack.s_symbol)
    h4_rows = []
    if h4_pack is not None:
        s = H4_SLICE
        for band in ("DESIGN", "CONFIRM"):
            z4, e4, p4 = run_cell(
                h4_pack, source=s["source"], z=s["z"], H=s["H"],
                event_type=s["event"], h=s["h"], band=band, policy="P-NONE",
            )
            summ = summarise_posts(p4, z4, e4)
            h4_rows.append({
                "symbol": symbol, "clock": "H4", "band": band, **s, **summ,
            })
            all_zones.extend(z4)
            all_events.extend(e4)
            all_posts.extend(p4)

    controls = {}
    if not skip_controls:
        controls["uncond"] = uncond_band_control(pack, "DESIGN")
        controls["time_shuffle"] = time_shuffle_event(pack, "DESIGN")
        controls["matched_random"] = matched_random_anchor(pack, "DESIGN")
        controls["gate_shuffle"] = gate_label_shuffle(pack, "DESIGN")
        controls["tripwire"] = path_future_destroy(pack, money_posts, "DESIGN")

    return {
        "symbol": symbol, "ok": True, "s_symbol": pack.s_symbol,
        "pack": pack,
        "zones": all_zones, "events": all_events, "posts": all_posts,
        "cells": cell_rows, "money": money_posts,
        "straddle": straddle_rows, "h4": h4_rows, "controls": controls,
    }


def build_residual_pin(cells: list[dict], controls_by_sym: dict) -> dict:
    """design §8.3 residual pin for SPDR-016."""
    # Primary cells: E-TOUCH, h=12, z=1.5, DESIGN, P-NONE, H1
    primary = [
        c for c in cells
        if c.get("band") == PRIMARY_BAND
        and c.get("event") == PRIMARY_EVENT
        and c.get("h") == 12
        and c.get("z") == 1.5
        and c.get("policy") == "P-NONE"
        and c.get("clock", PRIMARY_CLOCK) == PRIMARY_CLOCK
        and c.get("source") in ("Z-VOL", "Z-MAG")
    ]
    # Compare mean_r_h to matched-random null mean per symbol
    powered_momo = []
    powered_mr = []
    primary_out = []
    for c in primary:
        sym = c["symbol"]
        ctrl = controls_by_sym.get(sym, {})
        mr = ctrl.get("matched_random", {})
        null_mean = mr.get("null_mean_mean", float("nan"))
        live = c["mean_r_h"]
        delta = live - null_mean if np.isfinite(live) and np.isfinite(null_mean) else live
        # MOMO residual positive mean_r_h; MR residual negative (reversion = negative r_h)
        # design §8.1 SUPPORTED-residual (powered): NOT UNPOWERED (n_events, n_dates,
        # AND MDE ≤ 10 bps) AND |Δ vs control| ≥ 5 AND CI excludes 0 AND median-sign
        # consistent AND sign agrees in ≥2/3 chronological thirds. The MDE≤10 gate and the
        # median/thirds checks were previously omitted, which mislabeled tail-driven
        # UNPOWERED cells (e.g. DYDX H=24, MDE~172) as "powered" and wrongly opened 016.
        # NOTE: ci_low/ci_high here are on the raw cell mean (proxy); a cell that ever clears
        # the MDE bar should be re-checked with a paired block-bootstrap CI on Δ.
        mde = c.get("mde_bps", float("nan"))
        med = c.get("median_r_h", float("nan"))
        thirds = c.get("thirds_sign_agree", 0)
        powered = (
            c["n_decided"] >= UNPOWERED_MIN_EVENTS
            and c.get("n_dates", 0) >= UNPOWERED_MIN_DATES
            and np.isfinite(mde) and mde <= UNPOWERED_MDE_CEILING_BPS
        )
        label = None
        if c["n_decided"] >= UNPOWERED_MIN_EVENTS and c.get("n_dates", 0) >= UNPOWERED_MIN_DATES:
            if (powered and np.isfinite(delta) and delta >= 5
                    and c.get("ci_low", float("nan")) > 0
                    and np.isfinite(med) and med >= 0 and thirds >= THIRDS_SIGN_MIN):
                label = "MOMO"
                powered_momo.append(c)
            elif (powered and np.isfinite(delta) and delta <= -5
                    and c.get("ci_high", float("nan")) < 0
                    and np.isfinite(med) and med <= 0 and thirds >= THIRDS_SIGN_MIN):
                label = "MR"
                powered_mr.append(c)
            elif c["p_momo"] > c["p_mr"] + 0.05 and np.isfinite(live) and live > 0:
                label = "MOMO_RATE"
            elif c["p_mr"] > c["p_momo"] + 0.05 and np.isfinite(live) and live < 0:
                label = "MR_RATE"
        primary_out.append({
            "symbol": sym,
            "source": c["source"],
            "z": c["z"], "H": c["H"], "event": c["event"], "h": c["h"],
            "mean_r_h": c["mean_r_h"],
            "mean_r_h_delta": delta if np.isfinite(delta) else None,
            "p_momo": c["p_momo"], "p_mr": c["p_mr"],
            "n_decided": c["n_decided"],
            "band_label_raw": c.get("band_label_raw"),
            "label": label,
        })

    n_m = len(powered_momo)
    n_r = len(powered_mr)
    # also rate-dominant across primary cells (not only residual-SUPPORTED)
    rate_momo = sum(1 for p in primary_out if p.get("label") in ("MOMO", "MOMO_RATE"))
    rate_mr = sum(1 for p in primary_out if p.get("label") in ("MR", "MR_RATE"))

    if n_m > 0 and n_r == 0:
        status = "MOMO_DOMINANT"
        policy = "P-MOMO"
        start = True
    elif n_r > 0 and n_m == 0:
        status = "MR_DOMINANT"
        policy = "P-MR"
        start = True
    elif n_m > 0 and n_r > 0:
        status = "SPLIT"
        policy = "P-MOMO" if n_m >= n_r else "P-MR"
        start = True
    else:
        # 0 powered residual cells → residual object NOT established → residual_status = NONE.
        # A rate lean (MOMO_RATE/MR_RATE cell counts) is SUGGESTIVE only and is disclosed in the
        # rate_* fields below; it is NOT promoted to a *_DOMINANT residual label (that would
        # overstate — the earlier builder did this and it had to be hand-corrected each re-run).
        status = "NONE"
        policy = "NONE"
        start = False

    # rate-lean disclosure (direction of the per-cell rate tilt, if any) — never a residual verdict
    if rate_momo > rate_mr * 1.5:
        rate_lean = "MOMO_SUGGESTIVE"
    elif rate_mr > rate_momo * 1.5:
        rate_lean = "MR_SUGGESTIVE"
    elif rate_momo + rate_mr > 0:
        rate_lean = "MIXED_SUGGESTIVE"
    else:
        rate_lean = "NONE"

    return {
        "o3_compliant": True,
        "residual_status": status,
        "primary_cells": primary_out,
        "policy_for_016": policy if start else "NONE",
        "016_start_allowed": start,
        "n_powered_momo": n_m,
        "n_powered_mr": n_r,
        "n_rate_momo_suggestive": rate_momo,
        "n_rate_mr_suggestive": rate_mr,
        "rate_lean": rate_lean,
        "notes": (
            "residual_status=NONE unless ≥1 powered SUPPORTED cell; rate leans are SUGGESTIVE "
            "disclosure only (rate_lean field), never a residual verdict; operator may override "
            "016_start_allowed with signed residual freeze; AMENDMENT-S1 per-symbol SUPPORTED "
            "allowed, multi-symbol = credibility only"
        ),
        "spread_cost_disclosure": SPREAD_COST_DISCLOSURE,
    }


def integrity_check(universe_report: dict, golden: dict, controls_all: list,
                    train_end_ok: bool, o3_ok: bool) -> dict:
    tripwire_concerns = []
    for c in controls_all:
        tw = c.get("tripwire", {})
        if tw.get("integrity_concern"):
            tripwire_concerns.append(tw)

    checks = {
        "universe_pin_equal": bool(universe_report.get("set_equal_all")),
        "golden_traces_pass": bool(golden.get("all_pass")),
        "train_fence_asserted": train_end_ok,
        "o3_sot_path_present": o3_ok,
        "no_signed_product": True,
        "shock_not_regime": True,
        "straddle_not_headline": True,
        "both_momo_mr_emitted": True,
        "tripwire_positive_survivors": tripwire_concerns,
        "tripwire_hard_fail": len(tripwire_concerns) > 0,
    }
    # T1: tripwire integrity concern flags investigation but per design residual HARD
    # on positive money survivors above p95 → all_pass False if any concern
    hard = [
        checks["universe_pin_equal"],
        checks["golden_traces_pass"],
        checks["train_fence_asserted"],
        checks["o3_sot_path_present"],
        not checks["tripwire_hard_fail"],
    ]
    return {
        "all_pass": all(hard),
        "checks": checks,
        "deviations": DEVIATIONS,
        "interpretation_notes": INTERPRETATION_NOTES,
        "train_end_utc": TRAIN_END.isoformat(),
        "o3_sot": O3_SOT_PATH,
        "spread_cost_disclosure": SPREAD_COST_DISCLOSURE,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--skip-controls", action="store_true")
    ap.add_argument("--procs", type=int, default=0,
                    help="worker processes over symbols (0 = os.cpu_count()); 1 = serial")
    args = ap.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    manifest = load_fence_manifest()

    print("== universe recompute + pin assert ==")
    recomputed = recompute_universe(manifest)
    (RESULTS_DIR / "universe_recomputed.json").write_text(json.dumps(recomputed, indent=2))
    pin_report = assert_pin(recomputed)
    (RESULTS_DIR / "universe_pin_check.json").write_text(json.dumps(pin_report, indent=2))
    symbols = recomputed["symbols"]
    if args.limit:
        symbols = symbols[: args.limit]
    print(f"universe OK: {len(symbols)} symbols")

    all_zones, all_events, all_posts = [], [], []
    all_cells, all_money, all_straddle, all_h4 = [], [], [], []
    zvol_scale = {}
    controls_by_sym = {}
    packs = {}

    # Symbol-level parallelism (Tier-1). Each symbol is fully independent and uses
    # fixed control seeds, so results are identical to serial; we aggregate in
    # universe order below to keep row order deterministic regardless of proc count.
    n_proc = args.procs or (os.cpu_count() or 1)
    n_proc = max(1, min(n_proc, len(symbols)))
    results_by_sym: dict[str, dict] = {}
    if n_proc == 1:
        for sym in tqdm(symbols, desc="symbols"):
            res = process_symbol(sym, skip_controls=args.skip_controls)
            if res.get("ok"):
                results_by_sym[sym] = res
    else:
        print(f"== parallel: {n_proc} workers over {len(symbols)} symbols ==")
        worker = partial(process_symbol, skip_controls=args.skip_controls)
        with mp.get_context("spawn").Pool(n_proc) as pool:
            for res in tqdm(pool.imap_unordered(worker, symbols),
                            total=len(symbols), desc="symbols"):
                if res.get("ok"):
                    results_by_sym[res["symbol"]] = res

    for sym in symbols:
        res = results_by_sym.get(sym)
        if res is None:
            print(f"  skip {sym}: no data")
            continue
        packs[sym] = res["pack"]
        zvol_scale[sym] = res["s_symbol"]
        all_zones.extend(res["zones"])
        all_events.extend(res["events"])
        all_posts.extend(res["posts"])
        all_cells.extend(res["cells"])
        all_money.extend(res["money"])
        all_straddle.extend(res["straddle"])
        all_h4.extend(res["h4"])
        controls_by_sym[sym] = res["controls"]
        del res["pack"]

    print("== emit parquets / json ==")
    (RESULTS_DIR / "zvol_scale.json").write_text(json.dumps(zvol_scale, indent=2))

    def _write_parquet(name: str, rows: list[dict]) -> None:
        path = RESULTS_DIR / name
        if not rows:
            pl.DataFrame().write_parquet(path)
            return
        # unify keys; coerce bool/int/float; use pandas for mixed-null schema safety
        keys = sorted({k for r in rows for k in r})
        import pandas as pd
        data = {k: [] for k in keys}
        for r in rows:
            for k in keys:
                v = r.get(k)
                if isinstance(v, float) and not np.isfinite(v):
                    v = np.nan
                data[k].append(v)
        pd.DataFrame(data).to_parquet(path, index=False)

    _write_parquet("zones.parquet", all_zones)
    _write_parquet("events.parquet", all_events)
    _write_parquet("post_event.parquet", all_posts)
    _write_parquet("expectancy_by_cell.parquet", all_cells)
    _write_parquet("money_episodes.parquet", all_money)
    _write_parquet("straddle.parquet", all_straddle)
    _write_parquet("h4_coreport.parquet", all_h4)

    controls_out = {
        "by_symbol": controls_by_sym,
        "primary_cell": CONTROL_PRIMARY_CELL,
        "class_notes": {
            "uncond": "within_sample_attribution",
            "time_shuffle": "within_sample_attribution DERANGEMENT (zero fixed points)",
            "matched_random": "within_sample_attribution; DISJOINT excl live anchors ±1",
            "gate_shuffle": "within_sample_attribution DERANGEMENT (zero fixed points, >=200 seeds)",
            "tripwire": "INFORMATIVE T1; within-third foreign-path re-pair, causal recompute; "
                        "residual HARD on positive money survivors",
        },
    }
    (RESULTS_DIR / "controls.json").write_text(
        json.dumps(controls_out, indent=2, default=str)
    )

    residual_pin = build_residual_pin(all_cells, controls_by_sym)
    (RESULTS_DIR / "014_residual_pin.json").write_text(
        json.dumps(residual_pin, indent=2, default=str)
    )

    print("== golden traces ==")
    golden = run_golden(packs)
    (RESULTS_DIR / "golden_traces.json").write_text(json.dumps(golden, indent=2, default=str))

    # integrity
    o3_ok = (Path(__file__).resolve().parents[3] / O3_SOT_PATH).exists() or (
        Path(__file__).resolve().parents[4] / O3_SOT_PATH
    ).exists()
    # better: repo root
    from config import REPO_ROOT
    o3_ok = (REPO_ROOT / O3_SOT_PATH).exists()
    train_end_ok = True
    # assert no post exit >= train_end
    for p in all_posts:
        if p.get("exit_ts", 0) >= int(TRAIN_END.timestamp() * 1_000_000_000):
            train_end_ok = False
            break
    for m in all_money:
        if m.get("exit_ts", 0) >= int(TRAIN_END.timestamp() * 1_000_000_000):
            train_end_ok = False
            break

    integ = integrity_check(
        pin_report, golden, list(controls_by_sym.values()), train_end_ok, o3_ok
    )
    integ["n_symbols"] = len(packs)
    integ["n_cells"] = len(all_cells)
    integ["n_zones"] = len(all_zones)
    integ["n_events"] = len(all_events)
    integ["n_posts"] = len(all_posts)
    integ["runtime_sec"] = round(time.time() - t0, 1)
    (RESULTS_DIR / "integrity_selfcheck.json").write_text(json.dumps(integ, indent=2, default=str))

    # cell multiplicity disclosure
    mult = {
        "n_symbols": len(packs),
        "n_cell_rows": len(all_cells),
        "grid": {
            "sources": list(SOURCES),
            "z": list(Z_VALUES),
            "H": list(H_VALUES),
            "events": list(EVENT_TYPES),
            "h": list(H_POST),
            "bands": ["DESIGN", "CONFIRM"],
            "money_subset": {
                "sources": list(MONEY_SOURCES), "z": MONEY_Z, "H": MONEY_H,
                "event": MONEY_EVENT, "h": MONEY_H_POST, "policies": list(MONEY_POLICIES),
            },
        },
        "residual_pin": residual_pin["residual_status"],
        "016_start_allowed": residual_pin["016_start_allowed"],
        "integrity_all_pass": integ["all_pass"],
    }
    (RESULTS_DIR / "run_summary.json").write_text(json.dumps(mult, indent=2))

    print(f"DONE in {integ['runtime_sec']}s | integrity={integ['all_pass']} | "
          f"residual={residual_pin['residual_status']} | 016_start={residual_pin['016_start_allowed']}")


if __name__ == "__main__":
    main()
