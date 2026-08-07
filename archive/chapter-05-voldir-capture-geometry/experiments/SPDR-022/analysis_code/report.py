"""SPDR-022 markdown fragment generator for analysis.md (analyst-owned)."""

from __future__ import annotations

import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
ANA = ROOT / "results" / "analysis"
OUT = pathlib.Path(__file__).resolve().parent / "tables"
OUT.mkdir(exist_ok=True)
DEVICES = ["target", "stop", "trail", "hold", "size"]


def devices(u: str) -> pd.DataFrame:
    d = pd.concat([pd.read_parquet(ANA / u / f"device_{x}.parquet") for x in DEVICES], ignore_index=True)
    d["ci_excl_zero"] = (d.ci_low > 0) | (d.ci_high < 0)
    return d


def _fmt(v: object) -> str:
    if isinstance(v, float):
        return "" if pd.isna(v) else f"{v:.4f}"
    return "" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v)


def md(df: pd.DataFrame, path: pathlib.Path) -> None:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(_fmt(r[c]) for c in cols) + " |")
    text = "\n".join(lines)
    path.write_text(text)
    print(f"--- {path.name} ({len(df)} rows)")
    print(text)


def device_group(u: str, classes: list[str], tag: str) -> None:
    d = devices(u)
    s = d[d.arm_class.isin(classes) & (d.common_close_n.fillna(0) > 0)]
    g = (
        s.groupby(["entry_variant", "device", "setting", "component", "metric_name"], dropna=False)
        .agg(
            sym=("symbol", "nunique"),
            est_min=("estimate", "min"),
            est_med=("estimate", "median"),
            est_max=("estimate", "max"),
            ci_ex0=("ci_excl_zero", "sum"),
            mde_med=("mde", "median"),
            cfill=("common_fill_n", "sum"),
            cclose=("common_close_n", "sum"),
            efftr=("effective_trade_blocks", "sum"),
        )
        .reset_index()
    )
    md(g, OUT / f"md_device_{tag}_{u}.md")


def fixed_devices(u: str) -> None:
    d = devices(u)
    s = d[d.arm_class == "FIXED_MANAGEMENT"]
    g = (
        s.groupby(["entry_variant", "device", "setting", "state"], dropna=False)
        .agg(
            rows=("estimate", "size"),
            sym=("symbol", "nunique"),
            n_nonnull_est=("estimate", "count"),
            cfill=("common_fill_n", "sum"),
            cclose=("common_close_n", "sum"),
            efftr=("effective_trade_blocks", "sum"),
        )
        .reset_index()
    )
    md(g, OUT / f"md_fixed_device_{u}.md")


def native_group(u: str) -> None:
    d = pd.read_parquet(ANA / u / "per_stratum_estimates.parquet")
    d = d[(d.estimate_source == "COMMON_ORIGIN_OCCUPANCY_INCLUSIVE") & (d.state == "ALL")].copy()
    d["ci_excl_zero"] = (d.ci_low > 0) | (d.ci_high < 0)
    g = (
        d.groupby(["entry_variant", "arm_class", "component", "parameter", "orientation"], dropna=False)
        .agg(
            sym=("symbol", "nunique"),
            est_min=("estimate", "min"),
            est_med=("estimate", "median"),
            est_max=("estimate", "max"),
            ci_ex0=("ci_excl_zero", "sum"),
            mde_med=("mde", "median"),
            elig=("eligible_origin_n", "sum"),
            fills=("entry_fill_n", "sum"),
            closes=("close_n", "sum"),
            eff=("effective_origin_blocks", "sum"),
            ev_rate=("event_rate", "median"),
            fill_rate=("fill_rate", "median"),
            occ=("exposure_per_origin", "median"),
        )
        .reset_index()
    )
    md(g, OUT / f"md_native_{u}.md")


def native_descriptive(u: str) -> None:
    d = pd.read_parquet(ANA / u / "per_stratum_estimates.parquet")
    d = d[(d.estimate_source == "COMMON_ORIGIN_OCCUPANCY_INCLUSIVE") & (d.state == "ORDER_CREATED")]
    g = (
        d.groupby(["entry_variant", "arm_class"], dropna=False)
        .agg(
            rows=("estimate", "size"),
            gross_mean=("gross_mean_bps", "median"),
            gross_med=("gross_median_bps", "median"),
            gross_trim=("gross_trimmed_mean_bps", "median"),
            win_share=("win_share", "median"),
            wl=("win_loss_ratio", "median"),
            be_win=("breakeven_win_share_net", "median"),
            edge=("edge_bps", "median"),
            mfe=("mfe_bps", "median"),
            mae=("mae_bps", "median"),
            trades=("trade_count", "sum"),
        )
        .reset_index()
    )
    md(g, OUT / f"md_native_desc_{u}.md")


def exit_mix(u: str) -> None:
    d = pd.read_parquet(ANA / u / "per_stratum_estimates.parquet")
    d = d[d.exit_reason.notna()]
    g = d.groupby(["entry_variant", "arm_class", "exit_reason"], dropna=False).size().reset_index(name="rows")
    g = g.sort_values(["entry_variant", "arm_class", "rows"], ascending=[True, True, False])
    md(g.head(60), OUT / f"md_exit_{u}.md")


if __name__ == "__main__":
    for uni in ["ctrader", "crypto"]:
        print(f"##### {uni}")
        native_group(uni)
        native_descriptive(uni)
        exit_mix(uni)
        fixed_devices(uni)
        device_group(uni, ["MANAGEMENT"], "individual")
        device_group(uni, ["MANAGEMENT_COMPONENT_COMBINATION"], "compcombo")
        device_group(uni, ["MANAGEMENT_DEVICE_COMBINATION"], "devcombo")
