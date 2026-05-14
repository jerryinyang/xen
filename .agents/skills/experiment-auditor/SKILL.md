---
name: experiment-auditor
description: Audit TriLattice experiment code, outputs, and result integrity. Use when validating analysis implementation, checking numerical results, reviewing scope compliance, verifying holdout exclusion, finding bugs, assessing statistical assumptions, or responding to prompts such as audit, validate, check code, verify results, test correctness, numerical check, or is this experiment correct.
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
   - relevant modified files in `python/src/`
   - `python/experiments/<ID>/results/`
4. Read the bundled audit checklists in this skill's `references` directory.
   If needed, locate the file ending with `/experiment-auditor/references/audit-checklists.md`.

## Audit Workflow

1. Check scope compliance:
   - implementation matches the plan exactly;
   - features, instruments, levels, filters, and budgets match the scope;
   - no undocumented extra analyses were added.
2. Check data handling:
   - final 30 percent global holdout is excluded;
   - chronological ordering uses `ConfirmTime`;
   - validation status filtering is correct;
   - NaN and missing values are handled explicitly.
3. Check code correctness:
   - formulas, joins, groupings, lag logic, and indices are correct;
   - edge cases are handled;
   - public functions have useful type hints and docstrings;
   - random processes are deterministic.
4. Check numerical outputs:
   - spot-check selected calculations manually or with small samples;
   - verify ranges, counts, p-values, intervals, and effect signs;
   - compare plots against tabular outputs when possible.
5. Check statistical assumptions:
   - sample sizes are sufficient;
   - outliers and dependence risks are acknowledged;
   - chosen methods still fit the data produced.
6. Check result plausibility against project value ranges and enums from the references.

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
- Prefer concrete evidence over broad style feedback.

## References

| Resource | Read when |
| --- | --- |
| shared pipeline config in sibling `research-pipeline` skill | Always |
| `docs/references/dataset-reference.md` | Always |
| bundled audit checklists | Before writing `audit.md` |
| `python/experiments/INDEX.md` | To compare prior experiment patterns |
