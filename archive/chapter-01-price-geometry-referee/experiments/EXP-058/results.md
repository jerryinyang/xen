# Results: Experiment EXP-058 — Third-Barrier Geometry (Conditioned HA Harami; `/THIRD-TIME`, `/THIRD-EVENT` vs Benchmark Adaptive Cap)

## Summary

**Verdict: EVIDENCE_AGAINST** — no alternative third-barrier variant clears the P11 quorum on the binding endpoint. Raising the floor from 6 to 12/24/48 (`/THIRD-TIME`) or switching to an event-based structural exit (`/THIRD-EVENT`: next ZigZag `rd`-direction confirmation with 8× backstop) does not produce higher gross per-event median expectancy (P14, ATR-normalised, P15 fills) than the benchmark floor-6 adaptive time cap, on the `/STRONG-STAT`-conditioned HA harami population across the 99-cell grid. The result is a valid measured-negative characterization feeding the single 014-B G2; no candidate is registered, no gate is adjudicated here.

**0 candidate slots, 0 TEST reads, TRAIN-only, gross.** All defect gates PASS — determinism OK, causality OK, invariant checks OK (cap monotonicity in floor, `/THIRD-EVENT` cap bounds, warmup-set identity across time variants), EXP-053 reconciliation 99/99 cells to ≤1e-9 precision. The experiment has adequate power (99/99 cells powered for every variant) and the EVIDENCE_AGAINST classification is mechanical, not a power failure.

---

## Detailed Findings

### 1. No alternative third-barrier variant wins at P11 quorum

| Variant | Powered (m≥30) | Viable (CI_low>0) | Win (viable + beats_bench) | P11 pass? (≥5 cells, ≥3 instr) |
|---------|-------|--------|-----|----------|
| BENCH (reference) | 99 | 8 | 0 (N/A) | N/A |
| THIRD-TIME-T12 | 99 | 6 | 3 (BTCUSD-30m, XAUUSD-1h, USDCAD-5m) | No (3<5) |
| THIRD-TIME-T24 | 99 | 4 | 2 (XAUUSD-15m, USDCAD-5m) | No (2<5) |
| THIRD-TIME-T48 | 99 | 2 | 2 (BTCUSD-30m, USDCAD-5m) | No (2<5) |
| THIRD-EVENT | 99 | 1 | 0 | No (0<5) |

Every alternative third-barrier variant has adequate powered cells (99/99), but none reaches the required 5 winning cells over 3 instruments. THIRD-TIME-T12 comes closest with 3 wins across 3 instruments (BTCUSD-30m, XAUUSD-1h, USDCAD-5m), but this is below the P11 quorum. The mechanical EVIDENCE_AGAINST classification fires because `bench_pow=True` AND `alt_pow=True` AND `passers=[]` — adequate power exists to adjudicate, but no alternative beats the benchmark at P11 breadth.

**The per-variant forest plot** (`plots/per_variant_median_forest.png`) shows each alternative's per-cell median expectancy with one-sided CI_low whiskers, overlaid on the benchmark reference. The suppressing-viability effect is visible as the floor rises: the median expectancy mass does not shift upward systematically; rather, the number of cells whose CI_low clears zero shrinks.

### 2. The censoring/horizon trade-off is the headline diagnostic

Raising the floor depletes viable and win counts systematically:

| Variant | Floor | Viable cells | Win cells |
|---------|-------|-------------|-----------|
| BENCH | 6 | 8 | — |
| THIRD-TIME-T12 | 12 | 6 | 3 |
| THIRD-TIME-T24 | 24 | 4 | 2 |
| THIRD-TIME-T48 | 48 | 2 | 2 |
| THIRD-EVENT | event | 1 | 0 |

**Power is not the constraint** — all 99 cells remain powered (≥30 qualifying events) for every variant. The censoring fraction (`DATA_CENSORED` / built window) rises with the horizon, but not enough to push any cell below the 30-event power floor. Instead, the longer windows let TIMECAP exits drift toward zero or negative median: extra time admits symmetric noise, and the TIMECAP exit price — the channel through which the third-barrier lever moves expectancy — does not land systematically favourably. First-hit `r` stays near 0.50 across all variants (as expected under fixed 1:1 favourable/adverse geometry), confirming the lever works through TIMECAP composition and exit price, not through the FAV/ADV ratio.

**The censoring/power trade-off plot** (`plots/censoring_power_tradeoff.png`) visualises this: the DATA_CENSORED fraction grows (a cost of longer horizons), but it is the viability loss (CI_low crossing zero) that is the binding constraint — extra time does not transform TIMECAP'd events into favourable outcomes often enough.

**The return distribution plot** (`plots/return_distribution_by_variant.png`) shows the mechanism: as the horizon lengthens from floor=6→12→24→48 and to the event barrier, the return distribution mass does not shift rightward; it spreads. The median stays near zero or becomes negative in cells that were marginally positive at floor=6, because longer windows give the adverse target as much extra time as the favourable target (symmetric 1:1 geometry).

### 3. Pattern mirrors EXP-056: the benchmark 50%-of-M_sofar / 1:1 / adaptive-cap geometry is apparently optimal

EXP-056 (favourable-target OAT) returned EVIDENCE_AGAINST on the same conditioned population — no `/VPTARGET`/`/MAGTARGET` combination beat the benchmark 50% favourable configuration at P11 quorum. EXP-058 now returns the same classification on the third-barrier axis. Together, these two results suggest that the benchmark geometry (favourable = 50%-of-M_sofar, adverse = 1:1, third-barrier = floor-6 adaptive cap) sits at a local optimum on at least two orthogonal surface legs of the 014-B design: changing any single barrier either degrades expectancy or does not improve it with adequate power.

The economic mechanism is coherent across both experiments:
- **EXP-056**: changing the favourable target away from 50%-of-M_sofar does not improve expectancy (the benchmark already balances reach vs censoring).
- **EXP-058**: changing the third-barrier horizon (time or event) does not improve expectancy (the benchmark floor-6 already captures the available near-term resolution while avoiding symmetric noise from longer holds).

The **variant−benchmark contrast heatmap** (`plots/variant_benchmark_contrast_heatmap.png`) shows the per-cell pattern sparse and scattered — a few isolated cells (USDCAD-5m, BTCUSD-30m) flicker positive for some variants, but no coherent instrument/timeframe pattern emerges that would survive P11 breadth.

### 4. THIRD-EVENT is the weakest performer

The event-based third barrier — hold until the ZigZag confirms the next reversal-direction (`rd`) move, backstopped at 8× the benchmark cap — produces 1 viable cell and 0 win cells. This is the poorest result among all five variants.

The mechanism is anticipated in the scope: the ZigZag `rd`-confirm event often arrives too far out (the position has already resolved FAV/ADV, or the backstop binds), and when it does bind at or before a target, the `rd`-confirm bar's close does not systematically improve on the floor-6 adaptive cap. The event cap is a structural "give-up" rule that releases the position when the substrate itself confirms the reversal — but the data show this rule is costlier than the time cap at floor=6, not a superior alternative.

**The r + wins composition plot** (`plots/r_and_wins_composition.png`) shows the instrument × domain grid for THIRD-EVENT nearly blank on the win dimension — only GBPUSD-4h shows viability, and even that does not beat the benchmark.

### 5. Defect gates confirm the result is trustworthy

| Gate | Status |
|------|--------|
| Determinism (17 cells re-run, all 5 variants + baselines) | PASS |
| Causality violations | 0 |
| Invariants (cap monotonicity, `/THIRD-EVENT` bounds, warmup-set identity) | All PASS |
| EXP-053 reconciliation (99/99 cells, median + `r` + count to 1e-9) | PASS |

The EXP-053 reconciliation confirms the benchmark BENCH variant reproduces the earlier experiment exactly — same conditioned population, same median expectancy, same `r`. The invariant checks confirm that the longer floors produce monotone non-decreasing caps event-wise, `/THIRD-EVENT` caps respect `1 ≤ n_event ≤ 8×bench_N` with forward `rd`-confirm exits, and the warmup mask is identical across all time variants as expected.

---

## Hypothesis Verdict

**EVIDENCE_AGAINST** — The hypothesis that at least one alternative third-barrier geometry (`/THIRD-TIME` floor ∈ {12, 24, 48}; `/THIRD-EVENT` with ZigZag-`rd`-confirm and 8× backstop) produces higher gross per-event median expectancy than the benchmark floor-6 adaptive cap is **not supported**. No variant clears the P11 quorum (≥5 cells over ≥3 instruments) on the binding win endpoint.

This is a **measured-negative characterization** — not a power failure, not an inconclusive result, not a defect. The experiment has adequate power (99/99 cells powered across all variants), the methods are correct, and the data show a clear pattern: extending the holding horizon does not improve conditioned capture on benchmark favourable/adverse geometry. The deliverable label is `THIRD_BARRIER_CHARACTERISED`, feeding the single 014-B G2 across the full surface.

---

## Limitations

1. **Gross-only**: No costs (spread, slippage, commission) are modelled. The relative ranking of variants could shift under realistic cost assumptions — particularly for longer horizons where per-event ATR-normalised return is smaller and costs are a larger fraction.

2. **P15 fill approximation**: The intrabar path (`O→L→H→C` bullish, `O→H→L→C` bearish) is an approximation of unobserved intrabar motion, not a full tick replay. EXP-054 bounded its median impact at Δr ≈ 0.010 ATR units. The contrast between variants is unbiased (same approximation applies to all variants), but absolute expectancy levels carry this caveat.

3. **TRAIN-only**: All results are on the first-49% TRAIN slice. The nested TEST (final 30% of analysis set) and the final-30% global holdout remain sealed. Cross-validation performance of the benchmark vs alternatives on unseen data is unknown.

4. **One-at-a-time (OAT) variation only**: Only the third barrier is varied. Combinations of third-barrier changes with favourable-target changes (EXP-056) or adverse-target changes (EXP-057) are not tested here — that interaction is EXP-060. The benchmark may be a local optimum on each individual axis while a combined lever unlocks improvement.

5. **Operator-defined variant grid**: The `/THIRD-TIME` grid is floor-only (k=1.5, window=20 fixed) and the `/THIRD-EVENT` backstop is 8× bench_N. A different choice of k, window, or backstop multiplier could produce different results. These were predeclared operator decisions, not tuned.

---

## Alternative Explanations

1. **The benchmark floor-6 adaptive cap may already approximate the optimal horizon.** The P4 cap collapsed to floor=6 in 96/99 cells (014-A G1), meaning the 1.5×median trailing duration term is ≤ 6 bars in nearly every cell. Six bars is short enough that TIMECAP exits cluster near the entry price (limiting both upside and downside from the "left on close" effect), while longer horizons admit symmetric additional noise from both favourable and adverse sides.

2. **EXP-055's AVAILABILITY_GOOD (the lifetime reversal move exists) does not imply it can be captured as expectancy.** The lifetime move may arrive too late or be cancelled out by the adverse-side exposure during the extended hold. The censoring cost of waiting for it (lost qualifying events) outweighs the benefit from the few events where it pays off.

3. **The `/THIRD-EVENT` barrier is structurally disadvantaged.** The ZigZag `rd`-confirm event is a *confirmation* of the fade — by the time the substrate confirms the reversal, the favourable resolution may already have happened (or the window is dominated by the backstop, which is just a longer time cap). The event barrier was designed as a "give-up" rule but may simply be a worse time cap.

4. **The result is consistent with a symmetric path under 1:1 adverse geometry.** With favourable and adverse equidistant, extra holding time gives both targets equal opportunity. There is no asymmetry for the third-barrier lever to exploit — the benchmark's short floor-6 cap already exits before symmetric noise dominates.

---

## Recommended Next Steps

1. **Route EXP-058's `THIRD_BARRIER_CHARACTERISED` readout to the single 014-B G2** alongside EXP-056 (favourable OAT) and EXP-057 (adverse OAT) for family-wise assessment across the full surface.

2. **EXP-060 (combined levers)** — test whether combinations of third-barrier changes with favourable-target or adverse-target changes unlock improvement that OAT variation does not. The benchmark may be a local joint optimum, or the interaction may reveal a configuration that survives P11.

3. **Consider EXP-058's censoring narrative in EXP-059 (exit overlays).** The finding that longer horizons deplete viability via symmetric noise (not just via censoring counts) informs the design of partial-exit and trailing-stop variants: exit overlays that cut losing TIMECAP positions early may preserve the horizon extension's upside while mitigating its downside.
