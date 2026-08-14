# EXP-100 Implementation Handoff — Candidate Amendment Work

> **Created:** 2026-08-13T20:38:39Z  
> **Baseline HEAD:** `477287b81d93b2830e10aaa1384bf469a8908983`  
> **Status:** candidate code is uncommitted; no new experiment output was generated.

## Current position

The final 264-cell cTrader TRAIN emission remains frozen. During this attempt I did **not** launch Nautilus, preflight, matrix, TEST, holdout, or new emission runs. The current worktree contains a candidate implementation for the requested EXP-100 amendments, but the frozen results must not be described as results from this candidate code.

Current modified files:

- `python/src/xen/exp100/config.py`
- `python/src/xen/exp100/levels.py`
- `python/src/xen/exp100/processor.py`
- `python/src/xen/exp100/tpo.py`
- `python/src/xen/exp100/strategy.py`
- `python/experiments/EXP-100/design.md`
- `python/experiments/EXP-100/code/run_experiment.py`

## What was tried

1. **Reviewed the final SoT and QA run 10.** The fresh review returned `REVISE` for excursion-duration semantics and the online-profile boundary.
2. **Updated configuration** for the current amendment set:
   - 1H/4H confirmation references;
   - rolling 7/14/22/252 levels;
   - 50% tight-gap threshold;
   - temporary 1-minute observation validation support.
3. **Updated level construction** for NY 17:00 trading-day/week boundaries and session/rolling handling.
4. **Updated processor behavior** to:
   - use completed observation bars for raid start/return;
   - keep same-bar-return raids live;
   - seed the profile from the bounded current observation window;
   - support 4H references;
   - settle all eligible raids, keeping only the latest expected-side raid primary;
   - compute explicit excursion and swing durations.
5. **Updated schemas/contracts** for `excursion_duration_ns` and `swing_duration_ns`, retaining `duration_ns` as the swing-duration alias.
6. **Updated TPO startup** to return the frozen bin width and use the 50% tightness rule.
7. **Earlier temporary source-minute/TPO variants were restored** before the current candidate edits; no unapproved rerun was used to validate them.

## Verification completed

Passed:

```text
python -m compileall -q python/src/xen/exp100 python/experiments/EXP-100/code
pytest -q tests/test_exp100_features.py tests/test_exp100_levels.py \
  tests/test_exp100_tpo.py tests/test_exp100_matrix_runner.py \
  tests/test_exp100_processor.py tests/test_exp100_runner.py
# 63 passed

git diff --check
```

The processor tests initially exposed three settlement failures and one emission-field failure; those were corrected, and the selected suite then passed.

Not fully green:

```text
pytest -q tests/test_exp100_runner.py tests/test_exp100_control.py
# 15 passed, 1 failed
# failing test: test_destroy_records_singleton_group_as_empty
# cause: destroy_post_confirmation currently raises for a singleton group
```

`control.py` was not changed during this attempt.

## What remains

### Blocking decisions

1. **Choose the result object.** Either:
   - keep the frozen 264-cell emission and revert any result-affecting candidate code; or
   - approve the candidate as the next execution object, complete fresh QA, then rerun the full 264-cell TRAIN matrix.
2. **Do not mix claims.** Candidate-code behavior cannot be attributed to the frozen 264-cell results without a rerun.
3. **Resolve the online-profile finding.** QA run 10 reported an unbounded `SourceMinuteLog`/deferred replay path. The current worktree search does not find that symbol in `tpo.py`, so the reviewer/tree discrepancy must be reconciled by a fresh QA review. The final implementation must demonstrate bounded online state and no historical replay.
4. **Resolve duration contract semantics.** The candidate now computes explicit excursion and swing durations, but the frozen emissions do not contain those new fields. A contract-only interpretation is not validation of the frozen data.

### Required next sequence if the candidate is retained

1. Run a **fresh-context EXP-100 QA review** against the exact final dirty tree; append only to `python/experiments/EXP-100/qa-review.md`.
2. Fix any QA findings, including the singleton destroy-control test if it is in scope.
3. Re-run focused tests and the full relevant Python test suite.
4. Obtain explicit authorization for the full 264-cell TRAIN rerun.
5. Run the matrix with destroy control enabled; validate every cell and the family estimand gate.
6. Only then re-run downstream analysis/documentation. Do not inspect TEST/holdout.

### EXP-101–104

Keep EXP-101–104 as read-only analyses of the frozen EXP-100 data unless the operator explicitly authorizes a new EXP-100 execution object. They must not be presented as validation of the candidate implementation.

## Important references

- QA finding: `.pi/subagents/artifacts/75427d8a_reviewer_0_output.md`
- QA log: `python/experiments/EXP-100/qa-review.md`
- EXP-100 design: `python/experiments/EXP-100/design.md`
- Existing analysis handoff: `docs/superpowers/plans/2026-08-13-exp-100-amendment-13-analysis-handoff.md`
- Processor: `python/src/xen/exp100/processor.py`
- TPO store: `python/src/xen/exp100/tpo.py`
- Matrix runner: `python/experiments/EXP-100/code/run_matrix.py`
