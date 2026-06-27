# EXP-031 Pre-Execution Governance Review

**Experiment:** EXP-031 — AVWAP Edge Isolation (Entry-Timing vs Exit-Rule)
**Stage:** 4 (pre-execution)
**Date:** 2026-06-10
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py` (+ frozen
`code/event_method.py`)
**Governing checkpoint:** `docs/experiments-docs/checkpoints/2026-06-09-007-avwap-tradability-and-isolation/design.md`

## VERDICT: APPROVE

All governance constraints pass. No Critical or Warning issues. Two Info notes are
recorded for the Stage 5 audit. The implementation is approved for the manual execution
gate.

---

## Phase Alignment (checkpoint design.md)

- **In scope and correctly framed.** EXP-031 is the design §2/§5 edge-isolation experiment:
  it decomposes the EXP-028 measured per-event excess into entry-timing vs exit-rule
  contributions. Gross mechanism decomposition; costs/slippage are explicitly **out of
  scope** (EXP-030's separate question) — matches design §4/§7.
- **Dependency structure (LOCKED, design §3) respected.** EXP-031 runs **regardless** of
  EXP-030. EXP-030 completed 2026-06-10 as **INCONCLUSIVE** (5m/1h net EVIDENCE_AGAINST,
  4h INCONCLUSIVE_SPANS_ZERO); per the locked rule this does **not** cancel or gate
  EXP-031. No phase misalignment.
- **Multiplicity/registry gate satisfied.** Registered as `CF-AVWAP-001/DIAG-003`,
  **0 candidate-screening slots**, status SCOPED, in the Phase 007 batch of
  `docs/signal-registry/multiplicity-registry.md` (line 134) — legs and dominance
  thresholds predeclared, frozen EXP-027 inference, "no post-result leg reselection."
- **No holdout release, no tuning, no sweep** — design §7 honored. Horizons {1,6} frozen
  a priori; H=6 PRIMARY; dominance cut 0.67 predeclared.

---

## Scope (`scope.md`)

| Check | Result |
|-------|--------|
| Single falsifiable/exploratory question | PASS — one diagnostic decomposition; the falsifiable content is whether the split resolves (definite label vs INCONCLUSIVE/UNRESOLVED). |
| Predeclared, sign-complete criteria | PASS — the attribution rule covers every sign/significance combination (incl. negative-leg/>100% branches); 0.67 cut and H=6 primary fixed before results. |
| Boundaries explicit | PASS — instruments, domains, horizons, α, resamples, exclusions, primary domain (5m) all stated. |
| Holdout exclusion | PASS — final 30% never loaded/inspected; `start_idx+H` outside the slice is non-reportable, never extended into the holdout. |
| Real-price discipline | PASS — all returns are direction-signed log returns on **real domain Close**; synthetic chart prices prohibited in every role. |
| Zero-baseline handling | PASS — shares `s_entry/s_exit` defined only when X_full `CI_low>0` (significant nonzero total); no percentage-vs-zero metric. |
| Execution-path declaration (Phase 006 lesson 1) | PASS — scope explicitly states "Python re-analysis of the cTrader-confirmed upstream artifacts"; only added computation is a deterministic fixed-horizon recompute. |
| Complexity budget | PASS — 3 tests / 4 plots / 1 module. |

## Analysis Plan (`analysis-plan.md`)

| Check | Result |
|-------|--------|
| Method justification + simpler alternative | PASS — Wilcoxon, t-test, and plain i.i.d. bootstrap each considered and rejected with reasons; the frozen regime-cluster bootstrap + stratified paired sign-permutation reused unchanged. |
| Assumptions stated; no academic-finance pitfalls | PASS — no normality/stationarity/i.i.d.; regime-cluster exchangeability is the resampling unit; the X_exit equal-`dH` exchangeability null is explicitly stated as the leg's assumption (distribution-free permutation). |
| Cross-view alignment by timestamp | PASS — alignment via `start_idx` into timestamp-ordered rebuilt domains; rebuilt domain row counts hard-verified against EXP-020 `analysis_metadata.csv` before any `fh` compute. |
| Additivity rigor | PASS — the **common-control intersection** construction guarantees exact per-event `X_full* = X_entry + X_exit`; `N_full` vs `N_decomp(H)` reported separately (boundary attrition surfaced, not hidden). |
| Interpretation guide predeclared | PASS — classifier table + phase-outcome mapping fixed before results; H=1/H=6 disagreement is itself a reported finding. |
| Budget compliance | PASS — 3/4/1. |

## Code (`code/run_experiment.py`)

| Check | Result |
|-------|--------|
| Plan compliance | PASS — reconciliation anchor, common-control legs at H∈{1,6}, frozen inference, sign-complete classifier, 4 plots, 5 result CSVs + metadata; nothing beyond the plan. |
| Holdout exclusion | PASS — domains rebuilt via `xen.referee_calibration.load_analysis_data` (first-70% fence, EXP-020/022/024 convention); `fh` bounded by `start_idx+H ≤ n-1`; no `read_parquet`/full collect; no `.unique()` in loaders. |
| Look-ahead prevention | PASS — forward returns are outcomes; events/exits are the look-ahead-safe EXP-020/022 machinery (EXP-029-confirmed); horizons fixed a priori; base-bar `start_close` re-validated against rebuilt `log_close`. |
| Real-price outcome | PASS — `lifetime_bps` (EXP-022 real-Close BTC exit) and `fh_bps` (real-Close log return) only; no synthetic prices. |
| Timestamp alignment | PASS — `start_idx` into timestamp-ordered frames; metadata-validated; never bar-count across views. |
| Type safety / docstrings / sectioning | PASS — typed public functions, docstrings, VAL-style sections, functions within size norms. |
| NaN / edge cases | PASS — `fh` NaN past slice end; `powered` guards for `<DOMAIN_MIN_INSTRUMENTS`; `<MIN_CONTROLS` controls dropped; empty cells handled. |
| Separation of concerns | PASS — pure compute vs plotting vs orchestration; output dirs created only in orchestration; import side-effect-free. |
| No magic numbers | PASS — all thresholds are documented constants from the scope. |
| Performance / progress | PASS — vectorized NumPy gather + Polars group-by (no large row loops); `tqdm` on domain rebuild and horizon loops; concise `LOGGER` output. |
| Determinism | PASS — fixed `seed_for` seeds; frozen inference byte-hash-verified against EXP-027; additivity assertion `<1e-6`; X_full reconciliation hard gate (`X_FULL_RECONCILIATION_FAILED` aborts a mis-wired substrate). |
| Safe optimization | PASS — vectorization preserves sample membership, denominators, temporal ordering, and the paired-sign / cluster semantics of the frozen estimator. |

---

## Info notes (for the Stage 5 audit; non-blocking)

1. **Determinism replay.** Analysis-plan Step 5 specifies an in-process determinism
   replay; the code instead guarantees determinism via fixed `seed_for` seeds and leaves
   an independent bit-identical replay to the audit (the EXP-028/029 precedent). The
   Stage 5 audit **should** perform an independent replay and confirm bit-identical
   `decomposition_results.csv` and labels.
2. **X_full N reconciliation.** The reconciliation gate binds on the domain effect
   (abs OR rel tolerance) and reports `n_rebuilt` vs `n_exp028` without gating on exact
   counts. Because the population filter replicates EXP-028 `build_primary_excess`
   exactly, the audit should confirm `n_events`/`n_bull`/`n_bear` match EXP-028 as a
   substrate-integrity spot check.

---

## Routing

No REVISE/REJECT routing required. Proceed to the **manual execution gate**.

---

## Addendum (2026-06-10) — substrate-loading fix at the execution gate

The first manual run aborted in `validate_analysis_metadata` (all 12 cells), which is the
guard working as designed. Root cause: `data/timebars/` now contains both the original
full base files **and** new pre-sliced `timebars_analysis70_*` derivatives (the global
holdout has been physically removed from the directory). The raw `list_timebar_files`
glob matched all 8 files, and `load_analysis_data` re-sliced the already-70% `analysis70`
files to 70% again — a wrong, smaller window not matching EXP-020.

**Fix (no methodology/scope change):** pin the rebuild to the EXP-020 `source_file` set via
a new `expected_timebar_sources()` helper and filter `list_timebar_files` to those exact
filenames — the established **EXP-024 pattern**. This makes the code do what the approved
plan already required ("rebuild domains reproducing EXP-020 exactly; verify domain row
counts reproduce EXP-020 metadata"). Verified post-fix: all 12 cells reconcile against
EXP-020 (BTCUSD/5m = 216,982 domain bars, exact). The fix strengthens substrate/holdout
integrity (the `analysis70` derivatives are never double-sliced) and does not alter the
estimand, legs, inference, or classifier. Verdict **APPROVE** stands.
