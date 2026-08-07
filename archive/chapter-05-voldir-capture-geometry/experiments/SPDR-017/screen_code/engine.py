"""M-ZONE / M-SIGN-ERR / Z-VOL zone→event→residual engine (design §3–§5).

Causal: features/width ≤ t; anchor = open[t+1]; breach entry = open[j+1];
residual exit open at entry+h; TRAIN fence exit < train_end.
"""
from __future__ import annotations

import numpy as np

from config import (
    DEADBAND_BPS,
    NS,
    PRIMARY_ABLATION,
    PRIMARY_MODEL,
    STOP_ATR_MULT,
    TRAIN_END,
    ZVOL_EPS,
)
from costs import partial_net
from prepare import SeriesPack

_TRAIN_END_NS = int(TRAIN_END.timestamp() * NS)


def band_bounds(anchor: float, z: float, sigma_bps: float) -> tuple[float, float]:
    half = z * sigma_bps / 1e4
    return anchor * (1.0 + half), anchor * (1.0 - half)


def detect_event(
    pack: SeriesPack,
    t: int,
    H: int,
    upper: float,
    lower: float,
    event_type: str,
    centre: float,
) -> dict | None:
    n = pack.open.size
    if t + H >= n:
        return None
    window = range(t + 1, t + H + 1)
    if event_type == "E-HORIZON":
        j = t + H
        c = pack.close[j]
        if c > upper or c < lower:
            side = 1 if c > upper else -1
            return {"event": 1, "event_idx": j, "side": side, "event_type": event_type}
        return {"event": 0, "event_idx": -1, "side": 0, "event_type": event_type}

    for j in window:
        hi, lo, cl = pack.high[j], pack.low[j], pack.close[j]
        if event_type == "E-TOUCH":
            up_touch = hi >= upper
            dn_touch = lo <= lower
            if up_touch or dn_touch:
                if up_touch and dn_touch:
                    up_ext = (hi - centre) / centre * 1e4
                    dn_ext = (centre - lo) / centre * 1e4
                    if abs(up_ext - dn_ext) < 1e-9:
                        side = 0
                    else:
                        side = 1 if up_ext > dn_ext else -1
                elif up_touch:
                    side = 1
                else:
                    side = -1
                return {"event": 1, "event_idx": j, "side": side, "event_type": event_type}
        elif event_type == "E-CLOSE":
            if cl > upper or cl < lower:
                side = 1 if cl > upper else -1
                return {"event": 1, "event_idx": j, "side": side, "event_type": event_type}
    return {"event": 0, "event_idx": -1, "side": 0, "event_type": event_type}


def residual_r_h(pack: SeriesPack, event_idx: int, side: int, h: int) -> dict | None:
    entry = event_idx + 1
    exit_i = entry + h
    n = pack.open.size
    if entry >= n or exit_i >= n or side == 0:
        return None
    if int(pack.slot_start[exit_i]) >= _TRAIN_END_NS:
        return None
    entry_open = float(pack.open[entry])
    exit_open = float(pack.open[exit_i])
    if entry_open <= 0 or not np.isfinite(entry_open) or not np.isfinite(exit_open):
        return None
    r_h = side * 1e4 * (exit_open / entry_open - 1.0)
    return {
        "entry_idx": entry,
        "exit_idx": exit_i,
        "entry_open": entry_open,
        "exit_open": exit_open,
        "entry_ts": int(pack.slot_start[entry]),
        "exit_ts": int(pack.slot_start[exit_i]),
        "r_h": float(r_h),
        "side": int(side),
    }


def label_residual(r_h: float, c: float = DEADBAND_BPS) -> str:
    if r_h > c:
        return "MOMO"
    if r_h < -c:
        return "MR"
    return "FLAT"


def simulate_policy(
    pack: SeriesPack,
    entry_idx: int,
    trade_side: int,
    h: int,
    use_stop: bool = True,
) -> dict | None:
    n = pack.open.size
    if entry_idx >= n or trade_side == 0:
        return None
    entry_open = float(pack.open[entry_idx])
    atr_e = float(pack.atr_lag[entry_idx])
    if not np.isfinite(atr_e) or atr_e <= 0 or entry_open <= 0:
        return None
    stop_level = entry_open - trade_side * STOP_ATR_MULT * atr_e
    exit_i = entry_idx + h
    exit_reason = "time"
    for j in range(entry_idx, min(entry_idx + h, n)):
        if j == entry_idx:
            o = pack.open[j]
            if trade_side == 1 and o <= stop_level:
                exit_i = j
                exit_reason = "stop_open"
                break
            if trade_side == -1 and o >= stop_level:
                exit_i = j
                exit_reason = "stop_open"
                break
        if use_stop and j < n:
            if trade_side == 1 and pack.low[j] <= stop_level:
                exit_i = j + 1 if j + 1 < n and j + 1 <= entry_idx + h else min(j + 1, n - 1)
                exit_reason = "stop"
                break
            if trade_side == -1 and pack.high[j] >= stop_level:
                exit_i = j + 1 if j + 1 < n and j + 1 <= entry_idx + h else min(j + 1, n - 1)
                exit_reason = "stop"
                break
    if exit_i >= n:
        return None
    if int(pack.slot_start[exit_i]) >= _TRAIN_END_NS:
        return None
    exit_open = float(pack.open[exit_i])
    gross = trade_side * 1e4 * (exit_open / entry_open - 1.0)
    cost = partial_net(gross, int(pack.slot_start[entry_idx]), int(pack.slot_start[exit_i]), n_legs=1)
    return {
        "entry_idx": entry_idx,
        "exit_idx": exit_i,
        "entry_ts": int(pack.slot_start[entry_idx]),
        "exit_ts": int(pack.slot_start[exit_i]),
        "trade_side": trade_side,
        "gross_bps": float(gross),
        "exit_reason": exit_reason,
        **cost,
    }


def _sigma_mzone(pack: SeriesPack, t: int, H: int, ablation: str, model: str) -> float:
    """σ_bps = max(|ŷ_t|, Z-VOL σ_bps, 1.0)."""
    yh = pack.yhat.get(model, {}).get(ablation, {}).get(H)
    if yh is None or not np.isfinite(yh[t]):
        return float("nan")
    zvol = pack.sigma_zvol[t]
    if not np.isfinite(zvol):
        zvol = 0.0
    return float(max(abs(float(yh[t])), float(zvol), 1.0))


def _sigma_zvol(pack: SeriesPack, t: int) -> float:
    s = pack.sigma_zvol[t]
    if not np.isfinite(s) or s <= 0:
        return float("nan")
    return float(s)


def run_cell(
    pack: SeriesPack,
    *,
    source: str,
    z: float,
    H: int,
    event_type: str,
    h: int,
    band: str,
    policy: str = "P-NONE",
    ablation: str = PRIMARY_ABLATION,
    model: str = PRIMARY_MODEL,
    uncond: bool = False,
    feature_shuffle_perm: np.ndarray | None = None,
) -> tuple[list[dict], list[dict], list[dict]]:
    """Walk non-overlapping origins; return (zones, events, posts)."""
    if band == "DESIGN":
        lo, hi = pack.design_lo, pack.design_hi
    else:
        lo, hi = pack.design_hi, pack.confirm_hi

    zones: list[dict] = []
    events: list[dict] = []
    posts: list[dict] = []

    n = pack.open.size
    t = lo
    busy_until = -1
    # for feature-shuffle control: permute yhat indices within band
    yhat_series = None
    if source in ("M-ZONE", "M-SIGN-ERR"):
        yhat_series = pack.yhat.get(model, {}).get(ablation, {}).get(H)
        if yhat_series is None:
            return zones, events, posts

    while t < hi:
        if t < busy_until:
            t += 1
            continue
        max_need = t + H + 1 + h + 1
        if max_need >= n:
            break

        if uncond:
            sig = pack.uncond_sigma[t]
            yhat_t = 0.0
        elif source == "Z-VOL":
            sig = _sigma_zvol(pack, t)
            yhat_t = 0.0
        elif source == "M-ZONE":
            tt = int(feature_shuffle_perm[t]) if feature_shuffle_perm is not None else t
            if feature_shuffle_perm is not None:
                # use foreign yhat magnitude but still need finite local features
                if not np.isfinite(yhat_series[tt]):
                    t += 1
                    continue
                yhat_t = float(yhat_series[tt])
                zvol = pack.sigma_zvol[t] if np.isfinite(pack.sigma_zvol[t]) else 0.0
                sig = float(max(abs(yhat_t), float(zvol), 1.0))
            else:
                yhat_t = float(yhat_series[t]) if np.isfinite(yhat_series[t]) else float("nan")
                sig = _sigma_mzone(pack, t, H, ablation, model)
        elif source == "M-SIGN-ERR":
            if feature_shuffle_perm is not None:
                tt = int(feature_shuffle_perm[t])
                yhat_t = float(yhat_series[tt]) if np.isfinite(yhat_series[tt]) else float("nan")
            else:
                yhat_t = float(yhat_series[t]) if np.isfinite(yhat_series[t]) else float("nan")
            zvol = pack.sigma_zvol[t]
            if not np.isfinite(yhat_t) or not np.isfinite(zvol):
                t += 1
                continue
            sig = float(max(abs(yhat_t), float(zvol), 1.0))
        else:
            raise ValueError(source)

        if not np.isfinite(sig) or sig <= 0:
            t += 1
            continue

        anchor = float(pack.open[t + 1])
        if anchor <= 0 or not np.isfinite(anchor):
            t += 1
            continue

        if source == "M-SIGN-ERR" and not uncond:
            # centre = model-implied path centre; event when residual vs centre_model exceeds z·σ
            centre_model = anchor * (1.0 + yhat_t / 1e4)
            upper = centre_model + z * sig / 1e4 * anchor
            lower = centre_model - z * sig / 1e4 * anchor
            # rewrite as price levels:
            upper = centre_model * (1.0 + z * sig / 1e4) if False else centre_model + anchor * (z * sig / 1e4)
            lower = centre_model - anchor * (z * sig / 1e4)
            centre = centre_model
        else:
            upper, lower = band_bounds(anchor, z, sig)
            centre = anchor

        zrec = {
            "symbol": pack.symbol, "clock": pack.clock, "band": band,
            "source": source if not uncond else "UNCOND",
            "z": z, "H": H, "t_idx": t,
            "ablation": ablation, "model": model,
            "decision_ts": int(pack.slot_end[t]),
            "anchor_idx": t + 1,
            "anchor_ts": int(pack.slot_start[t + 1]),
            "anchor": anchor, "sigma_bps": float(sig),
            "yhat_bps": float(yhat_t) if np.isfinite(yhat_t) else None,
            "upper": upper, "lower": lower,
            "vol_tercile": _tercile(pack.vol_pct[t]),
            "mag_high": bool(np.isfinite(pack.mag_pct[t]) and pack.mag_pct[t] >= 2.0 / 3.0),
            "slow_regime": _regime(pack.slow_regime[t]),
            "shock_flag": bool(pack.shock_flag[t] == 1),
        }
        zones.append(zrec)

        ev = detect_event(pack, t, H, upper, lower, event_type, centre)
        if ev is None:
            break
        erec = {
            **{k: zrec[k] for k in (
                "symbol", "clock", "band", "source", "z", "H", "t_idx", "anchor_idx",
                "ablation", "model", "vol_tercile", "mag_high", "slow_regime", "shock_flag",
            )},
            "event_type": event_type,
            "event": int(ev["event"]),
            "event_idx": int(ev["event_idx"]),
            "side": int(ev["side"]),
            "event_ts": int(pack.slot_end[ev["event_idx"]]) if ev["event"] else -1,
        }
        events.append(erec)

        if ev["event"] == 1 and ev["side"] != 0:
            res = residual_r_h(pack, ev["event_idx"], ev["side"], h)
            if res is not None:
                lab = label_residual(res["r_h"])
                prec = {
                    **erec,
                    "h": h,
                    "label": lab,
                    "r_h": res["r_h"],
                    "entry_idx": res["entry_idx"],
                    "exit_idx": res["exit_idx"],
                    "entry_ts": res["entry_ts"],
                    "exit_ts": res["exit_ts"],
                    "policy": policy,
                }
                if policy in ("P-MOMO", "P-MR"):
                    trade_side = ev["side"] if policy == "P-MOMO" else -ev["side"]
                    mon = simulate_policy(pack, res["entry_idx"], trade_side, h)
                    if mon is not None:
                        prec.update({
                            "gross_bps": mon["gross_bps"],
                            "partial_net_bps": mon["partial_net_bps"],
                            "fee_rt_bps": mon["fee_rt_bps"],
                            "funding_bps": mon["funding_bps"],
                            "exit_reason": mon["exit_reason"],
                            "trade_side": mon["trade_side"],
                        })
                        busy_until = mon["exit_idx"] + 1
                    else:
                        busy_until = res["exit_idx"] + 1
                else:
                    busy_until = res["exit_idx"] + 1
                posts.append(prec)
            else:
                busy_until = t + H + 1
        else:
            busy_until = t + H + 1
        t = max(t + 1, busy_until)
    return zones, events, posts


def _tercile(pct: float) -> str:
    if not np.isfinite(pct):
        return "NA"
    if pct < 1.0 / 3.0:
        return "LOW"
    if pct < 2.0 / 3.0:
        return "MID"
    return "HIGH"


def _regime(v: float) -> str:
    if not np.isfinite(v):
        return "NA"
    return "HIGH" if v >= 0.5 else "LOW"
