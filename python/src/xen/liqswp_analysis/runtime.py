"""Integrity-first fixture and live orchestration with atomic result writes."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Protocol

import numpy as np
import polars as pl

from xen.liqswp_analysis.contract import AnalysisResult, IntegrityStatus


class ExperimentAdapter(Protocol):
    """Explicit experiment-owned behavior consumed by the shared runtime."""

    experiment: str

    def fixture_frame(self) -> pl.DataFrame: ...

    def live_frame(
        self, source_root: Path, gate_path: Path
    ) -> tuple[pl.DataFrame, dict[str, Any], IntegrityStatus]: ...

    def integrity(self, frame: pl.DataFrame) -> IntegrityStatus: ...

    def population(self, frame: pl.DataFrame) -> dict[str, Any]: ...

    def analyze(self, frame: pl.DataFrame) -> tuple[dict[str, Any], ...]: ...

    def extra(self, frame: pl.DataFrame) -> dict[str, Any]: ...


def _json_default(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"not JSON serializable: {type(value).__name__}")


def _write_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, default=_json_default)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _merge_integrity(source: IntegrityStatus, experiment: IntegrityStatus) -> IntegrityStatus:
    reasons = tuple(dict.fromkeys((*source.reasons, *experiment.reasons)))
    return IntegrityStatus(
        blocking_pass=source.blocking_pass and experiment.blocking_pass and not reasons,
        reasons=reasons,
        evidence={"source": source.to_dict(), "experiment": experiment.to_dict()},
    )


def _execute(
    adapter: ExperimentAdapter,
    frame: pl.DataFrame,
    source: dict[str, Any],
    source_integrity: IntegrityStatus,
    output: Path,
) -> dict[str, Any]:
    experiment_integrity = (
        adapter.integrity(frame) if source_integrity.blocking_pass else IntegrityStatus(True)
    )
    integrity = _merge_integrity(source_integrity, experiment_integrity)
    population = adapter.population(frame)
    value_rows = adapter.analyze(frame) if integrity.blocking_pass else ()
    extra = adapter.extra(frame) if integrity.blocking_pass else {}
    result = AnalysisResult(
        experiment=adapter.experiment,
        source=source,
        population=population,
        integrity=integrity,
        value_rows=value_rows,
        extra=extra,
    )
    payload = result.to_dict()
    _write_atomic(output, payload)
    return payload


def run_fixture(adapter: ExperimentAdapter, output: Path) -> dict[str, Any]:
    """Run a deterministic fixture through the same integrity/value ordering as live."""
    frame = adapter.fixture_frame()
    return _execute(adapter, frame, {"mode": "fixture"}, IntegrityStatus(True), output)


def run_live(
    adapter: ExperimentAdapter,
    source_root: Path,
    gate_path: Path,
    output: Path,
) -> dict[str, Any]:
    """Run the registered live analysis; callers remain responsible for operator gating."""
    frame, source, source_integrity = adapter.live_frame(source_root, gate_path)
    return _execute(adapter, frame, source, source_integrity, output)
