"""Shim: Nautilus emission contract v1 → ``xen.adjudication`` frames (INFR-010 Phase B).

Maps:

* ``bar_marks.parquet`` → positions frame (``SourceCloseTime``, ``RealOpen``, …)
* ``positions_ledger.parquet`` → ``cis_trades`` leg ledger
  (``EntryTime``, ``ExitTime``, ``Direction``, ``EntryFillPrice``, ``ExitFillPrice``,
  ``RealizedBps``, ``Censored``)

Linear return on fills (same contract as cTrader emissions)::

    RealizedBps = Direction * (ExitFillPrice - EntryFillPrice) / EntryFillPrice * 1e4
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import polars as pl

from xen.adjudication import MultiLegSeries, ReconcileReport, assemble_multileg_bps, reconcile
from xen.nautilus.emission import LoadedEmission, load_emission_v1


def _direction_from_entry(entry: str) -> int:
    e = str(entry).upper()
    if e in {"BUY", "LONG"}:
        return 1
    if e in {"SELL", "SHORT"}:
        return -1
    raise ValueError(f"unrecognised position entry side: {entry!r}")


def positions_ledger_to_cis_trades(ledger: pl.DataFrame) -> pl.DataFrame:
    """Convert Nautilus positions ledger rows into adjudication ``cis_trades`` legs."""
    if ledger.height == 0:
        return pl.DataFrame(
            schema={
                "EntryTime": pl.Datetime("ns"),
                "ExitTime": pl.Datetime("ns"),
                "Direction": pl.Int32,
                "EntryFillPrice": pl.Float64,
                "ExitFillPrice": pl.Float64,
                "RealizedBps": pl.Float64,
                "Censored": pl.Boolean,
                "LegSymbol": pl.Utf8,
            }
        )

    df = ledger
    # Accept either native Nautilus report names or already-normalised names.
    rename = {}
    for src, dst in (
        ("ts_opened", "EntryTime"),
        ("ts_closed", "ExitTime"),
        ("avg_px_open", "EntryFillPrice"),
        ("avg_px_close", "ExitFillPrice"),
        ("instrument_id", "LegSymbol"),
    ):
        if src in df.columns and dst not in df.columns:
            rename[src] = dst
    if rename:
        df = df.rename(rename)

    required = {"EntryTime", "EntryFillPrice", "entry"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"positions_ledger missing {sorted(missing)}")

    # Censored = still open at fence / no close timestamp or zero close price.
    if "ExitTime" not in df.columns:
        df = df.with_columns(pl.lit(None).cast(pl.Datetime("ns")).alias("ExitTime"))
    if "ExitFillPrice" not in df.columns:
        df = df.with_columns(pl.lit(None).cast(pl.Float64).alias("ExitFillPrice"))

    directions = [_direction_from_entry(v) for v in df.get_column("entry").to_list()]
    entry_px = df.get_column("EntryFillPrice").to_list()
    exit_px = df.get_column("ExitFillPrice").to_list()
    exit_t = df.get_column("ExitTime").to_list()

    realized = []
    censored = []
    for d, ep, xp, et in zip(directions, entry_px, exit_px, exit_t, strict=True):
        is_censored = et is None or xp is None or (isinstance(xp, float) and (xp != xp or xp == 0.0))
        censored.append(bool(is_censored))
        if is_censored or ep is None or ep == 0:
            realized.append(float("nan"))
        else:
            realized.append(float(d) * (float(xp) - float(ep)) / float(ep) * 1e4)

    out = pl.DataFrame(
        {
            "EntryTime": df.get_column("EntryTime"),
            "ExitTime": df.get_column("ExitTime"),
            "Direction": directions,
            "EntryFillPrice": [float(x) for x in entry_px],
            "ExitFillPrice": [float(x) if x is not None else float("nan") for x in exit_px],
            "RealizedBps": realized,
            "Censored": censored,
            "LegSymbol": (
                df.get_column("LegSymbol").cast(pl.Utf8)
                if "LegSymbol" in df.columns
                else pl.Series("LegSymbol", [""] * df.height)
            ),
        }
    )
    # Ensure datetime ns for searchsorted alignment.
    for col in ("EntryTime", "ExitTime"):
        if out[col].dtype != pl.Datetime("ns"):
            out = out.with_columns(pl.col(col).cast(pl.Datetime("ns")))
    return out


def bar_marks_to_positions(bar_marks: pl.DataFrame) -> pl.DataFrame:
    """Normalise bar marks to adjudication positions columns."""
    if bar_marks.height == 0:
        raise ValueError("bar_marks is empty — cannot build positions frame")
    df = bar_marks
    rename = {}
    for src, dst in (
        ("ts_event", "SourceCloseTime"),
        ("open", "RealOpen"),
        ("high", "RealHigh"),
        ("low", "RealLow"),
        ("close", "RealClose"),
    ):
        if src in df.columns and dst not in df.columns:
            rename[src] = dst
    if rename:
        df = df.rename(rename)
    if "SourceCloseTime" not in df.columns or "RealOpen" not in df.columns:
        raise ValueError(
            "bar_marks must carry SourceCloseTime/RealOpen (or ts_event/open)"
        )
    if df["SourceCloseTime"].dtype != pl.Datetime("ns"):
        df = df.with_columns(pl.col("SourceCloseTime").cast(pl.Datetime("ns")))
    cols = ["SourceCloseTime", "RealOpen"]
    for optional in ("RealHigh", "RealLow", "RealClose", "Position", "OpenLegs"):
        if optional in df.columns:
            cols.append(optional)
    return df.select(cols).sort("SourceCloseTime")


@dataclass(frozen=True)
class AdjudicationBundle:
    """Frames ready for ``assemble_multileg_bps`` / estimand gate."""

    positions: pl.DataFrame
    cis_trades: pl.DataFrame
    metadata: dict[str, Any]
    series: MultiLegSeries | None
    reconcile_report: ReconcileReport | None


def emission_to_adjudication_frames(
    emission: LoadedEmission | str | Path,
) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    """Return ``(positions, cis_trades, metadata)`` from an emission dir or loaded object."""
    if not isinstance(emission, LoadedEmission):
        emission = load_emission_v1(emission)
    positions = bar_marks_to_positions(emission.bar_marks)
    cis = positions_ledger_to_cis_trades(emission.positions_ledger)
    return positions, cis, emission.metadata


def adjudicate_emission(
    emission: LoadedEmission | str | Path,
    *,
    cost_bps: float = 0.0,
) -> AdjudicationBundle:
    """Parse emission and run the canonical multi-leg series + reconcile."""
    positions, cis, metadata = emission_to_adjudication_frames(emission)
    if positions.height < 2:
        return AdjudicationBundle(positions, cis, metadata, None, None)
    # Drop censored-only / empty leg books cleanly.
    if cis.height == 0:
        series = assemble_multileg_bps(positions, cis, cost_bps=cost_bps)
        return AdjudicationBundle(positions, cis, metadata, series, None)
    series = assemble_multileg_bps(positions, cis, cost_bps=cost_bps)
    rep = reconcile(series, cis)
    return AdjudicationBundle(positions, cis, metadata, series, rep)
