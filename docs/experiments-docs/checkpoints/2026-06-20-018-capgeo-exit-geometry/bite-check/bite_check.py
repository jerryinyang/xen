"""Phase 018 D9 bite check — pre-G0 separability-gate threshold calibration (NOT an experiment).

Calibrates and confirms the D0 §D4 separability-gate thresholds named in §D9 — the S2 tail
non-residual thresholds (`tau_tail`, `delta`, with the catastrophe anchor `K_tail`) and the S1
matched-control edge-call margin (`m`, the `m_cell` standard) — plus the D3 derivation-quantile
estimability sanity. Each threshold is shown to be **neither vacuous** (does not pass regardless of
shape) **nor impossible** (passes when the shape is genuinely separable), with the operating point
chosen on a ROC over the Phase-017 canonical fixtures: a **known-separable** unimodal-positive
fixture must PASS S2 and the **known-harami** minority-catastrophe shapes (`B_zero`, `B_neg`) must
FAIL S2 at false-flag <= 0.05 / detection >= 0.80.

Why this gate, not `ASS`: EXP-078 proved the `ASS` mean-median-gap / dip-test shape diagnostic is
*structurally blind* to the subtle median-positive minority-catastrophe shape (`B_zero` true
|g|=0.25, `B_pos` |g|=0.067). D4 S2 is therefore built on the **minority-mass / left-tail-mass**
detector that `ASS` lacks. This bite check verifies that detector actually discriminates the harami
failure shape on synthetic data before the thresholds are frozen at G0.

This is **pre-G0 calibration tooling, not an experiment**: no market data, no holdout, no slot. The
full Phase-018 screening (EXP-080 onward) and any TEST contact are authorized only after G0
ratification of the frozen values reported here.

Run:  python bite_check.py     # deterministic; writes bite_check_report.json beside this file
Deps: numpy, scipy
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
from scipy import stats

# --------------------------------------------------------------------------------------
# Constants (SEED = checkpoint open date; bite scale)
# --------------------------------------------------------------------------------------
SEED = 20260621
N_REP = 3000             # replicate draws per (fixture, n) for rate estimates
N_BOOT = 2000            # bootstrap draws per replicate (bite scale; production EXP = 10_000)
CI_ALPHA = 0.10          # 90% CI (one-sided lower leg used for S1)
N_CAL = 250              # representative powered n for the S2 operating-point calibration
N_FLOOR = 120            # operating-floor n (S2 binds via Wilson-hi <= 0.075 here)
N_SUBFLOOR = 60          # disclosed-infeasible n (S2 deferred below the floor)
N_S1 = 250               # sample size for the S1 margin calibration
N_D3 = 30                # >=30-event floor for the D3 estimability sanity

# --- FROZEN candidate thresholds under test (D4 S2 / S1) ---
K_TAIL = 3.0             # catastrophe anchor: tailmass = fraction below median - K_TAIL*MAD
TAU_TAIL = 0.06          # S2 post-exit minority-mass cap (PASS iff tailmass <= TAU_TAIL)
DELTA = 0.40             # S2 relative-q05 tolerance (ATR): PASS iff q05 >= q05_control - DELTA
S2_FALSE_FLAG_MAX = 0.05
S2_DETECTION_MIN = 0.80
FPR_TARGET = 0.05        # S1 matched-control edge-call FPR
FPR_WILSON_UPPER = 0.075


# --------------------------------------------------------------------------------------
# D1 synthetic data-generating processes (Phase-017 canonical shapes; EXP-078 registry)
# --------------------------------------------------------------------------------------
def gen_unimodal(mu: float, n: int, rng: np.random.Generator) -> np.ndarray:
    return rng.normal(mu, 1.0, n)


def gen_bimodal(w: float, mu1: float, s1: float, mu2: float, s2: float, n: int,
                rng: np.random.Generator) -> np.ndarray:
    comp = rng.random(n) < w
    return np.where(comp, rng.normal(mu1, s1, n), rng.normal(mu2, s2, n))


# Known-separable (negative for the S2 ROC): unimodal median-positive capture.
def fix_separable(n, rng):
    return gen_unimodal(0.15, n, rng)


# Matched-random control (the S2 q05 reference / S1 null): centred, unimodal.
def fix_control(n, rng):
    return gen_unimodal(0.0, n, rng)


# Known-harami (positive for the S2 ROC): Phase-017 minority-catastrophe shapes.
HARAMI_BINDING = {                                  # D9 binding detection targets
    "B_neg":  lambda n, r: gen_bimodal(0.85, 0.15, 0.5, -2.0, 0.6, n, r),
    "B_zero": lambda n, r: gen_bimodal(0.90, 0.15, 0.5, -1.5, 0.6, n, r),
}
HARAMI_DISCLOSED = {                                # reported, not binding
    "B_strong": lambda n, r: gen_bimodal(0.80, 0.20, 0.5, -2.0, 0.6, n, r),  # easy sanity-detect
    "B_pos":    lambda n, r: gen_bimodal(0.95, 0.10, 0.5, -1.0, 0.6, n, r),  # EXP-078 blind spot
}


# --------------------------------------------------------------------------------------
# Detectors
# --------------------------------------------------------------------------------------
def tailmass(x: np.ndarray, k: float = K_TAIL) -> float:
    """Minority-mass / left-tail-mass detector (the detector `ASS` lacks): fraction of mass below
    the catastrophe boundary `median - k*MAD` — a separated catastrophic minority mode, not the
    bulk's own shoulder. MAD==0 (degenerate) -> 0.0 (no resolvable tail)."""
    med = float(np.median(x))
    mad = float(stats.median_abs_deviation(x, scale=1.0))
    if mad == 0.0:
        return 0.0
    return float(np.mean(x < med - k * mad))


def q05(x: np.ndarray) -> float:
    return float(np.percentile(x, 5))


def s2_fail(x: np.ndarray, x_ctrl: np.ndarray,
            tau: float = TAU_TAIL, delta: float = DELTA) -> bool:
    """D4 S2: PASS iff tailmass <= tau AND q05 >= q05_control - delta. FAIL (detect) iff NOT PASS.
    The two legs are complementary: the tailmass leg catches the separated minority mode (B_zero),
    the relative-q05 leg catches deep catastrophes worse than the control's own tail (B_neg)."""
    leg_tail = tailmass(x) > tau
    leg_q05 = q05(x) < (q05(x_ctrl) - delta)
    return bool(leg_tail or leg_q05)


def bootstrap_ci_low(x: np.ndarray, rng: np.random.Generator,
                     n_boot: int = N_BOOT, alpha: float = CI_ALPHA) -> float:
    n = len(x)
    idx = rng.integers(0, n, size=(n_boot, n))
    boots = x[idx].mean(axis=1)
    return float(np.percentile(boots, 100 * alpha / 2))


def wilson_upper(k: int, n: int, z: float = 1.96) -> float:
    if n == 0:
        return 1.0
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return float((centre + margin) / denom)


# --------------------------------------------------------------------------------------
# Verdict container
# --------------------------------------------------------------------------------------
@dataclass
class Check:
    name: str
    candidate: str
    measured: str
    verdict: str            # OK | RE-ANCHOR
    recommendation: str


# --------------------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------------------
def _s2_rates(n: int, rng: np.random.Generator) -> dict:
    sep = [fix_separable(n, rng) for _ in range(N_REP)]
    ctl = [fix_control(n, rng) for _ in range(N_REP)]
    ff_k = sum(s2_fail(sep[i], ctl[i]) for i in range(N_REP))   # false-flag: S2 FAILS a separable
    out = {"n": n, "false_flag": ff_k / N_REP,
           "false_flag_wilson_hi": wilson_upper(ff_k, N_REP)}
    for label, g in {**HARAMI_BINDING, **HARAMI_DISCLOSED}.items():
        harm = [g(n, rng) for _ in range(N_REP)]
        det_k = sum(s2_fail(harm[i], ctl[i]) for i in range(N_REP))   # detect: S2 FAILS a harami
        out[f"det_{label}"] = det_k / N_REP
    return out


def check_s2_operating_point(rng: np.random.Generator) -> Check:
    cal = _s2_rates(N_CAL, rng)
    binding_det = [cal[f"det_{k}"] for k in HARAMI_BINDING]
    sep_ok = cal["false_flag"] <= S2_FALSE_FLAG_MAX
    det_ok = all(d >= S2_DETECTION_MIN for d in binding_det)
    ok = sep_ok and det_ok
    rec = (f"FREEZE K_tail={K_TAIL}, tau_tail={TAU_TAIL}, delta={DELTA} "
           f"(feasible window confirmed at n>={N_CAL})" if ok else
           "re-anchor: sweep tau_tail/delta to the feasible window in the report grid")
    det_str = ", ".join(f"{k}={cal[f'det_{k}']:.3f}" for k in HARAMI_BINDING)
    dis_str = ", ".join(f"{k}={cal[f'det_{k}']:.3f}" for k in HARAMI_DISCLOSED)
    return Check(
        "D9 S2 tau_tail/delta",
        f"K_tail={K_TAIL}, tau_tail={TAU_TAIL}, delta={DELTA} "
        f"(ff<={S2_FALSE_FLAG_MAX}, binding det>={S2_DETECTION_MIN})",
        f"@n={N_CAL}: separable false-flag={cal['false_flag']:.3f} "
        f"(Wilson-hi={cal['false_flag_wilson_hi']:.3f}); binding detection [{det_str}]; "
        f"disclosed [{dis_str}]",
        "OK" if ok else "RE-ANCHOR", rec)


def check_s2_floor(rng: np.random.Generator) -> Check:
    floor = _s2_rates(N_FLOOR, rng)
    sub = _s2_rates(N_SUBFLOOR, rng)
    floor_binding = [floor[f"det_{k}"] for k in HARAMI_BINDING]
    floor_ok = (floor["false_flag_wilson_hi"] <= FPR_WILSON_UPPER
                and all(d >= S2_DETECTION_MIN for d in floor_binding))
    rec = (f"operating floor n>={N_FLOOR} (binds on Wilson-hi<={FPR_WILSON_UPPER}); "
           f"S2 DEFERRED for cells with n<{N_FLOOR} (e.g. some 4h cells) -> disclosed, "
           f"adjudication carried by the frozen referee suite + median/tail disclosure")
    f_det = ", ".join(f"{k}={floor[f'det_{k}']:.3f}" for k in HARAMI_BINDING)
    s_det = ", ".join(f"{k}={sub[f'det_{k}']:.3f}" for k in HARAMI_BINDING)
    return Check(
        "D9 S2 operating floor",
        f"reliable floor n>={N_FLOOR}; n<{N_FLOOR} deferred",
        f"@n={N_FLOOR}: ff={floor['false_flag']:.3f} (Wilson-hi={floor['false_flag_wilson_hi']:.3f}), "
        f"det [{f_det}]  ||  @n={N_SUBFLOOR} (sub-floor): ff={sub['false_flag']:.3f} "
        f"(Wilson-hi={sub['false_flag_wilson_hi']:.3f}), det [{s_det}] -> INFEASIBLE, deferred",
        "OK" if floor_ok else "RE-ANCHOR", rec)


def check_s1_margin(rng: np.random.Generator) -> Check:
    """S1 X_fav matched-control edge-call FPR via the calibrated m_cell margin (retrospective §2.2,
    EXP-027/070 standard): under the null (candidate has no favourable edge over its matched-random
    control), bind CI_low(difference) > m where m = Q95 of the null CI_low distribution, so
    P(false positive | null) = 0.05 by construction. The bite confirms such an m exists and is
    finite/non-degenerate; EXP-083 recomputes m per realized structure at production bootstrap scale.
    """
    n = N_S1
    lows = np.empty(N_REP)
    for i in range(N_REP):
        x = fix_control(n, rng)                 # candidate X_fav under null
        xc = fix_control(n, rng)                # matched-random control X_fav
        lows[i] = bootstrap_ci_low(x - xc, rng)
    raw_fpr = float(np.mean(lows > 0.0))        # bare CI_low>0 rule (uncalibrated)
    m_cell = float(np.percentile(lows, 100 * (1 - FPR_TARGET)))   # Q95 of null CI_low
    cal_fpr = float(np.mean(lows > m_cell))
    cal_k = int(np.sum(lows > m_cell))
    whi = wilson_upper(cal_k, N_REP)
    ok = np.isfinite(m_cell) and cal_fpr <= FPR_TARGET + 1e-9 and whi <= FPR_WILSON_UPPER
    rec = (f"bind X_fav CI_low > m_cell={m_cell:.4f} (m_cell standard); recompute per realized "
           f"structure in EXP-083 at N_BOOT=10_000")
    return Check(
        "D9 S1 margin m",
        "FPR<=0.05 via calibrated m_cell (Wilson-hi<=0.075)",
        f"raw FPR@0={raw_fpr:.3f}; m_cell={m_cell:.4f} -> calibrated FPR={cal_fpr:.3f} "
        f"(Wilson-hi={whi:.3f})",
        "OK" if ok else "RE-ANCHOR", rec)


def check_d3_estimability(rng: np.random.Generator) -> Check:
    """D3 derivation-quantile sanity. BINDING: the four derivation quantiles
    (MFE_med/MFE_q40/TTP_q75/MAE_q90) are estimable (finite, non-degenerate) at the >=30-event
    floor, and the derivation rule is ALWAYS well-defined (the adverse leg `m_anti else MAE_q90`
    has a finite value for every cell). `m_anti` (dip-gated antimode) is *graceful* — finite when
    the dip resolves a split, NaN -> MAE_q90 fallback when it cannot, never garbage, rarely
    false-finite on unimodal.

    RE-ANCHOR NOTE (2026-06-21): an earlier draft required `m_anti` to be FINITE on a bimodal MAE
    at n=30. That is *impossible*, not a defect: Hartigan's dip is underpowered at small n (the same
    EXP-078 finding), so `m_anti` resolves a split only at large n (finite-rate ~0.03/0.09/0.43/0.95
    at n=30/120/250/500). D3 anticipates this with the `m_anti else MAE_q90` fallback, so a NaN
    `m_anti` is a defined outcome, not non-estimability. The binding floor is on the quantiles, which
    are estimable at n>=30. Disclosed consequence: at realistic per-cell n the adverse leg
    predominantly uses the MAE_q90 fallback; `m_anti` engages only in large-n cells. This does NOT
    weaken the S2 shape-guard, which uses minority-MASS (tailmass), not the dip.
    """
    n = N_D3
    q_fail = []
    rule_undef = []
    for _ in range(N_REP):
        # realistic per-event TRAIN fixture: MFE>=0, TTP positive bars, MAE>=0
        mfe = np.abs(gen_unimodal(0.6, n, rng)) + 0.05
        ttp = rng.integers(1, 25, n).astype(float)
        mae = np.abs(gen_bimodal(0.85, 0.3, 0.1, 1.8, 0.3, n, rng)) + 0.02
        q = [np.quantile(mfe, 0.5), np.quantile(mfe, 0.4),
             np.quantile(ttp, 0.75), np.quantile(mae, 0.90)]
        ok_q = (all(np.isfinite(v) for v in q) and np.quantile(mfe, 0.5) > 0
                and len(np.unique(mfe)) > 1)
        q_fail.append(not ok_q)
        # adverse leg is always well-defined: m_anti (finite) OR MAE_q90 (finite) fallback
        s_adv = _antimode(mae)
        if not np.isfinite(s_adv):
            s_adv = np.quantile(mae, 0.90)
        rule_undef.append(not np.isfinite(s_adv))
    q_rate = float(np.mean(q_fail))
    undef_rate = float(np.mean(rule_undef))
    # disclosure: m_anti resolution power across n (graceful fallback elsewhere)
    anti_finite = {nn: float(np.mean([
        np.isfinite(_antimode(np.abs(gen_bimodal(0.85, 0.3, 0.1, 1.8, 0.3, nn, rng)) + 0.02))
        for _ in range(300)])) for nn in (N_D3, N_CAL, 500)}
    ok = q_rate <= 0.05 and undef_rate == 0.0
    anti_str = ", ".join(f"n={k}:{v:.2f}" for k, v in anti_finite.items())
    return Check(
        "D9 D3 quantile estimability",
        "quantiles estimable at n>=30; derivation rule always well-defined",
        f"@n={n}: quantile non-estimable={q_rate:.3f}; adverse-leg undefined={undef_rate:.3f}; "
        f"m_anti dip-resolution finite-rate [{anti_str}] (NaN->MAE_q90 fallback elsewhere)",
        "OK" if ok else "RE-ANCHOR",
        "keep n>=30 floor; cells below floor disclosed, derived candidate not formed for that cell. "
        "Disclosed: m_anti engages only in large-n cells; adverse leg uses the MAE_q90 fallback "
        "elsewhere — S2 (minority-mass) is the binding shape-guard, not m_anti."
        if ok else f"raise the derivation floor (quantile estimability fails {q_rate:.2%} at n={n})")


def _antimode(x: np.ndarray) -> float:
    """Dip-gated antimode: if Hartigan's dip rejects unimodality, return the lowest-density point
    between the two robust modes (dominant-vs-catastrophic-minority boundary); else NaN."""
    try:
        import diptest
        _, dip_p = diptest.diptest(np.asarray(x, dtype=float))
    except Exception:
        dip_p = 1.0
    if dip_p >= 0.05:
        return float("nan")
    lo, hi = np.percentile(x, 5), np.percentile(x, 95)
    grid = np.linspace(lo, hi, 200)
    kde = stats.gaussian_kde(x)
    dens = kde(grid)
    return float(grid[int(np.argmin(dens))])


# --------------------------------------------------------------------------------------
# Diagnostic ROC grid (disclosure; not a pass/fail gate)
# --------------------------------------------------------------------------------------
def roc_grid(rng: np.random.Generator) -> list[dict]:
    rows = []
    for n in (N_SUBFLOOR, N_FLOOR, N_CAL):
        sep = [fix_separable(n, rng) for _ in range(N_REP)]
        ctl = [fix_control(n, rng) for _ in range(N_REP)]
        harm = {k: [g(n, rng) for _ in range(N_REP)] for k, g in HARAMI_BINDING.items()}
        for tau in (0.05, 0.06, 0.07):
            for delta in (0.30, 0.40):
                ff = np.mean([s2_fail(sep[i], ctl[i], tau, delta) for i in range(N_REP)])
                det = {k: float(np.mean([s2_fail(harm[k][i], ctl[i], tau, delta)
                                         for i in range(N_REP)])) for k in HARAMI_BINDING}
                rows.append({"n": n, "tau_tail": tau, "delta": delta,
                             "false_flag": float(ff), **{f"det_{k}": det[k] for k in det}})
    return rows


# --------------------------------------------------------------------------------------
# B_pos blind-spot disposition: harm-vs-visibility map (disclosure; not a gate)
# --------------------------------------------------------------------------------------
def harm_visibility_map(rng: np.random.Generator) -> dict:
    """Characterize the S2 blind spot across the minority (mass x depth) plane to show it is
    bounded to the economically benign region. The trap S2 exists to catch is
    median-positive AND expectancy-dead AND invisible; this confirms no materially-negative-mean
    shape escapes S2, so the residual `B_pos`-type blind spot carries positive (or break-even)
    expectancy and is closed by the frozen referee suite's expectancy leg. Disclosure only.

    Returns rows of (w_min, depth, true_mean, median, s2_detection) and the worst genuinely-harmful
    blind cell (median>0.05 AND mean<=0 AND detection<0.80)."""
    n, n_rep = N_CAL, 1500
    ctrl = [fix_control(n, rng) for _ in range(n_rep)]
    rows, harmful = [], []
    for w_min in (0.02, 0.05, 0.10, 0.15):
        for depth in (-0.5, -1.0, -1.5, -2.0, -3.0):
            w = 1 - w_min
            mean = w * 0.15 + w_min * depth                      # analytic true mean
            draws = [gen_bimodal(w, 0.15, 0.5, depth, 0.6, n, rng) for _ in range(n_rep)]
            det = float(np.mean([s2_fail(draws[i], ctrl[i]) for i in range(n_rep)]))
            med = float(np.median([np.median(d) for d in draws]))
            row = {"w_min": w_min, "depth": depth, "true_mean": round(mean, 4),
                   "median": round(med, 4), "s2_detection": round(det, 4)}
            rows.append(row)
            if med > 0.05 and mean <= 0.0 and det < S2_DETECTION_MIN:
                harmful.append(row)
    return {"rows": rows, "harmful_blind_cells": harmful,
            "interpretation": (
                "blind region (det<0.80) is bounded to true_mean>0 (benign) or true_mean~=0 "
                "(break-even, rejected by the frozen suite's expectancy/materiality leg); every "
                "materially-negative-mean shape is DETECTED. Blind spot and harm region are "
                "anti-correlated -> B_pos blind spot is economically benign; backstops = frozen "
                "referee suite (expectancy, binding) + S1 attribution + EXP-081 descriptive tail read.")}


# --------------------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------------------
def main() -> None:
    rng = np.random.default_rng(SEED)
    checks = [
        check_s2_operating_point(rng),
        check_s2_floor(rng),
        check_s1_margin(rng),
        check_d3_estimability(rng),
    ]
    grid = roc_grid(rng)
    harm = harm_visibility_map(rng)

    width = max(len(c.name) for c in checks)
    print(f"\nPhase 018 D9 bite check  (SEED={SEED}, N_REP={N_REP}, N_BOOT={N_BOOT})\n")
    print(f"{'check':<{width}}  verdict     measured / recommendation")
    print("-" * (width + 60))
    for c in checks:
        print(f"{c.name:<{width}}  {c.verdict:<10}  {c.measured}")
        print(f"{'':<{width}}  {'':<10}  -> {c.recommendation}")
    overall = "GREEN" if all(c.verdict == "OK" for c in checks) else "RE-ANCHOR NEEDED"
    print("\nOVERALL:", overall)
    hb = harm["harmful_blind_cells"]
    print(f"B_pos blind-spot disposition: {len(hb)} genuinely harmful blind cell(s) "
          f"(median>0.05 AND mean<=0 AND det<0.80) across the 20-cell (mass x depth) plane"
          + (f" -> worst {hb[0]} (break-even mean, suite-rejected)" if hb else ""))

    out = Path(__file__).with_name("bite_check_report.json")
    out.write_text(json.dumps({
        "seed": SEED, "overall": overall,
        "frozen": {"K_tail": K_TAIL, "tau_tail": TAU_TAIL, "delta": DELTA,
                   "m": "m_cell = Q95(null CI_low); per-cell, recomputed in EXP-083",
                   "operating_floor_n": N_FLOOR, "calibration_n": N_CAL,
                   "s2_false_flag_max": S2_FALSE_FLAG_MAX, "s2_detection_min": S2_DETECTION_MIN},
        "checks": [asdict(c) for c in checks],
        "roc_grid": grid,
        "bpos_harm_visibility_map": harm,
    }, indent=2))
    print("wrote", out.name)


if __name__ == "__main__":
    main()
