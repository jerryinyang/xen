"""Controls (design §6). Exit-matched derangements, matched comparator, plant curves.

The §6.1 leak tripwires live in ``tripwires.py`` — they run against the live pipeline and
need panel access, which these pure-array controls deliberately do not.
"""
from __future__ import annotations

import numpy as np

from config import (
    DERANGE_SEEDS,
    MAGMATCH_DECILES,
    MAGMATCH_SEEDS,
    PLANT_CURVE_BPS,
    TIMING_SEEDS,
)
from metrics import log_R_from_pWL


def _logR(r: np.ndarray) -> float:
    r = np.asarray(r, dtype=float)
    r = r[np.isfinite(r)]
    if r.size == 0:
        return float("nan")
    pos = r[r > 0]
    neg = r[r < 0]
    if pos.size == 0 or neg.size == 0:
        return float("nan")
    p = pos.size / (pos.size + neg.size)
    W = float(pos.mean())
    L = float((-neg).mean())
    return log_R_from_pWL(p, W, L)


def derange_indices(n: int, rng: np.random.Generator, *, max_tries: int = 50) -> np.ndarray:
    """A permutation of ``range(n)`` with ZERO fixed points (L-28), redrawn per seed."""
    if n < 2:
        return np.arange(n)
    ident = np.arange(n)
    for _ in range(max_tries):
        perm = rng.permutation(n)
        if not np.any(perm == ident):
            return perm
    # deterministic repair: rotate the remaining fixed points onto each other
    perm = rng.permutation(n)
    fixed = np.where(perm == ident)[0]
    if fixed.size:
        perm[fixed] = perm[np.roll(fixed, 1)]
    return perm


def _null_summary(nulls: np.ndarray, live: float) -> dict:
    nulls = np.asarray(nulls, dtype=float)
    nulls = nulls[np.isfinite(nulls)]
    return {
        "live_log_R": live,
        "null_mean": float(nulls.mean()) if nulls.size else float("nan"),
        "null_sd": float(nulls.std(ddof=1)) if nulls.size > 1 else float("nan"),
        "null_q05": float(np.quantile(nulls, 0.05)) if nulls.size else float("nan"),
        "null_q50": float(np.quantile(nulls, 0.50)) if nulls.size else float("nan"),
        "null_q95": float(np.quantile(nulls, 0.95)) if nulls.size else float("nan"),
        "n_null_draws": int(nulls.size),
        "n_distinct_null_values": int(np.unique(np.round(nulls, 12)).size),
        # internal: the raw draws, consumed by plant_curve. Keys starting with "_" are
        # stripped before controls.json is written.
        "_null_draws": nulls,
        "percentile": (
            float(np.mean(nulls < live)) if nulls.size and np.isfinite(live) else float("nan")
        ),
        "collapse_fraction": (
            float(np.median(nulls) / live)
            if nulls.size and np.isfinite(live) and live != 0 else float("nan")
        ),
        "collapse_fraction_status": "DISCLOSURE_ONLY",
    }


def side_derangement(
    r: np.ndarray,
    r_flip: np.ndarray,
    side: np.ndarray,
    *,
    exit_matched_method: np.ndarray | None = None,
    n_seeds: int = 2000,
) -> dict:
    """§6 CONTROL SIDE-DERANGEMENT, exit-matched on every arm.

    The side LABELS are deranged across episodes by a permutation with zero fixed points; an
    episode whose deranged label differs from its own takes its EXIT-MATCHED flipped payoff
    ``r_flip`` — which the engine produced by rebuilding the barrier on the flipped side and
    RE-RESOLVING the exit from M1 (§6 EXIT-MATCHING). Where the arm is time-exit the flipped
    payoff is the negation of the same exit, and §12 asserts that equality per arm.

    A previous form multiplied every side by −1 on every seed, so 2,000 seeds produced one
    distinct value and the percentile could only be 0.0 or 1.0 (QA run 8, R8-05). Deranging
    the labels leaves each seed's mix of flipped and unflipped episodes random, which is what
    gives the null its spread.
    """
    r = np.asarray(r, dtype=float)
    r_flip = np.asarray(r_flip, dtype=float)
    side = np.asarray(side, dtype=float)
    live = _logR(r)
    n = r.size
    nulls = []
    fixed_max = 0
    flipped_fracs = []
    seeds = DERANGE_SEEDS[:n_seeds]
    for sd in seeds:
        rng = np.random.default_rng(sd)
        perm = derange_indices(n, rng)
        fixed_max = max(fixed_max, int(np.sum(perm == np.arange(n))))
        flipped = side[perm] != side
        flipped_fracs.append(float(np.mean(flipped)) if n else float("nan"))
        r_d = np.where(flipped, r_flip, r)
        nulls.append(_logR(r_d))
    out = _null_summary(np.asarray(nulls, dtype=float), live)
    methods = (
        sorted({str(m) for m in exit_matched_method}) if exit_matched_method is not None else []
    )
    ff = np.asarray(flipped_fracs, dtype=float)
    ff = ff[np.isfinite(ff)]
    out.update({
        "fixed_point_count": fixed_max,
        "fixed_point_count_measured": True,
        # AMENDMENT-19(a) / R9-14: destruction strength is the flipped fraction, not the
        # permutation fixed-point count (which is 0 by construction)
        "flipped_fraction_mean": float(ff.mean()) if ff.size else float("nan"),
        "flipped_fraction_sd": float(ff.std(ddof=1)) if ff.size > 1 else float("nan"),
        "flipped_fraction_min": float(ff.min()) if ff.size else float("nan"),
        "flipped_fraction_max": float(ff.max()) if ff.size else float("nan"),
        "n_seeds": int(len(seeds)),
        "method": "side_label_derangement_exit_matched",
        "exit_matched_methods_present": methods,
        "n_reresolved_flips_available": int(np.isfinite(r_flip).sum()),
    })
    return out


def entry_timing_derangement(
    r: np.ndarray,
    symbol: np.ndarray,
    hold_hours: np.ndarray,
    side: np.ndarray,
    *,
    n_seeds: int = 2000,
) -> dict:
    """§6 CONTROL ENTRY-TIMING DERANGEMENT: entry timestamps deranged WITHIN symbol.

    Exact for a CONSTANT-hold time-exit arm, which is what it is run on, and the constancy is
    asserted rather than assumed. Writing ``r = side · ambient(t, h)``, re-timing episode ``i``
    to episode ``j``'s entry while keeping ``i``'s side and hold gives

        r_deranged[i] = side[i] · ambient(t_j, h) = side[i] · side[j] · r[j]

    so the ambient return realised over the DONOR's window is what is scored, under the
    RECEIVER's side. A previous form instead took ``|r[j]| · sign(side[i]) · sign(r[j])``,
    which preserves the donor's own realised sign and is the EXP-012 trap — permuted realised
    P&L cannot destroy the alignment the control exists to break (QA run 8, R8-07).
    """
    r = np.asarray(r, dtype=float)
    side = np.asarray(side, dtype=float)
    holds = np.asarray(hold_hours, dtype=float)
    live = _logR(r)
    finite_h = holds[np.isfinite(holds)]
    if finite_h.size and float(np.ptp(finite_h)) > 1e-9:
        return {
            "live_log_R": live,
            "status": "NOT_APPLICABLE_VARIABLE_HOLD",
            "reason": (
                "re-timing is exact only at a constant holding length; this arm's holds vary, "
                "so the control is demoted to DISCLOSURE rather than run approximately (§6)"
            ),
            "hold_hours_min": float(finite_h.min()),
            "hold_hours_max": float(finite_h.max()),
            "n_seeds": 0,
            "method": "within_symbol_timing_derange",
        }
    n = r.size
    nulls = []
    fixed_max = 0
    sym_index = {s: np.where(symbol == s)[0] for s in np.unique(symbol)}
    seeds = TIMING_SEEDS[:n_seeds]
    for sd in seeds:
        rng = np.random.default_rng(sd)
        r_d = np.full(n, np.nan)
        fixed = 0
        for idx in sym_index.values():
            if idx.size < 2:
                # a lone episode cannot be re-timed within its own symbol; it is dropped from
                # the null rather than left in place, which would be a fixed point
                continue
            perm = derange_indices(idx.size, rng)
            fixed += int(np.sum(perm == np.arange(idx.size)))
            donor = idx[perm]
            r_d[idx] = np.sign(side[idx]) * np.sign(side[donor]) * r[donor]
        fixed_max = max(fixed_max, fixed)
        nulls.append(_logR(r_d))
    out = _null_summary(np.asarray(nulls, dtype=float), live)
    out.update({
        "fixed_point_count": fixed_max,
        "fixed_point_count_measured": True,
        "n_seeds": int(len(seeds)),
        "n_symbols_used": int(sum(1 for v in sym_index.values() if v.size >= 2)),
        "n_episodes_dropped_singleton_symbol": int(
            sum(v.size for v in sym_index.values() if v.size < 2)
        ),
        "method": "within_symbol_timing_derange",
        "exit_matched": True,
        "exit_matched_reason": "constant-hold time-exit arm; asserted above",
        "hold_hours": float(finite_h[0]) if finite_h.size else float("nan"),
    })
    return out


def magnitude_matched_comparator(
    selected_r: np.ndarray,
    selected_decile: np.ndarray,
    complement_r: np.ndarray,
    complement_decile: np.ndarray,
    *,
    sigma_hat: float,
    n_seeds: int = 2000,
) -> dict:
    """M-3: match the complement on |decision-bar move| decile (§6, MANDATORY for L1 and L3).

    ``*_decile`` must be the per-symbol expanding causal decile of ``abs_r_decision_bps``.
    Matching on the LAYER'S OWN selection variable (the ŝ decile) makes the complement pool
    empty at exactly the deciles that have demand, and the comparator returns all-NaN — which
    is what shipped (QA run 8, R8-14).

    §6 refuses a bare percentile: the comparator's own mean, its null quantiles AND its plant
    curve are emitted, per P-24, along with the per-decile disjointness and collapse fraction.
    """
    selected_r = np.asarray(selected_r, dtype=float)
    selected_decile = np.asarray(selected_decile, dtype=float)
    complement_r = np.asarray(complement_r, dtype=float)
    complement_decile = np.asarray(complement_decile, dtype=float)
    live = _logR(selected_r)
    nulls = []
    per_decile = {}
    seeds = MAGMATCH_SEEDS[:n_seeds]
    for d in range(1, MAGMATCH_DECILES + 1):
        n_need = int(np.sum(selected_decile == d))
        pool = complement_r[(complement_decile == d) & np.isfinite(complement_r)]
        per_decile[str(d)] = {
            "n_selected": n_need,
            "n_complement_available": int(pool.size),
            "matched": bool(n_need > 0 and pool.size > 0),
            "with_replacement": bool(n_need > 0 and 0 < pool.size < n_need),
        }
    unmatched = [d for d, v in per_decile.items() if v["n_selected"] > 0 and not v["matched"]]
    for sd in seeds:
        rng = np.random.default_rng(sd)
        draws = []
        for d in range(1, MAGMATCH_DECILES + 1):
            n_need = int(np.sum(selected_decile == d))
            pool = complement_r[(complement_decile == d) & np.isfinite(complement_r)]
            if n_need == 0 or pool.size == 0:
                continue
            draws.append(rng.choice(pool, size=n_need, replace=(pool.size < n_need)))
        nulls.append(_logR(np.concatenate(draws)) if draws else float("nan"))
    arr = np.asarray(nulls, dtype=float)
    out = _null_summary(arr, live)
    out.update({
        "n_seeds": int(len(seeds)),
        "matched_on": "abs_r_decision_bps decile (per-symbol expanding causal, §4.1b)",
        "disjoint": True,
        "disjointness_note": "complement is the layer's excluded set; disjoint by construction",
        "per_decile": per_decile,
        "deciles_with_demand_unmatched": sorted(unmatched),
        "n_selected": int(np.isfinite(selected_r).sum()),
        "n_complement": int(np.isfinite(complement_r).sum()),
        "method": "magnitude_matched_decile",
        # §6: "a percentile alone is uninterpretable and is refused"
        "plant_curve": plant_curve(
            selected_r, arr[np.isfinite(arr)], sigma_hat=sigma_hat
        ),
    })
    return out


def plant_curve(
    r: np.ndarray,
    nulls: np.ndarray,
    *,
    sigma_hat: float,
    r_flip: np.ndarray | None = None,
    side: np.ndarray | None = None,
) -> dict:
    """§6 plant curve: detection RATE against the control's OWN null, per rung.

    The plant is added to a NULL-EQUIVALENT series, not the live series (R9-06). Planting onto
    the live series saturates every rung at 1.0 whenever the live value already sits near
    percentile 1.0, which makes the UNUSABLE clause inoperable.

    Preferred base (when ``r_flip`` and ``side`` are supplied): one deterministic exit-matched
    side-derangement draw — the same null the control draws from. Fallback: a half-flip of
    ``r``. Either way the curve should rise from near α at the finest rung.

    Rungs are also stated in σ̂ units, re-derived from the run-measured pooled σ̂ (L-50/P-21).
    """
    r = np.asarray(r, dtype=float)
    nulls = np.asarray(nulls, dtype=float)
    nulls = nulls[np.isfinite(nulls)]
    live = _logR(r)
    rng = np.random.default_rng(0xA19C0DE)
    if r_flip is not None and side is not None and r.size >= 2:
        rf = np.asarray(r_flip, dtype=float)
        sd = np.asarray(side, dtype=float)
        perm = derange_indices(r.size, rng)
        flipped = sd[perm] != sd
        r_base = np.where(flipped, rf, r)
        base_name = "null_equivalent_one_derange_draw"
    else:
        flip = rng.random(r.size) < 0.5
        r_base = np.where(flip, -r, r)
        base_name = "null_equivalent_half_flip"
    base_log_R = _logR(r_base)
    out = {
        "sigma_hat_bps": float(sigma_hat),
        "rungs_bps": list(PLANT_CURVE_BPS),
        "n_null_draws": int(nulls.size),
        "detection": {},
        "live_log_R": live,
        "plant_base": base_name,
        "plant_base_log_R": base_log_R,
    }
    for bps in PLANT_CURVE_BPS:
        lp = _logR(r_base + bps)
        rate = (
            float(np.mean(nulls < lp))
            if nulls.size and np.isfinite(lp) else float("nan")
        )
        out["detection"][str(bps)] = {
            "planted_log_R": lp,
            "detection_rate_vs_null": rate,
            "sigma_units": float(bps / sigma_hat) if sigma_hat > 0 else float("nan"),
        }
    return out
