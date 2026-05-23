# Phase 003 Design: ICT One Setup Time-Bar Validation

**Phase:** 003 - ICT One Setup Time-Bar Validation  
**Date:** 2026-05-23  
**Status:** Active  
**Predecessor:** 2026-05-16-001-signal-quality-classification  
**Planning spec:** [ict_one_setup_research_spec.md](../../../planning/ict_one_setup_research_spec.md)

## Decision Status

The event-chart signal-quality thesis is closed. This phase does not inherit event-chart hypotheses, chart-type roles, generated chart infrastructure, or prior signal-quality conclusions, except for one architectural fact: time bars remain the canonical real-price timeline.

The new thesis asks whether an objective version of the ICT-style "macro + sweep + displacement + IFVG/breaker" setup can be translated into deterministic, falsifiable, time-bar-native experiments.

## Phase Objective

Convert the discretionary ICT setup into objective components and test them in sequence. The phase starts with data readiness and component behavior, not full strategy backtesting.

The core research question is the organizing question, not a narrowing filter:

> Does a time-filtered failed-breakout model, confirmed by displacement and objective structure failure, produce evidence of robust post-signal edge after realistic constraints?

This checkpoint is exploratory at the component level. It should plan enough experiments to evaluate the primary ICT hypotheses from the planning spec individually:

- H1: macro-window behavior;
- H2: liquidity-sweep reversal behavior;
- H3: displacement confirmation;
- H4: FVG/IFVG timing;
- H5: breaker confirmation;
- H6: fixed 1:2 risk/reward.

Each experiment still answers one falsifiable question. The phase should not collapse all ICT concepts into one full-model test, and it should not let a negative early component erase the need to characterize later components. Negative component results change interpretation and priority; they do not justify post-hoc deletion of planned source-spec hypotheses.

## Data Scope

Primary data view:

- 1-minute time bars from `data/timebars/`.

Initial available instruments remain constrained by the current repository data reference:

- EURUSD
- XAUUSD
- BTCUSD
- USTEC

The ICT spec's preferred instruments and data requirements are not assumed available. NQ, ES, GBPUSD, BTC perpetuals, tick or 1-second data, bid/ask spread, exchange calendars, and commission/slippage inputs require explicit data-readiness verification before they can be used.

## Non-Inheritance Rules

This phase must not reuse the prior thesis as evidence for the ICT model.

- No Line Break, Renko, or Heiken Ashi features unless a future scope explicitly adds them as a new, justified diagnostic.
- No event-chart coverage, precision, or FE/AE role carries forward as a hypothesis.
- No chart-type parameter search.
- No claim that prior event-chart findings support ICT concepts.

Reusable infrastructure is limited to:

- Time-bar loading and chronological slicing.
- Global holdout exclusion.
- Train/test split inside the analysis set.
- Generic plotting, reporting, audit, and governance discipline.
- Generic statistical methods that fit the scoped question.

## Phase Gates

1. **Data readiness gate:** Verify timestamp coverage, NY-time conversion feasibility, active-session definitions, missing-bar behavior, and spread/slippage availability or defensible assumptions.
2. **Definition gate:** Translate one ICT primitive at a time into deterministic code: macro window, liquidity level, sweep, displacement, FVG/IFVG, breaker, risk, and target.
3. **Component characterization gate:** Test each primary ICT component on its own or against the simplest relevant baseline before treating it as part of a compound model.
4. **Ablation gate:** Add one component at a time and measure whether it improves the relevant metric after sample-size and coverage costs. A component can be documented as weak, neutral, or harmful without stopping the whole exploratory phase.
5. **Full-model gate:** Attempt full strategy backtesting only after data readiness is approved, deterministic definitions exist, and the component studies identify which variants are eligible for a combined model.

## Planned Experiment Roadmap

The next experiment ID is `EXP-012`.

Candidate IDs are planning placeholders. Actual scopes must still be created one at a time through the research pipeline and may be split further if a question exceeds the complexity budget.

| Candidate ID | Source Hypothesis | Question | Notes |
| --- | --- | --- |
| EXP-012 | Data prerequisite | Is the current time-bar dataset sufficient for ICT macro-window research? | Data readiness, NY-time conversion, session coverage, missing bars, instrument fit, cost assumptions, and unavailable preferred-data gaps. |
| EXP-013 | H1 | Are predefined NY macro windows statistically different from adjacent and randomized control windows? | Time-bar-native macro-window characterization: range, absolute return, sweep frequency, displacement frequency, and forward-return shape. |
| EXP-014 | H2 prerequisite | Can previous-day and overnight high/low liquidity levels be computed reproducibly on the available instruments? | Definition validation for PDH/PDL and ONH/ONL before event studies. |
| EXP-015 | H2 | Do prior-day and overnight high/low sweeps show measurable failed-breakout behavior? | Sweep-only event study using MFE, MAE, time-to-target, time-to-invalidation, and 1R/2R before-stop probabilities. |
| EXP-016 | H2 context | Are sweep outcomes materially different inside macro windows versus outside macro windows? | Tests whether H1 and H2 interact before adding confirmation logic. |
| EXP-017 | Premium/discount assumption | Does previous-day midpoint premium/discount filtering improve sweep quality or only reduce sample size? | Starts with the simplest location filter from the spec before VWAP or distance-from-open variants. |
| EXP-018 | H3 | Does adding deterministic displacement improve sweep-only outcomes? | Compare sweep-only versus sweep plus large-candle/body and close-location displacement definitions. |
| EXP-019 | H3 variant | Does requiring a micro swing break after sweep improve signal quality beyond simpler displacement? | Separate from EXP-018 to avoid conflating displacement definitions. |
| EXP-020 | H4 prerequisite | Can FVG and IFVG zones be detected reproducibly with stable sample sizes? | Definition validation for three-candle FVG and close-through inversion rules. |
| EXP-021 | H4 | Does IFVG confirmation improve entry quality enough to offset later entry and fewer signals? | Compare sweep rejection, displacement close, FVG formation, IFVG close, second-candle-open entry, and retest entry only within the approved budget. |
| EXP-022 | H5 prerequisite | Which objective breaker candidate is reproducible enough for testing? | Compare swing-break breaker versus last-opposite-candle/order-block proxy as definitions, not profitability claims. |
| EXP-023 | H5 | Does breaker confirmation improve trade quality beyond sweep plus displacement or IFVG? | Test one approved breaker definition at a time; report expectancy, drawdown, trade count, and average R. |
| EXP-024 | Entry rule | Does the second-candle-open execution rule improve or degrade entry quality versus simpler post-confirmation entries? | Isolates the ICT execution-timing claim from IFVG/breaker detection. |
| EXP-025 | H6 | Is the fixed 1:2 risk/reward target justified versus 1R, 1.5R, 3R, time stops, or nearest opposing liquidity? | Exit/risk-model experiment only after an entry event definition has enough sample size. |
| EXP-026 | Component ablation | Which validated components contribute net value when combined incrementally? | Produces the component contribution table from the source spec. |
| EXP-027 | Full model | Does the best predeclared full-model variant survive analysis-set testing after costs and robustness checks? | Run only after the component ablation identifies eligible variants. |
| EXP-028 | Robustness | Does the candidate survive year/regime/instrument segmentation, execution-delay perturbation, and spread/slippage stress? | Robustness and falsification, not optimization. |

This roadmap is intentionally broader than the first few experiments. It records the source-spec hypotheses so they are not lost, while preserving the pipeline rule that each actual experiment scope must stay small and falsifiable.

## Method Standards

- Use descriptive statistics, non-parametric comparisons, bootstrap intervals, and control-window tests before any model complexity.
- Predefine all windows, levels, buffers, and thresholds before results are inspected.
- Use NY-time conversion explicitly and document daylight-saving/session assumptions.
- Keep returns, MFE/MAE, R-multiple outcomes, and hit rates on real time-bar OHLC prices.
- Treat cost assumptions as explicit scenario inputs unless true spread/commission data exists.
- Report trade count and event count before interpreting expectancy.
- Avoid optimizing macro windows, buffers, targets, or confirmation delays against analysis-set performance.
- For exploratory component experiments, report component behavior even when the component fails to improve expectancy. The goal is to determine whether the ICT concept is measurable, neutral, harmful, or useful under objective definitions.
- Do not promote any component to full-model use unless its definition, sample size, and measured contribution are documented.

## Immediate Next Step

Scope `EXP-012` as a data-readiness and feasibility experiment. Do not start with the full ICT model.
