"""Immutable DESIGN-only SPDR-011 Run-1 bundle and CONFIRM access guard."""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import polars as pl


BUNDLE_SCHEMA = "spdr011-artifact-bundle/v1"
UNLOCK_SCHEMA = "spdr011-confirm-unlock/v1"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_bundle(root: Path, artifact: pl.DataFrame, *, metadata: dict[str, Any]) -> dict:
    """Write one DESIGN member and refuse to stage CONFIRM during Run 1."""
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty artifact bundle: {root}")
    if "band" not in artifact.columns:
        raise ValueError("artifact requires band column")
    bands = set(artifact["band"].unique().to_list())
    if bands != {"DESIGN"}:
        raise ValueError(f"Run-1 bundle must be DESIGN-only, got {sorted(bands)}")
    root.mkdir(parents=True, exist_ok=True)
    design_path = root / "design.parquet"
    artifact.sort("event_id").write_parquet(design_path)
    manifest = {
        "schema": BUNDLE_SCHEMA,
        "members": {
            "design.parquet": {"sha256": _sha256(design_path)},
        },
        "metadata": metadata,
    }
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"), default=str)
    manifest["bundle_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    (root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return manifest


def append_confirm_unlock(
    root: Path,
    *,
    frozen_rule_hash: str,
    operator_authority: str,
) -> dict:
    """Append one hash-chained operator authority record; never rewrite prior records."""
    if not frozen_rule_hash or not operator_authority:
        raise ValueError("frozen rule hash and operator authority are required")
    path = root / "confirm-unlock.jsonl"
    previous_hash = None
    if path.exists():
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line]
        if lines:
            previous_hash = hashlib.sha256(lines[-1].encode()).hexdigest()
    record = {
        "schema": UNLOCK_SCHEMA,
        "recorded_utc": datetime.now(UTC).isoformat(),
        "frozen_rule_hash": frozen_rule_hash,
        "operator_authority": operator_authority,
        "previous_record_sha256": previous_hash,
    }
    line = json.dumps(record, sort_keys=True, separators=(",", ":"))
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    return record


def read_band(
    root: Path,
    *,
    band: str,
    supplied_rule_hash: str | None = None,
) -> pl.DataFrame:
    """Read DESIGN directly; guard CONFIRM with the latest valid exact-hash authority."""
    if band == "DESIGN":
        return pl.read_parquet(root / "design.parquet")
    if band != "CONFIRM":
        raise ValueError("band must be DESIGN or CONFIRM")
    if not (root / "confirm.parquet").exists():
        raise PermissionError("CONFIRM not executed")
    unlock = root / "confirm-unlock.jsonl"
    if not unlock.exists() or supplied_rule_hash is None:
        raise PermissionError("CONFIRM is sealed without an operator unlock record")
    lines = [line for line in unlock.read_text().splitlines() if line]
    records = [json.loads(line) for line in lines]
    if not records:
        raise PermissionError("CONFIRM is sealed without an operator unlock record")
    for index, record_item in enumerate(records):
        expected_previous = (
            None if index == 0 else hashlib.sha256(lines[index - 1].encode()).hexdigest()
        )
        if record_item.get("previous_record_sha256") != expected_previous:
            raise PermissionError("CONFIRM unlock audit chain is invalid")
    record = records[-1]
    if record.get("schema") != UNLOCK_SCHEMA or not record.get("operator_authority"):
        raise PermissionError("latest CONFIRM unlock record lacks operator authority")
    if record.get("frozen_rule_hash") != supplied_rule_hash:
        raise PermissionError("CONFIRM unlock hash does not match the supplied frozen rule hash")
    return pl.read_parquet(root / "confirm.parquet")
