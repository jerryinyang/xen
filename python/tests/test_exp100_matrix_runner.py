"""Execution-apparatus tests for the EXP-100 frozen matrix."""

from datetime import UTC, datetime
import json
from pathlib import Path
import subprocess
import sys


CODE_DIR = Path(__file__).resolve().parents[1] / "experiments" / "EXP-100" / "code"
sys.path.insert(0, str(CODE_DIR))

import run_matrix  # noqa: E402


def test_matrix_runner_module_exists() -> None:
    assert (CODE_DIR / "run_matrix.py").is_file()


def test_full_grid_is_ctrader_only_264_unique_cells() -> None:
    cells = run_matrix.build_cells("full")

    # 11 configs: 15m/30m 3×2×2×11×1 = 132; 1h 3×1×2×11×2 = 132; total 264
    assert len(cells) == 264
    assert len({cell.cell_id for cell in cells}) == 264
    assert all(cell.venue == "CTRADER" for cell in cells)
    assert sum(cell.venue == "BYBIT" for cell in cells) == 0
    assert [cell.observation_minutes for cell in cells] == (
        [15] * 66 + [30] * 66 + [60] * 132
    )
    assert all(
        cell.confirmation_reference == "1H"
        for cell in cells
        if cell.observation_minutes in {15, 30}
    )
    hour_refs = {
        cell.confirmation_reference
        for cell in cells
        if cell.observation_minutes == 60
    }
    assert hour_refs == {"1H", "4H"}


def test_preflight_is_exactly_declared_ctrader_cell() -> None:
    (cell,) = run_matrix.build_cells("preflight")

    assert cell.venue == "CTRADER"
    assert cell.archive_symbol == "EURUSD"
    assert cell.instrument_id == "EURUSD.CTrader"
    assert cell.observation_minutes == 15
    assert cell.confirmation_method == "BREAKOUT_BAR"
    assert cell.confirmation_reference == "1H"
    assert cell.level_config == "PREVIOUS_1H"
    assert cell.start == datetime(2023, 10, 23, tzinfo=UTC)
    assert cell.end == datetime(2023, 11, 21, 23, 59, tzinfo=UTC)


def test_cell_ids_are_stable_and_filesystem_safe() -> None:
    first = run_matrix.build_cells("full")
    second = run_matrix.build_cells("full")

    assert [cell.cell_id for cell in first] == [cell.cell_id for cell in second]
    assert all(cell.cell_id == cell.cell_id.lower() for cell in first)
    assert all("/" not in cell.cell_id and " " not in cell.cell_id for cell in first)


def test_resume_skips_only_passing_validated_cell(tmp_path: Path) -> None:
    (cell,) = run_matrix.build_cells("preflight")
    run_dir = run_matrix.cell_run_dir(tmp_path, "preflight", cell)
    gate_path = run_matrix.cell_gate_path(tmp_path, "preflight", cell)
    run_dir.mkdir(parents=True)
    gate_path.parent.mkdir(parents=True)
    gate_path.write_text(json.dumps({"blocking_pass": True}), encoding="utf-8")

    assert run_matrix.resume_decision(tmp_path, "preflight", cell) == "SKIP"


def test_resume_refuses_incomplete_or_unvalidated_state(tmp_path: Path) -> None:
    (cell,) = run_matrix.build_cells("preflight")
    run_dir = run_matrix.cell_run_dir(tmp_path, "preflight", cell)
    work_dir = run_dir.parent / f".{run_dir.name}.work"
    work_dir.mkdir(parents=True)

    try:
        run_matrix.resume_decision(tmp_path, "preflight", cell)
    except RuntimeError as exc:
        assert "staging" in str(exc)
    else:
        raise AssertionError("stale staging path was accepted")

    work_dir.rmdir()
    run_dir.mkdir()
    try:
        run_matrix.resume_decision(tmp_path, "preflight", cell)
    except RuntimeError as exc:
        assert "passing integrity gate" in str(exc)
    else:
        raise AssertionError("unvalidated emission was accepted")


def test_resume_refuses_orphan_or_failed_gate(tmp_path: Path) -> None:
    (cell,) = run_matrix.build_cells("preflight")
    gate_path = run_matrix.cell_gate_path(tmp_path, "preflight", cell)
    gate_path.parent.mkdir(parents=True)
    gate_path.write_text(json.dumps({"blocking_pass": False}), encoding="utf-8")

    try:
        run_matrix.resume_decision(tmp_path, "preflight", cell)
    except RuntimeError as exc:
        assert "without a published emission" in str(exc)
    else:
        raise AssertionError("orphan gate was accepted")


def test_disk_guard_refuses_below_required_free_bytes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        run_matrix.shutil,
        "disk_usage",
        lambda _path: run_matrix.shutil._ntuple_diskusage(100, 95, 5),
    )

    try:
        run_matrix.require_free_disk(tmp_path, min_free_bytes=10)
    except RuntimeError as exc:
        assert "free disk" in str(exc)
    else:
        raise AssertionError("low disk was accepted")


def test_cell_and_gate_commands_pin_safety_inputs(tmp_path: Path) -> None:
    (cell,) = run_matrix.build_cells("preflight")

    command = run_matrix.cell_command(tmp_path, "preflight", cell)
    gate = run_matrix.gate_command(tmp_path, "preflight", cell)

    assert command[0] == sys.executable
    assert "--destroy-control" in command
    assert command[command.index("--catalog-path") + 1] == str(
        tmp_path / "data" / "catalog_ctrader"
    )
    assert command[command.index("--start") + 1] == cell.start.isoformat()
    assert command[command.index("--end") + 1] == cell.end.isoformat()
    assert command[command.index("--venue") + 1] == "CTRADER"
    assert gate[:3] == [sys.executable, "-m", "xen.estimand_validation"]
    assert gate[gate.index("--expect") + 1] == "EURUSD"
    assert gate[gate.index("--out") + 1] == str(
        run_matrix.cell_gate_path(tmp_path, "preflight", cell)
    )


def test_run_matrix_journals_validated_cell(tmp_path: Path, monkeypatch) -> None:
    def fake_run(command, **_kwargs):
        if command[1:3] == ["-m", "xen.estimand_validation"]:
            gate_path = Path(command[command.index("--out") + 1])
            gate_path.write_text(json.dumps({"blocking_pass": True}), encoding="utf-8")
        else:
            Path(command[command.index("--run-dir") + 1]).mkdir(parents=True)
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    monkeypatch.setattr(run_matrix.subprocess, "run", fake_run)

    result = run_matrix.run_matrix(
        repo_root=tmp_path,
        mode="preflight",
        min_free_bytes=0,
        timeout_seconds=60,
    )

    assert result == 0
    entries = [
        json.loads(line)
        for line in run_matrix.journal_path(tmp_path, "preflight")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert [entry["status"] for entry in entries] == [
        "STARTED",
        "PUBLISHED",
        "VALIDATED",
    ]
    assert entries[-1]["cell_id"] == run_matrix.build_cells("preflight")[0].cell_id


def test_run_matrix_stops_on_child_failure(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        run_matrix.subprocess,
        "run",
        lambda command, **_kwargs: subprocess.CompletedProcess(
            command, 2, stdout="", stderr="child failed"
        ),
    )

    result = run_matrix.run_matrix(
        repo_root=tmp_path,
        mode="preflight",
        min_free_bytes=0,
        timeout_seconds=60,
    )

    assert result == 1
    last = json.loads(
        run_matrix.journal_path(tmp_path, "preflight")
        .read_text(encoding="utf-8")
        .splitlines()[-1]
    )
    assert last["status"] == "FAILED"
    assert last["returncode"] == 2


def test_run_matrix_stops_on_timeout(tmp_path: Path, monkeypatch) -> None:
    def time_out(command, **_kwargs):
        raise subprocess.TimeoutExpired(command, timeout=1)

    monkeypatch.setattr(run_matrix.subprocess, "run", time_out)

    result = run_matrix.run_matrix(
        repo_root=tmp_path,
        mode="preflight",
        min_free_bytes=0,
        timeout_seconds=1,
    )

    assert result == 1
    last = json.loads(
        run_matrix.journal_path(tmp_path, "preflight")
        .read_text(encoding="utf-8")
        .splitlines()[-1]
    )
    assert last["status"] == "TIMEOUT"


def test_run_matrix_journals_low_disk_and_stops(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        run_matrix,
        "require_free_disk",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("free disk too low")),
    )

    result = run_matrix.run_matrix(
        repo_root=tmp_path,
        mode="preflight",
        min_free_bytes=10,
        timeout_seconds=1,
    )

    assert result == 1
    last = json.loads(
        run_matrix.journal_path(tmp_path, "preflight")
        .read_text(encoding="utf-8")
        .splitlines()[-1]
    )
    assert last["status"] == "LOW_DISK"


def test_run_matrix_workers_keep_one_subprocess_per_cell(tmp_path: Path, monkeypatch) -> None:
    seen: list[str] = []
    inflight = 0
    max_inflight = 0
    lock = run_matrix.threading.Lock()

    def fake_run(command, **_kwargs):
        nonlocal inflight, max_inflight
        with lock:
            inflight += 1
            max_inflight = max(max_inflight, inflight)
        try:
            if command[1:3] == ["-m", "xen.estimand_validation"]:
                gate_path = Path(command[command.index("--out") + 1])
                gate_path.write_text(json.dumps({"blocking_pass": True}), encoding="utf-8")
            else:
                Path(command[command.index("--run-dir") + 1]).mkdir(parents=True)
                seen.append(command[command.index("--instrument-id") + 1])
            run_matrix.time.sleep(0.05)
            return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")
        finally:
            with lock:
                inflight -= 1

    monkeypatch.setattr(run_matrix.subprocess, "run", fake_run)
    sample = run_matrix.build_cells("full")[:4]
    monkeypatch.setattr(run_matrix, "build_cells", lambda _mode: sample)

    result = run_matrix.run_matrix(
        repo_root=tmp_path,
        mode="full",
        min_free_bytes=0,
        timeout_seconds=60,
        workers=2,
    )

    assert result == 0
    assert max_inflight <= 4
    assert max_inflight >= 2
    assert len(seen) == 4
    entries = [
        json.loads(line)
        for line in run_matrix.journal_path(tmp_path, "full")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert sum(entry["status"] == "VALIDATED" for entry in entries) == 4
