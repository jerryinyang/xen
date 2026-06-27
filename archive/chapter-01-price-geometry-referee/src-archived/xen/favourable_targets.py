"""Favourable-target geometry for ``CF-HA-HARAMI-001`` (Phase 014-B, EXP-056).

The single new analysis module for the favourable-target surface read. It supplies
the *favourable-leg* primitives that EXP-056 varies one-at-a-time against the
frozen benchmark (``fav = C + rd*0.5*M_sofar``), while the adverse target (1:1),
the third barrier (adaptive time cap), and the P15 fills are held at benchmark and
reused from :mod:`xen.expectancy`:

1. **Volume profile of a reference move** (`volume_profile_levels`) — distributes
   each reference bar's ``TickVolume`` uniformly across its real ``[Low, High]``
   range into fixed-width ATR-scaled price bins, then returns the POC (max-volume
   bin centre) and the 70%-value-area boundaries ``VAL``/``VAH``. ``TickVolume`` is
   a **broker tick-count proxy** for traded volume — disclosed by every caller.
2. **Trailing-magnitude distance** (`trailing_magnitude_distance`) — a favourable
   distance ``frac * median(|magnitude|)`` of the trailing ``W`` moves confirmed
   *strictly before* the entry (the ``/MAGTARGET`` model; a magnitude estimate, no
   absolute price level).
3. **Generalized barriers** (`barriers_from_fav_level`, `barriers_from_distance`) —
   given a favourable price level (VP) or a favourable distance (BENCH/MAG), build
   ``(fav, adv, fav_dist)`` under the benchmark **1:1** adverse model
   (``adv = C - rd*fav_dist``) and a ``valid = fav_dist > 0`` flag (the target lies
   on the reversal side of ``C``). Real prices only.
4. **Paired median contrast bootstrap** (`paired_median_contrast_ci`) — a
   moving-block bootstrap of ``median(variant) - median(benchmark)`` on the
   **common qualifying-event subset**, drawing one set of block indices and
   applying it to both series so the shared event/regime noise cancels. Block
   construction is identical to :func:`xen.expectancy.bootstrap_median_distribution`;
   only the statistic (a paired median difference) changes.

Real prices only in every metric. Heiken Ashi prices never enter this module.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# --------------------------------------------------------------------------- #
# Frozen EXP-056 predeclared favourable-target constants (no tuning)
# --------------------------------------------------------------------------- #
VP_BIN_FRACTION = 0.10      # VP bin width = 0.10 * ATR_entry
VP_VALUE_AREA = 0.70        # VP value-area fraction
VP_MIN_REF_BARS = 3         # VP insufficient-profile floor (reference-span bars)
VP_MAX_BINS = 200_000       # defensive bound: n_bins scales with the reference
#                             range / (0.1*ATR_entry) ratio, NOT the bar count;
#                             a runaway ratio (e.g. volatility contraction) is a
#                             SUBSTRATE/METHOD_DEFECT tripwire, never silently run.
N_BOOT = 10_000             # P14 bootstrap resamples
BOOT_BATCH = 2_000          # bounded bootstrap memory batch


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class VPLevels:
    """Volume-profile levels for one reference move (real prices)."""

    defined: bool        # a profile with positive total volume was built
    poc: float           # centre of the maximum-volume bin
    val: float           # low edge of the lowest value-area bin
    vah: float           # high edge of the highest value-area bin
    n_bins: int
    total_volume: float  # summed reference TickVolume (proxy)


# --------------------------------------------------------------------------- #
# Pure computation — generalized benchmark-adverse barriers (1:1)
# --------------------------------------------------------------------------- #
def barriers_from_distance(
    entry_close: np.ndarray, rd: np.ndarray, fav_dist: np.ndarray,
) -> dict[str, np.ndarray]:
    """Barriers from a favourable *distance* (BENCH / ``/MAGTARGET``).

    ``fav = C + rd*fav_dist``; ``adv = C - rd*fav_dist`` (benchmark 1:1). ``valid``
    is ``fav_dist > 0`` (a non-positive distance has no reversal-side target).
    Real prices only.
    """
    return {
        "fav": entry_close + rd * fav_dist,
        "adv": entry_close - rd * fav_dist,
        "fav_dist": fav_dist,
        "valid": fav_dist > 0.0,
    }


def barriers_from_fav_level(
    entry_close: np.ndarray, rd: np.ndarray, fav_level: np.ndarray,
) -> dict[str, np.ndarray]:
    """Barriers from a favourable *price level* (``/VPTARGET``).

    ``fav_dist = rd*(fav_level - C)``; ``fav = fav_level``;
    ``adv = C - rd*fav_dist`` (benchmark 1:1). ``valid`` is ``fav_dist > 0`` (the
    level lies on the reversal side of ``C``; otherwise the variant event is
    excluded-with-record, never clamped). Non-finite levels are invalid.
    """
    with np.errstate(invalid="ignore"):
        fav_dist = rd * (fav_level - entry_close)
    valid = np.isfinite(fav_level) & (fav_dist > 0.0)
    return {
        "fav": fav_level,
        "adv": entry_close - rd * fav_dist,
        "fav_dist": fav_dist,
        "valid": valid,
    }


# --------------------------------------------------------------------------- #
# Pure computation — trailing-magnitude favourable distance (/MAGTARGET)
# --------------------------------------------------------------------------- #
def trailing_magnitude_distance(
    entry_epoch: np.ndarray, move_confirm_epoch: np.ndarray,
    move_magnitude: np.ndarray, window: int, frac: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Favourable distance from the trailing ``W`` moves confirmed before entry.

    For each entry ``t_i`` the binding window is the magnitudes of the last
    ``window`` moves with ``ConfirmTime`` *strictly* before ``t_i``. Fewer than
    ``window`` such moves -> ``defined = False`` (warmup-excluded). Otherwise
    ``fav_dist = frac * median(window magnitudes)`` (always positive, magnitudes
    are non-negative). Real prices only.

    Returns ``(fav_dist, defined)``; ``fav_dist`` is 0 where ``defined`` is False.
    """
    n = int(entry_epoch.shape[0])
    fav_dist = np.zeros(n, dtype=np.float64)
    defined = np.zeros(n, dtype=bool)
    # last move index whose ConfirmTime is strictly before the entry
    j_last = np.searchsorted(move_confirm_epoch, entry_epoch, side="left") - 1
    for e in range(n):
        jj = int(j_last[e])
        if jj + 1 < window:                      # fewer than W moves before t_i
            continue
        w = move_magnitude[jj - window + 1:jj + 1]
        defined[e] = True
        fav_dist[e] = frac * float(np.median(w))
    return fav_dist, defined


# --------------------------------------------------------------------------- #
# Pure computation — volume profile of one reference move (/VPTARGET)
# --------------------------------------------------------------------------- #
def volume_profile_levels(
    low: np.ndarray, high: np.ndarray, volume: np.ndarray, bin_width: float,
    value_area: float = VP_VALUE_AREA,
) -> VPLevels:
    """POC and 70%-value-area edges of a TickVolume profile (real prices).

    Each bar's ``volume`` is distributed **uniformly across its ``[Low, High]``
    range** into fixed-width bins of width ``bin_width`` spanning the reference
    ``[min Low, max High]`` (a degenerate ``High == Low`` bar deposits its full
    volume in the single bin containing that price). Deterministic tie-breaks:
    the POC is the **lowest-index (lowest-price)** maximum-volume bin; the value
    area grows outward from the POC annexing the larger-volume neighbour, **upper
    bin first** on a tie.

    Undefined (``defined = False``) when there are no bars, a non-positive bin
    width, or zero total volume.
    """
    n = int(low.shape[0])
    total_v = float(volume.sum()) if n else 0.0
    if n == 0 or bin_width <= 0.0 or total_v <= 0.0:
        return VPLevels(False, float("nan"), float("nan"), float("nan"), 0, total_v)
    lo, hi = float(low.min()), float(high.max())
    span = hi - lo
    n_bins = max(1, int(np.ceil(span / bin_width))) if span > 0.0 else 1
    if n_bins > VP_MAX_BINS:                       # disclosed defensive bound
        raise ValueError(
            f"volume_profile_levels: n_bins={n_bins} exceeds VP_MAX_BINS={VP_MAX_BINS} "
            f"(span={span}, bin_width={bin_width}); reference range/ATR ratio runaway")
    bin_vol = _accumulate_bin_volume(low, high, volume, lo, bin_width, n_bins)
    binned_v = float(bin_vol.sum())
    if binned_v <= 0.0:
        return VPLevels(False, float("nan"), float("nan"), float("nan"), n_bins, total_v)
    # Invariant (analysis-plan Step 9): the per-bar uniform deposit partitions
    # [lo,hi], so binned volume conserves the reference TickVolume total.
    assert abs(binned_v - total_v) <= max(1e-9, 1e-9 * total_v), (
        f"volume_profile_levels: bin volumes ({binned_v}) do not conserve the "
        f"reference TickVolume total ({total_v})")
    poc_bin = int(np.argmax(bin_vol))            # first max -> lowest price (tie)
    lo_b, hi_b = _grow_value_area(bin_vol, poc_bin, value_area)
    return VPLevels(
        defined=True,
        poc=lo + (poc_bin + 0.5) * bin_width,
        val=lo + lo_b * bin_width,               # low edge of lowest VA bin
        vah=lo + (hi_b + 1) * bin_width,         # high edge of highest VA bin
        n_bins=n_bins, total_volume=total_v,
    )


def _accumulate_bin_volume(
    low: np.ndarray, high: np.ndarray, volume: np.ndarray,
    lo: float, bin_width: float, n_bins: int,
) -> np.ndarray:
    """Distribute each bar's volume uniformly over ``[Low, High]`` into bins."""
    edges = lo + np.arange(n_bins + 1, dtype=np.float64) * bin_width
    left_edges, right_edges = edges[:-1], edges[1:]
    bin_vol = np.zeros(n_bins, dtype=np.float64)
    for i in range(int(low.shape[0])):
        v = float(volume[i])
        if v == 0.0:
            continue
        lo_i, hi_i = float(low[i]), float(high[i])
        if hi_i <= lo_i:                          # degenerate bar -> single bin
            b = min(n_bins - 1, max(0, int((lo_i - lo) / bin_width)))
            bin_vol[b] += v
            continue
        overlap = np.clip(np.minimum(hi_i, right_edges) - np.maximum(lo_i, left_edges),
                          0.0, None)
        bin_vol += v * overlap / (hi_i - lo_i)
    return bin_vol


def _grow_value_area(
    bin_vol: np.ndarray, poc_bin: int, value_area: float,
) -> tuple[int, int]:
    """Grow the contiguous value area outward from the POC (upper-first ties)."""
    n_bins = int(bin_vol.shape[0])
    lo_b = hi_b = poc_bin
    cum = float(bin_vol[poc_bin])
    target = value_area * float(bin_vol.sum())
    while cum < target and (lo_b > 0 or hi_b < n_bins - 1):
        up_v = float(bin_vol[hi_b + 1]) if hi_b < n_bins - 1 else -np.inf
        dn_v = float(bin_vol[lo_b - 1]) if lo_b > 0 else -np.inf
        if up_v >= dn_v:                          # tie -> annex the upper bin first
            hi_b += 1
            cum += up_v
        else:
            lo_b -= 1
            cum += dn_v
    return lo_b, hi_b


# --------------------------------------------------------------------------- #
# Pure computation — paired median contrast moving-block bootstrap
# --------------------------------------------------------------------------- #
def paired_median_contrast_ci(
    variant_values: np.ndarray, bench_values: np.ndarray,
    rng: np.random.Generator, n_boot: int = N_BOOT, batch: int = BOOT_BATCH,
) -> tuple[float, float, float, int]:
    """Paired moving-block bootstrap CI of ``median(variant) - median(bench)``.

    Both arrays are the variant and benchmark realised returns on the **common
    qualifying-event subset**, in entry-time order (equal length ``m``). Each
    resample draws **one** set of block start indices and applies it to **both**
    series, so the shared event/regime noise cancels (the correct, tighter paired
    difference CI rather than the independence-assuming
    :func:`xen.expectancy.contrast_ci`). Block construction matches
    :func:`xen.expectancy.bootstrap_median_distribution` exactly.

    Returns ``(ci_low_1s, ci_lo_2s, ci_hi_2s, block_len)`` — ``ci_low_1s`` is the
    one-sided 95% lower bound (5th percentile). ``NaN`` bounds when ``m == 0``.
    """
    m = int(variant_values.shape[0])
    if m == 0 or bench_values.shape[0] != m:
        return float("nan"), float("nan"), float("nan"), 1
    b = max(1, int(round(m ** (1.0 / 3.0))))
    n_blocks = int(np.ceil(m / b))
    max_start = max(0, m - b)
    offsets = np.arange(b, dtype=np.int64)
    deltas = np.empty(n_boot, dtype=np.float64)
    done = 0
    while done < n_boot:
        k = min(batch, n_boot - done)
        starts = rng.integers(0, max_start + 1, size=(k, n_blocks))
        idx = (starts[:, :, None] + offsets[None, None, :]
               ).reshape(k, n_blocks * b)[:, :m]
        deltas[done:done + k] = (np.median(variant_values[idx], axis=1)
                                 - np.median(bench_values[idx], axis=1))
        done += k
    return (float(np.percentile(deltas, 5.0)),
            float(np.percentile(deltas, 2.5)),
            float(np.percentile(deltas, 97.5)), b)
