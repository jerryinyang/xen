"""Direct and reverse schedules for the strategy-native breakout parameters.

Design section 5. "Direct" and "reverse" are identifiers, not favourable labels: the direct
threshold arm makes entry EASIER when the component reads high, the reverse arm makes it
STRICTER. The direct expiry arm keeps the pending order alive LONGER when the component reads
high, the reverse arm SHORTER.
"""

from __future__ import annotations

import polars as pl

from xen.adaptive_management.contracts import (
    Component,
    NativeArmSpec,
    NativeParameter,
    Orientation,
    PolicySpec,
    OriginState,
    build_native_lattice,
)
from xen.adaptive_management.entries import (
    FIXED_EXPIRY_BARS,
    FIXED_THRESHOLD_ATR,
    breakout_episodes,
    breach_episodes,
)

THRESHOLD_BOUNDS = (0.25, 1.00)
SCALE_RATIO_BOUNDS = (0.5, 2.0)
CATEGORICAL_EASIER = 0.375
CATEGORICAL_STRICTER = 0.750
EXPIRY_LONG = 4
EXPIRY_SHORT = 1
BAND_Z_BOUNDS = (1.0, 2.0)
BAND_Z_FIXED = 1.5
BAND_H_FIXED = 12
BAND_H_LONG = 24
BAND_H_SHORT = 4

SCALE_COLUMN = {
    Component.RANGE_SCALE: "range_scale_bps",
    Component.SWING_SCALE: "swing_scale_bps",
}
STATE_COLUMN = {
    Component.LEVEL_NOW: "level_now",
    Component.LEVEL_FORECAST_K4: "level_forecast_k4",
    Component.LEVEL_FORECAST_K12: "level_forecast_k12",
    Component.SHOCK: "shock",
    Component.SWING_GT_CUR: "swing_gt_cur",
    Component.TAIL_RISK: "tail_risk",
}
MEDIAN_KEY = {Component.RANGE_SCALE: "range", Component.SWING_SCALE: "swing"}


def scale_ratio(event_scale: float, median_scale: float) -> float:
    """q = clip(event_scale / calibration_median_scale, 0.5, 2.0) (design section 5)."""
    if (
        not median_scale
        or median_scale <= 0
        or event_scale is None
        or event_scale != event_scale
    ):
        return float("nan")
    return min(max(event_scale / median_scale, SCALE_RATIO_BOUNDS[0]), SCALE_RATIO_BOUNDS[1])


def breakout_threshold(
    orientation: Orientation, q: float | None = None, state: str | None = None
) -> float:
    """Continuous ``clip(0.50/q)`` / ``clip(0.50*q)`` or the categorical HIGH/LOW schedule."""
    if q is not None:
        raw = FIXED_THRESHOLD_ATR / q if orientation is Orientation.DIRECT else (
            FIXED_THRESHOLD_ATR * q
        )
        return min(max(raw, THRESHOLD_BOUNDS[0]), THRESHOLD_BOUNDS[1])
    if state == "HIGH":
        return CATEGORICAL_EASIER if orientation is Orientation.DIRECT else CATEGORICAL_STRICTER
    if state == "LOW":
        return CATEGORICAL_STRICTER if orientation is Orientation.DIRECT else CATEGORICAL_EASIER
    return FIXED_THRESHOLD_ATR


def expiry_bars(state: str, orientation: Orientation) -> int:
    """LONG_ON_HIGH (direct) vs SHORT_ON_HIGH (reverse) pending lifetime, in H1 bars."""
    if state == "HIGH":
        return EXPIRY_LONG if orientation is Orientation.DIRECT else EXPIRY_SHORT
    if state == "LOW":
        return EXPIRY_SHORT if orientation is Orientation.DIRECT else EXPIRY_LONG
    return FIXED_EXPIRY_BARS


def band_z(
    orientation: Orientation, q: float | None = None, state: str | None = None
) -> float:
    """Frozen continuous and categorical SPDR-022/023 band-width schedule."""
    if q is not None:
        raw = BAND_Z_FIXED / q if orientation is Orientation.DIRECT else BAND_Z_FIXED * q
        return min(max(raw, BAND_Z_BOUNDS[0]), BAND_Z_BOUNDS[1])
    if state == "HIGH":
        return BAND_Z_BOUNDS[0] if orientation is Orientation.DIRECT else BAND_Z_BOUNDS[1]
    if state == "LOW":
        return BAND_Z_BOUNDS[1] if orientation is Orientation.DIRECT else BAND_Z_BOUNDS[0]
    return BAND_Z_FIXED


def band_h(state: str, orientation: Orientation) -> int:
    """Frozen LONG_ON_HIGH / SHORT_ON_HIGH breach-zone lifetime."""
    if state == "HIGH":
        return BAND_H_LONG if orientation is Orientation.DIRECT else BAND_H_SHORT
    if state == "LOW":
        return BAND_H_SHORT if orientation is Orientation.DIRECT else BAND_H_LONG
    return BAND_H_FIXED


def _threshold_expression(
    component: Component, orientation: Orientation, median_scale: dict[str, float]
) -> pl.Expr:
    if component in SCALE_COLUMN:
        q = pl.struct(["symbol", SCALE_COLUMN[component]]).map_elements(
            lambda s: scale_ratio(
                s[SCALE_COLUMN[component]], median_scale.get(s["symbol"], float("nan"))
            ),
            return_dtype=pl.Float64,
        )
        raw = (
            FIXED_THRESHOLD_ATR / q if orientation is Orientation.DIRECT else FIXED_THRESHOLD_ATR * q
        )
        return raw.clip(*THRESHOLD_BOUNDS)
    state = pl.col(STATE_COLUMN[component])
    easier, stricter = (
        (CATEGORICAL_EASIER, CATEGORICAL_STRICTER)
        if orientation is Orientation.DIRECT
        else (CATEGORICAL_STRICTER, CATEGORICAL_EASIER)
    )
    return (
        pl.when(state == "HIGH")
        .then(pl.lit(easier))
        .when(state == "LOW")
        .then(pl.lit(stricter))
        .otherwise(pl.lit(FIXED_THRESHOLD_ATR))
    )


def _expiry_expression(component: Component, orientation: Orientation) -> pl.Expr:
    """Categorical for every component; continuous components use their own HIGH/LOW split."""
    if component in SCALE_COLUMN:
        # A continuous scale is discretised against its own calibration median ratio q >= 1.
        state = pl.when(pl.col("_q") >= 1.0).then(pl.lit("HIGH")).otherwise(pl.lit("LOW"))
    else:
        state = pl.col(STATE_COLUMN[component])
    longer, shorter = (
        (EXPIRY_LONG, EXPIRY_SHORT)
        if orientation is Orientation.DIRECT
        else (EXPIRY_SHORT, EXPIRY_LONG)
    )
    return (
        pl.when(state == "HIGH")
        .then(pl.lit(longer))
        .when(state == "LOW")
        .then(pl.lit(shorter))
        .otherwise(pl.lit(FIXED_EXPIRY_BARS))
        .cast(pl.Int64)
    )


def _attach_component_columns(
    origins: pl.DataFrame,
    features: pl.DataFrame,
    component: Component,
    median_scale: dict[str, float],
) -> pl.DataFrame:
    wanted = ["symbol", "ts"]
    if component in SCALE_COLUMN:
        wanted.append(SCALE_COLUMN[component])
    else:
        wanted.append(STATE_COLUMN[component])
    joined = origins.join(
        features.select(wanted).rename({"ts": "decision_ts"}),
        on=["symbol", "decision_ts"],
        how="left",
    )
    if component in SCALE_COLUMN:
        joined = joined.with_columns(
            pl.struct(["symbol", SCALE_COLUMN[component]])
            .map_elements(
                lambda s: scale_ratio(
                    s[SCALE_COLUMN[component]], median_scale.get(s["symbol"], float("nan"))
                ),
                return_dtype=pl.Float64,
            )
            .alias("_q")
        )
    return joined


def materialise_native_arm(
    origins: pl.DataFrame,
    features: pl.DataFrame,
    calibration_medians: dict[str, dict[str, float]],
    spec: NativeArmSpec,
    policy: PolicySpec | None = None,
) -> pl.DataFrame:
    """One row per common origin for one native arm; no origin is ever dropped."""
    if policy is not None:
        raise ValueError(
            "native parameter arms may not be crossed with management policies: "
            f"{spec.native_arm_id} x {policy.policy_id}"
        )
    if not spec.experiment_id or spec not in build_native_lattice(spec.experiment_id):
        raise ValueError("native spec is not a member of its experiment's frozen lattice")
    is_breakout = spec.experiment_id == "SPDR-021"
    if is_breakout and set(origins["entry_variant"].unique()) != {"BREAKOUT"}:
        raise ValueError("native spec experiment does not match origin population")
    if not is_breakout and "entry_variant" in origins.columns:
        raise ValueError("breach experiment spec cannot materialise breakout origins")

    if not spec.is_adaptive:
        if is_breakout:
            episodes = breakout_episodes(
                origins, FIXED_THRESHOLD_ATR, FIXED_EXPIRY_BARS,
                experiment_id=spec.experiment_id, native_arm_id=spec.native_arm_id,
            )
        else:
            episodes = breach_episodes(
                origins, spec.experiment_id, spec.entry_variant,
                z=BAND_Z_FIXED, horizon=BAND_H_FIXED,
                native_arm_id=spec.native_arm_id,
            )
        return episodes.with_columns(
            pl.lit(spec.native_arm_id).alias("native_arm_id"),
            pl.lit("FIXED").alias("orientation"),
            pl.lit(None, dtype=pl.Utf8).alias("component"),
            pl.lit(spec.comparator_id).alias("comparator_id"),
        )

    component = spec.component
    medians = calibration_medians.get(MEDIAN_KEY.get(component, ""), {})
    frame = _attach_component_columns(origins, features, component, medians)

    if spec.orientation_pair is not None:
        threshold_orientation, expiry_orientation = spec.orientation_pair
        orientation_label = f"{threshold_orientation}_{expiry_orientation}"
    else:
        threshold_orientation = (
            spec.orientation if spec.parameter is NativeParameter.BREAKOUT_THRESHOLD else None
        )
        expiry_orientation = (
            spec.orientation if spec.parameter is NativeParameter.PENDING_EXPIRY else None
        )
        orientation_label = str(spec.orientation)

    threshold = (
        _threshold_expression(component, threshold_orientation, medians)
        if threshold_orientation is not None
        else pl.lit(FIXED_THRESHOLD_ATR)
    )
    expiry = (
        _expiry_expression(component, expiry_orientation)
        if expiry_orientation is not None
        else pl.lit(FIXED_EXPIRY_BARS).cast(pl.Int64)
    )
    if component in SCALE_COLUMN:
        # NaN is missing here too: an unwarmed scale or a median fitted on too few bars
        # yields NaN, which must be NO_FEATURE rather than a NaN threshold.
        ready = (
            pl.col(SCALE_COLUMN[component]).is_not_null()
            & pl.col(SCALE_COLUMN[component]).cast(pl.Float64, strict=False).is_not_nan().fill_null(False)
            & pl.col("_q").is_not_null()
            & pl.col("_q").cast(pl.Float64, strict=False).is_not_nan().fill_null(False)
        )
        state_for_h = pl.when(pl.col("_q") >= 1.0).then(pl.lit("HIGH")).otherwise(pl.lit("LOW"))
        q_expr = pl.col("_q")
    else:
        ready = pl.col(STATE_COLUMN[component]).is_in(["HIGH", "LOW"])
        state_for_h = pl.col(STATE_COLUMN[component])
        q_expr = None

    if is_breakout:
        episodes = breakout_episodes(
            frame,
            pl.when(ready).then(threshold).otherwise(None),
            pl.when(ready).then(expiry).otherwise(None),
            experiment_id=spec.experiment_id,
            native_arm_id=spec.native_arm_id,
        ).with_columns(
            pl.when(pl.col("threshold_atr").is_null())
            .then(pl.lit(str(OriginState.NO_FEATURE)))
            .otherwise(pl.col("state")).alias("state")
        )
    else:
        z_orientation = (
            spec.orientation if spec.parameter is NativeParameter.BAND_Z else None
        )
        h_orientation = (
            spec.orientation if spec.parameter is NativeParameter.BAND_H else None
        )
        if spec.orientation_pair is not None:
            z_orientation, h_orientation = spec.orientation_pair
        if z_orientation is None:
            z_expr = pl.lit(BAND_Z_FIXED)
        elif q_expr is not None:
            z_expr = (
                BAND_Z_FIXED / q_expr
                if z_orientation is Orientation.DIRECT
                else BAND_Z_FIXED * q_expr
            ).clip(*BAND_Z_BOUNDS)
        else:
            z_expr = (
                pl.when(state_for_h == "HIGH")
                .then(BAND_Z_BOUNDS[0] if z_orientation is Orientation.DIRECT else BAND_Z_BOUNDS[1])
                .otherwise(BAND_Z_BOUNDS[1] if z_orientation is Orientation.DIRECT else BAND_Z_BOUNDS[0])
            )
        if h_orientation is None:
            h_expr = pl.lit(BAND_H_FIXED)
        else:
            h_expr = (
                pl.when(state_for_h == "HIGH")
                .then(BAND_H_LONG if h_orientation is Orientation.DIRECT else BAND_H_SHORT)
                .otherwise(BAND_H_SHORT if h_orientation is Orientation.DIRECT else BAND_H_LONG)
            )
        scheduled = frame.with_columns(
            pl.when(ready).then(z_expr).otherwise(None).alias("_z"),
            pl.when(ready).then(h_expr).otherwise(None).alias("_h"),
        )
        episodes = breach_episodes(
            scheduled, spec.experiment_id, spec.entry_variant,
            z=scheduled["_z"], horizon=scheduled["_h"],
            native_arm_id=spec.native_arm_id,
        )
    return _null_out_nan(
        episodes.with_columns(
            pl.lit(spec.native_arm_id).alias("native_arm_id"),
            pl.lit(orientation_label).alias("orientation"),
            pl.lit(str(component)).alias("component"),
            pl.lit(spec.comparator_id).alias("comparator_id"),
        )
    )


def _null_out_nan(frame: pl.DataFrame) -> pl.DataFrame:
    """An undefined parameter is null, never NaN: NaN would reach the engine as a price."""
    float_columns = [
        name for name, dtype in frame.schema.items() if dtype in (pl.Float32, pl.Float64)
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
