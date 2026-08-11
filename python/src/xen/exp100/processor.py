"""Causal, disk-backed level and raid processing for EXP-100.

All decisions made for a completed observation bar use feature values available
before that bar.  SQLite retains the live level, raid, and profile state; this
module keeps only current aggregation and feature scalars in memory.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from xen.nautilus.streaming import MemoryGuard

from .config import Exp100CellConfig
from .features import CausalVolatilityRegime, CausalWilderATR, StreamingOHLC
from .state_store import Exp100StateStore
from .tpo import TPOProfileStore
from .types import BarRecord


@dataclass
class Exp100Sinks:
    """Append-only destinations for the five EXP-100 output streams."""

    bar_marks: Any
    levels: Any
    raids: Any
    tpo_profiles: Any
    event_log: Any


class Exp100Processor:
    """Consume completed one-minute bars without retaining their history."""

    def __init__(
        self,
        config: Exp100CellConfig,
        state: Exp100StateStore,
        sinks: Exp100Sinks,
        memory_guard: MemoryGuard,
    ) -> None:
        config.validate()
        self.config = config
        self.state = state
        self.sinks = sinks
        self.memory_guard = memory_guard
        self._observations = StreamingOHLC(config.observation_minutes)
        self._references = StreamingOHLC(60 if config.confirmation_reference == "1H" else 1440)
        self._previous_reference: BarRecord | None = None
        self._atr = CausalWilderATR(config.atr_period)
        self._regime = CausalVolatilityRegime(config.regime_window)
        self._last_regime = CausalVolatilityRegime.ATR_UNDEFINED
        self._profiles = TPOProfileStore(
            state,
            value_area_mass=config.tpo_value_area,
            gap_mass=config.tpo_gap_mass,
            tight_ratio=config.tpo_tight_ratio,
        )
        self._processed_source_bars = 0
        self._completed_observations = 0
        self._finished = False

    def seed_level(self, level_id: str, *, price: float, side: str) -> None:
        """Insert an explicit level for focused processor tests only."""
        if not level_id:
            raise ValueError("level_id must be non-empty")
        if side not in {"HIGH", "LOW"}:
            raise ValueError("side must be HIGH or LOW")
        if not math.isfinite(price):
            raise ValueError("price must be finite")
        self.state.insert_level(
            {
                "level_id": level_id,
                "event_identity": self._level_identity(level_id, price, side, 0),
                "source_configuration": self.config.level_config,
                "side": side,
                "price": float(price),
                "creation_ts_ns": 0,
                "active": 1,
            }
        )

    def on_one_minute_bar(self, bar: BarRecord) -> None:
        """Accept one completed real source bar and process closed windows only."""
        if self._finished:
            raise RuntimeError("processor is finished")
        self._validate_bar(bar)
        self._processed_source_bars += 1

        observation = self._observations.update(bar)
        if observation is not None:
            self._on_observation_bar(observation)

        reference = self._references.update(bar)
        if reference is not None:
            self._on_reference_bar(reference)

        self.memory_guard.observe(
            self._processed_source_bars,
            pending_rows=self._pending_rows(),
            open_levels=self._count_active_levels(),
            open_raids=self._count_active_raids(),
            state_bytes=self._state_bytes(),
            last_timestamp=bar.ts_event_ns,
        )

    def finish(self, last_ts_ns: int | None) -> None:
        """Right-censor and emit every remaining live object exactly once."""
        if self._finished:
            return
        censor_ts = last_ts_ns
        for raid in self.state.iter_active_raids():
            endpoint_ts = censor_ts if censor_ts is not None else int(raid["sweep_ts_ns"])
            status = self._censor_status(raid)
            self._terminal_raid(raid, status=status, endpoint_ts_ns=endpoint_ts)
        for level in self.state.iter_active_levels():
            endpoint_ts = censor_ts if censor_ts is not None else int(level["creation_ts_ns"])
            row = {
                **level,
                "active": False,
                "status": "RIGHT_CENSORED",
                "endpoint_ts_ns": endpoint_ts,
                "censor_ts_ns": endpoint_ts,
            }
            self.sinks.levels.append(row)
            self._event("LEVEL_TERMINAL", endpoint_ts, level_id=level["level_id"], status=row["status"])
            self.state.delete_level(str(level["level_id"]))
        self._finished = True

    def snapshot(self) -> dict[str, int]:
        """Return bounded counters without materializing SQLite state rows."""
        return {
            "processed_source_bars": self._processed_source_bars,
            "completed_observations": self._completed_observations,
            "open_levels": self._count_active_levels(),
            "open_raids": self._count_active_raids(),
            "state_bytes": self._state_bytes(),
        }

    def _on_observation_bar(self, bar: BarRecord) -> None:
        atr_before = self._atr.value
        regime_before = self._last_regime

        for raid in self.state.iter_active_raids():
            level_price = float(raid["level_price"])
            side = str(raid["side"])
            updates: dict[str, Any] = {}
            if side == "HIGH":
                if bar.high > float(raid["max_price"]):
                    updates["max_price"] = bar.high
                    updates["max_excursion"] = bar.high - level_price
                    self._reset_or_add_profile(raid, bar, reset=True)
                else:
                    self._reset_or_add_profile(raid, bar, reset=False)
                if raid["return_ts_ns"] is None and bar.low <= level_price:
                    updates["return_ts_ns"] = bar.ts_event_ns
            else:
                if bar.low < float(raid["max_price"]):
                    updates["max_price"] = bar.low
                    updates["max_excursion"] = level_price - bar.low
                    self._reset_or_add_profile(raid, bar, reset=True)
                else:
                    self._reset_or_add_profile(raid, bar, reset=False)
                if raid["return_ts_ns"] is None and bar.high >= level_price:
                    updates["return_ts_ns"] = bar.ts_event_ns
            if updates:
                self.state.update_raid(str(raid["raid_id"]), updates)

        for level in self.state.iter_active_levels():
            level_id = str(level["level_id"])
            if self._has_active_raid(level_id):
                continue
            price = float(level["price"])
            side = str(level["side"])
            crossed = bar.high > price if side == "HIGH" else bar.low < price
            if not crossed:
                continue
            returned = bar.low <= price if side == "HIGH" else bar.high >= price
            if returned:
                raid = self._new_raid(level, bar, atr_before, regime_before, ambiguous=True)
                self._terminal_raid(
                    raid,
                    status="AMBIGUOUS_INTRABAR",
                    endpoint_ts_ns=bar.ts_event_ns,
                )
                continue
            self._new_raid(level, bar, atr_before, regime_before, ambiguous=False)

        atr_after = self._atr.update(bar)
        regime_after = self._regime.update(
            atr_after / bar.close if atr_after is not None and bar.close != 0.0 else None
        )
        self._last_regime = regime_after
        self._completed_observations += 1
        self.sinks.bar_marks.append(
            {
                "source_ts_event_ns": bar.ts_event_ns,
                "ts_event_ns": bar.ts_event_ns,
                "real_open": bar.open,
                "real_high": bar.high,
                "real_low": bar.low,
                "real_close": bar.close,
                "real_volume": bar.volume,
                "source_bars": bar.source_bars,
                "atr": atr_after,
                "regime": regime_after,
                **self.snapshot(),
            }
        )

    def _on_reference_bar(self, bar: BarRecord) -> None:
        previous = self._previous_reference
        self._previous_reference = bar
        if previous is None:
            return
        for raid in self.state.iter_active_raids():
            if bar.ts_event_ns <= int(raid["sweep_ts_ns"]):
                continue
            side = str(raid["side"])
            if raid["confirmation_ts_ns"] is None:
                if self._is_expected_reference_event(
                    side, float(raid["level_price"]), previous, bar
                ):
                    self.state.update_raid(
                        str(raid["raid_id"]),
                        {
                            "confirmation_ts_ns": bar.ts_event_ns,
                            "confirmation_method": self.config.confirmation_method,
                            "confirmation_reference": self.config.confirmation_reference,
                        },
                    )
                    self._finalize_profile(raid, bar.ts_event_ns, "CONFIRMED")
                elif self._is_opposing_reference_event(
                    side, float(raid["level_price"]), previous, bar
                ):
                    self._terminal_raid(raid, status="FAILED_BREAKOUT", endpoint_ts_ns=bar.ts_event_ns)
                continue
            if raid["return_ts_ns"] is not None and self._is_opposing_reference_event(
                side, float(raid["level_price"]), previous, bar
            ):
                self._terminal_raid(raid, status="COMPLETED", endpoint_ts_ns=bar.ts_event_ns)

    def _new_raid(
        self,
        level: dict[str, Any],
        bar: BarRecord,
        atr: float | None,
        regime: str,
        *,
        ambiguous: bool,
    ) -> dict[str, Any]:
        level_id = str(level["level_id"])
        side = str(level["side"])
        price = float(level["price"])
        prior_raid_count = self.state.prior_raid_count(level_id)
        raid_id = f"{level_id}:raid:{prior_raid_count + 1}"
        max_price = bar.high if side == "HIGH" else bar.low
        raid = {
            "raid_id": raid_id,
            "level_id": level_id,
            "event_identity": f"{level['event_identity']}|raid|{bar.ts_event_ns}|{prior_raid_count + 1}",
            "source_configuration": level["source_configuration"],
            "side": side,
            "level_price": price,
            "level_creation_ts_ns": level["creation_ts_ns"],
            "sweep_ts_ns": bar.ts_event_ns,
            "return_ts_ns": bar.ts_event_ns if ambiguous else None,
            "confirmation_ts_ns": None,
            "endpoint_ts_ns": None,
            "censor_ts_ns": None,
            "max_price": max_price,
            "max_excursion": (max_price - price) if side == "HIGH" else (price - max_price),
            "prior_raid_count": prior_raid_count,
            "raid_atr": atr,
            "raid_regime": regime,
            "profile_generation": None,
            "profile_finalized": False,
            "profile_undefined_reason": "AMBIGUOUS_INTRABAR" if ambiguous else None,
            "active": 1,
        }
        if not ambiguous and atr is not None and atr > 0.0 and math.isfinite(atr):
            generation = self._profiles.start(raid_id, bar.ts_event_ns, max_price, atr)
            raid["profile_generation"] = generation
            self._profiles.add_bar(raid_id, generation, bar)
        elif not ambiguous:
            raid["profile_undefined_reason"] = "ATR_UNDEFINED"
        self.state.insert_raid(raid)
        self._event("RAID_STARTED", bar.ts_event_ns, raid_id=raid_id, level_id=level_id)
        return raid

    def _reset_or_add_profile(
        self, raid: dict[str, Any], bar: BarRecord, *, reset: bool
    ) -> None:
        if raid.get("profile_finalized", False):
            return
        generation = raid.get("profile_generation")
        if not isinstance(generation, int):
            return
        if reset:
            generation = self._profiles.reset(str(raid["raid_id"]), float(raid["max_price"]), bar.ts_event_ns)
            self.state.update_raid(str(raid["raid_id"]), {"profile_generation": generation})
        self._profiles.add_bar(str(raid["raid_id"]), generation, bar)

    def _terminal_raid(self, raid: dict[str, Any], *, status: str, endpoint_ts_ns: int) -> None:
        raid_id = str(raid["raid_id"])
        generation = raid.get("profile_generation")
        if not raid.get("profile_finalized", False):
            self._finalize_profile(raid, endpoint_ts_ns, status)
        row = {
            **raid,
            "active": False,
            "status": status,
            "primary_completed": status == "COMPLETED",
            "endpoint_ts_ns": endpoint_ts_ns,
            "censor_ts_ns": endpoint_ts_ns if status.startswith("RIGHT_CENSORED_") else None,
        }
        self.sinks.raids.append(row)
        self._event("RAID_TERMINAL", endpoint_ts_ns, raid_id=raid_id, level_id=raid["level_id"], status=status)
        if isinstance(generation, int) and not raid.get("profile_finalized", False):
            self._delete_profile_state(raid_id)
        self.state.delete_raid(raid_id)

    def _finalize_profile(self, raid: dict[str, Any], end_ts_ns: int, raid_status: str) -> None:
        """Emit the profile at its confirmation boundary, then release its live rows."""
        raid_id = str(raid["raid_id"])
        generation = raid.get("profile_generation")
        if isinstance(generation, int):
            profile = self._profiles.finalize(raid_id, generation, end_ts_ns)
            self._delete_profile_state(raid_id)
        else:
            profile = self._undefined_profile(
                raid_id, end_ts_ns, str(raid.get("profile_undefined_reason") or raid_status)
            )
        gap_mask = profile.get("gap_mask")
        if isinstance(gap_mask, dict):
            profile["gap_mask"] = {
                key: value for key, value in gap_mask.items() if key != "store_path"
            }
        profile.update({"raid_status": raid_status, "endpoint_ts_ns": end_ts_ns})
        self.sinks.tpo_profiles.append(profile)
        self._event("TPO_PROFILE_TERMINAL", end_ts_ns, raid_id=raid_id, status=profile["profile_status"])
        if self._raid_is_active(raid_id):
            self.state.update_raid(raid_id, {"profile_finalized": True})

    def _delete_profile_state(self, raid_id: str) -> None:
        """Discard terminal profile rows after their terminal profile has been emitted."""
        connection = self.state._connection
        connection.execute("DELETE FROM profile_bins WHERE raid_id = ?", (raid_id,))
        connection.execute("DELETE FROM profile_gap_bins WHERE raid_id = ?", (raid_id,))
        connection.execute("DELETE FROM profile_state WHERE raid_id = ?", (raid_id,))
        connection.execute("DELETE FROM profile_meta WHERE raid_id = ?", (raid_id,))
        connection.commit()

    def _censor_status(self, raid: dict[str, Any]) -> str:
        if raid["return_ts_ns"] is None:
            return "RIGHT_CENSORED_EXCURSION"
        if raid["confirmation_ts_ns"] is None:
            return "RIGHT_CENSORED_CONFIRMATION"
        return "RIGHT_CENSORED_ENDPOINT"

    def _is_expected_reference_event(
        self, side: str, price: float, previous: BarRecord, bar: BarRecord
    ) -> bool:
        if self.config.confirmation_method == "LEVEL_CLOSE":
            return bar.close < price if side == "HIGH" else bar.close > price
        return bar.close < previous.low if side == "HIGH" else bar.close > previous.high

    def _is_opposing_reference_event(
        self, side: str, price: float, previous: BarRecord, bar: BarRecord
    ) -> bool:
        if self.config.confirmation_method == "LEVEL_CLOSE":
            return bar.close > price if side == "HIGH" else bar.close < price
        return bar.close > previous.high if side == "HIGH" else bar.close < previous.low

    @staticmethod
    def _validate_bar(bar: BarRecord) -> None:
        if bar.source_bars <= 0:
            raise ValueError("source_bars must be positive")
        if bar.low > bar.high:
            raise ValueError("bar low cannot exceed high")
        if not all(math.isfinite(value) for value in (bar.open, bar.high, bar.low, bar.close, bar.volume)):
            raise ValueError("bar OHLCV values must be finite")

    def _has_active_raid(self, level_id: str) -> bool:
        return any(str(raid["level_id"]) == level_id for raid in self.state.iter_active_raids())

    def _count_active_levels(self) -> int:
        return sum(1 for _ in self.state.iter_active_levels())

    def _count_active_raids(self) -> int:
        return sum(1 for _ in self.state.iter_active_raids())

    def _pending_rows(self) -> int:
        return sum(int(getattr(writer, "pending_rows", 0)) for writer in vars(self.sinks).values())

    def _state_bytes(self) -> int:
        path = Path(self.state.path)
        return path.stat().st_size if path.exists() else 0

    def _raid_is_active(self, raid_id: str) -> bool:
        return any(str(raid["raid_id"]) == raid_id for raid in self.state.iter_active_raids())

    def _level_identity(self, level_id: str, price: float, side: str, creation_ts_ns: int) -> str:
        return f"{self.config.level_config}|{level_id}|{side}|{price:.17g}|{creation_ts_ns}"

    def _undefined_profile(self, raid_id: str, end_ts_ns: int, reason: str) -> dict[str, Any]:
        return {
            "raid_id": raid_id,
            "profile_generation": None,
            "profile_start_ts_ns": None,
            "profile_end_ts_ns": end_ts_ns,
            "bin_width": None,
            "bracket_count": 0,
            "poc": None,
            "val": None,
            "vah": None,
            "va_count": 0,
            "va_mass": None,
            "va_mask": None,
            "gap_mask": None,
            "gap_span": None,
            "va_width": None,
            "tight_gap": False,
            "tpo_total": None,
            "tpo_conservation_ok": False,
            "profile_status": "UNDEFINED",
            "undefined_reason": reason,
        }

    def _event(self, event_type: str, ts_event_ns: int, **fields: Any) -> None:
        self.sinks.event_log.append({"event_type": event_type, "ts_event_ns": ts_event_ns, **fields})
