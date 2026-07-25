"""Partial cost (fees + funding + allowance). Spread UNAVAILABLE_NOT_CHARGED."""
from __future__ import annotations

import numpy as np

from xen.evaluation import bybit_fee_bps_per_side, count_bybit_funding_stamps

from config import ALLOWANCE_GOVERNING, FEE_RT_BPS, FUNDING_BPS_PER_STAMP

_FEE_RT_FROM_SCHEDULE = 2.0 * bybit_fee_bps_per_side(liquidity="taker")
assert abs(_FEE_RT_FROM_SCHEDULE - FEE_RT_BPS) < 1e-9


def funding_stamps(entry_ts_ns: int, exit_ts_ns: int) -> int:
    return count_bybit_funding_stamps(
        np.datetime64(int(entry_ts_ns), "ns"), np.datetime64(int(exit_ts_ns), "ns")
    )


def partial_net(gross_bps: float, entry_ts: int, exit_ts: int,
                n_legs: int = 1) -> dict:
    """partial_net = gross − n_legs*(fee_rt + allowance) − funding (1 stamp series per leg pair).

    Design §5: fee_rt 11.0 + funding 1.0×stamps + allowance 2.0 per leg.
    """
    stamps = funding_stamps(entry_ts, exit_ts)
    funding = FUNDING_BPS_PER_STAMP * stamps * n_legs
    fee = FEE_RT_BPS * n_legs
    allow = ALLOWANCE_GOVERNING * n_legs
    return {
        "funding_stamps": int(stamps),
        "fee_rt_bps": float(fee),
        "funding_bps": float(funding),
        "allowance_bps": float(allow),
        "partial_net_bps": float(gross_bps - fee - funding - allow),
    }
