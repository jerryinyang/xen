# Analysis Plan: Experiment EXP-004

## Objective

Reality-check the calibrated referee MDE map against simple real dogfood candidates without tuning those candidates.

## Methodology

### Step 1: Dependency and MDE Map Load

- **Method**: Read EXP-003 `mde_summary.csv` and use alpha `0.05` rows as the reference map.
- **Why this method**: EXP-004 explicitly depends on EXP-003 and anchors H-keystone against real candidate effect sizes.
- **Simpler alternative considered**: Comparing dogfood verdicts without MDE would not test consistency with the calibration map.
- **Assumptions**: Missing or non-finite MDE cells make the corresponding dogfood consistency cell inconclusive.
- **Expected output**: Dependency status in `run_metadata.json`.

### Step 2: Fixed Dogfood Candidate Evaluation

- **Method**: Generate Donchian(20) and MA(20,50) positions per instrument/domain, then evaluate both referees at alpha `0.05`.
- **Why this method**: The checkpoint names these simple real strategies as the dogfood anchor.
- **Simpler alternative considered**: More strategies or tuned lookbacks would expand scope and add degrees of freedom.
- **Assumptions**: Signals are standalone directional candidates. Donchian uses prior high/low windows; MA uses data available at bar close.
- **Expected output**: `dogfood_effects.csv`.

### Step 3: Consistency Classification

- **Method**: Locate each measured effect on the EXP-003 MDE map. Accept either verdict inside a grey band of one MDE grid half-step; otherwise require pass above MDE and reject below MDE.
- **Why this method**: It directly implements `design.md` section 10's consistency rule.
- **Simpler alternative considered**: A binary pass/reject count would hide whether disagreement is caused by real effects lying near the MDE boundary.
- **Assumptions**: MDE grid half-step is the appropriate Monte Carlo/grid-resolution uncertainty for this predeclared check.
- **Expected output**: `dogfood_consistency.csv`.

## Visualisations

1. Dogfood measured effects against MDE by domain/referee.
2. Consistency status count by domain.
3. Candidate verdict matrix.

## Interpretation Guide

- If verdicts match their MDE positions, H-dogfood is supported for those cells.
- If verdicts materially disagree with MDE positions, EXP-004 flags a synthetic-vs-real DGP gap.
- If MDE is missing or the effect lies in the grey band, the cell is inconclusive.

## Complexity Check

- Statistical tests: 2 / 2
- Visualisations: 3 / 3
- New modules: 0 / 0

## Implementation Safety and Performance

- No parameter tuning or strategy redesign is permitted.
- Use real domain `Close` prices for returns.
- Signals are aligned by timestamp through the ordered domain bars, never by cross-view bar counts.
- Bootstrap block length is estimated on train returns only.

