VERDICT: APPROVE

## Post-Experiment Governance Review: EXP-032

### Core Constraints

| Constraint | Check | Status |
| --- | --- | --- |
| Simplicity | The analysis uses the approved count waterfall, label-stratified bootstrap, and deterministic reference gates. No model or extra filter was added. | PASS |
| No academic-finance pitfalls | No normality, stationarity, or constant-volatility assumption is used. Bootstrap intervals are descriptive and non-parametric. | PASS |
| Single hypothesis | One question is answered: whether the 1-hour USTEC Candidate A breaker chain passes the predeclared magnitude gate before Branch A segmentation. | PASS |
| Complexity budget | 2 statistical test families / 3; 4 plots / 4; 0 new modules / 0. | PASS |
| No scope creep | No segmentation, controls, cost stress, stop perturbation, IFVG logic, Candidate B, or non-USTEC instrument was introduced. | PASS |

### OOS Holdout

| Check | Status |
| --- | --- |
| Final 30 percent global holdout excluded before aggregation | PASS |
| 1-hour aggregation uses analysis-set 1-minute bars only | PASS |
| Real 1-minute outcome bars are analysis-set only | PASS |
| Chronological train/test split inside analysis set | PASS |

### Look-Ahead Bias

| Check | Status |
| --- | --- |
| ATR14Prior uses only completed prior bars | PASS |
| BodyMedianPrior uses only completed prior bars | PASS |
| Displacement and breaker searches use event timestamps and scoped forward windows | PASS |
| Outcome clock starts strictly after the confirming 1-hour displacement close | PASS |

### Real-Price Discipline

| Check | Status |
| --- | --- |
| Synthetic 1-hour bars are detection-only | PASS |
| Return_R, MAE_R, MFE_R, hit rates, and log returns use real 1-minute OHLC | PASS |
| No chart-type synthetic prices are in scope or used | PASS |

### Results and Reporting

| Check | Status |
| --- | --- |
| Audit quality | PASS - audit verdict PASS with 0 critical and 0 warning issues. |
| Interpretation | PASS - results.md applies the predeclared REFUTED / AGAINST continuation verdict because the test diff is +0.116R versus the +0.918R hard gate. |
| Report quality | PASS - report.md states the negative branch decision clearly while preserving the secondary MAE observation. |
| Index updates | PASS - both experiment indexes include EXP-032 and the active checkpoint summary reflects the Branch A stop/reframe state. |

### Phase Alignment

EXP-032 is aligned with the Phase 004B reflection directive. It ran the one authorized 1-hour pre-segmentation extension and applied the binding hard gate before any EXP-033 segmentation scope. The result fails that gate, so the documented next state is correct: no automatic Branch A continuation; explicit checkpoint reframe or closure is required before further Branch A work.
