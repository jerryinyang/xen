# Experiment: EXP-027 — Event-Level Evaluation Method: Definition and Sparse-Regime Calibration

## Hypothesis

A predeclared **event-level** evaluation method — with **per-event matched-control
expectancy** as the binding decision statistic (reusing the EXP-021/022
regime-cluster bootstrap + stratified paired sign-permutation + Holm inference and
Evidence-FOR rule), and an exposure-aware **equity-curve-vs-buy-hold** companion —
exhibits **controlled false-positive error** (empirical FPR ≤ α₀ = 0.05 under
known-null sparse event processes) and **recovery** (a finite empirical
**event-level MDE** at TPR ≥ 0.80 while FPR ≤ α₀) across the 5m / 1h / 4h domains,
within a sparse activity envelope bracketing the real AVWAP signal
({~3 %, ~6 %, ~12 %} active). If so, the method is a fit-for-purpose yardstick for
re-screening the faithful selective AVWAP strategy in EXP-028; if not, no
fit-for-purpose yardstick yet exists and EXP-028 does not run under it.

## Question

Does an event-level evaluation method, calibrated to the activity regime of a
sparse (~6 %-active) event signal, have controlled error and the power to detect a
planted per-event edge — so that it can replace the per-bar continuous-position
frozen suite (which was calibrated only for ≥80 %-active series, EXP-005) as the
evaluation vehicle for the AVWAP selective event strategy?

This is a **methodology / calibration experiment** (`CF-AVWAP-001/METHOD-001`). It
consumes **no candidate-screening multiplicity slot**. It is in the lineage of
EXP-001/002 (substrate + golden-fixture) and EXP-003/005 (operating-characteristic
calibration), but the unit of analysis is **per-event**, not per-bar, and the
target regime is **sparse**, not high-activity.

## Background and binding correction constraints

Phases 004/005 screened/diagnosed a ~6 %-active event signal through a **per-bar
continuous-position referee** whose FPR/TPR/MDE map was validated only for
≥80 %-active series. The negative results (EXP-023, EXP-024 fork-(b), EXP-025) were
dominated by ~16× per-bar denominator dilution and category mismatches, not by
absence of signal (root cause:
`docs/code-reviews/2026-06-08-avwap-evaluation-framing-divergence-review.md`). The
defect was the **yardstick**, not the trade logic.

EXP-027 therefore observes the following hard constraints, each a direct response
to a documented prior-run failure mode:

1. **Per-event unit of analysis end-to-end.** Every estimand, denominator, null,
   and decision uses per-**event** quantities. The per-bar continuous-position
   floor and the frozen per-bar suite are **explicitly not** the vehicle here and
   are not invoked, compared against, or used as a floor anywhere in this
   experiment.
2. **No category mismatches.** A cumulative / multi-bar per-event return is never
   compared to a per-bar floor (the EXP-024 fork-(b) error). All comparisons are
   per-event vs. per-event (event vs. matched control) or per-event-aggregated vs.
   an exposure-matched baseline.
3. **Anti-overfitting / no metric-shopping.** The method is defined and calibrated
   on **synthetic null + planted-edge substrates only** — it never reads the real
   AVWAP bounce-event outcomes. It is **frozen before EXP-028 reads any real
   candidate result.** A failed calibration is a valid result, not license to try
   another metric.
4. **Activity-envelope match made explicit.** The method's validity is declared
   only over the measured sparse activity range; applying it outside that range is
   itself flagged as out-of-envelope (the precise error Stage 4 governance must
   catch this time).
5. **Zero-baseline discipline.** The null per-event excess is exactly 0 bps. Report
   **bps differences and rate CIs**; never compute percentage improvement over a
   zero or near-zero control mean.

## Scope Boundaries

- **Data Views**: Real 5m, 1h, and 4h domain OHLC bars rebuilt from the first-70 %
  analysis slice of 1-minute time bars (`xen.bar_aggregator`). EXP-020 **regime
  intervals** (`avwap_state_summary.csv` / regime summary, plus anchor-age context)
  are used **only as the matched-control scaffolding** — instrument / domain /
  regime-direction clustering and anchor-age matching, identical to EXP-021/022. No
  chart-type views.
  - **Anti-overfitting fence on EXP-020 inputs**: the real `avwap_events.csv`
    bounce **outcomes** (returns, lifetime completions, target hits) are **not read
    into the calibration**. The documented aggregate **activity rate** (~6 %; per
    EXP-024 6.17 / 5.73 / 5.67 %) is used only to set the predeclared sparse
    activity grid; real event **locations and outcomes** are never the signal under
    test. The signal under test is synthetic (placebo + planted-edge).
- **Candidate family / registry**: `CF-AVWAP-001/METHOD-001`, registered in
  `docs/signal-registry/multiplicity-registry.md` (Phase 006 batch). Methodology
  experiment; **0 candidate-screening slots**.
- **Parameters**:
  - domains: 5m strict coverage; 1h and 4h `min_coverage = 0.90` (matches
    EXP-020/021/022);
  - instruments: BTCUSD, EURUSD, USTEC, XAUUSD (all four — every EXP-020
    instrument/domain cell was reportable);
  - **activity-regime grid (declared validity range)**: {~3 %, ~6 %, ~12 %} active,
    bracketing the real signal; **~6 % is the primary calibration point**;
  - **synthetic null generators (≥2, structurally different)**: (1) **placebo
    events** placed at the target activity rate within real EXP-020 regime
    intervals on **real** first-70 % returns, with **no planted edge**, preserving
    realistic sparse clustering (intra-regime placement, clustered/pyramid-style
    placements allowed); (2) a second structurally different null (e.g.
    block-permuted real returns under the same placebo placement) for two-null
    agreement (EXP-001 precedent). Exact generators fixed in Stage 2;
  - **planted-edge mechanism**: a known direction-signed per-event drift added to
    placebo-event outcomes over a **bps edge grid** (decoupled from EXP-021's
    observed magnitudes); the per-event outcome window matches the strategy's hold
    semantics (representative fixed-horizon and/or lifetime-style window, fixed in
    Stage 2);
  - **inference (reused from EXP-021/022, unchanged in structure)**: matched
    controls = same `regime_id`, not a (placebo) trigger bar, outside a fixed
    exclusion window, ≥3 controls required, up to 5 selected by nearest anchor age
    then timestamp; domain statistic = unweighted mean across reportable
    instruments of each instrument's event-weighted mean direction-signed paired
    difference (bps); 95 % regime-cluster bootstrap CI; stratified paired
    sign-permutation p-value; **Holm** adjustment across the three domains;
  - **error grids**: α grid {0.10, 0.05, 0.01} with **primary α₀ = 0.05**;
    bootstrap resamples and permutation/draw counts at EXP-021/022/EXP-003 scale
    (≈1000 inner resamples; null/positive draw counts per cell fixed in Stage 2 to
    meet the precision thresholds below);
  - fixed seeds; deterministic generation; a determinism replay check.
- **Time range**: Full dataset with nested chronological split. First 70 % =
  analysis set (further split 70/30 train/test only where the method requires it);
  final 30 % = global holdout, never used.
- **Global holdout**: The final 30 % of each chronologically ordered source file
  must not be loaded, inspected, emitted, plotted, counted, or used in any
  capacity.
- **Look-ahead bias prevention**: regime intervals and anchor ages come from the
  EXP-020 look-ahead-safe substrate; domain bars ordered by `CloseTime`; placebo
  events and controls are placed/selected using only timestamp, regime direction,
  and anchor age known at that bar; future closes are used only as measured
  outcomes; the planted drift is added to outcome returns, never used in placement
  or matching.
- **Real-price outcome discipline**: all outcomes are direction-signed log returns
  in bps on **real domain `Close`** prices
  (`10000 * direction * log(Close[t+h] / Close[t])`). No synthetic chart prices, no
  Heiken-Ashi / Renko prices, no transaction costs / stops / fills / sizing
  (this is method calibration, not strategy P&L).
- **Exclusions**:
  - the real AVWAP bounce-event **outcomes** (read only in EXP-028, after the
    method is frozen);
  - the frozen per-bar suite and any per-bar continuous-position floor as an
    evaluation vehicle, comparator, or sanity floor;
  - the equity-curve companion as a **pass-gate** (it is a calibrated,
    non-gating companion only);
  - any sweep, tuning, threshold/metric/parameter reselection, or post-result
    re-choice against Phase 006 outcomes;
  - HYP-001 (direct AVWAP line S/R), exit overlays, detector/anchor branches,
    ALPHA/BAND/XTF/MA-DOMAIN sensitivity;
  - activity rates outside the bracketed sparse grid (method declared invalid
    there — out of envelope);
  - percentage improvement against a zero / near-zero baseline.

## Method definition — required design elements (fixed before measurement)

Per the Phase 006 design, EXP-027 must fix these objects before any measurement.

1. **Primary per-event estimand and denominator (the binding gate).**
   Per-event direction-signed real-price **matched-control excess** in bps:
   for each (placebo) event, `excess = event_return_bps − mean(matched_control_return_bps)`
   over the event's defined outcome window. Aggregated to the domain by the
   EXP-021 equal-weight-instrument estimator. **Denominator = number of reportable
   matched events** (events with a valid outcome window and ≥3 matched controls) —
   **never a bar count**. Null excess = exactly 0 bps.

2. **Equity-curve construction and buy-hold baseline (companion, non-gating).**
   The selective strategy's realized return **series** (in-position only during
   events, flat otherwise) compared to buy-hold on an **exposure-aware /
   risk-adjusted** basis (e.g. return-per-unit-risk and/or an exposure-matched
   baseline) so a ~6 %-exposed curve is **not** naively compared to a 100 %-invested
   buy-hold — this avoids re-introducing the exposure/dilution artifact that broke
   the per-bar framing. Exact normalization fixed in Stage 2. Calibrated for null
   behavior (no false advantage under placebo events) and reported alongside the
   gate, but it does **not** decide METHOD_VALID.

3. **Null / control generators for a sparse event process.** As in Parameters: a
   placebo-on-real-regime null (primary) plus a second structurally different null,
   both at each activity grid point, with no planted edge → FPR = fraction of null
   draws yielding Evidence-FOR.

4. **Decision rule and multiplicity adjustment.** The per-draw verdict is the
   **EXP-021 Evidence-FOR rule** applied to the per-event expectancy gate:
   effect > 0 **and** 95 % regime-cluster bootstrap CI lower bound > 0 **and**
   Holm-adjusted (across the 3 domains) permutation p ≤ α₀. Evidence-AGAINST /
   INCONCLUSIVE follow the EXP-021 structure. FPR = P(FOR | null draw);
   TPR = P(FOR | planted-edge draw); **event-level MDE** = smallest planted
   per-event edge (bps) with TPR ≥ 0.80 at FPR ≤ α₀.

5. **Activity-regime validity range.** {~3 %, ~6 %, ~12 %} active; the method is
   declared valid only over the sub-range where FPR is controlled **and** a finite
   MDE exists.

## Success / Failure Criteria

Precision thresholds (per EXP-003/005 precedent): a calibration cell is usable only
if the FPR Wilson 95 % half-width ≤ 0.03 and the TPR Wilson 95 % half-width ≤ 0.05;
under-powered cells are reported as such and excluded from FOR/AGAINST claims.

- **Evidence FOR — METHOD_VALID** (all hold):
  - **Controlled error**: empirical gate FPR ≤ α₀ = 0.05 (Wilson upper bound within
    the precision tolerance) under **both** null generators at the ~6 % primary
    activity point, in **every** domain, and not materially exceeding α₀ across the
    {~3 %, ~6 %, ~12 %} bracket;
  - **Recovery**: a **finite** event-level MDE exists (TPR ≥ 0.80 at FPR ≤ α₀) at
    the ~6 % point in **every** domain;
  - **Determinism**: deterministic replay equality on a re-run cell;
  - **Companion sanity (non-gating)**: the equity-curve-vs-buy-hold companion shows
    no systematic false advantage under the null and an advantage under planted
    edge, consistent with the gate.
- **Evidence AGAINST — METHOD_INVALID** (any holds):
  - gate FPR materially exceeds α₀ at the sparse activity rates in adequately
    powered cells (error not controlled); **or**
  - no finite MDE exists (TPR never reaches 0.80 at FPR ≤ α₀) in **any** domain at
    the ~6 % point (no recovery).
  - Consequence: no fit-for-purpose yardstick yet; **EXP-028 does not run** under
    this method; operator review of how to evaluate sparse signals.
- **Inconclusive**:
  - error is controlled and recovery holds in some domains but calibration
    precision (Wilson half-widths) is insufficient to declare a finite MDE in
    others at the ~6 % point; **or**
  - the two null generators disagree on FPR control beyond tolerance; **or**
  - companion null behavior contradicts the gate in a way that cannot be resolved
    without changing a frozen object (which is not permitted in-phase).
  - Consequence: report the partial map; operator decides whether to widen draws
    (a precision-only re-run, no object change) or treat the method as not yet
    validated.

## Complexity Budget

- Max statistical tests: **4** (regime-cluster bootstrap CI; stratified paired
  sign-permutation with Holm; Wilson FPR/TPR intervals; grid-defined event-level
  MDE determination).
- Max visualisations: **5** (FPR vs. activity-rate by domain; TPR/MDE recovery
  curves by domain at the primary rate; calibration-precision / under-powered-cell
  diagnostic; equity-curve companion null-vs-planted illustration; per-domain
  Evidence-FOR/AGAINST summary).
- Max new code modules: **1 experiment-local helper** under
  `python/experiments/EXP-027/code/` (sparse-null / planted-edge substrate +
  event-level inference). Reusing EXP-021/022 inference by copy or import is
  allowed; **no new or modified shared `python/src/xen/` module** unless governance
  explicitly approves it.

## Data Requirements

Required upstream artifacts (read-only; scaffolding + activity-rate reference only):

- `python/experiments/EXP-020/results/run_metadata.json` (dependency gate:
  `SUPPORTED_FULL`, ready domains, zero invariant failures, deterministic replay);
- `python/experiments/EXP-020/results/avwap_state_summary.csv` (regime intervals,
  anchor-age context — control scaffolding);
- `python/experiments/EXP-020/results/domain_readiness.csv`.

The real `avwap_events.csv` bounce **outcomes** are **not** consumed by the
calibration (anti-overfitting fence). 1-minute source files under `data/timebars/`
are sliced to the first 70 % before any domain bars are built.

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

```text
python/experiments/EXP-027/results/
- fpr_summary.csv              # gate FPR by domain / activity / null generator / alpha
- tpr_summary.csv              # gate TPR by domain / activity / planted edge / alpha
- mde_summary.csv              # event-level MDE by domain at the primary activity rate
- draw_verdicts.csv            # per-draw Evidence FOR/AGAINST/INCONCLUSIVE rows
- equity_companion_summary.csv # exposure-aware equity-vs-buy-hold null/planted behavior
- run_metadata.json            # status, determinism, dependency, validity-range verdict
python/experiments/EXP-027/plots/
- fpr_by_activity.png
- recovery_mde_curves.png
- calibration_precision.png
- equity_companion.png
- method_verdict_summary.png
```

## Suggested Direction

Treat EXP-027 as the event-level analog of EXP-003/005: build synthetic null and
planted-edge **sparse** event draws on the real-regime scaffold, push each draw
through the **unchanged** EXP-021/022 matched-control + regime-cluster-bootstrap +
permutation + Holm decision rule, and measure FPR / TPR / event-level MDE across
{~3 %, ~6 %, ~12 %} activity and the three domains. The binding question is whether
the inference that worked at EXP-021/022 event scale **still controls error and
retains power at the sparse activity rate**, especially on the thin 4h domain
(few events, few regime clusters). The equity-curve-vs-buy-hold companion is built
on an exposure-aware basis so it informs interpretation without re-importing the
per-bar dilution trap. Predeclare every object; measure once; freeze before
EXP-028.
