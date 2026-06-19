# Report: EXP-070 — Event-Level Method Calibration (EXP-027-Analog, TRAIN-only)

**Verdict:** CALIBRATION_DELIVERED
**Phase:** 016 — CF-HA-HARAMI-001 candidate screening
**HYP:** HYP-023 (registered in `docs/signal-registry/multiplicity-registry.md`)
**Date completed:** 2026-06-18
**Audit:** PASS
**TEST reads consumed:** 0
**Candidate slots consumed:** 0

---

## Purpose

EXP-070 is the EXP-027-analog (EXP-044-analog on the per-cell unit) for Phase 016. It
measures, for each of the six predeclared P5 TEST-family cells, whether the frozen
EXP-068 `N-PARTIAL-V2A` event-level inference machinery exhibits controlled per-cell
false-positive rate, finite CI recovery, and deterministic replay — using TRAIN rows only,
before any TEST contact. It does not evaluate the candidate signal; it validates that the
inference method itself is calibrated at each cell's realized event count. The output is
the per-cell calibration map that fixes the EXP-071 binding family and the calibrated
margin (P9 condition 4) that the EXP-071 freeze file records.

---

## Scope

- **Cells (P5 TEST family):** GBPUSD-5m, GBPUSD-1h, NZDUSD-1h, NZDUSD-2h, GBPJPY-30m,
  US2000-4h (ex-EURUSD, TEST-capped instrument-wide).
- **Signal:** MA(20,50)-native `/STRONG-STAT`-conditioned HA harami; `N-PARTIAL-V2A` arm
  (3-leg scaled partial exits, fractions {1/3, 2/3, 1} × 50% m_sofar, V2A equal weights).
- **Data:** TRAIN rows only (first 49% per file per cell). Zero TEST/holdout contact.
- **Nulls (two structurally-different generators):**
  - Null-A: matched-random placement on the real path (placement permutation).
  - Null-B: block-circular path rotation (block_len = round(n_bars^(1/3))); real
    placement, scrambled forward path.
- **Draws:** 1000 draws per (cell, null).
- **Bootstrap:** regime-clustered MBB, b = round(m^(1/3)), N_BOOT = 10,000,
  deterministic per-cell seed.
- **Binding FPR object (post D0-amendment-003):** full conjunction
  `ci_low_1s > 0 ∧ mean_ci_low_1s > 0 ∧ beats_rm_low_1s > 0`.
- **Binding null (post D0-amendment-004):** Null-A only; Null-B advisory.

---

## Key results

**All six cells: PASS. Experiment verdict: CALIBRATION_DELIVERED.**

| Cell | Null-A conj FPR | MDE | Calibrated margin | Temporal flag |
| --- | --- | --- | --- | --- |
| GBPUSD-5m | 0.035 | 0.025 ATR | 0.0533 ATR | GROWING |
| GBPUSD-1h | 0.014 | 0.025 ATR | 0.1263 ATR | DECAYING |
| NZDUSD-1h | 0.031 | 0.025 ATR | 0.1496 ATR | DECAYING |
| NZDUSD-2h | 0.031 | 0.025 ATR | 0.1678 ATR | STABLE |
| GBPJPY-30m | 0.014 | 0.025 ATR | 0.0722 ATR | DECAYING |
| US2000-4h | 0.018 | 0.025 ATR | 0.1614 ATR | STABLE |

- P12 reconciliation: exact (all abs-diffs = 0.0 — byte-identical reuse of EXP-068 / EXP-061 / EXP-066 bootstrap outputs).
- Determinism: PASS (2-cell cross-process byte-identical replay).
- All 1000/1000 draws complete for every (cell, null) pair.

---

## Amendment history

**D0-amendment-003 (2026-06-18):** After the first run returned `METHOD_DEFECT` on the
median-leg FPR object, the binding FPR object was corrected to the full conjunction (the
P4/P9 cell-acceptance event). The Null-B `beats-RM` arm was symmetrized. Second run
executed.

**D0-amendment-004 (2026-06-18):** The second run returned `METHOD_DEFECT` with Null-A
conjunction FPRs all controlled (0.014–0.035) but Null-B conjunction FPRs inflated in 5
of 6 cells (0.161–0.773) due to a **structural geometry bias** — STRONG-STAT conditioning
creates a systematic barrier-geometry advantage at the entry point that block rotation
cannot remove, because the geometry is a property of the entry, not the forward path. The
bias is timeframe-graded: longer TFs exhibit more extreme STRONG-STAT conditioning and
larger geometry gaps. All three Null-B conjunction legs are co-determined by the same
cause (dropping `beats-RM` from the Null-B conjunction changes nothing; confirmed by
`fpr_med_mean_nullB = fpr_full_conj_nullB` in all cells). The operator directed
**Option 3** (no re-run): Null-A is the sole binding null; Null-B is an advisory
contextual diagnostic. Under this amendment, all six cells pass.

---

## Interpretation of cell-level results

**GBPUSD-5m (PASS, GROWING).** Null-A FPR = 0.035 (controlled), MDE = 0.025 ATR,
calibrated margin = 0.053 ATR. The GROWING flag indicates the most recent TRAIN quarter
shows higher median (0.880 vs 0.697 full-TRAIN) — the signal appears to be strengthening
toward the present. Null-B FPR = 0.027 (also controlled), consistent with minimal
STRONG-STAT geometry gap at the 5m timeframe.

**GBPUSD-1h (PASS, DECAYING).** Null-A FPR = 0.014 (tightly controlled), MDE = 0.025
ATR, calibrated margin = 0.126 ATR. The DECAYING flag is severe: the final TRAIN quarter
median is −0.158 ATR (negative) against a full-TRAIN median of 1.565 ATR. The inference
method is calibrated, but the signal's recent TRAIN history is adverse. EXP-071
interpretation should weight this flag. Null-B FPR = 0.363 (inflated — structural geometry
bias, timeframe-graded).

**NZDUSD-1h (PASS, DECAYING).** Null-A FPR = 0.031, MDE = 0.025 ATR, calibrated margin
= 0.150 ATR. DECAYING flag is mild: final quarter 1.049 vs 1.533 full-TRAIN, still
positive. Null-B FPR = 0.340 (inflated — structural).

**NZDUSD-2h (PASS, STABLE).** Null-A FPR = 0.031, MDE = 0.025 ATR, calibrated margin =
0.168 ATR. Temporal stability is STABLE (final window 1.523 vs full-TRAIN 1.338, within
1 boot_se). The largest calibrated margin in the family (0.168 ATR), reflecting moderate
Null-A pseudo-signal spread. Null-B FPR = 0.759 (severely inflated — strongest
STRONG-STAT geometry gradient at the 2h timeframe).

**GBPJPY-30m (PASS, DECAYING).** Null-A FPR = 0.014 (tightly controlled), MDE = 0.025
ATR, calibrated margin = 0.072 ATR. DECAYING flag is severe: final quarter median ≈ 0
ATR (machine-precision zero) against full-TRAIN median 1.210 ATR. EXP-071 should weight
this flag. Null-B FPR = 0.161 (moderately inflated — consistent with 30m intermediate
geometry gradient).

**US2000-4h (PASS, STABLE).** Null-A FPR = 0.018 (tightly controlled), MDE = 0.025 ATR
(TPR = 0.860 at g = 0.025, tight but sufficient), calibrated margin = 0.161 ATR. CI width
is 2.30 ATR (widest in the family — m = 152 events). Temporal stability is STABLE, but
the final window has only 2 events (below the powered floor); the STABLE flag is
conservative. Null-B FPR = 0.773 (most severely inflated — consistent with the most
extreme STRONG-STAT geometry gradient at the 4h timeframe).

---

## EXP-071 authorization

EXP-070 clears the Phase 016 D0 P7/P8 pre-TEST gate. The following are finalized for
the EXP-071 freeze file:

- **Binding TEST family:** all six P5 cells (GBPUSD-5m, GBPUSD-1h, NZDUSD-1h,
  NZDUSD-2h, GBPJPY-30m, US2000-4h).
- **Per-cell calibrated margins (P9 condition 4):** as tabulated above.
- **Per-cell MDE context:** all six cells, 0.025 ATR.
- **Temporal stability disclosure:** GROWING (GBPUSD-5m), DECAYING×3 (GBPUSD-1h severe,
  NZDUSD-1h mild, GBPJPY-30m severe), STABLE×2 (NZDUSD-2h, US2000-4h).
- **Null-B advisory context:** 5m controlled (0.027); longer TFs inflated (0.161–0.773)
  by structural STRONG-STAT geometry gradient — disclosed as path-continuity diagnostic.

EXP-071 one-shot TEST confirmation of the non-4h FX core under `N-PARTIAL-V2A` is now
authorized. TEST family is frozen at the six cells above; no further modification is
permitted before the TEST read.

---

## Signal-registry disposition

**Registry: not applicable — calibration/methodology experiment.** EXP-070 consumes
0 candidate-screening slots and 0 TEST reads. It is an EXP-027-analog (method
validation), not a signal evaluation. The HYP-023 row in
`docs/signal-registry/multiplicity-registry.md` is annotated to reference
D0-amendment-003 and D0-amendment-004 (no new slot, no outcome row). The EXP-071 TEST
read will be recorded in `docs/signal-registry/test-read-ledger.md` when EXP-071 executes.

---

## Audit caveats carried forward

From `audit.md`:

- **W1 (Design-criteria tension, resolved):** The original P7 Leg 1 (median-leg FPR)
  was inconsistent with the P4/P9 conjunction cell-acceptance event. Resolved by
  D0-amendment-003 (binding object corrected to full conjunction).
- **W2 (Null-B geometry bias, advisory):** Null-B RM arm entries are drawn from the
  general pool (m_sofar > 0), creating a geometry mismatch with the STRONG-STAT signal
  entries (m_sofar ≥ p75). This is a structural design limitation of Null-B, not a code
  error. Resolved at the verdict level by D0-amendment-004 (Null-B demoted to advisory).
  The bias is documented and disclosed in the EXP-071 freeze file.

No Critical or Info-level audit findings required post-amendment changes.
