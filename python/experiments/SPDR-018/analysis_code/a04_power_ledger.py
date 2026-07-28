"""Q1 — per-017-item power / resolvability ledger. Plus C7, C8, M-2, B3 reconciliation."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen")
RES = ROOT / "python/experiments/SPDR-018/results"
pd.set_option("display.width", 260); pd.set_option("display.max_columns", 90); pd.set_option("display.max_rows", 500)

m = pd.read_parquet(RES / "metrics_by_cell.parquet")

# expand multi-item tags
recs = []
for i, r in m.iterrows():
    for tag in str(r["residue_item"]).split(","):
        recs.append((i, tag.strip()))
tagmap = pd.DataFrame(recs, columns=["idx", "item"])
mm = m.reset_index().rename(columns={"index": "idx"})
X = tagmap.merge(mm, on="idx")

print("=" * 100)
print("Q1 — POWER / RESOLVABILITY LEDGER PER 017 OPEN ITEM")
print("=" * 100)
led = X.groupby(["arm", "item"]).agg(
    cells=("idx", "size"),
    at_target=("at_parent_target_precision", lambda s: int((s == True).sum())),
    not_res=("levers_exhausted", lambda s: int((s == True).sum())),
    med_n=("n", "median"),
    med_n_dates=("n_dates", "median"),
    med_block_mde=("block_mde", "median"),
    med_target_mde=("target_mde", "median"),
)
led["frac_at_target"] = (led["at_target"] / led["cells"]).round(4)
led["mde_multiple_short"] = (led["med_block_mde"] / led["med_target_mde"]).round(2)
print(led.round(4).to_string())

print("\n--- multiple-short distribution among NOT_RESOLVABLE cells (levers_exhausted) ---")
nr = X[X["levers_exhausted"] == True].copy()
nr["mult"] = nr["block_mde"] / nr["target_mde"]
print("n NOT_RESOLVABLE (expanded tags):", len(nr), " unique cells:", nr["idx"].nunique())
print(nr["mult"].describe(percentiles=[0.5, 0.9, 0.99]).round(2).to_string())
print("\nby item:")
q = nr.groupby(["arm", "item"]).agg(n=("mult", "size"), med_mult=("mult", "median"),
                                    p90_mult=("mult", lambda s: s.quantile(0.9)),
                                    med_n=("n", "median"))
# required n = realised n * mult^2  (MDE ~ 1/sqrt(n))
nr["req_n"] = nr["n"] * nr["mult"] ** 2
q["med_required_n"] = nr.groupby(["arm", "item"])["req_n"].median()
print(q.round(2).to_string())

nrj = json.loads((RES / "not_resolvable.json").read_text())
cells = nrj["cells"]
print("\nnot_resolvable.json: n cells =", len(cells))
print("screen.md claim: 3,559 cells; median shortfall 7.9x; p90 27.3x")
mult = pd.Series([c.get("multiple_short") for c in cells], dtype=float)
print("analyst re-derived from json: median %.2f  p90 %.2f" % (mult.median(), mult.quantile(0.9)))
print("json concentration by item:")
print(pd.Series([c.get("residue_item") for c in cells]).value_counts().to_string())

print("\n" + "=" * 100)
print("C7 — DESIGN -> CONFIRM SIGN FLIP")
print("=" * 100)
c7 = m[(m["arm"] == "C") & (m["basis"] == "sign_flip")].copy()
print("pairs:", len(c7), "(screen: 2,714)")
print("sign_flipped True frac: %.4f  (screen 0.441)" % (c7["sign_flipped"] == True).mean())
fl = c7[c7["sign_flipped"] == True]
print("of flipped, band CIs overlap frac: %.4f  (screen 0.918)" % (fl["band_cis_overlap"] == True).mean())
print("of NON-flipped, band CIs overlap frac: %.4f" % (c7[c7["sign_flipped"] == False]["band_cis_overlap"] == True).mean())
# is the flip rate distinguishable from the coin-flip a pure-noise pair would give?
n = len(c7); k = int((c7["sign_flipped"] == True).sum())
se = np.sqrt(0.25 / n)
print(f"observed flip rate {k}/{n} = {k / n:.4f};  independent-pure-noise expectation 0.50, "
      f"binomial SE {se:.4f}, z = {(k / n - 0.5) / se:+.2f}")
print("  NOTE: the 2,714 pairs are NOT independent (shared symbols/events); the binomial SE is a")
print("  LOWER bound on uncertainty, so the true |z| is smaller than shown.")
# magnitude of the flip vs the CI width
c7["dgap"] = c7["confirm_mean_bps"] - c7["design_mean_bps"]
c7["pooled_mde"] = np.sqrt(c7["design_block_mde_bps"] ** 2 + c7["confirm_block_mde_bps"] ** 2)
print("\nDESIGN vs CONFIRM band means (bps):")
print(c7[["design_mean_bps", "confirm_mean_bps", "dgap", "design_block_mde_bps",
          "confirm_block_mde_bps", "pooled_mde", "design_n", "confirm_n"]].describe(
    percentiles=[0.05, 0.5, 0.95]).round(2).to_string())
print("\nfrac of ALL pairs where |CONFIRM-DESIGN| exceeds the two-band pooled block MDE: %.4f"
      % (c7["dgap"].abs() > c7["pooled_mde"]).mean())
print("frac of FLIPPED pairs where the change exceeds the pooled block MDE: %.4f"
      % (fl["confirm_mean_bps"].sub(fl["design_mean_bps"]).abs() >
         np.sqrt(fl["design_block_mde_bps"] ** 2 + fl["confirm_block_mde_bps"] ** 2)).mean())
print("pooled DESIGN mean %.3f bps ; pooled CONFIRM mean %.3f bps ; medians %.3f / %.3f"
      % (c7["design_mean_bps"].mean(), c7["confirm_mean_bps"].mean(),
         c7["design_mean_bps"].median(), c7["confirm_mean_bps"].median()))

print("\n" + "=" * 100)
print("C8 — RATE LEAN, two weightings")
print("=" * 100)
c8 = m[(m["arm"] == "C") & (m["basis"] == "rate_lean")]
print("cells:", len(c8))
print(c8[["p_momo_pooled_row_weighted", "p_momo_mean_of_per_symbol", "n_symbols_momo_leaning",
          "n_symbols_mr_leaning", "n"]].describe(percentiles=[0.5]).round(4).to_string())
print("median row-weighted %.4f (screen 0.4676) ; median symbol-weighted %.4f (screen 0.4699)"
      % (c8["p_momo_pooled_row_weighted"].median(), c8["p_momo_mean_of_per_symbol"].median()))

print("\n" + "=" * 100)
print("M-2 — WALL-CLOCK SPAN vs NOMINAL h")
print("=" * 100)
sp = m[m["span_nominal_span_hours"].notna()]
print("cells carrying a horizon:", len(sp), "(screen 18,990)")
print("median exact-span fraction: %.4f  (screen 0.906)" % sp["span_exact_span_frac"].median())
print("frac of those cells with ANY row exceeding nominal h: %.4f  (screen 0.782)"
      % (sp["span_frac_exceeding_nominal"] > 0).mean())
print("\nspan_frac_exceeding_nominal distribution:")
print(sp["span_frac_exceeding_nominal"].describe(percentiles=[0.5, 0.75, 0.9, 0.95, 0.99]).round(4).to_string())
print("\nspan hours vs nominal (ratio median/p95/max):")
sp2 = sp.assign(rmed=sp["span_span_hours_median"] / sp["span_nominal_span_hours"],
                rp95=sp["span_span_hours_p95"] / sp["span_nominal_span_hours"],
                rmax=sp["span_span_hours_max"] / sp["span_nominal_span_hours"])
print(sp2[["rmed", "rp95", "rmax"]].describe(percentiles=[0.5, 0.9, 0.99]).round(3).to_string())
# does the horizon read change on the exact-span-clean cells?
pw = sp[(sp["at_parent_target_precision"] == True) & sp["gross_p"].notna()]
print("\npowered horizon-carrying cells:", len(pw))
for lo, hi, lab in [(0.0, 0.9, "exact-span frac < 0.90"), (0.9, 0.99, "0.90-0.99"), (0.99, 1.01, ">= 0.99 (clean)")]:
    s = pw[(pw["span_exact_span_frac"] >= lo) & (pw["span_exact_span_frac"] < hi)]
    if len(s):
        print("  %-24s n=%4d  med gross_mean %+7.3f bps  med p %.4f  med W/L %.3f  med gross_edge %+.4f"
              % (lab, len(s), s["gross_mean"].median(), s["gross_p"].median(),
                 s["gross_W_L"].median(), s["gross_edge"].median()))

print("\n" + "=" * 100)
print("B3 RECONCILIATION — the design's '125 positive-mean cells'")
print("=" * 100)
B = m[m["arm"] == "B"]
tag = X[(X["arm"] == "B") & (X["item"] == "B3")]
print("cells tagged B3 by the screen:", len(tag), "(screen: 830 superset)")
print("\nAnalyst count of arm-B cells with a POSITIVE mean, by slice:")
for lab, s in [("all arm-B signed cells", B[B["gross_p"].notna()]),
               ("DESIGN band", B[(B["band"] == "DESIGN") & B["gross_p"].notna()]),
               ("CONFIRM band", B[(B["band"] == "CONFIRM") & B["gross_p"].notna()]),
               ("TRAIN band", B[(B["band"] == "TRAIN") & B["gross_p"].notna()]),
               ("DESIGN x H1", B[(B["band"] == "DESIGN") & (B["clock"] == "H1") & B["gross_p"].notna()]),
               ("H1 both bands", B[(B["clock"] == "H1") & B["band"].isin(["DESIGN", "CONFIRM"]) & B["gross_p"].notna()]),
               ("DESIGN x per_symbol", B[(B["band"] == "DESIGN") & (B["basis"] == "per_symbol") & B["gross_p"].notna()]),
               ]:
    print("  %-24s  n=%5d  gross_mean>0: %5d   net_mean>0: %4d" % (
        lab, len(s), int((s["gross_mean"] > 0).sum()), int((s["net_mean"] > 0).sum())))
print("\nnet_mean>0 counts by (band x clock x basis), looking for anything near 125:")
g = B[B["gross_p"].notna()].groupby(["band", "clock", "basis"]).agg(
    n=("gross_mean", "size"), pos_gross=("gross_mean", lambda s: int((s > 0).sum())),
    pos_net=("net_mean", lambda s: int((s > 0).sum())))
print(g.to_string())
