# Analysis Plan: Experiment EXP-012

## Objective

Determine whether the available 1-minute time-bar datasets are sufficient for Phase 003 ICT macro-window research without using unavailable preferred data or the final 30 percent global holdout.

## Methodology

### Step 1: Chronological Data Inventory

- **Method**: For each `data/timebars/` file, sort by `CloseTime`, exclude the final 30 percent global holdout, then report instrument, row count, first/last analysis timestamp, train/test counts, duplicate timestamps, and OHLC consistency failures.
- **Why this method**: The phase cannot proceed unless the time-bar base data and chronological slicing are trustworthy.
- **Simpler alternative considered**: File-name inspection alone is insufficient because it does not verify timestamp order, row coverage, or integrity.
- **Assumptions**: `CloseTime` is the authoritative ordering column from the dataset reference.
- **Expected output**: Data-readiness table by instrument and segment.

### Step 2: NY-Time and Macro-Window Feasibility

- **Method**: Apply the documented server-to-New-York conversion assumption, assign each analysis-set bar to the fixed macro windows, and compute expected versus observed bar counts by instrument, window, train/test segment, and NY date.
- **Why this method**: H1 and later macro-filter experiments require deterministic NY-time window membership.
- **Simpler alternative considered**: Testing only one macro window would not validate the full source-spec window set.
- **Assumptions**: Daylight-saving behavior is handled by `America/New_York`; any server timezone uncertainty is recorded as a readiness caveat.
- **Expected output**: Macro-window coverage table and missing-bar report.

### Step 3: Cost-Data Availability and Proxy Declaration

- **Method**: Confirm that bid, ask, commission, and slippage fields are absent or present in the schema; if absent, define labelled proxy scenarios for later experiments without applying them to outcomes here.
- **Why this method**: The planning spec requires costs or defensible assumptions, while the dataset reference only confirms OHLCV time bars.
- **Simpler alternative considered**: Ignoring costs would make later strategy-like experiments non-compliant.
- **Assumptions**: Cost proxies are scenario inputs, not inferred facts about the broker feed.
- **Expected output**: Cost-data availability statement and proxy scenario list.

## Visualisations

1. Bar coverage heatmap by instrument and NY macro window.
2. Missing-bar rate by instrument and train/test segment.
3. Optional timestamp timeline for any instrument with conversion or gap anomalies.

## Interpretation Guide

- Support: all four instruments meet the scoped conversion and >= 80 percent macro-window coverage thresholds, with documented cost proxy scenarios.
- Against: most instruments fail conversion or macro-window coverage, or missing bars exceed the scoped failure threshold.
- Inconclusive: some instruments are usable but coverage or timezone caveats prevent a phase-wide decision.

## Complexity Check

- Statistical tests: 0 / 0-1
- Visualisations: 2-3 / 4
- New modules: 1 / 1
