# Governance Review: Experiment EXP-083 — Post-Experiment

**Date:** 2026-06-22
**Review type:** Post-Experiment (consolidated Stage-8)
**Artifacts reviewed:** `audit.md` (incl. the binding **Re-Audit** section), `results.md`, `report.md`, and the index/registry updates (`python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md`, `docs/experiments-docs/families/cf-capgeo-001/INDEX.md`, `docs/signal-registry/candidate-families/cf-capgeo-001.md`, `docs/signal-registry/multiplicity-registry.md`, `docs/signal-registry/test-read-ledger.md`).

## Executive summary

EXP-083 is the Phase 018 HYP-004a TRAIN-only candidate screen. After a first-pass **REVISE** on a Critical verdict-material audit finding, the operator-directed fixes were applied, the experiment was **re-run**, and the **re-audit PASSed**. The binding run (`fa4035f3…`, `SCREEN_DELIVERED`, n_valid=26) is causally sound, holdout-clean, per-stratum, shape-aware, and within budget; the registry disposition is fully recorded. **VERDICT: APPROVE.**

## Constraint checks

| Check | Verdict | Evidence |
|---|---|---|
| Holdout / TEST discipline | PASS | TRAIN sub-split only; `holdout_untouched=true`, `test_stratum_touched=false`, `counted_test_reads=0`; ledger unchanged (all 48 strata 0/2 open). |
| Look-ahead / causality / real-price | PASS | Causal entry+1..cap first-touch, adverse-first P15 fill, real OHLC in ATR units; no synthetic chart price in any metric (re-audit re-confirmed). |
| Per-stratum (LESSON-001) | PASS | Binding outcome per `{substrate × cell × candidate}`; no pooled statistic binding; the verdict is a count over per-stratum valid flags. |
| Determinism / provenance | PASS | `determinism_ok=true` (byte-identical replay); `derive_barriers` sha256 `34d03f45…` asserted == EXP-082 pin; EXP-080/081/082 fingerprints asserted. |
| Single question / no scope creep | PASS | One TRAIN-screen question; the harami dedupe + per-candidate `m_cell` are audit-fixes, not scope expansion. |
| Complexity budget | PASS | 4 stat-method families / 5 plots / 1 new module — within ≤4/≤5/≤2. |

## Verdict-forensics confirmation (Stage-8 mandatory)

- **Per-stratum re-derivation + masking check — PRESENT.** The audit (and `results.md`) foreground that n_valid=26 = **4 S2-PASS (one well-powered AUDUSD-1h harami cell) + 22 S2-DEFERRED (low-n AVWAP-4h, binding S2 not evaluated)**, that all 26 trace to **4 underlying cells** (narrow breadth, no pooled-headline masking), and that **98.2% died at the cheap G-018a screen**. The flat "26 survivors" headline is explicitly not read at face value.
- **Mechanism statement — PRESENT.** Affirmatively established: all 26 survivors are favourable-capture-attributable (`x_fav>0` mean 1.33 ATR, `x_tail≤0`), **0 tail-truncation artifacts** — the EXP-082 trap did not materialise for survivors; and the data-derived D1/D2/D3 earned no distinctive TRAIN support (absent from the binding S2-passed set).
- **Gate-shape check — PRESENT.** The audit flags that the 3 RR S2-passers clear S2 by stop-truncation-to-point-mass (shape-clean but magnitude-unpriced −7.28 ATR/stop), and that for the 22 deferred survivors S2 is structurally not evaluated — distinguishing "shape-clean" from "magnitude-adjudicated," with the magnitude question correctly routed to EXP-084's cost layer.

## Materiality-handling confirmation (Stage-8 mandatory)

The first-pass audit's verdict-material finding (**C1** — entry-identical harami substrates drawing different matched-random nulls, flipping a binding-set member and moving `n_valid`/the pinned sha256) was correctly classified **Critical** and **fixed-and-rerun**, *not* down-classified to a documented Warning. The Warning **W1** (per-cell `m_cell` reuse) was bundled into the same operator-directed re-run. The re-audit affirmatively shows the fixes resolved C1 (harami consolidated to one stratum; inconsistency cannot recur) and that W1's per-candidate `m_cell` flipped no prior survivor. Remaining non-blocking **W2** (VP-POC selection-on-geometry) is shown not to touch the binding set and is carried to EXP-084/parity work. This is correct blocking-authority exercise.

## Signal-registry disposition confirmation (Stage-8 mandatory)

Registry-relevant result; disposition recorded in the same change:
- **candidate-families/cf-capgeo-001.md** — HYP-004a outcome recorded (`SCREEN_DELIVERED`; data-derived thesis unsupported on TRAIN; G-018 decision pending); family stays `REGISTERED`/SCREENING.
- **multiplicity-registry.md** — EXP-083 row advanced to the per-item outcomes (derived D1/D2/D3 non-distinctive/inconclusive — **retained**, never deleted; `/EXIT-RR` + `/EXIT-PARTIAL` the 4 binding survivors; `/EXIT-VP` 1 deferred; `/EXIT-TRAIL`, `/SIZE-VOLADJ` 0); harami slate consolidation recorded (both substrate entries retained).
- **test-read-ledger.md** — EXP-083 TRAIN-only **disclosure** entered; 0 counted reads; all 48 strata stay 0/2 open.

## Verdict

```
VERDICT: APPROVE
```

The screen verdict `SCREEN_DELIVERED` is sound and honestly qualified (TRAIN-only eligibility, not an edge claim); the Critical audit finding was fixed-and-rerun before interpretation; the verdict forensics (per-stratum masking, mechanism, gate-shape) are complete; and the signal-registry disposition is fully recorded. The G-018 decision (decline EXP-084 / ratify a narrow EXP-084 on the 4 conventional AUDUSD-1h survivors) is correctly surfaced as an operator decision and is out of scope for this experiment.
