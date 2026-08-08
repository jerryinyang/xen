"""INFR-022 zero-cost compliance tests for xen.xena.economics (§3.3)."""

from __future__ import annotations

from xen.xena.economics import (
    NO_COST_CHARGED,
    ZERO_COST_MODEL,
    check_cost_map_integrity,
    check_zero_cost_compliance,
    is_zero_cost_compliant,
)


def test_zero_cost_pin_is_compliant() -> None:
    """INFR-022 §3.3: cost_bps == 0 is a COMPLIANT zero-cost pin (the old
    placeholder-zero refusal is gone)."""
    assert is_zero_cost_compliant(0.0)[0]
    assert is_zero_cost_compliant(0)[0]
    assert not is_zero_cost_compliant(1.5)[0]


def test_missing_cost_allowed_only_under_zero_cost_model() -> None:
    assert is_zero_cost_compliant(None)[0] is False
    assert is_zero_cost_compliant(None, cost_model=NO_COST_CHARGED)[0]
    assert is_zero_cost_compliant(None, cost_scope=ZERO_COST_MODEL)[0]
    assert is_zero_cost_compliant(None, cost_scope="PARTIAL_FEES_FUNDING_ONLY")[0] is False


def test_non_finite_cost_refused() -> None:
    assert is_zero_cost_compliant(float("nan"))[0] is False
    assert is_zero_cost_compliant(float("inf"))[0] is False


def test_nonzero_without_directive_refused() -> None:
    ok, reason = is_zero_cost_compliant(2.0)
    assert not ok and reason == "non_zero_cost_bps_without_directive"
    ok, reason = is_zero_cost_compliant(2.0, has_directive=True)
    assert ok and reason is None


def test_cost_scope_charges_costs_refused_without_directive() -> None:
    assert is_zero_cost_compliant(0.0, cost_scope="PARTIAL_FEES_FUNDING_ONLY")[0] is False
    assert is_zero_cost_compliant(
        0.0, cost_scope="PARTIAL_FEES_FUNDING_ONLY", has_directive=True)[0]
    assert is_zero_cost_compliant(0.0, cost_scope=NO_COST_CHARGED)[0]
    assert is_zero_cost_compliant(0.0, cost_model=ZERO_COST_MODEL)[0]


def test_check_zero_cost_compliance_zero_pins_complete() -> None:
    cands = [
        {"candidate_id": "a", "symbol": "USTEC", "cost_bps": 0.0, "money_per_unit": 1.0},
        {"candidate_id": "b", "symbol": "EURUSD", "cost_bps": 0.0, "money_per_unit": 1.0},
    ]
    st = check_zero_cost_compliance(cands)
    assert st.complete
    assert st.cost_model == NO_COST_CHARGED
    assert st.reason == "ok"


def test_check_zero_cost_compliance_nonzero_blocks_without_directive() -> None:
    cands = [
        {"candidate_id": "a", "symbol": "USTEC", "cost_bps": 0.0, "money_per_unit": 1.0},
        {"candidate_id": "b", "symbol": "EURUSD", "cost_bps": 2.0, "money_per_unit": 1.0},
    ]
    st = check_cost_map_integrity(cands)  # alias must behave identically
    assert not st.complete
    assert st.n_incomplete == 1
    assert st.incomplete[0]["reasons"] == ["non_zero_cost_bps_without_directive"]
    assert st.reason == "INTEGRITY_INCOMPLETE"


def test_check_zero_cost_compliance_directive_legitimizes_costs() -> None:
    cands = [
        {"candidate_id": "a", "symbol": "USTEC", "cost_bps": 2.0, "money_per_unit": 1.0,
         "cost_scope": "PARTIAL_FEES_FUNDING_ONLY"},
    ]
    directive = {"reason": "operator scoped cost experiment EXP-XXX (design §6)",
                 "scope": "EXP-XXX"}
    st = check_zero_cost_compliance(cands, operator_cost_directive=directive)
    assert st.complete
    assert st.cost_model == "DIRECTIVE_BACKED"


def test_invalid_money_per_unit_still_blocks() -> None:
    cands = [
        {"candidate_id": "a", "symbol": "USTEC", "cost_bps": 0.0, "money_per_unit": 0.0},
    ]
    st = check_zero_cost_compliance(cands)
    assert not st.complete
    assert st.incomplete[0]["reasons"] == ["invalid_money_per_unit"]


def test_empty_universe_incomplete() -> None:
    st = check_zero_cost_compliance([])
    assert not st.complete
    assert st.reason == "empty_universe"
