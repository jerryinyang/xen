"""Regression tests for the A5 seasonal baseline keys (INFR-017).

The Int8-overflow defect these tests pin down was silent: it produced no
exception, self-consistent keys, and a plausible-looking artifact, while
collapsing the 1440-minute grid to 256 aliased buckets. Only an explicit
identity assertion catches that class of bug.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import polars as pl
import pytest

from xen.sigbar.baselines import (
    DAYS_PER_WEEK,
    FULL_GRID_CELLS,
    MINUTES_PER_DAY,
    _with_seasonal_keys,
    assert_seasonal_keys_valid,
    fit_seasonal_baseline,
)


def _synthetic_day(start: datetime, n_minutes: int = MINUTES_PER_DAY) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "OpenTime": [start + timedelta(minutes=i) for i in range(n_minutes)],
            "volume": [float(i % 97) for i in range(n_minutes)],
        }
    )


def test_minute_of_day_key_is_identity_over_a_full_day():
    """mod must equal the minute index 0..1439 — the direct overflow guard."""
    keyed = _with_seasonal_keys(_synthetic_day(datetime(2023, 1, 2)))
    assert keyed["mod"].to_list() == list(range(MINUTES_PER_DAY))


def test_known_overflow_points_are_correct():
    """The exact timestamps that wrapped under Int8 arithmetic."""
    df = pl.DataFrame(
        {
            "OpenTime": [
                datetime(2023, 1, 2, 2, 0),
                datetime(2023, 1, 2, 3, 0),
                datetime(2023, 1, 2, 5, 0),
                datetime(2023, 1, 2, 12, 30),
                datetime(2023, 1, 2, 23, 59),
            ],
            "volume": [1.0] * 5,
        }
    )
    assert _with_seasonal_keys(df)["mod"].to_list() == [120, 180, 300, 750, 1439]


def test_keys_span_full_range_over_a_week():
    keyed = _with_seasonal_keys(_synthetic_day(datetime(2023, 1, 2), MINUTES_PER_DAY * 7))
    assert keyed["mod"].n_unique() == MINUTES_PER_DAY
    assert sorted(keyed["dow"].unique().to_list()) == list(range(1, DAYS_PER_WEEK + 1))
    assert_seasonal_keys_valid(keyed)


def test_key_validator_rejects_out_of_range():
    bad = pl.DataFrame({"mod": [-97, 44], "dow": [1, 1]})
    with pytest.raises(ValueError, match="minute-of-day key out of range"):
        assert_seasonal_keys_valid(bad)


def test_fit_materialises_the_full_grid_including_uncovered_cells():
    """Uncovered cells must be explicit rows with n=0, not missing rows."""
    baseline = fit_seasonal_baseline(_synthetic_day(datetime(2023, 1, 2)), "volume")
    assert baseline.height == FULL_GRID_CELLS
    assert int((baseline["n"] > 0).sum()) == MINUTES_PER_DAY  # one weekday covered
    assert bool(baseline.filter(pl.col("n") == 0)["sparse"].all())
