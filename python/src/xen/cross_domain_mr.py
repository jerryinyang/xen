"""Cross-domain mean-reversion anchor + MR-screen constructors (CF-MR-003 / EXP-008).

Builds, for a (higher-domain anchor, lower-domain exec) pair, five independent **anchor-series**
constructions and the three-leg **MR screen** that selects entry timing. Every output an experiment
uses for a decision is causal by construction: an anchor value mapped onto exec bar ``j`` is the last
higher-domain bar whose ``CloseTime <= exec CloseTime[j]``, and the deviation/scale/screen series are
read at the **prior** exec close (the caller acts at bar ``i``'s open using index ``i-1``). This module
never reads a forming bar's own OHLC for a decision.

Provenance contract (which timestamps each output reads)
--------------------------------------------------------
- ``anchor_series(...)`` returns exec-aligned ``dev[j]`` and ``z[j]`` that are **fully determined by
  data with CloseTime <= exec CloseTime[j]** (rolling windows end at ``j``; the mapped anchor bar
  closed at or before exec close ``j``). They are decision inputs only after the caller lags them by
  one bar (use ``[i-1]`` to act at bar ``i``'s open). No output reads ``exec[j]``'s successors.
- ``mr_screen_pass(window)`` reads only the values inside ``window`` (the caller passes the trailing
  ``W_s`` deviations ending at ``i-1``). It never sees future deviations.
- This module computes **no outcome/excursion column** — the forward favourable excursion is built in
  the experiment orchestration (``run_experiment.py``) from real prices, strictly forward of the exec
  open, and is the only place future bars are read (as an outcome, never as a decision input).

Real-price discipline is the caller's responsibility: anchors/deviations here are analysis features;
the favourable-excursion outcome is measured on real time-bar OHLC by the caller.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# --------------------------------------------------------------------------- #
# Frozen design constants (EXP-008 design §4; never tuned mid-experiment)
# --------------------------------------------------------------------------- #
W_A: int = 20                  # anchor-domain window (anchor bars)
W_Z: int = 200                 # robust-z / scale window (exec bars)
W_S: int = 200                 # MR-screen window (exec bars)
Z_STAR: float = 2.0            # extreme-probe threshold on |z| (frozen probe; sensitivity in §8)
MAD_SCALE: float = 1.4826      # MAD -> std consistency factor (normal)

VR_Q: int = 4                  # variance-ratio aggregation
VR_DELTA: float = 0.10         # VR leg passes iff VR < 1 - VR_DELTA
HL_MAX: float = 48.0           # half-life leg passes iff finite and 0 < HL <= HL_MAX (exec bars)
HURST_DELTA: float = 0.05      # Hurst leg passes iff H < 0.5 - HURST_DELTA

SERIES: tuple[str, ...] = ("S1_CENTER", "S2_RANGE", "S3_DETREND", "S4_OU", "S5_SPREAD")

# Domain-pair axis (anchor_minutes, exec_minutes), design §3.
DOMAIN_PAIRS: dict[str, tuple[int, int]] = {
    "4h/1h": (240, 60),
    "4h/15m": (240, 15),
    "1D/1h": (1440, 60),
}

# S5 predeclared asset classes (design §4). Lone members -> UNPOWERED for S5.
S5_CLASSES: dict[str, tuple[str, ...]] = {
    "FX_MAJORS": ("EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD"),
    "JPY_CROSSES": ("EURJPY", "GBPJPY", "AUDJPY"),
    "INDICES": ("USTEC", "US500", "US2000", "JP225"),
}


@dataclass(frozen=True)
class AnchorSeries:
    """Exec-aligned deviation + standardized extreme series for one anchor construction.

    All arrays length ``n_exec``; ``dev[j]``/``z[j]`` known at exec close ``j`` (lag by 1 to decide).
    """

    dev: np.ndarray            # deviation to fade (sign(dev) -> fade direction); NaN in warmup
    z: np.ndarray              # standardized extreme measure (|z| >= Z_STAR is the probe)
    powered_frac: float        # fraction of exec bars with a finite (dev, z) (fit health)


# --------------------------------------------------------------------------- #
# Pure helpers — causal mapping + rolling primitives (all trailing, end-inclusive)
# --------------------------------------------------------------------------- #
def map_prev(anchor_ct: np.ndarray, values: np.ndarray, exec_ct: np.ndarray) -> np.ndarray:
    """Map an anchor-domain series onto exec bars by ``last anchor CloseTime <= exec CloseTime``.

    Parameters
    ----------
    anchor_ct, exec_ct : np.ndarray
        Anchor / exec ``CloseTime`` as int64 (ns) or float, both ascending.
    values : np.ndarray
        Anchor-domain values aligned to ``anchor_ct``.

    Returns
    -------
    np.ndarray
        Exec-aligned values (``NaN`` where no anchor bar has closed yet). Causal: uses only the
        most recent **completed** anchor bar at or before each exec close.
    """
    pos = np.searchsorted(anchor_ct, exec_ct, side="right") - 1     # last anchor idx with ct <= exec ct
    out = np.full(exec_ct.shape[0], np.nan, dtype=np.float64)
    ok = pos >= 0
    out[ok] = np.asarray(values, dtype=np.float64)[pos[ok]]
    return out


def _trailing_windows(x: np.ndarray, w: int) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(ends, mat)`` where ``mat[k]`` is the trailing ``w`` values ending at ``ends[k]``.

    Only full windows are returned. ``ends`` are absolute indices into ``x``.
    """
    from numpy.lib.stride_tricks import sliding_window_view

    n = x.shape[0]
    if n < w:
        return np.empty(0, dtype=np.int64), np.empty((0, w), dtype=np.float64)
    mat = sliding_window_view(x, w)                                 # row k spans x[k:k+w]
    ends = np.arange(w - 1, n)
    return ends, mat


def rolling_median_mad_z(dev: np.ndarray, w: int) -> np.ndarray:
    """Robust-z of ``dev`` against its own trailing ``w``-window: ``(dev - med)/(1.4826*MAD)``.

    Center + scale use the window **ending at the same bar** (all <= that bar's close). Bars without
    a full window, or with zero MAD, yield ``NaN``.
    """
    ends, mat = _trailing_windows(dev, w)
    z = np.full(dev.shape[0], np.nan, dtype=np.float64)
    if ends.shape[0] == 0:
        return z
    med = np.median(mat, axis=1)
    mad = np.median(np.abs(mat - med[:, None]), axis=1) * MAD_SCALE
    cur = dev[ends]
    good = np.isfinite(cur) & (mad > 0)
    z[ends[good]] = (cur[good] - med[good]) / mad[good]
    return z


def rolling_std_z(dev: np.ndarray, w: int) -> np.ndarray:
    """Standardize ``dev`` by its trailing ``w``-window std (mean ~0 residual/spread series)."""
    ends, mat = _trailing_windows(dev, w)
    z = np.full(dev.shape[0], np.nan, dtype=np.float64)
    if ends.shape[0] == 0:
        return z
    sd = np.std(mat, axis=1, ddof=1)
    cur = dev[ends]
    good = np.isfinite(cur) & (sd > 0)
    z[ends[good]] = cur[good] / sd[good]
    return z


# --------------------------------------------------------------------------- #
# Pure helpers — anchor-domain rolling constructors (return per-anchor-bar arrays)
# --------------------------------------------------------------------------- #
def rolling_median(close: np.ndarray, w: int) -> np.ndarray:
    """Trailing rolling median of ``close`` over ``w`` bars (NaN in warmup)."""
    ends, mat = _trailing_windows(close, w)
    out = np.full(close.shape[0], np.nan, dtype=np.float64)
    if ends.shape[0]:
        out[ends] = np.median(mat, axis=1)
    return out


def rolling_donchian_mid(high: np.ndarray, low: np.ndarray, w: int) -> np.ndarray:
    """Trailing Donchian midline ``(max High + min Low)/2`` over ``w`` bars."""
    eh, mh = _trailing_windows(high, w)
    el, ml = _trailing_windows(low, w)
    out = np.full(high.shape[0], np.nan, dtype=np.float64)
    if eh.shape[0]:
        out[eh] = (mh.max(axis=1) + ml.min(axis=1)) / 2.0
    return out


def rolling_ols_fit(logp: np.ndarray, w: int) -> tuple[np.ndarray, np.ndarray]:
    """Rolling OLS ``log(price) ~ time`` over ``w`` bars: fitted value at the window end + resid std.

    Returns ``(fit_end, resid_std)`` per bar. ``time`` is the local index ``0..w-1``; the fitted value
    at the last window position is ``a + b*(w-1)``. Warmup / degenerate -> ``NaN``.
    """
    ends, mat = _trailing_windows(logp, w)
    fit = np.full(logp.shape[0], np.nan, dtype=np.float64)
    rstd = np.full(logp.shape[0], np.nan, dtype=np.float64)
    if ends.shape[0] == 0:
        return fit, rstd
    t = np.arange(w, dtype=np.float64)
    t_mean = t.mean()
    t_c = t - t_mean
    denom = float(np.dot(t_c, t_c))                                 # sum (t-mean)^2, constant
    if denom <= 0:
        return fit, rstd
    y_mean = mat.mean(axis=1)
    b = (mat * t_c[None, :]).sum(axis=1) / denom                    # slope per window
    a = y_mean - b * t_mean
    fit_end = a + b * (w - 1)
    resid = mat - (a[:, None] + b[:, None] * t[None, :])
    rs = np.sqrt((resid ** 2).sum(axis=1) / (w - 2))               # OLS residual std (2 params)
    fit[ends] = fit_end
    rstd[ends] = rs
    return fit, rstd


def rolling_ou_fit(x: np.ndarray, w: int) -> tuple[np.ndarray, np.ndarray]:
    """Rolling AR(1) OU fit on ``x`` over ``w`` bars: equilibrium ``theta`` and ``sigma_eq``.

    Fits ``x_t = alpha + phi x_{t-1}`` on the trailing window; mean-reverting iff ``0 < phi < 1``.
    ``theta = alpha/(1-phi)``, ``sigma_eq = sigma_eps / sqrt(1-phi^2)``. Non-stationary / explosive
    (``phi`` outside ``(0,1)``) or degenerate windows -> ``NaN`` (UNPOWERED contribution).
    """
    n = x.shape[0]
    theta = np.full(n, np.nan, dtype=np.float64)
    sigma_eq = np.full(n, np.nan, dtype=np.float64)
    if n < w + 1:
        return theta, sigma_eq
    from numpy.lib.stride_tricks import sliding_window_view

    # AR(1) regresses x_t on x_{t-1}; a window ending at bar e uses pairs (x[e-w+1..e], lag).
    lag = sliding_window_view(x[:-1], w)                            # predictor rows
    cur = sliding_window_view(x[1:], w)                             # response rows
    ends = np.arange(w, n)                                          # response end index in x
    xm = lag.mean(axis=1)
    ym = cur.mean(axis=1)
    xc = lag - xm[:, None]
    yc = cur - ym[:, None]
    sxx = (xc ** 2).sum(axis=1)
    phi = np.divide((xc * yc).sum(axis=1), sxx, out=np.full(xm.shape, np.nan), where=sxx > 0)
    alpha = ym - phi * xm
    mr = np.isfinite(phi) & (phi > 0.0) & (phi < 1.0)
    resid = cur - (alpha[:, None] + phi[:, None] * lag)
    sig_eps = np.sqrt((resid ** 2).sum(axis=1) / (w - 2))
    th = np.divide(alpha, 1.0 - phi, out=np.full(alpha.shape, np.nan), where=mr)
    den = np.sqrt(np.where(mr, 1.0 - phi ** 2, np.nan))            # guarded (mr => |phi|<1)
    se = np.divide(sig_eps, den, out=np.full(alpha.shape, np.nan), where=mr & (den > 0))
    theta[ends[mr]] = th[mr]
    sigma_eq[ends[mr]] = se[mr]
    return theta, sigma_eq


def rolling_beta_fit(logp_i: np.ndarray, basket: np.ndarray, w: int) -> np.ndarray:
    """Rolling OLS ``log price_i ~ beta*basket + alpha`` over ``w`` bars: fitted anchor at window end.

    Returns the fitted value ``beta*basket + alpha`` evaluated at the **current** basket/logp (window
    end). Warmup / degenerate basket variance -> ``NaN``.
    """
    n = logp_i.shape[0]
    fit = np.full(n, np.nan, dtype=np.float64)
    ey, my = _trailing_windows(logp_i, w)
    ex, mx = _trailing_windows(basket, w)
    if ey.shape[0] == 0:
        return fit
    xm = mx.mean(axis=1)
    ym = my.mean(axis=1)
    xc = mx - xm[:, None]
    yc = my - ym[:, None]
    sxx = (xc ** 2).sum(axis=1)
    finite = np.isfinite(sxx) & (sxx > 0) & np.all(np.isfinite(mx), axis=1) & np.all(
        np.isfinite(my), axis=1)
    beta = np.full(xm.shape, np.nan)
    beta[finite] = (xc[finite] * yc[finite]).sum(axis=1) / sxx[finite]
    alpha = ym - beta * xm
    cur_x = basket[ey]
    fit[ey] = beta * cur_x + alpha                                  # fitted at current basket
    return fit


# --------------------------------------------------------------------------- #
# Pure computation — three-leg MR screen (applied to a trailing deviation window)
# --------------------------------------------------------------------------- #
def variance_ratio(dev_window: np.ndarray, q: int = VR_Q) -> float:
    """Lo-MacKinlay variance ratio ``VR(q)`` of the deviation series (MR -> < 1).

    ``VR = Var(q-step diffs) / (q * Var(1-step diffs))`` on levels. NaN if degenerate.
    """
    x = np.asarray(dev_window, dtype=np.float64)
    if x.shape[0] < q + 2 or not np.all(np.isfinite(x)):
        return float("nan")
    d1 = np.diff(x)
    dq = x[q:] - x[:-q]
    v1 = np.var(d1, ddof=1)
    vq = np.var(dq, ddof=1)
    if v1 <= 0:
        return float("nan")
    return float(vq / (q * v1))


def half_life(dev_window: np.ndarray) -> float:
    """AR(1) mean-reversion half-life of the deviation series (exec bars).

    Fits ``d_t = c + phi d_{t-1}``; ``HL = -ln(2)/ln(phi)`` for ``0 < phi < 1``. NaN otherwise
    (random-walk / anti-persistent / degenerate).
    """
    x = np.asarray(dev_window, dtype=np.float64)
    if x.shape[0] < 3 or not np.all(np.isfinite(x)):
        return float("nan")
    lag, cur = x[:-1], x[1:]
    xc = lag - lag.mean()
    sxx = float(np.dot(xc, xc))
    if sxx <= 0:
        return float("nan")
    phi = float(np.dot(xc, cur - cur.mean()) / sxx)
    if not (0.0 < phi < 1.0):
        return float("nan")
    return float(-np.log(2.0) / np.log(phi))


def hurst_dfa(dev_window: np.ndarray, min_box: int = 4, n_scales: int = 8) -> float:
    """Detrended-fluctuation-analysis Hurst exponent of the deviation series (MR -> < 0.5).

    Integrates the mean-removed series, linearly detrends non-overlapping boxes at log-spaced scales,
    and regresses ``log F(s)`` on ``log s``. NaN if degenerate.
    """
    x = np.asarray(dev_window, dtype=np.float64)
    n = x.shape[0]
    if n < 4 * min_box or not np.all(np.isfinite(x)):
        return float("nan")
    y = np.cumsum(x - x.mean())
    scales = np.unique(np.floor(np.logspace(
        np.log10(min_box), np.log10(n // 4), n_scales)).astype(int))
    scales = scales[scales >= min_box]
    fs: list[float] = []
    good_s: list[int] = []
    for s in scales:
        n_box = n // s
        if n_box < 1:
            continue
        seg = y[: n_box * s].reshape(n_box, s)
        t = np.arange(s, dtype=np.float64)
        t_c = t - t.mean()
        denom = float(np.dot(t_c, t_c))
        if denom <= 0:
            continue
        b = (seg * t_c[None, :]).sum(axis=1) / denom
        a = seg.mean(axis=1) - b * t.mean()
        resid = seg - (a[:, None] + b[:, None] * t[None, :])
        f = np.sqrt((resid ** 2).mean())
        if f > 0:
            fs.append(float(f))
            good_s.append(int(s))
    if len(good_s) < 3:
        return float("nan")
    coeffs = np.polyfit(np.log(good_s), np.log(fs), 1)
    return float(coeffs[0])


def mr_screen_pass(dev_window: np.ndarray) -> bool:
    """Two-leg MR-screen conjunction on a trailing deviation window (VR & half-life).

    **Amendment A1 (2026-07-01, operator-ratified):** the original third leg, ``Hurst-DFA<0.45``, is
    dropped. It was structurally unsatisfiable on the mean-reverting deviation **level** series: DFA
    integrates its input, so it scores the integrated OU level at ``H≈1.0-1.4`` (``H<0.45`` impossible),
    and even corrected to increments it needs windows ≥400 bars / half-lives ≈2 to fire — it measures
    long-range/increment persistence, ≈neutral for the moderate OU present here, not reversion-to-a-level.
    VR and half-life measure reversion-to-a-level directly. Forensic: ``code/hurst_forensics.py``,
    ``results/hurst_forensics.json``. ``hurst_dfa`` / ``screen_legs`` are retained for that record and
    for §8 leg-sensitivity disclosure, but Hurst is **not** in the binding conjunction.
    """
    vr = variance_ratio(dev_window)
    if not (np.isfinite(vr) and vr < 1.0 - VR_DELTA):
        return False
    hl = half_life(dev_window)
    return bool(np.isfinite(hl) and 0.0 < hl <= HL_MAX)


def screen_legs(dev_window: np.ndarray) -> tuple[bool, bool, bool]:
    """Per-leg pass booleans ``(vr_pass, hl_pass, hurst_pass)`` for drop-one sensitivity (§8)."""
    vr = variance_ratio(dev_window)
    hl = half_life(dev_window)
    h = hurst_dfa(dev_window)
    return (bool(np.isfinite(vr) and vr < 1.0 - VR_DELTA),
            bool(np.isfinite(hl) and 0.0 < hl <= HL_MAX),
            bool(np.isfinite(h) and h < 0.5 - HURST_DELTA))


# --------------------------------------------------------------------------- #
# Pure computation — the five exec-aligned anchor/deviation/z constructions
# --------------------------------------------------------------------------- #
def anchor_series(
    series: str,
    exec_close: np.ndarray,
    exec_ct: np.ndarray,
    anchor: dict[str, np.ndarray],
    basket: np.ndarray | None = None,
) -> AnchorSeries:
    """Build the exec-aligned ``(dev, z)`` for one of the five anchor constructions.

    Parameters
    ----------
    series : str
        One of ``SERIES``.
    exec_close, exec_ct : np.ndarray
        Exec-domain Close and CloseTime (ascending), length ``n_exec``.
    anchor : dict
        Anchor-domain arrays: ``close, high, low, hlc3, logclose, ct`` (all ascending, aligned).
    basket : np.ndarray | None
        For S5 only: exec-aligned basket log-price (class-mates, timestamp-aligned, ``<= exec ct``).
        ``None`` / all-NaN -> UNPOWERED S5.

    Returns
    -------
    AnchorSeries
        ``dev``/``z`` exec-aligned, causal (known at exec close ``j``); lag by 1 before deciding.
    """
    a_ct = anchor["ct"]
    if series == "S1_CENTER":
        a = map_prev(a_ct, rolling_median(anchor["close"], W_A), exec_ct)
        dev = exec_close - a
        z = rolling_median_mad_z(dev, W_Z)
    elif series == "S2_RANGE":
        mid = rolling_donchian_mid(anchor["high"], anchor["low"], W_A)
        a = map_prev(a_ct, mid, exec_ct)
        dev = exec_close - a
        z = rolling_median_mad_z(dev, W_Z)
    elif series == "S3_DETREND":
        fit, _ = rolling_ols_fit(anchor["logclose"], W_A)
        a = map_prev(a_ct, fit, exec_ct)
        dev = np.log(exec_close) - a
        z = rolling_std_z(dev, W_Z)
    elif series == "S4_OU":
        theta, sig_eq = rolling_ou_fit(anchor["hlc3"], W_A)
        th_e = map_prev(a_ct, theta, exec_ct)
        se_e = map_prev(a_ct, sig_eq, exec_ct)
        dev = exec_close - th_e
        z = np.divide(dev, se_e, out=np.full(dev.shape, np.nan), where=np.isfinite(se_e) & (se_e > 0))
    elif series == "S5_SPREAD":
        if basket is None:
            dev = np.full(exec_close.shape, np.nan)
            return AnchorSeries(dev=dev, z=dev.copy(), powered_frac=0.0)
        logp = np.log(exec_close)
        a = rolling_beta_fit(logp, basket, W_Z)                    # beta on exec-domain aligned pair
        dev = logp - a
        z = rolling_std_z(dev, W_Z)
    else:
        raise ValueError(f"Unknown series: {series}")
    powered = float(np.mean(np.isfinite(dev) & np.isfinite(z))) if dev.shape[0] else 0.0
    return AnchorSeries(dev=dev, z=z, powered_frac=powered)
