# Scope Design Reference

Guidance for formulating rigorous experiment scopes during Stage 1 of the research pipeline.

---

## Writing Good Hypotheses

### Structure

A testable hypothesis follows this pattern:
**[Feature/Metric A] has a [specific relationship] with [Feature/Metric B] under [conditions].**

### Examples by Research Area

#### Structure Label Transition (HH/HL/LH/LL)
- "The empirical transition probability P(HH | HL, Regime=Low) is significantly different from P(HH | HL, Regime=High), indicating regime-dependent structure dynamics."
- "Sequences with `ValidationStatus == 'Valid'` show different transition patterns than sequences including artifacts."

#### Bar Feature Patterns
- "High `ConfirmationStrength` (> 90th percentile) is followed by `BarReturn` of opposite sign more than 55% of the time within the next 3 bars."
- "`TickDensity` exhibits clustering: high-tick-density pivots are more likely to be followed by high-tick-density pivots than expected by chance."

#### Cross-Representation Validation
- "`ValidationStatus == 'Valid'` pivots show stronger label transition consistency than `ValidationStatus == 'Artifact'` pivots."

#### Regime-Conditioned Patterns
- "The distribution of `Label` transitions differs significantly between `ContextRegime=Low` and `ContextRegime=High` volatility periods."
- "`ImbalanceFlag` has predictive value for next-pivot `Label` in `Regime=High` but not in `Regime=Low`."

#### Sequential Dependencies
- "The `SequenceContext` (last 3 labels) predicts the next `Label` with accuracy significantly above random (25% for 4-class problem)."
- "`Slope` between consecutive pivots is autocorrelated: high-magnitude slopes tend to be followed by high-magnitude slopes."

### Hypotheses vs Exploratory Questions

Some experiments are exploratory — they don't test a hypothesis but characterise data. The question must still be specific:

**Good**: "What is the empirical joint distribution of `BarRange` and `VolatilityProxy` for valid EURUSD pivots in low-volatility regimes?"

**Bad**: "What patterns exist in the pivot data?"

---

## Complexity Budget Guidelines

| Experiment Type | Stat Tests | Visualisations | Code Modules |
|----------------|-----------|----------------|-------------|
| Descriptive / EDA | 0 | 2–4 | 0–1 |
| Single hypothesis test | 1–2 | 2–3 | 1 |
| Comparative (across regimes/instruments) | 2–4 | 3–5 | 1–2 |
| Multi-feature relationship | 2–3 | 3–5 | 1–2 |
| Sequence/transition analysis | 2–4 | 3–5 | 1–2 |

If an experiment needs more than these limits, **split it into multiple experiments**.

---

## Scope Boundary Patterns

### Feature Category Patterns

TriLattice features are organized into 5 categories:

- **Single feature from one category**: "`BarReturn` distribution" — simplest, best for initial exploration
- **Pairwise relationship within category**: "`BarRange` vs `VolatilityProxy`" — volatility relationship testing
- **Cross-category relationship**: "`ConfirmationStrength` vs next-pivot `BarReturn`" — predictive hypothesis
- **Sequential/transition analysis**: "`Label` N vs `Label` N+1" — structure dynamics
- **Regime-stratified**: Same analysis repeated for Low/Medium/High regimes — regime dependence testing

### Common Exclusions

Always consider excluding:
- `ValidationStatus == 'Artifact'` pivots unless explicitly studying validation failure modes
- `IsAmbiguous == true` pivots unless studying ambiguous structure
- `IsTrainingTarget == false` pivots for model training (these are time-triggered low-confidence)
- Pivots from the first/last N confirmations (warm-up / termination effects)
- Specific sessions or time periods with known anomalies
- The final 30% global holdout (always — non-negotiable)

---

## Success Criteria Patterns

### Good Criteria (concrete, measurable)

- "Evidence FOR: Spearman correlation between `ConfirmationStrength` and next-pivot `BarReturn` is > 0.15 with p < 0.05 (bootstrap)"
- "Evidence FOR: Transition prediction accuracy exceeds 35% (vs. 25% random baseline) with p < 0.01"
- "Evidence AGAINST: Effect size is < 0.05 or not statistically distinguishable from zero"
- "Inconclusive: Effect size is between 0.05 and 0.15, or significance is borderline (0.05 < p < 0.10)"

### Bad Criteria (vague, subjective)

- "Evidence FOR: There seems to be a relationship"
- "Evidence AGAINST: No clear pattern"

---

## Scope Splitting Rules

Each experiment answers **exactly one question**. If the user's idea naturally contains multiple questions, propose splitting:

| User's Broad Idea | Proposed Split |
|------------------|----------------|
| "Does confirmation strength predict reversal?" | EXP 1: "Does `ConfirmationStrength` predict next-pivot direction?" EXP 2: "Does `ConfirmationStrength` predict next-pivot magnitude?" |
| "What patterns exist in label transitions?" | EXP 1: "What is the empirical transition matrix P(Label_t | Label_t-1)?" EXP 2: "Does the transition matrix differ by `Regime`?" |
| "Can we predict next pivot label?" | EXP 1: "Can `SequenceContext` predict next `Label`?" EXP 2: "Can bar features predict next `Label`?" |

---

## Ideas Registry Mapping

When the user proposes an idea, consider how it maps to TriLattice capabilities:

| Idea | Possible Experiments |
|------|---------------------|
| Structure transition dynamics | "Do HH/HL/LH/LL labels show non-random transition patterns?" |
| Regime-conditioned patterns | "Are transition probabilities stable across volatility regimes?" |
| Cross-validation impact | "Do Valid vs Artifact pivots show different statistical properties?" |
| Bar feature predictiveness | "Can bar features (return, range, duration) predict next pivot characteristics?" |
| Imbalance signal value | "Does `ImbalanceFlag` predict structural breaks?" |
| Sequence memory | "Does `SequenceContext` (last 3 labels) improve next-label prediction?" |
| Session effects | "Do transition patterns differ across trading sessions (Asian/European/NY)?" |
| Confirmation quality | "Do price-triggered high-confidence pivots differ from time-triggered low-confidence?" |

If the user proposes an idea not covered above, note it and suggest adding it to future phase designs.

---

## Connecting to Checkpoints and Phase Design

**Primary source**: The latest checkpoint's `design.md` in `docs/experiments-docs/checkpoints/` — the authoritative guide for current phase experimentation. Scope experiments listed there first.

**Secondary source**: The previous phase's `retrospective.md`. If it contains "Recommended Next Experiments" or identified gaps, scope those next.

**Tertiary source**: `docs/references/architecture.md` — the architecture document may contain open research questions or validation needs for specific components (Stream A vs B vs C behavior, parameter sensitivity, etc.).

**Phase progression**: When a phase's experiments are complete, write the `retrospective.md` and, if proceeding, create the next phase's `design.md` before starting new experiments.
