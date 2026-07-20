"""A5 seasonal baselines — minute-of-day x day-of-week residual normalisation.

Source ``SIGNAL-SIGNED.md`` A5:

    "'high volume', 'large |Δ|', 'wide range', 'wide spread' are residuals
    against a fitted minute-of-day x day-of-week baseline per instrument (24/7
    venues have their own seasonal shape — regional session overlaps, funding
    timestamps), never flat rolling means and never raw numbers. **Delta gets
    its own baseline: |Δ| scales with volume, so normalize Δ/V and |Δ|
    separately.**"

Every threshold in the framework reads off these baselines, so they are Stage I
apparatus: fitted once on the DESIGN bank, frozen, hash-pinned, and never
refitted after a downstream result is seen.

Robust statistics throughout — median and MAD, not mean and SD. Intraday volume
is heavy-tailed and a single news minute would otherwise move the baseline for
that minute-of-week across the whole sample.
"""

from __future__ import annotations

import polars as pl

# The five metrics A5 names. `delta_abs` and `delta_ratio` are fitted
# SEPARATELY and deliberately — see the module docstring.
BASELINE_METRICS: tuple[str, ...] = (
    "volume",
    "range",
    "delta_abs",
    "delta_ratio",
    "spread",
)

# Cells with fewer than this many observations fall back to the day-of-week
# marginal (design.md §5). Disclosed per instrument as a fallback rate.
MIN_CELL_OBS = 8

# 1.4826 * MAD is the consistency-corrected robust SD estimate under normality.
_MAD_TO_SIGMA = 1.4826


MINUTES_PER_DAY = 1440
DAYS_PER_WEEK = 7
FULL_GRID_CELLS = MINUTES_PER_DAY * DAYS_PER_WEEK  # 10080


def _with_seasonal_keys(df: pl.DataFrame, time_col: str = "OpenTime") -> pl.DataFrame:
    """Attach minute-of-day (0-1439) and day-of-week (1-7) keys.

    The casts are load-bearing, not stylistic. Polars returns ``dt.hour()`` and
    ``dt.minute()`` as **Int8**, so ``hour * 60`` overflows for every hour >= 3
    and the sum wraps silently: 05:00 -> 44, 23:59 -> -97, collapsing the grid
    to 256 aliased buckets that pool ~5 unrelated times of day each. That
    reintroduces exactly the seasonal confound A5 exists to remove, and it
    surfaces downstream as uninterpretable results rather than as an exception.
    Caught at INFR-017 QA run 1 (Issue 1).
    """
    return df.with_columns(
        (
            pl.col(time_col).dt.hour().cast(pl.Int32) * 60
            + pl.col(time_col).dt.minute().cast(pl.Int32)
        ).alias("mod"),
        pl.col(time_col).dt.weekday().cast(pl.Int32).alias("dow"),
    )


def assert_seasonal_keys_valid(df: pl.DataFrame) -> None:
    """Raise unless the seasonal keys occupy their declared ranges.

    Guards the Int8-overflow class of defect at the point of use, so a silent
    aliasing can never reach a fitted baseline again.
    """
    mod_min, mod_max = df["mod"].min(), df["mod"].max()
    dow_min, dow_max = df["dow"].min(), df["dow"].max()
    if mod_min < 0 or mod_max > MINUTES_PER_DAY - 1:
        raise ValueError(
            f"minute-of-day key out of range [{mod_min}, {mod_max}] — expected [0, 1439] "
            "(integer overflow in the key expression?)"
        )
    if dow_min < 1 or dow_max > DAYS_PER_WEEK:
        raise ValueError(f"day-of-week key out of range [{dow_min}, {dow_max}] — expected [1, 7]")


def _full_grid() -> pl.DataFrame:
    """The complete 1440 x 7 cell index, so uncovered cells are explicit rows."""
    return pl.DataFrame(
        {"mod": list(range(MINUTES_PER_DAY))}
    ).join(pl.DataFrame({"dow": list(range(1, DAYS_PER_WEEK + 1))}), how="cross").select(
        pl.col("mod").cast(pl.Int32), pl.col("dow").cast(pl.Int32)
    )


def fit_seasonal_baseline(
    df: pl.DataFrame,
    metric: str,
    *,
    time_col: str = "OpenTime",
    min_cell_obs: int = MIN_CELL_OBS,
) -> pl.DataFrame:
    """Fit the minute-of-day x day-of-week robust baseline for one metric.

    Parameters
    ----------
    df :
        Bars for a single instrument, containing ``time_col`` and ``metric``.
    metric :
        Column to fit (one of :data:`BASELINE_METRICS`).
    time_col :
        Timestamp column; must be the bar open (naive UTC).
    min_cell_obs :
        Below this count a cell is marked ``SPARSE`` and inherits the
        day-of-week marginal instead of its own estimate.

    Returns
    -------
    polars.DataFrame
        One row per (``mod``, ``dow``) cell of the FULL 1440x7 grid, with
        ``loc``, ``scale``, ``n`` and ``sparse``. Cells with no observations are
        present with ``n = 0`` and the day-of-week fallback. ``scale`` is
        **null** (never zero) on a constant or empty cell, so residualising
        yields a null — an explicit "no usable baseline", not a divide-by-zero
        and not a fabricated finite value.
    """
    keyed = _with_seasonal_keys(df.select([time_col, metric]), time_col).drop_nulls(metric)
    if keyed.height:
        assert_seasonal_keys_valid(keyed)

    observed = keyed.group_by(["mod", "dow"]).agg(
        pl.col(metric).median().alias("loc_obs"),
        (pl.col(metric) - pl.col(metric).median()).abs().median().alias("mad_obs"),
        pl.len().alias("n"),
    )

    # Day-of-week marginal, used wherever a cell is too thin or has no data.
    marginal = keyed.group_by("dow").agg(
        pl.col(metric).median().alias("loc_m"),
        (pl.col(metric) - pl.col(metric).median()).abs().median().alias("mad_m"),
    )

    # Materialise the FULL grid so uncovered cells are explicit rows carrying the
    # fallback, not missing rows that silently left-join to null downstream.
    out = (
        _full_grid()
        .join(observed, on=["mod", "dow"], how="left")
        .join(marginal, on="dow", how="left")
        .with_columns(pl.col("n").fill_null(0))
        .with_columns((pl.col("n") < min_cell_obs).alias("sparse"))
        .with_columns(
            pl.when(pl.col("sparse")).then(pl.col("loc_m")).otherwise(pl.col("loc_obs")).alias("loc"),
            pl.when(pl.col("sparse")).then(pl.col("mad_m")).otherwise(pl.col("mad_obs")).alias("mad"),
        )
        .with_columns((pl.col("mad") * _MAD_TO_SIGMA).alias("scale"))
        .with_columns(
            # A constant or empty cell yields a null scale, which propagates as a
            # null residual — an explicit "no usable baseline here", never a
            # divide-by-zero and never a fabricated finite residual.
            pl.when(pl.col("scale") > 0)
            .then(pl.col("scale"))
            .otherwise(pl.lit(None))
            .alias("scale")
        )
        .select(["mod", "dow", "loc", "scale", "n", "sparse"])
        .sort(["dow", "mod"])
    )
    if out.height != FULL_GRID_CELLS:
        raise RuntimeError(
            f"seasonal grid has {out.height} cells, expected {FULL_GRID_CELLS}"
        )
    return out.with_columns(pl.lit(metric).alias("metric"))


def residualise(
    df: pl.DataFrame,
    baseline: pl.DataFrame,
    metric: str,
    *,
    time_col: str = "OpenTime",
) -> pl.DataFrame:
    """Convert a raw metric to its seasonal residual: ``(x - loc) / scale``.

    This is the only sanctioned way to say "high volume" / "large |Δ|" / "wide
    spread" in this family (A5). A raw threshold on any of these columns is a
    design error — every seasonal peak would read climactic on schedule.

    Parameters
    ----------
    df :
        Bars containing ``time_col`` and ``metric``.
    baseline :
        Output of :func:`fit_seasonal_baseline` for the same metric+instrument.
    metric :
        Column to residualise.

    Returns
    -------
    polars.DataFrame
        ``df`` plus ``<metric>_resid``. Null where the cell has no usable scale.
    """
    bl = baseline.filter(pl.col("metric") == metric).select(["mod", "dow", "loc", "scale"])
    return (
        _with_seasonal_keys(df, time_col)
        .join(bl, on=["mod", "dow"], how="left")
        .with_columns(((pl.col(metric) - pl.col("loc")) / pl.col("scale")).alias(f"{metric}_resid"))
        .drop(["mod", "dow", "loc", "scale"])
    )
