"""SPDR-006 fresh-context analyst emissions — re-derive from results/*.parquet.

CF-HTFCAP-001 vol-regime facet (VOL_HI / VOL_LO / DI×VOL_HI / DI_ADX×VOL_HI).
Does NOT import screen_code for verdict-bearing numbers. SPDR-004 DI/DI_ADX cells
are read-only via amplifier_vs_spdr004.parquet (no re-run).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

EXP = Path(__file__).resolve().parents[1]
RES = EXP / "results"
OUT = RES

FILTERS = ["VOL_HI", "VOL_LO", "DI×VOL_HI", "DI_ADX×VOL_HI"]
INTERACTION = ["DI×VOL_HI", "DI_ADX×VOL_HI"]
DOMAINS = ["1h/5m", "4h/15m", "1d/1h"]
PRIMARY = [
    "BTCUSDT",
    "SOLUSDT",
    "ETHUSDT",
    "XRPUSDT",
    "OPUSDT",
    "DOGEUSDT",
    "1000PEPEUSDT",
    "APTUSDT",
    "LTCUSDT",
    "LINKUSDT",
]


def load_cells() -> pl.DataFrame:
    return pl.read_parquet(RES / "cells.parquet")


def load_amp() -> pl.DataFrame:
    return pl.read_parquet(RES / "amplifier_vs_spdr004.parquet")


def load_unit_pin() -> dict:
    return json.loads((RES / "unit_pin.json").read_text())


def build_floor_map(pin: dict) -> dict[tuple[str, str, float], float]:
    """(symbol, domain, hold_mult) -> total_bps measured floor."""
    out: dict[tuple[str, str, float], float] = {}
    for e in pin.get("money_unit_floor_examples", []):
        out[(e["symbol"], e["domain"], float(e["hold_mult"]))] = float(
            e["cost_proxy"]["total_bps"]
        )
    return out


def treatment(df: pl.DataFrame) -> pl.DataFrame:
    return df.filter(pl.col("is_treatment") & pl.col("primary_stratum"))


def with_flags(t: pl.DataFrame) -> pl.DataFrame:
    return t.with_columns(
        [
            (pl.col("lift_ci_low").is_finite() & (pl.col("lift_ci_low") > 0)).alias(
                "lift_ci_pos"
            ),
            (pl.col("lift_ci_high").is_finite() & (pl.col("lift_ci_high") < 0)).alias(
                "lift_ci_neg"
            ),
            (pl.col("ci_low").is_finite() & (pl.col("ci_low") > 0)).alias("mean_ci_pos"),
            (pl.col("ci_high").is_finite() & (pl.col("ci_high") < 0)).alias(
                "mean_ci_neg"
            ),
            (pl.col("lift_bps").is_finite() & (pl.col("lift_bps") > 0)).alias(
                "lift_pos"
            ),
            (pl.col("mean_bps").is_finite() & (pl.col("mean_bps") > 0)).alias(
                "mean_pos"
            ),
            (
                pl.col("lift_ci_low_seed_range_lo").is_finite()
                & pl.col("lift_ci_low_seed_range_hi").is_finite()
                & (pl.col("lift_ci_low_seed_range_lo") < 0)
                & (pl.col("lift_ci_low_seed_range_hi") > 0)
            ).alias("lift_seed_band_straddles_0"),
            (
                (
                    (pl.col("block_sens_half_ci_low") > 0).cast(pl.Int8)
                    + (pl.col("block_sens_1x_ci_low") > 0).cast(pl.Int8)
                    + (pl.col("block_sens_2x_ci_low") > 0).cast(pl.Int8)
                ).is_in([1, 2])
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
                "n_seed_band_straddle": g.filter(
                    pl.col("lift_seed_band_straddles_0")
                ).height,
                "n_block_sens_fragile": g.filter(
                    pl.col("block_sens_sign_fragile")
                ).height,
                "med_mean_bps": med(g["mean_bps"]),
                "med_lift_bps": med(g["lift_bps"]),
                "med_n_trades": med(g["n_trades"].cast(pl.Float64)),
                "med_collapse": med(g["collapse"].drop_nulls())
                if g["collapse"].drop_nulls().len()
                else float("nan"),
                "med_collapse_lift_ci_pos": med(lift_ci["collapse"].drop_nulls())
                if lift_ci.height and lift_ci["collapse"].drop_nulls().len()
                else float("nan"),
                "med_collapse_lift_ci_pos_powered": med(
                    lift_ci_pow["collapse"].drop_nulls()
                )
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
    return t.filter(pl.col("lift_ci_pos")).sort(
        ["domain", "htf_filter", "base", "symbol", "hold_mult"]
    )


def detect_clusters(t: pl.DataFrame, floors: dict) -> pl.DataFrame:
    """K=3 promote-rule cluster scan on THIS grid only (no SPDR-004 pooling)."""
    rows = []
    for domain in DOMAINS:
        for filt in FILTERS:
            g = t.filter(
                (pl.col("domain") == domain) & (pl.col("htf_filter") == filt)
            )
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
                n_coll_ge_0_5 = (
                    int((sub["collapse"].drop_nulls() >= 0.5).sum()) if n else 0
                )
                n_coll_ge_0_8 = (
                    int((sub["collapse"].drop_nulls() >= 0.8).sum()) if n else 0
                )
                n_coll_lt_0_2 = (
                    int((sub["collapse"].drop_nulls() < 0.2).sum()) if n else 0
                )
                best_lift = float(sub["lift_bps"].max()) if n else float("nan")
                sole = n == 1
                n_seed_straddle = (
                    int(sub["lift_seed_band_straddles_0"].sum()) if n else 0
                )
                floor_vals = []
                n_mean_above_own_floor = 0
                if n:
                    for r in sub.iter_rows(named=True):
                        fl = floors.get(
                            (r["symbol"], domain, float(r["hold_mult"])),
                            float("nan"),
                        )
                        if np.isfinite(fl):
                            floor_vals.append(fl)
                        if (
                            np.isfinite(r["mean_bps"])
                            and np.isfinite(fl)
                            and r["mean_bps"] > fl
                        ):
                            n_mean_above_own_floor += 1
                floor_min = float(np.min(floor_vals)) if floor_vals else float("nan")
                floor_max = float(np.max(floor_vals)) if floor_vals else float("nan")
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
    return t.select(
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
    ).sort(["domain", "base", "htf_filter", "symbol", "hold_mult"])


def money_floor_table(t: pl.DataFrame, floors: dict) -> pl.DataFrame:
    rows = []
    for r in t.iter_rows(named=True):
        fl = floors.get(
            (r["symbol"], r["domain"], float(r["hold_mult"])), float("nan")
        )
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
                "mean_above_floor": bool(np.isfinite(mean) and np.isfinite(fl) and mean > fl),
                "lift_above_floor": bool(np.isfinite(lift) and np.isfinite(fl) and lift > fl),
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


def base_conditional(t: pl.DataFrame) -> pl.DataFrame:
    rows = []
    for key, g in t.group_by(
        ["domain", "base", "htf_filter", "hold_mult"], maintain_order=True
    ):
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


def amplifier_table(amp: pl.DataFrame) -> pl.DataFrame:
    a = amp.with_columns(
        [
            (pl.col("lift_ci_low").is_finite() & (pl.col("lift_ci_low") > 0)).alias(
                "lift_ci_pos"
            ),
            (pl.col("amp_lift_minus_frozen_lift") > 0).alias("amp_lift_pos"),
            (pl.col("amp_mean_minus_frozen_mean") > 0).alias("amp_mean_pos"),
            (
                pl.col("frozen_lift_ci_low").is_finite()
                & (pl.col("frozen_lift_ci_low") > 0)
            ).alias("frozen_lift_ci_pos"),
        ]
    )
    return a.sort(["domain", "htf_filter", "base", "symbol", "hold_mult"])


def amplifier_facets(a: pl.DataFrame) -> pl.DataFrame:
    rows = []

    def add(label: str, key: str, g: pl.DataFrame) -> None:
        cip = g.filter(pl.col("lift_ci_pos") & ~pl.col("unpowered"))
        rows.append(
            {
                "facet": label,
                "level": str(key),
                "n_rows": g.height,
                "n_lift_ci_pos_powered": cip.height,
                "n_amp_lift_pos": g.filter(pl.col("amp_lift_pos")).height,
                "n_amp_lift_pos_on_ci_pow": cip.filter(pl.col("amp_lift_pos")).height
                if cip.height
                else 0,
                "med_amp_lift_delta": med(g["amp_lift_minus_frozen_lift"]),
                "med_amp_lift_delta_ci_pow": med(cip["amp_lift_minus_frozen_lift"])
                if cip.height
                else float("nan"),
                "med_interaction_lift": med(g["lift_bps"]),
                "med_frozen_lift": med(g["frozen_lift_bps"]),
                "med_interaction_lift_ci_pow": med(cip["lift_bps"])
                if cip.height
                else float("nan"),
                "med_frozen_lift_ci_pow": med(cip["frozen_lift_bps"])
                if cip.height
                else float("nan"),
            }
        )

    for col, label in [
        ("htf_filter", "htf_filter"),
        ("base", "base"),
        ("domain", "domain"),
        ("hold_mult", "hold_mult"),
        ("symbol", "symbol"),
    ]:
        for key, g in a.group_by(col, maintain_order=True):
            k = key[0] if isinstance(key, tuple) else key
            add(label, k, g)

    for key, g in a.group_by(["domain", "base", "htf_filter"], maintain_order=True):
        add("domain×base×filter", f"{key[0]}|{key[1]}×{key[2]}", g)

    return pl.DataFrame(rows)


def promote_ladders(t: pl.DataFrame, floors: dict) -> pl.DataFrame:
    """Hold ladders for promote-facing UNF interaction cells on majors."""
    rows = []
    specs = [
        ("BTCUSDT", "4h/15m", "UNF", "DI×VOL_HI"),
        ("BTCUSDT", "4h/15m", "UNF", "DI_ADX×VOL_HI"),
        ("SOLUSDT", "4h/15m", "UNF", "DI×VOL_HI"),
        ("SOLUSDT", "4h/15m", "UNF", "DI_ADX×VOL_HI"),
        ("ETHUSDT", "4h/15m", "UNF", "DI_ADX×VOL_HI"),
        ("SOLUSDT", "4h/15m", "UNF", "VOL_HI"),
        ("SOLUSDT", "4h/15m", "UNF", "VOL_LO"),
        ("BTCUSDT", "4h/15m", "UNF", "VOL_HI"),
        ("BTCUSDT", "4h/15m", "UNF", "VOL_LO"),
    ]
    for sym, domain, base, filt in specs:
        g = t.filter(
            (pl.col("symbol") == sym)
            & (pl.col("domain") == domain)
            & (pl.col("base") == base)
            & (pl.col("htf_filter") == filt)
        ).sort("hold_mult")
        for r in g.iter_rows(named=True):
            fl = floors.get((sym, domain, float(r["hold_mult"])), float("nan"))
            rows.append(
                {
                    "label": f"{sym}|{domain}|{base}|{filt}",
                    "symbol": sym,
                    "domain": domain,
                    "base": base,
                    "htf_filter": filt,
                    "hold_mult": r["hold_mult"],
                    "mean_bps": r["mean_bps"],
                    "lift_bps": r["lift_bps"],
                    "lift_ci_low": r["lift_ci_low"],
                    "lift_ci_high": r["lift_ci_high"],
                    "n_trades": r["n_trades"],
                    "unpowered": r["unpowered"],
                    "collapse": r["collapse"],
                    "baseline_mean_bps": r["baseline_mean_bps"],
                    "phaseshift_mean_bps": r["phaseshift_mean_bps"],
                    "lift_ci_low_seed_range_lo": r["lift_ci_low_seed_range_lo"],
                    "lift_ci_low_seed_range_hi": r["lift_ci_low_seed_range_hi"],
                    "cost_floor_bps": fl,
                    "mean_minus_floor": r["mean_bps"] - fl
                    if np.isfinite(r["mean_bps"]) and np.isfinite(fl)
                    else float("nan"),
                    "lift_ci_pos": bool(
                        np.isfinite(r["lift_ci_low"]) and r["lift_ci_low"] > 0
                    ),
                }
            )
    return pl.DataFrame(rows)


def main() -> None:
    pin = load_unit_pin()
    floors = build_floor_map(pin)
    integrity = json.loads((RES / "integrity.json").read_text())
    assert integrity.get("all_pass") is True
    assert integrity.get("pass_count") == 14

    df = load_cells()
    t = with_flags(treatment(df))
    assert t.height == 1440, t.height
    assert t.filter(pl.col("htf_filter").is_in(["DI", "DI_ADX"])).height == 0

    methods = set(t["lift_ci_method"].drop_nulls().unique().to_list())
    allowed = {
        "two_sample_block",
        "two_sample_block_vs_battery",
        "two_sample_seed_means",
    }
    banned = {"battery_minus_seeds", "treatment_ci_minus_fixed_baseline"}
    assert methods <= allowed, f"unexpected lift_ci_method: {methods}"
    assert not (methods & banned), f"banned lift_ci_method present: {methods & banned}"

    # L-20 mean-CI fields finite on all cells; lift CI may be NaN on n=1 unpowered tails
    for col in [
        "block_h_ci_low",
        "ci_low_seed_range_lo",
        "block_sens_half_ci_low",
        "lift_block",
    ]:
        n_fin = int(t[col].is_finite().sum())
        assert n_fin == t.height, f"L-20 missing finite {col}: {n_fin}/{t.height}"
    powered = t.filter(~pl.col("unpowered"))
    for col in ["lift_ci_low", "lift_ci_low_seed_range_lo"]:
        n_fin = int(powered[col].is_finite().sum())
        assert n_fin == powered.height, (
            f"L-20 missing finite {col} on powered: {n_fin}/{powered.height}"
        )
    n_lift_nan = int((~t["lift_ci_low"].is_finite()).sum())
    assert n_lift_nan <= 16, f"unexpected lift_ci NaN mass: {n_lift_nan}"

    facets = summarize_facets(t)
    facets.write_parquet(OUT / "analyst_facets.parquet")
    facets.write_csv(OUT / "analyst_facets.csv")

    pos = positive_lift_cells(t)
    pos.write_parquet(OUT / "analyst_lift_ci_pos.parquet")
    pos.write_csv(OUT / "analyst_lift_ci_pos.csv")

    clusters = detect_clusters(t, floors)
    clusters.write_parquet(OUT / "analyst_clusters_k3.parquet")
    clusters.write_csv(OUT / "analyst_clusters_k3.csv")

    ladder = hold_ladder(t)
    ladder.write_parquet(OUT / "analyst_hold_ladder.parquet")
    ladder.write_csv(OUT / "analyst_hold_ladder.csv")

    fl_tbl = money_floor_table(t, floors)
    fl_tbl.write_parquet(OUT / "analyst_money_floor.parquet")
    fl_tbl.write_csv(OUT / "analyst_money_floor.csv")

    coll = collapse_table(t)
    coll.write_parquet(OUT / "analyst_control_c.parquet")
    coll.write_csv(OUT / "analyst_control_c.csv")

    bc = base_conditional(t)
    bc.write_parquet(OUT / "analyst_base_conditional.parquet")
    bc.write_csv(OUT / "analyst_base_conditional.csv")

    amp_raw = load_amp()
    assert amp_raw.height == 720, amp_raw.height
    amp = amplifier_table(amp_raw)
    amp.write_parquet(OUT / "analyst_amplifier.parquet")
    amp.write_csv(OUT / "analyst_amplifier.csv")

    amp_fac = amplifier_facets(amp)
    amp_fac.write_parquet(OUT / "analyst_amplifier_facets.parquet")
    amp_fac.write_csv(OUT / "analyst_amplifier_facets.csv")

    prom = promote_ladders(t, floors)
    prom.write_parquet(OUT / "analyst_promote_ladders.parquet")
    prom.write_csv(OUT / "analyst_promote_ladders.csv")

    lift_ci = t.filter(pl.col("lift_ci_pos"))
    lift_ci_pow = lift_ci.filter(~pl.col("unpowered"))
    clusters_ge3 = clusters.filter(
        pl.col("k3_cluster_ge3") & (pl.col("base_scope") != "ALL_BASES")
    )

    fl_pos = fl_tbl.filter(
        pl.col("lift_ci_excludes_zero")
        & ~pl.col("unpowered")
        & pl.col("mean_bps").is_finite()
    )
    n_mean_above = int(fl_pos["mean_above_floor"].sum()) if fl_pos.height else 0
    n_lift_above = int(fl_pos["lift_above_floor"].sum()) if fl_pos.height else 0

    amp_cip = amp.filter(pl.col("lift_ci_pos") & ~pl.col("unpowered"))
    amp_pos_on_cip = (
        int(amp_cip.filter(pl.col("amp_lift_pos")).height) if amp_cip.height else 0
    )

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
    by_filt = (
        t.group_by("htf_filter")
        .agg(
            [
                pl.len().alias("n"),
                pl.col("unpowered").sum().alias("n_unpowered"),
                pl.col("lift_ci_pos").sum().alias("n_lift_ci_pos"),
                (pl.col("lift_ci_pos") & ~pl.col("unpowered"))
                .sum()
                .alias("n_lift_ci_pos_powered"),
                pl.col("mean_bps").median().alias("med_mean"),
                pl.col("lift_bps").median().alias("med_lift"),
            ]
        )
        .sort("htf_filter")
    )

    coll_pos = lift_ci_pow.filter(pl.col("collapse").is_not_null())
    coll_arr = coll_pos["collapse"].to_numpy()
    coll_arr = coll_arr[np.isfinite(coll_arr)]

    headline = {
        "screen": "SPDR-006",
        "integrity": "PASS 14/14",
        "membership_byte_identical_to_spdr004": integrity.get(
            "membership_byte_identical_to_spdr004"
        ),
        "membership_sha256": integrity.get("membership_sha256"),
        "n_treatment": t.height,
        "n_unpowered": int(t.filter(pl.col("unpowered")).height),
        "n_powered": int(t.filter(~pl.col("unpowered")).height),
        "med_mean_bps": med(t["mean_bps"]),
        "med_lift_bps": med(t["lift_bps"]),
        "n_lift_ci_pos": lift_ci.height,
        "n_lift_ci_pos_powered": lift_ci_pow.height,
        "n_lift_ci_neg": int(t.filter(pl.col("lift_ci_neg")).height),
        "lift_ci_methods": sorted(methods),
        "battery_minus_seeds_count": 0,
        "di_only_treatment_count": 0,
        "by_base": by_base.to_dicts(),
        "by_htf_filter": by_filt.to_dicts(),
        "control_c_powered_ci_pos": {
            "n": int(len(coll_arr)),
            "med_collapse": float(np.median(coll_arr)) if len(coll_arr) else None,
            "frac_ge_0_5": float((coll_arr >= 0.5).mean()) if len(coll_arr) else None,
            "frac_ge_0_8": float((coll_arr >= 0.8).mean()) if len(coll_arr) else None,
            "n_lt_0_2": int((coll_arr < 0.2).sum()) if len(coll_arr) else 0,
        },
        "money_floor_powered_ci_pos": {
            "n": fl_pos.height,
            "n_mean_above_own_floor": n_mean_above,
            "n_lift_above_own_floor": n_lift_above,
            "spread_source": "unit_pin measured TRAIN-median SpreadBps (not GAP=2)",
        },
        "amplifier": {
            "n_rows": amp.height,
            "n_powered_ci_pos": amp_cip.height,
            "n_amp_lift_gt_frozen_on_powered_ci_pos": amp_pos_on_cip,
            "frac_amp_pos_on_powered_ci_pos": amp_pos_on_cip / amp_cip.height
            if amp_cip.height
            else None,
            "med_amp_lift_delta_all": med(amp["amp_lift_minus_frozen_lift"]),
            "med_amp_lift_delta_powered_ci_pos": med(
                amp_cip["amp_lift_minus_frozen_lift"]
            )
            if amp_cip.height
            else None,
            "med_interaction_lift_powered_ci_pos": med(amp_cip["lift_bps"])
            if amp_cip.height
            else None,
            "med_frozen_lift_powered_ci_pos": med(amp_cip["frozen_lift_bps"])
            if amp_cip.height
            else None,
        },
        "k3_clusters_per_base_ge3": clusters_ge3.filter(
            pl.col("n_member_cells") >= 3
        ).to_dicts(),
        "train_median_spread_bps": pin.get("train_median_spread_bps"),
        "note": (
            "Pooled figures disclosure-only. K=3 on THIS grid only. "
            "No disposition stamp in this artifact."
        ),
    }
    (OUT / "analyst_headline.json").write_text(json.dumps(headline, indent=2) + "\n")
    print(
        f"SPDR-006 analyst: treat={t.height} CI+={lift_ci.height} "
        f"CI+pow={lift_ci_pow.height} amp_cip={amp_cip.height} "
        f"amp_pos={amp_pos_on_cip} k3_rows={clusters_ge3.height}"
    )


if __name__ == "__main__":
    main()
