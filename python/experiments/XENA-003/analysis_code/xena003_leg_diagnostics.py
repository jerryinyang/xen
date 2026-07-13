"""XENA-003 leg diagnostics — fill mechanics, gross decomposition, adverse excursion.

Per certified-finalist member candidate, on the SEARCH band, decomposes the engine's own
gross leg return (RealizedBps, the canonical leg estimand) into:

    gross_bps  = dir*(ExitFill - EntryFill)/EntryFill*1e4        [what the oracle books]
    print_bps  = dir*(Open[fill_bar] - EntryFill)/EntryFill*1e4  [passive-limit print premium
                                                                  vs the LTF bar open]
    path_bps   = dir*(ExitFill - Open[fill_bar])/EntryFill*1e4   [forward price path]
    gross_bps == print_bps + path_bps  (identity, checked)

plus the oracle's FIRST mark increment (entry fill -> next LTF bar open), realised MAE vs the
nominal 2xATR sizing stop, and hold/exit anatomy.

Outputs: results_analyst/leg_diagnostics.parquet (+ .json summary)
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
RES = ROOT / "python" / "experiments" / "XENA-003" / "results"
OUT = ROOT / "python" / "experiments" / "XENA-003" / "results_analyst"

S0, S1 = 1622592060000000000, 1678233600000000000


def _diag_one(rec: dict) -> pl.DataFrame | None:
    run = RUNS / rec["run_dir"]
    cis = pl.read_parquet(run / "cis_trades.parquet")
    pos = pl.read_parquet(run / "positions.parquet").sort("SourceCloseTime")
    et = cis.get_column("EntryTime").dt.cast_time_unit("ns").cast(pl.Int64).to_numpy()
    sel = (et >= S0) & (et < S1) & (cis.get_column("Censored").to_numpy() == 0)
    cis = cis.filter(pl.Series(sel))
    if cis.height == 0:
        return None

    mt = pos.get_column("SourceCloseTime").dt.cast_time_unit("ns").cast(pl.Int64).to_numpy()
    mo = pos.get_column("RealOpen").to_numpy()
    mh = pos.get_column("RealHigh").to_numpy()
    ml = pos.get_column("RealLow").to_numpy()

    et = cis.get_column("EntryTime").dt.cast_time_unit("ns").cast(pl.Int64).to_numpy()
    xt = cis.get_column("ExitTime").dt.cast_time_unit("ns").cast(pl.Int64).to_numpy()
    d = cis.get_column("Direction").to_numpy().astype(float)
    ep = cis.get_column("EntryFillPrice").to_numpy()
    xp = cis.get_column("ExitFillPrice").to_numpy()
    sl = cis.get_column("SlPrice").to_numpy()
    rb = cis.get_column("RealizedBps").to_numpy()

    # bar containing the fill (same attribution as xen.adjudication: first bar CloseTime >= t)
    i0 = np.searchsorted(mt, et, side="left")
    i1 = np.minimum(np.searchsorted(mt, xt, side="left"), len(mt) - 1)
    i0 = np.minimum(i0, len(mt) - 1)
    o_fill = mo[i0]                                    # open of the fill bar
    o_next = mo[np.minimum(i0 + 1, len(mt) - 1)]       # oracle's first interior mark
    c_exit = mo[i1]

    print_bps = d * (o_fill - ep) / ep * 1e4
    path_bps = d * (xp - o_fill) / ep * 1e4
    first_mark_bps = d * (o_next - ep) / ep * 1e4
    exit_vs_open_bps = d * (xp - o_next) / ep * 1e4
    stop_bps = np.abs(ep - sl) / ep * 1e4

    # realised adverse excursion over the held bars (LTF bar extremes, engine emission)
    mae = np.empty(len(ep))
    for j in range(len(ep)):
        a, b = int(i0[j]), int(i1[j])
        if b < a:
            b = a
        if d[j] > 0:
            worst = ml[a:b + 1].min()
            mae[j] = (ep[j] - worst) / ep[j] * 1e4
        else:
            worst = mh[a:b + 1].max()
            mae[j] = (worst - ep[j]) / ep[j] * 1e4

    return pl.DataFrame({
        "candidate_id": [rec["candidate_id"]] * len(ep),
        "symbol": [rec["symbol"]] * len(ep),
        "dir": d, "entry": ep, "exit": xp,
        "gross_bps": rb, "print_bps": print_bps, "path_bps": path_bps,
        "first_mark_bps": first_mark_bps, "exit_vs_next_open_bps": exit_vs_open_bps,
        "stop_bps": stop_bps, "mae_bps": mae,
        "mae_over_stop": mae / stop_bps,
        "exit_reason": cis.get_column("ExitReason"),
        "bars_held": cis.get_column("BarsHeld"),
    })


def main() -> None:
    cert = json.loads((RES / "certification.json").read_text())
    union = sorted(set().union(*[set(r["subset"]) for r in cert["ranked"]]))
    man = json.loads((RUNS / "universe_manifest.json").read_text())
    recs = [c for c in man["candidates"] if c["candidate_id"] in set(union)]
    OUT.mkdir(parents=True, exist_ok=True)

    parts = []
    with ProcessPoolExecutor(max_workers=8) as ex:
        for r in tqdm(ex.map(_diag_one, recs, chunksize=4), total=len(recs)):
            if r is not None:
                parts.append(r)
    df = pl.concat(parts)
    df.write_parquet(OUT / "leg_diagnostics.parquet")

    ident = float(np.abs(df.get_column("gross_bps").to_numpy()
                         - df.get_column("print_bps").to_numpy()
                         - df.get_column("path_bps").to_numpy()).max())
    g = df.get_column("gross_bps").to_numpy()
    p = df.get_column("print_bps").to_numpy()
    pa = df.get_column("path_bps").to_numpy()
    fm = df.get_column("first_mark_bps").to_numpy()
    summ = {
        "n_legs": df.height, "n_candidates": len(parts),
        "identity_max_abs_err_bps": ident,
        "gross_mean": float(g.mean()), "gross_median": float(np.median(g)),
        "print_mean": float(p.mean()), "print_median": float(np.median(p)),
        "path_mean": float(pa.mean()), "path_median": float(np.median(pa)),
        "first_mark_mean": float(fm.mean()),
        "print_share_of_gross": float(p.mean() / g.mean()),
        "frac_print_positive": float((p > 0).mean()),
        "mae_over_stop_median": float(np.median(df.get_column("mae_over_stop"))),
        "frac_mae_gt_stop": float((df.get_column("mae_over_stop") > 1).mean()),
        "frac_mae_gt_2x_stop": float((df.get_column("mae_over_stop") > 2).mean()),
        "stop_bps_median": float(np.median(df.get_column("stop_bps"))),
    }
    (OUT / "leg_diagnostics_summary.json").write_text(json.dumps(summ, indent=1))
    print(json.dumps(summ, indent=1))

    per = (df.group_by("candidate_id").agg([
        pl.len().alias("n"), pl.col("gross_bps").mean().alias("gross_mean"),
        pl.col("print_bps").mean().alias("print_mean"),
        pl.col("path_bps").mean().alias("path_mean"),
        pl.col("first_mark_bps").mean().alias("first_mark_mean"),
        pl.col("stop_bps").median().alias("stop_med"),
        pl.col("mae_over_stop").median().alias("mae_over_stop_med"),
        (pl.col("mae_over_stop") > 1).mean().alias("frac_mae_gt_stop"),
        (pl.col("exit_reason") == "profit_exit").mean().alias("frac_profit_exit"),
    ]).sort("candidate_id"))
    per.write_parquet(OUT / "leg_diagnostics_percand.parquet")
    with pl.Config(tbl_rows=40, tbl_width_chars=200):
        print(per.head(30))


if __name__ == "__main__":
    main()
