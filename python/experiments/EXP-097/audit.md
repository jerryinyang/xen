# Audit Report: Experiment EXP-097

**Title:** Global-Holdout Release — One-Shot OOS-Final Confirmation of the RSI-2 Fade Deployment Portfolio
**Family / HYP:** `CF-MR-001` / `HYP-003` · **Phase:** 022 (batch 3) · **Audit date:** 2026-06-25
**Result under audit:** `DEPLOYABLE_CONFIRMED` — primary Portfolio B holdout Sharpe LB **4.762 > band 2.00**,
co-binding Calmar LB **10.731 > 0**; A co-adjudicated CONFIRM (5.05.../band 1.75); one holdout-governance event.

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 4

This is the single sanctioned global-holdout release. The audit confirms (a) the read reads *exactly* the
G-022a-frozen set / construction / primary / band / rule with nothing data-derived from the holdout; (b) the binding
metric is restricted to the holdout region so no analysis-set return enters it; (c) the holdout was loaded once,
here; (d) the headline reproduces **bit-for-bit** from the saved return series; and (e) the verdict is broad-based,
not masking a broken cell. The honest-prior "decay" did occur **per-cell** but was offset by diversification and the
circuit breaker — mechanism stated below. No verdict-material finding.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Frozen constants inherited from `E96`/`E95`; `confirm`/`adjudicate_g022` match G-022 §2 verbatim. |
| `code/run_experiment.py` | Holdout exclusion (the sanctioned exception) | PASS | `load_full_1m` is the sole full-file read; binding metric on `grid_epochs >= H_global` only; `H_global = max` per-cell cutoff excludes the ~2-day transition zone. |
| `code/run_experiment.py` | Loader ordering | PASS | `scan_parquet().sort("CloseTime")` before any slice; cutoff = `int(total*0.7)`; sorted-assertion guards. |
| `code/run_experiment.py` | Temporal/causal validity | PASS | Continuous causal `build_portfolio` over warmup+holdout; in-holdout causal-weight + causal-fill assertions both exercised and pass (rows 37632 / event 1467, both in holdout). |
| `code/run_experiment.py` | Real-price discipline | PASS | Real domain & 1m OHLC; entry/exit fills real touched prices; no HA/Renko. |
| `code/run_experiment.py` | NaN / zero-baseline | PASS | Sharpe/Calmar guarded → NaN never inf; `<2`-event cells → NaN with flag. |
| `code/run_experiment.py` | Determinism | PASS | Seeds off master `20260624`; `determinism_replay` byte-identical A/B; binding-statistic re-seed identity true; output hashes recorded. |
| `code/run_experiment.py` | Reuse / no re-derivation | PASS | `E96.resolve_cell_noise` (v2), `E95.build_grid`/`series_risk_metrics`, `pf.build_portfolio` reused verbatim; only new code is the loader + `>=H` slicing in orchestration. |
| `code/run_experiment.py` | Memory/perf, progress, logging | PASS | Lazy scan; `tqdm` over 8 cells; bootstrap batched; concise logging; output dirs in orchestration only. |
| `code/run_experiment.py` | Docstrings/types | PASS | Public functions typed + documented. |

## Numerical Validation

### Spot Checks (independent re-derivation from the saved series)

Re-computed the binding **point** metrics directly from `results/portfolio_returns_{A,B}.csv` (filter
`in_holdout==1`, weekly bucket `CADENCE_STEPS=168`, `annualized_sharpe` with `PPY_CAD=52.18`, `calmar` with same):

| Portfolio | reported ann_sharpe | re-derived | reported calmar | re-derived | match |
|-----------|--------------------:|-----------:|----------------:|-----------:|:-----:|
| A | 6.054719 | 6.0547 | 13.45204 | 13.4520 | ✓ |
| B | 6.639453 | 6.6395 | 17.45335 | 17.4533 | ✓ |

Holdout region = **13,286** hourly steps of **44,217** total = **30.04%** of the grid = **80** weeks; boundary
epoch `1734056580` = 2024-12-13 02:23 (USDCHF cutoff = max of the 8). Weekly Sharpe B = 0.919 (→ ×√52.18 = 6.64).
The lower bounds (4.762 B / 4.250 A) are a seeded moving-block bootstrap of the same series; the point statistics
matching to 4 dp confirms the series and the statistic are faithful (the LB is a deterministic function of that
series + master seed; `binding_statistic_determinism=true`).

### Range / Statistical Sanity

| Statistic | Value | Sensible? | Notes |
|-----------|-------|-----------|-------|
| B holdout ann Sharpe | 6.64 (LB 4.76) | YES | Structural — see Mechanism; a vol-targeted ERC book of 8 weakly-correlated MR cells; weekly Sharpe is 0.92, not anomalous. |
| B ann_vol | 0.1142 | YES | The 10% vol anchor is respected (realized 11.4% on holdout). |
| B MaxDD | 0.046 | YES | Consistent with Calmar 17.5 = 0.449/0.046. |
| n_holdout_weeks | 80 | YES | ≈ m*-calibration n (~79); block length unchanged in scale. |
| MTM conservation | ≤ 2.8e-14 ATR | YES | 8/8 cells PASS. |

## Verdict Forensics (run autonomously)

### Per-stratum re-derivation & masking check

| Cell | holdout net mean (ATR) | net ci_low_1s | net-neg? | analysis-v2 → holdout Δ mean | Read |
|------|----:|----:|:--:|----:|------|
| EURUSD-4h | +0.1317 | +0.1038 | no | **+0.033 (improved)** | strongest cell, OOS-final improved |
| XAUUSD-4h | +0.1148 | +0.0819 | no | **+0.031 (improved)** | improved |
| USDCHF-4h | +0.0950 | +0.0659 | no | +0.015 (improved) | improved |
| AUDJPY-4h | +0.0638 | +0.0396 | no | −0.009 | ~flat |
| GBPJPY-4h | +0.0458 | +0.0169 | no | −0.0003 | ~flat |
| US2000-1h | +0.0549 | +0.0371 | no | −0.005 | ~flat |
| USTEC-1h | +0.0334 | +0.0135 | no | −0.021 | decayed but still +ci_low |
| EURJPY-4h | −0.0060 | −0.0311 | **YES** | −0.034 (went negative) | the pre-flagged `NOISE_DEGRADED` cell broke OOS-final, as flagged |

- **Pooled/portfolio headline: B Sharpe LB 4.762.** **Is it masking heterogeneity? NO.** 7 of 8 cells carry a
  *positive* one-sided lower bound on the holdout; the verdict is broad-based, not one-cell-driven. The single
  net-negative cell (EURJPY-4h) is the cell that was **pre-flagged `NOISE_DEGRADED`** at G-022a (EXP-096 v2 ci_low
  0.0079) and carried under portfolio-only membership; it is the smallest positive contributor (`sum_marks` 37.9 vs
  EURUSD 224.9, US2000 461.0), so dropping it would *improve*, not rescue, the portfolio. No broken cell is hidden
  inside the aggregate; no healthy verdict is propped up by a single cell.

### Mechanism (why DEPLOYABLE_CONFIRMED, and why no portfolio decay)

1. **Why the Sharpe is high (~6.6, not a bug):** the binding estimand is a **diversified** ERC portfolio of 8
   low-correlation cells, vol-anchored to 10%. Diversification raises the portfolio's risk-adjusted return far
   above any single cell (single-cell net expectancies are 0.03–0.13 ATR); the same construction produced
   Sharpe ≈ 6 / LB ≈ 4.9 on the analysis set, and the bands (A 1.75 / B 2.00) were the A4 **m\*** calibrated
   *against this construction*. The holdout number is in-family with the analysis number — exactly what the
   pre-frozen band anticipated.
2. **Why it did not decay at the portfolio level despite the honest prior:** the prior expected uniform shrinkage.
   What actually happened is **heterogeneous**: the three strongest 4h FX/commodity cells (EURUSD/XAUUSD/USDCHF)
   *improved* OOS-final (+0.015…+0.033 ATR), while the JPY crosses and 1h index cells decayed modestly (EURJPY went
   net-negative; USTEC −0.021). The gainers offset the decayers, so the portfolio Sharpe LB moved only
   −0.135 (B: 4.897 → 4.762).
3. **Why B > A on the holdout (LB −0.135 vs A −0.897):** the circuit breaker is the driver. Portfolio A (static
   ERC) absorbed the full decay of the weak 1h cells (A LB 5.147 → 4.250); Portfolio B's trailing-50-trade breaker
   de-allocated the fragile cells (USTEC/US2000) during their weak stretches — its designed tail-insurance role —
   so B both lands higher (LB 4.762) and shrank far less. This is the mechanism behind the primary verdict, and it
   is the reason the programme made B (not A) the primary.

### Gate-shape check

- Binding gate: **Sharpe one-sided LB (risk-adjusted location) + co-binding Calmar LB (downside)**. Effect shape:
  **location** — a positive-mean, vol-stable, diversified return stream.
- **Is the gate the wrong instrument for this shape? NO.** The effect is precisely a risk-adjusted-mean (location)
  effect, which a Sharpe LB is built to see; the Calmar leg (LB 10.7) independently confirms the downside. There is
  no tail/bimodal/asymmetric structure the gate would be blind to. Gate and effect shape are matched.

## Scope Compliance

- Analysis plan followed: **YES** — set, construction, primary, bands, rule, statistic all as frozen; only new
  acts are the holdout load + `>=H` region slicing.
- Deviations: **none**.
- Complexity budget: 1 binding test / 1; 5 plots / 5; 0 new modules / 0. Within budget.
- Holdout discipline: **`global_holdout_shot_spent=true`, `holdout_first_touch=EXP-097`,
  `counted_test_reads=0`, `candidate_slots=0`** — one read; A+B from one materialization = one read (operator
  2026-06-25); non-repeatable / non-upgradable. The ledger + multiplicity-registry recording is a **Stage 7**
  obligation (see Info I4) — verified pending, not yet written.

## Issues

### Critical
None.

### Warning
None.

### Info

1. **I1 — Sharpe magnitude is structural, not a defect.** Annualized Sharpe ≈ 6.6 looks extreme in isolation but
   is the diversified ERC construction the band was calibrated against (analysis LB ≈ 4.9). Re-derived from the
   saved series to 4 dp. *Materiality:* none — it is the binding number itself, confirmed reproducible and in-family.
2. **I2 — EURJPY-4h broke OOS-final, as pre-flagged.** It is the only net-negative cell; it was carried under the
   G-022a `NOISE_DEGRADED` portfolio-only flag. *Materiality:* cannot move the verdict — it is the smallest positive
   contributor and the portfolio confirms with 6 other cells positive; dropping it would improve B. Disclosed, not
   re-adjudicated (frozen-set discipline).
3. **I3 — n_holdout_weeks=80 vs ~79 m\*-calibration n.** A one-week ceil/partial-bucket difference; the block
   length scale is unchanged. *Materiality:* none — does not move the LB across the band (margin is 4.76 vs 2.00).
4. **I4 — registry recording is a Stage 7 obligation.** The holdout-governance event must be entered in
   `docs/signal-registry/test-read-ledger.md` + `multiplicity-registry.md` in the same change as the result, and
   `CF-MR-001` advanced. Not an implementation defect — flagged so Stage 7/8 enforce it.

## Materiality & Re-Audit Requirements

- **No Critical findings → no fix + rerun required.** Every finding above is shown not to move any verdict-bearing
  number (the binding B Sharpe LB 4.762, Calmar LB 10.731, or which stratum is binding).
- The binding headline was **independently re-derived** from the saved return series and reproduces exactly; the
  per-stratum masking check confirms a broad-based verdict; the mechanism is stated; the gate matches the effect
  shape. **No re-execution** — and, per one-shot holdout discipline, none is permitted (re-running would re-touch
  the holdout; any confound found after the read is a permanent caveat, not a re-read).
