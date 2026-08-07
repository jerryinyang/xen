"""cTrader replication read — INDEPENDENT, SEPARATE, NEVER POOLED (design §10, AMENDMENT-C1).

    "Crypto pooled = the powered estimate. cTrader (EURUSD / XAUUSD / USTEC, INFR-021 fence) =
     independent replication read, scored and reported separately, never pooled into ``n``."
                                                             — SoT §5.4, operator-signed

Three things follow, and all three are enforced here:

  1. **Its own fence.** ``xen.nautilus.catalog_fence.load_fence_manifest`` defaults to the BYBIT
     INFR-011 manifest. The cTrader path is passed EXPLICITLY, every time. Its ``train_end`` is
     2023-11-22 (not 2023-12-18) and its holdout opens 2024-12-13 (not 2025-01-08).
  2. **Never pooled.** Nothing in this module returns rows that join to the crypto cells; the
     output lands in its own artifact and carries ``role='REPLICATION_ONLY'`` on every row.
  3. **Gross only.** The Bybit fee/funding overlay does not apply to these instruments and this
     programme has no sanctioned cTrader cost table (spread is unavailable and never charged).
     So the break-even reported here is the GROSS one, ``p_be = L/(W+L)``, and it is labelled as
     such. Inventing a cost model to produce a net number would be a fabricated cost claim.

The object replicated is arm B's: SPDR-013's episode under its declared capture geometry, built
with SPDR-013's own indicator and signal modules. The question it answers is narrow — does the
``(p, W, L, W/L)`` shape measured on crypto look the same on a different asset class? — and its
answer is credibility, never power (AMENDMENT-S1).
"""
from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import polars as pl
import pyarrow.parquet as pq

import cells
import parents
from config import (
    CTRADER_BAR_DIR,
    CTRADER_BAR_TYPE_SUFFIX,
    CTRADER_FENCE_PATH,
    CTRADER_FENCE_SHA256,
    CTRADER_HOLDOUT_START_NS,
    CTRADER_SYMBOLS,
    CTRADER_TRAIN_END_NS,
    NS,
)

_FIXED_POINT_SCALE = 1e16
_TWO64 = float(2 ** 64)
_OHLCV = ("open", "high", "low", "close", "volume")

#: the replication clocks — arm B's own (design §10 "Clocks inherited per arm")
CLOCKS = ("H1", "M15")


def fence():
    """The cTrader fence, loaded from the EXPLICIT path and hash-verified against the design."""
    from xen.nautilus.catalog_fence import load_fence_manifest
    m = load_fence_manifest(CTRADER_FENCE_PATH)
    if m.sha256 != CTRADER_FENCE_SHA256:
        raise AssertionError(
            f"cTrader fence sha256 mismatch: expected {CTRADER_FENCE_SHA256}, got {m.sha256}")
    return m


def _decode_i128(arr) -> np.ndarray:
    buf = np.frombuffer(arr.buffers()[1], dtype=np.uint64)
    n = len(arr)
    off = arr.offset * 2
    lo = buf[off: off + 2 * n: 2].astype(np.float64)
    hi = buf[off + 1: off + 2 * n: 2].astype(np.float64)
    return (lo + hi * _TWO64) / _FIXED_POINT_SCALE


def load_minutes(symbol: str) -> pl.DataFrame:
    """Fenced cTrader minute bars. HARD-stops at the cTrader ``train_end``, not the Bybit one."""
    m = fence()
    start = m.analysis_start_utc
    end = datetime.fromtimestamp(CTRADER_TRAIN_END_NS / NS, tz=timezone.utc)
    from xen.nautilus.catalog_fence import assert_within_fence
    assert_within_fence(m, start, end, band="TRAIN")

    d = CTRADER_BAR_DIR / f"{symbol}{CTRADER_BAR_TYPE_SUFFIX}"
    schema = {"ts_event": pl.Int64, "open": pl.Float64, "high": pl.Float64,
              "low": pl.Float64, "close": pl.Float64, "volume": pl.Float64}
    if not d.exists():
        return pl.DataFrame(schema=schema)
    lo_ns, hi_ns = int(start.timestamp() * NS), CTRADER_TRAIN_END_NS
    frames = []
    for f in sorted(d.glob("*.parquet")):
        tbl = pq.read_table(f, columns=["ts_event", *_OHLCV])
        if tbl.num_rows == 0:
            continue
        ts = tbl.column("ts_event").combine_chunks().to_numpy().astype(np.int64)
        keep = (ts >= lo_ns) & (ts < hi_ns)
        if not keep.any():
            continue
        cols = {"ts_event": ts[keep]}
        for name in _OHLCV:
            cols[name] = _decode_i128(tbl.column(name).combine_chunks())[keep]
        frames.append(pl.DataFrame(cols, schema=schema))
    if not frames:
        return pl.DataFrame(schema=schema)
    out = pl.concat(frames).sort("ts_event")
    hi = int(out["ts_event"].max())
    if hi >= CTRADER_TRAIN_END_NS:
        raise AssertionError(f"cTrader read crossed its own TRAIN fence: {hi}")
    if hi >= CTRADER_HOLDOUT_START_NS:
        raise AssertionError("cTrader read touched the sealed cTrader holdout")
    return out


def episodes(symbol: str, clock: str) -> pl.DataFrame:
    """SPDR-013's episode object, rebuilt on cTrader bars with SPDR-013's own modules.

    Signals: ``D-ZZ`` (the structural leg) and the ``D-SMA`` cells, exactly as the parent defines
    them. Exit: ``signalflip`` — hold from the open after a confirmation to the open after the
    next. No parameter is tuned and no arm is added (SoT §1.2: direction is measured, not
    targeted).
    """
    m13 = parents.load("SPDR-013")
    cat = m13["catalog_io"]
    minutes = load_minutes(symbol)
    if minutes.height == 0:
        return pl.DataFrame()
    bars = cat.aggregate_clock(minutes, clock)
    cb = bars.filter(pl.col("complete")).sort("slot_start")
    if cb.height < 200:
        return pl.DataFrame()

    high, low = cb["high"].to_numpy(), cb["low"].to_numpy()
    close, op = cb["close"].to_numpy(), cb["open"].to_numpy()
    ss = cb["slot_start"].to_numpy().astype(np.int64)
    atr = m13["indicators"].wilder_atr(high, low, close)
    atr_lag = np.full(atr.size, np.nan)
    atr_lag[1:] = atr[:-1]

    sigs: dict[str, np.ndarray] = {}
    swings = m13["indicators"].atr_zigzag(close, atr,
                                          parents.const("SPDR-013", "ATR_PERIOD") + 1)
    sigs["D-ZZ"] = m13["arms"].zz_signal(close.size, swings)
    for (period, mode), s in m13["arms"].sma_cells(close, atr_lag).items():
        sigs[f"D-SMA{period}_angle-{mode}"] = s

    rows = []
    for name, sig in sigs.items():
        flips = np.where((sig[1:] != sig[:-1]) & (sig[1:] != 0))[0] + 1
        for a, b in zip(flips[:-1], flips[1:]):
            e, x = a + 1, b + 1
            if x >= close.size:
                break
            side = float(sig[a])
            gross = side * (op[x] / op[e] - 1.0) * 1e4
            rows.append({"symbol": symbol, "clock": clock, "signal": name,
                         "exit_mode": "signalflip", "side": side,
                         "entry_ts": int(ss[e]), "exit_ts": int(ss[x]),
                         "entry_open": float(op[e]), "exit_open": float(op[x]),
                         "gross_bps": float(gross), "hold_bars": int(x - e)})
    return pl.DataFrame(rows) if rows else pl.DataFrame()


def run(*, n_boot: int | None = None) -> tuple[list[dict], int | None]:
    """The replication read. Returns (rows, max ts touched) — the latter feeds the self-check."""
    from config import BOOT_RESAMPLES
    n_boot = n_boot or BOOT_RESAMPLES
    out: list[dict] = []
    max_ts: int | None = None

    for symbol in CTRADER_SYMBOLS:
        for clock in CLOCKS:
            eps = episodes(symbol, clock)
            if eps.is_empty():
                out.append({"arm": "CTRADER", "role": "REPLICATION_ONLY", "symbol": symbol,
                            "clock": clock, "status": "NO_FENCED_BARS",
                            "note": "retained, never silently dropped"})
                continue
            df = eps.to_pandas()
            max_ts = max(max_ts or 0, int(df["exit_ts"].max()))
            for (sig, em), g in df.groupby(["signal", "exit_mode"], observed=True):
                # gross basis only — see the module docstring. cost_bps = 0 makes p_be_net == p_be,
                # and the field is labelled so no reader can mistake it for a net figure.
                rec = cells.score_signed_cell(
                    g, arm="B", item="cTrader-replication",
                    key={"symbol": symbol, "clock": clock, "signal": sig, "exit_mode": em,
                         "band": "CTRADER_TRAIN", "basis": "replication_gross_only"},
                    gross_col="gross_bps", net_col="gross_bps", ts_col="entry_ts",
                    exit_ts_col="exit_ts", h=None,
                    clock_minutes=parents.const("SPDR-013", "CLOCKS")[clock]["minutes"],
                    n_boot=n_boot)
                rec.update({
                    "arm": "CTRADER", "role": "REPLICATION_ONLY",
                    "pooled_into_powered_estimate": False,
                    "cost_basis": "GROSS ONLY — no sanctioned cTrader cost table exists",
                    "break_even_reported": "p_be (GROSS). p_be_net is NOT reported here.",
                    "fence": "INFR-021 cTrader manifest, train_end 2023-11-22, holdout 2024-12-13",
                    "fence_sha256": CTRADER_FENCE_SHA256,
                    "interpretation_role": ("independent replication / credibility only — never "
                                            "power, never pooled (AMENDMENT-C1 / AMENDMENT-S1)"),
                })
                rec.pop("p_be_net", None)
                rec.pop("edge", None)
                rec.pop("edge_ci_low", None)
                rec.pop("edge_ci_high", None)
                out.append(rec)
    return out, max_ts
