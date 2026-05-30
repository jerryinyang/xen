# Analysis Plan: Experiment EXP-035

## Objective

Determine whether a Python port of Market Bias (CEREBR) in chart-timeframe mode is **deterministic** (identical under shuffle-then-resort and a convergent two-seeding warmup) and whether its sign-only (bull/bear) states are **count-eligible** at `1h`/`4h` — each state meeting the row floors (`≥100` train, `≥50` test) and the binding independent-episode floors (`≥30` train, `≥15` test) on `≥2` distinct instruments in both segments, without collapsing into one dominant state. No return, excursion, or P&L metric is computed; this is a deterministic readiness survey. The verdict either advances Market Bias to the mid-phase reflection as a return-test candidate or records a readiness-gated no-go. Reference-fidelity status (deterministic-only vs reference-matched) is stated explicitly per the predeclared fallback.

## Methodology

Every statistic is computed per `(instrument, timeframe, aggregation, segment)` cell, under both strict and tolerant aggregation (the binding canonical rule is confirmed at the mid-phase reflection; EXP-035 reports under both so the reflection can lock one rule across the phase). Port-determinism digests and the warmup `W` are computed first, so all readiness counts come from a deterministic, warmed-up series. All methods are exact (counts, episode runs, deterministic hashes, deterministic warmup determination); no inferential test is used, consistent with the `0`-stat-test budget.

### Step 1: Holdout-excluded load and clock-aligned aggregation

- **Method**: `load_analysis_timebars(DATA_DIR, instrument)` (first 70% of `CloseTime`-sorted 1-minute bars). Aggregate to `60`/`240` minutes via `aggregate_ohlc(frame_1m, period_minutes, min_coverage)` for `min_coverage ∈ {None, 0.90}`.
- **Why this method**: Holdout exclusion applied to the 1-minute series before aggregation (`_pipeline-config.md` §"OOS Holdout Rules"). `aggregate_ohlc` is the audited deterministic resampler; `min_coverage` reuses the EXP-034 extension.
- **Simpler alternative considered**: Full-dataset aggregation then split — rejected (materializes holdout). Single timeframe — rejected (`design.md` requires `1h`/`4h` native).
- **Assumptions**: 1-minute `CloseTime` strictly increasing (aggregator sorts internally); aggregated `CloseTime` ordering governs everything; no outcomes computed.
- **Expected output**: per `(instrument, timeframe, aggregation)`, an aggregated real-OHLC frame.

### Step 2: Nested chronological train/test split

- **Method**: 70/30 chronological split on each aggregated series; record the train-cutoff `CloseTime` via `train_cutoff_time`. Segment assignment by each bar's own `CloseTime`.
- **Why this method**: Matches EXP-029/031/033/034 convention; comparable segments.
- **Simpler alternative considered**: Bar-index split — equivalent here, less robust; timestamp assignment preferred.
- **Assumptions**: same temporal-structure assumptions as Step 1. The warmup `W` (Step 4) is discarded **within** the resulting segments; the split is defined on the full aggregated series so the train cutoff is identical with or without warmup.
- **Expected output**: per cell, a `Segment` label and cutoff timestamp.

### Step 3: Market Bias port computation

- **Method**: `market_bias.compute_market_bias(bars_tf)` implements the chart-TF port:
  1. `o,h,l,c = EMA(Open/High/Low/Close, 100)` — causal EMA with Pine `ta.ema` seeding (SMA of the first 100 values, then recursive `α = 2/(100+1)`).
  2. `haclose = (o+h+l+c)/4`; `xhaopen = (o+c)/2`; `haopen[i] = (xhaopen[i−1] + haclose[i−1]) / 2` for `i≥1`, seeded `haopen[0] = (o[0]+c[0])/2` — i.e., the source's `xhaopen[1]`/`haclose[1]` recursion, **not** the standard `haopen[1]` recursion; `hahigh = max(h, haopen, haclose)`; `halow = min(l, haopen, haclose)`.
  3. `o2,c2 = EMA(haopen, 100), EMA(haclose, 100)` (same seeding).
  4. `osc_bias = 100·(c2 − o2)`; `osc_smooth = EMA(osc_bias, 7)`.
  5. `sign_state = bull if osc_bias > 0 else bear` (the measure-zero `osc_bias == 0` tie is carried from the prior bar's state, predeclared; its frequency reported). `four_way_state` per the Pine `sigcolor` switch (strong/weak bull/bear).
- **Why this method**: This is the exact published formula (`docs/planning/market-bias.txt`) with the chart-TF collapse (`request.security` no-ops) applied as `design.md` Candidate 2 specifies. The two flagged port hazards (`xhaopen[1]` recursion; SMA seeding) are implemented explicitly.
- **Simpler alternative considered**: Standard Heiken-Ashi recursion (`haopen[i] = (haopen[i−1] + haclose[i−1])/2`) and a cold EMA seed. Rejected — both would diverge from the published formula; the source uses `xhaopen[1]` and Pine uses SMA seeding.
- **Assumptions**:
  - **Causality / look-ahead prevention**: every EMA value uses only bars `≤` its own index; the HA recursion uses strictly prior bars. No future data.
  - **Determinism**: the port is a pure function of the aggregated bars; no randomness.
  - **NaN handling**: the first `100` bars of each EMA are seed-defined (SMA over the first window); bars before a defined seed are excluded by the warmup.
- **Expected output**: per cell, a table `(CloseTime, Segment, osc_bias, osc_smooth, sign_state, four_way_state)`.

### Step 4: Two-seeding warmup determination

- **Method**: `market_bias.convergence_warmup(bars_tf, floor=300)` computes the four-way state sequence twice — once with Pine SMA seeding, once with a cold first-value seed for every EMA — and returns the smallest index `W` such that the two state-label sequences are identical for all bars `≥ W`, with `W = max(W_converge, 300)`. If the sequences never become identical within the available (train) history, return a non-convergence sentinel. Discard the first `W` bars before all readiness counts.
- **Why this method**: This is the predeclared deterministic warmup rule (amendment 2): it removes the seed-dependent transient of the doubly-recursive EMA-100→EMA-100 chain without any discretionary choice. `300` is the floor (3× the nominal period); convergence may push `W` higher.
- **Simpler alternative considered**: A fixed `300`-bar warmup with no convergence check. Rejected — `300` may be insufficient for a doubly-stacked EMA-100; the convergence rule is the design's amended requirement and is fully predeclared.
- **Assumptions**:
  - **Seed-independence beyond `W`**: a causal EMA's dependence on its seed decays geometrically; the two seedings must converge to bit-identical labels in finite time on real data. Non-convergence is itself a readiness failure (the state would be seed-dependent).
  - **Label-level convergence** (not raw `osc_bias` equality) is the right criterion because the state label is what downstream tests consume.
- **Expected output**: per `(instrument, timeframe, aggregation)`, `W`, `W_converge`, `converged` (bool).

### Step 5: Post-warmup row counts, episode counts, persistence, transitions

- **Method**: After discarding the first `W` bars, within each segment (ordered by `CloseTime`):
  - row count per sign-only state (bull, bear) and per four-way state;
  - independent-episode count per state via run-length encoding of the state sequence (maximal runs of consecutive same-state bars);
  - median and distribution of episode length (bars) per state (persistence);
  - transition counts between states;
  - `dominant_state_share = max state row share` per segment (for the no-collapse check);
  - `osc_bias` magnitude distribution (quartiles) for later neutral-band feasibility (non-gating).
- **Why this method**: `design.md` Gate 2 makes independent episodes the binding denominator for this long-memory descriptor; row counts alone overstate independent information. Run-length encoding is the exact, assumption-free episode count. Persistence/transition/`|osc_bias|` are the secondary diagnostics `design.md` Candidate 2 requests.
- **Simpler alternative considered**: Row counts only. Rejected — explicitly the serial-dependence error `design.md` warns against for persistent states; episodes are required and are expected to be the binding constraint at `4h`.
- **Assumptions**:
  - **Serial dependence acknowledged**: episodes, not rows, are the independence unit; no i.i.d. assumption.
  - **Run definition**: consecutive equal `sign_state` (or `four_way_state`) labels form one episode; segment boundaries and the warmup cutoff terminate runs (conservative — can only split, never merge).
- **Expected output**: per cell, per-state row counts, episode counts, median episode length, transition counts, `dominant_state_share`, and `|osc_bias|` quartiles.

### Step 6: Port-determinism digest (readiness check 1)

- **Method**: Recompute the post-warmup Step-3 table twice per cell: (a) canonical load + aggregate + port; (b) deterministic permutation of the 1-minute rows (`numpy.random.default_rng(42).permutation`) then `sort("CloseTime")` then the same pipeline. SHA-256 over the serialized `(CloseTime, osc_bias[%.12g], osc_smooth[%.12g], sign_state, four_way_state)` per segment. Passes iff canonical and shuffled digests are byte-identical for both segments.
- **Why this method**: SHA-256 over a deterministic serialization is the canonical reproducibility check (EXP-020/029/033). Shuffle-then-resort probes any hidden row-order dependence in the load→aggregate→port chain.
- **Simpler alternative considered**: Comparing state counts only — rejected; distinct series can share counts. Full-table digest catches per-bar divergence.
- **Assumptions**: canonical serialization (fixed column order, `%.12g` floats, explicit NaN token); determinism of `aggregate_ohlc` and the port.
- **Expected output**: per cell, `digest_canonical`, `digest_shuffled`, `digests_match`.

### Step 7: Reference-fidelity check (predeclared fallback)

- **Method**: If an exported TradingView reference series (`osc_bias`/state) for any instrument/timeframe exists under `docs/planning/` at implementation time, align by `CloseTime` and report the max absolute `osc_bias` deviation and the state-label agreement share. Otherwise, record `reference_available = False`, claim only "deterministic re-implementation of the published Pine formula," and attach the unverified-fidelity caveat to every readiness conclusion.
- **Why this method**: Amendment 4 pre-commits the fallback. The port has two known fidelity hazards (`xhaopen[1]` recursion; SMA seeding) that cannot be externally verified without reference values; the experiment must not over-claim Pine-equivalence it cannot demonstrate.
- **Simpler alternative considered**: Asserting Pine-equivalence from formula inspection alone. Rejected — determinism ≠ fidelity; an undetected port error would be deterministic but wrong.
- **Assumptions**: if a reference exists, it was exported in chart-TF mode with the same `100/100/7` parameters.
- **Expected output**: `reference_available` (bool); if true, `max_abs_osc_dev` and `state_agreement_share`; the explicit claim string.

### Step 8: Aggregate verdict

- **Method**: Apply `scope.md` §"Aggregate Verdict" mechanically: a `(instrument, timeframe)` passes iff checks 1–5 (determinism, warmup convergence, row floor, episode floor, no-collapse) hold for both segments. Market Bias passes readiness iff `≥2` distinct instruments pass at `≥1` timeframe under an admissible aggregation; else readiness-gated no-go; else inconclusive per the single-instrument / fixable-determinism clauses. Apply the fast-stop conditions.
- **Why this method**: Mechanical, pre-registered, using only determinism and count evidence — never return performance (none exists). Matches `design.md` Gates 1, 2, 3, 7.
- **Simpler alternative considered**: Passing on four-way states. Rejected — sign-only is the primary descriptor (`design.md` Candidate 2); four-way is secondary diagnostic and expected to churn.
- **Assumptions**: none beyond determinism of the readiness tables.
- **Expected output**: `verdict.json` with per-`(instrument, timeframe)` pass flags, passing-instrument lists, `reference_available`, the claim string, and `verdict_text` (one of the three predeclared strings).

## Visualisations

1. **Port determinism + warmup panel** (1 figure, 2 subplots). Left: pass/fail grid of `digests_match` per `(instrument, timeframe, segment)`. Right: warmup `W` per `(instrument, timeframe)` with the `300` floor line and a marker for non-convergence. Purpose: establishes the series is deterministic and warmed-up before counts are read.
2. **`osc_bias` series + state shading** (1 figure, one representative `(instrument, timeframe)`, post-warmup, bounded sample). `osc_bias` and `osc_smooth` lines with sign-state background shading. Purpose: visual sanity check that the port produces the expected bull/bear regime structure and shows persistence; sampled deterministically if the series is long (bounded plotting).
3. **Sign-only episode-count readiness grid** (1 figure, heatmap/pass-fail). Columns: `(instrument, timeframe, segment)`; rows: bull, bear. Cell: independent-episode count, with the `30` train / `15` test floors as the pass/fail threshold. Purpose: the binding readiness verdict, mechanically auditable.
4. **Persistence + four-way diagnostic** (1 figure, 2 subplots). Left: median episode length (bars) per sign state per `(instrument, timeframe)`. Right: four-way state episode counts per `(instrument, timeframe, segment)` (secondary diagnostic, showing the strong/weak axis churn). Purpose: documents persistence and confirms four-way is the weaker descriptor.

No additional plots. Determinism digests, transition counts, `|osc_bias|` quartiles, and the verdict are tabular (`results/`).

## Interpretation Guide

- **If `≥2` distinct instruments pass checks 1–5 at `≥1` timeframe under an admissible aggregation**, Market Bias is deterministic and its sign-only states are count-eligible: it advances to the mid-phase reflection as a return-test candidate. State the reference-fidelity status (deterministic-only vs reference-matched) in the conclusion. Record passing instruments, `W` per cell, and episode counts in `results.md`.
- **If the port cannot be made deterministic for an unfixable reason (check 1)**, or the two seedings never converge within train history (check 2), Market Bias is a readiness-gated no-go: the state would be seed- or order-dependent and cannot carry a defensible return claim. No EXP-037 opens.
- **If independent-episode counts are inadequate on `≥2` distinct instruments (check 4)** at every timeframe, Market Bias is a readiness-gated no-go on the power constraint — expected to be the most likely failure mode at `4h` given the stacked EMA-100 persistence. REFUTED for the count-eligibility hypothesis; holdout-preserving.
- **If a single sign state holds `>0.95` of post-warmup bars (check 5)**, the state has collapsed and carries no usable contrast — readiness-gated no-go.
- **If exactly one instrument passes** on an otherwise promising timeframe, the result is INCONCLUSIVE (the `≥2` distinct-instrument rule is unmet); if no timeframe reaches `≥2`, the aggregate verdict is the readiness-gated no-go.
- **If determinism fails for a fixable implementation reason**, INCONCLUSIVE pending a fix and re-run before any verdict — never waved through.
- **Four-way churn** (low episode counts / very short episodes on the strong/weak axis) is an expected secondary finding, not a failure; sign-only is the gated descriptor. Report it to confirm the `design.md` expectation that the strong/weak axis adds little information.

## Complexity Check

- **Statistical tests**: 0 planned / 0 budgeted. All readiness checks are exact counts, exact episode runs, deterministic SHA-256 digests, and a deterministic warmup determination. No bootstrap or inferential test is needed for a determinism/count survey.
- **Visualisations**: 4 planned / 4 budgeted — determinism+warmup panel, `osc_bias` series+shading, sign-only episode-count grid, persistence+four-way diagnostic.
- **New modules**: 1 planned / 1 budgeted — `python/src/market_bias.py` (the single new module `design.md` reserves for the port). Aggregation and loading reuse existing modules.

## Data-View Comparison Considerations

### Cross-View Alignment

- The only cross-view operations are (a) the canonical vs shuffled determinism comparison and (b) the optional reference comparison — both aligned strictly on `CloseTime`, never bar index. Train/test assignment is by each bar's own `CloseTime`.

### Real-Price Outcome Discipline

- No returns, excursions, hit rates, or P&L are computed. Market Bias is derived from EMA-smoothed construction values of the real OHLC, but these are used only to label states; no outcome is computed from them or from any synthetic price. The readiness tables contain no return column by construction; any such column is a scope violation to be flagged. At EXP-037 (return test, post-reflection) all outcomes will use the aggregated real OHLC.

### Event Density Differences

- `4h` produces ≈¼ the bars of `1h`, and Market Bias's stacked smoothing produces fewer, longer episodes than raw direction; the episode floor is the explicit guard. The four-way split further fragments density and is reported as a diagnostic, not gated.

### Regime Stratification

- Out of scope. States are defined by `osc_bias` sign and its relation to `osc_smooth`, not by an external regime label. Any regime structure is absorbed into the per-segment episode counts; stratification would be scope creep.
