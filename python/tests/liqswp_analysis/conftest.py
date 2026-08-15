from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


ROOT = Path(__file__).parents[2]


@pytest.fixture
def load_exp_module():
    def load(exp: str) -> ModuleType:
        path = ROOT / "experiments" / exp / "analysis_code" / "analysis.py"
        spec = importlib.util.spec_from_file_location(f"{exp}_adapter", path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    return load
