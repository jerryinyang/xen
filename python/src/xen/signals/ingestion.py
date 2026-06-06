"""Ingestion harness for cTrader strategy-host output (INFR-001, design.md v2).

In the v2 execution model the **cTrader cAlgo is the sole signal generator**;
Python neither generates nor re-implements strategy signals. This module is the
*validation/ingestion* side: it reads a strategy-host run (the `positions.parquet`
emitted by the cAlgo, carrying the real OHLC the strategy executed on) and routes
the position series, evaluated on next-step real-price returns, through the
**frozen** referee suite unchanged.

Crucially, returns are computed from the **emitted** real OHLC (``RealClose``),
not by re-aggregating a local Parquet. That is what makes a genuine cTrader run
(its own feed) self-consistent and decoupled from any local price source
(design.md v2 fence #4).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from xen.referee_calibration import (
    domain_split_index,
    evaluate_referees,
    next_log_returns_from_bars,
    seed_for,
)

# Columns the strategy-host emits in positions.parquet (StrategyRunParquetWriter).
POSITION_COLUMNS = [
    "SourceCloseTime",
    "Domain",
    "Strategy",
    "Position",
    "SignalValue",
    "RealOpen",
    "RealHigh",
    "RealLow",
    "RealClose",
    "Warmup",
    "IsFlat",
]

_REQUIRED_COLUMNS = {"SourceCloseTime", "Position", "RealClose"}


@dataclass(frozen=True)
class EmittedRun:
    """A loaded strategy-host run directory."""

    positions: pl.DataFrame
    metadata: dict[str, Any]
    run_dir: Path


def load_emitted_run(run_dir: str | Path) -> EmittedRun:
    """Load ``positions.parquet`` and ``run_metadata.json`` from a host run dir."""
    run_path = Path(run_dir)
    positions_path = run_path / "positions.parquet"
    if not positions_path.exists():
        raise FileNotFoundError(f"No positions.parquet in strategy-host run: {run_path}")
    positions = pl.read_parquet(positions_path)
    _validate_positions(positions)
    metadata_path = run_path / "run_metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}
    return EmittedRun(positions=positions, metadata=metadata, run_dir=run_path)


def returns_and_positions(positions: pl.DataFrame) -> tuple[np.ndarray, np.ndarray, pl.DataFrame]:
    """Build next-step real-price returns and the aligned position array.

    Returns are computed from the emitted ``RealClose`` via the frozen
    ``next_log_returns_from_bars`` helper, so the suite sees exactly the prices
    the strategy ran on. The last bar has no forward return and is dropped, so the
    aligned position array is the chronological positions truncated to match.
    """
    _validate_positions(positions)
    ordered = positions.sort("SourceCloseTime")
    bars = ordered.select(
        pl.col("SourceCloseTime").alias("OpenTime"),
        pl.col("SourceCloseTime").alias("CloseTime"),
        pl.col("RealOpen").alias("Open"),
        pl.col("RealHigh").alias("High"),
        pl.col("RealLow").alias("Low"),
        pl.col("RealClose").alias("Close"),
        pl.lit(0, dtype=pl.Int64).alias("TickVolume"),
    )
    returns, aligned = next_log_returns_from_bars(bars)
    position_array = ordered.get_column("Position").to_numpy().astype(float)
    return returns, position_array[: len(returns)], aligned


def screen_emitted_positions(
    positions: pl.DataFrame,
    *,
    instrument: str,
    domain: str,
    seed: int,
    train_end_utc: Any | None = None,
    alpha_values: tuple[float, ...] = (0.05,),
    n_bootstrap: int = 1000,
) -> list[dict[str, Any]]:
    """Route emitted positions through the frozen referee suite unchanged.

    ``train_end_utc`` is the within-analysis train/test boundary. When provided,
    the split is derived from it on the emitted timestamps (reproducing the EXP-004
    split); when ``None`` the frozen referee falls back to its 70% row split.
    """
    returns, position_array, aligned = returns_and_positions(positions)
    split_index = domain_split_index(aligned, train_end_utc) if train_end_utc is not None else None
    return evaluate_referees(
        returns,
        position_array,
        instrument=instrument,
        domain=domain,
        alpha_values=alpha_values,
        n_bootstrap=n_bootstrap,
        seed=seed,
        split_index=split_index,
    )


def screen_emitted_run(
    run: EmittedRun,
    *,
    train_end_utc: Any | None = None,
    seed: int | None = None,
    seed_tag: str = "EXP-004",
    alpha_values: tuple[float, ...] = (0.05,),
    n_bootstrap: int = 1000,
) -> list[dict[str, Any]]:
    """Screen a loaded run, deriving instrument/domain/strategy from its rows.

    The default seed reproduces the EXP-004 seeding (``seed_for(seed_tag,
    instrument, domain, strategy)``) so a cTrader MA run is comparable to the
    known dogfood anchor; pass ``seed`` to override.
    """
    instrument = str(run.metadata.get("symbol") or _first(run.positions, "Domain", fallback="")).upper()
    if not instrument:
        instrument = str(run.metadata.get("symbol", "")).upper()
    domain = str(_first(run.positions, "Domain"))
    strategy = str(_first(run.positions, "Strategy"))
    resolved_seed = seed if seed is not None else seed_for(seed_tag, instrument, domain, strategy)
    return screen_emitted_positions(
        run.positions,
        instrument=instrument,
        domain=domain,
        seed=resolved_seed,
        train_end_utc=train_end_utc,
        alpha_values=alpha_values,
        n_bootstrap=n_bootstrap,
    )


def assert_before_analysis_end(source_close_time: Any, analysis_end_utc: Any | None) -> None:
    """Fail closed if any emitted timestamp reaches the holdout cutoff."""
    if analysis_end_utc is None:
        return
    if _as_utc_naive(source_close_time) >= _as_utc_naive(analysis_end_utc):
        raise ValueError(
            "Strategy output reaches or passes AnalysisEndUtc: "
            f"{source_close_time!s} >= {analysis_end_utc!s}"
        )


def assert_run_within_holdout(positions: pl.DataFrame, analysis_end_utc: Any) -> None:
    """Assert every emitted position is strictly before the holdout cutoff."""
    if positions.is_empty():
        return
    max_time = positions.get_column("SourceCloseTime").max()
    assert_before_analysis_end(max_time, analysis_end_utc)


def _validate_positions(positions: pl.DataFrame) -> None:
    missing = _REQUIRED_COLUMNS.difference(positions.columns)
    if missing:
        raise ValueError(f"positions is missing required columns: {sorted(missing)}")


def _first(frame: pl.DataFrame, column: str, *, fallback: str | None = None) -> Any:
    if frame.is_empty() or column not in frame.columns:
        if fallback is not None:
            return fallback
        raise ValueError(f"cannot read first value of empty/absent column {column!r}")
    return frame.get_column(column)[0]


def _as_utc_naive(value: Any) -> datetime:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    elif hasattr(value, "to_pydatetime"):
        dt = value.to_pydatetime()
    else:
        raise TypeError(f"Unsupported datetime value: {value!r}")
    if dt.tzinfo is not None:
        dt = dt.astimezone(UTC).replace(tzinfo=None)
    return dt
