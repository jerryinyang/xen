# EXP-043 — Pre-Execution Governance Review

**Date:** 2026-06-11
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`
**Reviewed against:** governance constraints, developer code conventions, active
checkpoint `2026-06-11-011-per-instrument-foundation/design.md` (Track A, §5.3/§8.2)

## Checks

### Scope (scope.md)
- Single exploratory readiness question, falsifiable per-cell criteria
  (READY / NOT_READY / CONSTRUCTED_EMPTY), measurable experiment verdict
  (READINESS_DELIVERED) and a predeclared substrate-level halt condition. PASS.
- Boundaries explicit: 17 instruments, {1h, 2h, 4h}, TRAIN stratum only, all
  parameters frozen (defaults-only baseline; band multiplier never varied —
  consistent with the Track A0 removal amendment). PASS.
- Holdout exclusion explicit; TEST never read, projections via the predeclared
  `TRAIN_count × (30/70)` rule with no TEST contact including row counts. PASS.
- Real-price discipline: N/A and correctly declared (no return/P&L/edge metric
  of any kind). PASS.
- Complexity budget realistic (0 tests / 3 plots / ≤1 module). PASS.
- Phase alignment: implements design §5.3 EXP-020-analog feeding gate G1;
  0 slots, 0 TEST reads, no ledger entry — matches §7.1. PASS.

### Analysis Plan (analysis-plan.md)
- Every step is a deterministic predicate or count; method/justification/
  simpler-alternative/assumptions documented per step. No statistical tests —
  matches the descriptive budget. PASS.
- Interpretation criteria predeclared verbatim from the scope (lenient G1:
  event count does not affect READY; sparse cells are power disclosures). PASS.
- Plots purposeful (power map, rate stability across domains, first-ever 2h
  retention disclosure), drawn from the aggregated 51-row summary only. PASS.
- Zero-baseline behavior predeclared: 0-event cells report rate 0.0 with the
  denominator disclosed; no division-by-zero path; no percentage-vs-zero
  metric anywhere. PASS.
- Denominators defined before implementation (cell TRAIN domain-bar count;
  candidate grid windows for the dropped fraction; 1h bar count for the 2h
  ratio). PASS. Chart-type duplicate-source denominators: N/A (no chart-type
  views in scope). PASS.

### Code (code/run_experiment.py)
- **Plan compliance:** implements exactly Steps 1–6 and the three plots;
  nothing extra. Constants match D0 predeclarations (P7 `min_coverage=0.90`;
  P8 DE30 carried verbatim in outputs). PASS.
- **Holdout/TEST exclusion:** F01-compliant — total row count from Parquet
  metadata; lazy column-projected scan; `head(train_rows)` collects only TRAIN
  file-order rows; **no full-file sort**; strict chronological order
  re-asserted on the collected slice (sorted + unique timestamps), failing
  loudly otherwise. TEST/holdout rows never enter the scan engine; projection
  uses the 30/70 factor only. Derivative `analysis70` exports excluded from
  the source glob. PASS.
- **Look-ahead / causality:** the sequential generator is called as-is with
  defaults only (frozen baseline; `test_avwap_band_param.py` anchors
  bit-for-bit reproduction); no vectorized re-implementation of sequential
  logic; all span checks use timestamps; index columns are used only for
  internal segment-consistency predicates, never cross-view alignment. PASS.
- **Construction-fence equivalence note:** the scope's "slice domain bars to
  `train_end_ts`" is implemented as an asserted invariant
  (`construction_train_fence`) rather than a filter. Because aggregation input
  is TRAIN-only, the slice set is provably empty; the assertion is strictly
  stronger (a violation surfaces as NOT_READY instead of being silently
  dropped). Verified equivalent — not a deviation.
- **Predicate correctness:** invariants verified against the generator's
  actual semantics (regimes contiguous `confirm_idx..end_idx`, alternating
  direction, anchor ≤ confirm; events strictly bar-ordered, arm bar strictly
  before trigger bar) and the aggregator's `(epoch−1)//period` bucket rule —
  no predicate can false-fire on correct output. PASS.
- **Import side effects:** none (path setup only); directories created in
  `main()`. PASS.
- **Memory/performance:** one instrument's 1-minute frame held at a time and
  dropped after its three cells; all checks are Polars expressions; plots
  consume the 51-row summary (no reloads, no pandas conversion of large
  frames). PASS.
- **Progress/logging:** single `tqdm(total=51)`; helpers quiet and typed;
  concise logging summaries; per-cell NOT_READY lines bounded at 51. PASS.
- **NaN/edge handling:** explicit — empty event tables short-circuit to zero
  violations; empty bars → CONSTRUCTED_EMPTY; NaN rate only with disclosed
  zero denominator; null/NaN in event columns is itself a counted invariant
  violation. PASS.
- **Determinism check:** full second regeneration with frame-identical
  comparison (`DataFrame.equals` on bars, events, regimes + scalar fields) —
  matches the plan's diagnosability rationale. PASS.
- Syntax check performed (`py_compile` PASS); experiment not executed
  (manual execution gate respected).

### Info notes (non-blocking)
1. `construction_checks` is ~45 lines — over the ~30-line guideline, but it is
   one cohesive Polars `select` of named predicates; splitting would hurt
   review clarity.
2. `generate_cell` return type annotates `object` for `AvwapResult`; importing
   the dataclass for the annotation would be marginally cleaner.
3. The fixed seed (43) in the rate plot is presentation jitter only — no
   analysis randomness anywhere.

## Revision 1 — 2026-06-11 operator adversarial review (pre-execution, no data contact)

Four operator issues + three structured findings validated; all fixes applied
to `scope.md`, `analysis-plan.md`, and `code/run_experiment.py` before any
TRAIN read:

1. **2h dropped-fraction thresholds frozen** (operator issue 1): < 10% clean
   PASS; 10–25% flagged disclosure (READY-eligible, recorded); > 25%
   construction FAIL → NOT_READY (named check `dropped_fraction`, 2h only —
   1h/4h fractions remain disclosures under the established construction).
   Removes the post-hoc judgment call.
2. **Systematic-failure threshold frozen** (operator issue 2): substrate-level
   halt iff non-determinism on any cell, or the same invariant violated on
   **≥ 3 instruments** (`SYSTEMATIC_INSTRUMENTS = 3`; was an unquantified
   "recurring", implemented as ≥ 2).
3. **TEST projection labeled heuristic** (operator issue 3): column renamed
   `projected_test_events_heuristic`; scope/plan/metadata state it is a
   uniformity heuristic, not an estimate — realized TEST counts depend on the
   TEST stratum's regime distribution.
4. **DE30 power note** (operator issue 4): `power_note` column added to the
   power statement — DE30 projected counts optimistic by ~15–20% vs full-span
   instruments (~5-months-shorter history); Track B power must use its
   realized span.
5. **F01 (Major) — ratio gate ambiguity:** resolved by the explicit
   disclosure-only option. Scope/plan now state the 2h/1h bar-count ratio
   cannot affect READY, with rationale: session-gap structure makes the ratio
   instrument-dependent (a 60-minute session break drops a 2h window at
   `min_coverage=0.90` while keeping one of its two 1h windows), and the
   exact per-window coverage/alignment predicates are the binding checks.
6. **F02 (Major) — clock-alignment definition:** resolved by the
   plan-revision option. The plan's "CloseTime modulo the domain period is
   constant" was inaccurate for the aggregator's actual semantics (domain-bar
   `CloseTime` = last observed source close; coverage-tolerant windows may
   close before the grid boundary — a modulo predicate would false-fail
   legitimate retained windows). Plan rewritten to the bucket-membership
   definition; the timestamp convention is disclosed in the plan, the code
   docstring, and `run_metadata.json`.
7. **F03 (Minor) — DE30 disclosure coverage:** `de30_truncated` added to
   `readiness_map.csv`; DE30 annotated "(truncated)" in the event-rate plot
   (the heatmap and dropped-fraction plot already carried it); P8 disclosure
   now in every output artifact.

Re-verified: thresholds and labels only — no change to sample membership,
temporal ordering, denominators, the frozen entry definition, or TRAIN-only
contact. Syntax check (`py_compile`) PASS; experiment still not executed.

## Verdict

```text
VERDICT: APPROVE
```
