# Results: EXP-031 — AVWAP Edge Isolation (Entry-Timing vs Exit-Rule)

## Summary

The EXP-028 per-event matched-control excess (+5.78 / +23.38 / +69.02 bps on 5m/1h/4h) was decomposed into entry-timing and exit-rule contributions under a predeclared additive decomposition. **The split is unresolved**: the attribution flips between entry-dominant and exit-dominant depending on the neutral exit horizon, with no domain showing agreement between H=1 and H=6.

At the PRIMARY horizon (H=6), entry timing contributes >100% of the total on every domain (s_entry = 1.53 on 5m, 1.13 on 1h), meaning the band-target/trend-change (BTC) exit is a net differential drag on bounce-entries relative to a neutral fixed-horizon exit. At the companion horizon (H=1), the exit rule dominates (s_exit = 0.80 on 5m), meaning the BTC exit adds significant differential value at very short horizons.

The horizon-contradictory pattern holds across all three domains and is itself the central finding: the entry/exit attribution is horizon-sensitive, and this experiment's predeclared resolution criterion (H=1 and H=6 agreement on the primary domain) is not met.

**Phase outcome**: ISOLATION_READ_UNRESOLVED.

## Detailed Findings

### Finding 1: Substrate validated (X_full replicates EXP-028 exactly)

The rebuilt X_full matched the EXP-028 PRIMARY effect to 0.0 bps on all three domains (5m: 5.7785, 1h: 23.3839, 4h: 69.0157). Per-event additivity holds to machine precision (max residual 3.55e-15 bps). The decomposition substrate is correctly wired.

### Finding 2: Entry-timing dominant at H=6 on every domain (PRIMARY horizon)

At the predeclared PRIMARY neutral horizon H=6:

| Domain | X_full (bps) | X_entry (bps) | X_exit (bps) | s_entry | s_exit | Label |
|--------|-------------|---------------|-------------|---------|--------|-------|
| 5m | 5.78 [5.40, 6.17] | **8.84** [8.36, 9.31] | −3.06 [−3.45, −2.69]† | 1.53 | −0.53 | ENTRY_DOMINANT |
| 1h | 23.38 [17.77, 29.46] | **26.53** [19.42, 34.15] | −3.15 [−8.63, 2.57]† | 1.13 | −0.13 | ENTRY_DOMINANT |
| 4h | 66.87 [45.77, 88.97] | **94.01** [67.18, 119.05] | −27.14 [−46.47, −7.44]† | 1.41 | −0.41 | ENTRY_DOMINANT |

*† Not leg-significant (CI spans zero).*

**Interpretation**: At the 6-bar horizon, entry timing carries more than the full excess on both reportable domains. The BTC exit is a differential *drag* on bounce-entries relative to a neutral fixed-horizon exit — it underperforms the passive exit on positions that entered at AVWAP bounces. This is consistent with exit-substitution data: on bounce-entries, the BTC exit subtracts 0.60 bps vs FH(6), while on control-entries it adds 2.47 bps.

### Finding 3: Exit-rule dominant at H=1 on every domain (companion horizon)

At the companion horizon H=1:

| Domain | X_full (bps) | X_entry (bps) | X_exit (bps) | s_entry | s_exit | Label |
|--------|-------------|---------------|-------------|---------|--------|-------|
| 5m | 5.78 [5.41, 6.17] | **1.16** [1.00, 1.32] | **4.61** [4.30, 4.96] | 0.20 | 0.80 | EXIT_DOMINANT |
| 1h | 23.38 [17.71, 29.74] | 0.01 [−2.58, 2.34]† | **23.37** [18.63, 28.81] | 0.00 | 1.00 | EXIT_DOMINANT |
| 4h | 69.02 [47.82, 90.25] | 7.99 [−0.90, 16.74]† | **61.03** [41.74, 81.90] | 0.12 | 0.88 | EXIT_DOMINANT |

*† Not leg-significant.*

**Interpretation**: At the 1-bar horizon, the BTC exit is the dominant driver. On 5m (the only domain where both legs are significant), the exit contributes 80% of the total. The exit-substitution data shows the mechanism: on bounce-entries, the BTC exit adds +0.42 bps vs FH(1), while on control-entries it *loses* −4.19 bps vs FH(1). The BTC exit therefore adds differential value specifically by avoiding adverse 1-bar moves on controls (the trend-change exit cuts losers early).

### Finding 4: H=1 vs H=6 label contradiction makes the split unresolved

| Domain | H=6 label | H=1 label | Agree? |
|--------|-----------|-----------|--------|
| 5m | ENTRY_DOMINANT | EXIT_DOMINANT | No |
| 1h | ENTRY_DOMINANT | EXIT_DOMINANT | No |
| 4h | ENTRY_DOMINANT | EXIT_DOMINANT | No |

Every domain flips between entry-dominant at the longer horizon and exit-dominant at the shorter horizon. The primary domain (5m) does not have H=1 and H=6 in agreement, so the predeclared ISOLATION_READ_UNRESOLVED outcome is triggered.

**Mechanism insight**: The flip is explained by the exit-substitution effect's horizon dependence. At H=1, the BTC exit's differential advantage on bounce-entries over controls is large and positive. At H=6, this advantage reverses — the BTC exit underperforms the fixed-horizon exit on bounce-entries but outperforms it on controls. The BTC exit is not uniformly beneficial: it adds value as a *loss-cutting* mechanism (short-horizon benefit) but removes value as a *trend-capturing* mechanism on bounce-entries at longer horizons.

## Hypothesis Verdict

**ISOLATION_READ_UNRESOLVED** (per scope §Success/Failure Criteria).

The predeclared condition for a resolved read was not met: the primary domain (5m) gives contradictory labels between H=6 (ENTRY_DOMINANT) and H=1 (EXIT_DOMINANT). The edge is real (X_full confirmed) and the decomposition is exact, but the attribution is horizon-sensitive — neither entry-timing nor the exit-rule dominates across both evaluation horizons.

This is a valid, informative result: the edge is *not* cleanly attributable to either the entry or the exit alone. Its character changes with the evaluation horizon, which constrains future scope design (see recommendations).

## Limitations

1. **Horizon sensitivity**: The primary finding (H=1 vs H=6 contradiction) means the attribution is a function of the neutral exit horizon, not a property of the strategy itself. A different predeclared horizon (e.g., H=3) could give a different result. The scope predeclared H=6 as PRIMARY and H=1 as companion, so a different choice is not a valid "better" answer — it would be a separate experiment.

2. **4h power**: 4h has only 185 events (n=187 before the NaN fix; 2 boundary events correctly excluded) with 3-4 reportable instruments. The 4h H=6 entry effects are now finite for all instruments (NaN issue fixed — see audit). The label (ENTRY_DOMINANT) was robust throughout and is now supported by finite point estimates.

3. **Gross decomposition**: This is a mechanism decomposition gross of costs. The entry-timing edge measured here is the bounce detector's ability to locate profitable entry points *before* costs — net tradability is EXP-030's separate question.

4. **Two-horizon snapshot**: The decomposition tested exactly two predeclared horizons {1, 6}. A more complete picture would require additional horizons, but that would be a new scope — not a permitted sweep here.

## Alternative Explanations

The horizon flip could reflect a structural property of the BTC exit: it acts as a **loss-cutter** at short horizons (exits trades that would reverse at H=1) but as a **trend-truncator** at longer horizons (exits trades that would have continued trending at H=6). The net effect on bounce-entries vs control-entries changes sign between these two regimes. This is a consistent, interpretable story that does not require the edge to be "truly" entry-dominant or exit-dominant — the split is horizon-dependent by construction.

## Recommended Next Steps

1. **Resolve the horizon ambiguity**: A follow-up experiment (provisionally EXP-033) could sweep H over a fine grid {1, 2, 3, 4, 5, 6, 12, 24} and report the entry/exit share curve as a function of H, on the primary domain (5m). This would reveal whether there is a crossover horizon where s_entry ≈ s_exit, and whether the attribution stabilizes at any H range. **Register as a new diagnostic (DIAG-004), not a candidate screen.** Predeclare the sweep before reading the EXP-031 results.

2. **Exit-overlay redesign (EXP-026/EXIT)**: The finding that the BTC exit is a differential drag on bounce-entries at H=6 but a benefit at H=1 informs the design of an exit that preserves the short-horizon loss-cutting while reducing the long-horizon trend-truncation. The shelf status of EXP-026 `/EXIT` should be re-evaluated with this information.

3. **HYP-001 line S/R test**: The unresolved isolation strengthens the case for testing HYP-001 directly (P(bounce | AVWAP approach) vs control levels), since the edge's mechanism is not cleanly localized to either entry or exit — the line itself may be doing work that this experiment cannot separate.
