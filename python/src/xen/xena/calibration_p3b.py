"""INFR-009 P3b re-calibration — studentized LCB + purged rank→TEST seam.

> **LEGACY CAL APPARATUS (INFR-022).** Not bindable on the live research path without a
> post-INFR-022 CAL redesign. Retired names used here for historical replay only: the
> ``n_legs_floor`` / ``n_blocks_floor`` domain guards (AMENDMENT-7 / L-56 detection floors)
> and the NET LCB path (zero-cost model). INFR-022: gross-only, sample-size as context.

Disjoint bank seeds from P3. Does not call run_final_gate. No fixture contact.
Predeclaration: design.md §P3b.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from xen.xena.calibration import SegmentLayout, path_universe
from xen.xena.certify import certify_and_rank, contiguous_purged_folds
from xen.xena.high_cadence_null import HighCadenceNullSpec, build_high_cadence_null
from xen.xena.oracle import CandidateStream, OracleConfig, evaluate
from xen.xena.score import lcb_g_studentized
from xen.xena.search import (SearchParams, bootstrap_block_starts, clip_grid_covering,
                             run_restart, universe_grid)

NS = 1_000_000_000
ALPHA = 0.05
LCB_CONFIDENCE = 0.95
RT_COST_BPS = 2.0

# Disjoint from P3 (bases 1000/2000)
SEED_BASE_LOW = 11_000
SEED_BASE_HIGH = 12_000


@dataclass(frozen=True)
class CadenceSpec:
    name: str
    hold_bars: int
    n_bars: int
    n_trades: int
    kind: str
    symbol: str = "SYNTH"


LOW = CadenceSpec("low", hold_bars=20, n_bars=6000, n_trades=80, kind="path")
HIGH = CadenceSpec("high", hold_bars=12, n_bars=12_000, n_trades=1000, kind="high")


@dataclass(frozen=True)
class ScaleSpec:
    name: str
    n_null: int
    n_cand: int
    budget: int
    n_restarts: int
    n_power: int
    n_coverage: int


TOY = ScaleSpec("toy", n_null=40, n_cand=16, budget=80, n_restarts=3,
                n_power=8, n_coverage=40)
PRODUCTION = ScaleSpec("production", n_null=40, n_cand=64, budget=200, n_restarts=5,
                       n_power=8, n_coverage=40)


def _layout(n_bars: int, hold_bars: int, *, purge_mult: int = 1,
            bar_seconds: int = 60) -> SegmentLayout:
    """50/30/20 with purge ≥ H bars between ranking and gate (B1)."""
    end = n_bars * bar_seconds * NS
    purge_ns = max(hold_bars, 1) * purge_mult * bar_seconds * NS
    return SegmentLayout.from_span(0, end, purge_ns=purge_ns)


def make_null_universe(seed: int, cadence: CadenceSpec, *,
                       n_candidates: int,
                       cost_bps: float = RT_COST_BPS,
                       edge_bps: float = 0.0) -> list[CandidateStream]:
    if cadence.kind == "high":
        # High-cadence path (shared marks); edge_bps>0 plants favourable exit shift (P-BF bite).
        spec = HighCadenceNullSpec(
            n_candidates=n_candidates, n_bars=cadence.n_bars,
            target_legs_per_candidate=min(cadence.n_trades, cadence.n_bars // 8),
            hold_bars=cadence.hold_bars, cost_bps=cost_bps, edge_bps=float(edge_bps),
            seed=seed, noise_bps=8.0)
        streams = build_high_cadence_null(spec)
    else:
        n_planted = 0 if edge_bps == 0.0 else max(1, n_candidates // 4)
        streams = path_universe(
            n_planted=n_planted, n_null=n_candidates - n_planted,
            edge_bps=edge_bps, seed=seed,
            n_trades=cadence.n_trades,
            n_bars=cadence.n_bars, cost_bps=cost_bps)
    if cadence.symbol != "SYNTH":
        streams = [CandidateStream(s.candidate_id, cadence.symbol, s.trades, s.marks,
                                   s.cost_bps, s.money_per_unit) for s in streams]
    return streams


def bank_seeds(cadence: CadenceSpec, n_null: int) -> list[tuple[int, CadenceSpec]]:
    base = SEED_BASE_LOW if cadence.name == "low" else SEED_BASE_HIGH
    out: list[tuple[int, CadenceSpec]] = []
    n_main = max(n_null - 12, 1)
    n_eur = min(6, max(0, n_null - n_main))
    n_xau = n_null - n_main - n_eur
    for i in range(n_main):
        out.append((base + i, cadence))
    for i in range(n_eur):
        c = CadenceSpec(cadence.name, cadence.hold_bars, cadence.n_bars,
                        cadence.n_trades, cadence.kind, symbol="EURUSD")
        out.append((base + 500 + i, c))
    for i in range(n_xau):
        c = CadenceSpec(cadence.name, cadence.hold_bars, cadence.n_bars,
                        cadence.n_trades, cadence.kind, symbol="XAUUSD")
        out.append((base + 600 + i, c))
    return out[:n_null]


def block_candidates(H: int) -> list[int]:
    return sorted({max(H, int(x)) for x in
                   (H, 2 * H, 4 * H, max(H, 32), max(H, 64), max(H, 128))})


def evaluate_lcb_st(subset: frozenset[str] | set[str], streams: list[CandidateStream],
                    config: OracleConfig, segment: tuple[int, int], *,
                    block: int, n_boot: int = 200, seed: int = 0) -> dict:
    """Studentized LCB on g_gross (gross-only, INFR-022). Sample size reported as context."""
    res = evaluate(subset, streams, config, segment=segment, seed=seed)
    grid = universe_grid(streams)
    grid = clip_grid_covering(grid, segment, streams)
    if len(grid) < 2:
        return {"lcb": float("-inf"), "pass_positive": False, "point": float("nan"),
                "empty_grid": True, "method": "studentized_bootstrap_t"}
    starts = bootstrap_block_starts(len(grid), block=block, n_boot=n_boot,
                                    seed=17_001 + seed)
    out = lcb_g_studentized(
        res, streams, grid, starts, block=block, confidence=LCB_CONFIDENCE)
    out["n_admitted"] = res.n_admitted
    out["empty_grid"] = False
    return out


def coverage_no_search(cadence: CadenceSpec, *, block: int, n_universes: int,
                       n_cand: int, subset_size: int = 5,
                       purge_mult: int = 1) -> dict[str, Any]:
    config = OracleConfig(charge_costs=False)
    layout = _layout(cadence.n_bars, cadence.hold_bars, purge_mult=purge_mult)
    H = cadence.hold_bars
    block = max(block, H)
    hits = 0
    rows = []
    seeds = bank_seeds(cadence, n_universes)
    for seed, cspec in seeds:
        streams = make_null_universe(seed, cspec, n_candidates=n_cand, edge_bps=0.0)
        rng = np.random.default_rng(seed + 91)
        ids = [s.candidate_id for s in streams]
        k = min(subset_size, len(ids))
        pick = frozenset(str(x) for x in rng.choice(ids, size=k, replace=False))
        lcb = evaluate_lcb_st(pick, streams, config, layout.gate, block=block, seed=seed)
        pos = bool(lcb.get("pass_positive"))
        hits += int(pos)
        rows.append({"seed": seed, "pass": pos,
                     "lcb": lcb.get("lcb"), "n_legs": lcb.get("n_legs"),
                     "n_nonempty_blocks": lcb.get("n_nonempty_blocks"),
                     "empty_bar_fraction": lcb.get("empty_bar_fraction")})
    n = len(seeds)
    rate = hits / max(n, 1)
    return {
        "cadence": cadence.name, "block": block, "H": H,
        "n": n, "n_lcb_positive": hits, "rate_lcb_positive": rate,
        "coverage_ok": (n > 0 and rate <= ALPHA),
        "alpha": ALPHA, "method": "studentized_bootstrap_t",
        "rows": rows,
    }


def select_block_and_floors(scale: ScaleSpec, *, purge_mult: int = 1) -> dict[str, Any]:
    """A1 block sweep on no-search coverage (the A3 n_legs_floor selection is RETIRED,
    INFR-022 L-63 — sample-size is context, never a gate).

    Shared L grid: union of per-cadence candidates with L ≥ max(H_low, H_high) so both
    cadences are evaluated at the same L (P3b joint rule).
    """
    H_joint = max(LOW.hold_bars, HIGH.hold_bars)
    shared_L = sorted({L for H in (LOW.hold_bars, HIGH.hold_bars)
                       for L in block_candidates(H) if L >= H_joint})
    if not shared_L:
        shared_L = block_candidates(H_joint)
    sweeps: dict[str, list] = {}
    for c in (LOW, HIGH):
        sweeps[c.name] = []
        for L in shared_L:
            sweeps[c.name].append(
                coverage_no_search(c, block=L, n_universes=scale.n_coverage,
                                   n_cand=scale.n_cand, purge_mult=purge_mult))
    by_L: dict[int, dict[str, bool]] = {}
    for cname, rows in sweeps.items():
        for r in rows:
            by_L.setdefault(r["block"], {})[cname] = r["coverage_ok"]
    ok_Ls = sorted(L for L, m in by_L.items()
                   if m.get("low") and m.get("high"))
    selected_block = ok_Ls[0] if ok_Ls else None
    block_use = selected_block if selected_block is not None else max(64, H_joint)

    return {
        "rule_block": "smallest L≥H with studentized no-search P(LCB>0)≤α both cadences",
        "selected_block": selected_block,
        "block_fallback": block_use if selected_block is None else None,
        "ok_blocks": ok_Ls,
        "coverage_stop_fail": selected_block is None,
        "sweeps": {k: [{kk: vv for kk, vv in r.items() if kk != "rows"} for r in v]
                   for k, v in sweeps.items()},
        "rule_A3": "RETIRED (INFR-022 L-63): n_legs_floor vetoes removed — sample-size is "
                   "context, never a gate",
        "selected_n_legs_floor": None,
        "A3_curve": [],
        "A3_fail": False,
        "method": "studentized_bootstrap_t",
        "purge_mult": purge_mult,
    }


def run_e2e_one(seed: int, cadence: CadenceSpec, *, block_lcb: int,
                scale: ScaleSpec, edge_bps: float = 0.0,
                purge_mult: int = 1) -> dict[str, Any]:
    """One e2e row (gross-only, INFR-022)."""
    config = OracleConfig(charge_costs=False)
    params = SearchParams(L=40, n_boot=80, block_bars=max(64, cadence.hold_bars),
                          init_size=4)
    streams = make_null_universe(seed, cadence, n_candidates=scale.n_cand,
                                 edge_bps=edge_bps)
    layout = _layout(cadence.n_bars, cadence.hold_bars, purge_mult=purge_mult)
    H = cadence.hold_bars
    block_lcb = max(block_lcb, H)

    finalists = [
        run_restart(streams, config, budget=scale.budget, restart_id=r + 1,
                    params=params, segment=layout.search,
                    skip_economics_precondition=True)
        for r in range(scale.n_restarts)
    ]
    folds = contiguous_purged_folds(
        layout.ranking[0], layout.ranking[1], n_folds=3,
        purge_ns=max(H, 1) * 60 * NS)
    pkg = certify_and_rank(
        finalists, streams, config, folds=folds, params=params,
        search_segment=layout.search, include_random_ref=False, include_fill_basis=False)
    if not pkg["ranked"]:
        return {"seed": seed, "cadence": cadence.name, "empty_shortlist": True,
                "gross_pass": False}
    top = pkg["ranked"][0].subset
    gross = evaluate_lcb_st(top, streams, config, layout.gate, block=block_lcb,
                            seed=seed)
    return {
        "seed": seed, "cadence": cadence.name, "symbol": cadence.symbol,
        "empty_shortlist": False, "subset_size": len(top),
        "g_search_hat": pkg["ranked"][0].search_F_hat,
        "gross_lcb": gross.get("lcb"), "gross_point": gross.get("point"),
        "gross_pass": bool(gross.get("pass_positive")),
        "n_legs": gross.get("n_legs"),
        "n_nonempty_blocks": gross.get("n_nonempty_blocks"),
        "empty_bar_fraction": gross.get("empty_bar_fraction"),
        "n_admitted_test": gross.get("n_admitted"),
        "block_lcb": block_lcb, "purge_ns": layout.purge_ns,
        "method": "studentized_bootstrap_t",
        "evaluation_count": pkg["evaluation_count"],
        "edge_bps": edge_bps,
        "gate_kind": "LCB_G_GROSS_95_STUDENTIZED",
    }


def end_to_end_alpha(cadence: CadenceSpec, *, block_lcb: int, scale: ScaleSpec,
                     purge_mult: int = 1) -> dict[str, Any]:
    seeds = bank_seeds(cadence, scale.n_null)
    rows = [run_e2e_one(seed, cspec, block_lcb=block_lcb, scale=scale,
                        purge_mult=purge_mult)
            for seed, cspec in seeds]
    in_dom = [r for r in rows if not r.get("empty_shortlist")]
    n_pass = sum(1 for r in in_dom if r.get("gross_pass"))
    n_in = len(in_dom)
    rate = n_pass / max(n_in, 1)
    return {
        "cadence": cadence.name, "n": len(rows), "n_in_domain": n_in,
        "n_gross_lcb_positive": n_pass, "alpha_hat": rate,
        "alpha_target": ALPHA, "pass_stop": n_in > 0 and rate <= ALPHA,
        "method": "studentized_bootstrap_t",
        "block_lcb": block_lcb, "purge_mult": purge_mult,
        "rows": rows,
    }


def power_curve(cadence: CadenceSpec, *, block_lcb: int, scale: ScaleSpec,
                edges: tuple[float, ...] = (5.0, 10.0, 20.0, 30.0, 40.0),
                purge_mult: int = 1) -> dict[str, Any]:
    """Power curve (gross-only; the NET power read is retired, INFR-022)."""
    base = 15_000 if cadence.name == "low" else 16_000
    curve = []
    for e in edges:
        hits_g = 0
        for i in range(scale.n_power):
            r = run_e2e_one(base + int(e * 10) + i, cadence, block_lcb=block_lcb,
                            scale=scale, edge_bps=e, purge_mult=purge_mult)
            hits_g += int(r.get("gross_pass", False))
        curve.append({"edge_bps": e, "n": scale.n_power,
                      "gross_lcb_power": hits_g / scale.n_power,
                      "cadence": cadence.name})
    return {"cadence": cadence.name, "curve": curve, "binding": False,
            "method": "studentized_bootstrap_t"}


def select_k(*, block_lcb: int, scale: ScaleSpec, purge_mult: int = 1) -> dict[str, Any]:
    """Policy cushion (gross-only; the NET power read is retired, INFR-022)."""
    ks = (1.0, 1.25, 1.5, 2.0)
    curve = []
    selected = None
    for k in ks:
        edge = max(k * RT_COST_BPS, 10.0)
        hits = 0
        for i in range(scale.n_power):
            r = run_e2e_one(17_000 + int(k * 100) + i, LOW, block_lcb=block_lcb,
                            scale=scale, edge_bps=edge, purge_mult=purge_mult)
            hits += int(r.get("gross_pass", False))
        rate = hits / scale.n_power
        curve.append({"k": k, "edge_bps": edge, "gross_lcb_power": rate,
                      "meets": rate >= 0.5})
        if selected is None and rate >= 0.5:
            selected = k
    return {"rule": "smallest k with gross-LCB power≥0.5 at edge=max(k·RT,10)",
            "selected_k": selected, "curve": curve,
            "k_rule_fail": selected is None}


def run_scale(scale: ScaleSpec, *, purge_mult: int = 1) -> dict[str, Any]:
    """One scale loop: block → e2e α both cadences → power/k (gross-only, INFR-022)."""
    print(f"  [{scale.name}] block sweep...", flush=True)
    sel = select_block_and_floors(scale, purge_mult=purge_mult)
    block = sel["selected_block"] or sel.get("block_fallback") or 64

    print(f"  [{scale.name}] e2e α low (block={block})...",
          flush=True)
    a_low = end_to_end_alpha(LOW, block_lcb=block, scale=scale,
                             purge_mult=purge_mult)
    print(f"  [{scale.name}] e2e α high...", flush=True)
    a_high = end_to_end_alpha(HIGH, block_lcb=block, scale=scale,
                              purge_mult=purge_mult)

    print(f"  [{scale.name}] power curves...", flush=True)
    pow_low = power_curve(LOW, block_lcb=block, scale=scale, purge_mult=purge_mult)
    pow_high = power_curve(HIGH, block_lcb=block, scale=scale, purge_mult=purge_mult)
    print(f"  [{scale.name}] k selection...", flush=True)
    k_sel = select_k(block_lcb=block, scale=scale, purge_mult=purge_mult)

    cov_fail = bool(sel.get("coverage_stop_fail"))
    alpha_fail = (not a_low["pass_stop"]) or (not a_high["pass_stop"])
    stop = cov_fail or alpha_fail

    return {
        "scale": scale.name,
        "scale_params": {
            "n_null": scale.n_null, "n_cand": scale.n_cand,
            "budget": scale.budget, "n_restarts": scale.n_restarts,
        },
        "block_A3_selection": sel,
        "selected_block": sel.get("selected_block"),
        "purge_mult": purge_mult,
        "alpha_low": {k: v for k, v in a_low.items() if k != "rows"},
        "alpha_high": {k: v for k, v in a_high.items() if k != "rows"},
        "alpha_low_rows": a_low["rows"],
        "alpha_high_rows": a_high["rows"],
        "power_low": pow_low,
        "power_high": pow_high,
        "k_selection": k_sel,
        "stop_condition": {
            "alpha_target": ALPHA,
            "coverage_fail": cov_fail,
            "alpha_low_fail": not a_low["pass_stop"],
            "alpha_high_fail": not a_high["pass_stop"],
            "STOP": stop,
            "verdict": "STOP" if stop else "PASS",
            "selected_block": sel.get("selected_block"),
            "selected_k": k_sel.get("selected_k"),
            "method": "studentized_bootstrap_t",
            "purge_mult": purge_mult,
        },
    }


def run_p3b_calibration(*, purge_mult: int = 1,
                        run_production: bool = True) -> dict[str, Any]:
    """C2: toy loop then mandatory production confirm."""
    report: dict[str, Any] = {
        "schema": "xena.infr009.p3b_cal.v1",
        "predeclared": {
            "alpha": ALPHA,
            "lcb_confidence": LCB_CONFIDENCE,
            "method": "studentized_bootstrap_t",
            "purge_mult_H": purge_mult,
            "seed_bases": {"low": SEED_BASE_LOW, "high": SEED_BASE_HIGH},
            "disjoint_from_p3": True,
            "fixtures_forbidden": ["XENA-001", "XENA-002", "XENA-003"],
            "A1": "bootstrap-t LCB",
            "A3": "RETIRED (INFR-022 L-63): n_legs_floor vetoes removed — sample-size is "
                 "context, never a gate",
            "B1": "purge ≥ H between ranking and gate",
        },
    }
    print("[P3b] TOY/MEDIUM scale...", flush=True)
    toy = run_scale(TOY, purge_mult=purge_mult)
    report["toy"] = toy

    prod = None
    if run_production:
        print("[P3b] PRODUCTION scale confirm...", flush=True)
        prod = run_scale(PRODUCTION, purge_mult=purge_mult)
        report["production"] = prod

    # Final verdict = production if run, else toy
    final = prod if prod is not None else toy
    report["stop_condition"] = dict(final["stop_condition"])
    report["stop_condition"]["toy_verdict"] = toy["stop_condition"]["verdict"]
    if prod is not None:
        report["stop_condition"]["production_verdict"] = prod["stop_condition"]["verdict"]
        report["stop_condition"]["STOP"] = prod["stop_condition"]["STOP"]
        report["stop_condition"]["verdict"] = (
            "STOP" if prod["stop_condition"]["STOP"] else "PROCEED_TO_P4_ELIGIBLE"
        )
    else:
        report["stop_condition"]["verdict"] = (
            "STOP" if toy["stop_condition"]["STOP"] else "TOY_PASS_NEED_PRODUCTION"
        )
    report["stop_condition"]["note"] = (
        "If STOP: no freeze, no α/confidence soften, no extensive-F. "
        "Escalation: B2 distant TEST; then B3 only after A1+B1+scale exhausted."
    )
    return report
