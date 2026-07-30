"""A1 — Independent M15 apparatus verification (data-analyst, SPDR-019 phase (a)).

Verifies, WITHOUT importing screen_code:
  1. M15 entry fills against raw M1 catalog bars (stop-price / gap-open rule, causality).
  2. M15 hold conversion: hours -> bars. L0 activeHold = 1 HOUR = 4 M15 bars, not 1 and not 4h.
  3. The day-block rule behaves as a CALENDAR-DAY rule on M15 (n_dates == distinct UTC dates).
  4. inactiveHold expiry window on M15 (2 hours).
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[3]          # python/
REPO = ROOT.parent
RES = REPO / "python/experiments/SPDR-019/results"
CATALOG = REPO / "data/catalog/data/bar"
NS = 1_000_000_000
TRAIN_END_NS = int(datetime(2023, 12, 18, tzinfo=timezone.utc).timestamp() * NS)
_OHLCV = ("open", "high", "low", "close", "volume")
_SCALE = 1e16
_TWO64 = float(2**64)


def _decode_i128(arr) -> np.ndarray:
    buf = np.frombuffer(arr.buffers()[1], dtype=np.uint64)
    n, off = len(arr), arr.offset * 2
    lo = buf[off : off + 2 * n : 2].astype(np.float64)
    hi = buf[off + 1 : off + 2 * n : 2].astype(np.float64)
    return (lo + hi * _TWO64) / _SCALE


def load_m1(symbol: str) -> pl.DataFrame:
    """Raw fenced 1m bars, decoded independently of screen_code."""
    cands = list(CATALOG.glob(f"{symbol}*"))
    if not cands:
        raise FileNotFoundError(f"no catalog dir for {symbol}: {CATALOG}")
    d = sorted(cands)[0]
    frames = []
    for f in sorted(d.glob("*.parquet")):
        tbl = pq.read_table(f, columns=["ts_event", *_OHLCV])
        if tbl.num_rows == 0:
            continue
        ts = tbl.column("ts_event").combine_chunks().to_numpy().astype(np.int64)
        keep = ts < TRAIN_END_NS
        if not keep.any():
            continue
        cols = {"ts_event": ts[keep]}
        for nm in _OHLCV:
            cols[nm] = _decode_i128(tbl.column(nm).combine_chunks())[keep]
        frames.append(pl.DataFrame(cols))
    return pl.concat(frames).sort("ts_event") if frames else pl.DataFrame()


def check_fills(ep: pl.DataFrame, m1: pl.DataFrame, label: str) -> dict:
    """Re-derive each episode's fill from raw M1 bars under design §2's rule."""
    ts = m1["ts_event"].to_numpy()
    op, hi, lo = (m1[c].to_numpy() for c in ("open", "high", "low"))
    rows = []
    for r in ep.iter_rows(named=True):
        # the fill bar: the M1 bar whose ts_event == fill_ts
        j = int(np.searchsorted(ts, r["fill_ts"]))
        ok_idx = j < len(ts) and ts[j] == r["fill_ts"]
        if not ok_idx:
            rows.append({"id": r["signal_ts"], "status": "FILL_TS_NOT_AN_M1_BAR"})
            continue
        stop, side, fp = r["stop_price"], r["side"], r["fill_price"]
        gapped = (op[j] > stop) if side > 0 else (op[j] < stop)
        expect = op[j] if gapped else stop
        traded_through = (hi[j] >= stop) if side > 0 else (lo[j] <= stop)
        # causality: bar covers (ts-60s, ts]; it must START at or after the decision close
        causal = (r["fill_ts"] - 60 * NS) >= r["decision_end_ns"]
        rows.append({
            "id": r["signal_ts"], "status": "OK",
            "expect": expect, "emitted": fp,
            "match": abs(expect - fp) <= 1e-9 * max(1.0, abs(expect)),
            "traded_through": bool(traded_through), "gapped": bool(gapped),
            "causal": bool(causal), "fill_kind": r["fill_kind"],
        })
    d = pl.DataFrame(rows)
    ok = d.filter(pl.col("status") == "OK")
    return {
        "label": label, "n": d.height, "n_ok_idx": ok.height,
        "n_price_match": int(ok["match"].sum()) if ok.height else 0,
        "n_traded_through": int(ok["traded_through"].sum()) if ok.height else 0,
        "n_gapped": int(ok["gapped"].sum()) if ok.height else 0,
        "n_causal": int(ok["causal"].sum()) if ok.height else 0,
        "bad_status": d.filter(pl.col("status") != "OK")["status"].to_list()[:5],
    }


def main() -> None:
    ep_all = pl.scan_parquet(RES / "episodes.parquet")

    # ---------- 2. HOLD CONVERSION (hours -> bars) on BOTH clocks ----------
    print("=" * 78)
    print("CHECK 2 — hold conversion, hours -> bars, per clock/variant")
    print("=" * 78)
    hold = (
        ep_all.filter(pl.col("exit_reason") == "TIME")
        .with_columns(((pl.col("exit_ts") - pl.col("fill_ts")) / (3600 * NS)).alias("held_h"))
        .group_by(["clock", "variant_id"])
        .agg(
            pl.len().alias("n"),
            pl.col("active_hold_hours").min().alias("ah_min"),
            pl.col("active_hold_hours").max().alias("ah_max"),
            pl.col("held_h").min().alias("held_min"),
            pl.col("held_h").median().alias("held_p50"),
            pl.col("held_h").max().alias("held_max"),
        )
        .collect()
        .sort(["variant_id", "clock"])
    )
    with pl.Config(tbl_rows=100, tbl_width_chars=200):
        print(hold.filter(pl.col("variant_id").str.starts_with("L4_HOLD")
                          | (pl.col("variant_id") == "L0_BASELINE")))

    # exit-grid alignment: M15 exits must land on 15m boundaries, H1 on 60m
    grid = (
        ep_all.filter(pl.col("exit_reason") == "TIME")
        .with_columns((pl.col("exit_ts") % (15 * 60 * NS) == 0).alias("on_m15"),
                      (pl.col("exit_ts") % (60 * 60 * NS) == 0).alias("on_h1"))
        .group_by("clock").agg(pl.len().alias("n"),
                               pl.col("on_m15").mean().alias("frac_on_15m_grid"),
                               pl.col("on_h1").mean().alias("frac_on_60m_grid"))
        .collect()
    )
    print("\ntime-exit timestamp grid alignment:")
    print(grid)

    # ---------- 1. M15 FILL verification on raw M1 ----------
    print("\n" + "=" * 78)
    print("CHECK 1 — M15 entry fills re-derived from raw M1 catalog")
    print("=" * 78)
    for sym in ("BTCUSDT", "SOLUSDT"):
        m1 = load_m1(sym)
        for clock in ("M15", "H1"):
            ep = (
                ep_all.filter(
                    (pl.col("symbol") == sym) & (pl.col("clock") == clock)
                    & (pl.col("variant_id") == "L0_BASELINE") & (pl.col("delta") == 0.5)
                )
                .sort("signal_ts").head(400).collect()
            )
            print(check_fills(ep, m1, f"{sym}/{clock}/L0/d=0.5 first {ep.height}"))

    # ---------- 4. inactiveHold expiry window ----------
    print("\n" + "=" * 78)
    print("CHECK 4 — pending-window length (inactiveHold = 2 hours) per clock")
    print("=" * 78)
    sig = pl.scan_parquet(RES / "signals.parquet")
    print(sig.collect_schema().names())

    # ---------- 3. CALENDAR-DAY blocks ----------
    print("\n" + "=" * 78)
    print("CHECK 3 — n_dates in metrics == distinct UTC calendar dates of episodes")
    print("=" * 78)
    met = pl.read_parquet(RES / "metrics_by_cell.parquet")
    # recompute n_dates independently for pooled TRAIN cells on both clocks
    probe = met.filter(
        (pl.col("scope") == "POOLED") & (pl.col("band") == "TRAIN")
        & pl.col("variant_id").is_in(["L0_BASELINE", "L4_HOLD_20H_UNMOD", "L1_SHAT_DECILE_GE9"])
    ).select(["variant_id", "clock", "delta", "n", "n_dates", "n_days",
              "effective_block_cap"]).sort(["variant_id", "clock", "delta"])
    eps = (
        ep_all.filter(pl.col("band") == "TRAIN")
        .with_columns(
            (pl.col("exit_ts") // (86400 * NS)).alias("day_of_exit"),
            (pl.col("fill_ts") // (86400 * NS)).alias("day_of_fill"),
        )
        .group_by(["variant_id", "clock", "delta"])
        .agg(pl.len().alias("n_ep"),
             pl.col("day_of_exit").n_unique().alias("days_exit"),
             pl.col("day_of_fill").n_unique().alias("days_fill"))
        .collect()
    )
    j = probe.join(eps, on=["variant_id", "clock", "delta"], how="left")
    with pl.Config(tbl_rows=50, tbl_width_chars=200):
        print(j)


if __name__ == "__main__":
    sys.exit(main())
