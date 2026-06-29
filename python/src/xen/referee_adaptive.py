"""Chapter-02 adaptive-referee branch — frozen E0 constants & primitives.

This module is the **redesign artifact** for the Phase-001 referee renew (KB L-12). It is kept
**separate** from the frozen Chapter-01 suite (`referee_calibration.py`) so that suite's artifact
hash stays stable: the renew adds, it does not mutate. Frozen primitives (split discipline, block
bootstrap, CIs, episode counts) are imported and reused unchanged.

E0 freezes two candidate-blind inputs every D-referee experiment (E1-E5) consumes
(`docs/experiments-docs/checkpoints/2026-06-27-001-referee-adaptivity-rsi2-benchmark/E0-frozen-constants.md`):

1. **17-instrument round-trip cost map** (Q6, operator-ratified 2026-06-28). Conservative,
   monotonic-by-liquidity, class-anchored to the frozen 4 (EURUSD 1.0 / XAUUSD 3.0 / USTEC 4.0 /
   BTCUSD 10.0). 1h/4h domains only (5m dropped). Never tuned on any E1-E5 / CF-MR-002 outcome.
2. **Open-to-open `<= t-1` return basis** (Q7). Replaces the frozen suite's close-to-close return
   for the adaptive path only; the frozen suite keeps close-to-close for parallel disclosure.

The adaptive gate itself (power-aware leg gating, validity-then-economics composite, return-series
statistic) is built at E3 and appended here once E0 is frozen.
"""
from __future__ import annotations

import json
import math
from statistics import NormalDist
from typing import Any, Callable

import numpy as np
import polars as pl

from xen.referee_calibration import (
    DOMAIN_SPECS,
    _episode_counts,
    _gate_bootstrap_pair,
    _stationary_block_indices,
    ci_from_means,
    estimate_block_length,
    finite_values,
    materiality_bps_for,
    naive_momentum_positions,
    resolve_split_index,
    strategy_return_bps,
)

# --------------------------------------------------------------------------- #
# E0.2 — 17-instrument round-trip cost map (Q6). FROZEN 2026-06-28.
# Per-bar round-trip bps, domain-invariant, 1h/4h only. Operator-ratified; the
# 4 Chapter-01 anchors (EURUSD/XAUUSD/USTEC/BTCUSD) are unchanged fixed points.
# --------------------------------------------------------------------------- #
ADAPTIVE_DOMAINS: tuple[str, ...] = ("1h", "4h")

ROUND_TRIP_COST_BPS_17: dict[str, dict[str, float]] = {
    # FX majors
    "EURUSD": {"1h": 1.0, "4h": 1.0},
    "USDJPY": {"1h": 1.0, "4h": 1.0},
    "GBPUSD": {"1h": 1.2, "4h": 1.2},
    "USDCHF": {"1h": 1.5, "4h": 1.5},
    "USDCAD": {"1h": 1.5, "4h": 1.5},
    "AUDUSD": {"1h": 1.5, "4h": 1.5},
    "NZDUSD": {"1h": 2.0, "4h": 2.0},
    # FX crosses
    "EURJPY": {"1h": 2.0, "4h": 2.0},
    "AUDJPY": {"1h": 2.5, "4h": 2.5},
    "GBPJPY": {"1h": 2.5, "4h": 2.5},
    # metal
    "XAUUSD": {"1h": 3.0, "4h": 3.0},
    # indices
    "US500": {"1h": 3.0, "4h": 3.0},
    "USTEC": {"1h": 4.0, "4h": 4.0},
    "DE30": {"1h": 4.0, "4h": 4.0},
    "JP225": {"1h": 4.0, "4h": 4.0},
    "US2000": {"1h": 5.0, "4h": 5.0},
    # crypto
    "BTCUSD": {"1h": 10.0, "4h": 10.0},
}


def entry_mask(positions: np.ndarray) -> np.ndarray:
    """Bars that open a new directional commitment (one round-trip per holding episode).

    An entry is a non-zero position differing from the previous bar's position (the first bar is an
    entry if non-zero); a direct sign flip is one entry; an exit to flat is not charged at the zero
    bar. Promoted from EXP-001 ``code/cost_conventions.py`` (reused by EXP-002+).
    """
    pos = np.asarray(positions, dtype=float)
    if len(pos) == 0:
        return np.zeros(0, dtype=bool)
    prev = np.concatenate(([0.0], pos[:-1]))
    return (pos != 0.0) & (pos != prev)


def strategy_return_bps_turnover(
    returns: np.ndarray, positions: np.ndarray, *, cost_bps: float
) -> np.ndarray:
    """Per-bar net strategy return in bps, charging ``cost_bps`` once per entry (amortized arm).

    Identical to :func:`xen.referee_calibration.strategy_return_bps` except the round-trip cost is
    deducted on entry bars only (one round-trip per holding episode) rather than every active bar.
    Total episode cost = ``cost_bps`` (vs ``L * cost_bps`` per-held), with equality iff every active
    bar is an entry (L == 1). The B-style amortized convention; the binding arm consumed by
    :func:`gate_stack_core_costfn` in EXP-002. Promoted from EXP-001 ``code/cost_conventions.py``.
    """
    n = min(len(returns), len(positions))
    ret = np.asarray(returns[:n], dtype=float)
    pos = np.asarray(positions[:n], dtype=float)
    gross = pos * ret * 10_000.0
    return gross - (cost_bps * entry_mask(pos).astype(float))


def adaptive_cost_bps_for(instrument: str, domain: str) -> float:
    """Frozen 17-instrument per-bar round-trip cost in bps (1h/4h only).

    Parameters
    ----------
    instrument : str
        cTrader symbol; case-insensitive.
    domain : str
        ``"1h"`` or ``"4h"`` (5m is out of adaptive scope, Q6).

    Returns
    -------
    float
        Round-trip cost in bps.
    """
    try:
        return ROUND_TRIP_COST_BPS_17[instrument.upper()][domain]
    except KeyError as exc:
        raise KeyError(
            f"No adaptive round-trip cost for {instrument}/{domain} "
            f"(domains: {ADAPTIVE_DOMAINS})"
        ) from exc


# --------------------------------------------------------------------------- #
# E0.1 — Open-to-open <= t-1 return basis (Q7). FROZEN 2026-06-28.
# --------------------------------------------------------------------------- #
def next_open_to_open_returns_from_bars(bars: pl.DataFrame) -> tuple[np.ndarray, pl.DataFrame]:
    """Return open-to-open next-step log returns and their aligned rows.

    The return realised at decision bar ``t`` is ``log(Open[t+1] / Open[t])`` — the executable
    next-step move from acting at bar ``t``'s open. A position consuming this series must itself be
    conditioned only on confirmed bars ``<= t-1`` (the forming bar's OHLC is unknown at the open);
    this primitive computes the forward open-to-open return and does not enforce that conditioning.
    Mirrors ``referee_calibration.next_log_returns_from_bars`` (close-to-close) in structure so the
    split / bootstrap / CI machinery is reused unchanged.

    Parameters
    ----------
    bars : pl.DataFrame
        Domain bars carrying at least ``OpenTime, CloseTime, Open, High, Low, Close, TickVolume``.

    Returns
    -------
    tuple[np.ndarray, pl.DataFrame]
        The open-to-open next-step log returns and the aligned rows (last bar dropped — no next
        open).
    """
    ordered = bars.sort("CloseTime").select(
        ["OpenTime", "CloseTime", "Open", "High", "Low", "Close", "TickVolume"]
    )
    aligned = ordered.with_columns(
        ((pl.col("Open").shift(-1) / pl.col("Open")).log()).alias("NextOpenLogReturn")
    ).drop_nulls("NextOpenLogReturn")
    returns = np.asarray(aligned.get_column("NextOpenLogReturn"), dtype=float)
    return returns, aligned


# --------------------------------------------------------------------------- #
# E1 cost-convention seam — parametrized gate-stack core (EXP-001).
#
# `referee_calibration.gate_stack_core` hardcodes the per-held-bar cost
# convention (`strategy_return_bps`) for the signal leg and exposes no seam to
# swap it. This wrapper MIRRORS that core but takes a `strategy_fn` so the
# amortized (per-entry) convention can be run through the same gate logic.
# It is added here (not in the frozen suite) so `referee_calibration.py` stays
# byte-frozen — the renew adds, it does not mutate. Every gate sub-primitive
# (split discipline, block bootstrap, episode counts, L1/L4 legs) is imported
# and reused unchanged.
#
# SEAM SCOPE (binding): `strategy_fn` is applied to the **signal leg only**.
# The L3 vs-naive control always uses the frozen per-held-bar `strategy_return_bps`,
# so it is a fixed reference across conventions. Consequences:
#   * strategy_fn=strategy_return_bps reproduces gate_stack_core EXACTLY (same
#     cost_bps) — the audit equivalence check.
#   * On a strictly-alternating signal (every active bar is an entry) the two
#     conventions produce an identical signal series AND share the unchanged
#     naive leg, so the whole gate output coincides (EXP-001 tripwire 2).
# --------------------------------------------------------------------------- #
def gate_stack_core_costfn(
    returns: np.ndarray,
    positions: np.ndarray,
    *,
    domain: str,
    cost_bps: float,
    n_bootstrap: int,
    seed: int,
    strategy_fn: Callable[..., np.ndarray] = strategy_return_bps,
    split_index: int | None = None,
) -> dict[str, Any]:
    """Alpha-independent gate-stack state with an injectable signal cost convention.

    Faithful mirror of :func:`xen.referee_calibration.gate_stack_core` with two
    differences: ``cost_bps`` is supplied explicitly (the E0 17-instrument map is
    the caller's responsibility — see :func:`adaptive_cost_bps_for`) and the
    signal leg is computed with ``strategy_fn`` instead of the hardcoded
    per-held-bar function. The vs-naive control leg is deliberately left on the
    frozen per-held-bar convention (a fixed reference; see seam-scope note above).
    Pass ``strategy_fn=strategy_return_bps`` to reproduce the frozen core exactly.

    Parameters
    ----------
    returns : np.ndarray
        Real next-step (open-to-open ``<= t-1``) returns, fractional.
    positions : np.ndarray
        Signal positions in ``{-1, 0, +1}``.
    domain : str
        ``"1h"`` or ``"4h"`` (selects the frozen ``DomainSpec`` + materiality).
    cost_bps : float
        Round-trip cost (bps) for both legs' cost charging.
    n_bootstrap : int
        Block-bootstrap resamples (passed through to the frozen bootstrap pair).
    seed : int
        Bootstrap seed (frozen ``seed + 1`` / ``seed + 2`` sub-seeding reused).
    strategy_fn : Callable, default ``strategy_return_bps``
        Signal-leg net-return function ``(returns, positions, *, cost_bps)``.
    split_index : int or None
        Train/test cut; ``None`` uses the frozen default split.

    Returns
    -------
    dict[str, Any]
        Same schema as :func:`gate_stack_core`, consumable by
        :func:`xen.referee_calibration.gate_stack_row`.
    """
    spec = DOMAIN_SPECS[domain]
    materiality_bps = materiality_bps_for(domain)
    strategy = strategy_fn(returns, positions, cost_bps=cost_bps)
    naive = strategy_return_bps(
        returns, naive_momentum_positions(returns), cost_bps=cost_bps
    )
    cut = resolve_split_index(len(strategy), split_index)
    train_values, test_values = strategy[:cut], strategy[cut:]
    pos_arr = np.asarray(positions, dtype=float)
    train_pos, test_pos = pos_arr[:cut], pos_arr[cut:]
    block_length = estimate_block_length(train_values)
    effective_n = len(test_values) / max(block_length, 1)

    diff_vs_naive = test_values - naive[cut : cut + len(test_values)]
    neutral_dist, naive_dist = _gate_bootstrap_pair(
        test_values,
        diff_vs_naive,
        n_bootstrap=n_bootstrap,
        block_length=block_length,
        seed=seed,
    )
    neutral_means, neutral_mean, n_neutral = neutral_dist
    naive_means, naive_mean, n_naive = naive_dist

    train_up, train_down, test_up, test_down = _episode_counts(train_pos, test_pos)
    return {
        "neutral_means": neutral_means,
        "neutral_mean": neutral_mean,
        "n_neutral": n_neutral,
        "naive_means": naive_means,
        "naive_mean": naive_mean,
        "n_naive": n_naive,
        "block_length": block_length,
        "effective_n": effective_n,
        "split_index": cut,
        "cost_bps": cost_bps,
        "materiality_bps": materiality_bps,
        "l1": bool(
            effective_n >= spec.min_effective_n
            and min(train_up, train_down, test_up, test_down) >= spec.min_state_count
        ),
        "l2": True,
        "l4": bool(np.mean(train_values) > 0.0 and np.mean(test_values) > 0.0),
        "train_up": train_up,
        "train_down": train_down,
        "test_up": test_up,
        "test_down": test_down,
    }


# --------------------------------------------------------------------------- #
# E3a — economic-leg ADAPTIVE gate (EXP-003). Built per the checkpoint reservation
# ("the adaptive gate itself ... built at E3"). Binding D0 (checkpoint:101-106):
# L1+coverage stay RIGID (validity floor, FPR~0); only the economic legs L3/L5 adapt.
# Changes vs the frozen stack: amortized accounting (E1); L2 no-op REMOVED (F4);
# L3/L5 power-aware (abstain where undefined, never veto); L5 gains a candidate-blind
# sub-population path (fixed q*-quantile of per-episode net-mean) to recover an edge
# confined to a latent sub-state (the E2 STATE loss, L-03). Frozen sub-primitives are
# reused unchanged; `referee_calibration.py` is untouched.
#
# Candidate-blindness (Q5): q*, MIN_EPISODES_SUBPOP, materiality are fixed module
# constants; the sub-pop statistic is computed on the test net series exactly as any
# referee leg is — no state mask, no selection, no performance-derived threshold.
# --------------------------------------------------------------------------- #
SUBPOP_QUANTILE: float = 0.75       # fixed q* — recovers an edge carried by >=25% of episodes (Q5)
MIN_EPISODES_SUBPOP: int = 5        # below this the sub-pop test is undefined -> ABSTAIN
# A1 (2026-06-29): studentized floor for the sub-pop L5 path. = Phi^-1(q*), the q*-quantile of the
# standard normal == the studentized q* (q*-quantile / std) of ANY symmetric-about-zero null. A
# pure-dispersion (no-edge) episode-mean distribution lands at ~this value regardless of scale, so a
# high-volatility null no longer clears the sub-pop test on raw-bps size alone. Derived from q*
# only (no data / FPR / outcome / state mask) -> candidate-blind, Q5. Tracks q* if q* changes.
Q_STUD_MIN: float = NormalDist().inv_cdf(SUBPOP_QUANTILE)   # = 0.6744897501960817 for q*=0.75


def episode_net_means(strategy_bps: np.ndarray, positions: np.ndarray) -> np.ndarray:
    """Per-episode mean net bps; an episode = a contiguous run of the same nonzero position.

    Flat bars (position 0) belong to no episode and break a run. Consumes a precomputed net
    series + its positions and reads no future bar (provenance: alpha to the input series only).

    Parameters
    ----------
    strategy_bps : np.ndarray
        Per-bar net strategy return in bps (already cost-charged).
    positions : np.ndarray
        Per-bar positions in ``{-1, 0, +1}``.

    Returns
    -------
    np.ndarray
        One mean per episode (empty if there are no active bars).
    """
    n = min(len(strategy_bps), len(positions))
    s = np.asarray(strategy_bps[:n], dtype=float)
    p = np.asarray(positions[:n], dtype=float)
    if n == 0:
        return np.empty(0, dtype=float)
    active = p != 0.0
    changed = np.concatenate(([True], p[1:] != p[:-1]))
    new_ep = active & changed
    ep_id = np.cumsum(new_ep) - 1
    valid = active & (ep_id >= 0)
    if not valid.any():
        return np.empty(0, dtype=float)
    ids = ep_id[valid].astype(np.int64)
    sums = np.bincount(ids, weights=s[valid])
    counts = np.bincount(ids)
    return sums[counts > 0] / counts[counts > 0]


def _block_bootstrap_quantile_dist(
    values: np.ndarray, *, q: float, n_resamples: int, block_length: int, seed: int
) -> np.ndarray:
    """Stationary block-bootstrap distribution of the ``q``-quantile (reuses the frozen resampler)."""
    finite = finite_values(values)
    n = len(finite)
    if n == 0 or n_resamples <= 0:
        return np.empty(0, dtype=float)
    bl = max(1, min(int(block_length), n))
    rng = np.random.default_rng(seed)
    cols = np.arange(n, dtype=np.int32)
    idx = _stationary_block_indices(rng, rows=n_resamples, n=n, block_length=bl, p=1.0 / bl, cols=cols)
    return np.quantile(finite[idx], q, axis=1)


def _block_bootstrap_studentized_quantile_dist(
    values: np.ndarray, *, q: float, n_resamples: int, block_length: int, seed: int
) -> np.ndarray:
    """Block-bootstrap distribution of the **studentized** ``q``-quantile (``q``-quantile / std).

    Scale-free per resample: each resample's ``q``-quantile is divided by that resample's std. A
    resample with zero dispersion contributes ``0.0`` (it cannot clear the positive studentized
    floor). Same Politis-Romano resampling / seeding as :func:`_block_bootstrap_quantile_dist`
    (A1, 2026-06-29).
    """
    finite = finite_values(values)
    n = len(finite)
    if n == 0 or n_resamples <= 0:
        return np.empty(0, dtype=float)
    bl = max(1, min(int(block_length), n))
    rng = np.random.default_rng(seed)
    cols = np.arange(n, dtype=np.int32)
    idx = _stationary_block_indices(rng, rows=n_resamples, n=n, block_length=bl, p=1.0 / bl, cols=cols)
    sample = finite[idx]
    quant = np.quantile(sample, q, axis=1)
    std = np.std(sample, axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(std > 0.0, quant / std, 0.0)


def subpop_quantile_materiality(
    episode_means: np.ndarray, *, q: float, materiality_bps: float, n_bootstrap: int,
    block_length: int, seed: int, alpha: float = 0.05,
) -> dict[str, Any]:
    """Dilution-robust L5 path: studentized ∧ raw-bps q-quantile of per-episode net-means (A1).

    PASS iff **both** floors clear (conjunction): the **studentized** ``q``-quantile
    (``q``-quantile / std) bootstrap CI-lower exceeds :data:`Q_STUD_MIN` (= ``Phi^-1(q)``, the
    null-shape level — kills high-dispersion noise-firing) **and** the **raw-bps** ``q``-quantile
    bootstrap CI-lower exceeds ``materiality_bps`` (the frozen economic floor). ABSTAIN when fewer
    than ``MIN_EPISODES_SUBPOP`` episodes or the episode-means have zero dispersion. ``q``,
    ``Q_STUD_MIN``, and the materiality floor are fixed predeclared constants (Q5) — the statistic
    reads the test net series + positions only, no state mask, no future bar.
    """
    n_ep = len(episode_means)
    finite = finite_values(episode_means)
    if n_ep < MIN_EPISODES_SUBPOP or len(finite) == 0 or float(np.std(finite)) == 0.0:
        return {"abstain": True, "passed": False, "stat": math.nan, "ci_lower": math.nan,
                "stud_stat": math.nan, "stud_ci_lower": math.nan, "n_episodes": n_ep}
    raw_dist = _block_bootstrap_quantile_dist(
        episode_means, q=q, n_resamples=n_bootstrap, block_length=block_length, seed=seed)
    stud_dist = _block_bootstrap_studentized_quantile_dist(
        episode_means, q=q, n_resamples=n_bootstrap, block_length=block_length, seed=seed + 1)
    raw_stat = float(np.quantile(finite, q))
    stud_stat = raw_stat / float(np.std(finite))
    raw_ci_lower = float(np.quantile(raw_dist, alpha / 2.0)) if len(raw_dist) else math.nan
    stud_ci_lower = float(np.quantile(stud_dist, alpha / 2.0)) if len(stud_dist) else math.nan
    passed = bool(stud_ci_lower > Q_STUD_MIN and raw_ci_lower > materiality_bps)
    return {"abstain": False, "passed": passed, "stat": raw_stat, "ci_lower": raw_ci_lower,
            "stud_stat": stud_stat, "stud_ci_lower": stud_ci_lower, "n_episodes": n_ep}


def gate_stack_adaptive(
    returns: np.ndarray, positions: np.ndarray, *, domain: str, cost_bps: float,
    n_bootstrap: int, seed: int, q: float = SUBPOP_QUANTILE, split_index: int | None = None,
) -> dict[str, Any]:
    """Alpha-independent state for the E3a economic-leg adaptive gate (L1 rigid; L3/L5 adapted).

    Amortized signal-leg accounting; L2 removed; the per-episode net-means + the raw and
    **studentized** q-quantile block-bootstrap distributions are computed here so
    :func:`adaptive_row` can apply alpha (A1 conjunction: studentized CI-lower > ``Q_STUD_MIN`` AND
    raw-bps CI-lower > ``materiality_bps``). L1 + coverage and the neutral/naive bootstrap pair are
    computed exactly as :func:`gate_stack_core_costfn` (the rigid validity floor and frozen L3).
    """
    spec = DOMAIN_SPECS[domain]
    materiality_bps = materiality_bps_for(domain)
    strategy = strategy_return_bps_turnover(returns, positions, cost_bps=cost_bps)
    naive = strategy_return_bps(returns, naive_momentum_positions(returns), cost_bps=cost_bps)
    cut = resolve_split_index(len(strategy), split_index)
    train_values, test_values = strategy[:cut], strategy[cut:]
    pos_arr = np.asarray(positions, dtype=float)
    train_pos, test_pos = pos_arr[:cut], pos_arr[cut:]
    block_length = estimate_block_length(train_values)
    effective_n = len(test_values) / max(block_length, 1)

    diff_vs_naive = test_values - naive[cut : cut + len(test_values)]
    neutral_dist, naive_dist = _gate_bootstrap_pair(
        test_values, diff_vs_naive, n_bootstrap=n_bootstrap, block_length=block_length, seed=seed)
    neutral_means, neutral_mean, n_neutral = neutral_dist
    naive_means, naive_mean, n_naive = naive_dist

    # Sub-pop L5 (A1): two block-bootstrap dists over per-episode net-means — the raw-bps q*-quantile
    # (economic floor) and the studentized q*-quantile = q*-quantile/std (null-shape floor). PASS in
    # `adaptive_row` requires BOTH CI-lowers to clear their floors (studentized > Q_STUD_MIN AND
    # raw > materiality_bps). ABSTAIN when too few episodes OR zero episode-mean dispersion.
    ep_means = episode_net_means(test_values, test_pos)
    ep_finite = finite_values(ep_means)
    ep_block = estimate_block_length(ep_means) if len(ep_means) else 1
    subpop_dist = _block_bootstrap_quantile_dist(
        ep_means, q=q, n_resamples=n_bootstrap, block_length=ep_block, seed=seed + 3)
    subpop_stud_dist = _block_bootstrap_studentized_quantile_dist(
        ep_means, q=q, n_resamples=n_bootstrap, block_length=ep_block, seed=seed + 4)
    ep_std = float(np.std(ep_finite)) if len(ep_finite) else 0.0
    raw_stat = float(np.quantile(ep_finite, q)) if len(ep_finite) else math.nan

    train_up, train_down, test_up, test_down = _episode_counts(train_pos, test_pos)
    return {
        "neutral_means": neutral_means, "neutral_mean": neutral_mean, "n_neutral": n_neutral,
        "naive_means": naive_means, "naive_mean": naive_mean, "n_naive": n_naive,
        "block_length": block_length, "effective_n": effective_n, "split_index": cut,
        "cost_bps": cost_bps, "materiality_bps": materiality_bps,
        "l1": bool(effective_n >= spec.min_effective_n
                   and min(train_up, train_down, test_up, test_down) >= spec.min_state_count),
        "subpop_q": q, "subpop_stat": raw_stat,
        "subpop_stud_stat": (raw_stat / ep_std if ep_std > 0.0 else math.nan),
        "subpop_dist": subpop_dist, "subpop_stud_dist": subpop_stud_dist, "n_episodes": len(ep_means),
        "subpop_abstain": (len(ep_means) < MIN_EPISODES_SUBPOP) or (ep_std == 0.0),
        "train_up": train_up, "train_down": train_down, "test_up": test_up, "test_down": test_down,
    }


def adaptive_row(core: dict[str, Any], *, alpha: float) -> dict[str, Any]:
    """Assemble the E3a adaptive verdict for one alpha (L1 rigid; power-aware L3/L5; L2 removed)."""
    ci_neutral = ci_from_means(core["neutral_mean"], core["neutral_means"], core["n_neutral"], alpha=alpha)
    ci_naive = ci_from_means(core["naive_mean"], core["naive_means"], core["n_naive"], alpha=alpha)
    l1 = bool(core["l1"])                       # rigid validity floor (incl. coverage)

    # L3 economic — power-aware {PASS, FAIL, ABSTAIN}.
    if core["n_neutral"] == 0 or core["n_naive"] == 0:
        l3 = "ABSTAIN"
    else:
        l3 = "PASS" if (ci_neutral.lower > 0.0 and ci_naive.lower > 0.0) else "FAIL"

    # L5 economic — pooled-material OR sub-population-material; power-aware.
    # Sub-pop (A1): PASS iff BOTH the studentized CI-lower > Q_STUD_MIN (null-shape floor) AND the
    # raw-bps CI-lower > materiality_bps (economic floor) — a high-dispersion null clears the bps
    # floor on size but fails the studentized floor (~Phi^-1(q*)), so it no longer passes.
    pooled_pass = bool(core["n_neutral"] > 0 and ci_neutral.lower > core["materiality_bps"])
    subpop_abstain = bool(core["subpop_abstain"]) or len(core["subpop_dist"]) == 0 \
        or len(core["subpop_stud_dist"]) == 0
    if subpop_abstain:
        subpop_raw_ci_lower = math.nan
        subpop_stud_ci_lower = math.nan
    else:
        subpop_raw_ci_lower = float(np.quantile(core["subpop_dist"], alpha / 2.0))
        subpop_stud_ci_lower = float(np.quantile(core["subpop_stud_dist"], alpha / 2.0))
    subpop_pass = bool((not subpop_abstain)
                       and subpop_stud_ci_lower > Q_STUD_MIN
                       and subpop_raw_ci_lower > core["materiality_bps"])
    if core["n_neutral"] == 0 and subpop_abstain:
        l5 = "ABSTAIN"
    else:
        l5 = "PASS" if (pooled_pass or subpop_pass) else "FAIL"

    economic = [l3, l5]
    passed = bool(l1 and ("FAIL" not in economic) and ("PASS" in economic))
    leg_results = {
        "L1_readiness": l1, "L3_outcome": l3, "L5_materiality": l5,
        "L5_pooled_pass": pooled_pass, "L5_subpop_pass": subpop_pass,
        "L5_subpop_abstain": subpop_abstain,
        "L5_subpop_raw_ci_lower_bps": subpop_raw_ci_lower,
        "L5_subpop_stud_ci_lower": subpop_stud_ci_lower,
        "L5_subpop_stud_stat": core["subpop_stud_stat"],
        "subpop_stat_bps": core["subpop_stat"], "n_episodes": core["n_episodes"],
        "ci_vs_naive_lower_bps": ci_naive.lower, "materiality_bps": core["materiality_bps"],
        "Q_STUD_MIN": Q_STUD_MIN,
    }
    return {
        "referee": "gate_stack_adaptive", "alpha": alpha,
        "verdict": "PASS" if passed else "REJECT", "passed": passed,
        "effect_bps": ci_neutral.mean, "ci_lower_bps": ci_neutral.lower, "ci_upper_bps": ci_neutral.upper,
        "effective_n": core["effective_n"], "block_length": core["block_length"],
        "split_index": core["split_index"], "leg_results": json.dumps(leg_results, sort_keys=True),
    }


# --------------------------------------------------------------------------- #
# E5 — Q4 composite-form VARIANT-C (EXP-005). Single sufficient statistic +
# power guards (referee-framework-assessment §10.3(c)): the incremental net edge
# (vs-naive CI-lower) IS the verdict; the other legs become reported diagnostics,
# not gates. This is the REJECTED-ALTERNATIVE form the E5 freeze adjudicates the
# primary §10.3a (`adaptive_row`) against by DET-dominance.
#
# ADDITIVE ONLY: it consumes the SAME `gate_stack_adaptive` core dict unchanged
# (identical split / block bootstrap / neutral+naive CI pair / sub-pop dists) and
# only assembles a different verdict. It does NOT edit `adaptive_row`,
# `gate_stack_adaptive`, or any module constant (the E5 regression anchor + an
# additions-only diff prove this). L1+coverage stay the rigid admissibility gate,
# bit-identical to §10.3a. No new free knob, threshold, or constant.
# --------------------------------------------------------------------------- #
def adaptive_row_variant_c(core: dict[str, Any], *, alpha: float) -> dict[str, Any]:
    """Assemble the E5 variant-c verdict for one alpha (single-statistic composite form).

    ⚠ REJECTED ALTERNATIVE — NOT THE FROZEN REFEREE. E5 (EXP-005) adjudicated this single-statistic
    form against the primary §10.3a (:func:`adaptive_row`) and **REFUTED it**: the incremental-over-
    naive statistic has no absolute edge floor, so it admits anything less-bad than the net-negative
    naive-momentum baseline — dogfood FPR up to 1.0, survives future-destroy (no FPR control). It is
    retained **only** as the form-check record for reproducibility. The FROZEN renewed referee is
    §10.3a (:func:`adaptive_row`); see ``EXP-005/results/freeze_manifest.json``. **Never call this as
    a referee / gate.**

    PASS iff ``L1 ∧ coverage ∧ (incremental-net vs-naive CI-lower > 0)`` — the single binding
    economic statistic is the incremental net edge over the naive-momentum control. Power-aware
    ABSTAIN when the naive leg is undefined (``n_naive == 0``); an abstaining economic statistic
    cannot PASS (there is no other binding leg to carry it — that is the point of the form). L5
    materiality (pooled + studentized sub-pop) and the L3 neutral CI are computed and emitted as
    **non-binding diagnostics** so the DET map can show what variant-c forgoes; they never gate.
    L1 + the neutral/naive bootstrap pair are read from the same ``core`` as :func:`adaptive_row`.
    """
    ci_neutral = ci_from_means(core["neutral_mean"], core["neutral_means"], core["n_neutral"], alpha=alpha)
    ci_naive = ci_from_means(core["naive_mean"], core["naive_means"], core["n_naive"], alpha=alpha)
    l1 = bool(core["l1"])                       # rigid validity floor (incl. coverage) — admissibility

    # Single binding economic statistic: incremental net edge vs the naive control.
    if core["n_naive"] == 0:
        economic = "ABSTAIN"
    else:
        economic = "PASS" if ci_naive.lower > 0.0 else "FAIL"
    passed = bool(l1 and economic == "PASS")

    # Diagnostics ONLY (non-binding) — what the multi-leg §10.3a form would have weighed.
    pooled_diag = bool(core["n_neutral"] > 0 and ci_neutral.lower > core["materiality_bps"])
    subpop_abstain = bool(core["subpop_abstain"]) or len(core["subpop_dist"]) == 0 \
        or len(core["subpop_stud_dist"]) == 0
    if subpop_abstain:
        subpop_raw_ci_lower = math.nan
        subpop_stud_ci_lower = math.nan
        subpop_pass_diag = False
    else:
        subpop_raw_ci_lower = float(np.quantile(core["subpop_dist"], alpha / 2.0))
        subpop_stud_ci_lower = float(np.quantile(core["subpop_stud_dist"], alpha / 2.0))
        subpop_pass_diag = bool(subpop_stud_ci_lower > Q_STUD_MIN
                                and subpop_raw_ci_lower > core["materiality_bps"])
    leg_results = {
        "L1_readiness": l1, "economic_statistic": economic,
        "binding_statistic": "incremental_net_vs_naive_ci_lower>0",
        "ci_vs_naive_lower_bps": ci_naive.lower,
        "DIAG_L3_neutral_ci_lower_bps": ci_neutral.lower,
        "DIAG_L5_pooled_pass": pooled_diag,
        "DIAG_L5_subpop_pass": subpop_pass_diag,
        "DIAG_L5_subpop_abstain": subpop_abstain,
        "DIAG_L5_subpop_raw_ci_lower_bps": subpop_raw_ci_lower,
        "DIAG_L5_subpop_stud_ci_lower": subpop_stud_ci_lower,
        "materiality_bps": core["materiality_bps"], "n_episodes": core["n_episodes"],
    }
    return {
        "referee": "gate_stack_adaptive/variant_c", "alpha": alpha,
        "verdict": "PASS" if passed else "REJECT", "passed": passed,
        "effect_bps": ci_neutral.mean, "ci_lower_bps": ci_neutral.lower, "ci_upper_bps": ci_neutral.upper,
        "effective_n": core["effective_n"], "block_length": core["block_length"],
        "split_index": core["split_index"], "leg_results": json.dumps(leg_results, sort_keys=True),
    }
