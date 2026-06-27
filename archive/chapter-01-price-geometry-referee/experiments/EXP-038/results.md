# Results: Experiment EXP-038

## Summary

EXP-038 evaluated the EURUSD-4h A1-cell on the held-back TEST stratum (dependent subsample check). The TEST stratum (n=12, boot_p=0.001, effect=+24.27 bps) produced a provisional pass: ci_low_1s 15.43 bps > calibrated margin 3.78 bps. The LOCO diagnostic confirms no single regime cluster drives the result (min ci_low_1s 13.25 bps across all 9 drops). The nomination precondition is met (TRAIN net point +6.22 > 0). The binding G2 verdict awaits the phase-level Holm family adjudication in `G2-gate-review.md`.

## Detailed Findings

### Finding 1: Integrity Guards All Pass — Exact Reproduction of EXP-034

- **Observation**: All five integrity guards pass. Full-cell count = 39 (exact). Full-cell net mean = 11.77 bps reproduces EXP-034's effect_bps to 0.0 bps deviation. Full-cell bootstrap CI with EXP-034's seed reproduces its ci_low/ci_high/ci_low_1s/boot_p to ≤ 8.9e-16. The experiment is an exact sample restriction of the already-audited EXP-034 pipeline.
- **Evidence**: reconciliation.csv (all 3 guards PASS). run_metadata.json determinism_replay max_drift = 0.0.
- **Interpretation**: The only difference from EXP-034 is the sample restriction. All cost/financing/filtering/estimator choices are identical. The TEST read is a clean stratum-level temporal-stability check.

### Finding 2: Null Calibration — Measured Anti-Conservatism Corrected

- **Observation**: The frozen bootstrap at the TEST structure (12 events, 9 clusters in 2 direction×regime strata) has FPR uncorrected = 0.0975. The calibrated margin m = 3.78 bps restores FPR to exactly 0.05. Sigma_b = 14.4 bps, sigma_w = 25.2 bps.
- **Evidence**: null_calibration.csv.
- **Interpretation**: The ~2× anti-conservatism at n≈12 matches the predeclared expectation from EXP-027's pooled calibration at n≈187. The 3.78 bps margin is mechanical (Q95 of null ci_low_1s) and moderate compared to the effect scale (+24.27 bps). The sigma_b/sigma_w ratio (~0.57) indicates moderate between-cluster variance — the regime clusters are meaningfully different but not extreme.

### Finding 3: One-Shot TEST — Provisional Pass

- **Observation**: EURUSD-4h TEST: n=12 (3 bull, 9 bear), effect=+24.27 bps, ci_low_1s=15.43 > margin 3.78, raw boot_p=0.001. Descriptive label EVIDENCE_FOR. The full analysis-set boot_p was 0.008 (n=39). The TEST p is stronger (more extreme) despite the smaller n, driven by the larger TEST-stratum effect (+24.27 vs +11.77 bps).
- **Evidence**: test_inference.csv. stratum_disclosure.csv: FULL +11.77, TRAIN +6.22, TEST +24.27.
- **Interpretation**: The A1-cell pass survives the TEST-stratum restriction. This is a provisional `A1_CELL_TEST_PASS_PROVISIONAL` — the final binding requires the phase-level Holm family in G2-gate-review.md.

### Finding 4: LOCO Diagnostic — No Single-Cluster Dependency

- **Observation**: All 9 regime-cluster drops produce ci_low_1s > margin (range 13.25–28.83 bps). The most removal-sensitive drop is the bull regime_id=59 (single event, ci_low_1s=13.25 bps) — still 9.5 bps above the 3.78 margin. Min ci_low_1s = 13.25 bps.
- **Evidence**: loco_diagnostic.csv. run_metadata.json loco_summary: all_above_margin=true, min_ci_low_1s=13.25.
- **Interpretation**: The provisional pass is not fragile — no single regime cluster carries the inference. This is a meaningful robustness signal for the operator considering the one-shot holdout nomination.

### Finding 5: Seed Robustness and Nomination Precondition

- **Observation**: Over 8 seeds, ci_low_1s ranges [14.59, 15.66] — all above margin, sign-stable positive (ci_low_1s_sign_stable=true). TRAIN-stratum net point = +6.22 bps > 0, so nomination precondition met (train_consistent=true).
- **Evidence**: seed_robustness.csv. run_metadata.json nomination_precondition_met=true.
- **Interpretation**: The TEST pass is not a seed artifact. The operator may nominate this package for the one-shot holdout.

### Finding 6: Temporal Pattern — TEST Events Show Larger Moves

- **Observation**: The full-cell net of +11.77 bps decomposes into TRAIN +6.22 (CI spans zero) and TEST +24.27 (CI well above zero). The TEST period (Sep 2024–Apr 2025) captured larger EURUSD price swings than the TRAIN period (Jan 2023–Aug 2024). The TRAIN 95% CI [−7.00, +17.65] spanning zero is consistent with a smaller/less-persistent edge in the earlier period.
- **Evidence**: stratum_disclosure.csv.
- **Interpretation**: This is the correct honest framing per R1.7: the TEST events are a dependent subsample that contributed to the EXP-034 pass, and the temporal pattern shows the EURUSD-4h edge was stronger later in the analysis period. This does not invalidate the TEST read (which is fresh at the stratum level), but it underscores that a holdout release would be the only fully disjoint confirmation.

## Hypothesis Verdict

**A1_CELL_TEST_PASS_PROVISIONAL_PENDING_PHASE_HOLM** (per predeclared criteria)

The hypothesis that EURUSD-4h retains positive net expectancy on the TEST stratum is supported at the provisional level (ci_low_1s 15.43 > margin 3.78, raw boot_p 0.001). The binding G2 verdict (phase-level Holm family adjudication in G2-gate-review.md) is the final gate.

## Limitations

1. **Dependent subsample (R1.7).** This is not an independent out-of-sample confirmation. The TEST events contributed to both the D0 cell selection and the EXP-034 pass. The holdout remains the only fully disjoint arbiter.
2. **Small TEST n (12 events).** The single-cell bootstrap on 12 events has limited precision. The null calibration corrects for anti-conservatism, but the effective power is low.
3. **Single cell, single domain.** EURUSD-4h only. Results do not generalize to other instruments, domains, or cells.
4. **Temporal non-stationarity.** The TEST events (later period) showed larger effects than TRAIN. This pattern may or may not persist into the holdout period.

## Alternative Explanations

- **Later-period market regime.** The stronger TEST signal (2024-09 onward) may reflect a market condition that differs from the TRAIN period (2023-01–2024-08). If the holdout period resembles TRAIN more than TEST, the effect may not replicate.
- **Regime cluster composition.** The 9 TEST clusters are spread across 12 events. If holdout-period events produce new regime clusters not represented in the TEST strata, the bootstrap's coverage may differ.

## Recommended Next Steps

1. **G2-gate-review.md adjudication** — combine this raw p (0.001) with EXP-037's realized p's. Family size = 4 if EXP-037 had a TEST read (which it did: EURUSD p=0.001, USTEC p=0.244, XAUUSD p=0.001). Adjudicate the phase-level Holm.
2. **If G2 is satisfied** → EXP-032 holdout-release checkpoint becomes admissible. The operator selects one package (EURUSD-4h baseline via this route, or EURUSD-4h FH-exit variant via EXP-037). Note: both routes share nearly the same EURUSD-4h events — a joint pass is NOT independent corroboration.
3. **If G2 is not satisfied** → Phase 008 routes CHARACTERISED_NOT_CONFIRMED.
