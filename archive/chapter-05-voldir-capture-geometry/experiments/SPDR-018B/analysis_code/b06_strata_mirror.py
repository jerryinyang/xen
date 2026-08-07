"""Per-stratum (p,W,L) tables, the W/L mirror test, the counter-outcome, and analyst artifacts."""
import numpy as np
import pandas as pd

R = "python/experiments/SPDR-018B/results/"
m = pd.read_parquet(R + "metrics_by_cell.parquet")
tgt = m["at_parent_target_precision"].fillna(False).astype(bool)
signed = m["gross_p"].notna()
pw = m[signed & tgt].copy()

GC = ["gross_p", "gross_W", "gross_L", "gross_W_L", "gross_p_be", "gross_p_be_net", "gross_edge",
      "gross_mean", "gross_median", "gross_trimmed_mean_10", "net_mean", "gross_cost_bps",
      "gross_n", "gross_n_dates", "gross_block_mde_mean_bps", "gross_mean_ci_low", "gross_mean_ci_high"]


def tab(df, by):
    def f(x):
        return pd.Series({
            "n_cells": len(x), "med_n": x.gross_n.median(),
            "p": x.gross_p.median(), "W": x.gross_W.median(), "L": x.gross_L.median(),
            "W_L": x.gross_W_L.median(), "p_be": x.gross_p_be.median(),
            "p_be_net": x.gross_p_be_net.median(), "edge": x.gross_edge.median(),
            "gross_bps": x.gross_mean.median(), "gross_median_bps": x.gross_median.median(),
            "gross_trim10_bps": x.gross_trimmed_mean_10.median(),
            "net_bps": x.net_mean.median(), "cost_bps": x.gross_cost_bps.median(),
            "share_clear_gross_be": (x.gross_p > x.gross_p_be).mean(),
            "share_clear_net_be": (x.gross_p > x.gross_p_be_net).mean(),
            "n_ci_excl_zero_pos": int((x.gross_mean_ci_low > 0).sum()),
            "n_ci_excl_zero_neg": int((x.gross_mean_ci_high < 0).sum()),
            "rate_term": (x.gross_p_be - x.gross_p).median(),
            "cost_term": (x.gross_p_be_net - x.gross_p_be).median(),
        })
    return df.groupby(by, dropna=False).apply(f, include_groups=False).round(4)


print("=== PER-STRATUM: the 315 powered signed cells ===")
outs = {}
for by in ["arm", "band", "clock", "symbol", "residue_item", "exit_mode", "source", "event_type"]:
    if by in pw.columns and pw[by].notna().any():
        t = tab(pw, by)
        outs[by] = t
        print(f"\n--- by {by} ---")
        print(t.to_string())

print("\n--- by arm x band ---")
print(tab(pw, ["arm", "band"]).to_string())
print("\n--- by arm x symbol ---")
print(tab(pw, ["arm", "symbol"]).to_string())

print("\n=== identity term decomposition, pooled disclosure ===")
print("  rate term median (p_be - p): %.5f   cost term median (p_be_net - p_be): %.5f" %
      ((pw.gross_p_be - pw.gross_p).median(), (pw.gross_p_be_net - pw.gross_p_be).median()))
for arm in ["B", "C"]:
    d = pw[pw.arm == arm]
    rt = (d.gross_p_be - d.gross_p).median(); ct = (d.gross_p_be_net - d.gross_p_be).median()
    print(f"  arm {arm}: rate {rt:+.5f} cost {ct:+.5f} -> cost share of gap {ct/(rt+ct):.4f}")

print("\n=== best / worst cells among the 315 (gross) ===")
cols = ["arm", "residue_item", "symbol", "band", "clock", "exit_mode", "gross_n", "gross_p", "gross_p_be",
        "gross_W", "gross_L", "gross_W_L", "gross_mean", "gross_mean_ci_low", "gross_mean_ci_high",
        "gross_cost_bps", "gross_p_be_net", "gross_edge"]
print(pw.nlargest(6, "gross_mean")[cols].round(3).to_string())
print(pw.nsmallest(4, "gross_mean")[cols].round(3).to_string())
print("\n  max gross mean among the 315: %.4f bps; its own cost %.3f bps" %
      (pw.gross_mean.max(), pw.loc[pw.gross_mean.idxmax(), "gross_cost_bps"]))
print("  cost that would be needed for ANY of the 315 to clear net: < %.4f bps (i.e. %.1f%% of the charge)" %
      (pw.gross_mean.max(), 100 * pw.gross_mean.max() / pw.gross_cost_bps.median()))
print("  cells with gross_mean > 0: %d/%d ; with gross CI_low > 0: %d ; CI_high < 0: %d" %
      ((pw.gross_mean > 0).sum(), len(pw), (pw.gross_mean_ci_low > 0).sum(), (pw.gross_mean_ci_high < 0).sum()))
print("  cells with net CI_low > 0:", int((pw.net_mean_ci_low > 0).sum()),
      " gross_edge CI_low > 0:", int((pw.gross_edge_ci_low > 0).sum()))

print("\n=== W/L MIRROR TEST ===")
def mirror(df, label):
    d = df[(df.gross_p > 0) & (df.gross_p < 1) & (df.gross_W_L > 0)]
    y = np.log(d.gross_W_L); x = np.log((1 - d.gross_p) / d.gross_p)
    if len(d) < 8:
        return
    b, a = np.polyfit(x, y, 1)
    r = np.corrcoef(x, y)[0, 1]
    logR = np.log(d.gross_p * d.gross_W / ((1 - d.gross_p) * d.gross_L))
    print(f"  {label:34s} n={len(d):5d} slope={b:+.4f} intercept={a:+.4f} r={r:+.4f} R2={r**2:.4f} "
          f"sd(logWL)={y.std():.4f} sd(mirror)={x.std():.4f} sd(logR)={logR.std():.4f} "
          f"median logR={logR.median():+.4f} free_share={logR.std()/y.std():.3f}")

mirror(pw, "315 powered")
for arm in ["B", "C"]:
    mirror(pw[pw.arm == arm], f"powered arm {arm}")
mirror(m[signed], "all 6,156 signed")
b = m[signed & (m.arm == "B")]
for em in sorted(b.exit_mode.dropna().unique()):
    mirror(b[b.exit_mode == em], f"arm B {em} (all cells)")

print("\n=== arm-B movability table (all 630 arm-B signed cells) ===")
t = b.groupby("exit_mode").apply(lambda x: pd.Series({
    "n": len(x), "p": x.gross_p.median(), "W_L": x.gross_W_L.median(),
    "mirror": ((1 - x.gross_p) / x.gross_p).median(),
    "median_logR": np.log(x.gross_p * x.gross_W / ((1 - x.gross_p) * x.gross_L)).median(),
    "gross_mean_median": x.gross_mean.median(), "gross_mean_mean": x.gross_mean.mean(),
    "W": x.gross_W.median(), "L": x.gross_L.median(),
}), include_groups=False).round(4)
print(t.to_string())
print("  W/L movement factor:", round(t.W_L.max() / t.W_L.min(), 1))

print("\n=== per-cell W/L CI vs the driftless mirror ===")
d = pw[pw.gross_W_L_ci_low.notna()]
mir = (1 - d.gross_p) / d.gross_p
excl = (mir < d.gross_W_L_ci_low) | (mir > d.gross_W_L_ci_high)
print(f"  cells with a W/L CI: {len(d)}/{len(pw)}; CI EXCLUDES the mirror in {int(excl.sum())} "
      f"({excl.mean()*100:.1f}%); cannot be distinguished in {int((~excl).sum())} ({(~excl).mean()*100:.1f}%)")

print("\n=== CI coverage on the three point statistics (315 powered) ===")
for c in ["gross_mean", "gross_p", "gross_W", "gross_L", "gross_W_L", "gross_edge",
          "gross_median", "gross_trimmed_mean_10", "net_median", "net_trimmed_mean_10"]:
    lo = c + "_ci_low"
    if lo in pw.columns:
        print(f"  {c:24s} CI present on {pw[lo].notna().sum():4d}/{len(pw)}")
    else:
        print(f"  {c:24s} NO CI COLUMN EMITTED")
print("  medians on the 315: mean %.3f | median %.3f | trimmed10 %.3f (gross bps)" %
      (pw.gross_mean.median(), pw.gross_median.median(), pw.gross_trimmed_mean_10.median()))
print("  sign agreement mean-vs-median %.3f; mean-vs-trimmed %.3f" %
      ((np.sign(pw.gross_mean) == np.sign(pw.gross_median)).mean(),
       (np.sign(pw.gross_mean) == np.sign(pw.gross_trimmed_mean_10)).mean()))

# ---------------- artifacts ----------------
keep = [c for c in ["arm", "arm_name", "residue_item", "symbol", "band", "clock", "exit_mode", "source",
                    "event_type", "conditioner", "conditioner_value", "z", "H", "h", "policy", "basis",
                    "at_parent_target_precision", "at_parent_target_precision_absolute__SUPERSEDED",
                    "target_mde_bps_sigma_scaled", "target_mde_bps_absolute__SUPERSEDED", "precision_basis",
                    "band_label_mean", "band_label_edge", "levers_exhausted"] + GC +
        ["gross_edge_ci_low", "gross_edge_ci_high", "gross_W_L_ci_low", "gross_W_L_ci_high",
         "net_mean_ci_low", "net_mean_ci_high", "net_median", "net_trimmed_mean_10"] if c in m.columns]
art = m.loc[signed, keep].copy()
art["mirror_WL"] = (1 - art.gross_p) / art.gross_p
art["log_R"] = np.log(art.gross_p * art.gross_W / ((1 - art.gross_p) * art.gross_L))
art["clears_gross_be"] = art.gross_p > art.gross_p_be
art["clears_net_be"] = art.gross_p > art.gross_p_be_net
art["payoff_scale_bps"] = art.gross_W + art.gross_L
art.to_parquet(R + "analyst_per_cell_magnitudes.parquet", index=False)
print("\nwrote analyst_per_cell_magnitudes.parquet rows=", len(art))

rows = []
for name, t in outs.items():
    t2 = t.reset_index().rename(columns={name: "level"})
    t2.insert(0, "stratum", name)
    rows.append(t2)
for nm, keys in [("arm_x_band", ["arm", "band"]), ("arm_x_symbol", ["arm", "symbol"]),
                 ("arm_x_clock", ["arm", "clock"])]:
    t2 = tab(pw, keys).reset_index()
    t2["level"] = t2[keys].astype(str).agg(" | ".join, axis=1)
    t2 = t2.drop(columns=keys); t2.insert(0, "stratum", nm)
    rows.append(t2)
pd.concat(rows, ignore_index=True).to_csv(R + "analyst_stratum_tables.csv", index=False)
print("wrote analyst_stratum_tables.csv views=", len(rows))
