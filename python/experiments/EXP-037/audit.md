# Audit Report: Experiment EXP-037

**Title:** Null Calibration of Frozen Reference Stack
**Audited:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, `python/src/referee_calibration.py`, `results/`
**Frozen reference:** `docs/experiments-docs/checkpoints/2026-05-31-006-thesis-qualification-referee-calibration/reference-stack-spec.md`; `python/experiments/EXP-036/code/run_experiment.py`

## Summary

- **Verdict**: PASS (implementation and results are trustworthy as measurements)
- **Critical Issues**: 0
- **Warnings**: 3
- **Info Notes**: 5

**Headline.** The harness is correct, holdout-clean, look-ahead-free, real-price-disciplined, deterministic, and a **faithful transcription of the EXP-036 stack** (proven by an exact reproduction of EXP-036's verdict, below). The experiment lands cleanly in the **predeclared "measurement-validity failure" branch** of `scope.md`: no block length produced a trusted second-order-holdout FPR because the predeclared Part A null fails its own realism diagnostics on 100% of realizations. That failure is a **genuine, correctly-measured property of the predeclared null-construction method, not a code artifact.** The three warnings are methodological inputs for Stage 6 interpretation and the mid-phase reflection (whether to issue a dated predeclared amendment to the null construction); none is a code defect that produced wrong numbers.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `referee_calibration.py` | Correctness (E1–E7 + ladder) | PASS | Byte-equivalent to EXP-036 gating logic; verified by exact observed-verdict reproduction. |
| `referee_calibration.py` | Holdout exclusion | PASS | Loads via `load_analysis_timebars` (first 70% by `CloseTime`); null resampling only permutes holdout-excluded rows. |
| `referee_calibration.py` | Look-ahead | PASS | Prior range `rolling_*(20).shift(1)` (causal); returns `shift(-1).over("Segment")` (forward, in-segment); resampling permutes causal observations only. |
| `referee_calibration.py` | Real-price discipline | PASS | All returns are log returns of aggregated real OHLC; no HA/Renko/LB price anywhere. |
| `referee_calibration.py` | NaN / zero-denominator | PASS | `_relative_diff`/`_stat_values`/`wilson_interval` guard non-finite; empty denominators emit `None`, never 0% or 100%. |
| `referee_calibration.py` | Determinism | PASS | Descriptor RNG (base 440000), return RNG (base 880000), stack-bootstrap seed all derived from `seed_index`/`block_length`; no wall-clock in the data path. |
| `run_experiment.py` | Organization / import side effects | PASS | Imports→path→constants→helpers→orchestration→`main()`; output dirs created only in orchestration. |
| `run_experiment.py` | Memory / plot reuse | PASS | Plots consume aggregated rate tables; no re-load or re-generation for plotting. |
| `run_experiment.py` | Logging/output | PASS | Orchestration-level logging; `print()` limited to the final concise summary. |
| both | Docstrings / type hints | PASS | Present on public functions. |

## Numerical Validation

### Spot Checks

**SC-1 — Faithful transcription (observed reproduction).** EXP-037 `results/observed_verdict.json` vs EXP-036 `results/verdict.json`, field-for-field:

| Field | EXP-036 | EXP-037 observed | Match |
|---|---|---|---|
| `outcome` | AGAINST | AGAINST | ✓ |
| `next_bar_neutral_and_control` | {1h:[], 4h:[]} | {1h:[], 4h:[]} | ✓ |
| `next_bar_neutral_only` | {1h:[], 4h:[]} | {1h:[], 4h:[]} | ✓ |
| `four_bar_neutral_and_control` | {1h:[XAUUSD], 4h:[]} | {1h:[XAUUSD], 4h:[]} | ✓ |
| `next_bar_control_adjudicable` | all 4, both tf | all 4, both tf | ✓ |

With `seed_index=0` the per-cell bootstrap seed is `BOOTSTRAP_SEED + offset` — identical to EXP-036 — and the load/aggregate/feature/return pipeline is line-equivalent. The harness measures the EXP-036 object. **(Q1 → confirmed faithful.)**

**SC-2 — Descriptor-merge mechanism (root cause of `DescriptorPass=0/450`).** Reproduced with the live module functions `_descriptor_indices`/`_episode_lengths` on a synthetic observed stream constructed as maximal runs:

```
observed : episodes=978, median_len=3.00, p90=5.00
resampled: episodes=632, median_len=4.00, p90=9.00
episode-count rel diff = 0.354  (tolerance 0.05)  -> FAILS
median-len  rel diff   = 0.333  (tolerance 0.10)  -> FAILS
observed adjacent-same-bucket episode pairs: 0
```

The observed bucket stream, being maximal runs, **never** places two same-bucket episodes adjacently. `_descriptor_indices` draws whole episode-blocks i.i.d. with replacement and concatenates; with ~3 bucket values, a constant fraction of adjacent draws share a bucket and **merge** under `_episode_ids`, collapsing the episode count and inflating lengths. The reproduced magnitude (−35% count) matches the production range (`descriptor_max_count_rel_diff` 0.39–0.56 across all 450 realizations; `descriptor_failed_cells = 16/16` every realization). This is deterministic and structural. **(Q2a → genuine, not a code bug; `_episode_lengths`/`_descriptor_diagnostics` count correctly — they faithfully report the merged structure.)**

**SC-3 — Autocorr diagnostic is near-unpassable.** `_return_autocorr_signs` produces 8 cells × 2 segments × 2 horizons × 2 lags = **64** sign comparisons; `_autocorr_compare` sets `pass = (mismatches == 0)`. Production shows median 12 mismatches (match rate ≈0.81; min 4, max 23) → `ReturnAutocorrPass = 0/450`. Near-zero noise autocorrelations have sign-unstable values, so requiring all 64 signs identical is effectively impossible. **(Q2b → confirmed; this gate alone would keep the trusted envelope empty even if the descriptor issue were fixed.)**

**SC-4 — Raw full-stack FOR.** `realization_summary.csv`: `FullStackFOR` sum = 0 over 450; verdict counts 429 AGAINST / 20 INCONCLUSIVE / 1 STATE_DIFFERENTIATION_ONLY / 0 FOR. `rate_summary.csv`: `full_stack_fpr = 0/75` in every (block, battery) `all_realizations` cell (Wilson upper ≤0.0487). **(Q2c → correctly computed.)**

### Range / Sanity Checks

| Metric | Expected | Actual | Pass? |
|---|---|---|---|
| Trusted FPR denominator | ≥0; `None` when empty | 0 for all L; `fpr=null` (not 0%) | YES |
| `diagnostic_pass` / `trusted_second_order` denominators | empty given 100% diag fail | 0 everywhere, blank rate/CI | YES |
| Raw verdict rates per 75-cell | sum to 1 | AGAINST+INCONCLUSIVE(+1 STATE) = 75 each | YES |
| `realizations_per_block` | 150 (no downscale; ~2.2s≪84s) | 150 | YES |
| `compute_stopped` | 0 (well under 30 CPU-h) | 0 | YES |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|---|---|---|---|
| Episode block bootstrap (descriptor null) | preserves run/episode structure (spec §3) | **NO** | SC-2: independent block draws merge adjacent same-bucket episodes; structure not preserved. |
| Autocorr-sign diagnostic | "signs unchanged" is achievable on real returns | **NO** | SC-3: 64-cell zero-mismatch gate is unpassable on noise-level autocorrelations. |
| Frozen episode bootstrap (E2–E5) | non-parametric, no normality/stationarity/iid | YES | Resamples episodes with replacement; recomputes `mu_mid` per draw. |
| Cross-instrument correlation diagnostic | Frobenius ≤0.20 distinguishes realism | PARTIAL | Behaves sensibly: `CrossCorrPass` rises 0.21→0.36 with block length. |

## Results Plausibility

Outputs are internally consistent and within domain. The empty trusted envelope is the **expected, predeclared** consequence of the diagnostics failing — `scope.md` "Evidence AGAINST measurement validity" branch. Crucially, the failure is attributable to the null-construction **method**, not to a property of the market data that would make a realistic null impossible — so a predeclared amendment to the descriptor resampler (and a less brittle return-autocorr gate) could plausibly rescue Stage A. That decision belongs to interpretation + the mid-phase reflection, **not** to a silent in-place code fix (the charter forbids re-tuning the generator after seeing it fail).

## Scope Compliance

- Analysis plan followed: **YES** (all 7 steps; observed baseline, diagnostics, null gen, frozen stack, rates, profile/stop).
- Deviations: the EXP-036 non-gating `row_diag` naive row-level diagnostic is not reproduced (Info I-2; does not affect any gate or measured rate).
- Complexity budget: 3/3 test families, 4/4 plots, 1/1 module.
- Holdout exclusion verified: **YES** (`load_analysis_timebars` first-70% slice; no path reaches the final 30%).

## Issues

### Critical

None.

### Warning

1. **Predeclared descriptor null cannot preserve episode structure (root cause of the empty envelope)**
   - File: `python/src/referee_calibration.py:579` (`_descriptor_indices`), `:598` (`_descriptor_blocks`); diagnostic at `:702` (`_descriptor_diagnostic_compare`).
   - Description: Independent episode-block resampling merges adjacent same-bucket episodes (SC-2), collapsing episode count ~35–56% and inflating lengths — far outside the ±5%/±10% tolerances. `DescriptorPass = 0/450`. The spec §3 goal "preserving the descriptor's own run/episode structure" is not achieved by this method.
   - Impact: No trusted FPR can be produced for any block length; this single mechanism invalidates the entire trusted envelope.
   - Fix: **Methodological, via a dated predeclared amendment (spec §6) — not an in-place EXP-037 edit.** Candidate redesigns for the reflection: resample episode *labels* under a transition model that forbids same-bucket adjacency, or circular-block the descriptor sequence without snapping to episodes, or relax the count/length tolerance with stated rationale.

2. **Return autocorr-sign diagnostic is effectively unpassable**
   - File: `python/src/referee_calibration.py:759` (`_autocorr_compare`, `pass = mismatches == 0`), `:737` (`_return_autocorr_signs`).
   - Description: Zero-mismatch requirement over 64 lag-1/lag-5 sign cells; near-zero noise autocorrelations flip sign under any resample (SC-3). `ReturnAutocorrPass = 0/450` independently of the descriptor issue.
   - Impact: Even a fixed descriptor null would yield an empty trusted envelope under the current gate.
   - Fix: **Predeclared amendment.** Operationalize "signs unchanged" only for autocorrelations whose observed magnitude exceeds a noise floor, or allow a small mismatch budget, with stated non-outcome-driven rationale.

3. **Raw `all_realizations` rates are plausibly downward-biased and must not be read as an FPR**
   - File: result `rate_summary.csv` / `fpr_envelope.json`.
   - Description: The unrealistic null produces *fewer, longer* descriptor episodes (SC-2) → fewer independent bootstrap units → wider test-segment CIs → systematically harder to clear "test CI lower bound > 0," i.e., harder to emit FOR. The raw 0/450 FOR is therefore both untrusted **and** plausibly conservatively biased.
   - Impact: Risk that Stage 6 misreads "raw FOR 0/450, Wilson upper ≤0.049" as "the stack is well-calibrated (~0% FPR)."
   - Fix: Interpretation must report the raw rates only as untrusted, bias-suspect descriptive context, and withhold any operating-characteristic claim — consistent with `analysis-plan.md` Interpretation Guide.

### Info

1. **Faithful transcription verified (positive).** Exact observed-verdict reproduction of EXP-036 (SC-1) confirms E1–E7 and the verdict ladder are transcribed correctly.
2. **Non-gating `row_diag` omitted.** EXP-036's naive row-level diagnostic bootstrap (`seed+7919`) is not reproduced. It never enters gating, so the measured object is unchanged; noted only so Stage 6 does not expect that column.
3. **Stack-bootstrap seed omits `block_length`.** `_cell_metrics` seeds with `BOOTSTRAP_SEED + seed_index*10000 + offset`; realizations sharing a `seed_index` across L reuse the index pattern (applied to different null data). No within-L bias; mild cross-L coupling only.
4. **Cross-instrument "common starts" weakened by per-instrument modulo.** `_apply_return_plan` takes `starts[i] % n_rows`, so restart *positions* are shared but absolute starts diverge when segment lengths differ. Gated by the Frobenius diagnostic, which behaves sensibly.
5. **Compute gate did not trigger.** Median ~2.2 s/FSE ≪ 84 s; all 450 FSE ran (`compute_stopped=0`), ~16 min wall — consistent with the predeclared budget.

## Re-Audit Requirements

None for EXP-037 as executed: the code and results are trustworthy and the experiment correctly reports its predeclared invalidity branch. Warnings 1–2 are **methodological items for the mid-phase reflection** (predeclared null-construction amendment), not fixes that change EXP-037's measured numbers. Warning 3 is an interpretation guardrail for Stage 6.
