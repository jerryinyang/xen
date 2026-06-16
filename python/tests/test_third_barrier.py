"""Numeric anchors for the EXP-058 third-barrier geometry module.

These are the unit tests the EXP-058 adversarial review (finding F03) flagged as
missing: the sole new causal code is ``third_event_caps`` (the forward
rd-confirm locator + 8*bench_N backstop + warmup exclusion) and the
``variant_caps`` wrapper. Until the experiment runs, the only correctness
assurance for that code is the in-run integration invariants; these tests give
the locator an external, hand-derivable reference for the edge cases those
asserts may not exercise (strict-after lower bound, backstop binding,
event/backstop boundary, warmup exclusion, /THIRD-TIME monotonicity).

Each assertion is hand-derived from the inputs — no value is copied back from
the implementation.
"""
from __future__ import annotations

import numpy as np

from xen.third_barrier import (
    BENCH_FLOOR,
    THIRD_EVENT_BACKSTOP_MULT,
    THIRD_TIME_FLOORS,
    third_event_caps,
    variant_caps,
)


# --------------------------------------------------------------------------- #
# third_event_caps — causal forward rd-confirm locator
# --------------------------------------------------------------------------- #
def test_event_strict_after_lower_bound_skips_move_at_entry_epoch() -> None:
    """A move confirming exactly at the entry epoch must be skipped (side='right'),
    even when its direction equals rd — the exit must confirm strictly after entry."""
    entry_idx = np.array([10], dtype=np.int64)
    entry_epoch = np.array([1000], dtype=np.int64)
    # Moves at epochs 900, 1000, 1100; all rd-direction (+1). The 1000 move is AT
    # the entry epoch and must be excluded; the 1100 move (idx 25) is the exit.
    move_confirm_epoch = np.array([900, 1000, 1100], dtype=np.int64)
    move_confirm_idx = np.array([5, 15, 25], dtype=np.int64)
    move_direction = np.array([1, 1, 1], dtype=np.int64)
    rd = np.array([1], dtype=np.int64)
    bench_n = np.array([100], dtype=np.int64)           # backstop 800 — does not bind
    bench_warmup = np.array([False])

    out = third_event_caps(entry_idx, entry_epoch, move_confirm_epoch, move_confirm_idx,
                           move_direction, rd, bench_n, bench_warmup)

    assert out["avail"][0]
    assert out["event_bound"][0]
    assert out["n_event"][0] == 25 - 10                 # exit at the 1100 move, not 1000


def test_event_backstop_binds_when_no_rd_confirm() -> None:
    """No rd-direction move within the backstop horizon -> n_event = backstop,
    event_bound False."""
    entry_idx = np.array([10], dtype=np.int64)
    entry_epoch = np.array([1000], dtype=np.int64)
    move_confirm_epoch = np.array([900, 1100, 1200], dtype=np.int64)
    move_confirm_idx = np.array([5, 15, 25], dtype=np.int64)
    move_direction = np.array([1, -1, -1], dtype=np.int64)   # never +1 after entry
    rd = np.array([1], dtype=np.int64)
    bench_n = np.array([3], dtype=np.int64)
    bench_warmup = np.array([False])

    out = third_event_caps(entry_idx, entry_epoch, move_confirm_epoch, move_confirm_idx,
                           move_direction, rd, bench_n, bench_warmup)

    assert out["avail"][0]
    assert not out["event_bound"][0]
    assert out["n_event"][0] == THIRD_EVENT_BACKSTOP_MULT * 3   # = 24


def test_event_boundary_equal_backstop_counts_as_event_bound() -> None:
    """An rd-confirm landing exactly at the backstop bar is event-bound (<= backstop)."""
    entry_idx = np.array([10], dtype=np.int64)
    entry_epoch = np.array([1000], dtype=np.int64)
    bench_n = np.array([3], dtype=np.int64)             # backstop = 24 -> exit bar 34
    move_confirm_epoch = np.array([1100], dtype=np.int64)
    move_confirm_idx = np.array([34], dtype=np.int64)   # 34 - 10 == 24 == backstop
    move_direction = np.array([1], dtype=np.int64)
    rd = np.array([1], dtype=np.int64)
    bench_warmup = np.array([False])

    out = third_event_caps(entry_idx, entry_epoch, move_confirm_epoch, move_confirm_idx,
                           move_direction, rd, bench_n, bench_warmup)

    assert out["event_bound"][0]
    assert out["n_event"][0] == THIRD_EVENT_BACKSTOP_MULT * 3   # = 24


def test_event_warmup_excluded() -> None:
    """A benchmark-warmup entry has no defined backstop -> avail False, n_event 0."""
    entry_idx = np.array([10], dtype=np.int64)
    entry_epoch = np.array([1000], dtype=np.int64)
    move_confirm_epoch = np.array([1100], dtype=np.int64)
    move_confirm_idx = np.array([15], dtype=np.int64)
    move_direction = np.array([1], dtype=np.int64)
    rd = np.array([1], dtype=np.int64)
    bench_n = np.array([0], dtype=np.int64)
    bench_warmup = np.array([True])

    out = third_event_caps(entry_idx, entry_epoch, move_confirm_epoch, move_confirm_idx,
                           move_direction, rd, bench_n, bench_warmup)

    assert not out["avail"][0]
    assert out["n_event"][0] == 0
    assert not out["event_bound"][0]


def test_event_n_event_at_least_one_for_available_entries() -> None:
    """Available (non-warmup) entries always get n_event >= 1 (no degenerate window)."""
    entry_idx = np.array([10, 10], dtype=np.int64)
    entry_epoch = np.array([1000, 1000], dtype=np.int64)
    move_confirm_epoch = np.array([900, 1100], dtype=np.int64)
    move_confirm_idx = np.array([5, 12], dtype=np.int64)
    move_direction = np.array([-1, 1], dtype=np.int64)
    rd = np.array([1, -1], dtype=np.int64)              # one event-bound, one backstop
    bench_n = np.array([6, 6], dtype=np.int64)
    bench_warmup = np.array([False, False])

    out = third_event_caps(entry_idx, entry_epoch, move_confirm_epoch, move_confirm_idx,
                           move_direction, rd, bench_n, bench_warmup)

    assert np.all(out["n_event"][out["avail"]] >= 1)
    assert out["event_bound"][0] and out["n_event"][0] == 12 - 10    # rd=+1 -> the 1100 move
    assert not out["event_bound"][1]                                 # rd=-1 -> backstop


def test_event_empty_input() -> None:
    """Empty entry set returns empty arrays without error."""
    empty_i = np.empty(0, dtype=np.int64)
    out = third_event_caps(empty_i, empty_i, np.array([100], dtype=np.int64),
                           np.array([1], dtype=np.int64), np.array([1], dtype=np.int64),
                           empty_i, empty_i, np.empty(0, dtype=bool))
    assert out["n_event"].shape[0] == 0
    assert out["avail"].shape[0] == 0
    assert out["event_bound"].shape[0] == 0


# --------------------------------------------------------------------------- #
# variant_caps — /THIRD-TIME floor lever (monotone) + /THIRD-EVENT delegation
# --------------------------------------------------------------------------- #
def _monotone_fixture() -> dict[str, np.ndarray]:
    """10 evenly spaced confirmed moves (duration 2 bars each) + a late entry.

    median duration = 2 -> round(1.5*2) = 3, so the cap is floor-bound for every
    /THIRD-TIME floor in {6, 12, 24, 48}: n_event == max(floor, 3) == floor.
    """
    n_moves = 10
    move_confirm_idx = np.arange(0, 2 * n_moves, 2, dtype=np.int64)        # 0,2,...,18
    move_confirm_epoch = np.arange(10, 10 * (n_moves + 1), 10, dtype=np.int64)[:n_moves]
    move_direction = np.where(np.arange(n_moves) % 2 == 0, 1, -1).astype(np.int64)
    entry_epoch = np.array([10_000], dtype=np.int64)     # after every move
    entry_idx = np.array([40], dtype=np.int64)
    rd = np.array([1], dtype=np.int64)
    return {"entry_idx": entry_idx, "entry_epoch": entry_epoch,
            "move_confirm_epoch": move_confirm_epoch, "move_confirm_idx": move_confirm_idx,
            "move_direction": move_direction, "rd": rd}


def test_third_time_caps_floor_bound_and_monotone() -> None:
    fx = _monotone_fixture()
    caps = variant_caps(fx["entry_idx"], fx["entry_epoch"], fx["move_confirm_epoch"],
                        fx["move_confirm_idx"], fx["move_direction"], fx["rd"],
                        list(THIRD_TIME_FLOORS.keys()))
    bench = caps["BENCH"]["n_event"][0]
    assert bench == max(BENCH_FLOOR, 3) == 6
    # cap is floor-bound (median term 3 < every floor): n_event == floor.
    assert caps["BENCH"]["n_event"][0] == 6
    assert caps["THIRD-TIME-T12"]["n_event"][0] == 12
    assert caps["THIRD-TIME-T24"]["n_event"][0] == 24
    assert caps["THIRD-TIME-T48"]["n_event"][0] == 48
    # monotone non-decreasing in floor, event-wise.
    seq = [caps[v]["n_event"][0] for v in
           ("BENCH", "THIRD-TIME-T12", "THIRD-TIME-T24", "THIRD-TIME-T48")]
    assert seq == sorted(seq)


def test_variant_caps_time_variants_share_warmup_mask() -> None:
    """Availability (~warmup) is floor-independent: identical across BENCH/T12/T24/T48."""
    fx = _monotone_fixture()
    caps = variant_caps(fx["entry_idx"], fx["entry_epoch"], fx["move_confirm_epoch"],
                        fx["move_confirm_idx"], fx["move_direction"], fx["rd"],
                        list(THIRD_TIME_FLOORS.keys()))
    bench_avail = caps["BENCH"]["avail"]
    for v in ("THIRD-TIME-T12", "THIRD-TIME-T24", "THIRD-TIME-T48"):
        assert np.array_equal(caps[v]["avail"], bench_avail)
        assert not caps[v]["event_bound"].any()         # not applicable to time variants


def test_variant_caps_event_uses_bench_backstop() -> None:
    """/THIRD-EVENT through the wrapper uses the BENCH cap as its backstop base."""
    fx = _monotone_fixture()
    caps = variant_caps(fx["entry_idx"], fx["entry_epoch"], fx["move_confirm_epoch"],
                        fx["move_confirm_idx"], fx["move_direction"], fx["rd"],
                        ["BENCH", "THIRD-EVENT"])
    bench_n = caps["BENCH"]["n_event"][0]
    evt = caps["THIRD-EVENT"]
    # no rd=+1 move confirms after entry (entry is past every move) -> backstop binds.
    assert evt["avail"][0]
    assert not evt["event_bound"][0]
    assert evt["n_event"][0] == THIRD_EVENT_BACKSTOP_MULT * bench_n


def test_variant_caps_unknown_variant_raises() -> None:
    fx = _monotone_fixture()
    try:
        variant_caps(fx["entry_idx"], fx["entry_epoch"], fx["move_confirm_epoch"],
                     fx["move_confirm_idx"], fx["move_direction"], fx["rd"], ["NOPE"])
    except ValueError as exc:
        assert "unknown variant id" in str(exc)
    else:                                                # pragma: no cover
        raise AssertionError("expected ValueError for unknown variant id")
