"""Cross-experiment result-contract checks; mechanics live in liqswp_analysis tests."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from xen.liqswp_analysis.contract import ZERO_COST_DISCLOSURE

ROOT = Path(__file__).parents[1]


def load(exp: str):
    path = ROOT / "experiments" / exp / "analysis_code" / "analysis.py"
    spec = importlib.util.spec_from_file_location(f"{exp}_contract", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("exp", ["EXP-101", "EXP-102", "EXP-103", "EXP-104"])
def test_fixture_uses_production_contract_and_is_deterministic(tmp_path: Path, exp: str) -> None:
    module = load(exp)
    first_path = tmp_path / f"{exp}-first.json"
    second_path = tmp_path / f"{exp}-second.json"
    first = module.run_fixture(n_destroy=8, seeds=(0, 1), n_boot=20, output=first_path)
    second = module.run_fixture(n_destroy=8, seeds=(0, 1), n_boot=20, output=second_path)
    assert first == second
    assert json.loads(first_path.read_text()) == first
    assert first["integrity"]["blocking_pass"]
    assert first["value_rows"]
    assert first["zero_cost_disclosure"] == ZERO_COST_DISCLOSURE
    assert all(set(row["sensitivities"]) == {"2", "5", "10"} for row in first["value_rows"])
    assert not any(
        key in {"SUPPORTED", "WASH", "CONTRADICTED"} for row in first["value_rows"] for key in row
    )
