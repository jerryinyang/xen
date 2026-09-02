"""Independent EXP-104 interrogation. Does not import experiment analysis.py."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import polars as pl

ROOT = Path(__file__).resolve().parents[4]
EXP = ROOT / "python/experiments/EXP-104"
SOURCE_ROOT = ROOT / "data/nautilus_runs/EXP-100/full"
FAMILY_GATE = ROOT / "python/experiments/EXP-100/results/estimand_validation.json"
LIVE = EXP / "results/analysis_results.json"
OUT_DIR = EXP / "analysis_code"
SUMMARY_PATH = OUT_DIR / "interrogation_summary.json"

TRAIN_START_NS = int(
    datetime(2021, 6, 2, 0, 1, tzinfo=timezone.utc).timestamp() * 1_000_000_000
)
TRAIN_END_NS = 1_700_611_200 * 1_000_000_000  # 2023-11-22T00:00:00Z
HOLDOUT_NS = TRAIN_END_NS
NS_PER_HOUR = 3_600_000_000_000
INTEGRITY_Z = 2.8
ARMS = ("LOW", "MID", "HIGH")
STRATUM = (
    "archive_symbol",
    "timeframe",
    "confirmation_method",
    "confirmation_reference",
    "side",
    "config",
)
RAID_COLS = [
    "raid_id",
    "level_id",
    "archive_symbol",
    "timeframe",
    "config",
    "side",
    "confirmation_method",
    "confirmation_reference",
    "sweep_ts_ns",
    "endpoint_ts_ns",
    "censor_ts_ns",
    "raid_regime",
    "confirmation_regime",
    "endpoint_regime",
    "profile_undefined_reason",
    "primary_attribution",
    "status",
    "primary_completed",
    "swing_price",
    "swing_bps",
    "swing_atr",
    "strong_move",
    "swing_duration_ns",
    "duration_ns",
    "profile_generation",
]


def _finite(value: Any) -> bool:
    return value is not None and value == value and not (
        isinstance(value, float) and math.isinf(value)
    )


def _close(a: Any, b: Any, *, rel: float = 1e-9, abs_: float = 1e-9) -> bool:
    if a is None and b is None:
        return True
    if not _finite(a) and not _finite(b):
        return True
    if not _finite(a) or not _finite(b):
        return False
    return math.isclose(float(a), float(b), rel_tol=rel, abs_tol=abs_)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _cell_dirs() -> list[Path]:
    return sorted(path for path in SOURCE_ROOT.iterdir() if path.is_dir())


def _later_swing(frame: pl.LazyFrame) -> pl.LazyFrame:
    return frame.filter(
        (pl.col("status") == "COMPLETED")
        & pl.col("primary_attribution").fill_null(False)
        & pl.col("primary_completed").fill_null(False)
    )


def _year_expr(column: str) -> pl.Expr:
    return (
        (pl.col(column) / 1_000_000_000)
        .cast(pl.Int64)
        .map_elements(
            lambda ts: datetime.fromtimestamp(int(ts), tz=timezone.utc).year
            if ts is not None
            else None,
            return_dtype=pl.Int32,
        )
        .alias("year")
    )


def integrity_files() -> dict[str, Any]:
    gate = _load_json(FAMILY_GATE)
    live = _load_json(LIVE)
    local_gate = _load_json(EXP / "results/estimand_validation.json")
    cells = gate["cells"]
    meta_fail: list[str] = []
    n_fills = 0
    versions = Counter()
    cost_models = Counter()
    contracts = Counter()
    nodes = Counter()
    after_train = 0
    holdout_hits = 0
    for cell in _cell_dirs():
        meta = _load_json(cell / "run_metadata.json")
        versions[str(meta.get("nautilus_version"))] += 1
        cost_models[str(meta.get("cost_model"))] += 1
        contracts[str(meta.get("emission_contract_version"))] += 1
        nodes[str(bool(meta.get("one_backtest_node")))] += 1
        n_fills += int(meta.get("n_fills") or 0)
        if meta.get("nautilus_version") != "1.230.0":
            meta_fail.append(f"{cell.name}:nautilus")
        if meta.get("cost_model") != "NO_COST_CHARGED":
            meta_fail.append(f"{cell.name}:cost")
        if meta.get("emission_contract_version") != "nautilus-emission-v1":
            meta_fail.append(f"{cell.name}:contract")
        if meta.get("one_backtest_node") is not True:
            meta_fail.append(f"{cell.name}:node")
    gate_sha = {exp: _sha256(ROOT / f"python/experiments/{exp}/results/estimand_validation.json")[:16]
                for exp in ("EXP-100", "EXP-101", "EXP-102", "EXP-103", "EXP-104")}
    no_cost_ok = all(cell.get("no_cost_charged", {}).get("ok") for cell in cells)
    blocking_cells = sum(1 for cell in cells if cell.get("blocking_pass"))
    live_integrity = live.get("integrity", {})
    return {
        "family_gate_blocking_pass": gate.get("blocking_pass"),
        "family_gate_n_cells": gate.get("n_cells"),
        "family_gate_blocking_cells": blocking_cells,
        "family_gate_no_cost_ok": no_cost_ok,
        "local_gate_sha16": gate_sha["EXP-104"],
        "gate_sha16": gate_sha,
        "gates_byte_identical_prefix": all(v == gate_sha["EXP-100"] for v in gate_sha.values()),
        "live_integrity_blocking_pass": live_integrity.get("blocking_pass"),
        "live_integrity_reasons": live_integrity.get("reasons") or [],
        "code_dir_exists": (EXP / "code").exists(),
        "n_source_cells": len(_cell_dirs()),
        "n_fills_metadata": n_fills,
        "nautilus_versions": dict(versions),
        "cost_models": dict(cost_models),
        "contracts": dict(contracts),
        "one_backtest_node": dict(nodes),
        "meta_fail": meta_fail[:20],
        "n_meta_fail": len(meta_fail),
        "live_rows_attested": live.get("source", {}).get("attestation", {}).get("rows"),
        "live_cells_attested": live.get("source", {}).get("attestation", {}).get("cells"),
        "live_join": live.get("source", {}).get("profile_regime_join"),
        "zero_cost_disclosure": live.get("zero_cost_disclosure"),
        "after_train_placeholder": after_train,
        "holdout_placeholder": holdout_hits,
        "local_gate_blocking_pass": local_gate.get("blocking_pass"),
    }


def raid_scan() -> tuple[pl.DataFrame, dict[str, Any]]:
    paths = [str(path / "raids.parquet") for path in _cell_dirs()]
    lazy = (
        pl.scan_parquet(paths)
        .select(RAID_COLS)
        .with_columns(pl.lit(True).alias("_in_scan"))
    )
    n_raw = lazy.select(pl.len().alias("n")).collect().item()
    train = lazy.filter(
        pl.col("endpoint_ts_ns").is_null() | (pl.col("endpoint_ts_ns") <= TRAIN_END_NS)
    )
    n_train = train.select(pl.len().alias("n")).collect().item()
    after_end = lazy.filter(
        pl.col("endpoint_ts_ns").is_not_null() & (pl.col("endpoint_ts_ns") > TRAIN_END_NS)
    ).select(pl.len().alias("n")).collect().item()
    after_sweep = lazy.filter(
        pl.col("sweep_ts_ns").is_not_null() & (pl.col("sweep_ts_ns") > TRAIN_END_NS)
    ).select(pl.len().alias("n")).collect().item()
    before_start = lazy.filter(
        pl.col("sweep_ts_ns").is_not_null() & (pl.col("sweep_ts_ns") < TRAIN_START_NS)
    ).select(pl.len().alias("n")).collect().item()
    duration_mismatch = train.filter(
        pl.col("swing_duration_ns").is_not_null()
        & pl.col("duration_ns").is_not_null()
        & (pl.col("swing_duration_ns") != pl.col("duration_ns"))
    ).select(pl.len().alias("n")).collect().item()
    duration_null_mismatch = train.filter(
        pl.col("swing_duration_ns").is_null() ^ pl.col("duration_ns").is_null()
    ).select(pl.len().alias("n")).collect().item()
    dup_ids = (
        train.group_by("raid_id")
        .agg(pl.len().alias("n"))
        .filter(pl.col("n") > 1)
        .select(pl.len().alias("n"))
        .collect()
        .item()
    )
    regime = train.group_by("raid_regime").agg(pl.len().alias("n")).collect()
    status = train.group_by("status").agg(pl.len().alias("n")).collect()
    conf = train.group_by("confirmation_regime").agg(pl.len().alias("n")).collect()
    end = train.group_by("endpoint_regime").agg(pl.len().alias("n")).collect()
    undef = (
        train.group_by("profile_undefined_reason")
        .agg(pl.len().alias("n"))
        .collect()
    )
    later = _later_swing(train)
    n_later = later.select(pl.len().alias("n")).collect().item()
    later_regime = later.group_by("raid_regime").agg(pl.len().alias("n")).collect()
    later_atr_undef = later.filter(
        pl.col("profile_undefined_reason").fill_null("") == "ATR_UNDEFINED"
    ).select(pl.len().alias("n")).collect().item()
    later_regime_undef = later.filter(pl.col("raid_regime") == "ATR_UNDEFINED").select(
        pl.len().alias("n")
    ).collect().item()
    missing = {
        col: train.select(pl.col(col).is_null().sum().alias("n")).collect().item()
        for col in ("swing_price", "swing_bps", "swing_atr", "swing_duration_ns", "strong_move")
    }
    year_all = (
        train.filter(pl.col("sweep_ts_ns").is_not_null())
        .with_columns(_year_expr("sweep_ts_ns"))
        .group_by("year")
        .agg(
            pl.len().alias("raids"),
            pl.col("primary_completed").fill_null(False).sum().alias("primary_completed"),
            (pl.col("status") == "COMPLETED").sum().alias("completed"),
        )
        .sort("year")
        .collect()
    )
    year_later = (
        later.filter(pl.col("sweep_ts_ns").is_not_null())
        .with_columns(_year_expr("sweep_ts_ns"))
        .group_by("year")
        .agg(pl.len().alias("later_swing"))
        .sort("year")
        .collect()
    )
    tf = train.group_by("timeframe").agg(pl.len().alias("n")).collect()
    symbols = train.group_by("archive_symbol").agg(pl.len().alias("n")).collect()
    methods = train.group_by("confirmation_method").agg(pl.len().alias("n")).collect()
    facts = {
        "n_raw": int(n_raw),
        "n_train": int(n_train),
        "n_dropped_by_endpoint_fence": int(n_raw - n_train),
        "n_endpoint_after_train": int(after_end),
        "n_sweep_after_train": int(after_sweep),
        "n_sweep_before_start": int(before_start),
        "duration_alias_mismatches": int(duration_mismatch),
        "duration_alias_nullness_mismatch": int(duration_null_mismatch),
        "duplicate_raid_id_groups": int(dup_ids),
        "regime_census": {str(r): int(n) for r, n in regime.iter_rows()},
        "status_census": {str(r): int(n) for r, n in status.iter_rows()},
        "confirmation_regime_census": {str(r): int(n) for r, n in conf.iter_rows()},
        "endpoint_regime_census": {str(r): int(n) for r, n in end.iter_rows()},
        "profile_undefined_reason": {str(r): int(n) for r, n in undef.iter_rows()},
        "n_later_swing": int(n_later),
        "later_swing_regime": {str(r): int(n) for r, n in later_regime.iter_rows()},
        "later_swing_profile_atr_undefined": int(later_atr_undef),
        "later_swing_raid_regime_atr_undefined": int(later_regime_undef),
        "missingness": missing,
        "year_all": year_all.to_dicts(),
        "year_later": year_later.to_dicts(),
        "timeframe": {str(r): int(n) for r, n in tf.iter_rows()},
        "symbols": {str(r): int(n) for r, n in symbols.iter_rows()},
        "confirmation_method": {str(r): int(n) for r, n in methods.iter_rows()},
    }
    later_df = later.collect(engine="streaming")
    return later_df, facts


def _channel_frame(later: pl.DataFrame, channel: str) -> pl.DataFrame:
    if channel in {"swing_atr", "strong_move"}:
        return later.filter(
            pl.col("profile_undefined_reason").fill_null("") != "ATR_UNDEFINED"
        )
    return later


def outcome_stats(later: pl.DataFrame) -> dict[str, Any]:
    channels = {
        "swing_atr": "swing_atr",
        "swing_duration_ns": "swing_duration_ns",
        "swing_price": "swing_price",
        "swing_bps": "swing_bps",
        "strong_move": "strong_move",
    }
    rows: list[dict[str, Any]] = []
    empty_arms = 0
    for channel, column in channels.items():
        frame = _channel_frame(later, channel)
        if channel == "strong_move":
            numeric = frame.with_columns(pl.col(column).cast(pl.Float64).alias("_value"))
        else:
            numeric = frame.with_columns(pl.col(column).cast(pl.Float64).alias("_value"))
        numeric = numeric.filter(pl.col("_value").is_not_null() & pl.col("_value").is_finite())
        grouped = (
            numeric.group_by([*STRATUM, "raid_regime"])
            .agg(
                pl.len().alias("n"),
                pl.col("_value").mean().alias("mean"),
                pl.col("_value").median().alias("median"),
                pl.col("_value").std().alias("std"),
                pl.col("_value").quantile(0.01).alias("q01"),
                pl.col("_value").quantile(0.05).alias("q05"),
                pl.col("_value").quantile(0.95).alias("q95"),
                pl.col("_value").quantile(0.99).alias("q99"),
            )
            .collect()
            if isinstance(numeric, pl.LazyFrame)
            else numeric.group_by([*STRATUM, "raid_regime"]).agg(
                pl.len().alias("n"),
                pl.col("_value").mean().alias("mean"),
                pl.col("_value").median().alias("median"),
                pl.col("_value").std().alias("std"),
                pl.col("_value").quantile(0.01).alias("q01"),
                pl.col("_value").quantile(0.05).alias("q05"),
                pl.col("_value").quantile(0.95).alias("q95"),
                pl.col("_value").quantile(0.99).alias("q99"),
            )
        )
        lookup: dict[tuple[Any, ...], dict[str, Any]] = {}
        for rec in grouped.to_dicts():
            key = tuple(rec[c] for c in STRATUM) + (rec["raid_regime"],)
            lookup[key] = rec
        strata = {tuple(rec[c] for c in STRATUM) for rec in grouped.to_dicts()}
        # also include later-swing strata that lost all finite values after ATR filter
        all_strata = {
            tuple(rec) for rec in later.select(list(STRATUM)).unique().iter_rows()
        }
        strata |= all_strata
        for stratum in strata:
            stats = {arm: lookup.get(stratum + (arm,)) for arm in ARMS}
            mid = stats["MID"]
            for arm in ("LOW", "HIGH"):
                arm_s = stats[arm]
                empty = arm_s is None or mid is None or arm_s["n"] == 0 or mid["n"] == 0
                if empty:
                    empty_arms += 1
                    rows.append(
                        {
                            "stratum": dict(zip(STRATUM, stratum, strict=True)),
                            "channel": channel,
                            "arm": arm,
                            "empty": True,
                            "reason": "EMPTY_ARM",
                            "arm_n": 0 if arm_s is None else int(arm_s["n"]),
                            "comparator_n": 0 if mid is None else int(mid["n"]),
                            "arm_mean": None,
                            "comparator_mean": None,
                            "estimate": None,
                            "arm_median": None,
                            "comparator_median": None,
                            "median_contrast": None,
                        }
                    )
                    continue
                rows.append(
                    {
                        "stratum": dict(zip(STRATUM, stratum, strict=True)),
                        "channel": channel,
                        "arm": arm,
                        "empty": False,
                        "reason": None,
                        "arm_n": int(arm_s["n"]),
                        "comparator_n": int(mid["n"]),
                        "arm_mean": float(arm_s["mean"]),
                        "comparator_mean": float(mid["mean"]),
                        "estimate": float(arm_s["mean"]) - float(mid["mean"]),
                        "arm_median": float(arm_s["median"]) if arm_s["median"] is not None else None,
                        "comparator_median": float(mid["median"]) if mid["median"] is not None else None,
                        "median_contrast": (
                            float(arm_s["median"]) - float(mid["median"])
                            if arm_s["median"] is not None and mid["median"] is not None
                            else None
                        ),
                        "arm_std": float(arm_s["std"]) if arm_s["std"] is not None else None,
                        "arm_q01": float(arm_s["q01"]) if arm_s["q01"] is not None else None,
                        "arm_q05": float(arm_s["q05"]) if arm_s["q05"] is not None else None,
                        "arm_q95": float(arm_s["q95"]) if arm_s["q95"] is not None else None,
                        "arm_q99": float(arm_s["q99"]) if arm_s["q99"] is not None else None,
                    }
                )
    pooled = []
    for channel, column in channels.items():
        frame = _channel_frame(later, channel)
        if channel == "strong_move":
            numeric = frame.with_columns(pl.col(column).cast(pl.Float64).alias("_value"))
        else:
            numeric = frame.with_columns(pl.col(column).cast(pl.Float64).alias("_value"))
        numeric = numeric.filter(pl.col("_value").is_not_null() & pl.col("_value").is_finite())
        by_arm = numeric.group_by("raid_regime").agg(
            pl.len().alias("n"),
            pl.col("_value").mean().alias("mean"),
            pl.col("_value").median().alias("median"),
            pl.col("_value").std().alias("std"),
            pl.col("_value").quantile(0.01).alias("q01"),
            pl.col("_value").quantile(0.05).alias("q05"),
            pl.col("_value").quantile(0.95).alias("q95"),
            pl.col("_value").quantile(0.99).alias("q99"),
        )
        recs = {r["raid_regime"]: r for r in by_arm.to_dicts()}
        mid = recs.get("MID")
        for arm in ("LOW", "HIGH"):
            a = recs.get(arm)
            if not a or not mid:
                continue
            pooled.append(
                {
                    "channel": channel,
                    "arm": arm,
                    "arm_n": int(a["n"]),
                    "comparator_n": int(mid["n"]),
                    "arm_mean": float(a["mean"]),
                    "comparator_mean": float(mid["mean"]),
                    "estimate": float(a["mean"]) - float(mid["mean"]),
                    "arm_median": float(a["median"]) if a["median"] is not None else None,
                    "comparator_median": float(mid["median"]) if mid["median"] is not None else None,
                    "arm_std": float(a["std"]) if a["std"] is not None else None,
                    "arm_q01": float(a["q01"]) if a["q01"] is not None else None,
                    "arm_q99": float(a["q99"]) if a["q99"] is not None else None,
                }
            )
    by_symbol = (
        _channel_frame(later, "swing_atr")
        .filter(pl.col("swing_atr").is_not_null() & pl.col("swing_atr").is_finite())
        .group_by(["archive_symbol", "raid_regime"])
        .agg(
            pl.len().alias("n"),
            pl.col("swing_atr").mean().alias("mean"),
            pl.col("swing_atr").median().alias("median"),
        )
        .to_dicts()
    )
    by_tf = (
        _channel_frame(later, "swing_atr")
        .filter(pl.col("swing_atr").is_not_null() & pl.col("swing_atr").is_finite())
        .group_by(["timeframe", "raid_regime"])
        .agg(
            pl.len().alias("n"),
            pl.col("swing_atr").mean().alias("mean"),
            pl.col("swing_atr").median().alias("median"),
        )
        .to_dicts()
    )
    tails = tail_concentration(later)
    return {
        "n_contrast_rows": len(rows),
        "n_empty_arm_rows": empty_arms,
        "rows": rows,
        "pooled_disclosure": pooled,
        "swing_atr_by_symbol": by_symbol,
        "swing_atr_by_timeframe": by_tf,
        "tails": tails,
    }


def tail_concentration(later: pl.DataFrame) -> dict[str, Any]:
    frame = _channel_frame(later, "swing_atr").filter(
        pl.col("swing_atr").is_not_null() & pl.col("swing_atr").is_finite()
    )
    out: dict[str, Any] = {}
    for arm in ARMS:
        sub = frame.filter(pl.col("raid_regime") == arm)
        n = sub.height
        if n == 0:
            out[arm] = {"n": 0}
            continue
        values = sub.select("swing_atr").to_series().to_numpy()
        total = float(values.sum())
        order = sorted(values, reverse=True)
        top1 = max(1, int(round(0.01 * n)))
        top5 = max(1, int(round(0.05 * n)))
        sm = _channel_frame(later, "strong_move").filter(pl.col("raid_regime") == arm)
        sm_n = sm.height
        sm_true = int(sm.select(pl.col("strong_move").fill_null(False).sum()).item())
        out[arm] = {
            "n": n,
            "mean": float(values.mean()),
            "median": float(sorted(values)[n // 2]),
            "min": float(values.min()),
            "max": float(values.max()),
            "top1pct_n": top1,
            "top1pct_share_of_sum": float(sum(order[:top1]) / total) if total else None,
            "top5pct_share_of_sum": float(sum(order[:top5]) / total) if total else None,
            "strong_move_n": sm_n,
            "strong_move_true": sm_true,
            "strong_move_rate": (sm_true / sm_n) if sm_n else None,
        }
    year = (
        _channel_frame(later, "swing_atr")
        .filter(pl.col("swing_atr").is_not_null() & pl.col("sweep_ts_ns").is_not_null())
        .with_columns(_year_expr("sweep_ts_ns"))
        .group_by(["year", "raid_regime"])
        .agg(
            pl.len().alias("n"),
            pl.col("swing_atr").mean().alias("mean_swing_atr"),
            pl.col("strong_move").cast(pl.Float64).mean().alias("strong_move_rate"),
        )
        .sort(["year", "raid_regime"])
        .to_dicts()
    )
    out["year_later_swing_atr"] = year
    return out


def frequency_census() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    provenance = {
        "raid_id_not_unique_cells": 0,
        "missing_sweep_mark": 0,
        "no_preceding_mark": 0,
        "regime_mismatch": 0,
        "mark_ts_duplicate_cells": 0,
        "cells": 0,
    }
    empty_exposure_rows = 0
    for cell in _cell_dirs():
        provenance["cells"] += 1
        marks = (
            pl.read_parquet(cell / "bar_marks.parquet", columns=["ts_event_ns", "regime"])
            .sort("ts_event_ns")
        )
        if marks.height == 0:
            continue
        dup = marks.height - marks.select("ts_event_ns").n_unique()
        if dup:
            provenance["mark_ts_duplicate_cells"] += 1
        marks = marks.with_columns(
            pl.col("regime").shift(1).alias("causal_regime"),
            pl.col("ts_event_ns").shift(1).alias("regime_source_ts_ns"),
        )
        raids = pl.read_parquet(
            cell / "raids.parquet",
            columns=[
                "raid_id",
                "sweep_ts_ns",
                "raid_regime",
                "archive_symbol",
                "timeframe",
                "confirmation_method",
                "confirmation_reference",
                "config",
                "side",
                "endpoint_ts_ns",
            ],
        )
        raids = raids.filter(
            pl.col("endpoint_ts_ns").is_null() | (pl.col("endpoint_ts_ns") <= TRAIN_END_NS)
        )
        if raids.select("raid_id").n_unique() != raids.height:
            provenance["raid_id_not_unique_cells"] += 1
        joined = raids.join(
            marks.select("ts_event_ns", "causal_regime", "regime_source_ts_ns"),
            left_on="sweep_ts_ns",
            right_on="ts_event_ns",
            how="left",
        )
        provenance["missing_sweep_mark"] += joined.filter(
            pl.col("regime_source_ts_ns").is_null() & pl.col("causal_regime").is_null()
            & pl.col("sweep_ts_ns").is_not_null()
        ).height
        # first-bar starts have a mark but null preceding
        first_ts = int(marks["ts_event_ns"][0])
        provenance["no_preceding_mark"] += joined.filter(pl.col("sweep_ts_ns") == first_ts).height
        provenance["regime_mismatch"] += joined.filter(
            pl.col("raid_regime").is_not_null()
            & pl.col("causal_regime").is_not_null()
            & (pl.col("raid_regime") != pl.col("causal_regime"))
        ).height
        eligible = marks.filter(pl.col("causal_regime").is_not_null())
        exposure_counts = {
            str(r): int(n)
            for r, n in eligible.group_by("causal_regime").agg(pl.len().alias("n")).iter_rows()
        }
        warmup = {
            k: exposure_counts.get(k, 0)
            for k in ("REGIME_WARMUP", "ATR_UNDEFINED")
            if exposure_counts.get(k, 0)
        }
        identity = raids.select(
            "archive_symbol",
            "timeframe",
            "confirmation_method",
            "confirmation_reference",
            "config",
            "side",
        ).unique()
        # keep only fully labelled confirmation cells (design cell grid)
        identity = identity.filter(pl.col("confirmation_method").is_not_null())
        starts = joined.group_by(
            [
                "archive_symbol",
                "timeframe",
                "confirmation_method",
                "confirmation_reference",
                "config",
                "side",
                "raid_regime",
            ]
        ).agg(pl.col("raid_id").n_unique().alias("starts"))
        start_lookup = {
            tuple(rec[c] for c in (*STRATUM, "raid_regime")): int(rec["starts"])
            for rec in starts.to_dicts()
        }
        eligible_marks = int(sum(exposure_counts.get(r, 0) for r in ARMS))
        for rec in identity.to_dicts():
            key = tuple(rec[c] for c in STRATUM)
            rates = {}
            for regime in ARMS:
                exposure = int(exposure_counts.get(regime, 0))
                n_starts = int(start_lookup.get(key + (regime,), 0))
                if exposure == 0:
                    empty_exposure_rows += 1
                    rate = None
                    contrast = None
                    reason = "EMPTY_EXPOSURE"
                else:
                    rate = 1000.0 * n_starts / exposure
                    rates[regime] = rate
                    reason = None
                    contrast = None
                rows.append(
                    {
                        **rec,
                        "causal_regime": regime,
                        "exposure": exposure,
                        "starts": n_starts,
                        "rate_per_1000": rate,
                        "contrast_minus_mid": contrast,
                        "eligible_marks": eligible_marks,
                        "empty_exposure_reason": reason,
                        "warmup_undefined_exposure": warmup,
                    }
                )
            mid_rate = rates.get("MID")
            for row in rows[-3:]:
                if row["rate_per_1000"] is None or mid_rate is None:
                    row["contrast_minus_mid"] = None
                elif row["causal_regime"] == "MID":
                    row["contrast_minus_mid"] = 0.0
                else:
                    row["contrast_minus_mid"] = row["rate_per_1000"] - mid_rate
    return {
        "n_rows": len(rows),
        "n_empty_exposure_rows": empty_exposure_rows,
        "provenance": provenance,
        "rows": rows,
    }


def compare_live(outcomes: dict[str, Any], frequency: dict[str, Any], raid_facts: dict[str, Any]) -> dict[str, Any]:
    live = _load_json(LIVE)
    mismatches: list[dict[str, Any]] = []

    def add(kind: str, **kwargs: Any) -> None:
        mismatches.append({"kind": kind, **kwargs})

    live_reg = live["extra"]["regime_census"]
    for k, v in raid_facts["regime_census"].items():
        if int(live_reg.get(k, -1)) != int(v):
            add("regime_census", key=k, recomputed=v, live=live_reg.get(k))
    live_status = live["extra"]["census"]["status"]
    for k, v in raid_facts["status_census"].items():
        if int(live_status.get(k, -1)) != int(v):
            add("status_census", key=k, recomputed=v, live=live_status.get(k))
    if int(live["population"]["rows"]) != int(raid_facts["n_train"]):
        add(
            "population_rows",
            recomputed=raid_facts["n_train"],
            live=live["population"]["rows"],
        )

    live_lookup: dict[tuple[Any, ...], dict[str, Any]] = {}
    empty_live = 0
    labelled_live = 0
    for rec in live["value_rows"]:
        st = rec["stratum"]
        key = tuple(st.get(c) for c in STRATUM) + (rec["channel"], rec["arm"])
        live_lookup[key] = rec
        if rec["observed"].get("reason"):
            empty_live += 1
        else:
            labelled_live += 1

    mean_mismatch = 0
    n_mismatch = 0
    empty_mismatch = 0
    matched = 0
    missing_in_live = 0
    extra_null_method = 0
    for rec in outcomes["rows"]:
        st = rec["stratum"]
        if st.get("confirmation_method") is None:
            continue
        key = tuple(st[c] for c in STRATUM) + (rec["channel"], rec["arm"])
        live_rec = live_lookup.get(key)
        if live_rec is None:
            missing_in_live += 1
            if missing_in_live <= 8:
                add("outcome_missing_in_live", key=[str(x) for x in key])
            continue
        matched += 1
        obs = live_rec["observed"]
        live_empty = bool(obs.get("reason"))
        if rec["empty"] != live_empty:
            empty_mismatch += 1
            if empty_mismatch <= 8:
                add(
                    "empty_flag",
                    key=[str(x) for x in key],
                    recomputed=rec["reason"],
                    live=obs.get("reason"),
                    recomputed_ns=(rec["arm_n"], rec["comparator_n"]),
                    live_ns=(obs.get("arm_n"), obs.get("comparator_n")),
                )
            continue
        if rec["empty"]:
            continue
        if rec["arm_n"] != obs.get("arm_n") or rec["comparator_n"] != obs.get("comparator_n"):
            n_mismatch += 1
            if n_mismatch <= 8:
                add(
                    "outcome_n",
                    key=[str(x) for x in key],
                    recomputed=(rec["arm_n"], rec["comparator_n"]),
                    live=(obs.get("arm_n"), obs.get("comparator_n")),
                )
        if not _close(rec["estimate"], obs.get("estimate"), rel=1e-8, abs_=1e-8):
            mean_mismatch += 1
            if mean_mismatch <= 8:
                add(
                    "outcome_estimate",
                    key=[str(x) for x in key],
                    recomputed=rec["estimate"],
                    live=obs.get("estimate"),
                    arm_mean=(rec["arm_mean"], obs.get("arm_mean")),
                )
        med = live_rec.get("medians") or {}
        if rec["arm_median"] is not None and med.get("arm") is not None:
            if not _close(rec["arm_median"], med.get("arm"), rel=1e-8, abs_=1e-8):
                if mean_mismatch + n_mismatch < 20:
                    add(
                        "outcome_median",
                        key=[str(x) for x in key],
                        recomputed=rec["arm_median"],
                        live=med.get("arm"),
                    )

    for rec in live["value_rows"]:
        if rec["stratum"].get("confirmation_method") is None:
            extra_null_method += 1

    live_freq = live["extra"]["frequency_census"][0]["census"]
    freq_lookup = {}
    live_empty_exp = 0
    live_empty_with_rate = 0
    for rec in live_freq:
        key = tuple(rec.get(c) for c in STRATUM) + (rec.get("causal_regime"),)
        freq_lookup[key] = rec
        if rec.get("empty_exposure_reason") == "EMPTY_EXPOSURE":
            live_empty_exp += 1
            if rec.get("rate_per_1000") is not None:
                live_empty_with_rate += 1
    freq_n_mismatch = 0
    freq_rate_mismatch = 0
    freq_matched = 0
    freq_missing = 0
    for rec in frequency["rows"]:
        key = tuple(rec[c] for c in STRATUM) + (rec["causal_regime"],)
        live_rec = freq_lookup.get(key)
        if live_rec is None:
            freq_missing += 1
            if freq_missing <= 8:
                add("freq_missing_in_live", key=[str(x) for x in key])
            continue
        freq_matched += 1
        if rec["exposure"] != live_rec.get("exposure") or rec["starts"] != live_rec.get("starts"):
            freq_n_mismatch += 1
            if freq_n_mismatch <= 8:
                add(
                    "freq_counts",
                    key=[str(x) for x in key],
                    recomputed=(rec["exposure"], rec["starts"]),
                    live=(live_rec.get("exposure"), live_rec.get("starts")),
                    live_reason=live_rec.get("empty_exposure_reason"),
                )
        if rec["empty_exposure_reason"] == "EMPTY_EXPOSURE":
            continue
        if not _close(rec["rate_per_1000"], live_rec.get("rate_per_1000"), rel=1e-8, abs_=1e-8):
            freq_rate_mismatch += 1
            if freq_rate_mismatch <= 8:
                add(
                    "freq_rate",
                    key=[str(x) for x in key],
                    recomputed=rec["rate_per_1000"],
                    live=live_rec.get("rate_per_1000"),
                )

    return {
        "n_mismatch_records": len(mismatches),
        "mismatches_head": mismatches[:40],
        "outcome_matched": matched,
        "outcome_missing_in_live": missing_in_live,
        "outcome_mean_mismatch": mean_mismatch,
        "outcome_n_mismatch": n_mismatch,
        "outcome_empty_mismatch": empty_mismatch,
        "live_value_rows": len(live["value_rows"]),
        "live_empty_reason_rows": empty_live,
        "live_labelled_rows": labelled_live,
        "live_null_method_value_rows": extra_null_method,
        "freq_matched": freq_matched,
        "freq_missing_in_live": freq_missing,
        "freq_n_mismatch": freq_n_mismatch,
        "freq_rate_mismatch": freq_rate_mismatch,
        "live_freq_rows": len(live_freq),
        "live_empty_exposure": live_empty_exp,
        "live_empty_exposure_with_rate": live_empty_with_rate,
        "live_join": live.get("source", {}).get("profile_regime_join"),
        "live_missingness": live["extra"]["census"]["missingness"],
        "live_population_labels": live["population"]["labels"],
    }


def control_disclosure() -> dict[str, Any]:
    live = _load_json(LIVE)
    recs = live["extra"]["control"]["records"]
    biting = [r for r in recs if r.get("raw_bite")]
    finite_collapse = [
        r["collapse_ratio"]
        for r in recs
        if _finite(r.get("collapse_ratio"))
    ]
    bite_collapse = [r["collapse_ratio"] for r in biting if _finite(r.get("collapse_ratio"))]
    a15_ok = 0
    a15_fail = 0
    a15_na = 0
    for rec in biting:
        md = rec.get("destroyed_mean")
        se = rec.get("raw_bootstrap_se")
        if not _finite(md) or not _finite(se):
            a15_na += 1
            continue
        if abs(float(md)) <= INTEGRITY_Z * float(se):
            a15_ok += 1
        else:
            a15_fail += 1
    singleton_records = 0
    singleton_groups = 0
    movable_groups = 0
    group_size_hist: Counter[int] = Counter()
    for rec in recs:
        gs = rec.get("group_sizes") or []
        if any(g == 1 for g in gs):
            singleton_records += 1
        for g in gs:
            group_size_hist[int(g) if int(g) <= 5 else 6] += 1
            if g == 1:
                singleton_groups += 1
            elif g >= 2:
                movable_groups += 1
    void_reasons = Counter(tuple(r.get("reasons") or []) for r in recs)
    notes = Counter(r.get("note") for r in recs)
    by_channel = {}
    for ch in ("swing_atr", "swing_duration_ns", "strong_move"):
        sub = [r for r in recs if r.get("channel") == ch]
        bite = [r for r in sub if r.get("raw_bite")]
        by_channel[ch] = {
            "n": len(sub),
            "raw_bite": len(bite),
            "destroyed_survives": sum(1 for r in sub if r.get("destroyed_survives")),
            "blocking_false": sum(1 for r in sub if r.get("blocking_pass") is False),
            "empty_note": sum(1 for r in sub if r.get("note")),
        }
    se_raw = [r.get("raw_bootstrap_se") for r in biting if _finite(r.get("raw_bootstrap_se"))]
    se_destroyed = [
        r.get("destroyed_bootstrap_se")
        for r in biting
        if _finite(r.get("destroyed_bootstrap_se"))
    ]
    return {
        "source": "python/experiments/EXP-104/results/analysis_results.json extra.control",
        "recomputed": False,
        "n_records": len(recs),
        "fixed_points": live["extra"]["control"].get("fixed_points"),
        "population_match": live["extra"]["control"].get("population_match"),
        "blocking_pass_all": all(r.get("blocking_pass") for r in recs),
        "destroyed_survives_any": any(r.get("destroyed_survives") for r in recs),
        "raw_bite_n": len(biting),
        "void_reasons": {str(k): v for k, v in void_reasons.items()},
        "notes": {str(k): v for k, v in notes.items()},
        "collapse_finite_n": len(finite_collapse),
        "collapse_finite_min": min(finite_collapse) if finite_collapse else None,
        "collapse_finite_max": max(finite_collapse) if finite_collapse else None,
        "bite_collapse_n": len(bite_collapse),
        "bite_collapse_min": min(bite_collapse) if bite_collapse else None,
        "bite_collapse_max": max(bite_collapse) if bite_collapse else None,
        "bite_collapse_median": (
            sorted(bite_collapse)[len(bite_collapse) // 2] if bite_collapse else None
        ),
        "a15_destroyed_inside_raw_bite_band": a15_ok,
        "a15_fail": a15_fail,
        "a15_na": a15_na,
        "integrity_z": INTEGRITY_Z,
        "singleton_records": singleton_records,
        "singleton_groups_sum_over_records": singleton_groups,
        "movable_groups_sum_over_records": movable_groups,
        "group_size_hist_1_to_5_plus": dict(group_size_hist),
        "by_channel": by_channel,
        "raw_se_bite_min": min(se_raw) if se_raw else None,
        "raw_se_bite_max": max(se_raw) if se_raw else None,
        "destroyed_se_bite_min": min(se_destroyed) if se_destroyed else None,
        "destroyed_se_bite_max": max(se_destroyed) if se_destroyed else None,
        "void_populations": live["extra"].get("void_populations"),
    }


def sign_tables(outcomes: dict[str, Any], frequency: dict[str, Any]) -> dict[str, Any]:
    live = _load_json(LIVE)
    live_lookup = {}
    for rec in live["value_rows"]:
        st = rec["stratum"]
        key = tuple(st.get(c) for c in STRATUM) + (rec["channel"], rec["arm"])
        live_lookup[key] = rec

    def interval_class(interval: list[float] | None) -> str:
        if not interval or not _finite(interval[0]) or not _finite(interval[1]):
            return "NO_INTERVAL"
        lo, hi = float(interval[0]), float(interval[1])
        if lo > 0:
            return "CI_ABOVE_0"
        if hi < 0:
            return "CI_BELOW_0"
        return "CI_OVERLAPS_0"

    summary: dict[str, Any] = {}
    for channel in ("swing_atr", "swing_duration_ns", "strong_move", "swing_price", "swing_bps"):
        by_arm: dict[str, Counter[str]] = {"LOW": Counter(), "HIGH": Counter()}
        by_symbol: dict[str, Counter[str]] = defaultdict(Counter)
        by_tf: dict[str, Counter[str]] = defaultdict(Counter)
        n_used = 0
        for rec in outcomes["rows"]:
            if rec["channel"] != channel or rec["empty"]:
                continue
            st = rec["stratum"]
            if st.get("confirmation_method") is None:
                continue
            key = tuple(st[c] for c in STRATUM) + (channel, rec["arm"])
            live_rec = live_lookup.get(key)
            cls = interval_class((live_rec or {}).get("observed", {}).get("interval"))
            by_arm[rec["arm"]][cls] += 1
            by_symbol[str(st["archive_symbol"])][cls] += 1
            by_tf[str(st["timeframe"])][cls] += 1
            n_used += 1
        summary[channel] = {
            "n": n_used,
            "by_arm": {k: dict(v) for k, v in by_arm.items()},
            "by_symbol": {k: dict(v) for k, v in by_symbol.items()},
            "by_timeframe": {k: dict(v) for k, v in by_tf.items()},
        }
    freq_sign = {"LOW": Counter(), "HIGH": Counter()}
    freq_by_symbol: dict[str, Counter[str]] = defaultdict(Counter)
    freq_by_tf: dict[str, Counter[str]] = defaultdict(Counter)
    live_freq_unc = {
        tuple(u["stratum"].get(c) for c in STRATUM): u
        for u in live["extra"]["frequency_census"][0]["uncertainty"]
    }
    tf_block = {"15m": "96", "30m": "48", "60m": "24", "1h": "24"}
    for rec in frequency["rows"]:
        if rec["causal_regime"] not in ("LOW", "HIGH"):
            continue
        if rec["empty_exposure_reason"]:
            freq_sign[rec["causal_regime"]]["EMPTY_EXPOSURE"] += 1
            continue
        contrast = rec["contrast_minus_mid"]
        if not _finite(contrast):
            freq_sign[rec["causal_regime"]]["NULL"] += 1
            continue
        key = tuple(rec[c] for c in STRATUM)
        unc = live_freq_unc.get(key)
        block = tf_block.get(str(rec["timeframe"]), "24")
        interval = None
        if unc:
            interval = (unc.get("sensitivities") or {}).get(block, {}).get("intervals", {}).get(
                rec["causal_regime"]
            )
        cls = interval_class(interval)
        # if no interval, fall back to point-sign disclosure
        if cls == "NO_INTERVAL":
            cls = "POINT_POS" if contrast > 0 else "POINT_NEG" if contrast < 0 else "POINT_ZERO"
        freq_sign[rec["causal_regime"]][cls] += 1
        freq_by_symbol[str(rec["archive_symbol"])][cls] += 1
        freq_by_tf[str(rec["timeframe"])][cls] += 1
    summary["frequency"] = {
        "by_arm": {k: dict(v) for k, v in freq_sign.items()},
        "by_symbol": {k: dict(v) for k, v in freq_by_symbol.items()},
        "by_timeframe": {k: dict(v) for k, v in freq_by_tf.items()},
    }
    # point-sign of recomputed contrasts
    point = {"LOW": Counter(), "HIGH": Counter()}
    for rec in frequency["rows"]:
        if rec["causal_regime"] not in ("LOW", "HIGH") or rec["empty_exposure_reason"]:
            continue
        c = rec["contrast_minus_mid"]
        if not _finite(c):
            continue
        point[rec["causal_regime"]]["pos" if c > 0 else "neg" if c < 0 else "zero"] += 1
    summary["frequency_point_sign"] = {k: dict(v) for k, v in point.items()}
    outcome_point = {}
    for channel in ("swing_atr", "swing_duration_ns", "strong_move"):
        c = {"LOW": Counter(), "HIGH": Counter()}
        for rec in outcomes["rows"]:
            if rec["channel"] != channel or rec["empty"]:
                continue
            est = rec["estimate"]
            if not _finite(est):
                continue
            c[rec["arm"]]["pos" if est > 0 else "neg" if est < 0 else "zero"] += 1
        outcome_point[channel] = {k: dict(v) for k, v in c.items()}
    summary["outcome_point_sign"] = outcome_point
    return summary


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    integrity = integrity_files()
    later, raid_facts = raid_scan()
    outcomes = outcome_stats(later)
    frequency = frequency_census()
    comparison = compare_live(outcomes, frequency, raid_facts)
    control = control_disclosure()
    signs = sign_tables(outcomes, frequency)
    compact_outcomes = []
    for rec in outcomes["rows"]:
        if rec["empty"]:
            continue
        compact_outcomes.append(
            {
                **rec["stratum"],
                "channel": rec["channel"],
                "arm": rec["arm"],
                "arm_n": rec["arm_n"],
                "comparator_n": rec["comparator_n"],
                "estimate": rec["estimate"],
                "arm_mean": rec["arm_mean"],
                "comparator_mean": rec["comparator_mean"],
                "arm_median": rec["arm_median"],
                "comparator_median": rec["comparator_median"],
            }
        )
    summary = {
        "experiment": "EXP-104",
        "hypothesis": "HYP-004",
        "scripts": ["python/experiments/EXP-104/analysis_code/interrogate.py"],
        "source_root": str(SOURCE_ROOT),
        "live_artifact": str(LIVE),
        "integrity": integrity,
        "raid_facts": raid_facts,
        "outcomes": {
            "n_contrast_rows": outcomes["n_contrast_rows"],
            "n_empty_arm_rows": outcomes["n_empty_arm_rows"],
            "pooled_disclosure": outcomes["pooled_disclosure"],
            "swing_atr_by_symbol": outcomes["swing_atr_by_symbol"],
            "swing_atr_by_timeframe": outcomes["swing_atr_by_timeframe"],
            "tails": outcomes["tails"],
        },
        "frequency": {
            "n_rows": frequency["n_rows"],
            "n_empty_exposure_rows": frequency["n_empty_exposure_rows"],
            "provenance": frequency["provenance"],
        },
        "comparison": comparison,
        "control": control,
        "signs": signs,
        "compact_outcomes": compact_outcomes,
        "frequency_rows": frequency["rows"],
    }
    SUMMARY_PATH.write_text(json.dumps(summary, allow_nan=True), encoding="utf-8")
    print(json.dumps({
        "wrote": str(SUMMARY_PATH),
        "n_later": raid_facts["n_later_swing"],
        "n_train": raid_facts["n_train"],
        "outcome_mean_mismatch": comparison["outcome_mean_mismatch"],
        "outcome_n_mismatch": comparison["outcome_n_mismatch"],
        "freq_n_mismatch": comparison["freq_n_mismatch"],
        "freq_rate_mismatch": comparison["freq_rate_mismatch"],
        "n_empty_arm": outcomes["n_empty_arm_rows"],
        "n_empty_exposure": frequency["n_empty_exposure_rows"],
        "provenance": frequency["provenance"],
    }, indent=2))


if __name__ == "__main__":
    main()
