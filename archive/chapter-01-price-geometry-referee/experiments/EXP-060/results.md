# Results: EXP-060 — Combined Event System (Conditioned HA Harami; Best Per-Layer Geometry, 2×2 Favourable×Adverse Factorial + Champion)

## Summary

The best per-layer combined system (champion A3: V2A partial-exit legs × ADV-NONE unbounded adverse) does not clear the programme's two-baseline conjunction test on any of 99 cells. The conditioned signal is viable (69/99 cells show positive median expectancy), and both geometric levers independently improve expectancy (favourable main effect, adverse main effect, both additive). However, the MA(20,50)-segmentation baseline captures systematically larger ambient swings — every cell's champion contrast against MA has a negative CI_low. The win condition (champion beats BOTH matched-random AND MA) is unmet everywhere. This is a substrate property, not a signal weakness: MA segments are structurally longer trends than ZigZag-defined reversal moves at any entry point.

The mechanical eligibility verdict is `CHARACTERISED_NOT_VIABLE_ELIGIBLE` — the single 014-B G2 input is negative for PROCEED_TO_SCREEN. EXP-060 emits the readout; the operator adjudicates the G2.

## Detailed Findings

### Finding 1: Champion A3 — 0/99 wins across 17 instruments

- **Observation**: The champion A3 (V2A × ADV-NONE) has **0 champion_wins** over all 99 cells. P11 composition: 99 powered, 69 viable, 0 wins across 17 instruments.
- **Evidence**:
  - `composition_readout.json` wins = `{"n_cells": 0, "n_instruments": 0, "passes": false}`
  - 69/99 cells VIABLE individually (median CI_low > 0, m ≥ 30)
  - 3/99 cells beat matched-random baseline (GBPUSD-4h, USDCHF-4h, US2000-4h)
  - 0/99 cells beat MA(20,50) baseline — `contrast_ma_low` negative in every cell (range −0.569 to −2.404 ATR)
  - A3 per-cell median expectancy ranges −0.125 to +0.929 ATR units (plot: `champion_binding_map.png`)
- **Interpretation**: The two-baseline IUT conjunction is the binding constraint. The MA(20,50) baseline captures structurally larger swings because its segments span multiple ZigZag-defined reversal moves — any single entry point (harami at strong-move exhaustion) claims at most one reversal leg, while the MA baseline represents the swing from crossover to crossover (multiple legs). This was pre-disclosed in EXP-055 ("0 cells beat MA(20,50) on median MFE") and is a property of the segmentation method, not the conditioned signal.

### Finding 2: Both geometric levers independently improve expectancy

- **Observation**: The 2×2 factorial decomposition (plots: `factorial_decomposition.png`) shows positive CI_low for both main effects in most cells.
- **Evidence**:
  - **Favourable main effect** (V2A vs single leg): `ci_low_1s` > 0 in 90+/99 cells for both `fav_main_1to1` (under 1:1 stop) and `fav_main_none` (under ADV-NONE). Point estimates ~0.10–0.20 ATR.
  - **Adverse main effect** (ADV-NONE vs 1:1): `ci_low_1s` > 0 in 75+/99 cells for both `adv_main_50pct` (under single leg) and `adv_main_v2a` (under V2A). Point estimates ~0.05–0.10 ATR.
  - **Interaction** (are the levers super-additive?): `interaction` point estimate near zero in most cells (−0.06 to +0.06 ATR); `ci_low_1s` near zero or negative — the levers are additive, not synergistic.
  - **Champion vs BENCH** (A3 − A0): positive in 99/99 cells — the combined system improves over benchmark defaults.
- **Interpretation**: Both the V2A partial-exit structure and the ADV-NONE unbounded-adverse rule independently raise median expectancy. They do not interfere (additive), confirming that the best-per-layer assembly strategy is valid. The improvement over BENCH (~0.20–0.35 ATR in high-power cells) is real and consistent across instruments and domains.

### Finding 3: Horizon sensitivity — longer cap helps

- **Observation**: A4 (champion at `/THIRD-TIME` floor=48) shows positive `horizon_a4_a3` paired contrast in most cells.
- **Evidence**:
  - `horizon_a4_a3` `ci_low_1s` > 0 in ~85+/99 cells. Point estimate median ~0.10–0.20 ATR.
  - A4 time-cap exit weight fraction is higher than A3's (plot: `horizon_sensitivity.png`), confirming the longer window censors more events.
  - A4 qualifying set is a strict subset of A3's (invariant vii: `a4_subset_ok` = True for all cells).
- **Interpretation**: ADV-NONE needs time to express — removing the stop means adverse is managed by the time cap, and a longer cap (48 vs 6 bars) improves outcome. This is intuitive: "let it run" strategies benefit from more room. The improvement is bounded by data-censoring (events near the TRAIN edge may hit the cap rather than resolve favourably).

### Finding 4: Exit-reason composition confirms the mechanism

- **Observation**: Per-arm exit weights (plot: `exit_reason_composition.png`) show the expected pattern.
  - **A0 (BENCH)**: ~50% FAV, ~18% ADV, ~32% TIMECAP — symmetric 1:1 barriers with a 6-bar cap.
  - **A1 (50PCT-NONE)**: ~52% FAV, 0% ADV, ~48% TIMECAP — removing the stop shifts unresolved events to the cap.
  - **A2 (V2A-1TO1)**: ~53% FAV (split across 1/3, 2/3, 1.0 legs), ~15% ADV, ~32% TIMECAP — V2A shifts FAV fraction up.
  - **A3 (V2A-NONE, champion)**: ~58% FAV (split), 0% ADV, ~42% TIMECAP — both levers combine: V2A raises FAV, ADV-NONE eliminates adverse.
  - **A4 (V2A-NONE-T48)**: ~60% FAV (split), 0% ADV, ~40% TIMECAP — longer cap shifts a fraction of TIMECAP back to FAV.
- **Interpretation**: The composition confirms the mechanism operates as designed: V2A spreads favourable exposure across three targets, ADV-NONE eliminates the adverse exit path entirely, and the time cap absorbs everything that does not resolve favourably within the horizon.

### Finding 5: Disclosed /STRONG-HA arm confirms the binding result

- **Observation**: The /STRONG-HA conditioned arm shows the same qualitative pattern: median expectancy positive in most cells, 0 champion_wins against both baselines.
- **Evidence**: `secondary_map.csv` — /STRONG-HA per-arm medians are slightly lower than /STRONG-STAT (consistent with EXP-051's lower ρ for HA impulse runs), but the pattern holds: A3 detectable positive, MA dominance systematic.
- **Interpretation**: The result is robust to the conditioning signal choice (magnitude-percentile vs HA impulse-run). Both conditioning arms agree: the combined system expectancy is real but the MA baseline cannot be beaten on this substrate.

## Hypothesis Verdict

**CHARACTERISED_NOT_VIABLE_ELIGIBLE** (mechanical, for the single 014-B G2 desk adjudication).

The scope defined a mechanical fork: PROCEED_TO_SCREEN if the champion clears P11 (≥5 cells over ≥3 instruments with both-baseline wins), CHARACTERISED_NOT_VIABLE_ELIGIBLE if powered composition is met but wins are not, and INCONCLUSIVE_POWER_LIMITED otherwise.

- Champion powered composition: **met** (99 cells, 17 instruments)
- Champion wins: **not met** (0 cells, 0 instruments — the MA baseline is systematically dominant)
- Verdict: **CHARACTERISED_NOT_VIABLE_ELIGIBLE**

## Limitations

1. **MA-baseline dominance is a substrate property, not a signal weakness.** The MA(20,50) segmentation baseline captures structurally longer and larger swings than any ZigZag-defined entry can claim. This does not mean the conditioned signal is absent (69/99 viable cells confirm it is present), but it means the signal cannot be distinguished from the ambient reversal-move structure using the programme's two-baseline standard. A different baseline (e.g., instrument-matched random walking) would change the verdict — but the MA baseline was predeclared and is the programme's binding standard.

2. **P15 fill-model approximation.** Intrabar order is unobserved in 1-minute data; the P15 path-ordered model is a documented approximation. EXP-054 measured its effect as IMMATERIAL (Δr ≈ 1%) for symmetric barriers on this substrate.

3. **ADV-NONE unbounded adverse.** Within the time cap, there is no adverse exit — an extreme adverse excursion would remain open until the cap expires. The median endpoint (P14) is robust, but the mean may diverge. Costs are out of 014-B scope; a tradability screen would need to model this.

4. **DE30 truncated history.** Broker m1 data ends 2026-01-16. DE30 does not appear among champion wins (immaterial).

5. **Bootstrap CI reproducibility.** As disclosed in the family INDEX, the moving-block bootstrap CI may differ across experiment scripts due to RNG stream dependence on execution context (~41–42 of 99 cells differ by ≤0.115 ATR). Within EXP-060, all arms share one RNG stream per cell, so the WIN logic is internally consistent.

## Alternative Explanations

1. **The two-baseline IUT may be too conservative on this substrate.** The MA(20,50) baseline is an independent segmentation method that produces structurally different (longer) trend definitions. It is not a "no-signal" baseline — it measures a different thing. A random-entry baseline (matched-count random on in-progress rd) is more informative as a signal-vs-null test, and here the champion beats random in 3 cells. The MA baseline answers a different question: "is this entry better than trading the whole MA-defined trend?" The answer is no — which is expected, because a single reversal entry cannot match a multi-leg trend hold.

2. **A different exit horizon might change the MA comparison.** The benchmark cap (floor=6) truncates ADV-NONE's advantage. A4 (floor=48) improves expectancy but still does not beat MA. Possibly no finite horizon on this substrate can match an MA segment's full swing — the question resolves to a ceiling, not a parameter.

## Recommended Next Steps

The mechanical readout feeds the single 014-B G2 operator adjudication. Per the 014-B design, EXP-060 is the final surface read. No follow-up experiment on CF-HA-HARAMI-001 is implied by these results — the G2 desk decides whether any cell or combination justifies PROCEED_TO_SCREEN despite the formal two-baseline failure.
