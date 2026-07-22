"""Causal 3-barrier capture geometry on real bars (``CF-HA-HARAMI-001`` family).

Given confirmed ZigZag moves (see ``xen.zigzag``) on real domain bars, this
module builds the Phase 014 benchmark 3-barrier system at each trend-change
confirmation and resolves, on real OHLC, whether price reaches the favourable
target before the adverse target. It is the first-class **capture-geometry**
primitive of Phase 014-A (EXP-049 / HYP-002): gross, exit-agnostic, real prices
only. No Heiken Ashi price ever enters a metric.

Frozen Phase 014 D0 defaults implemented here (no tuning):

- **Entry** = the confirmation bar's real close (``ConfirmClose``).
- **Reference move (P5 ``LOOKBACK=1``)** = the just-confirmed move; magnitude
  ``M = |EndPrice - StartPrice|`` (``M = 0`` excluded). Reversal direction
  ``rd = -Direction``.
- **Favourable target, two geometries (X = 50%)**:
  - **G1 (distance-based, primary):** ``fav_dist = 0.50 * M``;
    ``fav = C + rd*fav_dist``; ``adv = C - rd*fav_dist`` (1:1, P3).
  - **G2 (retracement-level, secondary):** ``level = E - Direction*0.50*M`` (the
    move midpoint); ``fav_dist = rd*(level - C)``; **degenerate if
    ``fav_dist <= 0``** (entry already at/through the level) -> excluded with
    record; else ``fav = level``, ``adv = C - rd*fav_dist`` (1:1 of fav_dist).
- **Third barrier (P4):** per-cell adaptive time cap ``N = max(6, round(1.5 *
  median(duration_bars of the trailing 20 moves confirmed strictly before the
  event)))`` completed bars after the confirmation bar, where ``duration_bars``
  of a move is its confirmation-to-confirmation bar count. An event whose
  trailing window holds ``< 5`` such durations is **warmup-excluded** (no
  barrier), never silently capped.
- **Resolution:** first real bar in ``[ConfirmIdx+1, min(ConfirmIdx+N,
  last_train_idx)]`` to touch a target resolves the event; a **same-bar
  double-touch resolves to ADVERSE** (conservative; intrabar order is unknown).
  Classes: ``FAV``, ``ADV``, ``TIMECAP`` (neither by ``N``), ``DATA_CENSORED``
  (window truncated by the TRAIN edge before ``N`` and before any hit).

The first-touch scan and time-cap derivation are explicit bounded sequential
loops (their causal/streaming semantics are the object under test). The block
bootstrap of the capture proportion is vectorized in bounded batches.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl

# --------------------------------------------------------------------------- #
# Frozen Phase 014 D0 constants (no tuning)
# --------------------------------------------------------------------------- #
FAVOURABLE_FRACTION = 0.50      # P2: X% of the reference move
THIRD_BARRIER_K = 1.5           # P4: time-cap multiple
THIRD_BARRIER_WINDOW = 20       # P4: trailing confirmed-move window
THIRD_BARRIER_FLOOR = 6         # P4: minimum cap (bars)
THIRD_BARRIER_MIN_MOVES = 5     # P4: warmup -> fewer than this -> excluded
RESOLVED_FLOOR = 30             # P12: minimum resolved events to report routing
VIABLE_R = 0.55                 # P12: capture-rate viability bar
NULL_R = 0.50                   # symmetric 1:1-barrier zero-edge reference
N_BOOT = 10_000                 # P12: bootstrap resamples
BOOT_BATCH = 2_000              # bounded bootstrap memory batch

# Outcome class codes.
CLASS_DATA_CENSORED = -1
CLASS_TIMECAP = 0
CLASS_ADV = 1
CLASS_FAV = 2
CLASS_LABELS: dict[int, str] = {
    CLASS_FAV: "FAV", CLASS_ADV: "ADV",
    CLASS_TIMECAP: "TIMECAP", CLASS_DATA_CENSORED: "DATA_CENSORED",
}


@dataclass(frozen=True)
class GeometryResult:
    """Per-cell capture outcome for one favourable geometry (G1 or G2)."""

    classes: np.ndarray            # outcome code per defined event (ordered)
    defined: int                   # events with a built barrier
    fav: int
    adv: int
    timecap: int
    data_censored: int
    resolved: int                  # fav + adv
    r: float | None                # fav / resolved, or None if resolved == 0
    ci_low_1s: float | None        # one-sided 95% lower bound (5th pct)
    ci_lo_2s: float | None
    ci_hi_2s: float | None
    boot_degenerate_frac: float
    block_len: int


# --------------------------------------------------------------------------- #
# Pure computation — indices, time cap, barriers
# --------------------------------------------------------------------------- #
def confirm_indices(moves: pl.DataFrame, bars: pl.DataFrame) -> np.ndarray:
    """Map each move's ``ConfirmTime`` to its domain-bar index (exact match).

    Raises ``ValueError`` if any confirmation time is absent from the bar grid
    (would indicate a substrate/aggregation inconsistency).
    """
    bar_epoch = bars.get_column("CloseTime").dt.epoch("s").to_numpy()
    confirm_epoch = moves.get_column("ConfirmTime").dt.epoch("s").to_numpy()
    idx = np.searchsorted(bar_epoch, confirm_epoch)
    if np.any(idx >= bar_epoch.shape[0]) or np.any(bar_epoch[np.minimum(
            idx, bar_epoch.shape[0] - 1)] != confirm_epoch):
        raise ValueError("ConfirmTime not found on the domain-bar grid")
    return idx.astype(np.int64)


def time_caps(confirm_idx: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """P4 adaptive caps per event and the warmup (insufficient-context) mask.

    ``duration_bars`` of move ``j`` is ``confirm_idx[j] - confirm_idx[j-1]``.
    For event ``k`` the trailing window is the durations of the (up to 20) moves
    confirmed strictly before ``k``; ``< 5`` available -> warmup (no cap).

    Returns
    -------
    (n_event, warmup) : (np.ndarray[int64], np.ndarray[bool])
        ``n_event`` is 0 where ``warmup`` is True (no defined cap).
    """
    n = confirm_idx.shape[0]
    durations = np.diff(confirm_idx)                  # durations[i] = move i+1
    # Move 0 has no prior confirmation, so its duration_bars is undefined (scope
    # §122); np.diff naturally omits it, so the trailing window below ranges over
    # durations of moves 1..k-1 only — the initial undefined duration is never used.
    n_event = np.zeros(n, dtype=np.int64)
    warmup = np.ones(n, dtype=bool)
    for k in range(n):
        lo, hi = max(0, k - THIRD_BARRIER_WINDOW - 1), max(0, k - 1)
        window = durations[lo:hi]                     # moves confirmed before k
        if window.shape[0] < THIRD_BARRIER_MIN_MOVES:
            continue
        cap = max(THIRD_BARRIER_FLOOR,
                  int(round(THIRD_BARRIER_K * float(np.median(window)))))
        n_event[k], warmup[k] = cap, False
    return n_event, warmup


def build_barriers(
    moves: pl.DataFrame, confirm_close: np.ndarray,
) -> dict[str, np.ndarray]:
    """Vectorized barrier targets for both geometries (no resolution yet).

    Returns arrays keyed by name: ``rd`` (reversal dir), ``m`` (magnitude),
    ``m0`` (zero-magnitude mask), G1/G2 ``fav``/``adv`` targets, and
    ``g2_degenerate`` (G2 ``fav_dist <= 0``) mask.
    """
    d = moves.get_column("Direction").to_numpy().astype(np.int64)
    s = moves.get_column("StartPrice").to_numpy().astype(np.float64)
    e = moves.get_column("EndPrice").to_numpy().astype(np.float64)
    c = confirm_close
    m = np.abs(e - s)
    rd = -d
    fav_dist_g1 = FAVOURABLE_FRACTION * m
    level = e - d * FAVOURABLE_FRACTION * m
    fav_dist_g2 = rd * (level - c)
    return {
        "rd": rd, "m": m, "m0": m == 0.0,
        "g1_fav": c + rd * fav_dist_g1, "g1_adv": c - rd * fav_dist_g1,
        "g2_fav": level, "g2_adv": c - rd * fav_dist_g2,
        "g2_degenerate": fav_dist_g2 <= 0.0,
    }


# --------------------------------------------------------------------------- #
# Pure computation — first-touch resolution (explicit causal loop)
# --------------------------------------------------------------------------- #
def resolve_first_touch(
    high: np.ndarray, low: np.ndarray, confirm_idx: np.ndarray,
    fav_target: np.ndarray, adv_target: np.ndarray, rd: np.ndarray,
    n_event: np.ndarray, defined: np.ndarray, n_bars: int,
) -> np.ndarray:
    """First-touch class per event over ``[ConfirmIdx+1, ConfirmIdx+N]`` real
    bars, fenced to ``n_bars-1``; same-bar double-touch -> ADVERSE.

    Only ``defined`` events are resolved; others get ``CLASS_DATA_CENSORED`` as
    a placeholder and must be filtered out by the caller before tallying.
    """
    out = np.full(confirm_idx.shape[0], CLASS_DATA_CENSORED, dtype=np.int64)
    for e in range(confirm_idx.shape[0]):
        if not defined[e]:
            continue
        start = int(confirm_idx[e]) + 1
        cap_end = int(confirm_idx[e]) + int(n_event[e])
        end = min(cap_end, n_bars - 1)
        ft, at, r = fav_target[e], adv_target[e], rd[e]
        cls = _scan_window(high, low, start, end, ft, at, r)
        if cls is not None:
            out[e] = cls
        elif end < cap_end:
            out[e] = CLASS_DATA_CENSORED       # truncated by TRAIN edge
        else:
            out[e] = CLASS_TIMECAP             # full cap, no hit
    return out


def _scan_window(
    high: np.ndarray, low: np.ndarray, start: int, end: int,
    fav_target: float, adv_target: float, rd: int,
) -> int | None:
    """Bounded sequential first-touch scan of one event window (causal)."""
    for i in range(start, end + 1):
        if rd == 1:
            fav, adv = high[i] >= fav_target, low[i] <= adv_target
        else:
            fav, adv = low[i] <= fav_target, high[i] >= adv_target
        if adv:                                # tie (fav & adv) -> ADVERSE
            return CLASS_ADV
        if fav:
            return CLASS_FAV
    return None


# --------------------------------------------------------------------------- #
# Pure computation — regime-clustered moving-block bootstrap of the proportion
# --------------------------------------------------------------------------- #
def block_bootstrap_ci(
    is_fav: np.ndarray, is_resolved: np.ndarray, rng: np.random.Generator,
    n_boot: int = N_BOOT, batch: int = BOOT_BATCH,
) -> tuple[float, float, float, float, int]:
    """Moving-block bootstrap of ``r = sum(fav)/sum(resolved)`` over the
    confirmation-ordered defined-event sequence (the P12 regime-clustered
    bootstrap; clustering unit = the confirmed move).

    Block length ``b = max(1, round(m**(1/3)))``; ``ceil(m/b)`` contiguous
    blocks per resample (truncated to length ``m``). Degenerate resamples
    (``sum(resolved) == 0``) are discarded and their fraction disclosed.

    Returns ``(ci_low_1s, ci_lo_2s, ci_hi_2s, degenerate_frac, block_len)`` —
    ``ci_low_1s`` is the one-sided 95% lower bound (5th percentile).
    """
    m = is_fav.shape[0]
    b = max(1, int(round(m ** (1.0 / 3.0))))
    n_blocks = int(np.ceil(m / b))
    max_start = max(0, m - b)
    fav = is_fav.astype(np.int32)
    res = is_resolved.astype(np.int32)
    offsets = np.arange(b, dtype=np.int64)
    r_stars: list[np.ndarray] = []
    degenerate, done = 0, 0
    while done < n_boot:
        k = min(batch, n_boot - done)
        starts = rng.integers(0, max_start + 1, size=(k, n_blocks))
        idx = (starts[:, :, None] + offsets[None, None, :]
               ).reshape(k, n_blocks * b)[:, :m]
        favc = fav[idx].sum(axis=1)
        resc = res[idx].sum(axis=1)
        valid = resc > 0
        degenerate += int((~valid).sum())
        r_stars.append(favc[valid] / resc[valid])
        done += k
    all_r = np.concatenate(r_stars)
    if all_r.shape[0] == 0:
        return float("nan"), float("nan"), float("nan"), 1.0, b
    return (
        float(np.percentile(all_r, 5.0)),
        float(np.percentile(all_r, 2.5)),
        float(np.percentile(all_r, 97.5)),
        degenerate / n_boot,
        b,
    )


# --------------------------------------------------------------------------- #
# Pure computation — per-geometry assembly
# --------------------------------------------------------------------------- #
def summarize_geometry(
    classes_all: np.ndarray, defined: np.ndarray, rng: np.random.Generator,
) -> GeometryResult:
    """Tally one geometry's defined events and (if powered) bootstrap ``r``."""
    classes = classes_all[defined]
    fav = int((classes == CLASS_FAV).sum())
    adv = int((classes == CLASS_ADV).sum())
    timecap = int((classes == CLASS_TIMECAP).sum())
    censored = int((classes == CLASS_DATA_CENSORED).sum())
    resolved = fav + adv
    r = (fav / resolved) if resolved > 0 else None
    ci_low = ci_lo = ci_hi = None
    degen_frac = 0.0
    block_len = max(1, int(round(max(classes.shape[0], 1) ** (1.0 / 3.0))))
    if resolved >= RESOLVED_FLOOR:             # P12 power gate before inference
        is_fav = (classes == CLASS_FAV)
        is_res = (classes == CLASS_FAV) | (classes == CLASS_ADV)
        ci_low, ci_lo, ci_hi, degen_frac, block_len = block_bootstrap_ci(
            is_fav, is_res, rng)
    return GeometryResult(
        classes=classes, defined=int(classes.shape[0]), fav=fav, adv=adv,
        timecap=timecap, data_censored=censored, resolved=resolved, r=r,
        ci_low_1s=ci_low, ci_lo_2s=ci_lo, ci_hi_2s=ci_hi,
        boot_degenerate_frac=degen_frac, block_len=block_len,
    )


def viable_status(result: GeometryResult) -> str:
    """Mechanical P12 per-cell status for one geometry."""
    if result.resolved < RESOLVED_FLOOR or result.r is None:
        return "NOT_VIABLE_BY_POWER"
    if result.r < VIABLE_R:
        return "BELOW_R"
    # A NaN lower bound means the bootstrap produced no valid resample (all
    # resamples degenerate; block_bootstrap_ci -> NaN with degen_frac==1.0).
    # IEEE 754 makes ``NaN <= NULL_R`` False and ``NaN is None`` False, so this
    # NaN must be caught explicitly or it would silently fall through to VIABLE
    # despite zero valid CI. No valid CI -> cannot assert CI_low>0.50.
    if (result.ci_low_1s is None or np.isnan(result.ci_low_1s)
            or result.ci_low_1s <= NULL_R):
        return "CI_SPANS_050"
    return "VIABLE"
