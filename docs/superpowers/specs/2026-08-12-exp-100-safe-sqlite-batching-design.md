# EXP-100 safe SQLite batching design

**Date:** 2026-08-12  
**Status:** operator-approved design; implementation pending written-spec review  
**Scope:** EXP-100 apparatus performance only

## Goal

Reduce EXP-100 wall time without changing any level, raid, confirmation, TPO,
control, emission, fence, or estimand semantics.

## Evidence and root cause

The approved BTCUSDT TRAIN smoke shape showed nonlinear slowdown as live raids
accumulated:

| Window | Wall time | Live raids at final observation |
|---|---:|---:|
| 1 day | 15.7 s | 73 |
| 2 days | 124.7 s | 320 |
| 3 days | ~341 s | 436 |

The two-day profile attributed 72.0 seconds to 348,878 SQLite commits and 38.0
seconds to 2,380,780 SQL executions. Active-profile processing consumed 99.7 of
124.6 profiled seconds. The first intervention therefore targets transaction
frequency; it does not alter active-object lifetime.

## Approved change

Add an explicit source-bar transaction boundary to `Exp100StateStore` and use it
around the state mutations caused by one call to
`Exp100Processor.on_one_minute_bar`.

- Exactly one outer SQLite transaction covers one source minute.
- Store methods retain their existing automatic-commit behavior when called
  outside that boundary.
- Methods that currently open their own transactions participate in the outer
  transaction instead of nesting `BEGIN` statements.
- An exception rolls back all SQLite mutations from that source minute.
- Processing order inside the minute remains unchanged.
- Append-only sink writes remain in their existing order. A failed cell is not
  published, as under the current runner contract.

This is a storage-boundary change only. There is no change to schemas, emitted
columns, timestamps, calculations, status labels, or event identities.

## Explicit exclusions

- No raid, level, or profile pruning.
- No timeout or lifetime change.
- No calendar partitioning or state stitching.
- No in-memory materialisation of all active objects.
- No TEST or holdout access.
- No cost model, strategy, control, analysis, or experiment-design change.
- No second optimization in the same implementation pass.

## Test-first implementation

Before production code changes, add focused tests proving:

1. mutations inside the source-bar boundary are committed together;
2. an exception rolls back raid, level, and profile mutations from that boundary;
3. existing standalone store operations still commit automatically;
4. profile range increments and generation resets work inside the boundary;
5. processor event ordering and emitted rows remain unchanged.

Then implement the minimum transaction-depth/ownership mechanism needed to pass
those tests. No unrelated state-store refactor is in scope.

## Verification gates

1. Run the focused EXP-100 store, processor, TPO, runner, control, level, feature,
   and streaming tests.
2. Re-run the three-day BTCUSDT TRAIN smoke with the frozen cell configuration.
3. Compare the new emission with the retained approved smoke:
   - identical Parquet row counts and values for `bar_marks`, `levels`, `raids`,
     and `tpo_profiles`, except `bar_marks.state_bytes` may differ because it is
     operational telemetry of SQLite's physical page layout;
   - identical ordered event-log payloads with no permitted differences;
   - identical destroy-control output for the fixed seed;
   - metadata differences limited to generation time, runtime/memory observations,
     and run-directory identity.
4. Run `xen.estimand_validation`; `blocking_pass` and zero-cost compliance must
   remain true.
5. Re-profile the same one-day and two-day slices.
6. Run fresh-context QA because a previously traced execution path changed.

Any research-bearing output-value or event-order difference is a failed
optimization, not an acceptable tolerance. The operator approved the sole
operational exception for `bar_marks.state_bytes` on 2026-08-12 after the first
equivalence run showed all other fields exactly equal.

## Later optimization gate

No further optimization is selected in advance. After transaction batching is
verified, the new profile may justify one additional isolated design cycle from:

1. combine repeated cursor passes over active raids without materialising them;
2. reduce TPO-bin SQL statement count while preserving exact integer counts;
3. avoid eager state-count/file-size queries between actual memory samples;
4. tune SQLite journal or temporary-storage settings without weakening rollback
   or atomic publication.

Each candidate requires measured evidence, its own test-first change, exact-output
equivalence, and re-profiling. Options involving partitioning or object-lifetime
changes remain excluded.

## Success criteria

- Exact research-output equivalence on the three-day smoke.
- Passing focused tests, estimand validation, zero-cost check, and fresh QA.
- Lower wall time on the same one-day and two-day profiling cells.
- No increase in asymptotic Python memory use and no governing-constraint change.
