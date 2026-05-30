# Experiment: EXP-034 — Prior-Range Location Readiness and Shared Aggregation-Coverage Rule

## Hypothesis

This is a **readiness experiment**, not a return test. It states a falsifiable *count-eligibility* claim, not an edge claim:

> On `1h` and `4h` real-price bars aggregated from holdout-excluded 1-minute data, the Prior-Range Location descriptor — `range_location = (Close − prior_low) / (prior_high − prior_low)` over the prior `20` completed same-timeframe bars, bucketed at the fixed thresholds bottom `≤ 0.20` / middle `(0.20, 0.80)` / top `≥ 0.80` — produces a deterministic feature whose top, middle, and bottom states each meet the predeclared numeric row and independent-episode floors (Gate 2) on at least two distinct instruments in both train and test segments, and the shared `1h`/`4h` aggregation-coverage rule is decidable by the predeclared strict-vs-tolerant feature-stability check.

If the descriptor's extreme buckets cannot be made count-eligible, or bucket assignment is unstable to the coverage rule, the Prior-Range Location candidate is recorded as a readiness-gated no-go and no return test (EXP-036) opens for it.

## Question

At `1h` and `4h`, what is the range-location distribution and the top/middle/bottom bucket count per instrument and segment; what is the outside-range rate; do the three states meet the numeric row and independent-episode floors; what is the `bar_aggregator` dropped-window rate at `1h`/`4h` under strict (exactly-`N`-bar) aggregation; and is the predeclared `0.90` minimum-coverage tolerance both necessary and admissible (i.e., does it materially change retention without destabilizing bucket assignment)?

This experiment also establishes the **shared aggregation-coverage rule** that every subsequent Phase 005 experiment (EXP-035 onward) inherits, per `design.md` §"Immediate Next Step".

## Scope Boundaries

- **Data Views**: 1-minute time bars from `data/timebars/`, deterministically aggregated to `1h` (60-minute) and `4h` (240-minute) clock-aligned OHLC bars via `python/src/bar_aggregator.aggregate_ohlc`. No chart-type inputs (no Line Break, Renko, or Heiken Ashi). No 1-minute analysis of the feature itself; the feature is defined only on the aggregated higher-timeframe bars.
- **Parameters** (all predeclared, frozen before implementation, never tuned on any result):
  - Prior-range lookback: `20` completed same-timeframe bars (high/low of the prior 20 bars, shifted so only completed bars are used).
  - Bucket thresholds: bottom `≤ 0.20`, middle `(0.20, 0.80)`, top `≥ 0.80`. Fixed thresholds, **not** data-driven terciles.
  - Timeframes: `1h` (`period_minutes = 60`) and `4h` (`period_minutes = 240`). `1d` is out of scope (no daily-session aggregator; deferred per `design.md` §"Data Scope").
  - Aggregation coverage settings, both reported: **strict** (`min_coverage = None`, retains windows with exactly `N` source bars — the current `aggregate_ohlc` behavior) and **tolerant** (`min_coverage = 0.90`, retains windows with `≥ ⌈0.90·N⌉` source bars). `0.90` is the single predeclared tolerant level; no other fraction is tested (a sweep would be tuning).
  - Numeric floors (Gate 2): each of the top, middle, and bottom states must have `≥ 100` train rows, `≥ 50` test rows, `≥ 30` train independent episodes, and `≥ 15` test independent episodes. An independent episode is a maximal run of consecutive same-timeframe bars assigned to the same bucket.
  - Reproducibility shuffle seed: `42` (deterministic permutation then re-sort by `CloseTime` before aggregation).
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC. All four are scoped because Gate 2 and the matched-control replication unit require evidence on `≥ 2` distinct instruments, and the coverage rule must be characterized per instrument (session-gap structure differs across forex, commodity, crypto, index).
- **Time range**: Full dataset per instrument with the nested chronological split applied to the **1-minute series before aggregation**. First 70% of the 1-minute series is the analysis set; after aggregation the higher-timeframe series is split chronologically 70/30 into train/test. The final 30% is the global holdout and is never loaded, inspected, aggregated, or used.
- **Global holdout**: The final 30% of each chronologically ordered instrument 1-minute dataset is excluded before any aggregation or feature computation, via `python/src/ict_timebar.load_analysis_timebars` (which slices the first 70% in the lazy plan). The full 1-minute dataset must never be aggregated and re-split.
- **Look-ahead bias prevention**: Aggregation uses only completed clock-aligned source windows. `prior_high`/`prior_low` use the rolling max-High/min-Low of the prior `20` bars **shifted by one bar**, so the feature at bar `i` uses only bars `≤ i−1` for the range and the bar-`i` close that is known at bar-`i` close. Train/test segment assignment is by the bar's own `CloseTime` against the per-instrument-timeframe train cutoff, never by bar index across views.
- **Real-price outcome discipline**: This experiment computes **no** forward return, FE/AE, hit rate, turnover, or P&L of any kind. It is readiness-only. The aggregated real OHLC is used solely to construct the feature and count states. The locked primary/secondary return metrics from `design.md` §"Locked Primary Edge Metric" are **not exercised** here; they are blocked until the mid-phase reflection issues a return-test directive (`design.md` Gate 7). No HA or Renko construction prices appear anywhere.
- **Exclusions**:
  - No return, excursion, hit-rate, or P&L metric (blocked by the readiness-before-return gate, `design.md` Gate 1).
  - No directional framing test, no matched-control comparison (prior-bar momentum sign control belongs to EXP-036, not here).
  - No `1d` analysis (no daily-session aggregator exists; deferred).
  - No data-driven bucket boundaries; the `0.20`/`0.80` thresholds are fixed.
  - No coverage-tolerance sweep; exactly one tolerant level (`0.90`) is tested against strict.
  - No other descriptor (Market Bias, Compression, Renko) — those are separate experiments.
  - No chart-type generators; no NY-time or macro-window features (not relevant to this descriptor).
  - No tick, bid/ask, spread, commission, or slippage fields.

## Success / Failure Criteria

The aggregate verdict is mechanical once the readiness table is computed. There is no return-based pass; "success" here means *count-eligibility established and the coverage rule decided*.

### Per-Instrument-Timeframe-Segment Readiness Checks

For each `(instrument, timeframe, segment)` cell, under the **canonical aggregation** (defined below):

1. **Determinism**: the SHA-256 digest of the serialized `(CloseTime, range_location, bucket, outside_range_flag)` feature table matches between (a) a fresh load + aggregate + feature pass and (b) a deterministically shuffled-then-resorted 1-minute load + the same pass. Both train and test digests must match.
2. **Row floor**: each of the bottom, middle, and top buckets has `≥ 100` rows in train and `≥ 50` rows in test.
3. **Episode floor**: each of the bottom, middle, and top buckets has `≥ 30` independent episodes in train and `≥ 15` in test.
4. **Denominator validity**: zero `NaN`/infinite `range_location` among in-range bars; the `prior_high − prior_low` denominator is strictly positive for every feature-eligible bar (degenerate flat-range bars are flagged and excluded from bucketing, and their share is reported — they must not silently dominate any bucket).

A `(instrument, timeframe)` pair **passes readiness** for Prior-Range Location iff checks 1–4 hold for **both** train and test segments.

### Coverage-Rule Decision (Gate-locking output)

5. **Coverage characterization**: report the strict dropped-window rate (`1 − retained/expected`) and the tolerant (`0.90`) dropped-window rate per `(instrument, timeframe)`.
6. **Coverage feature-interaction stability** (amendment 3, binding): on the set of windows present in **both** strict and tolerant aggregations (matched by `CloseTime`), report the share receiving the **identical bucket label** under each aggregation. The tolerant rule is **admissible** for the phase only if this identical-bucket share is `≥ 0.95` on at least two distinct instruments at each timeframe. If the feature is unstable to the tolerance (`< 0.95`), **strict aggregation is retained** even at the cost of coverage.

**Canonical aggregation selection (predeclared, not outcome-tuned):**
- If strict aggregation already yields readiness checks 1–4 on `≥ 2` distinct instruments at a timeframe, **strict is canonical** for that timeframe and the tolerant rule is reported as diagnostic only.
- If strict fails the row/episode floors purely because of dropped-window coverage loss **and** the tolerant rule is admissible (check 6), **tolerant (`0.90`) is canonical**.
- If strict fails and the tolerant rule is inadmissible (check 6 fails), the timeframe is recorded as **coverage-blocked** and Prior-Range Location readiness for that timeframe is a no-go.

This selection rule is fixed before results are inspected; it uses coverage and feature-stability evidence (checks 5–6), never return performance.

### Aggregate Verdict (Predeclared)

- **Evidence FOR readiness** (Prior-Range Location advances to the mid-phase reflection as a return-test candidate): the descriptor passes readiness checks 1–4 on `≥ 2` distinct instruments in both segments, at `≥ 1` timeframe, under the canonical aggregation, **and** the canonical aggregation rule for that timeframe is decided (not coverage-blocked).
- **Evidence AGAINST / readiness-gated no-go**: on no timeframe do `≥ 2` distinct instruments pass checks 1–4 under any admissible aggregation — extreme buckets are too sparse, episodes too few, denominators collapse, or the timeframe is coverage-blocked. Prior-Range Location is recorded as a readiness no-go; no EXP-036 opens for it. This is the design's preferred clean negative.
- **Inconclusive**: exactly one instrument passes on an otherwise promising timeframe, or determinism (check 1) fails for an implementation reason that must be fixed and re-run before a verdict. Inconclusive does not relax any floor; it triggers a documented gap and a fix-or-close decision.

**Fast stop** (`design.md` Candidate 1): stop and record the no-go immediately if, on every timeframe, extreme buckets are not count-eligible, or outside-range/middle states dominate so heavily that extremes cannot be tested, or train/test bucket assignment is unstable.

### Mathematical Attainability

The floors are jointly attainable in principle. With the `0.20`/`0.80` thresholds, a roughly uniform `range_location` would place ~20% of bars in each extreme. Prior 15m/1h aggregated analysis-set sizes (EXP-002-TF/EXP-031: tens of thousands of `1h` bars per instrument; `4h` ≈ ¼ of that) imply thousands of bars per extreme bucket at `1h`, far above the `100`/`50` row floors. The binding risk is at `4h` (fewer bars) and is exactly what the episode floor (`30`/`15`) tests. No floor is set above what a uniform-bucket null could plausibly clear, so failure cannot be a moved goalpost.

## Prerequisites and Sequencing

Requires:
- `python/src/bar_aggregator.aggregate_ohlc` extended with a backward-compatible `min_coverage: float | None = None` parameter (default `None` reproduces the current exactly-`N` behavior, preserving EXP-029/030/031/033 reproducibility). This is a code-organization extension to existing shared infrastructure, **not** a new analytical module.
- `python/src/ict_timebar.load_analysis_timebars`, `train_cutoff_time`, `INSTRUMENTS` (reused unchanged).

EXP-034 is the first Phase 005 experiment. EXP-035 (Market Bias) inherits the shared aggregation-coverage characterization produced here; the binding canonical coverage rule is confirmed at the mid-phase reflection after both readiness experiments complete (`design.md` §"Mid-Phase Reflection").

## Complexity Budget

- **Max statistical test families: 0.** This is a count/distribution readiness survey. All readiness checks are exact counts, deterministic digests, and exact shares — no inferential statistic, no bootstrap, no parametric assumption. This is the simplest sufficient approach (`design.md` complexity budget allows ≤ 3; `0` is chosen deliberately).
- **Max primary visualisations: 4.**
- **Max new reusable modules: 0.** The only `python/src` change is the backward-compatible `min_coverage` parameter on the existing `aggregate_ohlc` (code-organization extension, routed through governance). No new analytical module is created.

## Data Requirements

For each instrument and each timeframe (`60`, `240` minutes), and each aggregation setting (strict, tolerant `0.90`):

1. Load the holdout-excluded 1-minute analysis frame via `load_analysis_timebars(DATA_DIR, instrument)` (first 70% of `CloseTime`-sorted 1-minute bars).
2. Aggregate to the target timeframe via `aggregate_ohlc(frame_1m, period_minutes=tf, min_coverage=setting)`.
3. Apply the nested 70/30 chronological train/test split to the aggregated series; record the per-`(instrument, timeframe, aggregation)` train cutoff `CloseTime` via `train_cutoff_time`.
4. Compute `prior_high`/`prior_low` as `rolling_max(High, 20).shift(1)` / `rolling_min(Low, 20).shift(1)` (only completed prior bars); `range_location = (Close − prior_low) / (prior_high − prior_low)`; raw value retained for the outside-range flag (`raw < 0` or `raw > 1`); clipped value in `[0, 1]` used for bucketing; bars where `prior_high == prior_low` flagged degenerate and excluded from bucketing.
5. Assign buckets (bottom/middle/top) on the clipped value; compute bucket counts, outside-range rate, degenerate-bar share, and independent-episode counts per bucket per segment.
6. Compute coverage diagnostics (dropped-window rate; matched-window identical-bucket share strict-vs-tolerant).
7. Compute determinism digests (canonical vs shuffled-then-resorted).
8. Apply the canonical-aggregation selection and the aggregate verdict mechanically.

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
    bars_tf = aggregate_ohlc(bars_1m, period_minutes=60, min_coverage=None)
    # holdout exclusion is complete; never re-scan the full file without the slice
```

## Suggested Direction

Report coverage diagnostics (dropped-window rate; strict-vs-tolerant matched-bucket stability) **before** any bucket-count or readiness verdict, so the canonical-aggregation choice is visible and auditable before counts are read. Present the range-location distribution and bucket-count matrix next, then the episode-count readiness grid. The verdict is mechanical: pass readiness checks 1–4 on `≥ 2` distinct instruments at `≥ 1` timeframe under an admissible canonical aggregation, or record the readiness-gated no-go. Determinism digests are presented first so any later anomaly is traceable to a specific instrument/timeframe.
