# Analysis Plan: Experiment EXP-031 — AVWAP Edge Isolation (Entry-Timing vs Exit-Rule)

## Objective

Decompose the EXP-028 PRIMARY per-event matched-control excess (+5.78 / +23.38 /
+69.02 bps on 5m / 1h / 4h, EVIDENCE_FOR) into an **entry-timing** contribution and an
**exit-rule** contribution, per domain, and assign each domain a predeclared
attribution label (ENTRY_DOMINANT / EXIT_DOMINANT / MIXED / INCONCLUSIVE /
MIXED_UNRESOLVED) under the sign-complete classifier in the scope.

This is a **gross mechanism decomposition**, not a tradability screen and not an edge
verdict. The total being decomposed is already established (EXP-028, cTrader-confirmed
by EXP-029). The falsifiable content is **whether the split resolves**. The experiment
runs regardless of EXP-030 (design §3) and consumes **0 candidate-screening slots**
(`CF-AVWAP-001/DIAG-003`).

The decomposition is exact and additive **by construction** — `X_full = X_entry(H) +
X_exit(H)` per event — so there is no hidden residual; the only statistical questions
are (a) which legs are distinguishable from zero and (b) their relative share.

---

## Data Wiring (the substrate, made unambiguous)

All inputs are existing first-70%-analysis-set artifacts; **no new cTrader run, no new
event/exit logic** (scope execution-path declaration). Inputs:

- **`EXP-022/results/lifetime_observations.csv`** — one row per (event or control)
  with `role ∈ {event, control}`, `instrument`, `domain`, `regime_id`, `direction`,
  `start_idx`, `event_trigger_idx`, `start_close`, `lifetime_bps`, `reportable_event`,
  `is_pyramid_bounce`. This is the **exact EXP-028 PRIMARY population** (pyramids
  included). `lifetime_bps` is the band-target/trend-change (**BTC**) lifetime return,
  already direction-signed in bps.
- **Control→event pairing key**: `(instrument, domain, event_trigger_idx)`. Every
  `role=control` row shares its event's `event_trigger_idx`; controls are matched to
  exactly one event. (Verified in raw data: event row `start_idx=event_trigger_idx`,
  control rows carry the parent `event_trigger_idx` with their own earlier `start_idx`.)
- **Rebuilt real domain Close series** per (instrument, domain): aggregate the
  first-70% slice of 1-minute bars with `xen.bar_aggregator.aggregate_ohlc`, using the
  **identical** domain definitions as EXP-020/022/024 (5m strict; 1h/4h
  `min_coverage=0.90`). Used only for the fixed-horizon recompute. **Verify rebuilt
  per-domain row counts reproduce EXP-020 `analysis_metadata.csv` before use** — a
  mismatch means the domain rebuild diverged and the experiment is REVISE-blocked.
- **`EXP-020/results/avwap_events.csv`, `avwap_state_summary.csv`** — `regime_id`
  strata scaffolding (already present in the lifetime rows; used to confirm strata).
- **`EXP-021/results/reaction_observations.csv`** — soft cross-check only.
- **`EXP-027/code/event_method.py`** (as reused by EXP-028) — the frozen inference
  tail (`build_strata`, `bootstrap_effect_distribution`, `permutation_p`,
  `holm_adjust`, `domain_effect`), imported or copied **unchanged**.

### Fixed-horizon return (the only new computation)

For any row (event or control) with start index `i = start_idx`, signed direction `d`,
and `start_close = close[i]`, on the rebuilt domain Close array:

```
fh_bps(row, H) = 10000 * d * ln( close[i + H] / close[i] )
```

reportable at horizon `H` **iff `i + H` lies inside the first-70% analysis slice**
(`i + H <= n_domain - 1`). Frozen horizons `H ∈ {1, 6}`; **H = 6 PRIMARY**, **H = 1
robustness companion** (the EXP-027 secondary-horizon slots — no new method object).
This matches `forward_logdiff_from_close` in `event_method.py` (log-difference of real
Close), so the recompute is method-consistent with the frozen tail.

---

## Methodology

### Step 1 — Reconstruct the EXP-028 PRIMARY total (hard validation anchor)

- **Method**: Replicate EXP-028's PRIMARY aggregation on the **full** lifetime
  population: per event, `event_BTC − mean_c(control_BTC)` over **all** that event's
  lifetime controls; aggregate by the frozen `domain_effect` (per-instrument
  event-weighted mean → equal-weight mean across reportable instruments).
- **Why this method**: Establishes that the substrate is wired correctly before any
  attribution is read. If `X_full` here does not reproduce
  `EXP-028/results/event_level_results.csv` `effect_bps` within tolerance, the
  decomposition is mis-wired (scope: "REVISE-blocked").
- **Tolerance**: |Δeffect| ≤ 0.05 bps **and** ≤ 0.5% relative, per domain (consistent
  with the EXP-029 parity tolerance class). Also reproduce `n_events`, `n_bull`,
  `n_bear` exactly.
- **Simpler alternative considered**: Trust EXP-028's number without recomputation —
  rejected; the additive decomposition is only meaningful if `X_full` is rebuilt from
  the same primitives the legs are built from.
- **Assumptions**: `lifetime_observations.csv` is the EXP-028 PRIMARY population (stated
  in scope, confirmed by EXP-028 dependency gate). No distributional assumption.
- **Expected output**: `xfull_reconciliation.csv` (per domain: rebuilt effect, EXP-028
  effect, |Δ|, rel-Δ, N match flags, PASS/FAIL).

### Step 2 — Build the three legs on the common-control intersection (exact additivity)

Per-event additivity `X_full = X_entry(H) + X_exit(H)` holds **only if the same event
and the same control set feed both `X_full` and `X_entry(H)`**. Therefore the
decomposition is computed on a **common, H-specific population**:

- **Common control set** for an event at horizon `H`: that event's controls that have
  **both** a valid `lifetime_bps` **and** a reportable `fh_bps(·, H)`
  (`control_start_idx + H` inside the slice).
- **Decomposition-reportable event** at horizon `H`: `reportable_event=true`, has a
  reportable `fh_bps(event, H)`, **and** retains `≥ MIN_CONTROLS = 3` common controls
  (the EXP-027/028 reportability floor on controls).

On that common set, per event:

| Leg | Per-event quantity | Reuses / anchors to |
|-----|--------------------|---------------------|
| **X_full*** (decomp basis) | `event_BTC − mean_cc(control_BTC)` | ~EXP-028 PRIMARY on the common set |
| **X_entry(H)** | `event_FH(H) − mean_cc(control_FH(H))` | ~EXP-028 `sec_h{1,6}_bps`; ~EXP-021 reaction |
| **X_exit(H)** | `X_full* − X_entry(H)` = `event_dH − mean_cc(control_dH)`, where `dH = BTC − FH(H)` | the exit-substitution differential |

`mean_cc` is the mean over the **common** controls. `X_exit(H)` is algebraically the
matched-control difference of the per-row **exit-substitution effect** `dH = BTC − FH(H)`,
so all three legs are matched-control differences of the *same pairing* — they go
through identical inference machinery.

- **Why a neutral fixed-horizon exit isolates entry timing**: it carries no AVWAP/band
  information and is applied identically to event and control legs, so the only varied
  factor between `X_full*` and `X_entry(H)` is the exit rule. The residual `X_exit(H)`
  is therefore the BTC exit's **differential** value on bounce-entries vs control-entries.
- **Population accounting (must be reported, not hidden)**: `N_decomp(domain, H)` ≤
  `N_full(domain)` because events within `H` bars of the slice boundary, or that lose
  controls below the floor, drop out. Report both counts per (domain, H) in
  `decomposition_results.csv`. `X_full*` on the common set is reported alongside the
  Step-1 anchor; a large divergence (> a few %) between `X_full*` and the Step-1
  `X_full` is itself a flagged diagnostic (boundary attrition), not a silent change.
- **Simpler alternative considered**: Compute `X_entry` on its own maximal population
  and subtract domain-level effects — rejected; domain-level subtraction is **not**
  per-event additive when populations/control-sets differ, so the "residual" would not
  equal a real per-event exit contribution and the sign-permutation null for `X_exit`
  would be undefined.
- **Assumptions**: matched-control exchangeability within (instrument, direction)
  regime clusters (same assumption EXP-021/028 already rely on). For `X_exit`, the
  additional stated null is "the BTC exit's incremental value `dH` is equal in
  distribution on bounce-entries and control-entries", exact under sign-permutation of
  the per-event paired `dH` differences.
- **Expected output**: per-event leg arrays feeding Step 3; `decomposition_by_instrument.csv`.

### Step 3 — Frozen EXP-027/028 inference on each leg (unchanged machinery)

For each domain, each leg `∈ {X_full*, X_entry(H), X_exit(H)}`, each `H ∈ {1, 6}`:

- **Method**: the frozen tail from `event_method.py`, applied unchanged —
  1. `domain_effect`: instrument-averaged equal-weight effect (the point estimate).
  2. `build_strata` + `bootstrap_effect_distribution`: **95% regime-cluster bootstrap
     CI**, 1000 resamples, regime clusters resampled with replacement within
     (instrument, direction) strata. Percentiles (2.5, 97.5).
  3. `permutation_p`: **one-sided stratified paired sign-permutation** p-value, 1000
     resamples. For `X_full*`/`X_entry` the null is the symmetric matched-control
     mean-zero null (as EXP-028/021). For `X_exit` the null is the equal-`dH`-value
     null above (sign-permutation of the paired `dH` differences — same operator,
     different paired input).
  4. `holm_adjust`: Holm step-down over the leg-p family **{entry, exit} × {reportable
     domains}** at the PRIMARY horizon H=6. `X_full*` significance is reported against
     EXP-028's existing Holm-across-3-domains claim (not re-entered into the family —
     it is the anchor, not a tested leg).
- **Why these methods (catalog-justified)**: distribution-free bootstrap CI +
  permutation p are the catalog-preferred non-parametric tools; the **cluster**
  bootstrap and **stratified paired** permutation are mandatory here because returns
  are regime-clustered and instrument-heterogeneous — i.i.d. resampling would
  understate uncertainty. These are exactly the frozen EXP-021/027/028 estimators, so
  the inference transfers without recalibration.
- **Simpler alternatives considered**:
  - *Wilcoxon signed-rank on per-event diffs* — rejected: assumes symmetric independent
    differences, ignores regime clustering and instrument stratification.
  - *t-test / normal CI* — rejected: normality + i.i.d. (catalog "methods to avoid").
  - *Plain i.i.d. bootstrap* — rejected: ignores within-regime dependence the frozen
    estimator already absorbs.
- **Assumptions & fit to financial data**: within-(instrument, direction) regime
  clusters are the resampling unit (handles autocorrelation/overlap); no normality,
  stationarity, or i.i.d. across events assumed. Exchangeability of the *sign* of
  matched-control differences under the null is the only structural assumption — the
  same one EXP-021/028 stand on.
- **Leg-significance** (per scope): a leg is **leg-significant** iff bootstrap
  `CI_low > 0` **AND** Holm-adjusted sign-permutation `p ≤ 0.05` (the EXP-028 dual
  requirement). `α₀ = 0.05`.
- **Expected output**: `decomposition_results.csv` rows (per domain × H: effect, ci_low,
  ci_high, ci_half_width, raw_p, holm_p, leg_significant, n_events, n per direction,
  n_instruments, for each of X_full*/X_entry/X_exit).

### Step 4 — Predeclared attribution classifier (threshold rule, not an NHST)

- **Method**: apply the scope's **sign-complete** classifier per domain at **H=6**,
  evaluated **only when `X_full` is EVIDENCE_FOR on that domain** (a real total
  exists to attribute). With `s_entry = X_entry / X_full`, `s_exit = X_exit / X_full`
  (`s_entry + s_exit = 1` by additivity), and the predeclared **0.67** dominance cut,
  emit ENTRY_DOMINANT / EXIT_DOMINANT / MIXED / MIXED_UNRESOLVED / INCONCLUSIVE exactly
  per the scope's ordered condition table (including the >100%/negative-leg branches).
- **Shares are computed only when `X_full* CI_low > 0`** — denominator is the
  significant nonzero total, so there is **no division by a near-zero or zero baseline**
  (zero-baseline discipline; no percentage-improvement-against-zero metric).
- **H=1 is reported as a robustness companion**: a label that flips between H=1 and H=6
  is a **reported finding** (pushes toward MIXED / "unresolved"), never grounds to
  select the favorable horizon.
- **Why not a test**: the classifier is a deterministic threshold map over already-
  computed CIs/p-values; it adds **0** NHST to the budget.
- **Expected output**: per-domain label (H=6) + H=1 companion label + agreement flag in
  `decomposition_results.csv` / `run_metadata.json`.

### Step 5 — Determinism & soft cross-checks

- **Determinism replay**: re-run the full pipeline with the same fixed seeds; assert
  bit-identical leg effects, CIs, p-values, and labels (record in `run_metadata.json`).
- **Soft anchors (non-gating)**: report `X_entry(1)`/`X_entry(6)` against EXP-028
  `sec_h1_bps`/`sec_h6_bps` and against EXP-021 fixed-horizon reaction excess; large
  unexplained divergence is a caveat to surface, not a gate (populations differ by the
  common-control intersection).

---

## Visualisations (4 / 4 budget)

1. **`decomposition_stacked.png`** — per domain, stacked `X_full = X_entry + X_exit`
   bars with bootstrap CI whiskers on each leg, at **H=6 (primary)** and **H=1
   (companion)** side by side. Answers: *how does the total split, and is the split
   horizon-stable?*
2. **`attribution_shares.png`** — per domain `s_entry` / `s_exit` with the **0.67
   dominance band** marked, H=6 vs H=1. Answers: *which leg dominates and by how much?*
   (Shares plotted only for EVIDENCE_FOR domains; others annotated "no significant total".)
3. **`exit_substitution.png`** — per domain, the **event vs control** mean
   exit-substitution effect `dH = BTC − FH(H)` (the mechanism behind `X_exit`).
   Answers: *does the BTC exit add/subtract more on bounce-entries than on controls?*
   Reconciles with the retained EXP-024 "trend-change exits cut losers, not winners"
   finding.
4. **`attribution_summary.png`** — per-domain label dashboard (H=6 label, H=1 label,
   agreement flag, leg-significance ticks). Answers: *the bottom-line read per domain.*

All plots consume bounded per-domain summary arrays produced by the analysis pass — no
re-load or re-aggregation of raw bars solely for plotting.

---

## Interpretation Guide (predeclared, before results)

Per domain, at **H=6**, only when `X_full*` is EVIDENCE_FOR (`CI_low > 0` AND Holm
`p ≤ 0.05`); otherwise **INCONCLUSIVE**:

- Both legs leg-significant, `s_entry ≥ 0.67` → **ENTRY_DOMINANT**.
- Both legs leg-significant, `s_exit ≥ 0.67` → **EXIT_DOMINANT**.
- Both legs leg-significant, `max(s_entry, s_exit) < 0.67` → **MIXED**.
- Only X_entry leg-significant → **ENTRY_DOMINANT** (exit indistinguishable from 0).
- Only X_exit leg-significant → **EXIT_DOMINANT** (entry indistinguishable from 0).
- `X_entry < 0` (entry negative under neutral exit; exit > 100%) → **EXIT_DOMINANT**
  (note: entry leg negative).
- `X_exit < 0` (BTC exit a differential drag; entry > 100%) → **ENTRY_DOMINANT**
  (note: exit is a differential drag). *(This is the a-priori-plausible 5m branch:
  EXP-028 `sec_h6 = 8.62 > X_full = 5.78` ⇒ `X_exit(6) ≈ −2.84 < 0`.)*
- Neither leg leg-significant though X_full FOR → **MIXED_UNRESOLVED**.

**Phase-outcome mapping:**

- **ISOLATION_READ — resolved**: primary domain (5m) yields a definite label
  (ENTRY/EXIT/MIXED) and the H=1 companion does **not** contradict the H=6 label.
- **ISOLATION_READ — unresolved**: primary domain INCONCLUSIVE or MIXED_UNRESOLVED, or
  H=1 and H=6 give contradictory labels. Reported honestly as "edge present, split
  unresolved at this power/construction." Does **not** authorize a new horizon, a new
  neutral-exit definition, or a re-run with different legs.
- **Cross-domain divergence** in the entry/exit split is a **reported finding**, never
  averaged into a single number.
- **Hard gate**: if Step-1 `X_full` fails the EXP-028 reconciliation tolerance, **no
  attribution is read** (REVISE-blocked) until it reconciles.

---

## Implementation Safety Constraints (for `experiment-developer`)

- **Holdout**: slice the **first 70%** of 1-minute bars by `CloseTime` order **before**
  any domain aggregation (lazy `scan_parquet().sort("CloseTime").slice(0, cutoff)`); the
  final 30% is never loaded, aggregated, or referenced. An event/control with no real
  Close at `start_idx + H` inside the slice is **non-reportable at that horizon** —
  never extend the Close array into the holdout to fill it.
- **Temporal ordering & alignment**: order by `CloseTime`; align everything by
  **`start_idx` into the rebuilt domain array** (which is itself timestamp-ordered),
  never by raw bar index across views. Verify rebuilt domain row counts == EXP-020
  `analysis_metadata.csv` before computing any `fh_bps`.
- **Real-price discipline**: all returns (BTC `lifetime_bps` and `fh_bps`) are
  direction-signed log returns on **real domain Close**. No HA/Renko/Line Break prices
  in any role.
- **Denominators**: per-event matched events; per-instrument event-weighted mean →
  equal-weight across **reportable** instruments (`≥ 3 of 4`, `≥ 30 events/domain`,
  `≥ 8/direction`) — identical to EXP-028. Report `N_full` and `N_decomp(H)` separately.
- **Zero-baseline**: compute `s_entry`/`s_exit` **only** when `X_full* CI_low > 0`;
  otherwise emit the share fields as non-finite / "n/a" and label INCONCLUSIVE. Never
  divide by a near-zero total.
- **Frozen machinery**: import or unchanged-copy `event_method.py`
  (`domain_effect`, `build_strata`, `bootstrap_effect_distribution`, `permutation_p`,
  `holm_adjust`). Do **not** modify the estimators. No new/modified `python/src/xen/`
  module.
- **Determinism & bounded iteration**: fixed seeds (record in metadata); 1000 bootstrap
  + 1000 permutation resamples (bounded, as frozen); the bootstrap/permutation keep
  their existing **chunked-vectorized** form — do not re-vectorize the regime-cluster
  resampling in a way that changes the cluster unit or the paired-sign semantics.
- **Progress**: `tqdm` over the outer (domain × instrument) and leg loops; concise
  logging; helper functions return data rather than printing.
- **Additivity assertion**: after building legs, assert
  `max|X_full* − (X_entry + X_exit)| < 1e-9` per event (guards the construction).
- **Vectorization discipline**: the `fh_bps` recompute and control-mean aggregation are
  safely vectorizable (gather + segment mean); keep them vectorized but causally
  equivalent. The frozen inference stays as-is.

---

## Complexity Check

- **Statistical tests**: 3 / 3 — the three legs (X_full* / X_entry / X_exit) through the
  shared frozen bootstrap + sign-permutation + Holm machinery (X_full* reuses EXP-028's,
  X_entry largely reuses EXP-021's). The attribution rule is a predeclared threshold
  classifier, **not** an additional NHST.
- **Visualisations**: 4 / 4.
- **New modules**: 1 / 1 — `python/experiments/EXP-031/code/run_experiment.py` only;
  frozen inference reused by import/unchanged copy.
