"""ARCHIVED cost apparatus (INFR-022) — NOT callable from any live research path.

INFR-022 (2026-08-08) retired the cost model programme-wide: no spread, commission, or
swap enters any calculation in any experiment type unless an explicit operator cost
directive requests costs (recorded in the experiment's design.md). Everything in this
module is the pre-INFR-022 cost stack, moved verbatim for historical reproducibility
(FTMO/EXP-019 evidence, Bybit T1 fees/funding, spread-scale routing).

Binding rules:

* Only an operator cost directive may re-enable any function here, and the directive
  must be recorded in the design before execution (QA traces it).
* Live modules must not import from this module. Legacy CAL apparatus
  (``xena/calibration_*.py``, bannered as non-bindable) may import ``bybit_round_trip_cost_bps``
  for historical replay only.
* Names retained here for history: ``FTMO_COSTS``, ``round_trip_cost_bps``,
  ``usd_notional_per_lot``, ``BYBIT_USDT_PERP_FEES``, ``BYBIT_FUNDING_CONSERVATIVE_BPS_PER_8H``,
  ``bybit_fee_bps_per_side``, ``count_bybit_funding_stamps``, ``t1_round_trip_spread_bps``,
  ``SPREAD_SCALE_ROUTING_MULTIPLIER``, ``spread_scale_route``, ``bybit_round_trip_cost_bps``.
"""
from __future__ import annotations

from datetime import datetime, timezone

import numpy as np

# --------------------------------------------------------------------------- #
# Declared trading-cost table (EXP-019, CF-VOLHARV-001)
# --------------------------------------------------------------------------- #
# Source: FTMO published symbol specifications, https://ftmo.com/wp-json/ftmo/symbols
# (the data feed behind https://ftmo.com/en/symbols/), snapshot 2026-07-04. Values verbatim.
# Operator directive 2026-07-04 (EXP-019 deviation D5): cost basis = FTMO commissions +
# spread; swap DISREGARDED (design §6 swap table superseded).
#   * commission / commission_type: FTMO's published per-lot commission.
#     "flat_USD"  = fixed USD per 1 standard lot, ROUND TRIP (operator-confirmed 2026-07-07):
#                   the $5 figure is the full round-turn charge, so it is applied ONCE and is
#                   NOT scaled by ``commission_events``. As bps of notional it depends on the
#                   USD notional of one lot, which is currency-convention-specific — computed by
#                   ``usd_notional_per_lot`` (XXXUSD = contract_size·price; USDXXX = contract_size;
#                   cross = contract_size·base_usd_rate, which must be pinned explicitly).
#                   The ``pip_commission_per_lot`` field (FTMO's ~$3/lot ≈ 0.3 pips on EURUSD)
#                   is recorded verbatim for disclosure only and is NO LONGER used in the cost
#                   conversion (it disagrees with the authoritative $5 flat).
#     "percent"   = percent of notional per event; price-free (charged on the traded amount,
#                   not entry price). ``commission_basis`` ∈ {"per_side","round_turn"} pins the
#                   convention: "per_side" scales by ``commission_events`` (x2 for a round trip),
#                   "round_turn" is charged once. Default "per_side"; verify vs FTMO per symbol —
#                   a wrong per-side assumption on a round-turn % overstates the fee 2x.
#     Informative, never gating.
#   * spread_pips: NOT statically published (live-ticker only). Must be read off the live
#     FTMO page at analysis time and pinned here before the binding cost read; the design's
#     1x/2x stress read (§6) then applies to commission + spread jointly.
#   * pip_conversion: price units per pip; contract_size: units per 1.0 lot.
FTMO_COST_SNAPSHOT = "2026-07-06 https://ftmo.com/wp-json/ftmo/symbols"
FTMO_COSTS: dict[str, dict] = {
    # symbol: contract_size, digits, pip_conversion, commission, commission_type,
    #         usd_commission_per_lot, pip_commission_per_lot (FTMO-published pips), spread_pips
    # --------------------------------------------------------------------------- #
    # Forex — majors (all flat $5/lot USD commission)
    # --------------------------------------------------------------------------- #
    "EURUSD": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.30, "spread_pips": None},
    "GBPUSD": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.30, "spread_pips": None},
    "USDJPY": {"contract_size": 100000, "digits": 3, "pip_conversion": 0.01,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.48, "spread_pips": None},
    "USDCHF": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.27, "spread_pips": None},
    "USDCAD": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.41, "spread_pips": None},
    "AUDUSD": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.30, "spread_pips": None},
    "NZDUSD": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.30, "spread_pips": None},
    # Forex — crosses
    "EURJPY": {"contract_size": 100000, "digits": 3, "pip_conversion": 0.01,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.48, "spread_pips": None},
    "GBPJPY": {"contract_size": 100000, "digits": 3, "pip_conversion": 0.01,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.48, "spread_pips": None},
    "AUDJPY": {"contract_size": 100000, "digits": 3, "pip_conversion": 0.01,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.48, "spread_pips": None},
    "EURCHF": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.27, "spread_pips": None},
    "EURGBP": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.23, "spread_pips": None},
    "EURAUD": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.44, "spread_pips": None},
    "EURCAD": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.41, "spread_pips": None},
    "EURNZD": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.49, "spread_pips": None},
    "GBPAUD": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.44, "spread_pips": None},
    "GBPCAD": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.41, "spread_pips": None},
    "GBPCHF": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.27, "spread_pips": None},
    "GBPNZD": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.49, "spread_pips": None},
    "AUDCAD": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.41, "spread_pips": None},
    "AUDCHF": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.27, "spread_pips": None},
    "AUDNZD": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.49, "spread_pips": None},
    "NZDCAD": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.41, "spread_pips": None},
    "NZDCHF": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.27, "spread_pips": None},
    "NZDJPY": {"contract_size": 100000, "digits": 3, "pip_conversion": 0.01,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.48, "spread_pips": None},
    "CADJPY": {"contract_size": 100000, "digits": 3, "pip_conversion": 0.01,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.48, "spread_pips": None},
    "CADCHF": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.27, "spread_pips": None},
    "CHFJPY": {"contract_size": 100000, "digits": 3, "pip_conversion": 0.01,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 0.48, "spread_pips": None},



    # --------------------------------------------------------------------------- #
    # Metals CFD — percent commission
    # --------------------------------------------------------------------------- #
    # FTMO code XAU/USD (Metals CFD). Published percent (0.0014) and usd_commission (11.69)
    # are mutually inconsistent at the snapshot gold price — both recorded verbatim, disclosed.
    # percent-type ⇒ the usd_commission_per_lot field is disclosure-only (not used in the bps conv).
    "XAUUSD": {"contract_size": 100, "digits": 2, "pip_conversion": 1.0,
               "commission": 0.0014, "commission_type": "percent", "commission_basis": "per_side",
               "usd_commission_per_lot": 11.69, "pip_commission_per_lot": 0.24,
               "spread_pips": None},
    # FTMO code XAG/USD (Metals CFD). Same %-commission inconsistency noted for gold.
    "XAGUSD": {"contract_size": 5000, "digits": 3, "pip_conversion": 1.0,
               "commission": 0.0014, "commission_type": "percent", "commission_basis": "per_side",
               "usd_commission_per_lot": 8.85, "pip_commission_per_lot": 0.03,
               "spread_pips": None},
    # --------------------------------------------------------------------------- #
    # Crypto CFD — percent commission
    # --------------------------------------------------------------------------- #
    # FTMO code BTCUSD (Crypto CFD): 0.065% of notional per trade.
    "BTCUSD": {"contract_size": 1, "digits": 2, "pip_conversion": 1.0,
               "commission": 0.065, "commission_type": "percent", "commission_basis": "per_side",
               "usd_commission_per_lot": 81.407, "pip_commission_per_lot": 0.0,
               "spread_pips": None},
    # --------------------------------------------------------------------------- #
    # Cash-CFD indices: zero commission (spread-only pricing).
    # --------------------------------------------------------------------------- #
    "USTEC": {"contract_size": 1, "digits": 2, "pip_conversion": 1.0,
              "commission": 0.0, "commission_type": "percent", "usd_commission_per_lot": 0.0,
              "pip_commission_per_lot": 0.0, "spread_pips": None},
    "US500": {"contract_size": 1, "digits": 2, "pip_conversion": 1.0,
              "commission": 0.0, "commission_type": "percent", "usd_commission_per_lot": 0.0,
              "pip_commission_per_lot": 0.0, "spread_pips": None},
    "US2000": {"contract_size": 1, "digits": 2, "pip_conversion": 1.0,
               "commission": 0.0, "commission_type": "percent", "usd_commission_per_lot": 0.0,
               "pip_commission_per_lot": 0.0, "spread_pips": None},
    "JP225": {"contract_size": 10, "digits": 2, "pip_conversion": 1.0,
              "commission": 0.0, "commission_type": "percent", "usd_commission_per_lot": 0.0,
              "pip_commission_per_lot": 0.0, "spread_pips": None},
    "AUS200": {"contract_size": 1, "digits": 2, "pip_conversion": 1.0,
               "commission": 0.0, "commission_type": "percent", "usd_commission_per_lot": 0.0,
               "pip_commission_per_lot": 0.0, "spread_pips": None},
    "US30": {"contract_size": 1, "digits": 2, "pip_conversion": 1.0,
             "commission": 0.0, "commission_type": "percent", "usd_commission_per_lot": 0.0,
             "pip_commission_per_lot": 0.0, "spread_pips": None},
    "EU50": {"contract_size": 1, "digits": 2, "pip_conversion": 1.0,
             "commission": 0.0, "commission_type": "percent", "usd_commission_per_lot": 0.0,
             "pip_commission_per_lot": 0.0, "spread_pips": None},
    "GER40": {"contract_size": 1, "digits": 2, "pip_conversion": 1.0,
              "commission": 0.0, "commission_type": "percent", "usd_commission_per_lot": 0.0,
              "pip_commission_per_lot": 0.0, "spread_pips": None},
    "HK50": {"contract_size": 1, "digits": 2, "pip_conversion": 1.0,
             "commission": 0.0, "commission_type": "percent", "usd_commission_per_lot": 0.0,
             "pip_commission_per_lot": 0.0, "spread_pips": None},
    "UK100": {"contract_size": 1, "digits": 2, "pip_conversion": 1.0,
              "commission": 0.0, "commission_type": "percent", "usd_commission_per_lot": 0.0,
              "pip_commission_per_lot": 0.0, "spread_pips": None},
    # Exotics (informative — not in Xen universe)
    "USDZAR": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 5.0, "spread_pips": None},
    "USDSEK": {"contract_size": 100000, "digits": 5, "pip_conversion": 0.0001,
               "commission": 5.0, "commission_type": "flat_USD", "usd_commission_per_lot": 5.0,
               "pip_commission_per_lot": 3.33, "spread_pips": None},
}

# --------------------------------------------------------------------------- #
# Bybit USDT linear perpetual cost table (INFR-012, replaced FTMO for the Nautilus stack)
# --------------------------------------------------------------------------- #
# Source: Bybit derivatives fee schedule (USDT perpetuals), snapshot 2026-07-15.
# T1 lane: engine costless-honest; Chapter 05 charged fees + funding only.
# Spread cost unavailable: it was not charged, so reported cost understated total cost.
BYBIT_COST_SNAPSHOT = "2026-07-15 Bybit USDT linear perpetual fee schedule"
BYBIT_USDT_PERP_FEES: dict[str, float] = {
    "maker_bps_per_side": 2.0,    # 0.02% maker
    "taker_bps_per_side": 5.5,    # 0.055% taker
}
# Conservative funding assumption when history missing (R7) — 8h rate, bps of notional
BYBIT_FUNDING_CONSERVATIVE_BPS_PER_8H = 1.0
SPREAD_SCALE_ROUTING_MULTIPLIER = 3.0  # gross < 3× RT spread => undecidable on T1 (INFR-010 §4)
_NS_PER_HOUR = 3_600_000_000_000
_BYBIT_FUNDING_INTERVAL_NS = 8 * _NS_PER_HOUR


def _utc_timestamp_ns(value: str | datetime | np.datetime64) -> int:
    """Convert one UTC timestamp to integer nanoseconds."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError("datetime funding timestamps must be timezone-aware")
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    elif isinstance(value, str):
        value = value.removesuffix("Z")
    timestamp = np.datetime64(value, "ns")
    if np.isnat(timestamp):
        raise ValueError(f"invalid funding timestamp {value!r}")
    return int(timestamp.astype(np.int64))


def count_bybit_funding_stamps(
    entry_time: str | datetime | np.datetime64,
    exit_time: str | datetime | np.datetime64,
) -> int:
    """Count scheduled 00:00/08:00/16:00 UTC settlements in ``(entry, exit]``."""
    entry_ns = _utc_timestamp_ns(entry_time)
    exit_ns = _utc_timestamp_ns(exit_time)
    if exit_ns < entry_ns:
        raise ValueError("exit_time must be at or after entry_time")
    return exit_ns // _BYBIT_FUNDING_INTERVAL_NS - entry_ns // _BYBIT_FUNDING_INTERVAL_NS


def t1_round_trip_spread_bps(
    symbol: str,
    spread_bps: float,
    *,
    stress: float = 1.0,
) -> float:
    """Validate and stress one non-negative round-trip spread pin in bps."""
    del symbol  # per-symbol series already resolved by caller
    spread = float(spread_bps)
    multiplier = float(stress)
    if not np.isfinite(spread) or spread < 0.0:
        raise ValueError(f"spread_bps must be finite and non-negative, got {spread_bps!r}")
    if not np.isfinite(multiplier) or multiplier < 0.0:
        raise ValueError(f"stress must be finite and non-negative, got {stress!r}")
    return float(multiplier * spread)


def bybit_fee_bps_per_side(*, liquidity: str = "taker") -> float:
    """Published maker/taker fee in bps per side."""
    liq = liquidity.lower()
    if liq == "maker":
        return BYBIT_USDT_PERP_FEES["maker_bps_per_side"]
    if liq == "taker":
        return BYBIT_USDT_PERP_FEES["taker_bps_per_side"]
    raise ValueError(f"liquidity must be maker|taker, got {liquidity!r}")


def bybit_round_trip_cost_bps(
    symbol: str,
    entry_price: float,
    *,
    liquidity: str = "taker",
    spread_bps: float | None = None,
    funding_bps_per_8h: float | None = None,
    hold_hours: float = 8.0,
    funding_stamps: int | None = None,
    funding_coverage: str = "OK",
    stress: float = 1.0,
) -> dict:
    """ARCHIVED (INFR-022): declared T1 round-trip cost in bps.

    Retained for historical CAL replay only. Live research paths never charge costs;
    see the module banner. Original semantics (historical record):

    Spread was never charged programme-wide — no quote, effective or proxy spread was
    available for the Bybit T1 lane, so the cost stack was fees plus discrete funding
    only; every result carried ``cost_scope=PARTIAL_FEES_FUNDING_ONLY``.
    """
    del symbol, entry_price  # USDT-margined perps: bps of notional is price-free
    if spread_bps is not None:
        raise ValueError(
            "spread cost is not charged programme-wide: no quote or effective spread exists "
            "for the Bybit T1 lane, and a fixed proxy is not a substitute. Omit spread_bps. "
            "For decidability routing use spread_scale_route / t1_round_trip_spread_bps."
        )
    fee_side = bybit_fee_bps_per_side(liquidity=liquidity)
    multiplier = float(stress)
    if not np.isfinite(multiplier) or multiplier < 0.0:
        raise ValueError(f"stress must be finite and non-negative, got {stress!r}")
    fee_rt = multiplier * 2.0 * fee_side
    spread_rt = None
    spread_cost_status = "UNAVAILABLE_NOT_CHARGED"
    cost_scope = "PARTIAL_FEES_FUNDING_ONLY"
    if funding_bps_per_8h is None:
        funding_bps_per_8h = BYBIT_FUNDING_CONSERVATIVE_BPS_PER_8H
        if funding_coverage == "OK":
            funding_coverage = "GAP"
    if funding_stamps is None:
        funding_units = hold_hours / 8.0
        funding_method = "CONTINUOUS_LEGACY"
    else:
        if isinstance(funding_stamps, bool) or int(funding_stamps) != funding_stamps:
            raise ValueError("funding_stamps must be a non-negative integer")
        if funding_stamps < 0:
            raise ValueError("funding_stamps must be a non-negative integer")
        funding_units = float(funding_stamps)
        funding_method = "DISCRETE_STAMPS"
    funding_rt = multiplier * funding_bps_per_8h * funding_units
    total = fee_rt + funding_rt + (spread_rt if spread_rt is not None else 0.0)
    return {
        "total_bps": float(total),
        "fee_rt_bps": float(fee_rt),
        "spread_rt_bps": spread_rt,
        "spread_cost_status": spread_cost_status,
        "spread_cost_caveat": (
            "Spread cost unavailable and not charged; reported cost understates total cost "
            "and reported net performance is overstated."
        ),
        "cost_scope": cost_scope,
        "funding_rt_bps": float(funding_rt),
        "funding_method": funding_method,
        "funding_coverage": funding_coverage,
        "liquidity": liquidity,
        "stress": stress,
    }


def spread_scale_route(
    gross_edge_bps: float,
    rt_spread_bps: float,
    *,
    secondary_available: bool = True,
) -> dict:
    """ARCHIVED (INFR-022): §4 spread-scale routing — undecidable on T1 when gross < 3× RT
    spread. Retired with the T1 decidability routing; retained for historical replay."""
    threshold = SPREAD_SCALE_ROUTING_MULTIPLIER * rt_spread_bps
    undecidable = abs(gross_edge_bps) < threshold
    if undecidable and secondary_available:
        route = "AWAITING_MBP"
        note = "verdict-bearing confirmation requires T2 or park AWAITING_MBP"
    elif undecidable:
        route = "PARKED_T1_UNRESOLVED"
        note = "secondary data unavailable; unresolved on this catalog"
    else:
        route = "T1_DECIDABLE"
        note = "T1 may carry verdict-bearing reads (subject to power/cost)"
    return {
        "gross_edge_bps": float(gross_edge_bps),
        "rt_spread_bps": float(rt_spread_bps),
        "threshold_bps": float(threshold),
        "t1_undecidable": undecidable,
        "route": route,
        "note": note,
    }


def usd_notional_per_lot(symbol: str, price: float, *, base_usd_rate: float | None = None) -> float:
    """USD notional of one standard lot (the denominator for a fixed-USD commission → bps).

    Currency-convention aware — ``price`` alone only yields USD notional for XXXUSD pairs:
      * XXXUSD forex  → contract_size · price   (quote = USD; price is USD per base unit)
      * USDXXX forex  → contract_size           (base = USD; price is irrelevant)
      * cross forex   → contract_size · base_usd_rate  (base ≠ USD, quote ≠ USD; rate must be
                        pinned explicitly — same discipline as ``spread_pips``)
      * USD-priced non-forex (metals/crypto/indices) → contract_size · price
        (these are all percent-commission, so this branch is not reached via the cost path).
    """
    spec = FTMO_COSTS[symbol.upper()]
    cs = float(spec["contract_size"])
    sym = symbol.upper()
    if len(sym) == 6 and sym[3:] == "USD":            # XXXUSD: quote is USD
        return cs * price
    if len(sym) == 6 and sym[:3] == "USD":            # USDXXX: base is USD
        return cs
    if len(sym) == 6:                                  # cross: base ≠ USD, quote ≠ USD
        if base_usd_rate is None:
            raise ValueError(
                f"{symbol}: cross pair — base_usd_rate not pinned. A fixed-USD commission needs "
                "the base→USD rate to form USD notional; pin it explicitly before the cost read.")
        return cs * base_usd_rate
    return cs * price                                  # USD-priced non-forex (percent-comm anyway)


def round_trip_cost_bps(symbol: str, entry_price: float, *, spread_pips: float | None = None,
                        commission_events: float = 2.0, base_usd_rate: float | None = None,
                        stress: float = 1.0) -> float:
    """ARCHIVED (INFR-022): declared round-trip cost in bps of notional for one leg.

    Retained for historical reproducibility (FTMO/EXP-019 evidence); see the module banner.
    Original semantics (historical record):

    commission:
      * percent-type  → commission% of notional per event, scaled by ``commission_events``
        (2 = per-side reading of a round trip). Charged on the traded amount, not entry price.
      * flat_USD-type → the published ``usd_commission_per_lot`` is a ROUND-TRIP fixed-USD charge
        (operator-confirmed 2026-07-07), so it is applied ONCE and is independent of
        ``commission_events``. Converted to bps via the USD notional of one lot
        (``usd_notional_per_lot`` — currency-convention aware; crosses need ``base_usd_rate``).
        The pip-commission field is disclosure-only and no longer used here.
    spread: one full published spread per round trip (cross once at entry; exit symmetric
    half-spreads sum to one). ``stress`` scales the whole cost (design §6: report 1x and 2x).
    """
    spec = FTMO_COSTS[symbol.upper()]
    if spec["commission_type"] == "percent":
        # commission_basis pins whether the published % is per-side (×events for a round trip)
        # or already round-turn (charged once). Declared per symbol; verify vs FTMO before a
        # binding cost read. Prevents the silent ×2 overstatement when the % is round-turn.
        basis = spec.get("commission_basis", "per_side")
        events = commission_events if basis == "per_side" else 1.0
        comm_bps = events * spec["commission"] * 100.0             # percent of notional → bps
    else:                                                            # flat_USD: fixed $/lot, round trip
        usd_notional = usd_notional_per_lot(symbol, entry_price, base_usd_rate=base_usd_rate)
        comm_bps = spec["usd_commission_per_lot"] / usd_notional * 1e4
    sp = spread_pips if spread_pips is not None else spec["spread_pips"]
    if sp is None:
        raise ValueError(f"{symbol}: spread_pips not pinned — read it off the live FTMO page "
                         "and pass/pin it before the binding cost read (EXP-019 D5).")
    spread_bps = sp * spec["pip_conversion"] / entry_price * 1e4
    return float(stress * (comm_bps + spread_bps))
