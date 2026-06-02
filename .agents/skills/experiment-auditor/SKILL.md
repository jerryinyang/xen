---
name: experiment-auditor
description: Audit Xen experiment code, outputs, and result integrity. Use when validating analysis implementation, checking numerical results, reviewing scope compliance, verifying holdout exclusion, finding bugs, assessing statistical assumptions, or responding to prompts such as audit, validate, check code, verify results, test correctness, numerical check, or is this experiment correct.
---

# Experiment Auditor

Validate whether the implementation and results can be trusted. Report findings clearly and proportionately.

## Start

1. Read the shared pipeline config from the sibling `research-pipeline` skill in
   the same skills root. If the file tool cannot resolve sibling skill paths,
   locate the file whose path ends with `/research-pipeline/_pipeline-config.md`.
2. Read `docs/references/dataset-reference.md`.
3. Read the experiment artifacts:
   - `python/experiments/<ID>/scope.md`
   - `python/experiments/<ID>/analysis-plan.md`
   - `python/experiments/<ID>/code/`
   - relevant modified files in `python/src/xen/`
   - `python/experiments/<ID>/results/`
4. Read the bundled audit checklists in this skill's `references` directory.
   If needed, locate the file ending with `/experiment-auditor/references/audit-checklists.md`.

## Audit Workflow

1. Check scope compliance:
   - implementation matches the plan exactly;
   - features, instruments, parameters, filters, and budgets match the scope;
   - no undocumented extra analyses were added.
2. Check data handling:
   - final 30 percent global holdout is excluded;
   - chronological ordering uses `CloseTime`, event timestamp, or `SourceCloseTime` as appropriate;
   - cross-view alignment uses timestamps, never bar indices;
   - real-price outcome discipline: strategy, signal-return, and excursion metrics use scoped real time-bar prices. If chart types are in scope, HA returns use `RealClose`, never `HAClose`; Renko/Line Break signal returns use real prices aligned through `SourceCloseTime`;
   - NaN and missing values are handled explicitly.
3. Check code correctness:
   - formulas, joins, groupings, lag logic, and indices are correct;
   - edge cases are handled;
   - public functions have useful type hints and docstrings;
   - random processes are deterministic.
4. Check code standards against `experiment-developer/references/code-conventions.md`:
   - organization follows the sample structure;
   - non-trivial scripts use clear VAL-001-style sections;
   - output directories are created only in orchestration;
   - large Parquet loads are lazy, column-pruned where practical, sorted before
     holdout slicing, and collected only after the first-70-percent cut;
   - Polars, NumPy, or other vectorized operations replace Python row loops
     where the replacement is causally equivalent;
   - any remaining heavy loops are genuinely sequential/stateful, bounded, and
     tracked with `tqdm` progress;
   - performance optimizations do not change sample membership, temporal
     ordering, denominators, metric definitions, statistical interpretation, or
     streaming semantics;
   - plotting converts only aggregated or deterministically sampled data to
     pandas;
   - heavy loads/generator passes are not repeated solely for plotting;
   - logging/output is concise and traceable.
5. Check numerical outputs:
   - spot-check selected calculations manually or with small samples;
   - verify ranges, counts, p-values, intervals, and effect signs;
   - compare plots against tabular outputs when possible.
6. Check statistical assumptions:
   - sample sizes are sufficient;
   - outliers and dependence risks are acknowledged;
   - chosen methods still fit the data produced.
7. Check result plausibility against project value ranges and schemas from the references.
8. Check derived-view determinism: same input + same parameters = same output, unless the approved scope explicitly requires seeded randomness.

## Report

Create `python/experiments/<ID>/audit.md` using the bundled audit checklists.

Classify findings:

- Critical: blocks interpretation until fixed.
- Warning: may affect results or should be addressed.
- Info: useful context that does not affect trust.

Include exact file paths, functions, result files, and reproduction notes for each finding.

## Constraints

- Do not reinterpret results as final conclusions; leave that to `experiment-quant-analyst`.
- Do not expand the experiment scope.
- Do not inspect the final 30 percent global holdout.
- Prefer concrete evidence over broad style feedback, but treat code-standard
  violations that can change correctness, memory footprint, reproducibility, or
  governance enforcement as audit findings.
- Treat unsafe optimizations as correctness issues, not style issues. Examples
  include vectorized code that uses future rows, batch-only methods presented as
  streaming-safe, silent sampling/deduplication, altered denominators, or
  optimized joins/windows that no longer match the approved temporal alignment.

## References

| Resource | Read when |
| --- | --- |
| shared pipeline config in sibling `research-pipeline` skill | Always |
| `docs/references/dataset-reference.md` | Always |
| bundled audit checklists | Before writing `audit.md` |
| `python/experiments/INDEX.md` | To compare prior experiment patterns |
