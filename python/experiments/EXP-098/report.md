# EXP-098 — Cross-Broker & Aggregation-Method Robustness Replication of the RSI-2 Fade Deployment Portfolio

**Phase:** 022 (CF-MR-001 batch 3) · **Family / HYP:** `CF-MR-001` / `HYP-003` (deployment robustness companion) ·
**Type:** non-binding robustness / replication disclosure · **Date:** 2026-06-25
**Verdict:** **`CROSS_BROKER_ROBUST` ∧ `AGGREGATION_ROBUST`** (both arms ROBUST) · **EXP-097 verdict unchanged** ·
**0 candidate slots / 0 counted TEST reads** · audit PASS (0C/0W/3I) · opened by
[`D0-amendment-002`](../../../docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/D0-amendment-002.md).

## 1. Question

Rerun **verbatim** on a completely independent broker's data (PPS; `data/timebars/pps/`, same 8 carry-8
instruments and 2021-06 → 2026-06 span), does the G-022a-frozen RSI-2 fade deployment portfolio (carry-8 binding-v2
causal ERC + intra-1h MTM + circuit breaker) retain its confirmed risk-adjusted edge — and is that edge robust to
the bar-aggregation timestamping method? Two arms separate the two overfitting hypotheses EXP-097 could not:

- **Arm 1 `PPS-CANON`** — the deployed bucket-boundary aggregation (`xen.domain_bars.build_domain_bars`). Tests
  **broker overfit**.
- **Arm 2 `PPS-ALTAGG`** — identical bucketing/coverage/OHLC, but the bar is timestamped at the **actual last
  source 1-minute `CloseTime`** (`AGG-LASTCLOSE`). Tests **aggregation-method overfit**.

Criterion = the inherited EXP-097 band, per arm: primary Portfolio B **Sharpe LB > 2.00 AND Calmar LB > 0**.
Evaluation = the **full PPS timeline** after the trailing-90-day covariance burn-in (operator decision; the model
is fully frozen, so no held-back slice is needed on independent data). The INFR-003 dataset and its sealed global
holdout were **not** loaded.

## 2. Result

| Arm | Portfolio B Sharpe (LB) | Calmar LB | A Sharpe LB | n_weeks | CONFIRM_B | Label |
|---|---|---|---|---|---|---|
| **PPS-CANON** | 7.08 (**5.968**) > 2.00 | **12.53** > 0 | 6.147 > 1.75 | 251 | ✅ | **ROBUST** |
| **PPS-ALTAGG** | 7.22 (**6.104**) > 2.00 | **13.32** > 0 | 6.302 > 1.75 | 251 | ✅ | **ROBUST** |

→ **`CROSS_BROKER_ROBUST = true`** (Arm 1 B confirms) and **`AGGREGATION_ROBUST = true`** (both arms B confirm).

- **Broad-based, no masking.** All **8/8 cells net-positive on both arms** (PPS net ci_low +0.0105 … +0.0941).
  **EURJPY-4h** — net-negative on the INFR-003 holdout (−0.006) and pre-flagged `NOISE_DEGRADED` — is net-**positive**
  on PPS (+0.026, ci_low +0.0105). Drop-one masking (removes the largest contributor US2000-1h): B still confirms
  (Sharpe LB 5.48 / 5.57), `label_flips=false`.
- **Aggregation near-inert.** The two arms are near-identical: domain-bar counts match exactly except USTEC-1h /
  US2000-1h (+1 bar under the last-close label); per-cell nets identical to ~1e-5 on all 4h cells. The timestamping
  rule can only move the trailing/incomplete window → the edge does not depend on it.
- **Mechanism.** The bare RSI-2 fade + EXIT-RCT reversion-completion geometry nets positive via ATR-normalized cost
  being small on the slower domain — a property of price structure, not of one broker's feed — so it reproduces on
  PPS (per-cell nets within ~10–25% of INFR-003). The ~7 Sharpe is structural diversification of 8 low-correlation
  cells vol-anchored to 10% (in-family with EXP-097's ~4.9 LBs), not a bug.
- **Retention (descriptive, slice-caveated).** PPS full-timeline (n=251 wk) vs INFR-003 holdout (n=80 wk) ratio
  ≈ 1.25–1.45 — read as "confirms at least as strongly," not "stronger edge" (different slices). Non-binding.

## 3. Integrity

MTM conservation ≤ 2.8e-14 ATR (8/8 cells, both arms); determinism replay byte-identical (A & B);
binding-statistic determinism true; causal-weight + causal-fill assertions pass in the evaluable region;
real-price only; `infr003_holdout_loaded=false`; 11 output hashes recorded. Audit PASS (0C/0W/3I) — no
verdict-material finding; three Info notes (retention slice non-equivalence; disclosure-only provenance arg;
XAUUSD-4h coverage 0.199 within tolerance).

## 4. Key visualisations

- `plots/pps_equity_curves.png` — A/B/naive + per-cell evaluable equity, faceted by arm.
- `plots/pps_metric_vs_band.png` — Sharpe/Calmar LB vs band, both arms.
- `plots/pps_per_cell_net.png` — per-cell PPS net vs EXP-097 holdout (retention + masking).
- `plots/pps_drawdown_A_vs_B.png` — A vs B underwater, per arm.
- `plots/pps_arm_comparison.png` — Arm 1 vs Arm 2 aggregation sensitivity.

## 5. Disposition

- **Verdict:** SUPPORTED (non-binding) — the deployed portfolio is robust to broker feed and aggregation method.
  **EXP-097 `DEPLOYABLE_CONFIRMED` stands unchanged**; this is a strengthening robustness companion, not an
  upgrade or a re-read.
- **Reads / slots:** `counted_test_reads=0`, `candidate_slots=0`. PPS is an independent dataset, outside the
  INFR-003 analysis-TEST 48-stratum ledger and the INFR-003 global holdout (never loaded; the 11 carried strata
  stay 1/2, the other 37 stay 0/2). Recorded as a **robustness governance disclosure** in `test-read-ledger.md` and
  `multiplicity-registry.md` (item `AGG-LASTCLOSE` + PPS robustness data source). PPS is hereby "touched" as a
  robustness dataset — any *future binding* use needs its own governance.

## 6. Signal-registry disposition

**Registry-relevant (robustness disclosure).** `CF-MR-001` stays `DEPLOYABLE` (G-022 unchanged). The
multiplicity-registry EXP-098 row records the outcome (`CROSS_BROKER_ROBUST` ∧ `AGGREGATION_ROBUST`); the
`AGG-LASTCLOSE` item is retained (file-drawer); the test-read-ledger records the PPS robustness read as a
disclosure (no counted read, no slot, INFR-003 holdout untouched).

Artifacts: [`scope.md`](scope.md) · [`analysis-plan.md`](analysis-plan.md) · [`code/run_experiment.py`](code/run_experiment.py) ·
[`audit.md`](audit.md) · [`results.md`](results.md) · [`governance/pre-execution-review.md`](governance/pre-execution-review.md).
