from __future__ import annotations

import importlib.util
from pathlib import Path

import polars as pl


ROOT = Path(__file__).parents[1]


def _load_exp102():
    path = ROOT / "experiments/EXP-102/analysis_code/analysis.py"
    spec = importlib.util.spec_from_file_location("exp102_live", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _small_adapter(module):
    # Integrity-passing tests use the registered 2,000 destroy draws: the live
    # destroyed mean carries draw noise ~ sigma_d/sqrt(n_destroy), so small
    # test-only destroy counts can push the fixed draw mean past the bite.
    return module.Adapter(n_boot=8, n_destroy=2000, seeds=(0, 1))


def test_destroy_population_includes_every_count_band() -> None:
    module = _load_exp102()
    adapter = _small_adapter(module)
    base = adapter.fixture_frame()
    count_two = base.filter(pl.col("count_band") == "1").with_columns(
        pl.lit("2+").alias("count_band"),
        pl.lit(2).alias("prior_raid_count"),
        (pl.lit("TWO-") + pl.col("raid_id")).alias("raid_id"),
        (pl.lit("TWO-") + pl.col("level_id")).alias("level_id"),
    )
    frame = pl.concat((base, count_two), how="vertical_relaxed")

    status = adapter.integrity(frame)

    assert status.blocking_pass
    records = adapter.extra(frame)["control"]["records"]
    one_vs_zero = next(
        row for row in records if row["arm"] == "1" and row["channel"] == "swing_atr"
    )
    assert one_vs_zero["moved_rows"] == frame.height
    assert one_vs_zero["group_sizes"] == [frame.height]


def test_fixture_matches_the_registered_exp102_plants() -> None:
    module = _load_exp102()
    frame = _small_adapter(module).fixture_frame()

    assert frame.height == 400
    assert frame.group_by("count_band").len().sort("count_band").to_dicts() == [
        {"count_band": "0", "len": 200},
        {"count_band": "1", "len": 200},
    ]
    by_band = (
        frame.group_by("count_band")
        .agg(
            pl.col("swing_atr").mean().alias("atr"),
            pl.col("swing_duration_ns").mean().alias("duration"),
            pl.col("strong_move").mean().alias("strong"),
        )
        .sort("count_band")
    )
    rows = by_band.to_dicts()
    assert rows[1]["atr"] - rows[0]["atr"] == 0.5
    assert rows[1]["duration"] - rows[0]["duration"] == 3_600_000_000_000
    assert rows[1]["strong"] - rows[0]["strong"] == 0.25


def test_analysis_is_invariant_to_source_row_order() -> None:
    module = _load_exp102()
    frame = _small_adapter(module).fixture_frame()
    shuffled = frame.sample(fraction=1.0, shuffle=True, seed=99)

    ordered_rows = tuple(row for row in _small_adapter(module).analyze(frame) if row["arm"] == "1")
    shuffled_rows = tuple(
        row for row in _small_adapter(module).analyze(shuffled) if row["arm"] == "1"
    )

    assert shuffled_rows == ordered_rows


def test_one_invalid_control_blocks_the_complete_result() -> None:
    module = _load_exp102()
    adapter = _small_adapter(module)
    # A destroy that cannot change any eligible value (every row identical) is
    # vacuous and must block the complete result (AMENDMENT-16 keeps singleton
    # groups non-blocking, so vacuity is the fail-closed channel).
    frame = adapter.fixture_frame().with_columns(pl.lit(1.0).alias("swing_atr"))

    status = adapter.integrity(frame)

    assert not status.blocking_pass
    assert "VOID_NO_CHANGED_VALUE" in status.reasons


def test_duplicate_raid_id_is_cell_scoped_not_global() -> None:
    module = _load_exp102()
    adapter = _small_adapter(module)
    frame = adapter.fixture_frame()
    other_method = frame.with_columns(pl.lit("LEVEL_CLOSE").alias("confirmation_method"))
    across_cells = pl.concat((frame, other_method))
    within_cell = pl.concat((frame, frame))

    across = adapter.extra_integrity(across_cells)
    within = adapter.extra_integrity(within_cell)

    assert "VOID_DUPLICATE_RAID_ID" not in across.reasons
    assert "VOID_DUPLICATE_RAID_ID" in within.reasons


def test_malformed_prior_count_and_out_of_fence_rows_fail_integrity() -> None:
    module = _load_exp102()
    adapter = _small_adapter(module)
    frame = (
        adapter.fixture_frame()
        .drop("fixture")
        .with_row_index("row_number")
        .with_columns(
            pl.when(pl.col("row_number") == 0)
            .then(pl.lit(-1))
            .otherwise(pl.col("prior_raid_count"))
            .alias("prior_raid_count"),
            pl.when(pl.col("row_number") == 1)
            .then(pl.lit(module.TRAIN_START_NS - 1))
            .otherwise(pl.col("sweep_ts_ns"))
            .alias("sweep_ts_ns"),
        )
        .drop("row_number")
    )

    status = adapter.extra_integrity(frame)

    assert not status.blocking_pass
    assert set(status.reasons) >= {"VOID_PRIOR_RAID_COUNT", "VOID_BEFORE_TRAIN"}


def test_live_defaults_to_authoritative_gate_and_runs_fixture_first(
    tmp_path: Path, monkeypatch
) -> None:
    module = _load_exp102()
    calls: list[tuple[str, object]] = []

    def fixture(adapter, output):
        calls.append(("fixture", (adapter.n_boot, adapter.n_destroy, adapter.seeds, output)))
        return {"integrity": {"blocking_pass": True}}

    def live(adapter, source, gate, output):
        calls.append(
            ("live", (adapter.n_boot, adapter.n_destroy, adapter.seeds, source, gate, output))
        )
        return {"integrity": {"blocking_pass": True}}

    monkeypatch.setattr(module, "_run_fixture", fixture)
    monkeypatch.setattr(module, "run_live", live)
    output = tmp_path / "live.json"

    assert module.main(["--live", "--output", str(output)]) == 0

    assert [name for name, _ in calls] == ["fixture", "live"]
    _, live_call = calls[1]
    assert live_call[0:3] == (
        module.DEFAULT_N_BOOT,
        module.DEFAULT_DESTROYS,
        module.SEEDS,
    )
    assert live_call[4] == module.AUTHORITATIVE_GATE
