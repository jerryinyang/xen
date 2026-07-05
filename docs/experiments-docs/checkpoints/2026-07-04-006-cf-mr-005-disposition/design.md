# Checkpoint 006 — CF-MR-005 Disposition Phase (2026-07-04)

**Phase container** for the experiments that decide CF-MR-005's fate on valid evidence.
First phase run entirely under the INFR-001 pipeline (mechanism-first design → fresh-context
QA → operator execution gate → estimand script gate → data-analyst evidence → operator
verdict; hard gates integrity-only, `xen.evaluation` toolbox informative, frozen referee
retired from service).

## Context

VAL-006 (2026-07-04) re-derived the entire EXP-014b/c/016/017 multi-leg record from per-leg
truth after critical-017: the 61-cell extend field collapsed to a thin residue — a US2000
e0/e2 ladder cluster (net/leg CI_low>0, 2022-concentrated) and a US500 both-leg cluster
(positive in all 4 variants, ≤4 legs). CF-MR-005's mechanism and persistence questions were
disqualified upstream, never validly tested. Operator decisions (2026-07-04):

- exposure-honest evaluation (never raw-B&H kill verdicts; avg+peak normalizations);
- controlled thesis-shopping sanctioned — the residue clusters may be re-specified as a
  deliberate model and tested through the full critical lens;
- **one exhaustive disposition experiment**, full price-primary (new engine runs, correct
  emission contract), not analysis-only.

## Phase objectives

1. **EXP-018** — faithful, deliberately-specified ladder harvest disposition probe
   (see `python/experiments/EXP-018/design.md`): does the residue survive as a real,
   exposure-honest, regime-robust edge when the model is specified on purpose, emitted with
   the correct accounting contract, and evaluated natively?
2. Any follow-up probes this phase spawns (new EXP-IDs, same discipline).
3. **Retrospective**: family disposition decision (operator-signed) — continue, re-scope, or
   retire CF-MR-005 — on tested evidence, not upstream disqualification.

## Phase constraints

- TRAIN band only unless the operator explicitly authorizes a corrected TEST-read policy
  (EXP-016's 3 reads remain SPENT_ON_DEFECT; AUDUSD/NZDUSD/US2000-4h strata at 1/2).
- Estimand gate (`xen.estimand_validation`) blocking before any analysis; accounting only via
  `xen.adjudication`.
- No frozen-referee calls; evaluation via `xen.evaluation`, composed in the design.
- Family status untouched until the retrospective.

## Success criteria (phase)

The phase succeeds when the operator can sign a family disposition supported by at least one
validly-tested, exposure-honest read of the residue clusters — in either direction.
