# Results: Experiment EXP-096

**Noise Infusion — Realistic 1-Minute Entry Fill (RSI-2 Fade Portfolio, 8 confirmed cells)** · `CF-MR-001`/`HYP-003` ·
Phase 022 (batch 3) · **analysis-set only — NO holdout verdict.**

*Interpretation of the EXP-096 run (`results/` generated 2026-06-25; audit.md = PASS, 0C/0W/5I, full verdict
forensics). Every disposition is anchored to the pre-registered interpretation guide (`analysis-plan.md`
§"Interpretation Guide", SURVIVES/WITHIN-NOISE/BREAKS) — no goalposts moved after seeing results. The binding
variant is **v2** (next-1m-open + 0.05×ATR adverse slippage); v1/v3 are the disclosed sensitivity ladder. The
binding figure is the portfolio annualized-Sharpe MBB one-sided lower bound (co-binding Calmar LB), compared
like-for-like to the deployment-realistic cross-cell-median single-cell lower bound (amendment-001 A2/A3). All
reads are descriptive on the analysis set; the binding deployment verdict is EXP-097 on the sealed holdout.*

## Summary

Under the **binding realistic 1-minute entry fill (v2)**, the EXP-095 in-sample diversification benefit **SURVIVES**.
The 0.05×ATR adverse slippage subtracts a near-**uniform −0.05 ATR per event** (re-derived exact) from all eight
cells, which roughly **halves** the portfolio Sharpe lower bound (idealized A 10.28 → v2 5.15) — but it halves the
cross-cell-median single-cell baseline in lockstep (≈5.0 → 2.55), so the **relative** diversification margin is
preserved: Portfolio A v2 Sharpe LB **5.147** clears the median-cell baseline (2.554) by **+2.59 > sampling band
1.35** and is co-binding **ADDS_VALUE** on Calmar LB. The benefit is **broad-based** — all eight per-cell v2 Sharpe
LBs are positive and the portfolio LB exceeds even the best single cell — not one cell carrying losers. One cell,
**EURJPY-4h**, is flagged `NOISE_DEGRADED` (v2 net `ci_low` 0.0079 < its 0.025 margin) but is **still net-positive
and retained** (operator portfolio-only membership; G-022a decides the holdout-frozen set). The realized v2 edge
**clears the inherited gate m\*** comfortably (A LB 5.15 ≥ 1.75; B LB 4.90 ≥ 2.00). The A-vs-B picture is nuanced
and material to G-022a: the circuit-breaker is **NEUTRAL at the binding v2** (A ≈ B, reproducing EXP-095) but
becomes **large tail-insurance at the v3 stress ceiling**, where static-ERC A blows up (MaxDD 40.9%, Sharpe LB
−1.65) while breaker-B holds (MaxDD 6.0%, Sharpe LB +1.83). **Caveat held prominent:** Sharpe ~6–12 are in-sample
favorable-selected magnitudes — read the **survival/relative gap**, not the level; the binding deployment read is
EXP-097.

## Detailed Findings

### Finding 1 — The diversification benefit SURVIVES the binding v2 fill (the leg's main result)

- **Observation:** Portfolio A v2 annualized Sharpe **6.496 (MBB LB 5.147)**, B **6.287 (LB 4.897)**, naive-IV
  **6.441 (LB 5.089)**. The binding like-for-like benefit (portfolio Sharpe LB vs cross-cell-**median** single-cell
  Sharpe LB = 2.554):

  | Benefit read (v2, like-for-like LB vs LB) | Margin | Sampling band | Label |
  |---|---|---|---|
  | A Sharpe LB (5.147) vs median-cell LB (2.554) | **+2.59** | 1.35 | **ADDS_VALUE** |
  | B Sharpe LB (4.897) vs median-cell LB | +2.34 | 1.39 | **ADDS_VALUE** |
  | A Calmar LB vs median-cell Calmar LB (2.745) | **+4.28** | 3.03 | **ADDS_VALUE** (co-binding) |
  | B Calmar LB vs median-cell Calmar LB | +4.08 | 4.42 | ADDS_VALUE (point); band-wide (disclosed) |
  | *disclosed:* A vs ex-post-best-cell LB (3.652) | +1.69 | 1.35 | ADDS_VALUE |
  | *disclosed:* A vs naive-IV LB (5.089) | +0.06 | — | ERC ≈ naive-IV |

- **Evidence:** `benefit_v2.json`, `portfolio_metrics.csv`, `noise_ladder.csv`. Plots: `noise_sensitivity_ladder.png`,
  `equity_curves_v2.png`.
- **Interpretation:** Per the pre-registered rule (≥1 of A/B has v2 Sharpe LB exceeding the cross-cell-median by
  more than the sampling band, and not dominated on co-binding Calmar LB), the binding noise-survival read is
  **SURVIVES**. The margin (+2.59) is ~1.9× the one-sided sampling band (1.35) and far outside the disclosed
  cov-window nuisance bracket (v2 A Sharpe 6.55/6.50/6.46 at 60/90/120-day covariance — spread 0.09). The B Calmar
  benefit is positive on point but its margin (+4.08) sits just inside its wide sampling band (4.42); the **binding
  Sharpe LB and the A Calmar LB both clear cleanly**, so the co-binding read is satisfied. ERC ≈ naive-IV again
  (A 5.147 vs naive 5.089) — the lift is **generic low-correlation diversification, not an ERC-specific property**
  (consistent with EXP-095).

### Finding 2 — Mechanism: a uniform cost-scale slippage that preserves the relative margin

- **Observation:** `v2_net_mean = v1_net_mean − 0.05000` **exactly** for every cell (re-derived in audit: EURUSD-4h
  0.14847→0.09847; USTEC-1h 0.10451→0.05451; US2000-1h 0.10982→0.05982). v1 (latency only) is near-neutral
  (mean entry gap ≈ 0, both signs; v1 A Sharpe LB 10.31 ≈ idealized 10.28).
- **Evidence:** `per_cell_degradation.csv`, `entry_fill_audit.csv` (v2 mean adverse gap = 0.049–0.050 ATR all cells),
  `mtm_conservation.csv` (Σ marks = realized net(v2) ≤1.4e-14).
- **Interpretation:** The binding fill is **latency-neutral + a flat 0.05-ATR adverse tick**. Because that tick is
  subtracted from every cell roughly equally, it halves **both** the portfolio Sharpe LB **and** the cross-cell-
  median baseline — so the diversification *gap* survives even though the *level* roughly halves. The audit confirms
  this is **not** variance hiding and **not** a denominator change (keep mask byte-identical to EXP-093, event
  counts unchanged). This is the honest-prior outcome: a cost-scale bite on a ~0.28-ATR gross geometry, with
  diversification more robust than any single cell.

### Finding 3 — Per-cell degradation is broad-based; EURJPY-4h flagged but retained (disclosure)

- **Observation:** all eight v2 per-cell single-cell Sharpe LBs are **positive** — min **0.130 (EURJPY-4h)**, median
  **2.554**, max **3.652 (EURUSD-4h)**; the portfolio A v2 LB (5.147) exceeds **even the best single cell's LB**.
  Per-cell v2 net `ci_low_1s` vs the EXP-093 margin: 7/8 clear; **EURJPY-4h** (0.0079 < 0.025) is flagged
  `NOISE_DEGRADED`; GBPJPY-4h is next-weakest (0.0278, just clears).
- **Evidence:** `portfolio_metrics.csv` (v2 cell rows), `per_cell_degradation.csv`, `run_metadata.json`
  (`noise_degraded_cells_flagged: ["EURJPY-4h"]`). Plot: `per_cell_degradation.png`.
- **Interpretation:** The portfolio headline is **not masking heterogeneity** (audit per-stratum check): there is no
  negative/broken cell hidden inside the v2 aggregate, so the portfolio is the legitimate binding estimand and the
  cross-cell-median (2.554) honestly represents the eight cells. EURJPY-4h is the slippage-fragile cell (lowest gross
  geometry: ideal median only 0.016 ATR), still net-positive but no longer clearing its detectability margin under
  noise. Per the operator's **portfolio-only membership** rule it is **retained, not dropped** — this is a
  **disclosure input to the G-022a holdout-frozen-set decision**, not a verdict here.

### Finding 4 — Noise ladder shape: v1 neutral → v2 survives → v3 stress-ceiling breaks A (not B)

- **Observation (Portfolio A Sharpe LB):** ideal **10.28** → v1 **10.31** → v2 **5.15** → v3 **−1.65** (A MaxDD
  **40.9%**, Ulcer 0.188). v3 Portfolio B holds: Sharpe LB **+1.83**, MaxDD **6.0%**.
- **Evidence:** `noise_ladder.csv`, `portfolio_metrics.csv` (v3 rows), `run_metadata.json::noise_ladder`.
- **Interpretation:** v1 confirms execution **latency alone is near-costless**; v2 (the binding realistic-conservative
  fill) survives; v3 is a **deliberately harsh stress ceiling** (the absolute worst touched price across 3 one-minute
  bars). v3 bites the **fast 1h cells** hardest because a 3-minute swing is a larger fraction of a 1h cell's ATR(14)
  than of a 4h cell's (v3 mean adverse gap ≈ 0.15 ATR for USTEC/US2000 vs ≈ 0.05–0.075 for the 4h cells), driving
  the 1h cells (and EURJPY-4h) net-negative and blowing up static-ERC A. **This is a stress probe, not a deployment
  estimate** — the binding fill is v2. Its value is the A-vs-B finding below.

### Finding 5 — Circuit-breaker is NEUTRAL at v2 but large tail-insurance at v3 (material to G-022a A-vs-B)

- **Observation:** At the binding **v2**, A ≈ B — d(Sharpe LB) +0.25, d(MaxDD) +0.0013, d(Ulcer) −0.0012 (B
  marginally better on Ulcer, marginally worse on Sharpe; all inside the sampling-band overlap). Under **v3**, B
  (Sharpe LB +1.83, MaxDD 6.0%) vastly beats A (−1.65, MaxDD 40.9%) by de-allocating the fragile 1h cells
  (USTEC-1h 26.1% / US2000-1h 21.7% of grid steps).
- **Evidence:** `adaptability_v2.json`, `circuit_breaker_timeline_v2.csv`, `portfolio_metrics.csv` (v3).
  Plots: `circuit_breaker_timeline_v2.png`, `drawdown_A_vs_B_v2.png`.
- **Interpretation:** Per the pre-registered adaptability rule, at v2 the breaker is **NEUTRAL** (A ≈ B within the
  band — EXP-095's read persists). But the audit gate-shape forensics establish this is a real **edge-decay-threshold
  effect**, not an artifact: the breaker is **dormant at v2** (no cell's trailing-50 mean is negative) and **active at
  v3** (the 1h-cell means flip negative → de-allocation), preventing a 40.9%→6.0% drawdown blow-up. **For G-022a:**
  the breaker **costs ~nothing at the binding v2 and provides large tail insurance at the stress ceiling** — a
  genuine argument for deploying Portfolio B that EXP-095 (noise-free, no stress probe) could not see.

### Finding 6 — Gate statistic remains clearable under noise (inherited m\*)

- **Observation:** v2 A Sharpe LB **5.147 ≥ m\* 1.75** (edge +3.40); v2 B LB **4.897 ≥ m\* 2.00** (edge +2.90) →
  `statistic_clearable_under_noise = true`.
- **Evidence:** `gate_recheck.json`.
- **Interpretation:** m\* is **inherited** from EXP-095's A4 MDE-curve (not recomputed under noise — operator
  decision). The realized v2 edge clears it comfortably for both portfolios, so the inherited statistic remains
  detectable at the holdout-equivalent sample size under the binding fill. **Routes G-022a to freeze the confirmation
  band ≥ m\*** (≥1.75 A / ≥2.00 B), with the realized v2 LB (≈4.9–5.1) sitting well above.

### Finding 7 — Integrity clean; construction reused verbatim

- **Observation:** provenance abs-diff **0.0** vs EXP-093 on all 8 cells (counts match); MTM conservation ≤1.4e-14;
  determinism byte-identical (A & B); causal-fill + causal-weight assertions PASS; keep-mask invariant
  (`n_entry_unavailable_on_keep = 0`); `holdout_untouched = true`, `counted_test_reads = 0`, `candidate_slots = 0`.
  The idealized variant reproduces EXP-095's A Sharpe **point 11.691 exactly**.
- **Evidence:** `provenance_reconciliation.csv`, `mtm_conservation.csv`, `run_metadata.json`, audit.md.
- **Interpretation:** The pure entry-leg perturbation is faithfully implemented — only the entry price changed, the
  exit/keep are EXP-093-identical, and the EXP-095 construction is reused verbatim (point-estimate match). The noise
  read is therefore directly comparable to EXP-095.

## Disposition vs pre-registered measurable criteria

| Criterion (analysis-plan interpretation guide) | Disposition | Basis |
|---|---|---|
| **Noise survival (binding)** | **SURVIVES** | A (and B) v2 Sharpe LB clears the cross-cell-median baseline by +2.59 / +2.34 > sampling band (1.35/1.39); co-binding A Calmar LB clears (+4.28); margin far outside the cov-window bracket (Finding 1–2). |
| **Per-cell degradation (disclosure)** | **1 cell flagged, retained** | EURJPY-4h `NOISE_DEGRADED` (v2 ci_low 0.0079 < 0.025), still net-positive; all 8 per-cell LBs positive; G-022a decides membership (Finding 3). |
| **Adaptability A vs B (descriptive)** | **NEUTRAL at v2; B protective at v3** | v2 A ≈ B within band (breaker neutral, EXP-095 persists); v3 B +1.83/MaxDD 6.0% vs A −1.65/MaxDD 40.9% (Finding 5). |
| **Gate re-check (inherited m\*)** | **clearable under noise** | v2 A LB 5.15 ≥ 1.75; B LB 4.90 ≥ 2.00 → band ≥ m\* at G-022a (Finding 6). |
| **Integrity** | **PASS** | provenance 0.0; conservation ≤1.4e-14; determinism/causality/keep-mask PASS; 0 reads/slots; holdout untouched (Finding 7). |

## Hypothesis Verdict

**HYP-003 fill-realism leg: SURVIVES — descriptive, analysis-set only, no holdout verdict.**

Under a realistic 1-minute entry fill (binding v2 = next-1m-open + 0.05×ATR adverse slippage), the confirmed RSI-2
fade portfolio **retains its risk-adjusted diversification benefit**: the portfolio Sharpe lower bound clears the
deployment-realistic cross-cell-median baseline by more than its sampling band, co-binding on Calmar, broad-based
across all eight cells, and clears the inherited gate m\*. Execution latency alone is near-costless (v1); the
binding edge halves in level but survives in relative terms because the slippage hits all cells uniformly. The
realistic fill therefore **does not break the deployable portfolio**; it hands G-022a a **non-empty deployable set,
a noise-realistic band estimate (≥ m\*), and a sharpened A-vs-B decision** (breaker neutral at v2, large tail
insurance at the v3 stress ceiling). The binding deployment confirmation remains EXP-097 on the sealed holdout.

## Limitations

- **In-sample, favorable-selected magnitudes.** Sharpe ~6–12 are properties of 8 G-021-confirmed cells under
  continuous marking; read the **survival/relative gap**, not the absolute level. The binding deployment estimate is
  EXP-097 on the final-30% global holdout (same MTM construction).
- **v3 is a deliberately harsh stress ceiling, not a fill model.** "v3 A BREAKS" is an upper-bound execution probe
  (absolute worst of 3 one-minute bars); the realistic-conservative binding fill is v2, which survives. Do not read
  v3 as deployment failure.
- **m\* inherited, not recomputed under noise** (operator decision). The realized v2 edge clears it comfortably, but
  the gate's MDE was calibrated on the EXP-095 noise-free series; G-022a freezes the band ≥ m\*.
- **EURJPY-4h flagged.** A slippage-fragile cell retained under portfolio-only membership — a G-022a membership input,
  not a drop; its weakness is the binding-set composition question for the holdout read.
- **Diversification is correlation-dependent.** The benefit rests on the realized low cross-cell correlation (EXP-095
  mean |corr| 0.10); a higher-correlation regime would compress it — a robustness question for the holdout and
  beyond.

## Alternative Explanations

- **"The v2 survival is variance hiding / a denominator change."** Rejected by the audit: the keep mask is
  byte-identical to EXP-093 (n unchanged), MTM conservation is exact, and the per-event v2 shift is an exact −0.05
  ATR — the survival is the relative diversification margin under a uniform cost-shift, not a metric artifact.
- **"ERC's risk-parity drives the benefit."** Rejected: ERC ≈ naive-IV (5.147 vs 5.089) — the lift is generic
  low-correlation diversification, reproduced under noise, not an ERC-specific property.
- **"The breaker is useless (v2 neutral)."** Incomplete: it is neutral at the binding v2 but materially protective at
  the v3 stress ceiling (40.9%→6.0% MaxDD); the value is tail insurance that only appears when entries deteriorate
  enough to flip a cell's trailing mean negative.

## Recommended Next Steps (new scopes — not extensions of EXP-096)

1. **G-022a pre-holdout freeze (governance, not a new EXP).** With a non-empty deployable set, an analysis-set
   portfolio edge that survives the binding noise, and the inherited statistic clearable, freeze:
   (a) the **confirmation band ≥ m\*** (≥1.75 A / ≥2.00 B); (b) the **A-vs-B deployment choice** — EXP-096 argues for
   **Portfolio B** (≈free at v2, large tail insurance at stress) over A; (c) the **holdout-frozen deployable set** —
   decide whether to carry EURJPY-4h (flagged) or trim to the 7 unflagged cells. Then proceed to EXP-097, else HALT
   (holdout preserved).
2. **EXP-097 — global-holdout release (the single sanctioned one-shot).** Run the frozen, noise-aware (v2) portfolio
   (the G-022a-chosen construction and set) on the final-30% global holdout under the G-022a-frozen band; the binding
   DEPLOYABLE_CONFIRMED / DECAYED / INCONCLUSIVE verdict. New scope/D0 entry, gated behind the G-022a freeze.
3. **(Proposed, new D0) Correlation-stress robustness of the diversification benefit.** Re-evaluate the v2 portfolio
   benefit on a high-correlation regime subsample (the EXP-095/096 benefit rests on realized 0.10 cross-cell
   correlation), to bound how much a co-movement regime would compress it. New experiment, not a re-selection from
   EXP-096's disclosed brackets.

---

*Registry note (for Stage 7): EXP-096 is a portfolio-aggregate / cost-re-resolution disclosure — **0 counted TEST
reads, 0 candidate slots**, no stratum tally moves (11 carried strata stay 1/2, 37 stay 0/2), global holdout never
loaded. Dispositions: fill-realism leg **SURVIVES** at binding v2 (benefit ADDS_VALUE, broad-based, clears inherited
m\*); circuit-breaker **NEUTRAL at v2 / tail-protective at v3** (A-vs-B input to G-022a); EURJPY-4h flagged-retained
(membership input). No family-status change (`ADMITTED`/`TRADABLE` unchanged); analysis-set only — binding
deployment read is EXP-097.*
