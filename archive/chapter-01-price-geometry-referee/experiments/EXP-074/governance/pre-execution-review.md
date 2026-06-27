# EXP-074 — Pre-Execution Governance Review (re-issued for the 99-cell substrate scope)

**Date:** 2026-06-19
**Reviewer:** research-pipeline (consolidated Stage 4)
**Supersedes:** the prior APPROVE issued against the 6-cell (GBPUSD-5m + 5 disclosed) scope, and
the interim 99-cell *pooled* substrate verdict — both void. After an operator review of the first
run found the single pooled verdict masked strong domain structure (15m–1h separable; 5m noise;
2h/4h underpowered), the verdict layer was re-cut to a **per-domain dual-metric** read (operator
direction 2026-06-19). This review re-adjudicates scope + plan + code as a set.
**Artifacts:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`,
`docs/experiments-docs/checkpoints/2026-06-18-016-harami-candidate-screening/D0-amendment-005-train-diagnostic-followup-exp-074.md`,
`.../D0-amendment-006-exp-074-substrate-wide-expansion.md`

## Checks

**Registry precondition (file-drawer control).**
- Family `CF-HA-HARAMI-001` is `REGISTERED / OPEN`. ✓
- `multiplicity-registry.md` HYP-027 / EXP-074 row updated to the **full 99-cell MA-substrate
  matrix** (was GBPUSD-5m + 5 disclosed); the widened surface (14 features × 3 framings × 99
  cells) and the substrate-wide file-drawer control (≥50%-of-powered-cells share + cross-cell
  median CI + 2 pre-registered leads) are recorded. ✓
- No TEST-stratum read planned, so no `test-read-ledger.md` tally is consumed; ledger
  unchanged. ✓

**Holdout & TEST fence.**
- `load_train_1m` slices `[0, train_cutoff)` only, per cell; the next-21% TEST stratum and the
  final-30% holdout are never sliced or materialized. ✓
- Forward resolution clips at the TRAIN edge (boundary entries censor) — no TEST/holdout row is
  reachable. ✓
- EURUSD cells are characterized like any other: the EURUSD instrument-wide TEST cap is a
  TEST-stratum constraint and does not restrict a TRAIN-only diagnostic with 0 TEST reads. ✓
- Phase 016 D0 addenda (amendment-005 **and** amendment-006) authorize this TRAIN-only diagnostic;
  **operator ratification of amendment-006 required to lift the manual execution gate** (recorded
  here as the binding condition). ✓ (drafted; ratify before run)

**Scope / criteria soundness.**
- Verdict object is **per domain** (binding) and attainable/pre-stated, dual-metric: (i) per-cell
  any-feature separability rate; (ii) per-feature single-lever breadth (point |effect| ≥ 0.15 ∧ 1σ CI
  material-side ∧ all-framing consistency) with within-domain median CI. Four-tier verdict
  (SEPARATOR_FOUND / SEPARABLE_NO_UNIFORM_LEVER / NO_SEPARATOR / INCONCLUSIVE_POWER < 5 powered cells
  per domain). The pooled-substrate verdict is retained **disclosed-only** and does not bind. No
  zero-baseline percentage comparison. ✓
- The dual-metric design directly addresses the masking defect: the per-cell rate answers "is the
  tail separable", the breadth answers "is there a uniform lever" — they route EXP-075 differently
  (band-restricted vs feature-blended vs close) and are reported per band, not pooled. ✓
- Denominators defined: per-domain powered-cell denominator (n_q05 ≥ 30), per-feature breadth share,
  per-cell separability rate, per-group n, coverage counts per feature, censored count. ✓
- No parameter tuned, no filter selected, no candidate slot consumed. The single design lever
  (an exhaustion cap) is explicitly deferred to EXP-075. ✓

**Code conventions.**
- Imports → path → constants → types → helpers → plotting → orchestration → `main`; `Agg`
  backend; lazy scan + projection; `tqdm` on the 99-cell loop; bounded `N_BOOT`; dirs created in
  orchestration; type hints + docstrings. ✓
- 99-cell list **derived** from the frozen `exp068.INSTRUMENTS × DOMAINS − EXCLUDED_CELLS` (17×6−3),
  not hand-listed or outcome-filtered. ✓
- Determinism: all bootstrap seeds are integer lists (`[BASE_SEED, …]`); the cross-cell median
  bootstrap is seeded by integer feature index — **no `hash()` on string labels** (no
  PYTHONHASHSEED dependence). ✓
- Real-price outcomes: `r_e` from the certified `signal_arm`; HA used only for harami detection.
  ✓
- Frozen-machinery reuse: only departure from EXP-071 is the TRAIN entry mask; feature/`r_e`
  alignment asserted via the certified `qual` mask + stable argsort, hard-fail check retained. ✓
- Plots reuse the in-memory computed tables / `events` dict — no data reload for plotting. ✓
- Numpy-only statistics (scipy absent) validated against known tie/closed-form cases in the
  6-cell predecessor; unchanged here; flagged for audit. ✓

**Noted (not blocking).** The per-cell `verdict.json` is **descriptive** and point-effect based
(its SEPARATOR_FOUND feeds the per-domain *any-feature separability rate*); the **single-lever
breadth** independently adds the 1σ-CI gate. This is intentional — the two metrics answer different
questions. The auditor should confirm `domain_verdict.json` applies all three cell-candidacy
conditions (consistency ∧ point ≥ bar ∧ CI material-side) for the breadth metric, and that the
shared `_is_cell_candidate` / `_feature_breadth` helpers are used by both the per-domain and the
disclosed pooled paths (no divergent logic).

## Verdict

```text
VERDICT: APPROVE
```

Condition: operator ratifies **D0-amendment-006** (TRAIN-only diagnostic, substrate-wide, no TEST
contact) before execution. All other gates pass.
