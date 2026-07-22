"""INFR-013 sample-day check — ONE Bybit depth archive day, then delete.

Downloads a single `{date}_{symbol}_ob500.data.zip` archive into a scratch
directory, replays it through `xen.orderflow` book reconstruction + the
ingest skeleton (BookStateData sampling → scratch ParquetDataCatalog),
verifies invariants, writes a JSON report, and DELETES the archive and the
scratch catalog. Zero bulk data remains on disk (INFR-013 verify block).

Invariants checked:
  I1  first message is a snapshot; book syncs immediately
  I2  zero sequence gaps (or: every gap is ledgered and reported)
  I3  book never crossed while in-sync (checked every message)
  I4  level counts never exceed 500 per side; sizes strictly positive
  I5  every mid-file snapshot matches the reconstructed book exactly
      (strong replay-parity check; Bybit re-sends snapshots periodically)
  I6  catalog round-trip: sampled BookStateData rows read back, count > 0,
      all stamped with the current pipeline_version

Usage:
  uv run python experiments/INFR-013/code/sample_day_check.py \
      --symbol SOLUSDT --date 2023-07-12 --scratch /path/to/scratch \
      --out experiments/INFR-013/results/sample_day_report.json
"""

import argparse
import json
import shutil
import time
import urllib.request
from pathlib import Path

from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.persistence.catalog import ParquetDataCatalog

from xen.orderflow.book import L2Book
from xen.orderflow.config import PIPELINE_VERSION, config_hash, get_config
from xen.orderflow.data_types import BookStateData
from xen.orderflow.ingest import StreamingEngine, iter_landing_messages, write_to_catalog

ARCHIVE_URL = "https://quote-saver.bycsi.com/orderbook/linear/{symbol}/{date}_{symbol}_ob500.data.zip"


def check_day(archive: Path, symbol: str, catalog_path: Path) -> dict:
    """Replay one archive day; return the invariant report dict."""
    iid = InstrumentId.from_str(f"{symbol}-LINEAR.BYBIT")
    cfg = get_config(symbol)
    engine = StreamingEngine(iid, cfg)
    book: L2Book = engine.book
    catalog = ParquetDataCatalog(str(catalog_path))

    n_msgs = 0
    first_is_snapshot: bool | None = None
    crossed_violations = 0
    level_violations = 0
    snapshot_mismatches = 0
    mid_snapshots = 0
    pending = []
    t0 = time.time()

    for msg in iter_landing_messages(archive):
        if first_is_snapshot is None:
            first_is_snapshot = msg.type == "snapshot"
        if msg.type == "snapshot" and book.synced:
            # I5: reconstructed book must equal the re-sent snapshot exactly
            mid_snapshots += 1
            if book.bids != dict(msg.bids) or book.asks != dict(msg.asks):
                snapshot_mismatches += 1
        pending.extend(engine.process(msg))
        if len(pending) >= 100_000:
            write_to_catalog(catalog, pending)
            pending = []
        n_msgs += 1
        if book.synced and not book.out_of_sync:
            if book.crossed:
                crossed_violations += 1
            if len(book.bids) > 500 or len(book.asks) > 500:
                level_violations += 1
    if pending:
        write_to_catalog(catalog, pending)
    elapsed = time.time() - t0

    neg_sizes = sum(1 for s in book.bids.values() if s <= 0) + sum(
        1 for s in book.asks.values() if s <= 0
    )
    rows = catalog.query(BookStateData)
    version_ok = all(r.data.pipeline_version == PIPELINE_VERSION for r in rows)

    report = {
        "symbol": symbol,
        "pipeline_version": PIPELINE_VERSION,
        "config_hash": config_hash(cfg),
        "messages": n_msgs,
        "elapsed_s": round(elapsed, 1),
        "snapshots_applied": book.snapshots_applied,
        "deltas_applied": book.deltas_applied,
        "stale_dropped": book.stale_dropped,
        "sequence_gaps": len(book.gaps),
        "gap_ledger_head": [vars(g) for g in book.gaps[:10]],
        "mid_file_snapshots": mid_snapshots,
        "I1_first_is_snapshot": bool(first_is_snapshot),
        "I2_zero_gaps": len(book.gaps) == 0,
        "I3_crossed_violations": crossed_violations,
        "I4_level_violations": level_violations,
        "I4_nonpositive_sizes": neg_sizes,
        "I5_snapshot_mismatches": snapshot_mismatches,
        "I6_book_state_rows": len(rows),
        "I6_version_stamped": version_ok,
    }
    report["PASS"] = bool(
        first_is_snapshot
        and crossed_violations == 0
        and level_violations == 0
        and neg_sizes == 0
        and snapshot_mismatches == 0
        and len(rows) > 0
        and version_ok
    )
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="SOLUSDT")
    ap.add_argument("--date", default="2023-07-12")
    ap.add_argument("--scratch", required=True, help="scratch dir (archive + catalog live and die here)")
    ap.add_argument("--out", required=True, help="JSON report path")
    args = ap.parse_args()

    scratch = Path(args.scratch)
    scratch.mkdir(parents=True, exist_ok=True)
    archive = scratch / f"{args.date}_{args.symbol}_ob500.data.zip"
    catalog_path = scratch / "sample_day_catalog"
    url = ARCHIVE_URL.format(symbol=args.symbol, date=args.date)

    print(f"downloading {url}")
    urllib.request.urlretrieve(url, archive)
    print(f"downloaded {archive.stat().st_size / 1e6:.1f} MB")

    try:
        report = check_day(archive, args.symbol, catalog_path)
    finally:
        archive.unlink(missing_ok=True)
        shutil.rmtree(catalog_path, ignore_errors=True)
        print("scratch archive + catalog deleted (zero bulk data on disk)")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print(f"PASS={report['PASS']}")


if __name__ == "__main__":
    main()
