# Audit Report: Experiment EXP-019

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 1

EXP-019 results are suitable for interpretation. The current dependency manifest and metadata show all upstream artifacts and the predeclared dogfood reference book were found, the suite ran to `overall_status = COMPLETE`, and the suite summary recomputes from the standalone and incremental output rows. The only note is a stale `blocker_report.csv` left from an earlier blocked state; it is superseded by the current completed metadata and is not used as measurement evidence.

## Code Review

| File | Check | Verdict | Notes |
| --- | --- | --- | --- |
| `python/experiments/EXP-019/code/run_experiment.py` | Dependency gate | PASS | Requires EXP-009 COMPLETE, EXP-012 COMPLETE, EXP-018 COMPLETE, finite EXP-018 domain MDEs, and dogfood reference-book inputs at lines 130-233. |
| `python/src/xen/referee_calibration.py` | Holdout exclusion | PASS | Shared loader sorts by `CloseTime`, slices the first 70 percent, and only then collects at lines 120-143. |
| `python/experiments/EXP-019/code/run_experiment.py` | Reference-book discipline | PASS | Loads only predeclared `dogfood_reference_book.csv` and validates required columns at lines 430-442. |
| `python/experiments/EXP-019/code/run_experiment.py` | Timestamp alignment | PASS | Aligns reference positions to domain return rows by `CloseTime` and raises on missing joined rows at lines 445-464. |
| `python/experiments/EXP-019/code/run_experiment.py` | Dogfood negative path | PASS | Uses first-70% domain frames, excludes the reference family from candidates, and applies strict/loose/incremental suite components at lines 470-540. |
| `python/experiments/EXP-019/code/run_experiment.py` | Synthetic positive path | PASS | Builds and checks nonredundant positive fixtures before running suite components at lines 610-697. |
| `python/experiments/EXP-019/code/run_experiment.py` | Composition summary | PASS | Rule-based summary checks reject/pass path exercise at lines 703-738. |
| `python/experiments/EXP-019/code/run_experiment.py` | Output status | PASS | `overall_status = COMPLETE` only when every path/domain status is expected at lines 890-923. |
| `python/src/xen/incremental_referee.py` | Revised gate | PASS | Revised incremental verdict uses L1/L3/L4'/strict-L5 and defaults to no standalone L2 bootstrap at lines 605-637. |

## Numerical Validation

### Spot Checks

- `dependency_manifest.csv`: 3 `COMPLETE` upstream metadata rows and 8 `FOUND` artifact/input rows.
- `suite_manifest.csv`: 3 domains; strict MDEs 1/4/12 bps, ratified-loose MDEs 0.5/2/8 bps, revised incremental MDEs 12/16/32 bps.
- `suite_composition_summary.csv`: six path/domain rows; all dogfood rows `REJECT_PATH_EXERCISED`, all synthetic rows `PASS_PATH_EXERCISED`.
- Recomputed suite summary from `standalone_suite_verdicts.csv` and `incremental_suite_verdicts.csv`: exact match to reported pass counts and row counts.
- `positive_fixture_manifest.csv`: 3/3 `nonredundancy_ok = true`.

### Path Counts

| Path | Domain | Strict Passes | Loose/Fallback Passes | Incremental Passes | Status |
| --- | --- | ---: | ---: | ---: | --- |
| dogfood_negative | 5m | 0 | 0 | 0 | REJECT_PATH_EXERCISED |
| dogfood_negative | 1h | 0 | 0 | 0 | REJECT_PATH_EXERCISED |
| dogfood_negative | 4h | 0 | 0 | 0 | REJECT_PATH_EXERCISED |
| synthetic_positive | 5m | 1 | 1 | 1 | PASS_PATH_EXERCISED |
| synthetic_positive | 1h | 1 | 1 | 1 | PASS_PATH_EXERCISED |
| synthetic_positive | 4h | 1 | 1 | 1 | PASS_PATH_EXERCISED |

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
| --- | --- | --- | --- |
| Dogfood standalone passes | 0 | 0 across 120 standalone rows | YES |
| Dogfood incremental passes | 0 | 0 across 60 incremental rows | YES |
| Synthetic standalone passes | > 0 per domain | 1 strict and 1 loose/fallback per domain | YES |
| Synthetic incremental passes | > 0 per domain | 1 per domain | YES |
| Dogfood incremental CI lower | <= materiality / no positive pass | max -0.011632285276116226 | YES |
| Synthetic incremental CI lower | > incremental materiality | 15.9645, 23.9406, 39.9333 bps | YES |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
| --- | --- | --- | --- |
| Suite assembly | Upstream strict, loose, and incremental artifacts are present and finite | YES | `dependency_manifest.csv` and `suite_manifest.csv`. |
| D-dogfood-book | Reference book was predeclared and present | YES | `dependency_manifest.csv` marks book and manifest FOUND; metadata records reference family `donchian_20`. |
| Dogfood negative path | Candidate slate excludes the reference family | YES | `run_metadata.json` records `dogfood_reference_family_excluded_from_candidates = donchian_20`; dogfood candidate rows contain the remaining five families. |
| Positive path | Fixture is nonredundant and exercises pass path | YES | `positive_fixture_manifest.csv` all `nonredundancy_ok = true`; synthetic rows pass all suite components. |
| Holdout discipline | Final 30 percent global holdout excluded | YES | Real dogfood path uses `load_analysis_data()` before domain construction; positive path is synthetic in-memory data. |

## Results Plausibility

The outputs match the checkpoint expectation for an integration anchor: the EXP-009 dogfood family remains a negative path, while the synthetic fixture proves the pass path can be exercised across the strict, ratified-loose, and revised incremental components. The dogfood incremental CI lower bounds remain negative in every row, so no hidden positive incremental evidence drives a pass.

## Scope Compliance

- Analysis plan followed: YES
- Deviations: none
- Complexity budget: 4 measurements / 4 budgeted, 5 plots / 5 budgeted, 0 new modules / 1 budgeted
- Holdout exclusion verified: YES

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Stale blocker report remains in results directory**
   - File: `python/experiments/EXP-019/results/blocker_report.csv`
   - Description: The file still contains an earlier blocked-state message that the dogfood reference book was missing. The current `dependency_manifest.csv` marks the book FOUND, and `run_metadata.json` records `overall_status = COMPLETE`.
   - Impact: No impact on measured results or interpretation. Treat the current dependency manifest, run metadata, suite manifest, and composition summary as authoritative for the completed run.

## Re-Audit Requirements

None. The EXP-019 artifacts are suitable for interpretation. A future rerun should clear or overwrite stale blocker artifacts on success to reduce confusion.
