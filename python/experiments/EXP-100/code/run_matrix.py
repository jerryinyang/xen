"""Run the frozen EXP-100 matrix through one fresh subprocess per cell."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from run_experiment import execution_pin

BYBIT_SYMBOLS = (
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "AVAXUSDT",
    "ORDIUSDT",
    "1000BONKUSDT",
    "TIAUSDT",
    "DOGEUSDT",
    "XRPUSDT",
    "LINKUSDT",
)
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
    "ROLLING_16",
    "ROLLING_32",
    "ROLLING_64",
    "ROLLING_128",
    "ROLLING_256",
)
PREFLIGHT_START = datetime(2023, 11, 18, tzinfo=UTC)
PREFLIGHT_END = datetime(2023, 12, 17, 23, 59, tzinfo=UTC)
DEFAULT_CHUNK_SIZE = 50_000
DEFAULT_RSS_LIMIT_BYTES = 1_610_612_736
DEFAULT_MIN_FREE_BYTES = 20 * 1024**3
DEFAULT_TIMEOUT_SECONDS = 2 * 60 * 60
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
    start: datetime | None = None,
    end: datetime | None = None,
) -> MatrixCell:
    pin = execution_pin(venue)
    suffix = "-LINEAR.BYBIT" if venue == "BYBIT" else ".CTrader"
    return MatrixCell(
        venue=venue,
        archive_symbol=symbol,
        instrument_id=f"{symbol}{suffix}",
        observation_minutes=observation_minutes,
        confirmation_method=confirmation_method,
        confirmation_reference="1D" if observation_minutes == 60 else "1H",
        level_config=level_config,
        start=start or pin.train_start,
        end=end or pin.train_end,
    )


def build_cells(mode: str) -> tuple[MatrixCell, ...]:
    """Expand the declared preflight or frozen full matrix deterministically."""
    if mode == "preflight":
        return (
            _cell(
                "BYBIT",
                "BTCUSDT",
                15,
                "BREAKOUT_BAR",
                "PREVIOUS_1H",
                start=PREFLIGHT_START,
                end=PREFLIGHT_END,
            ),
        )
    if mode != "full":
        raise ValueError("mode must be 'preflight' or 'full'")
    cells = []
    for venue, symbols in (("BYBIT", BYBIT_SYMBOLS), ("CTRADER", CTRADER_SYMBOLS)):
        for symbol in symbols:
            for minutes in OBSERVATION_MINUTES:
                for method in CONFIRMATION_METHODS:
                    for level_config in LEVEL_CONFIGS:
                        cells.append(_cell(venue, symbol, minutes, method, level_config))
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


def run_matrix(
    *,
    repo_root: Path,
    mode: str,
    min_free_bytes: int = DEFAULT_MIN_FREE_BYTES,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    rss_limit_bytes: int = DEFAULT_RSS_LIMIT_BYTES,
) -> int:
    """Run cells serially, stopping at the first unsafe or invalid state."""
    root = Path(repo_root)
    journal = journal_path(root, mode)
    for cell in build_cells(mode):
        decision = resume_decision(root, mode, cell)
        if decision == "SKIP":
            _append_journal(journal, cell, "SKIPPED")
            continue
        run_dir = cell_run_dir(root, mode, cell)
        gate_path = cell_gate_path(root, mode, cell)
        run_dir.parent.mkdir(parents=True, exist_ok=True)
        gate_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            free_bytes = require_free_disk(root, min_free_bytes=min_free_bytes)
        except RuntimeError as exc:
            _append_journal(journal, cell, "LOW_DISK", reason=str(exc))
            return 1
        started = time.monotonic()
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
            _append_journal(
                journal,
                cell,
                "TIMEOUT",
                elapsed_seconds=time.monotonic() - started,
                timeout_seconds=timeout_seconds,
            )
            return 1
        if result.returncode != 0:
            _append_journal(
                journal,
                cell,
                "FAILED",
                elapsed_seconds=time.monotonic() - started,
                returncode=result.returncode,
                stderr=result.stderr[-4000:],
            )
            return 1
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
            _append_journal(journal, cell, "INVALID", reason="integrity gate timed out")
            return 1
        gate = (
            json.loads(gate_path.read_text(encoding="utf-8"))
            if gate_path.exists()
            else {}
        )
        if gate_result.returncode != 0 or gate.get("blocking_pass") is not True:
            _append_journal(
                journal,
                cell,
                "INVALID",
                returncode=gate_result.returncode,
                stderr=gate_result.stderr[-4000:],
            )
            return 1
        _append_journal(
            journal,
            cell,
            "VALIDATED",
            elapsed_seconds=time.monotonic() - started,
            peak_rss_bytes=_peak_rss_bytes(run_dir),
            artifact_bytes=_tree_bytes(run_dir),
        )
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
    )


if __name__ == "__main__":
    raise SystemExit(main())
