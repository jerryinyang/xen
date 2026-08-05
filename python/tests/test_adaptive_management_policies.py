"""Native-parameter and device formula tests (design sections 5 and 6)."""

import polars as pl
import pytest

from xen.adaptive_management.contracts import (
    Component,
    Device,
    Orientation,
    build_management_lattice,
    build_native_lattice,
)
from xen.adaptive_management.entries import breakout_origins
from xen.adaptive_management.native_parameters import (
    band_h,
    band_z,
    breakout_threshold,
    expiry_bars,
    materialise_native_arm,
    scale_ratio,
)
from xen.adaptive_management.policies import (
    materialise_policy,
    scale_distance,
    scale_size,
    state_distance,
    state_hold_bars,
    state_size,
)
from xen.adaptive_management.runner import _device_combination_schedule
from tests.test_adaptive_management_entries import _breach_fixture, golden_long_frame
from xen.adaptive_management.entries import breach_origins


def test_continuous_native_thresholds_run_both_directions():
    assert breakout_threshold(q=2.0, orientation=Orientation.DIRECT) == 0.25
    assert breakout_threshold(q=2.0, orientation=Orientation.REVERSE) == 1.00
    assert breakout_threshold(q=0.5, orientation=Orientation.DIRECT) == 1.00
    assert breakout_threshold(q=0.5, orientation=Orientation.REVERSE) == 0.25


def test_continuous_thresholds_are_clipped_to_the_declared_band():
    assert breakout_threshold(q=10.0, orientation=Orientation.DIRECT) == 0.25
    assert breakout_threshold(q=10.0, orientation=Orientation.REVERSE) == 1.00


def test_scale_ratio_is_clipped_between_half_and_two():
    assert scale_ratio(event_scale=100.0, median_scale=50.0) == 2.0
    assert scale_ratio(event_scale=1.0, median_scale=50.0) == 0.5
    assert scale_ratio(event_scale=75.0, median_scale=50.0) == 1.5


def test_categorical_native_parameters_are_balanced():
    assert breakout_threshold(state="HIGH", orientation=Orientation.DIRECT) == 0.375
    assert breakout_threshold(state="LOW", orientation=Orientation.DIRECT) == 0.750
    assert breakout_threshold(state="HIGH", orientation=Orientation.REVERSE) == 0.750
    assert breakout_threshold(state="LOW", orientation=Orientation.REVERSE) == 0.375
    assert expiry_bars("HIGH", Orientation.DIRECT) == 4
    assert expiry_bars("LOW", Orientation.DIRECT) == 1
    assert expiry_bars("HIGH", Orientation.REVERSE) == 1
    assert expiry_bars("LOW", Orientation.REVERSE) == 4
    assert band_z(state="HIGH", orientation=Orientation.DIRECT) == 1.0
    assert band_z(state="HIGH", orientation=Orientation.REVERSE) == 2.0
    assert band_h("HIGH", Orientation.DIRECT) == 24
    assert band_h("HIGH", Orientation.REVERSE) == 4


def test_continuous_breach_parameters_run_all_four_z_h_schedules():
    assert band_z(q=2.0, orientation=Orientation.DIRECT) == 1.0
    assert band_z(q=2.0, orientation=Orientation.REVERSE) == 2.0
    assert band_h("HIGH", Orientation.DIRECT) == 24
    assert band_h("HIGH", Orientation.REVERSE) == 4


def test_unknown_state_falls_back_to_the_fixed_value():
    assert breakout_threshold(state="UNKNOWN", orientation=Orientation.DIRECT) == 0.50
    assert expiry_bars("UNKNOWN", Orientation.DIRECT) == 2


def test_scale_distance_and_fixed_comparator():
    assert scale_distance(event_scale_bps=80.0, multiplier=1.5) == 120.0
    assert scale_distance(event_scale_bps=50.0, multiplier=1.5) == 75.0


def test_state_distance_emits_both_states():
    assert state_distance(100.0, "LOW") == 75.0
    assert state_distance(100.0, "HIGH") == 150.0
    assert state_distance(100.0, "UNKNOWN") == 100.0


def test_risk_size_is_clipped_and_tail_halved():
    assert scale_size(median_scale=50.0, event_scale=10.0) == 2.0
    assert scale_size(median_scale=50.0, event_scale=100.0, tail_high=True) == 0.5
    assert scale_size(median_scale=50.0, event_scale=100.0, shock_active=True) == 0.5
    assert state_size("HIGH") == 0.5
    assert state_size("LOW") == 1.0


def test_state_hold_bars_follows_the_declared_schedule():
    assert state_hold_bars("HIGH", component=Component.SHOCK) == 2
    assert state_hold_bars("LOW", component=Component.SHOCK) == 2
    assert state_hold_bars("HIGH", component=Component.LEVEL_NOW) == 12
    assert state_hold_bars("LOW", component=Component.LEVEL_NOW) == 4


def _features() -> pl.DataFrame:
    frame = golden_long_frame()
    return frame.with_columns(
        pl.lit(60.0).alias("range_scale_bps"),
        pl.lit(80.0).alias("swing_scale_bps"),
        pl.lit("HIGH").alias("level_now"),
        pl.lit("HIGH").alias("level_forecast_k4"),
        pl.lit("LOW").alias("level_forecast_k12"),
        pl.lit("LOW").alias("shock"),
        pl.lit("HIGH").alias("swing_gt_cur"),
        pl.lit("LOW").alias("tail_risk"),
    )


def _calibration_medians() -> dict[str, dict[str, float]]:
    return {
        "range": {"GOLDUSDT": 40.0},
        "swing": {"GOLDUSDT": 100.0},
    }


def test_native_arm_materialisation_keeps_every_origin():
    features = _features()
    origins = breakout_origins(features)
    medians = _calibration_medians()
    arms = [a for a in build_native_lattice("SPDR-021") if a.component == Component.RANGE_SCALE]
    for arm in arms:
        rows = materialise_native_arm(origins, features, medians, arm)
        assert rows.height == origins.height
        assert set(rows["origin_id"]) == set(origins["origin_id"])
        assert rows["native_arm_id"].unique().to_list() == [arm.native_arm_id]


def test_native_combination_uses_both_orientations_of_the_pair():
    features = _features()
    origins = breakout_origins(features)
    medians = _calibration_medians()
    combos = [
        a
        for a in build_native_lattice("SPDR-021")
        if a.component == Component.RANGE_SCALE and a.orientation_pair is not None
    ]
    thresholds = {}
    for arm in combos:
        row = materialise_native_arm(origins, features, medians, arm).row(0, named=True)
        thresholds[arm.orientation_pair] = (row["threshold_atr"], row["expiry_bars"])
    assert len({v for v in thresholds.values()}) == 4


def test_policy_rows_carry_a_fixed_device_comparator_value():
    features = _features()
    origins = breakout_origins(features)
    episodes = origins.with_columns(pl.col("origin_id").alias("episode_id"))
    medians = _calibration_medians()
    arm = next(
        a
        for a in build_management_lattice("SPDR-021")
        if a.is_adaptive
        and a.component == Component.RANGE_SCALE
        and a.device == Device.TARGET
        and a.setting == "M1.50"
    )
    row = materialise_policy(
        episodes, features, medians, arm, experiment_id="SPDR-021"
    ).row(0, named=True)
    assert row["target_distance_bps"] == 90.0  # 1.5 x 60 bps event scale
    assert row["fixed_target_distance_bps"] == 60.0  # 1.5 x 40 bps calibration median


def test_no_native_arm_is_crossed_with_management():
    features = _features()
    origins = breakout_origins(features)
    medians = _calibration_medians()
    native = build_native_lattice("SPDR-021")[1]
    policy = next(a for a in build_management_lattice("SPDR-021") if a.is_adaptive)
    with pytest.raises(ValueError, match="native.*management"):
        materialise_policy(
            origins, features, medians, policy,
            experiment_id="SPDR-021", native_arm=native
        )
    with pytest.raises(ValueError, match="native.*management"):
        materialise_native_arm(origins, features, medians, native, policy=policy)


@pytest.mark.parametrize(
    ("policy_id", "column", "expected"),
    [
        ("FIXED_TARGET_M0.75", "target_distance_bps", 30.0),
        ("FIXED_STOP_M1.50", "stop_distance_bps", 60.0),
        ("FIXED_HOLD_B2", "hold_bars", 2),
        ("FIXED_HOLD_B12", "hold_bars", 12),
    ],
)
def test_fixed_ladder_materialises_its_declared_value(policy_id, column, expected):
    features = _features()
    episodes = breakout_origins(features).with_columns(pl.col("origin_id").alias("episode_id"))
    spec = next(
        arm for arm in build_management_lattice("SPDR-021") if arm.policy_id == policy_id
    )
    row = materialise_policy(
        episodes, features, _calibration_medians(), spec, experiment_id="SPDR-021"
    ).row(0, named=True)
    assert row[column] == expected


def test_plain_baseline_materialises_one_bar_hold_without_a_device():
    features = _features()
    episodes = breakout_origins(features).with_columns(pl.col("origin_id").alias("episode_id"))
    spec = next(
        arm for arm in build_management_lattice("SPDR-021")
        if arm.policy_id == "FIXED_BASELINE_PLAIN"
    )
    row = materialise_policy(
        episodes, features, _calibration_medians(), spec, experiment_id="SPDR-021"
    ).row(0, named=True)
    assert row["device"] == "NONE"
    assert row["hold_bars"] == 1
    assert row["pending_expiry_bars"] == 2
    assert row["risk_size"] == 1.0


def test_range_size_does_not_import_shock_or_tail_restraint():
    features = _features().with_columns(
        pl.lit("HIGH").alias("shock"), pl.lit("HIGH").alias("tail_risk")
    )
    episodes = breakout_origins(features).with_columns(pl.col("origin_id").alias("episode_id"))
    spec = next(
        arm for arm in build_management_lattice("SPDR-021")
        if arm.component == Component.RANGE_SCALE and arm.device == Device.SIZE
        and arm.combination_id is None
    )
    row = materialise_policy(
        episodes, features, _calibration_medians(), spec, experiment_id="SPDR-021"
    ).row(0, named=True)
    assert row["risk_size"] == pytest.approx(40.0 / 60.0)


@pytest.mark.parametrize(
    ("experiment_id", "expected_hold"),
    [("SPDR-021", 1), ("SPDR-022", 4), ("SPDR-023", 4)],
)
def test_size_inherits_the_strategy_fixed_horizon(experiment_id, expected_hold):
    features = _features()
    episodes = breakout_origins(features).with_columns(
        pl.col("origin_id").alias("episode_id")
    )
    spec = next(
        arm
        for arm in build_management_lattice(experiment_id)
        if arm.device == Device.SIZE and arm.component == Component.RANGE_SCALE
        and arm.combination_id is None
    )
    row = materialise_policy(
        episodes, features, _calibration_medians(), spec,
        experiment_id=experiment_id,
    ).row(0, named=True)
    assert row["hold_bars"] == expected_hold


def test_only_time_based_devices_materialise_a_horizon():
    features = _features()
    episodes = breakout_origins(features).with_columns(
        pl.col("origin_id").alias("episode_id")
    )
    arms = build_management_lattice("SPDR-021")
    adaptive_hold = next(
        arm for arm in arms
        if arm.device == Device.HOLD and arm.component == Component.LEVEL_NOW
        and arm.combination_id is None
    )
    hold_row = materialise_policy(
        episodes, features, _calibration_medians(), adaptive_hold,
        experiment_id="SPDR-021",
    ).row(0, named=True)
    assert hold_row["hold_bars"] == 12

    for device in (Device.TARGET, Device.STOP, Device.TRAIL):
        spec = next(
            arm for arm in arms
            if arm.device == device and arm.component is None
        )
        row = materialise_policy(
            episodes, features, _calibration_medians(), spec,
            experiment_id="SPDR-021",
        ).row(0, named=True)
        assert row.get("hold_bars") is None


@pytest.mark.parametrize(
    ("combination_id", "expected_hold"),
    [
        ("DC_TARGET_STOP", None),
        ("DC_TRAIL_HOLD", 4),
        ("DC_TARGET_STOP_HOLD", 4),
    ],
)
def test_device_combinations_use_only_their_declared_hold(
    combination_id, expected_hold
):
    features = _features()
    episodes = breakout_origins(features).with_columns(
        pl.col("origin_id").alias("episode_id")
    )
    group = []
    for spec in build_management_lattice("SPDR-021"):
        if spec.combination_id != combination_id:
            continue
        frame = materialise_policy(
            episodes, features, _calibration_medians(), spec,
            experiment_id="SPDR-021",
        )
        group.append((spec, frame))
    row = _device_combination_schedule(
        combination_id, group, "BREAKOUT", "SPDR-021"
    ).row(0, named=True)
    assert row["hold_bars"] == expected_hold


def test_component_combination_executes_primary_then_adjustment_and_keeps_roles():
    features = _features()
    episodes = breakout_origins(features).with_columns(pl.col("origin_id").alias("episode_id"))
    spec = next(
        arm for arm in build_management_lattice("SPDR-021")
        if arm.combination_id == "CC_RANGE_SCALE__LEVEL_NOW"
        and arm.device == Device.TARGET
    )
    row = materialise_policy(
        episodes, features, _calibration_medians(), spec, experiment_id="SPDR-021"
    ).row(0, named=True)
    assert row["target_distance_bps"] == 90.0  # range 60, HIGH adjustment 1.50
    assert row["primary_component"] == "RANGE_SCALE"
    assert row["adjustment_component"] == "LEVEL_NOW"


@pytest.mark.parametrize(
    ("shock", "level", "expected_hold", "expected_eligible"),
    [
        ("HIGH", "LOW", 2, True),
        ("HIGH", "HIGH", 2, True),
        ("LOW", "LOW", 4, True),
        ("LOW", "HIGH", 12, True),
        ("UNKNOWN", "LOW", None, False),
        ("LOW", "UNKNOWN", None, False),
    ],
)
def test_shock_level_hold_uses_override_then_level_schedule(
    shock, level, expected_hold, expected_eligible
):
    features = _features().with_columns(
        pl.lit(shock).alias("shock"),
        pl.lit(level).alias("level_now"),
    )
    episodes = breakout_origins(features).with_columns(
        pl.col("origin_id").alias("episode_id")
    )
    spec = next(
        arm for arm in build_management_lattice("SPDR-021")
        if arm.combination_id == "CC_SHOCK__LEVEL_NOW"
        and arm.device == Device.HOLD
    )
    row = materialise_policy(
        episodes, features, _calibration_medians(), spec, experiment_id="SPDR-021"
    ).row(0, named=True)
    assert row["hold_bars"] == expected_hold
    assert row["eligible"] is expected_eligible


def test_out_of_lattice_and_mismatched_experiment_specs_are_rejected():
    features = _features()
    origins = breakout_origins(features)
    valid = next(a for a in build_native_lattice("SPDR-022") if a.is_adaptive)
    with pytest.raises(ValueError, match="experiment"):
        materialise_native_arm(origins, features, _calibration_medians(), valid)
    policy = next(a for a in build_management_lattice("SPDR-022") if a.is_adaptive)
    with pytest.raises(ValueError, match="experiment"):
        materialise_policy(
            origins, features, _calibration_medians(), policy, experiment_id="SPDR-021"
        )


def test_unready_component_is_explicit_not_substituted_with_fixed_values():
    features = _features().with_columns(pl.lit(None).alias("range_scale_bps"))
    origins = breakout_origins(features)
    spec = next(
        a for a in build_native_lattice("SPDR-021")
        if a.component == Component.RANGE_SCALE and a.is_adaptive
    )
    row = materialise_native_arm(
        origins, features, _calibration_medians(), spec
    ).row(0, named=True)
    assert row["state"] == "NO_FEATURE"
    assert row["threshold_atr"] is None


def test_nan_component_is_no_feature_not_an_eligible_nan_parameter():
    # A component undefined for the window (unwarmed swing scale, or a median fitted on too
    # few bars) arrives as NaN, not null. NaN must not schedule a NaN threshold or distance.
    features = _features().with_columns(
        pl.lit(float("nan"), dtype=pl.Float64).alias("range_scale_bps")
    )
    origins = breakout_origins(features)
    native_spec = next(
        a for a in build_native_lattice("SPDR-021")
        if a.component == Component.RANGE_SCALE and a.is_adaptive
    )
    native = materialise_native_arm(origins, features, _calibration_medians(), native_spec)
    assert set(native["state"]) == {"NO_FEATURE"}
    assert native["threshold_atr"].null_count() == native.height

    policy_spec = next(
        p for p in build_management_lattice("SPDR-021")
        if p.component == Component.RANGE_SCALE
        and p.device is Device.TARGET
        and p.is_adaptive
    )
    rows = materialise_policy(
        native, features, _calibration_medians(), policy_spec, experiment_id="SPDR-021"
    )
    assert set(rows["eligibility_status"]) == {"NO_FEATURE"}
    assert not rows["eligible"].any()


def test_breach_native_combination_materialises_all_four_z_h_pairs():
    h1, features = _breach_fixture()
    origins = breach_origins(h1, features)
    combos = [
        arm for arm in build_native_lattice("SPDR-022")
        if arm.component == Component.RANGE_SCALE
        and arm.entry_variant == "E_TOUCH"
        and arm.orientation_pair is not None
    ]
    observed = {
        (
            materialise_native_arm(
                origins, features, {"range": {"GOLDUSDT": 50.0}}, arm
            )["z"][0],
            materialise_native_arm(
                origins, features, {"range": {"GOLDUSDT": 50.0}}, arm
            )["horizon"][0],
        )
        for arm in combos
    }
    assert observed == {(1.0, 24), (1.0, 4), (2.0, 24), (2.0, 4)}
