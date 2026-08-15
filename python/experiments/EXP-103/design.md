# EXP-103 — TPO value gaps and tight-gap outcomes

- **Family:** `CF-LIQSWP-001/HYP-003`
- **Checkpoint:** `2026-08-11-019-liquidity-sweeps`
- **Status:** holistic design freeze through AMENDMENT-14; fresh QA required
- **Vehicle:** analysis-only re-analysis of the retained EXP-100 Nautilus emission; no new `BacktestNode`, re-emission, TEST read, or holdout access
- **Scope:** cTrader TRAIN only; `EURUSD`, `XAUUSD`, `USTEC`; 264 retained cells

## 1. Current source and authority

```text
FROZEN-SOURCE:
  root: data/nautilus_runs/EXP-100/full/
  source_version: retained 264-cell AMENDMENT-14 TRAIN emission; EXP-100 is
    completed and read-only.
  current_state_authority: EXP-100/report.md and checkpoint-019/status.md
    operator verdict; the EXP-100 design's historical rerun authorization is not
    operative. Do not rerun, modify, relabel, or re-emit EXP-100.
  family_gate: python/experiments/EXP-100/results/estimand_validation.json
  gate_precondition: blocking_pass=true; n_cells=264; every
    python/experiments/EXP-100/results/execution/full/<cell_id>.json has
    blocking_pass=true. Check this before reading any source row.
  per_cell_inputs: run_metadata.json, raids.parquet, tpo_profiles.parquet,
    bar_marks.parquet, raids_destroyed.parquet, event_log.jsonl.
  fence: INFR-021 cTrader TRAIN, 2021-06-02T00:01:00Z through
    2023-11-22T00:00:00Z; manifest SHA256
    4cdc7b01dd47200710d0d961639d55d52e1129ca89096e841eafd816b6061de0.
  seal: retain each cell's config_hash and event_log_sha256; require
    emission_contract_version=nautilus-emission-v1, Nautilus=1.230.0,
    cost_model=NO_COST_CHARGED, and one_backtest_node=true.
  analysis_boundary: independent Python analysis under analysis_code/ only;
    no source mutation, new engine process, TEST, or holdout query.

JOIN:
  left: every raids.parquet row.
  right: tpo_profiles.parquet on (raid_id, profile_generation).
  cardinality: at most one profile row per key; report every missing/extra key.
  retention: left join; failed, censored, undefined, and unmatched rows remain
    visible. Never silently inner-join away a raid.
```

The binding EXP-100 decision excludes every
`profile_undefined_reason=ATR_UNDEFINED` row from excursion, normalized-excursion,
`strong_move`, and excursion-derived interpretation without repair or substitution.
The raid and profile undefined reasons remain visible. `pre_mfe_retrace={price,status}`
is source metadata only and is outside HYP-003.

## 2. Mechanism, object identity, and frozen profile

```text
MECHANISM: A sweep whose excursion-to-confirmation path leaves a concentrated,
low-density TPO value gap may have a different later-swing distribution from a
non-tight defined profile. The gap is assigned at same-direction confirmation;
it is a retrospective conditioning label, not a live prediction or trade signal.
DERIVED: estimand=defined-profile tight-minus-non-tight outcome contrasts plus an
all-defined descriptive baseline; null=cross-gap-label future-destroyed outcome
alignment; horizon=confirmation through the first opposing reference event or
TRAIN censor; test=direct per-stratum non-parametric contrasts; pnl_object=none because
this event study contains no trade, leg, episode, or capital estimand.
```

```text
OBJECT-IDENTITY:
  measurement object == trading object: YES — the joined profile belongs to the
    same level-linked raid whose later swing is measured; no proxy entry is used.
  measured conditioning event == traded entry event: N/A — this is a descriptive
    event study with no orders, fills, or P&L.
  effect-splitting windows non-overlapping: YES — the profile interval ends at
    confirmation and the later-swing interval begins after confirmation; repeated
    level dependence is clustered by level_id.
```

The frozen profile contract is: closed 1m source bars, one inclusive TPO bracket per
observed bar; interval from the maximum-excursion-setting 1m bar through completed
same-direction confirmation; bin width `0.10 × causal observation-timeframe
Wilder ATR(14)` frozen at profile start; POC = lowest-price maximum-count bin; VA
expands contiguously from POC to at least 70% of total TPO count with upper-neighbour
first on ties; selected gap bins are the lowest-density VA bins reaching at least
30% of VA TPO count.

```text
VA_width  = vah - val
 gap_span = gap_high - gap_low + bin_width
 tight_gap = gap_span < 0.50 * VA_width
 gap_span_atr = gap_span / atr_unit
 gap_span_va = gap_span / VA_width
```

Use emitted `gap_mask`, `gap_span`, `gap_span_atr`, `gap_span_va`, `va_mask`,
`va_count`, `tpo_total`, `tpo_conservation_ok`, `profile_status`, and
`undefined_reason`; never reconstruct a profile from later outcome data.

## 3. Population, estimand, and field contract

All raid and profile rows remain in the census. The outcome population is exactly:

```text
raids.status == COMPLETED
and raids.primary_attribution == true
and raids.primary_completed == true
and joined profile_status == DEFINED
```

`CONFIRMED_NON_PRIMARY` profiles remain profile-only rows under AMENDMENT-6. Failed,
right-censored, missing-profile, and undefined-profile rows remain visible with reason
counts and do not enter the later-swing denominator. The binding ATR-undefined
exclusion applies to `swing_atr`, `strong_move`, and excursion-derived interpretation;
finite non-excursion fields are disclosed with the excluded count beside them.

The fixed comparator is **non-tight defined profiles** within the same
`archive_symbol × timeframe × confirmation_method × confirmation_reference × side × config`.
An all-defined profile baseline is a separate disclosure, not a substitute comparator.
The contrast is tight minus non-tight. Primary estimators are mean `swing_atr`
(where defined) and mean `swing_duration_ns`; medians and finite `swing_price`/
`swing_bps` summaries are secondary. `strong_move` is an unpaired difference in
proportions; no raid pairing is asserted.

Assert `swing_duration_ns == duration_ns` row-wise before any duration read. The
canonical duration is `swing_duration_ns`; display hours as
`swing_duration_ns / 3_600_000_000_000`. No `pre_mfe_retrace` outcome is analysed.

## 4. Estimator and neutral report contract

Clusters are complete `level_id` histories sorted by
`(first_raid_timestamp, level_id)`. A level may contribute to both profile arms, so
both arms are resampled jointly from the same cluster sequence.

For each requested block length `L`:

1. If either profile arm is empty, emit counts, null estimate/interval, and
   `EMPTY_ARM`; do not drop or interpret the row.
2. If `n_clusters >= 2`, set `L_eff=min(max(1,L), n_clusters-1)`. Draw
   `ceil(n_clusters/L_eff)` starts uniformly from `[0,n_clusters)`, append
   `L_eff` circularly consecutive clusters per start, and truncate to the first
   `n_clusters`.
3. Recompute both arm statistics and the tight-minus-non-tight contrast for 10,000
   resamples and seeds `0,1,2,3,4`. Use NumPy `linear` 2.5%/97.5% quantiles.
   Report every seed's bounds, median bounds, seed-bound ranges, and sensitivity
   results for `L=2`, `L=5`, and `L=10` (each capped by the same rule).
4. Report every profile reason, status, count, exclusion, estimate, interval, and
   arm population per exact stratum. Pooled values are disclosure-only.

```text
REPORT-LAYERS:
  observed: profile counts, gap labels, reason/status counts, exclusions, means,
    medians, direct contrasts, intervals, seed ranges, and destroyed-control values.
  ideal: non-tight defined profiles are the fixed same-stratum comparator; all-
    defined is descriptive. No pass/fail field or post-outcome baseline exists.
  interpretation: the analyst describes direction, interval overlap, robustness,
    and evidence for and against. No row receives a value label. An operator may
    append a tag only in a separate decision record after reviewing the complete
    evidence; it is not part of analysis tables or plots.
  analyst_boundary: analysis.md is a no-verdict handoff; a fresh analyst works
    from the registered design and emission, not implementation narrative. Observed
    and inferred statements stay separate; the analyst cannot decide progression or
    family status.
```

No machine or analysis-table field may be named `SUPPORTED`, `WASH`, `CONTRADICTED`,
`WORTH_EXPLORING`, `NOT_WORTH`, or `INCONCLUSIVE`. OPERATOR-ONLY READING BANDS (not emitted or assigned by code): positive-direction
contrast with its interval above zero; interval overlapping zero; or negative-direction
contrast with its interval below zero. They are not analysis labels, gates,
rankings, row filters, or dispositions; any tag belongs only in a separate operator
decision record.

## 5. Profile integrity checks

By cell and stratum, report one-to-one join counts; TPO conservation; fixed bin
assignment; POC tie-breaking; VA mass; 30% gap mass; strict 50% comparison; positive
`VA_width`; minimum-bin, zero-ATR, empty-profile, undefined-reason, reset-on-new-
maximum, and deterministic replay checks. A missing/extra join, mask/span mismatch,
conservation failure, or non-deterministic replay is a hard validity finding. These
checks attest the frozen source; they do not assign a value label.

## 6. Cross-gap future destroy and validity tripwire

```text
CONTROL GAP_CROSSWISE_FUTURE_DESTROY:
  question answered: does the tight/non-tight outcome contrast require aligned
    future movement rather than the gap label or event population alone?
  population: primary completed defined-profile rows grouped by exact
    archive_symbol × timeframe × confirmation_method × confirmation_reference ×
    side × config × status × primary_completed × outcome-nullness class. Tight and
    non-tight labels are pooled within each group. The nullness class is the five-bit
    tuple (is_null(swing_price), is_null(swing_bps), is_null(swing_atr),
    is_null(duration_ns), is_null(strong_move)); duration_ns is the asserted alias
    of swing_duration_ns.
  mapping: copy the raw rows; sort each group by (raid_id, original_row_position).
    For each seed d=0..1999, draw default_rng(d).permutation(n) and reject/re-draw
    until perm[i] != i for every recipient i. Move the complete outcome block
    (swing_price, swing_bps, swing_atr, swing_duration_ns, duration_ns,
    strong_move) from donor perm[i] to recipient i. The donor gap label may equal
    the recipient label; forbidding same-label donors can swap two arms rather than
    destroy association. Profile/event fields, gap labels, status, eligibility,
    nullness, and row counts stay fixed. A group with n<2 produces
    VOID_NO_DERANGEMENT and remains disclosed.
  DISJOINT from signal population: the destroy is calculated on a separate copy
    after the raw estimate; it cannot alter the profile, event, timestamp, or raw
    signal population.
  bite: the pre-read fixture in the tripwire block plants +0.50 ATR,
    +3_600_000_000_000 ns, and +0.25 proportion contrasts; its destroyed means
    must satisfy the declared validity inequalities before live rows are read.
  non-vacuity: the mapping changes sufficient statistics of swing_atr,
    swing_duration_ns, and strong_move while preserving the global outcome-block
    multiset and exactly zero fixed points.
  expected outcome: if the gap/outcome relationship is aligned, the direct
    contrast moves toward zero after destruction; otherwise raw and destroyed
    contrasts are both reported without a mechanism claim.
  disclosure: raw contrast; all 2,000 destroyed contrasts; their mean and empirical
    95% interval; collapse_fraction = mean_destroyed/raw (control-to-raw ratio);
    fixed-point count; changed-field count; mapped-row count; and any VOID reason.
  destroy form: 2,000 DERANGEMENTS (zero fixed points each).
```

```text
TRIPWIRE: GAP_CROSSWISE_FUTURE_DESTROY
  must collapse the aligned tight-gap/outcome contrast when a raw contrast is
    present; the fixture's destroyed-to-raw ratio is expected near zero. Live ratios
    are disclosed, not used as value thresholds.
  vacuity check: outcome blocks move across fixed gap labels while the profile and
    event population and marginal outcome blocks remain fixed, so this destroy can
    change this tight-gap contrast.
  authority: HARD validity only. It never assigns value, quality, power, or
    significance labels. Its authorized estimators are the raw same-population
    mean swing_atr contrast, mean swing_duration_ns contrast, and unpaired
    strong_move proportion contrast defined in §3.
  outer bootstrap: for each seed s=0..4, generate 10,000 joint level-cluster
    populations using §4. For every population b, recompute D_raw[s,b] and all
    2,000 deranged contrasts D_destroy[s,b,d]. Set
    m_destroy[s,b]=mean_d(D_destroy[s,b,d]);
    bootstrap_SE_raw[s]=std_b(D_raw[s,b], ddof=1); and
    bootstrap_SE_mean_destroyed[s]=std_b(m_destroy[s,b], ddof=1).
  live read: on the unresampled source population compute D_raw and
    m_destroy[s]=mean_d(D_destroy[s,d]). For every seed with finite values, if
    abs(D_raw) > INTEGRITY_Z*bootstrap_SE_raw[s], require
    abs(m_destroy[s]) <= INTEGRITY_Z*bootstrap_SE_mean_destroyed[s]. If that
    inequality fails, mark the affected stratum/channel invalid as
    VOID_FUTURE_DESTROY_SURVIVAL; do not interpret it as evidence against the
    mechanism. If D_raw is zero or non-finite, collapse_fraction is NaN and the
    live collapse attestation is not applicable. If no seed satisfies the raw
    inequality, report the control but do
    not claim a live collapse attestation. A missing statistic, failed derangement,
    or failed reconciliation is also invalidity, never a null result.
  integrity_bite: INTEGRITY_Z=2.8. This is the same-estimator bootstrap standard
    error used only for validity; it is not MDE, a detection floor, a value floor,
    or a row-selection rule.
  fixture before live analysis: use 200 rows per arm with identical fixed profile
    labels and no nulls. The pre-read smoke uses 10 outer-bootstrap replicates; live uses 10,000. For swing_atr, alternate non-tight 0.90/1.10 and tight
    1.40/1.60 (raw contrast +0.50). For duration, alternate non-tight
    3_000_000_000_000/4_200_000_000_000 and tight
    6_600_000_000_000/7_800_000_000_000 (raw contrast
    +3_600_000_000_000 ns). For strong_move, set true at one quarter of
    non-tight positions and one half of tight positions (raw proportion contrast
    +0.25). Every seed and channel must satisfy the raw-bite and destroyed-
    non-bite inequalities above. Failure blocks the affected live control.
```

The retained EXP-100 within-configuration destroy is an apparatus receipt only; it
can preserve tight/non-tight configuration marginals and is not the HYP-003 control.

```text
FIXTURE-TOPOLOGY:
  rows_per_arm=200 (non-tight and tight); one row is one complete level cluster;
  level_id=FIXTURE-{arm}-level-{i:04d}; cluster_size=1;
  first_raid_timestamp=1_700_000_000_000_000_000 + i*900_000_000_000;
  config=FIXTURE_CONFIG for both profile arms;
  deterministic row permutation seed=4, then raid_id=fixture-raid-{position:04d};
  cluster ordering=(first_raid_timestamp, level_id); all profile labels/status/nullness
  fields are identical except the declared arm and outcome values.
  fixture outer bootstrap=10 for the pre-read smoke; live=10,000.
```

## 7. Sample size, complexity, and integrity boundary

```text
SAMPLE-SIZE:
  expected events per stratum: measured from the retained emission; planning context only.
  minimum_n_for_primary_inference: none; every defined/undefined row retains n,
    estimate, interval, exclusions, and reason codes.
  declared_fixed_comparator: non-tight defined profiles in the same named stratum;
    all-defined is disclosure-only.
  channels:
    - name: mean swing_atr
      sigma_denominator: outcome_level
    - name: mean swing_duration_ns
      sigma_denominator: outcome_level
    - name: strong_move proportion difference
      sigma_denominator: unpaired_proportion_delta
  strata predeclared thin: every asset × timeframe × method × reference × side ×
    config, including empty arms, undefined profiles, and missing joins.
COMPLEXITY-BUDGET:
  integrity: one frozen-profile reconciliation set plus one future destroy.
  estimators: one direct contrast plus median/quantile disclosures; no parametric test.
  control: one 2,000-seed destroy and one 5-seed outer bootstrap battery.
  plots: at most four purpose-specific profile/contrast plots; pooled plots are
    disclosure-only. analysis modules: one independent module.
```

```text
HARD (block): source gate-first check; TRAIN/holdout fence; causal profile
  provenance; raid/profile join and TPO reconciliation; schema/object/count
  reconciliation; no-local-accounting; deterministic analysis; binding
  ATR_UNDEFINED exclusion; future-destroy validity; and zero-cost compliance.
INFORMATIVE (operator judges): every observed profile label, reason, count, effect,
  interval, robustness read, control ratio, and cross-stratum comparison.
```

There is no trade or leg-bps series, so PSR is **N/A**. No cost, spread, commission,
swap, power calculation, detection threshold, sample-size veto, automatic label, or
family disposition is in scope.

## 8. Golden trace

```text
GOLDEN-TRACE (closed 1m input; bin_width=1.0; ATR_unit=10.0):
  T1 tight fixture, profile_end=2023-01-03T12:19:00Z. Consecutive 1m brackets
    at bins 100,101,102,103,104,105 have counts [29,12,23,23,27,26],
    total=140. POC=100. The VA target is 98; upper-first expansion visits
    100,101,102,103,104, giving va_count=114, val=100, vah=105, VA_width=5.
    Lowest-density selection reaches 30% of 114 with bins 101 and 102 (12+23=35),
    so gap_span=2, gap_span_va=0.40, tight_gap=true.
  T2 non-tight fixture, profile_end=2023-01-03T14:24:00Z. Bins 100..105 have
    counts [10,18,13,7,7,30], total=85. POC=105. Lower-neighbour expansion
    visits 105,104,103,102,101, giving va_count=75, val=101, vah=106,
    VA_width=5. Lowest-density selection reaches 30% of 75 with bins 103,104,102;
    gap_span=3, gap_span_va=0.60, tight_gap=false.
  T3 strict boundary and outcome separation: with VA_width=4 and gap_span=2,
    gap_span_va=0.50 and tight_gap=false because the comparison is strict `<0.50`.
    The profile label is fixed at confirmation; later outcomes cannot rewrite it.
    A non-primary confirmed profile remains profile-only under AMENDMENT-6.
```

## 9. Amendments and final selection accounting

```text
AMENDMENT-2: 1H confirmation for 15m/30m, 1D for 1h — DIRECTION: TIGHTER
  running count: 0 looser / 1 tighter / 0 neutral
AMENDMENT-3: retain 1m engine input — DIRECTION: NEUTRAL
  running count: 0 looser / 1 tighter / 1 neutral
AMENDMENT-4: causal ATR normalisation — DIRECTION: NEUTRAL
  running count: 0 looser / 1 tighter / 2 neutral
AMENDMENT-5: SoT tight-gap condition — DIRECTION: NEUTRAL
  running count: 0 looser / 1 tighter / 3 neutral
AMENDMENT-6: close-all-eligible settlement — DIRECTION: TIGHTER
  running count: 0 looser / 2 tighter / 3 neutral
AMENDMENT-7: cTrader-only universe — DIRECTION: TIGHTER
  running count: 0 looser / 3 tighter / 3 neutral
AMENDMENT-8: observation-bar raid grain — DIRECTION: NEUTRAL
  running count: 0 looser / 3 tighter / 4 neutral
AMENDMENT-9: 1H and 4H 1h references; retire 1D — DIRECTION: LOOSER
  running count: 1 looser / 3 tighter / 4 neutral
AMENDMENT-10: NY 17:00 trading day/week — DIRECTION: NEUTRAL
  running count: 1 looser / 3 tighter / 5 neutral
AMENDMENT-11: rolling 7/14/22/252; 264 cells — DIRECTION: NEUTRAL
  running count: 1 looser / 3 tighter / 6 neutral
AMENDMENT-12: tightness at 50% VA width; gap mass 30% — DIRECTION: NEUTRAL
  running count: 1 looser / 3 tighter / 7 neutral
AMENDMENT-13: same-bar return leaves raid live — DIRECTION: LOOSER
  running count: 2 looser / 3 tighter / 7 neutral
AMENDMENT-14: add pre_mfe_retrace without changing HYP-003 — DIRECTION: NEUTRAL
  running count: 2 looser / 3 tighter / 8 neutral

FINAL-NULL / SELECTION ACCOUNTING:
  final design has 2 looser / 3 tighter / 8 neutral amendments. It has no
  machine qualification, ranking, capped-read selection, or value verdict, so
  expected machine false-qualifier count under a global null is zero by
  construction. This is an accounting statement, not evidence. No row is hidden,
  dropped, or relabelled by n, interval, sign, profile reason, or control result.
  F02/F04/F06 are not applicable: there is no battery selection, path-dependent
  exit, or phase-shift retention gate. F07 is satisfied by retaining every realised
  profile, status, count, outcome, and interval.
```

## 10. Zero-cost disclosure

```text
ZERO-COST-DISCLOSURE
  cost_model: NO_COST_CHARGED
  spread: not modeled
  commissions: not modeled
  swaps/funding: not modeled
  implication: every figure in this document is gross and cost-free; no spread,
    commission, or swap enters any calculation. Realised results would differ
    (likely worse) under any real cost schedule.
  prohibited_claims: fully-net, cost-complete, tradable, deployable
  lifting: only an explicit operator directive may introduce a cost model for a
    scoped experiment; the directive is recorded in that experiment's design.md.
```
