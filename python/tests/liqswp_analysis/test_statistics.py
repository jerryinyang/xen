from __future__ import annotations

import numpy as np

from xen.liqswp_analysis.statistics import (
    PopulationView,
    block_sensitivity,
    circular_cluster_indices,
    clustered_contrast_bootstrap,
    estimate_contrast,
)


def _population() -> PopulationView:
    return PopulationView(
        population_id="fixture:arm-vs-base:swing_atr",
        labels=np.asarray(["BASE", "BASE", "ARM", "ARM"], dtype=object),
        arm="ARM",
        comparator="BASE",
        cluster_ids=np.asarray(["L0", "L1", "L2", "L3"], dtype=object),
        values=np.asarray([1.0, 3.0, 5.0, 7.0]),
    )


def test_estimate_contrast_is_arm_minus_fixed_comparator() -> None:
    result = estimate_contrast(_population())
    assert result == {
        "population_id": "fixture:arm-vs-base:swing_atr",
        "estimate": 4.0,
        "arm_mean": 6.0,
        "comparator_mean": 2.0,
        "arm_n": 2,
        "comparator_n": 2,
        "reason": None,
    }


def test_circular_cluster_indices_resample_whole_ordered_clusters() -> None:
    indices = circular_cluster_indices(4, block_length=2, rng=np.random.default_rng(7))
    assert indices.shape == (4,)
    assert all(0 <= int(value) < 4 for value in indices)
    assert int(indices[1]) == (int(indices[0]) + 1) % 4
    assert int(indices[3]) == (int(indices[2]) + 1) % 4


def test_one_cluster_is_explicitly_unavailable() -> None:
    view = PopulationView(
        population_id="thin",
        labels=np.asarray(["BASE", "ARM"], dtype=object),
        arm="ARM",
        comparator="BASE",
        cluster_ids=np.asarray(["L0", "L0"], dtype=object),
        values=np.asarray([1.0, 2.0]),
    )
    result = clustered_contrast_bootstrap(view, block_length=5, n_boot=20, seeds=(0,))
    assert result["reason"] == "ONE_CLUSTER"
    assert result["interval"] is None
    assert result["n_clusters"] == 1


def test_nonfinite_draws_are_counted_not_allowed_to_poison_interval() -> None:
    view = PopulationView(
        population_id="thin-joint",
        labels=np.asarray(["BASE", "ARM", "ARM"], dtype=object),
        arm="ARM",
        comparator="BASE",
        cluster_ids=np.asarray(["L0", "L1", "L2"], dtype=object),
        values=np.asarray([1.0, 2.0, 4.0]),
    )
    result = clustered_contrast_bootstrap(view, block_length=2, n_boot=100, seeds=(1,))
    assert result["nonfinite_draws"] > 0
    assert result["finite_draws"] > 0
    assert result["interval"] is not None
    assert all(np.isfinite(result["interval"]))
    assert np.isfinite(result["bootstrap_se"])


def test_block_sensitivity_always_reports_2_5_10_without_hiding_thin_rows() -> None:
    result = block_sensitivity(_population(), lengths=(2, 5, 10), n_boot=20, seeds=(0,))
    assert list(result) == ["2", "5", "10"]
    assert all(item["population_id"] == _population().population_id for item in result.values())
