# Thesis Qualification System — Problem Statement

**Type:** Problem statement (not a design, specification, or rubric)
**Status:** Seed document for a new, separate project
**Scope:** Market-/strategy-agnostic. Deliberately free of any specific market, instrument set, indicator, dataset, or prior research programme.

---

## 0. Purpose and non-goals

This document states the *problem* of qualifying candidate trading theses and strategies: deciding which deserve scarce validation resources — held-out data, paper trading, capital — and which are rejected, under an honest accounting of both kinds of error.

It is **not**:

- a design or specification for a qualification system;
- a rubric, scoring function, or recommended set of gates;
- an endorsement of any particular validation methodology.

A concrete gate stack appears in §3 as a **specimen** — one internally coherent instantiation — purely to make the abstract failure modes in §4 tangible. Its specific choices are illustrative, not normative. The reader should assume every parameter and gate in that specimen could reasonably be designed differently.

The deliverable of the eventual project is a *referee*: a system that judges theses. This document defines what that referee must contend with, not how it should be built.

---

## 1. The core problem

A research process produces a stream of **candidate theses** — claims that some observable conditions the future behaviour of a market in an exploitable way. Theses are cheap to propose, expensive to validate honestly, and **most are false**. From finite historical data, the process must decide which candidates earn costly validation or capital, **without self-deception**.

The difficulty is structural, and the adversary is partly the analyst and partly the data:

- **Low signal-to-noise.** Genuine edges are small relative to the volatility of the outcome being predicted. The thing you are looking for is near the floor of what finite data can resolve.
- **Non-stationarity.** The data-generating process drifts across time and regime. Past behaviour is a biased, partial guide to future behaviour. There is no stable population to sample from.
- **Multiplicity.** Many theses are tested over the life of a research programme. Some will look good by chance. The more you search, the more spurious winners you manufacture.
- **Overfitting / data snooping.** Flexible search — over parameters, features, sub-samples, horizons — reliably discovers structure in noise. Researcher degrees of freedom are abundant and easy to exercise unconsciously.
- **Small effective samples.** After demanding statistical independence (de-correlating serially dependent observations, requiring distinct markets or regimes), the *effective* sample is far smaller than the raw row count, often by orders of magnitude.
- **Two-sided error costs.** A **false positive** wastes capital, attention, and credibility, and can compound into real losses. A **false negative** discards a real edge — and, at the scale of a programme, a systematically insensitive referee can make a sound research process look permanently barren while teaching nothing.

The qualification system is the referee that adjudicates these forces. Its own quality — how often it is right, and in which direction it errs — is a measurable property of the system. In practice it is almost always **unmeasured**, which is the central problem this document points at.

---

## 2. What a qualification system must do

These are desiderata any such system must either satisfy or *consciously* trade off. They are stated as requirements, not solutions.

- **D1 — Operationalise "edge."** Define what qualifies as an edge in terms that include both **statistical existence** and **economic materiality** net of realistic frictions. Statistical significance and tradability are different claims; a system must address both.
- **D2 — Control false discovery honestly** — both within a single evaluation and across the **cumulative search** the programme performs over its lifetime.
- **D3 — Quantify its own sensitivity.** Know the **minimum detectable effect (MDE)**. A "reject" verdict must be interpretable as *"no edge, or an edge below detectable magnitude X,"* with X known. A system that cannot state X cannot distinguish absence of edge from absence of power.
- **D4 — Preserve a protected final test.** Reserve some data or realisation that is never consumed during search, so the final estimate of a survivor is approximately unbiased.
- **D5 — Demand generalisation evidence.** Require that an edge persists outside the exact conditions it was discovered in — across time, regime, market, parameter neighbourhood, and execution assumptions.
- **D6 — Establish construct validity.** Ensure the measured outcome actually corresponds to what the thesis claims — the right horizon, the right outcome variable, the right baseline of comparison.
- **D7 — Enforce self-honesty.** Predeclaration of choices, prohibition of outcome-driven selection, and an auditable trail, so that researcher degrees of freedom cannot be exercised after seeing results.
- **D8 — Be calibrated.** The system's own error rates should be **measured**, not assumed. (See §6.)

These pull in opposite directions. D2, D4, D5, and D7 push toward **stringency**. D3 and D6 demand that the *cost* of that stringency be **measured**. A system that maximises the first group while ignoring the second becomes un-interpretable in the rejection direction — confident, disciplined, and unable to tell "nothing is there" from "I cannot see."

---

## 3. A reference specimen (one instantiation)

The following is **one** concrete gate stack, presented de-identified and solely as material for dissection. It is internally coherent and embodies several genuinely sound principles. It is shown so the failure modes in §4 are concrete, **not** as a model to copy. Read every choice below as "one defensible option among many."

**The specimen's structure:**

1. **Nested chronological split.** Order data by time. Carve off a final fraction as an **untouched reserve** that nothing in the search may inspect. Within the remainder, split again into train and test by time.
2. **Readiness gate (necessary precondition).** Before any outcome is measured, require predeclared **representation floors** — minimum counts of independent observations per state, in each segment. A candidate that cannot clear these is not outcome-tested.
3. **Outcome gate.** The candidate's state-conditioned, executable, direction-adjusted next-step return must beat **both** (a) its own **neutral baseline** state **and** (b) a **matched simple control** (a deliberately naive alternative predictor), with bootstrap confidence intervals on each difference excluding zero.
4. **Inference unit.** Resample **independent episodes / blocks**, not raw rows, because the conditioning states are serially dependent. Naive row-level inference is treated as diagnostic only.
5. **Replication requirement.** The same-signed effect must hold in **both** train and test, on at least **k of N distinct markets**, where the independence unit is the *market* — multiple horizons or parameter settings of the same market do not count as independent replication.
6. **Discipline constraints.** Full predeclaration of parameters, thresholds, and baselines; no selection on test-segment outcomes; one hypothesis per evaluation; a bounded complexity budget; and at most one predeclared secondary horizon that is explicitly **barred from producing a "pass."**

**What the specimen gets right** (worth carrying into any successor): the untouched reserve (D4), predeclaration and no-outcome-selection (D7), an honest serial-dependence-aware inference unit, an explicit baseline plus a matched control (a real attempt at D6), and a replication demand (D5). These are not the flaws. The flaws are what the specimen *omits to measure* and the *tensions it resolves silently*, dissected next.

---

## 4. Failure modes and design tensions

Each item generalises a concrete weakness into a tension that **any** qualification system must confront. For each: the mechanism, why it bites, and the open question it leaves.

### T1 — Unquantified operating characteristics (the meta-flaw)
The gates are declared but their **power and MDE are never computed**. Consequently a rejection is uninterpretable: "no edge" and "edge below an unknown detection floor" are indistinguishable outcomes of the same machinery. Every negative verdict inherits this ambiguity.
**Open question:** how does the system measure and report its own sensitivity, so that "reject" carries a quantified meaning?

### T2 — Conjunctive gating compounds false negatives
Each additional "must *also* pass" leg multiplies the probability of missing a real effect. A stack of individually reasonable gates can have brutally low *joint* power. The miss rate of the conjunction is rarely modelled even when each leg is justified in isolation.
**Open question:** should gates be conjunctive at all, or combined into a single calibrated decision statistic whose error rate is known?

### T3 — False-positive control via replication-breadth trades away power
Using "must replicate on ≥k distinct units" as the multiplicity control is a **blunt family-wise-error instrument**: it suppresses false positives by demanding broad replication, which simultaneously crushes the detection of narrow-but-real effects. Other multiplicity philosophies — false-discovery-rate control, hierarchical/partial pooling, a single pre-registered decisive test — have different and explicitly characterisable power profiles.
**Open question:** what multiplicity philosophy fits a *sequential, exploratory* research programme, and what does each cost in power?

### T4 — Statistical significance decoupled from economic materiality
Confidence intervals test "different from zero," not "larger than costs." This lets through effects that are statistically real but economically negligible, and rejects on statistical grounds rather than tradability. Neither pass nor fail is anchored to a **minimum economically meaningful effect** net of a frictions model.
**Open question:** what is the predeclared economic-materiality threshold, and how does a frictions model enter the gate in both directions?

### T5 — Construct validity of the outcome metric
The chosen outcome — its horizon, its variable, its baseline — can be **orthogonal to where the thesis's edge actually lives**. Forcing a single-step metric onto a multi-step phenomenon, or a directional metric onto a risk-/timing-/sizing phenomenon, guarantees a null result regardless of truth. The most *executable* or most *conservative* metric is often the least *powered* for the specific claim, and "most conservative" can quietly become "structurally unable to detect the claimed mechanism."
**Open question:** how is the measured outcome shown to align with the thesis's claimed mechanism *before* testing?

### T6 — Standalone-superiority vs. incremental information
A "must beat control X on its own" gate rejects candidates that carry **real incremental information** overlapping with X but valuable in combination, sizing, or an ensemble. "Beats the naive alternative standalone" and "adds information beyond the naive alternative" are different questions; a standalone gate only asks the first.
**Open question:** is the unit of qualification a standalone signal, or a marginal contribution to an existing model?

### T7 — The independence assumption in replication
Treating N "distinct" units as independent **overstates** confirmation when they share drivers (a pass can ride a common confound across correlated units) and **understates** power (you do not actually have N independent attempts). Cross-unit correlation is asserted away rather than modelled.
**Open question:** how is the dependence structure across replication units estimated and folded into the evidence calculus?

### T8 — Universality vs. specificity prior
Demanding broad replication encodes a strong prior that **real edges are universal**. Genuine regime- or market-specific edges are then recorded as failures, even though specificity can itself be signal (markets and regimes really do differ).
**Open question:** when is heterogeneity across units evidence against an edge, and when is it the edge?

### T9 — Readiness is not informativeness
Heavy machinery to prove a candidate is *measurable / eligible* tells you nothing about whether it carries edge, yet can dominate effort and attention. A necessary precondition can masquerade as progress.
**Open question:** what is the right effort allocation between eligibility checks and edge measurement?

### T10 — Programme-level selection and the file drawer
Per-evaluation predeclaration is clean, but the **cumulative search across many theses is itself a giant multiple-comparisons machine**. Without programme-level accounting (a registry of everything tried, including abandoned ideas), the eventual analysis-set "winner" that triggers a final-reserve spend is uncorrected for the full search that preceded it. A protected final reserve mitigates but does not eliminate this inflation.
**Open question:** how is the cumulative search tracked and corrected so the survivor's evidence reflects everything tried, not just the last evaluation?

### T11 — Non-stationarity and the choice of temporal split
A single chronological split tests **one regime ordering**. A candidate can pass or fail depending on where the cut lands. Walk-forward, regime-stratified, and combinatorial purged cross-validation give different — and differently biased — answers. The split design is itself a researcher degree of freedom that the rubric usually fixes silently.
**Open question:** what validation protocol best reflects the non-stationarity the strategy will face live, and how is that protocol's bias characterised?

### T12 — Binary verdicts discard information
Collapsing graded evidence into pass/reject throws away the **effect-size and uncertainty** that should govern *how much* to advance a candidate — the size of a follow-up, a posterior for a Bayesian update, a ranking against alternatives — rather than a hard yes/no.
**Open question:** should the system output a binary gate, a graded posterior, or an expected-value ranking?

---

## 5. The system encodes a loss function — usually implicitly

Every gate stack silently encodes a **loss function** over false-positive cost, false-negative cost, and validation budget. The specimen in §3 implicitly sets false-positive cost far above false-negative cost — a reasonable stance when capital is at risk — but **never states it**, and therefore never checks that its stringency actually matches it.

A successor system should make this loss **explicit and tunable**: stringency should be a chosen consequence of a stated error-cost trade-off, not an emergent property of stacking individually conservative gates. Two organisations with different costs of missing an edge should be able to instantiate the same framework at different operating points.

---

## 6. Meta-requirement: the system must be calibratable

Before any rubric is trusted, it must be possible to **test the tester**. Feed the system:

- **known-positive inputs** — planted or synthetic effects of *known* magnitude and structure; and
- **known-null inputs** — data constructed to contain no edge;

and measure the system's true-positive, false-positive, true-negative, and false-negative rates, its **empirical MDE**, and the pass rate of each individual gate leg.

This is not an optional diagnostic. A rubric whose operating characteristics are unknown **cannot distinguish "the world contains no edge" from "the rubric cannot see edge."** Calibration capability should be a first-class component of the system, designed in from the start and re-run whenever the rubric or the data regime changes. The ability to answer *"what would this system do with a real edge of size X?"* is what converts a negative result from a philosophical claim into a measured one.

---

## 7. Open design space (deliberately unresolved)

The successor project must decide the following. They are posed as questions to avoid prescribing answers here:

- **Unit of qualification** — a standalone signal, a marginal contribution to an existing model, or a complete strategy with sizing and execution?
- **Definition of edge** — pure statistical, economic net-of-cost, risk-adjusted, capacity-aware, or some composite?
- **Multiplicity philosophy** — family-wise error, false-discovery-rate, Bayesian, sequential testing, or a hybrid?
- **Validation protocol** — single chronological holdout, walk-forward, combinatorial purged cross-validation, live paper trading, or layered combinations?
- **Non-stationarity handling** — how is regime drift represented, stress-tested, and tolerated?
- **Decision output** — a binary gate, a graded posterior, or an expected-value ranking that feeds position/effort sizing?
- **Loss function** — how is the error-cost trade-off stated, exposed, and tuned per operating context?
- **Programme-level honesty** — how is the cumulative search registered and corrected (registry, file-drawer accounting, pre-registration discipline)?
- **Self-calibration** — how is the system itself validated, reported, and periodically re-calibrated?

---

## 8. Summary

The problem is **not** "design better gates." It is to build a **referee whose own error profile is known and whose stringency is matched to an explicit loss function**, operating over a sequential search in low-signal, non-stationary data, while resisting self-deception.

The specimen in §3 demonstrates the trap: a disciplined, well-intentioned, internally coherent gate stack can still be **un-interpretable in the rejection direction** if it never measures its own sensitivity. The principles worth carrying forward — predeclaration, an untouched reserve, an honest inference unit, explicit baselines and controls — are necessary but not sufficient. The thing left unsolved, and the reason this problem deserves its own project, is **measured stringency**: knowing what the referee can and cannot see before trusting what it says.
