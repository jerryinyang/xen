# EXP-096 — Post-Experiment Governance Review (Stage 8)

**Experiment:** EXP-096 — Noise Infusion: Realistic 1-Minute Entry Fill (RSI-2 Fade Portfolio, 8 cells)
**Phase:** 022 · **Family/HYP:** `CF-MR-001`/`HYP-003` (fill-realism leg) · **Date:** 2026-06-25
**Artifacts reviewed:** `audit.md`, `results.md`, `report.md`, the index/registry updates · **Against:** the bundled
governance constraints + the Stage-8 forensics/disposition requirements.

---

## Verdict

```text
VERDICT: APPROVE
```

EXP-096 is a clean analysis-set disclosure with an audit that carried full verdict forensics, an interpretation
anchored to the pre-registered criteria with no goalpost movement, and complete, accurate registry/ledger
dispositions. No Critical or Warning findings; no verdict-material issue was documented-and-proceeded.

---

## Checks applied

### 1. Audit carried verdict forensics (Stage-8 gate) — PASS
The audit re-derived the binding numbers from raw artifacts (it did not accept them at face value) and includes
all three required forensics:
- **Per-stratum masking check:** re-derived the v2 portfolio ADDS_VALUE per cell — all 8 per-cell v2 Sharpe LBs
  positive (min 0.130 EURJPY-4h, median 2.554, max 3.652), portfolio LB (5.147) > best single cell → the pooled
  headline is **not masking heterogeneity**; the portfolio is the legitimate estimand and the cross-cell-median
  baseline honestly represents the eight cells. The one weak cell (EURJPY-4h) is surfaced, not buried.
- **Mechanism statement:** the exact −0.05 ATR/event uniform slippage halves both the portfolio LB and the
  baseline (relative margin preserved; not variance hiding, keep mask byte-identical to EXP-093); v3 breaks the
  fast 1h cells because a 3-minute swing is a larger ATR fraction there.
- **Gate-shape check:** the binding Sharpe LB + co-binding Calmar LB capture the v3 catastrophe on both legs; the
  breaker's v2-neutral / v3-protective behavior is a genuine edge-decay-threshold effect, flagged for the
  interpreter and the G-022a A-vs-B decision.

### 2. Materiality / blocking — PASS
0 Critical, 0 Warning, 5 Info. Each Info is shown unable to move any verdict-bearing number (overlay seed; v3 is
disclosure-only with v2 binding; the NOISE_DEGRADED flag is non-binding under portfolio-only membership;
causality/determinism coverage on RNG-free or structurally-causal code). No verdict-material finding was
down-classified, so the materiality gate's no-rerun path is correctly justified.

### 3. Per-stratum doctrine in the result — PASS
The binding estimand is the portfolio (a genuine combined return stream, not a collapsed `.all()` over per-cell
verdicts), with per-cell degradation + per-cell baselines emitted as disclosure (LESSON-001). No collapsed
cross-cell PASS/FAIL is presented as the verdict.

### 4. No goalpost movement — PASS
`results.md` dispositions map one-to-one to the pre-registered SURVIVES/WITHIN-NOISE/BREAKS table: binding v2
SURVIVES (margin +2.59 > sampling band 1.35, co-binding Calmar); adaptability NEUTRAL-at-v2; gate clearable;
EURJPY-4h flagged-retained. m\* was inherited (not recomputed) per the operator decision recorded at Stage 1/2 —
not a post-hoc relaxation. v3 is consistently labelled a disclosure-only stress ceiling, not the binding read.

### 5. OOS holdout / look-ahead / real-price / determinism — PASS
`holdout_untouched=true`, `counted_test_reads=0`, `candidate_slots=0`; analysis slice only; entry-fill fenced at
`train_edge_epoch`; causal-fill + causal-weight assertions PASS; provenance abs-diff 0.0 vs EXP-093; MTM
conservation ≤1.4e-14; determinism byte-identical; real-price fills only. (All re-derived in the audit.)

### 6. Signal-registry disposition recorded (Stage-8 requirement) — PASS
A disposition is recorded in `report.md` and **applied in the same change**, and the result is registry-relevant:
- `candidate-families/cf-mr-001.md` — EXP-096 outcome under HYP-003; status **unchanged** (ADMITTED/TRADABLE,
  0 new slots) — correct (a deployment-wrapper leg, no new signal candidate).
- `multiplicity-registry.md` — Phase 022 EXP-096 row advanced `PLANNED → COMPLETE` with the outcome (retained).
- `test-read-ledger.md` — EXP-096 entered as a **disclosure** (portfolio-aggregate / cost-re-resolution,
  EXP-085 precedent): 0 counted reads, 11 carried strata stay 1/2, 37 stay 0/2, holdout never loaded. The
  Stage-4 read-accounting ratification is consistent with the recorded outcome.
- Master index updated live-status only (no per-experiment card); family detail index carries the full card.

---

## Info notes (carried, non-blocking)
- The five audit Info notes (overlay bootstrap-seed namespace; v3 stress-ceiling framing; NOISE_DEGRADED flag is
  full-analysis-set vs a TEST-calibrated margin; single-event causal-fill probe; determinism replay scope) are
  recorded for the interpreter/G-022a and move no verdict-bearing number.
- **For G-022a (not a governance defect — a routing input):** the A-vs-B evidence now leans toward Portfolio B
  (free at v2, large tail insurance at v3), and EURJPY-4h's flag raises the carry-8-vs-trim-to-7 membership
  question. These are the freeze-gate decisions, correctly left to G-022a.

---

## Completion authorization
All eight pipeline stages are complete with passing governance at both gates. EXP-096 is **APPROVED**. The phase
proceeds to the **G-022a** pre-holdout freeze (governance gate, not an experiment); **EXP-097** (the single
sanctioned global-holdout release) runs only after that freeze.
