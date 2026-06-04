# Audit Report: Experiment EXP-011

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 3

EXP-011 was re-audited against the hard-gated dependency code, the data-derived adoption caveats, and the corrected EXP-010 split overlay. It is a deterministic result-level synthesis: no raw market data is loaded, the predeclared Loss A/B/C selections reproduce from the saved CSVs, all scoped dependency tokens are COMPLETE, and the recommendation remains 5m tau 0.75, 1h tau 0.25, 4h tau 0.5.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Dependency gates | PASS | Hard-gates EXP-003/005/006/007/008/009/010 to COMPLETE and requires EXP-006 strict-reference plus EXP-007 structural-equivalence checks (lines 132-172). |
| `code/run_experiment.py` | Holdout exclusion | PASS | Reads result-level CSV/JSON artifacts only; searches found no `data/timebars`, `scan_parquet`, `read_parquet`, or raw-data glob in EXP-011 code. |
| `code/run_experiment.py` | Decision table | PASS | Builds one row per domain/tau at alpha0, attaches materiality and FPR reportability, and preserves strict/lenient flags (lines 186-200). |
| `code/run_experiment.py` | Sub-material reconstruction | PASS | Projects and filters EXP-006/EXP-003 draw CSVs before collection, joins on the full draw key, guards unmatched rows, and defines zero-pass sub-rate as 0.0 (lines 206-262). |
| `code/run_experiment.py` | EXP-007 reproduction | PASS | Reconstructed tau=0 sub-material rates must match EXP-007 within tolerance before recommendations are emitted (lines 265-280). |
| `code/loss_functions.py` | Loss-rule correctness | PASS | Loss A, B, C, sub-material limit, and one-grid-step consistency are frozen and mechanical (lines 23-39, 61-160). |
| `code/run_experiment.py` | Loss evaluation | PASS | Evaluates Loss A/B/C per domain and emits `RECOMMENDED` only when primary Loss A is selectable (lines 371-405). |
| `code/run_experiment.py` | Context overlays | PASS | EXP-008/009/010/005 overlays are read-only caveats and do not re-select tau (lines 411-447). |
| `code/run_experiment.py` | Adoption caveats | PASS | Split caveats are derived from the corrected EXP-010 overlay, not a hardcoded narrative; 5m/1h are split-robust, 4h is split-material (lines 459-510). |
| `code/run_experiment.py` | Outputs and metadata | PASS | Writes deterministic result tables, `adoption_rule.json`, `run_metadata.json`, and four scoped plots; metadata records `scoped_overlays_complete = true` plus method notes (lines 642-756). |
| `code/run_experiment.py` | Import side effects / logging | PASS | Output directories are created only in `main()`; plotting consumes small Step 2-6 tables only (lines 675-756). |

## Numerical Validation

### Spot Checks

Saved artifact checks:

- `run_metadata.json`: `overall_status = COMPLETE`, `measurements_produced = true`, `submaterial_repro_check = true`, `scoped_overlays_complete = true`, `inconclusive_domains = []`.
- Dependency tokens: EXP-003, EXP-005, EXP-006, EXP-007, EXP-008, EXP-009, and EXP-010 all `COMPLETE`.
- Output dimensions: `decision_table.csv` 21 rows, `sub_material_by_tau.csv` 210 rows, `loss_evaluation.csv` 9 rows, `recommendation.csv` 3 rows.
- Every decision row is reportable: `fpr = 0.0`, `fpr_wilson_half_width = 0.000479739258416217`, and `fpr_wilson_upper = 0.000959478516832434`.
- `sub_rate` in `decision_table.csv` matches the reconstructed `sub_material_by_tau.csv` at each row's operating MDE.

Manual recomputation of the three losses reproduced the saved recommendations:

| Domain | Loss A tau* | Loss B tau* | Loss C tau* | Saved verdict | Independent check |
|--------|-------------|-------------|-------------|---------------|-------------------|
| 5m | 0.75 | 0.75 | 0.25 | LOSS_SENSITIVE, spread 2, driver `sub_material` | MATCH |
| 1h | 0.25 | 0.25 | 0.0 | ROBUST, spread 1 | MATCH |
| 4h | 0.5 | 0.5 | 0.0 | LOSS_SENSITIVE, spread 2, driver `blind_band` | MATCH |

### Overlay Checks

`adoption_rule.json` is consistent with corrected upstream artifacts:

- EXP-005 detection status is `DETECTED_FLOOR` for 5m, 1h, and 4h.
- EXP-009 `n_at_or_above_mde = 0` for every domain.
- EXP-008 material per-instrument overlays: EURUSD on 1h; EURUSD and XAUUSD on 4h; none on 5m.
- EXP-010 split overlay: `walk_forward_material = false` on 5m and 1h, `true` on 4h.

### Range Checks

| Metric | Expected Range | Actual Range | Pass? |
|--------|----------------|--------------|-------|
| `fpr` | [0, 1] | 0.0 for all 21 decision rows | YES |
| `fpr_wilson_upper` | <= 0.05 for selectable rows | 0.000959478516832434 for all rows | YES |
| `mde_bps` | finite grid value | 5m 0.5-2.0, 1h 2.0-8.0, 4h 8.0-16.0 | YES |
| `sub_rate` at operating MDE | [0, 1] | 5m 0.0-0.4965, 1h 0.0-0.054653679653679656, 4h 0.0 | YES |
| `pass_count` in sub-material table | >= 0 | 0-2000 | YES |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|------------|--------|----------|
| Result-level synthesis | Upstream artifacts are complete and frozen | YES | All dependency tokens complete; missing/incomplete context dependencies now fail before output. |
| Loss A | FPR upper bound gates selectable cells, then MDE/sub-material/tau tie-breaks apply | YES | Independent selection reproduces 5m 0.75, 1h 0.25, 4h 0.5. |
| Loss B | Normalized blind-band, FPR, and sub-material terms use frozen unit weights | YES | Independent scalar choices match `loss_evaluation.csv`. |
| Loss C | Material-edge prior uses fixed grid points inside `[materiality, 4 * materiality]` | YES | `run_metadata.json` records 5m `{0.5,1.0,2.0}`, 1h `{2.0,4.0}`, 4h `{4.0,8.0,12.0}`. |
| Context overlays | EXP-005/008/009/010 do not re-select tau | YES | Overlays appear only in `adoption_rule.json` and adoption plot context; `recommendation.csv` comes from Loss A. |

## Results Plausibility

The recommendation is coherent with the Phase 002 record:

- 5m recommends `tau = 0.75` with MDE 0.5 bps and sub-material rate 0.39759036144578314; this keeps the lower MDE while staying under the 0.50 sub-material cap.
- 1h recommends `tau = 0.25` with MDE 2.0 bps and sub-material rate 0.026223776223776224; the cross-loss spread is one grid step, so the recommendation is robust.
- 4h recommends `tau = 0.5` with MDE 8.0 bps and sub-material rate 0.0; Loss C prefers the zero-buffer endpoint, so the domain is loss-sensitive.
- Corrected EXP-010 caveats now flag only 4h as split-sensitive; 5m and 1h are split-robust.

## Scope Compliance

- Analysis plan followed: YES.
- Deviations: none found in the corrected artifacts.
- Complexity budget: 2 / 2 statistical operations, 4 / 4 plots, 1 / 1 new modules.
- Holdout exclusion verified: YES.
- Recommendation status: all three domains `RECOMMENDED`; no inconclusive domains.
- Adoption status: no operating point is adopted or frozen in Phase 002.

## Issues

### Critical

None.

### Warning

None.

### Info

1. **Loss C is weakly independent on this substrate**
   - Since FPR is zero for every tau, Loss C reduces largely to missed-material-edge risk and is monotone toward low tau. The report/results disclose this as a caveat.

2. **Loss A can admit material sub-rate trade-offs**
   - 5m tau*=0.75 carries sub-material rate 0.39759036144578314 at the operating MDE. This is below the predeclared 0.50 cap but material context for Phase 003.

3. **Recommendation is not adoption**
   - EXP-011 records a Phase 002 recommendation and conditional adoption rule only. Fresh Phase 003 draws must ratify any tau change.

## Re-Audit Requirements

None.
