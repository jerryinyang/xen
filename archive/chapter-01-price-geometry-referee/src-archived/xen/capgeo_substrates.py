"""Frozen entry substrates for CF-CAPGEO-001 (Phase 018) behind a uniform interface.

Each substrate carries the **entry event only** (no exit — exits are EXP-082/083).
The three real entry detectors are the closed families' frozen finals, reused
unchanged so the substrates are the same objects those families validated:

- ``SUB-AVWAP``           : CF-AVWAP-001 final (``xen.avwap.generate_avwap_events``,
                            EXP-028/029 frozen defaults).
- ``SUB-HARAMI-*``        : the MA(20,50)-native ``/STRONG-STAT``-conditioned HA-harami
                            entry, **ported verbatim** from EXP-068 (``_ma_context`` +
                            ``harami_entry_indices`` + ``ma_segment_moves``). Both harami
                            substrates (``PARTIAL-V2A`` / ``V2A-ADVNONE``) share this one
                            entry population — they differ only by their *exit* (a later
                            benchmark arm), so the entry set is identical by construction.
- ``SUB-RANDOM``          : a fixed-seed matched-random entry, the attribution null;
                            entries land only on completed domain-bar closes.

All detection on HA candles; all gating/thresholds on real prices. Streaming/causal
semantics of the ported detectors are preserved (no vectorization of sequential logic).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl

from xen.avwap import (
    BAND_MULTIPLIER,
    FAST_MA,
    SLOW_MA,
    VOLUME_EXPONENT,
    generate_avwap_events,
)
from xen.expectancy import (
    InProgressState,
    adaptive_time_caps_by_epoch,
    live_in_progress_state,
    live_strong_stat,
)
from xen.ha_harami import detect_ha_harami
from xen.heiken_ashi_generator import generate_heiken_ashi
from xen.zigzag import wilder_atr

# --------------------------------------------------------------------------- #
# Frozen substrate constants (carried from EXP-068 / EXP-028-029; never tuned)
# --------------------------------------------------------------------------- #
ATR_PERIOD: int = 14               # P1 Wilder ATR (harami buildable gate)
MA_FAST: int = 20                  # P1 MA-segmentation substrate (native conditioning)
MA_SLOW: int = 50

SUB_AVWAP = "SUB-AVWAP"
SUB_HARAMI_PARTIAL_V2A = "SUB-HARAMI-PARTIAL-V2A"
SUB_HARAMI_V2A_ADVNONE = "SUB-HARAMI-V2A-ADVNONE"
SUB_RANDOM = "SUB-RANDOM"
HARAMI_SUBSTRATES = (SUB_HARAMI_PARTIAL_V2A, SUB_HARAMI_V2A_ADVNONE)


# --------------------------------------------------------------------------- #
# Output container
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class EntrySet:
    """One substrate's frozen entry population for one (instrument, domain) cell.

    Attributes
    ----------
    substrate, instrument, domain : str
        Cell identity.
    n_bars : int
        Domain-bar count of the fenced analysis slice (the rate denominator).
    entry_idx : np.ndarray
        Int64 domain-bar indices of the entries (ascending), one per entry event.
    entry_epoch : np.ndarray
        Int64 ``CloseTime`` epoch-seconds of the entries (ascending), aligned to
        ``entry_idx``. The operative (causal) entry timestamp.
    analysis_end_epoch : int
        Epoch-seconds of the last domain bar (the cell holdout fence).
    detail : dict
        Substrate-specific structural fields used by the invariant battery (e.g.
        AVWAP anchor/armed/trigger epochs; harami in-progress confirm epochs).
    """

    substrate: str
    instrument: str
    domain: str
    n_bars: int
    entry_idx: np.ndarray
    entry_epoch: np.ndarray
    analysis_end_epoch: int
    detail: dict


# --------------------------------------------------------------------------- #
# Ported pure helpers (verbatim from EXP-068 — do not re-derive)
# --------------------------------------------------------------------------- #
def _sma(values: np.ndarray, window: int) -> np.ndarray:
    """Trailing simple moving average; ``NaN`` until ``window`` values exist."""
    out = np.full(values.shape[0], np.nan, dtype=np.float64)
    if values.shape[0] < window:
        return out
    cs = np.cumsum(np.insert(values, 0, 0.0))
    out[window - 1:] = (cs[window:] - cs[:-window]) / window
    return out


def _map_to_grid(bar_epoch: np.ndarray, times: np.ndarray, label: str) -> np.ndarray:
    """Exact CloseTime->bar-index map (raises on any mismatch)."""
    idx = np.searchsorted(bar_epoch, times)
    if np.any(idx >= bar_epoch.shape[0]) or np.any(
        bar_epoch[np.minimum(idx, bar_epoch.shape[0] - 1)] != times
    ):
        raise ValueError(f"{label} not found on the domain-bar grid")
    return idx.astype(np.int64)


def _real_ohlc(bars: pl.DataFrame) -> dict[str, np.ndarray]:
    """Real-bar OHLC + TickVolume + CloseTime epochs (real prices only)."""
    return {
        "open": bars.get_column("Open").to_numpy().astype(np.float64),
        "high": bars.get_column("High").to_numpy().astype(np.float64),
        "low": bars.get_column("Low").to_numpy().astype(np.float64),
        "close": bars.get_column("Close").to_numpy().astype(np.float64),
        "volume": bars.get_column("TickVolume").to_numpy().astype(np.float64),
        "epoch": bars.get_column("CloseTime").dt.epoch("s").to_numpy().astype(np.int64),
    }


def _harami_entry_indices(bars: pl.DataFrame, bar_epoch: np.ndarray) -> np.ndarray:
    """Detect HA haramis and map each to its real domain-bar index (exact match)."""
    ha = generate_heiken_ashi(bars)
    haramis = detect_ha_harami(ha)
    if haramis.height == 0:
        return np.empty(0, dtype=np.int64)
    harami_epoch = haramis.get_column("HA0Time").dt.epoch("s").to_numpy().astype(np.int64)
    return _map_to_grid(bar_epoch, harami_epoch, "harami HA0Time")


def _ma_segment_moves(ohlc: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """MA(20,50)-crossover segmentation as a ZigZag-shaped confirmed-move set.

    Identical to EXP-060/060B/061/066/068 ``ma_segment_moves``.
    """
    close, epoch = ohlc["close"], ohlc["epoch"]
    n = close.shape[0]
    empty = {k: np.empty(0, dtype=t) for k, t in (
        ("confirm_epoch", np.int64), ("end_epoch", np.int64), ("end_price", np.float64),
        ("start_price", np.float64), ("direction", np.int64), ("confirm_idx", np.int64),
        ("start_idx", np.int64), ("end_idx", np.int64), ("magnitude", np.float64))}
    if n <= MA_SLOW:
        return empty
    diff = _sma(close, MA_FAST) - _sma(close, MA_SLOW)
    sign = np.sign(diff)
    defined = np.isfinite(diff) & (sign != 0.0)
    cross = np.zeros(n, dtype=bool)
    cross[1:] = defined[1:] & defined[:-1] & (sign[1:] != sign[:-1])
    cidx = np.flatnonzero(cross)
    if cidx.shape[0] < 2:
        return empty
    s, e = cidx[:-1], cidx[1:]
    return {
        "confirm_epoch": epoch[e], "end_epoch": epoch[e], "end_price": close[e],
        "start_price": close[s], "direction": sign[s].astype(np.int64),
        "confirm_idx": e.astype(np.int64), "start_idx": s.astype(np.int64),
        "end_idx": e.astype(np.int64), "magnitude": np.abs(close[e] - close[s]),
    }


# --------------------------------------------------------------------------- #
# Substrate entry generators (uniform EntrySet interface)
# --------------------------------------------------------------------------- #
def avwap_entries(bars: pl.DataFrame, *, instrument: str, domain: str) -> EntrySet:
    """SUB-AVWAP entry population: CF-AVWAP-001 final bounce entries (frozen defaults)."""
    ohlc = _real_ohlc(bars)
    n_bars = int(bars.height)
    fence = int(ohlc["epoch"][-1]) if n_bars else 0
    result = generate_avwap_events(
        bars, instrument=instrument, domain=domain,
        band_multiplier=BAND_MULTIPLIER, volume_exponent=VOLUME_EXPONENT,
        fast_ma=FAST_MA, slow_ma=SLOW_MA,
    )
    events = result.events
    if events.height == 0:
        return EntrySet(SUB_AVWAP, instrument, domain, n_bars,
                        np.empty(0, np.int64), np.empty(0, np.int64), fence,
                        {"anchor_epoch": np.empty(0, np.int64),
                         "armed_epoch": np.empty(0, np.int64)})
    trig = events.get_column("trigger_time").dt.epoch("s").to_numpy().astype(np.int64)
    anchor = events.get_column("anchor_time").dt.epoch("s").to_numpy().astype(np.int64)
    armed = events.get_column("armed_time").dt.epoch("s").to_numpy().astype(np.int64)
    order = np.argsort(trig, kind="stable")
    trig, anchor, armed = trig[order], anchor[order], armed[order]
    entry_idx = _map_to_grid(ohlc["epoch"], trig, "AVWAP trigger_time")
    return EntrySet(SUB_AVWAP, instrument, domain, n_bars, entry_idx, trig, fence,
                    {"anchor_epoch": anchor, "armed_epoch": armed})


def harami_native_entries(bars: pl.DataFrame, *, instrument: str, domain: str) -> EntrySet:
    """SUB-HARAMI-* entry population: MA(20,50)-native /STRONG-STAT-conditioned HA harami.

    Ported verbatim from EXP-068 ``_ma_context`` + ``compute_cell``: the deployable
    conditioned-entry set is ``harami_idx[buildable & retained_p75]`` where
    ``buildable = state.valid & (m_sofar>0) & finite(atr_entry) & (atr_entry>0)
    & ~bench_warmup``. Both harami substrates share this identical entry set.
    """
    ohlc = _real_ohlc(bars)
    n_bars = int(bars.height)
    fence = int(ohlc["epoch"][-1]) if n_bars else 0
    empty_detail = {"in_progress_confirm_epoch": np.empty(0, np.int64)}

    def _empty(sub: str) -> EntrySet:
        return EntrySet(sub, instrument, domain, n_bars,
                        np.empty(0, np.int64), np.empty(0, np.int64), fence, empty_detail)

    if n_bars == 0:
        return _empty(SUB_HARAMI_PARTIAL_V2A)
    atr = wilder_atr(ohlc["high"], ohlc["low"], ohlc["close"], ATR_PERIOD)
    entry_idx = _harami_entry_indices(bars, ohlc["epoch"])
    if entry_idx.shape[0] == 0:
        return _empty(SUB_HARAMI_PARTIAL_V2A)
    seg = _ma_segment_moves(ohlc)
    if seg["confirm_epoch"].shape[0] == 0:
        return _empty(SUB_HARAMI_PARTIAL_V2A)

    entry_epoch = ohlc["epoch"][entry_idx]
    entry_close = ohlc["close"][entry_idx]
    atr_entry = atr[entry_idx]
    state: InProgressState = live_in_progress_state(
        entry_epoch, entry_close, seg["confirm_epoch"], seg["end_price"],
        seg["end_epoch"], seg["direction"])
    _, bench_warmup = adaptive_time_caps_by_epoch(
        entry_epoch, seg["confirm_epoch"], seg["confirm_idx"])
    buildable = (state.valid & (state.m_sofar > 0.0) & np.isfinite(atr_entry)
                 & (atr_entry > 0.0) & ~bench_warmup)
    stat = live_strong_stat(state.k, state.m_sofar, seg["magnitude"])
    selected = buildable & stat["retained_p75"]
    sel_idx = entry_idx[selected]
    sel_epoch = entry_epoch[selected]
    # in-progress move confirm epoch at each selected entry (causality disclosure)
    confirm_at = np.where(state.valid, seg["confirm_epoch"][np.clip(state.k, 0, None)], -1)
    detail = {"in_progress_confirm_epoch": confirm_at[selected].astype(np.int64)}
    return EntrySet(SUB_HARAMI_PARTIAL_V2A, instrument, domain, n_bars,
                    sel_idx.astype(np.int64), sel_epoch.astype(np.int64), fence, detail)


def random_entries(
    bars: pl.DataFrame, *, instrument: str, domain: str, n_target: int,
    rng: np.random.Generator,
) -> EntrySet:
    """SUB-RANDOM matched-control entries: ``n_target`` distinct completed-bar closes.

    Sampled without replacement from the domain-bar indices (entries land only on
    real closes -> look-ahead-safe by construction), then sorted ascending. Fully
    determined by ``rng`` (seed fixed by the caller).
    """
    ohlc = _real_ohlc(bars)
    n_bars = int(bars.height)
    fence = int(ohlc["epoch"][-1]) if n_bars else 0
    k = int(min(max(0, n_target), n_bars))
    if k == 0:
        return EntrySet(SUB_RANDOM, instrument, domain, n_bars,
                        np.empty(0, np.int64), np.empty(0, np.int64), fence,
                        {"n_target": int(n_target)})
    idx = np.sort(rng.choice(n_bars, size=k, replace=False)).astype(np.int64)
    return EntrySet(SUB_RANDOM, instrument, domain, n_bars, idx,
                    ohlc["epoch"][idx].astype(np.int64), fence, {"n_target": int(n_target)})
