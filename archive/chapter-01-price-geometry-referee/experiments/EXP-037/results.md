# Results: Experiment EXP-037

## Summary

EXP-037 evaluated the `/EXIT-FH` fixed-horizon-exit capture-efficiency variant on 4h (EURUSD, USTEC, XAUUSD). The TRAIN mechanical tie-break selected H\*=12 (all_legs policy). On the one-shot TEST stratum, EURUSD-4h produced a **route_pass_provisional** result (ci_low_1s 21.94 bps > margin 8.42 bps, within-route Holm p=0.003). USTEC-4h was INCONCLUSIVE_SPANS_ZERO (power-limited at n=11). XAUUSD-4h showed point EVIDENCE_FOR but failed the calibrated margin (ci_low_1s 11.45 < margin 54.15). The `B2_NO_ROBUST_HSTAR` path was not triggered. The binding G2 verdict awaits the phase-level Holm family adjudication in `G2-gate-review.md`.

## Detailed Findings

### Finding 1: TRAIN Selection — H\* = 12, All Legs

- **Observation**: The mechanical tie-break over {4,6,8,12} retained all four horizons (all N>0, N1>0, N2>0). H\* = 12 was selected by the max-min worst-half criterion (worst-half 41.07 bps vs H=8's 29.80 bps). The N(H) curve was monotone increasing: 6.15 → 20.95 → 31.30 → 39.10 bps.
- **Evidence**: train_tiebreak.csv rows 1–5; frozen_selection.json.
- **Interpretation**: The capture-efficiency benefit grows with horizon in TRAIN — consistent with EXP-031's finding that the BTC exit is a long-horizon trend-truncator. Pyramid policy = all_legs (the only feasible policy under the n≥15 floor; first_leg_only and pyramid_legs_only both had per-instrument counts below floor for some instruments in TRAIN).

### Finding 2: Null Calibration — Significant Anti-Conservatism in XAUUSD

- **Observation**: The small-n bootstrap is anti-conservative at these cell sizes. FPR uncorrected: EURUSD 0.105, USTEC 0.104, XAUUSD 0.163. The margins restore FPR to 0.05 but vary widely: EURUSD 8.4 bps, USTEC 30.3 bps, XAUUSD 54.2 bps.
- **Evidence**: null_calibration.csv. The XAUUSD margin (54.2) is driven by sigma_b = 133.7 bps from only 4 TRAIN clusters.
- **Interpretation**: The margin is mechanical and correct — it reflects the poor identifiability of the cross-cluster mean in the 4-cluster XAUUSD cell. The calibration prevents the anti-conservative bootstrap from producing a false positive. This is the correct governance outcome.

### Finding 3: One-Shot TEST — EURUSD Provisional Pass

- **Observation**: EURUSD-4h TEST: n=12, net=+40.56 bps, ci_low_1s=21.94 > margin 8.42, raw boot_p=0.001, within-route Holm-3 p=0.003. Descriptive label EVIDENCE_FOR. FH-vs-BTC comparison: FH net +40.56 vs BTC net +24.27 — the FH exit added +16.29 bps on these same events.
- **Evidence**: test_verdicts.csv row 1; plot "test_verdicts.png".
- **Interpretation**: The fixed-horizon exit recovered substantial capture efficiency on the EURUSD-4h TEST stratum. The +16.29 bps FH-minus-BTC margin is directionally consistent with EXP-031's finding that the BTC exit drags 4h returns by −27 bps. This is a **route_pass_provisional** result — the final G2 pass requires the phase-level Holm family.

### Finding 4: One-Shot TEST — USTEC Power-Limited, XAUUSD Margin-Bound

- **Observation**: USTEC-4h: n=11, net=+45.22 bps but CI [−72.6, +158.7], boot_p=0.244. XAUUSD-4h: n=8, net=+21.59 bps, boot_p=0.001 but margin 54.2 > ci_low_1s 11.45.
- **Evidence**: test_verdicts.csv rows 2–3.
- **Interpretation**: USTEC is inconclusive as predeclared (power-limited at ~11 events). XAUUSD shows strong point evidence but the correct calibration margin blocks the pass — the cell's 8 events across 4 regime clusters cannot reliably distinguish signal from cluster-mean noise. Both are honest outcomes; neither is an experiment failure.

### Finding 5: FH-vs-BTC Companion (Non-Binding)

- **Observation**: On identical TEST events: EURUSD FH +40.56 vs BTC +24.27 (+16.29); USTEC FH +45.22 vs BTC −43.76 (+89.0 — driven by one extreme BTC adverse outcome in the small USTEC TEST set); XAUUSD FH +21.59 vs BTC +34.58 (−12.99).
- **Evidence**: test_verdicts.csv `fh_minus_btc_bps` column.
- **Interpretation**: The EURUSD capture-efficiency gain is the reliable signal. USTEC and XAUUSD comparisons are uninformative at these sample sizes. Non-binding per scope.

## Hypothesis Verdict

**ROUTE_PASS_PROVISIONAL_PENDING_PHASE_HOLM** (per predeclared criteria)

The experiment hypothesis is supported at the provisional level: EURUSD-4h produces a route_pass_provisional result (ci_low_1s > margin, within-route Holm p ≤ 0.05). The binding G2 adjudication (phase-level Holm family across all Phase 008 TEST p-values) is deferred to the checkpoint's `G2-gate-review.md`.

## Limitations

1. **Small TEST strata (n=8–12).** All three cells are at the power boundary of the frozen bootstrap. The null calibration corrects for anti-conservatism but the margin correction can be large (XAUUSD 54.2 bps).
2. **Single-shot TEST read.** The TEST stratum is evaluated exactly once, per design. No replication or cross-validation is possible within this experiment.
3. **No 5m/1h testing.** G1-B2 qualified only 4h (EXP-033 grid maxima ≤ 0 for 5m/1h). The FH exit was never tested on faster domains.
4. **XAUUSD cell count (n=8).** Below the ~13-event expectation from the power statement, driven by the all_legs policy being the only feasible choice.

## Alternative Explanations

- **EURUSD-4h provisional pass may be period-specific.** The TEST stratum covers late 2024–early 2025 price action. A different temporal sample within the analysis set (e.g., reversing TRAIN/TEST) could produce a different result. This is addressed by the holdout remaining sealed — the designated final arbiter.
- **The FH exit may not generalize to the BTC exit's event set.** The FH variant was tested on the same population as the BTC baseline (EXP-030/034 events), so the events are identical. The FH-vs-BTC comparison is within-event.

## Recommended Next Steps

1. **G2-gate-review.md adjudication** — combine EXP-037's raw p's and EXP-038's raw p in the phase-level Holm family. This is a desk artifact, not a new experiment.
2. **If G2 is satisfied** → EXP-032 holdout-release checkpoint becomes admissible (operator selects one package across EXP-037/038 candidates).
3. **If G2 is not satisfied** → Phase 008 routes CHARACTERISED_NOT_CONFIRMED; Tier C (Stage-C detectors, HYP-001) opens.
