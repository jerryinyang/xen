"""Hand-derived ground-truth anchors for the EXP-059B uncapped trailing resolver.

These are the unit tests the EXP-059B adversarial review (finding F07) flagged as
missing: the in-run ``lazy_dense_prefix_ok`` invariant only validates the lazy
uncapped stop against the dense capped builder on the shared
``[entry+1, entry+bench_n]`` prefix — the **uncapped region** (offset > bench_n),
which is the entire object under test, had no external oracle. Each scenario below
fixes a tiny synthetic OHLC series plus secondary-ZigZag pivots and asserts the
exit price / class / resolving offset that a person can derive by hand, with at
least one fill at an offset **past the 6-bar benchmark cap**.

Every expected value is hand-derived from the inputs — none is copied back from the
implementation. Long fade convention used throughout (``rd = +1``): the favourable
side is the High, the trailing stop sits below price and ratchets up toward
confirmed secondary pivot lows, and an exit fires when the Low reaches the stop.
"""
from __future__ import annotations

import numpy as np

from xen.position_exits import (
    ADV_TRAIL,
    LEG_LEVEL,
    LEG_NONE,
    PX_DATA_CENSORED,
    PX_FAV,
    PX_TIMECAP,
    PX_TRAIL,
    build_active_stops,
    resolve_legs,
    resolve_legs_uncapped,
)

F = np.float64


def _ohlc(rows: list[tuple[float, float, float, float]]) -> dict[str, np.ndarray]:
    """Build (open, high, low, close) float64 arrays from per-bar tuples."""
    arr = np.array(rows, dtype=F)
    return {"o": arr[:, 0].copy(), "h": arr[:, 1].copy(),
            "lo": arr[:, 2].copy(), "c": arr[:, 3].copy()}


# --------------------------------------------------------------------------- #
# Scenario 1 — trailing fill in the UNCAPPED region (offset 11 > bench_n=6)
# --------------------------------------------------------------------------- #
def test_uncapped_trail_fills_past_cap() -> None:
    # Secondary pivots: a down-move to 100 (confirm@2), an up-move to 110
    # (confirm@4) -> stop ratchets to the prior pivot low 100 from bar 4; then a
    # down-move to 104 (confirm@7) and an up-move to 115 (confirm@9) -> stop
    # ratchets up to 104 from bar 9. Hand-derived stop: NaN(1-3), 100(4-8), 104(9+).
    sci = np.array([2, 4, 7, 9], dtype=np.int64)
    sdir = np.array([-1, 1, -1, 1], dtype=np.int64)
    sep = np.array([100.0, 110.0, 104.0, 115.0], dtype=F)
    rows = [(108, 112, 106, 110)] * 15           # base: low 106 clears both stops
    rows[11] = (108, 106, 103, 104)              # bearish dip: low 103 <= stop 104
    d = _ohlc(rows)
    ei = np.array([0], dtype=np.int64)
    ec = np.array([105.0], dtype=F)
    rd = np.array([1], dtype=np.int64)
    levels = np.full((1, 1), np.nan, dtype=F)    # LEG_NONE: pure trailing
    no_rev = np.array([-1], dtype=np.int64)
    pop = np.array([True])
    px, cls, off = resolve_legs_uncapped(
        d["o"], d["h"], d["lo"], d["c"], ei, ec, rd, (LEG_NONE,), levels, no_rev,
        sci, sdir, sep, pop, last_train_idx=14)
    assert cls[0, 0] == PX_TRAIL
    assert px[0, 0] == 104.0                      # filled at the ratcheted stop
    assert off[0] == 11                           # past the 6-bar benchmark cap
    assert not (cls == PX_TIMECAP).any()          # uncapped emits no TIMECAP


# --------------------------------------------------------------------------- #
# Scenario 2 — never hit -> DATA_CENSORED at the TRAIN edge (no TIMECAP)
# --------------------------------------------------------------------------- #
def test_uncapped_censored_at_train_edge() -> None:
    sci = np.array([2, 4], dtype=np.int64)
    sdir = np.array([-1, 1], dtype=np.int64)
    sep = np.array([100.0, 110.0], dtype=F)       # stop = 100 from bar 4 onward
    d = _ohlc([(108, 112, 106, 110)] * 15)        # low 106 > 100 forever: no fill
    ei = np.array([0], dtype=np.int64)
    ec = np.array([105.0], dtype=F)
    rd = np.array([1], dtype=np.int64)
    levels = np.full((1, 1), np.nan, dtype=F)
    no_rev = np.array([-1], dtype=np.int64)
    pop = np.array([True])
    px, cls, off = resolve_legs_uncapped(
        d["o"], d["h"], d["lo"], d["c"], ei, ec, rd, (LEG_NONE,), levels, no_rev,
        sci, sdir, sep, pop, last_train_idx=14)
    assert cls[0, 0] == PX_DATA_CENSORED
    assert not np.isfinite(px[0, 0])
    assert off[0] == 14                           # held to last_train_idx
    assert not (cls == PX_TIMECAP).any()


# --------------------------------------------------------------------------- #
# Scenario 3 — the shared trailing stop binds every still-open V2A leg at one
# bar/level (offset 8 > cap), after a partial favourable leg already closed
# --------------------------------------------------------------------------- #
def test_uncapped_shared_stop_binds_open_legs() -> None:
    sci = np.array([2, 3], dtype=np.int64)
    sdir = np.array([-1, 1], dtype=np.int64)
    sep = np.array([100.0, 120.0], dtype=F)       # stop = 100 from bar 3 onward
    rows = [(108, 108, 106, 108)] * 15
    rows[5] = (108, 110, 106, 110)                # high 110 hits leg0 @109 only
    rows[8] = (108, 108, 99, 99)                  # low 99 <= stop 100: binds rest
    d = _ohlc(rows)
    ei = np.array([0], dtype=np.int64)
    ec = np.array([105.0], dtype=F)
    rd = np.array([1], dtype=np.int64)
    levels = np.array([[109.0, 111.0, 113.0]], dtype=F)  # V2A-style level legs
    no_rev = np.array([-1], dtype=np.int64)
    pop = np.array([True])
    px, cls, off = resolve_legs_uncapped(
        d["o"], d["h"], d["lo"], d["c"], ei, ec, rd, (LEG_LEVEL, LEG_LEVEL, LEG_LEVEL),
        levels, no_rev, sci, sdir, sep, pop, last_train_idx=14)
    assert list(cls[0]) == [PX_FAV, PX_TRAIL, PX_TRAIL]
    assert px[0, 0] == 109.0                       # partial favourable leg
    assert px[0, 1] == 100.0 and px[0, 2] == 100.0  # both bound at the same level
    assert off[0] == 8                             # the bind bar, past the cap


# --------------------------------------------------------------------------- #
# Scenario 4 — lazy uncapped stop == dense capped (no-init) resolver on a fill
# that lands inside the shared prefix (offset 3 <= bench_n=6)
# --------------------------------------------------------------------------- #
def test_uncapped_matches_capped_on_shared_prefix() -> None:
    sci = np.array([1, 2], dtype=np.int64)
    sdir = np.array([-1, 1], dtype=np.int64)
    sep = np.array([100.0, 110.0], dtype=F)        # stop = 100 from bar 2 onward
    rows = [(108, 108, 106, 108)] * 11
    rows[3] = (108, 108, 99, 99)                   # low 99 <= stop 100: fill @ off 3
    d = _ohlc(rows)
    ei = np.array([0], dtype=np.int64)
    ec = np.array([105.0], dtype=F)
    rd = np.array([1], dtype=np.int64)
    levels = np.full((1, 1), np.nan, dtype=F)
    no_rev = np.array([-1], dtype=np.int64)
    pop = np.array([True])
    adv = np.array([0.0], dtype=F)                 # unused under ADV_TRAIL + no init
    bench_n = np.array([6], dtype=np.int64)
    ltrain = 10

    # Dense capped (no-init) path, exactly as the EXP-059B capped siblings run it.
    active = build_active_stops(ei, rd, adv, True, sci, sdir, sep, bench_n, ltrain)
    cap_off = np.full(1, -1, dtype=np.int64)
    cap_px, cap_cls = resolve_legs(
        d["o"], d["h"], d["lo"], d["c"], ei, ec, rd, (LEG_NONE,), levels, no_rev,
        adv, bench_n, pop, ADV_TRAIL, active, ltrain, cap_off)

    # Lazy uncapped path.
    unc_px, unc_cls, unc_off = resolve_legs_uncapped(
        d["o"], d["h"], d["lo"], d["c"], ei, ec, rd, (LEG_NONE,), levels, no_rev,
        sci, sdir, sep, pop, ltrain)

    assert active[0, 2] == 100.0                    # dense stop level (hand-derived)
    assert cap_cls[0, 0] == PX_TRAIL and unc_cls[0, 0] == PX_TRAIL
    assert cap_px[0, 0] == 100.0 and unc_px[0, 0] == 100.0
    assert cap_off[0] == 3 and unc_off[0] == 3      # identical resolving offset


# --------------------------------------------------------------------------- #
# Scenario 5 — F04 additive offsets do not change the capped resolver's
# returned px/cls (frozen behaviour preserved whether or not exit_off is passed)
# --------------------------------------------------------------------------- #
def test_capped_exit_off_is_additive() -> None:
    sci = np.array([1, 2], dtype=np.int64)
    sdir = np.array([-1, 1], dtype=np.int64)
    sep = np.array([100.0, 110.0], dtype=F)
    rows = [(108, 108, 106, 108)] * 11
    rows[3] = (108, 108, 99, 99)
    d = _ohlc(rows)
    ei = np.array([0], dtype=np.int64)
    ec = np.array([105.0], dtype=F)
    rd = np.array([1], dtype=np.int64)
    levels = np.full((1, 1), np.nan, dtype=F)
    no_rev = np.array([-1], dtype=np.int64)
    adv = np.array([0.0], dtype=F)
    bench_n = np.array([6], dtype=np.int64)
    ltrain = 10
    active = build_active_stops(ei, rd, adv, True, sci, sdir, sep, bench_n, ltrain)

    base_px, base_cls = resolve_legs(
        d["o"], d["h"], d["lo"], d["c"], ei, ec, rd, (LEG_NONE,), levels, no_rev,
        adv, bench_n, np.array([True]), ADV_TRAIL, active, ltrain)        # no exit_off
    off = np.full(1, -1, dtype=np.int64)
    px2, cls2 = resolve_legs(
        d["o"], d["h"], d["lo"], d["c"], ei, ec, rd, (LEG_NONE,), levels, no_rev,
        adv, bench_n, np.array([True]), ADV_TRAIL, active, ltrain, off)   # with exit_off

    assert np.array_equal(base_px, px2, equal_nan=True)
    assert np.array_equal(base_cls, cls2)
    assert off[0] == 3                               # offset captured additively
