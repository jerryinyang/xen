"""Focused regression tests for the Chapter 05 cost/data preflight."""
from __future__ import annotations

import importlib
import importlib.util
import json
from pathlib import Path

import polars as pl
import pytest

import xen.evaluation as evaluation
import xen.sigbar as sigbar
from xen.sigbar.data_types import SIGBAR_PIPELINE_VERSION, SPREAD_UNUSABLE


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_chapter05_quarantine_verifies_frozen_infr017_artifact_without_cost_pins() -> None:
    assert hasattr(evaluation, "verify_chapter05_spread_quarantine")
    verify_quarantine = getattr(evaluation, "verify_chapter05_spread_quarantine")

    bundle = verify_quarantine()

    assert bundle["pin_sha256"] == (
        "e3b9fd9b9b5851b8a9a11f9ce34cd1e0fa8e10ea1fe1b210bd0090da379e6225"
    )
    assert bundle["stored_column_status"] == "UNUSABLE"
    assert "spread_pins_bps" not in bundle
    assert not hasattr(evaluation, "load_chapter05_cost_pins")
    assert not hasattr(evaluation, "CHAPTER05_SPREAD_PINS_BPS")


def test_chapter05_quarantine_verifier_rejects_tampered_artifact(tmp_path) -> None:
    verify_quarantine = evaluation.verify_chapter05_spread_quarantine
    source = evaluation.CHAPTER05_INFR017_COLUMN_PINS
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["summary"]["BTCUSDT"]["flip_median_bps"] = 99.0
    tampered = tmp_path / "column_pins.json"
    tampered.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="pin_sha256"):
        verify_quarantine(tampered)


@pytest.mark.parametrize("source_column", ["SpreadBps", "spread_feature"])
def test_signed_bar_access_quarantines_mean_price_skew(source_column: str) -> None:
    assert importlib.util.find_spec("xen.sigbar.access") is not None
    access = importlib.import_module("xen.sigbar.access")
    frame = pl.DataFrame({source_column: [-0.25, 0.50], "Volume": [10.0, 20.0]})

    exposed = access.quarantine_mean_price_skew(frame)

    assert source_column in frame.columns
    assert source_column not in exposed.columns
    assert exposed["MeanPriceSkewBps"].to_list() == [-0.25, 0.50]
    assert exposed["MeanPriceSkewStatus"].to_list() == [
        "UNUSABLE_AS_SPREAD",
        "UNUSABLE_AS_SPREAD",
    ]


def test_signed_bar_public_api_exposes_only_the_quarantined_access_name() -> None:
    assert sigbar.quarantine_mean_price_skew is not None
    assert sigbar.MEAN_PRICE_SKEW_COLUMN == "MeanPriceSkewBps"
    assert sigbar.UNUSABLE_AS_SPREAD == "UNUSABLE_AS_SPREAD"


def test_signed_bar_storage_contract_remains_byte_compatible() -> None:
    assert SIGBAR_PIPELINE_VERSION == "sigbar-0.1.0"
    assert SPREAD_UNUSABLE == "UNUSABLE"


def test_chapter05_unresolved_spread_route_is_parked_without_t2_rescue() -> None:
    route = evaluation.spread_scale_route(
        gross_edge_bps=1.0,
        rt_spread_bps=0.5,
        secondary_available=False,
    )

    assert route["t1_undecidable"] is True
    assert route["route"] == "PARKED_T1_UNRESOLVED"
    assert "T2" not in route["note"]


@pytest.mark.parametrize(
    ("relative_path", "forbidden"),
    [
        ("docs/references/xena-lane.md", "per-symbol pseudo-quote spread"),
        ("docs/knowledge-base/evaluation-framework.md", "Until the cost path rejects"),
        (
            ".claude/skills/research-pipeline/_pipeline-config.md",
            "1m OHLCV from Bybit trades + pseudo-quote spreads",
        ),
        (
            ".claude/skills/quant-designer/references/design-requirements.md",
            "from pseudo-quote series via xen.evaluation.t1_round_trip_spread_bps",
        ),
        (".claude/skills/qa-compliance/SKILL.md", "pseudo-quote spread + funding"),
        ("docs/references/architecture.md", "MBP secondary; BTC/ETH/SOL; collection deferred"),
        ("docs/signal-registry/candidate-families/cf-sigauc-001.md", "per-symbol measured pin from the T1 pseudo-quote series"),
        ("docs/references/xena-lane.md", "audited executable-spread"),
        ("docs/knowledge-base/families-explored.md", "audited executable spread pins"),
        ("docs/signal-registry/candidate-families/cf-sigauc-001.md", "measured spread RT"),
        ("docs/signal-registry/candidate-families/cf-sigauc-001.md", "fees + measured spread + funding"),
        ("docs/knowledge-base/pitfalls-ledger.md", "audited quote/execution pins"),
        ("docs/knowledge-base/lessons-and-amendments.md", "audited executable pins"),
        ("docs/knowledge-base/memory/spreadbps-unusable.md", "audited executable"),
    ],
)
def test_live_governance_has_no_obsolete_pseudo_spread_route(
    relative_path: str,
    forbidden: str,
) -> None:
    text = (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")
    assert forbidden not in text


@pytest.mark.parametrize(
    "relative_path",
    [
        "docs/references/chapter-05-cost-data-preflight.md",
        "docs/references/architecture.md",
        "docs/references/dataset-reference.md",
        "docs/knowledge-base/evaluation-framework.md",
        "docs/knowledge-base/memory/chapter05-entry-gate.md",
        ".claude/skills/quant-designer/references/design-requirements.md",
        ".claude/skills/qa-compliance/SKILL.md",
        "python/src/xen/evaluation.py",
    ],
)
def test_live_cost_guidance_discloses_missing_spread(relative_path: str) -> None:
    text = (PROJECT_ROOT / relative_path).read_text(encoding="utf-8").lower()
    assert "spread cost unavailable" in text
    assert "not charged" in text
    assert "understates" in text
    assert "load_chapter05_cost_pins" not in text


def test_chapter05_entry_memory_records_pass_without_authorising_registration() -> None:
    text = (
        PROJECT_ROOT / "docs/knowledge-base/memory/chapter05-entry-gate.md"
    ).read_text(encoding="utf-8")

    assert "Status: PREFLIGHT_PASSED_AWAITING_FAMILY_REGISTRATION" in text
    assert "family registration requires separate operator authorisation" in text
    assert "no outcome exists" in text
    assert "COST_AMENDMENT_QA_PENDING" not in text
    assert "If QA approves" not in text
