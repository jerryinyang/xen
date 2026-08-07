"""Zone / event / residual / money engine (design §2–§5).

Causal: features/width ≤ t; anchor = open[t+1]; breach entry = open[j+1];
residual exit open at entry+h; TRAIN fence exit < train_end.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from config import (
    DEADBAND_BPS,
    STOP_ATR_MULT,
    TRAIN_END,
    NS,
    ZMAG_SENSITIVITY_DIV,
    ZVOL_EPS,
)
from costs import partial_net

_TRAIN_END_NS = int(TRAIN_END.timestamp() * NS)


@dataclass
class SeriesPack:
    """Precomputed per-symbol clock series."""
    symbol: str
    clock: str
    slot_start: np.ndarray
    slot_end: np.ndarray
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    atr: np.ndarray
    atr_lag: np.ndarray
    park: np.ndarray
    ewma_park: np.ndarray
    sigma_zvol: np.ndarray          # s * ewma_park (bps)
    sigma_zmag: np.ndarray          # predicted mag (bps); NaN if ineligible
    abs_oo: np.ndarray
    uncond_sigma: np.ndarray        # expanding std abs_oo
    vol_pct: np.ndarray             # expanding percentile of ewma_park
    mag_pct: np.ndarray             # expanding percentile of sigma_zmag
    slow_regime: np.ndarray         # 1=HIGH 0=LOW of rv20-like (ewma_park median split)
    shock_flag: np.ndarray          # top-decile |r| (named shock only)
    r: np.ndarray
    s_symbol: float
    design_lo: int
    design_hi: int                  # exclusive index into arrays for DESIGN band end
    confirm_hi: int                 # exclusive for CONFIRM end


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
    """Scan active window bars t+1 .. t+H for event. Returns event dict or None if incomplete.

    Event bar index j is within the window. side UNDECIDED = 0.
    """
    n = pack.open.size
    # need bars t+1 .. t+H complete and residual space will be checked later
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
                        side = 0  # UNDECIDED
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
    """Breach entry = open[event_idx+1]; exit open at entry+h. r_h side-signed bps."""
    entry = event_idx + 1
    exit_i = entry + h
    n = pack.open.size
    if entry >= n or exit_i >= n or side == 0:
        return None
    # TRAIN fence: exit open timestamp must be < train_end
    # exit open is the open of bar exit_i; slot_start is bar open time
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
    """Open-to-open policy: enter at open[entry], exit min(h, stop). trade_side +1 long / -1 short."""
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
    # path bars entry .. entry+h-1 for stop touch; exit at next open after touch
    for j in range(entry_idx, min(entry_idx + h, n)):
        if j == entry_idx:
            # cannot stop on entry bar open already beyond? check open beyond stop
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
                # exit next open
                if j + 1 < n and j + 1 <= entry_idx + h:
                    exit_i = j + 1
                    exit_reason = "stop"
                else:
                    exit_i = min(j + 1, n - 1)
                    exit_reason = "stop"
                break
            if trade_side == -1 and pack.high[j] >= stop_level:
                if j + 1 < n and j + 1 <= entry_idx + h:
                    exit_i = j + 1
                    exit_reason = "stop"
                else:
                    exit_i = min(j + 1, n - 1)
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


def simulate_straddle(pack: SeriesPack, entry_idx: int, H: int) -> dict | None:
    """Dual-leg at zone anchor open; exit both at H. Secondary disclosure only."""
    exit_i = entry_idx + H
    if entry_idx >= pack.open.size or exit_i >= pack.open.size:
        return None
    if int(pack.slot_start[exit_i]) >= _TRAIN_END_NS:
        return None
    o0 = float(pack.open[entry_idx])
    o1 = float(pack.open[exit_i])
    if o0 <= 0:
        return None
    # long + short: gross sum is ~0 path; still apply 2× costs for disclosure
    long_g = 1e4 * (o1 / o0 - 1.0)
    short_g = 1e4 * (o0 / o1 - 1.0) if o1 > 0 else float("nan")  # wait: short gross = -long
    short_g = -long_g
    gross = long_g + short_g  # identically 0 pre-cost for OO on same path
    cost = partial_net(gross, int(pack.slot_start[entry_idx]), int(pack.slot_start[exit_i]), n_legs=2)
    return {
        "entry_idx": entry_idx,
        "exit_idx": exit_i,
        "entry_ts": int(pack.slot_start[entry_idx]),
        "exit_ts": int(pack.slot_start[exit_i]),
        "gross_bps": float(gross),
        "long_gross_bps": float(long_g),
        "short_gross_bps": float(short_g),
        **cost,
    }


def sigma_for_source(pack: SeriesPack, t: int, source: str, zmag_sens: bool = False) -> float:
    if source == "Z-VOL":
        s = pack.sigma_zvol[t]
    elif source == "Z-MAG":
        s = pack.sigma_zmag[t]
        if zmag_sens and np.isfinite(s):
            s = s / ZMAG_SENSITIVITY_DIV
    else:
        raise ValueError(source)
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
    zmag_sens: bool = False,
    uncond: bool = False,
) -> tuple[list[dict], list[dict], list[dict]]:
    """Walk non-overlapping origins; return (zones, events, post_or_money).

    band: DESIGN or CONFIRM selects origin index range.
    """
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
    while t < hi:
        if t < busy_until:
            t += 1
            continue
        # need anchor bar t+1 and window t+H, and residual entry+h if event
        max_need = t + H + 1 + h + 1
        if max_need >= n:
            break
        if uncond:
            sig = pack.uncond_sigma[t]
        else:
            sig = sigma_for_source(pack, t, source, zmag_sens=zmag_sens)
        if not np.isfinite(sig) or sig <= 0:
            t += 1
            continue
        # features known at t; anchor = open[t+1]
        anchor = float(pack.open[t + 1])
        if anchor <= 0 or not np.isfinite(anchor):
            t += 1
            continue
        upper, lower = band_bounds(anchor, z, sig)
        centre = anchor
        zrec = {
            "symbol": pack.symbol, "clock": pack.clock, "band": band,
            "source": source if not uncond else "UNCOND",
            "z": z, "H": H, "t_idx": t,
            "decision_ts": int(pack.slot_end[t]),
            "anchor_idx": t + 1,
            "anchor_ts": int(pack.slot_start[t + 1]),
            "anchor": anchor, "sigma_bps": float(sig),
            "upper": upper, "lower": lower,
            "vol_tercile": _tercile(pack.vol_pct[t]),
            "mag_high": bool(np.isfinite(pack.mag_pct[t]) and pack.mag_pct[t] >= 2.0 / 3.0),
            "slow_regime": _regime(pack.slow_regime[t]),
            "last_k_state_1": _last_k_state(pack.slow_regime, t, 1),
            "last_k_state_2": _last_k_state(pack.slow_regime, t, 2),
            "last_k_state_3": _last_k_state(pack.slow_regime, t, 3),
            "shock_flag": bool(pack.shock_flag[t] == 1),
            "zmag_sens": zmag_sens,
        }
        zones.append(zrec)

        ev = detect_event(pack, t, H, upper, lower, event_type, centre)
        if ev is None:
            # incomplete window — stop
            break
        erec = {
            **{k: zrec[k] for k in (
                "symbol", "clock", "band", "source", "z", "H", "t_idx", "anchor_idx",
                "vol_tercile", "mag_high", "slow_regime",
                "last_k_state_1", "last_k_state_2", "last_k_state_3",
                "shock_flag",
            )},
            "event_type": event_type,
            "event": int(ev["event"]),
            "event_idx": int(ev["event_idx"]),
            "side": int(ev["side"]),
            "event_ts": int(pack.slot_end[ev["event_idx"]]) if ev["event"] else -1,
        }
        events.append(erec)

        # occupation: zone window always occupies until t+H+1; residual extends if event
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
            # no decided event: free after zone window
            busy_until = t + H + 1
        t = max(t + 1, busy_until)
    return zones, events, posts


def _last_k_state(regime: np.ndarray, t: int, k: int) -> str:
    """Ordered slow-regime label sequence over the last K bars ending at t (≤ t, causal).

    design §4.4 / AMENDMENT-S2 (O3 'last-k states / last X labels'). Oldest→newest, so the
    LAST char is the decision bar t. 'H'=HIGH(1.0), 'L'=LOW(0.0), '?'=NaN/unknown (warm-up).
    Order + run-length are preserved (a count would discard both). Left-padded with '?' when
    fewer than K bars precede t.
    """
    lo = max(0, t - k + 1)
    w = regime[lo:t + 1]
    chars = ["H" if v == 1.0 else ("L" if v == 0.0 else "?") for v in w]
    pad = "?" * (k - len(chars))
    return pad + "".join(chars)


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
