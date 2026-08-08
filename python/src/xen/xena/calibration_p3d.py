"""INFR-009 P3d — design/confirm split; leg bootstrap + per-cadence L.

> **LEGACY CAL APPARATUS (INFR-022).** Not bindable on the live research path without a
> post-INFR-022 CAL redesign. Retired names used here for historical replay only: the NET
> LCB path (zero-cost model). INFR-022: gross-only LCBs; sample size as context.

Last estimator-calibration round. Confirm fail → binder-form fork (not implemented).
"""
from __future__ import annotations

import numpy as np
from typing import Any

import xen.xena.calibration_p3b as p3b
from xen.xena.calibration_p3b import (HIGH, LOW, CadenceSpec, ScaleSpec, _layout,
                                      bank_seeds, block_candidates, make_null_universe)
from xen.xena.certify import certify_and_rank, contiguous_purged_folds
from xen.xena.oracle import OracleConfig, evaluate
from xen.xena.score import lcb_g_leg_studentized, lcb_g_studentized
from xen.xena.search import (SearchParams, bootstrap_block_starts, clip_grid_covering,
                             run_restart, universe_grid)

ALPHA = 0.05
LCB_CONF = 0.95
NS = 1_000_000_000

# Disjoint from P3/P3b/P3c and each other
DESIGN_SEEDS = (31_000, 32_000)
CONFIRM_SEEDS = (41_000, 42_000)

DESIGN_SCALE = ScaleSpec("design", n_null=80, n_cand=64, budget=200, n_restarts=5,
                         n_power=6, n_coverage=80)
CONFIRM_SCALE = ScaleSpec("confirm", n_null=200, n_cand=64, budget=200, n_restarts=5,
                          n_power=6, n_coverage=200)


def _set_seeds(low: int, high: int) -> None:
    p3b.SEED_BASE_LOW = low
    p3b.SEED_BASE_HIGH = high


def binomial_se(p: float, n: int) -> float:
    p = min(max(p, 0.0), 1.0)
    return float(np.sqrt(p * (1 - p) / n)) if n > 0 else float("nan")


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return float("nan"), float("nan")
    ph = k / n
    d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    m = (z / d) * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n))
    return float(max(0, c - m)), float(min(1, c + m))


# --------------------------------------------------------------------------- #
# LCB evaluators
# --------------------------------------------------------------------------- #
def eval_lcb_calendar(subset, streams, config, segment, *, block: int, n_boot: int,
                      seed: int) -> dict:
    """Calendar studentized LCB on g_gross (gross-only, INFR-022)."""
    res = evaluate(subset, streams, config, segment=segment, seed=seed)
    grid = clip_grid_covering(universe_grid(streams), segment, streams)
    if len(grid) < 2:
        return {"pass_positive": False, "lcb": float("-inf"), "method": "calendar_st",
                "empty_grid": True}
    starts = bootstrap_block_starts(len(grid), block=block, n_boot=n_boot, seed=17_001 + seed)
    out = lcb_g_studentized(res, streams, grid, starts, block=block,
                            confidence=LCB_CONF)
    out["n_admitted"] = res.n_admitted
    out["empty_grid"] = False
    return out


def eval_lcb_legs(subset, streams, config, segment, *, n_boot: int, seed: int,
                  block_legs: int = 1) -> dict:
    """Leg-studentized LCB on g_gross (gross-only, INFR-022)."""
    res = evaluate(subset, streams, config, segment=segment, seed=seed)
    out = lcb_g_leg_studentized(res, streams, n_boot=n_boot, seed=seed + 99,
                                block_legs=block_legs, confidence=LCB_CONF)
    out["n_admitted"] = res.n_admitted
    return out


def coverage(cadence: CadenceSpec, *, method: str, block: int | None, n_boot: int,
             n_universes: int, n_cand: int, subset_size: int = 5,
             block_legs: int = 1, purge_mult: int = 1) -> dict:
    """No-search coverage under a frozen LCB method."""
    config = OracleConfig(charge_costs=False)
    layout = _layout(cadence.n_bars, cadence.hold_bars, purge_mult=purge_mult)
    hits = 0
    rows = []
    for seed, cspec in bank_seeds(cadence, n_universes):
        streams = make_null_universe(seed, cspec, n_candidates=n_cand)
        rng = np.random.default_rng(seed + 7)
        ids = [s.candidate_id for s in streams]
        k = min(subset_size, len(ids))
        pick = frozenset(str(x) for x in rng.choice(ids, size=k, replace=False))
        if method == "leg_studentized":
            lcb = eval_lcb_legs(pick, streams, config, layout.gate, n_boot=n_boot,
                                seed=seed, block_legs=block_legs)
        else:
            L = max(block or cadence.hold_bars, cadence.hold_bars)
            lcb = eval_lcb_calendar(pick, streams, config, layout.gate, block=L,
                                    n_boot=n_boot, seed=seed)
        pos = bool(lcb.get("pass_positive"))
        hits += int(pos)
        rows.append({"seed": seed, "pass": pos, "lcb": lcb.get("lcb"),
                     "n_legs": lcb.get("n_legs"),
                     "empty_bar_fraction": lcb.get("empty_bar_fraction")})
    rate = hits / max(n_universes, 1)
    return {
        "cadence": cadence.name, "method": method, "block": block,
        "block_legs": block_legs, "n_boot": n_boot,
        "n": n_universes, "n_lcb_positive": hits, "rate": rate,
        "coverage_ok": rate <= ALPHA, "rows": rows,
    }


# --------------------------------------------------------------------------- #
# DESIGN bank fit
# --------------------------------------------------------------------------- #
def design_fit_l_rule_and_interval(*, scale: ScaleSpec = DESIGN_SCALE,
                                   purge_mult: int = 1) -> dict[str, Any]:
    """Fit ladder (1)→(2)→… on design bank; return frozen procedure."""
    _set_seeds(*DESIGN_SEEDS)
    n = scale.n_coverage
    n_cand = scale.n_cand
    trace: list[dict] = []
    frozen: dict[str, Any] = {
        "purge_mult": purge_mult,
        "alpha": ALPHA,
        "lcb_confidence": LCB_CONF,
    }

    # ---- (1) more B calendar studentized ----
    print("[design] (1) calendar studentized B=200 vs B=400...", flush=True)
    for B in (200, 400):
        for c in (LOW, HIGH):
            for L in block_candidates(c.hold_bars)[:4]:  # short set
                cov = coverage(c, method="calendar_studentized", block=L, n_boot=B,
                               n_universes=n, n_cand=n_cand, purge_mult=purge_mult)
                trace.append({"step": 1, "B": B, **{k: v for k, v in cov.items()
                                                     if k != "rows"}})
    # check if any joint calendar config works both
    # (expected: high never ≤5%)
    high_ok_1 = any(t["coverage_ok"] and t["cadence"] == "high" and t["step"] == 1
                    for t in trace)
    print(f"  step1 high ever OK? {high_ok_1}", flush=True)

    # ---- (2) leg bootstrap studentized (mechanistic) ----
    print("[design] (2) leg-studentized bootstrap B=400 block_legs=1...", flush=True)
    selected_method = None
    for B in (200, 400):
        for bl in (1, 2, 4):
            low_c = coverage(LOW, method="leg_studentized", block=None, n_boot=B,
                             n_universes=n, n_cand=n_cand, block_legs=bl,
                             purge_mult=purge_mult)
            high_c = coverage(HIGH, method="leg_studentized", block=None, n_boot=B,
                              n_universes=n, n_cand=n_cand, block_legs=bl,
                              purge_mult=purge_mult)
            trace.append({"step": 2, "B": B, "block_legs": bl,
                          "low_rate": low_c["rate"], "high_rate": high_c["rate"],
                          "low_ok": low_c["coverage_ok"], "high_ok": high_c["coverage_ok"]})
            print(f"  B={B} bl={bl} low={low_c['rate']:.3f} high={high_c['rate']:.3f}",
                  flush=True)
            if low_c["coverage_ok"] and high_c["coverage_ok"] and selected_method is None:
                selected_method = {
                    "interval": "leg_studentized",
                    "n_boot": B,
                    "block_legs": bl,
                    "low": {"method": "leg_studentized", "block_legs": bl, "n_boot": B},
                    "high": {"method": "leg_studentized", "block_legs": bl, "n_boot": B},
                    "design_low_coverage_ok": True,
                    "design_high_coverage_ok": True,
                    "design_low_rate": low_c["rate"],
                    "design_high_rate": high_c["rate"],
                }

    # ---- per-cadence: if leg works for high only, pair with short calendar L for low ----
    if selected_method is None:
        print("[design] mixed: fit low short calendar L + high leg...", flush=True)
        # best high leg config (min rate)
        high_opts = [t for t in trace if t.get("step") == 2]
        high_opts.sort(key=lambda t: t["high_rate"])
        best_h = high_opts[0] if high_opts else {"B": 400, "block_legs": 1, "high_rate": 1.0}
        # low short L with calendar B=400
        low_L = None
        for L in sorted({LOW.hold_bars, 2 * LOW.hold_bars, 16, 24, 32}):
            if L < LOW.hold_bars:
                continue
            cov = coverage(LOW, method="calendar_studentized", block=L, n_boot=400,
                           n_universes=n, n_cand=n_cand, purge_mult=purge_mult)
            trace.append({"step": "2b_low_L", "L": L, "rate": cov["rate"],
                          "ok": cov["coverage_ok"]})
            if cov["coverage_ok"] and low_L is None:
                low_L = L
        if low_L is None:
            low_L = LOW.hold_bars  # best-effort short
        selected_method = {
            "interval": "per_cadence_mixed",
            "low": {"method": "calendar_studentized", "block": low_L, "n_boot": 400},
            "high": {"method": "leg_studentized", "block_legs": best_h["block_legs"],
                     "n_boot": best_h["B"]},
            "design_high_rate": best_h["high_rate"],
            "design_low_L": low_L,
        }
        # re-check high with best
        hc = coverage(HIGH, method="leg_studentized", block=None, n_boot=best_h["B"],
                      n_universes=n, n_cand=n_cand, block_legs=best_h["block_legs"],
                      purge_mult=purge_mult)
        selected_method["design_high_coverage_ok"] = hc["coverage_ok"]
        selected_method["design_high_rate"] = hc["rate"]
        lc = coverage(LOW, method="calendar_studentized", block=low_L, n_boot=400,
                      n_universes=n, n_cand=n_cand, purge_mult=purge_mult)
        selected_method["design_low_coverage_ok"] = lc["coverage_ok"]
        selected_method["design_low_rate"] = lc["rate"]

    frozen.update(selected_method)
    both_ok = bool(selected_method.get("design_low_coverage_ok") and
                   selected_method.get("design_high_coverage_ok"))
    if selected_method.get("interval") == "leg_studentized" and both_ok:
        ladder = "(2) leg_studentized both cadences"
    elif selected_method.get("interval") == "per_cadence_mixed":
        ladder = "(2) mixed: low calendar short-L + high leg_studentized"
    else:
        ladder = "partial — design did not clear both cadences fully"

    return {
        "bank": "design",
        "seeds": {"low": DESIGN_SEEDS[0], "high": DESIGN_SEEDS[1]},
        "scale": scale.name,
        "n_null": scale.n_null,
        "trace": [t for t in trace if t.get("step") != 1 or True],  # keep full
        "frozen_procedure": frozen,
        "design_coverage_both_ok": both_ok,
        "ladder_stop": ladder,
    }


def _lcb_for_procedure(subset, streams, config, segment, *, cadence_name: str,
                       procedure: dict, seed: int) -> dict:
    cfg = procedure.get(cadence_name) or procedure.get("high")
    method = cfg["method"]
    if method == "leg_studentized":
        return eval_lcb_legs(subset, streams, config, segment,
                             n_boot=cfg.get("n_boot", 400), seed=seed,
                             block_legs=cfg.get("block_legs", 1))
    return eval_lcb_calendar(subset, streams, config, segment,
                             block=cfg.get("block", 32), n_boot=cfg.get("n_boot", 400),
                             seed=seed)


def e2e_alpha(cadence: CadenceSpec, *, procedure: dict, scale: ScaleSpec,
              purge_mult: int = 1) -> dict:
    # Seeds must already be set by caller (design vs confirm).
    config = OracleConfig(charge_costs=False)
    params = SearchParams(L=40, n_boot=80, block_bars=max(64, cadence.hold_bars), init_size=4)
    rows = []
    for seed, cspec in bank_seeds(cadence, scale.n_null):
        streams = make_null_universe(seed, cspec, n_candidates=scale.n_cand)
        layout = _layout(cadence.n_bars, cadence.hold_bars, purge_mult=purge_mult)
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
            rows.append({"seed": seed, "gross_pass": False, "empty": True})
            continue
        top = pkg["ranked"][0].subset
        g = _lcb_for_procedure(top, streams, config, layout.gate,
                               cadence_name=cadence.name, procedure=procedure, seed=seed)
        rows.append({
            "seed": seed, "gross_pass": bool(g.get("pass_positive")),
            "gross_lcb": g.get("lcb"), "gross_point": g.get("point"),
            "g_search_hat": pkg["ranked"][0].search_F_hat,
            "n_legs": g.get("n_legs"), "method": g.get("method"),
            "empty": False,
        })
    n = len(rows)
    k = sum(1 for r in rows if r.get("gross_pass"))
    ph = k / max(n, 1)
    lo, hi = wilson(k, n)
    return {
        "cadence": cadence.name, "n": n, "n_gross_lcb_positive": k,
        "alpha_hat": ph, "alpha_se": binomial_se(ph, n),
        "alpha_wilson_95": {"low": lo, "high": hi},
        "pass_stop": ph <= ALPHA,
        "rows": rows,
    }


def confirm_gate(procedure: dict, *, scale: ScaleSpec = CONFIRM_SCALE,
                 purge_mult: int = 1) -> dict[str, Any]:
    _set_seeds(*CONFIRM_SEEDS)
    print("[confirm] coverage low/high...", flush=True)
    # coverage at frozen per-cadence settings
    cov = {}
    for c in (LOW, HIGH):
        cfg = procedure.get(c.name) or procedure["high"]
        if cfg["method"] == "leg_studentized":
            cov[c.name] = coverage(
                c, method="leg_studentized", block=None,
                n_boot=cfg.get("n_boot", 400), n_universes=scale.n_coverage,
                n_cand=scale.n_cand, block_legs=cfg.get("block_legs", 1),
                purge_mult=purge_mult)
        else:
            cov[c.name] = coverage(
                c, method="calendar_studentized", block=cfg.get("block", 32),
                n_boot=cfg.get("n_boot", 400), n_universes=scale.n_coverage,
                n_cand=scale.n_cand, purge_mult=purge_mult)
        print(f"  {c.name} cov rate={cov[c.name]['rate']:.4f} ok={cov[c.name]['coverage_ok']}",
              flush=True)

    print("[confirm] e2e α low...", flush=True)
    a_low = e2e_alpha(LOW, procedure=procedure, scale=scale, purge_mult=purge_mult)
    print(f"  low α̂={a_low['alpha_hat']:.4f}", flush=True)
    print("[confirm] e2e α high...", flush=True)
    a_high = e2e_alpha(HIGH, procedure=procedure, scale=scale, purge_mult=purge_mult)
    print(f"  high α̂={a_high['alpha_hat']:.4f}", flush=True)

    cov_fail = not (cov["low"]["coverage_ok"] and cov["high"]["coverage_ok"])
    alpha_fail = not (a_low["pass_stop"] and a_high["pass_stop"])
    stop = cov_fail or alpha_fail
    return {
        "bank": "confirm",
        "seeds": {"low": CONFIRM_SEEDS[0], "high": CONFIRM_SEEDS[1]},
        "procedure": procedure,
        "coverage": {k: {kk: vv for kk, vv in v.items() if kk != "rows"}
                     for k, v in cov.items()},
        "alpha_low": {k: v for k, v in a_low.items() if k != "rows"},
        "alpha_high": {k: v for k, v in a_high.items() if k != "rows"},
        "alpha_low_rows": a_low["rows"],
        "alpha_high_rows": a_high["rows"],
        "stop_condition": {
            "alpha_target": ALPHA,
            "coverage_fail": cov_fail,
            "alpha_low_fail": not a_low["pass_stop"],
            "alpha_high_fail": not a_high["pass_stop"],
            "STOP": stop,
            "verdict": "STOP" if stop else "PROCEED_TO_P4_ELIGIBLE",
            "gate_rule": "point alpha_hat<=5% both AND coverage<=5% both (per-cadence procedure)",
            "binder_form_fork_if_stop": [
                "(a) LCB on mean per-leg bps with leg bootstrap",
                "(b) permutation/randomization test for g_gross>0",
                "(c) two-stage: intensive screen + different TEST statistic",
            ],
            "note": (
                "If STOP: recommend binder-form fork — do NOT open P3e / more estimator knobs. "
                "If PASS: recommend P4 (operator mandate still required)."
            ),
        },
    }


def run_p3d(*, purge_mult: int = 1) -> tuple[dict, dict]:
    print("[P3d] DESIGN bank fit...", flush=True)
    design = design_fit_l_rule_and_interval(scale=DESIGN_SCALE, purge_mult=purge_mult)
    proc = design["frozen_procedure"]
    print("[P3d] frozen procedure:", proc, flush=True)
    print("[P3d] CONFIRM bank gate...", flush=True)
    confirm = confirm_gate(proc, scale=CONFIRM_SCALE, purge_mult=purge_mult)
    return design, confirm
