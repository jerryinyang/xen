# Scope Audit Second Opinion

Date: 2026-05-15

Reference scope: `docs/experiments-docs/checkpoints/2026-05-14-001-chart-type-validation/design.md`

## EXP-001

| Audit issue | Assessment | Rationale | Action |
| --- | --- | --- | --- |
| Entropy success threshold is mathematically impossible | Valid | Directional entropy is binary and capped at 1.0. A relative 10% increase over a baseline near 1.0 cannot be achieved while staying within the metric domain. | Replaced the scope criterion with remaining-headroom capture and updated `run_experiment.py` threshold logic. |
| Renko ghost-rate definition structurally inflates ghost count | Valid | Close-based Renko may emit multiple bricks from one source bar. Counting repeated `SourceCloseTime` rows as zero-real-movement ghosts measures construction multiplicity, not empty market movement. | Scope now excludes repeated-source rows from the event ghost denominator; code filters repeated `SourceCloseTime` rows before computing event ghost rate. |
| `head` before chronological sort | Valid | The Phase 1 design requires temporal holdout exclusion. Physical row order is not a safe proxy for chronological order. | Loader now sorts lazily by `CloseTime` before slicing the first 70%. |
| Silent `.unique()` in loader | Valid | Deduplication changes the analysis-set row boundary without a scoped rule or row-count audit. | Removed from EXP-001 loader. Future audit checklist now flags this pattern. |
| LineBreak5 evaluated but excluded from primary verdict | Noise for scope compliance | EXP-001 scope explicitly includes Line Break levels 3 and 5 while naming LineBreak3/Renko as primary hypothesis types. Reporting LineBreak5 as secondary context is within the design, provided it is labeled non-primary. | No code change. Existing `PrimaryForVerdict` field preserves the distinction. |
| Bootstrap with n=4 is coarse | Valid limitation, not a blocker | The design uses four instruments. Coarse intervals should be interpreted cautiously, but the method is transparent and in scope. | No code change. Keep documented in audit/results interpretation. |

## EXP-002

| Audit issue | Assessment | Rationale | Action |
| --- | --- | --- | --- |
| Percentage improvement table divides by zero | Valid | Time-bar hybrid rate and lag are zero by construction because regimes are defined on the time-bar timeline. Percentage improvement is undefined. | Code now emits absolute differences when the baseline is zero and labels `ImprovementKind`. |
| Original cleaner-than-time-bars success criterion is structurally impossible | Valid | Since time bars define the regime timestamps, event charts cannot have lower hybrid rate or lag than zero. The experiment can measure boundary cost, not superiority over the defining baseline. | Scope and analysis plan now frame time bars as a lower bound and use bounded absolute excess criteria. |
| Renko zero-coverage bricks deflate hybrid rate | Valid | Repeated `SourceCloseTime` rows have no elapsed source interval but still entered the denominator. | `compute_hybrid_rate` now excludes zero-coverage rows from the denominator. |
| First chart bar excluded from hybrid rate | Valid minor bias | The first event interval can span source bars and may cross a regime boundary. | `compute_hybrid_rate` now evaluates the first event interval from the analysis timeline start. |
| Bootstrap with n=4 is coarse | Valid limitation, not a blocker | Same small-instrument limitation as EXP-001. | No code change. |

## Proactive Cross-Experiment Checks

| Experiment | Similar issue found | Action |
| --- | --- | --- |
| EXP-003 | Full dataset was collected before slicing the first 70%; loader used silent `.unique()`. | Loader now performs lazy chronological 70% slicing and no silent dedupe. |
| EXP-004 | Full dataset was collected before slicing the first 70%; loader used silent `.unique()`. | Loader now performs lazy chronological 70% slicing and no silent dedupe. |
| EXP-005 | `read_parquet()` materialized the full instrument file before holdout slicing. | Loader now uses lazy chronological 70% slicing. |
| EXP-006 | `read_parquet()` materialized the full instrument file before holdout slicing. | Loader now uses lazy chronological 70% slicing. |

Existing result files for affected experiments should be treated as stale until rerun.
