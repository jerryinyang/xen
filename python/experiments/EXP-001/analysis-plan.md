# Analysis Plan: Experiment EXP-001

## Objective

Determine whether the synthetic substrate required by the Phase 001 calibration harness is valid on real analysis-set prices across 5m, 1h, and 4h domains.

## Methodology

### Step 1: P0 Aggregation Extension

- **Method**: VAL-001-style aggregation integrity checks for 5-minute and 240-minute parameterizations, plus coverage-grid retention reporting.
- **Why this method**: The checkpoint explicitly blocks EXP-001 on 5m/4h execution until `{5, 240}` minute aggregation is checked.
- **Simpler alternative considered**: Trusting the existing 15m/60m VAL-001 result is not sufficient because 5m and 240m have different coverage behavior.
- **Assumptions**: The first 70% chronological 1-minute analysis slice is the only allowed source. Strict-mode OHLC can be compared to an independent pandas oracle; tolerant coverage is checked for temporal integrity and source-bar denominator compliance.
- **Expected output**: `p0_aggregation_checks.csv` and `coverage_grid.csv`.

### Step 2: Known-Null Validation

- **Method**: Generate bar-permuted returns and random-signal controls, then measure the oracle signal's gross bps/trade effect over repeated fixed-seed draws.
- **Why this method**: Both nulls are predeclared in `design.md` and fail differently, giving direct detection of substrate leakage.
- **Simpler alternative considered**: A single random-signal null would not test whether return permutation creates an accidental oracle-recoverable state.
- **Assumptions**: Draw-level effects need no normality assumption; percentile intervals over draws are sufficient. Time order is not used after permutation except for the candidate evaluation timestamp.
- **Expected output**: `substrate_draws.csv` and null rows in `substrate_summary.csv`.

### Step 3: Known-Positive Validation

- **Method**: Inject `r'_{t+1} = r_{t+1} + s_t * delta`, where `delta = m + cost_bps`, and verify that oracle positions `p_t = s_t` recover net edge `m` bps/trade.
- **Why this method**: The mapping is closed-form, real-price-valid, and directly matches the checkpoint design.
- **Simpler alternative considered**: Modifying price levels directly is less transparent because the exact expected net effect is harder to audit.
- **Assumptions**: The pseudo-random state is observable to the oracle at time `t` and independent of future returns. The reconstructed return path remains a diagnostic substrate, not a tradable claim.
- **Expected output**: Positive rows in `substrate_draws.csv` and `substrate_summary.csv`.

## Visualisations

1. Null oracle-effect CI by domain and generator.
2. Positive recovered-vs-planted edge by domain.
3. Coverage retention by domain and coverage rule.
4. P0 status count by period.

## Interpretation Guide

- If P0 passes, known-null effects are indistinguishable from zero, and known-positive effects recover `m`, the substrate is valid and EXP-002/003 may use it.
- If any P0 check fails, the phase halts until aggregation integrity is fixed or a VAL rerun passes.
- If nulls show recoverable edge or positives fail recovery, the substrate is invalid and downstream referee measurements are not trustworthy.
- If sample size is insufficient for any instrument/domain cell, that cell is inconclusive and downstream measurement for that cell must be blocked.

## Complexity Check

- Statistical tests: 2 / 2
- Visualisations: 4 / 4
- New modules: 1 / 1

## Data-View Comparison Considerations

- Domains are aligned by `CloseTime`, not by row number.
- The final 30% holdout is excluded before any aggregation or synthetic generation.
- Tolerant aggregation reports `SourceBars` denominators; no silent coverage loss is accepted.
- Zero-baseline behavior is explicit: a planted `m=0` positive must behave like a null, and percentage improvement over zero is never used.
