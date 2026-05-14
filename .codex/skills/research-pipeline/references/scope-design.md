# Scope Design Reference

Guidance for formulating rigorous experiment scopes during Stage 1 of the Xen research pipeline.

---

## Writing Good Hypotheses

### Structure

A testable hypothesis follows this pattern:
**[Chart Type A] has a [specific relationship] with [Metric B] under [conditions], compared to [baseline].**

### Examples by Research Area

#### Chart-Type Information Content
- "Line Break bars at level 3 produce fewer ghost bars (zero-range bars) than 1-minute time bars on ≥3 of 4 instruments, with ghost rate ≤5% for Line Break vs ≥10% for time bars."
- "Renko bricks with ATR-14 have higher information content per bar (entropy) than time bars at matched sample size, measured by Shannon entropy of bar direction."

#### Volatility & Regime Representation
- "Line Break bars align more precisely with volatility regime boundaries (tercile-based) than time bars, with lower hybrid rate and faster regime detection on ≥3 instruments."
- "Renko brick size adapts to local volatility, producing fewer bars in low-volatility regimes and more bars in high-volatility regimes, with bar-count CV across regimes lower than time bars."

#### Noise Filtering & Robustness
- "Under 20% source-bar close perturbation, Renko directional stability (bar direction consistency) has lower CV than time bar directional stability across 4 instruments."
- "Heiken Ashi smoothed returns exhibit lower variance but systematically compress return magnitude by ≥50% compared to real returns, making HA-derived returns unreliable for risk estimation."

#### Market Structure Capture
- "Line Break reversal signals detect trend reversals faster than time-bar confirmation delays, with median latency reduction ≥30% on volatile instruments (XAUUSD, BTCUSD, USTEC)."
- "The speed-precision trade-off for Renko shows: lower detection latency than time bars on ≥3 instruments but higher false signal rate (precision ≤ time-bar precision on ≥2 instruments)."

#### Synthetic Price Distortion (Heiken Ashi Specific)
- "Heiken Ashi synthetic prices compress realised volatility by ≥30% on all 4 instruments, making HA-derived volatility metrics unreliable for risk management."
- "HA trend smoothing produces fewer false trend signals in low-volatility regimes but introduces systematic lag in high-volatility regimes."

#### Cross-Chart-Type Agreement
- "When Line Break and Renko agree on trend direction (both producing up-signals within a tolerance window), the agreement rate is ≥60% across all instruments and regimes."

### Hypotheses vs Exploratory Questions

Some experiments are exploratory — they don't test a hypothesis but characterise data. The question must still be specific:

**Good**: "What is the empirical distribution of bar duration for Renko (ATR-14) vs 1-minute time bars on EURUSD, and how does duration CV compare across volatility regimes?"

**Bad**: "What patterns exist in the chart-type data?"

---

## Complexity Budget Guidelines

| Experiment Type | Stat Tests | Visualisations | Code Modules |
|----------------|-----------|----------------|-------------|
| Descriptive / EDA | 0 | 2-4 | 0-1 |
| Single hypothesis test | 1-2 | 2-3 | 1 |
| Comparative (across chart types) | 2-4 | 3-5 | 1-2 |
| Multi-chart-type relationship | 2-3 | 3-5 | 1-2 |
| Cross-chart-type alignment | 2-4 | 3-5 | 1-2 |

If an experiment needs more than these limits, **split it into multiple experiments**.

---

## Scope Boundary Patterns

### Chart-Type Comparison Patterns

- **Single chart type vs baseline**: "Line Break bars produce fewer ghost bars than time bars" — simplest, best for initial characterisation
- **Multi-chart-type comparison**: "Information density ranking: time < Renko < Line Break on volatile instruments" — requires multiple pairwise comparisons
- **Regime-stratified comparison**: Same analysis repeated for low/medium/high volatility regimes
- **Timeframe-as-hyperparameter**: Same chart-type comparison on different timeframes (1min, 15min, 1h, 4h)

### Common Exclusions

Always consider excluding:
- Heiken Ashi HA prices from return calculations (use RealClose only)
- Low-activity periods where chart-type generators produce very few bars
- Specific sessions or time periods with known data anomalies
- The final 30% global holdout (always — non-negotiable)
- Bar-index alignment across chart types (always exclude — align by timestamp)

### Phantom Price Considerations

For any experiment involving Heiken Ashi:
- **Mandatory**: All return metrics use `RealClose` (or time-bar `Close`), never `HAClose`
- **Mandatory**: Report synthetic-to-real price ratio: how much does HA smooth vs real prices
- **Mandatory**: Document whether HA is used for signals only (acceptable) or for P&L (prohibited)

---

## Success Criteria Patterns

### Good Criteria (concrete, measurable)

- "Evidence FOR: Line Break ghost rate ≤5% while time bar ghost rate ≥10% on ≥3 instruments (bootstrap p < 0.05)"
- "Evidence FOR: Renko detection latency median ≤50% of time-bar latency on ≥3 instruments"
- "Evidence AGAINST: No statistically significant difference in information content between chart types (all p > 0.10)"
- "Inconclusive: Effect size between 5% and 15% improvement, or significance is borderline (0.05 < p < 0.10)"

### Bad Criteria (vague, subjective)

- "Evidence FOR: Line Break seems to filter noise better"
- "Evidence AGAINST: No clear pattern"

---

## Scope Splitting Rules

Each experiment answers **exactly one question**. If the user's idea naturally contains multiple questions, propose splitting:

| User's Broad Idea | Proposed Split |
|------------------|----------------|
| "Do Line Break bars capture trends better than time bars?" | EXP 1: "Do Line Break bars detect trend reversals faster than time bars?" EXP 2: "Do Line Break trend signals have higher precision than time-bar signals?" |
| "Which chart type is best for volatility analysis?" | EXP 1: "Which chart type has the lowest ghost bar rate across instruments?" EXP 2: "Which chart type aligns best with volatility regime boundaries?" |
| "Is Heiken Ashi useful for trading?" | EXP 1: "How much does HA distort return magnitudes?" EXP 2: "Does HA trend direction agree with time-bar trend direction across regimes?" |
| "Compare all chart types" | EXP 1: "Information density comparison across all chart types" EXP 2: "Noise robustness comparison across all chart types" |

---

## Ideas Registry Mapping

When the user proposes an idea, consider how it maps to Xen's research capabilities:

| Idea | Possible Experiments |
|------|---------------------|
| Information density differences | "Which chart types produce more information-dense bars with fewer ghost bars?" |
| Volatility regime capture | "Which chart type aligns best with volatility regime boundaries?" |
| Noise filtering | "How do chart types respond to synthetic noise injection?" |
| Trend detection | "Which chart type detects trend reversals faster, and what is the speed-precision trade-off?" |
| HA distortion | "How much does HA synthetic pricing distort returns and volatility?" |
| Cross-type agreement | "When chart types agree on trend direction, is the signal more reliable?" |
| Strategy theory validation | "Does Line Break trend continuation have positive expected return on time-matched real prices?" |
| Timeframe dependence | "Do chart-type advantages vary across timeframes?" |

If the user proposes an idea not covered above, note it and suggest adding it to the phase design.

---

## Connecting to Checkpoints and Phase Design

**Primary source**: The latest checkpoint's `design.md` in `docs/experiments-docs/checkpoints/` — the authoritative guide for current phase experimentation. Scope experiments listed there first.

**Secondary source**: The previous phase's `retrospective.md`. If it contains "Recommended Next Experiments" or identified gaps, scope those next.

**Tertiary source**: `docs/references/architecture.md` — the architecture document contains research questions, chart-type specifications, and constraints that may inform scope design.

**Phase progression**: When a phase's experiments are complete, write the `retrospective.md` and, if proceeding, create the next phase's `design.md` before starting new experiments.
