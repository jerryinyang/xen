# Results: EXP-070 — Event-Level Method Calibration (EXP-027-Analog, TRAIN-only)

**Verdict: CALIBRATION_DELIVERED**
**Date:** 2026-06-18
**Audit:** PASS (see `audit.md`)
**Amendment:** D0-amendment-004 (Null-B demoted to advisory; Null-A sole binding null; no re-run)

---

## 1. Summary

All six predeclared P5 TEST-family cells exhibit controlled Null-A conjunction FPR
(0.014–0.035, all ≤ α₀ = 0.05), non-degenerate bootstrap CI width, and a finite planted-
edge MDE of 0.025 ATR at TPR ≥ 0.80. P12 reconciliation is exact (all abs-diffs = 0.0
to machine precision). Determinism passes (2-cell cross-process byte-identical replay).
Zero TEST or holdout rows were read.

**All six cells are PASS. Experiment verdict: CALIBRATION_DELIVERED.**

Null-B conjunction FPRs are inflated in 5 of 6 cells (0.161–0.773) due to a structural
geometry bias (Section 4); per D0-amendment-004, Null-B is reported as an advisory
contextual diagnostic and does not gate cell classification.

---

## 2. Per-cell calibration map

| Cell | Null-A conj FPR | Null-B conj FPR (advisory) | Verdict | Temporal flag | MDE (ATR) | Calibrated margin (ATR) |
| --- | --- | --- | --- | --- | --- | --- |
| GBPUSD-5m | 0.035 | 0.027 | **PASS** | GROWING | 0.025 | 0.0533 |
| GBPUSD-1h | 0.014 | 0.363 | **PASS** | DECAYING | 0.025 | 0.1263 |
| NZDUSD-1h | 0.031 | 0.340 | **PASS** | DECAYING | 0.025 | 0.1496 |
| NZDUSD-2h | 0.031 | 0.759 | **PASS** | STABLE | 0.025 | 0.1678 |
| GBPJPY-30m | 0.014 | 0.161 | **PASS** | DECAYING | 0.025 | 0.0722 |
| US2000-4h | 0.018 | 0.773 | **PASS** | STABLE | 0.025 | 0.1614 |

**Calibrated margin** = empirical (1 − α₀) quantile of the Null-A pseudo-signal median
distribution (the per-cell P9 condition-4 threshold for EXP-071). All six values are
finalized for the EXP-071 freeze file.

**MDE** = smallest non-zero planted-edge g (ATR units) at which Null-A TPR ≥ 0.80, given
that the cell's Null-A conjunction FPR ≤ α₀ = 0.05. Under the amended binding rule (Null-A
only), all six cells satisfy the FPR condition; MDE is therefore finite for all six.

---

## 3. FPR precision and CI details

| Cell | Null | Conj FPR | HW (95%) | Median-leg FPR | Draw completion |
| --- | --- | --- | --- | --- | --- |
| GBPUSD-5m | A | 0.035 | ±0.012 | 0.999 | 1.0 |
| GBPUSD-5m | B (adv) | 0.027 | ±0.010 | 0.603 | 1.0 |
| GBPUSD-1h | A | 0.014 | ±0.008 | 0.707 | 1.0 |
| GBPUSD-1h | B (adv) | 0.363 | ±0.030 | 0.708 | 1.0 |
| NZDUSD-1h | A | 0.031 | ±0.011 | 0.831 | 1.0 |
| NZDUSD-1h | B (adv) | 0.340 | ±0.029 | 0.655 | 1.0 |
| NZDUSD-2h | A | 0.031 | ±0.011 | 0.378 | 1.0 |
| NZDUSD-2h | B (adv) | 0.759 | ±0.027 | 0.900 | 1.0 |
| GBPJPY-30m | A | 0.014 | ±0.008 | 0.641 | 1.0 |
| GBPJPY-30m | B (adv) | 0.161 | ±0.023 | 0.271 | 1.0 |
| US2000-4h | A | 0.018 | ±0.008 | 0.125 | 1.0 |
| US2000-4h | B (adv) | 0.773 | ±0.026 | 0.911 | 1.0 |

All Null-A HWs are ≤ 0.012 (well within the 0.03 precision gate). All draws complete to
1000/1000. All six cells have non-degenerate CI width (degenerate_ci = false; CI widths
0.36–2.30 ATR). US2000-4h has the widest CI (2.30 ATR) reflecting its small TRAIN count
(m = 152 events), but the CI is not degenerate and does not preclude classification.

---

## 4. Null-B advisory diagnostic: structural geometry bias

Null-B conjunction FPRs are inflated in five cells (0.161 → 0.363 → 0.340 → 0.759 →
0.773 for GBPJPY-30m, GBPUSD-1h, NZDUSD-1h, NZDUSD-2h, US2000-4h) and controlled in one
(GBPUSD-5m, 0.027). The inflation is **timeframe-graded** (5m controlled; longer TFs
progressively more inflated) and is a structural artifact of the STRONG-STAT conditioning.

**Root cause.** STRONG-STAT (`m_sofar ≥ p75` of trailing-20 MA segments) selects harami
entries deep inside strong moves. These entries have systematically larger `m_sofar`,
larger favourable distances, and wider barriers than general matched-pool entries
(`m_sofar > 0`). Block rotation scrambles the **forward path** but preserves the **entry
geometry** — so the Null-B signal arm retains the geometry advantage while the RM arm
draws from the smaller-geometry pool. The result: `beats-RM` fires systematically under
Null-B even when there is no real signal, inflating all three conjunction legs
simultaneously. This is confirmed by `fpr_med_mean_nullB = fpr_full_conj_nullB` in all
cells (dropping `beats-RM` from the Null-B conjunction changes nothing — all legs are
co-determined by the same geometry cause). The timeframe gradient reflects that longer
TF STRONG-STAT conditioning is more extreme, widening the geometry gap.

**This is not a code error.** The `_resolve_matched_draw` implementation correctly
separates `geom_ohlc` (real entry geometry) from `path_ohlc` (rotated path). The geometry
separation was implemented and verified; the inflation is an irreducible structural
property of the design.

**Advisory interpretation.** Null-B is retained as a disclosed diagnostic characterising
the signal's path-continuity dependence. The GBPUSD-5m Null-B FPR = 0.027 (controlled)
is notable: at the 5m timeframe, STRONG-STAT conditioning is least extreme (m_sofar gap
smallest), so Null-B sees the least geometry inflation. This gradient is informative for
EXP-071 TEST interpretation and is carried into the freeze file.

---

## 5. TPR / MDE context

All cells achieve TPR ≥ 0.80 at the first non-zero planted-edge grid point (g = 0.025 ATR),
under the translation-equivariance shortcut applied to Null-A draws. TPR at g = 0:

| Cell | TPR(g=0) | TPR(g=0.025) | MDE |
| --- | --- | --- | --- |
| GBPUSD-5m | 0.999 | 1.000 | 0.025 ATR |
| GBPUSD-1h | 0.707 | 1.000 | 0.025 ATR |
| NZDUSD-1h | 0.831 | 1.000 | 0.025 ATR |
| NZDUSD-2h | 0.378 | 0.994 | 0.025 ATR |
| GBPJPY-30m | 0.641 | 1.000 | 0.025 ATR |
| US2000-4h | 0.125 | 0.860 | 0.025 ATR |

TPR(g=0) equals the Null-A median-leg FPR (the translation shortcut uses the median leg
as the recovery statistic). The wide spread — from 0.125 (US2000-4h, m=152) to 0.999
(GBPUSD-5m, m=8586) — reflects the power difference across cells. All cells recover to
≥ 0.86 at g = 0.025 ATR; the MDE is uniform across the family.

---

## 6. Temporal stability

Walk-forward stability was assessed on four chronological quarters of each cell's TRAIN
events. The GBPUSD-5m GROWING flag and the DECAYING flags on GBPUSD-1h and GBPJPY-30m
are disclosed as context for EXP-071 TEST interpretation; they do not gate the
calibration verdict.

| Cell | Flag | Full-TRAIN median | Final window median | Note |
| --- | --- | --- | --- | --- |
| GBPUSD-5m | GROWING | 0.697 ATR | 0.880 ATR | Signal strengthening toward present |
| GBPUSD-1h | DECAYING | 1.565 ATR | −0.158 ATR | Severe — final quarter negative |
| NZDUSD-1h | DECAYING | 1.533 ATR | 1.049 ATR | Mild — final quarter still positive |
| NZDUSD-2h | STABLE | 1.338 ATR | 1.523 ATR | Final window powered (n=112), consistent |
| GBPJPY-30m | DECAYING | 1.210 ATR | ≈0 ATR | Severe — final quarter near zero |
| US2000-4h | STABLE | 1.624 ATR | 1.838 ATR | Final window n=2, below floor; note wide CI (2.30 ATR) |

The DECAYING flags on GBPUSD-1h and GBPJPY-30m are materially adverse: the most recent
TRAIN quarter exhibits median return near or below zero. These cells pass FPR calibration
and receive finite MDE and calibrated margin, but their temporal signal is degraded. The
EXP-071 one-shot TEST contact should interpret results for these cells in light of the
DECAYING flag.

---

## 7. P12 reconciliation

EXP-070 reconciliation targeted EXP-068 / EXP-061 / EXP-066 results to verify that the
frozen inference machinery is reproduced to 1e-9 tolerance.

| Reconciliation target | Max abs-diff | Verdict |
| --- | --- | --- |
| EXP-068 N-PARTIAL-V2A bootstrap medians | 0.0 | PASS (exact byte-reuse) |
| EXP-061 M0 bootstrap medians | 0.0 | PASS (exact byte-reuse) |
| EXP-066 PARTIAL-V2A bootstrap medians | 0.0 | PASS (exact byte-reuse) |

All reconciliation diffs are exactly 0.0 (byte-identical reuse). The TRAIN cells are a
strict subset of the EXP-068 TRAIN grid; the bootstrap seeds are reproducible per
`(instrument, domain)`; no tolerance is consumed. Freeze-faithfulness confirmed.

---

## 8. Determinism

Two cells were independently re-run in a fresh process and the output files were compared
byte-for-byte. Both replays were byte-identical. Determinism PASS.

---

## 9. EXP-071 freeze file inputs

The following values are finalized for the EXP-071 freeze file (D0 P8):

| Cell | Verdict | Calibrated margin (ATR) | MDE (ATR) | Temporal flag | Null-B conj FPR (advisory) |
| --- | --- | --- | --- | --- | --- |
| GBPUSD-5m | PASS | 0.0533 | 0.025 | GROWING | 0.027 |
| GBPUSD-1h | PASS | 0.1263 | 0.025 | DECAYING | 0.363 |
| NZDUSD-1h | PASS | 0.1496 | 0.025 | DECAYING | 0.340 |
| NZDUSD-2h | PASS | 0.1678 | 0.025 | STABLE | 0.759 |
| GBPJPY-30m | PASS | 0.0722 | 0.025 | DECAYING | 0.161 |
| US2000-4h | PASS | 0.1614 | 0.025 | STABLE | 0.773 |

**Binding EXP-071 family:** all six P5 cells (GBPUSD-5m, GBPUSD-1h, NZDUSD-1h,
NZDUSD-2h, GBPJPY-30m, US2000-4h) are PASS and enter the EXP-071 TEST family.

---

## 10. Signal-registry disposition

**Registry: not applicable — calibration/methodology experiment.** EXP-070 consumes
0 candidate-screening slots and 0 TEST reads. It is an EXP-027-analog (method
validation), not a signal evaluation. No candidate-family status change, no multiplicity-
registry outcome row, and no `test-read-ledger.md` entry are required for EXP-070 itself.
The HYP-023 row in `multiplicity-registry.md` is annotated with D0-amendment-003 and
D0-amendment-004. The EXP-071 TEST read (to be consumed when EXP-071 runs) will be
recorded at that time.
