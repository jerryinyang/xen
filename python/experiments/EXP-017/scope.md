# Experiment: EXP-017 - Revised Incremental Referee Golden-Fixture Correctness

## Hypothesis

The revised incremental referee, with L2 removed and retained legs L1, L3, L4', and L5, reproduces predeclared hand-computed verdicts on deterministic golden fixtures, exposes every retained leg without short-circuiting, omits L2 from the gate, and keeps L3 as the binding incremental-beyond-R claim.

## Question

Does the revised incremental referee logic behave exactly as specified before EXP-018 measures its operating characteristics?

## Scope Boundaries

- **Data Views**: Deterministic in-memory return-space and position fixtures. No market Parquet files are required except optional dependency metadata checks.
- **Parameters**: Primary `alpha0 = 0.05`; revised gate `L1 and L3 and L4' and L5`; L2 standalone-significance leg removed; L1 readiness on the incremental position; L3 incremental-beyond-R `ci_lower_bps > 0` on the marginal series; L4' no material sign reversal of the incremental edge across train/OOS; L5 strict `ci_lower_bps > materiality`; EXP-013 incremental substrate and D-incr-form marginal-net-P&L estimator reused unchanged.
- **Instruments**: Fixture labels may use the carried-forward instrument/domain conventions, but this is a logic test rather than a market-behavior experiment.
- **Time range**: Not applicable to fixture values. If dependency checks read real-data metadata, the final 30% global holdout remains excluded.
- **Global holdout**: The final 30% of the full dataset must not be loaded, inspected, or used in any capacity.
- **Look-ahead bias prevention**: Fixture expected values must be computed from fixture rows available at or before the evaluated timestamp.
- **Real-price outcome discipline**: Fixture returns represent real-price return contributions. No synthetic chart construction prices are in scope.
- **Metric denominators**: Verdict-match denominator is all predeclared fixture verdict rows. Leg-exposure denominator is fixture rows times the four retained legs. L2-absence denominator is all fixture rows. Zero-match failures are reported as counts and rates, not percentage improvements.
- **Fixture manifest**: Before replay, fixtures must include exact return/position rows, expected marginal-P&L fields, expected verdict, expected states for L1, L3, L4', and L5, and an explicit assertion that L2 is absent from the gate output for at least this coverage matrix:

  | Fixture ID | Purpose | L1 | L3 incremental-beyond-R | L4' no material sign reversal | L5 strict materiality | L2 | Expected verdict |
  | --- | --- | --- | --- | --- | --- | --- | --- |
  | `all_pass_revised` | Positive marginal edge with sufficient denominator, incremental evidence, no material sign reversal, and strict materiality | PASS | PASS | PASS | PASS | ABSENT | PASS |
  | `l1_readiness_fail` | Insufficient eligible/incremental denominator while retained computed quantities are otherwise favorable | FAIL | PASS | PASS | PASS | ABSENT | REJECT |
  | `l2_absent_former_standalone_fail` | Candidate lacks standalone significance but has positive material incremental edge, proving L2 removal changes the old L2-isolated fixture behavior | PASS | PASS | PASS | PASS | ABSENT | PASS |
  | `l3_reference_control_fail` | Candidate has standalone-looking edge but adds no marginal edge beyond R | PASS | FAIL | PASS | FAIL | ABSENT | REJECT |
  | `l4_material_sign_reversal_fail` | Incremental edge is globally favorable but has a material sign reversal across train/OOS | PASS | PASS | FAIL | PASS | ABSENT | REJECT |
  | `l5_strict_materiality_fail` | Incremental CI lower bound clears zero but not the strict materiality threshold | PASS | PASS | PASS | FAIL | ABSENT | REJECT |
  | `redundant_shared_structure` | R and C share latent structure with no marginal edge, guarding against phantom incremental pass | PASS | FAIL | PASS | FAIL | ABSENT | REJECT |

  Because L5 is strict `ci_lower_bps > materiality`, L5 implies L3 on the same marginal series. Fixtures must not require an impossible L3-fail/L5-pass state. Under this nesting **L5 (not L3) is the operationally binding leg** of the conjunction; L3 is exposed and verified as L5's directional precondition, so no fixture isolates an "L3-binding" state (see Phase 003b amendment [B1](../../../docs/experiments-docs/checkpoints/2026-06-05-003b-incremental-unit-redesign/amendments/2026-06-05-B1-pre-execution-review-corrections.md), F01).

  **Fixture nature (B1/F04).** These are *seeded-deterministic* fixtures: returns are generated from a fixed per-fixture seed and the retained-leg states are the predeclared, hand-reasoned outcomes of the revised gate on that fixed draw (verified against the fixed-seed block bootstrap), not closed-form analytic values. The construction is *adapted from* the EXP-014 fixture builder (B1/F05); the `l2_absent_former_standalone_fail` cell reuses EXP-014's L2-isolating parameters and additionally asserts at run time that the legacy standalone leg would have failed, so the L2-removal behavior is checked rather than assumed. The `l5_strict_materiality_fail` cell plants ~0.45 bps against the 0.5 bps materiality: L5=False is robust (CI lower < point estimate < materiality), and L3=True relies on the planted edge clearing zero, which has precedent in EXP-014's analogous fixture.
- **Dependency gate**: EXP-013 substrate must remain valid. EXP-014 is the predecessor logic fixture suite and must be cited as the prior implementation being revised. If the L2-removal patch touches shared estimator or CI code paths (`marginal_net_series`, `incremental_edge_ci`, `_contiguous_block_length`, or equivalent), EXP-013 must be re-run before EXP-017/018.
- **Exclusions**: Incremental MDE calibration; dependence-grid operating-characteristic measurement; real candidate signals; chart-type candidates; modifying the EXP-013 estimator based on fixture outcomes; any use of the global holdout.

## Success / Failure Criteria

- **Evidence FOR**: Every fixture verdict and every retained gate-leg state matches the predeclared, hand-reasoned expectation (seeded-deterministic, not closed-form), every retained leg is exposed for every fixture without short-circuiting, and L2 is absent from the revised gate output for every fixture.
- **Evidence AGAINST**: Any verdict mismatch, retained leg-state mismatch, missing retained leg exposure, emitted L2 gate leg, or accidental modification of the reused substrate/estimator path without the required EXP-013 re-run.
- **Inconclusive**: Fixture definitions are incomplete, EXP-013 dependency status is unavailable, or expected outputs were not predeclared before replay.

## Complexity Budget

- Max statistical tests: 2
- Max visualisations: 3
- Max new code modules: 1

## Data Requirements

EXP-013 must validate the incremental substrate before EXP-017 executes. Fixtures must include the revised coverage matrix above with precomputed expected verdicts, retained leg states, marginal-P&L fields, denominators, materiality thresholds, and reference-control values sufficient to verify L2 absence and the L3/L5 nesting. The output should include fixture verdict results, retained-leg exposure matrix, L2-absence check, row-level mismatch details, and metadata proving no short-circuit behavior.

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

Keep EXP-017 as a deterministic correctness gate. It should prove exact revised leg composition, fixture verdicts, retained-leg exposure, and L2 absence, not estimate market behavior or operating characteristics.
