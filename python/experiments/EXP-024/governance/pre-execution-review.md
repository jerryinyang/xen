VERDICT: APPROVE

# Pre-Execution Governance Review: EXP-024

**Experiment:** EXP-024 — AVWAP Event-Edge Dissipation Decomposition
**Review date:** 2026-06-08
**Reviewed artifacts:**

- `python/experiments/EXP-024/scope.md`
- `python/experiments/EXP-024/analysis-plan.md`
- `python/experiments/EXP-024/code/run_experiment.py`
- `docs/experiments-docs/checkpoints/2026-06-08-005-avwap-exit-and-branch-exploration/design.md`

## Decision

APPROVED for manual execution.

## Governance Checks

- **Checkpoint alignment:** PASS. EXP-024 is the Stage A diagnostic required by the active Phase 005 design. It runs no qualification suite and consumes no candidate-screening multiplicity slot.
- **Scope discipline:** PASS. The experiment has one organizing diagnostic question, fixed horizon grid, fixed floors, fixed primary domain, explicit fork criteria, bounded visualisations, and no parameter or exit-rule sweep.
- **Anti-overfitting guardrails:** PASS. The active checkpoint now states that EXP-024 can motivate but not qualify `/EXIT`; EXP-026 must use a predeclared mapping plus design/evaluation split or be labelled exploratory.
- **Holdout exclusion:** PASS. Scope and plan exclude the final 30 percent global holdout. Code uses `load_analysis_data()` to collect only the first-70% chronological slice and rejects horizon contributions beyond the analysis-set end.
- **Temporal and price discipline:** PASS. Domain bars are ordered by real `CloseTime`; event joins are re-validated by `trigger_idx` against reconstructed real-close arrays; all returns use real domain `Close` prices. No synthetic chart prices are used.
- **Plan compliance:** PASS. Code implements dependency gating, EXP-020 metadata reconstruction checks, event/domain join validation, fixed horizon returns, common-set bounded-vs-lifetime contrasts with CIs, fork verdict rows, trend-change return CIs, exposure descriptors, cost attribution, cross-checks to EXP-021, four bounded plots, and run metadata.
- **Code conventions:** PASS. Imports precede constants; output directories are created only in orchestration; helpers return data; progress tracking uses `tqdm`; logging is concise; plotting reuses bounded analysis outputs; no full-data pandas conversion or silent deduplication is present.
- **Numerical safety:** PASS. Empty/insufficient cells remain non-reportable or inconclusive; zero-baseline percentage improvement is not computed; fork (b) cannot be emitted from an underpowered above-floor horizon; floor-straddling cases resolve inconclusive rather than negative.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile python/experiments/EXP-024/code/run_experiment.py` passed.
- Experiment code was not executed, per research-pipeline manual execution gate.

## Amendment: Source-File Filter

After the first manual execution attempt, the EXP-020 metadata gate failed because
`data/timebars/` also contained `timebars_analysis70_*` snapshots. The implementation
now filters source files to the exact `source_file` names recorded in
`python/experiments/EXP-020/results/analysis_metadata.csv` before rebuilding domain
bars. A lightweight metadata-gate probe rebuilt the 12 expected instrument/domain
frames from the four EXP-020 source files and verified 12/12 metadata checks pass.

The Stage 4 verdict remains APPROVE.

## Amendment: Audit-Driven Cross-Check Revision

The post-run audit found that `exp021_crosscheck.csv` compared EXP-024 all-event
`g_all` means against EXP-021 reportable reaction rows, which are filtered by
same-regime control reportability. That comparison is not the matched-event
guardrail required by the approved analysis plan.

The implementation now:

- recomputes EXP-021 `{1,3,6}` event returns only on exact matched reportable
  EXP-021 event keys;
- hard-fails if any matched EXP-021 key is absent from the EXP-020 event table;
- hard-fails if the matched recomputed return differs from EXP-021 by more than
  `1e-6` bps;
- emits `results/event_join_diagnostics.csv` to verify the EXP-020 event to
  EXP-022 lifetime left join preserves row counts and has no duplicate join keys.

Verification: `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile
python/experiments/EXP-024/code/run_experiment.py` passed. The experiment was not
executed inside the pipeline; manual rerun is required before re-audit.

The Stage 4 verdict remains APPROVE.
