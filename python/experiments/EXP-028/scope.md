# Experiment: EXP-028 — Faithful Selective AVWAP Strategy Re-Screen

## Hypothesis

Under the frozen EXP-027 event-level evaluation method, the faithful selective AVWAP strategy — unchanged from the EXP-023 baseline — shows positive event-level edge (per-event matched-control expectancy > 0) on at least one domain (5m, 1h, or 4h), using only the first-70% analysis set and predeclared inference.

## Question

When the ~6%-active AVWAP selective event strategy is evaluated under a fit-for-purpose event-level method (per-event matched-control expectancy, regime-cluster bootstrap + stratified sign-permutation + Holm, frozen from EXP-027 METHOD_VALID), does it exhibit a detectable per-event edge on any domain, or is it a clean negative — resolving the EXP-023 framing-defect ambiguity?

## Strategy Definition (unchanged from EXP-023 baseline)

The strategy is the registered `CF-AVWAP-001/HYP-004` (re-screen `HYP-004-R`), with zero parameter changes from the Phase 004/005 baseline:

| Component | Specification |
|-----------|--------------|
| Regime detector | MA crossover, fast 20 / slow 50, on domain `Close` |
| AVWAP source | Typical price `(High + Low + Close) / 3` |
| AVWAP weight | `TickVolume ** 0.75` |
| Band spread | Median absolute deviation from anchored typical-price path |
| Band multiplier | 1.0 |
| Bounce definition | EXP-020: arm on close below AVWAP (bullish)/above AVWAP (bearish); trigger on close crossing back |
| Exit rule | EXP-022 band-target/trend-change completion rule |
| Position per event | Enter at trigger in bounce direction; hold until exit rule fires |
| Pyramid bounces | **Included** as individual events, tagged `is_pyramid_bounce` (reported as a diagnostic split, not a gate). Predeclared as closer to the original concept and matching the reused EXP-020/021/022 observations — see note below. |
| Return computation (binding) | EXP-022 own-exit **lifetime** return: direction-signed log return on real domain Close from entry (trigger close) to the band-target/trend-change exit close, in bps. Reuses EXP-022 `lifetime_bps`, reconciled to `10000 * direction * ln(exit_close / entry_close)`. |
| Cost | None (this is an event-level edge test, not P&L) |

**Faithfulness constraint:** The detector, AVWAP weights, band rule, bounce definition, and exit (completion) rule are identical to the EXP-020/021/022/023 substrate. The only change vs. EXP-023 is the **evaluation method** (per-bar frozen suite → event-level EXP-027 inference) and one predeclared, justified faithfulness correction: **pyramid bounces are included**. No parameter may be tuned, adjusted, or re-selected after reading the real AVWAP outcomes.

**Pyramid inclusion (predeclared, Phase 006 §4 — "closer to the original, not a tuning lever"):** Pyramid bounces are *included*, not filtered. (1) They contributed to every reused upstream observation — EXP-020 events are ~50% pyramid (10,461/20,911), EXP-021 applied no pyramid filter, and EXP-022's SUPPORTED lifetime result spans both `is_pyramid_bounce` event and control rows. (2) The original `anchored-vwap.md` records every bounce individually and tags pyramids for special evaluation; EXP-023's pyramid suppression was the deviation, so including them is closer to the original. (3) EXP-027 calibrated the inference on pyramid-style clustered placement, so the regime-cluster bootstrap (resampling `regime_id` clusters, never individual events) absorbs the extra within-regime dependence. `is_pyramid_bounce` is retained as a reported diagnostic split.

## Scope Boundaries

- **Data Views**:
  - Real 5m (strict), 1h / 4h (`min_coverage = 0.90`) OHLC domain bars rebuilt from the first-70% analysis slice of 1-minute time bars (`xen.bar_aggregator`), identical to EXP-020/021/022/027.
  - Real AVWAP bounce events from `python/experiments/EXP-020/results/avwap_events.csv` (trigger info, anchor context, regime scaffolding, target levels).
  - Real lifetime completion outcomes from `python/experiments/EXP-022/results/lifetime_observations.csv` (exit type, completion bar, bars-to-completion, lifetime return).
  - EXP-020 regime scaffolding (`avwap_state_summary.csv`, EXP-020 domain frames) for matched-control construction.
  - No chart-type views.
- **Candidate family / registry**: `CF-AVWAP-001/HYP-004-R` (re-screen of HYP-004 under corrected evaluation). Registered in `docs/signal-registry/multiplicity-registry.md` (Phase 006 batch). Consumes 0 new candidate-family slots — it corrects the evaluation vehicle for the existing baseline strategy.
- **Parameters**:
  - domains: 5m strict coverage; 1h and 4h `min_coverage = 0.90` (matches EXP-020/021/022/027);
  - instruments: BTCUSD, EURUSD, USTEC, XAUUSD (all four — all reportable in EXP-021/022);
  - inference: identical to the frozen EXP-027 method (see Method section below);
  - primary α₀ = 0.05; α grid {0.10, 0.05, 0.01};
  - 1000 regime-cluster bootstrap resamples;
  - 1000 stratified paired sign-permutation resamples;
  - Holm adjustment across the 3 domains;
  - reportability thresholds: ≥30 reportable events per domain, ≥8 per direction, ≥3 of 4 instruments (identical to EXP-021/027);
  - fixed seeds; deterministic generation; determinism replay check.
- **Time range**: Full dataset with nested chronological split. First 70% = analysis set; final 30% = global holdout, never used.
- **Global holdout**: The final 30% of each chronologically ordered source file must not be loaded, inspected, emitted, plotted, counted, or used in any capacity.
- **Look-ahead bias prevention**:
  - All temporal ordering by domain-bar `CloseTime`.
  - AVWAP events were generated by the EXP-020 look-ahead-safe state machine.
  - Per-event returns use the actual strategy exit (known at or after entry, from sequential domain bars).
  - Matched controls are selected using only regime id, anchor age, and timestamp known at the event trigger bar. Control forward returns are outcomes.
  - No future information relative to the event trigger influences control selection or event classification.
- **Real-price outcome discipline**: All event-level returns and control returns are direction-signed log returns on real domain `Close` prices (`10000 * direction * ln(exit_close / entry_close)` in bps). No synthetic chart prices (HA, Renko, Line Break). No strategy P&L from brick prices or HA prices. This is a real-price edge test, not a synthetic-price diagnostic.
- **Exclusions**:
  - The frozen per-bar qualification suite and any per-bar MDE floor (explicitly not the evaluation vehicle — the Phase 005 defect);
  - Any comparison of per-event aggregated returns to per-bar floors (the EXP-024 fork-(b) category mismatch);
  - The asymmetric endogenous-exit-vs-fixed-window construction as a *binding* gate — it is the non-binding, calibration-gated SECONDARY only (a binding use would re-commit the Phase-005 out-of-envelope error);
  - Any sweep, tuning, threshold/metric/parameter reselection, or post-result re-choice against EXP-028 outcomes (predeclared once, measured once);
  - Exit overlays, detector/anchor branches (`/LB`, `/MB`, `/ATR`, `/ANCHOR`), `/ALPHA`, `/BAND` sensitivity, cross-timeframe or XTF variants (all deferred);
  - HYP-001 (direct AVWAP line S/R) — remains untested, out of scope;
  - Activity rates outside the sparse envelope (method validity not declared there);
  - Percentage improvement against a zero or near-zero baseline — report bps effects, absolute rates, and CIs;
  - Transaction costs, slippage, stops, position-sizing / position-pyramiding P&L management (this is an event-level edge test, not a deployable strategy P&L). Note: pyramid *bounce events* are included as individual observations (see Strategy Definition) — only position-management pyramiding is excluded.

## Frozen Evaluation Method (EXP-027, METHOD_VALID)

The evaluation method is frozen as validated in EXP-027. **No aspect of the method — inference pipeline, decision rule, bootstrap parameters, permutation procedure, Holm structure, reportability thresholds, Evidence-FOR rule — may be changed after reading the real AVWAP event outcomes.**

The evaluation is a **dual gate**. The PRIMARY gate is **binding**; the SECONDARY is a calibrated, non-binding diagnostic. This keeps the binding verdict inside the construction EXP-027 actually calibrated (symmetric, exchangeable-under-null), while retaining the strategy's endogenous-exit-vs-fixed-window view only after its own null is shown controlled.

#### PRIMARY (binding): symmetric own-exit matched-control lifetime excess

| Element | Specification |
|---------|--------------|
| Unit of analysis | Each AVWAP bounce event (not each bar), pyramids included |
| Per-event return | EXP-022 own-exit **lifetime** return (entry trigger close → band-target/trend-change exit close), direction-signed log bps; reuses EXP-022 `lifetime_bps` |
| Matched controls | EXP-022 `role=control` rows for the same `(instrument, domain, regime_id, event_trigger_idx)` — each control completed under the **same** exit rule from its own non-trigger start (symmetric construction → mean-zero null excess); `MIN_CONTROLS=3` required for reportability |
| Per-event paired excess | `event_lifetime_bps − mean(control_lifetime_bps)` |
| Instrument-level aggregation | Event-weighted mean paired excess per instrument |
| Domain-level aggregation | Equal-weight mean across reportable instruments of instrument-level means |
| Inference | 95% regime-cluster bootstrap CI (1000 resamples, `regime_id` clusters within instrument×direction strata) |
| Null hypothesis test | Stratified paired sign-permutation p-value (1000 resamples) — exact under the symmetric construction |
| Multiplicity | Holm adjustment across the 3 domains |
| Secondary-horizon stability | EXP-021 fixed-horizon {1,6} excess (same events, EXP-027-calibrated symmetric construction) supplies the `decide_label` `effect_h1`/`effect_h6` slots — a PRIMARY FOR is downgraded to INCONCLUSIVE if the short-horizon reaction is jointly negative |
| Decision rule (Evidence-FOR) | `effect > 0` AND `CI_low > 0` AND `Holm_p ≤ α` AND secondary-horizon stable |
| Evidence-AGAINST | Effect ≤ 0, or CI upper bound < 0, or Holm_p > α — **only when adequately powered** (in-experiment CI half-width + event counts; **not** the EXP-027 numeric MDE, which is in H=3 units) |
| INCONCLUSIVE | Under-powered, mixed evidence not meeting FOR/AGAINST, or secondary-horizon instability |

FPR control for the PRIMARY gate rests on sign-permutation exactness under the symmetric (own-exit event vs own-exit control) construction plus EXP-027's sparse-count validation of the same inference machinery.

#### SECONDARY (non-binding, calibrated): endogenous-exit event vs fixed-window control

The EXP-023-style construction (event return to its endogenous EXP-022 exit; control = fixed window of the event's realized hold). It carries interpretive weight **only if** a predeclared in-experiment placebo-null check — placebo events + the same exit rule + the same fixed-window control, run before reading the real secondary excess — shows FPR ≤ α₀ and null mean-excess ≈ 0 in every domain. Otherwise it is reported `NOT_CALIBRATED` with zero weight. It never overrides the PRIMARY.

### Companion: Exposure-Aware Equity-Curve vs Baseline (Non-Gating)

- Construct the selective strategy's realized return series (in-position during events, flat otherwise).
- Construct the exposure-matched baseline: same number of trades taken at event-matched-control bars, identical hold duration, identical direction signing.
- Compare via cumulative log-equity difference and downside-risk-adjusted ratio (Sortino-style, as in EXP-027).
- Raw 100%-invested buy-hold is annotated context only, never the comparator — preventing re-import of the exposure/dilution artifact.
- Companion is **non-gating** — it informs interpretation but does not decide the hypothesis verdict. Companion sanity criteria (predeclared): no systematic false advantage under a null-equivalent (block-permuted returns; measured only for diagnostics, not for verdict) and plausible behavior.

## Success / Failure Criteria

Precision thresholds (per EXP-027/EXP-003): a cell is reportable only if the event count ≥ 30 per domain, ≥ 8 per direction, ≥ 3 of 4 instruments, and Wilson TPR/TE half-widths ≤ 0.05 where applicable.

All verdicts bind on the **PRIMARY** gate (symmetric own-exit lifetime excess). The SECONDARY and companion annotate but never decide.

- **Evidence FOR — EVAL_SUPPORTED** (all hold):
  - At least one domain is PRIMARY Evidence-FOR at α₀ = 0.05 (effect > 0, CI_low > 0, Holm_p ≤ 0.05, secondary-horizon stable);
  - The real AVWAP per-event own-exit matched-control excess exceeds zero with controlled error on that domain;
  - Companion equity behavior is consistent with the gate (no contradictory pattern).
  - **Phase outcome: EVAL_SUPPORTED** — the faithful strategy has a positive event-level edge on ≥1 domain under a fit-for-purpose, in-envelope yardstick.
- **Evidence AGAINST — EVAL_REFUTED** (both hold):
  - No domain is PRIMARY Evidence-FOR at α₀ = 0.05;
  - Every reportable domain has PRIMARY excess ≤ 0 or a CI excluding a material positive effect, **with adequate in-experiment power** — judged from the bootstrap CI half-width and event counts (≥30/domain, ≥8/direction, ≥3/4 instruments). The EXP-027 numeric MDE (1/4/32 bps) is **not** the lifetime power threshold (it is in H=3 units; lifetime returns are larger-magnitude/higher-variance) — it applies only to the fixed-horizon secondary-stability anchor.
  - **Phase outcome: EVAL_REFUTED** — the strategy-as-a-whole (entry timing + EXP-022 exit) shows no excess over a same-exit matched control under the correct yardstick.
  - **Interpretation bound (no overreach):** EXP-021 already showed a *positive* event-timing reaction at fixed horizon, so EVAL_REFUTED is **not** "the AVWAP bounce event has no edge"; the likely locus is the exit rule (EXP-024: trend-change cuts losers). Routes to FAMILY_REVIEW (Phase 006 §7).
- **Inconclusive**:
  - No domain reaches PRIMARY Evidence-FOR, but power limitations (thin 4h events, directional imbalance, insufficient reportable instruments) or secondary-horizon instability prevent a clean AGAINST reading;
  - Companion behavior contradicts the gate in an uninterpretable way (not attributable to known limitations).

## Complexity Budget

- Max statistical tests: **4** (regime-cluster bootstrap CI; stratified paired sign-permutation with Holm; event-count reportability table; equity companion bootstrap difference — reuses test 1's machinery).
- Max visualisations: **4** (per-domain event-level expectancy with CIs; equity-curve companion with exposure-matched baseline; event-count and direction-balance diagnostic; summary dashboard with verdicts).
- Max new code modules: **1 experiment-local script** under `python/experiments/EXP-028/code/run_experiment.py` that loads real AVWAP events, computes per-event returns via the EXP-022 exit rule, runs the frozen EXP-027 inference pipeline, produces results and plots. Reuse EXP-027's `event_method.py` by import or copy (unchanged — its inference pipeline is the frozen method). No new or modified shared `python/src/xen/` module.

## Data Requirements

### Required Upstream Artifacts

| Artifact | Path | Purpose |
|----------|------|---------|
| EXP-020 substrate gate | `python/experiments/EXP-020/results/run_metadata.json` | Dependency: must be SUPPORTED_FULL |
| EXP-020 AVWAP events | `python/experiments/EXP-020/results/avwap_events.csv` | Bounce event triggers, anchors, targets, regime scaffolding |
| EXP-020 state summary | `python/experiments/EXP-020/results/avwap_state_summary.csv` | Regime intervals for matched-control scaffolding |
| EXP-020 domain readiness | `python/experiments/EXP-020/results/domain_readiness.csv` | Domain/instrument reportability |
| EXP-022 lifetime observations | `python/experiments/EXP-022/results/lifetime_observations.csv` | Per-event completion outcomes (exit type, exit bar, lifetime return) |
| EXP-022 completion summary | `python/experiments/EXP-022/results/lifetime_completion_summary.csv` | Exit-type distribution |
| EXP-027 validation | `python/experiments/EXP-027/results/run_metadata.json` | Dependency: must be METHOD_VALID |
| 1-minute time bars | `data/timebars/timebars_*.parquet` | Domain bar reconstruction |
| EXP-027 `event_method.py` | `python/experiments/EXP-027/code/event_method.py` | Frozen inference pipeline (import or copy unchanged) |

### Anti-Overfitting / No-Tuning Fence

All parameters — strategy parameters, method parameters, decision rule, inference settings — are fixed before reading EXP-028 results. The experiment reads real AVWAP outcomes once and runs the frozen pipeline to produce a verdict. No parameter is varied post-hoc. No alternative metric is computed after seeing the effect direction.

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

### Expected Output Files

```
python/experiments/EXP-028/results/
- event_level_results.csv        # per-domain effect, CI, p-value, Holm-p, verdict
- event_diagnostics.csv          # event counts, direction balance, reportability
- equity_companion.csv           # equity-curve comparison
- run_metadata.json              # status, dependency, verdict, seeds
python/experiments/EXP-028/plots/
- event_expectancy.png           # per-domain effect with CIs
- equity_companion.png           # strategy vs exposure-matched baseline
- event_diagnostics.png          # event count and balance diagnostic
- verdict_summary.png            # headline verdict per domain
```

## Suggested Direction

**PRIMARY (binding):** Use EXP-022 `lifetime_observations.csv` directly — it already pairs each event (`role=event`, pyramids included) with its own-exit matched controls (`role=control`) via `(instrument, domain, regime_id, event_trigger_idx)`, both completed under the same band-target/trend-change exit. Per-event excess = `event_lifetime_bps − mean(control_lifetime_bps)`. Push through the frozen EXP-027 inference tail (regime-cluster bootstrap, sign-permutation, Holm, Evidence-FOR rule); feed the EXP-021 fixed-horizon {1,6} excess into the secondary-horizon-stability slots. **SECONDARY (non-binding):** the endogenous-exit-event vs fixed-window-control construction, reported with weight only if its predeclared placebo-null check passes. Build the equity companion exposure-aware (identical to EXP-027). No tuning, no alternative specifications, no post-hoc metric changes. If the PRIMARY is EVAL_SUPPORTED on any domain, the Phase 006 EVAL_SUPPORTED outcome is delivered; if EVAL_REFUTED on all reportable domains, the strategy-with-exit is a clean negative and `CF-AVWAP-001` moves to FAMILY_REVIEW (not a statement that the bounce event lacks edge — EXP-021 shows it has one at fixed horizon).
