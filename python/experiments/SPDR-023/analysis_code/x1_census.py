"""SPDR-023 fresh-context analyst — X1: raw-emission census, row-key audit, rates.

Independent of analyse.py. Streaming only: never collects a large frame.
Emits to results/analyst/<universe>/.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import polars as pl

ROOT = Path("/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen")
RUNS = {
    "ctrader": ROOT / "data/nautilus_runs/SPDR-023-ctrader-train-20260731T004708Z",
    "crypto": ROOT / "data/nautilus_runs/SPDR-023-crypto-train-20260731T004708Z",
}
OUT = ROOT / "python/experiments/SPDR-023/results/analyst"


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def run(universe: str) -> None:
    R = RUNS[universe]
    o = OUT / universe
    o.mkdir(parents=True, exist_ok=True)
    nps = pl.scan_parquet(R / "native_parameter_schedule.parquet")
    pol = pl.scan_parquet(R / "policy_schedule.parquet")
    org = pl.scan_parquet(R / "origins.parquet")
    fea = pl.scan_parquet(R / "features.parquet")

    n_org = org.select(pl.len()).collect().item()
    n_fea = fea.select(pl.len()).collect().item()
    n_nps = nps.select(pl.len()).collect().item()
    n_pol = pol.select(pl.len()).collect().item()
    n_arm = nps.select(pl.col("native_arm_id").n_unique()).collect().item()
    n_parm = pol.select(pl.col("arm_id").n_unique()).collect().item()
    n_key = nps.select(pl.struct("origin_id", "native_arm_id").n_unique()).collect().item()
    n_pkey = (
        pol.select(pl.struct("origin_id", "arm_id", "entry_variant").n_unique()).collect().item()
    )
    n_org_nps = nps.select(pl.col("origin_id").n_unique()).collect().item()

    audit = {
        "universe": universe,
        "origins_rows": n_org,
        "features_rows": n_fea,
        "features_minus_origins": n_fea - n_org,
        "native_schedule_rows": n_nps,
        "native_arms": n_arm,
        "origins_x_arms": n_org * n_arm,
        "native_rows_equal_product": n_nps == n_org * n_arm,
        "native_distinct_(origin,arm)_keys": n_key,
        "native_key_unique": n_key == n_nps,
        "native_distinct_origins": n_org_nps,
        "native_covers_all_origins": n_org_nps == n_org,
        "policy_schedule_rows": n_pol,
        "policy_arms": n_parm,
        "policy_origins_x_arms_x_variants": n_org * n_parm * 2,
        "policy_rows_equal_product": n_pol == n_org * n_parm * 2,
        "policy_distinct_(origin,arm)_keys": n_pkey,
        "policy_key_unique": n_pkey == n_pol,
        "episodes_sha256": sha(R / "episodes.parquet"),
        "native_parameter_schedule_sha256": sha(R / "native_parameter_schedule.parquet"),
    }
    audit["episodes_identical_to_native_schedule"] = (
        audit["episodes_sha256"] == audit["native_parameter_schedule_sha256"]
    )
    (o / "row_key_audit.json").write_text(json.dumps(audit, indent=2))
    print(json.dumps(audit, indent=2))

    # -- full state census, every observed state, by variant x arm_class x symbol
    census = (
        nps.group_by("symbol", "entry_variant", "arm_class", "state")
        .agg(pl.len().alias("rows"), pl.col("origin_id").n_unique().alias("origins"))
        .sort("symbol", "entry_variant", "arm_class", "state")
        .collect()
    )
    census.write_parquet(o / "state_census_native.parquet")
    census.write_csv(o / "state_census_native.csv")

    pcensus = (
        pol.group_by("symbol", "entry_variant", "state", "eligibility_status", "eligible")
        .agg(pl.len().alias("rows"))
        .sort("symbol", "entry_variant", "state", "eligibility_status")
        .collect()
    )
    pcensus.write_parquet(o / "state_census_policy.parquet")
    pcensus.write_csv(o / "state_census_policy.csv")

    # -- variant-level state asymmetry (item 1)
    asym = (
        nps.group_by("entry_variant", "state")
        .agg(pl.len().alias("rows"), pl.col("origin_id").n_unique().alias("origins"),
             pl.col("native_arm_id").n_unique().alias("arms"),
             (pl.col("side") == 0).sum().alias("side_zero"))
        .sort("state", "entry_variant")
        .collect()
    )
    asym.write_csv(o / "state_asymmetry_by_variant.csv")
    print(asym)

    # -- band-event rate / decided-side rate / selectivity, per arm x variant x symbol
    rates = (
        nps.group_by("symbol", "entry_variant", "native_arm_id", "arm_class",
                     "component", "orientation")
        .agg(
            pl.len().alias("eligible_origins"),
            (pl.col("state") == "NO_FEATURE").sum().alias("no_feature"),
            (pl.col("event_type").is_not_null()).sum().alias("band_events"),
            ((pl.col("event_type").is_not_null()) & (pl.col("side") != 0)).sum().alias("decided_side"),
            (pl.col("state") == "ORDER_CREATED").sum().alias("orders_created"),
            (pl.col("entry_ts").is_not_null()).sum().alias("filled"),
            (pl.col("state") == "EVENT_UNDECIDED").sum().alias("event_undecided"),
            (pl.col("state") == "NO_EVENT").sum().alias("no_event"),
            (pl.col("state") == "CENSORED").sum().alias("censored"),
            (pl.col("state") == "INCOMPLETE").sum().alias("incomplete"),
            pl.col("z").mean().alias("z_mean"),
            pl.col("horizon").mean().alias("h_mean"),
        )
        .with_columns(
            feature_ready=pl.col("eligible_origins") - pl.col("no_feature"),
        )
        .with_columns(
            band_event_rate=pl.col("band_events") / pl.col("feature_ready"),
            decided_side_rate=pl.col("decided_side") / pl.col("band_events"),
            selectivity_fill_per_origin=pl.col("filled") / pl.col("eligible_origins"),
            selectivity_fill_per_feature_ready=pl.col("filled") / pl.col("feature_ready"),
        )
        .sort("symbol", "entry_variant", "native_arm_id")
        .collect()
    )
    rates.write_parquet(o / "arm_rates.parquet")
    rates.write_csv(o / "arm_rates.csv")
    print("arm_rates rows", rates.height)


if __name__ == "__main__":
    for u in sys.argv[1:] or ["ctrader", "crypto"]:
        print("#" * 30, u)
        run(u)
