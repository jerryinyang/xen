# EXP-098 — Audit

**Date:** 2026-06-25 · **Auditor:** experiment-auditor (Stage 5) · **Verdict:** **PASS (0 Critical / 0 Warning /
3 Info)** · **Materiality:** no verdict-material finding; the robustness label is reproducible and non-binding on
EXP-097.

Scope/plan/code reviewed against `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, the results under
`results/`, and the reused modules (EXP-096/095/090, `xen.portfolio`, `xen.domain_bars`, `xen.bar_aggregator`).

## 1. Implementation correctness

- **Verbatim reuse confirmed.** The substrate (`E90.build_cell_context`, `resolve_arm`), the entry-fill
  (`resolve_entry_fills`), the cost overlay, the ERC/MTM/breaker (`xen.portfolio`), and the binding statistic
  (`E95.series_risk_metrics`) are imported and called unchanged. The only two deltas are the data source (PPS) and
  the Arm-2 aggregation label, exactly as scoped.
- **Arm-2 aggregation isolation verified.** `aggregate_ohlc_lastclose` is byte-equivalent to
  `xen.bar_aggregator.aggregate_ohlc` except `pl.last("CloseTime")` replaces the bucket-boundary label
  (line-checked). Injection via the `aggregation_arm()` context manager rebinds `E90.build_domain_bars` only for
  Arm 2 and restores it in a `finally` — no leakage across arms (confirmed: Arm 1 domain-bar counts equal the
  deployed construction; the manager restores the original symbol).
- **Independent-data discipline verified.** `load_full_pps_1m` raises on any non-`PPS_DIR` path;
  `infr003_holdout_loaded=false` in `integrity.json` and `run_metadata.json`; only `data/timebars/pps/` is opened.
  The INFR-003 dataset and its sealed global holdout are not loaded. `counted_test_reads=0`, `candidate_slots=0`.
- **Eval boundary verified.** `H_eval = grid_start + LOOKBACK_STEPS·STEP_SECONDS` = 2026-09-01 region (2021-09-01
  in the data), i.e. the first step with a full trailing-90-day covariance window — an estimator-warmup boundary,
  not a holdout. n_eval_steps ≈ 42k hourly steps / 251 weeks per arm.
- **Integrity battery PASS (both arms):** MTM conservation Σ(marks)=realized net ≤ 2.8e-14 ATR (all 8 cells);
  determinism replay byte-identical A & B; binding-statistic determinism (same seed → identical Sharpe/Calmar LB);
  causal-weight assertion (future grid rows do not move a past evaluable rebalance weight, row 23184); causal-fill
  assertion (a pre-signal 1m bar does not move an evaluable entry fill, event 98). Real-price only.
- **Output reproducibility:** 11 output hashes recorded; determinism replay covers the binding path.

## 2. Verdict forensics (autonomous)

**Headline.** Both arms label **ROBUST** → `CROSS_BROKER_ROBUST = true` ∧ `AGGREGATION_ROBUST = true`. Primary
Portfolio B PPS Sharpe LB **5.968 (CANON) / 6.104 (ALTAGG) > band 2.00**, co-binding Calmar LB **12.53 / 13.32 >
0**; A co-confirms (LB 6.15 / 6.30 > 1.75).

**Per-stratum re-derivation (masking check — the pooled headline is NOT masking heterogeneity).** All **8 of 8
cells carry a positive PPS net ci_low on BOTH arms** (CANON range +0.0105 … +0.0941; ALTAGG near-identical). This
is *stronger* than the binding object requires and stronger than EXP-097's INFR-003 holdout, where EURJPY-4h was
net-negative (−0.006, ci_low −0.031). On PPS, **EURJPY-4h is net-positive** (+0.026, ci_low +0.0105) on both arms
— the one previously-degraded cell recovers on the independent feed. The drop-one masking check removes the
largest contributor (US2000-1h, ~449/457 summed MTM) and B **still confirms** (Sharpe LB 5.48 / 5.57 > 2.00;
Calmar LB 10.30 / 10.43 > 0) → `label_flips=false`. No single cell carries the label; no broken cell is hidden.

**Mechanism (why ROBUST).** (a) *Cross-broker:* the bare RSI-2 fade + EXIT-RCT edge is a short-horizon
reversion-completion geometry whose net expectancy is driven by ATR-normalized cost being small on the slower
domain — a property of price structure, not of one broker's quote feed — so it reproduces on the PPS feed with
per-cell nets within ~10–25% of the INFR-003 values (4h core slightly lower, 1h pair slightly higher). (b)
*Aggregation:* the last-source-close relabel (Arm 2) differs from the bucket-boundary label (Arm 1) **only on
trailing/incomplete windows** the fence would otherwise drop — domain-bar counts are identical across arms except
USTEC-1h/US2000-1h (+1 bar each), and per-cell nets are identical to ~1e-5 except those two cells. The aggregation
method is therefore **near-inert** for this strategy, which is precisely why AGGREGATION_ROBUST holds so cleanly.
(c) *High Sharpe (~7):* structural diversification of 8 low-correlation cells vol-anchored to 10% — in-family with
EXP-097's analysis/holdout LBs (~4.9); not a bug. Provenance: per-arm `ann_vol` ≈ 0.105–0.109 (the 10% anchor),
MaxDD ≈ 0.048–0.060 (comparable to EXP-097's 0.034–0.06).

**Gate-shape check.** The binding gate (annualized Sharpe LB + co-binding Calmar LB on the weekly portfolio
series) is the correct instrument for a risk-adjusted **deployment** claim, and it *sees* the effect: the edge is a
diversified positive-mean return stream. The known **mean-carried / median-fragile** shape of the 1h tier is
faithfully reproduced and disclosed (USTEC-1h net median −0.031 with mean +0.051; US2000-1h median −0.034 with
mean +0.060) — the portfolio statistic is mean/vol-based (appropriate for deployment P&L), and the per-cell median
negativity is reported, not hidden. The 4h core is mean-AND-median positive on EURUSD/XAUUSD/USDCHF/AUDJPY-4h. No
"wrong instrument for the shape" issue.

## 3. Findings

- **Info-1 (slice non-equivalence in the retention companion).** `retention.json` divides the PPS **full-timeline**
  Sharpe LB (n=251 weeks) by EXP-097's **holdout-only** INFR-003 LB (n=80 weeks) → ratio ≈ 1.25–1.45. This is
  **not** a like-for-like decay measure (different slices and n); it reads as "PPS confirms at least as strongly,"
  not "the edge is 25% stronger." Already labelled descriptive/non-binding in the file; does **not** move the
  binding label (PPS B LB 5.97 ≫ 2.00 regardless of the comparison). Recommend the results write-up state the
  slice caveat explicitly.
- **Info-2 (provenance arg).** `resolve_cell_noise(ctx, ts_lo=file_start_epoch, …)` makes the disclosure-only
  `test_*` provenance fields span the full series; they do not enter any binding number (binding metric governed
  solely by `H_eval`). Confirmed by code path. Immaterial.
- **Info-3 (XAUUSD-4h coverage).** XAUUSD-4h dropped-fraction 0.199 (highest), n_domain 6471 — within the
  substrate's coverage tolerance and identical across arms; net-positive (ci_low +0.083). No exclusion warranted;
  noted for transparency.

## 4. Materiality statement

No finding can move a verdict-bearing number: the binding label is the per-arm Portfolio-B band test, which clears
by >3.9 Sharpe-LB margin on both arms and survives the drop-one masking check; all integrity assertions pass; the
three Info notes are descriptive/provenance only. The label is **non-binding on EXP-097** by construction
(`exp097_verdict_unchanged=true`). No fix-and-rerun required.

**VERDICT: PASS.**
