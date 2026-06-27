# Analysis Plan: Experiment EXP-046

## Objective

Determine, on TRAIN data only, whether any of 6 non-baseline one-at-a-time
entry-parameter variants (`/ALPHA` α ∈ {0.0, 0.375, 1.0}; `/MA-DOMAIN`
(fast,slow) ∈ {(10,25), (40,100), (60,150)}; baseline α=0.75, MA=(20,50) as
anchor row) raises gross per-event expectancy at H=8 domain bars above the
frozen per-cell cost floor by ≥1×SE, with sign robustness at H ∈ {4,16}, in
≥5 cells over ≥3 instruments of the 37-cell COVERED grid. Every threshold is
a ratified D0 predeclaration; this plan adds no new tests, thresholds, or
metrics.

## Methodology

### Step 1: Variant event generation + integrity layer

- **Method**: For each variant × cell: aggregate TRAIN 1-minute rows to the
  domain (frozen conventions; 2h `min_coverage=0.90`), generate AVWAP bounce
  events via the parameterized `xen.avwap` (P8 gate green first), record
  event count and a determinism hash (second generation pass, hash
  equality).
- **Why this method**: the substrate machinery is frozen and validated
  (EXP-043 readiness, Phase 011 regression suite); only α/MA inputs vary.
- **Simpler alternative considered**: none simpler exists; event generation
  is the experiment's substrate.
- **Assumptions**: source files chronologically ordered (VAL-001 rev. 3 /
  VAL-003 validated); TRAIN slice = first `int(int(0.7N)·0.7)` file-order
  rows (EXP-045 F01 pattern, no full-file sort), sortedness re-asserted on
  the collected slice.
  - **Temporal structure**: events ordered by trigger `CloseTime`; events
    whose H=16 evaluation window would cross `train_end_ts` are excluded
    from all three horizon metrics for that cell×variant (one population
    per cell×variant across horizons; prevents TEST leakage through the
    forward window and horizon-dependent membership).
  - **Cross-view alignment**: single data view; no cross-view joins.
  - **Real-price outcomes**: domain-bar real Close prices only.
- **Expected output**: `events_summary.csv` — variant, cell, n_events,
  n_evaluable, n_regimes_evaluable (cluster-count disclosure for reading the
  Step 3 SE), determinism_pass (full-frame equality of a second generation
  pass — events and regimes), events_digest (audit fingerprint over
  trigger_idx/time, direction, regime_id, anchor_idx).

### Step 2: Gross per-event expectancy at reference horizons

- **Method**: per cell×variant, direction-signed gross log-return in bps
  from event trigger close to the close H ∈ {4, 8, 16} domain bars later
  (the EXP-045 gross-proxy convention); per-event mean per horizon.
- **Why this method**: exit-agnostic, identical to the Phase 011 gross
  proxy → the baseline row reconciles directly against EXP-045.
- **Simpler alternative considered**: single-horizon gross (H=8 only) —
  rejected by D0: sign robustness at H=4/16 is a frozen clearance leg.
- **Assumptions**: per-event means over non-i.i.d., overlapping-window
  events — acceptable because no significance claim is made; overlap and
  clustering are absorbed descriptively by the Step 3 SE.
- **Expected output**: `gross_table.csv` — variant × cell × horizon mean
  (bps), n.

### Step 3: Bootstrap SE at H=8 (descriptive)

- **Method**: the frozen EXP-027 regime-cluster bootstrap resampling layer,
  applied to each cell×variant's H=8 per-event gross returns; report the
  bootstrap SE of the mean. No p-values, no CIs as verdicts.
- **Why this method**: the clearance margin is defined in units of this SE
  (D0 P5); reusing the frozen machinery avoids a new estimator and respects
  event clustering better than an i.i.d. SE.
- **Simpler alternative considered**: i.i.d. SE — rejected: known
  anti-conservative under event clustering (R1.2/EXP-032 lesson), and the
  EXP-027 layer is already frozen and calibrated on these populations.
- **Assumptions**: EXP-044 found a per-cell N1>N2 FPR offset — irrelevant
  here (no null-calibrated inference is run; SE is a noise yardstick only,
  disclosed in results).
- **Known limitation (disclosed, not corrected — the 1×SE margin multiplier
  is a frozen D0 value)**: the regime-cluster bootstrap preserves
  within-regime dependence but not overlap correlation *between* adjacent
  short regimes; where typical regime spans are shorter than H=8 bars the SE
  is potentially anti-conservative. `n_regimes_evaluable` is reported per
  cell so results.md can read cluster counts alongside any clearance.
- **Expected output**: SE column on the H=8 rows of `clearance_table.csv`
  (kept beside the floor and margin it parameterizes).

### Step 4: Cost floor and mechanical clearance

- **Method**: `floor = RT_i + financing_i × days(8,d)`, days = 1/3, 2/3,
  4/3 on 1h/2h/4h, P2 table verbatim. CLEAR iff (i) gross(H=8) ≥ floor +
  1×SE, (ii) gross(H=4) > 0 ∧ gross(H=16) > 0, (iii) n_evaluable ≥ 30,
  (iv) determinism_pass. Else NO_CLEAR, or BELOW_FLOOR when (iii) fails.
- **Why this method**: it is the ratified rule; nothing is estimated.
- **Simpler alternative considered**: n/a (frozen).
- **Expected output**: `clearance_table.csv` — variant × cell verdict,
  margin (gross − floor − SE, bps); per-variant rollup: clearing-cell
  count, distinct instruments, and the mechanical ordering keys
  (clearing-set size, instrument diversity, Σ margins).

### Step 5: Baseline reconciliation (integrity anchor; blocking)

- **Method**: three blocking legs per cell, all on the regenerated baseline
  events. (1) Event-count identity vs the EXP-043 realized counts (full
  population). (2) FH net mean at θ ∈ {4, 8, 16} vs the persisted EXP-045
  `score_curves.csv` values, recomputed under **EXP-045's own conventions
  identically on both sides** (full population, forced exits clipped to the
  last TRAIN bar, exact fractional-day financing) — this anchors the event
  population and the return arithmetic to the only persisted external
  reference. (3) Internal cross-check of the binding gross/evaluable path:
  the screen-side `evaluable_mask` + `gross_at_horizons` means must match an
  independently indexed recomputation on the same events (validates the
  exact population and code path the clearance rule reads, which has no
  external anchor). Tolerance 1e-9 bps on all numeric legs.
- **Expected output**: `reconciliation.csv` + pass/fail flag; computed and
  passed **before** any non-baseline row is interpreted. Any integrity
  failure (reconciliation or determinism) suppresses the mechanical G1
  readout entirely (`INCONCLUSIVE_INTEGRITY_FAIL`).

## Visualisations

1. **Margin heatmap — `/ALPHA` axis** (variants × 37 cells, gross(H=8) −
   floor − SE in bps, clearance cells outlined) — where, if anywhere, the
   exponent lever creates headroom.
2. **Margin heatmap — `/MA-DOMAIN` axis** (same layout) — same question for
   the detector-scale lever.
3. **Horizon-robustness panel**: per variant, scatter of gross(H=4) vs
   gross(H=16) for cells passing leg (i) — shows which near-clearances fail
   on sign robustness.
4. **Event-count map**: variants × cells n_evaluable with the 30-event
   floor marked — locates BELOW_FLOOR attrition (MA changes move event
   rates).

## Interpretation Guide

- If ≥1 non-baseline variant clears in ≥5 cells over ≥3 instruments —
  **ENTRY_GROSS_VIABLE**: that lever materially raises gross edge above the
  cost floor on TRAIN; Phase 013 rebuilds the net machinery on the winning
  variant (selected-on-TRAIN disclosure attached).
- If no variant meets the threshold — **ENTRY_GROSS_FLAT**: the
  entry-parameter lever cannot pay frozen costs on this substrate;
  programme pivots to substrate revision (operator pre-commitment). Partial
  signal (e.g. 3 clearing cells, or positive margins concentrated at 4h
  where SEs are ~41 bps) is still FLAT — the threshold does not soften.
- Integrity failures (reconciliation mismatch, determinism failures,
  wholesale event-floor collapse) — **inconclusive**: fix and rerun; no
  result is read from a failed-integrity grid.
- Context for reading margins: baseline gross is positive in 31/37 cells
  but ~5–7 bps short of net viability (EXP-045); a clearing variant must
  beat baseline gross by roughly that much plus the SE guard. 4h cells
  (32–86 events, MDE 64+ bps) clearing on noise is the main false-positive
  channel — the SE term and sign-robustness legs are the predeclared
  guards, and any 4h-only clearance pattern is reported with that caveat.
- G1-adjudication caveats (carried verbatim into results.md and the
  checkpoint gate review; none alters the frozen rules):
  1. *Cross-cell noise correlation.* Per-cell clearance noise is positively
     correlated across instruments (shared dollar/regime moves; correlated
     currency pairs and index CFDs), so the P6 composition threshold's
     false-positive rate is higher than an independence reading suggests —
     especially if a clearing set concentrates in one correlated bloc (e.g.
     JPY crosses, or US indices). Clearing-set composition is read with
     this in mind; no cross-cell correlation estimation is run (out of
     scope).
  2. *Calendar-day floor approximation.* The frozen P4 `days(8,d)` formula
     understates wall-clock financing for holds spanning weekends/closures;
     the bias is largest for 4h index-CFD cells (a weekend can add ~1–3
     days' financing ≈ 1–3 bps the floor omits). A clearing index cell
     whose margin is within a few bps of zero carries this caveat
     explicitly.
  3. *SE overlap limitation* (Step 3): clearances in cells with few
     evaluable regimes relative to event count are read with the
     anti-conservative-SE caveat.

## Complexity Check

- Statistical tests: 0 binding / 0 budget (bootstrap SE descriptive)
- Visualisations: 4 / 4
- New modules: 1 / 1 (sweep utilities; `xen.avwap` parameterization extends
  the existing module)

## Implementation Safety Constraints (for experiment-developer)

- TRAIN slice per EXP-045 F01: file-order row slice from Parquet metadata
  counts; never `.sort()` over the full file; re-assert sortedness on the
  collected slice; holdout/TEST rows never enter the scan engine's output.
- One event population per cell×variant: horizon evaluability (H=16 window
  inside TRAIN) decided once, before any horizon metric.
- Direction-signed bps returns from real domain-bar closes; no cost or
  financing arithmetic on returns — the floor is a standalone comparison
  constant per cell.
- Zero/low events: `n=0` rows carry no means (nulls, not NaN propagation);
  `n < 30` rows compute descriptive means but are BELOW_FLOOR.
- Bounded loops: 7 variants × 37 cells outer loop under `tqdm`; bootstrap
  iteration count = the frozen EXP-027 setting; domain bars and events are
  small after aggregation — collect bounded frames only.
- Vectorization safe for horizon returns (fixed-offset joins on bar index
  *within* a single chronologically sorted domain frame is acceptable here
  because the offset is defined in domain bars of one view — no cross-view
  bar-index alignment); event generation remains the sequential frozen
  generator, never vectorized.
- Determinism: second generation pass per cell×variant, hash compare;
  bootstrap seeded (fixed seed constant).
- Plot inputs are the bounded result tables; no reloads for plotting.
