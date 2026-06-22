# EXP-081 — Post-Experiment Governance Review (Stage 8)

**Date:** 2026-06-22 · **Reviewer:** research-pipeline consolidated governance
**Artifacts reviewed:** `audit.md`, `results.md`, `report.md`, index updates, signal-registry updates.

---

## Governance checks

| Check | Verdict | Evidence |
|---|---|---|
| Holdout untouched | ✅ | TRAIN sub-split only (`load_first70` → first-70%; EXP-081 slices first 70% of that); `holdout_untouched=true`; ledger disclosure confirms next-21% TEST + final-30% holdout never sliced. |
| Real-price discipline | ✅ | All MFE/MAE/TTP/outcome/ATR on real domain OHLC; HA only for harami entry detection (audit confirmed). |
| Per-stratum verdict (no collapsed PASS/FAIL) | ✅ | Verdict is per substrate-cell completeness; per-substrate medians declared disclosure-only (LESSON-001); no pooled edge claim in results.md/report.md. |
| Scope honored, no scope creep | ✅ | Gross, TRAIN-only, 0 slots; next steps (EXP-082/083) framed as new scopes, not extensions. |
| Complexity budget | ✅ | 2 tests / 5 plots / 2 modules as approved. |
| Methods non-parametric / no academic-finance pitfall | ✅ | Quantile / Hartigan-dip / KDE / moving-block bootstrap; no normality/stationarity assumption. |
| Interpretation honest, no overreach | ✅ | results.md states gross/TRAIN-only/no-edge explicitly; the median-positive harami read is reported with its mean≈0 caveat, not inflated. |

## Audit verdict-forensics confirmation (Stage 8 requirement)

The audit (`audit.md`) carries the mandatory forensics, run autonomously:
- **Per-stratum re-derivation & masking check:** ✅ D3 inputs re-derived from raw bars to full precision;
  the per-substrate medians shown **not** to mask heterogeneity via per-cell paired contrasts vs the
  within-cell SUB-RANDOM control (46 cells). The "entries ≈ random" and harami "median>mean in 33/46
  cells" findings are per-cell, not pooled artifacts.
- **Mechanism statement:** ✅ explains *why* — gross availability ≈ random (regime volatility shared with
  the matched control); harami mean killed by a ~5% catastrophic-minority tail (CF-HA-HARAMI-001 signature
  reproduced); only 1/184 dips resolve because the catastrophe is a heavy continuous tail, not a separated
  mode (so `MAE_q90` fallback dominates, as D9 designed).
- **Gate-shape check:** ✅ confirms `tailmass`/`q05` (on the outcome distribution) carry the
  minority-catastrophe detection, while `m_anti` (on MAE) answers stop-placement — different distributions
  by design, coherent; the shape `ASS` is blind to is surfaced descriptively here.

## Materiality handling

No verdict-material finding was down-classified. The sole Warning (W1: entries ≈ random / median-positive-
mean-killed shape) is shown to move **no** D3-bearing number — it is a mechanistic interpretation of
correct values, raised for Stage 6 and EXP-082/083, not a code defect. I1–I3 are expected-by-design,
bounded, or documented. No fix/rerun was required or skipped.

## Signal-registry disposition confirmation

Registry-relevant; disposition **recorded in the same change** (verified):
- `candidate-families/cf-capgeo-001.md`: HYP-002 advanced GATED → **COMPLETE — CHARACTERISATION_DELIVERED**;
  status header updated; family stays `REGISTERED`/SCREENING (characterization only — no slot, no screen
  verdict).
- `multiplicity-registry.md` (Phase 018 batch): EXP-081 outcome row added — D3 inputs locked for the
  registered `/EXIT-DERIVED` candidates; no new countable item, no item refuted.
- `test-read-ledger.md`: TRAIN-only **disclosure** entered; 0 counted reads; all 48 strata tallies
  unchanged.

## Documentation confirmation

`report.md` self-contained with key plots and registry disposition; `python/experiments/INDEX.md` row
added; family detail card added to `families/cf-capgeo-001/INDEX.md` (with ToC/list); master
`docs/experiments-docs/INDEX.md` live-status (Family Indexes + Checkpoint Status) updated with no
per-experiment card. Phase alignment intact (HYP-002 characterize → HYP-003 derive next).

---

```text
VERDICT: APPROVE
```
