# EXP-098 — Post-Experiment Governance Review (Stage 8)

**Date:** 2026-06-25 · **Reviewer:** research-pipeline consolidated governance · **Artifacts reviewed:**
`audit.md`, `results.md`, `report.md`, and the index/registry/ledger updates, against `governance-constraints.md`.

## Verdict-forensics check (audit)

- **Per-stratum masking check — present and affirmative.** The audit re-derives the verdict per cell (8/8
  net-positive on both arms) and runs a drop-one masking check (removes the largest contributor; B still confirms,
  no flip) → the pooled portfolio headline is **not** masking heterogeneity. ✅
- **Mechanism statement — present.** Cross-broker (price-structural cost geometry, not feed-specific), aggregation
  (last-close relabel only moves the trailing window → near-inert), and the ~7 Sharpe (structural diversification,
  in-family) are each explained. ✅
- **Gate-shape check — present.** The Sharpe-LB + Calmar-LB gate is the correct instrument for a deployment claim
  and sees the effect; the known mean-carried / median-fragile 1h shape is reproduced and disclosed (not "wrong
  instrument for the shape"). ✅
- **Run autonomously** (not contingent on anyone questioning the result). ✅

## Materiality check

No verdict-material finding. The three audit Info notes (retention slice non-equivalence; disclosure-only
provenance arg; XAUUSD-4h coverage 0.199 within tolerance) are each shown unable to move a verdict-bearing number
(the binding per-arm B band test clears by >3.9 Sharpe-LB margin and survives masking). No finding was
down-classified to avoid a fix-and-rerun. ✅

## Constraint checks (results / report)

- **Honest reporting / no overreaching.** `results.md` reports the binding labels, the broad-based per-cell read,
  and explicitly caveats the retention ratio as a non-like-for-like slice comparison (not "stronger edge"). ✅
- **Real-price discipline.** All metrics on real OHLC; `infr003_holdout_loaded=false` asserted. ✅
- **Non-binding discipline honored.** EXP-097's `DEPLOYABLE_CONFIRMED` is stated unchanged and non-upgradable
  throughout; EXP-098 is framed as a strengthening companion. ✅
- **Per-stratum doctrine.** Per-arm labels emitted separately; portfolio binding with per-cell disclosure +
  masking; overall `CROSS_BROKER_ROBUST` / `AGGREGATION_ROBUST` are explicit named composites, not a collapsed
  binding flag. ✅
- **Follow-ups as new scopes** (forward monitoring; deferred levers; any binding PPS use) — not scope extensions.
  ✅

## Signal-registry disposition check

A registry disposition is recorded (registry-relevant, robustness disclosure):
- **Candidate-family** `cf-mr-001.md` — EXP-098 outcome section added; status stays `DEPLOYABLE` (G-022
  unchanged). ✅
- **Multiplicity-registry** — EXP-098 row updated to the realized outcome; the `AGG-LASTCLOSE` item + PPS
  robustness data source retained (file-drawer). ✅
- **Test-read-ledger** — PPS robustness read recorded as a disclosure: `counted_test_reads=0`, `candidate_slots=0`,
  no stratum tally moves, INFR-003 holdout untouched; the EXP-097 holdout-spent note clarified alongside. ✅
- **Indexes** — `python/experiments/INDEX.md`, master `docs/experiments-docs/INDEX.md` live status, and family
  detail `families/cf-mr-001/INDEX.md` card all updated. ✅

## Verdict

```text
VERDICT: APPROVE
```
