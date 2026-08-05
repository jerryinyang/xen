"""Neutral probe: map the SPDR-023 analysis artifact value space (no mutation)."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

BASE = Path("experiments/SPDR-023/results/analysis")
UNIVERSES = ("ctrader", "crypto")


def show(df: pd.DataFrame, cols: list[str], name: str) -> None:
    print(f"--- {name}: {len(df)} rows")
    for c in cols:
        if c not in df.columns:
            continue
        vals = df[c].dropna().unique()
        print(f"   {c} ({len(vals)}): {sorted(map(str, vals))[:60]}")


def main() -> None:
    for u in UNIVERSES:
        print(f"######## {u}")
        ps = pd.read_parquet(BASE / u / "per_stratum_estimates.parquet")
        show(
            ps,
            [
                "estimate_source",
                "arm_class",
                "component",
                "parameter",
                "orientation",
                "orientation_pair",
                "entry_variant",
                "state",
                "metric_name",
                "device",
                "setting",
                "comparator_id",
                "symbol",
                "spread_cost_status",
                "cost_scope",
            ],
            "per_stratum_estimates",
        )
        print("   null-share of cost columns:")
        for c in [
            "spread_cost_status",
            "spread_rt_bps",
            "cost_scope",
            "partial_cost_mean_bps",
            "gross_mean_bps",
        ]:
            print(f"      {c}: null {ps[c].isna().mean():.4f} ({ps[c].isna().sum()}/{len(ps)})")

        npo = pd.read_parquet(BASE / u / "native_parameter_origins.parquet")
        show(
            npo,
            [
                "estimate_source",
                "arm_class",
                "parameter",
                "orientation",
                "orientation_pair",
                "component",
                "entry_variant",
                "state",
                "comparator_id",
            ],
            "native_parameter_origins",
        )

        ctl = pd.read_parquet(BASE / u / "controls.parquet")
        show(
            ctl,
            [
                "control",
                "analysis_stage",
                "population",
                "comparator",
                "comparator_id",
                "component",
                "entry_variant",
                "magnitude_bin",
                "undefined_reason",
            ],
            "controls",
        )

        for d in ("target", "stop", "trail", "hold", "size"):
            dev = pd.read_parquet(BASE / u / f"device_{d}.parquet")
            show(
                dev,
                ["arm_class", "component", "setting", "state", "metric_name", "comparator_id"],
                f"device_{d}",
            )


if __name__ == "__main__":
    sys.exit(main())
