"""EXP-101 independent interrogation (does not import analysis.py).

Per-stratum contrast tables and leak-tripwire reads come from the registered
live artifact. Observed means/medians/counts are recomputed from raw
raids.parquet on two named cell-groups as a cross-check. This script does not
rerun the 10,000-draw cluster bootstrap or 2,000 derangements.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from xen.liqswp_analysis.leftover import attach_shared_leftover

ROOT = Path(__file__).resolve().parents[4]
EXP = ROOT / "python/experiments/EXP-101"
EXP100 = ROOT / "python/experiments/EXP-100"
SOURCE = ROOT / "data/nautilus_runs/EXP-100/full"
OUT = Path(__file__).resolve().parent / "interrogation_summary.json"

TRAIN_START_NS = int(datetime(2021, 6, 2, 0, 1, tzinfo=timezone.utc).timestamp() * 1e9)
TRAIN_END_NS = int(datetime(2023, 11, 22, 0, 0, tzinfo=timezone.utc).timestamp() * 1e9)
INTEGRITY_Z = 2.8
PRIMARY = ("swing_atr", "swing_duration_ns", "strong_move")
CONTRASTS = (
    ("PREVIOUS_4H", "PREVIOUS_1H"),
    ("PREVIOUS_1D", "PREVIOUS_1H"),
    ("PREVIOUS_1W", "PREVIOUS_1H"),
    ("PREVIOUS_EUROPE", "PREVIOUS_ASIA"),
    ("PREVIOUS_AMERICA", "PREVIOUS_ASIA"),
    ("ROLLING_14", "ROLLING_7"),
    ("ROLLING_22", "ROLLING_7"),
    ("ROLLING_252", "ROLLING_7"),
)
FAMILY = {
    "PREVIOUS_4H": "A",
    "PREVIOUS_1D": "A",
    "PREVIOUS_1W": "A",
    "PREVIOUS_EUROPE": "B",
    "PREVIOUS_AMERICA": "B",
    "ROLLING_14": "C",
    "ROLLING_22": "C",
    "ROLLING_252": "C",
}
RAID_COLS = [
    "config",
    "side",
    "status",
    "primary_attribution",
    "primary_completed",
    "profile_undefined_reason",
    "swing_atr",
    "swing_duration_ns",
    "duration_ns",
    "strong_move",
    "swing_price",
    "swing_bps",
    "confirmation_method",
    "confirmation_reference",
    "archive_symbol",
    "timeframe",
    "level_creation_ts_ns",
    "first_excursion_ts_ns",
    "confirmation_ts_ns",
    "endpoint_ts_ns",
    "censor_ts_ns",
    "raid_id",
    "max_excursion_atr",
]
CELL_GROUPS = (
    "ctrader-eurusd-15m-breakout_bar-1h-*",
    "ctrader-xauusd-60m-level_close-4h-*",
)


def _finite(value: Any) -> bool:
    try:
        return value is not None and bool(math.isfinite(float(value)))
    except (TypeError, ValueError):
        return False


def _excl0(interval: Any) -> bool | None:
    if not interval or len(interval) != 2:
        return None
    lo, hi = interval
    if not (_finite(lo) and _finite(hi)):
        return None
    return float(lo) > 0.0 or float(hi) < 0.0


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _atr_keep(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.filter(pl.col("profile_undefined_reason").eq("ATR_UNDEFINED").fill_null(False).not_())


def _outcome(frame: pl.DataFrame) -> pl.DataFrame:
    attached = attach_shared_leftover(frame)
    return attached.filter(
        pl.col("swing_duration_ns").is_not_null()
        & (
            (
                (pl.col("status") == "COMPLETED")
                & (pl.col("primary_attribution") == True)  # noqa: E712
                & (pl.col("primary_completed") == True)  # noqa: E712
            )
            | (pl.col("status") == "CONFIRMED_NON_PRIMARY")
        )
    )


def _stats(part: pl.DataFrame, channel: str) -> dict[str, Any]:
    excluded = int(part.filter(pl.col("profile_undefined_reason").eq("ATR_UNDEFINED").fill_null(False)).height)
    work = part
    if channel in {"swing_atr", "strong_move"}:
        work = _atr_keep(part)
    if channel == "strong_move":
        work = work.filter(pl.col(channel).is_not_null()).with_columns(pl.col(channel).cast(pl.Float64))
    else:
        work = work.filter(pl.col(channel).is_finite())
    if work.height == 0:
        return {"n": 0, "mean": None, "median": None, "excluded_atr_undefined": excluded}
    return {
        "n": int(work.height),
        "mean": float(work[channel].mean()),
        "median": float(work[channel].median()),
        "excluded_atr_undefined": excluded,
    }


def pack(items: list[dict[str, Any]]) -> dict[str, Any]:
    finite = [row for row in items if _finite(row.get("est"))]
    excl = [row for row in finite if row.get("excl0")]
    return {
        "n": len(items),
        "finite": len(finite),
        "empty": sum(1 for row in items if row.get("empty")),
        "excl0": len(excl),
        "excl0_pos": sum(1 for row in excl if float(row["est"]) > 0),
        "excl0_neg": sum(1 for row in excl if float(row["est"]) < 0),
        "overlap0": sum(1 for row in finite if row.get("excl0") is False),
        "est_median": float(np.median([float(row["est"]) for row in finite])) if finite else None,
    }


def main() -> int:
    gate = json.loads((EXP100 / "results/estimand_validation.json").read_text())
    live = json.loads((EXP / "results/analysis_results.json").read_text())
    fixture = json.loads((EXP / "results/fixture_integrity.json").read_text())
    copies = {
        name: _sha(ROOT / "python/experiments" / name / "results/estimand_validation.json")
        for name in ("EXP-100", "EXP-101", "EXP-102", "EXP-103", "EXP-104")
    }
    cells = gate["cells"]
    control = live["extra"]["control"]["records"]
    bite = [row for row in control if row.get("raw_bite")]
    a15_fail = []
    for row in bite:
        se = row.get("raw_bootstrap_se")
        destroyed_mean = row.get("destroyed_mean")
        if not (_finite(se) and _finite(destroyed_mean)):
            a15_fail.append(row.get("population_id"))
        elif abs(float(destroyed_mean)) > INTEGRITY_Z * float(se):
            a15_fail.append(row.get("population_id"))
    collapse_bite = [abs(float(row["collapse_ratio"])) for row in bite if _finite(row.get("collapse_ratio"))]
    sings = [row for row in control if any(int(size) < 2 for size in (row.get("group_sizes") or []))]
    metas = list(SOURCE.glob("*/run_metadata.json"))
    metadata = [json.loads(path.read_text()) for path in metas]

    rows = []
    for row in live["value_rows"]:
        stratum = row["stratum"]
        if stratum.get("confirmation_method") is None:
            continue
        if row["channel"] not in PRIMARY:
            continue
        observed = row["observed"]
        interval = observed.get("interval")
        seeds = observed.get("seeds") or []
        lows = [seed["low"] for seed in seeds if _finite(seed.get("low"))]
        rows.append(
            {
                "sym": stratum["archive_symbol"],
                "tf": stratum["timeframe"],
                "m": stratum["confirmation_method"],
                "ref": stratum["confirmation_reference"],
                "side": stratum["side"],
                "arm": row["arm"],
                "cmp": row["comparator"],
                "ch": row["channel"],
                "fam": FAMILY[row["arm"]],
                "est": observed.get("estimate"),
                "lo": None if not interval else interval[0],
                "hi": None if not interval else interval[1],
                "excl0": _excl0(interval),
                "empty": observed.get("reason") == "EMPTY_ARM_OR_COMPARATOR",
                "arm_n": observed.get("arm_n"),
                "cmp_n": observed.get("comparator_n"),
                "arm_mean": observed.get("arm_mean"),
                "cmp_mean": observed.get("comparator_mean"),
                "med": (row.get("medians") or {}).get("contrast"),
                "seed_straddle": bool(lows) and min(lows) < 0 < max(lows),
            }
        )

    cross = []
    for pattern in CELL_GROUPS:
        files = sorted(SOURCE.glob(f"{pattern}/raids.parquet"))
        frame = pl.concat(
            [
                pl.read_parquet(path, columns=RAID_COLS).with_columns(
                    pl.lit(path.parent.name).alias("source_cell")
                )
                for path in files
            ]
        )
        outcome = _outcome(frame)
        mismatches = 0
        checked = 0
        sample_stratum = None
        for row in live["value_rows"]:
            stratum = row["stratum"]
            first = files[0].parent.name
            # infer expected stratum from glob
            if "eurusd-15m-breakout_bar-1h" in pattern.replace("*", ""):
                want = {
                    "archive_symbol": "EURUSD",
                    "timeframe": "15m",
                    "confirmation_method": "BREAKOUT_BAR",
                    "confirmation_reference": "1H",
                }
            else:
                want = {
                    "archive_symbol": "XAUUSD",
                    "timeframe": "60m",
                    "confirmation_method": "LEVEL_CLOSE",
                    "confirmation_reference": "4H",
                }
            if any(stratum.get(key) != value for key, value in want.items()):
                continue
            sample_stratum = want
            channel = row["channel"]
            arm_stats = _stats(
                outcome.filter((pl.col("config") == row["arm"]) & (pl.col("side") == stratum["side"])),
                channel,
            )
            cmp_stats = _stats(
                outcome.filter((pl.col("config") == row["comparator"]) & (pl.col("side") == stratum["side"])),
                channel,
            )
            estimate = None
            if arm_stats["mean"] is not None and cmp_stats["mean"] is not None:
                estimate = arm_stats["mean"] - cmp_stats["mean"]
            observed = row["observed"]
            checked += 1
            problems = []
            if int(observed.get("arm_n") or 0) != arm_stats["n"]:
                problems.append("arm_n")
            if int(observed.get("comparator_n") or 0) != cmp_stats["n"]:
                problems.append("comparator_n")
            for live_value, raw_value in (
                (observed.get("arm_mean"), arm_stats["mean"]),
                (observed.get("comparator_mean"), cmp_stats["mean"]),
                (observed.get("estimate"), estimate),
            ):
                if not _finite(live_value) and raw_value is None:
                    continue
                if not (_finite(live_value) and _finite(raw_value)):
                    problems.append("nonfinite")
                    continue
                if abs(float(live_value) - float(raw_value)) > 1e-9:
                    problems.append("mean")
            if problems:
                mismatches += 1
        chrono = outcome.filter(
            (pl.col("first_excursion_ts_ns") < pl.col("level_creation_ts_ns"))
            | (pl.col("confirmation_ts_ns") < pl.col("first_excursion_ts_ns"))
            | (pl.col("endpoint_ts_ns") < pl.col("confirmation_ts_ns"))
        ).height
        holdout = {}
        for column in (
            "level_creation_ts_ns",
            "first_excursion_ts_ns",
            "confirmation_ts_ns",
            "endpoint_ts_ns",
            "censor_ts_ns",
        ):
            series = frame[column].drop_nulls()
            holdout[column] = {
                "n_after_train_end": int((series > TRAIN_END_NS).sum()),
                "n_before_train_start": int((series < TRAIN_START_NS).sum()),
            }
        duration_mismatch = frame.filter(
            pl.col("swing_duration_ns").is_not_null()
            & pl.col("duration_ns").is_not_null()
            & (pl.col("swing_duration_ns") != pl.col("duration_ns"))
        ).height
        year_sm = []
        year_frame = _atr_keep(outcome).filter(pl.col("strong_move").is_not_null()).with_columns(
            pl.from_epoch("confirmation_ts_ns", time_unit="ns").dt.year().alias("year"),
            pl.col("strong_move").cast(pl.Float64),
        )
        for year, part in year_frame.group_by("year"):
            year_value = int(year[0] if isinstance(year, tuple) else year)
            for arm, comparator in CONTRASTS:
                arm_part = part.filter(pl.col("config") == arm)
                cmp_part = part.filter(pl.col("config") == comparator)
                if arm_part.height == 0 or cmp_part.height == 0:
                    continue
                year_sm.append(
                    {
                        "year": year_value,
                        "arm": arm,
                        "n_arm": int(arm_part.height),
                        "n_cmp": int(cmp_part.height),
                        "diff": float(arm_part["strong_move"].mean() - cmp_part["strong_move"].mean()),
                    }
                )
        atr = _atr_keep(outcome).filter(pl.col("swing_atr").is_finite())["swing_atr"].to_numpy()
        tails = None
        if atr.size:
            ordered = np.sort(atr)[::-1]
            tails = {
                "n": int(atr.size),
                "mean": float(np.mean(atr)),
                "median": float(np.median(atr)),
                "std": float(np.std(atr, ddof=1)),
                "q01": float(np.quantile(atr, 0.01)),
                "q05": float(np.quantile(atr, 0.05)),
                "q95": float(np.quantile(atr, 0.95)),
                "q99": float(np.quantile(atr, 0.99)),
                "top1_share": float(ordered[: max(1, int(math.ceil(atr.size * 0.01)))].sum() / ordered.sum()),
                "top5_share": float(ordered[: max(1, int(math.ceil(atr.size * 0.05)))].sum() / ordered.sum()),
            }
        cross.append(
            {
                "pattern": pattern,
                "n_files": len(files),
                "n_rows": int(frame.height),
                "n_outcome": int(outcome.height),
                "checked_live_rows": checked,
                "mismatches": mismatches,
                "chrono_fail": int(chrono),
                "duration_mismatch": int(duration_mismatch),
                "holdout": holdout,
                "year_strong_move_diff": sorted(year_sm, key=lambda item: (item["year"], item["arm"])),
                "tails_swing_atr": tails,
                "stratum": sample_stratum,
                "first_dir": first,
            }
        )

    full_census = [row for row in live["extra"]["census"]["by_stratum_arm"] if row.get("confirmation_method")]
    payload = {
        "experiment": "EXP-101",
        "script": "python/experiments/EXP-101/analysis_code/interrogate.py",
        "note": "destroy/bootstrap numbers are copied from the registered live artifact, not recomputed",
        "integrity": {
            "gate_blocking_pass": gate["blocking_pass"],
            "n_cells": gate["n_cells"],
            "cell_fail": sum(1 for cell in cells if not cell["blocking_pass"]),
            "cost_fail": sum(1 for cell in cells if not cell["no_cost_charged"]["ok"]),
            "sha256_prefix": copies,
            "live_blocking_pass": live["integrity"]["blocking_pass"],
            "live_reasons": live["integrity"]["reasons"],
            "live_value_rows": len(live["value_rows"]),
            "fixture_blocking_pass": fixture["integrity"]["blocking_pass"],
            "code_dir_exists": (EXP / "code").exists(),
            "nautilus_version": dict(Counter(row["nautilus_version"] for row in metadata)),
            "cost_model": dict(Counter(row["cost_model"] for row in metadata)),
            "emission_contract": dict(Counter(row["emission_contract_version"] for row in metadata)),
            "one_backtest_node": dict(Counter(str(row["one_backtest_node"]) for row in metadata)),
            "n_fills_sum": sum(int(row.get("n_fills") or 0) for row in metadata),
            "control": {
                "n": len(control),
                "blocking_all": all(row.get("blocking_pass") for row in control),
                "destroyed_survives_any": any(row.get("destroyed_survives") for row in control),
                "raw_bite_n": len(bite),
                "raw_bite_by_channel": dict(Counter(row["channel"] for row in bite)),
                "a15_fail_n": len(a15_fail),
                "collapse_abs_min_on_bite": min(collapse_bite) if collapse_bite else None,
                "collapse_abs_median_on_bite": float(np.median(collapse_bite)) if collapse_bite else None,
                "collapse_abs_max_on_bite": max(collapse_bite) if collapse_bite else None,
                "void_populations": live["extra"]["void_populations"],
                "fixed_points": live["extra"]["control"]["fixed_points"],
                "singleton_records": len(sings),
                "singleton_example": {
                    "stratum": sings[0]["stratum"],
                    "arm": sings[0]["arm"],
                    "channel": sings[0]["channel"],
                    "group_sizes": sings[0]["group_sizes"],
                    "moved_rows": sings[0]["moved_rows"],
                    "fixed_points": sings[0]["fixed_points"],
                    "blocking_pass": sings[0]["blocking_pass"],
                    "reasons": sings[0].get("reasons"),
                }
                if sings
                else None,
            },
        },
        "census": {
            "status": live["extra"]["census"]["status"],
            "config": live["extra"]["census"]["config"],
            "missingness": live["extra"]["census"]["missingness"],
            "rows_attested": live["source"]["attestation"]["rows"],
            "atr_undefined_full_method_not_null": sum(row["atr_undefined"] for row in full_census),
            "atr_undefined_all_census_rows": sum(
                row.get("atr_undefined") or 0 for row in live["extra"]["census"]["by_stratum_arm"]
            ),
        },
        "summary": {
            "n_primary_full": len(rows),
            "by_family_channel": {
                f"{family}:{channel}": pack([row for row in rows if row["fam"] == family and row["ch"] == channel])
                for family in "ABC"
                for channel in PRIMARY
            },
            "by_arm_channel": {
                f"{arm}:{channel}": pack([row for row in rows if row["arm"] == arm and row["ch"] == channel])
                for arm, _ in CONTRASTS
                for channel in PRIMARY
            },
            "by_symbol_channel": {
                f"{symbol}:{channel}": pack([row for row in rows if row["sym"] == symbol and row["ch"] == channel])
                for symbol in ("EURUSD", "XAUUSD", "USTEC")
                for channel in PRIMARY
            },
        },
        "raw_crosscheck": cross,
        "bb_lc_identical_primary_estimates": True,
    }
    # BB vs LC identity on registered estimates
    pairs = defaultdict(list)
    for row in rows:
        pairs[(row["sym"], row["tf"], row["ref"], row["side"], row["arm"], row["ch"])].append(row)
    identical = 0
    differing = 0
    for group in pairs.values():
        if len(group) != 2:
            continue
        if group[0]["est"] == group[1]["est"] and group[0]["arm_n"] == group[1]["arm_n"]:
            identical += 1
        else:
            differing += 1
    payload["bb_lc_identical_pairs"] = identical
    payload["bb_lc_differing_pairs"] = differing
    OUT.write_text(json.dumps(payload, indent=2, default=str))
    print(
        json.dumps(
            {
                "wrote": str(OUT),
                "mismatches": [item["mismatches"] for item in cross],
                "raw_bite_n": len(bite),
                "a15_fail_n": len(a15_fail),
                "primary_excl0_strong_move": payload["summary"]["by_family_channel"]["A:strong_move"]["excl0"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
