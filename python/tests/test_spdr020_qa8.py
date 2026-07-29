from __future__ import annotations

import importlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


CODE_DIR = Path(__file__).parents[1] / "experiments" / "SPDR-020" / "screen_code"
sys.path.insert(0, str(CODE_DIR))

config = importlib.import_module("config")
controls = importlib.import_module("controls")
event_engine = importlib.import_module("event_engine")
fills_bridge = importlib.import_module("fills_bridge")
golden = importlib.import_module("golden")
layers = importlib.import_module("layers")
metrics = importlib.import_module("metrics")
prepare = importlib.import_module("prepare")
provenance = importlib.import_module("provenance")
selection = importlib.import_module("selection")
selfcheck = importlib.import_module("selfcheck")


def _ns(day: int) -> int:
    return day * config.DAY_NS


def test_calendar_index_keeps_days_without_events() -> None:
    idx, starts = metrics.day_index(
        np.array([_ns(10), _ns(12)], dtype=np.int64),
        calendar_start_ns=_ns(10),
        calendar_end_ns=_ns(13),
    )
    assert idx.tolist() == [0, 2]
    assert starts.tolist() == [_ns(10), _ns(11), _ns(12)]


def test_paired_bootstrap_uses_identical_calendar_resamples() -> None:
    ts = np.array([_ns(i) for i in range(12)], dtype=np.int64)
    base = np.array([20, -10] * 6, dtype=float)
    changed = base.copy()
    changed[::2] += 5
    result = metrics.paired_delta_metrics(
        changed,
        ts,
        base,
        ts,
        n_boot=80,
        clock="H1",
    )
    assert result["paired"] is True
    assert result["calendar_days"] == 12
    assert result["resample_signature_a"] == result["resample_signature_b"]
    assert np.isfinite(result["delta_log_R"])
    assert result["ci_low"] <= result["delta_log_R"] <= result["ci_high"]
    assert {"via_WL", "via_p"}.issubset(result["ladder"])


def test_interaction_bootstrap_is_replicate_level() -> None:
    ts = np.array([_ns(i) for i in range(16)], dtype=np.int64)
    base = np.array([30, -20] * 8, dtype=float)
    shock = base + np.tile([2, 0], 8)
    level = base + np.tile([1, 0], 8)
    joint = base + np.tile([6, 0], 8)
    result = metrics.paired_interaction_metrics(
        joint,
        shock,
        level,
        base,
        ts,
        n_boot=80,
        clock="H1",
    )
    assert result["paired"] is True
    assert result["interaction_formula"] == "joint-shock-level+baseline"
    assert result["n_boot_replicates"] > 1
    assert result["ci_low"] <= result["delta_log_R"] <= result["ci_high"]
    assert {"via_WL", "via_p"}.issubset(result["ladder"])
    assert result["ladder"]["requested_replicates_per_seed"] == 80
    assert result["ladder"]["all_replicate_counts_match"] is True
    assert result["ladder"]["operator_definitions"]["via_WL"] != result[
        "ladder"
    ]["operator_definitions"]["via_p"]
    assert all(
        set(result["ladder"][operator])
        == {str(rung) for rung in config.LADDER_RUNGS}
        for operator in ("via_WL", "via_p")
    )


def test_paired_plant_operators_transform_different_sufficient_fields() -> None:
    totals = np.array([
        [10.0, 20.0, 6.0, 72.0, 4.0, -32.0, 0.0, 0.0],
    ])
    via_wl = metrics._plant_totals_via_wl(totals, 0.1)
    via_p = metrics._plant_totals_via_p(totals, 0.1)
    assert via_wl[0, 2] == totals[0, 2]
    assert via_wl[0, 4] == totals[0, 4]
    assert via_wl[0, 3] != totals[0, 3]
    assert via_p[0, 2] != totals[0, 2]
    assert via_p[0, 4] != totals[0, 4]
    assert np.isclose(via_p[0, 3] / via_p[0, 2], 12.0)
    assert np.isclose(-via_p[0, 5] / via_p[0, 4], 8.0)


def test_sensitivity_ladder_reports_fractional_replicate_detection() -> None:
    ts = np.array([_ns(i) for i in range(30)], dtype=np.int64)
    returns = np.array([25, -20, 8, -9, 15, -11] * 5, dtype=float)
    ladder = metrics.replicate_sensitivity_ladder(
        returns,
        ts,
        n_boot=120,
        clock="H1",
        rungs=(0.02, 0.05),
    )
    for operator in ("via_WL", "via_p"):
        assert set(ladder[operator]) == {"0.02", "0.05"}
        assert all(0.0 <= rate <= 1.0 for rate in ladder[operator].values())
    assert any(
        0.0 < rate < 1.0
        for operator in ("via_WL", "via_p")
        for rate in ladder[operator].values()
    )


def test_bootstrap_uses_exact_frozen_seed_battery() -> None:
    returns = np.array([20.0, -10.0] * 8)
    day_idx = np.arange(returns.size, dtype=np.int64)
    suff = metrics.day_sufficient(returns, day_idx, returns.size)
    result = metrics.envelope_ci_logR(suff, n_boot=20, clock="H1")
    assert {row["seed"] for row in result["per_seed"]} == set(config.BOOT_SEEDS)


def test_frozen_missing_zvol_pin_is_not_refit() -> None:
    assert not hasattr(prepare, "freeze_zvol_scale")
    assert np.isnan(prepare.resolve_frozen_s_symbol(float("nan")))
    assert prepare.zvol_source_is_available(float("nan")) is False


def test_zvol_partition_requires_exact_membership() -> None:
    covered = sorted(set(config.universe_symbols()) - set(config.ZVOL_NAN_SYMBOLS))
    result = selfcheck.check_zvol_partition(
        covered_symbols=covered,
        missing_symbols=sorted(config.ZVOL_NAN_SYMBOLS),
    )
    assert result["held"] is True
    bad = selfcheck.check_zvol_partition(
        covered_symbols=covered + [next(iter(config.ZVOL_NAN_SYMBOLS))],
        missing_symbols=[],
    )
    assert bad["held"] is False


def test_hold_variants_are_h_free_and_unique() -> None:
    cells = layers.expected_primary_cell_manifest()
    assert len(cells) == 1584
    assert len({layers.cell_manifest_key(row) for row in cells}) == 1584
    holds = [row for row in cells if row["variant_id"].startswith("L4_HOLD_")]
    assert len(holds) == 144
    assert all(row["h"] == row["hold_bars"] for row in holds)
    assert all(row["base_h"] is None for row in holds)
    full = layers.expected_full_cell_manifest()
    assert len(full) == 28512
    assert len({layers.cell_manifest_key(row) for row in full}) == 28512
    scored = layers.expand_manifest_bands(full)
    assert len(scored) == 85536


def test_manifest_reconciliation_keeps_explicit_empty_cells() -> None:
    manifest = layers.expected_primary_cell_manifest()[:2]
    actual = pd.DataFrame(
        [
            {
                **manifest[0],
                "band": "TRAIN",
                "log_R": 0.1,
                "ci_low": 0.0,
                "ci_high": 0.2,
                "ci_width": 0.2,
                "block_mde": 0.1,
            }
        ]
    )
    result = layers.reconcile_metrics_to_manifest(actual, manifest)
    assert len(result) == 6
    assert result["manifest_key"].is_unique
    assert result["empty"].sum() == 5


def test_cell_population_aggregates_exact_band_sufficient_statistics() -> None:
    cov = pd.DataFrame(
        [
            {"symbol": "A", "band": "DESIGN", "n_origins": 10, "n_events": 4, "n_undecided": 1},
            {"symbol": "B", "band": "DESIGN", "n_origins": 20, "n_events": 6, "n_undecided": 2},
            {"symbol": "A", "band": "CONFIRM", "n_origins": 5, "n_events": 1, "n_undecided": 0},
        ]
    )
    design = layers.aggregate_cell_population(cov, band="DESIGN")
    confirm = layers.aggregate_cell_population(cov, band="CONFIRM")
    pooled = layers.aggregate_cell_population(cov, band="TRAIN")
    assert design == {"n_origins": 30, "n_events": 10, "n_undecided": 3, "p_event": 1 / 3}
    assert confirm == {"n_origins": 5, "n_events": 1, "n_undecided": 0, "p_event": 0.2}
    assert pooled == {"n_origins": 35, "n_events": 11, "n_undecided": 3, "p_event": 11 / 35}


def test_selection_complement_is_disjoint_and_exhaustive() -> None:
    base = pd.DataFrame(
        {
            "event_key": ["a", "b", "c", "d"],
            "r_bps": [10.0, -5.0, 3.0, -2.0],
        }
    )
    selected = base.iloc[[0, 2]]
    complement = layers.exact_complement(base, selected, key_columns=("event_key",))
    assert complement["event_key"].tolist() == ["b", "d"]
    assert set(selected.event_key).isdisjoint(set(complement.event_key))
    assert len(selected) + len(complement) == len(base)


def test_tripwire_1_requires_real_rebuilt_event_key_difference() -> None:
    legal = controls.TripwireRun(
        conditioning=np.array([1.0, 2.0, 3.0]),
        event_keys={("A", 1), ("A", 3)},
        returns=np.array([10.0, -8.0]),
        timestamps=np.array([_ns(1), _ns(3)]),
    )
    unchanged = controls.evaluate_tripwire_1(legal, legal, n_boot=20)
    assert unchanged["hard_pass"] is False
    leaky = controls.TripwireRun(
        conditioning=np.array([2.0, 3.0, 4.0]),
        event_keys={("A", 1), ("A", 2)},
        returns=np.array([10.0, 6.0]),
        timestamps=np.array([_ns(1), _ns(2)]),
    )
    changed = controls.evaluate_tripwire_1(legal, leaky, n_boot=20)
    assert changed["hard_pass"] is True
    assert changed["event_key_symmetric_difference_count"] == 2
    assert set(changed["paired_deltas"]) == {"p", "W", "L", "log_R"}


def test_tripwire_2_derives_early_entries_from_pairs() -> None:
    result = controls.evaluate_tripwire_2(
        [
            {"anchor_idx": 4, "legal_event_idx": 7, "leaky_event_idx": 4},
            {"anchor_idx": 9, "legal_event_idx": 10, "leaky_event_idx": 9},
        ],
        live_returns=np.array([12.0, -7.0]),
        leaky_returns=np.array([2.0, 3.0]),
        timestamps=np.array([_ns(1), _ns(2)]),
        n_boot=20,
    )
    assert result["hard_pass"] is True
    assert result["future_touch_zones"] == 2
    assert result["early_entry_count"] == 2
    assert all(p["leaky_event_idx"] < p["legal_event_idx"] for p in result["event_index_pairs"])


def test_controls_change_intended_input_and_preserve_invariants() -> None:
    entries = np.array([0, 1, 2, 3])
    sides = np.array([1, -1, 1, -1])
    timing = controls.derange_indices(entries, seed=11)
    side = controls.derange_binary_sides(sides)
    assert np.all(timing != entries)
    assert np.all(side != sides)
    assert sorted(timing.tolist()) == sorted(entries.tolist())
    assert np.all(np.abs(side) == np.abs(sides))


def test_timing_control_reruns_exit_rule_instead_of_permuting_returns() -> None:
    entries = pd.DataFrame(
        {
            "event_key": ["a", "b", "c", "d"],
            "symbol": ["X"] * 4,
            "entry_idx": [0, 1, 2, 3],
            "side": [1, 1, -1, -1],
            "hold": [2] * 4,
        }
    )

    def rerun(frame: pd.DataFrame, exit_rule: str) -> np.ndarray:
        assert exit_rule == "TARGET_A2"
        return frame["side"].to_numpy() * (frame["entry_idx"].to_numpy() + 1.0)

    result = controls.entry_timing_control(
        entries,
        rerun=rerun,
        exit_rule="TARGET_A2",
        seeds=(11, 13),
    )
    assert result["reran_fills_and_exits"] is True
    assert result["exit_rule"] == "TARGET_A2"
    assert result["fixed_point_count"] == 0
    assert result["changed_entry_count"] == 8


def test_side_control_reruns_signed_estimand() -> None:
    entries = pd.DataFrame(
        {
            "event_key": ["a", "b", "c", "d"],
            "entry_idx": [0, 1, 2, 3],
            "side": [1, -1, 1, -1],
        }
    )

    def rerun(frame: pd.DataFrame, exit_rule: str) -> np.ndarray:
        assert exit_rule == "TRAIL_B1"
        return frame["side"].to_numpy() * np.array([10.0, 7.0, 4.0, 2.0])

    result = controls.side_label_control(
        entries,
        rerun=rerun,
        exit_rule="TRAIL_B1",
        seeds=(1, 2),
    )
    assert result["reran_signed_estimand"] is True
    assert result["fixed_point_count"] == 0
    assert result["fixed_point_definition"] == "source_row_identity"
    assert result["unique_assignment_count"] == 2


def test_ambient_and_magnitude_controls_are_disjoint() -> None:
    episodes = pd.DataFrame(
        {
            "event_key": ["a", "b", "c", "d", "e"],
            "is_breach": [True, False, False, True, False],
            "selected": [True, False, False, True, False],
            "move_decile": [1, 1, 2, 2, 2],
            "r_bps": [10.0, 2.0, -3.0, 8.0, 1.0],
        }
    )
    ambient = controls.ambient_base_control(episodes)
    matched = controls.magnitude_matched_control(episodes)
    assert ambient["disjoint"] is True
    assert matched["disjoint_per_decile"] is True
    assert ambient["n_control"] == 3


def test_primary_control_family_requires_reruns_and_all_mandatory_controls() -> None:
    episodes = pd.DataFrame(
        {
            "variant_id": ["L0_BASELINE"] * 4,
            "clock": ["H1"] * 4,
            "source": ["Z-VOL"] * 4,
            "z": [1.5] * 4,
            "H": [12] * 4,
            "h": [12] * 4,
            "event_type": ["E-TOUCH"] * 4,
            "policy": ["P-MOMO"] * 4,
            "band": ["CONFIRM"] * 4,
            "symbol": ["X"] * 4,
            "event_key": ["a", "b", "c", "d"],
            "entry_idx": [0, 1, 2, 3],
            "entry_ts": [_ns(i) for i in range(4)],
            "side": [1, -1, 1, -1],
            "r_bps": [10.0, -8.0, 7.0, -6.0],
        }
    )
    ambient = pd.DataFrame(
        {
            "event_key": ["a", "b", "c", "d", "e", "f"],
            "is_breach": [True, True, True, True, False, False],
            "r_bps": [10.0, -8.0, 7.0, -6.0, 2.0, -3.0],
        }
    )
    magnitude = pd.DataFrame(
        {
            "event_key": ["a", "b", "c", "d"],
            "selected": [True, False, True, False],
            "move_decile": [1, 1, 2, 2],
            "r_bps": [10.0, -8.0, 7.0, -6.0],
        }
    )

    def rerun(frame: pd.DataFrame, exit_rule: str) -> np.ndarray:
        assert exit_rule == "L0_BASELINE"
        return frame["side"].to_numpy() * (frame["entry_idx"].to_numpy() + 10.0)

    result = controls.run_primary_controls(
        episodes,
        n_boot=20,
        rerun=rerun,
        ambient_candidates=ambient,
        magnitude_candidates=magnitude,
        seeds=(11, 13),
    )
    assert {
        "mirror_null",
        "side_derangement",
        "entry_timing_derangement",
        "ambient_base",
        "magnitude_matched",
        "exit_matched_controls",
    }.issubset(result)
    assert result["control_manifest_complete"] is True
    assert result["all_mandatory_controls_present"] is True
    assert result["control_manifest"][0]["status"] == "UNUSABLE_VACUOUS"


def test_execution_candidate_refuses_developer_modes() -> None:
    expected = config.execution_manifest()
    smoke = dict(expected)
    smoke.update({"smoke": True, "n_boot": 50})
    result = selfcheck.execution_candidate_eligibility(smoke)
    assert result["eligible"] is False
    assert "developer_mode" in result["reasons"]
    assert "bootstrap_count" in result["reasons"]


def test_provenance_requires_all_executed_dependencies_tracked_and_hashed(tmp_path: Path) -> None:
    dependency = tmp_path / "fills.py"
    dependency.write_text("VALUE = 1\n")
    manifest = provenance.build_dependency_manifest(
        [dependency],
        repo_root=tmp_path,
        tracked_paths=set(),
    )
    assert manifest["complete"] is False
    assert manifest["dependencies"][0]["sha256"]
    assert manifest["dependencies"][0]["tracked"] is False
    assert manifest["dependencies"][0]["clean"] is True


@pytest.mark.parametrize(
    ("source", "forecast", "median", "h_hours", "expected_mod", "expected_unmod"),
    [
        ("Z-VOL", 12.0, 9.0, 4.0, 24.0, 18.0),
        ("Z-MAG", 30.0, 20.0, 4.0, 30.0, 20.0),
        ("Z-MAG-SENS", 15.0, 10.0, 4.0, 15.0, 10.0),
    ],
)
def test_source_specific_l4_boundary_never_falls_back_to_zvol(
    source: str,
    forecast: float,
    median: float,
    h_hours: float,
    expected_mod: float,
    expected_unmod: float,
) -> None:
    mod = layers.l4_source_distance_bps(
        source=source,
        forecast_bps=forecast,
        median_bps=median,
        h_hours=h_hours,
        multiplier=1.0,
        modulated=True,
    )
    unmod = layers.l4_source_distance_bps(
        source=source,
        forecast_bps=forecast,
        median_bps=median,
        h_hours=h_hours,
        multiplier=1.0,
        modulated=False,
    )
    assert mod["distance_bps"] == expected_mod
    assert unmod["distance_bps"] == expected_unmod
    assert mod["boundary_source"] == source
    with pytest.raises(ValueError, match="missing source-specific forecast"):
        layers.l4_source_distance_bps(
            source=source,
            forecast_bps=float("nan"),
            median_bps=median,
            h_hours=h_hours,
            multiplier=1.0,
            modulated=True,
        )


def test_hold_and_size_boundary_provenance_is_explicit() -> None:
    assert layers.l4_boundary_source("hold", "Z-MAG") == "NONE_TIME_EXIT"
    assert layers.l4_boundary_source("size", "Z-MAG") == "NONE"
    assert layers.l4_boundary_source("target", "Z-MAG") == "Z-MAG"


def test_golden_missing_specified_case_fails() -> None:
    result = golden.require_exact_case(
        pd.DataFrame({"symbol": ["BTCUSDT"], "z": [1.5]}),
        {"symbol": "ETHUSDT", "z": 1.5},
    )
    assert result["held"] is False
    assert result["reason"] == "specified_case_missing"


def test_golden_g2_uses_current_coverage_counts() -> None:
    coverage = pd.DataFrame(
        [
            {
                "symbol": "ETHUSDT", "clock": "H1", "source": "Z-VOL",
                "z": 1.5, "H": 12, "event_type": "E-TOUCH", "h": 12,
                "band": "DESIGN", "n_origins": 195, "n_events": 194,
            },
            {
                "symbol": "ETHUSDT", "clock": "H1", "source": "Z-VOL",
                "z": 1.5, "H": 12, "event_type": "E-TOUCH", "h": 12,
                "band": "CONFIRM", "n_origins": 249, "n_events": 249,
            },
            {
                "symbol": "ETHUSDT", "clock": "H1", "source": "Z-VOL",
                "z": 3.0, "H": 12, "event_type": "E-TOUCH", "h": 12,
                "band": "DESIGN", "n_origins": 200, "n_events": 100,
            },
            {
                "symbol": "ETHUSDT", "clock": "H1", "source": "Z-VOL",
                "z": 3.0, "H": 12, "event_type": "E-TOUCH", "h": 12,
                "band": "CONFIRM", "n_origins": 200, "n_events": 120,
            },
        ]
    )
    result = golden.reconstruct_g2(coverage)
    assert result["held"] is True
    assert result["detail"]["z3_falls_in_both_bands"] is True


def test_golden_g3_and_g4_require_concrete_rows() -> None:
    events = pd.DataFrame(
        [
            {
                "symbol": "X", "clock": "H1", "source": "Z-VOL", "z": 1.5,
                "H": 12, "band": "DESIGN", "t_idx": 10,
                "event_type": "E-TOUCH", "event": 1, "event_idx": 12,
                "side": 1, "upper": 101.0, "lower": 99.0,
                "event_high": 102.0, "event_low": 100.0, "event_close": 100.5,
            },
            {
                "symbol": "X", "clock": "H1", "source": "Z-VOL", "z": 1.5,
                "H": 12, "band": "DESIGN", "t_idx": 10,
                "event_type": "E-CLOSE", "event": 1, "event_idx": 14,
                "side": 1, "upper": 101.0, "lower": 99.0,
                "event_high": 102.0, "event_low": 100.0, "event_close": 101.5,
            },
        ]
    )
    episodes = pd.DataFrame(
        [
            {
                "symbol": "X", "variant_id": "L4_TARGET_A2_MOD",
                "policy": "P-MOMO", "entry_ts": 10, "exit_ts": 20,
                "suppressed": False,
            },
            {
                "symbol": "X", "variant_id": "L4_TARGET_A2_MOD",
                "policy": "P-MOMO", "entry_ts": 15, "exit_ts": -1,
                "suppressed": True, "suppressed_by_open_until": 20,
            },
        ]
    )
    assert golden.reconstruct_g3(events)["held"] is True
    assert golden.reconstruct_g4(episodes)["held"] is True
    assert golden.reconstruct_g3(events.iloc[:1])["held"] is False
    assert golden.reconstruct_g4(episodes.iloc[:1])["held"] is False


def test_golden_g8_rejects_structural_or_constant_evidence() -> None:
    incomplete = {"adverse_wins": True, "structural": True}
    assert golden.reconstruct_g8(incomplete)["held"] is False
    complete = {
        "symbol": "X",
        "m1_ts": 123,
        "entry_price": 100.0,
        "target_price": 102.0,
        "trail_price": 99.0,
        "m1_open": 100.0,
        "m1_high": 103.0,
        "m1_low": 98.0,
        "m1_close": 101.0,
        "chosen_reason": "TRAIL",
        "chosen_price": 99.0,
        "side": 1,
        "emitted_r_bps": -100.0,
        "independent_expected_reason": "TRAIL",
        "independent_expected_price": 99.0,
        "independent_expected_r_bps": -100.0,
        "dual_exit_probe": True,
        "trail_ratcheted_on_close_only": True,
        "time_exit_open_verified": True,
        "resolver_invoked": True,
        "target_and_trail_active": True,
        "resolver_trace": {
            "reason": "TRAIL",
            "exit_price": 99.0,
            "target_price_input": 102.0,
            "trail_width_price_input": 1.0,
            "target_active": True,
            "trail_active": True,
        },
    }
    assert golden.reconstruct_g8(complete)["held"] is True
    trail_only = dict(complete)
    trail_only["dual_exit_probe"] = False
    trail_only["target_and_trail_active"] = False
    assert golden.reconstruct_g8(trail_only)["held"] is False


def test_derangement_is_over_row_identity_even_with_duplicate_values() -> None:
    permutation = controls.derangement_permutation(4, seed=17)
    assert sorted(permutation.tolist()) == [0, 1, 2, 3]
    assert np.all(permutation != np.arange(4))
    values = np.array([1, 1, 2, 2])
    assert sorted(values[permutation].tolist()) == values.tolist()


def test_selection_complements_are_partitioned_by_exact_cell() -> None:
    common = {
        "clock": "H1", "source": "Z-VOL", "z": 1.5, "H": 12,
        "event_type": "E-TOUCH", "h": 12, "policy": "P-MOMO",
        "band": "DESIGN",
    }
    episodes_rows = [
        {**common, "symbol": symbol, "variant_id": variant, "event_key": key,
         "entry_ts": _ns(i), "r_bps": value}
        for symbol in ("X", "Y")
        for i, (variant, key, value) in enumerate((
            ("L0_BASELINE", f"{symbol}-a", 5.0),
            ("L0_BASELINE", f"{symbol}-b", -4.0),
            ("L2_SHOCK_HMM", f"{symbol}-a", 6.0),
        ))
    ]
    for symbol in ("X", "Y"):
        for event_type, suffix in (("E-CLOSE", "c"), ("E-HORIZON", "h")):
            episodes_rows.append({
                **common, "symbol": symbol, "event_type": event_type,
                "variant_id": "L0_BASELINE", "event_key": f"{symbol}-{suffix}",
                "entry_ts": _ns(4), "r_bps": 3.0,
            })
        for variant in (
            "L2_LEVEL_RMARKOV_K4",
            "L2_LEVEL_RMARKOV_K12",
            "L2_JOINT_HMM_HIGH_AND_K12_HIGH",
            "L3_TGTCUR_FIRES",
        ):
            episodes_rows.append({
                **common, "symbol": symbol, "variant_id": variant,
                "event_key": f"{symbol}-a", "entry_ts": _ns(0), "r_bps": 6.0,
            })
    episodes = pd.DataFrame(episodes_rows)
    metrics_for_selection = pd.DataFrame({
        "mde50": [0.1, 0.2],
        "log_R": [-0.1, 0.1],
    })
    result = selection.run_selection_checks(episodes, metrics_for_selection)
    rows = [r for r in result["rows"] if r["subset"] == "L2_SHOCK_HMM"]
    assert result["schema_ok"] is True
    assert len(rows) == 2
    assert all(r["n_selected"] == 1 and r["n_complement"] == 1 for r in rows)
    assert {r["cell"]["symbol"] for r in rows} == {"X", "Y"}


def test_ladder_uses_requested_replicates_without_cap(monkeypatch) -> None:
    called = {}

    def fake_ladder(*args, **kwargs):
        called["n_boot"] = kwargs["n_boot"]
        return {
            "via_WL": {str(x): 0.5 for x in config.LADDER_RUNGS},
            "via_p": {str(x): 0.5 for x in config.LADDER_RUNGS},
            "n_boot_replicates": kwargs["n_boot"] * len(config.BOOT_SEEDS),
            "requested_replicates_per_seed": kwargs["n_boot"],
        }

    monkeypatch.setattr(metrics, "replicate_sensitivity_ladder", fake_ladder)
    monkeypatch.setattr(
        metrics,
        "envelope_ci_logR",
        lambda *args, **kwargs: {
            "ci_low": -0.1, "ci_high": 0.2, "stat": 0.05,
            "blocks_days": [3, 7, 14],
        },
    )
    r = np.array([5.0, -4.0] * 6)
    ts = np.array([_ns(i) for i in range(12)])
    metrics.cell_metrics(r, ts, n_boot=2_000)
    assert called["n_boot"] == 2_000


def test_illegal_future_detector_uses_same_detector_but_enters_at_anchor() -> None:
    class Pack:
        open = np.full(20, 100.0)
        high = np.array([100.0] * 5 + [102.0] + [100.0] * 14)
        low = np.full(20, 100.0)
        close = np.full(20, 100.0)

    legal = event_engine.detect_event(
        Pack(), 2, 5, 101.0, 99.0, "E-TOUCH", 100.0,
    )
    leaky = event_engine.detect_event(
        Pack(), 2, 5, 101.0, 99.0, "E-TOUCH", 100.0,
        illegal_future_touch_at_anchor=True,
    )
    assert legal["event_idx"] == 5
    assert leaky["event_idx"] == 3
    assert leaky["actual_future_event_idx"] == legal["event_idx"]


def test_chronological_thirds_use_equal_time_intervals_not_equal_rows() -> None:
    start = config.DESIGN_START_NS
    end = config.TRAIN_END_NS
    span = end - start
    episodes = pd.DataFrame({
        "entry_ts": [
            start + 1,
            start + 2,
            start + 3,
            start + span // 3 + 1,
            start + 2 * span // 3 + 1,
        ],
        "r_bps": [10.0, 8.0, 6.0, -7.0, 9.0],
    })
    result = controls.chronological_thirds_control(episodes)
    assert [row["n"] for row in result["thirds"]] == [3, 1, 1]
    assert result["interval_start_ns"] == start
    assert result["interval_end_ns"] == end
    assert result["sign_agreement"] is False


def test_control_manifest_reconciles_and_labels_thin_l4_cell() -> None:
    common = {
        "clock": "H1", "z": 1.5, "H": 12, "h": 12,
        "event_type": "E-TOUCH", "policy": "P-MOMO", "symbol": "X",
        "band": "CONFIRM",
    }
    episodes = pd.DataFrame([
        {
            **common, "source": "Z-VOL", "variant_id": "L0_BASELINE",
            "event_key": f"l0-{index}", "entry_idx": index,
            "entry_ts": config.DESIGN_END_NS + index + 1,
            "side": side, "r_bps": value,
        }
        for index, (side, value) in enumerate(
            ((1, 10.0), (-1, -8.0), (1, 7.0), (-1, -6.0))
        )
    ] + [{
        **common, "source": "Z-MAG", "variant_id": "L4_TRAIL_B1_MOD",
        "event_key": "l4-thin", "entry_idx": 1,
        "entry_ts": config.DESIGN_END_NS + 10, "side": 1, "r_bps": 5.0,
    }])
    ambient = pd.DataFrame({
        "event_key": ["a", "b"], "is_breach": [True, False],
        "r_bps": [5.0, -4.0],
    })
    magnitude = pd.DataFrame({
        "event_key": ["a", "b"], "selected": [True, False],
        "move_decile": [1, 1], "r_bps": [5.0, -4.0],
    })

    def rerun(frame: pd.DataFrame, _exit_rule: str) -> np.ndarray:
        return frame["side"].to_numpy() * (frame["entry_idx"].to_numpy() + 10)

    result = controls.run_primary_controls(
        episodes, n_boot=20, rerun=rerun,
        ambient_candidates=ambient, magnitude_candidates=magnitude,
        seeds=(1, 2, 3),
    )
    assert result["control_manifest_complete"] is True
    assert result["required_control_cell_count"] == result[
        "emitted_control_cell_count"
    ]
    l4 = [
        row for row in result["control_manifest"]
        if row["family"] == "L4_EXIT_MATCHED"
    ]
    # Primary-base expansion requires Z-VOL×L4_TRAIL even when only Z-MAG emitted it;
    # the observed thin Z-MAG arm is still labelled, never skipped.
    statuses = {row["status"] for row in l4}
    assert "UNUSABLE_THIN" in statuses
    assert "MISSING" in statuses
    thin = next(row for row in l4 if row["status"] == "UNUSABLE_THIN")
    assert thin["cell"]["source"] == "Z-MAG"
    assert thin["plant_resolution"]["reason"] == (
        "not_estimable_on_thin_population"
    )
    missing = next(row for row in l4 if row["status"] == "MISSING")
    assert missing["cell"]["source"] == "Z-VOL"


def test_paired_ladders_emit_two_operators_and_per_seed_counts() -> None:
    timestamps = np.array([_ns(i) for i in range(30)])
    baseline = np.array([12.0, -8.0] * 15)
    changed = baseline + np.array([2.0, 0.0] * 15)
    result = metrics.paired_delta_metrics(
        changed, timestamps, baseline, timestamps, n_boot=20,
    )
    ladder = result["ladder"]
    assert ladder["operator_definitions"]["via_WL"] != ladder[
        "operator_definitions"
    ]["via_p"]
    assert ladder["requested_replicates_per_seed"] == 20
    assert ladder["realised_replicates_per_seed"]
    assert all(
        row["requested"] == 20
        and row["realised_base"] == 20
        for row in ladder["realised_replicates_per_seed"]
    )


def test_provenance_expands_repository_local_import_closure() -> None:
    controls_path = (
        Path(__file__).parents[1] / "src" / "xen" / "xena" / "controls.py"
    )
    evaluation_path = (
        Path(__file__).parents[1] / "src" / "xen" / "evaluation.py"
    )
    closure = provenance.expand_local_import_closure(
        [controls_path, evaluation_path],
        repo_root=Path(__file__).parents[2],
    )
    relative = {path.relative_to(Path(__file__).parents[2]).as_posix() for path in closure}
    assert "python/src/xen/xena/controls.py" in relative
    assert "python/src/xen/xena/report_layer.py" in relative
    assert "python/src/xen/adjudication.py" in relative


def test_g8_trace_uses_actual_resolver_with_both_exits_active() -> None:
    minute = 60 * config.NS
    m1 = {
        "ts": np.array([minute, 2 * minute]),
        "open": np.array([100.0, 100.0]),
        "high": np.array([100.0, 103.0]),
        "low": np.array([100.0, 98.0]),
        "close": np.array([100.0, 101.0]),
    }
    independent = golden.independent_adverse_fill(
        side=1,
        m1_open=100.0,
        m1_high=103.0,
        m1_low=98.0,
        target_price=102.0,
        trail_price=99.0,
    )
    assert independent["both_reachable"] is True
    assert independent["expected_reason"] == "TRAIL"
    assert independent["expected_price"] == 99.0
    fill = fills_bridge.resolve_target_trail_time(
        m1,
        np.array([100.0, 100.0, 100.0]),
        np.array([0, 2 * minute, 4 * minute]),
        side=1,
        entry_price=100.0,
        fill_ts=minute,
        fill_m1_idx=0,
        active_hold_ns=3 * minute,
        target_price=102.0,
        trail_width_price=1.0,
    )
    assert fill.reason == fills_bridge.EXIT_TRAIL
    assert fill.exit_price == independent["expected_price"]
    evidence = {
        "symbol": "X", "m1_ts": 2 * minute, "entry_price": 100.0,
        "target_price": 102.0, "trail_price": 99.0, "m1_open": 100.0,
        "m1_high": 103.0, "m1_low": 98.0, "m1_close": 101.0,
        "chosen_reason": fill.reason, "chosen_price": fill.exit_price,
        "side": 1, "emitted_r_bps": -100.0,
        "independent_expected_reason": independent["expected_reason"],
        "independent_expected_price": independent["expected_price"],
        "independent_expected_r_bps": -100.0,
        "dual_exit_probe": True,
        "trail_ratcheted_on_close_only": True,
        "time_exit_open_verified": True,
        "resolver_invoked": True, "target_and_trail_active": True,
        "resolver_trace": {
            "reason": fill.reason, "exit_price": fill.exit_price,
            "target_price_input": 102.0, "trail_width_price_input": 1.0,
            "target_active": True, "trail_active": True,
        },
    }
    assert golden.reconstruct_g8(evidence)["held"] is True


def test_required_control_cells_label_missing_l4_devices() -> None:
    start = config.DESIGN_START_NS
    episodes = pd.DataFrame({
        "variant_id": ["L0_BASELINE"] * 4,
        "clock": ["H1"] * 4,
        "source": ["Z-VOL"] * 4,
        "z": [1.5] * 4,
        "H": [12] * 4,
        "h": [12] * 4,
        "event_type": ["E-TOUCH"] * 4,
        "policy": ["P-MOMO"] * 4,
        "band": ["CONFIRM"] * 4,
        "symbol": ["X"] * 4,
        "event_key": list("abcd"),
        "entry_idx": [0, 1, 2, 3],
        "entry_ts": [start + i for i in range(4)],
        "side": [1, -1, 1, -1],
        "r_bps": [10.0, -8.0, 7.0, -6.0],
        "suppressed": [False] * 4,
    })
    ambient = pd.DataFrame({
        "event_key": list("abcdef"),
        "is_breach": [True] * 4 + [False] * 2,
        "r_bps": [10.0, -8.0, 7.0, -6.0, 2.0, -3.0],
    })
    magnitude = pd.DataFrame({
        "event_key": list("abcd"),
        "selected": [True, False, True, False],
        "move_decile": [1, 1, 2, 2],
        "r_bps": [10.0, -8.0, 7.0, -6.0],
    })

    def rerun(frame: pd.DataFrame, exit_rule: str) -> np.ndarray:
        return frame["side"].to_numpy() * (frame["entry_idx"].to_numpy() + 10.0)

    required = controls.expand_required_control_cells(
        episodes,
        l4_variants=("L4_TARGET_A2_MOD", "L4_TRAIL_B1_MOD"),
    )
    assert any(row["variant_id"] == "L4_TARGET_A2_MOD" for row in required)
    result = controls.run_primary_controls(
        episodes,
        n_boot=20,
        rerun=rerun,
        ambient_candidates=ambient,
        magnitude_candidates=magnitude,
        seeds=tuple(range(41000, 41020)),
        required_cells=required,
    )
    statuses = {row["status"] for row in result["control_manifest"]}
    assert "MISSING" in statuses
    assert result["control_manifest_complete"] is True
    assert result["all_control_cells_usable"] is False
    assert result["all_mandatory_controls_present"] is True
    assert result["missing_labelled_cells"]


def test_symbol_shard_writes_complete_marker_and_reloads() -> None:
    import importlib

    run_screen = importlib.import_module("run_screen")
    tmp = Path("/tmp/spdr020_shard_test")
    if tmp.exists():
        import shutil
        shutil.rmtree(tmp)
    tmp.mkdir()
    result = {
        "symbol": "BTCUSDT",
        "empty": False,
        "episodes": [{"event_key": "a", "r_bps": 1.0}],
        "zones": [{"z": 1.5}],
        "events": [{"event_idx": 1}],
        "cell_cov": [{"n_origins": 2}],
        "parity_posts": [{"entry_ts": 1}],
        "unit": {"symbol": "BTCUSDT", "s_symbol": 1.0},
        "tripwire": {"hard_pass": True},
        "g8_evidence": {"dual_exit_probe": True},
        "gate_info": {},
    }
    assert run_screen.shard_is_complete(tmp, "BTCUSDT") is False
    run_screen.write_symbol_shard(tmp, result)
    assert run_screen.shard_is_complete(tmp, "BTCUSDT") is True
    assert run_screen.list_complete_shard_symbols(tmp) == {"BTCUSDT"}
    loaded = run_screen.load_symbol_shard(tmp, "BTCUSDT")
    assert loaded["symbol"] == "BTCUSDT"
    assert loaded["episodes"][0]["event_key"] == "a"
    assert loaded["zones"][0]["z"] == 1.5
    assert loaded["unit"]["s_symbol"] == 1.0
    assert loaded["tripwire"]["hard_pass"] is True


def test_hold_control_requirements_use_device_horizon_not_primary_h() -> None:
    start = config.DESIGN_START_NS
    episodes = pd.DataFrame({
        "variant_id": ["L0_BASELINE"] * 4,
        "clock": ["H1"] * 4,
        "source": ["Z-VOL"] * 4,
        "z": [1.5] * 4,
        "H": [12] * 4,
        "h": [12] * 4,
        "event_type": ["E-TOUCH"] * 4,
        "policy": ["P-MOMO"] * 4,
        "band": ["CONFIRM"] * 4,
        "symbol": ["X"] * 4,
        "event_key": list("abcd"),
        "entry_idx": [0, 1, 2, 3],
        "entry_ts": [start + i for i in range(4)],
        "side": [1, -1, 1, -1],
        "r_bps": [10.0, -8.0, 7.0, -6.0],
        "suppressed": [False] * 4,
    })
    required = controls.expand_required_control_cells(
        episodes,
        l4_variants=(
            "L4_TARGET_A2_MOD",
            "L4_HOLD_4_UNMOD",
            "L4_HOLD_12_MOD",
            "L4_HOLD_24_UNMOD",
        ),
    )
    by_variant = {
        row["variant_id"]: row for row in required if row["variant_id"].startswith("L4_")
    }
    assert by_variant["L4_TARGET_A2_MOD"]["h"] == 12
    assert by_variant["L4_HOLD_4_UNMOD"]["h"] == 4
    assert by_variant["L4_HOLD_12_MOD"]["h"] == 12
    assert by_variant["L4_HOLD_24_UNMOD"]["h"] == 24
    # No impossible HOLD_4 at residual h=12.
    assert not any(
        row["variant_id"].startswith("L4_HOLD_4") and int(row["h"]) == 12
        for row in required
    )


def test_plant_operators_change_different_sufficient_statistics() -> None:
    totals = np.array([[10.0, 20.0, 6.0, 90.0, 4.0, -40.0, 0.0, 1000.0]])
    via_wl = metrics._plant_totals_via_wl(totals, 0.05)
    via_p = metrics._plant_totals_via_p(totals, 0.05)
    assert not np.allclose(via_wl, via_p)
    assert np.isclose(
        metrics._logR_from_totals(via_wl)[0] - metrics._logR_from_totals(totals)[0],
        0.05,
        atol=1e-12,
    )
    assert np.isclose(
        metrics._logR_from_totals(via_p)[0] - metrics._logR_from_totals(totals)[0],
        0.05,
        atol=1e-12,
    )
