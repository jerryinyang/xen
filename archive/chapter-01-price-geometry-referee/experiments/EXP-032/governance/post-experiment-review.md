# Post-Experiment Governance Review: EXP-032

**Date:** 2026-06-10
**Reviewed artifacts:** `audit.md`, `results.md`, `report.md`,
`python/experiments/INDEX.md` (EXP-032 row), `docs/experiments-docs/INDEX.md`
(EXP-032 section + Phase 009 checkpoint row),
`docs/signal-registry/multiplicity-registry.md` (`CF-AVWAP-001/HOLDOUT-B` row +
header status), against `governance-constraints.md`, the Phase 009 design, and
analysis-plan.md Revision 1.

```text
VERDICT: APPROVE
```

## Audit (Stage 5) — PASS quality confirmed

- All required dimensions covered: correctness, edge cases, NaN handling, the
  sanctioned holdout-access protocol (in place of the standard exclusion rule,
  per the Phase 009 §5 supersession accepted at Stage 4), look-ahead prevention,
  real-price discipline (real-OHLC FH returns; no synthetic prices in scope),
  timestamp alignment (the only bar-index use is the predeclared within-view
  `entry_idx + 12`), determinism, and code standards.
- Evidence is concrete: independent recomputation of every per-event identity
  (max error 0.0), cell aggregates (≤ 4e-15 bps), both content hashes, verdict
  logic replay, weekend-financing hand-check, truncation-flag consistency, and
  boundary/membership checks. Findings correctly classified (0 Critical,
  0 Warning, 4 Info).
- Critically for this experiment: the audit verified the one-shot controls with
  persisted evidence — freeze-before-outcome (manifest hash; mtime 41 s before
  all H2 artifacts and not rewritten), no-second-read (verdict file last), seal
  (one file opened), two-invocation execution — and itself read only persisted
  artifacts, never holdout rows.

## Results interpretation (Stage 6) — honest and anchored

- Verdict HOLDOUT_INCONCLUSIVE follows mechanically from the persisted numbers
  and the locked rule; the interpretation quotes the predeclared Interpretation
  Guide and does not move goalposts (the margin-vs-p distinction is reported as
  predeclared machinery working, not as a near-miss to be argued around).
- Uncertainty fully acknowledged: n=27, CI spans zero, power statement honored,
  alternative explanations (true ≈ +20 bps vs lucky zero-effect draw) stated as
  indistinguishable by design.
- Mandatory R1 disclosures present: F04 ex-post reportability (with the
  pre/post counts 27/27) and F05 calibration fidelity (correctly noted as
  load-bearing only for CONFIRMED).
- Non-binding companions kept non-binding throughout; no promotion language.
- Next steps are new scopes (retrospective, Tier-C routing, optional
  analysis-set-only FH parity), not extensions.

## Documentation (Stage 7) — complete and consistent

- `report.md` is self-contained, embeds 2 of 3 plots with captions, links all
  artifacts by relative path, states the spent-shot/never-upgradable
  consequence, and reproduces no claim absent from results.md/audit.md/raw
  outputs.
- `python/experiments/INDEX.md` row updated SCOPED → HOLDOUT_INCONCLUSIVE
  (shot SPENT) with correct numbers.
- `docs/experiments-docs/INDEX.md`: five-field EXP-032 section appended
  (observations factual, conclusions separated); Phase 009 checkpoint row
  updated to EXECUTED with retrospective pending.
- `multiplicity-registry.md`: `CF-AVWAP-001/HOLDOUT-B` marked COMPLETE —
  HOLDOUT_INCONCLUSIVE, shot SPENT, with the locked consequences; header status
  updated. Slot accounting consistent (1-of-1 programme holdout shot consumed).

## Constraint compliance

- Single hypothesis, family of 1, zero selection inside the experiment: upheld.
- Complexity budget: 1/1 test family, 3/3 plots, 1/1 module — within budget.
- Holdout: the EURUSD read was the sanctioned Phase 009 release (Stage-4
  approved); the seal on BTCUSD/USTEC/XAUUSD verifiably held; the EURUSD
  holdout is now recorded as contaminated-by-disclosure in all three indexes.
- Non-parametric, dependence-aware inference with measured Type-I calibration;
  no academic-finance pitfalls introduced.
- One-shot discipline: the verdict artifact exists; the no-second-read guard is
  active; documentation states in three places that no rerun or second read is
  admissible regardless of outcome.

## Notes (non-blocking)

1. The Phase 009 checkpoint still needs its `retrospective.md` to formally close
   the phase — phase-lifecycle work outside the EXP-032 pipeline, flagged in the
   indexes as pending.
2. Audit Info 2 (verdict turned on the margin, not the p-value) is correctly
   propagated into results.md/report.md wording; future readers should quote
   boot_p only with the margin context, as written.
```text
VERDICT: APPROVE
```
