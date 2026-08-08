"""INFR-015 CLS-EPISODE binder-form amendment — overlap-aware stage-2 blocks.

> **LEGACY CAL APPARATUS (INFR-022).** Not bindable on the live research path without a
> post-INFR-022 CAL redesign. Retired names used here for historical replay only:
> ``g_net`` stage-1 (L-26), the ``n_legs_floor`` / AMENDMENT-7 domain guards, and the
> ``stage2_net_lcb_positive`` deployability binding. INFR-022: zero-cost, gross-only.

Single form change vs the frozen INFR-014 harness (calibration_bybit.py, untouched —
it backs the accepted pin ac8a1eb6…): the CLS-EPISODE stage-2 leg bootstrap uses
``block_legs = episode_overlap_rule_v1(ledger)`` instead of 1. Everything else is the
INFR-014 procedure verbatim (design §3). Fresh disjoint seed banks (design §5).

CLS-FILTER is NOT re-measured here; the amended registry carries its block over
byte-identically (canonical JSON) from the existing pin.
"""
from __future__ import annotations

import hashlib
import json
import math
from copy import deepcopy
from pathlib import Path
from typing import Any

import numpy as np

import xen.xena.calibration_p3b as p3b
from xen.xena.calibration import SegmentLayout
from xen.xena.calibration_p3b import HIGH, LOW, CadenceSpec, ScaleSpec, bank_seeds
from xen.xena.calibration_p3d import binomial_se, eval_lcb_legs, wilson
from xen.xena.calibration_pc import (
    EMBARGO_FRAC,
    N_BOOT,
    STAGE_RANKING_FRAC,
    STAGE_SEARCH_FRAC,
    c_layout,
    deplant_stage2,
)
from xen.xena.calibration_bybit import (
    ALPHA,
    BITE_EDGE_BPS,
    BITE_N,
    BITE_SELECT_MIN,
    BITE_SURVIVAL_MAX,
    IntegrityError,
    _deplant_class_plants,
    _failure_label,
    _outcome,
    _search_params,
    _set_seeds,
    assert_stage1_zero_cost,
    make_episode_null_universe,
    verify_bybit_registry,
)
from xen.xena.certify import certify_and_rank, contiguous_purged_folds
from xen.xena.oracle import CandidateStream, OracleConfig, evaluate
from xen.xena.score import lcb_g_leg_studentized
from xen.xena.search import run_restart

NS = 1_000_000_000
CLASS_ID = "CLS-EPISODE"
BLOCK_RULE_ID = "episode_overlap_rule_v1"

# INFR-015 fresh banks (design §5) — disjoint from 91k–94k, 951k/952k, all ch03
DESIGN_SEEDS_15 = {"low": 95_000, "high": 96_000}
CONFIRM_SEEDS_15 = {"low": 97_000, "high": 98_000}
BITE_SEEDS_15 = {"low": 953_000, "high": 954_000}

DESIGN_SCALE_15 = ScaleSpec("design", n_null=80, n_cand=64, budget=200, n_restarts=5,
                            n_power=6, n_coverage=80)
CONFIRM_SCALE_15 = ScaleSpec("confirm", n_null=200, n_cand=64, budget=200, n_restarts=5,
                             n_power=6, n_coverage=200)

_INFR014_SEED_RANGES = (
    (91_000, 91_500), (92_000, 92_500), (93_000, 93_500), (94_000, 94_500),
    (951_000, 951_050), (952_000, 952_050),
)
_CH03_SEED_RANGES = (
    (71_000, 71_500), (72_000, 72_500), (81_000, 81_500), (82_000, 82_500),
    (791_000, 791_050), (792_000, 792_050),
)


# --------------------------------------------------------------------------- #
# episode_overlap_rule_v1 (design §3 — pinned estimators)
# --------------------------------------------------------------------------- #
def episode_overlap_block_legs(entry_ns: np.ndarray, exit_ns: np.ndarray) -> int:
    """B = min(max(1, ceil(q90(dur_h)/median(gap_h))), max(1, floor(n/4))).

    q90 = numpy.quantile(method="linear"); median = numpy.median; gaps from consecutive
    sorted EntryTime. Single-leg or zero/degenerate-gap stream => 1.
    """
    n = int(len(entry_ns))
    if n <= 1:
        return 1
    et = np.sort(np.asarray(entry_ns, dtype=np.int64), kind="mergesort")
    dur_h = (np.asarray(exit_ns, dtype=np.int64) - np.asarray(entry_ns, dtype=np.int64)
             ).astype(float) / (3600.0 * NS)
    dur_h = dur_h[np.isfinite(dur_h) & (dur_h > 0)]
    gaps_h = np.diff(et).astype(float) / (3600.0 * NS)
    med_gap = float(np.median(gaps_h)) if len(gaps_h) else 0.0
    if len(dur_h) == 0 or med_gap <= 0.0:
        return 1
    q90 = float(np.quantile(dur_h, 0.9, method="linear"))
    b_raw = max(1, int(math.ceil(q90 / med_gap)))
    cap = max(1, n // 4)
    return min(b_raw, cap)


def eval_lcb_legs_ep(subset, streams, config, segment, *, n_boot: int, seed: int) -> dict:
    """Stage-2 LCB with block_legs from episode_overlap_rule_v1 on the evaluated ledger.

    B == 1 routes to the UNMODIFIED legacy path (eval_lcb_legs, block_legs=1) so the
    degenerate case is bit-for-bit identical to the INFR-014 estimator (golden trace G2).
    Gross-only (INFR-022 zero-cost model).
    """
    res = evaluate(subset, streams, config, segment=segment, seed=seed)
    if res.ledger is not None and res.ledger.height > 0:
        led = res.ledger.sort("EntryTime")
        b = episode_overlap_block_legs(
            led.get_column("EntryTime").to_numpy().astype(np.int64),
            led.get_column("ExitTime").to_numpy().astype(np.int64),
        )
    else:
        b = 1
    if b == 1:
        out = eval_lcb_legs(subset, streams, config, segment, n_boot=n_boot, seed=seed,
                            block_legs=1)
        out["block_legs_used"] = 1
        out["block_rule"] = BLOCK_RULE_ID
        return out
    out = lcb_g_leg_studentized(res, streams, n_boot=n_boot, seed=seed + 99,
                                block_legs=b, confidence=0.95)
    out["n_admitted"] = res.n_admitted
    out["block_legs_used"] = int(b)
    out["block_rule"] = BLOCK_RULE_ID
    return out


# --------------------------------------------------------------------------- #
# Two-stage (stage-1 identical to INFR-014; stage-2 blocked)
# --------------------------------------------------------------------------- #
def run_two_stage_ep(
    streams: list[CandidateStream],
    cadence: CadenceSpec,
    layout: SegmentLayout,
    *,
    scale: ScaleSpec,
    seed: int,
    n_boot: int = N_BOOT,
) -> dict[str, Any]:
    """Stage-1 search→select(top-1) on g_gross; stage-2 blocked LCB(g_gross).

    INFR-022: gross-only (zero-cost model); the retired L-26 net-cost-binding stage-1
    and the stage-2 net (deployability) read are removed.
    """
    assert_stage1_zero_cost(charge_costs=False, score_kind="g_gross")
    config = OracleConfig(charge_costs=False)
    params = _search_params(cadence)
    finalists = [
        run_restart(
            streams, config, budget=scale.budget, restart_id=r + 1,
            params=params, segment=layout.search,
            skip_economics_precondition=True,
        )
        for r in range(scale.n_restarts)
    ]
    folds = contiguous_purged_folds(
        layout.ranking[0], layout.ranking[1], n_folds=3,
        purge_ns=max(cadence.hold_bars, 1) * 60 * NS,
    )
    pkg = certify_and_rank(
        finalists, streams, config, folds=folds, params=params,
        search_segment=layout.search, include_random_ref=False,
        include_fill_basis=False,
    )
    if not pkg["ranked"]:
        return {
            "empty": True, "gross_pass": False, "top": [],
            "g_search_hat": None,
        }
    top = pkg["ranked"][0].subset
    lcb_g = eval_lcb_legs_ep(top, streams, config, layout.gate, n_boot=n_boot,
                             seed=seed)
    top_ids = sorted(str(x) for x in top)
    return {
        "empty": False,
        "top": top_ids,
        "plant_in_top": any(t.startswith("epplant") for t in top_ids),
        "gross_pass": bool(lcb_g.get("pass_positive")),
        "gross_lcb": lcb_g.get("lcb"),
        "gross_point": lcb_g.get("point"),
        "n_legs": lcb_g.get("n_legs"),
        "block_legs_used": lcb_g.get("block_legs_used"),
        "g_search_hat": pkg["ranked"][0].search_F_hat,
        "stage1_score_kind": "g_gross",
        "stage1_charge_costs": False,
        "cost_model": "NO_COST_CHARGED",
    }


# --------------------------------------------------------------------------- #
# Seed disjointness (HARD)
# --------------------------------------------------------------------------- #
def assert_seed_disjoint_15() -> None:
    d = set(range(DESIGN_SEEDS_15["low"], DESIGN_SEEDS_15["low"] + 500)) | set(
        range(DESIGN_SEEDS_15["high"], DESIGN_SEEDS_15["high"] + 500))
    c = set(range(CONFIRM_SEEDS_15["low"], CONFIRM_SEEDS_15["low"] + 500)) | set(
        range(CONFIRM_SEEDS_15["high"], CONFIRM_SEEDS_15["high"] + 500))
    b = set(range(BITE_SEEDS_15["low"], BITE_SEEDS_15["low"] + 50)) | set(
        range(BITE_SEEDS_15["high"], BITE_SEEDS_15["high"] + 50))
    prior = set()
    for lo, hi in _INFR014_SEED_RANGES + _CH03_SEED_RANGES:
        prior |= set(range(lo, hi))
    if d & c or d & b or c & b:
        raise IntegrityError("INFR-015 bank collision (design/confirm/bite)")
    for name, s in (("design", d), ("confirm", c), ("bite", b)):
        if s & prior:
            raise IntegrityError(
                f"INFR-015 {name} bank collides with INFR-014/chapter-03 seeds")


# --------------------------------------------------------------------------- #
# Bite / coverage / e2e (episode class only)
# --------------------------------------------------------------------------- #
def bite_check_ep(cadence: CadenceSpec, *, scale: ScaleSpec,
                  embargo_frac: float = EMBARGO_FRAC, n: int = BITE_N) -> dict[str, Any]:
    layout = c_layout(cadence.n_bars, cadence.hold_bars, embargo_frac=embargo_frac)
    stage2_start = layout.gate[0]
    base = BITE_SEEDS_15[cadence.name]
    survive = selected = 0
    rows = []
    for i in range(n):
        seed = base + i
        streams = make_episode_null_universe(
            seed, cadence, n_candidates=scale.n_cand, edge_bps=BITE_EDGE_BPS, plant=True)
        streams = deplant_stage2(streams, edge_bps=BITE_EDGE_BPS,
                                 stage2_start_ns=stage2_start)
        streams = _deplant_class_plants(streams, edge_bps=BITE_EDGE_BPS,
                                        stage2_start_ns=stage2_start)
        out = run_two_stage_ep(streams, cadence, layout, scale=scale, seed=seed)
        selected += int(out.get("plant_in_top", False))
        survive += int(out.get("gross_pass", False))
        rows.append({
            "seed": seed, "plant_in_top": out.get("plant_in_top"),
            "stage2_pass": out.get("gross_pass"), "gross_lcb": out.get("gross_lcb"),
            "n_legs": out.get("n_legs"), "block_legs_used": out.get("block_legs_used"),
            "empty": out.get("empty"),
        })
    survival_rate = survive / max(n, 1)
    select_rate = selected / max(n, 1)
    return {
        "class_id": CLASS_ID, "cadence": cadence.name, "n": n,
        "stage2_survival_rate": survival_rate, "stage1_select_rate": select_rate,
        "select_ok": bool(select_rate >= BITE_SELECT_MIN),
        "survival_ok": bool(survival_rate <= BITE_SURVIVAL_MAX),
        "bite_ok": bool(select_rate >= BITE_SELECT_MIN
                        and survival_rate <= BITE_SURVIVAL_MAX),
        "thresholds": {"survival_max": BITE_SURVIVAL_MAX, "select_min": BITE_SELECT_MIN,
                       "planted_edge_bps": BITE_EDGE_BPS},
        "embargo_frac": embargo_frac, "stage2_start_ns": int(stage2_start), "rows": rows,
    }


def no_search_coverage_ep(cadence: CadenceSpec, *, scale: ScaleSpec,
                          embargo_frac: float = EMBARGO_FRAC, n_universes: int,
                          subset_size: int = 5, n_boot: int = N_BOOT,
                          alpha: float = ALPHA) -> dict[str, Any]:
    """No-search blocked-LCB pass rate. Uses current p3b.SEED_BASE_* (caller sets)."""
    config = OracleConfig(charge_costs=False)
    layout = c_layout(cadence.n_bars, cadence.hold_bars, embargo_frac=embargo_frac)
    hits = 0
    rows = []
    seed_base_low = int(p3b.SEED_BASE_LOW)
    seed_base_high = int(p3b.SEED_BASE_HIGH)
    for seed, cspec in bank_seeds(cadence, n_universes):
        streams = make_episode_null_universe(
            seed, cspec, n_candidates=scale.n_cand, edge_bps=0.0, plant=False)
        rng = np.random.default_rng(seed + 91)
        ids = [s.candidate_id for s in streams]
        k = min(subset_size, len(ids))
        pick = frozenset(str(x) for x in rng.choice(ids, size=k, replace=False))
        lcb = eval_lcb_legs_ep(pick, streams, config, layout.gate, n_boot=n_boot,
                               seed=seed)
        pos = bool(lcb.get("pass_positive"))
        hits += int(pos)
        rows.append({"seed": seed, "pass": pos, "lcb": lcb.get("lcb"),
                     "n_legs": lcb.get("n_legs"),
                     "block_legs_used": lcb.get("block_legs_used")})
    n = len(rows)
    rate = hits / max(n, 1)
    return {
        "class_id": CLASS_ID, "cadence": cadence.name, "n": n,
        "n_lcb_positive": hits, "rate": rate,
        "coverage_ok": bool(n > 0 and rate <= float(alpha)), "rows": rows,
        "seed_bases": {"low": seed_base_low, "high": seed_base_high},
        "alpha_target": float(alpha), "block_rule": BLOCK_RULE_ID,
    }


def e2e_alpha_ep(cadence: CadenceSpec, *, scale: ScaleSpec,
                 embargo_frac: float = EMBARGO_FRAC, n_boot: int = N_BOOT,
                 alpha: float = ALPHA) -> dict[str, Any]:
    layout_by: dict = {}
    rows = []
    seed_base_low = int(p3b.SEED_BASE_LOW)
    seed_base_high = int(p3b.SEED_BASE_HIGH)
    for seed, cspec in bank_seeds(cadence, scale.n_null):
        key = (cspec.n_bars, cspec.hold_bars)
        layout = layout_by.get(key) or c_layout(
            cspec.n_bars, cspec.hold_bars, embargo_frac=embargo_frac)
        layout_by[key] = layout
        streams = make_episode_null_universe(
            seed, cspec, n_candidates=scale.n_cand, edge_bps=0.0, plant=False)
        out = run_two_stage_ep(streams, cspec, layout, scale=scale, seed=seed,
                               n_boot=n_boot)
        rows.append({
            "seed": seed, "symbol": cspec.symbol,
            "gross_pass": bool(out.get("gross_pass")),
            "gross_lcb": out.get("gross_lcb"), "gross_point": out.get("gross_point"),
            "g_search_hat": out.get("g_search_hat"), "n_legs": out.get("n_legs"),
            "block_legs_used": out.get("block_legs_used"),
            "empty": out.get("empty", False),
        })
    n = len(rows)
    k = sum(1 for r in rows if r["gross_pass"])
    ph = k / max(n, 1)
    lo, hi = wilson(k, n)
    return {
        "class_id": CLASS_ID, "cadence": cadence.name, "n": n,
        "n_gross_lcb_positive": k, "alpha_hat": ph,
        "alpha_se": binomial_se(ph, n),
        "alpha_wilson_95": {"low": lo, "high": hi},
        "pass_stop": bool(ph <= float(alpha)),
        "seed_bases": {"low": seed_base_low, "high": seed_base_high},
        "alpha_target": float(alpha), "block_rule": BLOCK_RULE_ID,
        "rows": rows,
    }


# --------------------------------------------------------------------------- #
# DESIGN / CONFIRM banks
# --------------------------------------------------------------------------- #
def run_design_ep(*, scale: ScaleSpec = DESIGN_SCALE_15) -> dict[str, Any]:
    assert_seed_disjoint_15()
    _set_seeds(DESIGN_SEEDS_15["low"], DESIGN_SEEDS_15["high"])
    print("[INFR-015] DESIGN CLS-EPISODE: bite-check (blocked stage-2)...", flush=True)
    bite: dict[str, Any] = {}
    for c in (LOW, HIGH):
        b = bite_check_ep(c, scale=scale, embargo_frac=EMBARGO_FRAC)
        bite[c.name] = b
        print(f"  bite {c.name}: survival={b['stage2_survival_rate']:.3f} "
              f"select={b['stage1_select_rate']:.3f} ok={b['bite_ok']}", flush=True)
    bite_ok = all(bite[c]["bite_ok"] for c in ("low", "high"))
    if not bite_ok:
        return {
            "bank": "design", "class_id": CLASS_ID, "seeds": dict(DESIGN_SEEDS_15),
            "bite": {k: {kk: vv for kk, vv in v.items() if kk != "rows"}
                     for k, v in bite.items()},
            "frozen_procedure": None, "design_ok": False,
            "stop_reason": "bite_failed", "terminal": True,
            "recommend": "TERMINAL_blocking_killed_power_or_plant_missed",
            "note": "bite FAIL = TERMINAL, no confirm (Fork B / design §5, §13)",
        }
    print("[INFR-015] DESIGN CLS-EPISODE: no-search coverage (blocked)...", flush=True)
    _set_seeds(DESIGN_SEEDS_15["low"], DESIGN_SEEDS_15["high"])
    cov: dict[str, Any] = {}
    for c in (LOW, HIGH):
        cv = no_search_coverage_ep(c, scale=scale, embargo_frac=EMBARGO_FRAC,
                                   n_universes=scale.n_coverage, alpha=ALPHA)
        cov[c.name] = cv
        print(f"  cov {c.name}: rate={cv['rate']:.4f} ok={cv['coverage_ok']} "
              f"(n={cv['n']}) bases={cv.get('seed_bases')}", flush=True)

    frozen = {
        "binder": "two_stage_sample_split",
        "stage1": "search+certify top-1 on stage-1 bands",
        "stage1_score_kind": "g_net",
        "stage1_charge_costs": True,
        "stage2": "lcb_g_leg_studentized(g_gross) > 0 on distant embargoed band",
        "e2e_pass_event": "stage2_gross_lcb_positive",
        "deployability_binding": "stage2_net_lcb_positive",
        "functional": "g_gross_ratio",
        "estimator": "leg_studentized_bootstrap_t",
        "embargo_frac": EMBARGO_FRAC,
        "search_frac": STAGE_SEARCH_FRAC,
        "ranking_frac": STAGE_RANKING_FRAC,
        "n_boot": N_BOOT,
        "block_legs": BLOCK_RULE_ID,
        "block_rule_text": (
            "B = min(max(1, ceil(q90(episode_duration_h)/median(inter_entry_gap_h))), "
            "max(1, floor(n_legs/4))); q90=numpy.quantile(method='linear'); "
            "median=numpy.median; gaps from consecutive sorted EntryTime; "
            "single-leg or zero-gap => 1; B==1 routes to legacy block_legs=1 path"
        ),
        "confidence": 0.95,
        "alpha": ALPHA,
        "one_subset": True,
        "shortlist": False,
        "design_seeds": dict(DESIGN_SEEDS_15),
        "confirm_seeds": dict(CONFIRM_SEEDS_15),
        "design_bite_ok": True,
        "design_cov_low": cov["low"]["rate"],
        "design_cov_high": cov["high"]["rate"],
        "held_out_escalation": False,
        "gate_rule": "per_cadence point α̂≤5% AND no-search cov≤5% (Fork A)",
        "cost_stack": "bybit_round_trip_cost_bps_v2_no_spread",
        "spread_cost_status": "UNAVAILABLE_NOT_CHARGED",
        "cost_scope": "PARTIAL_FEES_FUNDING_ONLY",
        "class_id": CLASS_ID,
        "amends": "INFR-014 CLS-EPISODE (TERMINAL); pin ac8a1eb6… superseded on write",
    }
    return {
        "bank": "design", "class_id": CLASS_ID, "seeds": dict(DESIGN_SEEDS_15),
        "bite": {k: {kk: vv for kk, vv in v.items() if kk != "rows"}
                 for k, v in bite.items()},
        "bite_rows": {k: v["rows"] for k, v in bite.items()},
        "coverage": {k: {kk: vv for kk, vv in v.items() if kk != "rows"}
                     for k, v in cov.items()},
        "frozen_procedure": frozen,
        "design_ok": True,
        "stop_reason": None,
    }


def confirm_gate_ep(procedure: dict, *,
                    scale: ScaleSpec = CONFIRM_SCALE_15) -> dict[str, Any]:
    if not procedure or not procedure.get("design_bite_ok"):
        raise IntegrityError("confirm blocked unless design_ok procedure exists")
    required = ("embargo_frac", "n_boot", "block_legs", "alpha", "stage1_score_kind",
                "stage1_charge_costs", "e2e_pass_event")
    for k in required:
        if k not in procedure:
            raise IntegrityError(f"frozen procedure missing {k}")
    if procedure["block_legs"] != BLOCK_RULE_ID:
        raise IntegrityError(
            f"INFR-015 confirm requires block_legs={BLOCK_RULE_ID!r}, "
            f"got {procedure['block_legs']!r}")
    assert_stage1_zero_cost(
        charge_costs=bool(procedure["stage1_charge_costs"]),
        score_kind=str(procedure["stage1_score_kind"]))
    assert_seed_disjoint_15()
    embargo_frac = float(procedure["embargo_frac"])
    n_boot = int(procedure["n_boot"])
    alpha = float(procedure["alpha"])
    if scale.name == "confirm" and scale.n_null != CONFIRM_SCALE_15.n_null:
        raise IntegrityError(
            f"binding confirm n_null must be {CONFIRM_SCALE_15.n_null}, got {scale.n_null}")

    per: dict[str, Any] = {}
    _set_seeds(CONFIRM_SEEDS_15["low"], CONFIRM_SEEDS_15["high"])
    for c in (LOW, HIGH):
        print(f"[INFR-015] CONFIRM {c.name}: no-search coverage...", flush=True)
        cov = no_search_coverage_ep(c, scale=scale, embargo_frac=embargo_frac,
                                    n_universes=scale.n_coverage, n_boot=n_boot,
                                    alpha=alpha)
        if cov.get("seed_bases") != dict(CONFIRM_SEEDS_15):
            raise IntegrityError(
                f"confirm coverage seed_bases {cov.get('seed_bases')} != "
                f"CONFIRM_SEEDS_15 {CONFIRM_SEEDS_15} (G3 / INFR-014 Issue 9 class)")
        print(f"  cov {c.name}: {cov['rate']:.4f} ok={cov['coverage_ok']}", flush=True)
        print(f"[INFR-015] CONFIRM {c.name}: e2e α...", flush=True)
        a = e2e_alpha_ep(c, scale=scale, embargo_frac=embargo_frac,
                         n_boot=n_boot, alpha=alpha)
        if a.get("seed_bases") != dict(CONFIRM_SEEDS_15):
            raise IntegrityError(
                f"confirm e2e seed_bases {a.get('seed_bases')} != CONFIRM_SEEDS_15")
        print(f"  α̂ {c.name}: {a['alpha_hat']:.4f} ok={a['pass_stop']}", flush=True)
        certified = bool(cov["coverage_ok"] and a["pass_stop"])
        band = "CERTIFIED" if certified else (
            "FAIL_ALPHA" if not a["pass_stop"] else "FAIL_COV")
        per[c.name] = {
            "cadence": c.name, "band": band,
            "no_search_cov": cov["rate"], "e2e_alpha": a["alpha_hat"],
            "selection_inflation": a["alpha_hat"] - cov["rate"],
            "coverage_ok": cov["coverage_ok"], "alpha_ok": a["pass_stop"],
            "certified": certified, "alpha_se": a["alpha_se"],
            "alpha_wilson_95": a["alpha_wilson_95"], "n": a["n"],
            "n_gross_lcb_positive": a["n_gross_lcb_positive"],
            "seed_bases": a.get("seed_bases"), "alpha_target": alpha,
            "failure_label": (None if certified
                              else _failure_label(cov["rate"], a["alpha_hat"])),
            "coverage_rows": cov["rows"], "alpha_rows": a["rows"],
        }
    outcome = _outcome(per["low"]["certified"], per["high"]["certified"])
    return {
        "bank": "confirm", "class_id": CLASS_ID, "seeds": dict(CONFIRM_SEEDS_15),
        "procedure": procedure,
        "per_cadence": {k: {kk: vv for kk, vv in v.items()
                            if kk not in ("coverage_rows", "alpha_rows")}
                        for k, v in per.items()},
        "alpha_low_rows": per["low"]["alpha_rows"],
        "alpha_high_rows": per["high"]["alpha_rows"],
        "coverage_low_rows": per["low"]["coverage_rows"],
        "coverage_high_rows": per["high"]["coverage_rows"],
        "outcome": outcome,
        "stop_condition": {
            "alpha_target": alpha,
            "gate_rule": (f"point α̂≤{alpha} ∧ no_search_cov≤{alpha} "
                          "(Wilson disclosure-only; alpha from frozen procedure)"),
            "low_certified": per["low"]["certified"],
            "high_certified": per["high"]["certified"],
            "verdict": outcome["verdict"],
            "recommend": outcome["recommend"],
            "terminal": outcome["terminal"],
            "forbidden": [
                "no optional stopping", "no peek-and-extend", "no UCB gate",
                "no chapter-03 pin", "no costless stage-1",
                "confirm coverage must use confirm seeds (not design)",
                "no retune on this confirm data (TERMINAL-2 => new design)",
            ],
        },
    }


# --------------------------------------------------------------------------- #
# Registry amendment (design §11)
# --------------------------------------------------------------------------- #
def _canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True)


def amend_registry_episode(
    existing_path: str | Path,
    design: dict,
    confirm: dict,
    *,
    out_path: str | Path,
    design_seeds: dict[str, int] | None = None,
    confirm_seeds: dict[str, int] | None = None,
    amended_by: str = "INFR-015",
) -> dict:
    """Replace the CLS-EPISODE block; CLS-FILTER byte-identical (canonical JSON).

    Write policy: amend ONLY if the INFR-015 confirm verdict is certifiable; on
    TERMINAL the existing pin stands and this raises IntegrityError (caller reports
    TERMINAL-2, no write).
    """
    design_seeds = dict(design_seeds or DESIGN_SEEDS_15)
    confirm_seeds = dict(confirm_seeds or CONFIRM_SEEDS_15)
    # provenance guard (QA run 4 Issue 13): pin seed fields must match the frozen
    # procedure that produced the certifying confirm bank
    proc = design.get("frozen_procedure") or {}
    if proc.get("design_seeds") != design_seeds or proc.get("confirm_seeds") != confirm_seeds:
        raise IntegrityError(
            f"pin seed fields {design_seeds}/{confirm_seeds} != frozen procedure "
            f"{proc.get('design_seeds')}/{proc.get('confirm_seeds')}")
    certifiable = {"DUAL_CERTIFY", "HIGH_ONLY_CERTIFY", "LOW_ONLY_CERTIFY"}
    outcome = (confirm.get("outcome") or {})
    verdict = outcome.get("verdict", "TERMINAL")
    if verdict not in certifiable:
        raise IntegrityError(
            f"write policy: CLS-EPISODE verdict {verdict!r} not certifiable — "
            "existing pin stands (TERMINAL-2)")

    old = verify_bybit_registry(existing_path)  # canonical verify incl. hash
    old_artifact = json.loads(Path(existing_path).read_text(encoding="utf-8"))
    old_sha = old_artifact["sha256"]
    reg = deepcopy(old)

    filt_before = [c for c in reg["class_configs"] if c["class_id"] == "CLS-FILTER"]
    if len(filt_before) != 1:
        raise IntegrityError("existing pin must contain exactly one CLS-FILTER block")
    filt_canon_before = _canon(filt_before[0])

    new_ep = {
        "class_id": CLASS_ID,
        "family_prior": "CF-EPSOSC-001",
        "procedure": design["frozen_procedure"],
        "design_seeds": design_seeds,
        "confirm_seeds": confirm_seeds,
        "cost_stack": "bybit_round_trip_cost_bps_v1",
        "stage1_score_kind": "g_net",
        "stage1_charge_costs": True,
        "e2e_pass_event": "stage2_gross_lcb_positive",
        "deployability_binding": "stage2_net_lcb_positive",
        "confirm_summary": {
            "verdict": verdict,
            "certified": True,
            "per_cadence": confirm.get("per_cadence") or {},
            "recommend": outcome.get("recommend"),
            "terminal": bool(outcome.get("terminal", False)),
        },
        "limit_entry_cells": False,
        "design_ok": True,
        "amended_by": amended_by,
    }
    reg["class_configs"] = [
        (new_ep if c["class_id"] == CLASS_ID else c) for c in reg["class_configs"]
    ]
    superseded = list(reg.get("superseded_pins") or [])
    superseded.append(old_sha)
    reg["superseded_pins"] = superseded

    filt_after = [c for c in reg["class_configs"] if c["class_id"] == "CLS-FILTER"]
    if len(filt_after) != 1 or _canon(filt_after[0]) != filt_canon_before:
        raise IntegrityError("CLS-FILTER block changed — must be byte-identical")

    blob = _canon(reg).encode("utf-8")
    artifact = {"registry": reg, "sha256": hashlib.sha256(blob).hexdigest()}
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    verify_bybit_registry(path)
    return artifact


# =========================================================================== #
# AMENDMENT-4 (design §14) — derived n_legs_floor stage-2 domain guard
# Operator-directed follow-up (report §8). Fresh banks; block rule kept.
#
# INFR-022: the AMENDMENT-7 / L-56 detection-floor apparatus is SUPERSEDED for live use.
# This section is retained as historical CAL replay; the executable paths run gross-only
# without floors (``derive_n_legs_floor`` remains as a pure historical calculator).
# =========================================================================== #
FLOOR_GRID = (0, 4, 6, 8, 10, 12, 16, 20, 24, 32)
DESIGN_SEEDS_A4 = {"low": 99_000, "high": 100_000}
CONFIRM_SEEDS_A4 = {"low": 101_000, "high": 102_000}
BITE_SEEDS_A4 = {"low": 955_000, "high": 956_000}
_SPENT_15_RANGES = (
    (95_000, 95_500), (96_000, 96_500), (97_000, 97_500), (98_000, 98_500),
    (953_000, 953_050), (954_000, 954_050),
)


def assert_seed_disjoint_a4() -> None:
    d = set(range(DESIGN_SEEDS_A4["low"], DESIGN_SEEDS_A4["low"] + 500)) | set(
        range(DESIGN_SEEDS_A4["high"], DESIGN_SEEDS_A4["high"] + 500))
    c = set(range(CONFIRM_SEEDS_A4["low"], CONFIRM_SEEDS_A4["low"] + 500)) | set(
        range(CONFIRM_SEEDS_A4["high"], CONFIRM_SEEDS_A4["high"] + 500))
    b = set(range(BITE_SEEDS_A4["low"], BITE_SEEDS_A4["low"] + 50)) | set(
        range(BITE_SEEDS_A4["high"], BITE_SEEDS_A4["high"] + 50))
    prior = set()
    for lo, hi in (_INFR014_SEED_RANGES + _CH03_SEED_RANGES + _SPENT_15_RANGES):
        prior |= set(range(lo, hi))
    if d & c or d & b or c & b:
        raise IntegrityError("A4 bank collision (design/confirm/bite)")
    for name, s in (("design", d), ("confirm", c), ("bite", b)):
        if s & prior:
            raise IntegrityError(
                f"A4 {name} bank collides with spent INFR-015/INFR-014/ch03 seeds")


def eval_lcb_legs_ep_floor(subset, streams, config, segment, *, n_boot: int, seed: int) -> dict:
    """Historical AMENDMENT-4 entry point — the n_legs_floor domain guard is RETIRED
    (INFR-022 L-63); this routes to the blocked gross estimator :func:`eval_lcb_legs_ep`."""
    return eval_lcb_legs_ep(subset, streams, config, segment, n_boot=n_boot, seed=seed)


def derive_n_legs_floor(design_rows_by_cadence: dict[str, dict],
                        *, alpha: float = ALPHA,
                        grid: tuple[int, ...] = FLOOR_GRID) -> dict[str, Any]:
    """F* = smallest F in grid s.t. cov(F) <= alpha AND alpha_hat(F) <= alpha on BOTH
    cadences (design §14.2). Post-hoc monotone filtering of floor-OFF design rows —
    a row false-certifies under F iff gross_pass (or pass) AND n_legs >= F.
    """
    curve = []
    chosen = None
    for f in grid:
        entry: dict[str, Any] = {"floor": int(f), "per_cadence": {}}
        all_ok = True
        for cad, banks in design_rows_by_cadence.items():
            cov_rows = banks["coverage_rows"]
            a_rows = banks["alpha_rows"]
            n_cov = len(cov_rows)
            n_a = len(a_rows)
            cov_k = sum(1 for r in cov_rows
                        if r["pass"] and (r["n_legs"] or 0) >= f)
            a_k = sum(1 for r in a_rows
                      if r["gross_pass"] and (r["n_legs"] or 0) >= f)
            ood_a = sum(1 for r in a_rows if (r["n_legs"] or 0) < f) / max(n_a, 1)
            cov_rate = cov_k / max(n_cov, 1)
            a_rate = a_k / max(n_a, 1)
            ok = cov_rate <= alpha and a_rate <= alpha
            all_ok = all_ok and ok
            entry["per_cadence"][cad] = {
                "cov": cov_rate, "alpha_hat": a_rate,
                "out_of_domain_frac": ood_a, "ok": ok,
            }
        entry["all_ok"] = all_ok
        curve.append(entry)
        if all_ok and chosen is None:
            chosen = int(f)
    return {
        "grid": list(grid), "curve": curve, "floor_star": chosen,
        "rule": ("F* = smallest F in grid with design cov(F)<=alpha AND "
                 "alpha_hat(F)<=alpha on BOTH cadences; None => TERMINAL-3"),
        "alpha": float(alpha),
    }


def _bank_rows_ep(cadence: CadenceSpec, *, scale: ScaleSpec, seeds: dict[str, int],
                  n_universes_cov: int, n_null_e2e: int) -> dict[str, Any]:
    """Floor-OFF coverage + e2e rows (with n_legs) for the A4 design bank."""
    _set_seeds(seeds["low"], seeds["high"])
    cov = no_search_coverage_ep(cadence, scale=scale, n_universes=n_universes_cov)
    _set_seeds(seeds["low"], seeds["high"])
    sc = ScaleSpec(scale.name, n_null=n_null_e2e, n_cand=scale.n_cand,
                   budget=scale.budget, n_restarts=scale.n_restarts,
                   n_power=scale.n_power, n_coverage=scale.n_coverage)
    a = e2e_alpha_ep(cadence, scale=sc)
    return {"coverage_rows": cov["rows"], "alpha_rows": a["rows"],
            "cov_rate_floor_off": cov["rate"], "alpha_hat_floor_off": a["alpha_hat"],
            "seed_bases": a["seed_bases"]}


def bite_check_a4(cadence: CadenceSpec, *, scale: ScaleSpec,
                  n: int = BITE_N) -> dict[str, Any]:
    """Bite on A4 banks (gross-only; the floor guard is retired, INFR-022)."""
    layout = c_layout(cadence.n_bars, cadence.hold_bars, embargo_frac=EMBARGO_FRAC)
    stage2_start = layout.gate[0]
    base = BITE_SEEDS_A4[cadence.name]
    survive = selected = 0
    rows = []
    for i in range(n):
        seed = base + i
        streams = make_episode_null_universe(
            seed, cadence, n_candidates=scale.n_cand, edge_bps=BITE_EDGE_BPS, plant=True)
        streams = deplant_stage2(streams, edge_bps=BITE_EDGE_BPS,
                                 stage2_start_ns=stage2_start)
        streams = _deplant_class_plants(streams, edge_bps=BITE_EDGE_BPS,
                                        stage2_start_ns=stage2_start)
        assert_stage1_zero_cost(charge_costs=False, score_kind="g_gross")
        config = OracleConfig(charge_costs=False)
        params = _search_params(cadence)
        finalists = [
            run_restart(streams, config, budget=scale.budget, restart_id=r + 1,
                        params=params, segment=layout.search,
                        skip_economics_precondition=True)
            for r in range(scale.n_restarts)
        ]
        folds = contiguous_purged_folds(
            layout.ranking[0], layout.ranking[1], n_folds=3,
            purge_ns=max(cadence.hold_bars, 1) * 60 * NS)
        pkg = certify_and_rank(finalists, streams, config, folds=folds, params=params,
                               search_segment=layout.search, include_random_ref=False,
                               include_fill_basis=False)
        if not pkg["ranked"]:
            rows.append({"seed": seed, "empty": True})
            continue
        top = pkg["ranked"][0].subset
        top_ids = sorted(str(x) for x in top)
        plant_in = any(t.startswith("epplant") for t in top_ids)
        lcb_g = eval_lcb_legs_ep_floor(top, streams, config, layout.gate,
                                       n_boot=N_BOOT, seed=seed)
        selected += int(plant_in)
        survive += int(bool(lcb_g.get("pass_positive")))
        rows.append({"seed": seed, "plant_in_top": plant_in,
                     "stage2_pass": bool(lcb_g.get("pass_positive")),
                     "gross_lcb": lcb_g.get("lcb"), "n_legs": lcb_g.get("n_legs"),
                     "block_legs_used": lcb_g.get("block_legs_used")})
    survival_rate = survive / max(n, 1)
    select_rate = selected / max(n, 1)
    return {
        "class_id": CLASS_ID, "cadence": cadence.name, "n": n,
        "stage2_survival_rate": survival_rate, "stage1_select_rate": select_rate,
        "select_ok": bool(select_rate >= BITE_SELECT_MIN),
        "survival_ok": bool(survival_rate <= BITE_SURVIVAL_MAX),
        "bite_ok": bool(select_rate >= BITE_SELECT_MIN
                        and survival_rate <= BITE_SURVIVAL_MAX),
        "rows": rows,
    }


def run_design_a4(*, scale: ScaleSpec = DESIGN_SCALE_15) -> dict[str, Any]:
    """A4 design bank (historical): cov+e2e rows, floor derivation as DISCLOSURE ONLY
    (the floor guard is retired, INFR-022), bite + freeze gross-only."""
    assert_seed_disjoint_a4()
    print("[INFR-015/A4] DESIGN: cov+e2e rows (floor guard retired — disclosure only)...",
          flush=True)
    rows_by: dict[str, dict] = {}
    for c in (LOW, HIGH):
        rows_by[c.name] = _bank_rows_ep(
            c, scale=scale, seeds=DESIGN_SEEDS_A4,
            n_universes_cov=scale.n_coverage, n_null_e2e=scale.n_null)
        r = rows_by[c.name]
        print(f"  {c.name}: cov={r['cov_rate_floor_off']:.4f} "
              f"alpha={r['alpha_hat_floor_off']:.4f} bases={r['seed_bases']}",
              flush=True)
    # Historical calculator kept for the record; nothing binds on it after INFR-022.
    derivation = derive_n_legs_floor(rows_by)
    print(f"[INFR-015/A4] historical floor curve done; F* (DISCLOSURE ONLY) = "
          f"{derivation['floor_star']}", flush=True)

    print("[INFR-015/A4] bite (gross-only)...", flush=True)
    bite: dict[str, Any] = {}
    for c in (LOW, HIGH):
        b = bite_check_a4(c, scale=scale)
        bite[c.name] = b
        print(f"  bite {c.name}: survival={b['stage2_survival_rate']:.3f} "
              f"select={b['stage1_select_rate']:.3f} ok={b['bite_ok']}", flush=True)
    bite_ok = all(bite[c]["bite_ok"] for c in ("low", "high"))
    if not bite_ok:
        return {"bank": "design_a4", "class_id": CLASS_ID,
                "seeds": dict(DESIGN_SEEDS_A4), "floor_derivation": derivation,
                "bite": {k: {kk: vv for kk, vv in v.items() if kk != "rows"}
                         for k, v in bite.items()},
                "frozen_procedure": None, "design_ok": False,
                "stop_reason": "bite_failed", "terminal": True,
                "recommend": "TERMINAL_temporal_independence_failed"}

    frozen = {
        "binder": "two_stage_sample_split",
        "stage1": "search+certify top-1 on stage-1 bands",
        "stage1_score_kind": "g_gross",
        "stage1_charge_costs": False,
        "stage2": "lcb_g_leg_studentized(g_gross) > 0 on distant embargoed band",
        "e2e_pass_event": "stage2_gross_lcb_positive",
        "deployability_binding": "RETIRED (INFR-022 zero-cost; historical: stage2_net_lcb_positive)",
        "functional": "g_gross_ratio",
        "estimator": "leg_studentized_bootstrap_t",
        "embargo_frac": EMBARGO_FRAC,
        "search_frac": STAGE_SEARCH_FRAC,
        "ranking_frac": STAGE_RANKING_FRAC,
        "n_boot": N_BOOT,
        "block_legs": BLOCK_RULE_ID,
        "n_legs_floor": "RETIRED (INFR-022 L-63)",
        "n_legs_floor_rule": "RETIRED — historical derivation only: " + derivation["rule"],
        "confidence": 0.95,
        "alpha": ALPHA,
        "one_subset": True,
        "shortlist": False,
        "design_seeds": dict(DESIGN_SEEDS_A4),
        "confirm_seeds": dict(CONFIRM_SEEDS_A4),
        "design_bite_ok": True,
        "held_out_escalation": False,
        "gate_rule": "per_cadence point α̂≤5% AND no-search cov≤5% (Fork A)",
        "cost_stack": "bybit_round_trip_cost_bps_v2_no_spread",
        "spread_cost_status": "UNAVAILABLE_NOT_CHARGED",
        "cost_scope": "PARTIAL_FEES_FUNDING_ONLY",
        "class_id": CLASS_ID,
        "amends": "INFR-015 AMENDMENT-4 (floor guard RETIRED by INFR-022; block rule kept)",
    }
    return {"bank": "design_a4", "class_id": CLASS_ID, "seeds": dict(DESIGN_SEEDS_A4),
            "floor_derivation": derivation,
            "bite": {k: {kk: vv for kk, vv in v.items() if kk != "rows"}
                     for k, v in bite.items()},
            "bite_rows": {k: v["rows"] for k, v in bite.items()},
            "rows_by_cadence": rows_by,
            "frozen_procedure": frozen, "design_ok": True, "stop_reason": None}


def no_search_coverage_a4(cadence: CadenceSpec, *, scale: ScaleSpec, n_universes: int,
                          n_boot: int = N_BOOT, alpha: float = ALPHA) -> dict[str, Any]:
    """No-search blocked-LCB pass rate (gross-only; floor retired, INFR-022)."""
    config = OracleConfig(charge_costs=False)
    layout = c_layout(cadence.n_bars, cadence.hold_bars, embargo_frac=EMBARGO_FRAC)
    hits = 0
    rows = []
    seed_bases = {"low": int(p3b.SEED_BASE_LOW), "high": int(p3b.SEED_BASE_HIGH)}
    for seed, cspec in bank_seeds(cadence, n_universes):
        streams = make_episode_null_universe(
            seed, cspec, n_candidates=scale.n_cand, edge_bps=0.0, plant=False)
        rng = np.random.default_rng(seed + 91)
        ids = [s.candidate_id for s in streams]
        k = min(5, len(ids))
        pick = frozenset(str(x) for x in rng.choice(ids, size=k, replace=False))
        lcb = eval_lcb_legs_ep_floor(pick, streams, config, layout.gate, n_boot=n_boot,
                                     seed=seed)
        pos = bool(lcb.get("pass_positive"))
        hits += int(pos)
        rows.append({"seed": seed, "pass": pos, "lcb": lcb.get("lcb"),
                     "n_legs": lcb.get("n_legs"),
                     "block_legs_used": lcb.get("block_legs_used")})
    n = len(rows)
    rate = hits / max(n, 1)
    return {"class_id": CLASS_ID, "cadence": cadence.name, "n": n,
            "n_lcb_positive": hits, "rate": rate,
            "coverage_ok": bool(n > 0 and rate <= float(alpha)), "rows": rows,
            "seed_bases": seed_bases, "alpha_target": float(alpha),
            "block_rule": BLOCK_RULE_ID}


def e2e_alpha_a4(cadence: CadenceSpec, *, scale: ScaleSpec,
                 n_boot: int = N_BOOT, alpha: float = ALPHA) -> dict[str, Any]:
    """Full two-stage over null bank (gross-only; floor + net retired, INFR-022)."""
    layout_by: dict = {}
    rows = []
    seed_bases = {"low": int(p3b.SEED_BASE_LOW), "high": int(p3b.SEED_BASE_HIGH)}
    config = OracleConfig(charge_costs=False)
    for seed, cspec in bank_seeds(cadence, scale.n_null):
        key = (cspec.n_bars, cspec.hold_bars)
        layout = layout_by.get(key) or c_layout(
            cspec.n_bars, cspec.hold_bars, embargo_frac=EMBARGO_FRAC)
        layout_by[key] = layout
        streams = make_episode_null_universe(
            seed, cspec, n_candidates=scale.n_cand, edge_bps=0.0, plant=False)
        params = _search_params(cspec)
        finalists = [
            run_restart(streams, config, budget=scale.budget, restart_id=r + 1,
                        params=params, segment=layout.search,
                        skip_economics_precondition=True)
            for r in range(scale.n_restarts)
        ]
        folds = contiguous_purged_folds(
            layout.ranking[0], layout.ranking[1], n_folds=3,
            purge_ns=max(cspec.hold_bars, 1) * 60 * NS)
        pkg = certify_and_rank(finalists, streams, config, folds=folds, params=params,
                               search_segment=layout.search, include_random_ref=False,
                               include_fill_basis=False)
        if not pkg["ranked"]:
            rows.append({"seed": seed, "symbol": cspec.symbol, "gross_pass": False,
                         "empty": True, "n_legs": 0})
            continue
        top = pkg["ranked"][0].subset
        lcb_g = eval_lcb_legs_ep_floor(top, streams, config, layout.gate,
                                       n_boot=n_boot, seed=seed)
        rows.append({
            "seed": seed, "symbol": cspec.symbol,
            "gross_pass": bool(lcb_g.get("pass_positive")),
            "gross_lcb": lcb_g.get("lcb"), "gross_point": lcb_g.get("point"),
            "n_legs": lcb_g.get("n_legs"),
            "block_legs_used": lcb_g.get("block_legs_used"), "empty": False,
        })
    n = len(rows)
    k = sum(1 for r in rows if r["gross_pass"])
    ph = k / max(n, 1)
    lo, hi = wilson(k, n)
    return {"class_id": CLASS_ID, "cadence": cadence.name, "n": n,
            "n_gross_lcb_positive": k, "alpha_hat": ph,
            "alpha_se": binomial_se(ph, n),
            "alpha_wilson_95": {"low": lo, "high": hi},
            "pass_stop": bool(ph <= float(alpha)),
            "seed_bases": seed_bases, "alpha_target": float(alpha),
            "block_rule": BLOCK_RULE_ID,
            "rows": rows}


def confirm_gate_a4(procedure: dict, *,
                    scale: ScaleSpec = CONFIRM_SCALE_15) -> dict[str, Any]:
    """Binding A4 confirm: blocked stage-2, gross-only (the n_legs_floor guard is
    retired, INFR-022); fresh 101k/102k banks."""
    if not procedure or not procedure.get("design_bite_ok"):
        raise IntegrityError("confirm blocked unless design_ok procedure exists")
    required = ("embargo_frac", "n_boot", "block_legs", "alpha", "stage1_score_kind",
                "stage1_charge_costs", "e2e_pass_event")
    for k in required:
        if k not in procedure:
            raise IntegrityError(f"frozen procedure missing {k} (G4b)")
    if procedure["block_legs"] != BLOCK_RULE_ID:
        raise IntegrityError("A4 confirm requires episode_overlap_rule_v1")
    assert_stage1_zero_cost(
        charge_costs=bool(procedure["stage1_charge_costs"]),
        score_kind=str(procedure["stage1_score_kind"]))
    assert_seed_disjoint_a4()
    n_boot = int(procedure["n_boot"])
    alpha = float(procedure["alpha"])
    if scale.name == "confirm" and scale.n_null != CONFIRM_SCALE_15.n_null:
        raise IntegrityError("binding confirm n_null must be 200")

    per: dict[str, Any] = {}
    _set_seeds(CONFIRM_SEEDS_A4["low"], CONFIRM_SEEDS_A4["high"])
    for c in (LOW, HIGH):
        print(f"[INFR-015/A4] CONFIRM {c.name}: coverage...", flush=True)
        cov = no_search_coverage_a4(c, scale=scale, n_universes=scale.n_coverage,
                                    n_boot=n_boot, alpha=alpha)
        if cov.get("seed_bases") != dict(CONFIRM_SEEDS_A4):
            raise IntegrityError("A4 confirm coverage seed bases drifted (Issue-9 class)")
        print(f"  cov {c.name}: {cov['rate']:.4f} ok={cov['coverage_ok']}", flush=True)
        print(f"[INFR-015/A4] CONFIRM {c.name}: e2e α...", flush=True)
        a = e2e_alpha_a4(c, scale=scale, n_boot=n_boot, alpha=alpha)
        if a.get("seed_bases") != dict(CONFIRM_SEEDS_A4):
            raise IntegrityError("A4 confirm e2e seed bases drifted")
        print(f"  α̂ {c.name}: {a['alpha_hat']:.4f} ok={a['pass_stop']}", flush=True)
        certified = bool(cov["coverage_ok"] and a["pass_stop"])
        band = "CERTIFIED" if certified else (
            "FAIL_ALPHA" if not a["pass_stop"] else "FAIL_COV")
        per[c.name] = {
            "cadence": c.name, "band": band,
            "no_search_cov": cov["rate"], "e2e_alpha": a["alpha_hat"],
            "selection_inflation": a["alpha_hat"] - cov["rate"],
            "coverage_ok": cov["coverage_ok"], "alpha_ok": a["pass_stop"],
            "certified": certified, "alpha_se": a["alpha_se"],
            "alpha_wilson_95": a["alpha_wilson_95"], "n": a["n"],
            "n_gross_lcb_positive": a["n_gross_lcb_positive"],
            "seed_bases": a.get("seed_bases"), "alpha_target": alpha,
            "failure_label": (None if certified
                              else _failure_label(cov["rate"], a["alpha_hat"])),
            "coverage_rows": cov["rows"], "alpha_rows": a["rows"],
        }
    outcome = _outcome(per["low"]["certified"], per["high"]["certified"])
    return {
        "bank": "confirm_a4", "class_id": CLASS_ID, "seeds": dict(CONFIRM_SEEDS_A4),
        "procedure": procedure,
        "per_cadence": {k: {kk: vv for kk, vv in v.items()
                            if kk not in ("coverage_rows", "alpha_rows")}
                        for k, v in per.items()},
        "alpha_low_rows": per["low"]["alpha_rows"],
        "alpha_high_rows": per["high"]["alpha_rows"],
        "coverage_low_rows": per["low"]["coverage_rows"],
        "coverage_high_rows": per["high"]["coverage_rows"],
        "outcome": outcome,
        "stop_condition": {
            "alpha_target": alpha,
            "gate_rule": (f"point α̂≤{alpha} ∧ no_search_cov≤{alpha} "
                          "(gross-only; Wilson disclosure-only)"),
            "low_certified": per["low"]["certified"],
            "high_certified": per["high"]["certified"],
            "verdict": outcome["verdict"], "recommend": outcome["recommend"],
            "terminal": outcome["terminal"],
            "forbidden": [
                "no optional stopping", "no peek-and-extend", "no UCB gate",
                "no chapter-03 pin",
                "confirm coverage must use confirm seeds (not design)",
                "TERMINAL => fallback paths are NEW designs (report §8)",
            ],
        },
    }
