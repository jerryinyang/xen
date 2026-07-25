"""SPDR-015 fresh-context re-interrogation on the RE-RUN results (2026-07-24 06:24).

Reads only raw emissions under results/ and re-derives every headline per stratum.
Writes per-stratum tables to analysis_code/interrogation_tables/ and results/.
No experiment-local code imported. Canonical stratum defs from design.md.
"""
from __future__ import annotations

import json
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
OUT = Path(__file__).resolve().parent / "interrogation_tables"
OUT.mkdir(exist_ok=True)

POWERED_2A = (pl.col("n_origins") >= 80) & (pl.col("n_dates") >= 30)
POWERED_2B = (pl.col("n_oos") >= 80) & (pl.col("n_dates") >= 30)


def sec(t):
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


# ---------------------------------------------------------------- 2a
tm = pl.read_parquet(RES / "transition_metrics.parquet")
skill = tm.filter(~pl.col("is_shock_comparator") & (pl.col("method") != "persistence"))

sec("2A — corrected-CI SUPPORTED check (design AND-CI: dBrier<0 AND ci_hi<0)")
pw = skill.filter(POWERED_2A)
# recompute band from corrected CI columns to confirm labels
recomp = pw.with_columns(
    band_recomp=pl.when((pl.col("delta_brier_vs_pers") < 0) & (pl.col("delta_brier_ci_hi") < 0))
    .then(pl.lit("SUPPORTED"))
    .when(
        (pl.col("delta_brier_vs_pers") > 0) & (pl.col("delta_brier_ci_lo") > 0)
    )
    .then(pl.lit("CONTRADICTED"))
    .otherwise(pl.lit("WASH"))
)
mismatch = recomp.filter(pl.col("band_recomp") != pl.col("band_label"))
print("powered non-shock skill rows:", pw.height)
print("band recompute mismatches vs emitted:", mismatch.height)
if mismatch.height:
    print(mismatch.select(["symbol","clock","model","method","horizon_k",
                           "delta_brier_vs_pers","delta_brier_ci_lo","delta_brier_ci_hi",
                           "band_label","band_recomp"]))

sec("2A — per (clock,model,method,horizon) summary")
g2a = (
    pw.group_by(["clock", "model", "method", "horizon_k"])
    .agg(
        n_powered=pl.len(),
        med_dbrier=pl.col("delta_brier_vs_pers").median(),
        n_dneg=(pl.col("delta_brier_vs_pers") < 0).sum(),
        n_ci_hi_neg=(pl.col("delta_brier_ci_hi") < 0).sum(),
        n_supported=(pl.col("band_label") == "SUPPORTED").sum(),
        n_wash=(pl.col("band_label") == "WASH").sum(),
        n_contra=(pl.col("band_label") == "CONTRADICTED").sum(),
        med_stick=pl.col("stickiness").median(),
        med_gap=pl.col("state_gap_bps").median(),
    )
    .sort(["clock", "model", "method", "horizon_k"])
)
with pl.Config(tbl_rows=60, tbl_cols=20, fmt_str_lengths=40):
    print(g2a)
g2a.write_csv(OUT / "2a_summary_by_cell.csv")

sec("2A — state gap (level models, powered, per clock/model, k=1 only)")
gap = (
    tm.filter(~pl.col("is_shock_comparator") & (pl.col("method") == "empirical_p")
              & (pl.col("horizon_k") == 1) & POWERED_2A)
    .group_by(["clock", "model"])
    .agg(
        n=pl.len(),
        med_gap_bps=pl.col("state_gap_bps").median(),
        med_high_oo=pl.col("mean_next_abs_oo_HIGH").median(),
        med_low_oo=pl.col("mean_next_abs_oo_LOW").median(),
        med_stick=pl.col("stickiness").median(),
        n_gap_pos=(pl.col("state_gap_bps") > 0).sum(),
    )
    .sort(["clock", "model"])
)
print(gap)
gap.write_csv(OUT / "2a_state_gap.csv")

# full per-stratum 2a table to results/
pw.select(["symbol","clock","model","method","horizon_k","n_origins","n_dates",
           "delta_brier_vs_pers","delta_brier_ci_lo","delta_brier_ci_hi",
           "delta_accuracy_vs_pers","stickiness","state_gap_bps","band_label"]
          ).sort(["clock","model","method","horizon_k","symbol"]).write_parquet(
    RES / "per_stratum_2a.parquet")

# ---------------------------------------------------------------- 2b
om = pl.read_parquet(RES / "ordinal_metrics.parquet")
sec("2B — corrected-CI SUPPORTED check (AND-CI: (dhit>=0.05 AND hit_ci_lo>base) OR (dbrier<0 AND dbrier_ci_hi<0))")
pwb = om.filter(POWERED_2B)
recb = pwb.with_columns(
    band_recomp=pl.when(
        ((pl.col("delta_hit_vs_base") >= 0.05) & (pl.col("hit_ci_lo") > pl.col("base_rate")))
        | ((pl.col("delta_brier_vs_base") < 0) & (pl.col("delta_brier_ci_hi") < 0))
    ).then(pl.lit("SUPPORTED")).otherwise(pl.lit("WASH"))
)
mmb = recb.filter(pl.col("band_recomp") != pl.col("band_label"))
print("powered 2b rows:", pwb.height, " band mismatches:", mmb.height)
if mmb.height:
    print(mmb.select(["symbol","target","model","delta_hit_vs_base","hit_ci_lo","base_rate",
                      "delta_brier_vs_base","delta_brier_ci_hi","band_label","band_recomp"]))

sec("2B — per (target,model) summary")
g2b = (
    pwb.group_by(["target", "model"])
    .agg(
        n_powered=pl.len(),
        med_hit=pl.col("hit_rate").median(),
        med_base=pl.col("base_rate").median(),
        med_dhit=pl.col("delta_hit_vs_base").median(),
        n_hitci_gt_base=(pl.col("hit_ci_lo") > pl.col("base_rate")).sum(),
        med_dbrier=pl.col("delta_brier_vs_base").median(),
        n_dbrierci_neg=(pl.col("delta_brier_ci_hi") < 0).sum(),
        med_ic=pl.col("rank_ic_cont").median(),
        med_calib=pl.col("calibration_slope").median(),
        n_supported=(pl.col("band_label") == "SUPPORTED").sum(),
        n_wash=(pl.col("band_label") == "WASH").sum(),
    )
    .sort(["target", "model"])
)
with pl.Config(tbl_rows=40, tbl_cols=20, fmt_str_lengths=40):
    print(g2b)
g2b.write_csv(OUT / "2b_summary_by_cell.csv")

# per-stratum 2b full table
pwb.select(["symbol","target","model","n_oos","n_dates","hit_rate","base_rate",
            "delta_hit_vs_base","hit_ci_lo","delta_brier_vs_base","delta_brier_ci_hi",
            "rank_ic_cont","calibration_slope","band_label"]
           ).sort(["target","model","symbol"]).write_parquet(RES / "per_stratum_2b.parquet")

sec("2B — T-GT-CUR ridge per-symbol (powered)")
cur = pwb.filter((pl.col("target") == "T-GT-CUR") & (pl.col("model") == "ridge_cont")).sort("delta_hit_vs_base")
with pl.Config(tbl_rows=40, fmt_str_lengths=20):
    print(cur.select(["symbol","n_oos","hit_rate","base_rate","delta_hit_vs_base","hit_ci_lo",
                      "delta_brier_vs_base","delta_brier_ci_hi","rank_ic_cont","calibration_slope","band_label"]))

# ---------------------------------------------------------------- control
sec("CONTROL — LABEL-SHUFFLE derangement collapse + bite")
ld = pl.read_parquet(RES / "label_derange_collapse.parquet")
print("all zero-fixed-point:", ld["derangement_zero_fixed_points"].all(), " n_seeds unique:", ld["n_seeds"].unique().to_list())
csum = (
    ld.filter(pl.col("powered")).group_by("arm").agg(
        n_cells=pl.len(),
        med_collapse=pl.col("collapse_frac").median(),
        p05_collapse=pl.col("collapse_frac").quantile(0.05),
        p95_collapse=pl.col("collapse_frac").quantile(0.95),
        med_live_brier=pl.col("live_brier").median(),
        med_deranged_brier=pl.col("deranged_brier_median").median(),
        bite_detected_frac=pl.col("bite_detected").mean(),
    )
)
print(csum)
csum.write_csv(OUT / "control_collapse.csv")
# collapse_frac interpretation: deranged should be WORSE => collapse_frac ~ (live worse? ) check sign
print("\ncollapse_frac defn sample (live vs deranged Brier, powered):")
print(ld.filter(pl.col("powered")).select(["arm","symbol","model","method","live_brier","deranged_brier_median","collapse_frac","bite_detected"]).head(12))
print("\ncollapse_frac range:", ld.filter(pl.col('powered'))['collapse_frac'].min(), ld.filter(pl.col('powered'))['collapse_frac'].max())

# ---------------------------------------------------------------- shock comparator (disclosure)
sec("2A — R-SHOCK comparator (disclosure only, NOT regime)")
sh = tm.filter(pl.col("is_shock_comparator") & (pl.col("method") != "persistence") & POWERED_2A)
print(sh.group_by(["clock","method","horizon_k"]).agg(
    n=pl.len(), med_dbrier=pl.col("delta_brier_vs_pers").median(),
    n_ci_hi_neg=(pl.col("delta_brier_ci_hi")<0).sum(), med_stick=pl.col("stickiness").median()
).sort(["clock","method","horizon_k"]))

# ---------------------------------------------------------------- run length
sec("RUN-LENGTH disclosure")
rl = pl.read_parquet(RES / "run_length_metrics.parquet")
print(rl.group_by(["clock","model"]).agg(
    n=pl.len(), med_mae=pl.col("mae").median(), med_pred=pl.col("e_run_pred").median(),
    med_actual=pl.col("mean_actual").median()).sort(["clock","model"]))

# ---------------------------------------------------------------- spot recompute 2b BTC
sec("SPOT RECOMPUTE — BTC T-GT-CUR ridge from zz_ordinal")
zz = pl.read_parquet(RES / "zz_ordinal.parquet")
btc = zz.filter((pl.col("symbol")=="BTCUSDT")&(pl.col("target")=="T-GT-CUR")&(pl.col("model")=="ridge_cont"))
hit = (btc["y"] == (btc["p"] >= 0.5).cast(pl.Float64)).mean()
brier = ((btc["p"] - btc["y"])**2).mean()
print(f"n={btc.height} recompute hit={hit:.6f} brier={brier:.6f}")
row = om.filter((pl.col("symbol")=="BTCUSDT")&(pl.col("target")=="T-GT-CUR")&(pl.col("model")=="ridge_cont"))
print("emitted:", row.select(["n_oos","hit_rate","brier","rank_ic_cont"]).to_dicts())

print("\nDONE")
