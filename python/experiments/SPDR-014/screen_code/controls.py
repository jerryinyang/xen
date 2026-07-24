"""Controls + informative tripwire (design §7)."""
from __future__ import annotations

import numpy as np

from config import (
    CONTROL_PRIMARY_CELL,
    GATE_SHUFFLE_SEEDS,
    MATCHED_RANDOM_SEEDS,
    PLANT_BPS,
    TIME_SHUFFLE_SEEDS,
    TRIPWIRE_SEEDS,
)
from engine import SeriesPack, residual_r_h, run_cell, simulate_policy


def _derangement(rng: np.random.Generator, n: int) -> np.ndarray:
    """Permutation of range(n) with zero fixed points (perm[i] != i for all i).

    Rejection sampling: redraw a full permutation until it has no fixed point.
    P(derangement) → 1/e, so ~e draws in expectation regardless of n; always
    terminates (independent draws). For n < 2 a derangement is impossible;
    return identity (caller must guard singleton pools).
    """
    if n < 2:
        return np.arange(n)
    idx = np.arange(n)
    while True:
        perm = rng.permutation(n)
        if not np.any(perm == idx):
            return perm


def _third_of(idx: int, lo: int, span: int) -> int:
    return int(min(2, max(0, int(((idx - lo) / span) * 3))))


def _summarise_r(posts: list[dict]) -> dict:
    r = np.array([p["r_h"] for p in posts if np.isfinite(p.get("r_h", np.nan))], float)
    if r.size == 0:
        return {"n": 0, "mean_r_h": float("nan"), "median_r_h": float("nan"),
                "p_momo": float("nan"), "p_mr": float("nan")}
    return {
        "n": int(r.size),
        "mean_r_h": float(r.mean()),
        "median_r_h": float(np.median(r)),
        "p_momo": float(np.mean([p["label"] == "MOMO" for p in posts])),
        "p_mr": float(np.mean([p["label"] == "MR" for p in posts])),
    }


def uncond_band_control(pack: SeriesPack, band: str = "DESIGN") -> dict:
    c = CONTROL_PRIMARY_CELL
    live_z, live_e, live_p = run_cell(
        pack, source=c["source"], z=c["z"], H=c["H"], event_type=c["event"],
        h=c["h"], band=band, policy="P-NONE",
    )
    unc_z, unc_e, unc_p = run_cell(
        pack, source=c["source"], z=c["z"], H=c["H"], event_type=c["event"],
        h=c["h"], band=band, policy="P-NONE", uncond=True,
    )
    live_s = _summarise_r(live_p)
    unc_s = _summarise_r(unc_p)
    n_orig_l = max(1, len(live_z))
    n_orig_u = max(1, len(unc_z))
    p_ev_l = sum(1 for e in live_e if e["event"] == 1) / n_orig_l
    p_ev_u = sum(1 for e in unc_e if e["event"] == 1) / n_orig_u
    plant = live_s["mean_r_h"] + PLANT_BPS if np.isfinite(live_s["mean_r_h"]) else float("nan")
    return {
        "control": "UNCOND-BAND",
        "symbol": pack.symbol,
        "band": band,
        "cell": c,
        "live": live_s | {"p_event": p_ev_l, "n_origins": len(live_z)},
        "control_arm": unc_s | {"p_event": p_ev_u, "n_origins": len(unc_z)},
        "delta_mean_r_h": (
            live_s["mean_r_h"] - unc_s["mean_r_h"]
            if np.isfinite(live_s["mean_r_h"]) and np.isfinite(unc_s["mean_r_h"])
            else float("nan")
        ),
        "delta_p_event": p_ev_l - p_ev_u,
        "collapse": (
            unc_s["mean_r_h"] / live_s["mean_r_h"]
            if np.isfinite(live_s["mean_r_h"]) and abs(live_s["mean_r_h"]) > 1e-9
            else float("nan")
        ),
        "plant_mean": plant,
        "class": "within_sample_attribution",
    }


def time_shuffle_event(pack: SeriesPack, band: str = "DESIGN") -> dict:
    """Derange event timestamps within symbol×calendar-third; re-measure r_h."""
    c = CONTROL_PRIMARY_CELL
    _, live_e, live_p = run_cell(
        pack, source=c["source"], z=c["z"], H=c["H"], event_type=c["event"],
        h=c["h"], band=band, policy="P-NONE",
    )
    live_s = _summarise_r(live_p)
    # collect decided events
    decided = [e for e in live_e if e["event"] == 1 and e["side"] != 0 and e["event_idx"] >= 0]
    if band == "DESIGN":
        lo, hi = pack.design_lo, pack.design_hi
    else:
        lo, hi = pack.design_hi, pack.confirm_hi
    span = max(1, hi - lo)
    null_means = []
    for seed in TIME_SHUFFLE_SEEDS:
        rng = np.random.default_rng(seed)
        # partition by third of event_idx
        rvals = []
        for third in (0, 1, 2):
            pool = [e for e in decided
                    if int(((e["event_idx"] - lo) / span) * 3) == third]
            if len(pool) < 2:
                continue
            idxs = np.array([e["event_idx"] for e in pool])
            sides = np.array([e["side"] for e in pool])
            # true derangement: every event's side is re-paired to a foreign path
            perm = _derangement(rng, len(pool))
            for i, e in enumerate(pool):
                foreign_idx = int(idxs[perm[i]])
                res = residual_r_h(pack, foreign_idx, int(sides[i]), c["h"])
                if res is not None:
                    rvals.append(res["r_h"])
        if rvals:
            null_means.append(float(np.mean(rvals)))
    null_means = np.array(null_means, float)
    live_mean = live_s["mean_r_h"]
    pct = float((null_means < live_mean).mean()) if null_means.size and np.isfinite(live_mean) else float("nan")
    p95 = float(np.quantile(null_means, 0.95)) if null_means.size else float("nan")
    return {
        "control": "TIME-SHUFFLE-EVENT",
        "symbol": pack.symbol,
        "band": band,
        "cell": c,
        "live_mean_r_h": live_mean,
        "null_mean_mean": float(np.mean(null_means)) if null_means.size else float("nan"),
        "null_p95": p95,
        "live_percentile": pct,
        "n_seeds": int(null_means.size),
        "collapse": (
            float(np.mean(null_means) / live_mean)
            if null_means.size and np.isfinite(live_mean) and abs(live_mean) > 1e-9
            else float("nan")
        ),
        "destroy_form": "DERANGEMENT",
        "class": "within_sample_attribution",
    }


def matched_random_anchor(pack: SeriesPack, band: str = "DESIGN") -> dict:
    """Random non-overlapping anchors; residual at random H-window ends as pseudo-events."""
    c = CONTROL_PRIMARY_CELL
    _, _, live_p = run_cell(
        pack, source=c["source"], z=c["z"], H=c["H"], event_type=c["event"],
        h=c["h"], band=band, policy="P-NONE",
    )
    live_s = _summarise_r(live_p)
    n_live = max(1, live_s["n"])
    if band == "DESIGN":
        lo, hi = pack.design_lo, pack.design_hi
    else:
        lo, hi = pack.design_hi, pack.confirm_hi
    # §7 DISJOINT: exclude live anchors ±1 H1. A live event sits at entry_idx-1;
    # the pseudo-event index below is t0+H, so drop any t0 whose t0+H lands within
    # ±1 of a live event index.
    live_event_idx = {int(p["entry_idx"]) - 1 for p in live_p if np.isfinite(p.get("r_h", np.nan))}
    excluded_pseudo = set()
    for ev in live_event_idx:
        excluded_pseudo.update((ev - 1, ev, ev + 1))
    null_means = []
    null_p_event = []
    H, h = c["H"], c["h"]
    candidates = [t0 for t0 in range(lo, max(lo, hi - H - h - 2))
                  if (t0 + H) not in excluded_pseudo]
    for seed in MATCHED_RANDOM_SEEDS:
        rng = np.random.default_rng(seed)
        # sample n_live random event-like points
        rvals = []
        if len(candidates) < 5:
            continue
        chosen = rng.choice(candidates, size=min(n_live, len(candidates)), replace=False)
        for t0 in chosen:
            # pseudo event at t0+H with random side
            side = int(rng.choice([-1, 1]))
            res = residual_r_h(pack, int(t0 + H), side, h)
            if res is not None:
                rvals.append(res["r_h"])
        if rvals:
            null_means.append(float(np.mean(rvals)))
            null_p_event.append(1.0)  # always "event" by construction for residual compare
    null_means = np.array(null_means, float)
    live_mean = live_s["mean_r_h"]
    pct = float((null_means < live_mean).mean()) if null_means.size and np.isfinite(live_mean) else float("nan")
    return {
        "control": "MATCHED-RANDOM-ANCHOR",
        "symbol": pack.symbol,
        "band": band,
        "cell": c,
        "live_mean_r_h": live_mean,
        "null_mean_mean": float(np.mean(null_means)) if null_means.size else float("nan"),
        "null_p95": float(np.quantile(null_means, 0.95)) if null_means.size else float("nan"),
        "live_percentile": pct,
        "n_seeds": int(null_means.size),
        "disjoint_excl_live_pm1": True,
        "n_candidates": int(len(candidates)),
        "class": "within_sample_attribution",
    }


def gate_label_shuffle(pack: SeriesPack, band: str = "DESIGN") -> dict:
    """Derange vol tercile labels; compare stratum residual means (non-vacuity)."""
    c = CONTROL_PRIMARY_CELL
    _, _, live_p = run_cell(
        pack, source=c["source"], z=c["z"], H=c["H"], event_type=c["event"],
        h=c["h"], band=band, policy="P-NONE",
    )
    if not live_p:
        return {"control": "GATE-LABEL-SHUFFLE", "symbol": pack.symbol, "n": 0}
    # live HIGH vol residual mean
    high = [p["r_h"] for p in live_p if p.get("vol_tercile") == "HIGH"]
    live_high = float(np.mean(high)) if high else float("nan")
    labels = np.array([p.get("vol_tercile", "NA") for p in live_p])
    r = np.array([p["r_h"] for p in live_p], float)
    n = labels.size
    nulls = []
    for seed in GATE_SHUFFLE_SEEDS:  # >=200 seed floor (§9)
        rng = np.random.default_rng(seed)
        # true derangement: every residual gets a label from a different origin
        perm = _derangement(rng, n)
        shuf = labels[perm]
        m = shuf == "HIGH"
        if m.any():
            nulls.append(float(np.mean(r[m])))
    nulls = np.array(nulls, float)
    return {
        "control": "GATE-LABEL-SHUFFLE",
        "symbol": pack.symbol,
        "band": band,
        "live_high_mean_r_h": live_high,
        "null_mean": float(np.mean(nulls)) if nulls.size else float("nan"),
        "live_percentile": (
            float((nulls < live_high).mean())
            if nulls.size and np.isfinite(live_high) else float("nan")
        ),
        "destroy_form": "DERANGEMENT",
        "class": "within_sample_attribution",
    }


def path_future_destroy(pack: SeriesPack, money_posts: list[dict], band: str = "DESIGN") -> dict:
    """T1 informative tripwire on money partial_net; HARD concern if positive survivor above p95.

    Design §7: derange future-path pairing within symbol×third. Each live trade keeps its
    own decision (trade_side, hold h) but is re-paired to a *foreign* entry drawn as a
    within-third derangement; partial_net is recomputed causally via simulate_policy on that
    foreign path. Shuffling realized P&L (EXP-012) cannot collapse a mean stat — this re-pairs
    the path itself, which can.
    """
    live = [
        p for p in money_posts
        if p.get("band") == band and np.isfinite(p.get("partial_net_bps", np.nan))
        and p.get("trade_side", 0) != 0
    ]
    live_vals = np.array([p["partial_net_bps"] for p in live], float)
    live_mean = float(live_vals.mean()) if live_vals.size else float("nan")
    if band == "DESIGN":
        lo, hi = pack.design_lo, pack.design_hi
    else:
        lo, hi = pack.design_hi, pack.confirm_hi
    span = max(1, hi - lo)
    # group live trades by third of their entry index
    thirds: dict[int, list[dict]] = {0: [], 1: [], 2: []}
    for p in live:
        thirds[_third_of(int(p["entry_idx"]), lo, span)].append(p)
    nulls = []
    for seed in TRIPWIRE_SEEDS:
        rng = np.random.default_rng(seed)
        vals = []
        for pool in thirds.values():
            m = len(pool)
            if m < 2:
                continue  # cannot derange a singleton third
            perm = _derangement(rng, m)
            entries = np.array([int(pool[j]["entry_idx"]) for j in range(m)])
            for i, p in enumerate(pool):
                foreign_entry = int(entries[perm[i]])
                mon = simulate_policy(pack, foreign_entry, int(p["trade_side"]), int(p["h"]))
                if mon is not None:
                    vals.append(mon["partial_net_bps"])
        if vals:
            nulls.append(float(np.mean(vals)))
    nulls = np.array(nulls, float)
    p95 = float(np.quantile(nulls, 0.95)) if nulls.size else float("nan")
    positive = bool(np.isfinite(live_mean) and live_mean > 0)
    above = bool(positive and np.isfinite(p95) and live_mean > p95)
    return {
        "control": "PATH-FUTURE-DESTROY",
        "symbol": pack.symbol,
        "band": band,
        "live_mean_partial_net": live_mean,
        "null_p95": p95,
        "n_seeds": int(nulls.size),
        "positive_edge_claimed": positive,
        "survives_above_p95": above,
        "integrity_concern": above,  # HARD applicability only when positive
        "destroy_form": "DERANGEMENT_CAUSAL_PATH_REPAIR",
        "class": "INFORMATIVE",
        "note": "T1/DEV-1 class — informative; within-third foreign-path re-pair, "
                "partial_net recomputed causally; residual HARD only on positive money survivors",
    }
