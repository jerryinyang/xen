"""Live-contract regression tests for the registered EXP-104 analysis."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


PYTHON_ROOT = Path(__file__).parents[1]
PROJECT_ROOT = PYTHON_ROOT.parent


def _load_exp104() -> ModuleType:
    path = PYTHON_ROOT / "experiments/EXP-104/analysis_code/analysis.py"
    spec = importlib.util.spec_from_file_location("exp104_live_contract", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_retained_train_source_passes_gate_before_live_rows_are_read() -> None:
    """The accepted EXP-100 TRAIN source must satisfy EXP-104's source contract,
    including the §1 seal fields (contract version, Nautilus pin, single node,
    manifest binding, TRAIN start fence) now enforced fail-closed."""
    module = _load_exp104()
    adapter = module.Adapter(n_boot=2, n_destroy=2, seeds=(0,))
    source = PROJECT_ROOT / "data/nautilus_runs/EXP-100/full"
    gate = PYTHON_ROOT / "experiments/EXP-104/results/estimand_validation.json"

    attestation = module.validate_source_contract(adapter.source_spec(source, gate))

    assert attestation.integrity.blocking_pass, attestation.integrity.reasons
    assert len(attestation.paths) == 264


def test_fixture_integrity_passes_with_frequency_and_regime_disclosure() -> None:
    """The committed fixture receipt stays green with the new disclosure fields."""
    module = _load_exp104()
    adapter = module.Adapter(n_boot=10, n_destroy=20, seeds=(0, 1))

    status = adapter.integrity(adapter.fixture_frame())

    assert status.blocking_pass, status.reasons