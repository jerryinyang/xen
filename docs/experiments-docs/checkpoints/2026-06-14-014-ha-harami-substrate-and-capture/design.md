# Phase 014 — HA Harami Substrate & Capture Geometry (New Candidate Family)

**Checkpoint type:** Research phase design (FINALIZED — D0 ratified at G0).
**Date finalized:** 2026-06-14.
**Status:** ACTIVE — **G0 PASS 2026-06-14** (D0 ratified, `D0-predeclarations.md`); no
Phase 014 result exists; no row read under any harami event definition. Next pipeline
step: VAL-004 (15m/30m temporal integrity), then EXP-048.
**Candidate family:** `CF-HA-HARAMI-001` — Heiken Ashi Harami at trend exhaustion
(`docs/signal-registry/candidate-families/harami.md`).

> D0 ratification is complete (G0 PASS 2026-06-14); items marked **[D0]** are now
> frozen governance parameters (see `D0-predeclarations.md`). Items marked **[VAL]**
> are infrastructure gates that must PASS before analytical use.

## 1. Provenance

Phase 013 closed `CF-AVWAP-001` for new in-family phases (ANCHOR_MOVE_FLAT). The
pre-committed routing was a **new candidate family**. The Phase 013 retrospective's
binding correction is the design brief: the AVWAP family's available lifetime move
was ≈5–9× the cost floor in every cell, but no deterministic exit converted it to
net-of-cost capture — **the unsolved problem is capture geometry, not move
availability.** The mechanism for this family must make the peak → realizable-exit
conversion structurally cheaper, not the raw move bigger.

## 2. Objective

Build the HA-harami family from first principles: validate each primitive
separately, then assemble only survivors. No frozen end-to-end strategy is screened
in this phase. All work is **gross** (no costs); the frozen cost model enters only
at a future tradability screen of a registered candidate branch.

The family's response to the capture-geometry brief is a **structurally bounded
favourable target** (a fraction of the confirmed prior move). Whether that bound
actually solves the favourable-before-adverse problem is a hypothesis to measure
early (HYP-002 / EXP-049), not an assumption.

## 3. Multiplicity Gate

`CF-HA-HARAMI-001`, its hypotheses, and its full variant surface must appear in
`docs/signal-registry/multiplicity-registry.md` (Phase 014 batch) before any
result-producing code. Characterization experiments consume **no** candidate slot
and read **no** TEST stratum; they are descriptive/exploratory. A candidate branch
for screening is registered only at the close of 014-B.

## 4. Programme-Level Design Principles (carried from CF-AVWAP-001 lessons)

- **No blanket assumptions across instruments or domains.** All evaluation is
  per-cell (instrument × domain) from day one. Per the operator decision, readiness
  **and** characterization run on all 102 cells. Any composition/selection rule
  ("qualifies if ≥N cells over ≥M instruments") is a **mechanical, per-cell**
  criterion predeclared **[D0]** before results are read.
- **Separation of components.** ZigZag substrate (real bars) and HA harami detector
  (HA candles) are independent primitives, each validated before any combined event
  definition.
- **Capture geometry is first-class.** The 3-barrier framework is validated in
  this phase with the same breadth as the signal, including a gross capture-rate
  read in 014-A (EXP-049) — not deferred to 014-B.
- **Screen before machinery.** Each viability question gets the cheapest decisive
  gross read first, with pre-committed routing, before any net/inference machinery
  (validated three times: 011→012→013).
- **Predeclared defaults / OAT.** Every characterization experiment fixes
  all-but-one parameter at predeclared **[D0]** defaults and varies one at a time.
  No parameter is selected or frozen against analysis-set outcomes.
- **Mechanical thresholds.** Every qualitative claim ("materially different", "near
  exhaustion", "meaningful gap") has a predeclared quantitative bar and a declared
  baseline before results are read.
- **Cost model deferred.** Gross throughout; costs only at a future tradability
  screen.

## 5. [VAL] New-Domain Construction Gate (critical path, first)

15m and 30m are new domains with no prior construction or validation. Before any
102-cell readiness claim:

- Construct 15m and 30m clock-aligned OHLC via `xen.bar_aggregator`
  (`min_coverage=0.90`).
- Run a VAL-001-style temporal-integrity validation (a VAL-class experiment, e.g.
  **VAL-004**) across all 17 instruments for 15m and 30m: monotonic `CloseTime`,
  OHLC integrity, coverage/dropped-fraction disclosure, negative controls, holdout
  seal at first touch.
- **Gate:** 15m/30m cells enter EXP-048 only on VAL PASS. Cells failing a
  dropped-fraction gate are excluded with record (cf. JP225-2h in EXP-043).

## 6. Phase 014-A — Substrate & Component Primitives

Exploratory/descriptive. No candidate slot, no TEST read. Output: a per-cell
characterization map informing 014-B and any branch registration.

| EXP | HYP | Question | Notes |
| --- | --- | --- | --- |
| EXP-048 | HYP-001 | ZigZag substrate **and** HA harami detector readiness across all 102 cells: determinism, look-ahead safety, invariant checks, per-cell event/move rates, `/BARCFG` coverage (measured, not assumed). | EXP-020-analog. Gated on §5 VAL PASS for 15m/30m. |
| EXP-049 | HYP-002 | 3-barrier capture readiness **+ gross capture-rate**: barriers computable and causal (thresholds only from confirmed prior moves); per-cell favourable-before-adverse hit rate under default barriers. | First-class capture read. Reuse EXP-047 `move_size.py` MFE/MAE machinery. Gross, exit-agnostic. |
| EXP-050 | HYP-003 | Harami-in-context: where in a ZigZag move do harami signals occur vs predeclared baselines (random timestamps, alt trend defs)? | Mechanical "near-exhaustion" threshold **[D0]**. |
| EXP-051 | HYP-004 | Strong-move filters: do `/STRONG-STAT` and `/STRONG-HA` identify materially different move populations, cross-cell consistent? | Mechanical "materially different" threshold **[D0]**. |
| EXP-052 | HYP-005 | Signal interpretation: direct vs signal+confirmation descriptive properties (frequency, timing, outcome distribution). | Descriptive only; no selection. |

014-A selects/freezes no parameter or branch.

## 7. Phase 014-B — Reversal Target Framework & 3-Barrier System

Builds on validated 014-A primitives. Extends EXP-049 capture readiness to all
barrier-model variants. Still gross, still exploratory, no screening.

| Theme | Variants compared | Registry branch |
| --- | --- | --- |
| Capture-geometry deepening | all barrier model variants; coverage + causal correctness across cells. | (extends HYP-002) |
| Favourable target | benchmark `X%` vs volume-profile vs statistical-magnitude. | `/VPTARGET`, `/MAGTARGET` |
| Adverse target | 1:1 R:R vs previous-move-extreme vs none. | `/ADV-EXTREME`, `/ADV-NONE` |
| Third barrier | adaptive time-cap (benchmark) vs event-based. | `/THIRD-EVENT` (structural), `/THIRD-TIME` (k/window/floor sensitivity) |
| Combined barrier system | interaction of best per-layer candidates; per-cell hit/miss/expectancy distribution. | (derived event def.) |

HYPs and EXP-IDs for 014-B are registered before any result-producing code. At the
close of 014-B, a viable combined event definition may be registered as a candidate
branch for screening (event-level method calibration → EVAL_SUPPORTED → tradability
→ holdout).

## 8. D0 Predeclarations (RATIFIED — G0 PASS 2026-06-14)

All items below are frozen governance parameters. Full specification with rationale,
denominators, and zero-baseline handling in `D0-predeclarations.md` (the authoritative
record). Summary:

| ID | Item | Proposed default | Status |
| --- | --- | --- | --- |
| P1 | ZigZag ATR estimator / period / `ATR_MULT` | Wilder / 14 / 1.0 | **decided (operator)** |
| P2 | Favourable target `X%` (benchmark) | **50%** of prior confirmed move | **decided (operator)** |
| P3 | Adverse target (benchmark) | 1:1 R:R (= favourable distance, opposite side) | proposed |
| P4 | Third barrier (benchmark) | per-cell **adaptive** time cap `N = max(6, round(1.5 × median duration of trailing 20 confirmed moves))` bars | **revised (operator)** |
| P5 | `LOOKBACK` default | 1 (immediately preceding confirmed move) | proposed |
| P6 | Strong-move filter default | OFF (base harami) | proposed |
| P7 | `/STRONG-STAT` window + threshold | trailing **20** confirmed moves; magnitude **≥ p75** of window (MAD-multiple registered alt) | proposed |
| P8 | `/STRONG-HA` consecutive-bar count `X` | **3** bars, real body ≥ trailing-20 median HA body, no opposing wick | proposed |
| P9 | "near-exhaustion" definition + cluster materiality (HYP-003) | position **≥ 0.67** of confirmed move (price-excursion); clustered iff final-third rate ≥ baseline **+ 10 pp** | proposed |
| P10 | "materially different" move-population (HYP-004) | filtered median move magnitude **≥ 1.5×** unfiltered median, retained fraction in **[0.10, 0.50]** | proposed |
| P11 | Per-cell composition rule | **≥ 5 cells over ≥ 3 instruments** (programme convention) | proposed |
| P12 | Capture-rate "viable" bar (HYP-002 routing) | per-cell `P(fav before adv \| resolved)` **≥ 0.55**, bootstrap CI_low **> 0.50**, ≥ 30 resolved events | proposed |
| P13 | Baselines for HYP-003 | random matched-count timestamps (same cell/regime) + MA(20,50)-crossover alternative move segmentation | proposed |

Denominators (P12): primary `fav / (fav + adv)` (resolved-only; symmetric-barrier
null = 0.50); disclosed secondaries `fav / all events` and the third-barrier
censoring fraction. Zero-baseline: a cell with < 30 resolved events is
NOT_VIABLE-by-power (non-reportable for routing), never an infinite/undefined ratio.

## 9. Methodological Guardrails

- Final 30% global holdout excluded from all analysis; no new-universe row read under
  the HA-harami event definition; global holdout seal carries forward.
- Time bars order by `CloseTime`. Never align HA/real views by bar index.
- Harami detected on HA candles; every outcome metric on real prices only — never
  HA prices.
- ZigZag pivots are future information until confirmed; only the trend-change
  confirmation bar is a point-in-time reference for harami evaluation.
- `TickVolume` is a proxy (tick count); volume-profile targets lower priority,
  proxy disclosed.
- No tuning against Phase 014 outcomes; a failed primitive is a valid result, not
  permission to silently try a new variant.
- `tqdm` progress, lazy Polars, per-cell bounded memory across the 102-cell grid.

## 10. Phase Outcome Criteria (mechanical, predeclared)

Adjudicated at a phase gate after 014-A (G1) and after 014-B (G2). All criteria are
gross; all are per-cell first, then composed by P11 (≥5 cells over ≥3 instruments).

| Outcome | Criteria | Consequence |
| --- | --- | --- |
| PROCEED_TO_SCREEN | (a) substrate **and** detector READY (EXP-048) on ≥ the P11 quorum; (b) capture geometry **viable** — `P(fav before adv\|resolved) ≥ 0.55`, CI_low > 0.50, ≥30 resolved events (P12) in ≥5 cells over ≥3 instruments (P11) (EXP-049); (c) ≥1 014-B combined event definition clears the same P11/P12 composition vs declared baselines (P13). | Register a candidate branch; begin event-level method calibration (EXP-027 analog). |
| CHARACTERISED_NOT_VIABLE | Primitives READY but capture geometry fails P12 over P11 (the AVWAP failure mode in a new dress: signal real but capture geometry not viable). | Family carried as measured-negative; routing decision at retrospective; no candidate branch registered. |
| SUBSTRATE_REFUTED | Determinism / look-ahead / invariant failure, or coverage below the EXP-048 floor, in the substrate or the detector. | Fix or retire the failing primitive before any further work. |
| INCONCLUSIVE | Coverage/uncertainty insufficient, no correctness failure. | Record; new scope required for follow-up. |

## 11. Immediate Next Steps

1. Operator ratifies the §8 D0 items (G0).
2. Enter `CF-HA-HARAMI-001` + variants + HYPs in `multiplicity-registry.md` (Phase
   014 batch).
3. Run the §5 VAL gate (VAL-004) for 15m/30m before EXP-048.
4. Proceed through the research pipeline for EXP-048 (substrate/detector readiness).
