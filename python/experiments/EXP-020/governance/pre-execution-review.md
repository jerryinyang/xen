# Pre-Execution Review: EXP-020 — FVG IFVG Detection Reproducibility

**Reviewer:** Research Pipeline (Stage 4 Governance)
**Date:** 2026-05-25 (post-adversarial revision)
**Supersedes:** 2026-05-25 initial APPROVE (which did not catch F06/F07 from `docs/code-reviews/2026-05-25-145710-WAT-EXP-017-EXP-020-adversarial-review.md`)
**Artifacts reviewed:**
- `python/experiments/EXP-020/scope.md`
- `python/experiments/EXP-020/analysis-plan.md` (revised)
- `python/experiments/EXP-020/code/run_experiment.py` (revised)
- `python/src/ict_timebar.py`
- `docs/experiments-docs/checkpoints/2026-05-23-003-ict-one-setup-timebar-validation/design.md`

## Background — what the adversarial review caught

| Finding | Issue | Resolution in revised code |
|---|---|---|
| F06 (Major) | The original `verify_reproducibility` reran `detect_fvgs` on the same in-memory inputs. Determinism on identical inputs is guaranteed by deterministic NumPy code; the check therefore could not fail and validated nothing relevant for EXP-021. | `verify_reproducibility` now runs two real invariance checks: (a) a fresh disk reload via `load_instrument_bars` builds an independent in-memory frame and reruns detection; (b) the input rows are shuffled with `REPRODUCIBILITY_SHUFFLE_SEED`, re-sorted by `CloseTime`, and detection is rerun (run_experiment.py:282-365). Both digests must match. |
| F07 (Major) | Observed counts (~150K FVGs, ~140K IFVGs per instrument/segment) made the `>= 100 / >= 50` readiness floors trivial. The 85% IFVG base rate also meant IFVG inversion is not a discriminating event under the current parameters. | `summarize_counts` now reports `IFVGRate = IFVG_N / FVG_N` per instrument/segment and flags `Tautological` when `IFVGRate >= IFVG_TAUTOLOGY_RATE` (0.5). `ReadyForIFVGStudy` requires `not Tautological`. `evaluate_verdict` downgrades to INCONCLUSIVE when any instrument is tautological. |

## 1. Scope Document

| Check | Result | Notes |
|---|---|---|
| Single falsifiable question | PASS | One H4 prerequisite question (deterministic FVG/IFVG detection with stable counts). |
| Criteria measurable | PASS | `>= 100` FVGs and `>= 50` IFVGs per usable instrument/segment plus reproducibility under two invariance checks plus non-tautological base rate. |
| Holdout exclusion | PASS | `load_analysis_timebars` first-70% only. |
| Real-price discipline | PASS | Detection uses real time-bar OHLC; no synthetic prices, no P&L. |
| Phase 003 alignment | PASS | H4 prerequisite only; no entry-quality, breaker, or full-model claims. |
| Complexity budget | PASS | No statistical tests, four plots, no new shared module. |

## 2. Analysis Plan (revised)

| Check | Result | Notes |
|---|---|---|
| Reproducibility checks meaningful | PASS | Step 3 (revised) declares the same-process repeat 'is not a meaningful reproducibility test and is not used' and replaces it with fresh-reload and shuffle-then-resort invariance checks. |
| IFVG base rate reported | PASS | Step 3 (revised) explicitly requires `IFVGRate` per instrument/segment and gates readiness on it. |
| Floors role explicit | PASS | Step 3 (revised) acknowledges floors are intentionally low and that the tautology check is the actual readiness gate. |

## 3. Code Review

### FVG Detection

| Check | Result | Notes |
|---|---|---|
| Bearish FVG definition | PASS | `High[i] < Low[i-2]` via vectorised `_candidate_arrays` (run_experiment.py:104-148). |
| Bullish FVG definition | PASS | `Low[i] > High[i-2]` same path. |
| Min-size filter | PASS | `min_size = max(price_precision_step, 0.02 * ATR14Prior)` (run_experiment.py:136-138). |
| Look-ahead bias | PASS | FVG is knowable at candle `i` close; lifecycle starts at `i+1` (run_experiment.py:167). |
| ATR14Prior is shifted | PASS | `add_bar_diagnostics` shifts by one bar before exposing (`ict_timebar.py:170-172`). |

### Lifecycle Classification

| Check | Result | Notes |
|---|---|---|
| 120-bar window enforced | PASS | `end = min(start + LIFECYCLE_BARS, len(bars))` (run_experiment.py:168). |
| Bullish/bearish lifecycle bounds correct | PASS | Bullish partial = `lows <= upper`; bearish partial = `highs >= lower`. Full/inversion mirror the boundary convention. Verified by hand against the planning spec. |
| State precedence | PASS | inverted > fully_filled > partially_filled > expired > formed (run_experiment.py:205-214). |
| First-inversion timestamp | PASS | `np.flatnonzero(inversion_mask)[0]` (run_experiment.py:192-193). |

### Reproducibility

| Check | Result | Notes |
|---|---|---|
| Fresh-reload check | PASS | `load_instrument_bars(instrument)` is called a second time, independent of cached `bars_by_instrument` (run_experiment.py:333). |
| Shuffle-then-resort check | PASS | `_shuffle_then_resort` permutes rows with `REPRODUCIBILITY_SHUFFLE_SEED`, sorts by `CloseTime`, then recomputes. Stable mergesort preserves equal-timestamp order (run_experiment.py:282-303). |
| Both checks must match for `Reproducible=True` | PASS | `Reproducible` = both digests equal (run_experiment.py:361-363). |
| Per-check match flags exposed | PASS | `FreshReloadMatches` and `ShuffledResortMatches` columns are written to `reproducibility_digest.csv` for granular auditing. |

### Sample Adequacy and Tautology Guard

| Check | Result | Notes |
|---|---|---|
| Base rate reported | PASS | `IFVGRate` written to `count_readiness.csv` per instrument/segment. |
| Tautology threshold enforced | PASS | `Tautological = IFVGRate >= IFVG_TAUTOLOGY_RATE` (0.5); enters readiness gate at run_experiment.py:373-384. |
| Verdict downgrades on tautology | PASS | `evaluate_verdict` returns INCONCLUSIVE when any instrument is tautological even if reproducibility and floors pass (run_experiment.py:439-470). |

### Code Quality

| Check | Result | Notes |
|---|---|---|
| Imports lean | PASS | Only required helpers from `ict_timebar` are imported. |
| Plot reuse | PASS | All four plots read precomputed tables; no heavy reloads. |
| Performance | PASS | Vectorised candidate detection; bounded lifecycle classification per FVG. |

## 4. Verification

- `python3 -m py_compile python/experiments/EXP-020/code/run_experiment.py` passed.
- Experiment code was not executed by the reviewer.

## 5. Required Re-Execution

`python/experiments/EXP-020/results/` reflects the pre-revision code (trivial reproducibility check; no tautology guard). It must be regenerated. EXP-021 must read the regenerated readiness verdict and treat any `Tautological=True` instrument as ineligible for an IFVG entry study unless parameters are tightened.

## Verdict

```text
VERDICT: APPROVE
```

The revised implementation addresses F06/F07. The readiness gate is no longer trivially passable; tautological IFVG detection is surfaced and downgrades the verdict; reproducibility is exercised by two real invariance checks.

## Execution Instructions

```text
Pre-execution review: APPROVED (post-adversarial revision)

Experiment: EXP-020 — FVG IFVG Detection Reproducibility
Code:       python/experiments/EXP-020/code/run_experiment.py
Expected output: python/experiments/EXP-020/results/
                 python/experiments/EXP-020/plots/

The reproducibility verification now performs a fresh disk reload plus a
shuffled-then-resorted recompute and compares SHA-256 digests of FVG
identity columns. The readiness gate now requires `IFVGRate < 0.5` in
addition to the existing count floors.

Please run the experiment code and confirm when complete.
```
