"""Session anchors, initial-balance windows, breaks and excursions (INFR-018 HYP-I2).

Source ``SIGNAL-SIGNED.md`` A7: *"on this 24/7 venue, session anchors (daily
settlement/UTC-0, funding timestamps, major equity-market opens) are chosen by
measured breakout expectancy … selection across k candidates is k hypotheses."*

The whole module is anchor-agnostic on purpose: a candidate anchor and a
random-offset pseudo-anchor control differ **only** by the timestamp table they
supply, so the control cannot accidentally receive different treatment from the
real anchor. That is the design's non-degeneracy guarantee expressed in code
rather than in prose.

Nothing here computes an expectancy, a cost, or a grade. It computes the
dimensionless excursion asymmetry ``A = MFE/IB_width − MAE/IB_width``, which is
consumed only as a **contrast against a matched control** (design.md §0).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import polars as pl

#: IB lengths raced, in minutes (source S1: "the first 15-60 min").
IB_LENGTHS: tuple[int, ...] = (15, 30, 60)

#: Minimum coverage for a session to be admitted, as a fraction of its bars.
MIN_COVERAGE = 0.9

_UTC = ZoneInfo("UTC")


@dataclass(frozen=True)
class AnchorSpec:
    """A candidate session clock.

    Attributes
    ----------
    anchor_id :
        Stable identifier written into the registry pin.
    minutes_of_day :
        UTC minutes-of-day when ``tz`` is None (fixed-offset anchors).
    tz :
        IANA zone for DST-correct anchors; ``local_time`` is then the local
        wall-clock the anchor tracks. A fixed UTC offset is **wrong** for equity
        opens — New York's open moves by an hour twice a year, and pinning it to
        one UTC minute would mis-anchor roughly half the sample.
    local_time :
        ``(hour, minute)`` in ``tz``.
    """

    anchor_id: str
    minutes_of_day: tuple[int, ...] | None = None
    tz: str | None = None
    local_time: tuple[int, int] | None = None

    @property
    def sessions_per_day(self) -> int:
        return len(self.minutes_of_day) if self.minutes_of_day else 1


#: The four pre-registered candidates (design.md §3.1). Frozen before results.
CANDIDATE_ANCHORS: tuple[AnchorSpec, ...] = (
    AnchorSpec("A-UTC0", minutes_of_day=(0,)),
    AnchorSpec("A-FUND", minutes_of_day=(0, 480, 960)),
    AnchorSpec("A-USOPEN", tz="America/New_York", local_time=(9, 30)),
    AnchorSpec("A-EUOPEN", tz="Europe/London", local_time=(8, 0)),
)

#: INFR-020 operational anchors for 1h / 4h session framing (design §2 W4).
#: No breakout-expectancy race is run for these. They are not edge-bearing.
#: A-H4's grid is a strict superset of A-FUND; A-FUND was raced negative at
#: INFR-018 for breakout-after-IB — that evidence scopes anchor *quality*, not
#: absorption detection (AMENDMENT-9).
OPERATIONAL_ANCHORS: tuple[AnchorSpec, ...] = (
    AnchorSpec("A-H1", minutes_of_day=tuple(range(0, 1440, 60))),
    AnchorSpec("A-H4", minutes_of_day=(0, 240, 480, 720, 960, 1200)),
)

#: Wall-clock minutes of initial balance for the D6 pairs, before the
#: "minimum one LTF bar" floor. D4's 1h LTF forces 60 min (design §2 W4).
IB_WALL_CLOCK_MINUTES = 15


def ib_minutes_for_ltf(
    ltf_bar_minutes: int,
    *,
    wall_clock_minutes: int = IB_WALL_CLOCK_MINUTES,
) -> int:
    """IB length in wall-clock minutes as LTF bars covering it, minimum one bar.

    Holding wall-clock constant makes IB share-of-session vary across pairs
    (1%→25%); IB-derived objects are not cross-pair comparable without saying so.

    At ``ltf_bar_minutes=1`` and wall-clock 15 this returns 15 — the frozen
    ``session_breaks(..., ib_minutes=15)`` path for A-USOPEN / D1.
    """
    if ltf_bar_minutes < 1:
        raise ValueError(f"ltf_bar_minutes must be >= 1, got {ltf_bar_minutes}")
    if wall_clock_minutes < 1:
        raise ValueError(f"wall_clock_minutes must be >= 1, got {wall_clock_minutes}")
    return max(wall_clock_minutes, ltf_bar_minutes)


def operational_anchor(anchor_id: str) -> AnchorSpec:
    """Lookup an INFR-020 operational anchor by id; raise if unknown."""
    for a in OPERATIONAL_ANCHORS:
        if a.anchor_id == anchor_id:
            return a
    raise KeyError(f"unknown operational anchor {anchor_id!r}; known={[a.anchor_id for a in OPERATIONAL_ANCHORS]}")

#: UTC minutes-of-day occupied by each candidate anchor across the year,
#: including both DST phases of the equity opens.
OCCUPIED_MINUTES: dict[str, tuple[int, ...]] = {
    "A-UTC0": (0,),
    "A-FUND": (0, 480, 960),
    "A-EUOPEN": (420, 480),   # GMT 07:00 UTC / BST 08:00 UTC
    "A-USOPEN": (810, 870),   # EDT 13:30 UTC / EST 14:30 UTC
}

#: A pseudo-anchor must sit at least this far from the anchor it is CONTROLLING.
#: AMENDMENT-1 (design.md §11): the exclusion is scoped to the anchor under test,
#: not to all four candidates. Excluding every meaningful clock would make the
#: control *less* arbitrary than a genuinely arbitrary clock — an arbitrary draw
#: may land near some other meaningful time, and removing those draws lowers the
#: control level and inflates the contrast. Scoping the exclusion keeps the only
#: constraint that matters (a control must not be a near-copy of the thing it
#: controls) and biases the contrast conservatively rather than upward. It also
#: makes the 8-hourly shape feasible at all: the all-candidate exclusion left
#: too little of the 480-minute cycle to place the control clocks.
PSEUDO_EXCLUSION_MINUTES = 60

#: Control clocks per anchor. Above the L-19 floor of 25 disjoint seeds.
N_PSEUDO = 30


def _circ_dist(a: int, b: int) -> int:
    """Minutes between two minutes-of-day on the 1440-minute circle."""
    d = abs(a - b) % 1440
    return min(d, 1440 - d)


def feasible_offsets(anchor_id: str, sessions_per_day: int) -> list[int]:
    """Base offsets whose every implied anchor clears the exclusion zone.

    For the 8-hourly shape an offset ``m`` implies ``m``, ``m+480`` and
    ``m+960``; all three must clear, which is why this is computed rather than
    assumed.
    """
    occupied = OCCUPIED_MINUTES[anchor_id]
    step = 1440 // sessions_per_day
    out = []
    for m in range(step):
        implied = [(m + k * step) % 1440 for k in range(sessions_per_day)]
        if all(_circ_dist(i, o) >= PSEUDO_EXCLUSION_MINUTES for i in implied for o in occupied):
            out.append(m)
    return out


def pseudo_offsets(anchor_id: str, sessions_per_day: int, n: int, seed: int) -> list[int]:
    """Place ``n`` pseudo-anchor offsets controlling a specific candidate anchor.

    Every implied anchor minute sits at least
    :data:`PSEUDO_EXCLUSION_MINUTES` from the minutes of **the anchor being
    controlled**. That is what makes this destroy fixed-point-free **by
    construction** rather than by a post-hoc check (L-28): no control clock can
    coincide with the anchor it controls, so the control arm can never silently
    contain the real arm.

    The clocks are placed as a **stratified sample of the feasible arc with a
    seeded random phase**, not by rejection sampling. Rejection sampling with a
    mutual-spacing constraint fails unpredictably as the arc fills — the
    8-hourly shape leaves only ~361 feasible minutes, where random greedy
    packing tops out near Renyi's parking constant and cannot reliably place 30.
    A stratified placement always succeeds, spreads the control clocks maximally
    (so 30 clocks are 30 genuinely different clocks), keeps the draw regenerable
    from ``(anchor_id, shape, n, seed)`` alone, and lowers the variance of the
    arbitrary-clock estimate rather than raising it.

    Parameters
    ----------
    anchor_id :
        The candidate being controlled; keys :data:`OCCUPIED_MINUTES`.
    sessions_per_day :
        1 for a daily shape, 3 for the 8-hourly funding shape.
    n :
        Number of control clocks.
    seed :
        Frozen phase seed.

    Returns
    -------
    list[int]
        Sorted base offsets in minutes-of-day.
    """
    import random

    feas = feasible_offsets(anchor_id, sessions_per_day)
    if len(feas) < n:
        raise RuntimeError(
            f"only {len(feas)} feasible offsets for {anchor_id} (shape {sessions_per_day}); "
            f"cannot place {n} control clocks"
        )
    phase = random.Random(seed).random()
    idx = sorted({int((phase + k / n) % 1.0 * len(feas)) for k in range(n)})
    while len(idx) < n:  # collision at the wrap point; take the next free slot
        cand = next(i for i in range(len(feas)) if i not in idx)
        idx = sorted(set(idx) | {cand})
    return sorted(feas[i] for i in idx)


def assert_no_fixed_points(anchor_id: str, offsets: list[int], sessions_per_day: int) -> None:
    """Verify the control clocks share no anchor minute with the real anchor.

    L-28: VAL-008 shipped a destroy that left 11.1% of slots at true alignment
    and only partially collapsed the planted edge. The guarantee is asserted
    here rather than trusted to the sampler.
    """
    occupied = set(OCCUPIED_MINUTES[anchor_id])
    step = 1440 // sessions_per_day
    for m in offsets:
        implied = {(m + k * step) % 1440 for k in range(sessions_per_day)}
        if implied & occupied:
            raise RuntimeError(
                f"FIXED POINT in pseudo-anchor destroy for {anchor_id}: offset {m} implies "
                f"{sorted(implied & occupied)}, which the real anchor occupies"
            )


def anchor_table(spec: AnchorSpec, start: datetime, end: datetime) -> pl.DataFrame:
    """Materialise every session anchor instant in ``[start, end)``.

    Returns
    -------
    polars.DataFrame
        ``anchor_ts`` (naive UTC, sorted) and ``session_end`` (the next anchor).
        Sessions are back-to-back and exhaustive: a 24/7 venue has no gap.
    """
    stamps: list[datetime] = []
    day = datetime(start.year, start.month, start.day) - timedelta(days=2)
    last = end + timedelta(days=2)
    while day < last:
        if spec.minutes_of_day is not None:
            for m in spec.minutes_of_day:
                stamps.append(day + timedelta(minutes=m))
        else:
            tz = ZoneInfo(spec.tz)  # type: ignore[arg-type]
            hh, mm = spec.local_time  # type: ignore[misc]
            local = datetime(day.year, day.month, day.day, hh, mm, tzinfo=tz)
            stamps.append(local.astimezone(_UTC).replace(tzinfo=None))
        day += timedelta(days=1)
    stamps = sorted(set(stamps))
    df = pl.DataFrame({"anchor_ts": stamps}).with_columns(
        pl.col("anchor_ts").shift(-1).alias("session_end")
    )
    return df.drop_nulls("session_end")


def pseudo_spec(base_shape: int, offset: int, idx: int) -> AnchorSpec:
    """Build a pseudo-anchor spec at ``offset`` with the given session shape."""
    step = 1440 // base_shape
    return AnchorSpec(
        f"PSEUDO-{base_shape}x-{idx:02d}",
        minutes_of_day=tuple((offset + k * step) % 1440 for k in range(base_shape)),
    )


# ---------------------------------------------------------------------------
# Session construction — vectorised, one pass per (symbol, anchor, L)
# ---------------------------------------------------------------------------


def attach_sessions(bars: pl.DataFrame, anchors: pl.DataFrame, ib_minutes: int) -> pl.DataFrame:
    """Join bars to their session anchor and elapsed-minutes offset.

    Shared by the HYP-I2 break construction and the HYP-I3 poke construction so
    both phases partition time identically — HYP-I3 inherits the frozen anchor,
    and inheriting it through a *different* join would be a silent divergence.
    """
    if bars.height == 0:
        return bars
    return (
        bars.sort("OpenTime")
        .join_asof(
            anchors.sort("anchor_ts"),
            left_on="OpenTime",
            right_on="anchor_ts",
            strategy="backward",
        )
        .drop_nulls("anchor_ts")
        .filter(pl.col("OpenTime") < pl.col("session_end"))
        .with_columns(
            ((pl.col("OpenTime") - pl.col("anchor_ts")).dt.total_minutes()).alias("mins_since"),
            pl.lit(ib_minutes).alias("ib_minutes"),
        )
    )


def session_breaks(
    bars: pl.DataFrame, anchors: pl.DataFrame, ib_minutes: int, *, ib_shift: int = 0
) -> pl.DataFrame:
    """Compute one row per admitted session: IB, break, and excursion.

    The three windows are disjoint by construction and the disjointness is
    asserted downstream (design.md §2): the IB spans ``[anchor, anchor+L)``, the
    break is searched in ``[anchor+L, session_end)``, and the excursion is
    measured strictly **after** the break bar closes. An excursion that included
    its own break bar would import the break bar's range into the result.

    Parameters
    ----------
    bars :
        One symbol's fenced bars, sorted by ``OpenTime``.
    anchors :
        Output of :func:`anchor_table` covering the same span.
    ib_minutes :
        IB length ``L``.

    Returns
    -------
    polars.DataFrame
        ``anchor_ts, ib_high, ib_low, ib_width, n_ib, n_post, break_ts,
        break_side, break_close, mfe, mae, mfe_norm, mae_norm, asym``.
        Sessions with no break carry nulls in the break/excursion columns and
        are retained — the break RATE is part of the read, so dropping them
        would silently condition the statistic on breaking.
    """
    if bars.height == 0:
        return pl.DataFrame()

    joined = attach_sessions(bars, anchors, ib_minutes)
    if joined.height == 0:
        return pl.DataFrame()

    ib = (
        joined.filter(pl.col("mins_since") < ib_minutes)
        .group_by("anchor_ts")
        .agg(
            pl.col("High").max().alias("ib_high"),
            pl.col("Low").min().alias("ib_low"),
            pl.len().alias("n_ib"),
            # The bars that ESTABLISHED each edge. A class event that is itself
            # the bar which set an edge would otherwise score zero distance from
            # it, so the clustering test (HYP-I4) needs these to exclude a bar
            # from the level set it created (design.md §2).
            pl.col("OpenTime").sort_by("High", descending=True).first().alias("ib_high_ts"),
            pl.col("OpenTime").sort_by("Low").first().alias("ib_low_ts"),
        )
        .sort("anchor_ts")
    )
    # The TRUE width is retained separately from the boundary levels, because the
    # future-destroy tripwire below replaces the levels and must not also move the
    # normaliser (see the ib_shift comment).
    ib = ib.with_columns((pl.col("ib_high") - pl.col("ib_low")).alias("ib_width"))

    if ib_shift:
        # FUTURE-DESTROY TRIPWIRE (design.md §3.5): take each session's BOUNDARY
        # LEVELS from a LATER session's IB window, so the boundary encodes
        # information that did not exist when the session opened. The break
        # search, the excursion window, AND THE NORMALISER are untouched.
        #
        # Holding ib_width fixed is load-bearing, not tidiness. Shifting it too
        # would divide each session's excursion by a foreign session's width, so
        # the destroyed arm would differ from the real arm by a units change as
        # well as by the lost boundary information — and the tripwire's null
        # would be non-zero by construction, which is exactly what QA run 1
        # observed (collapse fraction −6.10 instead of ≈0). With the divisor
        # pinned, the ONLY thing destroyed is the boundary's causality, which is
        # what the tripwire is for.
        #
        # A contrast that SURVIVES this is a leak in the causal construction: the
        # emission is invalid and the code is fixed. It is never read as "no effect".
        ib = ib.with_columns(
            pl.col("ib_high").shift(-ib_shift),
            pl.col("ib_low").shift(-ib_shift),
        ).drop_nulls(["ib_high", "ib_low"])
    post = joined.filter(pl.col("mins_since") >= ib_minutes).join(ib, on="anchor_ts", how="inner")

    # Coverage: an under-covered session (listing day, outage) is marked
    # INCOMPLETE and COUNTED, never silently dropped (design.md §3.2). The length
    # is computed PER SESSION, not from the global maximum: DST makes A-USOPEN and
    # A-EUOPEN sessions 23h/24h/25h, and a global max would impose a ~98% coverage
    # bar on the short ones — an anchor-asymmetric admission filter inside a race
    # between anchors, penalising exactly the two DST anchors.
    counts = post.group_by("anchor_ts").agg(
        pl.len().alias("n_post"), pl.col("session_end").first().alias("session_end")
    ).with_columns(
        ((pl.col("session_end") - pl.col("anchor_ts")).dt.total_minutes()).alias("session_len")
    )
    graded = counts.join(ib, on="anchor_ts").with_columns(
        (
            (pl.col("n_ib") >= MIN_COVERAGE * ib_minutes)
            & (pl.col("n_post") >= MIN_COVERAGE * (pl.col("session_len") - ib_minutes))
        ).alias("admitted")
    )
    n_incomplete = graded.filter(~pl.col("admitted")).height
    ok = graded.filter(pl.col("admitted")).select(
        "anchor_ts", "session_end", "n_ib", "n_post", "ib_high", "ib_low", "ib_width",
        "ib_high_ts", "ib_low_ts",
    )
    post = post.join(ok.select("anchor_ts"), on="anchor_ts", how="semi")
    if post.height == 0:
        # KNOWN LIMITATION (QA I-27, open): when EVERY session is incomplete there
        # is no admitted row to carry the constant ``n_incomplete_sessions``
        # column, so this symbol contributes 0 to the caller's incomplete tally
        # instead of its true count. The count is a report layer and no gate reads
        # it; carrying it out would require changing this function's return
        # contract, which HYP-I3 and HYP-I4 also consume, so it is recorded rather
        # than patched mid-item.
        return pl.DataFrame()

    # First close beyond an IB edge, in time order. This is the PROVISIONAL
    # pre-A6 break rule (design.md §3.2): Phase 1 precedes the A6 freeze, so it
    # uses the source's minimal precursor, applied identically to every cell and
    # every control so it cannot favour one anchor.
    beyond = post.with_columns(
        pl.when(pl.col("Close") > pl.col("ib_high"))
        .then(pl.lit(1))
        .when(pl.col("Close") < pl.col("ib_low"))
        .then(pl.lit(-1))
        .otherwise(pl.lit(0))
        .alias("side")
    ).filter(pl.col("side") != 0)

    first = (
        beyond.sort("OpenTime")
        .group_by("anchor_ts")
        .agg(
            pl.col("OpenTime").first().alias("break_ts"),
            pl.col("side").first().alias("break_side"),
            pl.col("Close").first().alias("break_close"),
        )
    )

    exc = (
        post.join(first, on="anchor_ts", how="inner")
        .filter(pl.col("OpenTime") > pl.col("break_ts"))  # strictly after the break bar
        .group_by("anchor_ts")
        .agg(
            pl.col("High").max().alias("post_high"),
            pl.col("Low").min().alias("post_low"),
            pl.len().alias("n_exc"),
        )
    )

    out = (
        ok.join(first, on="anchor_ts", how="left")
        .join(exc, on="anchor_ts", how="left")
        .with_columns(
            pl.when(pl.col("break_side") == 1)
            .then(pl.col("post_high") - pl.col("break_close"))
            .otherwise(pl.col("break_close") - pl.col("post_low"))
            .alias("mfe"),
            pl.when(pl.col("break_side") == 1)
            .then(pl.col("break_close") - pl.col("post_low"))
            .otherwise(pl.col("post_high") - pl.col("break_close"))
            .alias("mae"),
        )
        .with_columns(
            # A zero-width IB (a fully flat opening window) would divide by zero;
            # it yields a null asymmetry rather than an infinity, and the count of
            # such sessions is reported.
            pl.when(pl.col("ib_width") > 0)
            .then(pl.col("mfe") / pl.col("ib_width"))
            .otherwise(None)
            .alias("mfe_norm"),
            pl.when(pl.col("ib_width") > 0)
            .then(pl.col("mae") / pl.col("ib_width"))
            .otherwise(None)
            .alias("mae_norm"),
        )
        .with_columns((pl.col("mfe_norm") - pl.col("mae_norm")).alias("asym"))
        .with_columns(pl.lit(n_incomplete).alias("n_incomplete_sessions"))
        .sort("anchor_ts")
    )
    return out
