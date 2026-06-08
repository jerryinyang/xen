VERDICT: APPROVE

# Post-Experiment Governance Review: EXP-024

**Experiment:** EXP-024 — AVWAP Event-Edge Dissipation Decomposition  
**Review date:** 2026-06-08  
**Reviewed artifacts:**

- `python/experiments/EXP-024/audit.md`
- `python/experiments/EXP-024/results.md`
- `python/experiments/EXP-024/report.md`
- `python/experiments/INDEX.md`
- `docs/experiments-docs/INDEX.md`
- `docs/signal-registry/multiplicity-registry.md`
- `docs/experiments-docs/checkpoints/2026-06-08-005-avwap-exit-and-branch-exploration/design.md`

## Decision

APPROVED. EXP-024 is complete as a diagnostic experiment with result category
`MIXED_OR_INCONCLUSIVE`.

## Governance Checks

- **Audit gate:** PASS. The rerun resolved the prior critical EXP-021 cross-check
  issue. `audit.md` records PASS with 0 critical issues, 2 warnings, and no
  re-audit requirements.
- **Scope discipline:** PASS. The experiment remains one diagnostic fork
  question. It does not run the frozen suite, does not screen a candidate, and
  does not expand into EXP-025 or `/EXIT`.
- **Checkpoint alignment:** PASS. The report records EXP-024 as Phase 005 Stage A
  diagnostic output and preserves the design's mixed/inconclusive routing rule.
- **Holdout and real-price discipline:** PASS. Audit confirms first-70% analysis
  slice only; returns use real domain Close prices.
- **Interpretation honesty:** PASS. `results.md` and `report.md` state that 5m
  resolves fork (b), 1h/4h remain unresolved, no domain supports fork (a), and
  EXP-026 `/EXIT` is not automatically justified.
- **Documentation:** PASS. `report.md` is present; both experiment indexes record
  EXP-024; the active checkpoint summary no longer says there is no Phase 005
  result.
- **Registry/file-drawer discipline:** PASS. The Phase 005 registry records
  `CF-AVWAP-001/DIAG-001` as completed with `MIXED_OR_INCONCLUSIVE`, and notes
  that `/EXIT` is reserved but not automatically unlocked by EXP-024.

## Verdict Rationale

The completed artifacts consistently support the same governed conclusion:
EXP-024 gives a primary-domain fork (b) diagnostic but not an all-domain fork (b)
or any fork (a) result. The appropriate pipeline consequence is completion of
EXP-024 and continuation to remaining Phase 005 work, not automatic execution of
EXP-026.
