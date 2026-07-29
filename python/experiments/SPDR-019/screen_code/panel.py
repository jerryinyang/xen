"""Per-symbol decision-clock panels: OHLC, ATR20, ŝ (H1), deciles, held-forward labels."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import polars as pl

from catalog_io import aggregate_clock, load_train_minutes, minutes_to_arrays
from config import (
    CLOCKS,
    DECILE_WARMUP_SHAT,
    DESIGN_END_NS,
    DESIGN_START_NS,
    NS,
    SHAT_CLOCK,
    SIGMA_WARMUP_BARS,
    TRAIN_END_NS,
)
from indicators import (
    abs_oo_bps,
    ewma_park,
    expanding_decile_edges,
    freeze_zvol_scale,
    parkinson,
    train_median_finite,
    wilder_atr,
)


@dataclass
class SymbolPanel:
    symbol: str
    clock: str
    slot_start: np.ndarray
    slot_end: np.ndarray
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    atr20: np.ndarray  # Wilder ATR at bar close [0]; decision uses atr at [0]
    s_hat_bps: np.ndarray  # H1 Parkinson-EWMA ŝ in bps, held forward to this clock
    s_hat_decile: np.ndarray  # expanding per-symbol decile of H1 ŝ history before bar
    s_hat_rank: np.ndarray  # expanding rank in [0,1]
    s_hat_uncond: float  # TRAIN-median ŝ per symbol (L4 unmodulated)
    abs_r_decision_bps: np.ndarray  # |decision-bar move| for M-3: |close[0]-close[1]|/… in bps-ish
    abs_r_decile: np.ndarray  # §4.1b M-3 DECILES: per-symbol expanding causal decile of the above
    m1: dict[str, np.ndarray] = field(repr=False)
    # parent gates held forward (H1 source)
    s_hmm_rv: np.ndarray = field(default_factory=lambda: np.empty(0))
    p_rmarkov_k4: np.ndarray = field(default_factory=lambda: np.empty(0))
    p_rmarkov_k12: np.ndarray = field(default_factory=lambda: np.empty(0))
    tgtcur_fires: np.ndarray = field(default_factory=lambda: np.empty(0))
    tgtmed5_fires: np.ndarray = field(default_factory=lambda: np.empty(0))
    p_stay: np.ndarray = field(default_factory=lambda: np.empty(0))  # for MOD hold
    n_prior_trans: np.ndarray = field(default_factory=lambda: np.empty(0))


def _complete_bars(minutes: pl.DataFrame, clock: str) -> pl.DataFrame:
    agg = aggregate_clock(minutes, clock)
    return agg.filter(pl.col("complete")).sort("slot_start")


def _hold_forward(
    src_end: np.ndarray,
    src_val: np.ndarray,
    dst_end: np.ndarray,
) -> np.ndarray:
    """Hold source values forward to each destination slot_end (no backfill).

    For each dst bar, take the latest src with src_end <= dst_end and finite value.
    """
    out = np.full(dst_end.size, np.nan)
    if src_end.size == 0:
        return out
    # the single-pointer walk below is only correct on an ascending source; a parent artifact
    # stored in another order would silently hold forward the wrong value (QA run 8, R8-21)
    if src_end.size > 1 and not np.all(np.diff(src_end) >= 0):
        raise AssertionError("_hold_forward requires src_end sorted ascending")
    j = 0
    last = np.nan
    n_src = src_end.size
    for i, t in enumerate(dst_end):
        while j < n_src and src_end[j] <= t:
            if np.isfinite(src_val[j]):
                last = float(src_val[j])
            j += 1
        out[i] = last
    return out


def build_shat_h1(minutes: pl.DataFrame) -> dict:
    """H1 ŝ series (bps) + expanding deciles. Shared across decision clocks."""
    bars = _complete_bars(minutes, SHAT_CLOCK)
    if bars.height < SIGMA_WARMUP_BARS + 10:
        return {"empty": True}
    slot_start = bars["slot_start"].to_numpy().astype(np.int64)
    slot_end = bars["slot_end"].to_numpy().astype(np.int64)
    o = bars["open"].to_numpy().astype(float)
    h = bars["high"].to_numpy().astype(float)
    lo = bars["low"].to_numpy().astype(float)
    c = bars["close"].to_numpy().astype(float)

    park = parkinson(h, lo)
    ewma = ewma_park(park)
    abs_oo = abs_oo_bps(o)
    design_mask = (slot_start >= DESIGN_START_NS) & (slot_start < DESIGN_END_NS)
    s_sym = freeze_zvol_scale(ewma, abs_oo, design_mask, SIGMA_WARMUP_BARS)
    if not np.isfinite(s_sym):
        # fallback: full TRAIN early bars
        train_mask = (slot_start >= DESIGN_START_NS) & (slot_start < TRAIN_END_NS)
        s_sym = freeze_zvol_scale(ewma, abs_oo, train_mask, SIGMA_WARMUP_BARS)
    s_hat = np.where(np.isfinite(ewma), s_sym * ewma, np.nan)
    # causal: ŝ at [0] is known at close of [0]; for exit widths we use ŝ at decision bar
    # warm-up: first 60 H1 bars of finite ewma are warm-up (§7)
    finite_idx = np.where(np.isfinite(s_hat))[0]
    if finite_idx.size > SIGMA_WARMUP_BARS:
        s_hat[: finite_idx[SIGMA_WARMUP_BARS - 1] + 1] = np.nan  # force warm-up gap

    decile, rank = expanding_decile_edges(s_hat, min_hist=DECILE_WARMUP_SHAT)
    train_mask = (slot_end < TRAIN_END_NS) & np.isfinite(s_hat)
    s_uncond = train_median_finite(s_hat, train_mask)
    return {
        "empty": False,
        "slot_end": slot_end,
        "slot_start": slot_start,
        "s_hat": s_hat,
        "decile": decile,
        "rank": rank,
        "s_hat_uncond": s_uncond,
        "s_symbol_scale": float(s_sym) if np.isfinite(s_sym) else float("nan"),
        "open": o, "high": h, "low": lo, "close": c,
        "atr20": wilder_atr(h, lo, c),
    }


def build_decision_panel(
    symbol: str,
    clock: str,
    minutes: pl.DataFrame,
    shat: dict,
    m1: dict[str, np.ndarray],
) -> SymbolPanel | None:
    bars = _complete_bars(minutes, clock)
    if bars.height < 30:
        return None
    slot_start = bars["slot_start"].to_numpy().astype(np.int64)
    slot_end = bars["slot_end"].to_numpy().astype(np.int64)
    o = bars["open"].to_numpy().astype(float)
    h = bars["high"].to_numpy().astype(float)
    lo = bars["low"].to_numpy().astype(float)
    c = bars["close"].to_numpy().astype(float)

    if clock == SHAT_CLOCK:
        atr = shat["atr20"]
        s_hat = shat["s_hat"]
        dec = shat["decile"]
        rank = shat["rank"]
        # align if needed (should be identical complete bars)
        if s_hat.size != c.size:
            s_hat = _hold_forward(shat["slot_end"], shat["s_hat"], slot_end)
            dec = _hold_forward(shat["slot_end"], shat["decile"], slot_end)
            rank = _hold_forward(shat["slot_end"], shat["rank"], slot_end)
            atr = wilder_atr(h, lo, c)
    else:
        atr = wilder_atr(h, lo, c)
        s_hat = _hold_forward(shat["slot_end"], shat["s_hat"], slot_end)
        dec = _hold_forward(shat["slot_end"], shat["decile"], slot_end)
        rank = _hold_forward(shat["slot_end"], shat["rank"], slot_end)

    # |decision-bar move| in bps of close-to-close on decision clock (for M-3 matching)
    abs_r = np.full(c.size, np.nan)
    with np.errstate(divide="ignore", invalid="ignore"):
        abs_r[1:] = 1e4 * np.abs(c[1:] / c[:-1] - 1.0)
    # §4.1b M-3 DECILES: "the SAME rule - per symbol, expanding, causal", same 250-bar warm-up.
    # The comparator must match on |decision-bar move|, never on the layer's own selection
    # variable (QA run 8, R8-14).
    abs_r_dec, _ = expanding_decile_edges(abs_r, min_hist=DECILE_WARMUP_SHAT)

    return SymbolPanel(
        symbol=symbol,
        clock=clock,
        slot_start=slot_start,
        slot_end=slot_end,
        open=o, high=h, low=lo, close=c,
        atr20=atr,
        s_hat_bps=s_hat,
        s_hat_decile=dec,
        s_hat_rank=rank,
        s_hat_uncond=float(shat["s_hat_uncond"]),
        abs_r_decision_bps=abs_r,
        abs_r_decile=abs_r_dec,
        m1=m1,
    )


def load_symbol_bundle(symbol: str, *, manifest=None) -> dict | None:
    """Load M1 once; build H1 ŝ + M15/H1 decision panels."""
    minutes = load_train_minutes(symbol, manifest=manifest)
    if minutes.height == 0:
        return None
    m1 = minutes_to_arrays(minutes)
    shat = build_shat_h1(minutes)
    if shat.get("empty"):
        return None
    panels = {}
    for clock in CLOCKS:
        p = build_decision_panel(symbol, clock, minutes, shat, m1)
        if p is not None:
            panels[clock] = p
    if not panels:
        return None
    return {
        "symbol": symbol,
        "minutes": minutes,
        "m1": m1,
        "shat": shat,
        "panels": panels,
        "atr20_median_h1": train_median_finite(shat["atr20"]),
        "s_hat_uncond": shat["s_hat_uncond"],
        "s_symbol_scale": shat["s_symbol_scale"],
    }
