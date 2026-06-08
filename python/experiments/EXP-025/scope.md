# Experiment: EXP-025 — AVWAP Line Support/Resistance Direct Test

## Hypothesis

AVWAP bounce trigger bars from the supported CF-AVWAP-001 first branch show a
larger **event-bar AVWAP line-rejection score** than matched same-regime
non-event control bars on at least one EXP-020 ready domain, without touching the
global holdout.

This is a **diagnostic component test**, not a candidate screen and not a
strategy/P&L claim.

## Question

Does price measurably react at the AVWAP line itself as support/resistance, or
were the EXP-021/022 positives mostly regime-gated continuation and completion
effects rather than direct line reaction?

## Scope Boundaries

- **Data Views**: EXP-020 `avwap_events.csv` and `avwap_state_summary.csv`, plus
  5m/1h/4h domain OHLC bars rebuilt from first-70% 1-minute analysis slices using
  the EXP-020 convention. No chart-type views.
- **Candidate family**: `CF-AVWAP-001/DIAG-002`, first branch only, as registered
  in `docs/signal-registry/multiplicity-registry.md`.
- **Dependency gate**:
  - EXP-020 must be `SUPPORTED_FULL`, with ready domains `{5m, 1h, 4h}`, zero
    invariant failures, and deterministic replay pass.
  - EXP-024 must be complete and documented; its result is context only and does
    not change EXP-025 metric definitions.
- **Primary metric**: event-bar AVWAP line-rejection score in basis points,
  computed at the trigger/control bar only:
  - For bullish direction `d=+1`:
    - `close_rebound_bps = 10000 * log(Close / AVWAP)`
    - `adverse_penetration_bps = max(0, 10000 * log(AVWAP / Low))`
    - `line_rejection_score_bps = close_rebound_bps - adverse_penetration_bps`
  - For bearish direction `d=-1`:
    - `close_rebound_bps = 10000 * log(AVWAP / Close)`
    - `adverse_penetration_bps = max(0, 10000 * log(High / AVWAP))`
    - `line_rejection_score_bps = close_rebound_bps - adverse_penetration_bps`
  - Positive values mean the bar closes away from the AVWAP line in the regime
    direction by more than it penetrates through the line intrabar.
- **Event denominator**:
  - All EXP-020 bounce trigger events with valid trigger index/time/close,
    finite contemporaneous AVWAP, valid real OHLC, and at least 3 matched
    controls under the fixed control rule below.
  - First and pyramid bounces are both included, matching EXP-020/021 event
    population discipline. `is_pyramid_bounce` is reported descriptively only.
- **Matched-control dimensions**:
  - Same instrument.
  - Same domain.
  - Same `regime_id` and regime direction.
  - Non-event bars only: exclude every EXP-020 trigger bar.
  - Exclude bars within 6 completed domain bars of any EXP-020 trigger in the
    same instrument/domain cell, matching EXP-021's contamination guard.
  - Controls must have finite contemporaneous AVWAP and band spread.
  - Controls must be line-proximate: `abs(close_to_avwap_bps) <=
    max(1.0, band_spread_bps)`, where `band_spread_bps` is the contemporaneous
    MAD band spread expressed relative to AVWAP. This uses the frozen EXP-020
    band context and is not swept.
  - Select up to 5 controls per event, ranked deterministically by:
    1. nearest absolute close-to-AVWAP distance in bps;
    2. nearest anchor age in bars;
    3. nearest timestamp/index within the same regime;
    4. smaller index as final stable tiebreak.
  - If fewer than 3 controls are available, the event is non-reportable for the
    matched primary test and counted in diagnostics.
- **Horizon**: event bar only (`h=0`). No future return horizon is part of the
  primary metric. EXP-021 already tested fixed-horizon continuation.
- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD. Use all four because EXP-020
  found every instrument/domain cell reportable.
- **Time range**: Full dataset with nested chronological split. First 70% =
  analysis set; final 30% = global holdout and is never loaded.
- **Global holdout**: The final 30% of each chronologically ordered source file
  must not be loaded, inspected, emitted, plotted, counted, or used in any
  capacity.
- **Look-ahead bias prevention**:
  - event definitions and regime intervals come from the EXP-020
    look-ahead-safe substrate;
  - domain bars are ordered by `CloseTime`;
  - per-bar AVWAP and band values are reconstructed causally from each regime's
    anchor using only bars available up to the evaluated bar;
  - controls are selected using only same-regime identity, AVWAP proximity,
    anchor age, timestamp, and non-event status, never future returns.
- **Real-price outcome discipline**: The metric uses real domain `Open/High/Low/Close`
  and contemporaneous AVWAP line values only. It is not strategy P&L and applies
  no transaction costs, fills, stops, targets, position sizing, or future returns.
- **Exclusions**:
  - frozen-suite candidate qualification;
  - cTrader strategy-host generation;
  - EXP-021 fixed-horizon return continuation;
  - EXP-022 lifetime target/trend-change outcomes;
  - EXP-024 bounded-hold exit decomposition;
  - alternative AVWAP branches, trend detectors, volume exponents, band
    multipliers, or bounce definitions;
  - any threshold sweep, line-proximity sweep, horizon sweep, parameter tuning,
    or post-result reselection;
  - percentage improvement against a zero or near-zero baseline;
  - final 30% global holdout.

## Success / Failure Criteria

Definitions:

- **Reportable matched event**: an EXP-020 bounce event with valid event-bar
  line-rejection score and at least 3 matched same-regime line-proximate controls.
- **Reportable instrument/domain cell**: at least 30 reportable matched events,
  with at least 8 bullish and 8 bearish reportable events.
- **Reportable domain**: at least 3 of 4 instruments are reportable.
- **Primary paired difference**: event `line_rejection_score_bps` minus the mean
  matched-control `line_rejection_score_bps`.
- **Domain estimator**: the unweighted mean, across reportable instruments in a
  domain, of each instrument's event-weighted mean primary paired difference.
  Instruments are equal-weighted so high-count/high-volatility cells do not
  dominate.
- **Zero-baseline behavior**: the null line-rejection advantage is exactly 0 bps.
  Report absolute bps differences and confidence intervals. Do not compute
  percentage improvement over the control mean or any zero baseline.

- **Evidence FOR**: all of the following:
  - dependency gate passes;
  - at least one reportable domain has primary domain estimator > 0 bps;
  - that domain's 95% regime-cluster bootstrap CI lower bound is > 0 bps;
  - its primary permutation p-value is `<= 0.05` after Holm adjustment across
    the three domains.
- **Evidence AGAINST**: any of the following:
  - dependency gate fails;
  - no domain is reportable;
  - every reportable domain has primary-effect CI upper bound `<= 0` bps.
- **Inconclusive**:
  - no domain meets Evidence FOR, but at least one reportable domain has a CI
    spanning 0 bps;
  - matched-control denominators are insufficient after fixed exclusions;
  - matching balance is materially broken: median absolute event-vs-control
    close-to-AVWAP distance differs by more than 2 bps in every reportable
    domain, making the line-proximity comparison untrustworthy.

## Complexity Budget

- Max statistical tests: 2
  1. Primary domain-level paired line-rejection advantage with regime-cluster
     bootstrap CI and Holm-adjusted permutation p-values.
  2. Matching-balance check on absolute close-to-AVWAP distance (thresholded
     diagnostic only; not an alternate market-edge claim).
- Max visualisations: 4
- Max new code modules: 0 shared modules. Use `python/experiments/EXP-025/code/run_experiment.py`
  for implementation; experiment-local helpers are acceptable inside that file.

## Data Requirements

Required upstream artifacts:

- `python/experiments/EXP-020/results/run_metadata.json`
- `python/experiments/EXP-020/results/analysis_metadata.csv`
- `python/experiments/EXP-020/results/avwap_events.csv`
- `python/experiments/EXP-020/results/avwap_state_summary.csv`
- `python/experiments/EXP-020/results/domain_readiness.csv`
- `python/experiments/EXP-020/results/invariant_checks.csv`
- `python/experiments/EXP-020/results/determinism_check.csv`
- `python/experiments/EXP-024/results.md` and `python/experiments/EXP-024/governance/post-experiment-review.md`

Implementation must rebuild domain OHLC bars from the exact source files named
in EXP-020 `analysis_metadata.csv`, after applying the first-70% chronological
slice. It must hard-fail if reconstructed domain row counts or min/max
`CloseTime` values disagree with EXP-020 metadata.

Implementation must reconstruct contemporaneous AVWAP and MAD-band spread for
all event and candidate-control bars inside each regime. Reconstructing per-bar
state is allowed only as a deterministic replay of the frozen EXP-020 AVWAP
definition; no candidate parameters may be changed.

Primary expected outputs:

- `line_rejection_observations.csv` - event/control matched records with score
  components, controls, paired differences, and reportability reasons.
- `line_rejection_summary.csv` - score components by instrument, domain,
  direction, and event/control role.
- `domain_line_rejection_tests.csv` - domain-level primary effects, CIs,
  p-values, Holm-adjusted decisions, and reportability.
- `control_match_diagnostics.csv` - event counts, control counts, proximity
  balance, and non-reportable reasons.
- `run_metadata.json`.

### Standard Loading Pattern

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob("timebars/timebars_*.parquet"))[-1]

scan = pl.scan_parquet(path).sort("CloseTime")
total_rows = int(scan.select(pl.len()).collect().item())
analysis_cutoff = int(total_rows * 0.7)
bars = scan.slice(0, analysis_cutoff).collect()
```

## Suggested Direction

Treat EXP-025 as a direct event-bar line-reaction study. Reuse EXP-021's
same-regime matched-control structure, but replace future-return outcomes with
the trigger/control-bar line-rejection score. Keep all score components visible
so the result can distinguish "closes away from the line" from "penetrates less
through the line" without creating multiple primary claims.
