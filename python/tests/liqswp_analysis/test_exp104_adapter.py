from __future__ import annotations

from types import ModuleType
from typing import Callable

import numpy as np
import polars as pl
from xen.liqswp_analysis.statistics import circular_cluster_indices


def test_exp104_emits_regime_contrasts_frequency_and_join_evidence(
    load_exp_module: Callable[[str], ModuleType],
) -> None:
    module = load_exp_module("EXP-104")
    adapter = module.Adapter(n_boot=40, n_destroy=2000, seeds=(0, 1))
    frame = adapter.fixture_frame()
    assert adapter.integrity(frame).blocking_pass
    rows = adapter.analyze(frame)
    assert {(row["arm"], row["comparator"]) for row in rows} == {
        ("LOW", "MID"),
        ("HIGH", "MID"),
    }
    assert {row["channel"] for row in rows} >= {
        "swing_atr",
        "swing_duration_ns",
        "strong_move",
    }
    extra = adapter.extra(frame)
    assert set(extra) >= {"frequency_census", "regime_census", "profile_join", "control"}
    assert extra["profile_join"]["unmatched_raids"] == 0


def test_frequency_blocks_dispatch_per_timeframe(
    load_exp_module: Callable[[str], ModuleType],
) -> None:
    """Per-timeframe one-day blocks must reach the registered L/2, L, 2L."""
    module = load_exp_module("EXP-104")
    assert module.FREQUENCY_BLOCKS_BY_TIMEFRAME["15m"] == (48, 96, 192)
    assert module.FREQUENCY_BLOCKS_BY_TIMEFRAME["30m"] == (24, 48, 96)
    assert module.FREQUENCY_BLOCKS_BY_TIMEFRAME["1h"] == (12, 24, 48)
    assert module.FREQUENCY_BLOCKS_BY_TIMEFRAME["60m"] == (12, 24, 48)


def _stratum_frame(**overrides):
    row = {
        "archive_symbol": "EURUSD",
        "timeframe": "60m",
        "confirmation_method": "CLOSE",
        "confirmation_reference": "1H",
        "side": "BUY",
        "config": "CFG",
        "causal_regime": "LOW",
        "starts": 1,
        "raid_regime": "LOW",
    }
    row.update(overrides)
    return row


def test_partition_payloads_maps_60m_and_keeps_warmup(
    load_exp_module: Callable[[str], ModuleType],
) -> None:
    module = load_exp_module("EXP-104")
    adapter = module.Adapter()
    frame = pl.DataFrame(
        [
            _stratum_frame(causal_regime="LOW", starts=1),
            _stratum_frame(causal_regime="MID", starts=0),
            _stratum_frame(causal_regime="REGIME_WARMUP", starts=0),
            _stratum_frame(causal_regime="ATR_UNDEFINED", starts=0),
        ]
    )
    payloads = module._partition_payloads(
        frame, adapter.stratum_columns, n_boot=4, seeds=(0,)
    )
    assert len(payloads) == 1
    assert payloads[0]["blocks"] == (12, 24, 48)
    assert payloads[0]["causal_regime"].count("REGIME_WARMUP") == 1
    assert payloads[0]["causal_regime"].count("ATR_UNDEFINED") == 1
    observed = module._frequency_from_codes(
        *module._encode_frequency_marks(
            payloads[0]["causal_regime"], payloads[0]["starts"]
        ),
        block_length=24,
    )
    assert observed["warmup_undefined_exposure"] == {
        "REGIME_WARMUP": 1,
        "ATR_UNDEFINED": 1,
    }
    assert observed["eligible_marks"] == 2


def test_frequency_arm_table_emits_empty_exposure_not_warmup_arm(
    load_exp_module: Callable[[str], ModuleType],
) -> None:
    module = load_exp_module("EXP-104")
    adapter = module.Adapter()
    marked = pl.DataFrame(
        [
            _stratum_frame(causal_regime="LOW"),
            _stratum_frame(causal_regime="REGIME_WARMUP"),
        ]
    )
    starts = pl.DataFrame([_stratum_frame(raid_regime="LOW", starts=1)]).select(
        *adapter.stratum_columns, "raid_regime", "starts"
    )
    table = module._frequency_arm_table(marked, starts, adapter.stratum_columns)
    regimes = set(table["causal_regime"].to_list())
    assert regimes == {"LOW", "MID", "HIGH"}
    reasons = {
        row["causal_regime"]: row["empty_exposure_reason"] for row in table.to_dicts()
    }
    assert reasons["LOW"] is None
    assert reasons["MID"] == "EMPTY_EXPOSURE"
    assert reasons["HIGH"] == "EMPTY_EXPOSURE"
    assert table.filter(pl.col("causal_regime") == "LOW")["starts"][0] == 1


def test_frequency_reports_warmup_undefined_and_observed_layers(
    load_exp_module: Callable[[str], ModuleType],
) -> None:
    module = load_exp_module("EXP-104")
    marks = [
        {"ts_event_ns": 1, "regime": "LOW"},
        {"ts_event_ns": 2, "regime": "MID"},
        {"ts_event_ns": 3, "regime": "REGIME_WARMUP"},
        {"ts_event_ns": 4, "regime": "HIGH"},
    ]
    raids = [{"raid_id": "r1", "sweep_ts_ns": 2, "raid_regime": "LOW"}]
    result = module.frequency_rate(marks, raids, block_length=96)
    assert result["exposure"] == {"LOW": 1, "MID": 1, "HIGH": 0}
    assert result["rates_per_1000"]["LOW"] == 1000.0
    assert result["warmup_undefined_exposure"] == {"REGIME_WARMUP": 1}
    assert "HIGH" in result["empty_exposure"]
    assert result["eligible_marks"] == 2


def test_frequency_uses_preceding_mark_and_reports_empty_exposure(
    load_exp_module: Callable[[str], ModuleType],
) -> None:
    module = load_exp_module("EXP-104")
    marks = [
        {"ts_event_ns": 1, "regime": "LOW"},
        {"ts_event_ns": 2, "regime": "MID"},
        {"ts_event_ns": 3, "regime": "MID"},
    ]
    raids = [{"raid_id": "r1", "sweep_ts_ns": 2, "raid_regime": "LOW"}]
    result = module.frequency_rate(marks, raids, block_length=96)
    assert result["exposure"] == {"LOW": 1, "MID": 1, "HIGH": 0}
    assert result["starts"] == {"LOW": 1, "MID": 0, "HIGH": 0}
    assert "HIGH" in result["empty_exposure"]


def _oracle_frequency_bootstrap(module, units, *, block_length, n_boot, seeds):
    """Gathered circular-block bootstrap: the registered per-draw estimator."""
    n = len(units)
    codes = np.array(
        [module._REGIME_CODE.get(unit["preceding_regime"], 5) for unit in units],
        dtype=np.intp,
    )
    start_counts = np.array([len(unit["starts"]) for unit in units], dtype=np.int64)
    seed_rows = []
    all_low = []
    all_high = []
    for seed in seeds:
        rng = np.random.default_rng(seed)
        low = []
        high = []
        for _ in range(n_boot):
            indices = circular_cluster_indices(n, block_length, rng)
            drawn = codes[indices]
            starts = start_counts[indices]
            exposure = np.bincount(drawn, minlength=6)[:3]
            sums = np.bincount(drawn, weights=starts, minlength=6)[:3]
            rates = [
                float("nan")
                if int(exposure[i]) == 0
                else 1000.0 * float(sums[i]) / float(exposure[i])
                for i in range(3)
            ]
            mid = rates[1]
            low.append(rates[0] - mid)
            high.append(rates[2] - mid)
        low_a = np.asarray(low, dtype=float)
        high_a = np.asarray(high, dtype=float)
        seed_rows.append(
            {
                "finite_draws": {
                    "LOW": int(np.isfinite(low_a).sum()),
                    "HIGH": int(np.isfinite(high_a).sum()),
                },
                "intervals": {
                    "LOW": module._interval_from_values(low_a),
                    "HIGH": module._interval_from_values(high_a),
                },
            }
        )
        all_low.append(low_a)
        all_high.append(high_a)
    return seed_rows, np.concatenate(all_low), np.concatenate(all_high)


def test_frequency_bootstrap_matches_gathered_circular_blocks(
    load_exp_module: Callable[[str], ModuleType],
) -> None:
    module = load_exp_module("EXP-104")
    regimes = ("LOW", "MID", "HIGH", "REGIME_WARMUP", "ATR_UNDEFINED") * 17
    units = [
        {"preceding_regime": regime, "starts": (None,) * (index % 5)}
        for index, regime in enumerate(regimes)
    ]
    kwargs = {"block_length": 7, "n_boot": 48, "seeds": (0, 4)}
    fast = module._frequency_bootstrap_units(units, **kwargs)
    seed_rows, all_low, all_high = _oracle_frequency_bootstrap(module, units, **kwargs)
    for got, expected in zip(fast["seeds"], seed_rows, strict=True):
        assert got["finite_draws"] == expected["finite_draws"]
        assert got["intervals"] == expected["intervals"]
    assert fast["intervals"] == {
        "LOW": module._interval_from_values(all_low),
        "HIGH": module._interval_from_values(all_high),
    }


def test_frequency_bootstrap_handles_live_length_marks_quickly(
    load_exp_module: Callable[[str], ModuleType],
) -> None:
    import time

    module = load_exp_module("EXP-104")
    n = 8_000
    codes = np.array([index % 3 for index in range(n)], dtype=np.int8)
    starts = np.array([index % 4 for index in range(n)], dtype=np.int64)
    t0 = time.perf_counter()
    result = module._frequency_bootstrap_codes(
        codes, starts, block_length=96, n_boot=200, seeds=(0,)
    )
    elapsed = time.perf_counter() - t0
    assert result["seeds"][0]["finite_draws"]["LOW"] == 200
    assert elapsed < 1.0
