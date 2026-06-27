# Results: Experiment EXP-095 (D0-amendment-001 rerun)

**Portfolio Construction & Online-Adaptive Risk Model (RSI-2 Fade, 8 confirmed cells)** · `CF-MR-001`/`HYP-003` ·
Phase 022 (batch 3) · **analysis-set only — NO holdout verdict.**

*Interpretation of the amendment rerun (`results/` regenerated 2026-06-24T22:53Z; audit.md re-audit = PASS). The
amendment (predeclared before this re-read) restored the D0 §D2.1 **intra-1h mark-to-market** (A1), re-specified
the benefit criterion as **like-for-like** portfolio Sharpe lower bound vs a **deployment-realistic cross-cell
median** single-cell lower bound (A2), made **Calmar/CVaR/Ulcer co-binding** (A3), and replaced the fixed-Sharpe=1.0
bite-check with an **MDE-curve** (A4). This supersedes the prior (flat-at-exit) reading. Binding figure = the
portfolio annualized-Sharpe MBB one-sided lower bound; all reads are descriptive on the analysis set and decide no
deployment verdict (that is EXP-097 under the G-022a-frozen rule).*

## Summary

Correcting the booking from flat-at-exit to **intra-1h mark-to-market** changed the verdict: the causal,
parameter-free **ERC portfolio now adds value decisively and robustly**. Portfolio A (static ERC) annualized
Sharpe **11.69 (lo 10.24)**, MaxDD **0.034**, Calmar 71.8 (lo 61.3); its Sharpe lower bound **exceeds every one of
the 8 constituent cells, the best single cell on both point (8.73) and lower bound (7.53), the cross-cell median
baseline (4.99) by +5.25, and the naive inverse-vol contrast (lo 10.07)** — the benefit criterion is **MET on every
baseline**. The mechanism is **genuine moment-to-moment diversification**: 8 cells at mean cross-cell correlation
**0.10**, marked continuously, average down to a portfolio MaxDD (0.034) **below every constituent** — a benefit
the lumpy flat-at-exit booking was *hiding* (the audit verified the marks are causal and inject real per-cell
adverse excursions, so this is a faithful measurement correction, not an artifact). **Two prior findings reverse:**
ERC now **≈ naive-IV** (marginally ahead, not "refuted by" it), and the **circuit-breaker is NEUTRAL** — A and B
are statistically indistinguishable (Sharpe LB 10.24 vs 10.19; MaxDD 3.44% vs 3.75%; B marginally *better* on
Ulcer), so the prior run's "B de-risks (−22.4% MaxDD)" is not reproduced — no material benefit, but no degradation
either. The new gate statistic is now **READY** (`statistic_ready_for_g022a=true`):
FPR controlled (A 0.000 / B 0.002) and the MDE-curve resolves a finite detectable margin (m* = 1.75 / 2.00) that
the realized edge (lo 10.24) clears comfortably — the recurring fixed-plant bite defect is fixed. **Caveat held
prominent:** Sharpe ~11–12 is an **in-sample, favorable-selected** magnitude, not a deployment estimate; the
binding deployment read is EXP-097.

## Detailed Findings

### Finding 1 — ERC portfolio adds value, robustly across every baseline (the corrected main read)

- **Observation:** Portfolio A Sharpe **11.69 (lo 10.24)**, B **11.57 (lo 10.19)**. The binding object — the Sharpe
  **lower bound** — clears every benchmark:

  | Baseline | Value | A LB (10.24) margin | Disposition |
  |---|---|---|---|
  | Cross-cell **median** single-cell Sharpe LB (deployment-realistic, binding) | 4.99 | **+5.25** | ADDS_VALUE |
  | Best single cell — **point** (US2000-1h) | 8.73 | +1.51 | clears |
  | Best single cell — **lower bound** | 7.53 | **+2.71** | ADDS_VALUE |
  | Naive inverse-vol — lower bound | 10.07 | +0.17 | clears |
  | Co-binding **Calmar LB** vs median-cell Calmar LB (8.25) | — | **+53.1** | ADDS_VALUE |

- **Evidence:** `benefit.json`, `run_metadata.json::metrics`, `portfolio_metrics.csv`. Per-cell Sharpe LBs span
  2.01 (EURJPY-4h) to 7.53 (US2000-1h); portfolio MaxDD 0.034 sits below all 8 cells (0.031–0.100). Plot 1 (equity
  curves), Plot 2 (weight + correlation heatmap). MBB block = rebalance cadence, N_BOOT=10_000, α=0.10, n=185 weeks.
- **Interpretation:** the diversification mechanism is genuine and now correctly measured. With mean |cross-cell
  correlation| 0.10, continuously marking 8 imperfectly-correlated cells averages the moment-to-moment P&L path,
  lifting the portfolio risk-adjusted return **above any single constituent** and cutting drawdown below all of
  them. Per the pre-registered criterion (at least one of A/B has a Sharpe LB exceeding the baseline by a material
  margin), the read is **SUPPORTED** — and unlike the superseded flat-at-exit run (where the margin was −0.09,
  within-noise), it now clears by **margins far larger than the sampling band** (1.45) on every baseline. This is
  the faithful correction of the prior "NOT MET": the lumpy exit-booking had understated the portfolio's
  diversification benefit.

### Finding 2 — ERC ≈ naive inverse-vol (prior refutation no longer holds)

- **Observation:** A 11.69 (lo 10.24) vs naive-IV 11.55 (lo 10.07) — ERC marginally ahead on both point and lower
  bound; naive-IV has the lowest MaxDD (0.031). The gap is small.
- **Evidence:** `portfolio_metrics.csv` (naive_iv row), `benefit.json::disclosed_naive_sharpe_lo`.
- **Interpretation:** the superseded run found "ERC does **not** beat naive-IV (sub-thesis refuted)". Under the
  corrected MTM booking that **reverses to a near-tie, ERC marginally ahead** — but this is **not** a strong ERC
  win. Honest read: on this analysis set the two sizers are statistically comparable; ERC's case rests on
  risk-equalization/robustness rather than a decisive in-sample Sharpe edge, and the holdout (EXP-097), not this
  set, adjudicates it. Do not claim ERC decisively beats naive-IV.

### Finding 3 — Circuit-breaker is NEUTRAL: A ≈ B, no material drawdown benefit (prior "de-risks" was a booking artifact)

- **Observation:** Portfolio A (static ERC) and B (ERC + breaker) are **statistically indistinguishable** —
  Sharpe LB **10.24 vs 10.19**, point 11.69 vs 11.57; **MaxDD 3.44% vs 3.75%** (0.31 percentage points apart on an
  ~11%-vol book); ann. return near-identical (0.950 / 0.938). The two drawdown statistics **disagree in direction**:
  B is marginally *worse* on MaxDD (single worst trough) but marginally *better* on **Ulcer** (0.00369 vs 0.00398 —
  shallower/shorter aggregate underwater). Calmar (71.7 vs 66.3) is the only visible gap, and it just amplifies the
  tiny MaxDD difference (`annret/MaxDD`). The breaker still de-allocates the fragile 1h cells (timeline intact).
- **Evidence:** `run_metadata.json::metrics.A/B`, `circuit_breaker_timeline.csv`. Plot 3 (A−B underwater), Plot 4
  (de-allocation timeline).
- **Interpretation:** the superseded run reported "B de-risks, MaxDD −22.4% (SUPPORTED)". That was a **flat-at-exit
  artifact** — exit-lumping concentrated drawdowns in a way the breaker happened to trim. Under proper MTM the
  breaker is **neutral**: A and B perform essentially the same (differences inside the sampling band and disagreeing
  across drawdown statistics). Per the pre-registered rule ("B de-risks supported **iff** MaxDD **materially** lower
  at comparable Sharpe"), the **positive claim that the breaker de-risks is NOT SUPPORTED** — there is **no material
  benefit** to add the breaker on this analysis set. This is **not** a degradation (B is not worse on any binding
  number outside noise); it is a wash. (It remains an online safety overlay that de-allocates
  decaying cells; its value, if any, is a fragile-cell/regime-shift insurance not captured by aggregate MaxDD on
  this favorable analysis set.)

### Finding 4 — Gate statistic now READY: FPR controlled and a finite, clearable MDE

- **Observation:** synthetic-null FPR **A 0.000** (Wilson-hi 0.0038) / **B 0.002** (0.0073) — controlled. The
  MDE-curve resolves a finite minimum detectable margin **m* = 1.75 (A) / 2.00 (B)** annualized Sharpe at the
  79-week holdout-equivalent; the realized analysis-set edge (lo 10.24) **far exceeds** it ⇒
  `statistic_ready_for_g022a = true`.
- **Evidence:** `bite_check.json`, `null_fpr_calibration.json` (`fire_rate_by_plant`), Plot 5 (MDE curve). N_NULL=1000,
  n_weeks_cal=79, block-permute zero-mean null on the per-trade grid (`null_b_block_permute_returns` form; not
  built around a signal-derived target).
- **Interpretation:** this fixes the recurring defect (the superseded run's fixed-Sharpe=1.0 plant was structurally
  unattainable at n≈79, mis-reporting `statistic_ready=false`; same root cause as EXP-094's first-run bite RED).
  The gate now reports **what it can detect** (m*) rather than asserting an arbitrary fixed plant, and the realized
  edge clears it. **Routes to G-022a:** freeze the confirmation band **≥ m*** (≥1.75 for A / ≥2.00 for B) — a band
  below the gate's own MDE would not be detectable at the holdout sample size.

### Finding 5 — Integrity clean; the favorable direction is a faithful correction

- **Observation:** MTM conservation exact (Σ marks = realized net per cell ≤2.8e-14; grid total unchanged at
  +2199.79); provenance reconciliation hash **identical** to the superseded run (realized nets untouched);
  determinism byte-identical (A & B); causal-weight assertion passes **and** the marks themselves are causal
  (audit perturbation test); `holdout_untouched=true`, `counted_test_reads=0`, `candidate_slots=0`; vol-anchor
  Sharpe-invariance spread 1.8e-15; realized vol 0.112 (closer to the 10% target than the 0.131 pre-MTM).
- **Evidence:** `run_metadata.json`, `provenance_reconciliation.csv`, audit.md (C1/amendment verification table).
- **Interpretation:** the audit confirmed the Sharpe rise is **temporal-spreading + genuine diversification**, not
  variance understatement or look-ahead — per-cell MTM columns retain real adverse excursions, marks are strictly
  causal, and the amendment rules were frozen before the re-read. The result is trustworthy as an **analysis-set,
  in-sample** measurement.

## Disposition vs pre-registered measurable criteria

| Criterion (scope §7 / plan) | Disposition (corrected) | Basis |
|---|---|---|
| **Portfolio benefit** (A/B Sharpe LB > baseline by a material margin) | **SUPPORTED** (was NOT MET pre-MTM) | A/B LB clear the median-cell baseline by +5.25/+5.20 and every other baseline; margins ≫ sampling band (Finding 1). |
| **ERC vs naive-IV** (disclosed contrast) | **ERC ≈ naive-IV, marginally ahead** (was "refuted") | 11.69 vs 11.55; lo 10.24 vs 10.07 (Finding 2). |
| **Adaptability (A vs B)** (B *materially* de-risks at comparable Sharpe) | **NOT SUPPORTED — breaker NEUTRAL** (was SUPPORTED pre-MTM) | A ≈ B within noise (Sharpe LB 10.24 vs 10.19; MaxDD 3.44% vs 3.75%; B marginally better on Ulcer) → no material benefit, not a degradation (Finding 3). |
| **Statistic readiness for G-022a** (FPR ≤ 0.05 AND detectable) | **READY** (`statistic_ready=true`; was NOT READY) | FPR controlled; MDE m* finite (1.75/2.00) and cleared by realized lo 10.24 (Finding 4). |
| **Inconclusive clause** | N/A (edge LB ≫ 0; gate resolves) | — |
| **Integrity** (determinism, causality, holdout, provenance, reads) | **PASS** | Finding 5. |

## Hypothesis Verdict

**HYP-003 portfolio-economics leg: SUPPORTED — descriptive, analysis-set only, no holdout verdict.**

- Diversification raises the portfolio Sharpe **lower bound** above every constituent and every baseline → the
  main read is now a **faithful positive** (correcting the prior flat-at-exit "NOT MET").
- The **ERC > naive-IV** sub-thesis is **not** established — they are comparable in-sample (ERC marginally ahead).
- The **online circuit-breaker is neutral** on this MTM-corrected analysis set — A ≈ B within noise, so the
  positive claim that it materially de-risks is not supported (prior "de-risks −22.4% MaxDD" was a booking
  artifact); it is a wash, not a degradation.
- The **G-022a gate statistic is READY** (FPR-controlled + finite, clearable MDE).

## Limitations

- **In-sample, favorable-selected — magnitude not deployment-realistic.** Sharpe ~11–12 is an in-sample property
  of 8 G-021-confirmed cells under continuous marking; the amendment fixed *comparability and the gate*, not the
  absolute-magnitude implausibility. **Read the level as "strong in-sample," not a deployment estimate.** The
  binding deployment read is EXP-097 on the sealed holdout (same MTM construction).
- **MTM mark price proxy.** Intermediate 1h marks use the causal `minute_open` (the context exposes no minute
  *close* price); conservation pins the realized total exactly, so this affects only sub-minute intra-position
  distribution — non-material (audit Info 1).
- **Weekly-Sharpe gate sees location.** Well-matched to this right-skewed location edge (LB ≫ 0), with Calmar LB
  co-reading the drawdown shape; conservative on tails. Not blind here.
- **Diversification is correlation-dependent.** The benefit rests on the realized mean cross-cell correlation
  (0.10); a regime where the cells co-move more (JPY cluster max 0.54) would compress it — a robustness question
  for the noise model and holdout.

## Alternative Explanations

- **"The Sharpe rise is MTM smoothing risk away."** Rejected by the audit: per-cell MTM columns carry real adverse
  excursions (ATR-unit MaxDD 6–20); marks are strictly causal; conservation is exact. The rise is temporal
  spreading + genuine diversification, not variance hiding.
- **"The amendment was reverse-engineered to a positive."** Rejected: A1–A4 were frozen in D0-amendment-001 before
  the re-read; A1 restores the already-frozen D0 §D2.1 MTM; A2 made the criterion stricter/more honest. The benefit
  is robust across four independent baselines.
- **"ERC's diversification is the driver."** Partly: ERC and naive-IV are comparable, so the lift is generic
  diversification of low-correlation cells, not an ERC-specific property — consistent with Finding 2.

## Recommended Next Steps (new scopes — not extensions of EXP-095)

1. **G-022a gate/band decision (governance, not a new EXP):** freeze the confirmation band **≥ m*** (≥1.75 for A /
   ≥2.00 for B) per the A4 MDE rule; adopt the MTM construction for the holdout statistic. Carry Findings 3–4
   (breaker neutral; gate ready) into the adjudication.
2. **EXP-096 (planned, Phase-022 batch):** noise/entry-fill infusion on this MTM portfolio — does the in-sample
   diversification benefit survive a realistic 1-minute fill model; decide the G-022a holdout-frozen set. Use the
   same intra-1h MTM (A1) so the noise read is comparable.
3. **EXP-XXX (proposed, new D0):** robustness of the diversification benefit under correlation stress — re-evaluate
   ERC vs naive-IV vs robustness-weighted sizers on **drawdown/tail under a high-correlation regime subsample and
   the EXP-096 noise model**, since the in-sample benefit rests on the realized 0.10 cross-cell correlation. New
   experiment with its own D0 entry, not a re-selection from EXP-095's disclosed brackets.

---

*Registry note (for Stage 7): EXP-095 (amendment rerun) is a portfolio-aggregate disclosure — 0 counted TEST reads,
0 candidate slots, no stratum tally moves (11 carried strata stay 1/2, 37 stay 0/2), global holdout never loaded.
Corrected dispositions: portfolio benefit SUPPORTED; ERC ≈ naive-IV; circuit-breaker NEUTRAL (A ≈ B; no material
de-risking — the prior −22.4% MaxDD claim was a booking artifact); gate statistic READY (band ≥ m* at G-022a).*
