# Experiment: EXP-045 — Phase 011 Track B Per-Cell Exit Training (37-Cell COVERED Grid)

## Question

This is the Phase 011 Track B measurement (`CF-AVWAP-001/PI-EXIT`,
design §5.4/§6; registered Track B, 0 slots, 0 TEST reads; opened by **G1
CLOSED 2026-06-11**, adjudication 2 of 2 in `G1-gate-review.md`):

> For each of the **37 COVERED cells** (EXP-044 `coverage_map.csv`), which of
> the two predeclared exit families — **FH (fixed-horizon)** and
> **MAD-band-target** — is tunable on TRAIN under the n-neighbour stability
> plane, what is the selected parameter θ\*, and does the cell qualify for
> the candidate portfolio (tunable AND stability floor P4)? Is the resulting
> membership set large enough to authorize Track C (G2 composition rule P5:
> ≥5 member cells spanning ≥3 instruments)?

This is a **measurement / selection experiment**, not a hypothesis test of
market edge: the binding inference happens later, once, at Track C (one-shot
TEST read). Per design §7.4, a small or empty membership set is a valid
result (G2 fail → FOUNDATION_NON-TUNABLE, no TEST read spent).

## Exploratory question (precise)

Per cell c (37 cells) and family f ∈ {FH, MAD}:

1. Net per-event TRAIN expectancy curve `score_f(θ)` over the predeclared
   grid.
2. Stability plane `S_f(θ)` = mean of `score_f` over the 3-point
   neighbourhood (k = 1), interior θ only.
3. Tunability (design §6): the **endpoint rule first** — endpoint stability
   scores are computed on their truncated (2-point) neighbourhoods, and if
   any endpoint's stability strictly exceeds every interior stability score
   the family is non-tunable (`endpoint_argmax`: the optimum lies on or
   beyond the grid edge, and extending the grid would be tuning); then
   separation `max S − median S > 1 × SE_f` (interior θ) **and** split-half
   agreement (each chronological-half θ\* within ±1 grid step of full-TRAIN
   θ\*). Endpoints are never θ\*-eligible.
4. Cell exit = the tunable family with the higher `S_f(θ\*_f)`; membership iff
   additionally `S(θ\*) ≥ +1 × SE` (P4).
5. G2 readout: membership count and instrument span vs P5.

## Background and binding constraints

- **Grid of record**: the **37 COVERED cells** from
  `python/experiments/EXP-044/results/coverage_map.csv` (G1 leg (ii)). The
  13 NOT_COVERED cells and JP225-2h are excluded with record and consume
  nothing. Dependency gate: hard-fail unless EXP-044 `run_metadata.json`
  records CALIBRATION_DELIVERED and the coverage map yields exactly 37
  COVERED cells.
- **Entry frozen**: baseline AVWAP-line arm/trigger
  (`generate_avwap_events` defaults — bit-for-bit the EXP-043/044
  substrate). No entry parameter is touched (Track A0 removed; design §11).
- **All selection constants are G0-frozen** (D0-predeclarations.md): FH grid,
  MAD grid P6, k = 1, the 1×SE separation multiplier, the P4 floor, the P5
  composition rule, the P2 cost model. **Nothing in this experiment may tune,
  extend, or re-derive any of them**; no grid extension after curves are
  seen; no post-result cost iteration.
- **TRAIN-only**: F01 file-order TRAIN rows (identical loader convention and
  source-identity binding as EXP-043/044). The TEST stratum and the final-30%
  global holdout are never loaded, counted, or used. Membership is decided
  with zero TEST contact.
- **Per-event unit**: each baseline bounce event (pyramid events included as
  independent positions — EXP-028/029 convention) is one position; per-event
  net return is the unit of all scores. Never a per-bar metric.

## Exit-family definitions (predeclared)

Both families open at the event trigger: position in the regime direction at
the trigger bar's completed real `Close`. All returns are direction-signed
log returns in bps on real domain `Close` prices.

**Family 1 — FH(H)**: exit at the completed close H domain bars after the
trigger bar. Grid H ∈ {2, 3, 4, 6, 8, 11, 16, 23} (near-geometric — integer
bars force consecutive ratios 1.33–1.50 around the design's ≈√2 target;
neighbourhood widths are therefore only approximately proportionally uniform
across the grid; design §5.4).
Interior (θ\*-eligible): {3, 4, 6, 8, 11, 16}.

**Family 2 — MAD-band-target(m)**: favorable target = `avwap_at_trigger ±
m × band_spread_at_trigger` (bull/bear; spread and AVWAP frozen at trigger —
the HYP-003/HYP-004-R completion framework with the multiplier as the swept
exit parameter). Exit at the **first** completed bar whose `Close` is at or
beyond the favorable target, **or** the first completed bar confirming the
opposite MA(20,50) regime (trend-change leg, structural constant), whichever
comes first. The trend-change leg is **strictly after** the trigger bar: an
opposite confirmation coinciding with the trigger bar does not exit the
event (the conservative reading; the event then runs to its target, the
next opposite confirmation, or TRAIN end). No stop at the adverse target; no other exit. Grid m ∈
{0.5, 0.7, 1.0, 1.4, 2.0, 2.8, 4.0, 5.7} (P6). Interior:
{0.7, 1.0, 1.4, 2.0, 2.8, 4.0}.

**Unfinished events (both families)**: an event whose exit bar would fall
beyond the last completed TRAIN bar is **force-closed at the last completed
TRAIN bar's close** (financing accrued through that bar), flagged
`forced_close`, and included in the score — exclusion would bias against
long-duration exits. Per-cell forced-close counts are reported per θ; a
θ whose forced-close fraction exceeds 20% in a cell is recorded as a
disclosure on that grid point (not excluded — the stability plane handles
degraded points by averaging).

## Net return definition (frozen P2 cost model)

`net_e(θ) = signed_log_bps(trigger_close → exit_close) − RT_i −
financing_i × elapsed_calendar_days(trigger_close_time, exit_close_time)`
with the CONSERVATIVE RT and financing rates from D0 P2 (17-instrument
table; EURUSD 3.0 RT / 0.6 financing etc.), identical in structure to
EXP-030/033. No slippage model beyond RT; no sizing; equal weight per event.

## SE definition (predeclared here; the one open operational detail)

`SE_f` (used in both the separation rule and the P4 floor) = the
**regime-cluster bootstrap standard error** (frozen EXP-027 resampling
structure: regime clusters within direction strata, 1000 resamples,
`seed_for` determinism) of the cell's per-event TRAIN net mean **at the
full-TRAIN interior stability argmax θ\*_f** of that family. One SE per
cell×family; computed after the curve, used only in the tunability/floor
checks (it does not re-rank θ).

## Family comparison and tie-breaks (predeclared)

- Cell exit = tunable family with the higher `S_f(θ\*_f)`.
- Exact tie, or both tunable with equal scores: **FH wins** (simpler family,
  fewer moving parts).
- One family tunable → it is the cell exit (subject to P4 for membership).
- Neither tunable → cell **NON_TUNABLE**, excluded from the portfolio,
  recorded with both families' failure reasons.

## Scope Boundaries

- **Cells**: the 37 COVERED cells (a partial 17×3 grid; e.g. BTCUSD
  contributes only its 2h cell, AUDUSD only 2h, USTEC only 4h). The
  authoritative list is read from `coverage_map.csv` at run time, never
  hard-coded.
- **Data**: F01 TRAIN 1-minute rows → 1h/2h/4h domain bars
  (`min_coverage=0.90`, P7) → frozen baseline events. Source-identity
  binding against the EXP-043 boundary record; per-cell regenerated event
  counts asserted against EXP-043 `power_statement.csv`.
- **Time range**: TRAIN stratum only.
- **Global holdout (mandatory exclusion)**: the final 30% of each
  chronologically ordered source file is never loaded, inspected, emitted,
  plotted, counted, or used in any capacity. The TEST stratum (last 30% of
  the analysis slice) is likewise untouched.
- **Look-ahead**: exits scan strictly forward from the trigger bar using
  completed closes only; targets/AVWAP/spread are frozen at trigger; no
  information after each bar's close enters any exit decision.
- **Real-price discipline**: all returns on real domain `Close`; no
  synthetic prices anywhere.
- **Exclusions**: any TEST or holdout contact; any entry-parameter change;
  grid extension or re-ranking after curves are seen; stops/sizing/risk
  overlays; cross-instrument pooling in any selection statistic; per-cell
  significance claims (Track D objects); the 13 NOT_COVERED cells and
  JP225-2h; 5m; cost-model iteration; E1–E5 exit families (out of scope this
  phase, design §4).

## Success / Failure Criteria

This is a deliverable-criterion measurement (like EXP-043/044):

- **TRAINING_DELIVERED (Evidence FOR)**: every one of the 37 cells receives
  a complete record — both families' score curves, stability planes,
  tunability verdicts with reasons, the selected exit (or NON_TUNABLE), the
  P4 membership verdict — plus the membership-set G2 readout
  (`G2_COMPOSITION_MET` iff ≥5 member cells spanning ≥3 instruments, P5) and
  a passing determinism replay. The experiment succeeds by producing the
  honest map, whatever the membership count.
- **Evidence AGAINST — none defined at the substrate level**: a small or
  empty membership set is the FOUNDATION_NON-TUNABLE *phase* path (G2,
  operator/governance act), not an experiment failure.
- **Inconclusive**: any cell's record incomplete (e.g. event-count
  consistency gate failure, non-determinism) — hard-fail conditions that
  stop the run rather than degrade it silently.

Honest prior (not a target): thin 4h cells (32–86 events) have wide SEs, so
the 1×SE separation and P4 floor will be hard to clear there; the EXP-044
MDE map (32–128 bps at 4h) says only large per-event edges are resolvable in
those cells. A membership set concentrated in 1h/2h is the expected shape.

## Complexity Budget

- Max statistical tests: **2** (regime-cluster bootstrap SE per cell×family;
  split-half θ\* agreement check). No p-values, no CIs as binding objects —
  selection only.
- Max visualisations: **5** (per-cell FH stability-plane grid; per-cell MAD
  stability-plane grid; selected-exit / membership map 17×3 with excluded
  cells hatched; S(θ\*) vs SE scatter by domain (P4 floor line);
  membership-composition summary with the G2 readout).
- Max new code modules: **1 experiment-local helper** under
  `python/experiments/EXP-045/code/` (exit simulation + stability-plane +
  selection logic). Reuse of EXP-043/044 loader/scaffolding code by copy or
  import preferred; **no new or modified `python/src/xen/` module**.

## Metric Denominators and Zero-Baseline Behavior

- `score_f(θ)` denominator: the cell's reportable event count at that θ
  (all baseline TRAIN events; forced-close events included). Never bars.
- Stability `S(θ)`: unweighted mean of the 3 neighbourhood scores (each
  already a per-event mean); endpoints contribute to neighbourhoods of
  interior points but are never θ\*-eligible.
- All scores are net bps per event (absolute differences vs the 0 baseline
  implicit in net expectancy); no percentage-over-zero metrics anywhere.
- Split-half halves: events ordered by `trigger_close_time`, split at the
  median event (first half gets the extra event when odd). A half with <10
  events in a cell makes that family's split-half check fail closed
  (non-tunable, reason `split_half_underpopulated`), never silently pass.

## Data Requirements

Read-only upstream artifacts:

- `python/experiments/EXP-044/results/coverage_map.csv` +
  `run_metadata.json` (dependency gate: CALIBRATION_DELIVERED, exactly 37
  COVERED cells);
- `python/experiments/EXP-043/results/power_statement.csv` and the EXP-043
  `boundaries` record (event-count consistency + source-identity binding);
- D0 P2 cost table (transcribed as frozen constants, with the EURUSD 3.0
  RT correction);
- 1-minute source files under `data/timebars/`, F01 TRAIN-sliced before any
  domain-bar construction.

### Expected Output Files

```text
python/experiments/EXP-045/results/
- exit_selection.csv      # per cell: family verdicts, θ*, S(θ*), SE, membership, reasons
- score_curves.csv        # per cell × family × θ: net mean, n_events, forced_close_frac, S(θ)
- split_half.csv          # per cell × family: full/half θ*, agreement flag
- membership.csv          # member cells with selected exit; G2 readout row
- run_metadata.json       # gates, seeds, determinism, counts, G2_COMPOSITION_MET
python/experiments/EXP-045/plots/   # ≤5 per the budget
```

## Suggested Direction

One pass per cell: load TRAIN bars once per instrument, regenerate the
frozen events, precompute per-event exit outcomes for **all** grid points of
both families in a single forward scan (exits are deterministic given the
bars — no resampling in the curve), then bootstrap only the SE at θ\*. The
heavy object is the per-event exit scan; vectorize the FH leg (pure index
offsets) and keep the MAD/trend-change leg an explicit bounded forward scan
(genuinely sequential semantics). Determinism replay on two predeclared
cells. Compute is far below EXP-044's.
