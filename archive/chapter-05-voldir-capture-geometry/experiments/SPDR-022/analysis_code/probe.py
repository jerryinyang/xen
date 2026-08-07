"""SPDR-022 analyst probes (independent of experiment code).

Reads only canonical analysis artifacts + run-level integrity JSON.
Writes derived full tables to analysis_code/tables/ (never mutates canonical output).
"""

from __future__ import annotations

import json
import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
ANA = ROOT / "results" / "analysis"
OUT = pathlib.Path(__file__).resolve().parent / "tables"
OUT.mkdir(exist_ok=True)
UNIS = ["ctrader", "crypto"]


def load(u: str, name: str) -> pd.DataFrame:
    return pd.read_parquet(ANA / u / f"{name}.parquet")


def populations() -> None:
    for u in UNIS:
        d = load(u, "per_stratum_estimates")
        g = (
            d[d.state.isin(["ALL", "ORDER_CREATED"])]
            .groupby(["entry_variant", "arm_class", "estimate_source", "state"], dropna=False)
            .agg(
                rows=("estimate", "size"),
                eligible_origin_n=("eligible_origin_n", "sum"),
                entry_fill_n=("entry_fill_n", "sum"),
                close_n=("close_n", "sum"),
                common_fill_n=("common_fill_n", "sum"),
                common_close_n=("common_close_n", "sum"),
                eff_origin=("effective_origin_blocks", "sum"),
                eff_trade=("effective_trade_blocks", "sum"),
            )
            .reset_index()
        )
        g.to_csv(OUT / f"populations_{u}.csv", index=False)
        print(f"== populations {u}")
        print(g.to_string(index=False))
        st = d.groupby(["entry_variant", "arm_class", "state"], dropna=False).size().reset_index(name="rows")
        st.to_csv(OUT / f"state_rows_{u}.csv", index=False)
        print(st.to_string(index=False))


def native_tables() -> None:
    for u in UNIS:
        d = load(u, "per_stratum_estimates")
        d = d[d.estimate_source == "COMMON_ORIGIN_OCCUPANCY_INCLUSIVE"]
        base = d[d.state == "ALL"].copy()
        base["ci_excl_zero"] = (base.ci_low > 0) | (base.ci_high < 0)
        base["abs_gt_mde"] = base.estimate.abs() > base.mde
        cols = [
            "symbol", "entry_variant", "arm_class", "component", "parameter", "orientation",
            "orientation_pair", "comparator_id", "estimate", "ci_low", "ci_high", "mde",
            "eligible_origin_n", "entry_fill_n", "close_n", "effective_origin_blocks",
            "event_rate", "fill_rate", "exposure_per_origin", "gross_mean_bps",
            "gross_median_bps", "gross_trimmed_mean_bps", "win_share", "win_loss_ratio",
            "edge_bps", "mfe_bps", "mae_bps", "exit_reason", "ci_excl_zero", "abs_gt_mde",
        ]
        base[cols].sort_values(cols[:6]).to_csv(OUT / f"native_all_{u}.csv", index=False)
        summ = (
            base.groupby(["entry_variant", "arm_class", "component", "parameter", "orientation"], dropna=False)
            .agg(
                symbols=("symbol", "nunique"),
                est_min=("estimate", "min"),
                est_med=("estimate", "median"),
                est_max=("estimate", "max"),
                n_ci_excl_zero=("ci_excl_zero", "sum"),
                n_pos=("estimate", lambda s: int((s > 0).sum())),
                mde_med=("mde", "median"),
                elig=("eligible_origin_n", "sum"),
                fills=("entry_fill_n", "sum"),
                closes=("close_n", "sum"),
                eff=("effective_origin_blocks", "sum"),
            )
            .reset_index()
        )
        summ.to_csv(OUT / f"native_summary_{u}.csv", index=False)
        print(f"== native summary {u} (rows={len(base)})")
        print(summ.round(4).to_string(index=False))


def device_tables() -> None:
    for u in UNIS:
        frames = []
        for dev in ["target", "stop", "trail", "hold", "size"]:
            df = load(u, f"device_{dev}")
            frames.append(df)
        d = pd.concat(frames, ignore_index=True)
        d.to_csv(OUT / f"device_all_{u}.csv", index=False)
        live = d[d.common_close_n.fillna(0) > 0].copy()
        live["ci_excl_zero"] = (live.ci_low > 0) | (live.ci_high < 0)
        summ = (
            live.groupby(["entry_variant", "device", "setting", "component", "metric_name"], dropna=False)
            .agg(
                rows=("estimate", "size"),
                symbols=("symbol", "nunique"),
                est_min=("estimate", "min"),
                est_med=("estimate", "median"),
                est_max=("estimate", "max"),
                n_ci_excl_zero=("ci_excl_zero", "sum"),
                mde_med=("mde", "median"),
                common_fill_n=("common_fill_n", "sum"),
                common_close_n=("common_close_n", "sum"),
                eff_trade=("effective_trade_blocks", "sum"),
            )
            .reset_index()
        )
        summ.to_csv(OUT / f"device_summary_{u}.csv", index=False)
        print(f"== device rows {u}: total={len(d)} with_common_close={len(live)}")
        print(d.groupby(["device", "state"], dropna=False).size().to_string())
        print(summ.round(4).to_string(index=False))


def controls_tables() -> None:
    for u in UNIS:
        c = load(u, "controls")
        n = load(u, "native_parameter_origins")
        raw = n[n.state == "ALL"][["symbol", "entry_variant", "arm_id", "estimate", "ci_low", "ci_high", "mde"]]
        raw = raw.rename(columns={"estimate": "raw_estimate", "ci_low": "raw_ci_low", "ci_high": "raw_ci_high", "mde": "raw_mde"})
        m = c.merge(raw, on=["symbol", "entry_variant", "arm_id"], how="left")
        m["collapse_fraction"] = m.estimate / m.raw_estimate
        m.to_csv(OUT / f"controls_joined_{u}.csv", index=False)
        for ctl in ["TIME_DERANGEMENT", "MAGNITUDE_MATCH"]:
            s = m[m.control == ctl]
            print(f"== {u} {ctl}: rows={len(s)} identical_to_raw={(s.estimate == s.raw_estimate).sum()}")
            print(
                s.groupby(["entry_variant", "magnitude_bin"], dropna=False)
                .agg(
                    rows=("estimate", "size"),
                    est_med=("estimate", "median"),
                    est_min=("estimate", "min"),
                    est_max=("estimate", "max"),
                    n_ci_excl_zero=("estimate", lambda x: 0),
                    count=("count", "sum"),
                    eff=("effective_count", "sum"),
                )
                .round(4)
                .to_string()
            )
            sub = s.dropna(subset=["collapse_fraction"])
            if len(sub):
                print("collapse_fraction quantiles:", sub.collapse_fraction.quantile([0.05, 0.25, 0.5, 0.75, 0.95]).round(4).to_dict())


def selection_state() -> None:
    for u in UNIS:
        s = load(u, "selection_checks")
        s.to_csv(OUT / f"selection_checks_{u}.csv", index=False)
        print(f"== selection_checks {u} rows={len(s)}")
        print(
            s.groupby(["entry_variant", "component"], dropna=False)
            .agg(
                rows=("selected_n", "size"),
                sel=("selected_n", "sum"),
                exc=("excluded_n", "sum"),
                payoff_med=("payoff_scale_ratio", "median"),
                sign_med=("sign_share_difference", "median"),
                gap_med=("excluded_mean_median_gap", "median"),
            )
            .round(4)
            .to_string()
        )
        st = load(u, "state_sections")
        st.to_csv(OUT / f"state_sections_{u}.csv", index=False)
        print(f"== state_sections {u} rows={len(st)}")
        print(
            st.groupby(["entry_variant", "state"], dropna=False)
            .agg(rows=("row_n", "size"), row_n=("row_n", "sum"), mean_outcome_bps=("mean_outcome_bps", "median"))
            .round(4)
            .to_string()
        )
        se = load(u, "native_parameter_selected_excluded")
        print(f"== selected_excluded {u} rows={len(se)}")
        print(
            se.groupby(["entry_variant", "selection", "state"], dropna=False)
            .agg(rows=("outcome_bps", "size"), mean_bps=("outcome_bps", "mean"), median_bps=("outcome_bps", "median"))
            .round(4)
            .to_string()
        )


def cost_fields() -> None:
    for u in UNIS:
        d = load(u, "per_stratum_estimates")
        print(
            u,
            "rows",
            len(d),
            {c: int(d[c].isna().sum()) for c in ["spread_cost_status", "spread_rt_bps", "cost_scope", "partial_cost_mean_bps"]},
        )
        t = load(u, "native_parameter_shared_trades")
        print(u, "shared_trades rows", len(t), "partial_cost_bps null", int(t.partial_cost_bps.isna().sum()),
              "nonzero", int((t.partial_cost_bps.fillna(0) != 0).sum()))
        run = pathlib.Path(ROOT.parents[1] / "data" / "nautilus_runs" / f"SPDR-022-{u}-train-20260803T140238Z")
        print(u, "run_summary disclosure", json.load(open(run / "run_summary.json"))["spread_cost_disclosure"])


if __name__ == "__main__":
    populations()
    native_tables()
    device_tables()
    controls_tables()
    selection_state()
    cost_fields()
