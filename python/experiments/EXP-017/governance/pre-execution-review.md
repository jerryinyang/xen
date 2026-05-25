# Pre-Execution Review: EXP-017 — Premium Discount Filter Impact on Sweep Quality

**Reviewer:** Research Pipeline (Stage 4 Governance)  
**Date:** 2026-05-25  
**Artifacts reviewed:**
- `python/experiments/EXP-017/scope.md`
- `python/experiments/EXP-017/analysis-plan.md`
- `python/experiments/EXP-017/code/run_experiment.py`
- `docs/experiments-docs/checkpoints/2026-05-23-003-ict-one-setup-timebar-validation/design.md`

---

## 1. Scope Document

| Check | Result | Notes |
|---|---|---|
| Single falsifiable question | PASS | Tests one location-filter question: whether prior-day midpoint filtering improves sweep quality enough to justify the sample-size cost |
| Hypothesis testable | PASS | Improvement thresholds and retention floors are explicit |
| Success / failure / inconclusive criteria concrete | PASS | `>= 5pp` Hit1R improvement or `>= 0.25R` MAE improvement on `>= 3` instruments; retention floor defined; mixed/wide outcomes reserved for INCONCLUSIVE |
| Data view explicit | PASS | Depends only on approved time-bar-native prerequisite artifacts from EXP-014 and EXP-015 |
| Holdout exclusion explicit | PASS | Scope inherits the analysis-set-only requirement and never reopens raw holdout access |
| Real-price outcome discipline | PASS | Reuses EXP-015 real-price outcome definitions unchanged |
| Prerequisites explicit | PASS | EXP-014 levels and EXP-015 sweep outcomes are named as required inputs |
| No scope creep | PASS | No VWAP, open-distance, overnight midpoint, macro, displacement, IFVG, breaker, or full-model logic added |
| Complexity budget realistic | PASS | Script implements 2 statistical comparisons, 3 plots, and 0 new shared modules |

**Scope verdict: PASS**

---

## 2. Analysis Plan

| Check | Result | Notes |
|---|---|---|
| Method justification | PASS | Step 1 uses only the approved PD midpoint; Step 2 reuses EXP-015 definitions; Step 3 measures effect and retention together |
| Simpler alternative considered | PASS | Plan explicitly rejects adding VWAP or other location filters in this experiment |
| Non-parametric methods | PASS | Bootstrap comparisons only; no normality or stationarity assumptions |
| Sample-size cost measured before interpretation | PASS | Retention is reported alongside effect sizes instead of treating filtered performance in isolation |
| Visualisation plan purposeful | PASS | Counts/retention, interval effects, and MAE shape each answer a distinct sub-question |
| Budget compliance | PASS | 2 tests / 2 allowed, 3 plots / 4 allowed, 0 modules / 1 allowed |

**Analysis-plan verdict: PASS**

---

## 3. Code Review

### Organization and Side Effects

| Check | Result | Notes |
|---|---|---|
| Imports → path setup → constants → helpers → plots → orchestration → `main()` | PASS | File follows the same layout as EXP-015/EXP-016 |
| No import-time I/O side effects | PASS | No directories, file writes, data loads, or plotting at import |
| Output directories created only in orchestration | PASS | `mkdir` only inside `run_experiment()` at [run_experiment.py](/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/python/experiments/EXP-017/code/run_experiment.py:764) |

### Scope and Design Compliance

| Check | Result | Notes |
|---|---|---|
| Only the simplest Phase 003 location filter is tested | PASS | Midpoint rule implemented directly from PDH/PDL; no alternative location filters added at [run_experiment.py](/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/python/experiments/EXP-017/code/run_experiment.py:144) |
| Time-bar-native ICT path preserved | PASS | No Line Break, Renko, or Heiken Ashi code paths |
| Component characterization gate respected | PASS | Script isolates the premium/discount filter over the EXP-015 sweep baseline instead of changing event logic, stop logic, or horizons |
| No compounding with later roadmap items | PASS | No macro interaction, displacement, FVG/IFVG, breaker, or execution-timing logic appears anywhere in the code |

### Holdout and Temporal Discipline

| Check | Result | Notes |
|---|---|---|
| No raw holdout access possible | PASS | EXP-017 reads only `EXP-014/results/liquidity_levels.csv` and `EXP-015/results/sweep_events.csv` at [run_experiment.py](/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/python/experiments/EXP-017/code/run_experiment.py:95) and [run_experiment.py](/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/python/experiments/EXP-017/code/run_experiment.py:112) |
| Upstream artifact dependencies are explicit | PASS | Missing prerequisite files fail fast with clear `FileNotFoundError` messages |
| No look-ahead introduced by the new filter | PASS | Midpoint uses prior-day PDH/PDL only, then evaluates filter pass from the event bar’s own `Close` at [run_experiment.py](/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/python/experiments/EXP-017/code/run_experiment.py:151) |
| Outcome definitions unchanged | PASS | Script reuses EXP-015 event-level outcomes rather than recomputing or retuning them |

### Statistical Correctness

| Check | Result | Notes |
|---|---|---|
| Filter effect measured against the full baseline, not a different event definition | PASS | Baseline is all sweep rows; filtered group is a nested subset |
| Nested subset dependence handled explicitly | PASS | Bootstrap resamples the full baseline rows and recomputes the filtered subset inside each resample at [run_experiment.py](/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/python/experiments/EXP-017/code/run_experiment.py:243) |
| Ambiguous same-bar target/stop cases excluded from Hit1R comparisons | PASS | `Hit1R_60m` comparisons use only non-ambiguous rows at [run_experiment.py](/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/python/experiments/EXP-017/code/run_experiment.py:319) |
| MAE improvement sign is coherent | PASS | Improvement is defined as `all-sweep median MAE - filtered median MAE`, so positive values mean less adverse excursion under the filter at [run_experiment.py](/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/python/experiments/EXP-017/code/run_experiment.py:341) |
| Retention floor enforced before verdict pass | PASS | Segment floor uses `>= 50%` retention or `>= 50` filtered events at [run_experiment.py](/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/python/experiments/EXP-017/code/run_experiment.py:311) |
| Instrument-level pass requires train/test retention floors and test-segment improvement | PASS | Encoded in `evaluate_verdict()` at [run_experiment.py](/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/python/experiments/EXP-017/code/run_experiment.py:404) |

### Code Quality

| Check | Result | Notes |
|---|---|---|
| Public functions typed and documented | PASS | Consistent with prior experiment scripts |
| NaN / empty-group handling explicit | PASS | Empty baselines, empty filtered subsets, and missing midpoint cases return `NaN` metrics rather than misleading zeros |
| No unnecessary new abstractions | PASS | Reuses only `ict_timebar.INSTRUMENTS`; keeps all experiment-specific logic local to the script |
| Plot inputs bounded | PASS | MAE plotting caps values at `8R` before boxplots at [run_experiment.py](/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/python/experiments/EXP-017/code/run_experiment.py:627) |
| Output surface focused | PASS | Writes event-level merged data, retention summary, outcome summary, primary effects, JSON summary, text summary, and 3 scoped plots only |

---

## 4. Verification Notes

| Check | Result | Notes |
|---|---|---|
| Syntax compile with system Python | PASS | `python3 -m py_compile python/experiments/EXP-017/code/run_experiment.py` |
| Syntax compile with project environment | PASS | `uv run python -m py_compile experiments/EXP-017/code/run_experiment.py` from `python/` |
| EXP-014 merge key uniqueness sanity check | PASS | Current `liquidity_levels.csv` has no duplicate `(Instrument, NYDate)` keys |
| EXP-015 prerequisite coverage sanity check | PASS | Current `sweep_events.csv` contains Train and Test sweep rows across all 4 instruments |

---

## 5. Information Notes

**INFO-1 — Upstream artifact dependency is intentional:** EXP-017 does not reload `data/timebars/` directly. That is correct here because the scope explicitly says to use EXP-014 level definitions and EXP-015 sweep outcomes. Reusing approved upstream artifacts is the simplest way to isolate the midpoint filter.

**INFO-2 — Baseline naming:** The output tables use “All sweeps” as the comparison group label. This is the correct baseline because the filter is being evaluated as a pruning rule on the existing sweep population, not as a new event generator.

---

## 6. Post-Adversarial Revision Note (F08)

The adversarial review (`docs/code-reviews/2026-05-25-145710-WAT-EXP-017-EXP-020-adversarial-review.md`) flagged that the `WidePositiveSignal` rule fired whenever any test-segment point estimate was strictly positive, even far below the predeclared threshold, which biased the verdict against AGAINST. `evaluate_verdict` (run_experiment.py:429-449) was tightened so the rule only fires when (a) the point estimate is at least half the threshold AND (b) the bootstrap CI95-high reaches the threshold — i.e., the interval is genuinely consistent with a real effect. `verdict_rule` in the JSON payload was updated to match. Re-execution required to refresh `results.json` and `numerical_summary.txt`.

## Verdict

```text
VERDICT: APPROVE
```

The implementation is scope-faithful, design-faithful, and code-quality-consistent with EXP-015 and EXP-016. It isolates the Phase 003 premium/discount assumption, preserves the approved EXP-015 sweep/outcome definitions, introduces no new holdout or look-ahead risk, and stays inside the declared complexity budget.

---

## Execution Instructions

```text
Pre-execution review: APPROVED

Experiment: EXP-017 — Premium Discount Filter Impact on Sweep Quality
Code:       python/experiments/EXP-017/code/run_experiment.py
Expected output: python/experiments/EXP-017/results/
                 python/experiments/EXP-017/plots/

Loads approved EXP-014 liquidity levels and EXP-015 sweep outcomes, applies the
prior-day midpoint premium/discount filter, then bootstrap-compares filtered
sweeps against the full EXP-015 sweep baseline on 60-minute Hit1R and median MAE
while reporting the filter’s sample-retention cost.

Please run the experiment code and confirm when complete.
```
