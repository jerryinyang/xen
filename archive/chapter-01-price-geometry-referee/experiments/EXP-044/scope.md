# Experiment: EXP-044 — Phase 011 Track A Per-Cell Event-Level Inference Calibration (EXP-027-Analog)

## Hypothesis

The frozen EXP-027 event-level inference machinery — per-event direction-signed
matched-control excess (bps) as the binding statistic, regime-cluster bootstrap
CI, stratified paired sign-permutation p-value, Evidence-FOR decision rule —
**applied per instrument×domain cell** (no cross-instrument pooling, per design
§5.6 and the Phase 011 out-of-scope list), exhibits controlled false-positive
error (empirical per-cell FPR ≤ α₀ = 0.05 under known-null sparse event draws)
and recovery (a finite per-cell event-level MDE at TPR ≥ 0.80) at each READY
cell's **realized TRAIN event count** (EXP-043 power table: 1h 151–273,
2h 86–143, 4h 32–86 events), across the 50 READY cells of the Phase 011 grid —
including the first-ever 2h domain and the 13 new-universe instruments.

Cells where the calibration holds are **COVERED**: G1 leg (ii) (design §8.2) is
satisfied for them and they may proceed to Track B. Cells where error is not
controlled or no finite MDE exists are **NOT_COVERED**: excluded from Track B
with record, consuming nothing — exactly as JP225-2h was excluded under leg (i).

## Question

For each of the 50 READY cells certified by EXP-043: does the unchanged
EXP-027 event-level inference, evaluated **standalone per cell** (single
instrument, single domain — no equal-weight instrument aggregation, no
cross-domain Holm), control FPR and retain power at that cell's realized
sparse event population, so that the Phase 011 binding per-cell machinery
(Track D / G3 verdicts, and any per-cell TRAIN inference Track B reports)
rests on a measured operating-characteristic map rather than on the EXP-027
pooled-domain map, which covered only {BTCUSD, EURUSD, USTEC, XAUUSD} ×
{5m, 1h, 4h} with a 3-domain equal-weight-instrument estimator?

This is a **methodology / calibration experiment** (`CF-AVWAP-001` Track A,
EXP-027-analog; registered 2026-06-11 in
`docs/signal-registry/multiplicity-registry.md`). It consumes **0
candidate-screening slots and 0 TEST reads**. It feeds **G1 adjudication 2
of 2** (`checkpoints/2026-06-11-011-per-instrument-foundation/G1-gate-review.md`).

## Background and binding constraints

EXP-027 (METHOD_VALID, Phase 006) calibrated this inference for sparse
(~3/6/12%-active) event processes, but at the **pooled-domain** unit: the
domain statistic averaged four instruments and Holm ran across three domains.
Phase 011 inverts this — per-cell verdicts, 17 instruments, a new 2h domain,
and per-cell event counts (32–273) far below the pooled-cell totals EXP-027
measured. Per-cell error control and MDE at these counts are unmeasured. The
EXP-027 machinery itself is **frozen and re-used unchanged** (design §5.3); the
only new object is the per-cell application.

Hard constraints (each inherits a documented prior failure mode):

1. **Per-event unit of analysis end-to-end.** No per-bar floor or per-bar suite
   is invoked anywhere (EXP-023/024 framing lesson).
2. **Synthetic-substrate-only calibration; anti-overfitting fence.** Null and
   planted-edge draws use placebo events placed within the **real EXP-043
   regime/event scaffolding on TRAIN bars**; the real bounce-event **outcomes**
   (returns, completions, target hits) are never read. The calibration is
   frozen before Track B reads any real exit-training result. A failed
   calibration is a valid result, not license to re-pick the method.
3. **No inference-object changes.** Matched-control rule (same `regime_id`,
   ≥3 controls, up to 5 by nearest anchor age then timestamp, exclusion
   window), bootstrap structure, permutation scheme, and the Evidence-FOR rule
   are EXP-027's, byte-for-byte in semantics. Only the aggregation level
   (single cell) differs, and that difference is predeclared here.
4. **Zero-baseline discipline.** Null per-event excess is exactly 0 bps;
   report bps differences and rate CIs; never percentage improvement over a
   zero/near-zero control mean.
5. **TRAIN stratum only.** F01-compliant loading: first
   `floor(0.7 × floor(0.7 × total))` file-order 1-minute rows per instrument
   (identical to EXP-043); TEST rows and the global holdout are never touched.

## Scope Boundaries

- **Instruments (17)**: BTCUSD, EURUSD, USTEC, XAUUSD, GBPUSD, USDJPY, USDCHF,
  USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, US500, US2000, DE30, JP225.
- **Domains**: 1h, 2h, 4h clock-aligned bars from 1-minute TRAIN rows
  (`min_coverage = 0.90`, EXP-043 construction spec). 5m retired (design).
- **Cell grid**: the **50 READY cells** from
  `python/experiments/EXP-043/results/readiness_map.csv`. JP225-2h is excluded
  (NOT_READY, G1 leg (i)) and is not calibrated.
- **Data views**: real TRAIN domain bars; frozen baseline AVWAP regime/event
  scaffolding regenerated deterministically via `generate_avwap_events`
  defaults (bit-for-bit the EXP-043 substrate) — used **only** for regime
  intervals, anchor ages, and realized event locations/rates as placement
  scaffolding. No chart-type views. No real event outcomes.
- **Synthetic substrates**:
  - **Null generators (2, structurally different — EXP-001/027 precedent)**:
    (1) placebo events at the cell's realized event rate placed within real
    regime intervals on real TRAIN returns, no planted edge; (2) a second
    structurally different null (e.g. block-permuted real returns under the
    same placebo placement). Exact generators fixed in Stage 2.
  - **Planted-edge mechanism**: known direction-signed per-event drift added
    to placebo-event outcomes over a predeclared bps grid spanning the
    EXP-027 MDE scale through the per-cell-plausible range (grid fixed in
    Stage 2, before any measurement); outcome window matching the Phase 011
    exit-hold semantics (representative fixed-horizon window, fixed in
    Stage 2).
- **Inference under test (frozen)**: per-cell EXP-027 gate — per-event
  matched-control excess; 95% regime-cluster bootstrap CI; stratified paired
  sign-permutation p; per-draw Evidence-FOR iff effect > 0 ∧ CI_low > 0 ∧
  p ≤ α₀. **No Holm inside this experiment** (single-cell unit; the Track D
  Holm-5 family correction is a G3 object, not a calibration object — but the
  per-cell α₀ = 0.05 operating point is the one G3 consumes pre-Holm).
- **Error grids**: primary α₀ = 0.05 (secondary {0.10, 0.01} reporting
  permitted within budget); draw and bootstrap counts fixed in Stage 2 to meet
  the precision thresholds below; fixed seeds; deterministic replay check on
  at least one re-run cell.
- **Event-count fidelity**: each cell is calibrated **at its own realized
  TRAIN event count** (EXP-043 `power_statement.csv`). If Stage 2 elects an
  event-count-tier design for tractability (calibrating shared count tiers and
  mapping cells to tiers), the mapping must be conservative (a cell maps to a
  tier ≤ its realized count) and predeclared.
- **Time range**: TRAIN stratum of the first-70% analysis slice (F01 row
  convention), per instrument file.
- **Global holdout (mandatory exclusion)**: the final 30% of each
  chronologically ordered source file is never loaded, inspected, emitted,
  plotted, counted, or used in any capacity. The TEST stratum (last 30% of the
  analysis slice) is likewise untouched.
- **Look-ahead bias prevention**: regime intervals/anchor ages from the
  look-ahead-safe frozen generator; placebo placement and control selection
  use only information available at the bar (timestamp, regime direction,
  anchor age); future closes enter only as measured outcomes; planted drift is
  added to outcomes, never used in placement or matching.
- **Real-price outcome discipline**: all outcomes are direction-signed log
  returns in bps on real domain `Close` prices. No synthetic chart prices, no
  costs/stops/fills/sizing (method calibration, not strategy P&L).
- **Exclusions**:
  - real AVWAP event outcomes (fence above); any Track B exit-training
    measurement; any TEST or holdout row;
  - cross-instrument pooling or cross-cell aggregation in any binding
    statistic (Phase 011 out-of-scope list);
  - the per-bar frozen suite as comparator or floor;
  - R1.2 matched-structure TEST-margin calibration (a G3-time, per-realized-
    TEST-structure object — out of scope here);
  - EXP-029-analog C#/Python parity (separate registered Track A item);
  - any sweep/tuning/metric reselection after results are seen; grid
    extension after curves are seen;
  - percentage improvement against a zero baseline;
  - JP225-2h.

## Success / Failure Criteria

**Precision thresholds** (EXP-003/005/027 precedent): a calibration cell is
usable only if the FPR Wilson 95% half-width ≤ 0.03 and TPR Wilson 95%
half-width ≤ 0.05; cells failing precision are reported **CALIBRATION_
UNDERPOWERED** and excluded from COVERED/NOT_COVERED claims pending an
operator precision-only re-run decision (draw-count increase only; no object
change).

Per-cell verdicts:

- **COVERED** (all hold): per-cell FPR ≤ α₀ under **both** null generators at
  the cell's event count (Wilson precision met); a **finite per-cell
  event-level MDE** exists (TPR ≥ 0.80 at FPR ≤ α₀); the MDE value is recorded
  for Track B/D power interpretation.
- **NOT_COVERED** (either holds): the FPR point estimate exceeds α₀ in an
  adequately powered cell under either null (graded `material` when the Wilson
  95% lower bound also exceeds α₀); or no finite MDE exists on the predeclared
  grid. Consequence: the cell fails G1 leg (ii), is excluded from Track B with
  record, consumes nothing.
- **CALIBRATION_UNDERPOWERED**: precision thresholds unmet at the budgeted
  draw counts.

Experiment-level:

- **Evidence FOR — CALIBRATION_DELIVERED**: the 50-cell coverage map is
  produced with every cell classified, the per-cell MDE table recorded, and
  the determinism replay passing. (Deliverable criterion — like EXP-043, the
  experiment succeeds by producing the honest map, however many cells are
  COVERED.)
- **Evidence AGAINST — METHOD_NOT_TRANSFERABLE** (substrate-level): the
  two null generators disagree on FPR control beyond tolerance in ≥3
  instruments, or a systematic FPR excess appears across an entire domain in
  adequately powered cells — meaning the per-cell application of the EXP-027
  machinery is itself invalid, not merely thin cells failing. Consequence:
  G1 cannot close; operator review of the Phase 011 per-cell inference design
  before any Track B work.
- **Inconclusive**: coverage map produced but a material fraction of cells
  (>1/3) is CALIBRATION_UNDERPOWERED, leaving G1 leg (ii) undecidable at
  budgeted precision. Consequence: operator decides precision-only re-run vs
  accepting a reduced Track B grid.

Expected (honest prior, not a target): thin 4h cells (32–55 events) may carry
large finite MDEs or fail recovery — that is exactly the information G1 and
Track D power planning need; a NOT_COVERED 4h tail is a valid outcome, not a
calibration defect.

## Complexity Budget

- Max statistical tests: **4** (regime-cluster bootstrap CI; stratified paired
  sign-permutation; Wilson FPR/TPR intervals; grid-defined per-cell MDE
  determination). No Holm in-experiment.
- Max visualisations: **5** (per-cell FPR map 17×3; per-cell MDE map/heatmap;
  MDE vs realized event count by domain; calibration-precision /
  underpowered-cell diagnostic; coverage-verdict summary).
- Max new code modules: **1 experiment-local helper** under
  `python/experiments/EXP-044/code/` (per-cell sparse null/planted-edge
  substrate + per-cell inference wrapper). Reuse of EXP-027/EXP-043 code by
  copy or import is allowed and preferred; **no new or modified shared
  `python/src/xen/` module** without explicit governance approval.

## Metric Denominators and Zero-Baseline Behavior

- Per-cell FPR denominator: number of completed null draws for that
  cell×generator×α (predeclared count, fixed in Stage 2).
- Per-cell TPR denominator: number of completed planted-edge draws for that
  cell×edge×α.
- Per-event excess denominator within a draw: number of **reportable matched
  events** (valid outcome window and ≥3 matched controls) — never a bar
  count. Draws whose reportable-event count falls below the EXP-027
  reportability rule are recorded and counted against a predeclared
  draw-completion floor (Stage 2), not silently dropped.
- Null per-event excess = exactly 0 bps; all effects reported as bps
  differences with CIs. No ratios against zero baselines anywhere.

## Data Requirements

Read-only upstream artifacts:

- `python/experiments/EXP-043/results/readiness_map.csv` (dependency gate:
  the 50 READY cells; hard-fail if missing or if EXP-043
  `run_metadata.json` does not record READINESS_DELIVERED with
  `substrate_alert: false`);
- `python/experiments/EXP-043/results/power_statement.csv` (realized per-cell
  TRAIN event counts — the calibration's event-count targets);
- EXP-027 code/artifacts as the frozen inference reference
  (`python/experiments/EXP-027/`);
- 1-minute source files under `data/timebars/`, F01 TRAIN-sliced before any
  domain-bar construction.

### Expected Output Files

```text
python/experiments/EXP-044/results/
- coverage_map.csv        # per-cell verdict: COVERED / NOT_COVERED / CALIBRATION_UNDERPOWERED + reasons
- fpr_per_cell.csv        # FPR by cell × null generator × alpha, with Wilson bounds
- tpr_mde_per_cell.csv    # TPR by cell × planted edge; per-cell event-level MDE
- draw_verdicts.parquet   # per-draw Evidence rows (bounded columns)
- run_metadata.json       # status, determinism, dependency gates, seeds, draw counts
python/experiments/EXP-044/plots/   # ≤5 per the budget
```

## Suggested Direction

Treat EXP-044 as EXP-027 re-run at the per-cell unit on the Phase 011 grid:
same nulls-on-real-scaffold construction, same frozen decision rule, with the
aggregation step removed and the event count set to each cell's realized
TRAIN population. The binding question is where per-cell inference stops
working as counts fall from ~270 (1h majors) to ~32 (thin 4h cells) — the
resulting MDE-vs-count curve is simultaneously the G1 leg (ii) verdict, the
Track B power context, and the Track D affordability map. Computational
tractability (50 cells × 2 nulls × draws × bootstraps) is a Stage 2/3 design
problem: prefer conservative event-count tiers or vectorized draw batching
over cutting draw counts below precision thresholds.
