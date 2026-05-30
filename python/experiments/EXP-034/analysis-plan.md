# Analysis Plan: Experiment EXP-034

## Objective

Determine whether the Prior-Range Location descriptor is **count-eligible** at `1h`/`4h` — i.e., whether its top, middle, and bottom buckets each meet the predeclared row floors (`≥100` train, `≥50` test) and independent-episode floors (`≥30` train, `≥15` test) on `≥2` distinct instruments in both segments — and **decide the shared aggregation-coverage rule** for the phase via the predeclared strict-vs-tolerant feature-stability check. No return, excursion, or P&L metric is computed; this is a deterministic readiness survey. The verdict either advances Prior-Range Location to the mid-phase reflection as a return-test candidate or records a readiness-gated no-go, and it locks the canonical `1h`/`4h` aggregation that EXP-035 onward inherit.

## Methodology

Every statistic below is computed per `(instrument, timeframe, aggregation, segment)` cell. Coverage diagnostics and determinism digests are computed first so the canonical-aggregation choice and any anomaly are auditable before counts are read. All methods are exact (counts, shares, deterministic hashes); no inferential test is used, consistent with the `0`-stat-test budget and the programme's simplicity principle.

### Step 1: Holdout-excluded load and clock-aligned aggregation

- **Method**: `load_analysis_timebars(DATA_DIR, instrument)` returns the first 70% of `CloseTime`-sorted 1-minute bars (holdout already excluded in the lazy plan). Aggregate to `60`- and `240`-minute clock-aligned OHLC via `aggregate_ohlc(frame_1m, period_minutes, min_coverage)` for `min_coverage ∈ {None (strict), 0.90 (tolerant)}`.
- **Why this method**: Holdout exclusion must be applied to the 1-minute series **before** aggregation (`_pipeline-config.md` §"OOS Holdout Rules", `scope.md` §"Global holdout"). `aggregate_ohlc` is the audited deterministic resampler from EXP-029; the `min_coverage` parameter is a backward-compatible extension whose default reproduces the exactly-`N` behavior used by prior experiments.
- **Simpler alternative considered**: Aggregating the full dataset then splitting on the higher-timeframe series. Rejected — it would materialize the holdout, violating the holdout discipline. Also rejected: using a single timeframe — the phase requires `1h` and `4h` natively (`design.md` §"Data Scope").
- **Assumptions**:
  - **Temporal structure**: 1-minute `CloseTime` strictly increasing within file; `aggregate_ohlc` sorts internally before bucketing.
  - **Cross-view alignment**: All downstream work aligns by aggregated `CloseTime`; no bar-index alignment.
  - **Real-price outcomes**: none computed; the aggregated real OHLC is used only to build the feature.
- **Expected output**: per `(instrument, timeframe, aggregation)`, an aggregated OHLC frame with a `SourceBars` count column.

### Step 2: Nested chronological train/test split

- **Method**: 70/30 chronological split on each aggregated series; record the train-cutoff `CloseTime` via `train_cutoff_time(frame, int(height*0.70))`. Segment assignment is by each bar's own `CloseTime` (`≤ cutoff` → Train, else Test).
- **Why this method**: Matches the nested-split convention of EXP-029/031/033 so segment definitions are comparable. Timestamp-based assignment is the authoritative form (`_pipeline-config.md`).
- **Simpler alternative considered**: Bar-index split. Equivalent here but less robust to future sparsity; timestamp assignment is preferred.
- **Assumptions**: same temporal-structure assumptions as Step 1.
- **Expected output**: per cell, a `Segment` label column and the recorded cutoff timestamp.

### Step 3: Prior-Range Location feature construction

- **Method**: `prior_high = rolling_max(High, window=20).shift(1)`, `prior_low = rolling_min(Low, window=20).shift(1)` (min_samples = 20, so the first 20 bars per series are null and feature-ineligible). `denom = prior_high − prior_low`. `raw_location = (Close − prior_low) / denom`. `outside_range_flag = (raw_location < 0) | (raw_location > 1)`. `clipped_location = clip(raw_location, 0, 1)`. Bars with `denom <= 0` (degenerate flat 20-bar range) are flagged `degenerate` and excluded from bucketing. Buckets on `clipped_location`: `bottom` (`≤ 0.20`), `top` (`≥ 0.80`), `middle` (otherwise).
- **Why this method**: This is the exact feature predeclared in `design.md` Candidate 1. The `.shift(1)` enforces look-ahead-free construction (the range uses only completed prior bars; the close is known at the bar's own close). Clipping with a separate outside-range flag matches `design.md` ("Clipped to `[0,1]` with a separate outside-range flag"). Degenerate-range handling makes the denominator explicit (`scope.md` readiness check 4) rather than letting division-by-zero produce silent `inf`/`NaN`.
- **Simpler alternative considered**: Data-driven terciles for buckets. Rejected — `design.md` locks fixed `0.20`/`0.80` thresholds; terciles would be outcome-adjacent and not comparable across segments.
- **Assumptions**:
  - **Look-ahead bias prevention**: feature at bar `i` uses bars `≤ i−1` for the range plus the bar-`i` close.
  - **NaN handling**: explicit — first-20 bars and degenerate-range bars are excluded from bucketing and their share reported; no silent propagation.
- **Expected output**: per cell, a feature table `(CloseTime, Segment, raw_location, clipped_location, outside_range_flag, degenerate_flag, bucket)`.

### Step 4: Bucket counts, outside-range rate, degenerate share

- **Method**: Per `(instrument, timeframe, aggregation, segment)`, count bars in each bucket among feature-eligible (non-null, non-degenerate) bars; compute `outside_range_rate = mean(outside_range_flag)` over feature-eligible bars and `degenerate_share = degenerate_count / total_feature_window_bars`.
- **Why this method**: Direct exact counts answer the count-eligibility question (`scope.md` readiness check 2) and the "do extremes/middle dominate" fast-stop condition. No estimator is needed.
- **Simpler alternative considered**: Reporting only proportions. Rejected — absolute counts are what the floors test; proportions are reported alongside for interpretability.
- **Assumptions**: none beyond Step 3.
- **Expected output**: per cell, bucket counts (`n_bottom`, `n_middle`, `n_top`), `outside_range_rate`, `degenerate_share`.

### Step 5: Independent-episode counts per bucket

- **Method**: Within each segment (ordered by `CloseTime`), an episode is a maximal run of consecutive feature-eligible bars carrying the same `bucket` label. Count episodes per bucket per segment via run-length encoding of the bucket sequence (consecutive equal labels collapse to one episode). Degenerate/null bars break runs (they are not assigned a bucket, so a run is interrupted by a gap). Also record median and distribution of episode length per bucket for persistence context.
- **Why this method**: `design.md` Gate 2 makes independent episodes the binding denominator for serially dependent descriptors; range-location persists across adjacent bars, so raw row counts overstate independent information. Run-length encoding is the exact, assumption-free way to count episodes.
- **Simpler alternative considered**: Treating each row as independent (row floor only). Rejected — that is exactly the serial-dependence error `design.md` §"Resolved Draft Gaps" item 7 warns against; episodes are required.
- **Assumptions**:
  - **Serial dependence acknowledged**: episodes, not rows, are the independence unit. No i.i.d. assumption.
  - **Run definition**: a null/degenerate bar interrupts a run; this is conservative (it can only split runs, never merge them).
- **Expected output**: per cell, episode counts (`ep_bottom`, `ep_middle`, `ep_top`) and per-bucket median episode length.

### Step 6: Coverage diagnostics and the strict-vs-tolerant feature-interaction check

- **Method**: Per `(instrument, timeframe)`:
  - `strict_dropped_rate` and `tolerant_dropped_rate` = `1 − retained_windows / expected_windows`, where `expected_windows = ⌊source_1m_rows / period_minutes⌋` (via `coverage_summary` or direct computation).
  - **Matched-window identical-bucket share**: inner-join the strict and tolerant feature tables on `CloseTime` (the full windows present in both — strict windows are a subset of tolerant windows, but their `range_location` can differ because the tolerant series interleaves partial windows into the prior-20 lookback). Compute the share of matched windows with identical `bucket` under both aggregations.
- **Why this method**: This operationalizes amendment 3 — the coverage tolerance directly perturbs the `20`-bar `prior_high`/`prior_low` (partial windows have understated High/Low and change the lookback composition), so admissibility must be tested on the feature itself, not assumed. The matched-window share is the exact measure of that perturbation.
- **Simpler alternative considered**: Comparing only bucket-count distributions strict-vs-tolerant. Rejected — equal marginal counts can hide per-bar reassignment; the matched join detects reassignment directly.
- **Assumptions**:
  - **Cross-aggregation alignment by timestamp**: the join is on `CloseTime`, never bar index.
  - **Subset structure**: strict full windows ⊆ tolerant retained windows; the join is well-defined.
- **Expected output**: per `(instrument, timeframe)`: `strict_dropped_rate`, `tolerant_dropped_rate`, `matched_identical_bucket_share`, `tolerant_admissible` (share `≥ 0.95`).

### Step 7: Determinism digest (readiness check 1)

- **Method**: Recompute the Step-3 feature table twice per cell: (a) canonical load + sort + aggregate + feature; (b) deterministic permutation of the 1-minute rows via `numpy.random.default_rng(42).permutation`, then `sort("CloseTime")`, then the same pipeline. SHA-256 over the serialized `(CloseTime, range_location[%.12g], bucket, outside_range_flag)` table per segment. Check passes iff canonical and shuffled digests are byte-identical for both segments.
- **Why this method**: SHA-256 over a deterministic serialization is the canonical reproducibility check used in EXP-020/029/033. Shuffle-then-resort probes whether any code path depends on input row order beyond the canonical `CloseTime` sort.
- **Simpler alternative considered**: Comparing counts only. Rejected — distinct feature tables can share counts; full-table digest catches mis-ordered or substituted rows.
- **Assumptions**: canonical serialization (fixed column order, `%.12g` float formatting, explicit NaN token). Determinism of `aggregate_ohlc` and the feature pass.
- **Expected output**: per cell, `digest_canonical`, `digest_shuffled`, `digests_match`.

### Step 8: Canonical-aggregation selection and aggregate verdict

- **Method**: Apply `scope.md` §"Canonical aggregation selection" then §"Aggregate Verdict" mechanically:
  1. For each timeframe, evaluate readiness checks 1–4 under **strict**. If `≥2` distinct instruments pass both segments → strict is canonical for that timeframe.
  2. Else, if strict fails purely on row/episode floors and tolerant is admissible (Step 6 share `≥0.95` on `≥2` instruments) → tolerant `0.90` is canonical; re-evaluate checks 1–4 under tolerant.
  3. Else → timeframe is coverage-blocked.
  4. Prior-Range Location passes readiness iff `≥2` distinct instruments pass checks 1–4 at `≥1` timeframe under the canonical (admissible) aggregation; else readiness-gated no-go; else inconclusive per the single-instrument / fixable-determinism clauses.
- **Why this method**: The verdict is mechanical and pre-registered, using only coverage and feature-stability evidence to choose aggregation — never return performance (there is none). Matches `design.md` Gates 1, 2, 6, 7.
- **Simpler alternative considered**: Always use tolerant to maximize counts. Rejected — that would silently change the feature where unstable; amendment 3 requires strict be retained if the tolerance destabilizes bucketing.
- **Assumptions**: none beyond determinism of the readiness tables.
- **Expected output**: `verdict.json` with `canonical_aggregation_per_timeframe`, per-timeframe `passing_instruments`, `verdict_text` (one of the three predeclared strings), and the locked coverage rule for downstream inheritance.

## Visualisations

1. **Coverage and stability panel** (1 figure, 2 subplots). Left: grouped bars of strict vs tolerant dropped-window rate per `(instrument, timeframe)`. Right: matched-window identical-bucket share per `(instrument, timeframe)` with the `0.95` admissibility line. Purpose: makes the canonical-aggregation decision auditable before any count is read.
2. **Range-location distribution** (1 figure, 2×4 grid: instruments × timeframes, strict aggregation, train+test overlaid or pooled-analysis). Histogram (≥30 bins) of `clipped_location` with the `0.20`/`0.80` bucket boundaries drawn. Purpose: shows whether extremes are populated or whether the middle dominates (fast-stop condition).
3. **Bucket-count matrix** (1 figure, heatmap). Rows: buckets (bottom/middle/top). Columns: `(instrument, timeframe, segment)` under the canonical aggregation. Cell value: row count, annotated. Row-floor reference (`100` train / `50` test) noted in caption. Purpose: shows row-floor status for all cells at once.
4. **Episode-count readiness grid** (1 figure, heatmap or pass/fail grid). Same column layout as plot 3, cell value: independent-episode count per bucket, with the `30` train / `15` test episode floors as the pass/fail threshold. Purpose: makes the binding (episode) readiness verdict mechanically auditable.

No additional plots. Determinism digests and the verdict are tabular (`results/`), not plotted.

## Interpretation Guide

- **If `≥2` distinct instruments pass readiness checks 1–4 at `≥1` timeframe under an admissible canonical aggregation**, Prior-Range Location is count-eligible: it advances to the mid-phase reflection as a return-test candidate, and the canonical `1h`/`4h` coverage rule is locked for the phase. Record passing instruments, the canonical aggregation per timeframe, and per-cell counts in `results.md`.
- **If no timeframe has `≥2` passing instruments under any admissible aggregation**, the extreme buckets are not count-eligible (too sparse), or episodes are too few, or denominators collapse, or both timeframes are coverage-blocked. This is a readiness-gated no-go for Prior-Range Location — REFUTED for the count-eligibility hypothesis — and no EXP-036 opens for it. This is the design's preferred clean negative and is fully holdout-preserving.
- **If exactly one instrument passes on an otherwise promising timeframe**, the result is INCONCLUSIVE for Prior-Range Location: the single-instrument pass is recorded but does not satisfy the `≥2` distinct-instrument rule. If no timeframe reaches `≥2`, the aggregate verdict is the readiness-gated no-go.
- **If the tolerant matched-bucket share is `< 0.95`** on the instruments that would otherwise need it, the tolerance is inadmissible: strict aggregation is retained and the timeframe is judged on strict counts alone (possibly coverage-blocked). This prevents a coverage convenience from silently redefining the feature.
- **If determinism (check 1) fails**, the result is INCONCLUSIVE pending a fix: a determinism failure indicates an order-dependent code path that must be corrected and re-run before any readiness verdict; it is never waved through.
- **If `degenerate_share` is non-trivial** (flat 20-bar ranges, plausible only in pathological low-volatility stretches), report it explicitly; degenerate bars are excluded from bucketing and must not inflate or deplete any bucket.

## Complexity Check

- **Statistical tests**: 0 planned / 0 budgeted. All readiness checks are exact counts, exact shares, and deterministic SHA-256 digests. No bootstrap or inferential test — none is needed for a count/distribution readiness survey, and `0` honors the simplicity principle.
- **Visualisations**: 4 planned / 4 budgeted — coverage+stability panel, range-location distribution, bucket-count matrix, episode-count readiness grid.
- **New modules**: 0 planned / 0 budgeted. The only `python/src` change is the backward-compatible `min_coverage` parameter on `aggregate_ohlc` (default `None` reproduces prior behavior) — a code-organization extension routed through governance, not a new analytical module.

## Data-View Comparison Considerations

### Cross-View Alignment

- The only cross-view operation is the strict-vs-tolerant matched-window join (Step 6), performed strictly on `CloseTime`, never on bar index. Train/test assignment is by each bar's own `CloseTime` against the per-cell cutoff.

### Real-Price Outcome Discipline

- No returns, excursions, hit rates, or P&L are computed. The aggregated real OHLC is used only for feature construction. By construction the readiness tables contain no return column; any such column appearing in code or output is a scope violation to be flagged. No HA/Renko construction prices appear.

### Event Density Differences

- `4h` produces ≈¼ the bars of `1h`; the row and episode floors are the explicit guard against insufficient density at coarser timeframes. Strict aggregation reduces density further via dropped windows — characterized in Step 6 and is the reason the tolerant rule exists.

### Regime Stratification

- Out of scope. Buckets are fixed at `0.20`/`0.80`, not regime-conditioned. Any regime structure is absorbed into the per-segment counts; regime stratification would be scope creep and is excluded.
