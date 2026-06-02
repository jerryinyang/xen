---
name: research-pipeline
description: Orchestrate the Xen research experiment lifecycle from idea or EXP-ID through scoped design, analysis planning, implementation, manual execution handoff, audit, interpretation, documentation, and governance review. Use when starting a new experiment, resuming a partial experiment, designing experiment scope, running the research pipeline end to end, continuing an EXP or VAL item, or enforcing the Xen experiment process.
---

# Research Pipeline

Coordinate the experiment workflow. Do not replace specialist skills; route work to them and enforce the project gates.

## Start

1. Read the bundled pipeline config from the directory containing this `SKILL.md`.
   If the file tool cannot resolve skill-relative paths, locate the file whose path
   ends with `/research-pipeline/_pipeline-config.md` and read that match.
2. Read `docs/references/dataset-reference.md`.
3. Read `docs/references/architecture.md`.
4. Read `python/experiments/INDEX.md` to identify existing experiments and the next EXP-ID.
5. Read `docs/experiments-docs/INDEX.md` for current research direction.
6. Read the newest active checkpoint under `docs/experiments-docs/checkpoints/`:
   - use `design.md` for active phase objectives;
   - use `retrospective.md` only for completed phase lessons and redirect decisions.
7. Determine the entry point: new EXP, resume EXP, VAL rerun, scope-only design, or phase batch work.

## Routing

Use these specialists:

| Need | Skill |
| --- | --- |
| Analysis plan or result interpretation | `experiment-quant-analyst` |
| Python implementation | `experiment-developer` |
| Code and result validation | `experiment-auditor` |
| Final report and indexes | `experiment-documenter` |

Suppress any specialist instruction to run standalone governance. The pipeline runs consolidated governance in Stage 4 and Stage 8.

## Experiment IDs

- Use `python/experiments/INDEX.md` as authoritative for EXP numbering.
- Do not reuse IDs.
- For VAL-series reruns, require the user to provide the VAL-ID explicitly.
- Store artifacts under `python/experiments/<ID>/`.
- For VAL scopes, reference the source EXP and list exactly what changed.

## Resume Detection

Inspect `python/experiments/<ID>/` and resume at the first missing or incomplete artifact:

| Missing or incomplete artifact | Resume at |
| --- | --- |
| `scope.md` | Stage 1 |
| `analysis-plan.md` | Stage 2 |
| `code/run_experiment.py` | Stage 3 |
| `governance/pre-execution-review.md` without `VERDICT: APPROVE` | Stage 4 |
| no files in `results/` | Manual execution gate |
| `audit.md` | Stage 5 |
| `results.md` | Stage 6 |
| `report.md` or index updates | Stage 7 |
| `governance/post-experiment-review.md` without `VERDICT: APPROVE` | Stage 8 |

Check artifact existence before reading stage files. Stop at the first missing artifact and route to the matching stage; for example, if `code/run_experiment.py` is absent, resume at Stage 3 instead of trying to read the code file.

Announce the resume point before continuing.

## Stage 1: Scope

Create `python/experiments/<ID>/scope.md`.

1. Clarify the idea with no more than three questions per round.
2. Split broad ideas into one falsifiable question per experiment.
3. State a testable hypothesis, or a precise exploratory question.
4. Define data views, instruments, features, parameters, time range, and exclusions.
   If chart types are in scope, define chart types and parameters explicitly.
5. Include the mandatory exclusion: the final 30 percent global holdout is excluded from all analysis.
6. Define measurable success, failure, and inconclusive criteria.
7. Set the complexity budget for tests, plots, and new code modules.
8. Define metric denominators and zero-baseline behavior before implementation.
9. Use the bundled experiment templates in this skill's `references` directory.
   If needed, locate the file ending with `/research-pipeline/references/experiment-templates.md`.
10. Use the bundled scope-design reference when scope design needs more detailed heuristics.
   If needed, locate the file ending with `/research-pipeline/references/scope-design.md`.

## Stage 2: Analysis Plan

Invoke `experiment-quant-analyst` with the scope and ask it to design the analysis plan.

Expected artifact: `python/experiments/<ID>/analysis-plan.md`.

## Stage 3: Implementation

Invoke `experiment-developer` with the approved scope and analysis plan.

Expected artifact: `python/experiments/<ID>/code/run_experiment.py`.

Require the implementation response to include a code-standards self-check
against `experiment-developer/references/code-conventions.md`, specifically:
organization and sectioning, lazy loading and holdout exclusion, bounded
plotting/data conversion, `tqdm` progress for long loops, concise
logging/output, safe Polars/vectorized performance choices, zero-baseline
handling, and any scope-specific temporal alignment, synthetic-price, or
duplicate-source event-denominator rules.

Before approving implementation, verify that the code follows the project code
conventions: imports before path setup and constants, output directories created
only in orchestration, lazy chronological holdout slicing, bounded memory use,
clear VAL-001-style sectioning for non-trivial scripts, `tqdm` progress for
long-running outer loops, concise logging, no silent deduplication, no
full-data collection before holdout exclusion, no repeated heavy
loads/generation for plotting when the analysis pass already has the data,
finite handling for zero-baseline metrics, and no optimization that changes
sample membership, temporal ordering, denominators, metric definitions,
statistical interpretation, or streaming/causal semantics.

## Stage 4: Pre-Execution Governance

Review `scope.md`, `analysis-plan.md`, and `code/run_experiment.py` against the bundled governance constraints.
If needed, locate the file ending with `/research-pipeline/references/governance-constraints.md`.

Also review the implementation against the developer code conventions and the
active checkpoint `design.md`. Code that creates output directories at import
time, reads or materializes large inputs before the holdout split, converts full
large analysis sets to pandas for plotting, silently deduplicates loader rows,
uses noisy helper-level `print()` output, lacks progress tracking for
multi-minute or multi-iteration loops, keeps avoidable Python row loops over
large frames, vectorizes sequential logic in a way that violates causal or
streaming semantics, or repeats heavy data loads for plots must receive
`REVISE`. If chart-type events are in scope, code that does not define
duplicate-source event denominators must also receive `REVISE`.
Scope criteria that are mathematically unattainable, compare percentage
improvement against a zero baseline, or leave scoped event denominators
undefined must also receive `REVISE`.

Write `python/experiments/<ID>/governance/pre-execution-review.md` with one verdict:

```text
VERDICT: APPROVE
```

```text
VERDICT: REVISE
FAILING_ARTIFACT: <path>
REQUIRED_SKILL: <skill>
ISSUES:
- <specific issue>
```

```text
VERDICT: REJECT
REASON: <brief reason>
```

For `REVISE`, route only the failing artifact to the appropriate specialist with concrete issues. Allow at most two revision cycles before stopping.

## Manual Execution Gate

Do not run experiment code yourself. When Stage 4 approves, tell the user:

```text
Pre-execution review: APPROVED

Experiment: <ID> - <title>
Code: python/experiments/<ID>/code/run_experiment.py
Expected output: python/experiments/<ID>/results/

<one-sentence computation summary>

Please run the experiment code and confirm when complete.
```

Resume only after the user clearly says results are ready.

## Stage 5: Audit

Invoke `experiment-auditor` with scope, plan, code, modified modules, and `results/`.

Expected artifact: `python/experiments/<ID>/audit.md`.

## Stage 6: Interpretation

Invoke `experiment-quant-analyst` with scope, plan, code, results, and audit.

Expected artifact: `python/experiments/<ID>/results.md`.

## Stage 7: Documentation

Invoke `experiment-documenter` with all experiment artifacts.

Expected artifacts:

- `python/experiments/<ID>/report.md`
- updated `python/experiments/INDEX.md`
- updated `docs/experiments-docs/INDEX.md`

## Stage 8: Post-Experiment Governance

Review `audit.md`, `results.md`, `report.md`, and index updates against the bundled governance constraints.
If needed, locate the file ending with `/research-pipeline/references/governance-constraints.md`.

Write `python/experiments/<ID>/governance/post-experiment-review.md` with `APPROVE`, `REVISE`, or `REJECT`. For `REVISE`, route concrete issues to the responsible specialist and allow at most two revision cycles.

## Completion

After post-experiment approval, report:

```text
Experiment <ID> complete.

Phase 1:
- scope.md
- analysis-plan.md
- code/run_experiment.py
- governance/pre-execution-review.md

Phase 2:
- audit.md
- results.md
- report.md
- governance/post-experiment-review.md

Key finding: <one-line summary>
Report: python/experiments/<ID>/report.md
```

## Hard Constraints

- Do not execute experiment code inside the pipeline.
- Do not bypass governance.
- Do not inspect or load the final 30 percent global holdout.
- Use `CloseTime` for temporal ordering of time bars. For chart-type events,
  use `SourceCloseTime` when aligning to real time. Never use bar indices for
  temporal alignment across different data views.
- Do not use information after the event timestamp when analyzing an event.
- Do not accept performance optimizations that compromise correctness,
  accuracy, data integrity, reliability, research interpretation, temporal
  causality, or streamed-data validity.
- Respect the scope's filtering and time range boundaries.
- Do not expand scope after approval. Create a new experiment for follow-up questions.
- Flag phase misalignment with checkpoint objectives before proceeding.
- For Heiken Ashi strategy, signal-quality, or return-evaluation experiments:
  never compute returns from HA prices. Always use
  `RealOpen/RealHigh/RealLow/RealClose` for return evaluation.
- HA synthetic-price distortion experiments may compute `HAClose`-based
  diagnostic returns only when the approved scope explicitly says the metric is
  non-tradable synthetic-price distortion and no P&L or signal validation uses
  those returns.
- For Renko strategy experiments: never compute P&L from brick prices. Use
  `SourceCloseTime` to align each signal to real time-bar prices.
- For chart-type comparisons: always align by timestamp, never by bar count.

## References

| Resource | Read when |
| --- | --- |
| bundled pipeline config in this skill directory | Always |
| `docs/references/dataset-reference.md` | Always |
| `docs/references/architecture.md` | Always |
| bundled experiment templates | Stage 1 |
| bundled scope-design reference | Stage 1 when scope is ambiguous |
| bundled governance constraints | Stage 4 and Stage 8 |
| `python/experiments/INDEX.md` | Start, resume, completion |
| `docs/experiments-docs/INDEX.md` | Start and completion |
| latest checkpoint in `docs/experiments-docs/checkpoints/` | Start and phase alignment |
