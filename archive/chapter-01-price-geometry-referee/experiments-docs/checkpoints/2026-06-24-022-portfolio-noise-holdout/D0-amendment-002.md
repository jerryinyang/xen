# D0-amendment-002 — Open EXP-098: Cross-Broker & Aggregation-Method Robustness Replication (PPS data)

**Date:** 2026-06-25 · **Phase:** 022 (CF-MR-001 batch 3) · **Family / HYP:** `CF-MR-001` / `HYP-003`
(deployment robustness companion) · **Status:** OPENED (operator-directed 2026-06-25).
**Consumes a new candidate slot?** **NO.** **Spends a counted TEST read / global-holdout shot?** **NO.**

## 1. What changes

Phase 022's frozen design (§4) ended at EXP-097, the single sanctioned global-holdout release
(`DEPLOYABLE_CONFIRMED`, shot SPENT). This amendment **adds one experiment, EXP-098**, as a **non-binding
robustness / replication disclosure** appended to the phase. It does not alter any prior experiment, the G-022a
freeze, the G-022 terminal verdict, or the deployable spec.

EXP-098 reruns the **G-022a-frozen deployment portfolio verbatim** (carry-8 cells; binding-v2 noise-aware causal
ERC + intra-1h MTM; circuit breaker; EXIT-RCT / adverse / cost / band all frozen) on an **independent broker's**
1-minute data — `data/timebars/pps/`, the same 8 instruments and the same 2021-06 → 2026-06 span — under **two
bar-aggregation timestamping methods**:

- **Arm 1 `PPS-CANON`** — the deployed `xen.domain_bars.build_domain_bars` (bucket-right-boundary label).
- **Arm 2 `PPS-ALTAGG`** — identical bucketing/coverage/OHLC, but each bar timestamped at the **actual last source
  1-minute bar's `CloseTime`** instead of the bucket boundary.

It tests two overfitting hypotheses EXP-097 could not separate: **broker overfit** (Arm 1) and **aggregation-method
overfit** (Arm 1 vs Arm 2). Evaluation slice = the **full PPS timeline** (operator decision — the model is frozen,
so no held-back slice is needed on independent data; binding metric over the full evaluable series after estimator
burn-in). Criterion = **reuse the EXP-097 band** (primary Portfolio B: Sharpe LB > 2.00 AND Calmar LB > 0), per
arm.

## 2. Multiplicity / registry treatment

- **One new countable item:** the alternate aggregation method **`AGG-LASTCLOSE`** (last-source-close
  timestamping), registered now in `multiplicity-registry.md` at its frozen definition as a **non-binding
  robustness disclosure** (file-drawer control; retained regardless of outcome). Arm 1's canonical aggregation is
  the already-registered deployed method.
- **PPS dataset** registered as a **robustness data source** (independent broker). It is **outside** the INFR-003
  48-stratum analysis-TEST ledger and **outside** the INFR-003 global holdout. Reading it is **not** a counted
  analysis-TEST read and **not** a global-holdout shot.
- **Slots / reads:** 0 candidate slots; 0 counted TEST reads. The 11 carried INFR-003 strata stay 1/2; the 37
  others stay 0/2; the INFR-003 global holdout stays spent-once (EXP-097) and is **not loaded**. The PPS read is
  recorded as a **robustness governance disclosure** in `test-read-ledger.md` + `multiplicity-registry.md` in the
  same change that records the EXP-098 result.

## 3. Binding constraints on EXP-098 (non-negotiable)

1. **Non-binding on EXP-097.** EXP-098 cannot upgrade, revoke, or revise the `DEPLOYABLE_CONFIRMED` verdict or the
   spent shot. It adds a robustness disclosure only.
2. **No re-derivation / re-tuning / re-selection** of the deployable set, construction, primary, band, or rule.
   No re-pruning of the cell set on PPS evidence.
3. **Independent-data discipline.** Only PPS is read; the INFR-003 dataset and its sealed holdout are not loaded;
   no mixing of broker eras within an analysis.
4. **Causal everything; real-price outcomes only; per-cell disclosure (LESSON-001).**
5. **Deviation handling** — a frozen-spec confound → dated amendment + hard-delete + full rerun.
6. Any *future binding* use of the PPS dataset requires its own governance (out of scope here).

## 4. Routing

EXP-098 runs the standard pipeline (scope → analysis-plan → implementation → pre-exec governance → manual
execution → audit → interpretation → documentation → post-exec governance). Its verdict is a robustness label
(`CROSS_BROKER_ROBUST` / `AGGREGATION_ROBUST` / `DEGRADED` / `INCONCLUSIVE`, per arm), recorded in the CF-MR-001
family index and the Phase 022 multiplicity batch. Phase 022 remains CLOSED at G-022 for the *deployment* verdict;
EXP-098 is an appended robustness companion, not a re-opening.
