# EXP-071 — One-Shot TEST Confirmation of the Full G-015 Passing Cell Set

**Family:** CF-HA-HARAMI-001 / CAND-001 (MA-native) · **HYP-024** · **Phase 016**
**Verdict:** `TEST_NOT_CONFIRMED` (Evidence AGAINST, on this scope)
**Date:** 2026-06-19 · **Posture:** gross only · **Audit:** PASS (0C/1W/3I) ·
**Governance:** pre-exec APPROVE / post-exec APPROVE

---

## One-line finding

The MA(20,50)-native `/STRONG-STAT`-conditioned HA harami under `N-PARTIAL-V2A` **does not
confirm** on its first TEST contact: **0/6** binding cells clear the predeclared composition
conjunction and **4/6** have median CI_low ≤ 0 — a majority directional negative. CAND-001 is
retired on this scope; the family stays OPEN. Six counted TEST reads consumed (one per stratum).

## What was tested

The harami family's first counted TEST read, mirroring EXP-037/038 in the AVWAP pipeline. After
EXP-070 delivered a Null-A-controlled, finite-MDE, deterministic event-level method
(CALIBRATION_DELIVERED), the frozen EXP-068 inference machinery (`N-PARTIAL-V2A` /
`N-V2A×ADV-NONE` / `N-BENCH` / `RM-native`) was applied **unchanged in semantics** to the TEST
stratum (next 21% of each instrument's 1-minute file, after the first-49% TRAIN slice) of the
predeclared 6-cell binding family:

> GBPUSD-5m, GBPUSD-1h, NZDUSD-1h, NZDUSD-2h, GBPJPY-30m, US2000-4h (ex-EURUSD)

**Binding gate (D0 P9):** a cell clears iff median CI_low>0 (Holm) ∧ raw-mean CI_low>0 ∧
beats-RM CI_low>0 (Holm) ∧ median > EXP-070 calibrated margin. Confirmation required ≥3 clearing
cells over ≥2 instruments, ≥2 non-4h.

## Result

| | value |
| --- | --- |
| Cells clearing the full conjunction | **0 / 6** |
| Cells with median CI_low ≤ 0 (1s) | **4 / 6** |
| Powered cells (≥30 events) | 6 / 6 (m = 3843/376/287/129/554/75) |
| Holm-significant median cells | 1 (GBPUSD-5m) |
| Holm-significant beats-RM cells | 1 (GBPUSD-5m) |
| Raw-mean-positive cells | 1 (GBPJPY-30m) |
| Portfolio composite median CI (non-binding) | 0.774 [0.496, 0.952] — **GBPUSD-5m-dominated** |
| P12 reconciliation / determinism | exact 0.0 / PASS |

No single cell passes all four legs: GBPUSD-5m (the lone Holm-significant, beats-RM, GROWING,
high-n cell) fails on raw-mean (tail-dragged, yellow-flagged); GBPJPY-30m (the lone raw-mean-
positive cell) fails both family-corrected Holm legs. The verdict is mechanically
TEST_NOT_CONFIRMED (majority median CI_low ≤ 0; D0 P9), not INCONCLUSIVE.

## Key interpretation points

- **The positive composite is one cell, not breadth.** The equal-weight composite is event-pooled
  (m_total=5264; GBPUSD-5m = 73%), so its positive median is essentially GBPUSD-5m. It is a
  non-binding disclosure and does not rescue the per-cell failure.
- **Family not refuted.** Positive median tilt across most cells and one genuine survivor
  (GBPUSD-5m) argue against closure. This is a candidate-definition negative on this scope.
- **GBPUSD-5m yellow flag** is the textbook PARTIAL_RECOVERY tail-drag (median+, beats-RM+,
  winsorm+, raw-mean−) — the natural seed for a TRAIN-only loss-tail diagnostic.
- **Part of the negative is power-limited** (NZDUSD-1h median CI_low −0.056; US2000-4h n=75),
  but this does not change the predeclared verdict.

## Registry disposition (Stage 7)

Registry-relevant — updated in the same change:

- **`docs/signal-registry/candidate-families/harami.md`** — CAND-001 marked
  `SCREENED — TEST_NOT_CONFIRMED (this scope); family OPEN`.
- **`docs/signal-registry/multiplicity-registry.md`** — HYP-024 / EXP-071 outcome recorded
  (TEST_NOT_CONFIRMED); CAND-001 slot retained in the ledger (refuted-on-scope, never deleted);
  6 counted TEST reads recorded; HYP-027/EXP-074 confirmed as the routed follow-up.
- **`docs/signal-registry/test-read-ledger.md`** — **6 counted TEST reads** entered (GBPUSD-5m,
  GBPUSD-1h, NZDUSD-1h, NZDUSD-2h, GBPJPY-30m, US2000-4h → each 1/2 lifetime); portfolio
  composite entered as a **disclosure** against all 6 strata.

## Routing

- **No EXP-072 / EXP-073** (conditional on TEST_CONFIRMED — not met).
- **EXP-074 / HYP-027** (registered, TRAIN-only diagnostic): characterize the GBPUSD-5m large-loss
  tail (exhaustion-magnitude bound; harami-polarity↔reversal-direction agreement) on TRAIN only,
  no candidate slot, no TEST contact; Phase 016 D0 addendum required before execution.
- **G-016 adjudication** pending — desk gate on the TEST_NOT_CONFIRMED readout, the disclosed
  composite caveat, and the EXP-074 routing.

## Artifacts

`scope.md` · `analysis-plan.md` · `code/run_experiment.py` · `frozen_selection.json`
(SHA `ca16bcd…`) · `governance/pre-execution-review.md` (APPROVE) · `audit.md` (PASS) ·
`results.md` · `governance/post-experiment-review.md` (APPROVE) ·
`results/{per_cell_results.csv, portfolio_results.csv, composition_verdict.json,
test_read_manifest.csv, run_metadata.json}` · `plots/` (5).
