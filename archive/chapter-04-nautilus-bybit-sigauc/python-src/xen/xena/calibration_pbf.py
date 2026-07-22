"""INFR-009 P-BF — permutation-through-search binder (selection-aware null).

Replaces LCB(g_gross)>0 as the pass knob. Frozen TEST functional: mean per-leg bps.
Null = re-run search→select→TEST on data with entry↔forward-return alignment broken.
g_gross / LCB kept as companion disclosure only.

Does not call run_final_gate. No XENA fixture TEST/holdout contact.
"""
from __future__ import annotations

import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import replace
from typing import Any

import numpy as np
import polars as pl

import xen.xena.calibration_p3b as p3b
from xen.xena.calibration_p3b import (HIGH, LOW, CadenceSpec, ScaleSpec, _layout,
                                      bank_seeds, make_null_universe)
from xen.xena.certify import certify_and_rank, contiguous_purged_folds
from xen.xena.oracle import CandidateStream, OracleConfig, evaluate
from xen.xena.score import (g_gross_point, lcb_g_leg_studentized, mean_per_leg_bps)
from xen.xena.search import SearchParams, run_restart

ALPHA = 0.05
NS = 1_000_000_000

# Disjoint from all prior P3* banks
DESIGN_SEEDS = (51_000, 52_000)
CONFIRM_SEEDS = (61_000, 62_000)

DESIGN_SCALE = ScaleSpec("design", n_null=16, n_cand=64, budget=200, n_restarts=5,
                         n_power=6, n_coverage=16)
CONFIRM_SCALE = ScaleSpec("confirm", n_null=200, n_cand=64, budget=200, n_restarts=5,
                          n_power=6, n_coverage=200)

# K ladder (amended P-BF.4 — see design.md dated amendment).
# Run K_POOL perms; certify candidate K against the HIGHER rung q_{K_POOL}, never
# against itself. Self-ref vs K_max was a bug: top rung always "stable" by construction.
K_DIAGNOSTIC = (19, 39, 59)          # reported only
K_CERTIFIABLE = (99, 149)            # may freeze if agree with K_POOL
K_POOL = 199                         # validation ceiling (not auto-frozen)
K_STABILITY_TOL = 0.25
# Projected confirm wall-time hard stop (seconds) before launching confirm
CONFIRM_WALL_BUDGET_S = 12 * 3600
# backward-compat aliases used in wall scaling
K_MAX = K_POOL
K_CANDIDATES = K_DIAGNOSTIC + K_CERTIFIABLE + (K_POOL,)
# Bite: planted edge must collapse; null mean shift small
BITE_PLANTED_EDGE_BPS = 20.0
BITE_N_PLANTED_U = 8
BITE_N_NULL_U = 8
BITE_PLANT_COLLAPSE_FRAC = 0.50  # permuted |mean| ≤ (1-frac)*real |mean| on plant bank
BITE_NULL_SHIFT_MAX_BPS = 3.0    # |mean_real - mean_perm| on null bank


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
# Permutation recipe — circular shift of marks Open (entry↔forward break)
# --------------------------------------------------------------------------- #
def permute_entry_forward_alignment(
    streams: list[CandidateStream],
    *,
    lag_bars: int,
    hold_bars: int,
) -> list[CandidateStream]:
    """Break entry-decision ↔ forward-return alignment without mean-invariant P&L shuffle.

    Recipe (exchangeability unit = bar on the shared marks path):
      1. Keep EntryTime, ExitTime, Direction, StopDistance, Censored, entry calendar.
      2. Circularly shift the Open series of each stream's marks by ``lag_bars``.
      3. Rebuild EntryPrice / ExitPrice from the shifted path at the original bar times.
      4. Do **not** re-apply any planted exit shift — plant collapses under the null.

    Preserves cadence, per-candidate leg counts, and cross-candidate crowding (same
    entry times). Does **not** shuffle RealizedBps / per-leg P&L directly (mean-invariant
    trap; EXP-012 / programme lesson permutation-destroy-mean-invariant).

    Parameters
    ----------
    streams : list[CandidateStream]
    lag_bars : int
        Circular lag; must be ≥ hold_bars and not a multiple of n_bars that is 0 mod n.
    hold_bars : int
        Cadence hold (used only to validate lag scale).
    """
    del hold_bars  # documented exchangeability scale; lag chosen by caller
    if lag_bars == 0:
        raise ValueError("lag_bars=0 is the identity; not a permutation")
    out: list[CandidateStream] = []
    for s in streams:
        times = s.marks.get_column("CloseTime").to_numpy().astype(np.int64)
        opens = s.marks.get_column("Open").to_numpy().astype(float)
        n = len(opens)
        lag = int(lag_bars) % n
        if lag == 0:
            raise ValueError("lag_bars multiple of n_bars is identity")
        opens_p = np.roll(opens, lag)
        marks = pl.DataFrame({"CloseTime": times, "Open": opens_p})
        rows = s.trades.to_dicts()
        new_rows = []
        for r in rows:
            i0 = int(np.searchsorted(times, int(r["EntryTime"]), side="left"))
            i1 = int(np.searchsorted(times, int(r["ExitTime"]), side="left"))
            i0 = min(max(i0, 0), n - 1)
            i1 = min(max(i1, 0), n - 1)
            ep = float(opens_p[i0])
            xp = float(opens_p[i1])
            new_rows.append({
                "EntryTime": int(r["EntryTime"]),
                "ExitTime": int(r["ExitTime"]),
                "Direction": float(r["Direction"]),
                "EntryPrice": ep,
                "ExitPrice": xp,
                "StopDistance": float(r["StopDistance"]),
                "Censored": bool(r["Censored"]),
            })
        trades = pl.DataFrame(new_rows, schema={
            "EntryTime": pl.Int64, "ExitTime": pl.Int64, "Direction": pl.Float64,
            "EntryPrice": pl.Float64, "ExitPrice": pl.Float64,
            "StopDistance": pl.Float64, "Censored": pl.Boolean,
        })
        out.append(CandidateStream(
            s.candidate_id, s.symbol, trades, marks, s.cost_bps, s.money_per_unit))
    return out


def draw_permutation_lags(n_bars: int, hold_bars: int, k: int, seed: int) -> np.ndarray:
    """Draw K distinct non-identity lags in [hold_bars, n_bars - hold_bars)."""
    lo = max(int(hold_bars), 1)
    hi = max(n_bars - lo, lo + 1)
    span = hi - lo
    if span <= 1:
        # degenerate short path — use [1, n_bars)
        lo, hi = 1, max(n_bars, 2)
        span = hi - lo
    rng = np.random.default_rng(seed)
    if span >= k:
        lags = rng.choice(np.arange(lo, hi), size=k, replace=False)
    else:
        lags = rng.integers(lo, hi, size=k)
        # force non-zero mod n_bars
        lags = np.where(lags % n_bars == 0, lo, lags)
    return lags.astype(np.int64)


def universe_signed_mean_bps(streams: list[CandidateStream]) -> float:
    """Unweighted mean of Direction*(Exit/Entry-1)*1e4 over all trades (bite diagnostic)."""
    vals: list[np.ndarray] = []
    for s in streams:
        t = s.trades
        if t.height == 0:
            continue
        d = t.get_column("Direction").to_numpy().astype(float)
        ep = t.get_column("EntryPrice").to_numpy().astype(float)
        xp = t.get_column("ExitPrice").to_numpy().astype(float)
        vals.append(d * (xp / np.maximum(ep, 1e-12) - 1.0) * 1e4)
    if not vals:
        return float("nan")
    return float(np.mean(np.concatenate(vals)))


# --------------------------------------------------------------------------- #
# Pipeline under real / permuted data
# --------------------------------------------------------------------------- #
def _search_params(cadence: CadenceSpec) -> SearchParams:
    return SearchParams(L=40, n_boot=80, block_bars=max(64, cadence.hold_bars), init_size=4)


def run_search_select_test(
    streams: list[CandidateStream],
    cadence: CadenceSpec,
    *,
    scale: ScaleSpec,
    seed: int,
    purge_mult: int = 1,
) -> dict[str, Any]:
    """One full search→select→TEST path. Returns mean-per-leg + companion disclosures."""
    config = OracleConfig(charge_costs=False)
    layout = _layout(cadence.n_bars, cadence.hold_bars, purge_mult=purge_mult)
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
        return {
            "empty": True, "mean_per_leg": float("-inf"), "g_gross": float("nan"),
            "lcb_leg": float("-inf"), "lcb_pass_disclosure": False,
            "n_legs": 0, "g_search_hat": float("nan"), "subset": [],
        }
    top = pkg["ranked"][0].subset
    res = evaluate(top, streams, config, segment=layout.gate, seed=seed)
    mpl = mean_per_leg_bps(res, streams, net=False)
    gg = g_gross_point(res, streams, net=False)
    lcb = lcb_g_leg_studentized(res, streams, n_boot=200, seed=seed + 99,
                                block_legs=1, confidence=0.95, net=False)
    return {
        "empty": False,
        "mean_per_leg": mpl,
        "g_gross": gg,
        "lcb_leg": lcb.get("lcb"),
        "lcb_pass_disclosure": bool(lcb.get("pass_positive")),
        "n_legs": lcb.get("n_legs"),
        "g_search_hat": pkg["ranked"][0].search_F_hat,
        "subset": sorted(str(x) for x in top),
    }


def permutation_null_stats(
    streams: list[CandidateStream],
    cadence: CadenceSpec,
    *,
    scale: ScaleSpec,
    seed: int,
    k: int,
    purge_mult: int = 1,
) -> dict[str, Any]:
    """K search-through-permutation mean-per-leg stats for one universe."""
    lags = draw_permutation_lags(cadence.n_bars, cadence.hold_bars, k, seed=seed + 77_001)
    null_stats: list[float] = []
    for j, lag in enumerate(lags):
        perm = permute_entry_forward_alignment(
            streams, lag_bars=int(lag), hold_bars=cadence.hold_bars)
        out = run_search_select_test(
            perm, cadence, scale=scale, seed=seed + 10_000 + j, purge_mult=purge_mult)
        null_stats.append(float(out["mean_per_leg"]))
    arr = np.asarray(null_stats, dtype=float)
    finite = arr[np.isfinite(arr)]
    q = float(np.quantile(finite, 1.0 - ALPHA)) if len(finite) else float("inf")
    return {
        "null_stats": null_stats,
        "n_finite": int(len(finite)),
        "q_1m_alpha": q,
        "lags": [int(x) for x in lags],
    }


def pass_rule(t_real: float, q_null: float) -> bool:
    """PASS iff TEST mean-per-leg exceeds (1−α) quantile of own perm null."""
    if not np.isfinite(t_real) or not np.isfinite(q_null):
        return False
    return bool(t_real > q_null)


# --------------------------------------------------------------------------- #
# Worker payloads (process-pool friendly)
# --------------------------------------------------------------------------- #
def _worker_universe(payload: dict) -> dict:
    """Run one universe: real pipeline + K perms (or bite-only raw means)."""
    seed = int(payload["seed"])
    cadence_name = payload["cadence_name"]
    cadence = LOW if cadence_name == "low" else HIGH
    # rebuild cadence with symbol if needed
    if payload.get("symbol") and payload["symbol"] != cadence.symbol:
        cadence = CadenceSpec(
            cadence.name, cadence.hold_bars, cadence.n_bars, cadence.n_trades,
            cadence.kind, symbol=payload["symbol"])
    scale = ScaleSpec(**payload["scale"])
    k = int(payload["k"])
    purge_mult = int(payload.get("purge_mult", 1))
    edge_bps = float(payload.get("edge_bps", 0.0))
    mode = payload.get("mode", "e2e")  # e2e | bite

    t0 = time.perf_counter()
    streams = make_null_universe(
        seed, cadence, n_candidates=scale.n_cand, edge_bps=edge_bps)

    if mode == "bite":
        # raw universe mean before/after one strong permutation (no full search)
        real_m = universe_signed_mean_bps(streams)
        lag = int(draw_permutation_lags(
            cadence.n_bars, cadence.hold_bars, 1, seed=seed + 3)[0])
        perm = permute_entry_forward_alignment(
            streams, lag_bars=lag, hold_bars=cadence.hold_bars)
        perm_m = universe_signed_mean_bps(perm)
        return {
            "seed": seed, "cadence": cadence_name, "edge_bps": edge_bps,
            "real_mean_bps": real_m, "perm_mean_bps": perm_m, "lag": lag,
            "wall_s": time.perf_counter() - t0, "mode": "bite",
        }

    real = run_search_select_test(
        streams, cadence, scale=scale, seed=seed, purge_mult=purge_mult)
    null = permutation_null_stats(
        streams, cadence, scale=scale, seed=seed, k=k, purge_mult=purge_mult)
    t_real = float(real["mean_per_leg"])
    q = float(null["q_1m_alpha"])
    passed = pass_rule(t_real, q)
    return {
        "seed": seed,
        "cadence": cadence_name,
        "edge_bps": edge_bps,
        "pass": passed,
        "mean_per_leg": t_real,
        "q_1m_alpha": q,
        "null_stats": null["null_stats"],
        "n_null_finite": null["n_finite"],
        "g_gross": real.get("g_gross"),
        "lcb_leg": real.get("lcb_leg"),
        "lcb_pass_disclosure": real.get("lcb_pass_disclosure"),
        "n_legs": real.get("n_legs"),
        "g_search_hat": real.get("g_search_hat"),
        "empty": real.get("empty"),
        "wall_s": time.perf_counter() - t0,
        "mode": "e2e",
        "k": k,
    }


def _map_universes(payloads: list[dict], *, n_workers: int | None = None,
                   desc: str = "") -> list[dict]:
    if not payloads:
        return []
    workers = n_workers or min(8, max(1, (os_cpu() or 4) - 1))
    print(f"  [{desc}] n={len(payloads)} workers={workers}", flush=True)
    if workers <= 1 or len(payloads) == 1:
        out_s: list[dict] = []
        for i, p in enumerate(payloads):
            try:
                out_s.append(_worker_universe(p))
            except Exception as e:  # noqa: BLE001 — surface worker faults
                print(f"    {desc} FAIL seed={p.get('seed')}: {e!r}", flush=True)
                raise
            if (i + 1) % max(1, len(payloads) // 10) == 0 or (i + 1) == len(payloads):
                print(f"    {desc} {i + 1}/{len(payloads)}", flush=True)
        return out_s
    out: list[dict | None] = [None] * len(payloads)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_worker_universe, p): i for i, p in enumerate(payloads)}
        done = 0
        for fut in as_completed(futs):
            i = futs[fut]
            try:
                out[i] = fut.result()
            except Exception as e:  # noqa: BLE001
                seed = payloads[i].get("seed")
                print(f"    {desc} FAIL seed={seed}: {e!r}", flush=True)
                raise
            done += 1
            if done % max(1, len(payloads) // 10) == 0 or done == len(payloads):
                print(f"    {desc} {done}/{len(payloads)}", flush=True)
    missing = [i for i, r in enumerate(out) if r is None]
    if missing:
        raise RuntimeError(f"{desc}: missing results for indices {missing[:5]}…")
    return [r for r in out if r is not None]


def os_cpu() -> int:
    import os
    return int(os.cpu_count() or 4)


def _scale_dict(scale: ScaleSpec) -> dict:
    return {
        "name": scale.name, "n_null": scale.n_null, "n_cand": scale.n_cand,
        "budget": scale.budget, "n_restarts": scale.n_restarts,
        "n_power": scale.n_power, "n_coverage": scale.n_coverage,
    }


def _seed_payloads(cadence: CadenceSpec, n: int, *, k: int, scale: ScaleSpec,
                   edge_bps: float = 0.0, mode: str = "e2e",
                   purge_mult: int = 1) -> list[dict]:
    rows = []
    for seed, cspec in bank_seeds(cadence, n):
        rows.append({
            "seed": seed,
            "cadence_name": cspec.name,
            "symbol": cspec.symbol,
            "k": k,
            "scale": _scale_dict(scale),
            "edge_bps": edge_bps,
            "mode": mode,
            "purge_mult": purge_mult,
        })
    return rows


# --------------------------------------------------------------------------- #
# DESIGN: bite-check + K-convergence + null calibration
# --------------------------------------------------------------------------- #
def bite_check(*, scale: ScaleSpec = DESIGN_SCALE, n_workers: int | None = None,
               purge_mult: int = 1) -> dict[str, Any]:
    """Validate permutation recipe bite on design seeds (small n)."""
    _set_seeds(*DESIGN_SEEDS)
    results: dict[str, Any] = {}
    for c in (LOW, HIGH):
        plant_payloads = _seed_payloads(
            c, BITE_N_PLANTED_U, k=1, scale=scale,
            edge_bps=BITE_PLANTED_EDGE_BPS, mode="bite", purge_mult=purge_mult)
        # offset plant seeds so they do not collide with null bank_seeds main range
        for p in plant_payloads:
            p["seed"] = int(p["seed"]) + 9_000
        null_payloads = _seed_payloads(
            c, BITE_N_NULL_U, k=1, scale=scale, edge_bps=0.0, mode="bite",
            purge_mult=purge_mult)
        plant_rows = _map_universes(plant_payloads, n_workers=n_workers,
                                    desc=f"bite-plant-{c.name}")
        null_rows = _map_universes(null_payloads, n_workers=n_workers,
                                   desc=f"bite-null-{c.name}")
        pr = np.array([r["real_mean_bps"] for r in plant_rows], dtype=float)
        pp = np.array([r["perm_mean_bps"] for r in plant_rows], dtype=float)
        nr = np.array([r["real_mean_bps"] for r in null_rows], dtype=float)
        np_ = np.array([r["perm_mean_bps"] for r in null_rows], dtype=float)
        plant_real = float(np.nanmean(pr))
        plant_perm = float(np.nanmean(pp))
        null_real = float(np.nanmean(nr))
        null_perm = float(np.nanmean(np_))
        # collapse: |plant_perm| should be much smaller than |plant_real| when plant>0
        if abs(plant_real) < 1e-6:
            plant_ok = abs(plant_perm) < BITE_NULL_SHIFT_MAX_BPS
            collapse_frac = float("nan")
        else:
            collapse_frac = 1.0 - abs(plant_perm) / abs(plant_real)
            plant_ok = bool(collapse_frac >= BITE_PLANT_COLLAPSE_FRAC)
        null_ok = bool(abs(null_real - null_perm) <= BITE_NULL_SHIFT_MAX_BPS)
        results[c.name] = {
            "plant_real_mean_bps": plant_real,
            "plant_perm_mean_bps": plant_perm,
            "plant_collapse_frac": collapse_frac,
            "plant_ok": plant_ok,
            "null_real_mean_bps": null_real,
            "null_perm_mean_bps": null_perm,
            "null_shift_bps": abs(null_real - null_perm),
            "null_ok": null_ok,
            "bite_ok": plant_ok and null_ok,
            "plant_rows": plant_rows,
            "null_rows": null_rows,
            "recipe": "circular_shift_marks_open_rebuild_fills",
            "thresholds": {
                "plant_collapse_frac_min": BITE_PLANT_COLLAPSE_FRAC,
                "null_shift_max_bps": BITE_NULL_SHIFT_MAX_BPS,
                "planted_edge_bps": BITE_PLANTED_EDGE_BPS,
            },
        }
        print(f"  bite {c.name}: plant {plant_real:.3f}→{plant_perm:.3f} "
              f"collapse={collapse_frac} ok={plant_ok}; "
              f"null {null_real:.3f}→{null_perm:.3f} ok={null_ok}", flush=True)
    both = all(results[c.name]["bite_ok"] for c in (LOW, HIGH))
    return {"ok": both, "by_cadence": results,
            "recipe": "circular_shift_marks_open_rebuild_fills",
            "exchangeability_unit": "bar (circular lag on marks Open)",
            "forbidden": "do not shuffle RealizedBps / per-leg P&L directly"}


def _prefix_q(null_stats: list[float] | np.ndarray, k: int) -> float:
    ns = np.asarray(null_stats[:k], dtype=float)
    fin = ns[np.isfinite(ns)]
    if len(fin) == 0:
        return float("inf")
    return float(np.quantile(fin, 1.0 - ALPHA))


def k_convergence(*, scale: ScaleSpec = DESIGN_SCALE, n_workers: int | None = None,
                  purge_mult: int = 1) -> dict[str, Any]:
    """On design null bank: run K_POOL perms; certify K vs higher rung (amended P-BF.4).

    Freeze gate (not self-referential):
      for K in (99, 149): median_u |q_K(u) − q_199(u)| / (MAD(q_199)+ε) ≤ tol
      smallest such K wins; joint K* = max(low, high).
    If neither certifiable → K* = None (do not freeze top rung by construction).
    """
    _set_seeds(*DESIGN_SEEDS)
    by_c: dict[str, Any] = {}
    walls: list[float] = []
    for c in (LOW, HIGH):
        payloads = _seed_payloads(
            c, scale.n_null, k=K_POOL, scale=scale, edge_bps=0.0, mode="e2e",
            purge_mult=purge_mult)
        rows = _map_universes(payloads, n_workers=n_workers, desc=f"kconv-{c.name}")
        walls.extend(float(r["wall_s"]) for r in rows)

        q_pool = np.asarray([_prefix_q(r["null_stats"], K_POOL) for r in rows], dtype=float)
        mad_pool = float(np.nanmedian(np.abs(q_pool - np.nanmedian(q_pool))))
        eps = max(mad_pool, 1.0)

        k_curve = []
        for K in K_CANDIDATES:
            qs = np.asarray([_prefix_q(r["null_stats"], K) for r in rows], dtype=float)
            passes = [
                pass_rule(float(r["mean_per_leg"]), float(q))
                for r, q in zip(rows, qs)
            ]
            rels = np.abs(qs - q_pool) / eps
            med_rel = float(np.nanmedian(rels))
            # Certifiable only if K < K_POOL (higher rung is the validator).
            certifiable = K in K_CERTIFIABLE
            stable = bool(certifiable and med_rel <= K_STABILITY_TOL)
            k_curve.append({
                "K": K,
                "median_q": float(np.nanmedian(qs)),
                "mad_q": float(np.nanmedian(np.abs(qs - np.nanmedian(qs)))),
                "pass_rate": float(np.mean(passes)),
                "n": len(rows),
                "median_rel_vs_Kpool": med_rel,
                "vs": K_POOL,
                "certifiable": certifiable,
                "stable": stable,
                # legacy key for readers
                "median_rel_vs_Kmax": med_rel,
            })

        chosen: int | None = None
        for entry in k_curve:
            if entry["stable"] and chosen is None:
                chosen = int(entry["K"])

        # primary disclosure: q_99 vs q_199 (the amendment's freeze gate)
        rel_99 = next(e["median_rel_vs_Kpool"] for e in k_curve if e["K"] == 99)
        rel_149 = next(e["median_rel_vs_Kpool"] for e in k_curve if e["K"] == 149)

        by_c[c.name] = {
            "k_curve": k_curve,
            "chosen_K": chosen,
            "converged": chosen is not None,
            "rel_q99_vs_q199": rel_99,
            "rel_q149_vs_q199": rel_149,
            "q99_vs_q199_ok": bool(rel_99 <= K_STABILITY_TOL),
            "n_universes": len(rows),
            "median_wall_s_per_universe_Kpool": float(
                np.median([r["wall_s"] for r in rows])),
            "rows_summary": [{
                "seed": r["seed"],
                "mean_per_leg": r["mean_per_leg"],
                "q99": _prefix_q(r["null_stats"], 99),
                "q149": _prefix_q(r["null_stats"], 149),
                "q199": _prefix_q(r["null_stats"], 199),
                "pass_K99": pass_rule(float(r["mean_per_leg"]),
                                      _prefix_q(r["null_stats"], 99)),
                "pass_Kpool": pass_rule(float(r["mean_per_leg"]),
                                        _prefix_q(r["null_stats"], K_POOL)),
                "wall_s": r["wall_s"],
            } for r in rows],
        }
        print(
            f"  kconv {c.name}: chosen_K={chosen} "
            f"rel99={rel_99:.3f} rel149={rel_149:.3f} tol={K_STABILITY_TOL} "
            f"curve={[(e['K'], round(e['median_rel_vs_Kpool'], 3), e['stable']) for e in k_curve]}",
            flush=True,
        )

    low_ok = by_c["low"]["converged"]
    high_ok = by_c["high"]["converged"]
    if low_ok and high_ok:
        K_star: int | None = max(int(by_c["low"]["chosen_K"]),
                                 int(by_c["high"]["chosen_K"]))
        converged = True
    else:
        K_star = None
        converged = False

    med_wall_pool = float(np.median(walls)) if walls else float("nan")
    n_workers = n_workers or min(8, max(1, os_cpu() - 1))
    n_jobs = CONFIRM_SCALE.n_null * 2
    if K_star is not None:
        scale_factor = (1 + K_star) / (1 + K_POOL)
        med_wall_kstar = med_wall_pool * scale_factor
        confirm_wall_est = med_wall_kstar * n_jobs / max(n_workers, 1)
        feasible = bool(confirm_wall_est <= CONFIRM_WALL_BUDGET_S)
    else:
        # Would-need wall at unvalidated ceiling (disclosure for exit (c) decision)
        med_wall_kstar = med_wall_pool
        confirm_wall_est = med_wall_pool * n_jobs / max(n_workers, 1)
        feasible = False

    return {
        "rule": "amended_P-BF.4_qK_vs_q199",
        "K_diagnostic": list(K_DIAGNOSTIC),
        "K_certifiable": list(K_CERTIFIABLE),
        "K_pool": K_POOL,
        "K_candidates": list(K_CANDIDATES),
        "K_max": K_POOL,
        "stability_tol": K_STABILITY_TOL,
        "K_star": K_star,
        "converged": converged,
        "by_cadence": by_c,
        "median_wall_s_universe_Kpool": med_wall_pool,
        "median_wall_s_universe_Kmax": med_wall_pool,
        "median_wall_s_universe_Kstar_est": med_wall_kstar,
        "confirm_wall_est_s": confirm_wall_est,
        "confirm_wall_budget_s": CONFIRM_WALL_BUDGET_S,
        "confirm_feasible": feasible,
        "n_workers_assumed": n_workers,
        "note": (
            "K* is smallest certifiable K in {99,149} with median rel vs q_199 ≤ tol. "
            "K_pool=199 is validator only — never frozen solely for being the top rung. "
            "If not converged → do not freeze; recommend exit (c)."
        ),
    }


def design_null_calibration(*, K: int, scale: ScaleSpec = DESIGN_SCALE,
                            n_workers: int | None = None,
                            purge_mult: int = 1) -> dict[str, Any]:
    """E2e false-pass on design null bank under frozen K (sanity, not the gate)."""
    _set_seeds(*DESIGN_SEEDS)
    out: dict[str, Any] = {}
    for c in (LOW, HIGH):
        payloads = _seed_payloads(
            c, scale.n_null, k=K, scale=scale, edge_bps=0.0, mode="e2e",
            purge_mult=purge_mult)
        rows = _map_universes(payloads, n_workers=n_workers,
                              desc=f"design-cal-{c.name}-K{K}")
        k_pass = sum(1 for r in rows if r["pass"])
        n = len(rows)
        ph = k_pass / max(n, 1)
        lo, hi = wilson(k_pass, n)
        out[c.name] = {
            "n": n, "n_pass": k_pass, "alpha_hat": ph,
            "alpha_se": binomial_se(ph, n),
            "alpha_wilson_95": {"low": lo, "high": hi},
            "calibration_ok": ph <= ALPHA + 0.05,  # loose design band (disclosure)
            "median_wall_s": float(np.median([r["wall_s"] for r in rows])),
            "rows": rows,
        }
        print(f"  design-cal {c.name}: α̂={ph:.3f} ({k_pass}/{n})", flush=True)
    return out


def run_design(*, n_workers: int | None = None, purge_mult: int = 1) -> dict[str, Any]:
    print("[P-BF] DESIGN: bite-check...", flush=True)
    bite = bite_check(scale=DESIGN_SCALE, n_workers=n_workers, purge_mult=purge_mult)
    if not bite["ok"]:
        return {
            "bank": "design",
            "seeds": {"low": DESIGN_SEEDS[0], "high": DESIGN_SEEDS[1]},
            "bite": _strip_rows(bite),
            "frozen_procedure": None,
            "design_ok": False,
            "stop_reason": "bite_check_failed",
            "note": "Fix permutation recipe; do not proceed to confirm.",
        }

    print("[P-BF] DESIGN: K-convergence (amended P-BF.4 vs q_199)...", flush=True)
    kconv = k_convergence(scale=DESIGN_SCALE, n_workers=n_workers, purge_mult=purge_mult)

    if not kconv.get("converged") or kconv.get("K_star") is None:
        return {
            "bank": "design",
            "seeds": {"low": DESIGN_SEEDS[0], "high": DESIGN_SEEDS[1]},
            "bite": _strip_rows(bite),
            "k_convergence": _strip_kconv(kconv),
            "frozen_procedure": None,
            "design_ok": False,
            "stop_reason": "K_not_converged",
            "recommend": "exit_(c)_two_stage",
            "note": (
                "q_99 (and q_149) did not settle vs q_199 on design bank. "
                "Do not freeze top-rung K by construction; do not under-K. "
                "Recommend exit (c) — compute/permutation-validity class."
            ),
        }

    if not kconv["confirm_feasible"]:
        return {
            "bank": "design",
            "seeds": {"low": DESIGN_SEEDS[0], "high": DESIGN_SEEDS[1]},
            "bite": _strip_rows(bite),
            "k_convergence": _strip_kconv(kconv),
            "frozen_procedure": None,
            "design_ok": False,
            "stop_reason": "confirm_compute_infeasible",
            "recommend": "exit_(c)_two_stage",
            "note": "Do not under-K the null; escalate to (c) rather than weak K.",
        }

    K = int(kconv["K_star"])
    # Design-null α̂ from K-convergence rows (prefix-K of the pool — no second search).
    cal: dict[str, Any] = {}
    for cname in ("low", "high"):
        curve = kconv["by_cadence"][cname]["k_curve"]
        hit = next((e for e in curve if e["K"] == K), curve[-1])
        n = int(hit["n"])
        k_pass = int(round(hit["pass_rate"] * n))
        ph = float(hit["pass_rate"])
        lo, hi = wilson(k_pass, n)
        cal[cname] = {
            "n": n, "n_pass": k_pass, "alpha_hat": ph,
            "alpha_se": binomial_se(ph, n),
            "alpha_wilson_95": {"low": lo, "high": hi},
            "source": f"k_convergence prefix K={K} certified vs q_{K_POOL}",
        }
        print(f"  design-cal {cname}: α̂={ph:.3f} ({k_pass}/{n}) [from kconv]", flush=True)

    frozen = {
        "binder": "permutation_through_search",
        "functional": "mean_per_leg_bps",
        "pass_rule": "T_real > quantile_{1-α}(T_perm_1..K)",
        "alpha": ALPHA,
        "K": K,
        "K_pool_validator": K_POOL,
        "K_rule": "amended_P-BF.4_qK_vs_q199",
        "permutation_recipe": "circular_shift_marks_open_rebuild_fills",
        "exchangeability_unit": "bar",
        "purge_mult": purge_mult,
        "n_restarts": DESIGN_SCALE.n_restarts,
        "n_cand": DESIGN_SCALE.n_cand,
        "budget": DESIGN_SCALE.budget,
        "companion_disclosure": ["g_gross_point", "lcb_g_leg_studentized"],
        "companion_not_pass_knob": True,
        "design_seeds": {"low": DESIGN_SEEDS[0], "high": DESIGN_SEEDS[1]},
        "confirm_seeds": {"low": CONFIRM_SEEDS[0], "high": CONFIRM_SEEDS[1]},
        "design_n_null": DESIGN_SCALE.n_null,
        "confirm_n_null": CONFIRM_SCALE.n_null,
        "bite_ok": True,
        "design_alpha_low": cal["low"]["alpha_hat"],
        "design_alpha_high": cal["high"]["alpha_hat"],
        "confirm_wall_est_s": kconv["confirm_wall_est_s"],
        "rel_q99_vs_q199_low": kconv["by_cadence"]["low"]["rel_q99_vs_q199"],
        "rel_q99_vs_q199_high": kconv["by_cadence"]["high"]["rel_q99_vs_q199"],
    }
    return {
        "bank": "design",
        "seeds": {"low": DESIGN_SEEDS[0], "high": DESIGN_SEEDS[1]},
        "bite": _strip_rows(bite),
        "k_convergence": _strip_kconv(kconv),
        "design_calibration": cal,
        "frozen_procedure": frozen,
        "design_ok": True,
        "stop_reason": None,
    }


def _strip_rows(bite: dict) -> dict:
    out = {k: v for k, v in bite.items() if k != "by_cadence"}
    bc = {}
    for cn, block in bite.get("by_cadence", {}).items():
        bc[cn] = {k: v for k, v in block.items() if k not in ("plant_rows", "null_rows")}
    out["by_cadence"] = bc
    return out


def _strip_kconv(kconv: dict) -> dict:
    out = {k: v for k, v in kconv.items() if k != "by_cadence"}
    bc = {}
    for cn, block in kconv.get("by_cadence", {}).items():
        bc[cn] = {k: v for k, v in block.items() if k != "rows_summary"}
        # keep compact summary
        bc[cn]["rows_summary"] = block.get("rows_summary", [])
    out["by_cadence"] = bc
    return out


# --------------------------------------------------------------------------- #
# CONFIRM gate (frozen procedure only)
# --------------------------------------------------------------------------- #
def confirm_gate(procedure: dict, *, scale: ScaleSpec = CONFIRM_SCALE,
                 n_workers: int | None = None) -> dict[str, Any]:
    _set_seeds(*CONFIRM_SEEDS)
    K = int(procedure["K"])
    purge_mult = int(procedure.get("purge_mult", 1))
    print(f"[P-BF] CONFIRM: K={K} n_null={scale.n_null} both cadences...", flush=True)
    alpha_blocks = {}
    row_blocks = {}
    for c in (LOW, HIGH):
        payloads = _seed_payloads(
            c, scale.n_null, k=K, scale=scale, edge_bps=0.0, mode="e2e",
            purge_mult=purge_mult)
        rows = _map_universes(payloads, n_workers=n_workers,
                              desc=f"confirm-{c.name}")
        k_pass = sum(1 for r in rows if r["pass"])
        n = len(rows)
        ph = k_pass / max(n, 1)
        lo, hi = wilson(k_pass, n)
        alpha_blocks[c.name] = {
            "cadence": c.name, "n": n, "n_pass": k_pass,
            "alpha_hat": ph, "alpha_se": binomial_se(ph, n),
            "alpha_wilson_95": {"low": lo, "high": hi},
            "pass_stop": ph <= ALPHA,
            "median_wall_s": float(np.median([r["wall_s"] for r in rows])),
            # companion disclosure: old LCB pass rate (not the gate)
            "companion_lcb_pass_rate": float(np.mean([
                1.0 if r.get("lcb_pass_disclosure") else 0.0 for r in rows])),
        }
        row_blocks[c.name] = [{
            "seed": r["seed"], "pass": r["pass"],
            "mean_per_leg": r["mean_per_leg"], "q_1m_alpha": r["q_1m_alpha"],
            "g_gross": r.get("g_gross"), "lcb_leg": r.get("lcb_leg"),
            "lcb_pass_disclosure": r.get("lcb_pass_disclosure"),
            "n_legs": r.get("n_legs"), "g_search_hat": r.get("g_search_hat"),
            "wall_s": r.get("wall_s"),
        } for r in rows]
        print(f"  confirm {c.name}: α̂={ph:.4f} ({k_pass}/{n}) "
              f"wilson=[{lo:.3f},{hi:.3f}] stop_ok={ph <= ALPHA}", flush=True)

    a_low = alpha_blocks["low"]
    a_high = alpha_blocks["high"]
    gate_pass = bool(a_low["pass_stop"] and a_high["pass_stop"])
    if gate_pass:
        verdict = "PASS"
        recommend = "P4"
        note = (
            "e2e point false-pass ≤5% both cadences under permutation-through-search. "
            "Recommend P4 (freeze procedure registry; blind VAL; route) — operator-mandated."
        )
    else:
        # Failure is α under a valid selection-aware null (not compute/recipe — those stopped at design)
        verdict = "FAIL"
        recommend = "TERMINAL_cannot_certify"
        note = (
            "the pipeline cannot certify gross structure at α=5% under a selection-aware null"
        )
    return {
        "bank": "confirm",
        "seeds": {"low": CONFIRM_SEEDS[0], "high": CONFIRM_SEEDS[1]},
        "procedure": procedure,
        "alpha_low": a_low,
        "alpha_high": a_high,
        "alpha_low_rows": row_blocks["low"],
        "alpha_high_rows": row_blocks["high"],
        "stop_condition": {
            "alpha_target": ALPHA,
            "alpha_low_fail": not a_low["pass_stop"],
            "alpha_high_fail": not a_high["pass_stop"],
            "PASS": gate_pass,
            "verdict": verdict,
            "recommend": recommend,
            "gate_rule": "point alpha_hat<=5% both cadences (permutation-calibrated mean-per-leg)",
            "note": note,
            "forbidden": [
                "no P3e", "no alpha soften", "no L/interval knobs on old LCB",
                "no implement exit (c) in this phase",
            ],
        },
    }


def run_pbf(*, n_workers: int | None = None, purge_mult: int = 1,
            design_only: bool = False,
            procedure: dict | None = None) -> tuple[dict, dict | None]:
    if procedure is None:
        design = run_design(n_workers=n_workers, purge_mult=purge_mult)
        if not design.get("design_ok") or design_only:
            return design, None
        procedure = design["frozen_procedure"]
    else:
        design = {"bank": "design", "frozen_procedure": procedure,
                  "design_ok": True, "note": "procedure supplied (skip redesign)"}
    confirm = confirm_gate(procedure, scale=CONFIRM_SCALE, n_workers=n_workers)
    return design, confirm
