"""EXP-103 adapter: TPO value-gap and tight-gap outcome contrasts."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import polars as pl

from xen.liqswp_analysis.adapter import BaseContrastAdapter, make_fixture_frame
from xen.liqswp_analysis.contract import IntegrityStatus
from xen.liqswp_analysis.destroy import (
    DestroySpec,
    apply_destroy_mappings,
    build_destroy_mappings,
    derange_indices as _derange_indices,
)
from xen.liqswp_analysis.runtime import run_fixture as _run_fixture
from xen.liqswp_analysis.runtime import run_live
from xen.liqswp_analysis.source import join_profiles_left as _join_profiles_frame
from xen.liqswp_analysis.source import scan_train_columns, validate_source_contract

EXPERIMENT = "EXP-103"
LABEL_COLUMN = "tight_gap"
LENGTHS = (2, 5, 10)
SEEDS = tuple(range(5))
DEFAULT_N_BOOT = 10_000
DEFAULT_DESTROYS = 2_000
REQUIRED_OUTCOME = (
    "swing_price",
    "swing_bps",
    "swing_atr",
    "swing_duration_ns",
    "duration_ns",
    "strong_move",
)
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
CONTROL_NULL_COLUMNS = (
    "swing_price",
    "swing_bps",
    "swing_atr",
    "swing_duration_ns",
    "strong_move",
)
PROFILE_COLUMNS = (
    "profile_status",
    "bracket_count",
    "poc",
    "val",
    "vah",
    "bin_width",
    "atr_unit",
    "va_width",
    "gap_span",
    "gap_span_atr",
    "gap_span_va",
    "va_mass",
    "va_mask",
    "gap_mask",
    "va_count",
    "tpo_total",
    "tpo_conservation_ok",
    "tight_gap",
    "undefined_reason",
)


def derange_indices(n: int, seed: int) -> np.ndarray:
    return _derange_indices(n, np.random.default_rng(seed))


def _mask(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        return json.loads(value)
    raise ValueError("mask must be a JSON object")


def replay_profile(counts: Sequence[int], *, start_bin: int = 100) -> dict[str, Any]:
    """Replay the frozen POC, upper-first VA, and low-density gap algorithm."""
    total = sum(int(value) for value in counts)
    poc_offset = max(range(len(counts)), key=lambda index: (counts[index], -index))
    selected = {poc_offset}
    selected_count = int(counts[poc_offset])
    target = int(np.ceil(0.70 * total))
    low = high = poc_offset
    while selected_count < target:
        lower = counts[low - 1] if low > 0 else -1
        upper = counts[high + 1] if high + 1 < len(counts) else -1
        if upper >= lower:
            high += 1
            chosen = high
        else:
            low -= 1
            chosen = low
        selected.add(chosen)
        selected_count += int(counts[chosen])
    gap_target = int(np.ceil(0.30 * selected_count))
    gap: list[int] = []
    gap_count = 0
    for index in sorted(selected, key=lambda item: (counts[item], item)):
        gap.append(index)
        gap_count += int(counts[index])
        if gap_count >= gap_target:
            break
    gap_low, gap_high = min(gap), max(gap)
    va_width = float(high - low + 1)
    gap_span = float(gap_high - gap_low + 1)
    return {
        "profile_status": "DEFINED",
        "bracket_count": 6,
        "bin_width": 1.0,
        "atr_unit": 10.0,
        "poc": float(start_bin + poc_offset),
        "val": float(start_bin + low),
        "vah": float(start_bin + high + 1),
        "va_width": va_width,
        "gap_span": gap_span,
        "gap_span_atr": gap_span / 10.0,
        "gap_span_va": gap_span / va_width,
        "va_mass": selected_count / total,
        "va_mask": json.dumps(
            {"low_bin_index": start_bin + low, "high_bin_index": start_bin + high}
        ),
        "gap_mask": json.dumps(
            {
                "outer_low_bin_index": start_bin + gap_low,
                "outer_high_bin_index": start_bin + gap_high,
                "selected_count": len(gap),
            }
        ),
        "va_count": selected_count,
        "tpo_total": total,
        "tpo_conservation_ok": True,
        "tight_gap": gap_span < 0.5 * va_width,
        "undefined_reason": None,
    }


def golden_profile_frame() -> pl.DataFrame:
    """Replay both amended hand-derived traces from their explicit bin counts."""
    rows = []
    for raid_id, generation, counts in (
        ("GOLDEN-T1", 1, (29, 12, 23, 23, 27, 26)),
        ("GOLDEN-T2", 2, (10, 18, 13, 7, 7, 30)),
    ):
        row = replay_profile(counts)
        row.update(raid_id=raid_id, profile_generation=generation)
        mask = _mask(row["gap_mask"])
        mask.update(
            raid_id=raid_id,
            profile_generation=generation,
            sha256="0" * 64,
        )
        row["gap_mask"] = json.dumps(mask)
        rows.append(row)
    return pl.DataFrame(rows)


def validate_profile_frame(frame: pl.DataFrame) -> tuple[IntegrityStatus, dict[str, Any]]:
    """Validate profile masks, conservation, derived scalars, and strict tightness."""
    reasons: list[str] = []
    defined = frame.filter(pl.col("profile_status") == "DEFINED")
    for row in defined.to_dicts():
        try:
            va_mask = _mask(row["va_mask"])
            gap_mask = _mask(row["gap_mask"])
            if int(va_mask["low_bin_index"]) > int(va_mask["high_bin_index"]):
                reasons.append("VOID_VA_MASK")
            if int(gap_mask["outer_low_bin_index"]) > int(gap_mask["outer_high_bin_index"]):
                reasons.append("VOID_GAP_MASK")
            if int(gap_mask["selected_count"]) < 1:
                reasons.append("VOID_GAP_MASK")
            if gap_mask["raid_id"] != row["raid_id"] or int(gap_mask["profile_generation"]) != int(
                row["profile_generation"]
            ):
                reasons.append("VOID_GAP_MASK_BINDING")
            sha = str(gap_mask["sha256"])
            if len(sha) != 64 or any(character not in "0123456789abcdef" for character in sha):
                reasons.append("VOID_GAP_MASK_HASH")
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            reasons.append("VOID_PROFILE_MASK")
            continue
        if row.get("tpo_conservation_ok") is not True:
            reasons.append("VOID_TPO_CONSERVATION")
        atr = float(row["atr_unit"])
        width = float(row["va_width"])
        span = float(row["gap_span"])
        if not np.isclose(float(row["bin_width"]), 0.1 * atr):
            reasons.append("VOID_BIN_WIDTH")
        if not np.isclose(float(row["gap_span_atr"]), span / atr):
            reasons.append("VOID_GAP_SPAN_ATR")
        if not np.isclose(float(row["gap_span_va"]), span / width):
            reasons.append("VOID_GAP_SPAN_VA")
        if not np.isclose(float(row["va_mass"]), row["va_count"] / row["tpo_total"]):
            reasons.append("VOID_VA_MASS")
        if int(row["bracket_count"]) < 1 or float(row["val"]) > float(row["poc"]):
            reasons.append("VOID_PROFILE_GEOMETRY")
        if float(row["poc"]) >= float(row["vah"]):
            reasons.append("VOID_PROFILE_GEOMETRY")
        if not np.isclose(width, float(row["vah"]) - float(row["val"])):
            reasons.append("VOID_VA_WIDTH")
        expected_span = (
            int(gap_mask["outer_high_bin_index"]) - int(gap_mask["outer_low_bin_index"]) + 1
        ) * float(row["bin_width"])
        if not np.isclose(span, expected_span):
            reasons.append("VOID_GAP_SPAN")
        if bool(row["tight_gap"]) != bool(span < 0.5 * width):
            reasons.append("VOID_TIGHT_GAP_BOUNDARY")
    unique = tuple(dict.fromkeys(reasons))
    evidence = {
        "all": frame.height,
        "defined": defined.height,
        "undefined": frame.height - defined.height,
        "reasons": list(unique),
    }
    return IntegrityStatus(not unique, unique, evidence), evidence


def profile_integrity_report(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Compatibility wrapper for focused profile integrity probes."""
    normalized = []
    for row in rows:
        item = dict(row)
        item.setdefault("undefined_reason", item.get("profile_undefined_reason"))
        normalized.append(item)
    status, evidence = validate_profile_frame(pl.DataFrame(normalized))
    return {"blocking_pass": status.blocking_pass, **evidence}


def join_profiles_left(
    raids: Sequence[dict[str, Any]], profiles: Sequence[dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    joined, evidence = _join_profiles_frame(
        pl.DataFrame(raids), pl.DataFrame(profiles), key="raid_id"
    )
    evidence["one_to_one"] = evidence["duplicate_profile_keys"] == 0
    return joined.to_dicts(), evidence


class Adapter(BaseContrastAdapter):
    experiment = EXPERIMENT
    label_column = LABEL_COLUMN
    contrasts = ((True, False),)
    control_group_columns = CONTROL_GROUP_COLUMNS
    control_null_columns = CONTROL_NULL_COLUMNS

    def _channel_frame(self, frame: pl.DataFrame, channel: str) -> pl.DataFrame:
        return super()._channel_frame(frame, channel).filter(pl.col("profile_status") == "DEFINED")

    def live_frame(
        self, source_root: Path, gate_path: Path
    ) -> tuple[pl.DataFrame, dict[str, Any], IntegrityStatus]:
        self._live_mode = True
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
        profile_frames: list[pl.LazyFrame] = []
        profile_columns = ("raid_id", "profile_generation", *PROFILE_COLUMNS)
        for raid_path in attestation.paths:
            source_cell = raid_path.parent.name
            raid_frames.append(
                scan_train_columns(
                    [raid_path],
                    columns=self.required_columns,
                    train_end_column="endpoint_ts_ns",
                    train_end_ns=1_700_611_200 * 1_000_000_000,
                ).with_columns(pl.lit(source_cell).alias("source_cell"))
            )
            profile_frames.append(
                pl.scan_parquet(raid_path.with_name("tpo_profiles.parquet"))
                .select(profile_columns)
                .with_columns(pl.lit(source_cell).alias("source_cell"))
            )
        raids = pl.concat(raid_frames).collect(engine="streaming")
        profiles = pl.concat(profile_frames).collect(engine="streaming")
        key = ["source_cell", "raid_id", "profile_generation"]
        duplicate_profiles = profiles.select(pl.struct(key).is_duplicated().sum()).item()
        unmatched = raids.join(profiles.select(key), on=key, how="anti").height
        extras = profiles.join(raids.select(key), on=key, how="anti").height
        joined = raids.join(profiles, on=key, how="left").with_columns(
            pl.when(pl.col("profile_status").is_null())
            .then(pl.lit("MISSING_PROFILE"))
            .otherwise(pl.lit("MATCHED"))
            .alias("profile_join_reason")
        )
        join_evidence = {
            "raid_rows": raids.height,
            "profile_rows": profiles.height,
            "unmatched_raids": unmatched,
            "extra_profiles": extras,
            "duplicate_profile_keys": int(duplicate_profiles),
        }
        source["profile_join"] = join_evidence
        reasons = list(attestation.integrity.reasons)
        if duplicate_profiles:
            reasons.append("VOID_DUPLICATE_PROFILE_KEY")
        if unmatched or extras:
            reasons.append("VOID_PROFILE_JOIN_MISMATCH")
        unique = tuple(dict.fromkeys(reasons))
        return joined, source, IntegrityStatus(not unique, unique, join_evidence)

    def fixture_frame(self) -> pl.DataFrame:
        frame = make_fixture_frame((False, True), label_column=LABEL_COLUMN)
        templates = golden_profile_frame().to_dicts()
        profile_rows = []
        for index, source in enumerate(frame.to_dicts()):
            template = dict(templates[0 if source[LABEL_COLUMN] else 1])
            template.update(raid_id=source["raid_id"], profile_generation=index + 1)
            mask = _mask(template["gap_mask"])
            mask.update(raid_id=source["raid_id"], profile_generation=index + 1)
            template["gap_mask"] = json.dumps(mask)
            profile_rows.append(template)
        profiles = pl.DataFrame(profile_rows)
        return frame.drop(LABEL_COLUMN).join(profiles, on="raid_id", how="left")

    def extra_integrity(self, frame: pl.DataFrame) -> IntegrityStatus:
        status, _ = validate_profile_frame(frame)
        golden_status, golden_evidence = validate_profile_frame(golden_profile_frame())
        reasons = tuple(dict.fromkeys((*status.reasons, *golden_status.reasons)))
        return IntegrityStatus(
            not reasons,
            reasons,
            {"profiles": status.evidence, "golden_trace": golden_evidence},
        )

    def census(self, frame: pl.DataFrame) -> dict[str, Any]:
        census = super().census(frame)
        census["profile_status"] = dict(
            Counter(str(value) for value in frame["profile_status"].to_list())
        )
        return census

    def extra(self, frame: pl.DataFrame) -> dict[str, Any]:
        extra = super().extra(frame)
        defined = frame.filter(pl.col("profile_status") == "DEFINED")
        extra["profile_census"] = {
            "all": frame.height,
            "defined": defined.height,
            "tight": defined.filter(pl.col("tight_gap") == True).height,  # noqa: E712
            "non_tight": defined.filter(pl.col("tight_gap") == False).height,  # noqa: E712
            "undefined_reasons": dict(
                Counter(str(value) for value in frame["undefined_reason"].to_list())
            ),
        }
        extra["all_defined_baseline"] = {
            channel: {
                "n": defined.filter(pl.col(channel).is_not_null()).height,
                "mean": defined[channel].cast(pl.Float64).mean(),
                "median": defined[channel].cast(pl.Float64).median(),
            }
            for channel in self.channels
        }
        golden_status, golden_evidence = validate_profile_frame(golden_profile_frame())
        extra["golden_trace"] = {
            "blocking_pass": golden_status.blocking_pass,
            **golden_evidence,
        }
        return extra


def _fixture_rows() -> list[dict[str, Any]]:
    return Adapter(n_boot=40, n_destroy=20, seeds=(0, 1)).fixture_frame().to_dicts()


def future_destroy(
    rows: Sequence[dict[str, Any]], label: str, seed: int
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    frame = pl.DataFrame(rows)
    columns = {
        column: frame[column].to_numpy()
        for column in (*CONTROL_GROUP_COLUMNS, *CONTROL_NULL_COLUMNS)
    }
    mappings = build_destroy_mappings(
        columns,
        DestroySpec(CONTROL_GROUP_COLUMNS, CONTROL_NULL_COLUMNS, CONTROL_NULL_COLUMNS),
        seeds=(seed,),
        population_id=f"fixture:{label}",
    )
    destroyed = [dict(row) for row in rows]
    for channel in CONTROL_NULL_COLUMNS:
        moved = apply_destroy_mappings(frame[channel].to_numpy(), mappings)[0]
        for index, value in enumerate(moved.tolist()):
            destroyed[index][channel] = value
    return destroyed, {"fixed_points": mappings.fixed_points, "mapped_rows": mappings.moved_rows}


def run_fixture(
    *,
    n_destroy: int = DEFAULT_DESTROYS,
    seeds: Sequence[int] = SEEDS,
    output: Path | None = None,
    n_boot: int = 200,
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
            adapter, source, gate, args.output or experiment_root / "results/analysis_results.json"
        )
    else:
        _run_fixture(adapter, args.output or experiment_root / "results/fixture_integrity.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
