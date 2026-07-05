"""EXP-020 data-analyst common loaders (analyst-owned; canonical xen estimands only)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[4]  # repo root
RUNS = ROOT / "data" / "strategy_runs"
RESULTS = Path(__file__).resolve().parents[1] / "results"
PLOTS = Path(__file__).resolve().parents[1] / "plots"

MR_BLOCK = ["NZDUSD", "AUDUSD", "GBPUSD", "USDCAD"]
RW_BLOCK = ["BTCUSD", "USDJPY", "AUDJPY", "GBPJPY", "EURJPY", "XAUUSD", "USDCHF"]
MID_BLOCK = ["EURUSD", "USTEC", "US500", "US2000", "JP225"]
ALL_SYMBOLS = MR_BLOCK + RW_BLOCK + MID_BLOCK

ROOTS = {
    "R": RUNS / "EXP-020-R",
    "R-twin": RUNS / "EXP-020-R-twin",
    "G": RUNS / "EXP-020-G",
    "G-invert": RUNS / "EXP-020-G-invert",
    "R-delay1": RUNS / "EXP-020-R-delay1",
    "G-delay1": RUNS / "EXP-020-G-delay1",
}

BLOCK_BARS = 60  # design §8 block bootstrap block length (~10 days of 4h bars)


def block_of(symbol: str) -> str:
    if symbol in MR_BLOCK:
        return "MR"
    if symbol in RW_BLOCK:
        return "RW"
    return "mid"


def params_table() -> pl.DataFrame:
    """A1 derived params (g, b_w, weekend spread ceiling, commission)."""
    return pl.read_csv(RESULTS / "exp020_params.csv")


def run_dirs(arm: str) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for d in sorted(ROOTS[arm].iterdir()):
        if not d.is_dir():
            continue
        meta = json.loads((d / "run_metadata.json").read_text())
        out[meta["symbol"]] = d
    return out


def load_run(arm: str, symbol: str) -> dict:
    d = run_dirs(arm)[symbol]
    return {
        "dir": d,
        "meta": json.loads((d / "run_metadata.json").read_text()),
        "positions": pl.read_parquet(d / "positions.parquet"),
        "cis_trades": pl.read_parquet(d / "cis_trades.parquet"),
        "trade_blotter": pl.read_parquet(d / "trade_blotter.parquet"),
        "events": pl.read_parquet(d / "events.parquet"),
    }


def portfolio_value(pos: pl.DataFrame) -> np.ndarray:
    """Per-bar portfolio value V = PortUnits*Close + PortCash (post-warmup rows)."""
    p = pos.filter(~pl.col("Warmup"))
    return (p["PortUnits"] * p["RealClose"] + p["PortCash"]).to_numpy()


def per_bar_log_returns(pos: pl.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """(times, per-bar log returns) of the emitted portfolio path."""
    p = pos.filter(~pl.col("Warmup")).sort("SourceCloseTime")
    v = (p["PortUnits"] * p["RealClose"] + p["PortCash"]).to_numpy()
    t = p["SourceCloseTime"].to_numpy()
    r = np.diff(np.log(v))
    return t[1:], r
