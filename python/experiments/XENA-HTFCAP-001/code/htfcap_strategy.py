"""XENA-HTFCAP-001 Nautilus strategy — DI×VOL_HI / DI_ADX×VOL_HI × fixed hold.

DEVIATIONS:
  D2 (NEUTRAL): Nautilus L1 bar matching fills market orders at bar **close**
    (same as VAL-008). Schedule/causality are engine-driven; ``run_batch.open_to_open_anchor``
    sets emission Entry/Exit fill prices to catalog **15m RealOpen** for L-29 / design
    open-to-open estimand. Not a silent change — required for L-29.
  D3 (operator-approved 2026-07-18, QA-2 #11): venue OMS = **HEDGING** (not NETTING).
    Greedy back-to-back re-entry (SPDR ``greedy_entries``: next entry = first gate-ON at
    index ≥ prev_entry + H) requires leg_{k+1} to OPEN at the same 15m open where leg_k
    CLOSES. Under NETTING a coincident close+open nets to nothing; HEDGING keeps each leg a
    distinct position id. Legs are non-overlapping by construction (next entry = prev exit),
    so there is never true concurrency. Deviates from the NETTING topology validated in
    INFR-014 S1 — re-smoked for multi-instrument cleanliness.

Mechanics (design §1–§4):
  - Decision on confirmed 15m bar close using last **clock-aligned** confirmed 4h HTF ≤ t−1
    (same bucket rule as ``xen.bar_aggregator.aggregate_ohlc`` / SPDR-006).
  - Greedy legs on the 15m OPEN grid (SPDR ``greedy_entries``): at boundary T, first close
    any leg whose hold expired (entry + H·15m == T), then open a new leg at T iff
    T ≥ next-allowed (= prev_entry + H·15m) and gate-ON. Entry/exit market orders fill at
    the next 15m RealOpen (L-29, anchored in run_batch).
  - Fixed hold H ∈ {16,32,64} 15m bars.
  - Finite synthetic SlPrice = EntryFill − side × 1.0 × HTF ATR(14)[confirmed]
    (sizing denominator only; no live stop order).
  - Engine costless-honest; costs via bybit_round_trip_cost_bps_v1 + funding at oracle.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from decimal import Decimal

from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.trading.strategy import Strategy

from features import StreamingHtfState

LTF_MINUTES = 15
HTF_MINUTES = 240
NS_PER_MIN = 60_000_000_000
NS_PER_SEC = 1_000_000_000
LTF_NS = LTF_MINUTES * NS_PER_MIN
HTF_SEC = HTF_MINUTES * 60


@dataclass
class LegSlRecord:
    """Per-leg synthetic stop price for XENA sizing contract."""

    entry_ts_ns: int
    side: int  # +1 long / −1 short
    entry_px: float
    sl_price: float
    atr_htf: float
    hold_bars: int


@dataclass
class _OhlcBucket:
    open_ns: int
    close_ns: int
    open: float
    high: float
    low: float
    close: float
    n: int = 0
    bucket_id: int = 0  # aggregate_ohlc-compatible bucket key


def _agg_bucket_id(close_ns: int, period_minutes: int) -> int:
    """Same bucket key as ``aggregate_ohlc``: (CloseTime_s - 1) // period_seconds."""
    close_s = int(close_ns // NS_PER_SEC)
    period_s = period_minutes * 60
    return (close_s - 1) // period_s


def _bucket_close_ns(bucket_id: int, period_minutes: int) -> int:
    """Aggregated bar CloseTime ns matching aggregate_ohlc."""
    period_s = period_minutes * 60
    return int((bucket_id + 1) * period_s * NS_PER_SEC)


def _bucket_open_ns(bucket_id: int, period_minutes: int) -> int:
    period_s = period_minutes * 60
    return int(bucket_id * period_s * NS_PER_SEC)


class HtfCapConfig(StrategyConfig, frozen=True):
    instrument_id: InstrumentId
    bar_type: BarType  # 1-MINUTE-LAST-EXTERNAL
    trade_size: Decimal
    filter_model: str  # "DI×VOL_HI" | "DI_ADX×VOL_HI"
    vol_thr: float
    adx_min: float  # ignored for DI×VOL_HI (pass 0.0)
    hold_bars: int  # 16 | 32 | 64
    candidate_id: str = ""


@dataclass
class _OpenLeg:
    position_id: object
    close_ns: int
    side: int
    atr: float
    entry_ns: int


class HtfCapStrategy(Strategy):
    """HTF interaction-filter gate → greedy fixed-hold market legs (HEDGING, D3)."""

    def __init__(self, config: HtfCapConfig) -> None:
        super().__init__(config)
        if config.filter_model not in ("DI×VOL_HI", "DI_ADX×VOL_HI"):
            raise ValueError(f"unknown filter_model={config.filter_model!r}")
        if config.hold_bars not in (16, 32, 64):
            raise ValueError(f"hold_bars must be 16|32|64, got {config.hold_bars}")
        self._htf = StreamingHtfState()
        self._ltf: _OhlcBucket | None = None
        self._htf_bucket: _OhlcBucket | None = None
        self._hold_ns = config.hold_bars * LTF_NS
        self._next_allowed_ns = 0  # greedy non-overlap: earliest allowed entry boundary
        self._open_legs: list[_OpenLeg] = []
        # FIFO of legs submitted but not yet position-opened: (close_ns, side, atr)
        self._pending: deque[tuple[int, int, float]] = deque()
        self.leg_sl_records: list[LegSlRecord] = []
        self.decision_log: list[dict] = []

    def on_start(self) -> None:
        self.instrument = self.cache.instrument(self.config.instrument_id)
        if self.instrument is None:
            self.log.error(f"instrument not found: {self.config.instrument_id}")
            self.stop()
            return
        self.subscribe_bars(self.config.bar_type)

    def on_bar(self, bar: Bar) -> None:
        """1m LAST bars → clock-aligned 15m/4h; complete LTF on last 1m (L-29)."""
        o, h, l, c = float(bar.open), float(bar.high), float(bar.low), float(bar.close)
        close_ns = int(bar.ts_event)
        ltf_bid = _agg_bucket_id(close_ns, LTF_MINUTES)
        ltf_open = _bucket_open_ns(ltf_bid, LTF_MINUTES)
        ltf_close = _bucket_close_ns(ltf_bid, LTF_MINUTES)

        cur = self._ltf
        if cur is None or cur.bucket_id != ltf_bid:
            # New 15m bucket — previous must already have been completed on its last 1m
            self._ltf = _OhlcBucket(
                open_ns=ltf_open,
                close_ns=ltf_close,
                open=o,
                high=h,
                low=l,
                close=c,
                n=1,
                bucket_id=ltf_bid,
            )
        else:
            cur.high = max(cur.high, h)
            cur.low = min(cur.low, l)
            cur.close = c
            cur.n += 1

        # Complete on the LAST 1m of the 15m window (close_ns == bucket close).
        # Market order here fills at next 1m open = next 15m RealOpen (L-29).
        if self._ltf is not None and close_ns >= self._ltf.close_ns:
            self._on_ltf_complete(self._ltf)
            self._ltf = None

    def on_stop(self) -> None:
        # Do not force-complete a partial LTF (would break clock alignment / open fill).
        self.close_all_positions(self.config.instrument_id)

    def _on_ltf_complete(self, ltf: _OhlcBucket) -> None:
        """Confirmed clock-aligned 15m bar: roll HTF, expire holds, greedy gate."""
        # --- HTF 4h: clock-aligned via aggregate_ohlc bucket on LTF CloseTime ---
        # Finalize previous HTF only when LTF enters a *new* HTF bucket (not on the
        # closing LTF of the old bucket). Matches SPDR map_htf_to_ltf: HTF CloseTime
        # STRICTLY < next LTF OpenTime before features are usable.
        htf_bid = _agg_bucket_id(ltf.close_ns, HTF_MINUTES)
        if self._htf_bucket is None:
            self._htf_bucket = _OhlcBucket(
                open_ns=_bucket_open_ns(htf_bid, HTF_MINUTES),
                close_ns=_bucket_close_ns(htf_bid, HTF_MINUTES),
                open=ltf.open,
                high=ltf.high,
                low=ltf.low,
                close=ltf.close,
                n=1,
                bucket_id=htf_bid,
            )
        elif self._htf_bucket.bucket_id == htf_bid:
            hb = self._htf_bucket
            hb.high = max(hb.high, ltf.high)
            hb.low = min(hb.low, ltf.low)
            hb.close = ltf.close
            hb.n += 1
        else:
            self._finalize_htf()
            self._htf_bucket = _OhlcBucket(
                open_ns=_bucket_open_ns(htf_bid, HTF_MINUTES),
                close_ns=_bucket_close_ns(htf_bid, HTF_MINUTES),
                open=ltf.open,
                high=ltf.high,
                low=ltf.low,
                close=ltf.close,
                n=1,
                bucket_id=htf_bid,
            )

        # T = boundary of this decision bar close == next 15m OPEN.
        t_ns = int(ltf.close_ns)

        # --- expire holds: close any leg whose hold ended at this open (fills at T) ---
        still_open: list[_OpenLeg] = []
        for leg in self._open_legs:
            if t_ns >= leg.close_ns:
                self._close_leg(leg)
            else:
                still_open.append(leg)
        self._open_legs = still_open

        # --- greedy gate for entry at this 15m open (next entry ≥ prev entry + H) ---
        adx_min = (
            float(self.config.adx_min)
            if self.config.filter_model == "DI_ADX×VOL_HI"
            else None
        )
        on, side, atr = self._htf.gate(
            vol_thr=float(self.config.vol_thr), adx_min=adx_min
        )
        self.decision_log.append(
            {
                "ltf_close_ns": ltf.close_ns,
                "ltf_open_ns": ltf.open_ns,
                "htf_ready": self._htf.ready,
                "gate_on": bool(on),
                "side": int(side),
                "atr": float(atr) if atr == atr else None,
                "vol_ratio": self._htf.vol_ratio,
                "adx": self._htf.adx,
                "dir": self._htf.dir,
                "eligible": bool(on and t_ns >= self._next_allowed_ns),
            }
        )
        if (
            on
            and side != 0
            and atr == atr
            and atr > 0
            and t_ns >= self._next_allowed_ns
        ):
            self._pending.append((t_ns + self._hold_ns, int(side), float(atr)))
            self._submit_entry(int(side))
            self._next_allowed_ns = t_ns + self._hold_ns

    def _finalize_htf(self) -> None:
        hb = self._htf_bucket
        if hb is None or hb.n < 1:
            self._htf_bucket = None
            return
        # Require substantial coverage (SPDR min_coverage=0.90 → ≥14 of 16 LTF bars)
        if hb.n < 14:
            self._htf_bucket = None
            return
        self._htf.update(hb.high, hb.low, hb.close, hb.close_ns)
        self._htf_bucket = None

    def _submit_entry(self, side: int) -> None:
        qty = self.instrument.make_qty(self.config.trade_size)
        order = self.order_factory.market(
            self.config.instrument_id,
            OrderSide.BUY if side > 0 else OrderSide.SELL,
            qty,
            time_in_force=TimeInForce.GTC,
        )
        self.submit_order(order)

    def _close_leg(self, leg: _OpenLeg) -> None:
        position = self.cache.position(leg.position_id)
        if position is not None and position.is_open:
            self.close_position(position)

    def on_position_opened(self, event) -> None:  # noqa: ANN001
        """Map each newly opened HEDGING position to its pending leg (FIFO)."""
        if not self._pending:
            return
        close_ns, side, atr = self._pending.popleft()
        try:
            entry_px = float(event.avg_px_open)
        except Exception:
            entry_px = float("nan")
        entry_ns = int(event.ts_opened)
        sl = entry_px - float(side) * 1.0 * float(atr)
        self.leg_sl_records.append(
            LegSlRecord(
                entry_ts_ns=entry_ns,
                side=int(side),
                entry_px=entry_px,
                sl_price=float(sl),
                atr_htf=float(atr),
                hold_bars=int(self.config.hold_bars),
            )
        )
        self._open_legs.append(
            _OpenLeg(
                position_id=event.position_id,
                close_ns=int(close_ns),
                side=int(side),
                atr=float(atr),
                entry_ns=entry_ns,
            )
        )
