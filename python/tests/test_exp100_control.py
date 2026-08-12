"""Focused tests for the EXP-100 future-destroy control."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from xen.exp100.control import destroy_post_confirmation


GROUP_COLUMNS = ("asset", "timeframe", "config")
VALUE_COLUMNS = ("swing_atr", "duration", "strong_move")


def write_control_rows(path: Path, *, include_confirmation: bool = False) -> Path:
    data: dict[str, list[object]] = {
        "raid_id": ["r1", "r2", "r3", "r4", "r5", "r6"],
        "asset": ["BTC", "BTC", "BTC", "ETH", "ETH", "ETH"],
        "timeframe": ["15m"] * 6,
        "config": ["PREVIOUS_1H"] * 6,
        "swing_atr": [1.1, 2.2, 3.3, 4.4, 5.5, 6.6],
        "duration": [11, 22, 33, 44, 55, 66],
        "strong_move": [True, False, True, False, True, False],
    }
    if include_confirmation:
        data["confirmation_ts_ns"] = [None, 2, 3, None, 5, 6]
    pq.write_table(pa.table(data), path)
    return path


def rows(path: Path) -> list[dict[str, object]]:
    return pq.read_table(path).to_pylist()


def grouped_multiset(path: Path) -> list[tuple[object, ...]]:
    values = [
        tuple(row[column] for column in (*GROUP_COLUMNS, *VALUE_COLUMNS))
        for row in rows(path)
    ]
    return sorted(values, key=repr)


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(64 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def test_destroy_has_zero_fixed_points_and_preserves_group_values(tmp_path: Path) -> None:
    source = write_control_rows(tmp_path / "source.parquet")
    destination = tmp_path / "destroyed.parquet"

    report = destroy_post_confirmation(
        source,
        destination,
        group_columns=GROUP_COLUMNS,
        value_columns=VALUE_COLUMNS,
        seed=17,
    )

    assert report["groups"] == 2
    assert report["rows"] == 6
    assert report["fixed_points"] == 0
    assert report["changed_rows"] == report["rows"]
    assert report["contrast_ratio"] == 1.0
    assert grouped_multiset(source) == grouped_multiset(destination)


def test_destroy_is_deterministic_for_same_seed(tmp_path: Path) -> None:
    source = write_control_rows(tmp_path / "source.parquet")
    first = tmp_path / "first.parquet"
    second = tmp_path / "second.parquet"

    kwargs = {
        "group_columns": GROUP_COLUMNS,
        "value_columns": VALUE_COLUMNS,
        "seed": 17,
    }
    destroy_post_confirmation(source, first, **kwargs)
    destroy_post_confirmation(source, second, **kwargs)

    assert digest(first) == digest(second)


def test_destroy_only_remaps_confirmed_rows_when_confirmation_column_exists(
    tmp_path: Path,
) -> None:
    source = write_control_rows(tmp_path / "source.parquet", include_confirmation=True)
    destination = tmp_path / "destroyed.parquet"

    report = destroy_post_confirmation(
        source,
        destination,
        group_columns=GROUP_COLUMNS,
        value_columns=VALUE_COLUMNS,
        seed=17,
    )

    assert report["rows"] == 4
    source_rows = rows(source)
    output_rows = rows(destination)
    for source_row, output_row in zip(source_rows, output_rows):
        if source_row["confirmation_ts_ns"] is None:
            assert output_row["swing_atr"] == source_row["swing_atr"]
            assert output_row["duration"] == source_row["duration"]
            assert output_row["strong_move"] == source_row["strong_move"]


def test_destroy_changes_strong_move_when_present(tmp_path: Path) -> None:
    """Non-vacuity requires the declared strong_move outcome to move with the destroy."""
    source = write_control_rows(tmp_path / "source.parquet")
    destination = tmp_path / "destroyed.parquet"

    report = destroy_post_confirmation(
        source,
        destination,
        group_columns=GROUP_COLUMNS,
        value_columns=VALUE_COLUMNS,
        seed=17,
    )

    assert report["changed_rows"] == report["rows"]
    source_rows = rows(source)
    output_rows = rows(destination)
    moved = sum(
        1
        for source_row, output_row in zip(source_rows, output_rows)
        if (
            source_row["swing_atr"] != output_row["swing_atr"]
            or source_row["duration"] != output_row["duration"]
            or source_row["strong_move"] != output_row["strong_move"]
        )
    )
    assert moved == len(source_rows)
    strong_moved = any(
        source_row["strong_move"] != output_row["strong_move"]
        for source_row, output_row in zip(source_rows, output_rows)
    )
    assert strong_moved


def test_destroy_rejects_singleton_group(tmp_path: Path) -> None:
    source = tmp_path / "source.parquet"
    pq.write_table(
        pa.table(
            {
                "raid_id": ["r1"],
                "asset": ["BTC"],
                "timeframe": ["15m"],
                "config": ["PREVIOUS_1H"],
                "swing_atr": [1.1],
                "duration": [11],
                "strong_move": [True],
            }
        ),
        source,
    )

    with pytest.raises(ValueError, match="singleton"):
        destroy_post_confirmation(
            source,
            tmp_path / "destroyed.parquet",
            group_columns=GROUP_COLUMNS,
            value_columns=VALUE_COLUMNS,
            seed=17,
        )


@pytest.mark.parametrize("missing", ["config", "swing_atr", "raid_id", "strong_move"])
def test_destroy_rejects_missing_required_columns(tmp_path: Path, missing: str) -> None:
    source = write_control_rows(tmp_path / "source.parquet")
    table = pq.read_table(source).drop([missing])
    pq.write_table(table, source)

    with pytest.raises(ValueError, match="missing"):
        destroy_post_confirmation(
            source,
            tmp_path / "destroyed.parquet",
            group_columns=GROUP_COLUMNS,
            value_columns=VALUE_COLUMNS,
            seed=17,
        )


def test_destroy_refuses_to_overwrite_aligned_source(tmp_path: Path) -> None:
    source = write_control_rows(tmp_path / "source.parquet")

    with pytest.raises(ValueError, match="overwrite"):
        destroy_post_confirmation(
            source,
            source,
            group_columns=GROUP_COLUMNS,
            value_columns=VALUE_COLUMNS,
            seed=17,
        )
