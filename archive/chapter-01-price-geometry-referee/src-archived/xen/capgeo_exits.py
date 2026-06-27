"""Frozen mechanical exit-derivation rule for CF-CAPGEO-001 (EXP-082 / D0 §D3).

This module is the **binding artifact** of the Phase 018 "derive" step. It implements the
ratified D0 §D3 triple-barrier exit-derivation rule as a single pure function,
:func:`derive_barriers`, that maps a frozen-entry substrate-cell's TRAIN return-structure
statistics (produced by EXP-081, ``xen.capgeo_geometry``) to a triple-barrier exit
``(T_fav, S_adv, H_cap)`` for each of the three registered ``/EXIT-DERIVED`` candidates:

- ``D1-MEDIAN-CAPTURE``    — ``T_fav = MFE_med``, ``S_adv = m_anti else MAE_q90``,           ``H_cap = TTP_q75``
- ``D2-TAIL-ROBUST``       — ``T_fav = MFE_med``, ``S_adv = min(m_anti, MAE_q90) else MAE_q90``, ``H_cap = TTP_q75``
- ``D3-CAPTURE-EFFICIENT`` — ``T_fav = MFE_q40``, ``S_adv = m_anti else MAE_q90``,           ``H_cap = TTP_med``

The adverse leg is **left-tail-parameterized**: it engages the catastrophic-minority boundary
``m_anti`` (the MAE antimode/dip location) wherever the dip resolves, else falls back to
``MAE_q90``. ``D2``'s "tightened to the dip" (D0 §D3) is the parameter-free
``min(m_anti, MAE_q90)`` — the *tighter* of the dip stop and the q90 stop — a distinct function
from ``D1`` (which keeps ``m_anti`` even were it wider). The two diverge iff a cell has
``m_anti > MAE_q90``; on power-limited data where ``m_anti`` resolves rarely and below
``MAE_q90`` they coincide numerically (a disclosed derivation outcome, not a defect — D0 §D9).

``T_fav``/``S_adv`` are in **ATR units** (EXP-081 normalization); ``H_cap`` is in **domain
bars** (``max(1, round(ttp_quantile))``, round-half-to-even). The function is **pure**: no I/O,
no globals, no RNG, no side effects — so EXP-083 imports it and calls it per walk-forward
fold-TRAIN for the causal barrier re-fit (D3/D5/D4.1), asserting the same source hash first.

No exit is *applied* here (that is EXP-083): this module only *constructs* the barrier triples.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# --------------------------------------------------------------------------- #
# Frozen candidate identifiers (registered /EXIT-DERIVED items; D0 §D2)
# --------------------------------------------------------------------------- #
D1_MEDIAN_CAPTURE: str = "D1-MEDIAN-CAPTURE"
D2_TAIL_ROBUST: str = "D2-TAIL-ROBUST"
D3_CAPTURE_EFFICIENT: str = "D3-CAPTURE-EFFICIENT"
CANDIDATES: tuple[str, ...] = (D1_MEDIAN_CAPTURE, D2_TAIL_ROBUST, D3_CAPTURE_EFFICIENT)


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CellStats:
    """The D3 input statistics for one substrate-cell (EXP-081 ``capgeo_geometry`` outputs).

    All distances are ATR-normalized; ``ttp_*`` are bars. ``m_anti`` is ``NaN`` when the MAE
    distribution is unimodal to the Hartigan dip (the common case — D0 §D9).
    """

    mfe_med: float
    mfe_q40: float
    ttp_med: float
    ttp_q75: float
    mae_q90: float
    m_anti: float


@dataclass(frozen=True)
class Barrier:
    """One derived triple-barrier exit for one (cell, candidate).

    ``s_adv_source`` records whether the adverse leg resolved to the dip antimode (``"m_anti"``)
    or the fallback quantile (``"mae_q90"``); ``h_cap_pre_round`` carries the pre-integerization
    ``ttp`` quantile for audit.
    """

    candidate: str
    t_fav: float
    s_adv: float
    h_cap: int
    s_adv_source: str
    h_cap_pre_round: float


# --------------------------------------------------------------------------- #
# Pure computation — the frozen D3 rule
# --------------------------------------------------------------------------- #
def _is_finite(x: float) -> bool:
    """True iff ``x`` is a finite real (the explicit ``m_anti`` resolution test)."""
    return isinstance(x, (int, float)) and math.isfinite(float(x))


def _h_cap_bars(ttp_quantile: float) -> tuple[int, float]:
    """Integerize a TTP quantile to a time-cap in bars: ``max(1, round-half-even(q))``.

    Returns ``(h_cap_bars, pre_round_float)``. ``round`` is Python's round-half-to-even, matching
    the analysis-plan freeze; the floor at 1 guarantees a valid (>=1-bar) holding window.
    """
    pre = float(ttp_quantile)
    return max(1, int(round(pre))), pre


def _s_adv_d1_d3(stats: CellStats) -> tuple[float, str]:
    """Adverse leg for D1/D3: ``m_anti`` if it resolves, else the ``MAE_q90`` fallback."""
    if _is_finite(stats.m_anti):
        return float(stats.m_anti), "m_anti"
    return float(stats.mae_q90), "mae_q90"


def _s_adv_d2(stats: CellStats) -> tuple[float, str]:
    """Adverse leg for D2 ("tightened to the dip"): ``min(m_anti, MAE_q90)`` if the dip resolves,
    else the ``MAE_q90`` fallback. Tighter-or-equal to D1; diverges iff ``m_anti > MAE_q90``."""
    if _is_finite(stats.m_anti):
        tightened = min(float(stats.m_anti), float(stats.mae_q90))
        # Source label reflects which value the min selected (the dip when it is the tighter stop).
        source = "m_anti" if tightened == float(stats.m_anti) else "mae_q90"
        return tightened, source
    return float(stats.mae_q90), "mae_q90"


def derive_barriers(stats: CellStats) -> dict[str, Barrier]:
    """Apply the frozen D0 §D3 rule to one cell's stats, returning a barrier per candidate.

    Parameters
    ----------
    stats : CellStats
        The cell's EXP-081 D3-input statistics (ATR units / bars).

    Returns
    -------
    dict[str, Barrier]
        ``{candidate_id: Barrier}`` for ``D1-MEDIAN-CAPTURE``, ``D2-TAIL-ROBUST``,
        ``D3-CAPTURE-EFFICIENT``. Pure: identical input yields identical output.
    """
    s_d1, src_d1 = _s_adv_d1_d3(stats)
    s_d2, src_d2 = _s_adv_d2(stats)
    s_d3, src_d3 = _s_adv_d1_d3(stats)

    h_q75, h_q75_pre = _h_cap_bars(stats.ttp_q75)
    h_med, h_med_pre = _h_cap_bars(stats.ttp_med)

    return {
        D1_MEDIAN_CAPTURE: Barrier(
            candidate=D1_MEDIAN_CAPTURE, t_fav=float(stats.mfe_med), s_adv=s_d1, h_cap=h_q75,
            s_adv_source=src_d1, h_cap_pre_round=h_q75_pre),
        D2_TAIL_ROBUST: Barrier(
            candidate=D2_TAIL_ROBUST, t_fav=float(stats.mfe_med), s_adv=s_d2, h_cap=h_q75,
            s_adv_source=src_d2, h_cap_pre_round=h_q75_pre),
        D3_CAPTURE_EFFICIENT: Barrier(
            candidate=D3_CAPTURE_EFFICIENT, t_fav=float(stats.mfe_q40), s_adv=s_d3, h_cap=h_med,
            s_adv_source=src_d3, h_cap_pre_round=h_med_pre),
    }
