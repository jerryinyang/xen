# Analysis Plan: Experiment EXP-036

## Objective

Determine whether the Prior-Range Location descriptor carries an **executable, control-adjusted directional edge** on `1h`/`4h` strict-aggregated real bars. Concretely: does the direction-adjusted next-bar log return of the extreme states (top → long, bottom → short) beat (a) the measured mean return of its own neutral middle bucket and (b) a matched prior-bar-momentum-sign control, with episode-level bootstrap CIs and train/test sign preservation on `>= 2` distinct instruments — and does the same hold at the single predeclared 4-bar hold? This is the first return test of the Phase 005 state-descriptor thesis. The verdict either advances Prior-Range Location to EXP-038 robustness (FOR), records state-differentiation-only or a clean refutation (AGAINST), or returns Inconclusive, all holdout-preserving.

## Methodology

Every statistic is computed per `(instrument, timeframe, segment)` cell under strict aggregation (the canonical Phase 005 rule). Eligible counts are reported before effect sizes so a count-driven Inconclusive surfaces first. Inference respects serial dependence: episodes, not rows, are the resampling unit. Two test families are used (per-mean episode bootstrap for `Δ_neutral`; paired episode bootstrap for `Δ_control`), re-applied to the 4-bar horizon.

### Step 1: Holdout-excluded load and strict clock-aligned aggregation

- **Method**: `load_analysis_timebars(DATA_DIR, instrument)` (first 70% of `CloseTime`-sorted 1-minute bars; holdout excluded in the lazy plan). Aggregate to `60`/`240` minutes via `aggregate_ohlc(frame_1m, period_minutes, min_coverage=None)` — strict, the rule the mid-phase reflection locked.
- **Why this method**: Holdout exclusion must precede aggregation (`_pipeline-config.md` §"OOS Holdout Rules"). Strict is canonical because EXP-034 cleared strict readiness on `>= 2` instruments at both timeframes; tolerant is feature-perturbing and inadmissible phase-wide (reflection §1).
- **Simpler alternative considered**: Tolerant aggregation to recover dropped windows. Rejected — it destabilizes the `20`-bar range feature (EXP-034) and would be a per-experiment aggregation degree of freedom the phase forbids.
- **Assumptions**: 1-minute `CloseTime` strictly increasing within file; `aggregate_ohlc` sorts internally and is deterministic (EXP-029-audited). No bar-index alignment anywhere.
- **Expected output**: per `(instrument, timeframe)`, a strict aggregated OHLC frame with a `SourceBars` column.

### Step 2: Nested chronological train/test split

- **Method**: 70/30 chronological split on each aggregated series; record train-cutoff `CloseTime` via `train_cutoff_time(frame, int(height*0.70))`; assign `Segment` by each bar's own `CloseTime` (`<= cutoff` → Train, else Test).
- **Why this method**: Matches EXP-029/031/033/034 so segment definitions are comparable across the phase. Train/test sign preservation — the core replication test — requires this split.
- **Simpler alternative considered**: Bar-index split. Equivalent here but timestamp assignment is the authoritative convention.
- **Assumptions**: same temporal-structure assumptions as Step 1.
- **Expected output**: per cell, a `Segment` column and the recorded cutoff timestamp.

### Step 3: Prior-Range Location feature (reuse of EXP-034 construction)

- **Method**: `prior_high = rolling_max(High,20).shift(1)`, `prior_low = rolling_min(Low,20).shift(1)`; `denom = prior_high − prior_low`; `raw = (Close − prior_low)/denom`; `outside_range_flag = (raw<0)|(raw>1)`; `clipped = clip(raw,0,1)`; `denom<=0` flagged degenerate and excluded; buckets on `clipped`: bottom `<=0.20`, top `>=0.80`, middle otherwise. Directional implication `d = +1` (top), `−1` (bottom), `0` (middle). Episode labels via run-length encoding of the bucket sequence (a null/degenerate bar breaks a run).
- **Why this method**: Bit-for-bit the readiness feature EXP-034 validated; reusing it guarantees the return test runs on the exact states already shown count-eligible and deterministic. `.shift(1)` enforces look-ahead-free construction.
- **Simpler alternative considered**: Recomputing buckets with data-driven terciles. Rejected — `design.md` locks fixed `0.20/0.80` thresholds.
- **Assumptions**:
  - **Look-ahead bias prevention**: state at bar `i` uses bars `<= i−1` for the range plus the bar-`i` close.
  - **NaN handling**: explicit — first-20 and degenerate bars excluded from bucketing; their share reported.
- **Expected output**: per cell, a feature table `(CloseTime, Segment, clipped, outside_range_flag, degenerate_flag, bucket, d, episode_id)`.

### Step 4: Executable returns and the return-eligibility filter

- **Method**: From the aggregated real OHLC, next-bar `r_i = ln(Close_{i+1}/Open_{i+1})` and 4-bar `r4_i = ln(Close_{i+4}/Open_{i+1})`, indexing the next row-adjacent bar(s) within the same segment. Return-eligibility: drop bar `i` if the required forward bar(s) do not exist in-segment (`i+1` for primary; `i+1…i+4` for secondary). Record the inter-bar clock gap `CloseTime_{i+1} − CloseTime_i` (and the 4-bar span) as a staleness diagnostic; gap-spanning entries are retained (entering at the next formed bar is executable; the gap delays entry, not the single-bar open-to-close return).
- **Why this method**: This is the locked executable convention (descriptor observed at close; entry next open; exit next close, real OHLC). Filtering on forward-bar existence rather than silently reindexing prevents fabricating returns across segment/series boundaries. Reporting the gap makes the executability assumption auditable rather than hidden.
- **Simpler alternative considered**: Close-to-close returns (`ln(Close_{i+1}/Close_i)`). Rejected as primary — it is not executable from the next open and is permitted only as a diagnostic by `design.md`; the open-to-close convention is the locked one. Also rejected: dropping all gap-spanning entries up front — that is a robustness perturbation reserved for EXP-038, not a primary-path choice.
- **Assumptions**:
  - **Real-price outcomes**: returns use aggregated real OHLC only; no HA/Renko prices.
  - **Alignment by timestamp**: forward bars selected by row adjacency within a `CloseTime`-sorted segment; never by bar index across instruments/timeframes.
- **Expected output**: per cell, `r`, `r4`, `eligible_primary`, `eligible_secondary`, `entry_gap_minutes`.

### Step 5: Control signal and state-aligned return series

- **Method**: Control momentum sign `c_i = sign(Close_i − Close_{i−1})` (flat bars `c_i=0` carry no control position). Descriptor aligned return `S^desc_i = d_i · r_i`; control aligned return `S^ctrl_i = c_i · r_i`. **Neutral baseline** `μ_mid = mean(r | middle-bucket bars)` measured per `(cell, segment, horizon)` — the descriptor's own middle state is the locked neutral baseline (`design.md` §"Locked Primary Edge Metric": the middle bucket, *not* a zero baseline). The vs-neutral excess `e_i = d_i · (r_i − μ_mid)` is the direction-adjusted excess of each extreme bar over the measured middle drift. The vs-control comparison is **paired on the descriptor's extreme (traded) bars** — on the exact bars the descriptor prescribes a position, compare its direction against the momentum-sign direction. Build the analogous `S^desc_i(4)`, `S^ctrl_i(4)`, `e_i(4)`, and `μ_mid(4)` from `r4_i`.
- **Why this method**: Two distinct, intentionally different baselines. (1) The neutral baseline `μ_mid` is the *measured* middle-bucket drift; `e_i` is zero in expectation under the null that an extreme bucket does not differ from the middle bucket, so a positive `Δ_neutral` proves separation from the neutral state rather than mere ambient drift. (2) The matched control isolates the *direction* choice on the descriptor's own traded bars; the central scientific question is whether range-location adds information beyond "follow recent momentum." `design.md` makes prior-bar momentum sign the binding matched control and the middle bucket the neutral baseline.
- **Simpler alternative considered**: (a) Defining the neutral contrast against flat cash / zero return. **Rejected — this is the error the audit caught**: it tests only whether extreme returns are positive, not whether they differ from the middle state, and `design.md` explicitly prohibits a zero baseline. (b) Evaluating the control on its own full population (unpaired). Rejected as primary — unpaired comparison confounds bar selection with direction choice; pairing on traded bars is tighter. (The unpaired control mean may be reported as a secondary diagnostic only.)
- **Assumptions**:
  - **Look-ahead**: `c_i` uses only `Close_i`, `Close_{i−1}` (`<= i`); `μ_mid` uses only same-segment middle-bucket returns; both independent of the per-bar `>= i+1` return being aligned.
  - **Direction-adjusted pooling**: top and bottom extremes pool into one `e_i` series via the sign `d_i`, each measured relative to the common `μ_mid`.
- **Expected output**: per cell/segment, `S^desc`, `S^ctrl`, and `e_i` arrays over eligible extreme bars (each tagged with `episode_id`), plus the middle-bucket return array (tagged with its own `episode_id`) and the scalar `μ_mid`.

### Step 6: Eligible counts per traded state (reported before effect sizes)

- **Method**: Per `(instrument, timeframe, segment)`, after the return-eligibility filter, count eligible rows and independent episodes for the top, bottom, **and middle** states. Compare each against the EXP-034 floors (`>= 100` train rows / `>= 50` test rows / `>= 30` train episodes / `>= 15` test episodes). The middle bucket is **not** "context only": it is the `μ_mid` baseline, so the vs-neutral contrast is adjudicable for a cell only when the middle state clears the floor (alongside the relevant extreme state).
- **Why this method**: A return estimate on a sub-floor state is not adjudicable; surfacing counts first prevents reading effect sizes from underpowered cells (mirrors EXP-034). The vs-neutral contrast depends on the middle bucket's mean, so its episode count governs the precision of `μ_mid` and must clear the floor too. The filter can only reduce the EXP-034 counts modestly, so this verifies the floors still hold rather than assuming it.
- **Simpler alternative considered**: Trusting EXP-034 counts directly, or treating the middle bucket as uncounted context. Rejected — the return-eligibility filter (forward-bar existence) changes counts, and the middle bucket is a measured baseline whose count bounds `μ_mid`'s precision.
- **Assumptions**: episode definition identical to EXP-034 (maximal same-bucket runs).
- **Expected output**: per cell, `n_rows`/`n_episodes` for top, bottom, and middle states, each with a floor pass/fail flag; a per-contrast adjudicability flag (vs-neutral needs the relevant extreme + middle; vs-control needs the relevant extreme).

### Step 7: Episode-level bootstrap CIs for Δ_neutral and Δ_control

- **Method**: Resampling unit = **independent state episode** (resample episodes with replacement, weighting each episode's contribution by its eligible bar count, `10,000` resamples, `numpy.random.default_rng(42)`).
  - `Δ_neutral = mean( d_i · (r_i − μ_mid) | extreme bars )` — the direction-adjusted excess of the extreme states over the **measured** middle-bucket drift `μ_mid`, **not** over zero. Because `μ_mid` is itself estimated from the middle bucket, the CI uses a **two-sample episode bootstrap**: each resample draws extreme episodes (for the `d_i · r_i` term) and middle episodes (to recompute `μ_mid`) **independently** with replacement, then recomputes `Δ_neutral`. Report point estimate and two-sided `95%` CI; the test is whether the CI excludes 0 positively. Under the null `E[r|top] = E[r|bottom] = μ_mid`, `Δ_neutral` is centered at 0, so a positive pass proves separation from the neutral middle state, not ambient drift.
  - `Δ_control = mean(S^desc_i − S^ctrl_i | extreme bars)`; paired single-sample episode-bootstrap CI (resample extreme episodes, recompute the paired mean difference each draw — `μ_mid` does not enter the head-to-head). Test whether the CI excludes 0 positively.
  - Repeat both for the 4-bar series (`S^desc(4)`, `S^ctrl(4)`, `μ_mid(4)`).
  - Report the per-side components `E[r|top] − μ_mid` and `μ_mid − E[r|bottom]` with their CIs so a one-sided-only effect (e.g., only the top bucket separates) is visible and not hidden by pooling.
  - Diagnostic only: naive row-level bootstrap CI for the same contrasts (to expose how much serial dependence widens the honest episode CI).
- **Why this method**: Range-location states persist across adjacent bars (EXP-034 episode lengths), so row-level resampling overstates independent information — exactly the serial-dependence error `design.md` §"Resolved Draft Gaps" item 7 forbids. The two-sample bootstrap for `Δ_neutral` propagates the sampling uncertainty of the middle-bucket baseline rather than treating `μ_mid` as a known constant. Episode resampling is the non-parametric, distribution-free inference the programme prefers; reusing the `default_rng(42)` convention and the existing mean/paired CI helpers (`signal_quality.bootstrap_means`, `bootstrap_diff_ci`; `timeframe_replication.bootstrap_mean_ci`) keeps it consistent with prior experiments.
- **Simpler alternative considered**: (a) Defining `Δ_neutral` against zero / flat cash and a one-sample bootstrap. **Rejected — the audit-caught error**: it tests extreme-return positivity, not differentiation from the middle bucket, and a zero baseline is prohibited. (b) Treating `μ_mid` as a fixed constant (one-sample bootstrap of the extremes only). Rejected — it understates the CI by ignoring middle-bucket estimation error. (c) Parametric t-CI. Rejected — financial returns are heavy-tailed and serially dependent; parametric normality is an academic-finance pitfall.
- **Assumptions**:
  - **Serial dependence**: addressed by episode resampling; no i.i.d. row assumption.
  - **Stationarity within segment**: not assumed beyond the episode bootstrap; train/test sign preservation is the cross-segment robustness check that guards against a train-only artifact.
- **Expected output**: per cell/segment/horizon, `μ_mid`, `Δ_neutral` and `Δ_control` point estimates, the two per-side components, `95%` episode-bootstrap CIs (and diagnostic row-bootstrap CIs).

### Step 8: Mechanical verdict — train/test sign preservation and distinct-instrument replication

- **Method**: Apply `scope.md` §"Success / Failure Criteria":
  1. A cell **replicates** a contrast at a horizon iff the test-segment CI excludes 0 positively **and** the train point estimate is positive (same sign).
  2. **Next-bar primary FOR (edge candidate)**: `>= 2` distinct instruments replicate **both** `Δ_neutral` and `Δ_control` at `>= 1` timeframe.
  3. **State-differentiation-only**: `>= 2` distinct instruments replicate `Δ_neutral` but not `Δ_control` (Gate 4 blocks edge language).
  4. **AGAINST (refutation)**: `< 2` distinct instruments replicate `Δ_control` at any timeframe on the next-bar primary, **and** the 4-bar secondary also fails its `Δ_control` gate.
  5. **Horizon-dependent state differentiation**: next-bar `Δ_control` gate fails but the 4-bar secondary passes both contrasts on `>= 2` distinct instruments — reopens the thesis at the longer horizon via a new experiment; not refutation.
  6. **Inconclusive**: exactly one instrument passes, or a contrast's eligible counts fall below the floor so `>= 2` cannot be adjudicated.
- **Why this method**: The verdict is pre-registered and uses only train/test sign preservation and distinct-instrument replication — no test-segment value selects parameters, timeframes, or candidates (Gate 6). Distinct instrument is the independence unit (Gate 4); two timeframes of one instrument never count as two replications.
- **Simpler alternative considered**: A single pooled cross-instrument p-value. Rejected — `design.md` evaluates by cell and replication count, not one pooled p-value, to avoid a single instrument driving the result.
- **Assumptions**: none beyond the per-cell CIs.
- **Expected output**: `verdict.json` with per-cell replication flags, per-timeframe distinct-instrument pass counts for each contrast/horizon, and the predeclared `verdict_text`.

## Visualisations

1. **Bucket mean returns vs the middle baseline, with CIs** (1 figure, 2×4 grid: timeframes × instruments). Per cell: mean next-bar return of the top, middle, and bottom buckets with `95%` episode-bootstrap CIs, the middle drift `μ_mid` drawn as the **baseline reference line** (not a zero line), and the pooled `Δ_neutral` excess annotated; train and test side by side. Purpose: shows the core vs-neutral result *as a contrast against the measured middle bucket* and whether top/bottom separate from it, with train/test stability at a glance.
2. **Descriptor minus control (Δ_control) with CIs** (1 figure, grouped by `(instrument, timeframe)`, train/test). Paired `Δ_control` point estimate + CI with a zero line. Purpose: the binding matched-control gate — does range-location beat momentum sign on its own traded bars.
3. **Train/test sign-preservation replication grid** (1 figure, pass/fail heatmap). Rows: `(instrument, timeframe)`; columns: {`Δ_neutral` next-bar, `Δ_control` next-bar, `Δ_neutral` 4-bar, `Δ_control` 4-bar}; cell = replicates (test CI excludes 0 positively AND train same-sign). Purpose: makes the `>= 2`-distinct-instrument verdict mechanically auditable.
4. **4-bar secondary horizon panel** (1 figure, same layout as plot 2 for the 4-bar `Δ_neutral`/`Δ_control`). Purpose: shows whether a multi-bar hold differs from next-bar (horizon-dependent differentiation), under the asymmetric gate.

No additional plots. Eligible counts, gap diagnostics, and the verdict are tabular (`results/`).

## Interpretation Guide

- **If `>= 2` distinct instruments show train/test sign-preserving positive `Δ_neutral` and `Δ_control` on the next-bar primary**, Prior-Range Location carries a control-adjusted directional edge on the analysis set: it advances to EXP-038 robustness. This is a discovery-gate pass, **not** a profitability claim (`design.md` §"Phase Thesis").
- **If `Δ_neutral` passes on `>= 2` instruments but `Δ_control` does not**, the extreme states' returns differ from the measured middle/neutral bucket but the descriptor does not beat trading recent momentum — recorded as state differentiation only; no edge candidate (Gate 4).
- **If the per-side components disagree** (e.g., the top bucket separates from `μ_mid` but the bottom does not), report it explicitly; a pooled `Δ_neutral` pass driven by a single side is weaker evidence and is flagged for EXP-038 rather than read as symmetric continuation.
- **If `< 2` instruments pass `Δ_control` on next-bar AND the 4-bar secondary also fails its control gate**, the state-descriptor thesis is refuted for the cleanest candidate, holdout intact — a clean, useful negative (`design.md` Expected Outcome #2).
- **If next-bar `Δ_control` fails but the 4-bar secondary passes both contrasts on `>= 2` instruments**, the effect is horizon-dependent: reopen at the longer horizon via a new experiment; this is explicitly not thesis refutation.
- **If exactly one instrument passes, or a state the contrast depends on (an extreme state, or the middle baseline for `Δ_neutral`) falls below the eligible floor after the return-eligibility filter**, the result is Inconclusive for that contrast — recorded without relaxing any floor.
- **If the entry-gap diagnostic shows a large share of gap-spanning entries** on a cell, flag it as an executability caveat for EXP-038 (gap-exclusion robustness), but it does not change the primary verdict here.
- **If the episode-bootstrap CI is much wider than the diagnostic row-bootstrap CI**, that quantifies the serial dependence the episode unit corrects for; the episode CI is the one that governs the verdict.

## Complexity Check

- **Statistical tests**: 2 families planned / 3 budgeted — (1) two-sample episode bootstrap for `Δ_neutral` (extreme vs middle-bucket baseline), (2) paired episode bootstrap for `Δ_control`; both re-applied to the 4-bar horizon (same families, second horizon). The per-side components and the row-level diagnostic are the same families, not new ones. No parametric test.
- **Visualisations**: 4 planned / 4 budgeted — bucket means vs `μ_mid` baseline, `Δ_control`, sign-preservation grid, 4-bar panel.
- **New modules**: 0 planned / 1 budgeted. All `python/src` modules reused unchanged; the episode-resampling wrapper lives in `code/run_experiment.py`.

## Data-View Comparison Considerations

### Cross-View Alignment

- Single data view (strict-aggregated real bars per timeframe); no cross-chart-type comparison. Forward-bar selection for returns is by row adjacency within a `CloseTime`-sorted segment; train/test assignment by each bar's own `CloseTime`. No bar-index alignment.

### Real-Price Outcome Discipline

- All returns (`r`, `r4`) and any FE/AE diagnostic use aggregated real OHLC only. No HA or Renko construction price appears. Any return column derived from a synthetic price would be a scope violation to flag.

### Event Density Differences

- `4h` has ≈¼ the bars of `1h`; the eligible-count check (Step 6) is the explicit guard. Strict aggregation drops windows (EXP-034: up to 24% at `4h`), reducing density further — captured in the entry-gap diagnostic and the eligible-count floors. A `4h` cell that fails the floor after filtering is Inconclusive, not a forced negative.

### Regime Stratification

- Out of scope. Buckets are fixed at `0.20/0.80`, not regime-conditioned. Volatility-regime stratification would be scope creep here; any regime structure is absorbed into the per-segment estimates and is a candidate for EXP-038, not EXP-036.
