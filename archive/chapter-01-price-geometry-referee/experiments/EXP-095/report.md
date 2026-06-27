# Experiment Report: EXP-095 — Portfolio Construction & Online-Adaptive Risk Model (RSI-2 Fade, 8 confirmed cells)

## Status: COMPLETED (D0-amendment-001 rerun; analysis-set only — no holdout verdict)

**Date**: 2026-06-25 (amendment rerun; original run 2026-06-24)
**Family / HYP**: `CF-MR-001` / `HYP-003` · **Phase**: 022 (batch 3 — Portfolio Construction, Noise Infusion & Global-Holdout Release)
**Instruments**: 8 G-021-confirmed cells — EURUSD-4h, XAUUSD-4h, USDCHF-4h, AUDJPY-4h, EURJPY-4h, GBPJPY-4h, USTEC-1h, US2000-1h
**Data Views / Feature Categories**: VAL-005 INFR-003 5-year 1-minute bars → causal 1h/4h domain bars; per-cell EXIT-RCT net per-event return streams (ATR units) reused from the EXP-090/093 substrate, with **intra-1h mark-to-market** (D0 §D2.1 / amendment-001 A1); analysis set only (TRAIN + EXP-093 analysis-TEST series as portfolio-aggregate disclosure)

> **Amendment lineage.** Cycle 1 audit: FAIL (Critical C1 — concurrent-risk cap on un-anchored weights → `1/vol²`).
> Cycle 2 (post-C1-fix): PASS, but under-weighted a verdict-material measurement defect — 4h positions were booked
> **flat-at-exit** instead of the **intra-1h mark-to-market D0 §D2.1 requires** (Sharpe/MaxDD inflated
> *differentially* across 1h/4h). Operator ratified **`D0-amendment-001`** (A1 intra-1h MTM; A2 like-for-like benefit
> + cross-cell-median baseline; A3 co-binding Calmar/CVaR/Ulcer; A4 MDE-curve bite-check), predeclared before the
> re-read; amend-in-place rerun complete and **re-audited PASS**. This report reflects that corrected rerun.

---

## Question

Built from the 8 G-021-confirmed cells, does a causal, parameter-free **ERC** portfolio deliver materially better
risk-adjusted performance (annualized Sharpe lower bound, with Calmar/tail co-binding) than a deployment-realistic
single-cell baseline — and does an online **circuit-breaker** (Portfolio B) measurably de-risk versus static ERC
(Portfolio A)? Is the new portfolio-level confirmation statistic calibrated and detectable so G-022a can freeze it?

## Hypothesis

`HYP-003` (portfolio-economics leg): a causal ERC portfolio of the confirmed cells beats a deployment-realistic
single-cell baseline on risk-adjusted return, and an online circuit-breaker de-risks the fragile cells —
descriptive on the analysis set, deciding no holdout verdict.

## Method Summary

Causal weekly-rebalanced ERC weights from a trailing 90-day Ledoit-Wolf covariance, a 10% annualized-vol anchor,
and a 1.5× concurrent-risk cap, aggregated by timestamp on a 1h grid with **intra-1h mark-to-market of open
positions** (so Sharpe/MaxDD reflect intra-position excursions and are comparable across 1h/4h). Binding endpoint:
the portfolio annualized-Sharpe MBB one-sided lower bound vs the **cross-cell median** single-cell Sharpe lower
bound (deployment-realistic; you cannot pick the ex-post-best cell ex ante), with **Calmar LB co-binding** and
CVaR/Ulcer co-reported. The new confirmation statistic is calibrated by synthetic-null FPR + an **MDE-curve** (the
smallest detectable planted Sharpe at the holdout n). See [analysis-plan.md](analysis-plan.md) and
[D0-amendment-001](../../../docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/D0-amendment-001.md);
all parameters frozen at D0, brackets disclosure-only.

## Key Findings

### Finding 1: ERC portfolio adds value — robustly, across every baseline (corrected main read)

Portfolio A (static ERC) annualized Sharpe **11.69 (MBB lo 10.24)**, MaxDD **0.034**, Calmar 71.8 (lo 61.3);
B **11.57 (lo 10.19)**, MaxDD 0.038. The binding Sharpe **lower bound** clears **every** benchmark: the
deployment-realistic **cross-cell median** single-cell LB (4.99) by **+5.25**, the best single cell on point (8.73)
*and* lower bound (7.53, by **+2.71**), and the naive inverse-vol LB (10.07). The co-binding **Calmar LB** clears
the median-cell Calmar LB (8.25) by **+53**. Margins are far larger than the sampling band (1.45). **Mechanism:**
genuine moment-to-moment diversification — 8 cells at mean cross-cell correlation **0.10**, marked continuously,
average down to a portfolio MaxDD (0.034) **below every constituent** (cells 0.031–0.100). This **corrects** the
superseded flat-at-exit run's "NOT MET (margin −0.09, within-noise)": the lumpy exit-booking was *hiding* the
portfolio's diversification benefit.

### Finding 2: ERC ≈ naive inverse-vol (prior refutation no longer holds)

A 11.69 (lo 10.24) vs naive-IV 11.55 (lo 10.07) — ERC marginally ahead on point and lower bound; naive-IV has the
lowest MaxDD (0.031). The superseded run's "ERC does not beat naive-IV (refuted)" **reverses to a near-tie, ERC
marginally ahead** — but this is **not** a strong ERC win. Honest read: the two sizers are statistically comparable
in-sample; the diversification lift is generic (low-correlation cells), not an ERC-specific property.

### Finding 3: Circuit-breaker is NEUTRAL — A ≈ B, no material drawdown benefit (prior "de-risks" was a booking artifact)

Portfolio A (static ERC) and B (ERC + breaker) are **statistically indistinguishable**: Sharpe LB **10.24 vs
10.19**, MaxDD **3.44% vs 3.75%** (0.31 pp apart on an ~11%-vol book), ann. return near-identical. The two drawdown
statistics **disagree**: B is marginally *worse* on MaxDD but marginally *better* on **Ulcer** (0.00369 vs 0.00398 —
shallower/shorter aggregate underwater); Calmar (71.7 vs 66.3) only amplifies the tiny MaxDD gap. The superseded
run's "B de-risks, MaxDD −22.4% (SUPPORTED)" was a **flat-at-exit artifact** (exit-lumping concentrated drawdowns
the breaker happened to trim). Under proper MTM the breaker is **neutral** — a wash, not a degradation. Per the
pre-registered rule ("B de-risks **iff** MaxDD **materially** lower at comparable Sharpe"), the positive claim is
**NOT SUPPORTED**: there is **no material benefit** to adding the breaker on this analysis set (it still de-allocates
the fragile 1h cells; the timeline is intact).

### Finding 4: Gate statistic now READY — FPR controlled and a finite, clearable MDE

Synthetic-null FPR **A 0.000** (Wilson-hi 0.0038) / **B 0.002** (0.0073) — controlled. The MDE-curve resolves a
finite minimum detectable margin **m\* = 1.75 (A) / 2.00 (B)** annualized Sharpe at the 79-week holdout-equivalent;
the realized analysis-set edge (lo 10.24) **far exceeds** it ⇒ `statistic_ready_for_g022a = true`. This **fixes**
the recurring defect (the superseded run's fixed-Sharpe=1.0 plant was structurally unattainable at n≈79 — same root
cause as EXP-094's first-run bite RED). **Routes to G-022a:** freeze the confirmation band **≥ m\*** (≥1.75 for A /
≥2.00 for B); a band below the gate's own MDE is not detectable at the holdout sample size.

### Finding 5: Integrity clean; the favorable direction is a faithful correction

MTM conservation exact (Σ marks = realized net per cell ≤2.8e-14; grid total unchanged); provenance reconciliation
hash **identical** to the superseded run (realized nets untouched, 8/8 abs-diff 0.0); marks **strictly causal**
(audit perturbation test); determinism byte-identical; `holdout_untouched=true`, `counted_test_reads=0`,
`candidate_slots=0`; vol-anchor Sharpe-invariance 1.8e-15; realized vol 0.112 (closer to the 10% target than 0.131
pre-MTM). The audit confirmed the Sharpe rise is temporal-spreading + genuine diversification, not variance hiding
or look-ahead, and the A1–A4 rules were frozen before the re-read (not goalpost-moving).

## Conclusion

**HYP-003 portfolio-economics leg: SUPPORTED — descriptive, analysis-set only, no holdout verdict.** Correcting the
booking to intra-1h mark-to-market reveals a genuine diversification benefit the flat-at-exit booking had hidden:
the ERC portfolio's Sharpe **lower bound** exceeds every constituent and every baseline by margins well beyond the
sampling band, with portfolio MaxDD below all 8 cells. Two prior findings **reverse** under the corrected booking
and are reported as faithful negatives: **ERC ≈ naive-IV** (not a decisive ERC win), and the **circuit-breaker is
neutral** — A ≈ B within noise, so its positive de-risking claim is not supported (the prior −22.4% MaxDD headline
was a booking artifact); a wash, not a degradation. The new gate statistic is **READY** (FPR-controlled
+ finite, clearable MDE), fixing the recurring fixed-plant defect. **Caveat held prominent:** Sharpe ~11–12 is an
**in-sample, favorable-selected** magnitude — the amendment fixed comparability and the gate, not the absolute-level
implausibility; the binding deployment verdict is **EXP-097** on the sealed holdout (same MTM construction).

## Registry Disposition

**Updates applied** (portfolio-aggregate disclosure — registry-relevant; no tally moves):

- **candidate-families/cf-mr-001.md:** status **unchanged** — `ADMITTED (BINDING)` / **TRADABLE**; EXP-095 is a
  deployment wrapper on the admitted lever; **0 new candidate slots**. HYP-003 note updated to the corrected
  dispositions.
- **multiplicity-registry.md:** Phase 022 EXP-095 outcome updated to the corrected dispositions (benefit
  **SUPPORTED**; ERC ≈ naive-IV; circuit-breaker **NEUTRAL** (no material de-risking; A ≈ B); gate statistic
  **READY**, band ≥ m\* at
  G-022a; D0-amendment-001 applied). Prior (superseded) flat-at-exit record retained for file-drawer integrity.
- **test-read-ledger.md:** **tally unchanged** — 0 counted TEST reads; 11 carried strata stay **1/2**, 37 stay
  **0/2**; global holdout never loaded. The EXP-095 disclosure verdict summary updated to the corrected dispositions.

## Limitations

- **In-sample, favorable-selected — magnitude not deployment-realistic.** Sharpe ~11–12 is an in-sample property
  of 8 G-021-confirmed cells under continuous marking. Read the level as "strong in-sample," not a deployment
  estimate. Binding deployment read = EXP-097.
- **Diversification is correlation-dependent.** The benefit rests on the realized mean cross-cell correlation
  (0.10; JPY cluster up to 0.54); a higher-correlation regime would compress it.
- **MTM mark proxy:** intermediate 1h marks use the causal `minute_open` (no minute-close price in the context);
  conservation pins the realized total exactly, so the effect is sub-minute intra-position distribution only
  (audit Info 1, non-material).
- **Adaptability leg neutral:** A ≈ B within noise — the circuit-breaker delivers no *material* drawdown reduction
  on this favorable analysis set (it is a wash, not a degradation); any
  value is fragile-cell/regime-shift insurance not captured by aggregate MaxDD here.

## Implications for Future Research

- G-022a must freeze the confirmation band ≥ m\* and adopt the MTM construction for the holdout statistic.
- Whether to deploy Portfolio A (static ERC) vs B (breaker) is now open: B no longer earns its complexity on this
  analysis set — the noise model (EXP-096) and holdout should decide.
- The diversification benefit's robustness to correlation stress and realistic fills is the open question.

## Recommended Next Experiments

1. **EXP-096 (planned, Phase-022 batch):** noise/entry-fill infusion on this MTM portfolio — does the in-sample
   diversification benefit survive a realistic 1-minute fill model; decides the G-022a holdout-frozen set (same
   intra-1h MTM so the read is comparable).
2. **G-022a (governance, not an EXP):** freeze the confirmation band ≥ m\* (≥1.75 A / ≥2.00 B); decide A vs B for
   the deployable set given the breaker is now neutral.
3. **EXP-XXX (proposed, new D0):** robustness of the diversification benefit under correlation stress — ERC vs
   naive-IV vs robustness-weighted sizers on drawdown/tail in a high-correlation regime subsample + the EXP-096
   noise model. New experiment with its own D0 entry, not a re-selection from EXP-095's disclosed brackets.

## Artifacts

| Artifact | Path |
|----------|------|
| Scope | [scope.md](scope.md) |
| Analysis Plan | [analysis-plan.md](analysis-plan.md) |
| Amendment | [D0-amendment-001.md](../../../docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/D0-amendment-001.md) |
| Code | [code/run_experiment.py](code/run_experiment.py) · module [python/src/xen/portfolio.py](../../src/xen/portfolio.py) |
| Audit (re-audit PASS) | [audit.md](audit.md) |
| Results | [results.md](results.md) |
| Governance Reviews | [governance/](governance/) |
| Plots | [plots/](plots/) |
| Results data | [results/](results/) |
