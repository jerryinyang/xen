# Analysis Plan: Experiment EXP-003

## Objective

Measure the operating characteristics of the minimal baseline and 5-check gate-stack referees on the validated synthetic substrate.

## Methodology

### Step 1: Dependency Gate

- **Method**: Require EXP-001 and EXP-002 metadata with `overall_status == "PASS"`.
- **Why this method**: EXP-003 depends on substrate validity and referee fixture correctness.
- **Simpler alternative considered**: Re-running those checks inside EXP-003 would duplicate scope and weaken phase traceability.
- **Assumptions**: Passing metadata is the approved pipeline signal from prior experiments.
- **Expected output**: Dependency status in `run_metadata.json`.

### Step 2: Paired Null Calibration

- **Method**: Feed identical known-null draws to both referees, using bar-permutation and random-signal nulls, and compute FPR/TNR with Wilson intervals.
- **Why this method**: Paired draws reduce baseline-vs-stack comparison noise and directly measure false positives.
- **Simpler alternative considered**: Unpaired draws are simpler but less precise for the same compute budget.
- **Assumptions**: Wilson intervals are distribution-free for Bernoulli pass/reject outcomes. Draws are generated from analysis-set real returns only.
- **Expected output**: Null rows in `draw_verdicts.csv` and `fpr_summary.csv`.

### Step 3: Paired Positive Calibration

- **Method**: Feed identical known-positive draws to both referees over the predeclared edge grid and compute TPR/FNR with Wilson intervals.
- **Why this method**: The TPR curve is required to locate empirical MDE.
- **Simpler alternative considered**: Testing one edge magnitude would not identify the MDE.
- **Assumptions**: The EXP-001 substrate validated the injection mapping. The state is observable at time `t`; outcome is `t -> t+1` real return.
- **Expected output**: Positive rows in `draw_verdicts.csv` and `tpr_summary.csv`.

### Step 4: MDE and Gate-Leg Diagnostics

- **Method**: For each domain/referee/alpha cell, choose the smallest `m` where FPR <= alpha and TPR >= 0.80 with usable precision. For gate-stack rows, parse L1-L5 pass rates.
- **Why this method**: This is the checkpoint's primary measured-stringency deliverable.
- **Simpler alternative considered**: Reporting only pass rates would not answer the economic-MDE question.
- **Assumptions**: MDE is grid-resolution limited; uncertainty is reported as a grid half-step and Wilson precision.
- **Expected output**: `mde_summary.csv` and `leg_pass_rates.csv`.

## Visualisations

1. FPR by domain/referee/alpha.
2. TPR curve by domain/referee.
3. MDE by domain/referee/alpha.
4. Gate-leg pass rates by domain.
5. Effective sample summary by domain.

## Interpretation Guide

- If FPR is controlled and TPR reaches 0.80 at finite `m`, the referee has a measured MDE for that domain.
- If FPR exceeds alpha, the referee is too permissive at that operating point.
- If FPR is controlled but TPR never reaches 0.80, the referee is structurally blind over the scoped edge grid.
- If Wilson precision misses the target, the cell is inconclusive rather than forced to a verdict.

## Complexity Check

- Statistical tests: 4 / 4
- Visualisations: 5 / 5
- New modules: 1 / 1

## Implementation Safety and Performance

- Use lazy Polars loading and slice the first 70% before collection.
- Use `tqdm` progress over instrument/domain/draw loops.
- Do not materialize the holdout or convert full raw datasets to pandas.
- Keep draw rows bounded to verdict-level outputs; do not store per-bar simulated returns.
- Estimate bootstrap block length on train returns only and reuse real-price `Close` returns for all candidate outcomes.

