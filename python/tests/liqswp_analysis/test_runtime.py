from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import polars as pl
import pytest

from xen.liqswp_analysis.contract import IntegrityStatus
from xen.liqswp_analysis.runtime import run_fixture, run_live


class FakeAdapter:
    experiment = "EXP-FAKE"

    def __init__(self, *, valid: bool = True, explode: bool = False) -> None:
        self.valid = valid
        self.explode = explode
        self.calls: list[str] = []

    def fixture_frame(self) -> pl.DataFrame:
        self.calls.append("fixture_frame")
        return pl.DataFrame({"value": [1.0, 2.0]})

    def live_frame(
        self, source_root: Path, gate_path: Path
    ) -> tuple[pl.DataFrame, dict[str, Any], IntegrityStatus]:
        self.calls.append("live_frame")
        return (
            pl.DataFrame({"value": [1.0, 2.0]}),
            {"mode": "live", "root": str(source_root), "gate": str(gate_path)},
            IntegrityStatus(True),
        )

    def integrity(self, frame: pl.DataFrame) -> IntegrityStatus:
        self.calls.append("integrity")
        if self.explode:
            raise RuntimeError("synthetic failure")
        return IntegrityStatus(self.valid, () if self.valid else ("VOID_SYNTHETIC",))

    def population(self, frame: pl.DataFrame) -> dict[str, Any]:
        self.calls.append("population")
        return {"rows": frame.height}

    def analyze(self, frame: pl.DataFrame) -> tuple[dict[str, Any], ...]:
        self.calls.append("analyze")
        return ({"observed": float(frame["value"].mean())},)

    def extra(self, frame: pl.DataFrame) -> dict[str, Any]:
        self.calls.append("extra")
        return {"columns": frame.columns}


def test_fixture_runs_integrity_before_value_and_writes_complete_artifact(tmp_path: Path) -> None:
    adapter = FakeAdapter()
    output = tmp_path / "fixture.json"
    payload = run_fixture(adapter, output)
    assert adapter.calls.index("integrity") < adapter.calls.index("analyze")
    assert json.loads(output.read_text()) == payload
    assert payload["experiment"] == "EXP-FAKE"
    assert payload["source"] == {"mode": "fixture"}
    assert payload["value_rows"] == [{"observed": 1.5}]
    assert payload["zero_cost_disclosure"]["prohibited_claims"].endswith("deployable")


def test_failed_integrity_never_calls_analysis_or_emits_value_rows(tmp_path: Path) -> None:
    adapter = FakeAdapter(valid=False)
    payload = run_fixture(adapter, tmp_path / "void.json")
    assert "analyze" not in adapter.calls
    assert payload["integrity"]["reasons"] == ["VOID_SYNTHETIC"]
    assert payload["value_rows"] == []


def test_live_uses_supplied_source_and_writes_result(tmp_path: Path) -> None:
    adapter = FakeAdapter()
    source = tmp_path / "source"
    gate = tmp_path / "gate.json"
    payload = run_live(adapter, source, gate, tmp_path / "live.json")
    assert payload["source"] == {"mode": "live", "root": str(source), "gate": str(gate)}
    assert "analyze" in adapter.calls


def test_exception_leaves_no_partial_final_artifact(tmp_path: Path) -> None:
    output = tmp_path / "failed.json"
    with pytest.raises(RuntimeError, match="synthetic failure"):
        run_fixture(FakeAdapter(explode=True), output)
    assert not output.exists()
    assert not list(tmp_path.glob(".failed.json.*.tmp"))
