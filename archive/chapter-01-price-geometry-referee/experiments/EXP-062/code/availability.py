"""EXP-062 pure helpers — long-horizon availability (AVWAP-analog lifetime MFE/MAE).

Copied verbatim from EXP-055's ``availability.py`` (HYP-008). The helpers are
substrate-generic — the end-of-M_b window takes any sorted confirmation-index
array (ZigZag confirmations in EXP-055; **MA(20,50) crossover indices** here),
so the same module serves the Phase 015 MA-substrate availability read (HYP-015)
unchanged. Provided functions:

- the **end-of-M_b window** ``end_of_mb_window``: the per-event excursion window
  ends at the **2nd** confirmation at/after the entry (the 1st ends the faded
  in-progress move M_a; the 2nd ends the reversal move M_b). On the MA substrate
  the confirmations are MA crossovers, so the window ends at the 2nd MA crossover
  at/after the harami;
- **ATR-normalised** lifetime favourable MFE / adverse MAE
  (``lifetime_excursions_atr``; ÷ Wilder ATR(14) at entry — the EXP-053 P14
  divisor);
- a **median** moving-block bootstrap (``median_block_bootstrap`` /
  ``median_diff_block_bootstrap``) reusing the EXP-049/053 regime-clustered
  resampling scheme (contiguous blocks, ``b = max(1, round(m**(1/3)))``,
  ``N_BOOT`` resamples), taking ``np.median`` of a continuous excursion;
- the mechanical ``MOVE_AVAILABLE`` / ``AVAILABILITY_*`` readout. The reference
  band ``{0.5, 1.0}`` ATR is a **comparison/reporting yardstick only — never
  subtracted** from any excursion (gross throughout).

Functions are pure (no I/O, no printing); the orchestration lives in
``run_experiment.py``.
"""
from __future__ import annotations

import numpy as np

# --------------------------------------------------------------------------- #
# Frozen constants (Phase 014-B / 015 D0 + operator scope decisions; no tuning)
# --------------------------------------------------------------------------- #
POWER_FLOOR = 30                       # P10/P14: min qualifying events to report
REF_LINES: tuple[float, float] = (0.5, 1.0)   # operator: reference band (ATR units)
REF_UPPER = 1.0                        # binding MOVE_AVAILABLE comparison line
N_BOOT = 10_000                        # P14 bootstrap resamples
BOOT_BATCH = 2_000                     # bounded bootstrap memory batch
P11_MIN_CELLS = 5                      # P11 composition threshold
P11_MIN_INSTR = 3                      # P11 composition threshold


# --------------------------------------------------------------------------- #
# Pure computation — end-of-reversal-move (M_b) window boundary
# --------------------------------------------------------------------------- #
def end_of_mb_window(
    entry_idx: np.ndarray, confirm_idx: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Per-event lifetime window end ``c2`` = the 2nd confirmation at/after entry.

    For entry bar ``e``, ``pos = searchsorted(confirm_idx, e, "right")`` is the
    first confirmation strictly after ``e`` (ends the faded in-progress move
    M_a); ``confirm_idx[pos+1]`` ends the reversal move M_b and is the window
    end. Fewer than two confirmations remain (``pos+1 >= n_confirm``) -> the event
    is **DATA_CENSORED** (``c2 = -1``), excluded by the caller and disclosed.

    Parameters
    ----------
    entry_idx : np.ndarray
        Harami entry bar indices (ascending), real domain-bar indices.
    confirm_idx : np.ndarray
        Sorted confirmation bar indices for the cell (ZigZag confirmations or, in
        EXP-062, MA(20,50) crossover indices).

    Returns
    -------
    (c2, censored) : tuple[np.ndarray[int64], np.ndarray[bool]]
        ``c2`` is the window-end bar index (``-1`` where censored); ``censored``
        is True where M_b does not complete inside the (TRAIN) frame.
    """
    n = int(entry_idx.shape[0])
    n_conf = int(confirm_idx.shape[0])
    if n == 0:
        return np.empty(0, dtype=np.int64), np.empty(0, dtype=bool)
    if n_conf == 0:
        return np.full(n, -1, dtype=np.int64), np.ones(n, dtype=bool)
    pos = np.searchsorted(confirm_idx, entry_idx, side="right")
    censored = (pos + 1) >= n_conf
    c2 = np.full(n, -1, dtype=np.int64)            # censored stay -1; only the
    keep = ~censored                               # non-censored second
    c2[keep] = confirm_idx[pos[keep] + 1]          # confirmation is materialised
    return c2, censored


# --------------------------------------------------------------------------- #
# Pure computation — ATR-normalised lifetime excursions over [e+1, c2]
# --------------------------------------------------------------------------- #
def lifetime_excursions_atr(
    high: np.ndarray, low: np.ndarray, entry_close: np.ndarray,
    entry_idx: np.ndarray, c2_idx: np.ndarray, rd: np.ndarray,
    atr_entry: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Per-event rd-aware ATR-normalised lifetime MFE and MAE (real prices).

    The window is ``[entry_idx+1, c2_idx]`` inclusive (bars strictly after entry,
    through the M_b end pivot bar). Favourable/adverse are taken in the reversal
    trade direction ``rd``; both excursions are floored at ``0.0`` (standard
    excursion convention) and divided by ``atr_entry`` (Wilder ATR(14) at the
    entry bar). Caller passes only qualifying (non-censored, finite-ATR) events;
    the loop is bounded (a few hundred events per cell).

    Returns
    -------
    (mfe, mae) : both >= 0, ATR units, aligned to ``entry_idx``.
    """
    n = int(entry_idx.shape[0])
    mfe = np.zeros(n, dtype=np.float64)
    mae = np.zeros(n, dtype=np.float64)
    for e in range(n):
        a, b = int(entry_idx[e]) + 1, int(c2_idx[e]) + 1
        assert b > a, (                             # caller passes only non-censored
            f"degenerate excursion window: entry={int(entry_idx[e])}, "  # events, so
            f"c2={int(c2_idx[e])} (expected c2 > entry)")  # c2 > entry must hold
        hi = float(high[a:b].max())
        lo = float(low[a:b].min())
        c = float(entry_close[e])
        atr = float(atr_entry[e])
        if rd[e] == 1:                              # long reversal: up favourable
            mfe[e] = max(0.0, (hi - c) / atr)
            mae[e] = max(0.0, (c - lo) / atr)
        else:                                       # short reversal: down favourable
            mfe[e] = max(0.0, (c - lo) / atr)
            mae[e] = max(0.0, (hi - c) / atr)
    return mfe, mae


def window_invariants_ok(
    entry_idx: np.ndarray, c2_idx: np.ndarray, confirm_idx: np.ndarray,
    qual: np.ndarray, n_bars: int,
) -> bool:
    """Verify the scope §Correctness-Gates window-ordering/fence invariants.

    For every qualifying (buildable, retained, non-censored) event this checks
    the invariant categories the scope lists beyond ``MFE/MAE >= 0``:

    - ``entry+1 <= c2 <= n_bars-1`` (window ordering + TRAIN fence: all domain
      bars are pre-fenced to ``CloseTime <= train_end_ts``, so ``c2 <= n_bars-1``
      is exactly "no window bar past the TRAIN edge");
    - ``c2 == confirm_idx[pos+1]`` with ``confirm_idx[pos] > entry``, where
      ``pos = searchsorted(confirm_idx, entry, "right")`` — i.e. ``c2`` is truly
      the 2nd confirmation strictly after the entry.

    Returns True iff no qualifying event violates any invariant (vacuously True
    when no event qualifies). Pure; raises nothing — the caller flags a defect.
    """
    q = np.flatnonzero(qual)
    if q.size == 0:
        return True
    e = entry_idx[q].astype(np.int64)
    c2 = c2_idx[q].astype(np.int64)
    if np.any(c2 < e + 1) or np.any(c2 > n_bars - 1):
        return False
    pos = np.searchsorted(confirm_idx, e, side="right")
    if np.any(pos + 1 >= confirm_idx.shape[0]):      # must be non-censored
        return False
    if np.any(confirm_idx[pos] <= e):                # 1st confirmation strictly
        return False                                 # after entry
    return bool(np.all(confirm_idx[pos + 1] == c2))  # c2 is the 2nd confirmation


# --------------------------------------------------------------------------- #
# Pure computation — median moving-block bootstrap (continuous statistic)
# --------------------------------------------------------------------------- #
def _block_resample_medians(
    values: np.ndarray, rng: np.random.Generator, n_boot: int, batch: int,
) -> tuple[np.ndarray, int]:
    """Moving-block resample medians of ``values`` (confirmation/entry order).

    Block length ``b = max(1, round(m**(1/3)))``; ``ceil(m/b)`` contiguous blocks
    per resample, truncated to length ``m`` — the EXP-049/053 regime-clustered
    moving-block scheme, taking ``np.median`` instead of a ratio.
    """
    m = int(values.shape[0])
    b = max(1, int(round(m ** (1.0 / 3.0))))
    n_blocks = int(np.ceil(m / b))
    max_start = max(0, m - b)
    offsets = np.arange(b, dtype=np.int64)
    meds: list[np.ndarray] = []
    done = 0
    while done < n_boot:
        k = min(batch, n_boot - done)
        starts = rng.integers(0, max_start + 1, size=(k, n_blocks))
        idx = (starts[:, :, None] + offsets[None, None, :]
               ).reshape(k, n_blocks * b)[:, :m]
        meds.append(np.median(values[idx], axis=1))
        done += k
    return np.concatenate(meds), b


def median_block_bootstrap(
    values: np.ndarray, rng: np.random.Generator,
    n_boot: int = N_BOOT, batch: int = BOOT_BATCH,
) -> tuple[float, float, float, float, int]:
    """Sample median + regime-clustered moving-block bootstrap CI of the median.

    Returns ``(median, ci_low_1s, ci_lo_2s, ci_hi_2s, block_len)`` where
    ``ci_low_1s`` is the one-sided 95% lower bound (5th percentile). An empty
    input returns NaNs (caller treats as not-powered / not-available).
    """
    m = int(values.shape[0])
    if m == 0:
        return float("nan"), float("nan"), float("nan"), float("nan"), 1
    dist, b = _block_resample_medians(values, rng, n_boot, batch)
    return (
        float(np.median(values)),
        float(np.percentile(dist, 5.0)),
        float(np.percentile(dist, 2.5)),
        float(np.percentile(dist, 97.5)),
        b,
    )


def median_diff_block_bootstrap(
    a: np.ndarray, b: np.ndarray, rng: np.random.Generator,
    n_boot: int = N_BOOT, batch: int = BOOT_BATCH,
) -> tuple[float, float, float, float]:
    """Contrast ``median(a) - median(b)`` via independent moving-block resamples.

    Each population is block-resampled by its own order (the same scheme as
    :func:`median_block_bootstrap`); the per-replicate difference forms the
    contrast distribution. Returns ``(diff, ci_low_1s, ci_lo_2s, ci_hi_2s)`` with
    ``ci_low_1s`` the one-sided 95% lower bound. Either population with < 2 events
    -> all NaN (disclosed, never a binding leg).
    """
    if a.shape[0] < 2 or b.shape[0] < 2:
        return float("nan"), float("nan"), float("nan"), float("nan")
    med_a, _ = _block_resample_medians(a, rng, n_boot, batch)
    med_b, _ = _block_resample_medians(b, rng, n_boot, batch)
    diff = med_a - med_b
    return (
        float(np.median(a) - np.median(b)),
        float(np.percentile(diff, 5.0)),
        float(np.percentile(diff, 2.5)),
        float(np.percentile(diff, 97.5)),
    )


# --------------------------------------------------------------------------- #
# Pure computation — mechanical per-cell + composition readout
# --------------------------------------------------------------------------- #
def move_available(
    m: int, mfe_ci_low_1s: float | None, median_mfe: float | None,
    median_mae: float | None,
) -> bool:
    """Mechanical per-cell ``MOVE_AVAILABLE`` (three legs, all required).

    (1) power: ``m >= POWER_FLOOR``; (2) availability vs the upper reference line:
    ``mfe_ci_low_1s > REF_UPPER`` (a lower-bound comparison on the median — the
    reference value is never subtracted from any MFE); (3) asymmetry:
    ``median_mfe > median_mae``. A NaN/None bound fails leg (2) (cannot assert),
    never silently passes.
    """
    if m < POWER_FLOOR:
        return False
    if mfe_ci_low_1s is None or not np.isfinite(mfe_ci_low_1s):
        return False
    if median_mfe is None or median_mae is None:
        return False
    if not (np.isfinite(median_mfe) and np.isfinite(median_mae)):
        return False
    return bool(mfe_ci_low_1s > REF_UPPER and median_mfe > median_mae)


def availability_status(m: int, available: bool) -> str:
    """Per-cell status string for the composition map / heatmaps."""
    if m < POWER_FLOOR:
        return "NOT_VIABLE_BY_POWER"
    return "MOVE_AVAILABLE" if available else "NOT_AVAILABLE"
