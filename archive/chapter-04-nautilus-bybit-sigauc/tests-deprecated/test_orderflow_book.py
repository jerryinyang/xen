"""INFR-013: synthetic-book tests for L2 reconstruction + sequence-gap handling."""

import pytest

from xen.orderflow.book import (
    BookNotSyncedError,
    DepthMessage,
    L2Book,
    parse_depth_line,
)


def _msg(type_: str, u: int, bids=(), asks=(), ts_ms: int = 1000) -> DepthMessage:
    return DepthMessage(ts_ms=ts_ms, cts_ms=ts_ms, type=type_, symbol="TESTUSDT",
                        bids=list(bids), asks=list(asks), u=u, seq=u)


def _synced_book() -> L2Book:
    book = L2Book()
    book.apply(_msg("snapshot", u=100,
                    bids=[(99.0, 1.0), (98.0, 2.0), (97.0, 3.0)],
                    asks=[(101.0, 1.5), (102.0, 2.5), (103.0, 3.5)]))
    return book


def test_snapshot_establishes_book():
    book = _synced_book()
    assert book.synced and not book.out_of_sync
    assert book.best_bid == (99.0, 1.0)
    assert book.best_ask == (101.0, 1.5)
    assert not book.crossed


def test_delta_update_insert_delete():
    book = _synced_book()
    book.apply(_msg("delta", u=101,
                    bids=[(99.0, 5.0), (99.5, 1.0)],   # update + insert
                    asks=[(101.0, 0.0)]))              # delete best ask
    assert book.best_bid == (99.5, 1.0)
    assert book.bids[99.0] == 5.0
    assert book.best_ask == (102.0, 2.5)
    assert book.deltas_applied == 1 and not book.out_of_sync


def test_delta_before_snapshot_raises():
    book = L2Book()
    with pytest.raises(BookNotSyncedError):
        book.apply(_msg("delta", u=5, bids=[(1.0, 1.0)]))


def test_stale_delta_dropped():
    book = _synced_book()
    book.apply(_msg("delta", u=100, bids=[(99.0, 9.0)]))  # u == last_u → stale
    assert book.stale_dropped == 1
    assert book.bids[99.0] == 1.0  # unchanged


def test_sequence_gap_flags_and_ledger():
    book = _synced_book()
    book.apply(_msg("delta", u=103, bids=[(99.0, 9.0)], ts_ms=2000))  # skip 101,102
    assert book.out_of_sync
    assert len(book.gaps) == 1
    gap = book.gaps[0]
    assert (gap.expected_u, gap.received_u, gap.ts_ms) == (101, 103, 2000)
    assert book.bids[99.0] == 9.0  # best-effort apply still happened


def test_snapshot_resyncs_after_gap():
    book = _synced_book()
    book.apply(_msg("delta", u=110, bids=[(99.0, 9.0)]))
    assert book.out_of_sync
    book.apply(_msg("snapshot", u=200, bids=[(90.0, 1.0)], asks=[(91.0, 1.0)]))
    assert not book.out_of_sync and book.synced
    assert book.bids == {90.0: 1.0} and book.asks == {91.0: 1.0}
    assert len(book.gaps) == 1  # ledger persists across resync


def test_u_equals_1_treated_as_snapshot():
    book = _synced_book()
    book.apply(_msg("delta", u=1, bids=[(50.0, 1.0)], asks=[(51.0, 1.0)]))
    assert book.snapshots_applied == 2
    assert book.bids == {50.0: 1.0}


def test_crossed_book_detected():
    book = _synced_book()
    book.apply(_msg("delta", u=101, bids=[(101.5, 1.0)]))
    assert book.crossed


def test_top_n_and_depth():
    book = _synced_book()
    assert book.top_n("BID", 2) == [(99.0, 1.0), (98.0, 2.0)]
    assert book.top_n("ASK", 2) == [(101.0, 1.5), (102.0, 2.5)]
    assert book.depth("BID", 3) == pytest.approx(6.0)
    assert book.depth("ASK", 50) == pytest.approx(7.5)


def test_parse_depth_line_bybit_shape():
    line = (
        '{"topic":"orderbook.500.BTCUSDT","ts":1690000000123,"type":"delta",'
        '"data":{"s":"BTCUSDT","b":[["29000.1","1.5"],["28999.9","0"]],'
        '"a":[["29000.2","2.0"]],"u":4567,"seq":890},"cts":1690000000100}'
    )
    msg = parse_depth_line(line)
    assert msg.symbol == "BTCUSDT" and msg.type == "delta"
    assert msg.ts_ms == 1690000000123 and msg.cts_ms == 1690000000100
    assert msg.bids == [(29000.1, 1.5), (28999.9, 0.0)]
    assert msg.asks == [(29000.2, 2.0)]
    assert msg.u == 4567 and msg.seq == 890
