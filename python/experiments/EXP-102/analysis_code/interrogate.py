"""Independent EXP-102 interrogation (no analysis.py import).

Full 264-cell parquet scan skipped per orchestrator steering. Per-stratum
contrasts come from the registered live analysis_results.json. Means/medians
for one cell are recomputed from raids.parquet. Destroy/bootstrap figures
are copied from extra.control and are not recomputed.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import polars as pl

from xen.estimand_validation import check_no_local_accounting

EXPERIMENT = "EXP-102"
PROJECT_ROOT = Path(__file__).resolve().parents[4]
SOURCE_ROOT = PROJECT_ROOT / "data/nautilus_runs/EXP-100/full"
EXP_ROOT = PROJECT_ROOT / "python/experiments/EXP-102"
LIVE_RESULTS = EXP_ROOT / "results/analysis_results.json"
FAMILY_GATE = PROJECT_ROOT / "python/experiments/EXP-100/results/estimand_validation.json"
LOCAL_GATE = EXP_ROOT / "results/estimand_validation.json"
FIXTURE = EXP_ROOT / "results/fixture_integrity.json"
OUT_JSON = Path(__file__).resolve().parent / "interrogate_summary.json"

TRAIN_START_NS = 1_622_592_060_000_000_000
TRAIN_END_NS = 1_700_611_200_000_000_000
INTEGRITY_Z = 2.8
NS_PER_HOUR = 3_600_000_000_000
SAMPLE_CELL = "ctrader-eurusd-15m-breakout_bar-1h-previous_1h"
STRATUM = (
    "archive_symbol",
    "timeframe",
    "confirmation_method",
    "confirmation_reference",
    "side",
    "config",
)
CHANNELS = ("swing_atr", "swing_duration_ns", "strong_move", "swing_bps", "swing_price")
PRIMARY = ("swing_atr", "swing_duration_ns", "strong_move")


def _is_num(value: Any) -> bool:
    return isinstance(value, (int, float)) and not (isinstance(value, float) and math.isnan(value))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_gate(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    cells = payload.get("cells") or []
    return {
        "path": str(path),
        "blocking_pass": payload.get("blocking_pass"),
        "n_cells": payload.get("n_cells"),
        "cell_blocking_pass_true": sum(1 for cell in cells if cell.get("blocking_pass") is True),
        "cell_blocking_pass_false": sum(1 for cell in cells if cell.get("blocking_pass") is False),
        "no_cost_charged_ok": sum(
            1 for cell in cells if (cell.get("no_cost_charged") or {}).get("ok") is True
        ),
        "sha256": _sha256(path),
        "sha256_prefix": _sha256(path)[:16],
    }


def _band(count: int) -> str:
    if count == 0:
        return "0"
    if count == 1:
        return "1"
    return "2+"


def _recompute_one_cell(cell_name: str) -> dict[str, Any]:
    cell = SOURCE_ROOT / cell_name
    frame = pl.read_parquet(cell / "raids.parquet")
    meta = json.loads((cell / "run_metadata.json").read_text())
    later = frame.filter(
        (pl.col("status") == "COMPLETED")
        & pl.col("primary_attribution").fill_null(False)
        & pl.col("primary_completed").fill_null(False)
    ).with_columns(
        pl.when(pl.col("prior_raid_count") == 0)
        .then(pl.lit("0"))
        .when(pl.col("prior_raid_count") == 1)
        .then(pl.lit("1"))
        .otherwise(pl.lit("2+"))
        .alias("count_band")
    )
    duration_mismatch = frame.filter(
        pl.col("duration_ns").is_not_null()
        & pl.col("swing_duration_ns").is_not_null()
        & (pl.col("duration_ns") != pl.col("swing_duration_ns"))
    ).height
    duration_nullness = frame.filter(
        pl.col("duration_ns").is_null() != pl.col("swing_duration_ns").is_null()
    ).height
    after_train = 0
    before_train = 0
    for column in ("sweep_ts_ns", "return_ts_ns", "confirmation_ts_ns", "endpoint_ts_ns"):
        before_train += frame.filter(
            pl.col(column).is_not_null() & (pl.col(column) < TRAIN_START_NS)
        ).height
        after_train += frame.filter(
            pl.col(column).is_not_null() & (pl.col(column) > TRAIN_END_NS)
        ).height
    causal = frame.filter(
        (
            pl.col("sweep_ts_ns").is_not_null()
            & pl.col("return_ts_ns").is_not_null()
            & (pl.col("return_ts_ns") < pl.col("sweep_ts_ns"))
        )
        | (
            pl.col("return_ts_ns").is_not_null()
            & pl.col("confirmation_ts_ns").is_not_null()
            & (pl.col("confirmation_ts_ns") < pl.col("return_ts_ns"))
        )
        | (
            pl.col("confirmation_ts_ns").is_not_null()
            & pl.col("endpoint_ts_ns").is_not_null()
            & (pl.col("endpoint_ts_ns") < pl.col("confirmation_ts_ns"))
        )
    ).height
    partner_name = cell_name.replace("breakout_bar", "level_close")
    partner = pl.read_parquet(SOURCE_ROOT / partner_name / "raids.parquet", columns=["raid_id"])
    contrasts: list[dict[str, Any]] = []
    for side in ("HIGH", "LOW"):
        side_df = later.filter(pl.col("side") == side)
        for channel in CHANNELS:
            eligible = side_df
            if channel in {"swing_atr", "strong_move"}:
                eligible = eligible.filter(
                    pl.col("profile_undefined_reason").fill_null("") != "ATR_UNDEFINED"
                )
            eligible = eligible.filter(pl.col(channel).is_not_null() & pl.col(channel).is_finite())
            stats = {
                band: eligible.filter(pl.col("count_band") == band)
                .select(
                    n=pl.len(),
                    mean=pl.col(channel).cast(pl.Float64).mean(),
                    median=pl.col(channel).cast(pl.Float64).median(),
                )
                .to_dicts()[0]
                for band in ("0", "1", "2+")
            }
            for arm in ("1", "2+"):
                arm_n = int(stats[arm]["n"])
                cmp_n = int(stats["0"]["n"])
                arm_mean = stats[arm]["mean"]
                cmp_mean = stats["0"]["mean"]
                contrasts.append(
                    {
                        "side": side,
                        "channel": channel,
                        "arm": arm,
                        "arm_n": arm_n,
                        "comparator_n": cmp_n,
                        "arm_mean": arm_mean,
                        "comparator_mean": cmp_mean,
                        "estimate": None
                        if arm_mean is None or cmp_mean is None
                        else float(arm_mean) - float(cmp_mean),
                        "arm_median": stats[arm]["median"],
                        "comparator_median": stats["0"]["median"],
                    }
                )
    return {
        "cell": cell_name,
        "partner": partner_name,
        "n_rows": frame.height,
        "n_unique_raid_id": frame["raid_id"].n_unique(),
        "partner_n_rows": partner.height,
        "partner_unique_raid_id": partner["raid_id"].n_unique(),
        "raid_id_set_equal": set(frame["raid_id"].to_list()) == set(partner["raid_id"].to_list()),
        "later_n": later.height,
        "later_by_band": later["count_band"].value_counts().to_dicts(),
        "later_atr_undefined": later.filter(
            pl.col("profile_undefined_reason") == "ATR_UNDEFINED"
        ).height,
        "status": frame["status"].value_counts().to_dicts(),
        "duration_alias_mismatches": duration_mismatch,
        "duration_alias_nullness": duration_nullness,
        "before_train": before_train,
        "after_train": after_train,
        "causal_failures": causal,
        "cost_model": meta.get("cost_model"),
        "nautilus_version": meta.get("nautilus_version"),
        "emission_contract_version": meta.get("emission_contract_version"),
        "one_backtest_node": meta.get("one_backtest_node"),
        "n_fills": meta.get("n_fills"),
        "n_orders": meta.get("n_orders"),
        "n_positions": meta.get("n_positions"),
        "config_hash_present": bool(meta.get("config_hash")),
        "event_log_sha256_present": bool(meta.get("event_log_sha256")),
        "contrasts": contrasts,
    }


def _match_cell_to_live(cell: dict[str, Any], live_rows: list[dict[str, Any]]) -> dict[str, Any]:
    mismatches = []
    matched = 0
    for rec in cell["contrasts"]:
        hits = [
            row
            for row in live_rows
            if row["channel"] == rec["channel"]
            and row["arm"] == rec["arm"]
            and row["stratum"].get("archive_symbol") == "EURUSD"
            and row["stratum"].get("timeframe") == "15m"
            and row["stratum"].get("confirmation_method") == "BREAKOUT_BAR"
            and row["stratum"].get("confirmation_reference") == "1H"
            and row["stratum"].get("config") == "PREVIOUS_1H"
            and row["stratum"].get("side") == rec["side"]
        ]
        if not hits:
            mismatches.append({"type": "missing_live", "rec": rec})
            continue
        observed = hits[0]["observed"]
        matched += 1
        diffs = {}
        for field in ("arm_n", "comparator_n"):
            if rec[field] != observed.get(field):
                diffs[field] = [rec[field], observed.get(field)]
        for field in ("arm_mean", "comparator_mean", "estimate"):
            left, right = rec[field], observed.get(field)
            if left is None or not _is_num(right):
                if left is not None or _is_num(right):
                    diffs[field] = [left, right]
                continue
            scale = max(abs(float(left)), abs(float(right)), 1e-12)
            if abs(float(left) - float(right)) > max(1e-9 * scale, 1e-12):
                diffs[field] = [left, right]
        if diffs:
            mismatches.append({"type": "value", "side": rec["side"], "channel": rec["channel"], "arm": rec["arm"], "diffs": diffs})
    return {"matched": matched, "mismatches": mismatches}


def _ci_class(interval: list[float] | None) -> str:
    if not interval:
        return "no_interval"
    low, high = interval
    if low > 0:
        return "ci_gt_0"
    if high < 0:
        return "ci_lt_0"
    return "overlap_0"


def _summarize_live(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload["value_rows"]
    finite = [row for row in rows if (row.get("observed") or {}).get("reason") is None]
    empty = [row for row in rows if (row.get("observed") or {}).get("reason") == "EMPTY_ARM_OR_COMPARATOR"]
    ci_counts: dict[str, dict[str, int]] = {}
    layer_counts: dict[str, dict[str, dict[str, int]]] = {}
    n_lists: dict[str, list[int]] = {}
    est_lists: dict[str, list[float]] = {}
    median_flip: dict[str, dict[str, int]] = {}
    block_flip = {channel: {"L2": 0, "L10": 0, "n": 0} for channel in PRIMARY}
    seed_straddle = {channel: {"excl0": 0, "straddle": 0} for channel in PRIMARY}
    opposite_atr: list[dict[str, Any]] = []
    for row in finite:
        channel = row["channel"]
        arm = row["arm"]
        key = f"{arm}|{channel}"
        klass = _ci_class((row.get("observed") or {}).get("interval"))
        ci_counts.setdefault(key, Counter())[klass] += 1
        observed = row["observed"]
        n_lists.setdefault(f"{key}|arm", []).append(int(observed.get("arm_n") or 0))
        n_lists.setdefault(f"{key}|cmp", []).append(int(observed.get("comparator_n") or 0))
        if _is_num(observed.get("estimate")):
            est_lists.setdefault(key, []).append(float(observed["estimate"]))
        med = (row.get("medians") or {}).get("contrast")
        est = observed.get("estimate")
        flip_key = key
        median_flip.setdefault(flip_key, Counter())
        if _is_num(med) and _is_num(est) and med != 0 and est != 0:
            median_flip[flip_key]["agree" if (med > 0) == (est > 0) else "flip"] += 1
        stratum = row["stratum"]
        for layer_name, layer_value in (
            ("archive_symbol", stratum.get("archive_symbol")),
            ("timeframe", stratum.get("timeframe")),
            ("confirmation_method", stratum.get("confirmation_method")),
            ("side", stratum.get("side")),
        ):
            layer_counts.setdefault(f"{key}|{layer_name}|{layer_value}", Counter())[klass] += 1
        if channel in PRIMARY:
            block_flip[channel]["n"] += 1
            base = klass
            if _ci_class((row.get("observed_L2") or {}).get("interval")) != base:
                block_flip[channel]["L2"] += 1
            if _ci_class((row.get("observed_L10") or {}).get("interval")) != base:
                block_flip[channel]["L10"] += 1
            if base in {"ci_gt_0", "ci_lt_0"}:
                seed_straddle[channel]["excl0"] += 1
                low_range = observed.get("seed_low_range") or [0, 0]
                if low_range[0] <= 0 <= low_range[1]:
                    seed_straddle[channel]["straddle"] += 1
        if channel == "swing_atr" and klass == "ci_gt_0":
            opposite_atr.append(
                {
                    "arm": arm,
                    "stratum": stratum,
                    "estimate": observed.get("estimate"),
                    "interval": observed.get("interval"),
                    "arm_n": observed.get("arm_n"),
                    "comparator_n": observed.get("comparator_n"),
                    "n_clusters": observed.get("n_clusters"),
                }
            )

    def _pct(values: list[float], q: float) -> float | None:
        if not values:
            return None
        ordered = sorted(values)
        return ordered[int(q * (len(ordered) - 1))]

    n_summary = {
        key: {
            "n": len(vals),
            "min": min(vals),
            "median": sorted(vals)[len(vals) // 2],
            "max": max(vals),
        }
        for key, vals in n_lists.items()
    }
    est_summary = {
        key: {
            "n": len(vals),
            "p05": _pct(vals, 0.05),
            "median": _pct(vals, 0.5),
            "p95": _pct(vals, 0.95),
        }
        for key, vals in est_lists.items()
    }

    control = payload["extra"]["control"]["records"]
    finite_ctrl = [row for row in control if _is_num(row.get("raw_estimate"))]
    collapses = [row["collapse_ratio"] for row in finite_ctrl if _is_num(row.get("collapse_ratio"))]
    bite_true = [row for row in finite_ctrl if row.get("raw_bite") is True]
    bite_collapses = [row["collapse_ratio"] for row in bite_true if _is_num(row.get("collapse_ratio"))]
    singleton_groups = 0
    singleton_records = 0
    group_total = 0
    void_reasons: Counter[str] = Counter()
    notes = Counter(row.get("note") for row in control)
    a15_inside = a15_outside = a15_no_se = 0
    se_raw_vals = [row.get("raw_bootstrap_se") for row in bite_true if _is_num(row.get("raw_bootstrap_se"))]
    for row in control:
        for reason in row.get("reasons") or []:
            void_reasons[str(reason)] += 1
        sizes = row.get("group_sizes") or []
        group_total += len(sizes)
        if any(size == 1 for size in sizes):
            singleton_records += 1
        singleton_groups += sum(1 for size in sizes if size == 1)
        if row.get("raw_bite") and _is_num(row.get("raw_estimate")):
            se = row.get("raw_bootstrap_se")
            destroyed = row.get("destroyed_mean")
            if not _is_num(se):
                a15_no_se += 1
            elif _is_num(destroyed) and abs(destroyed) <= INTEGRITY_Z * float(se):
                a15_inside += 1
            else:
                a15_outside += 1

    empty_strata = {
        (
            row["stratum"].get("archive_symbol"),
            row["stratum"].get("timeframe"),
            row["stratum"].get("config"),
            row["stratum"].get("side"),
            row["stratum"].get("confirmation_method"),
        )
        for row in empty
    }

    return {
        "n_value_rows": len(rows),
        "n_finite": len(finite),
        "n_empty": len(empty),
        "n_empty_strata": len(empty_strata),
        "empty_method_null": sum(1 for row in empty if row["stratum"].get("confirmation_method") is None),
        "independent_arms_false": sum(
            1 for row in finite if row["observed"].get("independent_arms") is False
        ),
        "ci_counts": {key: dict(value) for key, value in ci_counts.items()},
        "layer_ci_counts": {key: dict(value) for key, value in layer_counts.items()},
        "n_summary": n_summary,
        "est_summary": est_summary,
        "median_flip": {key: dict(value) for key, value in median_flip.items()},
        "block_flip": block_flip,
        "seed_straddle": seed_straddle,
        "opposite_atr_ci_gt_0": opposite_atr,
        "integrity": payload.get("integrity"),
        "population": payload.get("population"),
        "source_attestation": payload.get("source", {}).get("attestation"),
        "integrity_evidence": payload.get("extra", {}).get("integrity_evidence"),
        "void_populations": payload.get("extra", {}).get("void_populations"),
        "control": {
            "n_records": len(control),
            "notes": {str(k): v for k, v in notes.items()},
            "blocking_pass_true": sum(1 for row in control if row.get("blocking_pass") is True),
            "blocking_pass_false": sum(1 for row in control if row.get("blocking_pass") is False),
            "fixed_points_nonzero": sum(1 for row in control if (row.get("fixed_points") or 0) != 0),
            "destroyed_survives_true": sum(1 for row in control if row.get("destroyed_survives") is True),
            "population_match_false": sum(1 for row in control if row.get("population_match") is False),
            "raw_bite_true": sum(1 for row in control if row.get("raw_bite") is True),
            "finite_raw": len(finite_ctrl),
            "collapse_n": len(collapses),
            "collapse_min": min(collapses) if collapses else None,
            "collapse_p05": _pct(collapses, 0.05),
            "collapse_median": _pct(collapses, 0.5),
            "collapse_p95": _pct(collapses, 0.95),
            "collapse_max": max(collapses) if collapses else None,
            "abs_collapse_lt_0_5": sum(1 for value in collapses if abs(value) < 0.5),
            "abs_collapse_gt_1": sum(1 for value in collapses if abs(value) > 1),
            "bite_n": len(bite_true),
            "bite_collapse_n": len(bite_collapses),
            "bite_collapse_median": _pct(bite_collapses, 0.5),
            "bite_collapse_p05": _pct(bite_collapses, 0.05),
            "bite_collapse_p95": _pct(bite_collapses, 0.95),
            "bite_abs_lt_0_5": sum(1 for value in bite_collapses if abs(value) < 0.5),
            "singleton_groups": singleton_groups,
            "singleton_records": singleton_records,
            "group_total": group_total,
            "void_reasons": dict(void_reasons),
            "a15_bite_destroy_inside_raw_se_band": a15_inside,
            "a15_bite_destroy_outside_raw_se_band": a15_outside,
            "a15_bite_no_se": a15_no_se,
            "raw_bootstrap_se_bite_median": _pct([float(v) for v in se_raw_vals], 0.5) if se_raw_vals else None,
            "note": "destroy/bootstrap figures copied from registered live extra.control; not recomputed",
        },
        "census_live": {
            "count_band": payload["extra"]["census"].get("count_band"),
            "status": payload["extra"]["census"].get("status"),
            "missingness": payload["extra"]["census"].get("missingness"),
            "exact_prior_n_keys": len(payload["extra"]["census"].get("exact_prior_raid_count") or {}),
            "by_stratum_arm_n": len(payload["extra"]["census"].get("by_stratum_arm") or []),
        },
        "zero_cost_disclosure": payload.get("zero_cost_disclosure"),
    }


def main() -> int:
    code_dir = EXP_ROOT / "code"
    local_accounting = (
        {"ok": True, "banned_defs_found": [], "note": "no python/experiments/EXP-102/code directory"}
        if not code_dir.exists()
        else check_no_local_accounting(code_dir)
    )
    family_gate = _load_gate(FAMILY_GATE)
    local_gate = _load_gate(LOCAL_GATE)
    sibling_hashes = {
        exp: _sha256(PROJECT_ROOT / "python/experiments" / exp / "results/estimand_validation.json")[:16]
        for exp in ("EXP-100", "EXP-101", "EXP-102", "EXP-103", "EXP-104")
        if (PROJECT_ROOT / "python/experiments" / exp / "results/estimand_validation.json").exists()
    }
    live = json.loads(LIVE_RESULTS.read_text())
    fixture = json.loads(FIXTURE.read_text())
    cell = _recompute_one_cell(SAMPLE_CELL)
    match = _match_cell_to_live(cell, live["value_rows"])
    live_summary = _summarize_live(live)
    fixture_records = ((fixture.get("extra") or {}).get("control") or {}).get("records") or []
    n_dirs = sum(1 for path in SOURCE_ROOT.iterdir() if path.is_dir())
    summary = {
        "experiment": EXPERIMENT,
        "hypothesis": "HYP-002 later-swing outcomes differ by prior-raid count vs count-zero",
        "source_root": str(SOURCE_ROOT),
        "did_not_import_analysis_py": True,
        "did_not_rerun_bootstrap_or_destroy": True,
        "did_not_read_test_or_holdout": True,
        "full_parquet_scan": False,
        "one_cell_recompute": SAMPLE_CELL,
        "n_source_dirs": n_dirs,
        "gates": {
            "family": family_gate,
            "exp102_copy": local_gate,
            "sibling_sha256_prefix": sibling_hashes,
            "local_accounting": local_accounting,
            "no_local_code_dir": not code_dir.exists(),
        },
        "sample_cell": {k: v for k, v in cell.items() if k != "contrasts"} | {"n_contrasts": len(cell["contrasts"])},
        "sample_cell_contrasts": cell["contrasts"],
        "sample_cell_vs_live": match,
        "live_summary": live_summary,
        "fixture": {
            "blocking_pass": (fixture.get("integrity") or {}).get("blocking_pass"),
            "reasons": (fixture.get("integrity") or {}).get("reasons"),
            "n_control_records": len(fixture_records),
            "records": [
                {
                    "channel": row.get("channel"),
                    "arm": row.get("arm"),
                    "raw_estimate": row.get("raw_estimate"),
                    "destroyed_mean": row.get("destroyed_mean"),
                    "collapse_ratio": row.get("collapse_ratio"),
                    "raw_bite": row.get("raw_bite"),
                    "destroyed_survives": row.get("destroyed_survives"),
                    "blocking_pass": row.get("blocking_pass"),
                    "raw_bootstrap_se": row.get("raw_bootstrap_se"),
                }
                for row in fixture_records
            ],
            "note": "fixture tripwire copied from results/fixture_integrity.json; not recomputed",
        },
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2, default=str))
    print(
        json.dumps(
            {
                "gates_blocking": family_gate["blocking_pass"],
                "sha_prefix": sibling_hashes,
                "sample_match": match,
                "n_finite": live_summary["n_finite"],
                "control_bite": live_summary["control"]["raw_bite_true"],
                "wrote": str(OUT_JSON),
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
