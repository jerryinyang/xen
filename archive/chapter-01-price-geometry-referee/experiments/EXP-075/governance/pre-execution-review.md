# EXP-075 — Pre-Execution Governance Review (consolidated Stage 4)

**Date:** 2026-06-19
**Reviewer:** research-pipeline (consolidated Stage 4)
**Artifacts:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`,
`docs/experiments-docs/checkpoints/2026-06-18-016-harami-candidate-screening/D0-amendment-007-exp-075-train-design-followup.md` (revised).

## Checks

**Registry precondition (file-drawer control).**
- Family `CF-HA-HARAMI-001` is `REGISTERED / OPEN`. ✓
- `multiplicity-registry.md` HYP-028 / EXP-075 row is registered and **ACTIVATED** (the conditional
  row's substantive trigger — the q05-tail H1 finding — was met; `D0-amendment-007` revised to record
  that the formal `SEPARATOR_FOUND` verdict was **not** literally returned and that the proceed is on
  framing-resolved evidence with operator ratification). The countable surface (2 forms × 3
  percentiles × {M-GLOBAL, M-PERCELL}, band-core binding) is recorded. ✓
- No TEST-stratum read planned ⇒ no `test-read-ledger.md` tally consumed; ledger unchanged. ✓

**Holdout & TEST fence.**
- `load_train_1m` slices `[0, train_cutoff)` with `train_cutoff = int(int(total·0.7)·0.7)`, projection +
  sort before slice; the next-21% TEST stratum and final-30% holdout are never sliced or
  materialized. ✓
- The exhaustion cap is an entry-time boolean subset of already-resolved qualifying events — it only
  removes entries, never reaches forward, and never alters a retained event's resolution (causal). ✓
- Baseline `r_e` is reconciled to EXP-074 `events_<cell>.parquet` (`max|Δ| ≤ 1e-9`, hard-fail). ✓

**Scope / criteria soundness.**
- Single question (does a uniform exhaustion cap materially improve N-PARTIAL-V2A per band-core
  domain, and is it deployable vs overfit). Binding object = **per band-core domain** (15m/30m/1h);
  5m and band-pooled are disclosed-only. ✓
- Concrete, pre-registered decision thresholds, all pinned before code: retention ≥ 0.70 (and ≥ 30),
  uplift Δ ≥ +0.15, hurt Δ ≤ −0.10, overfit premium ≤ 0.20, powered = baseline q05 ≥ 30,
  INCONCLUSIVE_POWER < 2 domains with ≥ 5 powered. The only free parameter `U` is locked by a
  pre-registered mechanical rule (grid percentile maximizing improved band-core domains; ties →
  least restrictive). M-PERCELL is diagnostic-only, never deployed/frozen. ✓
- No zero-baseline percentage comparison (all endpoints are absolute shares/deltas and bootstrap CI
  legs). Denominators defined and pinned pre-cap (no membership drift). ✓
- No candidate slot consumed; the locked filter is **non-confirmatory** until a separate one-shot
  sealed-holdout experiment. ✓

**EXP-074 lessons implemented (binding).**
- **Lesson 1 (no pooling):** binding aggregation is strictly per band-core domain; band-pooled and 5m
  are written to separate disclosed-only fields; the M-GLOBAL-vs-per-domain masking risk is addressed
  by reporting the single global cap's effect per domain (hurt-check catches a global cap that helps
  one domain while breaking another). ✓
- **Lesson 2 (no rigid gate):** no separation/framing-consistency gate is re-run; the endpoint is the
  strategy's own legs via the **joint** four-leg criterion (the economically correct instrument for the
  exhaustion bimodality); the q05 finding is design rationale only. ✓

**Code conventions.**
- Imports → path → constants → types → I/O → pure compute → plotting → orchestration → `main`; `Agg`;
  lazy scan + projection + sort before slice; dirs created in `run()` (not import); `tqdm` on both
  passes; concise logging. ✓
- Determinism: integer-list seeds `[BASE_SEED, cell_index, sel, form_idx, thr_idx, purpose]` for
  signal bootstraps and a derived integer null-key for the matched-random draws — **no `hash()`** on
  labels. ✓
- Frozen-machinery reuse: resolution, returns, matched-random, and bootstrap are all imported from
  EXP-068 (no reimplementation); the cap is the only added entry-mask; `strong_stat_thr` is the
  small causal p75 helper copied from EXP-074. Real-price `r_e`; HA only for harami detection. ✓
- Bounded memory: resolutions are discarded per cell; pass B re-resolves the band-core + 5m cells it
  needs (the bootstrap dominates runtime, not the resolve) — no large multi-cell context cache. ✓
- Matched-random null re-drawn at the retained count per (cell, form, threshold); below-floor legs →
  NaN (cell cannot be "improved"); retention denominator guarded for zero; cap drops NaN features. ✓
- Plots reuse in-memory tables (no reload); bounded (numpy/aggregated). ✓
- Complexity budget: 3 stat families (block-bootstrap CIs, matched-random median contrast, descriptive
  per-domain share/Δ), 6 plots, 1 module — within budget. ✓

**Noted (not blocking).** (i) The run is bootstrap-heavy (~5,500 block-bootstraps incl. matched-random
re-draws) — expect a longish manual run; this is inherent to the per-threshold matched-null design and
is bounded/`tqdm`-tracked. (ii) Pass B re-resolves cells deterministically and does not re-assert the
EXP-074 reconciliation (asserted once in pass A on the identical `resolve_cell`); the auditor should
confirm the derived null-key is collision-free and that pass A/B resolutions are identical.

## Verdict

```text
VERDICT: APPROVE
```

Condition (already satisfied): operator ratification of the revised `D0-amendment-007` — recorded via
the operator's direction to proceed through EXP-075's pre-execution stages, made with the
"formal SEPARATOR_FOUND not met" conflict in full view. All other gates pass.
