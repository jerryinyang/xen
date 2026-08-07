"""MFE / capture-geometry diagnostic (operator question 2026-07-23).

Answers "available but capture geometry needs redefinition?" with three reads, per arm (DESIGN):

1. **Capture efficiency** — realized episode gross vs the realized-hold MFE (best favourable
   open-to-open excursion actually REACHED before the exit). If MFE >> realized gross, the arm
   reaches favourable ground then gives it back → a geometry problem, not an availability one.
2. **Horizon availability** — MFE over the fixed time-cap window from entry, REGARDLESS of the
   exit (what a better/longer exit could see).
3. **Signal vs random** — horizon MFE of the signal's entries vs random-timing entries (same clock,
   same 50/50 side, DESIGN band). If signal ≈ random, the horizon availability is ambient
   volatility, NOT signal-granted, and redefining geometry will not manufacture an edge.

All MFE reads are NON-TRADABLE ceilings (they peek at the within-window peak). Partial-cost floor
≈ 13.5 bps; net ceiling = MFE − floor. No tradability claim.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import polars as pl

SCREEN = Path(__file__).resolve().parents[1] / "screen_code"
sys.path.insert(0, str(SCREEN))

from xen.nautilus.catalog_fence import load_fence_manifest          # noqa: E402
from capture import horizon_excursion                                # noqa: E402
from config import BANDS, CLOCKS                                     # noqa: E402
from run_screen import prepare_clock                                 # noqa: E402

RESULTS = Path(__file__).resolve().parents[1] / "results"
COST_FLOOR = 13.5


def per_arm_capture() -> pl.DataFrame:
    ep = pl.read_parquet(RESULTS / "episodes.parquet").filter(pl.col("band") == "DESIGN")
    return (ep.group_by(["signal", "exit_mode", "clock"])
            .agg(pl.len().alias("n_ep"),
                 pl.col("gross_bps").median().round(1).alias("gross_med"),
                 pl.col("mfe_oo_bps").median().round(1).alias("mfe_oo_med"),
                 pl.col("mfe_hi_bps").median().round(1).alias("mfe_hi_med"),
                 pl.col("mae_oo_bps").median().round(1).alias("mae_oo_med"),
                 pl.col("horizon_mfe_oo_bps").median().round(1).alias("hz_mfe_med"),
                 (pl.col("gross_bps") > 0).mean().round(3).alias("p_right"))
            .with_columns(
                (pl.col("mfe_oo_med") - pl.col("gross_med")).round(1).alias("giveback_med"),
                (pl.col("mfe_oo_med") - COST_FLOOR).round(1).alias("net_mfe_ceiling"))
            .sort(["exit_mode", "signal", "clock"]))


def random_horizon_baseline(universe: list[str], n_draw: int = 3000, seed: int = 71000
                            ) -> pl.DataFrame:
    """Median horizon MFE of random-timing entries (50/50 side) per symbol x clock, DESIGN."""
    m = load_fence_manifest()
    rows = []
    for sym in universe:
        for clock in ("H1", "M15"):
            prep = prepare_clock(sym, clock, m)
            if prep is None:
                continue
            cap = CLOCKS[clock]["time_cap_bars"]
            blo = int(BANDS["DESIGN"][0].timestamp() * 1e9)
            bhi = int(BANDS["DESIGN"][1].timestamp() * 1e9)
            ss = prep["slot_start"]
            nsub = int((ss < bhi).sum())
            op, hi, lo, at = (prep["open"][:nsub], prep["high"][:nsub],
                              prep["low"][:nsub], prep["atr"][:nsub])
            elig = np.where((ss[:nsub] >= blo) & np.isfinite(at)
                            & (np.arange(nsub) > prep["start"]))[0]
            if elig.size < 50:
                continue
            rng = np.random.default_rng(seed)
            cand = rng.choice(elig, size=min(n_draw, elig.size), replace=False)
            side = rng.choice([1, -1], size=cand.size)
            hz = horizon_excursion(op, hi, lo, cand, side, cap)
            rows.append({"symbol": sym, "clock": clock,
                         "rand_hz_mfe_med": float(np.median(hz["horizon_mfe_oo_bps"]))})
    return pl.DataFrame(rows)


def signal_vs_random(universe: list[str]) -> pl.DataFrame:
    """Per (signal, exit_mode, clock): median over symbols of signal horizon-MFE / random-timing
    horizon-MFE. ~1 means the horizon availability is ambient, not signal-granted."""
    ep = pl.read_parquet(RESULTS / "episodes.parquet").filter(pl.col("band") == "DESIGN")
    sig_by_sym = (ep.group_by(["symbol", "signal", "exit_mode", "clock"])
                  .agg(pl.col("horizon_mfe_oo_bps").median().alias("sig_hz")))
    rand = random_horizon_baseline(universe)
    j = sig_by_sym.join(rand, on=["symbol", "clock"], how="inner")
    j = j.with_columns((pl.col("sig_hz") / pl.col("rand_hz_mfe_med")).alias("ratio"))
    return (j.group_by(["signal", "exit_mode", "clock"])
            .agg(pl.col("sig_hz").median().round(1).alias("sig_hz_med"),
                 pl.col("rand_hz_mfe_med").median().round(1).alias("rand_hz_med"),
                 pl.col("ratio").median().round(3).alias("sig_over_rand"))
            .sort(["exit_mode", "signal", "clock"]))


def main() -> None:
    import json
    universe = json.loads((RESULTS / "universe_recomputed.json").read_text())["symbols"]
    cap = per_arm_capture()
    svr = signal_vs_random(universe)
    with pl.Config(tbl_rows=200, tbl_cols=20, fmt_str_lengths=40):
        print("=== per-arm capture (DESIGN): realized gross vs MFE ===")
        print(cap)
        print("\n=== signal horizon-MFE vs random-timing horizon-MFE (median over symbols) ===")
        print(svr)
    cap.write_parquet(RESULTS / "mfe_capture_by_arm.parquet")
    svr.write_parquet(RESULTS / "mfe_signal_vs_random.parquet")
    print("\nwrote results/mfe_capture_by_arm.parquet, results/mfe_signal_vs_random.parquet")


if __name__ == "__main__":
    main()
