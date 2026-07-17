# Xen Experiments — Master Index (Chapter 04 — opens after INFR-010 Phase D)

Live status + family navigation for the current chapter. Chapter 03 is archived at
`archive/chapter-03-xena-mtfctx/experiments-docs/`; Chapter 02 at
`archive/chapter-02-mr-volharv-htfdi/experiments-docs/`; Chapter 01 at
`archive/chapter-01-price-geometry-referee/experiments-docs/`. Distilled canon:
`docs/knowledge-base/` (read first). Live ledgers: `docs/signal-registry/`.

## Current Checkpoint Status

**INFR-010 Phase D PASSED 2026-07-16 (VAL-008, operator verdict SUPPORTED) — Chapter 04
research may open.** Checkpoint-013 open (HTFCAP/EPSOSC + CAL). **INFR-014 COMPLETE
2026-07-17 — operator ACCEPTED partial pin (QA run 4 APPROVE)** — CLS-FILTER
LOW_ONLY_CERTIFY; CLS-EPISODE TERMINAL; active pin sha256 `ac8a1eb6…`. XENA-HTFCAP may
design on CLS-FILTER low; EPSOSC blocked pending new CAL. **INFR-015 COMPLETE
2026-07-18 — operator ACCEPTED amended pin `abbb1842…` (supersedes `ac8a1eb6…`; audit
CERTIFICATION SOUND). Active certified set: CLS-FILTER low + CLS-EPISODE low. XENA-EPSOSC
unblocked LOW-only — binding caveats: ≥16 gate-band legs (F*), α priced ≤~0.06, 4th
CLS-EPISODE cycle needs family-wise correction.** ch03 pin still VOID.
SPDR-004/005/006 complete (three WORTH_EXPLORING). INFR-013 COMPLETE.

## Current Infrastructure Tasks

| Item | Status | Detail |
|------|--------|--------|
| INFR-010 | Phases 0/A/B/C/D/E **COMPLETE 2026-07-16** | all phases closed (Phase E = INFR-013) |
| INFR-011 | Phase A COMPLETE 2026-07-16 | 894 ADMITTED, 672M bars, fence PINNED `35d3375e…`, catalog at `data/catalog/` |
| INFR-012 | Phase C COMPLETE 2026-07-15 | governance rebind verified 10/10 (`results/phase_c_verify.json`) |
| VAL-008 | COMPLETE 2026-07-16 — **Phase D PASS** | `python/experiments/VAL-008/report.md` |
| INFR-013 | Phase E COMPLETE 2026-07-16 — verify PASS | `xen.orderflow` contracts + skeleton; NO collection/detectors; spec `docs/references/orderflow-feature-store.md`; sample-day report `INFR-013/results/sample_day_report.json` |
| INFR-014 | **COMPLETE 2026-07-17 — pin ACCEPTED (partial)** | QA run 4 APPROVE; CLS-FILTER LOW_ONLY_CERTIFY; CLS-EPISODE TERMINAL; active pin sha256 `ac8a1eb6…`; S1 A-vs-B PASS; `python/experiments/INFR-014/report.md` |
| INFR-015 | **COMPLETE 2026-07-18 — pin `abbb1842…` ACCEPTED** | n_legs_floor F*=16 atop overlap blocks; LOW CERTIFIED (0.025/0.030, ood 0.75), HIGH FAIL_COV; audit SOUND; EPSOSC unblocked LOW-only; `python/experiments/INFR-015/report.md` §9.3 |

## Family Indexes

| Family | Range | Status |
|--------|-------|--------|
| [infrastructure-validation](families/infrastructure-validation/INDEX.md) | VAL-008 | Phase D PASS 2026-07-16 |

New candidate families register at `docs/signal-registry/candidate-families/` when research
opens.

## Checkpoint Retrospectives

None yet this chapter.
