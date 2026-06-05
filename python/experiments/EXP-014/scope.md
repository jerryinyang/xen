# Experiment: EXP-014 - Incremental Referee Golden-Fixture Correctness

## Hypothesis

The incremental referee reproduces predeclared hand-computed verdicts on deterministic golden fixtures, exposes all gate legs without short-circuiting, and correctly generalizes L3 from naive control to reference control.

## Question

Does the incremental referee logic behave exactly as specified before it is used for operating-characteristic calibration?

## Scope Boundaries

- **Data Views**: Deterministic in-memory return-space and position fixtures. No market Parquet files are required unless dependency metadata is checked.
- **Parameters**: Primary `alpha0 = 0.05`; inherited cost/materiality conventions; fixed marginal-P&L estimator from EXP-013; gate-leg mapping from the checkpoint default: L3 becomes reference control, L1/L2 readiness and L4 cross-market apply to the incremental position, and L5 is the incremental-edge materiality buffer.
- **Instruments**: Fixture labels may use the carried-forward instrument/domain conventions, but this is a logic test rather than a market-behavior experiment.
- **Time range**: Not applicable to fixture values. If dependency checks read real-data metadata, the final 30% global holdout remains excluded.
- **Global holdout**: The final 30% of the full dataset must not be loaded, inspected, or used in any capacity.
- **Look-ahead bias prevention**: Fixture expected values must be computed from the fixture rows available at or before the evaluated timestamp.
- **Real-price outcome discipline**: Fixture returns represent real-price return contributions. No synthetic chart construction prices are in scope.
- **Metric denominators**: Verdict-match denominator is all predeclared fixture verdict rows. Leg-exposure denominator is fixture rows times gate legs. Zero-match failures are reported as counts and rates, not percentage improvements.
- **Fixture manifest**: Before replay, fixtures must include exact return/position rows, expected marginal-P&L fields, expected verdict, and expected L1-L5 states for at least this coverage matrix:

  | Fixture ID | Purpose | L1 | L2 | L3 reference control | L4 | L5 | Expected verdict |
  | --- | --- | --- | --- | --- | --- | --- | --- |
  | `all_pass_incremental` | Positive marginal edge with sufficient denominator, significance, reference-control improvement, cross-market support, and materiality | PASS | PASS | PASS | PASS | PASS | PASS |
  | `l1_readiness_fail` | Insufficient eligible/incremental denominator while other computed quantities are otherwise favorable | FAIL | PASS | PASS | PASS | PASS | REJECT |
  | `l2_significance_fail` | Marginal point estimate positive but CI lower bound fails the evidence threshold | PASS | FAIL | PASS | PASS | PASS | REJECT |
  | `l3_reference_control_fail` | Candidate has standalone-looking edge but adds no marginal edge beyond R | PASS | PASS | FAIL | PASS | PASS | REJECT |
  | `l4_cross_market_fail` | Primary cell passes locally but required cross-market confirmation is absent | PASS | PASS | PASS | FAIL | PASS | REJECT |
  | `l5_materiality_fail` | Incremental edge is positive/significant but below the materiality buffer | PASS | PASS | PASS | PASS | FAIL | REJECT |
  | `redundant_shared_structure` | R and C share latent structure with no marginal edge; guards against phantom incremental pass | PASS | FAIL | FAIL | PASS | FAIL | REJECT |

  Every fixture row must record all five legs even when an earlier leg fails. Any fixture added after this manifest requires a dated pre-results amendment.
- **Pre-execution confirmation gate**: The checkpoint requires operator confirmation or override of D-incr-legs before EXP-014 executes. This scope records the checkpoint default and does not replace that confirmation. Stage 4 governance must record the `PHASE003-TRACKB-PREDECLARATION-CONFIRMED` token or a later dated pre-results amendment before fixture replay.
- **Exclusions**: Incremental MDE calibration; dependence-grid operating-characteristic measurement; real candidate signals; chart-type candidates; modifying the EXP-013 estimator based on fixture outcomes; any use of the global holdout.

## Success / Failure Criteria

- **Evidence FOR**: Every fixture verdict and every expected gate-leg state matches the hand-computed expectation, and every leg is exposed for every fixture without short-circuiting.
- **Evidence AGAINST**: Any verdict mismatch, any leg-state mismatch, or any missing leg exposure.
- **Inconclusive**: Fixture definitions are incomplete or the EXP-013 substrate dependency has not passed.

## Complexity Budget

- Max statistical tests: 2
- Max visualisations: 3
- Max new code modules: 1

## Data Requirements

EXP-013 must validate the incremental substrate before EXP-014 executes. Fixtures must include the predeclared coverage matrix above with precomputed expected verdicts, leg states, marginal-P&L fields, denominators, materiality thresholds, and reference-control values sufficient to verify the L3 mapping and all five gate legs. The output should include fixture verdict results, a leg-exposure matrix, row-level mismatch details, and metadata proving no short-circuit behavior.

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

## Suggested Direction

Keep EXP-014 as a deterministic correctness gate. It should prove exact referee logic and leg exposure, not estimate market behavior or operating characteristics.
