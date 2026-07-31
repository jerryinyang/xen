"""Read-only resource preflight for the adaptive-management SPDR runs.

The estimator reads the universe fence manifest and catalog instrument metadata only. It never
queries bars, executes orders, creates a result directory or emits any research value. Every
figure it reports is an operational capacity estimate, never evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
from typing import Any

from xen.adaptive_management.contracts import (
    ExperimentSpec,
    build_management_lattice,
    build_native_lattice,
)
from xen.adaptive_management.runner import REPO_ROOT, Universe, universe_config
from xen.nautilus.catalog_fence import load_fence_manifest

# Planning constants, calibrated against a measured bounded run (SPDR-021, cTrader EURUSD,
# 90 TRAIN days: 692 origins, 100,340 schedule rows, 26,507 order/fill rows,
# 22.6 MB published) and against a full-span symbol (997,890 rows, 122 s, 3.4 GB peak).
# They size disk, memory and time only, and carry no research meaning.
# Measured on the bounded real runs: 692 breakout origins and 1,536 breach zone origins over
# 1,537 warm H1 bars. A breach experiment has one zone origin per warm bar by construction.
ORIGIN_RATE_PER_H1_BAR = {
    "SPDR-021": 0.45,
    "SPDR-022": 1.00,
    "SPDR-023": 1.00,
}
ORDER_FILL_ROWS_PER_SCHEDULE_ROW = 0.5  # measured 0.26; held at an upper bound
BYTES_PER_SCHEDULE_ROW = 160  # measured ~68 B of tables + ~120 B per order row, compressed
BYTES_PER_SYMBOL_DAY = 160_000  # per-symbol bar marks and cell copies, measured ~150 KB/day
PUBLICATION_OVERHEAD = 2.0  # one in-progress copy plus the published copy
SECONDS_PER_SCHEDULE_ROW = 0.00013  # measured 122 s / 997,890 rows, full TRAIN span
WALL_CLOCK_LOW_FACTOR = 0.7
WALL_CLOCK_HIGH_FACTOR = 2.0
DISK_HEADROOM_FRACTION = 0.70


@dataclass(frozen=True)
class RunEstimate:
    experiment_id: str
    universe: str
    symbols: int
    h1_origins: int
    native_rows: int
    management_rows: int
    work_units: int
    order_fill_upper_bound: int
    estimated_output_bytes: int
    available_disk_bytes: int
    benchmark_seconds_per_unit: float
    estimated_wall_clock_low_seconds: float
    estimated_wall_clock_high_seconds: float


def estimate_run(
    spec: ExperimentSpec,
    universe: Universe,
    *,
    disk_path: Path | None = None,
) -> RunEstimate:
    """Estimate the cost of one experiment/universe run without touching bar data."""
    config = universe_config(universe)
    manifest = load_fence_manifest(config.manifest_path)
    catalog_instruments = _instrument_metadata(config)
    symbols = len(config.symbols)
    if len(catalog_instruments) != symbols:
        raise FileNotFoundError(
            f"catalog is missing declared instruments for {universe}: "
            f"{sorted(set(config.instrument_ids) - set(catalog_instruments))}"
        )

    train_hours = _train_hours(manifest.analysis_start_utc, manifest.train_end_utc)
    origins_per_symbol = int(train_hours * ORIGIN_RATE_PER_H1_BAR[spec.experiment_id])
    h1_origins = origins_per_symbol * symbols

    native = build_native_lattice(spec.experiment_id)
    management = build_management_lattice(spec.experiment_id)
    entry_variants = len({arm.entry_variant for arm in native if not arm.is_adaptive})
    native_rows = h1_origins * len(native)
    management_rows = h1_origins * len(management) * entry_variants

    order_fill_upper_bound = int(
        (native_rows + management_rows) * ORDER_FILL_ROWS_PER_SCHEDULE_ROW
    )
    symbol_days = symbols * train_hours / 24.0
    estimated_output_bytes = int(
        (
            (native_rows + management_rows) * BYTES_PER_SCHEDULE_ROW
            + symbol_days * BYTES_PER_SYMBOL_DAY
        )
        * PUBLICATION_OVERHEAD
    )

    rows_per_unit = (native_rows + management_rows) / max(symbols, 1)
    seconds_per_unit = rows_per_unit * SECONDS_PER_SCHEDULE_ROW
    total_seconds = seconds_per_unit * symbols

    target = Path(disk_path) if disk_path is not None else REPO_ROOT
    available = shutil.disk_usage(target).free

    return RunEstimate(
        experiment_id=spec.experiment_id,
        universe=config.name,
        symbols=symbols,
        h1_origins=h1_origins,
        native_rows=native_rows,
        management_rows=management_rows,
        work_units=symbols,
        order_fill_upper_bound=order_fill_upper_bound,
        estimated_output_bytes=estimated_output_bytes,
        available_disk_bytes=int(available),
        benchmark_seconds_per_unit=seconds_per_unit,
        estimated_wall_clock_low_seconds=total_seconds * WALL_CLOCK_LOW_FACTOR,
        estimated_wall_clock_high_seconds=total_seconds * WALL_CLOCK_HIGH_FACTOR,
    )


def check_disk_headroom(
    estimate: RunEstimate,
    *,
    fraction: float = DISK_HEADROOM_FRACTION,
) -> None:
    """Raise when the estimated footprint exceeds the allowed share of free space."""
    allowed = estimate.available_disk_bytes * fraction
    if estimate.estimated_output_bytes > allowed:
        raise RuntimeError(
            "insufficient disk headroom: "
            f"{estimate.estimated_output_bytes} bytes estimated exceeds "
            f"{int(allowed)} bytes ({fraction:.0%} of free space)"
        )


def report_lines(estimate: RunEstimate) -> list[str]:
    """Operator-readable preflight report; plain figures, no verdict."""
    return [
        f"experiment: {estimate.experiment_id} ({estimate.universe}, band=TRAIN)",
        f"symbols: {estimate.symbols}",
        f"H1 origins: {estimate.h1_origins}",
        f"native rows: {estimate.native_rows}",
        f"logical management rows: {estimate.management_rows}",
        f"estimated order/fill upper bound: {estimate.order_fill_upper_bound}",
        f"work units: {estimate.work_units}",
        f"estimated output bytes: {estimate.estimated_output_bytes}",
        f"available disk bytes: {estimate.available_disk_bytes}",
        f"benchmark seconds/unit: {estimate.benchmark_seconds_per_unit:.1f}",
        (
            "estimated wall clock: "
            f"{estimate.estimated_wall_clock_low_seconds / 60:.1f}"
            f"-{estimate.estimated_wall_clock_high_seconds / 60:.1f} minutes"
        ),
    ]


def _instrument_metadata(config: Any) -> dict[str, str]:
    from nautilus_trader.persistence.catalog import ParquetDataCatalog

    catalog = ParquetDataCatalog(str(config.catalog_path))
    available = {
        str(instrument.id): type(instrument).__name__ for instrument in catalog.instruments()
    }
    return {
        instrument_id: available[instrument_id]
        for instrument_id in config.instrument_ids
        if instrument_id in available
    }


def _train_hours(start: Any, end: Any) -> float:
    return max((end - start).total_seconds() / 3600.0, 0.0)
