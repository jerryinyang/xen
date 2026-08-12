"""Causal, disk-backed level and raid processing for EXP-100.

Only the current observation window (at most 60 source minutes), feature
scalars, and one completed reference bar live in Python. SQLite owns every
active level, raid, and TPO profile.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from xen.nautilus.streaming import MemoryGuard

from .config import Exp100CellConfig
from .features import CausalVolatilityRegime, CausalWilderATR, StreamingOHLC
from .levels import LevelCatalogue, LevelSpec
from .state_store import Exp100StateStore
from .tpo import TPOProfileStore
from .types import BarRecord

MINUTE_NS = 60_000_000_000


@dataclass
class Exp100Sinks:
    """Append-only destinations for the five EXP-100 output streams."""

    bar_marks: Any
    levels: Any
    raids: Any
    tpo_profiles: Any
    event_log: Any


class Exp100Processor:
    """Consume ordered observed source minutes without retaining history."""

    def __init__(
        self,
        config: Exp100CellConfig,
        state: Exp100StateStore,
        sinks: Exp100Sinks,
        memory_guard: MemoryGuard,
        *,
        auto_catalogue: bool = True,
    ) -> None:
        config.validate()
        self.config = config
        self.state = state
        self.sinks = sinks
        self.memory_guard = memory_guard
        self._observations = StreamingOHLC(config.observation_minutes)
        self._references = StreamingOHLC(
            60 if config.confirmation_reference == "1H" else 1440
        )
        self._window: deque[BarRecord] = deque(maxlen=config.observation_minutes)
        self._previous_reference: BarRecord | None = None
        self._last_source_ts_ns: int | None = None
        self._atr = CausalWilderATR(config.atr_period)
        self._regime = CausalVolatilityRegime(config.regime_window)
        self._last_regime = CausalVolatilityRegime.ATR_UNDEFINED
        self._profiles = TPOProfileStore(
            state,
            value_area_mass=config.tpo_value_area,
            gap_mass=config.tpo_gap_mass,
            tight_ratio=config.tpo_tight_ratio,
        )
        self._catalogue = LevelCatalogue(config.level_config, config.observation_minutes)
        self._auto_catalogue = auto_catalogue
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
        self._insert_level(
            LevelSpec(
                level_id=level_id,
                side=side,
                price=float(price),
                creation_ts_ns=0,
                anchor_key="seed",
            ),
            supersede_same_side=False,
        )

    def on_one_minute_bar(self, bar: BarRecord) -> None:
        """Accept one real observed source minute and process closed windows."""
        if self._finished:
            raise RuntimeError("processor is finished")
        self._validate_source_bar(bar)
        self._last_source_ts_ns = bar.ts_event_ns
        self._processed_source_bars += 1
        self._window.append(bar)
        with self.state.source_bar_transaction():
            # Existing open raids receive this minute first (profile + swing).
            self._update_active_raids_from_source(bar)
            # Raid start / return / same-1m ambiguity are decided on source minutes.
            self._process_source_raid_state(bar)

            observation = self._observations.update(bar)
            if observation is not None:
                self._on_observation_bar(observation)
                self._window.clear()
                if self._auto_catalogue:
                    for spec in self._catalogue.on_observation_bar(observation):
                        self._insert_level(spec, supersede_same_side=True)

            reference = self._references.update(bar)
            if reference is not None:
                self._on_reference_bar(reference)

            if self._auto_catalogue:
                for spec in self._catalogue.on_source_minute(bar):
                    self._insert_level(spec, supersede_same_side=True)

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
        for raid in self.state.iter_active_raids():
            endpoint_ts = last_ts_ns if last_ts_ns is not None else int(raid["sweep_ts_ns"])
            self._terminal_raid(raid, self._censor_status(raid), endpoint_ts)
        for level in self.state.iter_active_levels():
            endpoint_ts = last_ts_ns if last_ts_ns is not None else int(level["creation_ts_ns"])
            row = {
                **level,
                "active": False,
                "status": "RIGHT_CENSORED",
                "endpoint_ts_ns": endpoint_ts,
                "censor_ts_ns": endpoint_ts,
            }
            self.sinks.levels.append(row)
            self._event(
                "LEVEL_TERMINAL", endpoint_ts, level_id=level["level_id"], status=row["status"]
            )
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

    def _update_active_raids_from_source(self, bar: BarRecord) -> None:
        for raid in self.state.iter_active_raids():
            current = self._apply_source_to_profile(raid, bar)
            if current.get("confirmation_ts_ns") is not None:
                self._update_swing_extreme(current, bar)
            if current["return_ts_ns"] is not None:
                continue
            price = float(current["level_price"])
            returned = (
                bar.low <= price if current["side"] == "HIGH" else bar.high >= price
            )
            if returned:
                self.state.update_raid(
                    str(current["raid_id"]), {"return_ts_ns": bar.ts_event_ns}
                )

    def _update_swing_extreme(self, raid: dict[str, Any], bar: BarRecord) -> None:
        """Track the post-confirmation favorable extreme for swing magnitude."""
        side = str(raid["side"])
        extreme = bar.low if side == "HIGH" else bar.high
        current_extreme = raid.get("swing_extreme")
        if current_extreme is None:
            updated = extreme
        elif side == "HIGH":
            updated = min(float(current_extreme), extreme)
        else:
            updated = max(float(current_extreme), extreme)
        if current_extreme is None or updated != float(current_extreme):
            self.state.update_raid(str(raid["raid_id"]), {"swing_extreme": updated})
            raid["swing_extreme"] = updated

    def _apply_source_to_profile(self, raid: dict[str, Any], bar: BarRecord) -> dict[str, Any]:
        """Apply one source minute once to a live profile, resetting at a new max."""
        if raid.get("profile_finalized", False):
            return raid
        generation = raid.get("profile_generation")
        if not isinstance(generation, int):
            return raid
        side = str(raid["side"])
        extreme = bar.high if side == "HIGH" else bar.low
        is_new_max = extreme > float(raid["max_price"]) if side == "HIGH" else extreme < float(raid["max_price"])
        current = dict(raid)
        if is_new_max:
            generation = self._profiles.reset(str(raid["raid_id"]), extreme, bar.ts_event_ns)
            level_price = float(raid["level_price"])
            updates = {
                "profile_generation": generation,
                "max_price": extreme,
                "max_excursion": (
                    extreme - level_price if side == "HIGH" else level_price - extreme
                ),
                "excursion_ts_ns": bar.ts_event_ns,
                "excursion_atr": self._atr.value,
                "excursion_regime": self._last_regime,
            }
            current.update(updates)
            self.state.update_raid(str(raid["raid_id"]), updates)
        self._profiles.add_bar(str(raid["raid_id"]), generation, bar)
        return current

    def _process_source_raid_state(self, bar: BarRecord) -> None:
        """Detect strict 1m excursion, inclusive return, and same-1m ambiguity."""
        atr = self._atr.value
        regime = self._last_regime

        for level in self.state.iter_active_levels():
            level_id = str(level["level_id"])
            price = float(level["price"])
            side = str(level["side"])
            current_beyond = bar.high > price if side == "HIGH" else bar.low < price
            returned = bar.low <= price if side == "HIGH" else bar.high >= price
            beyond = current_beyond and not returned
            previous_beyond = bool(level.get("beyond", False))
            self.state.update_level(
                level_id,
                {
                    "beyond": beyond,
                    "last_source_ts_ns": bar.ts_event_ns,
                    "last_observation_ts_ns": bar.ts_event_ns,
                },
            )
            if not current_beyond or previous_beyond:
                continue
            if returned:
                raid = self._new_raid(level, bar, atr, regime, True)
                self._terminal_raid(raid, "AMBIGUOUS_INTRABAR", bar.ts_event_ns)
            else:
                self._new_raid(level, bar, atr, regime, False)

    def _on_observation_bar(self, bar: BarRecord) -> None:
        """Update causal ATR/regime and emit one observation bar mark."""
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

    def _new_raid(
        self,
        level: dict[str, Any],
        source_bar: BarRecord,
        atr: float | None,
        regime: str,
        ambiguous: bool,
    ) -> dict[str, Any]:
        level_id = str(level["level_id"])
        side = str(level["side"])
        price = float(level["price"])
        initial_extreme = source_bar.high if side == "HIGH" else source_bar.low
        prior_raid_count = self.state.prior_raid_count(level_id)
        raid_id = f"{level_id}:raid:{prior_raid_count + 1}"
        max_excursion = (
            initial_extreme - price if side == "HIGH" else price - initial_extreme
        )
        raid = {
            "raid_id": raid_id,
            "level_id": level_id,
            "event_identity": (
                f"{level['event_identity']}|raid|{source_bar.ts_event_ns}|{prior_raid_count + 1}"
            ),
            "source_configuration": level["source_configuration"],
            "side": side,
            "level_price": price,
            "level_creation_ts_ns": level["creation_ts_ns"],
            "sweep_ts_ns": source_bar.ts_event_ns,
            "first_excursion_ts_ns": source_bar.ts_event_ns,
            "return_ts_ns": source_bar.ts_event_ns if ambiguous else None,
            "confirmation_ts_ns": None,
            "endpoint_ts_ns": None,
            "censor_ts_ns": None,
            "max_price": initial_extreme,
            "max_excursion": max_excursion,
            "prior_raid_count": prior_raid_count,
            "raid_atr": atr,
            "raid_regime": regime,
            "excursion_ts_ns": source_bar.ts_event_ns,
            "excursion_atr": atr,
            "excursion_regime": regime,
            "confirmation_atr": None,
            "confirmation_regime": None,
            "endpoint_atr": None,
            "endpoint_regime": None,
            "profile_generation": None,
            "profile_finalized": False,
            "profile_undefined_reason": "AMBIGUOUS_INTRABAR" if ambiguous else None,
            "active": 1,
        }
        if not ambiguous and atr is not None and atr > 0.0 and math.isfinite(atr):
            raid["profile_generation"] = self._profiles.start(
                raid_id, source_bar.ts_event_ns, initial_extreme, atr
            )
        elif not ambiguous:
            raid["profile_undefined_reason"] = "ATR_UNDEFINED"
        self.state.insert_raid(raid)
        self._event(
            "RAID_STARTED", source_bar.ts_event_ns, raid_id=raid_id, level_id=level_id
        )
        if isinstance(raid["profile_generation"], int):
            return self._apply_source_to_profile(raid, source_bar)
        return raid

    def _on_reference_bar(self, bar: BarRecord) -> None:
        previous = self._previous_reference
        self._previous_reference = bar
        if previous is None:
            return
        expected = self._latest_active_raid(
            lambda raid: raid["confirmation_ts_ns"] is None
            and raid["return_ts_ns"] is not None
            and bar.ts_event_ns > int(raid["sweep_ts_ns"])
            and self._is_expected_reference_event(str(raid["side"]), previous, bar)
        )
        opposing_unconfirmed = self._latest_active_raid(
            lambda raid: raid["confirmation_ts_ns"] is None
            and raid["return_ts_ns"] is not None
            and bar.ts_event_ns > int(raid["sweep_ts_ns"])
            and self._is_opposing_reference_event(str(raid["side"]), previous, bar)
        )
        endpoint = self._latest_active_raid(
            lambda raid: raid["confirmation_ts_ns"] is not None
            and bool(raid.get("primary_attribution", False))
            and bar.ts_event_ns > int(raid["confirmation_ts_ns"])
            and self._is_opposing_reference_event(str(raid["side"]), previous, bar)
        )
        if expected is not None:
            side = str(expected["side"])
            initial_extreme = bar.low if side == "HIGH" else bar.high
            updates = {
                "confirmation_ts_ns": bar.ts_event_ns,
                "confirmation_method": self.config.confirmation_method,
                "confirmation_reference": self.config.confirmation_reference,
                "confirmation_atr": self._atr.value,
                "confirmation_regime": self._last_regime,
                # Higher-degree confirmation levels = previous completed reference
                # period high/low (not the swept raid level price).
                "confirmation_level_high": float(previous.high),
                "confirmation_level_low": float(previous.low),
                "confirmation_price": float(bar.close),
                "swing_extreme": float(initial_extreme),
                "primary_attribution": True,
            }
            self.state.update_raid(str(expected["raid_id"]), updates)
            self._finalize_profile({**expected, **updates}, bar.ts_event_ns, "CONFIRMED")
        if opposing_unconfirmed is not None:
            self._terminal_raid(opposing_unconfirmed, "FAILED_BREAKOUT", bar.ts_event_ns)
        if endpoint is not None:
            self._terminal_raid(endpoint, "COMPLETED", bar.ts_event_ns)

    def _latest_active_raid(
        self, eligible: Callable[[dict[str, Any]], bool]
    ) -> dict[str, Any] | None:
        latest: dict[str, Any] | None = None
        for raid in self.state.iter_active_raids():
            if not eligible(raid):
                continue
            if latest is None or (int(raid["sweep_ts_ns"]), str(raid["raid_id"])) > (
                int(latest["sweep_ts_ns"]),
                str(latest["raid_id"]),
            ):
                latest = raid
        return latest

    def _terminal_raid(self, raid: dict[str, Any], status: str, endpoint_ts_ns: int) -> None:
        current = dict(raid)
        if not current.get("profile_finalized", False):
            self._finalize_profile(current, endpoint_ts_ns, status)
            current["profile_finalized"] = True
        confirmation_ts_ns = current.get("confirmation_ts_ns")
        raid_atr = current.get("raid_atr")
        level_price = float(current["level_price"])
        if current.get("max_excursion") is not None:
            max_excursion = float(current["max_excursion"])
        else:
            max_price = float(current.get("max_price", level_price))
            max_excursion = (
                max_price - level_price
                if str(current["side"]) == "HIGH"
                else level_price - max_price
            )
        swing_atr = None
        max_excursion_atr = None
        max_excursion_bps = None
        strong_move = None
        swing_price = None
        swing_bps = None
        if level_price != 0.0 and math.isfinite(level_price):
            max_excursion_bps = (max_excursion / abs(level_price)) * 10_000.0
        if isinstance(raid_atr, (int, float)) and math.isfinite(float(raid_atr)) and float(raid_atr) > 0.0:
            atr = float(raid_atr)
            max_excursion_atr = max_excursion / atr
            swing_extreme = current.get("swing_extreme")
            if swing_extreme is not None and math.isfinite(float(swing_extreme)):
                if str(current["side"]) == "HIGH":
                    swing_price = level_price - float(swing_extreme)
                else:
                    swing_price = float(swing_extreme) - level_price
                swing_atr = swing_price / atr
                if level_price != 0.0 and math.isfinite(level_price):
                    swing_bps = (swing_price / abs(level_price)) * 10_000.0
                strong_move = bool(swing_atr > max_excursion_atr)
        duration_ns = None
        if confirmation_ts_ns is not None:
            duration_ns = endpoint_ts_ns - int(confirmation_ts_ns)
        current.update(
            {
                "active": False,
                "status": status,
                "primary_completed": status == "COMPLETED",
                "endpoint_ts_ns": endpoint_ts_ns,
                "censor_ts_ns": endpoint_ts_ns if status.startswith("RIGHT_CENSORED_") else None,
                "endpoint_atr": self._atr.value,
                "endpoint_regime": self._last_regime,
                "archive_symbol": self.config.archive_symbol,
                "timeframe": f"{self.config.observation_minutes}m",
                "config": self.config.level_config,
                "max_excursion": max_excursion,
                "max_excursion_bps": max_excursion_bps,
                "max_excursion_atr": max_excursion_atr,
                "swing_price": swing_price,
                "swing_bps": swing_bps,
                "swing_atr": swing_atr,
                "strong_move": strong_move,
                "duration_ns": duration_ns,
            }
        )
        self.sinks.raids.append(current)
        self._event(
            "RAID_TERMINAL",
            endpoint_ts_ns,
            raid_id=current["raid_id"],
            level_id=current["level_id"],
            status=status,
        )
        self.state.delete_raid(str(current["raid_id"]))

    def _finalize_profile(self, raid: dict[str, Any], end_ts_ns: int, raid_status: str) -> None:
        """Append terminal profile output before atomically deleting its live state."""
        raid_id = str(raid["raid_id"])
        generation = raid.get("profile_generation")
        if isinstance(generation, int):
            profile = self._profiles.finalize(raid_id, generation, end_ts_ns)
        else:
            profile = self._undefined_profile(
                raid_id,
                end_ts_ns,
                str(raid.get("profile_undefined_reason") or raid_status),
            )
        gap_mask = profile.get("gap_mask")
        if isinstance(gap_mask, dict):
            profile["gap_mask"] = {
                key: value for key, value in gap_mask.items() if key != "store_path"
            }
        profile.update({"raid_status": raid_status, "endpoint_ts_ns": end_ts_ns})
        self.sinks.tpo_profiles.append(profile)
        self.state.clear_profile_state(raid_id)
        self.state.update_raid(raid_id, {"profile_finalized": True})
        self._event(
            "TPO_PROFILE_TERMINAL",
            end_ts_ns,
            raid_id=raid_id,
            status=profile["profile_status"],
        )

    @staticmethod
    def _censor_status(raid: dict[str, Any]) -> str:
        if raid["return_ts_ns"] is None:
            return "RIGHT_CENSORED_EXCURSION"
        if raid["confirmation_ts_ns"] is None:
            return "RIGHT_CENSORED_CONFIRMATION"
        return "RIGHT_CENSORED_ENDPOINT"

    def _is_expected_reference_event(
        self, side: str, previous: BarRecord, bar: BarRecord
    ) -> bool:
        """Return True when the completed reference bar confirms expected-side move.

        ``BREAKOUT_BAR`` uses the previous reference bar extreme pattern.
        ``LEVEL_CLOSE`` uses the same previous completed confirmation-reference
        high/low as the higher-degree liquidity levels — never the swept raid
        level price. Numeric overlap with the breakout-bar extremes is disclosed
        by retaining both confirmation methods as separate strata.
        """
        if self.config.confirmation_method == "LEVEL_CLOSE":
            return (
                bar.close < previous.low if side == "HIGH" else bar.close > previous.high
            )
        return bar.close < previous.low if side == "HIGH" else bar.close > previous.high

    def _is_opposing_reference_event(
        self, side: str, previous: BarRecord, bar: BarRecord
    ) -> bool:
        if self.config.confirmation_method == "LEVEL_CLOSE":
            return (
                bar.close > previous.high if side == "HIGH" else bar.close < previous.low
            )
        return bar.close > previous.high if side == "HIGH" else bar.close < previous.low

    def _insert_level(self, spec: LevelSpec, *, supersede_same_side: bool) -> None:
        """Insert a catalogue level, optionally superseding unraided same-side levels."""
        if supersede_same_side:
            self._supersede_unraided_levels(side=spec.side, endpoint_ts_ns=spec.creation_ts_ns)
        self.state.insert_level(
            {
                "level_id": spec.level_id,
                "event_identity": self._level_identity(
                    spec.level_id, spec.price, spec.side, spec.creation_ts_ns
                ),
                "source_configuration": self.config.level_config,
                "side": spec.side,
                "price": float(spec.price),
                "creation_ts_ns": int(spec.creation_ts_ns),
                "anchor_key": spec.anchor_key,
                "beyond": False,
                "active": 1,
            }
        )
        self._event(
            "LEVEL_CREATED",
            spec.creation_ts_ns,
            level_id=spec.level_id,
            side=spec.side,
            price=spec.price,
        )

    def _supersede_unraided_levels(self, *, side: str, endpoint_ts_ns: int) -> None:
        """Emit SUPERSEDED_NO_RAID for same-side levels with no unresolved raid."""
        open_raid_levels = {
            str(raid["level_id"]) for raid in self.state.iter_active_raids()
        }
        for level in list(self.state.iter_active_levels()):
            if str(level["side"]) != side:
                continue
            level_id = str(level["level_id"])
            if level_id in open_raid_levels:
                continue
            row = {
                **level,
                "active": False,
                "status": "SUPERSEDED_NO_RAID",
                "endpoint_ts_ns": endpoint_ts_ns,
                "censor_ts_ns": None,
            }
            self.sinks.levels.append(row)
            self._event(
                "LEVEL_TERMINAL",
                endpoint_ts_ns,
                level_id=level_id,
                status=row["status"],
            )
            self.state.delete_level(level_id)

    def _validate_source_bar(self, bar: BarRecord) -> None:
        if bar.source_bars != 1:
            raise ValueError("source_bars must equal 1 for a source minute")
        if bar.ts_event_ns % MINUTE_NS != 0:
            raise ValueError("source timestamp must be minute aligned")
        if self._last_source_ts_ns is not None and bar.ts_event_ns <= self._last_source_ts_ns:
            raise ValueError("source timestamps must be strictly increasing")
        if bar.low > bar.high:
            raise ValueError("bar low cannot exceed high")
        if not all(
            math.isfinite(value)
            for value in (bar.open, bar.high, bar.low, bar.close, bar.volume)
        ):
            raise ValueError("bar OHLCV values must be finite")

    def _count_active_levels(self) -> int:
        return sum(1 for _ in self.state.iter_active_levels())

    def _count_active_raids(self) -> int:
        return self.state.count_active_raids()

    def _pending_rows(self) -> int:
        return sum(
            int(getattr(writer, "pending_rows", 0)) for writer in vars(self.sinks).values()
        )

    def _state_bytes(self) -> int:
        path = Path(self.state.path)
        return path.stat().st_size if path.exists() else 0

    def _level_identity(self, level_id: str, price: float, side: str, creation_ts_ns: int) -> str:
        return f"{self.config.level_config}|{level_id}|{side}|{price:.17g}|{creation_ts_ns}"

    @staticmethod
    def _undefined_profile(raid_id: str, end_ts_ns: int, reason: str) -> dict[str, Any]:
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
        self.sinks.event_log.append(
            {"event_type": event_type, "ts_event_ns": ts_event_ns, **fields}
        )
