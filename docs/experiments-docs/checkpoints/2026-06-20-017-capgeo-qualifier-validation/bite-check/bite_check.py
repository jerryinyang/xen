"""Phase 017 D2 bite check — pre-G0 threshold calibration (NOT an experiment).

Confirms each candidate threshold in `D0-predeclarations.md` §D2 is neither vacuous
(passes regardless) nor impossible (fails when the estimator is correct), and reports a
re-anchored value where a candidate fails. Uses a deliberately minimal reference estimator
(shrinkage-weighted sample statistics + bootstrap; closed-form shape proxies) — the full ASS
pipeline is validated separately in EXP-076-078. No market data, no holdout, no slot.

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
# Constants (mirror D0 candidate values; SEED = collection date)
# --------------------------------------------------------------------------------------
SEED = 20260620
N_REP = 1000            # replicate draws per (type, n) for rate/coverage estimates (bite scale)
N_BOOT = 2000           # bootstrap draws per replicate (bite scale; production = 10_000)
CI_ALPHA = 0.10         # 90% CI
N_GROUND = 10_000_000   # MC draws for ground-truth median
N_RECOVERY = 250        # sample size for the recovery/coverage bite (mid-range n)
N_FPR = 250             # sample size for the FPR bite
N_SHAPE = 500           # sample size for the shape-ROC bite

# D2 candidate thresholds under test
# Re-anchored 0.5 -> 0.85 after the 2026-06-20 bite check: median|err| of an UNBIASED
# estimator floors at 0.6745*SE (half-normal median), so 0.5 was impossible; 0.85 clears the
# correct estimator with ~20% margin while still failing a >=1*SE systematic bias.
RECOVERY_FACTOR = 0.85      # median|estimate - truth| <= RECOVERY_FACTOR * SE_true
COVERAGE_BAND = (0.86, 0.94)
FPR_TARGET = 0.05
FPR_WILSON_UPPER = 0.075
TAU_GAP_CANDIDATE = 0.30
SHAPE_FALSE_FLAG_MAX = 0.05
SHAPE_DETECTION_MIN = 0.80


# --------------------------------------------------------------------------------------
# D1 synthetic data-generating processes
# --------------------------------------------------------------------------------------
def gen_unimodal(mu: float, n: int, rng: np.random.Generator) -> np.ndarray:
    return rng.normal(mu, 1.0, n)


def gen_skewnormal(xi: float, omega: float, alpha: float, n: int,
                   rng: np.random.Generator) -> np.ndarray:
    return stats.skewnorm.rvs(a=alpha, loc=xi, scale=omega, size=n, random_state=rng)


def gen_bimodal(w: float, mu1: float, s1: float, mu2: float, s2: float, n: int,
                rng: np.random.Generator) -> np.ndarray:
    comp = rng.random(n) < w
    out = np.where(comp, rng.normal(mu1, s1, n), rng.normal(mu2, s2, n))
    return out


# D1 family registry (label -> sampler closure, truth dict)
def bimodal_truth(w, mu1, s1, mu2, s2, rng):
    mean = w * mu1 + (1 - w) * mu2
    draws = gen_bimodal(w, mu1, s1, mu2, s2, N_GROUND, rng)
    return {"mean": mean, "median": float(np.median(draws))}


# --------------------------------------------------------------------------------------
# Reference estimator (minimal ASS proxy) + bootstrap
# --------------------------------------------------------------------------------------
def expectancy_hat(x: np.ndarray) -> float:
    """Bite-scale expectancy = sample mean (single-type; no pooled shrinkage needed)."""
    return float(np.mean(x))


def bootstrap_ci(x: np.ndarray, stat_fn, rng: np.random.Generator,
                 n_boot: int = N_BOOT, alpha: float = CI_ALPHA) -> tuple[float, float]:
    n = len(x)
    idx = rng.integers(0, n, size=(n_boot, n))
    boots = np.array([stat_fn(x[i]) for i in idx])
    lo, hi = np.percentile(boots, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi)


# --------------------------------------------------------------------------------------
# Shape diagnostic (bite proxy): robust mean-median gap
# --------------------------------------------------------------------------------------
def mean_median_gap(x: np.ndarray) -> float:
    mad = stats.median_abs_deviation(x, scale=1.0)
    if mad == 0:
        return 0.0
    return float(abs(np.mean(x) - np.median(x)) / mad)


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
def check_recovery(rng: np.random.Generator) -> Check:
    mu, n = 0.10, N_RECOVERY
    se_true = 1.0 / np.sqrt(n)
    correct_err, biased_err = [], []
    for _ in range(N_REP):
        x = gen_unimodal(mu, n, rng)
        correct_err.append(abs(expectancy_hat(x) - mu))
        biased_err.append(abs(expectancy_hat(x) + 1.0 * se_true - mu))  # +1*SE bias
    correct_med = float(np.median(correct_err))
    biased_med = float(np.median(biased_err))
    band = RECOVERY_FACTOR * se_true
    correct_pass = correct_med <= band
    biased_fail = biased_med > band
    ok = correct_pass and biased_fail
    rec = (f"keep {RECOVERY_FACTOR}" if ok else
           f"set factor ~{correct_med / se_true:.2f} (correct estimator median |bias|/SE)")
    return Check(
        "D2.1 recovery bias", f"|bias| <= {RECOVERY_FACTOR}*SE ({band:.4f})",
        f"correct med|bias|={correct_med:.4f} (pass={correct_pass}); "
        f"+1SE-biased med|bias|={biased_med:.4f} (fails={biased_fail})",
        "OK" if ok else "RE-ANCHOR", rec)


def check_coverage(rng: np.random.Generator) -> Check:
    mu, n = 0.10, N_RECOVERY
    covered = 0
    for _ in range(N_REP):
        x = gen_unimodal(mu, n, rng)
        lo, hi = bootstrap_ci(x, expectancy_hat, rng)
        covered += int(lo <= mu <= hi)
    cov = covered / N_REP
    ok = COVERAGE_BAND[0] <= cov <= COVERAGE_BAND[1]
    mc = 1.96 * np.sqrt(cov * (1 - cov) / N_REP)
    rec = ("keep [0.86,0.94]" if ok else
           f"re-anchor band to {cov:.3f} +/- {mc:.3f}")
    return Check(
        "D2.1 coverage", f"90% CI coverage in {COVERAGE_BAND}",
        f"measured coverage={cov:.3f} (+/-{mc:.3f} MC)",
        "OK" if ok else "RE-ANCHOR", rec)


def check_fpr(rng: np.random.Generator) -> Check:
    """FPR is bound by a calibrated one-sided margin (m_cell analog, retrospective §2.2):
    bind `CI_low > m`, where m = Q95 of the null CI_low, so P(false positive | null) = 0.05 by
    construction. The bite confirms such an m exists and is finite/non-degenerate; EXP-077
    recomputes m per realized structure at production bootstrap scale.
    """
    n = N_FPR
    lows = []
    for _ in range(N_REP):
        x = gen_unimodal(0.0, n, rng)               # null: mu = 0
        lo, _ = bootstrap_ci(x, expectancy_hat, rng)
        lows.append(lo)
    lows = np.array(lows)
    raw_fpr = float(np.mean(lows > 0.0))            # bare CI_low>0 rule (uncalibrated)
    m_cell = float(np.percentile(lows, 100 * (1 - FPR_TARGET)))   # Q95 of null CI_low
    cal_fpr = float(np.mean(lows > m_cell))         # ~0.05 by construction
    ok = np.isfinite(m_cell) and cal_fpr <= FPR_TARGET + 1e-9
    rec = (f"bind CI_low > m_cell={m_cell:.4f} (m_cell analog); recompute per realized "
           f"structure in EXP-077 at N_BOOT=10_000")
    return Check(
        "D2.2 FPR", "FPR<=0.05 via calibrated margin (m_cell)",
        f"raw FPR@0={raw_fpr:.3f}; m_cell={m_cell:.4f} -> calibrated FPR={cal_fpr:.3f}",
        "OK" if ok else "RE-ANCHOR", rec)


def check_shape_roc(rng: np.random.Generator) -> Check:
    n = N_SHAPE
    # negatives: U family; positives: B family (median-positive, mean<=0 bimodal)
    neg = [mean_median_gap(gen_unimodal(0.10, n, rng)) for _ in range(N_REP)]
    pos = [mean_median_gap(gen_bimodal(0.85, 0.15, 0.5, -2.0, 0.6, n, rng))
           for _ in range(N_REP)]
    neg, pos = np.array(neg), np.array(pos)
    # sweep tau, find feasible window {false_flag<=0.05 and detection>=0.80}
    taus = np.linspace(0.0, 1.0, 201)
    feasible = []
    for t in taus:
        ff = float(np.mean(neg > t))
        det = float(np.mean(pos > t))
        if ff <= SHAPE_FALSE_FLAG_MAX and det >= SHAPE_DETECTION_MIN:
            feasible.append(t)
    cand_ff = float(np.mean(neg > TAU_GAP_CANDIDATE))
    cand_det = float(np.mean(pos > TAU_GAP_CANDIDATE))
    cand_ok = cand_ff <= SHAPE_FALSE_FLAG_MAX and cand_det >= SHAPE_DETECTION_MIN
    if feasible:
        window = f"[{min(feasible):.3f}, {max(feasible):.3f}]"
        mid = float(np.median(feasible))
    else:
        window, mid = "EMPTY", float("nan")
    rec = ("keep 0.30" if cand_ok else
           (f"re-anchor tau_gap ~{mid:.3f} (feasible {window})" if feasible
            else "no feasible tau on gap proxy alone -> rely on dip-test leg in EXP-078"))
    return Check(
        "D2.5 shape tau_gap", f"tau_gap={TAU_GAP_CANDIDATE} (ff<=0.05, det>=0.80)",
        f"@0.30 false_flag={cand_ff:.3f}, detection={cand_det:.3f}; feasible {window}",
        "OK" if cand_ok else "RE-ANCHOR", rec)


# --------------------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------------------
def main() -> None:
    rng = np.random.default_rng(SEED)
    checks = [
        check_recovery(rng),
        check_coverage(rng),
        check_fpr(rng),
        check_shape_roc(rng),
    ]
    width = max(len(c.name) for c in checks)
    print("\nPhase 017 D2 bite check  (SEED=%d, N_REP=%d, N_BOOT=%d)\n" % (SEED, N_REP, N_BOOT))
    print(f"{'check':<{width}}  verdict     measured / recommendation")
    print("-" * (width + 60))
    for c in checks:
        print(f"{c.name:<{width}}  {c.verdict:<10}  {c.measured}")
        print(f"{'':<{width}}  {'':<10}  -> {c.recommendation}")
    overall = "GREEN" if all(c.verdict == "OK" for c in checks) else "RE-ANCHOR NEEDED"
    print("\nOVERALL:", overall)

    out = Path(__file__).with_name("bite_check_report.json")
    out.write_text(json.dumps(
        {"seed": SEED, "overall": overall, "checks": [asdict(c) for c in checks]}, indent=2))
    print("wrote", out.name)


if __name__ == "__main__":
    main()
