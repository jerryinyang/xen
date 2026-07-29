import json
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from xen.resolution_basis import (
    build_expected_resolution,
    write_basis,
    write_expected_resolution,
)


def _basis():
    return {
        "n_bands": [
            {"n_band": "5,000-15,000", "c_median": 8.0},
            {"n_band": "15,000-inf", "c_median": 12.0},
        ]
    }


def _prior():
    return {
        "artifact_version": 1,
        "grain": ["source", "clock", "H", "h", "z", "event_type", "policy"],
        "declared_axes": {
            "source": ["Z-VOL", "Z-MAG"],
            "clock": ["H1"],
            "H": [12],
            "h": [12],
            "z": [1.5, 2.0],
            "event_type": ["E-TOUCH"],
            "policy": ["P-MOMO", "P-MR"],
        },
        "known_parent_cells": [
            {
                "source": "Z-VOL",
                "clock": "H1",
                "H": 12,
                "h": 12,
                "z": 1.5,
                "event_type": "E-TOUCH",
                "policy": "P-MOMO",
                "expected_n": 16_000,
            }
        ],
    }


def test_build_expected_resolution_expands_every_declared_stratum():
    payload = build_expected_resolution(
        _prior(),
        _basis(),
        generated_at_utc="2026-07-29T00:00:00Z",
        source_hashes={"parent.parquet": "abc"},
    )

    assert payload["row_count"] == 8
    assert len(payload["strata"]) == 8
    known = [
        row
        for row in payload["strata"]
        if row["source"] == "Z-VOL"
        and row["z"] == 1.5
        and row["policy"] == "P-MOMO"
    ][0]
    assert known["prior_status"] == "KNOWN_PARENT_SIGNED_ARM"
    assert known["n_band"] == "15,000-inf"
    assert known["expected_n"] == 16_000
    assert known["expected_mde50"] == pytest.approx(12 / 16_000**0.5)

    unknown = [
        row
        for row in payload["strata"]
        if row["source"] == "Z-MAG" and row["policy"] == "P-MR"
    ][0]
    assert unknown["prior_status"] == "UNKNOWN_NO_PARENT_SIGNED_ARM"
    assert unknown["expected_n"] is None
    assert unknown["n_band"] is None
    assert unknown["expected_mde50"] is None


def test_write_expected_resolution_is_stable_and_records_hashes(tmp_path):
    prior_path = tmp_path / "prior.json"
    basis_path = tmp_path / "basis.json"
    output_path = tmp_path / "expected.json"
    prior_path.write_text(json.dumps(_prior()))
    basis_path.write_text(json.dumps(_basis()))

    first = write_expected_resolution(
        prior_path,
        basis_path,
        output_path,
        generated_at_utc="2026-07-29T00:00:00Z",
        source_hashes={"parent.parquet": "abc"},
    )
    first_bytes = output_path.read_bytes()
    second = write_expected_resolution(
        prior_path,
        basis_path,
        output_path,
        generated_at_utc="2026-07-29T00:00:00Z",
        source_hashes={"parent.parquet": "abc"},
    )

    assert first == second
    assert output_path.read_bytes() == first_bytes
    assert first["input_sha256"]["prior"] == hashlib.sha256(
        prior_path.read_bytes()
    ).hexdigest()
    assert first["input_sha256"]["basis"] == hashlib.sha256(
        basis_path.read_bytes()
    ).hexdigest()


def test_prior_may_name_its_own_unknown_status_and_reason():
    prior = _prior()
    prior["known_parent_cells"] = []
    prior["unknown_status"] = "UNKNOWN_NO_PARENT_MEASURED_POPULATION"
    prior["unknown_reason"] = "no parent ever ran this entry"

    payload = build_expected_resolution(
        prior,
        _basis(),
        generated_at_utc="2026-07-29T00:00:00Z",
        source_hashes={"parent.parquet": "abc"},
    )

    statuses = {row["prior_status"] for row in payload["strata"]}
    assert statuses == {"UNKNOWN_NO_PARENT_MEASURED_POPULATION"}
    assert all(row["expected_n"] is None for row in payload["strata"])
    assert payload["provenance"] == "no parent ever ran this entry"


def _source_cells():
    # Two arms; arm B is deliberately coarser so a mixed population would shift `c`.
    rows = []
    for arm, base_n in (("C", 16_000), ("B", 400)):
        for h in (4, 12, 24):
            for i in range(4):
                rows.append(
                    {
                        "arm": arm,
                        "basis": f"b{i % 2}",
                        "h": h,
                        "gross_n": base_n + i,
                        "gross_block_mde_mean_bps": 10.0 + h,
                        "gross_p": 0.45,
                        "gross_L": 120.0,
                    }
                )
    # Three rows that are arithmetically undefined, one per exclusion reason.
    rows += [
        {"arm": "C", "basis": "b0", "h": 12, "gross_n": np.nan,
         "gross_block_mde_mean_bps": 12.0, "gross_p": 0.4, "gross_L": 100.0},
        {"arm": "C", "basis": "b0", "h": 12, "gross_n": 1,
         "gross_block_mde_mean_bps": 12.0, "gross_p": 0.4, "gross_L": 100.0},
        {"arm": "C", "basis": "b0", "h": 12, "gross_n": 500,
         "gross_block_mde_mean_bps": 12.0, "gross_p": 1.0, "gross_L": 100.0},
        {"arm": "C", "basis": "b0", "h": 12, "gross_n": 500,
         "gross_block_mde_mean_bps": 0.0, "gross_p": 0.4, "gross_L": 100.0},
    ]
    return pd.DataFrame(rows)


def test_write_basis_pins_one_population_and_accounts_for_every_dropped_row(tmp_path):
    out = tmp_path / "basis.json"
    source = tmp_path / "source.parquet"
    _source_cells().to_parquet(source)

    payload = write_basis(
        _source_cells(),
        out,
        source="source.parquet",
        source_ci_rule="SPDR-018 §6.2 verbatim",
        ladder=[0.03, 0.10],
        group_col="basis",
        horizon_col="h",
        input_filter={"column": "arm", "operator": "==", "value": "C",
                      "population": "signed parent arm C"},
        source_path=source,
        generated_at_utc="2026-07-29T00:00:00Z",
    )

    counts = payload["row_counts"]
    assert counts["source_input"] == 28
    assert counts["filter_matched"] == 16
    assert counts["retained"] == 12
    assert counts["excluded"] == 4
    assert counts["excluded_by_reason"] == {
        "missing_required_value": 1,
        "n_not_above_one": 1,
        "non_positive_or_non_finite_denominator": 1,
        "non_positive_or_non_finite_mde": 1,
    }
    assert sum(counts["excluded_by_reason"].values()) == counts["excluded"]
    # Arm B never enters: a mixed population would put cells in the small-n bands.
    assert {row["n_band"] for row in payload["n_bands"]} == {"15,000-inf"}
    assert payload["input_filter"]["value"] == "C"
    assert payload["source_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert payload["generator_sha256"] == hashlib.sha256(
        Path(__file__).resolve().parents[1].joinpath("src/xen/resolution_basis.py").read_bytes()
    ).hexdigest()


def test_write_basis_reports_per_horizon_c_instead_of_asserting_it_is_flat(tmp_path):
    payload = write_basis(
        _source_cells(),
        tmp_path / "basis.json",
        source="source.parquet",
        source_ci_rule="SPDR-018 §6.2 verbatim",
        ladder=[0.03],
        group_col="basis",
        horizon_col="h",
        input_filter={"column": "arm", "operator": "==", "value": "C",
                      "population": "signed parent arm C"},
    )

    band = payload["n_bands"][0]
    summaries = band["horizon_summaries"]
    assert [row["h"] for row in summaries] == [4, 12, 24]
    assert [row["cells"] for row in summaries] == [4, 4, 4]
    # The horizon medians differ here, which is exactly why they are emitted.
    assert len({round(row["c_median"], 6) for row in summaries}) == 3
    assert "flat" not in json.dumps(payload).lower()


def test_write_basis_without_a_filter_keeps_the_original_artifact_shape(tmp_path):
    payload = write_basis(
        _source_cells(),
        tmp_path / "basis.json",
        source="source.parquet",
        source_ci_rule="rule",
        ladder=[0.03],
        group_col="basis",
    )

    assert "row_counts" not in payload
    assert "input_filter" not in payload
    assert "horizon_summaries" not in payload["n_bands"][0]


def test_committed_resolution_artifacts_reproduce_from_the_pinned_inputs():
    python_root = Path(__file__).resolve().parents[1]
    source = python_root / "experiments/SPDR-018/results/analyst_per_cell_magnitudes.parquet"
    if not source.exists():  # pragma: no cover - emission not present in this checkout
        pytest.skip("SPDR-018 emission not available")

    for experiment in ("SPDR-019", "SPDR-020"):
        basis = json.loads(
            (python_root / f"experiments/{experiment}/results/resolution_basis.json").read_bytes()
        )
        assert basis["input_filter"]["column"] == "arm"
        assert basis["input_filter"]["value"] == "C"
        assert basis["row_counts"] == {
            "source_input": 24_098,
            "filter_matched": 18_988,
            "retained": 18_479,
            "excluded": 509,
            "excluded_by_reason": {
                "missing_required_value": 509,
                "n_not_above_one": 0,
                "non_positive_or_non_finite_denominator": 0,
                "non_positive_or_non_finite_mde": 0,
            },
        }
        assert basis["source_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
        band = next(row for row in basis["n_bands"] if row["n_band"] == "15,000-inf")
        assert (band["cells"], band["distinct_n"]) == (26, 8)
        assert [round(row["c_median"], 3) for row in band["horizon_summaries"]] == [
            11.855,
            8.363,
            11.744,
        ]
        assert "flat" not in json.dumps(basis).lower()


def test_spdr019_predeclaration_covers_every_declared_stratum_with_no_placeholder():
    python_root = Path(__file__).resolve().parents[1]
    results = python_root / "experiments/SPDR-019/results"
    expected = json.loads((results / "expected_resolution.json").read_bytes())
    prior = json.loads((results / "expected_resolution_prior.json").read_bytes())

    assert expected["grain"] == ["clock", "delta", "variant_id", "scope"]
    assert expected["row_count"] == 2 * 3 * 33 * 26 == len(expected["strata"])
    assert len(prior["declared_axes"]["variant_id"]) == 33
    assert not any(v.startswith("L5") for v in prior["declared_axes"]["variant_id"])
    assert {row["prior_status"] for row in expected["strata"]} == {
        "UNKNOWN_NO_PARENT_MEASURED_POPULATION"
    }
    assert all(row["expected_n"] is None for row in expected["strata"])
    assert all(row["expected_mde50"] is None for row in expected["strata"])
    assert expected["input_sha256"]["basis"] == hashlib.sha256(
        (results / "resolution_basis.json").read_bytes()
    ).hexdigest()
    assert expected["generated_at_utc"] == "2026-07-29T00:00:00Z"

    prohibited = {"powered", "unpowered", "at_target", "not_resolvable", "computed at run"}
    blob = json.dumps(expected).lower()
    assert not any(token in blob for token in prohibited)


def test_spdr020_predeclaration_still_carries_only_the_two_measured_parent_arms():
    python_root = Path(__file__).resolve().parents[1]
    results = python_root / "experiments/SPDR-020/results"
    expected = json.loads((results / "expected_resolution.json").read_bytes())

    assert expected["row_count"] == 1_296
    known = [row for row in expected["strata"] if row["prior_status"] == "KNOWN_PARENT_SIGNED_ARM"]
    assert sorted(row["expected_n"] for row in known) == [15_041, 15_331]
    assert all(row["n_band"] == "15,000-inf" for row in known)
    assert expected["input_sha256"]["basis"] == hashlib.sha256(
        (results / "resolution_basis.json").read_bytes()
    ).hexdigest()
