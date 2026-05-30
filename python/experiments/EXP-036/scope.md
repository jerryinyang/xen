# Experiment: EXP-036 — Prior-Range Location Executable State-Aligned Return Test

## Hypothesis

This is the first Phase 005 **return test**. It states the locked primary edge metric as a falsifiable claim for the highest-priority readiness-passing directional descriptor:

> On holdout-excluded `1h` and `4h` real-price bars (strict aggregation, the canonical Phase 005 rule fixed at the mid-phase reflection), the Prior-Range Location descriptor's **executable direction-adjusted next-bar log return** — top bucket (`>= 0.80`) traded long, bottom bucket (`<= 0.20`) traded short, entered at the next same-timeframe bar open and exited at that bar's close on real OHLC — exceeds, in the state's traded direction, (a) the measured mean return of its own neutral middle bucket **and** (b) a matched same-timeframe prior-bar-momentum-sign control, with episode-level bootstrap confidence intervals on the differences excluding zero and train/test sign preservation on **at least two distinct instruments**.

The continuation framing (top → long, bottom → short) is locked by `design.md` Candidate 1; the reversal framing is prohibited (refuted in EXP-015, EXP-030). Passing against the neutral state but **not** the matched control is recorded as descriptive state differentiation, not an edge candidate (Gate 4).

This experiment can produce candidate-manifest-eligible language only through the **next-bar primary**. The predeclared secondary 4-bar horizon cannot manufacture an edge claim; it exists only so a single hostile horizon cannot be reported as thesis-level refutation (`design.md` §"Predeclared secondary holding horizon").

## Question

On `1h`/`4h` strict-aggregated real bars, does trading the Prior-Range Location extreme states in their predeclared continuation direction earn a higher executable next-bar return than both the measured neutral middle-bucket state and a prior-bar-momentum-sign control, replicated across train and test on at least two distinct instruments? And at the single predeclared 4-bar hold, does the same contrast hold?

## Scope Boundaries

- **Data Views**: 1-minute time bars from `data/timebars/`, deterministically aggregated to `1h` (60-minute) and `4h` (240-minute) clock-aligned OHLC via `python/src/bar_aggregator.aggregate_ohlc` with `min_coverage=None` (**strict** — the canonical Phase 005 rule confirmed at the mid-phase reflection). No tolerant aggregation. No chart-type inputs (no Line Break, Renko, Heiken Ashi). No 1-minute feature analysis; the descriptor lives only on the aggregated higher-timeframe bars.
- **Parameters** (all predeclared, frozen before implementation, never tuned on any result, identical to the readiness definition in EXP-034):
  - Prior-range lookback: `20` completed same-timeframe bars; `prior_high = rolling_max(High, 20).shift(1)`, `prior_low = rolling_min(Low, 20).shift(1)`.
  - `range_location = (Close − prior_low) / (prior_high − prior_low)`; outside-range flag on `raw < 0 | raw > 1`; clipped to `[0,1]` for bucketing; bars with `prior_high == prior_low` flagged degenerate and excluded.
  - Bucket thresholds: bottom `<= 0.20`, middle `(0.20, 0.80)`, top `>= 0.80`. Fixed thresholds, **not** data-driven terciles.
  - Directional implication (locked, continuation): `d = +1` (top, long), `d = −1` (bottom, short), `d = 0` (middle, flat/no position).
  - Timeframes: `1h` and `4h`. `1d` out of scope (no daily aggregator; deferred per design).
  - **Primary executable return**: `r_i = ln(Close_{i+1} / Open_{i+1})`, where bar `i+1` is the next row-adjacent bar in the strict-aggregated series (descriptor observed at bar-`i` close; earliest entry next bar open; exit that bar's close).
  - **Secondary executable return (single predeclared horizon, fixed `4`)**: `r4_i = ln(Close_{i+4} / Open_{i+1})` — enter next bar open, exit close of the 4th subsequent same-timeframe bar. No other horizon is computed.
  - **Matched control**: prior-bar momentum sign `c_i = sign(Close_i − Close_{i−1})`, with the same executable next-bar and 4-bar return convention; `c_i = 0` (flat bar) bars contribute no control position.
  - Bootstrap: `10,000` resamples, seed `42`, **episode-level resampling** (resample whole independent state episodes with replacement; see Inference unit). Two-sided `95%` CIs.
  - Inference unit: independent state episodes — maximal runs of consecutive same-bucket bars (the EXP-034 episode definition). Naive row bootstrap is diagnostic only.
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC. All four are eligible at both `1h` and `4h` (EXP-034: strict readiness passed on all four at both timeframes). The replication unit is the **distinct instrument** (instrument is the independence unit; `1h` and `4h` of the same instrument do not count as independent replication).
- **Time range**: Full dataset per instrument with the nested chronological split applied to the **1-minute series before aggregation**. First 70% of the 1-minute series is the analysis set; after strict aggregation the higher-timeframe series is split chronologically 70/30 into train/test. The final 30% is the global holdout and is never loaded, inspected, aggregated, or used.
- **Global holdout**: Excluded before any aggregation or feature computation via `python/src/ict_timebar.load_analysis_timebars` (first-70% lazy slice). The full 1-minute dataset must never be aggregated and re-split.
- **Look-ahead bias prevention**: The descriptor at bar `i` uses bars `<= i−1` for the prior range plus the bar-`i` close (all known at bar-`i` close). The return uses only bars `>= i+1`. There is therefore **no overlap** between the information set defining the state and the bars producing the return. Train/test assignment is by each bar's own `CloseTime` against the per-instrument-timeframe train cutoff, never by bar index. The control `c_i` uses only `Close_i` and `Close_{i−1}` (both `<= i`).
- **Real-price outcome discipline**: All returns, and any secondary FE/AE diagnostic, are computed from the **aggregated real OHLC** (`Open/High/Low/Close`). No Heiken Ashi or Renko construction price appears anywhere. There is no synthetic-price path in this experiment.
- **Exclusions**:
  - No timeframe other than `1h`/`4h`; no `1d`.
  - No holding horizon other than the next-bar primary and the single fixed 4-bar secondary. No horizon sweep.
  - No bucket-boundary, lookback, warmup, or coverage-tolerance variation (a sweep would be test-selection; Gate 6).
  - No reversal framing; continuation is locked.
  - No position sizing, stops, targets, or compounding — the metric is a single per-observation log return, not a P&L curve. Continuous sizing must never be used to rescue an uninformative descriptor (`design.md` complexity budget).
  - No transaction-cost, slippage, or spread modeling — cost stress belongs to EXP-038, not here.
  - No other descriptor (Market Bias, Compression, Renko).
  - No global-holdout access.
  - No multitimeframe combination (Gate 3); each timeframe is tested independently.

## Success / Failure Criteria

All criteria are predeclared and evaluated per `(instrument, timeframe)` cell, separately for the **vs-neutral** and **vs-control** contrasts, and separately for the **next-bar primary** and the **4-bar secondary**. Define, over the extreme-state (traded) bars in a segment:

- **Descriptor state-aligned return** `S^desc_i = d_i · r_i` over the extreme (traded) bars.
- **Neutral-baseline drift** `μ_mid = mean(r | middle-bucket bars)` — the *measured* mean next-bar return of the descriptor's own neutral middle state in the same `(cell, segment, horizon)`. This is the locked neutral baseline: the middle bucket **itself**, **not** a zero/flat-cash baseline (`design.md` §"Locked Primary Edge Metric"; mid-phase reflection §3). The middle bucket is not traded (`d = 0`), but its return distribution is measured to serve as the baseline.
- **Vs-neutral contrast** `Δ_neutral = mean( d_i · (r_i − μ_mid) | extreme bars )` — the direction-adjusted excess return of the extreme states **over the measured middle-bucket drift**. Equivalently, the pooled combination of the two per-side contrasts `E[r | top] − μ_mid` (long side, expect `> 0`) and `μ_mid − E[r | bottom]` (short side, expect `> 0`). Under the null that the extreme buckets do **not** differ from the middle bucket (`E[r | top] = E[r | bottom] = μ_mid`), `Δ_neutral = 0` by construction; the test is whether its CI excludes `0` positively. Because `μ_mid` is itself an estimate, the CI uses a **two-sample episode bootstrap** (resample extreme episodes and middle episodes independently, recomputing `μ_mid` and `Δ_neutral` each draw). This is an absolute return difference against measured middle observations — never a percentage-over-zero comparison, and never against flat cash.
- **Vs-control contrast** `Δ_control = mean(S^desc_i − S^ctrl_i | extreme bars)`, where `S^ctrl_i = c_i · r_i` is evaluated on the **same extreme-state bars** (paired). The test is whether `Δ_control`'s episode-bootstrap CI excludes `0` positively — i.e., on the bars the descriptor trades, its direction earns more than trading the prior-bar momentum sign would. (The shared ambient drift on those bars applies to both legs; the contrast isolates the direction choice, so no `μ_mid` term enters here.)
- **Vs-control contrast** `Δ_control = mean(S^desc_i − S^ctrl_i | extreme bars)`, where `S^ctrl_i = c_i · r_i` is evaluated on the **same extreme-state bars** (paired). The test is whether `Δ_control`'s episode-bootstrap CI excludes `0` positively — i.e., on the bars the descriptor trades, its direction earns more than trading the prior-bar momentum sign would.

### Primary (next-bar) verdict — predeclared

- **Evidence FOR (edge candidate)**: on `>= 2` distinct instruments at `>= 1` timeframe, **both** `Δ_neutral` and `Δ_control` are positive with the test-segment `95%` CI excluding zero, **and** the train-segment point estimate has the **same sign** (positive) as the test estimate (train/test sign preservation). A surviving descriptor advances to EXP-038 robustness before any candidate-manifest language.
- **State-differentiation-only (not an edge candidate)**: `Δ_neutral` passes the above on `>= 2` distinct instruments but `Δ_control` does not. Recorded as descriptive state differentiation (the extreme states' returns differ from the middle/neutral bucket but the descriptor does not beat trading recent momentum). Gate 4 blocks edge-candidate language.
- **Evidence AGAINST (refutation of this descriptor)**: fewer than `2` distinct instruments show train/test sign-preserving positive `Δ_control` at any timeframe — i.e., the descriptor fails the matched-control gate. Combined with a failing 4-bar secondary (below), this is a clean refutation of Prior-Range Location as a state-descriptor edge, holdout intact.
- **Inconclusive**: exactly one instrument passes both contrasts, or eligible counts collapse for a contrast (an extreme state or its episodes fall below the EXP-034-confirmed floors after the return-eligibility filter), so the `>= 2`-instrument rule cannot be adjudicated.

### Secondary (4-bar) gate semantics — predeclared, asymmetric

- The 4-bar horizon uses identical machinery (`Δ_neutral`, `Δ_control`, same floors, same `>= 2`-instrument sign-preservation rule).
- It **cannot** produce edge-candidate or candidate-manifest language; only the next-bar primary can.
- If the next-bar primary fails its `Δ_control` gate **but** the 4-bar secondary passes both `Δ_neutral` and `Δ_control` on `>= 2` distinct instruments, the result is recorded as **horizon-dependent state differentiation**, which reopens the thesis at the longer horizon through a new predeclared experiment and is explicitly **not** thesis refutation.
- Failing both horizons against the matched control is the clean refutation of this descriptor.

### Return-eligibility filter (predeclared)

A descriptor observation at bar `i` is **return-eligible** for the next-bar primary only if bar `i+1` exists in the strict-aggregated segment (last bar of each segment has no next bar and is dropped); for the 4-bar secondary, bars `i+1 … i+4` must all exist. The inter-bar clock gap between bar `i` and bar `i+1` (and across the 4-bar window) is reported as an **executability/staleness diagnostic**; gap-spanning entries are retained because entering at the next formed bar is executable, and the gap delays entry rather than entering the single-bar open-to-close return. Robustness to excluding gap-spanning entries is deferred to EXP-038. The post-filter eligible row and episode counts must still clear the EXP-034 floors (`>= 100` train rows / `>= 50` test rows / `>= 30` train episodes / `>= 15` test episodes) for **each traded extreme state and for the middle/neutral state** (the middle bucket is the measured `μ_mid` baseline for the vs-neutral contrast, so its counts must clear the floors for that contrast to be adjudicated). A cell is adjudicated FOR/AGAINST on a contrast only when every state that contrast depends on clears the floor; cells failing after filtering are Inconclusive for that contrast.

### Mathematical Attainability

`Δ_neutral` and `Δ_control` are unbounded real differences with two-sided CIs; positive, negative, and zero-spanning outcomes are all reachable, so no criterion is mathematically unattainable and none compares against a zero denominator. `Δ_neutral` is zero under the null of no differentiation from the middle bucket, so a pass requires genuine separation from the measured neutral state, not mere ambient drift. EXP-034 confirmed the extreme buckets clear the row/episode floors on all four instruments at both timeframes under strict aggregation, and the middle bucket is the largest by construction (it spans `(0.20, 0.80)`), so the `μ_mid` baseline trivially clears the floor wherever the extremes do; the return-eligibility filter can only reduce counts modestly (drops the last bar per segment and requires forward bars), so the floors remain plausibly attainable — this is verified, not assumed, in the eligible-count check above.

## Prerequisites and Sequencing

Authorized by the Phase 005 mid-phase reflection (`docs/experiments-docs/checkpoints/2026-05-28-005-htf-state-descriptor-differentiation/mid-phase-reflection.md`, §2 and §4): EXP-036 is the only return test authorized at this gate. EXP-037 was not created (Market Bias failed readiness under canonical strict aggregation). EXP-038 (robustness) opens only if EXP-036 produces a surviving descriptor.

Reuses, unchanged:
- `python/src/bar_aggregator.aggregate_ohlc` (strict, `min_coverage=None`).
- `python/src/ict_timebar.load_analysis_timebars`, `train_cutoff_time`, `INSTRUMENTS`.
- The Prior-Range Location feature construction validated in EXP-034.
- Bootstrap convention `numpy.random.default_rng(42)`; existing CI helpers (`signal_quality.bootstrap_means` / `bootstrap_diff_ci`, `timeframe_replication.bootstrap_mean_ci`) as references for the per-mean and paired-difference CIs, wrapped by an inline episode-resampling routine (episodes, not rows, are the resampling unit).

## Complexity Budget

- **Max statistical test families: 2** (design allows ≤ 3). (1) Episode-level bootstrap CI on `Δ_neutral` (per-mean). (2) Episode-level paired bootstrap CI on `Δ_control` (paired difference). The same two families are applied to the 4-bar secondary — they are the same families re-applied to a second horizon, not new families. No parametric test.
- **Max primary visualisations: 4.**
- **Max new reusable modules: 0.** All `python/src` modules are reused unchanged; the episode-resampling wrapper lives in `code/run_experiment.py`, not in `python/src`.

## Data Requirements

For each instrument and timeframe (`60`, `240` minutes), strict aggregation only:

1. Load holdout-excluded 1-minute analysis frame via `load_analysis_timebars(DATA_DIR, instrument)` (first 70%).
2. Aggregate to the timeframe via `aggregate_ohlc(frame_1m, period_minutes=tf, min_coverage=None)`.
3. Apply the nested 70/30 chronological train/test split; record the per-cell train cutoff `CloseTime` via `train_cutoff_time`.
4. Construct the Prior-Range Location feature exactly as in EXP-034 (shifted 20-bar range, clip, outside-range flag, degenerate exclusion, buckets, episode labels).
5. Compute next-bar `r_i` and 4-bar `r4_i` from aggregated real OHLC; apply the return-eligibility filter; flag inter-bar gap durations.
6. Compute `d_i` (descriptor direction) and `c_i` (control momentum sign); form `S^desc`, `S^ctrl` on extreme bars.
7. Per cell and segment: eligible row/episode counts per traded state; `Δ_neutral`, `Δ_control` point estimates; episode-level bootstrap CIs.
8. Apply the predeclared primary and secondary verdicts mechanically; record train/test sign preservation and the per-timeframe distinct-instrument pass counts.

### Standard Loading Pattern

```python
import sys
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PYTHON_ROOT / "src"))

from ict_timebar import INSTRUMENTS, load_analysis_timebars, train_cutoff_time
from bar_aggregator import aggregate_ohlc

DATA_DIR = PYTHON_ROOT.parent / "data"

for instrument in INSTRUMENTS:
    loaded = load_analysis_timebars(DATA_DIR, instrument)  # first 70% only
    bars_1m = loaded.frame
    bars_tf = aggregate_ohlc(bars_1m, period_minutes=60, min_coverage=None)  # strict, canonical
    # holdout exclusion is complete; never re-scan the full file without the slice
```

## Suggested Direction

Report eligible row/episode counts for every state (top, bottom, **and middle** — the middle is the `μ_mid` baseline, not a discardable category) **before** any return estimate, so a count-driven Inconclusive is visible before effect sizes are read (mirrors EXP-034's coverage-first discipline). Present the three buckets' mean returns with the middle drift `μ_mid` drawn as the baseline line (not a zero line), then `Δ_neutral` (excess over `μ_mid`) and `Δ_control` with CIs per cell, then the train/test sign-preservation grid (the replication view that drives the verdict), then the 4-bar secondary panel. Keep the `Δ_control` comparison paired on the descriptor's own traded bars — the central scientific question is whether range-location adds anything beyond "trade in the direction of recent momentum." The verdict is mechanical: FOR requires train/test sign-preserving positive `Δ_neutral` **and** `Δ_control` on `>= 2` distinct instruments via the next-bar primary; anything weaker is state-differentiation-only, refutation, or inconclusive per the predeclared table.
