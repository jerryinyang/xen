# EXP-100 memory-safe implementation design

**Date:** 2026-08-11  
**Status:** Remediation complete; fresh QA pending before execution  
**Experiment:** EXP-100 — Liquidity sweeps / TPO profile geometry  
**Design authority:** `python/experiments/EXP-100/design.md`, the liquidity-sweep checkpoint, and the Xen research-pipeline contract

## Implementation progress — 2026-08-12

The design is unchanged. Four post-implementation gaps were remediated. No full
EXP-100 execution has been authorized or run.

Completed earlier:

1. **Tasks 1–5** — bounded streaming writers, SQLite live state, online TPO,
   causal processor, one-cell Nautilus runner, and disk-backed future-destroy.
2. **Memory-safety rules** — bounded Python state, streamed outputs, RSS abort
   as incomplete/non-publishable.

Remediation completed 2026-08-12:

3. **Production level catalogue** — `xen.exp100.levels.LevelCatalogue` creates
   previous-period (1H/4H/1D/1W), DST-aware session (Asia/Europe/America), and
   rolling (16–256) levels online; unraided same-side levels supersede as
   `SUPERSEDED_NO_RAID`.
4. **`LEVEL_CLOSE` fix** — confirmation/endpoint use previous completed
   confirmation-reference high/low (higher-degree levels), never the swept
   raid price; audit fields `confirmation_level_high/low` are emitted.
5. **`strong_move` + destroy non-vacuity** — post-confirmation swing extremes
   yield `swing_atr` / `max_excursion_atr` / `strong_move`; destroy deranges
   `swing_atr`, `duration_ns`, and `strong_move`; runner records non-vacuity
   status and fails when eligible rows do not change.
6. **Publication integrity** — pre-publish checks enforce TPO conservation on
   defined profiles and raid/profile/level/event terminal reconciliation.

Verification after remediation:

7. Focused EXP-100 suite: 59 passed (includes catalogue, LEVEL_CLOSE,
   strong_move, and destroy non-vacuity coverage).
8. Related regressions: streaming/foundation/estimand v2 — 17 passed, 1 skipped.
9. Compile checks clean for `src/xen/exp100` and `experiments/EXP-100/code`.

Handoff:

10. Fresh-context QA must review the remediated implementation before any
    execution approval. No full matrix or experiment run may start without
    QA APPROVE and operator execution gate.

## Problem and evidence

The cancelled implementation is not present in the current checkout, and no
cancelled-run log or artifact was found in the repository or temporary workspace.
Therefore this specification does not claim an exact source-line diagnosis of
that run. It addresses the failure using the memory hazards already documented
in the Xen programme and the resource model of Nautilus `BacktestNode`.

The verified hazards are:

1. Materialising an entire bar or schedule stream as Python objects. A prior
   Xen incident expanded 3,625,870 schedule rows into dictionaries and reached
   8.410 GB RSS. Ordered columnar consumption reduced that preparation to
   3.474 GB RSS.
2. Allowing Nautilus to retain all data for a run. `BacktestRunConfig` uses
   `chunk_size=None` for the all-data path; the streaming path clears engine
   data after each chunk while preserving strategy state.
3. Retaining completed events, profile rows, or report inputs in Python until
   the end of the run. This creates a second copy of the experiment evidence
   in addition to the engine and catalogue data.
4. Enabling analysis and account machinery that the apparatus does not use.
   EXP-100 has no trading objective, no fills, and no local accounting. The
   analysis and account paths must not be allowed to dominate its memory use.
5. Running multiple instruments or cells in one process. This violates the
   one-`BacktestNode` process boundary and multiplies native and Python
   retention.

The implementation must also avoid replacing a memory failure with silent data
loss. A memory guard may stop a cell, but a stopped cell is an incomplete,
invalid run; it must never publish a partial result as evidence.

## Goals and non-goals

### Goals

- Keep peak resident memory bounded independently of the number of input bars,
  emitted rows, completed raids, and completed profiles.
- Preserve the EXP-100 causal state machine exactly: decisions use only
  confirmed data at or before the decision bar, and P&L/accounting is not
  introduced.
- Preserve every required observation, level, raid, profile, censoring, and
  integrity record on disk.
- Make output independent of BacktestNode chunk size and deterministic across
  replay processes.
- Fail loudly and invalidate the cell if a configured memory ceiling is
  reached.
- Keep the implementation compatible with emission contract v1 and the
  Nautilus `BacktestNode` execution boundary.

### Non-goals

- Changing the liquidity-sweep mechanism, event definitions, timeframes,
  universe, confirmation methods, TPO rules, or estimand.
- Adding TEST/holdout data, a trading strategy, a cost model, or a value claim.
- Running the full experiment or requesting execution approval as part of this
  implementation change.
- Making the memory ceiling adaptive from observed results. The ceiling is an
  operational safety limit, not a research parameter.

## Chosen architecture

### One bounded cell per process

The runner creates one process for one cell:

`venue × instrument × observation timeframe × level configuration × confirmation method`

The process owns exactly one Nautilus `BacktestNode`. The parent scheduler
passes configuration and paths only; it never loads bars. The default scheduler
concurrency is one cell at a time until the smoke and memory checks establish a
safe host-level budget. Any later parallelism must be bounded by an explicit
worker budget and must not put multiple `BacktestNode` instances in one process.

The Bybit and cTrader scopes remain separate, as required by the design. No
cross-venue catalogue or dataframe is assembled.

### Native BacktestNode streaming

The runner uses Nautilus' native streaming path:

- `BacktestRunConfig(chunk_size=<fixed positive value>,
  dispose_on_completion=False)`;
- `BacktestEngineConfig(run_analysis=False)`;
- a frozen venue account configuration because the apparatus submits no
  orders and has no money-bearing objective; and
- `engine.clear_data()` only through Nautilus' streaming loop, never a manual
  strategy reset.

Chunk boundaries are transport boundaries only. The strategy object, its causal
state, and its state-store connection remain alive for the entire cell. The
first bar of a new chunk is processed as the direct successor of the last bar
of the previous chunk. A test will compare the same synthetic cell under a
small and a large chunk size and require equal ordered output hashes.

The initial chunk size is a documented runner constant, not an auto-tuned value
and not a methodology input. It may be changed for operational benchmarking,
but the selected value is recorded in `run_metadata.json` and does not change
event definitions.

### Streaming output writers

All high-volume outputs use append-only writers backed by Parquet row groups.
The writer accepts one row or a small bounded batch, writes the batch, updates a
streaming row count and digest, and releases the batch. It never accepts a
whole-run dataframe or a list of all rows.

The writer contract is:

- maximum pending rows and maximum pending approximate bytes are fixed;
- a flush occurs when either limit is reached;
- output is written to a cell-local temporary path and atomically finalized
  only after the cell passes its integrity checks;
- an exception leaves a partial marker and prevents publication;
- the finalizer computes file metadata by streaming file chunks, never by
  `read_bytes()` or by loading the complete table.

The writers cover:

- canonical `bar_marks.parquet`;
- canonical empty `fills.parquet`, `orders.parquet`, and
  `positions_ledger.parquet` with the required schemas;
- event/level/raid/profile tables required by the EXP-100 design;
- append-only `event_log.jsonl`; and
- bounded memory telemetry.

The canonical emission adapter will accept these finalized table paths (or a
streaming table source) in addition to its existing in-memory dataframe path.
It will continue to write the same contract-v1 names and metadata. The
implementation must not create a second in-memory copy merely to call the
adapter.

`bar_marks` is one row per completed observation bar, with the compact state
and integrity fields required to audit the stream. One-minute profile
contributions are not retained as Python rows; they are folded into the
profile state store described below.

### Disk-backed live state

The strategy keeps only the current bar, current aggregation buffers, a fixed
ATR/regime history, and the current database batch in Python. Long-lived live
state is held in a cell-local SQLite state store using cursors and keyed rows.
The state store is operational scratch state, not a published evidence table.

The store contains, at minimum:

- active level rows, keyed by immutable `level_id`;
- active raid rows, keyed by immutable `raid_id`, including its level identity;
- profile metadata, including the current profile generation and reset reason;
- sparse TPO bin counts keyed by `(raid_id, profile_generation, bin_index)`;
- terminal/processed keys needed for idempotent finalization; and
- a compact state-store schema/version record.

The processing rules are:

- SQL rows are consumed with cursors, not `fetchall()`, `to_dicts()`, or a
  Python list of all active objects.
- A level remains live until its configured terminal outcome is emitted. A
  superseded, unraided rolling/session level is emitted as a terminal
  `SUPERSEDED_NO_RAID` row and removed; a level with an unresolved raid is
  retained until that raid is resolved or censored.
- A completed raid is emitted and removed after all dependent profile and
  integrity rows are finalized. Its prior-raid count is queried from keyed
  state, not reconstructed from a retained event list.
- A profile reset increments its generation. Old generations are ignored by
  the active profile and deleted only after the new generation is durable, so
  reset semantics do not require rebuilding from historical bars.
- Profile bin updates are batched and upserted. At finalization, ordered SQL
  cursors make the POC, value area, mass mask, gap span, and strict tight-gap
  label without loading all bins into memory.

This gives a fixed-memory execution path even if an unusual market segment
leaves many unresolved objects. Disk use may increase, but memory does not
silently increase with historical length.

### Fixed causal feature state

The implementation retains only the minimum history required by the approved
design:

- Wilder ATR(14) state and its warm-up state;
- at most the trailing 252 completed ATR/close values for the EXP-104 regime
  rank on the same asset and observation timeframe;
- current 1m-to-observation aggregation state; and
- immutable level/configuration descriptors for the current cell.

Regime labels are assigned at raid, excursion, confirmation, and endpoint
using only values available at those events. Warm-up and missing values remain
explicit states. Future bars cannot alter an already emitted label.

The TPO implementation remains online and causal. Each completed 1m bar updates
the active profile's fixed-bin counts once; a new directional maximum resets
the profile generation. The profile interval, bin width, bracket count, POC,
value-area mass, gap mask, and all undefined reasons are emitted from the
state accumulated up to the configured endpoint. No retrospective historical
rebuild is permitted.

## Memory safety and failure semantics

### Resource limits

The runner records a high-water resident-memory sample at every completed input
chunk and at a fixed bar interval. The guard uses the platform-normalized
`ru_maxrss` value, which includes native Nautilus allocations as well as Python
objects. `tracemalloc` may be recorded for diagnostics but is not treated as a
complete memory measure.

The cell has an explicit RSS ceiling and a bounded output-batch ceiling. The
ceiling and sampling settings are recorded in run metadata. The runner also
records counts for open levels, open raids, active profile generations, pending
writer rows, and state-store bytes. These are diagnostics and must not be used
to filter observations.

If RSS or an internal batch limit is exceeded:

1. stop accepting new evidence;
2. close and mark all temporary outputs as incomplete;
3. write a concise failure record with the last processed timestamp, cell
   identity, peak RSS, and the exceeded limit; and
4. exit non-zero without writing a valid `fence_attestation.json` or a valid
   contract-v1 publication.

No partial file is promoted, and no later analysis may treat the cell as a
zero-result cell. A retry must start from a fresh cell directory and replay the
same frozen input.

### Host-level protection

The runner does not launch the full EXP-100 matrix from the implementation
smoke path. Cell execution is sequential by default. A matrix runner may only
increase concurrency after measuring the per-cell high-water RSS and enforcing
an explicit sum-of-worker limits below the host safety budget.

## Methodology invariants

The following are hard invariants and must be asserted by tests or runtime
checks:

- input bars are consumed through Nautilus `BacktestNode`; no vectorized
  substitute is introduced;
- all decisions use confirmed data no later than the decision timestamp;
- timestamps, instrument identity, and observation aggregation remain those in
  the EXP-100 design;
- strict raid crossing, inclusive later return, same-bar ambiguity, multiple
  level attribution, confirmation, breakout, endpoint, censoring, and TPO
  conservation rules are unchanged;
- every level and raid receives an explicit terminal or unresolved state;
- output order is stable and independent of chunk size;
- future-destroy control remains a deterministic zero-fixed-point derangement
  of post-confirmation blocks, preserving the required marginals and counts;
- output contains no fills, no positions, and no local accounting path;
- `cost_model` is exactly `NO_COST_CHARGED`, with the required zero-cost
  disclosure in money-bearing metadata; and
- a memory abort is an invalid/incomplete cell, never an observed null result.

## Alternatives considered

### A. Native streaming plus bounded writers and disk-backed live state — chosen

This preserves one continuous strategy state while removing whole-run Python
retention. It has the smallest methodological surface area and directly uses
the supported Nautilus streaming behavior. SQLite adds controlled I/O, but it
provides a real bound for unresolved levels and sparse profile bins rather than
relying on an optimistic market-activity assumption.

### B. Monthly or daily subprocess checkpoints

This could lower peak memory further, but it introduces serialization and
restart boundaries into a state machine whose levels, raids, ATR warm-up, and
TPO profile identity cross those boundaries. It would require an independent
checkpoint format and more replay-equivalence testing. It remains a fallback
only if native streaming plus the state store cannot meet the measured limit.

### C. Keep all state in Python and add garbage collection

This is rejected. Garbage collection cannot bound retained evidence, native
Nautilus data, or large dataframe copies, and it would leave the known failure
mode intact.

## Test and verification plan

Implementation starts with failing tests. The focused suite will cover:

1. bounded row writers flush at row/byte limits and never retain a completed
   batch;
2. state-store cursor paths do not materialize active levels, raids, or bins;
3. profile reset, value-area, gap, and conservation invariants are unchanged;
4. ATR/regime labels are causal and invariant when future bars are appended;
5. an identical synthetic cell produces identical ordered hashes at small and
   large BacktestNode chunk sizes;
6. the runner sets streaming, no-analysis, frozen-account, and one-node
   settings;
7. memory-limit trips produce an incomplete/non-publishable cell; and
8. the standard emission and estimand smoke checks accept a completed synthetic
   cell with empty fills and positions.

The implementation smoke uses short synthetic data only. It does not generate
the golden QA trace, execute the pinned universe, run the future-destroy
control over the full scope, or request the execution gate.

## Open review points before implementation

- Confirm that the initial fixed chunk size and RSS ceiling are operational
  defaults rather than experiment parameters.
- Confirm that the added SQLite state store is acceptable as scratch state and
  that only its finalized evidence tables are published.
- Confirm that the existing emission adapter may be extended with a streaming
  source while retaining its current dataframe API.

Approval of this specification authorizes test-first implementation of the
memory-safe apparatus. It does not authorize a full EXP-100 execution.
