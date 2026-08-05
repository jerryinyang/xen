# SPDR-021/022/023 Amended Rerun and Completion Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:executing-plans` for the
> main sequence. Use the Xen `research-pipeline` at every lifecycle boundary and the Xen
> `data-analyst` in a fresh context for each final `analysis.md`. Steps use checkbox
> (`- [ ]`) syntax so `/goal` can resume at the first unchecked item.

**Goal:** Correct the execution and analysis defects that invalidated parts of the first run,
amend the frozen design without changing its research grid, rerun all six TRAIN cells, complete
all three neutral analyses, and stop at the operator's combined interpretation gate.

**Architecture:** Keep one shared `xen.adaptive_management` implementation and three independent
experiment wrappers. Fix entry/exit lifecycle behavior in Nautilus, make the two declared native
estimands explicit, measure management only from genuinely filled and closed episodes, and execute
the declared controls. Process one symbol and one cell at a time to preserve the proven memory
profile; retain every safe optimisation already demonstrated to leave the experiment unchanged.

**Tech stack:** Python 3.13, Polars, NumPy, pytest, Ruff, NautilusTrader 1.230.0,
`xen.nautilus.catalog_fence`, emission contract v1, canonical `xen.adjudication`.

**Execution authority:** On 2026-08-03 the operator chose the engine-fix plus full-rerun route.
That authorises the six TRAIN reruns after the amended acceptance checks pass. It does not
authorise TEST/holdout contact, XENA, deployment, a family-status change, or an experiment verdict.

---

## `/goal` execution contract

Use this document as the single execution ledger. The goal is complete only when Tasks 1-9 are
checked and the final handoff is on disk. Do not stop between tasks merely to ask permission when
the next action is already covered here. Stop only at a listed stop condition or a pipeline gate
whose prerequisites failed.

Suggested goal objective:

```text
Execute docs/superpowers/plans/2026-07-30-spdr-021-023-stages-8-execution-handoff.md
from the first unchecked item through Tasks 1-9. Update the handoff after every completed task,
obey its gates and stop conditions, and finish only at the operator interpretation handoff.
```

The executing agent must:

- begin by reading this file, `AGENTS.md`, the `research-pipeline` skill and its mandatory
  references;
- inspect the current worktree before editing and preserve unrelated user changes;
- update this file immediately after each completed task with the observed tests, run IDs,
  durations, hashes and any safe deviation;
- use TDD for every behavioral correction: focused failing test, observed failure, minimum fix,
  focused pass, then regression pass;
- use fresh output paths and atomic publication; never overwrite a run or analysis in place;
- run SPDR-021, SPDR-022 and SPDR-023 regardless of the economic observations in either companion;
- leave all value, power and significance reads informative; no result may gate another result;
- make no commit, push, external publication or family-status change unless separately authorised.

The executing agent may make a small implementation adjustment without returning to the operator
only when all of these are true: it is required to satisfy a pass criterion below, it does not
change the frozen arms/populations/dates/estimands, it has a focused regression test, and it is
recorded in this handoff. Any research-scope change requires a further dated amendment and stops.

---

## Authoritative current state

### Complete and retained

- [x] Frozen arm grids, causal volatility features, common origins, native schedules and external
  management schedules are implemented for all three experiments.
- [x] Independent TRAIN-only wrappers, recoverable per-symbol execution, atomic assembly,
  integrity checks and 13-artifact analysis wrappers exist.
- [x] Six first-pass TRAIN cells with stamp `20260731T004708Z` completed.
- [x] The first-pass run exposed the defects below. Those emissions and all derived analysis are
  now **invalid for interpretation** and must be removed under Task 5.

### Confirmed defects requiring amendment and rerun

1. SPDR-022/023 market entries can submit protective exits inside the entry-fill callback before
   Nautilus has published the position. A denied exit is recorded but leaves the position and arm
   open, making the failure absorbing.
2. SIZE has no strategy-level closing horizon and closed zero episodes in every checked cell.
   It must inherit the strategy's fixed holding exit so the experiment measures sizing rather than
   indefinite occupancy. Pure TARGET/STOP/TRAIL arms retain their declared price-only semantics.
3. `native_parameter_shared_trades.parquet` identifies planned entries from `entry_ts`; it must
   identify actual fills from `_entry_ns`. It is empty for breakout stop entries and includes
   non-fills for breach market schedules.
4. Common-origin zero-exposure rows are intentional for the per-opportunity estimand. They are not
   trade observations. The analysis must separately report the actual co-fill/co-close lens and
   label counts and uncertainty by the population they describe.
5. Device `episode_n`/`effective_n` currently describe scheduled opportunities in places where
   they read like filled or closed episodes.
6. `controls.parquet` marks time derangement and magnitude matching as deferred; the approved
   design requires their outcome reads to be executed and reported.

### Current repository cautions

- All six old raw runs are local. SPDR-022 crypto was moved to
  `data/nautilus_runs/SPDR-022-crypto-train-20260731T004708Z` on 2026-08-03, so all invalid raw
  targets can be resolved and deleted without the external volume.
- The worktree contains untracked provisional SPDR-021/022 analyst scripts and outputs. They are
  part of the invalid first-pass analysis, not authoritative evidence. Task 5 names their route.
- The old `screen.md` files and SPDR-023 `analysis.md` are provisional even though tracked.
- The old claim that two analysis passes were hash-identical is not independently auditable because
  no persistent second-pass manifest was saved. The corrected run must retain that manifest.

---

## Binding constraints

- TRAIN only. Never load TEST or the final global holdout.
- Decisions use confirmed information available by `t-1`; execution remains Nautilus event-driven.
- Keep all eight volatility components, fixed/direct/reverse native arms, all four native
  orientation pairs, external devices and declared combinations exactly as approved.
- Native parameters and external management remain separate; no native x management crossing.
- SPDR-022/023 keep `E-TOUCH` and `E-CLOSE` separate. MOMO and MR remain separate experiments.
- Both native estimands are required:
  1. per eligible origin, including zero exposure while an arm is occupied;
  2. per actual common fill, using engine-recorded fill times on both sides.
- Management must report eligible origins, entry fills, closes and actual paired closes separately.
- SIZE inherits the strategy's fixed holding exit as common apparatus: one H1 bar for SPDR-021 and
  four H1 bars for SPDR-022/023. Adaptive HOLD uses its own declared duration. Pure
  TARGET/STOP/TRAIL arms keep their price-only exit semantics and report fence censoring plainly.
- No spread proxy. Keep `UNAVAILABLE_NOT_CHARGED`, `spread_rt_bps=null`,
  `PARTIAL_FEES_FUNDING_ONLY`, and the warning that reported net performance is overstated.
- No `SUPPORTED`, `REFUTED`, winner, deployability or universal-effect labels. Power is context only.
- All strata stay visible; no top-N pruning. Selective concentrations may be described plainly.

---

## Performance and reliability standard

The first execution round required careful resource work. Preserve these mechanisms:

- one Nautilus process per symbol/work unit;
- state-ledger batch streaming and release of terminal per-episode state;
- streaming run assembly instead of whole-run concatenation;
- disabled quadratic `PortfolioAnalyzer` accumulation guard;
- deterministic unit hashes, atomic `.inprogress` publication and hash-checked resume;
- per-symbol analysis, projected parquet columns and immediate release of wide frames;
- NumPy bootstrap kernels already proven against their Polars references;
- one-time comparator partitioning, join-based reporting validation and preallocated diagnostics.

Default to `--jobs 1` for execution and analysis. Do not run integrity or analysis beside an engine
cell. Do not implement the old Task 11 cache purge/streaming-report rewrite in this rerun: it changes
the emission path and is not needed for a reliable sequential run.

Operator amendment, 2026-08-03 after the first fresh cTrader cell: use `--jobs 2` for subsequent
engine cells. Fall back to `--jobs 1` if macOS memory pressure becomes warning/critical, swap grows
across two consecutive checks, or free disk falls below the Task 4 cell margin. Analysis remains
sequential at `--jobs 1`, and cells remain sequential.

A new optimisation is allowed only if:

1. it does not alter fences, dates, origins, arms, scheduling, engine event order, bootstrap draws,
   metrics, row order, numeric precision or artifact schemas;
2. a corrected reference fixture and the optimised path are byte-identical for every unaffected
   artifact, and exactly key/value-identical for artifacts intentionally changed by this amendment;
3. focused tests cover nulls, NaNs, empty groups, duplicate protection and ordering;
4. peak memory and wall time are measured before/after and written here;
5. the simpler safe route is preferred when the gain is not material.

Explicitly prohibited during this plan: fewer bootstrap draws, altered random seeds, pooled block
sums that change rounding, dropped candidate rows, reduced symbol sets, shortened dates, arm
pruning, changed bar resolution, cache purging, or parallelism enabled only because it appears fast.

---

## Final pass matrix

| Gate | Required evidence | Pass criterion |
| --- | --- | --- |
| Amendment | dated common and per-experiment records | all six defects above have exact declared semantics; grid unchanged |
| Exit lifecycle | focused Nautilus tests | exits wait for a confirmed position; failure closes or fails the work unit; no silent open arm |
| SIZE horizon | schedule + engine tests | SIZE closes on the strategy-fixed hold; no hidden cap is added to pure price devices |
| Shared fills | analysis tests | actual `_entry_ns` on both sides; breakout and breach fixtures exclude scheduled non-fills |
| Counts | analysis tests | eligible, filled, closed, co-filled and co-closed counts are separately named |
| Controls | outcome-control artifacts | time-deranged and magnitude-matched effects computed per declared stratum; none marked deferred |
| Corrected acceptance | synthetic + bounded real smoke | repeated breach episodes close; SIZE closes; no absorbing denied exit; all keys reconcile |
| Production cell | estimand + integrity artifacts | every hard check true before analysis |
| Reproduction | persistent SHA-256 manifest | two independent analysis passes match for all 13 artifacts in every cell |
| Analysis | three `screen.md` + three `analysis.md` | complete neutral maps; all populations and limitations visible |
| Closeout | full tests, lint, boundary searches, indexes | zero failures/findings; status accurate; no forbidden action |

---

### Task 1: Amend the frozen design and invalidate the first pass

**Files:**

- Modify: `docs/experiments-docs/checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/adaptive-management-design.md`
- Modify: `python/experiments/SPDR-021/design.md`
- Modify: `python/experiments/SPDR-022/design.md`
- Modify: `python/experiments/SPDR-023/design.md`
- Modify: `docs/superpowers/plans/2026-07-31-spdr-021-023-design-checklist.md`
- Create: `docs/superpowers/plans/2026-08-03-spdr-021-023-first-pass-invalidation.md`

**Produces:** one dated amendment shared by all three experiments and a compact audit explaining
why stamp `20260731T004708Z` cannot support interpretation.

- [x] **Step 1: Record the invalidation facts before deleting data**

Write the six defects from this handoff with raw counts already independently checked, exact old
run IDs/paths, and available source hashes. Record that all six raw runs were local before deletion.
Distinguish confirmed mechanism from inference: the absorbing `EXIT_DENIED` behavior and callback
timing are confirmed; “through-market trigger” is not established as the sole cause.

Pass: the record contains no economic verdict and does not preserve first-pass effect tables.

- [x] **Step 2: Append a dated amendment to the common design**

The amendment must declare:

```text
AMENDMENT DATE: 2026-08-03
CAUSE: execution lifecycle and reporting-population defects
GRID: unchanged
DATES / UNIVERSES / FEATURES / ORIENTATIONS: unchanged
FIRST PASS: invalid for interpretation; full six-cell rerun required

ENTRY-FILL IDENTITY:
  actual fill := state_ledger state == FILLED with non-null _entry_ns
  common fill := adaptive and fixed both have actual fills on the same declared origin key

SIZE HORIZON:
  SPDR-021 SIZE closing horizon := fixed strategy hold of 1 H1 bar after actual entry
  SPDR-022/023 SIZE closing horizon := fixed strategy hold of 4 H1 bars after actual entry
  adaptive HOLD uses its declared value
  pure TARGET / STOP / TRAIL arms keep price-only semantics; no hidden time cap

EXIT FAILURE:
  protective exits are submitted only after the engine exposes the position
  a rejected/denied exit triggers one deterministic reduce-only market fail-safe
  the arm is released only after confirmed close
  failure of the fail-safe aborts the work unit; no incomplete unit is published

REPORT POPULATIONS:
  eligible_origin_n, entry_fill_n, close_n, common_fill_n, common_close_n
  per-origin uncertainty uses origins; per-trade uncertainty uses actual paired trades

CONTROLS:
  time derangement and magnitude matching are computed against outcomes per stratum
  they remain informative and cannot gate another arm or experiment
```

Pass: no approved arm, component, combination, date, universe or direction is added or removed.

- [x] **Step 3: Mirror the amendment in each experiment design**

Change stale status text to: first pass invalidated; amended rerun authorised; analysis pending.
SPDR-021 must name threshold/expiry keys; SPDR-022 and SPDR-023 must name `z/H` plus separate
`E-TOUCH/E-CLOSE`. All three must link the common amendment rather than restating it inconsistently.

- [x] **Step 4: Extend the design checklist**

Add one row per amended clause with intended code, focused test and smoke evidence locations.
Leave evidence cells unchecked until Tasks 2-4 produce it.

Pass: every amended clause maps to a later task; no clause is accepted by prose alone.

**Task 1 completed 2026-08-03.** Evidence: dated invalidation record
`2026-08-03-spdr-021-023-first-pass-invalidation.md`; common design amendment §12; mirrored status
and experiment-specific keys in all three `design.md` files; ten unchecked amended-acceptance rows
in the design checklist. The raw audit resolved all six local runs, recorded compact source hashes,
and confirmed SIZE closed `0/2,024` filled SIZE episodes across the six cells. The approved arm,
component, combination, date, universe, entry-variant and orientation grid is unchanged.

---

### Task 2: Correct Nautilus position and exit lifecycle behavior

**Files:**

- Modify: `python/src/xen/adaptive_management/strategy.py`
- Modify if the schedule must expose the common cap: `python/src/xen/adaptive_management/policies.py`
- Modify only if required for report extraction: `python/src/xen/adaptive_management/engine.py`
- Modify: `python/tests/test_adaptive_management_strategy.py`
- Modify: `python/tests/test_adaptive_management_policies.py`
- Modify: `python/tests/test_adaptive_management_integrity.py`

**Interface:** a filled entry becomes exit-eligible only after its Nautilus position is visible.
SIZE inherits the fixed strategy hold. An exit failure cannot leave an arm permanently occupied.

- [x] **Step 1: Add failing lifecycle tests**

Add bounded engine tests for:

- a breach market fill whose position is absent inside the fill callback: no protective order is
  submitted until the position-open event (or the first supported callback where it is visible);
- target, stop and trail each submit with the intended `position_id` after confirmation;
- a denied protective leg submits exactly one reduce-only market fail-safe;
- a successful fail-safe records `CLOSED`, cancels siblings and releases the arm;
- a denied fail-safe raises and prevents work-unit publication;
- later origins execute after recovery, proving the denial is not absorbing;
- partial entry fills never create duplicate terminal rows or over-sized exits.

Pass of this step: tests fail on the current callback/failure behavior, not on fixture setup.

- [x] **Step 2: Add failing evaluation-horizon tests**

Assert:

```python
assert breakout_size_row["hold_bars"] == 1
assert breach_size_row["hold_bars"] == 4
assert adaptive_hold_row["hold_bars"] == adaptive_hold_value
assert target_only_row["hold_bars"] is None
assert stop_only_row["hold_bars"] is None
assert trail_only_row["hold_bars"] is None
```

Cover SIZE, adaptive HOLD and all three device combinations. A combination with HOLD uses that
HOLD; `TARGET+STOP` remains price-only. No horizon change may add an arm or change an entry
population.

- [x] **Step 3: Implement the minimum lifecycle state machine**

Queue the exit specification after the first entry fill, submit it only when the confirmed position
can be retrieved, and keep partial-fill quantities reconciled. On protective-exit failure, record
the failing leg, cancel any still-open siblings, and submit one tagged reduce-only market fail-safe
against the confirmed remaining quantity. Release only from the confirmed close path.

Do not solve this by releasing the slot, inventing a synthetic close, or swallowing an open
position at the fence.

- [x] **Step 4: Materialise the SIZE closing horizon**

Set the strategy-fixed hold only on SIZE schedule rows as declared by Task 1. Keep HOLD an
individual adaptive device with its own value. Ensure SIZE changes quantity only and is otherwise
closed by the strategy-fixed hold. Do not add a time exit to pure TARGET, STOP or TRAIL rows.

- [x] **Step 5: Strengthen integrity checks**

A complete run must fail integrity when a filled SIZE or HOLD episode lacks its scheduled close,
except an explicit fence-censored episode whose deadline lies beyond the TRAIN fence. A pure
price-only episode may be open at the fence and must be labelled censored. Fail when an exit failure
has neither a confirmed fail-safe close nor a failed work unit.

- [x] **Step 6: Verify the focused correction**

Run from `python/`:

```bash
PYTHONPATH=. .venv/bin/pytest \
  tests/test_adaptive_management_strategy.py \
  tests/test_adaptive_management_policies.py \
  tests/test_adaptive_management_integrity.py -q
.venv/bin/ruff check src/xen/adaptive_management/strategy.py \
  src/xen/adaptive_management/policies.py \
  tests/test_adaptive_management_strategy.py \
  tests/test_adaptive_management_policies.py \
  tests/test_adaptive_management_integrity.py
```

Pass: zero failures/findings; the old absorbing fixture now cycles through multiple episodes.

Completion evidence (2026-08-03): the new tests failed first on immediate protective
submission, null protective `position_id`, missing SIZE horizons and the absent lifecycle gate.
After the correction, the three-file focused suite passed (`105 passed in 28.06s`) and the exact
Ruff command above returned `All checks passed!`. The bounded engine cases cover TARGET, STOP
and TRAIL; unit lifecycle cases cover one reduce-only fail-safe, confirmed close, sibling
cancellation, slot release, later-origin admission, fail-safe denial and partial-fill accounting.

---

### Task 3: Correct estimands, counts, uncertainty labels and controls

**Files:**

- Modify: `python/src/xen/adaptive_management/analysis.py`
- Modify: `python/src/xen/adaptive_management/integrity.py`
- Modify: `python/tests/test_adaptive_management_analysis.py`
- Modify: `python/tests/test_adaptive_management_integrity.py`
- Modify only as thin wrappers: `python/experiments/SPDR-02{1,2,3}/analysis_code/analyse.py`

**Produces:** the same 13 canonical artifacts, with corrected shared-fill contents, explicit
population counts and computed control results.

- [x] **Step 1: Add failing actual-fill pairing tests**

Build two fixtures:

1. breakout STOP schedules where planned `entry_ts` is null but both arms have ledger `FILLED`
   rows; the pair must be retained;
2. breach MARKET schedules with planned `entry_ts` present but one or both arms never filled; those
   rows must be excluded from the shared-fill table.

Pair on the full declared origin identity, then require non-null `_entry_ns` for adaptive and fixed.
For the trade-outcome lens also require both `_exit_ns` values. Assert duplicates fail loudly.

- [x] **Step 2: Preserve and label the per-origin estimand**

Keep `outcome_bps=0.0` for an eligible origin with no exposure. Label its source
`COMMON_ORIGIN_OCCUPANCY_INCLUSIVE`. Its `event_count`, blocks, interval and MDE must be based on
eligible origins. Never describe this interval or MDE as trade-level.

- [x] **Step 3: Add unambiguous population columns**

Every applicable result row must expose:

```text
eligible_origin_n
entry_fill_n
close_n
common_fill_n
common_close_n
effective_origin_blocks
effective_trade_blocks
```

Use null when a population does not apply; do not fill it from another population. Retain existing
legacy count columns only when needed for compatibility, and define them in `analysis_summary.json`.

- [x] **Step 4: Derive uncertainty from the matching population**

Per-origin estimates resample origin/date blocks. Common-fill and common-close estimates resample
only actual paired fill/close blocks. Device-native metrics use closed episodes when the metric
requires an exit. A scheduled row may never inflate a trade-level `n`, interval or MDE.

- [x] **Step 5: Execute the two informative controls**

Replace `_control_inventory` placeholders with outcome-bearing rows for:

- time-deranged component assignments using the existing zero-fixed-point mapping and fixed seed;
- magnitude-matched comparisons within the declared symbol, component, entry-variant and magnitude
  strata.

Each row must name the control, population, comparator, estimate, interval, count and effective
count. Preserve all strata even when empty or undefined; write null plus the reason. The
`analysis_stage` value must be `COMPUTED`, never `DEFERRED_TO_STAGE_8`.

These controls are informative. Do not convert collapse, sign or interval behavior into a pass,
fail, supported or refuted label. The future-destroying causality tripwire remains a separate hard
integrity check.

- [x] **Step 6: Protect the proven analysis performance path**

Run the corrected fixture once through a simple reference implementation and once through the
production kernels. Assert identical row keys, values, null/NaN placement and ordering. For
unaffected artifacts require byte identity. Retain per-symbol processing and `jobs=1`; do not hold
all symbol payloads or both full comparison sides in memory when a projected/partitioned read works.

- [x] **Step 7: Verify analysis and controls**

```bash
cd python
PYTHONPATH=. .venv/bin/pytest \
  tests/test_adaptive_management_analysis.py \
  tests/test_adaptive_management_integrity.py -q
.venv/bin/ruff check src/xen/adaptive_management/analysis.py \
  src/xen/adaptive_management/integrity.py \
  tests/test_adaptive_management_analysis.py \
  tests/test_adaptive_management_integrity.py \
  experiments/SPDR-02{1,2,3}/analysis_code/analyse.py
```

Pass: zero failures/findings; breakout and breach shared-fill fixtures are correct; every control
is computed; no count can be mistaken for a different population.

Completion evidence (2026-08-03): actual-fill fixtures failed first because shared trades used
planned `entry_ts`; scheduled breach non-fills were therefore included and breakout fills with a
null planned time were excluded. After correction, the analysis/integrity suite passed (`77 passed
in 9.65s`) and the exact Ruff scope above returned `All checks passed!`. The suite also proves
origin-block versus trade-block counts, zero-valued unexposed origins, computed derangement and
magnitude controls with explicit null reasons, block-summary/reference equivalence, and byte
identity for unaffected artifacts across deterministic replays.

---

### Task 4: Re-run amended acceptance before deleting the first pass

**Files:**

- Update evidence rows in: `docs/superpowers/plans/2026-07-31-spdr-021-023-design-checklist.md`
- Update completion evidence in this handoff.

- [x] **Step 1: Run the full implementation suite**

```bash
cd python
PYTHONPATH=. .venv/bin/pytest tests/test_adaptive_management_*.py -q
PYTHONPATH=. .venv/bin/pytest tests -q
.venv/bin/ruff check src/xen/adaptive_management \
  tests/test_adaptive_management_*.py experiments/SPDR-02{1,2,3}
cd ..
git diff --check
```

Pass: zero failures and zero lint/diff findings. Record exact counts; do not reuse old counts.

Observed 2026-08-03: 237 adaptive-management tests passed; the complete suite passed with
529 passed, 4 skipped and 3 third-party warnings. Ruff and `git diff --check` were clean.

- [x] **Step 2: Run synthetic amendment traces**

Cover all three experiments and both breach variants. The trace must show actual entry fill,
position confirmation, accepted target/stop/trail, adaptive HOLD, fixed-horizon SIZE
close, denied-exit fail-safe and a later episode on the same arm.

Pass: expected and observed event/order/fill/position/ledger sequences match exactly.

Observed: the parametrised amended trace passed for SPDR-021 BREAKOUT and both E-TOUCH/E-CLOSE
variants in SPDR-022/023. Focused denial, fail-safe and later-episode tests also passed.

- [x] **Step 3: Run bounded real-catalog smokes**

Use TRAIN-only cTrader data for SPDR-021, SPDR-022 and SPDR-023. Use enough origins to observe
multiple fills and closes for TARGET, STOP, TRAIL, HOLD and SIZE. Run the estimand gate and
`run_integrity_checks` on each smoke.

Pass:

- `blocking_pass=true` for every smoke;
- no arm stays open after an exit denial;
- every device has more than one fill where the fixture admits it; HOLD and SIZE close on schedule,
  while pure price devices distinguish closed from legitimately censored episodes;
- `native_parameter_shared_trades.parquet` is non-empty and contains only actual common fills;
- controls contain computed outcome rows;
- row accounting has no missing, extra or duplicate key.

Observed in `/private/tmp/spdr-amended-acceptance-20260803-v9`: all three integrity checks passed;
origins were 371/839/839; actual common fills were 966/6,407/6,394; computed control rows were
320/640/640; and absorbing exit failures were 0/0/0. Every row-accounting check passed.

- [x] **Step 4: Prove corrected deterministic reproduction**

Run one bounded work unit clean, resumed and twice from scratch. Compare corrected canonical hashes.
Pass: all artifacts that should be deterministic match; no UUID, timestamp or path leaks into data.

Observed in `/private/tmp/spdr-amended-determinism-20260803`: clean, resumed and two scratch runs
all produced canonical content hash `7834a5cd8a0b7a87262ebfaf348065ac48cab8fa4b81b55d80b7c41baedd5c71`;
the resumed work unit was reused rather than rerun.

- [x] **Step 5: Refresh resource preflight**

Run preflight for all six cells. Record free disk, predicted output, measured smoke RSS and the
sequential wall-time range. Require at least predicted output plus 25% and 10 GiB free on the
selected filesystem. With 66 GiB free observed locally before invalidation, remeasure after old
artifacts are removed; do not assume that value.

Pre-deletion observation: 58.67 GB free; per-cell predicted outputs were 18.82/2.26 GB for
SPDR-021 crypto/cTrader, 58.81/7.07 GB for SPDR-022 and 58.81/7.07 GB for SPDR-023. Sequential
wall time was 10.16-29.02 hours and bounded-smoke peak child RSS was 1.84 GB. The largest-cell
25% threshold is 73.51 GB, so this step remains open until the explicitly required Task 5
post-deletion measurement.

Post-deletion observation: 103.47 GB free. All six cells pass; the largest requirement remains
73.51 GB and the 10 GiB minimum governs only the smaller cTrader cells.

Measured refresh after SPDR-022 crypto: the completed same-grid cell occupies 22,222,568 KiB
(21.2 GiB), versus the original 58.81 GB forecast. SPDR-022 and SPDR-023 cTrader outputs also match
within 1% (4,254,340 versus 4,290,136 KiB), supporting this analogue. Applying the required 25%
margin to the measured breach-crypto size gives 27,778,210 KiB (26.5 GiB). The 58 GiB observed
before SPDR-023 crypto therefore passes the refreshed margin without deleting canonical evidence.

- [x] **Step 6: Close the amended checklist**

Every amendment row must point to an observed test or smoke. Any unresolved clause stops before
deletion or production execution.

---

### Task 5: Hard-remove invalid first-pass artifacts and prepare fresh destinations

This is destructive and covered by the operator's full-rerun decision. Resolve and print every
target before deletion. Never use a glob, environment variable, repository root, `~` or broad
recursive target.

**Delete only:**

```text
data/nautilus_runs/SPDR-021-ctrader-train-20260731T004708Z
data/nautilus_runs/SPDR-021-crypto-train-20260731T004708Z
data/nautilus_runs/SPDR-022-ctrader-train-20260731T004708Z
data/nautilus_runs/SPDR-022-crypto-train-20260731T004708Z
data/nautilus_runs/SPDR-023-ctrader-train-20260731T004708Z
data/nautilus_runs/SPDR-023-crypto-train-20260731T004708Z
python/experiments/SPDR-021/results/analysis
python/experiments/SPDR-021/results/analyst
python/experiments/SPDR-022/results/analysis
python/experiments/SPDR-022/results/analyst
python/experiments/SPDR-023/results/analysis
python/experiments/SPDR-023/results/analyst
python/experiments/SPDR-021/screen.md
python/experiments/SPDR-021/analysis.md
python/experiments/SPDR-022/screen.md
python/experiments/SPDR-022/analysis.md
python/experiments/SPDR-023/screen.md
python/experiments/SPDR-023/analysis.md
```

- [x] **Step 1: Reconcile provisional analysis code**

Keep generic, corrected analysis utilities that are reusable on a new run. Remove untracked or
tracked one-off scripts whose only inputs are stamp `20260731T004708Z` or whose sole purpose was to
explain its invalid device outputs. Do not delete a reusable method until its corrected equivalent
is tested. Record exact retained/removed paths in the invalidation document.

- [x] **Step 2: Delete the resolved local targets**

First assert each resolved target is exactly one of the paths above and is not a symlink. Delete it,
then verify it is absent. Report total space recovered and that deletion is not recoverable except
from git for tracked Markdown/scripts.

- [x] **Step 3: Verify all six raw runs were removed**

Resolve the six exact local raw-run paths listed above after deletion. Pass: all six are absent and
no `.inprogress` sibling with stamp `20260731T004708Z` remains.

- [x] **Step 4: Verify decontamination**

Search live experiment results and analysis documents for `20260731T004708Z`. Pass: zero live
result or report references; the dated invalidation record and this historical path list are the
only permitted documentation references.

Observed 2026-08-03: the twelve directories and six Markdown targets are absent (two Markdown
targets were already absent), no matching `.inprogress` sibling exists, and the live search returned
zero references. Free space rose from 58.67 GB to 103.47 GB, a recoverable-space change of 44.79 GB.
The deleted generated artifacts are not locally recoverable; tracked scripts and Markdown remain
recoverable from Git history.

---

### Task 6: Execute and validate all six amended TRAIN cells

**Outputs:** fresh immutable run directories under `data/nautilus_runs/` unless the refreshed disk
preflight requires an explicitly recorded external destination.

- [x] **Step 1: Choose one fresh UTC run stamp**

Use the same stamp in these six immutable IDs:

```text
SPDR-021-ctrader-train-<stamp>
SPDR-021-crypto-train-<stamp>
SPDR-022-ctrader-train-<stamp>
SPDR-022-crypto-train-<stamp>
SPDR-023-ctrader-train-<stamp>
SPDR-023-crypto-train-<stamp>
```

Write the stamp into this handoff before launching. Refuse an existing final or `.inprogress`
destination unless it is the exact matching resumable unit set.

Fresh amended run stamp: `20260803T140238Z`. All six final and `.inprogress` destinations were
absent when selected.

- [x] **Step 2: Run cells sequentially with the approved worker count**

Run cTrader first for each experiment so lifecycle defects surface cheaply, then crypto. Use each
experiment's own `screen_code/run_screen.py`, `--universe`, `--output`, `--jobs 1`, and `--resume`
only for a hash-valid interrupted destination. Do not gate a later experiment on observed effects.

Recommended order:

```text
SPDR-021 cTrader -> SPDR-021 crypto
SPDR-022 cTrader -> SPDR-022 crypto
SPDR-023 cTrader -> SPDR-023 crypto
```

- [x] **Step 3: Monitor without competing workloads**

Record heartbeat, completed symbols, elapsed time, RSS, swap and disk. Stop launching new work if
the OS begins sustained swapping or free disk falls below the Task 4 margin; let the current atomic
unit finish when safe. Resume rather than restart a hash-valid interrupted run.

- [x] **Step 4: Validate each cell before launching its analysis**

For each completed cell:

1. run canonical estimand validation over `cells/`;
2. run `run_integrity_checks` over the raw root;
3. verify all declared symbols, exact arm lattice, row accounting, manifest/fence hashes and spread
   disclosure;
4. verify filled/closed census by device and no absorbing failure signature;
5. write run duration, peak RSS, output size and hard-check result into this handoff.

Pass: `blocking_pass=true`, zero missing/extra/duplicate rows, no unexplained open management
position, and every intended device is genuinely measured. A failing cell is fixed and rerun under
the amendment; it is never reinterpreted as an economic observation.

Production evidence recorded to date:

| Cell | Jobs | Duration | Size | Origins | Fills / closes | Estimand | Hard integrity | Absorbing exit failures | Row accounting |
| --- | ---: | ---: | ---: | ---: | ---: | :---: | :---: | ---: | :---: |
| SPDR-021 cTrader | 1 | 493 s | 733,256 KiB | 20,061 | 158,547 / 158,395 | pass | pass (14/14) | 0 | pass |
| SPDR-021 crypto | 2 | 1,167 s | 3,596,712 KiB | 102,160 | 771,135 / 770,178 | pass | pass (14/14) | 0 | pass |
| SPDR-022 cTrader | 2→1 | 5,816 s | 4,277,760 KiB | 44,700 | 1,448,950 / 1,448,594 | pass | pass (14/14) | 0 | pass |
| SPDR-022 crypto | 1 | 8,659 s | 22,222,568 KiB | 231,121 | 7,405,640 / 7,402,289 | pass | pass (14/14) | 0 | pass |
| SPDR-023 cTrader | 1 | 1,933 s | 4,290,136 KiB | 44,700 | 1,448,928 / 1,448,570 | pass | pass (14/14) | 0 | pass |
| SPDR-023 crypto | 1 | 9,149 s | 22,292,148 KiB | 231,121 | 7,435,982 / 7,432,667 | pass | pass (14/14) | 0 | pass |

The sandbox blocked process-list RSS reads and macOS `/usr/bin/time -l` aborted its resource
footer after the successful runner returned. The bounded acceptance peak remains 1.84 GB; during
the two-worker crypto run macOS reported 36-60% free memory, swap-out growth stopped on each
confirmation check, and disk remained above the cell margin. Subsequent cells use an in-process
child-RSS wrapper so production peak RSS is persisted.

SPDR-022 cTrader crossed the approved two-worker fallback after swap-out grew on two consecutive
checks. It was interrupted at 389 seconds with no complete unit, resumed at `jobs=1`, paused after
two hash-complete units to let memory recover, then resumed with both units reused. The final
segment measured 6.50 GB max child RSS and 7.63 GB max parent RSS; macOS memory recovered from 35%
to 77% free at the pause. No partial unit was published.

Execution checkpoint: `SPDR-022-crypto-train-20260803T140238Z` was launched sequentially at
`jobs=1` after the cTrader fallback. Its declared crypto universe contains 25 symbols; cTrader
contains 3, so each experiment has 28 symbols across both universes. BTCUSDT was atomically
published before the operator-directed performance pause below. While an engine cell is active,
work on this host is limited to lightweight documentation and read-only status checks; tests,
builds, analysis and other data-heavy development remain deferred.

Because the two-worker threshold was crossed on SPDR-022 cTrader, the remaining breach cells
(SPDR-022 crypto and both SPDR-023 universes) use `jobs=1`. Hash-valid completed units may be reused
after a memory-recovery pause; incomplete units are never treated as complete.

Operator-directed critical-path review, 2026-08-03: the projected ten-hour SPDR-022 crypto run was
paused after one hash-complete BTCUSDT unit and audited without reading outcomes. Five safe
operational fixes were accepted under the parity rule: ordered columnar schedule consumption,
`frozen_account=True` for independent research arms, `run_analysis=False`, release of terminal
client-order IDs while retaining duplicate-event guards, and streaming SHA-256 file hashing.
The focused adaptive-management suite passes 242 tests. Isolated schedule initialisation fell from
9.327 seconds / 8.410 GB RSS to 0.509 seconds / 3.474 GB. A 2,000-arm replay fell from 27.016 to
5.945 seconds with 4/4 report hashes equal. A full optimised BTCUSDT replay took 428.245 seconds at
5.749 GB RSS and matched the completed pre-optimisation unit byte-for-byte for orders, fills,
positions and state ledger (827,105 / 796,647 / 398,388 / 4,767,815 rows).

Full BTCUSDT preparation still costs 39.410 seconds and 3.892 GB RSS while the parent retains the
static tables. Parent plus child therefore remains about 9.6 GB per active job; two jobs exceed the
16 GB host and remain unsafe. The prohibited Task 11 pre-staging/cache/report-streaming redesign is
not implemented. The review, deferred findings, Rust decision rule and future-development checklist
are recorded in `docs/superpowers/plans/2026-08-03-spdr-critical-path-performance-review.md` and
now include an ETHUSDT sequential probe: replay reached Nautilus report generation at 414 seconds,
where swap grew across three checks but memory retained 39% free with zero throttled pages. The
incomplete unit was interrupted and not published. At `jobs=1`, further stopping is reserved for
warning/critical pressure, throttled pages or dangerously low free memory; swap growth already
caused the only available worker-count fallback. The resumed cell then completed in 8,659 seconds
(2 hours 24 minutes), reusing one unit and rerunning 24. Peak parent/child RSS was 8.00/6.94 GB.
All 25 symbols passed the estimand gate and all 14 integrity checks; all nine declared device
classes had fills and closes, with no absorbing failure signature. These findings are also recorded
as knowledge-base lesson L-54 / pitfall P-26.

Small gate correction: family estimand validation incorrectly passed the whole-universe expectation
into each one-symbol emission, making every cell claim the other symbols were missing even when the
family manifest was complete. `test_family_expectation_is_checked_across_single_instrument_cells`
failed first; `validate_family` now validates each cell locally and applies the declared universe at
family level. The estimand suites passed (7 passed, 1 skipped), then both SPDR-021 family gates passed.

## Live handoff and remaining execution directives

Checkpoint after final-cell validation (`20260803T140238Z` run stamp): Tasks 1-6 are complete.
All six independent TRAIN cells are immutable and passing; the production-evidence table above is
authoritative. SPDR-023 crypto completed 25/25 symbols in 9,149 seconds with 8.51/7.12 GB peak
parent/child RSS, then passed the 25-symbol estimand gate, all 14 hard checks and the nine-device
census with no absorbing failure signature. No TEST, holdout, XENA, verdict or family-status action
has occurred. The safe critical-path fixes and deferred report-emission work are recorded in
`docs/superpowers/plans/2026-08-03-spdr-critical-path-performance-review.md`.

Task 7 progress checkpoint, 2026-08-04:

- SPDR-021 cTrader canonical analysis completed in 376.868 seconds at 2.771 GB peak RSS. Its fresh
  second pass completed in 312.691 seconds at 2.650 GB; all 13 relative artifact names and SHA-256
  hashes match. The structural audit found zero duplicate full rows, real entry timestamps on both
  shared-fill sides, both native lenses, four orientation pairs, all controls `COMPUTED`, and no
  prohibited result field.
- SPDR-021 crypto canonical analysis completed in 1,987.793 seconds at 3.070 GB peak RSS. Its fresh
  second pass completed in 2,054.076 seconds at 3.052 GB; all 13 hashes and the same structural
  audit passed. `SPDR-021/results/analysis/reproduction-hashes.json` was re-read and independently
  verified against all 26 canonical/temporary files before the two exact temporary roots were
  removed. SPDR-021 therefore has 13/13 equality in both universes with persistent evidence.
- SPDR-022 cTrader canonical/reproduction analyses completed in 845.466/842.795 seconds at
  4.295/4.400 GB peak RSS. SPDR-022 crypto completed in 5,035.342/4,952.383 seconds at
  8.030/7.653 GB. All four passes emitted the same 13 relative artifact names; both universe hash
  sets match 13/13. Both structural audits found zero duplicate full rows, both entry variants,
  both native lenses, all four orientation pairs, complete common-fill timestamps, computed
  controls and no prohibited result fields. `SPDR-022/results/analysis/reproduction-hashes.json`
  was independently verified against all 26 canonical/temporary files before the two temporary
  roots were removed.
- SPDR-023 cTrader canonical analysis completed in 1,056.134 seconds at 4.084 GB peak RSS and
  emitted exactly the required 13 artifacts under its final canonical directory. The fresh
  reproduction root `/private/tmp/spdr023-ctrader-analysis-repro.34m2Y4` has been allocated and is
  complete: its independent pass finished in 849.041 seconds at 3.897 GB, matched all 13 hashes and
  passed the full structural audit. A parity-gated critical-path correction then completed a third
  cTrader pass in 539.170 seconds at 5.536 GB; all 13 hashes again match the pre-change canonical
  output. The accepted correction shares identical native-state bootstrap positions and exposes
  exact origin-ID bounds for Parquet pruning while retaining exact membership. Synthetic timings
  were 2.69× and 3.27× faster respectively; 49 analysis tests, all 245 adaptive-management tests
  and focused Ruff passed. An in-flight pre-change SPDR-023 crypto pass was operator-authorised to
  stop inside the confirmed bootstrap hotspot; atomic publication left no final or temporary
  crypto output.
- **Task 7 closed 2026-08-04.** SPDR-023 crypto canonical analysis published its 13 artifacts at
  12:23 local and its independent reproduction pass at
  `/private/tmp/spdr023-crypto-analysis-repro.ICXKaW/pass` completed at 13:27 local. The session
  running them was interrupted after both had already published atomically, so wall time and peak
  RSS were not persisted for this cell; both outputs are complete and were verified afterwards.
  All 13 relative names and SHA-256 hashes match. `SPDR-023/results/analysis/reproduction-hashes.json`
  was then written for both universes and independently re-verified against all 52 canonical and
  temporary files (2 universes x 13 artifacts x 2 passes, zero mismatches). The three SPDR-023
  temporary roots (`spdr023-crypto-analysis-repro.ICXKaW`, `spdr023-ctrader-analysis-repro.34m2Y4`,
  `spdr023-ctrader-analysis-optimized.DBVEB7`) were resolved, confirmed non-symlink, deleted and
  confirmed absent.
- SPDR-023 crypto structural audit: 25 symbols, both entry variants (`E_TOUCH`/`E_CLOSE`), all four
  orientation pairs, `FIXED_NATIVE`/`NATIVE`/`NATIVE_COMBINATION` classes, both lenses
  (`COMMON_ORIGIN_OCCUPANCY_INCLUSIVE`, `COMMON_CLOSE_TRADE`), zero duplicate origin or shared-trade
  keys, 1,742,747 shared-fill rows with zero null `_entry_ns` on either side, all four controls
  (`TIME_DERANGEMENT`, `MAGNITUDE_MATCH`, `FIXED_DEVICE`, `FIXED_NATIVE_PARAMETER`) `COMPUTED` with
  16,000/16,002 outcome-bearing rows and explicit `undefined_reason` on the two undefined rows, and
  no verdict/winner/rank/deployability field.
- All six cells re-opened together: three manifests report `all_equal=true`, each universe has
  exactly 13 artifacts, every controls table is `COMPUTED`, and both lenses are present everywhere.
- **Known limitation (all six cells, not specific to this cell):** the spread/cost disclosure is
  carried in each run's `config.json`/`run_summary.json`
  (`spread_cost_status=UNAVAILABLE_NOT_CHARGED`, `spread_rt_bps=null`,
  `cost_scope=PARTIAL_FEES_FUNDING_ONLY`) but the mirrored `spread_cost_status` / `cost_scope`
  columns in `per_stratum_estimates.parquet` are null, because the analysis reads those keys at the
  top level of the run config while the run nests them under `spread_cost_disclosure`. It affects
  only the mirrored descriptive columns, is identical in all six cells, and changes no estimate. The
  disclosure is therefore stated explicitly in every `screen.md` and `analysis.md` rather than
  re-running six analyses to repopulate two columns.

Execute the remainder in this order, without asking for a routine continuation gate:

1. **Run SPDR-023 crypto canonical and reproduction passes.** Recheck the refreshed disk/memory
   margin, use only `SPDR-023-crypto-train-20260803T140238Z`, `--jobs 1` and fresh output paths.
   Require 13/13 equality and the full population/control audit. Persist the SPDR-023 manifest,
   verify it against all 26 files, then remove only the two exact SPDR-023 temporary roots.
2. **Close Task 7.** Re-open all six summaries and three manifests; prove six 13/13 matches, exact
   row keys/accounting, both native lenses, actual common fills/closes, correct device populations,
   computed controls and no prohibited result fields. Record production/reproduction wall time and
   peak RSS for every cell in this handoff.
3. **Complete Task 8 with fresh analyst contexts.** First generate neutral `screen.md` files from
   the gated runs. Then use one isolated data-analyst context per experiment; each reads only its
   corrected raw/canonical artifacts and must keep universes, entry variants, population lenses,
   controls and limitations separate. Run row-key and prohibited-claim audits. No analyst may
   mutate emissions, read another analyst's prose, or issue an experiment/family verdict.
4. **Complete Task 9 and stop at the operator gate.** Run the full Python suite, focused Ruff and
   `git diff --check`; audit the programme boundaries and six integrity/reproduction records;
   update only neutral indexes/governance text and evidence rows. Final status is `AMENDED RERUN
   COMPLETE; ANALYSIS COMPLETE; AWAITING OPERATOR INTERPRETATION`. Do not commit, push, deploy,
   contact TEST/holdout, invoke XENA, change family status or supply the combined interpretation.

Resource directive: the original 58.81 GB crypto forecast is superseded for this matched grid by
the measured 21.2 GiB SPDR-022 crypto output; the required 25% margin is 26.5 GiB. Recheck before
each heavy stage. If free space or memory falls below the refreshed margin, finish the current
atomic write when safe, preserve state, and recover only explicitly temporary/non-canonical files.

---

### Task 7: Produce reproducible canonical analysis artifacts

**Outputs:** 13 artifacts under each
`python/experiments/SPDR-02X/results/analysis/{ctrader,crypto}/` plus a persistent reproduction
manifest per experiment.

- [x] **Step 1: Analyse one cell at a time with `--jobs 1`**

Use the matching experiment wrapper and corrected raw run. Complete the production analysis, free
its process memory, then continue. Never analyse two breach crypto cells concurrently.

- [x] **Step 2: Run an independent second pass**

For each cell, write a second pass to a fresh directory under `/private/tmp`. Do not copy the first
pass. Hash all 13 artifacts from both passes with SHA-256 and compare relative names.

- [x] **Step 3: Persist reproduction evidence**

Write `results/analysis/reproduction-hashes.json` for each experiment with run ID, universe,
artifact name, first-pass hash, second-pass hash and equality. Then remove the temporary second
pass.

Pass: 13/13 hashes equal in all six cells. A mismatch stops analysis publication until explained
and corrected.

- [x] **Step 4: Audit content and populations**

For each cell assert:

- exact unique full row keys and exact row accounting;
- both native lenses are present and clearly labelled;
- shared-fill rows have actual fills on both sides;
- eligible/fill/close/common counts reconcile to raw ledger states;
- device tables use the correct episode population;
- all controls are `COMPUTED` and carry outcomes;
- no verdict, winner, pass/fail-value or top-N field exists.

- [x] **Step 5: Record analysis resource facts**

Write wall time and peak RSS for each cell into this handoff. If a safe optimisation was used,
record its equivalence proof and before/after measurement.

---

### Task 8: Write the three neutral screens and independent analyses

**Files:**

- Create: `python/experiments/SPDR-021/screen.md`
- Create: `python/experiments/SPDR-022/screen.md`
- Create: `python/experiments/SPDR-023/screen.md`
- Create in fresh analyst contexts: `python/experiments/SPDR-02{1,2,3}/analysis.md`

- [x] **Step 1: Regenerate neutral `screen.md` records**

Each file records corrected run IDs/paths, integrity status, origin/event/fill/close counts,
complete arm/state counts, both universe sections, control availability, spread limitation and
links to complete tables. It must not contain an economic conclusion.

- [x] **Step 2: Run one fresh data-analyst context per experiment**

Each analyst reads the corrected raw emissions and canonical artifacts, not the invalidation
summary or another analyst's prose. The analyst may write probing scripts under that experiment's
`analysis_code/`, but must not mutate canonical emissions or hide rows.

- [x] **Step 3: Enforce required analysis content**

Each `analysis.md` must:

- keep cTrader and crypto separate;
- keep `E-TOUCH` and `E-CLOSE` separate for SPDR-022/023;
- show the occupancy-inclusive per-origin lens and actual common-fill/common-close lens separately;
- show fixed/direct/reverse and all four native orientation pairs;
- show individual components and devices before combinations;
- retain selected, excluded, filled, unfilled, closed and censored populations;
- report estimate, interval, correct population count, effective count and MDE without making power
  a gate;
- show fixed-device and plain-baseline comparisons plus both executed controls;
- report supporting, contrary, concentrated and unresolved observations plainly;
- disclose fees/funding-only cost scope and missing spread;
- avoid verdict, universal-effect, winner, tradability and deployability language.

- [x] **Step 4: Run row-key and claim-boundary audits**

Every full table row must be represented or linked. No selective prose table may replace full
reporting. Searches for prohibited labels may match only explicit boundary statements.

Pass: all three analyses are present, neutral, reproducible and based only on corrected runs.

---

### Task 9: Complete Task 10 closeout and operator handoff

**Files:**

- Modify neutral status only: `python/experiments/INDEX.md`
- Modify neutral status only: `docs/experiments-docs/INDEX.md`
- Modify neutral status only where stale execution text remains:
  `docs/references/chapter-06-governance.md`
- Modify evidence/disposition rows only, never family status:
  `docs/signal-registry/candidate-families/cf-voldir-001.md`
- Update this handoff with every completed task and final evidence.

- [x] **Step 1: Run final verification**

```bash
cd python
PYTHONPATH=. .venv/bin/pytest tests -q
.venv/bin/ruff check src/xen/adaptive_management \
  tests/test_adaptive_management_*.py experiments/SPDR-02{1,2,3}
cd ..
git diff --check
```

Pass: zero failures/findings. Record exact counts and warnings.

- [x] **Step 2: Verify programme boundaries**

Search and inspect to prove:

```text
zero TEST output or TEST read
zero holdout timestamp contact
zero XENA action
zero family-status transition
zero verdict/winner/deployability label outside explicit prohibitions
zero live reference to invalid first-pass results
six corrected runs and six passing integrity records
six 13/13 reproduction hash matches
three screens and three analyses
```

- [x] **Step 3: Update neutral indexes and evidence rows**

Use status: `AMENDED RERUN COMPLETE; ANALYSIS COMPLETE; AWAITING OPERATOR INTERPRETATION`.
Do not write a checkpoint retrospective, experiment verdict or family decision.

- [x] **Step 4: Finalise this handoff**

Check every completed task and add:

```text
amendment paths
fresh six-cell run stamp, paths, durations, sizes and peak RSS
hard-integrity result per cell
origin/fill/close and row-accounting totals
analysis durations and reproduction hashes
test/lint/diff results
screen.md and analysis.md paths
limitations and unresolved questions
confirmation that all three experiments ran independently
```

- [x] **Step 5: Give the operator one concise handoff and stop**

Lead with whether the corrected evidence is clean and complete. Link the three analyses and this
handoff. State the remaining limitations plainly. The operator makes the combined interpretation;
the executing agent does not.

---

## Task 9 closeout evidence, 2026-08-04

**Status: AMENDED RERUN COMPLETE; ANALYSIS COMPLETE; AWAITING OPERATOR INTERPRETATION.**
Tasks 1-9 are complete. No commit, push, deployment, TEST/holdout contact, XENA action,
family-status change or experiment verdict was made.

### Verification

- `PYTHONPATH=. .venv/bin/pytest tests -q` -> **538 passed, 4 skipped, 3 third-party warnings**.
- `ruff check src/xen/adaptive_management tests/test_adaptive_management_*.py experiments/SPDR-021
  experiments/SPDR-022 experiments/SPDR-023` -> **All checks passed!**
- `git diff --check` -> clean (trailing whitespace inside SPDR-023 table dumps was stripped first).

### Programme boundaries

- No TEST or holdout artifact was opened; every fence read is TRAIN with `status: PINNED`.
- No XENA action, no family-status transition; `cf-voldir-001.md` records evidence only.
- Zero live references to the invalidated first-pass stamp anywhere under `python/experiments/`
  or `docs/` outside the dated invalidation record and this ledger's historical path list.
- Six corrected runs at stamp `20260803T140238Z`, six passing integrity records (14/14 hard checks
  each), six 13/13 reproduction hash matches, three screens and three analyses on disk.
- Prohibited labels (`SUPPORTED`, `REFUTED`, winner, best arm, tradable, deployable, top-N) appear
  only inside explicit boundary statements and the verbatim quoted cost-disclosure block.

### Amendment paths

- `docs/experiments-docs/checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/adaptive-management-design.md` §12
- `docs/superpowers/plans/2026-08-03-spdr-021-023-first-pass-invalidation.md`
- `python/experiments/SPDR-02{1,2,3}/design.md`
- `docs/superpowers/plans/2026-07-31-spdr-021-023-design-checklist.md`

### Six-cell execution and analysis facts

| Cell | Exec jobs | Exec wall | Raw size | Origins | Fills / closes | Hard integrity | Production analysis | Reproduction analysis |
| --- | ---: | ---: | ---: | ---: | ---: | :---: | --- | --- |
| SPDR-021 cTrader | 1 | 493 s | 733,256 KiB | 20,061 | 158,547 / 158,395 | 14/14 | 376.868 s / 2.771 GB | 312.691 s / 2.650 GB |
| SPDR-021 crypto | 2 | 1,167 s | 3,596,712 KiB | 102,160 | 771,135 / 770,178 | 14/14 | 1,987.793 s / 3.070 GB | 2,054.076 s / 3.052 GB |
| SPDR-022 cTrader | 2 then 1 | 5,816 s | 4,277,760 KiB | 44,700 | 1,448,950 / 1,448,594 | 14/14 | 845.466 s / 4.295 GB | 842.795 s / 4.400 GB |
| SPDR-022 crypto | 1 | 8,659 s | 22,222,568 KiB | 231,121 | 7,405,640 / 7,402,289 | 14/14 | 5,035.342 s / 8.030 GB | 4,952.383 s / 7.653 GB |
| SPDR-023 cTrader | 1 | 1,933 s | 4,290,136 KiB | 44,700 | 1,448,928 / 1,448,570 | 14/14 | 1,056.134 s / 4.084 GB | 849.041 s / 3.897 GB |
| SPDR-023 crypto | 1 | 9,149 s | 22,292,148 KiB | 231,121 | 7,435,982 / 7,432,667 | 14/14 | not persisted (session interrupted after atomic publication) | not persisted (same) |

Row accounting passed in all six cells with no missing, extra or duplicate key. Estimand
`blocking_pass=true` in all six. Absorbing exit failures: 0 in all six.

Reproduction manifests: `python/experiments/SPDR-02{1,2,3}/results/analysis/reproduction-hashes.json`,
each `all_equal=true` for both universes; the SPDR-023 manifest was independently re-verified
against all 52 canonical and temporary files before its temporary roots were deleted.

### Outputs

- Screens: `python/experiments/SPDR-02{1,2,3}/screen.md` (generated by
  `python/experiments/SPDR-021/analysis_code/generate_screen_records.py`).
- Analyses: `python/experiments/SPDR-02{1,2,3}/analysis.md`, each written in a separate isolated
  analyst context that read only its own experiment's artifacts.
- Indexes updated to the neutral status: `python/experiments/INDEX.md`,
  `docs/experiments-docs/INDEX.md`, `docs/references/chapter-06-governance.md`,
  `docs/signal-registry/candidate-families/cf-voldir-001.md` (evidence row only).

### Limitations and unresolved questions carried to the operator

1. **Cost is effectively absent, not merely partial.** Spread is never charged
   (`UNAVAILABLE_NOT_CHARGED`) as declared, and all three analysts independently found engine
   commissions of exactly `0.00` and `partial_cost_bps` null on every row. All money figures are
   gross; net reads would be materially worse.
2. **Mirrored disclosure columns are null** in `per_stratum_estimates.parquet` in all six cells
   (`analysis.py` reads the keys at config top level; the run nests them under
   `spread_cost_disclosure`). Descriptive only; no estimate is affected.
3. **Time derangement is non-diagnostic for the origin-lens point estimates** in SPDR-021 and
   SPDR-022: a mean over origins is permutation-invariant, so the control reproduces the raw
   estimate to floating-point and only the interval moves. The future-shift tripwire is separate
   and passed. Magnitude matching does move every row.
4. **Structural zero-delta identities.** In SPDR-021 the native threshold is an admission rule, not
   a price offset, so on shared fills the paired delta is exactly 0 on all rows; in SPDR-023 every
   `BAND_H` arm has an exactly zero paired delta for the same structural reason. Native information
   therefore lives in *which* origins are admitted, not in the shared trade.
5. **Price-only device populations are thin and selection-conditioned.** `reach_rate`/`stop_rate`
   saturate at 0 or 1 for pure TARGET/STOP arms, and some common-close cells hold single-digit
   trades; these are retained unpruned and must not be read as effects.
6. **`payoff_scale_ratio` is null throughout `selection_checks.parquet`** and
   `excluded_mean_median_gap` is structurally zero, so that check cannot detect outcome-based
   selection in this design.
7. **Stale field:** `run_summary.json` still carries `hard_integrity: "NOT_YET_RUN_TASK_8"` while
   `integrity_selfcheck.json` records the completed 14/14 block with `blocking_pass: true`.
8. **SPDR-023 crypto analysis timings were not persisted** because the session was interrupted
   after both passes had already published atomically. Both outputs are complete and verified.

All three experiments ran independently: separate wrappers, separate runs, separate analyses, and
three isolated analyst contexts. No result gated another.

---

## Stop conditions

Stop and preserve the current atomic state when any of these occurs:

- an amended requirement conflicts with Nautilus behavior and satisfying it would change the
  research grid or estimand;
- TEST, holdout, wrong-universe or non-pinned-manifest contact;
- an unresolved design-checklist row;
- hard-integrity failure after two batched correction cycles;
- a position remains open after the declared horizon or exit-failure path;
- corrected clean/resume/reproduction hashes differ without an understood intended schema change;
- disk or memory falls below the refreshed safety margin;
- completion would require a commit, push, deployment, XENA action, family-status change or
  operator verdict.

Do not stop because an effect is small, inconsistent, uncertain, concentrated, unpowered or
contrary to expectation. Those are observations to report.
