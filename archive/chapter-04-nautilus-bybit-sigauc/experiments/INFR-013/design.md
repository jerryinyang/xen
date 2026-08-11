# INFR-013 — MBP Feature-Store Contracts + Skeleton (INFR-010 §6 Phase E)

**Type:** INFR / apparatus (no research hypothesis, no emissions, no TEST contact)
**Status:** design stub derived from `python/experiments/INFR-010/design.md` §6 Phase E
**Operator approval:** Phase E execution approved 2026-07-16 (Phases 0/A/B/C/D COMPLETE;
Phase D PASS per `python/experiments/VAL-008/report.md`)
**Spec:** `archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-013/orderflow-feature-store.md` (historical ratified proposal)

## Scope (IN)

1. Custom Nautilus `Data` subclasses + serialization registration + catalog schemas:
   footprint rows, `SessionProfileData`, `BookStateData`, five detector event types
   (iceberg / sweep / absorption / reload / pull).
2. Config-as-code: per-instrument thresholds (size buckets, imbalance ratio, absorption),
   snapshot Δt/N, session windows; every record stamped `pipeline_version`.
3. Book reconstruction + sequence-gap handling for the Bybit depth stream
   (snapshot/delta, `u` continuity, resync discipline) — unit-tested on synthetic books
   + ONE sample archive day.
4. Ingest-pipeline skeleton: landing → shared streaming-engine slot → catalog writer;
   five detector slots stubbed (`NotImplementedError`).

## Scope (OUT — deferred to the collection INFR, operator-gated)

Bulk depth download (BTC/ETH/SOL), detector implementations, queue-probabilistic
FillModel, golden-day parity harness, rolling raw-buffer ops, quotes-stream extraction.

## Constraints

- `nautilus_trader==1.230.0` hard pin (INFR-010 R5).
- One `BacktestNode`/process + `dispose_on_completion=False` lessons apply (VAL-008 §5)
  — noted; this INFR runs no BacktestNode.
- **Zero bulk data on disk**: the single sample archive day is downloaded to scratch,
  tested, and deleted; nothing lands under `data/`.
- No detector logic beyond stubs; no new research hypotheses.

## Code placement

- Shared package: `python/src/xen/orderflow/` (`data_types.py`, `config.py`, `book.py`,
  `ingest.py`) — single implementation, two runtimes (spec §7) is the target shape;
  this INFR delivers the batch-side skeleton only.
- Tests: `python/tests/test_orderflow_*.py`; sample-day runner:
  `python/experiments/INFR-013/code/sample_day_check.py`.

## Verify block (stop point)

- [x] Custom-data schemas round-trip through a `ParquetDataCatalog` (write → read → equal) —
      all 8 types, `tests/test_orderflow_datatypes.py` PASS 2026-07-16.
- [x] Book reconstruction passes synthetic-book unit tests (apply/delete/update, crossed-book
      guard, gap detection, snapshot resync) — `tests/test_orderflow_book.py` +
      `tests/test_orderflow_ingest.py` PASS (full suite 169 passed / 3 skipped).
- [x] Sample-day check PASS: SOLUSDT 2023-07-12 ob500 (57.3 MB zip, 734,622 messages,
      0 sequence gaps, 0 crossed/level/size violations, mid-file snapshot matched
      reconstruction exactly, 81,710 BookStateData rows stamped `mbp-store-0.1.0`) —
      `results/sample_day_report.json`; archive + scratch catalog deleted.
- [x] Zero bulk data on disk — nothing under repo `data/`; scratch cleaned.

**VERIFY PASS 2026-07-16 — INFR-013 stops here** (collection + detectors = separate
operator-gated INFR).
