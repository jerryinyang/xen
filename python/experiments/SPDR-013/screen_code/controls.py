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
    summ.update({
        "live_plant": live_plant,
        "plant_null_median": plant_median,
        "plant_falls_in_null_envelope": bool(p5 <= plant_median <= p95),
        "live_survives_above_null_p95": bool(live > p95),
        "tripwire_pass": bool((live <= p95) and (p5 <= plant_median <= p95)),
    })
    return summ


# --------------------------------------------------- matched random ----


def matched_random_entry(open_, high, low, atr, slot_start, episodes, cap,
                         start, band_lo_ns, band_hi_ns, block_bars=1,
                         seeds=MATCHED_RANDOM_SEEDS) -> dict:
    """Random non-overlapping entries with the live side distribution per third and the same
    time cap (§6). Full §4 capture geometry via the batch engine. Excludes live entry bars
    within +-1h (``block_bars`` = bars per hour on this clock: H1=1, M15=4) (DISJOINT).
    >=200 seeds, live percentile vs seed expectancy distribution."""
    if len(episodes) < 3:
        return {"powered": False, "n_episodes": len(episodes)}
    n = open_.size
    n_live = len(episodes)
    live_entry = np.array([e["entry_idx"] for e in episodes])
    live_ts = np.array([e["entry_ts"] for e in episodes])
    live_thirds = _thirds(live_ts, band_lo_ns, band_hi_ns)
    live_side = np.array([e["side"] for e in episodes], float)
    # per-third long fraction
    long_frac = {}
    for t in (0, 1, 2):
        mt = live_thirds == t
        long_frac[t] = float(np.mean(live_side[mt] > 0)) if mt.any() else 0.5
    # eligible entry bars: valid ATR, inside band, not within +-1 bar of a live entry
    eligible = np.zeros(n, dtype=bool)
    eligible[start + 1:] = True
    eligible &= np.isfinite(atr)
    ts = slot_start
    eligible &= (ts >= band_lo_ns) & (ts < band_hi_ns)
    block = np.zeros(n, dtype=bool)
    for e in live_entry:
        lo = max(0, e - block_bars); hi = min(n, e + block_bars + 1)
        block[lo:hi] = True
    eligible &= ~block
    elig_idx = np.where(eligible)[0]
    if elig_idx.size < n_live:
        return {"powered": False, "n_episodes": n_live, "reason": "insufficient_eligible_bars"}
    thirds_of = _thirds(ts, band_lo_ns, band_hi_ns)
    live = float(np.mean([e["partial_net_bps"] for e in episodes]))
    # bound the candidate pool: enough random draws to greedily fill ~n_live non-overlapping
    # episodes without simulating every eligible bar (M15 cells have tens of thousands).
    n_cand = int(min(elig_idx.size, max(4 * n_live, 1000)))
    lf_by_bar = np.array([long_frac[int(t)] for t in thirds_of])   # per-bar long prob (precomputed)
    nulls = np.empty(len(seeds))
    for si, seed in enumerate(seeds):
        rng = np.random.default_rng(seed)
        cand = rng.choice(elig_idx, size=n_cand, replace=False)
        cand.sort()
        sides = np.where(rng.random(cand.size) < lf_by_bar[cand], 1, -1)
        sim = simulate_independent(open_, high, low, atr, cand, sides, cap)
        # greedy non-overlap in entry order, cap at n_live
        order = np.argsort(cand)
        chosen, occupied_until = [], -1
        for oi in order:
            e0 = cand[oi]
            if e0 <= occupied_until or not sim["valid"][oi]:
                continue
            chosen.append(oi)
            occupied_until = int(sim["exit_idx"][oi])
            if len(chosen) >= n_live:
                break
        chosen = np.array(chosen, int)
        if chosen.size < 3:
            nulls[si] = np.nan
            continue
        c_entry_ts = ts[cand[chosen]]
        c_exit_ts = ts[sim["exit_idx"][chosen]]
        funding = _funding_bps(c_entry_ts, c_exit_ts)
        partial = sim["gross_bps"][chosen] - FEE_RT_BPS - funding - ALLOWANCE_GOVERNING
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
