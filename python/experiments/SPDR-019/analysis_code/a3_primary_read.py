"""A3 — the primary read.

M15, full TRAIN, pooled across symbols, on Delta log R vs L0 (design SS8.1 / AMENDMENT-9).
H1 = co-report / clock-effect check, where absolute log R is also interpretable.
Clocks NEVER pooled. Bands are LABELS, never gates (AMENDMENT-C7).
"""
from __future__ import annotations
from pathlib import Path
import polars as pl

RES = Path(__file__).resolve().parents[1] / "results"
pl.Config.set_tbl_rows(80); pl.Config.set_tbl_width_chars(250); pl.Config.set_fmt_float("full")

met = pl.read_parquet(RES / "metrics_by_cell.parquet")
ld = pl.read_parquet(RES / "layer_deltas.parquet")


def band_of(lo: pl.Expr, hi: pl.Expr) -> pl.Expr:
    return (pl.when(lo > 0).then(pl.lit("ABOVE_MIRROR"))
            .when(hi < 0).then(pl.lit("BELOW_MIRROR"))
            .otherwise(pl.lit("COVERS_MIRROR")))


print("#" * 100)
print("# PART 1 — PRIMARY READ: M15, TRAIN, POOLED, Delta log R vs L0")
print("#" * 100)
d = (ld.filter((pl.col("clock") == "M15") & (pl.col("band") == "TRAIN") & (pl.col("scope") == "POOLED"))
     .with_columns(band_of(pl.col("ci_low"), pl.col("ci_high")).alias("read"))
     .select(["variant_id", "delta", "delta_log_R", "ci_low", "ci_high", "ci_width",
              "block_mde", "n_dates", "read", "log_R_layer", "log_R_L0"])
     .sort(["variant_id", "delta"]))
print(d)
print("\nband tally (M15 pooled TRAIN deltas):")
print(d.group_by("read").len().sort("read"))
print("\nany ci_low > 0 ?", d.filter(pl.col("ci_low") > 0).height, "rows")
print(d.filter(pl.col("ci_low") > 0))

print("\n" + "#" * 100)
print("# PART 2 — CO-REPORT: H1, TRAIN, POOLED, Delta log R vs L0")
print("#" * 100)
h = (ld.filter((pl.col("clock") == "H1") & (pl.col("band") == "TRAIN") & (pl.col("scope") == "POOLED"))
     .with_columns(band_of(pl.col("ci_low"), pl.col("ci_high")).alias("read"))
     .select(["variant_id", "delta", "delta_log_R", "ci_low", "ci_high", "ci_width",
              "block_mde", "n_dates", "read"]).sort(["variant_id", "delta"]))
print(h)
print("\nband tally (H1 pooled TRAIN deltas):")
print(h.group_by("read").len().sort("read"))
print("\nH1 delta ci_low > 0:", h.filter(pl.col("ci_low") > 0).height)
print(h.filter(pl.col("ci_low") > 0))

print("\n" + "#" * 100)
print("# PART 3 — ABSOLUTE log R, POOLED TRAIN, both clocks")
print("#   (H1 = interpretable; M15 = ENTRY-QUALITY DISCLOSURE ONLY, AMENDMENT-9)")
print("#" * 100)
a = (met.filter((pl.col("scope") == "POOLED") & (pl.col("band") == "TRAIN")
                & pl.col("ci_low").is_not_null())
     .with_columns(band_of(pl.col("ci_low"), pl.col("ci_high")).alias("read"))
     .select(["clock", "variant_id", "delta", "n", "n_dates", "p", "p_be", "W", "L", "W_L",
              "log_R", "ci_low", "ci_high", "ci_width", "block_mde", "mde50", "read",
              "i_squared", "pooled_status", "fill_rate", "mean", "kappa"])
     .sort(["clock", "variant_id", "delta"]))
for clk in ("H1", "M15"):
    print(f"\n----- {clk} -----")
    print(a.filter(pl.col("clock") == clk).drop("clock"))
    sub = a.filter(pl.col("clock") == clk)
    print("band tally:", sub.group_by("read").len().sort("read").to_dicts())
    print("ci_low>0 rows:", sub.filter(pl.col("ci_low") > 0).height)
    print(sub.filter(pl.col("ci_low") > 0).select(
        ["variant_id", "delta", "n", "log_R", "ci_low", "ci_high", "mde50", "i_squared", "pooled_status"]))

print("\n" + "#" * 100)
print("# PART 4 — L0 baseline position vs the mirror (what the deltas are measured FROM)")
print("#" * 100)
l0 = (met.filter((pl.col("variant_id") == "L0_BASELINE") & (pl.col("scope") == "POOLED"))
      .with_columns(band_of(pl.col("ci_low"), pl.col("ci_high")).alias("read"))
      .select(["clock", "band", "delta", "n", "n_dates", "p", "p_be", "W", "L", "W_L", "log_R",
               "ci_low", "ci_high", "ci_width", "block_mde", "mde50", "read", "mean",
               "fill_rate", "p_flat", "kappa", "i_squared", "pooled_status"])
      .sort(["clock", "band", "delta"]))
print(l0)
