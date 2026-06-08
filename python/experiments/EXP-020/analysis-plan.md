# Analysis Plan: Experiment EXP-020

## Objective

Determine whether the registered Phase 004 AVWAP first branch can produce a
deterministic, look-ahead-safe event substrate with enough bounce-event coverage
to justify a follow-up reaction study. EXP-020 is a readiness experiment; it
does not test profitability or run the frozen qualification suite.

## Methodology

### Step 1: Analysis-Set Domain Construction

- **Method**: Lazy-load each 1-minute source file, sort by `CloseTime`, slice the
  first 70% analysis set, then build 5m, 1h, and 4h domain bars with the existing
  project aggregation convention.
- **Why this method**: It directly enforces the global holdout rule and matches
  the domain convention used by EXP-004/009 and VAL-002.
- **Simpler alternative considered**: Reading full Parquet files and slicing in
  memory. Rejected because full collection risks accidental holdout inspection.
- **Assumptions**: Source `CloseTime` order is the temporal authority; domain
  bars are valid only after completed source bars. This matches the dataset
  reference and the cTrader strategy-host contract.
- **Expected output**: `analysis_metadata.csv` with source rows, analysis rows,
  analysis end timestamp, domain rows, coverage settings, and minimum/maximum
  `CloseTime` per instrument/domain.

### Step 2: Sequential AVWAP State Generation

- **Method**: Generate MA regimes, viable pivots, anchored AVWAP, MAD bands,
  arming states, and bounce events with an explicit sequential state machine per
  instrument/domain.
- **Why this method**: The scoped question is whether the AVWAP substrate is
  streaming-safe. An explicit sequential implementation is the clearest way to
  audit causality, anchor selection, and re-arm behavior.
- **Simpler alternative considered**: Vectorized window joins over full domain
  frames. Rejected for the first implementation because it can hide look-ahead
  mistakes in anchor and temporary-cache handling.
- **Assumptions**: Each state update uses only the current and prior completed
  domain bars. This assumption is required and will be checked by invariants.
- **Expected output**:
  - `avwap_events.csv` with one row per bounce event and the scoped event
    metadata needed by later reaction studies: regime id, bounce ordinal,
    direction, anchor time/price, arming time, trigger time/close, AVWAP/band
    values at trigger, frozen favorable/adverse lifetime targets, pyramid-bounce
    tag, and anchor age;
  - `avwap_state_summary.csv` with per-regime and per-anchor diagnostics;
  - `invariant_checks.csv` with pass/fail checks and failure counts.

### Step 3: Invariant and Determinism Checks

- **Method**: Apply deterministic validation checks to generated event/state
  tables, then replay the generator once and compare event-table and summary
  hashes.
- **Why this method**: This experiment is primarily a correctness and readiness
  gate. Deterministic pass/fail checks are more appropriate than statistical
  tests for temporal invariants.
- **Simpler alternative considered**: Spot-checking a few rows manually. Rejected
  because a sparse spot check can miss invalid arming or anchor transitions.
- **Assumptions**: Hash equality is a valid determinism check only if output row
  ordering and floating-point formatting are canonicalized before hashing.
- **Expected output**:
  - `determinism_check.csv`;
  - `invariant_checks.csv`;
  - `run_metadata.json` with `overall_status`, ready-domain count, and invariant
    failure count.

### Step 4: Event-Coverage Readiness Classification

- **Method**: Summarize bounce counts, direction counts, event density per 10,000
  domain bars, regime counts, median regime length, median anchor age at event,
  and reportable-cell status by instrument/domain.
- **Why this method**: Coverage is the blocker for any reaction study. Count and
  density tables expose whether the event definition is usable without claiming
  edge.
- **Simpler alternative considered**: A single pooled event count. Rejected
  because pooling can hide one-domain or one-direction degeneracy.
- **Assumptions**: Event counts are descriptive and do not imply signal quality.
  A reportable cell only says the follow-up reaction experiment may have enough
  observations to be worth scoping.
- **Expected output**:
  - `event_coverage.csv`;
  - `domain_readiness.csv`;
  - `direction_balance.csv`;
  - `run_metadata.json` final status:
    `SUPPORTED_FULL`, `SUPPORTED_NARROW`, `REFUTED`, or `INCONCLUSIVE`.

## Visualisations

1. Event-density heatmap by instrument/domain - shows which cells are usable.
2. Direction-balance bar chart by instrument/domain - shows bullish/bearish
   degeneracy.
3. Regime-length and anchor-age distributions - checks whether anchors reset at
   plausible frequencies.
4. Bounded AVWAP overlay for one deterministic sample window per ready domain -
   visual audit of AVWAP, bands, anchors, and bounce markers.

## Interpretation Guide

- If all invariants pass, determinism matches, and all three domains are ready,
  interpret EXP-020 as `SUPPORTED_FULL`: EXP-021 may scope 5m, 1h, and 4h.
- If all invariants pass, determinism matches, and one or two domains are ready,
  interpret EXP-020 as `SUPPORTED_NARROW`: EXP-021 may scope only the ready
  domains after governance records the domain restriction.
- If any invariant fails, determinism mismatches, an event reaches the holdout,
  or no domain is ready, interpret EXP-020 as `REFUTED`: do not proceed to
  reaction or strategy screening for this branch.
- If invariants pass but coverage is borderline under the scope's inconclusive
  rule, interpret EXP-020 as `INCONCLUSIVE`: a new scope is required for any
  follow-up.

## Complexity Check

- Statistical tests: 1 / 1. The readiness classification is deterministic and
  threshold-based; no distributional test is used.
- Visualisations: 4 / 4.
- New modules: 1 / 1. A reusable `xen.avwap` helper is allowed if the
  implementation needs it.

## Data-View Comparison Considerations

EXP-020 uses only time-bar-derived domain bars. There is no chart-type
alignment. All cross-domain comparisons are descriptive and never align rows by
bar index. If future AVWAP variants use chart types, they require new registry
entries and scopes.

## Implementation Safety and Performance

- Use lazy Polars scans and slice to the first 70% before collection.
- Keep the AVWAP state machine sequential and explicit.
- Use `tqdm` over instrument/domain loops.
- Do not create output directories at import time.
- Do not convert full large frames to pandas for plots; plot only bounded
  summary tables or a preselected sample window.
- Reuse generated event/state tables for plotting instead of regenerating the
  AVWAP state machine.
- Treat zero total event counts and zero direction counts as non-reportable
  denominators, not as zero-percent effects.
- Record all parameter values and registry references in `run_metadata.json`.
- Do not compute EXP-021 reaction returns, EXP-022 band-target outcomes,
  EXP-022 trend-change completions, or P&L in EXP-020; only persist event
  metadata needed to implement those follow-ups.

## Expected Output Files

```text
python/experiments/EXP-020/results/
├── analysis_metadata.csv
├── avwap_events.csv
├── avwap_state_summary.csv
├── invariant_checks.csv
├── determinism_check.csv
├── event_coverage.csv
├── domain_readiness.csv
├── direction_balance.csv
└── run_metadata.json

python/experiments/EXP-020/plots/
├── event_density_heatmap.png
├── direction_balance.png
├── regime_anchor_distributions.png
└── avwap_sample_overlay.png
```
