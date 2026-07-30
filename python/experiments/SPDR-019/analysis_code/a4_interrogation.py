"""A4 — census, per-stratum, MOD-vs-UNMOD, controls, selection check, trigger."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np, polars as pl

RES = Path(__file__).resolve().parents[1] / "results"
NS = 1_000_000_000
pl.Config.set_tbl_rows(60); pl.Config.set_tbl_width_chars(260)

met = pl.read_parquet(RES / "metrics_by_cell.parquet")
ld = pl.read_parquet(RES / "layer_deltas.parquet")
ep = pl.scan_parquet(RES / "episodes.parquet")
RUNGS = [0.02, 0.03, 0.05, 0.075, 0.10, 0.15]

print("=" * 96); print("1. REALISED HOLDING SPAN vs THE 1-DAY MINIMUM BLOCK (dependence caveat)"); print("=" * 96)
sp = (ep.with_columns(((pl.col("exit_ts") - pl.col("fill_ts")) / (3600 * NS)).alias("h"))
      .group_by("clock").agg(pl.len().alias("n"),
                             (pl.col("h") > 24).mean().alias("frac_gt_24h"),
                             (pl.col("h") > 72).mean().alias("frac_gt_72h"),
                             pl.col("h").quantile(0.99).alias("p99_h"),
                             pl.col("h").max().alias("max_h")).collect())
print(sp)

print("\n" + "=" * 96); print("2. ci_low > 0 CENSUS vs THE PREDECLARED FALSE-POSITIVE EXPECTATION (2.5%)"); print("=" * 96)
def census(df, lbl, lo="ci_low"):
    tot = df.filter(pl.col(lo).is_not_null()).height
    pos = df.filter(pl.col(lo) > 0).height
    neg = df.filter(pl.col("ci_high") < 0).height
    print(f"{lbl:<62} rows={tot:>6}  ci_low>0={pos:>5} (exp {0.025*tot:6.1f})  ci_high<0={neg:>5}")
    return tot, pos, neg

FIX = (pl.col("scope") == "POOLED") & (pl.col("band") == "TRAIN")
PS = (pl.col("scope") != "POOLED") & (pl.col("band") == "TRAIN")
census(met.filter(FIX), "ABS log R | pooled, TRAIN, both clocks (the 198-cell tier)")
for c in ("M15", "H1"):
    census(met.filter(FIX & (pl.col("clock") == c)), f"ABS log R | pooled TRAIN {c}")
    census(ld.filter((pl.col("scope") == "POOLED") & (pl.col("clock") == c)), f"D log R  | pooled TRAIN {c}")
census(met.filter(PS), "ABS log R | PER-SYMBOL, TRAIN (disclosure tier)")
for c in ("M15", "H1"):
    census(met.filter(PS & (pl.col("clock") == c)), f"ABS log R | per-symbol TRAIN {c}")
    census(ld.filter((pl.col("scope") != "POOLED") & (pl.col("clock") == c)), f"D log R  | per-symbol TRAIN {c}")
census(met, "ABS log R | ALL rows, all bands, all scopes")
census(ld, "D log R  | ALL rows")

print("\n--- resolution distribution behind those aggregates (design SS13 mandatory) ---")
for lbl, df in (("pooled TRAIN M15 abs", met.filter(FIX & (pl.col("clock") == "M15"))),
                ("pooled TRAIN H1 abs", met.filter(FIX & (pl.col("clock") == "H1"))),
                ("pooled TRAIN M15 delta", ld.filter((pl.col("scope") == "POOLED") & (pl.col("clock") == "M15"))),
                ("pooled TRAIN H1 delta", ld.filter((pl.col("scope") == "POOLED") & (pl.col("clock") == "H1"))),
                ("per-symbol TRAIN abs", met.filter(PS))):
    sub = df.filter(pl.col("block_mde").is_not_null())
    line = [f"{lbl:<24} n={sub.height:<6} median block_mde={sub['block_mde'].median():.4f}"]
    for r in RUNGS:
        line.append(f"<{r}:{sub.filter(pl.col('block_mde') < r).height}")
    if "mde50" in sub.columns:
        line.append(f"median mde50={sub['mde50'].median():.4f}")
    print("  " + "  ".join(line))

print("\n" + "=" * 96); print("3. MOD vs UNMOD — does the volatility FORECAST add over a constant-width comparator?"); print("=" * 96)
pairs = [("L4_TARGET_A1", ), ("L4_TARGET_A2", ), ("L4_TARGET_A3", ), ("L4_TRAIL_B1", ), ("L4_TRAIL_B2", ),
         ("L4_HOLD_1H", ), ("L4_HOLD_4H", ), ("L4_HOLD_12H", ), ("L4_HOLD_20H", )]
rows = []
for (base,) in pairs:
    for clk in ("M15", "H1"):
        for dl in (0.25, 0.5, 1.0):
            g = ld.filter((pl.col("clock") == clk) & (pl.col("scope") == "POOLED") & (pl.col("delta") == dl)
                          & pl.col("variant_id").is_in([f"{base}_MOD", f"{base}_UNMOD"]))
            if g.height != 2:
                continue
            mo = g.filter(pl.col("variant_id").str.ends_with("_MOD")).row(0, named=True)
            un = g.filter(pl.col("variant_id").str.ends_with("_UNMOD")).row(0, named=True)
            rows.append({"device": base, "clock": clk, "delta": dl,
                         "d_MOD": mo["delta_log_R"], "d_UNMOD": un["delta_log_R"],
                         "MOD_minus_UNMOD": mo["delta_log_R"] - un["delta_log_R"],
                         "MOD_ci": f"[{mo['ci_low']:.4f},{mo['ci_high']:.4f}]",
                         "UNMOD_ci": f"[{un['ci_low']:.4f},{un['ci_high']:.4f}]",
                         "MOD_mde": mo["block_mde"]})
mu = pl.DataFrame(rows)
print(mu.sort(["clock", "device", "delta"]))
print("\nsign of (MOD - UNMOD) by clock:")
print(mu.group_by("clock").agg(pl.len(), (pl.col("MOD_minus_UNMOD") > 0).sum().alias("MOD_better"),
                               pl.col("MOD_minus_UNMOD").median().alias("median_gap"),
                               pl.col("MOD_mde").median().alias("median_mde")))

print("\n" + "=" * 96); print("4. L1 DOSE-RESPONSE (d>=5 -> d>=7 -> d>=9): monotone in the forecast?"); print("=" * 96)
l1 = (ld.filter((pl.col("scope") == "POOLED") & pl.col("variant_id").str.starts_with("L1_SHAT_DECILE"))
      .select(["clock", "delta", "variant_id", "delta_log_R", "ci_low", "ci_high", "block_mde"])
      .sort(["clock", "delta", "variant_id"]))
print(l1)

print("\n" + "=" * 96); print("5. THE L2 INTERACTION TERM (prediction 4) + the flagged 1000BONKUSDT rows"); print("=" * 96)
it = met.filter(pl.col("variant_id") == "L2_INTERACTION_HMM_X_K12")
print(it.filter(pl.col("scope") == "POOLED").select(
    ["clock", "band", "delta", "n", "n_dates", "log_R", "ci_low", "ci_high", "ci_width", "block_mde"]).sort(["clock", "band", "delta"]))
print("\ninteraction rows with ci_low>0 (ANY scope/band):")
print(it.filter(pl.col("ci_low") > 0).select(["clock", "band", "delta", "scope", "n", "n_dates", "log_R", "ci_low", "ci_high"]))
print("\nCAUTION (QA R12-01) — 1000BONKUSDT / H1 / all three deltas, interaction rows:")
print(it.filter((pl.col("scope") == "1000BONKUSDT") & (pl.col("clock") == "H1")).select(
    ["band", "delta", "n", "n_dates", "log_R", "ci_low", "ci_high"]).sort(["band", "delta"]))
print("\n  their JOINT input arm (L2_JOINT_HMM_HIGH_AND_K12_HIGH / 1000BONKUSDT / H1):")
print(met.filter((pl.col("variant_id") == "L2_JOINT_HMM_HIGH_AND_K12_HIGH") & (pl.col("scope") == "1000BONKUSDT")
                 & (pl.col("clock") == "H1")).select(
    ["band", "delta", "n", "n_dates", "p", "W", "L", "log_R", "ci_low", "ci_high", "ci_absent_reason"]).sort(["band", "delta"]))

print("\n" + "=" * 96); print("6. PER-SYMBOL HETEROGENEITY behind the pooled primary read"); print("=" * 96)
print("pooled I^2 distribution (TRAIN, cells with a CI):")
for c in ("M15", "H1"):
    s = met.filter(FIX & (pl.col("clock") == c) & pl.col("i_squared").is_not_null())
    print(f"  {c}: n={s.height} I2 median={s['i_squared'].median():.3f} q75={s['i_squared'].quantile(0.75):.3f} max={s['i_squared'].max():.3f} frac>0.5={(s['i_squared']>0.5).mean():.3f}")
print("\npooled_status values emitted:", met["pooled_status"].unique().to_list())
print("\nper-symbol log R spread, L0 TRAIN:")
ps = (met.filter((pl.col("variant_id") == "L0_BASELINE") & (pl.col("band") == "TRAIN") & (pl.col("scope") != "POOLED"))
      .select(["clock", "delta", "scope", "n", "log_R", "ci_low", "ci_high", "block_mde"]))
print(ps.group_by(["clock", "delta"]).agg(
    pl.len().alias("k"), pl.col("log_R").min().alias("min"), pl.col("log_R").median().alias("med"),
    pl.col("log_R").max().alias("max"), (pl.col("ci_low") > 0).sum().alias("above"),
    (pl.col("ci_high") < 0).sum().alias("below"), pl.col("block_mde").median().alias("med_mde")
).sort(["clock", "delta"]))

print("\n" + "=" * 96); print("7. PREDECLARED vs REALISED (calibration audit — consumed by nothing)"); print("=" * 96)
lad = pl.read_parquet(RES / "resolution_ladder.parquet")
print("prior_status values:", lad["prior_status"].unique().to_list())
print("expected_n non-null:", lad.filter(pl.col("expected_n").is_not_null()).height,
      "| expected_mde50 non-null:", lad.filter(pl.col("expected_mde50").is_not_null()).height)
print("=> the signed discrepancy distribution is EMPTY BY CONSTRUCTION: every prior is an explicit UNKNOWN.")
