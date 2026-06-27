# EXP-022 — Pre-Execution Governance Review

**Stage:** 4 (pre-execution)
**Date:** 2026-06-08
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`
**References:** governance-constraints.md, code-conventions.md, checkpoint
`2026-06-07-004-avwap-signal-exploration/design.md`

```text
VERDICT: APPROVE
```

## Critical pass revision note

A fresh pre-run audit found one scoped-output mismatch: `control_lifetime_diagnostics.csv`
was required to carry volatility-context ratio diagnostics, but the first
implementation only emitted separate event/control local-volatility medians.
`code/run_experiment.py` now emits `median_vol_context_ratio`,
`p25_vol_context_ratio`, `p75_vol_context_ratio`, and `n_vol_context_pairs` in
that diagnostic table. This does not change sample membership, primary
statistics, inference, or decision logic; it makes the scoped diagnostic output
auditable.

## Checkpoint alignment

EXP-022 is the planned **AVWAP Original Lifetime Move Study** in the Phase 004
experiment chain (design §5), gated on EXP-020 `SUPPORTED_FULL`. The EXP-020
substrate metadata confirms the gate (`overall_status=SUPPORTED_FULL`,
`ready_domains=[5m,1h,4h]`, `invariant_failure_count=0`, `determinism_pass=true`),
and the code re-asserts it (`check_dependency_gate` + `check_dependency_artifacts`)
before loading any substrate table, blocking with `EVIDENCE_AGAINST` otherwise.
The design's benchmark requirement (§7: a favorable lifetime result must be
measured against a look-ahead-safe benchmark) is satisfied by the matched
same-regime non-event control. No phase misalignment.

## Core constraints

- **Holdout (§5):** `load_analysis_data` slices the first 70% in a lazy plan
  before collection; `validate_event_join`/`validate_regime_join` hard-fail if any
  `trigger_idx`/regime index reaches `>= n` (holdout-fence breach); every
  completion scan is bounded by `analysis_end_idx = n-1`. No holdout path.
- **Look-ahead (§6):** targets are frozen at event/control start; trend-change is
  the nearest *later* opposite-direction MA(20,50) regime confirmation (a real
  confirmation bar); `frame_localvol_bps` uses only returns ending at the
  reference bar; control selection uses no future outcomes. The vectorized
  first-hit (`np.argmax` over the post-start segment) preserves first-completed-
  close-by-time ordering — explicitly permitted by the plan and not an
  order-changing shortcut.
- **Real-price discipline (§7):** all outcomes use real domain `Close`
  (log-return bps). No synthetic chart prices; not a chart-type experiment.
- **Timestamp alignment (§4/§6):** the cross-substrate join (EXP-020 events →
  reconstructed first-70% domain bars) is validated by `CloseTime` **and** `Close`
  (not bar count). Bar indices are used only *within a single domain frame* for
  the lifetime scan — the same approved pattern as EXP-021.
- **Non-parametric inference (§2):** regime-cluster bootstrap + stratified paired
  permutation + Holm; clusters are exact (same-regime controls). No
  normality/stationarity/i.i.d. assumptions.
- **Zero-baseline (§4):** rate differences are reported in percentage points and
  expectancy in bps (absolute) — no percentage-improvement-vs-zero, per scope.
- **Safe optimization (§8):** lazy scans/column-bounded reconstruction reused from
  `referee_calibration`; bootstrap/permutation chunked; plot inputs derived from
  in-memory records (no full-frame pandas conversion); `tqdm` over file rebuild,
  cells, and domain inference. The per-event scan is genuinely sequential,
  bounded, and look-ahead-safe.

## Code-convention checks

Organization/sectioning (VAL-001 separators), import-side-effect freedom
(directories created only in `run()` — verified by import smoke), type hints,
explicit NaN/zero-denominator handling (`np.divide` with `where`, `nanmean`, null
rates on empty denominators), deterministic seeds (`seed_for`), and concise
logging all conform. Verification after the critical pass:

- `uv run ruff check ../python/experiments/EXP-022/code/run_experiment.py` passes;
- `uv run python -m py_compile ../python/experiments/EXP-022/code/run_experiment.py`
  passes;
- import smoke passes and creates no `results/` or `plots/` directories;
- targeted helper checks for matched-set volatility-context ratio diagnostics pass.

## Complexity budget

- Statistical tests: 3/3 (favorable-rate regime-cluster bootstrap CI; paired
  permutation + Holm; expectancy-consistency bootstrap CI).
- Visualisations: 5/5 (outcome composition, favorable-rate forest, expectancy
  forest, bars-to-completion, direction×pyramid heatmap).
- New modules: 0 (all experiment-local in `run_experiment.py`; within the
  "≤1 helper module if needed" allowance).

No scope creep: the code produces exactly the scoped output set and no bonus
analyses.

## Info notes for Stage 5 audit (non-blocking, documented in `run_metadata.method_notes`)

These are faithful operationalizations of the plan's higher-level descriptions
and warrant audit confirmation against results, but violate no constraint:

1. **Paired permutation** is implemented as the rate analog of EXP-021's paired
   sign flip: within each matched set the single event slot is reassigned
   uniformly among that set's *completed* moves, preserving the observed event
   and control target-completion denominators exactly and remaining stratified
   (reassignment never crosses matched sets / instrument / direction).
2. **Expectancy-consistency** uses *target-completion* (favorable+adverse)
   lifetime expectancy for the FOR/AGAINST point-estimate check, aligned with the
   favorable-rate denominator; trend-change expectancy is reported separately and
   excluded from the decision.
3. **Trend-change boundary** = nearest later opposite-direction regime confirm bar
   from the state summary; shared by an event and its same-regime controls.
4. **Control lifetime eligibility** requires ≥1 future bar (vs EXP-021's fixed
   horizon feasibility); short windows resolve symmetrically as
   trend-change/unfinished and drop out of the target-completion denominator.
5. **Volatility-context ratio** is per matched set (control-mean local-vol /
   event local-vol), median across sets, feeding the predeclared
   `[0.5, 2.0]` confound downgrade.

## Decision

All governance and code-convention checks pass with no Critical or Warning
issues. Implementation matches the approved scope and analysis plan and respects
the holdout, look-ahead, real-price, and complexity-budget constraints.
**APPROVE** — proceed to the manual execution gate. No EXP-022 result files were
created during this review.
