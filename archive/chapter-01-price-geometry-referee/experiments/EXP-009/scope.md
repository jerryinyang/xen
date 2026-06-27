# Experiment: EXP-009 - Broadened Untuned Strategy Effect-Size Distribution

## Hypothesis

This is an **exploratory characterization** experiment (design §4: measurement
only, no pass/fail): where do the net (cost-applied) and gross effect sizes of a
**broadened set of untuned, fixed-parameter simple strategies** sit relative to
each domain's EXP-003 gate-stack MDE, and how is that effect-size distribution
shaped across instruments and strategy families?

EXP-004 anchored two untuned strategies (Donchian 20, MA 20/50) and found them at
a near-zero null/lower anchor below every domain MDE. EXP-009 widens the strategy
set to characterize the **distribution** of where simple untuned edges actually
live relative to the calibrated MDE map, without tuning anything.

## Question

When a canonical breadth of untuned simple strategies is measured on real prices,
what does the distribution of their net effect sizes look like relative to each
domain's gate MDE — are they uniformly below it (consistent with EXP-004), or do
some families/instruments produce effects at or above the MDE?

## Scope Boundaries

- **Data Views**: Base 1-minute time bars resampled to 5m, 1h, and 4h OHLC
  domains via the frozen `xen.referee_calibration` harness
  (`build_domain_frames`). No chart-type views are in scope.
- **Strategy set (predeclared, frozen before any result is read)**: A canonical
  breadth of fixed, untuned, standalone directional strategies. Positions are in
  `{-1, 0, +1}`, known at bar `t` from information available at or before `t`,
  and evaluated on `t -> t+1` real Close-to-Close returns. All parameters are
  fixed defaults and are **never tuned**:
  1. **Donchian(20) breakout** — reuse harness `donchian_breakout_positions(lookback=20)`. +1 on close above the prior-20 high, -1 below the prior-20 low, else flat. (trend)
  2. **MA(20/50) crossover** — reuse harness `ma_crossover_positions(fast=20, slow=50)`. +1 when fast MA > slow MA at `t`, -1 when below, else flat. (trend)
  3. **RSI(14) mean-reversion** — Wilder RSI on closes up to `t`; +1 when `RSI_t < 30`, -1 when `RSI_t > 70`, else flat. (mean-reversion)
  4. **Bollinger(20, 2.0) breakout** — 20-period SMA of close ± 2.0 population std (ddof=0) of close, all from closes up to and including `t`; +1 when `close_t >` upper band, -1 when `<` lower band, else flat. (trend / breakout)
  5. **MACD(12, 26, 9) crossover** — `MACD = EMA12(close) - EMA26(close)`, `signal = EMA9(MACD)`, all causal recursive EMAs seeded by the first available value; +1 when `MACD_t > signal_t`, -1 when below, else flat. (trend)
  6. **ROC(20) momentum** — `ROC_t = close_t / close_{t-20} - 1`; +1 when `ROC_t > 0`, -1 when `< 0`, else flat. (momentum)
  Warmup rows with insufficient history are flat (position 0); NaN is handled
  explicitly and never propagated into a position or return.
- **Referee evaluation**: For each strategy/instrument/domain, compute both the
  frozen minimal baseline (gross effect, no cost gate) and the frozen 5-check
  gate stack (net-of-cost effect) using `xen.referee_calibration.evaluate_referees`
  **unchanged**, at the alpha grid `{0.10, 0.05, 0.01}` with primary `alpha0=0.05`,
  1000 inner block-bootstrap resamples per verdict, the shared 1-minute
  `CloseTime` train/test boundary per `domain_split_index`, and the frozen
  per-instrument/per-domain costs.
- **Effect-size location**: For each cell, report the gross minimal-baseline
  effect with its block-bootstrap CI, the net gate-stack effect with its CI, and
  the cell's position relative to the EXP-003 **pooled domain** gate MDE (read at
  runtime from EXP-003 `mde_summary.csv`, rows `referee=gate_stack, alpha=0.05`;
  expected 5m=1.0, 1h=4.0, 4h=12.0 bps, asserted finite) and minimal-baseline MDE.
  Classify each net effect as `below_MDE`, `near_MDE` (within the EXP-003 grid
  uncertainty of the MDE), or `at_or_above_MDE`.
- **Distribution characterization**: Summarize the net-effect-size distribution
  per domain across the strategy x instrument cells (location and spread, e.g.
  median and percentile range), and per strategy family across instruments.
- **Parameters**: Domains `{5m, 1h, 4h}`; coverage 5m strict, 1h/4h
  `min_coverage=0.90` (frozen D-invariants); alpha grid `{0.10, 0.05, 0.01}`,
  primary `alpha0=0.05`; strategy parameters as fixed above; 1000 bootstrap
  resamples/verdict.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC.
- **Dependencies**: EXP-003 `run_metadata.json` present with
  `overall_status == "COMPLETE"` and finite gate-stack MDE rows in
  `mde_summary.csv` (artifact-based gate, mirroring EXP-004/EXP-005); EXP-004
  SUPPORTED (its candidate-position + `evaluate_referees` pattern is reused). The
  EXP-008 per-instrument MDE is **optional context only**, not a dependency
  (EXP-009 is methodologically independent of EXP-008 per design §8); if absent,
  comparison uses the pooled domain MDE only.
- **Time range**: Full dataset with nested chronological split per instrument
  file; first 70% = analysis set (70/30 train/test within it); final 30% = global
  holdout and is never used.
- **Global holdout**: The final 30% of each source file must not be loaded,
  inspected, or used in any capacity. Domains are built only from the first-70%
  1-minute analysis slice.
- **Look-ahead bias prevention**: Every strategy position at `t` uses only closes
  / highs / lows available at or before `t` and is evaluated against the
  `t -> t+1` real Close-to-Close return. Bootstrap block length is estimated on
  train returns only, as in the frozen harness.
- **Real-price outcome discipline**: All strategy returns are computed from real
  domain `Close` prices via the frozen harness cost model. No Heiken Ashi or
  Renko synthetic prices are in scope.
- **Exclusions**: Parameter tuning or optimization of any strategy; strategy
  improvement, ensembling, or selection; stop/target/risk logic; chart-type
  signals; per-instrument MDE estimation (that is EXP-008); split-protocol
  variation (that is EXP-010); loss-function selection or operating-point
  adoption (EXP-011); referee redesign or any change to the frozen harness; the
  global holdout; and any pass/fail qualification verdict on individual
  strategies (this is a distribution-characterization experiment).

## Success / Failure Criteria

This is an exploratory measurement; "success" is producing the scoped
distribution with usable precision, not a hypothesis verdict.

- **Evidence FOR (measurement delivered)**: For every reportable
  strategy x instrument x domain cell at `alpha0`, the gross and net effect sizes
  with block-bootstrap CIs are produced and located relative to the domain MDE,
  and the per-domain and per-family effect-size distributions are characterized.
- **Evidence AGAINST (measurement not deliverable)**: Required EXP-003 MDE
  artifacts are missing or non-finite, or the harness cannot evaluate the
  strategies on the analysis slice without changing leg logic, sample membership,
  or denominators.
- **Inconclusive (per cell)**: A cell's effective sample misses the D-prec
  precision target so its effect-size CI is uninformative — expected most likely
  on 4h. Reported as under-powered with honest CIs, never forced to a value.

## Complexity Budget

- Max statistical tests: 3 (block-bootstrap effect CIs; effect-vs-MDE location
  classification; distribution summary)
- Max visualisations: 5
- Max new code modules: 1 (an experiment-local helper under
  `python/experiments/EXP-009/code/` holding the four new position generators —
  RSI, Bollinger, MACD, ROC — that are not already in the harness; Donchian and
  MA crossover are reused from `xen.referee_calibration` unchanged; no shared
  `python/src/xen` module is modified, so no P0/temporal re-validation is
  triggered)

## Data Requirements

Load only the first 70% chronological analysis slice from each 1-minute source
file via the frozen harness `load_analysis_data`, build the `{5m, 1h, 4h}`
domains via `build_domain_frames`, derive `t -> t+1` returns and the shared split
index via `next_log_returns_from_bars` / `domain_split_index`, compute each
strategy's positions aligned to those returns, and evaluate both referees via
`evaluate_referees`.

Required upstream artifacts:

- `python/experiments/EXP-003/results/run_metadata.json`
- `python/experiments/EXP-003/results/mde_summary.csv`
- `python/experiments/EXP-004/results/run_metadata.json` (consistency anchor)

Primary expected outputs:

- `strategy_effects.csv` (gross + net effect, CIs, effective N, per cell)
- `strategy_verdicts.csv` (both referees, all alphas)
- `effect_vs_mde.csv` (location relative to domain MDE, with classification)
- `effect_distribution_summary.csv` (per-domain and per-family distribution)
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

Treat this as a distribution measurement, not a strategy hunt. Report where the
untuned effect sizes actually land relative to the MDE map and resist tuning any
strategy toward the MDE. If the broadened set still sits below every domain MDE
(as EXP-004 found for the two-strategy anchor), say so as a strengthening of the
null/lower anchor; if some family/instrument lands at or above an MDE, flag it as
a candidate worth a dedicated future experiment, not a result to act on here.
