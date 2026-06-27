# EXP-092 — Post-Experiment Governance Review

**Stage 8 (research-pipeline).** Reviews `audit.md`, `results.md`, `report.md`, and the index/registry updates
against the bundled governance constraints. Confirms the signal-registry disposition and the audit's verdict
forensics.

---

## Verdict forensics confirmation (binding Stage-8 check)

- **Per-stratum re-derivation + masking check** — PRESENT and correct. The audit re-derived the binding read
  **per cell** (all 11 strata), confirmed the `SEQUENCE_PASS` logic on each, and **affirmatively surfaced** the
  pooled "11/11" as a *disclosed* two-tier split (robust core 8 vs mean-carried 1h 2 vs fragile GBPUSD-1h) via
  the reported `margin_preread.csv` columns — not a hidden pooled boolean. The masking check is satisfied. ✓
- **Mechanism statement** — PRESENT. The verdict is driven by the carried cells being the upstream net-clearers
  reproduced on byte-identical populations; 4h dominance is attributed to smaller ATR-normalized cost on the
  slower domain (the EXP-091/094 mechanism). ✓
- **Gate-shape check** — PRESENT. The binding gate is the **mean** (location); the family is median-fragile on
  1h; the audit confirms D5 designates the mean as binding and co-reports the median (the shape read), so the
  gate is the right instrument with the shape disclosed, not retro-edited. ✓
- **Materiality** — every finding classified; **0 Critical, 0 Warning, 4 Info**, each with explicit reasoning
  that it cannot move a verdict-bearing number (two-tier disclosure is captured columns; GBPUSD-1h margin-fail
  is the frozen 4b/4c split; EURUSD dual-stratum is read-accounting for EXP-093; ≤6.2e-4 seed delta keeps every
  sign). No verdict-material finding was documented-and-proceeded. ✓

## Governance constraint review

| Constraint | Verdict |
|---|---|
| Single hypothesis / scope discipline | ✓ one question (which carried cells `SEQUENCE_PASS` → pinned set); no scope creep |
| Holdout untouched | ✓ `holdout_untouched=true`; TRAIN-only loader; 1m walk clipped at TRAIN edge by timestamp |
| Look-ahead / temporal | ✓ verbatim causal EXP-090 engine; domain→1m by timestamp, never bar index |
| Real-price discipline | ✓ real OHLC, ATR units; no synthetic prices |
| Non-parametric / no academic-finance pitfall | ✓ moving-block bootstrap lower bound (the ratified estimator); no normality/iid assumption |
| Per-stratum endpoint (LESSON-001) | ✓ binding read per cell; pooled count = disclosure with split exposed |
| Complexity budget | ✓ 1 test / 4 plots / 0 modules (design §5) |
| No goalpost-moving / no tuning | ✓ frozen D0 rule + cost table + margins; no new statistic ⇒ no bite-check (D0 §D4) |
| Determinism | ✓ replay PASS; output + candidate-set sha256 reproduced (audit re-derived the hash) |
| Honest reporting / no overreach | ✓ results.md states "TRAIN eligibility set, not an edge claim"; fragile cells flagged, not inflated |
| Follow-ups as new scopes | ✓ EXP-093 + deferred levers framed as separate D0s |

## Registry & ledger disposition (binding Stage-8 check)

Registry-relevant; updated in this same change:

- **`multiplicity-registry.md`** Phase 021 batch — EXP-092 advanced `PLANNED → SEQUENCE_DELIVERED` (candidate
  set hash, 11/11 PASS, robust core 8; no new countable item; no item refuted). ✓
- **`candidate-families/cf-mr-001.md`** — EXP-092 outcome section added (candidate set + robust core + EXP-093
  routing). ✓
- **`test-read-ledger.md`** — EXP-092 entered as a **TRAIN-only disclosure, not a counted read**; all 48 strata
  (incl. the 11 carried) remain **0/2 open**. Matches the metadata (`counted_test_reads=0`, `candidate_slots=0`)
  and the TRAIN-only convention. ✓
- **Indexes** — `python/experiments/INDEX.md` row added; `families/cf-mr-001/INDEX.md` lead + cards-table row +
  detailed five-field card added; master `docs/experiments-docs/INDEX.md` CF-MR-001 live-status row updated
  (EXP range `089–094`, lead = EXP-092). ✓

## Verdict

```text
VERDICT: APPROVE
```

The audit carried full verdict forensics (per-stratum masking check, mechanism, gate-shape) and exercised
materiality correctly (no verdict-material finding down-classified). The result is honestly reported as a
TRAIN-only hash-pinned candidate set (not an edge claim), per-stratum, with the quality split disclosed. The
signal-registry disposition is complete and consistent across all three registry files plus the three indexes;
TRAIN-only discipline and the 0/2 strata are preserved. No goalpost-moving, no new statistic, holdout sealed.

**EXP-092 is complete.** Phase 021 advances to **EXP-093** (the one-shot TEST on the smallest-defensible robust
core from this pinned set), a separate scope/D0 that spends the first counted TEST reads (≤1/carried-stratum,
cap 2/stratum).
