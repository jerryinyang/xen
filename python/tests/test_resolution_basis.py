import json
import hashlib

import pytest

from xen.resolution_basis import build_expected_resolution, write_expected_resolution


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
