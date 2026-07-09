"""Native target-based reversion metrics for CF-MR-003 / EXP-009 — does price return to the anchor?

Replaces EXP-008's fixed-horizon MFE-toward-anchor (a volatility-confounded max-excursion) with
**target-based** reads on real intrabar prices, each measured over an **event-specific** horizon tied to
the event's own fitted half-life:

  * anchor-hit          — did real price touch the entry-fixed anchor level within the horizon?
  * fraction-recovered  — how much of the entry dislocation was recovered toward the anchor (capped 1.0)?
  * time-to-anchor      — bars to first touch (censored), in half-life units.

Provenance contract (which timestamps each output reads)
--------------------------------------------------------
- The anchor **target level** and fade side are taken at the **prior** bar: `a_level_lag[i]` and
  `dev_lag[i]` are the caller-lagged (`[i-1]`) anchor price and deviation — the values known at bar `i`'s
  open. The entry reference is `open_[i]`. The horizon `H_i` is derived from `hl[i]`, the event's fitted
  half-life over the trailing screen window ending `i-1`.
- The outcome scans **real** `low[i..i+H_i-1]` / `high[i..i+H_i-1]` — strictly forward of the entry open;
  future bars enter only as the measured outcome, never as a decision input. No forming-bar OHLC feeds a
  decision. Synthetic prices are never used (real intrabar High/Low only).

Deterministic; the caller owns real-price discipline, event selection, and the control population.
"""
from __future__ import annotations

import numpy as np

# Dislocation-|z| bin edges (design §5): B1 [2,2.5), B2 [2.5,3), B3 [3,inf).
ZBIN_EDGES: tuple[float, ...] = (2.0, 2.5, 3.0, np.inf)


def anchor_price_level(series: str, exec_close: np.ndarray, dev: np.ndarray) -> np.ndarray:
    """Recover the anchor **price** level per exec bar from the deviation.

    Price-space series (S1 CENTER / S2 RANGE / S4 OU): ``dev = price - a`` -> ``a = close - dev``.
    Log-space series (S3 DETREND / S5 SPREAD): ``dev = log(price) - a_log`` -> ``a = close * exp(-dev)``.
    """
    if series in ("S3_DETREND", "S5_SPREAD"):
        return exec_close * np.exp(-dev)
    return exec_close - dev


def event_horizon(hl: np.ndarray, m: int, h_cap: int) -> np.ndarray:
    """Event-specific native horizon ``H_i = min(h_cap, ceil(m*hl))`` (0 where hl not finite/positive)."""
    hl = np.asarray(hl, dtype=np.float64)
    out = np.zeros(hl.shape[0], dtype=np.int64)
    ok = np.isfinite(hl) & (hl > 0)
    out[ok] = np.minimum(h_cap, np.ceil(m * hl[ok])).astype(np.int64)
    return out


def dislocation_bin(abs_z: float, edges: tuple[float, ...] = ZBIN_EDGES) -> int:
    """Return the |z| bin index (0..len(edges)-2), or -1 if below the lowest edge."""
    for b in range(len(edges) - 1):
        if edges[b] <= abs_z < edges[b + 1]:
            return b
    return -1


def measure_entry(i: int, open_: np.ndarray, low: np.ndarray, high: np.ndarray, a: float, s: float,
                  H: int, hl_scale: float, reverse: bool = False) -> tuple[float, float, float] | None:
    """One entry's (hit, frac, ttime) over horizon ``H`` toward anchor price ``a``; None if invalid.

    ``a`` = entry-fixed anchor price, ``s`` = fade side (``sign(dev[i-1])``), ``hl_scale`` = half-life for
    the time-in-HL-units read. ``reverse=True`` scans the **backward** window ``[i-H+1..i]`` — the
    time-reversal leak tripwire (a causal reversion must not survive). Real intrabar prices only.
    """
    n = open_.shape[0]
    if H < 1 or not np.isfinite(s) or s == 0.0 or not np.isfinite(a):
        return None
    if reverse:
        lo0, hi0 = i - H + 1, i + 1
        if lo0 < 0:
            return None
    else:
        lo0, hi0 = i, i + H
        if hi0 > n:
            return None
    o = open_[i]
    if s > 0.0:                                                # short: fall to the anchor
        D = o - a
        if not (D > 0):
            return None
        seg = low[lo0:hi0]
        fav = o - float(np.min(seg))
        reached = seg <= a
    else:                                                      # long: rise to the anchor
        D = a - o
        if not (D > 0):
            return None
        seg = high[lo0:hi0]
        fav = float(np.max(seg)) - o
        reached = seg >= a
    touched = np.flatnonzero(reached)
    tt = int(touched[0] + 1) if touched.size else H
    ttime = tt / hl_scale if np.isfinite(hl_scale) and hl_scale > 0 else np.nan
    return (1.0 if touched.size else 0.0, min(fav / D, 1.0), ttime)


def event_target_metrics(idx: np.ndarray, open_: np.ndarray, low: np.ndarray, high: np.ndarray,
                         a_level_lag: np.ndarray, dev_lag: np.ndarray, hl: np.ndarray,
                         horizon: np.ndarray) -> dict[str, np.ndarray]:
    """Per-entry native target metrics over each entry's own horizon (real intrabar prices).

    Parameters
    ----------
    idx : np.ndarray
        Entry (act-bar) indices to evaluate.
    open_, low, high : np.ndarray
        Real exec-domain OHLC arrays.
    a_level_lag, dev_lag : np.ndarray
        Caller-lagged (``[i-1]``) anchor **price** level and deviation (decision-time values).
    hl : np.ndarray
        Per-bar fitted half-life (used to express time-to-anchor in half-life units).
    horizon : np.ndarray
        Per-bar event horizon ``H_i`` (bars); 0 -> skip.

    Returns
    -------
    dict
        ``idx`` (kept), ``hit`` (0/1), ``frac`` (0..1), ``ttime`` (half-life units). Entries with a
        degenerate horizon, no remaining dislocation at the open, or an incomplete forward window are
        dropped (kept idx tells the caller which survived).
    """
    keep, hit, frac, ttime = [], [], [], []
    for i in idx:
        r = measure_entry(int(i), open_, low, high, a_level_lag[i], dev_lag[i], int(horizon[i]), hl[i])
        if r is None:
            continue
        keep.append(int(i))
        hit.append(r[0]); frac.append(r[1]); ttime.append(r[2])
    return {"idx": np.asarray(keep, dtype=np.int64), "hit": np.asarray(hit, dtype=np.float64),
            "frac": np.asarray(frac, dtype=np.float64), "ttime": np.asarray(ttime, dtype=np.float64)}
