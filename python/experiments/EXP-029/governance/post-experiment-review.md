VERDICT: APPROVE

## Post-Experiment Governance Review: EXP-029

### Core Constraints

| Constraint | Check | Status |
|-----------|-------|--------|
| Simplicity | Block bootstrap on inversion rate; no parametric assumptions; direct point comparison to 1m baseline. Appropriately simple for a detection-rate study. | PASS |
| No academic-finance pitfalls | Block bootstrap (n=2,000, block=50) preserves temporal dependence. No normality, stationarity, or i.i.d. assumptions made. | PASS |
| Single hypothesis | One question: does 15m IFVG rate drop materially below 50%? Detection-only scope, no return outcomes, no compound tests. | PASS |
| Complexity budget | 1 statistical test / 1; 4 plots / 4; 1 new module (bar_aggregator.py) / 1. Budget respected. | PASS |
| No scope creep | No return outcomes, no rule redesign, no second timeframe added. | PASS |

### OOS Holdout

| Check | Status |
|-------|--------|
| Final 30% never loaded | PASS — `load_analysis_timebars` uses lazy scan, sorts by CloseTime, slices first 70% before collect. Holdout never materialized. |
| Aggregation applied to analysis-set slice only | PASS — `aggregate_ohlc` receives only the holdout-excluded 1-minute frame. |
| Chronological split | PASS — 70/30 train/test applied to 15-minute frame by row position on CloseTime-sorted series. |

### Look-Ahead Bias

| Check | Status |
|-------|--------|
| ATR14Prior uses only prior bars | PASS — `rolling_mean(14).shift(1)` |
| FVG detection uses only CloseTime-ordered bars | PASS — vectorized on sorted 15-minute frame |
| Lifecycle walks forward from formation bar | PASS — `start = creation_idx + 1` |

### Real-Price Discipline

| Check | Status |
|-------|--------|
| No return or P&L outcomes | PASS — experiment is detection-only |
| No synthetic prices used | PASS — 15-minute OHLC is a resampled time-bar view; no HA/Renko prices |

### Results and Report Quality

| Check | Status |
|-------|--------|
| Honest reporting | PASS — AGAINST verdict correctly stated; lifecycle sensitivity result that isolates lifecycle duration vs timeframe effect is clearly reported |
| Uncertainty acknowledged | PASS — bootstrap CIs reported; count floors verified; limitations noted |
| No overreaching | PASS — AGAINST verdict correctly applied; the 8-bar finding is presented as diagnostic, not as a new positive result |
| Index updated | PASS — both `python/experiments/INDEX.md` and `docs/experiments-docs/INDEX.md` updated |

### Audit Quality

Audit (PASS, 0 critical, 1 warning, 3 info) is complete and commensurate with experiment complexity. The Warning (displacement overlap 0.0 due to timezone mismatch) is correctly classified and does not affect the verdict. Numerical spot checks verified inversion rates, verdict derivation, and ATR look-ahead.

### Phase Alignment

EXP-029 is aligned with the Phase 004A design.md pre-phase objectives. It answers the IFVG selectivity question as specified. The AGAINST finding provides the required Branch B directive: "Continue as selectivity redesign; unmodified IFVG remains too permissive."
