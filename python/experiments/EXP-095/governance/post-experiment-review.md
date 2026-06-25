# Post-Experiment Governance Review: EXP-095 (D0-amendment-001 rerun)

**Date:** 2026-06-25 · **Reviewer:** research-pipeline (consolidated Stage-8 governance)
**Artifacts reviewed:** `audit.md` (re-audit, amendment rerun), `results.md`, `report.md`, index + signal-registry updates
**Phase:** 022 (CF-MR-001 batch 3) · **Family / HYP:** `CF-MR-001` / `HYP-003`

```text
VERDICT: APPROVE
```

> Supersedes the prior post-experiment review of the flat-at-exit run. This governs the **D0-amendment-001
> amend-in-place rerun** (intra-1h MTM restored; benefit criterion re-specified; co-binding drawdown/tail;
> MDE-curve bite-check), which corrected a verdict-material measurement defect via a predeclared amendment + rerun.

## Basis

### Deviation handling (programme norm) — correctly executed
A verdict-material defect (4h booked flat-at-exit, deviating from frozen D0 §D2.1 intra-1h MTM, differentially
distorting the 1h-vs-4h binding comparison) was handled by a **dated amendment (`D0-amendment-001`) predeclaring
the changed rules (A1–A4) BEFORE the re-read + a full amend-in-place rerun**, not a silent follow-up. The amendment
**restores the already-frozen D0 MTM** and makes the benefit criterion **stricter/more honest** (lower-bound-vs-
lower-bound + a deployment-realistic median-cell baseline; ex-post-best demoted to disclosure). This is the
[[deviation_handling_amend_in_place]] norm applied correctly; 0 holdout cost (0 reads, holdout untouched).

### Favorable-direction scrutiny (anti-goalpost-moving) — satisfied
The rerun produced a favorable result (benefit now MET; gate now READY). Governance specifically confirms this is a
faithful measurement correction, not engineered:
- The A1–A4 rules are **dated and frozen in `D0-amendment-001` before the rerun was read** (verified).
- The audit **independently re-derived** the mechanism: MTM conservation exact (≤2.8e-14; provenance hash
  unchanged → realized nets untouched); marks **strictly causal** (future-price perturbation leaves earlier marks
  unchanged); per-cell MTM columns carry **real adverse excursions** (not variance-smoothing); the Sharpe rise is
  temporal-spreading + genuine diversification (mean cross-cell corr 0.10 → portfolio MaxDD below every cell).
- The benefit is **robust across four independent baselines** (median-cell, best-cell point, best-cell LB,
  naive-IV LB), not dependent on the new median baseline.

### Audit quality (Stage-8 specific) — verdict forensics present
- **Mechanism statement** (why the Sharpe rose), **per-stratum re-derivation with an affirmative masking check**
  (portfolio above all 8 cells = genuine diversification, not masking — all per-cell baselines disclosed), and a
  **gate-shape check** (location gate matched; A4 MDE gate fixed) are all present.
- **Both reversals reported honestly** (not buried): ERC ≈ naive-IV (prior refutation overturned) and the
  circuit-breaker turning NEUTRAL (A ≈ B within noise — no *material* de-risking; the prior −22.4% MaxDD was a
  flat-at-exit artifact). Governance treats a faithful reversal-to-neutral on a sub-leg as the discipline working,
  not a problem — and notes the prose was corrected to read "neutral / no material benefit," not "degradation."
- **Materiality:** 0 Critical; 2 Warnings (W1 in-sample magnitude; W2 breaker reversal) each shown to be faithful
  measurements that cannot be "fixed" by code, with explicit non-blocking reasoning; 3 Info non-material.

### Signal-registry disposition (Stage-8 specific) — recorded and applied
Registry-relevant (portfolio-aggregate disclosure). All updates applied in this change:
- **candidate-families/cf-mr-001.md:** status unchanged (ADMITTED (BINDING)/TRADABLE; deployment wrapper, 0 new
  slots); HYP-003 note updated to the corrected dispositions. ✓
- **multiplicity-registry.md:** Phase 022 EXP-095 outcome updated to the corrected dispositions (benefit
  SUPPORTED; ERC ≈ naive-IV; breaker NEUTRAL (no material de-risking); gate READY, band ≥ m\* at G-022a; D0-amendment-001 applied);
  prior superseded flat-at-exit record retained for file-drawer integrity. ✓
- **test-read-ledger.md:** **tally unchanged** — 0 counted reads, 11 carried strata stay 1/2, 37 stay 0/2, holdout
  never loaded; EXP-095 disclosure verdict summary updated. ✓

### Core-constraint checks
- **Holdout untouched:** `holdout_untouched=true`, `counted_test_reads=0`, `candidate_slots=0`; provenance hash
  identical to the prior run (no new holdout/TEST contact). ✓
- **Real-price discipline:** MTM marks use real causal `minute_open`/exit-fill prices; per-cell streams from the
  real-OHLC substrate; timestamp alignment on the 1h grid, never bar index. ✓
- **Single hypothesis / scope:** amendment A1–A4 within the frozen scope; entry/exit/cost/cells/seeds unchanged;
  EXP-096/097 explicitly out of scope. Complexity budget respected (A3 enriches the existing endpoint). ✓
- **No academic-finance pitfalls:** non-parametric MBB lower bounds (Sharpe + Calmar), block-permute zero-mean
  null on the per-trade grid (not a path rotation; not built around a signal-derived target); the A4 MDE-curve is
  the correct fix for the fixed-plant defect. ✓
- **Determinism / causality:** byte-identical second pass; causal-weight assertion + independent mark-causality
  test pass. ✓

### Results honesty
The interpretation leads with the corrected positive (benefit SUPPORTED via genuine diversification) **and** keeps
the in-sample-magnitude caveat prominent (Sharpe ~11–12 is not a deployment estimate; binding read = EXP-097),
reports both reversals as faithful negatives, and frames next steps as new experiments (EXP-096; the G-022a
band/A-vs-B decision; a correlation-stress robustness EXP). No overreach. ✓

## Conclusion

The verdict-material measurement defect was corrected by a predeclared amendment + amend-in-place rerun; the
favorable-direction result is **verified faithful** (conservation exact, marks causal, diversification genuine,
rules predeclared); the audit carries full verdict forensics with an affirmative masking check and reports both
reversals honestly; the signal-registry disposition is recorded with no tally moves. **APPROVE.**
