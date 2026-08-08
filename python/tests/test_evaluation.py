"""Tests for the xen.evaluation toolbox (INFR-001 WS-7; INFR-022 zero-cost + PSR)."""
from __future__ import annotations

import numpy as np
import pytest

import xen.evaluation as evaluation
from xen.adjudication import MultiLegSeries
from xen.evaluation import (
    ZERO_COST_DISCLOSURE,
    assert_zero_cost,
    block_bootstrap_ci,
    block_sensitivity,
    collapse_fraction,
    exposure_metrics,
    psr,
    psr_row,
    split_by,
    trimmed_mean,
    zero_cost_caveat,
)
from xen.evaluation_cost_legacy import (
    bybit_round_trip_cost_bps,
    count_bybit_funding_stamps,
    t1_round_trip_spread_bps,
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


def test_mde_and_cost_sensitivity_retired() -> None:
    """INFR-022 L-63: MDE / powered_label / cost_sensitivity removed from live evaluation."""
    assert not hasattr(evaluation, "mde")
    assert not hasattr(evaluation, "powered_label")
    assert not hasattr(evaluation, "cost_sensitivity")
    # moved to the archived legacy module (never callable from a live path)
    import xen.evaluation_cost_legacy as legacy
    assert hasattr(legacy, "round_trip_cost_bps")
    assert hasattr(legacy, "FTMO_COSTS")


# --------------------------------------------------------------------------- #
# Zero-cost model (INFR-022 directive 1)
# --------------------------------------------------------------------------- #
def test_zero_cost_disclosure_dict_and_caveat() -> None:
    assert ZERO_COST_DISCLOSURE["cost_model"] == "NO_COST_CHARGED"
    assert ZERO_COST_DISCLOSURE["spread"] == "not modeled"
    assert "prohibited_claims" in ZERO_COST_DISCLOSURE
    caveat = zero_cost_caveat()
    assert "ZERO-COST-DISCLOSURE" in caveat
    assert "cost_model: NO_COST_CHARGED" in caveat
    assert "tradable" in caveat and "deployable" in caveat


def test_assert_zero_cost_accepts_inert_pins() -> None:
    assert_zero_cost(cost_bps=0.0)
    assert_zero_cost(cost_bps=None, charge_costs=False, spread_bps=0)
    assert_zero_cost()  # no cost params at all


def test_assert_zero_cost_refuses_nonzero() -> None:
    for bad in (1.0, 2.5, True):
        with pytest.raises(ValueError, match="zero-cost model violated"):
            assert_zero_cost(cost_bps=bad)
    with pytest.raises(ValueError, match="zero-cost"):
        assert_zero_cost(charge_costs=True)


# --------------------------------------------------------------------------- #
# PSR (INFR-022 directive 4)
# --------------------------------------------------------------------------- #
def test_psr_normal_series_matches_analytic() -> None:
    """skew≈0, kurt≈3 → denom≈1 → PSR ≈ Φ(√(n−1)·SR̂)."""
    import math
    rng = np.random.default_rng(11)
    x = rng.normal(0.5, 1.0, size=250)  # SR̂ = 0.5
    out = psr(x)
    sr_hat = float(np.mean(x) / np.std(x))
    expected = 0.5 * (1 + math.erf(np.sqrt(249) * sr_hat / np.sqrt(2)))
    assert out["psr"] == pytest.approx(expected, abs=0.01)
    assert out["n"] == 250
    assert out["sr_hat"] == pytest.approx(sr_hat, abs=1e-12)


def test_psr_n_lt_2_is_nan_with_n_stated() -> None:
    for x in (np.array([]), np.array([3.0]), np.array([np.nan, 1.0])):
        out = psr(x)
        assert np.isnan(out["psr"])
        assert out["n"] == len(x)


def test_psr_skew_kurt_correction_sign() -> None:
    """Negative skew lowers PSR; excess kurtosis lowers PSR (same SR̂)."""
    rng = np.random.default_rng(13)
    n = 120
    base = rng.normal(0.25, 1.0, n)  # modest SR̂ so PSR is not saturated at 1
    # left-skewed variant: mirror the negative tail
    left_skew = base.copy()
    left_skew[base < 0] *= 4.0
    # heavy-tailed variant
    heavy = rng.normal(0.25, 1.0, n)
    heavy[::7] *= 5.0
    p_base = psr(base)
    p_left = psr(left_skew)
    p_heavy = psr(heavy)
    assert p_base["psr"] < 1.0
    assert p_left["skew"] < 0.0
    assert p_heavy["kurt"] > 3.0
    # both corrections reduce PSR below the near-normal base
    assert p_left["psr"] < p_base["psr"]
    assert p_heavy["psr"] < p_base["psr"]


def test_psr_deterministic_and_same_series() -> None:
    rng = np.random.default_rng(17)
    x = rng.normal(0.3, 1.0, size=100)
    assert psr(x) == psr(x)
    # psr_row emits the pairing columns psr + psr_n on the same series
    row = psr_row(x)
    assert set(row) == {"psr", "psr_n"}
    assert row["psr_n"] == 100
    assert row["psr"] == psr(x)["psr"]


def test_psr_sr_star_override() -> None:
    rng = np.random.default_rng(19)
    x = rng.normal(0.4, 1.0, size=200)
    assert psr(x, sr_star=0.0)["psr"] > psr(x, sr_star=0.5)["psr"]


# --------------------------------------------------------------------------- #
# Legacy cost functions retained in the archived module (historical replay only)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("stress", [0.5, 1.0, 2.0])
def test_bybit_cost_components_reconcile_with_stress_applied_once(stress: float) -> None:
    result = bybit_round_trip_cost_bps(
        "BTCUSDT",
        50_000.0,
        liquidity="taker",
        funding_bps_per_8h=1.0,
        hold_hours=4.0,
        stress=stress,
    )

    assert result["fee_rt_bps"] == pytest.approx(11.0 * stress)
    assert result["spread_rt_bps"] is None
    assert result["funding_rt_bps"] == pytest.approx(0.5 * stress)
    assert result["total_bps"] == pytest.approx(
        result["fee_rt_bps"]
        + result["funding_rt_bps"]
    )
    assert result["spread_cost_status"] == "UNAVAILABLE_NOT_CHARGED"
    assert result["cost_scope"] == "PARTIAL_FEES_FUNDING_ONLY"
    assert "understates" in result["spread_cost_caveat"]


@pytest.mark.parametrize("spread_bps", [-0.001, np.nan, np.inf, -np.inf])
def test_t1_round_trip_spread_rejects_invalid_input(spread_bps: float) -> None:
    with pytest.raises(ValueError, match="spread_bps"):
        t1_round_trip_spread_bps("BTCUSDT", spread_bps)


@pytest.mark.parametrize(
    ("entry_time", "exit_time", "expected"),
    [
        ("2026-07-22T04:00:00Z", "2026-07-22T08:00:00Z", 1),
        ("2026-07-22T06:00:00Z", "2026-07-22T10:00:00Z", 1),
        ("2026-07-22T08:00:00Z", "2026-07-22T12:00:00Z", 0),
        ("2026-07-22T22:00:00Z", "2026-07-23T02:00:00Z", 1),
    ],
)
def test_count_bybit_funding_stamps_for_fixed_four_hour_episode(
    entry_time: str,
    exit_time: str,
    expected: int,
) -> None:
    assert hasattr(evaluation, "count_bybit_funding_stamps") is False
    counter = count_bybit_funding_stamps
    assert counter(entry_time, exit_time) == expected


@pytest.mark.parametrize(
    ("entry_time", "exit_time", "expected_funding"),
    [
        ("2026-07-22T04:00:00Z", "2026-07-22T08:00:00Z", 1.0),
        ("2026-07-22T08:00:00Z", "2026-07-22T12:00:00Z", 0.0),
    ],
)
def test_bybit_cost_uses_discrete_funding_stamps_for_four_hour_episode(
    entry_time: str,
    exit_time: str,
    expected_funding: float,
) -> None:
    stamps = count_bybit_funding_stamps(entry_time, exit_time)
    result = bybit_round_trip_cost_bps(
        "BTCUSDT",
        50_000.0,
        liquidity="taker",
        funding_bps_per_8h=1.0,
        hold_hours=4.0,
        funding_stamps=stamps,
    )

    assert result["funding_rt_bps"] == pytest.approx(expected_funding)
    assert result["funding_method"] == "DISCRETE_STAMPS"


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


def test_bybit_round_trip_refuses_to_charge_spread() -> None:
    """Programme-wide policy: spread is never charged, and a caller may not opt back in."""
    with pytest.raises(ValueError, match="spread cost is not charged programme-wide"):
        bybit_round_trip_cost_bps(
            "BTCUSDT", 50_000.0, liquidity="taker", spread_bps=5.0,
        )


def test_bybit_round_trip_scope_is_always_partial() -> None:
    out = bybit_round_trip_cost_bps(
        "BTCUSDT", 50_000.0, liquidity="taker", funding_bps_per_8h=1.0, funding_stamps=1,
    )
    assert out["spread_rt_bps"] is None
    assert out["spread_cost_status"] == "UNAVAILABLE_NOT_CHARGED"
    assert out["cost_scope"] == "PARTIAL_FEES_FUNDING_ONLY"
    assert "understates total cost" in out["spread_cost_caveat"]
    assert out["total_bps"] == 12.0  # 11.0 fees + 1.0 funding, no spread
