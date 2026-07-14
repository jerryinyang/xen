#!/usr/bin/env python3
"""EXP-018 random-timing destroy: generate seeded entry schedules from the LIVE emissions.

Design §5 (operator-resolved 2026-07-04): the destroy arm re-plants the live arm's ladder
CADENCE at random times — per-level entry counts, inter-add gap structure, direction mix and
realized holds are preserved by treating each live EPISODE (chain-overlapping legs) as a rigid
template (relative bar offsets, levels, dirs, per-leg BarsHeld) and placing each template's
start bar uniformly at random on the non-warmup TRAIN bar grid (seeded, collision-free).
Exits in the destroy arm are matched-hold market exits (hold_bars column) — never the anchor
(L-08: an anchor exit closes near-anchor random entries instantly and biases the null).

Run AFTER the live cells, BEFORE the -rt twins:
    python3 gen_exp018_schedules.py
Reads  data/strategy_runs/<live-conf-stem>/cross_instrument_spread_mr_<symbol>_4h_*/
Writes schedules/EXP-018/<live-conf-stem>_<SYMBOL>.csv  (open_time_utc,level,dir,hold_bars)

No accounting here: only times, levels, directions, bar counts (no P&L columns are read).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import polars as pl

SEED = 20260704
DOMAIN_MINUTES = 240
HOLD_CAP = 48  # engine FrozenHorizonCap; censored legs' unfinished holds are capped here

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[2]
RUNS = ROOT / "data" / "strategy_runs"
OUT_DIR = SCRIPT_DIR / "schedules" / "EXP-018"

# live conf stem -> (symbols, both_leg)
CELLS = {
    "EXP-018-4h-A-extend": (["US2000", "NZDUSD"], False),
    "EXP-018-4h-A-allow": (["US2000"], False),
    "EXP-018-4h-B-extend": (["US2000"], False),
    "EXP-018-4h-blmkt-A": (["US500"], True),
}


def newest_run_dir(exp_stem: str, symbol: str) -> Path:
    base = RUNS / exp_stem
    cands = sorted(base.glob(f"cross_instrument_spread_mr_{symbol.lower()}_4h_*"))
    if not cands:
        raise SystemExit(f"no live run dir under {base} for {symbol} — run the live cell first")
    return cands[-1]


def load_grid(run_dir: Path) -> tuple[np.ndarray, np.ndarray]:
    """Return (open_times[ns], eligible_mask) for the emitted 4h bar grid."""
    pos = pl.read_parquet(run_dir / "positions.parquet").sort("SourceCloseTime")
    close = pos.get_column("SourceCloseTime").to_numpy()
    open_times = close - np.timedelta64(DOMAIN_MINUTES, "m")
    eligible = ~pos.get_column("Warmup").to_numpy()
    return open_times, eligible


def leg_templates(run_dir: Path, both_leg: bool,
                  open_times: np.ndarray) -> list[list[tuple[int, int, int, int]]]:
    """Live episodes as templates: lists of (bar_offset, level, dir, hold_bars).

    The decision bar of a leg = the bar BEFORE its entry fill (entries fire at next open);
    bar index = searchsorted(open_times, EntryTime) - 1.
    """
    cis = pl.read_parquet(run_dir / "cis_trades.parquet")
    if cis.height == 0:
        return []
    if both_leg:
        # One template row per spread group. The anchor (traded-instrument) leg is emitted first
        # per group (the engine opens it first, fills synchronously), and its Dir == SpreadDir.
        cis = (cis.sort("EntryTime")
               .group_by("SpreadPositionId", maintain_order=True)
               .agg(pl.col("EntryTime").first(),
                    pl.col("Direction").first(),
                    pl.col("BarsHeld").first(),
                    pl.col("Censored").first(),
                    pl.col("ExitTime").max())
               .with_columns(pl.lit(0).alias("LadderLevel")))
    entries = cis.sort("EntryTime").select(
        ["EntryTime", "LadderLevel", "Direction", "BarsHeld", "Censored", "ExitTime"])
    ent = entries.to_dicts()
    # bar index of each leg's decision bar
    idx = np.searchsorted(open_times, entries.get_column("EntryTime").to_numpy()) - 1
    exit_idx = np.searchsorted(open_times, entries.get_column("ExitTime").to_numpy()) - 1

    episodes: list[list[tuple[int, int, int, int]]] = []
    cur: list[tuple[int, int, int, int]] = []
    cur_end = -1
    base = 0
    for k, row in enumerate(ent):
        i = int(idx[k])
        if i < 0:
            continue
        hold = int(row["BarsHeld"]) if int(row["BarsHeld"]) > 0 else 1
        hold = min(hold, HOLD_CAP)
        if cur and i > cur_end:
            episodes.append(cur)
            cur = []
        if not cur:
            base = i
            cur_end = -1
        cur.append((i - base, int(row["LadderLevel"]), int(row["Direction"]), hold))
        cur_end = max(cur_end, int(exit_idx[k]))
    if cur:
        episodes.append(cur)
    return episodes


def place_episodes(episodes, open_times, eligible, rng, both_leg: bool) -> list[tuple]:
    """Place each episode template at a seeded random eligible start bar, collision-free."""
    n = len(open_times)
    occupied = np.zeros(n, dtype=bool)
    rows = []
    for ep in episodes:
        span = max(off + hold for off, _, _, hold in ep) + 1
        placed = False
        for _ in range(10_000):
            s = int(rng.integers(0, n - span))
            if not eligible[s]:
                continue
            window = slice(s, s + span)
            # both-leg (reentry none): whole episodes must not overlap; single-leg ladders may
            # overlap each other exactly as live extend/allow legs may — only both-leg blocks.
            if both_leg and occupied[window].any():
                continue
            for off, level, dr, hold in ep:
                rows.append((open_times[s + off], level, dr, hold))
            if both_leg:
                occupied[window] = True
            placed = True
            break
        if not placed:
            print(f"  WARN: episode span {span} unplaceable after 10k draws — skipped", file=sys.stderr)
    rows.sort(key=lambda r: r[0])
    return rows


def main() -> None:
    rng = np.random.default_rng(SEED)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for stem, (symbols, both_leg) in CELLS.items():
        for sym in symbols:
            run_dir = newest_run_dir(stem, sym)
            open_times, eligible = load_grid(run_dir)
            episodes = leg_templates(run_dir, both_leg, open_times)
            if not episodes:
                print(f"{stem} {sym}: live arm has no legs — no schedule written")
                continue
            rows = place_episodes(episodes, open_times, eligible, rng, both_leg)
            out = OUT_DIR / f"{stem}_{sym}.csv"
            with out.open("w") as f:
                f.write("open_time_utc,level,dir,hold_bars\n")
                for ts, level, dr, hold in rows:
                    iso = np.datetime_as_string(np.datetime64(ts, "s"), timezone="UTC")
                    f.write(f"{iso},{level},{dr},{hold}\n")
            n_ep = len(episodes)
            print(f"{stem} {sym}: {len(rows)} scheduled legs / {n_ep} episodes -> {out.name}")


if __name__ == "__main__":
    main()
