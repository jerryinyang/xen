"""Build neutral, non-pruning summary tables for the SPDR-023 amended TRAIN rerun.

Reads canonical analysis artifacts read-only. Writes markdown to stdout.
Universes, entry variants and the two native lenses are never pooled.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path("experiments/SPDR-023/results/analysis")
UNIVERSES = ("ctrader", "crypto")
VARIANTS = ("E_TOUCH", "E_CLOSE")


def fmt(x: float, nd: int = 3) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "n/a"
    return f"{x:.{nd}f}"


def ci_flags(g: pd.DataFrame) -> tuple[int, int]:
    pos = int(((g["ci_low"] > 0) & g["ci_low"].notna()).sum())
    neg = int(((g["ci_high"] < 0) & g["ci_high"].notna()).sum())
    return pos, neg


def native_origin_tables() -> None:
    print("\n\n===== NATIVE ORIGIN LENS (COMMON_ORIGIN_OCCUPANCY_INCLUSIVE) =====")
    for u in UNIVERSES:
        npo = pd.read_parquet(BASE / u / "native_parameter_origins.parquet")
        print(f"\n### universe={u} total_rows={len(npo)}")
        print("\n-- row census by arm_class x state (all rows retained) --")
        print(npo.groupby(["arm_class", "state"]).size().rename("rows").to_string())

        alls = npo[npo["state"] == "ALL"]
        for v in VARIANTS:
            sub = alls[alls["entry_variant"] == v]
            print(f"\n-- {u} / {v} / state=ALL : arm rollup over symbols --")
            hdr = (
                "| arm_class | parameter | orientation | component | sym_rows | "
                "eligible_origin_n | observed_event_n | entry_fill_n | close_n | "
                "event_rate | fill_rate | exposure/origin med | est med | est min | est max | "
                "CI>0 | CI<0 | mde med | eff_origin_blocks |"
            )
            print(hdr)
            print("|" + "---|" * 18)
            keys = ["arm_class", "parameter", "orientation", "component"]
            for k, g in sub.groupby(keys, dropna=False):
                pos, neg = ci_flags(g)
                elig = int(g["eligible_origin_n"].sum())
                oev = int(g["observed_event_count"].sum())
                fil = int(g["entry_fill_n"].sum())
                clo = int(g["close_n"].sum())
                print(
                    f"| {k[0]} | {k[1]} | {k[2]} | {k[3] if isinstance(k[3], str) else 'FIXED'} "
                    f"| {len(g)} | {elig} | {oev} | {fil} | {clo} "
                    f"| {fmt(oev / elig if elig else np.nan, 4)} "
                    f"| {fmt(fil / elig if elig else np.nan, 4)} "
                    f"| {fmt(g['exposure_per_origin'].median())} "
                    f"| {fmt(g['estimate'].median())} | {fmt(g['estimate'].min())} "
                    f"| {fmt(g['estimate'].max())} | {pos} | {neg} "
                    f"| {fmt(g['mde'].median())} | {int(g['effective_origin_blocks'].sum())} |"
                )

        print(f"\n-- {u} : non-ALL state populations (retained, not pruned) --")
        ns = npo[npo["state"] != "ALL"]
        agg = ns.groupby(["entry_variant", "state"]).agg(
            rows=("estimate", "size"),
            eligible_origin_n=("eligible_origin_n", "sum"),
            observed_event_n=("observed_event_count", "sum"),
            entry_fill_n=("entry_fill_n", "sum"),
            close_n=("close_n", "sum"),
            est_med=("estimate", "median"),
            mde_med=("mde", "median"),
        )
        print(agg.to_string())


def native_trade_lens() -> None:
    print("\n\n===== NATIVE TRADE LENS (COMMON_CLOSE_TRADE, shared trades) =====")
    from xen.evaluation import block_bootstrap_ci

    for u in UNIVERSES:
        st = pd.read_parquet(
            BASE / u / "native_parameter_shared_trades.parquet",
            columns=[
                "entry_variant",
                "native_arm_id",
                "arm_class",
                "component",
                "parameter",
                "orientation",
                "orientation_pair",
                "symbol",
                "entry_ts",
                "outcome_bps",
                "fixed_outcome_bps",
                "paired_outcome_delta_bps",
                "common_fill_n",
                "common_close_n",
                "_entry_ns",
                "_exit_ns",
                "fixed_entry_ns",
                "fixed_exit_ns",
            ],
        )
        print(f"\n### universe={u} shared_trade_rows={len(st)}")
        print(
            "real _entry_ns non-null:",
            int(st["_entry_ns"].notna().sum()),
            "| real _exit_ns non-null:",
            int(st["_exit_ns"].notna().sum()),
            "| fixed_entry_ns non-null:",
            int(st["fixed_entry_ns"].notna().sum()),
            "| fixed_exit_ns non-null:",
            int(st["fixed_exit_ns"].notna().sum()),
        )
        for v in VARIANTS:
            sub = st[st["entry_variant"] == v]
            print(f"\n-- {u} / {v} : paired adaptive-minus-fixed on common closes --")
            print(
                "| arm_class | parameter | orientation | component | common_close_n | "
                "mean delta bps | median | ci_low | ci_high | ci_low_seed_range | mde | "
                "eff_trade_blocks |"
            )
            print("|" + "---|" * 12)
            keys = ["arm_class", "parameter", "orientation", "component"]
            for k, g in sub.groupby(keys, dropna=False):
                d = g.sort_values("_entry_ns")["paired_outcome_delta_bps"].to_numpy()
                d = d[np.isfinite(d)]
                n = len(d)
                if n < 2:
                    print(f"| {k[0]} | {k[1]} | {k[2]} | {k[3]} | {n} | n/a |" + " n/a |" * 7)
                    continue
                r = block_bootstrap_ci(d, block=24, n_boot=2000, n_seeds=5, seed=240730)
                eff = max(1, n // 24)
                mde = 2.8 * float(np.std(d, ddof=1)) / np.sqrt(eff)
                slr = r["ci_low_seed_range"]
                print(
                    f"| {k[0]} | {k[1]} | {k[2]} | {k[3]} | {n} | {fmt(float(np.mean(d)))} "
                    f"| {fmt(float(np.median(d)))} | {fmt(r['ci'][0])} | {fmt(r['ci'][1])} "
                    f"| [{fmt(slr[0])}, {fmt(slr[1])}] "
                    f"| {fmt(mde)} | {eff} |"
                )


def device_tables() -> None:
    print("\n\n===== DEVICE TABLES (per device, individual components first) =====")
    for u in UNIVERSES:
        for dev in ("target", "stop", "trail", "hold", "size"):
            df = pd.read_parquet(BASE / u / f"device_{dev}.parquet")
            print(f"\n### {u} / device_{dev}.parquet total_rows={len(df)}")
            print("-- row census by arm_class x state --")
            print(df.groupby(["arm_class", "state"]).size().rename("rows").to_string())
            live = df[df["estimate"].notna()]
            print(f"-- rows with a defined estimate: {len(live)} of {len(df)}")
            for v in VARIANTS:
                sub = live[live["entry_variant"] == v]
                if sub.empty:
                    print(f"-- {u} / {v} / {dev}: no defined-estimate rows")
                    continue
                print(f"\n-- {u} / {v} / {dev} : adaptive-minus-fixed by component x setting --")
                print(
                    "| arm_class | component | setting | metric | comparator | sym_rows | "
                    "episode_n | entry_fill_n | close_n | common_fill_n | common_close_n | "
                    "obs med | comp med | est med | est min | est max | CI>0 | CI<0 | mde med | "
                    "eff_trade_blocks |"
                )
                print("|" + "---|" * 20)
                keys = ["arm_class", "component", "setting", "metric_name", "comparator_id"]
                for k, g in sub.groupby(keys, dropna=False):
                    pos, neg = ci_flags(g)
                    print(
                        f"| {k[0]} | {k[1] if isinstance(k[1], str) else 'FIXED'} | {k[2]} "
                        f"| {k[3]} | {k[4]} | {len(g)} | {int(g['episode_n'].sum())} "
                        f"| {int(g['entry_fill_n'].sum())} | {int(g['close_n'].sum())} "
                        f"| {int(g['common_fill_n'].sum())} | {int(g['common_close_n'].sum())} "
                        f"| {fmt(g['observed'].median())} | {fmt(g['comparator_observed'].median())} "
                        f"| {fmt(g['estimate'].median())} | {fmt(g['estimate'].min())} "
                        f"| {fmt(g['estimate'].max())} | {pos} | {neg} "
                        f"| {fmt(g['mde'].median())} | {int(g['effective_trade_blocks'].sum())} |"
                    )


def controls_tables() -> None:
    print("\n\n===== CONTROLS =====")
    for u in UNIVERSES:
        ctl = pd.read_parquet(BASE / u / "controls.parquet")
        print(f"\n### {u} controls rows={len(ctl)}")
        print(ctl.groupby(["control", "population", "comparator"]).size().to_string())
        print("\n-- undefined/pointer rows --")
        print(
            ctl[ctl["estimate"].isna()][
                ["control", "population", "comparator", "undefined_reason", "count"]
            ].to_string()
        )
        for c in ("TIME_DERANGEMENT", "MAGNITUDE_MATCH"):
            sub = ctl[ctl["control"] == c]
            for v in VARIANTS:
                s = sub[sub["entry_variant"] == v]
                if s.empty:
                    continue
                print(f"\n-- {u} / {v} / {c} by component (+magnitude_bin) --")
                gk = ["component"] + (["magnitude_bin"] if c == "MAGNITUDE_MATCH" else [])
                print(
                    "| component | bin | rows | count | est med | est min | est max | CI>0 | "
                    "CI<0 | mde med | eff_count |"
                )
                print("|" + "---|" * 11)
                for k, g in s.groupby(gk, dropna=False):
                    kt = k if isinstance(k, tuple) else (k,)
                    kk = (kt + ("-", "-"))[:2]
                    pos, neg = ci_flags(g)
                    print(
                        f"| {kk[0]} | {kk[1]} | {len(g)} | {int(g['count'].sum())} "
                        f"| {fmt(g['estimate'].median())} | {fmt(g['estimate'].min())} "
                        f"| {fmt(g['estimate'].max())} | {pos} | {neg} "
                        f"| {fmt(g['mde'].median())} | {int(g['effective_count'].sum())} |"
                    )


def selection_state_tables() -> None:
    print("\n\n===== SELECTION CHECKS AND STATE SECTIONS =====")
    for u in UNIVERSES:
        sc = pd.read_parquet(BASE / u / "selection_checks.parquet")
        print(f"\n### {u} selection_checks rows={len(sc)}")
        for v in VARIANTS:
            s = sc[sc["entry_variant"] == v]
            print(f"\n-- {u} / {v} selection check by component --")
            print(
                s.groupby("component")
                .agg(
                    rows=("payoff_scale_ratio", "size"),
                    payoff_ratio_med=("payoff_scale_ratio", "median"),
                    payoff_ratio_min=("payoff_scale_ratio", "min"),
                    payoff_ratio_max=("payoff_scale_ratio", "max"),
                    sign_share_diff_med=("sign_share_difference", "median"),
                    excl_mean_median_gap_med=("excluded_mean_median_gap", "median"),
                    selected_n=("selected_n", "sum"),
                    excluded_n=("excluded_n", "sum"),
                )
                .to_string()
            )
        ss = pd.read_parquet(BASE / u / "state_sections.parquet")
        print(f"\n### {u} state_sections rows={len(ss)}")
        for v in VARIANTS:
            s = ss[ss["entry_variant"] == v]
            print(f"\n-- {u} / {v} state sections by component x state --")
            print(
                s.groupby(["component", "state"])
                .agg(
                    rows=("row_n", "size"),
                    row_n=("row_n", "sum"),
                    mean_outcome_bps_med=("mean_outcome_bps", "median"),
                    mean_outcome_bps_min=("mean_outcome_bps", "min"),
                    mean_outcome_bps_max=("mean_outcome_bps", "max"),
                )
                .to_string()
            )


def selected_excluded_census() -> None:
    print("\n\n===== SELECTED / EXCLUDED ORIGIN PATH CENSUS =====")
    for u in UNIVERSES:
        se = pd.read_parquet(
            BASE / u / "native_parameter_selected_excluded.parquet",
            columns=["entry_variant", "arm_class", "component", "state", "selection", "outcome_bps"],
        )
        print(f"\n### {u} selected_excluded rows={len(se)}")
        print(
            se.groupby(["entry_variant", "selection", "state"])
            .agg(rows=("outcome_bps", "size"), mean_outcome_bps=("outcome_bps", "mean"))
            .to_string()
        )
        print("\n-- by arm_class x selection --")
        print(
            se.groupby(["entry_variant", "arm_class", "selection"])
            .agg(rows=("outcome_bps", "size"), mean_outcome_bps=("outcome_bps", "mean"))
            .to_string()
        )


def cost_scope() -> None:
    print("\n\n===== COST SCOPE / RECORDING DEFECT =====")
    for u in UNIVERSES:
        ps = pd.read_parquet(BASE / u / "per_stratum_estimates.parquet")
        print(f"\n### {u} per_stratum rows={len(ps)}")
        for c in ("spread_cost_status", "spread_rt_bps", "cost_scope", "partial_cost_mean_bps"):
            print(f"   {c}: non-null {int(ps[c].notna().sum())} of {len(ps)}")
        st = pd.read_parquet(
            BASE / u / "native_parameter_shared_trades.parquet", columns=["partial_cost_bps"]
        )
        print(f"   shared_trades.partial_cost_bps non-null: {int(st['partial_cost_bps'].notna().sum())} of {len(st)}")


def main() -> None:
    pd.set_option("display.width", 250)
    pd.set_option("display.max_rows", 3000)
    cost_scope()
    native_origin_tables()
    native_trade_lens()
    device_tables()
    controls_tables()
    selection_state_tables()
    selected_excluded_census()


if __name__ == "__main__":
    sys.exit(main())
