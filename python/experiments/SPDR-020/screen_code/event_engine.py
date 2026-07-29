"""SPDR-014 zone → breach-event grammar (inherited, not re-specified).

Causal: features/width ≤ t; anchor = open[t+1]; entry = open[j+1];
L0 residual exit = open[entry+h]. UNDECIDED side = 0. Deadband 5 bps.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from config import (
    DEADBAND_BPS,
    TRAIN_END_NS,
    ZMAG_SENSITIVITY_DIV,
)
from prepare import SeriesPack


@dataclass
class BreachEvent:
    symbol: str
    clock: str
    band: str
    source: str
    z: float
    H: int
    event_type: str
    t_idx: int
    anchor_idx: int
    event_idx: int
    side: int  # +1 / -1 / 0 UNDECIDED
    event: int  # 1 if breach, 0 if not
    upper: float
    lower: float
    anchor: float
    sigma_bps: float
    decision_ts: int
    event_ts: int
    n_undecided: int = 0


def band_bounds(anchor: float, z: float, sigma_bps: float) -> tuple[float, float]:
    half = z * sigma_bps / 1e4
    return anchor * (1.0 + half), anchor * (1.0 - half)


def sigma_for_source(pack: SeriesPack, t: int, source: str) -> float:
    if source == "Z-VOL":
        s = pack.sigma_zvol[t]
    elif source == "Z-MAG":
        s = pack.sigma_zmag[t]
    elif source == "Z-MAG-SENS":
        s = pack.sigma_zmag[t]
        if np.isfinite(s):
            s = s / ZMAG_SENSITIVITY_DIV
    else:
        raise ValueError(source)
    if not np.isfinite(s) or s <= 0:
        return float("nan")
    return float(s)


def detect_event(
    pack: SeriesPack,
    t: int,
    H: int,
    upper: float,
    lower: float,
    event_type: str,
    centre: float,
    illegal_future_touch_at_anchor: bool = False,
) -> dict | None:
    """Scan window t+1 .. t+H. side UNDECIDED = 0 when both touches equal."""
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
                        side = 0  # UNDECIDED
                    else:
                        side = 1 if up_ext > dn_ext else -1
                elif up_touch:
                    side = 1
                else:
                    side = -1
                return {
                    "event": 1,
                    "event_idx": t + 1 if illegal_future_touch_at_anchor else j,
                    "actual_future_event_idx": j,
                    "side": side,
                    "event_type": event_type,
                }
        elif event_type == "E-CLOSE":
            if cl > upper or cl < lower:
                side = 1 if cl > upper else -1
                return {"event": 1, "event_idx": j, "side": side, "event_type": event_type}
    return {"event": 0, "event_idx": -1, "side": 0, "event_type": event_type}


def residual_r_h(pack: SeriesPack, event_idx: int, side: int, h: int) -> dict | None:
    """Entry open[event_idx+1]; exit open[entry+h]. Side-signed r_h in bps."""
    entry = event_idx + 1
    exit_i = entry + h
    n = pack.open.size
    if entry >= n or exit_i >= n or side == 0:
        return None
    if int(pack.slot_start[exit_i]) >= TRAIN_END_NS:
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


def walk_zones(
    pack: SeriesPack,
    *,
    source: str,
    z: float,
    H: int,
    event_type: str,
    h: int,
    band: str,
    occupation_h: int | None = None,
    illegal_future_touch_at_anchor: bool = False,
) -> tuple[list[dict], list[dict], list[dict], dict]:
    """Non-overlapping origins (SPDR-014). Returns zones, events, residual posts, counts.

    Parent walks with occupation_h = max H_POST (24) then re-derives each h residual
    from the same non-overlapping events (SPDR-014 run_screen). That spacing is required
    for parent parity. Residual posts use the requested ``h``; occupation uses
    ``occupation_h`` (default max(h, 24) when None → caller should pass 24).
    UNDECIDED counted, excluded from posts.
    """
    if band == "DESIGN":
        lo, hi = pack.design_lo, pack.design_hi
    elif band == "CONFIRM":
        lo, hi = pack.design_hi, pack.confirm_hi
    else:  # TRAIN = full
        lo, hi = pack.design_lo, pack.confirm_hi

    occ_h = int(occupation_h) if occupation_h is not None else int(h)
    zones: list[dict] = []
    events: list[dict] = []
    posts: list[dict] = []
    n_undecided = 0
    n_origins = 0
    n_events = 0
    n = pack.open.size
    t = lo
    busy_until = -1
    while t < hi:
        if t < busy_until:
            t += 1
            continue
        max_need = t + H + 1 + occ_h + 1
        if max_need >= n:
            break
        sig = sigma_for_source(pack, t, source)
        if not np.isfinite(sig) or sig <= 0:
            t += 1
            continue
        anchor = float(pack.open[t + 1])
        if anchor <= 0 or not np.isfinite(anchor):
            t += 1
            continue
        n_origins += 1
        upper, lower = band_bounds(anchor, z, sig)
        centre = anchor
        zrec = {
            "symbol": pack.symbol, "clock": pack.clock, "band": band,
            "source": source, "z": z, "H": H, "t_idx": t,
            "decision_ts": int(pack.slot_end[t]),
            "anchor_idx": t + 1,
            "anchor_ts": int(pack.slot_start[t + 1]),
            "anchor": anchor, "sigma_bps": float(sig),
            "upper": upper, "lower": lower,
        }
        zones.append(zrec)

        ev = detect_event(
            pack,
            t,
            H,
            upper,
            lower,
            event_type,
            centre,
            illegal_future_touch_at_anchor=illegal_future_touch_at_anchor,
        )
        if ev is None:
            break
        erec = {
            **{k: zrec[k] for k in (
                "symbol", "clock", "band", "source", "z", "H", "t_idx", "anchor_idx",
                "decision_ts", "sigma_bps", "upper", "lower", "anchor",
            )},
            "event_type": event_type,
            "event": int(ev["event"]),
            "event_idx": int(ev["event_idx"]),
            "side": int(ev["side"]),
            "event_ts": int(pack.slot_end[ev["event_idx"]]) if ev["event"] else -1,
            "event_high": (
                float(pack.high[ev["event_idx"]]) if ev["event"] else float("nan")
            ),
            "event_low": (
                float(pack.low[ev["event_idx"]]) if ev["event"] else float("nan")
            ),
            "event_close": (
                float(pack.close[ev["event_idx"]]) if ev["event"] else float("nan")
            ),
            "actual_future_event_idx": int(
                ev.get("actual_future_event_idx", ev["event_idx"])
            ),
            "illegal_future_touch_at_anchor": illegal_future_touch_at_anchor,
        }
        events.append(erec)

        if ev["event"] == 1:
            n_events += 1
            if ev["side"] == 0:
                n_undecided += 1
                busy_until = t + H + 1
            else:
                # occupation residual at occ_h (parent: h=24); report residual at h
                res_occ = residual_r_h(pack, ev["event_idx"], ev["side"], occ_h)
                res = residual_r_h(pack, ev["event_idx"], ev["side"], h)
                if res is not None:
                    lab = label_residual(res["r_h"])
                    posts.append({
                        **erec,
                        "h": h,
                        "label": lab,
                        "r_h": res["r_h"],
                        "entry_idx": res["entry_idx"],
                        "exit_idx": res["exit_idx"],
                        "entry_ts": res["entry_ts"],
                        "exit_ts": res["exit_ts"],
                        "entry_open": res["entry_open"],
                        "exit_open": res["exit_open"],
                        "breach_side": int(ev["side"]),
                    })
                if res_occ is not None:
                    busy_until = res_occ["exit_idx"] + 1
                else:
                    busy_until = t + H + 1
        else:
            busy_until = t + H + 1
        t = max(t + 1, busy_until)

    counts = {
        "n_origins": n_origins,
        "n_events": n_events,
        "n_undecided": n_undecided,
        "n_decided": len(posts),
        "p_event": (n_events / n_origins) if n_origins else float("nan"),
    }
    return zones, events, posts, counts


def posts_from_events(
    pack: SeriesPack,
    events: list[dict],
    *,
    h: int,
) -> list[dict]:
    """Re-derive residual posts at hold h from a decided-event list (parent pattern)."""
    posts: list[dict] = []
    for e in events:
        if e.get("event") != 1 or int(e.get("side", 0)) == 0:
            continue
        res = residual_r_h(pack, int(e["event_idx"]), int(e["side"]), h)
        if res is None:
            continue
        posts.append({
            **e,
            "h": h,
            "label": label_residual(res["r_h"]),
            "r_h": res["r_h"],
            "entry_idx": res["entry_idx"],
            "exit_idx": res["exit_idx"],
            "entry_ts": res["entry_ts"],
            "exit_ts": res["exit_ts"],
            "entry_open": res["entry_open"],
            "exit_open": res["exit_open"],
            "breach_side": int(e["side"]),
        })
    return posts


def parity_cell_stats(posts: list[dict]) -> dict:
    """Parent-definition cell stats: mean_r_h, p_momo, p_mr, n_decided (flat in denom)."""
    if not posts:
        return {
            "mean_r_h": float("nan"), "p_momo": float("nan"), "p_mr": float("nan"),
            "n_decided": 0, "p_flat": float("nan"),
        }
    r = np.array([p["r_h"] for p in posts], dtype=float)
    labs = [label_residual(x) for x in r]
    n = len(r)
    n_momo = sum(1 for x in labs if x == "MOMO")
    n_mr = sum(1 for x in labs if x == "MR")
    n_flat = sum(1 for x in labs if x == "FLAT")
    return {
        "mean_r_h": float(np.mean(r)),
        "p_momo": n_momo / n if n else float("nan"),
        "p_mr": n_mr / n if n else float("nan"),
        "p_flat": n_flat / n if n else float("nan"),
        "n_decided": n,
    }
