# Audit Report: Experiment EXP-032

One-Shot Holdout Confirmation of Package B (EURUSD-4h, FH H\*=12, all_legs).
Registry `CF-AVWAP-001/HOLDOUT-B` — the programme's single sanctioned holdout read.
Audited 2026-06-10. **The audit read ONLY persisted artifacts** (`holdout_events.csv`,
`analysis_fh_nets.csv`, `holdout_verdict.csv`, `frozen_holdout_manifest.json`,
`run_metadata.json`, `null_calibration.csv`, `reconciliation.csv`) — no holdout row
was recomputed or re-read, per analysis-plan Step 5 (F01).

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 4

The implementation matches scope.md and analysis-plan.md (Revision 1) exactly. All
8 scoped integrity guards passed with persisted evidence. The binding verdict
**HOLDOUT_INCONCLUSIVE** (descriptive **INCONCLUSIVE_SPANS_ZERO**) is mechanically
correct from the persisted numbers: `ci_low_1s` 2.7086 ≤ margin 4.3189 (so not
CONFIRMED despite `boot_p` 0.0290 ≤ 0.05), `ci_high` 42.15 > 0 (so not REFUTED).
Every per-event and cell-level quantity I recomputed independently from the
persisted artifacts reproduces the verdict row to ≤ 4e-15 bps.

## Code Review

File: `python/experiments/EXP-032/code/run_experiment.py` (1140 lines, single
orchestration module; all analysis machinery imported verbatim from EXP-037/EXP-022
code paths, `xen.avwap`, `xen.bar_aggregator`, `xen.financing`, frozen EXP-027 tail).

| Check | Verdict | Notes |
|------|---------|-------|
| Correctness | PASS | FH net construction delegated to verbatim `EXP037.add_fh_net_columns` / `infer_test_cell`; guard 1c proves the estimator path reproduces the EXP-037 TEST anchor to 3.6e-7 bps (`reconciliation.csv`: 40.55888164 vs 40.558882, tol 0.01). |
| Edge cases | PASS | Series-end truncation handled (`min(si + 12, n-1)`), disclosed per event and as `truncated_share`; empty-stratum and missing-artifact paths raise hard stops; BTC companion handles unfinished events (none occurred, 27/27 completed). |
| Holdout access protocol | PASS | Sanctioned EURUSD full-series read only; `eurusd_source_path` rejects non-EURUSD resolution; `load_full_eurusd` asserts loader equivalence on the analysis prefix; seal check (`seal_only_eurusd_file_opened` = 1 file) PASS; no 5m/1h holdout aggregation, no per-bar suite import. |
| Freeze-before-outcome (guard 5) | PASS | `run_h2` (line 769ff) refuses without a hash-verified manifest; population/margin/constants read only from it; live regeneration key-matched against frozen keys (hard stop on divergence). |
| No-second-read (guard 6) | PASS | `run_h2` hard-stops if `holdout_verdict.csv` exists; verdict file written LAST as completion marker (code lines 877–880); post-verdict plots read persisted CSVs only (lines 1117–1122). |
| Two-invocation barrier (F03) | PASS | `--phase h1`/`--phase h2` CLI; H2 re-runs the deterministic H1 pipeline and must hash-match the frozen manifest (R1.6). Corroborated on disk: manifest mtime precedes all H2 artifacts by 41 s and was NOT rewritten by H2 (hash-match path returns existing record without write). |
| H1 outcome-freedom | PASS | `build_population` mirrors EXP-022 `_event_with_controls` up to and excluding the lifetime scan; no price-difference quantity over holdout rows is reachable in H1 (the only nets computed in H1 are the 39 disclosed analysis events on the analysis-only 4h series, guard 1c/dispersion input). |
| Hash pins (guards 2/3) | PASS | Independently recomputed: EXP-037 `frozen_selection.json` content hash == pinned `2bbbf65b…770b0fea`, H\*=12/all_legs confirmed; manifest `content_sha256` verifies and matches `run_metadata.json`; frozen-tail verification via `EXP037.verify_frozen_inference()` before anything else in `main()`. |
| Loader ordering | PASS | Lazy scan, column projection (`REQUIRED_TIMEBAR_COLUMNS`), `sort("CloseTime")` before collection, sortedness asserted; full collection is the sanctioned Phase 009 §5 exception for EURUSD only. |
| Memory/performance | PASS | Single full-series load reused by H1/H2/plots; one 4h rebuild per universe; bounded row loops (77 generated events; 27 holdout events); plots take bounded arrays from persisted CSVs. |
| Safe optimization | PASS | No vectorization that alters membership, ordering, denominators, or causal semantics; generator runs as the sequential stateful stream. |
| Progress tracking | PASS | `tqdm` on the 2000-replicate null calibration loop. |
| Logging/output | PASS | Concise orchestration-level INFO logging; helpers return data. |
| Organization/import side effects | PASS | VAL-001-style sectioning; `ensure_output_dirs()` called only in `main()`; no data loads or plotting at import. (Module-level `_load_module` of EXP-037/EXP-022 executes those scripts' definitions at import — both are import-safe with `main()` guards; see Info 4.) |
| Plot data reuse | PASS | All three plots render from `holdout_events.csv` / `analysis_fh_nets.csv` / the in-memory verdict row — no second holdout pass. |
| NaN handling | PASS | `net_btc` explicitly nullable for unfinished BTC events (none occurred); no silent NaN propagation in the binding column (27/27 finite). |
| Type hints / docstrings | PASS | All public functions typed and documented with guard semantics. |
| Determinism (guard 8) | PASS | Same-seed inference replay drift 0.0 ≤ 1e-12 (`run_metadata.json: determinism_replay.passed = true`); seeds namespaced ("EXP-032", "holdout"/"nullcal"/plot jitter). |

## Numerical Validation

### Spot Checks (independent recomputation from persisted artifacts)

- **Per-event net identity:** `net_12 = fh_12 − 3.0 − financing_bps` holds for all
  27 events, max abs error 0.0. `financing_bps = 0.6 × financing_days` exact for
  all 27.
- **Cell aggregates:** mean(`net_12`) = 20.596878751440496 vs verdict 20.5968787514405
  (diff 3.6e-15); gross 25.263529986 exact; financing mean 1.666651235 exact;
  decomposition `gross − RT − financing − net` = −3.6e-15.
- **Verdict logic replayed:** `ci_low_1s` 2.7086 > 4.3189? NO and `boot_p` 0.0290 ≤
  0.05 → not CONFIRMED; `ci_high` 42.15 < 0? NO → not REFUTED →
  **HOLDOUT_INCONCLUSIVE**; `ci_low` −0.389 < 0 < `ci_high` →
  **INCONCLUSIVE_SPANS_ZERO**. Both match the persisted verdict.
- **Weekend financing spot-check (plan-mandated):** event 3594, entry Thu
  2025-05-29 08:00 → exit Mon 2025-06-02 12:00; hand-computed elapsed = 4 + 4/24 =
  4.16667 fractional calendar days (weekend included), financing = 0.6 × 4.16667 =
  2.500 bps — matches `run_metadata.json` and the per-event row exactly.
- **Truncation:** flags equal `start_idx + 12 > 5023` for all 27;
  `fh_exit_idx = min(start_idx + 12, 5023)` for all 27; exactly 1 truncated event
  (trigger 5016, exits at last bar 5023) → share 1/27 = 0.037037, as persisted.
- **BTC companion:** mean(`net_btc`) = 2.3492355184 over 27/27 completed events —
  matches; labeled NON-BINDING in the verdict row.
- **Boundary/membership:** all 27 `trigger_ns` > manifest `boundary_ns` (min gap
  ≈ 19.6 days); manifest stratum keys == per-event table keys (27/27); triggers
  strictly increasing.
- **Hashes:** manifest content hash recomputed == stored == `run_metadata.json`;
  EXP-037 selection hash recomputed == pinned value.

### Range Checks

| Metric | Expected Range | Actual | Pass? |
|--------|---------------|--------|-------|
| `direction` | {+1, −1} | {−1, +1} | YES |
| `start_close` (EURUSD) | ~1.0–1.3 | [1.12761, 1.18797] | YES |
| `net_12` (bps) | plausible 4h-event scale (analysis era spans ±~150) | [−98.17, +133.70] | YES |
| `financing_days` | (0, ~5] for a 12×4h hold | [1.166, 4.167] | YES |
| `n_controls` | ≥ 5 (MIN_CONTROLS) for binding events | all 5 | YES |
| `trigger_ns` | monotone increasing, all > boundary | confirmed | YES |
| `boot_p` | (1+k)/(1+1000) grid | 0.028971 = 30/1001 | YES |

### Statistical Sanity

| Statistic | Value | Makes sense? | Notes |
|-----------|-------|--------------|-------|
| n_events | 27 | YES | Above the predeclared 15–18 expectation (Info 1); plan makes this disclosure-only — H2 correctly ran regardless. |
| net mean / CI | +20.60, two-sided [−0.39, 42.15] | YES | Wide CI at n=27 with σ_w≈30, σ_b≈58 bps; consistent with the predeclared power statement (effect below TEST's +40.56 → INCONCLUSIVE expected). |
| ci_low_1s vs margin | 2.71 vs 4.32 | YES | The margin (Q95 of null ci_low_1s) is exactly the anti-conservatism correction the calibration measured: uncorrected null FPR 0.0715 > 0.05, with-margin FPR 0.050. The dual rule worked as designed. |
| margin 4.32 vs EXP-037's 8.42 | YES | Smaller margin at n=27/16 clusters vs n=12 — direction consistent with more events/clusters tightening the null ci_low_1s distribution; confirms the plan's rationale for recomputing rather than reusing 8.42. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Frozen regime-cluster bootstrap | Cluster exchangeability within direction strata; coverage at this cell structure | PARTIAL→corrected | Measured uncorrected null FPR 0.0715 (anti-conservative at this structure); binding rule uses the calibrated margin, restoring FPR 0.05. Exactly the R1.2 design intent. |
| Gaussian cluster null (calibration vehicle) | Analysis-era variance components transport to holdout layout | DISCLOSED CAVEAT | σ_b = 57.85, σ_w = 29.98 from the 39 disclosed analysis nets; F05 calibration-fidelity caveat is predeclared and only binds a CONFIRMED verdict (outcome is INCONCLUSIVE, so it is not load-bearing here). Plot 3 shows holdout dispersion not visibly above analysis era. |
| Ex-post reportability (F04) | Binding population conditions on post-entry regime evolution | DISCLOSED | All 27 pre-reportability holdout events were reportable (counts persisted); the mandatory F04 disclosure must still accompany results.md/report.md. |

## Results Plausibility

Holdout mean +20.60 bps sits between the EXP-038 baseline scale (+24.27) and zero,
well below the EXP-037 TEST point (+40.56) — precisely the scenario the predeclared
power statement flagged as likely INCONCLUSIVE. The BTC-exit companion (+2.35 bps,
non-binding) is directionally consistent with EXP-031/033's finding that the BTC
exit drags at long horizons. The analysis-vs-holdout plot context (analysis mean
+32.87, n=39 vs holdout +20.60, n=27) shows attenuation, not reversal. Nothing
implausible.

## Scope Compliance

- Analysis plan followed: YES (Revision 1, including F01 persistence order, F03
  two-invocation execution, F04/F05 disclosure machinery).
- Deviations: none.
- Complexity budget: 1/1 test family (frozen bootstrap on one cell; null
  calibration is synthetic-data verification of the same family); 3/3 plots;
  1/1 new module (orchestration only).
- Holdout access: COMPLIANT with the Phase 009 §5 sanctioned-release protocol —
  EURUSD full-series read disclosed in `files_opened`; only one data file opened;
  BTCUSD/USTEC/XAUUSD holdout untouched. The standard exclusion rule is superseded
  for EURUSD within this scope only, per scope.md and the Phase 009 design.
- One-shot discipline: verdict file exists → shot SPENT; `holdout_spent = true`
  persisted in verdict and metadata; no-second-read guard now active for any rerun.

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Holdout count above the predeclared expectation (27 vs 15–18).**
   - Description: `frozen_holdout_manifest.json` records 27 binding events vs the
     scope's ≈15–18 power expectation. The plan explicitly classifies this as
     disclosure-only (no attribute-based discretion between freeze and read), and
     the code logged it without halting — correct behavior. The larger n if
     anything improved power; the verdict is still INCONCLUSIVE on the margin
     condition. Worth one line in results.md.
2. **CONFIRMED missed on the margin, not the p-value.**
   - Description: `boot_p` = 0.029 passed the α gate; the verdict turned on
     `ci_low_1s` 2.71 ≤ m_cell 4.32. Interpretation (Stage 6) should state this
     precisely: a positive but margin-insufficient lower bound under a calibration
     that measured uncorrected FPR 0.0715 at this exact structure.
3. **All holdout events reportable (pre == post = 27).**
   - Description: the reportability filter removed nothing in the holdout stratum.
     The mandatory F04 ex-post-reportability external-validity disclosure still
     applies to results.md/report.md (the estimand conditions on ex-post
     reportability even when the filter binds nothing here).
4. **Prior-experiment scripts loaded at import time.**
   - Description: `_load_module` executes EXP-037/EXP-022 `run_experiment.py` at
     module import (lines 124–130). Both are import-safe (`main()` guards, no
     import-time I/O beyond constants), and this is the predeclared "reused
     verbatim" mechanism, so no side-effect violation results. Noted for awareness
     only.

## Re-Audit Requirements

None — unconditional PASS. Per the one-shot discipline, no defect found here or
later could ground a rerun: a post-H2 defect would be a disclosed defect in a
spent shot. None was found.
