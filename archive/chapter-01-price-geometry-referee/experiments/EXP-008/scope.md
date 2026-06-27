# Experiment: EXP-008 - Per-Instrument MDE De-Pooling

## Hypothesis

Per-instrument gate-stack economic MDEs differ **materially** from the Phase 001
four-instrument pooled domain MDEs (EXP-003), where "materially" is the
predeclared, frozen margin

```
|per_instrument_MDE(instrument, domain) - pooled_MDE(domain)| >= max(0.5 bps, 20% of pooled_MDE(domain))
```

evaluated at the primary operating point `alpha0 = 0.05` for the frozen 5-check
gate stack. This is a **descriptive** comparison: a material difference on one or
more instrument/domain cells supports H-pool (the pooled MDE masks instrument
heterogeneity); all cells within the margin refutes it (the pooled MDE is a good
per-instrument proxy). Either direction is informative.

The frozen margin above is restated and **frozen here before any per-instrument
MDE artifact is loaded or computed**, per design `H-pool` (§4) and the §2 ⚠
predeclaration discipline. It may be changed only by a dated amendment authored
before any EXP-008 result is read.

## Question

When the EXP-003 pooled-by-domain gate-stack MDE map is de-pooled by instrument,
do the per-instrument MDEs stay within the predeclared margin of the pooled
domain MDE, or do specific instruments sit materially above or below it?

## Scope Boundaries

- **Data Views**: EXP-003 draw-level verdict artifacts are the primary and only
  data view. No new market-data measurement is required. The de-pooling is a
  result-level reprocessing of already-holdout-safe EXP-003 outputs (the same
  pattern as EXP-006 and EXP-007). If implementation must replay any harness
  step, it uses only the first 70% analysis slice and the existing EXP-003
  loading pattern.
- **De-pooling unit**: Group EXP-003 `draw_verdicts.csv` by
  `instrument x domain x referee x alpha` (and `edge_bps` for TPR) instead of
  pooling the four instruments. Sample membership, denominators, leg states,
  costs, materiality constants, and real-price effect/CI fields are reused from
  EXP-003 **unchanged**; only the grouping key changes (pooled -> per-instrument).
- **Per-instrument FPR**: Per `instrument x domain x referee x alpha`, FPR =
  fraction of null-scenario draw verdicts that PASS. Null denominator per cell is
  the per-instrument null-draw verdict count (EXP-003 used 500 draws per null
  generator per instrument per domain across two null generators -> ~1000 null
  verdicts per instrument/domain/referee/alpha).
- **Per-instrument TPR**: Per `instrument x domain x referee x alpha x edge_bps`,
  TPR = fraction of positive-scenario draw verdicts that PASS. Positive
  denominator per cell is the per-instrument positive-draw verdict count
  (EXP-003 used 500 positive draws per edge per instrument per domain).
- **Per-instrument MDE definition (matches EXP-003)**: For the gate stack at a
  given `instrument x domain x alpha`, the MDE is the **smallest planted edge in
  the EXP-003 edge grid** `{0.5, 1.0, 2.0, 4.0, 8.0, 12.0, 16.0, 24.0, 32.0}` bps
  whose per-instrument TPR `>= 0.80` while the per-instrument FPR at that cell is
  `<= alpha0`, with the D-prec precision target met (FPR Wilson half-width
  `<= 0.03` and TPR Wilson half-width `<= 0.05`). This reproduces the EXP-003 MDE
  definition restricted to a single instrument. The discrete grid means each MDE
  is grid-quantized; the local grid spacing to the next-lower grid point is
  reported as `mde_grid_uncertainty_bps`, mirroring EXP-003 `mde_summary.csv`.
- **Material-difference comparison**: For each `instrument x domain` at `alpha0`,
  compare the per-instrument gate MDE against the EXP-003 pooled gate MDE for that
  domain (read at runtime from EXP-003 `mde_summary.csv`, rows
  `referee=gate_stack, alpha=0.05`; expected values 5m=1.0, 1h=4.0, 4h=12.0 bps,
  asserted finite). Flag the cell `material` when the absolute difference meets
  the frozen margin above. Differences smaller than the local grid spacing are
  reported as `within_grid_resolution` and not over-interpreted.
- **Referees**: Gate stack is the headline referee (its MDE is the object H-pool
  is about). Minimal-baseline per-instrument rates may be emitted as optional
  diagnostic context but are not headline and carry no verdict.
- **Parameters**: Domains `{5m, 1h, 4h}`; alpha grid `{0.10, 0.05, 0.01}` with
  primary `alpha0=0.05`; TPR target `0.80`; EXP-003 edge grid as above; frozen
  margin `max(0.5 bps, 20% of pooled_MDE(domain))`.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC — each reported separately
  (this is the de-pooling experiment; the never-pool exception of design §5).
- **Dependencies**: EXP-001 `run_metadata.json` must record
  `overall_status == "PASS"`. EXP-003 is a measurement run, so its gate is
  artifact-based (mirroring EXP-004/EXP-005/EXP-006): require EXP-003
  `run_metadata.json` present with `overall_status == "COMPLETE"`,
  `draw_verdicts.csv` containing per-instrument rows for both scenarios, and
  `mde_summary.csv` containing finite pooled gate-stack MDE rows at the alpha
  grid.
- **Time range**: Inherited from EXP-003. Full dataset with the EXP-003 nested
  chronological split per instrument file; first 70% = analysis set; final 30% =
  global holdout and is never used.
- **Global holdout**: The final 30% of each source file must not be loaded,
  inspected, or used in any capacity. Result-level post-processing of EXP-003
  artifacts is preferred because those artifacts are already holdout-safe.
- **Look-ahead bias prevention**: No new signal construction is in scope. The
  reused EXP-003 draws used only `t -> t+1` real Close-to-Close returns and
  train-only block-length estimation.
- **Real-price outcome discipline**: All effect and CI fields reused from EXP-003
  are based on real domain `Close` prices. No synthetic chart prices are in scope.
- **Exclusions**: Generating fresh draws or new market-data measurement; the
  near-MDE realistic candidate (EXP-005); the L5 threshold sweep (EXP-006) and
  lenient-L5 variant (EXP-007); broadened strategy effect-size distribution
  (EXP-009); split-protocol comparison (EXP-010); loss-function selection or
  operating-point adoption (EXP-011); referee redesign; chart-type signals;
  parameter tuning; and any change to EXP-003 leg logic, costs, materiality,
  sample membership, or denominators.

## Success / Failure Criteria

The phase treats EXP-008's deliverable as the per-instrument map; the H-pool
verdict is the descriptive read of that map.

- **Evidence FOR (H-pool supported)**: With usable precision (D-prec met) at
  `alpha0`, at least one `instrument x domain` per-instrument gate MDE differs
  from its pooled domain MDE by at least the frozen margin. The per-instrument
  MDE map is produced for every reportable cell.
- **Evidence AGAINST (H-pool refuted)**: With usable precision at `alpha0`, every
  reportable per-instrument gate MDE lies within the frozen margin of its pooled
  domain MDE (the pooled MDE is an adequate per-instrument proxy).
- **Inconclusive (per cell)**: A per-instrument cell misses the D-prec precision
  target (FPR Wilson half-width `> 0.03` or TPR Wilson half-width `> 0.05`), or
  has no finite per-instrument MDE over the scoped edge grid. Expected most
  likely on 4h per-instrument cells; reported as under-powered with honest CIs,
  never forced to a verdict. EXP-008 is overall inconclusive only if no
  instrument/domain cell is reportable at `alpha0`.

## Complexity Budget

- Max statistical tests: 3 (per-instrument FPR Wilson intervals; per-instrument
  TPR Wilson intervals / MDE determination; material-difference comparison)
- Max visualisations: 4
- Max new code modules: 0 (result-level post-processing of EXP-003 CSV artifacts;
  no shared `python/src/xen` change, so no P0/temporal re-validation is triggered)

## Data Requirements

Use EXP-003 verdict-level artifacts as the measurement substrate:

- `python/experiments/EXP-001/results/run_metadata.json`
- `python/experiments/EXP-003/results/run_metadata.json`
- `python/experiments/EXP-003/results/draw_verdicts.csv`
- `python/experiments/EXP-003/results/mde_summary.csv`

Parse the per-draw rows (columns include `instrument, domain, scenario,
generator, edge_bps, draw, referee, alpha, verdict, passed, ...`), regroup by
instrument instead of pooling, and recompute Wilson FPR/TPR and the
per-instrument MDE. Use the existing `xen.referee_calibration.wilson_interval`
and `verdict_rate_rows` helpers unchanged for the rate computations. Use draw
verdict counts as denominators (no silent deduplication).

Primary expected outputs:

- `per_instrument_fpr_summary.csv`
- `per_instrument_tpr_summary.csv`
- `per_instrument_mde_summary.csv`
- `mde_pool_comparison.csv` (per-instrument vs pooled MDE, with `material` flag)
- `run_metadata.json`

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

Result-level post-processing of EXP-003 artifacts is preferred for EXP-008. The
loading pattern above is included only as the mandatory safety pattern if
implementation must replay any harness step.

## Suggested Direction

Treat this as a de-pooling measurement, not an adoption decision. Report each
per-instrument MDE in absolute bps next to its pooled domain MDE and the frozen
margin, and let EXP-011 decide whether per-instrument heterogeneity changes the
recommended operating point. Where 4h per-instrument cells are under-powered, say
so explicitly rather than forcing an MDE.
