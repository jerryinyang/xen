VERDICT: APPROVE

# Post-Experiment Governance Review: VAL-001 (rev. 3)

This supersedes the rev. 2 post-experiment review (retained in git history). It
reviews the re-run performed in place after the rev. 3 pre-execution approval.

## Reviewed Artifacts

- `python/experiments/VAL-001/audit.md` (rev. 3)
- `python/experiments/VAL-001/results.md` (rev. 3)
- `python/experiments/VAL-001/report.md` (rev. 3)
- `python/experiments/INDEX.md`
- `docs/experiments-docs/INDEX.md`
- `python/experiments/VAL-001/results/` and `plots/` (regenerated 08:50)

## Verdict Rationale

VAL-001 rev. 3 passes post-experiment governance. The audit reports PASS with 0
critical issues and 0 warnings. Interpretation is anchored to the predefined
success criteria, and the report and indexes preserve the same finding without
expanding scope. The three detection-power gaps that motivated rev. 3 are closed
and evidenced by the regenerated results.

## Governance Checks

| Constraint | Verdict | Evidence |
|------------|---------|----------|
| Scope discipline | PASS | One architecture-validation question; no strategy/return/P&L/forecasting/tuning claims added. Coverage strengthened, not expanded. |
| Holdout rule | PASS | Loader unchanged; results report first-70% analysis-slice counts (BTCUSD 1,088,960, etc.) with analysis-end timestamps before the holdout. Multi-position probe `tail` windows sit inside the analysis slice. |
| Look-ahead prevention | PASS | 60/60 prefix-stability checks PASS at head/middle/tail (0 diverged cuts); injected look-ahead generator detected at all 3 cut points. |
| Timestamp alignment | PASS | Time bars/resamples use `CloseTime`; Line Break/Renko use `SourceCloseTime`; full-output alignment checked on every emitted row; no bar-index alignment. |
| Real-price discipline | PASS | No returns, P&L, stops, targets, or signal outcomes. Synthetic prices validated only as data-layer fields. |
| Negative-control detection | PASS | 23/23 controls detected; coverage spans every base-integrity, resample, sparse-chart, HA, schema, look-ahead, and determinism check. Determinism control now routes a genuinely non-deterministic generator through the real check. |
| Statistical assumptions | PASS | No statistical tests; deterministic validation conclusions only. |
| Complexity budget | PASS | 0 statistical tests / 0; 2 plots / 2; 0 new modules / 0. |
| Audit thoroughness | PASS | Covers scope compliance, holdout, alignment, negative-control integrity, determinism reproducibility, numerical spot checks, plot/table consistency, and limitations; raises 3 non-blocking Info notes. |
| Results interpretation | PASS | Concrete values, evidence separated from interpretation, SUPPORTED verdict, limitations and alternative explanations included. |
| Final report | PASS | Self-contained, includes both plots, documents the rev. 3 changes and limitations, links artifacts, does not overstate predictive/trading implications. |
| Index updates | PASS | Both indexes show COMPLETED (rev. 3) with 416/416 PASS and 23/23 controls. |

## Verification Performed

- Confirmed all required post-execution artifacts exist and were regenerated.
- Confirmed `validation_checks.csv` has 416 rows, all PASS (98 per real
  instrument + 24 synthetic).
- Confirmed `negative_controls.csv` has 23 controls, all detected.
- Confirmed generator outputs reproduce rev. 2 (densities, event counts, and the
  107,824 / 128,556 Renko duplicate totals are byte-identical).

## Notes (non-blocking, carried from audit)

- A few structural/informational checks (`required_columns_present`,
  `single_symbol_per_file`, `timeframe_source_is_base`, `analysis_slice_loaded`)
  have no negative control; they are availability/informational checks, not core
  integrity assertions.
- No active checkpoint `design.md`; phase alignment limited to the scope's
  thesis-readiness framing.
- `run_metadata.json` records parameters and probe configuration but not a code
  hash.

## Decision

APPROVE. VAL-001 (rev. 3) is complete.
