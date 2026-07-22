"""SPDR-004 fresh-context analyst emissions — re-derive from results/cells.parquet.

Post AMENDMENTS 1–5 re-run (A5: two_sample_block_vs_battery for UNF; battery_minus_seeds
banned). Does NOT import screen_code for verdict-bearing numbers.
Outputs richer tables under results/ for analysis.md.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

EXP = Path(__file__).resolve().parents[1]
RES = EXP / "results"
OUT = RES

# Cost floors from unit_pin (taker, spread=2 placeholder GAP)
FLOOR = {
    ("1h/5m", 0.5): 13.0625,
    ("1h/5m", 1.0): 13.125,
    ("1h/5m", 2.0): 13.25,
    ("1h/5m", 4.0): 13.5,
    ("4h/15m", 0.5): 13.25,
    ("4h/15m", 1.0): 13.5,
    ("4h/15m", 2.0): 14.0,
    ("4h/15m", 4.0): 15.0,
    ("1d/1h", 0.5): 14.5,
    ("1d/1h", 1.0): 16.0,
    ("1d/1h", 2.0): 19.0,
    ("1d/1h", 4.0): 25.0,
}

PRIMARY = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "OPUSDT",
    "DOGEUSDT",
    "1000PEPEUSDT",
    "APTUSDT",
    "LTCUSDT",
    "LINKUSDT",
]


def load() -> pl.DataFrame:
    return pl.read_parquet(RES / "cells.parquet")


def treatment(df: pl.DataFrame) -> pl.DataFrame:
    return df.filter(pl.col("is_treatment") & pl.col("primary_stratum"))


def with_flags(t: pl.DataFrame) -> pl.DataFrame:
    """Add analyst flags (finite-safe)."""
    return t.with_columns(
        [
            (pl.col("lift_ci_low").is_finite() & (pl.col("lift_ci_low") > 0)).alias(
                "lift_ci_pos"
            ),
            (pl.col("lift_ci_high").is_finite() & (pl.col("lift_ci_high") < 0)).alias(
                "lift_ci_neg"
            ),
            (pl.col("ci_low").is_finite() & (pl.col("ci_low") > 0)).alias("mean_ci_pos"),
            (pl.col("ci_high").is_finite() & (pl.col("ci_high") < 0)).alias("mean_ci_neg"),
            (pl.col("lift_bps").is_finite() & (pl.col("lift_bps") > 0)).alias("lift_pos"),
            (pl.col("mean_bps").is_finite() & (pl.col("mean_bps") > 0)).alias("mean_pos"),
            # L-20: seed band on lift CI low straddles 0 → MC-fragile
            (
                pl.col("lift_ci_low_seed_range_lo").is_finite()
                & pl.col("lift_ci_low_seed_range_hi").is_finite()
                & (pl.col("lift_ci_low_seed_range_lo") < 0)
                & (pl.col("lift_ci_low_seed_range_hi") > 0)
            ).alias("lift_seed_band_straddles_0"),
            # block_sensitivity: sign(ci_low) changes across ½×/1×/2× on mean CI
            (
                (
                    (pl.col("block_sens_half_ci_low") > 0).cast(pl.Int8)
                    + (pl.col("block_sens_1x_ci_low") > 0).cast(pl.Int8)
                    + (pl.col("block_sens_2x_ci_low") > 0).cast(pl.Int8)
                )
                .is_in([1, 2])
            ).alias("block_sens_sign_fragile"),
            pl.when(pl.col("destroy_collapse_frac").is_finite())
            .then(pl.col("destroy_collapse_frac"))
            .otherwise(None)
            .alias("collapse"),
        ]
    )


def med(s: pl.Series) -> float:
    a = s.drop_nulls().to_numpy()
    a = a[np.isfinite(a)]
    return float(np.median(a)) if a.size else float("nan")


def summarize_facets(t: pl.DataFrame) -> pl.DataFrame:
    rows = []

    def add(label: str, key: str, g: pl.DataFrame) -> None:
        powered = g.filter(~pl.col("unpowered"))
        lift_ci = g.filter(pl.col("lift_ci_pos"))
        lift_ci_pow = lift_ci.filter(~pl.col("unpowered"))
        rows.append(
            {
                "facet": label,
                "level": str(key),
                "n_cells": g.height,
                "n_powered": powered.height,
                "n_unpowered": g.filter(pl.col("unpowered")).height,
                "n_lift_pos": g.filter(pl.col("lift_pos")).height,
                "n_lift_ci_pos": lift_ci.height,
                "n_lift_ci_pos_powered": lift_ci_pow.height,
                "n_lift_ci_neg": g.filter(pl.col("lift_ci_neg")).height,
                "n_mean_ci_pos": g.filter(pl.col("mean_ci_pos")).height,
                "n_seed_band_straddle": g.filter(pl.col("lift_seed_band_straddles_0")).height,
                "n_block_sens_fragile": g.filter(pl.col("block_sens_sign_fragile")).height,
                "med_mean_bps": med(g["mean_bps"]),
                "med_lift_bps": med(g["lift_bps"]),
                "med_n_trades": med(g["n_trades"].cast(pl.Float64)),
                "med_collapse": med(g["collapse"].drop_nulls())
                if g["collapse"].drop_nulls().len()
                else float("nan"),
                "med_collapse_lift_ci_pos": med(lift_ci["collapse"].drop_nulls())
                if lift_ci.height and lift_ci["collapse"].drop_nulls().len()
                else float("nan"),
                "med_collapse_lift_ci_pos_powered": med(lift_ci_pow["collapse"].drop_nulls())
                if lift_ci_pow.height and lift_ci_pow["collapse"].drop_nulls().len()
                else float("nan"),
                "n_collapse_ge_0_5_on_lift_ci_pos": int(
                    (lift_ci["collapse"].drop_nulls() >= 0.5).sum()
                )
                if lift_ci.height
                else 0,
                "n_collapse_ge_0_8_on_lift_ci_pos": int(
                    (lift_ci["collapse"].drop_nulls() >= 0.8).sum()
                )
                if lift_ci.height
                else 0,
            }
        )

    for col, label in [
        ("domain", "domain"),
        ("hold_mult", "hold_mult"),
        ("base", "base"),
        ("htf_filter", "htf_filter"),
        ("symbol", "symbol"),
        ("lift_ci_method", "lift_ci_method"),
    ]:
        for key, g in t.group_by(col, maintain_order=True):
            k = key[0] if isinstance(key, tuple) else key
            add(label, k, g)

    for key, g in t.group_by(["base", "htf_filter"], maintain_order=True):
        add("base×filter", f"{key[0]}×{key[1]}", g)

    for key, g in t.group_by(["domain", "hold_mult"], maintain_order=True):
        add("domain×hold", f"{key[0]}@h{key[1]}", g)

    for key, g in t.group_by(["domain", "base", "htf_filter"], maintain_order=True):
        add("domain×base×filter", f"{key[0]}|{key[1]}×{key[2]}", g)

    for key, g in t.group_by(["domain", "htf_filter"], maintain_order=True):
        add("domain×filter", f"{key[0]}|{key[1]}", g)

    for key, g in t.group_by(["symbol", "domain"], maintain_order=True):
        add("symbol×domain", f"{key[0]}|{key[1]}", g)

    return pl.DataFrame(rows)


def positive_lift_cells(t: pl.DataFrame) -> pl.DataFrame:
    """Cells with finite positive lift CI low (A4: all bases have lift CI)."""
    return t.filter(pl.col("lift_ci_pos")).sort(
        ["domain", "htf_filter", "base", "symbol", "hold_mult"]
    )


def rand_rank_cells(t: pl.DataFrame) -> pl.DataFrame:
    """RAND treatment: battery rank (L-19) + A4 lift CI."""
    return (
        t.filter(pl.col("base") == "RAND")
        .with_columns(
            [
                (pl.col("battery_rank").is_finite() & (pl.col("battery_rank") >= 0.9)).alias(
                    "rank_ge_90"
                ),
                (pl.col("battery_rank").is_finite() & (pl.col("battery_rank") >= 0.8)).alias(
                    "rank_ge_80"
                ),
            ]
        )
        .sort(["domain", "htf_filter", "symbol", "hold_mult"])
    )


def detect_clusters(t: pl.DataFrame) -> pl.DataFrame:
    """K=3 promote-rule cluster scan (factual).

    Connected region = same domain + same HTF modality (DI or DI_ADX), varying hold and/or
    symbol. Cell counts as 'cluster member' if:
      - powered
      - positive lift point estimate
      - lift_ci_low > 0 (A4 two-sample / battery methods cover all bases)
      OR (base==RAND and battery_rank >= 0.9) as L-19 alternate
    """
    rows = []
    for domain in ["1h/5m", "4h/15m", "1d/1h"]:
        for filt in ["DI", "DI_ADX"]:
            g = t.filter((pl.col("domain") == domain) & (pl.col("htf_filter") == filt))
            memb = g.filter(
                (~pl.col("unpowered"))
                & pl.col("lift_pos")
                & (
                    pl.col("lift_ci_pos")
                    | (
                        (pl.col("base") == "RAND")
                        & pl.col("battery_rank").is_finite()
                        & (pl.col("battery_rank") >= 0.9)
                    )
                )
            )
            for base_scope, sub in [
                ("ALL_BASES", memb),
                ("UNF", memb.filter(pl.col("base") == "UNF")),
                ("MOM", memb.filter(pl.col("base") == "MOM")),
                ("RAND", memb.filter(pl.col("base") == "RAND")),
            ]:
                n = sub.height
                n_sym = sub["symbol"].n_unique() if n else 0
                n_hold = sub["hold_mult"].n_unique() if n else 0
                symbols = sorted(sub["symbol"].unique().to_list()) if n else []
                holds = sorted(sub["hold_mult"].unique().to_list()) if n else []
                bases = sorted(sub["base"].unique().to_list()) if n else []
                med_lift = med(sub["lift_bps"]) if n else float("nan")
                med_mean = med(sub["mean_bps"]) if n else float("nan")
                med_coll = med(sub["collapse"].drop_nulls()) if n else float("nan")
                n_coll_ge_0_5 = int((sub["collapse"].drop_nulls() >= 0.5).sum()) if n else 0
                n_coll_ge_0_8 = int((sub["collapse"].drop_nulls() >= 0.8).sum()) if n else 0
                n_coll_lt_0_2 = int((sub["collapse"].drop_nulls() < 0.2).sum()) if n else 0
                best_lift = float(sub["lift_bps"].max()) if n else float("nan")
                sole = n == 1
                n_seed_straddle = (
                    int(sub["lift_seed_band_straddles_0"].sum()) if n else 0
                )
                floors = [FLOOR.get((domain, float(h)), float("nan")) for h in holds]
                floor_min = float(np.nanmin(floors)) if floors else float("nan")
                floor_max = float(np.nanmax(floors)) if floors else float("nan")
                # per-cell mean above its own floor
                n_mean_above_own_floor = 0
                if n:
                    for r in sub.iter_rows(named=True):
                        fl = FLOOR.get((domain, float(r["hold_mult"])), float("nan"))
                        if np.isfinite(r["mean_bps"]) and np.isfinite(fl) and r["mean_bps"] > fl:
                            n_mean_above_own_floor += 1
                rows.append(
                    {
                        "domain": domain,
                        "htf_filter": filt,
                        "base_scope": base_scope,
                        "n_member_cells": n,
                        "n_symbols": n_sym,
                        "n_holds": n_hold,
                        "bases": ",".join(bases),
                        "symbols": ",".join(symbols),
                        "holds": ",".join(str(h) for h in holds),
                        "k3_cluster_ge3": n >= 3,
                        "neighbourhood_ok": n >= 2,
                        "sole_positive": sole,
                        "med_mean_bps": med_mean,
                        "med_lift_bps": med_lift,
                        "best_lift_bps": best_lift,
                        "med_collapse": med_coll,
                        "n_collapse_ge_0_5": n_coll_ge_0_5,
                        "n_collapse_ge_0_8": n_coll_ge_0_8,
                        "n_collapse_lt_0_2": n_coll_lt_0_2,
                        "n_seed_band_straddle": n_seed_straddle,
                        "floor_bps_min_in_cluster": floor_min,
                        "floor_bps_max_in_cluster": floor_max,
                        "med_mean_vs_floor_min": med_mean - floor_min
                        if np.isfinite(med_mean) and np.isfinite(floor_min)
                        else float("nan"),
                        "med_mean_above_floor_min": bool(
                            np.isfinite(med_mean)
                            and np.isfinite(floor_min)
                            and med_mean > floor_min
                        ),
                        "n_mean_above_own_floor": n_mean_above_own_floor,
                    }
                )
    return pl.DataFrame(rows)


def hold_ladder(t: pl.DataFrame) -> pl.DataFrame:
    return (
        t.select(
            [
                "symbol",
                "domain",
                "base",
                "htf_filter",
                "hold_mult",
                "hold_bars",
                "mean_bps",
                "lift_bps",
                "lift_ci_low",
                "lift_ci_high",
                "lift_ci_method",
                "n_trades",
                "unpowered",
                "destroy_collapse_frac",
                "battery_rank",
                "mde_bps",
                "baseline_mean_bps",
                "lift_ci_low_seed_range_lo",
                "lift_ci_low_seed_range_hi",
            ]
        )
        .sort(["domain", "base", "htf_filter", "symbol", "hold_mult"])
    )


def money_floor_table(t: pl.DataFrame) -> pl.DataFrame:
    rows = []
    for r in t.iter_rows(named=True):
        fl = FLOOR.get((r["domain"], float(r["hold_mult"])), float("nan"))
        mean = r["mean_bps"]
        lift = r["lift_bps"]
        rows.append(
            {
                **{
                    k: r[k]
                    for k in [
                        "symbol",
                        "domain",
                        "hold_mult",
                        "base",
                        "htf_filter",
                        "mean_bps",
                        "lift_bps",
                        "lift_ci_low",
                        "n_trades",
                        "unpowered",
                        "lift_ci_excludes_zero",
                    ]
                },
                "cost_floor_bps": fl,
                "mean_minus_floor": mean - fl if np.isfinite(mean) else float("nan"),
                "mean_above_floor": bool(np.isfinite(mean) and mean > fl),
                "lift_above_floor": bool(np.isfinite(lift) and lift > fl),
                "t1_undecidable_gross_lt_6": bool(
                    np.isfinite(mean) and abs(mean) < 6.0
                ),
            }
        )
    return pl.DataFrame(rows)


def collapse_table(t: pl.DataFrame) -> pl.DataFrame:
    return t.select(
        [
            "symbol",
            "domain",
            "hold_mult",
            "base",
            "htf_filter",
            "mean_bps",
            "phaseshift_mean_bps",
            "destroy_collapse_frac",
            "lift_bps",
            "lift_ci_low",
            "lift_ci_excludes_zero",
            "n_trades",
            "unpowered",
        ]
    ).sort("destroy_collapse_frac", descending=True, nulls_last=True)


def membership_summary() -> pl.DataFrame:
    mem = pl.read_parquet(RES / "membership.parquet")
    days = (
        mem.group_by("symbol")
        .agg(
            [
                pl.len().alias("n_days"),
                pl.col("rank").mean().alias("mean_rank"),
                pl.col("trailing_24h_notional_usdt").median().alias("med_notional_usdt"),
                pl.col("trailing_24h_base_volume").median().alias("med_base_volume"),
            ]
        )
        .sort("n_days", descending=True)
    )
    days.write_parquet(OUT / "membership_days.parquet")
    days.write_csv(OUT / "membership_days.csv")
    return days


def base_conditional(t: pl.DataFrame) -> pl.DataFrame:
    rows = []
    for key, g in t.group_by(["domain", "base", "htf_filter", "hold_mult"], maintain_order=True):
        domain, base, filt, hold = key
        powered = g.filter(~pl.col("unpowered"))
        rows.append(
            {
                "domain": domain,
                "base": base,
                "htf_filter": filt,
                "hold_mult": hold,
                "n_symbols": g.height,
                "n_powered": powered.height,
                "med_treatment_mean_bps": med(g["mean_bps"]),
                "med_baseline_mean_bps": med(g["baseline_mean_bps"]),
                "med_lift_bps": med(g["lift_bps"]),
                "med_n_trades": med(g["n_trades"].cast(pl.Float64)),
                "n_lift_ci_pos": g.filter(pl.col("lift_ci_pos")).height,
                "n_mean_ci_pos": g.filter(pl.col("mean_ci_pos")).height,
                "med_collapse": med(g["collapse"].drop_nulls()),
            }
        )
    return pl.DataFrame(rows)


def per_stratum_top(t: pl.DataFrame, n: int = 40) -> pl.DataFrame:
    """Top powered lift_ci_pos cells by lift_bps for analysis tables."""
    return (
        t.filter(pl.col("lift_ci_pos") & ~pl.col("unpowered"))
        .sort("lift_bps", descending=True)
        .head(n)
        .select(
            [
                "symbol",
                "domain",
                "hold_mult",
                "base",
                "htf_filter",
                "mean_bps",
                "lift_bps",
                "lift_ci_low",
                "lift_ci_high",
                "lift_ci_method",
                "n_trades",
                "destroy_collapse_frac",
                "battery_rank",
                "baseline_mean_bps",
                "lift_ci_low_seed_range_lo",
                "lift_ci_low_seed_range_hi",
                "mde_bps",
            ]
        )
    )


def main() -> None:
    df = load()
    t = with_flags(treatment(df))
    assert t.height == 720, t.height

    # L-20 / A4 integrity on emissions
    methods = set(t["lift_ci_method"].unique().to_list())
    allowed = {
        "two_sample_block",
        "two_sample_block_vs_battery",  # AMENDMENT-5 UNF vs RAND battery
        "two_sample_seed_means",
    }
    banned = {"battery_minus_seeds", "treatment_ci_minus_fixed_baseline"}
    assert methods <= allowed, f"unexpected lift_ci_method: {methods}"
    assert not (methods & banned), f"banned lift_ci_method present: {methods & banned}"
    for col in [
        "block_h_ci_low",
        "ci_low_seed_range_lo",
        "block_sens_half_ci_low",
        "lift_block",
        "lift_ci_low",
        "lift_ci_low_seed_range_lo",
    ]:
        assert t[col].is_finite().sum() == t.height, f"L-20 missing finite {col}"

    facets = summarize_facets(t)
    facets.write_parquet(OUT / "analyst_facets.parquet")
    facets.write_csv(OUT / "analyst_facets.csv")

    pos = positive_lift_cells(t)
    pos.write_parquet(OUT / "analyst_lift_ci_pos.parquet")
    pos.write_csv(OUT / "analyst_lift_ci_pos.csv")

    clusters = detect_clusters(t)
    clusters.write_parquet(OUT / "analyst_clusters_k3.parquet")
    clusters.write_csv(OUT / "analyst_clusters_k3.csv")

    ladder = hold_ladder(t)
    ladder.write_parquet(OUT / "analyst_hold_ladder.parquet")
    ladder.write_csv(OUT / "analyst_hold_ladder.csv")

    floors = money_floor_table(t)
    floors.write_parquet(OUT / "analyst_money_floor.parquet")
    floors.write_csv(OUT / "analyst_money_floor.csv")

    coll = collapse_table(t)
    coll.write_parquet(OUT / "analyst_control_c.parquet")
    coll.write_csv(OUT / "analyst_control_c.csv")

    bc = base_conditional(t)
    bc.write_parquet(OUT / "analyst_base_conditional.parquet")
    bc.write_csv(OUT / "analyst_base_conditional.csv")

    rand = rand_rank_cells(t)
    rand.write_parquet(OUT / "analyst_rand_ranks.parquet")
    rand.write_csv(OUT / "analyst_rand_ranks.csv")

    top = per_stratum_top(t, 60)
    top.write_parquet(OUT / "analyst_top_lift_ci_pos.parquet")
    top.write_csv(OUT / "analyst_top_lift_ci_pos.csv")

    days = membership_summary()

    lift_ci = t.filter(pl.col("lift_ci_pos"))
    lift_ci_pow = lift_ci.filter(~pl.col("unpowered"))
    clusters_ge3 = clusters.filter(
        pl.col("k3_cluster_ge3") & (pl.col("base_scope") != "ALL_BASES")
    )
    clusters_all = clusters.filter(
        pl.col("k3_cluster_ge3") & (pl.col("base_scope") == "ALL_BASES")
    )

    # money floor on powered lift_ci_pos
    fl_pos = floors.filter(
        pl.col("lift_ci_excludes_zero")
        & ~pl.col("unpowered")
        & (pl.col("mean_bps").is_finite())
    )
    n_mean_above = int(fl_pos["mean_above_floor"].sum()) if fl_pos.height else 0
    n_lift_above = int(fl_pos["lift_above_floor"].sum()) if fl_pos.height else 0

    # Control C on powered lift_ci_pos
    coll_pos = lift_ci_pow.filter(pl.col("collapse").is_not_null())

    # Per-symbol CI-pos counts
    by_sym = (
        t.group_by("symbol")
        .agg(
            [
                pl.len().alias("n"),
                pl.col("unpowered").sum().alias("n_unpowered"),
                pl.col("lift_ci_pos").sum().alias("n_lift_ci_pos"),
                pl.col("lift_pos").sum().alias("n_lift_pos"),
                pl.col("mean_bps").median().alias("med_mean"),
                pl.col("lift_bps").median().alias("med_lift"),
                pl.col("collapse").median().alias("med_collapse"),
            ]
        )
        .sort("n_lift_ci_pos", descending=True)
    )

    # per-base CI+ (A5: UNF mass corrected)
    by_base = (
        t.group_by("base")
        .agg(
            [
                pl.len().alias("n"),
                pl.col("unpowered").sum().alias("n_unpowered"),
                pl.col("lift_ci_pos").sum().alias("n_lift_ci_pos"),
                (pl.col("lift_ci_pos") & ~pl.col("unpowered"))
                .sum()
                .alias("n_lift_ci_pos_powered"),
                pl.col("lift_ci_neg").sum().alias("n_lift_ci_neg"),
                pl.col("mean_bps").median().alias("med_mean"),
                pl.col("lift_bps").median().alias("med_lift"),
                pl.col("collapse").median().alias("med_collapse"),
                pl.col("lift_ci_method").first().alias("lift_ci_method"),
            ]
        )
        .sort("base")
    )
    unf_ci = t.filter((pl.col("base") == "UNF") & pl.col("lift_ci_pos"))
    unf_ci_pow = unf_ci.filter(~pl.col("unpowered"))

    headline = {
        "amendments": [
            "AMENDMENT-1",
            "AMENDMENT-2",
            "AMENDMENT-3",
            "AMENDMENT-4",
            "AMENDMENT-5",
        ],
        "primary_symbols": PRIMARY,
        "lift_ci_methods_observed": sorted(methods),
        "l20_fields_all_finite_on_treatment": True,
        "n_treatment": t.height,
        "n_unpowered": int(t["unpowered"].sum()),
        "n_lift_point_pos": int(t["lift_pos"].sum()),
        "n_lift_ci_pos": lift_ci.height,
        "n_lift_ci_pos_powered": lift_ci_pow.height,
        "n_lift_ci_neg": int(t["lift_ci_neg"].sum()),
        "n_mean_ci_pos": int(t["mean_ci_pos"].sum()),
        "n_lift_seed_band_straddles_0": int(t["lift_seed_band_straddles_0"].sum()),
        "n_lift_ci_pos_seed_band_straddles_0": int(
            lift_ci["lift_seed_band_straddles_0"].sum()
        ),
        "by_base": by_base.to_dicts(),
        "unf_n_lift_ci_pos": unf_ci.height,
        "unf_n_lift_ci_pos_powered": unf_ci_pow.height,
        "unf_med_lift_ci_pos": med(unf_ci["lift_bps"]) if unf_ci.height else float("nan"),
        "unf_med_collapse_ci_pos": med(unf_ci["collapse"].drop_nulls())
        if unf_ci.height
        else float("nan"),
        "med_mean_bps_all": med(t["mean_bps"]),
        "med_lift_bps_all": med(t["lift_bps"]),
        "med_collapse_all": med(t["collapse"].drop_nulls()),
        "med_collapse_lift_ci_pos": med(lift_ci["collapse"].drop_nulls()),
        "med_collapse_lift_ci_pos_powered": med(lift_ci_pow["collapse"].drop_nulls()),
        "n_collapse_ge_0_5_lift_ci_pos_powered": int(
            (coll_pos["collapse"] >= 0.5).sum()
        )
        if coll_pos.height
        else 0,
        "n_collapse_ge_0_8_lift_ci_pos_powered": int(
            (coll_pos["collapse"] >= 0.8).sum()
        )
        if coll_pos.height
        else 0,
        "n_collapse_lt_0_2_lift_ci_pos_powered": int(
            (coll_pos["collapse"] < 0.2).sum()
        )
        if coll_pos.height
        else 0,
        "n_powered_lift_ci_pos_mean_above_floor": n_mean_above,
        "n_powered_lift_ci_pos_lift_above_floor": n_lift_above,
        "n_powered_lift_ci_pos_total": fl_pos.height,
        "n_clusters_ge3_all_bases": clusters_all.height,
        "n_clusters_ge3_per_base": clusters_ge3.height,
        "clusters_ge3_all_bases": clusters_all.to_dicts(),
        "clusters_ge3_per_base": clusters_ge3.sort(
            "med_lift_bps", descending=True
        ).to_dicts(),
        "by_symbol": by_sym.to_dicts(),
        "membership_top15_days": days.head(15).to_dicts(),
        "membership_first_rebalance": "2022-07-15",
        "top_lift_ci_pos_powered": top.to_dicts(),
        "note": (
            "A5: lift CI = two_sample_block | two_sample_block_vs_battery | "
            "two_sample_seed_means. battery_minus_seeds BANNED. "
            "Prior UNF CI+ mass (~108 / pooled 219) VOID. "
            "Pooled counts disclosure-only. Promote = design §8 K=3 factual read only."
        ),
    }
    (OUT / "analyst_headline.json").write_text(
        json.dumps(headline, indent=2, default=str)
    )

    print("=== SPDR-004 analyst re-derive (A1–A5) ===")
    print(f"treatment={t.height} unpowered={headline['n_unpowered']}")
    print(
        f"lift_ci_pos={headline['n_lift_ci_pos']} powered={headline['n_lift_ci_pos_powered']}"
    )
    print("by_base CI+:")
    print(by_base)
    print(
        f"med_mean={headline['med_mean_bps_all']:.3f} med_lift={headline['med_lift_bps_all']:.3f}"
    )
    print(
        f"med_collapse lift_ci_pos_powered={headline['med_collapse_lift_ci_pos_powered']:.3f}"
    )
    print(
        f"collapse>=0.5 on powered CI+: {headline['n_collapse_ge_0_5_lift_ci_pos_powered']}/"
        f"{headline['n_lift_ci_pos_powered']}"
    )
    print(
        f"mean>floor on powered CI+: {n_mean_above}/{fl_pos.height}; "
        f"lift>floor: {n_lift_above}/{fl_pos.height}"
    )
    print("lift_ci_methods:", methods)
    print("clusters K>=3 (all bases):")
    print(clusters_all)
    print("clusters K>=3 (per base) top:")
    print(clusters_ge3.sort("med_lift_bps", descending=True).head(12))
    print("by_symbol:")
    print(by_sym)
    print("wrote results/analyst_*.{parquet,csv,json}")


if __name__ == "__main__":
    main()
