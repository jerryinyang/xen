"""Coverage gaps C7/C8/B3 (native), arms A and D item reads, counter-outcome flip test."""
import numpy as np
import pandas as pd

R = "python/experiments/SPDR-018B/results/"
m = pd.read_parquet(R + "metrics_by_cell.parquet")
tgt = m["at_parent_target_precision"].fillna(False).astype(bool)
signed = m["gross_p"].notna()
pd.set_option("display.width", 260)

print("=== coverage_gap_C7_C8.parquet ===")
c = pd.read_parquet(R + "coverage_gap_C7_C8.parquet")
print(" shape", c.shape); print(" cols", list(c.columns))
print(c.head(3).T.to_string()[:2500])
if "item" in c.columns:
    print(" item counts:", c["item"].value_counts().to_dict())
for cand in ["gap", "kind", "which", "residue_item", "C7", "C8"]:
    if cand in c.columns:
        print(f" {cand}:", c[cand].value_counts(dropna=False).head(6).to_dict())

print("\n=== coverage_gap_B3.parquet ===")
b3 = pd.read_parquet(R + "coverage_gap_B3.parquet")
print(" shape", b3.shape); print(" cols", list(b3.columns)[:40])
print(b3.head(2).T.to_string()[:2500])

print("\n=== arm A items ===")
a = m[m.arm == "A"]
print(" cells", len(a), " residue items:", a.residue_item.value_counts().to_dict())
print(" metric col:", a.metric.dropna().value_counts().head(10).to_dict() if "metric" in a else "n/a")
for it in sorted(a.residue_item.dropna().unique()):
    d = a[a.residue_item == it]
    print(f"\n -- {it}: n={len(d)} at_target={int(tgt[d.index].sum())}")
    for col in ["gap_bps", "gap_ci_low", "gap_ci_high", "rank_ic", "ic_ci_low", "incremental_r2",
                "thirds_populated", "thirds_sign_agree", "clause_satisfiable", "coverage_n_dates",
                "n_dates_short_of_225", "value", "mean_next_abs_oo_HIGH", "mean_next_abs_oo_LOW"]:
        if col in d and d[col].notna().any():
            v = d[col]
            if v.dtype == bool or v.dtype == object:
                print(f"      {col}: {v.dropna().value_counts().to_dict()}")
            else:
                print(f"      {col}: median {v.median():.4f} [p5 {v.quantile(.05):.4f}, p95 {v.quantile(.95):.4f}] n={v.notna().sum()}")
    if "gap_ci_low" in d and d.gap_ci_low.notna().any():
        print(f"      share CI-excl-zero positive: {(d.gap_ci_low>0).mean():.3f}")
    print("      band_label_gap:", d.band_label_gap.dropna().value_counts().to_dict() if "band_label_gap" in d else "")
    print("      band_label_ic :", d.band_label_ic.dropna().value_counts().to_dict() if "band_label_ic" in d else "")

print("\n=== arm D items ===")
dd = m[m.arm == "D"]
print(" cells", len(dd), " items:", dd.residue_item.value_counts().to_dict())
for it in sorted(dd.residue_item.dropna().unique()):
    d = dd[dd.residue_item == it]
    print(f"\n -- {it}: n={len(d)} at_target={int(tgt[d.index].sum())}")
    for col in ["n_trans", "min_trans_rule", "shortfall_n_trans", "mae", "e_run_pred", "hit_rate",
                "base_rate_high", "delta_brier_vs_pers", "delta_brier_ci_lo", "delta_brier_ci_hi",
                "p_stay", "accuracy", "brier", "horizon_k", "model"]:
        if col in d and d[col].notna().any():
            v = d[col]
            if v.dtype == object or str(v.dtype) in ("str","string","string[pyarrow]"):
                print(f"      {col}: {v.dropna().value_counts().head(6).to_dict()}")
            else:
                print(f"      {col}: median {v.median():.4f} [p5 {v.quantile(.05):.4f}, p95 {v.quantile(.95):.4f}] n={v.notna().sum()}")
    print("      band_label_mean:", d.band_label_mean.dropna().value_counts().to_dict())

print("\n=== D3/D4/C7/C8/C9 presence in the cell grid ===")
for it in ["D3", "D4", "C7", "C8", "C9", "B3"]:
    n = int(m.residue_item.astype(str).str.contains(it, na=False).sum())
    print(f"  residue_item containing {it}: {n} cells")

print("\n=== counter-outcome: powered cells whose gross CI excludes zero ===")
pw = m[signed & tgt]
neg = pw[pw.gross_mean_ci_high < 0]
pos = pw[pw.gross_mean_ci_low > 0]
print(f"  negative: {len(neg)}  positive: {len(pos)}  of {len(pw)}")
cols = ["arm", "residue_item", "symbol", "band", "clock", "exit_mode", "gross_n", "gross_p", "gross_W",
        "gross_L", "gross_mean", "gross_mean_ci_low", "gross_mean_ci_high", "gross_cost_bps"]
print(neg[cols].round(3).to_string())
print("\n  if the side were flipped on those cells: best flipped gross = %.3f bps vs its cost %.3f" %
      (-neg.gross_mean.min(), neg.loc[neg.gross_mean.idxmin(), "gross_cost_bps"]))
print("  flipped cells clearing their own vol-scaled cost:",
      int((-neg.gross_mean > neg.gross_cost_bps).sum()), "/", len(neg))
print("  median flipped gross: %.3f; median flipped net: %.3f" %
      ((-neg.gross_mean).median(), (-neg.gross_mean - neg.gross_cost_bps).median()))
print("  positive-tail cells:")
print(pos[cols].round(3).to_string())
print("\n  null expectation at nominal 95%%: ~%.0f per tail on %d cells" % (0.025 * len(pw), len(pw)))
