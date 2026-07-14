"""INFR-009 P3 calibration harness — LCB(g_gross) coverage + end-to-end α.

Uses the intensive score path only. Does **not** call ``run_final_gate`` (retired
extensive-F binder). Synthetic TEST bands only — never XENA-001/002/003 or holdout.

Predeclaration: ``python/experiments/INFR-009/design.md`` §P3.
Stop-condition: end-to-end α ≤ 5% at **both** cadences AND LCB coverage ≤ 5% at both.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any, Callable

import numpy as np

from xen.xena.calibration import SegmentLayout, path_universe
from xen.xena.certify import certify_and_rank, contiguous_purged_folds
from xen.xena.high_cadence_null import HighCadenceNullSpec, build_high_cadence_null
from xen.xena.oracle import CandidateStream, OracleConfig, evaluate
from xen.xena.score import g_gross_point, lcb_g
from xen.xena.search import (SearchParams, bootstrap_block_starts, clip_grid_covering,
                             run_restart, universe_grid)

NS = 1_000_000_000
DEFAULT_COST_BPS = 2.0
ALPHA = 0.05
LCB_CONFIDENCE = 0.95

# --- Predeclared counts (design.md §P3.2 / §P3.3) — committed before results ---
N_NULL_PER_CADENCE = 40
N_RESTARTS = 3
SEARCH_BUDGET = 50
N_CAND = 16
RT_COST_BPS = DEFAULT_COST_BPS
K_CANDIDATES = (1.0, 1.25, 1.5, 2.0)
K_POWER_FLOOR = 0.50
K_START = 32
K_CAP = 256


@dataclass(frozen=True)
class CadenceSpec:
    name: str
    hold_bars: int
    n_bars: int
    n_trades: int
    kind: str  # "path" | "high" | "heldout_path"
    symbol: str = "SYNTH"


LOW = CadenceSpec("low", hold_bars=20, n_bars=6000, n_trades=80, kind="path")
HIGH = CadenceSpec("high", hold_bars=12, n_bars=12_000, n_trades=1000, kind="high")


def _layout(n_bars: int, bar_seconds: int = 60) -> SegmentLayout:
    end = n_bars * bar_seconds * NS
    return SegmentLayout.from_span(0, end)


def make_null_universe(seed: int, cadence: CadenceSpec, *,
                       n_candidates: int = N_CAND,
                       cost_bps: float = RT_COST_BPS,
                       edge_bps: float = 0.0) -> list[CandidateStream]:
    """Fresh zero-edge (or planted) universe for one seed × cadence."""
    if cadence.kind == "high":
        spec = HighCadenceNullSpec(
            n_candidates=n_candidates,
            n_bars=cadence.n_bars,
            target_legs_per_candidate=min(cadence.n_trades, cadence.n_bars // 8),
            hold_bars=cadence.hold_bars,
            cost_bps=cost_bps,
            edge_bps=edge_bps,
            seed=seed,
            noise_bps=8.0,
        )
        streams = build_high_cadence_null(spec)
        if edge_bps != 0.0:
            # high-cadence builder ignores edge; plant via path_universe instead
            return path_universe(
                n_planted=max(1, n_candidates // 4), n_null=n_candidates - max(1, n_candidates // 4),
                edge_bps=edge_bps, seed=seed, n_trades=min(200, cadence.n_trades),
                n_bars=cadence.n_bars, cost_bps=cost_bps)
        # retag symbol if held-out style
        if cadence.symbol != "SYNTH":
            return [CandidateStream(s.candidate_id, cadence.symbol, s.trades, s.marks,
                                    s.cost_bps, s.money_per_unit) for s in streams]
        return streams
    # path null / planted
    n_planted = 0 if edge_bps == 0.0 else max(1, n_candidates // 4)
    n_null = n_candidates - n_planted
    streams = path_universe(
        n_planted=n_planted, n_null=n_null, edge_bps=edge_bps, seed=seed,
        n_trades=cadence.n_trades, n_bars=cadence.n_bars, cost_bps=cost_bps)
    if cadence.symbol != "SYNTH":
        streams = [CandidateStream(s.candidate_id, cadence.symbol, s.trades, s.marks,
                                   s.cost_bps, s.money_per_unit) for s in streams]
    return streams


def bank_seeds(cadence: CadenceSpec) -> list[tuple[int, CadenceSpec]]:
    """Predeclared mix: 28 path/high + 6 EURUSD + 6 XAUUSD (design §P3.3)."""
    base = 1000 if cadence.name == "low" else 2000
    out: list[tuple[int, CadenceSpec]] = []
    for i in range(28):
        out.append((base + i, cadence))
    for i in range(6):
        c = CadenceSpec(cadence.name, cadence.hold_bars, cadence.n_bars,
                        cadence.n_trades, "path" if cadence.kind != "high" else "high",
                        symbol="EURUSD")
        out.append((base + 100 + i, c))
    for i in range(6):
        c = CadenceSpec(cadence.name, cadence.hold_bars, cadence.n_bars,
                        cadence.n_trades, "path" if cadence.kind != "high" else "high",
                        symbol="XAUUSD")
        out.append((base + 200 + i, c))
    assert len(out) == N_NULL_PER_CADENCE
    return out


def block_candidates(H: int) -> list[int]:
    raw = [H, 2 * H, 4 * H, max(H, 32), max(H, 64), max(H, 128)]
    return sorted({max(H, int(x)) for x in raw})


def evaluate_lcb(subset: frozenset[str] | set[str], streams: list[CandidateStream],
                 config: OracleConfig, segment: tuple[int, int], *,
                 block: int, n_boot: int = 200, seed: int = 0,
                 net: bool = False, confidence: float = LCB_CONFIDENCE) -> dict:
    """LCB on a fixed subset over ``segment`` (synthetic gate band)."""
    cfg = replace(config, charge_costs=bool(net))
    res = evaluate(subset, streams, cfg, segment=segment, seed=seed)
    grid = universe_grid(streams)
    grid = clip_grid_covering(grid, segment, streams)
    if len(grid) < 2:
        return {"lcb": float("-inf"), "pass_positive": False, "point": float("nan"),
                "empty_grid": True}
    starts = bootstrap_block_starts(len(grid), block=block, n_boot=n_boot,
                                    seed=9_001 + seed)
    out = lcb_g(res, streams, grid, starts, block=block, confidence=confidence, net=net)
    out["n_admitted"] = res.n_admitted
    out["empty_grid"] = False
    return out


def coverage_no_search(cadence: CadenceSpec, *, block: int, n_universes: int = 40,
                       config: OracleConfig | None = None,
                       subset_size: int = 5) -> dict[str, Any]:
    """LCB coverage on fixed random subsets (no search) — block-length sweep input."""
    config = config or OracleConfig(charge_costs=False)
    layout = _layout(cadence.n_bars)
    H = cadence.hold_bars
    block = max(block, H)
    hits = 0
    rows = []
    seeds = bank_seeds(cadence)[:n_universes]
    for seed, cspec in seeds:
        streams = make_null_universe(seed, cspec, edge_bps=0.0)
        rng = np.random.default_rng(seed + 17)
        ids = [s.candidate_id for s in streams]
        k = min(subset_size, len(ids))
        pick = frozenset(str(x) for x in rng.choice(ids, size=k, replace=False))
        lcb = evaluate_lcb(pick, streams, config, layout.gate, block=block, seed=seed)
        pos = bool(lcb.get("pass_positive"))
        hits += int(pos)
        rows.append({"seed": seed, "lcb": lcb.get("lcb"), "pass": pos,
                     "symbol": cspec.symbol})
    rate = hits / max(len(seeds), 1)
    return {
        "cadence": cadence.name, "block": block, "H": H,
        "n": len(seeds), "n_lcb_positive": hits,
        "rate_lcb_positive": rate,
        "coverage_ok": rate <= ALPHA,  # P(LCB>0) ≤ α under true null
        "alpha": ALPHA,
        "rows": rows,
    }


def select_block_length(cadences: list[CadenceSpec] = (LOW, HIGH),
                        n_universes: int = 40) -> dict[str, Any]:
    """Rule P3.2: smallest L ≥ H with coverage_ok at BOTH cadences."""
    sweeps = {}
    for c in cadences:
        sweeps[c.name] = []
        for L in block_candidates(c.hold_bars):
            sweeps[c.name].append(coverage_no_search(c, block=L, n_universes=n_universes))
    # candidates that work for ALL cadences
    by_L: dict[int, dict[str, bool]] = {}
    for cname, rows in sweeps.items():
        for r in rows:
            by_L.setdefault(r["block"], {})[cname] = r["coverage_ok"]
    ok_Ls = sorted(L for L, m in by_L.items()
                   if all(m.get(c.name, False) for c in cadences))
    selected = ok_Ls[0] if ok_Ls else None
    return {
        "rule": "smallest L≥H with P(LCB>0)≤α at both cadences (no-search coverage)",
        "selected_block": selected,
        "ok_blocks": ok_Ls,
        "sweeps": {k: [{kk: vv for kk, vv in r.items() if kk != "rows"} for r in v]
                   for k, v in sweeps.items()},
        "coverage_stop_fail": selected is None,
    }


def run_e2e_one(seed: int, cadence: CadenceSpec, *, block_lcb: int,
                edge_bps: float = 0.0,
                config: OracleConfig | None = None,
                params: SearchParams | None = None,
                n_restarts: int = N_RESTARTS,
                budget: int = SEARCH_BUDGET) -> dict[str, Any]:
    """Full search → rank → fixed-TEST LCB on one synthetic universe."""
    config = config or OracleConfig(charge_costs=False)
    params = params or SearchParams(L=40, n_boot=80, block_bars=max(64, cadence.hold_bars),
                                    init_size=4)
    streams = make_null_universe(seed, cadence, edge_bps=edge_bps)
    layout = _layout(cadence.n_bars)
    H = cadence.hold_bars
    block_lcb = max(block_lcb, H)

    finalists = [
        run_restart(streams, config, budget=budget, restart_id=r + 1,
                    params=params, segment=layout.search,
                    skip_economics_precondition=True)
        for r in range(n_restarts)
    ]
    folds = contiguous_purged_folds(
        layout.ranking[0], layout.ranking[1], n_folds=3,
        purge_ns=max(H, 1) * 60 * NS)
    pkg = certify_and_rank(
        finalists, streams, config, folds=folds, params=params,
        search_segment=layout.search, include_random_ref=False, include_fill_basis=False)
    if not pkg["ranked"]:
        return {"seed": seed, "cadence": cadence.name, "empty_shortlist": True,
                "gross_pass": False, "net_pass": False}
    top = pkg["ranked"][0].subset
    gross = evaluate_lcb(top, streams, config, layout.gate, block=block_lcb,
                         seed=seed, net=False)
    net = evaluate_lcb(top, streams, config, layout.gate, block=block_lcb,
                       seed=seed, net=True)
    return {
        "seed": seed,
        "cadence": cadence.name,
        "symbol": cadence.symbol,
        "empty_shortlist": False,
        "subset_size": len(top),
        "g_search_hat": pkg["ranked"][0].search_F_hat,
        "fold_median": pkg["ranked"][0].median_F,
        "gross_lcb": gross.get("lcb"),
        "gross_point": gross.get("point"),
        "gross_pass": bool(gross.get("pass_positive")),
        "net_lcb": net.get("lcb"),
        "net_point": net.get("point"),
        "net_pass": bool(net.get("pass_positive")),
        "block_lcb": block_lcb,
        "n_admitted_test": gross.get("n_admitted"),
        "evaluation_count": pkg["evaluation_count"],
        "edge_bps": edge_bps,
        "gate_kind": "LCB_G_GROSS_95",
        "redesign_binder": True,
    }


def end_to_end_alpha(cadence: CadenceSpec, *, block_lcb: int,
                     n_universes: int = N_NULL_PER_CADENCE,
                     **kw) -> dict[str, Any]:
    seeds = bank_seeds(cadence)[:n_universes]
    rows = []
    for seed, cspec in seeds:
        rows.append(run_e2e_one(seed, cspec, block_lcb=block_lcb, edge_bps=0.0, **kw))
    n = len(rows)
    n_pass = sum(1 for r in rows if r.get("gross_pass"))
    rate = n_pass / max(n, 1)
    return {
        "cadence": cadence.name,
        "n": n,
        "n_gross_lcb_positive": n_pass,
        "alpha_hat": rate,
        "alpha_target": ALPHA,
        "pass_stop": rate <= ALPHA,
        "n_net_lcb_positive": sum(1 for r in rows if r.get("net_pass")),
        "block_lcb": block_lcb,
        "rows": rows,
    }


def power_curve(cadence: CadenceSpec, *, block_lcb: int,
                edges: tuple[float, ...] = (2.0, 5.0, 10.0, 20.0, 30.0, 40.0),
                n_per_edge: int = 10, **kw) -> dict[str, Any]:
    """Planted-edge recovery — disclosed, not frozen cells."""
    curve = []
    base = 5000 if cadence.name == "low" else 6000
    for e in edges:
        hits_g = hits_n = 0
        for i in range(n_per_edge):
            r = run_e2e_one(base + int(e * 10) + i, cadence, block_lcb=block_lcb,
                            edge_bps=e, **kw)
            hits_g += int(r.get("gross_pass", False))
            hits_n += int(r.get("net_pass", False))
        curve.append({
            "edge_bps": e,
            "n": n_per_edge,
            "gross_lcb_power": hits_g / n_per_edge,
            "net_lcb_power": hits_n / n_per_edge,
            "cadence": cadence.name,
        })
    return {"cadence": cadence.name, "curve": curve, "binding": False,
            "note": "disclosed only — not frozen to INFR-006 30/40 cells"}


def select_k(*, block_lcb: int, cadence: CadenceSpec = LOW,
             n_per_k: int = 10) -> dict[str, Any]:
    """Rule P3.2: smallest k with net-LCB power ≥ 0.5 at edge = k·RT."""
    curve = []
    selected = None
    for k in K_CANDIDATES:
        edge = k * RT_COST_BPS
        hits = 0
        for i in range(n_per_k):
            r = run_e2e_one(7000 + int(k * 100) + i, cadence, block_lcb=block_lcb,
                            edge_bps=edge)
            hits += int(r.get("net_pass", False))
        rate = hits / n_per_k
        curve.append({"k": k, "edge_bps": edge, "net_lcb_power": rate,
                      "n": n_per_k, "meets": rate >= K_POWER_FLOOR})
        if selected is None and rate >= K_POWER_FLOOR:
            selected = k
    return {
        "rule": f"smallest k in {K_CANDIDATES} with net-LCB power≥{K_POWER_FLOOR} "
                f"at edge=k×RT ({RT_COST_BPS} bps)",
        "selected_k": selected,
        "curve": curve,
        "k_rule_fail": selected is None,
        "floor_formula": "floor_bps = RT_cost_bps × k",
    }


def select_K_random_ref(cadence: CadenceSpec = LOW, *, max_k: int = K_CAP) -> dict[str, Any]:
    """Raise K until median/IQR of random-subset g_gross stabilizes (<10% relative)."""
    streams = make_null_universe(42, cadence)
    config = OracleConfig(charge_costs=False)
    layout = _layout(cadence.n_bars)
    universe = [s.candidate_id for s in streams]
    k_size = min(5, len(universe))
    rng = np.random.default_rng(99)

    def ref_stats(K: int) -> tuple[float, float]:
        gs = []
        for _ in range(K):
            pick = frozenset(str(x) for x in rng.choice(universe, size=k_size, replace=False))
            res = evaluate(pick, streams, config, segment=layout.search, seed=0)
            gs.append(g_gross_point(res, streams))
        arr = np.asarray(gs, dtype=float)
        finite = arr[np.isfinite(arr)]
        if len(finite) < 4:
            return float("nan"), float("nan")
        med = float(np.median(finite))
        iqr = float(np.quantile(finite, 0.75) - np.quantile(finite, 0.25))
        return med, iqr

    K = K_START
    history = []
    selected = K
    while K <= max_k:
        med, iqr = ref_stats(K)
        history.append({"K": K, "median": med, "iqr": iqr})
        if len(history) >= 2:
            prev = history[-2]
            eps = 1e-9
            d_med = abs(med - prev["median"]) / max(abs(prev["median"]), eps)
            d_iqr = abs(iqr - prev["iqr"]) / max(abs(prev["iqr"]), eps)
            if d_med < 0.10 and d_iqr < 0.10:
                selected = prev["K"]
                break
        selected = K
        K *= 2
    return {
        "rule": "double K from 32 until median & IQR change <10%; cap 256; evidence only",
        "selected_K": selected,
        "history": history,
        "binding": False,
    }


def rmax_dd_disclosure(cadence: CadenceSpec = LOW, n_universes: int = 20,
                       r_max: float = 0.05, daily_dd_limit: float = 0.05
                       ) -> dict[str, Any]:
    """Offline (R_max, DD) reconciliation — disclosure only, binds nothing."""
    config = OracleConfig(charge_costs=False, r_max=r_max)
    layout = _layout(cadence.n_bars)
    breaches = 0
    worst = []
    for seed, cspec in bank_seeds(cadence)[:n_universes]:
        streams = make_null_universe(seed, cspec)
        # full-universe walk on search+ranking+gate span for path stress
        subset = frozenset(s.candidate_id for s in streams[:8])
        res = evaluate(subset, streams, config,
                       segment=(layout.search[0], layout.gate[1]), seed=seed)
        eq = res.equity
        if len(eq) < 2:
            continue
        # crude daily-ish: split path into 20 equal segments; max peak-to-trough
        n = len(eq)
        seg = max(n // 20, 1)
        max_dd = 0.0
        for i in range(0, n, seg):
            chunk = eq[i:i + seg]
            if len(chunk) < 2:
                continue
            peak = chunk[0]
            for v in chunk:
                peak = max(peak, v)
                dd = (peak - v) / max(peak, 1e-9)
                max_dd = max(max_dd, dd)
        worst.append(max_dd)
        if max_dd > daily_dd_limit:
            breaches += 1
    rate = breaches / max(len(worst), 1)
    return {
        "binding": False,
        "role": "disclosure_only (operator Round-1 #3)",
        "r_max": r_max,
        "daily_dd_limit": daily_dd_limit,
        "n": len(worst),
        "breach_rate": rate,
        "worst_dd_median": float(np.median(worst)) if worst else float("nan"),
        "worst_dd_p95": float(np.quantile(worst, 0.95)) if worst else float("nan"),
        "reconciled_pair_disclosure": {
            "R_max": r_max,
            "daily_DD": daily_dd_limit,
            "empirical_breach_rate_on_nulls": rate,
            "note": "pair is contradictory at 5%/5% if breach_rate high — disclosure only",
        },
    }


def run_p3_calibration(*, n_null: int = N_NULL_PER_CADENCE,
                       n_power: int = 8,
                       n_coverage: int = 40) -> dict[str, Any]:
    """Full P3 sequence under predeclared rules. No fixture contact."""
    report: dict[str, Any] = {
        "schema": "xena.infr009.p3_cal.v1",
        "predeclared": {
            "alpha": ALPHA,
            "lcb_confidence": LCB_CONFIDENCE,
            "n_null_per_cadence": n_null,
            "n_restarts": N_RESTARTS,
            "budget": SEARCH_BUDGET,
            "rt_cost_bps": RT_COST_BPS,
            "fixtures_forbidden": ["XENA-001", "XENA-002", "XENA-003"],
            "gate_kind": "LCB_G_GROSS_95",
            "legacy_extensive_F_gate": False,
        },
    }
    # 1) block sweep → L
    block_sel = select_block_length([LOW, HIGH], n_universes=n_coverage)
    report["block_selection"] = block_sel
    block_lcb = block_sel["selected_block"]
    if block_lcb is None:
        # still measure e2e with H-floor block for diagnostics; stop will fire
        block_lcb = max(LOW.hold_bars, HIGH.hold_bars, 64)
        report["block_fallback_used"] = block_lcb

    # 2) end-to-end α both cadences
    alpha_low = end_to_end_alpha(LOW, block_lcb=block_lcb, n_universes=n_null)
    alpha_high = end_to_end_alpha(HIGH, block_lcb=block_lcb, n_universes=n_null)
    report["alpha_low"] = {k: v for k, v in alpha_low.items() if k != "rows"}
    report["alpha_high"] = {k: v for k, v in alpha_high.items() if k != "rows"}
    report["alpha_low_rows"] = alpha_low["rows"]
    report["alpha_high_rows"] = alpha_high["rows"]

    # 3) power (disclose)
    report["power_low"] = power_curve(LOW, block_lcb=block_lcb, n_per_edge=n_power)
    report["power_high"] = power_curve(HIGH, block_lcb=block_lcb, n_per_edge=n_power)

    # 4) k rule
    report["k_selection"] = select_k(block_lcb=block_lcb, n_per_k=n_power)

    # 5) K convergence
    report["K_selection"] = select_K_random_ref(LOW)

    # 6) R_max / DD disclosure
    report["rmax_dd_disclosure"] = rmax_dd_disclosure(LOW, n_universes=min(20, n_null))

    # stop-condition
    cov_fail = bool(block_sel.get("coverage_stop_fail"))
    alpha_fail = (not alpha_low["pass_stop"]) or (not alpha_high["pass_stop"])
    stop = cov_fail or alpha_fail
    report["stop_condition"] = {
        "alpha_target": ALPHA,
        "coverage_fail": cov_fail,
        "alpha_low_fail": not alpha_low["pass_stop"],
        "alpha_high_fail": not alpha_high["pass_stop"],
        "STOP": stop,
        "verdict": "STOP" if stop else "PROCEED_TO_P4_ELIGIBLE",
        "selected_block": block_sel.get("selected_block"),
        "selected_k": report["k_selection"].get("selected_k"),
        "selected_K": report["K_selection"].get("selected_K"),
        "note": (
            "If STOP: do not freeze, do not soften α/confidence, do not re-pin extensive-F. "
            "Re-run on a disjoint bank only after procedure change."
        ),
    }
    return report
