# Results: Experiment EXP-028

## Summary

The faithful selective AVWAP strategy shows positive event-level edge on **all three domains** under the PRIMARY symmetric own-exit matched-control lifetime excess gate. The EXP-023 negative was a framing/dilution artifact caused by applying a per-bar continuous-position referee to a ~6%-active event signal. Under the fit-for-purpose event-level method (EXP-027), all domains produce clean FOR verdicts with tight CIs above zero and strong Holm-adjusted significance. The phase outcome is **EVAL_SUPPORTED**.

## Detailed Findings

### Finding 1: PRIMARY — All 3 Domains EVIDENCE_FOR

| Domain | Effect (bps) | 95% CI | CI Half-Width | Holm p | n Events | Verdict |
|--------|-------------|--------|--------------|--------|----------|---------|
| 5m | +5.78 | [5.39, 6.13] | 0.37 | 0.003 | 12,795 | EVIDENCE_FOR |
| 1h | +23.38 | [17.40, 29.32] | 5.96 | 0.003 | 924 | EVIDENCE_FOR |
| 4h | +69.02 | [46.84, 90.52] | 21.84 | 0.003 | 187 | EVIDENCE_FOR |

All three domains meet the Evidence-FOR criteria: effect > 0, CI_low > 0, Holm_p ≤ 0.05, and secondary-horizon stable (fixed-horizon h1/h6 excess not jointly negative — see event_diagnostics.csv: all h1 and h6 fixed-horizon excesses are positive).

- **5m** is the strongest result in precision (tightest CI, largest sample). The +5.78 bps per-event excess over same-exit matched controls is a precise, high-confidence estimate.
- **1h** shows +23.38 bps with moderate precision (CI half-width ~6 bps). Sample size is adequate (924 events, 4 reportable instruments).
- **4h** shows the largest effect (+69.02 bps) but with the widest CI (half-width ~22 bps) and fewest events (187). Despite the wider CI, the lower bound remains far above zero.

The per-event excess consistently increases from 5m → 1h → 4h, matching the pattern in EXP-021 (fixed-horizon bounce reaction) and EXP-022 (lifetime completion advantage). This monotonic relationship is consistent with longer hold periods on slower domains capturing larger absolute moves.

### Finding 2: Secondary — Partially Calibrated, Agrees Where Calibrated

| Domain | Effect (bps) | Calibrated? | FPR | Verdict |
|--------|-------------|-------------|-----|---------|
| 5m | +4.26 | NO (FPR=1.0) | 1.00 | NOT_CALIBRATED |
| 1h | +13.73 | YES (FPR=0.03) | 0.03 | EVIDENCE_FOR |
| 4h | +57.35 | NO (FPR=0.26) | 0.26 | NOT_CALIBRATED |

The asymmetric endogenous-exit-vs-fixed-window construction is calibrated only on 1h. On 5m the construction is strongly biased (FPR=1.0, every placebo draw showed a false FOR), confirming the pre-execution concern: the endogenous exit rule creates a systematic positive bias in the asymmetric construction. On 4h the sample is too thin to calibrate reliably (FPR=0.26). The SECONDARY 1h result (+13.73 bps EVIDENCE_FOR) agrees with the PRIMARY direction, strengthening confidence.

### Finding 3: Equity Companion — Positive Across All Domains

| Domain | Strategy (bps) | Baseline (bps) | Advantage (bps) | Adv. Rate | Sortino Diff |
|--------|---------------|----------------|-----------------|-----------|-------------|
| 5m | +2,613.5 | −17,493.7 | +20,107.2 | 1.0 | +0.41 |
| 1h | +280.2 | −5,538.9 | +5,819.1 | 1.0 | +0.40 |
| 4h | +419.9 | −3,335.4 | +3,755.4 | 1.0 | +0.62 |

The exposure-matched baseline (same-exit controls at non-trigger regime bars) carries substantial negative cumulative returns across the analysis set. The selective strategy's cumulative log-equity is systematically positive against this baseline in every domain and every instrument (advantage_rate=1.0). The Sortino difference is positive across all domains, indicating the strategy's per-event return distribution has a better downside-risk profile than the baseline.

These cumulative totals are per-event arithmetic sums over hundreds to thousands of events — the correct effect-size estimate is the PRIMARY per-event excess (Finding 1), not the cumulative advantage magnitude.

### Finding 4: Pyramid Inclusion Does Not Drive the Result

| Domain | Total Events | Pyramid | Non-Pyramid | Pyramid Fraction |
|--------|-------------|---------|-------------|-----------------|
| 5m | 12,795 | 6,258 | 6,537 | 0.49 |
| 1h | 924 | 443 | 481 | 0.48 |
| 4h | 187 | 84 | 103 | 0.45 |

Pyramid bounces constitute roughly half of all events across domains, consistent with the EXP-020 ~50% pyramid prevalence. The regime-cluster bootstrap (resampling regime_id clusters) absorbs the extra within-regime dependence pyramids introduce. The diagnostic pyramid split is reported but does not change the verdict.

### Finding 5: Dependency Gates Pass and Determinism Confirmed

| Check | Status |
|-------|--------|
| EXP-020 overall_status | SUPPORTED_FULL |
| EXP-027 method_verdict | METHOD_VALID |
| EXP-022 lifetime artifacts | present |
| EXP-021 reaction artifacts | present |
| Frozen inference hash match | PASS (ea261b9e) |
| Control-matching equivalence | PASS |
| Alignment cells checked | 12/12 PASS |
| Event-frame reconciliation | 0 bad |

## Hypothesis Verdict

**EVAL_SUPPORTED**

The predeclared phase-outcome criterion is met: at least one domain (in fact all three) shows PRIMARY Evidence-FOR under the frozen EXP-027 event-level evaluation method. The faithful selective AVWAP strategy, evaluated under a fit-for-purpose, in-envelope yardstick, exhibits a positive per-event matched-control excess on all domains.

## Limitations

- **4h sample size** (187 events) limits precision. The effect is large (+69 bps) and both CI bounds well above zero, but the CI half-width (~22 bps) is wide. Direction is unambiguous; magnitude uncertainty is higher.
- **No cost model.** Returns are gross — transaction costs, slippage, and spread are not deducted. This is an event-level edge test, not a P&L estimate.
- **Analysis-set only.** Results hold on the first-70% chronological slice. The global holdout is sealed. Fresh-regime replication is required before any operational inference.
- **Pyramid inclusion is predeclared as faithful-to-original** but means events within the same regime are dependent. The regime-cluster bootstrap absorbs this dependence, but the effective information per event is lower than the raw count suggests.
- **Secondary construction is calibrated only on 1h.** The 5m and 4h secondary results carry zero interpretive weight as predeclared.

## Alternative Explanations

- **Timing skill vs structural advantage.** The PRIMARY compares the strategy's entry timing against same-exit controls at non-trigger regime bars. The positive excess could reflect either genuine AVWAP bounce timing skill or a structural difference between trigger and non-trigger bars that the matching does not fully control. The EXP-021 fixed-horizon bounce reaction (+3.8/+9.1/+37.6 bps at h=3) is consistent with genuine timing skill.
- **Exit rule dependence.** The EXP-022 band-target/trend-change exit rule is part of the evaluated strategy. A different exit rule would produce different event-level returns. The positive PRIMARY excess reflects the strategy-as-a-whole: entry + exit.

## Recommended Next Steps

1. **Fresh-regime replication.** Open a new experiment (new EXP-ID) that replicates the EXP-028 method on the global holdout (once that becomes accessible under a governance-approved fresh-regime protocol) or on a future live-collection window.
2. **FAMILY_REVIEW** as per Phase 006 §7. With EVAL_SUPPORTED, the strategy has a first fairly-evaluated positive result. The operator should decide whether to proceed to robustness testing, component isolation (exit rule contribution vs timing contribution), or exploration of registered detector/anchor branches (`/LB`, `/MB`, `/ATR`, `/ANCHOR`).
