"""Anchored VWAP (AVWAP) event-substrate generator for CF-AVWAP-001 (Phase 004).

This module implements the *frozen first-branch* AVWAP definition registered in
``docs/signal-registry/candidate-families/avwap.md`` and scoped for EXP-020:

- regime detector: simple MA crossover, fast 20 / slow 50, on domain ``Close``;
- anchor rule: on a confirmed regime change, anchor a bullish regime to the
  lowest ``Low`` of the just-ended segment and a bearish regime to the highest
  ``High`` (the viable pivots tracked from completed bars only);
- AVWAP source: typical price ``(High + Low + Close) / 3``;
- AVWAP weight: ``TickVolume ** 0.75``;
- band spread: median absolute deviation of typical price from the anchored
  AVWAP path since the active anchor, multiplier ``1.0``;
- bounce event: a confirmed close crosses the AVWAP in the regime direction
  after first moving to the opposite side (arm then trigger; re-arm required
  before the next trigger).

The generator is a deterministic, **streaming-safe** sequential state machine:
every state update uses only the current and prior completed domain bars, so it
never reads future information. Given identical input and parameters it produces
identical output (no randomness). Holdout exclusion is the caller's
responsibility — this module operates on whatever (already-sliced) frame it is
given.
"""
from __future__ import annotations

import heapq
import math
from dataclasses import dataclass

import numpy as np
import polars as pl


# --------------------------------------------------------------------------- #
# Frozen first-branch parameters (registry CF-AVWAP-001 baseline)
# --------------------------------------------------------------------------- #
FAST_MA = 20
SLOW_MA = 50
VOLUME_EXPONENT = 0.75
BAND_MULTIPLIER = 1.0

REQUIRED_COLUMNS: tuple[str, ...] = (
    "CloseTime",
    "Open",
    "High",
    "Low",
    "Close",
    "TickVolume",
)

# Output schemas (explicit so empty cells still produce well-typed frames).
EVENT_SCHEMA: dict[str, pl.DataType] = {
    "instrument": pl.Utf8,
    "domain": pl.Utf8,
    "regime_id": pl.Int64,
    "direction": pl.Int64,
    "bounce_index_in_regime": pl.Int64,
    "is_pyramid_bounce": pl.Boolean,
    "anchor_idx": pl.Int64,
    "anchor_time": pl.Datetime("us"),
    "anchor_price": pl.Float64,
    "armed_time": pl.Datetime("us"),
    "trigger_idx": pl.Int64,
    "trigger_time": pl.Datetime("us"),
    "trigger_close": pl.Float64,
    "avwap_at_trigger": pl.Float64,
    "band_spread_at_trigger": pl.Float64,
    "upper_band_at_trigger": pl.Float64,
    "lower_band_at_trigger": pl.Float64,
    "favorable_target_at_trigger": pl.Float64,
    "adverse_target_at_trigger": pl.Float64,
    "anchor_age_bars": pl.Int64,
}

REGIME_SCHEMA: dict[str, pl.DataType] = {
    "instrument": pl.Utf8,
    "domain": pl.Utf8,
    "regime_id": pl.Int64,
    "direction": pl.Int64,
    "confirm_idx": pl.Int64,
    "confirm_time": pl.Datetime("us"),
    "regime_start_idx": pl.Int64,
    "regime_end_idx": pl.Int64,
    "regime_length_bars": pl.Int64,
    "anchor_idx": pl.Int64,
    "anchor_time": pl.Datetime("us"),
    "anchor_price": pl.Float64,
    "anchor_age_at_confirm": pl.Int64,
    "num_bounces": pl.Int64,
}


# --------------------------------------------------------------------------- #
# Result container
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class AvwapResult:
    """Per-cell AVWAP generation output.

    Attributes
    ----------
    instrument, domain : str
        Cell identity.
    n_domain_bars : int
        Number of domain bars processed.
    analysis_end : str
        ISO string of the last domain-bar ``CloseTime`` (the cell's holdout
        fence; every event must satisfy ``trigger_time <= analysis_end``).
    events : pl.DataFrame
        One row per confirmed bounce event (``EVENT_SCHEMA``).
    regimes : pl.DataFrame
        One row per confirmed active regime (``REGIME_SCHEMA``).
    """

    instrument: str
    domain: str
    n_domain_bars: int
    analysis_end: str
    events: pl.DataFrame
    regimes: pl.DataFrame


# --------------------------------------------------------------------------- #
# Small numeric helpers (pure)
# --------------------------------------------------------------------------- #
class _StreamingMedian:
    """Append-only running median via two heaps.

    The median depends only on the multiset of pushed values, so it is
    deterministic regardless of insertion order. Used for the MAD band spread of
    ``|typical - avwap|`` since the active anchor; a fresh instance is created at
    every anchor reset.
    """

    def __init__(self) -> None:
        self._low: list[float] = []   # max-heap via negation (lower half)
        self._high: list[float] = []  # min-heap (upper half)

    def push(self, value: float) -> None:
        """Add ``value`` to the running multiset."""
        if not self._low or value <= -self._low[0]:
            heapq.heappush(self._low, -value)
        else:
            heapq.heappush(self._high, value)
        if len(self._low) > len(self._high) + 1:
            heapq.heappush(self._high, -heapq.heappop(self._low))
        elif len(self._high) > len(self._low):
            heapq.heappush(self._low, -heapq.heappop(self._high))

    def median(self) -> float:
        """Return the current median, or NaN when empty."""
        if not self._low:
            return math.nan
        if len(self._low) > len(self._high):
            return float(-self._low[0])
        return ((-self._low[0]) + self._high[0]) / 2.0


def _causal_sma(values: np.ndarray, window: int) -> np.ndarray:
    """Trailing simple moving average using only current and prior values.

    Parameters
    ----------
    values : np.ndarray
        1-D float array of domain closes.
    window : int
        Lookback length. Positions with fewer than ``window`` completed values
        are NaN.

    Returns
    -------
    np.ndarray
        Causal SMA with NaN warmup prefix.
    """
    n = values.size
    out = np.full(n, np.nan, dtype=float)
    if n < window:
        return out
    csum = np.cumsum(values)
    out[window - 1] = csum[window - 1] / window
    out[window:] = (csum[window:] - csum[:-window]) / window
    return out


def _regime_sign(close: np.ndarray) -> np.ndarray:
    """Causal MA(20,50) regime sign per bar: +1 bull, -1 bear, 0 warmup/tie."""
    fast = _causal_sma(close, FAST_MA)
    slow = _causal_sma(close, SLOW_MA)
    sign = np.zeros(close.size, dtype=np.int64)
    valid = ~np.isnan(fast) & ~np.isnan(slow)
    sign[valid & (fast > slow)] = 1
    sign[valid & (fast < slow)] = -1
    return sign


def _validate_domain_frame(frame: pl.DataFrame) -> None:
    """Validate the domain frame before generation; raise on contract breaches."""
    missing = [c for c in REQUIRED_COLUMNS if c not in frame.columns]
    if missing:
        raise ValueError(f"domain frame missing required columns: {missing}")
    if frame.is_empty():
        return
    if frame.get_column("TickVolume").null_count() > 0:
        raise ValueError(
            "TickVolume has null values; missing volume is an implementation "
            "error for EXP-020 (see scope Data Requirements)."
        )
    vmin = frame.get_column("TickVolume").min()
    if vmin is not None and vmin < 0:
        raise ValueError(f"TickVolume has negative values (min={vmin}).")
    if not frame.get_column("CloseTime").is_sorted():
        raise ValueError("domain frame must be sorted by CloseTime before generation.")


# --------------------------------------------------------------------------- #
# Core generator (sequential, streaming-safe, deterministic)
# --------------------------------------------------------------------------- #
def generate_avwap_events(
    frame: pl.DataFrame,
    *,
    instrument: str,
    domain: str,
) -> AvwapResult:
    """Generate AVWAP bounce events and regime diagnostics for one cell.

    The frame must be a single instrument/domain OHLCV frame, already sliced to
    the analysis set and sorted by ``CloseTime``. The function never reads beyond
    the current bar.

    Parameters
    ----------
    frame : pl.DataFrame
        Domain OHLC bars with ``CloseTime, Open, High, Low, Close, TickVolume``.
    instrument : str
        Instrument label stored on every output row.
    domain : str
        Domain label (e.g. ``5m``) stored on every output row.

    Returns
    -------
    AvwapResult
        Events table, regime table, bar count, and holdout-fence timestamp.
    """
    _validate_domain_frame(frame)
    n = frame.height
    analysis_end = "" if n == 0 else str(frame.get_column("CloseTime").max())

    if n < SLOW_MA:
        # Not enough bars to establish any regime; emit empty, well-typed tables.
        return AvwapResult(
            instrument=instrument,
            domain=domain,
            n_domain_bars=n,
            analysis_end=analysis_end,
            events=pl.DataFrame(schema=EVENT_SCHEMA),
            regimes=pl.DataFrame(schema=REGIME_SCHEMA),
        )

    high = frame.get_column("High").to_numpy().astype(float)
    low = frame.get_column("Low").to_numpy().astype(float)
    close = frame.get_column("Close").to_numpy().astype(float)
    typ = (high + low + close) / 3.0
    weight = np.power(frame.get_column("TickVolume").to_numpy().astype(float), VOLUME_EXPONENT)
    times = frame.get_column("CloseTime").to_list()
    sign = _regime_sign(close)

    events: list[dict] = []
    regimes: list[dict] = []

    active_regime = 0
    seg_min_low = math.inf
    seg_min_low_idx = -1
    seg_max_high = -math.inf
    seg_max_high_idx = -1

    anchor_active = False
    anchor_idx = -1
    anchor_price = math.nan
    regime_id = 0
    confirm_idx = -1
    bounce_count = 0
    cum_wp = 0.0
    cum_w = 0.0
    med = _StreamingMedian()
    armed = False
    armed_idx = -1

    for i in range(n):
        # Step 1: extend viable pivots with the completed bar i.
        if low[i] < seg_min_low:
            seg_min_low = low[i]
            seg_min_low_idx = i
        if high[i] > seg_max_high:
            seg_max_high = high[i]
            seg_max_high_idx = i

        s = int(sign[i])
        if s != 0 and s != active_regime:
            # Step 2: confirmed regime change (or initial establishment) at bar i.
            if anchor_active:
                regimes.append(
                    _regime_row(
                        instrument, domain, regime_id, active_regime, confirm_idx,
                        times[confirm_idx], end_idx=i - 1, anchor_idx=anchor_idx,
                        anchor_time=times[anchor_idx], anchor_price=anchor_price,
                        num_bounces=bounce_count,
                    )
                )
            if s == 1:
                anchor_idx, anchor_price = seg_min_low_idx, seg_min_low
            else:
                anchor_idx, anchor_price = seg_max_high_idx, seg_max_high
            regime_id += 1
            confirm_idx = i
            bounce_count = 0
            armed = False
            armed_idx = -1
            active_regime = s
            # Re-seed the anchored AVWAP and band window from the chosen pivot
            # through the confirmation bar (all completed; no look-ahead).
            cum_wp = 0.0
            cum_w = 0.0
            med = _StreamingMedian()
            for k in range(anchor_idx, i + 1):
                cum_wp += typ[k] * weight[k]
                cum_w += weight[k]
                if cum_w > 0.0:
                    med.push(abs(typ[k] - cum_wp / cum_w))
            anchor_active = True
            # Start the next segment's pivot window at the confirmation bar.
            seg_min_low, seg_min_low_idx = low[i], i
            seg_max_high, seg_max_high_idx = high[i], i
            # Signals derived from the new regime occur only AFTER this bar.
            continue

        if not anchor_active:
            continue

        # Step 3: advance the anchored AVWAP with the completed bar i and run the
        # arm/trigger bounce logic (i is strictly after the confirmation bar).
        cum_wp += typ[i] * weight[i]
        cum_w += weight[i]
        if cum_w <= 0.0:
            continue  # AVWAP undefined while cumulative weight is zero.
        avwap_i = cum_wp / cum_w
        med.push(abs(typ[i] - avwap_i))

        if active_regime == 1:
            if not armed:
                if close[i] < avwap_i:
                    armed, armed_idx = True, i
            elif close[i] > avwap_i:
                bounce_count += 1
                events.append(
                    _event_row(
                        instrument, domain, regime_id, active_regime, bounce_count,
                        anchor_idx, times[anchor_idx], anchor_price, times[armed_idx],
                        i, times[i], close[i], avwap_i, med.median(),
                    )
                )
                armed, armed_idx = False, -1
        else:  # active_regime == -1
            if not armed:
                if close[i] > avwap_i:
                    armed, armed_idx = True, i
            elif close[i] < avwap_i:
                bounce_count += 1
                events.append(
                    _event_row(
                        instrument, domain, regime_id, active_regime, bounce_count,
                        anchor_idx, times[anchor_idx], anchor_price, times[armed_idx],
                        i, times[i], close[i], avwap_i, med.median(),
                    )
                )
                armed, armed_idx = False, -1

    if anchor_active:
        regimes.append(
            _regime_row(
                instrument, domain, regime_id, active_regime, confirm_idx,
                times[confirm_idx], end_idx=n - 1, anchor_idx=anchor_idx,
                anchor_time=times[anchor_idx], anchor_price=anchor_price,
                num_bounces=bounce_count,
            )
        )

    return AvwapResult(
        instrument=instrument,
        domain=domain,
        n_domain_bars=n,
        analysis_end=analysis_end,
        events=_to_frame(events, EVENT_SCHEMA),
        regimes=_to_frame(regimes, REGIME_SCHEMA),
    )


def _event_row(
    instrument: str,
    domain: str,
    regime_id: int,
    direction: int,
    bounce_index: int,
    anchor_idx: int,
    anchor_time,
    anchor_price: float,
    armed_time,
    trigger_idx: int,
    trigger_time,
    trigger_close: float,
    avwap: float,
    band_spread: float,
) -> dict:
    """Build one bounce-event row with bands and frozen lifetime targets."""
    upper = avwap + BAND_MULTIPLIER * band_spread
    lower = avwap - BAND_MULTIPLIER * band_spread
    if direction == 1:
        favorable, adverse = upper, lower
    else:
        favorable, adverse = lower, upper
    return {
        "instrument": instrument,
        "domain": domain,
        "regime_id": regime_id,
        "direction": direction,
        "bounce_index_in_regime": bounce_index,
        "is_pyramid_bounce": bounce_index > 1,
        "anchor_idx": anchor_idx,
        "anchor_time": anchor_time,
        "anchor_price": float(anchor_price),
        "armed_time": armed_time,
        "trigger_idx": trigger_idx,
        "trigger_time": trigger_time,
        "trigger_close": float(trigger_close),
        "avwap_at_trigger": float(avwap),
        "band_spread_at_trigger": float(band_spread),
        "upper_band_at_trigger": float(upper),
        "lower_band_at_trigger": float(lower),
        "favorable_target_at_trigger": float(favorable),
        "adverse_target_at_trigger": float(adverse),
        "anchor_age_bars": trigger_idx - anchor_idx,
    }


def _regime_row(
    instrument: str,
    domain: str,
    regime_id: int,
    direction: int,
    confirm_idx: int,
    confirm_time,
    end_idx: int,
    anchor_idx: int,
    anchor_time,
    anchor_price: float,
    num_bounces: int,
) -> dict:
    """Build one per-regime diagnostic row."""
    return {
        "instrument": instrument,
        "domain": domain,
        "regime_id": regime_id,
        "direction": direction,
        "confirm_idx": confirm_idx,
        "confirm_time": confirm_time,
        "regime_start_idx": confirm_idx,
        "regime_end_idx": end_idx,
        "regime_length_bars": end_idx - confirm_idx + 1,
        "anchor_idx": anchor_idx,
        "anchor_time": anchor_time,
        "anchor_price": float(anchor_price),
        "anchor_age_at_confirm": confirm_idx - anchor_idx,
        "num_bounces": num_bounces,
    }


def _to_frame(rows: list[dict], schema: dict[str, pl.DataType]) -> pl.DataFrame:
    """Build a well-typed frame from rows, or an empty frame with ``schema``."""
    if not rows:
        return pl.DataFrame(schema=schema)
    return pl.DataFrame(rows, schema=schema)


# --------------------------------------------------------------------------- #
# Bounded visualization helper (recompute one small window only)
# --------------------------------------------------------------------------- #
def compute_band_trace(
    frame: pl.DataFrame,
    anchor_idx: int,
    end_idx: int,
) -> dict[str, np.ndarray]:
    """Recompute the per-bar AVWAP and MAD band over one bounded window.

    Used only for the sample-overlay plot. It mirrors the anchored AVWAP/band
    math of :func:`generate_avwap_events` for a single window ``[anchor_idx,
    end_idx]`` (callers must keep the window small and bounded). It is a
    deterministic visualization recompute, not a second state-machine pass.

    Returns
    -------
    dict[str, np.ndarray]
        Arrays ``close``, ``avwap``, ``upper``, ``lower`` and a list ``time``
        for the window, each of length ``end_idx - anchor_idx + 1``.
    """
    if not (0 <= anchor_idx <= end_idx < frame.height):
        raise ValueError("invalid window bounds for band trace")
    high = frame.get_column("High").to_numpy().astype(float)
    low = frame.get_column("Low").to_numpy().astype(float)
    close = frame.get_column("Close").to_numpy().astype(float)
    typ = (high + low + close) / 3.0
    weight = np.power(frame.get_column("TickVolume").to_numpy().astype(float), VOLUME_EXPONENT)
    times = frame.get_column("CloseTime").to_list()

    span = end_idx - anchor_idx + 1
    avwap = np.full(span, np.nan, dtype=float)
    upper = np.full(span, np.nan, dtype=float)
    lower = np.full(span, np.nan, dtype=float)
    cum_wp = 0.0
    cum_w = 0.0
    med = _StreamingMedian()
    for offset, k in enumerate(range(anchor_idx, end_idx + 1)):
        cum_wp += typ[k] * weight[k]
        cum_w += weight[k]
        if cum_w <= 0.0:
            continue
        a_k = cum_wp / cum_w
        med.push(abs(typ[k] - a_k))
        band = med.median()
        avwap[offset] = a_k
        upper[offset] = a_k + BAND_MULTIPLIER * band
        lower[offset] = a_k - BAND_MULTIPLIER * band
    return {
        "time": times[anchor_idx : end_idx + 1],
        "close": close[anchor_idx : end_idx + 1],
        "avwap": avwap,
        "upper": upper,
        "lower": lower,
    }
