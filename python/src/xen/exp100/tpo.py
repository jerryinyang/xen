"""Online, disk-backed TPO profile construction for EXP-100."""

from __future__ import annotations

import math
from decimal import Decimal, ROUND_FLOOR
from typing import Any, Iterator

from .state_store import Exp100StateStore
from .types import BarRecord


class TPOProfileStore:
    """Maintain one sparse fixed-width TPO profile per active raid."""

    def __init__(
        self,
        store: Exp100StateStore,
        *,
        value_area_mass: float = 0.70,
        gap_mass: float = 0.30,
        tight_ratio: float = 0.30,
    ) -> None:
        self.store = store
        self.value_area_mass = self._mass("value_area_mass", value_area_mass)
        self.gap_mass = self._mass("gap_mass", gap_mass)
        self.tight_ratio = self._mass("tight_ratio", tight_ratio)

    @staticmethod
    def _mass(name: str, value: float) -> float:
        if not math.isfinite(value) or not 0.0 < value <= 1.0:
            raise ValueError(f"{name} must be finite and in (0, 1]")
        return float(value)

    @staticmethod
    def _positive_finite(name: str, value: float) -> float:
        if not math.isfinite(value) or value <= 0.0:
            raise ValueError(f"{name} must be finite and positive")
        return float(value)

    @staticmethod
    def _finite(name: str, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite")
        return float(value)

    def start(
        self,
        raid_id: str,
        start_ts_ns: int,
        excursion_price: float,
        atr_unit: float,
    ) -> int:
        """Start generation one with a bin width frozen from the causal ATR."""
        self._finite("excursion_price", excursion_price)
        atr_decimal = Decimal(str(self._positive_finite("atr_unit", atr_unit)))
        bin_width = float(Decimal("0.10") * atr_decimal)
        return self.store.start_profile_generation(raid_id, start_ts_ns, bin_width)

    def add_bar(self, raid_id: str, generation: int, bar: BarRecord) -> None:
        """Apply one closed one-minute bar to each directly intersected bin."""
        state = self.store.get_profile_state(raid_id, generation)
        if state is None:
            raise KeyError((raid_id, generation))
        low = self._finite("bar.low", bar.low)
        high = self._finite("bar.high", bar.high)
        if low > high:
            raise ValueError("bar low cannot exceed high")
        bin_width = float(state["bin_width"])
        low_bin_index = self._bin_index(low, bin_width)
        high_bin_index = self._bin_index(high, bin_width)
        self.store.increment_profile_bin_range(
            raid_id, generation, low_bin_index, high_bin_index
        )

    def reset(self, raid_id: str, new_max_price: float, ts_ns: int) -> int:
        """Replace the active profile without reconstructing historical bars."""
        self._finite("new_max_price", new_max_price)
        state = self._current_profile_state(raid_id)
        return self.store.reset_profile_generation(
            raid_id, ts_ns, float(state["bin_width"])
        )

    def finalize(self, raid_id: str, generation: int, end_ts_ns: int) -> dict[str, Any]:
        """Derive the profile using cursor passes and bounded point queries only."""
        state = self.store.get_profile_state(raid_id, generation)
        if state is None:
            return self._undefined(raid_id, generation, end_ts_ns, None, "PROFILE_NOT_FOUND")

        bin_width = float(state["bin_width"])
        bracket_count = int(state["bracket_count"])
        expected_total = int(state["expected_tpo_total"])
        total, low_index, high_index, poc_index, poc_count = self._summary(
            raid_id, generation
        )
        if total == 0:
            return self._undefined(
                raid_id,
                generation,
                end_ts_ns,
                state,
                "EMPTY_PROFILE",
                tpo_total=0,
                conservation_ok=expected_total == 0,
            )
        if low_index is None or high_index is None or poc_index is None:
            return self._undefined(
                raid_id,
                generation,
                end_ts_ns,
                state,
                "INVALID_PROFILE_BINS",
                tpo_total=total,
                conservation_ok=False,
            )

        va_low, va_high, va_count = self._value_area(
            raid_id,
            generation,
            low_index,
            high_index,
            poc_index,
            poc_count,
            total,
        )
        if va_low == va_high:
            return self._undefined(
                raid_id,
                generation,
                end_ts_ns,
                state,
                "GAP_UNDEFINED",
                tpo_total=total,
                conservation_ok=total == expected_total,
            )
        val = va_low * bin_width
        vah = (va_high + 1) * bin_width
        va_width = vah - val
        gap_span = self._gap_span(
            raid_id, generation, va_low, va_high, va_count, bin_width
        )
        if gap_span is None or va_width <= 0.0:
            return self._undefined(
                raid_id,
                generation,
                end_ts_ns,
                state,
                "GAP_UNDEFINED",
                tpo_total=total,
                conservation_ok=total == expected_total,
            )
        gap_span_value, gap_mask = gap_span
        conservation_ok = total == expected_total
        # Bin width is frozen at 0.10 × ATR_unit when the profile starts.
        atr_unit = bin_width / 0.10
        gap_span_atr = gap_span_value / atr_unit if atr_unit > 0.0 else None
        gap_span_va = gap_span_value / va_width if va_width > 0.0 else None
        return {
            "raid_id": raid_id,
            "profile_generation": generation,
            "profile_start_ts_ns": int(state["profile_start_ts_ns"]),
            "profile_end_ts_ns": end_ts_ns,
            "bin_width": bin_width,
            "atr_unit": atr_unit,
            "bracket_count": bracket_count,
            "poc": poc_index * bin_width,
            "val": val,
            "vah": vah,
            "va_count": va_count,
            "va_mass": va_count / total,
            "va_mask": {"low_bin_index": va_low, "high_bin_index": va_high},
            "gap_mask": gap_mask,
            "gap_span": gap_span_value,
            "gap_span_atr": gap_span_atr,
            "gap_span_va": gap_span_va,
            "va_width": va_width,
            "tight_gap": gap_span_value < self.tight_ratio * va_width,
            "tpo_total": total,
            "tpo_conservation_ok": conservation_ok,
            "profile_status": "DEFINED",
            "undefined_reason": None,
        }

    @staticmethod
    def _bin_index(price: float, bin_width: float) -> int:
        price_decimal = Decimal(str(price))
        width_decimal = Decimal(str(bin_width))
        return int((price_decimal / width_decimal).to_integral_value(rounding=ROUND_FLOOR))

    def _current_profile_state(self, raid_id: str) -> dict[str, int | float]:
        generation = self.store.current_profile_generation(raid_id)
        if generation is None:
            raise KeyError(raid_id)
        state = self.store.get_profile_state(raid_id, generation)
        if state is None:
            raise KeyError(raid_id)
        return state

    def _summary(
        self, raid_id: str, generation: int
    ) -> tuple[int, int | None, int | None, int | None, int]:
        total = 0
        low_index: int | None = None
        high_index: int | None = None
        poc_index: int | None = None
        poc_count = 0
        for bin_index, count in self.store.iter_profile_bins(raid_id, generation):
            total += count
            low_index = bin_index if low_index is None else low_index
            high_index = bin_index
            if count > poc_count:
                poc_index = bin_index
                poc_count = count
        return total, low_index, high_index, poc_index, poc_count

    def _value_area(
        self,
        raid_id: str,
        generation: int,
        low_index: int,
        high_index: int,
        poc_index: int,
        poc_count: int,
        total: int,
    ) -> tuple[int, int, int]:
        va_low = poc_index
        va_high = poc_index
        va_count = poc_count
        target = self.value_area_mass * total
        while va_count < target:
            lower_index = va_low - 1 if va_low > low_index else None
            upper_index = va_high + 1 if va_high < high_index else None
            lower_count = (
                self.store.profile_bin_count(raid_id, generation, lower_index) or 0
                if lower_index is not None
                else None
            )
            upper_count = (
                self.store.profile_bin_count(raid_id, generation, upper_index) or 0
                if upper_index is not None
                else None
            )
            if lower_count is None and upper_count is None:
                break
            if upper_count is not None and (lower_count is None or upper_count >= lower_count):
                va_high = upper_index
                va_count += upper_count
            else:
                va_low = lower_index
                va_count += lower_count
        return va_low, va_high, va_count

    def _gap_span(
        self,
        raid_id: str,
        generation: int,
        va_low: int,
        va_high: int,
        va_count: int,
        bin_width: float,
    ) -> tuple[float, dict[str, Any]] | None:
        target = self.gap_mass * va_count
        def selected_indexes() -> Iterator[int]:
            selected_mass = 0
            for bin_index, count in self.store.iter_profile_bins_by_density(
                raid_id, generation, va_low, va_high
            ):
                selected_mass += count
                yield bin_index
                if selected_mass >= target:
                    return

        selected_count, gap_low, gap_high, digest = self.store.replace_profile_gap_mask(
            raid_id, generation, selected_indexes()
        )
        if gap_low is None or gap_high is None:
            return None
        return (gap_high - gap_low + 1) * bin_width, {
            "store_path": str(self.store.path),
            "raid_id": raid_id,
            "profile_generation": generation,
            "selected_count": selected_count,
            "sha256": digest,
            "outer_low_bin_index": gap_low,
            "outer_high_bin_index": gap_high,
        }

    def _undefined(
        self,
        raid_id: str,
        generation: int,
        end_ts_ns: int,
        state: dict[str, int | float] | None,
        reason: str,
        *,
        tpo_total: int | None = None,
        conservation_ok: bool = False,
    ) -> dict[str, Any]:
        return {
            "raid_id": raid_id,
            "profile_generation": generation,
            "profile_start_ts_ns": (
                int(state["profile_start_ts_ns"]) if state is not None else None
            ),
            "profile_end_ts_ns": end_ts_ns,
            "bin_width": float(state["bin_width"]) if state is not None else None,
            "bracket_count": int(state["bracket_count"]) if state is not None else 0,
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
            "tpo_total": tpo_total,
            "tpo_conservation_ok": conservation_ok,
            "profile_status": "UNDEFINED",
            "undefined_reason": reason,
        }
