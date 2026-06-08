VERDICT: APPROVE

# Pre-Execution Governance Review: EXP-025

**Experiment:** EXP-025 — AVWAP Line Support/Resistance Direct Test  
**Review date:** 2026-06-08  
**Reviewed artifacts:**

- `python/experiments/EXP-025/scope.md`
- `python/experiments/EXP-025/analysis-plan.md`
- `python/experiments/EXP-025/code/run_experiment.py`
- `docs/experiments-docs/checkpoints/2026-06-08-005-avwap-exit-and-branch-exploration/design.md`
- `.agents/skills/research-pipeline/references/governance-constraints.md`
- `.agents/skills/experiment-developer/references/code-conventions.md`

## Decision

APPROVED. EXP-025 is aligned with Phase 005 Stage A and is ready for manual
execution.

## Governance Checks

- **Scope discipline:** PASS. The scope asks exactly one diagnostic question:
  whether EXP-020 AVWAP bounce trigger bars show direct event-bar AVWAP-line
  rejection versus matched same-regime controls. It does not screen a candidate,
  tune thresholds, compute P&L, or expand into EXP-024/026.
- **Dependency discipline:** PASS. The implementation gates on EXP-020
  `SUPPORTED_FULL` readiness and on EXP-024 being documented and post-governance
  approved.
- **Holdout discipline:** PASS. Domain bars are rebuilt from exact EXP-020
  `source_file` values through `load_analysis_data()`, which applies the
  chronological first-70% analysis slice before collection; reconstructed
  domain counts and min/max `CloseTime` values must match EXP-020 metadata.
- **Temporal and look-ahead discipline:** PASS. Time bars order by `CloseTime`;
  event joins validate `trigger_idx`, `trigger_time`, and `trigger_close`;
  AVWAP/band values are replayed causally per regime from the frozen EXP-020
  anchor math. The primary metric is event-bar `h=0`; no future returns enter
  the score or matching.
- **Real-price discipline:** PASS. The line-rejection score uses real domain
  `High`, `Low`, and `Close`, with AVWAP only as a contemporaneous reference
  line. No synthetic chart prices, fills, costs, stops, targets, or strategy P&L
  are used.
- **Metric and denominator discipline:** PASS. The code implements the scoped
  bullish/bearish score formulas, the fixed non-event/near-trigger exclusions,
  line-proximity rule, 3-control minimum, reportability thresholds, equal-weight
  domain estimator, regime-cluster bootstrap CI, paired sign permutation, Holm
  adjustment, and the 2 bps matching-balance guard.
- **Complexity budget:** PASS. Statistical tests remain within the two-test
  budget: primary paired line-rejection inference and the matching-balance
  diagnostic. The four planned visualisations are implemented, and no shared
  code module is added.
- **Implementation standards:** PASS. Imports and constants have no data-loading
  or output side effects; output directories are created only in orchestration;
  large source files are sliced through the project lazy loader before domain
  aggregation; plotting reuses computed records; there is no pandas conversion,
  silent deduplication, noisy helper output, or repeated heavy data load. The
  multi-file/cell and inference loops use `tqdm`.
- **Static verification:** PASS. `python3 -m py_compile
  python/experiments/EXP-025/code/run_experiment.py` completed successfully.

## Notes

- The pipeline did not execute the experiment code, per the manual execution
  gate.
- The existing worktree contains unrelated modified and untracked files from
  other EXP/strategy-host work; this review did not alter or revert them.
