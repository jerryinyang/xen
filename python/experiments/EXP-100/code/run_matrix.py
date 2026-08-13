"""Run the frozen EXP-100 matrix through one fresh subprocess per cell."""

from __future__ import annotations

import argparse
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import dataclass
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time

from run_experiment import execution_pin

# Operator amendment 2026-08-12: crypto/Bybit universe excluded from EXP-100.
# Full matrix is cTrader replication assets only.
CTRADER_SYMBOLS = ("EURUSD", "XAUUSD", "USTEC")
OBSERVATION_MINUTES = (15, 30, 60)
CONFIRMATION_METHODS = ("BREAKOUT_BAR", "LEVEL_CLOSE")
LEVEL_CONFIGS = (
    "PREVIOUS_1H",
    "PREVIOUS_4H",
    "PREVIOUS_1D",
    "PREVIOUS_1W",
    "PREVIOUS_ASIA",
    "PREVIOUS_EUROPE",
    "PREVIOUS_AMERICA",
    "ROLLING_7",
    "ROLLING_14",
    "ROLLING_22",
    "ROLLING_252",
)
# 30-day TRAIN probe ending inside the cTrader INFR-021 fence (train_end=2023-11-22).
PREFLIGHT_START = datetime(2023, 10, 23, tzinfo=UTC)
PREFLIGHT_END = datetime(2023, 11, 21, 23, 59, tzinfo=UTC)
DEFAULT_CHUNK_SIZE = 50_000
DEFAULT_RSS_LIMIT_BYTES = 1_610_612_736
DEFAULT_MIN_FREE_BYTES = 20 * 1024**3
DEFAULT_TIMEOUT_SECONDS = 2 * 60 * 60
DEFAULT_WORKERS = 1
REPO_ROOT = Path(__file__).resolve().parents[4]


@dataclass(frozen=True, slots=True)
class MatrixCell:
    """Frozen identity and TRAIN bounds for one scheduled cell."""

    venue: str
    archive_symbol: str
    instrument_id: str
    observation_minutes: int
    confirmation_method: str
    confirmation_reference: str
    level_config: str
    start: datetime
    end: datetime

    @property
    def cell_id(self) -> str:
        parts = (
            self.venue,
            self.archive_symbol,
            f"{self.observation_minutes}m",
            self.confirmation_method,
            self.confirmation_reference,
            self.level_config,
        )
        return "-".join(part.lower() for part in parts)


def _cell(
    venue: str,
    symbol: str,
    observation_minutes: int,
    confirmation_method: str,
    level_config: str,
    *,
    confirmation_reference: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> MatrixCell:
    pin = execution_pin(venue)
    suffix = "-LINEAR.BYBIT" if venue == "BYBIT" else ".CTrader"
    if confirmation_reference is None:
        confirmation_reference = "1H"
    return MatrixCell(
        venue=venue,
        archive_symbol=symbol,
        instrument_id=f"{symbol}{suffix}",
        observation_minutes=observation_minutes,
        confirmation_method=confirmation_method,
        confirmation_reference=confirmation_reference,
        level_config=level_config,
        start=start or pin.train_start,
        end=end or pin.train_end,
    )


def _confirmation_references(observation_minutes: int) -> tuple[str, ...]:
    """15m/30m confirm on 1H; 1h keeps both 1H and 4H (AMENDMENT-9)."""
    if observation_minutes == 60:
        return ("1H", "4H")
    return ("1H",)


def build_cells(mode: str) -> tuple[MatrixCell, ...]:
    """Expand the declared preflight or frozen full matrix deterministically.

    Full-grid order is all 15m, then all 30m, then all 1h (AMENDMENT-9).
    """
    if mode == "preflight":
        # Representative cTrader cell on the shared 30-day TRAIN probe window.
        return (
            _cell(
                "CTRADER",
                "EURUSD",
                15,
                "BREAKOUT_BAR",
                "PREVIOUS_1H",
                confirmation_reference="1H",
                start=PREFLIGHT_START,
                end=PREFLIGHT_END,
            ),
        )
    if mode != "full":
        raise ValueError("mode must be 'preflight' or 'full'")
    cells = []
    for minutes in OBSERVATION_MINUTES:
        for symbol in CTRADER_SYMBOLS:
            for method in CONFIRMATION_METHODS:
                for level_config in LEVEL_CONFIGS:
                    for reference in _confirmation_references(minutes):
                        cells.append(
                            _cell(
                                "CTRADER",
                                symbol,
                                minutes,
                                method,
                                level_config,
                                confirmation_reference=reference,
                            )
                        )
    return tuple(cells)


def cell_run_dir(repo_root: Path, mode: str, cell: MatrixCell) -> Path:
    """Return the final atomic publication path for a scheduled cell."""
    return Path(repo_root) / "data" / "nautilus_runs" / "EXP-100" / mode / cell.cell_id


def cell_gate_path(repo_root: Path, mode: str, cell: MatrixCell) -> Path:
    """Return the per-cell integrity result path."""
    return (
        Path(repo_root)
        / "python"
        / "experiments"
        / "EXP-100"
        / "results"
        / "execution"
        / mode
        / f"{cell.cell_id}.json"
    )


def resume_decision(repo_root: Path, mode: str, cell: MatrixCell) -> str:
    """Return RUN or SKIP, refusing every ambiguous on-disk state."""
    run_dir = cell_run_dir(repo_root, mode, cell)
    gate_path = cell_gate_path(repo_root, mode, cell)
    staging = (
        run_dir.parent / f".{run_dir.name}.work",
        run_dir.parent / f".{run_dir.name}.publish",
    )
    if any(path.exists() for path in staging):
        raise RuntimeError(f"stale cell staging path exists for {cell.cell_id}")
    if run_dir.exists():
        if not gate_path.exists():
            raise RuntimeError(
                f"published emission has no passing integrity gate: {cell.cell_id}"
            )
        gate = json.loads(gate_path.read_text(encoding="utf-8"))
        if gate.get("blocking_pass") is not True:
            raise RuntimeError(f"published emission has a failed integrity gate: {cell.cell_id}")
        return "SKIP"
    if gate_path.exists():
        raise RuntimeError(f"integrity gate exists without a published emission: {cell.cell_id}")
    return "RUN"


def require_free_disk(path: Path, *, min_free_bytes: int) -> int:
    """Return free bytes or refuse a launch below the configured reserve."""
    free = int(shutil.disk_usage(path).free)
    if free < min_free_bytes:
        raise RuntimeError(f"free disk {free} is below required reserve {min_free_bytes}")
    return free


def cell_command(
    repo_root: Path,
    mode: str,
    cell: MatrixCell,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    rss_limit_bytes: int = DEFAULT_RSS_LIMIT_BYTES,
) -> list[str]:
    """Build the one-cell subprocess command with all frozen safety inputs."""
    root = Path(repo_root)
    pin = execution_pin(cell.venue)
    return [
        sys.executable,
        str(root / "python" / "experiments" / "EXP-100" / "code" / "run_experiment.py"),
        "--catalog-path",
        str(root / pin.catalog_path),
        "--run-dir",
        str(cell_run_dir(root, mode, cell)),
        "--instrument-id",
        cell.instrument_id,
        "--archive-symbol",
        cell.archive_symbol,
        "--venue",
        cell.venue,
        "--observation-minutes",
        str(cell.observation_minutes),
        "--confirmation-method",
        cell.confirmation_method,
        "--confirmation-reference",
        cell.confirmation_reference,
        "--level-config",
        cell.level_config,
        "--start",
        cell.start.isoformat(),
        "--end",
        cell.end.isoformat(),
        "--chunk-size",
        str(chunk_size),
        "--rss-limit-bytes",
        str(rss_limit_bytes),
        "--destroy-control",
    ]


def gate_command(repo_root: Path, mode: str, cell: MatrixCell) -> list[str]:
    """Build the mandatory post-publication integrity-gate command."""
    root = Path(repo_root)
    return [
        sys.executable,
        "-m",
        "xen.estimand_validation",
        str(cell_run_dir(root, mode, cell)),
        "--expect",
        cell.archive_symbol,
        "--out",
        str(cell_gate_path(root, mode, cell)),
    ]


def journal_path(repo_root: Path, mode: str) -> Path:
    """Return the append-only execution journal path."""
    return (
        Path(repo_root)
        / "python"
        / "experiments"
        / "EXP-100"
        / "results"
        / "execution"
        / f"{mode}-journal.jsonl"
    )


def _append_journal(path: Path, cell: MatrixCell, status: str, **fields: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_utc": datetime.now(UTC).isoformat(),
        "cell_id": cell.cell_id,
        "status": status,
        **fields,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True, default=str) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _run_one_cell(
    *,
    root: Path,
    mode: str,
    cell: MatrixCell,
    journal: Path,
    journal_lock: threading.Lock,
    min_free_bytes: int,
    timeout_seconds: int,
    chunk_size: int,
    rss_limit_bytes: int,
) -> int:
    """Run one cell in its own subprocesses. 0 = validated; 1 = stop the matrix."""
    run_dir = cell_run_dir(root, mode, cell)
    gate_path = cell_gate_path(root, mode, cell)
    run_dir.parent.mkdir(parents=True, exist_ok=True)
    gate_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        free_bytes = require_free_disk(root, min_free_bytes=min_free_bytes)
    except RuntimeError as exc:
        with journal_lock:
            _append_journal(journal, cell, "LOW_DISK", reason=str(exc))
        return 1
    started = time.monotonic()
    with journal_lock:
        _append_journal(
            journal,
            cell,
            "STARTED",
            run_dir=str(run_dir),
            gate_path=str(gate_path),
            free_bytes=free_bytes,
        )
    try:
        result = subprocess.run(
            cell_command(
                root,
                mode,
                cell,
                chunk_size=chunk_size,
                rss_limit_bytes=rss_limit_bytes,
            ),
            cwd=root / "python",
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        with journal_lock:
            _append_journal(
                journal,
                cell,
                "TIMEOUT",
                elapsed_seconds=time.monotonic() - started,
                timeout_seconds=timeout_seconds,
            )
        return 1
    if result.returncode != 0:
        with journal_lock:
            _append_journal(
                journal,
                cell,
                "FAILED",
                elapsed_seconds=time.monotonic() - started,
                returncode=result.returncode,
                stderr=result.stderr[-4000:],
            )
        return 1
    with journal_lock:
        _append_journal(
            journal,
            cell,
            "PUBLISHED",
            elapsed_seconds=time.monotonic() - started,
            returncode=result.returncode,
        )
    try:
        gate_result = subprocess.run(
            gate_command(root, mode, cell),
            cwd=root / "python",
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        with journal_lock:
            _append_journal(journal, cell, "INVALID", reason="integrity gate timed out")
        return 1
    gate = (
        json.loads(gate_path.read_text(encoding="utf-8"))
        if gate_path.exists()
        else {}
    )
    if gate_result.returncode != 0 or gate.get("blocking_pass") is not True:
        with journal_lock:
            _append_journal(
                journal,
                cell,
                "INVALID",
                returncode=gate_result.returncode,
                stderr=gate_result.stderr[-4000:],
            )
        return 1
    with journal_lock:
        _append_journal(
            journal,
            cell,
            "VALIDATED",
            elapsed_seconds=time.monotonic() - started,
            peak_rss_bytes=_peak_rss_bytes(run_dir),
            artifact_bytes=_tree_bytes(run_dir),
        )
    return 0


def run_matrix(
    *,
    repo_root: Path,
    mode: str,
    min_free_bytes: int = DEFAULT_MIN_FREE_BYTES,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    rss_limit_bytes: int = DEFAULT_RSS_LIMIT_BYTES,
    workers: int = DEFAULT_WORKERS,
) -> int:
    """Run cells, stopping at the first unsafe or invalid state.

    ``workers=1`` is the original serial loop. ``workers>1`` runs that many
    one-cell subprocesses at once. Each cell still owns one BacktestNode.
    """
    if workers < 1:
        raise ValueError("workers must be >= 1")
    root = Path(repo_root)
    journal = journal_path(root, mode)
    journal_lock = threading.Lock()
    pending: list[MatrixCell] = []
    for cell in build_cells(mode):
        decision = resume_decision(root, mode, cell)
        if decision == "SKIP":
            _append_journal(journal, cell, "SKIPPED")
            continue
        pending.append(cell)
    if workers == 1:
        for cell in pending:
            if _run_one_cell(
                root=root,
                mode=mode,
                cell=cell,
                journal=journal,
                journal_lock=journal_lock,
                min_free_bytes=min_free_bytes,
                timeout_seconds=timeout_seconds,
                chunk_size=chunk_size,
                rss_limit_bytes=rss_limit_bytes,
            ):
                return 1
        return 0
    stop = False
    with ThreadPoolExecutor(max_workers=workers) as pool:
        inflight = {}
        cells = iter(pending)
        for _ in range(min(workers, len(pending))):
            cell = next(cells)
            inflight[pool.submit(
                _run_one_cell,
                root=root,
                mode=mode,
                cell=cell,
                journal=journal,
                journal_lock=journal_lock,
                min_free_bytes=min_free_bytes,
                timeout_seconds=timeout_seconds,
                chunk_size=chunk_size,
                rss_limit_bytes=rss_limit_bytes,
            )] = cell
        while inflight:
            done, _ = wait(inflight, return_when=FIRST_COMPLETED)
            for future in done:
                inflight.pop(future)
                if future.result() != 0:
                    stop = True
            if stop:
                for future in inflight:
                    future.cancel()
                return 1
            for _ in range(workers - len(inflight)):
                try:
                    cell = next(cells)
                except StopIteration:
                    break
                inflight[pool.submit(
                    _run_one_cell,
                    root=root,
                    mode=mode,
                    cell=cell,
                    journal=journal,
                    journal_lock=journal_lock,
                    min_free_bytes=min_free_bytes,
                    timeout_seconds=timeout_seconds,
                    chunk_size=chunk_size,
                    rss_limit_bytes=rss_limit_bytes,
                )] = cell
    return 0


def _peak_rss_bytes(run_dir: Path) -> int | None:
    metadata_path = run_dir / "run_metadata.json"
    if not metadata_path.exists():
        return None
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    return metadata.get("memory", {}).get("peak_rss_bytes")


def _tree_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("preflight", "full"), required=True)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--min-free-bytes", type=int, default=DEFAULT_MIN_FREE_BYTES)
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--rss-limit-bytes", type=int, default=DEFAULT_RSS_LIMIT_BYTES)
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help="one-cell subprocesses to run at once (default 1 = serial)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    return run_matrix(
        repo_root=args.repo_root,
        mode=args.mode,
        min_free_bytes=args.min_free_bytes,
        timeout_seconds=args.timeout_seconds,
        chunk_size=args.chunk_size,
        rss_limit_bytes=args.rss_limit_bytes,
        workers=args.workers,
    )


if __name__ == "__main__":
    raise SystemExit(main())
