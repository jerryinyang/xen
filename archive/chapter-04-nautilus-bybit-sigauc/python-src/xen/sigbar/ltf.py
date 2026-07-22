"""Signed-aware LTF aggregation and window integrity (INFR-020 W2a/W2b).

Clock-aligned N-minute aggregation on the staging series **as recorded** —
no zero-fill / fabricated minutes on any primary path (AMENDMENT-6).

Every aggregated bar carries ``SourceBars``, ``n_missing``, ``window_class`` and
``traded_fraction``. Only ``COMPLETE`` windows may enter the event population
or a seasonal fit.

Gap days are derived from staging: UTC days inside the instrument's observed
DESIGN span with zero bars (QA-3 S-2). The ledger has no gap timestamps.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable

import polars as pl

#: Window integrity classes (design §2 W2a).
WINDOW_COMPLETE = "COMPLETE"
WINDOW_NO_TRADE_PARTIAL = "NO_TRADE_PARTIAL"
WINDOW_GAP_CONTAMINATED = "GAP_CONTAMINATED"

WINDOW_CLASSES: tuple[str, ...] = (
    WINDOW_COMPLETE,
    WINDOW_NO_TRADE_PARTIAL,
    WINDOW_GAP_CONTAMINATED,
)

# Float reconciliation tolerance for Buy+Sell == Volume (A8 / A4).
_SPLIT_TOL = 1e-6


def design_gap_days(bars_1m: pl.DataFrame, *, time_col: str = "OpenTime") -> set:
    """UTC calendar dates with zero bars inside the instrument's observed span.

    Frame is the instrument's own first/last bar in the loaded series (DESIGN
    when called on DESIGN-fenced bars), not the whole-archive ledger.
    """
    if bars_1m.height == 0:
        return set()
    t0 = bars_1m[time_col].min()
    t1 = bars_1m[time_col].max()
    # Inclusive calendar days from first bar day through last bar day.
    span = pl.DataFrame(
        {time_col: pl.datetime_range(t0, t1, interval="1d", eager=True)}
    ).with_columns(pl.col(time_col).dt.date().alias("d"))
    present = set(bars_1m.select(pl.col(time_col).dt.date()).unique().to_series().to_list())
    all_days = set(span["d"].to_list())
    return all_days - present


def gap_excision_spans(gap_days: Iterable) -> list[dict]:
    """Collapse gap dates into contiguous span records for disclosure."""
    days = sorted(gap_days)
    if not days:
        return []
    spans: list[dict] = []
    start = prev = days[0]
    for d in days[1:]:
        if (d - prev).days == 1:
            prev = d
            continue
        spans.append({"start": str(start), "end": str(prev), "n_days": (prev - start).days + 1})
        start = prev = d
    spans.append({"start": str(start), "end": str(prev), "n_days": (prev - start).days + 1})
    return spans


def _classify_window(
    open_time: datetime,
    period_minutes: int,
    source_times: list[datetime],
    gap_days: set,
) -> tuple[str, int, float]:
    """Return (window_class, n_missing, traded_fraction) for one window."""
    n = period_minutes
    source_set = set(source_times)
    source_bars = len(source_set)
    n_missing = n - source_bars
    traded_fraction = source_bars / n if n else 0.0
    if source_bars == n:
        return WINDOW_COMPLETE, 0, 1.0

    expected = [open_time + timedelta(minutes=i) for i in range(n)]
    missing = [t for t in expected if t not in source_set]
    if any(t.date() in gap_days for t in missing):
        return WINDOW_GAP_CONTAMINATED, n_missing, traded_fraction
    return WINDOW_NO_TRADE_PARTIAL, n_missing, traded_fraction


def aggregate_signed(
    bars_1m: pl.DataFrame,
    period_minutes: int,
    *,
    gap_days: set | None = None,
    complete_only: bool = False,
    time_col: str = "OpenTime",
) -> pl.DataFrame:
    """Clock-aligned N-minute aggregation carrying the taker split.

    Aggregation (design §2 W2b)::

        Open  = first 1m Open        Volume     = sum
        High  = max   1m High        BuyVolume  = sum
        Low   = min   1m Low         SellVolume = sum
        Close = last  1m Close       NTrades    = sum
        Delta = BuyVolume − SellVolume
        SourceBars = count

    No fabricated bars. Windows with fewer than ``period_minutes`` source rows
    are classified, not filled. Pass ``complete_only=True`` to retain only
    ``COMPLETE`` windows (the only population eligible for fit/events).

    Parameters
    ----------
    bars_1m :
        Staging 1-minute bars as recorded (signed columns present).
    period_minutes :
        N for the LTF bar.
    gap_days :
        Staging-derived UTC dates with zero bars; if None, derived from
        ``bars_1m`` itself.
    complete_only :
        If True, drop non-COMPLETE windows after classification.
    """
    if period_minutes < 1:
        raise ValueError(f"period_minutes must be >= 1, got {period_minutes}")
    if bars_1m.height == 0:
        return bars_1m.clear()

    required = {"Open", "High", "Low", "Close", "Volume", "BuyVolume", "SellVolume", "NTrades", time_col}
    missing = required - set(bars_1m.columns)
    if missing:
        raise ValueError(f"bars_1m missing required columns: {sorted(missing)}")

    gaps = set(gap_days) if gap_days is not None else design_gap_days(bars_1m, time_col=time_col)
    every = f"{period_minutes}m"

    # Source OpenTimes per window (for classification + causality).
    src = (
        bars_1m.sort(time_col)
        .group_by_dynamic(time_col, every=every, closed="left", label="left")
        .agg(
            pl.col("Open").first(),
            pl.col("High").max(),
            pl.col("Low").min(),
            pl.col("Close").last(),
            pl.col("Volume").sum(),
            pl.col("BuyVolume").sum(),
            pl.col("SellVolume").sum(),
            pl.col("NTrades").sum(),
            pl.len().alias("SourceBars"),
            pl.col(time_col).alias("_src_times"),
        )
    )

    if src.height == 0:
        return src

    classes: list[str] = []
    n_miss_list: list[int] = []
    frac_list: list[float] = []
    src_max: list[datetime] = []
    for row in src.iter_rows(named=True):
        open_t = row[time_col]
        times = list(row["_src_times"])
        wc, nm, tf = _classify_window(open_t, period_minutes, times, gaps)
        classes.append(wc)
        n_miss_list.append(nm)
        frac_list.append(tf)
        src_max.append(max(times) if times else open_t)

    out = (
        src.drop("_src_times")
        .with_columns(
            pl.Series("window_class", classes),
            pl.Series("n_missing", n_miss_list, dtype=pl.Int32),
            pl.Series("traded_fraction", frac_list),
            pl.Series("source_max_open", src_max),
            (pl.col("BuyVolume") - pl.col("SellVolume")).alias("Delta"),
        )
        .with_columns(
            # Bar close is exclusive end of the window; provenance bound.
            (pl.col(time_col) + pl.duration(minutes=period_minutes)).alias("CloseTime"),
        )
    )

    if complete_only:
        out = out.filter(pl.col("window_class") == WINDOW_COMPLETE)

    return out


def assert_bar_causality(
    aggregated: pl.DataFrame,
    bars_1m: pl.DataFrame,
    period_minutes: int,
    *,
    time_col: str = "OpenTime",
) -> None:
    """Raise unless every source minute of each agg bar lies in ``[open, open+N)``.

    VT-4(c)/(causality): an N-minute bar closing at t is composed only of
    1-minute bars with OpenTime < t.
    """
    if aggregated.height == 0:
        return
    # Vectorised: re-bucket the 1m series on the same clock grid and compare
    # counts + source bounds per window (QA-6 I-2 — this now runs on the
    # production path, so it must be O(n), not a per-row full-frame filter).
    recount = (
        bars_1m.sort(time_col)
        .group_by_dynamic(time_col, every=f"{period_minutes}m", closed="left", label="left")
        .agg(
            pl.len().alias("_n_src"),
            pl.col(time_col).max().alias("_src_max"),
        )
    )
    j = aggregated.join(recount, on=time_col, how="left")
    missing = j.filter(pl.col("_n_src").is_null())
    if missing.height:
        raise RuntimeError(
            f"BAR CAUSALITY: {missing.height} aggregated windows have no 1m source rows "
            f"(first {missing[time_col][0]})"
        )
    bad_count = j.filter(pl.col("_n_src") != pl.col("SourceBars"))
    if bad_count.height:
        r = bad_count.row(0, named=True)
        raise RuntimeError(
            f"BAR CAUSALITY: window {r[time_col]} SourceBars={r['SourceBars']} "
            f"but {r['_n_src']} 1m bars in [open, open+{period_minutes}m)"
        )
    close_expr = pl.col(time_col) + pl.duration(minutes=period_minutes)
    bad_bound = j.filter(pl.col("_src_max") >= close_expr)
    if bad_bound.height:
        raise RuntimeError(
            f"BAR CAUSALITY: {bad_bound.height} windows have a source OpenTime >= bar close"
        )
    if "source_max_open" in j.columns:
        bad_prov = j.filter(pl.col("source_max_open") >= close_expr)
        if bad_prov.height:
            raise RuntimeError(
                f"BAR CAUSALITY: {bad_prov.height} windows have source_max_open >= bar close"
            )


def assert_split_additive(aggregated: pl.DataFrame, *, tol: float = _SPLIT_TOL) -> None:
    """A4 / A8: BuyVolume + SellVolume == Volume within float tolerance."""
    if aggregated.height == 0:
        return
    gap = (
        aggregated.select(
            (pl.col("BuyVolume") + pl.col("SellVolume") - pl.col("Volume")).abs().max()
        ).item()
    )
    if gap is not None and gap > tol:
        raise RuntimeError(
            f"SPLIT ADDITIVITY: max |Buy+Sell−Volume| = {gap} > tol {tol}"
        )


def assert_windows_complete(
    df: pl.DataFrame,
    *,
    context: str = "fit/event",
) -> None:
    """Raise if any non-COMPLETE window reaches a primary fit/event path.

    VT-4(h). Also rejects missing classification columns on non-empty frames
    that claim to be LTF series.
    """
    if df.height == 0:
        return
    if "window_class" not in df.columns:
        raise RuntimeError(
            f"WINDOWS COMPLETE: {context} frame lacks window_class — "
            "cannot prove no partial/gap window entered the primary path"
        )
    bad = df.filter(pl.col("window_class") != WINDOW_COMPLETE)
    if bad.height:
        raise RuntimeError(
            f"WINDOWS COMPLETE: {bad.height} non-COMPLETE rows on {context} path "
            f"(classes={bad['window_class'].unique().to_list()})"
        )


def max_source_open(aggregated: pl.DataFrame) -> datetime | None:
    """Max source-bar OpenTime feeding the frame (for provenance asserts)."""
    if aggregated.height == 0 or "source_max_open" not in aggregated.columns:
        return None
    return aggregated["source_max_open"].max()


def absorb_candidate_predicate(
    bars: pl.DataFrame,
    thresholds: dict[str, dict[str, float]],
    *,
    require_complete: bool = True,
) -> pl.DataFrame:
    """Shared absorption candidate filter (OBJECT-IDENTITY §1.1).

    A candidate is an LTF bar whose seasonal volume residual is at/above the
    per-(symbol, timeframe) p90 cut and whose range residual is at/below the
    p10 cut, on the COMPLETE-window series only.

    SPDR-009 imports this function rather than reimplementing it.
    Zero-fill / reconstruction is WITHDRAWN — the predicate never sees a
    fabricated minute.
    """
    if bars.height == 0:
        return bars

    need = ("volume_resid", "range_resid")
    missing = [c for c in need if c not in bars.columns]
    if missing:
        raise RuntimeError(f"absorb_candidate_predicate missing columns {missing}")
    if "volume" not in thresholds or "range" not in thresholds:
        raise RuntimeError("thresholds must include volume and range cuts")

    v_hi = thresholds["volume"]["high"]
    r_lo = thresholds["range"]["low"]

    out = bars
    if require_complete:
        if "window_class" in out.columns:
            out = out.filter(pl.col("window_class") == WINDOW_COMPLETE)
        if "traded_fraction" in out.columns:
            # A9 tripwire: COMPLETE ⇒ traded_fraction == 1.0 under staging invariants.
            bad_tf = out.filter(pl.col("traded_fraction") < 1.0)
            if bad_tf.height:
                raise RuntimeError(
                    f"CANDIDATE TRADED_FRACTION: {bad_tf.height} COMPLETE rows with "
                    "traded_fraction < 1.0 (VT-4(j))"
                )
            out = out.filter(pl.col("traded_fraction") >= 1.0)

    return out.filter(
        (pl.col("volume_resid") >= v_hi) & (pl.col("range_resid") <= r_lo)
    )


def assign_candidate_sessions(
    cands: pl.DataFrame,
    anchors: pl.DataFrame,
    *,
    ltf_minutes: int,
    time_col: str = "OpenTime",
) -> pl.DataFrame:
    """Attach each candidate bar to its HTF session, decided at the bar's CLOSE.

    SHARED (OBJECT-IDENTITY §1.1): W5 and SPDR-009 must place a bar in the same
    session, so this lives here rather than in either consumer (QA-8 I8-2).

    Conditioning happens at the candidate's close, so the session is the one
    holding the bar's **last source minute** (``OpenTime + ltf − 1m``): a bar
    straddling an anchor belongs to the session it ends in. Emits
    ``close_time``, ``mins_since_close`` (close − anchor) and
    ``straddles_anchor``. Bars before the first anchor are dropped.

    D4 does not nest into its IB (A-USOPEN anchors at 13:30 UTC, D4 bars open on
    the hour), which is why the test cannot be taken at the bar's open.
    """
    if cands.height == 0 or anchors.height == 0:
        return cands.clear() if cands.height == 0 else pl.DataFrame()
    return (
        cands.with_columns(
            (pl.col(time_col) + pl.duration(minutes=ltf_minutes)).alias("close_time"),
            (pl.col(time_col) + pl.duration(minutes=ltf_minutes - 1)).alias(
                "last_source_minute"
            ),
        )
        .sort("last_source_minute")
        .join_asof(
            anchors.sort("anchor_ts"),
            left_on="last_source_minute",
            right_on="anchor_ts",
            strategy="backward",
        )
        .drop_nulls("anchor_ts")
        .with_columns(
            (pl.col("close_time") - pl.col("anchor_ts"))
            .dt.total_minutes()
            .alias("mins_since_close"),
            (pl.col(time_col) < pl.col("anchor_ts")).alias("straddles_anchor"),
        )
    )


def available_levels_for_candidates(
    cand_sessions: pl.DataFrame,
    levels: pl.DataFrame,
    *,
    time_col: str = "OpenTime",
) -> pl.DataFrame:
    """Candidate × level rows, flagged with whether the level is knowable.

    SHARED (OBJECT-IDENTITY §1.1) — the single implementation of the availability
    rule; W5 and SPDR-009 both call it (QA-8 I8-2). A level is available to a
    candidate when **both** hold:

    * it has finished forming by the candidate's close —
      ``mins_since_close >= available_mins_since`` (IB edges carry the IB
      wall-clock; prior-session levels carry 0); and
    * it was not made by the candidate's **own** minutes — ``formed_ts <
      OpenTime`` (QA-8 I8-1 / QA-9 R9-1). ``formed_ts`` is mandatory for every
      level kind: the edge-setting minute for extrema, and the last source
      minute for profile-derived levels. This also covers a D4 bar that
      straddles A-USOPEN and contributes its first 30 minutes to the prior
      session's levels.

    No forward price is consulted: unavailable levels are excluded, never
    approximated.
    """
    if cand_sessions.height == 0 or levels.height == 0:
        return pl.DataFrame()
    need = {
        "level_price",
        "level_kind",
        "available_mins_since",
        "anchor_ts",
        "formed_ts",
    }
    missing = need - set(levels.columns)
    if missing:
        raise RuntimeError(f"available_levels_for_candidates: levels missing {sorted(missing)}")
    if levels.filter(pl.col("formed_ts").is_null()).height:
        raise RuntimeError(
            "available_levels_for_candidates: every level requires non-null formed_ts "
            "provenance (QA-9 R9-1)"
        )

    lv = levels.select(
        "anchor_ts",
        "level_price",
        "level_kind",
        "available_mins_since",
        "formed_ts",
    )
    return (
        cand_sessions.select(time_col, "Close", "anchor_ts", "mins_since_close")
        .join(lv, on="anchor_ts", how="inner")
        .with_columns(
            (pl.col("mins_since_close") >= pl.col("available_mins_since")).alias("_formed_by_close"),
            (
                pl.col("formed_ts").is_null() | (pl.col("formed_ts") < pl.col(time_col))
            ).alias("_not_self_made"),
        )
        .with_columns(
            (pl.col("_formed_by_close") & pl.col("_not_self_made")).alias("level_available"),
            (pl.col("Close") - pl.col("level_price")).abs().alias("level_distance"),
            pl.col("level_kind").str.starts_with("IB_").alias("is_ib_edge"),
            # excluded because THIS bar's own minutes made the edge (I8-1),
            # distinct from excluded because the IB has not completed yet
            (~pl.col("_not_self_made")).alias("excluded_self_made"),
            (~pl.col("_formed_by_close")).alias("excluded_not_yet_formed"),
        )
        .drop("_formed_by_close", "_not_self_made")
    )


def prior_htf_session_ranges(
    bars_1m: pl.DataFrame,
    anchors: pl.DataFrame,
    *,
    time_col: str = "OpenTime",
) -> pl.DataFrame:
    """Per HTF session: prior-session range from **1-minute** bars only (W5 / D6.3).

    Count-only apparatus: no forward returns, excursions, or contrasts.
    ``prior_session_range`` is the high−low of the *previous* HTF session's 1m
    bars — available at this session's open. Levels/distances consume this as
    the primary zone scale (D6.4.5).

    Implemented via one asof-join + group_by (not a per-session full-frame filter).

    Prior session identity is the **calendar-adjacent** previous anchor in
    ``anchors`` — the same rule the level set uses (QA-6 I-6). A consumer whose
    calendar-adjacent predecessor traded no bars gets a null
    ``prior_session_range`` and is kept in the frame so the caller can count it;
    the run never silently borrows a non-adjacent earlier session.
    """
    if bars_1m.height == 0 or anchors.height == 0:
        return pl.DataFrame()

    joined = (
        bars_1m.sort(time_col)
        .join_asof(
            anchors.sort("anchor_ts"),
            left_on=time_col,
            right_on="anchor_ts",
            strategy="backward",
        )
        .drop_nulls("anchor_ts")
        .filter(pl.col(time_col) < pl.col("session_end"))
    )
    if joined.height == 0:
        return pl.DataFrame()

    cur = (
        joined.group_by("anchor_ts")
        .agg(
            pl.col("High").max().alias("session_high"),
            pl.col("Low").min().alias("session_low"),
            pl.len().alias("n_1m"),
            pl.col("session_end").first(),
        )
        .with_columns(
            (pl.col("session_high") - pl.col("session_low")).alias("session_range")
        )
        .sort("anchor_ts")
    )
    # Calendar-adjacent predecessor from the anchor table itself (not shift(1)
    # over sessions that happen to contain bars) — identical to the level set's
    # consumer→source map.
    a_list = anchors.sort("anchor_ts")["anchor_ts"].to_list()
    if len(a_list) < 2:
        return pl.DataFrame()
    link = pl.DataFrame(
        {
            "anchor_ts": a_list[1:],
            "_src_anchor_ts": a_list[:-1],
        }
    )
    src = cur.select(
        pl.col("anchor_ts").alias("_src_anchor_ts"),
        pl.col("session_range").alias("prior_session_range"),
        pl.col("session_high").alias("prior_session_high"),
        pl.col("session_low").alias("prior_session_low"),
        pl.col("n_1m").alias("prior_n_1m"),
    )
    return (
        cur.join(link, on="anchor_ts", how="inner")
        .join(src, on="_src_anchor_ts", how="left")
        .with_columns(
            pl.when(pl.col("prior_session_range") > 0)
            .then(pl.col("prior_session_range"))
            .otherwise(None)
            .alias("prior_session_range")
        )
        .sort("anchor_ts")
    )

def session_ib_from_1m(
    bars_1m: pl.DataFrame,
    anchors: pl.DataFrame,
    ib_minutes: int,
    *,
    time_col: str = "OpenTime",
) -> pl.DataFrame:
    """IB high/low/width from 1-minute bars only — no break/excursion columns.

    Safer for W5 than ``session_breaks``, which also emits MFE/MAE (outcome-
    adjacent and out of scope for this apparatus item).

    Degenerate sessions (``ib_width <= 0``) are **kept and flagged**
    (``ib_degenerate``) rather than silently dropped, so a thin instrument's
    denominator loss is countable (QA-6 I-9a).
    """
    if bars_1m.height == 0 or anchors.height == 0:
        return pl.DataFrame()
    joined = (
        bars_1m.sort(time_col)
        .join_asof(
            anchors.sort("anchor_ts"),
            left_on=time_col,
            right_on="anchor_ts",
            strategy="backward",
        )
        .drop_nulls("anchor_ts")
        .filter(pl.col(time_col) < pl.col("session_end"))
        .with_columns(
            ((pl.col(time_col) - pl.col("anchor_ts")).dt.total_minutes()).alias(
                "mins_since"
            )
        )
    )
    ib = (
        joined.filter(pl.col("mins_since") < ib_minutes)
        .group_by("anchor_ts")
        .agg(
            pl.col("High").max().alias("ib_high"),
            pl.col("Low").min().alias("ib_low"),
            # When each edge was made (INFR-018 ib_high_ts/ib_low_ts). A level
            # formed by a candidate bar's OWN minutes is not a level that bar can
            # be measured against (QA-8 I8-1).
            pl.col(time_col)
            .filter(pl.col("High") == pl.col("High").max())
            .min()
            .alias("ib_high_ts"),
            pl.col(time_col)
            .filter(pl.col("Low") == pl.col("Low").min())
            .min()
            .alias("ib_low_ts"),
            pl.len().alias("n_ib"),
            pl.col("session_end").first(),
        )
        .with_columns((pl.col("ib_high") - pl.col("ib_low")).alias("ib_width"))
        .with_columns((pl.col("ib_high") - pl.col("ib_low") <= 0).alias("ib_degenerate"))
        .sort("anchor_ts")
    )
    return ib


def infer_bar_minutes(df: pl.DataFrame, *, time_col: str = "OpenTime") -> int:
    """Modal positive spacing of ``time_col``, in whole minutes.

    Used to *measure* level-source provenance instead of echoing a declared
    constant (QA-6 I-2). Raises if the frame is too short to infer.
    """
    if df.height < 2:
        raise RuntimeError("infer_bar_minutes: need >= 2 rows to infer bar spacing")
    diffs = (
        df.select(pl.col(time_col).sort().diff().dt.total_minutes().alias("d"))
        .drop_nulls()
        .filter(pl.col("d") > 0)
    )
    if diffs.height == 0:
        raise RuntimeError("infer_bar_minutes: no positive time spacing in frame")
    return int(diffs["d"].mode().min())


def _finalise_levels(parts: list[pl.DataFrame], src_bar_minutes: int) -> pl.DataFrame:
    """Concat level parts and stamp measured source provenance on every row."""
    if not parts:
        return pl.DataFrame()
    out = pl.concat(parts, how="vertical").drop_nulls("level_price")
    return out.with_columns(
        pl.lit(src_bar_minutes).cast(pl.Int32).alias("level_source_bar_minutes")
    )


def nearest_level_distance(
    close: float,
    levels: list[float],
) -> float | None:
    """Absolute distance from close to nearest level price; None if no levels."""
    if not levels:
        return None
    return min(abs(close - lv) for lv in levels)


def structural_levels_1m(
    bars_1m: pl.DataFrame,
    anchors: pl.DataFrame,
    ib_minutes: int,
    *,
    time_col: str = "OpenTime",
    kernel: str = "K-UNIFORM",
    only_anchors: set | None = None,
    include_profile: bool = True,
) -> pl.DataFrame:
    """Seven-kind structural levels from prior/current HTF sessions on **1m bars**.

    Families (SPDR-009 §3.1 / INFR-018 prior_session_levels):
      IB_HIGH/LOW of *this* session (from 1m bars in IB window);
      PRIOR_SESSION_HIGH/LOW, PRIOR_POC, PRIOR_VAH, PRIOR_VAL from the prior
      HTF session's 1m bars under K-UNIFORM.

    No LTF bar is used for level prices (D6.3 / assert_levels_from_1m).

    Parameters
    ----------
    only_anchors :
        If set, only emit levels for these consumer-session anchor timestamps
        (and only profile the *prior* sessions they need). Speeds W5 when
        candidates are sparse.
    include_profile :
        If False, skip POC/VA (extremes + IB only) — faster diagnostic path.
    """
    from xen.sigbar.profile import build_profile, poc_and_value_area

    if bars_1m.height == 0 or anchors.height == 0:
        return pl.DataFrame()

    # D6.3 provenance, measured not asserted: the source series must actually be
    # 1-minute (QA-6 I-2). Card ban 2 (per-level delta) is enforced where the
    # distribution actually happens — profile.build_profile calls
    # assert_no_per_level_delta with the real weight column; echoing a literal
    # here would re-create the defect QA-6 I-2 removed (QA-7 I7-8).
    src_bar_minutes = infer_bar_minutes(bars_1m, time_col=time_col)
    if src_bar_minutes != 1:
        raise RuntimeError(
            f"LEVELS FROM 1M: level source series has bar_minutes={src_bar_minutes}; "
            "D6.3 requires 1-minute bars for every level price and volume-at-price"
        )

    ib = session_ib_from_1m(bars_1m, anchors, ib_minutes, time_col=time_col)
    if ib.height:
        # A degenerate IB suppresses only the IB edges. Prior-session levels are
        # knowable at the open and independent of it (QA-7 I7-3).
        ib = ib.filter(~pl.col("ib_degenerate"))
    ranges = prior_htf_session_ranges(bars_1m, anchors, time_col=time_col)

    if only_anchors is not None:
        if ib.height:
            ib = ib.filter(pl.col("anchor_ts").is_in(list(only_anchors)))
        if ranges.height:
            ranges = ranges.filter(pl.col("anchor_ts").is_in(list(only_anchors)))

    # ``available_mins_since``: minutes after the session anchor at which the
    # level price is knowable. IB edges are knowable only once the IB
    # wall-clock completes (SPDR-009 §3.1); prior-session levels at the open.
    parts: list[pl.DataFrame] = []
    if ib.height:
        parts += [
            ib.select(
                "anchor_ts",
                pl.col("ib_high").alias("level_price"),
                pl.lit("IB_HIGH").alias("level_kind"),
                pl.lit(ib_minutes).alias("available_mins_since"),
                pl.col("ib_high_ts").alias("formed_ts"),
            ),
            ib.select(
                "anchor_ts",
                pl.col("ib_low").alias("level_price"),
                pl.lit("IB_LOW").alias("level_kind"),
                pl.lit(ib_minutes).alias("available_mins_since"),
                pl.col("ib_low_ts").alias("formed_ts"),
            ),
        ]

    # One asof-join assigns every 1m bar to its HTF session, then group once.
    joined = (
        bars_1m.sort(time_col)
        .join_asof(
            anchors.sort("anchor_ts"),
            left_on=time_col,
            right_on="anchor_ts",
            strategy="backward",
        )
        .drop_nulls("anchor_ts")
        .filter(pl.col(time_col) < pl.col("session_end"))
    )

    # Map consumer anchor → prior (source) session anchor
    sess = anchors.sort("anchor_ts")
    a_list = sess["anchor_ts"].to_list()
    consumer_to_src: dict = {
        a_list[i + 1]: a_list[i] for i in range(len(a_list) - 1)
    }
    targets = (
        [a for a in only_anchors if a in consumer_to_src]
        if only_anchors is not None
        else list(consumer_to_src.keys())
    )
    if not targets:
        out = _finalise_levels(parts, src_bar_minutes)
        if out.height and ranges.height:
            out = out.join(
                ranges.select("anchor_ts", "prior_session_range"),
                on="anchor_ts",
                how="left",
            )
        if out.height and ib.height:
            out = out.join(
                ib.select("anchor_ts", "ib_width"),
                on="anchor_ts",
                how="left",
            )
        return out

    src_needed = {consumer_to_src[c] for c in targets}
    # Extremes for prior sessions — vectorised group_by
    src_stats = (
        joined.filter(pl.col("anchor_ts").is_in(list(src_needed)))
        .group_by("anchor_ts")
        .agg(
            pl.col("High").max().alias("prior_high"),
            pl.col("Low").min().alias("prior_low"),
            pl.col(time_col)
            .filter(pl.col("High") == pl.col("High").max())
            .min()
            .alias("prior_high_ts"),
            pl.col(time_col)
            .filter(pl.col("Low") == pl.col("Low").min())
            .min()
            .alias("prior_low_ts"),
            pl.col(time_col).max().alias("prior_profile_ts"),
            pl.len().alias("n_1m"),
        )
    )
    # Rebuild as consumer-keyed rows (consumer→src is 1:1 on a sorted anchor list)
    src_to_consumer = {consumer_to_src[c]: c for c in targets}
    prior_rows: list[dict] = []
    for row in src_stats.iter_rows(named=True):
        src_a = row["anchor_ts"]
        consumer = src_to_consumer.get(src_a)
        if consumer is None or int(row["n_1m"]) < 2:
            continue
        rec: dict = {
            "anchor_ts": consumer,
            "prior_high": float(row["prior_high"]),
            "prior_low": float(row["prior_low"]),
            "prior_high_ts": row["prior_high_ts"],
            "prior_low_ts": row["prior_low_ts"],
            "prior_profile_ts": row["prior_profile_ts"],
            "prior_poc": None,
            "prior_val": None,
            "prior_vah": None,
        }
        if include_profile:
            win = joined.filter(pl.col("anchor_ts") == src_a)
            try:
                edges, prof = build_profile(win, kernel)
                poc, val, vah = poc_and_value_area(edges, prof)
                rec.update({"prior_poc": poc, "prior_val": val, "prior_vah": vah})
            except (ValueError, ZeroDivisionError):
                pass
        prior_rows.append(rec)

    if prior_rows:
        prior = pl.DataFrame(prior_rows)
        for col, kind, ts_col in (
            ("prior_high", "PRIOR_SESSION_HIGH", "prior_high_ts"),
            ("prior_low", "PRIOR_SESSION_LOW", "prior_low_ts"),
            ("prior_poc", "PRIOR_POC", "prior_profile_ts"),
            ("prior_val", "PRIOR_VAL", "prior_profile_ts"),
            ("prior_vah", "PRIOR_VAH", "prior_profile_ts"),
        ):
            parts.append(
                prior.select(
                    "anchor_ts",
                    pl.col(col).alias("level_price"),
                    pl.lit(kind).alias("level_kind"),
                    pl.lit(0).alias("available_mins_since"),
                    pl.col(ts_col).alias("formed_ts"),
                ).drop_nulls("level_price")
            )

    out = _finalise_levels(parts, src_bar_minutes)
    if out.height and ranges.height:
        out = out.join(
            ranges.select("anchor_ts", "prior_session_range"),
            on="anchor_ts",
            how="left",
        )
    if out.height and ib.height:
        out = out.join(
            ib.select("anchor_ts", "ib_width"),
            on="anchor_ts",
            how="left",
        )
    return out


def assert_associativity(
    bars_1m: pl.DataFrame,
    *,
    via: int = 5,
    target: int = 15,
    gap_days: set | None = None,
    time_col: str = "OpenTime",
) -> None:
    """A5: 1m→via→target price/volume equals 1m→target directly on COMPLETE nest.

    Compares OHLC and the signed sums on windows where the coarser bar is
    COMPLETE under both paths (strict nested retention).
    """
    gaps = set(gap_days) if gap_days is not None else design_gap_days(bars_1m, time_col=time_col)
    direct = aggregate_signed(bars_1m, target, gap_days=gaps, complete_only=True, time_col=time_col)
    mid = aggregate_signed(bars_1m, via, gap_days=gaps, complete_only=True, time_col=time_col)
    if mid.height == 0 or direct.height == 0:
        return
    # Re-aggregate COMPLETE mid bars to target (mid bars are already via-sized).
    nested = (
        mid.sort(time_col)
        .group_by_dynamic(time_col, every=f"{target}m", closed="left", label="left")
        .agg(
            pl.col("Open").first(),
            pl.col("High").max(),
            pl.col("Low").min(),
            pl.col("Close").last(),
            pl.col("Volume").sum(),
            pl.col("BuyVolume").sum(),
            pl.col("SellVolume").sum(),
            pl.col("SourceBars").sum().alias("SourceBars"),
            pl.len().alias("n_mid"),
        )
        .filter(pl.col("n_mid") == target // via)
        .filter(pl.col("SourceBars") == target)
    )
    # Align on OpenTime for COMPLETE direct bars.
    joined = direct.select(
        time_col, "Open", "High", "Low", "Close", "Volume", "BuyVolume", "SellVolume"
    ).join(
        nested.select(
            time_col,
            pl.col("Open").alias("o2"),
            pl.col("High").alias("h2"),
            pl.col("Low").alias("l2"),
            pl.col("Close").alias("c2"),
            pl.col("Volume").alias("v2"),
            pl.col("BuyVolume").alias("b2"),
            pl.col("SellVolume").alias("s2"),
        ),
        on=time_col,
        how="inner",
    )
    if joined.height == 0:
        return
    for a, b in (
        ("Open", "o2"),
        ("High", "h2"),
        ("Low", "l2"),
        ("Close", "c2"),
        ("Volume", "v2"),
        ("BuyVolume", "b2"),
        ("SellVolume", "s2"),
    ):
        diff = joined.select((pl.col(a) - pl.col(b)).abs().max()).item()
        if diff is not None and diff > 1e-6:
            raise RuntimeError(
                f"ASSOCIATIVITY: max |{a}−nested| = {diff} on 1m→{via}→{target} vs 1m→{target}"
            )
