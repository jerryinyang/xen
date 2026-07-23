"""SPDR-012 fresh-context analyst — script 1: independent re-derivation + fence checks.

Recomputes the primary V-LEVEL OOS rank IC directly from results/vol_reliability.parquet
(per-origin predictions + targets) and compares against results/metrics_by_cell.parquet.
Also re-checks the TRAIN fence, the rv_next quarantine flag, and per-cell coverage.

Nothing here imports screen_code/ or analysis_code/summarise.py.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl
from scipy import stats

EXP = Path(__file__).resolve().parents[1]
RES = EXP / "results"

TEST_START_NS = int(np.datetime64("2023-12-18T00:00:00", "ns").astype("int64"))
HOLDOUT_START_NS = int(np.datetime64("2025-01-08T00:00:00", "ns").astype("int64"))
DESIGN_START_NS = int(np.datetime64("2021-06-29T06:53:00", "ns").astype("int64"))
DESIGN_END_NS = int(np.datetime64("2023-03-01T00:00:00", "ns").astype("int64"))


def load():
    v = pl.read_parquet(RES / "vol_reliability.parquet")
    m = pl.read_parquet(RES / "metrics_by_cell.parquet")
    return v, m


def fence(v: pl.DataFrame) -> dict:
    # target_slot_start is the OPEN of the target bar; the target's EXIT price is the open
    # of the bar after that, i.e. target_slot_start + clock span.
    span = {"H1": 3600, "H4": 4 * 3600, "D1": 86400}
    ex = v.with_columns(
        (pl.col("target_slot_start") + pl.col("clock").replace_strict(span) * 1_000_000_000)
        .alias("target_exit_ts")
    )
    out = {
        "max_slot_end": int(v["slot_end"].max()),
        "max_target_slot_start": int(v["target_slot_start"].max()),
        "max_target_exit_ts": int(ex["target_exit_ts"].max()),
        "n_rows_at_or_after_TEST": int(ex.filter(pl.col("target_exit_ts") >= TEST_START_NS).height),
        "n_rows_at_or_after_HOLDOUT": int(ex.filter(pl.col("target_exit_ts") >= HOLDOUT_START_NS).height),
        "n_DESIGN_rows_with_exit_at_or_after_DESIGN_END": int(
            ex.filter((pl.col("band") == "DESIGN") & (pl.col("target_exit_ts") > DESIGN_END_NS)).height
        ),
        "n_DESIGN_rows": int(v.filter(pl.col("band") == "DESIGN").height),
        "min_slot_start": int(v["slot_start"].min()),
    }
    for k in ("max_slot_end", "max_target_slot_start", "max_target_exit_ts", "min_slot_start"):
        out[k + "_utc"] = str(np.datetime64(out[k], "ns"))
    return out


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 10:
        return float("nan")
    return float(stats.spearmanr(a[ok], b[ok]).statistic)


def rederive_vlevel_ic(v: pl.DataFrame) -> pl.DataFrame:
    rows = []
    sub = v.filter(pl.col("oos"))
    for (sym, clock, band), g in sub.group_by(["symbol", "clock", "band"], maintain_order=True):
        p = g["pred__vlevel_ridge__target_abs_oo"].to_numpy()
        y = g["target_abs_oo"].to_numpy()
        rows.append({
            "symbol": sym, "clock": clock, "band": band,
            "ic_recomputed": spearman(p, y),
            "n_oos": int(np.isfinite(p).sum()),
        })
    return pl.DataFrame(rows)


def main() -> None:
    v, m = load()
    print("=== rows:", v.shape, m.shape)
    print("\n=== FENCE ===")
    print(json.dumps(fence(v), indent=1, default=str))

    print("\n=== independent re-derivation of V-LEVEL ridge OOS IC ===")
    mine = rederive_vlevel_ic(v)
    emitted = (
        m.filter((pl.col("arm") == "V-LEVEL") & (pl.col("metric") == "oos_ic")
                 & (pl.col("model") == "ridge") & (pl.col("target") == "target_abs_oo"))
        .select("symbol", "clock", "band", pl.col("value").alias("ic_emitted"),
                "ci_low", "ci_high", "n_obs", "n_dates", "mde",
                "band_label", "band_label_detected")
    )
    j = emitted.join(mine, on=["symbol", "clock", "band"], how="full", coalesce=True)
    j = j.with_columns((pl.col("ic_emitted") - pl.col("ic_recomputed")).abs().alias("absdiff"))
    print("max abs diff emitted vs recomputed:", j["absdiff"].max())
    print("n mismatched n_obs:", j.filter(pl.col("n_obs") != pl.col("n_oos")).height)
    print(j.sort("absdiff", descending=True).head(8))
    j.write_parquet(EXP / "analysis_code" / "out_vlevel_ic_check.parquet")

    print("\n=== rv_next quarantine ===")
    q = m.filter(pl.col("target") == "rv_next")
    print("rows with target=rv_next:", q.height,
          "| all flagged target_overlaps_feature:", bool(q["target_overlaps_feature"].all()))
    nq = m.filter((pl.col("target") != "rv_next") & pl.col("target_overlaps_feature"))
    print("rows flagged but target != rv_next:", nq.height,
          nq.select("arm", "metric", "target").unique().to_dicts()[:10])
    print("median oos_ic on rv_next by band:",
          q.filter(pl.col("metric") == "oos_ic").group_by("band")
           .agg(pl.col("value").median()).to_dicts())
    # also: any metric row NOT flagged that uses rv_next implicitly
    print("V-PERSIST ic_rv20_vs_rv_next flagged?",
          m.filter(pl.col("metric") == "ic_rv20_vs_rv_next")["target_overlaps_feature"].to_list()[:5])

    print("\n=== coverage per cell (origins) ===")
    cov = (v.group_by(["symbol", "clock", "band"])
           .agg(pl.len().alias("n_origins"),
                pl.col("target_date").n_unique().alias("n_dates"),
                pl.col("oos").sum().alias("n_oos"),
                pl.col("target_contiguous").mean().alias("contig_frac"))
           .sort(["clock", "band", "symbol"]))
    print(cov.group_by(["clock", "band"]).agg(
        pl.len().alias("n_cells"),
        pl.col("n_dates").median().alias("med_dates"),
        pl.col("n_dates").min().alias("min_dates"),
        pl.col("n_dates").max().alias("max_dates"),
        pl.col("n_origins").median().alias("med_origins"),
    ).sort(["band", "clock"]))
    cov.write_parquet(EXP / "analysis_code" / "out_coverage.parquet")


if __name__ == "__main__":
    main()
