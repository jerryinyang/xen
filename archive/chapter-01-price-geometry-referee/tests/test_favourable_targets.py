"""Numeric anchors for the EXP-056 favourable-target geometry module.

These are the unit/smoke tests the EXP-056 pre-execution review referenced but
that were never committed (adversarial finding F02). They give the *un-anchored*
new code an external, hand-computed reference, separate from the EXP-053 BENCH
reconciliation (which only covers the benchmark variant). Each assertion is
hand-derivable from the inputs — no value is copied back from the implementation.
"""
from __future__ import annotations

import numpy as np
import pytest

from xen.favourable_targets import (
    VP_MAX_BINS,
    barriers_from_distance,
    barriers_from_fav_level,
    paired_median_contrast_ci,
    trailing_magnitude_distance,
    volume_profile_levels,
)


# --------------------------------------------------------------------------- #
# Volume profile — POC / 70% value area / VAL / VAH (hand-computed)
# --------------------------------------------------------------------------- #
def test_vp_single_bin_bars_known_poc_and_value_area() -> None:
    # Three bars, each spanning exactly one width-1 bin: [0,1]=10, [1,2]=50,
    # [2,3]=20. lo=0, hi=3, n_bins=3, bin_vol=[10,50,20], total=80.
    low = np.array([0.0, 1.0, 2.0])
    high = np.array([1.0, 2.0, 3.0])
    vol = np.array([10.0, 50.0, 20.0])

    lv = volume_profile_levels(low, high, vol, bin_width=1.0)

    assert lv.defined
    assert lv.n_bins == 3
    assert lv.total_volume == pytest.approx(80.0)
    # POC = centre of the max-volume bin (bin 1): 0 + (1 + 0.5)*1 = 1.5.
    assert lv.poc == pytest.approx(1.5)
    # 70% of 80 = 56. POC bin (50) < 56 → annex the larger neighbour (bin 2, 20)
    # → cum 70 ≥ 56. VA = bins 1..2: VAL = 1*1 = 1.0, VAH = (2+1)*1 = 3.0.
    assert lv.val == pytest.approx(1.0)
    assert lv.vah == pytest.approx(3.0)


def test_vp_uniform_split_and_lowest_price_tie_break() -> None:
    # One bar spanning [0,2] with volume 100 splits uniformly into two width-1
    # bins → [50, 50]. Tie on the max → POC is the LOWEST-price bin (bin 0).
    lv = volume_profile_levels(
        np.array([0.0]), np.array([2.0]), np.array([100.0]), bin_width=1.0)

    assert lv.defined and lv.n_bins == 2
    assert lv.poc == pytest.approx(0.5)        # lowest-index max bin
    # 70% of 100 = 70. POC bin (50) < 70 → annex bin 1 → cum 100. VA spans both.
    assert lv.val == pytest.approx(0.0)
    assert lv.vah == pytest.approx(2.0)
    assert lv.total_volume == pytest.approx(100.0)


def test_vp_conserves_total_volume_with_overlapping_bars() -> None:
    # Overlapping, multi-bin bars: binned volume must equal the input total
    # (the conservation invariant the module asserts internally).
    low = np.array([0.0, 0.5, 1.3])
    high = np.array([2.0, 1.5, 3.7])
    vol = np.array([100.0, 40.0, 25.0])

    lv = volume_profile_levels(low, high, vol, bin_width=0.3)

    assert lv.defined
    assert lv.total_volume == pytest.approx(165.0)


@pytest.mark.parametrize(
    "low, high, vol, bin_width",
    [
        (np.empty(0), np.empty(0), np.empty(0), 1.0),          # no bars
        (np.array([0.0]), np.array([1.0]), np.array([0.0]), 1.0),  # zero volume
        (np.array([0.0]), np.array([1.0]), np.array([5.0]), 0.0),  # bad width
    ],
)
def test_vp_undefined_cases(low, high, vol, bin_width) -> None:
    lv = volume_profile_levels(low, high, vol, bin_width=bin_width)
    assert not lv.defined
    assert np.isnan(lv.poc) and np.isnan(lv.val) and np.isnan(lv.vah)


def test_vp_max_bins_tripwire_raises() -> None:
    # span/bin_width far above VP_MAX_BINS must raise (defect tripwire, not run).
    with pytest.raises(ValueError, match="VP_MAX_BINS"):
        volume_profile_levels(
            np.array([0.0]), np.array([1.0]), np.array([10.0]),
            bin_width=1.0 / (VP_MAX_BINS + 10))


# --------------------------------------------------------------------------- #
# Trailing-magnitude distance (/MAGTARGET) — median of trailing W, strictly before
# --------------------------------------------------------------------------- #
def test_mag_median_of_trailing_window() -> None:
    confirm = np.array([10, 20, 30, 40, 50], dtype=np.int64)
    magnitude = np.array([2.0, 4.0, 6.0, 8.0, 10.0])
    # entry at 45: moves with ConfirmTime < 45 are indices 0..3 (last = 40).
    # trailing W=2 → magnitudes [6, 8], median 7 → frac 0.5 → 3.5.
    dist, defined = trailing_magnitude_distance(
        np.array([45], dtype=np.int64), confirm, magnitude, window=2, frac=0.5)
    assert defined[0]
    assert dist[0] == pytest.approx(3.5)


def test_mag_strictly_before_entry_excludes_equal_timestamp() -> None:
    confirm = np.array([10, 20, 30, 40, 50], dtype=np.int64)
    magnitude = np.array([2.0, 4.0, 6.0, 8.0, 10.0])
    # entry exactly at 40: only moves at 10,20,30 are strictly before (last=30).
    # W=2 → magnitudes [4, 6], median 5 → frac 1.0 → 5.0.
    dist, defined = trailing_magnitude_distance(
        np.array([40], dtype=np.int64), confirm, magnitude, window=2, frac=1.0)
    assert defined[0]
    assert dist[0] == pytest.approx(5.0)


def test_mag_warmup_when_fewer_than_window_moves() -> None:
    confirm = np.array([10, 20, 30, 40], dtype=np.int64)
    magnitude = np.array([2.0, 4.0, 6.0, 8.0])
    # entry at 45: 4 moves strictly before, but W=5 → warmup (undefined, 0).
    dist, defined = trailing_magnitude_distance(
        np.array([45], dtype=np.int64), confirm, magnitude, window=5, frac=1.0)
    assert not defined[0]
    assert dist[0] == 0.0


# --------------------------------------------------------------------------- #
# Generalized 1:1 barriers — validity flags and adverse mirroring
# --------------------------------------------------------------------------- #
def test_barriers_from_distance_mirrors_adverse_1to1() -> None:
    close = np.array([100.0, 100.0])
    rd = np.array([1, -1], dtype=np.int64)
    dist = np.array([2.0, 3.0])

    bar = barriers_from_distance(close, rd, dist)

    assert bar["fav"].tolist() == [102.0, 97.0]     # C + rd*dist
    assert bar["adv"].tolist() == [98.0, 103.0]     # C - rd*dist (1:1)
    assert bar["valid"].tolist() == [True, True]


def test_barriers_from_distance_invalid_nonpositive() -> None:
    bar = barriers_from_distance(
        np.array([100.0, 100.0]), np.array([1, 1], dtype=np.int64),
        np.array([0.0, -1.0]))
    assert bar["valid"].tolist() == [False, False]


def test_barriers_from_fav_level_signed_side_and_nan() -> None:
    close = np.array([100.0, 100.0, 100.0])
    rd = np.array([1, 1, 1], dtype=np.int64)
    level = np.array([105.0, 95.0, np.nan])         # ahead / behind / undefined

    bar = barriers_from_fav_level(close, rd, level)

    assert bar["fav_dist"][0] == pytest.approx(5.0)
    assert bar["adv"][0] == pytest.approx(95.0)     # C - rd*fav_dist
    assert bar["valid"].tolist() == [True, False, False]


# --------------------------------------------------------------------------- #
# Paired median contrast bootstrap — exact recovery of a constant offset
# --------------------------------------------------------------------------- #
def test_paired_contrast_recovers_constant_offset_exactly() -> None:
    # variant = bench + 1.0 elementwise. The median difference is shift-invariant
    # under ANY shared resample, so every bootstrap delta is exactly 1.0 and all
    # three CI bounds collapse to the offset.
    rng = np.random.default_rng(0)
    bench = np.linspace(-2.0, 3.0, 64)
    variant = bench + 1.0

    ci_low, ci_lo, ci_hi, block = paired_median_contrast_ci(variant, bench, rng)

    assert ci_low == pytest.approx(1.0)
    assert ci_lo == pytest.approx(1.0)
    assert ci_hi == pytest.approx(1.0)
    assert block == round(64 ** (1.0 / 3.0))        # block = round(m^(1/3)) = 4


def test_paired_contrast_sign_and_determinism() -> None:
    # A variant uniformly better than bench yields a strictly positive one-sided
    # lower bound; identical seeds reproduce identical bounds (determinism).
    bench = np.array([0.0, 0.1, -0.1, 0.2, -0.2, 0.3, -0.3, 0.05] * 5)
    variant = bench + 0.5
    a = paired_median_contrast_ci(variant, bench, np.random.default_rng(7))
    b = paired_median_contrast_ci(variant, bench, np.random.default_rng(7))

    assert a == b                                   # deterministic given the seed
    assert a[0] > 0.0                               # CI_low(delta) > 0


def test_paired_contrast_empty_returns_nan() -> None:
    ci = paired_median_contrast_ci(
        np.empty(0), np.empty(0), np.random.default_rng(1))
    assert all(np.isnan(x) for x in ci[:3])
    assert ci[3] == 1
