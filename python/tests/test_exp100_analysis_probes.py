from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import polars as pl
import pytest


REPO = Path(__file__).resolve().parents[2]
ANALYSIS_CODE = REPO / "python/experiments/EXP-100/analysis_code"


def _load(name: str) -> ModuleType:
    path = ANALYSIS_CODE / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"exp100_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_golden_probe_uses_one_raid_per_declared_trace() -> None:
    report = _load("probe_integrity").run_golden()

    assert all(report["checks"].values())
    assert report["t1_after_excursion"]["raid_id"] == "T1-HIGH:raid:1"
    assert report["t1_after_excursion"]["return_ts_ns"] is None
    assert report["t1_after_return"]["return_ts_ns"] is not None
    assert [row["status"] for row in report["settled_raids"]] == [
        "CONFIRMED_NON_PRIMARY",
        "COMPLETED",
    ]


@pytest.mark.xfail(
    strict=True,
    reason="ATR-undefined raids retain the first source extreme, not the observation extreme",
)
def test_atr_undefined_initial_observation_tracks_full_extreme() -> None:
    report = _load("probe_integrity").probe_atr_undefined_initial_observation_extreme()

    assert report["implementation_matches_completed_observation_extreme"]


def test_same_bar_golden_does_not_mix_in_a_repierce() -> None:
    report = _load("probe_integrity").run_same_bar_return_golden()

    assert all(
        value
        for name, value in report["checks"].items()
        if name not in {"status", "max_excursion"}
    )
    assert report["checks"]["status"] == "COMPLETED"
    assert report["raid"]["raid_id"] == "SB-HIGH:raid:1"
    assert report["raid"]["return_ts_ns"] == report["raid"]["sweep_ts_ns"]


def test_coverage_marginals_retain_every_declared_layer_value() -> None:
    module = _load("summarize_coverage")
    rows = []
    for i, (venue, symbol, timeframe, method, ref, config) in enumerate(
        [
            ("ctrader", "EURUSD", "15m", "breakout_bar", "1h", "PREVIOUS_1H"),
            ("ctrader", "XAUUSD", "60m", "level_close", "4h", "ROLLING_7"),
        ],
        start=1,
    ):
        row = {
            "venue": venue,
            "symbol": symbol,
            "timeframe": timeframe,
            "method": method,
            "confirm_ref": ref,
            "level_config": config,
        }
        row.update({source: i for source, _ in module.MARGINAL_SUMS})
        rows.append(row)

    result = module.coverage_marginals(pl.DataFrame(rows))

    assert set(result["layer"]) == {layer for layer, _ in module.MARGINAL_LAYERS}
    assert set(
        result.filter(pl.col("layer") == "instrument")["value"]
    ) == {"EURUSD", "XAUUSD"}
    venue = result.filter(pl.col("layer") == "venue").row(0, named=True)
    assert venue["cells"] == 2
    assert venue["raids"] == 3
    assert venue["pre_mfe_defined"] == 3
