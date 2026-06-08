# Results: Experiment EXP-024 — AVWAP Event-Edge Dissipation Decomposition

## Summary

EXP-024 resolves the primary 5m diagnostic toward **fork (b): entry/position
dilution**. On the completed common event set, the best 5m bounded-hold horizon
is `h=16` with `g*=+0.370` bps, below the ratified-loose 5m floor of `0.5` bps;
every adequately powered 5m horizon remains below that floor. The slower
domains do not support fork (a): 1h and 4h have above-floor point estimates at
their best horizons, but their bootstrap CIs are too wide and straddle the
floors. The phase-level diagnostic verdict is therefore
**MIXED_OR_INCONCLUSIVE**, not a clean `/EXIT` trigger. The audit passes after
the matched EXP-021 cross-check correction.

## Detailed Findings

### 1. The rerun is auditable and the EXP-021 return guardrail now passes

- **Observation**: the corrected EXP-021 cross-check recomputes `{1,3,6}` event
  returns on exact reportable EXP-021 event keys and matches to zero difference.
- **Evidence**: `exp021_crosscheck.csv` max mean absolute difference `0.0` bps
  and max row absolute difference `0.0` bps. Matched event counts reproduce
  EXP-021 denominators: 5m `16,249`, 1h `1,207`, 4h `246/246/244`.
  `event_join_diagnostics.csv` reports row-count preservation and 0 duplicate
  join keys for the EXP-020 event to EXP-022 lifetime join.
- **Interpretation**: the prior audit blocker is resolved. EXP-024's domain
  reconstruction and return formula are consistent with EXP-021 on identical
  rows. Remaining differences between EXP-021 event means and EXP-024 all-event
  `g_all` are sample-definition differences, not calculation errors.

### 2. Primary 5m domain resolves fork (b): bounded hold does not reach the floor

- **Observation**: the best 5m bounded-hold gross return is below the loosest
  suite floor.
- **Evidence**: `fork_verdict.csv`: 5m `h*=16`, `g*=+0.370` bps, floor `0.5`,
  CI `[-0.396, +1.164]`, `p_holm=1.0`, `n=15,037`; `g_life(h*)=+0.058` and
  `delta=+0.312`, below the required `0.5` bps bounded-vs-lifetime margin.
  `horizon_decay.csv` shows all adequately powered 5m horizons have
  `g_common < 0.5` bps.
- **Interpretation**: under the predeclared rule, 5m is **FORK_B_DILUTION**.
  A bounded max-hold exit does not recover enough gross event edge to justify a
  scoped `/EXIT` remedy on the primary domain.

### 3. 1h and 4h are unresolved, not evidence for a fixable exit

- **Observation**: slower-domain point estimates can exceed their loose floors,
  but uncertainty is too wide to establish floor clearance.
- **Evidence**:
  - 1h: `h*=24`, `g*=+4.248` bps, floor `2.0`, CI `[-10.190, +18.417]`,
    `n=1,033`, `delta=+6.197`.
  - 4h: `h*=8`, `g*=+8.137` bps, floor `8.0`, CI `[-22.769, +39.747]`,
    `n=233`, `delta=+16.840`.
- **Interpretation**: neither slower domain satisfies fork (a), because
  floor-clearance precision fails. They also cannot be labeled fork (b), because
  their point estimates reach or exceed the floor. The correct labels are
  `INCONCLUSIVE_UNRESOLVED`.

### 4. Trend-change exits do not look like the main recoverable edge leak

- **Observation**: trend-change lifetime returns are negative on average in all
  domains.
- **Evidence**: `trend_change_returns.csv`: 5m mean `-2.79` bps
  (`[-3.32, -2.32]`), 1h `-8.76` (`[-15.03, -3.24]`), 4h `-17.59`
  (`[-40.38, +3.68]`). Fractions negative are 65.8%, 56.9%, and 54.0%.
- **Interpretation**: this does not support the clean fork (a) story that the
  always-on lifetime hold mainly gives back positive bounded-hold winners at
  trend changes. The trend-change subset is mostly adverse on realized signed
  return, which is more consistent with entry/exposure dilution than a simple
  "hold too long" repair.

### 5. Sparse exposure and pyramid events explain why component evidence dilutes

- **Observation**: AVWAP bounce events are sparse relative to domain bars, and
  many events are pyramid bounces rather than independent fresh entries.
- **Evidence**: `holding_exposure.csv`: event prevalence is 2.68% of 5m bars,
  2.26% of 1h bars, and 2.21% of 4h bars. Reconstructed active-bar fractions are
  6.17%, 5.73%, and 5.67%. Pyramid bounces account for 9,679/19,242 5m events,
  636/1,360 1h events, and 146/309 4h events.
- **Interpretation**: EXP-021/022 showed real conditional component behavior,
  but the always-on/bounded-hold vehicle expresses only a sparse and diluted
  subset of that behavior. That makes the EXP-023 baseline failure coherent with
  the positive component experiments.

### 6. Cost is not the primary explanation, but it worsens every domain

- **Observation**: the fork is gross-primary, and gross already fails to clear
  on the primary domain; cost pushes net values lower.
- **Evidence**: `cost_attribution.csv`: 5m `g*` gross `+0.370` becomes
  `-4.651` net after mean round-trip cost; 1h `+4.248` becomes `-0.597`; 4h
  `+8.137` becomes `+2.793`. Lifetime gross is near/negative and net is negative
  in all domains.
- **Interpretation**: cost is not the reason 5m fails the fork (it fails before
  cost), but it confirms that an eventual tradable candidate would need a much
  stronger gross edge than this diagnostic finds.

## Diagnostic Verdict

**MIXED_OR_INCONCLUSIVE.**

Per-domain verdicts:

| Domain | Verdict | Best horizon | `g*` bps | Floor bps | 95% CI | N |
| --- | --- | ---: | ---: | ---: | --- | ---: |
| 5m | `FORK_B_DILUTION` | 16 | +0.370 | 0.5 | [-0.396, +1.164] | 15,037 |
| 1h | `INCONCLUSIVE_UNRESOLVED` | 24 | +4.248 | 2.0 | [-10.190, +18.417] | 1,033 |
| 4h | `INCONCLUSIVE_UNRESOLVED` | 8 | +8.137 | 8.0 | [-22.769, +39.747] | 233 |

No domain supports fork (a). The primary 5m domain supports fork (b), while 1h
and 4h are unresolved. Under the Phase 005 design, this does **not**
automatically justify EXP-026 `/EXIT`; mixed/inconclusive output requires
operator/governance handling before any Stage B scope.

## Limitations

- This is a diagnostic, not a qualification screen. It runs no frozen suite and
  consumes no candidate-screening multiplicity slot.
- The 1h and 4h domains are under-resolved for floor-clearance decisions despite
  meeting the minimum completed-event count.
- The EXP-021 component reaction and EXP-024 bounded-hold decomposition are
  different estimands: matched event-control reaction versus all/completed-event
  gross returns.
- All results are on the first-70% analysis slice. The global holdout remains
  sealed.

## Alternative Explanations

- The slower-domain above-floor point estimates may reflect real but noisy
  recoverable edge. EXP-024 cannot claim that because the confidence intervals
  are too wide.
- A structurally different exit mechanism could still matter, but EXP-024 does
  not provide a clean empirical basis for one under the predeclared fork rule.
- The component edge may be more about identifying event-vs-control reaction than
  about a standalone event-entry vehicle. EXP-025's direct AVWAP-line S/R test
  is the scoped way to examine that mechanism.

## Recommended Next Steps

1. Do **not** open EXP-026 `/EXIT` as an automatically justified candidate screen
   from EXP-024 alone. If the operator wants to scope `/EXIT` anyway, it should
   be explicitly labeled mixed/inconclusive-derived and governed before any
   candidate-screening run.
2. Proceed with the remaining Phase 005 Stage A diagnostic, EXP-025, to test the
   direct AVWAP-line support/resistance mechanism.
3. Use EXP-024's result to inform Stage C priority: the always-on/bounded-hold
   overlay looks weak on the primary domain, so detector/anchor operationalization
   may be higher-value than exit timing alone.
