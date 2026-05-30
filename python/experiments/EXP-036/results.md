# Results: Experiment EXP-036

## Summary

Prior-Range Location is **REFUTED** as a Phase 005 executable state-descriptor edge. All scoped cells remained adjudicable after return filtering, but the next-bar primary did not replicate both required contrasts on any instrument-timeframe cell. The matched-control gate showed one positive next-bar cell (`XAUUSD 1h`), and the 4-bar secondary showed one cell passing both contrasts (`XAUUSD 1h`), but neither reached the predeclared `>=2` distinct-instrument threshold. The global holdout remains untouched.

## Detailed Findings

### 1. Counts Did Not Drive The Result

- **Observation**: All 32 metric rows are adjudicable for both neutral and control contrasts.
- **Evidence**: Minimum post-filter train state counts are `326` rows and `89` episodes; minimum test state counts are `118` rows and `35` episodes. These exceed the scoped floors of `100/30` in train and `50/15` in test.
- **Interpretation**: The negative verdict is not a power-floor failure. The descriptor had enough top, bottom, and middle observations to evaluate the predeclared gates.

### 2. The Next-Bar Primary Fails The Required Edge Gate

- **Observation**: No next-bar test-segment `Delta_neutral` CI excludes zero positively.
- **Evidence**: `verdict.json` reports no instruments in `next_bar_neutral_and_control` for either `1h` or `4h`. The only next-bar matched-control positive cell is `XAUUSD 1h`: `Delta_control = +0.000153`, CI `[+0.000052, +0.000252]`.
- **Interpretation**: A single control-positive cell is not enough, and it does not also pass the neutral-middle-bucket contrast. The descriptor fails the next-bar primary edge criterion.

### 3. The 4-Bar Secondary Does Not Reopen The Thesis

- **Observation**: The 4-bar secondary passes both `Delta_neutral` and `Delta_control` only for `XAUUSD 1h`.
- **Evidence**: `XAUUSD 1h Test four_bar` has `Delta_neutral = +0.000482`, CI `[+0.000088, +0.000855]`, and `Delta_control = +0.000317`, CI `[+0.000040, +0.000571]`.
- **Interpretation**: This is a real positive cell, but the predeclared secondary horizon needs `>=2` distinct instruments to produce horizon-dependent state differentiation. One instrument is insufficient, so no EXP-038 robustness path opens.

### 4. Several Train Positives Do Not Survive Test

- **Observation**: Some train cells are positive with CIs excluding zero, especially BTCUSD, but these do not replicate in test.
- **Evidence**: `BTCUSD 4h Train next_bar Delta_control = +0.000864`, CI `[+0.000152, +0.001590]`; the corresponding test control CI includes zero.
- **Interpretation**: The train/test sign-preservation rule correctly blocks train-only artifacts from being read as evidence.

### 5. Gap-Spanning Entries Are A Caveat, Not A Verdict Driver

- **Observation**: Median entry gaps are nominal (`60` minutes at `1h`, `240` minutes at `4h`), but max gaps are large and `4h` gap-spanning shares are `20.6%` to `25.2%`.
- **Evidence**: `gap_diagnostics.csv` reports `4h` gap shares of `0.252` for EURUSD, `0.211` for XAUUSD, `0.225` for BTCUSD, and `0.206` for USTEC.
- **Interpretation**: Gap handling remains an executability caveat. Because the descriptor does not survive the edge gate, there is no reason to open the planned EXP-038 gap-exclusion robustness path from EXP-036.

## Hypothesis Verdict

**REFUTED**

EXP-036 fails the predeclared matched-control replication gate. The next-bar primary has zero instruments passing both `Delta_neutral` and `Delta_control`. The 4-bar secondary has one passing instrument, below the `>=2` distinct-instrument threshold. This cleanly refutes Prior-Range Location as the highest-priority Phase 005 state-descriptor edge candidate, with the holdout intact.

## Limitations

- The 4-bar positive result in `XAUUSD 1h` is not enough for the predeclared gate but should be remembered as a localized observation, not erased.
- Strict aggregation creates material `4h` gap-spanning entries; this would need stress testing only if a descriptor had survived.
- No transaction-cost, spread, slippage, or execution-delay stress was in scope. Those belonged to EXP-038, which is not authorized by these results.

## Alternative Explanations

- Prior-Range Location may describe some localized return structure, especially for `XAUUSD 1h`, but it does not add robust information beyond the neutral state and momentum control across instruments.
- Continuation from prior-range extremes may be too coarse; however, changing bucket boundaries, lookback, horizon, or framing would be a new experiment, not a reinterpretation of EXP-036.

## Recommended Next Steps

1. Do not open EXP-038 from EXP-036. The predeclared survival gate was not met.
2. Treat Phase 005 as having no surviving directional state descriptor under its locked candidate path: Prior-Range Location is refuted here, and Market Bias was a readiness-gated no-go under the canonical strict rule.
3. Any further state-descriptor work should start from a new checkpoint or a new predeclared descriptor, not from tuning EXP-036's lookback, buckets, or horizon.
