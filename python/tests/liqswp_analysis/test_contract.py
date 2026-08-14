from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from xen.liqswp_analysis.contract import (
    AnalysisResult,
    IntegrityStatus,
    ZERO_COST_DISCLOSURE,
)


EXPECTED_DISCLOSURE = {
    "heading": "ZERO-COST-DISCLOSURE",
    "cost_model": "NO_COST_CHARGED",
    "spread": "not modeled",
    "commissions": "not modeled",
    "swaps/funding": "not modeled",
    "implication": (
        "every figure in this document is gross and cost-free; no spread, commission, "
        "or swap enters any calculation. Realised results would differ (likely worse) "
        "under any real cost schedule."
    ),
    "prohibited_claims": "fully-net, cost-complete, tradable, deployable",
    "lifting": (
        "only an explicit operator directive may introduce a cost model for a scoped "
        "experiment; the directive is recorded in that experiment's design.md."
    ),
}


def test_zero_cost_disclosure_is_canonical_verbatim() -> None:
    assert ZERO_COST_DISCLOSURE == EXPECTED_DISCLOSURE


def test_integrity_status_is_frozen_and_has_no_value_label() -> None:
    status = IntegrityStatus(blocking_pass=False, reasons=("VOID_SINGLETON_GROUP",))
    assert status.to_dict() == {
        "blocking_pass": False,
        "reasons": ["VOID_SINGLETON_GROUP"],
        "evidence": {},
    }
    assert not hasattr(status, "verdict")
    assert not hasattr(status, "label")
    with pytest.raises(FrozenInstanceError):
        status.blocking_pass = True  # type: ignore[misc]


def test_analysis_result_keeps_void_reason_and_suppresses_value_rows() -> None:
    result = AnalysisResult(
        experiment="EXP-101",
        source={"band": "TRAIN"},
        population={"rows": 2},
        integrity=IntegrityStatus(False, ("VOID_SINGLETON_GROUP",)),
        value_rows=({"observed": 1.0},),
    )
    payload = result.to_dict()
    assert payload["integrity"]["reasons"] == ["VOID_SINGLETON_GROUP"]
    assert payload["value_rows"] == []
    assert payload["zero_cost_disclosure"] == EXPECTED_DISCLOSURE
