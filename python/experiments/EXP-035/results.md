# Results: Experiment EXP-035

## Summary

The Market Bias (CEREBR) chart-timeframe port is **deterministic** and its two EMA seedings **converge** to an identical state-label sequence on every instrument and timeframe, so the port itself clears the determinism and warmup gates everywhere. The descriptor clears the Phase 005 episode-readiness gate, but **only marginally**: the sole `(timeframe, aggregation)` cell with `>= 2` distinct passing instruments in both segments is `1h/tolerant` (`BTCUSD`, `USTEC`). Under the strict aggregation that EXP-034 selected as canonical for Prior-Range Location, only `BTCUSD` passes `1h` — a single-instrument (inconclusive) result. Every `4h` cell and both FX/gold instruments (`EURUSD`, `XAUUSD`) fail the independent-episode floor. The mechanical verdict is **readiness-pass**, but it is conditional on an aggregation rule the phase has not yet locked.

The port claims **deterministic re-implementation of the published Pine v5 formula only** — no exported TradingView reference series is present, so Pine-equivalence is not established and any later negative Market Bias return result must carry the unverified-fidelity caveat.

## Detailed Findings

### The Port Is Deterministic and the Warmup Converges Everywhere

- **Observation**: All 32 rows have `Check1Determinism=True` and `Check2WarmupConverged=True`.
- **Evidence**: `results/readiness_table.csv` (`Check1`/`Check2` columns); `plots/01_determinism_warmup.png`. Convergence index `WConverge` ranges `100–405`, floored at `300` to give `W` in `[300, 405]`.
- **Interpretation**: The `xhaopen[1]` recursion and Pine SMA-vs-cold seedings reduce to the same state labels after a bounded, predeclared warmup, so the readiness counts that follow come from a deterministic, warmed-up series. This holds the formula fidelity question separate from the count-eligibility question.

### Episode Readiness Passes Only on `1h/tolerant`, and Only for Crypto and the Index

- **Observation**: `Check4EpisodeFloor` is the binding constraint, failing on 25 of 32 rows. The only cells passing both train and test are `BTCUSD 1h` (strict and tolerant) and `USTEC 1h tolerant`.
- **Evidence**: `results/verdict.json` (`passes_readiness=true`, `1h/tolerant=[BTCUSD, USTEC]`, `1h/strict=[BTCUSD]`, both `4h` cells empty); `plots/03_sign_episode_grid.png`.
- **Interpretation**: Market Bias generates enough independent sign-state episodes to be testable only on the higher-turnover instruments at the faster timeframe. The descriptor is count-eligible, but its eligibility is narrow.

### `4h` Fails Entirely on Episode Counts

- **Observation**: Every `4h` cell fails the episode floor; train sign-episode counts are `4–9` per state versus the `30` floor.
- **Evidence**: `readiness_table.csv` `4h` rows (`EpBull`/`EpBear`), e.g. `USTEC 4h strict Train` `EpBull=5, EpBear=4`.
- **Interpretation**: The stacked `EMA(100)→HA→EMA(100)` smoothing produces very long, persistent states (median episode lengths `100–430` bars). At `4h` the analysis window simply does not contain enough state flips to count. This was anticipated in the pre-execution review and is the intended discriminator, not a defect.

### FX and Gold Fall Just Short at `1h`

- **Observation**: `EURUSD` and `XAUUSD` fail the `1h` episode floor under both aggregations; train sign-episode counts cluster at `24–28` against the `30` floor.
- **Evidence**: e.g. `EURUSD 1h strict Train` `EpBull=25, EpBear=25`; `XAUUSD 1h tolerant Train` `EpBull=28, EpBear=27`.
- **Interpretation**: The smoothing produces fewer state transitions on the lower-volatility FX/metal series, so even at `1h` they miss the independent-episode floor. Readiness is concentrated in `BTCUSD` and `USTEC`.

### No State Collapse Anywhere

- **Observation**: `DominantShare` ranges `0.501–0.774`; no cell approaches the `0.95` collapse threshold.
- **Evidence**: `readiness_table.csv` `DominantShare` column; `plots/04_persistence_fourway.png`. The most imbalanced cells are `XAUUSD 4h` (`~0.77` bull-heavy) and `USTEC 4h` (`~0.74–0.76`).
- **Interpretation**: Both sign states remain materially populated; the readiness shortfall is about *too few transitions*, not *one state swallowing the series*.

### Aggregation Dependence Is the Decision the Reflection Inherits

- **Observation**: The readiness pass exists only because tolerant `0.90` aggregation supplies enough extra `1h` bars to push `USTEC` over the episode floor and to keep `BTCUSD` over it. Under strict, `1h` has one passing instrument.
- **Evidence**: `1h/tolerant=[BTCUSD, USTEC]` vs `1h/strict=[BTCUSD]` in `verdict.json`.
- **Interpretation**: EXP-034 selected **strict** as canonical for Prior-Range Location on feature-stability grounds. Market Bias only clears readiness under **tolerant**. If the mid-phase reflection locks a single phase-wide strict rule, Market Bias becomes inconclusive (one instrument). The scope predeclared that the binding canonical choice is made at the reflection (`scope.md` lines 23, 49), so this is the legitimate, predeclared outcome — but it forces a phase-level coherence decision rather than settling one.

## Hypothesis Verdict

**SUPPORTED (conditional).**

The hypothesis — deterministic reproduction of the published formula plus adequate independent-episode counts on `>= 2` distinct instruments at `>= 1` timeframe under an admissible aggregation — is met: the port is deterministic and convergent everywhere, and `1h/tolerant` passes on `BTCUSD` and `USTEC` in both segments. The support is conditional on tolerant aggregation and is narrow (one cell, two of four instruments, sign-only axis). It is materially weaker than EXP-034's all-instrument/both-timeframe strict pass.

## Limitations

- **Readiness-only.** No forward return, control-adjusted differentiation, FE/AE, hit rate, or P&L was computed. This says Market Bias *can* be return-tested on `1h/tolerant`, not that it carries edge.
- **Aggregation-dependent readiness.** The pass disappears under strict aggregation. The result does not by itself justify adopting tolerant aggregation phase-wide; EXP-034 found tolerant windows feature-perturbing for a different descriptor.
- **Instrument concentration.** Only `BTCUSD` and `USTEC` reach the episode floor; `EURUSD` and `XAUUSD` do not. Any return test inherits this two-instrument base, which is the minimum the gate allows.
- **Unverified fidelity.** No TradingView reference series exists, so the port is a deterministic re-implementation, not a verified Pine match. A single exported `osc_bias`/state series under `docs/planning/` would let a rerun report bar-for-bar deviation and lift this caveat.
- **Four-way axis not gated.** Four-way states are reported as a secondary diagnostic only; they are sparser than sign-only and were not used for the verdict.

## Alternative Explanations

- The narrow readiness may reflect the heavy double-`EMA(100)` smoothing producing structurally rare transitions rather than any market-state property worth trading. A return test must show the count-eligible states differentiate executable returns against a neutral/sign-flip control before Market Bias earns continued attention.
- `BTCUSD`/`USTEC` passing while `EURUSD`/`XAUUSD` fail may simply track realized volatility/turnover (more transitions per unit time) rather than anything specific to the Market Bias construction.

## Recommended Next Steps

1. Take the aggregation-canonicity tension to the **mid-phase reflection** as an explicit decision: a phase-wide strict rule demotes Market Bias to inconclusive; admitting tolerant for this descriptor revives it on two instruments.
2. If the reflection authorizes a Market Bias return test, scope it on `1h/tolerant`, `BTCUSD` + `USTEC`, sign-only states, and carry the deterministic-only fidelity caveat into every conclusion.
3. Before any return test, obtain an exported TradingView reference series for at least one instrument to convert the fidelity claim from "deterministic re-implementation" to a verified bar-for-bar match.
