from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).parents[1]


def _load_exp101():
    path = ROOT / "experiments/EXP-101/analysis_code/analysis.py"
    spec = importlib.util.spec_from_file_location("exp101_analysis_live", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_fixture_defaults_to_registered_ten_outer_bootstrap_replicates(
    monkeypatch, tmp_path: Path
) -> None:
    module = _load_exp101()
    observed: dict[str, object] = {}

    def capture(adapter, output: Path):
        observed.update(n_boot=adapter.n_boot, n_destroy=adapter.n_destroy, seeds=adapter.seeds)
        return {"output": str(output)}

    monkeypatch.setattr(module, "_run_fixture", capture)
    output = tmp_path / "fixture.json"
    module.run_fixture(output=output)

    assert observed == {
        "n_boot": 10,
        "n_destroy": 2_000,
        "seeds": (0, 1, 2, 3, 4),
    }


def test_live_defaults_to_frozen_exp100_family_gate(
    monkeypatch, tmp_path: Path
) -> None:
    module = _load_exp101()
    observed: dict[str, Path] = {}

    def capture(adapter, source: Path, gate: Path, output: Path):
        observed.update(source=source, gate=gate, output=output)
        return {}

    monkeypatch.setattr(module, "run_live", capture)
    output = tmp_path / "analysis.json"
    module.main(["--live", "--output", str(output)])

    project_root = Path(module.__file__).resolve().parents[4]
    assert observed["source"] == project_root / "data/nautilus_runs/EXP-100/full"
    assert observed["gate"] == (
        project_root / "python/experiments/EXP-100/results/estimand_validation.json"
    )
    assert observed["output"] == output


def test_future_destroy_uses_all_eleven_configurations_as_donors(
) -> None:
    module = _load_exp101()
    adapter = module.Adapter(n_boot=2, n_destroy=1, seeds=(0,))
    frame = adapter.fixture_frame()

    adapter.integrity(frame)
    first_control = adapter.extra(frame)["control"]["records"][0]

    assert first_control["group_sizes"] == [3_200]
    assert first_control["moved_rows"] == 3_200


def test_fixture_cli_uses_the_registered_bounded_fixture_runner(
    monkeypatch, tmp_path: Path
) -> None:
    module = _load_exp101()
    observed: dict[str, object] = {}

    def capture(*, output: Path):
        observed["output"] = output
        return {}

    monkeypatch.setattr(module, "run_fixture", capture)
    output = tmp_path / "fixture.json"
    module.main(["--fixture", "--output", str(output)])

    assert observed == {"output": output}
