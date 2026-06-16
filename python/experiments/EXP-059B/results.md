# Results: EXP-059B — Uncapped Structure Trailing (Conditioned HA Harami; `/EXIT-TRAIL-UNCAPPED`)

## Summary

Removing the benchmark time cap and initial stop from the structure trailing adverse-exit model does not improve conditioned HA harami capture. Neither binding arm — `TRAIL-PURE-UNCAPPED` (pure trailing, no cap, no initial stop) nor `COMBINED-UNCAPPED-V2A` (V2A partial legs on the same uncapped trailing scheme) — clears P11 (≥5 cells over ≥3 instruments with CI_low > 0 on own median expectancy and paired contrast vs BENCH > 0). The verdict is **EVIDENCE_AGAINST**: the trailing mechanism itself is the binding constraint, not the horizon.

The pure trailing arm is uniformly negative across all 99 cells — median expectancy −0.41 ATR in BTCUSD-5m — because removing the initial 1:1 stop exposes every position to unbounded adverse excursions before the first secondary ZigZag pivot confirmation can ratchet the stop. The V2A combined arm recovers marginally (1 viable cell, BTCUSD-5m) but still fails to beat the benchmark. The cap-isolation contrast confirms the finding: even among the 35–48% of events held past the benchmark cap, the uncapped model's divergent returns are not systematically positive (0/96 cells for pure TRAIL, 2/89 for COMBINED). The cap was not the constraint.

## Detailed Findings

### No binding arm clears P11

- **Observation**: 0 of 2 binding arms produce a single winning cell (viable + beats BENCH). The hypothesis is falsified per the predeclared mechanical rule.
- **Evidence**: `composition_readout.json` — verdict `EVIDENCE_AGAINST`, `n_pass: 0`, `passing_arms: []`. No arm has any cell where it is both viable (own CI_low > 0, m ≥ 30) and beats BENCH (paired contrast CI_low > 0). `per_arm_median_forest.png` shows all uncapped arm CIs straddle or lie below BENCH in virtually every cell.
- **Interpretation**: Uncapped trailing — with or without V2A partial legs — cannot rescue the conditioned signal's capture. The finding is informative, not power-limited: all 5 arms are powered in all 99 cells (≥30 qualifying events), and the INCONCLUSIVE_POWER_LIMITED scenario (flagged as "materially more likely" in scope due to high DATA_CENSORED from unbounded windows) did **not** materialize — total censored across all uncapped arms is 15–22 events, negligible against tens of thousands of qualifying events. `p11_wins_censoring.png` confirms ample power.

### Removing the initial stop dominates the result

- **Observation**: `TRAIL-PURE-UNCAPPED` has 0 viable cells (CI_low > 0 in 0/99) with uniformly negative median expectancy. In BTCUSD-5m, the best-case cell, median = −0.41 ATR (CI_low = −0.44). The mean is +0.10 — a fat right tail from rare runners does not offset the systematic adverse excursion damage.
- **Evidence**: `composition_readout.json` — TRAIL-PURE-UNCAPPED viable cells `[]`. Spot check per audit.
- **Interpretation**: Without the benchmark 1:1 initial stop, every position is exposed to unbounded adverse moves until the first post-entry secondary ZigZag pivot (0.5× ATR) confirms. This delay — often 1–3 bars in fast markets — is sufficient to produce large negative returns that dominate the median. The design principle "let it run" fails because the secondary `atr_mult=0.5` ratchet is too slow to capture adverse recovery, consistent with the EXP-059 finding that the trailing mechanism itself (capped) also underperformed the fixed exit.

### V2A partial legs help but not enough

- **Observation**: `COMBINED-UNCAPPED-V2A` raises median expectancy relative to pure trailing (BTCUSD-5m median = +0.08, CI_low = 0.01) — 1 viable cell — but still 0 wins. The paired vs-BENCH contrast in that cell is negative (CI_low < 0).
- **Evidence**: `composition_readout.json` — COMBINED-UNCAPPED-V2A viable: 1 cell (BTCUSD-5m); wins: 0 cells. Benchmarked by `arm_benchmark_contrast_heatmap.png` — the contrast heatmap is uniformly cold (no cell where the combined arm beats BENCH).
- **Interpretation**: The V2A fraction targets (1/3, 2/3, 1 × fav_dist) capture partial favourable excursion before the trailing stop fills, shifting the median upward from negative to barely positive in one cell. But the improvement is insufficient to clear the paired BENCH contrast — the trailing stop still binds on the remaining open weight, and when it does, it fills at a worse level than the fixed 1:1 exit would have for the position as a whole.

### The cap-isolation contrast shows the cap was not the constraint

- **Observation**: Even among the 35–48% of paired events that the uncapped arm holds past the benchmark cap (the *divergent subset*), the uncapped model does not systematically beat its capped no-init sibling: 0/96 divergent-positive cells for TRAIL-PURE, 2/89 for COMBINED.
- **Evidence**: `composition_readout.json` — `cap_isolation`: TRAIL-PURE median divergent share 48.3%, 0 divergent-positive cells; COMBINED median divergent share 35.8%, 2 divergent-positive cells (BTCUSD-30m, US2000-2h). `cap_isolation_contrast.png` — a sparse, scattered hot-spot map with no instrument-level cluster.
- **Interpretation**: The scope's ex-ante concern that the cap binds and distorts the trailing story is correct — the cap binds on ~half of events for the pure trailing arm. But removing the cap on those events does not help. The trailing stop, given enough rope, eventually fills at a worse price than the cap would have. This supports the interpretation that the trailing mechanism's secondary-pivot ratchet is the bottleneck, not the horizon.

### BENCH itself is weak — important caveat

- **Observation**: The benchmark fixed exit (50% fav / 1:1 stop / adaptive cap) is itself viable in only 9/99 cells (7 instruments). In 90/99 cells, BENCH's own CI spans 0.
- **Evidence**: `composition_readout.json` — BENCH viable: 9 cells, 7 instruments; wins: 0 (BENCH cannot "win" per the uncapped-only win rule, but its own viability is marginal).
- **Interpretation**: The conditioned `/STRONG-STAT` HA harami signal is not detectably positive under even the simplest adverse-exit model (fixed 1:1). The fact that two more aggressive exit models (uncapped trailing, V2A + trailing) also fail to beat this weak baseline means the constraint likely sits upstream — in the signal itself or in the favourable target geometry. Consistent with EXP-055 (move available peaks early) and EXP-057 (removing the adverse stop helped under the cap), the combined picture suggests the signal's MFE distribution is the primary limit.

## Hypothesis Verdict

**REFUTED* (formal: EVIDENCE_AGAINST)**

The hypothesis — that an uncapped structure trailing model, standalone or with V2A partials, would produce higher gross per-event median expectancy than the benchmark — is falsified. Neither binding arm clears P11.

Deliverable label: **UNCAPPED_TRAILING_CHARACTERISED** — recorded as a measured-negative characterization. Routing deferred to the single 014-B G2.

## Limitations

- **BENCH signal is weak in most cells (9/99 viable).** The EVIDENCE_AGAINST verdict describes "uncapped trailing does not beat the benchmark" but in most cells the benchmark itself does not produce detectably positive expectancy. The paired contrast captures "both arms ineffective" on those cells. G2 must read this alongside BENCH's own viability map (see audit Warning #1).
- **The vs-BENCH contrast is on the uncensored common subset.** It cannot speak to the (very few) censored events. With censoring at 15–22 total events across all cells, this is not a practical limitation here, but the principle holds.
- **No initial stop widens the return distribution.** The median endpoint (P14) is correct, but the mean is systematically positive in some cells where the median is negative — a reminder that the choice of median gates interpretation.
- **`ATR_MULT_TRAIL = 0.5` is frozen.** A finer-pivot secondary ZigZag (e.g., 0.3× ATR) might ratchet faster and contain adverse excursions sooner. This sensitivity is out of scope (registered as the `/THIRD-TIME` grid analog).
- **Gross only** — no cost model. The trailing stop's higher fill frequency and longer holds may incur higher transaction costs that would widen the gap further.
- **Only V2A partials are tested.** Other partial-exit schemes (V1, V3, reversal-based) were not paired with the uncapped trailing because EXP-059 showed V2A as the simplest broad performer that does not depend on the benchmark cap.

## Alternative Explanations

1. **The secondary ZigZag pivot ratchet is too slow.** With `atr_mult=0.5`, the trailing stop may confirm too late to protect against adverse moves in fast markets. A finer `atr_mult` (e.g., 0.3) or a different ratchet logic (e.g., trailing ATR channel) could change the result — but the family thesis treats the secondary pivot as the binding adverse-exit primitive; changing the ratchet would be a new countable branch.
2. **The signal's MFE peaks before the trailing stop can exploit it.** EXP-055 showed that the conditioned move's MFE distribution peaks within the first few bars. The trailing stop — which requires a secondary pivot to ratchet — may never lock in these early peaks before the move reverses. Consistent with the observation that most events resolve within the benchmark cap (even without one, the trailing stop fills quickly).
3. **The conditioning filter (/STRONG-STAT p75) may select for mean-reverting moves.** If the strongest moves are more likely to snap back, a "let it run" model is precisely wrong. This would explain why the capped exit (which clips at bar 6) outperforms the uncapped trailing (which waits longer for a worse fill). The V2A partials mitigate this partially (1/3, 2/3 legs capture early favourable excursion) but cannot overcome the trailing stop on the remaining weight.

## Recommended Next Steps

1. **Close `/EXIT-TRAIL-UNCAPPED` as a characterized negative.** No further investment in the single-uncapped-trailing branch for the conditioned HA harami population under the `atr_mult=0.5` secondary pivot ratchet.
2. **Route to G2.** The full 014-B position-management surface (EXP-056: favourable target geometry, EXP-057: adverse model alternatives, EXP-058: 3-barrier horizon, EXP-059: capped structure trailing, EXP-059B: uncapped trailing) is now characterised. G2 should assess the combined readout across all five experiments.
3. **Do not pursue a finer-pivot ratchet `/THIRD-TIME` grid** for the trailing stop on this population without re-evaluating the signal's MFE profile. EXP-055's MFE peak-timing analysis should inform whether any trailing scheme can systematically capture the conditioned move.
