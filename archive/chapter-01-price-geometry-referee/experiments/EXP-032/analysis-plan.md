# Analysis Plan: Experiment EXP-032 — One-Shot Holdout Confirmation of Package B (EURUSD-4h, FH H\*=12, all_legs)

> **Revision 1 (2026-06-10, pre-execution, via the Stage-4 REVISE route).**
> Resolves external review findings F01–F05 BEFORE any code run. Changes are
> machinery, wording, and disclosure only — **no frozen parameter, estimand,
> population rule, or inference quantity is touched**: (F01) per-event holdout
> outcomes are persisted (`holdout_events.csv`) before the verdict file, which is
> written last as the completion marker; post-verdict rendering/audit read only
> persisted artifacts; (F03) H1 and H2 are separate process invocations with a
> mechanical inter-phase check (machinery defects only — H2 runs regardless of
> entry attributes); (F02) hard-stop classes and consequences are predeclared in
> the Phase 009 `execution-addendum.md` (guard failures before H2 never spend the
> shot); (F04) the "causal entry attributes" wording is corrected for control
> counts (see Step 2) with a mandatory identifiability disclosure; (F05) a
> calibration-fidelity caveat is predeclared in the Interpretation Guide.

## Objective

Evaluate, **exactly once**, the Package-B candidate's net per-event expectancy on
the global holdout stratum (final 30% of the full EURUSD dataset — the
programme's single sanctioned holdout read, Phase 009 design §1): EURUSD-4h AVWAP
bounce events (EXP-020/022 population rule), fixed-horizon exit at H\* = 12
domain bars, all_legs pyramid policy, frozen CONSERVATIVE RT cost 3.0 bps plus
financing 0.6 bps/day (adverse-side, fractional calendar days), frozen EXP-027
regime-cluster bootstrap. **No selection of any kind occurs inside EXP-032** —
every parameter is inherited frozen (EXP-037 `frozen_selection.json`, hash
`2bbbf65b…770b0fea`; EXP-030 costs; EXP-027 tail `e50873d12a9f68d9`). The binding
verdict is mechanical on a single cell (family of 1, no Holm): HOLDOUT_CONFIRMED
iff `ci_low_1s > m_cell` AND one-sided bootstrap p ≤ 0.05; HOLDOUT_REFUTED iff
two-sided CI_high < 0; else HOLDOUT_INCONCLUSIVE. The shot is spent on any
outcome.

## Data Wiring

EXP-037's data wiring is incorporated by reference, with one structural change:
the event population is **regenerated over the full EURUSD series** (analysis +
holdout) instead of read from analysis-set artifacts, because the holdout events
do not exist in any prior artifact.

- **Source:** full EURUSD 1-minute series (latest
  `data/timebars/timebars_EURUSD_*.parquet`), sorted by `CloseTime`. **This is
  the sanctioned EURUSD holdout read (Phase 009 design §5); no other
  instrument's file is loaded at all in this experiment.**
- **Boundary:** `analysis_rows = int(total_rows × 0.7)`; boundary timestamp =
  CloseTime of 1-minute row `analysis_rows − 1`. An event is HOLDOUT iff its
  entry-confirmation (trigger) close time > boundary; ties → analysis stratum.
  Membership keys on the causal entry bar (R1.3 convention carried forward).
- **Domain rebuild:** 4h domain series via `xen.bar_aggregator`,
  EXP-031/033/037-identical parameters, built **once over the full series**.
  The analysis-prefix bars (CloseTime ≤ boundary) must be identical to the
  analysis-only rebuild EXP-037 used (prefix-equality assert: aggregation is
  causal/clock-aligned, so the prefix cannot depend on later rows; any drift is
  a hard stop).
- **Event regeneration:** `xen.avwap.generate_avwap_events` (frozen EXP-020
  parameters, unchanged) run as the sequential stateful stream over the full 4h
  domain frame, followed by the EXP-022-identical event/control record
  construction and **reportability rule** (`reportable_event` = ≥ MIN_CONTROLS
  same-regime matched controls, EXP-022 constants unchanged). The binding
  population is `role = event`, `reportable_event = true`, pyramids included
  (all_legs) — the same mechanical rule that defined the EXP-028/030/034/037
  population, applied across the boundary as a **deterministic ex-post population
  rule, frozen since EXP-022** (R1 correction: control candidacy spans the regime
  interval after the trigger, so reportability depends on post-entry regime
  evolution and the series truncation point — it is NOT identifiable at entry
  time; see the Interpretation Guide disclosure). Holdout event counts
  before/after the reportability filter are disclosed in H1.
- **FH outcome (EXP-033/037-identical construction, computed only in H2):**
  `fh_bps(e) = 10000 × d × ln(close[entry_idx + 12] / close[entry_idx])` on the
  full-series 4h rebuild, truncated to the last available bar when
  `entry_idx + 12` exceeds the series (truncated share disclosed — note the
  full-series end is the true data end, so truncation here is real, not a
  holdout fence). `net_e = fh_bps(e) − 3.0 − 0.6 ×
  elapsed_calendar_days(trigger_close_time, fh_exit_close_time)`; financing
  helper is the EXP-034 pure function (`xen.financing`), reused verbatim.
- **Frozen inference:** `event_method.py` tail, pinned hash `e50873d12a9f68d9`
  (hard assert), 1000-resample regime-cluster bootstrap, single-instrument
  specialization (regime clusters resampled within direction strata —
  EXP-034/037/038-identical).

## Methodology

### Step 1 — Integrity guards (hard gate; all PASS before anything else is emitted)

- **Method:**
  (a) **Hash pins:** EXP-037 `frozen_selection.json` content hash ==
  `2bbbf65ba0a3d9d50ad0c988e3845bdae93edc863756c810ff4f53f3770b0fea` (H\*=12,
  all_legs, and the 27/12 stratum manifest are read only from it); frozen-tail
  hash == `e50873d12a9f68d9`.
  (b) **Analysis-stratum reconciliation (lineage proof):** the regenerated
  full-series population, restricted to trigger ≤ boundary, must reproduce the
  EXP-037 EURUSD-4h partition **exactly**: 39 events total, 27 TRAIN / 12 TEST
  under the EXP-037 boundary (`boundary_ns` 1724624340000000000), with identical
  (regime_id, direction, event_trigger_idx) keys to the EXP-037 stratum manifest
  and identical reportability flags vs
  `EXP-022/results/lifetime_observations.csv`. Any mismatch is a hard stop — the
  generator lineage is broken and the holdout read must not proceed.
  (c) **EXP-037 TEST reproduction anchor (estimator proof):** recompute
  FH(12)/all_legs nets on the EXP-037 TEST stratum (12 events, analysis data
  only) through this experiment's code path; the event-weighted mean must
  reproduce `EXP-037/results/test_verdicts.csv` EURUSD net (+40.558882 bps) to
  ≤ 0.01 bps.
  (d) **Seal assertion:** runtime disclosure of every file opened and the row
  ranges materialized; assert no non-EURUSD timebars file is opened.
  Prefix-equality of the 4h rebuild per Data Wiring.
- **Why this method:** the one-shot read is only meaningful if (i) the holdout
  events come from provably the same generative lineage G2 certified
  (reconciliation), and (ii) the outcome arithmetic is provably the audited
  EXP-037 estimator (reproduction anchor). These two guards are the holdout
  analogues of EXP-037's guards 1–2.
- **Simpler alternative considered:** trust the shared modules — rejected; the
  full-series regeneration is a new execution path over the same code, and the
  reconciliation is what proves path-equivalence on disclosed data before any
  sealed data is interpreted.
- **Assumptions:** none beyond artifact integrity.
- **Expected output:** `results/reconciliation.csv` (one row per guard:
  PASS/FAIL + measured values; all PASS required);
  `results/analysis_fh_nets.csv` (per-event disclosed-data FH(12)/all_legs nets
  for the 39 analysis events — the persisted audit/plot input, R1/F01).
- **Hard-stop handling (R1/F02):** guard failures here never spend the shot;
  classification and consequences per the Phase 009 `execution-addendum.md`
  (class a: true lineage mismatch → blocked; class b: reportability-flag-only
  drift on boundary-spanning regimes → repairable reconciliation-expectation
  defect via Stage-4 REVISE; class c: environment-drift hash mismatch → rebuild
  the recorded environment, never regenerate the manifest).

### Step 2 — H1: holdout stratum manifest (entry attributes only)

- **Method:** from the regenerated population, select holdout-stratum events
  (trigger > boundary, reportable, all_legs). Persist entry attributes only:
  event keys (regime_id, direction, event_trigger_idx, trigger close time),
  `is_pyramid_bounce`, cluster layout (per-(direction, regime_id) sizes), counts
  before/after the reportability filter, boundary timestamp, and the inherited
  frozen constants. **No FH return, lifetime outcome, net, or any
  price-difference quantity over holdout rows is computed or persisted in H1**
  — structurally enforced: the H1 function has no access to the outcome helpers.
- **Why this method:** the manifest is the freeze object — it fixes the
  population and the calibration inputs on disk before any outcome exists,
  making "predeclared before the read" checkable rather than procedural.
- **Assumptions (R1-corrected, F04):** trigger and regime attributes are causal —
  guaranteed by the generator's streaming construction (EXP-020-validated) and
  unchanged parameters. Control COUNTS (and hence `reportable_event`) are NOT
  causal at entry: they are a deterministic ex-post rule frozen since EXP-022
  (candidacy spans `(confirm_idx, end_idx]` after the trigger and depends on the
  truncation point). "Entry attributes" in this plan therefore means quantities
  computable without any price-difference/outcome arithmetic, not quantities
  knowable at entry time. Consequences: (i) guard 1b can legitimately fail on
  flags alone for boundary-spanning regimes (class b of the execution addendum);
  (ii) holdout events near the series end are systematically less likely to be
  reportable; (iii) the binding estimand conditions on ex-post reportability —
  mandatory disclosure in results.md/report.md.
- **Expected output:** holdout section of
  `results/frozen_holdout_manifest.json`; disclosure table
  `results/holdout_stratum.csv` (entry attributes only).

### Step 3 — H1: synthetic-null calibration and binding margin (R1.2 analog)

- **Method** (EXP-037 Step 3b machinery, re-targeted to the holdout cell; no
  holdout outcome contact):
  1. **Structure** (entry attributes only): the holdout stratum's
     (direction, regime_id) cluster sizes under all_legs, from Step 2.
  2. **Dispersion** (disclosed data only): from the **full-analysis** EURUSD-4h
     FH(12)/all_legs `net_e` values (all 39 events — TRAIN and TEST are both
     already-disclosed strata; computed on analysis rows only), demeaned;
     method-of-moments components — `σ_w²` = pooled within-cluster variance over
     clusters with ≥ 2 events (fallback: total variance if none);
     `σ_b² = max(0, var(cluster means) − σ_w² × mean(1/n_c))`.
  3. **Null replicates:** R = 2000; each draws `r_i = a_c + e_i`,
     `a_c ~ N(0, σ_b²)`, `e_i ~ N(0, σ_w²)` (zero true mean) on the holdout
     cluster layout, scored by the frozen 1000-resample bootstrap; record
     `(ci_low_1s, boot_p)` per replicate. Seeds namespaced
     ("EXP-032", "nullcal"); `tqdm` over replicates.
  4. **Outputs:** measured null FPR of the uncorrected dual rule
     (`boot_p ≤ 0.05 AND ci_low_1s > 0`); binding margin
     `m_cell = max(0, Q95 of null ci_low_1s)`; FPR under the margin rule.
     Margin embedded in the manifest **before** H2 can run.
- **Why this method:** the frozen bootstrap has never been Type-I-calibrated at
  a ~15-event single cell; the holdout verdict is the programme's most expensive
  consequence, so an unmeasured anti-conservative Type-I rate is the asymmetric
  risk. The margin is the same smallest mechanical correction R1.2 established
  for EXP-037/038, recomputed at this cell's structure. Using all 39
  full-analysis events for dispersion (vs EXP-037's contained-TRAIN-only) is
  predeclared and strictly more data on the same disclosed stratum; TRAIN/TEST
  separation has no force here since both are disclosed and the evaluation
  stratum is the holdout.
- **Simpler alternative considered:** reuse EXP-037's EURUSD margin (8.42 bps)
  — rejected; the margin is structure-specific (cluster count/sizes differ at
  n≈15–18 vs n=12) and recomputation is mechanical. Skip calibration — rejected
  for the same reason it was rejected in R1.2.
- **Assumptions:** Gaussian cluster null with disclosed-data variance components
  is an adequate coverage-calibration vehicle (the standing R1.2 assumption;
  components persisted for transparency).
- **Expected output:** `results/null_calibration.csv` (structure, σ_b/σ_w,
  fpr_uncorrected, margin_bps, fpr_with_margin), written before the manifest is
  finalized.

### Step 4 — Freeze-before-outcome barrier and no-second-read guard (load-bearing)

- **Method:** finalize `results/frozen_holdout_manifest.json` — experiment ID,
  inherited frozen constants (H\*=12, all_legs, RT 3.0, financing 0.6, tail
  hash), boundary timestamp, holdout stratum manifest, calibration components +
  margin, reconciliation digest, and a content hash. **H2 is a separate
  orchestration function** that (a) hard-asserts the manifest exists, parses,
  and hash-verifies; (b) reads population/margin/constants only from it; (c) is
  unreachable before the manifest write. **Recovery semantics (EXP-037
  R1.6-identical):** if the manifest already exists, the recomputed record must
  content-hash-match exactly (hard stop on mismatch); if
  `results/holdout_verdict.csv` exists, H2 refuses to run — no second read under
  any circumstance, including crashes, reruns, or audit requests.
- **Why this method:** the disk barrier converts the one-shot promise into a
  checkable artifact; this is the same control EXP-037's audit verified.
- **Expected output:** finalized `results/frozen_holdout_manifest.json`.

### Step 5 — H2: one-shot holdout inference (frozen machinery; binding verdict)

- **Method:** on the manifest's holdout events: compute `net_e` per event
  (Data Wiring construction); event-weighted mean; frozen regime-cluster
  bootstrap (1000 resamples, clusters within direction strata, seeds namespaced
  "EXP-032") reporting (a) the one-sided 95% lower bound (5th bootstrap
  percentile — the binding bound), (b) the two-sided 95% CI (descriptive label
  only), (c) the raw one-sided bootstrap p (share of resamples ≤ 0).
  - **Multiplicity:** family of 1 — this is the phase's only binding read and
    the programme's only holdout read; no Holm correction exists or is needed.
    The 1000-resample p resolution (0.001) comfortably resolves α = 0.05.
  - **Binding verdict (mechanical, computed by code):**
    `HOLDOUT_CONFIRMED` iff `ci_low_1s > m_cell` AND `boot_p ≤ 0.05`;
    `HOLDOUT_REFUTED` iff two-sided `ci_high < 0`;
    `HOLDOUT_INCONCLUSIVE` otherwise.
  - **Descriptive label** (non-binding, two-sided CI): EVIDENCE_FOR /
    EVIDENCE_AGAINST / INCONCLUSIVE_SPANS_ZERO.
  - **Determinism:** same-seed replay of the inference step on the
    already-computed outcome vector must be byte-identical (replay flag in
    `run_metadata.json`); this is a replay of arithmetic, not a second read.
- **Why this method:** identical to the frozen Phase 007/008 machinery, so the
  holdout cell is directly comparable to the EXP-030/034/037/038 record;
  distribution-free and dependence-aware. Sign-permutation remains invalid for
  an absolute (non-paired) mean.
- **Simpler alternative considered:** Wilcoxon signed-rank vs 0 — rejected
  (symmetric-i.i.d. assumption, ignores regime clustering; same rejection as
  EXP-037). t-interval — rejected (parametric, n≈15, clustered).
- **Assumptions:** regime-cluster exchangeability within direction strata
  (standing EXP-027 calibration), now coverage-checked at this cell's structure
  by Step 3; small-n caveat per the scope's power statement — INCONCLUSIVE is an
  expected, honest outcome and still spends the shot.
- **Expected output (R1/F01 persistence order):** `results/holdout_events.csv`
  (per-event keys, `fh_12`, `net_12`, truncation flag, financing days/bps, and
  the Step-6 companion columns) written FIRST; then `results/run_metadata.json`
  (guard statuses, replay flag, files/rows disclosure, `holdout_spent = true`);
  then `results/holdout_verdict.csv` (n, mean net, ci_low_1s, two-sided CI,
  boot_p, margin, binding verdict, descriptive label) LAST — the completion
  marker the no-second-read guard keys on. All three are assembled in memory
  before the first write. Post-verdict rendering, audit, interpretation, and
  documentation read ONLY these persisted artifacts; recomputing any quantity
  from holdout rows after the verdict exists is prohibited.

### Step 6 — Non-binding companions (same pass, same events; never promotable)

- **Method:** in the same H2 pass on the identical holdout events: (a) the
  BTC-exit net (Package-A estimand: `lifetime_bps − 3.0 − financing(trigger →
  completion)`, the EXP-022 lifetime construction + EXP-034 overlay) — point
  estimate only; (b) the gross/cost/financing decomposition of the binding cell
  (event-weighted means of `fh_bps`, RT, financing). Clearly labeled
  non-binding; no additional test family; no CI on the companion.
- **Why this method:** (a) makes the exit-mechanism comparison visible on the
  only out-of-sample stratum that will ever exist, at zero additional read cost;
  (b) discloses where the net comes from. Under no outcome do these alter,
  upgrade, or substitute for the binding verdict, nor nominate any future
  holdout read (Phase 009 design §6).
- **Expected output:** companion columns in `results/holdout_verdict.csv`;
  plot 2.

## Visualisations (3 / 3 budget)

1. **Binding verdict picture:** holdout per-event net distribution (strip/dot
   plot, n labeled) with the event-weighted mean, two-sided 95% CI, one-sided
   lower bound, and the margin `m_cell` and zero line marked — the entire
   verdict visible in one panel.
2. **FH(12) vs BTC-exit companion on the same holdout events** (paired bars,
   point estimates, n labels) — labeled NON-BINDING.
3. **Analysis-vs-holdout comparison at FH(12)/all_legs:** per-event net
   distributions side by side (39 analysis vs n holdout events, means marked) —
   the regime-shift context for interpretation, no inference drawn.

## Interpretation Guide (predeclared)

- **Supports the hypothesis** iff `holdout_verdict.csv` records
  `HOLDOUT_CONFIRMED` (`ci_low_1s > m_cell` AND `boot_p ≤ 0.05`). Consequence:
  first net-positive, holdout-confirmed AVWAP candidate; next step (new scope,
  outside EXP-032) is cTrader per-bar parity of the FH exit on analysis data.
  The small-n caveat accompanies the verdict.
- **Contradicts** iff `HOLDOUT_REFUTED` (two-sided CI_high < 0): Package B
  fails out-of-sample; holdout spent; Tier-C routing per Phase 008 design §9.
- **Inconclusive** iff `HOLDOUT_INCONCLUSIVE` (neither bound condition met):
  holdout spent without confirmation; the TEST-stratum evidence stands but is
  permanently non-upgradable. This is the predeclared power-limited expectation
  if the true effect is materially below the TEST point estimate.
- The Step 6 companions are context only — under no outcome do they alter the
  verdict, justify a Package-A claim, or motivate any further holdout analysis.
  No frozen constant is revisited under any outcome. There is no amendment or
  rerun path AFTER H2: a defect discovered after H2 is a disclosed defect in a
  spent shot, not grounds for a second read. (Guard failures BEFORE H2 never
  spend the shot — execution addendum §1–§2.)
- **Mandatory disclosures accompanying any verdict (R1):** (i) the pre- vs
  post-reportability holdout event counts and the external-validity caveat that
  the confirmed estimand conditions on ex-post reportability (a live trader
  cannot identify the binding population at entry; F04); (ii) if plot 3 shows
  holdout per-event dispersion materially above the analysis era's, the
  calibration-fidelity caveat must accompany a CONFIRMED verdict — the margin's
  null transports the analysis-era variance scale onto the holdout cluster
  layout (F05). Neither disclosure alters the mechanical verdict.

## Implementation Safety Constraints (for `experiment-developer`)

- All quantities in absolute bps against a 0 baseline; no percentage-of-baseline
  metrics; no near-zero-denominator ratios.
- Timestamp ordering by `CloseTime`/trigger timestamps everywhere; the only
  bar-index use is `entry_idx + 12` on the single 4h rebuild (within-view,
  EXP-033-identical).
- **Stage separation is structural AND process-level (R1/F03):** H1 (Steps 1–4)
  and H2 (Steps 5–6) are separate functions run as separate process invocations
  (`--phase h1`, then `--phase h2`); the H2 invocation re-runs the deterministic
  H1 pipeline and must reproduce the frozen manifest hash exactly (R1.6) before
  any outcome contact — a genuine cross-process barrier. The inter-phase check is
  mechanical (manifest hash, well-formed finite calibration, non-empty stratum);
  the 15–18 count expectation is disclosure only. H2 runs regardless of how the
  entry attributes look; declining to run H2 after a clean H1 is not an available
  operator action. H2's population/margin/constants come from the hash-verified
  manifest (live regenerated rows key-matched against it, hard stop on
  divergence); no holdout outcome helper is reachable from H1; H2 refuses to run
  when `holdout_verdict.csv` exists.
- **Seal discipline:** only the EURUSD timebars file is opened; lazy scan,
  column projection; run metadata discloses every file and row range
  materialized. No 5m/1h aggregation, no per-bar suite import, no exploratory
  holdout plotting beyond the 3 predeclared figures.
- Event regeneration runs once over the full series; the population frame is
  built once and reused by H1, H2, and plots (no repeated heavy loads).
- Reportability/control logic, FH construction, financing helper, and the
  bootstrap are **reused verbatim** from the EXP-020/022/033/034/037 code
  paths — no reimplementation; any necessary refactor must be byte-equivalent
  on the reconciliation anchors (guards 1b/1c are the proof).
- Calibration: R = 2000 with `tqdm`; seeds namespaced ("EXP-032", "nullcal");
  bootstrap seeds namespaced "EXP-032"; fixed seeds throughout.
- Financing uses fractional calendar days including weekends; spot-check one
  weekend-spanning holdout hold in the audit trail.
- Truncated-FH events (window past true series end) disclosed as a column and
  count, never silent; expected nonzero for the last events near data end.
- No directory creation, data loads, or plotting at import time; helpers return
  data; concise orchestration-level logging only.

## Complexity Check

- Statistical test families: 1 / 1 (frozen regime-cluster bootstrap CI +
  one-sided p on the single holdout cell; the Step 3 null calibration is
  synthetic-data verification of the same frozen family, not a new family;
  Step 6 companions are point estimates with no inference).
- Visualisations: 3 / 3.
- New modules: 1 / 1 (orchestration script; all analysis machinery imported
  unchanged from `xen` and prior experiment code paths).
