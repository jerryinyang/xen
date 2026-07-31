"""Contract and arm-lattice tests for xen.adaptive_management.

Binding design:
docs/experiments-docs/checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/
adaptive-management-design.md (sections 4-7).
"""

import pytest

from xen.adaptive_management.contracts import (
    Component,
    Device,
    NativeParameter,
    Orientation,
    build_management_lattice,
    build_native_lattice,
    materialise_crossed_arm,
    native_combination_pairs,
)

EXPERIMENTS = ("SPDR-021", "SPDR-022", "SPDR-023")


def test_lattice_keeps_sizing_out_of_exit_combinations():
    arms = build_management_lattice("SPDR-021")
    assert not any(
        a.device == Device.SIZE
        and a.combination_id
        and a.combination_id.startswith("DC_")
        for a in arms
    )


def test_all_adaptive_arms_name_a_fixed_comparator():
    for experiment_id in EXPERIMENTS:
        for arm in (*build_native_lattice(experiment_id), *build_management_lattice(experiment_id)):
            if arm.is_adaptive:
                assert arm.comparator_id.startswith("FIXED_")


def test_native_lattice_is_broad_but_bounded():
    breakout = build_native_lattice("SPDR-021")
    assert {a.parameter for a in breakout if a.combination_id is None and a.is_adaptive} == {
        NativeParameter.BREAKOUT_THRESHOLD,
        NativeParameter.PENDING_EXPIRY,
    }
    breach = build_native_lattice("SPDR-022")
    assert {a.parameter for a in breach if a.combination_id is None and a.is_adaptive} == {
        NativeParameter.BAND_Z,
        NativeParameter.BAND_H,
    }
    singles = [a for a in (*breakout, *breach) if a.combination_id is None and a.is_adaptive]
    assert all(a.orientation in {Orientation.DIRECT, Orientation.REVERSE} for a in singles)


def test_native_combinations_are_only_four_orientation_pairs_per_component():
    pairs = native_combination_pairs("SPDR-021", Component.RANGE_SCALE)
    assert pairs == {
        ("DIRECT", "DIRECT"),
        ("DIRECT", "REVERSE"),
        ("REVERSE", "DIRECT"),
        ("REVERSE", "REVERSE"),
    }


def test_native_and_management_grids_never_cross():
    assert not any(a.native_arm_id for a in build_management_lattice("SPDR-021"))
    with pytest.raises(ValueError, match="native.*management"):
        materialise_crossed_arm(
            build_native_lattice("SPDR-021")[0],
            build_management_lattice("SPDR-021")[0],
        )


def test_native_adaptive_configuration_counts():
    assert len([a for a in build_native_lattice("SPDR-021") if a.is_adaptive]) == 64
    assert len([a for a in build_native_lattice("SPDR-022") if a.is_adaptive]) == 128
    assert len([a for a in build_native_lattice("SPDR-023") if a.is_adaptive]) == 128


def test_every_component_receives_every_applicable_native_arm():
    arms = build_native_lattice("SPDR-021")
    for component in Component:
        singles = [
            a
            for a in arms
            if a.component == component and a.combination_id is None and a.is_adaptive
        ]
        assert {(a.parameter, a.orientation) for a in singles} == {
            (p, o)
            for p in (NativeParameter.BREAKOUT_THRESHOLD, NativeParameter.PENDING_EXPIRY)
            for o in Orientation
        }
        combos = [a for a in arms if a.component == component and a.combination_id is not None]
        assert len(combos) == 4


def test_native_lattice_carries_fixed_comparator_rows():
    fixed = [a for a in build_native_lattice("SPDR-021") if not a.is_adaptive]
    assert {a.native_arm_id for a in fixed} == {"FIXED_NATIVE_BREAKOUT"}


def test_management_lattice_component_device_coverage():
    arms = build_management_lattice("SPDR-021")
    adaptive = [a for a in arms if a.is_adaptive and a.combination_id is None]
    pairs = {(a.component, a.device) for a in adaptive}
    expected = {
        (Component.RANGE_SCALE, Device.TARGET),
        (Component.RANGE_SCALE, Device.STOP),
        (Component.RANGE_SCALE, Device.TRAIL),
        (Component.RANGE_SCALE, Device.SIZE),
        (Component.SWING_SCALE, Device.TARGET),
        (Component.SWING_SCALE, Device.STOP),
        (Component.SWING_GT_CUR, Device.TARGET),
        (Component.SWING_GT_CUR, Device.HOLD),
        (Component.TAIL_RISK, Device.TARGET),
        (Component.TAIL_RISK, Device.STOP),
        (Component.TAIL_RISK, Device.SIZE),
    }
    for state in (
        Component.LEVEL_NOW,
        Component.LEVEL_FORECAST_K4,
        Component.LEVEL_FORECAST_K12,
        Component.SHOCK,
    ):
        expected |= {
            (state, d)
            for d in (Device.TARGET, Device.STOP, Device.TRAIL, Device.HOLD, Device.SIZE)
        }
    assert pairs == expected


def test_only_declared_combinations_exist():
    arms = build_management_lattice("SPDR-021")
    component_combos = {
        a.combination_id for a in arms if a.combination_id and a.combination_id.startswith("CC_")
    }
    device_combos = {
        a.combination_id for a in arms if a.combination_id and a.combination_id.startswith("DC_")
    }
    assert component_combos == {
        "CC_RANGE_SCALE__LEVEL_NOW",
        "CC_RANGE_SCALE__LEVEL_FORECAST_K4",
        "CC_RANGE_SCALE__LEVEL_FORECAST_K12",
        "CC_SHOCK__LEVEL_NOW",
        "CC_RANGE_SCALE__SWING_GT_CUR",
    }
    assert device_combos == {
        "DC_TARGET_STOP",
        "DC_TRAIL_HOLD",
        "DC_TARGET_STOP_HOLD",
    }


def test_plain_fixed_management_baseline_exists():
    arms = build_management_lattice("SPDR-021")
    baseline = [a for a in arms if a.policy_id == "FIXED_BASELINE_PLAIN"]
    assert len(baseline) == 1
    assert not baseline[0].is_adaptive
    assert baseline[0].device == Device.NONE
    assert baseline[0].fixed_hold_bars == 1
    assert baseline[0].pending_expiry_bars == 2


def test_plain_baseline_freezes_each_experiments_real_hold():
    assert next(
        a for a in build_management_lattice("SPDR-022")
        if a.policy_id == "FIXED_BASELINE_PLAIN"
    ).fixed_hold_bars == 4
    assert next(
        a for a in build_management_lattice("SPDR-023")
        if a.policy_id == "FIXED_BASELINE_PLAIN"
    ).fixed_hold_bars == 4


def test_component_combinations_preserve_both_components_and_roles():
    arms = build_management_lattice("SPDR-021")
    combo = next(
        a for a in arms
        if a.combination_id == "CC_RANGE_SCALE__LEVEL_NOW"
        and a.device == Device.TARGET
    )
    assert combo.component == Component.RANGE_SCALE
    assert combo.adjustment_component == Component.LEVEL_NOW
    assert combo.component_role == "PRIMARY_NUMERIC_SCHEDULE"
    assert combo.adjustment_role == "STATE_ADJUSTMENT"


def test_unknown_experiment_is_refused():
    with pytest.raises(ValueError, match="unknown experiment"):
        build_native_lattice("SPDR-999")
    with pytest.raises(ValueError, match="unknown experiment"):
        build_management_lattice("SPDR-999")
