"""Causal volatility components and frozen calibration.

Every value on decision bar ``t`` is a function of H1 bars completed at or before ``t``; the
strategy acts at the next actionable open. Formulas are ported (not imported) from the parent
screens named in :data:`FORMULA_SOURCES` so no experiment script is a runtime dependency.

Component table: adaptive-management-design.md section 4.
Calibration: section 6 - reference values are estimated on the first chronological 20% of TRAIN
after warm-up and then held constant. Expanding models update only from completed observations.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import numpy as np
import polars as pl

# --------------------------------------------------------------------------- #
# Frozen parent constants (ported verbatim)
# --------------------------------------------------------------------------- #

EWMA_LAMBDA = 0.94  # SPDR-012 config.EWMA_LAMBDA
RV_WINDOW = 20  # SPDR-012 config.RV_WINDOW
LEVEL_MEDIAN_WINDOW = 60  # SPDR-015 H1 CLOCKS["H1"]["warmup_bars"]
ATR_PERIOD_BREAKOUT = 20  # design section 8: ATR(20)
ATR_PERIOD_SWING = 14  # SPDR-013 config.ATR_PERIOD
ZZ_REVERSAL_ATR = 2.0  # SPDR-013 config.ZZ_REVERSAL_ATR
SWING_MIN_TRAIN = 20  # SPDR-013 zz_forecast.MIN_TRAIN
RIDGE_ALPHA = 1.0  # SPDR-013 zz_forecast.RIDGE_ALPHA
LOGIT_RIDGE_ALPHA = 1.0  # SPDR-015 config.LOGIT_RIDGE_ALPHA
INITIAL_FIT_FRACTION = 0.40  # SPDR-015 config.INITIAL_FIT_FRACTION
SHOCK_LIFE_BARS = 2  # design section 4: shock active for two bars
TAIL_UNCONDITIONAL_RATE = 0.10  # design section 4: high above the unconditional 0.10 rate
LEVEL_FORECAST_HORIZONS = (4, 12)
STATE_HIGH, STATE_LOW, STATE_UNKNOWN = "HIGH", "LOW", "UNKNOWN"

FORMULA_SOURCES: dict[str, str] = {
    "RANGE_SCALE": "SPDR-015 features._parkinson_ewma(lambda=0.94) x universe conversion",
    "SWING_SCALE": "SPDR-013 indicators.atr_zigzag(2.0xATR14) + zz_forecast ridge walk-forward",
    "LEVEL_NOW": "SPDR-015 features.add_state_models R-MARKOV rolling-median rv20 split",
    "LEVEL_FORECAST_K4": "SPDR-015 transitions.walk_forward_probs logistic_ridge k=4",
    "LEVEL_FORECAST_K12": "SPDR-015 transitions.walk_forward_probs logistic_ridge k=12",
    "SHOCK": "SPDR-015 features expanding-p90 |r| shock flag, two-bar life",
    "SWING_GT_CUR": "SPDR-018 D8 logit_ridge T-GT-CUR on SPDR-013 swing features",
    "TAIL_RISK": "SPDR-012 V-TAIL expanding P(next |move| > own expanding P90) by level state",
    "ATR20": "SPDR-013 indicators.wilder_atr(period=20) on H1 completed bars",
}

_SWING_FEATURES = ("magnitude_bps", "direction", "angle_bps_per_bar", "path_noise_atr", "bars")


@dataclass(frozen=True)
class Calibration:
    """Frozen reference values; every entry is estimated on TRAIN bars <= ``end_ts``."""

    end_ts: datetime
    start_ts: datetime
    train_start_ts: datetime
    train_end_ts: datetime
    row_count_by_symbol: dict[str, int]
    range_conversion: dict[str, float]
    median_range_scale_bps: dict[str, float]
    median_swing_scale_bps: dict[str, float]
    p90_move_bps: dict[str, float]
    formula_sources: tuple[tuple[str, str], ...] = tuple(sorted(FORMULA_SOURCES.items()))


# --------------------------------------------------------------------------- #
# Small causal primitives (ported)
# --------------------------------------------------------------------------- #


def _rolling_mean(x: np.ndarray, w: int) -> np.ndarray:
    return pl.Series(x).rolling_mean(window_size=w, min_samples=w).to_numpy()


def _rolling_median(x: np.ndarray, w: int) -> np.ndarray:
    return pl.Series(x).rolling_median(window_size=w, min_samples=w).to_numpy()


def _expanding_pct(x: np.ndarray) -> np.ndarray:
    """SPDR-015 expanding percentile rank, including the current completed observation."""
    out = np.full(x.size, np.nan)
    for i in range(x.size):
        if not np.isfinite(x[i]):
            continue
        history = x[: i + 1]
        history = history[np.isfinite(history)]
        out[i] = float(np.mean(history <= x[i]))
    return out


def _parkinson_ewma(high: np.ndarray, low: np.ndarray, lam: float = EWMA_LAMBDA) -> np.ndarray:
    """Causal Parkinson EWMA volatility level (SPDR-015 features._parkinson_ewma)."""
    with np.errstate(divide="ignore", invalid="ignore"):
        ln_hl = np.log(high / low)
    park_var = (ln_hl**2) / (4.0 * np.log(2.0))
    park_var = np.where(np.isfinite(park_var) & (high > 0) & (low > 0), park_var, np.nan)
    out = np.full(high.size, np.nan)
    var = np.nan
    for i in range(high.size):
        v = park_var[i]
        if not np.isfinite(v):
            out[i] = np.sqrt(var) if np.isfinite(var) else np.nan
            continue
        var = v if not np.isfinite(var) else lam * var + (1.0 - lam) * v
        out[i] = np.sqrt(var)
    return out


def wilder_atr(
    high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int
) -> np.ndarray:
    """Wilder ATR on completed bars (SPDR-013 indicators.wilder_atr). ``atr[i]`` uses bars <= i."""
    n = close.size
    atr = np.full(n, np.nan)
    if n <= period:
        return atr
    prev_close = np.empty(n)
    prev_close[0] = np.nan
    prev_close[1:] = close[:-1]
    tr = np.maximum(high - low, np.maximum(np.abs(high - prev_close), np.abs(low - prev_close)))
    tr[0] = high[0] - low[0]
    atr[period] = float(np.mean(tr[1 : period + 1]))
    for i in range(period + 1, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    return atr


def _expanding_p90(x: np.ndarray, min_history: int = 20) -> np.ndarray:
    """Expanding 90th percentile using strictly prior finite history (SPDR-015)."""
    out = np.full(x.size, np.nan)
    finite = np.isfinite(x)
    for i in range(1, x.size):
        hist = x[:i][finite[:i]]
        if hist.size < min_history:
            continue
        out[i] = float(np.percentile(hist, 90))
    return out


def shock_two_bar_life(flags: np.ndarray) -> np.ndarray:
    """A shock at bar ``i`` keeps the state active for ``SHOCK_LIFE_BARS`` bars including ``i``."""
    active = np.zeros(flags.size, dtype=np.int64)
    for lag in range(SHOCK_LIFE_BARS):
        shifted = np.zeros(flags.size, dtype=np.int64)
        if lag == 0:
            shifted = (flags == 1).astype(np.int64)
        else:
            shifted[lag:] = (flags[:-lag] == 1).astype(np.int64)
        active = np.maximum(active, shifted)
    return active


def tail_risk_state(probability: float) -> str:
    """HIGH above the unconditional 0.10 exceedance rate; UNKNOWN while undefined."""
    if not np.isfinite(probability):
        return STATE_UNKNOWN
    return STATE_HIGH if probability > TAIL_UNCONDITIONAL_RATE else STATE_LOW


def _states_to_labels(state: np.ndarray) -> list[str]:
    return [STATE_HIGH if s == 1 else STATE_LOW if s == 0 else STATE_UNKNOWN for s in state]


# --------------------------------------------------------------------------- #
# Expanding models
# --------------------------------------------------------------------------- #


def _logistic_ridge_fit(
    X: np.ndarray, y: np.ndarray, min_samples: int = 30
) -> np.ndarray | None:
    """IRLS logistic ridge (SPDR-015 transitions._logistic_ridge_fit)."""
    m = np.isfinite(X).all(axis=1) & (y >= 0)
    if m.sum() < min_samples:
        return None
    Xv, yv = X[m], y[m].astype(float)
    mu, sd = Xv.mean(axis=0), Xv.std(axis=0)
    sd[sd == 0] = 1.0
    Z = np.hstack([np.ones((Xv.shape[0], 1)), (Xv - mu) / sd])
    w = np.zeros(Z.shape[1])
    for _ in range(40):
        p = 1.0 / (1.0 + np.exp(-np.clip(Z @ w, -30, 30)))
        W = np.maximum(p * (1.0 - p), 1e-6)
        z = Z @ w + (yv - p) / W
        A = Z.T @ (Z * W[:, None])
        A[1:, 1:] += LOGIT_RIDGE_ALPHA * np.eye(A.shape[0] - 1)
        try:
            w_new = np.linalg.solve(A, Z.T @ (W * z))
        except np.linalg.LinAlgError:
            return None
        if np.max(np.abs(w_new - w)) < 1e-6:
            return np.concatenate([w_new, mu, sd])
        w = w_new
    return np.concatenate([w, mu, sd])


def _logistic_predict(pack: np.ndarray, X: np.ndarray) -> np.ndarray:
    p = X.shape[1]
    w, mu, sd = pack[: p + 1], pack[p + 1 : 2 * p + 1], pack[2 * p + 1 :]
    Z = np.hstack([np.ones((X.shape[0], 1)), (X - mu) / sd])
    return 1.0 / (1.0 + np.exp(-np.clip(Z @ w, -30, 30)))


def _ordinal_logit_predict(X: np.ndarray, y: np.ndarray, x: np.ndarray) -> float:
    """Frozen SPDR-015 T-GT-CUR logit-ridge sample, class and fallback behavior."""
    valid = np.isfinite(X).all(axis=1) & np.isfinite(y)
    yv = y[valid]
    if valid.sum() < 20 or yv.sum() < 3 or (1.0 - yv).sum() < 3:
        return float(np.nanmean(y))
    pack = _logistic_ridge_fit(X[valid], yv.astype(np.int64), min_samples=20)
    if pack is None:
        return float(np.nanmean(y))
    return float(_logistic_predict(pack, x[None, :])[0])


def _month_keys(ts_ns: np.ndarray) -> np.ndarray:
    dt = (ts_ns // 1_000_000).astype("datetime64[ms]")
    return dt.astype("datetime64[M]").astype(np.int64)


def _walk_forward_state_probability(
    X: np.ndarray, state: np.ndarray, ts_ns: np.ndarray, k: int
) -> np.ndarray:
    """Monthly-refit expanding logistic-ridge P(state_{t+k} = HIGH); NaN before the first fit."""
    n = state.size
    y = np.full(n, -1, dtype=np.int64)
    if k < n:
        y[: n - k] = state[k:]
    p_out = np.full(n, np.nan)
    usable = np.where(np.isfinite(X).all(axis=1) & (state >= 0) & (y >= 0))[0]
    if usable.size < 40:
        return p_out
    fit_end = usable[max(30, int(INITIAL_FIT_FRACTION * usable.size)) - 1]
    oos = usable[usable > fit_end]
    if oos.size == 0:
        return p_out
    months = _month_keys(ts_ns)
    points = [int(oos[0])]
    for i in range(1, oos.size):
        if months[oos[i]] != months[oos[i - 1]]:
            points.append(int(oos[i]))
    points.append(int(oos[-1]) + 1)
    for a, b in zip(points[:-1], points[1:], strict=True):
        # Training rows must be complete at the decision time: their own target needs k more bars.
        train = usable[usable + k < a]
        if train.size < 30:
            continue
        pack = _logistic_ridge_fit(X[train], y[train])
        if pack is None:
            continue
        predict_at = np.where(np.isfinite(X).all(axis=1) & (state >= 0))[0]
        predict_at = predict_at[(predict_at >= a) & (predict_at < b)]
        if predict_at.size:
            p_out[predict_at] = _logistic_predict(pack, X[predict_at])
    return p_out


@dataclass(frozen=True)
class _Swing:
    start_idx: int
    end_idx: int
    confirm_idx: int
    magnitude_bps: float
    direction: int
    angle_bps_per_bar: float
    path_noise_atr: float
    bars: int


def _atr_zigzag(close: np.ndarray, atr: np.ndarray, start: int) -> list[_Swing]:
    """Deterministic causal ATR-ZigZag (SPDR-013 indicators.atr_zigzag)."""
    n = close.size
    swings: list[_Swing] = []
    if n - start < 3:
        return swings
    direction, ext_idx, ext_price, last_pivot = 1, start, float(close[start]), start
    for i in range(start + 1, n):
        thr = ZZ_REVERSAL_ATR * atr[i]
        if not np.isfinite(thr) or thr <= 0:
            continue
        if direction == 1:
            if close[i] >= ext_price:
                ext_price, ext_idx = float(close[i]), i
            elif ext_price - close[i] >= thr:
                if ext_idx > last_pivot:
                    swings.append(_swing_features(last_pivot, ext_idx, i, close, atr))
                    last_pivot = ext_idx
                direction, ext_price, ext_idx = -1, float(close[i]), i
        else:
            if close[i] <= ext_price:
                ext_price, ext_idx = float(close[i]), i
            elif close[i] - ext_price >= thr:
                if ext_idx > last_pivot:
                    swings.append(_swing_features(last_pivot, ext_idx, i, close, atr))
                    last_pivot = ext_idx
                direction, ext_price, ext_idx = 1, float(close[i]), i
    return swings


def _swing_features(
    start_idx: int, end_idx: int, confirm_idx: int, close: np.ndarray, atr: np.ndarray
) -> _Swing:
    start_price, end_price = float(close[start_idx]), float(close[end_idx])
    magnitude_bps = abs(end_price - start_price) / start_price * 1e4
    bars = max(1, end_idx - start_idx)
    seg = np.arange(start_idx, end_idx + 1)
    bridge = start_price + (end_price - start_price) * (seg - start_idx) / max(
        1, end_idx - start_idx
    )
    dev = np.abs(close[start_idx : end_idx + 1] - bridge)
    atr_seg = atr[start_idx : end_idx + 1]
    atr_scale = float(np.nanmean(atr_seg)) if np.isfinite(atr_seg).any() else np.nan
    noise = float(np.mean(dev) / atr_scale) if np.isfinite(atr_scale) and atr_scale > 0 else np.nan
    return _Swing(
        start_idx=start_idx,
        end_idx=end_idx,
        confirm_idx=confirm_idx,
        magnitude_bps=magnitude_bps,
        direction=1 if end_price >= start_price else -1,
        angle_bps_per_bar=magnitude_bps / bars,
        path_noise_atr=noise,
        bars=bars,
    )


def _ridge_fit_predict(X_tr: np.ndarray, y_tr: np.ndarray, x_te: np.ndarray) -> float:
    """Ridge (alpha=1.0) fit/predict (SPDR-013 zz_forecast._ridge_fit_predict)."""
    mu, sd = X_tr.mean(axis=0), X_tr.std(axis=0)
    sd[sd == 0] = 1.0
    Xs = (X_tr - mu) / sd
    ym = y_tr.mean()
    w = np.linalg.solve(
        Xs.T @ Xs + RIDGE_ALPHA * np.eye(Xs.shape[1]), Xs.T @ (y_tr - ym)
    )
    return float(((x_te - mu) / sd) @ w + ym)


def _swing_forecasts(swings: list[_Swing], n_bars: int) -> tuple[np.ndarray, np.ndarray]:
    """Per-bar next-swing magnitude forecast and T-GT-CUR state, carried from confirmations.

    Both models are expanding walk-forward over confirmed swings: swing ``k``'s prediction uses
    swings ``< k`` only, and the value becomes readable at ``confirm_idx`` of swing ``k``.
    """
    scale = np.full(n_bars, np.nan)
    gt_cur = np.full(n_bars, -1, dtype=np.int64)
    if len(swings) < SWING_MIN_TRAIN + 2:
        return scale, gt_cur
    X = np.array([[getattr(s, f) for f in _SWING_FEATURES] for s in swings], float)
    mag = np.array([s.magnitude_bps for s in swings], float)
    # target of swing k: next swing's magnitude; only complete once swing k+1 confirms.
    y_next = np.full(len(swings), np.nan)
    y_next[:-1] = mag[1:]
    y_gt = np.where(np.isfinite(y_next), (y_next > mag).astype(float), -1.0)

    for k in range(SWING_MIN_TRAIN, len(swings)):
        # At confirmation of swing k, the (k-1)->k pair is complete and is admissible.
        train = np.arange(0, k)
        rows = train[np.isfinite(X[train]).all(axis=1) & np.isfinite(y_next[train])]
        if rows.size < SWING_MIN_TRAIN or not np.isfinite(X[k]).all():
            continue
        forecast = _ridge_fit_predict(X[rows], y_next[rows], X[k])
        confirm = swings[k].confirm_idx
        end = swings[k + 1].confirm_idx if k + 1 < len(swings) else n_bars
        scale[confirm:end] = max(forecast, 0.0)
        probability = _ordinal_logit_predict(X[rows], y_gt[rows], X[k])
        if np.isfinite(probability):
            gt_cur[confirm:end] = int(probability >= 0.50)
    return scale, gt_cur


def _tail_risk_probability(
    exceed: np.ndarray, level_state: np.ndarray, valid: np.ndarray
) -> np.ndarray:
    """Expanding P(next move exceeds own P90 | current level state), completed rows only."""
    n = exceed.size
    out = np.full(n, TAIL_UNCONDITIONAL_RATE)
    counts = {0: [0, 0], 1: [0, 0]}
    for i in range(n):
        state = int(level_state[i])
        if state in counts and counts[state][1] > 0:
            out[i] = counts[state][0] / counts[state][1]
        if valid[i] and state in counts:
            counts[state][1] += 1
            counts[state][0] += int(exceed[i] == 1)
    return out


# --------------------------------------------------------------------------- #
# Panel assembly
# --------------------------------------------------------------------------- #


def _symbol_panel(bars: pl.DataFrame, p90_move_bps: float | None = None) -> pl.DataFrame:
    """All causal columns for one symbol's H1 completed bars, sorted by ``ts``."""
    b = bars.sort("ts")
    o = b["open"].to_numpy()
    h = b["high"].to_numpy()
    lo = b["low"].to_numpy()
    c = b["close"].to_numpy()
    ts_ns = b["ts"].cast(pl.Datetime("ns")).to_numpy().astype("int64")
    n = c.size

    r = np.full(n, np.nan)
    r[1:] = np.log(c[1:] / c[:-1])
    abs_r = np.abs(r)
    rv20 = np.sqrt(_rolling_mean(r * r, RV_WINDOW))
    park_ewma = _parkinson_ewma(h, lo)
    atr20 = wilder_atr(h, lo, c, ATR_PERIOD_BREAKOUT)
    atr14 = wilder_atr(h, lo, c, ATR_PERIOD_SWING)

    level_median = _rolling_median(rv20, LEVEL_MEDIAN_WINDOW)
    lvl_pct = _expanding_pct(rv20)
    level_state = np.where(
        np.isfinite(level_median) & np.isfinite(rv20), (rv20 >= level_median).astype(np.int64), -1
    )
    shock_p90 = _expanding_p90(abs_r)
    shock_flag = np.where(
        np.isfinite(shock_p90) & np.isfinite(abs_r), (abs_r >= shock_p90).astype(np.int64), -1
    )
    shock_state = np.where(shock_flag < 0, -1, shock_two_bar_life(shock_flag))

    duration = np.zeros(n, dtype=np.int64)
    for i in range(n):
        if level_state[i] < 0:
            continue
        duration[i] = (
            1 if i == 0 or level_state[i] != level_state[i - 1] else min(64, duration[i - 1] + 1)
        )
    n_high_4 = pl.Series((level_state == 1).astype(float)).rolling_sum(4, min_samples=1).to_numpy()
    n_high_12 = (
        pl.Series((level_state == 1).astype(float)).rolling_sum(12, min_samples=1).to_numpy()
    )
    X_state = np.column_stack(
        [
            level_state.astype(float),
            duration.astype(float),
            rv20,
            park_ewma,
            lvl_pct,
            n_high_4,
            n_high_12,
            np.where(shock_state < 0, 0.0, shock_state.astype(float)),
        ]
    )
    X_state[level_state < 0] = np.nan
    forecast = {
        k: _walk_forward_state_probability(X_state, level_state, ts_ns, k)
        for k in LEVEL_FORECAST_HORIZONS
    }

    swing_start = int(np.argmax(np.isfinite(atr14))) if np.isfinite(atr14).any() else 0
    swing_scale, swing_gt = _swing_forecasts(_atr_zigzag(c, atr14, swing_start), n)

    abs_oo = np.full(n, np.nan)
    abs_oo[:-1] = 1e4 * np.abs(o[1:] / o[:-1] - 1.0)
    own_p90 = (
        np.full(n, p90_move_bps)
        if p90_move_bps is not None and np.isfinite(p90_move_bps)
        else _expanding_p90(abs_oo)
    )
    exceed = np.where(
        np.isfinite(own_p90) & np.isfinite(abs_oo), (abs_oo > own_p90).astype(np.int64), -1
    )
    tail_probability = _tail_risk_probability(exceed, level_state, exceed >= 0)

    return pl.DataFrame(
        {
            "symbol": b["symbol"],
            "ts": b["ts"],
            "open": o,
            "high": h,
            "low": lo,
            "close": c,
            "atr20": atr20,
            "rv20": rv20,
            "lvl_pct": lvl_pct,
            "park_ewma": park_ewma,
            "abs_oo_bps": abs_oo,
            "park_scale_bps": park_ewma * 1e4,
            "swing_scale_bps": swing_scale,
            "level_now": _states_to_labels(level_state),
            "level_forecast_k4": [
                STATE_UNKNOWN if not np.isfinite(p) else (STATE_HIGH if p >= 0.50 else STATE_LOW)
                for p in forecast[4]
            ],
            "level_forecast_k12": [
                STATE_UNKNOWN if not np.isfinite(p) else (STATE_HIGH if p >= 0.50 else STATE_LOW)
                for p in forecast[12]
            ],
            "level_forecast_p_k4": forecast[4],
            "level_forecast_p_k12": forecast[12],
            "shock": _states_to_labels(shock_state),
            "swing_gt_cur": _states_to_labels(swing_gt),
            "tail_risk_p": tail_probability,
            "tail_risk": [tail_risk_state(p) for p in tail_probability],
        }
    )


def fit_calibration(
    bars: pl.DataFrame,
    train_start: datetime,
    train_end: datetime,
) -> Calibration:
    """Freeze references on the first chronological 20% of explicit TRAIN after warm-up."""
    ordered = bars.sort(["symbol", "ts"])
    if ordered.is_empty() or ordered["ts"].min() > train_start or ordered["ts"].max() < train_end:
        raise ValueError("bars do not cover the explicit TRAIN bounds")
    train = ordered.filter(pl.col("ts").is_between(train_start, train_end, closed="both"))
    if train.is_empty():
        raise ValueError("TRAIN bounds contain no bars")
    conversion: dict[str, float] = {}
    median_range: dict[str, float] = {}
    median_swing: dict[str, float] = {}
    p90_move: dict[str, float] = {}
    row_counts: dict[str, int] = {}
    starts: list[datetime] = []
    ends: list[datetime] = []
    for symbol, group in train.group_by("symbol", maintain_order=True):
        name = symbol[0] if isinstance(symbol, tuple) else symbol
        after_warmup = group.slice(LEVEL_MEDIAN_WINDOW)
        take = int(np.floor(after_warmup.height * 0.20))
        if take < 1:
            raise ValueError(f"TRAIN calibration window empty after warm-up for {name}")
        window = after_warmup.head(take)
        row_counts[name] = take
        starts.append(window["ts"][0])
        # The last predictor's next-open target completes at the following open. Declare that
        # completion timestamp as the freeze boundary so no outcome crosses the stated band.
        ends.append(group["ts"][LEVEL_MEDIAN_WINDOW + take])
        panel = _symbol_panel(group).slice(LEVEL_MEDIAN_WINDOW, take)
        park = panel["park_scale_bps"].to_numpy()
        move = panel["abs_oo_bps"].to_numpy()
        swing = panel["swing_scale_bps"].to_numpy()
        park_median = float(np.nanmedian(park)) if np.isfinite(park).any() else np.nan
        move_median = float(np.nanmedian(move)) if np.isfinite(move).any() else np.nan
        factor = (
            move_median / park_median
            if np.isfinite(park_median) and park_median > 0 and np.isfinite(move_median)
            else 1.0
        )
        conversion[name] = factor
        median_range[name] = park_median * factor if np.isfinite(park_median) else np.nan
        median_swing[name] = float(np.nanmedian(swing)) if np.isfinite(swing).any() else np.nan
        p90_move[name] = (
            float(np.nanpercentile(move, 90)) if np.isfinite(move).any() else np.nan
        )
    return Calibration(
        end_ts=max(ends),
        start_ts=min(starts),
        train_start_ts=train_start,
        train_end_ts=train_end,
        row_count_by_symbol=row_counts,
        range_conversion=conversion,
        median_range_scale_bps=median_range,
        median_swing_scale_bps=median_swing,
        p90_move_bps=p90_move,
    )


def build_feature_panel(
    bars: pl.DataFrame,
    calibration: Calibration,
    *,
    availability_shift_bars: int = 0,
) -> pl.DataFrame:
    """One row per H1 decision bar; every value uses completed bars at or before that bar.

    Reads: ``open/high/low/close`` of bars ``<= t``. Writes no column that depends on bar
    ``t + 1`` or later. ``abs_oo_bps`` is a disclosure column measured over bar ``t`` and must
    never be used as a decision input.

    ``availability_shift_bars`` is the leak tripwire and nothing else: at ``1`` every component
    becomes readable one signal-domain bar EARLIER than it could have been, so each arm
    conditions on information it could not have had. The default ``0`` is the causal panel and
    is byte-identical to the panel this function produced before the parameter existed.
    """
    lag = 1 - int(availability_shift_bars)
    frames = []
    for symbol, group in bars.group_by("symbol", maintain_order=True):
        name = symbol[0] if isinstance(symbol, tuple) else symbol
        panel = _symbol_panel(group, calibration.p90_move_bps.get(name))
        factor = calibration.range_conversion.get(name, 1.0)
        frames.append(
            panel.with_columns(
                (pl.col("park_scale_bps") * factor).alias("range_scale_bps"),
                pl.lit(FORMULA_SOURCES["RANGE_SCALE"]).alias("range_scale_source"),
            ).with_columns(
                pl.col(column).shift(lag).alias(column)
                for column in (
                    "atr20",
                    "rv20",
                    "lvl_pct",
                    "park_ewma",
                    "park_scale_bps",
                    "range_scale_bps",
                    "swing_scale_bps",
                    "level_now",
                    "level_forecast_k4",
                    "level_forecast_k12",
                    "level_forecast_p_k4",
                    "level_forecast_p_k12",
                    "shock",
                    "swing_gt_cur",
                    "tail_risk_p",
                    "tail_risk",
                )
            ).with_columns(
                pl.col(column).fill_null(STATE_UNKNOWN).alias(column)
                for column in (
                    "level_now",
                    "level_forecast_k4",
                    "level_forecast_k12",
                    "shock",
                    "swing_gt_cur",
                    "tail_risk",
                )
            )
        )
    return pl.concat(frames).sort(["symbol", "ts"])
