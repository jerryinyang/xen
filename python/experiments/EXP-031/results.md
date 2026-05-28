# Results: EXP-031 — 15-Minute USTEC Breaker Chain

## Verdict

**INCONCLUSIVE** (reason: TEST_POSITIVE_BUT_BELOW_EXP023_50PCT_REFERENCE_BAND)

Both train and test segments show positive breaker-minus-baseline expectancy with bootstrap CIs excluding zero, in the same direction as the EXP-023 1-minute USTEC positive. The test magnitude (1.84R) is at 44% of the EXP-023 test magnitude (4.18R), falling just below the predeclared 50% comparability threshold. Counts are adequate. The finding is directionally encouraging but does not meet the FOR bar.

---

## Event Waterfall

| Segment | Sweep | Displacement | Breaker-Labeled | Risk-Feasible Breaker | Floor (≥50) |
|---------|-------|-------------|-----------------|----------------------|-------------|
| Train | 399 | 339 | 224 | 219 | PASS |
| Test | 145 | 124 | 79 | 78 | PASS |

**Retention vs EXP-023**: 15-minute displacement count (463) / EXP-023 1-minute count (437) = 1.059. The 15-minute analysis finds slightly more displacement events than 1-minute, consistent with 15-minute bars being larger candles with stronger apparent displacement. Resolution-cost limitation: NOT TRIGGERED.

Breaker confirmation rate: Train 224/339 = 66%; Test 79/124 = 64%. The Candidate A breaker retains approximately two-thirds of displacement events at 15-minute resolution.

---

## Primary Result: Breaker-minus-Baseline Return_R_60m

| Segment | Baseline Mean | Breaker Mean | Diff | 95% CI | CI Excludes Zero |
|---------|-------------|-------------|------|--------|-----------------|
| Train | −0.003R | +0.514R | +0.517R | [+0.235, +0.837] | YES |
| Test | +0.583R | +2.418R | **+1.836R** | [+0.560, +3.636] | YES |

Both CIs exclude zero. Both diffs are positive. The direction is consistent with the EXP-023 1-minute USTEC positive in both segments.

**Train observation**: The 15-minute train CI [0.235, 0.837] is notably sharper than the EXP-023 1-minute train CI [−1.085, 1.795]. The EXP-023 1-minute train result was essentially inconclusive on its own (CI included zero); the 15-minute train result provides definitively positive evidence for the first time.

---

## Comparison with EXP-023 1-Minute Reference

| Segment | EXP-031 15m Diff | EXP-023 1m Diff | Same Direction | EXP-031 ≥ 50% of EXP-023 |
|---------|-----------------|----------------|---------------|--------------------------|
| Train | +0.517R [0.235, 0.837] | +0.334R [−1.085, 1.795] | YES | YES (0.517 ≥ 0.167) |
| Test | +1.836R [0.560, 3.636] | +4.176R [0.066, 8.881] | YES | NO (1.836 < 2.088) |

The test point (1.836R) is at 44% of the EXP-023 test point (4.176R). The predeclared threshold requires ≥50% of the EXP-023 magnitude for the FOR criterion. The miss is narrow (6 percentage points below the threshold), but the threshold is predeclared and cannot be moved post-hoc.

Note: the EXP-023 test CI is very wide ([0.07, 8.88]) — the test-point comparison is between two noisy estimates, both from small sample sets (78 breaker-feasible events in EXP-031 test, with similarly thin counts in EXP-023 USTEC test). The narrow miss of the 50% threshold may not be practically meaningful.

---

## Outcome Summary

| Segment | Class | Trades | Feasible | Mean Return_R | MAE_R | MFE_R | Win Rate |
|---------|-------|--------|----------|--------------|-------|-------|---------|
| Train | Baseline | 339 | 331 | −0.003R | 1.350 | 1.426 | 23.0% |
| Train | Breaker | 224 | 219 | +0.514R | 0.671 | 1.566 | 32.1% |
| Test | Baseline | 124 | 120 | +0.583R | 2.192 | 3.269 | 20.9% |
| Test | Breaker | 79 | 78 | +2.418R | 0.861 | 4.194 | 28.0% |

Key observations:
- **Breaker dramatically reduces MAE (drawdown proxy)** in both segments: Train −0.679R (from 1.350 to 0.671), Test −1.331R (from 2.192 to 0.861). This is the clearest structural signal: the Candidate A breaker selects events with substantially lower adverse excursion.
- **Breaker improves MFE** in both segments: +0.140R train, +0.925R test.
- **Win rate improves** for breaker in both segments: +9.1pp train, +7.1pp test.
- The positive return_R effect is accompanied by a consistent MAE reduction, suggesting the breaker is selecting structurally cleaner setups rather than simply higher-leverage events.

---

## Secondary Bootstrap

| Metric | Segment | Baseline Mean | Breaker Mean | Diff | 95% CI |
|--------|---------|-------------|-------------|------|--------|
| MAE_R_60m | Train | 1.350 | 0.671 | −0.679 | [−1.093, −0.296] |
| MAE_R_60m | Test | 2.192 | 0.861 | −1.331 | [−2.629, −0.165] |
| Return_R_60m | Train | −0.003 | +0.514 | +0.517 | [+0.235, +0.837] |
| Return_R_60m | Test | +0.583 | +2.418 | +1.836 | [+0.560, +3.636] |

The MAE reduction CIs (train [−1.093, −0.296]; test [−2.629, −0.165]) both exclude zero negatively. The breaker consistently selects lower-drawdown events across both segments. This MAE improvement is arguably the most reliable signal, as it is mechanistically coherent with the Candidate A breaker's definition (it requires a specific structural sequence before confirmation, filtering out noisier, higher-drawdown events).

---

## Interpretation Against Success Criteria

| Criterion | Outcome |
|-----------|---------|
| Test CI excludes zero (positive direction) | MET — [0.560, 3.636] |
| Same direction as EXP-023 test | MET |
| EXP-031 test diff ≥ 50% of EXP-023 test diff | NOT MET — 44% vs threshold 50% |
| ≥ 50 risk-feasible breaker events on both segments | MET — 219 train, 78 test |
| Retention ≥ 30% vs EXP-023 1m | MET — ratio 1.059 |
| Sign reverses vs EXP-023 (AGAINST criterion) | NOT TRIGGERED |

---

## Conclusions for the Phase 004A Reflection

1. **The USTEC Candidate A breaker positive is directionally preserved at 15-minute resolution.** Both train (CI [0.235, 0.837]) and test (CI [0.560, 3.636]) show positive breaker-minus-baseline Return_R_60m with CIs excluding zero. The Phase 003 local positive is not a 1-minute resolution artifact.

2. **The 15-minute train result is sharper than EXP-023's 1-minute train result.** EXP-023's 1-minute train CI [−1.085, 1.795] included zero; EXP-031's 15-minute train CI [0.235, 0.837] firmly excludes zero. This is a meaningful improvement in evidential clarity.

3. **The 44% test-magnitude miss is a technicality, not a substantive negative finding.** The EXP-023 test CI was very wide ([0.07, 8.88]), making the 4.18R test point an imprecise reference. The predeclared 50% threshold is binding, but the practical distinction between 44% and 50% replication is within the noise of both estimates. The reflection should note this context.

4. **MAE reduction is the most structurally coherent and consistent finding.** Both segments show Candidate A breaker selects events with approximately half the drawdown of the displacement baseline, with CIs excluding zero in both segments. This provides independent mechanical support for the breaker's selectivity.

5. **Phase 004B Branch A (USTEC breaker validation) is supported to proceed.** The design.md's mid-checkpoint reflection criteria include "USTEC breaker positive survives" → proceed at 15-minute. EXP-031 provides this evidence. The resolution stability of the positive finding justifies proceeding to EXP-032 temporal segmentation and EXP-033 simplified-control tests.

6. **The INCONCLUSIVE verdict accurately captures the state.** The effect is real enough to justify a deeper falsification pass (EXP-032+), not strong enough to declare a candidate without segmentation and control checks.
