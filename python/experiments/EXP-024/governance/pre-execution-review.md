# Pre-Execution Governance Review: EXP-024

**Experiment**: EXP-024 - Second Candle Open Execution Timing
**Artifacts reviewed**: `scope.md`, `analysis-plan.md`, `code/run_experiment.py`
**Review date**: 2026-05-26
**Revision cycle**: 2 of 2

---

## Scope Review

| Check | Status | Notes |
|-------|--------|-------|
| Single falsifiable question | PASS | "Does second-candle-open improve or degrade entry quality versus simpler post-confirmation entries?" |
| Boundaries defined | PASS | 4 variants explicit; confirmation source = EXP-021; no new filters |
| Holdout exclusion stated | PASS | Final 30% excluded; nested split documented |
| Real-price outcome discipline | PASS | "All outcomes use real time-bar OHLC prices aligned by timestamp" |
| Success/failure criteria measurable | PASS | SecondCandleOpen "not worse" on >= 3 instruments with >= 50 risk-feasible confirmation-close and second-candle-open comparisons per segment; CI and MAE criteria predeclared |
| Complexity budget respected | PASS | Tests 2 / 2, plots 4 / 4, modules 1 / 1 |

## Analysis Plan Review

| Check | Status | Notes |
|-------|--------|-------|
| Method justification present | PASS | All 3 steps include "why this method" and "simpler alternative considered" |
| Execution timing isolated from confirmation quality | PASS | Confirmation set taken directly from EXP-021 without modification |
| Non-parametric bootstrap | PASS | n=10,000, seed=42, distribution-free |
| Interpretation guide predeclared | PASS | "Not worse" criterion defined: CI does not strictly exclude zero negatively on Return_R AND MAE does not strictly worsen |
| Budget compliance | PASS | 2 tests / 2, 4 plots / 4 |

## Code Review (post-revision)

| Check | Status | Notes |
|-------|--------|-------|
| Import side effects absent | PASS | `mkdir` only inside `run_experiment()` |
| Holdout exclusion enforced | PASS | `load_analysis_timebars()` enforces 70% split |
| Temporal ordering by CloseTime | PASS | All bar lookups use CloseTime nanoseconds |
| Confirmation source loaded correctly | PASS | EXP-021 entry_outcomes.csv filtered to IFVGClose rows only and now required to carry `MinRisk1R` for inherited-stop feasibility |
| ConfirmationClose, ImmediateNextOpen, SecondCandleOpen variants | PASS | Correctly derived from bars after InversionTime |
| Real-price outcomes | PASS | `compute_real_price_outcome()` called for all variants |
| `_is_invalidated()` logic (revised) | PASS | Conditions corrected: Bearish IFVG invalidated by close < LowerBound; Bullish IFVG invalidated by close > UpperBound |
| `_zone_touch()` logic (revised) | PASS | Conditions corrected: Bearish IFVG touch = bar_low <= UpperBound (from above); Bullish IFVG touch = bar_high >= LowerBound (from below) |
| FirstRetest entry price (revised) | PASS | Entry price corrected: Bearish IFVG uses UpperBound (zone top, touched from above); Bullish IFVG uses LowerBound (zone bottom, touched from below) |
| Inherited-risk feasibility guard (revised) | PASS | All timing variants inherit `MinRisk1R` from the confirmation source; infeasible rows are excluded from R-based and slippage summaries |
| Bounded plotting | PASS | `PLOT_MAX_POINTS = 5_000`, deterministic rng, `clip()` for R caps |
| Bootstrap parameters | PASS | REPS=10,000, SEED=42, 95% CI, mean difference |
| Organisation | PASS | Clear section separation throughout |

## Issues Resolved

| Issue | Resolution |
|-------|-----------|
| CRITICAL: `_is_invalidated()` had conditions swapped — Bearish IFVG returned True on `close > UpperBound` (bullish continuation, not invalidation); Bullish IFVG returned True on `close < LowerBound` (bearish continuation, not invalidation) | Fixed to: Bearish IFVG = `close < LowerBound`; Bullish IFVG = `close > UpperBound` (revision cycle 1) |
| CRITICAL: `_zone_touch()` had conditions swapped — Bearish IFVG checked `bar_high >= LowerBound` (near-always True after IFVG fires); Bullish IFVG checked `bar_low <= UpperBound` (near-always True) | Fixed to: Bearish IFVG = `bar_low <= UpperBound`; Bullish IFVG = `bar_high >= LowerBound` (revision cycle 1) |
| WARNING: FirstRetest entry price used wrong zone boundary — Bearish IFVG used `ifvg_lower` (zone bottom) instead of `ifvg_upper` (zone top, touched from above); Bullish IFVG used `ifvg_upper` instead of `ifvg_lower` | Fixed: swapped assignments (revision cycle 1) |
| CRITICAL/WARNING from post-execution audit: near-zero inherited risk invalidated timing-rule R and slippage metrics | Scope and plan now define an inherited-risk feasibility guard; code carries `MinRisk1R` from the confirmation source and excludes infeasible rows from R-based and slippage summaries (revision cycle 2) |

---

## Verdict

```text
VERDICT: APPROVE
```

All critical and warning issues resolved in revision cycle 1. No outstanding issues.
