# Data Analysis: SPDR-022 (amended TRAIN rerun, 2026-08-03)

**Experiment.** SPDR-022 — volatility-adaptive management after **MOMO breach** entries.
Family/registration `CF-VOLDIR-001/HYP-D9`; checkpoint
`2026-07-25-018-trade-opportunity-capture-geometry`; the common amendment
`adaptive-management-design.md` §12 (2026-08-03) is binding.

**Scope of this document.** Neutral interpretive read of the amended rerun only. It describes
what the emitted rows say and what mechanism would produce them. It contains no experiment
verdict, no family disposition, no ranking of arms, and no deployment statement. All figures are
TRAIN-band only; no TEST or holdout artifact was opened. This document is about the momentum
(MOMO) breach model and is independent of the mean-reversion companion; no companion artifact was
read.

**Runs read**

| universe | run_id | symbols | eligible origins | fills | positions |
|---|---|---|---|---|---|
| ctrader | `SPDR-022-ctrader-train-20260803T140238Z` | 3 (EURUSD, XAUUSD, USTEC) | 44,700 | 2,897,544 | 1,448,950 |
| crypto | `SPDR-022-crypto-train-20260803T140238Z` | 25 | 231,121 | 14,807,929 | 7,405,640 |

`run_summary.json` (both runs).

**Analyst code.** `python/experiments/SPDR-022/analysis_code/probe.py`, `report.py`, `report2.py`
(ruff-clean). Derived tables (never canonical) in `analysis_code/tables/`. No experiment-local
`code/` module was imported. No canonical artifact was modified.

---

## 1. Integrity gate

| Check | Result | Evidence |
|---|---|---|
| Estimand validation, all cells | `blocking_pass: true`; ctrader `n_cells: 3`, crypto `n_cells: 25`; manifest `ok: true`, `missing: []` | `results/estimand_validation.json` in each run dir |
| Hard integrity self-check | all 14 hard checks `true`: causality, deterministic_replay, entry_parity, fence, future_shift_changed_mapping, golden_traces, management_lattice, management_lifecycle, native_lattice, no_native_management_cross, order_fill_position_reconciliation, provenance, row_accounting, unique_result_keys | `integrity_selfcheck.json` (both) |
| Row accounting | ctrader `pass: true`, native_rows 5,811,000, management_rows 7,152,000, origin_count 44,700; crypto `pass: true` | `row_accounting.json` |
| Deterministic replay | `pass: true`, `mode: IMMEDIATE_REHASH` | `determinism.json` |
| Golden traces | `pass: true` | `golden_traces.json` |
| Fence / holdout | ctrader `status: PINNED`, train_end `2023-11-22T00:00:00Z`, holdout_start `2024-12-13T00:00:00Z`, manifest sha `4cdc7b01…`; crypto `status: PINNED`, train_end `2023-12-18T00:00:00Z`, holdout_start `2025-01-08T00:00:00Z`, manifest sha `35d3375e…` | `fence_attestation.json` |
| Reproduction | 13 artifacts per universe, first-pass and second-pass sha256 equal on every one, `all_equal: true` | `results/analysis/reproduction-hashes.json` |
| Future-shift tripwire | `future_shift_changed_mapping: true` — shifting the feature forward changes the origin→arm mapping, so the mapping is time-anchored | `integrity_selfcheck.json` |
| Derangement fixed points | `time_derangement.zero_fixed_points: true`, rows ctrader 44,703 / crypto 231,146, seed 240730 | `integrity_selfcheck.json` |
| Magnitude match | ctrader rows 43,523 (selected 21,763 / excluded 21,760); crypto rows 218,337 (109,175 / 109,162) | `controls.json` |

`run_summary.json` also carries `hard_integrity: "NOT_YET_RUN_TASK_8"` — a stale field written at
engine time; the separate `integrity_selfcheck.json` produced afterwards is the populated record
and reports `blocking_pass: true`. Both files are quoted here so the discrepancy is visible.

**Boundary statement (the only place value-laden words are permitted):** the integrity artifacts
above are the emission's own attestations and they pass; nothing in section 8 is a pass/fail on any
estimate.

## 2. Cost scope — read before any bps number below

Declared identically in `config.json` and `run_summary.json` for both universes:

```text
spread_cost_status: UNAVAILABLE_NOT_CHARGED
spread_rt_bps: null
cost_scope: PARTIAL_FEES_FUNDING_ONLY
implication: reported cost understates total cost; reported net performance is overstated
prohibited_claims: fully-net, cost-complete, tradable, deployable
```

Three separate facts, all verified against the emission:

1. **Spread is not charged.** `spread_rt_bps` is `null`; no spread term enters any fill.
   Every bps figure in this document therefore overstates realisable performance by an
   unmeasured amount.
2. **Known recording defect — mirrored cost columns are null.** In
   `per_stratum_estimates.parquet` the mirrored disclosure columns are null on **every** row:
   `spread_cost_status` null 2,414/2,414 (ctrader) and 19,961/19,961 (crypto); `spread_rt_bps`
   and `cost_scope` likewise null on all rows. The disclosure itself is intact in
   `config.json` / `run_summary.json`, so this is a mirroring defect in the analysis artifact,
   not a lost disclosure. Anyone reading the parquet alone would see no cost annotation.
3. **Commission / partial-cost fields are not populated either.** `partial_cost_mean_bps` is
   null on all 2,414 ctrader and all 19,961 crypto rows. In
   `native_parameter_shared_trades.parquet`, `partial_cost_bps` is null on all 377,857 ctrader
   rows and non-zero on zero rows. At the engine, every fill records commission exactly zero:
   ctrader `commissions` = `['0.00 USD']` on all 2,897,544 fills; crypto
   `['0.00000000 USDT']` on all 14,807,929 fills.

**Consequence.** Despite the `PARTIAL_FEES_FUNDING_ONLY` label, no cost of any kind was actually
charged in this rerun. Every outcome number below is a **gross** figure. Slippage is recorded
separately and is materially zero (crypto median 0.0, mean −0.000146 price units).

## 3. What the two lenses measure (mechanism)

The two native lenses are reported separately throughout and are never merged. They answer
different questions and have different denominators.

**Lens A — `COMMON_ORIGIN_OCCUPANCY_INCLUSIVE`.** Denominator is every *eligible scheduled
origin* (`eligible_origin_n`), including origins where the arm produced no event, no fill, or
zero exposure while the other side was occupied. The per-arm quantity is
`exposure_per_origin` = per-origin mean outcome, which reconciles as
`gross_mean_bps × fill_rate`. Worked check, EURUSD `E_TOUCH` fixed comparator:
`−0.4111 × 0.1850 = −0.0760` = emitted `exposure_per_origin`. The reported `estimate` is the
adaptive-minus-fixed difference of that per-origin quantity: for
`NAT_E_TOUCH_RANGE_SCALE_BAND_Z_DIRECT` on EURUSD, `0.021259 − (−0.0760) = 0.097307` = emitted
`estimate`. This lens carries the native `z`/`H` arms; uncertainty uses
`effective_origin_blocks`.

*Why it matters:* a band change moves **which breach events exist at all**. Conditioning on
fills would hide arms that simply trade less. Lens A prices the selectivity change and the
outcome change together, per origin.

**Lens B — `COMMON_CLOSE_TRADE`.** Denominator is actual common fills and closes: both the
adaptive and the fixed side have real `_entry_ns` and a confirmed close on the same declared
origin key (`common_fill_n`, `common_close_n`). This lens carries the external management device
arms; uncertainty uses `effective_trade_blocks`.

*Why it matters:* a stop or target changes the exit of an already-open position. Only a paired,
both-sides-closed trade isolates that.

`metric_name` on the native lens is `outcome_bps` throughout; on the device lens each device has
its own metric family (section 6).

## 4. Populations — nothing pruned

Row counts by universe, entry variant, arm class, lens and state. `E_TOUCH` and `E_CLOSE` are
never pooled. `eligible_origin_n` is summed over symbols and over the arms in a class, so it is a
disclosure of coverage, not a count of distinct origins (distinct eligible origins are 44,700
ctrader / 231,121 crypto).

### 4.1 ctrader populations

{{TABLE:md_populations_ctrader.md}}

### 4.2 crypto populations

{{TABLE:md_populations_crypto.md}}

### 4.3 Selected / excluded origin populations

Every eligible origin is retained and classified. `SELECTED` origins carry an outcome;
`EXCLUDED` origins are `NO_EVENT` or `NO_FEATURE` and carry outcome 0.0 by construction (they
are the zero-exposure origins Lens A includes).

ctrader (`native_parameter_selected_excluded.parquet`, 5,811,000 rows):

{{TABLE:md_selexc_ctrader.md}}

crypto (30,045,730 rows):

{{TABLE:md_selexc_crypto.md}}

Censored and incomplete populations are small and carry mean outcome 0.0: ctrader `CENSORED`
8 rows, `INCOMPLETE` 2,022 rows; crypto `CENSORED` 27 rows, `INCOMPLETE` 16,482 rows. They are
retained in the tables above rather than dropped. `EVENT_UNDECIDED` exists only for `E_TOUCH`
(ctrader 1,539 rows, crypto 73,689) — the touch variant can register a band touch whose side is
not yet decided, which the close variant cannot.

### 4.4 State sections

ctrader (`state_sections.parquet`, 3,861 rows):

{{TABLE:md_states_ctrader.md}}

crypto (30,978 rows):

{{TABLE:md_states_crypto.md}}

**Unfilled entries.** Fill rate on the fixed comparator sits near 0.16–0.19 of eligible origins
in both universes (section 5): roughly four in five eligible origins never become a trade under
the fixed band. That is the population Lens A keeps and Lens B necessarily drops.

## 5. Fixed comparators (baselines), per symbol and per entry variant

The fixed native comparator is the SPDR-014 Z-VOL band at H1, EWMA Parkinson width, `z=1.5`,
`H=12`, entering with the breach side at the next real open, unit size, no target/stop/trail,
exit after four H1 bars. Its own adaptive-minus-fixed estimate is 0.0 by construction
(self-comparison), which is why the `FIXED_NATIVE` rows show `estimate = 0.0000` and
`ci_excl_zero = 0`. The descriptive columns below are the baseline the adaptive arms are
differenced against. `exit_reason` is `HOLD=1.000000` on every baseline row — the baseline has no
price exit, so all closes are the four-bar time exit.

### 5.1 ctrader fixed native comparator

{{TABLE:md_baseline_ctrader.md}}

### 5.2 crypto fixed native comparator

{{TABLE:md_baseline_crypto.md}}

**Reading.** On both universes the fixed MOMO breach baseline sits close to zero in per-origin
terms and mixed in per-trade terms, with a win share just under one half and a win/loss ratio
just above one — a near-symmetric payoff. Because no spread and no commission are charged, these
are gross figures; `breakeven_win_share_net` is emitted alongside and sits at essentially the
same level as `win_share` (e.g. ctrader EURUSD `E_TOUCH` 0.5083 vs 0.4932), which says the
baseline sits at or about the arithmetic break-even of its own payoff geometry even before any
cost is applied.

### 5.3 Fixed-device comparators

The fixed device comparators are `FIXED_HOLD_B2/B4/B12`, `FIXED_SIZE_UNIT`,
`FIXED_TARGET_M0.75/M1.00/M1.50`, `FIXED_STOP_M0.75/M1.00/M1.50`,
`FIXED_TRAIL_M0.75/M1.00/M1.50` (`comparator_id` values in
`per_stratum_estimates.parquet`). Their self-comparison rows carry `estimate` 0 and none of the
2,715 live fixed-device rows (265 ctrader + 2,450 crypto) has a CI excluding zero — as expected
for a self-comparison, and a useful sanity anchor on the CI machinery.

ctrader fixed-device population rows by state:

{{TABLE:md_fixed_device_ctrader.md}}

crypto fixed-device population rows by state:

{{TABLE:md_fixed_device_crypto.md}}

### 5.4 Fixed-native-parameter comparator pointer

`controls.parquet` carries two pointer rows per universe rather than duplicate estimates:

{{TABLE:md_controls_pointer_ctrader.md}}

(identical two rows for crypto). The fixed-native-parameter comparator is therefore reported in
`native_parameter_origins.parquet` (section 6.1) and the fixed-device comparator in the device
tables (section 5.3 / 6.2); no comparator is missing, it is relocated.

## 6. Estimates

Every table gives estimate, CI bounds via min/median/max across the symbols in the group, the
count of symbol-rows whose bootstrap 95% CI excludes zero, the median MDE, the correct population
counts for the lens, and the effective block count. **Power is context here, never a gate:** no
row is removed, relabelled, or ranked because of its MDE, and a wide MDE is reported as a wide
MDE, not as an absence.

Group-level min/median/max are disclosures over the underlying per-symbol rows. **Every
per-symbol row is retained** in the linked full tables — `analysis_code/tables/native_all_*.csv`
(390 ctrader / 3,250 crypto native rows) and `analysis_code/tables/device_all_*.csv` (7,413
ctrader / 59,015 crypto device rows) — and ultimately in the canonical parquet files. Nothing is
top-N pruned.

### 6.1 Lens A — `COMMON_ORIGIN_OCCUPANCY_INCLUSIVE`: native `z` / `H` geometry

Individual volatility components first, each shown separately for `BAND_Z` and `BAND_H` and for
`DIRECT` and `REVERSE`; the bounded `BAND_Z+BAND_H` combination and its four orientation pairs
(`DIRECT_DIRECT`, `DIRECT_REVERSE`, `REVERSE_DIRECT`, `REVERSE_REVERSE`) follow in the same table
under `arm_class = NATIVE_COMBINATION`. The eight executable components are `LEVEL_NOW`,
`LEVEL_FORECAST_K4`, `LEVEL_FORECAST_K12`, `RANGE_SCALE`, `SWING_SCALE`, `SWING_GT_CUR`, `SHOCK`,
`TAIL_RISK`.

`elig` / `fills` / `closes` are summed over symbols within the group; `eff` is
`effective_origin_blocks`; `ev_rate`, `fill_rate` and `occ` (`exposure_per_origin`) are group
medians.

#### ctrader (130 rows; per-symbol rows in `tables/native_all_ctrader.csv`)

{{TABLE:md_native_ctrader.md}}

#### crypto (130 rows; per-symbol rows in `tables/native_all_crypto.csv`)

{{TABLE:md_native_crypto.md}}

#### Per-trade descriptive companion (same lens, `state = ORDER_CREATED`)

ctrader:

{{TABLE:md_native_desc_ctrader.md}}

crypto:

{{TABLE:md_native_desc_crypto.md}}

#### Exit-reason mix

Native arms close only on the four-bar hold; device and combination arms show the competing
exits. ctrader (first 37 rows of the grouping; full mix in `per_stratum_estimates.parquet`):

{{TABLE:md_exit_ctrader.md}}

crypto (first 60 rows):

{{TABLE:md_exit_crypto.md}}

### 6.2 Lens B — `COMMON_CLOSE_TRADE`: individual devices

Individual devices (`arm_class = MANAGEMENT`) are reported before any combination. Each device
carries its own metric family:

| device | metrics emitted |
|---|---|
| TARGET | `realised_capture_bps`, `missed_excess_bps`, `reach_rate`, `time_to_target` |
| STOP | `loss_severity_bps`, `adverse_excursion_bps`, `recovery_after_stop_bps`, `stop_rate` |
| TRAIL | `peak_giveback_bps`, `favourable_excursion_captured`, `loss_tail_bps` |
| HOLD | `outcome_by_time_bps`, `decay_bps`, `opportunity_duration`, `holding_efficiency` |
| SIZE | `drawdown_bps`, `tail_loss_bps`, `risk_dispersion`, `concentration` |

Only `outcome_by_time_bps` is an outcome in bps on the trade itself; the rest describe the
geometry of the trade (how far it ran, how long it took, how the loss tail is shaped). This
distinction drives section 7.

#### ctrader individual devices (294 rows)

{{TABLE:md_device_individual_ctrader.md}}

#### crypto individual devices (314 rows)

{{TABLE:md_device_individual_crypto.md}}

### 6.3 Lens B — component combinations (`MANAGEMENT_COMPONENT_COMBINATION`)

ctrader:

{{TABLE:md_device_compcombo_ctrader.md}}

crypto:

{{TABLE:md_device_compcombo_crypto.md}}

### 6.4 Lens B — device combinations (`MANAGEMENT_DEVICE_COMBINATION`)

`TARGET+STOP`, `TARGET+STOP+HOLD`, `TRAIL+HOLD`, all at `M1.00`.

ctrader:

{{TABLE:md_device_devcombo_ctrader.md}}

crypto:

{{TABLE:md_device_devcombo_crypto.md}}

## 7. Controls

Both predeclared controls executed. Neither can gate anything; both are informative.

### 7.1 TIME_DERANGEMENT

Population `ELIGIBLE_ORIGIN_TIME_DERANGED`, comparators `FIXED_NATIVE_BAND_E_TOUCH` and
`FIXED_NATIVE_BAND_E_CLOSE`, seed 240730, `zero_fixed_points: true`.

**The control's point estimate is numerically identical to the uncontrolled estimate on 100% of
rows.** ctrader: 384 control rows, maximum absolute difference from the corresponding raw arm
estimate `2.22e-16`; crypto: 3,200 rows, maximum absolute difference `1.42e-14`. Collapse
fraction (control effect ÷ raw effect) is 1.00 at the 5th, 25th, 50th, 75th and 95th percentile
in both universes.

The CI bounds *do* differ (e.g. EURUSD `E_TOUCH` `RANGE_SCALE BAND_Z DIRECT`: raw `ci_low`
−0.076595, control `ci_low` −0.072301, both with `estimate` 0.097307), which localises the
mechanism: the derangement was applied to the resampling used for the interval, not to the
origin→outcome mapping that produces the point estimate. A derangement that leaves the point
estimate bit-identical cannot destroy the quantity being estimated, so **as executed this control
is non-informative about the native estimates** — it neither supports nor undermines them. This
is a plain observation about the control, not a finding about the arms, and it is distinct from
the future-shift tripwire, which did change the mapping (`future_shift_changed_mapping: true`).

### 7.2 MAGNITUDE_MATCH

Population `ELIGIBLE_ORIGIN_MAGNITUDE_STRATUM`, four magnitude bins (0–3), same two comparators.
Unlike the derangement this control does move the estimate: no row is identical to its raw
counterpart, maximum absolute deviation 4.77 bps (ctrader) and 746.5 bps (crypto). Within-bin
medians are small and change sign across bins and across entry variants, and the per-bin MDEs are
wide (ctrader median 1.14 bps, crypto 8.26 bps). 64 of 1,536 ctrader rows (4.2%) and 909 of
12,800 crypto rows (7.1%) have a CI excluding zero.

ctrader controls:

{{TABLE:md_controls_ctrader.md}}

crypto controls:

{{TABLE:md_controls_crypto.md}}

## 8. Selection checks

`selection_checks.parquet` (390 ctrader / 3,250 crypto rows). `sign_share_difference` sits
tightly around 0.083–0.099 in every component and both variants; `excluded_mean_median_gap` is
0.0 everywhere — consistent with excluded origins carrying outcome 0.0 by construction.
`payoff_scale_ratio` is **null on every row in both universes** (0 non-null of 390 and of 3,250):
an unpopulated field, reported here rather than silently omitted.

ctrader:

{{TABLE:md_selection_ctrader.md}}

crypto:

{{TABLE:md_selection_crypto.md}}

## 9. Observations, reported symmetrically

### 9.1 Supporting observations (consistent with a volatility component changing something)

- **Device geometry moves reliably and in the mechanically expected direction.** On individual
  adaptive device arms with a live common-close population, the geometry metrics have CIs
  excluding zero at high rates: ctrader HOLD `decay_bps` 30/30 rows (median +6.39 bps) and
  `opportunity_duration` 30/30 (median +1.28); SIZE `risk_dispersion` 34/36 (median −5.51) and
  `tail_loss_bps` 34/36 (median −13.60); STOP `adverse_excursion_bps` 28/45 (median +0.60);
  TARGET `realised_capture_bps` 23/49 (median +0.77). Crypto reproduces the same pattern at
  larger scale: HOLD `decay_bps` 239/250 (median +30.75), `opportunity_duration` 239/250 (median
  +0.90), SIZE `risk_dispersion` 275/300 (median −31.19), TARGET `realised_capture_bps` 273/509
  (median +6.90).
  *Mechanism:* these are the direct arithmetic consequence of moving the device. A
  volatility-scaled hold that lengthens in low volatility mechanically raises decay and duration;
  a volatility-normalised size mechanically compresses risk dispersion and the loss tail. The
  data proves the device does what it is defined to do. It does not by itself say the trade
  outcome improved.
- **Both entry variants produce a working, separately-populated lattice.** `E_TOUCH` and
  `E_CLOSE` each carry their own eligible/filled/closed/common populations at every arm class
  (section 4), and neither ever falls back to the other: `E_TOUCH` fills 8,496 (ctrader fixed) vs
  `E_CLOSE` 7,537, and the `EVENT_UNDECIDED` state exists only under `E_TOUCH`.
- **A minority of native arms show intervals excluding zero.** ctrader 17 of 384 native rows
  (4.4%), crypto 135 of 3,200 (4.2%), spread across components and both orientations. Concrete
  examples with their full context are in the section 6.1 tables and the linked per-symbol CSVs.

### 9.2 Contrary observations

- **The native band estimates are small relative to their own MDE and cluster at chance.** The
  4.4% / 4.2% rate at which native-arm CIs exclude zero is close to the 5% expected from interval
  coverage alone if there were no systematic effect. Median absolute effects sit far below the
  median MDE: ctrader `E_TOUCH` NATIVE median estimate +0.0197 bps against median MDE 0.1756;
  `E_CLOSE` NATIVE median +0.0012 against 0.1386; crypto `E_TOUCH` NATIVE median +0.0643 against
  1.5967; `E_CLOSE` NATIVE median +0.0083 against 1.3834. Positive-sign share is near half
  (ctrader 210/384; crypto 1,703/3,200).
- **The only in-bps device outcome metric moves far less than the geometry metrics.**
  `outcome_by_time_bps` has a CI excluding zero on 6 of 30 ctrader HOLD rows and 15 of 250 crypto
  HOLD rows, against 30/30 and 239/250 for `decay_bps` on the identical populations. *Mechanism:*
  changing when you exit changes how the trade looks without changing where the price went. The
  geometry responds because it is defined by the device; the outcome does not follow it here.
- **Rate metrics on pure price-only device arms are degenerate by construction.**
  `reach_rate` estimate is exactly 0.0000 on all 49 ctrader and all 509 crypto adaptive TARGET
  rows, and `stop_rate` is 0.0000 on all 45 ctrader adaptive STOP rows (crypto: 1 of 443 rows
  non-zero). Inspection shows `observed = 1.0` and `comparator_observed = 1.0` on those rows.
  *Mechanism:* a pure TARGET or STOP arm has no time cap, so a close only exists when the level is
  hit. Conditioning on a common close therefore conditions on both sides having hit, and the rate
  difference collapses to zero by construction. These rows are not evidence of "no effect on
  reach"; the estimand cannot see reach on this population. The magnitude metrics on the same rows
  (`realised_capture_bps`, `loss_severity_bps`) remain informative.
- **The time-derangement control returned no information** (section 7.1): collapse fraction 1.00
  on every row.
- **The fixed baseline itself sits near its own break-even before any cost.**
  `breakeven_win_share_net` tracks `win_share` closely on the baseline rows (section 5), and no
  spread or commission was charged at all (section 2), so the entire comparison is a gross one.

### 9.3 Concentrated observations

- **Price-only device arms rest on very small common-close populations.** ctrader adaptive TARGET
  `M1.00` sums to 864 common closes across all symbols (per-group minimum 10, maximum 85) with
  effective trade blocks as low as 2; TRAIL `M1.00` 504 closes; STOP `M1.50` 1,028 closes with
  per-group minimum 1. Individual groups reach single digits: ctrader STOP `M0.75` on
  `SWING_SCALE` has 5 common closes on one symbol and reports `adverse_excursion_bps` +147.62 and
  `loss_severity_bps` −147.99 with a CI excluding zero. A three-figure bps estimate on five trades
  is a concentrated read and is reported as such.
- **HOLD and SIZE arms are the well-populated ones.** ctrader SIZE `STATE_HALVE_HIGH` carries
  320,660 common closes and 78,420 effective trade blocks; HOLD `STATE_LOW_4_HIGH_12` 219,704 and
  94,172. The device-lens evidence is therefore heavily concentrated in the two devices that
  always close (time-based and size-based) and thin in the three that close only on a price
  touch.
- **crypto symbol coverage is uneven.** Eligible origins per symbol range from 1,062 (TIAUSDT,
  effective origin blocks 46) to 12,527 (SOLUSDT/ADAUSDT, 522). Group ranges in section 6.1 are
  widened by the small-history symbols; the per-symbol rows in `tables/native_all_crypto.csv`
  separate them.
- **A few crypto native rows carry extreme values.** e.g. `E_CLOSE LEVEL_FORECAST_K12 BAND_Z
  REVERSE` spans −23.24 to +3.15 bps across 25 symbols; `SWING_SCALE` groups repeatedly show the
  same −17.4523 / +5.8164 extremes, indicating one or two symbols dominating that component's
  range in both directions.

### 9.4 Unresolved observations

- Why the time-derangement control's point estimate is bit-identical to the uncontrolled estimate
  (section 7.1). The emission shows the fact; it does not show the intent.
- Whether `holding_efficiency` is meant to be sparsely defined: it is non-null on 2 of 30 ctrader
  and 41 of 250 crypto adaptive HOLD rows, while the other three HOLD metrics are complete.
- Why `payoff_scale_ratio` is null on all 3,640 selection-check rows (section 8).
- Why the mirrored cost columns are null in `per_stratum_estimates.parquet` while intact in the
  run config (section 2, item 2).
- `run_summary.json` `hard_integrity: "NOT_YET_RUN_TASK_8"` versus `integrity_selfcheck.json`
  `blocking_pass: true` (section 1).
- 83 of 1,201 live ctrader device rows and 724 of 11,432 live crypto device rows have a null
  `estimate` despite a non-zero common-close population; these are retained in the tables as
  blanks rather than dropped, and the reason is not recorded in the artifact.

## 10. Question list

1. Do the emitted populations reconcile per cell? **Answered** — section 1 (`row_accounting`,
   `estimand_validation`) and section 4.
2. What is the outcome-bearing object under each lens, and does it match the design's estimand?
   **Answered** — section 3; Lens A is the eligible origin, Lens B is the paired closed trade,
   matching the §12 amendment's `entry_fill_n` / `common_close_n` definitions.
3. Are `E_TOUCH` and `E_CLOSE` kept separate everywhere? **Answered** — yes; sections 4–6 report
   them separately at every level and no fallback exists between them.
4. Do fixed/direct/reverse arm classes and all four orientation pairs appear? **Answered** —
   section 6.1; `FIXED`, `DIRECT`, `REVERSE` and `DIRECT_DIRECT` / `DIRECT_REVERSE` /
   `REVERSE_DIRECT` / `REVERSE_REVERSE`.
5. Are individual components and individual devices shown before combinations? **Answered** —
   sections 6.1 (individual before `NATIVE_COMBINATION`) and 6.2–6.4.
6. Per-stratum: which symbols carry or contradict a group figure? **Answered in part** — group
   ranges in section 6, full per-symbol rows in the linked CSVs; no cross-symbol homogeneity test
   was run, so group medians are disclosures only.
7. Occupancy: what fraction of eligible origins becomes a trade? **Answered** — fill rate
   0.16–0.19 on the fixed comparator (section 5), so Lens A's zero-exposure population is roughly
   four-fifths of origins.
8. Where does the outcome come from — win rate or payoff size? **Answered** — section 5:
   `win_share` just under 0.5 with `win_loss_ratio` just above 1.0; a near-symmetric payoff, and
   `breakeven_win_share_net` sits alongside `win_share`.
9. Cost sensitivity: at what round-trip cost does a positive figure disappear? **Answered
   qualitatively** — no cost is charged at all (section 2), and the native per-origin effects are
   fractions of a bps in ctrader and single-digit bps in crypto, so any non-zero spread applies
   directly against them. A quantitative sensitivity curve is **UNANSWERED**: `spread_rt_bps` is
   null, so there is no frozen cost map in this emission to sweep against.
10. Control collapse fractions? **Answered** — section 7: TIME_DERANGEMENT 1.00 on every row;
    MAGNITUDE_MATCH moves every row with sign-unstable per-bin medians.
11. Power: is a small figure distinguishable from an invisible one? **Answered** — every table
    carries the median MDE next to the estimate; on the native lens the median effect is roughly
    an order of magnitude below the median MDE in both universes, so most native rows are in the
    regime where the emission cannot resolve an effect of the size observed. Reported as context.
12. Censored / incomplete / unfilled populations retained? **Answered** — section 4.3/4.4.
13. What would make the headline device reads wrong? **Answered** — sections 9.2 and 9.3: the
    rate-metric degeneracy on price-only arms, the geometry-versus-outcome split, and the small
    common-close populations on TARGET/STOP/TRAIL.
14. Per-year stability. **UNANSWERED** — the canonical analysis artifacts aggregate over the whole
    TRAIN band and carry no year field; answering it would require a new emission or a per-trade
    re-aggregation from `native_parameter_shared_trades.parquet`, which is a proposal for the
    operator, not something done here.
15. Cross-lens agreement: do Lens A and Lens B agree on the same component? **UNANSWERED by
    design** — the two lenses are reported separately and are not merged; the native and
    management lattices are not crossed (`no_native_management_cross: true`).

## 11. Claim boundary and hand-off

This document describes SPDR-022 (MOMO) on TRAIN only. It does not choose between `E_TOUCH` and
`E_CLOSE`, does not gate or inform either companion experiment, issues no experiment or family
verdict, ranks nothing, and authorises nothing. The mean-reversion companion was not read and is
not referenced.

Suggested probes, for the operator to accept or decline:

- clarify the time-derangement implementation (why the point estimate is unchanged) before any
  weight is placed on that control;
- populate the mirrored cost columns and `payoff_scale_ratio` in the analysis artifacts;
- if per-year or per-regime structure matters, request a stratified re-aggregation;
- if the price-only device arms matter, request a population large enough that TARGET/STOP/TRAIL
  common closes are not in the tens.

Interpretation of these observations is the operator's.
