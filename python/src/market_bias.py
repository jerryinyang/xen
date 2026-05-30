"""Deterministic chart-timeframe port of the Market Bias (CEREBR) indicator.

Source: ``docs/planning/market-bias.txt`` (TradingView Pine v5, MPL-2.0,
© Professeur_X). Ported for Xen Phase 005 / EXP-035 in **chart-timeframe mode
only**: the indicator timeframe equals the bar timeframe, so the Pine
``request.security`` / ``indexHighTF`` / ``indexCurrTF`` machinery collapses to
identity (``f_no_repaint_request`` returns its expression unchanged) and there
is no multitimeframe or real-time lookahead-offset semantics to reproduce. The
port therefore implements only the local EMA / Heiken-Ashi recursion.

Two source-fidelity hazards from the audit are implemented explicitly:

1. The HA-open recursion keys off ``xhaopen[1]`` (the prior bar's ``(o+c)/2``),
   NOT the standard ``haopen[1]``. See :func:`_heiken_ashi`.
2. Pine ``ta.ema`` seeding. Pine seeds an EMA from the first available value;
   different platforms seed with the SMA of the first ``length`` values. The
   exact seed only affects a finite transient. Rather than assume one
   convention, :func:`convergence_warmup` runs the full pipeline under both an
   SMA seed and a cold (first-value) seed and reports the bar index beyond
   which the resulting state labels are identical — the predeclared,
   discretion-free warmup rule for EXP-035.

No exported TradingView reference series is currently available, so callers may
claim only "deterministic re-implementation of the published Pine formula," not
Pine-equivalence (EXP-035 scope, amendment 4).

All outputs are derived from EMA-smoothed construction values of the real OHLC.
These construction values define states only; any forward-return or P&L outcome
(EXP-037 and later) must use the aggregated real OHLC, never these values.
"""
from __future__ import annotations

import numpy as np
import polars as pl


HA_LEN = 100
HA_LEN2 = 100
OSC_LEN = 7
WARMUP_FLOOR = 300

SIGN_BULL = "bull"
SIGN_BEAR = "bear"
STRONG_BULL = "strong_bull"
WEAK_BULL = "weak_bull"
STRONG_BEAR = "strong_bear"
WEAK_BEAR = "weak_bear"

_REQUIRED_COLUMNS = ("CloseTime", "Open", "High", "Low", "Close")


def _ema(values: np.ndarray, length: int, seed: str) -> np.ndarray:
    """Causal EMA with a selectable seed convention.

    Steady-state recursion is ``alpha * x[i] + (1 - alpha) * ema[i-1]`` with
    ``alpha = 2 / (length + 1)`` for every convention; only the seed differs.

    Parameters
    ----------
    values : np.ndarray
        Source series (float64). May contain leading NaN (propagated).
    length : int
        EMA period.
    seed : str
        ``"cold"`` seeds ``ema[0] = values[0]``. ``"sma"`` seeds
        ``ema[length-1] = mean(values[:length])`` and leaves earlier values
        NaN; if fewer than ``length`` finite values exist it falls back to a
        cold seed to stay finite.

    Returns
    -------
    np.ndarray
        EMA series (float64), same length as ``values``.
    """
    n = values.shape[0]
    out = np.full(n, np.nan, dtype=float)
    if n == 0:
        return out
    alpha = 2.0 / (length + 1.0)
    if seed == "sma" and n >= length and np.all(np.isfinite(values[:length])):
        out[length - 1] = float(values[:length].mean())
        start = length
    else:
        out[0] = values[0]
        start = 1
    for i in range(start, n):
        prev = out[i - 1]
        out[i] = values[i] if not np.isfinite(prev) else alpha * values[i] + (1.0 - alpha) * prev
    return out


def _heiken_ashi(
    o: np.ndarray,
    h: np.ndarray,
    l: np.ndarray,
    c: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Source HA transform on smoothed OHLC, returning (haopen, haclose).

    Implements the published recursion exactly:
        haclose = (o + h + l + c) / 4
        xhaopen = (o + c) / 2
        haopen[i] = (xhaopen[i-1] + haclose[i-1]) / 2   for i >= 1
        haopen[0] = (o[0] + c[0]) / 2
    Note the recursion keys off ``xhaopen[i-1]`` (the prior bar's ``(o+c)/2``),
    not the prior ``haopen``.
    """
    haclose = (o + h + l + c) / 4.0
    xhaopen = (o + c) / 2.0
    haopen = np.full_like(haclose, np.nan)
    n = haopen.shape[0]
    if n == 0:
        return haopen, haclose
    haopen[0] = (o[0] + c[0]) / 2.0
    for i in range(1, n):
        haopen[i] = (xhaopen[i - 1] + haclose[i - 1]) / 2.0
    return haopen, haclose


def _oscillator(
    o: np.ndarray,
    h: np.ndarray,
    l: np.ndarray,
    c: np.ndarray,
    seed: str,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (osc_bias, osc_smooth) from raw OHLC under one seed convention."""
    sm_o = _ema(o, HA_LEN, seed)
    sm_h = _ema(h, HA_LEN, seed)
    sm_l = _ema(l, HA_LEN, seed)
    sm_c = _ema(c, HA_LEN, seed)
    haopen, haclose = _heiken_ashi(sm_o, sm_h, sm_l, sm_c)
    o2 = _ema(haopen, HA_LEN2, seed)
    c2 = _ema(haclose, HA_LEN2, seed)
    osc_bias = 100.0 * (c2 - o2)
    osc_smooth = _ema(osc_bias, OSC_LEN, seed)
    return osc_bias, osc_smooth


def _sign_states(osc_bias: np.ndarray) -> np.ndarray:
    """Sign-only state with the measure-zero ``osc_bias == 0`` tie carried.

    Returns an object array of {``"bull"``, ``"bear"``, ``None``}. NaN bias
    (pre-seed bars) maps to ``None``. An exact-zero bias carries the prior
    resolved sign; if no prior sign exists yet the bar stays ``None``.
    """
    n = osc_bias.shape[0]
    states = np.full(n, None, dtype=object)
    prev = None
    for i in range(n):
        x = osc_bias[i]
        if not np.isfinite(x):
            states[i] = None
            continue
        if x > 0.0:
            prev = SIGN_BULL
        elif x < 0.0:
            prev = SIGN_BEAR
        # x == 0.0 -> keep prev (tie carried)
        states[i] = prev
    return states


def _four_way_states(osc_bias: np.ndarray, osc_smooth: np.ndarray) -> np.ndarray:
    """Four-way state matching the Pine ``sigcolor`` switch."""
    n = osc_bias.shape[0]
    states = np.full(n, None, dtype=object)
    finite = np.isfinite(osc_bias) & np.isfinite(osc_smooth)
    bull = finite & (osc_bias > 0.0)
    bear = finite & (osc_bias < 0.0)
    states[bull & (osc_bias >= osc_smooth)] = STRONG_BULL
    states[bull & (osc_bias < osc_smooth)] = WEAK_BULL
    states[bear & (osc_bias <= osc_smooth)] = STRONG_BEAR
    states[bear & (osc_bias > osc_smooth)] = WEAK_BEAR
    return states


def compute_market_bias(bars: pl.DataFrame, seed: str = "sma") -> pl.DataFrame:
    """Compute Market Bias columns on chart-timeframe aggregated real bars.

    Parameters
    ----------
    bars : pl.DataFrame
        Aggregated OHLC bars sorted by ``CloseTime``; must contain
        ``CloseTime, Open, High, Low, Close``.
    seed : str, default "sma"
        EMA seed convention (``"sma"`` or ``"cold"``). Beyond the convergence
        warmup the two seeds produce identical state labels, so the choice does
        not affect post-warmup readiness; ``"sma"`` is the default canonical
        seed for the determinism digest.

    Returns
    -------
    pl.DataFrame
        ``bars`` with added columns ``osc_bias`` (float), ``osc_smooth``
        (float), ``sign_state`` (str/null), ``four_way_state`` (str/null).
    """
    missing = [c for c in _REQUIRED_COLUMNS if c not in bars.columns]
    if missing:
        raise ValueError(f"bars is missing required columns: {missing}")
    if bars.is_empty():
        return bars.with_columns(
            pl.lit(None, dtype=pl.Float64).alias("osc_bias"),
            pl.lit(None, dtype=pl.Float64).alias("osc_smooth"),
            pl.lit(None, dtype=pl.String).alias("sign_state"),
            pl.lit(None, dtype=pl.String).alias("four_way_state"),
        )
    o = bars["Open"].to_numpy().astype(float)
    h = bars["High"].to_numpy().astype(float)
    l = bars["Low"].to_numpy().astype(float)
    c = bars["Close"].to_numpy().astype(float)
    osc_bias, osc_smooth = _oscillator(o, h, l, c, seed)
    sign_state = _sign_states(osc_bias)
    four_way_state = _four_way_states(osc_bias, osc_smooth)
    return bars.with_columns(
        pl.Series("osc_bias", osc_bias),
        pl.Series("osc_smooth", osc_smooth),
        pl.Series("sign_state", sign_state.tolist(), dtype=pl.String),
        pl.Series("four_way_state", four_way_state.tolist(), dtype=pl.String),
    )


def convergence_warmup(bars: pl.DataFrame, floor: int = WARMUP_FLOOR) -> dict[str, int | bool]:
    """Determine the predeclared two-seeding warmup length.

    Runs the full pipeline under both the SMA seed and the cold seed and finds
    the smallest index ``W`` beyond which the four-way state labels are
    identical for all subsequent bars, floored at ``floor``.

    Parameters
    ----------
    bars : pl.DataFrame
        Aggregated OHLC bars (typically the full analysis-set series; the
        warmup prefix lies in the train segment).
    floor : int, default 300
        Minimum warmup length (3x the nominal EMA period).

    Returns
    -------
    dict
        ``w_converge`` (first index of permanent label agreement, or n if the
        sequences never agree at the tail), ``W`` (``max(w_converge, floor)``),
        and ``converged`` (True iff agreement holds through the final bar).
    """
    sma = compute_market_bias(bars, seed="sma")["four_way_state"].to_numpy()
    cold = compute_market_bias(bars, seed="cold")["four_way_state"].to_numpy()
    n = sma.shape[0]
    both_defined = np.array(
        [sma[i] is not None and cold[i] is not None for i in range(n)]
    )
    differ = np.array(
        [both_defined[i] and sma[i] != cold[i] for i in range(n)]
    )
    if differ.any():
        last_diff = int(np.flatnonzero(differ).max())
        w_converge = last_diff + 1
    else:
        defined_idx = np.flatnonzero(both_defined)
        w_converge = int(defined_idx[0]) if defined_idx.size else n
    converged = bool(w_converge < n)
    return {
        "w_converge": int(w_converge),
        "W": int(max(w_converge, floor)),
        "converged": converged,
    }
