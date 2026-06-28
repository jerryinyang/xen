"""Chapter-02 adaptive-referee branch — frozen E0 constants & primitives.

This module is the **redesign artifact** for the Phase-001 referee renew (KB L-12). It is kept
**separate** from the frozen Chapter-01 suite (`referee_calibration.py`) so that suite's artifact
hash stays stable: the renew adds, it does not mutate. Frozen primitives (split discipline, block
bootstrap, CIs, episode counts) are imported and reused unchanged.

E0 freezes two candidate-blind inputs every D-referee experiment (E1-E5) consumes
(`docs/experiments-docs/checkpoints/2026-06-27-001-referee-adaptivity-rsi2-benchmark/E0-frozen-constants.md`):

1. **17-instrument round-trip cost map** (Q6, operator-ratified 2026-06-28). Conservative,
   monotonic-by-liquidity, class-anchored to the frozen 4 (EURUSD 1.0 / XAUUSD 3.0 / USTEC 4.0 /
   BTCUSD 10.0). 1h/4h domains only (5m dropped). Never tuned on any E1-E5 / CF-MR-002 outcome.
2. **Open-to-open `<= t-1` return basis** (Q7). Replaces the frozen suite's close-to-close return
   for the adaptive path only; the frozen suite keeps close-to-close for parallel disclosure.

The adaptive gate itself (power-aware leg gating, validity-then-economics composite, return-series
statistic) is built at E3 and appended here once E0 is frozen.
"""
from __future__ import annotations

import numpy as np
import polars as pl

# --------------------------------------------------------------------------- #
# E0.2 — 17-instrument round-trip cost map (Q6). FROZEN 2026-06-28.
# Per-bar round-trip bps, domain-invariant, 1h/4h only. Operator-ratified; the
# 4 Chapter-01 anchors (EURUSD/XAUUSD/USTEC/BTCUSD) are unchanged fixed points.
# --------------------------------------------------------------------------- #
ADAPTIVE_DOMAINS: tuple[str, ...] = ("1h", "4h")

ROUND_TRIP_COST_BPS_17: dict[str, dict[str, float]] = {
    # FX majors
    "EURUSD": {"1h": 1.0, "4h": 1.0},
    "USDJPY": {"1h": 1.0, "4h": 1.0},
    "GBPUSD": {"1h": 1.2, "4h": 1.2},
    "USDCHF": {"1h": 1.5, "4h": 1.5},
    "USDCAD": {"1h": 1.5, "4h": 1.5},
    "AUDUSD": {"1h": 1.5, "4h": 1.5},
    "NZDUSD": {"1h": 2.0, "4h": 2.0},
    # FX crosses
    "EURJPY": {"1h": 2.0, "4h": 2.0},
    "AUDJPY": {"1h": 2.5, "4h": 2.5},
    "GBPJPY": {"1h": 2.5, "4h": 2.5},
    # metal
    "XAUUSD": {"1h": 3.0, "4h": 3.0},
    # indices
    "US500": {"1h": 3.0, "4h": 3.0},
    "USTEC": {"1h": 4.0, "4h": 4.0},
    "DE30": {"1h": 4.0, "4h": 4.0},
    "JP225": {"1h": 4.0, "4h": 4.0},
    "US2000": {"1h": 5.0, "4h": 5.0},
    # crypto
    "BTCUSD": {"1h": 10.0, "4h": 10.0},
}


def adaptive_cost_bps_for(instrument: str, domain: str) -> float:
    """Frozen 17-instrument per-bar round-trip cost in bps (1h/4h only).

    Parameters
    ----------
    instrument : str
        cTrader symbol; case-insensitive.
    domain : str
        ``"1h"`` or ``"4h"`` (5m is out of adaptive scope, Q6).

    Returns
    -------
    float
        Round-trip cost in bps.
    """
    try:
        return ROUND_TRIP_COST_BPS_17[instrument.upper()][domain]
    except KeyError as exc:
        raise KeyError(
            f"No adaptive round-trip cost for {instrument}/{domain} "
            f"(domains: {ADAPTIVE_DOMAINS})"
        ) from exc


# --------------------------------------------------------------------------- #
# E0.1 — Open-to-open <= t-1 return basis (Q7). FROZEN 2026-06-28.
# --------------------------------------------------------------------------- #
def next_open_to_open_returns_from_bars(bars: pl.DataFrame) -> tuple[np.ndarray, pl.DataFrame]:
    """Return open-to-open next-step log returns and their aligned rows.

    The return realised at decision bar ``t`` is ``log(Open[t+1] / Open[t])`` — the executable
    next-step move from acting at bar ``t``'s open. A position consuming this series must itself be
    conditioned only on confirmed bars ``<= t-1`` (the forming bar's OHLC is unknown at the open);
    this primitive computes the forward open-to-open return and does not enforce that conditioning.
    Mirrors ``referee_calibration.next_log_returns_from_bars`` (close-to-close) in structure so the
    split / bootstrap / CI machinery is reused unchanged.

    Parameters
    ----------
    bars : pl.DataFrame
        Domain bars carrying at least ``OpenTime, CloseTime, Open, High, Low, Close, TickVolume``.

    Returns
    -------
    tuple[np.ndarray, pl.DataFrame]
        The open-to-open next-step log returns and the aligned rows (last bar dropped — no next
        open).
    """
    ordered = bars.sort("CloseTime").select(
        ["OpenTime", "CloseTime", "Open", "High", "Low", "Close", "TickVolume"]
    )
    aligned = ordered.with_columns(
        ((pl.col("Open").shift(-1) / pl.col("Open")).log()).alias("NextOpenLogReturn")
    ).drop_nulls("NextOpenLogReturn")
    returns = np.asarray(aligned.get_column("NextOpenLogReturn"), dtype=float)
    return returns, aligned
