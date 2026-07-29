"""Fixed pivot-plus-momentum breakout entry (design §2). Not the research subject."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from config import ATR_PERIOD, L0_INACTIVE_HOLD_HOURS, NS
from fills import resolve_entry_stop
from panel import SymbolPanel


@dataclass
class Signal:
    symbol: str
    clock: str
    delta: float
    side: int  # +1 LONG, -1 SHORT
    decision_idx: int
    decision_end_ns: int
    stop_price: float
    atr20: float
    momentum_atr: float
    s_hat_bps: float
    s_hat_decile: float
    s_hat_rank: float
    abs_r_decision_bps: float
    abs_r_decile: float
    # fill (resolved later)
    filled: bool = False
    fill_ts: int = -1
    fill_price: float = float("nan")
    fill_kind: str = ""
    fill_m1_idx: int = -1
    suppressed: bool = False
    reason: str = "SIGNAL"


def detect_signals(panel: SymbolPanel, delta: float) -> list[Signal]:
    """All pivot+momentum signals on the decision clock at given deltaThreshold.

    Index [0] = decision bar (most recent confirmed). State ≤ t−1 relative to the live order
    (order is live after [0] closes). ATR20 and ŝ evaluated at [0].
    """
    h, lo, c = panel.high, panel.low, panel.close
    atr = panel.atr20
    n = c.size
    out: list[Signal] = []
    # need bars [2],[1],[0] → start at index 2
    for i in range(2, n):
        if not np.isfinite(atr[i]) or atr[i] <= 0:
            continue
        if i < ATR_PERIOD:
            continue
        # LONG: low[1] < min(low[0], low[2]) AND (close[0]-close[1])/ATR20 > delta
        # SHORT: high[1] > max(high[0], high[2]) AND -(close[0]-close[1])/ATR20 > delta
        # with [0]=i, [1]=i-1, [2]=i-2
        mom = (c[i] - c[i - 1]) / atr[i]
        long_pivot = lo[i - 1] < min(lo[i], lo[i - 2])
        short_pivot = h[i - 1] > max(h[i], h[i - 2])
        side = 0
        if long_pivot and mom > delta:
            side = 1
        elif short_pivot and (-mom) > delta:
            side = -1
        if side == 0:
            continue
        stop = float(h[i]) if side > 0 else float(lo[i])
        out.append(Signal(
            symbol=panel.symbol,
            clock=panel.clock,
            delta=float(delta),
            side=side,
            decision_idx=i,
            decision_end_ns=int(panel.slot_end[i]),
            stop_price=stop,
            atr20=float(atr[i]),
            momentum_atr=float(mom if side > 0 else -mom),
            s_hat_bps=float(panel.s_hat_bps[i]) if np.isfinite(panel.s_hat_bps[i]) else float("nan"),
            s_hat_decile=float(panel.s_hat_decile[i]) if np.isfinite(panel.s_hat_decile[i]) else float("nan"),
            s_hat_rank=float(panel.s_hat_rank[i]) if np.isfinite(panel.s_hat_rank[i]) else float("nan"),
            abs_r_decision_bps=(
                float(panel.abs_r_decision_bps[i])
                if np.isfinite(panel.abs_r_decision_bps[i]) else float("nan")
            ),
            abs_r_decile=(
                float(panel.abs_r_decile[i])
                if np.isfinite(panel.abs_r_decile[i]) else float("nan")
            ),
        ))
    return out


def resolve_signal_fills(
    signals: list[Signal],
    panel: SymbolPanel,
    *,
    inactive_hold_hours: float = L0_INACTIVE_HOLD_HOURS,
) -> list[Signal]:
    """Resolve each signal's entry stop on M1; mark filled / expired. No suppression yet."""
    inactive_ns = int(inactive_hold_hours * 3600 * NS)
    m1 = panel.m1
    for s in signals:
        ef = resolve_entry_stop(
            m1,
            side=s.side,
            stop_price=s.stop_price,
            decision_end_ns=s.decision_end_ns,
            inactive_hold_ns=inactive_ns,
        )
        s.filled = ef.filled
        s.fill_ts = ef.fill_ts
        s.fill_price = ef.fill_price
        s.fill_kind = ef.fill_kind
        s.fill_m1_idx = ef.m1_idx
        if not ef.filled:
            s.reason = "UNFILLED"
    return signals
