# Experiment: EXP-024 — AVWAP Event-Edge Dissipation Decomposition

## Hypothesis

This is a **diagnostic** experiment with a predeclared two-way fork, not a single
falsifiable edge claim and not a qualification screen.

**Central question (per domain):** between EXP-021's fixed-horizon bounce reaction
(+3.8 / +9.1 / +37.6 bps on 5m / 1h / 4h) and EXP-023's ~0-to-negative *gross*
realized strategy expectancy (−0.563 to +0.137 bps), is the conditional event edge
lost to

- **fork (a) — a fixable holding/exit problem**: a bounded max-hold horizon captures
  materially more signed gross edge than holding the always-on baseline to its
  lifetime completion (target / trend-change), so a different exit could plausibly
  recover edge; **or**
- **fork (b) — entry/position dilution (wrong vehicle)**: every adequately powered
  bounded max-hold horizon carries too little per-event gross edge to justify a
  scoped bounded-hold remedy, so the always-on overlay is the wrong way to express
  this event.

The verdict is reported per domain with a predeclared primary domain, and
aggregated to a phase-level fork that gates Phase 005 Stage B (EXP-026 `/EXIT`).

## Question

When an AVWAP bounce carries real conditional reaction yet the always-on baseline
that trades it returns ~0 gross, where does the edge go — and could a different
*exit/holding* rule recover it, or is the *entry/position* itself too diluted?

## Scope Boundaries

- **Data Views**: 5m / 1h / 4h OHLC domain bars rebuilt deterministically from the
  first-70% 1-minute analysis slice (5m strict coverage; 1h/4h `min_coverage=0.90`),
  reproducing the EXP-020/021/022 domain construction exactly. AVWAP/band/event
  state is **reused** from EXP-020, not recomputed for signal purposes.
- **Reused upstream artifacts** (read-only):
  - `python/experiments/EXP-020/results/avwap_events.csv` — bounce events:
    `instrument, domain, regime_id, direction, is_pyramid_bounce, trigger_idx,
    trigger_time, trigger_close, favorable/adverse_target_at_trigger`, etc.
  - `python/experiments/EXP-022/results/lifetime_observations.csv` — per-event
    lifetime outcome: `outcome ∈ {favorable, adverse, trend_change, unfinished}`,
    `bars_to_completion`, `lifetime_bps`, `completion_idx`, `is_favorable`.
  - `python/experiments/EXP-021/results/reaction_observations.csv` — fixed horizons
    {1,3,6} for cross-check of the horizon curve at those points.
  - Modules: `xen.avwap`, `xen.bar_aggregator` (domain reconstruction only).
- **Parameters**:
  - Horizon grid (predeclared, unified across domains): `h ∈ {1,2,3,4,5,6,8,10,12,16,20,24}`
    completed domain bars after the trigger, plus the **full-lifetime hold**
    (trigger → `completion_idx`) as the always-on reference. The grid is fixed
    a priori and is **not** chosen from realized returns.
  - Direction-signed real-close gross return in bps (log convention, matching the
    EXP-021/022 `signed_log_bps` estimator): `10_000 × direction ×
    (log_close[trigger_idx+h] − log_close[trigger_idx])`, reportable only when
    `trigger_idx+h` lies inside the analysis slice.
  - Ratified-loose floors (frozen suite, reference thresholds only — the suite is
    not run here): 5m 0.5, 1h 2, 4h 8 bps.
  - Cost convention (secondary lens only): per-event round-trip cost via
    `xen.referee_calibration.cost_bps_for(instrument, domain)` (the frozen EXP-004/023
    cost), charged once per held move; used for attribution only, never for the
    primary fork.
  - Bootstrap CIs: regime-cluster bootstrap (resample `regime_id` clusters within
    each instrument×direction stratum), matching the EXP-021/022 AVWAP
    event-uncertainty convention — the analysis unit is the event and events cluster
    by regime, so a continuous-series block bootstrap does not fit the event-level
    estimand; ≥10,000 resamples, Holm-adjusted across the horizon grid.
  - Primary domain (predeclared): **5m** — largest reportable event count (16,249),
    giving the best resolution for the floor-clearance test. 1h and 4h reported in
    full; 4h (≈246 events) may resolve INCONCLUSIVE on coverage.
- **Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD (decomposition reported per
  instrument×domain×direction; fork verdict issued per domain).
- **Time range**: Full dataset with nested chronological split. First 70% = analysis
  set; final 30% = global holdout (never used). All events inherit the EXP-020
  analysis-set fence.
- **Global holdout**: The final 30% must not be loaded, inspected, or used. Bounded
  horizons use only analysis-set closes; an event with no real close at `trigger_idx+h`
  inside the analysis slice is **non-reportable at that horizon** (its N drops out),
  never extended into the holdout.
- **Look-ahead bias prevention**: returns use only closes at or after the trigger and
  no later than the evaluated horizon; AVWAP/targets are frozen at the trigger
  (EXP-020). No future information selects the horizon grid.
- **Real-price outcome discipline**: all returns are from **real domain OHLC closes**.
  AVWAP and MAD bands are reference lines used only to define events (upstream), never
  as P&L prices. No Heiken Ashi / Renko prices anywhere.
- **Exclusions**: the frozen qualification suite (no screen, no pass/fail verdict);
  cTrader generation; parameter/exit/detector tuning; the global holdout; any
  optimization that picks a horizon to maximize realized return; ALPHA/BAND
  sensitivity; EXP-025's line-S/R question (separate scope).

## Success / Failure Criteria

The "result" is the per-domain fork verdict under this predeclared rule. Let
`g(h)` be the per-domain mean direction-signed **gross** return at horizon `h`,
computed on the events reportable at `h` **and** carrying a completed (non-unfinished)
lifetime outcome; let `g_life` be the always-on full-lifetime mean recomputed on that
same per-`h` event set; let `floor_d` be the domain ratified-loose floor; let
`g*` = max over the grid of `g(h)`, at horizon `h*`, with block-bootstrap 95% CI.

- **Fork (a) — fixable holding/exit problem (per domain)** if BOTH:
  1. `g* ≥ floor_d` with the `h*` bootstrap **CI lower bound ≥ floor_d** after
     Holm adjustment across the horizon grid (the bounded-hold edge clears the
     floor with usable precision, not as a noise-selected peak); AND
  2. `g* − g_life(h*) ≥ margin_d`, where `margin_d = max(0.5 bps, 0.25 × floor_d)`
     (5m 0.5, 1h 0.5, 4h 2.0 bps) — the bounded hold beats the always-on lifetime
     hold by a material margin on the common event set.
- **Fork (b) — entry/position dilution (per domain)** if `g(h) < floor_d` at **every**
  grid horizon (even the best bounded hold cannot reach the loosest suite floor),
  i.e. condition (a.1) fails everywhere.
- **Inconclusive (per domain)** if neither (a) nor (b) resolves under the precision
  rule: reportable completed-event N below the EXP-021/022 minimum, or the `h*` CI
  half-width so wide that floor-clearance is indeterminate (CI straddles `floor_d`).

- **Phase-level fork (gates Stage B)**:
  - **(a)** if the primary domain (5m) is fork (a), **or** any domain is fork (a) →
    Stage B (EXP-026 `/EXIT`) is justified, scoped on the supporting domain(s).
  - **(b)** only if **all three** domains are fork (b) → Stage B is skipped;
    redirect per design §6 OVERLAY_WRONG_VEHICLE.
  - otherwise mixed/inconclusive → recorded; operator decides Stage B scoping.

All comparisons are **absolute bps differences against fixed floors** — no
percentage-improvement-over-zero-baseline ratio is computed (zero-baseline pitfall
avoided). Denominators are reportable-event counts, reported per horizon and per
outcome class.

## Complexity Budget

- Max statistical tests: 2 (per-horizon mean block-bootstrap CIs with Holm
  adjustment across the grid; trend-change-exit return CI). The fork itself is a
  predeclared threshold rule, not an additional NHST.
- Max visualisations: 4
  1. Per-domain horizon-decay curve `g(h)` with CIs, EXP-021 {1,3,6} cross-check
     points, the always-on `g_life` line, and the ratified-loose floor.
  2. Outcome-composition + holding-period (`bars_to_completion`) distribution per
     domain (favorable / adverse / trend_change / unfinished).
  3. Trend-change-exit `lifetime_bps` distribution per domain (does it cut winners
     or save losers).
  4. Cost-attribution (secondary): gross vs net horizon curve and lifetime, showing
     cost drag.
- Max new code modules: 1 (a small reusable horizon-return-grid helper if not
  already covered by EXP-021/022 machinery; otherwise 0).

## Data Requirements

Rebuild 5m/1h/4h domain bars from the first-70% 1-minute slice exactly as
EXP-020/021/022 did (deterministic; verify domain row counts reproduce EXP-020's
`analysis_metadata.csv`). Join EXP-020 events to the rebuilt domain close series by
`trigger_idx`; join EXP-022 lifetime outcomes by event key
(`instrument, domain, regime_id, trigger_idx`). Exclude unfinished lifetimes from
the always-on reference (as EXP-022). Report per-horizon reportable N and the
pyramid-skip / exposure descriptive (event prevalence, active-bar fraction,
`is_pyramid_bounce` while-active count) to contextualize EXP-023's sparse exposure.

### Standard Loading Pattern

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob("timebars/timebars_*.parquet"))[-1]

scan = pl.scan_parquet(path).sort("CloseTime")
total_rows = int(scan.select(pl.len()).collect().item())
analysis_cutoff = int(total_rows * 0.7)
bars = scan.slice(0, analysis_cutoff).collect()  # holdout never loaded
```

## Suggested Direction

Treat the bounded-vs-lifetime comparison on a **common per-horizon event set** as the
spine: it isolates the *holding/exit* decision from entry/exposure effects, so fork
(a) vs (b) is decided without needing the cTrader realized series. Use EXP-022's
`trend_change` subset to show whether trend-change exits truncate winners (which would
make `/EXIT` high-value) or cut losses (which would point at entry dilution). Keep the
cost lens strictly secondary — the headline fork is on gross, per the confirmed scope.
