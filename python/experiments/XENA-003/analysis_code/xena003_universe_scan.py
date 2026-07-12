"""XENA-003 universe scan — per-candidate search-band leg economics (raw emissions).

Descriptive per-leg reads only. Gross per-leg P&L is the canonical engine estimand
``RealizedBps`` (= xen.adjudication's leg contract); net-of-cost per-leg uses
``xen.adjudication.per_leg_net``. NO local accounting primitives.

Outputs: results_analyst/universe_scan.parquet
"""
from __future__ import annotations

import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import polars as pl
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[4]
RUNS = ROOT / "data" / "strategy_runs" / "XENA-003"
OUT = ROOT / "python" / "experiments" / "XENA-003" / "results_analyst"

# Pre-registered band boundaries (design §5)
SEARCH = (np.datetime64("2021-06-02T00:01:00", "ns"), np.datetime64("2023-03-08T00:00:00", "ns"))


def _scan_one(rec: dict) -> dict:
    run = RUNS / rec["run_dir"]
    cis = pl.read_parquet(run / "cis_trades.parquet")
    s0 = int(SEARCH[0].astype("int64"))
    s1 = int(SEARCH[1].astype("int64"))
    cis = cis.with_columns(pl.col("EntryTime").dt.cast_time_unit("ns").cast(pl.Int64).alias("_et"))
    band = cis.filter((pl.col("_et") >= s0) & (pl.col("_et") < s1))
    n = band.height
    out = {"candidate_id": rec["candidate_id"], "symbol": rec["symbol"],
           "cost_bps_pin": rec["cost_bps"], "n_trades_band": n,
           "n_trades_all": cis.height}
    if n == 0:
        return out
    live = band.filter(pl.col("Censored") == 0)
    r = live.get_column("RealizedBps").to_numpy()
    stop = (np.abs(live.get_column("EntryFillPrice").to_numpy()
                   - live.get_column("SlPrice").to_numpy())
            / live.get_column("EntryFillPrice").to_numpy() * 1e4)
    held = live.get_column("BarsHeld").to_numpy()
    er = live.get_column("ExitReason").to_list()
    dur_min = ((live.get_column("ExitTime").dt.cast_time_unit("ns").cast(pl.Int64).to_numpy()
                - live.get_column("EntryTime").dt.cast_time_unit("ns").cast(pl.Int64).to_numpy())
               / 6e10)
    out.update({
        "n_live": len(r), "n_censored": n - len(r),
        "gross_mean_bps": float(np.mean(r)), "gross_median_bps": float(np.median(r)),
        "gross_std_bps": float(np.std(r)), "gross_sum_bps": float(np.sum(r)),
        "gross_q05": float(np.quantile(r, 0.05)), "gross_q95": float(np.quantile(r, 0.95)),
        "win_rate": float(np.mean(r > 0)),
        "stop_bps_median": float(np.median(stop)), "stop_bps_mean": float(np.mean(stop)),
        "stop_bps_q05": float(np.quantile(stop, 0.05)),
        "stop_bps_q95": float(np.quantile(stop, 0.95)),
        "bars_held_median": float(np.median(held)),
        "hold_minutes_median": float(np.median(dur_min)),
        "frac_profit_exit": float(np.mean([x == "profit_exit" for x in er])),
        "frac_hold_exit": float(np.mean([x == "hold_period" for x in er])),
        "long_frac": float(np.mean(live.get_column("Direction").to_numpy() > 0)),
        # leverage proxy: notional/equity per position at r=0.005 (oracle sizing)
        "lev_median": float(0.005 / (np.median(stop) / 1e4)),
    })
    return out


def main() -> None:
    manifest = json.loads((RUNS / "universe_manifest.json").read_text())
    cands = manifest["candidates"]
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        for r in tqdm(ex.map(_scan_one, cands, chunksize=16), total=len(cands)):
            rows.append(r)
    df = pl.DataFrame(rows)
    df = df.with_columns([
        pl.col("candidate_id").str.split("-").list.get(2).alias("domain"),
        pl.col("candidate_id").str.split("-").list.get(3).alias("hold"),
        pl.col("candidate_id").str.split("-").list.get(4).alias("variant"),
    ])
    df.write_parquet(OUT / "universe_scan.parquet")
    print(df.shape)
    print(df.select("gross_mean_bps", "gross_median_bps", "n_trades_band",
                    "stop_bps_median", "win_rate").describe())
    print("frac gross-profitable (sum>0):",
          float((df.get_column("gross_sum_bps") > 0).mean()))


if __name__ == "__main__":
    main()
