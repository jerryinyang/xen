# Analysis Plan: Experiment EXP-045

## Objective

For each of the **37 COVERED cells** (EXP-044 `coverage_map.csv`), train the
two G0-frozen exit families on TRAIN — **FH(H)**, H ∈ {2,3,4,6,8,11,16,23},
and **MAD-band-target(m)**, m ∈ {0.5,0.7,1.0,1.4,2.0,2.8,4.0,5.7} (P6) —
score each grid point by net per-event expectancy under the frozen P2
CONSERVATIVE cost model, select θ\* per family by the **n-neighbour
stability plane** (k = 1, interior-only, design §6), apply the tunability
rule (1×SE separation + split-half agreement) and the **P4 membership floor**
(S(θ\*) ≥ +1×SE), and produce the candidate-portfolio membership set with
the **G2 readout** (P5: ≥5 member cells over ≥3 instruments).

Every selection constant is G0-frozen; this plan only operationalizes. The
experiment is selection/measurement — no binding hypothesis test, no
p-values as decision objects, 0 TEST reads. A thin or empty membership set
is a valid deliverable (design §7.4).

## Reused vs. new components

| Component | Source | Status in EXP-045 |
| --- | --- | --- |
| F01 TRAIN load + source-identity binding + domain-bar construction (P7) | EXP-043/044 `code/` | reused by copy/import, unchanged |
| Frozen baseline event generation + per-cell count consistency gate | `xen.avwap` defaults + EXP-044 pattern | reused unchanged |
| Regime-cluster bootstrap resampling, `seed_for` | EXP-027 lineage / `xen.referee_calibration` | reused unchanged (SE only — no CI, no permutation) |
| Per-event exit simulation (both families), stability plane, tunability/membership classifier | new | the experiment-local helper (1 module budget) |

No new or modified `python/src/xen/` module.

## Methodology

### Step 1: Dependency gates and substrate (per cell)

- **Method**: hard-fail unless EXP-044 `run_metadata.json` records
  CALIBRATION_DELIVERED and `coverage_map.csv` yields exactly **37**
  COVERED cells; load the cell list from the file (never hard-coded).
  Per instrument: F01 TRAIN slice with the EXP-043 boundary assertions
  (file name, total/TRAIN rows, TRAIN-end timestamp). Per cell: build
  domain bars (P7), regenerate baseline events, assert event count equals
  EXP-043 `power_statement.csv` (hard-fail per cell on mismatch).
- **Why**: Track B must run on the certified, calibrated substrate;
  G1-excluded cells must be structurally unreachable.
- **Simpler alternative**: trust a hard-coded cell list — rejected
  (drift-unsafe; the artifact chain is the authority).
- **Output**: validated per-cell event/regime tables; gate confirmations in
  `run_metadata.json`.

### Step 2: Per-event exit simulation (single forward pass, both families)

- **Method**: per cell, one deterministic forward scan over TRAIN bars
  computes, for every event and every grid point:
  - **FH(H)**: exit index = trigger index + H (completed close). Pure index
    arithmetic — fully vectorizable (NumPy gather), causally safe because
    the exit rule uses no path information.
  - **MAD(m)**: favorable target = `avwap_at_trigger ± m ×
    band_spread_at_trigger` (frozen at trigger, direction-signed); exit at
    the first completed close at/beyond the target **or** the first
    opposite-regime confirmation bar, whichever is earlier. Implemented as
    an explicit bounded forward scan per event (genuinely sequential), with
    one optimization permitted because it is exactly causally equivalent:
    for each event, the first-crossing index over the monotone grid of
    targets can be found with a single pass recording running extremes —
    sample membership, exit bars, and semantics must be identical to the
    naive per-(event, m) scan (equivalence asserted on a fixture in tests).
    The trend-change bar per event is a precomputed `next opposite-regime
    start index` lookup (vectorized, from the regime table).
  - **Unfinished events**: force-close at the last completed TRAIN bar
    (flag `forced_close`); financing accrues through that bar. Per-(cell,
    family, θ) forced-close fractions recorded; >20% flagged as a
    disclosure on that grid point (scope rule — no exclusion).
  - **Net per event**: `signed_log_bps(trigger_close → exit_close) − RT_i −
    financing_i × elapsed_calendar_days(trigger_close_time,
    exit_close_time)` with the P2 constants (incl. the EURUSD 3.0 RT
    correction). Calendar days = exact fractional days from timestamps —
    matching EXP-033's convention.
- **Why**: one pass computes all 16 grid points per cell exactly; exits are
  deterministic, so no resampling belongs in the curve.
- **Simpler alternative**: rerun the scan per θ — equivalent but ~16× the
  work; rejected on efficiency with identical semantics required anyway.
- **Assumptions**: completed-close exit fills (no intrabar fills) — the
  same convention as every prior FH/lifetime experiment; conservative and
  consistent.
- **Output**: per-cell arrays `net[event, family, θ]`, exit metadata.

### Step 3: Score curves and stability planes

- **Method**: `score_f(θ)` = mean of `net[·, f, θ]` over all the cell's
  events (denominator = event count, never bars). `S_f(θ)` = unweighted
  mean of `score_f` over {θ−1, θ, θ+1} for **interior** θ only (endpoints
  feed neighbourhoods but are never θ\*-eligible). `θ\*_f` = argmax of
  `S_f` over interior points; deterministic tie-break to the **smaller** θ
  (fewer bars held / tighter target — lower financing exposure; fixed here
  before any curve is seen). Endpoint stability is additionally computed on
  truncated (2-point) neighbourhoods solely to operate the design-§6
  endpoint rule: if an endpoint's stability strictly exceeds every interior
  value, the family fails as `endpoint_argmax` (checked before all other
  tunability legs). Raw per-θ means in `score_curves.csv` are reported as-is
  for transparency (arithmetic mean, no trimming) and must not be
  interpreted point-by-point in thin cells — the stability plane and SE are
  the decision objects; an `interior` flag marks θ\*-eligibility.
- **Why**: exactly design §6; region averaging over a geometric grid.
- **Simpler alternative**: one-SE rule — explicitly superseded by design §6.
- **Output**: `score_curves.csv` (cell × family × θ: net mean, n_events,
  forced_close_frac, S(θ)).

### Step 4: SE, tunability, family selection, membership

- **Method**:
  - **SE_f**: regime-cluster bootstrap (1000 resamples, regime clusters
    within direction strata, `seed_for(EXP-045, instrument, domain,
    family, "se")`) standard error of the per-event net mean at θ\*_f —
    one SE per cell×family, per the scope's predeclared definition.
  - **Tunability** (fail-closed, reasons recorded, checked in this order):
    (a) endpoint dominance (truncated-neighbourhood endpoint stability >
    every interior stability) → `endpoint_argmax`;
    (b) separation: `max S − median S > 1 × SE_f` over interior θ, else
    `flat_plane`;
    (c) split-half: events split chronologically at the median event
    (first half gets the odd event); θ\* re-derived on each half must lie
    within ±1 grid step of full-TRAIN θ\*, else `split_half_disagreement`;
    a half with <10 events → `split_half_underpopulated` (fail).
  - **Cell exit**: tunable family with higher `S_f(θ\*_f)`; exact tie → FH.
    Neither tunable → NON_TUNABLE.
  - **Membership (P4)**: member iff cell has a selected exit **and**
    `S(θ\*) ≥ +1 × SE` of the leading family.
  - **G2 readout (P5)**: `G2_COMPOSITION_MET` iff ≥5 member cells spanning
    ≥3 distinct instruments. Reported as a readout for the gate review —
    the adjudication itself is a governance act, not this experiment's.
- **Why**: verbatim operationalization of §6 + P4 + P5; the only degrees of
  freedom (tie-breaks, split rule, fail-closed minima) are fixed here,
  pre-data.
- **Output**: `exit_selection.csv`, `split_half.csv`, `membership.csv`.

### Step 5: Determinism replay and metadata

Re-run two fixed cells end-to-end (GBPUSD-1h high-count, JP225-4h thin)
with identical seeds; assert identical score curves, SEs, verdicts, and that
**both** predeclared cells were actually replayed (hard-fail otherwise).
Note: the pipeline is structurally deterministic — the seeded bootstrap SE
is the only stochastic step — so the 2-cell replay is a regression check on
wiring, not the source of the determinism guarantee.
`run_metadata.json` records gates, seeds, per-cell headline, forced-close
summary, membership count/instrument span, `G2_COMPOSITION_MET`, and the
experiment verdict (TRAINING_DELIVERED iff all 37 records complete and the
replay passes).

## Visualisations (5 / 5 budget)

1. **FH stability-plane small-multiples** — S(θ) per cell with θ\* marked;
   the FH tunability read.
2. **MAD stability-plane small-multiples** — same for Family 2.
3. **Selected-exit / membership map (17×3)** — family + θ\* annotated;
   NOT_COVERED/JP225-2h hatched; NON_TUNABLE and floor-failures
   distinguished.
4. **S(θ\*) vs SE scatter by domain** with the P4 floor line S = SE — why
   cells passed/failed membership.
5. **Membership-composition summary** — member count by instrument/domain
   and the G2 readout headline.

## Interpretation Guide

- **TRAINING_DELIVERED**: all 37 cell records complete + determinism PASS.
  The membership set and G2 readout go to the gate review; if
  `G2_COMPOSITION_MET`, Track C scoping opens; if not, the phase path is
  FOUNDATION_NON-TUNABLE (operator/governance decision, no TEST spent).
- **Per-cell readings**: NON_TUNABLE and floor-failure are valid,
  expected outcomes — especially at 4h (wide SEs at 32–86 events; EXP-044
  MDEs 32–128 bps say only large edges are resolvable there). A
  1h/2h-concentrated membership is the predeclared honest prior.
- **No market-edge claim anywhere**: TRAIN-selected exits and membership
  are selection objects; the binding inference is Track C's single TEST
  read. Do not report TRAIN net means as evidence of tradability.
- **Inconclusive**: any incomplete cell record (gate failure,
  non-determinism) — these hard-fail the run rather than degrade silently.

**Predeclared interpretation caveats:**

1. **Selection bias on reported curves**: TRAIN net at θ\* is upward-biased
   as an estimate of out-of-sample net (winner's curse over 6 interior
   points × 2 families); the stability plane reduces but does not remove
   this. All downstream consumers get this caveat verbatim.
2. **Forced-close events** at long H / wide m compress late-TRAIN events'
   horizons; the disclosure threshold (>20%) marks affected grid points.
   If a cell's θ\* sits on a heavily-forced point, the split-half check is
   the guard (later half is most affected) — note, don't re-rank.
3. **SE at θ\* only**: the separation rule compares a max against a median
   using a single-point SE; this is the design's frozen rule, not an
   estimator choice open to improvement here. Direction of the bias:
   because S(θ\*) averages three adjacent θ values, its own sampling error
   is smaller than the per-event-mean SE used as the yardstick — the 1×SE
   separation and P4 floor are therefore **conservative** (fewer
   false-positive tunability/membership claims, more false negatives).
   Downstream consumers of tunability rates should account for this.
4. **DE30 disclosure (D0 P8, verbatim)**: DE30 truncated history — broker
   history ends 2026-01-16 (~5 months short); 70/30/holdout boundaries
   derive from its own realized timeline. Carried as a `disclosure` column
   on every row-level artifact containing DE30 rows, in
   `run_metadata.json`, and on the membership-map plot.

## Implementation Safety Constraints

- TRAIN-only F01 loading before any construction; TEST/holdout never enter
  the scan engine; chronological order asserted post-collect.
- Exits scan strictly forward from the trigger using completed closes;
  targets frozen at trigger; the MAD first-crossing optimization must be
  asserted equivalent to the naive scan on a fixture before any cell runs.
- Denominators are event counts; forced-close events included, flagged,
  never dropped; no per-bar metric anywhere.
- All randomness through `seed_for`; bootstrap is the only stochastic step.
- `tqdm` over the cell loop; helpers return data; plots from the bounded
  summary tables only; per-instrument 1-minute frame loaded once and freed.
- No grid extension, re-ranking, cost-value change, or selection-rule
  modification under any observed result — fail and stop instead.

## Complexity Check

- Statistical tests: **2 / 2** — regime-cluster bootstrap SE; split-half
  agreement check.
- Visualisations: **5 / 5** as listed.
- New modules: **1 / 1** experiment-local helper.

## Expected Output Files

```text
python/experiments/EXP-045/results/
- exit_selection.csv
- score_curves.csv
- split_half.csv
- membership.csv
- run_metadata.json
python/experiments/EXP-045/plots/
- fh_stability_planes.png
- mad_stability_planes.png
- exit_membership_map.png
- stability_vs_se.png
- membership_summary.png
```
