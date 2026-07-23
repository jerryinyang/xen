"""TF capture geometry (design §4) with per-arm EXIT-MODE decomposition (AMENDMENT-A3).

Two engines share one rule set:

* :func:`simulate_signal` — LIVE, sequential, causal; driven by a per-bar signal
  ``s[t] in {-1,0,+1}`` decided on completed bar ``t`` and actioned at ``open[t+1]``.
* :func:`simulate_independent` — vectorised batch of independent episodes (entry_idx, side) for
  the MATCHED-RANDOM-ENTRY control; replicates the same stop/trail timeline.

**Exit modes (AMENDMENT-A3, operator-directed 2026-07-23).** The frozen §4 stack is the
``combined`` arm; each termination rule is also isolated as its own arm so the exit contribution
is diagnosable, not guessed:

| mode | use_stop | use_trail | use_time | use_signalflip | meaning |
|---|---|---|---|---|---|
| combined | ✓ | ✓ | ✓ | ✓ | full §4 stack (the design freeze) |
| stop | ✓ | | | | 1.5·ATR hard stop only |
| trail | | ✓ | | | trailing stop only (no initial hard stop) |
| time | | | ✓ | | time cap only |
| signalflip | | | | ✓ | reverse-on-flip only (ZZ ⇒ full structural leg) |

``stop_active = use_stop or use_trail``. With ``use_stop`` off but ``use_trail`` on the stop starts
unreachable (``-inf·side``) until the trail first tightens it (§4 trail: entry+0.5·ATR then
HWM−2·ATR ratchet). Timeline stays causal (stop governing bar j uses opens ≤ j−1 + entry; touch
uses bar j high/low; IN-2/IN-3). One position per symbol; re-entry only on the next signal leg.
"""
from __future__ import annotations

import numpy as np

from config import (
    INITIAL_STOP_ATR,
    TRAIL_LOCK_ATR,
    TRAIL_RATCHET_ATR,
    TRAIL_TRIGGER_ATR,
)


# ------------------------------------------------------ signal helpers ----


def leg_starts(signal: np.ndarray) -> np.ndarray:
    """Boolean: bar ``t`` begins a new nonzero signal leg (``s[t]!=0`` and ``s[t]!=s[t-1]``)."""
    n = signal.size
    out = np.zeros(n, dtype=bool)
    if n == 0:
        return out
    prev = np.empty(n)
    prev[0] = 0.0
    prev[1:] = signal[:-1]
    return (signal != 0) & (signal != prev)


def _init_stop(entry_open: float, side: int, atr_e: float, use_stop: bool = True,
               use_trail: bool = True) -> float:
    if use_stop:
        return entry_open - side * INITIAL_STOP_ATR * atr_e
    if use_trail:
        return -np.inf * side          # long: -inf (unreachable), short: +inf; trail may tighten
    return np.nan                       # no stop mechanism (stop_active False, never read)


def _tighten(stop: float, side: int, entry_open: float, hwm: float, atr_e: float) -> float:
    """Winner trail (§4): once favourable open-to-open excursion >= 1.0*ATR, lock to
    entry+0.5*ATR*side then ratchet by HWM-2.0*ATR*side. Only ever tightens toward price."""
    fav = side * (hwm - entry_open)
    if fav < TRAIL_TRIGGER_ATR * atr_e:
        return stop
    lock = entry_open + side * TRAIL_LOCK_ATR * atr_e
    ratchet = hwm - side * TRAIL_RATCHET_ATR * atr_e
    if side > 0:
        return max(stop, lock, ratchet)
    return min(stop, lock, ratchet)


# ------------------------------------------------------- live engine ----


def simulate_signal(
    slot_start: np.ndarray,
    open_: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    atr: np.ndarray,
    signal: np.ndarray,
    cap: int,
    start: int,
    *,
    use_stop: bool = True,
    use_trail: bool = True,
    use_time: bool = True,
    use_signalflip: bool = True,
) -> list[dict]:
    """Live capture engine → one dict per closed episode, under the selected exit modes.

    Parameters as documented at module top; ``atr[entry-1]`` (lagged) sets the stop scale (§3.1).
    Entries always fire on a new signal leg when flat; exits fire only via the ENABLED rules.
    """
    n = open_.size
    stop_active = use_stop or use_trail
    ls = leg_starts(signal)
    episodes: list[dict] = []

    pos = 0
    entry_idx = -1
    entry_open = np.nan
    atr_e = np.nan
    stop = np.nan
    hwm = np.nan
    pending = False
    mfe_oo = mae_oo = mfe_hi = 0.0        # realized-hold excursions (bps from entry_open)

    a = max(start + 1, 1)
    for j in range(a, n):
        sig = int(signal[j - 1])
        if pos != 0:
            d = pos
            # realized-hold excursion trackers (open-to-open + intrabar high/low), from entry_open
            fav_oo = d * (open_[j] / entry_open - 1.0) * 1e4
            mfe_oo = max(mfe_oo, fav_oo)
            mae_oo = min(mae_oo, fav_oo)
            fav_hi = d * ((high[j] if d == 1 else low[j]) / entry_open - 1.0) * 1e4
            mfe_hi = max(mfe_hi, fav_hi)
            exited = False
            reason = ""
            if use_signalflip and sig != d:
                exited, reason = True, "SIGNAL"
            elif use_time and (j - entry_idx) >= cap:
                exited, reason = True, "TIME_CAP"
            elif stop_active and ((d == 1 and open_[j] <= stop) or (d == -1 and open_[j] >= stop)):
                exited, reason = True, "STOP_OPEN"
            elif pending:
                exited, reason = True, "STOP_INTRABAR"
            if exited:
                exit_open = float(open_[j])
                gross = d * (exit_open / entry_open - 1.0) * 1e4
                episodes.append({
                    "entry_idx": entry_idx, "exit_idx": j, "side": d,
                    "entry_open": entry_open, "exit_open": exit_open,
                    "entry_ts": int(slot_start[entry_idx]), "exit_ts": int(slot_start[j]),
                    "gross_bps": float(gross), "hold_bars": j - entry_idx,
                    "exit_reason": reason, "atr_entry": float(atr_e),
                    "mfe_oo_bps": float(mfe_oo), "mae_oo_bps": float(mae_oo),
                    "mfe_hi_bps": float(mfe_hi),
                })
                pos = 0
                pending = False
            else:
                if stop_active and d == 1 and low[j] <= stop:
                    pending = True
                elif stop_active and d == -1 and high[j] >= stop:
                    pending = True
                elif use_trail:
                    hwm = max(hwm, float(open_[j])) if d == 1 else min(hwm, float(open_[j]))
                    stop = _tighten(stop, d, entry_open, hwm, atr_e)
        if pos == 0 and ls[j - 1] and np.isfinite(atr[j - 1]):
            pos = sig
            entry_idx = j
            entry_open = float(open_[j])
            atr_e = float(atr[j - 1])
            stop = _init_stop(entry_open, pos, atr_e, use_stop, use_trail)
            hwm = entry_open
            pending = False
            mfe_oo = mae_oo = mfe_hi = 0.0

    if pos != 0:
        j = n - 1
        exit_open = float(open_[j])
        gross = pos * (exit_open / entry_open - 1.0) * 1e4
        episodes.append({
            "entry_idx": entry_idx, "exit_idx": j, "side": pos,
            "entry_open": entry_open, "exit_open": exit_open,
            "entry_ts": int(slot_start[entry_idx]), "exit_ts": int(slot_start[j]),
            "gross_bps": float(gross), "hold_bars": j - entry_idx,
            "exit_reason": "BAND_EDGE", "atr_entry": float(atr_e),
            "mfe_oo_bps": float(mfe_oo), "mae_oo_bps": float(mae_oo),
            "mfe_hi_bps": float(mfe_hi),
        })
    return episodes


# ------------------------------------------------ horizon availability ----


def horizon_excursion(open_: np.ndarray, high: np.ndarray, low: np.ndarray,
                      entry_idx: np.ndarray, side: np.ndarray, cap: int) -> dict:
    """Fixed-horizon MFE/MAE over ``[entry+1, min(entry+cap, n-1)]`` REGARDLESS of the arm's exit
    (the availability the ENTRY grants if a better exit could capture it). Open-based (tradable
    mark) MFE/MAE plus an intrabar-high MFE ceiling. Vectorised over episodes.

    This is a NON-TRADABLE availability ceiling (it peeks at the within-horizon peak), used only to
    ask "available but capture geometry needs redefinition?" — never a strategy return.
    """
    n = open_.size
    E = entry_idx.size
    entry_idx = entry_idx.astype(np.int64)
    side = side.astype(np.int64)
    entry_open = open_[entry_idx].astype(float)
    mfe_oo = np.zeros(E)
    mae_oo = np.zeros(E)
    mfe_hi = np.zeros(E)
    for k in range(1, cap + 1):
        bar = entry_idx + k
        ok = bar < n
        if not ok.any():
            break
        b = np.where(ok, bar, 0)
        fav_oo = np.where(ok, side * (open_[b] / entry_open - 1.0) * 1e4, -np.inf)
        mfe_oo = np.maximum(mfe_oo, np.where(ok, fav_oo, mfe_oo))
        mae_oo = np.minimum(mae_oo, np.where(ok, fav_oo, mae_oo))
        px = np.where(side == 1, high[b], low[b])
        fav_hi = side * (px / entry_open - 1.0) * 1e4
        mfe_hi = np.maximum(mfe_hi, np.where(ok, fav_hi, mfe_hi))
    return {"horizon_mfe_oo_bps": mfe_oo, "horizon_mae_oo_bps": mae_oo,
            "horizon_mfe_hi_bps": mfe_hi}


# ---------------------------------------------------- batch engine ----


def simulate_independent(
    open_: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    atr: np.ndarray,
    entry_idx: np.ndarray,
    side: np.ndarray,
    cap: int,
    *,
    use_stop: bool = True,
    use_trail: bool = True,
) -> dict:
    """Vectorised batch of INDEPENDENT episodes — MATCHED-RANDOM-ENTRY control.

    Random entries have no signal, so the TIME CAP is always the terminal (matches the design's
    "same mean hold cap"); ``use_stop``/``use_trail`` select which stop mechanics also apply, to
    mirror the live arm's exit geometry. Returns arrays aligned to the input episodes.
    """
    n = open_.size
    E = entry_idx.size
    entry_idx = entry_idx.astype(np.int64)
    side = side.astype(np.int64)
    atr_e = atr[entry_idx - 1].astype(float)
    entry_open = open_[entry_idx].astype(float)
    stop_active = use_stop or use_trail
    if use_stop:
        stop = entry_open - side * INITIAL_STOP_ATR * atr_e
    else:
        stop = np.where(side > 0, -np.inf, np.inf)      # trail may tighten from unreachable
    hwm = entry_open.copy()
    active = np.isfinite(atr_e) & (entry_idx >= 1)
    pending = np.zeros(E, dtype=bool)
    exit_idx = np.full(E, n - 1, dtype=np.int64)
    exit_open = np.full(E, np.nan)

    for k in range(1, cap + 1):
        bar = entry_idx + k
        in_range = active & (bar < n)
        if not in_range.any():
            break
        b = np.where(in_range, bar, 0)
        o = open_[b]
        hi = high[b]
        lo = low[b]
        do_pending = in_range & pending
        if do_pending.any():
            exit_idx[do_pending] = bar[do_pending]
            exit_open[do_pending] = o[do_pending]
            active[do_pending] = False
        rem = in_range & active & ~pending
        gap = stop_active & (((side == 1) & (o <= stop)) | ((side == -1) & (o >= stop)))
        timecap = np.full(E, k >= cap)
        do_open = rem & (gap | timecap)
        if do_open.any():
            exit_idx[do_open] = bar[do_open]
            exit_open[do_open] = o[do_open]
            active[do_open] = False
        rem2 = in_range & active & ~pending
        if stop_active:
            touch = ((side == 1) & (lo <= stop)) | ((side == -1) & (hi >= stop))
            pending[rem2 & touch] = True
            rem2 = rem2 & ~touch
        if use_trail and rem2.any():
            new_hwm = np.where(side == 1, np.maximum(hwm, o), np.minimum(hwm, o))
            hwm = np.where(rem2, new_hwm, hwm)
            fav = side * (hwm - entry_open)
            trig = fav >= TRAIL_TRIGGER_ATR * atr_e
            lock = entry_open + side * TRAIL_LOCK_ATR * atr_e
            ratchet = hwm - side * TRAIL_RATCHET_ATR * atr_e
            tightened = np.where(
                side > 0, np.maximum.reduce([stop, lock, ratchet]),
                np.minimum.reduce([stop, lock, ratchet]),
            )
            stop = np.where(rem2 & trig, tightened, stop)

    left = active
    if left.any():
        last_bar = np.minimum(entry_idx + cap, n - 1)
        exit_idx[left] = last_bar[left]
        exit_open[left] = open_[last_bar[left]]
    valid = np.isfinite(atr_e) & (entry_idx >= 1)
    gross = np.where(valid, side * (exit_open / entry_open - 1.0) * 1e4, np.nan)
    return {
        "exit_idx": exit_idx, "exit_open": exit_open, "gross_bps": gross,
        "hold_bars": exit_idx - entry_idx, "valid": valid,
    }
