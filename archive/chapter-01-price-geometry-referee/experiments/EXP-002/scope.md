# Experiment: EXP-002 - Referee Golden-Fixture Correctness

## Hypothesis

The minimal baseline referee and 5-check gate-stack referee reproduce predeclared hand-computed verdicts on deterministic golden fixtures, while the gate stack records every leg independently.

## Question

Are the referee implementations correct enough to measure in EXP-003?

## Scope Boundaries

- **Data Views**: Deterministic in-memory golden fixtures only. No real market data is read except the EXP-001 pass/fail dependency metadata.
- **Parameters**: Referee operating point `alpha=0.05`; stationary block-bootstrap resamples `n=1000`; EURUSD/5m cost and materiality defaults from the frozen Phase 001 helper module.
- **Fixtures**: clear positive oracle, null/negative edge, one-sided readiness failure, sub-material positive edge, and naive-control-equivalent candidate.
- **Instruments**: Fixture instrument label is EURUSD only because this experiment tests referee logic, not market behavior.
- **Time range**: Not applicable to fixture arrays. The EXP-001 dependency, if read, uses only its already-produced metadata and not raw data.
- **Global holdout**: No raw data is loaded by this experiment; the final 30% global holdout remains untouched.
- **Look-ahead bias prevention**: Fixture positions are generated at time `t` and evaluated only against aligned `t -> t+1` returns.
- **Real-price outcome discipline**: Fixtures are return-space diagnostics for implementation correctness; no synthetic chart prices or strategy backtests are in scope.
- **Exclusions**: FPR/TPR/MDE measurement, real candidate strategies, parameter tuning, chart-type signals, and any revision of referee rules after seeing EXP-003 results.

## Success / Failure Criteria

- **Evidence FOR**: Every fixture produces the expected minimal-baseline verdict, expected gate-stack verdict, and required gate-leg state; the gate stack emits all L1-L5 leg results for every fixture.
- **Evidence AGAINST**: Any fixture verdict or required leg state differs from expectation, or any gate-stack run omits a leg result.
- **Inconclusive**: EXP-001 has not passed, or a fixture cannot be evaluated due to insufficient length or non-finite output.

## Complexity Budget

- Max statistical tests: 1
- Max visualisations: 2
- Max new code modules: 0

## Data Requirements

EXP-002 requires `python/experiments/EXP-001/results/run_metadata.json` with `overall_status == "PASS"` before manual execution. It does not load raw Parquet data.

### Standard Loading Pattern

Not applicable; this experiment deliberately avoids raw data loading.

## Suggested Direction

Use deterministic fixtures with large margins so failures indicate implementation defects rather than sampling noise.

