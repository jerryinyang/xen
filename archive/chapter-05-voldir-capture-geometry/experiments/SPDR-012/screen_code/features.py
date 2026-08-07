"""Per-clock realised measures, features and targets (design §3.2, §3.3).

Every feature at origin ``i`` is a function of completed bars ``<= i`` only. Targets are
strictly one clock bar ahead of the origin.

Causality note (interpretation IN-7, see :data:`TARGET_NOTE`): design §3.2 writes
``abs_oo_i = 1e4*|O_{i+1}/O_i - 1|`` and design §3.3 states "Target = next bar's abs_oo".
``O_{i+1}`` is the traded price at the origin instant ``slot_end_i``, so ``abs_oo_i`` is
already known at origin ``i``; using it as origin ``i``'s target would violate design §7.4
("targets use next bar only") and the SPDR lane causal-lag rule. The forecast target is
therefore the NEXT bar's open-to-open move, ``target_abs_oo_i = oo_move_{i+1}``, entered at
``O_{i+1}`` — the same one-step-ahead horizon as ``rv_next_i``. The origin-known variant is
still emitted as ``oo_move`` for disclosure.
"""
from __future__ import annotations

import numpy as np
import polars as pl

from config import (
    CLOCKS,
    EWMA_LAMBDA,
    HAR_MEANS,
    NS,
    RV_WINDOW,
    SESSION_EDGES,
    WARMUP_DAYS,
)

TARGET_NOTE = (
    "target_abs_oo_i = 1e4*|O_{i+2}/O_{i+1} - 1| (move realised over bar i+1, entered at "
    "O_{i+1}); origin-known variant oo_move_i = 1e4*|O_{i+1}/O_i - 1| emitted for disclosure"
)

FEATURE_COLS = ("rv20", "ewma_vol", "parkinson", "gk")


def _ewma_vol(r: np.ndarray, lam: float) -> np.ndarray:
    """Causal RiskMetrics EWMA volatility: sigma^2_i = lam*sigma^2_{i-1} + (1-lam)*r_i^2."""
    out = np.full(r.shape, np.nan)
    var = np.nan
    for i in range(r.size):
        ri = r[i]
        if not np.isfinite(ri):
            out[i] = np.sqrt(var) if np.isfinite(var) else np.nan
            continue
        var = ri * ri if not np.isfinite(var) else lam * var + (1.0 - lam) * ri * ri
        out[i] = np.sqrt(var)
    return out


def _rolling_mean(x: np.ndarray, w: int) -> np.ndarray:
    s = pl.Series(x)
    return s.rolling_mean(window_size=w, min_periods=w).to_numpy()


def _rolling_median(x: np.ndarray, w: int) -> np.ndarray:
    s = pl.Series(x)
    return s.rolling_median(window_size=w, min_periods=w).to_numpy()


def build_features(clock_bars: pl.DataFrame, clock: str) -> pl.DataFrame:
    """Feature/target frame over COMPLETE clock bars (design §3.2-§3.3).

    Parameters
    ----------
    clock_bars : pl.DataFrame
        Output of :func:`catalog_io.aggregate_clock` (complete + incomplete rows).
    clock : str
        ``"H1"``, ``"H4"`` or ``"D1"``.

    Returns
    -------
    pl.DataFrame
        One row per complete bar, time-ordered, with realised measures, HAR regressors,
        one-step-ahead targets, calendar attributes and the ``is_origin`` warm-up flag.
    """
    spec = CLOCKS[clock]
    cb = clock_bars.filter(pl.col("complete")).sort("slot_start")
    if cb.height < 3:
        return pl.DataFrame(schema=_schema())

    slot_start = cb["slot_start"].to_numpy()
    slot_end = cb["slot_end"].to_numpy()
    o = cb["open"].to_numpy()
    h = cb["high"].to_numpy()
    lo = cb["low"].to_numpy()
    c = cb["close"].to_numpy()
    n = o.size
    span_ns = spec["minutes"] * 60 * NS

    # --- returns and realised measures (design §3.2) ---
    r = np.full(n, np.nan)
    r[1:] = np.log(c[1:] / c[:-1])
    rv_cc = r * r

    rv20 = np.sqrt(_rolling_mean(rv_cc, RV_WINDOW))
    ewma_vol = _ewma_vol(r, EWMA_LAMBDA)

    with np.errstate(divide="ignore", invalid="ignore"):
        ln_hl = np.log(h / lo)
        ln_co = np.log(c / o)
    parkinson = np.sqrt(ln_hl**2 / (4.0 * np.log(2.0)))
    gk_var = 0.5 * ln_hl**2 - (2.0 * np.log(2.0) - 1.0) * ln_co**2
    gk = np.where(np.isfinite(gk_var) & (gk_var > 0), np.sqrt(np.abs(gk_var)), 0.0)
    bad_ohlc = ~np.isfinite(ln_hl) | ~np.isfinite(ln_co) | (h <= 0) | (lo <= 0)
    gk = np.where(bad_ohlc, 0.0, gk)
    parkinson = np.where(bad_ohlc, np.nan, parkinson)

    rv20_mean_6 = _rolling_mean(rv20, HAR_MEANS[0])
    rv20_mean_24 = _rolling_mean(rv20, HAR_MEANS[1])
    abs_r = np.abs(r)

    # --- open-to-open moves and one-step-ahead targets (design §3.2-§3.3) ---
    oo_move = np.full(n, np.nan)                       # move over bar i, known at slot_end_i
    oo_move[:-1] = 1e4 * np.abs(o[1:] / o[:-1] - 1.0)
    target_abs_oo = np.full(n, np.nan)                 # target for origin i = oo_move_{i+1}
    target_abs_oo[:-1] = oo_move[1:]
    rv_next = np.full(n, np.nan)                       # rv20 measured at end of bar i+1
    rv_next[:-1] = rv20[1:]

    next_contiguous = np.zeros(n, dtype=bool)
    next_contiguous[:-1] = (slot_start[1:] - slot_start[:-1]) == span_ns
    target_contiguous = np.zeros(n, dtype=bool)        # bars i+1 and i+2 both adjacent
    target_contiguous[:-2] = next_contiguous[:-2] & next_contiguous[1:-1]

    # --- calendar attributes of the FORECAST bar i+1 (deterministic, known at origin) ---
    tgt_slot_start = np.full(n, -1, dtype=np.int64)
    tgt_slot_start[:-1] = slot_start[1:]
    tgt_sec = tgt_slot_start // NS
    hour = (tgt_sec % 86400) // 3600
    session = np.digitize(hour, SESSION_EDGES[1:-1], right=False)  # 0,1,2
    dow = ((tgt_sec // 86400) + 4) % 7                             # 1970-01-01 = Thursday
    target_date = (tgt_sec // 86400).astype(np.int64)               # UTC day index

    # --- warm-up (design §0): >=60 calendar days of complete history AND per-clock bars ---
    bar_index = np.arange(n)
    warm_ts = slot_end[0] + WARMUP_DAYS * 86400 * NS
    feat_ok = (
        np.isfinite(rv20) & np.isfinite(ewma_vol) & np.isfinite(parkinson)
        & np.isfinite(gk) & np.isfinite(rv20_mean_24) & np.isfinite(rv20_mean_6)
    )
    is_origin = (
        feat_ok
        & (slot_end >= warm_ts)
        & (bar_index >= spec["warmup_bars"])
        & np.isfinite(target_abs_oo)
        & (tgt_slot_start > 0)
    )

    return pl.DataFrame(
        {
            "slot_start": slot_start, "slot_end": slot_end,
            "open": o, "high": h, "low": lo, "close": c,
            "r": r, "rv_cc": rv_cc, "abs_r": abs_r,
            "rv20": rv20, "ewma_vol": ewma_vol, "parkinson": parkinson, "gk": gk,
            "rv20_mean_6": rv20_mean_6, "rv20_mean_24": rv20_mean_24,
            "oo_move": oo_move, "target_abs_oo": target_abs_oo, "rv_next": rv_next,
            "next_contiguous": next_contiguous, "target_contiguous": target_contiguous,
            "target_slot_start": tgt_slot_start, "target_date": target_date,
            "session": session.astype(np.int64), "dow": dow.astype(np.int64),
            "is_origin": is_origin,
        },
        schema=_schema(),
    )


def _schema() -> dict:
    f = pl.Float64
    return {
        "slot_start": pl.Int64, "slot_end": pl.Int64,
        "open": f, "high": f, "low": f, "close": f,
        "r": f, "rv_cc": f, "abs_r": f,
        "rv20": f, "ewma_vol": f, "parkinson": f, "gk": f,
        "rv20_mean_6": f, "rv20_mean_24": f,
        "oo_move": f, "target_abs_oo": f, "rv_next": f,
        "next_contiguous": pl.Boolean, "target_contiguous": pl.Boolean,
        "target_slot_start": pl.Int64, "target_date": pl.Int64,
        "session": pl.Int64, "dow": pl.Int64,
        "is_origin": pl.Boolean,
    }


def add_regime_states(df: pl.DataFrame, clock: str, window: int) -> pl.DataFrame:
    """V-REGIME observed 2-state discretisation: HIGH iff rv20 > trailing median (design §4).

    The trailing median window ends at bar ``i`` inclusive, so the state at ``i`` uses
    bars ``<= i`` only.
    """
    rv20 = df["rv20"].to_numpy()
    med = _rolling_median(rv20, window)
    state = np.where(np.isfinite(med) & np.isfinite(rv20), (rv20 > med).astype(np.int64), -1)
    return df.with_columns(
        pl.Series("regime_median", med),
        pl.Series("regime_state", state),  # 1 = HIGH, 0 = LOW, -1 = undefined
    )
