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
#   * commission / commission_type: FTMO's published per-lot commission. "flat_USD" = USD per
#     1 standard lot; "percent" = percent of notional per trade. Whether flat_USD is charged
#     per side or per round turn is not stated on the page — FTMO's own pip-commission field
#     (~$3/lot ≈ 0.3 pips on EURUSD) differs from the flat figure ($5), so both are recorded
#     and the conversion takes an explicit multiplier. Informative, never gating.
#   * spread_pips: NOT statically published (live-ticker only). Must be read off the live
#     FTMO page at analysis time and pinned here before the binding cost read; the design's
#     1x/2x stress read (§6) then applies to commission + spread jointly.
#   * pip_conversion: price units per pip; contract_size: units per 1.0 lot.
FTMO_COST_SNAPSHOT = "2026-07-04 https://ftmo.com/wp-json/ftmo/symbols"
FTMO_COSTS: dict[str, dict] = {
    # symbol: contract_size, digits, pip_conversion, commission, commission_type,
    #         usd_commission_per_lot, pip_commission_per_lot (FTMO-published pips), spread_pips
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
    "EURJPY": {"contract_size": 100000, "digits": 3, "pip_conversion": 0.01,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.48, "spread_pips": None},
    "GBPJPY": {"contract_size": 100000, "digits": 3, "pip_conversion": 0.01,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.48, "spread_pips": None},
    "AUDJPY": {"contract_size": 100000, "digits": 3, "pip_conversion": 0.01,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.48, "spread_pips": None},
    # FTMO code XAU/USD (Metals CFD). Published percent (0.0014) and usd_commission (11.69)
    # are mutually inconsistent at the snapshot gold price — both recorded verbatim, disclosed.
    "XAUUSD": {"contract_size": 100, "digits": 2, "pip_conversion": 1.0,
               "commission": 0.0014, "commission_type": "percent",
               "usd_commission_per_lot": 11.69, "pip_commission_per_lot": 0.24,
               "spread_pips": None},
    # FTMO code BTCUSD (Crypto CFD): 0.065% of notional per trade.
    "BTCUSD": {"contract_size": 1, "digits": 2, "pip_conversion": 1.0,
               "commission": 0.065, "commission_type": "percent",
               "usd_commission_per_lot": 81.407, "pip_commission_per_lot": 0.0,
               "spread_pips": None},
    # Cash-CFD indices: zero commission (spread-only pricing). FTMO codes US100.cash /
    # US500.cash / US2000.cash / JP225.cash.
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
}


def round_trip_cost_bps(symbol: str, entry_price: float, *, spread_pips: float | None = None,
                        commission_events: float = 2.0, stress: float = 1.0) -> float:
    """Declared round-trip cost in bps of notional for one leg (informative, never gating).

    commission: percent-type → commission% of notional per event; flat_USD-type → converted
    via the FTMO pip-commission (pips → price units → bps at ``entry_price``).
    ``commission_events`` = number of charged events per round trip (2 = per-side reading,
    1 = round-turn reading — the FTMO page does not disambiguate; disclose which was used).
    spread: one full published spread per round trip (cross once at entry; exit symmetric
    half-spreads sum to one). ``stress`` scales the whole cost (design §6: report 1x and 2x).
    """
    spec = FTMO_COSTS[symbol.upper()]
    if spec["commission_type"] == "percent":
        comm_bps_per_event = spec["commission"] * 100.0   # percent of notional → bps
    else:
        comm_price_units = spec["pip_commission_per_lot"] * spec["pip_conversion"]
        comm_bps_per_event = comm_price_units / entry_price * 1e4
    sp = spread_pips if spread_pips is not None else spec["spread_pips"]
    if sp is None:
        raise ValueError(f"{symbol}: spread_pips not pinned — read it off the live FTMO page "
                         "and pass/pin it before the binding cost read (EXP-019 D5).")
    spread_bps = sp * spec["pip_conversion"] / entry_price * 1e4
    return float(stress * (commission_events * comm_bps_per_event + spread_bps))


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
