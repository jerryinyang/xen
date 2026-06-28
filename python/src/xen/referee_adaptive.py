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

from typing import Any, Callable

import numpy as np
import polars as pl

from xen.referee_calibration import (
    DOMAIN_SPECS,
    _episode_counts,
    _gate_bootstrap_pair,
    estimate_block_length,
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
