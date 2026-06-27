# Analysis Plan: Experiment EXP-028

## Objective

Determine whether the faithful selective AVWAP strategy (unchanged in trade logic
from the EXP-023 baseline — MA(20,50) regime detector, typical-price AVWAP,
TickVolume^0.75 weight, MAD band ×1.0, EXP-020 bounce definition, EXP-022
completion rule) shows positive **event-level matched-control expectancy** on at
least one domain (5m, 1h, 4h), when evaluated under the frozen EXP-027 event-level
inference on the first-70% analysis set with predeclared inference.

This is the **re-screen of HYP-004** under a fit-for-purpose yardstick
(`CF-AVWAP-001/HYP-004-R`), resolving the EXP-023 framing-defect ambiguity. The
**inference tail** is frozen from EXP-027 (METHOD_VALID). The **return/excess
construction** is redesigned (vs. the first draft of this plan) so the binding gate
stays inside the construction EXP-027 actually calibrated — see the Construction
Discipline note below.

## Construction Discipline (binding — the Phase 006 correction applied to *this* experiment)

EXP-027 calibrated a **symmetric** per-event excess: event and control returns were
both formed over the **same fixed horizon** (primary `H=3`, family `{1,3,6}`). Under
that symmetric construction the null paired-excess is mean-zero and sign-symmetric,
so the gate's FPR is controlled. EXP-027 did **not** calibrate an asymmetric
construction in which the event uses an endogenous stopping rule while the control
uses a fixed window. Applying the gate to such an asymmetric construction would
repeat the Phase-005 error in a new form (a yardstick used outside its calibrated
envelope) — and EXP-024 already measured the bias direction (trend-change exits cut
losers; events fall *less than* controls but do not rise), so an asymmetric
construction is biased **toward a false negative**.

This plan therefore uses a **dual gate**:

- **PRIMARY (binding):** the EXP-022 **symmetric own-exit** matched-control lifetime
  excess. Event and control lifetimes are *both* completed under the same
  band-target/trend-change exit rule (this is exactly how EXP-022 built its
  observations), so the construction is symmetric and the gate's FPR control follows
  from sign-permutation exactness + EXP-027's sparse-count validation.
- **SECONDARY (non-binding, calibrated):** the endogenous-exit-event vs.
  fixed-window-control construction (the original draft). It carries interpretive
  weight **only if** a predeclared in-experiment placebo-null check confirms FPR ≤ α₀
  and null-excess ≈ 0 for that exact construction; otherwise it is reported as
  not-calibrated and carries zero weight.

A negative PRIMARY gate is the binding `EVAL_REFUTED`. A disagreeing or
non-calibrated SECONDARY never overrides the PRIMARY.

## Pyramid handling (predeclared — included; faithful to original concept and to the reused data)

Pyramid bounces are **included** (not filtered). Justification, per Phase 006
design §4 ("any position-rule change must be predeclared and justified as closer to
the original, not as a tuning lever"):

1. Pyramids contributed to every validated upstream observation this experiment
   reuses: EXP-020 events are ~50% pyramid (10,461 of 20,911); EXP-021 applied no
   pyramid filter; EXP-022's SUPPORTED lifetime result was computed over both
   `is_pyramid_bounce` ∈ {true, false} event and control rows.
2. The original `anchored-vwap.md` (HYP-002) concept pyramids; EXP-023's
   pyramid suppression was itself the deviation (framing review §2). Including
   pyramids is therefore **closer to the original**, not a new lever.
3. EXP-027 calibrated the method on placebo placement that deliberately allowed
   intra-regime clustering / pyramid-style placements, so the regime-cluster
   bootstrap (which resamples `regime_id` clusters, never individual events) is
   validated to absorb the extra within-regime dependence pyramids introduce.

`is_pyramid_bounce` is retained as a reported diagnostic split (not a gate), so the
pyramid vs. non-pyramid contribution is visible without changing the verdict basis.

## Frozen vs. re-implemented components (Finding 3 — precise delineation)

The whole `event_method.py` file is **not** frozen for EXP-028, because the variable
lifetime hold and the EXP-022-paired inputs require new substrate/return code. The
freeze applies **only to the inference-tail functions**, which are imported unchanged
and guarded:

| Reused **unchanged** (frozen inference tail) | Re-implemented for EXP-028 |
|---|---|
| `domain_effect`, `build_strata`, `bootstrap_effect_distribution`, `permutation_p`, `holm_adjust`, `decide_label`, `wilson_interval`, `sortino_ratio`, `equity_advantage` | event/control **return construction** (lifetime from EXP-022; fixed-horizon `{1,3,6}` for the secondary-stability inputs); control **eligibility** for the secondary fixed-window construction (the frozen `eligible_controls`/`place_regime_triggers` hardcode `MAX_HORIZON=6` and cannot serve a variable hold) |

Implementation imports the frozen tail from
`python/experiments/EXP-027/code/event_method.py` and asserts a **content hash of
those specific functions** (e.g. `inspect.getsource` over the named symbols) matches
the EXP-027 METHOD_VALID version; mismatch aborts with `FROZEN_INFERENCE_MODIFIED`.
A whole-file hash is **not** used (it would be meaningless given the necessary new
return code). `verify_control_matching()` is also called at startup as the
EXP-027 equivalence guard for any reused nearest-control logic in the secondary
construction.

## Methodology

### Step 1: Dependency gate check

- **Method**: Load and assert upstream status:
  - `EXP-020/results/run_metadata.json`: `overall_status == SUPPORTED_FULL`, ready on
    {5m, 1h, 4h}, zero invariant failures, deterministic replay; confirm
    `avwap_events.csv`, `avwap_state_summary.csv`, `domain_readiness.csv` exist.
  - `EXP-027/results/run_metadata.json`: `method_verdict == METHOD_VALID`.
  - `EXP-022/results/run_metadata.json`: completion run present; confirm
    `lifetime_observations.csv`, `lifetime_completion_summary.csv` exist.
- **Why this method**: Hard pre-conditions prevent running on an invalidated
  substrate or method. METHOD_VALID is the binding gate that the frozen inference
  tail is fit-for-purpose; SUPPORTED_FULL guarantees the regime/event substrate.
- **Simpler alternative considered**: file-existence only. Rejected — governance
  requires status verification.
- **Assumptions**: `run_metadata.json` files are well-formed; upstream outputs are
  immutable after their own governance verdict.
- **Expected output**: gate-pass assertion (hard-fail with diagnostic); recorded in
  `run_metadata.json.dependency_status`.

### Step 2: Load, reconstruct domains, and verify index alignment (Finding 6)

- **Method**:
  1. **Per-instrument source selection — identical to EXP-020/027.** Select one
     time-bar file per instrument by the **`Symbol` column**, latest-sorted wins
     (the exact selection EXP-020/021/022/027 used). Do **not** glob-and-take-last
     blindly: `data/timebars/` contains multiple/auxiliary files per instrument
     (e.g. `timebars_analysis70_xauusd_*`) and the wrong frame silently corrupts
     every index → return. This is the EXP-027 execution-time bug; guard against it.
  2. **Domain reconstruction**: lazy `pl.scan_parquet → sort(CloseTime) →
     first-70% slice → collect`, then `xen.bar_aggregator` → 5m (strict), 1h/4h
     (`min_coverage=0.90`). Store `Symbol, CloseTime, Open, High, Low, Close,
     TickVolume` per domain.
  3. **Load EXP-020 events** (`avwap_events.csv`) and **EXP-022 lifetime
     observations** (`lifetime_observations.csv`, both `role=event` and
     `role=control` rows).
  4. **Hard alignment guard**: for a sample of events per (instrument, domain),
     re-derive the trigger condition at `trigger_idx` against the rebuilt domain
     frame — assert `CloseTime[trigger_idx]` equals the event's `trigger_time` and
     that `Close[trigger_idx]` equals `trigger_close` to float tolerance. **Hard-fail
     on any mismatch** (the frame is misaligned; abort before any return is
     computed). Repeat for EXP-022 `start_idx`/`completion_idx`.
  5. **Holdout fence**: assert every event `trigger_idx`, EXP-022 `start_idx`, and
     `completion_idx` falls strictly inside the first-70% frame. Right-censored
     events (EXP-022 `outcome == unfinished` / null `completion_idx`) are excluded
     with a diagnostic count (they are an exit-rule non-completion, not a signal).
- **Why this method**: identical source selection + an explicit value-level alignment
  assertion is the only safe way to reuse EXP-020/022 integer indices against a
  freshly rebuilt frame; the EXP-027 incident proves assertion-by-assumption is not
  enough.
- **Simpler alternative considered**: trust the indices (original draft). Rejected —
  silent misalignment is the highest-impact, lowest-visibility failure here.
- **Assumptions**: EXP-020/022 indices are 0-indexed into the per-instrument
  first-70% domain frame produced by the identical selection.
- **Expected output**: in-memory domain frames; joined event/control tables;
  alignment-pass + fence-pass flags in `run_metadata.json`; diagnostic counts (total
  events, right-censored, holdout-excluded, usable; pyramid split).

### Step 3: PRIMARY excess — EXP-022 symmetric own-exit matched-control lifetime (Finding 1)

- **Method**:
  1. From `lifetime_observations.csv`, take usable `role=event` rows (reportable,
     completed, inside the fence; pyramids included). For each event, its matched
     controls are the `role=control` rows sharing the same
     `(instrument, domain, regime_id, event_trigger_idx)`.
  2. **Per-event return** = the event row's `lifetime_bps` (the direction-signed
     log lifetime return to its own band-target/trend-change exit). **Reconcile**:
     assert `lifetime_bps ≈ 10000·direction·ln(Close[completion_idx]/Close[start_idx])`
     on the rebuilt frame to float tolerance (proves the reused value equals the
     scope's stated metric); hard-fail on systematic mismatch.
  3. **Per-event control mean** = mean of the matched controls' `lifetime_bps` (each
     control completed under the **same** exit rule from its own non-trigger start —
     this is the symmetry that makes the null excess mean-zero).
  4. **Per-event paired excess** = `event_lifetime_bps − mean(control_lifetime_bps)`.
  5. **Reportability** (per event): ≥ `MIN_CONTROLS=3` matched controls (EXP-022's
     `reportable_event` flag, re-derived for audit).
- **Why this method**: this is the construction EXP-022 already validated and the one
  whose null is provably sign-symmetric. The PRIMARY gate is therefore the faithful
  strategy lifetime (entry+exit) measured against a benchmark that runs the *same*
  exit from a comparable starting point — isolating event-timing value while keeping
  the gate inside the calibrated structural envelope.
- **Simpler alternative considered**: rebuild controls as a fixed window of length =
  event hold (original draft). Rejected — asymmetric, uncalibrated, false-negative
  biased (Finding 1). Retained only as the SECONDARY (Step 6), gated by a null check.
- **Assumptions**: EXP-022 control `lifetime_bps` and the event/control link via
  `event_trigger_idx` are correct (re-derived/spot-checked). Within a regime, events
  (incl. pyramids) are dependent → handled by the regime-cluster bootstrap, not by
  treating events as independent.
- **Expected output**: per-event table `(symbol, domain, regime_id, direction,
  is_pyramid_bounce, trigger_idx, event_lifetime_bps, mean_control_lifetime_bps,
  paired_excess_bps, n_controls)`. Diagnostics: counts, pyramid split, reconciliation
  residuals.

### Step 4: Secondary-stability inputs — fixed-horizon {1,3,6} excess (Findings 4, 5)

- **Method**: For the same usable events, compute the **EXP-027-calibrated**
  symmetric fixed-horizon excess at `h ∈ {1,3,6}` (primary `h=3`): event return =
  `direction·10000·ln(Close[t+h]/Close[t])`; controls = same-regime, not-a-trigger,
  outside the 6-bar exclusion window, ≥6 forward bars, nearest by anchor-age then
  index, ≤5 / ≥3 (the frozen `nearest_controls`, equivalence-guarded). Paired excess
  = event − control-mean, per `h`.
- **Why this method**: this fixed-horizon excess **is** the construction EXP-027
  calibrated, so (a) its event-level MDE map (5m=1 / 1h=4 / 4h=32 bps at α₀=0.05)
  applies to it numerically, and (b) it reconnects to EXP-021's validated reaction
  (+3.8/+9.1/+37.6 bps at the bounce). It feeds `decide_label`'s `effect_h1`/
  `effect_h6` slots as the **secondary-horizon stability** input, replacing the
  original draft's degenerate "pass the same effect to all slots" neutering: a
  PRIMARY lifetime FOR is downgraded to `INCONCLUSIVE_SECONDARY_UNSTABLE` if the
  short-horizon reaction (h1 and h6) is jointly negative. It also serves as a
  calibration anchor (sanity vs. EXP-021/027).
- **Simpler alternative considered**: drop the secondary-horizon check entirely
  (original draft). Rejected — it discards both the stability guard and the
  reconnection to the only numerically-applicable MDE.
- **Assumptions**: fixed-horizon construction is symmetric and EXP-027-calibrated;
  forward closes are outcomes only.
- **Expected output**: per-event fixed-horizon excesses `{h1,h3,h6}`; per-domain
  fixed-horizon effects for the stability slots and the EXP-021/027 reconnection
  table.

### Step 5: Aggregation + PRIMARY inference (frozen tail) (Finding 1)

- **Method**: Apply the frozen EXP-027 inference to the PRIMARY lifetime paired
  excess (and, for the stability slots, to the `{1,6}` fixed-horizon excesses):
  1. **Domain effect** (`domain_effect`): equal-weight mean across reportable
     instruments of each instrument's event-weighted mean paired excess (EXP-008
     pooling discipline).
  2. **95% regime-cluster bootstrap CI** (`bootstrap_effect_distribution`,
     `N_BOOT=1000`): resample `regime_id` clusters with replacement within
     (instrument, direction) strata — absorbs within-regime/pyramid dependence.
  3. **Stratified paired sign-permutation p** (`permutation_p`, `N_PERM=1000`),
     one-sided (null: excess ≤ 0). Exact under the symmetric construction.
  4. **Holm across the 3 domains** (`holm_adjust`).
  5. **Per-domain verdict** (`decide_label`): `FOR ⇔ effect>0 ∧ CI_low>0 ∧
     Holm_p ≤ α₀`, downgraded to `INCONCLUSIVE_SECONDARY_UNSTABLE` if the Step-4
     `{h1,h6}` reaction is jointly negative; `EVIDENCE_AGAINST` if `CI_high ≤ 0`;
     else `INCONCLUSIVE_SPANS_ZERO`.
  6. **Reportability / power for an AGAINST read (Finding 4)**: a domain may be read
     `AGAINST` only if it is adequately powered, judged from **in-experiment**
     quantities — event count ≥30 (≥8/direction, ≥3/4 instruments) **and** the
     bootstrap CI half-width is finite and tight enough to exclude a material
     positive effect. The EXP-027 numeric MDE (1/4/32 bps) is **not** used as the
     lifetime-power threshold (it is in `H=3` units; lifetime returns are
     larger-magnitude/higher-variance). It is retained only as the structural-validity
     reference and as the applicable floor for the Step-4 fixed-horizon anchor.
- **Why this method**: the object the phase wants validated is exactly this decision
  rule; the regime-cluster bootstrap + sign-permutation correctly handle clustered,
  non-normal, heavy-tailed event returns. FPR control for the lifetime primary rests
  on sign-permutation exactness (symmetric construction) plus EXP-027's sparse-count
  validation of the same machinery.
- **Simpler alternative considered**: per-event t-test / Wilcoxon. Rejected —
  assume independence across events, violated by within-regime/pyramid clustering.
- **Assumptions**: regime clusters are the dependence unit; instruments
  equal-weighted; bootstrap CI ~95% coverage (EXP-027-validated structure).
- **Expected output**: `results/event_level_results.csv` — per domain
  `(domain, effect_bps, ci_low, ci_high, raw_p, holm_p, n_events, n_controls_mean,
  sec_h1_bps, sec_h6_bps, verdict)`.

### Step 6: SECONDARY construction + its predeclared placebo-null calibration (Finding 1)

- **Method** (non-binding, runs only as a calibrated diagnostic):
  1. **Predeclared placebo-null check, BEFORE reading the real secondary excess.**
     Using the EXP-020 regime scaffold, place placebo events (at the real ~ activity
     rate, pyramid-style clustering allowed), derive each placebo event's hold by
     applying the **same** band-target/trend-change exit rule, and build the
     **fixed-window** control of that hold length — i.e. the *exact* asymmetric
     construction. Push the placebo paired excesses through the frozen tail and
     measure FPR and mean null-excess across draws (fixed seeds). **Calibrated iff**
     FPR ≤ α₀ (Wilson upper bound within tolerance) **and** null mean-excess ≈ 0 in
     every domain.
  2. **Real secondary excess** (only reported with weight if step 1 calibrated):
     event return to its EXP-022 endogenous exit vs. a control fixed window of equal
     length, same frozen inference. Verdict reported as a **diagnostic** comparison
     to the PRIMARY.
- **Why this method**: the operator decision keeps both constructions; this is the
  honest way to keep the asymmetric one — it carries weight only after its own null
  is shown controlled, never on assertion. If the placebo-null check fails (expected
  risk given the EXP-024 drag), the secondary is labeled `NOT_CALIBRATED` and
  excluded from interpretation — a valid, predeclared outcome.
- **Simpler alternative considered**: report the secondary uncalibrated. Rejected —
  that is precisely the Phase-005 error.
- **Assumptions**: placebo placement/matching use bar-time info only; the planted
  null is exactly 0 excess by construction.
- **Expected output**: `results/secondary_calibration.csv` (FPR, null-excess per
  domain, `calibrated` flag) and `results/secondary_results.csv` (real secondary
  effect/CI/verdict, weight-bearing flag).

### Step 7: Equity companion (non-gating)

- **Method**: Exposure-aware companion on the PRIMARY lifetime trades (identical in
  structure to EXP-027's `equity_advantage`):
  1. **Strategy** per-trade returns = event lifetime log returns; cumulative
     log-equity per (instrument, domain).
  2. **Exposure-matched baseline** = same number of trades at the event's matched
     controls, same own-exit lifetime, same direction-signing (so exposure/holding
     are matched; the only difference is entry timing).
  3. **Metrics**: terminal cumulative log-equity advantage (`strategy − baseline`)
     with a regime-cluster bootstrap CI (reuses Step-5 machinery — no new test);
     Sortino-style ratio difference (`sortino_ratio`).
  4. **100% buy-hold** = annotated context only, explicitly labeled exposure-mismatched
     (~ strategy exposure vs 100%); never the comparator (prevents re-importing the
     dilution artifact).
  5. Domain-level = equal-weight across reportable instruments.
- **Why this method**: realizes the original headline (risk-adjusted equity vs
  baseline) on an exposure-matched basis. Non-gating: it informs interpretation but
  does not decide the verdict; EXP-027 documented the companion null is slightly
  negative-drifting, so it is read for *direction/consistency*, not as a test.
- **Simpler alternative considered**: raw strategy vs 100% buy-hold. Rejected — that
  is the exact exposure/dilution mismatch that broke EXP-023.
- **Assumptions**: log-return additivity; Sortino NaN when no downside (reported
  as-is, never 0).
- **Expected output**: `results/equity_companion.csv`
  `(domain, strategy_terminal_bps, baseline_terminal_bps, advantage_bps,
  sortino_diff, advantage_rate)`.

### Step 8: Per-domain verdicts and phase outcome (Finding 7)

- **Method**: Bind on the PRIMARY gate.
  1. **Per-domain verdict** = PRIMARY `decide_label` output.
  2. **Phase outcome**:
     - **EVAL_SUPPORTED**: ≥1 domain PRIMARY-`FOR`.
     - **EVAL_REFUTED**: no domain PRIMARY-`FOR` and every reportable domain is
       PRIMARY-`AGAINST` with adequate in-experiment power (Step 5.6).
     - **INCONCLUSIVE**: no `FOR`, but ≥1 reportable domain cannot be read cleanly
       `AGAINST` (thin events, directional imbalance, <3 instruments, or
       `INCONCLUSIVE_SECONDARY_UNSTABLE`).
  3. **Companion + secondary** annotate but never flip the PRIMARY.
  4. **Governance routing**: `EVAL_REFUTED` → `FAMILY_REVIEW` (Phase 006 §7).
  5. **Interpretation bound (Finding 7)**: EXP-021 already established a *positive*
     event-timing reaction at fixed horizon, so a PRIMARY `EVAL_REFUTED` is a
     statement about **the strategy as a whole (entry timing + EXP-022 exit)** vs. a
     same-exit matched control — **not** "the AVWAP bounce event has no edge."
     Record this explicitly to avoid the framing-review §6 overreach.
- **Expected output**: `run_metadata.json` (`overall_verdict`, per-domain PRIMARY
  verdicts, secondary `calibrated`/agreement, dependency + alignment + fence flags,
  seeds, determinism replay).

## Visualisations (4 / 4)

1. **PRIMARY per-domain expectancy forest** (`plots/event_expectancy.png`): lifetime
   matched-control excess (bps) with 95% regime-cluster bootstrap CI per domain,
   reference line at 0; annotate n_events, Holm-p, verdict; small inset showing the
   pyramid vs non-pyramid split contribution.
2. **Equity companion** (`plots/equity_companion.png`): strategy vs exposure-matched
   baseline cumulative log-equity (key comparison, same exposure), with 100% buy-hold
   as annotated exposure-mismatched context.
3. **Event-count / direction / pyramid diagnostic** (`plots/event_diagnostics.png`):
   per-domain reportable events split by direction and by `is_pyramid_bounce`, with
   the ≥30/≥8 thresholds marked; instrument distribution panel.
4. **Verdict summary — PRIMARY vs SECONDARY** (`plots/verdict_summary.png`):
   traffic-light per-domain PRIMARY verdict with effect/CI/Holm-p, alongside the
   SECONDARY effect annotated with its `calibrated` flag (so a non-calibrated
   secondary is visibly discounted), and the Step-4 fixed-horizon `{1,3,6}` anchor
   vs the EXP-021/027 reference.

## Interpretation Guide

- ≥1 domain PRIMARY-`FOR` (`effect>0`, `CI_low>0`, `Holm_p ≤ 0.05`, secondary-horizon
  stable) → **EVAL_SUPPORTED**: the faithful selective AVWAP strategy has a positive
  per-event edge under a fit-for-purpose, in-envelope yardstick; the EXP-023 negative
  was a framing/dilution artifact.
- No domain `FOR`, all reportable domains `AGAINST` with adequate in-experiment power
  → **EVAL_REFUTED**: under the correct yardstick the strategy-as-a-whole (entry +
  EXP-022 exit) shows no excess over a same-exit matched control. **Not** a statement
  that the bounce event has no edge (EXP-021 shows it does at fixed horizon); the
  likely locus is the exit rule (EXP-024: trend-change cuts losers). Routes to
  FAMILY_REVIEW.
- No `FOR` but ≥1 reportable domain not cleanly `AGAINST` → **INCONCLUSIVE**.
- SECONDARY: if `calibrated` and it agrees with PRIMARY, it strengthens the read; if
  it disagrees, prefer the PRIMARY and discuss the asymmetry; if `NOT_CALIBRATED`,
  ignore it for the verdict (record only).
- Companion: a negative exposure-matched advantage alongside a PRIMARY `FOR` is a
  fragility caveat (non-gating); a positive companion alongside `AGAINST` is null
  noise, not a hidden edge.
- Never report percentage improvement over a ~0 control mean — report bps effects,
  absolute rates, and CIs.

## Complexity Check

- **Statistical tests: 4 / 4** — (1) regime-cluster bootstrap CI; (2) stratified
  paired sign-permutation + Holm; (3) event-count / reportability table
  (descriptive); (4) equity companion bootstrap difference (reuses test 1). The
  Step-4 fixed-horizon excess, the Step-6 placebo-null check, and the SECONDARY
  construction all **reuse tests 1–2's machinery** (calibration/diagnostic
  applications) — no new test type.
- **Visualisations: 4 / 4** — expectancy forest; equity companion; event/pyramid
  diagnostic; PRIMARY-vs-SECONDARY verdict summary.
- **New code modules: 1 / 1** — `python/experiments/EXP-028/code/run_experiment.py`,
  importing the frozen inference tail from `EXP-027/code/event_method.py` (hash-guarded
  over the named functions). No new/modified `python/src/xen/` module.

## Implementation Safety Constraints

- **Frozen inference tail only**: import and hash-guard the named EXP-027 inference
  functions; abort `FROZEN_INFERENCE_MODIFIED` on mismatch. Do **not** whole-file
  hash. Re-implement return/eligibility code as tabulated above.
- **PRIMARY is binding**: the verdict is the EXP-022 symmetric own-exit lifetime
  excess through the frozen tail. SECONDARY/companion never override it.
- **SECONDARY gated by its own null**: report the secondary with weight only if its
  predeclared placebo-null check (run before reading the real secondary excess) shows
  FPR ≤ α₀ and null-excess ≈ 0; else `NOT_CALIBRATED`, zero weight.
- **Pyramids included**: predeclared, justified as closer-to-original + matching the
  reused EXP-020/021/022 observations; `is_pyramid_bounce` reported as a diagnostic
  split; regime-cluster bootstrap absorbs the clustering.
- **Index alignment**: identical per-instrument `Symbol`-keyed, latest-sorted source
  selection as EXP-020; hard value-level alignment assertion (`CloseTime`/`Close` at
  `trigger_idx`, `start_idx`, `completion_idx`) before any return; abort on mismatch.
- **Holdout fence**: first-70% lazy slice; every trigger/start/completion index inside
  the slice; right-censored (`unfinished`) events excluded with a diagnostic count.
- **Look-ahead**: control selection uses regime id, anchor age, and trigger-bar
  timestamp only; lifetime/forward closes are outcomes; note that the control-window
  *length* in the SECONDARY equals the event's realized hold (an outcome) — this is
  why the SECONDARY needs its own null calibration and is non-binding.
- **Real-price discipline**: all returns are direction-signed log returns on real
  domain `Close` (bps). No synthetic chart prices; no costs/stops/sizing (event-level
  edge test, not P&L).
- **MDE units**: EXP-027 MDE (1/4/32 bps) applies only to the Step-4 fixed-horizon
  anchor; it is **not** the power threshold for the lifetime PRIMARY (define AGAINST
  power from in-experiment CI half-width + counts).
- **Zero-baseline**: excesses are bps vs matched-control means; never a percentage
  over a ~0 baseline; non-finite ratios reported as-is, never 0.
- **Degenerate guards**: exclude events with missing exit (right-censored),
  degenerate prices (≤0/NaN), or <`MIN_CONTROLS`; record every exclusion; never
  silently drop.
- **Determinism**: all randomness via `seed_for(EXPERIMENT_ID, domain, purpose)`;
  one-domain replay asserts byte-identical results; record in `run_metadata.json`.
- **Performance**: lazy Polars load; in-memory after the slice; `tqdm` over event/
  draw loops; reuse the Step-3 paired arrays for the companion (no heavy reloads).
