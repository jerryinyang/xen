"""SPDR-005 fresh-context analyst — re-derive from results/*.parquet.

CF-EPSOSC-001 TRAIN-only episode-oscillation availability screen.
Does NOT import screen_code for verdict-bearing numbers.
K=3 promote read uses ONLY is_primary_promote=True (640 cells).
Primary unit: gross open-to-open bps/episode (L-16).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

EXP = Path(__file__).resolve().parents[1]
RES = EXP / "results"
OUT = RES

FEE_RT_TAKER_BPS = 11.0
FUNDING_BPS_PER_8H = 1.0  # GAP disclosed

# Promote-member definition (design §7): powered + lift_ci_low > 0
# Collapse expected under Control B ≈ 1


def load_cells() -> pl.DataFrame:
    return pl.read_parquet(RES / "cells.parquet")


def load_unit_pin() -> dict:
    return json.loads((RES / "unit_pin.json").read_text())


def load_integrity() -> dict:
    return json.loads((RES / "integrity.json").read_text())


def with_flags(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
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
            (
                pl.col("lift_ci_low_seed_range_lo").is_finite()
                & pl.col("lift_ci_low_seed_range_hi").is_finite()
                & (pl.col("lift_ci_low_seed_range_lo") < 0)
                & (pl.col("lift_ci_low_seed_range_hi") > 0)
            ).alias("lift_seed_band_straddles_0"),
            pl.when(pl.col("destroy_collapse_frac").is_finite())
            .then(pl.col("destroy_collapse_frac"))
            .otherwise(None)
            .alias("collapse"),
            # promote candidate: powered + positive lift CI
            (
                (~pl.col("unpowered"))
                & pl.col("lift_ci_low").is_finite()
                & (pl.col("lift_ci_low") > 0)
            ).alias("promote_cand"),
        ]
    )


def med(s: pl.Series) -> float:
    a = s.drop_nulls().to_numpy()
    a = a[np.isfinite(a)]
    return float(np.median(a)) if a.size else float("nan")


def cost_floor_bps(spread_bps: float, hold_hours: float) -> float:
    """Taker RT fee + measured RT spread + funding GAP scaled by hold hours."""
    funding = FUNDING_BPS_PER_8H * (hold_hours / 8.0)
    return FEE_RT_TAKER_BPS + float(spread_bps) + funding


def domain_minutes(domain: str) -> float:
    return {"5m": 5.0, "15m": 15.0, "1h": 60.0}[domain]


def summarize_facets(t: pl.DataFrame) -> pl.DataFrame:
    rows: list[dict] = []

    def add(label: str, key: str, g: pl.DataFrame) -> None:
        powered = g.filter(~pl.col("unpowered"))
        lift_ci = g.filter(pl.col("lift_ci_pos"))
        lift_ci_pow = lift_ci.filter(~pl.col("unpowered"))
        cand = g.filter(pl.col("promote_cand"))
        rows.append(
            {
                "facet": label,
                "level": str(key),
                "n_cells": g.height,
                "n_powered": powered.height,
                "n_unpowered": int(g["unpowered"].sum()),
                "n_lift_pos": int(g["lift_pos"].sum()),
                "n_lift_ci_pos": lift_ci.height,
                "n_lift_ci_pos_powered": lift_ci_pow.height,
                "n_lift_ci_neg": int(g["lift_ci_neg"].sum()),
                "n_mean_ci_pos": int(g["mean_ci_pos"].sum()),
                "n_promote_cand": cand.height,
                "n_seed_band_straddle": int(g["lift_seed_band_straddles_0"].sum()),
                "n_censored_flag_gt20": int(g["censored_flag_gt20"].sum()),
                "med_mean_bps": med(g["mean_bps"]),
                "med_lift_bps": med(g["lift_bps"]),
                "med_n_episodes": med(g["n_episodes"].cast(pl.Float64)),
                "med_censored_frac": med(g["censored_frac"]),
                "med_median_duration": med(g["median_duration"]),
                "med_frac_ret_clear": med(g["frac_ret_clear"]),
                "med_frac_time_clear": med(g["frac_time_clear"]),
                "med_battery_rank": med(g["battery_rank"]),
                "med_collapse": med(g["collapse"].drop_nulls())
                if g["collapse"].drop_nulls().len()
                else float("nan"),
                "med_collapse_lift_ci_pos": med(lift_ci["collapse"].drop_nulls())
                if lift_ci.height and lift_ci["collapse"].drop_nulls().len()
                else float("nan"),
                "med_collapse_promote_cand": med(cand["collapse"].drop_nulls())
                if cand.height and cand["collapse"].drop_nulls().len()
                else float("nan"),
                "n_collapse_ge_0_5_promote": int(
                    (cand["collapse"].drop_nulls() >= 0.5).sum()
                )
                if cand.height
                else 0,
                "n_collapse_ge_0_8_promote": int(
                    (cand["collapse"].drop_nulls() >= 0.8).sum()
                )
                if cand.height
                else 0,
                "n_rank_ge_0_9": int(
                    (
                        g["battery_rank"].is_finite() & (g["battery_rank"] >= 0.9)
                    ).sum()
                ),
                "n_rank_ge_0_8": int(
                    (
                        g["battery_rank"].is_finite() & (g["battery_rank"] >= 0.8)
                    ).sum()
                ),
            }
        )

    for col, label in [
        ("domain", "domain"),
        ("object", "object"),
        ("clear", "clear"),
        ("side", "side"),
        ("w", "w"),
        ("k", "k"),
        ("symbol", "symbol"),
    ]:
        for key, g in t.group_by(col, maintain_order=True):
            k = key[0] if isinstance(key, tuple) else key
            add(label, k, g)

    for key, g in t.group_by(["object", "domain"], maintain_order=True):
        add("object×domain", f"{key[0]}×{key[1]}", g)

    for key, g in t.group_by(["object", "domain", "clear"], maintain_order=True):
        add("object×domain×clear", f"{key[0]}×{key[1]}×{key[2]}", g)

    for key, g in t.group_by(["domain", "side"], maintain_order=True):
        add("domain×side", f"{key[0]}×{key[1]}", g)

    for key, g in t.group_by(["object", "side"], maintain_order=True):
        add("object×side", f"{key[0]}×{key[1]}", g)

    for key, g in t.group_by(["symbol", "domain"], maintain_order=True):
        add("symbol×domain", f"{key[0]}|{key[1]}", g)

    for key, g in t.group_by(["clear", "domain"], maintain_order=True):
        add("clear×domain", f"{key[0]}×{key[1]}", g)

    return pl.DataFrame(rows)


def detect_clusters(prim: pl.DataFrame) -> pl.DataFrame:
    """K=3 cluster scan on primary promote slice only.

    Cluster region = same episode-object family + domain + clear, varying k/W/symbol/side.
    Member = promote_cand (powered + lift_ci_low > 0).
    Design §7: K≥3 cells, same object family, varying k and/or W and/or symbol/domain.
    """
    rows: list[dict] = []
    memb = prim.filter(pl.col("promote_cand"))

    # Region definitions at multiple grains
    region_specs = [
        (["object", "domain", "clear"], "object×domain×clear"),
        (["object", "domain"], "object×domain"),
        (["object", "clear"], "object×clear"),
        (["object", "domain", "clear", "side"], "object×domain×clear×side"),
        (["object", "domain", "side"], "object×domain×side"),
        (["symbol", "object", "domain"], "symbol×object×domain"),
        (["symbol", "object", "domain", "clear"], "symbol×object×domain×clear"),
    ]

    for keys, grain in region_specs:
        for key, g in memb.group_by(keys, maintain_order=True):
            if isinstance(key, tuple):
                level = "×".join(str(x) for x in key)
            else:
                level = str(key)
            n = g.height
            n_sym = g["symbol"].n_unique()
            n_k = g["k"].n_unique()
            n_w = g["w"].n_unique()
            n_side = g["side"].n_unique()
            n_domain = g["domain"].n_unique()
            n_clear = g["clear"].n_unique() if "clear" not in keys else 1
            symbols = sorted(g["symbol"].unique().to_list())
            ks = sorted(g["k"].unique().to_list())
            ws = sorted(g["w"].unique().to_list())
            sides = sorted(g["side"].unique().to_list())
            med_lift = med(g["lift_bps"])
            med_mean = med(g["mean_bps"])
            med_coll = med(g["collapse"].drop_nulls())
            med_rank = med(g["battery_rank"])
            med_dur = med(g["median_duration"])
            med_cens = med(g["censored_frac"])
            n_coll_ge_05 = int((g["collapse"].drop_nulls() >= 0.5).sum())
            n_coll_ge_08 = int((g["collapse"].drop_nulls() >= 0.8).sum())
            n_seed_straddle = int(g["lift_seed_band_straddles_0"].sum())
            best_lift = float(g["lift_bps"].max())
            # neighbourhood: not sole positive — need ≥2 cells with adjacent k or W
            neighbourhood_ok = (n >= 2) and (n_k >= 2 or n_w >= 2 or n_sym >= 2)
            # design K: ≥3 cells, same object, varying k and/or W and/or symbol/domain
            k3 = n >= 3 and (n_k >= 2 or n_w >= 2 or n_sym >= 2 or n_domain >= 2)
            rows.append(
                {
                    "grain": grain,
                    "region": level,
                    "object": g["object"][0],
                    "n_member_cells": n,
                    "n_symbols": n_sym,
                    "n_k": n_k,
                    "n_w": n_w,
                    "n_side": n_side,
                    "n_domain": n_domain,
                    "n_clear": n_clear,
                    "symbols": ",".join(symbols),
                    "ks": ",".join(str(x) for x in ks),
                    "ws": ",".join(str(x) for x in ws),
                    "sides": ",".join(sides),
                    "k3_cluster_ge3": k3,
                    "neighbourhood_ok": neighbourhood_ok,
                    "sole_positive": n == 1,
                    "med_mean_bps": med_mean,
                    "med_lift_bps": med_lift,
                    "best_lift_bps": best_lift,
                    "med_battery_rank": med_rank,
                    "med_collapse": med_coll,
                    "n_collapse_ge_0_5": n_coll_ge_05,
                    "n_collapse_ge_0_8": n_coll_ge_08,
                    "n_seed_band_straddle": n_seed_straddle,
                    "med_median_duration_bars": med_dur,
                    "med_censored_frac": med_cens,
                    "med_frac_ret_clear": med(g["frac_ret_clear"]),
                    "med_frac_time_clear": med(g["frac_time_clear"]),
                }
            )
    return pl.DataFrame(rows).sort(
        ["grain", "n_member_cells", "med_lift_bps"], descending=[False, True, True]
    )


def money_floor_table(prim: pl.DataFrame, spreads: dict[str, float]) -> pl.DataFrame:
    rows: list[dict] = []
    for r in prim.iter_rows(named=True):
        spread = spreads.get(r["symbol"], float("nan"))
        # duration in bars → hours
        dur_bars = r["median_duration"]
        mins = domain_minutes(r["domain"])
        hold_h = (
            float(dur_bars) * mins / 60.0
            if np.isfinite(dur_bars) and dur_bars is not None
            else float("nan")
        )
        # also report fixed hold ladders for disclosure
        floor = (
            cost_floor_bps(spread, hold_h) if np.isfinite(hold_h) else float("nan")
        )
        floor_8h = cost_floor_bps(spread, 8.0)
        mean = r["mean_bps"]
        lift = r["lift_bps"]
        rows.append(
            {
                "symbol": r["symbol"],
                "domain": r["domain"],
                "object": r["object"],
                "w": r["w"],
                "k": r["k"],
                "clear": r["clear"],
                "side": r["side"],
                "mean_bps": mean,
                "lift_bps": lift,
                "lift_ci_low": r["lift_ci_low"],
                "n_episodes": r["n_episodes"],
                "unpowered": r["unpowered"],
                "promote_cand": r["promote_cand"],
                "median_duration_bars": dur_bars,
                "hold_hours_from_med_dur": hold_h,
                "spread_bps": spread,
                "cost_floor_bps": floor,
                "cost_floor_8h_bps": floor_8h,
                "mean_minus_floor": mean - floor
                if np.isfinite(mean) and np.isfinite(floor)
                else float("nan"),
                "mean_above_floor": bool(
                    np.isfinite(mean) and np.isfinite(floor) and mean > floor
                ),
                "lift_above_floor": bool(
                    np.isfinite(lift) and np.isfinite(floor) and lift > floor
                ),
                "t1_undecidable_lt_3x_spread": bool(
                    np.isfinite(mean)
                    and np.isfinite(spread)
                    and abs(mean) < 3.0 * spread
                ),
            }
        )
    return pl.DataFrame(rows)


def vr_analysis() -> dict:
    vr = pl.read_parquet(RES / "vr_facet.parquet")
    # design §5.5: flat if no lag with VR systematically <1 on ≥ half of symbols
    # in primary domains {15m, 1h}
    primary_domains = ["15m", "1h"]
    by = (
        vr.group_by(["domain", "lag"])
        .agg(
            [
                pl.col("vr").median().alias("med_vr"),
                pl.col("vr").mean().alias("mean_vr"),
                (pl.col("vr") < 1.0).mean().alias("frac_vr_lt1"),
                (pl.col("vr") < 1.0).sum().alias("n_vr_lt1"),
                pl.len().alias("n_symbols"),
            ]
        )
        .sort(["domain", "lag"])
    )
    # half-symbol rule: for each primary domain, any lag with frac_vr_lt1 >= 0.5?
    half_met = {}
    for d in primary_domains + ["5m"]:
        sub = by.filter(pl.col("domain") == d)
        lags_ok = sub.filter(pl.col("frac_vr_lt1") >= 0.5)
        half_met[d] = {
            "any_lag_half_lt1": lags_ok.height > 0,
            "lags_meeting": lags_ok["lag"].to_list() if lags_ok.height else [],
            "max_frac_lt1": float(sub["frac_vr_lt1"].max()) if sub.height else 0.0,
            "min_med_vr": float(sub["med_vr"].min()) if sub.height else float("nan"),
        }
    # flat = no lag with VR systematically <1 on ≥ half symbols on primary domains
    flat = not (
        half_met["15m"]["any_lag_half_lt1"] or half_met["1h"]["any_lag_half_lt1"]
    )
    # per-symbol primary-domain VR
    per_sym = (
        vr.filter(pl.col("domain").is_in(primary_domains))
        .group_by(["symbol", "domain"])
        .agg(
            [
                pl.col("vr").median().alias("med_vr"),
                (pl.col("vr") < 1.0).mean().alias("frac_lags_lt1"),
            ]
        )
        .sort(["domain", "med_vr"])
    )
    return {
        "by_domain_lag": by.to_dicts(),
        "half_symbol_rule": half_met,
        "vr_flat_primary_domains": flat,
        "per_symbol_primary": per_sym.to_dicts(),
        "coupling_note": (
            "VR not flat on primary domains → standard K≥3 promote path "
            "(no §5.5 stronger-evidence override)"
            if not flat
            else "VR flat → require K≥3 AND median lift ci_low > MDE with Control B collapse"
        ),
    }


def grid_twin_analysis() -> dict:
    gt = pl.read_parquet(RES / "grid_twin.parquet")
    by_dom = (
        gt.group_by("domain")
        .agg(
            [
                pl.col("mean_bps").median().alias("med_mean"),
                pl.col("mean_bps").mean().alias("mean_mean"),
                (pl.col("mean_bps") > 0).sum().alias("n_pos"),
                pl.len().alias("n"),
                pl.col("n_episodes").median().alias("med_n"),
            ]
        )
        .sort("domain")
    )
    pos = gt.filter(pl.col("mean_bps") > 0).sort("mean_bps", descending=True)
    return {
        "n_rows": gt.height,
        "med_mean_bps": med(gt["mean_bps"]),
        "mean_mean_bps": float(gt["mean_bps"].mean()),
        "n_positive": int((gt["mean_bps"] > 0).sum()),
        "by_domain": by_dom.to_dicts(),
        "top_positive": pos.head(10).to_dicts(),
        "all": gt.sort(["domain", "symbol"]).to_dicts(),
    }


def censoring_analysis(full: pl.DataFrame, prim: pl.DataFrame) -> dict:
    def block(g: pl.DataFrame, label: str) -> dict:
        return {
            "slice": label,
            "n_cells": g.height,
            "med_censored_frac": med(g["censored_frac"]),
            "mean_censored_frac": float(g["censored_frac"].mean()),
            "n_flag_gt20": int(g["censored_flag_gt20"].sum()),
            "n_any_censored": int((g["n_censored"] > 0).sum()),
            "med_n_censored": med(g["n_censored"].cast(pl.Float64)),
            "med_n_started": med(g["n_started"].cast(pl.Float64)),
        }

    rows = [block(full, "full_3240"), block(prim, "primary_640")]
    for col in ["clear", "domain", "object"]:
        for key, g in full.group_by(col, maintain_order=True):
            k = key[0] if isinstance(key, tuple) else key
            rows.append(block(g, f"full|{col}={k}"))
        for key, g in prim.group_by(col, maintain_order=True):
            k = key[0] if isinstance(key, tuple) else key
            rows.append(block(g, f"primary|{col}={k}"))
    # RET_ANCHOR alone is the A1 risk surface
    ret_full = full.filter(pl.col("clear") == "RET_ANCHOR")
    ret_prim = prim.filter(pl.col("clear") == "RET_ANCHOR")
    return {
        "blocks": rows,
        "ret_anchor_full_flag_gt20": int(ret_full["censored_flag_gt20"].sum()),
        "ret_anchor_primary_flag_gt20": int(ret_prim["censored_flag_gt20"].sum()),
        "ret_anchor_primary_med_censored_frac": med(ret_prim["censored_frac"]),
        "hybrid_primary_med_censored_frac": med(
            prim.filter(pl.col("clear") == "HYBRID")["censored_frac"]
        ),
    }


def path_diagnostics(prim: pl.DataFrame) -> pl.DataFrame:
    rows: list[dict] = []
    for keys, grain in [
        (["object", "domain", "clear"], "object×domain×clear"),
        (["clear"], "clear"),
        (["domain"], "domain"),
        (["object"], "object"),
    ]:
        for key, g in prim.group_by(keys, maintain_order=True):
            if isinstance(key, tuple):
                level = "×".join(str(x) for x in key)
            else:
                level = str(key)
            rows.append(
                {
                    "grain": grain,
                    "level": level,
                    "n_cells": g.height,
                    "med_median_duration_bars": med(g["median_duration"]),
                    "med_mean_duration_bars": med(g["mean_duration"]),
                    "med_frac_ret_clear": med(g["frac_ret_clear"]),
                    "med_frac_time_clear": med(g["frac_time_clear"]),
                    "med_n_episodes": med(g["n_episodes"].cast(pl.Float64)),
                    "med_censored_frac": med(g["censored_frac"]),
                }
            )
    return pl.DataFrame(rows)


def membership_summary() -> pl.DataFrame:
    mem = pl.read_parquet(RES / "membership.parquet")
    days = (
        mem.group_by("symbol")
        .agg(
            [
                pl.len().alias("n_days"),
                pl.col("rank").mean().alias("mean_rank"),
                pl.col("trailing_24h_base_volume").median().alias("med_base_volume"),
            ]
        )
        .sort("n_days", descending=True)
    )
    return days


def top_promote_cells(prim: pl.DataFrame, n: int = 40) -> pl.DataFrame:
    return (
        prim.filter(pl.col("promote_cand"))
        .sort("lift_bps", descending=True)
        .head(n)
        .select(
            [
                "symbol",
                "domain",
                "object",
                "w",
                "k",
                "clear",
                "side",
                "mean_bps",
                "lift_bps",
                "lift_ci_low",
                "lift_ci_high",
                "n_episodes",
                "battery_rank",
                "collapse",
                "median_duration",
                "frac_ret_clear",
                "frac_time_clear",
                "censored_frac",
                "mde_bps",
                "lift_ci_low_seed_range_lo",
                "lift_ci_low_seed_range_hi",
            ]
        )
    )


def main() -> None:
    integ = load_integrity()
    assert integ.get("all_pass") is True, "integrity not all_pass"
    assert integ.get("pass_count") == 12, integ.get("pass_count")

    pin = load_unit_pin()
    spreads = {k: float(v) for k, v in pin["train_median_spread_bps"].items()}

    df = with_flags(load_cells())
    assert df.height == 3240, df.height
    assert int(df["is_primary_promote"].sum()) == 640
    assert (df["primary_unit"] == "bps_per_episode").all()
    assert df["is_treatment"].all()

    full = df
    prim = df.filter(pl.col("is_primary_promote"))
    assert prim.height == 640

    # Facets — primary binding + full disclosure
    facets_prim = summarize_facets(prim).with_columns(
        pl.lit("primary").alias("slice")
    )
    facets_full = summarize_facets(full).with_columns(pl.lit("full").alias("slice"))
    facets = pl.concat([facets_prim, facets_full], how="diagonal_relaxed")
    facets.write_parquet(OUT / "analyst_facets.parquet")
    facets.write_csv(OUT / "analyst_facets.csv")

    clusters = detect_clusters(prim)
    clusters.write_parquet(OUT / "analyst_clusters_k3.parquet")
    clusters.write_csv(OUT / "analyst_clusters_k3.csv")

    floors = money_floor_table(prim, spreads)
    floors.write_parquet(OUT / "analyst_money_floor.parquet")
    floors.write_csv(OUT / "analyst_money_floor.csv")

    path = path_diagnostics(prim)
    path.write_parquet(OUT / "analyst_path_diag.parquet")
    path.write_csv(OUT / "analyst_path_diag.csv")

    top = top_promote_cells(prim, 60)
    top.write_parquet(OUT / "analyst_top_promote.parquet")
    top.write_csv(OUT / "analyst_top_promote.csv")

    pos = prim.filter(pl.col("lift_ci_pos")).sort("lift_bps", descending=True)
    pos.write_parquet(OUT / "analyst_lift_ci_pos.parquet")
    pos.write_csv(OUT / "analyst_lift_ci_pos.csv")

    days = membership_summary()
    days.write_parquet(OUT / "analyst_membership_days.parquet")
    days.write_csv(OUT / "analyst_membership_days.csv")

    vr = vr_analysis()
    gt = grid_twin_analysis()
    cens = censoring_analysis(full, prim)

    # Control B on promote candidates
    cand = prim.filter(pl.col("promote_cand"))
    coll_ok = cand.filter(pl.col("collapse").is_not_null())

    # Money: promote cand above floor
    fl_cand = floors.filter(pl.col("promote_cand"))
    n_mean_above = int(fl_cand["mean_above_floor"].sum()) if fl_cand.height else 0
    n_lift_above = int(fl_cand["lift_above_floor"].sum()) if fl_cand.height else 0

    # K=3 clusters at key grains
    cl_odc = clusters.filter(
        (pl.col("grain") == "object×domain×clear") & pl.col("k3_cluster_ge3")
    ).sort("med_lift_bps", descending=True)
    cl_od = clusters.filter(
        (pl.col("grain") == "object×domain") & pl.col("k3_cluster_ge3")
    ).sort("med_lift_bps", descending=True)
    cl_sym = clusters.filter(
        (pl.col("grain") == "symbol×object×domain") & pl.col("k3_cluster_ge3")
    ).sort("n_member_cells", descending=True)

    # Symbol heterogeneity primary
    by_sym = (
        prim.group_by("symbol")
        .agg(
            [
                pl.len().alias("n"),
                pl.col("unpowered").sum().alias("n_unpowered"),
                pl.col("lift_ci_pos").sum().alias("n_lift_ci_pos"),
                pl.col("promote_cand").sum().alias("n_promote_cand"),
                pl.col("mean_bps").median().alias("med_mean"),
                pl.col("lift_bps").median().alias("med_lift"),
                pl.col("collapse").median().alias("med_collapse"),
                pl.col("battery_rank").median().alias("med_rank"),
            ]
        )
        .sort("n_promote_cand", descending=True)
    )

    # Battery rank distribution on primary
    rank_stats = {
        "med_battery_rank_primary": med(prim["battery_rank"]),
        "med_battery_rank_promote_cand": med(cand["battery_rank"])
        if cand.height
        else float("nan"),
        "n_rank_ge_0_9_primary": int(
            (prim["battery_rank"].is_finite() & (prim["battery_rank"] >= 0.9)).sum()
        ),
        "n_rank_ge_0_8_primary": int(
            (prim["battery_rank"].is_finite() & (prim["battery_rank"] >= 0.8)).sum()
        ),
        "n_rank_ge_0_9_promote_cand": int(
            (cand["battery_rank"].is_finite() & (cand["battery_rank"] >= 0.9)).sum()
        )
        if cand.height
        else 0,
    }

    # Seed fragility on promote cand
    n_seed_straddle_cand = (
        int(cand["lift_seed_band_straddles_0"].sum()) if cand.height else 0
    )

    # Duration hours for cluster medians (15m domain bars)
    def bars_to_hours(bars: float, domain: str) -> float:
        if not np.isfinite(bars):
            return float("nan")
        return bars * domain_minutes(domain) / 60.0

    # Per-symbol money floors at measured median episode length of promote cand
    floor_by_sym = []
    for sym, spr in spreads.items():
        sub = cand.filter(pl.col("symbol") == sym) if cand.height else prim.filter(
            pl.col("symbol") == sym
        )
        if sub.height == 0:
            sub = prim.filter(pl.col("symbol") == sym)
        med_dur = med(sub["median_duration"])
        # use domain of majority promote cand for this symbol if any
        if sub.height and "domain" in sub.columns:
            dom_mode = (
                sub.group_by("domain")
                .agg(pl.len().alias("n"))
                .sort("n", descending=True)["domain"][0]
            )
        else:
            dom_mode = "15m"
        hold_h = bars_to_hours(med_dur, dom_mode)
        floor_by_sym.append(
            {
                "symbol": sym,
                "spread_bps": spr,
                "floor_2h": cost_floor_bps(spr, 2.0),
                "floor_8h": cost_floor_bps(spr, 8.0),
                "floor_24h": cost_floor_bps(spr, 24.0),
                "floor_at_med_episode_h": cost_floor_bps(spr, hold_h)
                if np.isfinite(hold_h)
                else float("nan"),
                "med_episode_hours_promote_or_all": hold_h,
                "med_duration_bars": med_dur,
                "domain_mode": dom_mode,
            }
        )

    # Structure identity: compare cluster med lifts vs grid twin
    structure_ok = (
        cl_odc.height > 0
        and med(pl.Series([r["med_lift_bps"] for r in cl_odc.to_dicts()]))
        > gt["med_mean_bps"]
        if cl_odc.height
        else False
    )

    # Promote-rule checklist (factual, not disposition stamp)
    has_k3 = cl_odc.height > 0 or cl_od.height > 0
    neighbourhood = (
        int(cl_odc.filter(pl.col("neighbourhood_ok")).height) > 0
        if cl_odc.height
        else False
    )
    collapse_ok = (
        cand.height > 0
        and int((coll_ok["collapse"] >= 0.5).sum()) == coll_ok.height
        if coll_ok.height
        else False
    )
    # money: cluster med mean vs floor
    money_notes = []
    for r in cl_odc.head(8).to_dicts():
        # rough floor: use 8h if 15m cluster else 8h
        domain = "15m" if "15m" in r["region"] else ("1h" if "1h" in r["region"] else "15m")
        # med duration bars → hours
        hold_h = bars_to_hours(r["med_median_duration_bars"], domain)
        # use median spread across symbols in cluster
        syms = r["symbols"].split(",") if r["symbols"] else list(spreads.keys())
        sprs = [spreads[s] for s in syms if s in spreads]
        med_spr = float(np.median(sprs)) if sprs else float("nan")
        fl = cost_floor_bps(med_spr, hold_h) if np.isfinite(hold_h) else float("nan")
        money_notes.append(
            {
                "region": r["region"],
                "med_mean_bps": r["med_mean_bps"],
                "med_lift_bps": r["med_lift_bps"],
                "hold_hours": hold_h,
                "med_spread": med_spr,
                "floor_bps": fl,
                "med_mean_above_floor": bool(
                    np.isfinite(r["med_mean_bps"])
                    and np.isfinite(fl)
                    and r["med_mean_bps"] > fl
                ),
                "n_cells": r["n_member_cells"],
                "n_symbols": r["n_symbols"],
            }
        )

    headline = {
        "experiment": "SPDR-005",
        "family": "CF-EPSOSC-001",
        "amendments": ["AMENDMENT-1"],
        "integrity_pass_count": integ["pass_count"],
        "integrity_all_pass": integ["all_pass"],
        "golden": {k: v.get("ok") for k, v in integ.get("golden", {}).items()},
        "n_treatment": full.height,
        "n_primary_promote": prim.height,
        "primary_unit": "bps_per_episode",
        "full": {
            "med_mean_bps": med(full["mean_bps"]),
            "med_lift_bps": med(full["lift_bps"]),
            "n_lift_ci_pos": int(full["lift_ci_pos"].sum()),
            "n_lift_ci_pos_powered": int(
                (full["lift_ci_pos"] & ~full["unpowered"]).sum()
            ),
            "n_unpowered": int(full["unpowered"].sum()),
            "n_censored_flag_gt20": int(full["censored_flag_gt20"].sum()),
        },
        "primary": {
            "med_mean_bps": med(prim["mean_bps"]),
            "med_lift_bps": med(prim["lift_bps"]),
            "n_lift_ci_pos": int(prim["lift_ci_pos"].sum()),
            "n_lift_ci_pos_powered": int(
                (prim["lift_ci_pos"] & ~prim["unpowered"]).sum()
            ),
            "n_promote_cand": cand.height,
            "n_unpowered": int(prim["unpowered"].sum()),
            "n_lift_ci_neg": int(prim["lift_ci_neg"].sum()),
            "n_mean_ci_pos": int(prim["mean_ci_pos"].sum()),
            "med_collapse_promote_cand": med(cand["collapse"].drop_nulls())
            if cand.height
            else float("nan"),
            "n_collapse_ge_0_5_promote": int((coll_ok["collapse"] >= 0.5).sum())
            if coll_ok.height
            else 0,
            "n_collapse_ge_0_8_promote": int((coll_ok["collapse"] >= 0.8).sum())
            if coll_ok.height
            else 0,
            "n_collapse_lt_0_2_promote": int((coll_ok["collapse"] < 0.2).sum())
            if coll_ok.height
            else 0,
            "frac_collapse_ge_0_5_promote": (
                float((coll_ok["collapse"] >= 0.5).sum()) / coll_ok.height
                if coll_ok.height
                else float("nan")
            ),
            "n_seed_band_straddle_promote": n_seed_straddle_cand,
            "n_mean_above_floor_promote": n_mean_above,
            "n_lift_above_floor_promote": n_lift_above,
            "n_promote_with_floor": fl_cand.height,
        },
        "primary_by_domain": facets_prim.filter(pl.col("facet") == "domain")
        .select(
            [
                "level",
                "n_cells",
                "n_powered",
                "n_promote_cand",
                "n_lift_ci_pos",
                "med_mean_bps",
                "med_lift_bps",
                "med_collapse_promote_cand",
                "med_battery_rank",
                "n_unpowered",
            ]
        )
        .to_dicts(),
        "primary_by_object": facets_prim.filter(pl.col("facet") == "object")
        .select(
            [
                "level",
                "n_cells",
                "n_promote_cand",
                "med_mean_bps",
                "med_lift_bps",
                "n_unpowered",
            ]
        )
        .to_dicts(),
        "primary_by_side": facets_prim.filter(pl.col("facet") == "side")
        .select(
            [
                "level",
                "n_cells",
                "n_promote_cand",
                "med_mean_bps",
                "med_lift_bps",
            ]
        )
        .to_dicts(),
        "primary_by_clear": facets_prim.filter(pl.col("facet") == "clear")
        .select(
            [
                "level",
                "n_cells",
                "n_promote_cand",
                "med_mean_bps",
                "med_lift_bps",
                "med_censored_frac",
                "n_censored_flag_gt20",
            ]
        )
        .to_dicts(),
        "primary_by_object_domain_clear": facets_prim.filter(
            pl.col("facet") == "object×domain×clear"
        )
        .select(
            [
                "level",
                "n_cells",
                "n_promote_cand",
                "n_lift_ci_pos_powered",
                "med_mean_bps",
                "med_lift_bps",
                "med_collapse_promote_cand",
                "n_collapse_ge_0_5_promote",
            ]
        )
        .sort("n_promote_cand", descending=True)
        .to_dicts(),
        "battery_rank": rank_stats,
        "clusters_k3_object_domain_clear": cl_odc.to_dicts(),
        "clusters_k3_object_domain": cl_od.to_dicts(),
        "clusters_k3_symbol_object_domain": cl_sym.head(20).to_dicts(),
        "n_k3_regions_odc": cl_odc.height,
        "n_k3_regions_od": cl_od.height,
        "n_k3_regions_sym": cl_sym.height,
        "by_symbol_primary": by_sym.to_dicts(),
        "vr": vr,
        "grid_twin": {
            "med_mean_bps": gt["med_mean_bps"],
            "n_positive": gt["n_positive"],
            "by_domain": gt["by_domain"],
            "top_positive": gt["top_positive"],
            "structure_identity_clusters_exist_and_not_sole_grid": bool(
                has_k3 and not (gt["n_positive"] > 0 and cl_odc.height == 0)
            ),
        },
        "censoring": cens,
        "money_floor_by_symbol": floor_by_sym,
        "money_cluster_notes": money_notes,
        "promote_rule_factual": {
            "has_k3_cluster_odc_or_od": has_k3,
            "neighbourhood_ok": neighbourhood,
            "control_b_collapse_all_promote_ge_0_5": collapse_ok,
            "vr_flat": vr["vr_flat_primary_domains"],
            "vr_coupling_note": vr["coupling_note"],
            "grid_twin_not_sole_positive": bool(
                has_k3  # treatment clusters exist
            ),
            "any_cluster_med_mean_above_floor": any(
                m["med_mean_above_floor"] for m in money_notes
            ),
            "structure_ok_heuristic": structure_ok,
        },
        "membership_top": days.head(15).to_dicts(),
        "top_promote_cells": top.head(25).to_dicts(),
        "path_diag_clear": path.filter(pl.col("grain") == "clear").to_dicts(),
        "path_diag_odc": path.filter(pl.col("grain") == "object×domain×clear")
        .sort("med_median_duration_bars")
        .to_dicts(),
        "spreads_measured": spreads,
        "fee_rt_taker_bps": FEE_RT_TAKER_BPS,
        "note": (
            "K=3 uses primary promote slice only (640). "
            "Pooled full-grid medians are disclosure-only. "
            "Disposition recommendation is in analysis.md, not here."
        ),
    }

    (OUT / "analyst_headline.json").write_text(
        json.dumps(headline, indent=2, default=str)
    )

    # Also dump VR and grid twin tables
    pl.DataFrame(vr["by_domain_lag"]).write_csv(OUT / "analyst_vr_by_domain_lag.csv")
    pl.read_parquet(RES / "grid_twin.parquet").write_csv(OUT / "analyst_grid_twin.csv")
    pl.DataFrame(cens["blocks"]).write_csv(OUT / "analyst_censoring.csv")

    print("=== SPDR-005 analyst re-derive ===")
    print(f"integrity {integ['pass_count']}/12 all_pass={integ['all_pass']}")
    print(f"full={full.height} primary={prim.height}")
    print(
        f"full med_mean={headline['full']['med_mean_bps']:.3f} "
        f"med_lift={headline['full']['med_lift_bps']:.3f} "
        f"CI+={headline['full']['n_lift_ci_pos']} unpowered={headline['full']['n_unpowered']}"
    )
    print(
        f"primary med_mean={headline['primary']['med_mean_bps']:.3f} "
        f"med_lift={headline['primary']['med_lift_bps']:.3f} "
        f"promote_cand={headline['primary']['n_promote_cand']} "
        f"unpowered={headline['primary']['n_unpowered']}"
    )
    print(
        f"collapse med promote={headline['primary']['med_collapse_promote_cand']:.3f} "
        f">=0.5: {headline['primary']['n_collapse_ge_0_5_promote']}/"
        f"{headline['primary']['n_promote_cand']}"
    )
    print("primary by domain:")
    print(facets_prim.filter(pl.col("facet") == "domain"))
    print("primary by object×domain×clear (top promote):")
    print(
        facets_prim.filter(pl.col("facet") == "object×domain×clear").sort(
            "n_promote_cand", descending=True
        )
    )
    print(f"K3 odc regions: {cl_odc.height}")
    print(cl_odc.select(["region", "n_member_cells", "n_symbols", "n_k", "n_w",
                          "med_lift_bps", "med_mean_bps", "med_collapse"]))
    print(f"VR flat={vr['vr_flat_primary_domains']} half_rule={vr['half_symbol_rule']}")
    print(f"GRID_TWIN med={gt['med_mean_bps']:.3f} n_pos={gt['n_positive']}")
    print(
        f"money promote mean>floor: {n_mean_above}/{fl_cand.height}; "
        f"lift>floor: {n_lift_above}/{fl_cand.height}"
    )
    print("promote_rule_factual:", json.dumps(headline["promote_rule_factual"], indent=2))
    print("wrote results/analyst_*.{parquet,csv,json}")


if __name__ == "__main__":
    main()
