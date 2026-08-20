"""Live-contract regression tests for the registered EXP-103 analysis."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import polars as pl
import pytest


PYTHON_ROOT = Path(__file__).parents[1]
PROJECT_ROOT = PYTHON_ROOT.parent


def _load_exp103() -> ModuleType:
    path = PYTHON_ROOT / "experiments/EXP-103/analysis_code/analysis.py"
    spec = importlib.util.spec_from_file_location("exp103_live_contract", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_retained_train_source_passes_gate_before_live_rows_are_read() -> None:
    """The accepted EXP-100 TRAIN source must satisfy EXP-103's source contract."""
    module = _load_exp103()
    adapter = module.Adapter(n_boot=2, n_destroy=2, seeds=(0,))
    source = PROJECT_ROOT / "data/nautilus_runs/EXP-100/full"
    gate = PYTHON_ROOT / "experiments/EXP-103/results/estimand_validation.json"

    attestation = module.validate_source_contract(adapter.source_spec(source, gate))

    assert attestation.integrity.blocking_pass, attestation.integrity.reasons
    assert len(attestation.paths) == 264


def test_one_invalid_control_channel_blocks_the_complete_analysis() -> None:
    """A surviving/vacuous hard control cannot be hidden when companion channels pass."""
    module = _load_exp103()
    adapter = module.Adapter(n_boot=20, n_destroy=20, seeds=(0, 1))
    frame = adapter.fixture_frame().with_columns(pl.lit(1.0).alias("swing_atr"))

    status = adapter.integrity(frame)

    assert not status.blocking_pass
    assert "VOID_NO_CHANGED_VALUE" in status.reasons


def test_duration_alias_null_mismatch_is_a_named_hard_failure() -> None:
    """A null/non-null duration alias mismatch must fail before control interpretation."""
    module = _load_exp103()
    adapter = module.Adapter(n_boot=20, n_destroy=20, seeds=(0, 1))
    frame = adapter.fixture_frame().with_columns(
        pl.when(pl.int_range(pl.len()) == 0)
        .then(None)
        .otherwise(pl.col("swing_duration_ns"))
        .alias("swing_duration_ns")
    )

    status = adapter.integrity(frame)

    assert not status.blocking_pass
    assert "VOID_DURATION_ALIAS_NULLNESS_MISMATCH" in status.reasons


def test_cluster_sequence_is_sorted_by_first_raid_timestamp_then_level() -> None:
    """Circular blocks must follow the predeclared complete-level chronology."""
    module = _load_exp103()
    adapter = module.Adapter(n_boot=2, n_destroy=2, seeds=(0,))
    frame = adapter.fixture_frame().head(4).with_columns(
        pl.Series("level_id", ["L-B", "L-A", "L-B", "L-A"]),
        pl.Series("sweep_ts_ns", [30, 20, 40, 10]),
    )

    _, view = adapter._population_view(
        frame,
        arm=False,
        comparator=True,
        channel="swing_atr",
    )

    assert view.cluster_ids.tolist() == ["L-A", "L-A", "L-B", "L-B"]


def test_destroy_se_uses_registered_nested_outer_bootstrap() -> None:
    """Destroy statistics must be recomputed inside each joint cluster population.

    Four rows, clusters A=[F@1.0, T@4.0] and B=[F@2.0, T@8.0], one destroy
    group of size 4. The registered procedure deranges the outcome blocks
    inside every resampled population b (donor pool = b's rows), so the
    destroyed mean for population b is the exact uniform-derangement mean
    E[D | b] = (W*G - S)/(m - 1), and the SE carries the exact within-
    population draw variance as Var/n_destroy. For seed 0, n_boot=20,
    n_destroy=8 this composition is
    sqrt(var_between(0.1388157894736842) + mean(Var_draw)/8 (1.4125)).
    """
    module = _load_exp103()
    source = module.Adapter(n_boot=2, n_destroy=2, seeds=(0,)).fixture_frame()
    rows = pl.concat(
        [
            source.filter(pl.col("tight_gap") == False).head(2),  # noqa: E712
            source.filter(pl.col("tight_gap") == True).head(2),  # noqa: E712
        ]
    )
    frame = rows.with_columns(
        pl.Series("level_id", ["A", "B", "A", "B"]),
        pl.Series("swing_atr", [1.0, 2.0, 4.0, 8.0]),
        pl.Series("swing_duration_ns", [1.0, 2.0, 4.0, 8.0]),
        pl.Series("duration_ns", [1.0, 2.0, 4.0, 8.0]),
        pl.Series("strong_move", [False, False, True, True]),
    )
    adapter = module.Adapter(n_boot=20, n_destroy=8, seeds=(0,))

    status = adapter.integrity(frame)
    record = next(
        row for row in status.evidence["controls"] if row["channel"] == "swing_atr"
    )

    # Exact sufficient-statistic composition of the registered procedure for
    # the rows above: seed-0 joint circular cluster draws with the destroy
    # recomputed inside each draw (uniform-derangement mean + exact draw
    # variance / n_destroy).
    assert record["destroyed_bootstrap_se"] == 1.2455182814690775
    assert record["nested_seeds"][0]["var_between_populations"] == 0.1388157894736842
    assert record["nested_seeds"][0]["var_within_draws_over_n_destroy"] == pytest.approx(
        1.4125
    )


def test_control_artifact_discloses_destroyed_summaries_not_draw_list() -> None:
    """Live JSON keeps mean/interval/draw-count; the 2,000-draw list is omitted."""
    module = _load_exp103()
    adapter = module.Adapter(n_boot=20, n_destroy=8, seeds=(0, 1))

    status = adapter.integrity(adapter.fixture_frame())
    record = next(
        row for row in status.evidence["controls"] if row["channel"] == "swing_atr"
    )

    assert record["destroyed_draws"] == 8
    assert record["destroyed_interval"] is not None
    assert "destroyed_contrasts" not in record
