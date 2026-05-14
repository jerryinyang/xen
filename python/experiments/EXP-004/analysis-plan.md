# Analysis Plan: Experiment EXP-004

## Objective

Quantify the detection latency and precision of chart-type trend reversal signals against a real-price reversal reference built from 1-minute time bars.

## Methodology

### Step 1: Build Real-Price Reversal Reference

- **Method**: ATR-scaled swing reversal detector on analysis-set 1-minute time bars, with each reversal timestamped only after confirmation.
- **Why this method**: It creates a simple real-price reference while respecting when a reversal would have become knowable.
- **Simpler alternative considered**: Close-to-close sign flips. That is too noisy and would turn ordinary 1-minute movement into reversal events.
- **Assumptions**: The reference is an operational label, not ground truth market structure; sensitivity to one alternate threshold is reported only as a stability check.
- **Expected output**: Reference reversal table per instrument with confirmation timestamp and direction.

### Step 2: Extract Chart-Type Reversal Signals

- **Method**: Direction-change events from each chart type, timestamped by `CloseTime` for time bars and Heiken Ashi and `SourceCloseTime` for Line Break and Renko.
- **Why this method**: Direction changes are the simplest comparable reversal signal available across chart types.
- **Simpler alternative considered**: Pattern-specific structure labels. That adds complexity and would broaden the experiment beyond speed-precision trade-off.
- **Assumptions**: Chart types have different event densities, so false and duplicate signals must be normalised per real-time window.
- **Expected output**: Signal table by instrument, chart type, timestamp, and direction.

### Step 3: Match Signals to Real Reversals

- **Method**: Event matching within a fixed tolerance window, reporting median latency, precision, recall, and split rate; paired bootstrap intervals for latency differences versus time bars.
- **Why this method**: These metrics map directly to speed and fidelity without strategy-return assumptions.
- **Simpler alternative considered**: Correlation between signal direction and future price movement. That would move toward predictive validation and is out of Phase 1 scope.
- **Assumptions**: Matched events are temporally dependent; interpretation focuses on instrument-level summaries and effect sizes.
- **Expected output**: Speed-precision table, latency intervals, and support/refutation flags.

## Visualisations

1. Event timeline for one representative reversal cluster - verifies timestamp matching.
2. Box plot of detection latency by chart type - compares speed.
3. Precision-recall scatter by chart type and instrument - shows trade-off.
4. Bar chart of split rate by chart type - shows duplicate signalling.
5. Heatmap of latency improvement versus precision change by instrument - summarises trade-offs.

## Interpretation Guide

- If Line Break or Renko reduces median latency by at least 30% on at least 3 instruments and precision does not exceed time bars by more than 10 percentage points, the speed-trade-off hypothesis is supported.
- If event-based chart types do not materially reduce latency, the hypothesis is refuted.
- If latency improves but precision falls by more than 25 percentage points, report an inconclusive or adverse trade-off rather than support.

## Complexity Check

- Statistical tests: 3 / 3
- Visualisations: 5 / 5
- New modules: 1 / 1

## Chart-Type Comparison Considerations

### Cross-Chart Alignment

- Match events by timestamp tolerance windows, never by bar sequence.
- Report unmatched real reversals and unmatched chart-type signals.
- The final 30% global holdout remains excluded before reversal labelling, chart generation, event matching, and plotting.
- Time bars and Heiken Ashi use `CloseTime`; Line Break and Renko use `SourceCloseTime`.

### Synthetic Price Discipline

- Reversal reference and validation use real time-bar prices.
- Heiken Ashi may produce direction-change signals, but HA synthetic prices are not used as real reversal evidence.
- This plan does not compute strategy returns or P&L.

### Bar Density Differences

- Normalise false signal and split rates per elapsed time and per reference reversal count.

### Regime Stratification

- Report optional low/medium/high volatility breakdown only if each regime has enough reversals for stable summaries.
