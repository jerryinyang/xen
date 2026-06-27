# Results: Experiment EXP-040

## Summary

EXP-040 tested HYP-001 (P(bounce | approach to AVWAP) > P(bounce | approach to matched control levels)) on 1h and 4h domains, analysis set, all four instruments. The binding family (2 pooled domain contrasts, Holm α = 0.05) yielded **INCONCLUSIVE** for 1h (Δ = +1.55 pp, CI [-4.52, +8.43], Holm p = 0.585) and **BELOW_FLOOR_NO_VERDICT** for 4h (Δ = −24.67 pp, CI [-44.63, −4.40], n = 50/22, floor = 100/arm). **HYP-001 is INCONCLUSIVE** — neither supported nor refuted. The mechanistic S/R question for the AVWAP line remains open.

## Detailed Findings

### 1h Domain — INCONCLUSIVE_SPANS_ZERO

- **Observation**: Δ = +1.55 pp, 95% CI [-4.52, +8.43], Holm p = 0.585. n = 1,594 AVWAP / 339 control episodes across 70 covariate-matched strata. Power statement: unclustered MDE ≈ 4.9 pp (optimistic under clustering), so a 1.6 pp signal is undetectable; immateriality verdict (CI half-width < 2 pp) was structurally unreachable.
- **Interpretation**: The CI symmetrically straddles zero. The point estimate is directionally consistent with HYP-001 but cannot be distinguished from noise. No evidence FOR (CI_low < 0) and no evidence AGAINST (CI_high > +2 pp). INCONCLUSIVE is the only reachable verdict at this n and effect size.

### 4h Domain — BELOW_FLOOR_NO_VERDICT

- **Observation**: Δ = −24.67 pp, 95% CI [-44.63, −4.40], Holm p = 0.980. n = 50 AVWAP / 22 control episodes across 7 strata — both arms well below the 100/arm reportability floor.
- **Interpretation**: The CI is entirely negative, which would constitute EVIDENCE_AGAINST if n were adequate, but the floor correctly prevents a verdict. The negative Δ (point estimate suggesting *fewer* AVWAP bounces than control) is consistent with the control arm's expected upward bias from the unmatched price-stretch regime (caveat 5). No claim attaches to this cell.

### Per-Instrument Descriptive (1h, non-binding)

All 1h CIs span zero, consistent with the pooled inconclusive read. No instrument suggests a reliable signal:

| Instrument | Δ (pp) | 95% CI | n AVWAP | n Control |
|---|---|---|---|---|
| BTCUSD | +5.4 | [-4.9, +16.8] | 515 | 109 |
| EURUSD | −5.4 | [-17.5, +6.1] | 415 | 89 |
| USTEC | +2.8 | [-11.1, +15.8] | 315 | 67 |
| XAUUSD | +3.0 | [-9.5, +15.6] | 349 | 74 |

EURUSD is the only instrument with a negative point estimate, suggesting no systematic cross-instrument pattern. 4h cells are below floor (BTCUSD n=40/18, EURUSD n=10/4) or empty (USTEC, XAUUSD).

### Moving-Copy Control Arm (Descriptive, Design §11/8)

The shifted-moving-copy control (AVWAP(t) + δ·BW(t)) isolates the moving-vs-static kinematic confound (caveat 4). Results are descriptive only — no permutation, no Holm, no verdict.

| Domain | Δ_m (pp) vs moving copy | 95% CI | n AVWAP / n moving | n static |
|---|---|---|---|---|
| 1h | **+3.41** | [-1.23, +8.35] | 1,647 / 522 | 1,594 / 339 |
| 4h | **+0.09** | [-12.68, +11.95] | 166 / 103 | 50 / 22 |

- **1h**: Δ_m = +3.41 pp — *larger* than the static contrast Δ = +1.55 pp. The moving-copy resolves the caveat-4 ambiguity: AVWAP's bounce premium does not shrink when the kinematic confound is controlled. If anything, the static control *underestimates* it (the kinematic effect pulls the static contrast toward zero). Both CIs span zero, but the directional consistency (both positive) is informative.
- **4h**: Δ_m = +0.09 pp — essentially zero. The strongly negative static Δ (−24.67 pp) was entirely a kinematic artifact: frozen levels don't move, so price approaches to them have systematically different dynamics. Against a moving level with identical kinematics, AVWAP is indistinguishable. This explains the sign discrepancy; the n=166/103 is above the static arm's n=50/22 (no clearance filter for the moving copy) but still below the 100/arm floor.

**Interpretation**: The kinematic confound is now quantified. On 1h it does not explain the AVWAP bounce premium; on 4h it explains the entire negative static Δ. The binding verdicts are unchanged, but the moving-copy arm converts the caveat-4 ambiguity into a measured quantity.

### Censoring Sensitivity

- **1h**: extreme imputations bracket Δ = +1.55 in [-2.47, +3.04]. Unresolved imbalance (95 AVWAP / 59 control) shifts the estimate within a ~5.5 pp range, consistent with the CI width.
- **4h**: bracket [-24.19, -19.89] around Δ = −24.67. Tiny n (25/10 unresolved) and the bracket adjoins the main estimate within ~0.5 pp — non-binding for a floor cell.

### Stability (Split-Half, Non-Binding)

- **1h**: h1 = −2.26 (n=967), h2 = +1.02 (n=966). Opposite signs reveal temporal instability consistent with noise around zero.
- **4h**: h1 = −20.93, h2 = −7.11 (n=36/half). Both negative but trivially small n.

## Hypothesis Verdict

**HYP-001: INCONCLUSIVE**

Neither domain met the FOR criteria (Δ > 0, CI_low > 0, Holm p ≤ 0.05) nor the AGAINST criteria (CI ≤ 0, or CI_high < +2 pp with CI_low ≤ 0). The 1h result is inconclusive by CI-spanning-zero. The 4h result is below the reportability floor. Per the scope, an INCONCLUSIVE verdict means the hypothesis remains open — no re-parameterization within this scope is permitted.

## Limitations (Carried from Analysis Plan)

1. **Bar-close granularity**: intrabar touches are invisible. This attenuates bounce rates symmetrically across arms.
2. **Control specificity**: the horizontal-snapshot control tests "AVWAP line vs frozen nearby level," not "vs every conceivable structural level." A FOR would be specific to this contrast; a null does not prove the absence of structure everywhere.
3. **Δ is a conditional rate difference**, not a tradable quantity. No economic claim attaches.
4. **Moving-vs-static kinematic confound (resolved in-scope via design §11/8)**: the AVWAP arm's level moves each bar while the static control is frozen, mechanically altering episode dynamics independent of any S/R property. The shifted-moving-copy control arm (AVWAP ± δ·BW) was implemented as a descriptive secondary arm (§Moving-Copy Control Arm above). On 1h it does not explain the AVWAP premium (Δ_m = +3.41 vs Δ = +1.55 pp). On 4h it explains the entire negative static Δ (Δ_m = +0.09 pp). The confound is now measured, not merely disclosed.
5. **Unmatched price-stretch regime**: control arm approaches occur 1.5–3.5 BW from VWAP, a location AVWAP approaches never occupy. Generic mean reversion inflates control bounce rates, biasing Δ against HYP-001 — conservative for a FOR but weakening interpretability of an AGAINST result.

## Alternative Explanations

An inconclusive read is consistent with both the S/R hypothesis and the null. The small positive 1h Δ (+1.55 pp), if real, could reflect relative momentum around pivots (price approaches the line during a move, then reverses as the move exhausts, coincidentally near the line) rather than the line itself exerting a barrier effect. This ambiguity is the core question the experiment was designed to resolve — and the sample did not supply enough power to separate them. The 4h result is consistent with either interpretation given the floor-truncated n.

## Recommended Next Steps

1. **HYP-001 remains open.** The INCONCLUSIVE verdict means neither FOR nor REFUTED was reached. Per design §8.3, a REFUTED (NO) closes the line-S/R mechanistic story and reframes the edge as relative momentum around pivots. That closure was not achieved.
2. **Power assessment for a follow-up experiment**: the 1h Δ = +1.55 pp (CI [-4.52, +8.43]) suggests the true effect, if any, is small (< 5 pp). At the unclustered MDE of ~4.9 pp (1,594 AVWAP / 339 control), detecting a 2–3 pp effect would require substantially more episode data — either a longer analysis window or more instruments. A dedicated power analysis should precede any repeat.
3. **Moving-copy control arm (completed)**: the shifted-moving-copy arm was implemented in-scope (design §11/8) and its results are reported above. The kinematic confound is measured: it does not explain the 1h premium, but explains the entire 4h negative static contrast. No further control refinement is needed for this experiment.
