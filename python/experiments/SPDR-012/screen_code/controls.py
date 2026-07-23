"""Controls + future-destroy tripwire (design §5).

Three controls and one tripwire, all on the V-LEVEL primary object (ridge forecast of the
next-bar ``|open->open|`` move):

* ``TIME-SHUFFLE-PREDICTORS`` — within-cell CIRCULAR SHIFT of the predictor series by
  ``U{1..n-1}``, targets fixed (200 seeds 101..300).
* ``TARGET-LABEL-DERANGEMENT`` — targets deranged inside (symbol x calendar-month) blocks
  with ZERO fixed points (L-28), predictors fixed (>=200 seeds from 31000).
* ``UNCONDITIONAL-MEAN-BASELINE`` — nested constant forecast; emitted by ``arms._forecast_rows``
  as ``dmae_vs_uncond`` / ``oos_r2_vs_uncond``.
* ``TARGET-FUTURE-DESTROY`` — REPORT LAYER (operator decision 2026-07-23, DEV-1; was framed
  as a hard tripwire). Reports whether the measurement collapses once every target is
  destroyed. It cannot detect look-ahead: destroying the outcome removes the association
  whether or not the predictor leaked. The operative non-vacuity device is the predictor-side
  CIRCULAR_SHIFT control; the no-leak claim rests on the design §7.4 construction asserts.

Both destroy controls carry the design's +0.25 rank-correlation bite plant: a synthetic
monotone predictor is planted, and the same destroy operation must remove it.
"""
from __future__ import annotations

import numpy as np
from scipy.stats import rankdata

from config import PLANT_RANK_CORR
from stats_core import spearman

# Operationalisation of design §5 "must collapse".
#
# design §5 tripwire: "live IC must not remain above null p99 IF THE METRIC IS ACAUSAL ...
# surviving IC => leak/bug". The leak signature is therefore a destroyed null that does NOT
# collapse: if the forecast secretly carried the outcome, replacing the outcomes would leave
# the IC where it was. The HARD check is accordingly run on the FULL destruction — an
# unrestricted derangement of every target — whose null must sit at zero.
#
# The design's pinned block form (derange inside symbol x calendar-month) is strictly WEAKER
# as a destroy: it cannot remove the BETWEEN-month component of the association, so its null
# is not centred at zero by construction and its median rises with the strength of the true
# relationship. It is therefore adjudicated as what design §5 declares it to be — the CONTROL
# "is reported skill an artifact of target marginals only?", read in the direction the design
# states ("live IC above null p95") — and never as a leak verdict. Both are reported per cell.
# Thresholds are expressed in units of the destroyed null's OWN dispersion, so no bespoke
# IC constant is asserted (QA F-3 / L-24 F06). Both are the conventional 3-sigma bar:
#   z_zero = |median(null)| / sd(null)          -> the destroyed centre must sit at zero
#   z_live = (live - median(null)) / sd(null)   -> ... and far from the live value
TRIPWIRE_Z = 3.0


def _month_blocks(dates: np.ndarray) -> list[np.ndarray]:
    """Contiguous calendar-month blocks of row indices; singleton blocks merged backwards."""
    days = dates.astype(np.int64)
    z = days + 719468
    era = np.where(z >= 0, z, z - 146096) // 146097
    doe = z - era * 146097
    yoe = (doe - doe // 1460 + doe // 36524 - doe // 146096) // 365
    y = yoe + era * 400
    doy = doe - (365 * yoe + yoe // 4 - yoe // 100)
    mp = (5 * doy + 2) // 153
    mth = np.where(mp < 10, mp + 3, mp - 9)
    y = np.where(mth <= 2, y + 1, y)
    key = y * 12 + mth

    blocks: list[np.ndarray] = []
    for k in np.unique(key):
        blocks.append(np.flatnonzero(key == k))
    merged: list[np.ndarray] = []
    for b in blocks:
        if b.size < 2 and merged:
            merged[-1] = np.concatenate([merged[-1], b])
        else:
            merged.append(b)
    return [b for b in merged if b.size >= 2]


def derange(n: int, rng: np.random.Generator) -> np.ndarray:
    """A permutation of ``range(n)`` with ZERO fixed points (L-28). ``n >= 2`` required."""
    if n < 2:
        raise ValueError("derangement requires n >= 2")
    for _ in range(64):
        p = rng.permutation(n)
        fixed = np.flatnonzero(p == np.arange(n))
        if fixed.size == 0:
            return p
        if fixed.size == 1:
            j = int(fixed[0])
            k = int(rng.integers(0, n - 1))
            k = k if k != j else n - 1
            p[j], p[k] = p[k], p[j]
        else:
            p[fixed] = p[np.roll(fixed, 1)]
        if not np.any(p == np.arange(n)):
            return p
    raise RuntimeError("failed to construct a derangement")


def derange_within_blocks(
    y: np.ndarray, blocks: list[np.ndarray], rng
) -> tuple[np.ndarray, int]:
    """Derange ``y`` inside each block.

    Returns the deranged series and the COUNT of index-level fixed points actually observed
    (expected exactly 0). The count is reported rather than only asserted, so the integrity
    self-check measures the property instead of trusting a literal (QA F-10) — assertions are
    stripped under ``python -O``.
    """
    out = y.copy()
    n_fixed = 0
    for b in blocks:
        p = derange(b.size, rng)
        n_fixed += int(np.sum(p == np.arange(b.size)))
        out[b] = y[b][p]
    return out, n_fixed


def plant_feature(y: np.ndarray, rho: float, rng: np.random.Generator) -> np.ndarray:
    """Synthetic monotone predictor with approximately ``rho`` rank correlation to ``y``."""
    n = y.size
    z = (rankdata(y) - 0.5) / n
    g = np.vectorize(_probit)(z)
    # Gaussian-copula inverse: rho_Spearman = (6/pi)*arcsin(r/2)  =>  r = 2*sin(pi*rho/6)
    a = float(np.clip(2.0 * np.sin(np.pi * rho / 6.0), -1.0, 1.0))
    return a * g + np.sqrt(max(1.0 - a * a, 0.0)) * rng.standard_normal(n)


def _probit(p: float) -> float:
    from scipy.special import ndtri

    return float(ndtri(min(max(p, 1e-12), 1 - 1e-12)))


def _envelope(vals: np.ndarray, live: float) -> dict:
    v = vals[np.isfinite(vals)]
    if v.size == 0:
        return {"n_seeds": 0}
    out = {
        "n_seeds": int(v.size),
        "mean": float(v.mean()),
        "p1": float(np.percentile(v, 1)),
        "p5": float(np.percentile(v, 5)),
        "p50": float(np.percentile(v, 50)),
        "p95": float(np.percentile(v, 95)),
        "p99": float(np.percentile(v, 99)),
        "sd": float(v.std()),
        "live": float(live) if np.isfinite(live) else None,
    }
    out["collapse_fraction"] = (
        float(out["p50"] / live) if np.isfinite(live) and abs(live) > 1e-12 else None
    )
    out["live_above_p95"] = bool(np.isfinite(live) and live > out["p95"])
    out["live_above_p99"] = bool(np.isfinite(live) and live > out["p99"])
    out["live_inside_central_90"] = bool(
        np.isfinite(live) and out["p5"] <= live <= out["p95"]
    )
    out["one_sided_p"] = (
        float((1.0 + float((v >= live).sum())) / (1.0 + v.size)) if np.isfinite(live) else None
    )
    return out


def time_shuffle_control(pred: np.ndarray, y: np.ndarray, seeds) -> dict:
    """CIRCULAR_SHIFT of the predictor series against fixed targets (design §5)."""
    n = pred.size
    live = spearman(pred, y)
    if n < 10:
        return {"status": "UNPOWERED", "n_obs": int(n), "live": live}
    vals = np.empty(len(seeds))
    shifts = np.empty(len(seeds), dtype=np.int64)
    for i, s in enumerate(seeds):
        rng = np.random.default_rng(s)
        k = int(rng.integers(1, n))
        shifts[i] = k
        vals[i] = spearman(np.roll(pred, k), y)
    env = _envelope(vals, live)
    env |= {
        "status": "OK", "destroy_form": "CIRCULAR_SHIFT", "n_obs": int(n),
        "seed_range": [int(min(seeds)), int(max(seeds))],
        "min_shift": int(shifts.min()), "max_shift": int(shifts.max()),
    }
    return env


def target_derangement_control(
    pred: np.ndarray, y: np.ndarray, dates: np.ndarray, seeds, *, unrestricted: bool = False
) -> dict:
    """DERANGEMENT of targets inside (symbol x calendar-month) blocks (design §5, L-28).

    ``unrestricted=True`` uses a single block over all rows — the disclosure control that
    removes every feature->target pairing (tripwire clause (b)).
    """
    n = pred.size
    live = spearman(pred, y)
    blocks = [np.arange(n)] if unrestricted else _month_blocks(dates)
    covered = int(sum(b.size for b in blocks))
    if n < 10 or not blocks:
        return {"status": "UNPOWERED", "n_obs": int(n), "live": live}
    vals = np.empty(len(seeds))
    index_fixed_points = 0
    value_collisions = 0
    for i, s in enumerate(seeds):
        rng = np.random.default_rng(s)
        yd, nf = derange_within_blocks(y, blocks, rng)
        index_fixed_points += nf
        value_collisions += int(np.sum((yd == y) & np.isfinite(y)))
        vals[i] = spearman(pred, yd)
    env = _envelope(vals, live)
    env |= {
        "status": "OK",
        "destroy_form": "DERANGEMENT",
        "block_form": "UNRESTRICTED" if unrestricted else "SYMBOL_x_CALENDAR_MONTH",
        "n_obs": int(n),
        "n_blocks": len(blocks), "rows_covered": covered,
        "seed_range": [int(min(seeds)), int(max(seeds))],
        "index_fixed_points": int(index_fixed_points),
        "value_collisions": int(value_collisions),
        "value_collision_note": (
            "index_fixed_points is the MEASURED count of i -> i landings across the whole seed "
            "battery and must be exactly 0 (L-28); value_collisions counts coincidental "
            "equal-VALUE landings, which are not fixed points"
        ),
    }
    return env


def bite_check(y: np.ndarray, dates: np.ndarray, seeds_shuffle, seeds_derange) -> dict:
    """+0.25 rank-correlation plant must be destroyed by both destroy operations (design §5)."""
    rng = np.random.default_rng(7)
    plant = plant_feature(y, PLANT_RANK_CORR, rng)
    live = spearman(plant, y)
    sh = time_shuffle_control(plant, y, seeds_shuffle[:50])
    de = target_derangement_control(plant, y, dates, seeds_derange[:50])
    return {
        "target_rank_corr": PLANT_RANK_CORR,
        "achieved_plant_ic": live,
        "shuffle": sh,
        "derangement": de,
        "plant_destroyed_by_shuffle": bool(
            sh.get("status") == "OK" and abs(sh.get("p50", 1.0)) < 0.05 and live > 0.15
        ),
        "plant_destroyed_by_derangement": bool(
            de.get("status") == "OK" and abs(de.get("p50", 1.0)) < 0.05 and live > 0.15
        ),
    }


def future_destroy_layer(derange_env: dict, global_env: dict) -> dict:
    """Future-destroy REPORT LAYER — observed / ideal / interpretation, no ``pass`` field.

    Operator decision 2026-07-23 (QA F-2/F-3, recorded as DEV-1): this reads as a report
    layer rather than a hard gate, because the check cannot fail in the way a gate implies.
    ``E[Spearman(pred, deranged y)] = 0`` for ANY fixed predictor, so destroying the outcome
    removes the association whether or not the predictor leaked — no outcome-side destroy can
    detect look-ahead. The interpretation string is a LABEL, never a gate (L-32).
    """
    if derange_env.get("status") != "OK" or global_env.get("status") != "OK":
        return {"layer": "future_destroy", "interpretation": "UNPOWERED",
                "reason": "insufficient origins for a destroy control"}
    live = global_env.get("live")
    g50 = global_env.get("p50")
    gsd = global_env.get("sd")
    b50 = derange_env.get("p50")
    if live is None or g50 is None or b50 is None or not gsd:
        return {"layer": "future_destroy", "interpretation": "UNPOWERED",
                "reason": "no finite IC"}
    z_zero = abs(g50) / gsd
    z_live = (live - g50) / gsd
    centred = z_zero <= TRIPWIRE_Z
    separated = (live <= 0) or (z_live >= TRIPWIRE_Z)
    if not centred:
        interp = "NULL_NOT_CENTRED"
    elif not separated:
        interp = "LIVE_INSIDE_DESTROYED_NULL"
    else:
        interp = "COLLAPSED_AS_EXPECTED"
    return {
        "layer": "future_destroy",
        "interpretation": interp,
        "ideal": {
            "null_centre": 0.0,
            "z_zero_at_most": TRIPWIRE_Z,
            "z_live_at_least": TRIPWIRE_Z,
        },
        "destroy_form_reported": "UNRESTRICTED_TARGET_DERANGEMENT",
        "live_ic": live,
        "null_p50": g50,
        "null_sd": gsd,
        "null_p99": global_env.get("p99"),
        "collapse_fraction": global_env.get("collapse_fraction"),
        "z_zero": z_zero,
        "z_live": z_live,
        "null_centred": bool(centred),
        "live_separated_from_null": bool(separated),
        "informative_power": (
            "this gate is a null-CENTRING sanity check, not a look-ahead leak test: "
            "E[Spearman(pred, deranged y)] = 0 for ANY fixed pred, so no target-side destroy "
            "can detect a leaking predictor (QA F-2). The operative non-vacuity devices are "
            "the predictor-side CIRCULAR_SHIFT control and the design §7.4 causality asserts."
        ),
        "reference_bars": (
            f"COLLAPSED_AS_EXPECTED when |median(null)|/sd(null) <= {TRIPWIRE_Z} and "
            f"(live - median(null))/sd(null) >= {TRIPWIRE_Z}; these are labels, not gates"
        ),
        "block_restricted_control": {
            "role": "design §5 CONTROL TARGET-LABEL-DERANGEMENT (not a leak verdict)",
            "null_p50": b50,
            "null_p95": derange_env.get("p95"),
            "null_p99": derange_env.get("p99"),
            "one_sided_p": derange_env.get("one_sided_p"),
            "live_above_p95": derange_env.get("live_above_p95"),
            "live_above_p99": derange_env.get("live_above_p99"),
            "collapse_fraction": derange_env.get("collapse_fraction"),
            "note": (
                "deranging inside symbol x calendar-month cannot remove the BETWEEN-month "
                "component, so this null is not centred at zero; its median rises with the "
                "strength of the true relationship. Read it in the design's stated direction "
                "(live IC above null p95 => skill beyond the target's within-block marginals), "
                "never as a collapse test."
            ),
        },
    }
