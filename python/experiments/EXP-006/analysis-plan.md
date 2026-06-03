# Analysis Plan: Experiment EXP-006

## Objective

Measure the gate stack's L5 stringency lever curve by sweeping the materiality threshold magnitude and recomputing FPR, TPR, and MDE from the EXP-003 draw-level verdicts without changing the referee's other legs.

## Methodology

### Step 1: Dependency and Artifact Load

- **Method**: Require supported EXP-001 and EXP-003 metadata, then load EXP-003 `draw_verdicts.csv`, `fpr_summary.csv`, `tpr_summary.csv`, and `mde_summary.csv`.
- **Why this method**: EXP-006 is explicitly a characterization of the EXP-003 calibrated harness and should not create a new draw substrate.
- **Simpler alternative considered**: Re-running EXP-003 draws would be redundant and would add compute without changing the scoped question.
- **Assumptions**: EXP-003 draw verdict rows contain all fields needed to reconstruct gate-stack pass states: `ci_lower_bps`, `effect_bps`, `passed`, `alpha`, and serialized L1-L5 diagnostics.
- **Expected output**: Dependency status in `run_metadata.json`.

### Step 2: Threshold-Swept Gate Reconstruction

- **Method**: For each gate-stack draw row and threshold `tau`, parse `leg_results`, keep L1-L4 unchanged, replace only L5 with `ci_lower_bps > tau_bps`, and recompute the conjoined pass flag.
- **Why this method**: It changes exactly the scoped L5 threshold magnitude while preserving the frozen reference gate's other mechanics and sample membership.
- **Simpler alternative considered**: Modifying `xen.referee_calibration.gate_stack_row` would risk changing the frozen harness and is unnecessary for post-processing.
- **Assumptions**: The EXP-003 `ci_lower_bps` field is the net-of-cost neutral CI lower bound used by frozen L5; `tau=1.00 x materiality` should reproduce EXP-003 gate-stack rows.
- **Expected output**: `threshold_draw_verdicts.csv`.

### Step 3: FPR and TPR Summaries

- **Method**: Compute Wilson-interval FPR from null rows and TPR from positive rows for each domain/alpha/threshold/edge cell.
- **Why this method**: FPR and TPR are Bernoulli pass-rate estimates and need the same precision accounting as EXP-003.
- **Simpler alternative considered**: Reporting raw pass rates without uncertainty would not meet Phase 002 precision criteria.
- **Assumptions**: Draw denominators are inherited from EXP-003 and remain fixed across thresholds; null and positive scenario labels remain unchanged.
- **Expected output**: `threshold_fpr_summary.csv` and `threshold_tpr_summary.csv`.

### Step 4: MDE Frontier and Strict-Reference Check

- **Method**: For each domain/alpha/threshold, define MDE as the smallest planted edge with FPR `<= alpha`, TPR `>= 0.80`, FPR Wilson half-width `<= 0.03`, and TPR Wilson half-width `<= 0.05`. Confirm that `tau=1.00 x materiality` reproduces EXP-003 gate MDE and FPR.
- **Why this method**: It directly traces the materiality lever curve and checks that the reconstruction did not drift from the frozen reference.
- **Simpler alternative considered**: A monotonicity-only check would not produce the MDE frontier required by `design.md`.
- **Assumptions**: MDE is grid-resolution limited; missing grid crossings are inconclusive, not infinite precision failures.
- **Expected output**: `threshold_mde_summary.csv` and `strict_reference_check.csv`.

## Visualisations

1. FPR vs threshold multiplier by domain at `alpha=0.05` - shows false-positive cost of reducing L5.
2. MDE vs threshold multiplier by domain at `alpha=0.05` - shows sensitivity gained or lost.
3. TPR curves by threshold for each domain - shows where power crosses 0.80.
4. Frontier plot of MDE against FPR by domain - summarizes the lever trade-off.

## Interpretation Guide

- If lowering `tau` reduces MDE while FPR remains `<= alpha0`, L5 is a usable sensitivity lever over that range.
- If lowering `tau` increases FPR above `alpha0`, the sensitivity gain is bought by unacceptable false positives.
- If MDE does not change across thresholds, another gate leg is binding over the scoped edge grid.
- If `tau=1.00 x materiality` fails to reproduce EXP-003, the reconstruction is invalid and the experiment fails before interpretation.
- If a cell misses precision or has no finite MDE, report it as inconclusive rather than extrapolating between grid points.

## Complexity Check

- Statistical tests: 3 / 3
- Visualisations: 4 / 4
- New modules: 0 / 0

## Data-View Comparison Considerations

### Cross-View Alignment

- EXP-006 is result-level post-processing of EXP-003; no cross-view market-data alignment is introduced.
- If any harness replay is required, use `CloseTime` ordering and the same domain construction as EXP-003.

### Implementation Safety and Performance

- Do not read or materialize source market data unless needed for a narrow audit check.
- Keep threshold reconstruction as a pure transformation of verdict rows.
- Use Polars group-by summaries for rate tables; convert only small summaries to pandas for plotting.
- Use `tqdm` if reconstructing over large draw/threshold loops.
- Do not alter draw membership, alpha values, edge values, leg definitions L1-L4, cost assumptions, materiality constants, or denominators.

### Real-Price Outcome Discipline

- Reused EXP-003 effect fields are already based on real domain `Close` returns.
- No Heiken Ashi, Renko, Line Break, or other chart-type prices are in scope.

### Denominators and Zero-Baseline Behavior

- FPR denominator is null draw verdict count per domain/alpha/threshold.
- TPR denominator is positive draw verdict count per domain/alpha/threshold/edge.
- MDE differences are reported in absolute bps and grid half-steps. Do not report percentage improvement when the baseline MDE is zero, missing, or non-finite.
- `tau=0` means a zero materiality buffer in the same L5 threshold mechanism; classify any `tau=0` MDE as an endpoint of the sweep, not as an adopted lenient referee.
