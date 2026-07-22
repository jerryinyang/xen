"""Reusable XENA attribution/leak controls as REPORT LAYERS (INFR-016).

Promotes the per-experiment controls (XENA-HTFCAP-001 `analysis_code/controls.py`) into
`xen`, and **retires their auto-verdict fields**:

* ``rand_sign_battery`` no longer emits an ``at_or_above_p95`` boolean at 25 seeds (that bar
  is ~the top order statistic of 25 draws = pure noise; HTFCAP SOL 24.9 bps read P80/FALSE
  and was auto-labelled a "fail"). It now runs a **≥2000-seed** battery and reports **effect
  size + one-sided p + CI** — a description, never a pass/fail.
* ``attribution_derangement`` no longer emits ``hard_fail_leak`` / a collapse<0.5 auto-REJECT.
  It reports the **collapse fraction** (how much edge is timing/construction-attributable)
  with battery percentiles — the operator judges (INFR-016 §4c, operator-ratified 2026-07-18).

**Control class (INFR-016 §4c, operator-ratified).** Two disjoint classes:

* ``future_destroy`` — destroys information from AFTER the decision (time-reversal /
  future-shuffle / label-permutation). Edge survival ⇒ acausal L-01 leak. **This class stays a
  HARD VALIDITY attestation** and is NOT rendered as a report layer here (it belongs to the
  data-validity block; see :func:`assert_future_destroy_class`).
* ``within_sample_attribution`` — scrambles within-sample alignment/timing while entries stay
  causal (≤ t-1), e.g. the HTFCAP gate-schedule derangement. A partly-surviving edge is an
  **attribution** finding, not a leak → **report layer**.

Every derangement here is an L-28 derangement (zero fixed points, code-asserted).
Every battery is data-independent (regenerable from seed + entry schedule).
"""
from __future__ import annotations

from typing import Any

import numpy as np

from xen.xena.report_layer import LayerReport, structural_label

DEFAULT_SIGN_BATTERY_SEEDS = 2000     # INFR-016 §7 (operator-ratified 2026-07-18)
DEFAULT_DERANGE_SEEDS = 25            # ≥15 (L-19); default 25 for a stable percentile read
SIGN_BATTERY_SEED0 = 1000
DERANGE_SEED0 = 7000

CONTROL_CLASSES = ("future_destroy", "within_sample_attribution")


def assert_future_destroy_class(control_class: str) -> None:
    """A ``future_destroy`` control stays a HARD validity attestation (INFR-016 §4c) — it must
    not be routed through the report-layer path in this module. Raises if misrouted."""
    if control_class == "future_destroy":
        raise ValueError(
            "future_destroy controls are a HARD data-validity attestation (L-01 leak "
            "survival), not a report layer — keep them in the validity block (INFR-016 §4c)")
    if control_class not in CONTROL_CLASSES:
        raise ValueError(f"control_class must be one of {CONTROL_CLASSES}, got {control_class!r}")


def make_derangement(n: int, rng: np.random.Generator) -> np.ndarray:
    """L-28: permutation with zero fixed points; regenerate on any fixed point."""
    if n <= 1:
        return np.arange(n)
    for _ in range(10_000):
        p = rng.permutation(n)
        if not np.any(p == np.arange(n)):
            return p
    return (np.arange(n) + 1) % n  # cycle fallback (still zero fixed points)


# --------------------------------------------------------------------------- #
# Sign battery — effect size + one-sided p + CI (NO at_or_above_p95 boolean)
# --------------------------------------------------------------------------- #
def sign_battery(direction: np.ndarray, entry_price: np.ndarray, exit_price: np.ndarray,
                 *, candidate_id: str, n_seeds: int = DEFAULT_SIGN_BATTERY_SEEDS,
                 seed0: int = SIGN_BATTERY_SEED0,
                 min_powered_seeds: int = 1000) -> LayerReport:
    """Rademacher sign-scramble battery on a fixed entry schedule → a report layer.

    Destroys directional content (Rademacher signs on |path magnitude|); keeps the entry
    schedule. Reports the observed raw median gross bps, the battery's null distribution, the
    live effect vs the battery mean, a **one-sided p** (fraction of null medians ≥ raw), and a
    percentile-bootstrap CI on the null median — NEVER a P95 boolean.

    ``min_powered_seeds``: below this the read is labelled UNPOWERED (a 25-seed battery cannot
    resolve a tail quantile — the HTFCAP defect).
    """
    d = np.asarray(direction, dtype=float)
    ep = np.asarray(entry_price, dtype=float)
    xp = np.asarray(exit_price, dtype=float)
    raw = d * (xp - ep) / ep * 1e4
    raw_med = float(np.median(raw))
    mag = np.abs(xp - ep) / ep * 1e4

    battery: list[float] = []
    for i in range(n_seeds):
        signs = np.random.default_rng(seed0 + i).choice(np.array([-1.0, 1.0]), size=len(raw))
        battery.append(float(np.median(signs * mag)))
    arr = np.asarray(battery, dtype=float)
    null_mean = float(np.mean(arr))
    null_sd = float(np.std(arr, ddof=1)) if len(arr) > 1 else float("nan")
    # one-sided p: P(null median >= observed raw median) under the sign-scramble null
    one_sided_p = float(np.mean(arr >= raw_med))
    effect = raw_med - null_mean
    # 95% CI on the null median (percentile bootstrap of the battery itself)
    ci_lo = float(np.quantile(arr, 0.025)) if len(arr) else float("nan")
    ci_hi = float(np.quantile(arr, 0.975)) if len(arr) else float("nan")
    percentile = float(np.mean(arr <= raw_med))

    powered = n_seeds >= min_powered_seeds
    # Structural label only (UNPOWERED / CONTRADICTED / None) — the plain read below carries
    # the p-strength; no p-cutpoint label (INFR-016 follow-up, retires the L-32-in-miniature).
    label = structural_label(powered=powered, directional_positive=raw_med > 0)
    interp = (
        f"raw {raw_med:.1f} bps vs sign-null mean {null_mean:.1f} bps "
        f"(effect {effect:+.1f}); one-sided p={one_sided_p:.3f}, "
        f"percentile {percentile:.2f}; "
        + ("underpowered — too few seeds to resolve the tail"
           if not powered else
           "suggestive but not decisive" if 0.15 < one_sided_p <= 0.35 else
           "directional signal above the null" if one_sided_p <= 0.15 else
           "within noise of the sign null"))
    return LayerReport(
        layer="sign_battery",
        candidate_id=candidate_id,
        observed=f"raw {raw_med:.1f} bps, p={one_sided_p:.3f}",
        ideal_range="raw median above the sign null with one-sided p ≤ ~0.05 (real edge)",
        interpretation=interp,
        interpretation_label=label,
        supporting={
            "n_legs": int(len(raw)),
            "n_seeds": int(n_seeds),
            "raw_median_gross_bps": raw_med,
            "null_mean_gross_bps": null_mean,
            "null_sd_gross_bps": null_sd,
            "effect_bps": effect,
            "one_sided_p": one_sided_p,
            "percentile_vs_battery": percentile,
            "null_ci95": [ci_lo, ci_hi],
            "powered": bool(powered),
            "form": "Rademacher sign scramble; schedule fixed (B-1); effect+p+CI, no P95 boolean",
        },
    )


# --------------------------------------------------------------------------- #
# Attribution derangement — reported collapse fraction (NO hard collapse<0.5 kill)
# --------------------------------------------------------------------------- #
def attribution_derangement(entry_idx: np.ndarray, block_id: np.ndarray,
                            block_edges: np.ndarray, n_blocks: int, grid_open: np.ndarray,
                            direction: np.ndarray, hold_bars: np.ndarray, *,
                            candidate_id: str, control_class: str = "within_sample_attribution",
                            n_seeds: int = DEFAULT_DERANGE_SEEDS,
                            seed0: int = DERANGE_SEED0) -> LayerReport:
    """Block-derangement attribution control on an open grid → a report layer.

    Remaps block b → derange(b) (zero fixed points), reprices matched-horizon open-to-open,
    and reports the **collapse fraction** distribution ``1 - deranged_median/raw_median``: how
    much of the edge is timing/construction-attributable. High collapse ⇒ mostly construction;
    low collapse ⇒ base entries carry edge independent of the alignment. **No auto-kill** — the
    operator reads the fraction (INFR-016 §4c). Only ``within_sample_attribution`` is allowed
    here; ``future_destroy`` stays a hard validity attestation.
    """
    assert_future_destroy_class(control_class)
    n_grid = len(grid_open)
    d = np.asarray(direction, dtype=float)
    ep_idx = np.asarray(entry_idx, dtype=int)
    hb = np.asarray(hold_bars, dtype=int)

    # raw matched-horizon open-to-open median on the true alignment
    raw_rets = []
    for i in range(len(ep_idx)):
        j0 = int(ep_idx[i])
        j1 = min(j0 + int(hb[i]), n_grid - 1)
        o0, o1 = grid_open[j0], grid_open[j1]
        if o0 > 0 and np.isfinite(o0) and np.isfinite(o1):
            raw_rets.append(float(d[i] * (o1 - o0) / o0 * 1e4))
    raw_med = float(np.median(raw_rets)) if raw_rets else float("nan")

    der_meds: list[float] = []
    collapses: list[float] = []
    all_zero_fixed = True
    for s in range(n_seeds):
        rng = np.random.default_rng(seed0 + s)
        perm = make_derangement(n_blocks, rng)
        all_zero_fixed = all_zero_fixed and not np.any(perm == np.arange(n_blocks))
        der_idx = ep_idx.copy()
        for i, b in enumerate(block_id):
            src_lo, src_hi = int(block_edges[b]), int(block_edges[b + 1])
            dst_b = int(perm[b])
            dst_lo, dst_hi = int(block_edges[dst_b]), int(block_edges[dst_b + 1])
            off = int(ep_idx[i] - src_lo)
            src_len, dst_len = max(1, src_hi - src_lo), max(1, dst_hi - dst_lo)
            der_idx[i] = min(dst_lo + int(off * dst_len / src_len), n_grid - 2)
        rets = []
        for i in range(len(der_idx)):
            j0 = int(der_idx[i])
            j1 = min(j0 + int(hb[i]), n_grid - 1)
            o0, o1 = grid_open[j0], grid_open[j1]
            if o0 > 0 and np.isfinite(o0) and np.isfinite(o1):
                rets.append(float(d[i] * (o1 - o0) / o0 * 1e4))
        dm = float(np.median(rets)) if rets else float("nan")
        der_meds.append(dm)
        collapses.append(1.0 - dm / raw_med if raw_med != 0 and np.isfinite(dm) else float("nan"))

    carr = np.asarray([c for c in collapses if np.isfinite(c)], dtype=float)
    med_collapse = float(np.median(carr)) if carr.size else float("nan")

    def _q(p: float) -> float:
        return float(np.quantile(carr, p)) if carr.size else float("nan")

    interp = (
        f"collapse {med_collapse:.2f} of edge is timing/construction-attributable "
        f"(battery p05–p95 {_q(0.05):.2f}–{_q(0.95):.2f}); "
        + ("most of the edge is the construction/timing"
           if med_collapse >= 0.5 else
           "base entries carry edge independent of the alignment — operator judges leak vs edge"))
    return LayerReport(
        layer="attribution_derangement",
        candidate_id=candidate_id,
        observed=f"collapse median {med_collapse:.2f}",
        ideal_range="≈1.0 if the edge is construction-specific; low = base-signal edge (not a leak)",
        interpretation=interp,
        interpretation_label=None,
        supporting={
            "control_class": control_class,
            "n_legs": int(len(raw_rets)),
            "n_blocks": int(n_blocks),
            "n_derange_seeds": int(n_seeds),
            "derangement_zero_fixed_points": bool(all_zero_fixed),
            "raw_median_gross_bps": raw_med,
            "deranged_median_gross_bps_battery": der_meds,
            "collapse_median": med_collapse,
            "collapse_p05": _q(0.05), "collapse_p25": _q(0.25),
            "collapse_p75": _q(0.75), "collapse_p95": _q(0.95),
            "form": (f"{n_seeds}-seed block-derangement battery; matched-horizon open-to-open; "
                     "collapse fraction reported (no auto-kill, INFR-016 §4c)"),
        },
    )
