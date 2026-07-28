"""Controls and tripwires (design §7).

Three uniform additions on top of each arm's inherited parent controls:

  * ``MAGNITUDE-MATCHED-COMPARATOR``  [within_sample_attribution -> REPORT LAYER]  (M-3)
  * ``SIDE-DERANGEMENT``              [within_sample_attribution -> REPORT LAYER]
  * ``AMBIENT-BASE``                  [disclosure -> base-conditional obligation]

plus the three tripwires. Every output here is a REPORT LAYER: a percentile, a null
distribution, an effect size, an MDE curve. There is no ``pass`` field, no
``at_or_above_pXX`` boolean and no collapse-fraction auto-kill (INFR-016 / L-32); collapse
fraction is emitted as DISCLOSURE ONLY because it is uninterpretable near a zero mean (M-5).
"""
from __future__ import annotations

import numpy as np

from config import (
    DERANGE_SEEDS,
    MAGMATCH_DECILES,
    MAGMATCH_NEIGHBOURHOOD,
    MAGMATCH_SEEDS,
    PLANT_CURVE_BPS,
    TRIPWIRE_SEEDS,
)
from metrics import _trimmed


# --------------------------------------------------------------------------- #
# derangement machinery (L-28: zero fixed points, measured and reported)
# --------------------------------------------------------------------------- #
def derangement(n: int, rng: np.random.Generator, *, max_tries: int = 64) -> np.ndarray:
    """A permutation of ``0..n-1`` with **zero fixed points**.

    Rejection-sample a uniform permutation, then fall back to Sattolo's algorithm (which produces
    a single n-cycle, fixed-point-free by construction) so the guarantee never depends on luck.
    A plain permutation has E[fixed points] = 1 for any n and leaks true alignment through them
    (VAL-008: 11.1% fixed alignment, collapse 0.87 not ~0).
    """
    if n < 2:
        return np.arange(n)
    for _ in range(max_tries):
        p = rng.permutation(n)
        if not np.any(p == np.arange(n)):
            return p
    p = np.arange(n)
    for i in range(n - 1, 0, -1):
        j = int(rng.integers(0, i))          # strictly j < i -> single cycle, no fixed point
        p[i], p[j] = p[j], p[i]
    assert not np.any(p == np.arange(n)), "Sattolo produced a fixed point"
    return p


def derangeable_mask(groups: np.ndarray) -> np.ndarray:
    """Rows whose group has >= 2 members — the only rows a within-group derangement can move.

    A singleton ``(symbol x month)`` group cannot be deranged in place: whatever permutation is
    applied, that row keeps its own label, which is a FIXED POINT. L-28 makes zero fixed points
    absolute, so such rows are EXCLUDED from the control population rather than left sitting in it
    — and the excluded mass is disclosed on every control, never dropped quietly.
    """
    g = np.asarray(groups)
    uniq, counts = np.unique(g, return_counts=True)
    big = set(uniq[counts >= 2].tolist())
    return np.array([x in big for x in g], dtype=bool)


def grouped_derangement(groups: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, int]:
    """Derange WITHIN each group. Callers must pre-filter to ``derangeable_mask``; any singleton
    group reaching here would be a fixed point, so its presence is reported, not silently kept."""
    perm = np.arange(groups.size)
    for g in np.unique(groups):
        idx = np.where(groups == g)[0]
        if idx.size < 2:
            continue
        perm[idx] = idx[derangement(idx.size, rng)]
    fixed = int(np.sum(perm == np.arange(groups.size)))
    return perm, fixed


def _percentile_of(live: float, null: np.ndarray) -> dict:
    """Percentile + two-sided and one-sided p — never a boolean (L-32)."""
    v = np.asarray(null, dtype=float)
    v = v[np.isfinite(v)]
    if v.size == 0 or not np.isfinite(live):
        return {"percentile": float("nan"), "p_one_sided": float("nan"),
                "p_two_sided": float("nan"), "n_seeds_effective": int(v.size)}
    pct = float((v < live).mean())
    p_hi = float((v >= live).mean())
    p_lo = float((v <= live).mean())
    return {
        "percentile": pct,
        "p_one_sided": min(p_hi, p_lo),
        "p_two_sided": min(1.0, 2.0 * min(p_hi, p_lo)),
        "null_mean": float(v.mean()),
        "null_sd": float(v.std(ddof=1)) if v.size > 1 else float("nan"),
        "null_q": [float(np.quantile(v, q)) for q in (0.025, 0.25, 0.5, 0.75, 0.975)],
        "n_seeds_effective": int(v.size),
    }


def _collapse_fraction_disclosure(live: float, null_mean: float) -> dict:
    """M-5: DISCLOSURE ONLY. Uninterpretable when the live mean is near zero (denominator -> 0)."""
    if not np.isfinite(live) or abs(live) < 1e-12:
        frac = float("nan")
    else:
        frac = float(1.0 - null_mean / live)
    return {
        "collapse_fraction": frac,
        "collapse_fraction_status": "DISCLOSURE_ONLY",
        "collapse_fraction_why": ("M-5: the denominator is the live mean; near zero the ratio is uninterpretable. "
                "The usable objects are the percentile and the null distribution."),
        "collapse_fraction_never_used_as": ("auto-kill / hard_fail_leak threshold "
                                            "(retired, INFR-016 / L-32)"),
    }


# --------------------------------------------------------------------------- #
# CONTROL: SIDE-DERANGEMENT
# --------------------------------------------------------------------------- #
def side_derangement(r_signed: np.ndarray, side: np.ndarray, group: np.ndarray, *,
                     seeds=DERANGE_SEEDS, stat=np.mean) -> dict:
    """Does the cell tell us WHICH WAY, or is a positive mean this symbol's drift?

    Side labels are deranged within ``(symbol x calendar-month)``; paths, states, entries and
    exits are unchanged. The metric is the mean of a SIGNED return, so deranging sides moves it
    directly — the opposite of the banned pattern (permuting realised P&L preserves the mean,
    L-14 / EXP-012). Applies to every cell carrying a signed return (arms B and C).
    """
    r = np.asarray(r_signed, dtype=float)
    s = np.asarray(side, dtype=float)
    ok = np.isfinite(r) & np.isfinite(s) & (s != 0)
    r, s, g = r[ok], s[ok], np.asarray(group)[ok]
    n_eligible = int(r.size)
    keep = derangeable_mask(g)
    n_singleton = int((~keep).sum())
    r, s, g = r[keep], s[keep], g[keep]
    if r.size < 2:
        return {"control": "SIDE-DERANGEMENT", "n": int(r.size), "degenerate": True,
                "n_excluded_singleton_group_rows": n_singleton}

    unsigned = r * s                       # side in {-1,+1} -> r/s == r*s
    live = float(stat(r))
    null = np.empty(len(seeds))
    fixed_total = 0
    label_agree = np.empty(len(seeds))
    for i, sd in enumerate(seeds):
        rng = np.random.default_rng(int(sd))
        perm, fixed = grouped_derangement(g, rng)
        fixed_total += fixed
        s_new = s[perm]
        label_agree[i] = float(np.mean(s_new == s))
        null[i] = float(stat(s_new * unsigned))

    pctl = _percentile_of(live, null)
    return {
        "control": "SIDE-DERANGEMENT",
        "class": "within_sample_attribution -> REPORT LAYER",
        "destroy_form": "DERANGEMENT",
        "n": int(r.size),
        "n_eligible_rows": n_eligible,
        "n_excluded_singleton_group_rows": n_singleton,
        "exclusion_reason": ("a singleton (symbol x calendar-month) group cannot be deranged in "
                             "place — keeping it would be a fixed point, which L-28 forbids. The "
                             "excluded mass is disclosed here, never dropped quietly."),
        "n_seeds": len(seeds),
        "live_effect_bps": live,
        **pctl,
        "fixed_points_total": int(fixed_total),
        "fixed_points_per_seed": 0.0 if len(seeds) == 0 else fixed_total / len(seeds),
        "side_label_agreement_mean": float(np.mean(label_agree)),
        "side_label_agreement_note": (
            "index derangement is exact (0 fixed points). Side is a BINARY label, so a deranged "
            "row can still receive the same value by coincidence; that residual agreement is "
            "disclosed here rather than hidden inside the fixed-point count."
        ),
        **_collapse_fraction_disclosure(live, float(np.mean(null))),
        "plant_curve": plant_curve(r, lambda x: float(stat(x)),
                                   lambda x, rng: _derange_plant(x, s, unsigned, g, rng)),
    }


def _derange_plant(_r_planted: np.ndarray, side: np.ndarray, unsigned: np.ndarray,
                   group: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Null draw for the plant curve.

    The plant is an edge that the STATE earns, so deranging the side destroys it: the null is
    built from the unplanted series. Carrying the plant into the null too would cancel it and
    make the curve flat — an MDE curve that cannot see any plant is not an MDE curve.
    """
    perm, _ = grouped_derangement(group, rng)
    return side[perm] * unsigned


# --------------------------------------------------------------------------- #
# CONTROL: MAGNITUDE-MATCHED COMPARATOR  (M-3)
# --------------------------------------------------------------------------- #
def magnitude_matched(live_abs_r: np.ndarray, live_outcome: np.ndarray,
                      pool_abs_r: np.ndarray, pool_outcome: np.ndarray,
                      pool_excluded: np.ndarray, *, seeds=MAGMATCH_SEEDS,
                      deciles: int = MAGMATCH_DECILES, stat=np.mean) -> dict:
    """On a conditioner DEFINED by move magnitude: is the effect the state, or a big bar?

    Draws a decile-stratified comparator from ``pool_*`` that matches the live rows' ``|r_t|``
    distribution but does NOT carry the state; live rows and their ``+-1`` bar neighbourhood are
    excluded (``pool_excluded``). A side-matched control cannot make this separation — that is
    the whole of M-3.

    When the state is *definitionally* the magnitude (``shock`` == top decile of ``|r_t|``), no
    disjoint magnitude-matched pool exists in the upper deciles. That is not a control failure to
    be papered over: it is reported as ``MATCH_INFEASIBLE_STATE_IS_MAGNITUDE`` with the realised
    per-decile supply, which is itself the answer to "is this anything more than a big bar?".
    """
    la = np.asarray(live_abs_r, dtype=float)
    lo = np.asarray(live_outcome, dtype=float)
    keep = np.isfinite(la) & np.isfinite(lo)
    la, lo = la[keep], lo[keep]
    pa = np.asarray(pool_abs_r, dtype=float)
    po = np.asarray(pool_outcome, dtype=float)
    avail = np.isfinite(pa) & np.isfinite(po) & ~np.asarray(pool_excluded, dtype=bool)
    pa_i = np.where(avail)[0]

    out: dict = {
        "control": "MAGNITUDE-MATCHED-COMPARATOR",
        "class": "within_sample_attribution -> REPORT LAYER",
        "rule": "M-3",
        "n_live": int(la.size),
        "n_pool_available": int(pa_i.size),
        "neighbourhood_excluded_bars": MAGMATCH_NEIGHBOURHOOD,
        "n_seeds": len(seeds),
    }
    if la.size < 2 or pa_i.size < 2:
        out["status"] = "DEGENERATE_TOO_FEW_ROWS"
        return out

    edges = np.quantile(la, np.linspace(0, 1, deciles + 1))
    edges[0], edges[-1] = -np.inf, np.inf
    live_bin = np.clip(np.digitize(la, edges[1:-1]), 0, deciles - 1)
    pool_bin = np.clip(np.digitize(pa[pa_i], edges[1:-1]), 0, deciles - 1)
    want = np.bincount(live_bin, minlength=deciles)
    have = np.bincount(pool_bin, minlength=deciles)
    supply = [{"decile": int(d), "live_n": int(want[d]), "pool_n": int(have[d]),
               "abs_r_lo": float(edges[d]), "abs_r_hi": float(edges[d + 1])}
              for d in range(deciles)]
    out["decile_supply"] = supply
    short = [d for d in range(deciles) if want[d] > 0 and have[d] == 0]
    out["deciles_with_no_comparator_supply"] = short

    if len(short) >= max(1, deciles // 2):
        out["status"] = "MATCH_INFEASIBLE_STATE_IS_MAGNITUDE"
        out["interpretation"] = (
            "The conditioner is definitionally the magnitude: no rows outside the state carry "
            "comparable |r_t| in most deciles, so a disjoint magnitude-matched comparator cannot "
            "exist. The state adds nothing over 'this was a big bar' that this design can "
            "separate — reported as a measured fact, not inferred."
        )
        out["live_effect_bps"] = float(stat(lo))
        return out

    per_bin = {d: pa_i[pool_bin == d] for d in range(deciles)}
    live = float(stat(lo))
    null = np.empty(len(seeds))
    matched_n = np.empty(len(seeds))
    for i, sd in enumerate(seeds):
        rng = np.random.default_rng(int(sd))
        take = []
        for d in range(deciles):
            k = int(want[d])
            src = per_bin[d]
            if k == 0 or src.size == 0:
                continue
            take.append(rng.choice(src, size=k, replace=src.size < k))
        if not take:
            null[i] = np.nan
            matched_n[i] = 0
            continue
        sel = np.concatenate(take)
        matched_n[i] = sel.size
        null[i] = float(stat(po[sel]))

    out["status"] = "MATCHED"
    out["live_effect_bps"] = live
    out["comparator_n_mean"] = float(np.nanmean(matched_n))
    out.update(_percentile_of(live, null))
    out.update(_collapse_fraction_disclosure(live, float(np.nanmean(null))))
    out["expected_if_H_true"] = "live outside the comparator distribution"
    out["expected_if_H_false"] = "live inside the comparator distribution"
    def _comparator_draw(_planted, rng):
        """A fresh matched comparator sample. The plant lives on the LIVE rows only, so the
        comparator null is unaffected by it — that is what makes the curve a detectability read."""
        take = [rng.choice(per_bin[d], size=int(want[d]), replace=per_bin[d].size < int(want[d]))
                for d in range(deciles) if want[d] > 0 and per_bin[d].size > 0]
        return po[np.concatenate(take)]

    out["plant_curve"] = plant_curve(lo, lambda x: float(stat(x)), _comparator_draw)
    return out


# --------------------------------------------------------------------------- #
# CONTROL: AMBIENT-BASE  (base-conditional obligation, spdr-lane)
# --------------------------------------------------------------------------- #
def ambient_base(live_r: np.ndarray, ambient_r: np.ndarray, *, cost_bps: float,
                 ts_live: np.ndarray, ts_ambient: np.ndarray) -> dict:
    """The cell's OWN conditional effect on the outcome distribution — not a lift-vs-baseline.

    Per the lane's binding directive a measured distributional shift on a null base is a POSITIVE
    QUANTIFICATION, reported as a magnitude with its CI, never qualified away as "within noise".
    """
    from metrics import signed_cell     # local import: avoids a cycle at module load

    a = signed_cell(live_r, ts_live, cost_bps=cost_bps, full=False)
    b = signed_cell(ambient_r, ts_ambient, cost_bps=cost_bps, full=False)
    deltas = {}
    for k in ("mean", "median", "p", "W", "L", "W_L"):
        deltas[f"delta_{k}"] = (float(a.get(k, np.nan) - b.get(k, np.nan))
                                if np.isfinite(a.get(k, np.nan)) and np.isfinite(b.get(k, np.nan))
                                else float("nan"))
    lr = np.asarray(live_r, dtype=float)
    ar = np.asarray(ambient_r, dtype=float)
    lr, ar = lr[np.isfinite(lr)], ar[np.isfinite(ar)]
    return {
        "control": "AMBIENT-BASE",
        "class": "disclosure -> BASE-CONDITIONAL OBLIGATION",
        "framing": ("the cell's own conditional effect on the outcome distribution, independent "
                    "of profitability — NOT a lift-vs-baseline read"),
        "n_live": int(lr.size), "n_ambient": int(ar.size),
        "live": {k: a.get(k) for k in ("mean", "median", "trimmed_mean_10", "p", "W", "L", "W_L",
                                       "mean_ci_low", "mean_ci_high", "p_ci_low", "p_ci_high",
                                       "W_ci_low", "W_ci_high", "L_ci_low", "L_ci_high",
                                       "W_L_ci_low", "W_L_ci_high", "block_mde_mean_bps")},
        "ambient": {k: b.get(k) for k in ("mean", "median", "trimmed_mean_10", "p", "W", "L",
                                          "W_L", "mean_ci_low", "mean_ci_high",
                                          "block_mde_mean_bps")},
        "delta_dispersion_sd_bps": (float(np.std(lr, ddof=1) - np.std(ar, ddof=1))
                                    if lr.size > 1 and ar.size > 1 else float("nan")),
        "delta_dispersion_iqr_bps": (
            float((np.percentile(lr, 75) - np.percentile(lr, 25))
                  - (np.percentile(ar, 75) - np.percentile(ar, 25)))
            if lr.size > 3 and ar.size > 3 else float("nan")),
        **deltas,
    }


# --------------------------------------------------------------------------- #
# MDE curve (bite) — the smallest plant detectable at realised n
# --------------------------------------------------------------------------- #
PLANT_SEEDS = tuple(range(50_000, 50_200))      # 200 draws -> percentile resolution 0.005


def plant_curve(r: np.ndarray, stat, null_draw, *, plants=PLANT_CURVE_BPS,
                seeds=PLANT_SEEDS) -> list[dict]:
    """Plant ``{5,10,20,40}`` bps on the live rows; report the seed-battery percentile at each.

    States the smallest plant detectable at the realised ``n`` — an MDE CURVE, never a pass mark.
    """
    r = np.asarray(r, dtype=float)
    r = r[np.isfinite(r)]
    out = []
    if r.size < 2:
        return out
    for plant in plants:
        planted = r + plant
        live = float(stat(planted))
        null = []
        for sd in seeds:
            rng = np.random.default_rng(int(sd))
            try:
                null.append(float(stat(null_draw(planted, rng))))
            except Exception:                     # a degenerate cell yields no null draw
                continue
        if not null:
            continue
        out.append({"plant_bps": float(plant), "live_effect": live,
                    **_percentile_of(live, np.asarray(null))})
    return out


# --------------------------------------------------------------------------- #
# TRIPWIRES (§7.1)
# --------------------------------------------------------------------------- #
def tripwire_1_construction(rows: dict) -> dict:
    """TRIPWIRE-1 [HARD]: per-row index assertions. A violation ABORTS the run.

    Every feature index <= the parent's declared lag; entry strictly after the decision bar; exit
    at the declared offset; expanding statistics use only rows strictly before the decision bar.
    """
    checks = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"check": name, "held": bool(ok), "detail": detail})
        if not ok:
            raise AssertionError(f"TRIPWIRE-1 violated: {name} — {detail}")

    t = np.asarray(rows["decision_idx"], dtype=np.int64)
    e = np.asarray(rows["entry_idx"], dtype=np.int64)
    x = np.asarray(rows["exit_idx"], dtype=np.int64)
    h = rows["h"]
    chk("entry strictly after the decision bar", bool(np.all(e > t)),
        f"min(entry-decision)={int((e - t).min()) if t.size else 'n/a'}")
    chk("exit at the declared offset", bool(np.all(x - e == h)),
        f"declared h={h}; observed offsets {np.unique(x - e)[:5].tolist() if t.size else 'n/a'}")
    if "feature_idx" in rows:
        f = np.asarray(rows["feature_idx"], dtype=np.int64)
        lag = int(rows.get("declared_lag", 1))
        chk("every feature index <= decision bar - declared lag", bool(np.all(f <= t - lag + 1)),
            f"declared_lag={lag}")
    if "expanding_end_idx" in rows:
        ee = np.asarray(rows["expanding_end_idx"], dtype=np.int64)
        chk("expanding statistics exclude the decision bar", bool(np.all(ee < t)), "")
    return {"tripwire": "TRIPWIRE-1 CONSTRUCTION ASSERTIONS", "severity": "HARD",
            "n_rows": int(t.size), "checks": checks, "all_held": True}


def tripwire_2_leaky_twin(legal_effect: float, leaky_effect: float, *, n_matched: int) -> dict:
    """TRIPWIRE-2 [HARD]: a deliberately leaky twin must differ by orders of magnitude.

    The leaky twin computes its conditioner threshold over a window INCLUDING the forward horizon,
    so it selects rows using the outcome and shifts the conditional mean materially. SPDR-012
    measured the analogous contrast at ~12 orders of magnitude.

    NOT an outcome-side destroy: SPDR-012 AMENDMENT-T1 established that no outcome-side destroy
    can detect look-ahead for a fixed predictor. The causality claim rests on TRIPWIRE-1 and -2.
    """
    ratio = (abs(leaky_effect) / abs(legal_effect)
             if np.isfinite(legal_effect) and abs(legal_effect) > 1e-12 else float("inf"))
    return {
        "tripwire": "TRIPWIRE-2 LEAKY-VARIANT DISCRIMINATION", "severity": "HARD",
        "legal_effect_bps": float(legal_effect), "leaky_effect_bps": float(leaky_effect),
        "abs_ratio_leaky_over_legal": float(ratio),
        "n_matched_rows": int(n_matched),
        "emitted_variant": "legal",
        "vacuity_check": ("the leaky threshold selects rows using the outcome, which shifts the "
                          "conditional mean materially"),
    }


def tripwire_3_forward_path(side: np.ndarray, unsigned_move: np.ndarray, group: np.ndarray, *,
                            seeds=TRIPWIRE_SEEDS, stat=np.mean) -> dict:
    """TRIPWIRE-3 [REPORT LAYER — explicitly NOT the causality claim].

    Derange ``decision row -> forward path`` within ``symbol x month``: each decision row keeps
    its own side and receives ANOTHER row's forward path. Zero fixed points; expected collapse
    to ~0; reported as a null distribution with no ``pass`` field.

    Note what is deranged and why it is not vacuous: permuting the *realised signed return* would
    be mean-invariant and therefore a dead tripwire (L-14 / EXP-012). Breaking the side-to-path
    pairing moves the mean whenever the sides are not all equal, so the control can actually
    differ from the live arm.
    """
    s = np.asarray(side, dtype=float)
    u = np.asarray(unsigned_move, dtype=float)
    ok = np.isfinite(s) & np.isfinite(u) & (s != 0)
    s, u, g = s[ok], u[ok], np.asarray(group)[ok]
    n_eligible = int(s.size)
    keep = derangeable_mask(g)
    n_singleton = int((~keep).sum())
    s, u, g = s[keep], u[keep], g[keep]
    if s.size < 2:
        return {"tripwire": "TRIPWIRE-3 FORWARD-PATH DERANGEMENT", "degenerate": True,
                "n_excluded_singleton_group_rows": n_singleton}
    live = float(stat(s * u))
    null = np.empty(len(seeds))
    fixed_total = 0
    for i, sd in enumerate(seeds):
        rng = np.random.default_rng(int(sd))
        perm, fixed = grouped_derangement(g, rng)
        fixed_total += fixed
        null[i] = float(stat(s * u[perm]))     # own side, another row's forward path
    return {
        "tripwire": "TRIPWIRE-3 FORWARD-PATH DERANGEMENT",
        "severity": "REPORT LAYER (not the causality claim)",
        "destroy_form": "DERANGEMENT (decision row -> forward path)",
        "n": int(s.size), "n_eligible_rows": n_eligible,
        "n_excluded_singleton_group_rows": n_singleton,
        "n_seeds": len(seeds),
        "live_effect_bps": live,
        "fixed_points_total": int(fixed_total),
        **_percentile_of(live, null),
        **_collapse_fraction_disclosure(live, float(np.mean(null))),
        "non_vacuity": ("the side-to-path pairing is broken, which moves the mean of a signed "
                        "return directly; permuting realised P&L would be mean-invariant (L-14)"),
        "not_the_causality_claim": ("SPDR-012 AMENDMENT-T1: no outcome-side destroy can detect "
                                    "look-ahead for a fixed predictor. Causality rests on "
                                    "TRIPWIRE-1 and TRIPWIRE-2."),
    }
