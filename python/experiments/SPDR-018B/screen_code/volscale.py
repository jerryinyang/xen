"""The volatility-scale ratio between the two universes — measured, cached, never asserted.

Operator directive 2026-07-25: scale the borrowed crypto cost model by the sigma-scale difference
so the charge is equivalent in volatility units. Crypto sigma comes from SPDR-018's EMITTED
unit_pin.json; cTrader sigma from this run's. Both are measured artifacts.
"""
from __future__ import annotations

import json
from pathlib import Path

from config18b import RESULTS_DIR, SPDR018_UNIT_PIN

_CACHE: dict[str, float] = {}


def vol_scale() -> float:
    if "r" in _CACHE:
        return _CACHE["r"]
    crypto = float(json.loads(Path(SPDR018_UNIT_PIN).read_text())["pooled_median_sigma_bps"])
    ct_path = RESULTS_DIR / "unit_pin.json"
    if not ct_path.exists():
        raise RuntimeError("cTrader unit pin not yet measured — run the unit pin stage first")
    ctrader = float(json.loads(ct_path.read_text())["pooled_median_sigma_bps"])
    _CACHE["r"] = ctrader / crypto
    return _CACHE["r"]


def detail() -> dict:
    crypto = float(json.loads(Path(SPDR018_UNIT_PIN).read_text())["pooled_median_sigma_bps"])
    ctrader = float(json.loads((RESULTS_DIR / "unit_pin.json").read_text())
                    ["pooled_median_sigma_bps"])
    r = vol_scale()
    return {"crypto_pooled_sigma_bps": crypto, "ctrader_pooled_sigma_bps": ctrader,
            "ratio_ctrader_over_crypto": r,
            "unscaled_cost_floor_bps": 13.5, "vol_scaled_cost_floor_bps": 13.5 * r,
            "both_legs_emitted": ["c_net_bps (vol-scaled, headline)",
                                  "c_net_unscaled_bps (unscaled borrowed, companion)"],
            "gross_remains_primary": True}
