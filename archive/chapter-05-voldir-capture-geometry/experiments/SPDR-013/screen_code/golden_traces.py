"""Golden traces G1-G3 (design §9) — hand-checkable anchors + engine consistency.

G1  BTCUSDT D-SMA14: first signal flip after 2022-09-14; SMA14 by hand from H1 closes; entry = next
    hour open; confirm side.
G2  ETHUSDT stop: synthetic path where the low breaches entry-1.5*ATR — the §4 exit rule fires.
G3  SOLUSDT D-ZZ: one confirmed swing; magnitude/angle/path_noise recomputed from OHLC vs the
    linear bridge (match to 1e-6 rel).

Plus an engine-parity check: the vectorised batch engine reproduces the sequential engine on a set
of independent (no-signal) episodes (design §4 rule identity).
"""
from __future__ import annotations

from datetime import datetime, timezone

import numpy as np

from arms import sma_signal
from capture import _init_stop, simulate_independent, simulate_signal
from config import ATR_PERIOD, INITIAL_STOP_ATR
from indicators import atr_zigzag, sma, wilder_atr


def g1_sma_flip(close: np.ndarray, open_: np.ndarray, slot_start: np.ndarray,
                atr_lag: np.ndarray) -> dict:
    after = int(datetime(2022, 9, 14, tzinfo=timezone.utc).timestamp() * 1e9)
    sig = sma_signal(close, atr_lag, 14, "off")
    m = sma(close, 14)
    idx = np.where(slot_start >= after)[0]
    flip = None
    for t in idx[:-1]:
        if t >= 1 and sig[t] != 0 and sig[t - 1] != 0 and sig[t] != sig[t - 1]:
            flip = int(t)
            break
    if flip is None:
        return {"found": False}
    hand_sma = float(np.mean(close[flip - 13: flip + 1]))
    return {
        "found": True, "flip_idx": flip,
        "flip_ts": int(slot_start[flip]),
        "sma14_engine": float(m[flip]), "sma14_hand": hand_sma,
        "sma_match": bool(abs(m[flip] - hand_sma) < 1e-6 * max(1.0, abs(hand_sma))),
        "close_at_flip": float(close[flip]), "signal_side": int(sig[flip]),
        "entry_next_open": float(open_[flip + 1]),
        "side_confirms": bool((sig[flip] == 1) == (close[flip] > m[flip])),
    }


def g2_stop_rule(atr_val: float = 100.0, entry_open: float = 10000.0) -> dict:
    """Synthetic: long entry, a bar whose low breaches entry-1.5*ATR → exit next open (§4/IN-3)."""
    stop = _init_stop(entry_open, 1, atr_val)
    n = 6
    open_ = np.array([entry_open, entry_open, entry_open, entry_open - 10, entry_open, entry_open])
    high = open_ + 20
    low = np.array([entry_open - 5, entry_open - 5, entry_open - 200, entry_open - 5,
                    entry_open - 5, entry_open - 5])   # bar 2 low breaches stop
    slot = np.arange(n, dtype=np.int64) * 3_600_000_000_000
    atr = np.full(n, atr_val)
    # one episode entered at bar 0
    sim = simulate_independent(open_, high, low, atr, np.array([1]), np.array([1]), cap=48)
    return {
        "stop_level": float(stop),
        "expected_stop_price": float(entry_open - INITIAL_STOP_ATR * atr_val),
        "breach_bar": 2, "exit_idx": int(sim["exit_idx"][0]),
        "exit_open": float(sim["exit_open"][0]),
        "exit_is_next_open_after_touch": bool(int(sim["exit_idx"][0]) == 3),
    }


def g3_zz_swing(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> dict:
    atr = wilder_atr(high, low, close, ATR_PERIOD)
    start = int(np.argmax(np.isfinite(atr)))
    swings = atr_zigzag(close, atr, start)
    if not swings:
        return {"found": False}
    sw = swings[0]
    # recompute features by hand
    mag = abs(sw.end_price - sw.start_price) / sw.start_price * 1e4
    bars = max(1, sw.end_idx - sw.start_idx)
    angle = mag / bars
    seg = np.arange(sw.start_idx, sw.end_idx + 1)
    bridge = sw.start_price + (sw.end_price - sw.start_price) * (seg - sw.start_idx) / bars
    dev = np.abs(close[sw.start_idx: sw.end_idx + 1] - bridge)
    atr_scale = np.nanmean(atr[sw.start_idx: sw.end_idx + 1])
    pn = float(np.mean(dev) / atr_scale)
    rel = lambda a, b: abs(a - b) / max(1e-9, abs(b))
    return {
        "found": True, "start_idx": sw.start_idx, "end_idx": sw.end_idx,
        "confirm_idx": sw.confirm_idx, "direction": sw.direction,
        "magnitude_bps": sw.magnitude_bps, "magnitude_hand": mag,
        "angle": sw.angle_bps_per_bar, "angle_hand": angle,
        "path_noise": sw.path_noise_atr, "path_noise_hand": pn,
        "match": bool(rel(sw.magnitude_bps, mag) < 1e-6 and rel(sw.angle_bps_per_bar, angle) < 1e-6
                      and rel(sw.path_noise_atr, pn) < 1e-6),
    }


def g3_independent_fixture() -> dict:
    """Independent numeric check of ``_swing_features`` (design §9 spirit; not self-referential).

    Fixed swing: start=100 (idx0) → end=110 (idx4); intermediate closes [100,103,104,108,110].
    Linear bridge = [100, 102.5, 105, 107.5, 110]; deviations = [0, 0.5, 1.0, 0.5, 0] → mean 0.4.
    ATR scale pinned to 2.0 over the swing → path_noise = 0.4/2.0 = 0.20 (hand-derived, no bridge
    code). magnitude = (110-100)/100*1e4 = 1000 bps; angle = 1000/4 = 250; direction +1.
    """
    from indicators import _swing_features
    close = np.array([100.0, 103.0, 104.0, 108.0, 110.0])
    atr = np.full(5, 2.0)
    sw = _swing_features(0, 4, 4, close, atr)
    exp = {"magnitude_bps": 1000.0, "angle": 250.0, "path_noise": 0.20, "direction": 1}
    rel = lambda a, b: abs(a - b) / max(1e-9, abs(b))
    return {
        "expected": exp,
        "got": {"magnitude_bps": sw.magnitude_bps, "angle": sw.angle_bps_per_bar,
                "path_noise": sw.path_noise_atr, "direction": sw.direction},
        "match": bool(rel(sw.magnitude_bps, 1000.0) < 1e-9 and rel(sw.angle_bps_per_bar, 250.0) < 1e-9
                      and rel(sw.path_noise_atr, 0.20) < 1e-9 and sw.direction == 1),
    }


def engine_parity(open_, high, low, atr, slot_start) -> dict:
    """Batch engine reproduces the sequential engine on independent (no-signal) episodes.

    Build a signal that enters once and never flips (so the sequential engine's only exits are
    stop/time-cap, matching the batch engine's independent-episode rules), for a few entry bars.
    """
    n = open_.size
    start = int(np.argmax(np.isfinite(atr)))
    entries = [i for i in range(start + 2, n - 300, max(1, (n - start) // 12))][:8]
    max_rel = 0.0
    checked = 0
    for e in entries:
        for side in (1, -1):
            sig = np.zeros(n)
            sig[e - 1:] = side               # single leg from bar e onward, never flips
            seq = simulate_signal(slot_start, open_, high, low, atr, sig, cap=48, start=start)
            if not seq:
                continue
            ep = seq[0]                       # first episode = the entry at e
            bat = simulate_independent(open_, high, low, atr,
                                       np.array([ep["entry_idx"]]), np.array([side]), cap=48)
            if not np.isfinite(bat["gross_bps"][0]):
                continue
            rel = abs(ep["gross_bps"] - float(bat["gross_bps"][0])) / max(1.0, abs(ep["gross_bps"]))
            max_rel = max(max_rel, rel)
            checked += 1
    return {"checked": checked, "max_rel_diff": float(max_rel),
            "parity_ok": bool(checked > 0 and max_rel < 1e-9)}
