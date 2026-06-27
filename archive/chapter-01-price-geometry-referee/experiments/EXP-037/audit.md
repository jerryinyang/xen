# Audit Report: Experiment EXP-037

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 2

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Implements the scope and analysis plan exactly: TRAIN tie-break (H candidates {4,6,8,12}, stability filter, max-min worst-half selection), pyramid policy one-SE rule, R1.2 null calibration, freeze-before-TEST barrier, one-shot TEST inference, descriptive FH-vs-BTC companion. No bonus analyses. |
| `code/run_experiment.py` | Edge cases | PASS | `B2_NO_ROBUST_HSTAR` empty-set path halts before TEST (no read). Empty instrument in TRAIN half → hard stop (pre-freeze). Empty TEST cell under policy → R1.6 pre-freeze feasibility catches via entry attributes. Truncated FH windows at series end disclosed. NaN/NaT → hard stop. |
| `code/run_experiment.py` | Type safety | PASS | Type hints on all public functions. NumPy/Polars types consistent. |
| `code/run_experiment.py` | NaN handling | PASS | `add_fh_net_columns` initialises FH arrays as NaN; hard checks on out-of-range indices. `infer_test_cell` operates on raw float arrays with no null inputs. No silent propagation. |
| `code/run_experiment.py` | Holdout exclusion | PASS | Standard fenced loader `load_analysis_data` → `build_domain_frames` → first-70% slice only. FH truncation `min(start_idx + H, n - 1)` indexes within the rebuilt analysis-slice series. Verified against EXP-020 metadata. |
| `code/run_experiment.py` | Loader ordering | PASS | Lazy scan sorts by CloseTime before first-70% slicing. No full-dataset collection. |
| `code/run_experiment.py` | Memory/performance | PASS | Polars lazy scans with column projection. Rebuilt 4h series is small (≈3,700 bars). Vectorized NumPy FH construction with no per-event Python loops. Bounded plot inputs. |
| `code/run_experiment.py` | Safe optimization | PASS | All vectorization is causally equivalent (sequential indices, no look-ahead, no future rows). `freeze_selection` content-hash assert prevents silent divergences under rerun. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` on file-rebuild loop (4 instruments) and TEST-cell loop (3 cells). Null calibration loop shows `tqdm` with `leave=False`. |
| `code/run_experiment.py` | Logging/output | PASS | Concise INFO-level logging. Helpers return data, not print. Console summary line with per-cell verdict. |
| `code/run_experiment.py` | Organization/import side effects | PASS | VAL-001-style sectioning (imports → path setup → constants → I/O helpers → integrity guards → pure computation → TRAIN stage → TEST stage → plotting → orchestration). Output dirs created in `ensure_output_dirs()` called from `main()`. Frozen-tail module load at import matches the approved EXP-033/034 pattern. |
| `code/run_experiment.py` | Plot data reuse | PASS | Plots use TRAIN tie-break table and TEST verdict table directly (small in-memory dicts/CSV rows). No reload or regeneration of heavy data. |
| `code/run_experiment.py` | Docstrings | PASS | Module-level docstring documents the full structure and load-bearing controls. Each function has docstring with parameters, purpose, and expected outputs. |

## Numerical Validation

### Spot Checks

1. **EXP-033 reproduction (guard 1):** The 4h objective net at H=12 reproduces `EXP-033/results/fh_net_curve.csv` to within machine epsilon (7.1e-15 bps). Per-instrument counts: EURUSD 27, USTEC 25, XAUUSD 34 — exact matches.

2. **Population reconciliation (guard 2):** TRAIN+TEST counts per cell: EURUSD 27+12=39, USTEC 25+11=36, XAUUSD 34+8=42 — exact matches to EXP-030 full-analysis counts.

3. **Boundary convention divergence:** 0 events shift between the 1m-timestamp and bar-index conventions for all 4h cells — unlikely for a 0.7/0.3 split on a smooth sequence, but plausible given the 4h event count and verified as consistent across both experiments.

4. **H\* tie-break:** N(H) values reproduced {6.15, 20.95, 31.30, 39.11} bps with all retained (N>0, N1>0, N2>0). Max-min criteria H=12 (worst-half 41.07 bps) selected over H=8 (worst-half 29.80). Consistent with EXP-033 disclosure of `h_star_stable: false`.

5. **Null calibration margins:** EURUSD margin 8.4 bps (FPR uncorrected 0.105→0.05), USTEC 30.3 bps (0.104→0.05), XAUUSD 54.2 bps (0.163→0.05). The margins track sigma_b (65/184/134 bps) — the cross-cluster dispersion in the TRAIN nets — which is a sensible driver.

6. **TEST results:**
   - EURUSD: n=12, net=+40.56 bps, ci_low_1s=21.94 > margin 8.42, boot_p=0.001 → route_pass_provisional ✓
   - USTEC: n=11, net=+45.22 bps but ci_low_1s=-58.84 < margin 30.34, boot_p=0.244 → inconclusive ✓
   - XAUUSD: n=8, net=+21.59 bps, ci_low_1s=11.45 < margin 54.15, boot_p=0.001 → EVIDENCE_FOR but fails margin — correctly flagged as not provisional ✓

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|---------------|-------------|-------|
| h_star | {4, 6, 8, 12} or null | 12 | YES |
| Test n_events per cell | > 0 | [8, 11, 12] | YES |
| boot_p | [0, 1] | [0.001, 0.244] | YES |
| ci_low_1s | ℝ | [-58.84, 21.94] | YES |
| fpr_uncorrected | [0, 1] | [0.104, 0.163] | YES |
| Truncated share | {0.0, 1.0} | 0.0 (all 3 cells) | YES |

### Statistical Sanity

| Statistic | Value | Does it make sense? | Notes |
|-----------|-------|--------------------|-------|
| EURUSD boot_p | 0.001 | YES | Effect 40.56 bps with tight one-sided lower bound 21.94 > margin 8.42 — strong signal |
| USTEC boot_p | 0.244 | YES | Wide interval [-72.6, +158.7] at n=11; expected power-limited per scope |
| XAUUSD boot_p | 0.001 | YES | Effect 21.59 bps but large sigma_b (133.7 bps) drives margin to 54.2 — correct calibration |
| EURUSD margin | 8.42 bps | YES | sigma_b 65.0 bps from TRAIN dispersion; with 12 TEST events in 9 clusters, the Q95 of null ci_low_1s at 8.4 is consistent |
| H\* = 12 | 41.07 worst-half bps | YES | Monotone increasing N(H); H=12 is the best worst-half — consistent with the EXP-033 disclosure that 4h capture efficiency grows with horizon |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Regime-cluster bootstrap | Exchangeability within direction×regime strata | YES (calibrated) | R1.2 null calibration measured FPR uncorrected at 0.104–0.163 — confirms anti-conservative bias at small n. Margin correction restores FPR to 0.05. |
| Gaussian cluster null model | Zero-mean Gaussian cluster effects + errors adequate for coverage calibration | YES (disclosure) | Method-of-moments sigma_b/sigma_w from TRAIN nets. Calibration only measures bootstrap coverage geometry, not tail risk. Disclosed; components persisted. |
| H\* tie-break stability filter | N(H)>0 AND N1(H)>0 AND N2(H)>0 selects robust horizons | YES | All 4 horizons retained. H=12 selected by max-min — the most stable criterion. |

## Results Plausibility

Outputs are consistent with the Phase 008 design expectations:
- EURUSD-4h shows the strongest capture-efficiency benefit (route_pass_provisional), consistent with the D0 disclosure and EXP-031's −27 bps BTC drag finding.
- USTEC-4h is power-limited at n=11 (CI spans −73 to +159 bps), as predeclared.
- XAUUSD-4h at n=8 shows point evidence but the large cross-cluster dispersion (sigma_b 133.7 bps from only 4 TRAIN clusters) drives the margin to 54.2 bps — correctly flagged as not provisional.
- The `B2_NO_ROBUST_HSTAR` path was not triggered (all horizons retained), which is consistent with the EXP-033 disclosure of positive TRAIN FH nets across the candidate set.
- The `is_pyramid_bounce` composition shows only `all_legs` was selected (first_leg_only: n=50 below min events for USTEC; pyramid_legs_only: n=36, USTEC=10 below 15). This matches EXP-033's `policy_stable = true` and the D0 pyramid-policy disclosures (pyramids are the stronger legs on 4h).

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 1 test family / 1 (budgeted 1); 3 plots / 3 (budgeted 3); 1 module / 1 (budgeted 1)
- Holdout exclusion verified: YES — first-70% loader fence, FH truncation within analysis set, boundary from 1-minute analysis rows only.

## Issues

### Critical

None.

### Warning

None.

### Info

1. **XAUUSD low TEST count (n=8).** The XAUUSD-4h TEST stratum has only 8 events, down from the ~13 expected in the power statement. This is driven by the `all_legs` policy (the only feasible choice under the pre-freeze feasibility filter), and the 8 events all have `is_pyramid_bounce = false` (from `train_tiebreak.csv`: XAUUSD has 0 pyramid legs out of 34 TRAIN events, but TEST pyramid composition is not checked against the power statement floor). The reduced sample does not change the verdict (margin 54.2 >> ci_low_1s 11.45), and the lower-than-expected count is a natural property of the 30% chronological split under the pyramid policy. Disclosed for awareness.

2. **`train_tiebreak.csv` column structure.** Row 6 (H=12, policy=all_legs) duplicates H=12 from rows 1-5 but adds the `se` column for the selected policy. The duplicate horizon column is a presentation convenience (the same tie-break output, disclosed with the policy bootstrap SE). No duplicate inference or double-counting — verified that the TEST stage reads only the frozen file's single H\*/policy.

## Re-Audit Requirements

None — PASS.
