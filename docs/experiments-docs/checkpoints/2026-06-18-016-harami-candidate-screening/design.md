# Phase 016 — CF-HA-HARAMI-001 Candidate Screening

**Status:** **ACTIVE — G0 PASS 2026-06-18** (D0 ratified; `D0-predeclarations.md` frozen;
EXP-070 scoping authorised; no TEST row before freeze file written and hash-pinned).
**Date:** 2026-06-18 (design).
**Family:** `CF-HA-HARAMI-001` (REGISTERED, OPEN — **first candidate active**).
**Opened by:** Phase 015 G-015 PROCEED_TO_SCREEN
([`../2026-06-17-015-ma-substrate-conditioned-harami-full-surface/G-015-gate-review.md`](../2026-06-17-015-ma-substrate-conditioned-harami-full-surface/G-015-gate-review.md);
operator routing "PROCEED; register both native arms"); Phase 015
[`retrospective.md`](../2026-06-17-015-ma-substrate-conditioned-harami-full-surface/retrospective.md) §5.
**Candidate:** `CF-HA-HARAMI-001/CAND-001` — MA(20,50)-native `/STRONG-STAT` conditioned HA harami,
MA-segment 3-barrier geometry; lead arm `N-PARTIAL-V2A`, disclosed arm `N-V2A×ADV-NONE`.
**Discipline (carried, binding):** detection on HA candles; every outcome metric on real prices
(`RealOpen/High/Low/Close`); holdouts sealed; no HA-price outcome metric.

---

## 1. Why Phase 016 exists

Phase 015 measured the full capture/exit surface on the MA(20,50) substrate and delivered
a **PROCEED_TO_SCREEN** verdict: the MA-native conditioned harami, under the bounded-downside
`N-PARTIAL-V2A` arm, satisfies the full G-015 conjunction (median CI_low>0 ∧ raw-mean CI_low>0
∧ beats-RM-native) at P11+P6. Signal is present even at the single-leg BENCH in a ~5-cell geometry-independent core
(GBPUSD/NZDUSD/GBPJPY); the hybrid object is CHARACTERISED_NOT_VIABLE on the disclosed surface.

All Phase 015 work was **gross and TRAIN-only**. Zero TEST rows were read. Phase 016 is the
**first TEST contact** in the family's history. Its job is to establish, in the predeclared
TEST stratum of the full `N-PARTIAL-V2A` G-015 passing cell set (ex-EURUSD), whether the
TRAIN-set gross edge holds out-of-sample — using a calibrated evaluation method — before any
cost/tradability or holdout considerations.

The phase is modelled on the Phase 006/008 AVWAP pipeline (EXP-027 → EXP-028/037/038):
method calibration first (TRAIN-only, verifies FPR control and finite MDE on the candidate's
event population), then a single one-shot TEST confirmation.

## 2. The candidate being screened

`CF-HA-HARAMI-001/CAND-001` (first candidate slot, consumed at G-015 2026-06-18):

- **Entry population**: MA-segment `/STRONG-STAT`-conditioned HA haramis (magnitude-so-far ≥
  p75 of trailing-20 confirmed MA-segment magnitudes; causal). 8360-class on the TRAIN set.
- **Conditioning object**: **native** (not hybrid). `/STRONG-STAT` recomputed on MA segments
  — the same substrate that defines the outcome geometry.
- **Lead arm (binding)**: `N-PARTIAL-V2A` — V2A partial exit (first close past 0.5×M_sofar
  takes half the position; remainder exits at the MA-adaptive cap or the 1:1 stop). Bounded-
  downside (P4=PARTIAL_RECOVERY, 0 tail-driven cells in the G-015 set). 9 G-015 cells / 5
  instruments / 7 non-4h.
- **Disclosed arm (secondary)**: `N-V2A×ADV-NONE` — same partial-exit with no adverse stop
  (MA cap sole stop-out, `adv_count=0`). Broader headline (14 cells / 9 instr) but
  TAIL_DRIVEN (8/14 composing cells 4h; P4=TAIL_DRIVEN, 63/99). Disclosed in EXP-068;
  carried as a secondary disclosure arm in Phase 016, not a binding confirmation target.
- **G-015 passing set (predeclared TEST family basis)**: 9 cells / 5 instruments / 7 non-4h
  from `N-PARTIAL-V2A`, including 2 4h cells. The 5-cell geometry-independent core common to
  both champion arms — GBPJPY-30m, GBPUSD-1h, GBPUSD-5m, NZDUSD-1h, NZDUSD-2h — is present
  even at single-leg BENCH. **EURUSD is TEST-capped instrument-wide** (holdout-contaminated,
  EXP-032) and is the only excluded instrument; all other G-015 passing cells, including 4h,
  enter the predeclared TEST family (subject to EXP-070 FPR calibration).

## 3. The single question

> *On the TEST stratum (last 30% of the first-70% analysis set) of the predeclared full
> `N-PARTIAL-V2A` G-015 passing cell set — excluding EURUSD only — does the MA-native
> conditioned harami show positive per-event gross expectancy (median CI_low>0), beat
> `RM-native`, and compose at a predeclared threshold (per-cell Holm-adjusted)? And at the
> portfolio level, does the gross equal-weight composite across those cells also show a
> positive signal (disclosed, non-binding for the confirmation gate)?*

## 4. Binding inheritances from the G-015 adjudication

Every Phase 016 scope inherits these constraints:

1. **Native object only.** The hybrid object is CHARACTERISED_NOT_VIABLE on the disclosed
   surface; it is never re-introduced as a binding arm in Phase 016.
2. **Lead arm: `N-PARTIAL-V2A`.** `N-V2A×ADV-NONE` is disclosed-secondary; it cannot
   qualify a failed TEST read or broaden a borderline verdict.
3. **EURUSD ineligible.** TEST-capped instrument-wide; no stratum-specific claim for any
   EURUSD × domain cell.
4. **Matched-random null (`RM-native`) in every TEST read.** Signal attribution requires
   beating the own-substrate random control, not just clearing zero.
5. **Gross only (EXP-070/071).** No cost model in the first TEST read. Costs enter only
   in the conditional EXP-072 follow-up; portfolio construction (EXP-073) is also gross
   in its TRAIN selection pass. Both conditional on EXP-071 TEST_CONFIRMED.
6. **Fixed per-cell bootstrap seed.** Inherited from Phase 015 to stabilise viability counts.
7. **Detection on HA candles, all outcomes on real prices** (`RealOpen/High/Low/Close`).
8. **Holdouts sealed.** The global final-30% holdout is never loaded, inspected, or used.

## 5. Experiment slate

EXP-IDs pre-assigned (EXP-067 and EXP-069 retired; next free ID = EXP-070).

### EXP-070 — Event-Level Method Calibration (EXP-027-analog, TRAIN-only)

**Mirrors:** EXP-027 (AVWAP), EXP-044 (Phase 011).
**Question (HYP-023):** On the MA-native conditioned harami event population (TRAIN set,
per-cell), does the predeclared evaluation method — per-event gross ATR-normalised expectancy
under `N-PARTIAL-V2A`, moving-block bootstrap, Holm inference — have controlled FPR (≤0.05
per cell), finite MDE, and deterministic replay, on the predeclared TEST family cells?
**Rationale:** Every new event population with distinct density, clustering, and skew
structure requires its own calibration. The Phase 015 bootstrap machinery used a fixed seed
and a 10,000-draw bootstrap, but FPR/MDE were never measured on the MA-native `N-PARTIAL-V2A`
population. This must pass before any TEST contact.
**Artifacts:** `python/experiments/EXP-070/`; TRAIN-only (first 49% per file); 0 TEST reads;
0 candidate slots.
**Pass criteria (D0):** ≤0.05 FPR in every predeclared TEST family cell (on null synthetic
populations with the same matched-random construction); finite MDE (CI width finite, not
degenerate) in ≥ all cells over ≥2 instruments; determinism second full-pass byte-identical.
A cell failing FPR control is excluded from the binding EXP-071 family with record (calibration
exclusions disclosed). The 2 4h cells in the TEST family are calibrated on the same basis;
they are not pre-excluded.
**Temporal stability diagnostic (walk-forward, TRAIN-only):** a rolling 6-month window on
the TRAIN timeline (step = 1 window; TRAIN rows only, no TEST contact) computes per-cell
gross `N-PARTIAL-V2A` expectancy point estimates. A cell is flagged `DECAYING` if the
final-window point estimate is more than 1 SE below the full-TRAIN estimate. Decaying cells
are disclosed in EXP-070's output and noted in the EXP-071 D0 predeclarations. Temporal
decay is disclosed evidence, not a calibration failure — it does not automatically exclude
the cell from the binding EXP-071 family.

### EXP-071 — One-Shot TEST Confirmation of the Full G-015 Passing Cell Set

**Mirrors:** EXP-037/038 (AVWAP Phase 008).
**Question (HYP-024):** On the TEST stratum of the full predeclared `N-PARTIAL-V2A` G-015
passing cell set (excluding EURUSD), does the MA-native arm show per-event gross expectancy
CI_low > 0, beat `RM-native`, and compose at the predeclared composition threshold? And
does the portfolio-aggregate gross composite confirm positive signal?
**Binding input:** the D0 predeclared TEST family — all G-015 passing cells from EXP-068
`N-PARTIAL-V2A` (all 9 cells), excluding EURUSD, materialized from EXP-068 results artifacts
before any TEST row reading; minus any cells excluded on FPR grounds by EXP-070 calibration.
The composition threshold is predeclared in D0.
**Freeze-before-TEST protocol:**
- All predeclarations in D0 are frozen before any TEST row is loaded.
- A freeze file (EXP-071 `frozen_selection.json`, hash-pinned) records the bound TEST family,
  the matched-random seed, and the inference method hash before EXP-070 verdict.
- No amendment to the TEST family after EXP-070 calibration results are seen.
**Disclosures (non-binding, output in same run):**
- `N-V2A×ADV-NONE` is run on the same TEST strata and reported alongside the binding arm,
  but its result does not determine the verdict.
- `N-BENCH` is disclosed as a signal-check anchor.
- `RM-native` matched-random is run on the TEST stratum for attribution.
- **10% symmetric winsorized mean** (`winsorm`, matching EXP-068 `_winsorized_mean` /
  `TRIM_FRAC=0.10`): computed per cell for both arms as a predeclared disclosed co-primary.
  A cell is `winsorm+` when `m ≥ 30` and the winsorized mean point estimate is `> 0`.
  For `N-PARTIAL-V2A` (binding arm): a cell that is `median+` ∧ `beats-RM` ∧ `winsorm+`
  ∧ `raw-mean-` receives a yellow-flag note (raw-mean failure is more informative in
  PARTIAL_RECOVERY than in TAIL_DRIVEN cells). For `N-V2A×ADV-NONE` (disclosed arm):
  `winsorm+` is the primary MEAN_RECOVERABLE diagnostic — `winsorm+` ∧ `mean-` cells are
  the EXP-072 tail-filter candidates. The winsorized mean does **not** substitute for
  `raw-mean CI_low>0` in the binding gate; the gate is unchanged.
**Composition threshold (D0):** predeclared before EXP-070 result; proposed ≥ 3 cells over
≥ 2 instruments from the predeclared TEST family with per-cell CI_low > 0 (Holm-adjusted
at α = 0.05) and beats-RM contrast CI_low > 0, each cell clearing a pre-TEST calibrated
margin (R1.2 analog). The margin follows Phase 008: a pre-TEST synthetic-null calibration
at the matched cluster structure sets the mechanical margin per cell. With 4h cells
included, the composition threshold remains instrument-anchored (≥2 instruments) rather
than domain-anchored.
**Portfolio disclosure (non-binding):** EXP-071 also emits a gross equal-weight composite
ATR-normalised expectancy CI across all binding TEST family cells — a portfolio-aggregate
metric entered in `test-read-ledger.md` as a disclosure against all member strata (not a
counted read per stratum). This metric gates nothing in EXP-071 but informs the G-016
assessment and the conditional EXP-073 scope.
**Counted TEST reads:** each instrument×domain stratum entering a binding stratum-specific
inference incurs 1 counted read (materialized in `test-read-ledger.md` at D0; capped at 2
lifetime per stratum). The declared TEST family strata must all be at 0 counted reads before
EXP-071 is authorised.
**Slots:** 0 new slots (CAND-001 slot consumed at G-015; EXP-071 is the first counted TEST
read under that slot, not a new slot).

### EXP-073 — Portfolio Construction and Fitness (conditional)

**Gate:** opened only if EXP-071 returns TEST_CONFIRMED (§7); requires explicit operator
direction; has its own D0 predeclaration. May run in parallel with EXP-072.
**Question (HYP-026, conditional):** Across the EXP-071 confirmed cell set, which portfolio
construction — equal-weight, inverse-volatility, instrument-cluster, or domain-stratified
— delivers the best gross portfolio-level expectancy on the TRAIN set and how does it hold
in the TEST stratum? Does the combined portfolio pass the programme's portfolio fitness
unit (EXP-018 analog) on the harami event population?
**Rationale:** Per-cell Holm inference proves individual cell edges; portfolio construction
determines tradable position-sizing, diversification structure, and portfolio-level economic
viability — a distinct and complementary question. The EXP-071 portfolio disclosure
(equal-weight composite) is the gross anchor; EXP-073 extends it to multiple schemes and
the portfolio fitness gate.
**Scope:** TRAIN-only portfolio scheme selection + TEST-stratum portfolio aggregate (entered
as a disclosure against all member strata, not a new per-stratum counted read). The
portfolio fitness gate (EXP-018 analog) is TRAIN-only. Multiple weighting schemes are
predeclared in EXP-073's own D0; the best scheme is selected by a predeclared TRAIN-side
rule before the TEST composite is computed.
**Note:** EXP-073 is a registered future scope, conditional on EXP-071 TEST_CONFIRMED.

### EXP-072 — Cost-Aware / Tail-Filter Follow-Up (conditional)

**Gate:** opened only if EXP-071 returns TEST_CONFIRMED (§7); requires explicit operator
direction; has its own D0 predeclaration before any cost-adjusted data contact.
**Question (HYP-025, conditional):** Under the frozen per-instrument cost model, does the
`N-PARTIAL-V2A` net per-event expectancy on the EXP-071 confirmed cell set remain positive
(CI_low > 0)? Does a targeted tail-filter / capped-downside treatment recover net positivity
in the `N-V2A×ADV-NONE` TAIL_DRIVEN cells (the MEAN_RECOVERABLE lever)?
**Rationale:** The Phase 015 mean edge is thin (11–14/99 gross). A cost model will further
narrow it. If EXP-071 confirms the gross edge, EXP-072 determines whether the signal is
economically viable before any cTrader parity or holdout consideration.
**Cost model (D0):** frozen per-instrument round-trip costs (carry forward from EXP-030
CONSERVATIVE model + Phase 008 financing convention). No iteration after cost results.
**Note:** EXP-072 is a registered future scope, conditional on EXP-071 TEST_CONFIRMED.

## 6. D0 decisions required before G0

These items must be operator-ratified before any result-producing code (including EXP-070):

**Q1 — Materialise the predeclared TEST family.** Extract all instrument×domain cells from
EXP-068 `N-PARTIAL-V2A` results (`g015_verdict.json` or `champion_map.csv`) that satisfy:
(a) g015-conjunction flag = True, (b) instrument ≠ EURUSD. 4h cells are included; there is
no domain exclusion. Enter each as a 0-read open stratum in `test-read-ledger.md` (5m/15m/30m
rows already materialized in the Phase 016 D0 change; 1h/2h/4h rows exist and are open).

**Q2 — Materialise 5m/15m/30m strata in `test-read-ledger.md`.** Domains 5m, 15m, and 30m
were introduced in Phase 014 (VAL-004 admitted; harami active on all 6 domains) but have
no ledger rows. Materialise all 17 instruments × {5m, 15m, 30m} = 51 new rows before any
harami experiment reads a TEST row in those domains. Old-universe 5m disclosures (EXP-021/
022/028/029/030/031/040 pre-split reads) must be noted for EURUSD/XAUUSD/BTCUSD/USTEC-5m.

**Q3 — Fix the composition threshold for EXP-071.** The proposed threshold (revised to
cover the full 9-cell family): ≥ 3 cells over ≥ 2 instruments from the predeclared TEST
family with per-cell CI_low > 0 (Holm-adjusted at α = 0.05) and beats-RM contrast CI_low
> 0, each cell clearing a pre-TEST calibrated margin (R1.2 analog). Domain composition is
disclosed (the ≥2 non-4h sub-rule from G-015 is not re-applied here as a gate condition;
operator to confirm or revise this). Operator to confirm threshold or revise.

**Q4 — Fix the method calibration (EXP-070) pass criteria.** Proposed: FPR ≤ 0.05 in every
declared cell on matched-structure null populations (same harami event density per cell, same
matched-random construction), finite CI width (not degenerate), determinism byte-identical
second pass. Any cell exceeding FPR = 0.05 by > 0.01 is excluded from the binding EXP-071
family with record.

**Q5 — Confirm the gross-only posture for EXP-071.** Phase 016 is gross throughout EXP-070
and EXP-071; costs enter only in EXP-072 (conditional). Operator to confirm this ordering.

**Q6 — EXP-073 D0 scope and portfolio fitness convention (if warranted).** Opened only after
EXP-071 TEST_CONFIRMED. Pre-commit on: (a) the set of weighting schemes to be tested
(proposed: equal-weight, inverse-ATR-volatility, instrument-cluster by region/type, domain-
stratified); (b) the TRAIN-side scheme selection rule (proposed: highest Sharpe-analog under
fixed seed on TRAIN events, selected once before the TEST composite is read); (c) whether the
EXP-018 portfolio fitness gate applies to the harami population or a harami-specific analog
is needed. Operator notes any deviations here. EXP-073 may run in parallel with EXP-072.

**Q7 — EXP-072 D0 scope (if warranted).** The cost model convention (frozen CONSERVATIVE RT
values from Phase 008), the financing layer, and the tail-filter / capped-downside mechanism
for `N-V2A×ADV-NONE` are to be predeclared at EXP-072's own D0, opened only after EXP-071
TEST_CONFIRMED. Operator notes any deviations from the Phase 008 cost convention here.

**Q9 — Winsorized mean as predeclared disclosed co-primary.** Confirm that the 10%
symmetric winsorized mean (matching EXP-068's `_winsorized_mean` function, `TRIM_FRAC=0.10`)
is predeclared as a disclosed co-primary in EXP-070 and EXP-071. The binding gate criterion
remains `raw-mean CI_low>0`; the winsorized mean is a disclosed point-estimate diagnostic,
not a gate condition. For `N-PARTIAL-V2A`: a `winsorm+` ∧ `raw-mean-` divergence in a
PARTIAL_RECOVERY cell is flagged (yellow flag). For `N-V2A×ADV-NONE`: `winsorm+` ∧ `mean-`
identifies MEAN_RECOVERABLE candidates for EXP-072. Operator confirms this convention or
revises (e.g., making `winsorm CI_low>0` a binding co-primary for the disclosed arm).

**Q10 — cTrader parity requirement (scope clarification).** For the harami family, no cTrader
strategy implementation or parity validation exists yet (the VAL-002 parity covers only the
AVWAP strategy). A Python-side TEST confirmation (EXP-071) is independent of cTrader parity;
parity is a follow-up requirement before any cTrader-side holdout or live deployment step.
Operator to confirm that EXP-071 proceeds as Python-only, with cTrader parity as a post-Phase-
016 gate (matching the Phase 006/008 sequence for AVWAP: EXP-028 Python → EXP-029 cTrader).

## 7. G-016 gate outcome criteria

G-016 is adjudicated **after the full Phase 016 slate** (EXP-070 pass + EXP-071 result;
EXP-072/EXP-073 output if opened). The terminal gate covers the binding TEST confirmation.

| Outcome | Criteria | Consequence |
| --- | --- | --- |
| **TEST_CONFIRMED** | EXP-071 composition threshold met (≥3 predeclared cells CI_low>0 ∧ beats-RM, ≥2 instruments, Holm-adjusted at α=0.05 + calibrated margin); no EXP-070 method defect in the binding cells. | Candidate advances: EXP-073 portfolio construction + EXP-072 cost-bearing tradability (both conditional) → cTrader parity → tradability → holdout. First counted TEST reads recorded in ledger. |
| **TEST_INCONCLUSIVE** | Gross CIs span zero on the composite or key binding cells (power-limited or CI half-width large); no systematic negative. | Record evidence; family stays OPEN. A targeted follow-up (e.g., larger cell count, cost awareness before commit) may be scoped separately. Counted reads consumed regardless. |
| **TEST_NOT_CONFIRMED** | Predeclared family fails the composition threshold with CI_low ≤ 0 on the majority of binding cells (systematic negative, not power-limited). | CAND-001 retired on the tested scope; family stays OPEN (hybrid object reinstatable as its own scope if a future gate judges the inferential disposition insufficient; other native arms may be registered separately). Counted reads consumed. |
| **METHOD_DEFECT** | EXP-070 FPR exceeds threshold in > 2/3 of predeclared cells, or determinism fails. | Fix calibration; re-run EXP-070 before any TEST contact. Does not consume counted reads. |

## 8. TEST-stratum management

**Cap rule (inherited):** 2 lifetime counted reads per instrument×domain TEST stratum.
At-cap strata are permanently capped and ineligible for future stratum-specific binding
reads (treated like EURUSD-4h after EXP-037/038).

**EURUSD exclusion (binding):** EURUSD is TEST-capped instrument-wide (holdout-contaminated
via EXP-032 + EURUSD-4h at the 2-read cap). No EURUSD stratum enters EXP-071's binding
family. EURUSD Phase 015 native cells are disclosed-only.

**Strata consumed by EXP-071:** each predeclared cell (excluding EURUSD) that enters a
binding stratum-specific inference incurs exactly 1 counted read. Budget: ≤ 9 strata
(the full N-PARTIAL-V2A G-015 passing count ex-EURUSD, including up to 2 4h cells).
EXP-073 portfolio aggregate is a disclosure against all member strata — no additional
counted reads beyond EXP-071's budget.

**New strata materialized at D0 (before G0):** 5m/15m/30m rows for all 17 instruments in
`test-read-ledger.md`. The old-universe 5m pre-split disclosures (Phases 004–010) are
recorded as disclosures in those rows, not as counted reads.

## 9. Guardrails (carried)

- Final-30% global holdout excluded; no data row from the holdout is loaded at any stage.
- TRAIN/TEST split by chronological 1-minute-row boundary (first 49% = TRAIN, next 21% = TEST,
  final 30% = holdout; strict chronological ordering per instrument file).
- No HA-price outcome metric; HA candles for harami detection only.
- No pooling of native and hybrid objects.
- `N-V2A×ADV-NONE` is disclosed in EXP-071 but never upgrades a failed binding arm verdict.
- Freeze-before-TEST: the TEST family and composition threshold are frozen and hashed before
  any TEST row is loaded; no amendment after EXP-070 results.
- No optimisation, parameter sweep, or post-result cell selection inside Phase 016. The
  declared TEST family is fixed at D0.
- Cost model frozen at EXP-072 D0 (if opened); no iteration after cost results.
- Detection on HA candles; MA(20,50) on real close; barriers evaluated on real prices.

## 10. Immediate next steps

1. **Operator D0 ratification** — rule on Q1–Q10 (§6); materialise the exact TEST family
   from EXP-068 results (all G-015 cells ex-EURUSD incl. 4h); freeze and enter the
   composition threshold and method pass criteria in `D0-predeclarations.md`. 5m/15m/30m
   strata are already materialized in `test-read-ledger.md` (Phase 016 D0 change 2026-06-18).
   **G0 gate is the D0 ratification.**
2. **Phase 016 batch already registered** in `multiplicity-registry.md` (HYP-023/024/025/026;
   EXP-070/071/072/073; done in Phase 016 D0 change).
3. **Scope EXP-070** (Stage 1) after G0 PASS; include temporal stability walk-forward
   diagnostic; implement + run; await calibration result.
4. **Scope EXP-071** after EXP-070 PASS: freeze the TEST family + inference hash; run the
   one-shot TEST (including portfolio-aggregate disclosure output); record counted reads in
   `test-read-ledger.md` in the same change that records the result.
5. **Open EXP-073 + EXP-072** if EXP-071 TEST_CONFIRMED (each with its own D0 before data
   contact; may run in parallel).
6. **G-016 adjudication** after EXP-071 (+ EXP-072/EXP-073 if warranted).

---

*Companion documents: Phase 015 retrospective
[`../2026-06-17-015-ma-substrate-conditioned-harami-full-surface/retrospective.md`](../2026-06-17-015-ma-substrate-conditioned-harami-full-surface/retrospective.md);
G-015 gate review
[`../2026-06-17-015-ma-substrate-conditioned-harami-full-surface/G-015-gate-review.md`](../2026-06-17-015-ma-substrate-conditioned-harami-full-surface/G-015-gate-review.md);
candidate family spec
[`../../../signal-registry/candidate-families/harami.md`](../../../signal-registry/candidate-families/harami.md);
family detail index
[`../../families/cf-ha-harami-001/INDEX.md`](../../families/cf-ha-harami-001/INDEX.md);
source candidate EXP-068 [`../../../../python/experiments/EXP-068/`](../../../../python/experiments/EXP-068/).*
