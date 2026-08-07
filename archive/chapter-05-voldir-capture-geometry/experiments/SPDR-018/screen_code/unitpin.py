"""Unit pin (design §4.3) — the sigma-hat divisor, MEASURED AT RUN, never asserted.

    sigma_t = LTF H1 Parkinson EWMA(lambda=0.94), 60 H1-bar warm-up, causal <= t-1, in bps.

This is byte-for-byte SPDR-014's Z-VOL width object: the Parkinson and EWMA functions are
imported from SPDR-014's own ``indicators`` module, so there is exactly one definition of the
divisor across all four arms (L-21 / P-15: a divisor asserted from memory inflated EXP-025 4.1x).

The measured TRAIN medians land in ``results/unit_pin.json``. sigma-normalisation exists ONLY to
buy power for pooling; bps stays the primary reporting unit everywhere, and a sigma-unit effect is
never compared to the cost floor.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import parents
from config import (
    CONFIRM_END,
    DESIGN_START,
    EWMA_LAMBDA,
    NS,
    RESULTS_DIR,
    SIGMA_CLOCK,
    SIGMA_WARMUP_BARS,
    UNIT_PIN,
)


def _p14():
    """SPDR-014's own indicator + catalog modules (the divisor's single definition)."""
    m = parents.load("SPDR-014")
    return m["indicators"], m["catalog_io"]


def sigma_bps_series(high: np.ndarray, low: np.ndarray) -> np.ndarray:
    """Causal sigma_t in bps, lagged to ``t-1``, with the first 60 bars withheld as warm-up.

    ``ewma_park`` is a causal EWMA that already includes bar ``t``; the decision bar must not be
    read, so the emitted series is shifted by one bar. Entries ``[0, 60)`` are NaN (warm-up).
    """
    ind, _ = _p14()
    park = ind.parkinson(np.asarray(high, dtype=float), np.asarray(low, dtype=float))
    ewma = ind.ewma_park(park, EWMA_LAMBDA)
    sig = np.full(ewma.size, np.nan)
    sig[1:] = ewma[:-1] * 1e4            # causal <= t-1, dimensionless -> bps
    sig[:SIGMA_WARMUP_BARS] = np.nan     # 60 H1-bar warm-up
    return sig


def horizon_scaled(sigma_bps: np.ndarray | float, h: int) -> np.ndarray | float:
    """sigma_t * sqrt(h) — the horizon-scaled divisor (design §4.3)."""
    return np.asarray(sigma_bps, dtype=float) * np.sqrt(float(h))


def measure(symbols: list[str], *, manifest=None) -> dict:
    """TRAIN-median sigma per symbol and pooled. Computed from the catalog, never recalled."""
    ind, cat = _p14()
    per_symbol: dict[str, dict] = {}
    all_vals: list[np.ndarray] = []
    missing: list[str] = []

    for sym in symbols:
        minutes = cat.load_minute_bars(sym, DESIGN_START, CONFIRM_END, band="TRAIN",
                                       manifest=manifest)
        if minutes.height == 0:
            missing.append(sym)
            per_symbol[sym] = {"n": 0, "median_sigma_bps": None,
                               "note": "no fenced TRAIN bars in catalog"}
            continue
        bars = cat.aggregate_clock(minutes, SIGMA_CLOCK)
        if bars.height == 0:
            missing.append(sym)
            per_symbol[sym] = {"n": 0, "median_sigma_bps": None, "note": "no complete H1 bars"}
            continue
        sig = sigma_bps_series(bars["high"].to_numpy(), bars["low"].to_numpy())
        ts = bars["slot_end"].to_numpy().astype(np.int64)
        ok = np.isfinite(sig) & (sig > 0)
        # fence assertion: nothing at or beyond train_end contributes
        assert ts[ok].max(initial=0) <= int(CONFIRM_END.timestamp() * NS), "unit pin crossed fence"
        vals = sig[ok]
        if vals.size == 0:
            missing.append(sym)
            per_symbol[sym] = {"n": 0, "median_sigma_bps": None, "note": "warm-up empty"}
            continue
        all_vals.append(vals)
        per_symbol[sym] = {
            "n": int(vals.size),
            "median_sigma_bps": float(np.median(vals)),
            "p25_sigma_bps": float(np.percentile(vals, 25)),
            "p75_sigma_bps": float(np.percentile(vals, 75)),
        }

    pooled = np.concatenate(all_vals) if all_vals else np.array([])
    return {
        "divisor_object": UNIT_PIN["divisor_object"],
        "unit_pin_spec": UNIT_PIN,
        "provenance": "COMPUTED AT RUN from data/catalog (never recalled, never asserted)",
        "band": "TRAIN [2021-06-29T06:53Z, 2023-12-18T00:00Z)",
        "n_symbols_requested": len(symbols),
        "n_symbols_measured": len(symbols) - len(missing),
        "symbols_without_a_value": missing,
        "coverage_gap_statement": (
            "all requested symbols carry a measured sigma"
            if not missing else
            f"{len(missing)} symbol(s) carry no measured sigma: {missing}"
        ),
        "per_symbol": per_symbol,
        "pooled_median_sigma_bps": float(np.median(pooled)) if pooled.size else None,
        "pooled_n": int(pooled.size),
        "reporting_rule": (
            "bps is primary. sigma-normalisation buys power for pooling only; it is never a "
            "headline in sigma units and never compared to the cost floor (P-15 / L-21)."
        ),
    }


def write(payload: dict, path: Path | None = None) -> Path:
    out = path or (RESULTS_DIR / "unit_pin.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return out
