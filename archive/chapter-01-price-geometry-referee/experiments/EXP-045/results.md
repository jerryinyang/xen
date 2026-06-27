# Results: Experiment EXP-045

## Summary

Track B exit training delivered its full map — verdict **TRAINING_DELIVERED**
(all 37 cell records complete, determinism PASS, audit PASS) — and the map is
empty: **0 member cells** out of 37 (35 NON_TUNABLE, 2 FLOOR_FAIL),
`G2_COMPOSITION_MET = false` against the P5 rule (≥5 cells over ≥3
instruments). Under the frozen CONSERVATIVE cost model, neither exit family
exhibits a tunable, positive, stable net-expectancy plateau in any cell: net
medians sit at −5 to −7 bps at every grid point of both families, 20/37
cells are net-negative at all 16 grid points, and the only two cells passing
tunability carry **negative** plateaus (EURUSD-1h FH(3), S(θ\*) = −3.45 bps;
US500-2h MAD(1.0), S(θ\*) = −0.37 bps), which the P4 floor correctly
excludes. The design-§8.3 consequence is the **FOUNDATION_NON-TUNABLE**
phase path with **no TEST read spent** — that adjudication is a governance
act (G2 gate review), not this experiment's verdict; this report supplies
the readout.

## Detailed Findings

### 1. The membership set is empty because net cost exceeds gross edge, not because selection malfunctioned

- **Observation**: median net per-event expectancy is −5 to −7 bps at
  *every* grid point of both families (FH 2→23 bars; MAD 0.5→5.7). Only
  17/37 cells have even one net-positive grid point. A gross-proxy check
  (best net + RT) shows 31/37 cells would have a positive best point before
  round-trip costs — the few-bps gross bounce edge survives, and the frozen
  CONSERVATIVE costs (RT 3.0–16.0 bps + financing) consume it.
- **Evidence**: `score_curves.csv`; audit spot-check (EURUSD-1h FH(3)
  reproduced from raw data to full float precision); plots
  `fh_stability_planes.png`, `mad_stability_planes.png`.
- **Interpretation**: this extends the Phase 008/010 cost lesson to the full
  17-instrument universe and the new 2h domain with per-instrument-trained
  exits: exit training cannot manufacture net edge that gross does not
  contain. The failure is economic, not methodological.

### 2. Failure modes are the noisy-flat-plane signature, not a grid-design defect

- **Observation**: across 74 family-cells, `endpoint_argmax` fired 42 times
  and `flat_plane` 30 times; only 2 passed tunability. Endpoint dominance is
  side-mixed (FH: 12 low / 8 high; MAD: 11 / 11) — a wandering best point on
  a flat, mostly-negative surface, not a systematic "optimum beyond the
  grid on one side". The two tunable cells have coherent interior plateaus
  that simply sit below zero.
- **Evidence**: `exit_selection.csv` reason counts; audit recomputation
  (0 mismatches across all 74 classifications).
- **Interpretation**: the n-neighbour stability machinery behaved exactly as
  designed — it declined to select on noise. Had the one-SE rule of Phase
  008 been used instead, many of these cells would have "selected"
  something; the operational no-signal detection (design §6) is the feature
  doing the work here.

### 3. The 4h domain shows the only net-positive points, but at unverifiable noise levels

- **Observation**: the median best-grid-point net is +13.8 bps at 4h vs
  −2.0 (1h) and −3.4 bps (2h); the largest are US500-4h +76.7, US2000-4h
  +53.4, DE30-4h +46.7 bps — yet all three cells are NON_TUNABLE
  (`endpoint_argmax` or `flat_plane`). Bootstrap SEs at 4h reach ~41 bps.
- **Evidence**: `score_curves.csv`, `exit_selection.csv`;
  `stability_vs_se.png`.
- **Interpretation**: consistent with the EXP-044 power map (4h per-cell
  MDEs 32–128 bps): single-grid-point positives of this size at 32–86
  events are indistinguishable from noise, and the tunability rule
  correctly refuses to certify them. These points are **not** evidence of a
  trainable 4h edge; treating them as candidates would be exactly the
  winner's-curse error the plan's caveat 1 predeclares.

### 4. Deliverable integrity

- **Observation**: 100% of cells classified; 0 forced-close disclosure
  points (all exits resolved within TRAIN); split-half halves ≥16 events
  everywhere; both replay cells frame-identical; DE30 rows carry the P8
  disclosure verbatim; audit PASS with an exact independent recomputation
  of one cell and a full-table re-derivation of every verdict.
- **Audit caveats carried**: `agree=false` in `split_half.csv` is
  informative geometry, not a binding failure count (the binding reason may
  be endpoint/flat); 4h SEs make the separation rule nearly unpassable
  there by design.

## Hypothesis Verdict

**TRAINING_DELIVERED — with an empty membership set.** The predeclared
deliverable criterion is met (honest map, every cell classified,
determinism PASS). The substantive answer to the Track B question is
negative: on TRAIN, under frozen CONSERVATIVE costs, **no cell of the
37-cell grid has a tunable exit with a positive stable plateau**, in either
family. The G2 composition rule (P5) is not met; per design §8.3 the phase
path is **FOUNDATION_NON-TUNABLE with no TEST read spent** — to be
adjudicated in the gate review, with the multi-instrument portfolio claim
never reaching Track C.

## Limitations

- **Cost-model dependence**: every verdict is net-of-CONSERVATIVE costs
  (2× BASE) plus financing. The cost model is frozen and binding for this
  phase (D0 P2; no post-result iteration), but the conclusion is "not
  tunable *at these costs*", not "no gross structure exists" — finding 1's
  gross proxy shows the gross edge persists.
- **Conservative selection rules**: the 1×SE separation and P4 floor are
  conservative by construction (single-point SE vs an averaged stability
  score — plan caveat 3), so some true-but-small plateaus may have been
  rejected. At the observed −5 to −7 bps medians this cannot change the
  G2 outcome: the floor requires a *positive* plateau.
- **TRAIN-selected, TRAIN-scored**: even these (negative) values are
  upward-biased estimates of out-of-sample performance (winner's curse,
  plan caveat 1) — which makes the empty membership *more* credible, not
  less.
- **DE30** rows carry the truncated-history disclosure (D0 P8, verbatim in
  all artifacts).

## Alternative Explanations

- **A wider MAD/FH grid would find the optimum**: the mixed dominance sides
  and flat planes argue against a systematically truncated grid; and the
  grids are G0-frozen — extension after seeing curves is excluded as
  tuning. The endpoint failures are predominantly noise-wandering, not a
  directional drift.
- **A different cost model rescues membership**: possible at BASE (half the
  RT), but BASE is diagnostic-only by frozen predeclaration. A future phase
  could redesign the cost layer; within Phase 011 the CONSERVATIVE verdict
  is the binding one.

## Recommended Next Steps

1. **G2 adjudication** (governance, not an EXP): record G2 FAIL →
   **FOUNDATION_NON-TUNABLE** in the Phase 011 gate review; Tracks C and D
   never open; TEST budget remains 0 of ≤6 spent. Per design §9 the
   programme routes to `/ENTRY` exploration or substrate-level revision.
2. **New scope (future phase, operator option)**: gross-structure
   characterisation of the 4h positives (US500/US2000/DE30) at an honest
   power budget — only meaningful if a cheaper execution layer or a
   different entry (raising gross per event above the cost floor) is on the
   table first.
3. **New scope (future phase)**: `/ENTRY`, `/ALPHA`, `/MA-DOMAIN` —
   the deferred entry-side levers — are now the only untried route to
   raising gross per-event edge; Phase 011's contribution is that the
   exit-side lever is measured and exhausted on this substrate.
