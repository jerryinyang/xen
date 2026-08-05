"""Neutral probe: where the paired native trade-lens signal actually lives.

Answers: what share of common closes differ at all, and how concentrated is the
mean paired delta in the differing minority.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path("experiments/SPDR-023/results/analysis")


def main() -> None:
    for u in ("ctrader", "crypto"):
        st = pd.read_parquet(
            BASE / u / "native_parameter_shared_trades.parquet",
            columns=[
                "entry_variant",
                "parameter",
                "orientation",
                "component",
                "arm_class",
                "paired_outcome_delta_bps",
                "outcome_bps",
                "fixed_outcome_bps",
                "_entry_ns",
                "fixed_entry_ns",
            ],
        )
        st["same_entry"] = st["_entry_ns"] == st["fixed_entry_ns"]
        st["nz"] = st["paired_outcome_delta_bps"].abs() > 1e-12
        print(f"\n######## {u} shared_trade_rows={len(st)}")
        g = st.groupby(["entry_variant", "parameter"]).agg(
            rows=("nz", "size"),
            share_identical_entry_ns=("same_entry", "mean"),
            share_nonzero_delta=("nz", "mean"),
            mean_delta_all=("paired_outcome_delta_bps", "mean"),
        )
        g["mean_delta_on_differing"] = st[st["nz"]].groupby(["entry_variant", "parameter"])[
            "paired_outcome_delta_bps"
        ].mean()
        print(g.to_string())

        print("\n-- top absolute-delta concentration (differing pairs only) --")
        d = st[st["nz"]]
        for (v, p), gg in d.groupby(["entry_variant", "parameter"]):
            a = gg["paired_outcome_delta_bps"].to_numpy()
            tot = float(np.sum(a))
            order = np.argsort(-np.abs(a))
            top1 = float(np.sum(a[order[: max(1, len(a) // 100)]]))
            print(
                f"   {v}/{p}: n={len(a)} sum={tot:.1f} bps; "
                f"largest 1% by |delta| contribute {top1:.1f} bps "
                f"({(top1 / tot * 100 if tot else float('nan')):.1f}% of the sum)"
            )


if __name__ == "__main__":
    sys.exit(main())
