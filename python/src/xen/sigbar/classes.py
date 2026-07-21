"""§2.3 signed effort-vs-result classes and their clustering test (HYP-I4 exit 2).

Source ``SIGNAL-SIGNED.md`` §2.3: *"volume = effort size; delta = effort
direction; range and close = result."* Each class has an unsigned base
(detectable from V alone) and a signed refinement (from Δ) that supplies the
direction which previously had to be inferred.

Every threshold is a **residual against the frozen A5 baselines**, never a raw
number (A5, and the item's hard constraints). A raw "high volume" cut would
read every seasonal peak as climactic on schedule — which is precisely the
confound the baselines exist to remove.

The percentile levels are **derived from the DESIGN-bank residual distribution
per symbol**, not asserted, and the realised residual values are written into
the pin so the thresholds are reproducible and auditable (L-24 F06 discipline).

This module classifies and locates. It never evaluates what happens next: a
forward outcome of any class is a signal read (S9/S10/S11), belongs to
checkpoint-015 Phase 6, and computing it here would breach the item's scope
fence and make Stage II unattributable.
"""

from __future__ import annotations

import numpy as np
import polars as pl

#: Percentile levels defining "high" and "low" on a residual distribution.
HIGH_PCTL = 0.90
LOW_PCTL = 0.10

CLASSES: tuple[str, ...] = (
    "ABSORPTION",
    "DRIVE",
    "DRIVE_WARNING_PRINT",
    "DRY_UP",
    "BLOWOFF",
    "VACUUM_RUN",
)

#: Located classes — the ones whose mechanism predicts proximity to structure.
#: DRY_UP is deliberately excluded FROM THE CLUSTERING TEST (it is still
#: detected and counted): source §2.3 defines it by a *trend* in effort across
#: bars, not by a location, so a clustering claim about it would test something
#: the mechanism does not assert.
LOCATED_CLASSES: tuple[str, ...] = ("ABSORPTION", "BLOWOFF", "VACUUM_RUN")

#: Consecutive bars DRY_UP inspects. Three is the source's own "1-3 bars" scale
#: and the shortest window in which "falling, and falling faster" is defined.
DRYUP_BARS = 3


def derive_thresholds(resid: pl.DataFrame, metrics: tuple[str, ...]) -> dict[str, dict[str, float]]:
    """Per-symbol residual values at the declared percentile levels.

    Returns
    -------
    dict
        ``{metric: {"high": value, "low": value, "n": count}}`` — the realised
        cut points, which go into the pin alongside the percentile levels so the
        thresholds can be re-derived rather than trusted.
    """
    out: dict[str, dict[str, float]] = {}
    for m in metrics:
        col = f"{m}_resid"
        if col not in resid.columns:
            continue
        s = resid[col].drop_nulls()
        if s.len() == 0:
            continue
        row = {
            "high": float(s.quantile(HIGH_PCTL)),
            "low": float(s.quantile(LOW_PCTL)),
            "n": s.len(),
            "high_pctl": HIGH_PCTL,
            "low_pctl": LOW_PCTL,
            "applied_to": f"{col} (signed)",
        }
        if m == "delta_ratio":
            # BLOWOFF tests EXTREME ONE-SIDED delta, so it reads |Δ/V| — both
            # tails, either side winning. The cut must therefore be the p90 of
            # the ABSOLUTE residual; pinning the signed p90 while the code
            # compares |resid| against it would make the threshold impossible to
            # re-derive from the pin (QA run 1, I-26).
            a = s.abs()
            row["abs_high"] = float(a.quantile(HIGH_PCTL))
            row["applied_to"] = (
                f"{col}: signed high/low for direction; abs_high = p{int(HIGH_PCTL*100)} of "
                f"|{col}| and is the value BLOWOFF actually compares against"
            )
        out[m] = row
    return out


def classify(bars: pl.DataFrame, th: dict[str, dict[str, float]]) -> pl.DataFrame:
    """Tag each bar with its §2.3 class, or null.

    Parameters
    ----------
    bars :
        Bars carrying ``volume_resid``, ``range_resid``, ``delta_abs_resid``,
        ``delta_ratio_resid`` (from the frozen A5 baselines) plus OHLC and
        ``Delta``.
    th :
        Output of :func:`derive_thresholds` for this symbol.

    Returns
    -------
    polars.DataFrame
        ``bars`` plus a ``sig_class`` column. Classes are evaluated in a fixed
        precedence order so a bar carries exactly one label; the order follows
        the source's own specificity (a Blowoff is a Drive with an extra
        condition, so Blowoff is tested first).
    """
    need = ("volume", "range", "delta_abs", "delta_ratio")
    missing = [m for m in need if m not in th]
    if missing:
        raise RuntimeError(f"missing derived thresholds for {missing}; cannot classify")

    v_hi, v_lo = th["volume"]["high"], th["volume"]["low"]
    r_hi, r_lo = th["range"]["high"], th["range"]["low"]
    d_hi = th["delta_abs"]["high"]
    # The pinned ABSOLUTE cut — matches what the BLOWOFF branch compares (I-26).
    dr_hi = th["delta_ratio"].get("abs_high", th["delta_ratio"]["high"])

    body_up = pl.col("Close") >= pl.col("Open")
    # "close near extreme" — within the top/bottom 20% of the bar's own range.
    rng = pl.col("High") - pl.col("Low")
    close_pos = pl.when(rng > 0).then((pl.col("Close") - pl.col("Low")) / rng).otherwise(0.5)
    at_extreme = (close_pos >= 0.8) | (close_pos <= 0.2)
    delta_agrees = (
        (body_up & (pl.col("Delta") > 0)) | ((~body_up) & (pl.col("Delta") < 0))
    )

    # DRY-UP's multi-bar precondition, computed before the single-bar chain so the
    # when/then ladder stays one expression. Window = DRYUP_BARS consecutive bars
    # inside the same session, all closing the same way, with both residual series
    # falling and |Δ| falling at least as fast as volume.
    same_dir = (pl.col("Close") - pl.col("Open")).sign()
    dv = pl.col("volume_resid") - pl.col("volume_resid").shift(1)
    dd = pl.col("delta_abs_resid") - pl.col("delta_abs_resid").shift(1)
    dryup = (
        (same_dir != 0)
        & (same_dir == same_dir.shift(1))
        & (same_dir == same_dir.shift(2))
        & (dv < 0)
        & (dv.shift(1) < 0)
        & (dd < 0)
        & (dd.shift(1) < 0)
        & (dd <= dv)  # |delta| shrinking at least as fast as volume
    )
    if "anchor_ts" in bars.columns:
        dryup = dryup.over("anchor_ts")  # never straddle a session boundary

    return bars.with_columns(dryup.fill_null(False).alias("_dryup_ok")).with_columns(
        pl.when(
            # BLOWOFF — V and range at extreme percentiles with extreme one-sided
            # delta. Location (the §2.4 extension qualifier) disambiguates it
            # from DRIVE downstream; here the print itself is tagged.
            (pl.col("volume_resid") >= v_hi)
            & (pl.col("range_resid") >= r_hi)
            & (pl.col("delta_abs_resid") >= d_hi)
            & (pl.col("delta_ratio_resid").abs() >= dr_hi)
        )
        .then(pl.lit("BLOWOFF"))
        .when(
            # ABSORPTION — heavy measured aggression, no result.
            (pl.col("volume_resid") >= v_hi)
            & (pl.col("range_resid") <= r_lo)
            & (pl.col("delta_abs_resid") >= d_hi)
        )
        .then(pl.lit("ABSORPTION"))
        .when(
            # DRIVE — effort and result agree, and the SIGN agrees too.
            (pl.col("volume_resid") >= v_hi)
            & (pl.col("range_resid") >= r_hi)
            & at_extreme
            & delta_agrees
        )
        .then(pl.lit("DRIVE"))
        .when(
            # WARNING PRINT — result WITHOUT aggression: the same wide
            # directional bar whose delta OPPOSES its close. Source §2.3/S10
            # calls this passive repricing or a stop cascade, not a Drive.
            (pl.col("volume_resid") >= v_hi)
            & (pl.col("range_resid") >= r_hi)
            & at_extreme
            & (~delta_agrees)
        )
        .then(pl.lit("DRIVE_WARNING_PRINT"))
        .when(
            # VACUUM RUN — distance travelled on thin interest.
            (pl.col("range_resid") >= r_hi) & (pl.col("volume_resid") <= v_lo)
        )
        .then(pl.lit("VACUUM_RUN"))
        .when(
            # DRY-UP — the fuel gauge emptying while price coasts. Unlike every
            # other class this one is a TREND across bars, not a single-bar
            # signature: directional bars whose volume is falling and whose net
            # aggression is falling FASTER (source §2.3, "|Δ| shrinking faster
            # than V — each bar carries fewer net aggressors").
            #
            # Both legs are seasonal residuals, so "shrinking" means shrinking
            # against this minute-of-week's own norm, not against the clock.
            pl.col("_dryup_ok")
        )
        .then(pl.lit("DRY_UP"))
        .otherwise(None)
        .alias("sig_class")
    ).drop("_dryup_ok")


def structural_distance(
    events: pl.DataFrame, levels: pl.DataFrame, scale_col: str = "ib_width"
) -> pl.DataFrame:
    """Normalised distance from each event bar to its nearest structural level.

    The event bar is excluded from the level set it is scored against — a bar
    cannot be "near" a level it created, and including it would manufacture the
    clustering the test is meant to detect (design.md §2).

    Parameters
    ----------
    events :
        Bars with ``anchor_ts``, ``OpenTime``, ``Close`` and the scale column.
    levels :
        ``anchor_ts, level_price, level_kind, level_created_ts`` — IB edges,
        prior-session VA edges and POC, prior-session extremes.
    scale_col :
        Divisor object for the normalised distance, stated per L-21.
    """
    j = events.join(levels, on="anchor_ts", how="inner").filter(
        # exclude any level this very bar created
        pl.col("level_created_ts").is_null() | (pl.col("level_created_ts") != pl.col("OpenTime"))
    )
    return (
        j.with_columns((pl.col("Close") - pl.col("level_price")).abs().alias("dist"))
        .group_by("anchor_ts", "OpenTime")
        .agg(
            pl.col("dist").min().alias("d_nearest"),
            pl.col(scale_col).first().alias("scale"),
            pl.col("level_kind").sort_by("dist").first().alias("nearest_kind"),
        )
        .with_columns(
            pl.when(pl.col("scale") > 0)
            .then(pl.col("d_nearest") / pl.col("scale"))
            .otherwise(None)
            .alias("d_norm")
        )
    )


#: Decile edges are taken from this many quantiles of the COMMON distribution.
_MATCH_QUANTILES = tuple(i / 10 for i in range(1, 10))


def residual_matched_control(
    all_bars: pl.DataFrame, event_bars: pl.DataFrame, *, seed: int, n_per_event: int = 1
) -> pl.DataFrame:
    """Sample non-event bars matched on volume and range residual deciles.

    The control holds the seasonal-residual regime FIXED and varies only class
    membership. That is what makes it non-degenerate: without the matching, the
    contrast would merely say "high-volume wide-range bars sit near structure",
    which is a property of activity, not of the class — exactly the confound
    that would make the §2.3 classes decorative.

    **The bins come from one COMMON distribution** (``all_bars``), and both arms
    are cut on those same edges. QA run 1 (I-3) found each population ranked
    against *itself*, which matches relative rank inside disjoint populations
    rather than residual values: class events sit in the upper tail of the full
    distribution, so event-decile 0 (the mildest class events) was paired with
    pool-decile 0 (the quietest ordinary bars) — opposite ends of the axis. The
    measured control then sat on the pool mean rather than the event mean, i.e.
    it was the unmatched pool, and the contrast reduced to "active bars vs quiet
    bars" — biased toward the conclusion the test is meant to interrogate.

    Parameters
    ----------
    all_bars :
        The session's bars, residualised and classified. Supplies the common
        binning distribution as well as the control pool.
    event_bars :
        The subset carrying the class under test.
    seed :
        Frozen; the draw is regenerable from ``(seed, session, class)``.
    n_per_event :
        Controls drawn per event.

    Returns
    -------
    polars.DataFrame
        The matched control bars. Empty if no stratum has a counterpart.
    """
    rng = np.random.default_rng(seed)

    def _edges(col: str) -> list[float]:
        s = all_bars[col].drop_nulls()
        if s.len() == 0:
            return []
        return [float(s.quantile(q)) for q in _MATCH_QUANTILES]

    def _binned(df: pl.DataFrame) -> pl.DataFrame:
        out = df
        for col, alias in (("volume_resid", "v_dec"), ("range_resid", "r_dec")):
            e = _edges(col)
            if not e:
                out = out.with_columns(pl.lit(0).alias(alias))
                continue
            expr = pl.lit(0)
            for i, cut in enumerate(e, start=1):
                expr = pl.when(pl.col(col) > cut).then(pl.lit(i)).otherwise(expr)
            out = out.with_columns(expr.alias(alias))
        return out

    pool = _binned(all_bars.filter(pl.col("sig_class").is_null()))
    ev = _binned(event_bars)

    picks: list[pl.DataFrame] = []
    for (vd, rd), grp in ev.group_by(["v_dec", "r_dec"]):
        cand = pool.filter((pl.col("v_dec") == vd) & (pl.col("r_dec") == rd))
        if cand.height == 0:
            continue
        k = min(grp.height * n_per_event, cand.height)
        idx = rng.choice(cand.height, size=k, replace=False)
        picks.append(cand[idx.tolist()])
    if not picks:
        return pool.head(0)
    return pl.concat(picks, how="vertical")


def match_quality(event_bars: pl.DataFrame, control_bars: pl.DataFrame) -> dict:
    """Measured balance of the matched arms — the control's own evidence.

    A control asserted to be matched must show it. Emitted alongside every
    clustering contrast so the operator can see the balance rather than trust it.
    """
    out: dict[str, float | int] = {"n_event": event_bars.height, "n_control": control_bars.height}
    for col in ("volume_resid", "range_resid"):
        if col in event_bars.columns and event_bars.height and control_bars.height:
            e = event_bars[col].drop_nulls().mean()
            c = control_bars[col].drop_nulls().mean()
            out[f"{col}_event_mean"] = float(e) if e is not None else float("nan")
            out[f"{col}_control_mean"] = float(c) if c is not None else float("nan")
            out[f"{col}_abs_gap"] = (
                abs(float(e) - float(c)) if e is not None and c is not None else float("nan")
            )
    return out
