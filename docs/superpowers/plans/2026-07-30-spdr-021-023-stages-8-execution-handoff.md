# SPDR-021/022/023 Stages 8 Through Execution Handoff Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` (recommended) or
> `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox
> (`- [ ]`) syntax for tracking.

**Goal:** Complete integrity enforcement and final implementation verification, then—only under
the authority rule below—run and neutrally analyse all six TRAIN cells for SPDR-021/022/023.

**Architecture:** Keep the three experiments independent while sharing the frozen
`xen.adaptive_management` implementation. Add one integrity module that validates raw run
artifacts before analysis, and operational recovery/progress that cannot alter the arm grid.
Execute each experiment sequentially; analyse crypto and cTrader separately from raw emissions.

**Tech Stack:** Python 3.13, Polars, NumPy, pytest, Ruff, NautilusTrader 1.230.0,
`xen.nautilus.catalog_fence`, emission contract v1, canonical `xen.adjudication`.

**Execution entrypoint:** Use `research-pipeline` as the lifecycle orchestrator and
`superpowers:executing-plans` for this document. The orchestrator coordinates stages; it does not
replace any pass criterion or operator gate below.

## Current handoff state

### Completed before this continuation plan

- [x] **Original Task 1 — frozen contracts and exact arm lattice.**
  `contracts.py` declares 8 executable component IDs, 64/128/128 adaptive native arms, the
  applicable device matrix, 5 component combinations and 3 device combinations.
- [x] **Original Task 2 — causal volatility features.**
  `features.py` and frozen parity fixtures cover calibration, range/swing scale, slow state,
  forecast states, shock, swing opportunity and tail risk using confirmed information.
- [x] **Original Task 3 — common origins and fixed entry populations.**
  `entries.py` retains no-event, unfilled and blocked origins; breakout and breach populations are
  independently identified.
- [x] **Original Task 4 — native and external schedules.**
  `native_parameters.py` and `policies.py` materialise direct, reverse and all four orientation
  pairs; native parameters are not crossed with management; sizing stays separate from exits.
- [x] **Original Task 5 — Nautilus execution.**
  `strategy.py` and `engine.py` execute entry orders and competing exits on native one-minute bars
  with one engine process per work unit.
- [x] **Original Task 6 — fenced runners and canonical emissions.**
  `runner.py` and three independent wrappers are TRAIN-only, universe-separated, atomic and
  non-overwriting. Combined raw tables live at the run root; canonical emissions are separated by
  instrument under `cells/`.
- [x] **Original Task 7 — origin-native and device-native analysis foundation.**
  `analysis.py` and three independent analysis wrappers emit all 13 declared analysis artifacts,
  keep breach variants/universes separate, and carry no verdict or winner fields.
- [x] **Independent Tasks 1–5 review and batch correction.**
  The prior review found 19 issues; all were routed in one batch and corrected before Stage 6.
- [x] **Stage 6 dry-run verification.**
  All 6 experiment × universe dry runs passed and created no result directories.
- [x] **Stage 7 schedule-shape verification.**
  Synthetic real-lattice smokes passed for SPDR-021/022/023, including native orientations and
  allowed device combinations.

### Verified at continuation start — 2026-07-30

- [x] `git diff --check` returned clean.
- [x] Adaptive-management suite: `120 passed`.
- [x] Complete Python suite: `412 passed, 4 skipped, 3 third-party/runtime warnings`.
- [x] Stage 8 files remain absent; no Stage 8 implementation has been claimed.
- [x] No full TRAIN experiment has run.
- [x] Nothing is staged or committed. Preserve that state unless the operator separately requests
  a commit.

### Remaining

- [x] Continuation Task 2 — close Stage 7 acceptance gaps against complete emitted-run fixtures.
  Complete fixture coverage now exercises all seven arm classes, four schedule states and all five
  management devices. Analysis emits the required device-native and shared-context fields,
  validates exact declared arm coverage and fixed comparators, rejects dropped origins and
  overwrite attempts, and keeps missing spread disclosed rather than imputed.
  Verification: `11 passed`; focused Ruff check passed.
- [x] Continuation Task 3 — implement Stage 8 hard integrity and informative controls.
  `integrity.py` now separates 13 blocking integrity checks from informative derangement and
  magnitude controls, reconciles real Nautilus report shapes, and atomically writes the five
  required JSON artifacts with exact source hashes. Independent mutations cover every named hard
  failure class, including SPDR-014 breach-entry parity and deterministic replay mismatch.
  Verification: Stage 8 `21 passed`; full adaptive-management suite `143 passed`; Ruff clean.
- [x] Continuation Task 4 — deterministic recovery, progress and resource preflight.
  `runner.py` publishes each symbol as a hash-verified unit inside one `.<name>.inprogress`
  directory, resumes only units whose config and bytes match, emits the declared progress payload
  with a 10-minute heartbeat, and `preflight.py` estimates a run read-only. Clean, `jobs=2` and
  interrupted-then-resumed runs are byte-identical.
  Verification: adaptive-management suite `157 passed`; Ruff clean.
- [x] Continuation Task 5 — final implementation verification and design audit.
  Full suite `455 passed, 4 skipped`; Ruff and `git diff --check` clean; six metadata-only dry runs
  each printed only their own experiment at `band=TRAIN` and created no output. Synthetic device
  smoke and a bounded real-catalog smoke (SPDR-021, cTrader EURUSD, 90 TRAIN days) reached a
  passing estimand gate and `blocking_pass=true`. Checklist with per-clause evidence:
  `docs/superpowers/plans/2026-07-31-spdr-021-023-design-checklist.md`.
- [x] Continuation Task 6 — SPDR code-asserted pre-execution acceptance.
  55 clause rows across the three experiments, zero failures, each with code location, test
  location and observed evidence from a bounded real run per experiment.
- [x] Continuation Task 7 — resource preflight and authority gate.
  Preflight artifacts under `python/experiments/SPDR-02{1,2,3}/results/preflight/`. Operator
  granted TRAIN execution authority for the six cells on 2026-07-31.
- [x] Continuation Task 8 — six TRAIN runs. All six cells complete and validated; see the
  execution record below.
- [ ] Continuation Tasks 9–10 — independent analysis and operator handoff. Blocked on analyser
  capacity, not on the runs; see "Task 9 progress — 2026-07-31" and
  `docs/superpowers/plans/2026-07-31-spdr-021-023-analysis-capacity-problem.md`.

## Execution record — run stamp `20260731T004708Z`

| cell | executed | estimand validation | integrity | size | location |
| --- | --- | --- | --- | --- | --- |
| SPDR-021 cTrader | yes | 3/3 cells | `blocking_pass=true` | 611 MB | local |
| SPDR-021 crypto | yes | 25/25 cells | `blocking_pass=true` | 2.96 GB | local |
| SPDR-022 cTrader | yes | 3/3 cells | `blocking_pass=true` | 2.82 GB | local |
| SPDR-023 cTrader | yes | 3/3 cells | `blocking_pass=true` | 2.83 GB | local |
| SPDR-022 crypto | yes | 25/25 cells | `blocking_pass=true` | 14.6 GB | `/Volumes/SSID/Xen/data/nautilus_runs/` |
| SPDR-023 crypto | yes | 25/25 cells | `blocking_pass=true` | 14.6 GB | local |

Re-verified from disk 2026-07-31: all six cells hold `blocking_pass=true` on 13/13 hard checks
with `row_accounting.pass=true`. Note `run_summary.json` still carries the stale literal
`hard_integrity: "NOT_YET_RUN_TASK_8"`; `integrity_selfcheck.json` is the authority.

Observed row counts: SPDR-021 cTrader 20,061 origins / 1.30M episodes; SPDR-021 crypto 102,160 /
6.64M; SPDR-022 cTrader 44,700 / 5.81M; SPDR-023 cTrader 44,700 / 5.81M; SPDR-022 crypto 210M
total rows across all artifacts. Both breach cTrader cells share origin and episode counts and
differ only in fills and positions, as MOMO and MR share one zone-origin clock.

### Defects found by real data during execution, all fixed with tests

1. Two-sided origins (one bar qualifying long and short) were rejected as an overlap; the overlap
   key is now the origin and the single-slot rule resolves the tie as `BLOCKED_ACTIVE`.
2. NaN features passed the null check and reached the engine as a NaN price; NaN is now
   `NO_FEATURE`, parameters are nulled, and a NaN schedule is refused before the run.
3. Bar volume (a venue tick count) capped fills and split one entry into several, re-arming the
   hold timer; a fill-capacity floor is applied and repeat entry fills no longer re-record.
4. H1 actionable timestamps with no traded minute stranded 5,510 schedule rows; rows now act on
   the first minute at or after their time, and rows past the final bar are recorded `CENSORED`.
5. State-ledger and Nautilus-report typing made emissions unreadable by the adjudication shim.
6. The golden-trace key counted one CLOSED row per episode instead of per arm.
7. Row accounting and entry parity assumed breach origins carry an entry variant; zone origins are
   common to both variants.
8. The order-status whitelist rejected `DENIED` and orders still live at the fence end.
9. Combination-arm exit legs failing at the same instant looked like duplicate result keys; the
   failing leg is now named.
10. Base trade size was a flat `1`, below the size increment of several crypto instruments, so a
    0.5x SIZE arm rounded to zero and the venue rejected it. Base is now 1000 increments of each
    instrument's own grid, and `base_size_increments` is part of the run identity.
11. Magnitude-matched controls aborted on unwarmed components instead of holding them out.
12. AppleDouble sidecars (`._*`) on the external volume were hashed as run artifacts and read as
    instrument cells.

### Task 9 progress — 2026-07-31

Execution (Task 8) is finished. Task 9 is open and has produced **no deliverable yet**: no
`results/analysis/` directory, no `screen.md`, no `analysis.md`. One cell (SPDR-021 cTrader) has
been analysed end-to-end as a capacity measurement, into a scratch directory, not published.

**The analyser could not have completed the six cells as written.** A first attempt on
SPDR-021 cTrader — the smallest cell — held 5.5 GB and was still running at 10 minutes while the
machine sat at 3.0 GB of a 4 GB swap. Profiling on bounded fixtures then showed the cost was not
where the run's memory story suggested:

| stage (1 200-origin fixture) | before | after |
| --- | --- | --- |
| read four parquets | 0.04s | 0.04s |
| `validate_full_reporting` | 0.09s | 0.03s |
| `_attach_path_diagnostics` ×2 | 0.90s | 0.18s |
| `origin_estimates` | 7.53s | 7.56s |
| `paired_estimates` | 5.14s | 5.19s |
| five `_device_table` calls | >5 min (killed) | 58s |

**Four bit-identical optimisations landed** in `src/xen/adaptive_management/analysis.py`, all
operator-approved, none touching the fence, the causal lag, the arms, the dates, the populations
or which rows are reported:

1. **NumPy metric kernels for the bootstrap draws.** `_paired_metric_interval` materialised two
   complete ~50-column DataFrame gathers per draw, 2 000 draws per metric per group, while the
   metric functions read at most four columns. Draws now gather NumPy columns. New parametrised
   test asserts each kernel equals its polars reference across nulls, NaNs, duplicated rows,
   reversed order and empty input.
2. **Comparator lookup by partition.** `_device_table` re-scanned the entire policy frame once per
   group to find the comparator; it now partitions once. Invisible on small fixtures, thousands of
   full passes over 37M rows on a breach crypto cell.
3. **`validate_full_reporting` by join.** ~260 full scans plus multimillion-element Python string
   sets became a group-by, an anti-join and a count comparison. Deliberately restricted to
   variants present in the origin ledger, so the check stays exactly as strict as before — a
   widened check could false-stop a valid run.
4. **Preallocated path diagnostics, projected ledger.** 11 Python lists of boxed floats became
   float64 arrays with a per-column written mask, preserving null-versus-NaN exactly. The ledger
   (78.6M rows on the breach crypto cells) is column-projected on read and released before the
   estimate stages allocate.

Declined, on the record: collapsing the bootstrap to per-block sums and counts. It is a large
speed win but `sum of sums / total count` rounds differently from `mean(concat)`, which would
break byte-identical reproduction and shift printed CI digits.

**Verification:** 12-origin fixture 892.7s → 29.5s (30×) with **all 13 artifacts byte-identical**
to the pre-change baseline; `pytest tests -q` `492 passed, 4 skipped`; Ruff clean on
`src/xen/adaptive_management`, `tests/test_adaptive_management_*.py` and the three experiment
directories.

**Measured full cell — SPDR-021 cTrader:** 766s (12.8 min), peak RSS 5.12 GB, 13 artifacts, rc 0.

**Still blocked.** CPU is no longer the constraint; memory is, on four of six cells. See
`docs/superpowers/plans/2026-07-31-spdr-021-023-analysis-capacity-problem.md` for the projections,
the options and the open decision.

### Open issue — engine memory is bounded by the Nautilus cache, not by our own state

**Symptom.** Swap grew to 70-80 GB and the machine killed the run (and once the desktop
application). Observed three times: twice with `--jobs 4`, once with integrity running beside a
run. `--jobs 1` has completed a full 25-symbol breach crypto cell (SPDR-022) without incident.

**Cause.** Each engine process retains every `Order` and `Position` object for the whole symbol
in the Nautilus cache. A breach crypto symbol carries 1.5-2.4M schedule rows and on the order of
a million orders, so per-engine memory grows monotonically into several GB and never falls. Four
concurrent engines multiply that. Our own per-episode dictionaries were a secondary term and are
now released at terminal states, which helped at the margin but does not bound the total.

**Why the obvious fix is wrong.** `Cache.purge_closed_orders` / `purge_closed_positions` exist,
but the run's emission is generated from that same cache by
`engine.trader.generate_orders_report()` and its siblings. Purging mid-run would silently drop
rows from `orders.parquet` / `fills.parquet` / `positions.parquet`. Do not call the purge API
without first changing where the emission comes from.

**Correct fix, for a dedicated task.** Capture order, fill and position events to disk as they
occur (the strategy already receives every one of them), build the per-unit artifacts from those
streams instead of from the end-of-run cache, then purge closed orders and positions behind a
safety buffer. That bounds engine memory by open episodes rather than by total episodes, and is
what would make `jobs > 1` safe on breach-sized symbols.

**Until then.** Run crypto breach cells with `--jobs 1`, and run integrity separately. Measured
throughput at `jobs=4` was about 6-7 minutes per symbol against 10.5-16.7 at `jobs=1`, so the
parallel path is genuinely faster per symbol - it simply does not survive 25 of them on a 16 GB
machine.

### Task 11 (next) — stream order and position artifacts during the run, then purge

**Why.** Engine memory is bounded by the Nautilus cache, which holds every `Order` and
`Position` for the whole symbol because the emission is generated from it at the end. This is the
open issue above. Emitting during the run removes the reason to keep them, so the cache can be
purged behind the writer and memory becomes a function of open episodes rather than of total
episodes. It also makes `jobs > 1` usable: `jobs=4` measured 6-7 minutes per symbol against
10.5-16.7 at `jobs=1`, and only failed because it could not survive 25 symbols.

**Files:**
- Modify: `python/src/xen/adaptive_management/strategy.py`
- Modify: `python/src/xen/adaptive_management/engine.py`
- Modify: `python/tests/test_adaptive_management_strategy.py`

**Route chosen.** Capture the exact report rows incrementally rather than adopting Nautilus's
event stream. `ReportProvider` builds a row as `order.to_dict()` and then
`DataFrame(...).set_index("client_order_id").sort_index()`, converting `ts_last` / `ts_init` to
datetimes. That is reproducible per event. Nautilus `StreamingConfig` /
`StreamingFeatherWriter` is the alternative but emits the event schema, which would force a
rewrite of the emission contract mapping and its validation; do not take that route without a
separate design decision.

- [ ] **Step 1: Write the failing equivalence test**

Run one bounded real symbol twice: once on the current end-of-run reports, once with incremental
capture. Assert `orders.parquet`, `fills.parquet` and `positions.parquet` are byte-identical, and
that the state ledger is unchanged. Pass of this step: it fails only because incremental capture
does not exist yet.

- [ ] **Step 2: Capture orders and positions as they terminate**

On each terminal order event and each position close, append `order.to_dict()` /
`position.to_dict()` to a batch and flush to a part file, reusing the ledger's batching pattern
(`flush_ledger`, fixed schema, atomic part files, `ledger_batch_rows` as the operational knob).
Assemble at stop by streaming the parts. Reproduce the reporter exactly: filter fills on
`filled_qty > 0`, sort by `client_order_id`, and convert `ts_last` / `ts_init` the same way.

- [ ] **Step 3: Purge behind the writer**

Only after a row is durably written, call `cache.purge_order` / `cache.purge_position` (or the
closed-bulk variants) behind a safety buffer so nothing still referenced by an open episode is
dropped. Never purge an order whose episode still holds a live hold deadline.

Pass: peak engine RSS on a full-span breach crypto symbol stops growing with symbol count; record
the measured peak against the pre-change baseline (several GB and monotonic).

- [ ] **Step 4: Prove the emission is unchanged**

Re-run the Step 1 equivalence check on a full-span symbol, not just a bounded one, and re-run the
existing byte-identity tests (two runs of one work unit; clean vs `jobs=2` vs resumed).

Pass: identical bytes for all three report artifacts and the ledger; full suite green; Ruff clean.

- [ ] **Step 5: Re-measure the worker ladder**

With memory bounded, re-run the `jobs=1` / `2` / `4` comparison on the same symbols and record
time-to-first-batch, minutes per symbol, peak RSS and page-outs per second. Only then decide the
default `jobs` for breach crypto cells.

Stop conditions: any byte difference in the three report artifacts or the ledger; any purge that
removes an order still reachable by an open episode.

### Performance and capacity work

- Nautilus `PortfolioAnalyzer` accumulated per-trade PnL by `pd.concat` per closed trade, which is
  quadratic. Disabled with a guard that fails the run if a future version accumulates again.
  360-day symbol: 276 s to 45 s; scaling became linear.
- `init_id` (a per-event UUID) is dropped from emissions, so two runs of one work unit are now
  byte-identical. They were not before.
- The state ledger streams to disk in batches instead of being held as one Python list.
- Run assembly streams each artifact from the per-symbol units; it previously concatenated 210M
  rows in memory and was killed by the kernel after every symbol had succeeded.
- Integrity reconciliation was two nested row-wise loops (118k x 3.5M rows on one cTrader cell);
  rewritten as grouped joins, 600 s+ to 0.4 s, with the original implementation kept as a test
  reference.
- Integrity now reads only the columns each check needs and releases each frame, after the
  eager whole-run load was killed by the kernel on the breach crypto cell.
- Parallel preparation was hoisted out of the worker pool, so peak memory scales with `jobs`
  rather than with symbol count.
- Per-episode strategy state (`_execution_rows`, `_by_client_order`) is released once an episode
  reaches a terminal state or closes. Emissions are unchanged: every release point is one where a
  later event previously hit an idempotence guard and wrote nothing. Episodes holding a live hold
  deadline are never released, so stop-time `OPEN_AT_FENCE_END` rows are unaffected.
  Note: SPDR-023 crypto's first 13 symbols ran before this change and the remainder after, since
  engine children import at spawn. The change is memory-only, so the cell stays consistent.

### Measured resource facts

- One full-span cTrader symbol: SPDR-021 122 s / 3.4 GB peak; SPDR-022 999 s / 961 MB published.
- SPDR-022 crypto at `jobs=1`: 25 symbols in 4 h 20 min, 10.5-16.7 min per symbol, 14.6 GB.
- `jobs=3` on 16 GB filled swap (11.9 of 12.3 GB) at 6.3 GB resident; throughput was not measured
  before the run was stopped, so no conclusion about its speed is recorded.
- Estimator constants are calibrated against measured runs; earlier model-only estimates
  overstated disk by roughly 5x and wall clock by an order of magnitude.

## Authority rule

This document is a plan, not fresh execution authority.

- If the executing session was started with the matching experiment prompt in
  `.ignore/prompts/prompts.md`, that prompt explicitly authorises its two full TRAIN runs; proceed
  after every pre-execution gate below passes.
- Otherwise stop after Task 6 and ask for TRAIN execution authority.
- No authority permits TEST, global holdout, cTrader data on or after 2024-12-13, XENA,
  deployment, family-status changes, a final verdict, staging, committing, pushing or publishing.

## Global constraints

- Read `AGENTS.md` first. Human-facing updates stay short and plain.
- The dirty worktree is authoritative. Do not reset, restore, clean, checkout or create a
  worktree from stale HEAD.
- The approved design in
  `docs/experiments-docs/checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/adaptive-management-design.md`
  is binding and wins over this plan.
- SPDR-021, SPDR-022 and SPDR-023 never gate one another on economic results. Integrity failures
  may stop invalid code or emissions.
- Crypto and cTrader are separate universes and are never pooled.
- Nautilus orders, fills and positions are execution truth. Do not reconstruct which competing
  order filled first from OHLC.
- Native parameters are never crossed with external management. Position size is never crossed
  with exit combinations.
- Report every fixed, direct, reverse, state, entry variant and allowed combination. No
  winner-only table and no `SUPPORTED`, `REFUTED`, `PASS`, `FAIL`, positive/negative, tradable or
  deployable value label.
- Confidence intervals, effective counts, power and MDE are informative only.
- Spread stays unavailable and uncharged. Every money-bearing artifact repeats
  `UNAVAILABLE_NOT_CHARGED`, `spread_rt_bps=null`, `PARTIAL_FEES_FUNDING_ONLY`, and the warning
  that reported net performance is overstated.
- Use TDD for every code change: failing focused test, observed failure, minimum implementation,
  focused pass, then regression pass.
- Do not add research parameters to any CLI. An operational `--resume` flag is allowed by the
  execution prompts; it must not change symbols, dates, arms, features or estimands.

## Final pass matrix

| Gate | Required evidence | Pass criterion |
|---|---|---|
| Stage 7 acceptance | focused analysis tests + real schedule-shape smoke | all required measures and all lattice/state keys emitted; no missing/duplicate row |
| Hard integrity | `integrity_selfcheck.json` per run | every hard check true; informative reads cannot alter this value |
| Golden traces | `golden_traces.json` | every hand-derived event, order and competing-exit trace matches |
| Determinism | `determinism.json` | sequential, parallel and resumed canonical hashes identical |
| Row accounting | `row_accounting.json` | zero missing, extra or duplicate origins/arms/results |
| Full tests | pytest | zero failures; declared skips only |
| Static checks | Ruff + `git diff --check` | zero findings |
| Dry runs | six wrapper invocations | six correct TRAIN plans; no result directory created |
| SPDR pre-execution self-check | code-asserted checklist + smoke evidence | every declared check true before the first full run |
| Production cell | estimand + integrity artifacts | all hard checks pass before analysis |
| Analysis | required parquet set + `analysis.md` | all strata visible, crypto/cTrader separate, no verdict or pruning |

---

### Task 1: Re-establish the authoritative baseline

**Files:**
- Read only: all files changed by Tasks 1–7.
- Read:
  `docs/superpowers/plans/2026-07-30-spdr-021-023-adaptive-management.md`
- Read:
  `docs/experiments-docs/checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/adaptive-management-design.md`

**Interfaces:**
- Consumes: current dirty worktree.
- Produces: a written clause-to-code/test checklist in the session notes; no repository file.

- [x] **Step 1: Inspect without modifying**

Run:

```bash
git status --short
git diff --check
rg --files python/src/xen/adaptive_management python/experiments/SPDR-02{1,2,3} \
  python/tests | sort
```

Pass: no merge markers or whitespace errors; Tasks 1–7 files are present; no Stage 8 file is
silently assumed to exist.

- [x] **Step 2: Re-run the current baseline**

Run from `python/`:

```bash
PYTHONPATH=. .venv/bin/pytest tests/test_adaptive_management_*.py -q
PYTHONPATH=. .venv/bin/pytest tests -q
```

Pass: zero failures. Record the exact pass/skip counts; do not rely on the handoff count.

- [x] **Step 3: Map each remaining design clause**

The checklist must name exact future code and test locations for:

```text
fences and provenance
t-1 causality
SPDR-014 entry parity
golden traces
origin/event/order/fill/position/result reconciliation
native and management lattice completeness
no native×management cross
future-shift tripwire
zero-fixed-point derangement
magnitude-matched controls
deterministic sequential/parallel/resume replay
partial-cost disclosure
all device-native measures
all common-origin and paired-episode estimates
```

Pass: every line maps to an existing implementation/test or to a task below. No unmapped clause
may be silently deferred.

Completion evidence: every listed clause is mapped to Continuation Tasks 2–4 below; no clause was
marked complete merely because a similarly named file exists.

---

### Task 2: Close Stage 7 acceptance gaps before building integrity

**Files:**
- Modify if required: `python/src/xen/adaptive_management/analysis.py`
- Modify if required: `python/tests/test_adaptive_management_analysis.py`
- Modify if required:
  `python/experiments/SPDR-02{1,2,3}/analysis_code/analyse.py`

**Interfaces:**
- Consumes:
  `analyse_run(run_dir: Path, output_dir: Path) -> None`,
  `origin_estimates(...)`, `paired_estimates(...)`.
- Produces: the 13 artifacts declared by `ANALYSIS_ARTIFACTS`.

- [x] **Step 1: Add a complete emitted-run fixture**

The fixture must include:

```python
required = {
    "FIXED_NATIVE", "NATIVE", "NATIVE_COMBINATION",
    "FIXED_MANAGEMENT", "MANAGEMENT",
    "MANAGEMENT_COMPONENT_COMBINATION",
    "MANAGEMENT_DEVICE_COMBINATION",
}
assert required.issubset(set(schedule["arm_class"]))
assert {"FILLED", "NO_EVENT", "EXPIRED", "BLOCKED_ACTIVE"}.issubset(
    set(schedule["state"])
)
```

Include one closed target, stop, trail, hold and size episode with engine-reported entry/exit
prices and identity keys. Include both selected and excluded origins.

- [x] **Step 2: Add failing output-content tests**

Tests must assert:

```python
target_metrics = set(pl.read_parquet(output / "device_target.parquet")["metric_name"])
stop_metrics = set(pl.read_parquet(output / "device_stop.parquet")["metric_name"])
trail_metrics = set(pl.read_parquet(output / "device_trail.parquet")["metric_name"])
hold_metrics = set(pl.read_parquet(output / "device_hold.parquet")["metric_name"])
size_metrics = set(pl.read_parquet(output / "device_size.parquet")["metric_name"])

assert target_metrics >= {
    "reach_rate", "realised_capture_bps",
    "missed_excess_bps", "time_to_target",
}
assert stop_metrics >= {
    "adverse_excursion_bps", "stop_rate",
    "loss_severity_bps", "recovery_after_stop_bps",
}
assert trail_metrics >= {
    "peak_giveback_bps", "favourable_excursion_captured",
    "loss_tail_bps",
}
assert hold_metrics >= {
    "outcome_by_time_bps", "decay_bps",
    "holding_efficiency", "opportunity_duration",
}
assert size_metrics >= {
    "risk_dispersion", "drawdown_bps",
    "tail_loss_bps", "concentration",
}
assert "expectancy_improvement" not in size_metrics
```

Also assert every estimate row carries:

```text
experiment_id, universe, symbol, entry_variant, arm_id, arm_class,
component, parameter_or_device, orientation_or_setting, state,
comparator_id, metric_name, estimate, ci_low, ci_high,
event_count or paired_n, effective_n, mde
```

Every trade-bearing stratum must additionally expose the design's shared context:

```text
trade_count, gross_mean_bps, gross_median_bps, gross_trimmed_mean_bps,
partial_cost_mean_bps, win_share, mean_win_bps, mean_loss_bps,
win_loss_ratio, breakeven_win_share_net, edge_bps, mfe_bps, mae_bps,
exit_reason and exit_reason_share
```

Missing spread stays null and disclosed; no spread proxy may make the partial-cost field look
fully net.

Pass of this step: the new tests fail for the precise missing field or row, not for fixture setup.

- [x] **Step 3: Enforce exact full-reporting keys**

Build expected keys from `build_native_lattice()` and `build_management_lattice()`, converting the
three declared `DC_*` groups into one logical emitted row each. Compare expected keys against
emitted keys for every observed state.

Required assertions:

```python
assert actual_keys == expected_keys
assert not estimates.select(result_key).is_duplicated().any()
assert no_native_management_cross.height == 0
assert all_common_origin_counts_match
assert every_adaptive_management_row_has_fixed_comparator
```

The three allowed device combinations must be exactly:

```text
DC_TARGET_STOP
DC_TRAIL_HOLD
DC_TARGET_STOP_HOLD
```

Pass: deleting any single arm, state, comparator or no-event origin makes a focused test fail.

- [x] **Step 4: Implement only the missing analysis behavior**

Rules:

- Use engine-reported fills/positions and canonical adjudication for money-bearing results.
- OHLC may measure MFE/MAE and post-exit diagnostics, but may not decide which order won.
- Native effects use the full common-origin ledger with no-trade origin outcome equal to zero
  exposure, plus a separately labelled shared-trade diagnostic.
- Management effects use identical episode IDs.
- Calendar blocks are at least 24 H1 bars; dates are sampled before retaining all instruments in
  the sampled block.
- Fixed-device and plain-baseline deltas are both visible.
- “Best” helpers, if retained, carry `metric_name` and the complete source row key.

- [x] **Step 5: Verify Stage 7**

Run:

```bash
PYTHONPATH=. .venv/bin/pytest tests/test_adaptive_management_analysis.py -q
.venv/bin/ruff check src/xen/adaptive_management/analysis.py \
  tests/test_adaptive_management_analysis.py \
  experiments/SPDR-02{1,2,3}/analysis_code/analyse.py
```

Pass: zero failures/findings; every declared artifact is produced atomically; re-analysis refuses
overwrite; no verdict/winner/pass column exists.

---

### Task 3: Implement Stage 8 hard integrity and informative controls

**Files:**
- Create: `python/src/xen/adaptive_management/integrity.py`
- Create: `python/tests/test_adaptive_management_integrity.py`

**Interfaces:**
- Produces:
  `run_integrity_checks(run_dir: Path, output_dir: Path | None = None) -> dict[str, Any]`
- Produces:
  `derange_component_times(features: pl.DataFrame, seed: int) -> pl.DataFrame`
- Produces:
  `future_shift_tripwire(features: pl.DataFrame) -> dict[str, Any]`
- Produces:
  `magnitude_matched_controls(episodes: pl.DataFrame, features: pl.DataFrame) -> pl.DataFrame`
- Produces:
  `replay_hashes(run_dir: Path) -> dict[str, str]`

- [x] **Step 1: Write failing structural-control tests**

```python
def test_derangement_has_zero_fixed_points(feature_fixture):
    out = derange_component_times(feature_fixture, seed=240730)
    assert out.height == feature_fixture.height
    assert out["source_ts"].n_unique() == feature_fixture["ts"].n_unique()
    assert (out["source_ts"] == out["ts"]).sum() == 0


def test_future_shift_changes_mapping_without_changing_rows(feature_fixture):
    out = future_shift_tripwire(feature_fixture)
    assert out["row_count_before"] == out["row_count_after"]
    assert out["unchanged_fraction"] < 1.0


def test_magnitude_match_preserves_named_strata(control_fixture):
    out = magnitude_matched_controls(control_fixture.episodes, control_fixture.features)
    assert out["symbol"].null_count() == 0
    assert out["magnitude_bin"].null_count() == 0
    assert out["selected"].any()
    assert (~out["selected"]).any()
```

Pass of this step: all tests fail because Stage 8 functions do not exist.

- [x] **Step 2: Write failing hard-integrity tests**

Cover each failure independently:

```text
STUB or wrong manifest hash
bar mark after TRAIN end
feature source timestamp later than decision t-1
missing or duplicate common origin
wrong native arm count (65 SPDR-021; 130 SPDR-022/023)
wrong logical management row count (80 per fixed entry population)
missing fixed-device comparator
native×management cross
duplicate result key
order without terminal state
fill without order
closed position without two economic fills
state-ledger price/outcome disagreement with canonical position
SPDR-014 fixed E-TOUCH/E-CLOSE parity drift
golden-trace mismatch
replay hash mismatch
```

Every test must mutate one valid fixture and assert the exact named check becomes false.

- [x] **Step 3: Implement hard checks**

`run_integrity_checks` must return:

```python
{
    "blocking_pass": bool,
    "hard_checks": {
        "fence": bool,
        "provenance": bool,
        "causality": bool,
        "entry_parity": bool,
        "golden_traces": bool,
        "order_fill_position_reconciliation": bool,
        "row_accounting": bool,
        "native_lattice": bool,
        "management_lattice": bool,
        "no_native_management_cross": bool,
        "unique_result_keys": bool,
        "future_shift_changed_mapping": bool,
        "deterministic_replay": bool,
    },
    "informative": {...},
}
```

`blocking_pass` is `all(hard_checks.values())`. It must never include effect size, power, MDE,
cost sensitivity, derangement collapse or magnitude-match outcomes.

- [x] **Step 4: Write required artifacts atomically**

Write beside the run or to the explicit output:

```text
integrity_selfcheck.json
golden_traces.json
determinism.json
row_accounting.json
controls.json
```

Pass:

- every JSON includes experiment, universe, run path, timestamp-free deterministic inputs and
  exact source artifact hashes;
- no artifact reports a value verdict;
- a failed hard check leaves `blocking_pass=false`;
- partial output is never published as complete.

- [x] **Step 5: Verify Stage 8**

Run:

```bash
PYTHONPATH=. .venv/bin/pytest tests/test_adaptive_management_integrity.py -q
PYTHONPATH=. .venv/bin/pytest tests/test_adaptive_management_*.py -q
```

Pass: zero failures. The last command must include Tasks 1–8, not only Stage 8.

---

### Task 4: Add deterministic recovery, progress and resource preflight

**Files:**
- Modify: `python/src/xen/adaptive_management/runner.py`
- Modify: `python/tests/test_adaptive_management_runner.py`
- Modify: `python/experiments/SPDR-02{1,2,3}/screen_code/run_screen.py`
- Create: `python/src/xen/adaptive_management/preflight.py`
- Create: `python/tests/test_adaptive_management_preflight.py`

**Interfaces:**
- Extend:
  `run_experiment(..., resume: bool = False, progress: Callable | None = None)`
- Produce:
  `estimate_run(spec, universe) -> RunEstimate`
- Wrappers add only the operational `--resume` flag; the existing research-free CLI remains
  otherwise unchanged.

`RunEstimate` is exactly:

```python
@dataclass(frozen=True)
class RunEstimate:
    experiment_id: str
    universe: str
    symbols: int
    h1_origins: int
    native_rows: int
    management_rows: int
    work_units: int
    order_fill_upper_bound: int
    estimated_output_bytes: int
    available_disk_bytes: int
    benchmark_seconds_per_unit: float
    estimated_wall_clock_low_seconds: float
    estimated_wall_clock_high_seconds: float
```

- [x] **Step 1: Write failing resume-identity tests**

```python
def test_resume_refuses_changed_config(interrupted_run):
    with pytest.raises(ValueError, match="resume configuration mismatch"):
        run_experiment(changed_spec, "crypto", interrupted_run.output, resume=True)


def test_resume_reuses_only_hash_valid_complete_units(interrupted_run):
    resumed = run_experiment(spec, "crypto", interrupted_run.output, resume=True)
    assert resumed["reused_units"] == interrupted_run.complete_units
    assert resumed["rerun_units"] == interrupted_run.incomplete_units


def test_resumed_and_clean_outputs_are_byte_identical(clean_run, resumed_run):
    assert replay_hashes(clean_run) == replay_hashes(resumed_run)
```

Pass of this step: failure is due to absent recovery support.

- [x] **Step 2: Implement a recoverable in-progress directory**

Use exactly one sibling directory, computed as:

```python
in_progress = output.parent / f".{output.name}.inprogress"
```

- `config.json`, manifest hashes and software pins are written before the first work unit.
- Each symbol work unit publishes atomically with its own completion hash.
- `--resume` reuses only a complete unit whose input/config hash matches.
- Default mode refuses an existing completed output or in-progress directory.
- Resume never changes universe, symbols, dates, jobs semantics, arm lattice or analysis.
- Final publication is one atomic rename to the requested output.
- Do not delete a failed in-progress directory; report its path.

- [x] **Step 3: Add progress heartbeats**

Progress payload:

```python
{
    "experiment_id": str,
    "universe": str,
    "completed_units": int,
    "total_units": int,
    "elapsed_seconds": float,
    "rows_processed": int,
    "throughput_rows_per_second": float,
    "eta_seconds": float | None,
}
```

Pass: a synthetic long-running test receives a first event, one event per completed unit, and a
final event. Production orchestration prints an update at least every 10 minutes even when no unit
finishes.

- [x] **Step 4: Add a read-only preflight estimator**

`estimate_run` may read catalog metadata and bounded TRAIN counts; it may not execute orders or
emit research results. Report:

```text
symbols, H1 origins, native rows, logical management rows,
estimated order/fill upper bound, work units, estimated output bytes,
available disk bytes, benchmark seconds/unit, estimated wall-clock range
```

Pass:

- disk estimate includes temporary plus final publication overhead;
- required disk is no more than 70% of available free space;
- estimates for SPDR-022/023 include both E-TOUCH and E-CLOSE;
- no result directory is created.

- [x] **Step 5: Prove clean/parallel/resume identity**

Run a bounded synthetic fixture with `jobs=1`, `jobs=2`, and interrupted+resume.

Pass: canonical hashes for config, schedules, orders, fills, positions, state ledger, raw tables
and summary match exactly. Timing/progress logs are excluded from canonical hashes.

---

### Task 5: Final implementation verification and design audit

**Files:**
- Modify only if a verified defect is found in Tasks 1–8 files.

- [x] **Step 1: Run all tests**

From `python/`:

```bash
PYTHONPATH=. .venv/bin/pytest tests -q
```

Pass: zero failures; skips are listed and none skips an adaptive-management hard check.

- [x] **Step 2: Run static checks**

```bash
.venv/bin/ruff check src/xen/adaptive_management \
  tests/test_adaptive_management_*.py \
  experiments/SPDR-02{1,2,3}
git diff --check
```

Pass: zero findings.

- [x] **Step 3: Run six metadata-only dry runs**

Use a fresh path for each command:

```bash
PYTHONPATH=. .venv/bin/python experiments/SPDR-021/screen_code/run_screen.py \
  --universe crypto --output /private/tmp/spdr021-crypto-dry --dry-run
PYTHONPATH=. .venv/bin/python experiments/SPDR-021/screen_code/run_screen.py \
  --universe ctrader --output /private/tmp/spdr021-ctrader-dry --dry-run
PYTHONPATH=. .venv/bin/python experiments/SPDR-022/screen_code/run_screen.py \
  --universe crypto --output /private/tmp/spdr022-crypto-dry --dry-run
PYTHONPATH=. .venv/bin/python experiments/SPDR-022/screen_code/run_screen.py \
  --universe ctrader --output /private/tmp/spdr022-ctrader-dry --dry-run
PYTHONPATH=. .venv/bin/python experiments/SPDR-023/screen_code/run_screen.py \
  --universe crypto --output /private/tmp/spdr023-crypto-dry --dry-run
PYTHONPATH=. .venv/bin/python experiments/SPDR-023/screen_code/run_screen.py \
  --universe ctrader --output /private/tmp/spdr023-ctrader-dry --dry-run
```

Pass:

- each prints its own experiment only;
- crypto paths never mention cTrader and vice versa;
- every plan says `band=TRAIN`;
- no listed output path exists afterward;
- native adaptive counts are 64, 128 and 128;
- logical management count is consistent with the frozen lattice.

- [x] **Step 4: Run synthetic and bounded real-catalog smokes**

Synthetic smoke must exercise all five devices and a competing target/stop path. Real-catalog
smoke uses one declared symbol and a bounded interval wholly inside TRAIN through the fence
wrapper; it is a smoke artifact under `/private/tmp`, not a research result.

Pass:

- non-STUB attestation;
- canonical emission validation passes per instrument cell;
- hard integrity passes;
- every expected artifact opens;
- no TEST or holdout timestamp appears;
- smoke artifacts are not copied into experiment results.

- [x] **Step 5: Complete the design checklist**

Record observed counts for:

```text
8 executable component IDs
64 / 128 / 128 adaptive native arms
fixed plus direct and reverse for each native parameter
4 orientation pairs per component
all common origins including no-event/no-fill/blocked
5 external devices
individual rows before combinations
5 allowed component combinations
3 allowed device combinations
no other combinations
no native×management cross
size absent from exit combinations
E-TOUCH and E-CLOSE separate in SPDR-022/023
crypto and cTrader separate
no verdict/value labels
```

Pass: every item has code location, test location and observed smoke evidence.

---

### Task 6: SPDR code-asserted pre-execution acceptance

**Files:**
- Modify only if a finding proves a defect in Tasks 1–8 files.

**Interfaces:**
- Consumes: approved designs, implementation, tests, hard checks and smoke evidence.
- Produces: one complete code-asserted pass matrix per experiment in the session handoff.

- [ ] **Step 1: Run the SPDR self-check**

Follow `docs/references/spdr-lane.md`: this is a code-asserted self-check, not the formal
fresh-context QA stage used by EXP/XENA. Run the full design checklist separately for each
experiment. Shared code may be inspected once, but evidence and counts remain experiment-specific.

- [ ] **Step 2: Require clause-by-clause evidence**

Each self-check row includes:

```text
design clause
code location
test location
smoke evidence
finding severity
required correction
```

Pass: no clause is marked “assumed”, “not checked” or equivalent.

- [ ] **Step 3: Batch corrections**

Collect every finding before fixing. Route the complete batch to one developer pass, then re-run
Tasks 2–5 rather than cycling one issue at a time.

- [ ] **Step 4: Stop or advance**

Pass: every code-asserted row is true for all three experiments, with test or smoke evidence.

Stop immediately on an unresolved finding, any design deviation, or any hard-integrity failure.
Economic weakness, uncertainty or low power is not a pre-execution block.

---

### Task 7: Execution preflight and authority gate

**Files:**
- Write run estimates under:
  `python/experiments/SPDR-02{1,2,3}/results/preflight/`
- Do not create full run directories in this task.

- [ ] **Step 1: Run preflight for all six cells**

Record exact work units, disk need and wall-clock range. Confirm catalogs and both manifests are
readable and pinned.

- [ ] **Step 2: Check resources**

Pass:

- projected peak disk use leaves at least 30% free;
- estimated memory per worker multiplied by `jobs` fits physical memory with at least 25% margin;
- every output path is new;
- no stale in-progress directory has an unmatched config hash.

- [ ] **Step 3: Apply the authority rule**

If this session was not started from the applicable authorised prompt in
`.ignore/prompts/prompts.md`, stop and request TRAIN execution authority.

If authorised, report the six output paths, chosen `jobs`, disk estimate and wall-clock range,
then proceed without asking again.

---

### Task 8: Run all six TRAIN cells without economic gating

**Files:**
- Produce canonical runs under `data/nautilus_runs/`.
- Produce integrity artifacts inside each run.

**Interfaces:**
- Consumes: self-check-complete implementation and preflight.
- Produces: two valid runs per experiment: `crypto` and `ctrader`.

- [ ] **Step 1: Choose immutable run IDs**

Resolve one UTC stamp before starting:

```bash
run_stamp="$(date -u +%Y%m%dT%H%M%SZ)"
```

Then resolve and record:

```text
SPDR-021-crypto-train-${run_stamp}
SPDR-021-ctrader-train-${run_stamp}
SPDR-022-crypto-train-${run_stamp}
SPDR-022-ctrader-train-${run_stamp}
SPDR-023-crypto-train-${run_stamp}
SPDR-023-ctrader-train-${run_stamp}
```

Record the resolved IDs before starting. Never reuse a completed output path.

- [ ] **Step 2: Execute experiments sequentially**

Run SPDR-021, then SPDR-022, then SPDR-023 because they share code and disk. Within an experiment,
run cTrader and crypto as independent cells. A weak result never cancels another cell.

Use the wrapper with the preflight-approved `jobs`. Use `--resume` only for the exact matching
in-progress directory.

- [ ] **Step 3: Monitor**

Report at least every 10 minutes:

```text
completed/total work units
elapsed time
throughput
ETA
disk used/free
current experiment and universe
```

If elapsed time exceeds twice the upper preflight estimate, pause new work units, preserve the
in-progress directory, diagnose, and either safely resume or report the blocker. Never narrow the
grid or dates to finish faster.

- [ ] **Step 4: Validate each cell before analysis**

Run:

```text
xen.estimand_validation on the run's cells directory
run_integrity_checks on the raw run root
```

Pass:

- every instrument cell has `blocking_pass=true`;
- root `integrity_selfcheck.json` has `blocking_pass=true`;
- row accounting has zero missing/extra/duplicate rows;
- fence and manifest hashes match the selected universe;
- deterministic hashes are recorded;
- spread disclosure is present.

Do not analyse a cell that fails. Fix and re-run the invalid cell; do not reinterpret a hard
failure as an economic result.

---

### Task 9: Run independent analysis and write neutral records

**Files:**
- Produce per run: the 13 Stage 7 analysis artifacts.
- Create: `python/experiments/SPDR-021/screen.md`
- Create: `python/experiments/SPDR-022/screen.md`
- Create: `python/experiments/SPDR-023/screen.md`
- Create in fresh analyst context:
  `python/experiments/SPDR-021/analysis.md`
- Create in fresh analyst context:
  `python/experiments/SPDR-022/analysis.md`
- Create in fresh analyst context:
  `python/experiments/SPDR-023/analysis.md`

- [ ] **Step 1: Run the experiment-specific analyzer**

Run each wrapper separately for its crypto and cTrader run. Refuse an experiment-ID mismatch.

Pass: all 13 artifacts exist per cell, contain unique full keys, and reproduce identically on a
second temporary analysis run.

- [ ] **Step 2: Create neutral `screen.md` files**

Each file records:

```text
run IDs and paths
fence and integrity status
origin/event/fill/episode counts
complete arm/state row counts
crypto and cTrader sections
spread-cost limitation
links to raw and analysis artifacts
```

No economic conclusion or selective table belongs in `screen.md`.

- [ ] **Step 3: Invoke a fresh-context data analyst**

The analyst reads raw emissions and canonical artifacts, not developer summaries. The approved
SPDR design overrides the data-analyst skill’s normal recommended-verdict section: these three
analyses contain observations for and against patterns, anomalies and unanswered questions, but
no experiment verdict.

- [ ] **Step 4: Enforce analysis content**

Each `analysis.md` must:

- keep crypto and cTrader separate;
- keep E-TOUCH and E-CLOSE separate for SPDR-022/023;
- show fixed, direct, reverse and all four native orientation pairs;
- show every component before combinations and every device before combinations;
- retain selected and excluded populations and all observed states;
- pair estimate, interval, count, effective count and MDE;
- show fixed-device and plain-baseline comparisons;
- state where a measure is unavailable rather than substituting a common score;
- include both supporting and contrary observations;
- repeat the partial-cost/spread limitation;
- avoid universal-effect, tradability, deployability, winner and verdict claims.

Pass: a row-key audit proves that every full-table row is represented or linked; no “top-N only”
presentation replaces full reporting.

---

### Task 10: Final handoff and operator interpretation gate

**Files:**
- Update only neutral run-status rows in:
  `python/experiments/INDEX.md`
- Update only neutral live-status rows in:
  `docs/experiments-docs/INDEX.md`
- Do not change family status or write a checkpoint verdict.

- [ ] **Step 1: Re-run final verification**

```bash
cd python
PYTHONPATH=. .venv/bin/pytest tests -q
.venv/bin/ruff check src/xen/adaptive_management \
  tests/test_adaptive_management_*.py \
  experiments/SPDR-02{1,2,3}
cd ..
git diff --check
```

Pass: zero failures/findings.

- [ ] **Step 2: Verify programme boundaries**

Run searches proving:

```text
zero TEST output
zero holdout timestamp
zero XENA action
zero family-status change
zero verdict/winner/deployability label in SPDR-021/022/023 analyses
zero staged or committed path unless separately authorised
```

- [ ] **Step 3: Give the operator one concise handoff**

Report:

```text
six run IDs, durations and paths
test/lint/diff counts
hard-integrity result per cell
origin/arm/state row-accounting totals
screen.md and analysis.md links
limitations and unresolved questions
confirmation that all three ran regardless of one another
```

Then stop. The operator, not the executing agent, makes the combined checkpoint interpretation
after reading all three analyses.

## Stop conditions

Stop and preserve evidence when any of these occurs:

- approved design conflicts with implementable engine behavior;
- TEST, holdout or forbidden cTrader date contact;
- non-pinned or wrong-universe manifest;
- hard-integrity failure after two batched correction cycles;
- missing catalog/instrument data;
- resource preflight fails the disk or memory margin;
- deterministic clean/parallel/resume hashes differ;
- the SPDR pre-execution self-check has any unresolved row;
- action requires staging, committing, publishing, XENA, deployment or family-status authority.

Do not stop merely because an effect is small, inconsistent, uncertain, concentrated, unpowered
or contrary to expectation. Those are observations to report.
