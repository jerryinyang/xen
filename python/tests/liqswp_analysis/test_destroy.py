from __future__ import annotations

import itertools

import numpy as np
import pytest

from xen.liqswp_analysis.destroy import (
    DestroySpec,
    _derangement_variance,
    apply_destroy_mappings,
    build_destroy_mappings,
    derange_indices,
    destroyed_contrasts,
    draw_destroy_contrasts,
    future_destroy_attestation,
    nested_destroy_bootstrap,
    reference_destroyed_contrasts,
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


def _nested_evidence(
    *,
    se_raw: float = 0.1,
    se_mean: float = 0.1,
    raw_estimate: float | None = None,
) -> dict:
    return {
        "seeds": [
            {
                "seed": 0,
                "finite_draws": 10_000,
                "nonfinite_draws": 0,
                "bootstrap_se_raw": se_raw,
                "bootstrap_se_mean_destroyed": se_mean,
                "var_between_populations": se_mean**2,
                "var_within_draws_over_n_destroy": 0.0,
            }
        ]
    }


def _donor_run(view: PopulationView, *, value_override=None) -> object:
    columns = _columns()
    if value_override is not None:
        columns["swing_atr"] = value_override
    return draw_destroy_contrasts(
        f"{view.population_id}|donor",
        columns,
        view.labels,
        arm=view.arm,
        comparator=view.comparator,
        channel="swing_atr",
        spec=_spec(),
        n_destroy=8,
        batch_size=4,
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
        n_destroy=1,
    )
    assert mappings.group_sizes == (4,)
    assert mappings.reasons == ()
    assert mappings.moved_rows == 4
    assert np.count_nonzero(mappings.permutations[0, 0] == np.arange(4)) == 0


def test_singleton_group_is_blocking_void() -> None:
    columns = _columns()
    columns["status"] = np.asarray(["A", "B", "B", "B"], dtype=object)
    view = _population()
    donor_run = draw_destroy_contrasts(
        f"{view.population_id}|donor",
        columns,
        view.labels,
        arm=view.arm,
        comparator=view.comparator,
        channel="swing_atr",
        spec=_spec(),
        n_destroy=8,
    )
    status = future_destroy_attestation(view, donor_run=donor_run, nested=_nested_evidence())
    assert not status.blocking_pass
    assert "VOID_SINGLETON_GROUP" in status.reasons


def test_population_mismatch_blocks_before_statistics() -> None:
    view = _population()
    columns = _columns()
    donor_run = draw_destroy_contrasts(
        "different-population",
        columns,
        view.labels,
        arm=view.arm,
        comparator=view.comparator,
        channel="swing_atr",
        spec=_spec(),
        n_destroy=8,
    )
    status = future_destroy_attestation(view, donor_run=donor_run, nested=_nested_evidence())
    assert not status.blocking_pass
    assert "VOID_POPULATION_MISMATCH" in status.reasons


def test_vacuous_mapping_blocks_when_eligible_values_do_not_change() -> None:
    view = _population()
    columns = _columns()
    columns["swing_atr"] = np.ones(4)
    donor_run = draw_destroy_contrasts(
        f"{view.population_id}|donor",
        columns,
        view.labels,
        arm=view.arm,
        comparator=view.comparator,
        channel="swing_atr",
        spec=_spec(),
        n_destroy=8,
    )
    status = future_destroy_attestation(view, donor_run=donor_run, nested=_nested_evidence())
    assert not status.blocking_pass
    assert "VOID_NO_CHANGED_VALUE" in status.reasons


def test_surviving_destroyed_edge_is_blocking() -> None:
    view = _population()
    donor_run = _donor_run(view)
    nested = _nested_evidence(se_raw=0.1, se_mean=0.1)
    status = future_destroy_attestation(view, donor_run=donor_run, nested=nested)
    assert not status.blocking_pass
    assert "VOID_FUTURE_DESTROY_SURVIVAL" in status.reasons


def test_no_raw_bite_reports_control_without_collapse_claim() -> None:
    view = _population()
    donor_run = _donor_run(view)
    # Raw contrast is finite but every per-seed raw SE is large: no raw bite.
    nested = _nested_evidence(se_raw=10.0, se_mean=0.1)
    status = future_destroy_attestation(view, donor_run=donor_run, nested=nested)
    assert status.blocking_pass
    assert status.evidence["raw_bite"] is False
    assert status.evidence["destroyed_survives"] is False


def test_empty_arm_is_valid_and_skips_destroy_attestation() -> None:
    view = PopulationView(
        population_id="exp101:eur:swing_atr",
        labels=np.asarray(["BASE", "BASE"], dtype=object),
        arm="ARM",
        comparator="BASE",
        cluster_ids=np.asarray(["L0", "L1"], dtype=object),
        values=np.asarray([1.0, 2.0]),
    )
    columns = {
        "symbol": np.asarray(["EUR", "EUR"], dtype=object),
        "status": np.asarray(["COMPLETED", "COMPLETED"], dtype=object),
        "profile_reason": np.asarray(["A", "B"], dtype=object),
        "swing_atr": np.asarray([1.0, 2.0]),
    }
    donor_run = draw_destroy_contrasts(
        f"{view.population_id}|donor",
        columns,
        view.labels,
        arm=view.arm,
        comparator=view.comparator,
        channel="swing_atr",
        spec=_spec(),
        n_destroy=8,
    )
    status = future_destroy_attestation(view, donor_run=donor_run, nested=_nested_evidence())
    assert status.blocking_pass
    assert status.evidence["note"] == "EMPTY_ARM_OR_COMPARATOR - no estimate possible"


def test_empty_donor_draw_discloses_without_array_operations() -> None:
    """An empty donor population must disclose EMPTY_ARM, never crash.

    Regression for the destroy.py:382 TypeError on an empty object-dtype label
    array (the `(labels == arm) & finite_channel` bitwise-and)."""
    columns = {
        "symbol": np.asarray([], dtype=object),
        "status": np.asarray([], dtype=object),
        "profile_reason": np.asarray([], dtype=object),
        "swing_atr": np.asarray([], dtype=float),
    }
    donor_run = draw_destroy_contrasts(
        "empty|donor",
        columns,
        np.asarray([], dtype=object),
        arm="ARM",
        comparator="BASE",
        channel="swing_atr",
        spec=_spec(),
        n_destroy=8,
    )
    assert donor_run.contrasts.shape == (8,)
    assert np.isnan(donor_run.contrasts).all()
    assert donor_run.summary.group_sizes == ()


def test_empty_view_nested_bootstrap_returns_empty_seeds() -> None:
    """An empty arm-vs-comparator view must return empty seeds, never crash.

    Regression for the np.stack(group_matrices) ValueError on an empty group
    matrix (the earlier n_clusters == 0 guard was dead code behind the stack)."""
    view = PopulationView(
        population_id="empty",
        labels=np.asarray([], dtype=object),
        arm="ARM",
        comparator="BASE",
        cluster_ids=np.asarray([], dtype=object),
        values=np.asarray([], dtype=float),
    )
    columns = {
        "symbol": np.asarray([], dtype=object),
        "status": np.asarray([], dtype=object),
        "profile_reason": np.asarray([], dtype=object),
        "swing_atr": np.asarray([], dtype=float),
    }
    nested = nested_destroy_bootstrap(view, columns, _spec(), channel="swing_atr")
    assert len(nested["seeds"]) == 5
    for seed_row in nested["seeds"]:
        assert seed_row["bootstrap_se_raw"] is None
        assert seed_row["finite_draws"] == 0
    donor_run = draw_destroy_contrasts(
        "empty|donor",
        columns,
        view.labels,
        arm=view.arm,
        comparator=view.comparator,
        channel="swing_atr",
        spec=_spec(),
        n_destroy=8,
    )
    status = future_destroy_attestation(view, donor_run=donor_run, nested=nested)
    assert status.blocking_pass
    assert status.evidence["note"] == "EMPTY_ARM_OR_COMPARATOR - no estimate possible"


def test_batched_destroy_equals_simple_reference() -> None:
    population = _population()
    mappings = build_destroy_mappings(
        _columns(),
        _spec(),
        seeds=(1, 2, 3, 4, 5),
        population_id=population.population_id,
        n_destroy=1,
    )
    moved = apply_destroy_mappings(population.values, mappings)
    assert moved.shape == (5, 1, 4)
    assert np.array_equal(
        destroyed_contrasts(population, mappings),
        reference_destroyed_contrasts(population, mappings),
    )


def test_draw_destroy_contrasts_matches_reference_seeded_mappings() -> None:
    population = _population()
    seeds = tuple(range(25))
    reference = build_destroy_mappings(
        _columns(),
        _spec(),
        seeds=seeds,
        population_id=population.population_id,
        n_destroy=1,
    )
    run = draw_destroy_contrasts(
        f"{population.population_id}|donor",
        _columns(),
        population.labels,
        arm=population.arm,
        comparator=population.comparator,
        channel="swing_atr",
        spec=_spec(),
        n_destroy=25,
        batch_size=4,
    )
    assert np.allclose(run.contrasts, destroyed_contrasts(population, reference))
    assert run.summary.group_sizes == reference.group_sizes
    assert run.summary.moved_rows == reference.moved_rows


def test_derangement_variance_matches_bruteforce_enumeration() -> None:
    """The exact closed-form draw variance equals brute-force derangement draws."""
    rng = np.random.default_rng(7)
    for m in range(2, 7):
        values = rng.normal(size=m)
        weights = rng.normal(size=m)
        G = float(values.sum())
        Q = float((values * values).sum())
        W = float(weights.sum())
        S = float((weights * values).sum())
        U = float((weights * weights).sum())
        Uv = float((weights * weights * values).sum())
        Uv2 = float((weights * weights * values * values).sum())
        V2 = float((weights * values * values).sum())
        closed = _derangement_variance(G, Q, W, S, U, Uv, Uv2, V2, m)
        derangements = [
            perm
            for perm in itertools.permutations(range(m))
            if all(perm[i] != i for i in range(m))
        ]
        draws = np.asarray(
            [float((weights * values[np.asarray(perm)]).sum()) for perm in derangements]
        )
        brute = float(((draws - draws.mean()) ** 2).mean())
        assert closed == pytest.approx(brute, abs=1e-10)
