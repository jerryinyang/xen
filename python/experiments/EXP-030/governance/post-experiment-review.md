VERDICT: APPROVE

## Post-Experiment Governance Review: EXP-030

### Core Constraints

| Constraint | Check | Status |
|-----------|-------|--------|
| Simplicity | Stratified bootstrap on Hit1R difference is the right tool for comparing two event groups with unbalanced level-type composition. No unnecessary complexity. | PASS |
| No academic-finance pitfalls | Stratified bootstrap (n=10,000) with no normality assumptions. Non-parametric throughout. | PASS |
| Single hypothesis | One question: does 15m sweep reversal behavior differ from EXP-015 1m baseline? Primary: Hit1R_60m sweep-minus-breach difference. | PASS |
| Complexity budget | 3 statistical tests (primary, secondary, horizon sweep) / 3; 4 plots / 4; 0 new modules (bar_aggregator reused) / 1 max. Budget respected. | PASS |
| No scope creep | No ICT chain, no filters, no parameter tuning against outcomes. Exactly the predeclared scope. | PASS |

### OOS Holdout

| Check | Status |
|-------|--------|
| Final 30% never loaded | PASS — `load_analysis_timebars` applies analysis-set cutoff before any aggregation |
| 15m aggregation on analysis-set only | PASS — 1-minute analysis-set frame passed to `aggregate_ohlc` |
| 1m outcome bars are analysis-set only | PASS — `bars_1m` derives from `loaded.frame` (analysis set) |
| Chronological split | PASS |

### Look-Ahead Bias

| Check | Status |
|-------|--------|
| ATR14Prior uses only prior bars | PASS — `rolling_mean(14).shift(1)` |
| Outcome clock starts strictly after confirming 15m candle | PASS — `searchsorted(event_ns, side="right")` skips bars ≤ CloseTime |
| ONH/ONL timing gate | PASS — `NYMinuteOfDay >= ON_LEVEL_MIN_MINUTE` prevents early-session ONL/ONH events |

### Real-Price Discipline

| Check | Status |
|-------|--------|
| All outcomes (Hit1R, MAE_R, MFE_R, Return_R) on real 1-minute OHLC | PASS — 15m view provides detection only; all outcome computation uses `bars_1m` (real 1-minute prices) |
| No synthetic prices used | PASS |

### Results and Report Quality

| Check | Status |
|-------|--------|
| Honest reporting | PASS — EURUSD reversal explicitly surfaced; BTCUSD negative pattern clearly stated; INCONCLUSIVE verdict correctly applied |
| Uncertainty acknowledged | PASS — all CIs reported; underpowered instruments identified; resolution-timing interpretation is framed as a hypothesis, not a fact |
| No overreaching | PASS — INCONCLUSIVE not inflated to AGAINST; the EURUSD reversal is stated as a finding for the reflection, not a proof of absence |
| Index updated | PASS |

### Audit Quality

Audit (PASS, 0 critical, 1 warning, 2 info) is complete. Warning correctly identifies the EURUSD reversal as a finding that must be surfaced in interpretation — which was done. No critical issues.

### Phase Alignment

EXP-030 is aligned with Phase 004A design.md. It answers the sweep-reversal replication question as specified. The INCONCLUSIVE result with no new positive instruments and a reversed EURUSD effect provides the reflection with clear evidence: the EXP-015 EURUSD positive is a resolution-specific artefact and no sweep-focused Phase 004B branch is warranted.
