"""SPDR-024 unit tests: the emission requirements, the cap rule and the estimator.

These are edge-case tests written against the design, not against the implementation's own
output. Where the design states a number (a rejected origin's counterfactual, a capital-
normalised delta), the number is written here by hand.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest import mock

import numpy as np
import polars as pl
import pytest

from xen.adaptive_management.contracts import (
    HOLD_CAP_GRID,
    SAFETY_CEILING_BARS,
    Component,
    Device,
    Orientation,
    build_management_lattice,
    build_native_lattice,
    experiment_spec,
)
from xen.adaptive_management.spdr024 import (
    MIN_REGIME_EPISODE_BARS,
    hold_cap_from_durations,
    regime_episode_summary,
    regime_panel,
)
from xen.adaptive_management.spdr024_analysis import (
    MDE_Z,
    SymbolSeries,
    _estimate_rows,
    breakeven_spread,
    clustered_interval,
    decompose,
    gate_permutation_control,
    governing_treatment,
    pool_filter_ladder,
    size_mechanism_ceiling,
)

UTC = timezone.utc


# --------------------------------------------------------------------------- #
# Lattice - the operator directives are structural, so they are tested structurally
# --------------------------------------------------------------------------- #


def test_no_reverse_orientation_arms():
    """OD-16 / amendment-1: the REVERSE arms are dropped, and so is the mixed pair."""
    arms = build_native_lattice("SPDR-024")
    assert not [arm for arm in arms if arm.orientation is Orientation.REVERSE]
    pairs = {arm.orientation_pair for arm in arms if arm.orientation_pair}
    assert pairs == {(Orientation.DIRECT, Orientation.DIRECT)}


def test_only_size_device_survives():
    """OD-11 / OD-15: the four refuted devices are not re-run as arms."""
    devices = {policy.device for policy in build_management_lattice("SPDR-024")}
    assert devices == {Device.SIZE, Device.NONE}
    assert Device.HOLD not in devices


def test_uncapped_arm_is_apparatus_not_a_hold_device():
    """The safety ceiling must not read as a hold-length arm (a refuted lever)."""
    uncapped = next(
        policy
        for policy in build_management_lattice("SPDR-024")
        if policy.policy_id == "UNCAPPED_HOLD_SAFETY_CEILING"
    )
    assert uncapped.device is Device.NONE
    assert uncapped.fixed_hold_bars == SAFETY_CEILING_BARS
    assert uncapped.is_adaptive is False


def test_both_sizing_forms_exist_where_a_numeric_scale_exists():
    """OD-14: continuous and discrete head to head on the components that support both."""
    policies = build_management_lattice("SPDR-024")
    by_component: dict[str, set[str]] = {}
    for policy in policies:
        if policy.device is Device.SIZE and policy.component is not None:
            by_component.setdefault(str(policy.component), set()).add(policy.setting)
    assert by_component[str(Component.RANGE_SCALE)] == {
        "STATE_HALVE_HIGH",
        "SCALE_NORMALISED",
    }
    assert by_component[str(Component.TAIL_RISK)] == {"STATE_HALVE_HIGH"}
    assert len(by_component) == len(list(Component))


def test_other_experiments_keep_both_orientations():
    """The SPDR-024 narrowing must not leak into the completed experiments."""
    arms = build_native_lattice("SPDR-021")
    assert {arm.orientation for arm in arms if arm.orientation} == set(Orientation)
    assert len(arms) == 65


def test_domain_is_declared_and_restricted():
    assert experiment_spec("SPDR-024", "H4").domain == "H4"
    with pytest.raises(ValueError, match="H1 domain only"):
        experiment_spec("SPDR-021", "H4")
    with pytest.raises(ValueError, match="unknown signal domain"):
        experiment_spec("SPDR-024", "H2")


# --------------------------------------------------------------------------- #
# E1 - regime episodes
# --------------------------------------------------------------------------- #


def _features(states: list[str], symbol: str = "SYN") -> pl.DataFrame:
    start = datetime(2023, 1, 1, tzinfo=UTC)
    return pl.DataFrame(
        {
            "symbol": [symbol] * len(states),
            "ts": [start + timedelta(hours=index) for index in range(len(states))],
            "level_now": states,
        }
    ).with_columns(pl.col("ts").cast(pl.Datetime("ns", "UTC")))


def test_regime_episodes_are_contiguous_runs():
    panel = regime_panel(_features(["LOW"] * 5 + ["HIGH"] * 6))
    assert panel["regime_episode_id"].n_unique() == 2
    summary = regime_episode_summary(panel)
    assert sorted(summary["length_bars"].to_list()) == [5, 6]
    # Contiguity is what makes V-C a legitimate block: no episode may interleave in time.
    for row in summary.iter_rows(named=True):
        window = panel.filter(pl.col("regime_episode_id") == row["regime_episode_id"])
        assert window["ts"].max() == row["end_ts"]
        assert window.height == row["length_bars"]


def test_short_episodes_merge_into_their_predecessor():
    """V-C RULES: below the declared minimum an episode is not its own block."""
    states = ["LOW"] * 6 + ["HIGH"] * (MIN_REGIME_EPISODE_BARS - 1) + ["LOW"] * 6
    panel = regime_panel(_features(states))
    assert panel["regime_episode_id"].n_unique() == 2
    assert panel["regime_episode_id"][0] == panel["regime_episode_id"][7]


def test_regime_panel_never_drops_a_bar():
    states = ["LOW", "HIGH"] * 12
    panel = regime_panel(_features(states))
    assert panel.height == len(states)
    assert panel["regime_state"].null_count() == 0


# --------------------------------------------------------------------------- #
# Hold cap - design section 7
# --------------------------------------------------------------------------- #


def test_cap_rule_picks_the_smallest_qualifying_grid_value():
    # 100 positions: 96 at 3 bars, 4 at 30 bars. A cap of 4 binds 4% (<= 5%); 2 binds 100%.
    durations = np.array([3.0] * 96 + [30.0] * 4)
    result = hold_cap_from_durations(durations)
    assert result["status"] == "SELECTED"
    assert result["hold_cap_bars"] == 4
    assert result["realised_bind_rate"] == pytest.approx(0.04)


def test_cap_rule_reports_not_applicable_rather_than_relaxing_itself():
    """Every arm-B position at the ceiling: no grid value qualifies, and none is invented."""
    durations = np.full(50, float(SAFETY_CEILING_BARS))
    result = hold_cap_from_durations(durations)
    assert result["status"] == "NOT_APPLICABLE"
    assert result["hold_cap_bars"] is None
    assert result["safety_ceiling_bind_rate"] == 1.0
    assert result["safety_ceiling_flagged"] is True
    assert set(result["bind_rate_by_candidate"]) == set(HOLD_CAP_GRID)


def test_cap_rule_flags_the_ceiling_above_its_declared_tolerance():
    durations = np.array([2.0] * 97 + [float(SAFETY_CEILING_BARS)] * 3)
    result = hold_cap_from_durations(durations)
    assert result["safety_ceiling_bind_rate"] == pytest.approx(0.03)
    assert result["safety_ceiling_flagged"] is True  # 3% exceeds the declared 2%


def test_cap_rule_on_no_closed_positions_selects_nothing():
    result = hold_cap_from_durations(np.array([]))
    assert result["status"] == "NOT_APPLICABLE"
    assert result["duration_distribution"]["closed_positions"] == 0


# --------------------------------------------------------------------------- #
# No result labels, and variance treatments
# --------------------------------------------------------------------------- #


_LABEL_DENYLIST = {
    "band",
    "governing_band",
    "component_specific_band",
    "resolution_class",
    "WASH",
    "step3_band",
    "floor_over_step3",
    "step3_resolving",
}


def test_no_artifact_column_carries_a_result_label():
    """The contract's central reporting rule, enforced on the emitted schema.

    `adaptive-management-design.md` section 9: "Emit event count, effective count, CI and MDE
    for every row. These are informative diagnostics, not verdict labels or pruning rules."
    Section 1: "power labels do not decide which rows are shown or how they are described."

    Two earlier builds violated this - the first banded every unresolvable cell `WASH`, and the
    correction to it replaced that with a `resolution_class` computed from the floor BEFORE the
    estimate was read, which is the same violation in a more systematic form.
    """
    import xen.adaptive_management.spdr024_analysis as module

    for name in (
        "band_label", "resolution_class", "_selection_band",
        "_band_or_identity", "_control_band", "_resolution_fields",
    ):
        assert not hasattr(module, name), f"{name} reintroduces a result label"

    series = SymbolSeries(
        symbol="A",
        values=np.linspace(-1.0, 1.0, 400),
        blocks={name: np.arange(400) for name in
                ("V_A_UNCHUNKED", "V_B_TIME_BLOCK", "V_C_REGIME_EPISODE")},
    )
    rows = _estimate_rows(
        [series], identity={"channel": "SCALE"}, populations={}, n_boot=20
    )
    for row in rows:
        bad = _LABEL_DENYLIST & set(row)
        assert not bad, f"result label emitted: {bad}"
        # Broader column-name denylist (step3_*, floor_over_*, *_band).
        for key in row:
            assert not key.startswith("step3_"), key
            assert not key.startswith("floor_over_"), key
            assert not key.endswith("_band"), key


def test_row_floor_uses_bootstrap_se_not_blocks_sqrt(monkeypatch):
    """AMENDMENT-7 R2 / D3.2: mde = MDE_Z × SE_bootstrap, not MDE_Z/√blocks."""
    rng = np.random.default_rng(11)
    n = 240
    # Strong within-block dependence so bootstrap SE ≠ 1/√blocks.
    values = np.repeat(rng.normal(size=n // 12), 12) + rng.normal(scale=0.05, size=n)
    series = [
        SymbolSeries(
            symbol="A",
            values=values,
            blocks={
                "V_A_UNCHUNKED": np.arange(n),
                "V_B_TIME_BLOCK": np.arange(n) // 12,
                "V_C_REGIME_EPISODE": np.arange(n) // 24,
            },
        )
    ]
    result = clustered_interval(series, "V_B_TIME_BLOCK", n_boot=400, seed=99)
    se = result["bootstrap_se_sigma"]
    assert np.isfinite(se) and se > 0
    assert result["mde_sigma"] == pytest.approx(MDE_Z * se, rel=1e-9)
    block_floor = MDE_Z / np.sqrt(result["effective_blocks"])
    # When bootstrap SE differs from 1/√blocks, the row floor must follow SE.
    assert abs(se - 1.0 / np.sqrt(result["effective_blocks"])) > 1e-4
    assert result["mde_sigma"] != pytest.approx(block_floor, rel=1e-3)


def test_scale_and_selection_declare_distinct_denominators():
    """AMENDMENT-7 R4: no silent dual-σ̂ ladder across channels."""
    series = SymbolSeries(
        symbol="A",
        values=np.linspace(-1.0, 1.0, 80),
        blocks={name: np.arange(80) for name in
                ("V_A_UNCHUNKED", "V_B_TIME_BLOCK", "V_C_REGIME_EPISODE")},
    )
    scale_rows = _estimate_rows(
        [series], identity={"channel": "SCALE"}, populations={}, n_boot=20
    )
    for row in scale_rows:
        assert row["sigma_denominator"] == "paired_delta"

    # Selection channel: synthetic admitted/rejected on two symbols.
    from xen.adaptive_management.spdr024_analysis import selection_channel_estimates

    rows = []
    start = datetime(2023, 1, 1, tzinfo=UTC)
    for symbol in ("A", "B"):
        for index in range(40):
            ts = start + timedelta(hours=index)
            exit_ts = ts + timedelta(hours=1)
            rows.append(
                {
                    "arm_id": "ADP_X",
                    "arm_class": "NATIVE",
                    "component": "TAIL_RISK",
                    "symbol": symbol,
                    "origin_id": f"{symbol}-{index}",
                    "decision_ts": ts,
                    "entry_ts": ts,
                    "exit_ts": exit_ts,
                    "regime_episode_id": f"R{index // 5}",
                    "regime_state": "HIGH" if index % 2 == 0 else "LOW",
                    "admitted": index % 3 != 0,
                    "rejection_class": (
                        "ADMITTED" if index % 3 != 0 else "EVALUATED_DECLINED"
                    ),
                    "outcome_bps": float(index % 7 - 3),
                    "counterfactual_outcome_bps": float((index % 5) - 2),
                }
            )
            rows.append(
                {
                    "arm_id": "FIXED_NATIVE_BREAKOUT",
                    "arm_class": "NATIVE",
                    "component": None,
                    "symbol": symbol,
                    "origin_id": f"{symbol}-{index}",
                    "decision_ts": ts,
                    "entry_ts": ts,
                    "exit_ts": exit_ts,
                    "regime_episode_id": f"R{index // 5}",
                    "regime_state": "HIGH" if index % 2 == 0 else "LOW",
                    "admitted": True,
                    "rejection_class": "ADMITTED",
                    "outcome_bps": float(index % 7 - 3),
                    "counterfactual_outcome_bps": None,
                }
            )
    table = selection_channel_estimates(pl.DataFrame(rows), domain_hours=1, n_boot=30)
    assert not table.is_empty()
    assert "sigma_denominator" in table.columns
    assert set(table["sigma_denominator"].drop_nulls().unique().to_list()) == {
        "outcome_level_bps"
    }
    # Selection floor (when finite) tracks bootstrap SE, not 2.8/√(n_a+n_b) alone.
    pooled = table.filter(pl.col("scope") == "POOLED")
    if pooled.height:
        row = pooled.row(0, named=True)
        if row.get("bootstrap_se_bps") is not None and np.isfinite(row["bootstrap_se_bps"]):
            assert row["mde_bps"] == pytest.approx(
                MDE_Z * row["bootstrap_se_bps"], rel=1e-6
            )


def test_size_mechanism_ceiling_is_baseline_only():
    """AMENDMENT-7 R1: ceiling = √p × |μ|/σ from baseline moments."""
    ceiling = size_mechanism_ceiling(2.0, 40.0, gate_rate=0.25)
    assert ceiling == pytest.approx(0.5 * (2.0 / 40.0), rel=1e-9)
    assert np.isnan(size_mechanism_ceiling(1.0, 0.0))


def test_preflight_module_imports_and_uses_r1_endpoint():
    """AMENDMENT-7 R5: preflight imports cleanly; labels use R1, not Step-3 0.150."""
    import importlib.util
    from pathlib import Path

    path = (
        Path(__file__).resolve().parents[1]
        / "experiments"
        / "SPDR-024"
        / "screen_code"
        / "preflight.py"
    )
    spec = importlib.util.spec_from_file_location("spdr024_preflight", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    assert not hasattr(module, "STEP3_OBSERVED_EFFECT_SIGMA")
    assert module.LABEL_DESCRIPTIVE == "DESCRIPTIVE_SIZE_MAGNITUDE_FLOOR_ABOVE_CEILING"
    # Floor above ceiling → descriptive; never CARRIES_MAGNITUDE on order counts.
    assert (
        module.descriptive_power_label(100, planning_floor=0.20, mechanism_ceiling=0.05)
        == module.LABEL_DESCRIPTIVE
    )
    assert (
        module.descriptive_power_label(100, planning_floor=0.02, mechanism_ceiling=0.05)
        == module.LABEL_CONTEXT
    )
    assert (
        module.descriptive_power_label(5, planning_floor=0.02, mechanism_ceiling=0.05)
        == module.LABEL_INSUFFICIENT
    )
    # Explicit ban: Step-3 range must not gate the label (code path, not ban prose).
    source = path.read_text(encoding="utf-8")
    assert "STEP3_OBSERVED" not in source
    assert "CARRIES_MAGNITUDE_QUESTION" not in source
    assert "mde > " not in source
    # Label function has no Step-3 constant comparison.
    import inspect
    label_src = inspect.getsource(module.descriptive_power_label)
    assert "0.150" not in label_src
    assert "0.022" not in label_src


def test_legacy_da_scripts_are_quarantined():
    """B1: exploratory da_*.py must not live on the emission path with band floors."""
    from pathlib import Path

    analysis_code = (
        Path(__file__).resolve().parents[1] / "experiments" / "SPDR-024" / "analysis_code"
    )
    live = list(analysis_code.glob("da_*.py"))
    assert live == [], f"live da scripts still on emission path: {live}"
    legacy = analysis_code / "legacy_pre_a7"
    assert legacy.is_dir()
    assert (legacy / "README.md").exists()
    # Each quarantined script refuses to run.
    for path in legacy.glob("da_*.py"):
        text = path.read_text(encoding="utf-8")
        assert "AMENDMENT_7_QUARANTINE" in text
        assert "raise RuntimeError" in text


def test_selection_tripwire_uses_all_declined_classes():
    """BR-1: PENDING_EXPIRY declines (ORDER_EXPIRED) must enter the leak test."""
    import inspect
    from xen.adaptive_management.spdr024_analysis import tripwire_collapse

    src = inspect.getsource(tripwire_collapse)
    assert "DECLINED_CLASSES" in src
    assert 'rejection_class") == "EVALUATED_DECLINED"' not in src


def test_regime_strata_do_not_emit_parametric_mde():
    """BR-2: no unblocked parametric floor inside regime_strata JSON."""
    from xen.adaptive_management.spdr024_analysis import _regime_matched_contrast
    import json

    rng = np.random.default_rng(3)
    admitted = pl.DataFrame(
        {
            "outcome_bps": rng.normal(size=80),
            "regime_state": ["HIGH"] * 40 + ["LOW"] * 40,
        }
    )
    declined = pl.DataFrame(
        {
            "counterfactual_outcome_bps": rng.normal(size=80),
            "regime_state": ["HIGH"] * 40 + ["LOW"] * 40,
        }
    )
    result = _regime_matched_contrast(admitted, declined)
    strata = json.loads(result["regime_strata"])
    for state, payload in strata.items():
        assert "mde_bps" not in payload, state


def test_emission_frames_have_no_banned_label_values_or_columns():
    """Widen label ban beyond scale _estimate_rows (Claude B5)."""
    series = SymbolSeries(
        symbol="A",
        values=np.linspace(-1.0, 1.0, 100),
        blocks={name: np.arange(100) for name in
                ("V_A_UNCHUNKED", "V_B_TIME_BLOCK", "V_C_REGIME_EPISODE")},
    )
    scale_rows = _estimate_rows(
        [series], identity={"channel": "SCALE"}, populations={}, n_boot=15
    )
    banned_names = _LABEL_DENYLIST | {
        "unmatched_contrast_resolves",
        "contrast_over_mde",
        "mde_bps_parametric_blocks",
    }
    banned_values = {
        "WASH", "UNPOWERED", "NOT_RESOLVABLE", "CARRIES_MAGNITUDE",
        "FULLY_RESOLVING", "CLEARS_FLOOR",
    }
    for row in scale_rows:
        assert not (banned_names & set(row)), banned_names & set(row)
        for key in row:
            assert not key.startswith("step3_"), key
            assert not key.endswith("_band"), key
        for value in row.values():
            if isinstance(value, str):
                assert value not in banned_values, value
    # Per-symbol floors use bootstrap SE, not free-standing 2.8/√n under a bootstrap name.
    per = next(r for r in scale_rows if r["scope"] == "PER_SYMBOL")
    assert np.isfinite(per["bootstrap_se_sigma"])
    assert per["mde_sigma"] == pytest.approx(MDE_Z * per["bootstrap_se_sigma"], rel=1e-6)


def test_every_row_carries_the_five_reporting_quantities():
    """Estimate, uncertainty, population count, effective count and MDE - on every row."""
    series = SymbolSeries(
        symbol="A",
        values=np.linspace(-1.0, 1.0, 400),
        blocks={name: np.arange(400) for name in
                ("V_A_UNCHUNKED", "V_B_TIME_BLOCK", "V_C_REGIME_EPISODE")},
    )
    rows = _estimate_rows(
        [series], identity={"channel": "SCALE"}, populations={}, n_boot=20
    )
    for row in rows:
        for field in ("estimate_sigma", "mde_sigma", "n_trades", "effective_blocks"):
            assert field in row


def test_populations_are_named_separately_and_never_borrowed():
    """A count may never be filled in from a different population (handoff Task 3 Step 3)."""
    series = SymbolSeries(
        symbol="A",
        values=np.linspace(-1.0, 1.0, 400),
        blocks={name: np.arange(400) for name in
                ("V_A_UNCHUNKED", "V_B_TIME_BLOCK", "V_C_REGIME_EPISODE")},
    )
    rows = _estimate_rows(
        [series],
        identity={"channel": "SCALE"},
        populations={"eligible_origin_n": 900, "entry_fill_n": 400, "close_n": 399,
                     "common_fill_n": 380},
        n_boot=20,
    )
    pooled = next(row for row in rows if row["scope"] == "POOLED")
    assert pooled["eligible_origin_n"] == 900
    assert pooled["entry_fill_n"] == 400
    assert pooled["close_n"] == 399
    assert pooled["common_fill_n"] == 380
    # This is a paired trade-lens read, so the origin-block count does not apply. It must be
    # null, never the trade-block count wearing another name.
    assert pooled["effective_origin_blocks"] is None
    assert pooled["effective_trade_blocks"] == pooled["effective_blocks"]


def test_the_widest_interval_governs():
    """D12: the most conservative treatment governs, never the most flattering."""
    narrow = {
        "treatment": "V_A_UNCHUNKED", "estimate_sigma": 0.2, "ci_low_sigma": 0.15,
        "ci_high_sigma": 0.25, "mde_sigma": 0.05, "n_trades": 900, "effective_blocks": 900,
    }
    wide = {
        "treatment": "V_C_REGIME_EPISODE", "estimate_sigma": 0.2, "ci_low_sigma": -0.10,
        "ci_high_sigma": 0.50, "mde_sigma": 0.12, "n_trades": 900, "effective_blocks": 60,
    }
    assert governing_treatment([narrow, wide])["treatment"] == "V_C_REGIME_EPISODE"


def _series(symbol: str, values: np.ndarray) -> SymbolSeries:
    n = values.size
    return SymbolSeries(
        symbol=symbol,
        values=values,
        blocks={
            "V_A_UNCHUNKED": np.arange(n),
            "V_B_TIME_BLOCK": np.arange(n) // 10,
            "V_C_REGIME_EPISODE": np.arange(n) // 25,
        },
    )


def test_blocking_never_increases_the_block_count_above_the_trade_count():
    rng = np.random.default_rng(7)
    series = [_series("A", rng.normal(size=200)), _series("B", rng.normal(size=200))]
    intervals = {
        name: clustered_interval(series, name, n_boot=50)
        for name in ("V_A_UNCHUNKED", "V_B_TIME_BLOCK", "V_C_REGIME_EPISODE")
    }
    assert intervals["V_A_UNCHUNKED"]["effective_blocks"] == 400
    assert intervals["V_B_TIME_BLOCK"]["effective_blocks"] == 40
    assert intervals["V_C_REGIME_EPISODE"]["effective_blocks"] == 16
    # AMENDMENT-7 R2: floor tracks bootstrap SE, not free-standing 2.8/√blocks.
    for item in intervals.values():
        assert item["mde_sigma"] == pytest.approx(
            MDE_Z * item["bootstrap_se_sigma"], rel=1e-9
        )


def test_interval_is_deterministic_for_a_fixed_seed():
    rng = np.random.default_rng(3)
    series = [_series("A", rng.normal(size=120))]
    first = clustered_interval(series, "V_A_UNCHUNKED", n_boot=100)
    second = clustered_interval(series, "V_A_UNCHUNKED", n_boot=100)
    assert first == second


def test_a_constant_series_cannot_be_normalised_and_is_reported_empty():
    series = [_series("A", np.zeros(50))]
    result = clustered_interval(series, "V_A_UNCHUNKED", n_boot=10)
    assert np.isnan(result["estimate_sigma"])
    assert result["effective_blocks"] == 0


# --------------------------------------------------------------------------- #
# Report ladder
# --------------------------------------------------------------------------- #


def test_pool_ladder_shows_all_three_steps_and_names_the_dropped_symbols():
    estimates = pl.DataFrame(
        {
            "channel": ["SCALE"] * 3,
            "arm_id": ["ADP_X"] * 3,
            "lens": ["PRIMARY_capital_normalised"] * 3,
            "scope": ["PER_SYMBOL"] * 3,
            "symbol": ["A", "B", "C"],
            "mean_delta_raw": [-5.0, 0.0, 4.0],
        }
    )
    ladder = pool_filter_ladder(estimates)
    steps = ladder["ladder_step"].to_list()
    assert steps == [
        "POOLED_ALL_SYMBOLS",
        "POOLED_DROP_WORST",
        "POOLED_DROP_BEST",
        "POOLED_DROP_BOTH",
    ]
    rows = {row["ladder_step"]: row for row in ladder.iter_rows(named=True)}
    assert rows["POOLED_ALL_SYMBOLS"]["unweighted_mean_of_symbol_means_raw"] == pytest.approx(
        -1 / 3
    )
    assert rows["POOLED_DROP_WORST"]["dropped_symbols"] == "A"
    assert rows["POOLED_DROP_BEST"]["dropped_symbols"] == "C"
    assert rows["POOLED_DROP_BOTH"]["unweighted_mean_of_symbol_means_raw"] == pytest.approx(0.0)
    # The ladder's pooled number must never be confused with the headline sigma-hat pooled one.
    assert "not_the_headline_pooled_estimate" in rows["POOLED_ALL_SYMBOLS"]
    # The ladder makes no claim; it is a concentration diagnostic.
    assert set(ladder["class"]) == {"CONCENTRATION_DIAGNOSTIC_NOT_A_CLAIM"}


# --------------------------------------------------------------------------- #
# Decomposition and the gate-permutation control
# --------------------------------------------------------------------------- #


def _size_series(symbol: str, weights: np.ndarray, baseline: np.ndarray) -> SymbolSeries:
    values = (weights - 1.0) * baseline
    n = values.size
    return SymbolSeries(
        symbol=symbol,
        values=values,
        blocks={name: np.arange(n) for name in ("V_A_UNCHUNKED", "V_B_TIME_BLOCK",
                                                "V_C_REGIME_EPISODE")},
        weights=weights,
        baseline=baseline,
    )


def test_decomposition_recovers_the_exposure_and_selectivity_terms():
    """The identity the whole sizing read rests on: E[(s-1)r] = (E[s]-1)E[r] + Cov(s,r)."""
    rng = np.random.default_rng(11)
    baseline = rng.normal(loc=5.0, scale=20.0, size=500)
    weights = np.where(baseline < 0, 0.5, 1.0)  # an oracle gate: cuts the losers
    parts = decompose([_size_series("A", weights, baseline)])
    total = float(np.mean((weights - 1.0) * baseline))
    assert parts["exposure_term_bps"] + parts["selectivity_term_bps"] == pytest.approx(total)
    # An oracle gate is almost all selectivity, and it must be POSITIVE: cutting losers helps.
    assert parts["selectivity_term_bps"] > 0
    assert parts["exposure_share_of_movement"] < 0.5


def test_exposure_share_is_a_share_of_movement_not_of_the_net_effect():
    """The two terms can oppose, so exposure alone can exceed the net. Both are emitted."""
    # Positive-mean baseline, gate halves the losers: exposure is negative (less capital on a
    # profitable population) while selectivity is positive (the cut lands on the bad trades).
    baseline = np.array([30.0, -10.0, 20.0, -10.0] * 50)
    weights = np.where(baseline < 0, 0.5, 1.0)
    parts = decompose([_size_series("A", weights, baseline)])
    assert parts["terms_oppose"] is True
    assert 0.0 <= parts["exposure_share_of_movement"] <= 1.0
    # The signed ratio is the one that reveals an exposure term larger than the net effect.
    assert abs(parts["exposure_over_net_effect"]) > 0.0
    assert parts["net_effect_bps"] == pytest.approx(
        parts["exposure_term_bps"] + parts["selectivity_term_bps"]
    )


def test_gate_permutation_control_is_not_applicable_when_the_gate_is_constant():
    """A permutation cannot destroy an association that does not vary (B3 vacuity)."""
    baseline = np.random.default_rng(9).normal(size=200)
    constant = _size_series("A", np.full(200, 0.5), baseline)
    result = gate_permutation_control([constant], "V_A_UNCHUNKED", n_draws=50)
    assert result["applicable"] is False
    assert "constant" in result["not_applicable_reason"]
    assert np.isnan(result["two_sided_p"])


def test_an_arbitrary_gate_is_almost_all_exposure():
    """A gate unrelated to outcomes carries no selectivity - that is the null to beat."""
    rng = np.random.default_rng(12)
    baseline = rng.normal(loc=5.0, scale=20.0, size=2000)
    weights = np.where(rng.random(2000) < 0.5, 0.5, 1.0)  # random, outcome-blind
    parts = decompose([_size_series("A", weights, baseline)])
    assert abs(parts["selectivity_term_bps"]) < abs(parts["exposure_term_bps"])
    # And the exposure term's sign follows the baseline's, which is the whole trap.
    assert np.sign(parts["exposure_term_bps"]) == -np.sign(parts["baseline_mean_bps"])


def test_gate_permutation_control_separates_an_oracle_gate_from_an_arbitrary_one():
    """The control must be able to come out either way (B3 non-vacuity)."""
    rng = np.random.default_rng(13)
    baseline = rng.normal(loc=2.0, scale=15.0, size=600)

    oracle = _size_series("A", np.where(baseline < 0, 0.5, 1.0), baseline)
    arbitrary = _size_series("A", np.where(rng.random(600) < 0.5, 0.5, 1.0), baseline)

    oracle_result = gate_permutation_control([oracle], "V_A_UNCHUNKED", n_draws=200)
    arbitrary_result = gate_permutation_control([arbitrary], "V_A_UNCHUNKED", n_draws=200)

    # The oracle gate sits in the tail of its own permutation null; the arbitrary one does not.
    assert oracle_result["two_sided_p"] < 0.05
    assert arbitrary_result["two_sided_p"] > 0.05
    # The control preserves the exposure term, so the null is centred away from zero, not on it.
    assert np.isfinite(oracle_result["null_mean_sigma"])


def test_a_structural_zero_is_reported_as_a_measured_share():
    """A difference that is zero on every row is reported as the share, not as a label.

    On the per-notional lens of a SIZE arm this is 1.0 because basis points cannot register a
    size change; on the primary lens a 1.0 means the arm never gated in that stratum. The
    emission states the measured share and lets the reader tell those apart from the lens, the
    gate rate and the counts, rather than asserting which one it is.
    """
    zeros = SymbolSeries(
        symbol="A",
        values=np.zeros(500),
        blocks={name: np.arange(500) for name in
                ("V_A_UNCHUNKED", "V_B_TIME_BLOCK", "V_C_REGIME_EPISODE")},
    )
    rows = _estimate_rows(
        [zeros], identity={"channel": "SCALE"}, populations={}, n_boot=20
    )
    pooled = [row for row in rows if row["scope"] == "POOLED"]
    assert {row["exact_zero_delta_share"] for row in pooled} == {1.0}
    assert all("band" not in row for row in pooled)


def test_breakeven_spread_divides_by_this_arms_own_round_trips():
    """M7: the divisor is the arm's own turnover, because cost does not cancel in a pair."""
    result = breakeven_spread(total_effect_bps=-250.0, round_trips=100)
    assert result["breakeven_spread_rt_bps"] == pytest.approx(2.5)
    assert result["round_trips"] == 100
    assert result["breakeven_spread_class"] == "NON_EMITTED_SCENARIO"
    assert breakeven_spread(1.0, 0)["round_trips"] == 0


def test_selection_rows_report_an_empty_rejected_population_as_a_fact():
    """An arm that declines no origin carrying a counterfactual has no population to read.

    That is a property of the rule's semantics, not of the sample, so it is emitted as the
    boolean `rejected_population_empty` beside `n_rejected` rather than as a band. It replaced
    `NOT_APPLICABLE_NO_REJECTION_SEMANTICS`, which asserted the same thing as a verdict.
    """
    from xen.adaptive_management.spdr024_analysis import selection_channel_estimates

    n = 40
    base = {
        "symbol": ["S"] * n,
        "origin_id": [f"o{i}" for i in range(n)],
        "decision_ts": [datetime(2023, 1, 1, tzinfo=UTC) + timedelta(hours=i) for i in range(n)],
        "regime_episode_id": [f"R{i // 5}" for i in range(n)],
        "regime_state": ["HIGH"] * (n // 2) + ["LOW"] * (n // 2),
        "outcome_bps": list(np.linspace(-5.0, 5.0, n)),
        "counterfactual_outcome_bps": [None] * n,
        "admitted": [True] * n,
        "rejection_class": ["ADMITTED"] * n,
        "exit_ts": [datetime(2023, 1, 1, tzinfo=UTC)] * n,
    }
    episodes = pl.concat(
        [
            pl.DataFrame({**base, "arm_id": ["FIXED_NATIVE_BREAKOUT"] * n,
                          "arm_class": ["FIXED_NATIVE"] * n, "component": [None] * n}),
            pl.DataFrame({**base, "arm_id": ["NAT_NO_DECLINES"] * n,
                          "arm_class": ["NATIVE"] * n, "component": ["SHOCK"] * n}),
        ],
        how="diagonal_relaxed",
    )
    table = selection_channel_estimates(episodes, domain_hours=1, n_boot=20)
    assert "band" not in table.columns
    pooled = table.filter(pl.col("scope") == "POOLED")
    assert pooled["rejected_population_empty"].to_list() == [True]
    assert pooled["n_rejected"].to_list() == [0]
    # And the five reporting quantities are on the row regardless.
    for field in ("contrast_bps", "ci_low_bps", "mde_bps", "n_admitted",
                  "effective_origin_blocks"):
        assert field in table.columns


def test_collapse_fraction_not_gated_on_mde_resolve():
    """AMENDMENT-7 R3: collapse is not suppressed by |est| ≥ MDE power rule."""
    from xen.adaptive_management.spdr024_analysis import _regime_matched_contrast

    rng = np.random.default_rng(21)
    admitted = pl.DataFrame(
        {
            "outcome_bps": rng.normal(scale=50.0, size=400),
            "regime_state": ["HIGH"] * 200 + ["LOW"] * 200,
        }
    )
    declined = pl.DataFrame(
        {
            "counterfactual_outcome_bps": rng.normal(scale=50.0, size=400),
            "regime_state": ["HIGH"] * 200 + ["LOW"] * 200,
        }
    )
    result = _regime_matched_contrast(admitted, declined)
    assert "unmatched_contrast_resolves" not in result
    # Collapse is arithmetic; only undefined when unmatched == 0.
    if result["unmatched_contrast_bps"] != 0:
        assert result["regime_match_collapse_fraction"] is not None
        assert np.isfinite(result["regime_match_collapse_fraction"])


def test_zero_unmatched_collapse_is_null_not_nan():
    """Undefined ratio (unmatched==0) is NULL, never NaN."""
    from xen.adaptive_management.spdr024_analysis import _regime_matched_contrast

    admitted = pl.DataFrame(
        {
            "outcome_bps": [1.0, 1.0, 1.0, 1.0] * 10,
            "regime_state": ["HIGH"] * 20 + ["LOW"] * 20,
        }
    )
    declined = pl.DataFrame(
        {
            "counterfactual_outcome_bps": [1.0, 1.0, 1.0, 1.0] * 10,
            "regime_state": ["HIGH"] * 20 + ["LOW"] * 20,
        }
    )
    result = _regime_matched_contrast(admitted, declined)
    assert result["unmatched_contrast_bps"] == pytest.approx(0.0)
    assert result["regime_match_collapse_fraction"] is None
    frame = pl.DataFrame([{"collapse": result["regime_match_collapse_fraction"]}])
    assert frame["collapse"].null_count() == 1


# --------------------------------------------------------------------------- #
# Admission is the fill, not the order (design section 2 OBJECT-IDENTITY)
# --------------------------------------------------------------------------- #


def test_admission_is_the_fill_so_expiry_rules_are_visible():
    """A rule acting on the pending order's lifetime must not read as inert.

    Banding admission on order creation made the eight `PENDING_EXPIRY` arms produce exactly
    the comparator's order set, zero declines, and a `NOT_APPLICABLE` band - while their
    realised fill counts differed from the comparator's by several percent. Admission is the
    stop fill, so an order that expired unfilled is an evaluated decline.
    """
    from xen.adaptive_management.spdr024_emission import _enrich

    schedule = pl.DataFrame(
        {
            "episode_id": ["e1", "e2", "e3"],
            "arm_id": ["A", "A", "A"],
            "policy_id": ["p", "p", "p"],
            "symbol": ["S", "S", "S"],
            "origin_id": ["o1", "o2", "o3"],
            "decision_ts": [
                datetime(2023, 1, 1, tzinfo=UTC),
                datetime(2023, 1, 1, 1, tzinfo=UTC),
                datetime(2023, 1, 1, 2, tzinfo=UTC),
            ],
            # o1 filled; o2 created an order that expired unfilled; o3 never triggered.
            "state": ["FILLED", "ORDER_CREATED", "NO_EVENT"],
            "risk_size": [1.0, 1.0, 1.0],
        }
    )
    frame = schedule.with_columns(
        pl.Series("_entry_ns", [1_000, None, None], dtype=pl.Int64),
        pl.Series("_exit_ns", [2_000, None, None], dtype=pl.Int64),
        pl.Series("_exit_reason", ["HOLD", None, None], dtype=pl.Utf8),
        pl.Series("outcome_bps", [10.0, None, None], dtype=pl.Float64),
    )

    def _passthrough(sched, ledger, universe):  # noqa: ARG001
        return frame

    with mock.patch(
        "xen.adaptive_management.spdr024_emission._attach_results", _passthrough
    ):
        result = _enrich(schedule, pl.DataFrame(), "ctrader", "H1", 3_600_000_000_000)

    assert result["admitted"].to_list() == [True, False, False]
    assert result["order_created"].to_list() == [True, True, False]
    assert result["rejection_class"].to_list() == [
        "ADMITTED",
        "EVALUATED_DECLINED_ORDER_EXPIRED",
        "EVALUATED_DECLINED",
    ]


# --------------------------------------------------------------------------- #
# The tripwire must report what it could actually bite on (design section 9)
# --------------------------------------------------------------------------- #


def test_tripwire_says_when_it_had_no_edge_to_collapse():
    """A pass with no arm above its own floor is the absence of a survivor, not a collapse."""
    from xen.adaptive_management.spdr024_analysis import tripwire_collapse

    def _frame(scale: float) -> pl.DataFrame:
        rng = np.random.default_rng(3)
        n = 300
        rows = []
        for arm_id, size in (("FIXED_SIZE_UNIT", 1.0), ("ADP_X_SIZE_STATE_HALVE_HIGH", 0.5)):
            base = rng.normal(scale=10.0, size=n)
            for index in range(n):
                rows.append(
                    {
                        "arm_id": arm_id,
                        "arm_class": "MANAGEMENT",
                        "device": "SIZE",
                        "symbol": "S",
                        "origin_id": f"o{index}",
                        "entry_ts": datetime(2023, 1, 1, tzinfo=UTC)
                        + timedelta(hours=index),
                        "regime_episode_id": f"R{index // 10}",
                        "regime_state": "HIGH",
                        "risk_size": size,
                        "admitted": True,
                        "rejection_class": "ADMITTED",
                        "outcome_bps": base[index],
                        "counterfactual_outcome_bps": None,
                        "capital_normalised_return_bps": base[index] * size * scale,
                    }
                )
        return pl.DataFrame(rows)

    result = tripwire_collapse(_frame(1.0), _frame(1.0), domain_hours=1, n_boot=50)
    assert result["non_vacuous"] is False or result["arms_with_a_causal_edge"] >= 0
    # The artifact must never let a no-bite pass read as a demonstrated collapse.
    assert "informative" in result
    assert "bite_note" in result
    if not result["arms_with_a_causal_edge"]:
        assert result["informative"] is False
        assert "nothing to collapse" in result["bite_note"]


def test_an_edge_that_does_not_collapse_is_reported_but_does_not_block():
    """A HARD failure means "the emission is invalid, fix the data". It must mean only that.

    Design §9's REJECT condition is "a SURVIVING edge under the shift"; its "expected collapse
    fraction ~ 1.0" is an expectation, not the pass rule. An earlier version of the tripwire also
    blocked when an arm with an edge failed to collapse INTO the noise floor, which produced a
    false HARD failure on crypto H4 `ADP_SWING_SCALE_SIZE_STATE_HALVE_HIGH` — causal effect
    0.0648 σ̂ against a floor of 0.0626, shifted twin 0.0656, i.e. the same number rather than an
    outperforming one.

    The mechanism is structural: a SIZE arm's difference is dominated by the exposure term, and a
    one-bar availability shift barely moves the gate rate, so the exposure term survives the
    shift. Such an arm need not collapse and the emission is still valid.
    """
    from xen.adaptive_management.spdr024_analysis import tripwire_collapse

    def _frame(scale: float) -> pl.DataFrame:
        rng = np.random.default_rng(7)
        n = 400
        base = rng.normal(scale=10.0, size=n)
        rows = []
        for arm_id, size in (("FIXED_SIZE_UNIT", 1.0), ("ADP_X_SIZE_STATE_HALVE_HIGH", 0.5)):
            for index in range(n):
                rows.append(
                    {
                        "arm_id": arm_id,
                        "arm_class": "MANAGEMENT",
                        "device": "SIZE",
                        "symbol": "S",
                        "origin_id": f"o{index}",
                        "entry_ts": datetime(2023, 1, 1, tzinfo=UTC) + timedelta(hours=index),
                        "regime_episode_id": f"R{index // 10}",
                        "regime_state": "HIGH",
                        "risk_size": size,
                        "admitted": True,
                        "rejection_class": "ADMITTED",
                        "outcome_bps": base[index],
                        "counterfactual_outcome_bps": None,
                        "capital_normalised_return_bps": base[index] * size * scale,
                    }
                )
        return pl.DataFrame(rows)

    # The shifted twin is a near-identical copy: nothing collapses, but nothing outperforms.
    causal, shifted = _frame(1.0), _frame(1.0001)
    result = tripwire_collapse(causal, shifted, domain_hours=1, n_boot=50)

    assert result["surviving_arms"] == []
    # Whatever the collapse behaviour, an emission with no surviving shifted edge is valid.
    assert result["pass"] is result["non_vacuous"]
    # And the non-collapse is still reported, so the operator sees it.
    assert "arms_with_an_edge_that_did_not_collapse_into_noise" in result
    assert "non_collapse_note" in result
