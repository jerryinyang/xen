# Analysis Plan: Experiment EXP-024

## Objective

Decide, per domain, whether the AVWAP bounce edge that EXP-021 measured
(+3.8/+9.1/+37.6 bps fixed-horizon reaction) but EXP-023 lost as an always-on
strategy (~0-to-negative gross) is lost to **fork (a)** — a fixable holding/exit
problem (a bounded max-hold captures materially more gross edge than holding to
lifetime completion, and reaches the ratified-loose suite floor) — or **fork (b)** —
entry/position dilution so deep that no scoped bounded-hold remedy is justified
(no adequately powered bounded horizon reaches the loosest floor). This is a **diagnostic**: no qualification
suite is run, no pass/fail verdict is issued, and the global holdout stays sealed.
The headline fork is decided on **gross** returns; cost is a secondary lens. The
result gates Phase 005 Stage B (EXP-026 `/EXIT`).

All returns are direction-signed **real domain-close** returns in bps. AVWAP and
MAD bands are reference lines used only to define events (inherited from EXP-020);
they are never P&L prices. The final 30% global holdout is never loaded.

## Methodology

### Step 1: Deterministic substrate reconstruction and event join

- **Method**: Rebuild 5m/1h/4h domain OHLC bars from the first-70% 1-minute
  analysis slice using `xen.bar_aggregator` with the EXP-020/021/022 coverage
  convention (5m strict; 1h/4h `min_coverage=0.90`). Verify the reconstructed
  domain row counts reproduce EXP-020 `analysis_metadata.csv` exactly (determinism
  gate). Load and exact-match-join three read-only upstream tables:
  EXP-020 `avwap_events.csv` (event index `trigger_idx`, `direction`, `instrument`,
  `domain`, `is_pyramid_bounce`, `trigger_close`), EXP-022 `lifetime_observations.csv`
  filtered to `role == "event"` (`outcome`, `bars_to_completion`, `lifetime_bps`,
  `completion_idx`), and EXP-021 `reaction_observations.csv` (horizons {1,3,6} for
  cross-check). Join key: `(instrument, domain, regime_id, trigger_idx)`.
- **Why this method**: The signal substrate is already validated (EXP-020
  SUPPORTED_FULL) and deterministic; reconstructing rather than re-deriving keeps the
  diagnostic anchored to the exact events the prior experiments measured. Re-using
  `trigger_idx` against the rebuilt domain close series gives the dense horizon grid
  EXP-021's {1,3,6} table cannot.
- **Simpler alternative considered**: Use only EXP-021's existing {1,3,6} returns.
  Rejected — three points cannot locate where the cumulative gross return peaks and
  decays relative to the full-lifetime hold, which is the crux of the fork.
- **Assumptions**: domain reconstruction is deterministic (verified against EXP-020
  row counts); `trigger_idx` indexes the same domain array. Temporal ordering by
  `CloseTime`; alignment by index into the identically-reconstructed array, never
  across mismatched views.
- **Expected output**: a joined per-event table; a determinism-check row confirming
  reconstructed domain row counts == EXP-020.

### Step 2: Horizon-decay curve — bounded max-hold gross returns

- **Method**: For each event and each grid horizon `h ∈ {1,2,3,4,5,6,8,10,12,16,20,24}`,
  compute the direction-signed log-close return
  `g_event(h) = 10_000 × direction × (log_close[trigger_idx+h] − log_close[trigger_idx])`
  (the EXP-021/022 `signed_log_bps` convention), using only analysis-set closes; an
  event is **reportable at h** only if `trigger_idx + h` lies inside the analysis
  slice. Per domain (and per instrument×direction for diagnostics), compute the mean
  `g(h)` with a **regime-cluster bootstrap** 95% CI (resample `regime_id` clusters
  within each instrument×direction stratum; ≥10,000 resamples), reusing the
  EXP-021/022 event-uncertainty machinery. Overlay the EXP-021 {1,3,6} points as an
  external cross-check (they should agree within bootstrap noise on the matched event
  set).
- **Why this method**: A per-horizon mean curve with resampling CIs is the simplest
  object that shows *where* the gross edge lives and how fast it decays. The
  regime-cluster bootstrap is the AVWAP event experiments' established
  dependence-preserving interval method — the analysis unit is the event and events
  in the same regime share the anchored AVWAP path — and avoids i.i.d./normality
  assumptions on returns.
- **Simpler alternative considered**: Plain SE/t-interval on per-horizon means, or a
  continuous-series stationary block bootstrap. Both rejected — events are discrete
  and cluster by regime, not by a continuous bar series; regime-cluster resampling is
  the validated EXP-021/022 choice and the correct dependence model for event means.
- **Assumptions**: exchangeability under the stationary bootstrap's block structure;
  no normality assumed. Denominator at each `h` is its reportable-event count
  `N(h)`, reported so the shrinking long-horizon sample is visible.
- **Expected output**: `horizon_decay.csv` (per domain×instrument×direction×h: mean,
  CI, `N(h)`); the pooled-by-domain `g(h)` curve used by the fork.

### Step 3: Always-on lifetime reference and bounded-vs-lifetime contrast

- **Method**: Define the always-on reference `g_life` as the mean direction-signed
  gross lifetime return (`lifetime_bps`, trigger→`completion_idx`) over **completed**
  (non-`unfinished`) events. To keep the comparison apples-to-apples, at each `h`
  recompute `g_life(h)` on the *common event set* reportable at `h` AND completed.
  Report the paired contrast `Δ(h) = g(h) − g_life(h)` with a bootstrap CI of the
  mean paired difference on the common set; identify `h* = argmax_h g(h)` and report
  `g*`, its CI, and `Δ(h*)`.
- **Why this method**: Restricting both legs to the same events isolates the
  *holding/exit* decision (bounded vs hold-to-completion) from entry, pyramid-skip,
  and exposure effects — so fork (a) vs (b) is decided without needing the cTrader
  realized series. Paired bootstrap on the common set is the honest uncertainty
  statement for `Δ`.
- **Simpler alternative considered**: Compare bounded means to the EXP-022 headline
  lifetime mean on all events. Rejected — different denominators (unfinished
  exclusion, horizon-reportability) would confound the holding contrast with sample
  composition.
- **Assumptions**: `unfinished` exclusion matches EXP-022; common-set pairing is
  valid because each event has both a bounded-`h` return and a completed lifetime
  return.
- **Expected output**: `bounded_vs_lifetime.csv` (per domain: `g*`, `h*`, CI,
  `g_life(h*)`, `Δ(h*)`, CI, common-set `N`).

### Step 4: Per-domain fork verdict (predeclared rule)

- **Method**: Apply the scope's fork rule, multiplicity-controlled across the grid.
  For each horizon compute the one-sided bootstrap tail `p_h = Pr(mean ≤ 0)`; apply
  **Holm** across the 12 horizons; a horizon is *positive* if Holm-adjusted
  `p_h < 0.05`. Let `floor_d ∈ {0.5, 2, 8}` bps for 5m/1h/4h.
  - **Fork (a)** if BOTH: (i) `g* ≥ floor_d`, the `h*` CI lower bound is
    `≥ floor_d`, and `h*` is Holm-positive; (ii)
    `g* − g_life(h*) ≥ margin_d`, `margin_d = max(0.5 bps, 0.25 × floor_d)`
    (5m 0.5, 1h 0.5, 4h 2.0 bps), on the common set. `h*` is the max-`g` horizon
    among horizons with adequate common-set N (≥ `DOMAIN_MIN_COMPLETED`).
  - **Fork (b)** if `g(h) < floor_d` at every grid horizon (a.i fails everywhere).
  - **Inconclusive** if neither resolves: reportable completed-`N` below the
    EXP-021/022 minimum, or the `h*` CI half-width so wide that floor-clearance is
    indeterminate (CI straddles `floor_d`).
  - **Phase-level**: fork (a) if the primary domain (5m) or any domain is fork (a)
    → Stage B justified on supporting domain(s); fork (b) only if all three domains
    are fork (b) → skip Stage B; else mixed/inconclusive → operator decides.
- **Why this method**: A predeclared threshold rule on an already-computed curve
  keeps the diagnostic honest; Holm across the horizon grid controls the
  "best-of-12-horizons" selection so a noise peak cannot trigger fork (a).
- **Simpler alternative considered**: Pick `h*` and test only it (no Holm).
  Rejected — selecting the max over a grid then testing it inflates the false-fork-(a)
  rate.
- **Assumptions**: the predeclared grid, floors, primary domain (5m), and margin are
  fixed before results; no goalpost movement.
- **Expected output**: `fork_verdict.csv` (per domain: verdict, `g*`, `h*`,
  Holm-adjusted `p_{h*}`, floor, `Δ(h*)`, margin, `N`) + phase-level row.

### Step 5: Trend-change-exit return decomposition (where the lifetime hold bleeds)

- **Method**: Among completed events with `outcome == "trend_change"`, summarize the
  `lifetime_bps` distribution per domain (mean with bootstrap CI, median, quartiles,
  fraction < 0). Place it descriptively against the `favorable` and `adverse` outcome
  return medians to read whether trend-change exits **cut winners** (their returns
  sit below favorable but are often positive/truncated) or **save losers** (their
  returns are predominantly negative). This is the "trend-change-exit return CI"
  budgeted test.
- **Why this method**: EXP-023 attributed the drag to trend-change exits + cost; this
  isolates the trend-change subset's realized signed return — the single most direct
  read on whether a revised exit (fork-a actionable) is promising.
- **Simpler alternative considered**: Count trend-change frequency only (EXP-023
  already gave 12.3%). Rejected — frequency without the return sign cannot
  distinguish "cuts winners" from "saves losers."
- **Assumptions**: trend_change `lifetime_bps` is real-close, direction-signed
  (inherited from EXP-022). Denominator = trend_change completed events per domain.
- **Expected output**: `trend_change_returns.csv` (per domain: mean+CI, median,
  quartiles, frac<0, N) and the favorable/adverse median context.

### Step 6: Holding-period and exposure/dilution descriptive

- **Method**: Per domain, summarize `bars_to_completion` by outcome
  (favorable/adverse/trend_change/unfinished) and report exposure descriptives:
  event prevalence, active-bar fraction, and the pyramid-skip count
  (`is_pyramid_bounce` events arriving while a position would already be active),
  to contextualize EXP-023's ~93%-flat sparse exposure (20,904 events → 17,478
  entries, 3,426 skipped). Descriptive only — no test.
- **Why this method**: Exposure/dilution is the candidate mechanism behind fork (b);
  surfacing it descriptively lets the reader see whether thin exposure (not exit
  timing) is the binding constraint.
- **Simpler alternative considered**: omit. Rejected — without exposure context a
  fork (b) verdict would be under-explained.
- **Assumptions**: pyramid/while-active reconstruction from EXP-020 event ordering is
  deterministic and look-ahead-safe.
- **Expected output**: `holding_exposure.csv`.

### Step 7: Cost-attribution (secondary lens — not part of the fork)

- **Method**: Apply the EXP-004/023 per-instrument flat-cost convention to the
  horizon curve and to `g_life`, producing gross-vs-net curves. Report the cost-drag
  decomposition (how much of the gross→net gap is per-active-bar cost). Deterministic
  subtraction; descriptive.
- **Why this method**: Confirms the scope's stance that the failure is not *only*
  cost (EXP-023 gross was already tiny) and quantifies cost's marginal contribution
  without letting it drive the verdict.
- **Simpler alternative considered**: skip cost entirely. Rejected — the
  gross-vs-net gap is a requested decomposition lens and informs `/EXIT` design.
- **Assumptions**: same flat per-instrument cost as EXP-004/023; net = gross − cost×
  active-bar fraction.
- **Expected output**: `cost_attribution.csv`; net overlays on the horizon plot.

## Visualisations

1. **Horizon-decay curve** (per domain): mean `g(h)` with CI band across the grid,
   EXP-021 {1,3,6} cross-check markers, the `g_life` always-on line, and the
   ratified-loose floor line — the primary fork visual.
2. **Outcome composition + holding period** (per domain): stacked outcome mix
   (favorable/adverse/trend_change/unfinished) and `bars_to_completion` distribution.
3. **Trend-change-exit return distribution** (per domain): histogram of trend_change
   `lifetime_bps` with mean/median and the favorable/adverse medians overlaid —
   "cuts winners vs saves losers."
4. **Cost attribution** (secondary): gross vs net horizon curve and lifetime per
   domain, showing cost drag.

## Interpretation Guide

- If for a domain `g*` reaches its loose floor with a Holm-positive `h*`, its CI
  lower bound also clears the floor, **and** it beats `g_life(h*)` by the margin →
  **fork (a)**: a bounded exit captures edge the always-on hold gives back; `/EXIT`
  is worth scoping (EXP-026) on that domain.
- If `g(h)` is below the loose floor at **every** adequately powered horizon →
  **fork (b)**: the bounded-hold remedy lacks floor-clearing per-event edge, so the
  entry/position is too diluted for scoped `/EXIT`; skip `/EXIT`, redirect per
  design §6.
- If the trend-change subset's `lifetime_bps` is predominantly **positive but
  truncated** (below favorable medians), it corroborates fork (a) (winners cut early);
  if predominantly **negative**, trend-change exits are saving losers and the drag is
  elsewhere (entry/exposure), corroborating fork (b).
- If reportable completed-`N` is too small (expected on 4h, ~246 events) or the `h*`
  CI straddles the floor → **inconclusive** for that domain; the phase verdict then
  rests on the resolvable domains (primary 5m).
- Cost lens: if the gross curve already fails the floor, cost is not the binding
  constraint — confirms the scope's gross-primary framing.

## Complexity Check

- Statistical tests: 2 / 2 — (1) per-horizon stationary block-bootstrap CIs with Holm
  adjustment across the grid (covers Steps 2–4, incl. the paired bounded-vs-lifetime
  bootstrap); (2) trend-change-exit return bootstrap CI (Step 5). Steps 6–7 are
  descriptive. The fork is a predeclared threshold rule, not an additional NHST.
- Visualisations: 4 / 4.
- New modules: 1 / 1 — at most one small reusable horizon-return-grid helper in
  `python/src/xen/` if not already covered by EXP-021/022 machinery; otherwise 0.

## Implementation Safety Constraints (for experiment-developer)

- **Holdout fence**: load only the first-70% 1-minute slice; never read the final 30%.
  A horizon contribution requires `trigger_idx + h < analysis_end_index`; events
  closer to the analysis-set end than `h` are non-reportable at `h` (drop from
  `N(h)`), never extended into the holdout.
- **Determinism gate**: reconstructed 5m/1h/4h domain row counts must equal EXP-020
  `analysis_metadata.csv`; fail loudly if not (the join indices depend on it).
- **Denominators / zero-baseline**: report `N(h)` per horizon and per-outcome counts;
  all fork comparisons are absolute bps vs fixed floors — compute **no**
  percentage-improvement-over-zero-baseline ratio. If a (domain, h) cell has zero
  reportable events, emit NaN and exclude it — never coerce to 0.
- **Look-ahead / real-price**: returns use only closes at or after the trigger up to
  the evaluated horizon, from real domain `Close` only. No AVWAP/band/HA/Renko price
  enters any return.
- **Vectorization that preserves causality**: the horizon-return gather
  (`log_close[trigger_idx + h]`) is a pure indexed lookup — safe to vectorize with
  NumPy/Polars. The regime-cluster bootstrap must resample whole `regime_id` clusters
  (carrying all their events); do **not** replace it with i.i.d. per-event resampling,
  which would understate dependence. Keep the event/pyramid while-active
  reconstruction sequential.
- **Bounded iteration / progress**: outer loops are bounded (4 instruments × 3 domains
  × 12 horizons; ≥10,000 bootstrap resamples per cell). Use `tqdm` over the
  domain×instrument×horizon grid and/or bootstrap batches; vectorize bootstrap
  resampling per cell rather than Python-looping each resample.
- **Organization**: imports → path setup → constants → I/O helpers → pure computation
  → plotting → orchestration → `main()`; output directories created only in
  orchestration; helpers return data, do not print; VAL-001-style sectioning.
