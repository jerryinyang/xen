"""A6 — independent end-to-end re-derivation of M15 episodes from raw M1 bars.

Covers the three things no QA run has verified on M15: entry signal, exit fill, r_bps.
Re-derives the M15 clock, ATR20, the pivot+momentum entry, the stop fill and the TIME exit
from the raw catalog, with no screen_code import.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np, polars as pl
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from a1_apparatus_m15 import load_m1  # raw decoder only

RES = Path(__file__).resolve().parents[1] / "results"
NS = 1_000_000_000


def agg_clock(m1: pl.DataFrame, minutes: int) -> pl.DataFrame:
    span = minutes * 60 * NS
    df = m1.with_columns(((pl.col("ts_event") - 60 * NS) // span * span).alias("slot_start"))
    return (df.group_by("slot_start").agg(
        pl.col("open").sort_by("ts_event").first().alias("open"),
        pl.col("high").max().alias("high"), pl.col("low").min().alias("low"),
        pl.col("close").sort_by("ts_event").last().alias("close"),
        pl.len().alias("n_min"), pl.col("ts_event").max().alias("last_ts"))
        .sort("slot_start").with_columns((pl.col("slot_start") + span).alias("slot_end")))


def wilder_atr(h, l, c, n=20):
    pc = np.concatenate([[np.nan], c[:-1]])
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    out = np.full(len(c), np.nan)
    if len(c) <= n:
        return out
    out[n] = np.nanmean(tr[1:n + 1])
    for i in range(n + 1, len(c)):
        out[i] = (out[i - 1] * (n - 1) + tr[i]) / n
    return out


SYM, CLOCK, MIN, DELTA = "BTCUSDT", "M15", 15, 0.5
m1 = load_m1(SYM)
bars = agg_clock(m1, MIN)
o, h, l, c = (bars[x].to_numpy() for x in ("open", "high", "low", "close"))
se = bars["slot_end"].to_numpy()
atr = wilder_atr(h, l, c)

# entry rule at decision index i ([0]=i, [1]=i-1, [2]=i-2)
sig = []
for i in range(21, len(c)):
    if not np.isfinite(atr[i]) or atr[i] <= 0:
        continue
    mom = (c[i] - c[i - 1]) / atr[i]
    if l[i - 1] < min(l[i], l[i - 2]) and mom > DELTA:
        sig.append((i, +1, h[i], mom))
    elif h[i - 1] > max(h[i], h[i - 2]) and -mom > DELTA:
        sig.append((i, -1, l[i], -mom))

print(f"{SYM}/{CLOCK}/d={DELTA}: I independently derive {len(sig)} raw signals from the catalog")

ts_m1 = m1["ts_event"].to_numpy(); op1, hi1, lo1 = (m1[x].to_numpy() for x in ("open", "high", "low"))
emit = (pl.scan_parquet(RES / "episodes.parquet").filter(
    (pl.col("symbol") == SYM) & (pl.col("clock") == CLOCK) & (pl.col("delta") == DELTA)
    & (pl.col("variant_id") == "L0_BASELINE")).sort("signal_ts").collect())
print(f"emitted L0 episodes for this cell: {emit.height}")

INACTIVE_H, ACTIVE_H = 2.0, 1.0
checked = matched = 0
report = []
for idx, side, stop, mom in sig:
    dclose = int(se[idx])
    row = emit.filter(pl.col("decision_end_ns") == dclose)
    if row.height != 1:
        continue
    r = row.row(0, named=True)
    # --- entry fill: first M1 bar in (dclose, dclose + inactiveHold] trading through stop
    win_end = dclose + int(INACTIVE_H * 3600 * NS)
    k0 = int(np.searchsorted(ts_m1, dclose, "right"))
    k1 = int(np.searchsorted(ts_m1, win_end, "right"))
    fill_i = fill_p = None
    for k in range(k0, k1):
        if (side > 0 and hi1[k] >= stop) or (side < 0 and lo1[k] <= stop):
            gap = (op1[k] > stop) if side > 0 else (op1[k] < stop)
            fill_i, fill_p = k, (op1[k] if gap else stop)
            break
    if fill_i is None:
        continue
    # --- TIME exit: open of the first M15 bar whose slot_start >= fill_ts + activeHold
    tgt = int(ts_m1[fill_i]) + int(ACTIVE_H * 3600 * NS)
    j = int(np.searchsorted(bars["slot_start"].to_numpy(), tgt, "left"))
    if j >= len(o):
        continue
    ex_ts, ex_p = int(bars["slot_start"].to_numpy()[j]), float(o[j])
    r_bps = side * (ex_p - fill_p) / fill_p * 1e4
    checked += 1
    ok = (abs(fill_p - r["fill_price"]) < 1e-9 and int(ts_m1[fill_i]) == r["fill_ts"]
          and abs(ex_p - r["exit_price"]) < 1e-9 and abs(r_bps - r["r_bps"]) < 1e-6
          and abs(stop - r["stop_price"]) < 1e-9)
    matched += ok
    if not ok and len(report) < 6:
        report.append({"decision_close": dclose, "mine": (int(ts_m1[fill_i]), fill_p, ex_ts, ex_p, round(r_bps, 4)),
                       "emitted": (r["fill_ts"], r["fill_price"], r["exit_ts"], r["exit_price"], round(r["r_bps"], 4))})
    if checked >= 500:
        break

print(f"\nEND-TO-END M15 re-derivation: {matched}/{checked} episodes match on "
      f"stop price, fill ts, fill price, exit ts, exit price AND r_bps")
for x in report:
    print("  MISMATCH", x)
