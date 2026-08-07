"""Level features + three state models (design §2.1–2.3).

R-MARKOV: HIGH iff rv20 ≥ trailing median of rv20 over warm-up window ending at t.
R-HMM-RV: 2-state Gaussian HMM on raw rv20 (causal monthly fit).
R-SHOCK: HIGH iff |r_t| ≥ expanding p90 of |r| — named shock comparator only.
"""
from __future__ import annotations

import numpy as np
import polars as pl

from config import (
    CLOCKS,
    DUR_CAP,
    EWMA_LAMBDA,
    N_HIGH_K,
    NS,
    RV_WINDOW,
    RUN_LEN_CAP,
)
from hmm import walk_forward_states


def _rolling_mean(x: np.ndarray, w: int) -> np.ndarray:
    s = pl.Series(x)
    return s.rolling_mean(window_size=w, min_periods=w).to_numpy()


def _rolling_median(x: np.ndarray, w: int) -> np.ndarray:
    s = pl.Series(x)
    return s.rolling_median(window_size=w, min_periods=w).to_numpy()


def _parkinson_ewma(high: np.ndarray, low: np.ndarray, lam: float) -> np.ndarray:
    """Causal Parkinson EWMA of variance, returned as sqrt (level)."""
    with np.errstate(divide="ignore", invalid="ignore"):
        ln_hl = np.log(high / low)
    park_var = (ln_hl ** 2) / (4.0 * np.log(2.0))
    park_var = np.where(np.isfinite(park_var) & (high > 0) & (low > 0), park_var, np.nan)
    out = np.full(high.size, np.nan)
    var = np.nan
    for i in range(high.size):
        v = park_var[i]
        if not np.isfinite(v):
            out[i] = np.sqrt(var) if np.isfinite(var) else np.nan
            continue
        var = v if not np.isfinite(var) else lam * var + (1.0 - lam) * v
        out[i] = np.sqrt(var) if var >= 0 else np.nan
    return out


def _expanding_pct(x: np.ndarray) -> np.ndarray:
    """Expanding percentile rank of x_t among x_0..x_t (causal)."""
    out = np.full(x.size, np.nan)
    for i in range(x.size):
        if not np.isfinite(x[i]):
            continue
        hist = x[: i + 1]
        hist = hist[np.isfinite(hist)]
        if hist.size == 0:
            continue
        out[i] = float(np.mean(hist <= x[i]))
    return out


def _expanding_p90(x: np.ndarray) -> np.ndarray:
    """Expanding 90th percentile of x using history < t for threshold at t (strict causal).

    At bar t, threshold = p90(x[:t]) so bar t is not in its own threshold.
    """
    out = np.full(x.size, np.nan)
    for i in range(1, x.size):
        hist = x[:i]
        hist = hist[np.isfinite(hist)]
        if hist.size < 20:
            continue
        out[i] = float(np.percentile(hist, 90))
    return out


def _duration(state: np.ndarray, cap: int = DUR_CAP) -> np.ndarray:
    """Bars already spent in current state (including t), capped."""
    n = state.size
    dur = np.zeros(n, dtype=np.int64)
    for i in range(n):
        if state[i] < 0:
            dur[i] = 0
            continue
        if i == 0 or state[i] != state[i - 1] or state[i - 1] < 0:
            dur[i] = 1
        else:
            dur[i] = min(cap, dur[i - 1] + 1)
    return dur


def _n_high_last_k(state: np.ndarray, k: int) -> np.ndarray:
    out = np.full(state.size, np.nan)
    for i in range(state.size):
        lo = max(0, i - k + 1)
        seg = state[lo : i + 1]
        valid = seg[seg >= 0]
        if valid.size == 0:
            continue
        out[i] = float(np.sum(valid == 1))
    return out


def _remaining_run_len(state: np.ndarray, cap: int = RUN_LEN_CAP) -> np.ndarray:
    """Remaining consecutive bars in current state from t+1, censored at cap."""
    n = state.size
    out = np.full(n, np.nan)
    for t in range(n - 1):
        if state[t] < 0:
            continue
        s = state[t]
        cnt = 0
        for u in range(t + 1, min(n, t + 1 + cap)):
            if state[u] < 0:
                break
            if state[u] == s:
                cnt += 1
            else:
                break
        out[t] = float(cnt)  # censored at cap if still running
    return out


def _month_keys(slot_end_ns: np.ndarray) -> np.ndarray:
    """UTC year*12+month from slot_end ns."""
    sec = slot_end_ns // NS
    # approximate month via day index is not needed — use datetime-free formula
    # days since epoch
    days = sec // 86400
    # use numpy datetime64 for correctness
    dt = (slot_end_ns // 1_000_000).astype("datetime64[ms]")
    years = dt.astype("datetime64[Y]").astype(int) + 1970
    months = dt.astype("datetime64[M]").astype(int) % 12 + 1
    return (years * 12 + months).astype(np.int64)


def build_bar_frame(clock_bars: pl.DataFrame, clock: str) -> pl.DataFrame:
    """Complete-bar frame with r, rv20, park_ewma, abs_oo next, origin flags."""
    spec = CLOCKS[clock]
    cb = clock_bars.filter(pl.col("complete")).sort("slot_start")
    if cb.height < 3:
        return pl.DataFrame()

    slot_start = cb["slot_start"].to_numpy()
    slot_end = cb["slot_end"].to_numpy()
    o = cb["open"].to_numpy()
    h = cb["high"].to_numpy()
    lo = cb["low"].to_numpy()
    c = cb["close"].to_numpy()
    n = o.size

    r = np.full(n, np.nan)
    r[1:] = np.log(c[1:] / c[:-1])
    abs_r = np.abs(r)
    rv_cc = r * r
    rv20 = np.sqrt(_rolling_mean(rv_cc, RV_WINDOW))
    park_ewma = _parkinson_ewma(h, lo, EWMA_LAMBDA)
    lvl_pct = _expanding_pct(rv20)

    # next-bar open-to-open |move| in bps (for state gap)
    abs_oo = np.full(n, np.nan)
    abs_oo[:-1] = 1e4 * np.abs(o[1:] / o[:-1] - 1.0)
    next_abs_oo = np.full(n, np.nan)
    next_abs_oo[:-1] = abs_oo[1:]

    target_date = (slot_end // NS // 86400).astype(np.int64)

    bar_index = np.arange(n)
    feat_ok = np.isfinite(rv20) & np.isfinite(park_ewma) & np.isfinite(r)
    is_origin = feat_ok & (bar_index >= spec["warmup_bars"]) & np.isfinite(next_abs_oo)

    return pl.DataFrame({
        "slot_start": slot_start,
        "slot_end": slot_end,
        "open": o, "high": h, "low": lo, "close": c,
        "r": r, "abs_r": abs_r, "rv20": rv20,
        "park_ewma": park_ewma, "lvl_pct": lvl_pct,
        "abs_oo": abs_oo, "next_abs_oo": next_abs_oo,
        "target_date": target_date,
        "is_origin": is_origin,
        "bar_index": bar_index,
    })


def add_state_models(df: pl.DataFrame, clock: str) -> tuple[pl.DataFrame, list[dict]]:
    """Attach R-MARKOV, R-HMM-RV, R-SHOCK states + shared predictors.

    Returns augmented frame and HMM fit log (for integrity / golden traces).
    """
    if df.height == 0:
        return df, []

    spec = CLOCKS[clock]
    rv20 = df["rv20"].to_numpy()
    abs_r = df["abs_r"].to_numpy()
    slot_end = df["slot_end"].to_numpy()
    n = df.height
    w = spec["warmup_bars"]

    # --- R-MARKOV: HIGH iff rv20 >= trailing median over window ending at t ---
    med = _rolling_median(rv20, w)
    markov = np.where(
        np.isfinite(med) & np.isfinite(rv20),
        (rv20 >= med).astype(np.int64),
        -1,
    )

    # --- R-SHOCK: HIGH iff |r| >= expanding p90 of |r| (history < t) ---
    p90 = _expanding_p90(abs_r)
    shock = np.where(
        np.isfinite(p90) & np.isfinite(abs_r),
        (abs_r >= p90).astype(np.int64),
        -1,
    )

    # --- R-HMM-RV: walk-forward on raw rv20 ---
    month_keys = _month_keys(slot_end)
    start_idx = max(w, 60)
    hmm_state, hmm_prob, fits = walk_forward_states(rv20, slot_end, start_idx, month_keys)

    # duration / n_high for markov (primary level); also for hmm
    markov_dur = _duration(markov)
    hmm_dur = _duration(hmm_state)
    n_high_4_m = _n_high_last_k(markov, 4)
    n_high_12_m = _n_high_last_k(markov, 12)
    n_high_4_h = _n_high_last_k(hmm_state, 4)
    n_high_12_h = _n_high_last_k(hmm_state, 12)

    # remaining run lengths (targets)
    run_markov = _remaining_run_len(markov)
    run_hmm = _remaining_run_len(hmm_state)

    out = df.with_columns([
        pl.Series("s_markov", markov),
        pl.Series("s_hmm_rv", hmm_state),
        pl.Series("hmm_high_prob", hmm_prob),
        pl.Series("s_shock", shock),  # shock flag — NOT titled regime
        pl.Series("dur_markov", markov_dur),
        pl.Series("dur_hmm", hmm_dur),
        pl.Series("n_high_4_markov", n_high_4_m),
        pl.Series("n_high_12_markov", n_high_12_m),
        pl.Series("n_high_4_hmm", n_high_4_h),
        pl.Series("n_high_12_hmm", n_high_12_h),
        pl.Series("run_len_markov", run_markov),
        pl.Series("run_len_hmm", run_hmm),
        pl.Series("regime_median", med),
        pl.Series("shock_p90", p90),
    ])
    return out, fits


def future_state_targets(state: np.ndarray, k: int) -> np.ndarray:
    """s_{t+k}; -1 if unavailable."""
    n = state.size
    out = np.full(n, -1, dtype=np.int64)
    if k < 1 or k >= n:
        return out
    out[: n - k] = state[k:]
    return out


def transition_flags(state: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    """trans_up / trans_dn within (t, t+k] given s_t."""
    n = state.size
    up = np.zeros(n, dtype=np.int64)
    dn = np.zeros(n, dtype=np.int64)
    for t in range(n):
        if state[t] < 0:
            continue
        end = min(n, t + k + 1)
        if state[t] == 0:
            for u in range(t + 1, end):
                if state[u] == 1:
                    up[t] = 1
                    break
        elif state[t] == 1:
            for u in range(t + 1, end):
                if state[u] == 0:
                    dn[t] = 1
                    break
    return up, dn
