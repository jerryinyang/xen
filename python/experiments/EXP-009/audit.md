# Audit Report: Experiment EXP-009

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

EXP-009 measures a broadened, fixed, untuned simple-strategy set against the frozen EXP-003 MDE map. The code uses the frozen `xen.referee_calibration` harness for domain construction, returns, split boundary, costs, referee legs, and Donchian/MA positions, with one experiment-local module for the four newly scoped indicators. No chart-type data or synthetic prices are in scope.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Dependency gate | PASS | Requires EXP-003 COMPLETE, EXP-004 PASS, and finite EXP-003 gate-stack MDE rows before measurement (lines 119-187). |
| `code/run_experiment.py` | Holdout exclusion | PASS | Uses `load_analysis_data` from the frozen harness for the first-70% analysis slice only; no direct full-data read exists in the experiment code. |
| `code/run_experiment.py` | Real-price discipline | PASS | Returns come from `next_log_returns_from_bars` on real OHLC domain frames; no HA/Renko/LB synthetic prices are referenced. |
| `code/run_experiment.py` | Look-ahead prevention | PASS | Positions are computed from domain bars sorted by `CloseTime`, aligned to `t -> t+1` returns, and evaluated through the frozen split/referee harness (lines 193-283). |
| `code/run_experiment.py` | Referee faithfulness | PASS | Calls `evaluate_referees` unchanged for both referees and all alphas; costs/materiality/bootstrap semantics stay frozen (lines 273-283). |
| `code/run_experiment.py` | MDE location | PASS | Classification is CI-aware: `below_MDE` requires the CI upper bound below the MDE, preventing overstatement (lines 216-248). |
| `code/strategies.py` | Indicator causality | PASS | RSI, Bollinger, MACD, and ROC use trailing or recursive calculations only; warmup/NaN rows are made flat and aligned via `_align` (lines 39-186). |
| `code/strategies.py` | Parameters | PASS | All strategy parameters are fixed constants matching scope; no optimization or tuning path exists (lines 17-26). |
| `code/run_experiment.py` | Memory/performance | PASS | Plotting uses the <=144 alpha0 effect rows; no reload or rerun for plots. |
| `code/run_experiment.py` | Progress/logging | PASS | Uses `tqdm` over instrument files; logging is concise. |
| `code/run_experiment.py` | Import side effects | PASS | Directories are created only inside `main()` via `ensure_output_dirs` (lines 105-108, 496-503). |

## Numerical Validation

### Spot Checks

Output dimensions match the approved design:

- `strategy_verdicts.csv`: 432 rows = 6 strategies x 4 instruments x 3 domains x 2 referees x 3 alphas.
- `strategy_effects.csv`: 144 rows = alpha0 subset for both referees.
- Gate-stack alpha0 cells: 72 = 6 strategies x 4 instruments x 3 domains.
- `analysis_metadata.csv`: 12 instrument/domain rows.

Gate-stack effect summary at alpha0:

| Domain | Median Net Effect | IQR | Min | Max | Cells Below MDE |
|--------|-------------------|-----|-----|-----|-----------------|
| 5m | -1.018395 bps | [-3.007847, -0.406185] | -9.987340 | -0.069953 | 24/24 |
| 1h | -0.998325 bps | [-2.878832, -0.383782] | -10.949345 | -0.080834 | 24/24 |
| 4h | -0.952547 bps | [-2.318087, -0.098853] | -13.029254 | +0.045022 | 24/24 |

Range checks:

| Metric | Expected Range | Actual Range | Pass? |
|--------|----------------|--------------|-------|
| Gate effective N | finite positive | 902 to 65,144 | YES |
| Gate block length | positive integer | 1 in all 72 cells | YES |
| Gate net effect | finite bps | -13.029254 to +0.045022 | YES |
| CI upper vs MDE | below MDE for `below_MDE` | 72/72 gate cells below MDE | YES |
| Domain rows | finite positive | 3,007 to 216,982 | YES |

The largest positive gate-stack point estimate is EURUSD/4h Donchian(20), +0.045022 bps with CI [-0.390681, +0.514643], far below the 12 bps 4h gate MDE.

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|------------|--------|----------|
| Frozen referee evaluation | EXP-003/004 harness semantics are reused unchanged | YES | `evaluate_referees` is called directly; no shared module changes. |
| Untuned breadth | Strategy parameters are fixed before results | YES | Constants in `strategies.py` and `run_experiment.py` match scope. |
| Causal indicator construction | Position at `t` uses data available at or before `t` | YES | Trailing windows, recursive EMAs, and `_align(...[:-1])` are explicit. |
| Distribution summary | Descriptive medians/IQR avoid normality assumptions | YES | No parametric distribution test is used. |

## Results Plausibility

The broadened set strengthens the EXP-004 lower/null anchor rather than surfacing a near-MDE real candidate. All 72 gate-stack net-effect cells are confidently below their domain MDE by the CI-aware classification. BTCUSD trend/momentum cells are strongly negative net of cost, which is plausible under the fixed-cost, always/mostly-active simple strategy setup and is not a positive-edge finding.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none found
- Complexity budget: 3 statistical checks / 3, 5 plots / 5, 1 local module / 1
- Holdout exclusion verified: YES
- Real-price outcome discipline verified: YES
- Strategy tuning/selection: none found

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Exploratory measurement only**
   - EXP-009 has no pass/fail strategy qualification claim. The audit supports the measurement, not adoption or rejection of any individual strategy family.

2. **Cost drag dominates many active strategies**
   - Several always-active or mostly-active BTCUSD trend/momentum strategies are sharply negative net of cost. This is a valid measured distribution feature, not a code defect.

## Re-Audit Requirements

None.
