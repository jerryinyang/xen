"""Read-only probes over the canonical SPDR-021 analysis artifacts.

Writes nothing. Prints grouped summaries used to ground `analysis.md`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1] / "results" / "analysis"
pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 400)
pd.set_option("display.max_columns", 60)


def load(universe: str, name: str) -> pd.DataFrame:
    return pd.read_parquet(ROOT / universe / f"{name}.parquet")


def native_all(universe: str) -> pd.DataFrame:
    d = load(universe, "per_stratum_estimates")
    n = d[
        d.arm_class.isin(["FIXED_NATIVE", "NATIVE", "NATIVE_COMBINATION"])
        & (d.state == "ALL")
    ].copy()
    n["arm_key"] = (
        n.component.fillna("FIXED")
        + " | "
        + n.parameter.fillna("-")
        + " | "
        + n.orientation.fillna("-")
    )
    return n


def sign_counts(g: pd.DataFrame) -> pd.Series:
    return pd.Series(
        {
            "n_cells": len(g),
            "median_est": g.estimate.median(),
            "min_est": g.estimate.min(),
            "max_est": g.estimate.max(),
            "ci_excl_zero_pos": int(((g.ci_low > 0)).sum()),
            "ci_excl_zero_neg": int(((g.ci_high < 0)).sum()),
            "median_mde": g.mde.median(),
            "median_elig": g.eligible_origin_n.median(),
            "median_blocks": g.effective_origin_blocks.astype(float).median(),
        }
    )


def cmd_native(universe: str) -> None:
    n = native_all(universe)
    print(f"### native lens=COMMON_ORIGIN_OCCUPANCY_INCLUSIVE state=ALL {universe}")
    print(n.groupby("arm_key").apply(sign_counts, include_groups=False).to_string())


def cmd_native_full(universe: str) -> None:
    n = native_all(universe)
    cols = [
        "symbol",
        "arm_key",
        "estimate",
        "ci_low",
        "ci_high",
        "mde",
        "eligible_origin_n",
        "signal_count",
        "fill_count",
        "entry_fill_n",
        "close_n",
        "effective_origin_blocks",
        "fill_rate",
        "exposure_per_origin",
    ]
    print(n[cols].sort_values(["arm_key", "symbol"]).to_string(index=False))


def cmd_mgmt(universe: str) -> None:
    d = load(universe, "per_stratum_estimates")
    m = d[~d.arm_class.isin(["FIXED_NATIVE", "NATIVE", "NATIVE_COMBINATION"])].copy()
    m["dev_key"] = m.device + " | " + m.setting
    print(f"### management lens=COMMON_CLOSE_TRADE {universe}")

    def f(g: pd.DataFrame) -> pd.Series:
        return pd.Series(
            {
                "n_cells": len(g),
                "median_est": g.estimate.median(),
                "min_est": g.estimate.min(),
                "max_est": g.estimate.max(),
                "ci_pos": int((g.ci_low > 0).sum()),
                "ci_neg": int((g.ci_high < 0).sum()),
                "median_mde": g.mde.median(),
                "median_ccn": g.common_close_n.median(),
                "min_ccn": g.common_close_n.min(),
                "max_ccn": g.common_close_n.max(),
                "median_blocks": g.effective_trade_blocks.astype(float).median(),
            }
        )

    print(m.groupby(["arm_class", "dev_key"]).apply(f, include_groups=False).to_string())


def cmd_mgmt_full(universe: str) -> None:
    d = load(universe, "per_stratum_estimates")
    m = d[~d.arm_class.isin(["FIXED_NATIVE", "NATIVE", "NATIVE_COMBINATION"])]
    cols = [
        "symbol",
        "arm_id",
        "device",
        "setting",
        "comparator_id",
        "estimate",
        "ci_low",
        "ci_high",
        "mde",
        "entry_fill_n",
        "close_n",
        "common_fill_n",
        "common_close_n",
        "effective_trade_blocks",
        "gross_mean_bps",
        "partial_cost_mean_bps",
        "win_share",
        "exit_reason",
    ]
    print(m[cols].sort_values(["device", "setting", "symbol"]).to_string(index=False))


def cmd_devices(universe: str) -> None:
    for dev in ["target", "stop", "trail", "hold", "size"]:
        d = load(universe, f"device_{dev}")
        d = d[d.state == "ORDER_CREATED"]
        print(f"### device {dev.upper()} {universe} (state=ORDER_CREATED)")

        def f(g: pd.DataFrame) -> pd.Series:
            return pd.Series(
                {
                    "n": len(g),
                    "median_obs": g.observed.median(),
                    "median_cmp": g.comparator_observed.median(),
                    "median_est": g.estimate.median(),
                    "min_est": g.estimate.min(),
                    "max_est": g.estimate.max(),
                    "ci_pos": int((g.ci_low > 0).sum()),
                    "ci_neg": int((g.ci_high < 0).sum()),
                    "median_mde": g.mde.median(),
                    "median_ccn": g.common_close_n.median(),
                    "median_blk": g.effective_trade_blocks.astype(float).median(),
                }
            )

        print(
            d.groupby(["metric_name", "arm_class", "setting"])
            .apply(f, include_groups=False)
            .to_string()
        )


def cmd_controls(universe: str) -> None:
    c = load(universe, "controls")
    print(f"### controls {universe}")
    print(c.groupby(["control", "analysis_stage", "population", "comparator"]).size())

    def f(g: pd.DataFrame) -> pd.Series:
        return pd.Series(
            {
                "n": len(g),
                "median_est": g.estimate.median(),
                "min_est": g.estimate.min(),
                "max_est": g.estimate.max(),
                "ci_pos": int((g.ci_low > 0).sum()),
                "ci_neg": int((g.ci_high < 0).sum()),
                "median_mde": g.mde.median(),
                "median_count": g["count"].median(),
                "median_eff": g.effective_count.median(),
            }
        )

    live = c[c.estimate.notna()]
    print(live.groupby(["control"]).apply(f, include_groups=False).to_string())
    print(
        live.groupby(["control", "symbol"]).apply(f, include_groups=False).to_string()
        if universe == "ctrader"
        else ""
    )
    print("undefined rows:")
    print(
        c[c.estimate.isna()][
            ["control", "analysis_stage", "population", "comparator", "undefined_reason"]
        ].to_string(index=False)
    )


def cmd_selection(universe: str) -> None:
    s = load(universe, "selection_checks")
    print(f"### selection_checks {universe}", s.shape)
    print(s.describe().to_string())
    print(s.sort_values("excluded_mean_median_gap", ascending=False).head(15).to_string(index=False))
    se = load(universe, "native_parameter_selected_excluded")
    print("selected/excluded rows", se.shape)
    print(se.groupby("selection").size())
    print(
        se.groupby(["selection"])
        .outcome_bps.agg(["count", "mean", "median", "std"])
        .to_string()
    )
    print(se.groupby(["state", "selection"]).size().to_string())


def cmd_states(universe: str) -> None:
    st = load(universe, "state_sections")
    print(f"### state_sections {universe}", st.shape)
    print(st.groupby("state").agg(rows=("row_n", "sum"), arms=("arm_id", "nunique")).to_string())
    print(
        st.groupby(["state"])
        .apply(
            lambda g: pd.Series(
                {
                    "wmean_outcome_bps": (g.mean_outcome_bps * g.row_n).sum() / g.row_n.sum(),
                    "min": g.mean_outcome_bps.min(),
                    "max": g.mean_outcome_bps.max(),
                }
            ),
            include_groups=False,
        )
        .to_string()
    )


def cmd_trades(universe: str) -> None:
    t = load(universe, "native_parameter_shared_trades")
    print(f"### shared trades {universe}", t.shape)
    print(t.groupby("analysis_state").size().to_string())
    filled = t[t._entry_ns.notna()]
    closed = t[t._exit_ns.notna()]
    print("rows", len(t), "with _entry_ns", len(filled), "with _exit_ns", len(closed))
    print("common_fill_n non-null", int(t.common_fill_n.notna().sum()))
    paired = t[t.paired_outcome_delta_bps.notna()]
    print("paired delta rows", len(paired))
    if len(paired):
        print(paired.paired_outcome_delta_bps.describe().to_string())
        print(
            paired.groupby(["component", "orientation", "parameter"])
            .paired_outcome_delta_bps.agg(["count", "mean", "median"])
            .to_string()
        )


def cmd_costs(universe: str) -> None:
    d = load(universe, "per_stratum_estimates")
    print(f"### cost/disclosure columns {universe}")
    for c in ["spread_cost_status", "spread_rt_bps", "cost_scope"]:
        print(c, "non-null:", int(d[c].notna().sum()), "of", len(d))
    print(d[["gross_mean_bps", "partial_cost_mean_bps", "edge_bps"]].describe().to_string())
    t = load(universe, "native_parameter_shared_trades")
    print("shared-trade partial_cost_bps:")
    print(t.partial_cost_bps.describe().to_string())


CMDS = {
    "native": cmd_native,
    "native_full": cmd_native_full,
    "mgmt": cmd_mgmt,
    "mgmt_full": cmd_mgmt_full,
    "devices": cmd_devices,
    "controls": cmd_controls,
    "selection": cmd_selection,
    "states": cmd_states,
    "trades": cmd_trades,
    "costs": cmd_costs,
}

if __name__ == "__main__":
    CMDS[sys.argv[1]](sys.argv[2])
