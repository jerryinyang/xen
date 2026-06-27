# EXP-042 — Pre-Execution Governance Review (Stage 4)

**Date:** 2026-06-11
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`,
modified module `python/src/xen/avwap.py`, against
`research-pipeline/references/governance-constraints.md`, the developer code
conventions, and the Phase 011 checkpoint `design.md` (+ D0 predeclarations,
G0 PASS 2026-06-11).

## Checks

- **Phase alignment:** Track A0 per design §5.2; G0 passed before any TRAIN
  contact; all scan parameters (horizons {4,8,16}, binding H=8, floor 30,
  bands, `min_coverage=0.90`) trace to frozen predeclarations — none is a
  tuning lever. PASS.
- **Entry-rule amendment:** the implementation review disclosed that the
  frozen substrate's band multiplier had no entry role (sweep would be
  vacuous). Resolved by operator ratification (arm-at-adverse-band; trigger
  unchanged) **before any TRAIN read**, recorded in scope.md, the design
  amendment log, and the multiplicity registry, with the b=1.0
  population-discontinuity disclosure. PASS (no data contact preceded the
  decision).
- **Holdout / TEST exclusion:** lazy scan → column projection → sort by
  `CloseTime` → `head(train_rows)` → collect; TEST and global-holdout rows are
  never materialized; power-statement TEST counts are boundary arithmetic
  only. R1.3 1-minute-row boundary; `train_end_ts` recorded per instrument.
  PASS.
- **Look-ahead / causality:** substrate is the sequential streaming state
  machine (unchanged semantics; new arm threshold uses the same-bar causal
  MAD median); forward returns use only bars after the trigger within TRAIN;
  windows spilling past the TRAIN end are excluded from that horizon's
  denominator. No cross-view alignment in scope. PASS.
- **Real prices:** returns on real domain Close (aggregated from 1-minute
  real bars); no synthetic chart prices anywhere. PASS.
- **Denominators / zero baseline:** per-horizon per-band per-cell
  denominators written explicitly; means emitted only for n ≥ 1; the floor
  rule absorbs degenerate cells; no division by zero (guarded); the
  DEGENERATE_FLOOR disclosure is computed mechanically. PASS.
- **Mechanical selection:** rank → floor imputation (worst rank 5) → median
  rank → wider-band tie-break implemented exactly as frozen; tie handling
  within a cell uses average ranks (deterministic). Helper functions
  unit-spot-checked (tie-break to wider band; floored band ranked worst
  despite best mean). PASS.
- **Code conventions:** sectioned organization; no import-time side effects
  (verified by import); dirs created in `main()` only; `tqdm` over the
  17-instrument outer loop; concise logging, quiet helpers; bounded memory
  (one instrument at a time, 1-minute frame dropped after use); plots reuse
  analysis outputs, no reloads; type hints and docstrings on public
  functions; deterministic (no randomness; SHA-256 of `band_scan.parquet`
  in metadata). PASS.
- **Complexity budget:** 0 statistical tests; 3 plots; 0 new modules (one
  backward-compatible parameterization of the existing `xen.avwap`
  generator — defaults reproduce the frozen baseline, verified by a
  determinism smoke test). Within budget. PASS.
- **Scope discipline:** no cost overlay, no CIs, no per-cell selection, no
  grid beyond the predeclared 5 bands; success criteria are mechanical
  (BAND_SELECTED always reachable; INCONCLUSIVE correctly unavailable).
  PASS.

**Info (non-blocking):** `main()` exceeds ~30 lines (orchestration; sectioned
and linear). The plan's `train_end_ts` containment assertion is tautological
under the head-slice construction; the boundary is recorded in metadata
instead — equivalent guarantee.

## Verdict

```text
VERDICT: APPROVE
```

## Addendum — 2026-06-11 adversarial-review fixes (pre-execution, no data contact)

Five findings (F01–F05) were raised against the approved package and resolved
before any TRAIN read:

- **F01 (Critical, fixed):** the original loader's full-file
  `sort("CloseTime")` would have evaluated over TEST/holdout rows. Replaced
  with file-order `head(train_rows)` (row count from Parquet metadata) + a
  hard sortedness assertion on the collected TRAIN slice (source order is
  VAL-001 rev. 3 / VAL-003 validated). Sealed rows now never enter the scan
  engine. The original holdout-exclusion PASS above is superseded by this
  stronger guarantee.
- **F03 (Major, fixed):** DEGENERATE_FLOOR now withholds the band freeze
  pending operator adjudication
  (`verdict = BAND_SELECTED_DEGENERATE_FLOOR_PENDING_ADJUDICATION`); scope
  amended accordingly (pre-read).
- **F04 (Major, fixed):** committed regression suite
  `python/tests/test_avwap_band_param.py` (baseline anchor 69 events,
  multiplier-invariance in baseline mode, determinism, monotonicity,
  bull/bear arm unit cases); full project suite 20/20 PASS.
- **F05 (Minor, fixed):** design/registry status headers updated to the
  ratified G0 state.
- **F02 (Major, fix rejected):** changing the frozen G0 selection statistic
  post-hoc would itself be a governance violation; the proxy-alignment risk
  is recorded as a standing disclosure in scope.md and carries into
  Tracks B/C.

Re-review of the amended `scope.md`, `code/run_experiment.py`, and
`python/src/xen/avwap.py` against the same constraint set: all checks PASS.

```text
VERDICT: APPROVE (re-affirmed post-F01–F05)
```
