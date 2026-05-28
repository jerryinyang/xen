VERDICT: APPROVE

## Post-Experiment Governance Review: EXP-031

### Core Constraints

| Constraint | Check | Status |
|-----------|-------|--------|
| Simplicity | Label-stratified bootstrap preserves the subset relationship between breaker and baseline in each replicate — the simplest correct approach for this comparison design. | PASS |
| No academic-finance pitfalls | Label-stratified bootstrap (n=10,000). No normality or stationarity assumptions. Non-parametric throughout. | PASS |
| Single hypothesis | One question: does the USTEC Candidate A breaker positive survive at 15-minute resolution? Primary metric: Return_R_60m breaker-minus-baseline difference vs EXP-023. | PASS |
| Complexity budget | 3 statistical tests (primary, secondary MAE, secondary Return) / 3; 4 plots / 4; 0 new modules (bar_aggregator reused) / 1 max. Budget respected. | PASS |
| No scope creep | No segmentation, no cost stress, no second-candle-open, no Candidate B, no other instruments. Exactly the predeclared scope. | PASS |

### OOS Holdout

| Check | Status |
|-------|--------|
| Final 30% never loaded | PASS — `load_analysis_timebars` applies analysis-set cutoff |
| 15m aggregation on analysis-set only | PASS |
| 1m outcome bars are analysis-set only | PASS |
| Chronological split | PASS |

### Look-Ahead Bias

| Check | Status |
|-------|--------|
| ATR14Prior uses only prior bars | PASS — `rolling_mean(14).shift(1)` |
| BodyMedian100Prior uses only prior bars | PASS — `rolling_median(100).shift(1)` |
| Candidate A OB search is backward-only before displacement | PASS — `range(before_idx - 1, search_start - 1, -1)` |
| Stop invalidation checked before breaker confirmation | PASS — `_close_invalidates_setup` terminates forward scan |
| Outcome clock starts strictly after displacement candle close | PASS — `searchsorted(entry_ns, side="right")` |

### Real-Price Discipline

| Check | Status |
|-------|--------|
| All outcomes on real 1-minute OHLC | PASS — `bars_1m` provides real prices; 15m view supplies detection only |
| Entry at displacement-close (real 15m bar close mapped to 1m) | PASS — `EntryTime = DisplacementTime` which is a 15m bar CloseTime, used to locate real 1-minute outcome window |
| No synthetic prices used | PASS |

### Results and Report Quality

| Check | Status |
|-------|--------|
| Honest reporting | PASS — INCONCLUSIVE verdict correctly applied; 44% vs 50% threshold gap explicitly discussed; EXP-023 reference imprecision noted |
| Uncertainty acknowledged | PASS — wide test CI reported; small test BreakerN (78) context given; bootstrap CI for EXP-023 reference noted as wide |
| No overreaching | PASS — "Phase 004B Branch A is supported to proceed" is appropriately scoped; not claiming a candidate has been found |
| Index updated | PASS |

### Audit Quality

Audit (PASS, 0 critical, 1 warning, 3 info) is thorough. The Warning correctly identifies that EXP-023's 1-minute train CI included zero, while EXP-031's 15-minute train result is sharper — important interpretive context that was incorporated in results.md. No critical issues.

### Phase Alignment

EXP-031 is aligned with Phase 004A design.md. It answers the USTEC breaker resolution-stability question as specified. The INCONCLUSIVE finding with both train and test CIs excluding zero positively and MAE reduction confirmed provides the reflection with clear evidence: the USTEC Candidate A breaker positive is not a 1-minute resolution artifact, and Phase 004B Branch A is supported to proceed.

The result satisfies the design.md mid-checkpoint criteria: "15-min FVG inversion stays high AND USTEC breaker survives → Proceed at 15-minute if event floors pass." Both conditions are met.
