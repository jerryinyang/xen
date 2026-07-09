# VAL-007 — Indices-Basket Completion Validation (INFR-005 Gate)

**Class:** VAL — data-admission validation, operator-reviewed, **outside the 8-stage
experiment pipeline**. No candidate, no slot, no edge inference.
**Governing checkpoint:** `docs/experiments-docs/checkpoints/2026-07-05-INFR-005-index-basket-completion/design.md`.
**Precedent (suite lineage):** VAL-005 (INFR-003) — reuses the VAL-001 rev.3 / VAL-003 pure
check functions **and** the full negative-control battery **unchanged**.
**Code:** `python/experiments/VAL-007/code/run_experiment.py`.

## 1. Object

The **6 index symbols** collected by INFR-005 to complete the 10-symbol Indices basket,
each admitted only if all five acceptance gates pass. Broker strings resolved at collection
(auto-fallback in `run-infr005-collection.sh`; see `reports/infr005-resolved.txt`):

| Canonical | Broker string (file) |
| --- | --- |
| AUS200 | AUS200 |
| US30   | US30 |
| EU50   | **STOXX50** |
| GER40  | **DE40** |
| HK50   | HK50 |
| UK100  | UK100 |

These 6 are the validation universe. The 4 already-loaded indices (USTEC/US500/US2000/JP225)
carry VAL-005 admission and are **not** re-validated here.

## 2. Acceptance gates (INFR-005 design §5, VAL-005 analog, unchanged)

| Gate | Criterion |
| --- | --- |
| **G1 — Temporal integrity** | Base-bar schema/monotonicity/OHLC; 15m/1h/4h deployed resamples (min_coverage=0.90) match an independent pandas oracle; no future timestamps; strict-mode prefix-stability proves no look-ahead. |
| **G2 — Admission / negative controls** | VAL-003 rev.3 negative-control battery + golden fixture, unchanged; every injected fault detected. |
| **G3 — Coverage / completeness** | Per-symbol row count, span, gap profile; all 6 present; per-instrument broker-start truncation disclosed (index CFDs are the truncation-prone class → INCONCLUSIVE-not-FAIL). |
| **G4 — Holdout seal** | Final-30% sealed per file at first touch on its own timeline; 0 holdout rows read. |
| **G5 — Determinism** | Deployed resamples reproduce byte-identically on a second pass. |

**Partial PASS allowed per symbol** (design §5): admit passing symbols; hold the rest.
A truncation on an index CFD is a disclosure (G3 INCONCLUSIVE), not a FAIL.

## 3. Holdout discipline

Only the first 70% of each file is ever materialized; the final 30% (global holdout, new
boundary on each file's own 2021-06 → 2026-07-06 timeline) is sealed at first touch and never
inspected. TEST-read ledger extension (6 symbols × {15m,1h,4h}, 0 counted reads) happens on
PASS, at documentation.

## 4. On PASS

Extend `test-read-ledger.md` (6 new strata); flip basket-table statuses to Loaded in
`dataset-reference.md`; flip master-index INFR-005 → COMPLETE; write the retrospective;
unblock EXP-022 (CF-CSRR-001 HYP-002 Indices arm).
