# Analysis Plan: Experiment EXP-033 — TRAIN-Only Horizon Sweep (Attribution Crossover + FH(H) Net Curve)

## Objective

Two predeclared diagnostic deliverables on TRAIN (first 70% of the analysis set):
(1) the attribution map s_entry(H) of the per-event matched-control excess over
H ∈ {1, 2, 3, 4, 6, 8, 12, 24} domain bars, locating the entry/exit crossover that
EXP-031 left unresolved; (2) the FH(H) absolute net expectancy curve of the
fixed-horizon-exit variant, from which the mechanical one-SE rules freeze H\*_d and
the pyramid policy for EXP-037 (B2), or rule a domain B2-ineligible. No candidate
verdict is produced.

## Data Wiring

Identical substrate to EXP-031 (whose plan §Data-Wiring is incorporated by
reference), with two changes:

1. **TRAIN cutoff:** per (instrument, domain), `train_cutoff_idx =
   floor(0.7 × n_domain_bars)` on the rebuilt domain series (which itself covers
   only the first-70% analysis slice). All analysis rows must satisfy the
   containment rule below. The TEST segment and the global holdout are never read.
2. **Fixed population across the grid (containment rule; amended 2026-06-10, F08,
   pre-execution):** a row (event or control) is included iff
   `start_idx + 24 ≤ train_cutoff_idx` **and** `completion_idx ≤ train_cutoff_idx`.
   The first clause makes the maximum horizon window fit inside TRAIN; the second
   (the predeclared correction — originally omitted) keeps the BTC-lifetime outcome
   inside TRAIN too, since an `x_full_star` lifetime completing past the boundary
   would read TEST prices. This deliberately differs from EXP-031's per-H
   reportability: with one fixed population, every event has a reportable FH return
   at **every** H, the common-control set is H-invariant, and curve differences
   across H are pure horizon effects, never population shifts. Excluded-row counts
   are disclosed per domain and clause (`excluded_window` / `excluded_lifetime`).

Inputs: `EXP-022/results/lifetime_observations.csv` (events + controls, BTC
lifetime returns), `EXP-020/results/avwap_events.csv` (trigger timestamps;
1:1 join), rebuilt domain Close series via `xen.bar_aggregator` (EXP-020-identical
parameters; row counts must reproduce `EXP-020/results/analysis_metadata.csv` or
the run is REVISE-blocked), and the frozen `event_method.py` tail (pinned hash
`e50873d12a9f68d9`; hard assert).

`fh_bps(row, H) = 10000 × d × ln(close[i+H] / close[i])` — the same
`forward_logdiff_from_close` construction as EXP-031.

## Methodology

### Step 1 — Reconciliation anchors (run before any sweep output)

- **Method**: (a) rebuilt domain bar counts == EXP-020 metadata, exact; (b) frozen
  tail hash == pinned value; (c) one-time relaxed-rule check: with the containment
  rule swapped for EXP-031's per-H inclusion rule on the **full analysis set**, the
  H ∈ {1, 6} legs must reproduce EXP-031's published
  `decomposition_results.csv` values to ≤ 0.01 bps (same code path, same
  population ⇒ near-exact). After this check passes, all outputs are TRAIN-only.
- **Why this method**: the sweep is only meaningful if it is provably the same
  estimator EXP-031 ran, evaluated at more horizons on a cleaner population.
- **Simpler alternative considered**: skip (c) and trust shared code — rejected;
  the containment rule is new logic adjacent to the population definition, exactly
  where a silent divergence would corrupt every downstream number.
- **Assumptions**: none beyond artifact integrity.
- **Expected output**: `results/reconciliation.csv` (PASS/FAIL per anchor).

### Step 2 — Attribution legs at every H (gross, matched-control)

- **Method**: on the fixed TRAIN population, per event with ≥ 3 common controls:
  `X_full* = event_BTC − mean_cc(control_BTC)` (H-invariant),
  `X_entry(H) = event_FH(H) − mean_cc(control_FH(H))`,
  `X_exit(H) = X_full* − X_entry(H)`. Aggregate by the frozen `domain_effect`
  (per-instrument event-weighted mean → equal-weight across all four reportable
  instruments). Inference per leg per H: frozen 95% regime-cluster bootstrap CI
  (1000 resamples, clusters resampled within (instrument, direction) strata) with
  **one shared resample-index set across all H per domain** so the curve and its
  bands are internally coherent; one-sided stratified paired sign-permutation p
  (1000), reported **descriptively** — no Holm family and no leg-significance
  claims, because this is a diagnostic map, not a verdict (predeclared; prevents
  48-cell multiplicity theater).
- **Why this method**: identical frozen machinery as EXP-031 ⇒ the crossover read
  is comparable to the Phase 007 record by construction.
- **Simpler alternative considered**: CIs only at "interesting" H after looking —
  rejected as post-hoc; the full grid is cheap and predeclared.
- **Assumptions**: matched-control exchangeability within (instrument, direction)
  regime clusters — the standing EXP-021/027/028 assumption; additivity is exact
  by construction on the common-control set.
- **Expected output**: `results/attribution_sweep.csv` (domain × H × leg: effect,
  CI, SE, raw p, n). s_entry(H) = X_entry/X_full\* reported only where
  |X_full\*| > its bootstrap SE; otherwise legs are reported and the share is
  marked `ill_defined`.

### Step 3 — Crossover characterization (predeclared rule)

- **Method**: per domain, `H_cross = the smallest grid H with s_entry(H) ≥ 0.5 such
  that s_entry ≥ 0.5 for every larger grid H` (stable crossover). If no such H:
  `NO_STABLE_CROSSOVER`. If s_entry ≥ 0.5 at H=1 already: `ENTRY_DOMINANT_THROUGHOUT`.
- **Why this method**: a threshold rule fixed before results — the EXP-031 lesson
  (predeclared classification, no post-hoc reading).
- **Simpler alternative considered**: eyeball the curve — rejected; the whole point
  is a mechanical, dispute-free read.
- **Assumptions**: none; descriptive of the point estimates (CIs shown alongside).
- **Expected output**: `results/crossover.csv` (domain, H_cross or class).

### Step 4 — FH(H) absolute net curve and the two mechanical selections

- **Method**: events only (`role = event`), same fixed population. Per event:
  `net_e(H) = fh_bps(e, H) − RT_cons_i − rate_i × elapsed_calendar_days(trigger_time,
  close_time[i+H])`. Curve objective per domain = equal-weight mean over
  **EURUSD, USTEC, XAUUSD** (BTCUSD excluded per D0 §4; BTCUSD curve disclosed).
  Bootstrap SE per H from the shared resample-index set. Then, with zero discretion:
  - **H\*_d** = smallest H with `net(H) ≥ max_H(net) − SE(argmax)`; if
    `max_H(net) ≤ 0`, emit `B2_ELIGIBLE_d = false`.
  - **Pyramid policy at H\*_d**: recompute the curve point under {all-legs,
    first-leg-only, pyramid-legs-only}; select the first policy in that preference
    order within one SE of the best.
- **Why this method**: the one-SE rule converts a noisy argmax into a stable,
  simplicity-preferring selection; computing it inside this experiment (not B2)
  keeps every TRAIN read upstream of the one-shot TEST read.
- **Simpler alternative considered**: plain argmax — rejected; on 4h
  (~120 TRAIN events) argmax over 8 points is noise-dominated, and the one-SE rule
  is the predeclared design remedy.
- **Assumptions**: financing model as frozen (adverse-side daily rate × fractional
  calendar days from rebuilt timestamps); zero-baseline behavior — all quantities
  in absolute bps against a 0 baseline, no ratios of near-zero quantities.
- **Selection-stability disclosure (added 2026-06-10, F07):** chronological
  split-half of the contained TRAIN events per domain; per-half point-estimate
  objective net curves; flags `eligibility_stable` (both halves' grid maxima > 0),
  `h_star_stable` (frozen H\*'s per-half net within one full-TRAIN SE of that
  half's maximum), `policy_stable` (analogous at H\*). Point estimates only — no
  new test family; the full-TRAIN SE is the comparison scale. Disclosure only: the
  mechanical selection is unchanged; the flags are recorded for the EXP-037 scope
  and governance to weigh (4h is power-fragile near the 15-event floor).
- **Expected output**: `results/fh_net_curve.csv` (domain × H × instrument-set ×
  pyramid-policy: net, SE, CI); `results/b2_selection.json` (per domain: H\*,
  policy, B2_ELIGIBLE flag, one-SE bookkeeping, stability-disclosure flags) —
  **frozen on emission**.

### Step 5 — Determinism

- **Method**: same-seed full replay; byte-identical CSV/JSON outputs required.
- **Expected output**: replay flag in `results/run_metadata.json`.

## Visualisations (4 / 4 budget)

1. **s_entry(H) per domain** with the 0.5 line and H_cross marker — the crossover
   answer at a glance.
2. **FH(H) net curve per domain** (3-instrument objective) with one-SE band of the
   max and the H\* marker — shows what the selection rule saw.
3. **Stacked X_entry/X_exit bars at H\*** per domain with CIs — the decomposition at
   the selected operating point.
4. **Pyramid-policy comparison at H\*** per domain — the three policy nets with SEs.

## Interpretation Guide (predeclared)

- If H_cross exists and is stable on 5m/1h (the powered domains), the EXP-031
  contradiction resolves into a horizon-regime structure: the BTC exit's value is
  confined to H < H_cross. B2's FH(H\*) variant then has a mechanism rationale.
- If `ENTRY_DOMINANT_THROUGHOUT` on a domain, the H=1 EXIT_DOMINANT read of EXP-031
  was the anomaly on that domain (population difference disclosed in Step 1c).
- If `NO_STABLE_CROSSOVER` (oscillating shares), attribution is genuinely
  horizon-unstable; B2 may still proceed on the net curve alone — eligibility is
  Step 4's, not Step 3's, decision.
- If `B2_ELIGIBLE = false` everywhere, the fixed-horizon exit cannot rescue absolute
  net on TRAIN; Tier B reduces to B1 (/COND) only, and the design §9 FLAT path
  becomes more likely.
- 4h reads carry ~120 events; wide bands are expected and disclosed, and the one-SE
  rule (not the reader) absorbs that noise.

## Implementation Safety Constraints (for `experiment-developer`)

- Timestamp ordering by `CloseTime`; never bar-index alignment across views.
- The TRAIN cutoff is computed on rebuilt domain bars per (instrument, domain);
  assert `train_cutoff_idx + 24 < n_domain` is impossible to violate by
  construction (containment uses the cutoff, not the series end).
- One fixed population per (instrument, domain); assert the common-control set is
  identical across all H (hard invariant, not a recomputation).
- Shared bootstrap resample indices across H per domain (resample once, evaluate
  all H columns).
- FH returns vectorized as shifted-Close joins (one pass for all H); the sweep loop
  is instrument × domain with `tqdm`; no per-event Python loops over large frames.
- No directory creation or data loads at import time; helpers return data, no
  helper-level printing.
- Financing duration from rebuilt-series timestamps (fractional days; includes
  weekends). Denominators: event counts per instrument fixed by the containment
  rule and disclosed; equal-weight means skip `unreportable` cells (< 30 events
  5m/1h, < 15 4h) with disclosure.
- `b2_selection.json` is written exactly once, after Step 4, before any plot.

## Complexity Check

- Statistical test families: 2 / 2 (regime-cluster bootstrap; stratified
  sign-permutation, descriptive).
- Visualisations: 4 / 4.
- New modules: 1 / 1 (orchestration script; `event_method.py` imported unchanged).
