# Phase 003 Design Amendment A1 — Incremental-Unit Methodology Corrections

**Amendment ID:** 2026-06-04-A1
**Authored:** 2026-06-04
**Re-validation completed:** 2026-06-05 (EXP-013/014 re-run 2026-06-04, EXP-015 re-run 2026-06-05)
**Phase:** 003 — Ratification & Incremental-Information Unit
**Status:** APPLIED — Track B re-validation complete (EXP-013 → EXP-014 → EXP-015 re-run; all expectations confirmed). `retrospective.md` pending.
**Trigger:** Adversarial review of EXP-012…016 (findings F01–F07). This amendment records
the corrections that change governed Track B code, so the predeclaration freeze is
preserved by documenting the change *before its dependent results are re-read*.

---

## 1. Scope and posture of this amendment

This amendment is a **correctness/methodology correction**, not a re-selection of any
predeclared object. Specifically:

- The **primary estimator is unchanged** (D-incr-form): incremental edge is still the
  model-free marginal net P&L of adding C to a book holding R, combined additively and
  clipped, with cost charged on incremental turnover. No linear/i.i.d./stationarity
  model is introduced.
- The **operating point (D-ratify-point), substrate construction (D-incr-substrate), and
  the gate-leg *mapping* (D-incr-legs) are unchanged** in intent.
- What changes: (a) how the inference layer estimates the bootstrap **block length**;
  (b) how the EXP-013 redundancy-null **verdict is aggregated**; (c) the **diagnostics
  retained** by EXP-015; and (d) the **first-principles documentation** of the leg
  semantics. None of these alters which edge/τ/estimator was predeclared.

Because items (a)–(c) change frozen Track B machinery (`xen/incremental_referee.py`) and
two Track B experiment scripts, per **D-reuse** ("any change to … the frozen harness
triggers re-validation (P0) before dependent experiments") the Track B re-validation
chain **EXP-013 → EXP-014 → EXP-015** must be re-run before any Track B result is relied
upon. See §6.

---

## 2. F04 — Block length must be estimated on the contiguous marginal series

**Defect.** `incremental_edge_ci` and `incremental_gate_core` estimated the stationary
block length on the **gap-extracted denominator series** (`net_full[denom_mask]`). Gap
extraction discards the time gaps between C-active episodes, so `estimate_block_length`
saw no cross-episode autocorrelation and collapsed to `block_length = 1` in every cell
(confirmed: EXP-013 `redundancy_null.csv` reported `block_length = 1` for all 12 cells).
The point estimator stayed model-free, but the **significance machinery (L2/L3 CI-lower
legs) became an effectively i.i.d. bootstrap**, ignoring within-episode autocorrelation —
in tension with governance §2 ("no i.i.d. assumption") for a unit intended to be frozen
and applied to autocorrelated real candidates in Phase 004.

**Correction.** Block length is now estimated on the **contiguous, full-length
`net_full` marginal series** (zeros off the denominator preserve the real time axis), via
the new `_contiguous_block_length` helper. `marginal_net_series` now returns `net_full`;
`incremental_edge_ci` accepts a `block_series=` argument; `incremental_gate_core` uses it.

**Validated behaviour** (synthetic + EXP-014 rerun):

| Candidate structure | Old (gappy) block | New (contiguous) block | Effect |
| --- | --- | --- | --- |
| Episode-coherent, 5m (ep 24) | 1 | ~13 | CIs ~3.6× wider; `effective_n` 3600 → 277 (still ≥ 120 floor) |
| Episode-coherent, 1h/4h | 1 | ~4 / ~3 | CIs widen at episode scale |
| Per-row signal (EXP-015 construction) | 1 | 1 | unchanged (genuinely near-i.i.d.) |
| Noise-dominated fixtures (EXP-014 l3/l5/redundant) | 1 | 1 | unchanged |

The block length is therefore **adaptive and principled**: it recovers the episode as the
independent unit for coherent candidates and stays at 1 for genuinely per-row signals.
**EXP-014 re-ran with 7/7 verdicts and 35/35 leg states reproduced**, so the deterministic
correctness gate is unaffected. The change is directionally conservative (wider CIs make
passing harder), so it cannot turn a refutation into a false validation.

---

## 3. F01 — Redundancy-null verdict must use the across-draw distribution

**Defect.** The EXP-013 redundancy null is the **binding Track B control**, yet its
verdict was driven by a **single canonical draw's** block-bootstrap CI. In cost-dominated
/ low-N cells (4h and BTCUSD/1h) that single-draw CI is far too wide to detect a
materiality-sized phantom (e.g. 4h CIs spanned ±10–14 bps against a 3.0 bps materiality),
so those cells "passed" the binding control only because the test had **no power**; four
of five `NULL_COST_DOMINATED` cells even had positive single-draw point estimates from
one-draw noise, opposite the expected negative cost drag.

**Correction.** The verdict now uses the **across-draw distribution** of the per-draw
incremental reading (`REDUNDANCY_DRAWS` draws) — the actual sampling distribution of the
estimator under the redundancy construction — with an explicit power gate:

- `PHANTOM_EDGE` — across-draw CI entirely positive **and** point breaches the null
  tolerance (a real shared-structure false edge; binding failure).
- `UNDER_POWERED` — across-draw CI half-width ≥ materiality, so the test cannot rule out a
  materiality-sized phantom. **Reported as such, never counted as a clean pass.**
- `PASS` — point within tolerance, CI lower ≤ 0, and CI tight enough to have detected a
  phantom (clean zero).
- `NULL_COST_DOMINATED` — a *powered* negative cost-drag reading beyond the tight band
  with no phantom positive (expected, not a failure).

The single-draw block-bootstrap CI (now with the F04 block length) is retained as a
**diagnostic only**. The overall substrate verdict additionally requires the binding
control to be **powered in at least one cell**; if every redundancy cell is under-powered
the substrate is `INCONCLUSIVE`, not `PASS`.

**Expected reclassification** (replayed on the recorded across-draw values, which F04 does
not change): **8 PASS, 3 UNDER_POWERED (BTCUSD/1h, BTCUSD/4h, USTEC/4h), 1
NULL_COST_DOMINATED, 0 PHANTOM** → substrate remains **PASS** (binding control powered in
9/12 cells, no phantom), but the three genuinely low-power cells are now honestly flagged
instead of silently passing.

**Confirmed on rerun (2026-06-04).** `redundancy_null.csv` returned exactly **8 PASS, 3
UNDER_POWERED (BTCUSD/1h, BTCUSD/4h, USTEC/4h), 1 NULL_COST_DOMINATED (XAUUSD/4h), 0
PHANTOM**; `run_metadata.json` records `overall_status: PASS`, `powered_null_cells: 9`,
`phantom_edge: false`, `redundancy_verdict_basis: across_draw_distribution`. The most
positive across-draw mean across all cells is `-0.041` bps, so no cell carries a positive
point estimate. The substrate stands **PASS**.

---

## 4. F03 — EXP-015 must retain per-leg and per-instrument diagnostics

**Defect.** EXP-015 discarded the per-leg states (`row.pop("leg_results")`) and pooled the
four instruments inside each dependence cell. The keystone **REFUTED** verdict was
therefore undiagnosable: the failing cells' TPR plateaus at exactly **0.75** across the two
largest edges (an edge-independent ceiling consistent with one of four pooled instruments,
or one alpha-independent leg, never clearing power), but the outputs could not distinguish a
genuine detectability limit from a single-instrument / leg-interaction artifact.

**Correction.** EXP-015 now retains the five leg states as boolean columns on each draw and
emits two diagnostic tables:

- `leg_pass_rates.csv` — per domain/grid cell/edge, the pass-rate of each leg among
  positive draws (identifies the binding leg behind a TPR plateau).
- `tpr_by_instrument.csv` — per domain/grid cell/instrument/edge TPR (exposes
  single-instrument power caps the pooled TPR hides).

These are **diagnostics**; the predeclared verdict rule (worst-case finite cell MDE; a
qualifying cell with no finite MDE refutes the domain) is **unchanged**, so the REFUTED
outcome is expected to stand. The diagnostics let the follow-up target the true cause.

**Confirmed on rerun (2026-06-05).** EXP-015 stands **REFUTED** in all three domains (5m 1
fail, 1h 2 fails, 4h 2 fails; FPR controlled, max `0.01`). The new diagnostics resolve the
plateau: in every failing cell the verdict pass rate equals the **L2 standalone-significance**
pass rate (5m/high `0.75`, 1h/mod `0.784`, 1h/high `0.716`, 4h/mod `0.63`, 4h/high `0.382`)
with L1/L4/L5 saturated at `1.0` and L3 ≥ `0.97`; `tpr_by_instrument.csv` shows the shortfall
is driven by **BTCUSD**, whose standalone TPR is `0.0`–`0.136` at the 32 bps ceiling while the
other instruments reach/approach `1.0`, holding the pooled per-cell TPR below the
`POWER_TARGET = 0.80` floor. The 0.75 plateau was therefore a single-instrument power cap, not
a four-way pooled ceiling — exactly the ambiguity F03 was added to resolve.

---

## 5. F02 — First-principles rationale for the incremental leg semantics

The incremental referee's legs are **deliberately less conservative** than the frozen
Phase 001 strict gate, and that reduced conservatism must be justified on first principles
rather than on EXP-014 fixture-reachability. The mapping below is the predeclared
**D-incr-legs** default; this amendment records *why* each departure is defensible and flags
the residual risk that must be resolved before any freeze.

| Leg | Frozen strict gate | Incremental gate | First-principles rationale | Residual risk |
| --- | --- | --- | --- | --- |
| L1 readiness | effective-n + up/down episodes on the candidate | same, on the **incremental** position | The claim is about the incremental position, so readiness must be measured there. | None material. |
| L2 significance | candidate net edge CI-lower > 0 | **standalone** C net edge CI-lower > 0 | Splitting L2 (standalone C is itself a signal) from L3 (C beats R) makes the two legs test genuinely different series, so a candidate that only *looks* good standalone but adds nothing beyond R is caught by L3, not hidden by a single conflated leg. | A candidate could pass L2 on standalone merit while L3 is the only real screen; acceptable because L3 is the binding incremental test. |
| L3 reference-control | naive-control CI-lower > 0 | **incremental-beyond-R** CI-lower > 0 | Direct generalization of "beats naive" to "beats the reference book" — the core portfolio-fitness claim. | None material; this is the intended generalization. |
| L4 cross-market | **both** train and OOS means > 0 | **no material sign reversal** across the two segments | A redundant candidate's near-zero cost-drag must not be forced to fail a "both positive" test (it has no edge to be positive about); only a *material* sign reversal indicates genuine cross-regime instability. | **Less conservative**: a candidate positive in train and ~0 in test passes L4 here but would fail the strict gate. Must be operator-accepted before freeze. |
| L5 materiality | CI-lower > materiality | **point estimate** > materiality | Makes L5 (economic magnitude) orthogonal to L3 (statistical significance), so the two test different dimensions. | **Less conservative**: a point > materiality with a CI-lower below it passes L5 here. The conjunction L3 ∧ L5 partly compensates, but this is weaker than the strict CI-lower materiality test and must be operator-accepted before freeze. |

**Governance position.** EXP-014 confirms the legs are **internally consistent** with the
predeclared coverage matrix; it does **not** establish that the reduced-conservatism L4/L5
are independently sound for live use. The legs therefore **must not be treated as validated
for freeze** until an operator records acceptance of the L4/L5 reductions (or overrides them
to the strict CI-based forms and re-validates). This is moot while EXP-015 stands REFUTED,
but it is a precondition for any future attempt to fix and freeze the incremental unit.

---

## 6. Re-validation and rerun consequences

| Experiment | Touched by | Rerun required? | Outcome (confirmed) |
| --- | --- | --- | --- |
| EXP-012 | none | **No** | Unchanged (Track A; does not use the incremental unit). |
| EXP-013 | F01 (verdict), F04 (block length) | **Yes — done 2026-06-04** | **PASS** confirmed: 108/108 recovery, 8 PASS / 3 `UNDER_POWERED` (BTCUSD/1h, BTCUSD/4h, USTEC/4h) / 1 `NULL_COST_DOMINATED` / 0 phantom, binding control powered 9/12, across-draw verdict basis recorded. |
| EXP-014 | F04 (block length) | **Yes — done 2026-06-04** | **PASS** confirmed: 7/7 verdicts + 35/35 leg states reproduced; `effective_n` episode-aware (`276.9` on `all_pass`); EXP-013 dependency gate re-confirmed PASS. |
| EXP-015 | F03 (diagnostics), F04 (block length, no-op for per-row) | **Yes — done 2026-06-05** | **REFUTED** confirmed (5m 1 fail, 1h/4h 2 fails; FPR ≤ `0.01`); `leg_pass_rates.csv` + `tpr_by_instrument.csv` attribute the failure to the **L2 standalone-significance leg driven by BTCUSD** (pooled TPR held below the `0.80` floor). |
| EXP-016 | upstream only | **No** — remains BLOCKED | EXP-015 stays non-`COMPLETE` (REFUTED) and the dogfood reference book is still undefined, so the precondition gate still blocks. |

**Phase-level outcome is unchanged in direction:** Phase 003 cannot reach
`FULL_FRAMEWORK_CONCLUDED` because the incremental unit is not validated/calibrated
(EXP-015 REFUTED). The **PARTIAL_SUCCESS** outcome and the operator decision it requires
(rescope Phase 004 to standalone-only, or open an incremental-unit follow-up) stand. The
EXP-013 → EXP-014 → EXP-015 re-validation reruns are **complete (2026-06-04/05) and confirm
every expectation above**; the phase `retrospective.md` should now be authored.
