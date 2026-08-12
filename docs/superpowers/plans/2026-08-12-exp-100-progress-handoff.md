# EXP-100 Progress Handoff — optimized apparatus ready for execution

> **Authoritative resume document as of 2026-08-12.** Resume through the Xen
> `research-pipeline`; do not re-implement or redesign the apparatus. The operator has
> approved the completed safe optimizations and stated that execution commences after
> this handoff is updated and the pending changes are committed. This document does not
> itself launch the full matrix. TEST/holdout remains forbidden.

**Experiment:** EXP-100 — Liquidity-sweep streaming apparatus  
**Family:** `CF-LIQSWP-001/HYP-000`  
**Checkpoint:** `2026-08-11-019-liquidity-sweeps`  
**Pipeline stage:** post-implementation, post-optimization, post-QA; full TRAIN execution next

## One-line status

**The apparatus and all three semantics-preserving speedups are QA-APPROVED; exact
three-day safety smokes and their integrity gates passed. No full matrix has run. Resume
at TRAIN execution, then validate every emitted cell before analysis.**

## Pipeline position

```text
1 Design .............. DONE
2 QA pre-exec ......... DONE  (qa-review.md through run 7 — APPROVE)
3 Execute ............. PARTIAL  (safety smokes only; full matrix next)
4 Estimand gate ....... DONE for safety smokes; REQUIRED per full-run cell
5 Data analysis ....... NOT STARTED
6 Document ............ NOT STARTED
```

| Gate | Status |
|---|---|
| Apparatus implementation | Complete |
| Safe performance optimization | Complete and approved |
| Fresh-context QA | Run 7 **APPROVE**, no blocking findings |
| Full TRAIN execution | Operator directed this to commence after the handoff commit; not started here |
| TEST / holdout | **Forbidden**; both programme holdout shots are already spent |
| Final experiment verdict | Not available until full execution, validation, and analysis |

## Retained implementation

- Memory-bounded runner: one `BacktestNode` per process, streaming input, SQLite live
  state, bounded Parquet/JSONL writers, RSS abort to an incomplete cell.
- Production level catalogue: previous 1H/4H/1D/1W, DST-aware sessions, and rolling
  16–256 observation bars (`python/src/xen/exp100/levels.py`).
- Raid lifecycle on source 1m bars: strict excursion, inclusive return, and same-minute
  `AMBIGUOUS_INTRABAR` handling.
- `BREAKOUT_BAR` and `LEVEL_CLOSE` confirmations, online TPO conservation, value-area
  and gap rules, excursion/swing outcomes, future-destroy control, and atomic publication.
- Smoke-discovered max-excursion reset fix: `update_raid` receives only mutable fields;
  immutable `raid_id` and `level_id` are never rewritten.

The governing methodology, object lifetimes, emission schemas, TRAIN fence, zero-cost
model, controls, event order, and estimands remain unchanged.

## Completed performance work

The original bottleneck was repeated SQLite work inside a source-minute loop whose cost
grows with the number of active raids. Three bounded, semantics-preserving changes are
now implemented:

1. **Source-minute transaction batching:** all SQLite mutations for one source minute
   share one outer transaction; standalone store operations still commit atomically and
   exceptions roll back the whole minute.
2. **TPO-bin bulk submission:** ordered inclusive bin upserts use a generator-fed
   `executemany`; no bin list is materialized and conservation totals are unchanged.
3. **Single active-raid pass:** profile, swing, and return processing share one streaming
   cursor in the original order. Operational raid-count telemetry uses an exact scalar
   SQL count instead of decoding every active payload.

Approved design records:

- `docs/superpowers/specs/2026-08-12-exp-100-safe-sqlite-batching-design.md`
- `docs/superpowers/plans/2026-08-12-exp-100-safe-sqlite-batching.md`
- `docs/superpowers/specs/2026-08-12-exp-100-sql-and-scan-optimization-design.md`
- `docs/superpowers/plans/2026-08-12-exp-100-sql-and-scan-optimization.md`

### Measured cumulative effect

All profile timings below use the same real-catalog slices and include profiler overhead.
The unprofiled wall readings are included to make the operational effect clear.

| Slice | Original | After transaction batching | Final cumulative |
|---|---:|---:|---:|
| 1 day | ~15.7 s | 4.23 s profile / 4.34 s wall | **3.48 s profile / 3.60 s wall** |
| 2 days | ~124.7 s | 24.43 s profile / 24.55 s wall | **19.57 s profile / 19.69 s wall** |
| 3 days | ~341 s wall | 55.41 s wall | exact final safety smoke completed; not separately timed |

For the two-day slice, direct SQLite `execute` calls fell from about 2.09 million after
transaction batching to about 786 thousand, while TPO writes moved to `executemany`.
Active-raid iterator yields fell from about 994 thousand to 342 thousand. Final one- and
two-day state counts were unchanged. Peak RSS stayed near 300 MiB, with only small
allocator/layout variation and no new asymptotic structure.

The methodology-required work still scales with active raids. These changes remove
duplicated storage and scan overhead; they do not claim that every full-window matrix
cell will be fast. Execution must retain the existing RSS abort and should record cell
runtime and peak memory.

## Safety and QA evidence

- Stage 1 and final cumulative three-day smokes exactly matched the retained research
  outputs: ordered `levels`, `raids`, `tpo_profiles`, fixed-seed `raids_destroyed`, and
  every `bar_marks` field except the explicitly permitted `state_bytes` telemetry.
- Event log was byte-identical: SHA-256
  `24ce58a1e6df2b5ed4b6953dbf28c8552de0dc187ba4d8463a78b9065b10cbe7`.
- `state_bytes` differed in 24 of 288 rows because transaction timing changes SQLite
  page layout. It is operational telemetry, not a research input or result.
- Both safety-smoke integrity checks passed: pinned TRAIN fence, schema and
  reconciliation valid, zero cost charged, `blocking_pass=true`.
- QA run 6 approved transaction batching; its correction addendum documents the
  `state_bytes` exception. QA run 7 approved the cumulative TPO and active-raid changes
  with no blocking findings.
- Final local verification after implementation: **299 passed, 5 skipped**; Ruff clean.
  The single warning is the existing NumPy warning in `test_xena_search.py`.

The append-only evidence is in `python/experiments/EXP-100/qa-review.md`.

## Retained smoke record

```text
run_dir: data/nautilus_runs/exp100_smoke/BTCUSDT_15m_BREAKOUT_PREVIOUS_1H_2023-12-01_2023-12-04
instrument: BTCUSDT-LINEAR.BYBIT
venue: BYBIT
observation_minutes: 15
confirmation_method: BREAKOUT_BAR
confirmation_reference: 1H
level_config: PREVIOUS_1H
start: 2023-12-01T00:00:00+00:00
end: 2023-12-03T23:59:00+00:00
destroy_control: yes
cost_model: NO_COST_CHARGED
fence: PINNED
estimand_validation: blocking_pass true
```

| Stream | Rows / note |
|---|---|
| bar_marks | 288 |
| levels | 144 |
| raids | 1,561 |
| tpo_profiles | 1,561 |
| fills / orders / positions | 0 |
| destroy | 28 eligible rows changed; 0 fixed points |

The retained integrity artifact is
`python/experiments/EXP-100/results/estimand_validation_smoke.json`.
Temporary optimization smoke/profile directories under `/tmp` are QA evidence only and
must not be treated as durable experiment emissions.

## What has not been done

- Full EXP-100 TRAIN matrix execution.
- Multi-cell orchestration beyond the one-cell CLI.
- Integrity validation of full-run cells.
- Raw-data interrogation and `analysis.md`.
- Operator verdict, `report.md`, or completion index updates.
- Any family-status change.

## Execution resume contract

Read, in order:

1. This handoff.
2. `python/experiments/EXP-100/design.md`.
3. `python/experiments/EXP-100/qa-review.md`, especially runs 6–7 and the run-6
   correction addendum.
4. The four optimization spec/plan files listed above.
5. `python/experiments/EXP-100/code/run_experiment.py`.

Then execute only the matrix defined by the approved design:

1. Use TRAIN data only and preserve the pinned fence.
2. Run one `BacktestNode` per process and a unique output directory per cell.
3. Keep `--destroy-control`, the zero-cost model, RSS abort, and atomic publication.
4. Do not reuse partial work directories as complete emissions.
5. Record wall time and peak RSS; stop and report if a cell hits the memory abort or if
   projected runtime makes the approved matrix operationally infeasible.
6. Run the estimand integrity gate on every completed emission before analysis.
7. Do not contact TEST/holdout, analyze partial cells as final evidence, or change the
   design to make execution finish.

If matrix orchestration code is required, keep it mechanical: expand only the approved
design grid, invoke the existing one-cell CLI in isolated processes, and add no research
logic. Any non-mechanical design or lifetime change requires a design amendment and fresh
QA.

## Key paths

| Role | Path |
|---|---|
| Design | `python/experiments/EXP-100/design.md` |
| QA log | `python/experiments/EXP-100/qa-review.md` |
| Runner | `python/experiments/EXP-100/code/run_experiment.py` |
| Package | `python/src/xen/exp100/` |
| Original implementation spec | `docs/superpowers/specs/2026-08-11-exp-100-memory-safe-implementation-design.md` |
| Original implementation plan | `docs/superpowers/plans/2026-08-11-exp-100-memory-safe-implementation.md` |
| Checkpoint source of truth | `docs/experiments-docs/checkpoints/2026-08-11-019-liquidity-sweeps/` |
| Smoke integrity result | `python/experiments/EXP-100/results/estimand_validation_smoke.json` |

## Suggested next-session goal

```text
Resume EXP-100 from the execution stage using
docs/superpowers/plans/2026-08-12-exp-100-progress-handoff.md. Run only the approved
TRAIN matrix with one BacktestNode per process, unique cell directories, destroy control,
RSS protection, and per-cell estimand validation. Do not contact TEST/holdout or change
the methodology. Stop and report any failed integrity gate, memory abort, or operationally
infeasible runtime before analysis.
```

## Changelog

| When | What |
|---|---|
| 2026-08-12 | Initial handoff after QA run 5 and the retained real-catalog smoke. |
| 2026-08-12 | Updated after transaction batching, TPO-bin bulk writes, active-raid scan consolidation, exact safety smokes, QA runs 6–7, and cumulative profiling. Full TRAIN execution is the next stage. |
