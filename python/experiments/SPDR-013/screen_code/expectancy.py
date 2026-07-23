"""Partial-cost application and the design §5 expectancy decomposition.

Cost stack is fees + discrete funding only (spread UNAVAILABLE_NOT_CHARGED, §0). Fee schedule and
the funding-stamp counter come from ``xen.evaluation`` (no local accounting primitive): fee RT =
2 x taker (11.0 bps), funding = 1.0 bps x discrete 00:00/08:00/16:00 UTC stamps in (entry, exit].
Allowance (0/2/5, governing 2.0) is the design's own sensitivity term, subtracted here.

  partial_net_bps = gross_signed_oo_bps - fee_rt - funding - allowance      (§4 UNIT-PIN)

RIGHT/WRONG use the GROSS sign so costs never redefine directional correctness (§5).
"""
from __future__ import annotations

import numpy as np

from xen.evaluation import bybit_fee_bps_per_side, count_bybit_funding_stamps

from config import (
    ALLOWANCE_GOVERNING,
    ALLOWANCE_SENSITIVITY,
    FEE_RT_BPS,
    FUNDING_BPS_PER_STAMP,
)

# design §4 pin cross-check: 11.0 == 2 x taker(5.5). Fail loudly if the schedule ever moves.
_FEE_RT_FROM_SCHEDULE = 2.0 * bybit_fee_bps_per_side(liquidity="taker")
assert abs(_FEE_RT_FROM_SCHEDULE - FEE_RT_BPS) < 1e-9, (
    f"design §4 fee pin 11.0 != 2x taker={_FEE_RT_FROM_SCHEDULE}"
)


def funding_stamps(entry_ts_ns: int, exit_ts_ns: int) -> int:
    """Discrete Bybit funding stamps in ``(entry, exit]`` via xen.evaluation."""
    return count_bybit_funding_stamps(
        np.datetime64(int(entry_ts_ns), "ns"), np.datetime64(int(exit_ts_ns), "ns")
    )


def apply_costs(episodes: list[dict]) -> list[dict]:
    """Attach fee / funding / partial_net (at every allowance in the sensitivity) per episode."""
    for ep in episodes:
        stamps = funding_stamps(ep["entry_ts"], ep["exit_ts"])
        funding = FUNDING_BPS_PER_STAMP * stamps
        ep["funding_stamps"] = int(stamps)
        ep["fee_rt_bps"] = FEE_RT_BPS
        ep["funding_bps"] = float(funding)
        ep["right"] = bool(ep["gross_bps"] > 0)          # §5 RIGHT = gross sign (explicit column)
        base = ep["gross_bps"] - FEE_RT_BPS - funding
        for allow in ALLOWANCE_SENSITIVITY:
            ep[f"partial_net_bps_a{int(allow)}"] = float(base - allow)
        ep["partial_net_bps"] = float(base - ALLOWANCE_GOVERNING)   # headline (governing 2.0)
    return episodes


def decomposition(gross: np.ndarray, partial: np.ndarray) -> dict:
    """Design §5 decomposition. RIGHT iff gross > 0; WRONG otherwise (incl. flat 0)."""
    gross = np.asarray(gross, float)
    partial = np.asarray(partial, float)
    n = int(np.isfinite(gross).sum())
    if n == 0:
        return {k: float("nan") for k in (
            "n_episodes", "p_right", "avail_when_right", "damage_when_wrong",
            "expectancy_gross", "expectancy_partial", "win_rate_net")} | {"n_episodes": 0}
    right = gross > 0
    n_right = int(right.sum())
    avail = float(gross[right].mean()) if n_right else 0.0
    damage = float(gross[~right].mean()) if (n - n_right) else 0.0
    return {
        "n_episodes": n,
        "p_right": n_right / n,
        "avail_when_right": avail,
        "damage_when_wrong": damage,
        "expectancy_gross": float(gross.mean()),
        "expectancy_partial": float(partial.mean()),   # headline
        "win_rate_net": float((partial > 0).mean()),    # disclosure only (§5)
    }
