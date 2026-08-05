"""TRAIN-only orchestration and canonical emissions for SPDR-021/022/023.

The runner reads each symbol once through its universe-specific fence, freezes calibration,
materialises the predeclared native and management schedules, executes each symbol in an
isolated Nautilus process, and atomically publishes one complete run directory.

Dry runs inspect catalog and manifest metadata only. They never query bars or create output.
"""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import platform
from pathlib import Path
import shutil
import threading
import time
from typing import Any, Literal

import nautilus_trader
from nautilus_trader.persistence.catalog import ParquetDataCatalog
import polars as pl

from xen.adaptive_management.contracts import (
    Device,
    ExperimentSpec,
    NativeArmSpec,
    OriginState,
    PolicySpec,
    build_management_lattice,
    build_native_lattice,
)
from xen.adaptive_management.engine import InstrumentSpec, WorkUnit, run_work_unit_subprocess
from xen.adaptive_management.entries import breach_origins, breakout_origins
from xen.adaptive_management.features import Calibration, build_feature_panel, fit_calibration
from xen.adaptive_management.native_parameters import materialise_native_arm
from xen.adaptive_management.policies import materialise_policy
from xen.nautilus.catalog_fence import (
    FenceManifest,
    FenceViolation,
    assert_within_fence,
    fence_attestation_payload,
    fenced_bar_query,
    load_fence_manifest,
)
from xen.nautilus.emission import write_emission_v1

Universe = Literal["crypto", "ctrader"]

REPO_ROOT = Path(__file__).resolve().parents[4]
CRYPTO_CATALOG = REPO_ROOT / "data" / "catalog"
CTRADER_CATALOG = REPO_ROOT / "data" / "catalog_ctrader"
CRYPTO_MANIFEST = (
    REPO_ROOT
    / "archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-011/artifacts"
    / "fence-manifest.json"
)
CTRADER_MANIFEST = (
    REPO_ROOT / "python/experiments/INFR-021/artifacts/fence-manifest.json"
)
CRYPTO_UNIVERSE = (
    REPO_ROOT
    / "docs/signal-registry/candidate-families/cf-voldir-001-universe.json"
)
CTRADER_SYMBOLS = ("EURUSD", "XAUUSD", "USTEC")

TABLE_ARTIFACTS = (
    "calibration",
    "features",
    "origins",
    "native_parameter_schedule",
    "episodes",
    "policy_schedule",
    "episode_results",
)
RAW_ARTIFACTS = tuple(f"{name}.parquet" for name in TABLE_ARTIFACTS) + (
    "config.json",
    "fence_attestation.json",
    "orders.parquet",
    "fills.parquet",
    "positions.parquet",
    "run_summary.json",
)

UNIT_FRAMES = TABLE_ARTIFACTS + (
    "state_ledger",
    "orders",
    "fills",
    "positions",
    "bar_marks",
)
UNIT_COMPLETION_FILE = "unit_complete.json"
HEARTBEAT_SECONDS = 600.0

SPREAD_COST_DISCLOSURE = {
    "spread_cost_status": "UNAVAILABLE_NOT_CHARGED",
    "spread_rt_bps": None,
    "cost_scope": "PARTIAL_FEES_FUNDING_ONLY",
    "implication": (
        "reported cost understates total cost; reported net performance is overstated"
    ),
    "prohibited_claims": ["fully-net", "cost-complete", "tradable", "deployable"],
}


@dataclass(frozen=True)
class UniverseConfig:
    name: Universe
    catalog_path: Path
    manifest_path: Path
    symbols: tuple[str, ...]
    instrument_ids: tuple[str, ...]
    catalog_version: str


@dataclass(frozen=True)
class RunPlan:
    spec: ExperimentSpec
    universe: UniverseConfig
    manifest: FenceManifest
    jobs: int
    metadata: dict[str, Any]


@dataclass(frozen=True)
class RunBundle:
    """Where each symbol's published frames live, plus the counts taken from their markers.

    The frames themselves are never all held at once: a full crypto breach cell is 210M rows,
    which is why assembly used to be killed after every symbol had already succeeded.
    """

    unit_dirs: dict[str, Path]
    instrument_id_map: dict[str, str]
    summary: dict[str, Any]


def universe_config(universe: Universe) -> UniverseConfig:
    """Return the frozen catalog, manifest and symbol identity for one universe."""
    if universe == "crypto":
        payload = json.loads(CRYPTO_UNIVERSE.read_text(encoding="utf-8"))
        symbols = tuple(str(symbol) for symbol in payload["symbols"])
        return UniverseConfig(
            name="crypto",
            catalog_path=CRYPTO_CATALOG,
            manifest_path=CRYPTO_MANIFEST,
            symbols=symbols,
            instrument_ids=tuple(f"{symbol}-LINEAR.BYBIT" for symbol in symbols),
            catalog_version="INFR-011-A6",
        )
    if universe == "ctrader":
        return UniverseConfig(
            name="ctrader",
            catalog_path=CTRADER_CATALOG,
            manifest_path=CTRADER_MANIFEST,
            symbols=CTRADER_SYMBOLS,
            instrument_ids=tuple(f"{symbol}.CTrader" for symbol in CTRADER_SYMBOLS),
            catalog_version="INFR-021",
        )
    raise ValueError(f"unknown universe: {universe}")


def _catalog_metadata(config: UniverseConfig) -> dict[str, Any]:
    """Read instrument metadata only; no bar query is performed."""
    catalog = ParquetDataCatalog(str(config.catalog_path))
    available = {str(instrument.id): type(instrument).__name__ for instrument in catalog.instruments()}
    missing = sorted(set(config.instrument_ids) - set(available))
    if missing:
        raise FileNotFoundError(f"catalog is missing declared instruments: {missing}")
    return {
        "catalog_path": str(config.catalog_path),
        "available_instruments": list(config.instrument_ids),
        "instrument_types": {key: available[key] for key in config.instrument_ids},
    }


def _run_plan(
    spec: ExperimentSpec,
    universe: Universe,
    *,
    jobs: int,
) -> RunPlan:
    if jobs < 1:
        raise ValueError("jobs must be at least 1")
    config = universe_config(universe)
    manifest = load_fence_manifest(config.manifest_path)
    assert_within_fence(
        manifest,
        manifest.analysis_start_utc,
        manifest.train_end_utc,
        band="TRAIN",
    )
    metadata = _catalog_metadata(config)
    return RunPlan(spec=spec, universe=config, manifest=manifest, jobs=jobs, metadata=metadata)


def _plan_payload(plan: RunPlan, *, dry_run: bool) -> dict[str, Any]:
    native = build_native_lattice(plan.spec.experiment_id)
    management = build_management_lattice(plan.spec.experiment_id)
    return {
        "experiment_id": plan.spec.experiment_id,
        "universe": plan.universe.name,
        "band": "TRAIN",
        "dry_run": dry_run,
        "jobs": plan.jobs,
        "symbols": list(plan.universe.symbols),
        "instrument_ids": list(plan.universe.instrument_ids),
        "catalog_path": str(plan.universe.catalog_path),
        "manifest_path": str(plan.universe.manifest_path),
        "manifest_sha256": plan.manifest.sha256,
        "train_start_utc": _iso(plan.manifest.analysis_start_utc),
        "train_end_utc": _iso(plan.manifest.train_end_utc),
        "native_arms": len(native),
        "native_adaptive_arms": sum(arm.is_adaptive for arm in native),
        "management_arms": len(management),
        "work_units": len(plan.universe.symbols),
        "base_size_increments": BASE_SIZE_INCREMENTS,
        "catalog_metadata": plan.metadata,
        "spread_cost_disclosure": SPREAD_COST_DISCLOSURE,
    }


def run_experiment(
    spec: ExperimentSpec,
    universe: Universe,
    output: Path,
    *,
    band: str = "TRAIN",
    jobs: int = 1,
    dry_run: bool = False,
    resume: bool = False,
    progress: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Run one experiment/universe independently and publish a complete atomic emission."""
    if band != "TRAIN":
        raise FenceViolation("adaptive-management SPDR runners are TRAIN-only")
    if spec.experiment_id not in {"SPDR-021", "SPDR-022", "SPDR-023"}:
        raise ValueError(f"unsupported experiment: {spec.experiment_id}")
    output = Path(output)
    in_progress = output.parent / f".{output.name}.inprogress"
    if output.exists():
        raise FileExistsError(f"refusing to overwrite completed output: {output}")
    if in_progress.exists() and not resume:
        raise FileExistsError(
            f"refusing to overwrite in-progress directory (use resume): {in_progress}"
        )
    plan = _run_plan(spec, universe, jobs=jobs)
    payload = _plan_payload(plan, dry_run=dry_run)
    if dry_run:
        return payload

    output.parent.mkdir(parents=True, exist_ok=True)
    config_hash = _config_hash(payload)
    resuming = resume and in_progress.exists()
    if resuming:
        _assert_resume_identity(in_progress, config_hash)
    else:
        in_progress.mkdir(parents=True)
        _atomic_json(payload, in_progress / "config.json")
        _atomic_json(_software_pins(plan, config_hash), in_progress / "software_pins.json")

    try:
        bundle = _execute_plan(
            plan,
            in_progress,
            config_hash=config_hash,
            resume=resuming,
            progress=progress,
        )
        _write_bundle(plan, payload, bundle, in_progress)
    except BaseException as error:
        error.add_note(f"in-progress directory preserved for resume: {in_progress}")
        raise

    for scratch in ("work", "units"):
        shutil.rmtree(in_progress / scratch, ignore_errors=True)
    in_progress.replace(output)
    return {**payload, **bundle.summary, "output": str(output)}


def _software_pins(plan: RunPlan, config_hash: str) -> dict[str, Any]:
    return {
        "experiment_id": plan.spec.experiment_id,
        "universe": plan.universe.name,
        "config_hash": config_hash,
        "manifest_sha256": plan.manifest.sha256,
        "catalog_version": plan.universe.catalog_version,
        "nautilus_version": nautilus_trader.__version__,
        "polars_version": pl.__version__,
        "python_version": platform.python_version(),
    }


def _config_hash(payload: dict[str, Any]) -> str:
    """Hash the research-identity part of a plan; operational knobs are excluded."""
    identity = {
        key: value
        for key, value in payload.items()
        if key not in {"jobs", "dry_run"}
    }
    encoded = json.dumps(identity, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _assert_resume_identity(in_progress: Path, config_hash: str) -> None:
    recorded = in_progress / "config.json"
    if not recorded.exists():
        raise ValueError(f"resume configuration mismatch: no config.json in {in_progress}")
    previous = json.loads(recorded.read_text(encoding="utf-8"))
    if _config_hash(previous) != config_hash:
        raise ValueError(
            f"resume configuration mismatch: {in_progress} was written for a different plan"
        )


def _execute_plan(
    plan: RunPlan,
    workspace: Path,
    *,
    config_hash: str = "",
    resume: bool = False,
    progress: Callable[[dict[str, Any]], None] | None = None,
) -> RunBundle:
    """Prepare and execute every symbol without widening the declared TRAIN fence."""
    catalog = ParquetDataCatalog(str(plan.universe.catalog_path))
    instruments = {str(item.id): item for item in catalog.instruments()}
    # Each worker thread reads through its own catalog handle.
    _local = threading.local()

    def _catalog() -> ParquetDataCatalog:
        existing = getattr(_local, "catalog", None)
        if existing is None:
            existing = ParquetDataCatalog(str(plan.universe.catalog_path))
            _local.catalog = existing
        return existing
    units_root = workspace / "units"
    units_root.mkdir(parents=True, exist_ok=True)
    symbols = list(plan.universe.symbols)
    instrument_map = dict(zip(symbols, plan.universe.instrument_ids, strict=True))

    reused = [
        symbol
        for symbol in symbols
        if resume and _unit_is_complete(units_root / symbol, config_hash)
    ]
    pending = [symbol for symbol in symbols if symbol not in set(reused)]

    reporter = _ProgressReporter(
        progress,
        experiment_id=plan.spec.experiment_id,
        universe=plan.universe.name,
        total_units=len(symbols),
    )
    reporter.start()
    try:
        for symbol in reused:
            reporter.unit_done(_unit_row_count(units_root / symbol))

        def prepare(symbol: str) -> tuple[str, WorkUnit, dict[str, pl.DataFrame], pl.DataFrame]:
            instrument_id = instrument_map[symbol]
            instrument = instruments[instrument_id]
            bar_type = f"{instrument_id}-1-MINUTE-LAST-EXTERNAL"
            bars = fenced_bar_query(
                _catalog(),
                [bar_type],
                plan.manifest.analysis_start_utc,
                plan.manifest.train_end_utc,
                band="TRAIN",
                manifest=plan.manifest,
            )
            if not bars:
                raise RuntimeError(f"TRAIN query returned no bars for {instrument_id}")
            minute = _bars_frame(symbol, bars)
            h1 = _hourly_frame(minute)
            tables, schedule = _materialise_symbol(plan.spec, h1)
            symbol_root = workspace / "work" / symbol
            shutil.rmtree(symbol_root, ignore_errors=True)
            symbol_root.mkdir(parents=True)
            bars_path = symbol_root / "bars.parquet"
            schedule_path = symbol_root / "schedule.parquet"
            _atomic_parquet(minute, bars_path)
            _atomic_parquet(schedule, schedule_path)
            unit = WorkUnit(
                unit_id=f"{plan.spec.experiment_id}-{plan.universe.name}-{symbol}",
                instrument=_instrument_spec(symbol, instrument),
                bars_path=str(bars_path),
                schedule_path=str(schedule_path),
                output_dir=str(symbol_root / "engine"),
                base_trade_size=_base_trade_size(instrument),
                fence_start_ns=int(plan.manifest.analysis_start_utc.timestamp() * 1e9),
                fence_end_ns=int(plan.manifest.train_end_utc.timestamp() * 1e9),
            )
            return symbol, unit, tables, _bar_marks(symbol, instrument_id, minute)

        def execute(
            item: tuple[str, WorkUnit, dict[str, pl.DataFrame], pl.DataFrame],
        ) -> int:
            symbol, unit, tables, bar_marks = item
            report = run_work_unit_subprocess(unit)
            frames = {name: tables[name] for name in TABLE_ARTIFACTS}
            frames["state_ledger"] = report["state_ledger"]
            frames["orders"] = report["orders"]
            frames["fills"] = report["fills"]
            frames["positions"] = report["positions"]
            frames["bar_marks"] = bar_marks
            _publish_unit(units_root / symbol, frames, config_hash)
            return sum(frame.height for frame in frames.values())

        def prepare_and_execute(symbol: str) -> int:
            return execute(prepare(symbol))

        if plan.jobs == 1:
            for symbol in pending:
                reporter.unit_done(prepare_and_execute(symbol))
        else:
            # Prepare inside the worker, not all upfront: a prepared symbol holds its whole
            # schedule in memory until it is published, so preparing every pending symbol
            # first made peak memory scale with the symbol count instead of with `jobs`.
            with ThreadPoolExecutor(max_workers=plan.jobs) as pool:
                for rows in pool.map(prepare_and_execute, pending):
                    reporter.unit_done(rows)
    finally:
        reporter.stop()

    unit_dirs = {symbol: units_root / symbol for symbol in symbols}
    rows: dict[str, int] = {}
    for symbol in symbols:
        marker = json.loads(
            (unit_dirs[symbol] / UNIT_COMPLETION_FILE).read_text(encoding="utf-8")
        )
        for name, count in marker.get("rows", {}).items():
            rows[name] = rows.get(name, 0) + int(count)
    return RunBundle(
        unit_dirs=unit_dirs,
        instrument_id_map=instrument_map,
        summary={
            "work_units": len(symbols),
            "completed_work_units": len(symbols),
            "reused_units": len(reused),
            "rerun_units": len(pending),
            "n_origins": rows.get("origins", 0),
            "n_episodes": rows.get("episodes", 0),
            "n_policy_rows": rows.get("policy_schedule", 0),
            "n_orders": rows.get("orders", 0),
            "n_fills": rows.get("fills", 0),
            "n_positions": rows.get("positions", 0),
        },
    )


def _publish_unit(
    unit_dir: Path,
    frames: dict[str, pl.DataFrame],
    config_hash: str,
) -> None:
    """Write one symbol's frames, then its completion marker last."""
    shutil.rmtree(unit_dir, ignore_errors=True)
    staging = unit_dir.parent / f".{unit_dir.name}.partial"
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True)
    digest = hashlib.sha256()
    for name in UNIT_FRAMES:
        path = staging / f"{name}.parquet"
        _atomic_parquet(frames[name], path)
        digest.update(name.encode("utf-8"))
        digest.update(_file_sha256(path))
    _atomic_json(
        {
            "config_hash": config_hash,
            "content_hash": digest.hexdigest(),
            "rows": {name: frames[name].height for name in UNIT_FRAMES},
        },
        staging / UNIT_COMPLETION_FILE,
    )
    staging.replace(unit_dir)


def _unit_is_complete(unit_dir: Path, config_hash: str) -> bool:
    marker = unit_dir / UNIT_COMPLETION_FILE
    if not marker.exists():
        return False
    try:
        payload = json.loads(marker.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    if payload.get("config_hash") != config_hash:
        return False
    digest = hashlib.sha256()
    for name in UNIT_FRAMES:
        path = unit_dir / f"{name}.parquet"
        if not path.exists():
            return False
        digest.update(name.encode("utf-8"))
        digest.update(_file_sha256(path))
    return digest.hexdigest() == payload.get("content_hash")


def _file_sha256(path: Path) -> bytes:
    """Hash an artifact without allocating one Python bytes object for the whole file."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").digest()


def _unit_row_count(unit_dir: Path) -> int:
    payload = json.loads((unit_dir / UNIT_COMPLETION_FILE).read_text(encoding="utf-8"))
    return int(sum(payload.get("rows", {}).values()))


def _read_unit(unit_dir: Path) -> dict[str, pl.DataFrame]:
    return {
        name: pl.read_parquet(unit_dir / f"{name}.parquet") for name in UNIT_FRAMES
    }


class _ProgressReporter:
    """Emit one event at start, one per completed unit, one at the end, plus heartbeats."""

    def __init__(
        self,
        callback: Callable[[dict[str, Any]], None] | None,
        *,
        experiment_id: str,
        universe: str,
        total_units: int,
        heartbeat_seconds: float = HEARTBEAT_SECONDS,
    ) -> None:
        self._callback = callback
        self._experiment_id = experiment_id
        self._universe = universe
        self._total_units = total_units
        self._heartbeat_seconds = heartbeat_seconds
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._started = time.monotonic()
        self._completed = 0
        self._rows = 0

    def start(self) -> None:
        if self._callback is None:
            return
        self._started = time.monotonic()
        self._emit()
        self._thread = threading.Thread(target=self._heartbeat, daemon=True)
        self._thread.start()

    def unit_done(self, rows: int) -> None:
        with self._lock:
            self._completed += 1
            self._rows += int(rows)
        self._emit()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None
        self._emit()

    def _heartbeat(self) -> None:
        while not self._stop.wait(self._heartbeat_seconds):
            self._emit()

    def _emit(self) -> None:
        if self._callback is None:
            return
        with self._lock:
            completed = self._completed
            rows = self._rows
        elapsed = max(time.monotonic() - self._started, 1e-9)
        throughput = rows / elapsed
        eta: float | None = None
        if completed and completed < self._total_units:
            eta = (elapsed / completed) * (self._total_units - completed)
        self._callback(
            {
                "experiment_id": self._experiment_id,
                "universe": self._universe,
                "completed_units": completed,
                "total_units": self._total_units,
                "elapsed_seconds": elapsed,
                "rows_processed": rows,
                "throughput_rows_per_second": throughput,
                "eta_seconds": eta,
            }
        )


def _materialise_symbol(
    spec: ExperimentSpec,
    h1: pl.DataFrame,
) -> tuple[dict[str, pl.DataFrame], pl.DataFrame]:
    train_start = h1["ts"].min()
    train_end = h1["ts"].max()
    calibration = fit_calibration(h1, train_start, train_end)
    features = build_feature_panel(h1, calibration)
    medians = {
        "range": calibration.median_range_scale_bps,
        "swing": calibration.median_swing_scale_bps,
    }
    if spec.experiment_id == "SPDR-021":
        origin_work = breakout_origins(
            h1.join(features.select("symbol", "ts", "atr20"), on=["symbol", "ts"])
        )
        public_origins = origin_work
    else:
        origin_work = breach_origins(h1, features).with_columns(
            pl.col("decision_ts").cast(pl.Datetime("ns", "UTC"))
        )
        public_origins = origin_work.select(
            column for column in origin_work.columns if not column.startswith("_path_")
        )

    native_parts: list[pl.DataFrame] = []
    fixed_by_variant: dict[str, pl.DataFrame] = {}
    for arm in build_native_lattice(spec.experiment_id):
        episodes = materialise_native_arm(origin_work, features, medians, arm)
        native_parts.append(_native_schedule(episodes, arm, spec.experiment_id))
        if not arm.is_adaptive:
            fixed_by_variant[arm.entry_variant] = episodes
    native_schedule = _concat(native_parts)

    policy_parts: list[pl.DataFrame] = []
    policies = build_management_lattice(spec.experiment_id)
    for variant, fixed_episodes in fixed_by_variant.items():
        materialised: list[tuple[PolicySpec, pl.DataFrame]] = []
        for policy in policies:
            rows = materialise_policy(
                fixed_episodes,
                features,
                medians,
                policy,
                experiment_id=spec.experiment_id,
            )
            materialised.append((policy, rows))
        policy_parts.extend(_management_schedules(materialised, variant, spec.experiment_id))
    policy_schedule = _concat(policy_parts)
    execution_schedule = _concat([native_schedule, policy_schedule]).select(
        _strategy_columns()
    )

    return (
        {
            "calibration": _calibration_frame(calibration),
            "features": features,
            "origins": public_origins,
            "native_parameter_schedule": native_schedule,
            "episodes": native_schedule,
            "policy_schedule": policy_schedule,
            "episode_results": pl.DataFrame(),
        },
        execution_schedule,
    )


def _native_schedule(
    episodes: pl.DataFrame,
    arm: NativeArmSpec,
    experiment_id: str,
) -> pl.DataFrame:
    arm_class = (
        "FIXED_NATIVE"
        if not arm.is_adaptive
        else "NATIVE_COMBINATION"
        if arm.combination_id
        else "NATIVE"
    )
    hold = 1 if experiment_id == "SPDR-021" else 4
    return _schedule_defaults(episodes).with_columns(
        pl.lit(arm.native_arm_id).alias("arm_id"),
        pl.lit(arm_class).alias("arm_class"),
        pl.lit(arm.native_arm_id).alias("native_arm_id"),
        pl.lit("NONE").alias("policy_id"),
        pl.lit(str(Device.NONE)).alias("device"),
        pl.lit(None, dtype=pl.Utf8).alias("exit_reason"),
        pl.lit(hold, dtype=pl.Int64).alias("hold_bars"),
        pl.lit(1.0).alias("risk_size"),
    )


def _management_schedules(
    materialised: list[tuple[PolicySpec, pl.DataFrame]],
    entry_variant: str,
    experiment_id: str,
) -> list[pl.DataFrame]:
    output: list[pl.DataFrame] = []
    device_groups: dict[str, list[tuple[PolicySpec, pl.DataFrame]]] = {}
    for policy, frame in materialised:
        if policy.combination_id and policy.combination_id.startswith("DC_"):
            device_groups.setdefault(policy.combination_id, []).append((policy, frame))
            continue
        output.append(_policy_schedule(frame, policy, entry_variant, experiment_id))
    for combination_id, group in device_groups.items():
        output.append(
            _device_combination_schedule(
                combination_id, group, entry_variant, experiment_id
            )
        )
    return output


def _policy_schedule(
    frame: pl.DataFrame,
    policy: PolicySpec,
    entry_variant: str,
    experiment_id: str,
) -> pl.DataFrame:
    arm_class = (
        "FIXED_MANAGEMENT"
        if not policy.is_adaptive
        else "MANAGEMENT_COMPONENT_COMBINATION"
        if policy.combination_id
        else "MANAGEMENT"
    )
    scheduled = _schedule_defaults(frame)
    prior_state = (
        pl.col("state")
        if "state" in scheduled.columns
        else pl.lit(str(OriginState.ORDER_CREATED))
    )
    return scheduled.with_columns(
        pl.when(pl.col("eligible").fill_null(False))
        .then(prior_state)
        .otherwise(pl.lit(str(OriginState.NO_FEATURE)))
        .alias("state"),
        pl.lit(policy.policy_id).alias("arm_id"),
        pl.lit(arm_class).alias("arm_class"),
        pl.lit(None, dtype=pl.Utf8).alias("native_arm_id"),
        pl.lit(policy.policy_id).alias("policy_id"),
        pl.lit(str(policy.device)).alias("device"),
        pl.lit(entry_variant).alias("entry_variant"),
        pl.lit(experiment_id).alias("experiment_id"),
        pl.lit(1.0).alias("risk_size")
        if "risk_size" not in frame.columns
        else pl.col("risk_size").fill_null(1.0),
    )


def _device_combination_schedule(
    combination_id: str,
    group: list[tuple[PolicySpec, pl.DataFrame]],
    entry_variant: str,
    experiment_id: str,
) -> pl.DataFrame:
    base = _schedule_defaults(group[0][1])
    prior_state = (
        pl.col("state")
        if "state" in base.columns
        else pl.lit(str(OriginState.ORDER_CREATED))
    )
    eligible = pl.Series("eligible", [True] * base.height)
    devices: list[str] = []
    for policy, frame in group:
        devices.append(str(policy.device))
        eligible = eligible & frame["eligible"].fill_null(False)
        for column in (
            "target_distance_bps",
            "stop_distance_bps",
            "trail_distance_bps",
            "trail_activation_bps",
            "hold_bars",
        ):
            if column in frame.columns:
                base = base.with_columns(frame[column].alias(column))
    return base.with_columns(eligible).with_columns(
        pl.when(pl.col("eligible"))
        .then(prior_state)
        .otherwise(pl.lit(str(OriginState.NO_FEATURE)))
        .alias("state"),
        pl.lit(combination_id).alias("arm_id"),
        pl.lit("MANAGEMENT_DEVICE_COMBINATION").alias("arm_class"),
        pl.lit(None, dtype=pl.Utf8).alias("native_arm_id"),
        pl.lit(combination_id).alias("policy_id"),
        pl.lit("+".join(devices)).alias("device"),
        pl.lit(entry_variant).alias("entry_variant"),
        pl.lit(experiment_id).alias("experiment_id"),
        pl.lit(1.0).alias("risk_size"),
    )


def _schedule_defaults(frame: pl.DataFrame) -> pl.DataFrame:
    defaults: dict[str, tuple[Any, pl.DataType]] = {
        "target_distance_bps": (None, pl.Float64),
        "stop_distance_bps": (None, pl.Float64),
        "trail_distance_bps": (None, pl.Float64),
        "trail_activation_bps": (None, pl.Float64),
        "hold_bars": (None, pl.Int64),
        "risk_size": (1.0, pl.Float64),
        "exit_reason": (None, pl.Utf8),
    }
    expressions = [
        pl.lit(value, dtype=dtype).alias(name)
        for name, (value, dtype) in defaults.items()
        if name not in frame.columns
    ]
    return frame.with_columns(expressions) if expressions else frame


def _strategy_columns() -> list[str]:
    from xen.adaptive_management.strategy import SCHEDULE_COLUMNS

    return list(SCHEDULE_COLUMNS)


def _bars_frame(symbol: str, bars: list[Any]) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "symbol": [symbol] * len(bars),
            "ts": [
                datetime.fromtimestamp(int(bar.ts_event) / 1e9, tz=timezone.utc)
                for bar in bars
            ],
            "open": [float(bar.open) for bar in bars],
            "high": [float(bar.high) for bar in bars],
            "low": [float(bar.low) for bar in bars],
            "close": [float(bar.close) for bar in bars],
            "volume": [float(bar.volume) for bar in bars],
        }
    ).with_columns(pl.col("ts").cast(pl.Datetime("ns", "UTC")))


def _hourly_frame(minutes: pl.DataFrame) -> pl.DataFrame:
    return (
        minutes.sort("ts")
        .group_by_dynamic(
            "ts",
            every="1h",
            period="1h",
            closed="right",
            label="right",
        )
        .agg(
            pl.col("symbol").first(),
            pl.col("open").first(),
            pl.col("high").max(),
            pl.col("low").min(),
            pl.col("close").last(),
            pl.col("volume").sum(),
            pl.len().alias("minute_count"),
        )
        .filter(pl.col("minute_count") > 0)
        .drop("minute_count")
        .sort("ts")
    )


# The SIZE device scales unit risk between 0.5x and 2.0x, so the base quantity must keep every
# multiple representable on the instrument's own size grid. A flat "1" is below the increment of
# some crypto instruments (BONK trades in lots of 100), where a 0.5x arm rounds to zero and the
# venue rejects the order. 1000 increments keeps the multiplier faithful to ~0.1% everywhere.
BASE_SIZE_INCREMENTS = 1000


def _base_trade_size(instrument: Any) -> str:
    """Base quantity for one instrument, on its own size grid."""
    increment = Decimal(str(instrument.size_increment))
    base = increment * BASE_SIZE_INCREMENTS
    if base * Decimal("0.5") < increment:
        raise ValueError(
            f"base trade size {base} cannot represent a 0.5x risk arm on {instrument.id}"
        )
    return format(base.normalize(), "f")


def _instrument_spec(symbol: str, instrument: Any) -> InstrumentSpec:
    venue = str(instrument.id.venue)
    kind = type(instrument).__name__.lower()
    return InstrumentSpec(
        symbol=str(instrument.id.symbol),
        instrument_id=str(instrument.id),
        venue=venue,
        price_precision=int(instrument.price_precision),
        size_precision=int(instrument.size_precision),
        price_increment=str(instrument.price_increment),
        size_increment=str(instrument.size_increment),
        quote_currency=str(instrument.quote_currency),
        base_currency=str(getattr(instrument, "base_currency", "USD") or "USD"),
        instrument_kind=kind,
        asset_class=getattr(getattr(instrument, "asset_class", None), "name", ""),
    )


def _calibration_frame(calibration: Calibration) -> pl.DataFrame:
    rows = []
    for symbol in calibration.row_count_by_symbol:
        rows.append(
            {
                "symbol": symbol,
                "start_ts": calibration.start_ts,
                "end_ts": calibration.end_ts,
                "train_start_ts": calibration.train_start_ts,
                "train_end_ts": calibration.train_end_ts,
                "row_count": calibration.row_count_by_symbol[symbol],
                "range_conversion": calibration.range_conversion[symbol],
                "median_range_scale_bps": calibration.median_range_scale_bps[symbol],
                "median_swing_scale_bps": calibration.median_swing_scale_bps[symbol],
                "p90_move_bps": calibration.p90_move_bps[symbol],
            }
        )
    return pl.DataFrame(rows)


def _bar_marks(symbol: str, instrument_id: str, frame: pl.DataFrame) -> pl.DataFrame:
    return frame.select(
        pl.lit(symbol).alias("symbol"),
        pl.lit(instrument_id).alias("instrument_id"),
        pl.col("ts").alias("SourceCloseTime"),
        pl.col("open").alias("RealOpen"),
        pl.col("high").alias("RealHigh"),
        pl.col("low").alias("RealLow"),
        pl.col("close").alias("RealClose"),
    )


def _write_bundle(
    plan: RunPlan,
    config_payload: dict[str, Any],
    bundle: RunBundle,
    workspace: Path,
) -> None:
    order = list(bundle.unit_dirs)
    for name in TABLE_ARTIFACTS:
        # episode_results is the engine's state ledger; the per-unit file of that name is the
        # empty placeholder produced before execution.
        source = "state_ledger" if name == "episode_results" else name
        _stream_units(
            [bundle.unit_dirs[symbol] / f"{source}.parquet" for symbol in order],
            workspace / f"{name}.parquet",
        )
    for name in ("orders", "fills", "positions"):
        _stream_units(
            [bundle.unit_dirs[symbol] / f"{name}.parquet" for symbol in order],
            workspace / f"{name}.parquet",
        )
    canonical_config = _canonical_config(config_payload)
    attestation = _universe_attestation(plan.universe, plan.manifest)
    _atomic_json(attestation, workspace / "fence_attestation.json")
    _atomic_json(bundle.instrument_id_map, workspace / "instrument_id_map.json")
    for symbol, instrument_id in sorted(bundle.instrument_id_map.items()):
        unit = bundle.unit_dirs[symbol]
        # One symbol in memory at a time: its unit already holds exactly that symbol's rows.
        unit_frames = {
            name: pl.read_parquet(unit / f"{name}.parquet")
            for name in ("fills", "orders", "positions", "bar_marks")
        }
        write_emission_v1(
            workspace / "cells" / symbol,
            fills=_for_instrument(unit_frames["fills"], instrument_id),
            orders=_for_instrument(unit_frames["orders"], instrument_id),
            positions_ledger=_for_instrument(unit_frames["positions"], instrument_id),
            bar_marks=_for_instrument(unit_frames["bar_marks"], instrument_id),
            instrument_id_map={symbol: instrument_id},
            run_config={**canonical_config, "symbol": symbol},
            catalog_version=plan.universe.catalog_version,
            catalog_path=str(plan.universe.catalog_path),
            fence=attestation,
            nautilus_version=nautilus_trader.__version__,
            platform=platform.platform(),
            extra_metadata={
                "experiment_id": plan.spec.experiment_id,
                "universe": plan.universe.name,
                "symbol": symbol,
                "spread_cost_disclosure": SPREAD_COST_DISCLOSURE,
            },
        )
    _atomic_json(canonical_config, workspace / "config.json")
    _atomic_json(
        {
            "jobs": config_payload["jobs"],
            "dry_run": config_payload["dry_run"],
            "nautilus_version": nautilus_trader.__version__,
            "platform": platform.platform(),
        },
        workspace / "run_environment.json",
    )
    canonical_summary = {
        key: value
        for key, value in bundle.summary.items()
        if key not in {"reused_units", "rerun_units"}
    }
    _atomic_json(
        {
            **canonical_summary,
            "experiment_id": plan.spec.experiment_id,
            "universe": plan.universe.name,
            "band": "TRAIN",
            "hard_integrity": "NOT_YET_RUN_TASK_8",
            "spread_cost_disclosure": SPREAD_COST_DISCLOSURE,
        },
        workspace / "run_summary.json",
    )
    missing = sorted(set(RAW_ARTIFACTS) - {path.name for path in workspace.iterdir()})
    if missing:
        raise RuntimeError(f"incomplete run bundle: missing {missing}")


def _stream_units(paths: list[Path], target: Path) -> None:
    """Concatenate per-symbol parquet files without holding the whole run in memory."""
    usable = [path for path in paths if path.exists() and pl.read_parquet_schema(path)]
    temporary = target.with_suffix(".parquet.tmp")
    if not usable:
        pl.DataFrame().write_parquet(temporary)
        temporary.replace(target)
        return
    if len(usable) == 1:
        shutil.copyfile(usable[0], temporary)
        temporary.replace(target)
        return
    pl.scan_parquet(usable).sink_parquet(temporary)
    temporary.replace(target)


def _canonical_config(payload: dict[str, Any]) -> dict[str, Any]:
    """Config identity of the run; operational knobs live in run_environment.json."""
    return {key: value for key, value in payload.items() if key not in {"jobs", "dry_run"}}


def _for_instrument(frame: pl.DataFrame, instrument_id: str) -> pl.DataFrame:
    if frame.is_empty() or "instrument_id" not in frame.columns:
        return frame
    return frame.filter(pl.col("instrument_id").cast(pl.Utf8) == instrument_id)


def _universe_attestation(
    config: UniverseConfig,
    manifest: FenceManifest,
) -> dict[str, Any]:
    payload = fence_attestation_payload(manifest)
    payload["manifest_path"] = config.manifest_path.relative_to(REPO_ROOT).as_posix()
    payload["universe"] = config.name
    payload["catalog_path"] = config.catalog_path.relative_to(REPO_ROOT).as_posix()
    return payload


def _atomic_parquet(frame: pl.DataFrame, path: Path) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.write_parquet(temporary)
    temporary.replace(path)


def _atomic_json(payload: dict[str, Any], path: Path) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _concat(frames: list[pl.DataFrame]) -> pl.DataFrame:
    nonempty = [frame for frame in frames if frame is not None and frame.width]
    if not nonempty:
        return pl.DataFrame()
    return pl.concat(nonempty, how="diagonal_relaxed")


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")
