"""Focused EXP-100 integrity probes: TRAIN-boundary stamps, destroy bite, golden T1-T3."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import polars as pl

from xen.exp100.config import Exp100CellConfig
from xen.exp100.processor import Exp100Processor, Exp100Sinks
from xen.exp100.state_store import Exp100StateStore
from xen.exp100.types import BarRecord
from xen.nautilus.streaming import MemoryGuard

REPO = Path(__file__).resolve().parents[4]
EMISSION_ROOT = REPO / "data/nautilus_runs/EXP-100/full"
OUT_DIR = REPO / "python/experiments/EXP-100/results/analysis"
CENSUS = OUT_DIR / "cell_census.parquet"
TRAIN_END = datetime(2023, 11, 22, tzinfo=timezone.utc)
HOLDOUT_START = datetime(2024, 12, 13, tzinfo=timezone.utc)
MINUTE_NS = 60_000_000_000


class CollectingWriter:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    @property
    def pending_rows(self) -> int:
        return 0

    def append(self, row: dict[str, Any]) -> None:
        self.rows.append(dict(row))


def _ns_to_utc(ts_ns: int) -> datetime:
    return datetime.fromtimestamp(ts_ns / 1_000_000_000, tz=timezone.utc)


def probe_past_train() -> dict[str, Any]:
    census = pl.read_parquet(CENSUS)
    flagged = census.filter(pl.col("raid_ts_past_train") > 0)
    samples: list[dict[str, Any]] = []
    exact_train_end = 0
    after_train_end = 0
    holdout = 0
    fields = Counterish()
    for row in flagged.iter_rows(named=True):
        raids = pl.read_parquet(EMISSION_ROOT / row["cell_id"] / "raids.parquet")
        for raid in raids.iter_rows(named=True):
            for field in (
                "sweep_ts_ns",
                "first_excursion_ts_ns",
                "return_ts_ns",
                "confirmation_ts_ns",
                "endpoint_ts_ns",
                "censor_ts_ns",
            ):
                ts = raid.get(field)
                if ts is None:
                    continue
                dt = _ns_to_utc(int(ts))
                if dt >= HOLDOUT_START:
                    holdout += 1
                    fields.add(field + "|holdout")
                elif dt > TRAIN_END:
                    after_train_end += 1
                    fields.add(field + "|after")
                    if len(samples) < 8:
                        samples.append(
                            {
                                "cell_id": row["cell_id"],
                                "field": field,
                                "ts": dt.isoformat(),
                                "status": raid["status"],
                                "raid_id": raid["raid_id"],
                            }
                        )
                elif dt == TRAIN_END:
                    exact_train_end += 1
                    fields.add(field + "|exact")
    return {
        "n_flagged_cells": flagged.height,
        "exact_train_end": exact_train_end,
        "after_train_end": after_train_end,
        "holdout": holdout,
        "fields": fields.as_dict(),
        "after_samples": samples,
    }


class Counterish:
    def __init__(self) -> None:
        self._c: dict[str, int] = {}

    def add(self, key: str) -> None:
        self._c[key] = self._c.get(key, 0) + 1

    def as_dict(self) -> dict[str, int]:
        return dict(sorted(self._c.items()))


def probe_destroy_cells() -> dict[str, Any]:
    targets = [
        "ctrader-eurusd-60m-breakout_bar-4h-rolling_252",
        "ctrader-eurusd-60m-level_close-4h-rolling_252",
        "ctrader-eurusd-60m-breakout_bar-1h-rolling_252",
        "ctrader-eurusd-60m-level_close-1h-rolling_252",
        "ctrader-xauusd-60m-level_close-1h-rolling_252",
        "ctrader-ustec-60m-level_close-4h-rolling_252",
    ]
    out: list[dict[str, Any]] = []
    for cell_id in targets:
        path = EMISSION_ROOT / cell_id
        meta = json.loads((path / "run_metadata.json").read_text(encoding="utf-8"))
        raids = pl.read_parquet(path / "raids.parquet")
        dest = pl.read_parquet(path / "raids_destroyed.parquet")
        joined = raids.join(dest, on="raid_id", suffix="_d")
        confirmed = joined.filter(pl.col("confirmation_ts_ns").is_not_null())
        finite = confirmed.filter(
            pl.col("swing_atr").is_finite() & pl.col("swing_atr_d").is_finite()
        )
        row: dict[str, Any] = {
            "cell_id": cell_id,
            "emitted_raid_rows": raids.height,
            "primary_confirmed_rows": confirmed.height,
            "status": raids["status"].value_counts().to_dicts(),
            "destroy": meta["destroy_control"],
            "aligned_finite_primary_pairs": finite.height,
        }
        if finite.height:
            delta = (finite["swing_atr"] - finite["swing_atr_d"]).abs()
            row["mean_abs_d_swing"] = float(delta.mean())
            row["raw_mean_swing"] = float(finite["swing_atr"].mean())
            row["raw_std_swing"] = float(finite["swing_atr"].std()) if finite.height > 1 else None
            if finite.height > 1:
                se = float(finite["swing_atr"].std() / (finite.height**0.5))
                row["raw_se"] = se
                row["integrity_bite"] = 2.8 * se
                row["mean_abs_swing_change_clears_integrity_bite"] = (
                    float(delta.mean()) >= 2.8 * se
                )
            row["aligned_finite_primary_pair_rows"] = [
                {
                    "raid_id": r["raid_id"],
                    "status": r["status"],
                    "swing_atr": r["swing_atr"],
                    "swing_atr_d": r["swing_atr_d"],
                    "duration_ns": r["duration_ns"],
                    "duration_d": r["duration_ns_d"],
                    "strong_move": r["strong_move"],
                    "strong_move_d": r["strong_move_d"],
                }
                for r in finite.iter_rows(named=True)
            ]
        out.append(row)
    return {"cells": out}


def _bar(i: int, o: float, h: float, low: float, c: float) -> BarRecord:
    return BarRecord(
        ts_event_ns=i * MINUTE_NS,
        open=o,
        high=h,
        low=low,
        close=c,
        volume=1.0,
        source_bars=1,
    )


def _flat(i: int, price: float = 100.0) -> BarRecord:
    return _bar(i, price, price, price, price)


def run_golden() -> dict[str, Any]:
    """Feed design T1 and T2/T3 through isolated shared-processor traces."""
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        config = Exp100CellConfig(
            venue="CTRADER",
            archive_symbol="EURUSD",
            instrument_id="EURUSD.CTrader",
            observation_minutes=15,
            confirmation_method="BREAKOUT_BAR",
            confirmation_reference="1H",
            level_config="PREVIOUS_1H",
        )
        t1_sinks = Exp100Sinks(
            bar_marks=CollectingWriter(),
            levels=CollectingWriter(),
            raids=CollectingWriter(),
            tpo_profiles=CollectingWriter(),
            event_log=CollectingWriter(),
        )
        t1_processor = Exp100Processor(
            config,
            Exp100StateStore(tmp_path / "t1-state.sqlite"),
            t1_sinks,
            MemoryGuard(limit_bytes=None, sample_every=10_000),
            auto_catalogue=False,
        )
        t1_processor.seed_level("T1-HIGH", price=100.0, side="HIGH")
        minute = 0
        # Keep the first observation wholly beyond the high level.  Using flat
        # 100.00 source bars here would make it an AMENDMENT-13 same-bar return
        # and legitimately allow a later completed observation to start raid 2.
        for _ in range(14):
            t1_processor.on_one_minute_bar(_flat(minute, 101.2))
            minute += 1
        t1_processor.on_one_minute_bar(
            _bar(minute, 101.2, 101.2, 100.8, 101.0)
        )
        minute += 1
        after_excursion = [
            dict(row) for row in t1_processor.state.iter_active_raids()
        ]

        # A source-minute wick cannot create another observation-grain raid.
        t1_processor.on_one_minute_bar(
            _bar(minute, 101.0, 101.5, 101.0, 101.1)
        )
        minute += 1
        for _ in range(14):
            t1_processor.on_one_minute_bar(_flat(minute, 100.0))
            minute += 1
        after_return = [dict(row) for row in t1_processor.state.iter_active_raids()]

        # Isolate the reference settlement trace so aggregation boundaries cannot
        # accidentally settle T1 while constructing T2.
        settle_sinks = Exp100Sinks(
            bar_marks=CollectingWriter(),
            levels=CollectingWriter(),
            raids=CollectingWriter(),
            tpo_profiles=CollectingWriter(),
            event_log=CollectingWriter(),
        )
        settle_processor = Exp100Processor(
            config,
            Exp100StateStore(tmp_path / "settle-state.sqlite"),
            settle_sinks,
            MemoryGuard(limit_bytes=None, sample_every=10_000),
            auto_catalogue=False,
        )
        for raid_id, level_id, sweep_ts_ns in (
            ("T1-HIGH:raid:1", "T1-HIGH", 10),
            ("T2-HIGH:raid:1", "T2-HIGH", 20),
        ):
            settle_processor.state.insert_raid(
                {
                    "raid_id": raid_id,
                    "level_id": level_id,
                    "event_identity": raid_id,
                    "side": "HIGH",
                    "level_price": 100.0,
                    "sweep_ts_ns": sweep_ts_ns,
                    "first_excursion_ts_ns": sweep_ts_ns,
                    "return_ts_ns": sweep_ts_ns + 1,
                    "confirmation_ts_ns": None,
                    "max_price": 101.2,
                    "max_excursion": 1.2,
                    "profile_generation": None,
                    "profile_finalized": False,
                    "active": 1,
                }
            )
        settle_processor._previous_reference = BarRecord(
            60, 100.0, 101.0, 99.0, 100.5, 1.0, 1
        )
        confirmation = BarRecord(120, 99.0, 100.0, 98.0, 98.5, 1.0, 1)
        settle_processor._on_reference_bar(confirmation)
        live_after_confirmation = [
            dict(row) for row in settle_processor.state.iter_active_raids()
        ]
        endpoint = BarRecord(180, 101.0, 102.0, 100.5, 101.5, 1.0, 1)
        settle_processor._on_reference_bar(endpoint)

        settled = [dict(row) for row in settle_sinks.raids.rows]
        t1_settled = next(
            row for row in settled if row["raid_id"] == "T1-HIGH:raid:1"
        )
        t2_settled = next(
            row for row in settled if row["raid_id"] == "T2-HIGH:raid:1"
        )
        checks = {
            "t1_started_once": len(after_excursion) == 1,
            "t1_max_excursion_1_20": bool(
                after_excursion
                and abs(float(after_excursion[0]["max_excursion"]) - 1.2) < 1e-9
            ),
            "t1_prior_0": bool(
                after_excursion and after_excursion[0]["prior_raid_count"] == 0
            ),
            "t1_wick_did_not_add_raid": bool(
                len(after_return) == 1
                and after_return[0]["raid_id"] == "T1-HIGH:raid:1"
            ),
            "t1_still_live_after_return": bool(
                after_return and after_return[0]["return_ts_ns"] is not None
            ),
            "t1_not_ambiguous": not t1_sinks.raids.rows,
            "t1_non_primary_if_both_confirmed": (
                t1_settled["status"] == "CONFIRMED_NON_PRIMARY"
                and not t1_settled["primary_attribution"]
            ),
            "t2_primary_if_both_confirmed": bool(
                len(live_after_confirmation) == 1
                and live_after_confirmation[0]["raid_id"] == "T2-HIGH:raid:1"
                and live_after_confirmation[0]["primary_attribution"]
            ),
            "t2_completed_on_opposing_reference": (
                t2_settled["status"] == "COMPLETED"
            ),
            "t3_confirmation_timestamp_is_reference_close": (
                t2_settled["confirmation_ts_ns"] == confirmation.ts_event_ns
                and t2_settled["endpoint_ts_ns"] == endpoint.ts_event_ns
            ),
        }
        return {
            "checks": checks,
            "t1_after_excursion": after_excursion[0] if after_excursion else None,
            "t1_after_return": after_return[0] if after_return else None,
            "settled_raids": settled,
        }


def probe_atr_undefined_initial_observation_extreme() -> dict[str, Any]:
    """Characterize max-excursion tracking before an ATR-backed profile exists."""
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as tmp:
        config = Exp100CellConfig(
            venue="CTRADER",
            archive_symbol="EURUSD",
            instrument_id="EURUSD.CTrader",
            observation_minutes=15,
            confirmation_method="BREAKOUT_BAR",
            confirmation_reference="1H",
            level_config="PREVIOUS_1H",
        )
        sinks = Exp100Sinks(
            bar_marks=CollectingWriter(),
            levels=CollectingWriter(),
            raids=CollectingWriter(),
            tpo_profiles=CollectingWriter(),
            event_log=CollectingWriter(),
        )
        processor = Exp100Processor(
            config,
            Exp100StateStore(Path(tmp) / "state.sqlite"),
            sinks,
            MemoryGuard(limit_bytes=None, sample_every=10_000),
            auto_catalogue=False,
        )
        processor.seed_level("ATR-U-HIGH", price=100.0, side="HIGH")
        for minute in range(14):
            processor.on_one_minute_bar(_flat(minute, 100.8))
        processor.on_one_minute_bar(_bar(14, 100.8, 101.2, 100.8, 101.0))
        raid = dict(next(processor.state.iter_active_raids()))
        expected = 1.2
        observed = float(raid["max_excursion"])
        return {
            "population": "single synthetic 15m raid with ATR_UNDEFINED",
            "expected_completed_observation_max_excursion": expected,
            "observed_max_excursion": observed,
            "difference": observed - expected,
            "implementation_matches_completed_observation_extreme": (
                abs(observed - expected) < 1e-9
            ),
            "profile_generation": raid.get("profile_generation"),
            "profile_undefined_reason": raid.get("profile_undefined_reason"),
        }


def run_same_bar_return_golden() -> dict[str, Any]:
    """AMENDMENT-13: pierce-and-return on one observation bar stays live."""
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        config = Exp100CellConfig(
            venue="CTRADER",
            archive_symbol="EURUSD",
            instrument_id="EURUSD.CTrader",
            observation_minutes=15,
            confirmation_method="BREAKOUT_BAR",
            confirmation_reference="1H",
            level_config="PREVIOUS_1H",
        )
        sinks = Exp100Sinks(
            bar_marks=CollectingWriter(),
            levels=CollectingWriter(),
            raids=CollectingWriter(),
            tpo_profiles=CollectingWriter(),
            event_log=CollectingWriter(),
        )
        processor = Exp100Processor(
            config,
            Exp100StateStore(tmp_path / "state.sqlite"),
            sinks,
            MemoryGuard(limit_bytes=None, sample_every=10_000),
            auto_catalogue=False,
        )
        minute = 0
        for _ in range(20 * 15):
            processor.on_one_minute_bar(_flat(minute, 100.0))
            minute += 1
        processor.seed_level("SB-HIGH", price=100.00, side="HIGH")
        # Same completed observation bar: high beyond 100 and low returns to 100.
        for _offset in range(14):
            processor.on_one_minute_bar(_flat(minute, 100.10))
            minute += 1
        processor.on_one_minute_bar(_bar(minute, 100.10, 101.20, 99.90, 100.05))
        minute += 1
        snap = processor.snapshot()
        # Drive only the reference state transitions. Feeding another observation
        # above 100 would correctly start a second raid after this same-bar return,
        # which tests re-piercing rather than the single-raid golden expectation.
        processor._previous_reference = BarRecord(
            minute * MINUTE_NS, 100.0, 101.0, 99.0, 100.5, 1.0, 1
        )
        confirmation = BarRecord(
            (minute + 60) * MINUTE_NS, 99.0, 100.0, 98.0, 98.5, 1.0, 1
        )
        endpoint = BarRecord(
            (minute + 120) * MINUTE_NS, 101.0, 102.0, 100.5, 101.5, 1.0, 1
        )
        processor._on_reference_bar(confirmation)
        processor._on_reference_bar(endpoint)
        processor.finish(endpoint.ts_event_ns)
        raids = [dict(r) for r in sinks.raids.rows]
        sb = [r for r in raids if r.get("level_id") == "SB-HIGH"]
        checks = {
            "live_after_same_bar_pierce_return": snap["open_raids"] == 1,
            "one_terminal_raid": len(sb) == 1,
            "return_equals_sweep": bool(
                sb
                and sb[0].get("return_ts_ns") is not None
                and sb[0].get("return_ts_ns") == sb[0].get("sweep_ts_ns")
            ),
            "not_ambiguous": bool(sb and sb[0].get("status") != "AMBIGUOUS_INTRABAR"),
            "status_in_expected": bool(
                sb
                and sb[0].get("status")
                in {
                    "COMPLETED",
                    "CONFIRMED_NON_PRIMARY",
                    "FAILED_BREAKOUT",
                    "RIGHT_CENSORED_EXCURSION",
                    "RIGHT_CENSORED_CONFIRMATION",
                    "RIGHT_CENSORED_ENDPOINT",
                }
            ),
            "status": sb[0].get("status") if sb else None,
            "max_excursion": sb[0].get("max_excursion") if sb else None,
        }
        return {"checks": checks, "raid": sb[0] if sb else None, "snap": snap}


def probe_independent_raid_sample() -> dict[str, Any]:
    """Recompute 3 completed raids from observation bar_marks + level price."""
    cell_id = "ctrader-eurusd-15m-breakout_bar-1h-previous_1d"
    path = EMISSION_ROOT / cell_id
    raids = pl.read_parquet(path / "raids.parquet")
    marks = pl.read_parquet(path / "bar_marks.parquet")
    completed = raids.filter(pl.col("status") == "COMPLETED").head(3)
    marks = marks.sort("ts_event_ns")
    rows: list[dict[str, Any]] = []
    for raid in completed.iter_rows(named=True):
        price = float(raid["level_price"])
        side = raid["side"]
        sweep = int(raid["sweep_ts_ns"])
        ret = int(raid["return_ts_ns"])
        bars = marks.filter(
            (pl.col("ts_event_ns") >= sweep) & (pl.col("ts_event_ns") <= ret)
        )
        first = bars.head(1).row(0, named=True)
        last = bars.tail(1).row(0, named=True)
        if side == "HIGH":
            first_beyond = first["RealHigh"] > price
            last_return = last["RealLow"] <= price
            same_bar_return = first["RealLow"] <= price
            max_exc = float(bars["RealHigh"].max()) - price
        else:
            first_beyond = first["RealLow"] < price
            last_return = last["RealHigh"] >= price
            same_bar_return = first["RealHigh"] >= price
            max_exc = price - float(bars["RealLow"].min())
        rows.append(
            {
                "raid_id": raid["raid_id"],
                "side": side,
                "n_obs_bars_to_return": bars.height,
                "first_beyond": first_beyond,
                "same_bar_return": same_bar_return,
                "later_return": last_return and bars.height >= 2,
                "emitted_max_excursion": raid["max_excursion"],
                "recomputed_obs_max_excursion": max_exc,
                "obs_max_matches_or_exceeds": max_exc + 1e-12 >= float(raid["max_excursion"]),
            }
        )
    return {"cell_id": cell_id, "rows": rows}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "past_train": probe_past_train(),
        "destroy": probe_destroy_cells(),
        "golden": run_golden(),
        "atr_undefined_initial_observation_extreme": (
            probe_atr_undefined_initial_observation_extreme()
        ),
        "same_bar_return_golden": run_same_bar_return_golden(),
        "independent_raid_sample": probe_independent_raid_sample(),
    }
    (OUT_DIR / "probe_integrity.json").write_text(
        json.dumps(report, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
