"""Signal-quality evaluation toolbox (INFR-001 WS-7; INFR-022 zero-cost + powering strip).

Informative evidence only: no MDE, no cost, no power floors; PSR + sample-size context only.

Replaces the frozen monolithic referee stack (`referee_adaptive` / `referee_pstar` /
`referee_calibration` / `incremental_referee`) for NEW adjudication. Those modules stay
byte-frozen for historical reproducibility but are retired from service: their multi-gate
conjunctions, readiness floors, and materiality thresholds selected fragile gate-threaders
and vetoed robust candidates (L-17, B-5/B-7; operator decision 2026-07-04).

INFR-022 (operator directive 2026-08-08) — binding frame:
* **Zero cost model.** No spread, commission, or swap enters any calculation programme-wide
  unless an explicit operator cost directive (recorded in the experiment's design.md)
  requests costs. Every money-bearing report carries the zero-cost caveat
  (`zero_cost_caveat`, `ZERO_COST_DISCLOSURE`). The retired cost stack lives in
  `xen.evaluation_cost_legacy` (ARCHIVED banner; not callable from any live path).
* **No MDE / no powering.** `mde`, `powered_label`, `cost_sensitivity` and all detection
  floors were removed (L-63). Retained: sample-size *context* (never a hide/drop rule) and
  DIRECT comparisons against a pre-specified baseline. No arbitrary threshold or gate on
  realised estimates.
* **PSR.** Probabilistic Sharpe Ratio (Bailey & López de Prado 2012, skew/kurt-adjusted)
  is reported beside every mean per-trade/leg bps read, on the same trade series (`psr`,
  `psr_row`). PSR is evidence, never a gate.

Design frame:
* **Validity is gated elsewhere** — leak tripwire, holdout, causality, and the per-bar↔per-leg
  reconciliation live in `xen.estimand_validation` and the analyst's integrity phase.
* **Everything here is evidence** — effect sizes with CIs, exposure-honest economics,
  robustness curves. No function returns a verdict; the operator judges value.
* **Candidate-aware composition** — the Quant Designer picks which pieces apply and on which
  estimand (per-leg, episode, per-active-bar), derived from the candidate's own mechanism.
  There is no fixed stack to "pass".

Exposure-honesty contract (operator feedback 2026-07-04): a part-time strategy is never
compared raw against 100%-exposed buy-and-hold. Report occupancy, time-averaged and peak
deployed exposure, return per unit exposure-time, and the B&H benchmark scaled to the same
exposure profile — both normalizations, judgment left to the reader.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Callable

import numpy as np

from xen.adjudication import MultiLegSeries

DEFAULT_N_BOOT = 10_000
DEFAULT_BLOCK = 5
DEFAULT_ALPHA = 0.05
DEFAULT_N_SEEDS = 5   # INFR-004 F2: seed battery — one draw is a noisy yardstick (L-19)

# INFR-004 F5: approved reporting language for a CI that clears zero. A percentile bootstrap
# CI is NOT a hypothesis test; report the interval, do not claim a p-value.
#   USE:  "bootstrap 95% CI excludes zero"
#   NOT:  "data this extreme would occur <5% of the time if the true effect were 0"
CI_EXCLUDES_ZERO_PHRASE = "bootstrap 95% CI excludes zero"


def trimmed_mean(x: np.ndarray, *, trim: float = 0.2) -> float:
    """Symmetric trimmed mean (drops ``trim`` from each tail) — outlier-robust stat for
    ``block_bootstrap_ci``. INFR-004 F4 robustness disclosure alongside np.mean/np.median."""
    a = np.sort(np.asarray(x, dtype=float))
    k = int(np.floor(len(a) * trim))
    core = a[k:len(a) - k] if len(a) - 2 * k > 0 else a
    return float(core.mean())


# --------------------------------------------------------------------------- #
# Core statistics
# --------------------------------------------------------------------------- #
def block_bootstrap_ci(x: np.ndarray, stat: Callable[[np.ndarray], float] = np.mean, *,
                       block: int = DEFAULT_BLOCK, n_boot: int = DEFAULT_N_BOOT,
                       alpha: float = DEFAULT_ALPHA, seed: int = 0,
                       n_seeds: int = DEFAULT_N_SEEDS) -> dict:
    """Circular-block bootstrap CI over a time-ordered sample. Returns evidence, not a verdict.

    INFR-004 hardening:
      * F1 — effective block is capped to ``[1, n-1]`` and starts are drawn over the full
        circular range ``[0, n)``. The prior code truncated starts to ``[0, n-block)`` and
        wrapped with ``% n``; for ``n <= block+1`` (and for ``block >= n``) every resample
        collapsed to the original series, emitting a **zero-width CI** — false certainty on
        sparse strata. The cap + full circular range guarantee genuine resampling for any n>=2.
      * F2 — the CI is aggregated across an ``n_seeds`` battery (median of each bound); the
        per-seed spread of each bound is reported as ``ci_low_seed_range`` / ``ci_high_seed_range``
        so Monte-Carlo noise near the zero boundary is visible, not hidden behind one draw (L-19).
    """
    n = len(x)
    if n == 0:
        return {"n": 0, "block": 0, "stat": float("nan"), "ci": [float("nan")] * 2,
                "ci_low_seed_range": [float("nan")] * 2, "ci_high_seed_range": [float("nan")] * 2}
    if n == 1:
        return {"n": 1, "block": 1, "stat": float(x[0]), "ci": [float(x[0])] * 2,
                "ci_low_seed_range": [float(x[0])] * 2, "ci_high_seed_range": [float(x[0])] * 2}
    eff_block = max(1, min(int(block), n - 1))          # F1: keep block strictly < n
    n_blocks = int(np.ceil(n / eff_block))
    lo = np.empty(n_seeds)
    hi = np.empty(n_seeds)
    for s in range(n_seeds):
        rng = np.random.default_rng(seed + s)
        starts = rng.integers(0, n, size=(n_boot, n_blocks))   # F1: full circular start range
        stats = np.empty(n_boot)
        for b in range(n_boot):
            idx = (starts[b][:, None] + np.arange(eff_block)[None, :]).ravel()[:n] % n
            stats[b] = stat(x[idx])
        lo[s] = np.quantile(stats, alpha / 2)
        hi[s] = np.quantile(stats, 1 - alpha / 2)
    return {"n": n, "block": eff_block, "stat": float(stat(x)),
            "ci": [float(np.median(lo)), float(np.median(hi))],
            "ci_low_seed_range": [float(lo.min()), float(lo.max())],
            "ci_high_seed_range": [float(hi.min()), float(hi.max())]}


def block_sensitivity(x: np.ndarray, blocks: list[int], *,
                      stat: Callable[[np.ndarray], float] = np.mean, n_boot: int = DEFAULT_N_BOOT,
                      alpha: float = DEFAULT_ALPHA, seed: int = 0,
                      n_seeds: int = DEFAULT_N_SEEDS) -> list[dict]:
    """CI at each requested block length (INFR-004 F3). If the sign of ``ci[0]`` changes
    across a sensible block range the inference is block-fragile — evidence, never a verdict.
    Each row carries the effective ``block`` actually used."""
    out = []
    for bl in blocks:
        r = block_bootstrap_ci(x, stat, block=bl, n_boot=n_boot, alpha=alpha, seed=seed,
                               n_seeds=n_seeds)
        out.append({"block_req": int(bl), **r})
    return out


# --------------------------------------------------------------------------- #
# Zero-cost model (INFR-022 directive 1)
# --------------------------------------------------------------------------- #
ZERO_COST_DISCLOSURE: dict[str, object] = {
    "cost_model": "NO_COST_CHARGED",
    "spread": "not modeled",
    "commissions": "not modeled",
    "swaps/funding": "not modeled",
    "implication": (
        "every figure in this document is gross and cost-free; no spread, commission, or "
        "swap enters any calculation. Realised results would differ (likely worse) under "
        "any real cost schedule."
    ),
    "prohibited_claims": ["fully-net", "cost-complete", "tradable", "deployable"],
    "lifting": (
        "only an explicit operator directive may introduce a cost model for a scoped "
        "experiment; the directive is recorded in that experiment's design.md."
    ),
}


def zero_cost_caveat() -> str:
    """Canonical zero-cost disclosure text (INFR-022 §3.1) — must appear VERBATIM on every
    report, analysis and results document."""
    return (
        "ZERO-COST-DISCLOSURE\n"
        "  cost_model: NO_COST_CHARGED\n"
        "  spread: not modeled\n"
        "  commissions: not modeled\n"
        "  swaps/funding: not modeled\n"
        "  implication: every figure in this document is gross and cost-free; no spread,\n"
        "    commission, or swap enters any calculation. Realised results would differ\n"
        "    (likely worse) under any real cost schedule.\n"
        "  prohibited_claims: fully-net, cost-complete, tradable, deployable\n"
        "  lifting: only an explicit operator directive may introduce a cost model for a\n"
        "    scoped experiment; the directive is recorded in that experiment's design.md."
    )


def assert_zero_cost(**kwargs) -> None:
    """Raise unless every cost-related parameter is inert (0 / None / False).

    INFR-022 §3.2: no cost function is called in any live path; cost parameters are
    pinned to their zero value and enforced by asserts where they exist. A non-zero cost
    parameter without an operator directive is a governance violation.
    """
    offending = {k: v for k, v in kwargs.items() if v not in (0, 0.0, None, False)}
    if offending:
        raise ValueError(
            "zero-cost model violated (INFR-022): non-inert cost parameter(s) "
            f"{offending} — no spread, commission, or swap may enter any live calculation "
            "unless an explicit operator cost directive is recorded in the design"
        )


# --------------------------------------------------------------------------- #
# PSR — Probabilistic Sharpe Ratio (INFR-022 directive 4)
# --------------------------------------------------------------------------- #
def _normal_cdf(z: float) -> float:
    """Standard normal CDF via erf (pure; no scipy dependency)."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def psr(per_trade_bps: np.ndarray, *, sr_star: float = 0.0) -> dict:
    """Probabilistic Sharpe Ratio (Bailey & López de Prado, 2012), skew/kurtosis-adjusted.

    Computed from the SAME per-trade series as the mean-trade (bps) figure it accompanies:
    ``SR_hat`` is the **per-trade** Sharpe (mean/std of that series — not annualised),
    ``n`` the number of trades in that population, ``gamma3``/``gamma4`` the empirical
    skewness/kurtosis of the same vector. Empirical moments only — no normality assumption.
    Default ``sr_star = 0`` (design may override).

    PSR is **evidence, never a gate**. ``n < 2`` or non-finite moments → ``psr = NaN`` with
    ``n`` stated; the row is still reported (N3).
    """
    x = np.asarray(per_trade_bps, dtype=float)
    n = int(len(x))
    if n < 2 or not np.all(np.isfinite(x)):
        return {"psr": float("nan"), "n": n,
                "sr_hat": float("nan"), "skew": float("nan"), "kurt": float("nan")}
    mean = float(x.mean())
    sd = float(x.std())
    if sd <= 0.0:
        # degenerate constant series: SR_hat undefined → NaN (moments undefined)
        return {"psr": float("nan"), "n": n,
                "sr_hat": float("nan"), "skew": float("nan"), "kurt": float("nan")}
    sr_hat = mean / sd
    dev = x - mean
    g3 = float((dev ** 3).mean() / sd ** 3)      # empirical skewness (population form)
    g4 = float((dev ** 4).mean() / sd ** 4)      # empirical kurtosis (population form)
    denom2 = 1.0 - g3 * sr_hat + (g4 - 1.0) / 4.0 * sr_hat ** 2
    if denom2 <= 0.0:
        # variance term non-positive → PSR undefined on this series
        return {"psr": float("nan"), "n": n, "sr_hat": sr_hat, "skew": g3, "kurt": g4}
    z = (sr_hat - float(sr_star)) * math.sqrt(n - 1) / math.sqrt(denom2)
    return {"psr": float(_normal_cdf(z)), "n": n, "sr_hat": sr_hat, "skew": g3, "kurt": g4}


def psr_row(per_trade_bps: np.ndarray, *, sr_star: float = 0.0) -> dict:
    """PSR row fragment for analysis tables / dict rows: ``psr`` + ``psr_n`` beside the
    mean-trade bps column, on the SAME series (INFR-022 §4.2 pairing rule)."""
    out = psr(per_trade_bps, sr_star=sr_star)
    return {"psr": out["psr"], "psr_n": int(out["n"])}


# --------------------------------------------------------------------------- #
# Exposure-honest economics
# --------------------------------------------------------------------------- #
def exposure_metrics(series: MultiLegSeries, *, real_open: np.ndarray) -> dict:
    """Occupancy, deployed exposure, and return normalized both ways, with the B&H benchmark
    scaled to the strategy's exposure profile. All fields disclosed; none binding.
    """
    t = series.times.astype("datetime64[s]").astype("int64")
    years = max(float(t[-1] - t[0]) / (365.25 * 24 * 3600), 1e-9)
    bars_per_year = len(t) / years
    net = series.net_bps
    total = float(net.sum())
    occ = float((series.open_legs > 0).mean())
    avg_exp_all = float(series.open_legs.mean())                       # capital-time deployed
    active = series.open_legs > 0
    avg_exp_active = float(series.open_legs[active].mean()) if active.any() else float("nan")
    peak = int(series.open_legs.max())

    ann_on_unit = total / 1e4 / years                                   # per 1-unit notional
    ann_on_avg_exposure = (ann_on_unit / avg_exp_all) if avg_exp_all > 0 else float("nan")
    ann_on_peak_exposure = (ann_on_unit / peak) if peak > 0 else float("nan")

    bh_ret = np.diff(np.log(real_open))
    bh_ann = float(bh_ret.sum() / years)
    bh_vol = float(bh_ret.std() * np.sqrt(bars_per_year))
    cum = np.cumsum(net)
    return {
        "years": years, "occupancy": occ,
        "avg_exposure_legs_all_bars": avg_exp_all,
        "avg_exposure_legs_active_bars": avg_exp_active,
        "peak_exposure_legs": peak,
        "ann_return_on_unit_notional": ann_on_unit,
        "ann_return_on_avg_exposure": ann_on_avg_exposure,
        "ann_return_on_peak_exposure": ann_on_peak_exposure,
        "max_drawdown_bps_unit": float((cum - np.maximum.accumulate(cum)).min()),
        "bh_ann_return": bh_ann,
        "bh_ann_vol": bh_vol,
        "bh_exposure_time_matched_return": bh_ann * occ,   # B&H held only the strategy's
        #                                                    active fraction of the time
    }


def collapse_fraction(raw_effect: float, control_effect: float) -> float:
    """Continuous control disclosure (L-15): control/raw. Never reduced to survive/die."""
    return float(control_effect / raw_effect) if abs(raw_effect) > 1e-12 else float("nan")


# --------------------------------------------------------------------------- #
# Frozen spread-quarantine provenance (kept live — data provenance, not a cost read)
# --------------------------------------------------------------------------- #
CHAPTER05_INFR017_PIN_SHA256 = (
    "e3b9fd9b9b5851b8a9a11f9ce34cd1e0fa8e10ea1fe1b210bd0090da379e6225"
)
CHAPTER05_INFR017_COLUMN_PINS = (
    Path(__file__).resolve().parents[3]
    / "archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-017/results/column_pins.json"
)


def verify_chapter05_spread_quarantine(path: str | Path | None = None) -> dict:
    """Verify the frozen artifact that declares the stored spread field unusable."""
    artifact_path = Path(path) if path is not None else CHAPTER05_INFR017_COLUMN_PINS
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    stable_payload = {
        key: value
        for key, value in payload.items()
        if key not in {"generated_utc", "pin_sha256"}
    }
    actual_sha = hashlib.sha256(
        json.dumps(stable_payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    recorded_sha = payload.get("pin_sha256")
    if actual_sha != recorded_sha or actual_sha != CHAPTER05_INFR017_PIN_SHA256:
        raise ValueError(
            "INFR-017 pin_sha256 mismatch: "
            f"computed={actual_sha}, recorded={recorded_sha}, "
            f"expected={CHAPTER05_INFR017_PIN_SHA256}"
        )
    status = payload["W2_decision"]["stored_column_status"]
    if status != "UNUSABLE":
        raise ValueError(f"INFR-017 stored column status changed: {status!r}")
    return {
        "source": str(artifact_path),
        "pin_sha256": actual_sha,
        "stored_column_status": status,
    }


def split_by(values: np.ndarray, labels: np.ndarray, *, block: int = DEFAULT_BLOCK,
             n_boot: int = DEFAULT_N_BOOT, alpha: float = DEFAULT_ALPHA,
             seed: int = 0) -> dict:
    """Per-label mean+CI table (year splits, regime splits, strata). Pooled = disclosure only."""
    out = {}
    for lab in sorted(set(labels.tolist())):
        out[str(lab)] = block_bootstrap_ci(values[labels == lab], np.mean, block=block,
                                           n_boot=n_boot, alpha=alpha, seed=seed)
    out["_pooled_disclosure_only"] = block_bootstrap_ci(values, np.mean, block=block,
                                                        n_boot=n_boot, alpha=alpha, seed=seed)
    return out
