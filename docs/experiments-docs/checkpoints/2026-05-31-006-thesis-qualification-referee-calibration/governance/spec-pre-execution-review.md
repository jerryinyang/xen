# Pre-Execution Governance Review — Deliverable #2 (Reference-Stack Specification)

**Artifact reviewed:** `docs/experiments-docs/checkpoints/2026-05-31-006-thesis-qualification-referee-calibration/reference-stack-spec.md`
**Phase:** 006 — Thesis-Qualification Referee Calibration
**Gate:** Spec-before-experiment (design.md phase gate 1) — the spec must pass this before any EXP-037 scope is written.
**Date:** 2026-05-31
**Framework:** `research-pipeline/references/governance-constraints.md` + Phase 006 binding constraints.

---

## VERDICT: APPROVE

```text
VERDICT: APPROVE
APPROVED_ARTIFACT: docs/experiments-docs/checkpoints/2026-05-31-006-thesis-qualification-referee-calibration/reference-stack-spec.md
NEXT_STAGE: EXP-037 scope may be created against the frozen reference-stack specification.
```

The revised specification now satisfies the checkpoint's spec-before-experiment gate. It freezes the EXP-036 evidentiary stack as the primary §5.6 calibration object, keeps admissibility fixed, separates null and power calibration, predeclares the calibration harness degrees of freedom, and gives concrete numeric rules for materiality, null validity, compute budget, synthetic mechanisms, and the H0/H1 founding-thesis verdict.

No experiment code was run during this governance pass.

---

## Blocking Issues Resolved

### C1/C2 — Materiality no longer alters the frozen stack

Resolved. The frozen-stack verdict is computed at κ = 0 exactly as EXP-036 did. Proxy costs and net-surplus floors now form a separate materiality-survival axis over executable strategy return `mean(d·r) - κ - η`. `Delta_neutral`, `Delta_control`, and E5 remain unmodified, so the §5.6 calibration still attaches to the stack that actually issued the prior closures.

### C3 — Null preserves episode structure

Resolved. The null no longer permutes row labels. It independently resamples a descriptor stream and a return/control stream, with descriptor blocks snapped to complete state episodes and return blocks drawn on common cross-instrument time indices. The spec now predeclares episode-count, episode-length, autocorrelation, and cross-correlation diagnostics; failed episode diagnostics invalidate trusted FPR for that null family.

### C4 — Synthetic mechanisms are operationalized or excluded

Resolved. Each H0/H1 mechanism now has an explicit observable OHLC planting protocol. Pure variants the next-open -> next-close metric cannot observe are labelled construct-validity diagnostics and excluded from the MDE-spread statistic, preventing tautological zero-power results from being treated as measured stack sensitivity.

### C5 — Founding decision rule is numeric

Resolved. The spec defines per-mechanism MDE as the smallest trusted second-order-holdout magnitude with TPR ≥ 0.80 and Wilson 90% lower bound ≥ 0.60. The H0/H1 sensitivity statistic is `S = max(MDE_m) / min(MDE_m)`, with H1 requiring finite MDEs and `S ≤ 2.0`; H0 follows when the drift anchor is finite but any observable mechanism is undetected at max grid or `S > 2.0`.

---

## Major Issues Resolved

- **M1:** B remains 10,000 for every calibration evaluation; no reduced-bootstrap variant is substituted for the frozen stack.
- **M2:** The compute budget is now derived in full-stack equivalents: cap 1,290 FSE / 30 CPU-hours, with a profiling, downscale, and stop rule before long execution.
- **M3:** Power planting now uses accepted null-resampled series from Part A, not an unresolved "real or null" fork.
- **M4:** The spec separates representation/adjudicability pass rates, cell-level false-pass rates, both-contrast cell pass, and aggregate E5∧E6 stack-level false-pass rates. E6 is no longer described as a per-cell leg.
- **M5:** The second-order holdout is partitioned by seed/configuration and retains all four instruments, preserving the stack's `k = 2 of 4` behavior in the trusted battery.

---

## Governance Checks

- **Holdout discipline:** Approved. The final 30% global market holdout remains excluded before aggregation, resampling, and effect planting.
- **Admissibility fixed:** Approved. Look-ahead, real-price outcomes, timestamp alignment, train/test split, inference unit, and holdout exclusion are not calibrated or softened.
- **Species tagging:** Approved. Null calibration remains trustworthy conditional on null diagnostics; power remains fragile and synthetic-family conditioned.
- **No scalar MDE:** Approved. The spec reports a power surface and uses cross-mechanism MDE sensitivity only for the founding H0/H1 ruling.
- **Economic materiality:** Approved as proxy-regime reporting, not broker-cost truth. Costs are frozen design proxies and do not alter the frozen-stack verdict.
- **Compute budget:** Approved with the explicit profile/downscale/stop rule.
- **Scope:** Approved. The artifact remains a pre-registration spec; it does not create EXP-037 scope, write experiment code, run calibration, re-score closed theses, or access holdout.

## Residual Notes

- The proxy-cost values are governance-frozen modelling proxies, not externally validated transaction-cost estimates.
- Trust in Part A still depends on passing the predeclared null-realism diagnostics. A failed diagnostic produces an untrusted FPR for that null family, not a silent pass.
- If EXP-037 profiling breaches the compute budget after the specified downscale, the correct outcome is a compute-infeasibility finding before execution.

**Decision:** Deliverable #2 is approved and frozen. EXP-037 may now proceed to Stage 1 scope design against this specification.
