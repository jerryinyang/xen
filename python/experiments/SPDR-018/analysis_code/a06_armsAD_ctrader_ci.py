"""Arms A & D quantification (A1-A5, D1-D8), cTrader replication, IN-5 CI coverage audit."""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen")
RES = ROOT / "python/experiments/SPDR-018/results"
pd.set_option("display.width", 270); pd.set_option("display.max_columns", 90); pd.set_option("display.max_rows", 500)

m = pd.read_parquet(RES / "metrics_by_cell.parquet")
A = m[m.arm == "A"]; D = m[m.arm == "D"]

print("=" * 100); print("ARM A — SPDR-012 residue"); print("=" * 100)
print("\nA1 V-REGIME-HMM: HIGH-LOW next-|move| gap, pooled full TRAIN")
g = A[(A.metric == "gap_high_low_bps")]
print("  cells:", len(g))
pool = g[g.basis == "pooled_raw"]
print(pool[["clock", "band", "gap_bps", "gap_ci_low", "gap_ci_high", "n_high", "n_low",
            "n_dates", "band_label_gap", "mean_next_abs_oo_HIGH", "mean_next_abs_oo_LOW"]].to_string())
print("\n  per-symbol gap by clock (median + share with CI excluding zero):")
ps = g[g.basis == "per_symbol"]
print(ps.groupby(["clock", "band"]).agg(
    n=("gap_bps", "size"), med_gap=("gap_bps", "median"),
    frac_ci_excl_0_pos=("gap_ci_low", lambda s: float((s > 0).mean())),
    frac_ci_excl_0_neg=("gap_ci_high", lambda s: float((s < 0).mean())),
    med_ciw=("gap_ci_high", "median")).round(3).to_string())
print("\n  gap relative to the cost floor (13.5 bps partial) — this is a MAGNITUDE object, not P&L:")
print("  pooled gaps: ", pool[["clock", "band", "gap_bps"]].to_string(index=False))

print("\nA2 V-TAIL (exceedance diffs at p90/p95):")
t = A[A.metric.isin(["exceed_diff_p90", "exceed_diff_p95"])]
print(t.groupby(["metric", "clock", "band", "basis"]).agg(
    n=("value", "size"), med=("value", "median"),
    frac_ci_pos=("ci_low", lambda s: float((s > 0).mean())),
    frac_ci_neg=("ci_high", lambda s: float((s < 0).mean())),
    at_target=("at_parent_target_precision", lambda s: int((s == True).sum()))).round(4).to_string())

print("\nA3 DESIGN-band date deficit (target >= 225 dates):")
a3 = m[m.residue_item.str.contains("A3", na=False)]
print(a3.groupby(["band", "basis", "clock"]).agg(
    n=("n_dates", "size"), med_dates=("n_dates", "median"),
    frac_ge225=("n_dates", lambda s: float((s >= 225).mean())),
    med_short=("n_dates_short_of_225", "median")).round(3).to_string())

print("\nA4 V-CLOCK incremental R^2 (obs per date vs dummies):")
a4 = A[A.metric.astype(str).str.startswith("incr_r2")]
print(a4.groupby(["clock", "variant", "band"]).agg(
    n=("incremental_r2", "size"), med_r2=("incremental_r2", "median"),
    med_obs_per_date=("n_obs_per_date", "median"), med_dummies=("n_dummies", "median"),
    frac_ci_pos=("r2_ci_low", lambda s: float((s > 0).mean())),
    lbl=("band_label_r2", lambda s: s.value_counts().to_dict())).to_string())

print("\nA5 calendar-thirds clause satisfiability:")
a5 = A[A.metric == "calendar_thirds_populated"]
print("  cells:", len(a5))
print("  thirds_populated distribution:", a5["thirds_populated"].value_counts().to_dict())
print("  clause_satisfiable:", a5["clause_satisfiable"].value_counts(dropna=False).to_dict())
print("  thirds_sign_agree distribution:", a5["thirds_sign_agree"].value_counts(dropna=False).to_dict())

print("\nA IC cells (oos_ic):")
ic = A[A.metric == "oos_ic"]
print(ic.groupby(["clock", "band", "basis"]).agg(
    n=("rank_ic", "size"), med_ic=("rank_ic", "median"),
    frac_ci_pos=("ic_ci_low", lambda s: float((s > 0).mean())),
    lbl=("band_label_ic", lambda s: s.value_counts().to_dict())).round(4).to_string())

print("\n" + "=" * 100); print("ARM D — SPDR-015 residue"); print("=" * 100)
print("\nD1 transitions (trans_up / trans_dn), n_trans vs the <50 rule:")
d1 = D[D.metric.isin(["trans_up", "trans_dn"])]
print(d1.groupby(["metric", "clock", "band", "basis"]).agg(
    n=("n_trans", "size"), med_n_trans=("n_trans", "median"),
    frac_ge50=("n_trans", lambda s: float((s >= 50).mean())),
    med_short=("shortfall_n_trans", "median"),
    at_target=("at_parent_target_precision", lambda s: int((s == True).sum()))).round(3).to_string())

print("\nD2 run-length MAE:")
d2 = D[D.metric == "run_len_mae"]
print(d2.groupby(["clock", "band", "basis"]).agg(
    n=("mae", "size"), med_mae=("mae", "median"), med_e_run=("e_run_pred", "median"),
    at_target=("at_parent_target_precision", lambda s: int((s == True).sum()))).round(3).to_string())

print("\nD3/D4/D8 hit-rate targets by band and model:")
hr = D[D.metric == "hit_rate"]
print(hr.groupby(["target", "band", "base_model"]).agg(
    n=("hit_rate", "size"), med_hit=("hit_rate", "median"), med_base=("base_rate", "median"),
    med_lift=("delta_accuracy_vs_pers", "median"),
    at_target=("at_parent_target_precision", lambda s: int((s == True).sum())),
    lbl=("band_label", lambda s: s.value_counts().to_dict())).round(4).to_string())

print("\nD5/D6 delta-Brier vs persistence, by model/band:")
db = D[D.metric == "delta_brier_vs_base_rate"]
print(db.groupby(["model", "clock", "band", "horizon_k"]).agg(
    n=("delta_brier_vs_pers", "size"), med=("delta_brier_vs_pers", "median"),
    frac_ci_neg=("delta_brier_ci_hi", lambda s: float((s < 0).mean())),
    frac_ci_pos=("delta_brier_ci_lo", lambda s: float((s > 0).mean())),
    at_target=("at_parent_target_precision", lambda s: int((s == True).sum()))).round(5).to_string())

print("\nD7 D1 stickiness p_stay:")
d7 = D[D.metric == "p_stay"]
print(d7.groupby(["clock", "band", "basis"]).agg(
    n=("p_stay", "size"), med=("p_stay", "median"), lo=("p_stay", "min"), hi=("p_stay", "max"),
    at_target=("at_parent_target_precision", lambda s: int((s == True).sum()))).round(4).to_string())

print("\nD8 CONFIRM-vs-DESIGN comparison on the same objects:")
d8 = D[D.residue_item.astype(str).str.contains("D8", na=False)]
print("D8-tagged cells:", len(d8), " never_scored_before True:", int((d8["never_scored_before"] == True).sum()))
print(d8.groupby(["metric", "band"]).agg(
    n=("value", "size"), med_hit=("hit_rate", "median"), med_base=("base_rate", "median"),
    med_dbrier=("delta_brier_vs_pers", "median")).round(4).to_string())

print("\n" + "=" * 100); print("cTRADER REPLICATION (credibility only — NEVER pooled into n)"); print("=" * 100)
ctr = pd.read_parquet(RES / "ctrader_replication.parquet")
print("rows:", len(ctr), "cols:", list(ctr.columns)[:40])
num = [c for c in ["p", "W", "L", "W_L", "p_be", "mean", "gross_mean", "gross_p", "gross_W",
                   "gross_L", "gross_W_L", "gross_p_be", "n"] if c in ctr.columns]
print(ctr[num].describe(percentiles=[0.5]).round(4).to_string())
sym = [c for c in ["symbol", "instrument"] if c in ctr.columns]
if sym:
    print("\nper instrument:")
    print(ctr.groupby(sym[0])[num].median().round(4).to_string())

print("\n" + "=" * 100); print("IN-5 — CI COVERAGE AUDIT (which statistics carry a CI, where)"); print("=" * 100)
s = m[m.gross_p.notna()]
for c in ["gross_mean_ci_low", "gross_median_ci_low", "gross_trimmed_mean_ci_low",
          "net_mean_ci_low", "net_median_ci_low", "net_trimmed_mean_ci_low",
          "gross_p_ci_low", "gross_W_ci_low", "gross_L_ci_low", "gross_W_L_ci_low",
          "gross_edge_ci_low"]:
    if c in s:
        print(f"  {c:32s} present on {s[c].notna().sum():6d} / {len(s)} signed cells "
              f"({s[c].notna().mean():.3f})")
print("\n  levers_exhausted cells:", int((m.levers_exhausted == True).sum()),
      "  at_parent_target_precision & signed:", int(((m.at_parent_target_precision == True) & m.gross_p.notna()).sum()))
pw = s[s.at_parent_target_precision == True]
print("  among POWERED signed cells, median CI coverage:")
for c in ["gross_median_ci_low", "gross_trimmed_mean_ci_low"]:
    print(f"    {c}: {pw[c].notna().mean():.4f}")
# does the median/trimmed-mean disagree with the mean in sign?
d = pw[pw.gross_median.notna()]
print("\n  MEAN vs MEDIAN vs TRIMMED-MEAN sign agreement on powered cells (n=%d):" % len(d))
print("    sign(mean)==sign(median):        %.4f" % (np.sign(d.gross_mean) == np.sign(d.gross_median)).mean())
print("    sign(mean)==sign(trimmed_mean):  %.4f" % (np.sign(d.gross_mean) == np.sign(d.gross_trimmed_mean_10)).mean())
print("    median gross mean %.3f | median gross median %.3f | median gross trimmed %.3f bps"
      % (d.gross_mean.median(), d.gross_median.median(), d.gross_trimmed_mean_10.median()))
print("    median NET mean %.3f | median NET median %.3f | median NET trimmed %.3f bps"
      % (d.net_mean.median(), d.net_median.median(), d.net_trimmed_mean_10.median()))
