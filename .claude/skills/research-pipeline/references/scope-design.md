# Scope Design Reference

Guidance for formulating rigorous experiment scopes during Stage 1 of the Xen research pipeline.

This reference is thesis-neutral. Every research thesis — chart-type studies, time-bar-native signal studies, price-action studies, and others — uses the same scoping discipline: one falsifiable question, explicit data views, fixed parameters, chronological holdout protection, and predeclared interpretation criteria.

---

## Writing Good Hypotheses

A testable hypothesis follows this pattern:

**[Feature or event definition] has a [specific relationship] with [metric] under [conditions], compared to [baseline/control].**

Examples:

- "Predefined intraday session windows have higher 20-minute realized range than adjacent same-day control windows on at least 3 of 4 available instruments, with bootstrap confidence intervals excluding zero."
- "Bars closing beyond the prior-day high have lower 60-minute forward return than a matched control set, measured on real time-bar prices."
- "Adding one deterministic confirmation filter to an event definition improves median adverse excursion by at least 0.25 ATR without reducing sample size below the predeclared minimum."
- "Line Break level 3 produces fewer ghost bars than 1-minute time bars on at least 3 of 4 instruments." Use examples like this only when chart types are explicitly in scope.

Some experiments are exploratory. The question must still be specific:

**Good:** "What fraction of available USTEC 1-minute bars fall inside a predefined intraday session window after timezone conversion, and what missing-bar rate exists inside those windows?"

**Bad:** "What patterns exist in the data?"

---

## Complexity Budget Guidelines

| Experiment Type | Stat Tests | Visualisations | Code Modules |
|----------------|-----------|----------------|-------------|
| Data readiness / EDA | 0-1 | 2-4 | 0-1 |
| Single hypothesis test | 1-2 | 2-3 | 1 |
| Event study | 1-3 | 3-5 | 1-2 |
| Multi-feature relationship | 2-3 | 3-5 | 1-2 |
| Cross-view alignment | 2-4 | 3-5 | 1-2 |

If an experiment needs more than these limits, split it into multiple experiments.

---

## Scope Boundary Patterns

### Time-Bar-Native Patterns

- **Data readiness:** "Can the available time bars support this thesis after timezone, session, and missing-bar checks?"
- **Window characterization:** "Do predefined windows differ from adjacent or randomized control windows?"
- **Event study:** "What happens after a deterministic event definition such as a breakout beyond a prior extreme?"
- **Component ablation:** "Does adding exactly one filter improve the predeclared metric enough to justify the lower sample count?"
- **Exit/risk validation:** "Does a target or stop rule produce a better distribution than simpler alternatives?"

### Optional Chart-Type Patterns

Use these only when the active checkpoint or approved scope explicitly includes chart types:

- **Single chart type vs baseline:** "Line Break bars produce fewer ghost bars than time bars."
- **Multi-chart-type comparison:** "Information density ranking across Time, Renko, and Line Break."
- **Timeframe-as-hyperparameter:** Same chart-type comparison on 1m, 15m, and 1h source bars.

---

## Common Exclusions

Always consider excluding:

- The final 30% global holdout.
- Any feature, filter, or threshold not named in the scope.
- Any data unavailable in the repository, such as bid/ask spread or tick data, unless a defensible proxy is explicitly scoped.
- Any use of data after the event timestamp for signal construction.
- Parameter tuning against analysis-set outcomes.
- Bar-index alignment across data views.

For chart-type scopes, also exclude:

- Heiken Ashi HA prices from strategy/P&L/signal-return calculations unless the scope is explicitly a non-tradable distortion diagnostic.
- Renko brick prices from strategy P&L.
- Silent handling of repeated `SourceCloseTime` rows.

---

## Decomposing a Broad Thesis

A broad, multi-component thesis (a full discretionary "setup", or a strategy with several stacked rules) is too broad for a single experiment. Split it into prerequisites and one-component-at-a-time additions:

1. **Data readiness:** timezone/session coverage, missing bars, instrument fit, and cost/spread availability or proxy assumptions.
2. **Context windows:** compare any fixed time-of-day or session windows against adjacent and randomized controls.
3. **Base events:** test the simplest deterministic event definition (e.g. a level breach) before more elaborate ones.
4. **Confirmation filters:** add exactly one deterministic filter to a base event at a time.
5. **Composite definitions:** introduce one additional component only after the prior one shows evidence.
6. **Risk/target:** compare fixed targets/stops only after entry logic has evidence.
7. **Full model:** only after components survive ablation.

Do not begin with a full strategy backtest. A full model has too many degrees of freedom and will blur which component, if any, carries evidence.

---

## Success Criteria Patterns

Good criteria:

- "Evidence FOR: Session windows show higher median range than controls on at least 3 instruments, with bootstrap CI for median difference above zero and minimum effect size >= 0.10 ATR."
- "Evidence AGAINST: The scoped event has no positive expectancy advantage over matched controls after costs, or sample size falls below the minimum event count."
- "Inconclusive: Effect direction is mixed across instruments, confidence intervals overlap zero, or event count is below the predeclared threshold."

Bad criteria:

- "Evidence FOR: The setup looks clean."
- "Evidence AGAINST: No clear pattern."

---

## Connecting to Checkpoints and Phase Design

**Primary source**: The latest active checkpoint's `design.md` in `docs/experiments-docs/checkpoints/` is the authoritative guide for current phase experimentation.

**Secondary source**: The previous phase's `retrospective.md` supplies lessons and redirect decisions. It does not automatically authorize inheritance of old hypotheses or infrastructure.

**Tertiary source**: `docs/references/architecture.md` and `docs/references/dataset-reference.md` provide architecture and data constraints.

When a phase's experiments are complete, write the `retrospective.md` and, if proceeding, create the next phase's `design.md` before starting new experiments.
