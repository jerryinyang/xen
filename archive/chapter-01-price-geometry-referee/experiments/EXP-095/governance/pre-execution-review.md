# EXP-095 — Stage 4 Pre-Execution Governance Review

**Experiment:** EXP-095 — Portfolio Construction & Online-Adaptive Risk Model (RSI-2 Fade, 8 confirmed cells)
**Family / HYP:** `CF-MR-001` / `HYP-003` · **Phase:** 022 (batch 3) · **Date:** 2026-06-24
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, `python/src/xen/portfolio.py`
**Governing design / D0:** `docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/{design.md, D0-predeclarations.md}`
**Review history:** cycle 0 — REVISE (Finding 1, null-construction densification); cycle 1 — **APPROVE** (Finding 1 fixed & verified).

---

## Verdict

```
VERDICT: APPROVE
```

Finding 1 (the blocking null-construction bug) is resolved and verified. All other checks
(holdout, look-ahead, real-price, determinism, registry/ledger, complexity budget,
per-stratum/aggregate doctrine) passed in cycle 0 and are unchanged — the cycle-1 fix
touched only `xen.portfolio.block_permute_zero_mean`, with no edit to `run_experiment.py`,
the scope, or the plan. Proceed to the manual execution gate.

---

## Finding 1 — RESOLVED (cycle 1)

**Was (cycle 0, BLOCKING):** `block_permute_zero_mean` re-centered the **whole grid**
(`out - out.mean(axis=0)`), turning every structural flat-step zero into `-mean`. That
densified the matrix and broke the `!= 0.0` trade-mask the construction path keys on
(`_trailing_trade_counts` → active/warmup gate; `breaker_multipliers` → Portfolio B), so the
null A/B portfolios did not mirror the real A/B and the calibrated FPR was the FPR of a
different construction than the rule G-022a will freeze.

**Fix (verified):** `portfolio.py:515–528` now re-centers **trade entries only** — subtracts
each column's mean over its non-zero entries, applied only at non-zero positions, leaving
structural zeros at exactly `0.0` (vectorized; `counts > 0` divide guard). The no-edge
condition is enforced on the *trade stream* (the construction's unit of a "trade"), without
densifying the matrix. The docstring documents the no-edge condition and the real-vs-null
parallelism rationale.

**Verification (pure-function unit check, did not run the experiment):**
- nonzero fraction null ≈ 0.12 vs source ≈ 0.10 (no densification; previously would be ≈1.0);
- per-cell **trade** expectancy zeroed to machine epsilon (|mean| < 1e-12) — matched no-edge;
- trailing trade counts stay sparse (e.g. 3/10/4 at row 30) → active/warmup gate still bites,
  so the null construction path mirrors the real one;
- block-permutation still resamples intact rows → cross-cell covariance + within-cell
  autocorrelation preserved; `null_b_block_permute_returns` form unchanged (not a path
  rotation, not built around a signal-derived target).

**Carried to experiment-quant-analyst (non-gating):** annotate analysis-plan §Step-8
("re-center each cell to zero mean") to read explicitly as *trade-entry* re-centering. Wording
only; binding behavior is now in code.

---

## Non-blocking notes (carried to results-stage disclosure; do not gate)

- **N1 (Info)** — hourly co-reported metrics (`ann_vol`/`Calmar`/`ann_return`) and the vol
  anchor use calendar-hour annualization (`≈8766`) over a grid with structural closed-market
  zeros. The **binding** Sharpe + lower bound run on the **weekly-aggregated** series
  (`≈52.18`, correct) and Sharpe is anchor-invariant, so the binding read is unaffected.
  Record the calendar-hour basis in `run_metadata.json` / `results.md`.
- **N2 (Info)** — Portfolio B applies the breaker multiplier, renormalizes survivors to sum 1,
  then re-anchors to 10% vol (`portfolio.py:337–345`): B de-risks in **expectancy/composition**,
  not total vol. Defensible reading of D3; disclose explicitly in `results.md` (the A−B read is
  descriptive / non-binding).
- **N3 (Info)** — `BITE_FIRE_FLOOR = 0.80` is a conventional detection-power floor and
  `BITE_PLANT_SHARPE = 1.0` is a generic materiality-scale edge from the null's own scale
  (correctly not signal-derived). State 0.80 is a conventional floor, not a calibrated threshold.

---

## Checklist (passing items — confirmed cycle 0, unchanged cycle 1)

| Check | Status | Evidence |
|---|---|---|
| Single falsifiable question | PASS | scope §1 — portfolio risk-adjusted vs best single cell + A-vs-B adaptability. |
| Holdout untouched | PASS | `load_analysis_1m` slices `[0, int(total*0.7))`, asserts height, never materializes holdout; `holdout_untouched=true`. |
| Chronological split | PASS | `sort("CloseTime")` then index slice; cross-domain alignment by `CloseTime` epoch, never bar index. |
| Look-ahead / causality | PASS | trailing windows strictly `<t`; causal-weight perturbation unit assertion (`run_experiment.py:667–686`). |
| Real-price discipline | PASS | per-cell net returns from EXP-090 substrate (real OHLC + intrabar fill); no HA/brick prices; `real_prices_only=true`. |
| Provenance ("reused verbatim") | PASS | deterministic re-resolution + hard provenance gate vs EXP-093 `test_per_cell.csv` (≤1e-9 ATR; exact counts). |
| Per-stratum / aggregate doctrine | PASS | portfolio = design-ratified deployment estimand (D4); per-cell baselines disclosed (LESSON-001); A and B calibrated separately; `statistic_ready` is the genuine G-022a A∧B conjunction with per-portfolio detail. |
| Null form + fidelity | PASS | block-permute common time index (not path rotation), not signal-derived; **trade-mask preserved (Finding 1 fix)** so null A/B mirror real A/B. |
| Determinism | PASS | seeds via `seed_for` off master `20260624`; threads pinned; byte-identical second-pass assertion. |
| Registry — family/lever | PASS | `cf-mr-001.md` ADMITTED (BINDING)/TRADABLE; HYP-003 active. |
| Registry — multiplicity | PASS | `multiplicity-registry.md:895–940` Phase-022 batch + EXP-095 (SCOPED, 0/0); portfolio params + NEW binding statistic registered. |
| Ledger — TEST reads | PASS | `test-read-ledger.md:285–295` EXP-095 = portfolio-aggregate disclosure, 0 counted reads; 8 cells within 11 carried strata at 1/2; holdout sealed. |
| No optimization | PASS | all hyperparameters frozen at D0 values; brackets computed as disclosed sensitivity only, never used to select. |
| Complexity budget | PASS | 1 binding test + calibration; 5 plots; 1 module — matches scope §9. |
| Code conventions | PASS | sectioned, typed, no import-time side effects, `tqdm` on outer loops, bounded bootstrap, NaN-not-inf on zero denominators; cycle-1 fix is vectorized with a divide guard. |

---

## Manual Execution Gate

```
Pre-execution review: APPROVED

Experiment: EXP-095 - Portfolio Construction & Online-Adaptive Risk Model (RSI-2 Fade, 8 confirmed cells)
Code: python/experiments/EXP-095/code/run_experiment.py
Expected output: python/experiments/EXP-095/results/

Resolves the 8 G-021-confirmed per-cell EXIT-RCT streams through the frozen EXP-090/093 substrate
(provenance-gated vs EXP-093), builds causal ERC Portfolio A vs circuit-breaker Portfolio B over the
analysis set, compares risk-adjusted performance to the best single cell, and calibrates + bite-checks
the new portfolio-level holdout confirmation statistic for G-022a — analysis-set only, holdout never loaded.

Please run the experiment code and confirm when complete.
```
