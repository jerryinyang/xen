# Results: Experiment EXP-098

**Cross-Broker & Aggregation-Method Robustness Replication of the RSI-2 Fade Deployment Portfolio (PPS data)**
Phase 022 · `CF-MR-001` / `HYP-003` (robustness companion) · **non-binding disclosure** · 2026-06-25

## Summary

Rerun **verbatim** on a completely independent broker's 1-minute data (PPS; same 8 carry-8 instruments and span),
the G-022a-frozen RSI-2 fade deployment portfolio **replicates cleanly and is robust to the bar-aggregation
method**. On both arms the primary Portfolio B clears the inherited EXP-097 band — PPS annualized Sharpe LB
**5.97 (Arm 1 PPS-CANON) / 6.10 (Arm 2 PPS-ALTAGG) > band 2.00**, co-binding Calmar LB **12.5 / 13.3 > 0** — so
`CROSS_BROKER_ROBUST = true` and `AGGREGATION_ROBUST = true`. The replication is **broad-based** (all 8 cells
net-positive on both arms) and **survives a drop-one masking check**. The result is a robustness disclosure: it
**does not** change EXP-097's spent, non-upgradable `DEPLOYABLE_CONFIRMED` verdict — but it materially strengthens
the deployment claim by ruling out broker-feed overfit and aggregation-method overfit. Audit PASS (0C/0W/3I).

## Detailed Findings

### Finding 1 — Cross-broker robust (Arm 1, PPS-CANON)

- **Observation:** with the deployed bucket-boundary aggregation, Portfolio B on the full PPS timeline (n=251
  evaluable weeks, after the trailing-90-day covariance burn-in) has annualized Sharpe **7.08 (MBB LB 5.968)** and
  Calmar LB **12.53** → CONFIRM. A co-confirms (Sharpe 7.28, LB 6.147; Calmar LB 12.17); naive-IV LB 6.13.
- **Evidence:** `results/eval_metrics.csv`, `results/verdict.json`; ann vol ≈ 0.108 (the 10% anchor), MaxDD 0.060.
- **Interpretation:** the confirmed edge is **not** a cTrader/INFR-003 feed artifact. It reproduces on an unrelated
  broker's quotes/spreads/session structure with a clearly confirming risk-adjusted edge. → `CROSS_BROKER_ROBUST`.

### Finding 2 — Aggregation-method robust (Arm 1 vs Arm 2)

- **Observation:** the last-source-close aggregation (Arm 2) gives Portfolio B Sharpe **7.22 (LB 6.104)**, Calmar
  LB **13.32** → CONFIRM. The two arms are **near-identical**: domain-bar counts match exactly except USTEC-1h and
  US2000-1h (+1 bar each under the last-close label, which retains one trailing window the boundary-fence drops);
  per-cell nets are identical to ~1e-5 on all 4h cells and differ only marginally on the two 1h cells.
- **Evidence:** `results/per_cell_pps.csv` (CANON vs ALTAGG rows), `run_metadata.json` domain-bar counts,
  `plots/pps_arm_comparison.png`.
- **Interpretation:** the timestamping rule is **near-inert** for this strategy — it can only move the
  trailing/incomplete window, which rarely changes the resolved event population. The confirmed edge is not an
  artifact of bucket-boundary labeling. → `AGGREGATION_ROBUST`.

### Finding 3 — Broad-based, no masking, EURJPY-4h recovers

- **Observation:** all **8/8 cells are net-positive on both arms** (PPS net ci_low +0.0105 … +0.0941). Notably
  **EURJPY-4h** — the cell flagged `NOISE_DEGRADED` and net-**negative** on the INFR-003 holdout (−0.006, ci_low
  −0.031) — is net-**positive** on PPS (+0.026, ci_low +0.0105). The drop-one masking check removes the largest
  contributor (US2000-1h) and B **still confirms** (Sharpe LB 5.48 / 5.57; no flip).
- **Evidence:** `results/per_cell_pps.csv`, `integrity.json` (`masking.label_flips=false`),
  `plots/pps_per_cell_net.png`.
- **Interpretation:** the portfolio headline is not carried (or hidden) by any single cell; the replication is
  genuinely broad-based.

### Finding 4 — Retention vs INFR-003 (descriptive, slice-caveated)

- **Observation:** per-cell PPS nets sit within ~10–25% of the EXP-097 INFR-003 holdout values (4h core slightly
  lower, 1h pair slightly higher); the portfolio retention ratio (PPS full-timeline LB ÷ INFR-003 holdout LB) ≈
  1.25–1.45.
- **Evidence:** `results/retention.json`.
- **Interpretation (caveat):** this ratio compares **different slices** — PPS full-timeline (n=251 weeks) vs the
  INFR-003 holdout-only window (n=80 weeks). It should be read as "PPS confirms at least as strongly on independent
  data," **not** as "the edge is ~25% stronger." It is descriptive context only and does not enter the binding
  label (PPS B LB 5.97 ≫ band 2.00 regardless).

### Finding 5 — Integrity

- **Observation:** MTM conservation ≤ 2.8e-14 ATR (8/8 cells, both arms); determinism replay byte-identical (A &
  B); binding-statistic determinism true; causal-weight + causal-fill assertions pass in the evaluable region;
  real-price only; INFR-003 holdout never loaded.
- **Evidence:** `results/integrity.json`, `results/mtm_conservation_*.csv`.
- **Interpretation:** the replication is the *same* frozen computation on *different* data — credible.

## Hypothesis Verdict

**SUPPORTED (non-binding robustness disclosure): `CROSS_BROKER_ROBUST = true` ∧ `AGGREGATION_ROBUST = true`.**

The deployed RSI-2 fade portfolio is robust to (i) the broker/data feed and (ii) the bar-aggregation timestamping
method: primary Portfolio B clears the inherited band on both arms, broad-based and masking-robust. This rules out
the two overfitting hypotheses EXP-097 could not separate. Per programme discipline, EXP-098 **cannot upgrade or
revoke** EXP-097's spent `DEPLOYABLE_CONFIRMED` verdict — it stands as a strengthening robustness companion.

## Limitations

- **Non-binding by construction.** A robustness cross-check, not a sanctioned holdout; cannot change the deployment
  verdict.
- **Full-timeline read.** PPS was read in full (operator decision); legitimate because the model is fully frozen
  (no selection), but it means PPS is now "touched" as a robustness dataset — any *future binding* use needs its
  own governance.
- **Slice non-equivalence** in the retention ratio (Finding 4) — descriptive only.
- **In-family scale.** The ~7 Sharpe is a diversified, vol-anchored in-family figure (consistent with EXP-097);
  not a claim of a higher live edge than the EXP-097 deployment estimate.

## Follow-up (new scopes only — not extensions)

- A live/forward-paper monitoring scope for the deployed book on the production feed (separate governance).
- The registered deferred levers (vol-regime, contrarian, 25/75 sizing, 15m domain, faster-cost,
  instrument/domain expansion) — each its own dated `D0-amendment-*` + slot decision.
- Any *binding* use of PPS (e.g. a sanctioned second-feed holdout) — its own governance and read accounting.
