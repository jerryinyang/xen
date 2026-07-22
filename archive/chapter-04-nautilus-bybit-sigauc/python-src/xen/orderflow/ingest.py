"""Ingest-pipeline skeleton: landing → streaming engine → catalog writer (INFR-013).

Implements the batch runtime slot of the "single implementation, two runtimes"
rule (spec §7). The five detector slots are STUBBED — implementations are
deferred to the collection INFR (operator-gated). Wiring, sequencing, and the
catalog write path are real so the collection INFR only fills detector bodies.

NO bulk collection lives here: `iter_landing_messages` reads whatever single
archive file it is pointed at; nothing downloads.
"""

import io
import zipfile
from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path

from nautilus_trader.core.data import Data
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.persistence.catalog import ParquetDataCatalog

from xen.orderflow.book import DepthMessage, L2Book, parse_depth_line
from xen.orderflow.config import PIPELINE_VERSION, InstrumentOrderflowConfig
from xen.orderflow.data_types import BookStateData

_MS_TO_NS = 1_000_000

# ---------------------------------------------------------------------------
# Landing zone reader
# ---------------------------------------------------------------------------


def iter_landing_messages(path: Path) -> Iterator[DepthMessage]:
    """Stream parsed depth messages from one landing-zone archive file.

    Accepts a plain `.data`/`.jsonl` file or a `.zip` containing one such
    member (Bybit `{date}_{symbol}_ob500.data.zip` layout). Streams line by
    line — never materializes the archive in memory.
    """
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
            if len(names) != 1:
                raise ValueError(f"{path}: expected exactly one member, got {names}")
            with zf.open(names[0]) as fh:
                for line in io.TextIOWrapper(fh, encoding="utf-8"):
                    if line.strip():
                        yield parse_depth_line(line)
    else:
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    yield parse_depth_line(line)


# ---------------------------------------------------------------------------
# Detector slots (STUBS — deferred to the collection INFR)
# ---------------------------------------------------------------------------


class StreamingDetector(ABC):
    """One online detector: consumes book updates, emits event Data objects.

    The same subclass instance must be runnable in batch (here) and inside a
    live NautilusTrader Actor (spec §7) — keep all state internal and causal.
    """

    def __init__(self, config: InstrumentOrderflowConfig) -> None:
        self.config = config

    @abstractmethod
    def on_depth(self, ts_event_ns: int, book: L2Book, msg: DepthMessage) -> list[Data]:
        """Process one applied depth update; return zero or more events."""


class IcebergDetector(StreamingDetector):
    def on_depth(self, ts_event_ns: int, book: L2Book, msg: DepthMessage) -> list[Data]:
        raise NotImplementedError("iceberg detector deferred to the collection INFR")


class SweepDetector(StreamingDetector):
    def on_depth(self, ts_event_ns: int, book: L2Book, msg: DepthMessage) -> list[Data]:
        raise NotImplementedError("sweep detector deferred to the collection INFR")


class AbsorptionDetector(StreamingDetector):
    def on_depth(self, ts_event_ns: int, book: L2Book, msg: DepthMessage) -> list[Data]:
        raise NotImplementedError("absorption detector deferred to the collection INFR")


class ReloadDetector(StreamingDetector):
    def on_depth(self, ts_event_ns: int, book: L2Book, msg: DepthMessage) -> list[Data]:
        raise NotImplementedError("reload detector deferred to the collection INFR")


class PullDetector(StreamingDetector):
    def on_depth(self, ts_event_ns: int, book: L2Book, msg: DepthMessage) -> list[Data]:
        raise NotImplementedError("pull detector deferred to the collection INFR")


DETECTOR_SLOTS: tuple[type[StreamingDetector], ...] = (
    IcebergDetector,
    SweepDetector,
    AbsorptionDetector,
    ReloadDetector,
    PullDetector,
)


# ---------------------------------------------------------------------------
# Streaming engine (shared slot)
# ---------------------------------------------------------------------------


class StreamingEngine:
    """Book reconstruction + detector fan-out + BookStateData sampling.

    Detectors default OFF (all slots are stubs in INFR-013). BookStateData
    sampling at the configured snapshot cadence is implemented — it is pure
    bookkeeping off the reconstructed book, and gives the catalog-writer path
    real objects to move. No emission while the book is out_of_sync.
    """

    def __init__(
        self,
        instrument_id: InstrumentId,
        config: InstrumentOrderflowConfig,
        detectors: tuple[StreamingDetector, ...] = (),
    ) -> None:
        self.instrument_id = instrument_id
        self.config = config
        self.detectors = detectors
        self.book = L2Book()
        self._last_sample_ms: int | None = None
        self._prev_bb: tuple[float, float] | None = None
        self._prev_ba: tuple[float, float] | None = None

    def process(self, msg: DepthMessage) -> list[Data]:
        """Apply one depth message; return emitted Data objects (ts-ordered)."""
        self.book.apply(msg)
        out: list[Data] = []
        ts_event_ns = msg.cts_ms * _MS_TO_NS
        if self.book.synced and not self.book.out_of_sync:
            for det in self.detectors:
                out.extend(det.on_depth(ts_event_ns, self.book, msg))
            sample = self._maybe_sample(ts_event_ns, msg.ts_ms)
            if sample is not None:
                out.append(sample)
        return out

    def _maybe_sample(self, ts_event_ns: int, ts_ms: int) -> BookStateData | None:
        interval = self.config.snapshot_interval_ms
        if self._last_sample_ms is not None and ts_ms - self._last_sample_ms < interval:
            return None
        bb, ba = self.book.best_bid, self.book.best_ask
        if bb is None or ba is None:
            return None
        self._last_sample_ms = ts_ms
        n = self.config.snapshot_depth_n
        depth_bid = self.book.depth("BID", n)
        depth_ask = self.book.depth("ASK", n)
        ofi = self._compute_ofi(bb, ba)
        self._prev_bb, self._prev_ba = bb, ba
        return BookStateData(
            instrument_id=self.instrument_id,
            best_bid_price=bb[0],
            best_ask_price=ba[0],
            best_bid_size=bb[1],
            best_ask_size=ba[1],
            spread=ba[0] - bb[0],
            depth_bid=depth_bid,
            depth_ask=depth_ask,
            depth_n=n,
            book_slope=depth_bid / depth_ask if depth_ask > 0 else 0.0,
            ofi=ofi,
            pipeline_version=PIPELINE_VERSION,
            ts_event=ts_event_ns,
            ts_init=ts_event_ns,
        )

    def _compute_ofi(
        self, bb: tuple[float, float], ba: tuple[float, float]
    ) -> float:
        """Cont-style best-level order-flow imbalance vs the previous sample."""
        if self._prev_bb is None or self._prev_ba is None:
            return 0.0
        pb, pa = self._prev_bb, self._prev_ba
        if bb[0] > pb[0]:
            e_bid = bb[1]
        elif bb[0] < pb[0]:
            e_bid = -pb[1]
        else:
            e_bid = bb[1] - pb[1]
        if ba[0] < pa[0]:
            e_ask = ba[1]
        elif ba[0] > pa[0]:
            e_ask = -pa[1]
        else:
            e_ask = ba[1] - pa[1]
        return e_bid - e_ask


# ---------------------------------------------------------------------------
# Catalog writer
# ---------------------------------------------------------------------------


def write_to_catalog(catalog: ParquetDataCatalog, objects: list[Data]) -> None:
    """Write emitted custom Data objects into the Nautilus catalog, grouped by type.

    All types are pre-registered by `@customdataclass` at import; the catalog
    partitions by data type / instrument per its own layout (spec §5.1).
    """
    by_type: dict[type, list[Data]] = {}
    for obj in objects:
        by_type.setdefault(type(obj), []).append(obj)
    for _, group in sorted(by_type.items(), key=lambda kv: kv[0].__name__):
        group.sort(key=lambda o: o.ts_event)
        catalog.write_data(group)


def run_ingest(
    landing_file: Path,
    catalog_path: Path,
    instrument_id: InstrumentId,
    config: InstrumentOrderflowConfig,
    detectors: tuple[StreamingDetector, ...] = (),
    flush_every: int = 500_000,
) -> L2Book:
    """Skeleton batch ingest: one landing archive → streaming engine → catalog.

    Returns the final L2Book (gap ledger + counters) for the caller's
    invariant checks / gap report. Detectors default OFF (stubs).
    """
    catalog = ParquetDataCatalog(str(catalog_path))
    engine = StreamingEngine(instrument_id, config, detectors)
    pending: list[Data] = []
    for msg in iter_landing_messages(landing_file):
        pending.extend(engine.process(msg))
        if len(pending) >= flush_every:
            write_to_catalog(catalog, pending)
            pending = []
    if pending:
        write_to_catalog(catalog, pending)
    return engine.book
