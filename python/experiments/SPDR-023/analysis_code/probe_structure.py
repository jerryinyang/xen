"""Neutral probe: row accounting and population structure of SPDR-023 analysis tables."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

BASE = Path("experiments/SPDR-023/results/analysis")

pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 400)
pd.set_option("display.max_columns", 60)


def main() -> None:
    for u in ("ctrader", "crypto"):
        print(f"######## {u}")
        ps = pd.read_parquet(BASE / u / "per_stratum_estimates.parquet")
        print("per_stratum rows by estimate_source x arm_class x state:")
        print(
            ps.groupby(["estimate_source", "arm_class", "state"], dropna=False)
            .size()
            .rename("n")
            .reset_index()
        )
        print("\nestimate null share by estimate_source:")
        print(ps.groupby("estimate_source")["estimate"].agg(["size", "count"]))

        npo = pd.read_parquet(BASE / u / "native_parameter_origins.parquet")
        print("\nnative_parameter_origins rows by arm_class x parameter x state:")
        print(
            npo.groupby(["arm_class", "parameter", "state"], dropna=False)
            .size()
            .rename("n")
            .reset_index()
        )
        print("\nnpo numeric non-null counts:")
        print(npo[[c for c in npo.columns if npo[c].dtype.kind in "fi"]].count())

        dev = pd.read_parquet(BASE / u / "device_target.parquet")
        print("\ndevice_target rows by arm_class x state:")
        print(dev.groupby(["arm_class", "state"], dropna=False).size())
        print("\ndevice_target counts non-null:")
        print(dev[[c for c in dev.columns if dev[c].dtype.kind in "fi"]].count())
        print("\nsample device_target rows:")
        print(dev.head(6).to_string())

        ctl = pd.read_parquet(BASE / u / "controls.parquet")
        print("\ncontrols rows by control x population:")
        print(ctl.groupby(["control", "population"], dropna=False).size())
        print("\ncontrols estimate non-null by control:")
        print(ctl.groupby("control")["estimate"].agg(["size", "count"]))
        print()


if __name__ == "__main__":
    sys.exit(main())
