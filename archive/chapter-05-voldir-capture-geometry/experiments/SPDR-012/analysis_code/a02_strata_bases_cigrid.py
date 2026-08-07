"""SPDR-012 analyst — script 2: per-stratum V-LEVEL table, three candidate bases, CI-grid fragility.

Outputs
  out_vlevel_strata.csv      per (symbol, clock, band) primary IC with envelope + labels
  out_cigrid_fragility.csv   per bootstrapped metric: does sign(ci_low) depend on block or seed?
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

EXP = Path(__file__).resolve().parents[1]
RES = EXP / "results"
OUT = EXP / "analysis_code"

pl.Config.set_tbl_rows(200)
pl.Config.set_tbl_width_chars(240)
pl.Config.set_fmt_str_lengths(40)


def primary(m: pl.DataFrame) -> pl.DataFrame:
    return (
        m.filter((pl.col("arm") == "V-LEVEL") & (pl.col("metric") == "oos_ic")
                 & (pl.col("model") == "ridge") & (pl.col("target") == "target_abs_oo"))
        .select("symbol", "clock", "band", "value", "ci_low", "ci_high", "se", "se_median",
                "n_obs", "n_dates", "mde", "band_label", "band_label_detected")
        .sort(["band", "clock", "symbol"])
    )


def main() -> None:
    m = pl.read_parquet(RES / "metrics_by_cell.parquet")
    p = primary(m)
    p.write_csv(OUT / "out_vlevel_strata.csv")

    print("=== V-LEVEL primary (ridge, next |open->open|) per band x clock ===")
    agg = (p.group_by(["band", "clock"])
           .agg(pl.len().alias("cells"),
                pl.col("value").median().round(4).alias("med_IC"),
                pl.col("value").min().round(4).alias("min_IC"),
                pl.col("value").max().round(4).alias("max_IC"),
                (pl.col("ci_low") > 0).sum().alias("ci_low_gt0"),
                (pl.col("ci_high") < 0).sum().alias("ci_high_lt0"),
                pl.col("n_dates").median().alias("med_dates"),
                pl.col("n_obs").median().alias("med_nobs"))
           .sort(["band", "clock"]))
    print(agg)

    print("\n=== label counts (both rules) ===")
    for col in ("band_label", "band_label_detected"):
        print(col)
        print(p.group_by(["band", "clock", col]).agg(pl.len()).sort(["band", "clock", col]))

    print("\n=== full per-stratum table ===")
    print(p)

    # ---- three candidate bases ----------------------------------------------------------
    print("\n=== THREE CANDIDATE BASES for design 6.4 ===")
    st = m.filter(pl.col("arm") == "STABILITY")
    n3_cal = st.filter(pl.col("metric") == "n_thirds_positive_calendar")
    n3_smp = st.filter(pl.col("metric") == "n_thirds_positive_sample")

    def clause1(band: str, labelcol: str) -> dict:
        sub = p.filter(pl.col("band") == band)
        sup = sub.filter(pl.col(labelcol) == "SUPPORTED")
        syms = sorted(set(sup["symbol"].to_list()))
        powered = sub.filter(pl.col(labelcol) != "UNPOWERED")
        return {
            "band": band, "label_rule": labelcol,
            "n_symbols_SUPPORTED_on_>=1_clock": len(syms),
            "symbols": syms,
            "n_cells": sub.height,
            "n_powered_cells": powered.height,
            "n_SUPPORTED_cells": sup.height,
            "pct_cells_IC_positive": round(100 * float((sub["value"] > 0).mean()), 1),
            "pct_powered_with_positive_IC": (
                round(100 * float((powered["value"] > 0).mean()), 1) if powered.height else None),
        }

    for b, lc in (("CONFIRM", "band_label"), ("DESIGN", "band_label"),
                  ("DESIGN", "band_label_detected"), ("CONFIRM", "band_label_detected")):
        print(json.dumps(clause1(b, lc), indent=1))

    print("\nclause 3 — thirds")
    for name, df in (("calendar", n3_cal), ("sample", n3_smp)):
        vals = df["value"].to_numpy()
        print(f"  {name}: n_cells={len(vals)} "
              f">=2 positive: {(vals >= 2).sum()} | ==1: {(vals == 1).sum()} | ==0: {(vals == 0).sum()}")
    # how many thirds were actually powered/non-empty
    for name in ("calendar", "sample"):
        sub = st.filter(pl.col("metric").str.starts_with(f"ic_third"))
        sub = sub.filter(pl.col("metric").str.ends_with(name))
        piv = sub.pivot(values="value", index=["symbol", "clock"], on="metric")
        cols = [c for c in piv.columns if c.startswith("ic_third")]
        nn = piv.select([pl.col(c).is_not_null().cast(pl.Int8) for c in cols]).sum_horizontal()
        print(f"  {name}: non-empty thirds per cell -> "
              f"{dict(zip(*np.unique(nn.to_numpy(), return_counts=True)))}")

    # ---- CI grid fragility --------------------------------------------------------------
    print("\n=== CI GRID FRAGILITY (L-20) ===")
    grids = json.loads((RES / "ci_grid.json").read_text())["grids"]
    rows = []
    for g in grids:
        cells = g["block_sensitivity"]
        lows = np.array([c["ci_low"] for c in cells])
        highs = np.array([c["ci_high"] for c in cells])
        by_block = {}
        for b in (1, 3, 7):
            sel = [c for c in cells if c["block"] == b]
            by_block[b] = (min(c["ci_low"] for c in sel), max(c["ci_high"] for c in sel))
        rows.append({
            "key": g["key"], "point": g["point"],
            "n_grid": len(cells),
            "env_low": g["ci_low_envelope"], "env_high": g["ci_high_envelope"],
            "min_low": float(lows.min()), "max_low": float(lows.max()),
            "min_high": float(highs.min()), "max_high": float(highs.max()),
            "sign_low_agree": bool(np.all(np.sign(lows) == np.sign(lows[0]))),
            "sign_high_agree": bool(np.all(np.sign(highs) == np.sign(highs[0]))),
            "n_cells_low_gt0": int((lows > 0).sum()),
            "low_b1": by_block[1][0], "low_b3": by_block[3][0], "low_b7": by_block[7][0],
        })
    fg = pl.DataFrame(rows)
    fg = fg.with_columns([
        pl.col("key").str.split("|").list.get(0).alias("arm"),
        pl.col("key").str.split("|").list.get(1).alias("symbol"),
        pl.col("key").str.split("|").list.get(2).alias("clock"),
        pl.col("key").str.split("|").list.get(3).alias("band"),
        pl.col("key").str.split("|").list.get(4).alias("metric"),
        pl.col("key").str.split("|").list.get(5).alias("model"),
        pl.col("key").str.split("|").list.get(6).alias("target"),
    ])
    fg.write_csv(OUT / "out_cigrid_fragility.csv")
    print("n bootstrapped metrics with a grid:", fg.height,
          "| all 15-cell:", bool((fg["n_grid"] == 15).all()))
    frag = fg.filter(~pl.col("sign_low_agree"))
    print("metrics where sign(ci_low) is NOT constant across the 15 grid cells:", frag.height)
    print(frag.group_by(["arm", "metric"]).agg(pl.len()).sort("len", descending=True).head(20))

    # focus: the band-carrying primary metric
    prim = fg.filter((pl.col("arm") == "V-LEVEL") & (pl.col("metric") == "oos_ic")
                     & (pl.col("model") == "ridge") & (pl.col("target") == "target_abs_oo"))
    print("\nprimary V-LEVEL cells with a grid:", prim.height)
    print("  envelope low > 0:", int((prim["env_low"] > 0).sum()),
          "| every grid cell low > 0:", int((prim["n_cells_low_gt0"] == 15).sum()),
          "| some but not all:", int(((prim["n_cells_low_gt0"] > 0) & (prim["n_cells_low_gt0"] < 15)).sum()))
    print(prim.filter((prim["n_cells_low_gt0"] > 0) & (prim["n_cells_low_gt0"] < 15))
          .select("symbol", "clock", "band", "point", "env_low", "n_cells_low_gt0",
                  "low_b1", "low_b3", "low_b7"))

    # regime gaps
    gp = fg.filter(pl.col("metric") == "gap_high_low_bps")
    print("\nregime/HMM gap metrics with a grid:", gp.height,
          "| envelope low>0:", int((gp["env_low"] > 0).sum()),
          "| all 15 grid lows > 0:", int((gp["n_cells_low_gt0"] == 15).sum()),
          "| block-fragile (some but not all):",
          int(((gp["n_cells_low_gt0"] > 0) & (gp["n_cells_low_gt0"] < 15)).sum()))
    print(gp.filter((gp["n_cells_low_gt0"] > 0) & (gp["n_cells_low_gt0"] < 15))
          .select("arm", "symbol", "clock", "band", "point", "env_low",
                  "n_cells_low_gt0", "low_b1", "low_b3", "low_b7").head(30))


if __name__ == "__main__":
    main()
