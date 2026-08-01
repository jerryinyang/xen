"""SPDR-022 analyst pass 1: row-key audit, populations, states, controls.

Independent of the canonical analyse.py. Streams with pl.scan_parquet and collects
only aggregates. One universe per invocation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

OUT = Path("python/experiments/SPDR-022/results/analyst")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--universe", required=True)
    a = ap.parse_args()
    run = Path(a.run)
    u = a.universe
    OUT.mkdir(parents=True, exist_ok=True)

    origins = pl.scan_parquet(run / "origins.parquet")
    feats = pl.scan_parquet(run / "features.parquet")
    nat = pl.scan_parquet(run / "native_parameter_schedule.parquet")
    pol = pl.scan_parquet(run / "policy_schedule.parquet")
    led = pl.scan_parquet(run / "episode_results.parquet")

    rep: dict = {"universe": u}

    n_origin = origins.select(pl.len()).collect().item()
    n_feat = feats.select(pl.len()).collect().item()
    n_sym = origins.select(pl.col("symbol").n_unique()).collect().item()
    rep["origins"] = n_origin
    rep["features"] = n_feat
    rep["symbols"] = n_sym
    rep["feature_minus_origin"] = n_feat - n_origin
    rep["origin_id_unique"] = origins.select(pl.col("origin_id").n_unique()).collect().item()
    rep["component_ready_false"] = (
        origins.filter(~pl.col("component_ready")).select(pl.len()).collect().item()
    )

    # feature rows carrying no origin
    extra = (
        feats.select("symbol", "ts")
        .join(origins.select("symbol", pl.col("decision_ts").alias("ts")), on=["symbol", "ts"], how="anti")
        .collect()
    )
    rep["feature_rows_without_origin"] = extra.height
    rep["feature_rows_without_origin_ts"] = sorted({str(t) for t in extra["ts"]})
    rep["origin_rows_without_feature"] = (
        origins.select("symbol", pl.col("decision_ts").alias("ts"))
        .join(feats.select("symbol", "ts"), on=["symbol", "ts"], how="anti")
        .select(pl.len())
        .collect()
        .item()
    )

    # ---- row-key audit -------------------------------------------------
    for label, sched in (("native", nat), ("management", pol)):
        rows = sched.select(pl.len()).collect().item()
        arms = sched.select(pl.col("arm_id").n_unique()).collect().item()
        variants = sched.select(pl.col("entry_variant").n_unique()).collect().item()
        keyed = sched.select("origin_id", "entry_variant", "arm_id").unique().select(pl.len()).collect().item()
        orig_cov = sched.select(pl.col("origin_id").n_unique()).collect().item()
        # arms per variant
        apv = sched.select("entry_variant", "arm_id").unique().group_by("entry_variant").len().collect()
        rep[f"{label}_rows"] = rows
        rep[f"{label}_arms"] = arms
        rep[f"{label}_arms_per_variant"] = apv.to_dicts()
        rep[f"{label}_distinct_keys"] = keyed
        rep[f"{label}_duplicate_keys"] = rows - keyed
        rep[f"{label}_origins_covered"] = orig_cov
        rep[f"{label}_origins_missing"] = n_origin - orig_cov
        expect = sum(d["len"] for d in apv.to_dicts()) * n_origin
        rep[f"{label}_expected_rows_arms_x_origins"] = expect
        rep[f"{label}_row_key_audit_pass"] = bool(rows == keyed == expect and orig_cov == n_origin)

    # ---- states --------------------------------------------------------
    for label, sched in (("native", nat), ("management", pol)):
        t = sched.group_by("entry_variant", "state").len().sort("entry_variant", "len", descending=[False, True]).collect()
        t.write_parquet(OUT / f"{u}_{label}_states_by_variant.parquet")
        rep[f"{label}_states_by_variant"] = t.to_dicts()
        t2 = sched.group_by("arm_class").agg(pl.len(), pl.col("arm_id").n_unique().alias("arms")).collect()
        rep[f"{label}_arm_class"] = t2.to_dicts()

    ledger_states = led.group_by("arm_class", "state").len().sort("arm_class", "len", descending=[False, True]).collect()
    ledger_states.write_parquet(OUT / f"{u}_ledger_states_by_armclass.parquet")
    rep["ledger_rows"] = led.select(pl.len()).collect().item()
    rep["ledger_states"] = led.group_by("state").len().sort("len", descending=True).collect().to_dicts()

    # ---- controls artifacts -------------------------------------------
    rep["run_controls_json"] = json.loads((run / "controls.json").read_text())
    for k in ("source_artifact_hashes",):
        rep["run_controls_json"].pop(k, None)
    sc = json.loads((run / "integrity_selfcheck.json").read_text())
    rep["integrity_hard_checks"] = sc["hard_checks"]
    rep["integrity_blocking_pass"] = sc["blocking_pass"]
    rep["run_summary_hard_integrity_field"] = json.loads((run / "run_summary.json").read_text()).get("hard_integrity")
    rep["run_environment"] = json.loads((run / "run_environment.json").read_text())
    ra = json.loads((run / "row_accounting.json").read_text())
    h = ra["source_artifact_hashes"]
    rep["sha_episodes"] = h["episodes.parquet"]
    rep["sha_native_parameter_schedule"] = h["native_parameter_schedule.parquet"]
    rep["episodes_equals_native_schedule_sha"] = h["episodes.parquet"] == h["native_parameter_schedule.parquet"]

    (OUT / f"{u}_populations.json").write_text(json.dumps(rep, indent=2, default=str))
    print(json.dumps({k: v for k, v in rep.items() if not isinstance(v, list)}, indent=2, default=str))


if __name__ == "__main__":
    main()
