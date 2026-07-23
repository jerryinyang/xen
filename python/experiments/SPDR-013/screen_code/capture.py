"""TF capture geometry (design §4, frozen) — cut losers quickly, let winners run.

Two engines that share one rule set:

* :func:`simulate_signal` — the LIVE, sequential, causal engine driven by a per-bar signal
  ``s[t] in {-1,0,+1}`` decided on completed bar ``t`` and actioned at ``open[t+1]``. Handles
  reverse-on-flip and flat-on-zero (§4 opposite-signal), one position per symbol, and the
  "stop may exit earlier without reverse until next signal" leg rule.
* :func:`simulate_independent` — a vectorised batch engine for the MATCHED-RANDOM-ENTRY control:
  independent episodes (entry_idx, side) with no signal, exiting only on stop / trail / time cap.
  It replicates :func:`simulate_signal`'s stop/trail timeline exactly (asserted in golden traces).

Timeline (causal): the stop governing bar ``j`` is a function of opens through ``j-1`` and the
entry; ``open[j]`` is the actionable price at bar ``j``. Stop TOUCH uses bar ``j``'s high/low and,
per §4 / IN-3, exits at ``open[j]`` on an adverse gap-open or at ``open[j+1]`` on an intrabar touch.
HWM is the running extreme of OPENS (IN-2).
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
    out = (signal != 0) & (signal != prev)
    return out


# ------------------------------------------------------- live engine ----


def _init_stop(entry_open: float, side: int, atr_e: float) -> float:
    return entry_open - side * INITIAL_STOP_ATR * atr_e


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


def simulate_signal(
    slot_start: np.ndarray,
    open_: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    atr: np.ndarray,
    signal: np.ndarray,
    cap: int,
    start: int,
) -> list[dict]:
    """Run the live capture engine and return one dict per closed episode.

    Parameters
    ----------
    slot_start : np.ndarray
        Bar open timestamps (int ns) — used for funding-stamp counting downstream.
    open_, high, low : np.ndarray
        Completed-bar OHLC of one clock.
    atr : np.ndarray
        Wilder ATR(14); the engine reads ``atr[entry-1]`` (lagged) at entry (§3.1).
    signal : np.ndarray
        Per-bar side ``in {-1,0,+1}`` decided on completed bar t; actioned at ``open[t+1]``.
    cap : int
        Time cap in bars (H1 48 / M15 192).
    start : int
        First bar with a valid ATR (warm-up boundary); no decision before ``start+1``.

    Returns
    -------
    list[dict]
        Episodes with entry/exit index, price, timestamp, side, gross bps, exit reason.
    """
    n = open_.size
    ls = leg_starts(signal)
    episodes: list[dict] = []

    pos = 0
    entry_idx = -1
    entry_open = np.nan
    atr_e = np.nan
    stop = np.nan
    hwm = np.nan
    pending = False

    a = max(start + 1, 1)
    for j in range(a, n):
        sig = int(signal[j - 1])
        # ---- exit if in position (all decisions at open[j]) ----
        if pos != 0:
            d = pos
            exited = False
            reason = ""
            if sig != d:
                exited, reason = True, "SIGNAL"
            elif (j - entry_idx) >= cap:
                exited, reason = True, "TIME_CAP"
            elif (d == 1 and open_[j] <= stop) or (d == -1 and open_[j] >= stop):
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
                })
                pos = 0
                pending = False
            else:
                # no exit at open -> intrabar touch schedules next-open exit, else trail
                if d == 1 and low[j] <= stop:
                    pending = True
                elif d == -1 and high[j] >= stop:
                    pending = True
                else:
                    if d == 1:
                        hwm = max(hwm, float(open_[j]))
                    else:
                        hwm = min(hwm, float(open_[j]))
                    stop = _tighten(stop, d, entry_open, hwm, atr_e)
        # ---- entry if flat (same bar re-entry allowed after a SIGNAL exit) ----
        if pos == 0 and ls[j - 1] and np.isfinite(atr[j - 1]):
            pos = sig
            entry_idx = j
            entry_open = float(open_[j])
            atr_e = float(atr[j - 1])
            stop = _init_stop(entry_open, pos, atr_e)
            hwm = entry_open
            pending = False

    # close any still-open episode at the last available open (band edge)
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
        })
    return episodes


# ---------------------------------------------------- batch engine ----


def simulate_independent(
    open_: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    atr: np.ndarray,
    entry_idx: np.ndarray,
    side: np.ndarray,
    cap: int,
) -> dict:
    """Vectorised batch of INDEPENDENT episodes (no signal) — MATCHED-RANDOM-ENTRY control.

    Each episode enters at ``open[entry_idx]`` with ``atr[entry_idx-1]`` and exits on stop / trail /
    time cap using the identical §4 timeline as :func:`simulate_signal`. Returns arrays aligned to
    the input episodes: ``exit_idx``, ``exit_open``, ``gross_bps``, ``hold_bars``.
    """
    n = open_.size
    E = entry_idx.size
    entry_idx = entry_idx.astype(np.int64)
    side = side.astype(np.int64)
    atr_e = atr[entry_idx - 1].astype(float)
    entry_open = open_[entry_idx].astype(float)
    stop = entry_open - side * INITIAL_STOP_ATR * atr_e
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
        b = np.where(in_range, bar, 0)          # safe gather index
        o = open_[b]
        hi = high[b]
        lo = low[b]
        # (1) pending intrabar touch -> exit at this bar's open
        do_pending = in_range & pending
        if do_pending.any():
            exit_idx[do_pending] = bar[do_pending]
            exit_open[do_pending] = o[do_pending]
            active[do_pending] = False
        # (2) remaining active: gap-open beyond stop, or time cap -> exit at open
        rem = in_range & active & ~pending
        gap = ((side == 1) & (o <= stop)) | ((side == -1) & (o >= stop))
        timecap = np.full(E, k >= cap)
        do_open = rem & (gap | timecap)
        if do_open.any():
            exit_idx[do_open] = bar[do_open]
            exit_open[do_open] = o[do_open]
            active[do_open] = False
        # (3) still active: intrabar touch schedules next-open exit; else trail
        rem2 = in_range & active & ~pending
        touch = ((side == 1) & (lo <= stop)) | ((side == -1) & (hi >= stop))
        pending[rem2 & touch] = True
        upd = rem2 & ~touch
        if upd.any():
            new_hwm = np.where(side == 1, np.maximum(hwm, o), np.minimum(hwm, o))
            hwm = np.where(upd, new_hwm, hwm)
            fav = side * (hwm - entry_open)
            trig = fav >= TRAIL_TRIGGER_ATR * atr_e
            lock = entry_open + side * TRAIL_LOCK_ATR * atr_e
            ratchet = hwm - side * TRAIL_RATCHET_ATR * atr_e
            tightened = np.where(
                side > 0, np.maximum.reduce([stop, lock, ratchet]),
                np.minimum.reduce([stop, lock, ratchet]),
            )
            stop = np.where(upd & trig, tightened, stop)

    # force-close anything still active (pending or ran past cap window) at last valid open
    left = active
    if left.any():
        last_bar = np.minimum(entry_idx + cap, n - 1)
        exit_idx[left] = last_bar[left]
        exit_open[left] = open_[last_bar[left]]
    valid = np.isfinite(atr_e) & (entry_idx >= 1)
    gross = np.where(valid, side * (exit_open / entry_open - 1.0) * 1e4, np.nan)
    return {
        "exit_idx": exit_idx,
        "exit_open": exit_open,
        "gross_bps": gross,
        "hold_bars": exit_idx - entry_idx,
        "valid": valid,
    }
