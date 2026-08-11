"""Validated, deterministic configuration for one EXP-100 cell."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

VENUES = frozenset({"BYBIT", "CTRADER"})
OBSERVATION_MINUTES = frozenset({15, 30, 60})
CONFIRMATION_METHODS = frozenset({"BREAKOUT_BAR", "LEVEL_CLOSE"})
CONFIRMATION_REFERENCES = frozenset({"1H", "1D"})

# These are the independent level strata frozen by the liquidity-sweep
# checkpoint.  A cell processes one value at a time; coincident prices remain
# distinct because their source configuration is part of the identity.
LEVEL_CONFIGS = frozenset(
    {
        "PREVIOUS_1H",
        "PREVIOUS_4H",
        "PREVIOUS_1D",
        "PREVIOUS_1W",
        "PREVIOUS_ASIA",
        "PREVIOUS_EUROPE",
        "PREVIOUS_AMERICA",
        "ROLLING_16",
        "ROLLING_32",
        "ROLLING_64",
        "ROLLING_128",
        "ROLLING_256",
    }
)


@dataclass(frozen=True, slots=True)
class Exp100CellConfig:
    """Immutable configuration for one venue/instrument/timeframe cell."""

    venue: str
    archive_symbol: str
    instrument_id: str
    observation_minutes: int
    confirmation_method: str
    confirmation_reference: str
    level_config: str
    atr_period: int = 14
    regime_window: int = 252
    tpo_value_area: float = 0.70
    tpo_gap_mass: float = 0.30
    tpo_tight_ratio: float = 0.30

    def validate(self) -> None:
        """Raise ``ValueError`` unless all fields match the frozen design."""
        if self.venue not in VENUES:
            raise ValueError(f"venue must be one of {sorted(VENUES)}, got {self.venue!r}")
        for field_name in ("archive_symbol", "instrument_id"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if self.observation_minutes not in OBSERVATION_MINUTES:
            raise ValueError(
                "observation_minutes must be one of "
                f"{sorted(OBSERVATION_MINUTES)}, got {self.observation_minutes!r}"
            )
        if self.confirmation_method not in CONFIRMATION_METHODS:
            raise ValueError(
                "confirmation_method must be one of "
                f"{sorted(CONFIRMATION_METHODS)}, got {self.confirmation_method!r}"
            )
        if self.confirmation_reference not in CONFIRMATION_REFERENCES:
            raise ValueError(
                "confirmation_reference must be one of "
                f"{sorted(CONFIRMATION_REFERENCES)}, got {self.confirmation_reference!r}"
            )
        expected_reference = "1H" if self.observation_minutes in {15, 30} else "1D"
        if self.confirmation_reference != expected_reference:
            raise ValueError(
                f"observation_minutes={self.observation_minutes} requires "
                f"confirmation_reference={expected_reference}"
            )
        if self.level_config not in LEVEL_CONFIGS:
            raise ValueError(
                f"level_config must be one of {sorted(LEVEL_CONFIGS)}, "
                f"got {self.level_config!r}"
            )
        if self.atr_period != 14:
            raise ValueError("atr_period is frozen at 14")
        if self.regime_window != 252:
            raise ValueError("regime_window is frozen at 252")
        if self.tpo_value_area != 0.70:
            raise ValueError("tpo_value_area is frozen at 0.70")
        if self.tpo_gap_mass != 0.30:
            raise ValueError("tpo_gap_mass is frozen at 0.30")
        if self.tpo_tight_ratio != 0.30:
            raise ValueError("tpo_tight_ratio is frozen at 0.30")

    def to_dict(self) -> dict[str, Any]:
        """Return fields in declaration order after validating the config."""
        self.validate()
        return asdict(self)

    def serialize(self) -> str:
        """Return a stable compact JSON representation for hashing and metadata."""
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    def to_json(self) -> str:
        """Compatibility alias for :meth:`serialize`."""
        return self.serialize()
