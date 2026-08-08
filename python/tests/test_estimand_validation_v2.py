"""INFR-012 estimand gate v2 tests — Nautilus emission contract v1."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import polars as pl
import pytest

from xen.estimand_validation import (
    PHASE_B_STUB_STATUS,
    validate_nautilus_run_v2,
    validate_run,
)
from xen.nautilus.emission import write_emission_v1

_REPO = Path(__file__).resolve().parents[2]
_SMOKE_BAR = _REPO / "data" / "nautilus_runs" / "INFR-010-smoke-bar-1.230.0"


def _write_minimal_emission(
    tmp_path: Path,
    *,
    fence: dict | None = None,
    instrument_map: dict[str, str] | None = None,
) -> Path:
    bars = pl.DataFrame(
        {
            "SourceCloseTime": [
                datetime(2024, 1, 1, 0, 0),
                datetime(2024, 1, 1, 0, 1),
            ],
            "RealOpen": [100.0, 101.0],
        }
    ).with_columns(pl.col("SourceCloseTime").cast(pl.Datetime("ns")))
    ledger = pl.DataFrame(
        {
            "instrument_id": ["BTCUSDT-LINEAR.BYBIT"],
            "entry": ["BUY"],
            "avg_px_open": [100.0],
            "avg_px_close": [101.0],
            "ts_opened": [datetime(2024, 1, 1, 0, 0)],
            "ts_closed": [datetime(2024, 1, 1, 0, 1)],
        }
    ).with_columns(
        pl.col("ts_opened").cast(pl.Datetime("ns")),
        pl.col("ts_closed").cast(pl.Datetime("ns")),
    )
    run_dir = tmp_path / "run"
    write_emission_v1(
        run_dir,
        fills=pl.DataFrame(),
        orders=pl.DataFrame(),
        positions_ledger=ledger,
        bar_marks=bars,
        instrument_id_map=instrument_map or {"BTCUSDT": "BTCUSDT-LINEAR.BYBIT"},
        run_config={"strategy": "test"},
        nautilus_version="1.230.0",
        platform="test",
        fence=fence,
        catalog_version="test-v1",
        catalog_path="data/catalog",
    )
    return run_dir


@pytest.mark.skipif(not _SMOKE_BAR.exists(), reason="Phase B smoke emission not present")
def test_phase_b_stub_attestation_fails_blocking() -> None:
    """HARD REQUIREMENT: v2 must FAIL Phase-B STUB fence_attestation."""
    fence = json.loads((_SMOKE_BAR / "fence_attestation.json").read_text())
    assert fence.get("status") == PHASE_B_STUB_STATUS

    report = validate_run(_SMOKE_BAR, expected_instruments=["BTCUSDT"])
    assert report["emission_type"] == "nautilus_v1"
    assert report["gate_version"] == "v2"
    assert not report["blocking_pass"]
    assert not report["fence"]["ok"]
    assert "STUB" in report["fence"]["reason"]


def test_stub_emission_fails_in_tmp(tmp_path: Path) -> None:
    run_dir = _write_minimal_emission(tmp_path)  # default STUB fence from write_emission_v1
    report = validate_nautilus_run_v2(run_dir, repo_root=_REPO)
    assert not report["blocking_pass"]
    assert report["fence"]["status"] == PHASE_B_STUB_STATUS


def test_pinned_manifest_passes_when_manifest_exists(tmp_path: Path) -> None:
    manifest_dir = (
        tmp_path
        / "archive"
        / "chapter-04-nautilus-bybit-sigauc"
        / "experiments"
        / "INFR-011"
        / "artifacts"
    )
    manifest_dir.mkdir(parents=True)
    manifest = manifest_dir / "fence-manifest.json"
    manifest.write_text(
        json.dumps({
            "train_end_utc": "2025-01-01T00:00:00Z",
            "test_start_utc": "2025-01-01T00:00:00Z",
            "holdout_start_utc": "2025-06-01T00:00:00Z",
        }) + "\n",
        encoding="utf-8",
    )
    import hashlib
    manifest_sha = hashlib.sha256(manifest.read_bytes()).hexdigest()

    fence = {
        "status": "PINNED",
        "analysis_end_utc": "2025-06-01T00:00:00Z",
        "manifest_path": (
            "archive/chapter-04-nautilus-bybit-sigauc/experiments/"
            "INFR-011/artifacts/fence-manifest.json"
        ),
        "manifest_sha256": manifest_sha,
    }
    run_dir = _write_minimal_emission(tmp_path / "em", fence=fence)
    report = validate_nautilus_run_v2(run_dir, repo_root=tmp_path)
    assert report["fence"]["within_fence"]
    assert report["fence"]["manifest"]["ok"]
    assert report["blocking_pass"]


def test_spread_scale_routing() -> None:
    from xen.evaluation_cost_legacy import spread_scale_route  # archived (INFR-022)

    # XENA-003 class: 1.96 bps gross vs 0.71 bps breakeven spread
    r = spread_scale_route(1.96, 0.71 / 3.0)  # rt spread ~0.71 if threshold uses 3×
    # With rt_spread_bps=0.237, threshold=0.71 — 1.96 is decidable
    assert not r["t1_undecidable"]

    r2 = spread_scale_route(1.0, 0.5)  # gross 1.0 < 3*0.5=1.5
    assert r2["t1_undecidable"]
    assert r2["route"] == "AWAITING_MBP"


def test_no_cost_charged_blocks_commissioned_emission(tmp_path: Path) -> None:
    """INFR-022 §3.2: an emission carrying a non-zero commission column fails the gate."""
    ledger = pl.DataFrame(
        {
            "instrument_id": ["BTCUSDT-LINEAR.BYBIT"],
            "entry": ["BUY"],
            "avg_px_open": [100.0],
            "avg_px_close": [101.0],
            "ts_opened": [datetime(2024, 1, 1, 0, 0)],
            "ts_closed": [datetime(2024, 1, 1, 0, 1)],
            "commissions": [0.05],  # engine-charged commission — forbidden
        }
    ).with_columns(
        pl.col("ts_opened").cast(pl.Datetime("ns")),
        pl.col("ts_closed").cast(pl.Datetime("ns")),
    )
    run_dir = tmp_path / "run"
    write_emission_v1(
        run_dir,
        fills=pl.DataFrame(),
        orders=pl.DataFrame(),
        positions_ledger=ledger,
        bar_marks=pl.DataFrame(
            {
                "SourceCloseTime": [datetime(2024, 1, 1, 0, 0),
                                    datetime(2024, 1, 1, 0, 1)],
                "RealOpen": [100.0, 101.0],
            }
        ).with_columns(pl.col("SourceCloseTime").cast(pl.Datetime("ns"))),
        instrument_id_map={"BTCUSDT": "BTCUSDT-LINEAR.BYBIT"},
        run_config={"strategy": "test"},
        nautilus_version="1.230.0",
        platform="test",
        fence={
            "status": "PINNED",
            "analysis_end_utc": "2025-06-01T00:00:00Z",
            "manifest_path": (
                "archive/chapter-04-nautilus-bybit-sigauc/experiments/"
                "INFR-011/artifacts/fence-manifest.json"
            ),
            "manifest_sha256": "x" * 64,
        },
        catalog_version="test-v1",
        catalog_path="data/catalog",
    )
    report = validate_nautilus_run_v2(run_dir, repo_root=_REPO)
    assert not report["blocking_pass"]
    assert not report["no_cost_charged"]["ok"]
    assert "commissions" in report["no_cost_charged"]["emission_cost_columns"]["non_zero_columns"]
    assert report["no_cost_charged"]["cost_model"] == "NO_COST_CHARGED"


def test_nonzero_cost_bps_requires_directive(tmp_path: Path) -> None:
    """INFR-022 §3.4: a non-zero --cost-bps pin fails without operator_cost_directive.json."""
    run_dir = _write_minimal_emission(tmp_path / "em")
    report = validate_nautilus_run_v2(run_dir, cost_bps=2.0, repo_root=_REPO)
    assert not report["blocking_pass"]
    assert not report["no_cost_charged"]["ok"]
    assert "missing operator_cost_directive.json" in report["no_cost_charged"]["cost_directive"]["reason"]
    # with the directive file present, the pin is directive-backed
    (run_dir / "operator_cost_directive.json").write_text(
        json.dumps({"reason": "operator JI: scoped cost experiment EXP-X (design §6)",
                    "scope": "EXP-X"}),
        encoding="utf-8",
    )
    report2 = validate_nautilus_run_v2(run_dir, cost_bps=2.0, repo_root=_REPO)
    assert report2["no_cost_charged"]["ok"]
    assert report2["no_cost_charged"]["cost_model"] == "DIRECTIVE_BACKED"
    # (blocking_pass stays False here only because the minimal emission's fence is a
    # Phase-B STUB — unrelated to the zero-cost check, covered by other tests)
