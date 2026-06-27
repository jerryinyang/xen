# EXP-091 — Post-Experiment Governance Review (Stage 8)

**Date:** 2026-06-24 · **Reviewer:** research-pipeline (consolidated Stage-8 governance) · **Artifacts
reviewed:** `audit.md`, `results.md`, `report.md`, `python/experiments/INDEX.md`,
`docs/experiments-docs/families/cf-mr-001/INDEX.md`, `docs/experiments-docs/INDEX.md`,
`docs/signal-registry/{candidate-families/cf-mr-001.md, multiplicity-registry.md, test-read-ledger.md}` ·
**Phase:** 021 · **HYP:** `CF-MR-001/HYP-002`.

---

## Verdict-forensics confirmation (blocking check)

- **Per-stratum re-derivation with masking check — PRESENT.** The audit re-derived the verdict per domain and
  per cell (independently from the raw CSVs, not from `run_metadata.json`): RCT 0/10 on 15m, 5/10 on 1h; the
  pooled "RCT passes 5/3" headline is shown to be a legitimate predeclared D6 count (not an illegitimate pooled
  boolean) **but** carrying three masked properties — domain-conditional, boundary-fragile, mean/tail-carried —
  each surfaced and confirmed not to move the mechanical count. **PASS.**
- **Mechanism statement — PRESENT.** The verdict is explained as a pure ATR-normalized cost-geometry effect
  (gross ≈ domain-invariant; fixed-bps RT ÷ entry ATR scales lethally on the faster domain), not signal strength
  — a concrete driver, not a numeric restatement. **PASS.**
- **Gate-shape check — PRESENT.** The binding gate (mean expectancy lower bound) is confirmed the correct
  instrument for a location effect on the mean; the median disagreement on 3/5 clearing cells is recorded for the
  interpreter without retro-editing the gate. **PASS.**

## Materiality / blocking discipline

- **0 Critical findings;** the audit shows affirmatively that every Warning/Info cannot move sample membership, a
  denominator, the binding (mean) metric, causality, or the mechanical screen verdict. No verdict-material
  finding was documented-and-down-classified. The numbers reproduce exactly (net-clear bool vs `net_ci_low>0` 0
  mismatches; cost identity to machine eps; determinism PASS). **No fix-and-rerun owed.** **PASS.**

## Signal-registry disposition (blocking check)

- **Recorded and registry-relevant.** Candidate-family `cf-mr-001.md` advanced (EXP-091 outcome section added;
  family stays `ADMITTED (BINDING)`, Phase 021 OPEN and advancing). Multiplicity registry EXP-091 row advanced
  PLANNED → COMPLETE with **per-exit-family file-drawer outcomes recorded** — RCT clears; ERT, ATR-barrier,
  RSI-revert-on-close, fixed-bar, partial/trail each die (retained, not reopened). **Test-read ledger:** no
  counted read (TRAIN-only); all 48 strata stay 0/2 open — consistent and correctly left unchanged. **PASS.**

## Scope / budget / discipline

- **Single hypothesis, no scope creep.** The screen answers exactly the design §4 EXP-091 question; no candidate
  selection, Holm rule, or TEST read leaked in (those are EXP-092/093). Budget: 2/≤2 tests, 4/≤4 plots, 0/target
  0–1 modules. **PASS.**
- **Holdout / real-price / per-stratum doctrine.** TRAIN sub-split only; analysis-TEST + final-30% never sliced;
  real touched fill prices + real ATR throughout; per-stratum verdict (LESSON-001) honoured — the experiment
  verdict is the predeclared count over per-stratum net-clears, not a collapsed `.all()`. **PASS.**
- **Cost-table provenance.** Phase-021-local table (`D0-amendment-003`, operator-ratified pre-run, hashed);
  shared `xen.capgeo_cost.COST_CONSTANTS` not mutated (Phase-018 integrity). The single most outcome-determining
  input is ratified and its sensitivity disclosed (faster-cost companion). **PASS.**
- **Honest reporting.** `results.md` / `report.md` state the pass is genuine *and* fragile/domain-conditional/
  mean-tail-carried; no inflation of a marginal result. Next step (EXP-092) is a specific new experiment, not a
  scope extension. **PASS.**

## Routing note

The screen is **non-empty** (RCT passes), so the mechanical G-021 NOT_TRADABLE-at-0-reads route does **not** fire
here. Phase 021 correctly advances to EXP-092 (per-instrument cost-bearing sequence, 0 reads / 0 slots), which the
documentation directs to a 1h-scoped, smallest-defensible candidate set centered on the robust core (USTEC-1h,
US2000-1h). G-021 remains PENDING.

---

```text
VERDICT: APPROVE
```
