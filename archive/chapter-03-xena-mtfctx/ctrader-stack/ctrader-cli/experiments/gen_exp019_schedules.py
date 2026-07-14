#!/usr/bin/env python3
"""EXP-019 (CF-VOLHARV-001) schedule generator — seeded, calendar-only, never prices.

Generates one schedule CSV per (instrument, seed): random-timing entry bars (~1 per 8
4h bars, seeded jitter), seeded coin-flip direction, hold round-robin {6,12,24,48} in
schedule order. Consumes ONLY the engine's emitted 4h bar calendar (timestamps — the
``SourceCloseTime`` column of a calendar-emission run; deviation D1 in Xen.RandomHold.cs):
data-independence is provable by construction because no price column is ever read.

Inputs:  data/strategy_runs/EXP-019-cal/random_hold_<symbol>_4h_<stamp>/positions.parquet
Outputs: tools/ctrader-cli/experiments/schedules/EXP-019/EXP-019-4h-<SYMBOL>_seed<i>.csv
         + NZDUSD delay-twin (+1 calendar bar): ..._seed<i>_shift1.csv

Rules (design §4 + operator elicitation 2026-07-04):
  * base seed 20260705; seed_i = base + i, i in 1..25
  * warmup: first 50 calendar bars excluded (D4)
  * inter-entry gap ~ seeded uniform integer in [4, 12] (mean 8)
  * drop entries whose hold cannot complete before the fence: entry_idx + hold <= N-2 (D3)
  * CSV row time = the FILL bar's open (the robot fires when the previous bar completes;
    fill timestamp == scheduled bar open — design §7 tripwire 2)
"""

from __future__ import annotations

import argparse
import sys
from datetime import timedelta
from pathlib import Path

import numpy as np
import polars as pl

BASE_SEED = 20260705
N_SEEDS = 25
WARMUP_BARS = 50
GAP_LO, GAP_HI = 4, 12          # inclusive; mean 8
HOLD_GRID = (6, 12, 24, 48)     # round-robin in schedule order
DOMAIN_MINUTES = 240

ROOT = Path(__file__).resolve().parents[3]
CAL_ROOT = ROOT / "data" / "strategy_runs" / "EXP-019-cal"
OUT_DIR = Path(__file__).resolve().parent / "schedules" / "EXP-019"

SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD",
    "EURJPY", "GBPJPY", "AUDJPY", "XAUUSD", "BTCUSD",
    "USTEC", "US500", "US2000", "JP225",
]
SHIFT_SYMBOLS = ["NZDUSD"]      # +1-bar delay twin (design §7 tripwire 3)


def load_calendar(symbol: str) -> list:
    """Return the engine 4h bar OPEN times (UTC, sorted) for one instrument.

    Reads only ``SourceCloseTime`` from the newest calendar-emission run — timestamps,
    never prices. Open = close - 240 minutes.
    """
    runs = sorted(CAL_ROOT.glob(f"random_hold_{symbol.lower()}_4h_*"))
    if not runs:
        raise FileNotFoundError(f"No calendar emission for {symbol} under {CAL_ROOT}")
    closes = (
        pl.read_parquet(runs[-1] / "positions.parquet", columns=["SourceCloseTime"])
        .sort("SourceCloseTime")["SourceCloseTime"]
        .to_list()
    )
    return [t - timedelta(minutes=DOMAIN_MINUTES) for t in closes]


def build_schedule(opens: list, seed: int, shift: int = 0) -> list[tuple]:
    """One seeded schedule: rows (fill_bar_open_utc, level=0, dir, hold_bars).

    ``shift`` moves every entry to the next calendar bar (delay twin); dir/hold are
    unchanged so the twin is the same draw displaced wholesale by one bar.
    """
    rng = np.random.default_rng(seed)
    n = len(opens)
    rows: list[tuple] = []
    idx = WARMUP_BARS
    k = 0
    while True:
        idx += int(rng.integers(GAP_LO, GAP_HI + 1))
        if idx >= n:
            break
        direction = 1 if rng.integers(0, 2) == 1 else -1
        hold = HOLD_GRID[k % len(HOLD_GRID)]
        k += 1
        fill_idx = idx + shift
        if fill_idx + hold > n - 2:      # drop can't-complete (D3); twin drops by its own rule
            continue
        rows.append((opens[fill_idx], 0, direction, hold))
    return rows


def write_csv(path: Path, rows: list[tuple]) -> None:
    with path.open("w") as f:
        f.write("open_time_utc,level,dir,hold_bars\n")
        for t, level, direction, hold in rows:
            f.write(f"{t.strftime('%Y-%m-%dT%H:%M:%SZ')},{level},{direction},{hold}\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--symbols", nargs="*", default=SYMBOLS)
    ap.add_argument("--seeds", nargs="*", type=int, default=list(range(1, N_SEEDS + 1)))
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for symbol in args.symbols:
        opens = load_calendar(symbol)
        for i in args.seeds:
            seed = BASE_SEED + i
            rows = build_schedule(opens, seed)
            out = OUT_DIR / f"EXP-019-4h-{symbol}_seed{i}.csv"
            write_csv(out, rows)
            line = f"{symbol} seed{i}: {len(rows)} entries -> {out.name}"
            if symbol in SHIFT_SYMBOLS:
                srows = build_schedule(opens, seed, shift=1)
                sout = OUT_DIR / f"EXP-019-4h-{symbol}_seed{i}_shift1.csv"
                write_csv(sout, srows)
                line += f"; shift1: {len(srows)} entries"
            print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
