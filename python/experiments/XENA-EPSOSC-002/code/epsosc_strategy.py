"""XENA-EPSOSC-001 Nautilus strategy — VOLARM armed-stretch fade (+ STRETCH probe).

DEVIATIONS: none open (QA run-1 D1 was false pin-method alarm — fixed in build_universe
  content pin; D2 membership recompute is delisted-inclusive default).

Mechanics (design §1–§4):
  - Confirmed events on LTF bars ≤ t−1 (ATR, stretch, VOLARM arm, membership).
  - Market entry fills at next LTF RealOpen (next 1m open after LTF complete).
  - Clear: RET_ANCHOR (0.25·k·ATR re-cross or anchor cross) or HYBRID (same +
    time cap H = W LTF bars). TIME-only excluded.
  - One-sided (LONG_ONLY / SHORT_ONLY); no re-entry while episode open.
  - Membership gate: causal online top-10 via precomputed membership series
    (xen.nautilus.universe_selection rule_hash 0dd53037…); daily 00:00 UTC.
    Open episodes may run to clear after membership exit.
  - Finite synthetic SlPrice = EntryFill − side × 1.0 × k·ATR(14)[t−1]
    (sizing denominator only; no live stop order).
  - Engine costless-honest; costs injected at oracle/analysis via
    bybit_round_trip_cost_bps_v1 + funding × episode duration.
  - Segment-end open legs left open → shim Censored=True (oracle segment-end
    censoring; censored-fraction disclosed in batch runner).
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import polars as pl
from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.trading.strategy import Strategy

from features import StreamingLtfState

NS_PER_MIN = 60_000_000_000
NS_PER_DAY = 86_400_000_000_000


@dataclass
class LegSlRecord:
    """Per-leg synthetic stop price for XENA sizing contract."""

    entry_ts_ns: int
    side: int  # +1 long / −1 short
    entry_px: float
    sl_price: float
    atr_ltf: float
    k: float
    clear_policy: str
    w: int


@dataclass
class _OhlcBucket:
    open_ns: int
    close_ns: int
    open: float
    high: float
    low: float
    close: float
    n: int = 0


class EpsoscConfig(StrategyConfig, frozen=True):
    instrument_id: InstrumentId
    bar_type: BarType  # 1-MINUTE-LAST-EXTERNAL
    trade_size: Decimal
    object_type: str  # "VOLARM" | "STRETCH"
    ltf_minutes: int  # 15 | 60
    w: int  # 96 | 192
    k: float  # 2.5 | 3.0
    clear_policy: str  # "RET_ANCHOR" | "HYBRID"
    side_mode: str  # "LONG_ONLY" | "SHORT_ONLY"
    membership_path: str = ""  # parquet with rebalance_ts, symbol|instrument_id
    symbol: str = ""
    candidate_id: str = ""


class EpsoscStrategy(Strategy):
    """VOLARM/STRETCH episode fade on LTF open-to-open with membership gate."""

    def __init__(self, config: EpsoscConfig) -> None:
        super().__init__(config)
        if config.object_type not in ("VOLARM", "STRETCH"):
            raise ValueError(f"object_type={config.object_type!r}")
        if config.ltf_minutes not in (15, 60):
            raise ValueError(f"ltf_minutes must be 15|60, got {config.ltf_minutes}")
        if config.w not in (96, 192):
            raise ValueError(f"w must be 96|192, got {config.w}")
        if config.k not in (2.5, 3.0):
            raise ValueError(f"k must be 2.5|3.0, got {config.k}")
        if config.clear_policy not in ("RET_ANCHOR", "HYBRID"):
            raise ValueError(f"clear_policy={config.clear_policy!r}")
        if config.side_mode not in ("LONG_ONLY", "SHORT_ONLY"):
            raise ValueError(f"side_mode={config.side_mode!r}")
        # Binding grid: VOLARM×15m; disclosure probe: STRETCH×1h
        if config.object_type == "VOLARM" and config.ltf_minutes != 15:
            raise ValueError("VOLARM binding grid is 15m only")
        if config.object_type == "STRETCH" and config.ltf_minutes != 60:
            raise ValueError("STRETCH disclosure probe is 1h only")
        if config.object_type == "STRETCH" and config.clear_policy != "RET_ANCHOR":
            raise ValueError("STRETCH probe is RET_ANCHOR only (design §4.2)")

        self._ltf_ns = int(config.ltf_minutes) * NS_PER_MIN
        self._state = StreamingLtfState(
            w=int(config.w), volarm=(config.object_type == "VOLARM")
        )
        self._ltf: _OhlcBucket | None = None
        self._member_set: set[int] = set()  # rebalance_ts_ns when symbol ∈ top-10
        self._want_dir = 1 if config.side_mode == "LONG_ONLY" else -1
        self._h_time = int(config.w)  # HYBRID / TIME cap in LTF bars

        self._in_position = False
        self._pos_side = 0
        self._bars_held = 0
        self._pending_entry: tuple[int, float] | None = None  # (side, atr)
        self._awaiting_entry_fill = False
        self._awaiting_exit_fill = False
        self.leg_sl_records: list[LegSlRecord] = []
        self.decision_log: list[dict] = []
        self.n_entries = 0
        self.n_exits = 0
        self.n_censored_open = 0  # still open at on_stop

    def on_start(self) -> None:
        self.instrument = self.cache.instrument(self.config.instrument_id)
        if self.instrument is None:
            self.log.error(f"instrument not found: {self.config.instrument_id}")
            self.stop()
            return
        self._member_set = self._load_membership()
        self.subscribe_bars(self.config.bar_type)

    def _load_membership(self) -> set[int]:
        path = str(self.config.membership_path or "")
        sym = str(self.config.symbol or "")
        if not path or not Path(path).exists():
            self.log.warning(f"membership path missing: {path!r} — gate always OFF")
            return set()
        df = pl.read_parquet(path)
        # Accept symbol or instrument_id column
        if "symbol" in df.columns and sym:
            df = df.filter(pl.col("symbol") == sym)
        elif "instrument_id" in df.columns and sym:
            iid = f"{sym}-LINEAR.BYBIT"
            df = df.filter(
                (pl.col("instrument_id") == iid) | (pl.col("instrument_id") == sym)
            )
        if df.height == 0:
            return set()
        col = "rebalance_ts"
        if col not in df.columns:
            return set()
        s = df.get_column(col)
        if s.dtype == pl.Datetime or str(s.dtype).startswith("Datetime"):
            ns = s.dt.epoch("ns").to_list()
        else:
            ns = [int(x) for x in s.to_list()]
        return set(int(x) for x in ns)

    def _is_member_at(self, open_ns: int) -> bool:
        """Membership at open_ns = top-10 on the UTC day-00:00 rebalance ≤ open.

        Daily rebalance at 00:00 UTC; bars on calendar day D use rebalance D 00:00
        (known before any bar that day — causal ≤ t−1).
        """
        if not self._member_set:
            return False
        day_ns = (int(open_ns) // NS_PER_DAY) * NS_PER_DAY
        return day_ns in self._member_set

    def on_bar(self, bar: Bar) -> None:
        """1m LAST bars → clock-aligned LTF completes drive features + episode."""
        o, h, l, c = float(bar.open), float(bar.high), float(bar.low), float(bar.close)
        close_ns = int(bar.ts_event)
        open_ns = close_ns - NS_PER_MIN
        window_open = (open_ns // self._ltf_ns) * self._ltf_ns

        cur = self._ltf
        if cur is None or cur.open_ns != window_open:
            if cur is not None and cur.n > 0:
                self._on_ltf_complete(cur)
            self._ltf = _OhlcBucket(
                open_ns=window_open,
                close_ns=window_open + self._ltf_ns,
                open=o,
                high=h,
                low=l,
                close=c,
                n=1,
            )
        else:
            cur.high = max(cur.high, h)
            cur.low = min(cur.low, l)
            cur.close = c
            cur.n += 1

    def on_stop(self) -> None:
        if self._ltf is not None and self._ltf.n > 0:
            self._on_ltf_complete(self._ltf)
            self._ltf = None
        # Leave open legs open for segment-end / fence censoring (do NOT force-close
        # into a synthetic exit). Nautilus may still flatten on dispose — runner
        # marks still-open ledger rows as Censored via shim.
        if self._in_position:
            self.n_censored_open += 1

    def _on_ltf_complete(self, ltf: _OhlcBucket) -> None:
        """Confirmed LTF bar: update features, clear/hold, gate entry next open."""
        self._state.update(ltf.high, ltf.low, ltf.close, ltf.close_ns)

        # --- clear / time cap on open episode (exit at next LTF open) ---
        if self._in_position and not self._awaiting_exit_fill:
            self._bars_held += 1
            clear_hit = self._state.clear_hit(self._pos_side, float(self.config.k))
            time_hit = (
                self.config.clear_policy == "HYBRID" and self._bars_held >= self._h_time
            )
            if clear_hit or time_hit:
                self._submit_exit()
                return  # no re-entry same bar

        # --- event gate for entry at next LTF open (no pyramiding) ---
        if self._in_position or self._awaiting_entry_fill or self._awaiting_exit_fill:
            return

        side = self._state.event_side(float(self.config.k))
        member = self._is_member_at(ltf.open_ns)  # membership at decision bar open
        # next-open membership: last rebalance ≤ next LTF open (= this close_ns)
        member_next = self._is_member_at(ltf.close_ns)
        want = side == self._want_dir and side != 0
        atr = self._state.atr
        ready = atr == atr and atr > 0 and self._state.anchor == self._state.anchor

        self.decision_log.append(
            {
                "ltf_close_ns": ltf.close_ns,
                "side": int(side),
                "want": bool(want),
                "member": bool(member_next),
                "armed": bool(self._state.armed),
                "stretch": self._state.stretch_units(),
                "atr": float(atr) if atr == atr else None,
                "vol_ratio": self._state.vol_ratio,
            }
        )
        # Entry eligibility at next open: membership known at next open (≤ t−1 rebalance)
        if want and member_next and ready:
            self._pending_entry = (int(side), float(atr))
            self._submit_entry(int(side))

    def _submit_entry(self, side: int) -> None:
        if self._awaiting_entry_fill or self._in_position:
            return
        qty = self.instrument.make_qty(self.config.trade_size)
        order = self.order_factory.market(
            self.config.instrument_id,
            OrderSide.BUY if side > 0 else OrderSide.SELL,
            qty,
            time_in_force=TimeInForce.GTC,
        )
        self._awaiting_entry_fill = True
        self.submit_order(order)

    def _submit_exit(self) -> None:
        if self._awaiting_exit_fill or not self._in_position:
            return
        qty = self.instrument.make_qty(self.config.trade_size)
        order = self.order_factory.market(
            self.config.instrument_id,
            OrderSide.SELL if self._pos_side > 0 else OrderSide.BUY,
            qty,
            time_in_force=TimeInForce.GTC,
        )
        self._awaiting_exit_fill = True
        self.submit_order(order)

    def on_order_filled(self, event) -> None:  # noqa: ANN001
        fill_px = float(event.last_px)
        fill_ts = int(event.ts_event)
        try:
            is_buy = event.order_side == OrderSide.BUY
        except Exception:
            is_buy = "BUY" in str(event.order_side).upper()

        if self._awaiting_entry_fill and not self._in_position:
            side = 1 if is_buy else -1
            atr = float("nan")
            if self._pending_entry is not None:
                side, atr = self._pending_entry
            k = float(self.config.k)
            sl = fill_px - float(side) * 1.0 * k * float(atr)
            self.leg_sl_records.append(
                LegSlRecord(
                    entry_ts_ns=fill_ts,
                    side=int(side),
                    entry_px=fill_px,
                    sl_price=float(sl),
                    atr_ltf=float(atr),
                    k=k,
                    clear_policy=str(self.config.clear_policy),
                    w=int(self.config.w),
                )
            )
            self._in_position = True
            self._pos_side = int(side)
            self._bars_held = 0
            self._awaiting_entry_fill = False
            self._pending_entry = None
            self.n_entries += 1
            return

        if self._awaiting_exit_fill and self._in_position:
            self._in_position = False
            self._pos_side = 0
            self._bars_held = 0
            self._awaiting_exit_fill = False
            self._pending_entry = None
            self.n_exits += 1
