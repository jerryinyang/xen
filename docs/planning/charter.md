# Founding Charter — Thesis-Qualification Programme

**Type:** Programme charter / founding design (the analogue of a phase `design.md`)
**Status:** Draft for approval — founding document of Xen's refreshed research direction
**Companion:** [`thesis-qualification-system-problem-statement.md`](thesis-qualification-system-problem-statement.md) (the seed; the *what must be contended with*)
**Date:** 2026-05-30

This charter turns the problem statement into a *programme*: an object of study, a falsifiable founding thesis, a founding experiment, and the constraints under which all of it operates. It is deliberately committal where the problem statement was deliberately agnostic — the problem statement argues that *measured stringency* is the missing primitive; this charter accepts that argument as the working hypothesis and sets out to test it before building anything on top of it.

The prior Xen theses (chart-type validation, signal-quality, ICT, HTF state-descriptors) are closed and archived, and stay closed. But the **gate stack that judged them is retained in `python/src` as the baseline referee under test** — because the founding experiment calibrates *that* stack first (see §4). The object of study is now the *referee*, not any single market thesis.

---

## 1. Object of study

The **referee**, not any market thesis. This programme produces (a) a qualification system that judges candidate theses, and (b) — first and inseparably — the **measurement apparatus that makes its verdicts interpretable**. A gate stack without a measured error profile is out of scope by definition; it is the thing the programme exists to replace.

The unit of progress is a *measured property of the referee*, not a verdict on a trading idea.

**System boundary.** The qualification system is more than its gate stack. It comprises: (i) a *thesis registry* — every candidate tried, including abandoned ones (the T10 file-drawer ledger); (ii) a *data protocol* — splits, holdout, admissibility; (iii) the *gate stack* — the evidentiary rules under test; (iv) a *cost model* — frictions / economic-materiality floor; (v) a *decision policy* — what a verdict triggers; and (vi) a *human workflow* — predeclaration, audit, governance. Calibration in this charter targets the gate stack's evidentiary layer; the other five components are named so they are not silently conflated with it.

Theses to come still ride on the chart-type architecture (time bars primarily; Line Break, Renko, Heiken Ashi available). Chart generation remains shared, agnostic infrastructure and is not part of what this programme puts on trial.

---

## 2. Founding thesis (falsifiable)

> **H1.** A qualification system's operating characteristics — false-positive rate, a power *surface*, and per-leg pass rates — can be measured with enough fidelity that its verdicts (especially **"reject"**) carry a quantified, trustworthy meaning.

> **Null (H0).** They cannot. The power estimate is so sensitive to the choice of synthetic effect-generator that an "empirical minimum detectable effect" is merely relocated guesswork — the calibrator itself needs calibrating, and its fidelity is unfalsifiable.

This is the right *first* question. The problem statement's §6 proposes calibration as the cure for un-interpretable rejections. But calibration only measures the referee with respect to the synthetic data-generating process used to plant effects, and the structure of real edges is exactly what is unknown. If H0 holds, the entire §6 program is built on sand — and the programme must discover that **before** designing gates around it. We refuse to assume the cure works.

**Decision rule (predeclared):**
- If the power estimate is **stable** across a deliberately diverse family of planted structures → H1 is supported for that family; calibration earns provisional trust and the programme proceeds to gate design.
- If the power estimate **moves materially** with the synthetic family → H0 is supported; priority shifts from "design gates" to "characterise and bound the fidelity gap," and no calibrated MDE is reported as if it were real.

---

## 3. Two species of calibration (kept separate — this is load-bearing)

The problem statement merges these under one "calibration" banner. This programme splits them permanently, because they have opposite epistemic status:

| | **Null calibration** | **Power / MDE calibration** |
|---|---|---|
| Measures | FPR, per-leg false-pass rate | TPR, detectable-effect surface |
| Needs a model of "a real edge"? | **No** | **Yes** — the thing we don't have |
| Method | Dependence-preserving resampling of the **real** series (circular-block / stationary bootstrap; multivariate / sieve for cross-series) that breaks the conditioning relationship while preserving serial dependence, volatility clustering, calendar structure, and cross-market correlation. Naive shuffles are diagnostic-only | Plant synthetic effects of known magnitude/structure into real or surrogate series |
| Epistemic status | **Trustworthy** — conclusions may be staked on it | **Fragile** — assumption-laden; conditional on the synthetic family |

Conclusions are weighted by which species produced them. A claim resting on power calibration always carries its synthetic-family conditioning explicitly.

**Null realism is a validity requirement, not a detail.** A null that destroys volatility clustering, serial dependence, calendar effects, or cross-market correlation manufactures noise that looks tradeable and makes the FPR estimate optimistic. The null construction is predeclared and its preserved/destroyed structure documented — because the trustworthiness of the "trustworthy" half is exactly the realism of the null.

---

## 4. Founding experiment (EXP-001): calibrate the existing Xen stack as the baseline referee

The first object measured is the **existing Xen gate stack** (representation floors + neutral-baseline + matched-control superiority + train/test sign preservation on ≥k instruments + predeclaration — the §3 specimen, instantiated in `python/src`). This is a deliberate reversal of an earlier plan to start from a freshly designed stack: two independent reviews converged on calibrating the *current* stack first, because it is the only thing that **answers Xen §5.6** — were the three closures sound, or was the stack blind to a modest real edge? — at near-zero marginal cost, since the harness must be built regardless. Throughout this charter, "the reference stack" therefore means the existing Xen stack for the founding experiment.

Design of a *successor* stack is **deferred** until the calibration ruling is in (§9), and is to be informed by where the existing stack actually sits — appropriately strict, too insensitive, or mismatched to the kind of edge worth finding. No gate threshold is loosened before that measurement (constraint 13).

**Part A — Null calibration (trustworthy).**
Resample a real series (block / stationary bootstrap + permutation) to break the candidate's conditioning relationship while preserving dependence structure. Run the full reference stack against thousands of such nulls. Report:
- the stack's empirical FPR at its declared thresholds, and
- the false-pass rate of **each individual gate leg** (which legs leak, which over-reject).

**Part B — Power bracketing (fragile, explicitly caveated).**
Plant synthetic edges across a **deliberately diverse family** spanning both *parameters* (horizon, regime location, magnitude, persistence, cross-unit correlation) and — crucially — *edge mechanisms*: directional drift, volatility/risk filtering, timing improvement, sizing information, and marginal contribution to an existing model. Varying mechanism, not just magnitude of a single directional effect, is what exposes whether a stack is structurally blind to a whole *kind* of edge (e.g. a directional-return gate that cannot see a sizing or timing edge). Run the stack against each. The headline deliverable is **not "the MDE."** It is:
- the **sensitivity of the apparent MDE to the synthetic family** — the direct empirical test of H0/§2; and
- a **power surface** conditioned on (effect structure × regime × replication breadth × horizon), never a scalar.

**Why this design answers the founding thesis directly:** Part B's sensitivity result *is* the test of H0. A large sensitivity is not a nuisance to be averaged away — it is the finding.

---

## 5. Binding constraints (the problem statement's failure modes, promoted to rules)

Each constraint below traces to a critique of the problem statement and exists to stop the successor system from re-committing the error.

1. **Null vs power calibration are never merged** (§3). Every reported error rate is tagged with its species and, for power, its synthetic-family conditioning.
2. **No scalar MDE.** Sensitivity (D3/T1) is reported as a conditioned power *surface or function*. "State X" language is banned; X is high-dimensional and regime-dependent.
3. **The §6 ↔ T10 ↔ D4 trilemma is a hard constraint, not three independent questions.** Re-calibration frequency (§6 wants it often), cumulative-search accounting (T10 charges every look against a shrinking budget), and the single protected reserve (D4, spendable once) are mutually limiting. The programme picks an explicit operating point and states what it sacrifices; it does not pretend to maximise all three.
4. **The loss function's false-negative arm is a declared prior, not a measurement** (§5). FN cost is unknowable at rejection time (the discarded edge's size/existence is unknown). It is labelled non-empirical wherever it appears; "tunable" never implies "measured" on that arm.
5. **Alpha decay is a first-class failure mode** (omission in the problem statement). The reference stack must address post-discovery temporal decay — an edge real at validation and gone at deployment. Gate sensitivity analysis includes a decay axis.
6. **The calibration harness has a bounded, stated compute budget** (omission). The cure must be affordable relative to the programme it referees; a calibration regime more expensive than the research it governs is a design failure to be flagged, not absorbed.
7. **The harness's own degrees of freedom are predeclared and audited** (referee-of-the-referee). Synthetic generator, planted effect sizes, and null construction are researcher DoF under the problem statement's own logic (D7). They are pre-registered, and the regress has an **explicit stopping rule** stated up front.
8. **Construct validity vs predeclaration tension is named** (T5 vs D7). Aligning the outcome metric to the thesis mechanism "before testing" is itself a fork in the garden of forking paths. The mechanism for constraining metric choice (so D6 does not become a predeclared-but-still-chosen escape hatch) is an explicit design item, not an assumed harmony.
9. **Admissibility constraints are separated from evidentiary rules — and only the latter are calibrated.** *Admissibility constraints* (no look-ahead, no holdout contamination, real-price P&L, timestamp alignment, predeclaration) are hard validity preconditions: they are never softened into a score, have no operating characteristics to tune, and calibrating them is a category error. *Evidentiary rules* (replication breadth, CI-exclusion, matched-control superiority, the detectable-effect threshold, pass/reject cutoffs) are the objects whose error profiles are measured and tuned. The reference stack is specified in these two layers explicitly; calibration holds the admissibility layer fixed while varying the evidentiary layer.
10. **The referee must not overfit its own calibration suite.** A gate stack tuned until it scores well on a known battery is overfit at the meta level — the same disease, one floor up. The calibration battery is **versioned and frozen**, and a **second-order holdout** (calibration cases never seen during referee design) gives the referee its own untouched reserve. Operating characteristics drawn from the tuning battery are labelled in-sample; trust attaches only to the second-order holdout.
11. **Economic materiality is a first-class threshold, not a by-product of CI-exclusion** (T4). A pass requires clearing a predeclared minimum economically meaningful effect *net of a frictions model* — not merely "different from zero." Because the current data lacks true spread/slippage fields, the frictions model is expressed as **explicit, predeclared proxy-cost regimes** (e.g. low / central / stress), and survival is reported per regime, never under a single hidden cost assumption.
12. **The output is a decision ladder, not a binary verdict** (T12). A candidate resolves to one of: *reject*, *redesign the construct*, *gather more data*, *paper-trade*, *spend a slice of the protected reserve*, or *allocate capital* — graded by effect size and uncertainty. The rungs that consume scarce resources (holdout, capital) are gated by the programme-level cumulative-search correction (T10), so the ladder cannot become a way to nibble the reserve.
13. **Do not loosen the current gates before calibration.** Thresholds and gate legs are *measured first* and changed only on the evidence of that measurement. A gate is never softened because theses keep failing it; relaxation that precedes calibration is indistinguishable from rescuing a false positive.

---

## 6. Honesty clauses (predeclared, non-negotiable)

- **C1 — Answer §5.6; do not rescue theses.** The founding experiment deliberately calibrates the *existing* Xen stack to answer §5.6 (were the three closures sound, or gate-blind?). It measures the **referee only**: the closed theses stay closed and are not re-run, re-scored, or rescued. If the old stack proves insensitive, that finding changes the *referee* — after which any thesis, old or new, must re-qualify from scratch through the corrected stack. A "the gate was blind" result is never a back-door reinstatement of a prior candidate. *(This supersedes the earlier C1, which left §5.6 deliberately unanswered; that stance was reversed when the existing stack became the baseline-under-test.)*
- **C2 — The flattering hypothesis is held under suspicion.** This direction was born from a hypothesis (the referee may be blind) that is more comfortable than its alternative (the ideas were false). That asymmetry is acknowledged. The founding experiment is structured so the *uncomfortable* outcome is a first-class, reportable result, not an afterthought.
- **C3 — "Near-impassable" is a finding, not a license.** If the reference stack proves near-impassable even at modest planted effects, that is a recorded finding about conjunctive stringency (T2). It is **not** grounds to keep loosening gates until something passes — that path manufactures false positives and is the exact self-deception the problem statement warns against.
- **C4 — H0 is allowed to win.** If power estimates prove unstable across synthetic families, the programme says so plainly and does not report a calibrated MDE as if it were trustworthy. A null result on the founding thesis is a successful outcome.

---

## 7. Open design space carried forward (deliberately unresolved here)

These remain open from problem statement §7 and are scheduled for design *after* the founding experiment reports, because their right answers depend on whether calibration is trustworthy (§2):

- Unit of qualification (standalone signal / marginal contribution / complete strategy).
- Definition of edge (statistical / economic-net-of-cost / risk-adjusted / capacity-aware / composite).
- Multiplicity philosophy (FWER / FDR / Bayesian / sequential / hybrid) — and its power cost (T3).
- Validation protocol (single holdout / walk-forward / combinatorial purged CV / paper / layered) and its characterised bias (T11).
- Standalone-superiority vs incremental-information as the qualification unit (T6).
- Cross-unit dependence in replication, estimated and folded into the evidence calculus (T7).
- Universality-vs-specificity prior: when is heterogeneity evidence against an edge, and when is it the edge (T8)?
- Decision output: binary gate / graded posterior / expected-value ranking (T12).
- The trilemma operating point (constraint 3) made concrete.

---

## 8. Scope boundaries

- **In scope:** the referee and its measurement; the **existing Xen stack as the baseline referee under test**; its two-part calibration; characterisation of calibration fidelity; the §5.6 ruling.
- **Out of scope (for the founding experiment):** designing the *successor / final* production gate stack (deferred to post-calibration); loosening any existing gate threshold before calibration (constraint 13); any verdict on, or re-run of, a real trading thesis; spending any protected reserve.
- **Architecture, not under trial:** the chart-type generators (time bars, Line Break, Renko, Heiken Ashi) and aggregation/alignment helpers remain shared infrastructure. Theses ride on them; the referee does not judge them.

---

## 9. Founding deliverables

1. This charter (approved).
2. A predeclared specification of the **existing Xen stack as the baseline referee**, transcribed **in two layers** — admissibility constraints vs evidentiary rules (constraint 9) — with its gates, thresholds, baselines, inference unit made explicit, plus the proxy-cost regimes (constraint 11), constraint 7's harness DoF, and a **frozen calibration battery + reserved second-order holdout** (constraint 10) all pre-registered.
3. EXP-001 calibration: Part A (null → FPR + per-leg leak/over-reject) and Part B (power surface + synthetic-family sensitivity = the H0/H1 verdict), run against the existing stack.
4. A written **§5.6 ruling** plus the founding-thesis ruling (§2 decision rule): is the existing stack appropriately strict, too insensitive, or mismatched to the kind of edge worth finding — and is the calibration itself trustworthy (H1) or generator-dependent (H0)?
5. *Deferred / conditional:* a successor reference-stack design, undertaken **only after** the §5.6 ruling and informed by it — never before, and never as a way to relax a gate that theses kept failing (constraint 13).
