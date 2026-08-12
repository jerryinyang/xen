# EXP-100 SQL and active-raid scan optimization design

**Date:** 2026-08-12  
**Status:** operator-approved through implementation and verification  
**Scope:** two cumulative, semantics-preserving EXP-100 apparatus optimizations

## Goal

Reduce the post-transaction-batching bottlenecks without changing any research
object, timestamp, status, calculation, event ordering, fence, control, or
estimand.

## Evidence

After source-minute transaction batching, the two-day profile took 24.43 seconds.
The dominant paths were:

| Path | Cumulative time | Calls / context |
|---|---:|---:|
| active-profile update | 13.29 s | 2,880 source minutes |
| SQLite `execute` | 8.49 s | 2,089,754 calls |
| profile-bin range increment | 7.58 s | 289,111 profile-bars |
| active-raid cursor iteration | 6.70 s | 993,670 yielded rows |
| JSON payload decoding | 5.98 s | 1,134,772 decodes |
| second raid-state pass | 3.87 s | 2,880 source minutes |

The first change targets Python-to-SQL call overhead. The second removes one
high-frequency cursor/decode pass. Neither changes active-object lifetime, TPO
membership, or reference-event selection.

## Stage 1 — streaming TPO-bin writes

`Exp100StateStore.increment_profile_bin_range` currently calls
`Connection.execute` once per intersected bin. Replace only that loop with one
`Connection.executemany` call fed by a generator of the same ordered parameter
tuples.

- The SQL text and `ON CONFLICT ... count + 1` rule remain identical.
- Bin indexes remain the inclusive integer range `low..high` in ascending order.
- The generator prevents range materialisation in Python.
- The profile-state conservation update remains a separate keyed statement.
- Existing transaction ownership, rollback, and standalone atomicity remain.
- No SQLite schema, pragma, or journal setting changes.

### Stage-1 safety gate

Before Stage 2:

1. a test must fail because the current path invokes `execute` per bin;
2. exact bin counts, bracket count, and expected TPO total must pass after the
   change, including negative bin indexes;
3. focused and full EXP-100 tests must pass;
4. a fresh three-day TRAIN smoke must match the retained approved smoke exactly
   for every research-bearing field and ordered event;
5. `xen.estimand_validation` must pass with pinned fence and zero cost.

Do not profile Stage 1. A Stage-1 safety failure stops Stage 2.

## Stage 2 — one streaming active-raid pass per source minute

The current source-minute path iterates all active raids once for profile/swing
updates and again for inclusive-return detection. Combine these into one cursor
pass without materialising rows.

For each yielded raid, preserve this per-raid order:

1. apply the source bar to its non-finalized TPO profile;
2. update a confirmed raid's favorable swing extreme;
3. if the raid has not returned, apply the same inclusive return test and persist
   `return_ts_ns` when true.

After the cursor is exhausted, run active-level raid-start/ambiguity detection in
its existing position. New raids created from that level pass therefore remain
ineligible for profile/return processing until the next source minute, exactly as
before.

The three reference-bar selection scans remain unchanged. They are lower
frequency and combine three different eligibility/max-selection operations;
changing them is outside this scope.

### Stage-2 safety gate

Before cumulative profiling:

1. a test must fail because the current source-minute path opens two active-raid
   cursors;
2. processor tests must prove raid state and emissions remain unchanged;
3. focused and full tests must pass;
4. a second fresh three-day TRAIN smoke must match the retained approved smoke
   exactly for every research-bearing field and ordered event;
5. the integrity gate must pass with pinned fence and zero cost;
6. fresh-context QA must approve the cumulative change.

Only after all six checks pass may cumulative profiling begin.

## Output-equivalence contract

Exact equality is required for:

- ordered rows and values in `levels`, `raids`, `tpo_profiles`, and
  `raids_destroyed`;
- every `bar_marks` column except `state_bytes`;
- event-log bytes;
- destroy-control membership and fixed-seed values;
- fence, cost, config, count, and estimand attestations.

`bar_marks.state_bytes` is the existing operator-approved operational exception:
it may reflect SQLite physical page layout. Metadata may differ only in generation
time and runtime/memory telemetry.

## Cumulative profiling

After Stage-2 QA approval, profile the same one-day and two-day cells used by the
prior investigation and run an unprofiled three-day wall-time smoke if the final
safety smoke was profiled differently. Record total time, SQL calls/time, profile
increment time, active-raid cursor/decode time, commit time/count, final live-state
counts, and peak RSS.

No third optimization is authorized by this design.

## Explicit exclusions

- No pruning, timeout, partitioning, stitching, or object-lifetime change.
- No in-memory active-raid list or bin-range list.
- No reference-bar scan change.
- No SQL schema, JSON payload schema, emission schema, or pragma change.
- No TEST/holdout access, cost path, strategy logic, analysis, or full matrix.
- No profiling between Stage 1 and Stage 2.

## Success criteria

- Both red-green test cycles are observed.
- Both three-day safety gates preserve exact research outputs.
- Final estimand validation and fresh QA approve the cumulative change.
- Cumulative profiling is performed only after final safety approval.
- Same final live-state counts and no asymptotic memory increase.
