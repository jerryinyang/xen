"""External trade-management device parameters and their fixed-device comparators.

Design section 6. Every adaptive row carries the same-device fixed comparator computed on the
TRAIN-median causal scale, so "having a device" is separated from "adapting that device".
Position sizing is a separate risk-normalisation read and is never attached to an exit
combination.
"""

from __future__ import annotations

import polars as pl

from xen.adaptive_management.contracts import (
    BASELINE_HOLD_BARS,
    Component,
    Device,
    NativeArmSpec,
    PolicySpec,
    OriginState,
    SCALE_COMPONENTS,
    STATE_SIZE_SETTING,
    UNCAPPED_ARM_ID,
    build_management_lattice,
)
from xen.adaptive_management.native_parameters import (
    MEDIAN_KEY,
    SCALE_COLUMN,
    STATE_COLUMN,
    scale_ratio,
)

STATE_LOW_MULTIPLIER = 0.75
STATE_HIGH_MULTIPLIER = 1.50
SIZE_BOUNDS = (0.5, 2.0)
SIZE_RESTRAINT = 0.5
TRAIL_ACTIVATION_MULTIPLE = 1.0  # design section 6: activate after 1.0 x the trail distance
SHOCK_HOLD_BARS = 2
OPPORTUNITY_HOLD = {"LOW": 4, "HIGH": 12}
FIXED_HOLD_BARS = 4


def scale_distance(event_scale_bps: float, multiplier: float) -> float:
    """Adaptive distance = m x causal event scale (design section 6)."""
    return multiplier * event_scale_bps


def state_distance(fixed_distance_bps: float, state: str) -> float:
    """State-conditioned distance: 0.75x in the lower state, 1.50x in the higher state."""
    if state == "HIGH":
        return STATE_HIGH_MULTIPLIER * fixed_distance_bps
    if state == "LOW":
        return STATE_LOW_MULTIPLIER * fixed_distance_bps
    return fixed_distance_bps


def scale_size(
    median_scale: float,
    event_scale: float,
    tail_high: bool = False,
    shock_active: bool = False,
) -> float:
    """RANGE_SCALE-only inverse-range sizing; no undeclared shock/tail cross."""
    if not event_scale or event_scale <= 0:
        size = 1.0
    else:
        size = min(max(median_scale / event_scale, SIZE_BOUNDS[0]), SIZE_BOUNDS[1])
    _ = tail_high, shock_active
    return size


def state_size(state: str) -> float:
    """State size restraint: the higher state halves the unit risk; the lower state keeps it.

    Design section 6 names the halving for high TAIL_RISK and active SHOCK. Section 7 also marks
    LEVEL_NOW and LEVEL_FORECAST as size components; the same restraint rule is applied to their
    HIGH state, which is the only size rule the design supplies.
    """
    if state == "HIGH":
        return SIZE_RESTRAINT
    if state == "LOW":
        return 1.0
    return 1.0


def state_hold_bars(state: str, component: Component) -> int:
    """SHOCK uses a 2-bar window; other state components use 4 (low) / 12 (high) bars."""
    if component is Component.SHOCK:
        return SHOCK_HOLD_BARS
    return OPPORTUNITY_HOLD.get(state, FIXED_HOLD_BARS)


def _multiplier_from_setting(setting: str) -> float:
    return float(setting[1:])


def _baseline_hold(experiment_id: str) -> int:
    """Bars the plain baseline holds, in signal-domain bars."""
    if experiment_id in {"SPDR-021", "SPDR-024"}:
        return BASELINE_HOLD_BARS
    return FIXED_HOLD_BARS


def _distance_columns(
    spec: PolicySpec, median_scale: dict[str, float]
) -> tuple[pl.Expr, pl.Expr]:
    """Return (adaptive distance, fixed-device comparator distance) in bps."""
    device_median = pl.col("symbol").replace_strict(
        median_scale, default=None, return_dtype=pl.Float64
    )
    if spec.component in SCALE_COLUMN and spec.setting.startswith("M"):
        m = _multiplier_from_setting(spec.setting)
        return pl.col(SCALE_COLUMN[spec.component]) * m, device_median * m
    fixed = device_median * 1.0
    state = pl.col(STATE_COLUMN[spec.component]) if spec.component in STATE_COLUMN else pl.lit(
        "UNKNOWN"
    )
    adaptive = (
        pl.when(state == "HIGH")
        .then(fixed * STATE_HIGH_MULTIPLIER)
        .when(state == "LOW")
        .then(fixed * STATE_LOW_MULTIPLIER)
        .otherwise(fixed)
    )
    return adaptive, fixed


def materialise_policy(
    episodes: pl.DataFrame,
    features: pl.DataFrame,
    calibration_medians: dict[str, dict[str, float]],
    spec: PolicySpec,
    *,
    experiment_id: str,
    native_arm: NativeArmSpec | None = None,
) -> pl.DataFrame:
    """One row per eligible episode for one management arm, with its fixed-device comparator."""
    if native_arm is not None or spec.native_arm_id is not None:
        raise ValueError(
            "native parameter arms may not be crossed with management policies: "
            f"{spec.policy_id}"
        )
    if spec.experiment_id != experiment_id or spec not in build_management_lattice(experiment_id):
        raise ValueError("management spec is not a member of the supplied experiment lattice")
    component = spec.component
    wanted = ["symbol", "ts"]
    for column in (
        SCALE_COLUMN.get(component),
        STATE_COLUMN.get(component),
        "range_scale_bps",
        "shock",
        "tail_risk",
        STATE_COLUMN.get(spec.adjustment_component),
    ):
        if column and column in features.columns and column not in wanted:
            wanted.append(column)
    frame = episodes.join(
        features.select(wanted).rename({"ts": "decision_ts"}),
        on=["symbol", "decision_ts"],
        how="left",
    )
    medians = calibration_medians.get(MEDIAN_KEY.get(component, "range"), {})

    columns: list[pl.Expr] = [
        pl.lit(spec.policy_id).alias("policy_id"),
        pl.lit(str(spec.device)).alias("device"),
        pl.lit(spec.setting).alias("setting"),
        pl.lit(spec.comparator_id).alias("comparator_id"),
        pl.lit(spec.combination_id, dtype=pl.Utf8).alias("combination_id"),
        pl.lit(str(component) if component else None, dtype=pl.Utf8).alias("component"),
        pl.lit(None, dtype=pl.Utf8).alias("native_arm_id"),
        pl.lit(str(component) if component else None, dtype=pl.Utf8).alias(
            "primary_component"
        ),
        pl.lit(
            str(spec.adjustment_component) if spec.adjustment_component else None,
            dtype=pl.Utf8,
        ).alias("adjustment_component"),
        pl.lit(spec.component_role, dtype=pl.Utf8).alias("component_role"),
        pl.lit(spec.adjustment_role, dtype=pl.Utf8).alias("adjustment_role"),
        pl.lit(True).alias("eligible"),
        pl.lit("ELIGIBLE").alias("eligibility_status"),
    ]

    if spec.device is Device.NONE:
        columns += [
            pl.lit(spec.fixed_hold_bars, dtype=pl.Int64).alias("hold_bars"),
            pl.lit(spec.pending_expiry_bars, dtype=pl.Int64).alias("pending_expiry_bars"),
            pl.lit(1.0).alias("risk_size"),
            pl.lit(
                "SAFETY_CEILING" if spec.policy_id == UNCAPPED_ARM_ID else None,
                dtype=pl.Utf8,
            ).alias("hold_exit_reason"),
        ]
    elif not spec.is_adaptive:
        if spec.device in (Device.TARGET, Device.STOP, Device.TRAIL):
            multiplier = _multiplier_from_setting(spec.setting)
            median = pl.col("symbol").replace_strict(
                calibration_medians.get("range", {}),
                default=None,
                return_dtype=pl.Float64,
            )
            name = str(spec.device).lower()
            columns.append((median * multiplier).alias(f"{name}_distance_bps"))
            columns.append((median * multiplier).alias(f"fixed_{name}_distance_bps"))
            if spec.device is Device.TRAIL:
                columns.append(
                    (median * multiplier * TRAIL_ACTIVATION_MULTIPLE).alias(
                        "trail_activation_bps"
                    )
                )
        elif spec.device is Device.HOLD:
            columns += [
                pl.lit(spec.fixed_hold_bars, dtype=pl.Int64).alias("hold_bars"),
                pl.lit(spec.fixed_hold_bars, dtype=pl.Int64).alias("fixed_hold_bars"),
            ]
        else:
            columns += [
                pl.lit(1.0).alias("risk_size"),
                pl.lit(1.0).alias("fixed_risk_size"),
                pl.lit(_baseline_hold(experiment_id), dtype=pl.Int64).alias("hold_bars"),
            ]
    elif spec.device in (Device.TARGET, Device.STOP, Device.TRAIL):
        adaptive, fixed = _distance_columns(spec, medians)
        adjustment = spec.adjustment_component
        if adjustment is not None:
            state = pl.col(STATE_COLUMN[adjustment])
            if component is Component.RANGE_SCALE:
                adaptive = pl.col("range_scale_bps")
            elif component is Component.SHOCK:
                adaptive = fixed
            adaptive = (
                pl.when(state == "HIGH").then(adaptive * STATE_HIGH_MULTIPLIER)
                .when(state == "LOW").then(adaptive * STATE_LOW_MULTIPLIER)
                .otherwise(None)
            )
        name = str(spec.device).lower()
        columns += [
            adaptive.alias(f"{name}_distance_bps"),
            fixed.alias(f"fixed_{name}_distance_bps"),
        ]
        if spec.device is Device.TRAIL:
            columns.append(
                (adaptive * TRAIL_ACTIVATION_MULTIPLE).alias("trail_activation_bps")
            )
    elif spec.device is Device.HOLD:
        state_component = spec.adjustment_component or component
        state = pl.col(STATE_COLUMN[state_component]) if state_component in STATE_COLUMN else pl.lit(
            "UNKNOWN"
        )
        if component is Component.SHOCK and spec.adjustment_component is not None:
            shock = pl.col(STATE_COLUMN[Component.SHOCK])
            bars = (
                pl.when(shock == "HIGH")
                .then(pl.lit(SHOCK_HOLD_BARS))
                .when((shock == "LOW") & (state == "HIGH"))
                .then(pl.lit(OPPORTUNITY_HOLD["HIGH"]))
                .when((shock == "LOW") & (state == "LOW"))
                .then(pl.lit(OPPORTUNITY_HOLD["LOW"]))
                .otherwise(None)
            )
        elif component is Component.SHOCK:
            bars = (
                pl.when(state.is_in(["HIGH", "LOW"]))
                .then(pl.lit(SHOCK_HOLD_BARS))
                .otherwise(None)
            )
        else:
            bars = (
                pl.when(state == "HIGH")
            .then(pl.lit(OPPORTUNITY_HOLD["HIGH"]))
            .when(state == "LOW")
            .then(pl.lit(OPPORTUNITY_HOLD["LOW"]))
                .otherwise(None)
            )
        columns += [
            bars.cast(pl.Int64).alias("hold_bars"),
            pl.lit(FIXED_HOLD_BARS, dtype=pl.Int64).alias("fixed_hold_bars"),
        ]
    else:  # Device.SIZE
        if component in SCALE_COLUMN and spec.setting == STATE_SIZE_SETTING:
            # The discrete gate on a numeric component: its own calibration-median ratio
            # q >= 1 is the HIGH state, exactly as the native expiry schedule discretises it.
            median = pl.col("symbol").replace_strict(
                medians, default=None, return_dtype=pl.Float64
            )
            state = (
                pl.when(pl.col(SCALE_COLUMN[component]) >= median)
                .then(pl.lit("HIGH"))
                .when(pl.col(SCALE_COLUMN[component]).is_not_null())
                .then(pl.lit("LOW"))
                .otherwise(pl.lit("UNKNOWN"))
            )
            size = (
                pl.when(state == "HIGH").then(pl.lit(SIZE_RESTRAINT))
                .when(state == "LOW").then(pl.lit(1.0))
                .otherwise(None)
            )
        elif component in SCALE_COMPONENTS:
            median = pl.col("symbol").replace_strict(
                medians, default=None, return_dtype=pl.Float64
            )
            size = (median / pl.col(SCALE_COLUMN[component])).clip(*SIZE_BOUNDS)
            if spec.adjustment_component is not None:
                state = pl.col(STATE_COLUMN[spec.adjustment_component])
                size = (
                    pl.when(state == "HIGH").then(size * SIZE_RESTRAINT)
                    .when(state == "LOW").then(size)
                    .otherwise(None)
                )
        elif component is Component.SHOCK and spec.adjustment_component is not None:
            shock = pl.col(STATE_COLUMN[Component.SHOCK])
            level = pl.col(STATE_COLUMN[spec.adjustment_component])
            size = (
                pl.when(shock == "HIGH").then(SIZE_RESTRAINT)
                .when((shock == "LOW") & (level == "HIGH")).then(SIZE_RESTRAINT)
                .when((shock == "LOW") & (level == "LOW")).then(1.0)
                .otherwise(None)
            )
        else:
            state = (
                pl.col(STATE_COLUMN[component])
                if component in STATE_COLUMN
                else pl.lit("UNKNOWN")
            )
            size = (
                pl.when(state == "HIGH").then(pl.lit(SIZE_RESTRAINT))
                .when(state == "LOW").then(pl.lit(1.0))
                .otherwise(None)
            )
        columns += [
            size.alias("risk_size"),
            pl.lit(1.0).alias("fixed_risk_size"),
            pl.lit(_baseline_hold(experiment_id), dtype=pl.Int64).alias("hold_bars"),
        ]

    result = _null_out_nan(frame.with_columns(columns))
    value_columns = [
        name
        for name in (
            "target_distance_bps", "stop_distance_bps", "trail_distance_bps",
            "hold_bars", "risk_size",
        )
        if name in result.columns
    ]
    if value_columns:
        ready = pl.any_horizontal(
            _is_present(result.schema[name], name) for name in value_columns
        )
        result = result.with_columns(
            ready.alias("eligible"),
            pl.when(ready).then(pl.lit("ELIGIBLE"))
            .otherwise(pl.lit(str(OriginState.NO_FEATURE))).alias("eligibility_status"),
        )
    return result


def _null_out_nan(frame: pl.DataFrame) -> pl.DataFrame:
    """An undefined parameter is null, never NaN: NaN would reach the engine as a price."""
    float_columns = [
        name
        for name, dtype in frame.schema.items()
        if dtype in (pl.Float32, pl.Float64)
    ]
    if not float_columns:
        return frame
    return frame.with_columns(
        [
            pl.when(pl.col(name).is_nan().fill_null(False))
            .then(None)
            .otherwise(pl.col(name))
            .alias(name)
            for name in float_columns
        ]
    )


def _is_present(dtype: pl.DataType, name: str) -> pl.Expr:
    """A feature value is present only if it is neither null nor NaN.

    A NaN reaches this point whenever a component is undefined for the window (an
    unwarmed swing scale, or a median fitted on too few bars). Treating it as present
    schedules a NaN price and aborts the engine mid-run, so it is NO_FEATURE.
    """
    present = pl.col(name).is_not_null()
    if dtype in (pl.Float32, pl.Float64):
        present = present & pl.col(name).cast(pl.Float64, strict=False).is_not_nan().fill_null(False)
    return present


def scale_ratio_for(event_scale: float, median_scale: float) -> float:
    """Re-exported for callers that need the native q on a management row."""
    return scale_ratio(event_scale, median_scale)
