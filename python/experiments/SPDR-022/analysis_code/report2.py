"""Extra markdown fragments: baselines, populations, controls (analyst-owned)."""

from __future__ import annotations

import pathlib

import pandas as pd

from report import md  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
ANA = ROOT / "results" / "analysis"
OUT = pathlib.Path(__file__).resolve().parent / "tables"


def baseline(u: str) -> None:
    d = pd.read_parquet(ANA / u / "per_stratum_estimates.parquet")
    f = d[(d.arm_class == "FIXED_NATIVE") & (d.state == "ORDER_CREATED")]
    cols = ["symbol", "entry_variant", "eligible_origin_n", "entry_fill_n", "close_n", "event_rate",
            "fill_rate", "exposure_per_origin", "gross_mean_bps", "gross_median_bps",
            "gross_trimmed_mean_bps", "win_share", "win_loss_ratio", "breakeven_win_share_net",
            "mfe_bps", "mae_bps", "effective_origin_blocks", "exit_reason"]
    md(f[cols].sort_values(["symbol", "entry_variant"]), OUT / f"md_baseline_{u}.md")


def populations(u: str) -> None:
    p = pd.read_csv(OUT / f"populations_{u}.csv")
    md(p, OUT / f"md_populations_{u}.md")
    s = pd.read_parquet(ANA / u / "native_parameter_selected_excluded.parquet")
    g = (s.groupby(["entry_variant", "selection", "state"], dropna=False)
         .agg(rows=("outcome_bps", "size"), mean_bps=("outcome_bps", "mean"),
              median_bps=("outcome_bps", "median")).reset_index())
    md(g, OUT / f"md_selexc_{u}.md")
    st = pd.read_parquet(ANA / u / "state_sections.parquet")
    g2 = (st.groupby(["entry_variant", "state"], dropna=False)
          .agg(rows=("row_n", "size"), row_n=("row_n", "sum"),
               mean_outcome_bps=("mean_outcome_bps", "median")).reset_index())
    md(g2, OUT / f"md_states_{u}.md")


def controls(u: str) -> None:
    c = pd.read_parquet(ANA / u / "controls.parquet")
    n = pd.read_parquet(ANA / u / "native_parameter_origins.parquet")
    raw = n[n.state == "ALL"][["symbol", "entry_variant", "arm_id", "estimate"]].rename(columns={"estimate": "raw"})
    m = c.merge(raw, on=["symbol", "entry_variant", "arm_id"], how="left")
    m["ci_excl"] = (m.ci_low > 0) | (m.ci_high < 0)
    m["identical_to_raw"] = (m.estimate - m.raw).abs() < 1e-12
    g = (m[m.control.isin(["TIME_DERANGEMENT", "MAGNITUDE_MATCH"])]
         .groupby(["control", "entry_variant", "magnitude_bin"], dropna=False)
         .agg(rows=("estimate", "size"), est_min=("estimate", "min"), est_med=("estimate", "median"),
              est_max=("estimate", "max"), ci_excl=("ci_excl", "sum"), mde_med=("mde", "median"),
              count=("count", "sum"), eff=("effective_count", "sum"),
              identical_to_raw=("identical_to_raw", "sum")).reset_index())
    md(g, OUT / f"md_controls_{u}.md")
    md(c[c.undefined_reason.notna()][["control", "analysis_stage", "population", "comparator", "undefined_reason"]],
       OUT / f"md_controls_pointer_{u}.md")


def selection(u: str) -> None:
    s = pd.read_parquet(ANA / u / "selection_checks.parquet")
    g = (s.groupby(["entry_variant", "component"], dropna=False)
         .agg(rows=("selected_n", "size"), selected_n=("selected_n", "sum"), excluded_n=("excluded_n", "sum"),
              payoff_scale_ratio_med=("payoff_scale_ratio", "median"),
              sign_share_difference_med=("sign_share_difference", "median"),
              excluded_mean_median_gap_med=("excluded_mean_median_gap", "median"),
              payoff_nonnull=("payoff_scale_ratio", "count")).reset_index())
    md(g, OUT / f"md_selection_{u}.md")


if __name__ == "__main__":
    for uni in ["ctrader", "crypto"]:
        print(f"##### {uni}")
        baseline(uni)
        populations(uni)
        controls(uni)
        selection(uni)
