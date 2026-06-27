# EXP-032 Pre-Execution Governance Review

**Date:** 2026-06-10
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`
**References applied:** research-pipeline governance constraints, developer code
conventions, Phase 009 checkpoint `design.md`
(`docs/experiments-docs/checkpoints/2026-06-10-009-avwap-holdout-release/`).

This is the final gate before the manual execution handoff for the programme's
one-shot holdout read (Phase 009 design §10: REVISE findings must be resolved
before any code run, including Phase H1).

## Scope and phase alignment

- Single falsifiable question (Package-B net per-event expectancy on the holdout
  stratum); locked one-shot discipline, frozen parameters, predeclared mechanical
  verdict rule, honest power statement. Matches Phase 009 design §1–§8 verbatim.
- The standard holdout rule is superseded for EURUSD only, within this scope only,
  by the Phase 009 design (the sanctioned release the rule reserves for). The
  scope correctly keeps BTCUSD/USTEC/XAUUSD sealed and bans any EURUSD holdout use
  beyond the §4/§6 estimand.
- Zero-baseline rule respected: absolute bps vs 0, no percentage-of-baseline
  metric. Event-level denominators defined (reportable events, all_legs; counts
  pre/post reportability disclosed).
- Complexity budget: 1 test family / 3 plots / 1 new module — realistic and
  matched by plan and code.

## Analysis plan

- Every step carries "why this method" and "simpler alternative considered";
  frozen EXP-027 regime-cluster bootstrap (non-parametric, dependence-aware);
  Wilcoxon/t-interval correctly rejected. R1.2-analog null calibration justified
  (frozen bootstrap never Type-I-calibrated at a ~15-event single cell) with
  predeclared margin rule. Interpretation guide is fully predeclared with no
  amendment path. Family of 1 — no Holm needed; correct.
- Dispersion-from-39-disclosed-events choice is predeclared and sound (TRAIN/TEST
  separation has no force once both are disclosed and the evaluation stratum is
  the holdout).

## Code review (`code/run_experiment.py`)

Verified against the code-conventions checklist and the plan's Implementation
Safety Constraints:

- **Plan compliance:** Steps 1–6 map one-to-one (guards -> H1 manifest ->
  calibration -> freeze barrier -> one-shot H2 -> companions). Expected artifacts
  exactly as planned: `reconciliation.csv`, `holdout_stratum.csv`,
  `null_calibration.csv`, `frozen_holdout_manifest.json`, `holdout_verdict.csv`,
  `run_metadata.json`, 3 plots. No bonus analyses.
- **Structural H1/H2 separation:** `run_h1` computes entry attributes only for
  holdout rows; the only price-difference quantities it computes are the
  disclosed-data analysis nets on the ANALYSIS-ONLY 4h series (guard 1c /
  calibration dispersion). Outcome helpers (`add_fh_net_columns` on full-series
  arrays, `scan_lifetime`, `attach_btc_net`) are reachable only from `run_h2`.
  `run_h2` re-reads the manifest from disk, hash-verifies it, reads
  margin/policy/constants only from it, and key-matches live rows against the
  frozen stratum manifest (hard stop on divergence).
- **No-second-read / R1.6 recovery:** `run_h2` refuses to run when
  `holdout_verdict.csv` exists; an existing manifest must content-hash-match the
  recomputed record (hard stop on mismatch). Both verified present at
  `run_h2()` entry and `freeze_holdout_manifest()`.
- **Integrity guards:** EXP-037 `frozen_selection.json` content-hash pin
  (verified executable against the on-disk artifact: hash
  `2bbbf65b…770b0fea` matches, H*=12/all_legs, 27/12 EURUSD manifest extracted);
  frozen-tail pin `e50873d12a9f68d9` (verified executable); EXP-022 key+flag and
  EXP-037 key/partition reconciliation; TEST reproduction anchor at ≤ 0.01 bps;
  loader-equivalence and 4h prefix-equality asserts; seal registry asserting
  exactly one (EURUSD) data file opened, with row-range disclosure.
- **Reuse verbatim:** generator `xen.avwap` (frozen parameters); EXP-022 control
  selection/lifetime scan and EXP-037 FH/net/inference/variance-components loaded
  by module path and called directly — no reimplementation. Frozen constants
  cross-asserted against the EXP-037 module at startup.
- **Temporal discipline:** boundary and stratum membership keyed on trigger close
  TIME (ties -> analysis); the only bar-index arithmetic is `start_idx + 12`
  within the single 4h view (EXP-033-identical, scope-sanctioned). Sequential
  stateful generator kept sequential; truncation at the true series end disclosed
  as column + share.
- **Conventions:** no import-time side effects (verified by import test: no
  directories created, no data loaded); lazy column-projected scan with sort
  before slice; `tqdm` on the R=2000 calibration loop; concise orchestration
  logging; bounded plot inputs (≤ ~57 points, no pandas conversion, no reload);
  fixed namespaced seeds ("EXP-032"/"nullcal", "EXP-032"/"holdout"); same-seed
  determinism replay with 1e-12 tolerance; financing via the shared
  `xen.financing` helper with self-check, fractional calendar days, and a
  weekend-spanning spot-check recorded in run metadata; NaN/empty handling
  explicit (empty holdout stratum, unfinished BTC-exit lifetimes disclosed and
  excluded from the companion point estimate only).

## Info notes (non-blocking)

1. The EURUSD parquet is opened twice (full sorted scan + the canonical
   `load_analysis_data` prefix path) — same single file; this powers the
   loader-equivalence assert that pins the prefix to the EXP-020/037 lineage and
   is disclosed in the seal registry.
2. A few orchestration functions exceed the ~30-line guideline (`run_h1`,
   `run_h2`, `freeze_holdout_manifest`) — consistent with the EXP-037 precedent
   for guard-dense orchestration; helpers remain small and pure.
3. The lineage reconciliation may legitimately hard-stop at runtime if
   boundary-spanning regimes change control counts for late analysis events;
   that is the designed honest outcome (generator lineage proof), not a code
   defect — and it stops the run BEFORE the manifest freeze and any outcome
   contact.

```text
VERDICT: APPROVE
```

---

# Revision 1 — Re-gate after external pre-execution review (2026-06-10)

An external review delivered findings F01 (Critical) and F02–F04 (Major), F05
(Minor), all pre-execution-fixable without touching any frozen parameter. The
initial APPROVE is superseded; this revision re-reviews the amended artifacts.
Phase 009 design §10 requires REVISE findings resolved before any code run,
including Phase H1 — confirmed: no code has been run.

## Findings and resolutions

| Finding | Resolution | Artifact |
| --- | --- | --- |
| F01 (Critical): per-event holdout outcomes never persisted; post-verdict crash loses mandated disclosures; Stage-5 audit has no protocol-compliant data path | H2 now assembles EVERY disclosure in memory, then writes `holdout_events.csv` (per-event keys, fh_12, net_12, truncation flag, financing days/bps, BTC companion columns) → `run_metadata.json` → `holdout_verdict.csv` LAST (completion marker: a crash before it is a deterministic resumable rerun; after it, nothing mandated is lost). H1 persists `analysis_fh_nets.csv`. Plots render from persisted artifacts only; the plan and addendum predeclare that post-verdict rendering/audit read only persisted artifacts (not a second read) and prohibit holdout-row recomputation | `code/run_experiment.py` (run_h2, run_h1, main), `analysis-plan.md` Step 5, addendum §4 |
| F02 (Major): benign hard-stops conflated with "lineage broken"; no predeclared consequence on a no-amendment shot | Phase 009 `execution-addendum.md` adopted pre-execution: class (a) key/strata mismatch → blocked, analysis-only investigation; class (b) reportability-flag-only drift on boundary-spanning regimes → repairable reconciliation-expectation defect via Stage-4 REVISE; class (c) environment-drift hash mismatch → rebuild recorded environment, never regenerate the manifest. Governing principle: guard failures before H2 never spend the shot. Code support: manifest now records python/numpy/polars versions and reports differing top-level fields on R1.6 mismatch | `docs/experiments-docs/checkpoints/2026-06-10-009-avwap-holdout-release/execution-addendum.md`; `code/run_experiment.py` (freeze_holdout_manifest) |
| F03 (Major): single-process H1→H2 removes the verification point between freeze and spend; in-process manifest check near-circular | Execution split into `--phase h1` / `--phase h2` invocations; the H2 invocation re-runs the deterministic H1 pipeline and must reproduce the frozen manifest hash exactly (R1.6) — a genuine cross-process barrier. Mechanical `verify_h1_artifacts` runs between phases (hash, finite well-formed calibration, non-empty stratum); the 15–18 count expectation is disclosure-only. Predeclared: H2 runs regardless of entry attributes; the check may halt only for machinery defects (no discretionary selection lever) | `code/run_experiment.py` (parse_args, verify_h1_artifacts, main), `analysis-plan.md` safety constraints, addendum §3 |
| F04 (Major): "entry attributes are causal" is false for control counts; binding population not identifiable at entry | Plan Step 2 assumption corrected (control counts are a deterministic EX-POST rule frozen since EXP-022; "entry attributes" = outcome-free, not entry-knowable); Data Wiring wording corrected; mandatory disclosure predeclared for results.md/report.md (pre/post-reportability counts + external-validity caveat on any tradability claim). No population-rule change — the rule remains lineage-frozen, exactly what G2 certified | `analysis-plan.md` (Data Wiring, Step 2, Interpretation Guide), addendum §5 |
| F05 (Minor): margin transports analysis-era dispersion onto a possibly regime-shifted holdout | No method change (correctly frozen). Predeclared: if plot 3 shows holdout dispersion materially above the analysis era's, the calibration-fidelity caveat must accompany a CONFIRMED verdict | `analysis-plan.md` Interpretation Guide, addendum §6 |

## Re-verification

- All frozen parameters unchanged (H*=12, all_legs, RT 3.0 bps, 0.6 bps/day,
  tail hash `e50873d12a9f68d9`, selection hash `2bbbf65b…770b0fea`, N_BOOT 1000,
  R 2000, margin rule, verdict rule, boundary convention). Diffed against the
  pre-revision constants block — identical.
- Estimand-neutrality: the new artifacts (`holdout_events.csv`,
  `analysis_fh_nets.csv`) are disclosures of quantities the plan already
  computed; the two-invocation split changes process structure only (the H2
  invocation's regenerated population must hash-match the frozen manifest, so no
  re-selection is possible).
- Code re-verified: compiles; imports with zero side effects; frozen pins
  resolve; `verify_h1_artifacts` hash/calibration guards fire correctly on
  synthetic defects and pass on a well-formed record; argparse restricts to
  `h1`/`h2`; weekend day-of-week arithmetic validated against a known
  Thursday→Monday window.
- Complexity budget unchanged: 1 test family / 3 plots / 1 module.

## Notes carried forward to Stage 5/6/7

The auditor must validate the binding verdict from `holdout_events.csv` and the
analysis-set anchors — never by recomputing from holdout rows. The interpreter
and documenter must include the F04 identifiability disclosure and, if
triggered, the F05 calibration-fidelity caveat.

```text
VERDICT: APPROVE
```
