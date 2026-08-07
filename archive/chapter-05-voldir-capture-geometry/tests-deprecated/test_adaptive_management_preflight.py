from __future__ import annotations

from pathlib import Path

import pytest

from xen.adaptive_management.contracts import experiment_spec
from xen.adaptive_management.preflight import (
    RunEstimate,
    check_disk_headroom,
    estimate_run,
    report_lines,
)
from xen.adaptive_management.runner import universe_config


def _skip_if_no_catalog(universe: str) -> None:
    if not universe_config(universe).catalog_path.exists():
        pytest.skip(f"{universe} catalog is not present")


@pytest.mark.parametrize("universe", ["ctrader", "crypto"])
def test_estimate_reports_every_declared_field(universe):
    _skip_if_no_catalog(universe)
    estimate = estimate_run(experiment_spec("SPDR-021"), universe)
    assert isinstance(estimate, RunEstimate)
    assert estimate.universe == universe
    assert estimate.symbols == len(universe_config(universe).symbols)
    assert estimate.work_units == estimate.symbols
    assert estimate.h1_origins > 0
    assert estimate.native_rows > estimate.h1_origins
    assert estimate.management_rows > 0
    assert estimate.order_fill_upper_bound >= estimate.native_rows
    assert estimate.estimated_output_bytes > 0
    assert estimate.available_disk_bytes > 0
    assert estimate.benchmark_seconds_per_unit > 0
    assert (
        estimate.estimated_wall_clock_low_seconds
        < estimate.estimated_wall_clock_high_seconds
    )


def test_estimate_creates_no_result_directory_and_reads_no_bars(monkeypatch, tmp_path):
    _skip_if_no_catalog("ctrader")
    from xen.nautilus import catalog_fence

    def forbidden(*args, **kwargs):
        raise AssertionError("preflight must not query bars")

    monkeypatch.setattr(catalog_fence, "fenced_bar_query", forbidden)
    before = set(tmp_path.iterdir())
    estimate_run(experiment_spec("SPDR-021"), "ctrader", disk_path=tmp_path)
    assert set(tmp_path.iterdir()) == before


def test_estimates_cover_both_entry_variants_for_022_and_023():
    _skip_if_no_catalog("ctrader")
    from xen.adaptive_management.contracts import (
        build_management_lattice,
        build_native_lattice,
    )

    for experiment_id in ("SPDR-022", "SPDR-023"):
        estimate = estimate_run(experiment_spec(experiment_id), "ctrader")
        native = build_native_lattice(experiment_id)
        variants = {arm.entry_variant for arm in native if not arm.is_adaptive}
        assert variants == {"E_TOUCH", "E_CLOSE"}
        assert estimate.native_rows == estimate.h1_origins * len(native)
        assert estimate.management_rows == (
            estimate.h1_origins * len(build_management_lattice(experiment_id)) * 2
        )


def test_disk_headroom_check_uses_seventy_percent_of_free_space():
    _skip_if_no_catalog("ctrader")
    estimate = estimate_run(experiment_spec("SPDR-021"), "ctrader")
    check_disk_headroom(estimate)

    tight = RunEstimate(
        **{
            **estimate.__dict__,
            "estimated_output_bytes": int(estimate.available_disk_bytes * 0.71),
        }
    )
    with pytest.raises(RuntimeError, match="insufficient disk headroom"):
        check_disk_headroom(tight)


def test_output_estimate_includes_publication_overhead():
    _skip_if_no_catalog("ctrader")
    from xen.adaptive_management import preflight

    estimate = estimate_run(experiment_spec("SPDR-021"), "ctrader")
    rows = estimate.native_rows + estimate.management_rows
    assert estimate.estimated_output_bytes > rows * preflight.BYTES_PER_SCHEDULE_ROW
    assert preflight.PUBLICATION_OVERHEAD >= 2.0
    assert estimate.order_fill_upper_bound == int(
        rows * preflight.ORDER_FILL_ROWS_PER_SCHEDULE_ROW
    )


def test_estimate_is_calibrated_against_the_measured_bounded_run():
    # The bounded SPDR-021 cTrader smoke published 22.6 MB for 100,340 schedule rows over
    # 90 symbol-days. The estimator must cover that, and must not exceed it by over 4x.
    _skip_if_no_catalog("ctrader")
    from xen.adaptive_management import preflight

    measured_bytes = 22_580 * 1024
    modelled = (
        100_340 * preflight.BYTES_PER_SCHEDULE_ROW
        + 90 * preflight.BYTES_PER_SYMBOL_DAY
    ) * preflight.PUBLICATION_OVERHEAD
    assert modelled >= measured_bytes
    assert modelled <= measured_bytes * 4


def test_report_lines_are_plain_and_carry_no_verdict():
    _skip_if_no_catalog("ctrader")
    lines = report_lines(estimate_run(experiment_spec("SPDR-021"), "ctrader"))
    text = "\n".join(lines).lower()
    assert "band=train" in text
    for banned in ("pass", "fail", "verdict", "worth", "significant"):
        assert banned not in text
    assert not Path("preflight").exists()
