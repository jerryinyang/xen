

def test_cost_map_refuses_a_universe_declaring_spread_in_scope() -> None:
    """One universe may not mix cost conventions (programme-wide no-spread policy)."""
    from xen.xena.economics import check_cost_map_integrity, is_valid_cost_scope

    assert is_valid_cost_scope(None)  # undeclared stays loadable
    assert is_valid_cost_scope("PARTIAL_FEES_FUNDING_ONLY")
    assert not is_valid_cost_scope("FULL_DECLARED_COMPONENTS")

    good = [{"candidate_id": "c1", "symbol": "BTCUSDT", "cost_bps": 12.0,
             "money_per_unit": 1.0, "cost_scope": "PARTIAL_FEES_FUNDING_ONLY"}]
    assert check_cost_map_integrity(good).complete

    bad = [{"candidate_id": "c2", "symbol": "BTCUSDT", "cost_bps": 17.0,
            "money_per_unit": 1.0, "cost_scope": "FULL_DECLARED_COMPONENTS"}]
    status = check_cost_map_integrity(bad)
    assert not status.complete
    assert "cost_scope_charges_spread" in status.incomplete[0]["reasons"]
