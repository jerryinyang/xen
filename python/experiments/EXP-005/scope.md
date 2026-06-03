# Experiment: EXP-005 - Near-MDE Realistic-Candidate Detection Anchor

## Hypothesis

On each scoped domain, the frozen Phase 001 5-check gate stack detects an imperfect realistic candidate whose expected net real-price edge is at least the EXP-003 gate-stack MDE, with pooled-domain TPR >= 0.80 at `FPR <= alpha0 = 0.05`.

## Question

Is the oracle-calibrated EXP-003 MDE map an honest detection floor for a weak-but-real, imperfect candidate signal?

## Scope Boundaries

- **Data Views**: Base 1-minute time bars resampled to 5m, 1h, and 4h OHLC domains. No chart-type views are in scope.
- **Parameters**: 5m strict coverage; 1h and 4h `min_coverage=0.90`; primary `alpha0=0.05`; reporting alpha grid `{0.10, 0.05, 0.01}` for comparability with EXP-003; EXP-003 gate MDE map at `alpha=0.05`: 5m = 1.0 bps, 1h = 4.0 bps, 4h = 12.0 bps. The gate MDE per domain is **read at runtime** from EXP-003 `mde_summary.csv` (rows `referee=gate_stack`, `alpha=0.05`); the listed `1.0 / 4.0 / 12.0` bps are the predeclared expected values and are asserted finite. A domain whose gate MDE is missing or non-finite is reported inconclusive, never hardcoded.
- **Near-MDE edge grid**: For each domain, target candidate net edges are `{0.5, 1.0, 1.5, 2.0} x domain_gate_mde`, giving 5m `{0.5, 1.0, 1.5, 2.0}` bps, 1h `{2.0, 4.0, 6.0, 8.0}` bps, and 4h `{6.0, 12.0, 18.0, 24.0}` bps.
- **Realistic candidate construction**: For each draw, generate a latent state `S_t in {-1, +1}` with the same seed discipline as the EXP-003 synthetic substrate. Generate an imperfect candidate `C_t in {-1, 0, +1}` independently per eligible bar:
  - `p_active = 0.80`.
  - Conditional on being active, `C_t = S_t` with probability `q_match = 0.75`.
  - Conditional on being active, `C_t = -S_t` with probability `1 - q_match = 0.25`.
  - Conditional on not being active, `C_t = 0`.
  - These parameters are fixed and are not tuned.
- **Positive edge planting**: For positive draws, plant drift on the latent state, not directly on the candidate: `R'_t = R_t + S_t * (delta_bps / 10_000)` (drift added in real fractional return units), where `delta_bps = (target_edge_bps + p_active * cost_bps) / (p_active * (2 * q_match - 1))` and `cost_bps = cost_bps_for(instrument, domain)` from the frozen harness. Thus `delta_bps` is computed **per instrument** (costs differ: EURUSD 1, XAUUSD 3, BTCUSD 10, USTEC 4) while the target net edge is held equal across instruments, matching how EXP-003 pooled instruments. This closed-form value makes the candidate's expected all-eligible-row net edge equal the target under the harness per-active-bar cost model (`strategy_return_bps` charges `cost_bps` to every active bar). Implementations may inject the drift by reusing the frozen `plant_positive_edge(returns, states, net_edge_bps=delta_bps, cost_bps=0.0)`.
- **Null generation**: Use the same candidate construction with no planted drift. Use two null views: unmodified real returns with candidate independent of returns, and bar-permuted returns with the same candidate.
- **Active-bar denominator**: Eligible rows are domain bars with a defined `t -> t+1` real Close-to-Close return. Active bars are rows where `C_t != 0`. Report active rate as `active_bars / eligible_rows` on train and test. Referee effects remain the frozen harness all-eligible-row mean so EXP-005 composes with EXP-003.
- **TPR/FPR denominators**: FPR denominator is null draw verdict count per domain/referee/alpha. TPR denominator is positive draw verdict count per domain/referee/alpha/target-edge. Pooled-domain summaries pool the four instruments, matching EXP-003; per-instrument summaries are secondary masking checks.
- **Draw counts**: 500 positive draws per edge/instrument/domain; 500 null draws per null generator/instrument/domain; 1000 inner block-bootstrap resamples per verdict.
- **Referees**: Frozen Phase 001 minimal baseline and frozen Phase 001 5-check gate stack. The gate stack is the headline referee; the minimal baseline is a diagnostic reference.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC.
- **Dependencies**: EXP-001 `run_metadata.json` must record `overall_status == "PASS"`. EXP-003 is a measurement run that records `overall_status == "COMPLETE"` (not `"PASS"`), so its gate is **artifact-based**, mirroring EXP-004: require EXP-003 `run_metadata.json` present with `overall_status == "COMPLETE"` and `mde_summary.csv` containing finite gate-stack MDE rows at `alpha=0.05`. The dependency gate must **not** require `EXP-003 overall_status == "PASS"`.
- **Frozen-harness reuse**: The realistic-candidate construction (latent state, noisy candidate, expected-edge calibration) lives in an experiment-local helper under `python/experiments/EXP-005/code/`. `xen.referee_calibration` is imported and **reused unchanged** (design D-reuse); any edit to it would trigger P0/temporal-integrity re-validation before EXP-005 may run, so no shared `python/src/xen` module is modified unless governance requires it.
- **Pre-execution confirmation**: Before EXP-005 execution, Stage 4 governance must record operator confirmation or a pre-results design amendment for all Phase 002 operator-confirmation items in `design.md`: `D-nearMDE`, `D-lenientL5`, and `D-loss`. No Phase 002 measurement may be read before that confirmation.
- **Time range**: Full dataset with nested chronological split per instrument file. First 70% = analysis set; final 30% = global holdout and is never used.
- **Global holdout**: The final 30% of each source file must not be loaded, inspected, or used in any capacity.
- **Look-ahead bias prevention**: Candidate states at time `t` are generated without future data and evaluated only against `t -> t+1` real Close-to-Close returns. Bootstrap block length is estimated on train returns only.
- **Real-price outcome discipline**: All candidate outcomes use real domain `Close` prices plus the predeclared synthetic drift for the known-positive substrate. No synthetic chart prices are in scope.
- **Exclusions**: Chart-type signals, real strategy tuning, loss-function tuning, referee redesign, threshold sweeping, lenient-L5 variants, walk-forward validation, stop/target logic, bid/ask spread estimation, and any use of Phase 002 outcomes to alter the candidate construction.

## Success / Failure Criteria

- **Evidence FOR**: For each reportable domain at `alpha0=0.05`, pooled-domain FPR is `<= 0.05` with Wilson half-width `<= 0.03`, and pooled-domain TPR is `>= 0.80` with Wilson half-width `<= 0.05` for the target edge equal to `1.0 x` that domain's EXP-003 gate MDE. Higher grid points must not show a material TPR reversal unexplained by Monte Carlo precision. Candidate active rate must remain within `0.80 +/- 0.02` overall and match rate within `0.75 +/- 0.02` among active bars.
- **Evidence AGAINST**: With usable precision, pooled-domain FPR exceeds `alpha0`, or pooled-domain TPR is below `0.80` at `1.0 x` MDE despite the candidate construction sanity checks passing.
- **Inconclusive**: EXP-003 MDE artifacts are missing/imprecise, the candidate construction sanity checks fail, or effective sample / Wilson precision misses the target, especially on 4h or per-instrument breakdowns.

## Complexity Budget

- Max statistical tests: 4
- Max visualisations: 5
- Max new code modules: 1 experiment-local helper module at most; no shared `python/src/xen` module changes unless governance requires them

## Data Requirements

Load only the first 70% chronological analysis slice from each 1-minute source file. Resample domains after holdout exclusion using the existing EXP-003 harness helpers. Use the same shared `CloseTime` split boundary inherited from the 1-minute source for every domain.

Required upstream artifacts:

- `python/experiments/EXP-001/results/run_metadata.json`
- `python/experiments/EXP-003/results/run_metadata.json`
- `python/experiments/EXP-003/results/mde_summary.csv`

Primary expected outputs:

- `realistic_candidate_draws.csv`
- `candidate_sanity.csv`
- `fpr_summary.csv`
- `tpr_summary.csv`
- `detection_summary.csv`
- `per_instrument_detection.csv`
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

## Suggested Direction

Treat this as a keystone closure experiment, not a tuning run: measure whether the frozen gate detects the predeclared realistic candidate at and above the EXP-003 MDE, and classify non-detection as a real structural-blindness finding rather than adjusting the candidate or referee.
