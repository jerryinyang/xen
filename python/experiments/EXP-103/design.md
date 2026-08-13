# EXP-103 — TPO value gaps and tight gaps

- **Family:** `CF-LIQSWP-001/HYP-003`
- **Checkpoint:** `2026-08-11-019-liquidity-sweeps`
- **Status:** design amended through AMENDMENT-13; fresh QA pending
- **Vehicle:** analysis-only re-analysis of the frozen EXP-100 Nautilus emission; no new `BacktestNode`, no re-emission
- **Scope:** cTrader TRAIN only; `EURUSD`, `XAUUSD`, `USTEC`; 264 frozen cells

## Frozen source and join contract

```text
FROZEN-SOURCE:
  root: data/nautilus_runs/EXP-100/full/
  family_gate: python/experiments/EXP-100/results/estimand_validation.json
  gate_precondition: family_gate.blocking_pass=true; n_cells=264; every
    python/experiments/EXP-100/results/execution/full/<cell_id>.json has
    blocking_pass=true; do not read any source row before this check.
  per_cell_inputs: run_metadata.json, raids.parquet, tpo_profiles.parquet,
    bar_marks.parquet, raids_destroyed.parquet, event_log.jsonl.
  fence: INFR-021 cTrader TRAIN, 2021-06-02T00:01:00Z through
    2023-11-22T00:00:00Z; manifest SHA256
    4cdc7b01dd47200710d0d961639d55d52e1129ca89096e841eafd816b6061de0.
  seal: each cell uses its own run_metadata.config_hash and
    run_metadata.event_log_sha256; emission_contract_version=nautilus-emission-v1;
    Nautilus=1.230.0; cost_model=NO_COST_CHARGED; one_backtest_node=true.
  analysis_boundary: read-only Python analysis under analysis_code/; no new
    Nautilus process, no new emission, no TEST, and no holdout access.

JOIN:
  left: every row in raids.parquet.
  right: tpo_profiles.parquet on (raid_id, profile_generation).
  cardinality: require at most one profile row per key and report every missing or
    extra key; use a left join so failed, censored, undefined, and unmatched rows
    remain visible. Never silently inner-join away a raid.
```

## Mechanism

```text
MECHANISM: A sweep whose excursion-to-confirmation path leaves a concentrated,
low-density TPO value gap may have a different subsequent swing distribution.
The gap is known at same-direction confirmation and is a conditioning label for
the later swing, not a live prediction of the raid.
DERIVED: estimand=defined-profile tight versus non-tight outcome contrasts with
an all-profile baseline; null=cross-gap-label future-destroyed outcome alignment;
horizon=confirmation to opposing event or censor; test=direct per-stratum
ATR-normalised comparisons.
```

## Object identity and frozen profile algorithm

```text
OBJECT-IDENTITY:
  measurement object == trading object: YES — the joined profile belongs to the
    same level-linked raid whose later swing is measured.
  measured conditioning event == traded entry event: N/A — this is a descriptive
    event study, not a deployment strategy and emits no fills.
  effect-splitting windows non-overlapping: YES — profile interval ends at the
    confirmation event; the later-swing interval begins after confirmation.
```

- Source: closed 1m bars, one TPO bracket per observed bar.
- Interval: maximum-excursion-setting 1m bar through the completed same-direction
  confirmation close; a new maximum resets the profile online.
- Bin width: `0.10 × causal observation-timeframe Wilder ATR(14)`, frozen at profile start.
- Contribution: one count in every bin intersecting each bar's inclusive low-high.
- POC: lowest-price maximum-count bin.
- VA: contiguous expansion from POC to at least 70% of total TPO count, upper-first on ties.
- Gap: lowest-density VA bins until at least 30% of VA TPO count; exact mask and outer span.

```text
VA_width  = vah - val
 gap_span = gap_high - gap_low + bin_width  # emitted outer-bin span
 tight_gap = gap_span < 0.50 * VA_width
 gap_span_atr = gap_span / atr_unit
 gap_span_va = gap_span / VA_width
```

The analysis uses emitted `gap_mask`, `gap_span`, `gap_span_atr`, `gap_span_va`,
`va_mask`, `va_count`, `tpo_total`, `tpo_conservation_ok`, `profile_status`, and
`undefined_reason`; it does not reconstruct a profile from later outcome data.

## Population and estimand

All raid rows and all joined profile rows remain in the census. Profile population:
`profile_status=DEFINED`, `profile_status` undefined rows, and every undefined
reason are reported separately. Primary later-swing population is exactly
`raids.status=COMPLETED AND raids.primary_attribution=true AND
raids.primary_completed=true AND profile_status=DEFINED`. `CONFIRMED_NON_PRIMARY`
profiles remain a profile-only arm under AMENDMENT-6; they do not enter the later-
swing denominator. Failed, right-censored, missing-profile, and undefined-profile
rows remain visible with explicit reason counts.

The primary comparator is **non-tight defined profiles** within the same
`archive_symbol × timeframe × confirmation_method × confirmation_reference × side × config`
stratum; an all-defined-profile baseline is reported separately. `tight_gap` is
read only from the joined frozen profile row. No row is dropped because its profile
is undefined or its outcome is missing.

Primary outcome reads are `swing_atr`, `swing_bps`, `duration_ns`, and
`strong_move` on the primary population. Five-seed level-clustered block-bootstrap
intervals, block sensitivity, mean/median summaries, and paired-label deltas are
reported per stratum. No trade or leg-bps series exists; PSR is explicitly N/A.

## Required integrity checks

The analysis must report, by cell and stratum: one-to-one raid/profile join counts;
TPO count conservation; fixed bin assignment; POC tie-breaking; VA 70% coverage;
gap 30% mass; strict 50% tightness arithmetic; `VA_width <= 0`; minimum-bin,
zero-ATR, empty-profile, undefined-reason, reset-on-new-maximum, and deterministic
replay checks. Missing/extra rows or a mask/span mismatch are hard integrity findings.

## Control and tripwire

```text
CONTROL GAP_CROSSWISE_FUTURE_DESTROY:
  question answered: does the tight/non-tight contrast require aligned future
    movement rather than the profile label or event population alone?
  population: primary defined-profile outcome rows, grouped by exact
    archive_symbol × timeframe × confirmation_method × confirmation_reference ×
    side × config × status × primary_completed; tight and non-tight labels are
    pooled within each group.
  mapping: deterministically move post-confirmation outcome blocks
    (swing_price, swing_bps, swing_atr, duration_ns, strong_move) to an opposite
    gap-label row; keep profile fields, gap mask, tight_gap, status, eligibility,
    missingness, and row counts fixed. Use a zero-fixed-point derangement; a
    one-label/singleton group is reported N/A, never dropped.
  DISJOINT from signal population: the destroy changes only future outcome-block
    alignment and does not alter the profile or event rows.
  bite: a pre-read fixture plants a known +0.50 ATR tight/non-tight contrast at
    fixed profile labels and population; the crosswise destroy must remove it.
  non-vacuity: swing_atr, duration_ns, and strong_move sufficient statistics move.
  expected outcome if H true: tight/non-tight contrast collapses toward the
    non-tight fixed comparator; if H false: a contrast remains.
  disclosure: raw/destroy contrast, collapse fraction, fixed points, and mapped
    row count per stratum.
  destroy form: DERANGEMENT (zero fixed points).

TRIPWIRE: GAP_CROSSWISE_FUTURE_DESTROY
  must collapse the defined tight-gap/outcome alignment;
  vacuity check: outcome blocks move across fixed profile labels and the planted
    contrast changes, so this control can referee HYP-003;
  if permutation-based: derangement=YES (zero fixed points; L-28);
  integrity_bite: INTEGRITY_Z × bootstrap_SE from the same gap-contrast
    estimator, INTEGRITY_Z=2.8; validity only, never MDE or a research floor.
```

The EXP-100 within-configuration destroy remains an apparatus receipt, not the sole
HYP-003 control, because it can preserve tight/non-tight configuration marginals.

## Interpretation and sample size

```text
BANDS (per stratum, operator-only):
  SUPPORTED: direct tight/non-tight contrast is positive with its reported interval;
  WASH: direct contrast is small or interval-overlapping;
  CONTRADICTED: direct contrast is negative with its reported interval.
  These are report-layer tags only; never machine fields, gates, or row filters.
POOLED: disclosure-only.
SAMPLE-SIZE:
  expected events per stratum: measured from the frozen emission; planning context only.
  minimum_n_for_primary_inference: none; every defined/undefined row is retained.
  declared_fixed_comparator: non-tight defined profiles in the same named stratum;
    all-defined-profile baseline is descriptive.
  channels:
    - name: continuous profile-conditioned outcome
      sigma_denominator: outcome_level
    - name: strong_move paired labels
      sigma_denominator: paired_delta
  strata predeclared thin: every asset × timeframe × method × reference × side × config,
    including zero/undefined profile-reason rows.
```

No MDE, power curve, detection floor, `UNPOWERED` machine label, or count veto is allowed.

## Golden trace

```text
GOLDEN-TRACE (all bars are closed 1m input; bin_width=1.0 and ATR_unit=10.0):
  T1 tight fixture, profile_end=2023-01-03T12:19:00Z. Consecutive 1m brackets
    at prices 100,101,102,103,104,105 have TPO counts
    [29,12,23,23,27,26], total=140. POC=100. The VA target is 98; upper-first
    expansion visits 100,101,102,103,104 with va_count=114, val=100, vah=105,
    VA_width=5. Lowest-density selection reaches 30% of 114 with bins 101 and
    102 (12+23=35); gap_span=2, gap_span_va=0.40, tight_gap=true.
  T2 non-tight fixture, profile_end=2023-01-03T14:24:00Z. Consecutive 1m
    brackets at prices 100..105 have counts [10,18,13,7,7,30], total=85.
    POC=105; lower-first expansion visits 105,104,103,102,101 with
    va_count=75, val=101, vah=106, VA_width=5. Lowest-density selection
    reaches 30% of 75 with bins 103,104,102; gap_span=3, gap_span_va=0.60,
    tight_gap=false. The two masks and spans are exact emitted expectations.
  T3 outcome separation: both labels are assigned at profile confirmation;
    a later swing may be summarized only after the label is fixed and cannot
    rewrite either tight_gap value. A non-primary confirmed profile remains
    profile-only under AMENDMENT-6.
```

## Governance, amendments, and final null

```text
HARD (block): frozen family estimand gate; holdout exclusion; causal profile
  provenance; raid/profile join and TPO reconciliation; no-local-accounting;
  deterministic read; GAP_CROSSWISE_FUTURE_DESTROY integrity; zero-cost compliance.
INFORMATIVE (operator judges): gap labels, profile reason counts, all contrasts,
  intervals, robustness reads, and collapse fractions.

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

FINAL-NULL / SELECTION ACCOUNTING:
  final gate set is the complete 2L/3T/7N ledger above. There is no candidate
  qualification gate, capped-read selection rule, or machine value verdict;
  expected machine false-qualifier count under a global null is zero by
  construction. The future-destroy result is a validity attestation, not a value
  qualifier. No battery eligibility rule is applied, no rows are hidden, and no
  status transition is automated. No one-directional amendment streak reaches
  three. F02 time-stability, F04 exit-matched null, and F06 derived phase-shift
  threshold rules are N/A: there is no battery selection, path-dependent exit,
  or phase-shift retention gate. F07 is satisfied by retaining every realised
  profile reason, count, outcome, and interval.
```

## Zero-cost disclosure

```text
ZERO-COST-DISCLOSURE:
  cost_model: NO_COST_CHARGED
  spread: not modeled
  commissions: not modeled
  swaps/funding: not modeled
  implication: every figure in this document is gross and cost-free; no spread, commission,
  or swap enters any calculation. Realised results would differ (likely worse) under any
  real cost schedule.
  prohibited_claims: fully-net, cost-complete, tradable, deployable
  lifting: only an explicit operator directive may introduce a cost model for a scoped
  experiment; the directive is recorded in that experiment's design.md.
```
