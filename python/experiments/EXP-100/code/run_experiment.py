"""Run one EXP-100 cell through a memory-bounded Nautilus BacktestNode."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import nautilus_trader
import pyarrow.parquet as pq
from nautilus_trader.backtest.node import BacktestNode
from nautilus_trader.config import (
    BacktestDataConfig,
    BacktestEngineConfig,
    BacktestRunConfig,
    BacktestVenueConfig,
    ImportableStrategyConfig,
    LoggingConfig,
)
from nautilus_trader.core.datetime import dt_to_unix_nanos
from nautilus_trader.model.data import Bar
from nautilus_trader.model.identifiers import InstrumentId

from xen.nautilus.catalog_fence import (
    assert_within_fence,
    fence_attestation_payload,
    load_fence_manifest,
)
from xen.nautilus.emission import (
    StreamingEmissionSource,
    write_emission_v1_from_paths,
)
from xen.nautilus.streaming import MemoryBudgetExceeded

from xen.exp100 import Exp100CellConfig
from xen.exp100.control import destroy_post_confirmation
from xen.exp100.strategy import (
    DEFAULT_MEMORY_SAMPLE_EVERY,
    DEFAULT_WRITER_MAX_BYTES,
    DEFAULT_WRITER_MAX_ROWS,
)

DEFAULT_CHUNK_SIZE = 50_000
DEFAULT_RSS_LIMIT_BYTES = 1_610_612_736
DEFAULT_DESTROY_SEED = 17
_PARQUET_STREAMS = ("bar_marks", "levels", "raids", "tpo_profiles")
_CELL_NODE_CREATED = False
REPO_ROOT = Path(__file__).resolve().parents[4]


@dataclass(frozen=True, slots=True)
class VenueExecutionPin:
    """Repository-pinned catalog and TRAIN fence for one approved venue."""

    catalog_path: Path
    fence_path: Path
    fence_sha256: str
    train_start: datetime
    train_end: datetime


EXP100_VENUES = {
    "BYBIT": VenueExecutionPin(
        catalog_path=Path("data/catalog"),
        fence_path=Path(
            "archive/chapter-04-nautilus-bybit-sigauc/experiments/"
            "INFR-011/artifacts/fence-manifest.json"
        ),
        fence_sha256="35d3375ec5ec18b3c6e4c5eec814ade4d492bd60e3fb694fed19e16bc2c00448",
        train_start=datetime(2021, 6, 29, 6, 53, tzinfo=UTC),
        train_end=datetime(2023, 12, 18, tzinfo=UTC),
    ),
    "CTRADER": VenueExecutionPin(
        catalog_path=Path("data/catalog_ctrader"),
        fence_path=Path(
            "archive/chapter-05-voldir-capture-geometry/experiments/"
            "INFR-021/artifacts/fence-manifest.json"
        ),
        fence_sha256="4cdc7b01dd47200710d0d961639d55d52e1129ca89096e841eafd816b6061de0",
        train_start=datetime(2021, 6, 2, 0, 1, tzinfo=UTC),
        train_end=datetime(2023, 11, 22, tzinfo=UTC),
    ),
}


def execution_pin(venue: str) -> VenueExecutionPin:
    """Return the frozen execution pin for an approved EXP-100 venue."""
    try:
        return EXP100_VENUES[venue]
    except KeyError as exc:
        raise ValueError(f"unsupported EXP-100 venue: {venue!r}") from exc


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _bar_type(cell: Exp100CellConfig) -> str:
    return f"{cell.instrument_id}-1-MINUTE-LAST-EXTERNAL"


def _build_backtest_run_config(
    cell: Exp100CellConfig,
    *,
    catalog_path: Path,
    start_time: datetime,
    end_time: datetime,
    staging_path: Path,
    chunk_size: int,
    rss_limit_bytes: int | None,
) -> BacktestRunConfig:
    cell.validate()
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if rss_limit_bytes is not None and rss_limit_bytes <= 0:
        raise ValueError("rss_limit_bytes must be positive or None")
    start = _utc(start_time)
    end = _utc(end_time)
    if start > end:
        raise ValueError("start_time must not be after end_time")

    instrument_id = InstrumentId.from_str(cell.instrument_id)
    bar_type = _bar_type(cell)
    strategy_config = ImportableStrategyConfig(
        strategy_path="xen.exp100.strategy:Exp100Strategy",
        config_path="xen.exp100.strategy:Exp100StrategyConfig",
        config={
            "instrument_id": cell.instrument_id,
            "bar_type": bar_type,
            "cell_config_json": cell.serialize(),
            "state_path": str(staging_path / "state.sqlite"),
            "output_staging_path": str(staging_path),
            "writer_max_rows": DEFAULT_WRITER_MAX_ROWS,
            "writer_max_bytes": DEFAULT_WRITER_MAX_BYTES,
            "rss_limit_bytes": rss_limit_bytes,
            "memory_sample_every": DEFAULT_MEMORY_SAMPLE_EVERY,
        },
    )
    engine = BacktestEngineConfig(
        logging=LoggingConfig(log_level="ERROR", log_colors=False, print_config=False),
        strategies=[strategy_config],
        run_analysis=False,
    )
    venue = BacktestVenueConfig(
        name=str(instrument_id.venue),
        oms_type="NETTING",
        account_type="MARGIN",
        base_currency="USDT",
        starting_balances=["100000 USDT"],
        book_type="L1_MBP",
        frozen_account=True,
    )
    data = BacktestDataConfig(
        catalog_path=str(catalog_path),
        data_cls=Bar,
        instrument_id=instrument_id,
        bar_types=[bar_type],
        start_time=dt_to_unix_nanos(start),
        end_time=dt_to_unix_nanos(end),
    )
    return BacktestRunConfig(
        engine=engine,
        venues=[venue],
        data=[data],
        chunk_size=chunk_size,
        raise_exception=True,
        dispose_on_completion=False,
        start=dt_to_unix_nanos(start),
        end=dt_to_unix_nanos(end),
    )


def build_backtest_run_config(
    cell: Exp100CellConfig,
    *,
    catalog_path: Path,
    start_time: datetime,
    end_time: datetime,
    staging_path: Path,
    chunk_size: int,
) -> BacktestRunConfig:
    """Build the one-instrument, streaming BacktestNode configuration.

    Parameters
    ----------
    cell : Exp100CellConfig
        Frozen identity and methodology settings for one cell.
    catalog_path : Path
        ParquetDataCatalog path read by Nautilus.
    start_time, end_time : datetime
        Inclusive TRAIN-band replay bounds.
    staging_path : Path
        Cell-local path for SQLite state and bounded stream writers.
    chunk_size : int
        Positive native Nautilus transport chunk size.

    Returns
    -------
    BacktestRunConfig
        A single no-order streaming run configuration.
    """
    return _build_backtest_run_config(
        cell,
        catalog_path=catalog_path,
        start_time=start_time,
        end_time=end_time,
        staging_path=staging_path,
        chunk_size=chunk_size,
        rss_limit_bytes=DEFAULT_RSS_LIMIT_BYTES,
    )


def _run_metadata_config(
    cell: Exp100CellConfig,
    *,
    catalog_path: Path,
    start_time: datetime,
    end_time: datetime,
    chunk_size: int,
) -> dict[str, Any]:
    return {
        "api": "BacktestNode",
        "strategy": "Exp100Strategy",
        "instrument_id": cell.instrument_id,
        "bar_type": _bar_type(cell),
        "venue": cell.venue,
        "cell": cell.to_dict(),
        "catalog_path": str(catalog_path),
        "start_time": _utc(start_time).isoformat(),
        "end_time": _utc(end_time).isoformat(),
        "chunk_size": chunk_size,
        "dispose_on_completion": False,
        "run_analysis": False,
        "frozen_account": True,
        "orders_submitted": False,
        "cost_model": "NO_COST_CHARGED",
    }


def _copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as src, destination.open("wb") as dst:
        shutil.copyfileobj(src, dst, length=1024 * 1024)


def _validate_stream_manifest(work_dir: Path, manifest: dict[str, Any]) -> None:
    counts = manifest.get("row_counts")
    if not isinstance(counts, dict):
        raise ValueError("stream manifest has no row_counts mapping")
    for name in _PARQUET_STREAMS:
        path = work_dir / f"{name}.parquet"
        if not path.exists():
            raise FileNotFoundError(path)
        actual = int(pq.ParquetFile(path).metadata.num_rows)
        expected = int(counts.get(name, -1))
        if actual != expected:
            raise ValueError(f"{name} row count mismatch: {actual} != {expected}")
    event_path = work_dir / "event_log.jsonl"
    if not event_path.exists():
        raise FileNotFoundError(event_path)
    with event_path.open("r", encoding="utf-8") as handle:
        actual_events = sum(1 for _ in handle)
    if actual_events != int(counts.get("event_log", -1)):
        raise ValueError("event_log row count mismatch")
    snapshot = manifest.get("snapshot", {})
    if snapshot.get("open_levels", 0) != 0 or snapshot.get("open_raids", 0) != 0:
        raise ValueError("cell finished with live EXP-100 state")
    _validate_publication_integrity(work_dir)


def _validate_publication_integrity(work_dir: Path) -> None:
    """Enforce TPO conservation and raid/profile/event reconciliation before publish."""
    profiles_path = work_dir / "tpo_profiles.parquet"
    raids_path = work_dir / "raids.parquet"
    levels_path = work_dir / "levels.parquet"
    event_path = work_dir / "event_log.jsonl"

    profiles = pq.ParquetFile(profiles_path).read().to_pylist()
    raids = pq.ParquetFile(raids_path).read().to_pylist()
    levels = pq.ParquetFile(levels_path).read().to_pylist()

    for profile in profiles:
        status = profile.get("profile_status")
        if status == "DEFINED" and profile.get("tpo_conservation_ok") is not True:
            raise ValueError(
                f"TPO conservation failed for raid {profile.get('raid_id')!r}"
            )

    raid_ids = {row.get("raid_id") for row in raids}
    profile_raid_ids = {row.get("raid_id") for row in profiles}
    if raid_ids != profile_raid_ids:
        missing = sorted(raid_ids - profile_raid_ids)
        extra = sorted(profile_raid_ids - raid_ids)
        raise ValueError(
            f"raid/profile reconciliation failed; missing_profiles={missing} "
            f"extra_profiles={extra}"
        )

    for level in levels:
        if level.get("status") is None:
            raise ValueError(f"level {level.get('level_id')!r} missing terminal status")
        if level.get("active") is True:
            raise ValueError(f"level {level.get('level_id')!r} still marked active")

    for raid in raids:
        if raid.get("status") is None:
            raise ValueError(f"raid {raid.get('raid_id')!r} missing terminal status")
        if raid.get("active") is True:
            raise ValueError(f"raid {raid.get('raid_id')!r} still marked active")

    terminal_raid_events = 0
    terminal_level_events = 0
    with event_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            event_type = payload.get("event_type")
            if event_type == "RAID_TERMINAL":
                terminal_raid_events += 1
            elif event_type == "LEVEL_TERMINAL":
                terminal_level_events += 1
    if terminal_raid_events != len(raids):
        raise ValueError(
            f"raid event reconciliation failed: events={terminal_raid_events} "
            f"rows={len(raids)}"
        )
    if terminal_level_events != len(levels):
        raise ValueError(
            f"level event reconciliation failed: events={terminal_level_events} "
            f"rows={len(levels)}"
        )


def _remove_publish_stage(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def run_cell(
    cell: Exp100CellConfig,
    *,
    catalog_path: Path,
    run_dir: Path,
    start_time: datetime,
    end_time: datetime,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    rss_limit_bytes: int = DEFAULT_RSS_LIMIT_BYTES,
    destroy_control: bool = False,
    destroy_seed: int = DEFAULT_DESTROY_SEED,
) -> Path:
    """Run and atomically publish exactly one EXP-100 TRAIN cell.

    Parameters
    ----------
    cell : Exp100CellConfig
        Frozen identity and methodology settings for one cell.
    catalog_path : Path
        Real Nautilus ParquetDataCatalog path.
    run_dir : Path
        Final emission directory; it must not already exist.
    start_time, end_time : datetime
        TRAIN-band replay bounds checked against the canonical fence manifest.
    chunk_size : int, default 50000
        Positive fixed Nautilus streaming chunk size.
    rss_limit_bytes : int, default 1610612736
        Process RSS ceiling; a breach leaves an incomplete marker and publishes nothing.

    Returns
    -------
    Path
        The atomically published contract-v1 run directory.
    """
    global _CELL_NODE_CREATED
    cell.validate()
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if rss_limit_bytes <= 0:
        raise ValueError("rss_limit_bytes must be positive")
    run_dir = Path(run_dir)
    catalog_path = Path(catalog_path)
    if run_dir.exists():
        raise FileExistsError(f"run_dir already exists: {run_dir}")
    start = _utc(start_time)
    end = _utc(end_time)
    pin = execution_pin(cell.venue)
    manifest = load_fence_manifest(REPO_ROOT / pin.fence_path)
    if manifest.sha256 != pin.fence_sha256:
        raise ValueError(
            f"{cell.venue} fence hash mismatch: {manifest.sha256} != {pin.fence_sha256}"
        )
    assert_within_fence(manifest, start, end, band="TRAIN")
    fence = fence_attestation_payload(manifest)

    run_dir.parent.mkdir(parents=True, exist_ok=True)
    work_dir = run_dir.parent / f".{run_dir.name}.work"
    publish_stage = run_dir.parent / f".{run_dir.name}.publish"
    if work_dir.exists() or publish_stage.exists():
        raise FileExistsError("cell staging path already exists")
    # Nautilus initializes process-global Rust logging; a second node aborts the process.
    # The scheduler/CLI therefore owns one cell per fresh process.
    if _CELL_NODE_CREATED:
        raise RuntimeError("one BacktestNode per process; run each cell in a fresh process")
    work_dir.mkdir(parents=True)
    _CELL_NODE_CREATED = True
    node: BacktestNode | None = None
    try:
        run_config = _build_backtest_run_config(
            cell,
            catalog_path=catalog_path,
            start_time=start,
            end_time=end,
            staging_path=work_dir,
            chunk_size=chunk_size,
            rss_limit_bytes=rss_limit_bytes,
        )
        node = BacktestNode(configs=[run_config])
        node.run()
        node.dispose()
        node = None

        stream_manifest_path = work_dir / "stream_manifest.json"
        stream_manifest = json.loads(stream_manifest_path.read_text(encoding="utf-8"))
        _validate_stream_manifest(work_dir, stream_manifest)
        row_counts = {name: int(value) for name, value in stream_manifest["row_counts"].items()}
        source = StreamingEmissionSource(
            fills=None,
            orders=None,
            positions_ledger=None,
            bar_marks=work_dir / "bar_marks.parquet",
            event_log=work_dir / "event_log.jsonl",
            row_counts=row_counts,
        )
        publish_stage.mkdir()
        write_emission_v1_from_paths(
            publish_stage,
            source=source,
            instrument_id_map={cell.archive_symbol: cell.instrument_id},
            run_config=_run_metadata_config(
                cell,
                catalog_path=catalog_path,
                start_time=start,
                end_time=end,
                chunk_size=chunk_size,
            ),
            catalog_version=None,
            catalog_path=str(catalog_path),
            fence=fence,
            nautilus_version=nautilus_trader.__version__,
            platform=platform.platform(),
            extra_metadata={
                "cost_model": "NO_COST_CHARGED",
                "memory": {
                    "rss_limit_bytes": rss_limit_bytes,
                    "peak_rss_bytes": int(stream_manifest["peak_rss_bytes"]),
                    "sample_every": DEFAULT_MEMORY_SAMPLE_EVERY,
                },
                "state_snapshot": stream_manifest["snapshot"],
                "writer_limits": {
                    "max_rows": DEFAULT_WRITER_MAX_ROWS,
                    "max_bytes": DEFAULT_WRITER_MAX_BYTES,
                },
                "one_backtest_node": True,
            },
        )
        for name in ("levels", "raids", "tpo_profiles"):
            _copy_file(work_dir / f"{name}.parquet", publish_stage / f"{name}.parquet")
        if destroy_control:
            value_columns = (
                "swing_atr",
                "duration_ns",
                "strong_move",
                "pre_mfe_retrace",
            )
            control_report = destroy_post_confirmation(
                publish_stage / "raids.parquet",
                publish_stage / "raids_destroyed.parquet",
                group_columns=("archive_symbol", "timeframe", "config"),
                value_columns=value_columns,
                seed=destroy_seed,
            )
            eligible = int(control_report.get("rows", 0))
            changed = int(control_report.get("changed_rows", 0))
            if eligible == 0:
                control_report["non_vacuity"] = "VACUOUS_NO_ELIGIBLE"
            elif changed == 0:
                raise ValueError(
                    "destroy control is vacuous: post-confirmation outcome block did not change"
                )
            else:
                control_report["non_vacuity"] = "CHANGED"
            metadata_path = publish_stage / "run_metadata.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["destroy_control"] = {
                "path": "raids_destroyed.parquet",
                "seed": int(destroy_seed),
                "group_columns": ["archive_symbol", "timeframe", "config"],
                "value_columns": list(value_columns),
                **control_report,
            }
            metadata_path.write_text(
                json.dumps(metadata, indent=2, sort_keys=True, default=str) + "\n",
                encoding="utf-8",
            )
        os.replace(publish_stage, run_dir)
        shutil.rmtree(work_dir, ignore_errors=True)
        return run_dir
    except MemoryBudgetExceeded:
        if node is not None:
            node.dispose()
        _remove_publish_stage(publish_stage)
        raise
    except Exception:
        if node is not None:
            node.dispose()
        _remove_publish_stage(publish_stage)
        raise


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return _utc(parsed)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog-path", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--instrument-id", required=True)
    parser.add_argument("--archive-symbol", required=True)
    parser.add_argument("--venue", choices=("BYBIT", "CTRADER"), required=True)
    parser.add_argument("--observation-minutes", type=int, choices=(15, 30, 60), required=True)
    parser.add_argument(
        "--confirmation-method", choices=("BREAKOUT_BAR", "LEVEL_CLOSE"), required=True
    )
    parser.add_argument("--confirmation-reference", choices=("1H", "4H"), required=True)
    parser.add_argument("--level-config", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--rss-limit-bytes", type=int, default=DEFAULT_RSS_LIMIT_BYTES)
    parser.add_argument(
        "--destroy-control",
        action="store_true",
        help="emit the isolated deterministic future-destroy control",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse one-cell CLI arguments and return a process exit code."""
    args = _parser().parse_args(argv)
    cell = Exp100CellConfig(
        venue=args.venue,
        archive_symbol=args.archive_symbol,
        instrument_id=args.instrument_id,
        observation_minutes=args.observation_minutes,
        confirmation_method=args.confirmation_method,
        confirmation_reference=args.confirmation_reference,
        level_config=args.level_config,
    )
    published = run_cell(
        cell,
        catalog_path=args.catalog_path,
        run_dir=args.run_dir,
        start_time=_parse_datetime(args.start),
        end_time=_parse_datetime(args.end),
        chunk_size=args.chunk_size,
        rss_limit_bytes=args.rss_limit_bytes,
        destroy_control=args.destroy_control,
    )
    print(published)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
