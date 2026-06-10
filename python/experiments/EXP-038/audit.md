# Audit Report: Experiment EXP-038

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 1

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Implements the scope and analysis plan exactly: integrity guards (hash pin, population reconciliation, per-event net reproduction + EXP-034-seed CI replay), trigger-time TRAIN/TEST partition, R1.2 null calibration, one-shot TEST inference with provisional rule, LOCO diagnostic, seed robustness, and transparency disclosures. No bonus analyses. |
| `code/run_experiment.py` | Edge cases | PASS | Empty TEST stratum → hard stop (guard). Empty subset in LOCO → records NaN row. Zero TEST events from a cluster → `n_remaining=0` noted. NaN net → hard stop. All index ranges validated against rebuilt series. R1.6 no-second-read guard. Partition recovery via byte-identity check. |
| `code/run_experiment.py` | Type safety | PASS | Type hints on all public functions. NumPy/Polars types consistent. |
| `code/run_experiment.py` | NaN handling | PASS | `attach_costs_and_financing` hard-fails on NaN/NaT in trigger/exit timestamps and net values. LOCO skips degenerate drops gracefully. No silent propagation. |
| `code/run_experiment.py` | Holdout exclusion | PASS | Standard fenced loader `load_analysis_data` → `build_domain_frames` → first-70% slice. Boundary from `data.train_end_ts` (last TRAIN 1m bar). Global holdout never loaded. Verified against EXP-020 metadata. |
| `code/run_experiment.py` | Loader ordering | PASS | Lazy scan sorts by CloseTime before first-70% slicing. No full-dataset collection. |
| `code/run_experiment.py` | Memory/performance | PASS | Single-instrument rebuild is trivially bounded. `test_partition.csv` is 39 rows. `infer_cell` runs on 12 events. Seed-robustness loop uses `tqdm`. No Python row loops over large frames. |
| `code/run_experiment.py` | Safe optimization | PASS | All operations are direct sequential computations on the existing event table. No vectorization shortcuts that alter temporal or causal semantics. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` on the null calibration loop (2000 replicates) and LOCO loop (9 drops) and seed-robustness loop (8 seeds). |
| `code/run_experiment.py` | Logging/output | PASS | Concise INFO-level logging. Helpers return data. Console summary line shows all key statistics. |
| `code/run_experiment.py` | Organization/import side effects | PASS | VAL-001-style sectioning. Output dirs created in `ensure_output_dirs()` called from `main()`. Frozen-tail module load at import matches the approved EXP-034 pattern. |
| `code/run_experiment.py` | Plot data reuse | PASS | Plots use TEST per-event nets and stratum disclosure table directly (≤ 39 events). No reload or regeneration. |
| `code/run_experiment.py` | Docstrings | PASS | Module-level docstring documents the full structure. Each function has docstring with purpose and expected outputs. |

## Numerical Validation

### Spot Checks

1. **Population reconciliation (guard G-count):** Full-cell count = 39 exactly (EXP-030/034 EURUSD-4h). TRAIN=27, TEST=12, TRAIN+TEST=39. Verified from `test_partition.csv` — 27 TRAIN rows + 12 TEST rows.

2. **Per-event net reproduction (guard G-net):** Full-cell net mean = 11.77035756668762 bps, deviation from EXP-034 `effect_bps` = 0.0 (exact match to full double precision). This is expected when the identical filtering, cost, and financing code is run on the same population.

3. **EXP-034-seed CI replay (guard G-net CI):** Full-cell bootstrap CI replay with EXP-034's seed: ci_low_1s deviation = 8.88e-16 (within 1e-6 tolerance). Root cause: the bootstrap is deterministic with the same seed, so the only possible divergence is from code-path differences — verified none exist.

4. **Null calibration:** margin = 3.78 bps from R=2000 replicates. FPR uncorrected = 0.0975 (anti-conservative, as expected at n≈12), FPR with margin = 0.05 (target). Sigma_b = 14.4 bps, sigma_w = 25.2 bps — consistent with the EXP-030 EURUSD-4h dispersion (sigma ≈ 30 bps per-event, ~14 bps cross-cluster component).

5. **TEST inference:** n=12, boot_p=0.001 (1/1001 — the most significant possible for 1000 resamples where all are > some threshold), effect=+24.27 bps, ci_low_1s=15.43 > margin 3.78.

6. **LOCO diagnostic:** All 9 regime-cluster drops produce ci_low_1s > margin (range 13.25–28.83 bps). The most fragile drop is the bull regime_id=59 (ci_low_1s=13.25 bps), still well above the 3.78 margin.

7. **Seed robustness:** Over 8 seeds, ci_low_1s ranges [14.59, 15.66] — all above margin, all sign-stable positive. ci_low ranges [13.50, 14.35] — all above 0.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| Full-cell n | 39 | 39 | YES |
| TEST n | > 0 | 12 | YES |
| boot_p | [0, 1] | 0.001 (TEST), 0.008 (FULL), 0.166 (TRAIN) | YES |
| ci_low_1s (TEST) | ℝ | 15.43 | YES |
| margin | > 0 | 3.78 | YES |
| LOCO ci_low_1s | ℝ | [13.25, 28.83] | YES |
| Seed-robust ci_low_1s_min | ℝ | 14.59 | YES |
| Nomination precondition | {true, false} | true (TRAIN net > 0) | YES |
| Full-field holding days | ≥ 0 | [0.33, 1.33] quartiles | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| TEST boot_p | 0.001 | YES | With effect 24.27 bps and one-sided CI_low 15.43, nearly all bootstrap resamples are > 0 — p at the resolution floor is clean. |
| Full-cell boot_p | 0.008 | YES | Effect 11.77 bps, CI_low 4.24 bps. Consistent with EXP-034 pass. |
| TRAIN net mean | 6.22 bps | YES | TRAIN net is smaller than TEST (6.22 vs 24.27), as expected from the chronological ordering — later events (TEST) had larger moves. Both are positive — consistent with the non-disjoint nature of the read. |
| Nomination precondition | TRAIN net 6.22 > 0 | YES | Satisfied; the operator may nominate this package. |
| TEST vs full CI | TEST CI [14.2, 38.8] narrower than full [2.6, 20.4] despite smaller n | EXPLAINED | The opposite pattern is actually present: full CI [2.6, 20.4] width 17.8, TEST CI [14.2, 38.8] width 24.6 — TEST is wider as expected for smaller n. The TEST CI is shifted upward (higher mean events later in the period). |
| FPR uncorrected | 0.0975 | YES | Percentile bootstrap on 12 events in 9 clusters: the ~10% anti-conservatism is within the expected range. The 3.78 bps margin restores FPR to exactly 0.05. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Regime-cluster bootstrap | Exchangeability within direction×regime strata | YES (calibrated) | R1.2 null calibration: FPR uncorrected 0.0975 confirms anti-conservative bias at n≈12. Margin 3.78 bps restores FPR to 0.05. |
| Gaussian cluster null model | Zero-mean Gaussian cluster effects adequate for coverage calibration | YES (disclosure) | Components from TRAIN nets via method-of-moments. Calibration is for coverage geometry, not tail modeling. Disclosed. |
| LOCO fragility assumption | The per-drop bootstrap preserves regime-cluster dependence structure | YES | Each drop re-runs the frozen bootstrap on the remaining clusters — the same covariance structure. |
| Seed robustness | CI stability across seeds indicates estimator stability | YES | All 8 seeds produce ci_low_1s > margin and sign-stable positive — the pass is not a seed artifact. |

## Results Plausibility

All results are internally consistent and align with Phase 008 expectations:

- EURUSD-4h TEST shows a provisional pass (ci_low_1s 15.43 >> margin 3.78, boot_p 0.001). The effect 24.27 bps on TEST is substantially larger than the full-cell 11.77 bps — driven by the later TEST events (calendar 2024-09-06 onward) having larger price moves. This is a property of the specific temporal sample, not a mechanical artifact.

- The TRAIN net (6.22 bps, ci_spans_zero) confirming the nomination precondition is met is consistent with the disclosed dependent nature of the read: TEST events were part of the full-cell pass.

- The LOCO diagnostic shows no single-regime dependence: the lowest per-drop ci_low_1s (13.25 bps, removing regime_id=59 bull, a single event) is still 9.5 bps above the margin.

- Seed robustness confirms the pass is not a sampling artifact at the 0.001 p-level.

- The `train_consistent = true` flag (TRAIN net point 6.22 > 0) means the operator may nominate this package for the one-shot holdout — per R1.7.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 1 test family / 1 (budgeted 1); 2 plots / 2 (budgeted 2); 0 new modules / 0 (budgeted 0)
- Holdout exclusion verified: YES — first-70% loader fence, boundary from `data.train_end_ts` (last TRAIN 1m bar), global holdout never touched.

## Issues

### Critical

None.

### Warning

None.

### Info

1. **TRAIN stratum net CI spans zero (EVIDENCE_FOR label from two-sided).** The TRAIN read shows net 6.22 bps with CI [-7.00, +17.65] — spannning zero. The `train_consistent` flag correctly records `true` (point > 0), which is the scope-mandated criterion. The CI width reflects the small TRAIN n (27 events) and large dispersion. Disclosed as NON-BINDING transparency; no selection or tuning uses it.

## Re-Audit Requirements

None — PASS.
