"""EXP-019 data-analyst interrogation — seed battery, direction split, delay twin, costs, VR.

Own code on canonical xen estimands only (per_leg_net); no experiment-local accounting.
Outputs: results/battery.csv, results/direction.csv, results/twin.csv, results/costs.csv,
results/vr.csv, results/summary.json (headline numbers for analysis.md).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from xen.adjudication import per_leg_net                     # noqa: E402
from xen.evaluation import FTMO_COSTS                        # noqa: E402

ROOT = Path(__file__).resolve().parents[4]
LIVE = ROOT / "data" / "strategy_runs" / "EXP-019"
TWIN = ROOT / "data" / "strategy_runs" / "EXP-019-delay1"
OUT = Path(__file__).resolve().parents[1] / "results"

HOLDS = (6, 12, 24, 48)
EXP018_TARGET = 31.5          # bps/leg, NZDUSD rt anomaly (EXP-018)
PLANT = 15.0                  # predeclared synthetic offset (design §5)


def load_family(root: Path) -> pl.DataFrame:
    rows = []
    for d in sorted(root.glob("random_hold_*")):
        meta = json.loads((d / "run_metadata.json").read_text())
        sym = meta["symbol"].upper()
        seed = int(meta["parameters"]["schedule_seed"])
        legs = per_leg_net(pl.read_parquet(d / "cis_trades.parquet"), cost_bps=0.0)
        legs = legs.with_columns(pl.lit(sym).alias("symbol"), pl.lit(seed).alias("seed"))
        rows.append(legs)
    return pl.concat(rows)


def seed_stratum_means(legs: pl.DataFrame) -> pl.DataFrame:
    """Per (symbol, hold, seed): mean gross bps over completed legs."""
    return (legs.filter(pl.col("Censored") == 0)
                .group_by("symbol", "HorizonBars", "seed")
                .agg(pl.col("NetBps").mean().alias("seed_mean"),
                     pl.len().alias("n_legs")))


def battery_table(sm: pl.DataFrame) -> pl.DataFrame:
    """Across-seed battery per (symbol, hold): mean, sd, se, sign counts, MDE."""
    return (sm.group_by("symbol", "HorizonBars")
              .agg(pl.col("seed_mean").mean().alias("battery_mean"),
                   pl.col("seed_mean").std().alias("seed_sd"),
                   (pl.col("seed_mean").std() / pl.col("seed_mean").len().sqrt()).alias("battery_se"),
                   (pl.col("seed_mean") > 0).sum().alias("n_pos_seeds"),
                   pl.col("seed_mean").len().alias("n_seeds"),
                   pl.col("n_legs").sum().alias("n_legs"),
                   pl.col("seed_mean").min().alias("seed_min"),
                   pl.col("seed_mean").max().alias("seed_max"))
              .with_columns((2.0 * pl.col("battery_se")).alias("battery_mde"))
              .sort("symbol", "HorizonBars"))


def per_seed_ci_low(legs: pl.DataFrame, offset: float, n_boot: int = 2000,
                    seed0: int = 7) -> pl.DataFrame:
    """Per (symbol, hold, seed): does a simple bootstrap CI_low clear 0 after +offset?

    Plain iid bootstrap over legs within a seed-stratum (legs within one seed are near-
    independent draws — entries ≥4 bars apart; holds overlap partially, so this slightly
    understates SE for H=24/48; the planted check only needs order-of-magnitude bite).
    """
    rng = np.random.default_rng(seed0)
    out = []
    for (sym, hold, seed), grp in legs.filter(pl.col("Censored") == 0).group_by(
            "symbol", "HorizonBars", "seed"):
        x = grp["NetBps"].to_numpy() + offset
        n = len(x)
        if n < 10:
            out.append({"symbol": sym, "HorizonBars": hold, "seed": seed, "ci_low": np.nan})
            continue
        idx = rng.integers(0, n, size=(n_boot, n))
        means = x[idx].mean(axis=1)
        out.append({"symbol": sym, "HorizonBars": hold, "seed": seed,
                    "ci_low": float(np.quantile(means, 0.025))})
    return pl.DataFrame(out)


def direction_split(legs: pl.DataFrame, drift: dict[str, float]) -> pl.DataFrame:
    """Per (symbol, hold): long/short means + analytic drift benchmark dir*mu*H (bps)."""
    d = (legs.filter(pl.col("Censored") == 0)
             .group_by("symbol", "HorizonBars", "Direction")
             .agg(pl.col("NetBps").mean().alias("mean_bps"), pl.len().alias("n"))
             .pivot(values=["mean_bps", "n"], index=["symbol", "HorizonBars"],
                    on="Direction"))
    d = d.rename({c: c.replace('{"', "").replace('"}', "").replace(",", "_") for c in d.columns})
    d = d.with_columns(
        pl.col("symbol").replace_strict(drift, default=None).alias("mu_bar_bps"))
    return d.with_columns(
        (pl.col("mu_bar_bps") * pl.col("HorizonBars")).alias("drift_long_expected_bps"),
        (-pl.col("mu_bar_bps") * pl.col("HorizonBars")).alias("drift_short_expected_bps"),
    ).sort("symbol", "HorizonBars")


def window_drift(root: Path) -> dict[str, float]:
    """Per instrument: mean open-to-open 4h log return over the emitted band, bps."""
    drift = {}
    seen = set()
    for d in sorted(root.glob("random_hold_*")):
        meta = json.loads((d / "run_metadata.json").read_text())
        sym = meta["symbol"].upper()
        if sym in seen:
            continue
        seen.add(sym)
        opens = pl.read_parquet(d / "positions.parquet", columns=["RealOpen"])["RealOpen"].to_numpy()
        r = np.diff(np.log(opens)) * 1e4
        drift[sym] = float(np.mean(r))
    return drift


def variance_ratio(root: Path) -> pl.DataFrame:
    """VR(H) = Var(H-bar o2o sum)/(H*Var(1)) per instrument at H in HOLDS (disclosure)."""
    rows = []
    seen = set()
    for d in sorted(root.glob("random_hold_*")):
        meta = json.loads((d / "run_metadata.json").read_text())
        sym = meta["symbol"].upper()
        if sym in seen:
            continue
        seen.add(sym)
        opens = pl.read_parquet(d / "positions.parquet", columns=["RealOpen"])["RealOpen"].to_numpy()
        r = np.diff(np.log(opens))
        v1 = np.var(r)
        for h in HOLDS:
            csum = np.cumsum(r)
            rh = csum[h:] - csum[:-h]
            rows.append({"symbol": sym, "H": h, "vr": float(np.var(rh) / (h * v1))})
    return pl.DataFrame(rows)


def commission_bps_table(legs: pl.DataFrame) -> pl.DataFrame:
    """Round-trip commission bps per symbol at the median entry price (per-side x2 and x1)."""
    med = (legs.group_by("symbol").agg(pl.col("EntryFillPrice").median().alias("px")))
    rows = []
    for sym, px in med.iter_rows():
        spec = FTMO_COSTS[sym]
        if spec["commission_type"] == "percent":
            per_event = spec["commission"] * 100.0
        else:
            per_event = spec["pip_commission_per_lot"] * spec["pip_conversion"] / px * 1e4
        rows.append({"symbol": sym, "median_px": px,
                     "comm_rt_bps_x2": 2 * per_event, "comm_rt_bps_x1": per_event})
    return pl.DataFrame(rows)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    legs = load_family(LIVE)
    twin_legs = load_family(TWIN)
    print(f"live legs: {legs.height}, twin legs: {twin_legs.height}")
    legs.write_parquet(OUT / "legs_live.parquet")
    twin_legs.write_parquet(OUT / "legs_twin.parquet")

    sm = seed_stratum_means(legs)
    bat = battery_table(sm)
    bat.write_csv(OUT / "battery.csv")

    # Planted-offset bite check (run BEFORE interpreting the real read): +15 bps must be
    # flagged (CI_low>0) in >=24/25 seeds per stratum; and at offset 0 as the false-positive
    # disclosure.
    plant = per_seed_ci_low(legs, PLANT).group_by("symbol", "HorizonBars").agg(
        (pl.col("ci_low") > 0).sum().alias("n_flagged"), pl.len().alias("n_seeds"))
    null_fp = per_seed_ci_low(legs, 0.0).group_by("symbol", "HorizonBars").agg(
        (pl.col("ci_low") > 0).sum().alias("n_flagged"), pl.len().alias("n_seeds"))
    plant.write_csv(OUT / "plant_check.csv")
    null_fp.write_csv(OUT / "null_fp_check.csv")

    drift = window_drift(LIVE)
    dirsplit = direction_split(legs, drift)
    dirsplit.write_csv(OUT / "direction.csv")

    # Delay twin: NZDUSD per (hold, seed) paired diff live - twin.
    sm_twin = seed_stratum_means(twin_legs).rename({"seed_mean": "twin_mean", "n_legs": "twin_n"})
    tw = (sm.filter(pl.col("symbol") == "NZDUSD")
            .join(sm_twin, on=["symbol", "HorizonBars", "seed"])
            .with_columns((pl.col("seed_mean") - pl.col("twin_mean")).alias("pair_diff")))
    twsum = (tw.group_by("HorizonBars")
               .agg(pl.col("seed_mean").mean().alias("live_battery"),
                    pl.col("twin_mean").mean().alias("twin_battery"),
                    pl.col("pair_diff").mean().alias("mean_pair_diff"),
                    (pl.col("pair_diff").std() / pl.col("pair_diff").len().sqrt())
                    .alias("pair_diff_se"))
               .sort("HorizonBars"))
    twsum.write_csv(OUT / "twin.csv")

    comm = commission_bps_table(legs)
    comm.write_csv(OUT / "costs.csv")

    vr = variance_ratio(LIVE)
    vr.write_csv(OUT / "vr.csv")

    # NZDUSD anomaly placement: EXP-018 +31.5 vs the pooled-hold per-seed mean distribution.
    nz = (legs.filter((pl.col("symbol") == "NZDUSD") & (pl.col("Censored") == 0))
              .group_by("seed").agg(pl.col("NetBps").mean().alias("seed_mean")))
    nz_means = np.sort(nz["seed_mean"].to_numpy())
    pctl = float((nz_means < EXP018_TARGET).mean())

    # Physicality/structure extras.
    cap_note = {"censored_live": int(legs["Censored"].sum()),
                "censored_twin": int(twin_legs["Censored"].sum())}
    years = (legs.filter(pl.col("Censored") == 0)
                 .with_columns(pl.col("EntryTime").dt.year().alias("yr"))
                 .group_by("symbol", "yr").agg(pl.col("NetBps").mean().alias("mean_bps"),
                                               pl.len().alias("n")))
    years.write_csv(OUT / "per_year.csv")

    summary = {
        "n_live_legs": legs.height, "n_twin_legs": twin_legs.height,
        "nzdusd_pooled_seed_means_minmax": [float(nz_means[0]), float(nz_means[-1])],
        "exp018_31p5_percentile_in_nzdusd_seed_dist": pctl,
        "global_battery_mean_bps": float(sm["seed_mean"].mean()),
        **cap_note,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
