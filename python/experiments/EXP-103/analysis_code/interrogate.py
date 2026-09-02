"""EXP-103 independent interrogation (no analysis.py import).

Recomputes observed means/counts from one raw cell as a cross-check.
Builds per-stratum tight vs non-tight tables from the registered live
analysis_results.json. Does not rerun 10k bootstrap or 2,000 destroys.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[4]
EMISSION = ROOT / "data" / "nautilus_runs" / "EXP-100" / "full"
EXP = ROOT / "python" / "experiments" / "EXP-103"
LIVE_PATH = EXP / "results" / "analysis_results.json"
GATE_PATH = EXP / "results" / "estimand_validation.json"
FIX_PATH = EXP / "results" / "fixture_integrity.json"
OUT = Path(__file__).resolve().parent / "interrogation_summary.json"

CELL = EMISSION / "ctrader-eurusd-15m-breakout_bar-1h-previous_1d"
CELL_LC = EMISSION / "ctrader-eurusd-15m-level_close-1h-previous_1d"
STRATUM = (
    "archive_symbol",
    "timeframe",
    "confirmation_method",
    "confirmation_reference",
    "side",
    "config",
)
INTEGRITY_Z = 2.8
NS_PER_HOUR = 3_600_000_000_000
TRAIN_START_NS = int(datetime(2021, 6, 2, 0, 1, tzinfo=timezone.utc).timestamp() * 1e9)
TRAIN_END_NS = int(datetime(2023, 11, 22, 0, 0, tzinfo=timezone.utc).timestamp() * 1e9)


def sha16(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()[:16]


def close(a, b, atol=1e-9, rtol=1e-9) -> bool:
    if a is None or b is None:
        return a == b
    return bool(np.isclose(float(a), float(b), atol=atol, rtol=rtol, equal_nan=True))


def golden_replay(counts, start_bin=100, bin_width=1.0):
    total = sum(counts)
    poc_offset = max(range(len(counts)), key=lambda i: (counts[i], -i))
    selected = {poc_offset}
    selected_count = counts[poc_offset]
    target = math.ceil(0.70 * total)
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
        selected_count += counts[chosen]
    gap_target = math.ceil(0.30 * selected_count)
    gap, gap_count = [], 0
    for index in sorted(selected, key=lambda i: (counts[i], i)):
        gap.append(index)
        gap_count += counts[index]
        if gap_count >= gap_target:
            break
    va_width = float((high - low + 1) * bin_width)
    gap_span = float((max(gap) - min(gap) + 1) * bin_width)
    return {
        "poc": start_bin + poc_offset,
        "va_count": selected_count,
        "val": float(start_bin + low),
        "vah": float(start_bin + high + 1),
        "va_width": va_width,
        "gap_span": gap_span,
        "gap_span_va": gap_span / va_width,
        "tight_gap": gap_span < 0.50 * va_width,
        "gap_bins": [start_bin + i for i in gap],
        "gap_mass": gap_count,
    }


def ci_bucket(interval):
    if not interval or interval[0] is None or interval[1] is None:
        return "no_interval"
    lo, hi = interval
    if lo > 0:
        return "above0"
    if hi < 0:
        return "below0"
    return "overlap0"


def outcome_join(cell: Path) -> pl.DataFrame:
    raids = pl.read_parquet(
        cell / "raids.parquet",
        columns=[
            "raid_id",
            "profile_generation",
            "status",
            "primary_attribution",
            "primary_completed",
            "side",
            "swing_atr",
            "swing_bps",
            "swing_price",
            "swing_duration_ns",
            "duration_ns",
            "strong_move",
            "confirmation_ts_ns",
            "endpoint_ts_ns",
            "censor_ts_ns",
            "first_excursion_ts_ns",
            "profile_undefined_reason",
        ],
    )
    prof = pl.read_parquet(
        cell / "tpo_profiles.parquet",
        columns=[
            "raid_id",
            "profile_generation",
            "profile_status",
            "tight_gap",
            "undefined_reason",
            "tpo_conservation_ok",
            "bin_width",
            "atr_unit",
            "va_width",
            "vah",
            "val",
            "gap_span",
            "va_count",
            "tpo_total",
            "profile_end_ts_ns",
        ],
    )
    return raids.join(prof, on=["raid_id", "profile_generation"], how="left")


def main() -> int:
    live = json.loads(LIVE_PATH.read_text())
    gate = json.loads(GATE_PATH.read_text())
    fixture = json.loads(FIX_PATH.read_text())
    rows = live["value_rows"]
    recs = live["extra"]["control"]["records"]

    joined = outcome_join(CELL)
    unmatched = joined.filter(pl.col("profile_status").is_null()).height
    outcome = joined.filter(
        (pl.col("status") == "COMPLETED")
        & (pl.col("primary_attribution") == True)
        & (pl.col("primary_completed") == True)
        & (pl.col("profile_status") == "DEFINED")
    )
    defined = joined.filter(pl.col("profile_status") == "DEFINED")
    live_index = {}
    for r in rows:
        s = r["stratum"]
        live_index[tuple(s.get(k) for k in STRATUM) + (r["channel"],)] = r

    cell_match = []
    for side in ("LOW", "HIGH"):
        sub = outcome.filter(pl.col("side") == side)
        tight = sub.filter(pl.col("tight_gap") == True)
        nontight = sub.filter(pl.col("tight_gap") == False)
        for field in ("swing_atr", "swing_duration_ns", "strong_move", "swing_bps", "swing_price"):
            if field == "strong_move":
                tv = tight[field].drop_nulls().cast(pl.Float64)
                nv = nontight[field].drop_nulls().cast(pl.Float64)
            else:
                tv = tight[field].drop_nulls()
                nv = nontight[field].drop_nulls()
            tmean = float(tv.mean()) if tv.len() else None
            nmean = float(nv.mean()) if nv.len() else None
            est = (tmean - nmean) if tmean is not None and nmean is not None else None
            key = ("EURUSD", "15m", "BREAKOUT_BAR", "1H", side, "PREVIOUS_1D", field)
            obs = live_index[key]["observed"]
            cell_match.append({
                "side": side,
                "channel": field,
                "raw_arm_n": tv.len(),
                "raw_comp_n": nv.len(),
                "raw_estimate": est,
                "live_arm_n": obs.get("arm_n"),
                "live_comp_n": obs.get("comparator_n"),
                "live_estimate": obs.get("estimate"),
                "match": (
                    tv.len() == obs.get("arm_n")
                    and nv.len() == obs.get("comparator_n")
                    and close(est, obs.get("estimate"))
                    and close(tmean, obs.get("arm_mean"))
                    and close(nmean, obs.get("comparator_mean"))
                ),
            })

    lc = outcome_join(CELL_LC)
    lc_out = lc.filter(
        (pl.col("status") == "COMPLETED")
        & (pl.col("primary_attribution") == True)
        & (pl.col("primary_completed") == True)
        & (pl.col("profile_status") == "DEFINED")
    )

    signs = {}
    for ch in ("swing_atr", "swing_duration_ns", "strong_move", "swing_bps", "swing_price"):
        c = Counter()
        n_arm = n_comp = 0
        for r in rows:
            if r["channel"] != ch:
                continue
            o = r["observed"]
            if o.get("reason"):
                c["empty"] += 1
                continue
            est = o.get("estimate")
            if est is None or est != est:
                c["nan"] += 1
            else:
                c["pos" if est > 0 else ("zero" if est == 0 else "neg")] += 1
            c[ci_bucket(o.get("interval"))] += 1
            n_arm += o.get("arm_n") or 0
            n_comp += o.get("comparator_n") or 0
        signs[ch] = {"counts": dict(c), "sum_arm_n": n_arm, "sum_comp_n": n_comp}

    layers = {}
    for layer in STRATUM:
        layers[layer] = {}
        for ch in ("swing_atr", "swing_duration_ns", "strong_move"):
            by = defaultdict(Counter)
            for r in rows:
                if r["channel"] != ch or r["observed"].get("reason"):
                    continue
                val = str(r["stratum"].get(layer))
                est = r["observed"].get("estimate")
                if est is None or est != est:
                    continue
                by[val]["n"] += 1
                by[val]["pos" if est > 0 else "neg"] += 1
                by[val][ci_bucket(r["observed"].get("interval"))] += 1
                by[val]["arm_n"] += r["observed"].get("arm_n") or 0
                by[val]["comp_n"] += r["observed"].get("comparator_n") or 0
            layers[layer][ch] = {k: dict(v) for k, v in sorted(by.items())}

    # BB vs LC pairwise identity
    pair_eq = Counter()
    for ch in ("swing_atr", "swing_duration_ns", "strong_move"):
        pair = defaultdict(dict)
        for r in rows:
            if r["channel"] != ch or r["observed"].get("reason"):
                continue
            s = r["stratum"]
            key = tuple(s[k] for k in STRATUM if k != "confirmation_method")
            pair[key][s["confirmation_method"]] = (
                r["observed"]["estimate"],
                r["observed"]["arm_n"],
                r["observed"]["comparator_n"],
            )
        n_eq = sum(
            1
            for v in pair.values()
            if v.get("BREAKOUT_BAR") == v.get("LEVEL_CLOSE")
            and "BREAKOUT_BAR" in v
            and "LEVEL_CLOSE" in v
        )
        pair_eq[ch] = {"pairs": len(pair), "equal": n_eq}

    a15_ok = a15_fail = flag_mm = 0
    biters = []
    n_singleton = 0
    n_groups = 0
    for r in recs:
        for g in r.get("group_sizes") or []:
            n_groups += 1
            if g < 2:
                n_singleton += 1
        raw, se, md = r.get("raw_estimate"), r.get("raw_bootstrap_se"), r.get("destroyed_mean")
        if raw is None or se is None or raw != raw or se != se:
            continue
        bites = abs(raw) > INTEGRITY_Z * se
        if bites != bool(r.get("raw_bite")):
            flag_mm += 1
        if r.get("raw_bite"):
            biters.append(abs(r["collapse_ratio"]) if r.get("collapse_ratio") == r.get("collapse_ratio") else None)
            if md is not None and abs(md) <= INTEGRITY_Z * se:
                a15_ok += 1
            else:
                a15_fail += 1

    t1 = golden_replay([29, 12, 23, 23, 27, 26])
    t2 = golden_replay([10, 18, 13, 7, 7, 30])

    tw = cw = tn = cn = 0.0
    for r in rows:
        if r["channel"] != "swing_atr" or r["observed"].get("reason"):
            continue
        o = r["observed"]
        tw += o["arm_mean"] * o["arm_n"]
        tn += o["arm_n"]
        cw += o["comparator_mean"] * o["comparator_n"]
        cn += o["comparator_n"]

    summary = {
        "experiment": "EXP-103",
        "method": "registered live JSON per-stratum tables + one-cell raw recompute; no bootstrap/destroy rerun",
        "gate": {
            "blocking_pass": gate["blocking_pass"],
            "n_cells": gate["n_cells"],
            "cell_fail": sum(1 for c in gate["cells"] if not c["blocking_pass"]),
            "cost_fail": sum(1 for c in gate["cells"] if not c["no_cost_charged"]["ok"]),
            "sha16": sha16(GATE_PATH),
            "sha16_exp100": sha16(ROOT / "python" / "experiments" / "EXP-100" / "results" / "estimand_validation.json"),
        },
        "live_integrity": live["integrity"]["blocking_pass"],
        "live_reasons": live["integrity"]["reasons"],
        "code_dir_exists": (EXP / "code").exists(),
        "one_cell": {
            "path": str(CELL.relative_to(ROOT)),
            "raid_rows": joined.height,
            "unmatched_profiles": unmatched,
            "outcome_n": outcome.height,
            "defined": defined.height,
            "conservation_fail": defined.filter(pl.col("tpo_conservation_ok") != True).height,
            "tight_boundary_fail": defined.filter(
                pl.col("tight_gap") != (pl.col("gap_span") < 0.50 * pl.col("va_width"))
            ).height,
            "duration_mismatch": joined.filter(
                pl.col("swing_duration_ns").is_not_null()
                & pl.col("duration_ns").is_not_null()
                & (pl.col("swing_duration_ns") != pl.col("duration_ns"))
            ).height,
            "profile_end_eq_confirm": outcome.filter(
                pl.col("profile_end_ts_ns") == pl.col("confirmation_ts_ns")
            ).height,
            "holdout_after_train": sum(
                joined.filter(pl.col(c).is_not_null() & (pl.col(c) > TRAIN_END_NS)).height
                for c in ("confirmation_ts_ns", "endpoint_ts_ns", "censor_ts_ns", "first_excursion_ts_ns")
            ),
            "raw_vs_live_matches": sum(1 for x in cell_match if x["match"]),
            "raw_vs_live_rows": len(cell_match),
            "cell_match": cell_match,
            "meta": json.loads((CELL / "run_metadata.json").read_text())["cost_model"],
            "n_fills": json.loads((CELL / "run_metadata.json").read_text())["n_fills"],
            "lc_outcome_n": lc_out.height,
            "lc_raids_sha16": sha16(CELL_LC / "raids.parquet"),
            "bb_raids_sha16": sha16(CELL / "raids.parquet"),
            "lc_profiles_sha16": sha16(CELL_LC / "tpo_profiles.parquet"),
            "bb_profiles_sha16": sha16(CELL / "tpo_profiles.parquet"),
        },
        "signs": signs,
        "layers": layers,
        "bb_lc_identical_estimates": dict(pair_eq),
        "control_registered_not_recomputed": {
            "n_records": len(recs),
            "raw_bite": dict(Counter(r.get("raw_bite") for r in recs)),
            "destroyed_survives": dict(Counter(r.get("destroyed_survives") for r in recs)),
            "fixed_points": sorted({r.get("fixed_points") for r in recs}),
            "singleton_groups": n_singleton,
            "n_groups": n_groups,
            "min_group": min((g for r in recs for g in (r.get("group_sizes") or [])), default=None),
            "a15_destroyed_inside_raw_bite_band": a15_ok,
            "a15_fail": a15_fail,
            "a15_flag_vs_median_se_mismatch": flag_mm,
            "biter_abs_collapse_median": float(np.median([x for x in biters if x is not None])),
            "biter_abs_collapse_max": max(x for x in biters if x is not None),
            "void_reasons_any": sum(1 for r in recs if r.get("reasons")),
        },
        "golden": {"T1": t1, "T2": t2, "T3_tight": (2.0 < 0.50 * 4.0)},
        "fixture_blocking_pass": fixture["integrity"]["blocking_pass"],
        "census_live": live["extra"]["census"]["status"],
        "profile_census_live": live["extra"]["profile_census"],
        "all_defined_live": live["extra"]["all_defined_baseline"],
        "disclosure_weighted_swing_atr": {
            "tight": tw / tn,
            "nontight": cw / cn,
            "contrast": tw / tn - cw / cn,
            "n_tight": tn,
            "n_nontight": cn,
        },
        "zero_cost": live["zero_cost_disclosure"]["cost_model"],
        "n_value_rows": len(rows),
    }
    OUT.write_text(json.dumps(summary, indent=2, default=str))
    print("wrote", OUT)
    print("one-cell matches", summary["one_cell"]["raw_vs_live_matches"], "/", summary["one_cell"]["raw_vs_live_rows"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
