# Analysis Plan: Experiment EXP-012

## Objective

Determine whether the fixed EXP-011 loose referee point reproduces its Phase 002 operating characteristics on fresh synthetic draws and therefore gets adopted per domain, or falls back to strict.

## Methodology

### Step 1: Fixed-Point and Dependency Verification

- **Method**: Deterministic artifact and configuration check.
- **Why this method**: EXP-012 is a ratification of a predeclared point. The first requirement is confirming the measured object is exactly the checkpoint object: EXP-011 tau 0.75/0.25/0.5, frozen strict reference, unchanged EXP-003 harness, EXP-010 corrected 4h estimator, and fresh seeds disjoint from Phase 001/002.
- **Simpler alternative considered**: Trusting filenames or comments. That is insufficient because the checkpoint makes predeclaration freeze and seed freshness part of the claim.
- **Assumptions**: Dependency artifacts are available and identify the Phase 002 MDE/sub-material values and prior seeds. This is a governance assumption, not a market-statistical assumption.
- **Expected output**: `run_metadata.json` dependency block and a fixed-point manifest.

### Step 2: Fresh-Draw FPR and MDE Measurement

- **Method**: Reuse the EXP-003 calibration harness on fresh known-null and known-positive draws. Summarize FPR and TPR with Wilson intervals; derive MDE as the smallest edge-grid point satisfying the scoped detection criterion at controlled FPR.
- **Why this method**: It directly measures the operating characteristics named by H-ratify while preserving comparability with Phase 002.
- **Simpler alternative considered**: Reuse Phase 002 draws. That would not test the Goodhart risk the checkpoint is targeting.
- **Assumptions**: The synthetic generators and real-price return substrate remain valid from EXP-001/EXP-003. Time ordering is by `CloseTime`; all observations come from the first 70% analysis slice.
- **Expected output**: FPR summary, TPR summary, MDE summary, and draw-level verdicts for each domain/referee/alpha cell.

### Step 3: Sub-Material Pass-Rate and Adoption Rule

- **Method**: Rule-based comparison against the frozen checkpoint thresholds: FPR <= alpha0 at D-prec, MDE within one edge-grid step of Phase 002, and sub-material pass rate within +/-0.10 absolute of Phase 002 and <=0.50.
- **Why this method**: Adoption is a binary predeclared rule, not a statistical model selection problem.
- **Simpler alternative considered**: Rank domains by loss or choose the best observed tau. That is outside scope because tau is frozen before measurement.
- **Assumptions**: Sub-material pass rate is computed on the same denominator used in Phase 002 for the operating MDE. Zero pass counts are represented as zero rates with Wilson intervals, not percentage deltas.
- **Expected output**: Per-domain adoption table with explicit FPR, MDE, sub-material rate, and verdict `ADOPT_LOOSE` or `STRICT_FALLBACK`.

### Step 4: 4h Split-Sensitivity Gate

- **Method**: Compare the 4h single chronological split with anchored walk-forward K=5 using the corrected EXP-010 test-size-weighted, stratified pooled-OOS estimator.
- **Why this method**: The checkpoint adds this as a 4h-specific adoption gate because corrected EXP-010 flagged 4h split sensitivity.
- **Simpler alternative considered**: Use the single split only. That would omit a checkpoint-required condition.
- **Assumptions**: Both protocols remain inside the first 70% analysis set. Agreement means MDEs within one edge-grid step and both FPR values <= alpha0 at D-prec.
- **Expected output**: 4h protocol-comparison table and final 4h binary adoption/fallback decision.

## Visualisations

1. Bar plot of fresh-draw FPR with Wilson intervals by domain and referee - shows alpha0 control.
2. MDE comparison plot of Phase 002 versus fresh-draw MDE by domain - shows one-grid-step agreement or failure.
3. Sub-material pass-rate plot by domain - shows +/-0.10 tolerance and 0.50 ceiling.
4. 4h protocol comparison plot - shows single split versus anchored walk-forward MDE and FPR.

## Interpretation Guide

- If a domain passes all adoption conditions, the loose referee is adopted for that domain because the fixed point reproduced its predeclared operating characteristics on fresh seeds.
- If a domain fails any adoption condition, that domain falls back to strict because ratification is confirm-or-reject, never re-select.
- If 4h passes the single-split adoption criteria but fails the protocol-agreement gate, 4h falls back to strict with no intermediate caveat verdict.
- If a cell cannot meet D-prec, report it as under-powered and do not force an adoption decision from that cell.

## Complexity Check

- Statistical tests: 4 / 4
- Visualisations: 4 / 4
- New modules: 0-1 / 1

## Data-View Comparison Considerations

### Cross-View Alignment

- Domain bars must share split boundaries from canonical base `CloseTime` timestamps.
- Do not align domains by row count or bar index.

### Implementation Safety and Performance

- Use lazy Polars scans and slice the first 70% before collecting data.
- Use `tqdm` progress tracking for instrument, domain, alpha, edge, draw, and protocol loops.
- Keep sequential synthetic draw generation reproducible with recorded seeds.
- Do not optimize by changing sample membership, temporal ordering, denominators, metric definitions, or reproducibility.

### Real-Price Outcome Discipline

- All return and referee metrics use real OHLC domain prices.
- Chart-type and synthetic construction prices are out of scope.

### Event Density Differences

- Sparse or under-powered cells must report draw denominators and Wilson half-widths.

### Regime Stratification

- No regime stratification is scoped for EXP-012.
