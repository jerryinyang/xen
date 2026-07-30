#!/usr/bin/env python3
"""SPDR-019 orchestrator — phase (a) only, 33 variants, TRAIN-only.

    python run_screen.py --jobs 8
    python run_screen.py --smoke   # 2 symbols, reduced bootstrap

Emits design §15 artifacts. No disposition. Fresh-context analysis.md is stage 5.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from config import (  # noqa: E402
    BOOT_RESAMPLES,
    CLOCKS_RUN,
    CONTROL_N_SEEDS,
    CONTROL_PRIMARY,
    COST_FLOOR_BPS,
    DELTA_THRESHOLDS,
    DERIVED_VARIANTS,
    EXPECTED_RESOLUTION_SHA256,
    NS,
    RESULTS_DIR,
    RESOLUTION_BASIS_SHA256,
    SIZING_VARIANTS,
    SPREAD_COST_DISCLOSURE,
    TRIPWIRE_SYMBOL,
    UNIVERSE_PIN_FAMILY,
    VARIANT_IDS,
)
import controls as controls_mod  # noqa: E402
import engine  # noqa: E402
import golden  # noqa: E402
import integrity  # noqa: E402
import metrics  # noqa: E402
import parent_gates  # noqa: E402
import panel as panel_mod  # noqa: E402
import selection  # noqa: E402
import selfcheck  # noqa: E402
import tripwires  # noqa: E402


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
        if out[c].dtype == object:
            out[c] = out[c].map(
                lambda v: json.dumps(v, default=_json) if isinstance(v, (list, dict)) else v
            )
    out.to_parquet(p, index=False)
    return p


def universe() -> list[str]:
    pin = json.loads(Path(UNIVERSE_PIN_FAMILY).read_text())
    return list(pin["symbols"])


def verify_predeclaration() -> None:
    """HARD: consume committed hashes; never regenerate."""
    def sha(p: Path) -> str:
        h = hashlib.sha256()
        h.update(p.read_bytes())
        return h.hexdigest()

    b = RESULTS_DIR / "resolution_basis.json"
    e = RESULTS_DIR / "expected_resolution.json"
    assert b.exists() and e.exists(), "predeclaration artifacts missing"
    bs, es = sha(b), sha(e)
    assert bs == RESOLUTION_BASIS_SHA256, f"resolution_basis.json hash mismatch: {bs}"
    assert es == EXPECTED_RESOLUTION_SHA256, f"expected_resolution.json hash mismatch: {es}"
    print(f"  predeclaration OK  basis={bs[:16]}…  expected={es[:16]}…", flush=True)


# --------------------------------------------------------------------------- worker
def _process_symbol(task: dict) -> dict:
    """Per-symbol work unit: panels, gates, all (clock, delta, variant) episodes."""
    symbol = task["symbol"]
    n_boot = task.get("n_boot", BOOT_RESAMPLES)
    deltas = task.get("deltas", list(DELTA_THRESHOLDS))
    clocks = task.get("clocks", list(CLOCKS_RUN))
    variants = task.get("variants", list(VARIANT_IDS))
    try:
        bundle = panel_mod.load_symbol_bundle(symbol)
        if bundle is None:
            return {"symbol": symbol, "empty": True, "episodes": [], "signals": [], "parity": {}}

        # attach gates on each clock panel (H1 labels held forward)
        trans = parent_gates._load_015_transitions()
        parity = None
        for clock, pan in bundle["panels"].items():
            parity = parent_gates.attach_gates(pan, symbol, trans_mod=trans)

        episodes = []
        signals = []
        tripwire_base = None
        for clock in clocks:
            if clock not in bundle["panels"]:
                continue
            pan = bundle["panels"][clock]
            for delta in deltas:
                base = engine.base_signals(pan, delta)
                if clock == "H1" and float(delta) == 0.5:
                    tripwire_base = base
                # L0 once; L1–L3 select from it; L4 re-exits the entry stream
                l0_eps, l0_rows, sig_by_key = engine.build_l0_episodes(pan, base)
                l0_cache = (l0_eps, sig_by_key)
                for ep in l0_eps:
                    episodes.append(engine.episode_to_row(ep))
                signals.extend(l0_rows)
                for vid in variants:
                    if vid in DERIVED_VARIANTS or vid == "L0_BASELINE":
                        continue
                    eps, srows = engine.assemble_episodes_for_variant(
                        pan, base, vid, l0_cache=l0_cache,
                    )
                    for ep in eps:
                        episodes.append(engine.episode_to_row(ep))
                    signals.extend(srows)

        unit = {
            "symbol": symbol,
            "s_hat_uncond": bundle["s_hat_uncond"],
            "atr20_median_h1": bundle["atr20_median_h1"],
            "s_symbol_scale": bundle["s_symbol_scale"],
            "n_h1": int(bundle["panels"]["H1"].close.size) if "H1" in bundle["panels"] else 0,
        }
        return {
            "symbol": symbol,
            "empty": False,
            "episodes": episodes,
            "signals": signals,
            "parity": parity or {},
            "unit": unit,
            "n_boot": n_boot,
            "tripwire": (
                _run_tripwires(bundle, tripwire_base) if tripwire_base is not None else {}
            ),
        }
    except Exception as e:
        return {
            "symbol": symbol, "empty": True, "error": repr(e),
            "traceback": traceback.format_exc(),
            "episodes": [], "signals": [],
        }


def _run_tripwires(bundle: dict, base: list) -> dict:
    """Run both §6.1 tripwires against the LIVE pipeline for this symbol.

    Both run on the H1 panel at δ = 0.5 — the golden-trace anchor — so QA can re-derive every
    emitted id from the catalog. Neither may reconstruct its own input: whatever the pipeline
    produces is what the structural conditions are read off (QA run 8, R8-01 / R8-02).
    """
    if "H1" not in bundle["panels"]:
        return {}
    pan = bundle["panels"]["H1"]
    tw1 = tripwires.tripwire_1(pan, base, engine)
    # TRIPWIRE-2 needs a target arm: the 33 variants place a target OR a trail, so the
    # both-reachable population is built by pairing each target episode with the trail its own
    # ŝ device would have set (documented in tripwires.tripwire_2).
    tgt_eps, _ = engine.assemble_episodes_for_variant(pan, base, "L4_TARGET_A1_UNMOD")
    tw2 = tripwires.tripwire_2(pan, tgt_eps)
    return {"symbol": bundle["symbol"], "tripwire_1": tw1, "tripwire_2": tw2}


def run_tasks(tasks: list[dict], jobs: int, *, label: str) -> list[dict]:
    t0 = time.time()
    if jobs <= 1:
        out = []
        for i, t in enumerate(tasks, 1):
            out.append(_process_symbol(t))
            print(f"  [{label}] {i}/{len(tasks)} {t['symbol']} ({time.time()-t0:.0f}s)", flush=True)
        return out
    # polars arm needs spawn (Rust thread pool does not survive fork)
    ctx = mp.get_context("spawn")
    with ctx.Pool(jobs) as pool:
        out = []
        for i, res in enumerate(pool.imap_unordered(_process_symbol, tasks), 1):
            out.append(res)
            print(
                f"  [{label}] {i}/{len(tasks)} {res.get('symbol','?')} ({time.time()-t0:.0f}s)",
                flush=True,
            )
    out = sorted(out, key=lambda r: r.get("symbol", ""))
    return out


SIZING_LOGR_COLUMNS = (
    "log_R", "ci_low", "ci_high", "ci_width", "block_mde", "mirror_band",
    "mde50", "mde80", "mde95", "realised_c", "ladder",
)


def _score_one_cell(args: tuple) -> dict | None:
    """Worker for one cell — pure function of episode arrays."""
    (vid, clock, delta, band, scope, r, ts, exit_ts, hold, symbols, mfe,
     fill_rate, n_signals, n_suppressed, n_ineligible, n_boot) = args
    if r.size == 0:
        return None
    m = metrics.cell_metrics(r, ts, n_boot=n_boot, cost_bps=COST_FLOOR_BPS, mfe=mfe)
    sp = metrics.span_stats(ts, exit_ts, float(hold) if np.isfinite(hold) else 1.0)
    m.update(sp)
    cov = metrics.effective_coverage(ts, symbols)
    m["effective_frac_of_nominal"] = cov.get("effective_frac_of_nominal")
    m["n_symbols_in_cell"] = cov.get("n_symbols")
    m.update({
        "variant_id": vid,
        "clock": clock,
        "delta": float(delta),
        "scope": scope,
        "band": band,
        "evidence_class": "[S]" if scope == "POOLED" and band == "TRAIN" else "[D]",
        "sizing_no_logR_claim": vid in SIZING_VARIANTS,
        "spread_cost_status": SPREAD_COST_DISCLOSURE["spread_cost_status"],
        "fill_rate": fill_rate,
        "n_signals": n_signals,
        "n_suppressed": n_suppressed,
        "n_ineligible": n_ineligible,
        "n_episodes": int(r.size),
        # attached by _attach_control_collapse where a control actually refereed this cell
        "collapse_fraction": None,
        "collapse_fraction_status": "NOT_REFEREED",
    })
    if vid in SIZING_VARIANTS:
        # SoT §4.4 / §13: a sizing cell may not carry a log R claim. Flagging it left the
        # number in the artifact for a reader who ignores the flag; the forbidden claim is
        # now unavailable rather than merely disclosed (QA run 8, R8-25).
        m["sizing_dispersion_sd_bps"] = float(np.std(r, ddof=1)) if r.size > 1 else float("nan")
        m["sizing_dispersion_iqr_bps"] = (
            float(np.percentile(r, 75) - np.percentile(r, 25)) if r.size > 1 else float("nan")
        )
        for col in SIZING_LOGR_COLUMNS:
            m[col] = None
        m["log_R_suppressed_reason"] = "SIZING_VARIANT_MAY_NOT_CARRY_A_LOG_R_CLAIM"
    return m


def _signal_counts(signals: pd.DataFrame) -> dict:
    """Per (variant, clock, delta, scope, band) signal accounting for the §12 fill rate.

    Unfilled and suppressed signals are counted, never dropped — a device that changes the
    fill rate changes the population and would otherwise silently re-select it (§2).
    """
    out: dict = {}
    if signals is None or signals.empty:
        return out
    need = {"variant_id", "clock", "delta", "symbol", "band", "reason"}
    if not need.issubset(signals.columns):
        return out
    for (vid, clock, delta, sym, band), g in signals.groupby(
        ["variant_id", "clock", "delta", "symbol", "band"], dropna=False
    ):
        rec = {
            "n_signals": int(len(g)),
            "n_episodes": int((g["reason"] == "EPISODE").sum()),
            "n_unfilled": int((g["reason"] == "UNFILLED").sum()),
            "n_suppressed": int((g["reason"] == "SUPPRESSED").sum()),
            "n_ineligible": int((g["reason"] == "INELIGIBLE").sum()),
        }
        for scope in (sym, "POOLED"):
            for b in (band, "TRAIN"):
                key = (vid, clock, float(delta), scope, b)
                acc = out.setdefault(key, dict.fromkeys(rec, 0))
                for k, v in rec.items():
                    acc[k] += v
    return out


def _score_cells(
    episodes: pd.DataFrame,
    signals: pd.DataFrame,
    n_boot: int,
    *,
    jobs: int = 1,
) -> list[dict]:
    """Metrics for every (variant, clock, delta, scope, band) cell."""
    if episodes.empty:
        return []
    counts = _signal_counts(signals)
    scopes = ["POOLED"] + sorted(episodes["symbol"].unique().tolist())
    tasks = []
    for vid in VARIANT_IDS:
        if vid in DERIVED_VARIANTS:
            continue
        for clock in CLOCKS_RUN:
            for delta in DELTA_THRESHOLDS:
                base = episodes[
                    (episodes.variant_id == vid)
                    & (episodes.clock == clock)
                    & np.isclose(episodes.delta, delta)
                ]
                if base.empty:
                    continue
                for band, sub in (
                    ("TRAIN", base),
                    ("DESIGN", base[base.band == "DESIGN"]),
                    ("CONFIRM", base[base.band == "CONFIRM"]),
                ):
                    if sub.empty:
                        continue
                    for scope in scopes:
                        cell = sub if scope == "POOLED" else sub[sub.symbol == scope]
                        if cell.empty:
                            continue
                        c = counts.get((vid, clock, float(delta), scope, band), {})
                        n_sig = c.get("n_signals", 0)
                        tasks.append((
                            vid, clock, float(delta), band, scope,
                            cell["r_bps"].to_numpy(dtype=float),
                            cell["fill_ts"].to_numpy(dtype=np.int64),
                            cell["exit_ts"].to_numpy(dtype=np.int64),
                            float(cell["active_hold_hours"].median()),
                            cell["symbol"].to_numpy(),
                            cell["mfe_bps"].to_numpy(dtype=float)
                            if "mfe_bps" in cell.columns else None,
                            (c.get("n_episodes", 0) / n_sig) if n_sig else float("nan"),
                            n_sig,
                            c.get("n_suppressed", 0),
                            c.get("n_ineligible", 0),
                            n_boot,
                        ))
    print(f"  scoring {len(tasks)} cells (jobs={jobs}, n_boot={n_boot})…", flush=True)
    if jobs <= 1:
        rows = []
        for i, t in enumerate(tasks, 1):
            m = _score_one_cell(t)
            if m is not None:
                rows.append(m)
            if i % 200 == 0:
                print(f"    {i}/{len(tasks)}", flush=True)
        return rows
    ctx = mp.get_context("spawn")
    with ctx.Pool(jobs) as pool:
        rows = [m for m in pool.imap_unordered(_score_one_cell, tasks, chunksize=8) if m]
    return rows


def _arm_index(episodes: pd.DataFrame) -> dict:
    """Group the episode frame ONCE by (variant, clock, δ).

    The delta reads ask for a few hundred arms; filtering the whole frame per ask meant
    hundreds of millions of string comparisons over a multi-hundred-thousand-row frame, which
    dominated the stage. Grouping once leaves each later filter working on a few thousand rows.
    """
    if episodes.empty:
        return {}
    return {
        (vid, clock, float(delta)): g
        for (vid, clock, delta), g in episodes.groupby(
            ["variant_id", "clock", "delta"], sort=False
        )
    }


def _arm_arrays(arm_idx: dict, vid, clock, delta, scope, band):
    """(r, ts) for one arm, on the full-TRAIN band or a verification band."""
    g = arm_idx.get((vid, clock, float(delta)))
    if g is None or g.empty:
        return None
    if band != "TRAIN":
        g = g[g["band"] == band]
    if scope != "POOLED":
        g = g[g["symbol"] == scope]
    if g.empty:
        return None
    return (
        g["r_bps"].to_numpy(dtype=float),
        g["fill_ts"].to_numpy(dtype=np.int64),
    )


def _add_interaction_rows(
    metrics_rows: list[dict], arm_idx: dict, n_boot: int
) -> list[dict]:
    """L2_INTERACTION = ΔlogR(joint) − ΔlogR(shock) − ΔlogR(k12), paired-bootstrapped."""
    extra = []
    by = {}
    for r in metrics_rows:
        by[(r.get("clock"), r.get("delta"), r.get("scope"), r.get("band"),
            r.get("variant_id"))] = r
    scopes = {r.get("scope") for r in metrics_rows}
    for clock in CLOCKS_RUN:
        for delta in DELTA_THRESHOLDS:
            for scope in scopes:
                for band in ("TRAIN", "DESIGN", "CONFIRM"):
                    arms = {}
                    for name, vid in (
                        ("l0", "L0_BASELINE"),
                        ("shock", "L2_SHOCK_HMM"),
                        ("k12", "L2_LEVEL_RMARKOV_K12"),
                        ("joint", "L2_JOINT_HMM_HIGH_AND_K12_HIGH"),
                    ):
                        src = by.get((clock, float(delta), scope, band, vid))
                        if src is None:
                            arms = {}
                            break
                        # AMENDMENT-20 eligibility: the interaction of an arm whose own log R is
                        # undefined is undefined. Such a term is NOT BUILT rather than emitted
                        # and then exempted — there is nothing to measure when an input arm has
                        # a one-sided outcome set (QA run 11, R11-03).
                        if not metrics.log_R_is_defined(
                            src.get("p"), src.get("W"), src.get("L")
                        ):
                            arms = {}
                            break
                        a = _arm_arrays(arm_idx, vid, clock, delta, scope, band)
                        if a is None:
                            arms = {}
                            break
                        arms[name] = a
                    if not arms:
                        continue
                    # (joint − L0) − (shock − L0) − (k12 − L0), inside every replicate
                    d = metrics.paired_combo_ci(
                        arms,
                        lambda v: v["joint"] - v["shock"] - v["k12"] + v["l0"],
                        n_boot=n_boot,
                    )
                    # §9 CI-relative band on the interaction row (R9-16)
                    ci_lo, ci_hi = d["ci_low"], d["ci_high"]
                    if np.isfinite(ci_lo) and ci_lo > 0:
                        mirror = "ABOVE_THE_MIRROR"
                    elif np.isfinite(ci_hi) and ci_hi < 0:
                        mirror = "BELOW_THE_MIRROR"
                    else:
                        mirror = "COVERS_THE_MIRROR"
                    extra.append({
                        "variant_id": "L2_INTERACTION_HMM_X_K12",
                        "clock": clock, "delta": float(delta), "scope": scope, "band": band,
                        "log_R": d["delta_log_R"],
                        "ci_low": d["ci_low"],
                        "ci_high": d["ci_high"],
                        "ci_width": d["ci_width"],
                        "block_mde": d["block_mde"],
                        "mirror_band": mirror,
                        "n": by[(clock, float(delta), scope, band,
                                 "L2_JOINT_HMM_HIGH_AND_K12_HIGH")].get("n"),
                        "n_dates": d.get("n_days"),
                        "p": float("nan"), "W": float("nan"), "L": float("nan"),
                        "evidence_class": "[S]" if scope == "POOLED" and band == "TRAIN" else "[D]",
                        "note": "interaction term Δjoint−Δshock−Δk12, paired block bootstrap",
                        # the interaction CI IS the §8.1 block form (paired on a common day
                        # index); declare it so the §12 MDE clause can verify it
                        "mde_source_for_bands": "block",
                        "per_seed_ci": d.get("per_seed", []),
                        "spread_cost_status": SPREAD_COST_DISCLOSURE["spread_cost_status"],
                    })
    return metrics_rows + extra


def _layer_deltas(metrics_rows: list[dict], arm_idx: dict, n_boot: int) -> list[dict]:
    """Δ log R vs L0 per layer — the M15 PRIMARY read (§8.1), so it gets the block rule."""
    out = []
    seen = set()
    l0_by = {
        (r.get("clock"), r.get("delta"), r.get("scope")): r
        for r in metrics_rows
        if r.get("band") == "TRAIN" and r.get("variant_id") == "L0_BASELINE"
    }
    for r in metrics_rows:
        if r.get("band") != "TRAIN" or r.get("variant_id") == "L0_BASELINE":
            continue
        vid, clock, delta, scope = (
            r.get("variant_id"), r.get("clock"), r.get("delta"), r.get("scope")
        )
        if vid in SIZING_VARIANTS or (vid, clock, delta, scope) in seen:
            continue
        a = _arm_arrays(arm_idx, vid, clock, delta, scope, "TRAIN")
        b = _arm_arrays(arm_idx, "L0_BASELINE", clock, delta, scope, "TRAIN")
        if a is None or b is None:
            continue
        seen.add((vid, clock, delta, scope))
        d = metrics.delta_logR_paired(a[0], a[1], b[0], b[1], n_boot=n_boot)
        out.append({
            "variant_id": vid, "clock": clock, "delta": delta, "scope": scope, "band": "TRAIN",
            "log_R_layer": r.get("log_R"),
            "log_R_L0": (l0_by.get((clock, delta, scope)) or {}).get("log_R"),
            "delta_log_R": d["delta_log_R"],
            "ci_low": d["ci_low"],
            "ci_high": d["ci_high"],
            "ci_width": d["ci_width"],
            "block_mde": d["block_mde"],
            "n_dates": d.get("n_days"),
            "per_seed_ci": d.get("per_seed", []),
            "primary_read_on_M15": clock == "M15",
        })
    return out


def _strip_internal(obj):
    """Drop internal ``_``-prefixed payload keys (raw null draws) before writing JSON."""
    if isinstance(obj, dict):
        return {k: _strip_internal(v) for k, v in obj.items() if not str(k).startswith("_")}
    if isinstance(obj, list):
        return [_strip_internal(v) for v in obj]
    return obj


CONTROL_ARMS = (
    "L0_BASELINE",
    "L4_TARGET_A1_UNMOD", "L4_TARGET_A2_UNMOD", "L4_TARGET_A3_UNMOD",
    "L4_TARGET_A1_MOD", "L4_TARGET_A2_MOD", "L4_TARGET_A3_MOD",
    "L4_TRAIL_B1_UNMOD", "L4_TRAIL_B2_UNMOD",
    "L4_TRAIL_B1_MOD", "L4_TRAIL_B2_MOD",
)
M3_LAYER_ARMS = (
    "L1_SHAT_DECILE_GE5", "L1_SHAT_DECILE_GE7", "L1_SHAT_DECILE_GE9",
    "L3_TGTCUR_FIRES", "L3_TGTCUR_DOES_NOT_FIRE", "L3_TGTMED5_CO_REPORT",
)


def _run_controls(episodes: pd.DataFrame, *, n_ctrl: int, sigma: float) -> dict:
    """§6 controls on the primary (clock, δ) cell, per arm.

    The side derangement runs on EVERY target and trail arm, not only the time-exit baseline —
    §6's EXIT-MATCHING clause is binding on both derangements and the path-dependent arms are
    exactly the ones it was written for (QA run 8, R8-04).
    """
    clock, delta = CONTROL_PRIMARY["clock"], CONTROL_PRIMARY["delta"]
    out: dict = {
        "primary_cell": dict(CONTROL_PRIMARY),
        "side_derangement_by_arm": {},
        "refereed_cells": {},
    }
    base = episodes[(episodes.clock == clock) & np.isclose(episodes.delta, delta)]
    if base.empty:
        out["status"] = "NO_EPISODES_ON_PRIMARY_CELL"
        return out

    for vid in CONTROL_ARMS:
        arm = base[base.variant_id == vid]
        if arm.empty:
            out["side_derangement_by_arm"][vid] = {"status": "NO_EPISODES"}
            continue
        r_arm = arm["r_bps"].to_numpy(dtype=float)
        r_flip = arm["r_bps_side_flipped"].to_numpy(dtype=float)
        side_arm = arm["side"].to_numpy(dtype=float)
        payload = controls_mod.side_derangement(
            r_arm, r_flip, side_arm,
            exit_matched_method=arm["exit_matched_method"].to_numpy(),
            n_seeds=n_ctrl,
        )
        payload["plant_curve"] = controls_mod.plant_curve(
            r_arm,
            payload.get("_null_draws", np.empty(0)),
            sigma_hat=sigma,
            r_flip=r_flip,
            side=side_arm,
        )
        out["side_derangement_by_arm"][vid] = payload
        out["refereed_cells"][f"{vid}|{clock}|{delta}|POOLED|TRAIN"] = {
            "control": "side_derangement",
            "collapse_fraction": payload.get("collapse_fraction"),
        }

    prim = base[base.variant_id == CONTROL_PRIMARY["variant_id"]]
    if not prim.empty:
        out["side_derangement"] = out["side_derangement_by_arm"].get(
            CONTROL_PRIMARY["variant_id"], {}
        )
        out["plant_curve"] = out["side_derangement"].get("plant_curve", {})
        out["entry_timing"] = controls_mod.entry_timing_derangement(
            prim["r_bps"].to_numpy(dtype=float),
            prim["symbol"].to_numpy(),
            prim["active_hold_hours"].to_numpy(dtype=float),
            prim["side"].to_numpy(dtype=float),
            n_seeds=n_ctrl,
        )
        out["fixed_point_count"] = max(
            int(v.get("fixed_point_count", 0))
            for v in list(out["side_derangement_by_arm"].values()) + [out["entry_timing"]]
            if isinstance(v, dict) and "fixed_point_count" in v
        ) if out["side_derangement_by_arm"] else 0

    # M-3 magnitude-matched comparator — MANDATORY for L1 and L3 (§6)
    l0 = base[base.variant_id == "L0_BASELINE"]
    mm: dict = {}
    for vid in M3_LAYER_ARMS:
        sub = base[base.variant_id == vid]
        if sub.empty or l0.empty:
            mm[vid] = {"status": "NO_EPISODES"}
            continue
        keys = set(zip(sub.symbol, sub.decision_end_ns, sub.side))
        comp = l0[[
            (s, t, d) not in keys
            for s, t, d in zip(l0.symbol, l0.decision_end_ns, l0.side)
        ]]
        if comp.empty:
            mm[vid] = {"status": "EMPTY_COMPLEMENT"}
            continue
        mm[vid] = controls_mod.magnitude_matched_comparator(
            sub["r_bps"].to_numpy(dtype=float),
            sub["abs_r_decile"].to_numpy(dtype=float),
            comp["r_bps"].to_numpy(dtype=float),
            comp["abs_r_decile"].to_numpy(dtype=float),
            sigma_hat=sigma,
            n_seeds=n_ctrl,
        )
    out["magnitude_matched_by_arm"] = mm
    out["magnitude_matched"] = mm.get("L1_SHAT_DECILE_GE7", {})
    return out


def _attach_homogeneity(metrics_rows: list[dict]) -> None:
    """§9: every pooled figure ships WITH an I² across the per-symbol cells behind it.

    The per-symbol cells are already scored, so this is a free post-pass. Absent it, §9's
    condition on the pooled read could not be evaluated at all (QA run 8, R8-23).
    """
    by_pool: dict = {}
    for r in metrics_rows:
        key = (r.get("variant_id"), r.get("clock"), r.get("delta"), r.get("band"))
        if r.get("scope") == "POOLED":
            by_pool.setdefault(key, {"pooled": None, "symbols": []})["pooled"] = r
        else:
            by_pool.setdefault(key, {"pooled": None, "symbols": []})["symbols"].append(r)
    for key, pack in by_pool.items():
        pooled = pack["pooled"]
        if pooled is None:
            continue
        vals, ses = [], []
        for s in pack["symbols"]:
            lr, mde = s.get("log_R"), s.get("block_mde")
            if lr is None or mde is None:
                continue
            vals.append(lr)
            ses.append((mde / 1.96) if isinstance(mde, float) else float("nan"))
        h = metrics.homogeneity(np.asarray(vals, dtype=float), np.asarray(ses, dtype=float))
        pooled.update({
            "i_squared": h["i_squared"],
            "homogeneity_q": h["q_stat"],
            "homogeneity_df": h["q_df"],
            "homogeneity_k_symbols": h["k_symbols"],
            "per_symbol_spread_log_R": h["per_symbol_spread"],
            "pooled_status": (
                "PRIMARY_CANDIDATE_OPERATOR_JUDGES" if h["k_symbols"] >= 2
                else "DISCLOSURE_ONLY_LANE_DEFAULT"
            ),
            "pooled_status_note": (
                "§9: pooled holds PRIMARY status only conditionally on the emitted "
                "homogeneity statistic; the OPERATOR judges it. No cutoff here, nothing "
                "machine-dropped (INFR-016)."
            ),
        })


def _attach_control_collapse(metrics_rows: list[dict], controls_payload: dict) -> None:
    """Attach each control's collapse fraction to the cells that control actually refereed."""
    refereed = controls_payload.get("refereed_cells", {})
    for r in metrics_rows:
        key = "|".join(str(r.get(k)) for k in ("variant_id", "clock", "delta", "scope", "band"))
        hit = refereed.get(key)
        if hit:
            r["collapse_fraction"] = hit.get("collapse_fraction")
            r["collapse_fraction_status"] = "DISCLOSURE_ONLY"
            r["collapse_fraction_source"] = hit.get("control")


def _join_predeclaration(metrics_df: pd.DataFrame) -> pd.DataFrame:
    exp = json.loads((RESULTS_DIR / "expected_resolution.json").read_text())
    strata = exp.get("strata", [])
    # map (clock, delta, variant_id, scope) -> expected
    lookup = {}
    for s in strata:
        key = (s.get("clock"), float(s.get("delta", s.get("deltaThreshold", 0))),
               s.get("variant_id"), s.get("scope"))
        lookup[key] = s
    exp_n, exp_mde, prior = [], [], []
    for _, row in metrics_df.iterrows():
        key = (row.get("clock"), float(row.get("delta")), row.get("variant_id"), row.get("scope"))
        s = lookup.get(key, {})
        exp_n.append(s.get("expected_n"))
        exp_mde.append(s.get("expected_mde50"))
        prior.append(s.get("prior_status"))
    metrics_df = metrics_df.copy()
    metrics_df["expected_n"] = exp_n
    metrics_df["expected_mde50"] = exp_mde
    metrics_df["prior_status"] = prior
    metrics_df["delta_n_realised_minus_expected"] = np.nan  # null expected
    metrics_df["delta_mde50_realised_minus_expected"] = np.nan
    return metrics_df


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="SPDR-019 phase-(a) screen")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--smoke", action="store_true", help="2 symbols, n_boot=50")
    ap.add_argument("--n-boot", type=int, default=None)
    ap.add_argument("--symbols", type=str, default=None, help="comma-separated subset")
    args = ap.parse_args(argv)

    t_start = time.time()
    print("SPDR-019 phase (a) — 33 variants, TRAIN only", flush=True)
    verify_predeclaration()

    syms = universe()
    if args.symbols:
        syms = [s.strip() for s in args.symbols.split(",")]
    if args.smoke:
        syms = [s for s in ("BTCUSDT", "ETHUSDT") if s in syms] or syms[:2]
    n_boot = args.n_boot or (50 if args.smoke else BOOT_RESAMPLES)
    print(f"  symbols={len(syms)}  jobs={args.jobs}  n_boot={n_boot}", flush=True)

    # wall-clock estimate before the full run: BOTH stages probed. The metrics stage was
    # previously a hardcoded 300 s, which under-reported by orders of magnitude (QA run 8,
    # R8-28); it is now extrapolated from a real cell-scoring probe.
    if not args.smoke and args.n_boot is None:
        t0 = time.time()
        probe = _process_symbol(
            {"symbol": syms[0], "n_boot": 50, "deltas": [0.5], "clocks": ["H1"]}
        )
        dt_ep = time.time() - t0
        est_ep = dt_ep * len(syms) * len(DELTA_THRESHOLDS) * len(CLOCKS_RUN) / max(args.jobs, 1)

        probe_eps = pd.DataFrame(probe.get("episodes") or [])
        dt_cell, n_probe_cells, est_met = 0.0, 0, float("nan")
        if not probe_eps.empty:
            t1 = time.time()
            probe_rows = _score_cells(
                probe_eps, pd.DataFrame(probe.get("signals") or []),
                n_boot=n_boot, jobs=1,
            )
            dt_cell = time.time() - t1
            n_probe_cells = max(len(probe_rows), 1)
            n_variants = len([v for v in VARIANT_IDS if v not in DERIVED_VARIANTS])
            total_cells = (
                n_variants * len(CLOCKS_RUN) * len(DELTA_THRESHOLDS) * 3 * (len(syms) + 1)
            )
            est_met = dt_cell / n_probe_cells * total_cells / max(args.jobs, 1)
        est = est_ep + (est_met if np.isfinite(est_met) else 0.0)
        print(f"  ESTIMATED wall-clock ≈ {est/60:.1f} min "
              f"(episodes {est_ep/60:.1f} min + metrics {est_met/60:.1f} min; "
              f"probe {syms[0]}); check in if >2×", flush=True)
        write_json("run_estimate.json", {
            "probe_symbol": syms[0],
            "probe_episode_stage_s": dt_ep,
            "probe_cell_stage_s": dt_cell,
            "probe_cells_scored": n_probe_cells,
            "estimated_episode_stage_s": est_ep,
            "estimated_metrics_stage_s": est_met,
            "estimated_s": est, "jobs": args.jobs, "n_symbols": len(syms),
            "n_boot": n_boot,
        })

    tasks = [{"symbol": s, "n_boot": n_boot} for s in syms]
    results = run_tasks(tasks, args.jobs, label="symbols")

    # §12: determinism runs UNCONDITIONALLY whenever --jobs > 1. The previous `and not
    # args.smoke` guard left `determinism_ok = True` recorded as a HARD check that held on a
    # run where nothing was compared (QA run 8, R8-27).
    determinism_ok = None
    if args.jobs > 1:
        print("  determinism: re-running 1 symbol sequential…", flush=True)
        seq = _process_symbol(tasks[0])
        par = next(r for r in results if r["symbol"] == tasks[0]["symbol"])
        h1 = hashlib.sha256(
            json.dumps(seq.get("episodes", []), sort_keys=True, default=_json).encode()
        ).hexdigest()
        h2 = hashlib.sha256(
            json.dumps(par.get("episodes", []), sort_keys=True, default=_json).encode()
        ).hexdigest()
        determinism_ok = h1 == h2
        print(f"  determinism {'OK' if determinism_ok else 'FAIL'} {h1[:12]} vs {h2[:12]}", flush=True)

    # assemble episodes
    ep_rows = []
    sig_rows = []
    units = []
    parities = []
    tw_mats = []
    for r in results:
        if r.get("error"):
            print(f"  ERROR {r['symbol']}: {r['error']}", flush=True)
        ep_rows.extend(r.get("episodes") or [])
        sig_rows.extend(r.get("signals") or [])
        if r.get("unit"):
            units.append(r["unit"])
        if r.get("parity"):
            parities.append(r["parity"])
        if r.get("tripwire"):
            tw_mats.append(r["tripwire"])

    episodes = pd.DataFrame(ep_rows) if ep_rows else pd.DataFrame()
    signals = pd.DataFrame(sig_rows) if sig_rows else pd.DataFrame()
    print(f"  episodes={len(episodes)}  signals={len(signals)}", flush=True)

    if not episodes.empty:
        write_parquet("episodes.parquet", episodes)
    if not signals.empty:
        write_parquet("signals.parquet", signals)

    # unit pin — measured at run, before anything consumes σ̂ (§7)
    unit_pin = {
        "divisor_object_1": "Wilder ATR(20) decision clock at [0] — deltaThreshold only",
        "divisor_object_2": "H1 Parkinson EWMA λ=0.94 ŝ in bps (SPDR-014 Z-VOL identical)",
        "per_symbol": units,
        "pooled_s_hat_median": float(np.nanmedian([u["s_hat_uncond"] for u in units])) if units else None,
        "pooled_atr20_median": float(np.nanmedian([u["atr20_median_h1"] for u in units])) if units else None,
        "cost_floor_bps_DISCLOSURE_ONLY": COST_FLOOR_BPS,
        "spread_cost_disclosure": SPREAD_COST_DISCLOSURE,
        "n_h1_bars_pooled": int(sum(u.get("n_h1", 0) for u in units)),
    }
    write_json("unit_pin.json", unit_pin)

    # parent parity — computed once, strictly. A parity computation that RAISED is a failure,
    # not a pass: the previous fallback aggregate swallowed the exception and admitted
    # NO_PARENT_ROW / PARENT_NAN as passing (QA run 8, R8-15).
    try:
        parent_parity = parent_gates.run_all_parity(syms)
    except Exception as e:
        parent_parity = {
            "hard_pass": False,
            "error": repr(e),
            "traceback": traceback.format_exc(),
            "rows": parities,
            "reason": "parity computation raised; a raised check is a FAILURE (P-23)",
        }
        print(f"  parent parity ERROR (hard fail): {e}", flush=True)
    write_json("parent_gate_parity.json", parent_parity)

    # controls (§6). Battery is PINNED at CONTROL_N_SEEDS, independent of --n-boot (R9-05).
    controls_payload = {"spread_cost_disclosure": SPREAD_COST_DISCLOSURE}
    n_ctrl = CONTROL_N_SEEDS
    sigma = unit_pin.get("pooled_s_hat_median") or float("nan")
    if not episodes.empty:
        controls_payload.update(_run_controls(episodes, n_ctrl=n_ctrl, sigma=sigma))
    controls_payload["n_ctrl_seeds_pinned"] = n_ctrl
    write_json("controls.json", _strip_internal(controls_payload))

    # metrics
    print("  scoring cells…", flush=True)
    mrows = _score_cells(episodes, signals, n_boot=n_boot, jobs=args.jobs)
    arm_idx = _arm_index(episodes)
    mrows = _add_interaction_rows(mrows, arm_idx, n_boot)
    _attach_homogeneity(mrows)
    _attach_control_collapse(mrows, controls_payload)
    metrics_df = pd.DataFrame(mrows) if mrows else pd.DataFrame()
    if not metrics_df.empty:
        metrics_df = _join_predeclaration(metrics_df)
        # drop heavy nested for parquet
        for col in ("per_block_ci", "per_seed_ci", "ladder"):
            if col in metrics_df.columns:
                metrics_df[col] = metrics_df[col].map(
                    lambda v: json.dumps(v, default=_json) if not isinstance(v, str) else v
                )
        write_parquet("metrics_by_cell.parquet", metrics_df)

    # layer deltas — the M15 primary read, paired block bootstrap (§8.1)
    print("  layer deltas (paired block bootstrap)…", flush=True)
    ld = _layer_deltas(mrows, arm_idx, n_boot)
    if ld:
        ld_df = pd.DataFrame(ld)
        ld_df["per_seed_ci"] = ld_df["per_seed_ci"].map(
            lambda v: json.dumps(v, default=_json)
        )
        write_parquet("layer_deltas.parquet", ld_df)

    # resolution ladder = metrics projection
    if not metrics_df.empty:
        ladder_cols = [
            c for c in metrics_df.columns
            if c in (
                "variant_id", "clock", "delta", "scope", "band", "n", "n_dates",
                "log_R", "ci_low", "ci_high", "ci_width", "block_mde", "mde50", "mde80", "mde95",
                "realised_c", "effective_n", "expected_n", "expected_mde50", "prior_status",
            ) or c.startswith("detect_")
        ]
        write_parquet("resolution_ladder.parquet", metrics_df[ladder_cols])

    # selection L-51 — every subset §12 names (R9-07)
    sel_cells = {}
    l51_layer_vids = (
        "L1_SHAT_DECILE_GE5", "L1_SHAT_DECILE_GE7", "L1_SHAT_DECILE_GE9",
        "L2_SHOCK_HMM", "L2_LEVEL_RMARKOV_K4", "L2_LEVEL_RMARKOV_K12",
        "L2_JOINT_HMM_HIGH_AND_K12_HIGH",
        "L3_TGTCUR_FIRES", "L3_TGTCUR_DOES_NOT_FIRE", "L3_TGTMED5_CO_REPORT",
    )
    if not episodes.empty:
        for clock in CLOCKS_RUN:
            l0 = episodes[(episodes.variant_id == "L0_BASELINE") & (episodes.clock == clock)]
            for vid in l51_layer_vids:
                sub = episodes[(episodes.variant_id == vid) & (episodes.clock == clock)]
                if len(sub) and len(l0):
                    keys = set(zip(sub.symbol, sub.decision_end_ns, sub.side))
                    exc = l0[[
                        (s, t, d) not in keys
                        for s, t, d in zip(l0.symbol, l0.decision_end_ns, l0.side)
                    ]]
                    sel_cells[f"{vid}|{clock}"] = {
                        "selected_r": sub["r_bps"].to_numpy(),
                        "excluded_r": exc["r_bps"].to_numpy() if len(exc) else np.array([]),
                    }
        # cells above vs below median mde50 on the scored TRAIN POOLED rows
        if mrows:
            cell_mde = {
                (r.get("variant_id"), r.get("clock"), r.get("delta")): r.get("mde50")
                for r in mrows
                if r.get("band") == "TRAIN" and r.get("scope") == "POOLED"
                and isinstance(r.get("mde50"), (int, float)) and np.isfinite(r.get("mde50"))
            }
            if cell_mde:
                med = float(np.median(list(cell_mde.values())))
                above_r, below_r = [], []
                for (vid, clock, delta), mde in cell_mde.items():
                    g = episodes[
                        (episodes.variant_id == vid) & (episodes.clock == clock)
                        & np.isclose(episodes.delta, float(delta))
                    ]
                    if g.empty:
                        continue
                    if mde >= med:
                        above_r.append(g["r_bps"].to_numpy())
                    else:
                        below_r.append(g["r_bps"].to_numpy())
                if above_r and below_r:
                    sel_cells["MDE50_ABOVE_MEDIAN"] = {
                        "selected_r": np.concatenate(above_r),
                        "excluded_r": np.concatenate(below_r),
                    }
                    sel_cells["MDE50_BELOW_MEDIAN"] = {
                        "selected_r": np.concatenate(below_r),
                        "excluded_r": np.concatenate(above_r),
                    }
    selection_payload = selection.run_selection_checks(sel_cells)
    write_json("selection_check.json", selection_payload)

    # tripwires — pre-declared anchor BTCUSDT (golden G1), never selected by a passing count (R9-10).
    # Counts and id lists are also POOLED across every symbol that ran a tripwire.
    tw1 = {"hard_pass": False, "missing": True}
    tw2 = {"hard_pass": False, "missing": True}
    tw_symbol = TRIPWIRE_SYMBOL
    by_sym = {tm.get("symbol"): tm for tm in tw_mats if tm.get("symbol")}
    if TRIPWIRE_SYMBOL in by_sym:
        tm = by_sym[TRIPWIRE_SYMBOL]
        tw1 = tm.get("tripwire_1", tw1)
        tw2 = tm.get("tripwire_2", tw2)
    elif tw_mats:
        # anchor absent from this run (e.g. a non-BTC smoke) — fall back to first symbol, labelled
        tm = sorted(tw_mats, key=lambda t: t.get("symbol", ""))[0]
        tw1 = tm.get("tripwire_1", tw1)
        tw2 = tm.get("tripwire_2", tw2)
        tw_symbol = tm.get("symbol")
        tw1 = dict(tw1)
        tw1["anchor_fallback"] = True
        tw1["declared_anchor"] = TRIPWIRE_SYMBOL
    # pool structural counts across all symbols so clause-2 is not carried by selection
    if tw_mats:
        pool = {
            "count_clock_vs_m1": sum(
                int(tm.get("tripwire_2", {}).get("count_clock_vs_m1", 0)) for tm in tw_mats
            ),
            "count_both_reachable": sum(
                int(tm.get("tripwire_2", {}).get("count_both_reachable", 0)) for tm in tw_mats
            ),
            "count_favourable_diff": sum(
                int(tm.get("tripwire_2", {}).get("count_favourable_diff", 0)) for tm in tw_mats
            ),
            "n_symbols_pooled": len(tw_mats),
            "symbols": sorted(tm.get("symbol", "") for tm in tw_mats),
        }
        tw2 = dict(tw2)
        tw2["pooled"] = pool
        # hard_pass requires the anchor payload AND a non-zero pooled both-reachable count
        tw2["hard_pass"] = bool(
            tw2.get("hard_pass") and pool["count_both_reachable"] > 0
        )

    integrity_extra = integrity.build_integrity_extra(
        episodes=episodes,
        signals=signals,
        metrics_rows=mrows,
        controls=controls_payload,
        tripwire_1=tw1,
        tripwire_2=tw2,
        n_boot=n_boot,
        parent_parity=parent_parity,
    )
    integrity_extra["tripwire_symbol"] = tw_symbol

    # golden
    bundles_min = {}  # golden needs bundles — rebuild BTC/ETH cheaply if smoke/full
    # Only the traces' own cells are materialised as records. Converting the WHOLE episode
    # frame to python dicts cost several GB on two symbols and would not survive 25.
    episodes_by_key = {}
    if not episodes.empty:
        want = {("BTCUSDT", "H1", 0.5, "L0_BASELINE"), ("ETHUSDT", "H1", 0.5, "L0_BASELINE")}
        for key in want:
            sym, clock, delta, vid = key
            g = episodes[
                (episodes.symbol == sym) & (episodes.clock == clock)
                & np.isclose(episodes.delta, delta) & (episodes.variant_id == vid)
            ]
            if not g.empty:
                episodes_by_key[key] = g.to_dict("records")
    # load BTC/ETH for golden
    for s in ("BTCUSDT", "ETHUSDT"):
        if s in syms:
            try:
                b = panel_mod.load_symbol_bundle(s)
                if b:
                    bundles_min[s] = b
            except Exception:
                pass
    golden_payload = golden.build_golden_traces(bundles_min, episodes_by_key, mrows)
    # G6 and G7 read the REAL tripwire payloads (QA run 8, R8-12)
    golden_payload["G6"] = golden.g6_from_tripwire1(tw1, tw_symbol)
    golden_payload["G7"] = golden.g7_from_tripwire2(tw2)
    write_json("golden_traces.json", golden_payload)

    # selfcheck
    print("  self-check…", flush=True)
    integ = selfcheck.run_selfcheck(
        metrics_df=metrics_df if not metrics_df.empty else pd.DataFrame(),
        episodes_df=episodes if not episodes.empty else pd.DataFrame(),
        signals_df=signals if not signals.empty else None,
        integrity_extra=integrity_extra,
        controls=controls_payload,
        selection=selection_payload,
        golden=golden_payload,
        parent_parity=parent_parity,
        unit_pin=unit_pin,
        determinism_ok=determinism_ok,
        jobs=args.jobs,
    )
    write_json("integrity_selfcheck.json", integ)

    elapsed = time.time() - t_start
    summary = {
        "experiment": "SPDR-019",
        "phase": "a",
        "n_variants": 33,
        "n_symbols": len(syms),
        "n_episodes": int(len(episodes)),
        "n_metric_rows": int(len(metrics_df)),
        "n_boot": n_boot,
        "jobs": args.jobs,
        "elapsed_s": elapsed,
        "all_hard_pass": integ.get("all_hard_pass"),
        "hard_fail_names": integ.get("hard_fail_names"),
        "smoke": args.smoke,
        "spread_cost_disclosure": SPREAD_COST_DISCLOSURE,
    }
    write_json("run_summary.json", summary)
    print(f"  done in {elapsed/60:.1f} min  hard_pass={integ.get('all_hard_pass')}  "
          f"fails={integ.get('hard_fail_names')}", flush=True)
    return 0 if integ.get("all_hard_pass") else 1


if __name__ == "__main__":
    # spawn-safe
    mp.freeze_support()
    raise SystemExit(main())
