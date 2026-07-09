# VAL-007 — Indices-Basket Completion Validation (INFR-005 Gate)

**Status:** **PASS (ADMITTED).** All five acceptance gates pass on all 6 new index
symbols. The INFR-005-collected symbols are admitted as canonical Indices-basket data,
completing the 10-symbol basket.
**Date:** 2026-07-06.
**Class:** VAL — data-admission validation, operator-reviewed, **outside the 8-stage
experiment pipeline**. No candidate, no slot, no edge inference.
**Governing checkpoint:** `docs/experiments-docs/checkpoints/2026-07-05-INFR-005-index-basket-completion/design.md`.
**Code:** `python/experiments/VAL-007/code/run_experiment.py`.
**Results:** `python/experiments/VAL-007/results/` (`verdict.json`, `gate_summary.csv`,
`validation_checks.csv`, `negative_controls.csv`, `holdout_seal_manifest.csv`,
`coverage_span.csv`).

---

## 1. Verdict

**PASS (ADMITTED).** G1–G5 all pass on all 6 symbols; 0 missing; 0 holdout rows read; 0
disclosed truncations.

| Gate | Title | Status | Summary |
| --- | --- | --- | --- |
| **G1** | Temporal integrity | **PASS** | 139 checks, 0 FAIL, 0 INCONCLUSIVE |
| **G2** | Negative controls | **PASS** | 23 controls, 0 missed; golden fixture PASS |
| **G3** | Coverage / completeness | **PASS** | 6/6 present; 0 truncations disclosed |
| **G4** | Holdout seal | **PASS** | 6 files sealed; **holdout_rows_read = 0** |
| **G5** | Determinism | **PASS** | 18 two-pass checks, 0 non-identical |

6,115,842 analysis (first-70%) rows validated across 6 index symbols; 2,621,080
final-30% holdout rows sealed at first touch and never inspected.

## 2. Scope as executed

- **Symbols (6):** the INFR-005 additions completing the Indices basket, by their
  **resolved broker strings**: AUS200, US30, **STOXX50** (=EU50), **DE40** (=GER40),
  HK50, UK100. GER40/DE40 is the live DAX 40 — **not** the retired DE30. The 4 already-loaded
  indices (USTEC/US500/US2000/JP225) carry VAL-005 admission and are not re-validated.
- **Broker-string resolution:** `run-infr005-collection.sh` auto-fallback resolved EU50→STOXX50
  and GER40→DE40 (primaries rejected by broker); the other 4 collected under primary names.
  Mapping recorded in `tools/ctrader-cli/reports/infr005-resolved.txt`.
- **Span:** ~5-year target from 2021-06-01; every symbol's m1 history reaches 2021-06-02 —
  **0 truncations** (all 6 supplied the full target start; the truncation-prone index-CFD
  class did not trigger a disclosure this run).
- **Views:** 1-minute base bars; 15m/1h/4h domain bars via `bar_aggregator` (clock-aligned,
  `min_coverage=0.90`), matching an independent pandas oracle.
- **Slice:** first-70% analysis rows only; final-30% sealed at first touch.
- **Suite reuse:** VAL-001 rev.3 / VAL-003 pure check functions **and** the full
  negative-control battery imported **unchanged** from the archived VAL-003 runner; VAL-007
  adds only the 6-symbol file discovery + the INFR-005 collection-date guard.

## 3. Per-symbol coverage & seal

| Symbol (broker) | Canonical | Analysis start | Holdout boundary | Total rows | Analysis (70%) | Holdout (30%, sealed) | Span (days) |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| AUS200  | AUS200 | 2021-06-02 | 2025-01-07 | 1,457,604 | 1,020,322 | 437,282 | 1315 |
| US30    | US30   | 2021-06-02 | 2024-12-11 | 1,782,944 | 1,248,060 | 534,884 | 1288 |
| STOXX50 | EU50   | 2021-06-02 | 2025-01-29 | 985,348   | 689,743   | 295,605 | 1337 |
| DE40    | GER40  | 2021-06-02 | 2024-12-11 | 1,701,658 | 1,191,160 | 510,498 | 1288 |
| HK50    | HK50   | 2021-06-02 | 2024-12-30 | 1,122,912 | 786,038   | 336,874 | 1307 |
| UK100   | UK100  | 2021-06-02 | 2024-12-11 | 1,686,456 | 1,180,519 | 505,937 | 1288 |

## 4. Disposition

INFR-005 **COMPLETE** on VAL-007 PASS. Indices basket now 10/10 admitted (4 VAL-005 +
6 VAL-007). Downstream, at documentation:

1. Extend `docs/signal-registry/test-read-ledger.md` — 6 symbols × {15m,1h,4h} strata, 0 counted reads.
2. Flip `docs/references/dataset-reference.md` basket-table statuses (AUS200/US30/EU50/GER40/HK50/UK100) Pending → Loaded; record resolved broker strings.
3. Flip master-index INFR-005 row → COMPLETE.
4. Unblock **EXP-022** (CF-CSRR-001 HYP-002 Indices arm) — VAL-007 gate satisfied.
