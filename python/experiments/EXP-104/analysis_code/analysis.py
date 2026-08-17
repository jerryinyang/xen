"""EXP-104 adapter: raid-regime contrasts and causal frequency census."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import polars as pl

from xen.liqswp_analysis.adapter import BaseContrastAdapter, make_fixture_frame
from xen.liqswp_analysis.contract import IntegrityStatus
from xen.liqswp_analysis.runtime import run_fixture as _run_fixture
from xen.liqswp_analysis.runtime import run_live
from xen.liqswp_analysis.source import scan_train_columns, validate_source_contract
from xen.liqswp_analysis.statistics import circular_cluster_indices

EXPERIMENT = "EXP-104"
LABEL_COLUMN = "raid_regime"
SEEDS = tuple(range(5))
DEFAULT_N_BOOT = 10_000
DEFAULT_DESTROYS = 2_000
CONTROL_GROUP_COLUMNS = (
    "archive_symbol",
    "timeframe",
    "confirmation_method",
    "confirmation_reference",
    "side",
    "config",
    "status",
    "primary_completed",
)
# 5 bits: duration_ns is the declared alias of swing_duration_ns (not duplicated)
CONTROL_NULL_COLUMNS = (
    "swing_price",
    "swing_bps",
    "swing_atr",
    "duration_ns",
    "strong_move",
)

# Frequency block lengths: one-day blocks for 15m/30m/1h + half/double
# 15m: 96 bars/day, half=48, double=192
# 30m: 48 bars/day, half=24, double=96
# 1h: 24 bars/day, half=12, double=48
FREQUENCY_BLOCK_LENGTHS = (12, 24, 48, 96, 192)
FREQUENCY_BLOCK_LENGTHS_DEFAULT = (24, 48, 96)  # 1h, 30m, 15m one-day blocks


def _build_frequency_units(
    bar_marks: Sequence[dict[str, Any]], raids: Sequence[dict[str, Any]]
) -> list[dict[str, Any]]:
    marks = sorted(bar_marks, key=lambda row: int(row["ts_event_ns"]))
    timestamps = [int(mark["ts_event_ns"]) for mark in marks]
    if len(timestamps) != len(set(timestamps)):
        raise RuntimeError("observation mark timestamps are not unique")
    mark_index = {timestamp: index for index, timestamp in enumerate(timestamps)}
    raid_ids = Counter(row.get("raid_id") for row in raids)
    if any(count != 1 for count in raid_ids.values()):
        raise RuntimeError("raid_id frequency join is not one-to-one")
    by_timestamp: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for raid in raids:
        timestamp = int(raid["sweep_ts_ns"])
        if timestamp not in mark_index:
            raise RuntimeError("raid sweep timestamp has no observation mark")
        if mark_index[timestamp] == 0:
            raise RuntimeError("raid sweep has no preceding observation mark")
        by_timestamp[timestamp].append(raid)
    units: list[dict[str, Any]] = []
    for index in range(1, len(marks)):
        timestamp = timestamps[index]
        preceding = marks[index - 1].get("regime")
        starts = tuple(sorted(by_timestamp.get(timestamp, ()), key=lambda row: str(row["raid_id"])))
        for raid in starts:
            if raid.get(LABEL_COLUMN) != preceding:
                raise RuntimeError("raid regime provenance mismatch")
        units.append({"preceding_regime": preceding, "starts": starts})
    return units


def _frequency_from_units(units: Sequence[dict[str, Any]], block_length: int) -> dict[str, Any]:
    regimes = ("LOW", "MID", "HIGH")
    exposure = Counter({regime: 0 for regime in regimes})
    starts = Counter({regime: 0 for regime in regimes})
    excluded = Counter()
    warmup_undefined_exposure = Counter()
    for unit in units:
        regime = unit["preceding_regime"]
        if regime in regimes:
            exposure[regime] += 1
            starts[regime] += len(unit["starts"])
        elif regime in ("REGIME_WARMUP", "ATR_UNDEFINED"):
            warmup_undefined_exposure[regime] += 1
        else:
            excluded[str(regime)] += 1
    rates = {
        regime: (1000.0 * starts[regime] / exposure[regime] if exposure[regime] else None)
        for regime in regimes
    }
    return {
        "exposure": dict(exposure),
        "starts": dict(starts),
        "rates_per_1000": rates,
        "contrasts_minus_mid": {
            regime: (
                rates[regime] - rates["MID"]
                if rates[regime] is not None and rates["MID"] is not None
                else None
            )
            for regime in ("LOW", "HIGH")
        },
        "block_length": int(block_length),
        "empty_exposure": [regime for regime in regimes if exposure[regime] == 0],
        "excluded_exposure": dict(excluded),
        "warmup_undefined_exposure": dict(warmup_undefined_exposure),
        "eligible_marks": len(units),
    }


def frequency_rate(
    bar_marks: Sequence[dict[str, Any]],
    raids: Sequence[dict[str, Any]],
    *,
    block_length: int,
) -> dict[str, Any]:
    """Use the preceding completed observation mark as causal exposure."""
    return _frequency_from_units(_build_frequency_units(bar_marks, raids), block_length)


def _frequency_bootstrap_units(
    units: Sequence[dict[str, Any]],
    *,
    block_length: int,
    n_boot: int,
    seeds: Sequence[int],
) -> dict[str, Any]:
    seed_rows = []
    samples_by_regime: dict[str, list[float]] = {"LOW": [], "HIGH": []}
    for seed in seeds:
        rng = np.random.default_rng(seed)
        samples: dict[str, list[float]] = {"LOW": [], "HIGH": []}
        for _ in range(n_boot):
            indices = circular_cluster_indices(len(units), block_length, rng)
            estimate = _frequency_from_units([units[int(index)] for index in indices], block_length)
            for regime in samples:
                value = estimate["contrasts_minus_mid"][regime]
                if value is not None and np.isfinite(value):
                    samples[regime].append(float(value))
                    samples_by_regime[regime].append(float(value))
        seed_rows.append(
            {
                "seed": int(seed),
                "n_boot": int(n_boot),
                "finite_draws": {key: len(values) for key, values in samples.items()},
                "intervals": {
                    key: (
                        [float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))]
                        if values
                        else None
                    )
                    for key, values in samples.items()
                },
            }
        )
    return {
        "block_length": block_length,
        "seeds": seed_rows,
        "intervals": {
            key: (
                [float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))]
                if values
                else None
            )
            for key, values in samples_by_regime.items()
        },
    }


def frequency_bootstrap(
    bar_marks: Sequence[dict[str, Any]],
    raids: Sequence[dict[str, Any]],
    *,
    block_length: int = 96,
    n_boot: int = DEFAULT_N_BOOT,
    seeds: Sequence[int] = SEEDS,
) -> dict[str, Any]:
    units = _build_frequency_units(bar_marks, raids)
    if not units:
        return {"reason": "EMPTY_EXPOSURE", "intervals": {}, "seeds": []}
    return _frequency_bootstrap_units(units, block_length=block_length, n_boot=n_boot, seeds=seeds)


class Adapter(BaseContrastAdapter):
    experiment = EXPERIMENT
    label_column = LABEL_COLUMN
    contrasts = (("LOW", "MID"), ("HIGH", "MID"))
    control_group_columns = CONTROL_GROUP_COLUMNS
    control_null_columns = CONTROL_NULL_COLUMNS
    # EXP-104: joint resampling (default independent_arms=False)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._frequency_live: list[dict[str, Any]] = []

    def live_frame(
        self, source_root: Path, gate_path: Path
    ) -> tuple[pl.DataFrame, dict[str, Any], IntegrityStatus]:
        self._live_mode = True
        # Default to EXP-100 authoritative gate
        attestation = validate_source_contract(self.source_spec(source_root, gate_path))
        source = {
            "mode": "live",
            "root": str(source_root),
            "gate": str(gate_path),
            "attestation": attestation.evidence,
        }
        if not attestation.integrity.blocking_pass:
            return pl.DataFrame(), source, attestation.integrity
        raid_frames: list[pl.LazyFrame] = []
        mark_frames: list[pl.LazyFrame] = []
        profile_key_frames: list[pl.LazyFrame] = []
        for raid_path in attestation.paths:
            source_cell = raid_path.parent.name
            raids = scan_train_columns(
                [raid_path],
                columns=self.required_columns,
                train_end_column="endpoint_ts_ns",
                train_end_ns=1_700_611_200 * 1_000_000_000,
            ).with_columns(pl.lit(source_cell).alias("source_cell"))
            raid_frames.append(raids)
            marks = (
                pl.scan_parquet(raid_path.with_name("bar_marks.parquet"))
                .select("ts_event_ns", "regime")
                .sort("ts_event_ns")
                .with_columns(
                    pl.col("ts_event_ns").shift(1).alias("regime_source_ts_ns"),
                    pl.col("regime").shift(1).alias("causal_regime"),
                    pl.lit(source_cell).alias("source_cell"),
                )
            )
            mark_frames.append(marks)
            profile_key_frames.append(
                pl.scan_parquet(raid_path.with_name("tpo_profiles.parquet"))
                .select("raid_id", "profile_generation")
                .with_columns(pl.lit(source_cell).alias("source_cell"))
            )
        raids = pl.concat(raid_frames).collect(engine="streaming")
        marks = pl.concat(mark_frames).collect(engine="streaming")
        profiles = pl.concat(profile_key_frames).collect(engine="streaming")
        key = ["source_cell", "raid_id", "profile_generation"]
        duplicate_profiles = profiles.select(pl.struct(key).is_duplicated().sum()).item()
        unmatched_profiles = raids.join(profiles, on=key, how="anti").height
        extra_profiles = profiles.join(raids.select(key), on=key, how="anti").height
        joined = raids.join(
            marks.select("source_cell", "ts_event_ns", "regime_source_ts_ns", "causal_regime"),
            left_on=["source_cell", "sweep_ts_ns"],
            right_on=["source_cell", "ts_event_ns"],
            how="left",
        ).with_columns(
            pl.when(pl.struct(key).is_not_null())
            .then(pl.lit("MATCHED"))
            .otherwise(pl.lit("MISSING_PROFILE"))
            .alias("profile_join_reason")
        )
        # Determine profile membership without adding outcome-bearing profile fields.
        joined = (
            joined.join(
                profiles.with_columns(pl.lit(True).alias("__profile_matched")), on=key, how="left"
            )
            .with_columns(
                pl.when(pl.col("__profile_matched").fill_null(False))
                .then(pl.lit("MATCHED"))
                .otherwise(pl.lit("MISSING_PROFILE"))
                .alias("profile_join_reason")
            )
            .drop("__profile_matched")
        )
        missing_mark = joined.filter(pl.col("regime_source_ts_ns").is_null()).height
        regime_mismatch = joined.filter(
            pl.col(LABEL_COLUMN).is_not_null()
            & pl.col("causal_regime").is_not_null()
            & (pl.col(LABEL_COLUMN) != pl.col("causal_regime"))
        ).height
        identity = raids.select("source_cell", *self.stratum_columns).unique()
        marked_exposure = marks.filter(pl.col("causal_regime").is_in(["LOW", "MID", "HIGH"])).join(
            identity, on="source_cell", how="left"
        )
        exposure = marked_exposure.group_by(*self.stratum_columns, "causal_regime").len(
            name="exposure"
        )
        starts = joined.group_by(*self.stratum_columns, LABEL_COLUMN).agg(
            pl.col("raid_id").n_unique().alias("starts")
        )
        frequency_rows = (
            exposure.join(
                starts,
                left_on=[*self.stratum_columns, "causal_regime"],
                right_on=[*self.stratum_columns, LABEL_COLUMN],
                how="left",
            )
            .with_columns(pl.col("starts").fill_null(0))
            .to_dicts()
        )
        starts_by_mark = joined.group_by("source_cell", "sweep_ts_ns").agg(
            pl.col("raid_id").n_unique().alias("starts")
        )
        units_frame = marked_exposure.join(
            starts_by_mark,
            left_on=["source_cell", "ts_event_ns"],
            right_on=["source_cell", "sweep_ts_ns"],
            how="left",
        ).with_columns(pl.col("starts").fill_null(0))
        sensitivities = []
        for partition in units_frame.partition_by(list(self.stratum_columns), maintain_order=True):
            stratum = {column: partition[column][0] for column in self.stratum_columns}
            units = [
                {"preceding_regime": regime, "starts": (None,) * int(count)}
                for regime, count in zip(
                    partition["causal_regime"].to_list(),
                    partition["starts"].to_list(),
                    strict=True,
                )
            ]
            sensitivities.append(
                {
                    "stratum": stratum,
                    "sensitivities": {
                        str(length): _frequency_bootstrap_units(
                            units,
                            block_length=length,
                            n_boot=self.n_boot,
                            seeds=self.seeds,
                        )
                        for length in FREQUENCY_BLOCK_LENGTHS_DEFAULT
                    },
                }
            )
        self._frequency_live = [{"census": frequency_rows, "uncertainty": sensitivities}]
        join_evidence = {
            "duplicate_profile_keys": int(duplicate_profiles),
            "unmatched_raids": unmatched_profiles,
            "extra_profiles": extra_profiles,
            "missing_preceding_marks": missing_mark,
            "regime_mismatches": regime_mismatch,
        }
        source["profile_regime_join"] = join_evidence
        reasons = list(attestation.integrity.reasons)
        if duplicate_profiles or unmatched_profiles or extra_profiles:
            reasons.append("VOID_PROFILE_JOIN_MISMATCH")
        if missing_mark or regime_mismatch:
            reasons.append("VOID_REGIME_PROVENANCE")
        unique = tuple(dict.fromkeys(reasons))
        return joined, source, IntegrityStatus(not unique, unique, join_evidence)

    def fixture_frame(self) -> pl.DataFrame:
        frame = make_fixture_frame(
            (("MID", "LOW"), ("MID", "HIGH")),
            label_column=LABEL_COLUMN,
            config_value="FIXTURE_CONFIG",
        )
        return frame.with_columns(
            (pl.col("sweep_ts_ns") - 1).alias("regime_source_ts_ns"),
            pl.lit("MATCHED").alias("profile_join_reason"),
        )

    def extra_integrity(self, frame: pl.DataFrame) -> IntegrityStatus:
        reasons: list[str] = []
        if "regime_source_ts_ns" not in frame.columns:
            reasons.append("VOID_REGIME_PROVENANCE")
        elif frame.filter(pl.col("regime_source_ts_ns") >= pl.col("sweep_ts_ns")).height:
            reasons.append("VOID_NONCAUSAL_REGIME")
        if "profile_join_reason" not in frame.columns:
            reasons.append("VOID_PROFILE_JOIN_EVIDENCE")
        evidence = {
            "causal_regime_rows": (
                frame.filter(pl.col("regime_source_ts_ns") < pl.col("sweep_ts_ns")).height
                if "regime_source_ts_ns" in frame.columns
                else 0
            ),
            "profile_join": (
                dict(Counter(str(value) for value in frame["profile_join_reason"].to_list()))
                if "profile_join_reason" in frame.columns
                else {}
            ),
        }
        unique = tuple(dict.fromkeys(reasons))
        return IntegrityStatus(not unique, unique, evidence)

    def extra(self, frame: pl.DataFrame) -> dict[str, Any]:
        extra = super().extra(frame)
        regimes = Counter(str(value) for value in frame[LABEL_COLUMN].to_list())
        unmatched = (
            frame.filter(pl.col("profile_join_reason") != "MATCHED").height
            if "profile_join_reason" in frame.columns
            else frame.height
        )
        extra.update(
            {
                "frequency_census": self._frequency_live
                or {"starts": dict(regimes), "exposure": "fixture-only"},
                "regime_census": dict(regimes),
                "confirmation_regime_census": dict(
                    Counter(str(value) for value in frame["confirmation_regime"].to_list())
                ),
                "endpoint_regime_census": dict(
                    Counter(str(value) for value in frame["endpoint_regime"].to_list())
                ),
                "profile_join": {"unmatched_raids": unmatched},
            }
        )
        return extra


def run_fixture(
    *,
    n_destroy: int = DEFAULT_DESTROYS,
    seeds: Sequence[int] = SEEDS,
    output: Path | None = None,
    n_boot: int = 10,
) -> dict[str, Any]:
    destination = output or Path(__file__).resolve().parents[1] / "results/fixture_integrity.json"
    return _run_fixture(Adapter(n_boot=n_boot, n_destroy=n_destroy, seeds=seeds), destination)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fixture", "--fixture-only", "--smoke", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--source-root", "--root", type=Path)
    parser.add_argument("--gate", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    experiment_root = Path(__file__).resolve().parents[1]
    adapter = Adapter()
    if args.live:
        source = args.source_root or experiment_root.parents[2] / "data/nautilus_runs/EXP-100/full"
        gate = args.gate or experiment_root / "results/estimand_validation.json"
        run_live(
            adapter,
            source,
            gate,
            args.output or experiment_root / "results/analysis_results.json",
        )
    else:
        _run_fixture(adapter, args.output or experiment_root / "results/fixture_integrity.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


