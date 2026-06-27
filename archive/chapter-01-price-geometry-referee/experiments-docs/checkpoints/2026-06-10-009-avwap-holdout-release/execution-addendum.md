# Phase 009 Execution Addendum — EXP-032 Hard-Stop Taxonomy and Two-Invocation Protocol

**Status:** Adopted 2026-06-10, pre-execution (before any EXP-032 code run,
including Phase H1), via the Stage-4 REVISE route the design §10 provides.
**Source:** external pre-execution review of EXP-032 (findings F01–F05).
**Frozen-parameter impact:** NONE. This addendum classifies process failures and
fixes execution mechanics; no cost, financing, horizon, policy, population,
inference, or margin parameter is touched. The design §3 single-shot rules are
unchanged and remain binding.

## 1. Governing principle

**Guard failures before Phase H2 never spend the shot.** The shot is spent if and
only if a holdout outcome quantity has been computed (Phase H2 entered the outcome
computation). Everything earlier — loader checks, prefix equality, lineage
reconciliation, calibration, the freeze itself — is machinery that may hard-stop
and be repaired without contacting any holdout outcome. A defect discovered AFTER
H2 remains, as the design states, a disclosed defect in a spent shot.

## 2. Hard-stop classification (predeclared consequences)

| Class | Signature | Classification | Consequence |
| --- | --- | --- | --- |
| (a) True lineage mismatch | Reconciliation guard 1b fails on EVENT KEYS or strata: regenerated analysis-stratum triggers/regime ids/directions differ from the EXP-022/EXP-037 record, or the 27/12 partition under the EXP-037 boundary does not reproduce | Generator-lineage defect — the holdout events would not come from the population G2 certified | **Blocked.** Investigate on analysis data only. The holdout read must not proceed until the lineage question is resolved in a separate, analysis-set-only scope. Shot NOT spent. |
| (b) Reportability-flag-only drift | Guard 1b fails ONLY on `reportable_event` flags / `n_controls` for late analysis events in boundary-spanning regimes, with all event keys, triggers, and strata identical | Known, benign mechanism — control candidacy in `(confirm_idx, end_idx]` is an ex-post population rule; a boundary-spanning regime gains candidates (extended `end_idx`) and loses candidates (holdout triggers' exclusion windows). This is a defect in the reconciliation EXPECTATION, not in the generator lineage | **Repairable** via the Stage-4 REVISE route (design §10): amend the reconciliation expectation to compare flags only for events whose regime closes at or before the boundary, disclose the boundary-spanning exceptions, and re-gate. No frozen parameter changes. Shot NOT spent (no outcome was contacted). |
| (c) Environment-drift hash mismatch | R1.6 manifest recovery fails with the `environment` field (python/numpy/polars versions, recorded in the manifest) among the differing fields, or calibration floats drift after a library upgrade | Reproducibility-infrastructure failure, not a research event | **Rebuild the recorded environment** from the versions in the frozen manifest and rerun. NEVER regenerate or overwrite the manifest. Shot NOT spent. |

Any hard stop not matching these signatures is treated as class (a) until shown
otherwise: blocked, investigated on analysis data only, shot not spent.

## 3. Two-invocation execution protocol (F03)

- EXP-032 runs as two separate process invocations: `--phase h1` (guards, stratum
  manifest, null calibration, freeze; **no holdout outcome contact**) and
  `--phase h2` (the irreversible read). The H2 invocation re-runs the
  deterministic H1 pipeline and must reproduce the frozen manifest's content hash
  exactly (R1.6) — making the freeze barrier a genuine cross-process check rather
  than an in-memory formality.
- Between invocations a MECHANICAL verification runs (and is also re-run at the
  start of `--phase h2`): manifest parses and hash-verifies; calibration record
  is well-formed and finite; stratum manifest is non-empty. The predeclared
  15–18 holdout-count expectation is a logged disclosure only.
- **No selection lever:** H2 WILL be run regardless of how the H1 entry
  attributes look (count, regime composition, margin size). The inter-phase
  check may halt only for defects in machinery, never for unattractive
  attributes. Declining to run H2 after a clean H1 is not an available action
  for the operator under this protocol.

## 4. Persistence and post-verdict access (F01)

- Phase H2 persists, in order: `holdout_events.csv` (per-event keys, `fh_12`,
  `net_12`, truncation flag, financing days/bps, BTC-exit companion columns),
  then `run_metadata.json`, then `holdout_verdict.csv` — the verdict file last,
  so the no-second-read guard marks a FULLY persisted read. A crash before the
  verdict write leaves a deterministic, resumable rerun (same frozen manifest,
  same seeds); a crash after it loses nothing mandated.
- H1 persists `analysis_fh_nets.csv` (per-event disclosed-data nets for the 39
  analysis events).
- **Post-verdict rendering, audit, interpretation, and documentation read ONLY
  the persisted artifacts** (`holdout_events.csv`, `analysis_fh_nets.csv`,
  `holdout_verdict.csv`, `run_metadata.json`, `frozen_holdout_manifest.json`).
  Reading these files is not a second holdout read. Recomputing any quantity
  from holdout 1-minute or 4h rows after the verdict exists is prohibited —
  including by the Stage-5 auditor, whose numerical validation operates on the
  persisted per-event table and the analysis-set reproduction anchors.

## 5. Estimand identifiability disclosure (F04)

The binding population rule (`reportable_event`: >= 3 same-regime matched
controls) is a deterministic EX-POST rule, frozen since EXP-022 — control
candidacy depends on how the regime evolves after entry and on the series
truncation point. It is NOT identifiable at entry time by a live trader. This is
unchanged from what G2 certified (the rule is lineage-frozen), but every
EXP-032 results/report artifact MUST carry: (i) the pre- vs post-reportability
holdout event counts (H1 `counts`), and (ii) the external-validity caveat that a
HOLDOUT_CONFIRMED estimand conditions on ex-post reportability, so any
tradability claim inherits that conditioning.

## 6. Calibration-fidelity caveat (F05)

The margin calibration takes the cluster LAYOUT from the real holdout stratum but
transports the variance SCALE from the disclosed analysis era (the standing R1.2
assumption, correctly frozen). If plot 3 shows holdout per-event dispersion far
above the analysis era's, the calibration-fidelity caveat must accompany a
CONFIRMED verdict in results.md and report.md.
