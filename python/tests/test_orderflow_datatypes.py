"""INFR-013: custom Data contracts round-trip through dict, msgpack, and catalog."""

from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.persistence.catalog import ParquetDataCatalog

from xen.orderflow.config import PIPELINE_VERSION
from xen.orderflow.data_types import (
    ALL_CUSTOM_TYPES,
    AbsorptionEvent,
    BookStateData,
    FootprintRowData,
    IcebergEvent,
    PullEvent,
    ReloadEvent,
    SessionProfileData,
    SweepEvent,
)

IID = InstrumentId.from_str("BTCUSDT-LINEAR.BYBIT")


def _sample_instances() -> list:
    """One populated instance of every custom type."""
    common = {"instrument_id": IID, "pipeline_version": PIPELINE_VERSION,
              "ts_event": 1_000_000_000, "ts_init": 1_000_000_001}
    return [
        FootprintRowData(bar_close_ns=2_000_000_000, bar_resolution_s=1, price=50_000.1,
                         bid_volume=1.5, ask_volume=2.5, trade_count=7,
                         max_single_print=0.9, **common),
        SessionProfileData(session_id="UTC_DAY:2023-07-12", session_start_ns=1,
                           session_end_ns=2, poc=50_000.0, vah=50_100.0, val=49_900.0,
                           value_area_pct=0.70, total_volume=1234.5, shape="D",
                           lvn_prices_json="[49950.0]", **common),
        BookStateData(best_bid_price=50_000.0, best_ask_price=50_000.1,
                      best_bid_size=1.0, best_ask_size=2.0, spread=0.1, depth_bid=10.0,
                      depth_ask=12.0, depth_n=50, book_slope=0.833, ofi=-0.5, **common),
        IcebergEvent(price=50_000.0, side="BID", visible_size=5.0, total_filled=25.0,
                     refill_count=4, **common),
        SweepEvent(direction="UP", levels_swept=5, slippage_ticks=5, volume=12.0, **common),
        AbsorptionEvent(price=50_000.0, side_absorbed="ASK", absorbed_volume=99.0, **common),
        ReloadEvent(price=50_000.0, side="BID", added_size=8.0,
                    concurrent_aggression_volume=6.0, fresh=True, **common),
        PullEvent(price=50_010.0, side="ASK", size_pulled=20.0,
                  distance_at_pull_ticks=3.0, **common),
    ]


def test_all_types_covered():
    assert {type(x) for x in _sample_instances()} == set(ALL_CUSTOM_TYPES)


def test_dict_and_bytes_roundtrip():
    for obj in _sample_instances():
        cls = type(obj)
        back = cls.from_dict(obj.to_dict())
        assert back.to_dict() == obj.to_dict(), cls.__name__
        back2 = cls.from_bytes(obj.to_bytes())
        assert back2.to_dict() == obj.to_dict(), cls.__name__
        assert back.ts_event == obj.ts_event and back.ts_init == obj.ts_init
        assert back.pipeline_version == PIPELINE_VERSION


def test_catalog_roundtrip_all_types(tmp_path):
    catalog = ParquetDataCatalog(str(tmp_path))
    objs = _sample_instances()
    for obj in objs:
        catalog.write_data([obj])
    for obj in objs:
        cls = type(obj)
        rows = catalog.query(cls)
        assert len(rows) == 1, cls.__name__
        inner = rows[0].data  # catalog returns CustomData wrappers
        assert type(inner) is cls
        assert inner.to_dict() == obj.to_dict(), cls.__name__
