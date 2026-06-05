"""Track B incremental-information / portfolio-fitness machinery (Phase 003).

This module implements the predeclared Phase 003 incremental unit: it judges a
candidate signal ``C`` by the **incremental net edge it adds beyond a reference
signal ``R``** (the economic reading is *portfolio fitness*). It reuses the frozen
``xen.referee_calibration`` primitives (cost model, block bootstrap, episode
counts, Wilson/percentile CIs) unchanged and adds three things:

1. **Marginal net-P&L estimator (D-incr-form).** ``marginal_net_series`` builds the
   model-free incremental P&L of adding C to a book holding R: combine positions
   additively then clip to the per-domain position bound, take the marginal
   position ``m = combined - R``, evaluate it on **real-price** returns, and charge
   the **incremental** turnover cost only where C changes the book. No linear /
   i.i.d. / stationarity model of the R-C relationship is imposed, so dependence
   cannot manufacture a phantom linear-residual edge.
2. **Known-truth R/C substrate (D-incr-substrate).** ``build_rc_substrate`` plants a
   blockwise latent state, partitions episodes into R-only / C-change / overlap /
   inactive masks, and optionally plants a marginal edge ``m`` on the C-change rows.
   With no planted edge it is the **redundancy null**: R and C share structure but
   C adds no marginal edge.
3. **Legged incremental referee (D-incr-legs).** ``incremental_gate_*`` generalises
   the frozen 5-check gate to the conditional claim: L3 "naive control" becomes
   "reference control" (C must add edge *beyond* R), L1 readiness / L2 significance
   / L4 cross-market apply to the relevant positions, and L5 is the incremental-edge
   materiality buffer.

================================================================================
OPERATOR-CONFIRMATION-GATED DESIGN CHOICES (checkpoint D-incr-form / -substrate /
-legs; ``PHASE003-TRACKB-PREDECLARATION-CONFIRMED`` token required before any Track
B measurement is read). These are defensible defaults that encode the scope; they
must be confirmed or overridden at the Stage 4 gate:

- **Position bound** = 1 (directional signals in {-1,0,+1}); combined = clip(R+C).
- **Denominator** = bars where the combined position differs from R-alone (m != 0).
- **Incremental cost** = the per-episode round-trip cost amortised across the
  episode: ``cost_bps / episode_length`` per denominator bar. This is the smallest
  faithful "cost on the incremental turnover C induces" reading; it is exact when
  C-change episodes are isolated (which the per-episode 25% mask assignment makes
  typical). Consequence: the redundancy null reads approximately
  ``-cost_bps / episode_length`` (a small negative *cost drag*, never a phantom
  positive). High-cost instruments at short episodes (notably BTCUSD on 1h/4h) can
  exceed the tight ``max(0.5, 15% of materiality)`` null band; those cells are
  reported as cost-dominated / under-powered, not as phantom-edge failures. The
  binding control -- **no phantom POSITIVE edge from shared structure** -- holds
  regardless.
- **Leg mapping** (per EXP-014 scope coverage matrix). The matrix requires states
  that are unreachable under CI-monotone legs (L3 FAIL with L5 PASS; redundant C
  with L4 PASS), so the legs are deliberately orthogonal: L2 = standalone-C
  significance (C is individually positive, CI lower > 0); L3 = incremental-beyond-R
  significance (marginal CI lower > 0 = reference control); L4 = cross-market
  confirmation (the incremental edge does not reverse sign across the two segments);
  L5 = incremental-edge materiality as a POINT-magnitude test (point estimate >
  buffer, orthogonal to L3 significance). L2/L3 use genuinely different series and
  L3/L5 test different dimensions, so each leg fails independently.

  NOTE (adversarial-review F02): these legs are deliberately *less conservative*
  than the frozen Phase 001 strict gate (L2 reads standalone-C rather than the
  incremental position; L4 is "no material sign reversal" rather than "both segments
  positive"; L5 is a point test rather than a CI-lower test). That reduced
  conservatism, and the first-principles rationale for each departure, is recorded in
  the Phase 003 checkpoint amendment
  ``checkpoints/2026-06-04-003-.../amendments/2026-06-04-A1-incremental-unit-corrections.md``.
  The legs must NOT be treated as validated for freeze until that rationale is
  operator-accepted; EXP-014 confirms internal consistency, not independent soundness.
================================================================================
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import numpy as np

from xen.referee_calibration import (
    DOMAIN_SPECS,
    MeanCI,
    block_bootstrap_means,
    ci_from_means,
    cost_bps_for,
    count_state_episodes,
    estimate_block_length,
    finite_values,
    materiality_bps_for,
    resolve_split_index,
    strategy_return_bps,
)

# Per-domain blockwise latent-state episode length (D-incr-substrate). Frozen.
EPISODE_LENGTHS: dict[str, int] = {"5m": 24, "1h": 8, "4h": 4}
# Per-domain directional position bound for the combined book (D-incr-form).
POSITION_BOUND: float = 1.0
# Seeded R/C masks (D-incr-substrate). Each episode is assigned wholly to one mask,
# targeting equal shares so ~25% of eligible rows fall in each mask.
RC_MASKS: tuple[str, ...] = ("R_only", "C_change", "overlap", "inactive")


@dataclass(frozen=True)
class RCSubstrate:
    """A constructed known-truth R/C substrate for one cell/draw."""

    scoped_returns: np.ndarray   # real returns plus any planted marginal drift
    r_positions: np.ndarray
    c_positions: np.ndarray
    planted_edge_bps: float
    episode_length: int
    cost_bps: float
    mask_fractions: dict[str, float]
    denominator_count: int


# --------------------------------------------------------------------------- #
# Position combination + marginal net-P&L estimator (D-incr-form)
# --------------------------------------------------------------------------- #
def combine_positions(
    r_positions: np.ndarray, c_positions: np.ndarray, *, bound: float = POSITION_BOUND
) -> np.ndarray:
    """Additive-then-clipped combined book position (D-incr-form combination rule)."""
    combined = np.asarray(r_positions, dtype=float) + np.asarray(c_positions, dtype=float)
    return np.clip(combined, -bound, bound)


def per_bar_incremental_cost(cost_bps: float, episode_length: int) -> float:
    """Amortised per-episode round-trip incremental cost per denominator bar.

    One C-change episode incurs one round trip (enter + exit) = ``cost_bps``,
    amortised across its ``episode_length`` denominator bars. See the module-level
    design note: this is the smallest faithful "cost on the incremental turnover C
    induces" reading and is exact for isolated C-change episodes.
    """
    return cost_bps / max(int(episode_length), 1)


def marginal_net_series(
    scoped_returns: np.ndarray,
    r_positions: np.ndarray,
    c_positions: np.ndarray,
    *,
    cost_bps: float,
    episode_length: int,
    bound: float = POSITION_BOUND,
) -> dict[str, Any]:
    """Model-free marginal net P&L of adding C to a book holding R.

    Incremental edge = (combined book *with* C) minus (combined book *without* C),
    per eligible bar, on real-price returns, charging cost only on the incremental
    turnover C induces. Imposes no linear / i.i.d. / stationarity model of the R-C
    relationship.

    Parameters
    ----------
    scoped_returns : np.ndarray
        Real next-step returns (fractional), possibly with a planted marginal drift.
    r_positions, c_positions : np.ndarray
        Reference and candidate positions in ``{-1, 0, +1}``.
    cost_bps : float
        Round-trip cost (bps) for the instrument/domain.
    episode_length : int
        Blockwise episode length used to amortise the incremental round-trip cost.
    bound : float
        Per-domain position bound for the combined book.

    Returns
    -------
    dict[str, Any]
        ``net_denominator`` (per-denominator-bar net marginal bps, chronological),
        ``gross_denominator`` (cost-free), ``net_full`` (the full-length, time-
        contiguous net marginal series with zeros off the denominator -- used for
        autocorrelation-aware block-length estimation; see ``_contiguous_block_length``),
        ``denominator_mask`` (full length), ``per_bar_cost``, and the denominator count.
    """
    n = min(len(scoped_returns), len(r_positions), len(c_positions))
    ret = np.asarray(scoped_returns[:n], dtype=float)
    r = np.asarray(r_positions[:n], dtype=float)
    c = np.asarray(c_positions[:n], dtype=float)
    combined = combine_positions(r, c, bound=bound)
    marginal = combined - r
    denom_mask = marginal != 0.0
    cost = per_bar_incremental_cost(cost_bps, episode_length)
    gross_full = marginal * ret * 10_000.0
    net_full = gross_full - cost * denom_mask.astype(float)
    return {
        "net_denominator": net_full[denom_mask],
        "gross_denominator": gross_full[denom_mask],
        "net_full": net_full,
        "denominator_mask": denom_mask,
        "per_bar_cost_bps": cost,
        "denominator_count": int(np.count_nonzero(denom_mask)),
    }


def _contiguous_block_length(
    contiguous_series: np.ndarray | None,
    fallback_series: np.ndarray,
    split_index: int | None,
) -> int:
    """Block length from the contiguous (pre-mask) marginal series when available.

    The incremental denominator is a *gap-extraction* of the marginal series
    (``net_full[denom_mask]``), which discards the time gaps between C-active
    episodes. ``estimate_block_length`` on that gap-extracted series therefore sees
    no cross-episode autocorrelation and collapses to ``1`` -- an effectively i.i.d.
    bootstrap that ignores within-episode dependence (adversarial-review F04).

    Estimating instead on the full-length, time-contiguous ``net_full`` series (zeros
    off the denominator preserve the real time axis) recovers the true scale of
    dependence: it returns ~episode-scale blocks for episode-coherent candidates and
    ~1 for genuinely per-row signals, so both the CI and ``effective_n`` count the
    number of independent *episodes*, not the raw bar count. This keeps the legged
    machinery free of the i.i.d. assumption (governance section 2 / D-incr-form) for
    autocorrelated real candidates, not just for the synthetic substrate.

    Falls back to the gap-extracted train segment when no contiguous series is given.
    """
    if contiguous_series is None:
        return estimate_block_length(fallback_series)
    contiguous = finite_values(contiguous_series)
    if len(contiguous) == 0:
        return estimate_block_length(fallback_series)
    cut = resolve_split_index(len(contiguous), split_index)
    return estimate_block_length(contiguous[:cut])


def incremental_edge_ci(
    net_denominator: np.ndarray,
    *,
    alpha: float,
    n_bootstrap: int,
    seed: int,
    split_index: int | None = None,
    block_series: np.ndarray | None = None,
) -> tuple[MeanCI, int]:
    """Stationary block-bootstrap CI of the incremental edge on the marginal series.

    The bootstrap runs on the test segment of the (chronological) denominator series,
    exactly as the frozen referee does. The block length is estimated on
    ``block_series`` -- the contiguous, full-length ``net_full`` marginal series -- so
    within-episode autocorrelation is preserved instead of being destroyed by
    gap-extraction (adversarial-review F04; see ``_contiguous_block_length``). When
    ``block_series`` is omitted it falls back to the gap-extracted train segment.
    Returns ``(MeanCI, block_length)``.
    """
    series = finite_values(net_denominator)
    if len(series) == 0:
        return MeanCI(float("nan"), float("nan"), float("nan"), 0), 1
    cut = resolve_split_index(len(series), split_index)
    train, test = series[:cut], series[cut:]
    block_length = _contiguous_block_length(block_series, train, split_index)
    means, sample_mean, n = block_bootstrap_means(
        test, n_resamples=n_bootstrap, block_length=block_length, seed=seed
    )
    return ci_from_means(sample_mean, means, n, alpha=alpha), block_length


# --------------------------------------------------------------------------- #
# Known-truth R/C substrate (D-incr-substrate)
# --------------------------------------------------------------------------- #
def _blockwise_state(n: int, episode_length: int, rng: np.random.Generator) -> np.ndarray:
    """Blockwise latent state in {-1,+1}; each episode of length L has one sign."""
    n_episodes = (n + episode_length - 1) // episode_length
    signs = rng.choice(np.array([-1.0, 1.0]), size=n_episodes)
    return np.repeat(signs, episode_length)[:n]


def _assign_episode_masks(
    n: int, episode_length: int, rng: np.random.Generator
) -> np.ndarray:
    """Assign each whole episode to one of the four masks, ~25% of rows each.

    Episodes are assigned by a seeded permutation split into four equal groups, so
    each mask receives ~25% of episodes (hence ~25% of rows). Per-episode assignment
    keeps R, C, and the marginal position blockwise, which keeps incremental
    turnover sparse (one round trip per C-change episode).
    """
    n_episodes = (n + episode_length - 1) // episode_length
    order = rng.permutation(n_episodes)
    mask_by_episode = np.empty(n_episodes, dtype=object)
    for rank, episode in enumerate(order):
        mask_by_episode[episode] = RC_MASKS[rank % len(RC_MASKS)]
    return np.repeat(mask_by_episode, episode_length)[:n]


def build_rc_substrate(
    real_returns: np.ndarray,
    *,
    domain: str,
    instrument: str,
    seed: int,
    planted_edge_bps: float,
    bound: float = POSITION_BOUND,
) -> RCSubstrate:
    """Construct a seeded known-truth R/C substrate (positive or redundancy null).

    Latent state ``S`` is blockwise with the domain episode length. Episodes are
    partitioned into R-only / C-change / overlap / inactive masks. ``R = S`` on
    R-only and overlap (else 0); ``C = S`` on C-change and overlap (else 0). The
    combined book differs from R-alone only on C-change (the incremental
    denominator). For ``planted_edge_bps > 0`` a drift is added on the C-change rows
    so the expected **net** marginal P&L on the denominator equals ``planted_edge_bps``
    after the amortised incremental cost; for ``0`` it is the redundancy null.

    Parameters
    ----------
    real_returns : np.ndarray
        Real next-step returns for the domain.
    domain, instrument : str
        Used for the episode length, cost, and seeding.
    seed : int
        Deterministic seed for the latent state and mask assignment.
    planted_edge_bps : float
        Marginal edge to plant on the denominator (0 = redundancy null).
    bound : float
        Combined-book position bound.

    Returns
    -------
    RCSubstrate
        The scoped returns and R/C positions plus construction metadata.
    """
    n = len(real_returns)
    episode_length = EPISODE_LENGTHS[domain]
    cost_bps = cost_bps_for(instrument, domain)
    rng = np.random.default_rng(seed)
    state = _blockwise_state(n, episode_length, rng)
    masks = _assign_episode_masks(n, episode_length, rng)

    r_active = np.isin(masks, ["R_only", "overlap"])
    c_active = np.isin(masks, ["C_change", "overlap"])
    r_positions = np.where(r_active, state, 0.0)
    c_positions = np.where(c_active, state, 0.0)

    # Denominator = bars where combined differs from R-alone = the C-change mask.
    c_change_mask = masks == "C_change"
    scoped = np.asarray(real_returns, dtype=float).copy()
    if planted_edge_bps > 0.0:
        cost = per_bar_incremental_cost(cost_bps, episode_length)
        # Solve drift so net marginal P&L on the denominator equals the planted edge.
        delta_return = (planted_edge_bps + cost) / 10_000.0
        scoped[c_change_mask] = scoped[c_change_mask] + state[c_change_mask] * delta_return

    total = max(n, 1)
    mask_fractions = {m: float(np.count_nonzero(masks == m)) / total for m in RC_MASKS}
    return RCSubstrate(
        scoped_returns=scoped,
        r_positions=r_positions,
        c_positions=c_positions,
        planted_edge_bps=float(planted_edge_bps),
        episode_length=episode_length,
        cost_bps=cost_bps,
        mask_fractions=mask_fractions,
        denominator_count=int(np.count_nonzero(c_change_mask)),
    )


# --------------------------------------------------------------------------- #
# Legged incremental referee (D-incr-legs)
# --------------------------------------------------------------------------- #
def incremental_gate_core(
    scoped_returns: np.ndarray,
    r_positions: np.ndarray,
    c_positions: np.ndarray,
    *,
    instrument: str,
    domain: str,
    n_bootstrap: int,
    seed: int,
    split_index: int | None = None,
    episode_length: int | None = None,
) -> dict[str, Any]:
    """Alpha-independent incremental-referee state for one (R, C) evaluation.

    Computes (i) the standalone candidate net series (for L2 significance), (ii) the
    marginal net series beyond R (for L3 reference-control, L5 materiality, effect),
    and the alpha-free L1 readiness / L4 cross-market legs on the incremental
    position. Bootstrap-mean distributions are computed once and reused across the
    alpha grid by :func:`incremental_gate_row`.
    """
    spec = DOMAIN_SPECS[domain]
    cost_bps = cost_bps_for(instrument, domain)
    materiality_bps = materiality_bps_for(domain)
    ep_len = episode_length if episode_length is not None else EPISODE_LENGTHS[domain]

    # Standalone candidate net series (L2): C judged on its own, frozen cost model.
    standalone = strategy_return_bps(scoped_returns, c_positions, cost_bps=cost_bps)

    # Marginal (incremental) net series on the denominator (L3 / L5 / effect).
    marginal = marginal_net_series(
        scoped_returns, r_positions, c_positions, cost_bps=cost_bps, episode_length=ep_len
    )
    net_denominator = finite_values(marginal["net_denominator"])
    denom_count = marginal["denominator_count"]

    # L1 readiness on the incremental position: enough effective denominator and
    # enough up/down incremental episodes (both directions present, train and test).
    combined = combine_positions(r_positions, c_positions)
    m_pos = combined - np.asarray(r_positions, dtype=float)
    cut_full = resolve_split_index(len(m_pos), split_index)
    inc_train_up = count_state_episodes(m_pos[:cut_full], 1.0)
    inc_train_down = count_state_episodes(m_pos[:cut_full], -1.0)
    inc_test_up = count_state_episodes(m_pos[cut_full:], 1.0)
    inc_test_down = count_state_episodes(m_pos[cut_full:], -1.0)

    # Block bootstrap on the marginal series for L3/L5 (incremental edge CI). The
    # block length is estimated on the contiguous, full-length ``net_full`` series so
    # within-episode autocorrelation is captured rather than being destroyed by
    # gap-extraction (adversarial-review F04); effective_n then counts independent
    # episodes, not raw denominator bars.
    inc_cut = resolve_split_index(len(net_denominator), None)
    inc_train, inc_test = net_denominator[:inc_cut], net_denominator[inc_cut:]
    inc_block = _contiguous_block_length(marginal.get("net_full"), inc_train, None)
    inc_means, inc_mean, inc_n = block_bootstrap_means(
        inc_test, n_resamples=n_bootstrap, block_length=inc_block, seed=seed + 1
    )
    effective_n = len(inc_test) / max(inc_block, 1)
    l1 = bool(
        effective_n >= spec.min_effective_n
        and min(inc_train_up, inc_train_down, inc_test_up, inc_test_down) >= spec.min_state_count
    )
    # L4 cross-market: the incremental edge must CONFIRM across the two segments
    # (train/test stand in for two market regimes), i.e. it does not REVERSE sign.
    # A redundant C with no marginal edge (consistent ~0 cost drag) confirms; a C
    # whose edge flips sign across regimes is unconfirmed. This sign-consistency
    # reading (not strict both-positive) is the predeclared D-incr-legs choice that
    # reproduces the EXP-014 coverage matrix (redundant passes L4; the reversal
    # fixture fails it); confirm or override at the Stage 4 gate.
    inc_train_mean = float(np.mean(inc_train)) if len(inc_train) else 0.0
    inc_test_mean = float(np.mean(inc_test)) if len(inc_test) else 0.0
    # Only a MATERIAL reversal (both segments exceed the materiality buffer in
    # opposite directions) counts as missing cross-market confirmation; an
    # immaterial near-zero flip (e.g. the redundancy null's cost drag) confirms.
    eps = materiality_bps
    l4 = not (
        (inc_train_mean > eps and inc_test_mean < -eps)
        or (inc_train_mean < -eps and inc_test_mean > eps)
    )

    # Standalone bootstrap for L2 significance (frozen split convention).
    s_cut = resolve_split_index(len(standalone), split_index)
    s_block = estimate_block_length(standalone[:s_cut])
    s_means, s_mean, s_n = block_bootstrap_means(
        standalone[s_cut:], n_resamples=n_bootstrap, block_length=s_block, seed=seed + 2
    )
    return {
        "inc_means": inc_means,
        "inc_mean": inc_mean,
        "inc_n": inc_n,
        "inc_block": inc_block,
        "standalone_means": s_means,
        "standalone_mean": s_mean,
        "standalone_n": s_n,
        "effective_n": effective_n,
        "denominator_count": denom_count,
        "materiality_bps": materiality_bps,
        "cost_bps": cost_bps,
        "l1": l1,
        "l4": l4,
        "inc_train_mean": inc_train_mean,
        "inc_test_mean": inc_test_mean,
        "inc_train_up": inc_train_up,
        "inc_train_down": inc_train_down,
        "inc_test_up": inc_test_up,
        "inc_test_down": inc_test_down,
    }


def incremental_gate_row(core: dict[str, Any], *, alpha: float) -> dict[str, Any]:
    """Assemble the incremental-referee verdict row for one alpha from its core.

    Legs (D-incr-legs / EXP-014 coverage matrix). L3 and L5 are deliberately
    orthogonal so the matrix's L3-fail/L5-pass cell is reachable:
    - L1 readiness: incremental denominator effective-n and up/down episode counts.
    - L2 significance: standalone candidate net edge CI lower bound > 0 (C is
      individually a positive signal).
    - L3 reference-control: incremental-beyond-R edge CI lower bound > 0 (C's
      marginal edge significantly excludes zero = it beats the reference).
    - L4 cross-market: the incremental edge does not reverse sign across the two
      segments (cross-regime confirmation).
    - L5 materiality: incremental edge POINT estimate > the materiality buffer
      (economic magnitude; orthogonal to L3 significance). This point-magnitude
      reading is the predeclared D-incr-legs choice that makes the matrix's
      independent L3/L5 cells reachable; confirm or override at the Stage 4 gate.
    """
    ci_inc = ci_from_means(core["inc_mean"], core["inc_means"], core["inc_n"], alpha=alpha)
    ci_standalone = ci_from_means(
        core["standalone_mean"], core["standalone_means"], core["standalone_n"], alpha=alpha
    )
    l1, l4 = core["l1"], core["l4"]
    l2 = bool(np.isfinite(ci_standalone.lower) and ci_standalone.lower > 0.0)
    l3 = bool(np.isfinite(ci_inc.lower) and ci_inc.lower > 0.0)
    l5 = bool(np.isfinite(ci_inc.mean) and ci_inc.mean > core["materiality_bps"])
    passed = bool(l1 and l2 and l3 and l4 and l5)
    leg_results = {
        "L1_readiness": l1,
        "L2_significance": l2,
        "L3_reference_control": l3,
        "L4_cross_market": l4,
        "L5_materiality": l5,
        "materiality_bps": core["materiality_bps"],
        "incremental_ci_lower_bps": ci_inc.lower,
        "standalone_ci_lower_bps": ci_standalone.lower,
        "denominator_count": core["denominator_count"],
    }
    return {
        "referee": "incremental_gate",
        "alpha": alpha,
        "verdict": "PASS" if passed else "REJECT",
        "passed": passed,
        "incremental_edge_bps": ci_inc.mean,
        "incremental_ci_lower_bps": ci_inc.lower,
        "incremental_ci_upper_bps": ci_inc.upper,
        "standalone_edge_bps": ci_standalone.mean,
        "standalone_ci_lower_bps": ci_standalone.lower,
        "effective_n": core["effective_n"],
        "block_length": core["inc_block"],
        "denominator_count": core["denominator_count"],
        "leg_results": json.dumps(leg_results, sort_keys=True),
    }


def incremental_gate_verdict(
    scoped_returns: np.ndarray,
    r_positions: np.ndarray,
    c_positions: np.ndarray,
    *,
    instrument: str,
    domain: str,
    alpha: float,
    n_bootstrap: int,
    seed: int,
    split_index: int | None = None,
    episode_length: int | None = None,
) -> dict[str, Any]:
    """Single-alpha incremental-referee verdict (core + row convenience wrapper)."""
    core = incremental_gate_core(
        scoped_returns,
        r_positions,
        c_positions,
        instrument=instrument,
        domain=domain,
        n_bootstrap=n_bootstrap,
        seed=seed,
        split_index=split_index,
        episode_length=episode_length,
    )
    return incremental_gate_row(core, alpha=alpha)
