"""Per-position financing/swap cost overlay (Phase 008 cost layer).

Financing is charged once per realized position as

    financing_bps = rate_bps_per_day * elapsed_calendar_days(entry, exit)

with *fractional* calendar days from real bar timestamps. Calendar time includes
weekends and market closures — deliberately: it is both more accurate than a
bar-count approximation and conservative (a position held over a weekend pays the
weekend). The rate is the adverse-side daily swap magnitude, applied regardless of
direction (a conservative bound; triple-swap days are averaged into the rate).

Rates themselves are experiment constants (predeclared in the owning scope and
frozen at scope approval); this module is the pure mechanics only.
"""
from __future__ import annotations

import numpy as np

NS_PER_DAY: int = 86_400 * 1_000_000_000


def elapsed_calendar_days(entry_time: np.ndarray, exit_time: np.ndarray) -> np.ndarray:
    """Fractional calendar days between two datetime arrays (vectorized).

    Parameters
    ----------
    entry_time, exit_time:
        Arrays coercible to ``datetime64[ns]``, element-aligned. ``exit_time`` must
        be >= ``entry_time`` element-wise (a negative holding period is a wiring
        bug, not a market outcome).

    Returns
    -------
    np.ndarray
        Float days (fractional), same shape as the inputs.
    """
    entry_ns = np.asarray(entry_time, dtype="datetime64[ns]").astype(np.int64)
    exit_ns = np.asarray(exit_time, dtype="datetime64[ns]").astype(np.int64)
    days = (exit_ns - entry_ns) / NS_PER_DAY
    if np.any(days < 0):
        bad = int(np.sum(days < 0))
        raise ValueError(f"negative holding period in {bad} row(s): exit_time < entry_time")
    return days


def financing_bps_from_days(
    rate_bps_per_day: np.ndarray | float,
    holding_days: np.ndarray | float,
) -> np.ndarray:
    """Adverse-side financing charge in bps from precomputed fractional days.

    This is the single multiplication every experiment's net computation must route
    through (so the self-check covers the live path). Durations should come from
    :func:`elapsed_calendar_days`.

    Parameters
    ----------
    rate_bps_per_day:
        Scalar or per-row array of adverse-side daily swap magnitudes (bps/day,
        non-negative).
    holding_days:
        Fractional calendar days held (non-negative).

    Returns
    -------
    np.ndarray
        ``rate * holding_days`` per position, in bps.
    """
    rate = np.asarray(rate_bps_per_day, dtype=float)
    days = np.asarray(holding_days, dtype=float)
    if np.any(rate < 0):
        raise ValueError("financing rate must be non-negative (adverse-side magnitude)")
    if np.any(days < 0):
        raise ValueError("holding_days must be non-negative")
    return rate * days


def financing_bps(
    rate_bps_per_day: np.ndarray | float,
    entry_time: np.ndarray,
    exit_time: np.ndarray,
) -> np.ndarray:
    """Adverse-side financing charge in bps for each position (vectorized).

    Parameters
    ----------
    rate_bps_per_day:
        Scalar or per-row array of adverse-side daily swap magnitudes (bps/day,
        non-negative).
    entry_time, exit_time:
        Position entry/exit timestamps (coercible to ``datetime64[ns]``).

    Returns
    -------
    np.ndarray
        ``rate * fractional_calendar_days`` per position, in bps.
    """
    return financing_bps_from_days(
        rate_bps_per_day, elapsed_calendar_days(entry_time, exit_time))


def verify_financing() -> bool:
    """Hand-computed financing cases; raises on any mismatch (run-time self-check).

    Cases: exact single day; weekend-spanning Fri->Mon hold (3 calendar days —
    the property a bar-count approximation gets wrong); intraday fraction; zero
    duration; and the negative-duration guard.

    Returns
    -------
    bool
        ``True`` if every case matches its hand-computed expectation.
    """
    cases = [
        # (rate, entry, exit, expected_bps)
        (1.0, "2026-06-01T00:00:00", "2026-06-02T00:00:00", 1.0),
        (0.6, "2026-06-05T12:00:00", "2026-06-08T12:00:00", 1.8),   # Fri -> Mon
        (10.0, "2026-06-01T00:00:00", "2026-06-01T06:00:00", 2.5),  # 0.25 day
        (1.2, "2026-06-01T08:00:00", "2026-06-01T08:00:00", 0.0),   # zero hold
    ]
    entry = np.array([c[1] for c in cases], dtype="datetime64[ns]")
    exit_ = np.array([c[2] for c in cases], dtype="datetime64[ns]")
    rates = np.array([c[0] for c in cases], dtype=float)
    expected = np.array([c[3] for c in cases], dtype=float)
    got = financing_bps(rates, entry, exit_)
    if not np.allclose(got, expected, rtol=0, atol=1e-12):
        raise ValueError(f"financing self-check FAILED: got {got.tolist()}, "
                         f"expected {expected.tolist()}")
    try:
        financing_bps(1.0, np.array(["2026-06-02T00:00:00"], dtype="datetime64[ns]"),
                      np.array(["2026-06-01T00:00:00"], dtype="datetime64[ns]"))
    except ValueError:
        return True
    raise ValueError("financing self-check FAILED: negative duration not rejected")
