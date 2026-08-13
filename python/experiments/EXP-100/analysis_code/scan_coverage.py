"""EXP-100 coverage / reconciliation scan — analyst-owned, raw emissions only.

Does not import python/experiments/EXP-100/code/. Verdict-bearing numbers come
from published parquet + run_metadata + the family estimand gate.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import polars as pl

REPO = Path(__file__).resolve().parents[4]
EMISSION_ROOT = REPO / "data/nautilus_runs/EXP-100/full"
GATE_ROOT = REPO / "python/experiments/EXP-100/results/execution/full"
FAMILY_GATE = REPO / "python/experiments/EXP-100/results/estimand_validation.json"
OUT_DIR = REPO / "python/experiments/EXP-100/results/analysis"

TRAIN_END = datetime(2023, 11, 22, tzinfo=timezone.utc)
TRAIN_START = datetime(2021, 6, 2, 0, 1, tzinfo=timezone.utc)
HOLDOUT_START = datetime(2024, 12, 13, tzinfo=timezone.utc)
NY = ZoneInfo("America/New_York")
MINUTE_NS = 60_000_000_000
INTEGRITY_Z = 2.8

EXPECTED_STATUSES = {
    "COMPLETED",
    "CONFIRMED_NON_PRIMARY",
    "FAILED_BREAKOUT",
    "RIGHT_CENSORED_EXCURSION",
    "RIGHT_CENSORED_CONFIRMATION",
    "RIGHT_CENSORED_ENDPOINT",
}
RETIRED_STATUSES = {"AMBIGUOUS_INTRABAR"}
LEVEL_STATUSES = {"SUPERSEDED_NO_RAID", "RIGHT_CENSORED"}
EXPECTED_LEVEL_CONFIGS = {
    "PREVIOUS_1H",
    "PREVIOUS_4H",
    "PREVIOUS_1D",
    "PREVIOUS_1W",
    "PREVIOUS_ASIA",
    "PREVIOUS_EUROPE",
    "PREVIOUS_AMERICA",
    "ROLLING_7",
    "ROLLING_14",
    "ROLLING_22",
    "ROLLING_252",
}
EXPECTED_GRID = {
    "15m": {"confirm_refs": {"1h"}, "n_cells": 66},
    "30m": {"confirm_refs": {"1h"}, "n_cells": 66},
    "60m": {"confirm_refs": {"1h", "4h"}, "n_cells": 132},
}


def _parse_cell(name: str) -> dict[str, str]:
    parts = name.split("-")
    return {
        "cell_id": name,
        "venue": parts[0],
        "symbol": parts[1].upper(),
        "timeframe": parts[2],
        "method": parts[3],
        "confirm_ref": parts[4],
        "level_config": "_".join(parts[5:]).upper(),
    }


def _ns_to_utc(ts_ns: int) -> datetime:
    return datetime.fromtimestamp(ts_ns / 1_000_000_000, tz=timezone.utc)


def _observation_minutes(tf: str) -> int:
    return int(tf.replace("m", ""))


def _status_counts(series: pl.Series) -> dict[str, int]:
    if series.len() == 0:
        return {}
    table = series.value_counts()
    return {
        str(status): int(count)
        for status, count in zip(table["status"], table["count"], strict=True)
    }


def _scan_one(cell_dir: Path) -> dict[str, Any]:
    ident = _parse_cell(cell_dir.name)
    meta = json.loads((cell_dir / "run_metadata.json").read_text(encoding="utf-8"))
    fence = json.loads((cell_dir / "fence_attestation.json").read_text(encoding="utf-8"))
    dc = meta["destroy_control"]
    cell_cfg = meta["run_config"]["cell"]
    obs_min = int(cell_cfg["observation_minutes"])

    raids = pl.read_parquet(cell_dir / "raids.parquet")
    levels = pl.read_parquet(cell_dir / "levels.parquet")
    tpo = pl.read_parquet(cell_dir / "tpo_profiles.parquet")
    marks = pl.read_parquet(
        cell_dir / "bar_marks.parquet",
        columns=["SourceCloseTime", "ts_event_ns"],
    )

    raid_status = _status_counts(raids["status"]) if raids.height else {}
    level_status = (
        _status_counts(levels["status"]) if levels.height else {}
    )
    unknown_raid_status = sorted(set(raid_status) - EXPECTED_STATUSES)
    unknown_level_status = sorted(set(level_status) - LEVEL_STATUSES)

    n_raid_ids = raids["raid_id"].n_unique() if raids.height else 0
    n_level_ids = levels["level_id"].n_unique() if levels.height else 0
    raid_dup = int(raids.height - n_raid_ids) if raids.height else 0
    level_dup = int(levels.height - n_level_ids) if levels.height else 0

    raid_set = set(raids["raid_id"].to_list()) if raids.height else set()
    tpo_set = set(tpo["raid_id"].to_list()) if tpo.height else set()
    missing_profiles = len(raid_set - tpo_set)
    extra_profiles = len(tpo_set - raid_set)

    defined = tpo.filter(pl.col("profile_status") == "DEFINED") if tpo.height else tpo
    undefined = tpo.filter(pl.col("profile_status") == "UNDEFINED") if tpo.height else tpo
    defined_bad = (
        defined.filter(pl.col("tpo_conservation_ok") != True).height if defined.height else 0
    )
    tight = defined.filter(pl.col("tight_gap") == True).height if defined.height else 0
    if defined.height:
        ratio_ok = defined.filter(
            (pl.col("gap_span") < 0.50 * pl.col("va_width")) == pl.col("tight_gap")
        ).height
        tight_mismatch = int(defined.height - ratio_ok)
        va_mass_ok = defined.filter(pl.col("va_mass") >= 0.70 - 1e-12).height
        va_mass_short = int(defined.height - va_mass_ok)
    else:
        tight_mismatch = 0
        va_mass_short = 0

    confirmed = (
        raids.filter(pl.col("confirmation_ts_ns").is_not_null()) if raids.height else raids
    )
    completed = raids.filter(pl.col("status") == "COMPLETED") if raids.height else raids
    ambiguous = (
        raids.filter(pl.col("status") == "AMBIGUOUS_INTRABAR") if raids.height else raids
    )
    primary = (
        raids.filter(pl.col("primary_attribution") == True) if raids.height else raids
    )

    # AMENDMENT-13: same-bar return is recorded and stays live until confirm/fail.
    n_same_bar_return = 0
    n_return = 0
    n_confirm_without_return = 0
    n_same_bar_closed_ambiguous = 0
    chrono_fail = 0
    grid_fail = 0
    method_mismatch = 0
    ref_mismatch = 0
    future_ts = 0
    holdout_ts = 0
    if raids.height:
        for row in raids.iter_rows(named=True):
            sweep = row["sweep_ts_ns"]
            first = row["first_excursion_ts_ns"]
            ret = row["return_ts_ns"]
            conf = row["confirmation_ts_ns"]
            end = row["endpoint_ts_ns"]
            status = row["status"]
            if ret is not None:
                n_return += 1
                if sweep is not None and int(ret) == int(sweep):
                    n_same_bar_return += 1
                    if status == "AMBIGUOUS_INTRABAR":
                        n_same_bar_closed_ambiguous += 1
            if conf is not None and ret is None:
                n_confirm_without_return += 1
            if first is not None and sweep is not None and first > sweep:
                chrono_fail += 1
            if ret is not None and sweep is not None and ret < sweep:
                chrono_fail += 1
            if conf is not None and sweep is not None and conf <= sweep:
                chrono_fail += 1
            if conf is not None and end is not None and end < conf:
                chrono_fail += 1
            if sweep is not None and end is not None and end < sweep:
                chrono_fail += 1
            if sweep is not None and (sweep % MINUTE_NS != 0):
                grid_fail += 1
            if row.get("confirmation_method") not in (None, cell_cfg["confirmation_method"]):
                if row["confirmation_method"] is not None:
                    method_mismatch += 1
            if row.get("confirmation_reference") not in (
                None,
                cell_cfg["confirmation_reference"],
            ):
                if row["confirmation_reference"] is not None:
                    ref_mismatch += 1
            for ts in (sweep, first, ret, conf, end, row.get("censor_ts_ns")):
                if ts is None:
                    continue
                dt = _ns_to_utc(int(ts))
                if dt >= HOLDOUT_START:
                    holdout_ts += 1
                if dt >= TRAIN_END:
                    future_ts += 1

    last_mark = int(marks["SourceCloseTime"].max()) if marks.height else 0
    last_mark_dt = _ns_to_utc(last_mark) if last_mark else None
    mark_mono = True
    if marks.height > 1:
        t = marks.sort("SourceCloseTime")["SourceCloseTime"]
        mark_mono = bool((t.diff().fill_null(1) > 0).all())
    mark_holdout = bool(last_mark_dt is not None and last_mark_dt >= HOLDOUT_START)
    mark_past_train = bool(last_mark_dt is not None and last_mark_dt >= TRAIN_END)

    # Destroy join on raid_id for confirmed rows.
    destroyed = pl.read_parquet(cell_dir / "raids_destroyed.parquet")
    destroy_count_mismatch = int(destroyed.height != raids.height)
    destroy_id_mismatch = 0
    destroy_status_mismatch = 0
    n_value_changed = 0
    n_swing_changed = 0
    mean_abs_d_swing = None
    raw_mean_swing = None
    raw_se_swing = None
    integrity_bite = None
    destroy_collapses = None
    if raids.height:
        raw_ids = raids["raid_id"]
        dest_ids = destroyed["raid_id"]
        destroy_id_mismatch = int(not raw_ids.equals(dest_ids))
        destroy_status_mismatch = int(not raids["status"].equals(destroyed["status"]))
        joined = raids.select(
            [
                "raid_id",
                "confirmation_ts_ns",
                "status",
                "swing_atr",
                "duration_ns",
                "strong_move",
            ]
        ).join(
            destroyed.select(
                [
                    "raid_id",
                    pl.col("swing_atr").alias("d_swing_atr"),
                    pl.col("duration_ns").alias("d_duration_ns"),
                    pl.col("strong_move").alias("d_strong_move"),
                ]
            ),
            on="raid_id",
            how="inner",
        )
        eligible = joined.filter(pl.col("confirmation_ts_ns").is_not_null())
        if eligible.height:
            changed = eligible.filter(
                (pl.col("swing_atr") != pl.col("d_swing_atr"))
                | (
                    pl.col("swing_atr").is_null()
                    != pl.col("d_swing_atr").is_null()
                )
                | (pl.col("duration_ns") != pl.col("d_duration_ns"))
                | (
                    pl.col("duration_ns").is_null()
                    != pl.col("d_duration_ns").is_null()
                )
                | (pl.col("strong_move") != pl.col("d_strong_move"))
                | (
                    pl.col("strong_move").is_null()
                    != pl.col("d_strong_move").is_null()
                )
            )
            n_value_changed = changed.height
            swing_changed = eligible.filter(
                (pl.col("swing_atr") != pl.col("d_swing_atr"))
                | (pl.col("swing_atr").is_null() != pl.col("d_swing_atr").is_null())
            )
            n_swing_changed = swing_changed.height
            finite = eligible.filter(
                pl.col("swing_atr").is_finite() & pl.col("d_swing_atr").is_finite()
            )
            if finite.height:
                delta = (finite["swing_atr"] - finite["d_swing_atr"]).abs()
                mean_abs_d_swing = float(delta.mean())
                raw_mean_swing = float(finite["swing_atr"].mean())
                if finite.height >= 2:
                    raw_se_swing = float(finite["swing_atr"].std() / (finite.height**0.5))
                    integrity_bite = INTEGRITY_Z * raw_se_swing
                    destroy_collapses = mean_abs_d_swing >= integrity_bite

    live_end = int(meta.get("n_fills") or 0) != 0
    cost_ok = meta.get("cost_model") == "NO_COST_CHARGED"
    active_raids = int(raids.filter(pl.col("active") == True).height) if raids.height else 0
    active_levels = (
        int(levels.filter(pl.col("active") == True).height) if levels.height else 0
    )

    return {
        **ident,
        "n_raids": int(raids.height),
        "n_levels": int(levels.height),
        "n_tpo": int(tpo.height),
        "n_bar_marks": int(marks.height),
        "n_fills": int(meta.get("n_fills") or 0),
        "n_orders": int(meta.get("n_orders") or 0),
        "cost_model": meta.get("cost_model"),
        "cost_ok": cost_ok,
        "has_fills": live_end,
        "n_confirmed": int(confirmed.height) if confirmed is not None else 0,
        "n_completed": int(completed.height) if completed is not None else 0,
        "n_ambiguous": int(ambiguous.height) if ambiguous is not None else 0,
        "n_primary_attr": int(primary.height) if primary is not None else 0,
        "n_failed": int(raid_status.get("FAILED_BREAKOUT", 0)),
        "n_non_primary": int(raid_status.get("CONFIRMED_NON_PRIMARY", 0)),
        "n_censor_exc": int(raid_status.get("RIGHT_CENSORED_EXCURSION", 0)),
        "n_censor_conf": int(raid_status.get("RIGHT_CENSORED_CONFIRMATION", 0)),
        "n_censor_end": int(raid_status.get("RIGHT_CENSORED_ENDPOINT", 0)),
        "n_return": n_return,
        "n_same_bar_return": n_same_bar_return,
        "n_confirm_without_return": n_confirm_without_return,
        "n_same_bar_closed_ambiguous": n_same_bar_closed_ambiguous,
        "same_bar_return_frac": (
            float(n_same_bar_return / raids.height) if raids.height else None
        ),
        "ambiguous_frac": (
            float(ambiguous.height / raids.height) if raids.height else None
        ),
        "raid_status_json": json.dumps(raid_status, sort_keys=True),
        "level_status_json": json.dumps(level_status, sort_keys=True),
        "unknown_raid_status": json.dumps(unknown_raid_status),
        "unknown_level_status": json.dumps(unknown_level_status),
        "retired_status_hits": int(
            sum(raid_status.get(status, 0) for status in RETIRED_STATUSES)
        ),
        "raid_dup": raid_dup,
        "level_dup": level_dup,
        "missing_profiles": missing_profiles,
        "extra_profiles": extra_profiles,
        "n_defined_tpo": int(defined.height) if defined is not None else 0,
        "n_undefined_tpo": int(undefined.height) if undefined is not None else 0,
        "defined_conservation_fail": defined_bad,
        "n_tight_defined": tight,
        "tight_rule_mismatch": tight_mismatch,
        "va_mass_short": va_mass_short,
        "chrono_fail": chrono_fail,
        "grid_fail": grid_fail,
        "method_mismatch": method_mismatch,
        "ref_mismatch": ref_mismatch,
        "raid_ts_past_train": future_ts,
        "raid_ts_holdout": holdout_ts,
        "last_mark_utc": last_mark_dt.isoformat() if last_mark_dt else None,
        "mark_monotonic": mark_mono,
        "mark_holdout": mark_holdout,
        "mark_past_train": mark_past_train,
        "active_raids": active_raids,
        "active_levels": active_levels,
        "destroy_non_vacuity": dc.get("non_vacuity"),
        "destroy_fixed_points": int(dc.get("fixed_points") or 0),
        "destroy_groups": int(dc.get("groups") or 0),
        "destroy_rows": int(dc.get("rows") or 0),
        "destroy_changed_meta": int(dc.get("changed_rows") or 0),
        "destroy_skipped_singleton": int(dc.get("skipped_singleton_groups") or 0),
        "destroy_contrast_meta": dc.get("contrast_ratio"),
        "destroy_seed": dc.get("seed"),
        "destroy_count_mismatch": destroy_count_mismatch,
        "destroy_id_mismatch": destroy_id_mismatch,
        "destroy_status_mismatch": destroy_status_mismatch,
        "destroy_n_value_changed": n_value_changed,
        "destroy_n_swing_changed": n_swing_changed,
        "mean_abs_d_swing": mean_abs_d_swing,
        "raw_mean_swing": raw_mean_swing,
        "raw_se_swing": raw_se_swing,
        "integrity_bite": integrity_bite,
        "destroy_collapses": destroy_collapses,
        "fence_status": fence.get("status"),
        "train_end_utc": fence.get("train_end_utc"),
        "holdout_start_utc": fence.get("holdout_start_utc"),
        "analysis_end_utc": fence.get("analysis_end_utc"),
        "manifest_sha256": fence.get("manifest_sha256"),
        "run_start": meta["run_config"]["start_time"],
        "run_end": meta["run_config"]["end_time"],
        "catalog_path": meta.get("catalog_path"),
        "nautilus_version": meta.get("nautilus_version"),
        "tpo_tight_ratio": cell_cfg.get("tpo_tight_ratio"),
        "tpo_gap_mass": cell_cfg.get("tpo_gap_mass"),
    }


def scan_trading_clock() -> dict[str, Any]:
    """AMENDMENT-10: 1D/1W anchors must be NY trading sessions, not weekend stubs."""
    rows: list[dict[str, Any]] = []
    sunday_date_anchors = 0
    saturday_date_anchors = 0
    for cell_dir in sorted(EMISSION_ROOT.iterdir()):
        if not cell_dir.is_dir():
            continue
        ident = _parse_cell(cell_dir.name)
        if ident["level_config"] not in {"PREVIOUS_1D", "PREVIOUS_1W"}:
            continue
        levels = pl.read_parquet(
            cell_dir / "levels.parquet",
            columns=["anchor_key", "side", "creation_ts_ns", "status"],
        )
        weekend_anchors = 0
        create_sunday = 0
        create_saturday = 0
        create_friday_cut = 0
        anchors = levels["anchor_key"].unique().to_list()
        if ident["level_config"] == "PREVIOUS_1D":
            for anchor in anchors:
                day = datetime.fromisoformat(str(anchor)).date()
                if day.weekday() == 5:
                    saturday_date_anchors += 1
                    weekend_anchors += 1
                elif day.weekday() == 6:
                    sunday_date_anchors += 1
                    weekend_anchors += 1
        for ts in levels["creation_ts_ns"].to_list():
            local = _ns_to_utc(int(ts)).astimezone(NY)
            if local.weekday() == 6:
                create_sunday += 1
            elif local.weekday() == 5:
                create_saturday += 1
            elif local.weekday() == 4 and local.hour >= 17:
                create_friday_cut += 1
        rows.append(
            {
                **ident,
                "n_levels": levels.height,
                "n_anchors": len(anchors),
                "n_high": levels.filter(pl.col("side") == "HIGH").height,
                "n_low": levels.filter(pl.col("side") == "LOW").height,
                "weekend_anchors": weekend_anchors,
                "create_sunday": create_sunday,
                "create_saturday": create_saturday,
                "create_friday_cut": create_friday_cut,
                "first_anchor": min(str(a) for a in anchors) if anchors else None,
                "last_anchor": max(str(a) for a in anchors) if anchors else None,
            }
        )
    frame = pl.DataFrame(rows)
    return {
        "n_1d_1w_cells": frame.height,
        "weekend_date_anchors_1d_sunday": sunday_date_anchors,
        "weekend_date_anchors_1d_saturday": saturday_date_anchors,
        "min_1d_anchors": int(
            frame.filter(pl.col("level_config") == "PREVIOUS_1D")["n_anchors"].min()
        ),
        "max_1d_anchors": int(
            frame.filter(pl.col("level_config") == "PREVIOUS_1D")["n_anchors"].max()
        ),
        "min_1w_anchors": int(
            frame.filter(pl.col("level_config") == "PREVIOUS_1W")["n_anchors"].min()
        ),
        "max_1w_anchors": int(
            frame.filter(pl.col("level_config") == "PREVIOUS_1W")["n_anchors"].max()
        ),
        "zero_level_cells": int(frame.filter(pl.col("n_levels") == 0).height),
        "rows": frame.to_dicts(),
    }


def scan_method_overlap() -> dict[str, Any]:
    """BREAKOUT_BAR vs LEVEL_CLOSE: same previous-reference test (disclosed)."""
    pairs: list[dict[str, Any]] = []
    cells = {p.name: p for p in EMISSION_ROOT.iterdir() if p.is_dir()}
    seen: set[tuple[str, str, str, str]] = set()
    for name, path in cells.items():
        ident = _parse_cell(name)
        key = (ident["symbol"], ident["timeframe"], ident["confirm_ref"], ident["level_config"])
        if key in seen:
            continue
        seen.add(key)
        bb = (
            f"ctrader-{ident['symbol'].lower()}-{ident['timeframe']}"
            f"-breakout_bar-{ident['confirm_ref']}-{ident['level_config'].lower()}"
        )
        lc = (
            f"ctrader-{ident['symbol'].lower()}-{ident['timeframe']}"
            f"-level_close-{ident['confirm_ref']}-{ident['level_config'].lower()}"
        )
        if bb not in cells or lc not in cells:
            pairs.append({"key": list(key), "missing_pair": True})
            continue
        a = pl.read_parquet(cells[bb] / "raids.parquet", columns=["raid_id", "status"])
        b = pl.read_parquet(cells[lc] / "raids.parquet", columns=["raid_id", "status"])
        id_equal = set(a["raid_id"].to_list()) == set(b["raid_id"].to_list())
        status_equal = False
        if id_equal and a.height == b.height:
            status_equal = a.sort("raid_id")["status"].equals(b.sort("raid_id")["status"])
        pairs.append(
            {
                "symbol": ident["symbol"],
                "timeframe": ident["timeframe"],
                "confirm_ref": ident["confirm_ref"],
                "level_config": ident["level_config"],
                "n_bb": a.height,
                "n_lc": b.height,
                "raid_id_equal": id_equal,
                "status_equal": status_equal,
            }
        )
    frame = pl.DataFrame(pairs)
    return {
        "n_pairs": frame.height,
        "n_id_equal": int(frame.filter(pl.col("raid_id_equal") == True).height)
        if "raid_id_equal" in frame.columns
        else 0,
        "n_status_equal": int(frame.filter(pl.col("status_equal") == True).height)
        if "status_equal" in frame.columns
        else 0,
        "n_count_diff": int(frame.filter(pl.col("n_bb") != pl.col("n_lc")).height)
        if "n_bb" in frame.columns
        else 0,
        "rows": frame.to_dicts(),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cells = sorted(p for p in EMISSION_ROOT.iterdir() if p.is_dir())
    if len(cells) != 264:
        raise SystemExit(f"expected 264 published cells, found {len(cells)}")

    family = json.loads(FAMILY_GATE.read_text(encoding="utf-8"))
    gates = list(GATE_ROOT.glob("*.json"))
    gate_pass = 0
    for path in gates:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("blocking_pass"):
            gate_pass += 1

    rows = [_scan_one(cell) for cell in cells]
    frame = pl.DataFrame(rows)
    frame.write_parquet(OUT_DIR / "cell_census.parquet")
    frame.write_csv(OUT_DIR / "cell_census.csv")

    clock = scan_trading_clock()
    (OUT_DIR / "trading_clock.json").write_text(
        json.dumps(
            {k: v for k, v in clock.items() if k != "rows"},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    pl.DataFrame(clock["rows"]).write_parquet(OUT_DIR / "trading_clock.parquet")

    overlap = scan_method_overlap()
    (OUT_DIR / "method_overlap.json").write_text(
        json.dumps({k: v for k, v in overlap.items() if k != "rows"}, indent=2) + "\n",
        encoding="utf-8",
    )
    pl.DataFrame(overlap["rows"]).write_parquet(OUT_DIR / "method_overlap.parquet")

    integrity_fail_cols = [
        "raid_dup",
        "level_dup",
        "missing_profiles",
        "extra_profiles",
        "defined_conservation_fail",
        "tight_rule_mismatch",
        "chrono_fail",
        "grid_fail",
        "method_mismatch",
        "ref_mismatch",
        "raid_ts_holdout",
        "mark_holdout",
        "active_raids",
        "active_levels",
        "destroy_fixed_points",
        "destroy_count_mismatch",
        "destroy_id_mismatch",
        "destroy_status_mismatch",
        "n_fills",
        "n_ambiguous",
        "n_confirm_without_return",
        "n_same_bar_closed_ambiguous",
        "retired_status_hits",
    ]
    fail_counts = {col: int(frame[col].sum()) for col in integrity_fail_cols}
    vacuous = frame.filter(pl.col("destroy_non_vacuity") == "VACUOUS_SINGLETON")
    changed = frame.filter(pl.col("destroy_non_vacuity") == "CHANGED")
    collapse = changed.filter(pl.col("destroy_collapses") == False)

    observed_configs = set(frame["level_config"].unique().to_list())
    grid_check: dict[str, Any] = {}
    for tf, expected in EXPECTED_GRID.items():
        sub = frame.filter(pl.col("timeframe") == tf)
        refs = set(sub["confirm_ref"].unique().to_list()) if sub.height else set()
        grid_check[tf] = {
            "n_cells": sub.height,
            "expected_n_cells": expected["n_cells"],
            "confirm_refs": sorted(refs),
            "expected_confirm_refs": sorted(expected["confirm_refs"]),
            "ok": sub.height == expected["n_cells"] and refs == expected["confirm_refs"],
        }

    summary = {
        "n_cells": frame.height,
        "family_blocking_pass": family.get("blocking_pass"),
        "family_n_cells": family.get("n_cells"),
        "per_cell_gates": len(gates),
        "per_cell_gate_pass": gate_pass,
        "symbols": sorted(frame["symbol"].unique().to_list()),
        "timeframes": sorted(frame["timeframe"].unique().to_list()),
        "methods": sorted(frame["method"].unique().to_list()),
        "confirm_refs": sorted(frame["confirm_ref"].unique().to_list()),
        "level_configs": sorted(frame["level_config"].unique().to_list()),
        "level_configs_expected": sorted(EXPECTED_LEVEL_CONFIGS),
        "level_configs_ok": observed_configs == EXPECTED_LEVEL_CONFIGS,
        "grid_check": grid_check,
        "n_zero_raid_cells": int(frame.filter(pl.col("n_raids") == 0).height),
        "n_zero_level_cells": int(frame.filter(pl.col("n_levels") == 0).height),
        "n_zero_1d_cells": int(
            frame.filter(
                (pl.col("level_config") == "PREVIOUS_1D") & (pl.col("n_levels") == 0)
            ).height
        ),
        "n_zero_1w_cells": int(
            frame.filter(
                (pl.col("level_config") == "PREVIOUS_1W") & (pl.col("n_levels") == 0)
            ).height
        ),
        "total_raids": int(frame["n_raids"].sum()),
        "total_levels": int(frame["n_levels"].sum()),
        "total_confirmed": int(frame["n_confirmed"].sum()),
        "total_completed": int(frame["n_completed"].sum()),
        "total_ambiguous": int(frame["n_ambiguous"].sum()),
        "total_return": int(frame["n_return"].sum()),
        "total_same_bar_return": int(frame["n_same_bar_return"].sum()),
        "total_confirm_without_return": int(frame["n_confirm_without_return"].sum()),
        "total_same_bar_closed_ambiguous": int(
            frame["n_same_bar_closed_ambiguous"].sum()
        ),
        "min_same_bar_return_frac": float(frame["same_bar_return_frac"].min()),
        "max_same_bar_return_frac": float(frame["same_bar_return_frac"].max()),
        "median_same_bar_return_frac": float(frame["same_bar_return_frac"].median()),
        "min_ambiguous_frac": float(frame["ambiguous_frac"].min()),
        "max_ambiguous_frac": float(frame["ambiguous_frac"].max()),
        "median_ambiguous_frac": float(frame["ambiguous_frac"].median()),
        "cost_ok_cells": int(frame.filter(pl.col("cost_ok") == True).height),
        "destroy_vacuous_cells": vacuous["cell_id"].to_list(),
        "destroy_changed_cells": int(changed.height),
        "destroy_collapse_false_cells": collapse["cell_id"].to_list(),
        "integrity_fail_sums": fail_counts,
        "mark_past_train_cells": int(frame.filter(pl.col("mark_past_train") == True).height),
        "raid_ts_past_train_sum": int(frame["raid_ts_past_train"].sum()),
        "clock_weekend_sunday_anchors": clock["weekend_date_anchors_1d_sunday"],
        "clock_weekend_saturday_anchors": clock["weekend_date_anchors_1d_saturday"],
        "clock_zero_level_cells": clock["zero_level_cells"],
        "method_pairs": overlap["n_pairs"],
        "method_id_equal": overlap["n_id_equal"],
        "method_status_equal": overlap["n_status_equal"],
        "method_count_diff": overlap["n_count_diff"],
        "nautilus_versions": sorted(set(frame["nautilus_version"].to_list())),
        "tight_ratio_values": sorted(set(frame["tpo_tight_ratio"].to_list())),
        "gap_mass_values": sorted(set(frame["tpo_gap_mass"].to_list())),
    }
    (OUT_DIR / "scan_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
