from __future__ import annotations

import numpy as np

from xen.liqswp_analysis.destroy import (
    DestroySpec,
    apply_destroy_mappings,
    build_destroy_mappings,
    derange_indices,
    destroyed_contrasts,
    future_destroy_attestation,
    reference_destroyed_contrasts,
    stream_destroy_control,
)
from xen.liqswp_analysis.statistics import PopulationView


def _columns() -> dict[str, np.ndarray]:
    return {
        "symbol": np.asarray(["EUR", "EUR", "EUR", "EUR"], dtype=object),
        "status": np.asarray(["COMPLETED"] * 4, dtype=object),
        "profile_reason": np.asarray(["A", "B", "C", "D"], dtype=object),
        "swing_atr": np.asarray([1.0, 2.0, 3.0, 4.0]),
    }


def _spec() -> DestroySpec:
    return DestroySpec(
        group_columns=("symbol", "status"),
        null_columns=("swing_atr",),
        channels=("swing_atr",),
    )


def _population() -> PopulationView:
    return PopulationView(
        population_id="exp101:eur:swing_atr",
        labels=np.asarray(["BASE", "BASE", "ARM", "ARM"], dtype=object),
        arm="ARM",
        comparator="BASE",
        cluster_ids=np.asarray(["L0", "L1", "L2", "L3"], dtype=object),
        values=np.asarray([1.0, 2.0, 3.0, 4.0]),
    )


def test_derangement_has_zero_fixed_points() -> None:
    mapping = derange_indices(12, np.random.default_rng(3))
    assert sorted(mapping.tolist()) == list(range(12))
    assert np.count_nonzero(mapping == np.arange(12)) == 0


def test_exact_grouping_does_not_use_undeclared_columns() -> None:
    columns = _columns()
    mappings = build_destroy_mappings(
        columns,
        _spec(),
        seeds=(1,),
        population_id="exp101:eur:swing_atr",
    )
    assert mappings.group_sizes == (4,)
    assert mappings.reasons == ()
    assert mappings.moved_rows == 4
    assert np.count_nonzero(mappings.permutations[0] == np.arange(4)) == 0


def test_singleton_group_is_blocking_void() -> None:
    columns = _columns()
    columns["status"] = np.asarray(["A", "B", "B", "B"], dtype=object)
    mappings = build_destroy_mappings(
        columns,
        _spec(),
        seeds=(1,),
        population_id="singleton",
    )
    assert "VOID_SINGLETON_GROUP" in mappings.reasons
    status = future_destroy_attestation(
        _population(),
        mappings,
        se_population_id=_population().population_id,
        raw_bootstrap_se=0.1,
        destroyed_estimates=np.asarray([0.0, 0.1]),
        destroyed_bootstrap_se=0.1,
    )
    assert not status.blocking_pass
    assert "VOID_SINGLETON_GROUP" in status.reasons


def test_population_mismatch_blocks_before_statistics() -> None:
    mappings = build_destroy_mappings(
        _columns(),
        _spec(),
        seeds=(1,),
        population_id="different-population",
    )
    status = future_destroy_attestation(
        _population(),
        mappings,
        se_population_id="also-different",
        raw_bootstrap_se=0.1,
        destroyed_estimates=np.asarray([0.0, 0.1]),
        destroyed_bootstrap_se=0.1,
    )
    assert not status.blocking_pass
    assert "VOID_POPULATION_MISMATCH" in status.reasons


def test_vacuous_mapping_blocks_when_eligible_values_do_not_change() -> None:
    columns = _columns()
    columns["swing_atr"] = np.ones(4)
    mappings = build_destroy_mappings(
        columns,
        _spec(),
        seeds=(1,),
        population_id=_population().population_id,
    )
    status = future_destroy_attestation(
        _population(),
        mappings,
        se_population_id=_population().population_id,
        raw_bootstrap_se=0.1,
        destroyed_estimates=np.asarray([0.0, 0.1]),
        destroyed_bootstrap_se=0.1,
    )
    assert not status.blocking_pass
    assert "VOID_NO_CHANGED_VALUE" in status.reasons


def test_surviving_destroyed_edge_is_blocking() -> None:
    mappings = build_destroy_mappings(
        _columns(),
        _spec(),
        seeds=(1, 2),
        population_id=_population().population_id,
    )
    status = future_destroy_attestation(
        _population(),
        mappings,
        se_population_id=_population().population_id,
        raw_bootstrap_se=0.1,
        destroyed_estimates=np.asarray([1.0, 1.2]),
        destroyed_bootstrap_se=0.1,
    )
    assert not status.blocking_pass
    assert "VOID_FUTURE_DESTROY_SURVIVAL" in status.reasons


def test_batched_destroy_equals_simple_reference() -> None:
    population = _population()
    mappings = build_destroy_mappings(
        _columns(),
        _spec(),
        seeds=(1, 2, 3, 4, 5),
        population_id=population.population_id,
    )
    moved = apply_destroy_mappings(population.values, mappings)
    assert moved.shape == (5, 4)
    assert np.array_equal(
        destroyed_contrasts(population, mappings),
        reference_destroyed_contrasts(population, mappings),
    )


def test_streamed_destroy_matches_reference_and_bounds_mapping_batch() -> None:
    population = _population()
    seeds = tuple(range(25))
    reference = build_destroy_mappings(
        _columns(), _spec(), seeds=seeds, population_id=population.population_id
    )
    run = stream_destroy_control(
        population,
        _columns(),
        _spec(),
        seeds=seeds,
        batch_size=4,
    )
    assert np.array_equal(run.estimates, destroyed_contrasts(population, reference))
    assert np.allclose(
        run.average_values, apply_destroy_mappings(population.values, reference).mean(0)
    )
    assert run.max_materialized_mappings == 4
    assert run.summary.permutations.shape == (0, 4)
