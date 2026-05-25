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

### Step 3: Reproducibility, Base Rate, and Sample Adequacy

- **Method (reproducibility)**: Run two invariance checks per instrument and compare SHA-256 digests of FVG identity columns. (a) Fresh disk reload via `load_analysis_timebars` builds an independent in-memory frame and reruns detection. (b) The input rows are shuffled with a fixed seed, re-sorted by `CloseTime`, and detection is rerun. Both digests must match the first pass. A same-process repeat of `detect_fvgs` on identical inputs is not a meaningful reproducibility test and is not used.
- **Method (base rate)**: Report `IFVGRate = IFVG_N / FVG_N` per instrument/segment. When `IFVGRate >= 0.5`, IFVG inversion is no longer a discriminating event under the current parameterisation; the instrument is flagged as `Tautological` and cannot pass the readiness gate even if FVG/IFVG counts clear the floors.
- **Method (sample adequacy)**: Compare counts against the scoped floors (`>= 100` FVGs, `>= 50` IFVGs per usable instrument/segment). Floors are intentionally low; the tautology check is what actually gates readiness on this 1-minute dataset.
- **Why this method**: EXP-021 depends on deterministic IFVG events *and* on IFVG being a selective signal. The original check tested neither.
- **Expected output**: Reproducibility digest table (with `FreshReloadMatches`, `ShuffledResortMatches`), count/readiness/tautology table, and a verdict by instrument.

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
