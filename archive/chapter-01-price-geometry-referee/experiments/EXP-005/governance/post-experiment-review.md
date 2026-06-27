# EXP-005 - Post-Experiment Governance Review

**Experiment:** EXP-005 - Near-MDE Realistic-Candidate Detection Anchor
**Stage:** 8 (post-experiment)
**Reviewed artifacts:** `audit.md`, `results.md`, `report.md`, `python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md`
**Checkpoint:** `2026-06-03-002-referee-refinement-and-stringency` (ACTIVE)
**Date:** 2026-06-03

```text
VERDICT: APPROVE
```

---

## Governance Checks

| Check | Result |
| --- | --- |
| Audit completeness | PASS - `audit.md` reviews code, holdout exclusion, temporal alignment, frozen-harness reuse, candidate construction, numerical table consistency, and result plausibility. It records PASS with 0 Critical and 0 Warning issues. |
| Results interpretation | PASS - `results.md` anchors the verdict to the predeclared criteria, reports FPR/TPR values and Wilson precision, includes audit caveats, and does not move goalposts after seeing results. |
| Report completeness | PASS - `report.md` is self-contained, includes method summary, key quantitative results, selected plots, limitations, future implications, and artifact links. |
| Index updates | PASS - `python/experiments/INDEX.md` has a concise EXP-005 row; `docs/experiments-docs/INDEX.md` has the detailed five-field EXP-005 section and updated active checkpoint status. |
| Scope discipline | PASS - Post-execution artifacts stay on the single EXP-005 question: whether the frozen gate detects the predeclared realistic candidate at the EXP-003 MDE. No threshold tuning, lenient-L5 evaluation, strategy tuning, or adoption decision is introduced. |
| Holdout and temporal discipline | PASS - The audit verifies first-70% chronological loading through the frozen helper and real `Close` outcome discipline. The post artifacts do not introduce any new data access or holdout-dependent claim. |
| Statistical honesty | PASS - The conclusion is limited to the scoped candidate class; sub-MDE limitations, candidate-construction caveats, and `block_length = 1` are explicitly recorded. |
| Phase alignment | PASS - The report correctly frames EXP-005 as a Phase 002 characterization result that recommends no adoption and feeds EXP-006/007/008/010/011. |

## Notes

- The supported finding is specific to the predeclared EXP-005 realistic-candidate construction (`p_active=0.80`, `q_match=0.75`) and does not claim live strategy profitability.
- The detailed index now records that EXP-005 closes the keystone for this candidate class while preserving Phase 002's "characterize and recommend, do not adopt" posture.

## Conclusion

All post-execution artifacts satisfy the research-pipeline governance constraints. EXP-005 is approved as complete.
