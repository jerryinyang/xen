"""Frozen contracts and the predeclared arm lattice.

Every arm in this module is declared by
`adaptive-management-design.md` sections 4 to 7. Nothing here is selected from outcomes,
and no row carries a verdict, quality or ranking label.

Native-arm counts (design section 5): 8 executable component IDs x 2 native parameters x 2
orientations = 32 single arms, plus 4 predeclared orientation pairs per component = 32
combination arms, giving 64 adaptive native configurations per entry variant. SPDR-021 has one
entry variant (64); SPDR-022 and SPDR-023 have two (E-TOUCH / E-CLOSE) and therefore 128 each.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #


class Component(StrEnum):
    """The eight executable volatility component IDs (seven families; LEVEL_FORECAST x2)."""

    RANGE_SCALE = "RANGE_SCALE"
    SWING_SCALE = "SWING_SCALE"
    LEVEL_NOW = "LEVEL_NOW"
    LEVEL_FORECAST_K4 = "LEVEL_FORECAST_K4"
    LEVEL_FORECAST_K12 = "LEVEL_FORECAST_K12"
    SHOCK = "SHOCK"
    SWING_GT_CUR = "SWING_GT_CUR"
    TAIL_RISK = "TAIL_RISK"


class Device(StrEnum):
    NONE = "NONE"
    TARGET = "TARGET"
    STOP = "STOP"
    TRAIL = "TRAIL"
    HOLD = "HOLD"
    SIZE = "SIZE"


class EntryOrderType(StrEnum):
    NONE = "NONE"
    STOP = "STOP"
    MARKET = "MARKET"


class NativeParameter(StrEnum):
    BREAKOUT_THRESHOLD = "BREAKOUT_THRESHOLD"
    PENDING_EXPIRY = "PENDING_EXPIRY"
    BAND_Z = "BAND_Z"
    BAND_H = "BAND_H"


class Orientation(StrEnum):
    DIRECT = "DIRECT"
    REVERSE = "REVERSE"


class OriginState(StrEnum):
    """Exactly one of these is recorded per origin per arm."""

    NO_EVENT = "NO_EVENT"
    ORDER_CREATED = "ORDER_CREATED"
    EXPIRED = "EXPIRED"
    FILLED = "FILLED"
    BLOCKED_ACTIVE = "BLOCKED_ACTIVE"
    NO_FEATURE = "NO_FEATURE"
    EVENT_UNDECIDED = "EVENT_UNDECIDED"
    INCOMPLETE = "INCOMPLETE"
    CENSORED = "CENSORED"
    REJECTED = "REJECTED"
    DENIED = "DENIED"


# --------------------------------------------------------------------------- #
# Frozen records
# --------------------------------------------------------------------------- #

SCALE_COMPONENTS = (Component.RANGE_SCALE, Component.SWING_SCALE)
STATE_COMPONENTS = (
    Component.LEVEL_NOW,
    Component.LEVEL_FORECAST_K4,
    Component.LEVEL_FORECAST_K12,
    Component.SHOCK,
    Component.SWING_GT_CUR,
    Component.TAIL_RISK,
)

DISTANCE_MULTIPLIERS = (0.75, 1.00, 1.50)
HOLD_CAPS = (2, 4, 12)
STATE_DISTANCE_SETTING = "STATE_LOW_075_HIGH_150"
STATE_SIZE_SETTING = "STATE_HALVE_HIGH"
SCALE_SIZE_SETTING = "SCALE_NORMALISED"
STATE_HOLD_SETTING = "STATE_LOW_4_HIGH_12"
SHOCK_HOLD_SETTING = "STATE_SHOCK_2"

# Design section 7 - the applicable component x device table, verbatim.
APPLICABLE_DEVICES: dict[Component, tuple[Device, ...]] = {
    Component.RANGE_SCALE: (Device.TARGET, Device.STOP, Device.TRAIL, Device.SIZE),
    Component.SWING_SCALE: (Device.TARGET, Device.STOP),
    Component.LEVEL_NOW: (
        Device.TARGET, Device.STOP, Device.TRAIL, Device.HOLD, Device.SIZE
    ),
    Component.LEVEL_FORECAST_K4: (
        Device.TARGET, Device.STOP, Device.TRAIL, Device.HOLD, Device.SIZE
    ),
    Component.LEVEL_FORECAST_K12: (
        Device.TARGET, Device.STOP, Device.TRAIL, Device.HOLD, Device.SIZE
    ),
    Component.SHOCK: (
        Device.TARGET, Device.STOP, Device.TRAIL, Device.HOLD, Device.SIZE
    ),
    Component.SWING_GT_CUR: (Device.TARGET, Device.HOLD),
    Component.TAIL_RISK: (Device.TARGET, Device.STOP, Device.SIZE),
}

# Design section 7 - the only component combinations allowed (k=4 and k=12 separate).
COMPONENT_COMBINATIONS: tuple[tuple[Component, Component], ...] = (
    (Component.RANGE_SCALE, Component.LEVEL_NOW),
    (Component.RANGE_SCALE, Component.LEVEL_FORECAST_K4),
    (Component.RANGE_SCALE, Component.LEVEL_FORECAST_K12),
    (Component.SHOCK, Component.LEVEL_NOW),
    (Component.RANGE_SCALE, Component.SWING_GT_CUR),
)

# Design section 7 - the only multi-device combinations allowed. Sizing is never included.
DEVICE_COMBINATIONS: dict[str, tuple[Device, ...]] = {
    "DC_TARGET_STOP": (Device.TARGET, Device.STOP),
    "DC_TRAIL_HOLD": (Device.TRAIL, Device.HOLD),
    "DC_TARGET_STOP_HOLD": (Device.TARGET, Device.STOP, Device.HOLD),
}

NATIVE_PARAMETERS: dict[str, tuple[NativeParameter, NativeParameter]] = {
    "SPDR-021": (NativeParameter.BREAKOUT_THRESHOLD, NativeParameter.PENDING_EXPIRY),
    "SPDR-022": (NativeParameter.BAND_Z, NativeParameter.BAND_H),
    "SPDR-023": (NativeParameter.BAND_Z, NativeParameter.BAND_H),
}

ENTRY_VARIANTS: dict[str, tuple[str, ...]] = {
    "SPDR-021": ("BREAKOUT",),
    "SPDR-022": ("E_TOUCH", "E_CLOSE"),
    "SPDR-023": ("E_TOUCH", "E_CLOSE"),
}


@dataclass(frozen=True)
class ExperimentSpec:
    experiment_id: str
    entry_variants: tuple[str, ...]
    native_parameters: tuple[NativeParameter, NativeParameter]


@dataclass(frozen=True)
class Origin:
    """A common-origin clock entry, fixed before any adaptive parameter is applied."""

    origin_id: str
    symbol: str
    decision_ts: datetime
    entry_variant: str


@dataclass(frozen=True)
class Episode:
    """One arm's realisation of an origin: order created, expired, filled or blocked."""

    episode_id: str
    origin_id: str
    symbol: str
    side: int
    state: OriginState
    event_ts: datetime | None = None
    entry_ts: datetime | None = None
    actionable_ts: datetime | None = None
    entry_order_type: EntryOrderType = EntryOrderType.NONE
    entry_variant: str = ""


@dataclass(frozen=True)
class PolicySpec:
    policy_id: str
    component: Component | None
    device: Device
    setting: str
    comparator_id: str
    combination_id: str | None = None
    native_arm_id: str | None = None
    is_adaptive: bool = True
    experiment_id: str = ""
    entry_variant: str = ""
    adjustment_component: Component | None = None
    component_role: str | None = None
    adjustment_role: str | None = None
    fixed_hold_bars: int | None = None
    pending_expiry_bars: int | None = None


@dataclass(frozen=True)
class NativeArmSpec:
    native_arm_id: str
    component: Component | None
    parameter: NativeParameter | None
    orientation: Orientation | None
    comparator_id: str
    entry_variant: str
    parameters: tuple[NativeParameter, ...] = ()
    combination_id: str | None = None
    orientation_pair: tuple[Orientation, Orientation] | None = None
    is_adaptive: bool = True
    experiment_id: str = ""


@dataclass(frozen=True)
class ResultKey:
    """The full row key required by design section 3."""

    experiment_id: str
    entry_variant: str
    universe: str
    symbol: str
    arm_class: str
    component: str
    parameter_or_device: str
    orientation_or_setting: str
    state: str


# --------------------------------------------------------------------------- #
# Lattice builders
# --------------------------------------------------------------------------- #


def experiment_spec(experiment_id: str) -> ExperimentSpec:
    """Return the frozen spec for a declared experiment ID."""
    if experiment_id not in NATIVE_PARAMETERS:
        raise ValueError(f"unknown experiment: {experiment_id}")
    return ExperimentSpec(
        experiment_id=experiment_id,
        entry_variants=ENTRY_VARIANTS[experiment_id],
        native_parameters=NATIVE_PARAMETERS[experiment_id],
    )


def _fixed_native_arm_id(experiment_id: str, entry_variant: str) -> str:
    kind = "BREAKOUT" if experiment_id == "SPDR-021" else "BAND"
    suffix = "" if experiment_id == "SPDR-021" else f"_{entry_variant}"
    return f"FIXED_NATIVE_{kind}{suffix}"


def build_native_lattice(experiment_id: str) -> tuple[NativeArmSpec, ...]:
    """Fixed comparator, both single-parameter orientations and all four orientation pairs."""
    spec = experiment_spec(experiment_id)
    first, second = spec.native_parameters
    arms: list[NativeArmSpec] = []
    for entry_variant in spec.entry_variants:
        comparator_id = _fixed_native_arm_id(experiment_id, entry_variant)
        arms.append(
            NativeArmSpec(
                native_arm_id=comparator_id,
                component=None,
                parameter=None,
                orientation=None,
                comparator_id=comparator_id,
                entry_variant=entry_variant,
                parameters=(first, second),
                is_adaptive=False,
                experiment_id=experiment_id,
            )
        )
        for component in Component:
            for parameter in (first, second):
                for orientation in Orientation:
                    arms.append(
                        NativeArmSpec(
                            native_arm_id=(
                                f"NAT_{entry_variant}_{component}_{parameter}_{orientation}"
                            ),
                            component=component,
                            parameter=parameter,
                            orientation=orientation,
                            comparator_id=comparator_id,
                            entry_variant=entry_variant,
                            parameters=(parameter,),
                            experiment_id=experiment_id,
                        )
                    )
            for pair in _ORIENTATION_PAIRS:
                arms.append(
                    NativeArmSpec(
                        native_arm_id=(
                            f"NATCOMB_{entry_variant}_{component}_{pair[0]}_{pair[1]}"
                        ),
                        component=component,
                        parameter=None,
                        orientation=None,
                        comparator_id=comparator_id,
                        entry_variant=entry_variant,
                        parameters=(first, second),
                        combination_id=f"NC_{first}__{second}",
                        orientation_pair=pair,
                        experiment_id=experiment_id,
                    )
                )
    return tuple(arms)


_ORIENTATION_PAIRS: tuple[tuple[Orientation, Orientation], ...] = (
    (Orientation.DIRECT, Orientation.DIRECT),
    (Orientation.DIRECT, Orientation.REVERSE),
    (Orientation.REVERSE, Orientation.DIRECT),
    (Orientation.REVERSE, Orientation.REVERSE),
)


def native_combination_pairs(experiment_id: str, component: Component) -> set[tuple[str, str]]:
    """The four predeclared orientation pairs for a component's native combination."""
    arms = build_native_lattice(experiment_id)
    return {
        (a.orientation_pair[0].value, a.orientation_pair[1].value)
        for a in arms
        if a.component == component and a.orientation_pair is not None
    }


def _adaptive_setting(component: Component, device: Device) -> tuple[str, ...]:
    """The frozen setting labels for one component x device cell."""
    if device is Device.SIZE:
        return (SCALE_SIZE_SETTING,) if component in SCALE_COMPONENTS else (STATE_SIZE_SETTING,)
    if device is Device.HOLD:
        return (SHOCK_HOLD_SETTING,) if component is Component.SHOCK else (STATE_HOLD_SETTING,)
    if component in SCALE_COMPONENTS:
        return tuple(f"M{m:.2f}" for m in DISTANCE_MULTIPLIERS)
    return (STATE_DISTANCE_SETTING,)


def _comparator_id(device: Device, setting: str) -> str:
    if device is Device.SIZE:
        return "FIXED_SIZE_UNIT"
    if device is Device.HOLD:
        return "FIXED_HOLD_B4"
    if setting.startswith("M"):
        return f"FIXED_{device}_{setting}"
    return f"FIXED_{device}_M1.00"


def _fixed_management_arms(experiment_id: str) -> list[PolicySpec]:
    """The plain fixed-management baseline plus every fixed-device comparator row."""
    arms = [
        PolicySpec(
            policy_id="FIXED_BASELINE_PLAIN",
            component=None,
            device=Device.NONE,
            setting="UNIT_NO_TARGET_NO_STOP_NO_TRAIL",
            comparator_id="FIXED_BASELINE_PLAIN",
            is_adaptive=False,
            experiment_id=experiment_id,
            fixed_hold_bars=1 if experiment_id == "SPDR-021" else 4,
            pending_expiry_bars=2 if experiment_id == "SPDR-021" else None,
        )
    ]
    for device in (Device.TARGET, Device.STOP, Device.TRAIL):
        for m in DISTANCE_MULTIPLIERS:
            setting = f"M{m:.2f}"
            arms.append(
                PolicySpec(
                    policy_id=f"FIXED_{device}_{setting}",
                    component=None,
                    device=device,
                    setting=setting,
                    comparator_id=f"FIXED_{device}_{setting}",
                    is_adaptive=False,
                    experiment_id=experiment_id,
                )
            )
    for bars in HOLD_CAPS:
        arms.append(
            PolicySpec(
                policy_id=f"FIXED_HOLD_B{bars}",
                component=None,
                device=Device.HOLD,
                setting=f"B{bars}",
                comparator_id=f"FIXED_HOLD_B{bars}",
                is_adaptive=False,
                experiment_id=experiment_id,
                fixed_hold_bars=bars,
            )
        )
    arms.append(
        PolicySpec(
            policy_id="FIXED_SIZE_UNIT",
            component=None,
            device=Device.SIZE,
            setting="UNIT",
            comparator_id="FIXED_SIZE_UNIT",
            is_adaptive=False,
            experiment_id=experiment_id,
        )
    )
    return arms


def build_management_lattice(experiment_id: str) -> tuple[PolicySpec, ...]:
    """Individual component x device arms first, then the declared bounded combinations."""
    experiment_spec(experiment_id)
    arms: list[PolicySpec] = _fixed_management_arms(experiment_id)

    for component in Component:
        for device in APPLICABLE_DEVICES[component]:
            for setting in _adaptive_setting(component, device):
                arms.append(
                    PolicySpec(
                        policy_id=f"ADP_{component}_{device}_{setting}",
                        component=component,
                        device=device,
                        setting=setting,
                        comparator_id=_comparator_id(device, setting),
                        experiment_id=experiment_id,
                    )
                )

    for distance_component, state_component in COMPONENT_COMBINATIONS:
        combination_id = f"CC_{distance_component}__{state_component}"
        if distance_component is Component.RANGE_SCALE and state_component in {
            Component.LEVEL_NOW,
            Component.LEVEL_FORECAST_K4,
            Component.LEVEL_FORECAST_K12,
        }:
            shared = [Device.TARGET, Device.STOP, Device.TRAIL, Device.HOLD, Device.SIZE]
        elif distance_component is Component.SHOCK:
            shared = [Device.TARGET, Device.STOP, Device.TRAIL, Device.HOLD, Device.SIZE]
        else:
            shared = [Device.TARGET, Device.HOLD]
        for device in shared:
            setting = f"{STATE_DISTANCE_SETTING}_ON_{distance_component}"
            if device is Device.HOLD:
                setting = STATE_HOLD_SETTING
            arms.append(
                PolicySpec(
                    policy_id=f"ADPCC_{distance_component}_{state_component}_{device}",
                    component=distance_component,
                    device=device,
                    setting=setting,
                    comparator_id=_comparator_id(device, setting),
                    combination_id=combination_id,
                    experiment_id=experiment_id,
                    adjustment_component=state_component,
                    component_role="PRIMARY_NUMERIC_SCHEDULE",
                    adjustment_role="STATE_ADJUSTMENT",
                )
            )

    for combination_id, devices in DEVICE_COMBINATIONS.items():
        for device in devices:
            if device is Device.HOLD:
                arms.append(
                    PolicySpec(
                        policy_id=f"ADPDC_{combination_id}_{device}",
                        component=None,
                        device=device,
                        setting="B4",
                        comparator_id="FIXED_HOLD_B4",
                        combination_id=combination_id,
                        is_adaptive=False,
                        experiment_id=experiment_id,
                        fixed_hold_bars=4,
                    )
                )
                continue
            arms.append(
                PolicySpec(
                    policy_id=f"ADPDC_{combination_id}_{device}",
                    component=Component.RANGE_SCALE,
                    device=device,
                    setting="M1.00",
                    comparator_id=f"FIXED_{device}_M1.00",
                    combination_id=combination_id,
                    experiment_id=experiment_id,
                )
            )
    return tuple(arms)


def materialise_crossed_arm(native: NativeArmSpec, policy: PolicySpec) -> None:
    """Always refuses: native parameters are never crossed with external management."""
    raise ValueError(
        "native parameter arms may not be crossed with management policies: "
        f"{native.native_arm_id} x {policy.policy_id}"
    )
