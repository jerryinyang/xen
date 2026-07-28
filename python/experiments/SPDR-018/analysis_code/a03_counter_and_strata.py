"""Q4 counter-outcomes, Q5 heterogeneity, Q2 (p,W,L,edge) per stratum, cost-vs-rate decomposition."""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen")
RES = ROOT / "python/experiments/SPDR-018/results"
pd.set_option("display.width", 260)
pd.set_option("display.max_columns", 80)
pd.set_option("display.max_rows", 400)

m = pd.read_parquet(RES / "metrics_by_cell.parquet")
pw = m[(m["at_parent_target_precision"] == True) & (m["gross_p"].notna())].copy()

print("=" * 95)
print("Q4 — POWERED COUNTER-OUTCOMES  (SoT §10 end-state 3)")
print("=" * 95)
sig = pw[(pw["gross_mean_ci_low"] > 0) | (pw["gross_mean_ci_high"] < 0)].copy()
print("powered cells whose GROSS-mean block CI excludes zero:", len(sig), "of", len(pw))
print("  positive:", int((sig["gross_mean"] > 0).sum()), " negative:", int((sig["gross_mean"] < 0).sum()))
neg = sig[sig["gross_mean"] < 0].copy()
neg["flipped_gross"] = -neg["gross_mean"]
neg["flipped_net"] = -neg["gross_mean"] - neg["gross_cost_bps"]
print("\nIF the side were flipped (a counter-design), the SAME cells give:")
print(neg[["flipped_gross", "flipped_net", "gross_cost_bps", "gross_n"]].describe(
    percentiles=[0.5, 0.9, 0.99]).round(2).to_string())
print("\ncells whose flipped GROSS mean would exceed the partial cost floor:",
      int((neg["flipped_gross"] > neg["gross_cost_bps"]).sum()))
print("cells whose flipped gross-mean CI (mirrored) low > cost floor:",
      int(((-neg["gross_mean_ci_high"]) > neg["gross_cost_bps"]).sum()))
print("\nWhere they sit:")
print(neg.groupby(["arm", "residue_item", "basis"]).agg(
    n=("gross_mean", "size"), med_gross=("gross_mean", "median"),
    med_flip_net=("flipped_net", "median"), med_n=("gross_n", "median")).round(2).to_string())
print("\ntop-10 by |gross mean|:")
cols = ["arm", "residue_item", "symbol", "band", "clock", "basis", "conditioner", "event_type",
        "policy", "exit_mode", "signal", "gross_n", "gross_p", "gross_W", "gross_L", "gross_W_L",
        "gross_mean", "gross_mean_ci_low", "gross_mean_ci_high", "gross_cost_bps", "flipped_net"]
cols = [c for c in cols if c in neg.columns]
print(neg.reindex(neg["gross_mean"].abs().sort_values(ascending=False).index).head(10)[cols].to_string())

# the single positive one
pos = sig[sig["gross_mean"] > 0]
if len(pos):
    print("\nthe POSITIVE powered cell(s):")
    print(pos[cols[:-1]].to_string())

print("\n" + "=" * 95)
print("Q2/Q5 — PER-STRATUM (p, W, L, W/L, edge) + gross-vs-net distance decomposition")
print("=" * 95)


def strat_table(df, keys, name):
    g = df.groupby(keys, dropna=False).agg(
        n_cells=("gross_p", "size"),
        med_n=("gross_n", "median"),
        p=("gross_p", "median"),
        W=("gross_W", "median"),
        L=("gross_L", "median"),
        W_L=("gross_W_L", "median"),
        p_be=("gross_p_be", "median"),
        p_be_net=("gross_p_be_net", "median"),
        gross_edge=("gross_edge", "median"),
        net_edge=("net_edge", "median"),
        gross_bps=("gross_mean", "median"),
        net_bps=("net_mean", "median"),
        cost=("gross_cost_bps", "median"),
    )
    g["rate_term"] = (g["p_be"] - g["p"]).round(4)
    g["cost_term"] = (g["p_be_net"] - g["p_be"]).round(4)
    g["cost_share_of_gap"] = (g["cost_term"] / (g["cost_term"] + g["rate_term"])).round(3)
    print(f"\n### {name}")
    print(g.round(4).to_string())
    return g


tabs = {}
tabs["arm"] = strat_table(pw, ["arm"], "by arm (powered signed cells)")
tabs["item"] = strat_table(pw, ["arm", "residue_item"], "by residue item")
tabs["band"] = strat_table(pw, ["arm", "band"], "by band (DESIGN vs CONFIRM vs full TRAIN)")
tabs["clock"] = strat_table(pw, ["arm", "clock"], "by clock")
tabs["basis"] = strat_table(pw, ["arm", "basis"], "by basis")
tabs["symbol"] = strat_table(pw[pw["symbol"].notna()], ["symbol"], "by symbol")
tabs["exit"] = strat_table(pw[pw["exit_mode"].notna()], ["exit_mode", "signal"], "arm B by exit_mode x signal")
tabs["Cgrid"] = strat_table(pw[pw.arm == "C"], ["conditioner", "event_type", "policy"],
                            "arm C by conditioner x event x policy")
tabs["Ch"] = strat_table(pw[pw.arm == "C"], ["z", "h"], "arm C dose-response z x h")

parts = []
for k, v in tabs.items():
    d = v.reset_index()
    d.insert(0, "stratum_view", k)
    d["stratum_key"] = d.iloc[:, 1:].astype(str).agg(" | ".join, axis=1) if False else None
    parts.append(d)
pd.concat(parts, ignore_index=True).to_csv(RES / "analyst_stratum_tables.csv", index=False)
print("\n[written] results/analyst_stratum_tables.csv")

# full per-cell magnitude table (L-03: nothing hidden behind a pooled count)
keep = [c for c in ["arm", "residue_item", "basis", "band", "clock", "symbol", "signal",
                    "exit_mode", "conditioner", "conditioner_value", "event_type", "policy",
                    "source", "z", "h", "H", "leg", "model", "method", "target", "metric",
                    "at_parent_target_precision", "levers_exhausted",
                    "gross_n", "gross_n_dates", "gross_p", "gross_p_ci_low", "gross_p_ci_high",
                    "gross_W", "gross_W_ci_low", "gross_W_ci_high", "gross_L", "gross_L_ci_low",
                    "gross_L_ci_high", "gross_W_L", "gross_W_L_ci_low", "gross_W_L_ci_high",
                    "gross_p_be", "gross_p_be_net", "gross_edge", "gross_edge_ci_low",
                    "gross_edge_ci_high", "gross_mean", "gross_mean_ci_low", "gross_mean_ci_high",
                    "gross_median", "gross_trimmed_mean_10", "gross_cost_bps",
                    "net_mean", "net_mean_ci_low", "net_mean_ci_high", "net_edge",
                    "gross_block_mde_mean_bps", "gross_block_mde_p", "gross_block_mde_edge",
                    "target_mde", "target_rule", "band_label_mean", "band_label_edge",
                    "span_exact_span_frac", "span_frac_exceeding_nominal",
                    "coverage_effective_frac_of_nominal"] if c in m.columns]
full = m[m["gross_p"].notna()][keep]
full.to_parquet(RES / "analyst_per_cell_magnitudes.parquet", index=False)
print("[written] results/analyst_per_cell_magnitudes.parquet  rows=", len(full))
