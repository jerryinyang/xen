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
| INFR-010 | infrastructure (engine + data migration master plan) | **ALL PHASES 0/A/B/C/D/E COMPLETE 2026-07-16** — Phase D (VAL-008) PASS; Phase E (INFR-013) verify PASS | design v2 (D1–D8); Chapter 04 unblocked (checkpoint-013) |
| INFR-011 | infrastructure (OHLCV primary dataset from Bybit trades) | **PHASE A COMPLETE 2026-07-16, verify PASS** — A5 PASS_WITH_EXCLUSIONS (894 ADMITTED + 9 SPEC_INCOMPLETE, 672M bars after EC2 day-hole repair); A6 fence PINNED (`artifacts/fence-manifest.json`, wrapper `xen.nautilus.catalog_fence`); A4 catalog ingested at `data/catalog/` | per INFR-010 §6 Phase A (amended); admission ledger + instrument specs in `artifacts/` |
| INFR-012 | infrastructure (governance rebind — docs/skills/gates) | **PHASE C COMPLETE 2026-07-15, verify PASS** (`results/phase_c_verify.json` — 10/10 checks incl. estimand gate v2 + STUB-fails test) | per INFR-010 §6 Phase C |
| VAL-008 | infrastructure-validation (Phase D end-to-end dry run) | **COMPLETE 2026-07-16 — operator verdict SUPPORTED / Phase D PASS** — gate 39/39 PASS on PINNED attestation; planted leak caught 3/3 blind (BASELINE clear 0/3); destroys collapse 0.977–1.064; STUB correctly fails; 4 NEUTRAL amendments incl. shuffle→derangement control repair (L-10) | apparatus PASS; stack findings §5 of `VAL-008/report.md` (derangement rule, fill-ts semantics, dispose_on_completion, one-node-per-process) |
| INFR-013 | infrastructure (MBP feature-store contracts + skeleton, Phase E) | **COMPLETE 2026-07-16, verify PASS** — `xen.orderflow` package (8 custom Data types + catalog schemas round-trip; config-as-code + `pipeline_version`/`config_hash`; Bybit L2 book reconstruction + `u`-sequence gap ledger; ingest skeleton, 5 detector slots stubbed); sample-day check PASS (SOLUSDT 2023-07-12, 734,622 msgs, 0 gaps, mid-file snapshot exact match; archive deleted — zero bulk data) | per INFR-010 §6 Phase E; NO collection, NO detectors; spec published `docs/references/orderflow-feature-store.md`; report `INFR-013/results/sample_day_report.json` |
