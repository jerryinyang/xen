"""Signal-quality evaluation toolbox (INFR-001 WS-7) — informative, never gating.

Replaces the frozen monolithic referee stack (`referee_adaptive` / `referee_pstar` /
`referee_calibration` / `incremental_referee`) for NEW adjudication. Those modules stay
byte-frozen for historical reproducibility but are retired from service: their multi-gate
conjunctions, readiness floors, and materiality thresholds selected fragile gate-threaders
and vetoed robust candidates (L-17, B-5/B-7; operator decision 2026-07-04).

Design frame:
* **Validity is gated elsewhere** — leak tripwire, holdout, causality, and the per-bar↔per-leg
  reconciliation live in `xen.estimand_validation` and the analyst's integrity phase.
* **Everything here is evidence** — effect sizes with CIs, exposure-honest economics,
  robustness curves, power. No function returns a verdict; the operator judges value.
* **Candidate-aware composition** — the Quant Designer picks which pieces apply and on which
  estimand (per-leg, episode, per-active-bar), derived from the candidate's own mechanism.
  There is no fixed stack to "pass".

Exposure-honesty contract (operator feedback 2026-07-04): a part-time strategy is never
compared raw against 100%-exposed buy-and-hold. Report occupancy, time-averaged and peak
deployed exposure, return per unit exposure-time, and the B&H benchmark scaled to the same
exposure profile — both normalizations, judgment left to the reader.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
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
    """CI at each requested block length (INFR-004 F3). Mirrors ``cost_sensitivity``: if the
    sign of ``ci[0]`` changes across a sensible block range the inference is block-fragile —
    evidence, never a verdict. Each row carries the effective ``block`` actually used."""
    out = []
    for bl in blocks:
        r = block_bootstrap_ci(x, stat, block=bl, n_boot=n_boot, alpha=alpha, seed=seed,
                               n_seeds=n_seeds)
        out.append({"block_req": int(bl), **r})
    return out


def mde(x: np.ndarray, *, block: int = DEFAULT_BLOCK, n_boot: int = DEFAULT_N_BOOT,
        alpha: float = DEFAULT_ALPHA, seed: int = 0) -> float:
    """Minimum detectable mean shift: the smallest planted constant that lifts CI_low above 0.

    Computed as the half-width of the bootstrap CI of the mean around its point value —
    the shift needed for the observed sampling noise to clear zero. Cells whose plausible
    effect < MDE are UNPOWERED and must never be read as negatives.
    """
    r = block_bootstrap_ci(x, np.mean, block=block, n_boot=n_boot, alpha=alpha, seed=seed)
    if r["n"] < 2:
        return float("nan")
    return float(r["stat"] - r["ci"][0])


def powered_label(x: np.ndarray, plausible_effect: float, **kw) -> dict:
    """{'mde', 'plausible_effect', 'powered'} — a negative is reportable only when powered."""
    m = mde(x, **kw)
    return {"mde": m, "plausible_effect": plausible_effect,
            "powered": bool(np.isfinite(m) and m <= plausible_effect)}


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


# --------------------------------------------------------------------------- #
# Robustness disclosures
# --------------------------------------------------------------------------- #
def cost_sensitivity(gross_per_leg: np.ndarray, costs: list[float], *,
                     block: int = DEFAULT_BLOCK, n_boot: int = DEFAULT_N_BOOT,
                     alpha: float = DEFAULT_ALPHA, seed: int = 0) -> list[dict]:
    """Net per-leg mean + CI at each candidate round-trip cost. Where the CI dies is evidence."""
    out = []
    for c in costs:
        r = block_bootstrap_ci(gross_per_leg - c, np.mean, block=block, n_boot=n_boot,
                               alpha=alpha, seed=seed)
        out.append({"cost_bps": float(c), **r})
    return out


def collapse_fraction(raw_effect: float, control_effect: float) -> float:
    """Continuous control disclosure (L-15): control/raw. Never reduced to survive/die."""
    return float(control_effect / raw_effect) if abs(raw_effect) > 1e-12 else float("nan")


# --------------------------------------------------------------------------- #
# Declared trading-cost table (EXP-019, CF-VOLHARV-001)
# --------------------------------------------------------------------------- #
# Source: FTMO published symbol specifications, https://ftmo.com/wp-json/ftmo/symbols
# (the data feed behind https://ftmo.com/en/symbols/), snapshot 2026-07-04. Values verbatim.
# Operator directive 2026-07-04 (EXP-019 deviation D5): cost basis = FTMO commissions +
# spread; swap DISREGARDED (design §6 swap table superseded).
#   * commission / commission_type: FTMO's published per-lot commission.
#     "flat_USD"  = fixed USD per 1 standard lot, ROUND TRIP (operator-confirmed 2026-07-07):
#                   the $5 figure is the full round-turn charge, so it is applied ONCE and is
#                   NOT scaled by ``commission_events``. As bps of notional it depends on the
#                   USD notional of one lot, which is currency-convention-specific — computed by
#                   ``usd_notional_per_lot`` (XXXUSD = contract_size·price; USDXXX = contract_size;
#                   cross = contract_size·base_usd_rate, which must be pinned explicitly).
#                   The ``pip_commission_per_lot`` field (FTMO's ~$3/lot ≈ 0.3 pips on EURUSD)
#                   is recorded verbatim for disclosure only and is NO LONGER used in the cost
#                   conversion (it disagrees with the authoritative $5 flat).
#     "percent"   = percent of notional per event; price-free (charged on the traded amount,
#                   not entry price). ``commission_basis`` ∈ {"per_side","round_turn"} pins the
#                   convention: "per_side" scales by ``commission_events`` (x2 for a round trip),
#                   "round_turn" is charged once. Default "per_side"; verify vs FTMO per symbol —
#                   a wrong per-side assumption on a round-turn % overstates the fee 2x.
#     Informative, never gating.
#   * spread_pips: NOT statically published (live-ticker only). Must be read off the live
#     FTMO page at analysis time and pinned here before the binding cost read; the design's
#     1x/2x stress read (§6) then applies to commission + spread jointly.
#   * pip_conversion: price units per pip; contract_size: units per 1.0 lot.
FTMO_COST_SNAPSHOT = "2026-07-06 https://ftmo.com/wp-json/ftmo/symbols"
FTMO_COSTS: dict[str, dict] = {
    # symbol: contract_size, digits, pip_conversion, commission, commission_type,
    #         usd_commission_per_lot, pip_commission_per_lot (FTMO-published pips), spread_pips
    # --------------------------------------------------------------------------- #
    # Forex — majors (all flat $5/lot USD commission)
    # --------------------------------------------------------------------------- #
    "EURUSD": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.30, "spread_pips": None},
    "GBPUSD": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.30, "spread_pips": None},
    "USDJPY": {"contract_size": 100000, "digits": 3, "pip_conversion": 0.01,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.48, "spread_pips": None},
    "USDCHF": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.27, "spread_pips": None},
    "USDCAD": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.41, "spread_pips": None},
    "AUDUSD": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.30, "spread_pips": None},
    "NZDUSD": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.30, "spread_pips": None},
    # Forex — crosses
    "EURJPY": {"contract_size": 100000, "digits": 3, "pip_conversion": 0.01,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.48, "spread_pips": None},
    "GBPJPY": {"contract_size": 100000, "digits": 3, "pip_conversion": 0.01,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.48, "spread_pips": None},
    "AUDJPY": {"contract_size": 100000, "digits": 3, "pip_conversion": 0.01,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.48, "spread_pips": None},
    "EURCHF": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.27, "spread_pips": None},
    "EURGBP": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.23, "spread_pips": None},
    "EURAUD": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.44, "spread_pips": None},
    "EURCAD": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.41, "spread_pips": None},
    "EURNZD": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.49, "spread_pips": None},
    "GBPAUD": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.44, "spread_pips": None},
    "GBPCAD": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.41, "spread_pips": None},
    "GBPCHF": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.27, "spread_pips": None},
    "GBPNZD": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.49, "spread_pips": None},
    "AUDCAD": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.41, "spread_pips": None},
    "AUDCHF": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.27, "spread_pips": None},
    "AUDNZD": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.49, "spread_pips": None},
    "NZDCAD": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.41, "spread_pips": None},
    "NZDCHF": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.27, "spread_pips": None},
    "NZDJPY": {"contract_size": 100000, "digits": 3, "pip_conversion": 0.01,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.48, "spread_pips": None},
    "CADJPY": {"contract_size": 100000, "digits": 3, "pip_conversion": 0.01,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.48, "spread_pips": None},
    "CADCHF": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.27, "spread_pips": None},
    "CHFJPY": {"contract_size": 100000, "digits": 3, "pip_conversion": 0.01,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.48, "spread_pips": None},



    # --------------------------------------------------------------------------- #
    # Metals CFD — percent commission
    # --------------------------------------------------------------------------- #
    # FTMO code XAU/USD (Metals CFD). Published percent (0.0014) and usd_commission (11.69)
    # are mutually inconsistent at the snapshot gold price — both recorded verbatim, disclosed.
    # percent-type ⇒ the usd_commission_per_lot field is disclosure-only (not used in the bps conv).
    "XAUUSD": {"contract_size": 100, "digits": 2, "pip_conversion": 1.0,
               "commission": 0.0014, "commission_type": "percent", "commission_basis": "per_side",
               "usd_commission_per_lot": 11.69, "pip_commission_per_lot": 0.24,
               "spread_pips": None},
    # FTMO code XAG/USD (Metals CFD). Same %-commission inconsistency noted for gold.
    "XAGUSD": {"contract_size": 5000, "digits": 3, "pip_conversion": 1.0,
               "commission": 0.0014, "commission_type": "percent", "commission_basis": "per_side",
               "usd_commission_per_lot": 8.85, "pip_commission_per_lot": 0.03,
               "spread_pips": None},
    # --------------------------------------------------------------------------- #
    # Crypto CFD — percent commission
    # --------------------------------------------------------------------------- #
    # FTMO code BTCUSD (Crypto CFD): 0.065% of notional per trade.
    "BTCUSD": {"contract_size": 1, "digits": 2, "pip_conversion": 1.0,
               "commission": 0.065, "commission_type": "percent", "commission_basis": "per_side",
               "usd_commission_per_lot": 81.407, "pip_commission_per_lot": 0.0,
               "spread_pips": None},
    # --------------------------------------------------------------------------- #
    # Cash-CFD indices: zero commission (spread-only pricing).
    # --------------------------------------------------------------------------- #
    "USTEC": {"contract_size": 1, "digits": 2, "pip_conversion": 1.0,
              "commission": 0.0, "commission_type": "percent", "usd_commission_per_lot": 0.0,
              "pip_commission_per_lot": 0.0, "spread_pips": None},
    "US500": {"contract_size": 1, "digits": 2, "pip_conversion": 1.0,
              "commission": 0.0, "commission_type": "percent", "usd_commission_per_lot": 0.0,
              "pip_commission_per_lot": 0.0, "spread_pips": None},
    "US2000": {"contract_size": 1, "digits": 2, "pip_conversion": 1.0,
               "commission": 0.0, "commission_type": "percent", "usd_commission_per_lot": 0.0,
               "pip_commission_per_lot": 0.0, "spread_pips": None},
    "JP225": {"contract_size": 10, "digits": 2, "pip_conversion": 1.0,
              "commission": 0.0, "commission_type": "percent", "usd_commission_per_lot": 0.0,
              "pip_commission_per_lot": 0.0, "spread_pips": None},
    "AUS200": {"contract_size": 1, "digits": 2, "pip_conversion": 1.0,
               "commission": 0.0, "commission_type": "percent", "usd_commission_per_lot": 0.0,
               "pip_commission_per_lot": 0.0, "spread_pips": None},
    "US30": {"contract_size": 1, "digits": 2, "pip_conversion": 1.0,
             "commission": 0.0, "commission_type": "percent", "usd_commission_per_lot": 0.0,
             "pip_commission_per_lot": 0.0, "spread_pips": None},
    "EU50": {"contract_size": 1, "digits": 2, "pip_conversion": 1.0,
             "commission": 0.0, "commission_type": "percent", "usd_commission_per_lot": 0.0,
             "pip_commission_per_lot": 0.0, "spread_pips": None},
    "GER40": {"contract_size": 1, "digits": 2, "pip_conversion": 1.0,
              "commission": 0.0, "commission_type": "percent", "usd_commission_per_lot": 0.0,
              "pip_commission_per_lot": 0.0, "spread_pips": None},
    "HK50": {"contract_size": 1, "digits": 2, "pip_conversion": 1.0,
             "commission": 0.0, "commission_type": "percent", "usd_commission_per_lot": 0.0,
             "pip_commission_per_lot": 0.0, "spread_pips": None},
    "UK100": {"contract_size": 1, "digits": 2, "pip_conversion": 1.0,
              "commission": 0.0, "commission_type": "percent", "usd_commission_per_lot": 0.0,
              "pip_commission_per_lot": 0.0, "spread_pips": None},
    # Exotics (informative — not in Xen universe)
    "USDZAR": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 5.0, "spread_pips": None},
    "USDSEK": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 3.33, "spread_pips": None},
}

# --------------------------------------------------------------------------- #
# Bybit USDT linear perpetual cost table (INFR-012, replaces FTMO for new stack)
# --------------------------------------------------------------------------- #
# Source: Bybit derivatives fee schedule (USDT perpetuals), snapshot 2026-07-15.
# T1 lane: engine costless-honest; fees + funding + a conservative cost-floor proxy injected here.
# Netted-turnover rule carries (commission charged on net position change per event).
BYBIT_COST_SNAPSHOT = "2026-07-15 Bybit USDT linear perpetual fee schedule"
BYBIT_USDT_PERP_FEES: dict[str, float] = {
    "maker_bps_per_side": 2.0,    # 0.02% maker
    "taker_bps_per_side": 5.5,    # 0.055% taker
}
# Conservative funding assumption when history missing (R7) — 8h rate, bps of notional
BYBIT_FUNDING_CONSERVATIVE_BPS_PER_8H = 1.0
SPREAD_SCALE_ROUTING_MULTIPLIER = 3.0  # gross < 3× RT spread => undecidable on T1 (INFR-010 §4)
CHAPTER05_INFR017_PIN_SHA256 = (
    "e3b9fd9b9b5851b8a9a11f9ce34cd1e0fa8e10ea1fe1b210bd0090da379e6225"
)
CHAPTER05_INFR017_COLUMN_PINS = (
    Path(__file__).resolve().parents[3]
    / "archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-017/results/column_pins.json"
)
CHAPTER05_SPREAD_PINS_BPS = {
    "BTCUSDT": 0.244,
    "ETHUSDT": 0.305,
    "SOLUSDT": 0.727,
    "DOGEUSDT": 1.477,
    "XRPUSDT": 1.965,
}
_NS_PER_HOUR = 3_600_000_000_000
_BYBIT_FUNDING_INTERVAL_NS = 8 * _NS_PER_HOUR


def load_chapter05_cost_pins(path: str | Path | None = None) -> dict:
    """Load five INFR-017 cost-floor proxies: a conservative upper bound, not quotes.

    The sample-only reconstruction was validated on only 20 symbol-days; these values are
    neither executable nor measured spreads.
    """
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
    derived = {
        symbol: round(
            max(float(values["flip_median_bps"]), float(values["one_tick_bps"])),
            3,
        )
        for symbol, values in payload["summary"].items()
    }
    if derived != CHAPTER05_SPREAD_PINS_BPS:
        raise ValueError(
            f"Chapter-05 spread pins disagree with INFR-017: {derived!r}"
        )
    return {
        "source": str(artifact_path),
        "pin_sha256": actual_sha,
        "stored_column_status": status,
        "spread_pins_bps": derived,
    }


def _utc_timestamp_ns(value: str | datetime | np.datetime64) -> int:
    """Convert one UTC timestamp to integer nanoseconds."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError("datetime funding timestamps must be timezone-aware")
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    elif isinstance(value, str):
        value = value.removesuffix("Z")
    timestamp = np.datetime64(value, "ns")
    if np.isnat(timestamp):
        raise ValueError(f"invalid funding timestamp {value!r}")
    return int(timestamp.astype(np.int64))


def count_bybit_funding_stamps(
    entry_time: str | datetime | np.datetime64,
    exit_time: str | datetime | np.datetime64,
) -> int:
    """Count scheduled 00:00/08:00/16:00 UTC settlements in ``(entry, exit]``."""
    entry_ns = _utc_timestamp_ns(entry_time)
    exit_ns = _utc_timestamp_ns(exit_time)
    if exit_ns < entry_ns:
        raise ValueError("exit_time must be at or after entry_time")
    return exit_ns // _BYBIT_FUNDING_INTERVAL_NS - entry_ns // _BYBIT_FUNDING_INTERVAL_NS


def t1_round_trip_spread_bps(
    symbol: str,
    spread_bps: float,
    *,
    stress: float = 1.0,
) -> float:
    """Validate and stress one non-negative round-trip spread pin in bps."""
    del symbol  # per-symbol series already resolved by caller
    spread = float(spread_bps)
    multiplier = float(stress)
    if not np.isfinite(spread) or spread < 0.0:
        raise ValueError(f"spread_bps must be finite and non-negative, got {spread_bps!r}")
    if not np.isfinite(multiplier) or multiplier < 0.0:
        raise ValueError(f"stress must be finite and non-negative, got {stress!r}")
    return float(multiplier * spread)


def bybit_fee_bps_per_side(*, liquidity: str = "taker") -> float:
    """Published maker/taker fee in bps per side."""
    liq = liquidity.lower()
    if liq == "maker":
        return BYBIT_USDT_PERP_FEES["maker_bps_per_side"]
    if liq == "taker":
        return BYBIT_USDT_PERP_FEES["taker_bps_per_side"]
    raise ValueError(f"liquidity must be maker|taker, got {liquidity!r}")


def bybit_round_trip_cost_bps(
    symbol: str,
    entry_price: float,
    *,
    liquidity: str = "taker",
    spread_bps: float,
    funding_bps_per_8h: float | None = None,
    hold_hours: float = 8.0,
    funding_stamps: int | None = None,
    funding_coverage: str = "OK",
    stress: float = 1.0,
) -> dict:
    """Declared T1 round-trip cost in bps (informative for analysis, never gating).

    Components: fees (2× per-side for round trip) + T1 spread + funding.
    Provide ``funding_stamps`` for timestamp-counted settlement charges; otherwise the
    legacy continuous ``hold_hours / 8`` accrual is retained for historical callers.
    ``funding_coverage`` ∈ {OK, GAP} — GAP triggers conservative assumption flag (R7).
    Returns component breakdown for disclosure.
    """
    del symbol, entry_price  # USDT-margined perps: bps of notional is price-free
    fee_side = bybit_fee_bps_per_side(liquidity=liquidity)
    multiplier = float(stress)
    if not np.isfinite(multiplier) or multiplier < 0.0:
        raise ValueError(f"stress must be finite and non-negative, got {stress!r}")
    fee_rt = multiplier * 2.0 * fee_side
    spread_rt = multiplier * t1_round_trip_spread_bps("", spread_bps)
    if funding_bps_per_8h is None:
        funding_bps_per_8h = BYBIT_FUNDING_CONSERVATIVE_BPS_PER_8H
        if funding_coverage == "OK":
            funding_coverage = "GAP"
    if funding_stamps is None:
        funding_units = hold_hours / 8.0
        funding_method = "CONTINUOUS_LEGACY"
    else:
        if isinstance(funding_stamps, bool) or int(funding_stamps) != funding_stamps:
            raise ValueError("funding_stamps must be a non-negative integer")
        if funding_stamps < 0:
            raise ValueError("funding_stamps must be a non-negative integer")
        funding_units = float(funding_stamps)
        funding_method = "DISCRETE_STAMPS"
    funding_rt = multiplier * funding_bps_per_8h * funding_units
    total = fee_rt + spread_rt + funding_rt
    return {
        "total_bps": float(total),
        "fee_rt_bps": float(fee_rt),
        "spread_rt_bps": float(spread_rt),
        "funding_rt_bps": float(funding_rt),
        "funding_method": funding_method,
        "funding_coverage": funding_coverage,
        "liquidity": liquidity,
        "stress": stress,
    }


def spread_scale_route(
    gross_edge_bps: float,
    rt_spread_bps: float,
    *,
    secondary_available: bool = True,
) -> dict:
    """§4 spread-scale routing — undecidable on T1 when gross < 3× RT spread."""
    threshold = SPREAD_SCALE_ROUTING_MULTIPLIER * rt_spread_bps
    undecidable = abs(gross_edge_bps) < threshold
    if undecidable and secondary_available:
        route = "AWAITING_MBP"
        note = "verdict-bearing confirmation requires T2 or park AWAITING_MBP"
    elif undecidable:
        route = "PARKED_T1_UNRESOLVED"
        note = "secondary data unavailable; unresolved on this catalog"
    else:
        route = "T1_DECIDABLE"
        note = "T1 may carry verdict-bearing reads (subject to power/cost)"
    return {
        "gross_edge_bps": float(gross_edge_bps),
        "rt_spread_bps": float(rt_spread_bps),
        "threshold_bps": float(threshold),
        "t1_undecidable": undecidable,
        "route": route,
        "note": note,
    }


def usd_notional_per_lot(symbol: str, price: float, *, base_usd_rate: float | None = None) -> float:
    """USD notional of one standard lot (the denominator for a fixed-USD commission → bps).

    Currency-convention aware — ``price`` alone only yields USD notional for XXXUSD pairs:
      * XXXUSD forex  → contract_size · price   (quote = USD; price is USD per base unit)
      * USDXXX forex  → contract_size           (base = USD; price is irrelevant)
      * cross forex   → contract_size · base_usd_rate  (base ≠ USD, quote ≠ USD; rate must be
                        pinned explicitly — same discipline as ``spread_pips``)
      * USD-priced non-forex (metals/crypto/indices) → contract_size · price
        (these are all percent-commission, so this branch is not reached via the cost path).
    """
    spec = FTMO_COSTS[symbol.upper()]
    cs = float(spec["contract_size"])
    sym = symbol.upper()
    if len(sym) == 6 and sym[3:] == "USD":            # XXXUSD: quote is USD
        return cs * price
    if len(sym) == 6 and sym[:3] == "USD":            # USDXXX: base is USD
        return cs
    if len(sym) == 6:                                  # cross: base ≠ USD, quote ≠ USD
        if base_usd_rate is None:
            raise ValueError(
                f"{symbol}: cross pair — base_usd_rate not pinned. A fixed-USD commission needs "
                "the base→USD rate to form USD notional; pin it explicitly before the cost read.")
        return cs * base_usd_rate
    return cs * price                                  # USD-priced non-forex (percent-comm anyway)


def round_trip_cost_bps(symbol: str, entry_price: float, *, spread_pips: float | None = None,
                        commission_events: float = 2.0, base_usd_rate: float | None = None,
                        stress: float = 1.0) -> float:
    """Declared round-trip cost in bps of notional for one leg (informative, never gating).

    commission:
      * percent-type  → commission% of notional per event, scaled by ``commission_events``
        (2 = per-side reading of a round trip). Charged on the traded amount, not entry price.
      * flat_USD-type → the published ``usd_commission_per_lot`` is a ROUND-TRIP fixed-USD charge
        (operator-confirmed 2026-07-07), so it is applied ONCE and is independent of
        ``commission_events``. Converted to bps via the USD notional of one lot
        (``usd_notional_per_lot`` — currency-convention aware; crosses need ``base_usd_rate``).
        The pip-commission field is disclosure-only and no longer used here.
    spread: one full published spread per round trip (cross once at entry; exit symmetric
    half-spreads sum to one). ``stress`` scales the whole cost (design §6: report 1x and 2x).
    """
    spec = FTMO_COSTS[symbol.upper()]
    if spec["commission_type"] == "percent":
        # commission_basis pins whether the published % is per-side (×events for a round trip)
        # or already round-turn (charged once). Declared per symbol; verify vs FTMO before a
        # binding cost read. Prevents the silent ×2 overstatement when the % is round-turn.
        basis = spec.get("commission_basis", "per_side")
        events = commission_events if basis == "per_side" else 1.0
        comm_bps = events * spec["commission"] * 100.0             # percent of notional → bps
    else:                                                            # flat_USD: fixed $/lot, round trip
        usd_notional = usd_notional_per_lot(symbol, entry_price, base_usd_rate=base_usd_rate)
        comm_bps = spec["usd_commission_per_lot"] / usd_notional * 1e4
    sp = spread_pips if spread_pips is not None else spec["spread_pips"]
    if sp is None:
        raise ValueError(f"{symbol}: spread_pips not pinned — read it off the live FTMO page "
                         "and pass/pin it before the binding cost read (EXP-019 D5).")
    spread_bps = sp * spec["pip_conversion"] / entry_price * 1e4
    return float(stress * (comm_bps + spread_bps))


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
