# Experiment: EXP-006 - L5 Materiality Threshold Sweep

## Hypothesis

This is an exploratory characterization experiment: how do the frozen gate stack's FPR and economic MDE vary as the L5 materiality threshold magnitude is swept per domain?

## Question

What is the L5 stringency lever curve, `MDE(tau)` and `FPR(tau)`, for the Phase 001 gate stack?

## Scope Boundaries

- **Data Views**: EXP-003 draw-level verdict artifacts are the primary data view. No new market-data measurement is required. If implementation replays any harness step, it must use only the first 70% analysis slice and the existing EXP-003 loading pattern.
- **Threshold sweep**: Sweep domain-normalized L5 thresholds `tau = multiplier x materiality_bps(domain)` for multipliers `{0.00, 0.25, 0.50, 0.75, 1.00, 1.50, 2.00}`. `tau=1.00 x materiality` is the frozen strict gate reference. `tau=0.00` is the zero-buffer endpoint of the same threshold mechanism.
- **Operational L5 rule**: Preserve the frozen harness mechanism and change only the L5 threshold magnitude: `L5_tau = ci_lower_bps > tau_bps` on the net-of-cost effect CI. L1-L4 remain unchanged from EXP-003. This follows `D-reuse` and `D-frozen-ref` in `design.md`.
- **Parameters**: Domains 5m, 1h, 4h; alpha grid `{0.10, 0.05, 0.01}` with primary `alpha0=0.05`; EXP-003 planted edge grid `{0.5, 1.0, 2.0, 4.0, 8.0, 12.0, 16.0, 24.0, 32.0}` bps for MDE summaries.
- **Referees**: Gate stack with swept L5 threshold. Minimal baseline is not modified and is included only as optional reference context.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC, pooled by domain to match EXP-003. Per-instrument rows may be emitted as diagnostics but are not headline.
- **Dependencies**: EXP-001 and EXP-003 must be supported. EXP-003 `draw_verdicts.csv`, `fpr_summary.csv`, `tpr_summary.csv`, and `mde_summary.csv` must exist.
- **Time range**: Full dataset with nested chronological split per instrument file as already applied by EXP-003. First 70% = analysis set; final 30% = global holdout and is never used.
- **Global holdout**: The final 30% of each source file must not be loaded, inspected, or used in any capacity. Result-level post-processing of EXP-003 artifacts is preferred because those artifacts are already holdout-safe.
- **Look-ahead bias prevention**: No new signal construction is in scope. Existing EXP-003 draws used only `t -> t+1` real Close-to-Close returns and train-only block-length estimation.
- **Real-price outcome discipline**: All effect and CI fields reused from EXP-003 are based on real domain `Close` prices. No synthetic chart prices are in scope.
- **Exclusions**: Lenient-L5 mechanism from EXP-007, near-MDE realistic candidates from EXP-005, per-instrument MDE de-pooling from EXP-008, loss-function selection from EXP-011, any threshold chosen for adoption, chart-type signals, and any referee redesign.

## Success / Failure Criteria

- **Evidence FOR**: The sweep produces FPR, TPR, and MDE summaries for every reportable domain/alpha/threshold cell, and the `tau=1.00 x materiality` rows reproduce the EXP-003 strict gate FPR and MDE at matching domain/alpha values.
- **Evidence AGAINST**: The strict-reference row cannot reproduce EXP-003, required EXP-003 artifacts are missing or inconsistent, or threshold rows cannot be reconstructed without changing L1-L4 or sample membership.
- **Inconclusive**: A domain/threshold cell misses the Phase 002 precision target (FPR Wilson half-width `> 0.03` or TPR Wilson half-width `> 0.05`) or has no finite MDE over the scoped edge grid.

## Complexity Budget

- Max statistical tests: 3
- Max visualisations: 4
- Max new code modules: 0

## Data Requirements

Use EXP-003 verdict-level artifacts as the measurement substrate:

- `python/experiments/EXP-003/results/draw_verdicts.csv`
- `python/experiments/EXP-003/results/fpr_summary.csv`
- `python/experiments/EXP-003/results/tpr_summary.csv`
- `python/experiments/EXP-003/results/mde_summary.csv`

Parse `leg_results` for gate-stack rows, keep L1-L4 fixed, and recompute only L5 and the conjoined pass flag for each threshold. Use draw verdict counts as denominators.

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

Result-level post-processing is preferred for EXP-006. The loading pattern above is included only as the mandatory safety pattern if implementation must replay the harness.

## Suggested Direction

Treat the sweep as a frontier measurement, not an operating-point choice. Report the sensitivity/stringency trade-off in absolute bps and FPR terms, and leave any recommendation or adoption decision to EXP-011 and Phase 003.
