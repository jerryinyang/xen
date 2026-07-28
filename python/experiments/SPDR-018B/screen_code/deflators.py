"""The two deflators — derived, not asserted, and deliberately different objects.

An earlier version used ONE ratio (H1 bar volatility, 0.1786) for both cost and precision. That
was wrong for cost: cost scales with what a trade actually PAYS, not with bar noise. The analyst
measured the realised trade-payoff ratio at 0.32-0.48 against the 0.1786 used, i.e. ~2x off.

  COST target  -> payoff scale: median (W + L) per arm, cTrader / crypto.  DERIVED PER ARM.
  PRECISION    -> noise scale:  pooled sigma-hat ratio, cTrader / crypto.  (the MDE is a noise
                  quantity, so sigma is the correct deflator there)
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np, pandas as pd
from config18b import RESULTS_DIR, SPDR018_UNIT_PIN

C18 = Path(SPDR018_UNIT_PIN).parent          # SPDR-018/results
_C: dict = {}


def sigma_ratio() -> float:
    """Noise-scale deflator — for PRECISION TARGETS only."""
    if "s" in _C:
        return _C["s"]
    a = float(json.loads(Path(SPDR018_UNIT_PIN).read_text())["pooled_median_sigma_bps"])
    b = float(json.loads((RESULTS_DIR / "unit_pin.json").read_text())["pooled_median_sigma_bps"])
    _C["s"] = b / a
    return _C["s"]


def _payoff_scale(df: pd.DataFrame) -> float:
    """Median (W + L) over powered signed cells — the scale a trade actually pays out on."""
    d = df.copy()
    for c in ("W", "L", "at_parent_target_precision"):
        if c in d:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    if "at_parent_target_precision" in d:
        p = d[d.at_parent_target_precision == 1]
        if len(p) >= 30:
            d = p
    v = (d["W"] + d["L"]).dropna()
    return float(np.median(v)) if len(v) else float("nan")


def payoff_ratio_per_arm() -> dict:
    """COST deflator, DERIVED per arm (operator directive 2026-07-26)."""
    if "p" in _C:
        return _C["p"]
    out = {}
    for arm in ("B", "C"):
        ct = RESULTS_DIR / f"arm_{arm}.parquet"
        cr = C18 / f"arm_{arm}.parquet"
        if not (ct.exists() and cr.exists()):
            continue
        a = _payoff_scale(pd.read_parquet(cr))
        b = _payoff_scale(pd.read_parquet(ct))
        out[arm] = {"crypto_payoff_scale_bps": a, "ctrader_payoff_scale_bps": b,
                    "ratio": (b / a) if (np.isfinite(a) and a > 0) else float("nan")}
    vals = [v["ratio"] for v in out.values() if np.isfinite(v.get("ratio", np.nan))]
    out["_default"] = float(np.median(vals)) if vals else sigma_ratio()
    _C["p"] = out
    return out


def detail() -> dict:
    pr = payoff_ratio_per_arm()
    return {
        "cost_deflator": {"basis": "realised payoff scale, median (W+L), DERIVED PER ARM",
                          "per_arm": {k: v for k, v in pr.items() if k != "_default"},
                          "default_for_other_arms": pr["_default"],
                          "supersedes": "the 0.17855 bar-volatility ratio, which was ~2x too low"},
        "precision_deflator": {"basis": "pooled sigma-hat ratio (a NOISE quantity)",
                               "ratio": sigma_ratio(),
                               "why_different": ("cost scales with what a trade pays; the MDE "
                                                 "scales with bar noise. One ratio for both was "
                                                 "the original error.")},
    }
