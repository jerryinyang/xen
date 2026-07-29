"""M1 fill resolution — entry stops, targets, trails, time exits (design §2).

Adverse-precedence rule: if target and trail/stop are both reachable in the same M1 bar,
the adverse one fills (trail/stop). Never assume favourable ordering.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from config import NS

# exit reasons
EXIT_TIME = "TIME"
EXIT_TARGET = "TARGET"
EXIT_TRAIL = "TRAIL"
EXIT_NONE = "NONE"
FILL_STOP = "STOP"
FILL_GAP = "GAP"
FILL_EXPIRED = "EXPIRED"


@dataclass(frozen=True)
class EntryFill:
    filled: bool
    fill_ts: int
    fill_price: float
    fill_kind: str  # STOP | GAP | EXPIRED
    m1_idx: int  # index of fill M1 bar, or -1


@dataclass(frozen=True)
class ExitFill:
    exit_ts: int
    exit_price: float
    reason: str
    m1_idx: int


def _first_m1_after(ts: np.ndarray, after_ns: int) -> int:
    """Index of first M1 bar with ts > after_ns (decision bar close → fill after)."""
    return int(np.searchsorted(ts, after_ns, side="right"))


def resolve_entry_stop(
    m1: dict[str, np.ndarray],
    *,
    side: int,
    stop_price: float,
    decision_end_ns: int,
    inactive_hold_ns: int,
) -> EntryFill:
    """Resolve buy-stop (LONG) / sell-stop (SHORT) on M1 (design §2).

    LONG: first M1 with high >= stop → fill at stop; if open > stop → gap fill at open.
    SHORT: first M1 with low <= stop → fill at stop; if open < stop → gap fill at open.
    Window: M1 ts strictly after decision_end, up to decision_end + inactive_hold.
    """
    ts = m1["ts"]
    o, h, lo = m1["open"], m1["high"], m1["low"]
    lo_i = _first_m1_after(ts, decision_end_ns)
    if lo_i >= ts.size:
        return EntryFill(False, -1, float("nan"), FILL_EXPIRED, -1)
    hi_deadline = decision_end_ns + inactive_hold_ns
    # last bar with ts <= deadline
    hi_i = int(np.searchsorted(ts, hi_deadline, side="right")) - 1
    if hi_i < lo_i:
        return EntryFill(False, -1, float("nan"), FILL_EXPIRED, -1)

    if side > 0:  # LONG buy stop
        for i in range(lo_i, hi_i + 1):
            if h[i] >= stop_price:
                if o[i] > stop_price:
                    return EntryFill(True, int(ts[i]), float(o[i]), FILL_GAP, i)
                return EntryFill(True, int(ts[i]), float(stop_price), FILL_STOP, i)
    else:  # SHORT sell stop
        for i in range(lo_i, hi_i + 1):
            if lo[i] <= stop_price:
                if o[i] < stop_price:
                    return EntryFill(True, int(ts[i]), float(o[i]), FILL_GAP, i)
                return EntryFill(True, int(ts[i]), float(stop_price), FILL_STOP, i)
    return EntryFill(False, -1, float("nan"), FILL_EXPIRED, -1)


def resolve_entry_stop_on_clock(
    clock: dict[str, np.ndarray],
    *,
    side: int,
    stop_price: float,
    decision_end_ns: int,
    inactive_hold_ns: int,
) -> EntryFill:
    """TRIPWIRE-2(a) twin: identical stop rule resolved on the DECISION-CLOCK bar OHLC.

    Same window and same fill convention as :func:`resolve_entry_stop`, but the price stream
    is the decision clock rather than M1. Never used by the research emission — its only
    purpose is to produce the differing-fill ids §6.1 requires.
    """
    ts = clock["slot_end"]
    o, h, lo = clock["open"], clock["high"], clock["low"]
    lo_i = _first_m1_after(ts, decision_end_ns)
    if lo_i >= ts.size:
        return EntryFill(False, -1, float("nan"), FILL_EXPIRED, -1)
    hi_i = int(np.searchsorted(ts, decision_end_ns + inactive_hold_ns, side="right")) - 1
    if hi_i < lo_i:
        return EntryFill(False, -1, float("nan"), FILL_EXPIRED, -1)
    if side > 0:
        for i in range(lo_i, hi_i + 1):
            if h[i] >= stop_price:
                if o[i] > stop_price:
                    return EntryFill(True, int(ts[i]), float(o[i]), FILL_GAP, i)
                return EntryFill(True, int(ts[i]), float(stop_price), FILL_STOP, i)
    else:
        for i in range(lo_i, hi_i + 1):
            if lo[i] <= stop_price:
                if o[i] < stop_price:
                    return EntryFill(True, int(ts[i]), float(o[i]), FILL_GAP, i)
                return EntryFill(True, int(ts[i]), float(stop_price), FILL_STOP, i)
    return EntryFill(False, -1, float("nan"), FILL_EXPIRED, -1)


def resolve_time_exit(
    clock_open: np.ndarray,
    clock_slot_start: np.ndarray,
    *,
    fill_ts: int,
    active_hold_ns: int,
) -> ExitFill | None:
    """Time exit at open of first decision-clock bar at or after fill_ts + active_hold.

    open-to-open exit matching the entry convention (design §2).
    """
    deadline = fill_ts + active_hold_ns
    # first bar whose open (slot_start) >= deadline
    i = int(np.searchsorted(clock_slot_start, deadline, side="left"))
    if i >= clock_slot_start.size:
        return None
    return ExitFill(
        exit_ts=int(clock_slot_start[i]),
        exit_price=float(clock_open[i]),
        reason=EXIT_TIME,
        m1_idx=-1,
    )


def resolve_target_trail_time(
    m1: dict[str, np.ndarray],
    clock_open: np.ndarray,
    clock_slot_start: np.ndarray,
    *,
    side: int,
    entry_price: float,
    fill_ts: int,
    fill_m1_idx: int,
    active_hold_ns: int,
    target_price: float | None,
    trail_width_price: float | None,
    favourable_precedence: bool = False,
) -> ExitFill | None:
    """Resolve L4 exits on M1 with adverse precedence (design §2).

    - Target: first M1 through target → at target; gap → at open.
    - Trail: ratchets once per M1 close; triggers on first M1 through trail level.
    - Time: open of first decision bar at/after active_hold.
    - Same M1 bar, both target and trail reachable at DISTINCT prices → trail/stop wins.
    - Target/trail at or before time-exit bar open take precedence over time.

    ``favourable_precedence`` inverts ONLY the both-reachable branch (target wins). It is the
    TRIPWIRE-2(b) twin (§6.1) and is never used by the research emission.
    """
    has_target = target_price is not None and np.isfinite(target_price)
    has_trail = trail_width_price is not None and trail_width_price > 0
    if not has_target and not has_trail:
        # pure time exit: no side-dependent branch is reachable, so scanning M1 is both
        # wasted work and misleading about what decides the exit
        return resolve_time_exit(
            clock_open, clock_slot_start, fill_ts=fill_ts, active_hold_ns=active_hold_ns
        )

    ts = m1["ts"]
    o, h, lo, c = m1["open"], m1["high"], m1["low"], m1["close"]
    n = ts.size
    start = max(fill_m1_idx + 1, _first_m1_after(ts, fill_ts))
    if start >= n:
        return None

    time_ex = resolve_time_exit(
        clock_open, clock_slot_start, fill_ts=fill_ts, active_hold_ns=active_hold_ns
    )
    time_ts = time_ex.exit_ts if time_ex is not None else None

    # trail state: extreme since entry (close-based ratchet)
    if trail_width_price is not None and trail_width_price > 0:
        if side > 0:
            extreme = entry_price  # highest close
            trail_level = entry_price - trail_width_price
        else:
            extreme = entry_price  # lowest close
            trail_level = entry_price + trail_width_price
    else:
        extreme = float("nan")
        trail_level = float("nan")

    end_i = n
    if time_ts is not None:
        # §2: a barrier triggering AT OR BEFORE the time-exit bar's open takes precedence.
        # m1["ts"] is the M1 bar CLOSE, so the bar covering [time_ts-60s, time_ts] must be
        # scanned; side="right" includes it. side="left" dropped it (a one-minute bias
        # toward the time exit on every target/trail arm).
        end_i = int(np.searchsorted(ts, time_ts, side="right"))

    for i in range(start, end_i):
        tgt_hit = False
        trail_hit = False
        tgt_px = float("nan")
        trail_px = float("nan")

        if target_price is not None and np.isfinite(target_price):
            if side > 0 and h[i] >= target_price:
                tgt_hit = True
                tgt_px = float(o[i]) if o[i] > target_price else float(target_price)
            elif side < 0 and lo[i] <= target_price:
                tgt_hit = True
                tgt_px = float(o[i]) if o[i] < target_price else float(target_price)

        if trail_width_price is not None and np.isfinite(trail_level):
            if side > 0 and lo[i] <= trail_level:
                trail_hit = True
                trail_px = float(o[i]) if o[i] < trail_level else float(trail_level)
            elif side < 0 and h[i] >= trail_level:
                trail_hit = True
                trail_px = float(o[i]) if o[i] > trail_level else float(trail_level)

        if tgt_hit and trail_hit:
            # adverse precedence when levels are DISTINCT
            if abs(tgt_px - trail_px) > 1e-12 * max(1.0, abs(entry_price)):
                if favourable_precedence:
                    return ExitFill(int(ts[i]), tgt_px, EXIT_TARGET, i)
                return ExitFill(int(ts[i]), trail_px, EXIT_TRAIL, i)
            # price-identical: either is fine; take trail as design's adverse default
            return ExitFill(int(ts[i]), trail_px, EXIT_TRAIL, i)
        if trail_hit:
            return ExitFill(int(ts[i]), trail_px, EXIT_TRAIL, i)
        if tgt_hit:
            return ExitFill(int(ts[i]), tgt_px, EXIT_TARGET, i)

        # ratchet trail on this M1 close (after checking triggers on this bar)
        if trail_width_price is not None and trail_width_price > 0:
            if side > 0:
                if c[i] > extreme:
                    extreme = float(c[i])
                    trail_level = extreme - trail_width_price
            else:
                if c[i] < extreme:
                    extreme = float(c[i])
                    trail_level = extreme + trail_width_price

    if time_ex is not None:
        return time_ex
    return None


def mfe_bps(
    m1: dict[str, np.ndarray],
    *,
    side: int,
    entry_price: float,
    fill_m1_idx: int,
    exit_ts: int,
) -> float:
    """Maximum favourable excursion over ``[fill bar, exit]`` in bps (κ's denominator, §5).

    Vectorised over the M1 slice: no per-bar Python loop, so it costs the same on the
    time-exit arms as on the barrier arms.
    """
    ts = m1["ts"]
    if fill_m1_idx < 0 or ts.size == 0 or not (entry_price > 0):
        return float("nan")
    end_i = int(np.searchsorted(ts, exit_ts, side="right"))
    if end_i <= fill_m1_idx:
        return float("nan")
    if side > 0:
        best = float(np.max(m1["high"][fill_m1_idx:end_i]))
    else:
        best = float(np.min(m1["low"][fill_m1_idx:end_i]))
    if not np.isfinite(best):
        return float("nan")
    return float(side * (best / entry_price - 1.0) * 1e4)


def signed_r_bps(side: int, entry: float, exit_: float) -> float:
    """Signed gross return in bps from entry fill to exit fill."""
    if not (np.isfinite(entry) and np.isfinite(exit_) and entry > 0):
        return float("nan")
    return float(side * (exit_ / entry - 1.0) * 1e4)


def bps_to_price_width(entry_price: float, width_bps: float) -> float:
    """Convert a width stated in bps of price into absolute price units."""
    return float(entry_price * width_bps / 1e4)


def both_reachable_in_bar(
    *,
    side: int,
    high: float,
    low: float,
    target_price: float,
    trail_level: float,
) -> bool:
    """Whether target and trail are both reachable in one M1 OHLC bar."""
    if side > 0:
        return (high >= target_price) and (low <= trail_level)
    return (low <= target_price) and (high >= trail_level)
