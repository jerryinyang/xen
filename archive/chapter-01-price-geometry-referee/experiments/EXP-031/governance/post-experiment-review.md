# EXP-031 Post-Experiment Governance Review

**Experiment:** EXP-031 — AVWAP Edge Isolation (Entry-Timing vs Exit-Rule)
**Stage:** 8 (post-experiment)
**Date:** 2026-06-10
**Artifacts reviewed:** `audit.md`, `results.md`, `report.md`, index updates
**Governing checkpoint:** `docs/experiments-docs/checkpoints/2026-06-09-007-avwap-tradability-and-isolation/design.md`

## VERDICT: APPROVE

## Phase Alignment

- **In scope and correctly framed.** EXP-031 is the design §2/§5 edge-isolation experiment. It decomposes the EXP-028 measured per-event excess into entry-timing vs exit-rule contributions. Gross mechanism decomposition; costs/slippage out of scope (EXP-030) — matches design §4/§7.
- **Dependency structure (LOCKED, design §3) respected.** EXP-031 ran regardless of EXP-030 (INCONCLUSIVE). Isolation outcome ISOLATION_READ_UNRESOLVED feeds future scope design as intended by design §9.
- **Phase 007 status updated.** Both Phase 007 experiments (EXP-030, EXP-031) are now complete. The checkpoint status in `docs/experiments-docs/INDEX.md` reflects this.

## Artifact Checks

### Audit (`audit.md`)

| Check | Result |
|-------|--------|
| Thoroughness | PASS — correctness, edge cases, NaN handling, holdout exclusion, look-ahead bias, synthetic-price discipline, frozen inference integrity all checked. |
| Evidence | PASS — specific line numbers, values, and code excerpts in every finding. |
| Severity classification | PASS — 1 Warning (NaN passthrough in Polars `is_not_null`), 2 Info notes. Correctly classified. |
| Numerical validation | PASS — spot checks on 5m H=6 and H=1 decomposition; additivity verification; reconciliation checks; exit-substitution cross-check. |
| Scope compliance | PASS — plan followed, no deviations, budget respected, holdout verified. |

**Finding:** One Warning issue — NaN values in `fh_H` columns pass through `pl.col(fh).is_not_null()` filter in `build_legs` because Polars 1.41.2 treats `float('nan')` as not-null. Affects BTCUSD/4h at H=6 (companion horizon). Classification (ENTRY_DOMINANT) is CI-based and unaffected; the point estimate is NaN but the label is correct.

**Impact on conclusions:** None. The primary domain (5m) and primary horizon (H=6) are clean. The 4h H=6 label is correct. The ISOLATION_READ_UNRESOLVED outcome is driven by the 5m H=1 vs H=6 contradiction, which is unaffected.

### Results Interpretation (`results.md`)

| Check | Result |
|-------|--------|
| Honest reporting | PASS — the horizon flip is stated clearly; unresolved read is not spun as negative. |
| Uncertainty acknowledged | PASS — CIs, sample sizes, and the NaN caveat for 4h are all reported. |
| No overreaching | PASS — the conclusion is ISOLATION_READ_UNRESOLVED, not a false claim of entry or exit dominance. |
| Verdict supported | PASS — the predeclared resolution rule is transparently applied. |
| Next steps reasonable | PASS — proposed experiments are new scopes (fine-grid horizon sweep, exit redesign, HYP-001 test). |

### Report (`report.md`)

| Check | Result |
|-------|--------|
| Self-contained | PASS — question, method, findings, limitations, and recommendations all present. |
| Key plots included | PASS — decomposition stacked and attribution shares referenced. |
| Limitations honest | PASS — horizon sensitivity, 4h NaN caveat, gross-only decomposition, two-horizon limitation. |
| Artifacts linked | PASS — all paths relative. |

### Index Updates

| Check | Result |
|-------|--------|
| `python/experiments/INDEX.md` | PASS — concise row added with title, status, and one-line finding. |
| `docs/experiments-docs/INDEX.md` | PASS — comprehensive section appended with five-field schema. Checkpoint status updated to COMPLETED. |

## Verdict Justification

All governance constraints pass. The audit identifies one Warning (NaN handling in Polars `is_not_null` for the 4h companion-horizon cell), which:
1. Does **not** affect the primary classification (5m primary domain, H=6 primary horizon — both clean).
2. Does **not** affect the phase outcome (ISOLATION_READ_UNRESOLVED, driven by the 5m H=1 vs H=6 contradiction — unaffected).
3. Is correctly documented in all downstream artifacts (audit Warning, results.md caveat, report.md limitation).
4. Has a known fix (`is_finite()` instead of `is_not_null()`) that would produce the same classification.

The experiment conclusion is robust to this issue. APPROVE.
