# Pre-Execution Governance Review — EXP-044

**Date:** 2026-06-11
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, `code/cell_calibration.py`
**Phase alignment:** Phase 011 design §5.3 (EXP-027-analog) / §8.2 (G1 leg ii); registered 2026-06-11 in the multiplicity registry (Track A, 0 slots, 0 TEST reads); G1-gate-review.md adjudication 1 of 2 names EXP-044 as the binding remaining G1 condition. No misalignment.

## Core constraints

- **Simplicity:** the simplest sufficient design — the frozen EXP-027 machinery re-applied per cell with the aggregation/Holm steps removed; no new inference objects. The dropped second-horizon robustness leg and unused truncation rule are justified by EXP-027 precedent and the per-draw-all-edges structure. PASS.
- **No academic-finance pitfalls:** non-parametric throughout (placebo/permutation nulls, regime-cluster bootstrap, sign permutation, Wilson intervals); two structurally different nulls; no normality/stationarity/i.i.d. assumptions. PASS.
- **Strict scoping:** single question (per-cell error control + recovery at realized counts); boundaries explicit (50 READY cells, TRAIN-only, JP225-2h excluded); measurable per-cell and experiment-level criteria predeclared; budget 4 tests / 5 plots / 1 module, met exactly. PASS.
- **OOS holdout:** F01 file-order TRAIN slice (`head(train_rows)` on a lazy scan with column projection) — TEST and the final-30% holdout never enter the scan engine; chronological order re-asserted; regime indices interior-bounded. PASS.
- **Look-ahead:** placement and control matching use only bar-index regime/anchor/trigger-location information; forward `H_cal` returns are outcomes only; planted drift touches outcomes only. PASS.
- **Real-price discipline:** outcomes are direction-signed log bps on real domain `Close`; the N2 block-permuted series is a scoped synthetic **null**, not a tradable claim. PASS.
- **Anti-overfitting fence:** real trigger locations are exclusions only; real event outcomes never computed; calibration frozen relative to Track B results by construction. PASS.
- **Zero-baseline/denominators:** null excess exactly 0 bps; denominators are reportable matched events / reportable draws (never bars); non-finite MDE reported as null; unreportable draws and completion rates recorded, not dropped. PASS.
- **Safe optimization:** vectorized control matching guarded by a pre-draw equivalence check against the EXP-021-style reference; bootstrap-once/CI-shift with per-`g` permutation recomputation is exact, not approximate; chunked resampling bounds memory; `tqdm` on the outer cell loop; plots from aggregated summaries only; no import-time side effects. PASS.
- **Determinism:** all randomness through `seed_for`; two predeclared replay cells (BTCUSD-1h, JP225-4h) fully re-run and compared frame-identically; verdict binds determinism. PASS.

## Artifact checks

- **scope.md:** falsifiable per-cell criteria, mandatory holdout exclusion stated, denominator/zero-baseline section present, complexity budget realistic. PASS.
- **analysis-plan.md:** every method carries why-this/simpler-alternative/assumptions; interpretation guide predeclared (COVERED / NOT_COVERED / CALIBRATION_UNDERPOWERED; CALIBRATION_DELIVERED / METHOD_NOT_TRANSFERABLE / INCONCLUSIVE with the >1/3 rule); draw counts (500) shown to meet Wilson precision thresholds by construction. PASS.
- **code:** implements the plan exactly (H_cal=8; edge grid {1,…,128}; 500/1000/1000 counts; α grid with primary 0.05; per-cell rule `effect>0 ∧ ci95_low>0 ∧ p≤α`, no Holm); typed, sectioned, docstringed; NaN paths explicit; EXP-043 dependency gate and per-cell count-consistency gate hard-fail; both modules compile. One declared deviation — the optional TPR truncation rule is unused (structurally unnecessary); this changes no predeclared object. PASS.

## Verdict

```text
VERDICT: APPROVE
```

Computation summary: ~50 cells × (500 N1 draws × 9 edge levels + 500 N2 draws), each draw one regime-cluster bootstrap (1000) and per-edge sign permutations (1000), plus a 2-cell determinism replay — expect tens of minutes to low hours, single machine. *(Superseded by Revision 1 below.)*

---

## Revision 1 — 2026-06-11 (pre-execution adversarial review; re-approved)

Two independent reviews were assessed before any data contact. Dispositions:

**Code fixes applied (valid findings):**

- **Exact-count placement** (review B/F01, valid): per-regime rate rounding let
  placed counts drift from the EXP-043 realized targets (deltas up to ~10
  events). Replaced with deterministic largest-remainder allocation per
  direction plus exact-count placement with in-pool top-up; placed counts and a
  `placement_exact` flag are recorded per draw and summarized in metadata.
- **Pool-restricted pyramids** (B/F02, valid bug): pyramid follow-ons checked a
  global eligibility mask and could land in an adjacent regime's pool near
  boundaries, mislabeling direction. Membership is now tested against the
  generating regime's pool only; verified by a synthetic adjacent-pool test
  (400 trials, no leakage, exact counts).
- **Classification gap closed** (review A/F01, valid): FPR point estimates in
  (α₀, ~0.069) at adequate precision were classed CALIBRATION_UNDERPOWERED.
  Now NOT_COVERED (`fpr_point_above_alpha0_adequate_precision`); UNDERPOWERED
  is reserved for genuine precision/completion shortfalls. Scope and plan
  updated in sync (pre-data, no measured object affected).
- **Source-identity binding** (B/F04, valid): each instrument's source file
  name, total/TRAIN row counts, and TRAIN-end timestamp are now asserted
  against the EXP-043 `boundaries` record; `readiness_map.csv` is cross-checked
  against `power_statement.csv` (50 READY cells, JP225-2h excluded).
- **Fence made literal** (B/F05, valid in spirit; severity overstated — pools
  already excluded real-trigger bars, so outcomes were never gathered): forward
  outcomes at real trigger indices are NaN-masked in both N1 and N2 arrays, so
  any accidental gather propagates loudly.
- **Diagnostics + timing** (A/F04 diagnostic part, A/F07): per-cell regimes per
  direction, block length, and allocation recorded in the coverage map;
  wall-time and placement-fidelity rate recorded in `run_metadata.json`.

**Documentation fixes applied:** predeclared interpretation caveats added for
the H_cal=8 horizon-transfer assumption with a named post-G1 validation item
(A/F02, B/F03), the N2 hybrid-structure asymmetry and its
disagreement-diagnosis procedure (A/F03), small-regime bootstrap coverage
(A/F04), and the per-bar block-length limitation (A/F06); the unused truncation
rule now carries its structural justification (A/F05).

**Pushed back (not implemented):**

- **BCa/bootstrap-t correction or minimum-regime exclusion floor** (A/F04 fix
  suggestion): rejected. The frozen EXP-027 rule — percentile regime-cluster
  bootstrap included — is the object under test; degraded CI coverage at small
  regime counts surfaces as measured FPR excess, which is precisely what this
  calibration exists to detect. Changing the CI method here would be
  metric-shopping, and an a-priori exclusion floor would pre-empt the
  measurement.
- **Secondary H=3/H=6 leg on thin cells now** (A/F02 fix option a): deferred to
  the named post-G1 item, conditioned on where Track B/D actually selects
  exits; running it unconditionally adds compute and scope without a decision
  it would change today.

**Corrected computation estimate:** ≈6 billion sign-multiply operations for
permutations plus ≈0.75 billion bootstrap element-operations across ~275k
draw-evaluations; realistically **several hours single-machine** (not "tens of
minutes"); the 2-cell replay adds ~4%. Elapsed time is now recorded in
`run_metadata.json` for downstream planning.

Both modules recompile; placement unit tests pass.

```text
VERDICT: APPROVE (Revision 1)
```
