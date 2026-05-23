# Analysis Plan: Experiment EXP-020

## Objective

Validate that three-candle FVGs and close-through IFVG inversions can be detected reproducibly with stable sample sizes on approved time bars.

## Methodology

### Step 1: FVG Detection

- **Method**: Apply bearish `High[i] < Low[i-2]` and bullish `Low[i] > High[i-2]` definitions with the scoped minimum-size filter using prior ATR_14 and price precision.
- **Why this method**: It preserves the planning spec's three-candle FVG definition while avoiding tiny gaps caused by price precision noise.
- **Simpler alternative considered**: No size filter would be source-valid but may create unstable low-value micro-gaps.
- **Assumptions**: Candle `i` close is the first timestamp when the FVG is knowable.
- **Expected output**: FVG table with side, bounds, size, creation time, and segment.

### Step 2: Lifecycle and IFVG Classification

- **Method**: Track each FVG for 120 bars and label lifecycle state as formed, partially filled, fully filled, inverted, or expired; IFVG requires a later close through the opposite side.
- **Why this method**: Later IFVG entry studies need stable zones and timestamps.
- **Simpler alternative considered**: Counting FVGs only would not validate inversion mechanics.
- **Assumptions**: One FVG can have one first inversion timestamp; duplicate overlaps are counted but flagged.
- **Expected output**: Lifecycle table and IFVG count table.

### Step 3: Reproducibility and Sample Adequacy

- **Method**: Rerun detection with the same input/config and verify identical event IDs, bounds, and timestamps; compare counts against scoped floors.
- **Why this method**: EXP-021 depends on deterministic IFVG events.
- **Simpler alternative considered**: Manual spot checks alone are insufficient for reproducibility.
- **Assumptions**: Deterministic input ordering by `CloseTime`.
- **Expected output**: Reproducibility digest and readiness verdict by instrument.

## Visualisations

1. FVG and IFVG count bars by instrument and segment.
2. FVG size distribution.
3. Lifecycle state distribution.
4. Optional zone-duration distribution.

## Interpretation Guide

- Support: counts and lifecycle states are deterministic and meet FVG/IFVG floors across usable instruments.
- Against: definitions are ambiguous, unstable, or too sparse.
- Inconclusive: FVGs are common but IFVGs are too sparse for later entries.

## Complexity Check

- Statistical tests: 0 / 0-1
- Visualisations: 3-4 / 4
- New modules: 1 / 1
