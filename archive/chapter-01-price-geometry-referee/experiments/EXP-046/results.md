# Results: Experiment EXP-046

## Summary

The entry-side gross screen is **FLAT**. Across the 6 non-baseline OAT
entry-parameter variants (`/ALPHA` α ∈ {0.0, 0.375, 1.0}; `/MA-DOMAIN`
(10,25)/(40,100)/(60,150)) on the 37-cell COVERED grid, no variant comes
close to the predeclared composition threshold of ≥5 clearing cells over ≥3
instruments: the best non-baseline variants (ma_40_100, alpha_1.0) clear 3
cells each, and ma_40_100 spans only 2 instruments. Integrity is clean —
reconciliation 259/259 legs pass at 1e-9 bps, determinism 259/259, audit
PASS with zero critical findings — so the mechanical G1 readout
**ENTRY_GROSS_FLAT** stands on a fully valid grid. Neither the tick-volume
exponent nor the regime-detector MA scale is a lever that lifts the AVWAP
bounce gross edge over frozen CONSERVATIVE costs at any meaningful breadth.
Per the operator pre-commitment, this routes the programme to substrate
revision; G1 itself is adjudicated in the Phase 012 checkpoint.

## Detailed Findings

### 1. No variant approaches the composition threshold

- **Observation**: clearance partition is 14 CLEAR / 235 NO_CLEAR /
  10 BELOW_FLOOR over 259 cell×variant rows. Per-variant clearing counts
  (`variant_rollup.csv`): baseline 3 cells / 3 instruments; alpha_1.0 3/3;
  ma_40_100 3/2; alpha_0.0 2/2; alpha_0.375 2/2; ma_60_150 1/1; ma_10_25 0.
- **Evidence**: `clearance_table.csv`, both margin heatmaps
  (`margin_heatmap_alpha.png`, `margin_heatmap_ma.png`).
- **Interpretation**: the threshold (≥5 cells, ≥3 instruments) is missed by
  a wide margin everywhere — this is not a near-miss FLAT. No non-baseline
  variant even exceeds the baseline's own 3 clearing cells, so the levers do
  not add breadth over the substrate they perturb.

### 2. Clearances concentrate in the predeclared false-positive channel

- **Observation**: 12 of 14 CLEAR rows are 4h cells; 8 of 14 are US index
  CFDs (US2000 ×6, US500 ×2, DE30 ×2 of the remainder). US2000-4h clears
  under five different variants including baseline.
- **Evidence**: CLEAR rows in `clearance_table.csv`; 4h SEs on clearing
  cells run 6–28 bps with n as low as 33–66 evaluable events.
- **Interpretation**: this is exactly the pattern the analysis plan flagged
  as the main false-positive channel (small 4h samples, large SEs, shared
  index-bloc noise). It argues that even the 14 observed clearances
  overstate any real edge; it cannot soften FLAT and is carried as a caveat
  to G1, not a result.

### 3. Variant effects on gross level are small and breadth-free

- **Observation**: per-variant H=8 cross-cell medians sit in a narrow band
  around zero — baseline −1.15 bps; alpha_0.0 −2.35; alpha_0.375 −1.27;
  alpha_1.0 −1.62; ma_10_25 −0.54; ma_40_100 −0.16; ma_60_150 +0.28.
  Positive-gross cell counts at H=8 range 12–19 of 37.
- **Evidence**: `gross_table.csv`; note event populations differ across
  variants by construction, so these are level comparisons against the
  floor, not matched contrasts.
- **Interpretation**: shifting α across its full range or scaling the
  detector 2× in either direction moves the typical cell by ~1–2 bps —
  an order of magnitude short of the ~5–20 bps floors. The gross shortfall
  is a property of the bounce substrate, not of its entry parameterization.

### 4. Slow detectors lose eligibility rather than gain edge

- **Observation**: all 10 BELOW_FLOOR rows are MA variants on 4h cells —
  ma_60_150 (8 rows, n = 12–28) and ma_40_100 (2 rows, n = 13–17).
  ma_60_150 also posts the highest median gross (+0.28 bps) and the only
  2h clearance besides ma_40_100's (US500-2h, margin +5.74 bps, n = 33).
- **Evidence**: `events_summary.csv`, `event_count_map.png`.
- **Interpretation**: slowing the regime detector mildly improves per-event
  quality while collapsing event counts below the 30-event floor exactly
  where holding costs are highest — the lever trades breadth for a small
  quality gain and cannot generate the required composition.

### 5. Sign robustness rarely binds; the floor+SE leg does

- **Observation**: only one row passes the margin leg but fails the
  H=4/H=16 sign leg (ma_40_100 USDCHF-4h, margin +1.69 bps). Eleven rows
  sit within 5 bps below a zero margin.
- **Evidence**: `horizon_robustness.png`; near-miss list from
  `clearance_table.csv`.
- **Interpretation**: the binding constraint is the gross level against
  floor + 1×SE, not horizon fragility — consistent with a substrate whose
  edge is simply too small, rather than one with horizon-specific shape.

## Hypothesis Verdict

**REFUTED** (mechanical G1 readout: **ENTRY_GROSS_FLAT**).

The hypothesis required ≥1 non-baseline variant clearing in ≥5 cells over
≥3 instruments. Best observed: 3 cells. All integrity legs passed
(reconciliation 259/259 at 1e-9 bps against EXP-043 counts and the EXP-045
FH anchor; determinism 259/259), so the FLAT readout is read from a valid
grid. Under the ratified Phase 012 pre-commitment, the entry-parameter
lever is exhausted and the programme pivots to substrate revision. Final
adjudication occurs in the Phase 012 checkpoint `G1-gate-review.md`.

## Limitations

G1-adjudication caveats, carried verbatim from the analysis plan (none
alters the frozen rules):

1. *Cross-cell noise correlation.* Per-cell clearance noise is positively
   correlated across instruments (shared dollar/regime moves; correlated
   currency pairs and index CFDs), so the P6 composition threshold's
   false-positive rate is higher than an independence reading suggests —
   especially if a clearing set concentrates in one correlated bloc (e.g.
   JPY crosses, or US indices). Clearing-set composition is read with this
   in mind; no cross-cell correlation estimation is run (out of scope).
2. *Calendar-day floor approximation.* The frozen P4 `days(8,d)` formula
   understates wall-clock financing for holds spanning weekends/closures;
   the bias is largest for 4h index-CFD cells (a weekend can add ~1–3 days'
   financing ≈ 1–3 bps the floor omits). A clearing index cell whose margin
   is within a few bps of zero carries this caveat explicitly — here that
   covers DE30-4h under alpha_1.0 (margin +0.85 bps) and the other
   sub-5-bps index clearances.
3. *SE overlap limitation* (Step 3): clearances in cells with few evaluable
   regimes relative to event count are read with the anti-conservative-SE
   caveat (`n_regimes_evaluable` is reported per row in
   `events_summary.csv`).

Additional limitations:

- Bootstrap SEs are descriptive; no significance claims are made anywhere.
- Event populations differ across variants by construction (no matched
  variant-vs-baseline contrast was scoped); Finding 3's medians are level
  summaries only.
- TRAIN-only: nothing here characterizes TEST behavior; 0 TEST reads were
  made.

## Alternative Explanations

- The OAT grid samples each lever at 3 points around the baseline; a finer
  or interacting (`/ALPHA`×`/MA-DOMAIN`) grid could in principle find a
  pocket the OAT sweep misses. Given the ~1–2 bps median movement across
  the full sampled range of both levers, a hidden interaction large enough
  to close a 5–20 bps gap is implausible, and combinations were explicitly
  excluded at D0.
- The 14 clearances could reflect genuine pockets of edge (notably US2000)
  rather than noise; caveats 1–3 cut against this, and under the frozen
  rule it is irrelevant to G1 either way. Any future substrate work can
  treat US2000-4h's repeated clearance as hypothesis-generating only.

## Recommended Next Steps

1. **Substrate revision (Phase 013, per the operator pre-commitment)** —
   close Phase 012 via `G1-gate-review.md` with ENTRY_GROSS_FLAT and design
   the substrate pivot as a new phase/scope, not as an extension of the
   AVWAP-bounce entry grid.
2. **Optional new EXP if a revised substrate emerges**: carry forward the
   EXP-046 harness (loader gates, reconciliation pattern, clearance
   mechanics) unchanged — it reproduced external anchors at 1e-9 bps and is
   cheap to re-point at a new event generator.
