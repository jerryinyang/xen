# Post-Experiment Governance Review: EXP-070

**Reviewer:** Pipeline governance (automated Stage 8)
**Date:** 2026-06-18
**Experiment:** EXP-070 — Event-Level Method Calibration (EXP-027-Analog, TRAIN-only)

---

## Review checklist

### 1. Scope integrity

- [x] Hypothesis was testable and stated before results existed.
- [x] Data scope: TRAIN rows only (first 49% per file). Zero TEST/holdout contact confirmed.
- [x] All six P5 TEST-family cells predeclared at D0; no cells added or removed post-data.
- [x] Candidate slots consumed: 0 (methodology experiment, not a signal evaluation).
- [x] TEST reads consumed: 0.
- [x] Holdout never accessed.

### 2. Analysis plan adherence

- [x] Binding FPR object: full conjunction (`ci_low_1s>0 ∧ mean_ci_low_1s>0 ∧ beats_rm_low_1s>0`)
  per D0-amendment-003 — matches predeclared object.
- [x] Binding null: Null-A only per D0-amendment-004 — matches amended predeclaration.
- [x] Null-B reported as advisory contextual diagnostic — not used for gating.
- [x] Calibrated margin: empirical (1 − α₀) quantile of Null-A pseudo-signal median distribution
  — computed per predeclared method.
- [x] TPR/MDE: translation-equivariance shortcut applied to Null-A draws — per predeclared method.
- [x] Temporal stability: four-quarter TRAIN walk-forward — per predeclared method.
- [x] P12 reconciliation: EXP-068 / EXP-061 / EXP-066 targets at 1e-9 — all abs-diffs = 0.0.
- [x] Determinism: 2-cell cross-process replay — byte-identical.

### 3. Audit compliance

- [x] Audit verdict: PASS.
- [x] Warning W1 (design-criteria tension): resolved by D0-amendment-003.
- [x] Warning W2 (Null-B geometry bias): documented, root-cause established, resolved at verdict
  level by D0-amendment-004 (advisory demotion, no code change, no re-run).
- [x] No Critical audit findings outstanding.

### 4. Amendment governance (P15)

- [x] **D0-amendment-003** (2026-06-18): binding FPR object → full conjunction; Null-B RM arm
  symmetrized. Operator-directed after first-run audit. P15 sign-off recorded in amendment
  document. No new multiplicity slot, no TEST read.
- [x] **D0-amendment-004** (2026-06-18): Null-B demoted to advisory; Null-A sole binding null.
  Operator-directed after second-run structural geometry-bias analysis. P15 sign-off recorded
  in amendment document. No re-run, no new multiplicity slot, no TEST read.
- [x] Both amendments are self-consistent: they correct or re-scope the binding control object
  without introducing new candidate definitions, new parameters, or TEST contact.
- [x] The D0 "both-nulls" clause is superseded by D0-amendment-004 on documented terms.

### 5. Results and report

- [x] All six cells classified: GBPUSD-5m PASS, GBPUSD-1h PASS, NZDUSD-1h PASS, NZDUSD-2h PASS,
  GBPJPY-30m PASS, US2000-4h PASS.
- [x] Experiment verdict: CALIBRATION_DELIVERED — correct given all-PASS classification,
  exact P12 reconciliation, and determinism PASS.
- [x] results.md: present; covers FPR table, advisory Null-B explanation, MDE, temporal
  stability, P12 reconciliation, determinism, and EXP-071 freeze inputs.
- [x] report.md: present; covers scope, amendment history, per-cell interpretation,
  EXP-071 authorization, and signal-registry disposition.
- [x] Temporal stability flags disclosed: GROWING (GBPUSD-5m), DECAYING×3 (GBPUSD-1h severe,
  NZDUSD-1h mild, GBPJPY-30m severe), STABLE×2. Flags are contextual — they do not gate
  the calibration verdict but are recorded for EXP-071 interpretation.
- [x] DECAYING-severe cells (GBPUSD-1h final window −0.158 ATR; GBPJPY-30m final window ≈0 ATR)
  are explicitly flagged for weight in EXP-071 TEST interpretation.

### 6. Signal-registry disposition

- [x] Disposition recorded in results.md and report.md: **registry: not applicable —
  calibration/methodology experiment** (0 candidate slots, 0 TEST reads).
- [x] HYP-023 multiplicity-registry row annotated (D0-amendment-003, D0-amendment-004; no new
  row, no outcome row, no item renamed or deleted).
- [x] No candidate-family status change required; EXP-070 gates methodology, not signal validity.
- [x] `test-read-ledger.md`: unchanged (EXP-070 consumes 0 counted reads; the EXP-071 TEST read
  is recorded when EXP-071 executes).

### 7. Index and documentation

- [x] EXP-070 row added to `python/experiments/INDEX.md`.
- [x] EXP-070 card added to `docs/experiments-docs/families/cf-ha-harami-001/INDEX.md`.
- [x] `docs/experiments-docs/INDEX.md` Phase 016 checkpoint status updated to reflect
  EXP-070 CALIBRATION_DELIVERED; EXP-071 authorized.

### 8. Phase-alignment check

- [x] EXP-070 is the Phase 016 method-calibration step (EXP-027-analog), as specified in the
  Phase 016 design and D0-predeclarations.
- [x] CALIBRATION_DELIVERED verdict clears the D0 P7/P8 pre-TEST gate.
- [x] All six P5 cells are PASS; the EXP-071 binding TEST family is frozen (6 cells).
- [x] Calibrated margins for all six cells are finalized; EXP-071 freeze file inputs are complete.
- [x] Phase 016 progresses to EXP-071 (one-shot TEST confirmation of the non-4h FX core under
  `N-PARTIAL-V2A`).

---

## Decision

All checklist items pass. No revisions required.

```text
VERDICT: APPROVE
```

EXP-070 is complete. Phase 016 EXP-071 is authorized to proceed (one-shot TEST
confirmation; binding TEST family = all six P5 cells; EXP-071 freeze file inputs
finalized from this experiment).
