"""SPDR-012 summary tables — neutral quantification for screen.md / analysis.md.

Reads only the emitted screen artifacts (no re-derivation of the estimand) and prints the
per-stratum tables the design requires: coverage, V-LEVEL primary IC by cell, regime gaps,
tails, cross-section, calendar, controls, stability, and the design §6.4 PASS/STOP clauses.

Every money figure is bps under PARTIAL_FEES_FUNDING_ONLY (spread unavailable, not charged).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

EXP = Path(__file__).resolve().parents[1]
RES = EXP / "results"

pl.Config.set_tbl_rows(200)
pl.Config.set_tbl_cols(30)
pl.Config.set_fmt_str_lengths(60)
pl.Config.set_tbl_width_chars(200)


def load() -> tuple[pl.DataFrame, dict, dict, dict]:
    m = pl.read_parquet(RES / "metrics_by_cell.parquet")
    controls = json.loads((RES / "controls.json").read_text())
    diags = json.loads((RES / "cell_diagnostics.json").read_text())
    check = json.loads((RES / "integrity_selfcheck.json").read_text())
    return m, controls, diags, check


def coverage(diags: dict) -> pl.DataFrame:
    rows = []
    for key, d in diags["cells"].items():
        sym, clock = key.split("|")
        rows.append({
            "symbol": sym, "clock": clock, "status": d.get("status"),
            "minute_bars": d.get("n_minute_bars"), "clock_slots": d.get("n_clock_slots"),
            "complete": d.get("n_complete"),
            "design_origins": d.get("n_design_origins", 0),
            "confirm_origins": d.get("n_confirm_origins", 0),
            "initial_fit_n": d.get("initial_fit_n"),
            "oos_n_design": d.get("oos_n_design"),
            "contig_design": d.get("contiguous_frac_design"),
            "contig_confirm": d.get("contiguous_frac_confirm"),
            "boundary_dropped": d.get("n_boundary_dropped"),
        })
    return pl.DataFrame(rows).sort(["clock", "symbol"])


def primary_ic(m: pl.DataFrame) -> pl.DataFrame:
    return (
        m.filter(
            (pl.col("arm") == "V-LEVEL") & (pl.col("metric") == "oos_ic")
            & (pl.col("model") == "ridge") & (pl.col("target") == "target_abs_oo")
        )
        .select("symbol", "clock", "band", "value", "ci_low", "ci_high", "n_obs", "n_dates",
                "mde", "band_label", "band_label_detected")
        .sort(["band", "clock", "symbol"])
    )


def metric_table(m: pl.DataFrame, arm: str, metric: str, **eq) -> pl.DataFrame:
    f = (pl.col("arm") == arm) & (pl.col("metric") == metric)
    for k, v in eq.items():
        f = f & (pl.col(k) == v)
    return (
        m.filter(f)
        .select("symbol", "clock", "band", "model", "value", "ci_low", "ci_high",
                "n_obs", "n_dates", "mde", "band_label", "band_label_detected")
        .sort(["band", "clock", "symbol"])
    )


def label_counts(t: pl.DataFrame, col: str = "band_label") -> pl.DataFrame:
    return t.group_by(["band", "clock", col]).len().sort(["band", "clock", col])


def controls_table(controls: dict) -> pl.DataFrame:
    rows = []
    for key, bands in controls["cells"].items():
        sym, clock = key.split("|")
        for band, c in bands.items():
            if c.get("status") != "OK":
                rows.append({"symbol": sym, "clock": clock, "band": band,
                             "status": c.get("status")})
                continue
            sh = c["TIME-SHUFFLE-PREDICTORS"]
            de = c["TARGET-LABEL-DERANGEMENT"]
            gl = c["TARGET-DERANGEMENT-UNRESTRICTED"]
            tw = c["TARGET-FUTURE-DESTROY_REPORT_LAYER"]
            bite = c["BITE_PLANT"]
            rows.append({
                "symbol": sym, "clock": clock, "band": band, "status": "OK",
                "live_ic": sh.get("live"),
                "shuf_p50": sh.get("p50"), "shuf_p95": sh.get("p95"),
                "shuf_collapse": sh.get("collapse_fraction"),
                "live_outside_shuf_90": not sh.get("live_inside_central_90", True),
                "der_p50": de.get("p50"), "der_p95": de.get("p95"), "der_p99": de.get("p99"),
                "der_collapse": de.get("collapse_fraction"), "der_p": de.get("one_sided_p"),
                "glob_p50": gl.get("p50"), "glob_collapse": gl.get("collapse_fraction"),
                "destroy_layer": tw.get("interpretation"),
                "z_zero": tw.get("z_zero"), "z_live": tw.get("z_live"),
                "plant_ic": bite.get("achieved_plant_ic"),
                "plant_killed_shuffle": bite.get("plant_destroyed_by_shuffle"),
                "plant_killed_derange": bite.get("plant_destroyed_by_derangement"),
            })
    return pl.DataFrame(rows, infer_schema_length=None).sort(["band", "clock", "symbol"])


def three_bases(m: pl.DataFrame, ctl: pl.DataFrame) -> dict:
    """Design §6.4 clauses evaluated on all THREE candidate bases — no recommendation.

    Operator decision 2026-07-23 (QA F-4): the frozen §6.4 recommendation is not computed.
    Each basis is reported side by side with what it would imply, and the PASS/STOP call is
    the operator's at the gate.
    """
    t = primary_ic(m)
    st = m.filter((pl.col("arm") == "STABILITY")
                  & pl.col("metric").str.starts_with("n_thirds_positive"))
    ok = ctl.filter(pl.col("status") == "OK")

    def clause1(band: str, label_col: str) -> dict:
        b = t.filter(pl.col("band") == band)
        sup = sorted(b.filter(pl.col(label_col) == "SUPPORTED")["symbol"].unique().to_list())
        powered = b.filter(pl.col(label_col) != "UNPOWERED")
        n_powered_symbols = powered["symbol"].n_unique()
        return {
            "cells": b.height,
            "symbols_with_a_forecast": b["symbol"].n_unique(),
            "symbols_SUPPORTED": sup,
            "n_symbols_SUPPORTED": len(sup),
            "n_powered_cells": powered.height,
            "n_powered_symbols": n_powered_symbols,
            "clause_1_ge_10_of_25": len(sup) >= 10,
            "clause_1_fallback_ge_40pct_of_powered_symbols": (
                (len(sup) / n_powered_symbols >= 0.40) if n_powered_symbols else False
            ),
            "frac_cells_positive_ic": float((b["value"] > 0).mean()) if b.height else None,
        }

    def clause3(mode: str) -> dict:
        sub = st.filter(pl.col("metric") == f"n_thirds_positive_{mode}")
        return {
            "cells_reported": sub.height,
            "cells_with_ge2_positive_thirds": int(sub.filter(pl.col("value") >= 2).height),
            "cells_with_only_one_powered_third": int(sub.filter(pl.col("n_obs") < 2).height),
        }

    clause2 = {
        "cells": ok.height,
        "cells_live_outside_shuffle_central_90": int(ok["live_outside_shuf_90"].sum())
        if ok.height else 0,
        "cells_block_derangement_p_below_0p05": int((ok["der_p"] < 0.05).sum())
        if ok.height else 0,
        "note": "predictor-side circular shift is the operative non-vacuity device",
    }

    return {
        "operator_decision": (
            "2026-07-23 — report all three bases, recommend nothing (QA F-4)"
        ),
        "basis_A_CONFIRM_design_labels": {
            "what_it_is": "verification window Mar-Dec 2023, literal §6.3 thresholds",
            "caveat": "§0 designates CONFIRM a verification read, not the estimation read",
            "clause_1": clause1("CONFIRM", "band_label"),
            "clause_3": "not defined on CONFIRM (§6.2 thirds are a DESIGN-band object)",
        },
        "basis_B_DESIGN_design_labels": {
            "what_it_is": "estimation window, literal §6.3 thresholds — the frozen basis",
            "caveat": (
                "the catalog history cap leaves ~100 unique dates per cell, below the ~225 "
                "the §6.3 UNPOWERED rule needs; the first literal calendar third is empty"
            ),
            "clause_1": clause1("DESIGN", "band_label"),
            "clause_3": clause3("calendar"),
        },
        "basis_C_DESIGN_disclosure_labels": {
            "what_it_is": "estimation window, detection-floor labels + per-sample thirds",
            "caveat": "both variants are disclosure companions the design never froze",
            "clause_1": clause1("DESIGN", "band_label_detected"),
            "clause_3": clause3("sample"),
        },
        "clause_2_destroy_controls_common_to_all_bases": clause2,
    }


def main() -> None:
    m, controls, diags, check = load()
    ctl = controls_table(controls)

    print("=" * 100)
    print("INTEGRITY SELF-CHECK:", check["all_pass"])
    for c in check["checks"]:
        print(f"  [{'PASS' if c['pass'] else 'FAIL'}] {c['id']}: {c['clause']}")
    print("\nSPREAD COST:", json.dumps(check["spread_cost_disclosure"]))

    print("\n" + "=" * 100 + "\nCOVERAGE (per symbol x clock)")
    cov = coverage(diags)
    print(cov)

    print("\n" + "=" * 100 + "\nV-LEVEL PRIMARY OOS IC (ridge -> next |open->open| move)")
    t = primary_ic(m)
    print(t)
    print("\nband label counts (design rule):")
    print(label_counts(t))
    print("\nband label counts (detected disclosure rule):")
    print(label_counts(t, "band_label_detected"))

    print("\n" + "=" * 100 + "\nV-LEVEL model comparison (median OOS IC by model x target x band)")
    print(
        m.filter((pl.col("arm") == "V-LEVEL") & (pl.col("metric") == "oos_ic"))
        .group_by(["band", "clock", "model", "target"])
        .agg(pl.col("value").median().alias("median_ic"), pl.len().alias("cells"))
        .sort(["band", "clock", "target", "model"])
    )

    print("\n" + "=" * 100 + "\ndMAE vs unconditional mean (bps; positive = model better)")
    print(
        m.filter((pl.col("metric") == "dmae_vs_uncond") & (pl.col("arm") == "V-LEVEL")
                 & (pl.col("model") == "ridge") & (pl.col("target") == "target_abs_oo"))
        .select("symbol", "clock", "band", "value", "ci_low", "ci_high", "n_dates")
        .sort(["band", "clock", "symbol"])
    )

    for arm, metric in (("V-REGIME", "gap_high_low_bps"),
                        ("V-REGIME-HMM", "gap_high_low_bps"),
                        ("V-XS", "xs_gap_top_minus_bottom_bps"),
                        ("V-TAIL", "exceed_diff_p90"),
                        ("V-TAIL", "exceed_diff_p95")):
        print("\n" + "=" * 100 + f"\n{arm} :: {metric}")
        tt = metric_table(m, arm, metric)
        print(tt)
        if "band_label" in tt.columns and tt.filter(pl.col("band_label") != "").height:
            print(label_counts(tt.filter(pl.col("band_label") != "")))

    print("\n" + "=" * 100 + "\nV-PERSIST autocorr summary (median across symbols)")
    print(
        m.filter((pl.col("arm") == "V-PERSIST")
                 & pl.col("metric").str.starts_with("autocorr"))
        .group_by(["band", "clock", "metric"])
        .agg(pl.col("value").median().alias("median"), pl.len().alias("cells"))
        .sort(["band", "clock", "metric"])
    )
    print("\nhalf-life of |r| (bars of the clock)")
    print(
        m.filter((pl.col("arm") == "V-PERSIST") & (pl.col("metric") == "half_life_abs_r_bars"))
        .group_by(["band", "clock"]).agg(pl.col("value").median().alias("median_half_life"),
                                         pl.col("value").is_not_null().sum().alias("cells"))
        .sort(["band", "clock"])
    )

    print("\n" + "=" * 100 + "\nV-MEASURE univariate IC vs next |move| (median across symbols)")
    print(
        m.filter((pl.col("arm") == "V-MEASURE")
                 & pl.col("metric").str.starts_with("ic_"))
        .group_by(["band", "clock", "metric"])
        .agg(pl.col("value").median().alias("median_ic"), pl.len().alias("cells"))
        .sort(["band", "clock", "metric"])
    )

    print("\n" + "=" * 100 + "\nV-CLOCK incremental OOS R2 over V-LEVEL (median across symbols)")
    print(
        m.filter((pl.col("arm") == "V-CLOCK") & pl.col("metric").str.starts_with("incr_r2"))
        .group_by(["band", "clock", "metric"])
        .agg(pl.col("value").median().alias("median_incr_r2"), pl.len().alias("cells"))
        .sort(["band", "clock", "metric"])
    )
    print("\nV-LEVEL OOS R2 vs unconditional (median)")
    print(
        m.filter((pl.col("arm") == "V-CLOCK") & (pl.col("metric") == "oos_r2_vlevel_only"))
        .group_by(["band", "clock"]).agg(pl.col("value").median().alias("median_r2"),
                                         pl.len().alias("cells"))
        .sort(["band", "clock"])
    )

    print("\n" + "=" * 100 + "\nCONTROLS + TRIPWIRE")
    print(ctl)
    print("\nfuture-destroy REPORT LAYER interpretation counts (labels, not gates):")
    print(ctl.group_by(["band", "destroy_layer"]).len().sort(["band", "destroy_layer"]))

    print("\n" + "=" * 100 + "\nSTABILITY (DESIGN thirds, V-LEVEL primary IC)")
    print(
        m.filter(pl.col("arm") == "STABILITY")
        .select("symbol", "clock", "metric", "value", "n_obs")
        .sort(["clock", "symbol", "metric"])
    )

    print("\n" + "=" * 100 + "\nDESIGN §6.4 CLAUSES ON ALL THREE BASES (no recommendation)")
    print(json.dumps(three_bases(m, ctl), indent=2))

    print("\n" + "=" * 100 + "\nMULTIPLICITY")
    print(f"  metric rows emitted      : {m.height}")
    print(f"  arms x clocks x symbols  : "
          f"{m['arm'].n_unique()} x {m['clock'].n_unique()} x {m['symbol'].n_unique()}")
    print(f"  distinct (arm,symbol,clock,band) cells: "
          f"{m.select(['arm','symbol','clock','band']).unique().height}")


if __name__ == "__main__":
    main()
