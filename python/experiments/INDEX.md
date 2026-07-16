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
| INFR-010 | infrastructure (engine + data migration master plan) | IN PROGRESS — Phase 0 done; Phase B VERIFY PASS 2026-07-14 (`nautilus_trader==1.230.0`); Phase A (INFR-011) parallel | design v2 locked (D1–D8); spawns INFR-011..013 + VAL |
| INFR-011 | infrastructure (OHLCV primary dataset from Bybit trades) | **PHASE A COMPLETE 2026-07-16, verify PASS** — A5 PASS_WITH_EXCLUSIONS (894 ADMITTED + 9 SPEC_INCOMPLETE, 672M bars after EC2 day-hole repair); A6 fence PINNED (`artifacts/fence-manifest.json`, wrapper `xen.nautilus.catalog_fence`); A4 catalog ingested at `data/catalog/` | per INFR-010 §6 Phase A (amended); admission ledger + instrument specs in `artifacts/` |
| INFR-012 | infrastructure (governance rebind — docs/skills/gates) | IN PROGRESS — verify block | per INFR-010 §6 Phase C |
