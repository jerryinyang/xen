# Results: Experiment EXP-032 — One-Shot Holdout Confirmation of Package B (EURUSD-4h, FH H\*=12, all_legs)

Interpretation written from the persisted artifacts only (`holdout_verdict.csv`,
`holdout_events.csv`, `analysis_fh_nets.csv`, `null_calibration.csv`,
`frozen_holdout_manifest.json`, `run_metadata.json`) — no holdout row was re-read.
Audit: PASS (0 critical, 0 warnings). Registry `CF-AVWAP-001/HOLDOUT-B`.

## Summary

The programme's single sanctioned holdout read is spent, and the binding verdict is
**HOLDOUT_INCONCLUSIVE** (descriptive label **INCONCLUSIVE_SPANS_ZERO**). On the 27
holdout-stratum EURUSD-4h events, Package B delivered a net per-event expectancy of
**+20.60 bps** (two-sided 95% CI [−0.39, +42.15]), with one-sided bootstrap
p = 0.029 ≤ 0.05 — but the one-sided 95% lower bound (+2.71 bps) did not clear the
predeclared calibration margin m_cell = 4.32 bps. Under the locked mechanical rule,
this is neither confirmation nor refutation: the point estimate is positive and the
p-gate passed, but the lower bound is not far enough above zero to survive the
measured small-n anti-conservatism of the frozen bootstrap at this cell structure
(uncorrected null FPR 0.0715). This is precisely the predeclared power-limited
outcome the scope anticipated if the true effect sat materially below the EXP-037
TEST point estimate. The TEST-stratum evidence (net +40.56 bps) stands but is
permanently non-upgradable; the holdout is now contaminated-by-disclosure for any
EURUSD-4h event-level claim.

## Detailed Findings

### 1. The binding cell missed CONFIRMED on the margin, not the p-value

- **Observation**: ci_low_1s = +2.71 bps > 0 but ≤ m_cell = 4.32 bps; boot_p =
  0.029 ≤ 0.05. Both conditions were required; one failed.
- **Evidence**: `holdout_verdict.csv` (n = 27); `null_calibration.csv` — at the
  holdout's exact cluster layout (16 direction×regime clusters), the frozen
  bootstrap's uncorrected dual rule had a measured null FPR of 0.0715; the margin
  restores 0.050. Plot `holdout_verdict.png` shows the full geometry.
- **Interpretation**: had the programme used the uncalibrated rule
  (`ci_low_1s > 0` AND p ≤ 0.05), this read would have "confirmed" — at a measured
  false-positive rate above nominal. The margin did exactly the job R1.2 designed
  it for. The honest statement is: positive evidence, insufficient to clear a
  properly calibrated bar at n = 27.

### 2. Effect attenuation, not reversal, out of sample

- **Observation**: holdout mean +20.60 bps vs analysis-era mean +32.87 bps
  (n = 39) at the identical FH(12)/all_legs estimand; per-event signs split 13
  positive / 14 negative with the mean carried by large winners (max +133.7,
  min −98.2 bps).
- **Evidence**: `analysis_fh_nets.csv`, `holdout_events.csv`; plot
  `analysis_vs_holdout.png` (context only, no inference). Holdout dispersion is
  visually comparable to the analysis era's (analysis-era σ_w ≈ 30.0, σ_b ≈ 57.8
  bps from `null_calibration.csv`).
- **Interpretation**: the out-of-sample point estimate landed between the EXP-038
  baseline scale (+24.27) and zero, well below the EXP-037 TEST point (+40.56) —
  consistent with ordinary winner's-curse attenuation of a selected cell rather
  than with the edge being absent. This is speculation-adjacent context, not
  evidence: the CI spans zero and the binding read is spent.

### 3. Non-binding companion: the FH(12) exit again dominates the BTC exit

- **Observation**: on the identical 27 events, the BTC-exit (Package-A) net point
  estimate is +2.35 bps vs +20.60 bps for the binding FH(12) cell (27/27 BTC
  events completed).
- **Evidence**: `holdout_verdict.csv` companion columns; plot `fh_vs_btc_exit.png`
  (labeled NON-BINDING). Decomposition of the binding cell: gross +25.26 − RT 3.00
  − financing 1.67 = net +20.60 bps.
- **Interpretation**: directionally consistent with EXP-031/033/037 — the
  trend-change exit is a drag at long horizons on this population. Predeclared as
  never promotable: this cannot ground any Package-A claim or future holdout read.

### 4. Predeclared power expectation exceeded; verdict still margin-bound

- **Observation**: the holdout stratum held 27 binding events vs the predeclared
  ≈15–18 expectation (disclosure-only deviation; H2 correctly ran regardless).
- **Evidence**: `frozen_holdout_manifest.json` counts; audit.md Info 1.
- **Interpretation**: even with ~50% more events than expected, the cell could not
  clear the margin — the limiting factor is per-event dispersion (σ on the order
  of 60–70 bps per event against a +20 bps mean), not an unluckily thin stratum.

## Hypothesis Verdict

**INCONCLUSIVE** (binding: `HOLDOUT_INCONCLUSIVE`; descriptive:
`INCONCLUSIVE_SPANS_ZERO`).

Per the predeclared Interpretation Guide: the holdout is spent without
confirmation. The Phase 008 TEST-stratum evidence for Package B stands as the
final in-sample word but is **permanently non-upgradable** — there is no second
holdout read for `CF-AVWAP-001` Package B under any circumstance. Routing follows
the REFUTED path for resource purposes (Phase 008 design §9 / Phase 009 design §8):
return to characterisation, Tier C.

## Mandatory disclosures (R1)

- **Ex-post reportability (F04):** the binding estimand conditions on
  `reportable_event`, which depends on post-entry regime evolution and the series
  truncation point — a live trader cannot identify the binding population at entry
  time. In this stratum the filter happened to bind nothing (27 events pre- and
  post-reportability), but the estimand definition still carries this
  external-validity caveat.
- **Calibration fidelity (F05):** the margin's null transports the analysis-era
  variance scale (σ_b 57.85, σ_w 29.98 bps) onto the holdout cluster layout. This
  caveat is load-bearing only for a CONFIRMED verdict; the outcome is INCONCLUSIVE,
  and plot 3 shows holdout dispersion comparable to the analysis era's, so it does
  not alter the reading.

## Limitations

- n = 27 events in a single instrument/domain cell; per-event dispersion ~60–70
  bps means the design could only confirm effects well above ~+25 bps net — the
  predeclared power statement anticipated exactly this INCONCLUSIVE zone.
- The one-shot design forbids any sensitivity analysis, alternative horizon, or
  cost variant on holdout data; nothing beyond the single predeclared cell can be
  or was computed.
- The boot_p (0.029) and ci_low_1s come from the same frozen bootstrap whose
  uncorrected FPR at this structure measured 0.0715 — the raw p-value should not
  be quoted as standalone evidence without the margin context.
- Holdout era (2025-05 → 2026-05 triggers) is a single contiguous regime sample;
  attenuation vs the analysis era cannot be decomposed into regime shift vs
  selection effect from one read.

## Alternative Explanations

- **True effect ≈ +20 bps:** the analysis-era TEST estimate (+40.56) was an upward
  fluctuation of a genuinely positive but smaller edge; the holdout read is
  exactly what that world produces. Indistinguishable, by design, from:
- **True effect ≈ 0 with a lucky stratum:** a zero-mean process with this cluster
  dispersion produces ci_low_1s > 0 with measured probability ≈ 0.07; the margin
  rule exists because this alternative is not negligible at n = 27.
- The data cannot separate these; the programme's predeclared answer is the
  verdict label itself.

## Recommended Next Steps

(New scopes only; nothing extends EXP-032. The holdout is spent — none of these
may touch holdout rows for EURUSD-4h event-level claims.)

1. **Phase 009 retrospective and Tier-C routing** per Phase 008 design §9: close
   the checkpoint with the spent-shot outcome recorded; route to Stage-C branches
   (HYP-001 line) for the next characterisation phase.
2. **Optional analysis-set-only follow-up:** cTrader per-bar parity of the FH exit
   (the Phase 009 design names this as the next step only under CONFIRMED; if the
   programme ever wants FH-exit machinery validated for other uses, it must be
   scoped on analysis data as its own experiment).
3. **Multiplicity registry update:** record `CF-AVWAP-001/HOLDOUT-B` as SPENT /
   INCONCLUSIVE in `docs/signal-registry/multiplicity-registry.md` (documentation
   stage).
