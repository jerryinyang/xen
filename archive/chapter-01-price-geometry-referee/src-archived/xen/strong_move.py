"""Strong-move filters for ``CF-HA-HARAMI-001`` (Phase 014, P7/P8).

Two causal, deterministic move-population filters over a confirmed ZigZag move
segmentation (``xen.zigzag``), reusable across Phase 014 (EXP-051 characterisation;
014-B combined events):

- **``/STRONG-STAT`` (P7)** — a confirmed move is *retained* iff its real-price
  magnitude ``|EndPrice - StartPrice|`` is large relative to a trailing causal
  window of the prior ``min(window, available)`` confirmed-move magnitudes. Two
  registered threshold forms: the **p75** percentile (binding) and **median +
  1*MAD** (disclosed). A move with ``< min_window`` prior confirmed moves has no
  defined threshold (warmup -> ``NO_DECISION``).

- **``/STRONG-HA`` (P8)** — detection on Heiken Ashi candles (detection only; no HA
  price feeds any magnitude metric). An HA bar *qualifies* iff its real body is at
  least the trailing causal median HA body **and** it has no opposing wick
  (bullish: ``HALow == HAOpen``; bearish: ``HAHigh == HAOpen``). A qualifying *run*
  is ``run_len`` consecutive same-direction qualifying bars. A confirmed move is
  retained iff a qualifying run lies fully inside its ``(StartTime, EndTime]`` span
  -- under the **same-direction** rule (binding) or the **any-direction** rule
  (disclosed sensitivity). Same-direction retention is a subset of any-direction.

**Causality.** ``/STRONG-STAT`` windows use only moves strictly prior (by sequence
order = ``ConfirmTime`` order); ``/STRONG-HA`` qualification uses each bar's own body
and a strictly-prior trailing median, so runs are causal by construction. The
run->move mapping operates on an already-confirmed completed segmentation (not a
live signal): the retained-move *magnitude* references the move's terminal pivot and
is therefore a non-tradable descriptive characterisation, never a trading decision.
All functions are pure (no I/O, no import-time side effects) and deterministic:
identical input yields identical output.
"""
from __future__ import annotations

import numpy as np
import polars as pl


# Per-move filter decision classes.
NO_DECISION = "no_decision"   # warmup: no defined threshold / cannot contain a run

DEFAULT_WINDOW = 20           # P7/P8 trailing window length
DEFAULT_MIN_WINDOW = 5        # P4-analog warmup floor
DEFAULT_RUN_LEN = 3           # P8 X = 3 consecutive HA bars
DEFAULT_P75 = 0.75            # P7 binding percentile


# --------------------------------------------------------------------------- #
# Type-7 (linear) quantile on a pre-sorted array (matches numpy method="linear")
# --------------------------------------------------------------------------- #
def _quantile_sorted(sorted_vals: np.ndarray, q: float) -> float:
    """Linear (type-7) quantile of an ascending array; matches ``numpy`` default."""
    n = sorted_vals.shape[0]
    if n == 1:
        return float(sorted_vals[0])
    pos = q * (n - 1)
    lo = int(np.floor(pos))
    frac = pos - lo
    if lo >= n - 1:
        return float(sorted_vals[-1])
    return float(sorted_vals[lo] + frac * (sorted_vals[lo + 1] - sorted_vals[lo]))


# --------------------------------------------------------------------------- #
# /STRONG-STAT — trailing-window move-magnitude filter (both forms)
# --------------------------------------------------------------------------- #
def move_magnitudes(moves: pl.DataFrame) -> np.ndarray:
    """Real-price move magnitudes ``|EndPrice - StartPrice|`` (one per move, in order)."""
    if moves.height == 0:
        return np.empty(0, dtype=np.float64)
    start = moves.get_column("StartPrice").to_numpy().astype(np.float64)
    end = moves.get_column("EndPrice").to_numpy().astype(np.float64)
    return np.abs(end - start)


def strong_stat_decisions(
    magnitudes: np.ndarray,
    window: int = DEFAULT_WINDOW,
    min_window: int = DEFAULT_MIN_WINDOW,
    q: float = DEFAULT_P75,
) -> dict[str, np.ndarray]:
    """Per-move ``/STRONG-STAT`` decisions for both registered threshold forms.

    For move ``i`` the window is the ``min(window, available)`` magnitudes strictly
    prior to ``i`` (sequence order). The window includes every prior confirmed move
    (degenerate zero-magnitude moves are part of the realized sequence); the *caller*
    excludes degenerate moves from the population. A move with ``< min_window`` prior
    moves is ``NO_DECISION`` (``defined = False``). Retention is inclusive (``>=``).

    Parameters
    ----------
    magnitudes : np.ndarray
        Move magnitudes in confirmation order (float64), length ``n``.
    window, min_window : int
        Trailing window length and warmup floor.
    q : float
        Binding percentile (default 0.75).

    Returns
    -------
    dict[str, np.ndarray]
        ``defined`` (bool), ``retained_p75`` (bool), ``retained_mad`` (bool), each
        length ``n``. Retained flags are ``False`` wherever ``defined`` is ``False``.
    """
    n = int(magnitudes.shape[0])
    defined = np.zeros(n, dtype=bool)
    retained_p75 = np.zeros(n, dtype=bool)
    retained_mad = np.zeros(n, dtype=bool)
    if n == 0:
        return {"defined": defined, "retained_p75": retained_p75, "retained_mad": retained_mad}
    mags = magnitudes.astype(np.float64)
    for i in range(n):
        lo = max(0, i - window)
        w = mags[lo:i]  # strictly prior
        if w.shape[0] < min_window:
            continue
        defined[i] = True
        ws = np.sort(w)
        thr_p75 = _quantile_sorted(ws, q)
        med = _quantile_sorted(ws, 0.5)
        mad = _quantile_sorted(np.sort(np.abs(w - med)), 0.5)  # raw MAD (no 1.4826)
        retained_p75[i] = mags[i] >= thr_p75
        retained_mad[i] = mags[i] >= (med + mad)
    return {"defined": defined, "retained_p75": retained_p75, "retained_mad": retained_mad}


# --------------------------------------------------------------------------- #
# /STRONG-HA — HA impulse qualification, run detection, run->move mapping
# --------------------------------------------------------------------------- #
def annotate_ha_impulse(
    ha_candles: pl.DataFrame,
    window: int = DEFAULT_WINDOW,
    min_window: int = DEFAULT_MIN_WINDOW,
) -> pl.DataFrame:
    """Annotate HA candles with the per-bar ``/STRONG-HA`` qualification.

    Adds ``body`` (``|HAClose - HAOpen|``), ``median_body`` (trailing causal median of
    the prior ``min(window, available)`` bodies, defined once ``>= min_window`` prior
    bodies exist), ``median_defined``, ``no_opposing_wick`` (bullish: ``HALow ==
    HAOpen``; bearish: ``HAHigh == HAOpen``, exact equality), and ``qualify``
    (``median_defined & (body >= median_body) & no_opposing_wick``). HA prices are
    used here for detection only.

    ``ha_candles`` must carry ``CloseTime, HAOpen, HAHigh, HALow, HAClose, Direction``
    sorted by ``CloseTime``.
    """
    required = {"CloseTime", "HAOpen", "HAHigh", "HALow", "HAClose", "Direction"}
    missing = required.difference(ha_candles.columns)
    if missing:
        raise ValueError(f"ha_candles missing required columns: {sorted(missing)}")
    body = (pl.col("HAClose") - pl.col("HAOpen")).abs()
    no_wick = (
        pl.when(pl.col("Direction") == 1)
        .then(pl.col("HALow") == pl.col("HAOpen"))
        .otherwise(pl.col("HAHigh") == pl.col("HAOpen"))
    )
    out = ha_candles.with_columns(body.alias("body")).with_columns(
        pl.col("body").shift(1).rolling_median(window_size=window, min_periods=min_window)
        .alias("median_body"),
        no_wick.alias("no_opposing_wick"),
    )
    return out.with_columns(
        pl.col("median_body").is_not_null().alias("median_defined"),
        (
            pl.col("median_body").is_not_null()
            & (pl.col("body") >= pl.col("median_body"))
            & pl.col("no_opposing_wick")
        ).alias("qualify"),
    )


def ha_run_warmup_end_time(
    ha_annotated: pl.DataFrame,
    min_window: int = DEFAULT_MIN_WINDOW,
    run_len: int = DEFAULT_RUN_LEN,
) -> object | None:
    """``CloseTime`` of the earliest HA bar that could *end* a qualifying run.

    The earliest qualifiable bar is at index ``min_window`` (it has ``min_window``
    prior bodies); a run of ``run_len`` consecutive qualifiable bars can therefore end
    no earlier than index ``min_window + run_len - 1``. A move whose ``EndTime`` is
    before this time cannot contain a run (``NO_DECISION`` for ``/STRONG-HA``).
    Returns ``None`` when the frame is too short for any run.
    """
    end_idx = min_window + run_len - 1
    if ha_annotated.height <= end_idx:
        return None
    return ha_annotated.get_column("CloseTime")[end_idx]


def find_impulse_runs(
    ha_annotated: pl.DataFrame,
    run_len: int = DEFAULT_RUN_LEN,
) -> pl.DataFrame:
    """Detect qualifying impulse runs (``run_len`` consecutive same-direction bars).

    Returns one row per run with ``run_first_time``, ``run_last_time`` (the run's first
    and last bar ``CloseTime``) and ``run_dir`` (the shared ``Direction``). Vectorised:
    a window of length ``run_len`` ending at bar ``i`` is a run iff all bars qualify and
    all share one direction (``|sum(Direction)| == run_len`` for ``Direction in
    {-1,+1}``).
    """
    n = ha_annotated.height
    time_schema = ha_annotated.schema["CloseTime"]
    empty = pl.DataFrame(
        schema={"run_first_time": time_schema, "run_last_time": time_schema,
                "run_dir": pl.Int32}
    )
    if n < run_len:
        return empty
    qualify = ha_annotated.get_column("qualify").to_numpy()
    direction = ha_annotated.get_column("Direction").to_numpy().astype(np.int64)
    times = ha_annotated.get_column("CloseTime")

    cum_q = np.concatenate(([0], np.cumsum(qualify.astype(np.int64))))
    all_qual = (cum_q[run_len:] - cum_q[:-run_len]) == run_len
    cum_d = np.concatenate(([0], np.cumsum(direction)))
    win_dir_sum = cum_d[run_len:] - cum_d[:-run_len]
    same_dir = np.abs(win_dir_sum) == run_len
    is_run_end = all_qual & same_dir  # window [j, j+run_len-1] ends at j+run_len-1

    end_idx = np.flatnonzero(is_run_end) + (run_len - 1)
    if end_idx.shape[0] == 0:
        return empty
    first_idx = end_idx - (run_len - 1)
    return pl.DataFrame({
        "run_first_time": times.gather(first_idx),
        "run_last_time": times.gather(end_idx),
        "run_dir": direction[end_idx].astype(np.int32),
    })


def map_runs_to_moves(
    run_first_epoch: np.ndarray,
    run_last_epoch: np.ndarray,
    run_dir: np.ndarray,
    move_start_epoch: np.ndarray,
    move_end_epoch: np.ndarray,
    move_dir: np.ndarray,
) -> dict[str, np.ndarray]:
    """Map qualifying runs to the confirmed moves whose span fully contains them.

    A run is *inside* move ``m`` iff ``move_start_epoch[m] < run_first`` and
    ``run_last <= move_end_epoch[m]`` -- i.e. all run bars fall in ``(StartTime_m,
    EndTime_m]``. Because confirmed moves tile time (``EndTime`` strictly increasing,
    ``StartTime_{m} = EndTime_{m-1}``), the containing move of ``run_last`` is found by
    a forward as-of search on ``move_end_epoch``.

    Returns ``retained_primary`` (run direction matches the move) and
    ``retained_sensitivity`` (any direction), both bool arrays over moves.
    ``retained_primary`` is a subset of ``retained_sensitivity`` by construction.
    """
    n_moves = int(move_end_epoch.shape[0])
    retained_primary = np.zeros(n_moves, dtype=bool)
    retained_sensitivity = np.zeros(n_moves, dtype=bool)
    if n_moves == 0 or run_last_epoch.shape[0] == 0:
        return {"retained_primary": retained_primary,
                "retained_sensitivity": retained_sensitivity}

    idx = np.searchsorted(move_end_epoch, run_last_epoch, side="left")
    valid = idx < n_moves
    m = idx[valid]
    first_v = run_first_epoch[valid]
    last_v = run_last_epoch[valid]
    dir_v = run_dir[valid]
    inside = (first_v > move_start_epoch[m]) & (last_v <= move_end_epoch[m])
    m_in = m[inside]
    dir_in = dir_v[inside]
    retained_sensitivity[m_in] = True
    dir_match = dir_in == move_dir[m_in]
    retained_primary[m_in[dir_match]] = True
    return {"retained_primary": retained_primary,
            "retained_sensitivity": retained_sensitivity}
