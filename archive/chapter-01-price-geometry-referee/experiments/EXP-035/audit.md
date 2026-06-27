# Audit Report: Experiment EXP-035

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 0

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | All three covariates constructed according to plan. C1 formula correct with spread>0 guard. C2 UTC hour computed correctly. C3: ATR Wilder smoothing correct; trailing percentile via two-pointer sweep with bisect (causal, calendar-window). Joint contrast bootstrap (F06) correctly resamples from union regime universe. Selection-aware permutation (F05) correctly re-selects candidate in each permutation. |
| `code/run_experiment.py` | Edge cases | PASS | C1 values outside [0,1] preserved (not clipped); <30-day history excluded from C3 only; empty-bin guards; unreportable bins (<30/<15 events) make domain×dimension G1-ineligible; composition_skewed flag for instrument-dominated bins. |
| `code/run_experiment.py` | Type safety | PASS | NumPy typed arrays; Polars schema-aware; `ensure_bool()` for CSV Boolean coercion. |
| `code/run_experiment.py` | NaN handling | PASS | `.is_finite()` on c3 values; `.is_not_null()` on lifetime_bps; binning uses `is_finite()` guards; `np.nanpercentile` for bootstrap distribution. |
| `code/run_experiment.py` | Holdout exclusion | PASS | `load_analysis_data` applies first-70% slice; TRAIN cutoff nested at 70% of domain bars; containment rule (completion_idx ≤ cutoff) ensures no TEST prices leak. |
| `code/run_experiment.py` | Loader ordering | PASS | Lazy scan sorts by `CloseTime` before first-70% slicing. |
| `code/run_experiment.py` | Memory/performance | PASS | Tidy frame built once; all tests are pure functions of it. ATR loop bounded sequential (Wilder smoothing O(n)). Trailing percentile O(n log w) with two-pointer+bisect. |
| `code/run_experiment.py` | Safe optimization | PASS | No unsafe vectorization; ATR loop is genuinely sequential (Wilder recurrence); trailing percentile uses bounded O(n) two-pointer sweep — both correctly causal. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` on file rebuild and characterisation loop (12 domain×dimension cells). |
| `code/run_experiment.py` | Logging/output | PASS | Concise INFO-level; helpers return data. |
| `code/run_experiment.py` | Organization/import side effects | PASS | Clear sectioning; directories created in `main()`. |
| `code/run_experiment.py` | Plot data reuse | PASS | Plots from emitted CSV/JSON output; no re-load of heavy data. |
| `code/run_experiment.py` | Docstrings | PASS | Module docstring and all functions documented. |

## Numerical Validation

### Spot Checks

5m/c1_completion: SNR = 1.42 (Δ=1.30 bps, half-width=0.91 bps) — materiality condition NOT met because `candidate_mean_net_bps = −7.07 ≤ 0` (fails §8.1(i)'s "top bin net > 0" sub-clause). Correct implementation.

4h/c3_vol: Δ=37.12 bps, half-width=63.46 bps, SNR=0.58 — not material (SNR < 1.0). Wide CI consistent with ~42 events per 4h tercile.

TRAIN containment: 5m from 12,795 → 9,000 events (3,795 excluded by lifetime boundary) — plausible given 24-bar window.

C3 history exclusion: 5m=454 events (5% of TRAIN) without 30-day ATR history — reasonable for early-period events.

Permutation p for 5m/c1: 0.010 — correct (Δ=1.30 bps in the correct direction, survives Holm at α_G1=0.10).

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| C1 (completion share) | ℝ (terciles handle tails) | [−1.7, +1.9] approx | YES |
| C3 (vol percentile) | [0, 1] | [0, 1] | YES |
| Net outcome | ℝ | [−8.0, +11.8] bps (domain means) | YES |
| Bin event counts | ≥ 0 | [14, 6588] | YES |
| SNR per cell | [0, ∞) | [0.03, 1.42] | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| 5m C1 SNR | 1.42 | YES | Small positive gradient (Δ=1.30 bps) but candidate net negative (−7.07) — consistent with overall negative 5m absolute net |
| 1h C2 candidate net | +0.27 bps | YES | Asia session has slightly positive net on 1h; SNR=0.59 — not decisive |
| 4h all SNR values | 0.15–0.58 | YES | ~125 TRAIN events across 4 instruments → terciles ~10 events each → wide CIs |
| All 9 cells: material=False | Consistent | YES | No dimension passes the conjunction because every candiate_mean_net_bps ≤ 0 (except 1h/asia at +0.27 but SNR=0.59 < 1) |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| F06 joint bootstrap | Cross-bin covariance captured | YES | Single resample over union regime universe. |
| F05 permutation | Exchangeability within strata | PARTIAL | Event-level label permutation under clustering is acknowledged as anti-conservative; confined to multiplicity leg (iv) where it loosens the gate, not the materiality leg (i). |
| Reportability floors | Guard small-n bins | YES | Predeclared thresholds (30/15 events) enforced; 4h cells near floor disclosed. |

## Results Plausibility

- Zero qualified dimensions is a valid, clean outcome: no G1-qualifying conditioning dimension on any domain.
- The 5m/c1_completion cell comes closest: SNR=1.42 (barely above the 1.0 floor) and structured+stable+multiplicity all pass, but the candidate net is −7.07 bps — the top %completion tercile still has negative absolute net expectancy under frozen costs+financing. This is a predeclared expected pattern: conditioning can separate good from bad, but it cannot make a net-negative domain positive.
- 4h reads are underpowered — the design predeclared this. SNR values 0.15–0.58 on n≈125 events across 4 instruments are diagnostic-only.
- The finding routes the phase toward FLAT/Tier-C per design §9 (design §9: "ZERO QUALIFIED dimensions → selectivity/efficiency levers exhausted on this entry substrate").

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 3 test families / 3 budgeted, 5 plots / 5 budgeted, 1 module / 1 budgeted
- Holdout exclusion verified: YES

## Issues

### Critical

None.

### Warning

None.

### Info

None.

## Re-Audit Requirements

None.
