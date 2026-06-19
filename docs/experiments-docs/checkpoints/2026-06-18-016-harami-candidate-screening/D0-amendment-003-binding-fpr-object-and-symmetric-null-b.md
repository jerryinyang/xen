# D0-amendment-003 — Binding FPR object (P7 Leg 1) + symmetric Null B

**Date:** 2026-06-18
**Checkpoint:** `2026-06-18-016-harami-candidate-screening`
**Authority:** This amendment supersedes the named clauses of `D0-predeclarations.md`
(per P15). The base document is not retroactively edited.
**Trigger:** EXP-070 first run (2026-06-18) returned `METHOD_DEFECT`; the EXP-070 audit
(`python/experiments/EXP-070/audit.md`) identified (a) a design-criteria inconsistency
between P7 Leg 1 and P4/P9, and (b) an implementation asymmetry in the Null B `beats-RM`
arm. Operator reviewed the audit and the "accept vs. amend" options and **directed the
amendment + re-run** (decision recorded 2026-06-18).

---

## What changed

### Change 1 — Binding FPR object: median leg → full conjunction (supersedes P7 Leg 1)

**Before (P7 Leg 1):** a cell "passes FPR" iff the proportion of null-draw runs calling
**`median CI_low > 0`** ≤ 0.05; FPR-exclusion at > 0.06; `METHOD_DEFECT` if > 2/3 of cells
fail.

**After:** the binding FPR object is the **full conjunction already defined in P4 and gated
on in P9** — a null draw is a false positive iff
**`median CI_low > 0` ∧ `raw-mean CI_low > 0` ∧ `beats-RM contrast CI_low > 0`**
(the exact event P9 uses to clear a cell for composition, minus the calibrated-margin
condition, which this calibration *produces*). All P7 Leg 1 thresholds carry over **onto
the conjunction object, unchanged in value**:

- a cell **passes FPR** iff conjunction-FPR ≤ α₀ = 0.05;
- conjunction-FPR in (0.05, 0.06] → **retained with record**;
- conjunction-FPR > 0.06 under either null → **excluded** from the binding EXP-071 family
  with record (disclosed in the freeze file, P8);
- **`METHOD_DEFECT`** iff > 2/3 of the six P5 cells (≥ 5) fail conjunction-FPR control
  under either null, or any retained cell has a degenerate CI, or determinism fails.

The **median-leg FPR remains computed and reported** as a **disclosed, non-binding
diagnostic** (it is the P3 viability endpoint and stays informative), alongside the
binding conjunction-FPR.

**Why this is a correction, not metric-shopping:**

1. **It removes a pre-existing D0 inconsistency.** P4 ("a cell passes the full conjunction
   iff `median CI_low>0 ∧ raw-mean CI_low>0 ∧ beats-RM CI_low>0`") and P9 (composition
   threshold) already define the EXP-071 **cell-acceptance event** as this conjunction.
   P7 Leg 1 calibrated the FPR of a **sub-leg** (median only), not the event actually
   gated on. The amendment makes EXP-070 calibrate the **same object EXP-071 fires on** —
   the correct calibration target by construction.
2. **The object is not newly chosen after seeing results.** The conjunction was ratified at
   G0 (P4/P9) before any EXP-070 result existed. EXP-070's first run already emitted the
   conjunction-FPR as the predeclared "disclosed secondary FPR." This amendment elevates an
   already-predeclared object; it does not introduce a new statistic, arm, or threshold.
3. **The numeric thresholds (α₀=0.05, 0.06 tolerance, >2/3 defect rule) are unchanged.**
   Only the object they apply to changes, from median-leg to the P4/P9 conjunction.
4. **The median leg is not discarded** (anti-suppression): it is retained as a disclosed
   diagnostic, so the substrate-driven nature of the absolute median stays visible to the
   EXP-071 freeze decision.

Predeclared consequence (unchanged from design §7 / P7): a `METHOD_DEFECT` under the new
binding object would again require fix-and-re-run before any TEST contact, with no counted
reads consumed.

### Change 2 — Null B `beats-RM` arm symmetrized (clarifies P7 Leg 1 null construction)

P7 Leg 1 requires "matched-structure null populations." EXP-070 operationalised two nulls
(scope/analysis-plan Step 3): Null A (matched-random placement, real path) and Null B
(block-circular-rotated path, real placement). The audit found the Null B `beats-RM` arm
was constructed **asymmetrically**: the matched-random (RM) arm took its entry close and
time caps from the **rotated** path while taking `rd`/`m_sofar`/ATR from the **real** state
at the same indices, whereas the Null B signal arm used fully real entry geometry walked
forward on the rotated path. The mismatch biased `beats-RM` and inflated the (then
non-binding) Null B conjunction-FPR in a count-graded way.

**After:** the Null B RM arm must use the **same real entry geometry as the Null B signal
arm** (real entry close, `rd`, `m_sofar`, ATR, time caps at the drawn indices) and resolve
forward on the rotated path — so both Null B arms differ from each other only in placement,
and from the real signal only in the permuted forward path. This is required because the
conjunction-FPR (which includes `beats-RM`) is now the **binding** object under Change 1;
the Null B contrast must therefore be a faithful true-edge-0 comparison.

---

## Multiplicity / TEST-read impact (P15-required)

- **New multiplicity slot consumed:** **No.** HYP-023 remains a single method-calibration
  item. No new candidate, variant, detector, or parameter branch is introduced; the
  conjunction object pre-exists in P4/P9. `multiplicity-registry.md` HYP-023 row is updated
  in place to note the amendment (no new row, no renamed item).
- **New TEST read consumed:** **No.** EXP-070 remains TRAIN-only (first 49% per file). The
  six P5 strata stay at **0 counted reads** (`test-read-ledger.md`). No TEST or holdout row
  is loaded by the re-run.
- **TEST family (P5):** **Unchanged** — six cells, frozen. This amendment does not add or
  remove any cell.
- **Calibrated margin (P9 condition 4):** the per-cell "calibrated margin (R1.2 analog)"
  that P9 references as an EXP-070 Leg-1 output is to be derived from the **same conjunction
  calibration** under this amendment (an EXP-070 deliverable feeding the EXP-071 freeze
  file). Its exact construction is specified in the amended EXP-070 analysis-plan and is not
  a new D0 item.

## Affected artifacts (to be updated in this change)

- `python/experiments/EXP-070/scope.md` — Success/Failure criteria, binding FPR object,
  `METHOD_DEFECT` trigger, Null B RM-arm construction (reference this amendment).
- `python/experiments/EXP-070/analysis-plan.md` — Step 3 (symmetric Null B RM arm), Step 4
  (binding conjunction-FPR + verdicts), Interpretation guide.
- `python/experiments/EXP-070/code/run_experiment.py` — symmetric Null B RM arm; bind
  `classify_cell` / `experiment_verdict` on conjunction-FPR; median-leg retained disclosed.
- First-run results archived (not overwritten) under `python/experiments/EXP-070/results_v1/`
  with this amendment cited, preserving the `METHOD_DEFECT` record.
- `docs/signal-registry/multiplicity-registry.md` — HYP-023 row annotated (amendment-003;
  no new slot).

## Operator sign-off

Operator directed this amendment on 2026-06-18 after reviewing the EXP-070 audit and the
explicit accept-vs-amend decision, and selected the **full-conjunction** binding object.
This entry constitutes the P15 sign-off record. Re-ratification of the affected clauses
(P7 Leg 1; P7 null-construction) is granted on the terms above. All other D0 items (P1–P6,
P8–P14) stand unchanged.
