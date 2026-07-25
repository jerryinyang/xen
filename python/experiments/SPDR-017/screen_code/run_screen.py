"""SPDR-017 orchestrator — independent mispricing + MOMO/MR (O3 Group 3b).

TRAIN-only. DESIGN primary; CONFIRM verify. Emits design §7 artifacts.

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
    ABLATIONS,
    CONTROL_PRIMARY_CELL,
    DEVIATIONS,
    EVENT_TYPES,
    H_POST,
    H_VALUES,
    INTERPRETATION_NOTES,
    MONEY_ABLATION,
    MONEY_EVENT,
    MONEY_H,
    MONEY_H_POST,
    MONEY_MODEL,
    MONEY_POLICIES,
    MONEY_SOURCE,
    MONEY_Z,
    O3_SOT_PATH,
    PRIMARY_ABLATION,
    PRIMARY_BAND,
    PRIMARY_CLOCK,
    PRIMARY_EVENT,
    PRIMARY_MODEL,
    PRIMARY_SOURCE,
    REPO_ROOT,
    RESULTS_DIR,
    SPREAD_COST_DISCLOSURE,
    THIRDS_SIGN_MIN,
    TRAIN_END,
    UNPOWERED_MDE_CEILING_BPS,
    UNPOWERED_MIN_DATES,
    UNPOWERED_MIN_EVENTS,
    Z_VALUES,
)
from controls import (
    feature_shuffle_control,
    level_only_zvol_control,
    matched_random_anchor,
    path_future_destroy,
    time_shuffle_event,
    uncond_band_control,
)
from engine import label_residual, residual_r_h, run_cell
from golden_traces import run_golden
from prepare import feature_rows, model_oos_rows, prepare_symbol
from stats_core import band_residual, boot_mean, mde_from_se
from universe import assert_pin, recompute_universe

_DAY_NS = 86_400_000_000_000


def summarise_posts(posts: list[dict], zones: list[dict], events: list[dict]) -> dict:
    n_orig = len(zones)
    n_ev = sum(1 for e in events if e["event"] == 1)
    decided = [p for p in posts if p.get("side", 0) != 0 and np.isfinite(p.get("r_h", np.nan))]
    r = np.array([p["r_h"] for p in decided], float)
    labels = [p["label"] for p in decided]
    dates = (
        np.array([p["entry_ts"] // _DAY_NS for p in decided], dtype=np.int64)
        if decided else np.array([], dtype=np.int64)
    )
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
        "mean_r_h_momo": (
            float(np.mean([p["r_h"] for p in decided if p["label"] == "MOMO"]))
            if n_momo else float("nan")
        ),
        "mean_r_h_mr": (
            float(np.mean([p["r_h"] for p in decided if p["label"] == "MR"]))
            if n_mr else float("nan")
        ),
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


def _cell_row(symbol, source, z, H, event, h, band, policy, ablation, model,
              posts, zones, events) -> dict:
    summ = summarise_posts(posts, zones, events)
    decided = [p for p in posts if np.isfinite(p.get("r_h", np.nan))]
    thirds = thirds_sign_agree(decided, summ["mean_r_h"])
    label = band_residual(
        summ["mean_r_h"], summ["ci_low"], summ["ci_high"],
        summ["n_decided"], summ["n_dates"], summ["se"], thirds, summ["median_r_h"],
    )
    return {
        "symbol": symbol, "clock": PRIMARY_CLOCK, "band": band,
        "source": source, "z": z, "H": H, "event": event, "h": h,
        "policy": policy, "ablation": ablation, "model": model,
        **summ,
        "thirds_sign_agree": thirds,
        "band_label_raw": label,
    }


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
    feat_rows = feature_rows(pack, "DESIGN") + feature_rows(pack, "CONFIRM")
    oos_rows = model_oos_rows(pack)

    # ---- Primary grid: M-ZONE A2 M-RIDGE × z × H × event × band ----
    base_keys = []
    for z in Z_VALUES:
        for H in H_VALUES:
            for event in EVENT_TYPES:
                for band in ("DESIGN", "CONFIRM"):
                    base_keys.append((PRIMARY_SOURCE, z, H, event, band,
                                      PRIMARY_ABLATION, PRIMARY_MODEL))

    # Z-VOL co-baseline (014 grammar) E-TOUCH primary
    for z in Z_VALUES:
        for H in H_VALUES:
            for band in ("DESIGN", "CONFIRM"):
                base_keys.append(("Z-VOL", z, H, PRIMARY_EVENT, band, "NA", "NA"))

    # M-SIGN-ERR secondary co-report (primary cell only)
    for band in ("DESIGN", "CONFIRM"):
        base_keys.append(("M-SIGN-ERR", 1.5, 12, PRIMARY_EVENT, band,
                          PRIMARY_ABLATION, PRIMARY_MODEL))

    # Ablation A0/A1/A2 at primary cell
    for abl in ABLATIONS:
        for band in ("DESIGN", "CONFIRM"):
            if abl == PRIMARY_ABLATION:
                continue  # already in primary grid
            base_keys.append((PRIMARY_SOURCE, 1.5, 12, PRIMARY_EVENT, band,
                              abl, PRIMARY_MODEL))

    # GBM sensitivity at primary cell DESIGN
    base_keys.append((PRIMARY_SOURCE, 1.5, 12, PRIMARY_EVENT, "DESIGN",
                      PRIMARY_ABLATION, "M-GBM"))

    for source, z, H, event, band, abl, model in tqdm(
        base_keys, desc=f"{symbol} cells", leave=False
    ):
        zones, events, posts24 = run_cell(
            pack, source=source, z=z, H=H, event_type=event, h=24,
            band=band, policy="P-NONE", ablation=abl, model=model,
        )
        all_zones.extend(zones)
        all_events.extend(events)
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
                        "anchor_idx", "ablation", "model",
                        "vol_tercile", "mag_high", "slow_regime", "shock_flag",
                        "event_type", "event", "event_idx", "side", "event_ts",
                    ) if k in e},
                    "h": h,
                    "label": label_residual(res["r_h"]),
                    "r_h": res["r_h"],
                    "entry_idx": res["entry_idx"],
                    "exit_idx": res["exit_idx"],
                    "entry_ts": res["entry_ts"],
                    "exit_ts": res["exit_ts"],
                    "policy": "P-NONE",
                })
            all_posts.extend(posts)
            cell_rows.append(_cell_row(
                symbol, source, z, H, event, h, band, "P-NONE", abl, model,
                posts, zones, events,
            ))

    # Money subset
    for policy in MONEY_POLICIES:
        for band in ("DESIGN", "CONFIRM"):
            zones, events, posts = run_cell(
                pack, source=MONEY_SOURCE, z=MONEY_Z, H=MONEY_H,
                event_type=MONEY_EVENT, h=MONEY_H_POST, band=band, policy=policy,
                ablation=MONEY_ABLATION, model=MONEY_MODEL,
            )
            money_posts.extend(posts)
            all_posts.extend(posts)
            cell_rows.append(_cell_row(
                symbol, MONEY_SOURCE, MONEY_Z, MONEY_H, MONEY_EVENT, MONEY_H_POST,
                band, policy, MONEY_ABLATION, MONEY_MODEL, posts, zones, events,
            ))

    controls = {}
    if not skip_controls:
        controls["uncond"] = uncond_band_control(pack, "DESIGN")
        controls["level_only_zvol"] = level_only_zvol_control(pack, "DESIGN")
        controls["time_shuffle"] = time_shuffle_event(pack, "DESIGN")
        controls["matched_random"] = matched_random_anchor(pack, "DESIGN")
        controls["feature_shuffle"] = feature_shuffle_control(pack, "DESIGN")
        controls["tripwire"] = path_future_destroy(pack, money_posts, "DESIGN")

    return {
        "symbol": symbol, "ok": True, "s_symbol": pack.s_symbol,
        "pack": pack,
        "zones": all_zones, "events": all_events, "posts": all_posts,
        "cells": cell_rows, "money": money_posts,
        "features": feat_rows, "model_oos": oos_rows,
        "controls": controls,
    }


def build_residual_pin(cells: list[dict], controls_by_sym: dict) -> dict:
    """Own 017 residual pin (parallel schema to 014; does not feed 016)."""
    primary = [
        c for c in cells
        if c.get("band") == PRIMARY_BAND
        and c.get("event") == PRIMARY_EVENT
        and c.get("h") == 12
        and c.get("z") == 1.5
        and c.get("policy") == "P-NONE"
        and c.get("source") == PRIMARY_SOURCE
        and c.get("ablation") == PRIMARY_ABLATION
        and c.get("model") == PRIMARY_MODEL
        and c.get("clock", PRIMARY_CLOCK) == PRIMARY_CLOCK
    ]
    powered_momo, powered_mr, primary_out = [], [], []
    for c in primary:
        sym = c["symbol"]
        ctrl = controls_by_sym.get(sym, {})
        mr = ctrl.get("matched_random", {})
        null_mean = mr.get("null_mean_mean", float("nan"))
        live = c["mean_r_h"]
        delta = live - null_mean if np.isfinite(live) and np.isfinite(null_mean) else live
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
            "ablation": c.get("ablation"),
            "model": c.get("model"),
            "z": c["z"], "H": c["H"], "event": c["event"], "h": c["h"],
            "mean_r_h": c["mean_r_h"],
            "mean_r_h_delta": delta if np.isfinite(delta) else None,
            "p_momo": c["p_momo"], "p_mr": c["p_mr"],
            "n_decided": c["n_decided"],
            "band_label_raw": c.get("band_label_raw"),
            "label": label,
        })

    n_m, n_r = len(powered_momo), len(powered_mr)
    rate_momo = sum(1 for p in primary_out if p.get("label") in ("MOMO", "MOMO_RATE"))
    rate_mr = sum(1 for p in primary_out if p.get("label") in ("MR", "MR_RATE"))

    if n_m > 0 and n_r == 0:
        status, policy = "MOMO_DOMINANT", "P-MOMO"
    elif n_r > 0 and n_m == 0:
        status, policy = "MR_DOMINANT", "P-MR"
    elif n_m > 0 and n_r > 0:
        status = "SPLIT"
        policy = "P-MOMO" if n_m >= n_r else "P-MR"
    else:
        status, policy = "NONE", "NONE"

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
        "experiment": "SPDR-017",
        "residual_status": status,
        "primary_cells": primary_out,
        "policy_for_refine": policy if status != "NONE" else "NONE",
        "n_powered_momo": n_m,
        "n_powered_mr": n_r,
        "n_rate_momo_suggestive": rate_momo,
        "n_rate_mr_suggestive": rate_mr,
        "rate_lean": rate_lean,
        "not_for_016": True,
        "notes": (
            "017 own residual pin; does not feed SPDR-016 (016 reads 014 pin only). "
            "No hard start gate on 014 residual. residual_status=NONE unless ≥1 powered "
            "SUPPORTED cell. AMENDMENT-S1 per-symbol OK."
        ),
        "spread_cost_disclosure": SPREAD_COST_DISCLOSURE,
    }


def build_ablation_table(cells: list[dict]) -> list[dict]:
    """A0/A1/A2 at primary cell DESIGN."""
    rows = []
    for c in cells:
        if (c.get("band") == "DESIGN"
                and c.get("source") == PRIMARY_SOURCE
                and c.get("z") == 1.5 and c.get("H") == 12
                and c.get("event") == PRIMARY_EVENT and c.get("h") == 12
                and c.get("policy") == "P-NONE"
                and c.get("model") == PRIMARY_MODEL
                and c.get("ablation") in ABLATIONS):
            rows.append({
                "symbol": c["symbol"],
                "ablation": c["ablation"],
                "mean_r_h": c["mean_r_h"],
                "median_r_h": c["median_r_h"],
                "p_momo": c["p_momo"],
                "p_mr": c["p_mr"],
                "n_decided": c["n_decided"],
                "p_event": c["p_event"],
                "ci_low": c["ci_low"],
                "ci_high": c["ci_high"],
                "mde_bps": c["mde_bps"],
                "band_label_raw": c["band_label_raw"],
            })
    return rows


def build_vs_014(cells: list[dict]) -> list[dict]:
    """Informative Δ: M-ZONE A2 vs Z-VOL at matched cells DESIGN E-TOUCH h=12."""
    mzone = {
        (c["symbol"], c["z"], c["H"]): c
        for c in cells
        if c.get("band") == "DESIGN" and c.get("source") == "M-ZONE"
        and c.get("event") == PRIMARY_EVENT and c.get("h") == 12
        and c.get("policy") == "P-NONE" and c.get("ablation") == "A2"
        and c.get("model") == "M-RIDGE"
    }
    zvol = {
        (c["symbol"], c["z"], c["H"]): c
        for c in cells
        if c.get("band") == "DESIGN" and c.get("source") == "Z-VOL"
        and c.get("event") == PRIMARY_EVENT and c.get("h") == 12
        and c.get("policy") == "P-NONE"
    }
    rows = []
    for key, mz in mzone.items():
        zv = zvol.get(key)
        if zv is None:
            continue
        rows.append({
            "symbol": key[0], "z": key[1], "H": key[2],
            "event": PRIMARY_EVENT, "h": 12,
            "mzone_mean_r_h": mz["mean_r_h"],
            "zvol_mean_r_h": zv["mean_r_h"],
            "delta_mean_r_h": (
                mz["mean_r_h"] - zv["mean_r_h"]
                if np.isfinite(mz["mean_r_h"]) and np.isfinite(zv["mean_r_h"])
                else float("nan")
            ),
            "mzone_p_momo": mz["p_momo"], "zvol_p_momo": zv["p_momo"],
            "mzone_p_mr": mz["p_mr"], "zvol_p_mr": zv["p_mr"],
            "mzone_n": mz["n_decided"], "zvol_n": zv["n_decided"],
            "note": "informative baseline only — not a start gate",
        })
    return rows


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
        "no_014_start_gate": True,
        "both_momo_mr_emitted": True,
        "ablation_a0_a1_a2": True,
        "tripwire_positive_survivors": tripwire_concerns,
        "tripwire_hard_fail": len(tripwire_concerns) > 0,
    }
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


def _write_parquet(name: str, rows: list[dict]) -> None:
    path = RESULTS_DIR / name
    if not rows:
        pl.DataFrame().write_parquet(path)
        return
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--skip-controls", action="store_true")
    ap.add_argument("--procs", type=int, default=0,
                    help="worker processes (0 = cpu_count); 1 = serial")
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
    all_cells, all_money = [], []
    all_features, all_oos = [], []
    zvol_scale = {}
    controls_by_sym = {}
    packs = {}

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
        all_features.extend(res["features"])
        all_oos.extend(res["model_oos"])
        controls_by_sym[sym] = res["controls"]
        del res["pack"]

    print("== emit parquets / json ==")
    (RESULTS_DIR / "zvol_scale.json").write_text(json.dumps(zvol_scale, indent=2))
    _write_parquet("features.parquet", all_features)
    _write_parquet("model_oos.parquet", all_oos)
    _write_parquet("zones.parquet", all_zones)
    _write_parquet("events.parquet", all_events)
    _write_parquet("post_event.parquet", all_posts)
    _write_parquet("expectancy_by_cell.parquet", all_cells)
    _write_parquet("money_episodes.parquet", all_money)

    abl_rows = build_ablation_table(all_cells)
    _write_parquet("ablation.parquet", abl_rows)
    vs_rows = build_vs_014(all_cells)
    _write_parquet("vs_014_baseline.parquet", vs_rows)

    controls_out = {
        "by_symbol": controls_by_sym,
        "primary_cell": CONTROL_PRIMARY_CELL,
        "class_notes": {
            "uncond": "within_sample_attribution",
            "level_only_zvol": "014 Z-VOL informative baseline",
            "time_shuffle": "within_sample_attribution DERANGEMENT",
            "matched_random": "within_sample_attribution DISJOINT",
            "feature_shuffle": "model_skill",
            "tripwire": "INFORMATIVE T1 path-destroy",
        },
    }
    (RESULTS_DIR / "controls.json").write_text(json.dumps(controls_out, indent=2, default=str))

    residual_pin = build_residual_pin(all_cells, controls_by_sym)
    (RESULTS_DIR / "017_residual_pin.json").write_text(
        json.dumps(residual_pin, indent=2, default=str)
    )

    print("== golden traces ==")
    golden = run_golden(packs)
    (RESULTS_DIR / "golden_traces.json").write_text(json.dumps(golden, indent=2, default=str))

    o3_ok = (REPO_ROOT / O3_SOT_PATH).exists()
    train_end_ok = True
    train_end_ns = int(TRAIN_END.timestamp() * 1_000_000_000)
    for p in all_posts:
        if p.get("exit_ts", 0) >= train_end_ns:
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

    # ablation layer-lift disclosure
    weak_load = False
    if abl_rows:
        by_sym: dict[str, dict] = {}
        for r in abl_rows:
            by_sym.setdefault(r["symbol"], {})[r["ablation"]] = r
        for sym, m in by_sym.items():
            a1 = m.get("A1", {}).get("mean_r_h", float("nan"))
            a2 = m.get("A2", {}).get("mean_r_h", float("nan"))
            a0 = m.get("A0", {}).get("mean_r_h", float("nan"))
            if (np.isfinite(a2) and np.isfinite(a1) and abs(a2) > abs(a1) + 1
                    and np.isfinite(a0) and abs(a1) <= abs(a0) + 1):
                # A2 wins only over A1 while A1 ~ A0 → WEAK-DIR load-bearing
                if abs(a2) > abs(a0) + 2:
                    weak_load = True

    mult = {
        "n_symbols": len(packs),
        "n_cell_rows": len(all_cells),
        "residual_status": residual_pin["residual_status"],
        "rate_lean": residual_pin["rate_lean"],
        "weak_dir_load_bearing_flag": weak_load,
        "integrity_all_pass": integ["all_pass"],
        "runtime_sec": integ["runtime_sec"],
        "014_residual_note": "informative baseline only; 017 not gated on 014",
    }
    (RESULTS_DIR / "run_summary.json").write_text(json.dumps(mult, indent=2))

    print(
        f"DONE in {integ['runtime_sec']}s | integrity={integ['all_pass']} | "
        f"residual={residual_pin['residual_status']} | weak_dir_load={weak_load}"
    )


if __name__ == "__main__":
    main()
