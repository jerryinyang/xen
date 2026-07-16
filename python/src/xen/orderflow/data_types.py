"""Custom Nautilus Data contracts for the orderflow feature store (INFR-013).

Each class subclasses `nautilus_trader.core.data.Data` via `@customdataclass`,
which auto-generates dict/msgpack/arrow codecs and registers the type with the
serialization layer (`register_serializable_type` + `register_arrow`), so the
objects write into and read back from a `ParquetDataCatalog` and can be
subscribed to by strategies like native data.

Every record carries `pipeline_version` (feature-definition versioning,
spec §2.3) — extraction code is schema; threshold changes create dataset
discontinuities that must be traceable.

Timestamps: `ts_event` = exchange timestamp (ns), `ts_init` = ingest
timestamp (ns), per spec §6.4.

Detector event payloads follow spec §4.4 field lists. AbsorptionEvent's
research-only validation field (subsequent-N-bar return) is intentionally
NOT part of the signal-lane contract (look-ahead by construction, spec §7);
it belongs in a separate research table at detector-implementation time.
"""

from nautilus_trader.model.custom import customdataclass
from nautilus_trader.core.data import Data
from nautilus_trader.model.identifiers import InstrumentId


_NULL_INSTRUMENT = InstrumentId.from_str("NULL-LINEAR.BYBIT")


@customdataclass
class FootprintRowData(Data):
    """One footprint cell: per (base bar, price level) traded-volume split (spec §4.1)."""

    instrument_id: InstrumentId = _NULL_INSTRUMENT
    bar_close_ns: int = 0  # close of the base bar this row belongs to
    bar_resolution_s: int = 1  # base-bar resolution (aggregate upward on read)
    price: float = 0.0
    bid_volume: float = 0.0  # volume traded at this level with aggressor = sell
    ask_volume: float = 0.0  # volume traded at this level with aggressor = buy
    trade_count: int = 0
    max_single_print: float = 0.0
    pipeline_version: str = ""


@customdataclass
class SessionProfileData(Data):
    """Session volume-profile summary (spec §4.2)."""

    instrument_id: InstrumentId = _NULL_INSTRUMENT
    session_id: str = ""  # e.g. "UTC_DAY:2023-07-12"
    session_start_ns: int = 0
    session_end_ns: int = 0
    poc: float = 0.0
    vah: float = 0.0
    val: float = 0.0
    value_area_pct: float = 0.70
    total_volume: float = 0.0
    shape: str = ""  # profile shape classifier: P / b / D / DD
    lvn_prices_json: str = "[]"  # JSON list of LVN price bands
    pipeline_version: str = ""


@customdataclass
class BookStateData(Data):
    """Per-sample book scalars: spread, depth, slope, OFI (spec §4.3)."""

    instrument_id: InstrumentId = _NULL_INSTRUMENT
    best_bid_price: float = 0.0
    best_ask_price: float = 0.0
    best_bid_size: float = 0.0
    best_ask_size: float = 0.0
    spread: float = 0.0
    depth_bid: float = 0.0  # cumulative size over top-N bid levels
    depth_ask: float = 0.0  # cumulative size over top-N ask levels
    depth_n: int = 0
    book_slope: float = 0.0  # depth_bid / depth_ask (path-of-least-resistance)
    ofi: float = 0.0  # order-flow imbalance vs previous sample
    pipeline_version: str = ""


@customdataclass
class IcebergEvent(Data):
    """Executed volume at a price exceeds displayed size across refills (spec §4.4)."""

    instrument_id: InstrumentId = _NULL_INSTRUMENT
    price: float = 0.0
    side: str = ""  # "BID" | "ASK"
    visible_size: float = 0.0
    total_filled: float = 0.0
    refill_count: int = 0
    pipeline_version: str = ""


@customdataclass
class SweepEvent(Data):
    """Single aggressive sequence consumes >= k levels (spec §4.4)."""

    instrument_id: InstrumentId = _NULL_INSTRUMENT
    direction: str = ""  # "UP" | "DOWN"
    levels_swept: int = 0
    slippage_ticks: int = 0
    volume: float = 0.0
    pipeline_version: str = ""


@customdataclass
class AbsorptionEvent(Data):
    """High traded volume at a level with price failing to advance (spec §4.4)."""

    instrument_id: InstrumentId = _NULL_INSTRUMENT
    price: float = 0.0
    side_absorbed: str = ""  # "BID" | "ASK"
    absorbed_volume: float = 0.0
    pipeline_version: str = ""


@customdataclass
class ReloadEvent(Data):
    """Passive size added at/near touch concurrent with same-side aggression (spec §4.4)."""

    instrument_id: InstrumentId = _NULL_INSTRUMENT
    price: float = 0.0
    side: str = ""  # "BID" | "ASK"
    added_size: float = 0.0
    concurrent_aggression_volume: float = 0.0
    fresh: bool = False  # fresh vs resting via level lifecycle
    pipeline_version: str = ""


@customdataclass
class PullEvent(Data):
    """Large level removed shortly before price arrival without execution (spec §4.4)."""

    instrument_id: InstrumentId = _NULL_INSTRUMENT
    price: float = 0.0
    side: str = ""  # "BID" | "ASK"
    size_pulled: float = 0.0
    distance_at_pull_ticks: float = 0.0
    pipeline_version: str = ""


EVENT_TYPES = (IcebergEvent, SweepEvent, AbsorptionEvent, ReloadEvent, PullEvent)

ALL_CUSTOM_TYPES = (
    FootprintRowData,
    SessionProfileData,
    BookStateData,
    *EVENT_TYPES,
)
