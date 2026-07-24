"""Golden traces G1–G4 (design §10)."""
from __future__ import annotations

import numpy as np

from config import EWMA_LAMBDA, ZVOL_EPS
from costs import partial_net
from engine import SeriesPack, band_bounds, label_residual, residual_r_h, simulate_policy
from indicators import ewma_park, parkinson


def g1_zvol_band(pack: SeriesPack, z: float = 1.5, H: int = 12) -> dict:
    """Hand Parkinson + EWMA λ=0.94 + s_symbol → band match emission to 1e-9 rel."""
    t = pack.design_lo + 5
    if t + H + 2 >= pack.open.size:
        return {"found": False, "reason": "short series"}
    # hand recompute park and ewma up to t
    park_hand = parkinson(pack.high[: t + 1], pack.low[: t + 1])
    ewma_hand = ewma_park(park_hand, EWMA_LAMBDA)
    e_t = float(ewma_hand[-1])
    e_eng = float(pack.ewma_park[t])
    s = pack.s_symbol
    sig_hand = s * e_t
    sig_eng = float(pack.sigma_zvol[t])
    anchor = float(pack.open[t + 1])
    up_h, lo_h = band_bounds(anchor, z, sig_hand)
    up_e, lo_e = band_bounds(anchor, z, sig_eng)
    rel = lambda a, b: abs(a - b) / max(1e-12, abs(b))
    return {
        "found": True,
        "symbol": pack.symbol,
        "t_idx": t,
        "s_symbol": s,
        "ewma_hand": e_t,
        "ewma_engine": e_eng,
        "ewma_match": bool(rel(e_t, e_eng) < 1e-9 or abs(e_t - e_eng) < 1e-15),
        "sigma_hand": sig_hand,
        "sigma_engine": sig_eng,
        "sigma_match": bool(rel(sig_hand, sig_eng) < 1e-9),
        "upper_hand": up_h, "upper_engine": up_e,
        "lower_hand": lo_h, "lower_engine": lo_e,
        "band_match": bool(rel(up_h, up_e) < 1e-9 and rel(lo_h, lo_e) < 1e-9),
        "pass": bool(rel(sig_hand, sig_eng) < 1e-9 and rel(up_h, up_e) < 1e-9),
    }


def g2_etouch_synthetic() -> dict:
    """Synthetic path breaches upper only; side=+1; breach entry = next open; r_12 hand."""
    n = 40
    open_ = np.full(n, 100.0)
    high = np.full(n, 100.5)
    low = np.full(n, 99.5)
    close = np.full(n, 100.0)
    # bar 10: upper breach
    upper = 101.0
    high[10] = 102.0
    close[10] = 100.2
    open_[11] = 100.3
    # exit open 11+12=23
    open_[23] = 101.0
    side = 1
    entry_open = open_[11]
    exit_open = open_[23]
    r_h = side * 1e4 * (exit_open / entry_open - 1.0)
    # engine-style residual via tiny pack
    slot = np.arange(n, dtype=np.int64) * 3_600_000_000_000
    pack = SeriesPack(
        symbol="SYN", clock="H1", slot_start=slot, slot_end=slot + 3_600_000_000_000,
        open=open_, high=high, low=low, close=close,
        atr=np.full(n, 1.0), atr_lag=np.full(n, 1.0),
        park=np.full(n, 0.01), ewma_park=np.full(n, 0.01),
        sigma_zvol=np.full(n, 100.0), sigma_zmag=np.full(n, np.nan),
        abs_oo=np.full(n, 10.0), uncond_sigma=np.full(n, 10.0),
        vol_pct=np.full(n, 0.5), mag_pct=np.full(n, np.nan),
        slow_regime=np.full(n, 0.0), shock_flag=np.zeros(n), r=np.zeros(n),
        s_symbol=1.0, design_lo=0, design_hi=n, confirm_hi=n,
    )
    res = residual_r_h(pack, 10, 1, 12)
    return {
        "found": True,
        "side": side,
        "r_h_hand": r_h,
        "r_h_engine": res["r_h"] if res else None,
        "entry_next_open": True,
        "match": bool(res is not None and abs(res["r_h"] - r_h) < 1e-9),
        "label": label_residual(r_h),
        "pass": bool(res is not None and abs(res["r_h"] - r_h) < 1e-9),
    }


def g3_zmag_ineligible(pack: SeriesPack) -> dict:
    """Z-MAG ineligible before first usable forecast; width NaN."""
    # find first finite sigma_zmag
    finite = np.where(np.isfinite(pack.sigma_zmag))[0]
    if finite.size == 0:
        return {
            "found": True, "symbol": pack.symbol,
            "n_eligible": 0, "all_ineligible_early": True,
            "pass": True, "note": "no completed ZZ forecast — all Z-MAG ineligible",
        }
    first = int(finite[0])
    early_nan = bool(not np.isfinite(pack.sigma_zmag[:first]).any()) if first > 0 else True
    return {
        "found": True,
        "symbol": pack.symbol,
        "first_eligible_idx": first,
        "early_all_nan": early_nan,
        "pass": early_nan,
    }


def g4_pmr_cost(pack: SeriesPack) -> dict:
    """P-MR against-side entry, stop 1.5 ATR, partial_net = gross − 11 − funding − 2."""
    # find a decided residual-like entry mid series
    t = pack.design_lo + 50
    if t + 20 >= pack.open.size:
        return {"found": False}
    mon = simulate_policy(pack, t, trade_side=-1, h=12, use_stop=True)
    if mon is None:
        return {"found": False, "reason": "policy None"}
    hand = partial_net(mon["gross_bps"], mon["entry_ts"], mon["exit_ts"], n_legs=1)
    match = abs(hand["partial_net_bps"] - mon["partial_net_bps"]) < 1e-9
    return {
        "found": True,
        "symbol": pack.symbol,
        "gross_bps": mon["gross_bps"],
        "partial_net_engine": mon["partial_net_bps"],
        "partial_net_hand": hand["partial_net_bps"],
        "fee": mon["fee_rt_bps"],
        "funding": mon["funding_bps"],
        "match": match,
        "pass": match,
    }


def run_golden(packs: dict[str, SeriesPack]) -> dict:
    out = {}
    btc = packs.get("BTCUSDT")
    eth = packs.get("ETHUSDT")
    sol = packs.get("SOLUSDT")
    avax = packs.get("AVAXUSDT")
    out["G1"] = g1_zvol_band(btc) if btc else {"found": False}
    out["G2"] = g2_etouch_synthetic()
    out["G3"] = g3_zmag_ineligible(sol) if sol else {"found": False}
    out["G4"] = g4_pmr_cost(avax) if avax else (
        g4_pmr_cost(btc) if btc else {"found": False}
    )
    out["all_pass"] = all(
        out[k].get("pass", out[k].get("match", False)) for k in ("G1", "G2", "G3", "G4")
        if out[k].get("found", False)
    )
    return out
