"""INFR-009 P-C — binder-form exit (c): two-stage sample-split.

> **LEGACY CAL APPARATUS (INFR-022).** Not bindable on the live research path without a
> post-INFR-022 CAL redesign. Retired names used here for historical replay only: the NET
> LCB path (zero-cost model). INFR-022: gross-only LCBs; sample size as context.

Predeclaration: design.md §P-C (committed 2026-07-14). Parent: §P-BF DESIGN STOP.

Select on a stage-1 band only, then test ONCE on a distant/embargoed stage-2 band with the
**frozen P3d estimator** (leg-studentized LCB on the binding g_gross ratio). Conditional on the
selection, stage-2 is a single fresh test → α controlled by construction. The entire load sits on
stage-2 being genuinely decorrelated from stage-1 — proven per cadence by the P-C.3 bite-check
(a stage-1-only planted edge must NOT survive into stage-2).

No permutation, no K×-search, no tail quantile → host-safe (compute = n_null × (1 search + 1 eval)).

Forks (operator, 2026-07-14):
  A — per-cadence certification (dual-AND retired for (c) gate logic only; α/n/split unchanged).
  B — bite failure → TERMINAL; NO held-out-instrument escalation in this experiment.

Does not call run_final_gate. No XENA-001/002/003 TEST/holdout contact.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import polars as pl

import xen.xena.calibration_p3b as p3b
from xen.xena.calibration import SegmentLayout
from xen.xena.calibration_p3b import (HIGH, LOW, CadenceSpec, ScaleSpec, bank_seeds,
                                      make_null_universe)
from xen.xena.calibration_p3d import binomial_se, eval_lcb_legs, wilson
from xen.xena.certify import certify_and_rank, contiguous_purged_folds
from xen.xena.oracle import CandidateStream, OracleConfig
from xen.xena.search import SearchParams, run_restart

ALPHA = 0.05
NS = 1_000_000_000

# --- frozen procedure (P-C.1/P-C.2; estimator inherited from P3d, embargo predeclared) ---
EMBARGO_FRAC = 0.20            # distant gap between stage-1 (ranking end) and stage-2 (gate start)
STAGE_SEARCH_FRAC = 0.50      # of usable (post-embargo) span
STAGE_RANKING_FRAC = 0.25
N_BOOT = 200                   # leg bootstrap replicates (P3d frozen)
BLOCK_LEGS = 1                 # IID leg bootstrap (P3d frozen)

# --- bite-check thresholds (P-C.3; frozen before any run) ---
BITE_EDGE_BPS = 20.0
BITE_N = 8
BITE_SURVIVAL_MAX = 0.125      # α + tol (0.05 + 0.075); small-n (n=8) design band
BITE_SELECT_MIN = 0.5          # sanity: stage-1 must actually select the plant
BITE_SEEDS = {"low": 791_000, "high": 792_000}  # disjoint from all P3*/P-BF banks
_SELECTION_INFLATION_MAX = 0.02  # forensics label boundary (coverage-limited vs selection-unsafe)

# --- design/confirm split (P-C.4; disjoint from every prior bank) ---
DESIGN_SEEDS = (71_000, 72_000)
CONFIRM_SEEDS = (81_000, 82_000)
DESIGN_SCALE = ScaleSpec("design", n_null=80, n_cand=64, budget=200, n_restarts=5,
                         n_power=6, n_coverage=80)
CONFIRM_SCALE = ScaleSpec("confirm", n_null=200, n_cand=64, budget=200, n_restarts=5,
                          n_power=6, n_coverage=200)

_PLANT_PREFIXES = ("plant", "HCPLANT")


def _set_seeds(low: int, high: int) -> None:
    p3b.SEED_BASE_LOW = low
    p3b.SEED_BASE_HIGH = high


# --------------------------------------------------------------------------- #
# Distant-embargo two-stage layout
# --------------------------------------------------------------------------- #
def c_layout(n_bars: int, hold_bars: int, *, embargo_frac: float = EMBARGO_FRAC,
             bar_seconds: int = 60) -> SegmentLayout:
    """Stage-1 (search+ranking) | large EMBARGO | stage-2 (gate).

    Embargo = ``embargo_frac`` of the full span (low 60·H, high 200·H at 0.20) ≫ regime
    memory (~100 bars). Adjacent-purge (1·H) leaked in P3d — this does not.
    """
    del hold_bars  # scale documented in P-C.2; embargo is span-fraction, not H-multiple
    end = n_bars * bar_seconds * NS
    purge_ns = int(embargo_frac * end)
    return SegmentLayout.from_span(0, end, search_frac=STAGE_SEARCH_FRAC,
                                   ranking_frac=STAGE_RANKING_FRAC, purge_ns=purge_ns)


# --------------------------------------------------------------------------- #
# Stage-1-localized plant (bite-check): de-plant the distant band
# --------------------------------------------------------------------------- #
def deplant_stage2(streams: list[CandidateStream], *, edge_bps: float,
                   stage2_start_ns: int) -> list[CandidateStream]:
    """Remove the planted exit-fill shift from planted-candidate trades in the stage-2 band.

    Both generators plant ``ExitPrice = raw_exit · (1 + d·e/1e4)``; the exact inverse
    ``raw_exit = ExitPrice / (1 + d·e/1e4)`` restores the unplanted exit. Applied only to
    planted candidates (``plant*`` / ``HCPLANT*``) so null candidates (edge=0) are untouched.
    Result: the plant lives in stage-1 only.
    """
    out: list[CandidateStream] = []
    for s in streams:
        if not s.candidate_id.startswith(_PLANT_PREFIXES):
            out.append(s)
            continue
        tr = s.trades
        et = tr.get_column("EntryTime").to_numpy().astype(np.int64)
        d = tr.get_column("Direction").to_numpy().astype(float)
        xp = tr.get_column("ExitPrice").to_numpy().astype(float)
        in_s2 = et >= int(stage2_start_ns)
        raw = xp / (1.0 + d * edge_bps / 1e4)
        new_xp = np.where(in_s2, raw, xp)
        tr2 = tr.with_columns(pl.Series("ExitPrice", new_xp))
        out.append(CandidateStream(s.candidate_id, s.symbol, tr2, s.marks,
                                   s.cost_bps, s.money_per_unit))
    return out


# --------------------------------------------------------------------------- #
# Core two-stage pipeline (select on stage-1 → LCB on stage-2)
# --------------------------------------------------------------------------- #
def _search_params(cadence: CadenceSpec) -> SearchParams:
    return SearchParams(L=40, n_boot=80, block_bars=max(64, cadence.hold_bars), init_size=4)


def run_two_stage(streams: list[CandidateStream], cadence: CadenceSpec,
                  layout: SegmentLayout, *, scale: ScaleSpec, seed: int,
                  n_boot: int = N_BOOT, block_legs: int = BLOCK_LEGS) -> dict[str, Any]:
    """One full stage-1 search→select(top-1) → stage-2 leg-studentized LCB(g_gross).
    Gross-only (INFR-022 zero-cost model)."""
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
        return {"empty": True, "gross_pass": False, "top": []}
    top = pkg["ranked"][0].subset
    lcb = eval_lcb_legs(top, streams, config, layout.gate, n_boot=n_boot, seed=seed,
                        block_legs=block_legs)
    top_ids = sorted(str(x) for x in top)
    return {
        "empty": False,
        "top": top_ids,
        "plant_in_top": any(t.startswith(_PLANT_PREFIXES) for t in top_ids),
        "gross_pass": bool(lcb.get("pass_positive")),
        "gross_lcb": lcb.get("lcb"),
        "gross_point": lcb.get("point"),
        "n_legs": lcb.get("n_legs"),
        "g_search_hat": pkg["ranked"][0].search_F_hat,
    }


# --------------------------------------------------------------------------- #
# Bite-check (P-C.3) — independence proof, per cadence
# --------------------------------------------------------------------------- #
def bite_check(cadence: CadenceSpec, *, scale: ScaleSpec,
               embargo_frac: float = EMBARGO_FRAC, n: int = BITE_N) -> dict[str, Any]:
    """Stage-1-only planted edge must NOT survive into stage-2 (else bands are dependent)."""
    layout = c_layout(cadence.n_bars, cadence.hold_bars, embargo_frac=embargo_frac)
    stage2_start = layout.gate[0]
    base = BITE_SEEDS[cadence.name]
    survive = selected = 0
    rows = []
    for i in range(n):
        seed = base + i
        streams = make_null_universe(seed, cadence, n_candidates=scale.n_cand,
                                     edge_bps=BITE_EDGE_BPS)
        streams = deplant_stage2(streams, edge_bps=BITE_EDGE_BPS,
                                 stage2_start_ns=stage2_start)
        out = run_two_stage(streams, cadence, layout, scale=scale, seed=seed)
        selected += int(out.get("plant_in_top", False))
        survive += int(out.get("gross_pass", False))
        rows.append({"seed": seed, "plant_in_top": out.get("plant_in_top"),
                     "stage2_pass": out.get("gross_pass"), "gross_lcb": out.get("gross_lcb"),
                     "n_legs": out.get("n_legs"), "empty": out.get("empty")})
    survival_rate = survive / max(n, 1)
    select_rate = selected / max(n, 1)
    select_ok = select_rate >= BITE_SELECT_MIN
    survival_ok = survival_rate <= BITE_SURVIVAL_MAX
    return {
        "cadence": cadence.name,
        "n": n,
        "stage2_survival_rate": survival_rate,
        "stage1_select_rate": select_rate,
        "select_ok": bool(select_ok),          # bite has bite (sanity)
        "survival_ok": bool(survival_ok),      # independence holds
        "bite_ok": bool(select_ok and survival_ok),
        "thresholds": {"survival_max": BITE_SURVIVAL_MAX, "select_min": BITE_SELECT_MIN,
                       "planted_edge_bps": BITE_EDGE_BPS},
        "embargo_frac": embargo_frac,
        "stage2_start_ns": int(stage2_start),
        "rows": rows,
    }


# --------------------------------------------------------------------------- #
# No-search coverage on the stage-2 band (forensics baseline)
# --------------------------------------------------------------------------- #
def no_search_coverage(cadence: CadenceSpec, *, scale: ScaleSpec,
                       embargo_frac: float = EMBARGO_FRAC, n_universes: int,
                       subset_size: int = 5, block_legs: int = BLOCK_LEGS,
                       n_boot: int = N_BOOT) -> dict[str, Any]:
    """Frozen-estimator LCB pass rate on a random k=5 subset (no search) on stage-2."""
    config = OracleConfig(charge_costs=False)
    layout = c_layout(cadence.n_bars, cadence.hold_bars, embargo_frac=embargo_frac)
    hits = 0
    rows = []
    for seed, cspec in bank_seeds(cadence, n_universes):
        streams = make_null_universe(seed, cspec, n_candidates=scale.n_cand, edge_bps=0.0)
        rng = np.random.default_rng(seed + 91)
        ids = [s.candidate_id for s in streams]
        k = min(subset_size, len(ids))
        pick = frozenset(str(x) for x in rng.choice(ids, size=k, replace=False))
        lcb = eval_lcb_legs(pick, streams, config, layout.gate, n_boot=n_boot, seed=seed,
                            block_legs=block_legs)
        pos = bool(lcb.get("pass_positive"))
        hits += int(pos)
        rows.append({"seed": seed, "pass": pos, "lcb": lcb.get("lcb"),
                     "n_legs": lcb.get("n_legs")})
    n = len(rows)
    rate = hits / max(n, 1)
    return {"cadence": cadence.name, "n": n, "n_lcb_positive": hits, "rate": rate,
            "coverage_ok": bool(n > 0 and rate <= ALPHA), "rows": rows}


# --------------------------------------------------------------------------- #
# End-to-end α on the null bank (P-C.5 gate quantity)
# --------------------------------------------------------------------------- #
def e2e_alpha(cadence: CadenceSpec, *, scale: ScaleSpec,
              embargo_frac: float = EMBARGO_FRAC, n_boot: int = N_BOOT,
              block_legs: int = BLOCK_LEGS) -> dict[str, Any]:
    """Full two-stage pipeline over the null bank; point α̂ = frac stage-2 LCB(g_gross)>0."""
    layout_by = {}
    rows = []
    for seed, cspec in bank_seeds(cadence, scale.n_null):
        key = (cspec.n_bars, cspec.hold_bars)
        layout = layout_by.get(key) or c_layout(cspec.n_bars, cspec.hold_bars,
                                                embargo_frac=embargo_frac)
        layout_by[key] = layout
        streams = make_null_universe(seed, cspec, n_candidates=scale.n_cand, edge_bps=0.0)
        out = run_two_stage(streams, cspec, layout, scale=scale, seed=seed,
                            n_boot=n_boot, block_legs=block_legs)
        rows.append({"seed": seed, "symbol": cspec.symbol,
                     "gross_pass": bool(out.get("gross_pass")),
                     "gross_lcb": out.get("gross_lcb"), "gross_point": out.get("gross_point"),
                     "g_search_hat": out.get("g_search_hat"), "n_legs": out.get("n_legs"),
                     "empty": out.get("empty", False)})
    n = len(rows)
    k = sum(1 for r in rows if r["gross_pass"])
    ph = k / max(n, 1)
    lo, hi = wilson(k, n)
    return {"cadence": cadence.name, "n": n, "n_gross_lcb_positive": k, "alpha_hat": ph,
            "alpha_se": binomial_se(ph, n), "alpha_wilson_95": {"low": lo, "high": hi},
            "pass_stop": bool(ph <= ALPHA), "rows": rows}


# --------------------------------------------------------------------------- #
# Forensics label (P-C.6) + per-cadence outcome (P-C.5)
# --------------------------------------------------------------------------- #
def _failure_label(no_search_cov: float, e2e: float) -> str:
    inflation = e2e - no_search_cov
    if inflation <= _SELECTION_INFLATION_MAX:
        return "coverage_limited"      # data-density, not selection-unsafe
    return "selection_unsafe"


def _outcome(low_cert: bool, high_cert: bool) -> dict[str, Any]:
    if low_cert and high_cert:
        return {"verdict": "DUAL_CERTIFY", "certified_cadences": ["low", "high"],
                "recommend": "P4_both", "terminal": False}
    if high_cert:
        return {"verdict": "HIGH_ONLY_CERTIFY", "certified_cadences": ["high"],
                "recommend": "P4_high_only", "terminal": False,
                "note": "high-cadence binder certified only; low terminal for this binder"}
    if low_cert:
        return {"verdict": "LOW_ONLY_CERTIFY", "certified_cadences": ["low"],
                "recommend": "P4_low_only", "terminal": False,
                "note": "low-cadence binder certified only; high terminal for this binder"}
    return {"verdict": "TERMINAL", "certified_cadences": [], "terminal": True,
            "recommend": "TERMINAL_cannot_certify",
            "note": "neither cadence certified under selection-aware two-stage design"}


# --------------------------------------------------------------------------- #
# DESIGN bank (validation-only: bite + coverage; nothing fit here)
# --------------------------------------------------------------------------- #
def run_design(*, scale: ScaleSpec = DESIGN_SCALE) -> dict[str, Any]:
    """Validate the predeclared embargo (bite) + disclose no-search coverage; freeze procedure.

    No knob is fit on the design bank: embargo is predeclared (P-C.2), the estimator is the
    P3d frozen leg-studentized LCB. Design is pure validation → no design→confirm leakage.
    """
    _set_seeds(*DESIGN_SEEDS)
    print("[P-C] DESIGN: bite-check (stage-1-localized plant → stage-2 survival)...", flush=True)
    bite = {}
    for c in (LOW, HIGH):
        b = bite_check(c, scale=scale, embargo_frac=EMBARGO_FRAC)
        bite[c.name] = b
        print(f"  bite {c.name}: survival={b['stage2_survival_rate']:.3f} "
              f"(≤{BITE_SURVIVAL_MAX}) select={b['stage1_select_rate']:.3f} "
              f"ok={b['bite_ok']}", flush=True)
    bite_ok = all(bite[c]["bite_ok"] for c in ("low", "high"))
    if not bite_ok:
        return {
            "bank": "design", "seeds": {"low": DESIGN_SEEDS[0], "high": DESIGN_SEEDS[1]},
            "bite": {k: {kk: vv for kk, vv in v.items() if kk != "rows"}
                     for k, v in bite.items()},
            "frozen_procedure": None, "design_ok": False,
            "stop_reason": "bite_failed",
            "terminal": True,
            "recommend": "TERMINAL_temporal_independence_failed",
            "note": ("stage-2 temporal independence failed bite; cannot run a selection-safe "
                     "two-stage binder on this stream at α=5%. No held-out escalation (Fork B)."),
        }

    print("[P-C] DESIGN: no-search coverage on stage-2 band (disclosure)...", flush=True)
    cov = {}
    for c in (LOW, HIGH):
        cv = no_search_coverage(c, scale=scale, embargo_frac=EMBARGO_FRAC,
                                n_universes=scale.n_coverage)
        cov[c.name] = cv
        print(f"  cov {c.name}: rate={cv['rate']:.4f} ok={cv['coverage_ok']} (n={cv['n']})",
              flush=True)

    frozen = {
        "binder": "two_stage_sample_split",
        "stage1": "search+certify top-1 on stage-1 bands",
        "stage2": "lcb_g_leg_studentized(g_gross) > 0 on distant embargoed band",
        "functional": "g_gross_ratio",          # design §3 binding estimand (not mean_per_leg)
        "estimator": "leg_studentized_bootstrap_t",  # P3d frozen
        "embargo_frac": EMBARGO_FRAC,
        "search_frac": STAGE_SEARCH_FRAC, "ranking_frac": STAGE_RANKING_FRAC,
        "n_boot": N_BOOT, "block_legs": BLOCK_LEGS, "confidence": 0.95,
        "alpha": ALPHA, "one_subset": True, "shortlist": False,
        "design_seeds": {"low": DESIGN_SEEDS[0], "high": DESIGN_SEEDS[1]},
        "confirm_seeds": {"low": CONFIRM_SEEDS[0], "high": CONFIRM_SEEDS[1]},
        "design_bite_ok": True,
        "design_cov_low": cov["low"]["rate"], "design_cov_high": cov["high"]["rate"],
        "held_out_escalation": False,           # Fork B
        "gate_rule": "per_cadence point α̂≤5% AND no-search cov≤5% (Fork A)",
    }
    return {
        "bank": "design", "seeds": {"low": DESIGN_SEEDS[0], "high": DESIGN_SEEDS[1]},
        "bite": {k: {kk: vv for kk, vv in v.items() if kk != "rows"} for k, v in bite.items()},
        "bite_rows": {k: v["rows"] for k, v in bite.items()},
        "coverage": {k: {kk: vv for kk, vv in v.items() if kk != "rows"} for k, v in cov.items()},
        "frozen_procedure": frozen, "design_ok": True, "stop_reason": None,
    }


# --------------------------------------------------------------------------- #
# CONFIRM gate (frozen procedure only; per-cadence certification)
# --------------------------------------------------------------------------- #
def confirm_gate(procedure: dict, *, scale: ScaleSpec = CONFIRM_SCALE) -> dict[str, Any]:
    _set_seeds(*CONFIRM_SEEDS)
    embargo_frac = float(procedure["embargo_frac"])
    n_boot = int(procedure["n_boot"])
    block_legs = int(procedure["block_legs"])
    per: dict[str, Any] = {}
    for c in (LOW, HIGH):
        print(f"[P-C] CONFIRM {c.name}: no-search coverage...", flush=True)
        cov = no_search_coverage(c, scale=scale, embargo_frac=embargo_frac,
                                 n_universes=scale.n_coverage, block_legs=block_legs,
                                 n_boot=n_boot)
        print(f"  cov {c.name}: {cov['rate']:.4f} ok={cov['coverage_ok']}", flush=True)
        print(f"[P-C] CONFIRM {c.name}: e2e α...", flush=True)
        a = e2e_alpha(c, scale=scale, embargo_frac=embargo_frac, n_boot=n_boot,
                      block_legs=block_legs)
        print(f"  α̂ {c.name}: {a['alpha_hat']:.4f} ok={a['pass_stop']}", flush=True)
        certified = bool(cov["coverage_ok"] and a["pass_stop"])
        per[c.name] = {
            "cadence": c.name,
            "no_search_cov": cov["rate"],
            "e2e_alpha": a["alpha_hat"],
            "selection_inflation": a["alpha_hat"] - cov["rate"],
            "coverage_ok": cov["coverage_ok"],
            "alpha_ok": a["pass_stop"],
            "certified": certified,
            "alpha_se": a["alpha_se"], "alpha_wilson_95": a["alpha_wilson_95"],
            "n": a["n"], "n_gross_lcb_positive": a["n_gross_lcb_positive"],
            "failure_label": None if certified else _failure_label(cov["rate"], a["alpha_hat"]),
            "coverage_rows": cov["rows"],
            "alpha_rows": a["rows"],
        }
    outcome = _outcome(per["low"]["certified"], per["high"]["certified"])
    return {
        "bank": "confirm", "seeds": {"low": CONFIRM_SEEDS[0], "high": CONFIRM_SEEDS[1]},
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
            "alpha_target": ALPHA,
            "gate_rule": "per-cadence point α̂≤5% AND no-search cov≤5% (Fork A per-cadence)",
            "low_certified": per["low"]["certified"],
            "high_certified": per["high"]["certified"],
            "verdict": outcome["verdict"],
            "recommend": outcome["recommend"],
            "terminal": outcome["terminal"],
            "forbidden": ["no P3e", "no α soften", "no LCB-confidence drop",
                          "no held-out escalation in this experiment",
                          "single-cadence pass ≠ full route-restore (per-cadence P4)"],
            "note": (
                "Per-cadence certification (Fork A). A single-cadence pass certifies only that "
                "cadence's binder, not a full XENA route-restore. Failure with "
                "selection_inflation≈0 is coverage-limited, not selection-unsafe (see failure_label)."
            ),
        },
    }


def run_pc(*, scale_design: ScaleSpec = DESIGN_SCALE,
           scale_confirm: ScaleSpec = CONFIRM_SCALE) -> tuple[dict, dict | None]:
    design = run_design(scale=scale_design)
    if not design.get("design_ok"):
        return design, None
    confirm = confirm_gate(design["frozen_procedure"], scale=scale_confirm)
    return design, confirm
