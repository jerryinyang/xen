"""INFR-013: ingest skeleton — landing reader, engine sampling, detector stubs, catalog."""

import zipfile

import pytest
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.persistence.catalog import ParquetDataCatalog

from xen.orderflow.config import PIPELINE_VERSION, config_hash, get_config
from xen.orderflow.data_types import BookStateData
from xen.orderflow.ingest import (
    DETECTOR_SLOTS,
    StreamingEngine,
    iter_landing_messages,
    run_ingest,
)

IID = InstrumentId.from_str("BTCUSDT-LINEAR.BYBIT")

LINES = [
    '{"topic":"orderbook.500.BTCUSDT","ts":1690000000000,"type":"snapshot",'
    '"data":{"s":"BTCUSDT","b":[["100.0","1.0"],["99.0","2.0"]],'
    '"a":[["101.0","1.0"],["102.0","2.0"]],"u":10,"seq":10},"cts":1690000000000}',
    '{"topic":"orderbook.500.BTCUSDT","ts":1690000000500,"type":"delta",'
    '"data":{"s":"BTCUSDT","b":[["100.0","3.0"]],"a":[],"u":11,"seq":11},'
    '"cts":1690000000500}',
    '{"topic":"orderbook.500.BTCUSDT","ts":1690000001500,"type":"delta",'
    '"data":{"s":"BTCUSDT","b":[],"a":[["101.0","0"]],"u":12,"seq":12},'
    '"cts":1690000001500}',
]


def _write_zip(tmp_path):
    data_path = tmp_path / "2023-07-12_BTCUSDT_ob500.data"
    data_path.write_text("\n".join(LINES) + "\n")
    zip_path = tmp_path / "2023-07-12_BTCUSDT_ob500.data.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(data_path, data_path.name)
    data_path.unlink()
    return zip_path


def test_iter_landing_messages_zip(tmp_path):
    msgs = list(iter_landing_messages(_write_zip(tmp_path)))
    assert [m.type for m in msgs] == ["snapshot", "delta", "delta"]
    assert msgs[0].u == 10


def test_engine_samples_book_state():
    engine = StreamingEngine(IID, get_config("BTCUSDT"))
    out = []
    for line in LINES:
        from xen.orderflow.book import parse_depth_line
        out.extend(engine.process(parse_depth_line(line)))
    # snapshot_interval_ms=1000: sample at snapshot ts and at ts+1500, not ts+500
    samples = [o for o in out if isinstance(o, BookStateData)]
    assert len(samples) == 2
    first, second = samples
    assert first.best_bid_price == 100.0 and first.best_ask_price == 101.0
    assert second.best_ask_price == 102.0  # 101 deleted before second sample
    assert all(s.pipeline_version == PIPELINE_VERSION for s in samples)
    assert second.ts_event == 1690000001500 * 1_000_000


def test_detector_stubs_raise():
    cfg = get_config("BTCUSDT")
    assert len(DETECTOR_SLOTS) == 5
    engine = StreamingEngine(IID, cfg, detectors=tuple(d(cfg) for d in DETECTOR_SLOTS))
    from xen.orderflow.book import parse_depth_line
    with pytest.raises(NotImplementedError):
        engine.process(parse_depth_line(LINES[0]))


def test_run_ingest_end_to_end(tmp_path):
    zip_path = _write_zip(tmp_path)
    catalog_path = tmp_path / "catalog"
    book = run_ingest(zip_path, catalog_path, IID, get_config("BTCUSDT"))
    assert book.synced and not book.out_of_sync and not book.gaps
    assert book.deltas_applied == 2
    rows = ParquetDataCatalog(str(catalog_path)).query(BookStateData)
    assert len(rows) == 2
    assert rows[0].data.pipeline_version == PIPELINE_VERSION


def test_config_hash_deterministic_and_per_symbol():
    a, b = get_config("BTCUSDT"), get_config("ETHUSDT")
    assert config_hash(a) == config_hash(a)
    assert config_hash(a) != config_hash(b)
    with pytest.raises(KeyError):
        get_config("NOPEUSDT")
