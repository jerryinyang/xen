"""Bounded-performance proof for the registered nested 10k outer-bootstrap destroy.

EXP-102 QA issue 7: a representative stratum must complete within an
operator-usable runtime. This test runs the exact nested destroy at the
registered live scale (5 outer seeds x 10,000 cluster populations with the
2,000-draw derangement statistics recomputed inside every population) on a
representative 4,000-row / 1,000-cluster stratum for both joint and independent
arm resampling, and bounds the wall-clock time.
"""

from __future__ import annotations

import time

import numpy as np

from xen.liqswp_analysis.destroy import DestroySpec, nested_destroy_bootstrap
from xen.liqswp_analysis.statistics import PopulationView

# Generous CI-safe bound; typical runtime is ~3-7s per seed battery on this size.
BOUND_SECONDS = 120.0


def _representative_view(seed: int = 11) -> tuple[PopulationView, dict[str, np.ndarray]]:
    rng = np.random.default_rng(seed)
    n_rows, n_clusters = 4_000, 1_000
    rows_per_cluster = n_rows // n_clusters
    labels = np.empty(n_rows, dtype=object)
    clusters = np.empty(n_rows, dtype=object)
    values = np.empty(n_rows, dtype=float)
    for c in range(n_clusters):
        base = c * rows_per_cluster
        for j in range(rows_per_cluster):
            index = base + j
            clusters[index] = f"L-{c}"
            labels[index] = "ARM" if j % 2 == 0 else "BASE"
            values[index] = 1.0 + 0.1 * (j % 2) + rng.normal(0.0, 0.01)
    view = PopulationView(
        population_id="perf:stratum:swing_atr",
        labels=labels,
        arm="ARM",
        comparator="BASE",
        cluster_ids=clusters,
        values=values,
    )
    n_rows = len(values)
    columns = {
        "archive_symbol": np.asarray(["EURUSD"] * n_rows, dtype=object),
        "timeframe": np.asarray(["15m"] * n_rows, dtype=object),
        "confirmation_method": np.asarray(["BREAKOUT_BAR"] * n_rows, dtype=object),
        "confirmation_reference": np.asarray(["1H"] * n_rows, dtype=object),
        "side": np.asarray(["HIGH"] * n_rows, dtype=object),
        "status": np.asarray(["COMPLETED"] * n_rows, dtype=object),
        "primary_completed": np.asarray([True] * n_rows, dtype=object),
        "swing_price": np.ones(n_rows),
        "swing_bps": np.ones(n_rows),
        "swing_atr": values,
        "duration_ns": np.ones(n_rows),
        "strong_move": np.asarray([False] * n_rows, dtype=object),
        "swing_duration_ns": np.ones(n_rows),
    }
    return view, columns


def _spec() -> DestroySpec:
    return DestroySpec(
        (
            "archive_symbol",
            "timeframe",
            "confirmation_method",
            "confirmation_reference",
            "side",
            "status",
            "primary_completed",
        ),
        ("swing_price", "swing_bps", "swing_atr", "duration_ns", "strong_move"),
        ("swing_atr",),
    )


def test_nested_destroy_representative_stratum_completes_in_bounded_runtime() -> None:
    """One representative stratum at the registered live scale finishes in bounds."""
    view, columns = _representative_view()
    start = time.perf_counter()
    result = nested_destroy_bootstrap(
        view,
        columns,
        _spec(),
        channel="swing_atr",
        outer_seeds=(0, 1, 2, 3, 4),
        n_boot=10_000,
        block_length=5,
        n_destroy=2_000,
        independent_arms=False,
    )
    elapsed = time.perf_counter() - start
    assert elapsed < BOUND_SECONDS, f"nested destroy took {elapsed:.1f}s"
    assert len(result["seeds"]) == 5
    assert all(seed["bootstrap_se_raw"] is not None for seed in result["seeds"])
    assert all(seed["bootstrap_se_mean_destroyed"] is not None for seed in result["seeds"])
    assert all(seed["finite_draws"] > 0 for seed in result["seeds"])


def test_nested_destroy_independent_arms_completes_in_bounded_runtime() -> None:
    """The EXP-101 independent arm/comparator resampling is bounded too."""
    view, columns = _representative_view()
    start = time.perf_counter()
    result = nested_destroy_bootstrap(
        view,
        columns,
        _spec(),
        channel="swing_atr",
        outer_seeds=(0, 1, 2, 3, 4),
        n_boot=10_000,
        block_length=5,
        n_destroy=2_000,
        independent_arms=True,
    )
    elapsed = time.perf_counter() - start
    assert elapsed < BOUND_SECONDS, f"nested destroy took {elapsed:.1f}s"
    assert len(result["seeds"]) == 5
    assert all(seed["bootstrap_se_raw"] is not None for seed in result["seeds"])
    assert all(seed["bootstrap_se_mean_destroyed"] is not None for seed in result["seeds"])
