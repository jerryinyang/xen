from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import polars as pl
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PROJECT_ROOT / "python/experiments/SPDR-011/code"


def _load(name: str):
    path = CODE_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"spdr011_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _events() -> pl.DataFrame:
    t0 = datetime(2022, 10, 1, 4, tzinfo=timezone.utc)
    return pl.DataFrame(
        {
            "event_id": ["E1", "E2"],
            "band": ["DESIGN", "DESIGN"],
            "symbol": ["BTCUSDT", "ETHUSDT"],
            "entry_ts": [t0, t0 + timedelta(hours=4)],
            "exit_ts": [t0 + timedelta(hours=4), t0 + timedelta(hours=8)],
            "trigger_ts": [t0, t0 + timedelta(hours=4)],
            "direction": [1, -1],
            "vol_tercile": ["HIGH", "MID"],
            "cross_rank": [1, 3],
            "beta60": [1.0, 1.2],
            "utc_slot": [4, 8],
            "calendar_third": [1, 1],
        }
    )


def test_outcome_join_keeps_located_rows_and_uses_open_to_open_prices() -> None:
    runner = _load("runner_contract")
    events = _events()
    t0 = events["entry_ts"][0]
    marks = pl.DataFrame(
        {
            "symbol": ["BTCUSDT"] * 4,
            "SourceCloseTime": [
                t0 + timedelta(minutes=1),
                t0 + timedelta(hours=1, minutes=1),
                t0 + timedelta(hours=2, minutes=1),
                t0 + timedelta(hours=4, minutes=1),
            ],
            "RealOpen": [107.0, 106.0, 105.0, 104.0],
        }
    )

    out = runner.attach_open_to_open_outcomes(events, marks)

    assert out.height == 2
    first = out.row(0, named=True)
    assert first["gross_signed_4h_bps"] == pytest.approx(-280.3738317757)
    assert first["gross_absolute_4h_bps"] == pytest.approx(280.3738317757)
    assert first["4h_available"] is True
    second = out.row(1, named=True)
    assert second["4h_available"] is False
    assert second["gross_signed_4h_bps"] is None
    assert second["outcome_unavailable_reason"] == "ENTRY_MARK_MISSING"


def test_partial_costs_use_shared_bybit_stack_and_never_charge_spread() -> None:
    runner = _load("runner_contract")
    t0 = datetime(2022, 10, 1, 4, tzinfo=timezone.utc)
    outcomes = pl.DataFrame(
        {
            "event_id": ["NO_STAMP", "ONE_STAMP"],
            "entry_ts": [t0, t0 + timedelta(hours=4)],
            "exit_ts": [t0 + timedelta(hours=4), t0 + timedelta(hours=8)],
            "entry_open": [100.0, 100.0],
            "gross_signed_4h_bps": [30.0, 30.0],
            "4h_available": [True, True],
        }
    )

    out = runner.attach_partial_costs(outcomes)

    assert out["funding_stamps"].to_list() == [1, 0]
    assert out["fee_rt_bps"].to_list() == pytest.approx([11.0, 11.0])
    assert out["spread_rt_bps"].to_list() == [None, None]
    assert out["partial_net_2bps"].to_list() == pytest.approx([16.0, 17.0])
    assert set(out["cost_scope"].to_list()) == {"PARTIAL_FEES_FUNDING_ONLY"}


def test_short_golden_trace_uses_real_open_at_exact_four_hour_boundary() -> None:
    runner = _load("runner_contract")
    entry = datetime(2022, 10, 2, 20, tzinfo=timezone.utc)
    events = pl.DataFrame(
        {
            "event_id": ["GT-2"],
            "symbol": ["ETHUSDT"],
            "entry_ts": [entry],
            "direction": [-1],
        }
    )
    marks = pl.DataFrame(
        {
            "symbol": ["ETHUSDT", "ETHUSDT"],
            "SourceCloseTime": [
                entry + timedelta(minutes=1),
                entry + timedelta(hours=4, minutes=1),
            ],
            "RealOpen": [88.0, 84.0],
        }
    )

    out = runner.attach_open_to_open_outcomes(events, marks)

    assert out["gross_signed_4h_bps"].item() == pytest.approx(454.5454545455)


def test_signed_flow_join_requires_relative_volume_identity_and_causal_timestamp() -> None:
    runner = _load("runner_contract")
    events = _events().head(1)
    trigger = events["trigger_ts"][0]
    signed = pl.DataFrame(
        {
            "symbol": ["BTCUSDT"],
            "trigger_ts": [trigger],
            "signed_known_ts": [trigger],
            "BuyVolume": [70.0],
            "SellVolume": [30.0],
            "Volume": [100.0],
            "flow_pct_long": [0.75],
            "flow_pct_short": [0.25],
        }
    )

    out = runner.attach_signed_flow(events, signed)

    assert out["imbalance"].item() == pytest.approx(0.4)
    assert out["aligned_flow"].item() == pytest.approx(0.4)
    assert out["flow_upper_tercile"].item() is True

    short = runner.attach_signed_flow(events.with_columns(pl.lit(-1).alias("direction")), signed)
    assert short["aligned_flow"].item() == pytest.approx(-0.4)
    assert short["flow_pct"].item() == pytest.approx(0.25)
    assert short["flow_upper_tercile"].item() is False

    large = signed.with_columns(
        pl.lit(70_000_000.0).alias("BuyVolume"),
        pl.lit(30_000_000.0).alias("SellVolume"),
        pl.lit(100_000_000.01).alias("Volume"),
    )
    runner.attach_signed_flow(events, large)

    with pytest.raises(ValueError, match=r"BuyVolume \+ SellVolume"):
        runner.attach_signed_flow(events, signed.with_columns(pl.lit(99.0).alias("Volume")))
    with pytest.raises(ValueError, match="known after trigger"):
        runner.attach_signed_flow(
            events,
            signed.with_columns(
                (pl.col("signed_known_ts") + pl.duration(minutes=1)).alias("signed_known_ts")
            ),
        )


def test_future_destroy_is_stratified_zero_fixed_and_sentinel_calibrated() -> None:
    controls = _load("controls")
    n = 24
    rows = pl.DataFrame(
        {
            "event_id": [f"E{i}" for i in range(n)],
            "symbol": ["BTCUSDT"] * 12 + ["ETHUSDT"] * 12,
            "band": ["DESIGN"] * n,
            "calendar_third": [1] * 6 + [2] * 6 + [1] * 6 + [2] * 6,
            "vol_tercile": (["HIGH", "MID"] * 12),
            "direction": ([1, -1] * 12),
            "gross_signed_4h_bps": np.linspace(-30.0, 30.0, n),
        }
    )

    mapping = controls.stratified_derangement(rows, seed=17)
    assert mapping["source_event_id"].to_list() != mapping["path_event_id"].to_list()
    assert not any(
        a == b
        for a, b in zip(mapping["source_event_id"], mapping["path_event_id"], strict=True)
    )
    joined = mapping.join(
        rows.select("event_id", "symbol", "calendar_third"),
        left_on="source_event_id",
        right_on="event_id",
    ).join(
        rows.select("event_id", "symbol", "calendar_third"),
        left_on="path_event_id",
        right_on="event_id",
        suffix="_path",
    )
    assert joined.filter(
        (pl.col("symbol") != pl.col("symbol_path"))
        | (pl.col("calendar_third") != pl.col("calendar_third_path"))
    ).is_empty()

    report = controls.calibrate_future_destroy_sentinel(rows, n_seeds=2000, seed0=100)
    assert report["derangement_zero_fixed_points"] is True
    assert report["raw_sentinel_bps"] == pytest.approx(50.0, abs=0.5)
    lo, hi = report["synthetic_null_envelope_99"]
    assert lo <= report["post_destroy_sentinel_bps"] <= hi
    assert "pass" not in report


def test_date_block_bootstrap_retains_whole_dates_and_has_no_auto_verdict() -> None:
    controls = _load("controls")
    values = pl.DataFrame(
        {
            "trade_date": [datetime(2022, 1, 1).date()] * 2
            + [datetime(2022, 1, 2).date()] * 2,
            "value_bps": [10.0, 20.0, -5.0, 5.0],
        }
    )

    report = controls.date_block_inference(
        values,
        value_col="value_bps",
        n_boot=100,
        seeds=(1, 2),
        block_days=1,
    )

    assert report["independent_unit"] == "UTC_DATE"
    assert report["n_dates"] == 2
    assert set(report["statistics"]) == {"mean", "median", "trimmed_mean_20pct"}
    assert "pass" not in report
    assert "verdict" not in report


def test_schedule_submits_on_completed_boundary_for_next_open_fill() -> None:
    strategy = _load("spdr011_strategy")
    t0 = datetime(2022, 10, 1, 4, tzinfo=timezone.utc)
    events = pl.DataFrame(
        {
            "event_id": ["LONG", "SHORT"],
            "symbol": ["BTCUSDT", "BTCUSDT"],
            "entry_ts": [t0, t0 + timedelta(hours=4)],
            "exit_ts": [t0 + timedelta(hours=4), t0 + timedelta(hours=8)],
            "direction": [1, -1],
        }
    )

    schedule = strategy.build_target_schedule(events)

    assert schedule["decision_ts"].to_list() == [
        t0,
        t0 + timedelta(hours=4),
        t0 + timedelta(hours=4),
        t0 + timedelta(hours=8),
    ]
    assert schedule["action"].to_list() == ["ENTRY", "EXIT", "ENTRY", "EXIT"]
    assert schedule["event_id"].to_list() == ["LONG", "LONG", "SHORT", "SHORT"]
    assert schedule["client_order_id"].n_unique() == 4
    with pytest.raises(ValueError, match="overlap"):
        strategy.build_target_schedule(
            events.with_columns(
                pl.when(pl.col("event_id") == "SHORT")
                .then(pl.lit(t0 + timedelta(hours=2)))
                .otherwise(pl.col("entry_ts"))
                .alias("entry_ts")
            )
        )


def test_contiguous_same_direction_events_remain_two_explicit_round_trips() -> None:
    strategy = _load("spdr011_strategy")
    t0 = datetime(2022, 10, 1, 4, tzinfo=timezone.utc)
    events = pl.DataFrame(
        {
            "event_id": ["L1", "L2"],
            "symbol": ["BTCUSDT", "BTCUSDT"],
            "entry_ts": [t0, t0 + timedelta(hours=4)],
            "exit_ts": [t0 + timedelta(hours=4), t0 + timedelta(hours=8)],
            "direction": [1, 1],
        }
    )

    schedule = strategy.build_target_schedule(events)

    assert schedule["action"].to_list() == ["ENTRY", "EXIT", "ENTRY", "EXIT"]
    assert schedule["direction"].to_list() == [1, 1, 1, 1]
    assert schedule.filter(pl.col("decision_ts") == t0 + timedelta(hours=4)).height == 2
    with pytest.raises(ValueError, match="one prefiltered symbol"):
        strategy.build_target_schedule(
            events.with_columns(
                pl.when(pl.col("event_id") == "L2")
                .then(pl.lit("ETHUSDT"))
                .otherwise(pl.col("symbol"))
                .alias("symbol")
            )
        )


def test_ordered_layer_inputs_preserve_all_predeclared_arms() -> None:
    layers = _load("layers")
    artifact = pl.DataFrame(
        {
            "event_id": ["H1", "H2", "M1"],
            "vol_tercile": ["HIGH", "HIGH", "MID"],
            "4h_available": [True, False, True],
            "cross_rank": [1, 2, 3],
            "top2": [True, True, False],
            "flow_upper_tercile": [True, False, False],
            "aligned_flow": [0.8, 0.2, -0.3],
            "gross_absolute_4h_bps": [50.0, None, 20.0],
            "partial_net_2bps": [15.0, None, -5.0],
        }
    )

    views = layers.ordered_layer_inputs(artifact)

    assert tuple(views) == ("L1", "L2", "L3", "L4", "L5")
    assert views["L1"].frame["event_id"].to_list() == ["H1"]
    assert views["L2"].frame["event_id"].to_list() == ["H1", "M1"]
    assert views["L4"].frame["cross_rank"].to_list() == [1]
    assert views["L5"].frame["event_id"].to_list() == ["H1"]
    assert all("pass" not in view.metadata for view in views.values())


def test_direction_derangement_reassigns_events_without_fixed_points() -> None:
    controls = _load("controls")
    rows = pl.DataFrame(
        {
            "event_id": [f"E{i}" for i in range(6)],
            "symbol": ["BTCUSDT"] * 6,
            "band": ["DESIGN"] * 6,
            "calendar_third": [1] * 6,
            "direction": [1, -1, 1, -1, 1, -1],
        }
    )

    out = controls.direction_derangement(rows, seed=99)

    assert not any(
        a == b
        for a, b in zip(out["source_event_id"], out["direction_event_id"], strict=True)
    )
    assert sorted(out["deranged_direction"].to_list()) == sorted(rows["direction"].to_list())


def test_matched_random_timing_preserves_exact_cells_and_excludes_live_dates() -> None:
    controls = _load("controls")
    t0 = datetime(2022, 10, 1, 4, tzinfo=timezone.utc)
    live = pl.DataFrame(
        {
            "event_id": ["E1", "E2"],
            "symbol": ["BTCUSDT", "BTCUSDT"],
            "band": ["DESIGN", "DESIGN"],
            "direction": [1, 1],
            "utc_slot": [4, 4],
            "vol_tercile": ["HIGH", "HIGH"],
            "calendar_third": [1, 1],
            "occupancy": [2, 2],
            "beta60": [1.0, 1.1],
            "trade_day": [t0.date(), (t0 + timedelta(days=1)).date()],
        }
    )
    candidates = pl.DataFrame(
        {
            "candidate_id": ["C1", "C2", "C3"],
            "symbol": ["BTCUSDT"] * 3,
            "band": ["DESIGN"] * 3,
            "direction": [1] * 3,
            "utc_slot": [4] * 3,
            "vol_tercile": ["HIGH"] * 3,
            "calendar_third": [1] * 3,
            "occupancy": [2] * 3,
            "beta60": [0.95, 1.05, 1.2],
            "trade_day": [
                (t0 + timedelta(days=2)).date(),
                (t0 + timedelta(days=3)).date(),
                (t0 + timedelta(days=4)).date(),
            ],
        }
    )

    matches = controls.matched_random_timing(live, candidates, n_seeds=2, seed0=7)

    assert matches.height == 4
    assert matches.group_by("seed").agg(pl.col("candidate_id").n_unique())["candidate_id"] \
        .to_list() == [2, 2]
    assert not set(matches["matched_trade_day"].to_list()) & set(live["trade_day"].to_list())
    assert set(matches["symbol"].to_list()) == {"BTCUSDT"}


def test_l4_random_top2_matches_date_cluster_occupancy_and_signed_beta() -> None:
    controls = _load("controls")
    day = datetime(2022, 10, 1).date()
    events = pl.DataFrame(
        {
            "trade_day": [day, day, day],
            "symbol": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
            "top2": [True, True, False],
            "direction": [1, -1, 1],
            "beta60": [1.0, 0.8, 0.2],
        }
    )

    out = controls.random_top2_cluster_matches(
        events,
        symbols=("BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT"),
        realised_pairs=pl.DataFrame(
            {"trade_day": [day], "symbol_1": ["BTCUSDT"], "symbol_2": ["ETHUSDT"]}
        ),
        n_seeds=2,
        seed0=51_000,
    )

    assert out.height == 2
    assert out["matched_episode_count"].to_list() == [2, 2]
    assert out["beta_distance"].to_list() == pytest.approx([0.8, 0.8])
    assert set(zip(out["symbol_1"], out["symbol_2"], strict=True)) == {
        ("ETHUSDT", "SOLUSDT")
    }


def test_run1_bundle_contains_design_only_and_never_stages_confirm(tmp_path: Path) -> None:
    bundle = _load("bundle")
    root = tmp_path / "bundle"
    artifact = pl.DataFrame({"event_id": ["D"], "band": ["DESIGN"], "value": [1]})
    manifest = bundle.write_bundle(root, artifact, metadata={"experiment": "SPDR-011"})

    assert set(manifest["members"]) == {"design.parquet"}
    assert not (root / "confirm.parquet").exists()
    assert bundle.read_band(root, band="DESIGN")["event_id"].to_list() == ["D"]
    with pytest.raises(PermissionError, match="not executed"):
        bundle.read_band(root, band="CONFIRM")


def test_run1_bundle_rejects_confirm_rows(tmp_path: Path) -> None:
    bundle = _load("bundle")
    artifact = pl.DataFrame(
        {"event_id": ["D", "C"], "band": ["DESIGN", "CONFIRM"], "value": [1, 2]}
    )

    with pytest.raises(ValueError, match="DESIGN-only"):
        bundle.write_bundle(tmp_path / "bundle", artifact, metadata={})


def test_conversion_control_batteries_report_effects_without_auto_verdict() -> None:
    controls = _load("controls")
    rows = pl.DataFrame(
        {
            "event_id": [f"E{i}" for i in range(8)],
            "symbol": ["BTCUSDT"] * 4 + ["ETHUSDT"] * 4,
            "band": ["DESIGN"] * 8,
            "calendar_third": [1] * 8,
            "direction": [1, -1] * 4,
            "vol_tercile": ["HIGH", "MID"] * 4,
            "gross_signed_4h_bps": [30.0, -10.0, 20.0, 5.0] * 2,
            "total_bps": [11.0] * 8,
            "4h_available": [True] * 8,
        }
    )

    report = controls.conversion_control_batteries(rows, n_seeds=2, seed0=31_000)

    assert report["seed_range"] == [31_000, 31_001]
    assert len(report["direction_derangement"]["seed_effect_bps"]) == 2
    assert len(report["future_path_derangement"]["seed_effect_bps"]) == 2
    assert "pass" not in report
    assert "verdict" not in report


def test_runner_pins_current_census_derivation_and_signed_attestation() -> None:
    run = _load("run_spdr011")

    assert run._sha256(run.CENSUS) == run.CENSUS_SHA256
    assert run._sha256(run.CENSUS_JSON) == run.CENSUS_JSON_SHA256
    assert run._sha256(run.CENSUS_DERIVATION) == run.CENSUS_DERIVATION_SHA256
    assert run._sha256(run.SIGNED_ATTESTATION) == run.SIGNED_ATTESTATION_SHA256


def test_live_signed_catalog_tree_rehash_detects_post_attestation_mutation(
    tmp_path: Path,
) -> None:
    run = _load("run_spdr011")
    catalog = tmp_path / "catalog"
    catalog.mkdir()
    (catalog / "a.bin").write_bytes(b"alpha")
    frozen = run.catalog_tree_sha256(catalog)

    assert run.assert_signed_catalog_tree(catalog, frozen, frozen) == frozen
    (catalog / "a.bin").write_bytes(b"corrupted")
    with pytest.raises(RuntimeError, match="tree hash mismatch"):
        run.assert_signed_catalog_tree(catalog, frozen, frozen)


@pytest.mark.parametrize(
    ("raw", "ci_lowers", "destroyed", "expected"),
    [
        (14.99, [1.0] * 5, [0.0] * 2000, "NOT_APPLICABLE"),
        (20.0, [1.0, 1.0, 0.0, 1.0, 1.0], [0.0] * 2000, "NOT_APPLICABLE"),
        (20.0, [1.0] * 5, [0.0] * 1979 + [25.0] * 21, "INVALID"),
        (20.0, [1.0] * 5, [6.0] * 2000, "INVALID"),
        (20.0, [1.0] * 5, np.linspace(-2.0, 2.0, 2000).tolist(), "VALID"),
    ],
)
def test_future_destroy_survival_rule(
    raw: float,
    ci_lowers: list[float],
    destroyed: list[float],
    expected: str,
) -> None:
    controls = _load("controls")

    report = controls.adjudicate_future_destroy(
        raw_effect_bps=raw,
        date_block_ci_lower_by_seed=ci_lowers,
        destroyed_effect_bps=destroyed,
    )

    assert report["integrity_status"] == expected


def _fill_reconciliation_fixture() -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    strategy = _load("spdr011_strategy")
    t0 = datetime(2022, 10, 1, 4, tzinfo=timezone.utc)
    events = pl.DataFrame(
        {
            "event_id": ["E1"],
            "symbol": ["BTCUSDT"],
            "entry_ts": [t0],
            "exit_ts": [t0 + timedelta(hours=4)],
            "direction": [1],
            "4h_available": [True],
            "outcome_unavailable_reason": [None],
        }
    )
    schedule = strategy.build_target_schedule(events)
    fills = schedule.select(
        "client_order_id",
        pl.lit("BTCUSDT-LINEAR.BYBIT").alias("instrument_id"),
        pl.when(pl.col("action") == "ENTRY").then(pl.lit("BUY")).otherwise(pl.lit("SELL"))
        .alias("side"),
        pl.when(pl.col("action") == "ENTRY").then(100.0).otherwise(105.0).alias("avg_px"),
        (pl.col("decision_ts").dt.epoch("ns") + 2).alias("ts_last"),
    )
    orders = fills.select("client_order_id").with_columns(pl.lit("FILLED").alias("status"))
    marks = pl.DataFrame(
        {
            "symbol": ["BTCUSDT", "BTCUSDT"],
            "SourceCloseTime": [
                t0 + timedelta(minutes=1),
                t0 + timedelta(hours=4, minutes=1),
            ],
            "RealOpen": [100.0, 105.0],
        }
    )
    return events, schedule, fills, orders, marks


def test_event_fill_reconciliation_accepts_exact_tagged_actions() -> None:
    contract = _load("runner_contract")
    events, schedule, fills, orders, marks = _fill_reconciliation_fixture()

    result = contract.reconcile_event_fills(events, schedule, fills, orders, marks)

    assert result["actions"].height == 2
    assert result["actions"]["actual_fill_source_ts"].to_list() == result["actions"][
        "expected_fill_source_ts"
    ].to_list()
    assert result["events"]["fill_reconciliation_status"].to_list() == ["RECONCILED"]


def test_event_fill_reconciliation_preserves_polars_nanoseconds() -> None:
    contract = _load("runner_contract")
    events, schedule, fills, orders, marks = _fill_reconciliation_fixture()
    fills = fills.with_columns(
        pl.from_epoch("ts_last", time_unit="ns")
        .dt.replace_time_zone("UTC")
        .alias("ts_last")
    )

    result = contract.reconcile_event_fills(events, schedule, fills, orders, marks)

    assert result["events"]["fill_reconciliation_status"].to_list() == ["RECONCILED"]


@pytest.mark.parametrize(
    "corruption",
    ["missing_fill", "wrong_side", "wrong_price", "wrong_time", "rejected_order"],
)
def test_event_fill_reconciliation_rejects_corruption(corruption: str) -> None:
    contract = _load("runner_contract")
    events, schedule, fills, orders, marks = _fill_reconciliation_fixture()
    if corruption == "missing_fill":
        fills = fills.head(1)
    elif corruption == "wrong_side":
        fills = fills.with_columns(
            pl.when(pl.arange(0, pl.len()) == 0)
            .then(pl.lit("SELL"))
            .otherwise(pl.col("side"))
            .alias("side")
        )
    elif corruption == "wrong_price":
        fills = fills.with_columns(
            pl.when(pl.arange(0, pl.len()) == 0)
            .then(pl.lit(100.01))
            .otherwise(pl.col("avg_px"))
            .alias("avg_px")
        )
    elif corruption == "wrong_time":
        fills = fills.with_columns((pl.col("ts_last") + 1).alias("ts_last"))
    else:
        orders = orders.with_columns(pl.lit("REJECTED").alias("status"))

    with pytest.raises(RuntimeError, match="fill reconciliation"):
        contract.reconcile_event_fills(events, schedule, fills, orders, marks)


def test_unavailable_event_cannot_masquerade_as_complete_fill_pair() -> None:
    contract = _load("runner_contract")
    events, schedule, fills, orders, marks = _fill_reconciliation_fixture()
    events = events.with_columns(
        pl.lit(False).alias("4h_available"),
        pl.lit("EXIT_4H_MARK_MISSING").alias("outcome_unavailable_reason"),
    )

    with pytest.raises(RuntimeError, match="masquerades"):
        contract.reconcile_event_fills(events, schedule, fills, orders, marks)


def test_run1_selects_design_events_only() -> None:
    runner = _load("run_spdr011")
    events = pl.DataFrame(
        {
            "event_id": ["D", "C"],
            "band": ["DESIGN", "CONFIRM"],
            "entry_ts": [
                datetime(2023, 2, 28, 20, tzinfo=timezone.utc),
                datetime(2023, 3, 1, 4, tzinfo=timezone.utc),
            ],
        }
    )

    selected = runner._run1_events(events)

    assert selected["event_id"].to_list() == ["D"]
    assert set(selected["band"].to_list()) == {"DESIGN"}


def test_run1_data_end_covers_last_exit_open_without_reaching_later_confirm() -> None:
    runner = _load("run_spdr011")
    events = pl.DataFrame(
        {"exit_ts": [datetime(2023, 3, 1, tzinfo=timezone.utc)]}
    )

    assert runner._run1_data_end(events) == datetime(
        2023,
        3,
        1,
        0,
        1,
        tzinfo=timezone.utc,
    )


def test_executable_events_exclude_missing_outcomes_without_dropping_artifact_rows() -> None:
    runner = _load("run_spdr011")
    artifact = pl.DataFrame(
        {
            "event_id": ["READY", "MISSING"],
            "4h_available": [True, False],
        }
    )

    executable = runner._executable_events(artifact)

    assert artifact.height == 2
    assert executable["event_id"].to_list() == ["READY"]


def test_execution_tick_frame_sequences_real_open_after_decision() -> None:
    runner = _load("run_spdr011")
    decision = datetime(2022, 10, 1, 4, tzinfo=timezone.utc)
    schedule = pl.DataFrame(
        {
            "client_order_id": ["ENTRY"],
            "symbol": ["BTCUSDT"],
            "decision_ts": [decision],
        }
    )
    marks = pl.DataFrame(
        {
            "symbol": ["BTCUSDT"],
            "SourceCloseTime": [decision + timedelta(minutes=1)],
            "RealOpen": [107.0],
            "Volume": [12.5],
        }
    )

    ticks = runner._execution_tick_frame(schedule, marks)

    assert ticks.row(0, named=True) == {
        "client_order_id": "ENTRY",
        "symbol": "BTCUSDT",
        "source_close_ts": decision + timedelta(minutes=1),
        "ts_event": decision,
        "ts_init_ns": int(decision.timestamp() * 1_000_000_000) + 2,
        "price": 107.0,
        "size": 12.5,
    }


def test_execution_tick_frame_rejects_missing_real_open() -> None:
    runner = _load("run_spdr011")
    decision = datetime(2022, 10, 1, 4, tzinfo=timezone.utc)
    schedule = pl.DataFrame(
        {
            "client_order_id": ["ENTRY"],
            "symbol": ["BTCUSDT"],
            "decision_ts": [decision],
        }
    )
    marks = pl.DataFrame(
        schema={
            "symbol": pl.String,
            "SourceCloseTime": pl.Datetime("us", "UTC"),
            "RealOpen": pl.Float64,
            "Volume": pl.Float64,
        }
    )

    with pytest.raises(RuntimeError, match="missing real-open execution marks"):
        runner._execution_tick_frame(schedule, marks)


def test_execution_tick_frame_rejects_less_size_than_adapter_order() -> None:
    runner = _load("run_spdr011")
    decision = datetime(2022, 10, 1, 4, tzinfo=timezone.utc)
    schedule = pl.DataFrame(
        {
            "client_order_id": ["ENTRY"],
            "symbol": ["DOGEUSDT"],
            "decision_ts": [decision],
        }
    )
    marks = pl.DataFrame(
        {
            "symbol": ["DOGEUSDT"],
            "SourceCloseTime": [decision + timedelta(minutes=1)],
            "RealOpen": [0.0595],
            "Volume": [0.5],
        }
    )

    with pytest.raises(RuntimeError, match="insufficient execution-tick size"):
        runner._execution_tick_frame(schedule, marks)


def test_execution_ticks_use_real_price_after_order_insertion() -> None:
    from nautilus_trader.model.enums import AggressorSide
    from nautilus_trader.persistence.catalog import ParquetDataCatalog

    runner = _load("run_spdr011")
    instrument = ParquetDataCatalog(str(PROJECT_ROOT / "data/catalog")).instruments(
        instrument_ids=["BTCUSDT-LINEAR.BYBIT"]
    )[0]
    decision = datetime(2022, 10, 1, 4, tzinfo=timezone.utc)
    frame = pl.DataFrame(
        {
            "client_order_id": ["ENTRY"],
            "symbol": ["BTCUSDT"],
            "source_close_ts": [decision + timedelta(minutes=1)],
            "ts_event": [decision],
            "ts_init_ns": [int(decision.timestamp() * 1_000_000_000) + 2],
            "price": [107.0],
            "size": [12.5],
        }
    )

    ticks = runner._execution_ticks(frame, {"BTCUSDT": instrument})

    assert len(ticks) == 1
    assert float(ticks[0].price) == 107.0
    assert ticks[0].ts_event == int(decision.timestamp() * 1_000_000_000)
    assert ticks[0].ts_init == int(decision.timestamp() * 1_000_000_000) + 2
    assert ticks[0].aggressor_side == AggressorSide.NO_AGGRESSOR


def test_execution_latency_inserts_one_nanosecond_before_real_open_tick() -> None:
    runner = _load("run_spdr011")

    config = runner._execution_latency_config()

    assert config.config == {
        "base_latency_nanos": 0,
        "insert_latency_nanos": 1,
        "update_latency_nanos": 0,
        "cancel_latency_nanos": 0,
    }


def test_engine_fills_real_open_across_multiple_instrument_streams(tmp_path: Path) -> None:
    """Data-stream merge order must not change the scheduled real-open fill."""
    from nautilus_trader.backtest.node import BacktestNode
    from nautilus_trader.config import (
        BacktestDataConfig,
        BacktestEngineConfig,
        BacktestRunConfig,
        BacktestVenueConfig,
        ImportableStrategyConfig,
        LoggingConfig,
    )
    from nautilus_trader.core.datetime import dt_to_unix_nanos
    from nautilus_trader.model.data import Bar, BarType, TradeTick
    from nautilus_trader.model.enums import AggressorSide
    from nautilus_trader.model.identifiers import TradeId
    from nautilus_trader.persistence.catalog import ParquetDataCatalog

    runner = _load("run_spdr011")
    strategy = _load("spdr011_strategy")
    source_catalog = ParquetDataCatalog(str(PROJECT_ROOT / "data/catalog"))
    instruments = {
        symbol: source_catalog.instruments(
            instrument_ids=[f"{symbol}-LINEAR.BYBIT"]
        )[0]
        for symbol in ("XRPUSDT", "ETHUSDT")
    }
    decision = datetime(2024, 1, 1, 4, tzinfo=timezone.utc)
    exit_ = decision + timedelta(minutes=2)
    final_exit = exit_ + timedelta(minutes=2)
    schedules = {}
    bars = []
    ticks = []
    expected = {}
    for symbol, instrument in instruments.items():
        event_ids = (
            [f"{symbol}-STREAM-1", f"{symbol}-STREAM-2"]
            if symbol == "XRPUSDT"
            else [f"{symbol}-STREAM-1"]
        )
        events = pl.DataFrame(
            {
                "event_id": event_ids,
                "symbol": [symbol] * len(event_ids),
                "entry_ts": [decision, exit_][: len(event_ids)],
                "exit_ts": [exit_, final_exit][: len(event_ids)],
                "direction": [1] * len(event_ids),
            }
        )
        schedule = strategy.build_target_schedule(events)
        schedule_path = tmp_path / f"{symbol}-schedule.parquet"
        runtime_schedule = (
            schedule.with_columns(
                pl.when(pl.col("action") == "ENTRY")
                .then(0)
                .otherwise(1)
                .alias("_reverse_priority")
            )
            .sort(["decision_ts", "_reverse_priority"])
            .drop("_reverse_priority")
        )
        runtime_schedule.write_parquet(schedule_path)
        schedules[symbol] = schedule_path
        bar_type = BarType.from_str(f"{instrument.id}-1-MINUTE-LAST-EXTERNAL")
        if symbol == "XRPUSDT":
            bar_points = [
                (decision - timedelta(minutes=1), 100.0),
                (decision + timedelta(minutes=1), 110.0),
                (exit_, 105.0),
                (exit_ + timedelta(minutes=1), 106.0),
                (final_exit, 103.0),
                (final_exit + timedelta(minutes=1), 104.0),
            ]
            execution_prices = {decision: 107.0, exit_: 104.0, final_exit: 102.0}
        else:
            bar_points = [
                (decision - timedelta(minutes=1), 199.0),
                (decision, 200.0),
                (decision + timedelta(minutes=1), 210.0),
                (exit_, 205.0),
                (exit_ + timedelta(minutes=1), 206.0),
            ]
            execution_prices = {decision: 207.0, exit_: 204.0}
        for dt, close in sorted(bar_points):
            ts_ns = dt_to_unix_nanos(dt)
            bars.append(
                Bar(
                    bar_type,
                    instrument.make_price(close),
                    instrument.make_price(close + 1),
                    instrument.make_price(close - 1),
                    instrument.make_price(close),
                    instrument.make_qty(1_000),
                    ts_ns,
                    ts_ns,
                )
            )
        offset_ns = runner.EXECUTION_SEQUENCE_OFFSET_NS[symbol]
        for row in schedule.iter_rows(named=True):
            price = execution_prices[row["decision_ts"]]
            ts_ns = dt_to_unix_nanos(row["decision_ts"])
            ticks.append(
                TradeTick(
                    instrument.id,
                    instrument.make_price(price),
                    instrument.make_qty(1_000),
                    AggressorSide.NO_AGGRESSOR,
                    TradeId(f"OPEN-{row['client_order_id']}"),
                    ts_ns,
                    ts_ns + offset_ns + 2,
                )
            )
            expected[row["client_order_id"]] = (price, ts_ns + offset_ns + 2)
    catalog_path = tmp_path / "catalog"
    catalog = ParquetDataCatalog(str(catalog_path))
    catalog.write_data(list(instruments.values()))
    catalog.write_data(bars)
    catalog.write_data(ticks)

    strategy_configs = [
        ImportableStrategyConfig(
            strategy_path="spdr011_strategy:Spdr011ScheduleStrategy",
            config_path="spdr011_strategy:Spdr011ScheduleConfig",
            config={
                "instrument_id": str(instrument.id),
                "trade_size": "1",
                "schedule_path": str(schedules[symbol]),
                "decision_offset_ns": runner.EXECUTION_SEQUENCE_OFFSET_NS[symbol],
            },
        )
        for symbol, instrument in instruments.items()
    ]
    run_config = BacktestRunConfig(
        dispose_on_completion=False,
        engine=BacktestEngineConfig(
            logging=LoggingConfig(log_level="ERROR", log_colors=False, print_config=False),
            strategies=strategy_configs,
        ),
        venues=[
            BacktestVenueConfig(
                name="BYBIT",
                oms_type="NETTING",
                account_type="MARGIN",
                base_currency="USDT",
                starting_balances=["1000000 USDT"],
                book_type="L1_MBP",
                latency_model=runner._execution_latency_config(),
            )
        ],
        data=[
            BacktestDataConfig(
                catalog_path=str(catalog_path),
                data_cls=Bar,
                instrument_id=str(instrument.id),
            )
            for instrument in instruments.values()
        ]
        + [
            BacktestDataConfig(
                catalog_path=str(catalog_path),
                data_cls=TradeTick,
                instrument_id=str(instrument.id),
            )
            for instrument in instruments.values()
        ],
    )
    node = BacktestNode(configs=[run_config])
    node.run()
    fills = node.get_engine(run_config.id).trader.generate_order_fills_report()
    node.dispose()

    actual = {
        str(client_order_id): (float(row["avg_px"]), int(row["ts_last"].value))
        for client_order_id, row in fills.iterrows()
    }
    assert actual == expected
    xrp_shared_ids = strategy.build_target_schedule(
        pl.DataFrame(
            {
                "event_id": ["XRPUSDT-STREAM-1", "XRPUSDT-STREAM-2"],
                "symbol": ["XRPUSDT", "XRPUSDT"],
                "entry_ts": [decision, exit_],
                "exit_ts": [exit_, final_exit],
                "direction": [1, 1],
            }
        )
    ).filter(pl.col("decision_ts") == exit_)["client_order_id"].to_list()
    shared_fill_ns = (
        dt_to_unix_nanos(exit_)
        + runner.EXECUTION_SEQUENCE_OFFSET_NS["XRPUSDT"]
        + 2
    )
    actual_shared_ids = [
        str(client_order_id)
        for client_order_id, row in fills.iterrows()
        if int(row["ts_last"].value) == shared_fill_ns
        and str(row["instrument_id"]).startswith("XRPUSDT-")
    ]
    assert actual_shared_ids == xrp_shared_ids


def test_unavailable_event_with_no_schedule_or_fills_reconciles_as_unavailable() -> None:
    contract = _load("runner_contract")
    events, schedule, fills, orders, marks = _fill_reconciliation_fixture()
    events = events.with_columns(
        pl.lit(False).alias("4h_available"),
        pl.lit("EXIT_4H_MARK_MISSING").alias("outcome_unavailable_reason"),
    )
    empty_schedule = schedule.head(0)
    empty_fills = fills.head(0)
    empty_orders = orders.head(0)

    result = contract.reconcile_event_fills(
        events,
        empty_schedule,
        empty_fills,
        empty_orders,
        marks,
    )

    assert result["actions"].is_empty()
    assert result["events"]["fill_reconciliation_status"].to_list() == ["UNAVAILABLE"]


class _FakeBar:
    def __init__(self, ts_event: int) -> None:
        self.ts_event = ts_event
        self.open = 100.0
        self.high = 101.0
        self.low = 99.0
        self.close = 100.5
        self.volume = 10.0


class _FakeFence:
    analysis_start_utc = datetime(2022, 10, 1, tzinfo=timezone.utc)
    train_end_utc = datetime(2022, 11, 1, tzinfo=timezone.utc)


def test_bar_marks_emits_utc_aware_source_close_time(monkeypatch) -> None:
    """Real marks must carry UTC tz so they join to the UTC-aware census (Run-1 seam)."""
    runner = _load("run_spdr011")
    ts_ns = int(datetime(2022, 10, 1, 4, 1, tzinfo=timezone.utc).timestamp() * 1_000_000_000)

    monkeypatch.setattr(runner, "ParquetDataCatalog", lambda _path: object())
    monkeypatch.setattr(
        runner, "fenced_bar_query", lambda *a, **k: [_FakeBar(ts_ns)]
    )

    marks = runner._bar_marks(
        pl.DataFrame(
            {"exit_ts": [datetime(2022, 10, 1, 4, tzinfo=timezone.utc)]}
        ),
        _FakeFence(),
    )

    dtype = marks.schema["SourceCloseTime"]
    assert isinstance(dtype, pl.Datetime)
    assert dtype.time_zone == "UTC", f"marks SourceCloseTime must be UTC-aware, got {dtype}"

    # The derived entry_ts must join a UTC-aware census entry_ts without a dtype error.
    events = pl.DataFrame(
        {
            "event_id": ["E1"],
            "symbol": [runner.SYMBOLS[0]],
            "entry_ts": [datetime(2022, 10, 1, 4, tzinfo=timezone.utc)],
            "direction": [1],
        }
    )
    contract = _load("runner_contract")
    out = contract.attach_open_to_open_outcomes(events, marks)
    assert out.filter(pl.col("symbol") == runner.SYMBOLS[0])["entry_open"][0] == 100.0
