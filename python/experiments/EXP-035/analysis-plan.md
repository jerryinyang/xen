# Analysis Plan: Experiment EXP-035 — TRAIN-Only Conditioning Characterisation (Clinical-Trade Dimensions)

## Objective

Characterise, on TRAIN only, whether the faithful strategy's per-event **absolute
net** expectancy (frozen CONSERVATIVE costs + predeclared financing) varies
materially and stably across three predeclared dimensions — %completion-to-target
at confirmation (C1), session (C2), trailing volatility regime (C3) — and emit the
design-§8.1 G1 qualification flag per domain × dimension. **Hard no-selection
rule:** no stratum, rule, or threshold is chosen here; flags only. Rule-freezing
belongs to the EXP-036 Tier-B scope.

## Data Wiring

- `EXP-022/results/lifetime_observations.csv`, `role = event`,
  `reportable_event = true`, joined 1:1 to `EXP-020/results/avwap_events.csv`
  (instrument/domain/regime_id/trigger index/pyramid flag; zero unmatched rows is a
  hard assert — unmatched rows are a data defect, not a filter).
- Rebuilt domain series (EXP-031-identical; bar counts == EXP-020 metadata) for
  completion timestamps and the ATR covariate.
- **TRAIN + containment:** `train_cutoff_idx = floor(0.7 × n_domain_bars)` per
  (instrument, domain); an event is included iff `completion_idx ≤
  train_cutoff_idx` (the BTC lifetime completes inside TRAIN). Exclusion counts
  disclosed. TEST and holdout never read.
- Outcome per event: `net_e = lifetime_bps_e − RT_cons_i − financing_e`, financing
  identical to EXP-034 Step 2 (shared helper).
- Frozen `event_method.py` tail, pinned hash `e50873d12a9f68d9`; G1 constants
  α_G1 = 0.10, SNR floor 1.0.

## Methodology

### Step 1 — Covariate construction (all causal at trigger time)

- **Method**:
  - **C1**: `c1 = 1 − dir_signed(favorable_target_at_trigger − trigger_close) /
    band_spread_at_trigger` (every term an at-trigger column). Sanity disclosure:
    distribution of c1, share outside [0, 1] (possible when remaining distance
    exceeds the band spread — kept, not clipped; terciles handle tails).
  - **C2**: UTC hour of `trigger_time` → Asia [00, 08), London [08, 16),
    NY [16, 24).
  - **C3**: ATR(14) (standard true range, rebuilt domain bars, strictly ≤ trigger
    timestamp) expressed as percentile rank within the trailing 90-calendar-day
    window of the same instrument×domain series; events with < 30 days of history
    excluded from C3 only (disclosed).
- **Why this method**: all three are computable from existing artifacts with zero
  look-ahead; band-spread normalization (C1) and percentile ranking (C3) make bins
  cross-instrument comparable so per-domain pooling is legitimate.
- **Simpler alternative considered**: raw remaining-bps for C1 / raw ATR for C3 —
  rejected; both scale with instrument price/vol levels, making pooled terciles
  instrument-composition artifacts.
- **Assumptions**: band geometry columns are at-trigger (EXP-020 provenance,
  invariant-checked there).
- **Expected output**: one tidy per-event TRAIN frame (event id, domain,
  instrument, direction, regime cluster, c1, c2, c3, net_e); covariate summary
  table.

### Step 2 — Binning and reportability floors

- **Method**: C1/C3 → TRAIN-quantile terciles pooled per domain, boundaries
  computed once and recorded in `results/tercile_boundaries.csv` (frozen on
  emission); C2 → fixed UTC bins. Floors: a bin with < 30 events (5m/1h) or < 15
  (4h) is `unreportable`; a domain×dimension with any unreportable bin reports
  descriptively but is **G1-ineligible**. Per-bin instrument composition disclosed
  (a bin dominated by one instrument is flagged `composition_skewed` — descriptive
  flag, interpretation caveat, not a gate).
- **Why this method**: predeclared bins are the anti-overfitting backbone;
  composition disclosure guards against reading an instrument effect as a
  dimension effect.
- **Simpler alternative considered**: per-instrument terciles — rejected; bins of
  ~3 events on 4h are meaningless and the normalizations in Step 1 already handle
  comparability.
- **Assumptions**: pooling across instruments after normalization; flagged where
  composition skew makes it doubtful.
- **Expected output**: bin assignments; floor/eligibility table.

### Step 3 — Per domain × dimension contrast and materiality (the §8.1(i)–(ii) read)

- **Method**: bin means of `net_e` with frozen regime-cluster bootstrap CIs (1000
  resamples, clusters within (instrument, direction) strata). Ordered dims (C1,
  C3): the candidate is the better-net tercile end (sign-complete reading of
  "top-vs-bottom"); Δ = candidate-minus-anti tercile mean; **monotonicity** = weak
  ordering of the three bin point estimates (either direction). Session (C2):
  candidate bin = max-net bin; contrast = candidate-vs-rest; **omnibus** =
  between-bin spread statistic (max pairwise |difference|).
  **Contrast CI (amended 2026-06-10, F06):** from a single **joint** cluster
  resample — regime clusters drawn once per replicate within each (instrument,
  direction) stratum over the union regime universe of both bins, with both bin
  means formed from the same resampled clusters. Two independent bin bootstraps
  would mis-scale the contrast CI (the SNR denominator) where a regime spans bins.
  **Materiality (§8.1 i)**: Δ (or candidate contrast) ≥ its own 95% CI half-width,
  AND top/candidate-bin net point > 0.
- **Why this method**: the cluster bootstrap is the frozen dependence-aware
  estimator; SNR ≥ 1 is the design's lenient-but-quantified materiality floor.
- **Simpler alternative considered**: Kruskal-Wallis across bins — rejected as the
  materiality leg; it tests distributional difference, not economic size, and
  ignores clustering. (Its permutation analogue appears in Step 4 as the C2
  omnibus.)
- **Assumptions**: regime clusters capture within-domain dependence (standing
  EXP-027 calibration).
- **Expected output**: `results/characterisation.csv` (domain × dimension × bin:
  n, mean net, CI; plus Δ, Δ CI, SNR, monotonicity flag).

### Step 4 — Permutation p for the Holm leg (§8.1 iv)

- **Method**: one-sided permutation p (1000 permutations) for the Step-3 contrast:
  bin labels permuted across events **within (instrument, direction) strata** —
  the frozen machinery's strata, clarifying the scope's "regime-cluster strata"
  wording: regime clusters remain the *bootstrap resampling unit*; permutation
  strata are (instrument, direction), exactly as in EXP-031's stratified
  permutation. **Selection-aware statistics (amended 2026-06-10, F05):** because
  the observed candidate bin is data-selected, the permutation statistic
  re-selects by the same max rule inside every permutation — ordered dims:
  `|mean(high) − mean(low)|`; sessions: `max_b(mean_b − mean_rest_b)`; omnibus:
  between-bin spread (already selection-aware). Holding the observed candidate
  fixed under the null would be anti-conservative (~2× for ordered dims, more for
  sessions) — beyond the cluster-correlation caveat below. Holm across the 3
  dimensions within each domain at α_G1 = 0.10.
  **Disclosed caveat (predeclared):** event-level label permutation under
  within-cluster correlation remains anti-conservative; this is acceptable because
  §8.1 is a conjunction — the binding materiality evidence is the cluster-aware
  SNR criterion (Step 3), and (iv) serves as a multiplicity screen, not the sole
  significance leg.
- **Why this method**: keeps §8.1(iv) well-defined with the same operator family
  the programme already uses; the conjunction structure contains its known
  weakness.
- **Simpler alternative considered**: cluster-level label permutation — rejected:
  C3 is near-constant within clusters, making the within-cluster null degenerate
  and cluster-size heterogeneity makes between-cluster label exchange ill-posed.
- **Assumptions**: exchangeability of bin labels within strata under the null of
  no association (stated; weakened by clustering, per the caveat).
- **Expected output**: raw and Holm-adjusted p per domain × dimension.

### Step 5 — Split-half stability (§8.1 iii) and qualification assembly

- **Method**: chronological split of TRAIN at the per-domain median event
  timestamp; recompute bin means and Δ per half **using the frozen full-TRAIN
  tercile boundaries** (boundaries are not re-estimated per half — stability of
  the *effect*, not the binning, is under test). Stability = same top/candidate
  bin in both halves AND Δ > 0 in both halves. Assemble the final flag:
  QUALIFIED iff (i) ∧ (ii) ∧ (iii) ∧ (iv) and the dimension is floor-eligible.
- **Why this method**: split-half is the simplest temporal-stability check and was
  fixed in design §8.1; freezing boundaries isolates one moving part.
- **Simpler alternative considered**: rolling-window stability — rejected; more
  parameters, same question, budget-violating.
- **Assumptions**: two halves are a coarse but assumption-free regime probe.
- **Expected output**: `results/g1_qualification.csv` (domain × dimension: every
  sub-criterion verdict + QUALIFIED flag); determinism replay flag in
  `run_metadata.json`.

## Visualisations (5 / 5 budget)

1. **C1 bin means with CIs per domain** — the %completion gradient.
2. **C2 bin means with CIs per domain** — the session pattern.
3. **C3 bin means with CIs per domain** — the vol-regime gradient.
4. **Split-half stability panel** — Δ per half per domain × dimension; instability
   visible at a glance.
5. **Qualification matrix** — domain × dimension grid coloring each §8.1
   sub-criterion and the final flag.

## Interpretation Guide (predeclared)

- QUALIFIED on a dimension ⇒ that dimension earns a single frozen rule slot in the
  EXP-036 Tier-B scope (rule frozen there, from these TRAIN statistics, before any
  TEST read). Multiple qualifications ⇒ conjunctive rules allowed only if
  predeclared at Tier-B scope time.
- Zero QUALIFIED dimensions ⇒ the conditioning lever is empty on this entry
  substrate; B1 does not open, and the phase outcome leans on A1/B2 (design §9).
  This is a valid outcome, **not** permission to add dimensions, re-bin, or relax
  α_G1.
- A material-but-unstable read (fails iii only) is hypothesis-generating: report
  it honestly as such; it does not qualify and must not be "rescued".
- 4h is expected to be floor-fragile (~40 events per tercile); a 4h-ineligible
  outcome is predeclared as likely and carries no evidential weight against the
  dimension on other domains.
- A qualified gradient driven by one instrument (composition flag) is reported with
  that caveat; the Tier-B rule it motivates should anticipate instrument
  interaction in its declared TEST family.

## Implementation Safety Constraints (for `experiment-developer`)

- All covariates strictly at-or-before trigger timestamp; ATR window advances by
  calendar time; never read bars past `trigger_idx` for covariates or past
  `completion_idx` for outcomes.
- Build the tidy frame once; every test is a pure function of it (no re-loading
  per dimension).
- One shared bootstrap resample-index set per domain across dimensions and bins.
- Tercile boundaries computed once, written to results, then treated as frozen
  constants (split-half reuses them; no re-estimation).
- Zero-baseline: absolute bps everywhere; bin contrasts are differences, never
  ratios; floors guard small-n bins; `unreportable` bins propagate to
  G1-ineligibility, never silently dropped.
- Permutations and bootstrap bounded at 1000 each; `tqdm` over domain × dimension;
  helpers return data; no import-time side effects.
- The qualification assembly reads only emitted sub-criterion columns — no
  recomputation at assembly time (prevents drift between the flag and its
  evidence).

## Complexity Check

- Statistical test families: 3 / 3 (cluster-bootstrap CIs/contrasts; permutation
  tests — pairwise + omnibus as one family; split-half stability).
- Visualisations: 5 / 5.
- New modules: 1 / 1 (covariate construction + characterisation orchestration;
  financing helper shared with EXP-034).
