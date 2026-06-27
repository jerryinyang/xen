"""Leak-canary regression for L-01 (the look-ahead that shipped a false DEPLOYABLE_CONFIRMED).

Self-contained, deterministic encoding of the causal-provenance detection logic the Chapter-02
auditor must apply. It does NOT touch market data or the holdout.

The Chapter-01 leak: an exit's favourable limit used ``rct_target[di]`` — information from bar
``di`` itself — to act *during* bar ``di``. The live-actable choice is ``rct_target[di-1]``. A
signal that conditions on the **same bar** it acts in manufactures an edge against the favourable
next move; the same signal conditioned only on the **prior bar** carries no edge on i.i.d. data.

Two discriminating facts the provenance trace + leak tripwire rely on:

1. A same-bar (look-ahead) signal shows a large edge; the prior-bar (causal) signal does not.
2. A future-destroying shuffle leaves the same-bar look-ahead edge intact (it never depended on
   time order) — which is exactly how the tripwire flags a leak.
"""

from __future__ import annotations

import numpy as np


def _series(n: int = 50_000, seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.standard_normal(n) * 0.01  # i.i.d. next-step returns


def _favourable(returns: np.ndarray) -> np.ndarray:
    """Favourable side of each bar's realized next move (the exit's target)."""
    return np.maximum(returns, 0.0)


def _edge(signal: np.ndarray, favourable: np.ndarray) -> float:
    """Signal-conditional mean favourable capture (the 'edge')."""
    return float(np.mean(signal * favourable))


def test_lookahead_signal_has_edge_causal_signal_does_not() -> None:
    returns = _series()
    fav = _favourable(returns)
    # Look-ahead: condition on the SAME bar we act in (knows the sign of its own move).
    edge_lookahead = _edge(np.sign(returns), fav)
    # Causal: condition only on the PRIOR bar.
    edge_causal = _edge(np.sign(np.roll(returns, 1)), fav)

    assert edge_lookahead > 1e-3, "same-bar look-ahead must manufacture a positive edge"
    assert abs(edge_causal) < 0.05 * edge_lookahead, (
        "the prior-bar (causal) signal must carry essentially no edge on i.i.d. data — "
        "an edge that exists only with same-bar conditioning is the L-01 look-ahead signature"
    )


def test_future_shuffle_tripwire_flags_the_leak() -> None:
    returns = _series()
    fav = _favourable(returns)
    rng = np.random.default_rng(11)
    shuffled = returns.copy()
    rng.shuffle(shuffled)  # destroy time order / any future information

    # The look-ahead edge SURVIVES the shuffle (it never depended on time order) ⇒ leak detected.
    leak_real = _edge(np.sign(returns), fav)
    leak_shuffled = _edge(np.sign(shuffled), _favourable(shuffled))
    assert leak_shuffled > 0.5 * leak_real, (
        "a look-ahead edge survives a future-destroying shuffle ⇒ leak detected (REJECT-class)"
    )

    # The causal signal has ~0 edge before and after the shuffle — no real edge ever existed.
    causal_real = _edge(np.sign(np.roll(returns, 1)), fav)
    causal_shuffled = _edge(np.sign(np.roll(shuffled, 1)), _favourable(shuffled))
    assert abs(causal_real) < 0.05 * leak_real
    assert abs(causal_shuffled) < 0.05 * leak_real
