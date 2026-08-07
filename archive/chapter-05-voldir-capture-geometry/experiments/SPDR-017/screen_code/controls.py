"""Controls + informative tripwire (design §4)."""
from __future__ import annotations

import numpy as np

from config import (
    CONTROL_PRIMARY_CELL,
    FEATURE_SHUFFLE_SEEDS,
    MATCHED_RANDOM_SEEDS,
    PLANT_BPS,
    TIME_SHUFFLE_SEEDS,
    TRIPWIRE_SEEDS,
)
from engine import residual_r_h, run_cell, simulate_policy
from prepare import SeriesPack


def _derangement(rng: np.random.Generator, n: int) -> np.ndarray:
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


def _primary_kwargs() -> dict:
    c = CONTROL_PRIMARY_CELL
    return dict(
        source=c["source"], z=c["z"], H=c["H"], event_type=c["event"],
        h=c["h"], ablation=c["ablation"], model=c["model"],
    )


def uncond_band_control(pack: SeriesPack, band: str = "DESIGN") -> dict:
    kw = _primary_kwargs()
    live_z, live_e, live_p = run_cell(pack, band=band, policy="P-NONE", **kw)
    unc_z, unc_e, unc_p = run_cell(pack, band=band, policy="P-NONE", uncond=True, **kw)
    live_s = _summarise_r(live_p)
    unc_s = _summarise_r(unc_p)
    n_orig_l = max(1, len(live_z))
    n_orig_u = max(1, len(unc_z))
    p_ev_l = sum(1 for e in live_e if e["event"] == 1) / n_orig_l
    p_ev_u = sum(1 for e in unc_e if e["event"] == 1) / n_orig_u
    return {
        "control": "UNCOND-BAND",
        "symbol": pack.symbol,
        "band": band,
        "cell": CONTROL_PRIMARY_CELL,
        "live": live_s | {"p_event": p_ev_l, "n_origins": len(live_z)},
        "control_arm": unc_s | {"p_event": p_ev_u, "n_origins": len(unc_z)},
        "delta_mean_r_h": (
            live_s["mean_r_h"] - unc_s["mean_r_h"]
            if np.isfinite(live_s["mean_r_h"]) and np.isfinite(unc_s["mean_r_h"])
            else float("nan")
        ),
        "delta_p_event": p_ev_l - p_ev_u,
        "class": "within_sample_attribution",
    }


def level_only_zvol_control(pack: SeriesPack, band: str = "DESIGN") -> dict:
    """LEVEL-ONLY = 014 Z-VOL recipe at same z,H,E-TOUCH (informative baseline)."""
    c = CONTROL_PRIMARY_CELL
    live_z, live_e, live_p = run_cell(
        pack, source="M-ZONE", z=c["z"], H=c["H"], event_type=c["event"],
        h=c["h"], band=band, policy="P-NONE",
        ablation=c["ablation"], model=c["model"],
    )
    bas_z, bas_e, bas_p = run_cell(
        pack, source="Z-VOL", z=c["z"], H=c["H"], event_type=c["event"],
        h=c["h"], band=band, policy="P-NONE",
    )
    live_s = _summarise_r(live_p)
    bas_s = _summarise_r(bas_p)
    return {
        "control": "LEVEL-ONLY-ZVOL",
        "symbol": pack.symbol,
        "band": band,
        "cell": c,
        "live": live_s,
        "control_arm": bas_s,
        "delta_mean_r_h": (
            live_s["mean_r_h"] - bas_s["mean_r_h"]
            if np.isfinite(live_s["mean_r_h"]) and np.isfinite(bas_s["mean_r_h"])
            else float("nan")
        ),
        "class": "within_sample_attribution",
        "note": "014 Z-VOL baseline — informative, not a start gate",
    }


def time_shuffle_event(pack: SeriesPack, band: str = "DESIGN") -> dict:
    c = CONTROL_PRIMARY_CELL
    kw = _primary_kwargs()
    _, live_e, live_p = run_cell(pack, band=band, policy="P-NONE", **kw)
    live_s = _summarise_r(live_p)
    decided = [e for e in live_e if e["event"] == 1 and e["side"] != 0 and e["event_idx"] >= 0]
    if band == "DESIGN":
        lo, hi = pack.design_lo, pack.design_hi
    else:
        lo, hi = pack.design_hi, pack.confirm_hi
    span = max(1, hi - lo)
    null_means = []
    for seed in TIME_SHUFFLE_SEEDS:
        rng = np.random.default_rng(seed)
        rvals = []
        for third in (0, 1, 2):
            pool = [e for e in decided
                    if int(((e["event_idx"] - lo) / span) * 3) == third]
            if len(pool) < 2:
                continue
            idxs = np.array([e["event_idx"] for e in pool])
            sides = np.array([e["side"] for e in pool])
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
    return {
        "control": "TIME-SHUFFLE-EVENT",
        "symbol": pack.symbol,
        "band": band,
        "cell": c,
        "live_mean_r_h": live_mean,
        "null_mean_mean": float(np.mean(null_means)) if null_means.size else float("nan"),
        "null_p95": float(np.quantile(null_means, 0.95)) if null_means.size else float("nan"),
        "live_percentile": pct,
        "n_seeds": int(null_means.size),
        "destroy_form": "DERANGEMENT",
        "class": "within_sample_attribution",
    }


def matched_random_anchor(pack: SeriesPack, band: str = "DESIGN") -> dict:
    c = CONTROL_PRIMARY_CELL
    kw = _primary_kwargs()
    _, _, live_p = run_cell(pack, band=band, policy="P-NONE", **kw)
    live_s = _summarise_r(live_p)
    n_live = max(1, live_s["n"])
    if band == "DESIGN":
        lo, hi = pack.design_lo, pack.design_hi
    else:
        lo, hi = pack.design_hi, pack.confirm_hi
    live_event_idx = {int(p["entry_idx"]) - 1 for p in live_p if np.isfinite(p.get("r_h", np.nan))}
    excluded_pseudo = set()
    for ev in live_event_idx:
        excluded_pseudo.update((ev - 1, ev, ev + 1))
    null_means = []
    H, h = c["H"], c["h"]
    candidates = [t0 for t0 in range(lo, max(lo, hi - H - h - 2))
                  if (t0 + H) not in excluded_pseudo]
    for seed in MATCHED_RANDOM_SEEDS:
        rng = np.random.default_rng(seed)
        rvals = []
        if len(candidates) < 5:
            continue
        chosen = rng.choice(candidates, size=min(n_live, len(candidates)), replace=False)
        for t0 in chosen:
            side = int(rng.choice([-1, 1]))
            res = residual_r_h(pack, int(t0 + H), side, h)
            if res is not None:
                rvals.append(res["r_h"])
        if rvals:
            null_means.append(float(np.mean(rvals)))
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


def feature_shuffle_control(pack: SeriesPack, band: str = "DESIGN") -> dict:
    """Permute ŷ assignment within band (model skill destroy)."""
    c = CONTROL_PRIMARY_CELL
    kw = _primary_kwargs()
    _, _, live_p = run_cell(pack, band=band, policy="P-NONE", **kw)
    live_s = _summarise_r(live_p)
    if band == "DESIGN":
        lo, hi = pack.design_lo, pack.design_hi
    else:
        lo, hi = pack.design_hi, pack.confirm_hi
    n = pack.open.size
    null_means = []
    for seed in FEATURE_SHUFFLE_SEEDS:
        rng = np.random.default_rng(seed)
        perm = np.arange(n)
        band_idx = np.arange(lo, hi)
        if band_idx.size < 2:
            continue
        shuf = band_idx.copy()
        rng.shuffle(shuf)
        perm[band_idx] = shuf
        _, _, null_p = run_cell(
            pack, band=band, policy="P-NONE", feature_shuffle_perm=perm, **kw,
        )
        ns = _summarise_r(null_p)
        if ns["n"] > 0 and np.isfinite(ns["mean_r_h"]):
            null_means.append(ns["mean_r_h"])
    null_means = np.array(null_means, float)
    live_mean = live_s["mean_r_h"]
    return {
        "control": "FEATURE-SHUFFLE",
        "symbol": pack.symbol,
        "band": band,
        "cell": c,
        "live_mean_r_h": live_mean,
        "null_mean_mean": float(np.mean(null_means)) if null_means.size else float("nan"),
        "null_p95": float(np.quantile(null_means, 0.95)) if null_means.size else float("nan"),
        "live_percentile": (
            float((null_means < live_mean).mean())
            if null_means.size and np.isfinite(live_mean) else float("nan")
        ),
        "n_seeds": int(null_means.size),
        "class": "model_skill",
    }


def path_future_destroy(pack: SeriesPack, money_posts: list[dict], band: str = "DESIGN") -> dict:
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
                continue
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
        "integrity_concern": above,
        "destroy_form": "DERANGEMENT_CAUSAL_PATH_REPAIR",
        "class": "INFORMATIVE",
        "note": "T1 informative path-destroy; residual HARD only on positive money survivors",
        "plant_bps_ref": PLANT_BPS,
    }
