"""Cross-sectional relative-strength conditioning primitives (Phase 019 Screen X; EXP-087).

The single new module for EXP-087. It supplies the **information axis** the programme has never
varied: conditioning sourced from the *relationship between instruments* rather than single-series
price geometry. Two frozen primitives (D0-amendment-002), both directional by construction, both at a
20-domain-bar lookback, both tails:

- ``COND-XSRANK`` — at each domain timestamp, rank every instrument's trailing 20-bar real-price log
  return across the synchronized cross-section; an instrument fires **LONG** in the top decile (relative
  strength), **SHORT** in the bottom decile (relative weakness).
- ``COND-XSDIV``  — the same trailing 20-bar return **minus the equal-weight basket mean**; fire
  LONG/SHORT on the top/bottom decile of the divergence distribution.

Synchronization (frozen): the cross-section is built on a **forward-filled union timestamp grid** per
domain — each instrument contributes its **last completed bar** (strictly causal backward fill, never a
future bar) at every union timestamp. A grid timestamp with fewer than ``MIN_XS_INSTR`` synchronized
instruments cannot define a decile and is excluded (disclosed, never forced). An instrument fires an
event **only at its own completed-bar closes** (grid timestamps that coincide with one of its bar
closes), so every entry maps to a real domain-bar index on that instrument's own timeline — alignment
is by ``CloseTime``, never by bar index.

Causality: the trailing return, the rank, and the divergence at ``t`` use only bars completed strictly
``<= t``; the forward fill is backward-only. No synthetic (HA/Renko) price ever enters — every figure is
on real domain OHLC ``Close``.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
import polars as pl

# --------------------------------------------------------------------------- #
# Frozen primitive constants (D0-amendment-002; never tuned)
# --------------------------------------------------------------------------- #
COND_XSRANK: str = "COND-XSRANK"     # cross-sectional 20-bar-return rank, top/bottom decile LONG/SHORT
COND_XSDIV: str = "COND-XSDIV"       # 20-bar return minus equal-weight basket mean, top/bottom decile
PRIMITIVES: tuple[str, str] = (COND_XSRANK, COND_XSDIV)

LOOKBACK: int = 20                   # trailing return lookback in domain bars
DECILE_Q: float = 0.10               # bottom/top decile cutoff (both tails)
MIN_XS_INSTR: int = 8                # min synchronized instruments to define a decile (half universe)


# --------------------------------------------------------------------------- #
# Output container (EXP-080 EntrySet-compatible: entry_idx + entry_epoch + direction)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class XSEntrySet:
    """One cross-sectional primitive's directional entry population for one (instrument, domain) cell.

    Attributes
    ----------
    instrument, domain, primitive : str
        Cell + primitive identity.
    entry_idx : np.ndarray
        Int64 domain-bar indices of the entries (ascending), one per fired event, on the
        instrument's **own** domain-bar timeline.
    entry_epoch : np.ndarray
        Int64 ``CloseTime`` epoch-seconds of the entries (ascending), aligned to ``entry_idx``.
    direction : np.ndarray
        Int64 ``+1`` (LONG, top decile) / ``-1`` (SHORT, bottom decile), aligned to ``entry_idx``.
    n_grid : int
        Union-grid timestamp count for this domain (disclosure; identical across the domain's cells).
    n_grid_excluded : int
        Grid timestamps excluded for ``< MIN_XS_INSTR`` synchronized instruments (disclosure).
    """

    instrument: str
    domain: str
    primitive: str
    entry_idx: np.ndarray
    entry_epoch: np.ndarray
    direction: np.ndarray
    n_grid: int
    n_grid_excluded: int


# --------------------------------------------------------------------------- #
# Pure computation — trailing return + causal forward-filled union grid
# --------------------------------------------------------------------------- #
def trailing_logret(close: np.ndarray, lookback: int = LOOKBACK) -> np.ndarray:
    """Trailing ``lookback``-bar real-price log return; ``NaN`` until ``lookback`` bars exist.

    ``r[t] = log(close[t]) - log(close[t - lookback])`` — causal (uses only bars completed ``<= t``).
    Non-positive prices yield ``NaN`` (never an invalid log).

    Parameters
    ----------
    close : np.ndarray
        Real domain-bar close prices (float64), length ``n``.
    lookback : int
        Trailing window in bars.

    Returns
    -------
    np.ndarray
        Length-``n`` trailing log return with the first ``lookback`` entries ``NaN``.
    """
    x = np.asarray(close, dtype=np.float64)
    n = x.shape[0]
    out = np.full(n, np.nan, dtype=np.float64)
    if n <= lookback:
        return out
    with np.errstate(invalid="ignore", divide="ignore"):
        logp = np.where(x > 0.0, np.log(x), np.nan)
    out[lookback:] = logp[lookback:] - logp[:-lookback]
    return out


def _build_grid(epochs: dict[str, np.ndarray], rets: dict[str, np.ndarray],
                instruments: list[str]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Forward-filled union grid: per-instrument trailing return + own-bar index at each grid timestamp.

    Returns ``(grid, ret_grid, own_idx)`` where ``grid`` is the sorted unique union of all instruments'
    ``CloseTime`` epochs, ``ret_grid[g, k]`` is instrument ``k``'s last-completed-bar trailing return at
    grid timestamp ``g`` (``NaN`` before its first bar / before warmup), and ``own_idx[g, k]`` is that
    instrument's own bar index when the grid timestamp coincides with one of its bar closes (else ``-1``).
    The fill is strictly backward (causal): ``searchsorted(..., side='right') - 1``.
    """
    grid = np.unique(np.concatenate([epochs[i] for i in instruments])) if instruments else \
        np.empty(0, dtype=np.int64)
    g, k = grid.shape[0], len(instruments)
    ret_grid = np.full((g, k), np.nan, dtype=np.float64)
    own_idx = np.full((g, k), -1, dtype=np.int64)
    for col, inst in enumerate(instruments):
        ep = epochs[inst]
        if ep.shape[0] == 0:
            continue
        pos = np.searchsorted(ep, grid, side="right") - 1     # last bar with epoch <= grid (causal)
        valid = pos >= 0
        posc = np.clip(pos, 0, None)
        ret_grid[valid, col] = rets[inst][posc[valid]]
        exact = valid & (ep[posc] == grid)                    # grid timestamp == own bar close
        own_idx[exact, col] = posc[exact]
    return grid, ret_grid, own_idx


def _decile_membership(ret_grid: np.ndarray, ok: np.ndarray, primitive: str
                       ) -> tuple[np.ndarray, np.ndarray]:
    """Top/bottom-decile boolean masks ``(top, bot)`` over the cross-section for one primitive.

    ``COND-XSRANK`` deciles on the raw trailing return; ``COND-XSDIV`` on the return minus the
    equal-weight basket mean. Inclusive boundaries (``>=`` top, ``<=`` bottom) on the realized
    cross-sectional distribution at each timestamp; only rows with ``>= MIN_XS_INSTR`` present
    instruments (``ok``) can fire. Degenerate all-equal rows where a column is simultaneously top and
    bottom are resolved to no-fire (excluded), deterministically.
    """
    finite = np.isfinite(ret_grid)
    if primitive == COND_XSDIV:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            basket = np.nanmean(ret_grid, axis=1)
        values = ret_grid - basket[:, None]
    else:
        values = ret_grid
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        q_hi = np.nanquantile(values, 1.0 - DECILE_Q, axis=1)
        q_lo = np.nanquantile(values, DECILE_Q, axis=1)
    gate = finite & ok[:, None]
    top = gate & (values >= q_hi[:, None])
    bot = gate & (values <= q_lo[:, None])
    ambiguous = top & bot                                      # all-equal degenerate row -> no fire
    top = top & ~ambiguous
    bot = bot & ~ambiguous
    return top, bot


# --------------------------------------------------------------------------- #
# Orchestration-facing builder (one domain, all instruments, both primitives)
# --------------------------------------------------------------------------- #
def build_cross_section(domain_bars: dict[str, pl.DataFrame], domain: str, *,
                        lookback: int = LOOKBACK, min_xs_instr: int = MIN_XS_INSTR
                        ) -> dict[tuple[str, str], XSEntrySet]:
    """Cross-sectional directional entry sets for one domain, both primitives, all instruments.

    Parameters
    ----------
    domain_bars : dict[str, pl.DataFrame]
        ``{instrument: TRAIN domain bars}`` for one domain. Each frame must carry ``CloseTime`` and
        ``Close`` and be ``CloseTime``-sorted (asserted).
    domain : str
        Domain label (e.g. ``"15m"``), recorded on each returned set.
    lookback : int
        Trailing-return lookback in bars (frozen 20).
    min_xs_instr : int
        Minimum synchronized instruments to define a decile (frozen 8).

    Returns
    -------
    dict[tuple[str, str], XSEntrySet]
        Keyed by ``(instrument, primitive)``. Entries are on each instrument's own domain-bar timeline,
        ascending, with the cross-sectional decile sign as direction.
    """
    instruments = sorted(domain_bars)
    epochs: dict[str, np.ndarray] = {}
    rets: dict[str, np.ndarray] = {}
    for inst in instruments:
        bars = domain_bars[inst]
        ct = bars.get_column("CloseTime")
        if not ct.is_sorted():
            raise ValueError(f"{inst}-{domain}: domain bars not CloseTime-sorted")
        epochs[inst] = ct.dt.epoch("s").to_numpy().astype(np.int64)
        rets[inst] = trailing_logret(bars.get_column("Close").to_numpy().astype(np.float64), lookback)

    grid, ret_grid, own_idx = _build_grid(epochs, rets, instruments)
    n_present = np.isfinite(ret_grid).sum(axis=1)
    ok = n_present >= min_xs_instr
    n_grid = int(grid.shape[0])
    n_grid_excluded = int(np.count_nonzero(~ok))
    own = own_idx >= 0

    out: dict[tuple[str, str], XSEntrySet] = {}
    for primitive in PRIMITIVES:
        top, bot = _decile_membership(ret_grid, ok, primitive)
        fire_top = top & own
        fire_bot = bot & own
        for col, inst in enumerate(instruments):
            ft = fire_top[:, col]
            fb = fire_bot[:, col]
            rows = np.flatnonzero(ft | fb)
            entry_idx = own_idx[rows, col].astype(np.int64)
            direction = np.where(ft[rows], 1, -1).astype(np.int64)
            entry_epoch = grid[rows].astype(np.int64)
            out[(inst, primitive)] = XSEntrySet(
                instrument=inst, domain=domain, primitive=primitive,
                entry_idx=entry_idx, entry_epoch=entry_epoch, direction=direction,
                n_grid=n_grid, n_grid_excluded=n_grid_excluded)
    return out
