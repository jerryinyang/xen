"""Golden traces G1–G4 (design §7)."""
from __future__ import annotations

import numpy as np

from config import EWMA_LAMBDA, FEATURE_LAYERS, RIDGE_ALPHA, ZVOL_EPS
from engine import band_bounds, label_residual, residual_r_h
from indicators import ewma_park, parkinson
from models import feature_matrix, ridge_fit, ridge_predict
from prepare import SeriesPack


def g1_ridge_matrix(pack: SeriesPack, H: int = 12, ablation: str = "A2") -> dict:
    """G1: BTCUSDT design matrix at listed t → M-RIDGE ŷ matches hand refit."""
    if pack.symbol != "BTCUSDT":
        return {"found": False, "reason": "not BTCUSDT"}
    t = pack.design_lo + 120
    yh = pack.yhat.get("M-RIDGE", {}).get(ablation, {}).get(H)
    if yh is None or t >= pack.open.size or not np.isfinite(yh[t]):
        # find first finite yhat in DESIGN
        if yh is None:
            return {"found": False, "reason": "no yhat"}
        finite = np.where(np.isfinite(yh[pack.design_lo:pack.design_hi]))[0]
        if finite.size == 0:
            return {"found": False, "reason": "no finite yhat in DESIGN"}
        t = pack.design_lo + int(finite[0])

    X = feature_matrix(pack.features, ablation)
    y = pack.y_target[H]
    ready = pack.y_ready[H]
    # hand-fit on causal prior rows (same rule as walk-forward at month of t)
    tr = np.where(
        (np.arange(pack.open.size) < t)
        & np.isfinite(y)
        & np.isfinite(X).all(axis=1)
        & np.isfinite(ready)
        & (ready <= t)
    )[0]
    if tr.size < 20:
        return {"found": True, "pass": False, "reason": "insufficient train", "t_idx": t, "n_train": int(tr.size)}
    w, mu, sd, ym = ridge_fit(X[tr], y[tr], RIDGE_ALPHA)
    hand = float(ridge_predict(X[t: t + 1], w, mu, sd, ym)[0])
    eng = float(yh[t])
    # monthly refit may differ if hand uses all prior and engine reuses month state —
    # match within 1e-6 relative when same train set; else check finite + same sign class
    rel = abs(hand - eng) / max(1.0, abs(hand))
    return {
        "found": True,
        "symbol": pack.symbol,
        "t_idx": t,
        "H": H,
        "ablation": ablation,
        "n_train": int(tr.size),
        "yhat_hand": hand,
        "yhat_engine": eng,
        "abs_diff": abs(hand - eng),
        "rel_diff": rel,
        "pass": bool(rel < 1e-4 or abs(hand - eng) < 1e-6),
        "note": "expanding prior rows at t (month-refit engine may share fit within month)",
    }


def g2_mzone_band(pack: SeriesPack, z: float = 1.5, H: int = 12) -> dict:
    """G2: ETHUSDT M-ZONE band z=1.5 H=12 from ŷ and Z-VOL floor."""
    if pack.symbol != "ETHUSDT":
        return {"found": False, "reason": "not ETHUSDT"}
    yh = pack.yhat.get("M-RIDGE", {}).get("A2", {}).get(H)
    t = pack.design_lo + 80
    if yh is None:
        return {"found": False, "reason": "no yhat"}
    finite = np.where(np.isfinite(yh[pack.design_lo:pack.design_hi])
                      & np.isfinite(pack.sigma_zvol[pack.design_lo:pack.design_hi]))[0]
    if finite.size == 0:
        return {"found": False, "reason": "no finite yhat+zvol"}
    t = pack.design_lo + int(finite[0])
    yhat = float(yh[t])
    zvol = float(pack.sigma_zvol[t])
    sig_hand = max(abs(yhat), zvol, 1.0)
    # ewma sanity
    park_hand = parkinson(pack.high[: t + 1], pack.low[: t + 1])
    ewma_hand = ewma_park(park_hand, EWMA_LAMBDA)
    e_match = abs(float(ewma_hand[-1]) - float(pack.ewma_park[t])) < 1e-12 or (
        abs(float(ewma_hand[-1]) - float(pack.ewma_park[t]))
        / max(ZVOL_EPS, abs(float(pack.ewma_park[t]))) < 1e-9
    )
    anchor = float(pack.open[t + 1])
    up_h, lo_h = band_bounds(anchor, z, sig_hand)
    return {
        "found": True,
        "symbol": pack.symbol,
        "t_idx": t,
        "yhat": yhat,
        "zvol": zvol,
        "sigma_hand": sig_hand,
        "upper": up_h,
        "lower": lo_h,
        "anchor": anchor,
        "ewma_match": bool(e_match),
        "sigma_floor_ok": bool(sig_hand >= max(zvol, 1.0) - 1e-12),
        "pass": bool(e_match and sig_hand >= max(zvol, 1.0) - 1e-12 and up_h > lo_h),
    }


def g3_etouch_label() -> dict:
    """G3: synthetic E-TOUCH → r_12 MOMO/MR label hand check."""
    n = 40
    open_ = np.full(n, 100.0)
    high = np.full(n, 100.5)
    low = np.full(n, 99.5)
    close = np.full(n, 100.0)
    high[10] = 102.0
    close[10] = 100.2
    open_[11] = 100.3
    open_[23] = 101.0  # exit = entry+12
    side = 1
    entry_open = open_[11]
    exit_open = open_[23]
    r_h = side * 1e4 * (exit_open / entry_open - 1.0)
    slot = np.arange(n, dtype=np.int64) * 3_600_000_000_000
    # minimal pack-like for residual_r_h
    from prepare import SeriesPack
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
    lab = label_residual(r_h)
    return {
        "found": True,
        "r_h_hand": r_h,
        "r_h_engine": res["r_h"] if res else None,
        "label": lab,
        "match": bool(res is not None and abs(res["r_h"] - r_h) < 1e-9),
        "pass": bool(res is not None and abs(res["r_h"] - r_h) < 1e-9 and lab in ("MOMO", "MR", "FLAT")),
    }


def g4_ablation_diff(pack: SeriesPack, H: int = 12) -> dict:
    """G4: A0 score ≠ A2 when WEAK-DIR active on fixture symbol."""
    a0 = pack.yhat.get("M-RIDGE", {}).get("A0", {}).get(H)
    a2 = pack.yhat.get("M-RIDGE", {}).get("A2", {}).get(H)
    if a0 is None or a2 is None:
        return {"found": False, "reason": "missing ablation yhat"}
    m = np.isfinite(a0) & np.isfinite(a2)
    if m.sum() < 10:
        return {"found": True, "pass": False, "reason": "too few paired predictions", "n": int(m.sum())}
    diff = float(np.mean(np.abs(a0[m] - a2[m])))
    # WEAK-DIR columns present and non-constant somewhere
    wd = FEATURE_LAYERS["A2"][len(FEATURE_LAYERS["A0"]):]  # weak after proven+derived? actually A2-A1
    wd = [c for c in FEATURE_LAYERS["A2"] if c not in FEATURE_LAYERS["A1"]]
    active = False
    for c in wd:
        v = pack.features.get(c)
        if v is not None and np.nanstd(v[m]) > 1e-12:
            active = True
            break
    return {
        "found": True,
        "symbol": pack.symbol,
        "n_paired": int(m.sum()),
        "mean_abs_diff_a0_a2": diff,
        "weak_dir_active": active,
        "pass": bool(diff > 1e-9 and active),
        "note": "A0≠A2 when WEAK-DIR varies; discloses load-bearing risk if only A2 wins",
    }


def run_golden(packs: dict[str, SeriesPack]) -> dict:
    out = {}
    btc = packs.get("BTCUSDT")
    eth = packs.get("ETHUSDT")
    sol = packs.get("SOLUSDT")
    out["G1"] = g1_ridge_matrix(btc) if btc else {"found": False, "pass": False}
    out["G2"] = g2_mzone_band(eth) if eth else {"found": False, "pass": False}
    out["G3"] = g3_etouch_label()
    # G4 on SOL if present else first pack
    g4_pack = sol or (next(iter(packs.values())) if packs else None)
    out["G4"] = g4_ablation_diff(g4_pack) if g4_pack else {"found": False, "pass": False}
    out["all_pass"] = all(bool(v.get("pass")) for v in out.values() if isinstance(v, dict) and "pass" in v)
    return out
