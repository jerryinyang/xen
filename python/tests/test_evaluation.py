"""Tests for the xen.evaluation toolbox (INFR-001 WS-7)."""
from __future__ import annotations

import numpy as np
import pytest

from xen.adjudication import MultiLegSeries
from xen.evaluation import (
    block_bootstrap_ci,
    block_sensitivity,
    collapse_fraction,
    cost_sensitivity,
    exposure_metrics,
    mde,
    powered_label,
    split_by,
    trimmed_mean,
)


def test_block_bootstrap_ci_covers_known_mean() -> None:
    rng = np.random.default_rng(1)
    x = rng.normal(5.0, 1.0, size=400)
    r = block_bootstrap_ci(x, seed=1)
    assert r["ci"][0] < x.mean() < r["ci"][1]
    assert r["stat"] == pytest.approx(x.mean())
    half_width = (r["ci"][1] - r["ci"][0]) / 2
    assert 0.05 < half_width < 0.3  # ~2*sigma/sqrt(n) scale, not degenerate


def test_small_n_ci_is_not_zero_width() -> None:
    # INFR-004 F1: n <= block+1 previously collapsed to ci=[stat, stat] (false certainty).
    x = np.array([1.0, 2.0, 3.0, 4.0])   # n=4 < DEFAULT_BLOCK+1=6
    r = block_bootstrap_ci(x, seed=1)
    assert r["ci"][1] - r["ci"][0] > 0.0
    assert r["block"] <= r["n"] - 1
    # block explicitly >= n must also resample, not rotate the whole series
    r2 = block_bootstrap_ci(x, block=10, seed=1)
    assert r2["ci"][1] - r2["ci"][0] > 0.0


def test_seed_battery_reports_mc_band() -> None:
    # INFR-004 F2: per-seed spread of each CI bound is disclosed.
    rng = np.random.default_rng(7)
    x = rng.normal(0.0, 3.0, size=80)
    r = block_bootstrap_ci(x, seed=7)
    assert r["ci_low_seed_range"][0] <= r["ci"][0] <= r["ci_low_seed_range"][1]
    assert r["ci_high_seed_range"][0] <= r["ci"][1] <= r["ci_high_seed_range"][1]


def test_block_sensitivity_curve() -> None:
    # INFR-004 F3: one row per requested block, effective block reported.
    rng = np.random.default_rng(8)
    x = rng.normal(2.0, 1.0, size=200)
    curve = block_sensitivity(x, [10, 20, 40], seed=8)
    assert [row["block_req"] for row in curve] == [10, 20, 40]
    assert all(row["ci"][0] < x.mean() < row["ci"][1] for row in curve)


def test_trimmed_mean_robust_to_outlier() -> None:
    # INFR-004 F4: trimmed mean ignores a planted extreme the plain mean chases.
    x = np.concatenate([np.zeros(20), np.array([1000.0])])
    assert abs(trimmed_mean(x)) < abs(x.mean())
    r = block_bootstrap_ci(x, trimmed_mean, seed=1)
    assert r["stat"] == pytest.approx(trimmed_mean(x))


def test_mde_and_powered_label() -> None:
    rng = np.random.default_rng(2)
    x = rng.normal(0.0, 10.0, size=50)
    m = mde(x, seed=2)
    assert m > 0
    assert powered_label(x, plausible_effect=m * 2, seed=2)["powered"]
    assert not powered_label(x, plausible_effect=m / 10, seed=2)["powered"]


def test_cost_sensitivity_monotone() -> None:
    rng = np.random.default_rng(3)
    gross = rng.normal(10.0, 5.0, size=300)
    curve = cost_sensitivity(gross, [0.0, 5.0, 10.0], seed=3)
    stats = [row["stat"] for row in curve]
    assert stats[0] > stats[1] > stats[2]
    assert stats[0] - stats[2] == pytest.approx(10.0)


def test_collapse_fraction() -> None:
    assert collapse_fraction(10.0, 5.0) == pytest.approx(0.5)
    assert np.isnan(collapse_fraction(0.0, 5.0))


def test_split_by_has_pooled_disclosure() -> None:
    v = np.array([1.0, 2.0, 3.0, 10.0, 11.0, 12.0])
    labs = np.array([2021, 2021, 2021, 2022, 2022, 2022])
    r = split_by(v, labs, block=2)
    assert set(r) == {"2021", "2022", "_pooled_disclosure_only"}
    assert r["2022"]["stat"] > r["2021"]["stat"]


def test_exposure_metrics_normalizations() -> None:
    times = np.array([np.datetime64("2021-01-01") + np.timedelta64(4 * i, "h")
                      for i in range(2190)])  # one year of 4h bars
    net = np.zeros(2190)
    net[:1095] = 1.0                      # +1 bp/bar while exposed, first half-year
    open_legs = np.zeros(2190, dtype=np.int64)
    open_legs[:1095] = 4                  # 4 legs deployed half the time
    s = MultiLegSeries(times, net.copy(), net, open_legs, 100, 0, 0.0)
    opens = np.full(2190, 100.0)          # flat B&H
    m = exposure_metrics(s, real_open=opens)
    assert m["occupancy"] == pytest.approx(0.5)
    assert m["avg_exposure_legs_all_bars"] == pytest.approx(2.0)
    assert m["peak_exposure_legs"] == 4
    # unit-notional return divided across normalizations
    assert m["ann_return_on_avg_exposure"] == pytest.approx(
        m["ann_return_on_unit_notional"] / 2.0)
    assert m["ann_return_on_peak_exposure"] == pytest.approx(
        m["ann_return_on_unit_notional"] / 4.0)
    assert m["bh_exposure_time_matched_return"] == pytest.approx(0.0)
