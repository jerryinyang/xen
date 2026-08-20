"""EXP-104 adapter: raid-regime contrasts and causal frequency census."""

from __future__ import annotations

import argparse
import os
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import polars as pl

from xen.liqswp_analysis.adapter import BaseContrastAdapter, make_fixture_frame
from xen.liqswp_analysis.contract import IntegrityStatus
from xen.liqswp_analysis.runtime import run_fixture as _run_fixture
from xen.liqswp_analysis.runtime import run_live
from xen.liqswp_analysis.source import (
    key_join_evidence,
    scan_train_columns,
    validate_source_contract,
)

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
# 1h / live 60m: 24 bars/day, half=12, double=48
FREQUENCY_BLOCK_LENGTHS = (12, 24, 48, 96, 192)
FREQUENCY_BLOCK_LENGTHS_DEFAULT = (24, 48, 96)  # unknown TF: 1h/30m/15m one-day blocks
# Per-timeframe primary one-day block L with sensitivities L/2 and 2L.
# Live observation cells are labelled 60m (confirmation refs stay 1H/4H).
FREQUENCY_BLOCKS_BY_TIMEFRAME = {
    "15m": (48, 96, 192),  # L=96
    "30m": (24, 48, 96),  # L=48
    "1h": (12, 24, 48),  # L=24
    "60m": (12, 24, 48),  # L=24; same as 1h
}


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


_REGIME_CODE = {
    "LOW": 0,
    "MID": 1,
    "HIGH": 2,
    "REGIME_WARMUP": 3,
    "ATR_UNDEFINED": 4,
}
_REGIME_NAMES = ("LOW", "MID", "HIGH")


def _start_count(value: Any) -> int:
    if isinstance(value, (int, np.integer)):
        return int(value)
    return len(value)


def _encode_frequency_marks(
    regimes: Sequence[Any], starts: Sequence[Any]
) -> tuple[np.ndarray, np.ndarray]:
    codes = np.fromiter(
        (_REGIME_CODE.get(str(regime) if regime is not None else "", 5) for regime in regimes),
        dtype=np.int8,
        count=len(regimes),
    )
    counts = np.fromiter(
        (_start_count(value) for value in starts), dtype=np.int64, count=len(starts)
    )
    return codes, counts


def _frequency_from_codes(
    codes: np.ndarray, start_counts: np.ndarray, block_length: int
) -> dict[str, Any]:
    tallies = np.bincount(codes.astype(np.intp), minlength=6)
    start_sums = np.bincount(
        codes.astype(np.intp), weights=start_counts.astype(np.float64), minlength=6
    )
    exposure = {name: int(tallies[index]) for index, name in enumerate(_REGIME_NAMES)}
    starts = {name: int(start_sums[index]) for index, name in enumerate(_REGIME_NAMES)}
    warmup_undefined = {
        name: int(tallies[index])
        for name, index in (("REGIME_WARMUP", 3), ("ATR_UNDEFINED", 4))
        if int(tallies[index])
    }
    excluded = {"other": int(tallies[5])} if int(tallies[5]) else {}
    rates = {
        name: (1000.0 * starts[name] / exposure[name] if exposure[name] else None)
        for name in _REGIME_NAMES
    }
    return {
        "exposure": exposure,
        "starts": starts,
        "rates_per_1000": rates,
        "contrasts_minus_mid": {
            name: (
                rates[name] - rates["MID"]
                if rates[name] is not None and rates["MID"] is not None
                else None
            )
            for name in ("LOW", "HIGH")
        },
        "block_length": int(block_length),
        "empty_exposure": [name for name in _REGIME_NAMES if exposure[name] == 0],
        "excluded_exposure": excluded,
        "warmup_undefined_exposure": warmup_undefined,
        "eligible_marks": int(sum(exposure.values())),
    }


def _frequency_from_units(units: Sequence[dict[str, Any]], block_length: int) -> dict[str, Any]:
    codes, start_counts = _encode_frequency_marks(
        [unit["preceding_regime"] for unit in units],
        [unit["starts"] for unit in units],
    )
    return _frequency_from_codes(codes, start_counts, block_length)


def _py_value(value: Any) -> Any:
    """Plain-Python scalar (polars scalars expose .item)."""
    return value.item() if hasattr(value, "item") else value


def _partition_payloads(
    units_frame: pl.DataFrame,
    stratum_columns: Sequence[str],
    n_boot: int,
    seeds: Sequence[int],
) -> list[dict[str, Any]]:
    """Census input for each stratum partition as plain, picklable data."""
    payloads: list[dict[str, Any]] = []
    for partition in units_frame.partition_by(list(stratum_columns), maintain_order=True):
        stratum = {column: _py_value(partition[column][0]) for column in stratum_columns}
        payloads.append(
            {
                "stratum": stratum,
                "blocks": FREQUENCY_BLOCKS_BY_TIMEFRAME.get(
                    str(stratum.get("timeframe")),
                    FREQUENCY_BLOCK_LENGTHS_DEFAULT,
                ),
                "n_boot": n_boot,
                "seeds": tuple(seeds),
                "causal_regime": partition["causal_regime"].to_list(),
                "starts": partition["starts"].to_list(),
            }
        )
    return payloads


def _frequency_arm_table(
    marked_exposure: pl.DataFrame,
    starts: pl.DataFrame,
    stratum_columns: Sequence[str],
) -> pl.DataFrame:
    """LOW/MID/HIGH rows per stratum, including EMPTY_EXPOSURE arms.

    Warmup/undefined marks stay out of this table; they are disclosure on the
    census, never converted to an arm.
    """
    arm_exposure = (
        marked_exposure.filter(pl.col("causal_regime").is_in(list(_REGIME_NAMES)))
        .group_by(*stratum_columns, "causal_regime")
        .len(name="exposure")
    )
    grid = marked_exposure.select(*stratum_columns).unique().join(
        pl.DataFrame({"causal_regime": list(_REGIME_NAMES)}),
        how="cross",
    )
    return (
        grid.join(
            arm_exposure,
            on=[*stratum_columns, "causal_regime"],
            how="left",
        )
        .join(
            starts,
            left_on=[*stratum_columns, "causal_regime"],
            right_on=[*stratum_columns, LABEL_COLUMN],
            how="left",
        )
        .with_columns(
            pl.col("exposure").fill_null(0),
            pl.col("starts").fill_null(0),
        )
        .with_columns(
            pl.when(pl.col("exposure") == 0)
            .then(pl.lit("EMPTY_EXPOSURE"))
            .otherwise(pl.lit(None))
            .alias("empty_exposure_reason")
        )
    )


def _run_census(
    payloads: Sequence[dict[str, Any]], workers: int
) -> list[dict[str, Any]]:
    """Census over strata. Processes (not threads) when workers>1: the payloads
    are small plain data (so no polars pickling), the draw loop is numpy-heavy,
    and processes sidestep the GIL. map() preserves order, so outputs are
    identical to the sequential path."""
    if workers > 1 and payloads:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            return list(pool.map(_census_partition, payloads, chunksize=1))
    return [_census_partition(payload) for payload in payloads]


def _census_partition(payload: dict[str, Any]) -> dict[str, Any]:
    """Frequency census for one stratum partition: observed rates plus block-
    bootstrap sensitivities. Stateless and deterministic per seed."""
    stratum = payload["stratum"]
    blocks = payload["blocks"]
    codes, start_counts = _encode_frequency_marks(
        payload["causal_regime"], payload["starts"]
    )
    observed = _frequency_from_codes(
        codes, start_counts, block_length=blocks[len(blocks) // 2]
    )
    sensitivities = {
        str(length): _frequency_bootstrap_codes(
            codes,
            start_counts,
            block_length=length,
            n_boot=payload["n_boot"],
            seeds=payload["seeds"],
        )
        for length in blocks
    }
    return {"stratum": stratum, "observed": observed, "sensitivities": sensitivities}


def frequency_rate(
    bar_marks: Sequence[dict[str, Any]],
    raids: Sequence[dict[str, Any]],
    *,
    block_length: int,
) -> dict[str, Any]:
    """Use the preceding completed observation mark as causal exposure."""
    return _frequency_from_units(_build_frequency_units(bar_marks, raids), block_length)


def _prefix_mark_tables(
    codes: np.ndarray, start_counts: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Inclusive prefix counts/start-sums for LOW/MID/HIGH (cols 0..2)."""
    n = int(codes.size)
    inc_c = np.zeros((n, 3), dtype=np.int64)
    inc_s = np.zeros((n, 3), dtype=np.int64)
    eligible = (codes >= 0) & (codes <= 2)
    if eligible.any():
        rows = np.nonzero(eligible)[0]
        cols = codes[eligible].astype(np.intp)
        inc_c[rows, cols] = 1
        inc_s[rows, cols] = start_counts[eligible]
    prefix_c = np.zeros((n + 1, 3), dtype=np.int64)
    prefix_s = np.zeros((n + 1, 3), dtype=np.int64)
    prefix_c[1:] = np.cumsum(inc_c, axis=0)
    prefix_s[1:] = np.cumsum(inc_s, axis=0)
    return prefix_c, prefix_s


def _add_circular_blocks(
    prefix_c: np.ndarray,
    prefix_s: np.ndarray,
    starts: np.ndarray,
    take: int,
    n: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Sum prefix tables over circular ranges [start, start+take)."""
    out_shape = (*starts.shape, 3)
    if take <= 0 or starts.size == 0:
        zeros = np.zeros(out_shape, dtype=np.int64)
        return zeros, zeros
    end = starts + int(take)
    wrap = end > n
    counts = prefix_c[np.minimum(end, n)] - prefix_c[starts]
    sums = prefix_s[np.minimum(end, n)] - prefix_s[starts]
    if np.any(wrap):
        wrapped_starts = starts[wrap]
        wrapped_end = end[wrap] - n
        counts = np.array(counts, copy=True)
        sums = np.array(sums, copy=True)
        counts[wrap] = prefix_c[n] - prefix_c[wrapped_starts] + prefix_c[wrapped_end]
        sums[wrap] = prefix_s[n] - prefix_s[wrapped_starts] + prefix_s[wrapped_end]
    return counts, sums


def _frequency_contrasts_from_totals(
    exposure: np.ndarray, start_sums: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """LOW-minus-MID and HIGH-minus-MID rate contrasts; NaN if an arm is empty."""
    rates = np.where(
        exposure > 0, 1000.0 * start_sums / np.maximum(exposure, 1), np.nan
    )
    mid = rates[..., 1]
    return rates[..., 0] - mid, rates[..., 2] - mid


def _interval_from_values(values: np.ndarray) -> list[float] | None:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return None
    return [float(np.quantile(finite, 0.025)), float(np.quantile(finite, 0.975))]


def _frequency_bootstrap_codes(
    codes: np.ndarray,
    start_counts: np.ndarray,
    *,
    block_length: int,
    n_boot: int,
    seeds: Sequence[int],
) -> dict[str, Any]:
    """Registered circular-block frequency bootstrap on mark codes.

    Same starts and block layout as circular_cluster_indices (one
    rng.integers(0, n) per block, last block truncated). Contrasts are the
    sums of those circular ranges, via prefix tables — identical to gathering
    every resampled mark, without building an 80k-index array per draw.
    """
    n_units = int(codes.size)
    if n_units < 1 or int(n_boot) < 1:
        empty = {"LOW": None, "HIGH": None}
        return {
            "block_length": int(block_length),
            "seeds": [
                {
                    "seed": int(seed),
                    "n_boot": int(n_boot),
                    "finite_draws": {"LOW": 0, "HIGH": 0},
                    "intervals": empty,
                }
                for seed in seeds
            ],
            "intervals": empty,
        }
    effective = 1 if n_units == 1 else min(max(1, int(block_length)), n_units - 1)
    n_blocks = (n_units + effective - 1) // effective
    remainder = n_units - (n_blocks - 1) * effective
    prefix_c, prefix_s = _prefix_mark_tables(codes, start_counts)
    seed_rows = []
    all_low: list[np.ndarray] = []
    all_high: list[np.ndarray] = []
    for seed in seeds:
        rng = np.random.default_rng(seed)
        # C-order (n_boot, n_blocks) matches n_boot sequential size=n_blocks draws.
        block_starts = rng.integers(0, n_units, size=(int(n_boot), n_blocks))
        if n_blocks == 1:
            exposure, start_sums = _add_circular_blocks(
                prefix_c, prefix_s, block_starts[:, 0], remainder, n_units
            )
        else:
            head_c, head_s = _add_circular_blocks(
                prefix_c, prefix_s, block_starts[:, :-1], effective, n_units
            )
            last_c, last_s = _add_circular_blocks(
                prefix_c, prefix_s, block_starts[:, -1], remainder, n_units
            )
            exposure = head_c.sum(axis=1) + last_c
            start_sums = head_s.sum(axis=1) + last_s
        low, high = _frequency_contrasts_from_totals(exposure, start_sums)
        seed_rows.append(
            {
                "seed": int(seed),
                "n_boot": int(n_boot),
                "finite_draws": {
                    "LOW": int(np.isfinite(low).sum()),
                    "HIGH": int(np.isfinite(high).sum()),
                },
                "intervals": {
                    "LOW": _interval_from_values(low),
                    "HIGH": _interval_from_values(high),
                },
            }
        )
        all_low.append(low)
        all_high.append(high)
    stacked_low = np.concatenate(all_low) if all_low else np.asarray([], dtype=float)
    stacked_high = np.concatenate(all_high) if all_high else np.asarray([], dtype=float)
    return {
        "block_length": int(block_length),
        "seeds": seed_rows,
        "intervals": {
            "LOW": _interval_from_values(stacked_low),
            "HIGH": _interval_from_values(stacked_high),
        },
    }


def _frequency_bootstrap_units(
    units: Sequence[dict[str, Any]],
    *,
    block_length: int,
    n_boot: int,
    seeds: Sequence[int],
) -> dict[str, Any]:
    codes, start_counts = _encode_frequency_marks(
        [unit["preceding_regime"] for unit in units],
        [unit["starts"] for unit in units],
    )
    return _frequency_bootstrap_codes(
        codes,
        start_counts,
        block_length=block_length,
        n_boot=n_boot,
        seeds=seeds,
    )


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
        profile_key = ["source_cell", "raid_id", "profile_generation"]
        join_counts = key_join_evidence(raids, profiles, profile_key)
        joined = raids.join(
            marks.select("source_cell", "ts_event_ns", "regime_source_ts_ns", "causal_regime"),
            left_on=["source_cell", "sweep_ts_ns"],
            right_on=["source_cell", "ts_event_ns"],
            how="left",
        )
        joined = (
            joined.join(
                profiles.with_columns(pl.lit(True).alias("__profile_matched")),
                on=profile_key,
                how="left",
                nulls_equal=True,
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
        join_evidence = {
            **join_counts,
            "missing_preceding_marks": missing_mark,
            "regime_mismatches": regime_mismatch,
        }
        source["profile_regime_join"] = join_evidence
        reasons = list(attestation.integrity.reasons)
        if (
            join_counts["duplicate_profile_keys"]
            or join_counts["unmatched_raids"]
            or join_counts["extra_profiles"]
        ):
            reasons.append("VOID_PROFILE_JOIN_MISMATCH")
        if missing_mark or regime_mismatch:
            reasons.append("VOID_REGIME_PROVENANCE")
        unique = tuple(dict.fromkeys(reasons))
        if unique:
            # Integrity first: do not spend the frequency bootstrap on a voided source.
            return joined, source, IntegrityStatus(False, unique, join_evidence)
        identity = raids.select("source_cell", *self.stratum_columns).unique()
        # Preceding mark must exist. Keep warmup/undefined in the census;
        # do not convert them to LOW/MID/HIGH arms.
        marked_exposure = marks.filter(pl.col("causal_regime").is_not_null()).join(
            identity, on="source_cell", how="left"
        )
        starts = joined.group_by(*self.stratum_columns, LABEL_COLUMN).agg(
            pl.col("raid_id").n_unique().alias("starts")
        )
        frequency_rows = _frequency_arm_table(
            marked_exposure, starts, self.stratum_columns
        ).to_dicts()
        starts_by_mark = joined.group_by("source_cell", "sweep_ts_ns").agg(
            pl.col("raid_id").n_unique().alias("starts")
        )
        units_frame = marked_exposure.join(
            starts_by_mark,
            left_on=["source_cell", "ts_event_ns"],
            right_on=["source_cell", "sweep_ts_ns"],
            how="left",
        ).with_columns(pl.col("starts").fill_null(0))
        payloads = _partition_payloads(units_frame, self.stratum_columns, self.n_boot, self.seeds)
        results = _run_census(payloads, self.workers)
        observed_by_stratum: dict[tuple[Any, ...], dict[str, Any]] = {}
        sensitivities: list[dict[str, Any]] = []
        for result in results:
            stratum_key = tuple(result["stratum"][column] for column in self.stratum_columns)
            observed_by_stratum[stratum_key] = result["observed"]
            sensitivities.append(
                {"stratum": result["stratum"], "sensitivities": result["sensitivities"]}
            )
        for row in frequency_rows:
            observed = observed_by_stratum.get(
                tuple(row[column] for column in self.stratum_columns)
            )
            if observed is None:
                continue
            regime = row["causal_regime"]
            row["rate_per_1000"] = observed["rates_per_1000"].get(regime)
            row["contrast_minus_mid"] = observed["contrasts_minus_mid"].get(regime)
            row["warmup_undefined_exposure"] = observed["warmup_undefined_exposure"]
            row["excluded_exposure"] = observed["excluded_exposure"]
            row["eligible_marks"] = observed["eligible_marks"]
        self._frequency_live = [{"census": frequency_rows, "uncertainty": sensitivities}]
        return joined, source, IntegrityStatus(True, (), join_evidence)

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
    if args.live:
        adapter = Adapter(
            workers=int(os.environ.get("XEN_WORKERS", "1")),
            n_boot=int(os.environ.get("XEN_N_BOOT", str(DEFAULT_N_BOOT))),
        )
        source = args.source_root or experiment_root.parents[2] / "data/nautilus_runs/EXP-100/full"
        gate = args.gate or experiment_root.parent / "EXP-100/results/estimand_validation.json"
        run_live(
            adapter,
            source,
            gate,
            args.output or experiment_root / "results/analysis_results.json",
        )
    else:
        _run_fixture(
            Adapter(n_boot=10, n_destroy=DEFAULT_DESTROYS, seeds=SEEDS),
            args.output or experiment_root / "results/fixture_integrity.json",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


