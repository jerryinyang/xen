# Results: Experiment EXP-004

## Summary

EXP-004 tested whether Line Break (level 3) and Renko (ATR-14) detect real-price trend reversals faster than 1-minute time bars on at least 3 of 4 instruments, with precision no more than 10 percentage points higher. The hypothesis is **REFUTED**. Event-based charts are dramatically slower — not faster — than the time-bar baseline. Line Break median latency is 110-111 minutes (55x slower), Renko is 101-105 minutes (50x slower), and Heiken Ashi is 4.0 minutes (2x slower), compared to the time-bar baseline of 2.0 minutes across all four instruments. The trade-off runs in the opposite direction: event-based charts are far more precise (~99.9% for Line Break and Renko) but miss most reversals (recall 34-40% for Line Break, 72-75% for Renko).

## Detailed Findings

### Finding 1: Event-based charts are slower, not faster

- **Observation**: Median detection latency for event-based charts is 50-55x higher than the time-bar baseline.
- **Evidence**:
  - Time bars: 2.0 min median latency (all 4 instruments)
  - LineBreak: 110-111 min (EURUSD, XAUUSD, BTCUSD, USTEC)
  - Renko: 101-105 min (all 4 instruments)
  - HeikenAshi: 4.0 min (all 4 instruments)
  - Latency improvement vs Time is negative for all event charts: LineBreak -5400%, Renko -5000%, HeikenAshi -100%
  - `support_summary.csv`: FasterCount = 0/4 for all chart types; CombinedTailProbability = 1.0
- **Interpretation**: The speed hypothesis is decisively refuted. The mechanism is clear: the ATR-scaled swing reversal detector on 1-minute bars confirms reversals on nearly every bar (119K-147K reversals per instrument), because 1-minute price movement frequently crosses the 1.5x ATR threshold. Event-based charts, by design, require larger cumulative price moves to change direction, so their signals lag behind the 1-minute reversal reference by many bars.

### Finding 2: Event-based charts are far more precise but have low recall

- **Observation**: Line Break and Renko achieve ~99.9% precision but recall of only 34-40% (Line Break) and 72-75% (Renko).
- **Evidence** (`precision_recall_summary.csv`):
  - Time bars: precision 26-28%, recall ~100%, split rate 83-85%
  - LineBreak: precision 99.9%, recall 34-40%, split rate ~0%
  - Renko: precision 99.9%, recall 72-75%, split rate ~0.04%
  - HeikenAshi: precision 52-56%, recall ~100%, split rate 47-51%
- **Interpretation**: Event-based charts emit far fewer signals (40K-89K vs 419K-547K for time bars), and most of those signals do correspond to real reversals. The cost is that many real reversals go undetected. This is a precision-recall trade-off, not a speed advantage. Time bars, by contrast, detect almost every reversal but generate massive numbers of false/duplicate signals (split rate 83-85%).

### Finding 3: Heiken Ashi occupies an intermediate position

- **Observation**: Heiken Ashi has 2x the latency of time bars (4.0 vs 2.0 min), moderate precision (52-56%), and high recall (~100%).
- **Evidence**: HA produces 206K-264K signals (fewer than time bars' 419K-547K but far more than event charts), with split rates of 47-51%.
- **Interpretation**: HA's smoothing reduces some noise relative to raw time bars but does not achieve the precision of event-based charts. Its latency penalty is modest (2x) compared to Line Break/Renko (50-55x).

### Finding 4: Reversal labels are stable under threshold sensitivity

- **Observation**: Primary (1.5x ATR) and alternate (2.0x ATR) reversal labels show 100% overlap in both directions across all instruments.
- **Evidence** (`sensitivity_summary.csv`): PrimaryOverlapRate = 1.0, AlternateOverlapRate >= 0.99999, MedianConfirmationShiftMinutes = 1.0, StableLabels = True for all instruments.
- **Interpretation**: The reversal reference is stable. The 120-minute tolerance window is wide enough that both thresholds detect reversals in the same time regions, typically 1 minute apart. This validates the reference but also suggests the sensitivity check has limited discriminative power (noted in audit.md).

### Finding 5: The decision rule fails completely

- **Observation**: The success criterion required >=30% latency reduction on >=3 instruments with precision within +10pp.
- **Evidence** (`support_summary.csv`):
  - LineBreak: FasterCount=0, CombinedSupportCount=0, FasterRuleMet=False, CombinedRuleMet=False
  - Renko: FasterCount=0, CombinedSupportCount=0, FasterRuleMet=False, CombinedRuleMet=False
  - HeikenAshi: FasterCount=0, CombinedSupportCount=0, FasterRuleMet=False, CombinedRuleMet=False
  - Exact tail probability under fair sign null: 1.0 for all chart types
- **Interpretation**: Not a single instrument shows the hypothesized speed advantage. The result is not borderline — it is in the opposite direction with overwhelming magnitude.

## Hypothesis Verdict

**REFUTED**

The hypothesis that "Line Break level 3 and Renko ATR-14 detect predefined real-price trend reversals faster than 1-minute time-bar confirmation on at least 3 of 4 instruments" is decisively refuted. The observed effect is in the opposite direction: event-based charts are 50-55x slower than the time-bar baseline.

The complementary precision claim ("precision is not higher than the time-bar baseline") is also not supported in the way the hypothesis intended. Event-based charts are far more precise (~99.9% vs ~27%), but this comes with dramatically lower recall (34-75% vs ~100%). The speed-precision trade-off exists, but it is a precision-recall trade-off, not a speed advantage.

**What the data actually shows**: Event-based charts trade recall for precision. They detect fewer reversals but with much higher signal quality. Time bars detect nearly all reversals but with massive signal redundancy (83-85% split rate). The practical implication is that event-based charts may be useful for reducing signal noise, not for faster detection.

## Limitations

1. **Reversal reference granularity**: The ATR-scaled swing detector on 1-minute bars produces very frequent reversals (100K-150K per instrument). This makes the "speed" comparison favor time bars by construction, since the reference is defined on the same 1-minute grid. A coarser reversal definition (e.g., on 15-minute bars or using a higher ATR multiplier) might yield different results.
2. **Sensitivity check limited discriminative power**: The 120-minute tolerance window makes the primary/alternate threshold overlap trivially high (audit.md Warning 1).
3. **Single threshold pair**: Only 1.5x and 2.0x ATR were tested. A wider range of thresholds might reveal regimes where event-based charts are faster.
4. **Direction-change signals only**: The experiment uses the simplest possible chart-type signal (direction change). More sophisticated signals (e.g., pattern-based reversals) might have different speed characteristics.

## Alternative Explanations

1. **Reference bias**: The reversal reference is built from 1-minute bars, so it is inherently aligned with the time-bar signal timeline. Event-based charts operate on a different event clock, making direct latency comparison inherently unfavorable to them. This is a methodological limitation, not a flaw — but it means the "speed" question may be better framed as "event density" rather than "latency."
2. **ATR threshold too low**: A 1.5x ATR threshold on 1-minute bars may be too sensitive, producing reversals on ordinary noise. If the threshold were higher (e.g., 3-5x ATR), the reversal count would decrease and event-based charts might show relatively better speed.

## Recommended Next Steps

1. **EXP-007 (suggested)**: Repeat the speed-precision comparison using a coarser reversal reference (e.g., 15-minute bar swing detection or higher ATR multiplier) to test whether event-based charts show a speed advantage when the reference is not on the same 1-minute grid.
2. **EXP-008 (suggested)**: Characterize the precision-recall trade-off explicitly as a function of chart-type parameters (Line Break level, Renko ATR period) to map the efficient frontier of signal quality vs. detection rate.
3. **EXP-001 (Information Density)**: The finding that time bars have 83-85% split rate vs near-0% for event charts directly relates to the information density question in EXP-001.
