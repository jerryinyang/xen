"""Focused online TPO profile tests for EXP-100."""

from pathlib import Path

import pytest

from xen.exp100.state_store import Exp100StateStore
from xen.exp100.tpo import TPOProfileStore
from xen.exp100.types import BarRecord


def test_tpo_conservation_and_strict_tight_boundary(tmp_path: Path) -> None:
    """Every closed bar contributes once per intersected fixed bin."""
    with Exp100StateStore(tmp_path / "state.sqlite") as store:
        profile = TPOProfileStore(store)
        generation = profile.start("R1", 1, excursion_price=101.2, atr_unit=1.0)
        profile.add_bar("R1", generation, BarRecord(2, 100.0, 101.0, 99.5, 100.5, 1.0, 1))
        profile.add_bar("R1", generation, BarRecord(3, 100.5, 101.0, 100.0, 100.8, 1.0, 1))
        result = profile.finalize("R1", generation, 4)

    assert result["tpo_conservation_ok"] is True
    assert result["bracket_count"] == 2
    assert result["tight_gap"] == (result["gap_span"] < 0.30 * result["va_width"])


def test_tpo_reset_discards_previous_generation_without_rebuild(tmp_path: Path) -> None:
    """A new maximum starts a clean generation at its own one-minute bar."""
    with Exp100StateStore(tmp_path / "state.sqlite") as store:
        profile = TPOProfileStore(store)
        first = profile.start("R1", 1, excursion_price=100.0, atr_unit=1.0)
        profile.add_bar("R1", first, BarRecord(2, 100.0, 100.0, 100.0, 100.0, 1.0, 1))
        second = profile.reset("R1", new_max_price=102.0, ts_ns=3)
        profile.add_bar("R1", second, BarRecord(4, 102.0, 102.0, 102.0, 102.0, 1.0, 1))
        result = profile.finalize("R1", second, 5)

    assert result["profile_generation"] == second
    assert result["tpo_total"] == result["bracket_count"]
    assert result["profile_generation"] > first
    assert result["profile_start_ts_ns"] == 3


def test_tpo_uses_lowest_poc_tie_and_upper_value_area_tie(tmp_path: Path) -> None:
    """POC and value-area tie breakers are deterministic price choices."""
    with Exp100StateStore(tmp_path / "state.sqlite") as store:
        profile = TPOProfileStore(store)
        generation = profile.start("R1", 1, excursion_price=0.1, atr_unit=1.0)
        for ts_ns, price in enumerate((0.1, 0.1, 0.1, 0.0, 0.2), start=2):
            profile.add_bar(
                "R1",
                generation,
                BarRecord(ts_ns, price, price, price, price, 1.0, 1),
            )
        result = profile.finalize("R1", generation, 7)

    assert result["poc"] == pytest.approx(0.1)
    assert result["va_mask"] == {"low_bin_index": 1, "high_bin_index": 2}
    assert result["val"] == pytest.approx(0.1)
    assert result["vah"] == pytest.approx(0.3)
    assert result["va_count"] == 4


def test_tpo_rejects_invalid_grid_parameters(tmp_path: Path) -> None:
    """A profile cannot invent a grid from invalid constants or ATR."""
    with Exp100StateStore(tmp_path / "state.sqlite") as store:
        with pytest.raises(ValueError, match="value_area_mass"):
            TPOProfileStore(store, value_area_mass=0.0)
        with pytest.raises(ValueError, match="gap_mass"):
            TPOProfileStore(store, gap_mass=float("nan"))
        with pytest.raises(ValueError, match="tight_ratio"):
            TPOProfileStore(store, tight_ratio=1.1)
        profile = TPOProfileStore(store)
        with pytest.raises(ValueError, match="atr_unit"):
            profile.start("R1", 1, excursion_price=101.0, atr_unit=0.0)


def test_tpo_empty_profile_emits_explicit_reason(tmp_path: Path) -> None:
    """Finalization distinguishes an empty persisted profile from numeric output."""
    with Exp100StateStore(tmp_path / "state.sqlite") as store:
        profile = TPOProfileStore(store)
        generation = profile.start("R1", 1, excursion_price=101.0, atr_unit=1.0)
        result = profile.finalize("R1", generation, 2)

    assert result["profile_status"] == "UNDEFINED"
    assert result["undefined_reason"] == "EMPTY_PROFILE"


def test_tpo_gap_uses_va_mass_and_emits_separated_mask(tmp_path: Path) -> None:
    """VA-mass and total-mass thresholds select different low-density bins."""
    with Exp100StateStore(tmp_path / "state.sqlite") as store:
        profile = TPOProfileStore(store)
        generation = profile.start("R1", 1, excursion_price=0.1, atr_unit=1.0)
        for index, count in ((0, 4), (1, 10), (2, 3), (3, 4), (4, 9)):
            for offset in range(count):
                price = index / 10
                profile.add_bar(
                    "R1",
                    generation,
                    BarRecord(index * 100 + offset, price, price, price, price, 1.0, 1),
                )
        result = profile.finalize("R1", generation, 1000)

    assert result["tpo_total"] == 30
    assert result["va_count"] == 21
    assert result["gap_mask"] == "2|0"
    assert result["gap_span"] == pytest.approx(0.3)


def test_tpo_duplicate_start_is_rejected(tmp_path: Path) -> None:
    """A repeated causal start cannot replace an existing profile generation."""
    with Exp100StateStore(tmp_path / "state.sqlite") as store:
        profile = TPOProfileStore(store)
        first = profile.start("R1", 1, excursion_price=100.0, atr_unit=1.0)
        with pytest.raises(ValueError, match="already exists"):
            profile.start("R1", 2, excursion_price=101.0, atr_unit=1.0)

        assert store.current_profile_generation("R1") == first


def test_tpo_uses_exact_decimal_boundaries_for_negative_prices(tmp_path: Path) -> None:
    """Exact positive and negative boundaries map to their mathematical bins."""
    with Exp100StateStore(tmp_path / "state.sqlite") as store:
        profile = TPOProfileStore(store)
        generation = profile.start("R1", 1, excursion_price=0.0, atr_unit=1.0)
        profile.add_bar("R1", generation, BarRecord(2, 0.3, 0.3, 0.3, 0.3, 1.0, 1))
        profile.add_bar("R1", generation, BarRecord(3, -0.1, -0.1, -0.1, -0.1, 1.0, 1))

        assert list(store.iter_profile_bins("R1", generation)) == [(-1, 1), (3, 1)]


def test_tpo_one_bin_gap_is_explicitly_undefined(tmp_path: Path) -> None:
    """A one-bin value area cannot produce a meaningful gap/tightness label."""
    with Exp100StateStore(tmp_path / "state.sqlite") as store:
        profile = TPOProfileStore(store)
        generation = profile.start("R1", 1, excursion_price=100.0, atr_unit=1.0)
        profile.add_bar("R1", generation, BarRecord(2, 100.0, 100.0, 100.0, 100.0, 1.0, 1))
        result = profile.finalize("R1", generation, 3)

    assert result["profile_status"] == "UNDEFINED"
    assert result["undefined_reason"] == "GAP_UNDEFINED"
    assert result["tight_gap"] is False
