"""Controls (design §6). DIRECTION-DERANGEMENT + SMA-BENCHMARK + MATCHED-RANDOM-ENTRY are
INFORMATIVE; PATH-FUTURE-DESTROY is the HARD future-destroy validity tripwire (§11).

All derangements are fixed-point-free index permutations within (symbol x DESIGN calendar-third),
matching L-28. Batteries are >=200 seeds with percentile reads (L-19). Costs use the governing
allowance (2.0 bps).
"""
from __future__ import annotations

import numpy as np

from capture import simulate_independent
from config import (
    ALLOWANCE_GOVERNING,
    DERANGE_SEEDS,
    FEE_RT_BPS,
    FUNDING_BPS_PER_STAMP,
    MATCHED_RANDOM_SEEDS,
    NS,
    PLANT_EXPECTANCY_BPS,
    PLANT_TRIPWIRE_BPS,
    TRIPWIRE_SEEDS,
)

_FUNDING_INTERVAL_NS = 8 * 3600 * NS


def _derangement(rng: np.random.Generator, idx: np.ndarray) -> np.ndarray:
    """Fixed-point-free permutation of ``idx`` (retry until no i->i). len 1 -> unchanged (flagged)."""
    n = idx.size
    if n < 2:
        return idx.copy()
    while True:
        perm = rng.permutation(n)
        if not np.any(perm == np.arange(n)):
            return idx[perm]


def _thirds(entry_ts: np.ndarray, band_lo_ns: int, band_hi_ns: int) -> np.ndarray:
    """Assign each entry to a DESIGN calendar-third (equal elapsed time) in {0,1,2}."""
    span = max(1, band_hi_ns - band_lo_ns)
    frac = (entry_ts - band_lo_ns) / span
    return np.clip((frac * 3).astype(int), 0, 2)


def _funding_bps(entry_ts: np.ndarray, exit_ts: np.ndarray) -> np.ndarray:
    """Vectorised discrete funding (same formula as xen.evaluation.count_bybit_funding_stamps)."""
    stamps = exit_ts // _FUNDING_INTERVAL_NS - entry_ts // _FUNDING_INTERVAL_NS
    return FUNDING_BPS_PER_STAMP * stamps.astype(float)


# ------------------------------------------------ direction derangement ----


def direction_derangement(episodes: list[dict], band_lo_ns: int, band_hi_ns: int,
                          seeds=DERANGE_SEEDS) -> dict:
    """Derange entry SIDES within (symbol x third); paths (raw returns) + costs fixed (§6)."""
    if len(episodes) < 3:
        return {"powered": False, "n_episodes": len(episodes)}
    side = np.array([e["side"] for e in episodes], float)
    raw = np.array([e["gross_bps"] / e["side"] for e in episodes], float)   # own-path oo return
    cost = np.array([FEE_RT_BPS + e["funding_bps"] + ALLOWANCE_GOVERNING for e in episodes], float)
    entry_ts = np.array([e["entry_ts"] for e in episodes])
    thirds = _thirds(entry_ts, band_lo_ns, band_hi_ns)
    live = float(np.mean(side * raw - cost))
    nulls = np.empty(len(seeds))
    for si, seed in enumerate(seeds):
        rng = np.random.default_rng(seed)
        side_perm = side.copy()
        for t in (0, 1, 2):
            m = np.where(thirds == t)[0]
            if m.size >= 2:
                # _derangement is fixed-point-free at index level (L-28); side VALUE collisions
                # (both long) are expected and legitimate for a +-1 label.
                side_perm[m] = side[_derangement(rng, m)]
        nulls[si] = float(np.mean(side_perm * raw - cost))
    return _summarise_null(live, nulls, n_episodes=len(episodes), plant_bps=PLANT_EXPECTANCY_BPS)


# ------------------------------------------------- path future-destroy ----


def path_future_destroy(episodes: list[dict], band_lo_ns: int, band_hi_ns: int,
                        seeds=TRIPWIRE_SEEDS) -> dict:
    """HARD tripwire (§6/§11). Pair each (entry,side) to a FOREIGN episode's future path (derange
    the raw open-to-open return within symbol x third). PASS = live does NOT survive above the
    destroyed-null p95 (no future-info leak). Bite: a +30 bps PAIRED plant must collapse into the
    unplanted-null envelope (proves the destroy removes real paired signed edge)."""
    if len(episodes) < 3:
        return {"powered": False, "n_episodes": len(episodes)}
    side = np.array([e["side"] for e in episodes], float)
    raw = np.array([e["gross_bps"] / e["side"] for e in episodes], float)
    cost = np.array([FEE_RT_BPS + e["funding_bps"] + ALLOWANCE_GOVERNING for e in episodes], float)
    entry_ts = np.array([e["entry_ts"] for e in episodes])
    thirds = _thirds(entry_ts, band_lo_ns, band_hi_ns)
    raw_plant = raw + PLANT_TRIPWIRE_BPS * side           # genuine paired +30 bps edge
    live = float(np.mean(side * raw - cost))
    live_plant = float(np.mean(side * raw_plant - cost))  # == live + 30
    nulls = np.empty(len(seeds))
    plant_nulls = np.empty(len(seeds))
    for si, seed in enumerate(seeds):
        rng = np.random.default_rng(seed)
        raw_perm = raw.copy()
        rawp_perm = raw_plant.copy()
        for t in (0, 1, 2):
            m = np.where(thirds == t)[0]
            if m.size >= 2:
                d = _derangement(rng, m)
                raw_perm[m] = raw[d]
                rawp_perm[m] = raw_plant[d]
        nulls[si] = float(np.mean(side * raw_perm - cost))
        plant_nulls[si] = float(np.mean(side * rawp_perm - cost))
    p5, p95 = float(np.percentile(nulls, 5)), float(np.percentile(nulls, 95))
    summ = _summarise_null(live, nulls, n_episodes=len(episodes))
    plant_median = float(np.median(plant_nulls))
    survives = bool(live > p95)
    summ.update({
        "live_plant": live_plant,
        "plant_null_median": plant_median,
        "plant_falls_in_null_envelope": bool(p5 <= plant_median <= p95),
        "live_survives_above_null_p95": survives,
        # DEV-1: INFORMATIVE only. An outcome-side destroy cannot separate a causal timing edge
        # from a leak on a mean-P&L object, so survival is a hard-style CONCERN only for a cell
        # that CLAIMS a positive edge (live>0). tripwire_pass kept for disclosure, does not gate.
        "live_positive": bool(live > 0),
        "hard_concern_positive_edge_survives": bool(survives and live > 0),
        "tripwire_pass": bool((not survives) and (p5 <= plant_median <= p95)),
        "gating": "INFORMATIVE_ONLY_DEV1",
    })
    return summ


# --------------------------------------------------- matched random ----


def build_random_cache(open_, high, low, atr, start, geoms, cap) -> dict:
    """Precompute independent-episode outcomes (exit_idx, gross) for EVERY candidate entry bar and
    BOTH sides, once per stop-geometry ``(use_stop, use_trail)`` at the clock's time ``cap`` (SAFE
    speedup, AMENDMENT-A3 note).

    These outcomes are a deterministic function of (entry bar, side, geometry, cap) — identical no
    matter which live signal is being controlled — so caching them lets MATCHED-RANDOM-ENTRY reuse
    them across every SMA period / exit-mode cell sharing the geometry instead of re-simulating
    200x per cell. Nothing causal/statistical changes: sample membership, denominators and the
    §4 exit rules are untouched; only redundant recomputation is removed.

    Returns ``{(use_stop, use_trail): {"exit_idx": (n,2) int, "gross": (n,2) float}}``; column
    0 = long, column 1 = short. Time cap is always the terminal for random episodes (no signal).
    """
    n = open_.size
    bars = np.arange(start + 1, n)
    cache: dict = {}
    for (us, ut) in geoms:
        exit_idx = np.full((n, 2), n - 1, dtype=np.int64)
        gross = np.full((n, 2), np.nan)
        for col, sd in ((0, 1), (1, -1)):
            sim = simulate_independent(open_, high, low, atr, bars,
                                       np.full(bars.size, sd), cap,
                                       use_stop=us, use_trail=ut)
            exit_idx[bars, col] = sim["exit_idx"]
            gross[bars, col] = sim["gross_bps"]
        cache[(us, ut)] = {"exit_idx": exit_idx, "gross": gross}
    return cache


def matched_random_entry(slot_start, atr, episodes, start, band_lo_ns, band_hi_ns,
                         cache_geom, block_bars=1, seeds=MATCHED_RANDOM_SEEDS) -> dict:
    """Random non-overlapping entries with the live side distribution per third and the same time
    cap (§6), drawing outcomes from the precomputed ``cache_geom`` (matching the arm's stop
    geometry). Excludes live entry bars within +-1h (``block_bars`` = bars/hour: H1=1, M15=4)
    (DISJOINT). >=200 seeds; live percentile vs seed expectancy distribution + a +20 bps bite."""
    if len(episodes) < 3:
        return {"powered": False, "n_episodes": len(episodes)}
    n = slot_start.size
    n_live = len(episodes)
    live_entry = np.array([e["entry_idx"] for e in episodes])
    live_ts = np.array([e["entry_ts"] for e in episodes])
    live_thirds = _thirds(live_ts, band_lo_ns, band_hi_ns)
    live_side = np.array([e["side"] for e in episodes], float)
    long_frac = {}
    for t in (0, 1, 2):
        mt = live_thirds == t
        long_frac[t] = float(np.mean(live_side[mt] > 0)) if mt.any() else 0.5
    ex_idx = cache_geom["exit_idx"]
    gross_c = cache_geom["gross"]
    eligible = np.zeros(n, dtype=bool)
    eligible[start + 1:] = True
    eligible &= np.isfinite(atr) & np.isfinite(gross_c[:, 0])
    eligible &= (slot_start >= band_lo_ns) & (slot_start < band_hi_ns)
    block = np.zeros(n, dtype=bool)
    for e in live_entry:
        lo = max(0, e - block_bars); hi = min(n, e + block_bars + 1)
        block[lo:hi] = True
    eligible &= ~block
    elig_idx = np.where(eligible)[0]
    if elig_idx.size < n_live:
        return {"powered": False, "n_episodes": n_live, "reason": "insufficient_eligible_bars"}
    thirds_of = _thirds(slot_start, band_lo_ns, band_hi_ns)
    lf_by_bar = np.array([long_frac[int(t)] for t in thirds_of])
    live = float(np.mean([e["partial_net_bps"] for e in episodes]))
    n_cand = int(min(elig_idx.size, max(3 * n_live, 1000)))
    nulls = np.empty(len(seeds))
    for si, seed in enumerate(seeds):
        rng = np.random.default_rng(seed)
        cand = np.sort(rng.choice(elig_idx, size=n_cand, replace=False))
        cols = np.where(rng.random(cand.size) < lf_by_bar[cand], 0, 1)   # 0 long, 1 short
        c_exit = ex_idx[cand, cols]
        c_gross = gross_c[cand, cols]
        # greedy non-overlap in start order (interval scheduling), cap at n_live
        chosen_entry, chosen_exit, chosen_gross = [], [], []
        occupied_until = -1
        for p in range(cand.size):
            c0 = cand[p]
            if c0 <= occupied_until:
                continue
            chosen_entry.append(c0)
            chosen_exit.append(int(c_exit[p]))
            chosen_gross.append(c_gross[p])
            occupied_until = int(c_exit[p])
            if len(chosen_entry) >= n_live:
                break
        if len(chosen_entry) < 3:
            nulls[si] = np.nan
            continue
        c_entry_ts = slot_start[np.array(chosen_entry)]
        c_exit_ts = slot_start[np.array(chosen_exit)]
        funding = _funding_bps(c_entry_ts, c_exit_ts)
        partial = np.array(chosen_gross) - FEE_RT_BPS - funding - ALLOWANCE_GOVERNING
        nulls[si] = float(np.nanmean(partial))
    nulls = nulls[np.isfinite(nulls)]
    return _summarise_null(live, nulls, n_episodes=n_live, plant_bps=PLANT_EXPECTANCY_BPS)


# --------------------------------------------------------- summary ----


def _summarise_null(live: float, nulls: np.ndarray, n_episodes: int,
                    plant_bps: float = 0.0) -> dict:
    nulls = np.asarray(nulls, float)
    nulls = nulls[np.isfinite(nulls)]
    if nulls.size < 10:
        return {"powered": False, "n_episodes": n_episodes, "n_seeds": int(nulls.size)}
    median = float(np.median(nulls))
    p95 = float(np.percentile(nulls, 95))
    p5 = float(np.percentile(nulls, 5))
    pct = float(np.mean(nulls < live))              # live percentile vs null
    collapse = float(median / live) if live not in (0.0,) and np.isfinite(live) else float("nan")
    out = {
        "powered": True, "n_episodes": n_episodes, "n_seeds": int(nulls.size),
        "live": live, "null_median": median, "null_p5": p5, "null_p95": p95,
        "live_percentile_vs_null": pct, "collapse_median_over_live": collapse,
        "live_above_null_p95": bool(live > p95),
    }
    if plant_bps:
        # bite/MDE (§6 CONTROL blocks): a +plant_bps true edge must read EXTREME vs the null.
        plant_live = live + plant_bps
        out.update({
            "plant_bps": float(plant_bps),
            "plant_live": float(plant_live),
            "plant_detected_above_null_p95": bool(plant_live > p95),
        })
    return out


def sma_benchmark_delta(zz_stats: dict, sma_stats: dict) -> dict:
    """Δ expectancy (ZZ − SMA) with a combined-SE CI (disclosure; not a gate, §6)."""
    if not zz_stats or not sma_stats:
        return {"powered": False}
    dz = zz_stats["expectancy_partial"] - sma_stats["expectancy_partial"]
    se = float(np.sqrt(zz_stats.get("se", np.nan) ** 2 + sma_stats.get("se", np.nan) ** 2))
    return {
        "powered": True,
        "zz_expectancy": zz_stats["expectancy_partial"],
        "sma_expectancy": sma_stats["expectancy_partial"],
        "delta_zz_minus_sma": float(dz),
        "delta_se": se,
        "delta_ci_low": float(dz - 1.96 * se) if np.isfinite(se) else float("nan"),
        "delta_ci_high": float(dz + 1.96 * se) if np.isfinite(se) else float("nan"),
    }
