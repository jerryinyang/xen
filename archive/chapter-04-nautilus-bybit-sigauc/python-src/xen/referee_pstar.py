"""E6 — P*-capable referee variant (EXP-007). ADDITIVE; the frozen suites are not touched.

Both frozen gates adjudicate ``position * market-return`` only: the §10.3a adaptive gate
(:func:`xen.referee_adaptive.gate_stack_adaptive`) hardcodes the signal leg as
``strategy_return_bps_turnover(returns, positions)`` and exposes no ``strategy_fn`` seam, and the
frozen Chapter-01 suite hardcodes ``strategy_return_bps(returns, positions)``. A CF-MR-002 intrabar
**engine-realized P* favourable-limit fill** (EXP-006) is a realized per-bar net series that is NOT
``position * market-return``; the frozen gates cannot consume it and editing the hash-frozen modules
is forbidden (the E5 freeze is REJECT-class).

This module supplies the missing adjudication path **additively**: :func:`gate_stack_pstar` is a
faithful mirror of :func:`xen.referee_adaptive.gate_stack_adaptive` with **exactly one** change — the
signal leg is an *injected* realized per-bar net series (``realized_bps``) instead of
``strategy_return_bps_turnover(returns, positions)``. Every other sub-primitive (L1 + coverage rigid
validity floor; L3 vs-naive; L5 pooled + studentized sub-pop; block bootstrap; split discipline) is
**imported from the frozen modules and reused unchanged**, and the result dict has the same schema so
:func:`xen.referee_adaptive.adaptive_row` consumes it with no edit.

Reduction identity (the freeze proof, EXP-007 Arm R): with
``realized_bps = strategy_return_bps_turnover(returns, positions)`` the produced core dict is
*bit-identical* to ``gate_stack_adaptive(returns, positions)`` (see
:func:`gate_stack_pstar_reduces_to_adaptive`). The P*-capable gate is therefore §10.3a plus a pure
signal-leg source swap — no new threshold, knob, or constant.

Causal-provenance contract. ``gate_stack_pstar`` reads only its inputs: ``realized_bps[t]`` (the
strategy's realized net return for bar ``t``, supplied by the caller — the cTrader engine's causal
fill for a real run, or :func:`make_realized_fill` for a synthetic calibration substrate), the market
``returns`` (for the frozen naive control leg only), and ``positions`` (episode/turnover counts). No
output reads a future bar. ``make_realized_fill`` rests both bracket limits from ``<= t-1`` and is a
**calibration-substrate construct only** — it never adjudicates a real price strategy (that is the
engine's ``ExitFillPrice`` emission, EXP-006).
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np

from xen.referee_adaptive import (
    DOMAIN_SPECS,
    MIN_EPISODES_SUBPOP,
    SUBPOP_QUANTILE,
    _block_bootstrap_quantile_dist,
    _block_bootstrap_studentized_quantile_dist,
    _episode_counts,
    _gate_bootstrap_pair,
    episode_net_means,
    estimate_block_length,
    finite_values,
    gate_stack_adaptive,
    materiality_bps_for,
    naive_momentum_positions,
    resolve_split_index,
    strategy_return_bps,
    strategy_return_bps_turnover,
)

# --------------------------------------------------------------------------- #
# P*-capable adaptive gate-stack core (signal leg = injected realized series).
# --------------------------------------------------------------------------- #
def gate_stack_pstar(
    returns: np.ndarray,
    positions: np.ndarray,
    realized_bps: np.ndarray,
    *,
    domain: str,
    cost_bps: float,
    n_bootstrap: int,
    seed: int,
    q: float = SUBPOP_QUANTILE,
    split_index: int | None = None,
) -> dict[str, Any]:
    """§10.3a adaptive core with the signal leg sourced from an injected realized net series.

    Faithful mirror of :func:`xen.referee_adaptive.gate_stack_adaptive`; the ONLY difference is
    ``strategy = realized_bps`` (the engine-realized / bracket-realized per-bar net bps) instead of
    ``strategy_return_bps_turnover(returns, positions)``. The vs-naive L3 control leg stays on the
    frozen per-held-bar **market-return** reference (a fixed reference; identical seam scope to
    :func:`xen.referee_adaptive.gate_stack_core_costfn`). All sub-primitives are the frozen ones.

    Parameters
    ----------
    returns : np.ndarray
        Real next-step (open-to-open ``<= t-1``) market returns, fractional. Used for the naive
        control leg only; the signal leg comes from ``realized_bps``.
    positions : np.ndarray
        Signal positions in ``{-1, 0, +1}`` (episode / turnover counts; sub-pop episode means).
    realized_bps : np.ndarray
        Per-bar realized strategy net return in **bps** (already cost-charged), aligned to
        ``returns``. For a position-state strategy with no limit fill this equals
        ``strategy_return_bps_turnover(returns, positions, cost_bps=cost_bps)`` (the reduction
        identity); for a P*-fill strategy it is the engine's realized fill series.
    domain : str
        ``"1h"`` or ``"4h"`` (selects the frozen ``DomainSpec`` + materiality).
    cost_bps : float
        Round-trip cost (bps) for the naive control leg's cost charging.
    n_bootstrap : int
        Block-bootstrap resamples (passed through to the frozen bootstrap pair).
    seed : int
        Bootstrap seed (frozen ``seed + 1 .. seed + 4`` sub-seeding reused).
    q : float, default ``SUBPOP_QUANTILE``
        Sub-population quantile (frozen ``q* = 0.75``).
    split_index : int or None
        Train/test cut; ``None`` uses the frozen default split.

    Returns
    -------
    dict[str, Any]
        Same schema as :func:`xen.referee_adaptive.gate_stack_adaptive`, consumable by
        :func:`xen.referee_adaptive.adaptive_row` unchanged.
    """
    spec = DOMAIN_SPECS[domain]
    materiality_bps = materiality_bps_for(domain)
    strategy = np.asarray(realized_bps, dtype=float)        # <-- the one change vs gate_stack_adaptive
    naive = strategy_return_bps(returns, naive_momentum_positions(returns), cost_bps=cost_bps)
    if len(strategy) != len(naive):
        raise ValueError(
            f"realized_bps length {len(strategy)} must match market-return length {len(naive)}")
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


def gate_stack_pstar_reduces_to_adaptive(
    returns: np.ndarray,
    positions: np.ndarray,
    *,
    domain: str,
    cost_bps: float,
    n_bootstrap: int,
    seed: int,
    q: float = SUBPOP_QUANTILE,
    split_index: int | None = None,
) -> bool:
    """Reduction identity (EXP-007 Arm R): with realized := turnover, pstar core == adaptive core.

    Proves :func:`gate_stack_pstar` is §10.3a plus a pure signal-leg source swap. Returns ``True``
    iff the two core dicts are bit-identical (NaN-aware array equality) for the given inputs.
    """
    realized = strategy_return_bps_turnover(returns, positions, cost_bps=cost_bps)
    a = gate_stack_adaptive(returns, positions, domain=domain, cost_bps=cost_bps,
                            n_bootstrap=n_bootstrap, seed=seed, q=q, split_index=split_index)
    b = gate_stack_pstar(returns, positions, realized, domain=domain, cost_bps=cost_bps,
                         n_bootstrap=n_bootstrap, seed=seed, q=q, split_index=split_index)
    return _cores_equal(a, b)


def _cores_equal(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """NaN-aware deep equality for two gate-core dicts (same keys, arrays, scalars)."""
    if a.keys() != b.keys():
        return False
    for key in a:
        va, vb = a[key], b[key]
        if isinstance(va, np.ndarray) or isinstance(vb, np.ndarray):
            va, vb = np.asarray(va, dtype=float), np.asarray(vb, dtype=float)
            if va.shape != vb.shape or not np.array_equal(va, vb, equal_nan=True):
                return False
        elif isinstance(va, float) or isinstance(vb, float):
            if not (va == vb or (math.isnan(float(va)) and math.isnan(float(vb)))):
                return False
        elif va != vb:
            return False
    return True


# --------------------------------------------------------------------------- #
# Realized-fill construct for synthetic calibration substrates (NOT for real runs).
# --------------------------------------------------------------------------- #
def make_realized_fill(
    returns: np.ndarray,
    positions: np.ndarray,
    *,
    fav_limit_bps: float,
    adv_limit_bps: float,
    cost_bps: float,
) -> np.ndarray:
    """Causal resting-bracket realized per-bar NET bps series — CALIBRATION SUBSTRATE ONLY.

    Synthetic analog of the cTrader engine's ``ExitFillPrice`` emission (EXP-006): a held position's
    per-bar directional return is realized through a **resting bracket** — a favourable limit
    (take-profit) at ``+fav_limit_bps`` and an adverse limit (stop) at ``-adv_limit_bps``, both
    **rested from ``<= t-1``** (constants known before the bar opens; causal). The bar's directional
    return ``dir * returns[t]`` is clipped to ``[-adv_limit_bps, +fav_limit_bps]`` (a net-return
    bracket; without an intrabar high/low path this approximates "limit touched", and is symmetric
    and unbiased when ``fav == adv`` — the EXP-007 N1 control). Round-trip ``cost_bps`` is charged
    **once per entry** (a position change into a non-zero state — binding-leg amortized cost, L-02),
    matching :func:`strategy_return_bps_turnover`. Flat bars contribute ``0``.

    This is a calibration construct (EXP-007 Arms N/P): it is never used to adjudicate a real price
    strategy — the engine's realized fill is. Provenance: output ``[t]`` reads ``returns[t]`` (the
    bar's own realized outcome) and ``positions[t-1..t]`` (entry detection); the bracket limits are
    rested constants. No future bar is read.

    Parameters
    ----------
    returns : np.ndarray
        Per-bar open-to-open market returns (fractional), aligned to ``positions``.
    positions : np.ndarray
        Per-bar positions in ``{-1, 0, +1}``.
    fav_limit_bps, adv_limit_bps : float
        Favourable (take-profit) and adverse (stop) bracket half-widths in bps (``>= 0``).
    cost_bps : float
        Round-trip cost charged once per entry.

    Returns
    -------
    np.ndarray
        Per-bar realized strategy net return in bps, same length as ``returns``.
    """
    if fav_limit_bps < 0.0 or adv_limit_bps < 0.0:
        raise ValueError("bracket limits must be non-negative bps")
    r = np.asarray(returns, dtype=float)
    pos = np.asarray(positions, dtype=float)
    if r.shape != pos.shape:
        raise ValueError(f"returns {r.shape} and positions {pos.shape} must align")
    directional_bps = pos * r * 10_000.0
    realized = np.clip(directional_bps, -adv_limit_bps, fav_limit_bps)
    realized = np.where(pos != 0.0, realized, 0.0)
    # Amortized cost: charge once per entry (transition into a non-zero state).
    prev = np.concatenate(([0.0], pos[:-1]))
    entries = (pos != 0.0) & (pos != prev)
    realized = realized - np.where(entries, cost_bps, 0.0)
    return realized
