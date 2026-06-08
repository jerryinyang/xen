# Results: Experiment EXP-025 — AVWAP Line Support/Resistance Direct Test

## Summary

EXP-025 tests whether AVWAP bounce trigger bars show direct line-level support/resistance behavior, measured by a predeclared line-rejection score versus matched same-regime proximate controls. The result is the opposite of the scoped hypothesis: events systematically have **worse** (more negative) line-rejection scores than controls across all 24 reportable instrument/domain/direction cells. Under the predeclared criteria, this yields **INCONCLUSIVE** — no domain meets Evidence FOR (effects are negative, not positive), but the 4h domain's CI spans zero, so Evidence AGAINST also does not apply. The 5m domain provides the cleanest read (unbroken balance, n=10,432, tight CIs) and decisively shows EVIDENCE_AGAINST, but the overall verdict is inconclusive because the 4h domain's CI crosses zero.

## Detailed Findings

### 1. Primary domain-level effects are consistently negative

The domain-level paired line-rejection advantage (event score minus mean matched-control score) is negative in every reportable domain:

| Domain | Effect (bps) | CI Low | CI High | n | Holm p | Decision | Balance |
|--------|-------------|--------|---------|---|--------|----------|---------|
| 5m | -4.41 | -4.85 | -4.00 | 10,432 | 1.0 | EVIDENCE_AGAINST | OK (1.99 bps) |
| 1h | -16.94 | -22.12 | -11.77 | 763 | 1.0 | EVIDENCE_AGAINST | Broken (6.58 bps) |
| 4h | -6.77 | -34.13 | +22.80 | 120 | 1.0 | INCONCLUSIVE_SPANS_ZERO | Broken (27.57 bps) |

All three domains are reportable (5m: 4 instruments, 1h: 4 instruments, 4h: 3 instruments — XAUUSD excluded at 26 events < 30). No domain has a positive point estimate, so Evidence FOR cannot be met. The 4h CI spans zero, preventing the clean Evidence AGAINST that would apply if every domain's upper bound were ≤ 0.

### 2. 5m is the cleanest read and shows Evidence AGAINST

The 5m domain has 10,432 reportable events across 4 instruments, a narrow 0.85 bps CI width, and median event-control proximity difference of 1.99 bps — just under the predeclared 2.0 bps balance threshold. The effect of -4.41 bps (CI [-4.85, -4.00]) is precisely estimated, entirely negative, and its one-sided Holm-adjusted p for a positive advantage is 1.0. Under the predeclared criteria, 5m is EVIDENCE_AGAINST.

### 3. 1h and 4h have broken matching balance

The 1h domain median proximity difference is 6.58 bps (> 2.0 threshold), and 4h is 27.57 bps. Both fail the predeclared balance guard, meaning event and control bars are not equally line-proximate at the domain level. This is partly mechanical: bounce triggers (events) cross the AVWAP line by definition, so their absolute close-to-AVWAP distance is systematically larger than non-crossing but line-proximate controls. The balance guard was correctly triggered on these domains, and their negative effects should be read with this caveat.

### 4. Score component decomposition explains the sign reversal

Across all 24 reportable cells, the pattern is consistent:
- **Events**: mean `line_rejection_score` is near-zero or slightly negative (e.g., BTCUSD 5m bullish -1.00 bps, EURUSD 5m bullish -0.23 bps)
- **Controls**: mean `line_rejection_score` is positive (e.g., BTCUSD 5m bullish +8.13 bps, EURUSD 5m bullish +1.45 bps)

The decomposition shows events have systematically higher `adverse_penetration` (intrabar penetration through AVWAP) than controls, while `close_rebound` is comparable. This is structurally expected: a bullish bounce trigger closes above AVWAP (positive rebound) but its intrabar low penetrates below AVWAP (positive adverse penetration), and the low's penetration typically exceeds the close's rebound because the bar must cross the line to trigger. Controls sit near AVWAP without crossing, so their intrabar penetration is smaller.

### 5. Matching quality and diagnostics

- **Mean controls per reportable event**: ~4.5–4.9 (close to the 5-control maximum), indicating adequate candidate pool availability when proximity conditions are met.
- **Non-reportable events**: All attrition is due to `insufficient_line_proximate_controls` (< 3 controls within band proximity). Zero events lost to invalid AVWAP or score computation.
- **Balance note**: The 5m domain-level median proximity diff (1.99 bps) is borderline. BTCUSD 5m shows instrument-level broken balance (bullish 4.81 bps, bearish 3.67 bps), masked by domain-level pooling. This does not change the overall conclusion since the effect is negative across all instruments.

## Hypothesis Verdict

**INCONCLUSIVE.**

The scoped hypothesis posited a positive line-rejection advantage (events reject AVWAP more strongly than controls). The data show the opposite: events have **worse** line-rejection scores than controls. Under the predeclared criteria:

- **Evidence FOR**: not met — no domain has a positive point estimate.
- **Evidence AGAINST**: not met because the 4h domain's CI spans zero (upper bound +22.80 bps), so not "every reportable domain's CI upper bound ≤ 0."
- **Inconclusive trigger**: at least one reportable domain (4h) has a CI spanning zero.

The 5m domain alone would produce Evidence AGAINST (CI [-4.85, -4.00], upper bound < 0), and it is the cleanest read. But the predeclared criteria require all reportable domains to have CI upper bound ≤ 0 for Evidence AGAINST, and 4h prevents that.

## Limitations

- **Metric design conflates trigger definition with line-rejection signal**: Bounce triggers cross AVWAP by definition, so adverse penetration is inherent. The score systematically penalizes events for the crossing that defines them. This is not a bug — it means the scoped hypothesis was structurally unlikely to find positive effects under this metric.
- **Balance broken on slower domains**: 1h and 4h fail the predeclared proximity guard (6.58 and 27.57 bps). Their negative effects may partly reflect systematic proximity differences rather than pure line-rejection behavior.
- **4h small sample size**: 120 events across 3 instruments with 2–5 regime clusters per instrument/direction cell produce a coarse bootstrap distribution (CI width 57 bps). The INCONCLUSIVE label is appropriate.
- **BTCUSD 5m instrument-level proximity imbalance**: BTCUSD 5m shows broken balance (3.67–4.81 bps) but is not flagged because the domain-level median (1.99 bps) passes the threshold. This is a transparency gap, not a correctness issue.
- **Analysis set only**: All results are on the first-70% chronological slice. The global holdout remains sealed.
- **Diagnostic, not a candidate screen**: EXP-025 tests a component mechanism. It does not qualify or disqualify a tradable strategy.

## Alternative Explanations

- **The negative effect is structural, not behavioral**: The score formula gives events a penalty for the intrabar crossing that defines them. A bounce trigger cannot occur without adverse penetration (the low must go below AVWAP in bullish direction to trigger the bounce close above), so the metric systematically disadvantages events versus controls that are near AVWAP without crossing. This means EXP-025 does not test "does the AVWAP line act as S/R" in the general sense — it tests "do crossing bars reject the line more than non-crossing proximate bars," which is a subtly different question.
- **EXP-021/022 positives are not invalidated**: The positive component evidence (fixed-horizon bounce continuation, lifetime target/trend-change outcomes) is about regime-gated continuation and completion effects, not direct bar-level line reaction. EXP-025's negative result is orthogonal — continuation can be real even without the trigger bar itself showing a line-rejection score advantage.
- **A different metric could test the same hypothesis**: If the scoped question were "do bounce-trigger bars show less intrabar penetration than similarly crossing non-trigger bars," a different control strategy (matching on crossing intensity rather than proximity) would be needed. That is a separate experiment, not a post-hoc fix to EXP-025.

## Recommended Next Steps

1. **Register INCONCLUSIVE in the multiplicity registry** under CF-AWAP-001/DIAG-002. The diagnostic tested direct bar-level line rejection and found events perform worse than controls, consistent with a structural metric artifact. This does not retire the diagnostic — it documents the metric limitation.
2. **Do not open a new experiment to fix the metric**. The structural issue (trigger definition conflates with line-rejection signal) means any metric that scores bars on AVWAP crossing will face the same confound at the trigger bar itself. A meaningful line-S/R test would require a different identification strategy (e.g., prospective AVWAP proximity, not bounce triggers), which is a fundamentally different experiment.
3. **Phase 005 Stage A completes with EXP-025**. The three diagnostics now resolve:
   - EXP-023 (baseline screen): REFUTED — always-on AVWAP does not qualify.
   - EXP-024 (bounded-hold decomposition): MIXED_OR_INCONCLUSIVE — fork (b) dilution on 5m, not clean fork (a). 
   - EXP-025 (line S/R): INCONCLUSIVE — events show worse line-rejection, metric conflated with trigger logic.
   - Collectively, no diagnostic provides a clean Stage A positive that automatically justifies Stage B candidate work under the Phase 005 design.
4. **Stage B/C decisions require operator and governance handling** of the mixed/inconclusive Phase 005 Stage A output before any new candidate-screening scope or operationalization study.
