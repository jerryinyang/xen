# Phase 006 Design: Thesis-Qualification Referee Calibration

**Phase:** 006 — Thesis-Qualification Referee Calibration
**Date:** 2026-05-31
**Status:** Active
**Predecessor:** 2026-05-28-005-htf-state-descriptor-differentiation

## Decision Status

Phases 001–005 closed both major theses the programme pursued — event-chart-as-alpha (001–002) and ICT-as-alpha (003–004) — and then the higher-timeframe state-descriptor thesis (005), each with a clean, holdout-preserving no-go and no candidate manifest. Three consecutive closures share one uncomfortable property: **every "reject" was issued by a gate stack whose own error profile was never measured.** A rejection from such a stack cannot distinguish *"no edge exists"* from *"an edge exists but below the stack's unmeasured detection floor."* That ambiguity — not any particular market idea — is what Phase 006 takes as its object.

Xen is therefore refreshed **in place** (same repo, no separate project, no new project name) onto a new object of study: the **referee** that qualifies trading theses, and — first and inseparably — the measurement apparatus that makes its verdicts interpretable. This is not a search for a market edge. The unit of progress this phase is a *measured property of the referee*, not a verdict on a trading idea.

This design **synthesises and supersedes-as-operative** the three planning documents in `docs/planning/`:

- `thesis-qualification-system-problem-statement.md` — the seed (what the referee must contend with; desiderata D1–D8, the §3 reference specimen, failure modes T1–T12, the implicit loss function §5, the calibratability requirement §6).
- `charter.md` — the founding design (object of study, falsifiable founding thesis, the two-species calibration split, the founding experiment, 13 binding constraints, 4 honesty clauses).
- `state-and-open-decisions.md` — the reconciled state and the resolved decisions D0–D7 (intentional artefact retention; the baseline stack materialised by transcription from EXP-036; numbering continued at Phase 006 / EXP-037).

Those documents argue the case and record the decisions; **this document locks the phase**: the object measured, the baseline referee under test, the two-part calibration, the gates, the constraints, and the execution order.

## What Changed From Prior Phases

| | Phases 001–005 | Phase 006 |
| --- | --- | --- |
| Object of study | a market thesis (chart type, ICT setup, state descriptor) | the **referee** that judges theses |
| Unit of progress | a verdict on a trading idea | a **measured property of the gate stack** (FPR, power surface, per-leg pass rates) |
| What is "on trial" | the candidate descriptor | the **gate stack itself** (the existing Xen stack) |
| Holdout role | a future reserve for a surviving candidate | untouched; this phase spends none of it |
| Preferred outcome | a defensible decision | a **trustworthy measurement** of the referee, including the uncomfortable one |

The chart-type architecture (`bar_aggregator.py`, `time_alignment.py`, `linebreak_generator.py`, `renko_generator.py`, `heiken_ashi_generator.py`) remains shared, agnostic infrastructure. Theses to come still ride on it; the referee does not put it on trial.

## Phase Thesis (founding thesis, falsifiable)

> **H1.** A qualification system's operating characteristics — false-positive rate, a power *surface*, and per-leg pass rates — can be measured with enough fidelity that its verdicts (especially **"reject"**) carry a quantified, trustworthy meaning.

> **Null (H0).** They cannot. The power estimate is so sensitive to the choice of synthetic effect-generator that an "empirical minimum detectable effect" is merely relocated guesswork — the calibrator itself needs calibrating, and its fidelity is unfalsifiable.

This is the *first* question, asked before any gate is redesigned. The problem statement's §6 proposes calibration as the cure for un-interpretable rejections, but calibration only measures the referee *with respect to the synthetic data-generating process used to plant effects* — and the structure of real edges is exactly what is unknown. If H0 holds, the entire §6 programme is built on sand, and Phase 006 must discover that **before** designing gates around it. The cure is not assumed to work.

**Decision rule (predeclared):**

- If the power estimate is **stable** across a deliberately diverse family of planted structures → H1 is supported *for that family*; calibration earns provisional trust and the programme may proceed to successor-gate design (a later phase).
- If the power estimate **moves materially** with the synthetic family → H0 is supported; priority shifts from "design gates" to "characterise and bound the fidelity gap," and **no calibrated MDE is reported as if it were real.**

A null result on H1 is a successful, reportable outcome of this phase (honesty clause C4).

## The Baseline Referee Under Test

The first object measured is the **existing Xen gate stack** — the one that closed Phases 003–005 — not a freshly designed stack. Two independent reviews converged on calibrating the *current* stack first, because it is the only thing that **answers Xen §5.6** (were the three closures sound, or was the stack blind to a modest real edge?) at near-zero marginal cost, since the calibration harness must be built regardless.

Per decision D2, the stack is **materialised by verbatim transcription from the retained `python/experiments/EXP-036/code/run_experiment.py`** — the last and most-evolved Phase-005 application — then frozen. Its predeclared constants are verified identical across the Phase-005 closure experiments EXP-034/035/036. There is no reconstruction-from-memory and no sealed archive to breach; the implementation is read directly.

Following binding constraint 9, the stack is specified in **two layers**, and **only the evidentiary layer is calibrated**:

### Admissibility layer (validity preconditions — held FIXED, never calibrated)

These are hard preconditions with no operating characteristics to tune; calibrating them would be a category error. Calibration holds them constant.

- No look-ahead: a descriptor is observed only after its bar closes; earliest entry is the next bar open.
- Holdout exclusion: the final 30% global holdout is removed from the 1-minute series before any aggregation or computation.
- Real-price outcomes only: all returns use real OHLC; **no synthetic (HA/Renko) price enters any measured return**.
- Timestamp alignment by `CloseTime` (aggregated real bars) / `SourceCloseTime` (chart-type events); never by bar index.
- Inference unit = independent state **episode** (or non-overlapping block); naive row-level inference is diagnostic only.
- Full predeclaration of parameters, thresholds, baselines, and split.

### Evidentiary layer (the objects whose error profiles are measured)

Transcribed verbatim from EXP-036 and frozen (constraint 13 — measured first, never loosened to make theses pass):

1. **Representation floors** (per state, per segment): rows ≥ 100 (train) / ≥ 50 (test); **episodes** ≥ 30 (train) / ≥ 15 (test). Adjudicability: the neutral contrast requires both extreme buckets *and* the middle bucket to clear floors; the control contrast requires both extremes.
2. **Neutral-baseline gate** (`Delta_neutral`): direction-adjusted excess of the extreme state's executable next-bar log return over the *measured* middle-bucket mean `mu_mid`, via a two-sample episode bootstrap that propagates the baseline's sampling error.
3. **Matched-control gate** (`Delta_control`): paired head-to-head against a deliberately naive prior-bar-momentum-sign control, `mean((d − c)·r)` on the descriptor's own traded bars.
4. **Replication / sign-preservation rule:** the test-segment bootstrap CI lower bound > 0 **and** the train-segment point estimate > 0 (same-signed; test CI excludes zero positively).
5. **Replication breadth k = 2:** the both-contrast pass must hold on **≥ 2 distinct instruments** at a timeframe; the independence unit is the **instrument** (horizons/parameters of one instrument do not count).
6. **Bootstrap:** 10,000 episode-level resamples, fixed seed, deterministic per-cell seed offsets, cell-budget cap 2M index cells.
7. **Secondary horizon:** a single predeclared 4-bar hold under asymmetric semantics — it can reopen a question at a longer horizon but is **barred from producing the primary pass**.
8. **Decision ladder (already present):** `FOR` / `STATE_DIFFERENTIATION_ONLY` / `HORIZON_DEPENDENT` / `INCONCLUSIVE` / `AGAINST` — the stack already emits a graded verdict, not a binary one (constraint 12 in embryo).

### What the stack does NOT yet contain (added *around* it in Deliverable #2, never *into* it)

These are calibration-harness or charter constructs, absent from the closed-thesis stack and therefore newly drafted — not transcribed:

- **Economic-materiality threshold + proxy-cost regimes** (constraint 11). EXP-036 carries only an `EntryGapMin` executability diagnostic, no spread/slippage model. A pass must clear a predeclared minimum economically meaningful effect *net of frictions*, reported per **low / central / stress** proxy regime, never under one hidden cost.
- **Harness degrees of freedom + an explicit stopping rule** (constraint 7). The synthetic generator, planted effect sizes, and null construction are researcher DoF; they are pre-registered with a stated stopping rule for the regress.
- **Frozen calibration battery + second-order holdout** (constraint 10). The battery is versioned and frozen; a reserve of calibration cases never seen during referee work gives the referee its own untouched holdout. Trust attaches only to that reserve.
- **Compute budget** (constraint 6), stated up front (D7).

## Two Species of Calibration (kept separate — load-bearing)

The problem statement merges these under one "calibration" banner; this phase splits them **permanently**, because they have opposite epistemic status. Every reported error rate is tagged with its species; a claim resting on power calibration always carries its synthetic-family conditioning explicitly.

| | **Null calibration** | **Power / MDE calibration** |
| --- | --- | --- |
| Measures | FPR, per-leg false-pass rate | TPR, detectable-effect *surface* |
| Needs a model of "a real edge"? | **No** | **Yes** — the thing we don't have |
| Method | Dependence-preserving resampling of the **real** series (circular-block / stationary bootstrap; multivariate / sieve for cross-series) that breaks the candidate's conditioning relationship while preserving serial dependence, volatility clustering, calendar structure, and cross-market correlation. Naive shuffles are diagnostic-only. | Plant synthetic effects of known magnitude/structure into real or surrogate series. |
| Epistemic status | **Trustworthy** — conclusions may be staked on it | **Fragile** — assumption-laden; conditional on the synthetic family |

**Null realism is a validity requirement, not a detail.** A null that destroys volatility clustering, serial dependence, calendar effects, or cross-market correlation manufactures noise that looks tradeable and makes the FPR estimate optimistic. The null construction is predeclared and its preserved/destroyed structure documented — because the trustworthiness of the "trustworthy" half is exactly the realism of the null.

## Founding Experiment Roadmap

The charter's single founding experiment (two-part calibration) is realised through the pipeline as **one pre-registration deliverable plus two experiments**, honouring the one-falsifiable-question-per-experiment rule. The next free experiment ID is `EXP-037` (verified: `python/experiments/INDEX.md` tops out at EXP-036). IDs are never reused; the EXP-037/038 placeholders that appeared in the *closed* Phase 005 design were never instantiated and remain free.

### Deliverable #2 — Predeclared reference-stack specification (runs first, no code)

A pre-registration document, governance-reviewed before any EXP-037 scope, that:

1. transcribes the EXP-036 evidentiary stack and freezes it (the two layers above), naming EXP-036 as the canonical version and noting any earlier-phase divergence in shape;
2. drafts the four new constructs — economic-materiality threshold + low/central/stress proxy-cost regimes; harness DoF + explicit stopping rule; frozen battery + second-order holdout; compute budget;
3. predeclares the null-construction method (block/stationary bootstrap + permutation) and the synthetic-effect family for power (mechanisms × parameters).

This is the immediate next artifact (see *Immediate Next Step*). It is the object both experiments execute against.

### Stage A — Null calibration (trustworthy)

| Candidate ID | Question | Decision use |
| --- | --- | --- |
| **EXP-037** | Resampling real series to break the candidate's conditioning relationship while preserving dependence structure, what is the frozen stack's empirical **FPR** at its declared thresholds, and the **false-pass rate of each individual gate leg** (which legs leak, which over-reject)? | Produces the *trustworthy* half of the referee's error profile and the first direct input to the §5.6 ruling: is the stack appropriately strict, or over-rejecting at its declared thresholds? |

### Stage B — Power bracketing (fragile, explicitly caveated)

| Candidate ID | Question | Decision use |
| --- | --- | --- |
| **EXP-038** | Planting synthetic edges across a deliberately diverse family spanning **parameters** (horizon, regime location, magnitude, persistence, cross-unit correlation) and **mechanisms** (directional drift, volatility/risk filtering, timing improvement, sizing information, marginal contribution), how **sensitive is the apparent MDE to the synthetic family**, and what is the **power surface** conditioned on (effect structure × regime × replication breadth × horizon)? | The sensitivity result **is** the H0/H1 verdict (§ Phase Thesis). The headline is *not* "the MDE"; a large sensitivity is the finding, not a nuisance to average away. |

### Ruling (after Stage B)

A written **§5.6 ruling** (is the existing stack appropriately strict, too insensitive, or mismatched to the kind of edge worth finding?) plus the **founding-thesis ruling** (is the calibration itself trustworthy under H1, or generator-dependent under H0?). This is the phase's deliverable #4.

### Deferred (no ID; by design)

Design of a *successor / production* gate stack is deferred until the ruling is in, and is to be informed by where the existing stack actually sits. **No gate threshold is loosened before that measurement** (constraint 13). Spending any protected reserve and re-running any closed thesis are out of scope.

## Data Scope

- **Instruments:** EURUSD, XAUUSD, USTEC, BTCUSD — `data/timebars/`, 2023-01 → 2026-05, 1-minute base bars aggregated via `python/src/bar_aggregator.aggregate_ohlc`. The real series is the substrate for both the null resampling (Stage A) and the surrogate base for planted effects (Stage B).
- **Mandatory exclusion:** the final 30% global holdout is excluded from all analysis, applied chronologically to the 1-minute series **before** any aggregation, resampling, or effect-planting. This phase spends none of it.
- **No cost fields:** no tick, bid/ask, spread, commission, or slippage data is assumed. Economic-materiality claims use the predeclared low/central/stress **proxy-cost regimes** only (constraint 11) — never a single hidden cost.
- **Holdout-of-the-referee:** distinct from the market-data holdout, the **second-order calibration holdout** (constraint 10) reserves calibration cases the referee never sees during its own design; operating characteristics drawn from the tuning battery are labelled in-sample.

## Binding Constraints (charter §5, promoted to phase rules)

Each traces to a failure mode of the problem statement and exists to stop the successor system from re-committing it. Full text in `charter.md`; enforced here.

1. **Null vs power never merged** — every error rate tagged with species and, for power, its synthetic-family conditioning.
2. **No scalar MDE** — sensitivity is reported as a conditioned power *surface*; "State X" language banned.
3. **The §6 ↔ T10 ↔ D4 trilemma is one hard constraint** — re-calibration frequency, cumulative-search accounting, and the single protected reserve are mutually limiting; the phase picks an explicit operating point and states what it sacrifices.
4. **The false-negative arm of the loss function is a declared prior, not a measurement** — FN cost is unknowable at rejection time; "tunable" never implies "measured" on that arm.
5. **Alpha decay is a first-class failure mode** — gate sensitivity analysis includes a post-discovery temporal-decay axis.
6. **Bounded, stated compute budget** — a calibration regime more expensive than the research it referees is a design failure to flag, not absorb.
7. **Harness DoF predeclared and audited** — synthetic generator, planted sizes, null construction are pre-registered with an explicit stopping rule for the regress.
8. **Construct-validity vs predeclaration tension named** — aligning the metric to the mechanism "before testing" is itself a fork; the constraining mechanism is an explicit design item.
9. **Admissibility separated from evidentiary — only the latter calibrated** (see § Baseline Referee). Calibration holds the admissibility layer fixed.
10. **No overfitting the calibration suite** — versioned/frozen battery + second-order holdout; tuning-battery characteristics are in-sample.
11. **Economic materiality is first-class** — a pass clears a predeclared minimum meaningful effect net of a frictions model, reported per proxy-cost regime.
12. **Output is a decision ladder, not a binary verdict** — reject / redesign / gather-more-data / paper-trade / spend-reserve-slice / allocate, gated by the cumulative-search correction.
13. **Do not loosen the current gates before calibration** — thresholds measured first, changed only on that evidence; pre-calibration relaxation is indistinguishable from rescuing a false positive.

## Honesty Clauses (charter §6, non-negotiable)

- **C1 — Answer §5.6; do not rescue theses.** The experiment calibrates the *existing* stack to answer §5.6, but measures the **referee only**: closed theses stay closed and are never re-run, re-scored, or rescued. A "the gate was blind" result changes the *referee*, after which any thesis — old or new — must re-qualify from scratch through the corrected stack. It is never a back-door reinstatement of a prior candidate.
- **C2 — The flattering hypothesis is held under suspicion.** This direction was born from the more comfortable hypothesis (the referee may be blind) over its alternative (the ideas were false). The phase is structured so the *uncomfortable* outcome is a first-class, reportable result.
- **C3 — "Near-impassable" is a finding, not a license.** If the stack proves near-impassable even at modest planted effects, that is a recorded finding about conjunctive stringency (T2), **not** grounds to loosen gates until something passes.
- **C4 — H0 is allowed to win.** If power proves unstable across synthetic families, the phase says so plainly and reports no calibrated MDE as if it were trustworthy. A null result on the founding thesis is a successful outcome.

## Phase Gates

1. **Spec-before-experiment gate.** No EXP-037 scope is created until Deliverable #2 (the predeclared, frozen reference-stack spec + the four constructs) passes pre-execution governance. The stack, null construction, synthetic family, battery/holdout partition, and compute budget are all fixed before any calibration runs.
2. **Species-tagging gate.** Every reported error rate carries its species (null = trustworthy / power = fragile-conditional). A power number presented without its synthetic-family conditioning is a `REVISE`.
3. **Admissibility-fixed gate.** Calibration varies the evidentiary layer only. Any procedure that softens an admissibility precondition (look-ahead, holdout contamination, synthetic-price returns, timestamp-by-index) into a tunable score is a category error and a `REJECT`.
4. **No-scalar-MDE gate.** Power is reported as a conditioned surface. A single headline MDE is a `REVISE`.
5. **Second-order-holdout gate.** Trust attaches only to calibration cases the referee never saw during design. Tuning-battery characteristics must be labelled in-sample.
6. **Do-not-loosen gate.** No gate threshold or leg is changed this phase. Relaxation is deferred to a post-ruling successor design and may never be motivated by theses having failed (constraint 13).
7. **Holdout gate.** No Phase 006 work inspects or spends the final 30% global market holdout.
8. **§5.6-measures-the-referee gate.** Outputs are properties of the stack. No closed thesis is re-run, re-scored, or rescued (C1).

## Methods Standards

- Chronological analysis-set slicing with the final 30% global holdout excluded before aggregation/resampling; the existing nested train/test convention (0.70 train fraction within the analysis set) is part of the stack-under-test, transcribed as-is.
- Null calibration uses dependence-preserving resampling (circular-block / stationary bootstrap; multivariate / sieve for cross-series) that breaks conditioning while preserving serial dependence, volatility clustering, calendar structure, and cross-market correlation. Naive shuffles are diagnostic-only and labelled.
- Power calibration plants effects of known magnitude/structure varied by **mechanism and parameter**; every power claim names its synthetic family.
- Inference unit = independent episode / non-overlapping block (the stack's own convention); 10,000-resample episode bootstraps with fixed deterministic seeding, as transcribed.
- Real OHLC for every measured return; no synthetic price in any error-rate computation.
- Report counts, coverage, and per-leg pass rates before headline error rates. Define denominators and zero-baseline behaviour before implementation.
- Economic materiality reported per low/central/stress proxy-cost regime, never under a single hidden cost.

## Complexity Budget

Per experiment:

- Maximum statistical test families: 3.
- Maximum primary plots: 4 (for the power surface, bounded conditioned slices — never an unbounded grid dump).
- Maximum new reusable modules: 1, and only if existing modules cannot support the scope cleanly. The natural new module is a **calibration harness** under `python/src/` (null resampler + synthetic-effect planter + the frozen-stack runner), shared by EXP-037 and EXP-038; it is built once.
- Never materialise the holdout or unbounded detail tables for plotting.

For the checkpoint:

- One pre-registration deliverable (#2) + two experiments (EXP-037 null, EXP-038 power) + one ruling (#4).
- The compute budget (constraint 6 / D7) is fixed in Deliverable #2 and bounds bootstrap replications × effect families × stack legs × instruments up front; exceeding it is a flagged design failure, not an absorbed cost.
- No successor-stack implementation, no gate-threshold change, and no holdout access in this checkpoint.

## Explicit Non-Goals

- No design or implementation of a *successor / production* gate stack — deferred until the ruling (charter §9).
- No loosening of any existing gate threshold or leg before calibration (constraint 13).
- No re-run, re-score, or rescue of any closed thesis (chart-type, ICT, USTEC breaker, IFVG, state-descriptor) (C1).
- No verdict on any real trading idea this phase; the object is the referee.
- No access to or spend of the final 30% global market holdout.
- No scalar MDE; no power number reported without its synthetic-family conditioning.
- No treatment of the false-negative cost arm as measured rather than a declared prior (constraint 4).
- No reference to the `.ignore/projects/v01.zip` snapshot as an authority; the live retained artefacts are the source of record.

## Expected Phase Outcomes

One of the following is sufficient and useful:

1. **H1 supported (calibration is trustworthy for the tested family).** Power is stable across the diverse synthetic family; the stack's FPR and power surface are reported with quantified meaning, and the §5.6 ruling states where the stack sits (appropriately strict / too insensitive / mismatched). The programme earns the right to proceed to successor-gate design in a later phase.
2. **H0 supported (calibration is generator-dependent).** Power moves materially with the synthetic family; the phase reports no calibrated MDE as real, pivots to characterising and bounding the fidelity gap, and records that the §6 cure is not, as posed, trustworthy. A successful null result (C4).
3. **§5.6 ruling regardless of H1/H0.** Even where power is fragile, null calibration (trustworthy) still yields the FPR and per-leg leak/over-reject profile — enough to say whether the three closures were issued by an over-strict, appropriately strict, or blind stack, holdout intact.
4. **Near-impassable finding.** If the stack rejects even modest, well-formed planted effects, that conjunctive-stringency result (T2) is recorded as a finding — never as license to loosen gates (C3).

## Resolved Decisions Carried In (D0–D7, 2026-05-31)

From `state-and-open-decisions.md`; recorded here so the phase is self-contained:

1. **D0 — artefact retention intentional.** The prior EXP-001…036 tree, checkpoints, and code-reviews are retained (working tree clean at HEAD `947a6bd`), on two analysts' recommendation to reuse them. The `.ignore/projects/v01.zip` is a backup snapshot, not a seal.
2. **D1 — baseline referee = the §5.6 closure stack** (not the Phase-2 `proceed_criteria` signal-quality gate, which answers a different question).
3. **D2 — materialised by transcription from EXP-036** (accessible, not sealed); the earlier "predeclare-from-memory" fidelity tension is void.
4. **D3 — evidentiary thresholds are read facts** (floors 100/50 rows, 30/15 episodes; k = 2; 10k episode bootstrap; neutral-vs-`mu_mid`; naive momentum-sign control); only economic-materiality + proxy-cost regimes are newly drafted.
5. **D4 — numbering continues** at Phase 006 / EXP-037 (never reused; on-disk EXP-001…036 reinforce this).
6. **D5 — `python/INDEX.md` forward rewrite** to the qualification programme is scheduled with the checkpoint opening (still carries the old "Event-Based Price Aggregation Research" header).
7. **D6 — commit the refresh**: narrow `.gitignore` so the three `docs/planning/*.md` founding docs are tracked; the archive stays ignored.
8. **D7 — compute budget** fixed in Deliverable #2, anchored to EXP-036's actual harness cost.

## Immediate Next Step

Produce **Deliverable #2 — the predeclared reference-stack specification** (a pre-registration document in this checkpoint folder), comprising: (a) the EXP-036 evidentiary stack transcribed and frozen in two layers; (b) the four new constructs drafted for review — economic-materiality threshold + low/central/stress proxy-cost regimes, harness DoF + explicit stopping rule, frozen calibration battery + second-order holdout, and the compute budget; and (c) the predeclared null construction and synthetic-effect family. It then passes pre-execution governance **before** any `EXP-037` scope is created. No experiment code is written until that gate clears.

Two house-keeping items accompany the opening: rewrite `python/INDEX.md` to the qualification programme (D5), and commit the refresh with a narrowed `.gitignore` so the founding docs are tracked (D6).
