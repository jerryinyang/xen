# Xen Experiments — Chapter 04 (opens after INFR-010 Phase D)

Per-experiment artifacts live here (`EXP-*/`, `VAL-*/`, `INFR-*/`: design.md, code, results,
report.md). Chapter 03 is archived at `archive/chapter-03-xena-mtfctx/experiments/`; Chapter 02
at `archive/chapter-02-mr-volharv-htfdi/experiments/`. Read `docs/knowledge-base/` before
designing anything.

The chapter substrate is the **INFR-010 migration** (engine → NautilusTrader, data → Bybit
USDT-perp OHLCV universe, anti-survivorship). Chapter 04 research opens only after INFR-010
Phase D (end-to-end VAL) passes; until then only migration INFR/VAL items belong here.

| ID | Family | Status | Verdict |
|----|--------|--------|---------|
| INFR-010 | infrastructure (engine + data migration master plan) | IN PROGRESS — Phase 0 (chapter-03 close) executed 2026-07-14; next Phase A (INFR-011 OHLCV dataset) ∥ Phase B (engine foundation) | design v2 locked (D1–D8); spawns INFR-011..013 + VAL |
