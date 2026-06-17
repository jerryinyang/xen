# Phase 014-B — Conditioned Signal, Capture Geometry & Position-Management Surface

**Checkpoint type:** Research sub-phase design (extends Phase 014 `design.md` §7).
**Date:** 2026-06-15.
**Status:** ACTIVE — opened after the 014-A **G1 gate** (`G1-gate-review.md`): primitives
READY, benchmark capture `CHARACTERISED_NOT_VIABLE` **on the unconditioned object only**;
family **OPEN**; operator directed proceed-to-014-B (no closure). **G0-B PASS 2026-06-15**
(operator ratified `014-B-D0-addendum.md` P14–P21: median expectancy endpoint, mean
disclosed; `ATR_MULT_TRAIL = 0.5`, tunable later). All work remains **gross, 0 candidate
slots, 0 TEST reads, holdouts sealed.**
**Governing family spec:** `docs/signal-registry/candidate-families/harami.md`.
**D0 addendum (binding params):** `014-B-D0-addendum.md` (P14–P21).

> ## MANDATORY READING — before scoping ANY 014-B experiment
> Every 014-B experiment scope (research-pipeline Stage 1) MUST first read
> [`014-A-conditioning-gap-and-validation-lessons.md`](014-A-conditioning-gap-and-validation-lessons.md)
> and confirm in its `scope.md` that the experiment (a) applies the family's **conditioning**
> where the hypothesis requires it, (b) **anchors at the harami** when testing signal
> efficacy, (c) treats position-in-move as **descriptive-only** (never a live filter), and
> (d) uses the **expectancy** endpoint (P14), not first-hit `r`, as the binding metric. This
> is a hard Stage-1 precondition; a scope that omits the confirmation is REVISE at Stage 4.

## 1. Why 014-B exists (what 014-A did *not* test)

014-A validated primitives and characterised the **unconditioned** signal. The family's
actual hypothesis — *a strong-move-qualified HA harami, **anchored at the harami**, marks a
reversal that a non-symmetric capture geometry can convert to gross-positive expectancy* —
was **never run through an outcome read**:

- EXP-049 (`r≈0.50`) anchored on the **ZigZag confirmation, no harami, filter OFF**.
- EXP-052 (excursion ≈0) used the **raw harami, filter OFF**.
- EXP-050 measured raw-harami **position** (a non-live, descriptive quantity) — a base rate,
  not a refutation.
- EXP-051 proved `/STRONG` carves a materially different population but fed it into **no**
  outcome read.

Two further unaddressed risks from G1: the EXP-049 read was **short-horizon** (P4 cap bound
at the 6-bar floor in 96/99 cells) under a **worst-case tie-break**, and no AVWAP-style
**lifetime availability** diagnostic exists. 014-B closes all of these.

## 2. Objective

Measure the **conditioned** signal's gross capture across the **full registered + new**
barrier and position-management surface, plus a corrected fill model and a lifetime
availability read, so that a closure decision (if any) is made at G2 on the *complete*
conditioned surface — never on the unconditioned benchmark. No frozen end-to-end strategy is
screened; gross throughout; the cost model enters only at a future tradability screen.

## 3. Binding endpoint (operator decision 2026-06-15) — see P14

The binding viability metric is the **median gross per-event expectancy** (ATR-normalised
realised gross return under the rule, with realistic intrabar fills — median chosen for
robustness to the fat-tailed return distribution), with regime-clustered
moving-block-bootstrap CIs. The **mean** per-event return and first-hit `r` (P12) are retained
as **disclosed secondaries** only. Rationale: partial exits and trailing stops cannot express
value under a first-hit rate (lessons §8.6) — the metric must match the mechanism.

## 4. No intermediate gates (operator decision 2026-06-15)

The full surface is explored before any adjudication. **There are no G1.x sub-gates and no
early-closure path inside 014-B.** A single **G2** is adjudicated only after every theme
below is measured. This is a deliberate guard against premature closure: a negative on one
geometry never short-circuits the others.

## 5. Experiment slate (gross; 0 slots; 0 TEST; all per-cell then P11)

EXP-IDs assigned at Stage-1 scoping (next free per `python/experiments/INDEX.md`; the slate
below is the registered plan). The three **lead** reads (EXP-053/054/055) are the cheapest
decisive ones and run first; the remainder run regardless of their outcome.

| Order | EXP (planned) | HYP | Question | Notes |
| --- | --- | --- | --- | --- |
| **Lead 1** | EXP-053 | HYP-006 | **Conditioned-signal efficacy.** Does the `/STRONG`-conditioned harami (live magnitude-percentile filter; `/STRONG-HA` alt), **anchored at the harami**, produce positive gross per-event expectancy under benchmark barriers vs matched controls, P11-composed? | The actual family hypothesis. Expectancy endpoint (P14). |
| **Lead 2** | EXP-054 | HYP-007 | **Intrabar fill-model correction (method).** Under a path-ordered fill model (green `O→L→H→C`, red `O→H→L→C`, P15) replacing the worst-case tie-break, does the benchmark capture readout change materially vs EXP-049? | Satisfies the long-standing "intrabar exit fills DEFERRED behind a dedicated fill-rule method validation." Re-reads EXP-049 benchmark. |
| **Lead 3** | EXP-055 | HYP-008 | **Long-horizon availability (AVWAP-analog).** Over the full reversal move, what is the conditioned signal's lifetime favourable MFE vs adverse MAE (gross, ATR-normalised), vs the cost-floor-analog reference? | Settles AVWAP's situation (move available, capture missing) vs worse (no move). EXP-047 `move_size.py` machinery. |
| Surface | EXP-056 | HYP-009 | **Favourable-target geometry.** `/VPTARGET`, `/MAGTARGET` vs benchmark 50%, expectancy. | TickVolume proxy disclosed for `/VPTARGET`. |
| Surface | EXP-057 | HYP-010 | **Adverse-target geometry.** `/ADV-EXTREME`, `/ADV-NONE` vs benchmark 1:1, expectancy. | The asymmetric lever that can move `r` off 0.50. |
| Surface | EXP-058 | HYP-011 | **Third-barrier geometry.** `/THIRD-EVENT`, `/THIRD-TIME` vs benchmark adaptive cap, expectancy + censoring. | P4 bound at floor in 96/99 — `/THIRD-TIME` probes longer horizons. |
| Surface | EXP-059 | HYP-012 | **Position-management exits.** `/EXIT-PARTIAL` (scaled favourable) and `/EXIT-TRAIL-STRUCT` (smaller-ATR ZigZag structure trailing), individually and combined, expectancy. | New branches (operator draft). Requires the P15 fill model. |
| Surface | EXP-059B | HYP-012 (follow-up) | **Uncapped structure trailing (EXP-059 gap-fill).** The `/EXIT-TRAIL-UNCAPPED` adverse model — no time-cap backstop, no initial stop — `TRAIL-PURE-UNCAPPED` and `COMBINED-UNCAPPED-V2A` vs BENCH; capped no-init siblings disclosed for cap-isolation. | EXP-059 measured every trailing arm under the benchmark cap; see §10. New countable variant; 0 slots / 0 TEST. |
| Surface | EXP-060 | HYP-013 | **Combined event system.** Best per-layer geometry + conditioned signal: per-cell hit/miss/expectancy distribution vs declared baselines (P13). | The candidate-event characterisation; output feeds G2. |

## 6. New registered branches (operator draft `.ignore/temp/exit.md`)

Defined fully in `014-B-D0-addendum.md` (P17/P18); registered in
`multiplicity-registry.md` (Phase 014-B batch) and `candidate-families/harami.md`.

- **`CF-HA-HARAMI-001/EXIT-PARTIAL`** — favourable-side scaled/partial exits; entry weight
  split into ≤3 parts. Variant #1: {first-profitable-close, calculated target,
  reversal-event}. Variant #2: percentage-to-final-target splits. Adverse-target model
  unchanged. Take-profit only.
- **`CF-HA-HARAMI-001/EXIT-TRAIL-STRUCT`** — adverse-side structure-based trailing stop on a
  **smaller-ATR ZigZag** (predeclared `ATR_MULT` < benchmark): new pivot high → trail stop to
  most recent low (longs); new pivot low → trail to most recent high (shorts); exit on fill.
- **Fill-model correction** — not a signal branch but a measurement-method standard (P15);
  applies to every 014-B outcome read involving more than one barrier on a bar.

## 7. Methodological guardrails (carried from §9 of the master design, plus 014-B additions)

- Final-30% global holdout excluded; no new-universe row read under the HA-harami event
  definition; gross only; detection on HA candles, **all outcome metrics on real prices**.
- ZigZag pivots are future information until confirmed; the harami confirmation bar is the
  point-in-time anchor. **Position-in-move is descriptive-only — never a live filter** (the
  end pivot is future information for an in-progress move).
- The **live "end-of-move" condition is the magnitude-percentile filter** (`/STRONG-STAT`),
  computed from the known move-start to current price vs the trailing distribution.
- No tuning against 014-B outcomes; OAT against predeclared defaults; no post-result variant
  selection. A failed geometry is a valid result, not licence to silently try another.
- `tqdm`, lazy Polars, per-cell bounded memory across the 99-cell member grid.

## 8. G2 outcome criteria (mechanical, predeclared; adjudicated after the full slate)

All gross; per-cell first, composed by P11 (≥5 cells over ≥3 instruments); endpoint =
expectancy (P14), CI_low > 0, ≥30 events.

| Outcome | Criteria | Consequence |
| --- | --- | --- |
| **PROCEED_TO_SCREEN** | ≥1 combined event definition (EXP-060) clears P11 expectancy viability vs declared baselines (P13), on the conditioned signal. | Register that definition as a candidate branch (its first slot); begin event-level method calibration (EXP-027 analog). |
| **CHARACTERISED_NOT_VIABLE** | Full conditioned surface measured; no combined definition clears P11 expectancy. | Family carried as measured-negative **on the full surface**; routing at retrospective; closure now well-supported. |
| **SUBSTRATE/METHOD_DEFECT** | A determinism/causality/invariant failure, or the fill-model read (EXP-054) shows the benchmark null was a tie-break artifact (benchmark flips materially). | Fix the defect / re-baseline before G2 adjudication. |
| **INCONCLUSIVE** | Coverage/power insufficient on the conditioned population, no correctness failure. | Record; new scope for follow-up. |

## 9. Immediate next steps

1. Register the Phase 014-B batch (HYP-006–013, EXP-053–060, `/EXIT-PARTIAL`,
   `/EXIT-TRAIL-STRUCT`, fill-model method) in `multiplicity-registry.md` and
   `candidate-families/harami.md`. *(done with this design.)*
2. Scope EXP-053 (conditioned efficacy) — Stage 1, after the mandatory lessons read.
3. Proceed EXP-053 → EXP-054 → EXP-055, then the surface EXP-056–060, then G2.

## 10. Addendum (2026-06-16) — EXP-059B: uncapped structure trailing (EXP-059 gap-fill)

EXP-059 measured every standalone-trailing and combined arm under the benchmark adaptive time
cap (verified in `xen.position_exits`: `resolve_legs`/`build_active_stops` are bounded by
`bench_n`, with an explicit `TIMECAP` exit). Even `TRAIL-TP-NOINIT`, which already drops the
initial 1:1 stop, retained the cap — so the family's "trailing as a standalone adverse-exit
model" (no initial stop **and** no time cap) was never measured. EXP-059B fills this gap on the
same conditioned population and 99-cell grid via the new countable variant
`CF-HA-HARAMI-001/EXIT-TRAIL-UNCAPPED`: `TRAIL-PURE-UNCAPPED` and `COMBINED-UNCAPPED-V2A` vs
BENCH (binding paired contrast), with capped no-init siblings re-run for a disclosed
cap-isolation contrast and `DATA_CENSORED` disclosed separately from capped censoring. Full
specification: [`014-B-EXP-059B-uncapped-trailing-addendum.md`](014-B-EXP-059B-uncapped-trailing-addendum.md).
0 slots, 0 TEST reads, TRAIN-only, gross; joins the single 014-B G2 (no intermediate gate).

## 11. Addendum (2026-06-17) — EXP-060B: MA(20,50) substrate dominance, genuine lead or skew artifact? (EXP-060 gap-fill)

EXP-060 returned `CHARACTERISED_NOT_VIABLE_ELIGIBLE` (champion 0/99 wins) and recorded the result as *"MA-baseline
dominance is a substrate property."* Post-hoc investigation of the generated results (2026-06-17) found that
reading rests on two confounds the experiment's emitted outputs cannot resolve: (i) the champion's gross **mean**
is ≈0 or negative on 5/6 domains despite a positive median — a capped-upside (V2A) / uncapped-downside (`/ADV-NONE`)
left-skew mirage — and EXP-060 emitted MA's *median* only, never MA's mean or exit-composition; (ii) MA(20,50)'s
median advantage was **never tested against a matched-random control on the MA substrate**, so "the harami adds
value on MA" is unsupported (on ZigZag the entry was already proven redundant vs random). EXP-060B fills both on
the same conditioned population and 99-cell grid: it emits MA mean + exit-reason composition, adds the
matched-random-on-MA control (`RM3`), and bootstraps the mean alongside the median. Binding discriminator: does the
MA-substrate harami (`M3`) clear P11 median viability **and** beat `RM3` (CI_low>0) with mean clearing P11
(SUBSTRATE_LEAD_FOUND), or is MA's dominance the same median≫mean / entry-redundant artifact (ARTIFACT_CONFIRMED)?
Median binding (P14), mean disclosed; **no new countable item** (composes registered `/EXIT-PARTIAL` V2A,
`/ADV-NONE`, the benchmark cap, and the two P13 baselines; the MA-substrate matched-random is a null). 0 slots,
0 TEST reads, TRAIN-only, gross; runs **before** and feeds the single 014-B G2 (no intermediate gate). Full
specification: [`014-B-EXP-060B-ma-substrate-dominance-addendum.md`](014-B-EXP-060B-ma-substrate-dominance-addendum.md).
