"""Causal pivot-tiling assignment of events to confirmed moves + position-in-move.

Reusable across Phase 014 (EXP-050 harami-in-context; reused by 014-B combined
events). A *move segmentation* is any non-overlapping, time-ordered set of
confirmed moves, each carrying a ``StartTime``/``EndTime`` interval and
``StartPrice``/``EndPrice``/``Direction``. Examples: the ``xen.zigzag``
confirmed-move sequence (half-open pivot tiling) and an MA-crossover regime
segmentation (closed intervals with flat gaps).

Given event timestamps and the *real* signal price at each event, this module
assigns each event to the unique containing move under pivot tiling and computes
the price-excursion position::

    pos = (P - StartPrice) / (EndPrice - StartPrice)

The denominator carries the move's sign, so ``pos`` is direction-signed for up-
and down-moves alike; ``pos >= 0.67`` is the P9 "near exhaustion" (final third).

**Descriptive-allowance note (binding).** The assignment is a deterministic
geometric grouping over a *precomputed completed segmentation*; it is not a live
signal. ``pos`` references the move's terminal pivot ``EndPrice``, which is future
information relative to a mid-move event, so it is valid only as a *non-tradable*
descriptive characterization of **completed** moves -- no trading, signal,
capture, or P&L decision may consume ``pos`` or an unconfirmed pivot. The
genuinely sequential causal logic (the ZigZag state machine, the one-row-shift HA
harami detector, the MA crossover) lives in the upstream frozen generators, not
here; the interval-join below only groups already-confirmed moves.
"""
from __future__ import annotations

import numpy as np
import polars as pl


# Exclusion classes (an event has no defined position).
ASSIGNED = "assigned"
BEFORE_FIRST = "before_first"   # left-bound guard fail (ZigZag warmup / pre-regime)
AFTER_LAST = "after_last"       # no forward move (forming tail / post-regime)
DEGENERATE = "degenerate"       # containing move has EndPrice == StartPrice

POSITION_THRESHOLD = 0.67       # P9 "near exhaustion" (final third)

_MOVE_COLUMNS = ("StartTime", "EndTime", "StartPrice", "EndPrice", "Direction")


def assign_to_moves(
    events: pl.DataFrame,
    moves: pl.DataFrame,
    *,
    event_time: str = "EventTime",
    event_price: str = "EventPrice",
    left_strict: bool = True,
    threshold: float = POSITION_THRESHOLD,
) -> pl.DataFrame:
    """Assign each event to its unique containing confirmed move (pivot tiling).

    Parameters
    ----------
    events : pl.DataFrame
        Must contain ``event_time`` (sorted non-decreasing) and ``event_price``.
        Row order is preserved (the caller may rely on a positional bar index).
    moves : pl.DataFrame
        Must contain ``StartTime, EndTime, StartPrice, EndPrice, Direction`` with
        non-overlapping, time-ordered intervals. An empty frame assigns every
        event to ``AFTER_LAST``.
    event_time, event_price : str
        Column names of the event timestamp and the (real) signal price.
    left_strict : bool, default True
        ``True`` -> half-open ``(StartTime, EndTime]`` (ZigZag pivot tiling);
        ``False`` -> closed ``[StartTime, EndTime]`` (MA-crossover regimes).
    threshold : float, default 0.67
        Final-third threshold for the ``final_third`` flag.

    Returns
    -------
    pl.DataFrame
        ``events`` (original columns, original order) plus ``move_dir``,
        ``move_start_price``, ``move_end_price``, ``move_start_time``,
        ``move_end_time``, ``pos`` (Float64; null unless ``ASSIGNED``),
        ``final_third`` (Boolean; null unless ``ASSIGNED``) and ``exclusion``.

    The containing move of an event at time ``t`` is the move with the smallest
    ``EndTime >= t`` (forward as-of), subject to the left bound ``StartTime < t``
    (``left_strict``) or ``StartTime <= t``. Forward as-of is exact under
    non-overlapping intervals and resolves the boundary case ``t == EndTime_i``
    (== ``StartTime_{i+1}`` in contiguous tiling) to the move ending at ``t``.
    """
    missing = set(_MOVE_COLUMNS).difference(moves.columns)
    if missing:
        raise ValueError(f"moves missing required columns: {sorted(missing)}")
    if {event_time, event_price}.difference(events.columns):
        raise ValueError(f"events must contain '{event_time}' and '{event_price}'")
    if events.height and not events.get_column(event_time).is_sorted():
        raise ValueError(f"events must be sorted non-decreasing by '{event_time}'")

    if events.height == 0 or moves.height == 0:
        return events.with_columns(
            pl.lit(None, dtype=pl.Int32).alias("move_dir"),
            pl.lit(None, dtype=pl.Float64).alias("move_start_price"),
            pl.lit(None, dtype=pl.Float64).alias("move_end_price"),
            pl.lit(None, dtype=events.schema[event_time]).alias("move_start_time"),
            pl.lit(None, dtype=events.schema[event_time]).alias("move_end_time"),
            pl.lit(None, dtype=pl.Float64).alias("pos"),
            pl.lit(None, dtype=pl.Boolean).alias("final_third"),
            pl.lit(AFTER_LAST).alias("exclusion"),
        )

    right = (
        moves.select(
            pl.col("StartTime").alias("move_start_time"),
            pl.col("EndTime").alias("move_end_time"),
            pl.col("StartPrice").alias("move_start_price"),
            pl.col("EndPrice").alias("move_end_price"),
            pl.col("Direction").cast(pl.Int32).alias("move_dir"),
        )
        .sort("move_end_time")
    )

    joined = events.join_asof(
        right,
        left_on=event_time,
        right_on="move_end_time",
        strategy="forward",
    )

    if left_strict:
        guard_fail = pl.col("move_start_time") >= pl.col(event_time)
    else:
        guard_fail = pl.col("move_start_time") > pl.col(event_time)

    exclusion = (
        pl.when(pl.col("move_end_time").is_null())
        .then(pl.lit(AFTER_LAST))
        .when(guard_fail)
        .then(pl.lit(BEFORE_FIRST))
        .when(pl.col("move_end_price") == pl.col("move_start_price"))
        .then(pl.lit(DEGENERATE))
        .otherwise(pl.lit(ASSIGNED))
        .alias("exclusion")
    )
    joined = joined.with_columns(exclusion)

    pos = (
        pl.when(pl.col("exclusion") == ASSIGNED)
        .then(
            (pl.col(event_price) - pl.col("move_start_price"))
            / (pl.col("move_end_price") - pl.col("move_start_price"))
        )
        .otherwise(None)
        .alias("pos")
    )
    joined = joined.with_columns(pos)
    final_third = (
        pl.when(pl.col("exclusion") == ASSIGNED)
        .then(pl.col("pos") >= threshold)
        .otherwise(None)
        .alias("final_third")
    )
    return joined.with_columns(final_third)


def direction_matched_rate(
    inmove_pos: np.ndarray,
    inmove_dir: np.ndarray,
    event_dir: np.ndarray,
    *,
    threshold: float = POSITION_THRESHOLD,
) -> float:
    """Exact direction-stratified random-timing final-third rate (R->inf limit).

    ``FT_rand = sum_d w_d * q_d`` where ``q_d`` is the in-move-bar final-third
    rate of direction ``d`` and ``w_d`` is the assigned-event direction mix. This
    is the closed-form limit of a matched-count uniform draw over in-move bars,
    computed exactly to remove Monte-Carlo noise from a governance-binding number.

    Parameters
    ----------
    inmove_pos, inmove_dir : np.ndarray
        Position and containing-move direction of every eligible in-move bar.
    event_dir : np.ndarray
        Containing-move direction of every assigned event (supplies the weights).
    threshold : float, default 0.67
        Final-third threshold.

    Returns
    -------
    float
        ``FT_rand``.

    Raises
    ------
    ValueError
        If ``event_dir`` is empty. ``FT_rand`` is a direction-mix-weighted rate
        and is undefined with no assigned events (the weights are ``0/0``);
        callers must guard on the event count before calling rather than letting
        a ``nan`` propagate silently into ``Delta`` and the CI.
    """
    n = int(event_dir.shape[0])
    if n == 0:
        raise ValueError(
            "event_dir is empty: FT_rand is undefined with no assigned events; "
            "guard on the event count before calling"
        )
    total = 0.0
    for d in (-1, 1):
        w = float(np.count_nonzero(event_dir == d)) / n
        if w == 0.0:
            continue
        mask = inmove_dir == d
        # An event of direction d has >= 1 eligible in-move bar (its own bar is
        # in the population), so q_d is defined whenever w_d > 0.
        q = float(np.mean(inmove_pos[mask] >= threshold)) if mask.any() else 0.0
        total += w * q
    return total


def duration_fraction(
    event_idx: np.ndarray,
    start_idx: np.ndarray,
    end_idx: np.ndarray,
) -> np.ndarray:
    """Duration-fraction position on bar indices ``(t - start) / (end - start)``.

    A zero-span move (``end_idx == start_idx``) yields ``nan`` (excluded).
    """
    span = (end_idx - start_idx).astype(np.float64)
    out = np.full(event_idx.shape, np.nan, dtype=np.float64)
    ok = span != 0.0
    out[ok] = (event_idx[ok].astype(np.float64) - start_idx[ok]) / span[ok]
    return out
