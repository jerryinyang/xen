# Audit Report: Experiment EXP-020

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 1

EXP-020 can be interpreted. The implementation matches the scoped three-candle FVG and close-through IFVG rules, loads holdout-excluded time bars through the shared loader, and writes internally consistent lifecycle, count, and reproducibility tables. I did not rerun the full experiment code inside the pipeline; validation used code inspection and lightweight checks over the generated output files.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `python/experiments/EXP-020/code/run_experiment.py` | Correctness | PASS | FVG detection applies the scoped `High[i] < Low[i-2]` / `Low[i] > High[i-2]` rules plus the `max(price_step, 0.02 * ATR14Prior)` size filter. |
| `python/experiments/EXP-020/code/run_experiment.py` | Edge cases | PASS | Short input sequences, incomplete 120-bar lifecycle windows, and NaN ATR values are handled explicitly. |
| `python/experiments/EXP-020/code/run_experiment.py` | Type safety | PASS | Public functions and the `PreparedBars` dataclass are typed and documented. |
| `python/experiments/EXP-020/code/run_experiment.py` | NaN handling | PASS | ATR nulls fall back to the price-step floor; lifecycle timestamps become `NaT` when the event never reaches that state. |
| `python/experiments/EXP-020/code/run_experiment.py` | Holdout exclusion | PASS | All raw bars enter through `load_analysis_timebars()`, which slices the analysis set before collection. |
| `python/src/ict_timebar.py` | Loader ordering | PASS | The shared loader sorts by `CloseTime`, slices the first 70%, then collects. |
| `python/experiments/EXP-020/code/run_experiment.py` | Memory/performance | PASS | Detection uses cached numpy arrays, selects only required columns, and bounds the reproducibility check to a sampled bar window. |
| `python/experiments/EXP-020/code/run_experiment.py` | Logging/output | PASS | Helper functions do not print; orchestration logs detected counts and writes a concise completion summary. |
| `python/experiments/EXP-020/code/run_experiment.py` | Organization/import side effects | PASS | Output directories are created in `run_experiment()`, not on import. |
| `python/experiments/EXP-020/code/run_experiment.py` | Plot data reuse | PASS | Plots are built from the already-computed event, count, lifecycle, and reproducibility tables. |
| `python/experiments/EXP-020/code/run_experiment.py` | Docstrings | PASS | Public and core helper functions are documented. |

## Numerical Validation

### Spot Checks

Internal consistency checks over the generated outputs match exactly:

- `fvg_lifecycle_events.csv` row count: `962,199`
- Sum of `FVG_N` across `count_readiness.csv`: `962,199`
- Sum of `IsIFVG` across `fvg_lifecycle_events.csv`: `817,561`
- Sum of `IFVG_N` across `count_readiness.csv`: `817,561`
- Sum of lifecycle counts in `lifecycle_counts.csv`: `962,199`

The EURUSD Train readiness row also recomputes exactly from the count table:

- `FVG_N = 167,956`
- `IFVG_N = 142,897`
- `IFVGRate = 142,897 / 167,956 = 0.8508002096`

That matches the stored `IFVGRate` in `python/experiments/EXP-020/results/count_readiness.csv`.

### Range Checks

| Metric | Expected Range | Actual Range / Count | Pass? |
|--------|---------------|----------------------|-------|
| `Side` | `Bearish`, `Bullish` | Only `Bearish`, `Bullish` observed | YES |
| `LifecycleState` | formed / partially filled / fully filled / inverted / expired | All 5 states observed; no extras | YES |
| `IFVG_N` | `<= FVG_N` | Always true | YES |
| `IFVGRate` | `[0, 1]` | `0.8421` to `0.8527` | YES |
| Reproducibility digests | exact match booleans | 4/4 instruments `FreshReloadMatches=True` and `ShuffledResortMatches=True` | YES |
| Plots | 4 scoped PNGs | All 4 files present and non-empty | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|---------------------|-------|
| Reproducible instruments | `4/4` | YES | Detection is deterministic under both reloaded and shuffled-resorted inputs. |
| Ready instruments | `0/4` | YES | All instruments clear count floors but fail the tautology gate. |
| IFVG rate min/max | `0.842` / `0.853` | YES | The observed base rate is consistently far above the `0.50` selectivity threshold. |
| Any ready segment | `False` | YES | Consistent with the reported verdict summary. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|------------|--------|----------|
| FVG detection | Candle `i` close is the first knowable timestamp | YES | Candidate rows are indexed at `i` and use only `i` and `i-2` information plus prior ATR. |
| ATR size floor | Only prior-known ATR is used | YES | `ATR14Prior` is shifted in the shared diagnostics and passed into FVG detection. |
| Lifecycle and inversion | Later state transitions use only forward bars after formation | YES | `classify_lifecycle()` scans `creation_idx + 1` onward. |
| Reproducibility | Event identities depend only on sorted bar data and parameters | YES | Fresh-reload and shuffled-resort digests match the first-pass digest on all instruments. |

## Results Plausibility

The results are plausible and internally coherent. FVGs are extremely common on this 1-minute dataset, IFVGs occur on most of them within the 120-bar lifecycle window, and the reproducibility checks pass exactly. That supports the conclusion that the detection mechanics are deterministic but not selective enough for downstream IFVG-entry work under the current parameterization.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 0 statistical tests / 0-1 allowed, 4 plots / 4 allowed, 0 new shared modules / 1 allowed
- Holdout exclusion verified: YES
- Real-price discipline verified: YES, no profitability metrics are computed
- Timestamp alignment verified: YES

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Reproducibility digests are sampled rather than full-dataset hashes**
   - File: `python/experiments/EXP-020/code/run_experiment.py`, lines 356-379
   - Description: The reproducibility check intentionally hashes the first `50,000` bars per instrument instead of the full bar history.
   - Impact: This bounds runtime while still exercising fresh-reload and ordering invariance. Full-run count and lifecycle tables remain internally consistent, so trust is not affected.
   - Reproduction: Compare `REPRODUCIBILITY_SAMPLE_BARS` in code with `SampleBars` in `reproducibility_digest.csv`.

## Re-Audit Requirements

None.
