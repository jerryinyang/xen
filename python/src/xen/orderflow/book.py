"""Bybit L2 depth-stream book reconstruction + sequence-gap handling (INFR-013).

Reconstructs the full order book from Bybit v5 orderbook messages
(`type: "snapshot" | "delta"`), tracking the per-topic update id `u`:

- `snapshot` (or `u == 1`, Bybit's service-restart resend) replaces the book
  and resynchronizes the sequence.
- `delta` with `u <= last_u` is stale → dropped and counted.
- `delta` with `u > last_u + 1` is a SEQUENCE GAP → recorded in the gap
  ledger, the delta is still applied (best-effort book), and the book is
  flagged `out_of_sync` until the next snapshot. Downstream consumers must
  treat out-of-sync intervals as unusable for detector emission.
- Applying a delta while never synced (no snapshot seen) raises.

Prices/sizes arrive as strings; price keys are kept as the parsed float of
the exact source string (identical strings → identical keys). Size "0"
deletes the level.
"""

from dataclasses import dataclass, field

import msgspec


class BookNotSyncedError(RuntimeError):
    """A delta was applied before any snapshot established the book."""


@dataclass(frozen=True)
class SequenceGap:
    """One detected discontinuity in the `u` sequence."""

    ts_ms: int
    expected_u: int
    received_u: int


@dataclass
class DepthMessage:
    """Parsed Bybit v5 orderbook archive/websocket message."""

    ts_ms: int  # gateway timestamp (message `ts`)
    cts_ms: int  # matching-engine timestamp (`cts`; falls back to ts)
    type: str  # "snapshot" | "delta"
    symbol: str
    bids: list[tuple[float, float]]
    asks: list[tuple[float, float]]
    u: int
    seq: int


def parse_depth_line(line: str | bytes) -> DepthMessage:
    """Parse one JSONL line of a Bybit orderbook archive into a DepthMessage."""
    raw = msgspec.json.decode(line)
    data = raw["data"]
    ts = int(raw["ts"])
    return DepthMessage(
        ts_ms=ts,
        cts_ms=int(raw.get("cts", ts)),
        type=raw["type"],
        symbol=data["s"],
        bids=[(float(p), float(s)) for p, s in data.get("b", [])],
        asks=[(float(p), float(s)) for p, s in data.get("a", [])],
        u=int(data["u"]),
        seq=int(data.get("seq", 0)),
    )


@dataclass
class L2Book:
    """Full-depth L2 book state with sequence-gap ledger."""

    symbol: str = ""
    bids: dict[float, float] = field(default_factory=dict)
    asks: dict[float, float] = field(default_factory=dict)
    last_u: int | None = None
    last_ts_ms: int = 0
    synced: bool = False  # at least one snapshot applied
    out_of_sync: bool = False  # gap since last snapshot
    gaps: list[SequenceGap] = field(default_factory=list)
    stale_dropped: int = 0
    snapshots_applied: int = 0
    deltas_applied: int = 0

    # -- update application ------------------------------------------------

    def apply(self, msg: DepthMessage) -> None:
        """Apply one parsed depth message (dispatch on type / u==1 resend)."""
        if msg.type == "snapshot" or msg.u == 1:
            self._apply_snapshot(msg)
        elif msg.type == "delta":
            self._apply_delta(msg)
        else:
            raise ValueError(f"unknown depth message type: {msg.type!r}")

    def _apply_snapshot(self, msg: DepthMessage) -> None:
        self.symbol = msg.symbol
        self.bids = dict(msg.bids)
        self.asks = dict(msg.asks)
        self.last_u = msg.u
        self.last_ts_ms = msg.ts_ms
        self.synced = True
        self.out_of_sync = False
        self.snapshots_applied += 1

    def _apply_delta(self, msg: DepthMessage) -> None:
        if not self.synced or self.last_u is None:
            raise BookNotSyncedError(
                f"{msg.symbol}: delta u={msg.u} before any snapshot"
            )
        if msg.u <= self.last_u:
            self.stale_dropped += 1
            return
        if msg.u != self.last_u + 1:
            self.gaps.append(
                SequenceGap(ts_ms=msg.ts_ms, expected_u=self.last_u + 1, received_u=msg.u)
            )
            self.out_of_sync = True
        for price, size in msg.bids:
            if size == 0.0:
                self.bids.pop(price, None)
            else:
                self.bids[price] = size
        for price, size in msg.asks:
            if size == 0.0:
                self.asks.pop(price, None)
            else:
                self.asks[price] = size
        self.last_u = msg.u
        self.last_ts_ms = msg.ts_ms
        self.deltas_applied += 1

    # -- reads ---------------------------------------------------------------

    @property
    def best_bid(self) -> tuple[float, float] | None:
        if not self.bids:
            return None
        price = max(self.bids)
        return price, self.bids[price]

    @property
    def best_ask(self) -> tuple[float, float] | None:
        if not self.asks:
            return None
        price = min(self.asks)
        return price, self.asks[price]

    @property
    def crossed(self) -> bool:
        """True if best bid >= best ask (invariant violation on a synced book)."""
        bb, ba = self.best_bid, self.best_ask
        return bb is not None and ba is not None and bb[0] >= ba[0]

    def top_n(self, side: str, n: int) -> list[tuple[float, float]]:
        """Top-N (price, size) levels; side 'BID' descending, 'ASK' ascending."""
        if side == "BID":
            return sorted(self.bids.items(), key=lambda x: -x[0])[:n]
        if side == "ASK":
            return sorted(self.asks.items(), key=lambda x: x[0])[:n]
        raise ValueError(f"side must be 'BID' or 'ASK', got {side!r}")

    def depth(self, side: str, n: int) -> float:
        """Cumulative size over the top-N levels of one side."""
        return sum(size for _, size in self.top_n(side, n))
