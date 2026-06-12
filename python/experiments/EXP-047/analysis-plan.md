# Analysis Plan: Experiment EXP-047

`CF-AVWAP-001/DIAG-007` — `/ANCHOR` move-size diagnostic. All binding values
are frozen at Phase 013 D0 (RATIFIED 2026-06-12): `ATR_period=14`, `k=1.0`,
`M=2`, ≥30 TRAIN-event floor, ≥5 cells over ≥3 instruments composition. This
plan restates them; nothing here is data-derived or tunable.

## Objective

Determine, on TRAIN data only and gross of all costs, whether the
ATR-prominence significant-pivot anchor (`/ANCHOR`) materially shifts the
available per-event favorable move-size (MFE) distribution rightward
relative to the frozen running-extreme baseline anchor and the frozen
per-cell cost floor, in enough cells (P6 composition) to justify an
in-family `/ANCHOR` viability phase — versus confirming the move-size
ceiling is intrinsic to the AVWAP family. One falsifiable question, two
mechanical sub-steps (readiness, then distribution comparison). Not a
viability test, not a net screen, no inference claims.

## Methodology

### Step 0: P8 regression gate (precondition, no TRAIN read)

- **Method**: extend `python/tests/test_avwap_band_param.py`-convention
  suite with (a) baseline-anchor fixture invariance at default parameters
  (bit-for-bit vs frozen fixtures), (b) `/ANCHOR` look-ahead-safety and
  determinism smoke tests on synthetic fixtures, (c) the running-extreme
  fallback path. All green before any TRAIN row is read.
- **Why**: P8 is the data-contact gate; a leaking or non-deterministic new
  anchor would manufacture a spurious MFE shift.
- **Expected output**: green pytest run recorded in the experiment log /
  run metadata.

### Step 1: Event generation, both anchors, 51 cells

- **Method**: per instrument (17) load the 1-minute file lazily, sort by
  `CloseTime`, slice analysis set (first 70%) then TRAIN (first 70% of
  analysis, 1-minute-row `train_end_ts` boundary), aggregate to 1h/2h/4h
  via frozen `xen.bar_aggregator` conventions, and run
  `xen.avwap.generate_avwap_events` twice on the identical TRAIN bars:
  baseline defaults (running-extreme) and `/ANCHOR` (P1: ATR(14)
  prominence, `k=1.0`, most-extreme tie-break, running-extreme fallback
  with `anchor_fallback` tag).
- **Why this method**: reuses the frozen substrate machinery; the only
  varied element is the anchor pivot-selection rule, which is exactly the
  registered branch under test.
- **Simpler alternative considered**: generating only `/ANCHOR` events and
  reusing persisted baseline outputs — rejected: both arms must be produced
  by the same code path on the same slice for a clean comparison, with the
  baseline arm reconciled against persisted anchors instead (Step 2).
- **Assumptions**: temporal ordering by `CloseTime`; sequential stateful
  generation (no look-ahead); deterministic replay. These are the P2/P8
  checks, verified, not assumed.
- **Expected output**: per cell × anchor event tables (trigger time/price,
  direction, lifetime end, `anchor_fallback`), event counts, fallback rate.

### Step 2: Baseline reconciliation (integrity anchor, blocking)

- **Method**: on the 37-cell COVERED grid, regenerated baseline event
  counts must equal the EXP-043 realized counts exactly; baseline gross
  figures must reconcile with the persisted EXP-045/EXP-046 anchors per the
  Phase 012 baseline-row convention (float-precision tolerance).
- **Why**: proves the parameterised-anchor refactor did not perturb the
  frozen substrate; any discrepancy is a blocking integrity finding that
  suppresses the G1 readout.
- **Expected output**: reconciliation table, all-pass required.

### Step 3: G1a readiness (EXP-020 analog, per cell, `/ANCHOR` arm)

- **Method**: per cell, mechanical checks — 0 invariant violations
  (EXP-020 invariant set, anchor-adapted: e.g. anchor at or before
  regime-confirmation bar, anchor price equals a realized segment Low/High,
  arm precedes trigger, event ordering strictly increasing), determinism
  replay drift 0 (regenerate and diff), look-ahead safety (anchor
  selectable from bars ≤ confirmation bar; ATR causal — verified
  structurally plus a truncation probe on a sample of regime changes:
  regenerating with the input truncated at the confirmation bar must select
  the same anchor), ≥30 TRAIN `/ANCHOR` events.
- **Why**: a new anchor is a new event definition; readiness is the hard
  admissibility gate (design §7).
- **Expected output**: `readiness_map.csv` — per cell READY/NOT_READY with
  failing check; NOT_READY cells excluded from Step 4 with record.

### Step 4: Move-size distributions (per READY cell × anchor)

- **Method**: per event, gross, direction-signed, real domain-bar prices:
  - **MFE** = max favorable excursion from the trigger close over the event
    lifetime (lifetime = to next MA(20,50) trend-change or analysis-set
    end, EXP-022 boundary; unfinished events flagged `lifetime_censored`
    and counted, with the censored fraction disclosed). The lifetime path
    includes the entry point (excursion 0), so MFE is floored at 0;
  - **MAE** = matching max adverse excursion over the same window, floored
    at 0 (standard excursion convention);
  - per cell × anchor: median, IQR, bootstrap SE of the median (frozen
    EXP-027 resampling layer, ≥10,000 resamples, fixed seed, descriptive);
  - **matched-control MFE** (context, descriptive only): same MFE statistic
    on matched non-event bars under the EXP-021/027 convention adapted to
    the lifetime statistic — candidates share the event's `regime_id`
    (fixing instrument/domain/regime direction), are not trigger bars, sit
    outside a 6-bar exclusion window around any trigger; per event, up to 5
    controls selected by nearest anchor age then nearest timestamp, minimum
    3 for the event to contribute. Known limitation (disclosed): controls
    share the event's regime sub-segment, so a volatility artifact confined
    to exactly the anchor-selected sub-periods shifts controls too — the
    panel is a descriptive context read carried to the checkpoint, never a
    diagnostic gate.
- **Why this method**: the diagnostic asks the ceiling question — how big
  is the available move — which is horizon-independent; medians + IQR +
  bootstrap SE are the distribution-free location/spread summary already
  validated in this programme.
- **Simpler alternative considered**: fixed-horizon expectancy (Phase 012
  form) — rejected at design level: already measured flat; not the ceiling
  question.
- **Assumptions**: events within a cell are not i.i.d. (overlap, regime
  clustering); the bootstrap SE is therefore descriptive, never a
  significance claim — consistent with the 0-binding-tests budget. The two
  anchor arms are different event populations; the comparison is a
  location shift, not a paired test (unpaired-population honesty, design
  §7).
- **Expected output**: `move_size_distributions.csv` — per cell × anchor:
  n, median_MFE, IQR_MFE, SE_median_MFE, median_MAE, SE_median_MAE,
  censored fraction, fallback rate, matched-control median MFE.

### Step 5: Cost-floor reference and per-cell classification (P4/P5)

- **Method**: per cell, `floor_i,d = RT_i + financing_i × days(L_i,d, d)`
  with the frozen Phase 011 P2 CONSERVATIVE table verbatim; `L_i,d` = the
  cell's median lifetime holding time in domain bars, computed per anchor
  arm. The **binding floor for the P5 check is the maximum of the two
  arms' floors** (conservative: a `/ANCHOR` lifetime shift in either
  direction can only hold or raise the bar, never soften leg 2); both
  arms' floors are tabulated. `days(L, d) = L × hours(d)/24`. The floor is
  a reference line, never subtracted.
  Then the mechanical P5 classification per READY cell — SHIFTED_VIABLE iff
  all of:
  1. `median_MFE(/ANCHOR) ≥ median_MFE(baseline) + 1 × SE_diff`, where
     `SE_diff` is the bootstrap SE of the median difference (independent
     resampling of the two unpaired arms, difference of medians per
     replicate, fixed seed);
  2. `median_MFE(/ANCHOR) ≥ 2 × floor_i,d` (M=2);
  3. `Δ median_MAE ≤ Δ median_MFE` (Δ = `/ANCHOR` − baseline);
  4. n(/ANCHOR) ≥ 30;
  5. determinism replay passes.
- **Why**: this is the ratified D0 rule, restated; the G1b phase statistic
  is the composition of SHIFTED_VIABLE cells (≥5 cells over ≥3
  instruments), adjudicated at checkpoint level, not inside the experiment.
- **Expected output**: `shift_classification.csv` — per cell: all five leg
  states, verdict, floor, margins; plus a phase-input summary row count by
  instrument (no pooling for verdicts).

## Visualisations (4 / 4 budget)

1. **Per-domain MFE-median vs floor panels** (3 panels, one figure):
   baseline and `/ANCHOR` medians per cell with SE whiskers, `floor` and
   `2×floor` reference lines — the headline ceiling-vs-floor read.
2. **MFE-shift vs MAE-shift scatter** (per cell, colored by domain): shows
   leg 1 vs leg 3 jointly — whether favorable shifts are erased adversely.
3. **Readiness / fallback-rate map** (17×3 grid heatmap): READY state and
   `anchor_fallback` rate per cell — a high fallback rate means `/ANCHOR`
   collapses toward baseline (itself an informative read).
4. **Matched-control context panel**: per-cell `/ANCHOR`-vs-baseline median
   MFE difference alongside the matched-control difference — volatility
   sub-period check.

## Interpretation Guide

- If the SHIFTED_VIABLE set spans ≥5 cells over ≥3 instruments →
  **ANCHOR_MOVE_VIABLE**: anchor placement is a real move-geometry lever;
  route to an in-family viability phase (a ceiling, not an edge — capture
  and net viability remain unproven).
- If the composition threshold is not met → **ANCHOR_MOVE_FLAT**: the
  move-size ceiling is intrinsic to the AVWAP family on this anchor class;
  route to a new candidate family. A complete, routable outcome.
- High fallback rates with near-identical distributions mean `/ANCHOR`
  degenerates to baseline — reported as supporting FLAT, not as a defect.
- If matched-control MFE shifts about as much as event MFE, the apparent
  shift is a volatility-sampling artifact — disclosed; the P5 rule still
  binds mechanically, and the context read is carried to the checkpoint.
- Integrity failures (Step 0/2 red, determinism drift, readiness collapse
  across most of the grid) → **Inconclusive**: the mechanical count is
  suppressed; fix-and-rerun is a governance decision, not an analyst one.

Disclosed caveats for the checkpoint reader:
- P5 leg 1 (1×SE_diff) is a noise guard, not a materiality margin; the sole
  materiality gate is leg 2 (M=2 × binding floor). A `leg1_borderline` flag
  marks cells where |ΔMFE − SE_diff| < 0.25×SE_diff, since the bootstrap SE
  estimator itself carries ~10–15% sampling variability at n≈30–50 and
  near-boundary leg-1 calls are seed-brittle.
- 14 of 51 cells have no external reconciliation anchor (outside the
  EXP-043 power statement / EXP-046 baseline rows); their baseline
  integrity rests on code-path identity plus the P8 suite. Listed in
  `run_metadata.json` (`unreconciled_cells`).
- The P6 composition threshold is the inherited Phase 011/012 breadth
  convention, not re-powered for this diagnostic; the output includes
  non-binding sensitivity flags at (≥4 cells, ≥2 instruments) and (≥3, ≥2)
  so the operator can judge robustness of the G1b readout.

## Complexity Check

- Statistical tests: 0 binding / 0 budget (bootstrap SEs descriptive; G1
  counts mechanical)
- Visualisations: 4 / 4
- New modules: 1 / 1 (move-size diagnostic utilities; anchor
  parameterisation inside existing `xen.avwap`; P8 tests in
  `python/tests/`)

## Data-View Comparison Considerations

- **Alignment**: all temporal logic by `CloseTime` on domain bars; events
  carry trigger timestamps; never bar-index alignment across views.
- **Unequal populations**: the two anchors emit different event counts and
  timings by construction; report n per arm everywhere; no paired framing.
- **Denominators / zero baselines**: per-event denominators with n always
  reported; medians undefined for empty arms are not computed (cells
  reported NOT_READY/BELOW_FLOOR); floors strictly positive; no
  ratio/percentage metrics.
- **Implementation safety** (for `experiment-developer`):
  - lazy Polars scans; sort by `CloseTime`; slice analysis set then TRAIN
    before collection; never materialise rows past `train_end_ts`;
  - event generation is genuinely sequential — keep the explicit streaming
    loop in `xen.avwap`; do not vectorise the anchor state machine;
  - MFE/MAE per event may be vectorised (window max/min over the lifetime
    slice) — causally safe because the excursion window ends at the
    lifetime boundary and is evaluated retrospectively per completed event;
  - bounded iteration: 17 instruments × 3 domains × 2 anchors outer loop
    under `tqdm`; bootstrap loops fixed at the predeclared resample count
    with fixed seeds;
  - plotting consumes the bounded per-cell summary tables produced by the
    analysis pass — no reloads or regeneration for plots;
  - concise orchestration-level logging; helpers return data.
