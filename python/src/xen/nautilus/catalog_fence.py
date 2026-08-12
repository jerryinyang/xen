"""Global calendar fence (INFR-011 A6) — manifest loader + fence-enforcing queries.

The fence manifest
(``archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-011/artifacts/fence-manifest.json``)
pins ABSOLUTE dates for the nested chronological split over the admitted catalog
range (INFR-010 D6):

    analysis_start_utc ──► train_end_utc ──► holdout_start_utc ──► data_end_utc
    |─────────── TRAIN ───────────|──── TEST ────|──── HOLDOUT (never) ────|

Every catalog read in experiment code goes through :func:`fenced_bar_query` (or
is bounded by :func:`assert_within_fence`). HOLDOUT is refused unconditionally —
no sanctioned path exists in code; both lifetime holdout shots are governance
events, not API calls.

Emission attestation: :func:`fence_attestation_payload` produces the
``fence_attestation.json`` payload that ``xen.estimand_validation`` v2 verifies
(``status="PINNED"`` + ``manifest_sha256`` of the manifest file).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from nautilus_trader.persistence.catalog import ParquetDataCatalog

MANIFEST_RELPATH = (
    "archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-011/artifacts/fence-manifest.json"
)
_BANDS = ("TRAIN", "TEST")


class FenceViolation(RuntimeError):
    """A query attempted to read beyond its sanctioned band."""


@dataclass(frozen=True)
class FenceManifest:
    analysis_start_utc: datetime
    train_end_utc: datetime
    holdout_start_utc: datetime
    data_end_utc: datetime
    path: Path
    sha256: str
    raw: dict[str, Any]

    @property
    def analysis_end_utc(self) -> datetime:
        """End of the sanctioned analysis set (= holdout start)."""
        return self.holdout_start_utc


def _repo_root() -> Path:
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("repo root not found (no .git upward of xen.nautilus)")


def _parse_utc(s: str) -> datetime:
    dt = datetime.fromisoformat(s.rstrip("Z"))
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def load_fence_manifest(path: str | Path | None = None) -> FenceManifest:
    """Load + hash the pinned fence manifest (default: canonical repo path)."""
    p = Path(path) if path is not None else _repo_root() / MANIFEST_RELPATH
    blob = p.read_bytes()
    raw = json.loads(blob)
    return FenceManifest(
        analysis_start_utc=_parse_utc(raw["analysis_start_utc"]),
        train_end_utc=_parse_utc(raw["train_end_utc"]),
        holdout_start_utc=_parse_utc(raw["holdout_start_utc"]),
        data_end_utc=_parse_utc(raw["data_end_utc"]),
        path=p,
        sha256=hashlib.sha256(blob).hexdigest(),
        raw=raw,
    )


def band_bounds(manifest: FenceManifest, band: str) -> tuple[datetime, datetime]:
    """Sanctioned [start, end] for a band. HOLDOUT is never a valid band."""
    if band == "TRAIN":
        return manifest.analysis_start_utc, manifest.train_end_utc
    if band == "TEST":
        return manifest.train_end_utc, manifest.holdout_start_utc
    raise FenceViolation(
        f"band must be one of {_BANDS} — HOLDOUT reads are refused unconditionally"
    )


def assert_within_fence(
    manifest: FenceManifest,
    start: datetime,
    end: datetime,
    *,
    band: str = "TRAIN",
) -> None:
    """Raise :class:`FenceViolation` unless [start, end] lies inside ``band``."""
    lo, hi = band_bounds(manifest, band)
    s = start if start.tzinfo else start.replace(tzinfo=timezone.utc)
    e = end if end.tzinfo else end.replace(tzinfo=timezone.utc)
    if s > e:
        raise FenceViolation(f"start {s} after end {e}")
    if s < lo or e > hi:
        raise FenceViolation(
            f"query [{s} .. {e}] outside sanctioned {band} band [{lo} .. {hi}]"
        )
    if e >= manifest.holdout_start_utc and band != "TEST":
        raise FenceViolation("query touches holdout boundary")


def fenced_bar_query(
    catalog: "ParquetDataCatalog",
    bar_types: list[str],
    start: datetime,
    end: datetime,
    *,
    band: str = "TRAIN",
    manifest: FenceManifest | None = None,
) -> list[Any]:
    """Fence-enforcing catalog bar read — the ONLY sanctioned bar-read path.

    Parameters
    ----------
    catalog :
        ``ParquetDataCatalog`` at ``data/catalog/``.
    bar_types :
        Bar type strings, e.g. ``"BTCUSDT-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL"``.
    start, end :
        UTC bounds of the read; must lie inside ``band``.
    band :
        ``"TRAIN"`` (default) or ``"TEST"``. TEST reads on candidate emissions
        are counted governance events — the caller must hold operator approval.

    Returns
    -------
    list
        Nautilus ``Bar`` objects within the sanctioned window.
    """
    m = manifest or load_fence_manifest()
    assert_within_fence(m, start, end, band=band)
    return catalog.bars(bar_types=bar_types, start=start, end=end)


def fence_attestation_payload(
    manifest: FenceManifest | None = None,
) -> dict[str, Any]:
    """``fence_attestation.json`` payload for emission writes (estimand gate v2)."""
    m = manifest or load_fence_manifest()
    try:
        manifest_relpath = m.path.resolve().relative_to(_repo_root().resolve()).as_posix()
    except ValueError as exc:
        raise ValueError("fence manifest must be inside the repository") from exc
    return {
        "status": "PINNED",
        "analysis_end_utc": m.analysis_end_utc.isoformat().replace("+00:00", "Z"),
        "train_end_utc": m.train_end_utc.isoformat().replace("+00:00", "Z"),
        "holdout_start_utc": m.holdout_start_utc.isoformat().replace("+00:00", "Z"),
        "manifest_path": manifest_relpath,
        "manifest_sha256": m.sha256,
    }
