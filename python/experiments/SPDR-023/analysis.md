# SPDR-023 — analysis of the amended TRAIN rerun

- **Experiment:** SPDR-023, volatility-adaptive management after mean-reversion (MR) breach entries
- **Family / registration:** `CF-VOLDIR-001/HYP-D10`
- **Runs analysed:** `data/nautilus_runs/SPDR-023-ctrader-train-20260803T140238Z`,
  `data/nautilus_runs/SPDR-023-crypto-train-20260803T140238Z`
- **Canonical analysis artifacts:** `python/experiments/SPDR-023/results/analysis/{ctrader,crypto}/`
  (13 artifacts each) plus `results/analysis/reproduction-hashes.json`
- **Band:** TRAIN only. **Interpretation label carried by the artifacts:** `DESCRIPTIVE_ONLY`
- **Governing contract:** checkpoint `adaptive-management-design.md`, binding in full, including the
  2026-08-03 amendment in §12
- **This document fully replaces any SPDR-023 `analysis.md` written from the invalidated first pass.**

This analysis is written independently of the momentum companion experiment. Nothing here is read
from, compared with, or conditioned on any other experiment's prose.

## 0. What this document may and may not say

Per §11 and the `INTERPRETATION` block of the checkpoint contract, no verdict bands apply to
SPDR-023. Every row below is described by estimate, uncertainty, population count, effective count
and minimum detectable effect (MDE). Power is reported as context and is never used to keep, drop,
promote or demote a row. Small, inconsistent, concentrated and unresolved observations are stated
plainly as observations.

**Explicit boundary statement (the only place such words are used):** this run charges no spread and
in fact charges no cost at all (§2). Nothing here is a tradability or deployment claim, and no row in
this document may be read as one.

## 1. Integrity gate

All items below are read from the emitted run artifacts, not from any summary.

| Check | ctrader | crypto | Source |
|---|---|---|---|
| Estimand validation | `blocking_pass: true`, `n_cells: 3`, manifest `ok: true`, `missing: []` | `blocking_pass: true`, `n_cells: 25`, manifest `ok: true`, `missing: []` | `estimand_validation.json` |
| Fence | `status: PINNED`, `within_fence: true`, `train_end_utc 2023-11-22T00:00:00Z`, `holdout_start_utc 2024-12-13T00:00:00Z`, manifest sha256 `4cdc7b01…61de0` matches expected | `status: PINNED`, `within_fence: true`, `train_end_utc 2023-12-18T00:00:00Z`, `holdout_start_utc 2025-01-08T00:00:00Z`, manifest sha256 `35d3375e…c0448` | `fence_attestation.json`, per-cell `fence` block |
| Hard checks (14) | all `true` | all `true` | `integrity_selfcheck.json` → `hard_checks` |
| Future-shift tripwire | `future_shift_changed_mapping: true` | `future_shift_changed_mapping: true` | `integrity_selfcheck.json` |
| Time-derangement non-vacuity | `zero_fixed_points: true`, `rows: 44703`, `seed: 240730` | `zero_fixed_points: true`, `rows: 231146`, `seed: 240730` | `integrity_selfcheck.json` → `informative.time_derangement` |
| Magnitude match populations | `rows: 43523`, `selected_rows: 21763`, `excluded_rows: 21760` | `rows: 218337`, `selected_rows: 109175`, `excluded_rows: 109162` | `integrity_selfcheck.json` → `informative.magnitude_match` |
| Row accounting | `pass: true`, `origin_count: 44700`, `native_rows: 5811000`, `management_rows: 7152000` | `pass: true`, `origin_count: 231121`, `native_rows: 30045730`, `management_rows: 36979360` | `row_accounting.json` |
| Determinism | expected replay hashes recorded per cell artifact; `deterministic_replay: true` | same | `determinism.json`, `integrity_selfcheck.json` |
| Analysis reproduction | `all_equal: true` across all 13 artifacts | `all_equal: true` across all 13 artifacts | `results/analysis/reproduction-hashes.json` (`artifact_count_per_universe: 13`) |
| Holdout | no read in this analysis touches any path at or after the holdout start; all reads are the TRAIN run directory and `results/analysis/` | same | — |

The 14 hard checks reported `true` are: `causality`, `deterministic_replay`, `entry_parity`,
`fence`, `future_shift_changed_mapping`, `golden_traces`, `management_lattice`,
`management_lifecycle`, `native_lattice`, `no_native_management_cross`,
`order_fill_position_reconciliation`, `provenance`, `row_accounting`, `unique_result_keys`.

**Amendment §12 execution-lifecycle identity, verified directly.** In
`native_parameter_shared_trades.parquet`, `_entry_ns` and `_exit_ns` are non-null on **377,333 of
377,333** ctrader rows and **1,742,747 of 1,742,747** crypto rows, and the fixed side's
`fixed_entry_ns` / `fixed_exit_ns` are non-null on the same rows. Actual fills and common fills are
therefore engine-sourced on both sides, as the amendment requires.

Integrity is the only part of this document with blocking authority, and nothing here blocks.

## 2. Cost scope — disclosure, recording defect, and what is actually charged

**Declared scope (intact upstream).** `config.json` → `spread_cost_disclosure` and
`run_summary.json` → `spread_cost_disclosure` both carry, verbatim:

```text
spread_cost_status: UNAVAILABLE_NOT_CHARGED
spread_rt_bps: null
cost_scope: PARTIAL_FEES_FUNDING_ONLY
implication: reported cost understates total cost; reported net performance is overstated
prohibited_claims: fully-net, cost-complete, tradable, deployable
```

Spread is **not charged**. Every outcome figure in this document therefore **overstates** what the
same trades would return once spread is applied.

**Known recording defect (mirrored columns).** The three mirrored disclosure columns in
`per_stratum_estimates.parquet` are null in every row:

| Column | ctrader non-null | crypto non-null |
|---|---|---|
| `spread_cost_status` | 0 of 2,413 | 0 of 19,956 |
| `spread_rt_bps` | 0 of 2,413 | 0 of 19,956 |
| `cost_scope` | 0 of 2,413 | 0 of 19,956 |

Mechanism of the defect, located in `python/src/xen/adaptive_management/analysis.py` (~line 1279):
the columns are filled with `config.get("spread_cost_status")`, `config.get("spread_rt_bps")` and
`config.get("cost_scope")`, i.e. from the **top level** of `config.json`; the disclosure actually
lives nested under the `spread_cost_disclosure` key. The lookup misses and writes null. This is a
mirroring bug only — the disclosure itself is present and correct in the run config and run summary,
so the scope statement is not lost, only un-mirrored into the estimate table.

**Commission / partial-cost fields are NOT populated — checked.** Beyond the mirroring defect, the
partial-cost view is empty everywhere:

| Field | ctrader | crypto |
|---|---|---|
| `per_stratum_estimates.partial_cost_mean_bps` | 0 non-null of 2,413 | 0 non-null of 19,956 |
| `native_parameter_shared_trades.partial_cost_bps` | 0 non-null of 377,333 | 0 non-null of 1,742,747 |
| raw `positions.parquet` `commissions` | single distinct value `['0.00 USD']` across 1,448,928 rows | same form |

Consequence, stated plainly: **all outcome figures in this document are gross.** The overstatement
runs on two counts, not one — spread is never charged (declared), and the fee/funding component that
the declared `PARTIAL_FEES_FUNDING_ONLY` scope would have charged is zero and unrecorded (not
declared). `gross_mean_bps` itself is present on only 1,072 of 2,413 ctrader rows and 9,152 of 19,956
crypto rows, because the origin-lens rows do not carry per-trade payoff columns.

## 3. Question list

Answered in the sections named; nothing is left silently unanswered.

| # | Question | Answered in |
|---|---|---|
| Q1 | Do the amended execution-lifecycle identities (real `_entry_ns`, common fill on both sides) hold in the emission? | §1 |
| Q2 | What cost is actually charged, and is the disclosure intact? | §2 |
| Q3 | How many origins, fills, closes, common fills and common closes exist per universe, variant and arm class, and where do the excluded populations go? | §4 |
| Q4 | Under the origin lens, how much does each volatility component change the MR band's event rate, fill rate and per-origin outcome, per parameter and orientation? | §5 |
| Q5 | Under the trade lens, how much does each component change the actual paired trade, and on how many pairs does anything change at all? | §6 |
| Q6 | Do the four orientation pairs behave differently from the single-parameter arms? | §5, §6 |
| Q7 | What does each individual device (TARGET, STOP, TRAIL, HOLD, SIZE) do against its fixed comparator, before any combination? | §7 |
| Q8 | What do the combinations add over the individual reads? | §7.6 |
| Q9 | Do the two executed controls (TIME_DERANGEMENT, MAGNITUDE_MATCH) and the two comparator controls (FIXED_DEVICE, FIXED_NATIVE_PARAMETER) behave non-vacuously? | §8 |
| Q10 | Are the three selection-check numbers recorded, and are they informative as defined? | §9 |
| Q11 | Where is any observed effect concentrated, and would removing the tail change it? | §6.3 |
| Q12 | For each observation, is it resolved relative to its own MDE, or unresolved at this power? | §5–§8, summarised §11 |
| Q13 | What would make the headline numbers wrong? | §10 |

## 4. Populations — nothing hidden, nothing pruned

Population definitions are the ones the artifacts themselves declare in
`analysis_summary.json` → `count_definitions`: `eligible_origin_n` = eligible scheduled origins;
`entry_fill_n` = actual filled entries; `close_n` = actual confirmed closes; `common_fill_n` =
origins filled on both comparison sides; `common_close_n` = origins closed on both sides;
`effective_origin_blocks` / `effective_trade_blocks` = resampled origin/date and paired-trade/date
blocks. `block_bars: 24` in both universes.

Per-arm eligible-origin denominators are **44,700** (ctrader) and **231,121** (crypto), identical for
every arm and both entry variants — the common origin clock is fixed before any native parameter is
applied, exactly as §5 of the contract requires.

The full origin-path census (selected / excluded, by state and by arm class, all
5,811,000 ctrader and 30,045,730 crypto rows accounted for) is in Appendix A6. Two structural facts
from it:

- every `EXCLUDED` row has `mean_outcome_bps` exactly `0.000000` — the excluded population is the
  no-event / no-feature origins, which by construction carry no outcome;
- the only state with non-zero outcomes is `ORDER_CREATED`.

Variant-asymmetric bookkeeping worth flagging: `EVENT_UNDECIDED` rows appear only under `E_TOUCH`
(ctrader 1,539 origin rows; crypto 73,689) and `CENSORED` rows only under `E_CLOSE` (ctrader 8;
crypto 27). Both are retained and reported, not folded away.

Completeness gaps, retained and disclosed rather than filled: in crypto, `NATIVE` arms have 1,600
`ALL` rows but only 1,568 `ORDER_CREATED` rows and 1,493 `NO_EVENT` rows — 32 arm×symbol×variant
cells never created an order and are therefore absent from the `ORDER_CREATED` slice. ctrader shows
the same pattern at 192 `ALL` vs 190 `NO_EVENT` for `NATIVE`.

## 5. Native lens 1 — `COMMON_ORIGIN_OCCUPANCY_INCLUSIVE`

**What this lens is.** Per eligible origin, adaptive minus fixed, with the denominator held at the
full eligible-origin count and **zero-exposure origins included** — an origin contributes 0 when the
arm was occupied and could not act. It answers "what does this component do to the strategy's
opportunity set", not "what does it do to a trade". This lens is never merged with §6.

Full roll-ups are in Appendix A1 (all four universe × entry-variant blocks, every arm class,
parameter, orientation, orientation pair and component, plus the non-`ALL` state populations). Every
row of `native_parameter_origins.parquet` (2,121 ctrader / 17,176 crypto) is represented there or in
the state census; per-symbol rows are recoverable by filtering that parquet on
`symbol`, `entry_variant`, `arm_id`, `state`.

### 5.1 The fixed comparator

| Universe | Variant | eligible_origin_n | observed_event_n | event_rate | entry_fill_n | fill_rate | close_n | exposure/origin (bps, median over symbols) | effective_origin_blocks |
|---|---|---|---|---|---|---|---|---|---|
| ctrader | E_TOUCH | 44,700 | 44,637 | 0.9986 | 8,496 | 0.1901 | 8,496 | 0.071 | 2,229 |
| ctrader | E_CLOSE | 44,700 | 44,126 | 0.9872 | 7,537 | 0.1686 | 7,537 | 0.053 | 2,229 |
| crypto | E_TOUCH | 231,121 | 230,550 | 0.9975 | 43,077 | 0.1864 | 43,077 | 0.443 | 9,637 |
| crypto | E_CLOSE | 231,121 | 227,045 | 0.9824 | 38,212 | 0.1653 | 38,211 | 0.435 | 9,637 |

Reading: under the fixed `z=1.5, H=12` band, essentially every eligible origin produces a band event,
but only 17–19% of origins convert to an actual fill. The binding constraint on the MR breach
strategy is **not** event availability; it is conversion from event to fill under one-position-per-
instrument occupancy. That framing matters for §5.2: an arm that changes the event rate is not
thereby changing the traded population by the same amount.

### 5.2 What `H` does, and what `z` does — mechanism

The two native parameters act through different channels, and the data separate them cleanly.

- **`H` (band lifetime) moves the event rate hard and the fill rate barely.** ctrader E_TOUCH,
  `BAND_H DIRECT LEVEL_FORECAST_K12`: event rate `0.5791` against the fixed `0.9986`, fill rate
  `0.1132` against `0.1901`. Same variant, `BAND_H DIRECT LEVEL_NOW`: event rate `0.9715`, fill rate
  `0.1891` — nearly unchanged. Mechanism: `H` decides how long a zone stays alive; components whose
  `LONG_ON_HIGH` schedule shortens the band on the more common state (the `LEVEL_FORECAST`
  components, which are `HIGH` roughly half the time) cut the event rate roughly in half, while
  components that are `HIGH` almost always leave it near the fixed value.
- **`z` (band width) leaves the event rate near the fixed value and moves *which* price the entry
  happens at.** ctrader E_TOUCH `BAND_Z DIRECT RANGE_SCALE`: event rate `0.9991`, fill rate `0.1970`
  — both essentially at the fixed level, yet the per-origin estimate is `-0.102` bps, the largest
  single-parameter magnitude in that block. Mechanism: a narrower or wider band changes the level the
  breach is measured against, so the same origin fires at a different price.

Neither channel supplies direction, consistent with the design's `MECHANISM` block.

### 5.3 Size of the per-origin changes against their own noise floor

ctrader, both variants, all 64 adaptive native arms plus the 4 orientation pairs per component: the
median per-symbol estimate lies in `[-0.151, +0.078]` bps and the median MDE in `[0.053, 0.282]` bps.
Estimates are of the same order as, or smaller than, the detectable floor. Per-symbol CI exclusions
are correspondingly rare — in the E_TOUCH block, 6 arms of 65 have exactly one of three symbol CIs
above zero and 2 have one below; every other arm has 0 and 0.

crypto is wider on both sides: median estimates in `[-0.806, +0.752]` bps, median MDE in
`[0.436, 2.353]` bps. Per-symbol CI exclusions occur in both directions within the same arm — e.g.
E_TOUCH `BAND_H DIRECT LEVEL_NOW`: 1 of 25 symbols above zero, 2 of 25 below; E_CLOSE
`BAND_Z+BAND_H REVERSE_REVERSE TAIL_RISK`: 3 of 25 above zero, 0 below, median `+0.312` bps against
an MDE of `1.696`.

Plain reading: **at the origin lens, no component's per-origin change is resolved against its own
noise floor in either universe, in either entry variant, for either parameter or for any orientation
pair.** That is an observation about resolution at this population size, not a statement that the
change is zero.

### 5.4 Orientation

All four orientation pairs are emitted for all eight executable component IDs
(`DIRECT_DIRECT`, `DIRECT_REVERSE`, `REVERSE_DIRECT`, `REVERSE_REVERSE`), for both variants, in both
universes — 32 combination arms per variant, matching the contract's declared grid. The single-
parameter `DIRECT` / `REVERSE` arms and the `FIXED` comparator are emitted alongside. Neither
orientation is systematically larger: in the ctrader E_TOUCH `BAND_Z` block the `DIRECT` medians run
`-0.134 … +0.038` and the `REVERSE` medians `-0.116 … +0.030`; in the E_CLOSE block `DIRECT` runs
`-0.077 … +0.035` and `REVERSE` `-0.085 … +0.053`. The orientation labels behave as identifiers, as
the contract intends, and not as a favourable/unfavourable split.

## 6. Native lens 2 — `COMMON_CLOSE_TRADE`

**What this lens is.** Actual paired trades: origins where **both** the adaptive and the fixed side
produced a real fill and a real close, with engine `_entry_ns` / `_exit_ns` on both sides. The
estimand is `paired_outcome_delta_bps` = adaptive outcome minus fixed outcome on the same origin.
This lens is never merged with §5, and it answers a different question: given that both sides traded
the same origin, how different was the trade?

Full per-arm tables (every arm class, parameter, orientation, orientation pair and component, both
variants, both universes, with `common_close_n`, mean, median, block-bootstrap CI at `block=24`, the
seed band on the lower bound, MDE and effective trade blocks) are in Appendix A2. CIs there are
computed with the canonical `xen.evaluation.block_bootstrap_ci` (5-seed battery, 2,000 resamples,
seed 240730), not with experiment-local code.

### 6.1 `H` arms carry no trade-lens signal at all — and this is structural

For **every** `BAND_H` arm, in both universes and both entry variants:

| Universe | Variant | Parameter | shared-trade rows | share with identical `_entry_ns` on both sides | share with non-zero delta | mean delta |
|---|---|---|---|---|---|---|
| ctrader | E_TOUCH | BAND_H | 91,227 | 1.000000 | 0.000000 | 0.000 |
| ctrader | E_CLOSE | BAND_H | 60,966 | 1.000000 | 0.000000 | 0.000 |
| crypto | E_TOUCH | BAND_H | 464,860 | 1.000000 | 0.000000 | 0.000 |
| crypto | E_CLOSE | BAND_H | 304,139 | 1.000000 | 0.000000 | 0.000 |

Mechanism: `H` decides only whether and for how long a zone remains eligible to fire. Conditional on
both the adaptive and the fixed side having actually filled the same origin, the breach level, the
side and the entry bar are identical, so it is literally the same trade on both sides. The delta is
exactly zero by identity, not approximately zero by measurement.

The consequence is a reporting rule, not a finding about the component: **`H` arms are informative
only in the origin lens (§5), where they change the event and fill rates; the trade lens cannot see
them.** Any attempt to read an `H` effect from paired trades is reading a structural zero.

### 6.2 `z` and `z+H` arms — most paired trades are also identical

| Universe | Variant | Parameter | rows | share identical entry | share non-zero delta | mean delta, all pairs | mean delta, differing pairs only |
|---|---|---|---|---|---|---|---|
| ctrader | E_TOUCH | BAND_Z | 43,207 | 0.786632 | 0.213299 | 0.130 bps | 0.612 bps |
| ctrader | E_TOUCH | BAND_Z+BAND_H | 85,314 | 0.793211 | 0.206742 | 0.150 | 0.728 |
| ctrader | E_CLOSE | BAND_Z | 33,082 | 0.715706 | 0.284294 | 0.361 | 1.269 |
| ctrader | E_CLOSE | BAND_Z+BAND_H | 63,537 | 0.730031 | 0.269969 | 0.235 | 0.872 |
| crypto | E_TOUCH | BAND_Z | 176,113 | 0.771283 | 0.228291 | 0.628 | 2.750 |
| crypto | E_TOUCH | BAND_Z+BAND_H | 350,938 | 0.775738 | 0.223891 | 0.512 | 2.285 |
| crypto | E_CLOSE | BAND_Z | 151,973 | 0.694505 | 0.304850 | 2.196 | 7.203 |
| crypto | E_CLOSE | BAND_Z+BAND_H | 294,724 | 0.706213 | 0.293159 | 1.758 | 5.997 |

Mechanism: `q = clip(scale / calibration_median_scale, 0.5, 2.0)` and the resulting `z` is clipped
to `[1.00, 2.00]`. On 69–79% of common closes the adaptive `z` lands close enough to `1.50` that the
same minute bar breaches both bands, so the entry timestamp and price coincide and the delta is
exactly zero. The median paired delta is therefore `0.000` for **every** `z`-bearing arm in every
block of Appendix A2. All of the mean is carried by the 21–30% minority where the bands actually
diverged.

`E_CLOSE` diverges more often than `E_TOUCH` in both universes (28.4% vs 21.3% ctrader; 30.5% vs
22.8% crypto), which follows from the mechanism: an outside-close test resolves at bar granularity,
so a band shift is more likely to flip the outcome than a touch test that only needs the extreme to
reach the level.

### 6.3 Concentration — where the mean actually lives, and it is not stable

Restricting to the differing pairs and ranking by `|delta|`, the largest 1% contribute:

| Universe | Variant | Parameter | differing pairs | summed delta | contribution of the largest 1% |
|---|---|---|---|---|---|
| ctrader | E_CLOSE | BAND_Z | 9,405 | 11,934.5 bps | 4,854.8 bps (40.7%) |
| ctrader | E_CLOSE | BAND_Z+BAND_H | 17,153 | 14,952.7 | 9,949.3 (66.5%) |
| ctrader | E_TOUCH | BAND_Z | 9,216 | 5,636.7 | 2,957.0 (52.5%) |
| ctrader | E_TOUCH | BAND_Z+BAND_H | 17,638 | 12,836.2 | 8,970.4 (69.9%) |
| crypto | E_CLOSE | BAND_Z | 46,329 | 333,720.7 | 102,686.3 (30.8%) |
| crypto | E_CLOSE | BAND_Z+BAND_H | 86,401 | 518,172.1 | 244,723.9 (47.2%) |
| crypto | E_TOUCH | BAND_Z | 40,205 | 110,579.0 | **−30,762.3 (−27.8%)** |
| crypto | E_TOUCH | BAND_Z+BAND_H | 78,572 | 179,519.3 | **−29,989.0 (−16.7%)** |

Two things follow, and they point in opposite directions:

- in six of eight cells the extreme 1% supplies 31–70% of the entire summed difference — the mean is
  a tail statistic, and the median is flat zero;
- in the two crypto `E_TOUCH` cells the extreme 1% contributes with the **opposite sign** to the
  bulk, i.e. removing the tail would make the mean *larger*, not smaller.

The sign of the tail's contribution is therefore not stable across entry variant or universe. This is
reported as a concentration property of the estimand, not as a defect.

### 6.4 Resolution at the arm level

Appendix A2 gives the block-bootstrap CI for each arm. In the ctrader `E_TOUCH` block, of the 48
`z`-bearing arms exactly two have a CI excluding zero:
`NATIVE_COMBINATION BAND_Z+BAND_H DIRECT_REVERSE SWING_GT_CUR`, `+1.292` bps,
CI `[0.371, 2.219]`, `common_close_n 2,713`, seed band on the lower bound `[0.359, 0.421]`,
MDE `6.238`; and `NATIVE_COMBINATION BAND_Z+BAND_H DIRECT_REVERSE SWING_SCALE`, `−0.648` bps,
CI `[−1.198, −0.131]`, `common_close_n 3,741`, seed band `[−1.218, −1.187]`, MDE `4.022`. Both sit an
order of magnitude below their own MDE, and neither is reproduced by the same component's
single-parameter arm. Every other arm's CI spans zero. The MDE range across the block is
`3.4–10.4` bps against estimates of `|0.0–1.3|` bps.

Plain reading: the trade lens is **unresolved at this population for essentially every arm**, in both
universes and both variants.

## 7. Devices — individual reads before any combination

Device tables are per device, per component, per setting, per metric, per comparator, with all six
populations and both effective counts. Full roll-ups for all five devices, both variants and both
universes are in Appendix A3, and every row of `device_{target,stop,trail,hold,size}.parquet` is
covered by the state census plus those roll-ups. Per-symbol rows are recoverable by filtering the
device parquet on `symbol`, `entry_variant`, `arm_id`, `state`, `metric_name`.

Row availability, stated up front rather than hidden: most device rows are zero-population
bookkeeping states. ctrader `device_target.parquet` has 344 rows with a defined estimate out of
2,040; `device_stop` 288 of 1,848; `device_trail` 198 of 1,053; `device_hold` 282 of 1,284;
`device_size` 495 of 1,188. crypto: 3,408 of 16,232; 3,084 of 14,704; 1,907 of 8,391; 2,406 of
10,140; 4,037 of 9,548. The undefined rows are `NO_FEATURE`, `NO_EVENT`, `INCOMPLETE` and
`EVENT_UNDECIDED` states with `episode_n = 0`; they are retained in the artifacts and counted here.

Second population caveat, larger in effect: paired device estimates are computed on **common
closes**, which can be far fewer than the fills. Example, ctrader `E_TOUCH`
`MANAGEMENT_DEVICE_COMBINATION RANGE_SCALE M1.00` target: `entry_fill_n 57,650` but
`common_close_n 1,121`. Every device estimate below is a statement about the common-close
population, not about all fills.

### 7.1 A structural fact that governs the whole device section

For every pure `TARGET` arm the observed `reach_rate` is `1.000` and for every pure `STOP` arm the
observed `stop_rate` is `1.000` — fixed comparators and adaptive arms alike, both universes, both
variants. This is the §12 amendment working as written: pure `TARGET` / `STOP` / `TRAIL` arms keep
price-only semantics with no hidden time cap, so the episode can only end at the device. The device
is absorbing.

Consequence: `reach_rate` and `stop_rate` carry no discriminating information in this design, and the
informative device-native measures are the distance, capture, severity and timing measures. This is
stated as a design property, not as a shortcoming of any component.

### 7.2 TARGET

crypto and ctrader are reported separately; the ctrader block is small.

- ctrader `E_TOUCH`, `RANGE_SCALE M1.00` against `FIXED_TARGET_M1.00`: `realised_capture_bps` median
  `+2.437` (observed `9.915` vs comparator `7.376`), 2 of 3 symbol CIs above zero, 1 below, MDE
  `3.317`, `common_close_n 211`, `effective_trade_blocks 40`. Paired `missed_excess_bps` median
  `−1.608`, 1 CI above / 2 below, MDE `2.734`.
- ctrader `E_TOUCH`, `SWING_SCALE M0.75`: `realised_capture_bps` `+190.956` on **`common_close_n 3`**,
  one symbol only, MDE `71.138`. Reported in full and unpruned; a three-trade cell.
- The state-conditioned arms (`STATE_LOW_075_HIGH_150` on `LEVEL_NOW`, `LEVEL_FORECAST_K4/K12`,
  `SHOCK`, `SWING_GT_CUR`, `TAIL_RISK`) show medians within `±0.21` bps of the fixed target with
  0 of 3 CIs excluding zero in almost every case.

Mechanism reading for the `RANGE_SCALE` rows: an adaptive distance set from the event's own scale is
wider than the frozen TRAIN-median distance when the event is large, so a reached target captures
more — and correspondingly the episodes that reach it take longer (`time_to_target` median `+0.949`
at `M1.00`, `+4.521` at `M1.50`). Capture and duration move together, which is what a distance
change should do.

### 7.3 STOP

crypto `E_TOUCH`, `RANGE_SCALE` adaptive distances against their matched fixed comparators — this is
the most consistent single-device pattern in the run:

| Setting | Metric | observed med | comparator med | est med | est min | est max | CI>0 | CI<0 | MDE med | common_close_n | eff_trade_blocks |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M0.75 | adverse_excursion_bps | 101.037 | 72.583 | +28.002 | −43.188 | 133.477 | 20/25 | 1/25 | 16.940 | 2,185 | 416 |
| M0.75 | loss_severity_bps | −72.761 | −43.990 | −25.236 | −110.359 | 28.666 | 1/25 | 20/25 | 11.095 | 2,185 | 416 |
| M1.00 | adverse_excursion_bps | 121.594 | 91.283 | +28.813 | −133.872 | 490.878 | 20/25 | 1/25 | 22.199 | 1,618 | 344 |
| M1.00 | loss_severity_bps | −91.005 | −58.727 | −27.290 | −296.334 | 33.300 | 1/25 | 22/25 | 18.565 | 1,618 | 344 |
| M1.50 | adverse_excursion_bps | 171.576 | 131.346 | +39.901 | −110.541 | 289.671 | 15/25 | 1/25 | 44.440 | 648 | 196 |
| M1.50 | loss_severity_bps | −145.255 | −87.910 | −40.015 | −222.088 | 78.336 | 1/25 | 18/25 | 29.013 | 648 | 196 |

Mechanism: `adaptive distance = m × causal event scale` versus `fixed distance = m × TRAIN-median
scale`. On the crypto universe the event-conditional scale at a breach is systematically above the
TRAIN median, so the adaptive stop sits further away; an absorbing stop that sits further away is
reached later, after a larger adverse excursion, and books a larger loss when reached. The estimates
exceed their MDEs and the direction is consistent across 15–22 of 25 symbols. This is a **mechanical
consequence of the distance rule**, not evidence that the volatility input improved or worsened
anything — the same widening would follow from any rule that widens the stop.

The state-conditioned stop arms are much smaller: `LEVEL_NOW STATE_LOW_075_HIGH_150` gives
`adverse_excursion_bps +6.860` (8/25 above zero, 1 below, MDE `10.554`) and `loss_severity_bps
−4.231` (1 above, 9 below, MDE `6.761`); the forecast arms are smaller still
(`+0.437` and `+0.382` on adverse excursion, MDE `2.3–2.6`).

### 7.4 TRAIL

crypto `E_TOUCH`, `RANGE_SCALE` against matched fixed trails:

| Setting | Metric | observed med | comparator med | est med | CI>0 | CI<0 | MDE med | common_close_n |
|---|---|---|---|---|---|---|---|---|
| M0.75 | peak_giveback_bps | 71.175 | 56.469 | +9.386 | 16/25 | 0/25 | 8.136 | 2,812 |
| M1.00 | peak_giveback_bps | 94.351 | 69.443 | +20.948 | 16/25 | 0/25 | 12.341 | 1,719 |
| M1.50 | peak_giveback_bps | 139.657 | 102.063 | +30.885 | 21/25 | 0/25 | 18.343 | 896 |
| M0.75 | favourable_excursion_captured | 0.384 | 0.330 | +0.044 | 9/25 | 1/25 | 0.056 | 2,812 |
| M1.00 | favourable_excursion_captured | 0.385 | 0.381 | +0.005 | 4/25 | 2/25 | 0.054 | 1,719 |
| M1.50 | favourable_excursion_captured | 0.402 | 0.387 | −0.003 | 4/25 | 2/25 | 0.061 | 896 |

Mechanism, same as §7.3: a wider trail gives back more of the peak before it triggers. Peak giveback
rises consistently and clears its MDE; the measure that would say whether the wider trail was worth
it — `favourable_excursion_captured` — does **not** resolve, with CI exclusions in both directions at
`M1.00` and `M1.50`. The `SHOCK STATE_LOW_075_HIGH_150` arm runs the other way on capture
(`−0.026`, 1 above / 5 below) and on giveback (`−1.540`, 2 above / 7 below).

### 7.5 HOLD

crypto `E_TOUCH`, `STATE_LOW_4_HIGH_12` against `FIXED_HOLD_B4`:

| Component | Metric | observed med | comparator med | est med | CI>0 | CI<0 | MDE med | common_close_n |
|---|---|---|---|---|---|---|---|---|
| LEVEL_NOW | opportunity_duration | 2.744 | 1.751 | +0.973 | 25/25 | 0/25 | 0.185 | 15,131 |
| LEVEL_NOW | decay_bps | 179.428 | 145.783 | +37.153 | 24/25 | 0/25 | 9.937 | 15,131 |
| LEVEL_NOW | outcome_by_time_bps | −0.110 | 3.398 | −2.975 | 1/25 | 0/25 | 12.498 | 15,131 |
| LEVEL_FORECAST_K4 | opportunity_duration | 2.766 | 1.797 | +0.939 | 24/25 | 0/25 | 0.233 | 9,054 |
| LEVEL_FORECAST_K4 | outcome_by_time_bps | 1.510 | 3.081 | −1.804 | 3/25 | 1/25 | 15.609 | 9,054 |
| SWING_GT_CUR | opportunity_duration | 2.649 | 1.806 | +0.883 | 23/25 | 0/25 | 0.182 | 15,093 |
| SHOCK (`STATE_SHOCK_2`) | opportunity_duration | 0.889 | 1.794 | −0.918 | 0/25 | 25/25 | 0.075 | 20,233 |
| SHOCK (`STATE_SHOCK_2`) | decay_bps | 113.946 | 167.432 | −49.672 | 0/25 | 25/25 | 9.308 | 20,233 |
| SHOCK (`STATE_SHOCK_2`) | outcome_by_time_bps | 3.886 | 4.171 | −0.394 | 0/25 | 0/25 | 10.036 | 20,233 |

Mechanism, stated plainly: these arms *are* duration settings. `STATE_LOW_4_HIGH_12` holds 12 bars in
the high state instead of 4; `STATE_SHOCK_2` holds 2 bars instead of 4. That `opportunity_duration`
and `decay_bps` move in the declared direction across 23–25 of 25 symbols is the arm doing exactly
what it is defined to do, and is not independent evidence about the volatility component. The measure
that is not mechanically forced — `outcome_by_time_bps` — does **not** resolve for any component
(medians `−2.975 … +0.465`, MDE `10.0–16.1`, at most 3 of 25 CIs on either side).

`holding_efficiency` is thinly populated (crypto `FIXED_HOLD_B2` has it on 2 symbol rows,
`common_close_n 514`; `FIXED_HOLD_B12` on 5 rows, `n 2,036`) and is reported as-is.

### 7.6 SIZE, and what the combinations add

crypto `E_TOUCH`, size arms against `FIXED_SIZE_UNIT` (`common_close_n 43,077`,
`effective_trade_blocks 9,637` for every row — size arms close at the amended fixed 4-H1-bar hold,
so the population is the full fixed-hold trade set):

| Component / setting | risk_dispersion | tail_loss_bps | drawdown_bps | concentration |
|---|---|---|---|---|
| LEVEL_NOW `STATE_HALVE_HIGH` | −59.108 (0 above / 25 below, MDE 17.762) | −103.391 (0/23, MDE 49.083) | +2,431.650 (6/0, MDE 3,283.724) | 0.000 (3/0, MDE 0.003) |
| TAIL_RISK `STATE_HALVE_HIGH` | −55.181 (0/25, MDE 15.878) | −101.975 (0/23, MDE 53.840) | +2,471.486 (5/0, MDE 3,146.063) | 0.000 (5/1) |
| SHOCK `STATE_HALVE_HIGH` | −26.694 (0/25, MDE 9.993) | −42.815 (0/19, MDE 33.629) | +1,026.627 (1/0, MDE 2,375.875) | 0.000 (7/0) |
| LEVEL_FORECAST_K4 `STATE_HALVE_HIGH` | −23.836 (0/25, MDE 9.159) | −33.651 (0/18, MDE 39.165) | +1,238.298 (1/0, MDE 2,742.103) | 0.000 (12/0) |
| LEVEL_FORECAST_K12 `STATE_HALVE_HIGH` | −22.339 (0/24, MDE 7.066) | −33.651 (0/17, MDE 34.293) | +1,087.276 (1/0, MDE 2,365.122) | 0.000 (12/0) |
| RANGE_SCALE `SCALE_NORMALISED` | +5.187 (9 above / 7 below, MDE 22.920) | +11.923 (5/3, MDE 56.531) | −314.105 (1/2, MDE 3,996.028) | 0.000 (2/3) |

Mechanism: `STATE_HALVE_HIGH` halves risk in the high state, so dispersion and tail loss fall on 24–25
of 25 symbols and clear their MDEs — again, the arm doing what it is defined to do, and per the
contract explicitly a restraint arm, not an expectancy claim. `drawdown_bps` moves toward zero but
does **not** clear its MDE in 19–24 of 25 symbols. The one size arm that does not follow the pattern
is `RANGE_SCALE SCALE_NORMALISED`, whose `clip(median_scale/event_scale, 0.5, 2.0)` rule raises size
as often as it lowers it: dispersion `+5.187` with 9 symbol CIs above zero and 7 below — genuinely
mixed, and reported as mixed.

**Combinations.** `MANAGEMENT_COMPONENT_COMBINATION` and `MANAGEMENT_DEVICE_COMBINATION` rows are
reported in Appendix A3 after the individual rows, per §7 of the contract. Two observations:

- component combinations largely track the stronger of their parts —
  crypto `E_TOUCH` size `STATE_LOW_075_HIGH_150_ON_SHOCK`: dispersion `−66.347` (0/25),
  tail loss `−125.795` (0/23), i.e. the same direction and a somewhat larger magnitude than the
  single `SHOCK STATE_HALVE_HIGH` row above;
- device combinations behave differently from either device alone because the devices compete. crypto
  `E_TOUCH` trail `MANAGEMENT_DEVICE_COMBINATION RANGE_SCALE M1.00`:
  `favourable_excursion_captured −2.155` (0 above / 12 below), `loss_tail_bps −268.007`
  (0/23), `peak_giveback_bps +48.460` (25/0). ctrader `E_TOUCH` target under the same class:
  `reach_rate −0.466` (0 above / 4 below) — the only place in the run where a reach rate departs from
  `1.000`, because a competing stop now ends episodes the pure target arm would have carried to the
  target. This is the clearest demonstration in the run that the pure-device reads in §7.1–§7.5 are
  conditional on there being no competing exit.

## 8. Controls

All four declared controls are present in `controls.parquet`; two are computed and two are pointers
to the tables that carry them.

| Control | Population | Comparator | ctrader rows | crypto rows | Status |
|---|---|---|---|---|---|
| `TIME_DERANGEMENT` | `ELIGIBLE_ORIGIN_TIME_DERANGED` | `FIXED_NATIVE_BAND_E_TOUCH` / `_E_CLOSE` | 384 | 3,200 | computed, estimate on every row |
| `MAGNITUDE_MATCH` | `ELIGIBLE_ORIGIN_MAGNITUDE_STRATUM` | `FIXED_NATIVE_BAND_E_TOUCH` / `_E_CLOSE` | 1,536 | 12,800 | computed, estimate on every row |
| `FIXED_DEVICE` | `COMMON_CLOSE_TRADE` | `DECLARED_FIXED_DEVICE` | 1 | 1 | pointer row, `undefined_reason: REPORTED_IN_DEVICE_TABLES` |
| `FIXED_NATIVE_PARAMETER` | `ELIGIBLE_ORIGIN` | `DECLARED_FIXED_NATIVE` | 1 | 1 | pointer row, `undefined_reason: REPORTED_IN_NATIVE_PARAMETER_ORIGINS` |

The two comparator controls are therefore **not missing** — they are the fixed-device and
fixed-native comparators reported throughout §5, §6 and §7, and `controls.parquet` carries an
explicit pointer row rather than a duplicate estimate. Both comparator classes appear in the data:
13 `comparator_id` values in `per_stratum_estimates.parquet` covering `FIXED_NATIVE_BAND_E_TOUCH`,
`FIXED_NATIVE_BAND_E_CLOSE`, `FIXED_TARGET_M{0.75,1.00,1.50}`, `FIXED_STOP_M{0.75,1.00,1.50}`,
`FIXED_TRAIL_M{0.75,1.00,1.50}`, `FIXED_HOLD_B4` and `FIXED_SIZE_UNIT` (the hold table additionally
carries `FIXED_HOLD_B2` and `FIXED_HOLD_B12`).

### 8.1 TIME_DERANGEMENT — non-vacuous, and small

Non-vacuity is attested at the run level: `zero_fixed_points: true`, seed `240730`, 44,703 (ctrader) /
231,146 (crypto) deranged rows. The control changes component-to-episode alignment and therefore the
adaptive device values, which is the right form for this estimand — it is not a mean-invariant
permutation.

ctrader, aligned-minus-deranged per component, per-symbol medians (24 rows per component per variant,
`count 357,600`, `effective_count 17,832`):

| Component | E_TOUCH median | E_TOUCH MDE | E_CLOSE median | E_CLOSE MDE |
|---|---|---|---|---|
| LEVEL_FORECAST_K12 | −0.027 | 0.244 | −0.005 | 0.231 |
| LEVEL_FORECAST_K4 | −0.004 | 0.246 | +0.012 | 0.236 |
| LEVEL_NOW | −0.024 | 0.231 | +0.016 | 0.192 |
| RANGE_SCALE | −0.024 | 0.193 | +0.040 | 0.180 |
| SHOCK | −0.050 | 0.221 | +0.018 | 0.207 |
| SWING_GT_CUR | −0.037 | 0.225 | −0.000 | 0.197 |
| SWING_SCALE | −0.035 | 0.178 | −0.002 | 0.176 |
| TAIL_RISK | −0.017 | 0.227 | +0.021 | 0.201 |

Every median sits at roughly one fifth of its own MDE. crypto is wider — E_TOUCH medians
`−0.353 … +0.011` against MDE `1.78–2.06`, E_CLOSE `−0.444 … +0.122` against MDE `1.47–1.82` — with
per-symbol CI exclusions in both directions inside the same component (E_TOUCH `LEVEL_FORECAST_K12`:
2 of 200 rows above zero, 14 below; E_CLOSE `TAIL_RISK`: 9 above, 0 below).

Reading, deliberately narrow: at the origin lens, breaking the component's alignment to event time
does not produce a difference large enough to resolve against this population's own noise floor. Per
the contract the collapse fraction here is descriptive only and cannot gate anything.

### 8.2 MAGNITUDE_MATCH — the estimate depends on the magnitude bin, and not consistently

Four magnitude bins (`0.0`–`3.0`) × 8 components × 2 variants, 24 symbol rows per cell in ctrader
(`count ≈ 87,000`, `effective_count 5,784–7,088` rising then falling across bins).

ctrader `E_TOUCH` shows a monotone gradient across bins for **every** component: bin 0 medians run
`+0.046 … +0.342`, bin 1 `−0.046 … +0.289`, bin 2 `−0.217 … +0.105`, bin 3 `−0.842 … −0.417`. The
state-minus-matched-state difference is most negative in the largest-magnitude bin for all eight
components.

ctrader `E_CLOSE` does **not** reproduce that gradient: bin 3 medians run `+0.276 … +0.539` for the
level and forecast components, i.e. the opposite sign in the same bin. Both variants' full bin
tables are in Appendix A4.

Reading: the magnitude-matched comparison is sensitive to the magnitude stratum, and the direction of
that sensitivity flips between entry variants. A pooled magnitude-match number would hide this, so
none is offered.

## 9. Selection checks and state sections

The contract's three-number selection check is only two-thirds recorded, and the third number is
degenerate as defined:

| Number | ctrader | crypto | Note |
|---|---|---|---|
| `payoff_scale_ratio` | **0 non-null of 390** | **0 non-null of 3,250** | not recorded anywhere in the emission |
| `sign_share_difference` | 390 of 390, range `0.0809 … 0.1126` | 3,186 of 3,250, range `0.0647 … 0.1515` | recorded |
| `excluded_mean_median_gap` | 390 of 390, **all exactly 0.000** | 3,250 of 3,250, **all exactly 0.000** | recorded but structurally zero |

The `excluded_mean_median_gap` is zero by construction: the excluded population under this definition
is the no-event / no-feature origins, whose `outcome_bps` is `0.000000` in every row of the census
(Appendix A6), so their mean and median coincide at zero. The number is present but carries no
information about excluded *episodes*.

Selected / excluded totals: ctrader 4,905,955 selected vs 905,045 excluded; crypto 25,246,738 vs
4,798,992. Per-component splits are in Appendix A5, and they differ sharply by component — ctrader
`E_TOUCH` `RANGE_SCALE` excludes 10,174 of 357,600 while `LEVEL_FORECAST_K12` excludes 150,644,
which is the same `H`-driven event-rate mechanism described in §5.2 seen from the selection side.

`state_sections.parquet` reports `LEVEL_NOW` in both `LOW` and `HIGH` and every other state; all
non-`ORDER_CREATED` states carry `mean_outcome_bps` exactly `0.000000`. The full component × state
tables are in Appendix A5.

## 10. What would make these numbers wrong

Falsification probes run, and their results:

1. *Are the paired deltas an artifact of mismatched fills?* No — every shared-trade row has real
   `_entry_ns` / `_exit_ns` on both sides (§1), and the zero deltas are traced to identical entry
   timestamps, not to missing data (§6.1, §6.2).
2. *Is the `H`-arm zero a bug?* It is an identity: `share_identical_entry_ns = 1.000000` on all
   921,192 `BAND_H` shared-trade rows across both universes. A bug would not produce exactly
   1.000000 on every cell.
3. *Are the resolved device effects economically informative or mechanically forced?* Mechanically
   forced in the cases that resolve — distance arms widen distances (§7.3, §7.4), duration arms change
   duration (§7.5), halving arms halve risk (§7.6). In each case the co-reported outcome measure
   (`outcome_by_time_bps`, `favourable_excursion_captured`, `drawdown_bps`) does not resolve.
4. *Would trimming the tail change the trade-lens means?* Yes, and not in a stable direction — in six
   of eight cells trimming would shrink the mean sharply, in two crypto `E_TOUCH` cells it would
   enlarge it (§6.3).
5. *Are any of the CIs Monte-Carlo fragile?* The seed bands on the lower CI bound are reported for
   every arm in Appendix A2. Eight arms have a lower-bound seed band that
   straddles zero and are flagged as MC-fragile near the boundary: ctrader `E_TOUCH`
   `NATIVE BAND_Z REVERSE SWING_SCALE` (seed band `[−0.028, 0.002]`, CI `[−0.017, 0.935]`) and
   `NATIVE_COMBINATION REVERSE_DIRECT TAIL_RISK` (`[−0.052, 0.042]`), plus six crypto arms —
   `NATIVE BAND_Z REVERSE LEVEL_NOW` (`[−0.026, 0.139]`), `NATIVE BAND_Z REVERSE SWING_GT_CUR`
   (`[−0.008, 0.240]`), `NATIVE_COMBINATION REVERSE_DIRECT RANGE_SCALE` (`[−0.018, 0.091]`),
   `NATIVE_COMBINATION REVERSE_DIRECT TAIL_RISK` (`[−0.091, 0.206]`),
   `NATIVE_COMBINATION REVERSE_REVERSE LEVEL_FORECAST_K12` (`[−0.146, 0.089]`) and
   `NATIVE_COMBINATION REVERSE_REVERSE LEVEL_FORECAST_K4` (`[−0.156, 0.115]`).
6. *Do the numbers survive the cost scope?* Unknown by construction — no cost is charged at all
   (§2), so the effect of cost on any of these figures cannot be read from this run.

## 11. Observations, stated symmetrically

**Supporting the design's mechanism statement** ("confirmed volatility objects alter `z` and `H` in
both directions, changing which breach events exist, or alter post-entry distance, duration,
selection or risk normalisation"):

- `H` arms change which breach events exist, substantially: event rate `0.5791` vs the fixed `0.9986`
  for `LEVEL_FORECAST_K12` in ctrader `E_TOUCH`, with a parallel drop in fill rate `0.1132` vs
  `0.1901` (§5.2). Both universes and both variants show the same channel.
- `z` arms change the entry price on a definite minority of origins — 21.3% to 30.5% of common
  closes, with the rest exactly identical (§6.2). The mechanism is visible and quantified.
- Distance devices change post-entry distance as specified: adaptive `RANGE_SCALE` stops widen
  adverse excursion by `+28.0` to `+39.9` bps (15–20 of 25 crypto symbols with CIs excluding zero,
  above their MDEs), and adaptive trails raise peak giveback by `+9.4` to `+30.9` bps (16–21 of 25)
  (§7.3, §7.4).
- Duration devices change duration and risk-normalisation devices change risk dispersion, both across
  23–25 of 25 crypto symbols and clear of their MDEs (§7.5, §7.6).

**Contrary to any reading that these mechanisms move outcomes:**

- No component's per-origin outcome change is resolved against its own MDE anywhere in §5 — in either
  universe, either variant, either parameter, or any of the four orientation pairs.
- At the trade lens, 2 of 48 ctrader `E_TOUCH` `z`-bearing arms have CIs excluding zero, both an order
  of magnitude below their own MDE and neither reproduced by the same component's single-parameter
  arm (§6.4).
- Every device measure that is **not** mechanically forced fails to resolve: `outcome_by_time_bps`
  (medians `−2.975 … +0.465`, MDE `10.0–16.1`), `favourable_excursion_captured` at `M1.00`/`M1.50`
  (CI exclusions in both directions), `drawdown_bps` (MDE `2,365–3,996` against estimates of
  `+1,027 … +2,471`).
- The `H` arms cannot move a trade-lens outcome at all — the delta is exactly zero by identity on all
  921,192 paired rows (§6.1).
- `TIME_DERANGEMENT` medians sit at roughly one fifth of their MDE in ctrader, so breaking event-time
  alignment does not produce a resolvable difference at the origin lens (§8.1).

**Concentrated:**

- The trade-lens mean is a tail statistic: median exactly `0.000` for every `z`-bearing arm, and the
  largest 1% of differing pairs carrying 30.8%–69.9% of the summed delta in six of eight cells (§6.3).
- The tail's sign is not stable — in crypto `E_TOUCH` the extreme 1% contributes `−27.8%` (`BAND_Z`)
  and `−16.7%` (`BAND_Z+BAND_H`) of the sum, against the bulk (§6.3).
- Thin cells exist and are reported unpruned, e.g. ctrader `SWING_SCALE M0.75` target,
  `common_close_n 3`, estimate `+190.956` bps against MDE `71.138` (§7.2).

**Unresolved / open:**

- `payoff_scale_ratio` is not recorded in any row of `selection_checks.parquet` in either universe;
  one third of the contract's declared selection check is therefore unavailable (§9).
- `excluded_mean_median_gap` is structurally zero under the current excluded-population definition and
  says nothing about excluded episodes (§9).
- The mirrored cost columns in `per_stratum_estimates.parquet` are null (cause identified, §2), and
  the partial fee/funding cost is both unpopulated and zero at source — so the run's actual cost scope
  is narrower than the declared `PARTIAL_FEES_FUNDING_ONLY`.
- 32 crypto `NATIVE` arm×symbol×variant cells and 2 ctrader cells have no `ORDER_CREATED` row; they
  are retained as absent rather than imputed (§4).
- Eight trade-lens arms have Monte-Carlo-fragile CIs at the zero boundary (§10, item 5).
- `holding_efficiency` is populated on only a handful of symbol rows per hold setting (§7.5).

## 12. Claim boundary

This document describes the MR breach model only. It does not choose between `E_TOUCH` and `E_CLOSE`,
does not compare SPDR-023 with any companion experiment, does not issue a family or experiment
verdict, does not rank arms, and does not authorise any downstream stage. No cost of any kind is
charged in this run, so nothing above is a tradability or deployment statement. Per §11 of the
checkpoint contract, the checkpoint-level interpretation is the operator's, after all three analyses.

## 13. Reproduction

Analysis code written for this document, independent of the experiment's own `code/`:

- `python/experiments/SPDR-023/analysis_code/probe_map.py` — value-space census of every artifact
- `python/experiments/SPDR-023/analysis_code/probe_structure.py` — row accounting and population
  structure
- `python/experiments/SPDR-023/analysis_code/probe_concentration.py` — entry-identity and tail
  concentration of the paired trade lens
- `python/experiments/SPDR-023/analysis_code/build_tables.py` — the appendix roll-ups

Run from `python/` with `PYTHONPATH=. .venv/bin/python <script>`. All four are lint-clean under
`python/.venv/bin/ruff check`. Confidence intervals in Appendix A2 use the canonical
`xen.evaluation.block_bootstrap_ci` (`block=24`, `n_boot=2000`, `n_seeds=5`, `seed=240730`). No
canonical emission or analysis artifact was modified.

---

# Appendix — full roll-up tables

Every row of every canonical analysis artifact is either printed below or reachable by the filter
recipes given in §5, §6 and §7. Section keys: **A1** native origin lens, **A2** native trade lens,
**A3** device tables, **A4** controls, **A5** selection checks and state sections, **A6** selected /
excluded census. The cost-scope block is printed first.

## A0 — cost scope and recording defect

**ctrader per_stratum rows=2413**

```text
   spread_cost_status: non-null 0 of 2413
   spread_rt_bps: non-null 0 of 2413
   cost_scope: non-null 0 of 2413
   partial_cost_mean_bps: non-null 0 of 2413
   shared_trades.partial_cost_bps non-null: 0 of 377333
```

**crypto per_stratum rows=19956**

```text
   spread_cost_status: non-null 0 of 19956
   spread_rt_bps: non-null 0 of 19956
   cost_scope: non-null 0 of 19956
   partial_cost_mean_bps: non-null 0 of 19956
   shared_trades.partial_cost_bps non-null: 0 of 1742747
```


## A1 — native origin lens (`COMMON_ORIGIN_OCCUPANCY_INCLUSIVE`)

**universe=ctrader total_rows=2121**

**-- row census by arm_class x state (all rows retained) --**

```text
arm_class           state
FIXED_NATIVE        ALL                  6
                    EVENT_UNDECIDED      3
                    INCOMPLETE           6
                    NO_EVENT             6
                    NO_FEATURE           6
                    ORDER_CREATED        6
NATIVE              ALL                192
                    CENSORED             7
                    EVENT_UNDECIDED     96
                    INCOMPLETE         174
                    NO_EVENT           190
                    NO_FEATURE         192
                    ORDER_CREATED      192
NATIVE_COMBINATION  ALL                192
                    CENSORED             1
                    EVENT_UNDECIDED     96
                    INCOMPLETE         180
                    NO_EVENT           192
                    NO_FEATURE         192
                    ORDER_CREATED      192
```

**-- ctrader / E_TOUCH / state=ALL : arm rollup over symbols --**

| arm_class | parameter | orientation | component | sym_rows | eligible_origin_n | observed_event_n | entry_fill_n | close_n | event_rate | fill_rate | exposure/origin med | est med | est min | est max | CI>0 | CI<0 | mde med | eff_origin_blocks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIXED_NATIVE | BAND_Z+BAND_H | FIXED | FIXED | 3 | 44700 | 44637 | 8496 | 8496 | 0.9986 | 0.1901 | 0.071 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 2229 |
| NATIVE | BAND_H | DIRECT | LEVEL_FORECAST_K12 | 3 | 44700 | 25884 | 5060 | 5060 | 0.5791 | 0.1132 | 0.042 | -0.006 | -0.038 | 0.037 | 0 | 0 | 0.162 | 2229 |
| NATIVE | BAND_H | DIRECT | LEVEL_FORECAST_K4 | 3 | 44700 | 26055 | 5062 | 5062 | 0.5829 | 0.1132 | 0.057 | 0.025 | -0.014 | 0.052 | 0 | 0 | 0.166 | 2229 |
| NATIVE | BAND_H | DIRECT | LEVEL_NOW | 3 | 44700 | 43426 | 8453 | 8453 | 0.9715 | 0.1891 | 0.046 | -0.026 | -0.034 | 0.028 | 0 | 0 | 0.056 | 2229 |
| NATIVE | BAND_H | DIRECT | RANGE_SCALE | 3 | 44700 | 44258 | 8493 | 8493 | 0.9901 | 0.1900 | 0.045 | -0.018 | -0.026 | 0.097 | 0 | 0 | 0.057 | 2229 |
| NATIVE | BAND_H | DIRECT | SHOCK | 3 | 44700 | 41987 | 8471 | 8471 | 0.9393 | 0.1895 | 0.067 | -0.004 | -0.041 | 0.146 | 0 | 0 | 0.063 | 2229 |
| NATIVE | BAND_H | DIRECT | SWING_GT_CUR | 3 | 44700 | 42047 | 8260 | 8260 | 0.9406 | 0.1848 | 0.062 | -0.009 | -0.056 | 0.104 | 0 | 0 | 0.072 | 2229 |
| NATIVE | BAND_H | DIRECT | SWING_SCALE | 3 | 44700 | 42989 | 8267 | 8267 | 0.9617 | 0.1849 | 0.044 | -0.028 | -0.036 | 0.029 | 0 | 0 | 0.070 | 2229 |
| NATIVE | BAND_H | DIRECT | TAIL_RISK | 3 | 44700 | 44160 | 8486 | 8486 | 0.9879 | 0.1898 | 0.059 | -0.014 | -0.040 | -0.012 | 0 | 0 | 0.061 | 2229 |
| NATIVE | BAND_H | REVERSE | LEVEL_FORECAST_K12 | 3 | 44700 | 25593 | 5057 | 5057 | 0.5726 | 0.1131 | 0.055 | -0.012 | -0.016 | 0.046 | 0 | 0 | 0.163 | 2229 |
| NATIVE | BAND_H | REVERSE | LEVEL_FORECAST_K4 | 3 | 44700 | 25427 | 5057 | 5055 | 0.5688 | 0.1131 | 0.017 | 0.007 | -0.063 | 0.037 | 0 | 0 | 0.163 | 2229 |
| NATIVE | BAND_H | REVERSE | LEVEL_NOW | 3 | 44700 | 42567 | 8450 | 8448 | 0.9523 | 0.1890 | 0.080 | 0.009 | 0.009 | 0.010 | 0 | 0 | 0.054 | 2229 |
| NATIVE | BAND_H | REVERSE | RANGE_SCALE | 3 | 44700 | 42083 | 8476 | 8476 | 0.9415 | 0.1896 | 0.052 | -0.004 | -0.019 | 0.044 | 0 | 0 | 0.055 | 2229 |
| NATIVE | BAND_H | REVERSE | SHOCK | 3 | 44700 | 44231 | 8474 | 8474 | 0.9895 | 0.1896 | 0.048 | -0.015 | -0.023 | 0.037 | 0 | 0 | 0.057 | 2229 |
| NATIVE | BAND_H | REVERSE | SWING_GT_CUR | 3 | 44700 | 42046 | 8268 | 8267 | 0.9406 | 0.1850 | 0.063 | -0.008 | -0.024 | -0.002 | 0 | 0 | 0.065 | 2229 |
| NATIVE | BAND_H | REVERSE | SWING_SCALE | 3 | 44700 | 41104 | 8260 | 8259 | 0.9196 | 0.1848 | 0.037 | -0.034 | -0.053 | 0.204 | 0 | 0 | 0.069 | 2229 |
| NATIVE | BAND_H | REVERSE | TAIL_RISK | 3 | 44700 | 42181 | 8484 | 8483 | 0.9436 | 0.1898 | 0.053 | 0.007 | -0.019 | 0.046 | 0 | 0 | 0.053 | 2229 |
| NATIVE | BAND_Z | DIRECT | LEVEL_FORECAST_K12 | 3 | 44700 | 26632 | 5060 | 5060 | 0.5958 | 0.1132 | 0.008 | -0.064 | -0.140 | 0.296 | 1 | 0 | 0.258 | 2229 |
| NATIVE | BAND_Z | DIRECT | LEVEL_FORECAST_K4 | 3 | 44700 | 26628 | 5099 | 5099 | 0.5957 | 0.1141 | 0.027 | 0.027 | -0.231 | 0.108 | 0 | 0 | 0.261 | 2229 |
| NATIVE | BAND_Z | DIRECT | LEVEL_NOW | 3 | 44700 | 44396 | 8498 | 8498 | 0.9932 | 0.1901 | -0.008 | 0.038 | -0.335 | 0.073 | 0 | 0 | 0.265 | 2229 |
| NATIVE | BAND_Z | DIRECT | RANGE_SCALE | 3 | 44700 | 44661 | 8805 | 8805 | 0.9991 | 0.1970 | -0.105 | -0.102 | -0.224 | -0.024 | 0 | 0 | 0.236 | 2229 |
| NATIVE | BAND_Z | DIRECT | SHOCK | 3 | 44700 | 44384 | 8072 | 8072 | 0.9929 | 0.1806 | 0.009 | -0.062 | -0.435 | 0.305 | 1 | 1 | 0.266 | 2229 |
| NATIVE | BAND_Z | DIRECT | SWING_GT_CUR | 3 | 44700 | 43361 | 8272 | 8272 | 0.9700 | 0.1851 | 0.026 | -0.045 | -0.289 | 0.220 | 0 | 0 | 0.259 | 2229 |
| NATIVE | BAND_Z | DIRECT | SWING_SCALE | 3 | 44700 | 43468 | 8535 | 8535 | 0.9724 | 0.1909 | -0.132 | -0.134 | -0.250 | -0.052 | 0 | 0 | 0.213 | 2229 |
| NATIVE | BAND_Z | DIRECT | TAIL_RISK | 3 | 44700 | 44648 | 8790 | 8790 | 0.9988 | 0.1966 | -0.040 | -0.111 | -0.279 | 0.056 | 0 | 0 | 0.269 | 2229 |
| NATIVE | BAND_Z | REVERSE | LEVEL_FORECAST_K12 | 3 | 44700 | 26568 | 5050 | 5050 | 0.5944 | 0.1130 | 0.017 | -0.054 | -0.063 | 0.022 | 0 | 0 | 0.268 | 2229 |
| NATIVE | BAND_Z | REVERSE | LEVEL_FORECAST_K4 | 3 | 44700 | 26552 | 5016 | 5016 | 0.5940 | 0.1122 | -0.012 | -0.083 | -0.124 | 0.087 | 0 | 0 | 0.251 | 2229 |
| NATIVE | BAND_Z | REVERSE | LEVEL_NOW | 3 | 44700 | 44291 | 8405 | 8405 | 0.9909 | 0.1880 | -0.062 | -0.114 | -0.233 | 0.018 | 0 | 0 | 0.259 | 2229 |
| NATIVE | BAND_Z | REVERSE | RANGE_SCALE | 3 | 44700 | 44426 | 8139 | 8139 | 0.9939 | 0.1821 | 0.087 | 0.029 | -0.239 | 0.168 | 0 | 0 | 0.215 | 2229 |
| NATIVE | BAND_Z | REVERSE | SHOCK | 3 | 44700 | 44531 | 8860 | 8860 | 0.9962 | 0.1982 | -0.072 | -0.116 | -0.143 | 0.052 | 0 | 0 | 0.279 | 2229 |
| NATIVE | BAND_Z | REVERSE | SWING_GT_CUR | 3 | 44700 | 43345 | 8255 | 8255 | 0.9697 | 0.1847 | -0.042 | -0.090 | -0.385 | 0.038 | 0 | 0 | 0.263 | 2229 |
| NATIVE | BAND_Z | REVERSE | SWING_SCALE | 3 | 44700 | 43302 | 7961 | 7961 | 0.9687 | 0.1781 | 0.040 | 0.030 | -0.208 | 0.121 | 0 | 0 | 0.185 | 2229 |
| NATIVE | BAND_Z | REVERSE | TAIL_RISK | 3 | 44700 | 44393 | 8170 | 8170 | 0.9931 | 0.1828 | -0.059 | 0.022 | -0.412 | 0.040 | 0 | 0 | 0.251 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | LEVEL_FORECAST_K12 | 3 | 44700 | 24893 | 5033 | 5033 | 0.5569 | 0.1126 | -0.017 | -0.088 | -0.129 | 0.304 | 1 | 0 | 0.261 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | LEVEL_FORECAST_K4 | 3 | 44700 | 25234 | 5074 | 5074 | 0.5645 | 0.1135 | 0.035 | -0.020 | -0.192 | 0.116 | 0 | 0 | 0.263 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | LEVEL_NOW | 3 | 44700 | 42020 | 8462 | 8462 | 0.9400 | 0.1893 | 0.017 | 0.003 | -0.339 | 0.098 | 0 | 0 | 0.273 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | RANGE_SCALE | 3 | 44700 | 43963 | 8797 | 8796 | 0.9835 | 0.1968 | -0.130 | -0.113 | -0.246 | -0.049 | 0 | 0 | 0.244 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | SHOCK | 3 | 44700 | 38753 | 8007 | 8006 | 0.8670 | 0.1791 | 0.015 | -0.056 | -0.253 | 0.348 | 1 | 0 | 0.277 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | SWING_GT_CUR | 3 | 44700 | 40238 | 8232 | 8231 | 0.9002 | 0.1842 | 0.010 | -0.061 | -0.312 | 0.214 | 0 | 0 | 0.265 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | SWING_SCALE | 3 | 44700 | 42759 | 8523 | 8523 | 0.9566 | 0.1907 | -0.098 | -0.143 | -0.228 | -0.017 | 0 | 0 | 0.208 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | TAIL_RISK | 3 | 44700 | 43412 | 8774 | 8774 | 0.9712 | 0.1963 | -0.052 | -0.124 | -0.252 | 0.108 | 0 | 0 | 0.272 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | LEVEL_FORECAST_K12 | 3 | 44700 | 26471 | 5056 | 5056 | 0.5922 | 0.1131 | 0.014 | -0.057 | -0.160 | 0.305 | 1 | 0 | 0.256 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | LEVEL_FORECAST_K4 | 3 | 44700 | 26444 | 5100 | 5098 | 0.5916 | 0.1141 | 0.032 | 0.014 | -0.210 | 0.112 | 0 | 0 | 0.265 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | LEVEL_NOW | 3 | 44700 | 44129 | 8499 | 8497 | 0.9872 | 0.1901 | -0.016 | 0.026 | -0.367 | 0.065 | 0 | 0 | 0.272 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | RANGE_SCALE | 3 | 44700 | 43836 | 8803 | 8802 | 0.9807 | 0.1969 | -0.104 | -0.119 | -0.217 | -0.023 | 0 | 0 | 0.245 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | SHOCK | 3 | 44700 | 44533 | 8065 | 8065 | 0.9963 | 0.1804 | 0.009 | -0.062 | -0.490 | 0.331 | 1 | 1 | 0.260 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | SWING_GT_CUR | 3 | 44700 | 43220 | 8273 | 8273 | 0.9669 | 0.1851 | 0.042 | -0.029 | -0.257 | 0.227 | 0 | 0 | 0.262 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | SWING_SCALE | 3 | 44700 | 42606 | 8536 | 8534 | 0.9532 | 0.1910 | -0.092 | -0.151 | -0.264 | -0.011 | 0 | 0 | 0.216 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | TAIL_RISK | 3 | 44700 | 44206 | 8794 | 8793 | 0.9889 | 0.1967 | -0.025 | -0.096 | -0.211 | 0.065 | 0 | 0 | 0.267 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | LEVEL_FORECAST_K12 | 3 | 44700 | 26520 | 5046 | 5046 | 0.5933 | 0.1129 | 0.004 | -0.068 | -0.068 | 0.029 | 0 | 0 | 0.268 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | LEVEL_FORECAST_K4 | 3 | 44700 | 26551 | 5015 | 5015 | 0.5940 | 0.1122 | -0.026 | -0.097 | -0.145 | 0.104 | 0 | 0 | 0.257 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | LEVEL_NOW | 3 | 44700 | 44283 | 8404 | 8404 | 0.9907 | 0.1880 | -0.113 | -0.124 | -0.232 | -0.032 | 0 | 0 | 0.257 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | RANGE_SCALE | 3 | 44700 | 44411 | 8140 | 8140 | 0.9935 | 0.1821 | 0.108 | 0.037 | -0.247 | 0.194 | 0 | 0 | 0.212 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | SHOCK | 3 | 44700 | 44107 | 8864 | 8864 | 0.9867 | 0.1983 | -0.084 | -0.059 | -0.156 | -0.044 | 0 | 0 | 0.276 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | SWING_GT_CUR | 3 | 44700 | 43217 | 8251 | 8251 | 0.9668 | 0.1846 | -0.059 | -0.088 | -0.270 | 0.021 | 0 | 0 | 0.269 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | SWING_SCALE | 3 | 44700 | 43165 | 7955 | 7955 | 0.9657 | 0.1780 | 0.070 | 0.017 | -0.305 | 0.150 | 0 | 0 | 0.183 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | TAIL_RISK | 3 | 44700 | 44558 | 8164 | 8164 | 0.9968 | 0.1826 | -0.111 | -0.030 | -0.356 | 0.009 | 0 | 0 | 0.255 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | LEVEL_FORECAST_K12 | 3 | 44700 | 24287 | 5026 | 5026 | 0.5433 | 0.1124 | 0.022 | -0.003 | -0.049 | 0.017 | 0 | 0 | 0.268 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | LEVEL_FORECAST_K4 | 3 | 44700 | 23951 | 4983 | 4982 | 0.5358 | 0.1115 | 0.018 | -0.050 | -0.106 | 0.099 | 0 | 0 | 0.249 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | LEVEL_NOW | 3 | 44700 | 40193 | 8349 | 8348 | 0.8992 | 0.1868 | -0.103 | -0.092 | -0.193 | -0.022 | 0 | 0 | 0.249 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | RANGE_SCALE | 3 | 44700 | 39512 | 8075 | 8075 | 0.8839 | 0.1806 | 0.078 | 0.039 | -0.233 | 0.159 | 0 | 0 | 0.213 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | SHOCK | 3 | 44700 | 43677 | 8853 | 8853 | 0.9771 | 0.1981 | -0.063 | -0.096 | -0.134 | -0.017 | 0 | 0 | 0.274 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | SWING_GT_CUR | 3 | 44700 | 40167 | 8219 | 8219 | 0.8986 | 0.1839 | -0.004 | -0.070 | -0.297 | 0.077 | 0 | 0 | 0.282 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | SWING_SCALE | 3 | 44700 | 38830 | 7903 | 7902 | 0.8687 | 0.1768 | 0.037 | -0.034 | -0.265 | 0.160 | 0 | 0 | 0.189 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | TAIL_RISK | 3 | 44700 | 39131 | 8104 | 8103 | 0.8754 | 0.1813 | -0.096 | -0.015 | -0.394 | 0.032 | 0 | 0 | 0.249 | 2229 |
**-- ctrader / E_CLOSE / state=ALL : arm rollup over symbols --**

| arm_class | parameter | orientation | component | sym_rows | eligible_origin_n | observed_event_n | entry_fill_n | close_n | event_rate | fill_rate | exposure/origin med | est med | est min | est max | CI>0 | CI<0 | mde med | eff_origin_blocks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIXED_NATIVE | BAND_Z+BAND_H | FIXED | FIXED | 3 | 44700 | 44126 | 7537 | 7537 | 0.9872 | 0.1686 | 0.053 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 2229 |
| NATIVE | BAND_H | DIRECT | LEVEL_FORECAST_K12 | 3 | 44700 | 24043 | 4450 | 4450 | 0.5379 | 0.0996 | 0.005 | -0.054 | -0.104 | 0.012 | 0 | 0 | 0.170 | 2229 |
| NATIVE | BAND_H | DIRECT | LEVEL_FORECAST_K4 | 3 | 44700 | 24463 | 4458 | 4457 | 0.5473 | 0.0997 | 0.007 | -0.020 | -0.122 | 0.014 | 0 | 0 | 0.162 | 2229 |
| NATIVE | BAND_H | DIRECT | LEVEL_NOW | 3 | 44700 | 40784 | 7461 | 7460 | 0.9124 | 0.1669 | 0.006 | 0.002 | -0.050 | 0.013 | 0 | 0 | 0.084 | 2229 |
| NATIVE | BAND_H | DIRECT | RANGE_SCALE | 3 | 44700 | 42928 | 7528 | 7527 | 0.9604 | 0.1684 | 0.016 | 0.004 | -0.037 | 0.005 | 0 | 0 | 0.066 | 2229 |
| NATIVE | BAND_H | DIRECT | SHOCK | 3 | 44700 | 36774 | 7443 | 7442 | 0.8227 | 0.1665 | 0.007 | 0.002 | -0.046 | 0.012 | 0 | 0 | 0.120 | 2229 |
| NATIVE | BAND_H | DIRECT | SWING_GT_CUR | 3 | 44700 | 39087 | 7282 | 7281 | 0.8744 | 0.1629 | 0.025 | -0.024 | -0.054 | 0.032 | 0 | 0 | 0.118 | 2229 |
| NATIVE | BAND_H | DIRECT | SWING_SCALE | 3 | 44700 | 41814 | 7319 | 7319 | 0.9354 | 0.1637 | 0.007 | -0.046 | -0.049 | -0.004 | 0 | 0 | 0.092 | 2229 |
| NATIVE | BAND_H | DIRECT | TAIL_RISK | 3 | 44700 | 42708 | 7519 | 7519 | 0.9554 | 0.1682 | -0.002 | -0.005 | -0.055 | -0.003 | 0 | 0 | 0.088 | 2229 |
| NATIVE | BAND_H | REVERSE | LEVEL_FORECAST_K12 | 3 | 44700 | 23619 | 4453 | 4453 | 0.5284 | 0.0996 | 0.024 | 0.031 | -0.090 | 0.042 | 0 | 0 | 0.167 | 2229 |
| NATIVE | BAND_H | REVERSE | LEVEL_FORECAST_K4 | 3 | 44700 | 23203 | 4447 | 4447 | 0.5191 | 0.0995 | 0.011 | 0.011 | -0.071 | 0.018 | 0 | 0 | 0.180 | 2229 |
| NATIVE | BAND_H | REVERSE | LEVEL_NOW | 3 | 44700 | 38995 | 7441 | 7441 | 0.8724 | 0.1665 | 0.015 | 0.019 | -0.038 | 0.030 | 0 | 0 | 0.109 | 2229 |
| NATIVE | BAND_H | REVERSE | RANGE_SCALE | 3 | 44700 | 37178 | 7430 | 7430 | 0.8317 | 0.1662 | 0.034 | 0.015 | -0.045 | 0.041 | 0 | 0 | 0.123 | 2229 |
| NATIVE | BAND_H | REVERSE | SHOCK | 3 | 44700 | 43220 | 7505 | 7505 | 0.9669 | 0.1679 | 0.038 | 0.016 | -0.033 | 0.045 | 0 | 0 | 0.067 | 2229 |
| NATIVE | BAND_H | REVERSE | SWING_GT_CUR | 3 | 44700 | 38968 | 7298 | 7298 | 0.8718 | 0.1633 | 0.054 | 0.000 | -0.030 | 0.017 | 0 | 0 | 0.101 | 2229 |
| NATIVE | BAND_H | REVERSE | SWING_SCALE | 3 | 44700 | 36241 | 7260 | 7259 | 0.8108 | 0.1624 | 0.050 | -0.003 | -0.006 | 0.048 | 0 | 0 | 0.129 | 2229 |
| NATIVE | BAND_H | REVERSE | TAIL_RISK | 3 | 44700 | 37398 | 7441 | 7440 | 0.8366 | 0.1665 | 0.043 | 0.025 | -0.031 | 0.050 | 0 | 0 | 0.113 | 2229 |
| NATIVE | BAND_Z | DIRECT | LEVEL_FORECAST_K12 | 3 | 44700 | 26188 | 4551 | 4551 | 0.5859 | 0.1018 | 0.062 | -0.055 | -0.074 | 0.122 | 0 | 0 | 0.237 | 2229 |
| NATIVE | BAND_Z | DIRECT | LEVEL_FORECAST_K4 | 3 | 44700 | 26241 | 4570 | 4570 | 0.5870 | 0.1022 | 0.062 | 0.026 | -0.040 | 0.070 | 0 | 0 | 0.243 | 2229 |
| NATIVE | BAND_Z | DIRECT | LEVEL_NOW | 3 | 44700 | 43805 | 7629 | 7629 | 0.9800 | 0.1707 | 0.007 | 0.014 | -0.065 | 0.041 | 0 | 0 | 0.241 | 2229 |
| NATIVE | BAND_Z | DIRECT | RANGE_SCALE | 3 | 44700 | 44449 | 7847 | 7847 | 0.9944 | 0.1755 | 0.084 | 0.019 | -0.005 | 0.091 | 0 | 0 | 0.209 | 2229 |
| NATIVE | BAND_Z | DIRECT | SHOCK | 3 | 44700 | 43275 | 7237 | 7237 | 0.9681 | 0.1619 | 0.054 | -0.048 | -0.169 | 0.061 | 0 | 0 | 0.233 | 2229 |
| NATIVE | BAND_Z | DIRECT | SWING_GT_CUR | 3 | 44700 | 42632 | 7384 | 7384 | 0.9537 | 0.1652 | 0.064 | 0.011 | -0.075 | 0.109 | 0 | 0 | 0.213 | 2229 |
| NATIVE | BAND_Z | DIRECT | SWING_SCALE | 3 | 44700 | 43204 | 7614 | 7614 | 0.9665 | 0.1703 | 0.040 | -0.077 | -0.156 | 0.091 | 0 | 0 | 0.163 | 2229 |
| NATIVE | BAND_Z | DIRECT | TAIL_RISK | 3 | 44700 | 44352 | 7888 | 7888 | 0.9922 | 0.1765 | 0.055 | 0.035 | 0.002 | 0.054 | 0 | 0 | 0.253 | 2229 |
| NATIVE | BAND_Z | REVERSE | LEVEL_FORECAST_K12 | 3 | 44700 | 26021 | 4486 | 4486 | 0.5821 | 0.1004 | 0.014 | -0.002 | -0.039 | 0.010 | 0 | 0 | 0.235 | 2229 |
| NATIVE | BAND_Z | REVERSE | LEVEL_FORECAST_K4 | 3 | 44700 | 25948 | 4441 | 4441 | 0.5805 | 0.0994 | 0.032 | -0.085 | -0.099 | 0.053 | 0 | 0 | 0.225 | 2229 |
| NATIVE | BAND_Z | REVERSE | LEVEL_NOW | 3 | 44700 | 43354 | 7436 | 7436 | 0.9699 | 0.1664 | 0.046 | -0.023 | -0.060 | 0.053 | 0 | 0 | 0.225 | 2229 |
| NATIVE | BAND_Z | REVERSE | RANGE_SCALE | 3 | 44700 | 43246 | 7211 | 7211 | 0.9675 | 0.1613 | 0.046 | 0.053 | -0.064 | 0.054 | 0 | 0 | 0.193 | 2229 |
| NATIVE | BAND_Z | REVERSE | SHOCK | 3 | 44700 | 44111 | 7949 | 7949 | 0.9868 | 0.1778 | 0.063 | 0.022 | -0.022 | 0.070 | 0 | 0 | 0.235 | 2229 |
| NATIVE | BAND_Z | REVERSE | SWING_GT_CUR | 3 | 44700 | 42601 | 7343 | 7343 | 0.9530 | 0.1643 | 0.011 | -0.024 | -0.042 | -0.001 | 0 | 0 | 0.236 | 2229 |
| NATIVE | BAND_Z | REVERSE | SWING_SCALE | 3 | 44700 | 42252 | 7050 | 7050 | 0.9452 | 0.1577 | 0.068 | 0.043 | -0.049 | 0.060 | 0 | 0 | 0.168 | 2229 |
| NATIVE | BAND_Z | REVERSE | TAIL_RISK | 3 | 44700 | 43159 | 7244 | 7244 | 0.9655 | 0.1621 | 0.047 | -0.049 | -0.070 | 0.072 | 0 | 0 | 0.223 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | LEVEL_FORECAST_K12 | 3 | 44700 | 22554 | 4483 | 4483 | 0.5046 | 0.1003 | 0.129 | 0.076 | -0.086 | 0.152 | 1 | 0 | 0.228 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | LEVEL_FORECAST_K4 | 3 | 44700 | 23125 | 4508 | 4508 | 0.5173 | 0.1009 | 0.116 | 0.050 | 0.013 | 0.123 | 1 | 0 | 0.239 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | LEVEL_NOW | 3 | 44700 | 38510 | 7535 | 7535 | 0.8615 | 0.1686 | 0.096 | 0.043 | 0.032 | 0.063 | 0 | 0 | 0.241 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | RANGE_SCALE | 3 | 44700 | 42371 | 7815 | 7814 | 0.9479 | 0.1748 | 0.088 | 0.047 | -0.012 | 0.095 | 0 | 0 | 0.203 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | SHOCK | 3 | 44700 | 32448 | 7051 | 7050 | 0.7259 | 0.1577 | 0.053 | -0.000 | -0.015 | 0.053 | 0 | 0 | 0.223 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | SWING_GT_CUR | 3 | 44700 | 36595 | 7247 | 7247 | 0.8187 | 0.1621 | 0.103 | 0.071 | -0.041 | 0.110 | 0 | 0 | 0.216 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | SWING_SCALE | 3 | 44700 | 41447 | 7582 | 7582 | 0.9272 | 0.1696 | 0.036 | -0.081 | -0.181 | 0.076 | 0 | 0 | 0.177 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | TAIL_RISK | 3 | 44700 | 41440 | 7838 | 7838 | 0.9271 | 0.1753 | 0.050 | 0.032 | -0.003 | 0.049 | 0 | 0 | 0.237 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | LEVEL_FORECAST_K12 | 3 | 44700 | 25270 | 4520 | 4520 | 0.5653 | 0.1011 | 0.083 | -0.034 | -0.108 | 0.100 | 0 | 0 | 0.235 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | LEVEL_FORECAST_K4 | 3 | 44700 | 25088 | 4559 | 4558 | 0.5613 | 0.1020 | 0.056 | 0.018 | -0.030 | 0.063 | 0 | 0 | 0.251 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | LEVEL_NOW | 3 | 44700 | 42006 | 7606 | 7605 | 0.9397 | 0.1702 | 0.004 | 0.011 | -0.067 | 0.074 | 0 | 0 | 0.252 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | RANGE_SCALE | 3 | 44700 | 40443 | 7794 | 7794 | 0.9048 | 0.1744 | 0.071 | 0.075 | -0.012 | 0.078 | 0 | 0 | 0.196 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | SHOCK | 3 | 44700 | 43990 | 7182 | 7182 | 0.9841 | 0.1607 | 0.068 | -0.047 | -0.151 | 0.075 | 0 | 0 | 0.241 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | SWING_GT_CUR | 3 | 44700 | 41504 | 7369 | 7369 | 0.9285 | 0.1649 | 0.092 | 0.021 | -0.021 | 0.099 | 0 | 0 | 0.208 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | SWING_SCALE | 3 | 44700 | 39184 | 7578 | 7577 | 0.8766 | 0.1695 | 0.066 | 0.001 | -0.092 | 0.073 | 0 | 0 | 0.172 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | TAIL_RISK | 3 | 44700 | 41441 | 7862 | 7861 | 0.9271 | 0.1759 | 0.070 | 0.033 | 0.017 | 0.068 | 0 | 0 | 0.246 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | LEVEL_FORECAST_K12 | 3 | 44700 | 25548 | 4478 | 4478 | 0.5715 | 0.1002 | 0.018 | 0.002 | -0.035 | 0.021 | 0 | 0 | 0.231 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | LEVEL_FORECAST_K4 | 3 | 44700 | 25734 | 4437 | 4437 | 0.5757 | 0.0993 | 0.037 | -0.081 | -0.081 | 0.053 | 0 | 0 | 0.222 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | LEVEL_NOW | 3 | 44700 | 42895 | 7430 | 7430 | 0.9596 | 0.1662 | 0.071 | 0.027 | -0.046 | 0.047 | 0 | 0 | 0.213 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | RANGE_SCALE | 3 | 44700 | 43383 | 7209 | 7208 | 0.9705 | 0.1613 | 0.054 | 0.061 | -0.023 | 0.092 | 0 | 0 | 0.191 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | SHOCK | 3 | 44700 | 41134 | 7931 | 7930 | 0.9202 | 0.1774 | 0.090 | 0.045 | 0.037 | 0.064 | 0 | 0 | 0.233 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | SWING_GT_CUR | 3 | 44700 | 41528 | 7329 | 7328 | 0.9290 | 0.1640 | 0.085 | -0.007 | -0.031 | 0.032 | 0 | 0 | 0.241 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | SWING_SCALE | 3 | 44700 | 42096 | 7036 | 7036 | 0.9417 | 0.1574 | 0.062 | 0.069 | -0.073 | 0.091 | 0 | 0 | 0.173 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | TAIL_RISK | 3 | 44700 | 43801 | 7242 | 7242 | 0.9799 | 0.1620 | 0.063 | -0.000 | -0.052 | 0.070 | 0 | 0 | 0.223 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | LEVEL_FORECAST_K12 | 3 | 44700 | 21954 | 4416 | 4416 | 0.4911 | 0.0988 | 0.017 | -0.008 | -0.036 | 0.064 | 0 | 0 | 0.239 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | LEVEL_FORECAST_K4 | 3 | 44700 | 21385 | 4356 | 4355 | 0.4784 | 0.0974 | 0.022 | -0.031 | -0.079 | 0.021 | 0 | 0 | 0.235 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | LEVEL_NOW | 3 | 44700 | 36048 | 7300 | 7299 | 0.8064 | 0.1633 | 0.055 | 0.017 | -0.062 | 0.068 | 0 | 0 | 0.225 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | RANGE_SCALE | 3 | 44700 | 33845 | 7028 | 7028 | 0.7572 | 0.1572 | 0.093 | 0.060 | 0.040 | 0.064 | 0 | 0 | 0.191 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | SHOCK | 3 | 44700 | 42309 | 7934 | 7934 | 0.9465 | 0.1775 | 0.074 | 0.035 | 0.021 | 0.070 | 0 | 0 | 0.240 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | SWING_GT_CUR | 3 | 44700 | 36338 | 7221 | 7220 | 0.8129 | 0.1615 | 0.093 | 0.017 | -0.023 | 0.040 | 0 | 0 | 0.241 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | SWING_SCALE | 3 | 44700 | 33146 | 6876 | 6876 | 0.7415 | 0.1538 | 0.116 | 0.073 | -0.001 | 0.129 | 0 | 0 | 0.194 | 2229 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | TAIL_RISK | 3 | 44700 | 33426 | 7045 | 7044 | 0.7478 | 0.1576 | 0.076 | 0.078 | -0.075 | 0.083 | 0 | 0 | 0.232 | 2229 |
**-- ctrader : non-ALL state populations (retained, not pruned) --**

```text
                               rows  eligible_origin_n  observed_event_n  entry_fill_n  close_n   est_med   mde_med
entry_variant state
E_CLOSE       CENSORED            8             117040                 8             0        0  0.000000  0.000000
              INCOMPLETE        180            2679678                 0             0        0  0.000000  0.000000
              NO_EVENT          195            2905500                 0             0        0  0.000000  0.037138
              NO_FEATURE        195            2905500                 0             0        0  0.000000  0.012913
              ORDER_CREATED     195            2905500           2382365        435949   435929  0.006647  0.168517
E_TOUCH       EVENT_UNDECIDED   195            2905500              1539             0        0  0.000000  0.000000
              INCOMPLETE        180            2679678                 0             0        0  0.000000  0.000000
              NO_EVENT          193            2875430                 0             0        0 -0.001235  0.013833
              NO_FEATURE        195            2905500                 0             0        0 -0.001037  0.019295
              ORDER_CREATED     195            2905500           2517999        491940   491918 -0.018765  0.187965
```

**universe=crypto total_rows=17176**

**-- row census by arm_class x state (all rows retained) --**

```text
arm_class           state
FIXED_NATIVE        ALL                  50
                    EVENT_UNDECIDED      23
                    INCOMPLETE           50
                    NO_EVENT             44
                    NO_FEATURE           50
                    ORDER_CREATED        50
NATIVE              ALL                1600
                    CENSORED              7
                    EVENT_UNDECIDED     700
                    INCOMPLETE         1424
                    NO_EVENT           1493
                    NO_FEATURE         1600
                    ORDER_CREATED      1568
NATIVE_COMBINATION  ALL                1600
                    CENSORED             20
                    EVENT_UNDECIDED     707
                    INCOMPLETE         1480
                    NO_EVENT           1542
                    NO_FEATURE         1600
                    ORDER_CREATED      1568
```

**-- crypto / E_TOUCH / state=ALL : arm rollup over symbols --**

| arm_class | parameter | orientation | component | sym_rows | eligible_origin_n | observed_event_n | entry_fill_n | close_n | event_rate | fill_rate | exposure/origin med | est med | est min | est max | CI>0 | CI<0 | mde med | eff_origin_blocks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIXED_NATIVE | BAND_Z+BAND_H | FIXED | FIXED | 25 | 231121 | 230550 | 43077 | 43077 | 0.9975 | 0.1864 | 0.443 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 9637 |
| NATIVE | BAND_H | DIRECT | LEVEL_FORECAST_K12 | 25 | 231121 | 134682 | 25553 | 25553 | 0.5827 | 0.1106 | 0.446 | 0.062 | -2.658 | 7.532 | 1 | 1 | 1.474 | 9637 |
| NATIVE | BAND_H | DIRECT | LEVEL_FORECAST_K4 | 25 | 231121 | 135230 | 25572 | 25564 | 0.5851 | 0.1106 | 0.297 | -0.055 | -8.299 | 7.261 | 1 | 1 | 1.388 | 9637 |
| NATIVE | BAND_H | DIRECT | LEVEL_NOW | 25 | 231121 | 225856 | 42781 | 42773 | 0.9772 | 0.1851 | 0.566 | 0.073 | -2.872 | 2.298 | 1 | 2 | 0.538 | 9637 |
| NATIVE | BAND_H | DIRECT | RANGE_SCALE | 25 | 231121 | 226973 | 43058 | 43051 | 0.9821 | 0.1863 | 0.230 | -0.045 | -3.289 | 0.445 | 0 | 1 | 0.490 | 9637 |
| NATIVE | BAND_H | DIRECT | SHOCK | 25 | 231121 | 223986 | 42959 | 42948 | 0.9691 | 0.1859 | 0.482 | 0.048 | -5.205 | 2.070 | 1 | 1 | 0.508 | 9637 |
| NATIVE | BAND_H | DIRECT | SWING_GT_CUR | 25 | 231121 | 214496 | 40621 | 40617 | 0.9281 | 0.1758 | 0.646 | 0.071 | -14.121 | 8.689 | 0 | 0 | 0.779 | 9637 |
| NATIVE | BAND_H | DIRECT | SWING_SCALE | 25 | 231121 | 211724 | 40305 | 40298 | 0.9161 | 0.1744 | 0.419 | 0.044 | -20.249 | 2.393 | 1 | 0 | 0.782 | 9637 |
| NATIVE | BAND_H | DIRECT | TAIL_RISK | 25 | 231121 | 226841 | 43060 | 43051 | 0.9815 | 0.1863 | 0.283 | 0.010 | -2.923 | 0.608 | 0 | 1 | 0.584 | 9637 |
| NATIVE | BAND_H | REVERSE | LEVEL_FORECAST_K12 | 25 | 231121 | 135397 | 25549 | 25549 | 0.5858 | 0.1105 | 0.369 | -0.091 | -2.784 | 7.827 | 1 | 2 | 1.401 | 9637 |
| NATIVE | BAND_H | REVERSE | LEVEL_FORECAST_K4 | 25 | 231121 | 134892 | 25544 | 25539 | 0.5836 | 0.1105 | 0.258 | -0.043 | -8.500 | 8.077 | 1 | 2 | 1.436 | 9637 |
| NATIVE | BAND_H | REVERSE | LEVEL_NOW | 25 | 231121 | 225609 | 42756 | 42751 | 0.9762 | 0.1850 | 0.615 | 0.077 | -1.823 | 3.826 | 1 | 0 | 0.636 | 9637 |
| NATIVE | BAND_H | REVERSE | RANGE_SCALE | 25 | 231121 | 227423 | 43032 | 43024 | 0.9840 | 0.1862 | 0.295 | 0.052 | -5.293 | 1.504 | 0 | 0 | 0.436 | 9637 |
| NATIVE | BAND_H | REVERSE | SHOCK | 25 | 231121 | 229365 | 42941 | 42940 | 0.9924 | 0.1858 | 0.492 | 0.053 | -6.224 | 1.889 | 1 | 1 | 0.461 | 9637 |
| NATIVE | BAND_H | REVERSE | SWING_GT_CUR | 25 | 231121 | 214561 | 40653 | 40643 | 0.9283 | 0.1759 | 0.636 | 0.044 | -14.322 | 8.510 | 2 | 0 | 0.695 | 9637 |
| NATIVE | BAND_H | REVERSE | SWING_SCALE | 25 | 231121 | 213774 | 40288 | 40282 | 0.9249 | 0.1743 | 0.392 | -0.059 | -20.249 | 1.831 | 1 | 0 | 0.872 | 9637 |
| NATIVE | BAND_H | REVERSE | TAIL_RISK | 25 | 231121 | 227555 | 43030 | 43027 | 0.9846 | 0.1862 | 0.283 | 0.025 | -6.627 | 1.101 | 1 | 3 | 0.506 | 9637 |
| NATIVE | BAND_Z | DIRECT | LEVEL_FORECAST_K12 | 25 | 231121 | 136929 | 25277 | 25277 | 0.5925 | 0.1094 | 0.097 | -0.195 | -30.186 | 3.204 | 0 | 2 | 1.977 | 9637 |
| NATIVE | BAND_Z | DIRECT | LEVEL_FORECAST_K4 | 25 | 231121 | 137063 | 25456 | 25456 | 0.5930 | 0.1101 | 0.080 | -0.201 | -46.251 | 4.175 | 0 | 2 | 1.976 | 9637 |
| NATIVE | BAND_Z | DIRECT | LEVEL_NOW | 25 | 231121 | 228702 | 42494 | 42494 | 0.9895 | 0.1839 | 0.176 | -0.318 | -13.328 | 10.657 | 1 | 1 | 2.021 | 9637 |
| NATIVE | BAND_Z | DIRECT | RANGE_SCALE | 25 | 231121 | 230321 | 42403 | 42403 | 0.9965 | 0.1835 | 0.408 | 0.276 | -3.903 | 9.826 | 0 | 0 | 1.979 | 9637 |
| NATIVE | BAND_Z | DIRECT | SHOCK | 25 | 231121 | 228987 | 40919 | 40919 | 0.9908 | 0.1770 | 0.449 | -0.061 | -39.859 | 8.501 | 0 | 1 | 2.062 | 9637 |
| NATIVE | BAND_Z | DIRECT | SWING_GT_CUR | 25 | 231121 | 217326 | 40634 | 40634 | 0.9403 | 0.1758 | 0.209 | -0.429 | -9.263 | 8.517 | 0 | 1 | 2.014 | 9637 |
| NATIVE | BAND_Z | DIRECT | SWING_SCALE | 25 | 231121 | 215472 | 39529 | 39529 | 0.9323 | 0.1710 | 0.113 | -0.306 | -20.249 | 3.877 | 0 | 1 | 2.040 | 9637 |
| NATIVE | BAND_Z | DIRECT | TAIL_RISK | 25 | 231121 | 230026 | 42579 | 42579 | 0.9953 | 0.1842 | 0.171 | -0.282 | -7.769 | 14.111 | 0 | 1 | 2.155 | 9637 |
| NATIVE | BAND_Z | REVERSE | LEVEL_FORECAST_K12 | 25 | 231121 | 137137 | 25689 | 25689 | 0.5934 | 0.1111 | 0.172 | -0.499 | -12.668 | 8.492 | 0 | 2 | 2.156 | 9637 |
| NATIVE | BAND_Z | REVERSE | LEVEL_FORECAST_K4 | 25 | 231121 | 136847 | 25501 | 25501 | 0.5921 | 0.1103 | -0.112 | -0.618 | -5.769 | 3.226 | 0 | 0 | 2.126 | 9637 |
| NATIVE | BAND_Z | REVERSE | LEVEL_NOW | 25 | 231121 | 228477 | 42679 | 42679 | 0.9886 | 0.1847 | 0.252 | 0.157 | -21.422 | 6.685 | 0 | 0 | 2.301 | 9637 |
| NATIVE | BAND_Z | REVERSE | RANGE_SCALE | 25 | 231121 | 230070 | 43360 | 43360 | 0.9955 | 0.1876 | 0.302 | -0.202 | -34.872 | 3.537 | 0 | 1 | 2.094 | 9637 |
| NATIVE | BAND_Z | REVERSE | SHOCK | 25 | 231121 | 230091 | 44627 | 44627 | 0.9955 | 0.1931 | 0.609 | -0.197 | -9.358 | 3.100 | 0 | 0 | 2.085 | 9637 |
| NATIVE | BAND_Z | REVERSE | SWING_GT_CUR | 25 | 231121 | 217302 | 40280 | 40280 | 0.9402 | 0.1743 | 0.050 | -0.806 | -21.563 | 6.120 | 1 | 0 | 2.201 | 9637 |
| NATIVE | BAND_Z | REVERSE | SWING_SCALE | 25 | 231121 | 215869 | 40768 | 40768 | 0.9340 | 0.1764 | 0.297 | 0.071 | -20.249 | 1.389 | 0 | 1 | 1.916 | 9637 |
| NATIVE | BAND_Z | REVERSE | TAIL_RISK | 25 | 231121 | 230101 | 43160 | 43160 | 0.9956 | 0.1867 | 0.102 | -0.423 | -30.635 | 4.498 | 0 | 1 | 2.353 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | LEVEL_FORECAST_K12 | 25 | 231121 | 128818 | 25168 | 25168 | 0.5574 | 0.1089 | 0.036 | -0.335 | -30.186 | 3.235 | 0 | 2 | 1.949 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | LEVEL_FORECAST_K4 | 25 | 231121 | 130046 | 25388 | 25378 | 0.5627 | 0.1098 | -0.016 | -0.079 | -36.777 | 3.222 | 0 | 2 | 1.984 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | LEVEL_NOW | 25 | 231121 | 217413 | 42385 | 42375 | 0.9407 | 0.1834 | 0.297 | -0.439 | -13.658 | 11.300 | 0 | 1 | 2.185 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | RANGE_SCALE | 25 | 231121 | 219562 | 42307 | 42300 | 0.9500 | 0.1831 | 0.097 | 0.020 | -3.698 | 6.013 | 0 | 0 | 1.977 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | SHOCK | 25 | 231121 | 209353 | 40744 | 40731 | 0.9058 | 0.1763 | 0.417 | -0.238 | -36.755 | 7.322 | 0 | 1 | 2.045 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | SWING_GT_CUR | 25 | 231121 | 206762 | 40501 | 40496 | 0.8946 | 0.1752 | 0.098 | -0.350 | -9.594 | 9.175 | 0 | 0 | 1.971 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | SWING_SCALE | 25 | 231121 | 204343 | 39419 | 39414 | 0.8841 | 0.1706 | 0.131 | -0.149 | -20.249 | 3.560 | 0 | 1 | 1.986 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | TAIL_RISK | 25 | 231121 | 217570 | 42459 | 42450 | 0.9414 | 0.1837 | 0.069 | -0.233 | -8.597 | 14.620 | 0 | 1 | 2.081 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | LEVEL_FORECAST_K12 | 25 | 231121 | 137086 | 25247 | 25247 | 0.5931 | 0.1092 | 0.049 | -0.395 | -39.697 | 2.891 | 0 | 2 | 1.941 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | LEVEL_FORECAST_K4 | 25 | 231121 | 137005 | 25438 | 25436 | 0.5928 | 0.1101 | 0.079 | -0.176 | -36.155 | 4.213 | 0 | 2 | 1.968 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | LEVEL_NOW | 25 | 231121 | 228703 | 42475 | 42473 | 0.9895 | 0.1838 | 0.065 | -0.406 | -7.216 | 10.129 | 1 | 1 | 2.059 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | RANGE_SCALE | 25 | 231121 | 229650 | 42381 | 42376 | 0.9936 | 0.1834 | 0.057 | 0.259 | -3.675 | 8.314 | 0 | 1 | 1.909 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | SHOCK | 25 | 231121 | 229879 | 40889 | 40888 | 0.9946 | 0.1769 | 0.485 | -0.070 | -41.904 | 8.351 | 0 | 1 | 2.097 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | SWING_GT_CUR | 25 | 231121 | 217576 | 40641 | 40633 | 0.9414 | 0.1758 | 0.129 | -0.452 | -8.971 | 8.360 | 0 | 1 | 1.985 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | SWING_SCALE | 25 | 231121 | 215097 | 39505 | 39500 | 0.9307 | 0.1709 | 0.000 | -0.252 | -20.249 | 3.728 | 0 | 1 | 2.029 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | TAIL_RISK | 25 | 231121 | 230219 | 42552 | 42550 | 0.9961 | 0.1841 | 0.060 | -0.477 | -10.225 | 12.468 | 0 | 1 | 2.058 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | LEVEL_FORECAST_K12 | 25 | 231121 | 137059 | 25662 | 25662 | 0.5930 | 0.1110 | 0.133 | -0.550 | -12.668 | 8.219 | 1 | 2 | 2.119 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | LEVEL_FORECAST_K4 | 25 | 231121 | 137184 | 25508 | 25503 | 0.5936 | 0.1104 | -0.098 | -0.545 | -6.316 | 3.295 | 0 | 0 | 2.116 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | LEVEL_NOW | 25 | 231121 | 228881 | 42685 | 42680 | 0.9903 | 0.1847 | 0.350 | 0.015 | -19.525 | 7.264 | 0 | 0 | 2.340 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | RANGE_SCALE | 25 | 231121 | 229637 | 43364 | 43355 | 0.9936 | 0.1876 | 0.451 | -0.099 | -33.057 | 3.253 | 0 | 1 | 2.104 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | SHOCK | 25 | 231121 | 229604 | 44655 | 44643 | 0.9934 | 0.1932 | 0.456 | -0.385 | -17.381 | 2.805 | 0 | 0 | 2.123 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | SWING_GT_CUR | 25 | 231121 | 217450 | 40263 | 40258 | 0.9408 | 0.1742 | -0.056 | -0.760 | -22.111 | 7.802 | 1 | 0 | 2.179 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | SWING_SCALE | 25 | 231121 | 214789 | 40771 | 40766 | 0.9293 | 0.1764 | 0.329 | 0.045 | -20.249 | 1.454 | 0 | 2 | 1.906 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | TAIL_RISK | 25 | 231121 | 230314 | 43172 | 43167 | 0.9965 | 0.1868 | 0.069 | -0.368 | -30.342 | 4.752 | 0 | 1 | 2.300 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | LEVEL_FORECAST_K12 | 25 | 231121 | 130950 | 25613 | 25613 | 0.5666 | 0.1108 | 0.244 | -0.331 | -18.325 | 8.820 | 0 | 2 | 2.147 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | LEVEL_FORECAST_K4 | 25 | 231121 | 129764 | 25423 | 25418 | 0.5615 | 0.1100 | 0.005 | -0.469 | -9.582 | 2.936 | 0 | 1 | 2.133 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | LEVEL_NOW | 25 | 231121 | 217489 | 42576 | 42571 | 0.9410 | 0.1842 | 0.282 | -0.006 | -22.791 | 7.036 | 0 | 0 | 2.346 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | RANGE_SCALE | 25 | 231121 | 222474 | 43261 | 43253 | 0.9626 | 0.1872 | 0.410 | -0.174 | -42.519 | 3.129 | 0 | 1 | 2.010 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | SHOCK | 25 | 231121 | 227375 | 44594 | 44593 | 0.9838 | 0.1929 | 0.486 | -0.191 | -9.789 | 3.718 | 0 | 0 | 2.164 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | SWING_GT_CUR | 25 | 231121 | 206292 | 40174 | 40165 | 0.8926 | 0.1738 | -0.233 | -0.614 | -25.377 | 8.250 | 1 | 1 | 2.174 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | SWING_SCALE | 25 | 231121 | 210717 | 40696 | 40689 | 0.9117 | 0.1761 | 0.400 | 0.175 | -20.249 | 2.881 | 0 | 2 | 1.935 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | TAIL_RISK | 25 | 231121 | 220174 | 43058 | 43053 | 0.9526 | 0.1863 | 0.003 | -0.408 | -30.965 | 3.788 | 0 | 1 | 2.345 | 9637 |
**-- crypto / E_CLOSE / state=ALL : arm rollup over symbols --**

| arm_class | parameter | orientation | component | sym_rows | eligible_origin_n | observed_event_n | entry_fill_n | close_n | event_rate | fill_rate | exposure/origin med | est med | est min | est max | CI>0 | CI<0 | mde med | eff_origin_blocks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIXED_NATIVE | BAND_Z+BAND_H | FIXED | FIXED | 25 | 231121 | 227045 | 38212 | 38211 | 0.9824 | 0.1653 | 0.435 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 9637 |
| NATIVE | BAND_H | DIRECT | LEVEL_FORECAST_K12 | 25 | 231121 | 121757 | 22548 | 22548 | 0.5268 | 0.0976 | 0.083 | -0.430 | -1.859 | 5.537 | 0 | 1 | 1.387 | 9637 |
| NATIVE | BAND_H | DIRECT | LEVEL_FORECAST_K4 | 25 | 231121 | 123383 | 22591 | 22578 | 0.5338 | 0.0977 | 0.241 | -0.367 | -2.841 | 5.869 | 0 | 1 | 1.375 | 9637 |
| NATIVE | BAND_H | DIRECT | LEVEL_NOW | 25 | 231121 | 205563 | 37699 | 37686 | 0.8894 | 0.1631 | 0.877 | 0.070 | -1.639 | 3.603 | 1 | 0 | 0.691 | 9637 |
| NATIVE | BAND_H | DIRECT | RANGE_SCALE | 25 | 231121 | 203760 | 37943 | 37932 | 0.8816 | 0.1642 | 0.504 | 0.016 | -0.984 | 0.763 | 0 | 0 | 0.573 | 9637 |
| NATIVE | BAND_H | DIRECT | SHOCK | 25 | 231121 | 190457 | 37689 | 37669 | 0.8241 | 0.1631 | 0.691 | 0.056 | -0.962 | 3.604 | 1 | 0 | 0.695 | 9637 |
| NATIVE | BAND_H | DIRECT | SWING_GT_CUR | 25 | 231121 | 197161 | 35787 | 35779 | 0.8531 | 0.1548 | 0.696 | -0.037 | -3.202 | 6.548 | 0 | 0 | 0.825 | 9637 |
| NATIVE | BAND_H | DIRECT | SWING_SCALE | 25 | 231121 | 188031 | 35432 | 35421 | 0.8136 | 0.1533 | 0.401 | -0.035 | -5.816 | 17.452 | 0 | 0 | 0.729 | 9637 |
| NATIVE | BAND_H | DIRECT | TAIL_RISK | 25 | 231121 | 205040 | 37938 | 37923 | 0.8872 | 0.1641 | 0.890 | 0.032 | -0.965 | 1.148 | 0 | 0 | 0.673 | 9637 |
| NATIVE | BAND_H | REVERSE | LEVEL_FORECAST_K12 | 25 | 231121 | 125372 | 22569 | 22569 | 0.5425 | 0.0977 | 0.236 | -0.484 | -4.539 | 1.873 | 0 | 2 | 1.420 | 9637 |
| NATIVE | BAND_H | REVERSE | LEVEL_FORECAST_K4 | 25 | 231121 | 123770 | 22551 | 22540 | 0.5355 | 0.0976 | 0.074 | -0.491 | -3.660 | 2.433 | 0 | 3 | 1.407 | 9637 |
| NATIVE | BAND_H | REVERSE | LEVEL_NOW | 25 | 231121 | 207205 | 37666 | 37656 | 0.8965 | 0.1630 | 0.723 | 0.008 | -0.814 | 7.126 | 0 | 0 | 0.676 | 9637 |
| NATIVE | BAND_H | REVERSE | RANGE_SCALE | 25 | 231121 | 211728 | 37913 | 37903 | 0.9161 | 0.1640 | 0.735 | 0.043 | -0.772 | 9.174 | 0 | 0 | 0.708 | 9637 |
| NATIVE | BAND_H | REVERSE | SHOCK | 25 | 231121 | 224064 | 38002 | 37998 | 0.9695 | 0.1644 | 0.615 | 0.016 | -1.374 | 6.242 | 0 | 0 | 0.497 | 9637 |
| NATIVE | BAND_H | REVERSE | SWING_GT_CUR | 25 | 231121 | 194915 | 35802 | 35790 | 0.8433 | 0.1549 | 0.561 | -0.004 | -3.178 | 12.952 | 0 | 0 | 0.789 | 9637 |
| NATIVE | BAND_H | REVERSE | SWING_SCALE | 25 | 231121 | 200723 | 35547 | 35540 | 0.8685 | 0.1538 | 0.427 | 0.044 | -5.816 | 17.452 | 0 | 0 | 0.853 | 9637 |
| NATIVE | BAND_H | REVERSE | TAIL_RISK | 25 | 231121 | 210448 | 37926 | 37918 | 0.9106 | 0.1641 | 0.790 | 0.078 | -0.530 | 8.237 | 0 | 0 | 0.614 | 9637 |
| NATIVE | BAND_Z | DIRECT | LEVEL_FORECAST_K12 | 25 | 231121 | 133392 | 22653 | 22653 | 0.5772 | 0.0980 | 0.392 | -0.313 | -2.034 | 9.712 | 0 | 1 | 1.753 | 9637 |
| NATIVE | BAND_Z | DIRECT | LEVEL_FORECAST_K4 | 25 | 231121 | 133923 | 22781 | 22781 | 0.5794 | 0.0986 | 0.347 | -0.326 | -2.084 | 18.228 | 0 | 1 | 1.776 | 9637 |
| NATIVE | BAND_Z | DIRECT | LEVEL_NOW | 25 | 231121 | 223521 | 37961 | 37961 | 0.9671 | 0.1642 | 0.762 | 0.077 | -1.599 | 17.572 | 0 | 0 | 1.820 | 9637 |
| NATIVE | BAND_Z | DIRECT | RANGE_SCALE | 25 | 231121 | 225236 | 37556 | 37555 | 0.9745 | 0.1625 | 0.268 | -0.056 | -2.198 | 14.311 | 0 | 0 | 1.800 | 9637 |
| NATIVE | BAND_Z | DIRECT | SHOCK | 25 | 231121 | 220408 | 36259 | 36258 | 0.9536 | 0.1569 | 0.750 | 0.752 | -3.656 | 12.755 | 0 | 0 | 1.817 | 9637 |
| NATIVE | BAND_Z | DIRECT | SWING_GT_CUR | 25 | 231121 | 212282 | 36313 | 36313 | 0.9185 | 0.1571 | 0.692 | 0.017 | -3.652 | 19.408 | 0 | 0 | 1.786 | 9637 |
| NATIVE | BAND_Z | DIRECT | SWING_SCALE | 25 | 231121 | 209919 | 34895 | 34894 | 0.9083 | 0.1510 | 0.172 | -0.003 | -5.816 | 17.452 | 0 | 0 | 1.628 | 9637 |
| NATIVE | BAND_Z | DIRECT | TAIL_RISK | 25 | 231121 | 224426 | 37972 | 37971 | 0.9710 | 0.1643 | 0.647 | 0.179 | -3.938 | 21.955 | 0 | 0 | 1.823 | 9637 |
| NATIVE | BAND_Z | REVERSE | LEVEL_FORECAST_K12 | 25 | 231121 | 134206 | 22973 | 22972 | 0.5807 | 0.0994 | 0.279 | -0.386 | -3.152 | 23.241 | 1 | 0 | 1.718 | 9637 |
| NATIVE | BAND_Z | REVERSE | LEVEL_FORECAST_K4 | 25 | 231121 | 133520 | 22755 | 22754 | 0.5777 | 0.0985 | 0.299 | -0.592 | -4.564 | 14.882 | 0 | 0 | 1.754 | 9637 |
| NATIVE | BAND_Z | REVERSE | LEVEL_NOW | 25 | 231121 | 223156 | 38055 | 38054 | 0.9655 | 0.1647 | 0.958 | 0.241 | -2.687 | 6.890 | 1 | 0 | 1.721 | 9637 |
| NATIVE | BAND_Z | REVERSE | RANGE_SCALE | 25 | 231121 | 225667 | 38714 | 38714 | 0.9764 | 0.1675 | 0.767 | 0.052 | -4.187 | 11.974 | 1 | 0 | 1.547 | 9637 |
| NATIVE | BAND_Z | REVERSE | SHOCK | 25 | 231121 | 228144 | 40192 | 40192 | 0.9871 | 0.1739 | 0.604 | -0.011 | -2.007 | 7.237 | 0 | 0 | 1.822 | 9637 |
| NATIVE | BAND_Z | REVERSE | SWING_GT_CUR | 25 | 231121 | 212204 | 35788 | 35787 | 0.9182 | 0.1548 | 0.092 | -0.176 | -5.573 | 7.026 | 0 | 0 | 1.768 | 9637 |
| NATIVE | BAND_Z | REVERSE | SWING_SCALE | 25 | 231121 | 212703 | 36455 | 36455 | 0.9203 | 0.1577 | 0.690 | -0.028 | -5.816 | 17.452 | 0 | 0 | 1.550 | 9637 |
| NATIVE | BAND_Z | REVERSE | TAIL_RISK | 25 | 231121 | 225163 | 38525 | 38525 | 0.9742 | 0.1667 | 0.966 | 0.176 | -4.129 | 7.490 | 3 | 0 | 1.644 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | LEVEL_FORECAST_K12 | 25 | 231121 | 111350 | 22237 | 22237 | 0.4818 | 0.0962 | 0.472 | -0.261 | -1.958 | 10.486 | 0 | 1 | 1.731 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | LEVEL_FORECAST_K4 | 25 | 231121 | 113782 | 22437 | 22422 | 0.4923 | 0.0971 | 0.415 | -0.227 | -2.958 | 22.790 | 0 | 1 | 1.778 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | LEVEL_NOW | 25 | 231121 | 189320 | 37354 | 37339 | 0.8191 | 0.1616 | 0.799 | -0.015 | -2.533 | 21.178 | 0 | 0 | 1.828 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | RANGE_SCALE | 25 | 231121 | 188014 | 36905 | 36893 | 0.8135 | 0.1597 | 0.166 | 0.041 | -3.702 | 13.562 | 0 | 0 | 1.763 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | SHOCK | 25 | 231121 | 162867 | 35160 | 35139 | 0.7047 | 0.1521 | 0.822 | 0.512 | -5.282 | 19.241 | 0 | 0 | 1.874 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | SWING_GT_CUR | 25 | 231121 | 183798 | 35676 | 35667 | 0.7952 | 0.1544 | 0.547 | -0.218 | -3.935 | 20.487 | 1 | 0 | 1.803 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | SWING_SCALE | 25 | 231121 | 173590 | 34242 | 34230 | 0.7511 | 0.1482 | 0.190 | -0.108 | -5.816 | 17.452 | 0 | 0 | 1.728 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | TAIL_RISK | 25 | 231121 | 187494 | 37301 | 37285 | 0.8112 | 0.1614 | 0.713 | 0.134 | -9.540 | 20.196 | 0 | 0 | 1.955 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | LEVEL_FORECAST_K12 | 25 | 231121 | 132319 | 22551 | 22551 | 0.5725 | 0.0976 | 0.288 | -0.341 | -2.053 | 10.195 | 0 | 1 | 1.735 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | LEVEL_FORECAST_K4 | 25 | 231121 | 131744 | 22691 | 22684 | 0.5700 | 0.0982 | 0.227 | -0.308 | -1.842 | 17.245 | 0 | 1 | 1.819 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | LEVEL_NOW | 25 | 231121 | 220273 | 37817 | 37810 | 0.9531 | 0.1636 | 0.677 | 0.063 | -1.911 | 16.588 | 0 | 0 | 1.756 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | RANGE_SCALE | 25 | 231121 | 218974 | 37401 | 37392 | 0.9474 | 0.1618 | 0.372 | 0.033 | -1.540 | 14.285 | 0 | 0 | 1.792 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | SHOCK | 25 | 231121 | 226646 | 36113 | 36110 | 0.9806 | 0.1563 | 0.663 | 0.533 | -3.762 | 13.962 | 0 | 0 | 1.822 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | SWING_GT_CUR | 25 | 231121 | 208705 | 36267 | 36257 | 0.9030 | 0.1569 | 0.696 | -0.025 | -3.654 | 18.424 | 0 | 1 | 1.752 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | SWING_SCALE | 25 | 231121 | 205040 | 34785 | 34779 | 0.8872 | 0.1505 | 0.287 | -0.075 | -5.816 | 17.452 | 0 | 0 | 1.683 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | TAIL_RISK | 25 | 231121 | 222321 | 37841 | 37837 | 0.9619 | 0.1637 | 0.636 | 0.137 | -4.091 | 21.407 | 0 | 0 | 1.845 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | LEVEL_FORECAST_K12 | 25 | 231121 | 130968 | 22913 | 22913 | 0.5667 | 0.0991 | 0.263 | -0.424 | -3.111 | 23.241 | 1 | 0 | 1.703 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | LEVEL_FORECAST_K4 | 25 | 231121 | 131582 | 22747 | 22733 | 0.5693 | 0.0984 | 0.339 | -0.578 | -4.564 | 14.334 | 0 | 0 | 1.758 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | LEVEL_NOW | 25 | 231121 | 219493 | 38030 | 38016 | 0.9497 | 0.1645 | 1.025 | 0.295 | -2.523 | 6.009 | 2 | 0 | 1.789 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | RANGE_SCALE | 25 | 231121 | 216253 | 38639 | 38627 | 0.9357 | 0.1672 | 0.691 | -0.017 | -4.469 | 11.002 | 0 | 0 | 1.566 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | SHOCK | 25 | 231121 | 214970 | 40113 | 40094 | 0.9301 | 0.1736 | 0.652 | 0.065 | -1.798 | 7.363 | 0 | 0 | 1.807 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | SWING_GT_CUR | 25 | 231121 | 209164 | 35728 | 35720 | 0.9050 | 0.1546 | 0.156 | -0.158 | -5.532 | 6.479 | 0 | 0 | 1.725 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | SWING_SCALE | 25 | 231121 | 200081 | 36321 | 36308 | 0.8657 | 0.1572 | 0.573 | -0.069 | -5.816 | 17.452 | 0 | 0 | 1.515 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | TAIL_RISK | 25 | 231121 | 220320 | 38504 | 38487 | 0.9533 | 0.1666 | 0.944 | 0.271 | -4.315 | 7.769 | 3 | 0 | 1.724 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | LEVEL_FORECAST_K12 | 25 | 231121 | 116952 | 22712 | 22712 | 0.5060 | 0.0983 | 0.264 | -0.410 | -3.210 | 22.492 | 1 | 0 | 1.768 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | LEVEL_FORECAST_K4 | 25 | 231121 | 114528 | 22439 | 22429 | 0.4955 | 0.0971 | 0.418 | -0.546 | -4.144 | 14.133 | 0 | 0 | 1.785 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | LEVEL_NOW | 25 | 231121 | 192196 | 37545 | 37535 | 0.8316 | 0.1624 | 0.806 | 0.454 | -2.728 | 8.825 | 1 | 0 | 1.714 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | RANGE_SCALE | 25 | 231121 | 203330 | 38229 | 38218 | 0.8798 | 0.1654 | 0.782 | 0.087 | -4.179 | 12.723 | 1 | 0 | 1.562 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | SHOCK | 25 | 231121 | 220269 | 40106 | 40103 | 0.9530 | 0.1735 | 0.637 | -0.068 | -2.441 | 7.276 | 0 | 0 | 1.839 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | SWING_GT_CUR | 25 | 231121 | 178510 | 35179 | 35165 | 0.7724 | 0.1522 | 0.454 | -0.037 | -4.649 | 8.805 | 0 | 0 | 1.758 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | SWING_SCALE | 25 | 231121 | 195204 | 36103 | 36095 | 0.8446 | 0.1562 | 0.356 | 0.208 | -5.816 | 17.452 | 0 | 0 | 1.510 | 9637 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | TAIL_RISK | 25 | 231121 | 196556 | 38046 | 38037 | 0.8504 | 0.1646 | 1.093 | 0.312 | -3.097 | 7.923 | 3 | 0 | 1.696 | 9637 |
**-- crypto : non-ALL state populations (retained, not pruned) --**

```text
                               rows  eligible_origin_n  observed_event_n  entry_fill_n  close_n   est_med   mde_med
entry_variant state
E_CLOSE       CENSORED           27             177462                27             0        0  0.000000  0.000000
              INCOMPLETE       1477           13895002                 0             0        0  0.000000  0.000000
              NO_EVENT         1586           14986813                 0             0        0 -0.065523  0.278688
              NO_FEATURE       1625           15022865                 0             0        0  0.000000  0.380725
              ORDER_CREATED    1593           14991585          12174878       2183794  2183324  0.135129  1.303950
E_TOUCH       EVENT_UNDECIDED  1430           14504951             73689             0        0  0.000000  0.012532
              INCOMPLETE       1477           13895002                 0             0        0  0.000000  0.000000
              NO_EVENT         1493           14825415                 0             0        0 -0.003897  0.062293
              NO_FEATURE       1625           15022865                 0             0        0  0.000000  0.336565
              ORDER_CREATED    1593           14991585          12965180       2465108  2464846 -0.054582  1.595825
```


## A2 — native trade lens (`COMMON_CLOSE_TRADE`)

**universe=ctrader shared_trade_rows=377333**

```text
real _entry_ns non-null: 377333 | real _exit_ns non-null: 377333 | fixed_entry_ns non-null: 377333 | fixed_exit_ns non-null: 377333
```

**-- ctrader / E_TOUCH : paired adaptive-minus-fixed on common closes --**

| arm_class | parameter | orientation | component | common_close_n | mean delta bps | median | ci_low | ci_high | ci_low_seed_range | mde | eff_trade_blocks |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NATIVE | BAND_H | DIRECT | LEVEL_FORECAST_K12 | 3838 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 159 |
| NATIVE | BAND_H | DIRECT | LEVEL_FORECAST_K4 | 3796 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 158 |
| NATIVE | BAND_H | DIRECT | LEVEL_NOW | 6425 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 267 |
| NATIVE | BAND_H | DIRECT | RANGE_SCALE | 6449 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 268 |
| NATIVE | BAND_H | DIRECT | SHOCK | 6326 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 263 |
| NATIVE | BAND_H | DIRECT | SWING_GT_CUR | 6226 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 259 |
| NATIVE | BAND_H | DIRECT | SWING_SCALE | 6236 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 259 |
| NATIVE | BAND_H | DIRECT | TAIL_RISK | 6473 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 269 |
| NATIVE | BAND_H | REVERSE | LEVEL_FORECAST_K12 | 3794 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 158 |
| NATIVE | BAND_H | REVERSE | LEVEL_FORECAST_K4 | 3787 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 157 |
| NATIVE | BAND_H | REVERSE | LEVEL_NOW | 6368 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 265 |
| NATIVE | BAND_H | REVERSE | RANGE_SCALE | 6357 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 264 |
| NATIVE | BAND_H | REVERSE | SHOCK | 6381 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 265 |
| NATIVE | BAND_H | REVERSE | SWING_GT_CUR | 6220 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 259 |
| NATIVE | BAND_H | REVERSE | SWING_SCALE | 6185 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 257 |
| NATIVE | BAND_H | REVERSE | TAIL_RISK | 6366 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 265 |
| NATIVE | BAND_Z | DIRECT | LEVEL_FORECAST_K12 | 1609 | -0.926 | 0.000 | -2.335 | 0.441 | [-2.381, -2.227] | 9.992 | 67 |
| NATIVE | BAND_Z | DIRECT | LEVEL_FORECAST_K4 | 1637 | 0.195 | 0.000 | -1.171 | 1.522 | [-1.184, -1.099] | 9.046 | 68 |
| NATIVE | BAND_Z | DIRECT | LEVEL_NOW | 2814 | 0.408 | 0.000 | -0.562 | 1.413 | [-0.580, -0.550] | 6.948 | 117 |
| NATIVE | BAND_Z | DIRECT | RANGE_SCALE | 3587 | -0.044 | 0.000 | -0.594 | 0.517 | [-0.629, -0.577] | 3.872 | 149 |
| NATIVE | BAND_Z | DIRECT | SHOCK | 2726 | 0.194 | 0.000 | -0.786 | 1.144 | [-0.790, -0.746] | 7.021 | 113 |
| NATIVE | BAND_Z | DIRECT | SWING_GT_CUR | 2735 | 0.291 | 0.000 | -0.661 | 1.262 | [-0.668, -0.647] | 6.405 | 113 |
| NATIVE | BAND_Z | DIRECT | SWING_SCALE | 3769 | -0.464 | 0.000 | -1.004 | 0.064 | [-1.052, -0.996] | 4.100 | 157 |
| NATIVE | BAND_Z | DIRECT | TAIL_RISK | 2912 | -0.037 | 0.000 | -0.736 | 0.645 | [-0.769, -0.690] | 5.131 | 121 |
| NATIVE | BAND_Z | REVERSE | LEVEL_FORECAST_K12 | 1647 | 0.257 | 0.000 | -0.752 | 1.332 | [-0.764, -0.726] | 7.669 | 68 |
| NATIVE | BAND_Z | REVERSE | LEVEL_FORECAST_K4 | 1655 | 0.850 | 0.000 | -0.112 | 1.984 | [-0.145, -0.083] | 8.455 | 68 |
| NATIVE | BAND_Z | REVERSE | LEVEL_NOW | 2800 | 0.529 | 0.000 | -0.300 | 1.427 | [-0.315, -0.289] | 5.887 | 116 |
| NATIVE | BAND_Z | REVERSE | RANGE_SCALE | 3345 | 0.277 | 0.000 | -0.405 | 0.945 | [-0.466, -0.383] | 4.525 | 139 |
| NATIVE | BAND_Z | REVERSE | SHOCK | 2926 | 0.357 | 0.000 | -0.429 | 1.165 | [-0.455, -0.416] | 5.537 | 121 |
| NATIVE | BAND_Z | REVERSE | SWING_GT_CUR | 2809 | -0.490 | 0.000 | -1.255 | 0.286 | [-1.275, -1.212] | 6.012 | 117 |
| NATIVE | BAND_Z | REVERSE | SWING_SCALE | 3526 | 0.465 | 0.000 | -0.017 | 0.935 | [-0.028, 0.002] | 3.401 | 146 |
| NATIVE | BAND_Z | REVERSE | TAIL_RISK | 2710 | 0.296 | 0.000 | -0.516 | 1.124 | [-0.530, -0.488] | 5.573 | 112 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | LEVEL_FORECAST_K12 | 1569 | -0.473 | 0.000 | -1.668 | 0.724 | [-1.680, -1.624] | 8.463 | 65 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | LEVEL_FORECAST_K4 | 1615 | 0.502 | 0.000 | -0.640 | 1.678 | [-0.682, -0.605] | 8.059 | 67 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | LEVEL_NOW | 2764 | 0.536 | 0.000 | -0.337 | 1.407 | [-0.344, -0.313] | 5.832 | 115 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | RANGE_SCALE | 3576 | -0.219 | 0.000 | -0.761 | 0.327 | [-0.775, -0.748] | 3.956 | 149 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | SHOCK | 2690 | -0.390 | 0.000 | -1.115 | 0.351 | [-1.148, -1.100] | 5.360 | 112 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | SWING_GT_CUR | 2639 | 0.422 | 0.000 | -0.506 | 1.311 | [-0.551, -0.491] | 5.968 | 109 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | SWING_SCALE | 3709 | -0.522 | 0.000 | -1.082 | 0.027 | [-1.087, -1.055] | 4.247 | 154 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | TAIL_RISK | 2867 | 0.015 | 0.000 | -0.763 | 0.785 | [-0.788, -0.723] | 5.363 | 119 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | LEVEL_FORECAST_K12 | 1630 | -0.708 | 0.000 | -2.212 | 0.793 | [-2.260, -2.113] | 10.444 | 67 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | LEVEL_FORECAST_K4 | 1629 | 0.099 | 0.000 | -1.420 | 1.578 | [-1.534, -1.333] | 9.976 | 67 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | LEVEL_NOW | 2772 | 0.359 | 0.000 | -0.594 | 1.271 | [-0.608, -0.560] | 6.636 | 115 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | RANGE_SCALE | 3559 | -0.192 | 0.000 | -0.782 | 0.371 | [-0.811, -0.770] | 3.937 | 148 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | SHOCK | 2707 | -0.380 | 0.000 | -1.239 | 0.502 | [-1.289, -1.230] | 6.026 | 112 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | SWING_GT_CUR | 2713 | 1.292 | 0.000 | 0.371 | 2.219 | [0.359, 0.421] | 6.238 | 113 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | SWING_SCALE | 3741 | -0.648 | 0.000 | -1.198 | -0.131 | [-1.218, -1.187] | 4.022 | 155 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | TAIL_RISK | 2876 | 0.338 | 0.000 | -0.441 | 1.111 | [-0.487, -0.410] | 5.426 | 119 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | LEVEL_FORECAST_K12 | 1629 | 0.844 | 0.000 | -0.080 | 1.905 | [-0.114, -0.049] | 7.156 | 67 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | LEVEL_FORECAST_K4 | 1685 | 0.511 | 0.000 | -0.621 | 1.718 | [-0.663, -0.569] | 8.838 | 70 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | LEVEL_NOW | 2765 | 0.366 | 0.000 | -0.435 | 1.250 | [-0.448, -0.402] | 5.947 | 115 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | RANGE_SCALE | 3333 | 0.173 | 0.000 | -0.545 | 0.855 | [-0.565, -0.492] | 4.108 | 138 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | SHOCK | 2909 | 0.596 | 0.000 | -0.228 | 1.461 | [-0.259, -0.212] | 5.768 | 121 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | SWING_GT_CUR | 2790 | -0.168 | 0.000 | -0.968 | 0.683 | [-1.010, -0.929] | 6.062 | 116 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | SWING_SCALE | 3514 | 0.500 | 0.000 | -0.116 | 1.079 | [-0.121, -0.092] | 4.229 | 146 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | TAIL_RISK | 2697 | -0.046 | 0.000 | -0.854 | 0.812 | [-0.895, -0.823] | 5.449 | 112 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | LEVEL_FORECAST_K12 | 1623 | 0.709 | 0.000 | -0.265 | 1.755 | [-0.295, -0.221] | 7.855 | 67 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | LEVEL_FORECAST_K4 | 1597 | 0.737 | 0.000 | -0.447 | 2.144 | [-0.487, -0.404] | 8.854 | 66 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | LEVEL_NOW | 2711 | 0.668 | 0.000 | -0.122 | 1.580 | [-0.132, -0.120] | 6.032 | 112 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | RANGE_SCALE | 3219 | -0.126 | 0.000 | -0.741 | 0.464 | [-0.767, -0.712] | 3.981 | 134 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | SHOCK | 2913 | 0.578 | 0.000 | -0.292 | 1.471 | [-0.297, -0.261] | 5.882 | 121 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | SWING_GT_CUR | 2737 | -0.058 | 0.000 | -0.942 | 0.902 | [-0.998, -0.898] | 6.489 | 114 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | SWING_SCALE | 3476 | 0.181 | 0.000 | -0.282 | 0.642 | [-0.286, -0.272] | 3.509 | 144 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | TAIL_RISK | 2660 | 0.355 | 0.000 | -0.326 | 1.047 | [-0.334, -0.305] | 5.302 | 110 |
**-- ctrader / E_CLOSE : paired adaptive-minus-fixed on common closes --**

| arm_class | parameter | orientation | component | common_close_n | mean delta bps | median | ci_low | ci_high | ci_low_seed_range | mde | eff_trade_blocks |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NATIVE | BAND_H | DIRECT | LEVEL_FORECAST_K12 | 2548 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 106 |
| NATIVE | BAND_H | DIRECT | LEVEL_FORECAST_K4 | 2603 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 108 |
| NATIVE | BAND_H | DIRECT | LEVEL_NOW | 4310 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 179 |
| NATIVE | BAND_H | DIRECT | RANGE_SCALE | 4483 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 186 |
| NATIVE | BAND_H | DIRECT | SHOCK | 4125 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 171 |
| NATIVE | BAND_H | DIRECT | SWING_GT_CUR | 4080 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 170 |
| NATIVE | BAND_H | DIRECT | SWING_SCALE | 4350 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 181 |
| NATIVE | BAND_H | DIRECT | TAIL_RISK | 4423 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 184 |
| NATIVE | BAND_H | REVERSE | LEVEL_FORECAST_K12 | 2582 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 107 |
| NATIVE | BAND_H | REVERSE | LEVEL_FORECAST_K4 | 2500 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 104 |
| NATIVE | BAND_H | REVERSE | LEVEL_NOW | 4261 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 177 |
| NATIVE | BAND_H | REVERSE | RANGE_SCALE | 4011 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 167 |
| NATIVE | BAND_H | REVERSE | SHOCK | 4429 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 184 |
| NATIVE | BAND_H | REVERSE | SWING_GT_CUR | 4236 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 176 |
| NATIVE | BAND_H | REVERSE | SWING_SCALE | 3939 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 164 |
| NATIVE | BAND_H | REVERSE | TAIL_RISK | 4086 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 170 |
| NATIVE | BAND_Z | DIRECT | LEVEL_FORECAST_K12 | 1297 | 0.944 | 0.000 | -0.196 | 2.131 | [-0.280, -0.144] | 8.221 | 54 |
| NATIVE | BAND_Z | DIRECT | LEVEL_FORECAST_K4 | 1306 | 0.994 | 0.000 | -0.185 | 2.245 | [-0.242, -0.151] | 8.237 | 54 |
| NATIVE | BAND_Z | DIRECT | LEVEL_NOW | 2174 | -0.066 | 0.000 | -0.946 | 0.815 | [-0.969, -0.878] | 6.239 | 90 |
| NATIVE | BAND_Z | DIRECT | RANGE_SCALE | 2705 | -0.154 | 0.000 | -0.746 | 0.446 | [-0.757, -0.722] | 4.431 | 112 |
| NATIVE | BAND_Z | DIRECT | SHOCK | 2217 | 0.208 | 0.000 | -0.755 | 1.119 | [-0.790, -0.743] | 6.250 | 92 |
| NATIVE | BAND_Z | DIRECT | SWING_GT_CUR | 2161 | 0.735 | 0.000 | -0.144 | 1.599 | [-0.168, -0.101] | 5.963 | 90 |
| NATIVE | BAND_Z | DIRECT | SWING_SCALE | 2770 | 0.047 | 0.000 | -0.647 | 0.755 | [-0.660, -0.629] | 4.968 | 115 |
| NATIVE | BAND_Z | DIRECT | TAIL_RISK | 2190 | -0.436 | 0.000 | -1.276 | 0.444 | [-1.301, -1.263] | 6.262 | 91 |
| NATIVE | BAND_Z | REVERSE | LEVEL_FORECAST_K12 | 1255 | -0.552 | 0.000 | -1.835 | 0.832 | [-1.954, -1.814] | 8.122 | 52 |
| NATIVE | BAND_Z | REVERSE | LEVEL_FORECAST_K4 | 1233 | 0.617 | 0.000 | -0.700 | 1.966 | [-0.727, -0.672] | 9.184 | 51 |
| NATIVE | BAND_Z | REVERSE | LEVEL_NOW | 2152 | 0.872 | 0.000 | -0.260 | 1.966 | [-0.334, -0.224] | 6.860 | 89 |
| NATIVE | BAND_Z | REVERSE | RANGE_SCALE | 2574 | 0.977 | 0.000 | 0.251 | 1.770 | [0.234, 0.282] | 4.875 | 107 |
| NATIVE | BAND_Z | REVERSE | SHOCK | 2126 | -0.034 | 0.000 | -1.118 | 1.083 | [-1.166, -1.042] | 7.579 | 88 |
| NATIVE | BAND_Z | REVERSE | SWING_GT_CUR | 2104 | 0.144 | 0.000 | -0.839 | 1.108 | [-0.861, -0.773] | 6.704 | 87 |
| NATIVE | BAND_Z | REVERSE | SWING_SCALE | 2683 | 0.357 | 0.000 | -0.264 | 0.984 | [-0.273, -0.230] | 4.493 | 111 |
| NATIVE | BAND_Z | REVERSE | TAIL_RISK | 2135 | 1.451 | 0.000 | 0.496 | 2.439 | [0.476, 0.536] | 6.713 | 88 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | LEVEL_FORECAST_K12 | 1218 | 0.533 | 0.000 | -0.663 | 1.759 | [-0.702, -0.595] | 8.280 | 50 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | LEVEL_FORECAST_K4 | 1203 | 0.816 | 0.000 | -0.508 | 2.192 | [-0.539, -0.422] | 9.020 | 50 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | LEVEL_NOW | 2053 | -0.045 | 0.000 | -0.843 | 0.761 | [-0.908, -0.830] | 6.090 | 85 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | RANGE_SCALE | 2632 | -0.355 | 0.000 | -0.982 | 0.285 | [-1.007, -0.954] | 4.574 | 109 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | SHOCK | 1975 | 0.069 | 0.000 | -0.653 | 0.775 | [-0.675, -0.627] | 5.609 | 82 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | SWING_GT_CUR | 2008 | 0.333 | 0.000 | -0.558 | 1.259 | [-0.585, -0.540] | 6.244 | 83 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | SWING_SCALE | 2698 | -0.457 | 0.000 | -1.033 | 0.118 | [-1.052, -0.998] | 4.281 | 112 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | TAIL_RISK | 2137 | -0.343 | 0.000 | -1.104 | 0.466 | [-1.144, -1.093] | 6.091 | 89 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | LEVEL_FORECAST_K12 | 1335 | 0.446 | 0.000 | -0.748 | 1.616 | [-0.765, -0.683] | 8.233 | 55 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | LEVEL_FORECAST_K4 | 1276 | 0.969 | 0.000 | -0.240 | 2.166 | [-0.274, -0.219] | 9.111 | 53 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | LEVEL_NOW | 2167 | -0.006 | 0.000 | -0.907 | 0.936 | [-0.970, -0.864] | 6.769 | 90 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | RANGE_SCALE | 2649 | -0.241 | 0.000 | -0.961 | 0.494 | [-0.978, -0.950] | 4.781 | 110 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | SHOCK | 2180 | 0.354 | 0.000 | -0.576 | 1.271 | [-0.591, -0.555] | 6.404 | 90 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | SWING_GT_CUR | 2080 | 1.414 | 0.000 | 0.467 | 2.399 | [0.459, 0.533] | 6.524 | 86 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | SWING_SCALE | 2687 | -0.224 | 0.000 | -0.805 | 0.388 | [-0.811, -0.800] | 4.259 | 111 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | TAIL_RISK | 2233 | 0.127 | 0.000 | -0.741 | 1.063 | [-0.761, -0.705] | 6.272 | 93 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | LEVEL_FORECAST_K12 | 1248 | -0.234 | 0.000 | -1.528 | 1.150 | [-1.582, -1.427] | 10.101 | 52 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | LEVEL_FORECAST_K4 | 1257 | 0.525 | 0.000 | -0.578 | 1.649 | [-0.598, -0.551] | 7.783 | 52 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | LEVEL_NOW | 2067 | 0.590 | 0.000 | -0.405 | 1.608 | [-0.415, -0.356] | 6.856 | 86 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | RANGE_SCALE | 2506 | 0.378 | 0.000 | -0.351 | 1.091 | [-0.365, -0.319] | 4.733 | 104 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | SHOCK | 2122 | -0.014 | 0.000 | -1.006 | 1.024 | [-1.051, -0.993] | 6.735 | 88 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | SWING_GT_CUR | 2101 | 0.368 | 0.000 | -0.556 | 1.297 | [-0.583, -0.544] | 6.284 | 87 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | SWING_SCALE | 2611 | 1.193 | 0.000 | 0.528 | 1.893 | [0.500, 0.535] | 4.656 | 108 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | TAIL_RISK | 2089 | 0.915 | 0.000 | -0.009 | 1.814 | [-0.052, 0.042] | 6.747 | 87 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | LEVEL_FORECAST_K12 | 1182 | -0.583 | 0.000 | -1.809 | 0.709 | [-1.840, -1.772] | 8.185 | 49 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | LEVEL_FORECAST_K4 | 1146 | -0.208 | 0.000 | -1.290 | 0.859 | [-1.306, -1.247] | 7.942 | 47 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | LEVEL_NOW | 1979 | 0.024 | 0.000 | -0.986 | 1.039 | [-1.031, -0.931] | 6.535 | 82 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | RANGE_SCALE | 2366 | 0.441 | 0.000 | -0.207 | 1.146 | [-0.221, -0.196] | 4.648 | 98 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | SHOCK | 2063 | 0.282 | 0.000 | -0.838 | 1.488 | [-0.901, -0.822] | 7.250 | 85 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | SWING_GT_CUR | 1981 | -0.118 | 0.000 | -1.133 | 0.886 | [-1.162, -1.112] | 6.855 | 82 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | SWING_SCALE | 2399 | 0.514 | 0.000 | -0.103 | 1.156 | [-0.139, -0.091] | 4.544 | 99 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | TAIL_RISK | 1889 | 0.465 | 0.000 | -0.373 | 1.313 | [-0.401, -0.353] | 6.130 | 78 |
**universe=crypto shared_trade_rows=1742747**

```text
real _entry_ns non-null: 1742747 | real _exit_ns non-null: 1742747 | fixed_entry_ns non-null: 1742747 | fixed_exit_ns non-null: 1742747
```

**-- crypto / E_TOUCH : paired adaptive-minus-fixed on common closes --**

| arm_class | parameter | orientation | component | common_close_n | mean delta bps | median | ci_low | ci_high | ci_low_seed_range | mde | eff_trade_blocks |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NATIVE | BAND_H | DIRECT | LEVEL_FORECAST_K12 | 19410 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 808 |
| NATIVE | BAND_H | DIRECT | LEVEL_FORECAST_K4 | 19478 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 811 |
| NATIVE | BAND_H | DIRECT | LEVEL_NOW | 32615 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 1358 |
| NATIVE | BAND_H | DIRECT | RANGE_SCALE | 33162 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 1381 |
| NATIVE | BAND_H | DIRECT | SHOCK | 32652 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 1360 |
| NATIVE | BAND_H | DIRECT | SWING_GT_CUR | 31063 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 1294 |
| NATIVE | BAND_H | DIRECT | SWING_SCALE | 30728 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 1280 |
| NATIVE | BAND_H | DIRECT | TAIL_RISK | 33145 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 1381 |
| NATIVE | BAND_H | REVERSE | LEVEL_FORECAST_K12 | 19503 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 812 |
| NATIVE | BAND_H | REVERSE | LEVEL_FORECAST_K4 | 19496 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 812 |
| NATIVE | BAND_H | REVERSE | LEVEL_NOW | 32604 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 1358 |
| NATIVE | BAND_H | REVERSE | RANGE_SCALE | 33039 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 1376 |
| NATIVE | BAND_H | REVERSE | SHOCK | 33077 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 1378 |
| NATIVE | BAND_H | REVERSE | SWING_GT_CUR | 30923 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 1288 |
| NATIVE | BAND_H | REVERSE | SWING_SCALE | 30815 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 1283 |
| NATIVE | BAND_H | REVERSE | TAIL_RISK | 33150 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 1381 |
| NATIVE | BAND_Z | DIRECT | LEVEL_FORECAST_K12 | 6902 | 2.288 | 0.000 | -0.191 | 4.773 | [-0.289, -0.150] | 17.358 | 287 |
| NATIVE | BAND_Z | DIRECT | LEVEL_FORECAST_K4 | 6978 | -1.198 | 0.000 | -3.960 | 1.361 | [-4.032, -3.718] | 19.071 | 290 |
| NATIVE | BAND_Z | DIRECT | LEVEL_NOW | 11495 | -0.682 | 0.000 | -2.734 | 1.394 | [-2.861, -2.682] | 14.813 | 478 |
| NATIVE | BAND_Z | DIRECT | RANGE_SCALE | 14032 | -1.163 | 0.000 | -3.241 | 0.795 | [-3.363, -3.193] | 12.729 | 584 |
| NATIVE | BAND_Z | DIRECT | SHOCK | 11466 | 0.123 | 0.000 | -2.727 | 2.809 | [-2.867, -2.607] | 18.105 | 477 |
| NATIVE | BAND_Z | DIRECT | SWING_GT_CUR | 11191 | 0.324 | 0.000 | -1.999 | 2.632 | [-2.097, -1.929] | 15.460 | 466 |
| NATIVE | BAND_Z | DIRECT | SWING_SCALE | 14247 | 0.967 | 0.000 | -0.480 | 2.426 | [-0.509, -0.411] | 9.671 | 593 |
| NATIVE | BAND_Z | DIRECT | TAIL_RISK | 11741 | -0.324 | 0.000 | -2.387 | 1.744 | [-2.535, -2.267] | 14.811 | 489 |
| NATIVE | BAND_Z | REVERSE | LEVEL_FORECAST_K12 | 6946 | 0.000 | 0.000 | -2.408 | 2.376 | [-2.470, -2.308] | 16.994 | 289 |
| NATIVE | BAND_Z | REVERSE | LEVEL_FORECAST_K4 | 6864 | 0.525 | 0.000 | -3.142 | 3.757 | [-3.312, -3.002] | 22.119 | 286 |
| NATIVE | BAND_Z | REVERSE | LEVEL_NOW | 11639 | 2.376 | 0.000 | 0.023 | 4.746 | [-0.026, 0.139] | 16.561 | 484 |
| NATIVE | BAND_Z | REVERSE | RANGE_SCALE | 14247 | 1.318 | 0.000 | -0.296 | 2.946 | [-0.339, -0.253] | 11.332 | 593 |
| NATIVE | BAND_Z | REVERSE | SHOCK | 11558 | 1.469 | 0.000 | -0.758 | 3.711 | [-0.778, -0.651] | 15.202 | 481 |
| NATIVE | BAND_Z | REVERSE | SWING_GT_CUR | 10831 | -0.113 | 0.000 | -2.753 | 2.253 | [-2.822, -2.657] | 17.388 | 451 |
| NATIVE | BAND_Z | REVERSE | SWING_SCALE | 14359 | 1.881 | 0.000 | 0.390 | 3.390 | [0.381, 0.425] | 10.327 | 598 |
| NATIVE | BAND_Z | REVERSE | TAIL_RISK | 11617 | 1.679 | 0.000 | -0.943 | 4.225 | [-1.101, -0.806] | 17.055 | 484 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | LEVEL_FORECAST_K12 | 6802 | 0.927 | 0.000 | -1.555 | 3.497 | [-1.663, -1.491] | 17.469 | 283 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | LEVEL_FORECAST_K4 | 6910 | -1.108 | 0.000 | -3.833 | 1.439 | [-3.934, -3.730] | 18.533 | 287 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | LEVEL_NOW | 11427 | -0.937 | 0.000 | -2.989 | 1.133 | [-3.042, -2.887] | 14.499 | 476 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | RANGE_SCALE | 13968 | -1.012 | 0.000 | -2.965 | 0.834 | [-2.991, -2.947] | 12.923 | 582 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | SHOCK | 11306 | 0.595 | 0.000 | -2.023 | 2.969 | [-2.132, -1.840] | 16.802 | 471 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | SWING_GT_CUR | 11116 | 0.730 | 0.000 | -1.316 | 2.825 | [-1.398, -1.228] | 14.043 | 463 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | SWING_SCALE | 14281 | 0.585 | 0.000 | -0.878 | 2.065 | [-0.893, -0.831] | 9.906 | 595 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | TAIL_RISK | 11653 | -0.622 | 0.000 | -2.807 | 1.571 | [-3.040, -2.761] | 15.446 | 485 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | LEVEL_FORECAST_K12 | 6862 | 1.928 | 0.000 | -0.597 | 4.456 | [-0.617, -0.426] | 18.240 | 285 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | LEVEL_FORECAST_K4 | 6945 | 1.269 | 0.000 | -1.297 | 3.726 | [-1.336, -1.110] | 18.545 | 289 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | LEVEL_NOW | 11508 | -0.701 | 0.000 | -2.925 | 1.510 | [-2.994, -2.860] | 14.909 | 479 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | RANGE_SCALE | 13895 | -0.261 | 0.000 | -2.195 | 1.517 | [-2.302, -2.123] | 12.819 | 578 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | SHOCK | 11387 | 1.238 | 0.000 | -1.183 | 3.619 | [-1.324, -1.155] | 17.043 | 474 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | SWING_GT_CUR | 11317 | 0.067 | 0.000 | -2.009 | 2.122 | [-2.056, -1.875] | 14.707 | 471 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | SWING_SCALE | 14328 | 0.881 | 0.000 | -0.610 | 2.337 | [-0.653, -0.565] | 9.612 | 597 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | TAIL_RISK | 11744 | -0.117 | 0.000 | -2.404 | 2.067 | [-2.501, -2.282] | 15.091 | 489 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | LEVEL_FORECAST_K12 | 6895 | -0.105 | 0.000 | -2.816 | 2.701 | [-2.897, -2.735] | 18.366 | 287 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | LEVEL_FORECAST_K4 | 6870 | 1.045 | 0.000 | -2.620 | 4.315 | [-2.891, -2.498] | 22.686 | 286 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | LEVEL_NOW | 11645 | 0.829 | 0.000 | -1.317 | 2.876 | [-1.469, -1.272] | 15.109 | 485 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | RANGE_SCALE | 14250 | 1.887 | 0.000 | 0.243 | 3.501 | [0.186, 0.356] | 11.185 | 593 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | SHOCK | 11633 | 0.306 | 0.000 | -1.791 | 2.356 | [-1.840, -1.692] | 14.227 | 484 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | SWING_GT_CUR | 10773 | -0.172 | 0.000 | -2.762 | 2.246 | [-2.915, -2.673] | 17.266 | 448 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | SWING_SCALE | 14337 | 2.336 | 0.000 | 0.942 | 3.837 | [0.910, 1.016] | 9.679 | 597 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | TAIL_RISK | 11676 | 0.284 | 0.000 | -2.203 | 2.748 | [-2.326, -2.176] | 17.489 | 486 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | LEVEL_FORECAST_K12 | 6848 | 1.667 | 0.000 | -0.837 | 4.208 | [-0.964, -0.773] | 17.435 | 285 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | LEVEL_FORECAST_K4 | 6834 | 0.902 | 0.000 | -2.483 | 3.905 | [-2.614, -2.384] | 21.931 | 284 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | LEVEL_NOW | 11539 | 0.870 | 0.000 | -1.303 | 3.011 | [-1.364, -1.234] | 15.008 | 480 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | RANGE_SCALE | 14133 | 1.020 | 0.000 | -0.695 | 2.723 | [-0.854, -0.558] | 11.187 | 588 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | SHOCK | 11538 | 0.660 | 0.000 | -1.381 | 2.810 | [-1.455, -1.300] | 15.140 | 480 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | SWING_GT_CUR | 10655 | -0.906 | 0.000 | -3.467 | 1.437 | [-3.601, -3.304] | 17.185 | 443 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | SWING_SCALE | 14228 | 1.774 | 0.000 | 0.348 | 3.271 | [0.326, 0.387] | 9.494 | 592 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | TAIL_RISK | 11635 | 0.566 | 0.000 | -2.066 | 3.091 | [-2.159, -1.947] | 17.376 | 484 |
**-- crypto / E_CLOSE : paired adaptive-minus-fixed on common closes --**

| arm_class | parameter | orientation | component | common_close_n | mean delta bps | median | ci_low | ci_high | ci_low_seed_range | mde | eff_trade_blocks |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NATIVE | BAND_H | DIRECT | LEVEL_FORECAST_K12 | 12885 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 536 |
| NATIVE | BAND_H | DIRECT | LEVEL_FORECAST_K4 | 12866 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 536 |
| NATIVE | BAND_H | DIRECT | LEVEL_NOW | 21453 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 893 |
| NATIVE | BAND_H | DIRECT | RANGE_SCALE | 21310 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 887 |
| NATIVE | BAND_H | DIRECT | SHOCK | 20458 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 852 |
| NATIVE | BAND_H | DIRECT | SWING_GT_CUR | 20325 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 846 |
| NATIVE | BAND_H | DIRECT | SWING_SCALE | 19807 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 825 |
| NATIVE | BAND_H | DIRECT | TAIL_RISK | 21521 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 896 |
| NATIVE | BAND_H | REVERSE | LEVEL_FORECAST_K12 | 12964 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 540 |
| NATIVE | BAND_H | REVERSE | LEVEL_FORECAST_K4 | 12905 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 537 |
| NATIVE | BAND_H | REVERSE | LEVEL_NOW | 21354 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 889 |
| NATIVE | BAND_H | REVERSE | RANGE_SCALE | 21707 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 904 |
| NATIVE | BAND_H | REVERSE | SHOCK | 22423 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 934 |
| NATIVE | BAND_H | REVERSE | SWING_GT_CUR | 20167 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 840 |
| NATIVE | BAND_H | REVERSE | SWING_SCALE | 20409 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 850 |
| NATIVE | BAND_H | REVERSE | TAIL_RISK | 21585 | 0.000 | 0.000 | 0.000 | 0.000 | [0.000, 0.000] | 0.000 | 899 |
| NATIVE | BAND_Z | DIRECT | LEVEL_FORECAST_K12 | 6004 | 2.220 | 0.000 | -1.858 | 5.746 | [-1.897, -1.543] | 24.444 | 250 |
| NATIVE | BAND_Z | DIRECT | LEVEL_FORECAST_K4 | 6036 | 1.174 | 0.000 | -2.811 | 4.867 | [-2.881, -2.637] | 25.213 | 251 |
| NATIVE | BAND_Z | DIRECT | LEVEL_NOW | 10138 | -0.151 | 0.000 | -2.915 | 2.654 | [-3.051, -2.797] | 18.697 | 422 |
| NATIVE | BAND_Z | DIRECT | RANGE_SCALE | 12112 | 0.544 | 0.000 | -1.816 | 2.790 | [-1.914, -1.662] | 14.997 | 504 |
| NATIVE | BAND_Z | DIRECT | SHOCK | 9966 | 4.142 | 0.000 | 0.872 | 7.127 | [0.816, 1.098] | 20.850 | 415 |
| NATIVE | BAND_Z | DIRECT | SWING_GT_CUR | 9658 | 3.728 | 0.000 | 0.774 | 6.667 | [0.747, 0.839] | 20.395 | 402 |
| NATIVE | BAND_Z | DIRECT | SWING_SCALE | 12053 | 1.283 | 0.000 | -0.624 | 3.213 | [-0.728, -0.480] | 12.502 | 502 |
| NATIVE | BAND_Z | DIRECT | TAIL_RISK | 10093 | 2.023 | 0.000 | -0.692 | 4.638 | [-0.805, -0.627] | 19.358 | 420 |
| NATIVE | BAND_Z | REVERSE | LEVEL_FORECAST_K12 | 5943 | 4.140 | 0.000 | 0.824 | 7.604 | [0.802, 0.932] | 22.172 | 247 |
| NATIVE | BAND_Z | REVERSE | LEVEL_FORECAST_K4 | 5929 | 5.361 | 0.000 | 2.271 | 8.711 | [2.164, 2.338] | 22.325 | 247 |
| NATIVE | BAND_Z | REVERSE | LEVEL_NOW | 9981 | 3.101 | 0.000 | 0.300 | 5.866 | [0.226, 0.360] | 19.055 | 415 |
| NATIVE | BAND_Z | REVERSE | RANGE_SCALE | 12177 | 3.479 | 0.000 | 1.529 | 5.396 | [1.463, 1.618] | 13.839 | 507 |
| NATIVE | BAND_Z | REVERSE | SHOCK | 10044 | -1.045 | 0.000 | -3.606 | 1.591 | [-3.787, -3.581] | 18.119 | 418 |
| NATIVE | BAND_Z | REVERSE | SWING_GT_CUR | 9503 | 2.646 | 0.000 | 0.060 | 5.176 | [-0.008, 0.240] | 17.538 | 395 |
| NATIVE | BAND_Z | REVERSE | SWING_SCALE | 12168 | 0.948 | 0.000 | -0.729 | 2.615 | [-0.733, -0.696] | 10.684 | 507 |
| NATIVE | BAND_Z | REVERSE | TAIL_RISK | 10168 | 3.853 | 0.000 | 1.399 | 6.248 | [1.385, 1.476] | 17.399 | 423 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | LEVEL_FORECAST_K12 | 5676 | 3.445 | 0.000 | 0.391 | 6.656 | [0.169, 0.446] | 22.123 | 236 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | LEVEL_FORECAST_K4 | 5640 | 1.015 | 0.000 | -2.143 | 4.218 | [-2.377, -2.122] | 23.582 | 235 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | LEVEL_NOW | 9455 | -2.126 | 0.000 | -5.001 | 0.660 | [-5.023, -4.890] | 18.478 | 393 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | RANGE_SCALE | 11407 | 1.118 | 0.000 | -1.257 | 3.517 | [-1.315, -1.143] | 15.862 | 475 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | SHOCK | 8956 | 2.193 | 0.000 | -0.951 | 5.375 | [-1.042, -0.843] | 20.629 | 373 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | SWING_GT_CUR | 9027 | 2.743 | 0.000 | 0.171 | 5.464 | [0.085, 0.221] | 18.488 | 376 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | SWING_SCALE | 11395 | 0.955 | 0.000 | -0.544 | 2.450 | [-0.595, -0.487] | 10.519 | 474 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_DIRECT | TAIL_RISK | 9470 | 0.353 | 0.000 | -2.311 | 3.118 | [-2.377, -2.213] | 18.208 | 394 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | LEVEL_FORECAST_K12 | 5964 | 2.019 | 0.000 | -1.569 | 5.653 | [-1.761, -1.475] | 24.568 | 248 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | LEVEL_FORECAST_K4 | 5988 | 0.518 | 0.000 | -2.697 | 3.897 | [-2.878, -2.664] | 23.412 | 249 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | LEVEL_NOW | 10066 | 0.208 | 0.000 | -3.211 | 3.435 | [-3.225, -3.028] | 20.853 | 419 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | RANGE_SCALE | 11933 | 1.667 | 0.000 | -0.728 | 4.045 | [-0.815, -0.698] | 16.122 | 497 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | SHOCK | 10017 | 5.094 | 0.000 | 1.757 | 8.438 | [1.704, 1.837] | 20.962 | 417 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | SWING_GT_CUR | 9521 | 2.806 | 0.000 | 0.100 | 5.574 | [0.046, 0.231] | 19.253 | 396 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | SWING_SCALE | 11790 | 1.129 | 0.000 | -0.767 | 3.074 | [-0.854, -0.738] | 13.161 | 491 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | DIRECT_REVERSE | TAIL_RISK | 10077 | 1.381 | 0.000 | -1.580 | 4.388 | [-1.686, -1.477] | 19.738 | 419 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | LEVEL_FORECAST_K12 | 6036 | 3.631 | 0.000 | 0.318 | 7.068 | [0.213, 0.475] | 22.721 | 251 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | LEVEL_FORECAST_K4 | 5855 | 4.634 | 0.000 | 1.518 | 7.818 | [1.456, 1.546] | 21.664 | 243 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | LEVEL_NOW | 9922 | 5.363 | 0.000 | 2.792 | 7.905 | [2.694, 2.907] | 18.025 | 413 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | RANGE_SCALE | 12014 | 2.100 | 0.000 | 0.005 | 4.143 | [-0.018, 0.091] | 13.435 | 500 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | SHOCK | 10209 | 0.211 | 0.000 | -2.562 | 3.019 | [-2.773, -2.487] | 19.046 | 425 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | SWING_GT_CUR | 9445 | 2.743 | 0.000 | -0.258 | 5.602 | [-0.341, -0.080] | 18.940 | 393 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | SWING_SCALE | 11954 | 1.291 | 0.000 | -0.310 | 2.904 | [-0.403, -0.242] | 10.648 | 498 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_DIRECT | TAIL_RISK | 10025 | 2.843 | 0.000 | -0.011 | 5.588 | [-0.091, 0.206] | 18.988 | 417 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | LEVEL_FORECAST_K12 | 5739 | 2.920 | 0.000 | -0.028 | 5.916 | [-0.146, 0.089] | 21.330 | 239 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | LEVEL_FORECAST_K4 | 5664 | 2.983 | 0.000 | -0.049 | 5.964 | [-0.156, 0.115] | 21.193 | 236 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | LEVEL_NOW | 9453 | 0.884 | 0.000 | -1.587 | 3.353 | [-1.641, -1.361] | 16.487 | 393 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | RANGE_SCALE | 11665 | 2.461 | 0.000 | 0.763 | 4.195 | [0.695, 0.790] | 11.690 | 486 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | SHOCK | 9936 | -1.066 | 0.000 | -3.399 | 1.364 | [-3.603, -3.315] | 16.644 | 414 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | SWING_GT_CUR | 8948 | 1.484 | 0.000 | -1.166 | 4.026 | [-1.322, -1.097] | 17.711 | 372 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | SWING_SCALE | 11786 | 0.940 | 0.000 | -0.621 | 2.512 | [-0.682, -0.563] | 10.333 | 491 |
| NATIVE_COMBINATION | BAND_Z+BAND_H | REVERSE_REVERSE | TAIL_RISK | 9691 | 1.604 | 0.000 | -0.797 | 4.055 | [-0.995, -0.780] | 17.398 | 403 |

## A3 — device tables

**ctrader / device_target.parquet total_rows=2040**

**-- row census by arm_class x state --**

```text
arm_class                         state
FIXED_MANAGEMENT                  EVENT_UNDECIDED     36
                                  INCOMPLETE          72
                                  NO_EVENT            72
                                  NO_FEATURE          72
                                  ORDER_CREATED       72
MANAGEMENT                        EVENT_UNDECIDED    144
                                  INCOMPLETE         288
                                  NO_EVENT           288
                                  NO_FEATURE         144
                                  ORDER_CREATED      288
MANAGEMENT_COMPONENT_COMBINATION  EVENT_UNDECIDED     60
                                  INCOMPLETE          96
                                  NO_EVENT           120
                                  ORDER_CREATED      120
MANAGEMENT_DEVICE_COMBINATION     EVENT_UNDECIDED     24
                                  INCOMPLETE          48
                                  NO_EVENT            48
                                  ORDER_CREATED       48
```

**-- rows with a defined estimate: 344 of 2040**

**-- ctrader / E_TOUCH / target : adaptive-minus-fixed by component x setting --**

| arm_class | component | setting | metric | comparator | sym_rows | episode_n | entry_fill_n | close_n | common_fill_n | common_close_n | obs med | comp med | est med | est min | est max | CI>0 | CI<0 | mde med | eff_trade_blocks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIXED_MANAGEMENT | FIXED | M0.75 | missed_excess_bps | FIXED_TARGET_M0.75 | 3 | 937 | 940 | 937 | 940 | 937 | 26.112 | 26.112 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 130 |
| FIXED_MANAGEMENT | FIXED | M0.75 | reach_rate | FIXED_TARGET_M0.75 | 3 | 937 | 940 | 937 | 940 | 937 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 130 |
| FIXED_MANAGEMENT | FIXED | M0.75 | realised_capture_bps | FIXED_TARGET_M0.75 | 3 | 937 | 940 | 937 | 940 | 937 | 5.532 | 5.532 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 130 |
| FIXED_MANAGEMENT | FIXED | M0.75 | time_to_target | FIXED_TARGET_M0.75 | 3 | 937 | 940 | 937 | 940 | 937 | 44.010 | 44.010 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 130 |
| FIXED_MANAGEMENT | FIXED | M1.00 | missed_excess_bps | FIXED_TARGET_M1.00 | 3 | 582 | 585 | 582 | 585 | 582 | 25.617 | 25.617 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 102 |
| FIXED_MANAGEMENT | FIXED | M1.00 | reach_rate | FIXED_TARGET_M1.00 | 3 | 582 | 585 | 582 | 585 | 582 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 102 |
| FIXED_MANAGEMENT | FIXED | M1.00 | realised_capture_bps | FIXED_TARGET_M1.00 | 3 | 582 | 585 | 582 | 585 | 582 | 7.376 | 7.376 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 102 |
| FIXED_MANAGEMENT | FIXED | M1.00 | time_to_target | FIXED_TARGET_M1.00 | 3 | 582 | 585 | 582 | 585 | 582 | 49.880 | 49.880 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 102 |
| FIXED_MANAGEMENT | FIXED | M1.50 | missed_excess_bps | FIXED_TARGET_M1.50 | 3 | 436 | 438 | 436 | 438 | 436 | 22.520 | 22.520 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 107 |
| FIXED_MANAGEMENT | FIXED | M1.50 | reach_rate | FIXED_TARGET_M1.50 | 3 | 436 | 438 | 436 | 438 | 436 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 107 |
| FIXED_MANAGEMENT | FIXED | M1.50 | realised_capture_bps | FIXED_TARGET_M1.50 | 3 | 436 | 438 | 436 | 438 | 436 | 11.064 | 11.064 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 107 |
| FIXED_MANAGEMENT | FIXED | M1.50 | time_to_target | FIXED_TARGET_M1.50 | 3 | 436 | 438 | 436 | 438 | 436 | 79.618 | 79.618 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 107 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | missed_excess_bps | FIXED_TARGET_M1.00 | 3 | 441 | 470 | 467 | 443 | 441 | 27.350 | 27.359 | 0.000 | -0.009 | 0.082 | 0 | 0 | 0.154 | 80 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | reach_rate | FIXED_TARGET_M1.00 | 3 | 441 | 470 | 467 | 443 | 441 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 80 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | realised_capture_bps | FIXED_TARGET_M1.00 | 3 | 441 | 470 | 467 | 443 | 441 | 7.208 | 7.376 | 0.000 | -0.168 | 0.055 | 0 | 0 | 0.249 | 80 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | time_to_target | FIXED_TARGET_M1.00 | 3 | 441 | 470 | 467 | 443 | 441 | 72.700 | 55.066 | 0.000 | -0.035 | 17.633 | 0 | 0 | 8.861 | 80 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | missed_excess_bps | FIXED_TARGET_M1.00 | 3 | 449 | 476 | 473 | 451 | 449 | 26.511 | 26.912 | 0.000 | -0.401 | 0.082 | 0 | 1 | 0.425 | 80 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | reach_rate | FIXED_TARGET_M1.00 | 3 | 449 | 476 | 473 | 451 | 449 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 80 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | realised_capture_bps | FIXED_TARGET_M1.00 | 3 | 449 | 476 | 473 | 451 | 449 | 7.208 | 7.376 | 0.000 | -0.168 | 0.198 | 0 | 0 | 0.273 | 80 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | time_to_target | FIXED_TARGET_M1.00 | 3 | 449 | 476 | 473 | 451 | 449 | 68.025 | 53.572 | 0.000 | -0.035 | 14.453 | 0 | 0 | 10.859 | 80 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | missed_excess_bps | FIXED_TARGET_M1.00 | 3 | 358 | 495 | 492 | 360 | 358 | 27.109 | 27.174 | -0.064 | -0.474 | 0.000 | 0 | 0 | 0.950 | 73 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | reach_rate | FIXED_TARGET_M1.00 | 3 | 358 | 495 | 492 | 360 | 358 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 73 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | realised_capture_bps | FIXED_TARGET_M1.00 | 3 | 358 | 495 | 492 | 360 | 358 | 7.500 | 7.376 | 0.023 | 0.000 | 0.355 | 0 | 0 | 0.779 | 73 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | time_to_target | FIXED_TARGET_M1.00 | 3 | 358 | 495 | 492 | 360 | 358 | 82.449 | 66.018 | 0.000 | -0.129 | 16.432 | 0 | 0 | 14.444 | 73 |
| MANAGEMENT | RANGE_SCALE | M0.75 | missed_excess_bps | FIXED_TARGET_M0.75 | 3 | 168 | 481 | 478 | 169 | 168 | 23.905 | 24.706 | -0.801 | -5.541 | 0.300 | 1 | 0 | 3.135 | 27 |
| MANAGEMENT | RANGE_SCALE | M0.75 | reach_rate | FIXED_TARGET_M0.75 | 3 | 168 | 481 | 478 | 169 | 168 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 27 |
| MANAGEMENT | RANGE_SCALE | M0.75 | realised_capture_bps | FIXED_TARGET_M0.75 | 3 | 168 | 481 | 478 | 169 | 168 | 6.653 | 5.532 | 1.049 | -0.300 | 8.341 | 1 | 1 | 3.225 | 27 |
| MANAGEMENT | RANGE_SCALE | M0.75 | time_to_target | FIXED_TARGET_M0.75 | 3 | 168 | 481 | 478 | 169 | 168 | 5.600 | 7.081 | 3.698 | -55.511 | 133.370 | 1 | 1 | 68.483 | 27 |
| MANAGEMENT | RANGE_SCALE | M1.00 | missed_excess_bps | FIXED_TARGET_M1.00 | 3 | 211 | 423 | 420 | 212 | 211 | 28.967 | 30.575 | -1.608 | -9.253 | 0.327 | 1 | 2 | 2.734 | 40 |
| MANAGEMENT | RANGE_SCALE | M1.00 | reach_rate | FIXED_TARGET_M1.00 | 3 | 211 | 423 | 420 | 212 | 211 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 40 |
| MANAGEMENT | RANGE_SCALE | M1.00 | realised_capture_bps | FIXED_TARGET_M1.00 | 3 | 211 | 423 | 420 | 212 | 211 | 9.915 | 7.376 | 2.437 | -0.327 | 11.876 | 2 | 1 | 3.317 | 40 |
| MANAGEMENT | RANGE_SCALE | M1.00 | time_to_target | FIXED_TARGET_M1.00 | 3 | 211 | 423 | 420 | 212 | 211 | 44.855 | 43.906 | 0.949 | -0.017 | 5.547 | 2 | 1 | 3.048 | 40 |
| MANAGEMENT | RANGE_SCALE | M1.50 | missed_excess_bps | FIXED_TARGET_M1.50 | 3 | 239 | 350 | 348 | 241 | 239 | 21.591 | 22.526 | -0.935 | -9.489 | 0.491 | 1 | 1 | 3.506 | 70 |
| MANAGEMENT | RANGE_SCALE | M1.50 | reach_rate | FIXED_TARGET_M1.50 | 3 | 239 | 350 | 348 | 241 | 239 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 70 |
| MANAGEMENT | RANGE_SCALE | M1.50 | realised_capture_bps | FIXED_TARGET_M1.50 | 3 | 239 | 350 | 348 | 241 | 239 | 13.171 | 11.064 | 1.955 | -0.491 | 15.299 | 2 | 1 | 3.805 | 70 |
| MANAGEMENT | RANGE_SCALE | M1.50 | time_to_target | FIXED_TARGET_M1.50 | 3 | 239 | 350 | 348 | 241 | 239 | 113.294 | 105.712 | 4.521 | -0.300 | 7.582 | 2 | 1 | 5.749 | 70 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | missed_excess_bps | FIXED_TARGET_M1.00 | 3 | 310 | 674 | 671 | 312 | 310 | 26.253 | 27.011 | -0.757 | -1.036 | 0.000 | 0 | 0 | 2.101 | 64 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | reach_rate | FIXED_TARGET_M1.00 | 3 | 310 | 674 | 671 | 312 | 310 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 64 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | realised_capture_bps | FIXED_TARGET_M1.00 | 3 | 310 | 674 | 671 | 312 | 310 | 7.579 | 7.376 | 0.203 | 0.000 | 0.312 | 0 | 0 | 0.671 | 64 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | time_to_target | FIXED_TARGET_M1.00 | 3 | 310 | 674 | 671 | 312 | 310 | 80.743 | 69.727 | 0.000 | -63.823 | 21.179 | 0 | 0 | 107.483 | 64 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_075_HIGH_150 | missed_excess_bps | FIXED_TARGET_M1.00 | 3 | 372 | 520 | 517 | 374 | 372 | 25.975 | 25.881 | 0.095 | 0.000 | 0.244 | 0 | 0 | 0.812 | 73 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_075_HIGH_150 | reach_rate | FIXED_TARGET_M1.00 | 3 | 372 | 520 | 517 | 374 | 372 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 73 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_075_HIGH_150 | realised_capture_bps | FIXED_TARGET_M1.00 | 3 | 372 | 520 | 517 | 374 | 372 | 7.056 | 7.376 | -0.174 | -0.320 | 0.000 | 0 | 0 | 0.769 | 73 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_075_HIGH_150 | time_to_target | FIXED_TARGET_M1.00 | 3 | 372 | 520 | 517 | 374 | 372 | 72.406 | 65.782 | 0.000 | -0.568 | 16.998 | 0 | 0 | 13.438 | 73 |
| MANAGEMENT | SWING_SCALE | M0.75 | missed_excess_bps | FIXED_TARGET_M0.75 | 1 | 3 | 28 | 27 | 3 | 3 | 4.342 | 79.659 | -75.316 | -75.316 | -75.316 | 0 | 0 | 129.436 | 3 |
| MANAGEMENT | SWING_SCALE | M0.75 | reach_rate | FIXED_TARGET_M0.75 | 1 | 3 | 28 | 27 | 3 | 3 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 3 |
| MANAGEMENT | SWING_SCALE | M0.75 | realised_capture_bps | FIXED_TARGET_M0.75 | 1 | 3 | 28 | 27 | 3 | 3 | 196.489 | 5.533 | 190.956 | 190.956 | 190.956 | 1 | 0 | 71.138 | 3 |
| MANAGEMENT | SWING_SCALE | M0.75 | time_to_target | FIXED_TARGET_M0.75 | 1 | 3 | 28 | 27 | 3 | 3 | 125.089 | 0.156 | 124.933 | 124.933 | 124.933 | 1 | 0 | 48.183 | 3 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | missed_excess_bps | FIXED_TARGET_M1.00 | 3 | 307 | 637 | 634 | 309 | 307 | 27.185 | 27.172 | 0.013 | -3.115 | 0.736 | 1 | 1 | 1.653 | 64 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | reach_rate | FIXED_TARGET_M1.00 | 3 | 307 | 637 | 634 | 309 | 307 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 64 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | realised_capture_bps | FIXED_TARGET_M1.00 | 3 | 307 | 637 | 634 | 309 | 307 | 7.418 | 7.376 | -0.059 | -0.736 | 2.928 | 1 | 1 | 0.903 | 64 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | time_to_target | FIXED_TARGET_M1.00 | 3 | 307 | 637 | 634 | 309 | 307 | 20.428 | 66.309 | -0.883 | -77.203 | 16.494 | 0 | 1 | 124.619 | 64 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | missed_excess_bps | FIXED_TARGET_M1.00 | 1 | 173 | 405 | 404 | 173 | 173 | 26.197 | 27.829 | -1.633 | -1.633 | -1.633 | 0 | 1 | 1.222 | 33 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | reach_rate | FIXED_TARGET_M1.00 | 1 | 173 | 405 | 404 | 173 | 173 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 33 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | realised_capture_bps | FIXED_TARGET_M1.00 | 1 | 173 | 405 | 404 | 173 | 173 | 9.989 | 7.478 | 2.511 | 2.511 | 2.511 | 1 | 0 | 1.548 | 33 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | time_to_target | FIXED_TARGET_M1.00 | 1 | 173 | 405 | 404 | 173 | 173 | 40.259 | 40.903 | -0.644 | -0.644 | -0.644 | 0 | 0 | 2.295 | 33 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | missed_excess_bps | FIXED_TARGET_M1.00 | 2 | 305 | 580 | 578 | 306 | 305 | 45.578 | 45.718 | -0.141 | -0.195 | -0.086 | 0 | 0 | 1.124 | 60 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | reach_rate | FIXED_TARGET_M1.00 | 2 | 305 | 580 | 578 | 306 | 305 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 60 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | realised_capture_bps | FIXED_TARGET_M1.00 | 2 | 305 | 580 | 578 | 306 | 305 | 7.457 | 7.426 | 0.030 | 0.000 | 0.061 | 0 | 0 | 0.893 | 60 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | time_to_target | FIXED_TARGET_M1.00 | 2 | 305 | 580 | 578 | 306 | 305 | 99.635 | 91.343 | 8.292 | -1.053 | 17.636 | 0 | 0 | 15.777 | 60 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | missed_excess_bps | FIXED_TARGET_M1.00 | 6 | 1121 | 57650 | 57650 | 1127 | 1121 | 32.101 | 25.969 | 4.384 | 0.327 | 6.141 | 6 | 0 | 2.175 | 204 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | reach_rate | FIXED_TARGET_M1.00 | 6 | 1121 | 57650 | 57650 | 1127 | 1121 | 0.534 | 1.000 | -0.466 | -0.529 | 0.000 | 0 | 4 | 0.056 | 204 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | realised_capture_bps | FIXED_TARGET_M1.00 | 6 | 1121 | 57650 | 57650 | 1127 | 1121 | 1.700 | 7.376 | -5.676 | -8.106 | -0.327 | 0 | 6 | 1.829 | 204 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | time_to_target | FIXED_TARGET_M1.00 | 6 | 1121 | 57650 | 57650 | 1127 | 1121 | 0.344 | 51.362 | -51.018 | -63.648 | -0.017 | 0 | 6 | 85.149 | 204 |
**-- ctrader / E_CLOSE / target : adaptive-minus-fixed by component x setting --**

| arm_class | component | setting | metric | comparator | sym_rows | episode_n | entry_fill_n | close_n | common_fill_n | common_close_n | obs med | comp med | est med | est min | est max | CI>0 | CI<0 | mde med | eff_trade_blocks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIXED_MANAGEMENT | FIXED | M0.75 | missed_excess_bps | FIXED_TARGET_M0.75 | 3 | 729 | 732 | 729 | 732 | 729 | 24.457 | 24.457 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 124 |
| FIXED_MANAGEMENT | FIXED | M0.75 | reach_rate | FIXED_TARGET_M0.75 | 3 | 729 | 732 | 729 | 732 | 729 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 124 |
| FIXED_MANAGEMENT | FIXED | M0.75 | realised_capture_bps | FIXED_TARGET_M0.75 | 3 | 729 | 732 | 729 | 732 | 729 | 5.532 | 5.532 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 124 |
| FIXED_MANAGEMENT | FIXED | M0.75 | time_to_target | FIXED_TARGET_M0.75 | 3 | 729 | 732 | 729 | 732 | 729 | 39.088 | 39.088 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 124 |
| FIXED_MANAGEMENT | FIXED | M1.00 | missed_excess_bps | FIXED_TARGET_M1.00 | 2 | 490 | 492 | 490 | 492 | 490 | 34.751 | 34.751 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 109 |
| FIXED_MANAGEMENT | FIXED | M1.00 | reach_rate | FIXED_TARGET_M1.00 | 2 | 490 | 492 | 490 | 492 | 490 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 109 |
| FIXED_MANAGEMENT | FIXED | M1.00 | realised_capture_bps | FIXED_TARGET_M1.00 | 2 | 490 | 492 | 490 | 492 | 490 | 7.427 | 7.427 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 109 |
| FIXED_MANAGEMENT | FIXED | M1.00 | time_to_target | FIXED_TARGET_M1.00 | 2 | 490 | 492 | 490 | 492 | 490 | 84.349 | 84.349 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 109 |
| FIXED_MANAGEMENT | FIXED | M1.50 | missed_excess_bps | FIXED_TARGET_M1.50 | 2 | 409 | 411 | 409 | 411 | 409 | 30.910 | 30.910 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 119 |
| FIXED_MANAGEMENT | FIXED | M1.50 | reach_rate | FIXED_TARGET_M1.50 | 2 | 409 | 411 | 409 | 411 | 409 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 119 |
| FIXED_MANAGEMENT | FIXED | M1.50 | realised_capture_bps | FIXED_TARGET_M1.50 | 2 | 409 | 411 | 409 | 411 | 409 | 11.141 | 11.141 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 119 |
| FIXED_MANAGEMENT | FIXED | M1.50 | time_to_target | FIXED_TARGET_M1.50 | 2 | 409 | 411 | 409 | 411 | 409 | 101.446 | 101.446 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 119 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | missed_excess_bps | FIXED_TARGET_M1.00 | 2 | 410 | 460 | 458 | 411 | 410 | 36.606 | 36.839 | -0.234 | -0.496 | 0.029 | 0 | 1 | 0.346 | 89 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | reach_rate | FIXED_TARGET_M1.00 | 2 | 410 | 460 | 458 | 411 | 410 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 89 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | realised_capture_bps | FIXED_TARGET_M1.00 | 2 | 410 | 460 | 458 | 411 | 410 | 7.686 | 7.427 | 0.258 | -0.101 | 0.618 | 1 | 0 | 0.352 | 89 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | time_to_target | FIXED_TARGET_M1.00 | 2 | 410 | 460 | 458 | 411 | 410 | 72.005 | 68.079 | 3.926 | -0.083 | 7.935 | 0 | 0 | 4.358 | 89 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | missed_excess_bps | FIXED_TARGET_M1.00 | 2 | 356 | 519 | 517 | 357 | 356 | 35.577 | 35.811 | -0.233 | -0.388 | -0.078 | 0 | 1 | 0.295 | 78 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | reach_rate | FIXED_TARGET_M1.00 | 2 | 356 | 519 | 517 | 357 | 356 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 78 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | realised_capture_bps | FIXED_TARGET_M1.00 | 2 | 356 | 519 | 517 | 357 | 356 | 7.730 | 7.428 | 0.302 | 0.099 | 0.506 | 1 | 0 | 0.253 | 78 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | time_to_target | FIXED_TARGET_M1.00 | 2 | 356 | 519 | 517 | 357 | 356 | 95.396 | 75.373 | 20.023 | 7.696 | 32.350 | 0 | 0 | 20.544 | 78 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | missed_excess_bps | FIXED_TARGET_M1.00 | 2 | 314 | 557 | 555 | 315 | 314 | 34.388 | 35.045 | -0.657 | -1.095 | -0.219 | 0 | 1 | 0.706 | 75 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | reach_rate | FIXED_TARGET_M1.00 | 2 | 314 | 557 | 555 | 315 | 314 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 75 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | realised_capture_bps | FIXED_TARGET_M1.00 | 2 | 314 | 557 | 555 | 315 | 314 | 8.286 | 7.428 | 0.858 | 0.528 | 1.188 | 1 | 0 | 0.726 | 75 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | time_to_target | FIXED_TARGET_M1.00 | 2 | 314 | 557 | 555 | 315 | 314 | 106.603 | 85.063 | 21.541 | 8.100 | 34.982 | 0 | 0 | 30.768 | 75 |
| MANAGEMENT | RANGE_SCALE | M0.75 | missed_excess_bps | FIXED_TARGET_M0.75 | 3 | 313 | 514 | 511 | 315 | 313 | 26.499 | 26.551 | -0.129 | -3.126 | -0.052 | 0 | 1 | 1.330 | 76 |
| MANAGEMENT | RANGE_SCALE | M0.75 | reach_rate | FIXED_TARGET_M0.75 | 3 | 313 | 514 | 511 | 315 | 313 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 76 |
| MANAGEMENT | RANGE_SCALE | M0.75 | realised_capture_bps | FIXED_TARGET_M0.75 | 3 | 313 | 514 | 511 | 315 | 313 | 7.601 | 5.532 | 1.995 | 0.082 | 4.890 | 2 | 0 | 0.898 | 76 |
| MANAGEMENT | RANGE_SCALE | M0.75 | time_to_target | FIXED_TARGET_M0.75 | 3 | 313 | 514 | 511 | 315 | 313 | 49.841 | 45.664 | 4.177 | -24.764 | 10.963 | 2 | 0 | 10.010 | 76 |
| MANAGEMENT | RANGE_SCALE | M1.00 | missed_excess_bps | FIXED_TARGET_M1.00 | 2 | 162 | 421 | 419 | 162 | 162 | 34.343 | 39.111 | -4.768 | -7.969 | -1.567 | 0 | 2 | 2.376 | 44 |
| MANAGEMENT | RANGE_SCALE | M1.00 | reach_rate | FIXED_TARGET_M1.00 | 2 | 162 | 421 | 419 | 162 | 162 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 44 |
| MANAGEMENT | RANGE_SCALE | M1.00 | realised_capture_bps | FIXED_TARGET_M1.00 | 2 | 162 | 421 | 419 | 162 | 162 | 14.318 | 7.428 | 6.890 | 2.580 | 11.201 | 2 | 0 | 2.858 | 44 |
| MANAGEMENT | RANGE_SCALE | M1.00 | time_to_target | FIXED_TARGET_M1.00 | 2 | 162 | 421 | 419 | 162 | 162 | 127.725 | 97.629 | 30.095 | 10.748 | 49.443 | 2 | 0 | 29.340 | 44 |
| MANAGEMENT | RANGE_SCALE | M1.50 | missed_excess_bps | FIXED_TARGET_M1.50 | 2 | 111 | 297 | 295 | 112 | 111 | 32.485 | 38.469 | -5.984 | -10.279 | -1.688 | 0 | 0 | 6.617 | 36 |
| MANAGEMENT | RANGE_SCALE | M1.50 | reach_rate | FIXED_TARGET_M1.50 | 2 | 111 | 297 | 295 | 112 | 111 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 36 |
| MANAGEMENT | RANGE_SCALE | M1.50 | realised_capture_bps | FIXED_TARGET_M1.50 | 2 | 111 | 297 | 295 | 112 | 111 | 21.540 | 11.141 | 10.399 | 2.429 | 18.369 | 2 | 0 | 7.837 | 36 |
| MANAGEMENT | RANGE_SCALE | M1.50 | time_to_target | FIXED_TARGET_M1.50 | 2 | 111 | 297 | 295 | 112 | 111 | 54.981 | 49.756 | 5.226 | -1.067 | 11.519 | 0 | 0 | 10.487 | 36 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | missed_excess_bps | FIXED_TARGET_M1.00 | 2 | 360 | 671 | 669 | 361 | 360 | 36.611 | 37.262 | -0.651 | -0.670 | -0.631 | 0 | 1 | 1.520 | 82 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | reach_rate | FIXED_TARGET_M1.00 | 2 | 360 | 671 | 669 | 361 | 360 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 82 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | realised_capture_bps | FIXED_TARGET_M1.00 | 2 | 360 | 671 | 669 | 361 | 360 | 7.407 | 7.427 | -0.020 | -0.259 | 0.220 | 0 | 0 | 0.498 | 82 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | time_to_target | FIXED_TARGET_M1.00 | 2 | 360 | 671 | 669 | 361 | 360 | 45.739 | 49.089 | -3.350 | -4.772 | -1.928 | 0 | 1 | 7.617 | 82 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_075_HIGH_150 | missed_excess_bps | FIXED_TARGET_M1.00 | 2 | 329 | 461 | 459 | 330 | 329 | 35.027 | 35.744 | -0.717 | -0.795 | -0.639 | 0 | 0 | 1.965 | 79 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_075_HIGH_150 | reach_rate | FIXED_TARGET_M1.00 | 2 | 329 | 461 | 459 | 330 | 329 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 79 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_075_HIGH_150 | realised_capture_bps | FIXED_TARGET_M1.00 | 2 | 329 | 461 | 459 | 330 | 329 | 7.479 | 7.428 | 0.052 | -0.564 | 0.667 | 0 | 0 | 0.756 | 79 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_075_HIGH_150 | time_to_target | FIXED_TARGET_M1.00 | 2 | 329 | 461 | 459 | 330 | 329 | 81.280 | 85.134 | -3.854 | -6.598 | -1.110 | 0 | 0 | 8.058 | 79 |
| MANAGEMENT | SWING_SCALE | M0.75 | missed_excess_bps | FIXED_TARGET_M0.75 | 1 | 5 | 22 | 21 | 5 | 5 | 1.682 | 33.105 | -31.423 | -31.423 | -31.423 | 0 | 1 | 26.808 | 5 |
| MANAGEMENT | SWING_SCALE | M0.75 | reach_rate | FIXED_TARGET_M0.75 | 1 | 5 | 22 | 21 | 5 | 5 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 5 |
| MANAGEMENT | SWING_SCALE | M0.75 | realised_capture_bps | FIXED_TARGET_M0.75 | 1 | 5 | 22 | 21 | 5 | 5 | 153.520 | 5.534 | 147.986 | 147.986 | 147.986 | 1 | 0 | 7.303 | 5 |
| MANAGEMENT | SWING_SCALE | M0.75 | time_to_target | FIXED_TARGET_M0.75 | 1 | 5 | 22 | 21 | 5 | 5 | 281.027 | 0.257 | 280.770 | 280.770 | 280.770 | 1 | 0 | 216.680 | 5 |
| MANAGEMENT | SWING_SCALE | M1.00 | missed_excess_bps | FIXED_TARGET_M1.00 | 1 | 3 | 21 | 20 | 3 | 3 | 7.351 | 55.526 | -48.176 | -48.176 | -48.176 | 0 | 1 | 21.705 | 3 |
| MANAGEMENT | SWING_SCALE | M1.00 | reach_rate | FIXED_TARGET_M1.00 | 1 | 3 | 21 | 20 | 3 | 3 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 3 |
| MANAGEMENT | SWING_SCALE | M1.00 | realised_capture_bps | FIXED_TARGET_M1.00 | 1 | 3 | 21 | 20 | 3 | 3 | 183.376 | 7.375 | 176.002 | 176.002 | 176.002 | 1 | 0 | 25.027 | 3 |
| MANAGEMENT | SWING_SCALE | M1.00 | time_to_target | FIXED_TARGET_M1.00 | 1 | 3 | 21 | 20 | 3 | 3 | 180.044 | 0.167 | 179.878 | 179.878 | 179.878 | 1 | 0 | 160.211 | 3 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | missed_excess_bps | FIXED_TARGET_M1.00 | 2 | 301 | 523 | 521 | 302 | 301 | 32.893 | 34.262 | -1.369 | -2.647 | -0.091 | 0 | 1 | 0.632 | 75 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | reach_rate | FIXED_TARGET_M1.00 | 2 | 301 | 523 | 521 | 302 | 301 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 75 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | realised_capture_bps | FIXED_TARGET_M1.00 | 2 | 301 | 523 | 521 | 302 | 301 | 9.183 | 7.428 | 1.755 | 0.373 | 3.138 | 1 | 0 | 0.737 | 75 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | time_to_target | FIXED_TARGET_M1.00 | 2 | 301 | 523 | 521 | 302 | 301 | 110.709 | 88.294 | 22.415 | 9.862 | 34.968 | 1 | 0 | 30.867 | 75 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | missed_excess_bps | FIXED_TARGET_M1.00 | 6 | 300 | 1360 | 1354 | 302 | 300 | 27.738 | 32.095 | -2.769 | -5.357 | 1.789 | 0 | 5 | 1.945 | 89 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | reach_rate | FIXED_TARGET_M1.00 | 6 | 300 | 1360 | 1354 | 302 | 300 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 89 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | realised_capture_bps | FIXED_TARGET_M1.00 | 6 | 300 | 1360 | 1354 | 302 | 300 | 12.671 | 7.475 | 5.243 | 2.143 | 12.497 | 6 | 0 | 1.809 | 89 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | time_to_target | FIXED_TARGET_M1.00 | 6 | 300 | 1360 | 1354 | 302 | 300 | 36.324 | 14.827 | 3.436 | 1.164 | 2460.133 | 6 | 0 | 2.889 | 89 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | missed_excess_bps | FIXED_TARGET_M1.00 | 2 | 181 | 733 | 731 | 182 | 181 | 29.779 | 30.426 | -0.648 | -1.056 | -0.239 | 0 | 1 | 0.901 | 47 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | reach_rate | FIXED_TARGET_M1.00 | 2 | 181 | 733 | 731 | 182 | 181 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 47 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | realised_capture_bps | FIXED_TARGET_M1.00 | 2 | 181 | 733 | 731 | 182 | 181 | 8.353 | 7.428 | 0.925 | 0.576 | 1.273 | 1 | 0 | 0.917 | 47 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | time_to_target | FIXED_TARGET_M1.00 | 2 | 181 | 733 | 731 | 182 | 181 | 40.518 | 22.123 | 18.395 | -1.372 | 38.162 | 0 | 0 | 29.166 | 47 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | missed_excess_bps | FIXED_TARGET_M1.00 | 4 | 964 | 26635 | 26635 | 968 | 964 | 40.518 | 35.120 | 5.431 | 4.768 | 6.029 | 4 | 0 | 1.903 | 218 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | reach_rate | FIXED_TARGET_M1.00 | 4 | 964 | 26635 | 26635 | 968 | 964 | 0.485 | 1.000 | -0.515 | -0.535 | -0.484 | 0 | 4 | 0.064 | 218 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | realised_capture_bps | FIXED_TARGET_M1.00 | 4 | 964 | 26635 | 26635 | 968 | 964 | 0.391 | 7.427 | -7.036 | -7.992 | -6.024 | 0 | 4 | 1.548 | 218 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | time_to_target | FIXED_TARGET_M1.00 | 4 | 964 | 26635 | 26635 | 968 | 964 | 0.452 | 85.163 | -84.464 | -96.435 | -72.987 | 0 | 4 | 105.853 | 218 |
**ctrader / device_stop.parquet total_rows=1848**

**-- row census by arm_class x state --**

```text
arm_class                         state
FIXED_MANAGEMENT                  EVENT_UNDECIDED     36
                                  INCOMPLETE          72
                                  NO_EVENT            72
                                  NO_FEATURE          72
                                  ORDER_CREATED       72
MANAGEMENT                        EVENT_UNDECIDED    132
                                  INCOMPLETE         264
                                  NO_EVENT           264
                                  NO_FEATURE         120
                                  ORDER_CREATED      264
MANAGEMENT_COMPONENT_COMBINATION  EVENT_UNDECIDED     48
                                  INCOMPLETE          72
                                  NO_EVENT            96
                                  ORDER_CREATED       96
MANAGEMENT_DEVICE_COMBINATION     EVENT_UNDECIDED     24
                                  INCOMPLETE          48
                                  NO_EVENT            48
                                  ORDER_CREATED       48
```

**-- rows with a defined estimate: 288 of 1848**

**-- ctrader / E_TOUCH / stop : adaptive-minus-fixed by component x setting --**

| arm_class | component | setting | metric | comparator | sym_rows | episode_n | entry_fill_n | close_n | common_fill_n | common_close_n | obs med | comp med | est med | est min | est max | CI>0 | CI<0 | mde med | eff_trade_blocks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIXED_MANAGEMENT | FIXED | M0.75 | adverse_excursion_bps | FIXED_STOP_M0.75 | 2 | 714 | 716 | 714 | 716 | 714 | 9.959 | 9.959 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 92 |
| FIXED_MANAGEMENT | FIXED | M0.75 | loss_severity_bps | FIXED_STOP_M0.75 | 2 | 714 | 716 | 714 | 716 | 714 | -6.426 | -6.426 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 92 |
| FIXED_MANAGEMENT | FIXED | M0.75 | recovery_after_stop_bps | FIXED_STOP_M0.75 | 2 | 714 | 716 | 714 | 716 | 714 | 45.956 | 45.956 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 92 |
| FIXED_MANAGEMENT | FIXED | M0.75 | stop_rate | FIXED_STOP_M0.75 | 2 | 714 | 716 | 714 | 716 | 714 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 92 |
| FIXED_MANAGEMENT | FIXED | M1.00 | adverse_excursion_bps | FIXED_STOP_M1.00 | 2 | 537 | 539 | 537 | 539 | 537 | 11.303 | 11.303 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 93 |
| FIXED_MANAGEMENT | FIXED | M1.00 | loss_severity_bps | FIXED_STOP_M1.00 | 2 | 537 | 539 | 537 | 539 | 537 | -8.003 | -8.003 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 93 |
| FIXED_MANAGEMENT | FIXED | M1.00 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 2 | 537 | 539 | 537 | 539 | 537 | 43.455 | 43.455 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 93 |
| FIXED_MANAGEMENT | FIXED | M1.00 | stop_rate | FIXED_STOP_M1.00 | 2 | 537 | 539 | 537 | 539 | 537 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 93 |
| FIXED_MANAGEMENT | FIXED | M1.50 | adverse_excursion_bps | FIXED_STOP_M1.50 | 2 | 589 | 591 | 589 | 591 | 589 | 15.145 | 15.145 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 129 |
| FIXED_MANAGEMENT | FIXED | M1.50 | loss_severity_bps | FIXED_STOP_M1.50 | 2 | 589 | 591 | 589 | 591 | 589 | -11.451 | -11.451 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 129 |
| FIXED_MANAGEMENT | FIXED | M1.50 | recovery_after_stop_bps | FIXED_STOP_M1.50 | 2 | 589 | 591 | 589 | 591 | 589 | 38.112 | 38.112 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 129 |
| FIXED_MANAGEMENT | FIXED | M1.50 | stop_rate | FIXED_STOP_M1.50 | 2 | 589 | 591 | 589 | 591 | 589 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 129 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | adverse_excursion_bps | FIXED_STOP_M1.00 | 2 | 423 | 516 | 514 | 423 | 423 | 12.114 | 11.750 | 0.364 | 0.047 | 0.682 | 1 | 0 | 0.236 | 77 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | loss_severity_bps | FIXED_STOP_M1.00 | 2 | 423 | 516 | 514 | 423 | 423 | -8.453 | -8.134 | -0.319 | -0.655 | 0.017 | 0 | 1 | 0.259 | 77 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 2 | 423 | 516 | 514 | 423 | 423 | 46.856 | 46.606 | 0.250 | -0.034 | 0.535 | 0 | 0 | 0.689 | 77 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | stop_rate | FIXED_STOP_M1.00 | 2 | 423 | 516 | 514 | 423 | 423 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 77 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | adverse_excursion_bps | FIXED_STOP_M1.00 | 2 | 425 | 519 | 517 | 425 | 425 | 12.026 | 11.745 | 0.282 | 0.047 | 0.516 | 1 | 0 | 0.259 | 77 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | loss_severity_bps | FIXED_STOP_M1.00 | 2 | 425 | 519 | 517 | 425 | 425 | -8.392 | -8.134 | -0.258 | -0.533 | 0.017 | 0 | 1 | 0.274 | 77 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 2 | 425 | 519 | 517 | 425 | 425 | 46.846 | 46.531 | 0.315 | -0.034 | 0.663 | 0 | 0 | 0.575 | 77 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | stop_rate | FIXED_STOP_M1.00 | 2 | 425 | 519 | 517 | 425 | 425 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 77 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | adverse_excursion_bps | FIXED_STOP_M1.00 | 2 | 159 | 556 | 554 | 160 | 159 | 12.509 | 11.206 | 1.304 | 1.168 | 1.440 | 0 | 0 | 1.632 | 30 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | loss_severity_bps | FIXED_STOP_M1.00 | 2 | 159 | 556 | 554 | 160 | 159 | -9.554 | -8.234 | -1.319 | -1.342 | -1.297 | 0 | 2 | 0.959 | 30 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 2 | 159 | 556 | 554 | 160 | 159 | 39.639 | 39.229 | 0.410 | -0.510 | 1.330 | 0 | 0 | 2.934 | 30 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | stop_rate | FIXED_STOP_M1.00 | 2 | 159 | 556 | 554 | 160 | 159 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 30 |
| MANAGEMENT | RANGE_SCALE | M0.75 | adverse_excursion_bps | FIXED_STOP_M0.75 | 2 | 179 | 737 | 735 | 179 | 179 | 14.895 | 8.787 | 6.108 | 6.035 | 6.181 | 1 | 0 | 4.086 | 29 |
| MANAGEMENT | RANGE_SCALE | M0.75 | loss_severity_bps | FIXED_STOP_M0.75 | 2 | 179 | 737 | 735 | 179 | 179 | -10.221 | -5.671 | -4.550 | -6.544 | -2.555 | 0 | 1 | 3.804 | 29 |
| MANAGEMENT | RANGE_SCALE | M0.75 | recovery_after_stop_bps | FIXED_STOP_M0.75 | 2 | 179 | 737 | 735 | 179 | 179 | 44.649 | 46.270 | -1.621 | -1.912 | -1.330 | 0 | 0 | 6.217 | 29 |
| MANAGEMENT | RANGE_SCALE | M0.75 | stop_rate | FIXED_STOP_M0.75 | 2 | 179 | 737 | 735 | 179 | 179 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 29 |
| MANAGEMENT | RANGE_SCALE | M1.00 | adverse_excursion_bps | FIXED_STOP_M1.00 | 2 | 105 | 368 | 366 | 105 | 105 | 15.046 | 10.887 | 4.158 | 2.250 | 6.067 | 1 | 0 | 4.654 | 27 |
| MANAGEMENT | RANGE_SCALE | M1.00 | loss_severity_bps | FIXED_STOP_M1.00 | 2 | 105 | 368 | 366 | 105 | 105 | -11.053 | -7.428 | -3.625 | -4.453 | -2.797 | 0 | 1 | 5.961 | 27 |
| MANAGEMENT | RANGE_SCALE | M1.00 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 2 | 105 | 368 | 366 | 105 | 105 | 38.426 | 47.625 | -9.199 | -16.714 | -1.684 | 0 | 0 | 17.125 | 27 |
| MANAGEMENT | RANGE_SCALE | M1.00 | stop_rate | FIXED_STOP_M1.00 | 2 | 105 | 368 | 366 | 105 | 105 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 27 |
| MANAGEMENT | RANGE_SCALE | M1.50 | adverse_excursion_bps | FIXED_STOP_M1.50 | 2 | 274 | 504 | 502 | 274 | 274 | 18.026 | 14.512 | 3.515 | 2.944 | 4.085 | 2 | 0 | 2.268 | 69 |
| MANAGEMENT | RANGE_SCALE | M1.50 | loss_severity_bps | FIXED_STOP_M1.50 | 2 | 274 | 504 | 502 | 274 | 274 | -14.764 | -11.191 | -3.573 | -4.245 | -2.902 | 0 | 2 | 2.690 | 69 |
| MANAGEMENT | RANGE_SCALE | M1.50 | recovery_after_stop_bps | FIXED_STOP_M1.50 | 2 | 274 | 504 | 502 | 274 | 274 | 36.301 | 38.347 | -2.046 | -4.099 | 0.007 | 0 | 0 | 6.861 | 69 |
| MANAGEMENT | RANGE_SCALE | M1.50 | stop_rate | FIXED_STOP_M1.50 | 2 | 274 | 504 | 502 | 274 | 274 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 69 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | adverse_excursion_bps | FIXED_STOP_M1.00 | 2 | 76 | 572 | 570 | 76 | 76 | 11.732 | 10.808 | 0.923 | 0.364 | 1.483 | 0 | 0 | 1.733 | 18 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | loss_severity_bps | FIXED_STOP_M1.00 | 2 | 76 | 572 | 570 | 76 | 76 | -9.132 | -8.626 | -0.506 | -0.552 | -0.461 | 0 | 0 | 1.108 | 18 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 2 | 76 | 572 | 570 | 76 | 76 | 23.422 | 24.183 | -0.762 | -1.675 | 0.151 | 0 | 0 | 3.020 | 18 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | stop_rate | FIXED_STOP_M1.00 | 2 | 76 | 572 | 570 | 76 | 76 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 18 |
| MANAGEMENT | SWING_SCALE | M0.75 | adverse_excursion_bps | FIXED_STOP_M0.75 | 1 | 4 | 55 | 54 | 4 | 4 | 176.105 | 9.698 | 166.408 | 166.408 | 166.408 | 1 | 0 | 19.330 | 3 |
| MANAGEMENT | SWING_SCALE | M0.75 | loss_severity_bps | FIXED_STOP_M0.75 | 1 | 4 | 55 | 54 | 4 | 4 | -170.937 | -5.532 | -165.405 | -165.405 | -165.405 | 0 | 1 | 20.712 | 3 |
| MANAGEMENT | SWING_SCALE | M0.75 | recovery_after_stop_bps | FIXED_STOP_M0.75 | 1 | 4 | 55 | 54 | 4 | 4 | 8.204 | 86.087 | -77.883 | -77.883 | -77.883 | 0 | 1 | 40.863 | 3 |
| MANAGEMENT | SWING_SCALE | M0.75 | stop_rate | FIXED_STOP_M0.75 | 1 | 4 | 55 | 54 | 4 | 4 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 3 |
| MANAGEMENT | SWING_SCALE | M1.00 | adverse_excursion_bps | FIXED_STOP_M1.00 | 1 | 2 | 22 | 21 | 2 | 2 | 222.120 | 18.210 | 203.910 | 203.910 | 203.910 | 1 | 0 | n/a | 1 |
| MANAGEMENT | SWING_SCALE | M1.00 | loss_severity_bps | FIXED_STOP_M1.00 | 1 | 2 | 22 | 21 | 2 | 2 | -207.788 | -7.377 | -200.410 | -200.410 | -200.410 | 0 | 1 | n/a | 1 |
| MANAGEMENT | SWING_SCALE | M1.00 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 1 | 2 | 22 | 21 | 2 | 2 | 229.075 | 247.160 | -18.085 | -18.085 | -18.085 | 0 | 1 | n/a | 1 |
| MANAGEMENT | SWING_SCALE | M1.00 | stop_rate | FIXED_STOP_M1.00 | 1 | 2 | 22 | 21 | 2 | 2 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | n/a | 1 |
| MANAGEMENT | SWING_SCALE | M1.50 | adverse_excursion_bps | FIXED_STOP_M1.50 | 1 | 2 | 28 | 27 | 2 | 2 | 262.331 | 21.002 | 241.329 | 241.329 | 241.329 | 1 | 0 | n/a | 1 |
| MANAGEMENT | SWING_SCALE | M1.50 | loss_severity_bps | FIXED_STOP_M1.50 | 1 | 2 | 28 | 27 | 2 | 2 | -250.704 | -11.063 | -239.641 | -239.641 | -239.641 | 0 | 1 | n/a | 1 |
| MANAGEMENT | SWING_SCALE | M1.50 | recovery_after_stop_bps | FIXED_STOP_M1.50 | 1 | 2 | 28 | 27 | 2 | 2 | 371.773 | 282.809 | 88.964 | 88.964 | 88.964 | 1 | 0 | n/a | 1 |
| MANAGEMENT | SWING_SCALE | M1.50 | stop_rate | FIXED_STOP_M1.50 | 1 | 2 | 28 | 27 | 2 | 2 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | n/a | 1 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | adverse_excursion_bps | FIXED_STOP_M1.00 | 2 | 320 | 399 | 397 | 322 | 320 | 13.709 | 11.850 | 1.859 | 0.954 | 2.763 | 1 | 0 | 1.312 | 65 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | loss_severity_bps | FIXED_STOP_M1.00 | 2 | 320 | 399 | 397 | 322 | 320 | -10.129 | -8.267 | -1.862 | -2.737 | -0.987 | 0 | 1 | 0.845 | 65 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 2 | 320 | 399 | 397 | 322 | 320 | 44.514 | 44.646 | -0.132 | -1.402 | 1.139 | 0 | 0 | 3.278 | 65 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | stop_rate | FIXED_STOP_M1.00 | 2 | 320 | 399 | 397 | 322 | 320 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 65 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | adverse_excursion_bps | FIXED_STOP_M1.00 | 2 | 104 | 579 | 577 | 104 | 104 | 20.493 | 11.751 | 8.741 | 4.539 | 12.944 | 1 | 0 | 8.593 | 30 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | loss_severity_bps | FIXED_STOP_M1.00 | 2 | 104 | 579 | 577 | 104 | 104 | -14.913 | -7.427 | -7.486 | -10.169 | -4.803 | 0 | 1 | 8.958 | 30 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | recovery_after_stop_bps | FIXED_STOP_M1.00 | 2 | 104 | 579 | 577 | 104 | 104 | 45.672 | 50.528 | -4.856 | -9.148 | -0.565 | 0 | 0 | 14.653 | 30 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | stop_rate | FIXED_STOP_M1.00 | 2 | 104 | 579 | 577 | 104 | 104 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 30 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | adverse_excursion_bps | FIXED_STOP_M1.00 | 2 | 131 | 529 | 527 | 132 | 131 | 13.332 | 11.759 | 1.573 | 1.440 | 1.706 | 0 | 0 | 1.995 | 26 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | loss_severity_bps | FIXED_STOP_M1.00 | 2 | 131 | 529 | 527 | 132 | 131 | -10.019 | -8.422 | -1.596 | -1.656 | -1.537 | 0 | 2 | 1.019 | 26 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | recovery_after_stop_bps | FIXED_STOP_M1.00 | 2 | 131 | 529 | 527 | 132 | 131 | 43.183 | 42.776 | 0.407 | -0.726 | 1.540 | 0 | 0 | 3.642 | 26 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | stop_rate | FIXED_STOP_M1.00 | 2 | 131 | 529 | 527 | 132 | 131 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 26 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | adverse_excursion_bps | FIXED_TARGET_M1.00 | 6 | 1121 | 57650 | 57650 | 1127 | 1121 | 8.083 | 35.159 | -27.076 | -57.046 | 0.000 | 0 | 4 | 34.642 | 204 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | stop_rate | FIXED_TARGET_M1.00 | 6 | 1121 | 57650 | 57650 | 1127 | 1121 | 0.457 | 0.000 | 0.457 | 0.000 | 0.528 | 4 | 0 | 0.051 | 204 |
**-- ctrader / E_CLOSE / stop : adaptive-minus-fixed by component x setting --**

| arm_class | component | setting | metric | comparator | sym_rows | episode_n | entry_fill_n | close_n | common_fill_n | common_close_n | obs med | comp med | est med | est min | est max | CI>0 | CI<0 | mde med | eff_trade_blocks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIXED_MANAGEMENT | FIXED | M0.75 | adverse_excursion_bps | FIXED_STOP_M0.75 | 3 | 750 | 753 | 750 | 753 | 750 | 10.268 | 10.268 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 123 |
| FIXED_MANAGEMENT | FIXED | M0.75 | loss_severity_bps | FIXED_STOP_M0.75 | 3 | 750 | 753 | 750 | 753 | 750 | -5.965 | -5.965 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 123 |
| FIXED_MANAGEMENT | FIXED | M0.75 | recovery_after_stop_bps | FIXED_STOP_M0.75 | 3 | 750 | 753 | 750 | 753 | 750 | 35.555 | 35.555 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 123 |
| FIXED_MANAGEMENT | FIXED | M0.75 | stop_rate | FIXED_STOP_M0.75 | 3 | 750 | 753 | 750 | 753 | 750 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 123 |
| FIXED_MANAGEMENT | FIXED | M1.00 | adverse_excursion_bps | FIXED_STOP_M1.00 | 3 | 522 | 525 | 522 | 525 | 522 | 10.661 | 10.661 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 107 |
| FIXED_MANAGEMENT | FIXED | M1.00 | loss_severity_bps | FIXED_STOP_M1.00 | 3 | 522 | 525 | 522 | 525 | 522 | -7.436 | -7.436 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 107 |
| FIXED_MANAGEMENT | FIXED | M1.00 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 3 | 522 | 525 | 522 | 525 | 522 | 34.077 | 34.077 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 107 |
| FIXED_MANAGEMENT | FIXED | M1.00 | stop_rate | FIXED_STOP_M1.00 | 3 | 522 | 525 | 522 | 525 | 522 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 107 |
| FIXED_MANAGEMENT | FIXED | M1.50 | adverse_excursion_bps | FIXED_STOP_M1.50 | 3 | 388 | 391 | 388 | 391 | 388 | 14.111 | 14.111 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 94 |
| FIXED_MANAGEMENT | FIXED | M1.50 | loss_severity_bps | FIXED_STOP_M1.50 | 3 | 388 | 391 | 388 | 391 | 388 | -11.064 | -11.064 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 94 |
| FIXED_MANAGEMENT | FIXED | M1.50 | recovery_after_stop_bps | FIXED_STOP_M1.50 | 3 | 388 | 391 | 388 | 391 | 388 | 30.084 | 30.084 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 94 |
| FIXED_MANAGEMENT | FIXED | M1.50 | stop_rate | FIXED_STOP_M1.50 | 3 | 388 | 391 | 388 | 391 | 388 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 94 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | adverse_excursion_bps | FIXED_STOP_M1.00 | 3 | 280 | 358 | 355 | 282 | 280 | 11.973 | 11.910 | 0.000 | -0.022 | 0.063 | 0 | 0 | 0.058 | 61 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | loss_severity_bps | FIXED_STOP_M1.00 | 3 | 280 | 358 | 355 | 282 | 280 | -7.403 | -7.390 | 0.000 | -0.014 | 0.043 | 0 | 0 | 0.043 | 61 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 3 | 280 | 358 | 355 | 282 | 280 | 34.050 | 34.077 | -0.027 | -0.398 | 0.000 | 0 | 0 | 0.078 | 61 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | stop_rate | FIXED_STOP_M1.00 | 3 | 280 | 358 | 355 | 282 | 280 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 61 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | adverse_excursion_bps | FIXED_STOP_M1.00 | 3 | 404 | 448 | 445 | 407 | 404 | 11.889 | 11.239 | 0.000 | -0.022 | 0.650 | 1 | 0 | 0.058 | 92 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | loss_severity_bps | FIXED_STOP_M1.00 | 3 | 404 | 448 | 445 | 407 | 404 | -7.984 | -7.384 | 0.000 | -0.600 | 0.043 | 0 | 1 | 0.043 | 92 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 3 | 404 | 448 | 445 | 407 | 404 | 34.050 | 34.077 | 0.000 | -0.027 | 0.890 | 1 | 0 | 0.078 | 92 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | stop_rate | FIXED_STOP_M1.00 | 3 | 404 | 448 | 445 | 407 | 404 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 92 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | adverse_excursion_bps | FIXED_STOP_M1.00 | 3 | 247 | 413 | 410 | 249 | 247 | 11.508 | 10.284 | 1.224 | -1.628 | 1.911 | 2 | 0 | 1.316 | 63 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | loss_severity_bps | FIXED_STOP_M1.00 | 3 | 247 | 413 | 410 | 249 | 247 | -8.577 | -7.390 | -1.188 | -1.398 | -0.146 | 0 | 2 | 0.572 | 63 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 3 | 247 | 413 | 410 | 249 | 247 | 37.970 | 34.801 | 1.154 | 0.728 | 3.169 | 1 | 0 | 1.375 | 63 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | stop_rate | FIXED_STOP_M1.00 | 3 | 247 | 413 | 410 | 249 | 247 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 63 |
| MANAGEMENT | RANGE_SCALE | M0.75 | adverse_excursion_bps | FIXED_STOP_M0.75 | 3 | 146 | 364 | 361 | 148 | 146 | 11.229 | 8.413 | 2.817 | 0.098 | 8.306 | 2 | 0 | 2.335 | 38 |
| MANAGEMENT | RANGE_SCALE | M0.75 | loss_severity_bps | FIXED_STOP_M0.75 | 3 | 146 | 364 | 361 | 148 | 146 | -7.939 | -5.610 | -2.329 | -7.665 | -0.018 | 0 | 2 | 2.090 | 38 |
| MANAGEMENT | RANGE_SCALE | M0.75 | recovery_after_stop_bps | FIXED_STOP_M0.75 | 3 | 146 | 364 | 361 | 148 | 146 | 33.413 | 34.358 | -0.945 | -11.870 | -0.285 | 0 | 2 | 3.841 | 38 |
| MANAGEMENT | RANGE_SCALE | M0.75 | stop_rate | FIXED_STOP_M0.75 | 3 | 146 | 364 | 361 | 148 | 146 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 38 |
| MANAGEMENT | RANGE_SCALE | M1.00 | adverse_excursion_bps | FIXED_STOP_M1.00 | 3 | 156 | 563 | 560 | 157 | 156 | 15.041 | 11.310 | 1.649 | 1.445 | 6.897 | 3 | 0 | 1.539 | 38 |
| MANAGEMENT | RANGE_SCALE | M1.00 | loss_severity_bps | FIXED_STOP_M1.00 | 3 | 156 | 563 | 560 | 157 | 156 | -11.687 | -7.376 | -1.564 | -7.102 | -0.838 | 0 | 2 | 2.248 | 38 |
| MANAGEMENT | RANGE_SCALE | M1.00 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 3 | 156 | 563 | 560 | 157 | 156 | 22.192 | 24.557 | -2.365 | -12.679 | 0.143 | 0 | 0 | 5.511 | 38 |
| MANAGEMENT | RANGE_SCALE | M1.00 | stop_rate | FIXED_STOP_M1.00 | 3 | 156 | 563 | 560 | 157 | 156 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 38 |
| MANAGEMENT | RANGE_SCALE | M1.50 | adverse_excursion_bps | FIXED_STOP_M1.50 | 3 | 198 | 386 | 383 | 199 | 198 | 16.122 | 13.725 | 2.397 | 0.750 | 2.413 | 2 | 0 | 1.368 | 56 |
| MANAGEMENT | RANGE_SCALE | M1.50 | loss_severity_bps | FIXED_STOP_M1.50 | 3 | 198 | 386 | 383 | 199 | 198 | -13.382 | -11.064 | -2.319 | -2.742 | -0.962 | 0 | 3 | 1.351 | 56 |
| MANAGEMENT | RANGE_SCALE | M1.50 | recovery_after_stop_bps | FIXED_STOP_M1.50 | 3 | 198 | 386 | 383 | 199 | 198 | 26.650 | 28.227 | -1.577 | -7.008 | -0.661 | 0 | 0 | 6.606 | 56 |
| MANAGEMENT | RANGE_SCALE | M1.50 | stop_rate | FIXED_STOP_M1.50 | 3 | 198 | 386 | 383 | 199 | 198 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 56 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | adverse_excursion_bps | FIXED_STOP_M1.00 | 3 | 229 | 568 | 565 | 230 | 229 | 11.441 | 11.539 | 0.490 | -0.099 | 1.567 | 1 | 0 | 1.062 | 54 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | loss_severity_bps | FIXED_STOP_M1.00 | 3 | 229 | 568 | 565 | 230 | 229 | -8.138 | -7.391 | -0.747 | -0.841 | 0.225 | 0 | 1 | 0.599 | 54 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 3 | 229 | 568 | 565 | 230 | 229 | 24.750 | 25.519 | -0.768 | -1.007 | -0.458 | 0 | 1 | 2.525 | 54 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | stop_rate | FIXED_STOP_M1.00 | 3 | 229 | 568 | 565 | 230 | 229 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 54 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | adverse_excursion_bps | FIXED_STOP_M1.00 | 3 | 188 | 307 | 304 | 189 | 188 | 13.511 | 11.830 | 1.570 | -1.957 | 1.681 | 2 | 0 | 1.553 | 44 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | loss_severity_bps | FIXED_STOP_M1.00 | 3 | 188 | 307 | 304 | 189 | 188 | -9.577 | -7.396 | -0.966 | -2.181 | 0.372 | 0 | 1 | 0.933 | 44 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 3 | 188 | 307 | 304 | 189 | 188 | 37.730 | 34.801 | 2.512 | 0.471 | 2.929 | 1 | 0 | 2.546 | 44 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | stop_rate | FIXED_STOP_M1.00 | 3 | 188 | 307 | 304 | 189 | 188 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 44 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | adverse_excursion_bps | FIXED_STOP_M1.00 | 2 | 64 | 533 | 531 | 64 | 64 | 22.005 | 14.215 | 7.790 | 6.140 | 9.440 | 2 | 0 | 6.030 | 18 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | loss_severity_bps | FIXED_STOP_M1.00 | 2 | 64 | 533 | 531 | 64 | 64 | -17.275 | -10.070 | -7.205 | -10.009 | -4.402 | 0 | 2 | 4.202 | 18 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | recovery_after_stop_bps | FIXED_STOP_M1.00 | 2 | 64 | 533 | 531 | 64 | 64 | 46.065 | 54.327 | -8.262 | -13.055 | -3.469 | 0 | 0 | 24.486 | 18 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | stop_rate | FIXED_STOP_M1.00 | 2 | 64 | 533 | 531 | 64 | 64 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 18 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | adverse_excursion_bps | FIXED_STOP_M1.00 | 3 | 202 | 405 | 402 | 204 | 202 | 11.634 | 10.360 | 1.274 | -4.883 | 3.166 | 2 | 0 | 1.456 | 52 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | loss_severity_bps | FIXED_STOP_M1.00 | 3 | 202 | 405 | 402 | 204 | 202 | -8.627 | -7.390 | -1.237 | -2.418 | -0.437 | 0 | 2 | 0.796 | 52 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | recovery_after_stop_bps | FIXED_STOP_M1.00 | 3 | 202 | 405 | 402 | 204 | 202 | 41.289 | 37.327 | 2.329 | 1.212 | 5.402 | 1 | 0 | 2.270 | 52 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | stop_rate | FIXED_STOP_M1.00 | 3 | 202 | 405 | 402 | 204 | 202 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 52 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | adverse_excursion_bps | FIXED_TARGET_M1.00 | 4 | 964 | 26635 | 26635 | 968 | 964 | 9.841 | 54.490 | -44.640 | -57.331 | -31.967 | 0 | 4 | 31.936 | 218 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | stop_rate | FIXED_TARGET_M1.00 | 4 | 964 | 26635 | 26635 | 968 | 964 | 0.508 | 0.000 | 0.508 | 0.479 | 0.532 | 4 | 0 | 0.059 | 218 |
**ctrader / device_trail.parquet total_rows=1053**

**-- row census by arm_class x state --**

```text
arm_class                         state
FIXED_MANAGEMENT                  EVENT_UNDECIDED     27
                                  INCOMPLETE          54
                                  NO_EVENT            54
                                  NO_FEATURE          54
                                  ORDER_CREATED       54
MANAGEMENT                        EVENT_UNDECIDED     63
                                  INCOMPLETE         126
                                  NO_EVENT           126
                                  NO_FEATURE          72
                                  ORDER_CREATED      126
MANAGEMENT_COMPONENT_COMBINATION  EVENT_UNDECIDED     36
                                  INCOMPLETE          54
                                  NO_EVENT            72
                                  ORDER_CREATED       72
MANAGEMENT_DEVICE_COMBINATION     EVENT_UNDECIDED      9
                                  INCOMPLETE          18
                                  NO_EVENT            18
                                  ORDER_CREATED       18
```

**-- rows with a defined estimate: 198 of 1053**

**-- ctrader / E_TOUCH / trail : adaptive-minus-fixed by component x setting --**

| arm_class | component | setting | metric | comparator | sym_rows | episode_n | entry_fill_n | close_n | common_fill_n | common_close_n | obs med | comp med | est med | est min | est max | CI>0 | CI<0 | mde med | eff_trade_blocks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIXED_MANAGEMENT | FIXED | M0.75 | favourable_excursion_captured | FIXED_TRAIL_M0.75 | 3 | 887 | 890 | 887 | 890 | 887 | 0.310 | 0.310 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 127 |
| FIXED_MANAGEMENT | FIXED | M0.75 | loss_tail_bps | FIXED_TRAIL_M0.75 | 3 | 887 | 890 | 887 | 890 | 887 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 127 |
| FIXED_MANAGEMENT | FIXED | M0.75 | peak_giveback_bps | FIXED_TRAIL_M0.75 | 3 | 887 | 890 | 887 | 890 | 887 | 6.519 | 6.519 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 127 |
| FIXED_MANAGEMENT | FIXED | M1.00 | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 3 | 545 | 548 | 545 | 548 | 545 | 0.382 | 0.382 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 98 |
| FIXED_MANAGEMENT | FIXED | M1.00 | loss_tail_bps | FIXED_TRAIL_M1.00 | 3 | 545 | 548 | 545 | 548 | 545 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 98 |
| FIXED_MANAGEMENT | FIXED | M1.00 | peak_giveback_bps | FIXED_TRAIL_M1.00 | 3 | 545 | 548 | 545 | 548 | 545 | 8.090 | 8.090 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 98 |
| FIXED_MANAGEMENT | FIXED | M1.50 | favourable_excursion_captured | FIXED_TRAIL_M1.50 | 3 | 544 | 547 | 544 | 547 | 544 | 0.380 | 0.380 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 121 |
| FIXED_MANAGEMENT | FIXED | M1.50 | loss_tail_bps | FIXED_TRAIL_M1.50 | 3 | 544 | 547 | 544 | 547 | 544 | 0.049 | 0.049 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 121 |
| FIXED_MANAGEMENT | FIXED | M1.50 | peak_giveback_bps | FIXED_TRAIL_M1.50 | 3 | 544 | 547 | 544 | 547 | 544 | 11.472 | 11.472 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 121 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 3 | 463 | 506 | 503 | 465 | 463 | 0.374 | 0.388 | -0.014 | -0.016 | 0.000 | 0 | 1 | 0.020 | 88 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | loss_tail_bps | FIXED_TRAIL_M1.00 | 3 | 463 | 506 | 503 | 465 | 463 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.111 | 88 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | peak_giveback_bps | FIXED_TRAIL_M1.00 | 3 | 463 | 506 | 503 | 465 | 463 | 8.315 | 8.070 | 0.000 | -0.149 | 0.245 | 0 | 0 | 0.288 | 88 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 3 | 478 | 520 | 517 | 480 | 478 | 0.368 | 0.380 | -0.012 | -0.016 | 0.000 | 0 | 1 | 0.022 | 88 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | loss_tail_bps | FIXED_TRAIL_M1.00 | 3 | 478 | 520 | 517 | 480 | 478 | 0.000 | 0.000 | 0.000 | -0.000 | 0.000 | 0 | 0 | 0.116 | 88 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | peak_giveback_bps | FIXED_TRAIL_M1.00 | 3 | 478 | 520 | 517 | 480 | 478 | 8.466 | 8.139 | 0.000 | -0.149 | 0.327 | 1 | 0 | 0.312 | 88 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 3 | 389 | 540 | 537 | 391 | 389 | 0.346 | 0.384 | -0.031 | -0.038 | 0.000 | 0 | 1 | 0.051 | 81 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | loss_tail_bps | FIXED_TRAIL_M1.00 | 3 | 389 | 540 | 537 | 391 | 389 | 0.000 | 0.000 | 0.000 | -0.000 | 0.000 | 0 | 0 | 0.165 | 81 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | peak_giveback_bps | FIXED_TRAIL_M1.00 | 3 | 389 | 540 | 537 | 391 | 389 | 8.634 | 8.143 | 0.067 | 0.000 | 0.491 | 0 | 0 | 0.753 | 81 |
| MANAGEMENT | RANGE_SCALE | M0.75 | favourable_excursion_captured | FIXED_TRAIL_M0.75 | 3 | 195 | 459 | 456 | 197 | 195 | 0.373 | 0.246 | 0.045 | 0.044 | 0.261 | 2 | 0 | 0.082 | 39 |
| MANAGEMENT | RANGE_SCALE | M0.75 | loss_tail_bps | FIXED_TRAIL_M0.75 | 3 | 195 | 459 | 456 | 197 | 195 | 0.123 | 0.000 | 0.102 | 0.000 | 0.988 | 2 | 0 | 0.332 | 39 |
| MANAGEMENT | RANGE_SCALE | M0.75 | peak_giveback_bps | FIXED_TRAIL_M0.75 | 3 | 195 | 459 | 456 | 197 | 195 | 7.087 | 6.318 | 0.769 | -0.150 | 6.953 | 1 | 1 | 2.699 | 39 |
| MANAGEMENT | RANGE_SCALE | M1.00 | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 3 | 156 | 367 | 364 | 157 | 156 | 0.404 | 0.379 | 0.048 | 0.024 | 0.094 | 1 | 0 | 0.086 | 32 |
| MANAGEMENT | RANGE_SCALE | M1.00 | loss_tail_bps | FIXED_TRAIL_M1.00 | 3 | 156 | 367 | 364 | 157 | 156 | 0.085 | 0.000 | 0.085 | 0.012 | 0.327 | 1 | 0 | 0.100 | 32 |
| MANAGEMENT | RANGE_SCALE | M1.00 | peak_giveback_bps | FIXED_TRAIL_M1.00 | 3 | 156 | 367 | 364 | 157 | 156 | 10.979 | 8.277 | 2.702 | -0.327 | 9.588 | 2 | 1 | 3.179 | 32 |
| MANAGEMENT | RANGE_SCALE | M1.50 | favourable_excursion_captured | FIXED_TRAIL_M1.50 | 3 | 169 | 341 | 338 | 171 | 169 | 0.392 | 0.365 | 0.007 | 0.000 | 0.060 | 0 | 0 | 0.065 | 53 |
| MANAGEMENT | RANGE_SCALE | M1.50 | loss_tail_bps | FIXED_TRAIL_M1.50 | 3 | 169 | 341 | 338 | 171 | 169 | 0.300 | 0.008 | 0.156 | -0.461 | 0.771 | 0 | 0 | 0.652 | 53 |
| MANAGEMENT | RANGE_SCALE | M1.50 | peak_giveback_bps | FIXED_TRAIL_M1.50 | 3 | 169 | 341 | 338 | 171 | 169 | 13.457 | 11.450 | 2.007 | -0.167 | 13.020 | 2 | 0 | 1.377 | 53 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 3 | 354 | 696 | 693 | 356 | 354 | 0.336 | 0.398 | -0.036 | -0.062 | 0.000 | 0 | 1 | 0.055 | 74 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | loss_tail_bps | FIXED_TRAIL_M1.00 | 3 | 354 | 696 | 693 | 356 | 354 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.263 | 74 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | peak_giveback_bps | FIXED_TRAIL_M1.00 | 3 | 354 | 696 | 693 | 356 | 354 | 8.602 | 8.069 | 0.000 | -0.372 | 0.533 | 1 | 0 | 0.625 | 74 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 2 | 282 | 503 | 501 | 282 | 282 | 0.340 | 0.387 | -0.047 | -0.058 | -0.037 | 0 | 1 | 0.039 | 65 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | loss_tail_bps | FIXED_TRAIL_M1.00 | 2 | 282 | 503 | 501 | 282 | 282 | 0.022 | 0.346 | -0.324 | -0.367 | -0.281 | 0 | 1 | 0.581 | 65 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | peak_giveback_bps | FIXED_TRAIL_M1.00 | 2 | 282 | 503 | 501 | 282 | 282 | 10.043 | 8.000 | 2.043 | 1.822 | 2.264 | 2 | 0 | 1.349 | 65 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 2 | 341 | 656 | 654 | 342 | 341 | 0.330 | 0.376 | -0.046 | -0.052 | -0.039 | 0 | 1 | 0.061 | 69 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | loss_tail_bps | FIXED_TRAIL_M1.00 | 2 | 341 | 656 | 654 | 342 | 341 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.160 | 69 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | peak_giveback_bps | FIXED_TRAIL_M1.00 | 2 | 341 | 656 | 654 | 342 | 341 | 9.527 | 9.513 | 0.013 | -0.487 | 0.513 | 0 | 0 | 0.806 | 69 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 3 | 404 | 16357 | 16357 | 406 | 404 | -2.820 | 0.382 | -3.202 | -6.701 | 0.048 | 1 | 2 | 6.279 | 94 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | loss_tail_bps | FIXED_TRAIL_M1.00 | 3 | 404 | 16357 | 16357 | 406 | 404 | -37.488 | 0.000 | -37.488 | -152.345 | 0.327 | 1 | 2 | 42.798 | 94 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | peak_giveback_bps | FIXED_TRAIL_M1.00 | 3 | 404 | 16357 | 16357 | 406 | 404 | 13.651 | 8.083 | 5.569 | -0.327 | 27.259 | 2 | 1 | 5.001 | 94 |
**-- ctrader / E_CLOSE / trail : adaptive-minus-fixed by component x setting --**

| arm_class | component | setting | metric | comparator | sym_rows | episode_n | entry_fill_n | close_n | common_fill_n | common_close_n | obs med | comp med | est med | est min | est max | CI>0 | CI<0 | mde med | eff_trade_blocks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIXED_MANAGEMENT | FIXED | M0.75 | favourable_excursion_captured | FIXED_TRAIL_M0.75 | 3 | 753 | 756 | 753 | 756 | 753 | 0.321 | 0.321 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 129 |
| FIXED_MANAGEMENT | FIXED | M0.75 | loss_tail_bps | FIXED_TRAIL_M0.75 | 3 | 753 | 756 | 753 | 756 | 753 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 129 |
| FIXED_MANAGEMENT | FIXED | M0.75 | peak_giveback_bps | FIXED_TRAIL_M0.75 | 3 | 753 | 756 | 753 | 756 | 753 | 6.647 | 6.647 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 129 |
| FIXED_MANAGEMENT | FIXED | M1.00 | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 2 | 549 | 551 | 549 | 551 | 549 | 0.377 | 0.377 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 115 |
| FIXED_MANAGEMENT | FIXED | M1.00 | loss_tail_bps | FIXED_TRAIL_M1.00 | 2 | 549 | 551 | 549 | 551 | 549 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 115 |
| FIXED_MANAGEMENT | FIXED | M1.00 | peak_giveback_bps | FIXED_TRAIL_M1.00 | 2 | 549 | 551 | 549 | 551 | 549 | 8.479 | 8.479 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 115 |
| FIXED_MANAGEMENT | FIXED | M1.50 | favourable_excursion_captured | FIXED_TRAIL_M1.50 | 2 | 395 | 397 | 395 | 397 | 395 | 0.412 | 0.412 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 114 |
| FIXED_MANAGEMENT | FIXED | M1.50 | loss_tail_bps | FIXED_TRAIL_M1.50 | 2 | 395 | 397 | 395 | 397 | 395 | 0.193 | 0.193 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 114 |
| FIXED_MANAGEMENT | FIXED | M1.50 | peak_giveback_bps | FIXED_TRAIL_M1.50 | 2 | 395 | 397 | 395 | 397 | 395 | 12.013 | 12.013 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 114 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 2 | 439 | 564 | 562 | 439 | 439 | 0.378 | 0.381 | -0.003 | -0.004 | -0.002 | 0 | 0 | 0.025 | 91 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | loss_tail_bps | FIXED_TRAIL_M1.00 | 2 | 439 | 564 | 562 | 439 | 439 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.085 | 91 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | peak_giveback_bps | FIXED_TRAIL_M1.00 | 2 | 439 | 564 | 562 | 439 | 439 | 9.028 | 8.655 | 0.372 | -0.026 | 0.771 | 1 | 0 | 0.322 | 91 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 2 | 387 | 537 | 535 | 387 | 387 | 0.378 | 0.379 | -0.001 | -0.002 | -0.000 | 0 | 0 | 0.017 | 80 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | loss_tail_bps | FIXED_TRAIL_M1.00 | 2 | 387 | 537 | 535 | 387 | 387 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.037 | 80 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | peak_giveback_bps | FIXED_TRAIL_M1.00 | 2 | 387 | 537 | 535 | 387 | 387 | 9.120 | 8.731 | 0.390 | 0.065 | 0.714 | 1 | 0 | 0.262 | 80 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 2 | 306 | 551 | 549 | 306 | 306 | 0.346 | 0.366 | -0.020 | -0.032 | -0.007 | 0 | 0 | 0.047 | 74 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | loss_tail_bps | FIXED_TRAIL_M1.00 | 2 | 306 | 551 | 549 | 306 | 306 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.064 | 74 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | peak_giveback_bps | FIXED_TRAIL_M1.00 | 2 | 306 | 551 | 549 | 306 | 306 | 9.880 | 8.818 | 1.062 | 0.758 | 1.366 | 1 | 0 | 0.736 | 74 |
| MANAGEMENT | RANGE_SCALE | M0.75 | favourable_excursion_captured | FIXED_TRAIL_M0.75 | 3 | 318 | 520 | 517 | 319 | 318 | 0.378 | 0.308 | 0.070 | -0.087 | 0.163 | 2 | 0 | 0.055 | 76 |
| MANAGEMENT | RANGE_SCALE | M0.75 | loss_tail_bps | FIXED_TRAIL_M0.75 | 3 | 318 | 520 | 517 | 319 | 318 | 0.090 | 0.000 | 0.000 | -0.016 | 0.455 | 1 | 0 | 0.210 | 76 |
| MANAGEMENT | RANGE_SCALE | M0.75 | peak_giveback_bps | FIXED_TRAIL_M0.75 | 3 | 318 | 520 | 517 | 319 | 318 | 8.448 | 7.002 | 1.446 | -0.025 | 3.184 | 2 | 0 | 0.816 | 76 |
| MANAGEMENT | RANGE_SCALE | M1.00 | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 2 | 158 | 386 | 384 | 158 | 158 | 0.407 | 0.367 | 0.040 | 0.033 | 0.048 | 0 | 0 | 0.058 | 44 |
| MANAGEMENT | RANGE_SCALE | M1.00 | loss_tail_bps | FIXED_TRAIL_M1.00 | 2 | 158 | 386 | 384 | 158 | 158 | 0.347 | 0.000 | 0.347 | 0.063 | 0.631 | 0 | 0 | 0.347 | 44 |
| MANAGEMENT | RANGE_SCALE | M1.00 | peak_giveback_bps | FIXED_TRAIL_M1.00 | 2 | 158 | 386 | 384 | 158 | 158 | 15.108 | 9.524 | 5.584 | 2.245 | 8.924 | 2 | 0 | 2.206 | 44 |
| MANAGEMENT | RANGE_SCALE | M1.50 | favourable_excursion_captured | FIXED_TRAIL_M1.50 | 2 | 97 | 263 | 261 | 98 | 97 | 0.443 | 0.408 | 0.036 | 0.003 | 0.068 | 0 | 0 | 0.085 | 37 |
| MANAGEMENT | RANGE_SCALE | M1.50 | loss_tail_bps | FIXED_TRAIL_M1.50 | 2 | 97 | 263 | 261 | 98 | 97 | 2.848 | 0.360 | 2.488 | 0.653 | 4.322 | 1 | 0 | 3.248 | 37 |
| MANAGEMENT | RANGE_SCALE | M1.50 | peak_giveback_bps | FIXED_TRAIL_M1.50 | 2 | 97 | 263 | 261 | 98 | 97 | 20.332 | 12.097 | 8.235 | 2.574 | 13.896 | 2 | 0 | 5.082 | 37 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 2 | 368 | 761 | 759 | 369 | 368 | 0.328 | 0.374 | -0.046 | -0.056 | -0.036 | 0 | 1 | 0.038 | 81 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | loss_tail_bps | FIXED_TRAIL_M1.00 | 2 | 368 | 761 | 759 | 369 | 368 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.119 | 81 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | peak_giveback_bps | FIXED_TRAIL_M1.00 | 2 | 368 | 761 | 759 | 369 | 368 | 8.890 | 8.642 | 0.248 | 0.102 | 0.395 | 0 | 0 | 0.506 | 81 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 3 | 157 | 723 | 720 | 157 | 157 | 0.401 | 0.408 | 0.011 | -0.010 | 0.034 | 0 | 0 | 0.058 | 40 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | loss_tail_bps | FIXED_TRAIL_M1.00 | 3 | 157 | 723 | 720 | 157 | 157 | 0.080 | 0.171 | -0.091 | -0.848 | 0.544 | 0 | 0 | 0.467 | 40 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | peak_giveback_bps | FIXED_TRAIL_M1.00 | 3 | 157 | 723 | 720 | 157 | 157 | 12.115 | 7.928 | 3.580 | 3.431 | 4.563 | 3 | 0 | 1.797 | 40 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 2 | 181 | 714 | 712 | 181 | 181 | 0.344 | 0.365 | -0.020 | -0.035 | -0.006 | 0 | 0 | 0.068 | 46 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | loss_tail_bps | FIXED_TRAIL_M1.00 | 2 | 181 | 714 | 712 | 181 | 181 | 0.000 | 0.095 | -0.095 | -0.190 | 0.000 | 0 | 1 | 0.599 | 46 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | peak_giveback_bps | FIXED_TRAIL_M1.00 | 2 | 181 | 714 | 712 | 181 | 181 | 9.510 | 8.237 | 1.273 | 0.816 | 1.729 | 1 | 0 | 0.945 | 46 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 2 | 447 | 8651 | 8651 | 449 | 447 | -2.656 | 0.386 | -3.042 | -3.682 | -2.403 | 0 | 2 | 2.789 | 107 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | loss_tail_bps | FIXED_TRAIL_M1.00 | 2 | 447 | 8651 | 8651 | 449 | 447 | -70.396 | 0.000 | -70.396 | -98.522 | -42.270 | 0 | 2 | 37.420 | 107 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | peak_giveback_bps | FIXED_TRAIL_M1.00 | 2 | 447 | 8651 | 8651 | 449 | 447 | 19.556 | 8.340 | 11.216 | 6.610 | 15.821 | 2 | 0 | 3.128 | 107 |
**ctrader / device_hold.parquet total_rows=1284**

**-- row census by arm_class x state --**

```text
arm_class                         state
FIXED_MANAGEMENT                  EVENT_UNDECIDED     36
                                  INCOMPLETE          72
                                  NO_EVENT            72
                                  NO_FEATURE          72
                                  ORDER_CREATED       72
MANAGEMENT                        EVENT_UNDECIDED     60
                                  INCOMPLETE          96
                                  NO_EVENT           120
                                  ORDER_CREATED      120
MANAGEMENT_COMPONENT_COMBINATION  EVENT_UNDECIDED     60
                                  INCOMPLETE          96
                                  NO_EVENT           120
                                  ORDER_CREATED      120
MANAGEMENT_DEVICE_COMBINATION     EVENT_UNDECIDED     24
                                  INCOMPLETE          48
                                  NO_EVENT            48
                                  ORDER_CREATED       48
```

**-- rows with a defined estimate: 282 of 1284**

**-- ctrader / E_TOUCH / hold : adaptive-minus-fixed by component x setting --**

| arm_class | component | setting | metric | comparator | sym_rows | episode_n | entry_fill_n | close_n | common_fill_n | common_close_n | obs med | comp med | est med | est min | est max | CI>0 | CI<0 | mde med | eff_trade_blocks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIXED_MANAGEMENT | FIXED | B12 | decay_bps | FIXED_HOLD_B12 | 3 | 3486 | 3487 | 3486 | 3487 | 3486 | 44.355 | 44.355 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1942 |
| FIXED_MANAGEMENT | FIXED | B12 | holding_efficiency | FIXED_HOLD_B12 | 1 | 1153 | 1153 | 1153 | 1153 | 1153 | -4.906 | -4.906 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 641 |
| FIXED_MANAGEMENT | FIXED | B12 | opportunity_duration | FIXED_HOLD_B12 | 3 | 3486 | 3487 | 3486 | 3487 | 3486 | 5.553 | 5.553 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1942 |
| FIXED_MANAGEMENT | FIXED | B12 | outcome_by_time_bps | FIXED_HOLD_B12 | 3 | 3486 | 3487 | 3486 | 3487 | 3486 | -1.218 | -1.218 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1942 |
| FIXED_MANAGEMENT | FIXED | B2 | decay_bps | FIXED_HOLD_B2 | 3 | 13170 | 13170 | 13170 | 13170 | 13170 | 17.407 | 17.407 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 2000 |
| FIXED_MANAGEMENT | FIXED | B2 | opportunity_duration | FIXED_HOLD_B2 | 3 | 13170 | 13170 | 13170 | 13170 | 13170 | 0.920 | 0.920 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 2000 |
| FIXED_MANAGEMENT | FIXED | B2 | outcome_by_time_bps | FIXED_HOLD_B2 | 3 | 13170 | 13170 | 13170 | 13170 | 13170 | -0.086 | -0.086 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 2000 |
| FIXED_MANAGEMENT | FIXED | B4 | decay_bps | FIXED_HOLD_B4 | 3 | 8496 | 8496 | 8496 | 8496 | 8496 | 24.489 | 24.489 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1952 |
| FIXED_MANAGEMENT | FIXED | B4 | opportunity_duration | FIXED_HOLD_B4 | 3 | 8496 | 8496 | 8496 | 8496 | 8496 | 1.772 | 1.772 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1952 |
| FIXED_MANAGEMENT | FIXED | B4 | outcome_by_time_bps | FIXED_HOLD_B4 | 3 | 8496 | 8496 | 8496 | 8496 | 8496 | 0.385 | 0.385 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1952 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_4_HIGH_12 | decay_bps | FIXED_HOLD_B4 | 3 | 1955 | 3303 | 3303 | 1955 | 1955 | 29.921 | 24.791 | 5.510 | 5.130 | 13.610 | 3 | 0 | 1.444 | 865 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_4_HIGH_12 | holding_efficiency | FIXED_HOLD_B4 | 1 | 726 | 1178 | 1178 | 726 | 726 | -4.755 | -3.988 | -0.767 | -0.767 | -0.767 | 0 | 1 | 0.918 | 300 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_4_HIGH_12 | opportunity_duration | FIXED_HOLD_B4 | 3 | 1955 | 3303 | 3303 | 1955 | 1955 | 3.300 | 1.796 | 1.431 | 1.085 | 1.768 | 3 | 0 | 0.224 | 865 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_4_HIGH_12 | outcome_by_time_bps | FIXED_HOLD_B4 | 3 | 1955 | 3303 | 3303 | 1955 | 1955 | -0.929 | -0.182 | -0.747 | -0.778 | -0.188 | 0 | 0 | 1.629 | 865 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_4_HIGH_12 | decay_bps | FIXED_HOLD_B4 | 3 | 1994 | 3302 | 3302 | 1994 | 1994 | 29.249 | 24.325 | 4.924 | 4.473 | 12.464 | 3 | 0 | 1.376 | 883 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_4_HIGH_12 | opportunity_duration | FIXED_HOLD_B4 | 3 | 1994 | 3302 | 3302 | 1994 | 1994 | 3.409 | 1.784 | 1.490 | 1.407 | 1.762 | 3 | 0 | 0.237 | 883 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_4_HIGH_12 | outcome_by_time_bps | FIXED_HOLD_B4 | 3 | 1994 | 3302 | 3302 | 1994 | 1994 | 0.454 | -1.319 | 0.801 | 0.185 | 1.774 | 1 | 0 | 1.737 | 883 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_4_HIGH_12 | decay_bps | FIXED_HOLD_B4 | 3 | 3432 | 5556 | 5556 | 3432 | 3432 | 30.213 | 24.545 | 5.667 | 4.092 | 10.982 | 3 | 0 | 1.218 | 1488 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_4_HIGH_12 | opportunity_duration | FIXED_HOLD_B4 | 3 | 3432 | 5556 | 5556 | 3432 | 3432 | 3.238 | 1.791 | 1.451 | 1.398 | 1.483 | 3 | 0 | 0.191 | 1488 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_4_HIGH_12 | outcome_by_time_bps | FIXED_HOLD_B4 | 3 | 3432 | 5556 | 5556 | 3432 | 3432 | 0.112 | -1.158 | 0.336 | -0.312 | 1.269 | 0 | 0 | 1.553 | 1488 |
| MANAGEMENT | SHOCK | STATE_SHOCK_2 | decay_bps | FIXED_HOLD_B4 | 3 | 4398 | 13148 | 13148 | 4398 | 4398 | 16.454 | 23.437 | -6.983 | -9.464 | -3.513 | 0 | 3 | 1.020 | 1933 |
| MANAGEMENT | SHOCK | STATE_SHOCK_2 | opportunity_duration | FIXED_HOLD_B4 | 3 | 4398 | 13148 | 13148 | 4398 | 4398 | 0.893 | 1.849 | -0.923 | -0.986 | -0.891 | 0 | 3 | 0.062 | 1933 |
| MANAGEMENT | SHOCK | STATE_SHOCK_2 | outcome_by_time_bps | FIXED_HOLD_B4 | 3 | 4398 | 13148 | 13148 | 4398 | 4398 | -0.119 | -0.249 | 0.234 | -0.549 | 0.570 | 0 | 0 | 1.149 | 1933 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_4_HIGH_12 | decay_bps | FIXED_HOLD_B4 | 3 | 3921 | 5592 | 5592 | 3921 | 3921 | 30.786 | 25.052 | 5.734 | 2.278 | 9.342 | 3 | 0 | 1.253 | 1491 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_4_HIGH_12 | opportunity_duration | FIXED_HOLD_B4 | 3 | 3921 | 5592 | 5592 | 3921 | 3921 | 2.695 | 1.826 | 0.915 | 0.712 | 1.180 | 3 | 0 | 0.140 | 1491 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_4_HIGH_12 | outcome_by_time_bps | FIXED_HOLD_B4 | 3 | 3921 | 5592 | 5592 | 3921 | 3921 | 0.638 | 0.638 | -0.508 | -1.007 | -0.000 | 0 | 0 | 1.334 | 1491 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_4_HIGH_12 | decay_bps | FIXED_HOLD_B4 | 12 | 11302 | 17753 | 17753 | 11302 | 11302 | 30.067 | 24.668 | 5.589 | 2.278 | 13.610 | 12 | 0 | 1.328 | 4727 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_4_HIGH_12 | holding_efficiency | FIXED_HOLD_B4 | 1 | 726 | 1178 | 1178 | 726 | 726 | -4.755 | -3.988 | -0.767 | -0.767 | -0.767 | 0 | 1 | 0.918 | 300 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_4_HIGH_12 | opportunity_duration | FIXED_HOLD_B4 | 12 | 11302 | 17753 | 17753 | 11302 | 11302 | 3.214 | 1.794 | 1.419 | 0.712 | 1.768 | 12 | 0 | 0.192 | 4727 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_4_HIGH_12 | outcome_by_time_bps | FIXED_HOLD_B4 | 12 | 11302 | 17753 | 17753 | 11302 | 11302 | 0.153 | -0.670 | -0.094 | -1.007 | 1.774 | 1 | 0 | 1.591 | 4727 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_4_HIGH_12 | decay_bps | FIXED_HOLD_B4 | 3 | 3550 | 6584 | 6584 | 3550 | 3550 | 28.521 | 24.085 | 4.437 | 2.528 | 6.445 | 3 | 0 | 1.239 | 1595 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_4_HIGH_12 | opportunity_duration | FIXED_HOLD_B4 | 3 | 3550 | 6584 | 6584 | 3550 | 3550 | 2.809 | 1.794 | 0.993 | 0.983 | 1.015 | 3 | 0 | 0.173 | 1595 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_4_HIGH_12 | outcome_by_time_bps | FIXED_HOLD_B4 | 3 | 3550 | 6584 | 6584 | 3550 | 3550 | -0.391 | -0.464 | 0.074 | -0.124 | 0.415 | 0 | 0 | 1.544 | 1595 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | decay_bps | FIXED_TARGET_M1.00 | 3 | 561 | 28858 | 28858 | 564 | 561 | 8.773 | 3.825 | 4.948 | -0.000 | 8.720 | 2 | 1 | 2.148 | 102 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | decay_bps | FIXED_TRAIL_M1.00 | 3 | 404 | 16357 | 16357 | 406 | 404 | 13.651 | 8.083 | 5.569 | -0.327 | 27.259 | 2 | 1 | 5.001 | 94 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | holding_efficiency | FIXED_TARGET_M1.00 | 2 | 164 | 19216 | 19216 | 166 | 164 | -0.341 | 0.782 | -1.124 | -2.239 | -0.008 | 0 | 2 | 1.162 | 34 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | holding_efficiency | FIXED_TRAIL_M1.00 | 3 | 404 | 16357 | 16357 | 406 | 404 | -2.820 | 0.382 | -3.202 | -6.701 | 0.048 | 1 | 2 | 6.279 | 94 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | opportunity_duration | FIXED_TARGET_M1.00 | 3 | 561 | 28858 | 28858 | 564 | 561 | 0.214 | 32.936 | -32.732 | -42.975 | -0.017 | 0 | 3 | 57.219 | 102 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | opportunity_duration | FIXED_TRAIL_M1.00 | 3 | 404 | 16357 | 16357 | 406 | 404 | 0.786 | 35.717 | -34.931 | -65.500 | 0.000 | 0 | 2 | 75.403 | 94 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | outcome_by_time_bps | FIXED_TARGET_M1.00 | 3 | 561 | 28858 | 28858 | 564 | 561 | 1.800 | 7.376 | -5.576 | -8.082 | -0.327 | 0 | 3 | 1.815 | 102 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | outcome_by_time_bps | FIXED_TRAIL_M1.00 | 3 | 404 | 16357 | 16357 | 406 | 404 | 1.676 | 7.184 | -5.508 | -13.027 | 0.327 | 1 | 2 | 9.823 | 94 |
**-- ctrader / E_CLOSE / hold : adaptive-minus-fixed by component x setting --**

| arm_class | component | setting | metric | comparator | sym_rows | episode_n | entry_fill_n | close_n | common_fill_n | common_close_n | obs med | comp med | est med | est min | est max | CI>0 | CI<0 | mde med | eff_trade_blocks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIXED_MANAGEMENT | FIXED | B12 | decay_bps | FIXED_HOLD_B12 | 3 | 3388 | 3389 | 3388 | 3389 | 3388 | 44.413 | 44.413 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1955 |
| FIXED_MANAGEMENT | FIXED | B12 | holding_efficiency | FIXED_HOLD_B12 | 2 | 2244 | 2244 | 2244 | 2244 | 2244 | -4.071 | -4.071 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1292 |
| FIXED_MANAGEMENT | FIXED | B12 | opportunity_duration | FIXED_HOLD_B12 | 3 | 3388 | 3389 | 3388 | 3389 | 3388 | 5.484 | 5.484 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1955 |
| FIXED_MANAGEMENT | FIXED | B12 | outcome_by_time_bps | FIXED_HOLD_B12 | 3 | 3388 | 3389 | 3388 | 3389 | 3388 | 0.485 | 0.485 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1955 |
| FIXED_MANAGEMENT | FIXED | B2 | decay_bps | FIXED_HOLD_B2 | 3 | 11085 | 11085 | 11085 | 11085 | 11085 | 17.417 | 17.417 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 2025 |
| FIXED_MANAGEMENT | FIXED | B2 | opportunity_duration | FIXED_HOLD_B2 | 3 | 11085 | 11085 | 11085 | 11085 | 11085 | 0.905 | 0.905 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 2025 |
| FIXED_MANAGEMENT | FIXED | B2 | outcome_by_time_bps | FIXED_HOLD_B2 | 3 | 11085 | 11085 | 11085 | 11085 | 11085 | 0.117 | 0.117 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 2025 |
| FIXED_MANAGEMENT | FIXED | B4 | decay_bps | FIXED_HOLD_B4 | 3 | 7537 | 7537 | 7537 | 7537 | 7537 | 23.986 | 23.986 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1979 |
| FIXED_MANAGEMENT | FIXED | B4 | opportunity_duration | FIXED_HOLD_B4 | 3 | 7537 | 7537 | 7537 | 7537 | 7537 | 1.805 | 1.805 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1979 |
| FIXED_MANAGEMENT | FIXED | B4 | outcome_by_time_bps | FIXED_HOLD_B4 | 3 | 7537 | 7537 | 7537 | 7537 | 7537 | 0.312 | 0.312 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1979 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_4_HIGH_12 | decay_bps | FIXED_HOLD_B4 | 3 | 2209 | 2996 | 2995 | 2210 | 2209 | 28.453 | 23.691 | 4.762 | 4.557 | 16.045 | 3 | 0 | 1.234 | 1003 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_4_HIGH_12 | opportunity_duration | FIXED_HOLD_B4 | 3 | 2209 | 2996 | 2995 | 2210 | 2209 | 3.499 | 1.875 | 1.624 | 1.328 | 1.925 | 3 | 0 | 0.235 | 1003 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_4_HIGH_12 | outcome_by_time_bps | FIXED_HOLD_B4 | 3 | 2209 | 2996 | 2995 | 2210 | 2209 | 2.590 | 0.729 | 2.003 | -2.943 | 2.520 | 2 | 0 | 1.784 | 1003 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_4_HIGH_12 | decay_bps | FIXED_HOLD_B4 | 3 | 2254 | 3020 | 3020 | 2254 | 2254 | 29.397 | 22.368 | 7.030 | 4.175 | 15.040 | 3 | 0 | 1.653 | 1034 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_4_HIGH_12 | holding_efficiency | FIXED_HOLD_B4 | 1 | 770 | 1015 | 1015 | 770 | 770 | -2.406 | -2.242 | -0.164 | -0.164 | -0.164 | 0 | 0 | 0.400 | 353 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_4_HIGH_12 | opportunity_duration | FIXED_HOLD_B4 | 3 | 2254 | 3020 | 3020 | 2254 | 2254 | 3.470 | 1.846 | 1.624 | 1.516 | 1.763 | 3 | 0 | 0.226 | 1034 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_4_HIGH_12 | outcome_by_time_bps | FIXED_HOLD_B4 | 3 | 2254 | 3020 | 3020 | 2254 | 2254 | 2.564 | 0.607 | 1.957 | -1.514 | 2.267 | 2 | 0 | 2.117 | 1034 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_4_HIGH_12 | decay_bps | FIXED_HOLD_B4 | 3 | 3833 | 5082 | 5082 | 3833 | 3833 | 29.348 | 23.109 | 6.239 | 4.141 | 11.706 | 3 | 0 | 1.186 | 1711 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_4_HIGH_12 | opportunity_duration | FIXED_HOLD_B4 | 3 | 3833 | 5082 | 5082 | 3833 | 3833 | 3.359 | 1.854 | 1.476 | 1.466 | 1.737 | 3 | 0 | 0.183 | 1711 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_4_HIGH_12 | outcome_by_time_bps | FIXED_HOLD_B4 | 3 | 3833 | 5082 | 5082 | 3833 | 3833 | 2.506 | 1.588 | 1.176 | 0.918 | 1.948 | 2 | 0 | 1.570 | 1711 |
| MANAGEMENT | SHOCK | STATE_SHOCK_2 | decay_bps | FIXED_HOLD_B4 | 3 | 5047 | 11069 | 11069 | 5047 | 5047 | 16.289 | 22.723 | -6.435 | -11.052 | -3.590 | 0 | 3 | 0.867 | 1952 |
| MANAGEMENT | SHOCK | STATE_SHOCK_2 | opportunity_duration | FIXED_HOLD_B4 | 3 | 5047 | 11069 | 11069 | 5047 | 5047 | 0.884 | 1.819 | -0.940 | -0.963 | -0.935 | 0 | 3 | 0.059 | 1952 |
| MANAGEMENT | SHOCK | STATE_SHOCK_2 | outcome_by_time_bps | FIXED_HOLD_B4 | 3 | 5047 | 11069 | 11069 | 5047 | 5047 | 0.144 | 0.391 | -0.236 | -0.894 | 0.114 | 0 | 0 | 1.070 | 1952 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_4_HIGH_12 | decay_bps | FIXED_HOLD_B4 | 3 | 4106 | 5131 | 5130 | 4107 | 4106 | 30.344 | 23.628 | 6.716 | 2.821 | 11.479 | 3 | 0 | 1.334 | 1674 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_4_HIGH_12 | holding_efficiency | FIXED_HOLD_B4 | 1 | 1292 | 1656 | 1656 | 1292 | 1292 | -2.999 | -2.890 | -0.109 | -0.109 | -0.109 | 0 | 0 | 0.323 | 549 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_4_HIGH_12 | opportunity_duration | FIXED_HOLD_B4 | 3 | 4106 | 5131 | 5130 | 4107 | 4106 | 2.991 | 1.811 | 1.158 | 0.822 | 1.180 | 3 | 0 | 0.166 | 1674 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_4_HIGH_12 | outcome_by_time_bps | FIXED_HOLD_B4 | 3 | 4106 | 5131 | 5130 | 4107 | 4106 | 0.520 | 0.659 | -0.345 | -1.657 | -0.139 | 0 | 0 | 1.544 | 1674 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_4_HIGH_12 | decay_bps | FIXED_HOLD_B4 | 12 | 12402 | 16229 | 16227 | 12404 | 12402 | 29.373 | 23.369 | 6.478 | 2.821 | 16.045 | 12 | 0 | 1.284 | 5422 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_4_HIGH_12 | holding_efficiency | FIXED_HOLD_B4 | 2 | 2062 | 2671 | 2671 | 2062 | 2062 | -2.703 | -2.566 | -0.137 | -0.164 | -0.109 | 0 | 0 | 0.362 | 902 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_4_HIGH_12 | opportunity_duration | FIXED_HOLD_B4 | 12 | 12402 | 16229 | 16227 | 12404 | 12402 | 3.387 | 1.850 | 1.496 | 0.822 | 1.925 | 12 | 0 | 0.202 | 5422 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_4_HIGH_12 | outcome_by_time_bps | FIXED_HOLD_B4 | 12 | 12402 | 16229 | 16227 | 12404 | 12402 | 2.068 | 0.694 | 1.047 | -2.943 | 2.520 | 6 | 0 | 1.690 | 5422 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_4_HIGH_12 | decay_bps | FIXED_HOLD_B4 | 3 | 4024 | 6004 | 6004 | 4024 | 4024 | 27.124 | 22.862 | 4.262 | 2.638 | 8.180 | 3 | 0 | 1.345 | 1802 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_4_HIGH_12 | opportunity_duration | FIXED_HOLD_B4 | 3 | 4024 | 6004 | 6004 | 4024 | 4024 | 2.798 | 1.836 | 0.997 | 0.877 | 1.024 | 3 | 0 | 0.163 | 1802 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_4_HIGH_12 | outcome_by_time_bps | FIXED_HOLD_B4 | 3 | 4024 | 6004 | 6004 | 4024 | 4024 | 1.114 | 1.022 | 0.092 | 0.063 | 0.516 | 0 | 0 | 1.609 | 1802 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | decay_bps | FIXED_TARGET_M1.00 | 2 | 482 | 13326 | 13326 | 484 | 482 | 10.470 | 4.175 | 6.295 | 5.144 | 7.447 | 2 | 0 | 1.428 | 109 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | decay_bps | FIXED_TRAIL_M1.00 | 2 | 447 | 8651 | 8651 | 449 | 447 | 19.556 | 8.340 | 11.216 | 6.610 | 15.821 | 2 | 0 | 3.128 | 107 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | holding_efficiency | FIXED_TARGET_M1.00 | 2 | 482 | 13326 | 13326 | 484 | 482 | -2.380 | 0.734 | -3.114 | -3.197 | -3.031 | 0 | 2 | 1.195 | 109 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | holding_efficiency | FIXED_TRAIL_M1.00 | 2 | 447 | 8651 | 8651 | 449 | 447 | -2.656 | 0.386 | -3.042 | -3.682 | -2.403 | 0 | 2 | 2.789 | 107 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | opportunity_duration | FIXED_TARGET_M1.00 | 2 | 482 | 13326 | 13326 | 484 | 482 | 0.279 | 57.165 | -56.886 | -64.979 | -48.793 | 0 | 2 | 71.338 | 109 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | opportunity_duration | FIXED_TRAIL_M1.00 | 2 | 447 | 8651 | 8651 | 449 | 447 | 0.883 | 37.479 | -36.596 | -37.755 | -35.437 | 0 | 2 | 53.349 | 107 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | outcome_by_time_bps | FIXED_TARGET_M1.00 | 2 | 482 | 13326 | 13326 | 484 | 482 | 0.380 | 7.427 | -7.047 | -7.992 | -6.103 | 0 | 2 | 1.547 | 109 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | outcome_by_time_bps | FIXED_TRAIL_M1.00 | 2 | 447 | 8651 | 8651 | 449 | 447 | -0.012 | 7.852 | -7.864 | -10.408 | -5.321 | 0 | 2 | 4.749 | 107 |
**ctrader / device_size.parquet total_rows=1188**

**-- row census by arm_class x state --**

```text
arm_class                         state
FIXED_MANAGEMENT                  EVENT_UNDECIDED     12
                                  INCOMPLETE          24
                                  NO_EVENT            24
                                  NO_FEATURE          24
                                  ORDER_CREATED       24
MANAGEMENT                        EVENT_UNDECIDED     72
                                  INCOMPLETE         144
                                  NO_EVENT           144
                                  NO_FEATURE         144
                                  ORDER_CREATED      144
MANAGEMENT_COMPONENT_COMBINATION  EVENT_UNDECIDED     48
                                  INCOMPLETE          96
                                  NO_EVENT            96
                                  NO_FEATURE          96
                                  ORDER_CREATED       96
```

**-- rows with a defined estimate: 495 of 1188**

**-- ctrader / E_TOUCH / size : adaptive-minus-fixed by component x setting --**

| arm_class | component | setting | metric | comparator | sym_rows | episode_n | entry_fill_n | close_n | common_fill_n | common_close_n | obs med | comp med | est med | est min | est max | CI>0 | CI<0 | mde med | eff_trade_blocks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIXED_MANAGEMENT | FIXED | UNIT | concentration | FIXED_SIZE_UNIT | 15 | 8496 | 8496 | 8496 | 8496 | 8496 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1952 |
| FIXED_MANAGEMENT | FIXED | UNIT | drawdown_bps | FIXED_SIZE_UNIT | 3 | 8496 | 8496 | 8496 | 8496 | 8496 | -3035.417 | -3035.417 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1952 |
| FIXED_MANAGEMENT | FIXED | UNIT | risk_dispersion | FIXED_SIZE_UNIT | 3 | 8496 | 8496 | 8496 | 8496 | 8496 | 34.968 | 34.968 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1952 |
| FIXED_MANAGEMENT | FIXED | UNIT | tail_loss_bps | FIXED_SIZE_UNIT | 3 | 8496 | 8496 | 8496 | 8496 | 8496 | 73.182 | 73.182 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1952 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_HALVE_HIGH | concentration | FIXED_SIZE_UNIT | 15 | 8496 | 8496 | 8496 | 8496 | 8496 | 0.000 | 0.000 | 0.000 | 0.000 | 0.001 | 2 | 0 | 0.000 | 1952 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_HALVE_HIGH | drawdown_bps | FIXED_SIZE_UNIT | 3 | 8496 | 8496 | 8496 | 8496 | 8496 | -2870.345 | -3035.417 | 165.071 | -107.886 | 375.097 | 0 | 0 | 587.831 | 1952 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_HALVE_HIGH | risk_dispersion | FIXED_SIZE_UNIT | 3 | 8496 | 8496 | 8496 | 8496 | 8496 | 32.825 | 34.968 | -3.353 | -5.031 | -2.143 | 0 | 3 | 0.635 | 1952 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_HALVE_HIGH | tail_loss_bps | FIXED_SIZE_UNIT | 3 | 8496 | 8496 | 8496 | 8496 | 8496 | 71.240 | 73.182 | -4.470 | -6.416 | -1.942 | 0 | 3 | 5.645 | 1952 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_HALVE_HIGH | concentration | FIXED_SIZE_UNIT | 15 | 8496 | 8496 | 8496 | 8496 | 8496 | 0.000 | 0.000 | 0.000 | 0.000 | 0.001 | 2 | 0 | 0.000 | 1952 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_HALVE_HIGH | drawdown_bps | FIXED_SIZE_UNIT | 3 | 8496 | 8496 | 8496 | 8496 | 8496 | -2771.321 | -3035.417 | 264.096 | -35.590 | 376.406 | 0 | 0 | 467.660 | 1952 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_HALVE_HIGH | risk_dispersion | FIXED_SIZE_UNIT | 3 | 8496 | 8496 | 8496 | 8496 | 8496 | 31.416 | 34.968 | -3.552 | -5.175 | -2.932 | 0 | 3 | 0.857 | 1952 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_HALVE_HIGH | tail_loss_bps | FIXED_SIZE_UNIT | 3 | 8496 | 8496 | 8496 | 8496 | 8496 | 69.298 | 73.182 | -5.740 | -6.416 | -3.884 | 0 | 3 | 6.466 | 1952 |
| MANAGEMENT | LEVEL_NOW | STATE_HALVE_HIGH | concentration | FIXED_SIZE_UNIT | 15 | 8496 | 8496 | 8496 | 8496 | 8496 | 0.000 | 0.000 | 0.000 | 0.000 | 0.001 | 2 | 0 | 0.001 | 1952 |
| MANAGEMENT | LEVEL_NOW | STATE_HALVE_HIGH | drawdown_bps | FIXED_SIZE_UNIT | 3 | 8496 | 8496 | 8496 | 8496 | 8496 | -2156.489 | -3035.417 | 481.198 | 468.351 | 878.927 | 2 | 0 | 851.609 | 1952 |
| MANAGEMENT | LEVEL_NOW | STATE_HALVE_HIGH | risk_dispersion | FIXED_SIZE_UNIT | 3 | 8496 | 8496 | 8496 | 8496 | 8496 | 28.472 | 34.968 | -6.495 | -10.478 | -3.930 | 0 | 3 | 1.004 | 1952 |
| MANAGEMENT | LEVEL_NOW | STATE_HALVE_HIGH | tail_loss_bps | FIXED_SIZE_UNIT | 3 | 8496 | 8496 | 8496 | 8496 | 8496 | 58.717 | 73.182 | -14.465 | -19.839 | -10.144 | 0 | 3 | 6.297 | 1952 |
| MANAGEMENT | RANGE_SCALE | SCALE_NORMALISED | concentration | FIXED_SIZE_UNIT | 15 | 8496 | 8496 | 8496 | 8496 | 8496 | 0.000 | 0.000 | 0.000 | -0.001 | 0.001 | 0 | 0 | 0.001 | 1952 |
| MANAGEMENT | RANGE_SCALE | SCALE_NORMALISED | drawdown_bps | FIXED_SIZE_UNIT | 3 | 8496 | 8496 | 8496 | 8496 | 8496 | -1990.431 | -3035.417 | 252.623 | 111.383 | 1239.417 | 2 | 0 | 952.468 | 1952 |
| MANAGEMENT | RANGE_SCALE | SCALE_NORMALISED | risk_dispersion | FIXED_SIZE_UNIT | 3 | 8496 | 8496 | 8496 | 8496 | 8496 | 34.765 | 34.968 | -7.163 | -22.183 | -0.203 | 0 | 2 | 1.204 | 1952 |
| MANAGEMENT | RANGE_SCALE | SCALE_NORMALISED | tail_loss_bps | FIXED_SIZE_UNIT | 3 | 8496 | 8496 | 8496 | 8496 | 8496 | 71.840 | 73.182 | -13.203 | -42.149 | -1.342 | 0 | 2 | 5.225 | 1952 |
| MANAGEMENT | SHOCK | STATE_HALVE_HIGH | concentration | FIXED_SIZE_UNIT | 15 | 8496 | 8496 | 8496 | 8496 | 8496 | 0.000 | 0.000 | 0.000 | 0.000 | 0.001 | 2 | 0 | 0.001 | 1952 |
| MANAGEMENT | SHOCK | STATE_HALVE_HIGH | drawdown_bps | FIXED_SIZE_UNIT | 3 | 8496 | 8496 | 8496 | 8496 | 8496 | -2751.463 | -3035.417 | 134.594 | 15.145 | 283.954 | 0 | 0 | 559.162 | 1952 |
| MANAGEMENT | SHOCK | STATE_HALVE_HIGH | risk_dispersion | FIXED_SIZE_UNIT | 3 | 8496 | 8496 | 8496 | 8496 | 8496 | 32.026 | 34.968 | -2.942 | -7.034 | -2.629 | 0 | 3 | 0.848 | 1952 |
| MANAGEMENT | SHOCK | STATE_HALVE_HIGH | tail_loss_bps | FIXED_SIZE_UNIT | 3 | 8496 | 8496 | 8496 | 8496 | 8496 | 71.175 | 73.182 | -4.853 | -10.303 | -2.007 | 0 | 3 | 6.044 | 1952 |
| MANAGEMENT | TAIL_RISK | STATE_HALVE_HIGH | concentration | FIXED_SIZE_UNIT | 15 | 8496 | 8496 | 8496 | 8496 | 8496 | 0.000 | 0.000 | 0.000 | -0.000 | 0.001 | 1 | 0 | 0.000 | 1952 |
| MANAGEMENT | TAIL_RISK | STATE_HALVE_HIGH | drawdown_bps | FIXED_SIZE_UNIT | 3 | 8496 | 8496 | 8496 | 8496 | 8496 | -1873.761 | -3035.417 | 897.796 | 458.608 | 1356.087 | 2 | 0 | 737.373 | 1952 |
| MANAGEMENT | TAIL_RISK | STATE_HALVE_HIGH | risk_dispersion | FIXED_SIZE_UNIT | 3 | 8496 | 8496 | 8496 | 8496 | 8496 | 28.444 | 34.968 | -9.334 | -27.414 | -6.524 | 0 | 3 | 1.016 | 1952 |
| MANAGEMENT | TAIL_RISK | STATE_HALVE_HIGH | tail_loss_bps | FIXED_SIZE_UNIT | 3 | 8496 | 8496 | 8496 | 8496 | 8496 | 58.717 | 73.182 | -19.113 | -58.959 | -14.465 | 0 | 3 | 6.297 | 1952 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | concentration | FIXED_SIZE_UNIT | 45 | 25488 | 25488 | 25488 | 25488 | 25488 | 0.000 | 0.000 | 0.000 | -0.000 | 0.002 | 2 | 0 | 0.001 | 5856 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | drawdown_bps | FIXED_SIZE_UNIT | 9 | 25488 | 25488 | 25488 | 25488 | 25488 | -2189.507 | -3035.417 | 435.731 | -12.868 | 1769.956 | 2 | 0 | 522.919 | 5856 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | risk_dispersion | FIXED_SIZE_UNIT | 9 | 25488 | 25488 | 25488 | 25488 | 25488 | 32.310 | 34.968 | -7.498 | -28.436 | -2.006 | 0 | 9 | 1.141 | 5856 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | tail_loss_bps | FIXED_SIZE_UNIT | 9 | 25488 | 25488 | 25488 | 25488 | 25488 | 69.987 | 73.182 | -13.948 | -57.031 | -3.195 | 0 | 7 | 5.125 | 5856 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | concentration | FIXED_SIZE_UNIT | 15 | 8496 | 8496 | 8496 | 8496 | 8496 | 0.000 | 0.000 | 0.000 | 0.000 | 0.002 | 3 | 0 | 0.001 | 1952 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | drawdown_bps | FIXED_SIZE_UNIT | 3 | 8496 | 8496 | 8496 | 8496 | 8496 | -2239.963 | -3035.417 | 795.453 | 526.107 | 820.587 | 0 | 0 | 812.154 | 1952 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | risk_dispersion | FIXED_SIZE_UNIT | 3 | 8496 | 8496 | 8496 | 8496 | 8496 | 27.357 | 34.968 | -7.611 | -14.423 | -5.048 | 0 | 3 | 1.147 | 1952 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | tail_loss_bps | FIXED_SIZE_UNIT | 3 | 8496 | 8496 | 8496 | 8496 | 8496 | 56.228 | 73.182 | -16.954 | -31.521 | -12.867 | 0 | 3 | 6.271 | 1952 |
**-- ctrader / E_CLOSE / size : adaptive-minus-fixed by component x setting --**

| arm_class | component | setting | metric | comparator | sym_rows | episode_n | entry_fill_n | close_n | common_fill_n | common_close_n | obs med | comp med | est med | est min | est max | CI>0 | CI<0 | mde med | eff_trade_blocks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIXED_MANAGEMENT | FIXED | UNIT | concentration | FIXED_SIZE_UNIT | 12 | 7537 | 7537 | 7537 | 7537 | 7537 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1979 |
| FIXED_MANAGEMENT | FIXED | UNIT | drawdown_bps | FIXED_SIZE_UNIT | 3 | 7537 | 7537 | 7537 | 7537 | 7537 | -1337.736 | -1337.736 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1979 |
| FIXED_MANAGEMENT | FIXED | UNIT | risk_dispersion | FIXED_SIZE_UNIT | 3 | 7537 | 7537 | 7537 | 7537 | 7537 | 34.687 | 34.687 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1979 |
| FIXED_MANAGEMENT | FIXED | UNIT | tail_loss_bps | FIXED_SIZE_UNIT | 3 | 7537 | 7537 | 7537 | 7537 | 7537 | 75.364 | 75.364 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1979 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_HALVE_HIGH | concentration | FIXED_SIZE_UNIT | 12 | 7537 | 7537 | 7537 | 7537 | 7537 | 0.000 | 0.000 | 0.000 | 0.000 | 0.001 | 2 | 0 | 0.001 | 1979 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_HALVE_HIGH | drawdown_bps | FIXED_SIZE_UNIT | 3 | 7537 | 7537 | 7537 | 7537 | 7537 | -883.257 | -1337.736 | 188.420 | 136.974 | 599.153 | 0 | 0 | 457.222 | 1979 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_HALVE_HIGH | risk_dispersion | FIXED_SIZE_UNIT | 3 | 7537 | 7537 | 7537 | 7537 | 7537 | 31.924 | 34.687 | -3.535 | -5.823 | -2.763 | 0 | 3 | 0.879 | 1979 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_HALVE_HIGH | tail_loss_bps | FIXED_SIZE_UNIT | 3 | 7537 | 7537 | 7537 | 7537 | 7537 | 71.239 | 75.364 | -8.002 | -11.653 | -4.124 | 0 | 3 | 5.507 | 1979 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_HALVE_HIGH | concentration | FIXED_SIZE_UNIT | 12 | 7537 | 7537 | 7537 | 7537 | 7537 | 0.000 | 0.000 | 0.000 | 0.000 | 0.001 | 2 | 0 | 0.001 | 1979 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_HALVE_HIGH | drawdown_bps | FIXED_SIZE_UNIT | 3 | 7537 | 7537 | 7537 | 7537 | 7537 | -966.286 | -1337.736 | 252.524 | 105.390 | 458.876 | 0 | 0 | 381.851 | 1979 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_HALVE_HIGH | risk_dispersion | FIXED_SIZE_UNIT | 3 | 7537 | 7537 | 7537 | 7537 | 7537 | 30.712 | 34.687 | -3.975 | -6.073 | -2.850 | 0 | 3 | 0.860 | 1979 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_HALVE_HIGH | tail_loss_bps | FIXED_SIZE_UNIT | 3 | 7537 | 7537 | 7537 | 7537 | 7537 | 66.475 | 75.364 | -8.888 | -12.062 | -5.879 | 0 | 3 | 4.671 | 1979 |
| MANAGEMENT | LEVEL_NOW | STATE_HALVE_HIGH | concentration | FIXED_SIZE_UNIT | 12 | 7537 | 7537 | 7537 | 7537 | 7537 | 0.000 | 0.000 | 0.000 | 0.000 | 0.002 | 1 | 0 | 0.002 | 1979 |
| MANAGEMENT | LEVEL_NOW | STATE_HALVE_HIGH | drawdown_bps | FIXED_SIZE_UNIT | 3 | 7537 | 7537 | 7537 | 7537 | 7537 | -985.068 | -1337.736 | 352.668 | 308.656 | 522.296 | 0 | 0 | 494.536 | 1979 |
| MANAGEMENT | LEVEL_NOW | STATE_HALVE_HIGH | risk_dispersion | FIXED_SIZE_UNIT | 3 | 7537 | 7537 | 7537 | 7537 | 7537 | 27.221 | 34.687 | -7.466 | -11.234 | -3.868 | 0 | 3 | 1.185 | 1979 |
| MANAGEMENT | LEVEL_NOW | STATE_HALVE_HIGH | tail_loss_bps | FIXED_SIZE_UNIT | 3 | 7537 | 7537 | 7537 | 7537 | 7537 | 57.873 | 75.364 | -17.491 | -26.834 | -8.218 | 0 | 3 | 6.077 | 1979 |
| MANAGEMENT | RANGE_SCALE | SCALE_NORMALISED | concentration | FIXED_SIZE_UNIT | 12 | 7537 | 7537 | 7537 | 7537 | 7537 | 0.000 | 0.000 | 0.000 | -0.001 | 0.001 | 1 | 0 | 0.001 | 1979 |
| MANAGEMENT | RANGE_SCALE | SCALE_NORMALISED | drawdown_bps | FIXED_SIZE_UNIT | 3 | 7537 | 7537 | 7537 | 7537 | 7537 | -1009.805 | -1337.736 | 508.396 | 61.871 | 876.033 | 2 | 0 | 506.622 | 1979 |
| MANAGEMENT | RANGE_SCALE | SCALE_NORMALISED | risk_dispersion | FIXED_SIZE_UNIT | 3 | 7537 | 7537 | 7537 | 7537 | 7537 | 34.539 | 34.687 | -7.442 | -22.017 | -0.148 | 0 | 2 | 1.223 | 1979 |
| MANAGEMENT | RANGE_SCALE | SCALE_NORMALISED | tail_loss_bps | FIXED_SIZE_UNIT | 3 | 7537 | 7537 | 7537 | 7537 | 7537 | 72.179 | 75.364 | -14.926 | -40.982 | -3.185 | 0 | 2 | 6.132 | 1979 |
| MANAGEMENT | SHOCK | STATE_HALVE_HIGH | concentration | FIXED_SIZE_UNIT | 12 | 7537 | 7537 | 7537 | 7537 | 7537 | 0.000 | 0.000 | 0.000 | -0.000 | 0.001 | 1 | 0 | 0.001 | 1979 |
| MANAGEMENT | SHOCK | STATE_HALVE_HIGH | drawdown_bps | FIXED_SIZE_UNIT | 3 | 7537 | 7537 | 7537 | 7537 | 7537 | -1137.215 | -1337.736 | 200.522 | 188.503 | 250.149 | 0 | 0 | 416.326 | 1979 |
| MANAGEMENT | SHOCK | STATE_HALVE_HIGH | risk_dispersion | FIXED_SIZE_UNIT | 3 | 7537 | 7537 | 7537 | 7537 | 7537 | 31.269 | 34.687 | -3.418 | -6.257 | -3.104 | 0 | 3 | 0.879 | 1979 |
| MANAGEMENT | SHOCK | STATE_HALVE_HIGH | tail_loss_bps | FIXED_SIZE_UNIT | 3 | 7537 | 7537 | 7537 | 7537 | 7537 | 67.972 | 75.364 | -7.391 | -11.609 | -7.155 | 0 | 3 | 5.720 | 1979 |
| MANAGEMENT | TAIL_RISK | STATE_HALVE_HIGH | concentration | FIXED_SIZE_UNIT | 12 | 7537 | 7537 | 7537 | 7537 | 7537 | 0.000 | 0.000 | 0.000 | -0.001 | 0.001 | 0 | 0 | 0.001 | 1979 |
| MANAGEMENT | TAIL_RISK | STATE_HALVE_HIGH | drawdown_bps | FIXED_SIZE_UNIT | 3 | 7537 | 7537 | 7537 | 7537 | 7537 | -771.966 | -1337.736 | 565.770 | 308.656 | 1113.260 | 2 | 0 | 351.697 | 1979 |
| MANAGEMENT | TAIL_RISK | STATE_HALVE_HIGH | risk_dispersion | FIXED_SIZE_UNIT | 3 | 7537 | 7537 | 7537 | 7537 | 7537 | 27.191 | 34.687 | -9.437 | -27.680 | -7.497 | 0 | 3 | 1.176 | 1979 |
| MANAGEMENT | TAIL_RISK | STATE_HALVE_HIGH | tail_loss_bps | FIXED_SIZE_UNIT | 3 | 7537 | 7537 | 7537 | 7537 | 7537 | 57.873 | 75.364 | -18.674 | -56.550 | -17.491 | 0 | 3 | 6.077 | 1979 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | concentration | FIXED_SIZE_UNIT | 36 | 22611 | 22611 | 22611 | 22611 | 22611 | 0.000 | 0.000 | 0.000 | -0.001 | 0.003 | 3 | 0 | 0.001 | 5937 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | drawdown_bps | FIXED_SIZE_UNIT | 9 | 22611 | 22611 | 22611 | 22611 | 22611 | -933.323 | -1337.736 | 425.063 | 66.869 | 1323.746 | 3 | 0 | 602.963 | 5937 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | risk_dispersion | FIXED_SIZE_UNIT | 9 | 22611 | 22611 | 22611 | 22611 | 22611 | 31.464 | 34.687 | -7.498 | -28.504 | -2.746 | 0 | 9 | 1.364 | 5937 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | tail_loss_bps | FIXED_SIZE_UNIT | 9 | 22611 | 22611 | 22611 | 22611 | 22611 | 65.811 | 75.364 | -17.829 | -59.347 | -4.848 | 0 | 8 | 7.052 | 5937 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | concentration | FIXED_SIZE_UNIT | 12 | 7537 | 7537 | 7537 | 7537 | 7537 | 0.000 | 0.000 | 0.000 | 0.000 | 0.002 | 1 | 0 | 0.002 | 1979 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | drawdown_bps | FIXED_SIZE_UNIT | 3 | 7537 | 7537 | 7537 | 7537 | 7537 | -906.416 | -1337.736 | 431.321 | 343.213 | 765.740 | 0 | 0 | 510.170 | 1979 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | risk_dispersion | FIXED_SIZE_UNIT | 3 | 7537 | 7537 | 7537 | 7537 | 7537 | 25.855 | 34.687 | -8.832 | -14.489 | -5.298 | 0 | 3 | 1.280 | 1979 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | tail_loss_bps | FIXED_SIZE_UNIT | 3 | 7537 | 7537 | 7537 | 7537 | 7537 | 56.870 | 75.364 | -18.493 | -30.528 | -11.587 | 0 | 3 | 6.648 | 1979 |
**crypto / device_target.parquet total_rows=16232**

**-- row census by arm_class x state --**

```text
arm_class                         state
FIXED_MANAGEMENT                  EVENT_UNDECIDED     276
                                  INCOMPLETE          600
                                  NO_EVENT            528
                                  NO_FEATURE          600
                                  ORDER_CREATED       600
MANAGEMENT                        EVENT_UNDECIDED    1092
                                  INCOMPLETE         2400
                                  NO_EVENT           2100
                                  NO_FEATURE         1200
                                  ORDER_CREATED      2400
MANAGEMENT_COMPONENT_COMBINATION  EVENT_UNDECIDED     424
                                  INCOMPLETE          800
                                  NO_EVENT            876
                                  ORDER_CREATED      1000
MANAGEMENT_DEVICE_COMBINATION     EVENT_UNDECIDED     184
                                  INCOMPLETE          400
                                  NO_EVENT            352
                                  ORDER_CREATED       400
```

**-- rows with a defined estimate: 3408 of 16232**

**-- crypto / E_TOUCH / target : adaptive-minus-fixed by component x setting --**

| arm_class | component | setting | metric | comparator | sym_rows | episode_n | entry_fill_n | close_n | common_fill_n | common_close_n | obs med | comp med | est med | est min | est max | CI>0 | CI<0 | mde med | eff_trade_blocks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIXED_MANAGEMENT | FIXED | M0.75 | missed_excess_bps | FIXED_TARGET_M0.75 | 25 | 6135 | 6157 | 6135 | 6157 | 6135 | 178.144 | 178.144 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 892 |
| FIXED_MANAGEMENT | FIXED | M0.75 | reach_rate | FIXED_TARGET_M0.75 | 25 | 6135 | 6157 | 6135 | 6157 | 6135 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 892 |
| FIXED_MANAGEMENT | FIXED | M0.75 | realised_capture_bps | FIXED_TARGET_M0.75 | 25 | 6135 | 6157 | 6135 | 6157 | 6135 | 43.969 | 43.969 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 892 |
| FIXED_MANAGEMENT | FIXED | M0.75 | time_to_target | FIXED_TARGET_M0.75 | 25 | 6135 | 6157 | 6135 | 6157 | 6135 | 15.140 | 15.140 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 892 |
| FIXED_MANAGEMENT | FIXED | M1.00 | missed_excess_bps | FIXED_TARGET_M1.00 | 25 | 4063 | 4086 | 4063 | 4086 | 4063 | 175.494 | 175.494 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 745 |
| FIXED_MANAGEMENT | FIXED | M1.00 | reach_rate | FIXED_TARGET_M1.00 | 25 | 4063 | 4086 | 4063 | 4086 | 4063 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 745 |
| FIXED_MANAGEMENT | FIXED | M1.00 | realised_capture_bps | FIXED_TARGET_M1.00 | 25 | 4063 | 4086 | 4063 | 4086 | 4063 | 58.613 | 58.613 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 745 |
| FIXED_MANAGEMENT | FIXED | M1.00 | time_to_target | FIXED_TARGET_M1.00 | 25 | 4063 | 4086 | 4063 | 4086 | 4063 | 24.069 | 24.069 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 745 |
| FIXED_MANAGEMENT | FIXED | M1.50 | missed_excess_bps | FIXED_TARGET_M1.50 | 25 | 3043 | 3066 | 3043 | 3066 | 3043 | 166.653 | 166.653 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 767 |
| FIXED_MANAGEMENT | FIXED | M1.50 | reach_rate | FIXED_TARGET_M1.50 | 25 | 3043 | 3066 | 3043 | 3066 | 3043 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 767 |
| FIXED_MANAGEMENT | FIXED | M1.50 | realised_capture_bps | FIXED_TARGET_M1.50 | 25 | 3043 | 3066 | 3043 | 3066 | 3043 | 87.937 | 87.937 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 767 |
| FIXED_MANAGEMENT | FIXED | M1.50 | time_to_target | FIXED_TARGET_M1.50 | 25 | 3043 | 3066 | 3043 | 3066 | 3043 | 32.471 | 32.471 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 767 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | missed_excess_bps | FIXED_TARGET_M1.00 | 25 | 3362 | 4520 | 4498 | 3380 | 3362 | 214.396 | 216.432 | -0.153 | -7.321 | 4.651 | 0 | 3 | 2.275 | 634 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | reach_rate | FIXED_TARGET_M1.00 | 25 | 3362 | 4520 | 4498 | 3380 | 3362 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 634 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | realised_capture_bps | FIXED_TARGET_M1.00 | 25 | 3362 | 4520 | 4498 | 3380 | 3362 | 61.373 | 58.610 | 0.161 | -14.504 | 10.024 | 4 | 1 | 2.393 | 634 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | time_to_target | FIXED_TARGET_M1.00 | 25 | 3362 | 4520 | 4498 | 3380 | 3362 | 26.018 | 25.788 | 0.000 | -1.243 | 29.270 | 0 | 1 | 0.119 | 634 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | missed_excess_bps | FIXED_TARGET_M1.00 | 25 | 3170 | 4163 | 4141 | 3186 | 3170 | 215.132 | 216.432 | -0.154 | -8.445 | 3.480 | 0 | 3 | 2.822 | 588 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | reach_rate | FIXED_TARGET_M1.00 | 25 | 3170 | 4163 | 4141 | 3186 | 3170 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 588 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | realised_capture_bps | FIXED_TARGET_M1.00 | 25 | 3170 | 4163 | 4141 | 3186 | 3170 | 63.137 | 58.610 | 0.337 | -5.957 | 10.024 | 4 | 0 | 2.736 | 588 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | time_to_target | FIXED_TARGET_M1.00 | 25 | 3170 | 4163 | 4141 | 3186 | 3170 | 25.924 | 25.904 | 0.000 | -1.197 | 29.357 | 2 | 0 | 0.107 | 588 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | missed_excess_bps | FIXED_TARGET_M1.00 | 25 | 2121 | 4452 | 4430 | 2133 | 2121 | 202.427 | 209.213 | -2.591 | -9.875 | 7.185 | 1 | 1 | 7.186 | 407 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | reach_rate | FIXED_TARGET_M1.00 | 25 | 2121 | 4452 | 4430 | 2133 | 2121 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 407 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | realised_capture_bps | FIXED_TARGET_M1.00 | 25 | 2121 | 4452 | 4430 | 2133 | 2121 | 62.717 | 58.610 | 3.946 | -9.382 | 23.905 | 3 | 0 | 6.995 | 407 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | time_to_target | FIXED_TARGET_M1.00 | 25 | 2121 | 4452 | 4430 | 2133 | 2121 | 9.606 | 13.952 | -0.255 | -169.659 | 31.812 | 1 | 1 | 3.348 | 407 |
| MANAGEMENT | RANGE_SCALE | M0.75 | missed_excess_bps | FIXED_TARGET_M0.75 | 25 | 2439 | 5092 | 5068 | 2454 | 2439 | 212.821 | 224.660 | -11.375 | -110.052 | 8.717 | 0 | 13 | 11.409 | 437 |
| MANAGEMENT | RANGE_SCALE | M0.75 | reach_rate | FIXED_TARGET_M0.75 | 25 | 2439 | 5092 | 5068 | 2454 | 2439 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 437 |
| MANAGEMENT | RANGE_SCALE | M0.75 | realised_capture_bps | FIXED_TARGET_M0.75 | 25 | 2439 | 5092 | 5068 | 2454 | 2439 | 69.087 | 43.977 | 15.927 | 0.880 | 145.521 | 19 | 0 | 9.566 | 437 |
| MANAGEMENT | RANGE_SCALE | M0.75 | time_to_target | FIXED_TARGET_M0.75 | 25 | 2439 | 5092 | 5068 | 2454 | 2439 | 16.197 | 9.116 | 2.688 | -65.647 | 115.987 | 16 | 0 | 6.391 | 437 |
| MANAGEMENT | RANGE_SCALE | M1.00 | missed_excess_bps | FIXED_TARGET_M1.00 | 25 | 1357 | 3102 | 3079 | 1368 | 1357 | 199.169 | 223.015 | -8.729 | -141.926 | 5.330 | 1 | 11 | 15.821 | 331 |
| MANAGEMENT | RANGE_SCALE | M1.00 | reach_rate | FIXED_TARGET_M1.00 | 25 | 1357 | 3102 | 3079 | 1368 | 1357 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 331 |
| MANAGEMENT | RANGE_SCALE | M1.00 | realised_capture_bps | FIXED_TARGET_M1.00 | 25 | 1357 | 3102 | 3079 | 1368 | 1357 | 92.614 | 58.618 | 21.370 | -49.486 | 166.085 | 16 | 1 | 12.560 | 331 |
| MANAGEMENT | RANGE_SCALE | M1.00 | time_to_target | FIXED_TARGET_M1.00 | 25 | 1357 | 3102 | 3079 | 1368 | 1357 | 43.842 | 19.267 | 1.897 | -8.850 | 139.452 | 16 | 1 | 6.513 | 331 |
| MANAGEMENT | RANGE_SCALE | M1.50 | missed_excess_bps | FIXED_TARGET_M1.50 | 25 | 1149 | 2491 | 2467 | 1158 | 1149 | 164.165 | 194.166 | -13.398 | -194.894 | 16.791 | 0 | 10 | 20.643 | 371 |
| MANAGEMENT | RANGE_SCALE | M1.50 | reach_rate | FIXED_TARGET_M1.50 | 25 | 1149 | 2491 | 2467 | 1158 | 1149 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 371 |
| MANAGEMENT | RANGE_SCALE | M1.50 | realised_capture_bps | FIXED_TARGET_M1.50 | 25 | 1149 | 2491 | 2467 | 1158 | 1149 | 126.173 | 87.946 | 28.410 | -1.302 | 428.777 | 18 | 0 | 17.121 | 371 |
| MANAGEMENT | RANGE_SCALE | M1.50 | time_to_target | FIXED_TARGET_M1.50 | 25 | 1149 | 2491 | 2467 | 1158 | 1149 | 37.432 | 17.800 | 2.129 | -96.713 | 400.111 | 14 | 0 | 4.426 | 371 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | missed_excess_bps | FIXED_TARGET_M1.00 | 25 | 2200 | 5336 | 5314 | 2212 | 2200 | 216.043 | 215.445 | 1.600 | -18.815 | 24.226 | 5 | 2 | 7.045 | 421 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | reach_rate | FIXED_TARGET_M1.00 | 25 | 2200 | 5336 | 5314 | 2212 | 2200 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 421 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | realised_capture_bps | FIXED_TARGET_M1.00 | 25 | 2200 | 5336 | 5314 | 2212 | 2200 | 57.408 | 58.615 | -2.904 | -17.659 | 20.654 | 1 | 8 | 5.401 | 421 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | time_to_target | FIXED_TARGET_M1.00 | 25 | 2200 | 5336 | 5314 | 2212 | 2200 | 7.974 | 13.577 | -0.877 | -194.715 | 26.730 | 0 | 8 | 3.394 | 421 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_075_HIGH_150 | missed_excess_bps | FIXED_TARGET_M1.00 | 25 | 2408 | 4727 | 4704 | 2421 | 2408 | 207.780 | 209.373 | -0.142 | -2.475 | 12.062 | 2 | 0 | 5.572 | 462 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_075_HIGH_150 | reach_rate | FIXED_TARGET_M1.00 | 25 | 2408 | 4727 | 4704 | 2421 | 2408 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 462 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_075_HIGH_150 | realised_capture_bps | FIXED_TARGET_M1.00 | 25 | 2408 | 4727 | 4704 | 2421 | 2408 | 56.199 | 58.616 | 0.000 | -9.851 | 5.398 | 1 | 1 | 4.852 | 462 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_075_HIGH_150 | time_to_target | FIXED_TARGET_M1.00 | 25 | 2408 | 4727 | 4704 | 2421 | 2408 | 24.050 | 22.929 | 0.000 | -8.192 | 81.806 | 1 | 2 | 1.280 | 462 |
| MANAGEMENT | SWING_SCALE | M0.75 | missed_excess_bps | FIXED_TARGET_M0.75 | 7 | 33 | 147 | 140 | 34 | 33 | 30.652 | 125.422 | -103.502 | -212.722 | -46.057 | 0 | 5 | 145.437 | 29 |
| MANAGEMENT | SWING_SCALE | M0.75 | reach_rate | FIXED_TARGET_M0.75 | 7 | 33 | 147 | 140 | 34 | 33 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 29 |
| MANAGEMENT | SWING_SCALE | M0.75 | realised_capture_bps | FIXED_TARGET_M0.75 | 7 | 33 | 147 | 140 | 34 | 33 | 575.203 | 33.450 | 541.646 | 512.823 | 733.030 | 7 | 0 | 128.556 | 29 |
| MANAGEMENT | SWING_SCALE | M0.75 | time_to_target | FIXED_TARGET_M0.75 | 7 | 33 | 147 | 140 | 34 | 33 | 401.367 | 5.142 | 401.333 | 62.150 | 3630.861 | 7 | 0 | 362.145 | 29 |
| MANAGEMENT | SWING_SCALE | M1.00 | missed_excess_bps | FIXED_TARGET_M1.00 | 6 | 20 | 113 | 107 | 20 | 20 | 52.234 | 217.442 | -155.924 | -470.153 | -118.662 | 0 | 3 | 169.742 | 20 |
| MANAGEMENT | SWING_SCALE | M1.00 | reach_rate | FIXED_TARGET_M1.00 | 6 | 20 | 113 | 107 | 20 | 20 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 20 |
| MANAGEMENT | SWING_SCALE | M1.00 | realised_capture_bps | FIXED_TARGET_M1.00 | 6 | 20 | 113 | 107 | 20 | 20 | 992.292 | 44.544 | 934.376 | 506.394 | 2646.593 | 6 | 0 | 171.814 | 20 |
| MANAGEMENT | SWING_SCALE | M1.00 | time_to_target | FIXED_TARGET_M1.00 | 6 | 20 | 113 | 107 | 20 | 20 | 212.673 | 1.098 | 206.913 | 13.072 | 814.117 | 6 | 0 | 52.858 | 20 |
| MANAGEMENT | SWING_SCALE | M1.50 | missed_excess_bps | FIXED_TARGET_M1.50 | 5 | 9 | 54 | 49 | 10 | 9 | 67.464 | 234.983 | -205.415 | -308.806 | 77.657 | 1 | 3 | 44.501 | 9 |
| MANAGEMENT | SWING_SCALE | M1.50 | reach_rate | FIXED_TARGET_M1.50 | 5 | 9 | 54 | 49 | 10 | 9 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 9 |
| MANAGEMENT | SWING_SCALE | M1.50 | realised_capture_bps | FIXED_TARGET_M1.50 | 5 | 9 | 54 | 49 | 10 | 9 | 876.123 | 66.804 | 809.319 | 610.022 | 1756.364 | 5 | 0 | 324.847 | 9 |
| MANAGEMENT | SWING_SCALE | M1.50 | time_to_target | FIXED_TARGET_M1.50 | 5 | 9 | 54 | 49 | 10 | 9 | 949.267 | 0.158 | 949.217 | 71.733 | 3872.850 | 5 | 0 | 830.928 | 9 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | missed_excess_bps | FIXED_TARGET_M1.00 | 25 | 1860 | 4125 | 4103 | 1871 | 1860 | 238.198 | 253.629 | -3.081 | -25.493 | 29.412 | 5 | 2 | 9.902 | 356 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | reach_rate | FIXED_TARGET_M1.00 | 25 | 1860 | 4125 | 4103 | 1871 | 1860 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 356 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | realised_capture_bps | FIXED_TARGET_M1.00 | 25 | 1860 | 4125 | 4103 | 1871 | 1860 | 55.482 | 58.610 | 1.432 | -29.412 | 16.846 | 2 | 8 | 6.473 | 356 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | time_to_target | FIXED_TARGET_M1.00 | 25 | 1860 | 4125 | 4103 | 1871 | 1860 | 12.092 | 14.706 | -0.181 | -71.775 | 31.806 | 2 | 9 | 3.212 | 356 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | missed_excess_bps | FIXED_TARGET_M1.00 | 35 | 1459 | 5456 | 5423 | 1474 | 1459 | 152.834 | 175.449 | -20.834 | -113.014 | 18.351 | 0 | 19 | 20.770 | 389 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | reach_rate | FIXED_TARGET_M1.00 | 35 | 1459 | 5456 | 5423 | 1474 | 1459 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 389 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | realised_capture_bps | FIXED_TARGET_M1.00 | 35 | 1459 | 5456 | 5423 | 1474 | 1459 | 91.434 | 44.915 | 22.298 | -8.135 | 151.822 | 19 | 1 | 21.002 | 389 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | time_to_target | FIXED_TARGET_M1.00 | 35 | 1459 | 5456 | 5423 | 1474 | 1459 | 10.845 | 9.367 | 1.034 | -278.435 | 390.151 | 10 | 1 | 7.870 | 389 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | missed_excess_bps | FIXED_TARGET_M1.00 | 19 | 1419 | 3612 | 3594 | 1428 | 1419 | 156.705 | 160.431 | -5.213 | -64.915 | 0.209 | 0 | 1 | 9.102 | 293 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | reach_rate | FIXED_TARGET_M1.00 | 19 | 1419 | 3612 | 3594 | 1428 | 1419 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 293 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | realised_capture_bps | FIXED_TARGET_M1.00 | 19 | 1419 | 3612 | 3594 | 1428 | 1419 | 49.322 | 44.814 | 4.393 | -28.996 | 18.588 | 1 | 1 | 7.668 | 293 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | time_to_target | FIXED_TARGET_M1.00 | 19 | 1419 | 3612 | 3594 | 1428 | 1419 | 6.193 | 9.743 | -0.727 | -323.160 | 21.030 | 0 | 2 | 3.473 | 293 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | missed_excess_bps | FIXED_TARGET_M1.00 | 50 | 7895 | 311694 | 311694 | 7937 | 7895 | 223.657 | 180.230 | 39.028 | -28.982 | 117.212 | 44 | 0 | 13.555 | 1490 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | reach_rate | FIXED_TARGET_M1.00 | 50 | 7895 | 311694 | 311694 | 7937 | 7895 | 0.502 | 1.000 | -0.498 | -0.659 | -0.364 | 0 | 48 | 0.080 | 1490 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | realised_capture_bps | FIXED_TARGET_M1.00 | 50 | 7895 | 311694 | 311694 | 7937 | 7895 | 1.346 | 58.614 | -53.946 | -148.823 | 28.982 | 0 | 46 | 13.998 | 1490 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | time_to_target | FIXED_TARGET_M1.00 | 50 | 7895 | 311694 | 311694 | 7937 | 7895 | 0.401 | 24.587 | -24.216 | -144.996 | 0.227 | 2 | 46 | 31.844 | 1490 |
**-- crypto / E_CLOSE / target : adaptive-minus-fixed by component x setting --**

| arm_class | component | setting | metric | comparator | sym_rows | episode_n | entry_fill_n | close_n | common_fill_n | common_close_n | obs med | comp med | est med | est min | est max | CI>0 | CI<0 | mde med | eff_trade_blocks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIXED_MANAGEMENT | FIXED | M0.75 | missed_excess_bps | FIXED_TARGET_M0.75 | 25 | 6405 | 6427 | 6405 | 6427 | 6405 | 217.555 | 217.555 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1165 |
| FIXED_MANAGEMENT | FIXED | M0.75 | reach_rate | FIXED_TARGET_M0.75 | 25 | 6405 | 6427 | 6405 | 6427 | 6405 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1165 |
| FIXED_MANAGEMENT | FIXED | M0.75 | realised_capture_bps | FIXED_TARGET_M0.75 | 25 | 6405 | 6427 | 6405 | 6427 | 6405 | 43.971 | 43.971 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1165 |
| FIXED_MANAGEMENT | FIXED | M0.75 | time_to_target | FIXED_TARGET_M0.75 | 25 | 6405 | 6427 | 6405 | 6427 | 6405 | 16.997 | 16.997 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1165 |
| FIXED_MANAGEMENT | FIXED | M1.00 | missed_excess_bps | FIXED_TARGET_M1.00 | 25 | 4685 | 4709 | 4685 | 4709 | 4685 | 198.577 | 198.577 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1035 |
| FIXED_MANAGEMENT | FIXED | M1.00 | reach_rate | FIXED_TARGET_M1.00 | 25 | 4685 | 4709 | 4685 | 4709 | 4685 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1035 |
| FIXED_MANAGEMENT | FIXED | M1.00 | realised_capture_bps | FIXED_TARGET_M1.00 | 25 | 4685 | 4709 | 4685 | 4709 | 4685 | 58.619 | 58.619 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1035 |
| FIXED_MANAGEMENT | FIXED | M1.00 | time_to_target | FIXED_TARGET_M1.00 | 25 | 4685 | 4709 | 4685 | 4709 | 4685 | 21.532 | 21.532 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1035 |
| FIXED_MANAGEMENT | FIXED | M1.50 | missed_excess_bps | FIXED_TARGET_M1.50 | 25 | 3184 | 3208 | 3184 | 3208 | 3184 | 162.076 | 162.076 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 880 |
| FIXED_MANAGEMENT | FIXED | M1.50 | reach_rate | FIXED_TARGET_M1.50 | 25 | 3184 | 3208 | 3184 | 3208 | 3184 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 880 |
| FIXED_MANAGEMENT | FIXED | M1.50 | realised_capture_bps | FIXED_TARGET_M1.50 | 25 | 3184 | 3208 | 3184 | 3208 | 3184 | 87.947 | 87.947 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 880 |
| FIXED_MANAGEMENT | FIXED | M1.50 | time_to_target | FIXED_TARGET_M1.50 | 25 | 3184 | 3208 | 3184 | 3208 | 3184 | 36.427 | 36.427 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 880 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | missed_excess_bps | FIXED_TARGET_M1.00 | 25 | 3797 | 4508 | 4484 | 3817 | 3797 | 200.828 | 202.440 | 0.000 | -8.200 | 1.624 | 0 | 2 | 1.427 | 842 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | reach_rate | FIXED_TARGET_M1.00 | 25 | 3797 | 4508 | 4484 | 3817 | 3797 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 842 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | realised_capture_bps | FIXED_TARGET_M1.00 | 25 | 3797 | 4508 | 4484 | 3817 | 3797 | 60.590 | 58.615 | 0.567 | -13.919 | 9.853 | 2 | 1 | 1.594 | 842 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | time_to_target | FIXED_TARGET_M1.00 | 25 | 3797 | 4508 | 4484 | 3817 | 3797 | 22.811 | 21.825 | 0.000 | -0.499 | 0.986 | 2 | 1 | 0.212 | 842 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | missed_excess_bps | FIXED_TARGET_M1.00 | 25 | 3808 | 4614 | 4590 | 3827 | 3808 | 218.170 | 220.343 | -0.238 | -11.089 | 4.385 | 0 | 2 | 1.736 | 851 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | reach_rate | FIXED_TARGET_M1.00 | 25 | 3808 | 4614 | 4590 | 3827 | 3808 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 851 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | realised_capture_bps | FIXED_TARGET_M1.00 | 25 | 3808 | 4614 | 4590 | 3827 | 3808 | 63.506 | 58.615 | 1.105 | -7.142 | 11.089 | 2 | 0 | 1.882 | 851 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | time_to_target | FIXED_TARGET_M1.00 | 25 | 3808 | 4614 | 4590 | 3827 | 3808 | 23.103 | 21.706 | 0.000 | -1.873 | 5.962 | 2 | 2 | 0.247 | 851 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | missed_excess_bps | FIXED_TARGET_M1.00 | 25 | 2321 | 4089 | 4065 | 2334 | 2321 | 192.864 | 192.042 | -2.591 | -32.785 | 3.797 | 0 | 3 | 7.053 | 530 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | reach_rate | FIXED_TARGET_M1.00 | 25 | 2321 | 4089 | 4065 | 2334 | 2321 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 530 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | realised_capture_bps | FIXED_TARGET_M1.00 | 25 | 2321 | 4089 | 4065 | 2334 | 2321 | 62.495 | 58.615 | 3.285 | -3.797 | 12.925 | 6 | 0 | 6.643 | 530 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | time_to_target | FIXED_TARGET_M1.00 | 25 | 2321 | 4089 | 4065 | 2334 | 2321 | 11.844 | 15.502 | 0.234 | -158.190 | 9.163 | 4 | 1 | 2.391 | 530 |
| MANAGEMENT | RANGE_SCALE | M0.75 | missed_excess_bps | FIXED_TARGET_M0.75 | 25 | 2676 | 5821 | 5799 | 2689 | 2676 | 174.038 | 182.632 | -8.216 | -107.522 | 4.517 | 0 | 13 | 9.864 | 605 |
| MANAGEMENT | RANGE_SCALE | M0.75 | reach_rate | FIXED_TARGET_M0.75 | 25 | 2676 | 5821 | 5799 | 2689 | 2676 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 605 |
| MANAGEMENT | RANGE_SCALE | M0.75 | realised_capture_bps | FIXED_TARGET_M0.75 | 25 | 2676 | 5821 | 5799 | 2689 | 2676 | 63.879 | 43.972 | 13.015 | -7.976 | 142.365 | 18 | 1 | 7.380 | 605 |
| MANAGEMENT | RANGE_SCALE | M0.75 | time_to_target | FIXED_TARGET_M0.75 | 25 | 2676 | 5821 | 5799 | 2689 | 2676 | 15.055 | 10.951 | 2.883 | -23.758 | 42.762 | 12 | 0 | 10.231 | 605 |
| MANAGEMENT | RANGE_SCALE | M1.00 | missed_excess_bps | FIXED_TARGET_M1.00 | 25 | 1704 | 3599 | 3575 | 1717 | 1704 | 164.414 | 179.898 | -16.168 | -157.981 | 5.330 | 2 | 15 | 10.958 | 442 |
| MANAGEMENT | RANGE_SCALE | M1.00 | reach_rate | FIXED_TARGET_M1.00 | 25 | 1704 | 3599 | 3575 | 1717 | 1704 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 442 |
| MANAGEMENT | RANGE_SCALE | M1.00 | realised_capture_bps | FIXED_TARGET_M1.00 | 25 | 1704 | 3599 | 3575 | 1717 | 1704 | 85.116 | 58.625 | 18.066 | -49.486 | 189.260 | 17 | 2 | 7.925 | 442 |
| MANAGEMENT | RANGE_SCALE | M1.00 | time_to_target | FIXED_TARGET_M1.00 | 25 | 1704 | 3599 | 3575 | 1717 | 1704 | 17.205 | 12.381 | 0.702 | -739.717 | 76.807 | 15 | 2 | 2.924 | 442 |
| MANAGEMENT | RANGE_SCALE | M1.50 | missed_excess_bps | FIXED_TARGET_M1.50 | 25 | 1136 | 2843 | 2820 | 1146 | 1136 | 156.415 | 235.389 | -22.289 | -291.262 | 15.249 | 0 | 12 | 26.041 | 384 |
| MANAGEMENT | RANGE_SCALE | M1.50 | reach_rate | FIXED_TARGET_M1.50 | 25 | 1136 | 2843 | 2820 | 1146 | 1136 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 384 |
| MANAGEMENT | RANGE_SCALE | M1.50 | realised_capture_bps | FIXED_TARGET_M1.50 | 25 | 1136 | 2843 | 2820 | 1146 | 1136 | 129.819 | 87.923 | 36.888 | -102.421 | 428.777 | 22 | 1 | 19.506 | 384 |
| MANAGEMENT | RANGE_SCALE | M1.50 | time_to_target | FIXED_TARGET_M1.50 | 25 | 1136 | 2843 | 2820 | 1146 | 1136 | 31.130 | 17.405 | 3.802 | -1471.167 | 901.817 | 14 | 1 | 6.302 | 384 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | missed_excess_bps | FIXED_TARGET_M1.00 | 25 | 2468 | 4767 | 4743 | 2480 | 2468 | 186.780 | 187.782 | 1.252 | -24.292 | 25.502 | 3 | 1 | 5.730 | 545 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | reach_rate | FIXED_TARGET_M1.00 | 25 | 2468 | 4767 | 4743 | 2480 | 2468 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 545 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | realised_capture_bps | FIXED_TARGET_M1.00 | 25 | 2468 | 4767 | 4743 | 2480 | 2468 | 58.313 | 58.620 | -3.037 | -18.590 | 21.645 | 1 | 7 | 4.373 | 545 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | time_to_target | FIXED_TARGET_M1.00 | 25 | 2468 | 4767 | 4743 | 2480 | 2468 | 13.908 | 16.014 | -0.147 | -133.406 | 1.414 | 1 | 5 | 2.167 | 545 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_075_HIGH_150 | missed_excess_bps | FIXED_TARGET_M1.00 | 25 | 2531 | 3896 | 3874 | 2548 | 2531 | 187.068 | 185.871 | 0.000 | -7.268 | 15.482 | 2 | 1 | 4.222 | 594 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_075_HIGH_150 | reach_rate | FIXED_TARGET_M1.00 | 25 | 2531 | 3896 | 3874 | 2548 | 2531 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 594 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_075_HIGH_150 | realised_capture_bps | FIXED_TARGET_M1.00 | 25 | 2531 | 3896 | 3874 | 2548 | 2531 | 57.311 | 58.615 | 0.644 | -15.482 | 11.086 | 2 | 1 | 4.113 | 594 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_075_HIGH_150 | time_to_target | FIXED_TARGET_M1.00 | 25 | 2531 | 3896 | 3874 | 2548 | 2531 | 26.288 | 26.528 | 0.000 | -7.645 | 125.634 | 2 | 1 | 1.443 | 594 |
| MANAGEMENT | SWING_SCALE | M0.75 | missed_excess_bps | FIXED_TARGET_M0.75 | 8 | 39 | 204 | 196 | 41 | 39 | 99.529 | 255.080 | -104.458 | -259.230 | 757.180 | 1 | 5 | 144.583 | 31 |
| MANAGEMENT | SWING_SCALE | M0.75 | reach_rate | FIXED_TARGET_M0.75 | 8 | 39 | 204 | 196 | 41 | 39 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 31 |
| MANAGEMENT | SWING_SCALE | M0.75 | realised_capture_bps | FIXED_TARGET_M0.75 | 8 | 39 | 204 | 196 | 41 | 39 | 666.604 | 33.300 | 635.199 | 267.961 | 1373.368 | 8 | 0 | 143.209 | 31 |
| MANAGEMENT | SWING_SCALE | M0.75 | time_to_target | FIXED_TARGET_M0.75 | 8 | 39 | 204 | 196 | 41 | 39 | 221.084 | 0.344 | 218.060 | 19.983 | 1866.017 | 8 | 0 | 187.415 | 31 |
| MANAGEMENT | SWING_SCALE | M1.00 | missed_excess_bps | FIXED_TARGET_M1.00 | 7 | 10 | 114 | 107 | 11 | 10 | 25.500 | 212.370 | -139.806 | -232.748 | 223.551 | 2 | 5 | 100.368 | 9 |
| MANAGEMENT | SWING_SCALE | M1.00 | reach_rate | FIXED_TARGET_M1.00 | 7 | 10 | 114 | 107 | 11 | 10 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 9 |
| MANAGEMENT | SWING_SCALE | M1.00 | realised_capture_bps | FIXED_TARGET_M1.00 | 7 | 10 | 114 | 107 | 11 | 10 | 1226.168 | 44.402 | 1180.914 | 353.398 | 1452.192 | 7 | 0 | 575.337 | 9 |
| MANAGEMENT | SWING_SCALE | M1.00 | time_to_target | FIXED_TARGET_M1.00 | 7 | 10 | 114 | 107 | 11 | 10 | 294.358 | 0.442 | 293.925 | 20.017 | 10517.283 | 7 | 0 | 565.204 | 9 |
| MANAGEMENT | SWING_SCALE | M1.50 | missed_excess_bps | FIXED_TARGET_M1.50 | 5 | 11 | 76 | 71 | 11 | 11 | 52.219 | 138.386 | -93.603 | -365.535 | 77.657 | 1 | 3 | 151.600 | 11 |
| MANAGEMENT | SWING_SCALE | M1.50 | reach_rate | FIXED_TARGET_M1.50 | 5 | 11 | 76 | 71 | 11 | 11 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 11 |
| MANAGEMENT | SWING_SCALE | M1.50 | realised_capture_bps | FIXED_TARGET_M1.50 | 5 | 11 | 76 | 71 | 11 | 11 | 876.123 | 67.404 | 809.319 | 758.002 | 2746.736 | 5 | 0 | 198.496 | 11 |
| MANAGEMENT | SWING_SCALE | M1.50 | time_to_target | FIXED_TARGET_M1.50 | 5 | 11 | 76 | 71 | 11 | 11 | 1308.733 | 8.383 | 1260.383 | 412.758 | 3872.850 | 5 | 0 | 515.633 | 11 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | missed_excess_bps | FIXED_TARGET_M1.00 | 25 | 2007 | 3684 | 3660 | 2019 | 2007 | 189.463 | 193.218 | -2.140 | -25.493 | 27.472 | 3 | 3 | 8.674 | 465 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | reach_rate | FIXED_TARGET_M1.00 | 25 | 2007 | 3684 | 3660 | 2019 | 2007 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 465 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | realised_capture_bps | FIXED_TARGET_M1.00 | 25 | 2007 | 3684 | 3660 | 2019 | 2007 | 55.558 | 58.615 | 2.877 | -29.440 | 33.928 | 6 | 5 | 7.493 | 465 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | time_to_target | FIXED_TARGET_M1.00 | 25 | 2007 | 3684 | 3660 | 2019 | 2007 | 12.031 | 15.144 | 0.056 | -71.775 | 8.967 | 6 | 5 | 2.793 | 465 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | missed_excess_bps | FIXED_TARGET_M1.00 | 42 | 2135 | 7067 | 7025 | 2151 | 2135 | 173.760 | 186.839 | -15.491 | -257.302 | 11.096 | 1 | 19 | 17.441 | 632 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | reach_rate | FIXED_TARGET_M1.00 | 42 | 2135 | 7067 | 7025 | 2151 | 2135 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 632 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | realised_capture_bps | FIXED_TARGET_M1.00 | 42 | 2135 | 7067 | 7025 | 2151 | 2135 | 80.209 | 54.380 | 20.876 | -10.105 | 268.507 | 27 | 0 | 15.701 | 632 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | time_to_target | FIXED_TARGET_M1.00 | 42 | 2135 | 7067 | 7025 | 2151 | 2135 | 13.410 | 10.907 | 1.353 | -239.144 | 125.741 | 16 | 0 | 2.188 | 632 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | missed_excess_bps | FIXED_TARGET_M1.00 | 18 | 1383 | 3247 | 3229 | 1391 | 1383 | 171.533 | 183.019 | -2.683 | -22.298 | 8.584 | 0 | 3 | 8.619 | 344 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | reach_rate | FIXED_TARGET_M1.00 | 18 | 1383 | 3247 | 3229 | 1391 | 1383 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 344 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | realised_capture_bps | FIXED_TARGET_M1.00 | 18 | 1383 | 3247 | 3229 | 1391 | 1383 | 57.019 | 55.293 | 6.427 | -8.584 | 15.225 | 4 | 0 | 7.741 | 344 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | time_to_target | FIXED_TARGET_M1.00 | 18 | 1383 | 3247 | 3229 | 1391 | 1383 | 8.857 | 11.126 | 0.614 | -242.923 | 9.510 | 3 | 1 | 3.716 | 344 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | missed_excess_bps | FIXED_TARGET_M1.00 | 50 | 9223 | 209053 | 209053 | 9271 | 9223 | 249.089 | 201.440 | 37.608 | 14.911 | 112.168 | 40 | 0 | 14.151 | 2068 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | reach_rate | FIXED_TARGET_M1.00 | 50 | 9223 | 209053 | 209053 | 9271 | 9223 | 0.511 | 1.000 | -0.489 | -0.667 | -0.375 | 0 | 48 | 0.079 | 2068 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | realised_capture_bps | FIXED_TARGET_M1.00 | 50 | 9223 | 209053 | 209053 | 9271 | 9223 | 0.354 | 58.620 | -50.221 | -134.097 | -23.994 | 0 | 46 | 12.112 | 2068 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | time_to_target | FIXED_TARGET_M1.00 | 50 | 9223 | 209053 | 209053 | 9271 | 9223 | 0.436 | 21.802 | -21.495 | -102.316 | 0.085 | 0 | 46 | 22.725 | 2068 |
**crypto / device_stop.parquet total_rows=14704**

**-- row census by arm_class x state --**

```text
arm_class                         state
FIXED_MANAGEMENT                  EVENT_UNDECIDED     276
                                  INCOMPLETE          600
                                  NO_EVENT            528
                                  NO_FEATURE          600
                                  ORDER_CREATED       600
MANAGEMENT                        EVENT_UNDECIDED    1000
                                  INCOMPLETE         2200
                                  NO_EVENT           1924
                                  NO_FEATURE         1000
                                  ORDER_CREATED      2200
MANAGEMENT_COMPONENT_COMBINATION  EVENT_UNDECIDED     336
                                  INCOMPLETE          600
                                  NO_EVENT            704
                                  ORDER_CREATED       800
MANAGEMENT_DEVICE_COMBINATION     EVENT_UNDECIDED     184
                                  INCOMPLETE          400
                                  NO_EVENT            352
                                  ORDER_CREATED       400
```

**-- rows with a defined estimate: 3084 of 14704**

**-- crypto / E_TOUCH / stop : adaptive-minus-fixed by component x setting --**

| arm_class | component | setting | metric | comparator | sym_rows | episode_n | entry_fill_n | close_n | common_fill_n | common_close_n | obs med | comp med | est med | est min | est max | CI>0 | CI<0 | mde med | eff_trade_blocks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIXED_MANAGEMENT | FIXED | M0.75 | adverse_excursion_bps | FIXED_STOP_M0.75 | 25 | 6736 | 6761 | 6736 | 6761 | 6736 | 68.875 | 68.875 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1023 |
| FIXED_MANAGEMENT | FIXED | M0.75 | loss_severity_bps | FIXED_STOP_M0.75 | 25 | 6736 | 6761 | 6736 | 6761 | 6736 | -44.001 | -44.001 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1023 |
| FIXED_MANAGEMENT | FIXED | M0.75 | recovery_after_stop_bps | FIXED_STOP_M0.75 | 25 | 6736 | 6761 | 6736 | 6761 | 6736 | 253.591 | 253.591 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1023 |
| FIXED_MANAGEMENT | FIXED | M0.75 | stop_rate | FIXED_STOP_M0.75 | 25 | 6736 | 6761 | 6736 | 6761 | 6736 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1023 |
| FIXED_MANAGEMENT | FIXED | M1.00 | adverse_excursion_bps | FIXED_STOP_M1.00 | 25 | 5747 | 5771 | 5747 | 5771 | 5747 | 85.002 | 85.002 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 995 |
| FIXED_MANAGEMENT | FIXED | M1.00 | loss_severity_bps | FIXED_STOP_M1.00 | 25 | 5747 | 5771 | 5747 | 5771 | 5747 | -58.633 | -58.633 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 995 |
| FIXED_MANAGEMENT | FIXED | M1.00 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 25 | 5747 | 5771 | 5747 | 5771 | 5747 | 252.339 | 252.339 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 995 |
| FIXED_MANAGEMENT | FIXED | M1.00 | stop_rate | FIXED_STOP_M1.00 | 25 | 5747 | 5771 | 5747 | 5771 | 5747 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 995 |
| FIXED_MANAGEMENT | FIXED | M1.50 | adverse_excursion_bps | FIXED_STOP_M1.50 | 25 | 2995 | 3019 | 2995 | 3019 | 2995 | 126.816 | 126.816 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 685 |
| FIXED_MANAGEMENT | FIXED | M1.50 | loss_severity_bps | FIXED_STOP_M1.50 | 25 | 2995 | 3019 | 2995 | 3019 | 2995 | -87.958 | -87.958 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 685 |
| FIXED_MANAGEMENT | FIXED | M1.50 | recovery_after_stop_bps | FIXED_STOP_M1.50 | 25 | 2995 | 3019 | 2995 | 3019 | 2995 | 279.346 | 279.346 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 685 |
| FIXED_MANAGEMENT | FIXED | M1.50 | stop_rate | FIXED_STOP_M1.50 | 25 | 2995 | 3019 | 2995 | 3019 | 2995 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 685 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | adverse_excursion_bps | FIXED_STOP_M1.00 | 25 | 4668 | 5405 | 5382 | 4683 | 4668 | 91.711 | 88.211 | 0.437 | -14.736 | 29.023 | 3 | 0 | 2.607 | 813 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | loss_severity_bps | FIXED_STOP_M1.00 | 25 | 4668 | 5405 | 5382 | 4683 | 4668 | -61.611 | -58.644 | -0.355 | -16.577 | 12.063 | 1 | 4 | 1.985 | 813 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 25 | 4668 | 5405 | 5382 | 4683 | 4668 | 261.097 | 284.323 | 0.000 | -27.902 | 64.921 | 0 | 0 | 3.924 | 813 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | stop_rate | FIXED_STOP_M1.00 | 25 | 4668 | 5405 | 5382 | 4683 | 4668 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 813 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | adverse_excursion_bps | FIXED_STOP_M1.00 | 25 | 4639 | 5339 | 5317 | 4651 | 4639 | 91.595 | 89.042 | 0.382 | -13.165 | 29.023 | 4 | 0 | 2.342 | 806 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | loss_severity_bps | FIXED_STOP_M1.00 | 25 | 4639 | 5339 | 5317 | 4651 | 4639 | -60.956 | -58.643 | -0.946 | -16.577 | 10.809 | 0 | 6 | 2.486 | 806 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 25 | 4639 | 5339 | 5317 | 4651 | 4639 | 261.212 | 284.323 | 0.000 | -29.874 | 64.921 | 1 | 0 | 3.504 | 806 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | stop_rate | FIXED_STOP_M1.00 | 25 | 4639 | 5339 | 5317 | 4651 | 4639 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 806 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | adverse_excursion_bps | FIXED_STOP_M1.00 | 25 | 2042 | 4010 | 3986 | 2049 | 2042 | 92.171 | 92.256 | 6.860 | -14.508 | 29.023 | 8 | 1 | 10.554 | 383 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | loss_severity_bps | FIXED_STOP_M1.00 | 25 | 2042 | 4010 | 3986 | 2049 | 2042 | -62.386 | -58.699 | -4.231 | -25.733 | 10.553 | 1 | 9 | 6.761 | 383 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 25 | 2042 | 4010 | 3986 | 2049 | 2042 | 268.076 | 293.587 | -1.575 | -68.130 | 64.921 | 0 | 1 | 18.291 | 383 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | stop_rate | FIXED_STOP_M1.00 | 25 | 2042 | 4010 | 3986 | 2049 | 2042 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 383 |
| MANAGEMENT | RANGE_SCALE | M0.75 | adverse_excursion_bps | FIXED_STOP_M0.75 | 25 | 2185 | 5144 | 5119 | 2194 | 2185 | 101.037 | 72.583 | 28.002 | -43.188 | 133.477 | 20 | 1 | 16.940 | 416 |
| MANAGEMENT | RANGE_SCALE | M0.75 | loss_severity_bps | FIXED_STOP_M0.75 | 25 | 2185 | 5144 | 5119 | 2194 | 2185 | -72.761 | -43.990 | -25.236 | -110.359 | 28.666 | 1 | 20 | 11.095 | 416 |
| MANAGEMENT | RANGE_SCALE | M0.75 | recovery_after_stop_bps | FIXED_STOP_M0.75 | 25 | 2185 | 5144 | 5119 | 2194 | 2185 | 216.810 | 276.205 | -2.786 | -263.089 | 45.364 | 1 | 4 | 26.987 | 416 |
| MANAGEMENT | RANGE_SCALE | M0.75 | stop_rate | FIXED_STOP_M0.75 | 25 | 2185 | 5144 | 5119 | 2194 | 2185 | 1.000 | 1.000 | 0.000 | -0.071 | 0.000 | 0 | 0 | 0.000 | 416 |
| MANAGEMENT | RANGE_SCALE | M1.00 | adverse_excursion_bps | FIXED_STOP_M1.00 | 25 | 1618 | 3542 | 3517 | 1625 | 1618 | 121.594 | 91.283 | 28.813 | -133.872 | 490.878 | 20 | 1 | 22.199 | 344 |
| MANAGEMENT | RANGE_SCALE | M1.00 | loss_severity_bps | FIXED_STOP_M1.00 | 25 | 1618 | 3542 | 3517 | 1625 | 1618 | -91.005 | -58.727 | -27.290 | -296.334 | 33.300 | 1 | 22 | 18.565 | 344 |
| MANAGEMENT | RANGE_SCALE | M1.00 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 25 | 1618 | 3542 | 3517 | 1625 | 1618 | 267.884 | 284.639 | -6.437 | -427.326 | 101.332 | 5 | 4 | 32.172 | 344 |
| MANAGEMENT | RANGE_SCALE | M1.00 | stop_rate | FIXED_STOP_M1.00 | 25 | 1618 | 3542 | 3517 | 1625 | 1618 | 1.000 | 1.000 | 0.000 | -0.333 | 0.000 | 0 | 0 | 0.000 | 344 |
| MANAGEMENT | RANGE_SCALE | M1.50 | adverse_excursion_bps | FIXED_STOP_M1.50 | 25 | 648 | 2275 | 2251 | 656 | 648 | 171.576 | 131.346 | 39.901 | -110.541 | 289.671 | 15 | 1 | 44.440 | 196 |
| MANAGEMENT | RANGE_SCALE | M1.50 | loss_severity_bps | FIXED_STOP_M1.50 | 25 | 648 | 2275 | 2251 | 656 | 648 | -145.255 | -87.910 | -40.015 | -222.088 | 78.336 | 1 | 18 | 29.013 | 196 |
| MANAGEMENT | RANGE_SCALE | M1.50 | recovery_after_stop_bps | FIXED_STOP_M1.50 | 23 | 646 | 2067 | 2045 | 654 | 646 | 256.478 | 359.003 | -12.440 | -223.356 | 102.022 | 3 | 3 | 85.497 | 194 |
| MANAGEMENT | RANGE_SCALE | M1.50 | stop_rate | FIXED_STOP_M1.50 | 25 | 648 | 2275 | 2251 | 656 | 648 | 1.000 | 1.000 | 0.000 | -0.034 | 0.000 | 0 | 0 | 0.000 | 196 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | adverse_excursion_bps | FIXED_STOP_M1.00 | 25 | 2258 | 4874 | 4852 | 2263 | 2258 | 84.841 | 87.096 | -2.888 | -25.935 | 29.023 | 1 | 7 | 7.918 | 391 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | loss_severity_bps | FIXED_STOP_M1.00 | 25 | 2258 | 4874 | 4852 | 2263 | 2258 | -56.055 | -58.699 | 2.237 | -16.577 | 13.450 | 9 | 1 | 4.638 | 391 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 25 | 2258 | 4874 | 4852 | 2263 | 2258 | 263.219 | 279.175 | -0.893 | -30.341 | 64.921 | 1 | 2 | 14.665 | 391 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | stop_rate | FIXED_STOP_M1.00 | 25 | 2258 | 4874 | 4852 | 2263 | 2258 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 391 |
| MANAGEMENT | SWING_SCALE | M0.75 | adverse_excursion_bps | FIXED_STOP_M0.75 | 11 | 45 | 249 | 238 | 46 | 45 | 869.353 | 63.510 | 811.830 | 210.602 | 1125.864 | 11 | 0 | 179.416 | 29 |
| MANAGEMENT | SWING_SCALE | M0.75 | loss_severity_bps | FIXED_STOP_M0.75 | 11 | 45 | 249 | 238 | 46 | 45 | -795.782 | -33.121 | -754.960 | -1104.378 | -217.268 | 0 | 11 | 172.076 | 29 |
| MANAGEMENT | SWING_SCALE | M0.75 | recovery_after_stop_bps | FIXED_STOP_M0.75 | 7 | 34 | 158 | 151 | 35 | 34 | 398.792 | 368.255 | 30.536 | -353.173 | 147.098 | 3 | 2 | 28.175 | 19 |
| MANAGEMENT | SWING_SCALE | M0.75 | stop_rate | FIXED_STOP_M0.75 | 11 | 45 | 249 | 238 | 46 | 45 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 29 |
| MANAGEMENT | SWING_SCALE | M1.00 | adverse_excursion_bps | FIXED_STOP_M1.00 | 11 | 49 | 264 | 253 | 52 | 49 | 965.331 | 59.316 | 895.210 | 321.446 | 2022.654 | 11 | 0 | 205.691 | 39 |
| MANAGEMENT | SWING_SCALE | M1.00 | loss_severity_bps | FIXED_STOP_M1.00 | 11 | 49 | 264 | 253 | 52 | 49 | -946.298 | -44.146 | -877.050 | -1990.291 | -315.049 | 0 | 11 | 144.680 | 39 |
| MANAGEMENT | SWING_SCALE | M1.00 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 5 | 35 | 171 | 166 | 35 | 35 | 322.986 | 371.923 | -70.664 | -145.324 | 568.174 | 2 | 1 | 90.405 | 26 |
| MANAGEMENT | SWING_SCALE | M1.00 | stop_rate | FIXED_STOP_M1.00 | 11 | 49 | 264 | 253 | 52 | 49 | 1.000 | 1.000 | 0.000 | -0.200 | 0.000 | 0 | 0 | 0.000 | 39 |
| MANAGEMENT | SWING_SCALE | M1.50 | adverse_excursion_bps | FIXED_STOP_M1.50 | 11 | 22 | 111 | 100 | 22 | 22 | 1370.180 | 95.779 | 1293.059 | 686.137 | 3141.667 | 11 | 0 | 149.608 | 20 |
| MANAGEMENT | SWING_SCALE | M1.50 | loss_severity_bps | FIXED_STOP_M1.50 | 11 | 22 | 111 | 100 | 22 | 22 | -1350.080 | -66.838 | -1261.345 | -2921.250 | -549.476 | 0 | 11 | 165.231 | 20 |
| MANAGEMENT | SWING_SCALE | M1.50 | stop_rate | FIXED_STOP_M1.50 | 11 | 22 | 111 | 100 | 22 | 22 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 20 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | adverse_excursion_bps | FIXED_STOP_M1.00 | 25 | 1832 | 4059 | 4036 | 1838 | 1832 | 100.198 | 92.256 | 5.622 | -28.023 | 35.600 | 7 | 3 | 10.910 | 381 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | loss_severity_bps | FIXED_STOP_M1.00 | 25 | 1832 | 4059 | 4036 | 1838 | 1832 | -55.206 | -58.721 | -2.254 | -23.248 | 18.447 | 5 | 7 | 8.994 | 381 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 25 | 1832 | 4059 | 4036 | 1838 | 1832 | 268.076 | 266.419 | -2.899 | -50.889 | 44.041 | 1 | 2 | 22.987 | 381 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | stop_rate | FIXED_STOP_M1.00 | 25 | 1832 | 4059 | 4036 | 1838 | 1832 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 381 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | adverse_excursion_bps | FIXED_STOP_M1.00 | 37 | 1197 | 4630 | 4594 | 1207 | 1197 | 127.786 | 88.600 | 40.796 | -48.195 | 368.871 | 21 | 2 | 26.491 | 312 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | loss_severity_bps | FIXED_STOP_M1.00 | 37 | 1197 | 4630 | 4594 | 1207 | 1197 | -93.815 | -58.720 | -33.098 | -294.919 | 43.828 | 2 | 23 | 22.666 | 312 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | recovery_after_stop_bps | FIXED_STOP_M1.00 | 37 | 1197 | 4630 | 4594 | 1207 | 1197 | 205.552 | 216.389 | -2.633 | -51.875 | 64.294 | 9 | 2 | 43.900 | 312 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | stop_rate | FIXED_STOP_M1.00 | 37 | 1197 | 4630 | 4594 | 1207 | 1197 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 312 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | adverse_excursion_bps | FIXED_STOP_M1.00 | 22 | 1456 | 3896 | 3875 | 1462 | 1456 | 87.757 | 87.736 | 8.384 | -33.631 | 233.969 | 9 | 1 | 11.170 | 285 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | loss_severity_bps | FIXED_STOP_M1.00 | 22 | 1456 | 3896 | 3875 | 1462 | 1456 | -59.257 | -57.376 | -8.409 | -58.021 | 21.810 | 1 | 12 | 8.712 | 285 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | recovery_after_stop_bps | FIXED_STOP_M1.00 | 21 | 1455 | 3714 | 3694 | 1461 | 1455 | 268.076 | 264.373 | -2.781 | -57.087 | 18.641 | 0 | 3 | 21.558 | 284 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | stop_rate | FIXED_STOP_M1.00 | 22 | 1456 | 3896 | 3875 | 1462 | 1456 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 285 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | adverse_excursion_bps | FIXED_TARGET_M1.00 | 50 | 7895 | 311694 | 311694 | 7937 | 7895 | 67.337 | 225.265 | -157.865 | -373.282 | 35.677 | 2 | 44 | 123.836 | 1490 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | stop_rate | FIXED_TARGET_M1.00 | 50 | 7895 | 311694 | 311694 | 7937 | 7895 | 0.498 | 0.000 | 0.498 | 0.364 | 0.659 | 48 | 0 | 0.071 | 1490 |
**-- crypto / E_CLOSE / stop : adaptive-minus-fixed by component x setting --**

| arm_class | component | setting | metric | comparator | sym_rows | episode_n | entry_fill_n | close_n | common_fill_n | common_close_n | obs med | comp med | est med | est min | est max | CI>0 | CI<0 | mde med | eff_trade_blocks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIXED_MANAGEMENT | FIXED | M0.75 | adverse_excursion_bps | FIXED_STOP_M0.75 | 25 | 5572 | 5597 | 5572 | 5597 | 5572 | 71.410 | 71.410 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1056 |
| FIXED_MANAGEMENT | FIXED | M0.75 | loss_severity_bps | FIXED_STOP_M0.75 | 25 | 5572 | 5597 | 5572 | 5597 | 5572 | -43.975 | -43.975 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1056 |
| FIXED_MANAGEMENT | FIXED | M0.75 | recovery_after_stop_bps | FIXED_STOP_M0.75 | 25 | 5572 | 5597 | 5572 | 5597 | 5572 | 219.286 | 219.286 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1056 |
| FIXED_MANAGEMENT | FIXED | M0.75 | stop_rate | FIXED_STOP_M0.75 | 25 | 5572 | 5597 | 5572 | 5597 | 5572 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1056 |
| FIXED_MANAGEMENT | FIXED | M1.00 | adverse_excursion_bps | FIXED_STOP_M1.00 | 25 | 4114 | 4138 | 4114 | 4138 | 4114 | 92.023 | 92.023 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 872 |
| FIXED_MANAGEMENT | FIXED | M1.00 | loss_severity_bps | FIXED_STOP_M1.00 | 25 | 4114 | 4138 | 4114 | 4138 | 4114 | -58.632 | -58.632 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 872 |
| FIXED_MANAGEMENT | FIXED | M1.00 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 25 | 4114 | 4138 | 4114 | 4138 | 4114 | 231.179 | 231.179 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 872 |
| FIXED_MANAGEMENT | FIXED | M1.00 | stop_rate | FIXED_STOP_M1.00 | 25 | 4114 | 4138 | 4114 | 4138 | 4114 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 872 |
| FIXED_MANAGEMENT | FIXED | M1.50 | adverse_excursion_bps | FIXED_STOP_M1.50 | 25 | 2701 | 2724 | 2701 | 2724 | 2701 | 139.408 | 139.408 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 690 |
| FIXED_MANAGEMENT | FIXED | M1.50 | loss_severity_bps | FIXED_STOP_M1.50 | 25 | 2701 | 2724 | 2701 | 2724 | 2701 | -87.918 | -87.918 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 690 |
| FIXED_MANAGEMENT | FIXED | M1.50 | recovery_after_stop_bps | FIXED_STOP_M1.50 | 25 | 2701 | 2724 | 2701 | 2724 | 2701 | 325.779 | 325.779 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 690 |
| FIXED_MANAGEMENT | FIXED | M1.50 | stop_rate | FIXED_STOP_M1.50 | 25 | 2701 | 2724 | 2701 | 2724 | 2701 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 690 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | adverse_excursion_bps | FIXED_STOP_M1.00 | 25 | 3152 | 3933 | 3908 | 3169 | 3152 | 95.815 | 93.984 | 0.730 | -14.062 | 17.033 | 2 | 0 | 3.155 | 673 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | loss_severity_bps | FIXED_STOP_M1.00 | 25 | 3152 | 3933 | 3908 | 3169 | 3152 | -57.732 | -58.616 | -1.359 | -16.490 | 9.951 | 0 | 6 | 2.141 | 673 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 25 | 3152 | 3933 | 3908 | 3169 | 3152 | 258.256 | 254.832 | 0.000 | -45.295 | 18.421 | 1 | 0 | 4.821 | 673 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | stop_rate | FIXED_STOP_M1.00 | 25 | 3152 | 3933 | 3908 | 3169 | 3152 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 673 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | adverse_excursion_bps | FIXED_STOP_M1.00 | 25 | 3147 | 3992 | 3967 | 3163 | 3147 | 95.978 | 93.462 | 2.489 | -11.851 | 44.119 | 4 | 0 | 3.395 | 672 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | loss_severity_bps | FIXED_STOP_M1.00 | 25 | 3147 | 3992 | 3967 | 3163 | 3147 | -60.963 | -58.630 | -2.332 | -21.440 | 8.186 | 0 | 8 | 2.641 | 672 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 25 | 3147 | 3992 | 3967 | 3163 | 3147 | 257.477 | 256.077 | 0.000 | -18.791 | 23.848 | 1 | 0 | 4.193 | 672 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | stop_rate | FIXED_STOP_M1.00 | 25 | 3147 | 3992 | 3967 | 3163 | 3147 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 672 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | adverse_excursion_bps | FIXED_STOP_M1.00 | 25 | 1848 | 3377 | 3352 | 1861 | 1848 | 102.708 | 94.535 | 7.010 | -17.415 | 44.119 | 6 | 1 | 9.264 | 430 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | loss_severity_bps | FIXED_STOP_M1.00 | 25 | 1848 | 3377 | 3352 | 1861 | 1848 | -65.963 | -58.689 | -6.419 | -24.027 | 10.299 | 1 | 9 | 8.027 | 430 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 25 | 1848 | 3377 | 3352 | 1861 | 1848 | 281.900 | 282.407 | 0.000 | -31.252 | 23.848 | 2 | 1 | 19.000 | 430 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | stop_rate | FIXED_STOP_M1.00 | 25 | 1848 | 3377 | 3352 | 1861 | 1848 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 430 |
| MANAGEMENT | RANGE_SCALE | M0.75 | adverse_excursion_bps | FIXED_STOP_M0.75 | 25 | 2385 | 4430 | 4405 | 2397 | 2385 | 96.666 | 74.827 | 26.692 | 1.817 | 258.090 | 20 | 0 | 10.203 | 511 |
| MANAGEMENT | RANGE_SCALE | M0.75 | loss_severity_bps | FIXED_STOP_M0.75 | 25 | 2385 | 4430 | 4405 | 2397 | 2385 | -76.053 | -43.964 | -24.832 | -220.115 | -2.115 | 0 | 21 | 9.302 | 511 |
| MANAGEMENT | RANGE_SCALE | M0.75 | recovery_after_stop_bps | FIXED_STOP_M0.75 | 25 | 2385 | 4430 | 4405 | 2397 | 2385 | 252.942 | 257.420 | 2.731 | -35.734 | 224.414 | 5 | 2 | 16.189 | 511 |
| MANAGEMENT | RANGE_SCALE | M0.75 | stop_rate | FIXED_STOP_M0.75 | 25 | 2385 | 4430 | 4405 | 2397 | 2385 | 1.000 | 1.000 | 0.000 | -0.007 | 0.000 | 0 | 0 | 0.000 | 511 |
| MANAGEMENT | RANGE_SCALE | M1.00 | adverse_excursion_bps | FIXED_STOP_M1.00 | 25 | 1001 | 3203 | 3178 | 1010 | 1001 | 119.945 | 102.650 | 23.273 | -67.891 | 490.878 | 21 | 1 | 14.683 | 245 |
| MANAGEMENT | RANGE_SCALE | M1.00 | loss_severity_bps | FIXED_STOP_M1.00 | 25 | 1001 | 3203 | 3178 | 1010 | 1001 | -91.158 | -58.639 | -23.967 | -296.334 | 51.353 | 1 | 22 | 13.471 | 245 |
| MANAGEMENT | RANGE_SCALE | M1.00 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 24 | 1000 | 3027 | 3003 | 1009 | 1000 | 243.342 | 240.391 | 5.132 | -427.326 | 282.570 | 6 | 4 | 25.889 | 244 |
| MANAGEMENT | RANGE_SCALE | M1.00 | stop_rate | FIXED_STOP_M1.00 | 25 | 1001 | 3203 | 3178 | 1010 | 1001 | 1.000 | 1.000 | 0.000 | -0.019 | 0.000 | 0 | 0 | 0.000 | 245 |
| MANAGEMENT | RANGE_SCALE | M1.50 | adverse_excursion_bps | FIXED_STOP_M1.50 | 25 | 975 | 2292 | 2268 | 984 | 975 | 162.122 | 128.764 | 54.607 | -110.541 | 754.490 | 19 | 1 | 33.732 | 279 |
| MANAGEMENT | RANGE_SCALE | M1.50 | loss_severity_bps | FIXED_STOP_M1.50 | 25 | 975 | 2292 | 2268 | 984 | 975 | -135.984 | -87.939 | -53.263 | -446.533 | 78.336 | 1 | 21 | 31.941 | 279 |
| MANAGEMENT | RANGE_SCALE | M1.50 | recovery_after_stop_bps | FIXED_STOP_M1.50 | 23 | 972 | 2172 | 2150 | 981 | 972 | 272.092 | 350.060 | -12.063 | -726.468 | 89.592 | 4 | 6 | 31.147 | 277 |
| MANAGEMENT | RANGE_SCALE | M1.50 | stop_rate | FIXED_STOP_M1.50 | 25 | 975 | 2292 | 2268 | 984 | 975 | 1.000 | 1.000 | 0.000 | -0.020 | 0.000 | 0 | 0 | 0.000 | 279 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | adverse_excursion_bps | FIXED_STOP_M1.00 | 25 | 2380 | 4206 | 4181 | 2394 | 2380 | 86.548 | 94.100 | -1.227 | -24.121 | 23.060 | 1 | 5 | 7.856 | 525 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | loss_severity_bps | FIXED_STOP_M1.00 | 25 | 2380 | 4206 | 4181 | 2394 | 2380 | -58.604 | -58.587 | 1.783 | -19.874 | 20.016 | 10 | 1 | 4.543 | 525 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 25 | 2380 | 4206 | 4181 | 2394 | 2380 | 236.913 | 232.612 | 2.621 | -23.081 | 38.665 | 1 | 2 | 18.823 | 525 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | stop_rate | FIXED_STOP_M1.00 | 25 | 2380 | 4206 | 4181 | 2394 | 2380 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 525 |
| MANAGEMENT | SWING_SCALE | M0.75 | adverse_excursion_bps | FIXED_STOP_M0.75 | 10 | 45 | 188 | 178 | 48 | 45 | 735.657 | 65.547 | 670.110 | 423.204 | 1970.067 | 10 | 0 | 186.379 | 33 |
| MANAGEMENT | SWING_SCALE | M0.75 | loss_severity_bps | FIXED_STOP_M0.75 | 10 | 45 | 188 | 178 | 48 | 45 | -705.178 | -43.140 | -665.918 | -1999.725 | -303.152 | 0 | 10 | 160.904 | 33 |
| MANAGEMENT | SWING_SCALE | M0.75 | recovery_after_stop_bps | FIXED_STOP_M0.75 | 5 | 25 | 67 | 62 | 27 | 25 | 641.053 | 270.381 | 62.724 | -125.240 | 641.073 | 3 | 1 | 20.842 | 16 |
| MANAGEMENT | SWING_SCALE | M0.75 | stop_rate | FIXED_STOP_M0.75 | 10 | 45 | 188 | 178 | 48 | 45 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 33 |
| MANAGEMENT | SWING_SCALE | M1.00 | adverse_excursion_bps | FIXED_STOP_M1.00 | 9 | 22 | 107 | 98 | 24 | 22 | 1008.820 | 82.667 | 932.597 | 426.614 | 2622.037 | 9 | 0 | 188.716 | 17 |
| MANAGEMENT | SWING_SCALE | M1.00 | loss_severity_bps | FIXED_STOP_M1.00 | 9 | 22 | 107 | 98 | 24 | 22 | -965.797 | -58.764 | -907.033 | -2665.109 | -391.596 | 0 | 9 | 265.827 | 17 |
| MANAGEMENT | SWING_SCALE | M1.00 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 3 | 14 | 56 | 53 | 14 | 14 | 441.511 | 258.831 | 182.680 | -352.012 | 816.543 | 2 | 1 | 0.000 | 9 |
| MANAGEMENT | SWING_SCALE | M1.00 | stop_rate | FIXED_STOP_M1.00 | 9 | 22 | 107 | 98 | 24 | 22 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 17 |
| MANAGEMENT | SWING_SCALE | M1.50 | adverse_excursion_bps | FIXED_STOP_M1.50 | 9 | 13 | 75 | 66 | 14 | 13 | 1837.438 | 91.241 | 1720.303 | 785.470 | 9861.942 | 9 | 0 | 333.331 | 11 |
| MANAGEMENT | SWING_SCALE | M1.50 | loss_severity_bps | FIXED_STOP_M1.50 | 9 | 13 | 75 | 66 | 14 | 13 | -1373.801 | -66.239 | -1307.562 | -9779.107 | -621.511 | 0 | 9 | 83.919 | 11 |
| MANAGEMENT | SWING_SCALE | M1.50 | stop_rate | FIXED_STOP_M1.50 | 9 | 13 | 75 | 66 | 14 | 13 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 11 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | adverse_excursion_bps | FIXED_STOP_M1.00 | 25 | 1837 | 3661 | 3637 | 1849 | 1837 | 95.891 | 97.553 | 5.818 | -53.473 | 37.066 | 5 | 4 | 11.869 | 423 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | loss_severity_bps | FIXED_STOP_M1.00 | 25 | 1837 | 3661 | 3637 | 1849 | 1837 | -56.806 | -58.609 | -5.658 | -12.445 | 19.706 | 4 | 7 | 7.637 | 423 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | recovery_after_stop_bps | FIXED_STOP_M1.00 | 24 | 1836 | 3501 | 3478 | 1848 | 1836 | 247.459 | 247.965 | -2.929 | -51.228 | 21.643 | 1 | 5 | 18.544 | 422 |
| MANAGEMENT | TAIL_RISK | STATE_LOW_075_HIGH_150 | stop_rate | FIXED_STOP_M1.00 | 25 | 1837 | 3661 | 3637 | 1849 | 1837 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 423 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | adverse_excursion_bps | FIXED_STOP_M1.00 | 39 | 1283 | 3890 | 3854 | 1300 | 1283 | 133.596 | 81.259 | 59.143 | -9.918 | 435.998 | 29 | 1 | 36.314 | 355 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | loss_severity_bps | FIXED_STOP_M1.00 | 39 | 1283 | 3890 | 3854 | 1300 | 1283 | -113.637 | -58.630 | -51.809 | -338.530 | 2.402 | 2 | 31 | 35.480 | 355 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | recovery_after_stop_bps | FIXED_STOP_M1.00 | 39 | 1283 | 3890 | 3854 | 1300 | 1283 | 269.134 | 260.698 | -0.760 | -169.216 | 128.240 | 3 | 7 | 47.571 | 355 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | stop_rate | FIXED_STOP_M1.00 | 39 | 1283 | 3890 | 3854 | 1300 | 1283 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 355 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | adverse_excursion_bps | FIXED_STOP_M1.00 | 24 | 1466 | 3222 | 3198 | 1478 | 1466 | 91.201 | 86.287 | 9.488 | -36.878 | 66.179 | 9 | 1 | 12.189 | 368 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | loss_severity_bps | FIXED_STOP_M1.00 | 24 | 1466 | 3222 | 3198 | 1478 | 1466 | -64.633 | -57.451 | -9.388 | -45.384 | 21.811 | 1 | 11 | 5.806 | 368 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | recovery_after_stop_bps | FIXED_STOP_M1.00 | 24 | 1466 | 3222 | 3198 | 1478 | 1466 | 268.377 | 272.950 | -0.367 | -78.278 | 34.068 | 3 | 1 | 23.090 | 368 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | stop_rate | FIXED_STOP_M1.00 | 24 | 1466 | 3222 | 3198 | 1478 | 1466 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 368 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | adverse_excursion_bps | FIXED_TARGET_M1.00 | 50 | 9223 | 209053 | 209053 | 9271 | 9223 | 68.429 | 202.947 | -133.124 | -368.341 | 119.109 | 2 | 40 | 97.156 | 2068 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | stop_rate | FIXED_TARGET_M1.00 | 50 | 9223 | 209053 | 209053 | 9271 | 9223 | 0.489 | 0.000 | 0.489 | 0.375 | 0.667 | 48 | 0 | 0.068 | 2068 |
**crypto / device_trail.parquet total_rows=8391**

**-- row census by arm_class x state --**

```text
arm_class                         state
FIXED_MANAGEMENT                  EVENT_UNDECIDED     207
                                  INCOMPLETE          450
                                  NO_EVENT            396
                                  NO_FEATURE          450
                                  ORDER_CREATED       450
MANAGEMENT                        EVENT_UNDECIDED     483
                                  INCOMPLETE         1050
                                  NO_EVENT            924
                                  NO_FEATURE          600
                                  ORDER_CREATED      1050
MANAGEMENT_COMPONENT_COMBINATION  EVENT_UNDECIDED     252
                                  INCOMPLETE          450
                                  NO_EVENT            528
                                  ORDER_CREATED       600
MANAGEMENT_DEVICE_COMBINATION     EVENT_UNDECIDED      69
                                  INCOMPLETE          150
                                  NO_EVENT            132
                                  ORDER_CREATED       150
```

**-- rows with a defined estimate: 1907 of 8391**

**-- crypto / E_TOUCH / trail : adaptive-minus-fixed by component x setting --**

| arm_class | component | setting | metric | comparator | sym_rows | episode_n | entry_fill_n | close_n | common_fill_n | common_close_n | obs med | comp med | est med | est min | est max | CI>0 | CI<0 | mde med | eff_trade_blocks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIXED_MANAGEMENT | FIXED | M0.75 | favourable_excursion_captured | FIXED_TRAIL_M0.75 | 25 | 6463 | 6485 | 6463 | 6485 | 6463 | 0.343 | 0.343 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 988 |
| FIXED_MANAGEMENT | FIXED | M0.75 | loss_tail_bps | FIXED_TRAIL_M0.75 | 25 | 6463 | 6485 | 6463 | 6485 | 6463 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 988 |
| FIXED_MANAGEMENT | FIXED | M0.75 | peak_giveback_bps | FIXED_TRAIL_M0.75 | 25 | 6463 | 6485 | 6463 | 6485 | 6463 | 58.748 | 58.748 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 988 |
| FIXED_MANAGEMENT | FIXED | M1.00 | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 25 | 4944 | 4967 | 4944 | 4967 | 4944 | 0.383 | 0.383 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 928 |
| FIXED_MANAGEMENT | FIXED | M1.00 | loss_tail_bps | FIXED_TRAIL_M1.00 | 25 | 4944 | 4967 | 4944 | 4967 | 4944 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 928 |
| FIXED_MANAGEMENT | FIXED | M1.00 | peak_giveback_bps | FIXED_TRAIL_M1.00 | 25 | 4944 | 4967 | 4944 | 4967 | 4944 | 68.777 | 68.777 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 928 |
| FIXED_MANAGEMENT | FIXED | M1.50 | favourable_excursion_captured | FIXED_TRAIL_M1.50 | 25 | 3282 | 3306 | 3282 | 3306 | 3282 | 0.389 | 0.389 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 828 |
| FIXED_MANAGEMENT | FIXED | M1.50 | loss_tail_bps | FIXED_TRAIL_M1.50 | 25 | 3282 | 3306 | 3282 | 3306 | 3282 | 0.082 | 0.082 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 828 |
| FIXED_MANAGEMENT | FIXED | M1.50 | peak_giveback_bps | FIXED_TRAIL_M1.50 | 25 | 3282 | 3306 | 3282 | 3306 | 3282 | 101.324 | 101.324 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 828 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 25 | 4085 | 5430 | 5406 | 4100 | 4085 | 0.370 | 0.382 | 0.000 | -0.044 | 0.013 | 0 | 5 | 0.012 | 774 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | loss_tail_bps | FIXED_TRAIL_M1.00 | 25 | 4085 | 5430 | 5406 | 4100 | 4085 | 0.000 | 0.000 | 0.000 | -0.809 | 2.858 | 0 | 0 | 0.000 | 774 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | peak_giveback_bps | FIXED_TRAIL_M1.00 | 25 | 4085 | 5430 | 5406 | 4100 | 4085 | 73.781 | 73.291 | 0.571 | -13.247 | 35.214 | 5 | 1 | 0.884 | 774 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 25 | 3966 | 5123 | 5099 | 3982 | 3966 | 0.377 | 0.382 | 0.000 | -0.055 | 0.023 | 0 | 3 | 0.014 | 744 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | loss_tail_bps | FIXED_TRAIL_M1.00 | 25 | 3966 | 5123 | 5099 | 3982 | 3966 | 0.000 | 0.000 | 0.000 | -0.220 | 2.858 | 0 | 0 | 0.000 | 744 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | peak_giveback_bps | FIXED_TRAIL_M1.00 | 25 | 3966 | 5123 | 5099 | 3982 | 3966 | 73.781 | 73.291 | 0.490 | -1.245 | 35.214 | 5 | 0 | 0.884 | 744 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 25 | 2180 | 5011 | 4988 | 2191 | 2180 | 0.366 | 0.379 | -0.003 | -0.053 | 0.055 | 0 | 2 | 0.049 | 442 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | loss_tail_bps | FIXED_TRAIL_M1.00 | 25 | 2180 | 5011 | 4988 | 2191 | 2180 | 0.000 | 0.000 | 0.000 | -4.118 | 6.160 | 0 | 0 | 1.933 | 442 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | peak_giveback_bps | FIXED_TRAIL_M1.00 | 25 | 2180 | 5011 | 4988 | 2191 | 2180 | 75.959 | 72.284 | 4.752 | -2.572 | 23.499 | 4 | 0 | 8.880 | 442 |
| MANAGEMENT | RANGE_SCALE | M0.75 | favourable_excursion_captured | FIXED_TRAIL_M0.75 | 25 | 2812 | 6517 | 6493 | 2823 | 2812 | 0.384 | 0.330 | 0.044 | -0.198 | 0.232 | 9 | 1 | 0.056 | 538 |
| MANAGEMENT | RANGE_SCALE | M0.75 | loss_tail_bps | FIXED_TRAIL_M0.75 | 25 | 2812 | 6517 | 6493 | 2823 | 2812 | 0.633 | 0.000 | 0.902 | -0.000 | 20.166 | 4 | 0 | 0.902 | 538 |
| MANAGEMENT | RANGE_SCALE | M0.75 | peak_giveback_bps | FIXED_TRAIL_M0.75 | 25 | 2812 | 6517 | 6493 | 2823 | 2812 | 71.175 | 56.469 | 9.386 | 0.231 | 105.578 | 16 | 0 | 8.136 | 538 |
| MANAGEMENT | RANGE_SCALE | M1.00 | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 25 | 1719 | 3435 | 3412 | 1734 | 1719 | 0.385 | 0.381 | 0.005 | -0.169 | 0.152 | 4 | 2 | 0.054 | 403 |
| MANAGEMENT | RANGE_SCALE | M1.00 | loss_tail_bps | FIXED_TRAIL_M1.00 | 25 | 1719 | 3435 | 3412 | 1734 | 1719 | 0.589 | 0.000 | 0.000 | -9.843 | 34.863 | 1 | 0 | 4.195 | 403 |
| MANAGEMENT | RANGE_SCALE | M1.00 | peak_giveback_bps | FIXED_TRAIL_M1.00 | 25 | 1719 | 3435 | 3412 | 1734 | 1719 | 94.351 | 69.443 | 20.948 | 0.929 | 133.988 | 16 | 0 | 12.341 | 403 |
| MANAGEMENT | RANGE_SCALE | M1.50 | favourable_excursion_captured | FIXED_TRAIL_M1.50 | 25 | 896 | 2566 | 2543 | 902 | 896 | 0.402 | 0.387 | -0.003 | -0.095 | 0.176 | 4 | 2 | 0.061 | 321 |
| MANAGEMENT | RANGE_SCALE | M1.50 | loss_tail_bps | FIXED_TRAIL_M1.50 | 25 | 896 | 2566 | 2543 | 902 | 896 | 4.554 | 3.864 | 1.014 | -13.257 | 137.086 | 5 | 1 | 14.185 | 321 |
| MANAGEMENT | RANGE_SCALE | M1.50 | peak_giveback_bps | FIXED_TRAIL_M1.50 | 25 | 896 | 2566 | 2543 | 902 | 896 | 139.657 | 102.063 | 30.885 | -3.038 | 386.437 | 21 | 0 | 18.343 | 321 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 25 | 2338 | 5219 | 5197 | 2352 | 2338 | 0.341 | 0.379 | -0.026 | -0.122 | 0.087 | 1 | 5 | 0.053 | 480 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | loss_tail_bps | FIXED_TRAIL_M1.00 | 25 | 2338 | 5219 | 5197 | 2352 | 2338 | 0.000 | 0.000 | 0.000 | -3.842 | 3.371 | 0 | 2 | 2.499 | 480 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | peak_giveback_bps | FIXED_TRAIL_M1.00 | 25 | 2338 | 5219 | 5197 | 2352 | 2338 | 73.216 | 75.167 | -1.540 | -17.258 | 14.358 | 2 | 7 | 6.504 | 480 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 28 | 1025 | 4124 | 4098 | 1042 | 1025 | 0.395 | 0.400 | 0.003 | -0.447 | 0.262 | 2 | 6 | 0.087 | 297 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | loss_tail_bps | FIXED_TRAIL_M1.00 | 28 | 1025 | 4124 | 4098 | 1042 | 1025 | 1.163 | 2.017 | 0.000 | -32.096 | 28.782 | 2 | 3 | 14.305 | 297 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | peak_giveback_bps | FIXED_TRAIL_M1.00 | 28 | 1025 | 4124 | 4098 | 1042 | 1025 | 105.047 | 62.929 | 24.249 | -22.569 | 107.652 | 17 | 2 | 20.046 | 297 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 16 | 1308 | 3649 | 3633 | 1314 | 1308 | 0.360 | 0.386 | -0.038 | -0.138 | 0.082 | 1 | 2 | 0.052 | 278 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | loss_tail_bps | FIXED_TRAIL_M1.00 | 16 | 1308 | 3649 | 3633 | 1314 | 1308 | 0.000 | 0.000 | 0.000 | -23.313 | 0.157 | 0 | 2 | 3.283 | 278 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | peak_giveback_bps | FIXED_TRAIL_M1.00 | 16 | 1308 | 3649 | 3633 | 1314 | 1308 | 62.983 | 57.515 | 4.049 | -18.865 | 20.971 | 3 | 0 | 7.042 | 278 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 13 | 1121 | 40897 | 40897 | 1130 | 1121 | -1.766 | 0.389 | -2.155 | -7.148 | -0.294 | 0 | 12 | 1.610 | 245 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | loss_tail_bps | FIXED_TRAIL_M1.00 | 25 | 3594 | 85079 | 85079 | 3612 | 3594 | -268.007 | 0.000 | -268.007 | -1369.790 | -58.349 | 0 | 23 | 178.008 | 835 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | peak_giveback_bps | FIXED_TRAIL_M1.00 | 25 | 3594 | 85079 | 85079 | 3612 | 3594 | 124.266 | 70.123 | 48.460 | 9.650 | 295.626 | 25 | 0 | 20.958 | 835 |
**-- crypto / E_CLOSE / trail : adaptive-minus-fixed by component x setting --**

| arm_class | component | setting | metric | comparator | sym_rows | episode_n | entry_fill_n | close_n | common_fill_n | common_close_n | obs med | comp med | est med | est min | est max | CI>0 | CI<0 | mde med | eff_trade_blocks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIXED_MANAGEMENT | FIXED | M0.75 | favourable_excursion_captured | FIXED_TRAIL_M0.75 | 25 | 6253 | 6275 | 6253 | 6275 | 6253 | 0.345 | 0.345 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1167 |
| FIXED_MANAGEMENT | FIXED | M0.75 | loss_tail_bps | FIXED_TRAIL_M0.75 | 25 | 6253 | 6275 | 6253 | 6275 | 6253 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1167 |
| FIXED_MANAGEMENT | FIXED | M0.75 | peak_giveback_bps | FIXED_TRAIL_M0.75 | 25 | 6253 | 6275 | 6253 | 6275 | 6253 | 55.267 | 55.267 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1167 |
| FIXED_MANAGEMENT | FIXED | M1.00 | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 25 | 4853 | 4877 | 4853 | 4877 | 4853 | 0.389 | 0.389 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1101 |
| FIXED_MANAGEMENT | FIXED | M1.00 | loss_tail_bps | FIXED_TRAIL_M1.00 | 25 | 4853 | 4877 | 4853 | 4877 | 4853 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1101 |
| FIXED_MANAGEMENT | FIXED | M1.00 | peak_giveback_bps | FIXED_TRAIL_M1.00 | 25 | 4853 | 4877 | 4853 | 4877 | 4853 | 69.225 | 69.225 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1101 |
| FIXED_MANAGEMENT | FIXED | M1.50 | favourable_excursion_captured | FIXED_TRAIL_M1.50 | 25 | 3371 | 3395 | 3371 | 3395 | 3371 | 0.389 | 0.389 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 951 |
| FIXED_MANAGEMENT | FIXED | M1.50 | loss_tail_bps | FIXED_TRAIL_M1.50 | 25 | 3371 | 3395 | 3371 | 3395 | 3371 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 951 |
| FIXED_MANAGEMENT | FIXED | M1.50 | peak_giveback_bps | FIXED_TRAIL_M1.50 | 25 | 3371 | 3395 | 3371 | 3395 | 3371 | 100.329 | 100.329 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 951 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 25 | 3886 | 4733 | 4709 | 3907 | 3886 | 0.371 | 0.385 | -0.001 | -0.094 | 0.015 | 0 | 3 | 0.020 | 886 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | loss_tail_bps | FIXED_TRAIL_M1.00 | 25 | 3886 | 4733 | 4709 | 3907 | 3886 | 0.000 | 0.000 | 0.000 | -1.155 | 0.360 | 0 | 0 | 0.046 | 886 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_075_HIGH_150 | peak_giveback_bps | FIXED_TRAIL_M1.00 | 25 | 3886 | 4733 | 4709 | 3907 | 3886 | 72.944 | 70.782 | 0.906 | -13.989 | 16.604 | 5 | 1 | 1.533 | 886 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 25 | 3898 | 4909 | 4885 | 3916 | 3898 | 0.371 | 0.386 | 0.000 | -0.075 | 0.019 | 1 | 3 | 0.015 | 894 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | loss_tail_bps | FIXED_TRAIL_M1.00 | 25 | 3898 | 4909 | 4885 | 3916 | 3898 | 0.000 | 0.000 | 0.000 | -1.397 | 0.340 | 0 | 0 | 0.438 | 894 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_075_HIGH_150 | peak_giveback_bps | FIXED_TRAIL_M1.00 | 25 | 3898 | 4909 | 4885 | 3916 | 3898 | 74.636 | 71.569 | 1.250 | -9.502 | 20.249 | 6 | 0 | 1.652 | 894 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 25 | 2381 | 4505 | 4481 | 2394 | 2381 | 0.354 | 0.381 | -0.014 | -0.075 | 0.032 | 0 | 5 | 0.044 | 582 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | loss_tail_bps | FIXED_TRAIL_M1.00 | 25 | 2381 | 4505 | 4481 | 2394 | 2381 | 0.000 | 0.000 | 0.000 | -2.997 | 6.965 | 0 | 0 | 2.694 | 582 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_075_HIGH_150 | peak_giveback_bps | FIXED_TRAIL_M1.00 | 25 | 2381 | 4505 | 4481 | 2394 | 2381 | 76.686 | 72.029 | 3.240 | -4.291 | 20.249 | 6 | 1 | 6.410 | 582 |
| MANAGEMENT | RANGE_SCALE | M0.75 | favourable_excursion_captured | FIXED_TRAIL_M0.75 | 24 | 2705 | 6108 | 6088 | 2716 | 2705 | 0.380 | 0.319 | 0.049 | -0.084 | 0.271 | 10 | 0 | 0.044 | 630 |
| MANAGEMENT | RANGE_SCALE | M0.75 | loss_tail_bps | FIXED_TRAIL_M0.75 | 25 | 2774 | 6356 | 6335 | 2785 | 2774 | 0.721 | 0.000 | 0.721 | -0.000 | 20.004 | 9 | 0 | 0.585 | 646 |
| MANAGEMENT | RANGE_SCALE | M0.75 | peak_giveback_bps | FIXED_TRAIL_M0.75 | 25 | 2774 | 6356 | 6335 | 2785 | 2774 | 69.634 | 59.481 | 10.154 | -4.747 | 108.589 | 15 | 0 | 6.444 | 646 |
| MANAGEMENT | RANGE_SCALE | M1.00 | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 24 | 1944 | 3784 | 3762 | 1957 | 1944 | 0.389 | 0.383 | 0.004 | -0.228 | 0.316 | 1 | 2 | 0.050 | 543 |
| MANAGEMENT | RANGE_SCALE | M1.00 | loss_tail_bps | FIXED_TRAIL_M1.00 | 25 | 2002 | 3977 | 3954 | 2016 | 2002 | 0.713 | 0.000 | 0.000 | -0.701 | 69.098 | 3 | 0 | 4.526 | 560 |
| MANAGEMENT | RANGE_SCALE | M1.00 | peak_giveback_bps | FIXED_TRAIL_M1.00 | 25 | 2002 | 3977 | 3954 | 2016 | 2002 | 92.256 | 74.125 | 16.909 | -6.562 | 166.195 | 15 | 0 | 10.795 | 560 |
| MANAGEMENT | RANGE_SCALE | M1.50 | favourable_excursion_captured | FIXED_TRAIL_M1.50 | 24 | 946 | 2741 | 2719 | 953 | 946 | 0.388 | 0.388 | 0.015 | -0.101 | 0.266 | 3 | 4 | 0.061 | 355 |
| MANAGEMENT | RANGE_SCALE | M1.50 | loss_tail_bps | FIXED_TRAIL_M1.50 | 25 | 959 | 2846 | 2823 | 966 | 959 | 7.677 | 1.916 | 3.054 | -38.937 | 765.912 | 6 | 2 | 7.027 | 360 |
| MANAGEMENT | RANGE_SCALE | M1.50 | peak_giveback_bps | FIXED_TRAIL_M1.50 | 25 | 959 | 2846 | 2823 | 966 | 959 | 129.409 | 102.323 | 34.604 | -2.065 | 386.437 | 22 | 0 | 19.882 | 360 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 25 | 2790 | 5154 | 5130 | 2805 | 2790 | 0.348 | 0.376 | -0.025 | -0.115 | 0.054 | 0 | 4 | 0.045 | 652 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | loss_tail_bps | FIXED_TRAIL_M1.00 | 25 | 2790 | 5154 | 5130 | 2805 | 2790 | 0.000 | 0.000 | 0.000 | -2.829 | 0.925 | 0 | 0 | 1.667 | 652 |
| MANAGEMENT | SHOCK | STATE_LOW_075_HIGH_150 | peak_giveback_bps | FIXED_TRAIL_M1.00 | 25 | 2790 | 5154 | 5130 | 2805 | 2790 | 69.423 | 70.384 | -1.552 | -17.383 | 20.113 | 3 | 5 | 4.827 | 652 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 34 | 1533 | 4554 | 4520 | 1548 | 1533 | 0.380 | 0.401 | -0.014 | -0.096 | 0.079 | 0 | 2 | 0.079 | 472 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | loss_tail_bps | FIXED_TRAIL_M1.00 | 34 | 1533 | 4554 | 4520 | 1548 | 1533 | 1.593 | 1.538 | -0.031 | -26.623 | 38.111 | 2 | 0 | 8.560 | 472 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | peak_giveback_bps | FIXED_TRAIL_M1.00 | 34 | 1533 | 4554 | 4520 | 1548 | 1533 | 91.407 | 64.939 | 20.460 | -28.473 | 172.930 | 20 | 1 | 14.776 | 472 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 17 | 1303 | 3358 | 3341 | 1311 | 1303 | 0.344 | 0.384 | -0.015 | -0.147 | 0.054 | 0 | 5 | 0.057 | 346 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | loss_tail_bps | FIXED_TRAIL_M1.00 | 17 | 1303 | 3358 | 3341 | 1311 | 1303 | 0.000 | 0.000 | 0.000 | -3.739 | 10.225 | 0 | 0 | 3.184 | 346 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | peak_giveback_bps | FIXED_TRAIL_M1.00 | 17 | 1303 | 3358 | 3341 | 1311 | 1303 | 72.084 | 71.526 | 2.640 | -9.702 | 27.226 | 4 | 1 | 7.353 | 346 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | favourable_excursion_captured | FIXED_TRAIL_M1.00 | 12 | 1370 | 31026 | 31026 | 1381 | 1370 | -1.306 | 0.379 | -1.674 | -8.699 | -0.413 | 0 | 11 | 1.684 | 363 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | loss_tail_bps | FIXED_TRAIL_M1.00 | 25 | 3889 | 67363 | 67363 | 3911 | 3889 | -303.881 | 0.000 | -303.881 | -1012.675 | -69.749 | 0 | 24 | 163.310 | 1014 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | peak_giveback_bps | FIXED_TRAIL_M1.00 | 25 | 3889 | 67363 | 67363 | 3911 | 3889 | 128.315 | 70.152 | 69.321 | 16.132 | 397.701 | 25 | 0 | 22.011 | 1014 |
**crypto / device_hold.parquet total_rows=10140**

**-- row census by arm_class x state --**

```text
arm_class                         state
FIXED_MANAGEMENT                  EVENT_UNDECIDED     276
                                  INCOMPLETE          600
                                  NO_EVENT            528
                                  NO_FEATURE          600
                                  ORDER_CREATED       600
MANAGEMENT                        EVENT_UNDECIDED     424
                                  INCOMPLETE          800
                                  NO_EVENT            876
                                  ORDER_CREATED      1000
MANAGEMENT_COMPONENT_COMBINATION  EVENT_UNDECIDED     424
                                  INCOMPLETE          800
                                  NO_EVENT            876
                                  ORDER_CREATED      1000
MANAGEMENT_DEVICE_COMBINATION     EVENT_UNDECIDED     184
                                  INCOMPLETE          400
                                  NO_EVENT            352
                                  ORDER_CREATED       400
```

**-- rows with a defined estimate: 2406 of 10140**

**-- crypto / E_TOUCH / hold : adaptive-minus-fixed by component x setting --**

| arm_class | component | setting | metric | comparator | sym_rows | episode_n | entry_fill_n | close_n | common_fill_n | common_close_n | obs med | comp med | est med | est min | est max | CI>0 | CI<0 | mde med | eff_trade_blocks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIXED_MANAGEMENT | FIXED | B12 | decay_bps | FIXED_HOLD_B12 | 25 | 17277 | 17280 | 17277 | 17280 | 17277 | 292.154 | 292.154 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 9634 |
| FIXED_MANAGEMENT | FIXED | B12 | holding_efficiency | FIXED_HOLD_B12 | 5 | 2036 | 2036 | 2036 | 2036 | 2036 | -5.633 | -5.633 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 1141 |
| FIXED_MANAGEMENT | FIXED | B12 | opportunity_duration | FIXED_HOLD_B12 | 25 | 17277 | 17280 | 17277 | 17280 | 17277 | 5.330 | 5.330 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 9634 |
| FIXED_MANAGEMENT | FIXED | B12 | outcome_by_time_bps | FIXED_HOLD_B12 | 25 | 17277 | 17280 | 17277 | 17280 | 17277 | -2.652 | -2.652 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 9634 |
| FIXED_MANAGEMENT | FIXED | B2 | decay_bps | FIXED_HOLD_B2 | 25 | 68844 | 68844 | 68844 | 68844 | 68844 | 120.134 | 120.134 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 9637 |
| FIXED_MANAGEMENT | FIXED | B2 | holding_efficiency | FIXED_HOLD_B2 | 2 | 514 | 514 | 514 | 514 | 514 | -5.254 | -5.254 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 72 |
| FIXED_MANAGEMENT | FIXED | B2 | opportunity_duration | FIXED_HOLD_B2 | 25 | 68844 | 68844 | 68844 | 68844 | 68844 | 0.895 | 0.895 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 9637 |
| FIXED_MANAGEMENT | FIXED | B2 | outcome_by_time_bps | FIXED_HOLD_B2 | 25 | 68844 | 68844 | 68844 | 68844 | 68844 | 2.300 | 2.300 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 9637 |
| FIXED_MANAGEMENT | FIXED | B4 | decay_bps | FIXED_HOLD_B4 | 25 | 43077 | 43077 | 43077 | 43077 | 43077 | 174.353 | 174.353 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 9637 |
| FIXED_MANAGEMENT | FIXED | B4 | holding_efficiency | FIXED_HOLD_B4 | 2 | 319 | 319 | 319 | 319 | 319 | -2.543 | -2.543 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 73 |
| FIXED_MANAGEMENT | FIXED | B4 | opportunity_duration | FIXED_HOLD_B4 | 25 | 43077 | 43077 | 43077 | 43077 | 43077 | 1.781 | 1.781 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 9637 |
| FIXED_MANAGEMENT | FIXED | B4 | outcome_by_time_bps | FIXED_HOLD_B4 | 25 | 43077 | 43077 | 43077 | 43077 | 43077 | 2.373 | 2.373 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 9637 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_4_HIGH_12 | decay_bps | FIXED_HOLD_B4 | 25 | 9180 | 17011 | 17008 | 9181 | 9180 | 168.974 | 139.554 | 30.592 | 0.000 | 87.429 | 22 | 0 | 10.625 | 3882 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_4_HIGH_12 | holding_efficiency | FIXED_HOLD_B4 | 7 | 1175 | 2355 | 2355 | 1175 | 1175 | -1.858 | -1.840 | 0.027 | -0.054 | 0.134 | 0 | 0 | 0.276 | 513 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_4_HIGH_12 | opportunity_duration | FIXED_HOLD_B4 | 25 | 9180 | 17011 | 17008 | 9181 | 9180 | 2.728 | 1.774 | 0.971 | 0.000 | 1.604 | 23 | 0 | 0.233 | 3882 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_4_HIGH_12 | outcome_by_time_bps | FIXED_HOLD_B4 | 25 | 9180 | 17011 | 17008 | 9181 | 9180 | 3.017 | 1.949 | 0.465 | -9.988 | 74.749 | 0 | 0 | 16.141 | 3882 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_4_HIGH_12 | decay_bps | FIXED_HOLD_B4 | 25 | 9054 | 16881 | 16876 | 9055 | 9054 | 169.571 | 135.765 | 31.384 | 14.288 | 141.673 | 23 | 0 | 11.556 | 3828 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_4_HIGH_12 | holding_efficiency | FIXED_HOLD_B4 | 5 | 690 | 1277 | 1276 | 690 | 690 | -1.854 | -2.090 | -0.046 | -5.302 | 0.236 | 0 | 0 | 0.452 | 298 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_4_HIGH_12 | opportunity_duration | FIXED_HOLD_B4 | 25 | 9054 | 16881 | 16876 | 9055 | 9054 | 2.766 | 1.797 | 0.939 | 0.079 | 1.433 | 24 | 0 | 0.233 | 3828 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_4_HIGH_12 | outcome_by_time_bps | FIXED_HOLD_B4 | 25 | 9054 | 16881 | 16876 | 9055 | 9054 | 1.510 | 3.081 | -1.804 | -27.701 | 110.280 | 3 | 1 | 15.609 | 3828 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_4_HIGH_12 | decay_bps | FIXED_HOLD_B4 | 25 | 15131 | 28312 | 28307 | 15132 | 15131 | 179.428 | 145.783 | 37.153 | 16.753 | 116.782 | 24 | 0 | 9.937 | 6347 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_4_HIGH_12 | holding_efficiency | FIXED_HOLD_B4 | 3 | 125 | 264 | 264 | 125 | 125 | -4.248 | -4.115 | -0.520 | -1.624 | -0.133 | 0 | 0 | 1.071 | 54 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_4_HIGH_12 | opportunity_duration | FIXED_HOLD_B4 | 25 | 15131 | 28312 | 28307 | 15132 | 15131 | 2.744 | 1.751 | 0.973 | 0.654 | 1.339 | 25 | 0 | 0.185 | 6347 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_4_HIGH_12 | outcome_by_time_bps | FIXED_HOLD_B4 | 25 | 15131 | 28312 | 28307 | 15132 | 15131 | -0.110 | 3.398 | -2.975 | -10.121 | 67.548 | 1 | 0 | 12.498 | 6347 |
| MANAGEMENT | SHOCK | STATE_SHOCK_2 | decay_bps | FIXED_HOLD_B4 | 25 | 20233 | 68676 | 68676 | 20233 | 20233 | 113.946 | 167.432 | -49.672 | -265.948 | -22.982 | 0 | 25 | 9.308 | 9496 |
| MANAGEMENT | SHOCK | STATE_SHOCK_2 | holding_efficiency | FIXED_HOLD_B4 | 4 | 322 | 1152 | 1152 | 322 | 322 | -1.835 | -1.964 | 0.589 | -0.323 | 1.372 | 1 | 0 | 0.873 | 161 |
| MANAGEMENT | SHOCK | STATE_SHOCK_2 | opportunity_duration | FIXED_HOLD_B4 | 25 | 20233 | 68676 | 68676 | 20233 | 20233 | 0.889 | 1.794 | -0.918 | -0.992 | -0.597 | 0 | 25 | 0.075 | 9496 |
| MANAGEMENT | SHOCK | STATE_SHOCK_2 | outcome_by_time_bps | FIXED_HOLD_B4 | 25 | 20233 | 68676 | 68676 | 20233 | 20233 | 3.886 | 4.171 | -0.394 | -113.550 | 30.054 | 0 | 0 | 10.036 | 9496 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_4_HIGH_12 | decay_bps | FIXED_HOLD_B4 | 25 | 15093 | 26050 | 26042 | 15096 | 15093 | 190.717 | 168.681 | 27.681 | 0.000 | 192.375 | 23 | 0 | 8.238 | 6082 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_4_HIGH_12 | holding_efficiency | FIXED_HOLD_B4 | 6 | 1039 | 1920 | 1918 | 1040 | 1039 | -1.996 | -1.924 | -0.102 | -0.302 | 0.082 | 0 | 0 | 0.324 | 431 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_4_HIGH_12 | opportunity_duration | FIXED_HOLD_B4 | 25 | 15093 | 26050 | 26042 | 15096 | 15093 | 2.649 | 1.806 | 0.883 | 0.000 | 1.535 | 23 | 0 | 0.182 | 6082 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_4_HIGH_12 | outcome_by_time_bps | FIXED_HOLD_B4 | 25 | 15093 | 26050 | 26042 | 15096 | 15093 | 2.321 | 2.984 | 0.000 | -45.202 | 33.568 | 1 | 0 | 10.842 | 6082 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_4_HIGH_12 | decay_bps | FIXED_HOLD_B4 | 100 | 48458 | 88254 | 88233 | 48464 | 48458 | 178.982 | 150.194 | 31.681 | 0.000 | 192.375 | 92 | 0 | 10.417 | 20139 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_4_HIGH_12 | holding_efficiency | FIXED_HOLD_B4 | 21 | 3029 | 5816 | 5813 | 3030 | 3029 | -2.263 | -2.120 | -0.046 | -5.302 | 0.236 | 0 | 0 | 0.332 | 1296 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_4_HIGH_12 | opportunity_duration | FIXED_HOLD_B4 | 100 | 48458 | 88254 | 88233 | 48464 | 48458 | 2.737 | 1.776 | 0.952 | 0.000 | 1.604 | 95 | 0 | 0.217 | 20139 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_4_HIGH_12 | outcome_by_time_bps | FIXED_HOLD_B4 | 100 | 48458 | 88254 | 88233 | 48464 | 48458 | 1.358 | 2.838 | -0.956 | -45.202 | 110.280 | 5 | 1 | 13.644 | 20139 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_4_HIGH_12 | decay_bps | FIXED_HOLD_B4 | 25 | 15095 | 31549 | 31545 | 15096 | 15095 | 164.952 | 152.886 | 18.084 | -42.902 | 77.137 | 18 | 0 | 10.197 | 6741 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_4_HIGH_12 | holding_efficiency | FIXED_HOLD_B4 | 5 | 519 | 1260 | 1259 | 519 | 519 | -2.054 | -2.528 | 0.048 | -0.302 | 0.609 | 1 | 0 | 0.284 | 250 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_4_HIGH_12 | opportunity_duration | FIXED_HOLD_B4 | 25 | 15095 | 31549 | 31545 | 15096 | 15095 | 2.435 | 1.730 | 0.670 | 0.111 | 1.090 | 23 | 0 | 0.178 | 6741 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_4_HIGH_12 | outcome_by_time_bps | FIXED_HOLD_B4 | 25 | 15095 | 31549 | 31545 | 15096 | 15095 | -0.476 | 2.830 | -2.167 | -13.069 | 64.627 | 0 | 1 | 11.921 | 6741 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | decay_bps | FIXED_TARGET_M1.00 | 25 | 3948 | 155869 | 155869 | 3969 | 3948 | 71.398 | 29.925 | 40.717 | 7.088 | 196.524 | 24 | 0 | 18.403 | 745 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | decay_bps | FIXED_TRAIL_M1.00 | 25 | 3594 | 85079 | 85079 | 3612 | 3594 | 124.266 | 70.123 | 48.460 | 9.650 | 295.626 | 25 | 0 | 20.958 | 835 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | holding_efficiency | FIXED_TARGET_M1.00 | 6 | 266 | 18454 | 18454 | 272 | 266 | -1.496 | 0.673 | -2.203 | -4.172 | -0.402 | 0 | 6 | 1.055 | 53 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | holding_efficiency | FIXED_TRAIL_M1.00 | 13 | 1121 | 40897 | 40897 | 1130 | 1121 | -1.766 | 0.389 | -2.155 | -7.148 | -0.294 | 0 | 12 | 1.610 | 245 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | opportunity_duration | FIXED_TARGET_M1.00 | 25 | 3948 | 155869 | 155869 | 3969 | 3948 | 0.261 | 24.454 | -24.190 | -143.210 | 0.105 | 1 | 23 | 31.885 | 745 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | opportunity_duration | FIXED_TRAIL_M1.00 | 25 | 3594 | 85079 | 85079 | 3612 | 3594 | 0.896 | 24.663 | -23.745 | -118.416 | 0.332 | 1 | 21 | 33.055 | 835 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | outcome_by_time_bps | FIXED_TARGET_M1.00 | 25 | 3948 | 155869 | 155869 | 3969 | 3948 | 1.346 | 58.614 | -53.946 | -148.823 | 28.982 | 0 | 23 | 13.998 | 745 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | outcome_by_time_bps | FIXED_TRAIL_M1.00 | 25 | 3594 | 85079 | 85079 | 3612 | 3594 | 10.902 | 63.484 | -45.275 | -169.948 | 21.209 | 1 | 19 | 31.006 | 835 |
**-- crypto / E_CLOSE / hold : adaptive-minus-fixed by component x setting --**

| arm_class | component | setting | metric | comparator | sym_rows | episode_n | entry_fill_n | close_n | common_fill_n | common_close_n | obs med | comp med | est med | est min | est max | CI>0 | CI<0 | mde med | eff_trade_blocks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIXED_MANAGEMENT | FIXED | B12 | decay_bps | FIXED_HOLD_B12 | 25 | 16445 | 16453 | 16445 | 16453 | 16445 | 312.023 | 312.023 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 9626 |
| FIXED_MANAGEMENT | FIXED | B12 | holding_efficiency | FIXED_HOLD_B12 | 7 | 1102 | 1104 | 1102 | 1104 | 1102 | -3.480 | -3.480 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 644 |
| FIXED_MANAGEMENT | FIXED | B12 | opportunity_duration | FIXED_HOLD_B12 | 25 | 16445 | 16453 | 16445 | 16453 | 16445 | 5.298 | 5.298 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 9626 |
| FIXED_MANAGEMENT | FIXED | B12 | outcome_by_time_bps | FIXED_HOLD_B12 | 25 | 16445 | 16453 | 16445 | 16453 | 16445 | -0.575 | -0.575 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 9626 |
| FIXED_MANAGEMENT | FIXED | B2 | decay_bps | FIXED_HOLD_B2 | 25 | 57058 | 57058 | 57058 | 57058 | 57058 | 123.050 | 123.050 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 9636 |
| FIXED_MANAGEMENT | FIXED | B2 | holding_efficiency | FIXED_HOLD_B2 | 1 | 156 | 156 | 156 | 156 | 156 | -3.748 | -3.748 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 27 |
| FIXED_MANAGEMENT | FIXED | B2 | opportunity_duration | FIXED_HOLD_B2 | 25 | 57058 | 57058 | 57058 | 57058 | 57058 | 0.885 | 0.885 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 9636 |
| FIXED_MANAGEMENT | FIXED | B2 | outcome_by_time_bps | FIXED_HOLD_B2 | 25 | 57058 | 57058 | 57058 | 57058 | 57058 | 3.151 | 3.151 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 9636 |
| FIXED_MANAGEMENT | FIXED | B4 | decay_bps | FIXED_HOLD_B4 | 25 | 38211 | 38212 | 38211 | 38212 | 38211 | 175.559 | 175.559 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 9636 |
| FIXED_MANAGEMENT | FIXED | B4 | holding_efficiency | FIXED_HOLD_B4 | 4 | 967 | 967 | 967 | 967 | 967 | -4.173 | -4.173 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 244 |
| FIXED_MANAGEMENT | FIXED | B4 | opportunity_duration | FIXED_HOLD_B4 | 25 | 38211 | 38212 | 38211 | 38212 | 38211 | 1.793 | 1.793 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 9636 |
| FIXED_MANAGEMENT | FIXED | B4 | outcome_by_time_bps | FIXED_HOLD_B4 | 25 | 38211 | 38212 | 38211 | 38212 | 38211 | 2.578 | 2.578 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 9636 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_4_HIGH_12 | decay_bps | FIXED_HOLD_B4 | 25 | 11180 | 15452 | 15449 | 11182 | 11180 | 180.561 | 135.315 | 35.507 | 0.000 | 86.945 | 21 | 0 | 10.954 | 4787 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_4_HIGH_12 | holding_efficiency | FIXED_HOLD_B4 | 5 | 533 | 725 | 724 | 534 | 533 | -3.933 | -3.352 | -0.277 | -1.412 | 0.127 | 0 | 1 | 0.290 | 212 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_4_HIGH_12 | opportunity_duration | FIXED_HOLD_B4 | 25 | 11180 | 15452 | 15449 | 11182 | 11180 | 2.860 | 1.805 | 1.029 | 0.000 | 1.960 | 24 | 0 | 0.218 | 4787 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_LOW_4_HIGH_12 | outcome_by_time_bps | FIXED_HOLD_B4 | 25 | 11180 | 15452 | 15449 | 11182 | 11180 | -3.670 | 0.294 | -0.346 | -17.849 | 63.916 | 0 | 4 | 15.221 | 4787 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_4_HIGH_12 | decay_bps | FIXED_HOLD_B4 | 25 | 11097 | 15254 | 15251 | 11100 | 11097 | 181.578 | 138.614 | 36.654 | 6.448 | 72.502 | 23 | 0 | 13.870 | 4765 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_4_HIGH_12 | holding_efficiency | FIXED_HOLD_B4 | 5 | 513 | 707 | 706 | 514 | 513 | -3.909 | -3.423 | -0.095 | -1.170 | 3.213 | 0 | 0 | 0.624 | 211 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_4_HIGH_12 | opportunity_duration | FIXED_HOLD_B4 | 25 | 11097 | 15254 | 15251 | 11100 | 11097 | 2.928 | 1.773 | 1.062 | 0.658 | 1.759 | 25 | 0 | 0.227 | 4765 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_LOW_4_HIGH_12 | outcome_by_time_bps | FIXED_HOLD_B4 | 25 | 11097 | 15254 | 15251 | 11100 | 11097 | -0.286 | 0.774 | -0.708 | -12.885 | 58.663 | 0 | 1 | 15.248 | 4765 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_4_HIGH_12 | decay_bps | FIXED_HOLD_B4 | 25 | 18674 | 25580 | 25577 | 18677 | 18674 | 206.180 | 167.241 | 39.613 | 19.963 | 88.235 | 24 | 0 | 10.310 | 7959 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_4_HIGH_12 | holding_efficiency | FIXED_HOLD_B4 | 4 | 474 | 643 | 642 | 475 | 474 | -4.187 | -5.143 | -0.057 | -0.658 | 2.571 | 0 | 0 | 1.607 | 193 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_4_HIGH_12 | opportunity_duration | FIXED_HOLD_B4 | 25 | 18674 | 25580 | 25577 | 18677 | 18674 | 2.852 | 1.778 | 1.088 | 0.767 | 1.295 | 25 | 0 | 0.178 | 7959 |
| MANAGEMENT | LEVEL_NOW | STATE_LOW_4_HIGH_12 | outcome_by_time_bps | FIXED_HOLD_B4 | 25 | 18674 | 25580 | 25577 | 18677 | 18674 | 4.122 | 2.858 | -0.635 | -16.955 | 86.495 | 0 | 0 | 12.776 | 7959 |
| MANAGEMENT | SHOCK | STATE_SHOCK_2 | decay_bps | FIXED_HOLD_B4 | 25 | 25063 | 56920 | 56920 | 25064 | 25063 | 120.001 | 171.484 | -50.205 | -147.678 | -21.716 | 0 | 25 | 8.452 | 9553 |
| MANAGEMENT | SHOCK | STATE_SHOCK_2 | holding_efficiency | FIXED_HOLD_B4 | 3 | 282 | 694 | 694 | 282 | 282 | -4.508 | -6.481 | 0.113 | -0.131 | 1.973 | 0 | 0 | 1.104 | 115 |
| MANAGEMENT | SHOCK | STATE_SHOCK_2 | opportunity_duration | FIXED_HOLD_B4 | 25 | 25063 | 56920 | 56920 | 25064 | 25063 | 0.894 | 1.803 | -0.909 | -1.134 | -0.577 | 0 | 25 | 0.068 | 9553 |
| MANAGEMENT | SHOCK | STATE_SHOCK_2 | outcome_by_time_bps | FIXED_HOLD_B4 | 25 | 25063 | 56920 | 56920 | 25064 | 25063 | 2.456 | 4.163 | -0.132 | -22.330 | 56.070 | 1 | 2 | 8.726 | 9553 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_4_HIGH_12 | decay_bps | FIXED_HOLD_B4 | 25 | 17481 | 23672 | 23664 | 17486 | 17481 | 200.303 | 172.431 | 34.300 | -21.148 | 414.479 | 23 | 0 | 8.457 | 7464 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_4_HIGH_12 | holding_efficiency | FIXED_HOLD_B4 | 5 | 1234 | 1688 | 1687 | 1234 | 1234 | -2.868 | -2.245 | -0.236 | -0.623 | 0.108 | 0 | 1 | 0.462 | 531 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_4_HIGH_12 | opportunity_duration | FIXED_HOLD_B4 | 25 | 17481 | 23672 | 23664 | 17486 | 17481 | 2.824 | 1.828 | 1.049 | 0.678 | 1.710 | 23 | 0 | 0.190 | 7464 |
| MANAGEMENT | SWING_GT_CUR | STATE_LOW_4_HIGH_12 | outcome_by_time_bps | FIXED_HOLD_B4 | 25 | 17481 | 23672 | 23664 | 17486 | 17481 | 5.073 | 2.482 | -1.550 | -382.507 | 78.006 | 1 | 0 | 10.182 | 7464 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_4_HIGH_12 | decay_bps | FIXED_HOLD_B4 | 100 | 58432 | 79958 | 79941 | 58445 | 58432 | 189.091 | 154.504 | 36.342 | -21.148 | 414.479 | 91 | 0 | 10.948 | 24975 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_4_HIGH_12 | holding_efficiency | FIXED_HOLD_B4 | 19 | 2754 | 3763 | 3759 | 2757 | 2754 | -3.638 | -3.352 | -0.111 | -1.412 | 3.213 | 0 | 2 | 0.543 | 1147 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_4_HIGH_12 | opportunity_duration | FIXED_HOLD_B4 | 100 | 58432 | 79958 | 79941 | 58445 | 58432 | 2.856 | 1.796 | 1.055 | 0.000 | 1.960 | 97 | 0 | 0.212 | 24975 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_4_HIGH_12 | outcome_by_time_bps | FIXED_HOLD_B4 | 100 | 58432 | 79958 | 79941 | 58445 | 58432 | 1.927 | 1.789 | -0.823 | -382.507 | 86.495 | 1 | 5 | 14.085 | 24975 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_4_HIGH_12 | decay_bps | FIXED_HOLD_B4 | 25 | 19325 | 28745 | 28742 | 19328 | 19325 | 193.665 | 168.293 | 21.801 | 4.622 | 116.852 | 17 | 0 | 10.714 | 8319 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_4_HIGH_12 | holding_efficiency | FIXED_HOLD_B4 | 5 | 565 | 875 | 875 | 565 | 565 | -4.459 | -3.187 | -0.054 | -1.272 | 1.687 | 0 | 1 | 1.046 | 235 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_4_HIGH_12 | opportunity_duration | FIXED_HOLD_B4 | 25 | 19325 | 28745 | 28742 | 19328 | 19325 | 2.548 | 1.787 | 0.751 | 0.523 | 1.253 | 25 | 0 | 0.169 | 8319 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_4_HIGH_12 | outcome_by_time_bps | FIXED_HOLD_B4 | 25 | 19325 | 28745 | 28742 | 19328 | 19325 | 4.306 | 3.173 | 0.006 | -11.295 | 73.905 | 1 | 0 | 12.725 | 8319 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | decay_bps | FIXED_TARGET_M1.00 | 25 | 4612 | 104534 | 104534 | 4636 | 4612 | 72.530 | 26.181 | 36.421 | 8.026 | 162.619 | 23 | 0 | 13.218 | 1034 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | decay_bps | FIXED_TRAIL_M1.00 | 25 | 3889 | 67363 | 67363 | 3911 | 3889 | 128.315 | 70.152 | 69.321 | 16.132 | 397.701 | 25 | 0 | 22.011 | 1014 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | holding_efficiency | FIXED_TARGET_M1.00 | 7 | 478 | 14832 | 14832 | 485 | 478 | -1.387 | 0.693 | -2.076 | -3.477 | -1.599 | 0 | 7 | 1.049 | 86 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | holding_efficiency | FIXED_TRAIL_M1.00 | 12 | 1370 | 31026 | 31026 | 1381 | 1370 | -1.306 | 0.379 | -1.674 | -8.699 | -0.413 | 0 | 11 | 1.684 | 363 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | opportunity_duration | FIXED_TARGET_M1.00 | 25 | 4612 | 104534 | 104534 | 4636 | 4612 | 0.263 | 20.713 | -20.502 | -98.383 | -0.043 | 0 | 23 | 22.436 | 1034 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | opportunity_duration | FIXED_TRAIL_M1.00 | 25 | 3889 | 67363 | 67363 | 3911 | 3889 | 0.837 | 22.481 | -21.516 | -110.512 | 0.464 | 1 | 21 | 21.092 | 1014 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | outcome_by_time_bps | FIXED_TARGET_M1.00 | 25 | 4612 | 104534 | 104534 | 4636 | 4612 | 0.336 | 58.620 | -50.221 | -134.097 | -23.994 | 0 | 23 | 12.239 | 1034 |
| MANAGEMENT_DEVICE_COMBINATION | RANGE_SCALE | M1.00 | outcome_by_time_bps | FIXED_TRAIL_M1.00 | 25 | 3889 | 67363 | 67363 | 3911 | 3889 | 6.910 | 61.792 | -54.098 | -129.652 | 5.546 | 0 | 20 | 30.258 | 1014 |
**crypto / device_size.parquet total_rows=9548**

**-- row census by arm_class x state --**

```text
arm_class                         state
FIXED_MANAGEMENT                  EVENT_UNDECIDED      92
                                  INCOMPLETE          200
                                  NO_EVENT            176
                                  NO_FEATURE          200
                                  ORDER_CREATED       200
MANAGEMENT                        EVENT_UNDECIDED     552
                                  INCOMPLETE         1200
                                  NO_EVENT           1056
                                  NO_FEATURE         1200
                                  ORDER_CREATED      1200
MANAGEMENT_COMPONENT_COMBINATION  EVENT_UNDECIDED     368
                                  INCOMPLETE          800
                                  NO_EVENT            704
                                  NO_FEATURE          800
                                  ORDER_CREATED       800
```

**-- rows with a defined estimate: 4037 of 9548**

**-- crypto / E_TOUCH / size : adaptive-minus-fixed by component x setting --**

| arm_class | component | setting | metric | comparator | sym_rows | episode_n | entry_fill_n | close_n | common_fill_n | common_close_n | obs med | comp med | est med | est min | est max | CI>0 | CI<0 | mde med | eff_trade_blocks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIXED_MANAGEMENT | FIXED | UNIT | concentration | FIXED_SIZE_UNIT | 117 | 43077 | 43077 | 43077 | 43077 | 43077 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 9637 |
| FIXED_MANAGEMENT | FIXED | UNIT | drawdown_bps | FIXED_SIZE_UNIT | 25 | 43077 | 43077 | 43077 | 43077 | 43077 | -8427.629 | -8427.629 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 9637 |
| FIXED_MANAGEMENT | FIXED | UNIT | risk_dispersion | FIXED_SIZE_UNIT | 25 | 43077 | 43077 | 43077 | 43077 | 43077 | 242.744 | 242.744 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 9637 |
| FIXED_MANAGEMENT | FIXED | UNIT | tail_loss_bps | FIXED_SIZE_UNIT | 25 | 43077 | 43077 | 43077 | 43077 | 43077 | 489.183 | 489.183 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 9637 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_HALVE_HIGH | concentration | FIXED_SIZE_UNIT | 117 | 43077 | 43077 | 43077 | 43077 | 43077 | 0.000 | 0.000 | 0.000 | -0.011 | 0.009 | 12 | 0 | 0.001 | 9637 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_HALVE_HIGH | drawdown_bps | FIXED_SIZE_UNIT | 25 | 43077 | 43077 | 43077 | 43077 | 43077 | -7529.371 | -8427.629 | 1087.276 | -700.003 | 8171.019 | 1 | 0 | 2365.122 | 9637 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_HALVE_HIGH | risk_dispersion | FIXED_SIZE_UNIT | 25 | 43077 | 43077 | 43077 | 43077 | 43077 | 225.512 | 242.744 | -22.339 | -83.791 | -1.035 | 0 | 24 | 7.066 | 9637 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_HALVE_HIGH | tail_loss_bps | FIXED_SIZE_UNIT | 25 | 43077 | 43077 | 43077 | 43077 | 43077 | 448.879 | 489.183 | -33.651 | -174.387 | 0.000 | 0 | 17 | 34.293 | 9637 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_HALVE_HIGH | concentration | FIXED_SIZE_UNIT | 117 | 43077 | 43077 | 43077 | 43077 | 43077 | 0.000 | 0.000 | 0.000 | -0.011 | 0.010 | 12 | 0 | 0.001 | 9637 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_HALVE_HIGH | drawdown_bps | FIXED_SIZE_UNIT | 25 | 43077 | 43077 | 43077 | 43077 | 43077 | -7260.786 | -8427.629 | 1238.298 | -901.459 | 8371.293 | 1 | 0 | 2742.103 | 9637 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_HALVE_HIGH | risk_dispersion | FIXED_SIZE_UNIT | 25 | 43077 | 43077 | 43077 | 43077 | 43077 | 220.585 | 242.744 | -23.836 | -81.129 | -9.728 | 0 | 25 | 9.159 | 9637 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_HALVE_HIGH | tail_loss_bps | FIXED_SIZE_UNIT | 25 | 43077 | 43077 | 43077 | 43077 | 43077 | 446.796 | 489.183 | -33.651 | -181.748 | 0.000 | 0 | 18 | 39.165 | 9637 |
| MANAGEMENT | LEVEL_NOW | STATE_HALVE_HIGH | concentration | FIXED_SIZE_UNIT | 117 | 43077 | 43077 | 43077 | 43077 | 43077 | 0.000 | 0.000 | 0.000 | -0.014 | 0.029 | 3 | 0 | 0.003 | 9637 |
| MANAGEMENT | LEVEL_NOW | STATE_HALVE_HIGH | drawdown_bps | FIXED_SIZE_UNIT | 25 | 43077 | 43077 | 43077 | 43077 | 43077 | -5995.980 | -8427.629 | 2431.650 | 76.899 | 10230.470 | 6 | 0 | 3283.724 | 9637 |
| MANAGEMENT | LEVEL_NOW | STATE_HALVE_HIGH | risk_dispersion | FIXED_SIZE_UNIT | 25 | 43077 | 43077 | 43077 | 43077 | 43077 | 187.789 | 242.744 | -59.108 | -165.524 | -25.969 | 0 | 25 | 17.762 | 9637 |
| MANAGEMENT | LEVEL_NOW | STATE_HALVE_HIGH | tail_loss_bps | FIXED_SIZE_UNIT | 25 | 43077 | 43077 | 43077 | 43077 | 43077 | 399.357 | 489.183 | -103.391 | -409.961 | 0.000 | 0 | 23 | 49.083 | 9637 |
| MANAGEMENT | RANGE_SCALE | SCALE_NORMALISED | concentration | FIXED_SIZE_UNIT | 117 | 43077 | 43077 | 43077 | 43077 | 43077 | 0.000 | 0.000 | 0.000 | -0.005 | 0.024 | 2 | 3 | 0.004 | 9637 |
| MANAGEMENT | RANGE_SCALE | SCALE_NORMALISED | drawdown_bps | FIXED_SIZE_UNIT | 25 | 43077 | 43077 | 43077 | 43077 | 43077 | -8901.699 | -8427.629 | -314.105 | -4283.985 | 3382.766 | 1 | 2 | 3996.028 | 9637 |
| MANAGEMENT | RANGE_SCALE | SCALE_NORMALISED | risk_dispersion | FIXED_SIZE_UNIT | 25 | 43077 | 43077 | 43077 | 43077 | 43077 | 243.006 | 242.744 | 5.187 | -282.295 | 92.577 | 9 | 7 | 22.920 | 9637 |
| MANAGEMENT | RANGE_SCALE | SCALE_NORMALISED | tail_loss_bps | FIXED_SIZE_UNIT | 25 | 43077 | 43077 | 43077 | 43077 | 43077 | 487.312 | 489.183 | 11.923 | -462.027 | 111.965 | 5 | 3 | 56.531 | 9637 |
| MANAGEMENT | SHOCK | STATE_HALVE_HIGH | concentration | FIXED_SIZE_UNIT | 117 | 43077 | 43077 | 43077 | 43077 | 43077 | 0.000 | 0.000 | 0.000 | -0.004 | 0.021 | 7 | 0 | 0.001 | 9637 |
| MANAGEMENT | SHOCK | STATE_HALVE_HIGH | drawdown_bps | FIXED_SIZE_UNIT | 25 | 43077 | 43077 | 43077 | 43077 | 43077 | -6509.845 | -8427.629 | 1026.627 | -1136.451 | 9682.235 | 1 | 0 | 2375.875 | 9637 |
| MANAGEMENT | SHOCK | STATE_HALVE_HIGH | risk_dispersion | FIXED_SIZE_UNIT | 25 | 43077 | 43077 | 43077 | 43077 | 43077 | 213.367 | 242.744 | -26.694 | -158.902 | -8.606 | 0 | 25 | 9.993 | 9637 |
| MANAGEMENT | SHOCK | STATE_HALVE_HIGH | tail_loss_bps | FIXED_SIZE_UNIT | 25 | 43077 | 43077 | 43077 | 43077 | 43077 | 435.572 | 489.183 | -42.815 | -332.913 | 0.000 | 0 | 19 | 33.629 | 9637 |
| MANAGEMENT | TAIL_RISK | STATE_HALVE_HIGH | concentration | FIXED_SIZE_UNIT | 117 | 43077 | 43077 | 43077 | 43077 | 43077 | 0.000 | 0.000 | 0.000 | -0.013 | 0.012 | 5 | 1 | 0.003 | 9637 |
| MANAGEMENT | TAIL_RISK | STATE_HALVE_HIGH | drawdown_bps | FIXED_SIZE_UNIT | 25 | 43077 | 43077 | 43077 | 43077 | 43077 | -6573.591 | -8427.629 | 2471.486 | 76.899 | 13991.221 | 5 | 0 | 3146.063 | 9637 |
| MANAGEMENT | TAIL_RISK | STATE_HALVE_HIGH | risk_dispersion | FIXED_SIZE_UNIT | 25 | 43077 | 43077 | 43077 | 43077 | 43077 | 187.766 | 242.744 | -55.181 | -441.003 | -29.078 | 0 | 25 | 15.878 | 9637 |
| MANAGEMENT | TAIL_RISK | STATE_HALVE_HIGH | tail_loss_bps | FIXED_SIZE_UNIT | 25 | 43077 | 43077 | 43077 | 43077 | 43077 | 388.363 | 489.183 | -101.975 | -656.146 | -58.651 | 0 | 23 | 53.840 | 9637 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | concentration | FIXED_SIZE_UNIT | 351 | 129231 | 129231 | 129231 | 129231 | 129231 | 0.000 | 0.000 | 0.000 | -0.014 | 0.052 | 23 | 4 | 0.003 | 28911 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | drawdown_bps | FIXED_SIZE_UNIT | 75 | 129231 | 129231 | 129231 | 129231 | 129231 | -7391.217 | -8427.629 | 890.363 | -2940.150 | 10801.215 | 3 | 0 | 3891.505 | 28911 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | risk_dispersion | FIXED_SIZE_UNIT | 75 | 129231 | 129231 | 129231 | 129231 | 129231 | 222.716 | 242.744 | -22.093 | -367.855 | 15.151 | 2 | 50 | 16.165 | 28911 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | tail_loss_bps | FIXED_SIZE_UNIT | 75 | 129231 | 129231 | 129231 | 129231 | 129231 | 435.718 | 489.183 | -35.013 | -927.096 | 339.873 | 1 | 25 | 52.859 | 28911 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | concentration | FIXED_SIZE_UNIT | 117 | 43077 | 43077 | 43077 | 43077 | 43077 | 0.000 | 0.000 | 0.000 | -0.012 | 0.036 | 4 | 0 | 0.003 | 9637 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | drawdown_bps | FIXED_SIZE_UNIT | 25 | 43077 | 43077 | 43077 | 43077 | 43077 | -5401.045 | -8427.629 | 2615.161 | 15.562 | 14172.826 | 10 | 0 | 3643.491 | 9637 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | risk_dispersion | FIXED_SIZE_UNIT | 25 | 43077 | 43077 | 43077 | 43077 | 43077 | 178.283 | 242.744 | -66.347 | -210.267 | -27.670 | 0 | 25 | 18.274 | 9637 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | tail_loss_bps | FIXED_SIZE_UNIT | 25 | 43077 | 43077 | 43077 | 43077 | 43077 | 380.471 | 489.183 | -125.795 | -472.948 | 0.000 | 0 | 23 | 41.821 | 9637 |
**-- crypto / E_CLOSE / size : adaptive-minus-fixed by component x setting --**

| arm_class | component | setting | metric | comparator | sym_rows | episode_n | entry_fill_n | close_n | common_fill_n | common_close_n | obs med | comp med | est med | est min | est max | CI>0 | CI<0 | mde med | eff_trade_blocks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIXED_MANAGEMENT | FIXED | UNIT | concentration | FIXED_SIZE_UNIT | 100 | 38211 | 38212 | 38211 | 38212 | 38211 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 9636 |
| FIXED_MANAGEMENT | FIXED | UNIT | drawdown_bps | FIXED_SIZE_UNIT | 25 | 38211 | 38212 | 38211 | 38212 | 38211 | -7099.700 | -7099.700 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 9636 |
| FIXED_MANAGEMENT | FIXED | UNIT | risk_dispersion | FIXED_SIZE_UNIT | 25 | 38211 | 38212 | 38211 | 38212 | 38211 | 245.459 | 245.459 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 9636 |
| FIXED_MANAGEMENT | FIXED | UNIT | tail_loss_bps | FIXED_SIZE_UNIT | 25 | 38211 | 38212 | 38211 | 38212 | 38211 | 490.731 | 490.731 | 0.000 | 0.000 | 0.000 | 0 | 0 | 0.000 | 9636 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_HALVE_HIGH | concentration | FIXED_SIZE_UNIT | 100 | 38211 | 38212 | 38211 | 38212 | 38211 | 0.000 | 0.000 | 0.000 | -0.015 | 0.010 | 11 | 0 | 0.002 | 9636 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_HALVE_HIGH | drawdown_bps | FIXED_SIZE_UNIT | 25 | 38211 | 38212 | 38211 | 38212 | 38211 | -6574.396 | -7099.700 | 710.844 | -890.034 | 7888.804 | 3 | 0 | 1905.726 | 9636 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_HALVE_HIGH | risk_dispersion | FIXED_SIZE_UNIT | 25 | 38211 | 38212 | 38211 | 38212 | 38211 | 226.857 | 245.459 | -20.192 | -112.800 | -2.163 | 0 | 24 | 8.013 | 9636 |
| MANAGEMENT | LEVEL_FORECAST_K12 | STATE_HALVE_HIGH | tail_loss_bps | FIXED_SIZE_UNIT | 25 | 38211 | 38212 | 38211 | 38212 | 38211 | 445.381 | 490.731 | -40.328 | -219.495 | 0.000 | 0 | 17 | 41.122 | 9636 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_HALVE_HIGH | concentration | FIXED_SIZE_UNIT | 100 | 38211 | 38212 | 38211 | 38212 | 38211 | 0.000 | 0.000 | 0.000 | -0.014 | 0.011 | 12 | 0 | 0.002 | 9636 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_HALVE_HIGH | drawdown_bps | FIXED_SIZE_UNIT | 25 | 38211 | 38212 | 38211 | 38212 | 38211 | -6229.654 | -7099.700 | 732.190 | -816.782 | 8158.388 | 3 | 0 | 2123.749 | 9636 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_HALVE_HIGH | risk_dispersion | FIXED_SIZE_UNIT | 25 | 38211 | 38212 | 38211 | 38212 | 38211 | 224.105 | 245.459 | -24.519 | -129.765 | -11.431 | 0 | 25 | 8.220 | 9636 |
| MANAGEMENT | LEVEL_FORECAST_K4 | STATE_HALVE_HIGH | tail_loss_bps | FIXED_SIZE_UNIT | 25 | 38211 | 38212 | 38211 | 38212 | 38211 | 431.961 | 490.731 | -44.115 | -213.757 | 0.000 | 0 | 18 | 41.066 | 9636 |
| MANAGEMENT | LEVEL_NOW | STATE_HALVE_HIGH | concentration | FIXED_SIZE_UNIT | 100 | 38211 | 38212 | 38211 | 38212 | 38211 | 0.000 | 0.000 | 0.000 | -0.011 | 0.022 | 5 | 0 | 0.004 | 9636 |
| MANAGEMENT | LEVEL_NOW | STATE_HALVE_HIGH | drawdown_bps | FIXED_SIZE_UNIT | 25 | 38211 | 38212 | 38211 | 38212 | 38211 | -5865.976 | -7099.700 | 826.906 | -1319.093 | 8085.550 | 7 | 0 | 2553.746 | 9636 |
| MANAGEMENT | LEVEL_NOW | STATE_HALVE_HIGH | risk_dispersion | FIXED_SIZE_UNIT | 25 | 38211 | 38212 | 38211 | 38212 | 38211 | 180.883 | 245.459 | -55.041 | -157.629 | -27.233 | 0 | 25 | 17.582 | 9636 |
| MANAGEMENT | LEVEL_NOW | STATE_HALVE_HIGH | tail_loss_bps | FIXED_SIZE_UNIT | 25 | 38211 | 38212 | 38211 | 38212 | 38211 | 352.355 | 490.731 | -101.963 | -243.611 | -7.534 | 0 | 21 | 53.241 | 9636 |
| MANAGEMENT | RANGE_SCALE | SCALE_NORMALISED | concentration | FIXED_SIZE_UNIT | 100 | 38211 | 38212 | 38211 | 38212 | 38211 | 0.000 | 0.000 | 0.000 | -0.020 | 0.025 | 0 | 1 | 0.004 | 9636 |
| MANAGEMENT | RANGE_SCALE | SCALE_NORMALISED | drawdown_bps | FIXED_SIZE_UNIT | 25 | 38211 | 38212 | 38211 | 38212 | 38211 | -8416.444 | -7099.700 | -541.662 | -3870.616 | 5707.253 | 2 | 1 | 5305.940 | 9636 |
| MANAGEMENT | RANGE_SCALE | SCALE_NORMALISED | risk_dispersion | FIXED_SIZE_UNIT | 25 | 38211 | 38212 | 38211 | 38212 | 38211 | 237.910 | 245.459 | 2.934 | -270.617 | 58.572 | 7 | 6 | 28.947 | 9636 |
| MANAGEMENT | RANGE_SCALE | SCALE_NORMALISED | tail_loss_bps | FIXED_SIZE_UNIT | 25 | 38211 | 38212 | 38211 | 38212 | 38211 | 479.337 | 490.731 | 13.671 | -487.641 | 122.374 | 6 | 3 | 61.037 | 9636 |
| MANAGEMENT | SHOCK | STATE_HALVE_HIGH | concentration | FIXED_SIZE_UNIT | 100 | 38211 | 38212 | 38211 | 38212 | 38211 | 0.000 | 0.000 | 0.000 | -0.016 | 0.018 | 6 | 1 | 0.002 | 9636 |
| MANAGEMENT | SHOCK | STATE_HALVE_HIGH | drawdown_bps | FIXED_SIZE_UNIT | 25 | 38211 | 38212 | 38211 | 38212 | 38211 | -6667.575 | -7099.700 | 731.588 | -2002.371 | 8689.116 | 0 | 0 | 1924.900 | 9636 |
| MANAGEMENT | SHOCK | STATE_HALVE_HIGH | risk_dispersion | FIXED_SIZE_UNIT | 25 | 38211 | 38212 | 38211 | 38212 | 38211 | 218.686 | 245.459 | -27.386 | -140.891 | -7.197 | 0 | 25 | 10.063 | 9636 |
| MANAGEMENT | SHOCK | STATE_HALVE_HIGH | tail_loss_bps | FIXED_SIZE_UNIT | 25 | 38211 | 38212 | 38211 | 38212 | 38211 | 429.706 | 490.731 | -48.264 | -279.998 | 0.000 | 0 | 19 | 45.277 | 9636 |
| MANAGEMENT | TAIL_RISK | STATE_HALVE_HIGH | concentration | FIXED_SIZE_UNIT | 100 | 38211 | 38212 | 38211 | 38212 | 38211 | 0.000 | 0.000 | 0.000 | -0.012 | 0.013 | 4 | 0 | 0.004 | 9636 |
| MANAGEMENT | TAIL_RISK | STATE_HALVE_HIGH | drawdown_bps | FIXED_SIZE_UNIT | 25 | 38211 | 38212 | 38211 | 38212 | 38211 | -5671.049 | -7099.700 | 1330.439 | -543.451 | 7815.147 | 9 | 0 | 2118.143 | 9636 |
| MANAGEMENT | TAIL_RISK | STATE_HALVE_HIGH | risk_dispersion | FIXED_SIZE_UNIT | 25 | 38211 | 38212 | 38211 | 38212 | 38211 | 179.764 | 245.459 | -53.045 | -346.844 | -23.964 | 0 | 25 | 16.662 | 9636 |
| MANAGEMENT | TAIL_RISK | STATE_HALVE_HIGH | tail_loss_bps | FIXED_SIZE_UNIT | 25 | 38211 | 38212 | 38211 | 38212 | 38211 | 387.535 | 490.731 | -98.312 | -775.072 | -21.140 | 0 | 22 | 51.047 | 9636 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | concentration | FIXED_SIZE_UNIT | 300 | 114633 | 114636 | 114633 | 114636 | 114633 | 0.000 | 0.000 | 0.000 | -0.021 | 0.027 | 17 | 4 | 0.003 | 28908 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | drawdown_bps | FIXED_SIZE_UNIT | 75 | 114633 | 114636 | 114633 | 114636 | 114633 | -6524.502 | -7099.700 | 876.974 | -3831.578 | 10315.536 | 3 | 0 | 3646.798 | 28908 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | risk_dispersion | FIXED_SIZE_UNIT | 75 | 114633 | 114636 | 114633 | 114636 | 114633 | 221.421 | 245.459 | -21.821 | -365.278 | 36.712 | 3 | 47 | 19.577 | 28908 |
| MANAGEMENT_COMPONENT_COMBINATION | RANGE_SCALE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | tail_loss_bps | FIXED_SIZE_UNIT | 75 | 114633 | 114636 | 114633 | 114636 | 114633 | 442.919 | 490.731 | -38.549 | -503.113 | 86.095 | 3 | 21 | 61.938 | 28908 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | concentration | FIXED_SIZE_UNIT | 100 | 38211 | 38212 | 38211 | 38212 | 38211 | 0.000 | 0.000 | 0.000 | -0.010 | 0.031 | 5 | 0 | 0.004 | 9636 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | drawdown_bps | FIXED_SIZE_UNIT | 25 | 38211 | 38212 | 38211 | 38212 | 38211 | -5894.587 | -7099.700 | 1312.315 | -303.097 | 9031.408 | 9 | 0 | 2648.702 | 9636 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | risk_dispersion | FIXED_SIZE_UNIT | 25 | 38211 | 38212 | 38211 | 38212 | 38211 | 173.016 | 245.459 | -63.809 | -199.664 | -29.169 | 0 | 25 | 17.173 | 9636 |
| MANAGEMENT_COMPONENT_COMBINATION | SHOCK | STATE_LOW_075_HIGH_150_ON_SHOCK | tail_loss_bps | FIXED_SIZE_UNIT | 25 | 38211 | 38212 | 38211 | 38212 | 38211 | 344.868 | 490.731 | -112.482 | -469.883 | -7.534 | 0 | 22 | 51.988 | 9636 |

## A4 — controls

**ctrader controls rows=1922**

```text
control                 population                         comparator
FIXED_DEVICE            COMMON_CLOSE_TRADE                 DECLARED_FIXED_DEVICE          1
FIXED_NATIVE_PARAMETER  ELIGIBLE_ORIGIN                    DECLARED_FIXED_NATIVE          1
MAGNITUDE_MATCH         ELIGIBLE_ORIGIN_MAGNITUDE_STRATUM  FIXED_NATIVE_BAND_E_CLOSE    768
                                                           FIXED_NATIVE_BAND_E_TOUCH    768
TIME_DERANGEMENT        ELIGIBLE_ORIGIN_TIME_DERANGED      FIXED_NATIVE_BAND_E_CLOSE    192
                                                           FIXED_NATIVE_BAND_E_TOUCH    192
```

**-- undefined/pointer rows --**

```text
                  control          population             comparator                      undefined_reason  count
0            FIXED_DEVICE  COMMON_CLOSE_TRADE  DECLARED_FIXED_DEVICE             REPORTED_IN_DEVICE_TABLES    NaN
1  FIXED_NATIVE_PARAMETER     ELIGIBLE_ORIGIN  DECLARED_FIXED_NATIVE  REPORTED_IN_NATIVE_PARAMETER_ORIGINS    NaN
```

**-- ctrader / E_TOUCH / TIME_DERANGEMENT by component (+magnitude_bin) --**

| component | bin | rows | count | est med | est min | est max | CI>0 | CI<0 | mde med | eff_count |
|---|---|---|---|---|---|---|---|---|---|---|
| LEVEL_FORECAST_K12 | - | 24 | 357600 | -0.027 | -0.160 | 0.305 | 3 | 0 | 0.244 | 17832 |
| LEVEL_FORECAST_K4 | - | 24 | 357600 | -0.004 | -0.231 | 0.116 | 0 | 0 | 0.246 | 17832 |
| LEVEL_NOW | - | 24 | 357600 | -0.024 | -0.367 | 0.098 | 0 | 0 | 0.231 | 17832 |
| RANGE_SCALE | - | 24 | 357600 | -0.024 | -0.247 | 0.194 | 0 | 0 | 0.193 | 17832 |
| SHOCK | - | 24 | 357600 | -0.050 | -0.490 | 0.348 | 3 | 1 | 0.221 | 17832 |
| SWING_GT_CUR | - | 24 | 357600 | -0.037 | -0.385 | 0.227 | 0 | 0 | 0.225 | 17832 |
| SWING_SCALE | - | 24 | 357600 | -0.035 | -0.305 | 0.204 | 0 | 0 | 0.178 | 17832 |
| TAIL_RISK | - | 24 | 357600 | -0.017 | -0.412 | 0.108 | 0 | 0 | 0.227 | 17832 |
**-- ctrader / E_CLOSE / TIME_DERANGEMENT by component (+magnitude_bin) --**

| component | bin | rows | count | est med | est min | est max | CI>0 | CI<0 | mde med | eff_count |
|---|---|---|---|---|---|---|---|---|---|---|
| LEVEL_FORECAST_K12 | - | 24 | 357600 | -0.005 | -0.108 | 0.152 | 1 | 0 | 0.231 | 17832 |
| LEVEL_FORECAST_K4 | - | 24 | 357600 | 0.012 | -0.122 | 0.123 | 0 | 0 | 0.236 | 17832 |
| LEVEL_NOW | - | 24 | 357600 | 0.016 | -0.067 | 0.074 | 0 | 0 | 0.192 | 17832 |
| RANGE_SCALE | - | 24 | 357600 | 0.040 | -0.064 | 0.095 | 0 | 0 | 0.180 | 17832 |
| SHOCK | - | 24 | 357600 | 0.018 | -0.169 | 0.075 | 0 | 0 | 0.207 | 17832 |
| SWING_GT_CUR | - | 24 | 357600 | -0.000 | -0.075 | 0.110 | 0 | 0 | 0.197 | 17832 |
| SWING_SCALE | - | 24 | 357600 | -0.002 | -0.181 | 0.129 | 0 | 0 | 0.176 | 17832 |
| TAIL_RISK | - | 24 | 357600 | 0.021 | -0.075 | 0.083 | 0 | 0 | 0.201 | 17832 |
**-- ctrader / E_TOUCH / MAGNITUDE_MATCH by component (+magnitude_bin) --**

| component | bin | rows | count | est med | est min | est max | CI>0 | CI<0 | mde med | eff_count |
|---|---|---|---|---|---|---|---|---|---|---|
| LEVEL_FORECAST_K12 | 0.0 | 24 | 87056 | 0.285 | -0.244 | 0.798 | 0 | 0 | 1.079 | 5784 |
| LEVEL_FORECAST_K12 | 1.0 | 24 | 87048 | 0.035 | -0.591 | 0.416 | 0 | 0 | 1.184 | 7088 |
| LEVEL_FORECAST_K12 | 2.0 | 24 | 87048 | 0.097 | -0.945 | 1.874 | 0 | 1 | 1.174 | 7056 |
| LEVEL_FORECAST_K12 | 3.0 | 24 | 87032 | -0.842 | -2.126 | 0.276 | 0 | 3 | 1.224 | 6688 |
| LEVEL_FORECAST_K4 | 0.0 | 24 | 87056 | 0.124 | -0.243 | 0.537 | 0 | 0 | 1.070 | 5784 |
| LEVEL_FORECAST_K4 | 1.0 | 24 | 87048 | 0.049 | -0.836 | 0.945 | 0 | 0 | 1.175 | 7088 |
| LEVEL_FORECAST_K4 | 2.0 | 24 | 87048 | 0.105 | -0.785 | 1.848 | 0 | 0 | 1.175 | 7056 |
| LEVEL_FORECAST_K4 | 3.0 | 24 | 87032 | -0.640 | -2.496 | 0.923 | 0 | 3 | 1.262 | 6688 |
| LEVEL_NOW | 0.0 | 24 | 87056 | 0.178 | -0.288 | 1.103 | 0 | 0 | 1.117 | 5784 |
| LEVEL_NOW | 1.0 | 24 | 87048 | -0.046 | -0.821 | 1.500 | 0 | 0 | 1.192 | 7088 |
| LEVEL_NOW | 2.0 | 24 | 87048 | -0.030 | -0.596 | 1.226 | 0 | 0 | 1.218 | 7056 |
| LEVEL_NOW | 3.0 | 24 | 87032 | -0.417 | -1.816 | 0.371 | 0 | 1 | 1.355 | 6688 |
| RANGE_SCALE | 0.0 | 24 | 87056 | 0.221 | -0.335 | 1.049 | 0 | 0 | 1.108 | 5784 |
| RANGE_SCALE | 1.0 | 24 | 87048 | 0.200 | -0.621 | 1.318 | 1 | 0 | 1.094 | 7088 |
| RANGE_SCALE | 2.0 | 24 | 87048 | 0.011 | -0.742 | 4.380 | 3 | 0 | 1.053 | 7056 |
| RANGE_SCALE | 3.0 | 24 | 87032 | -0.450 | -2.285 | 0.637 | 0 | 0 | 1.192 | 6688 |
| SHOCK | 0.0 | 24 | 87056 | 0.078 | -0.461 | 0.825 | 0 | 0 | 1.081 | 5784 |
| SHOCK | 1.0 | 24 | 87048 | 0.094 | -0.693 | 1.059 | 1 | 1 | 1.156 | 7088 |
| SHOCK | 2.0 | 24 | 87048 | -0.130 | -0.943 | 2.369 | 0 | 0 | 1.131 | 7056 |
| SHOCK | 3.0 | 24 | 87032 | -0.811 | -1.992 | 0.560 | 0 | 0 | 1.391 | 6688 |
| SWING_GT_CUR | 0.0 | 24 | 87056 | 0.134 | -0.194 | 1.329 | 0 | 0 | 1.142 | 5784 |
| SWING_GT_CUR | 1.0 | 24 | 87048 | 0.289 | -0.661 | 1.105 | 0 | 1 | 1.195 | 7088 |
| SWING_GT_CUR | 2.0 | 24 | 87048 | -0.217 | -0.866 | 2.917 | 1 | 1 | 1.249 | 7056 |
| SWING_GT_CUR | 3.0 | 24 | 87032 | -0.428 | -1.549 | -0.077 | 0 | 0 | 1.333 | 6688 |
| SWING_SCALE | 0.0 | 24 | 87056 | 0.046 | -0.351 | 1.317 | 1 | 0 | 0.867 | 5784 |
| SWING_SCALE | 1.0 | 24 | 87048 | 0.036 | -0.688 | 0.617 | 0 | 0 | 0.936 | 7088 |
| SWING_SCALE | 2.0 | 24 | 87048 | -0.057 | -0.834 | 3.760 | 3 | 1 | 0.927 | 7056 |
| SWING_SCALE | 3.0 | 24 | 87032 | -0.550 | -3.054 | 0.301 | 0 | 1 | 1.288 | 6688 |
| TAIL_RISK | 0.0 | 24 | 87056 | 0.342 | -0.348 | 1.506 | 1 | 1 | 1.118 | 5784 |
| TAIL_RISK | 1.0 | 24 | 87048 | 0.087 | -0.676 | 1.021 | 0 | 0 | 1.121 | 7088 |
| TAIL_RISK | 2.0 | 24 | 87048 | -0.049 | -0.819 | 3.523 | 3 | 1 | 1.168 | 7056 |
| TAIL_RISK | 3.0 | 24 | 87032 | -0.432 | -2.431 | 0.331 | 0 | 0 | 1.313 | 6688 |
**-- ctrader / E_CLOSE / MAGNITUDE_MATCH by component (+magnitude_bin) --**

| component | bin | rows | count | est med | est min | est max | CI>0 | CI<0 | mde med | eff_count |
|---|---|---|---|---|---|---|---|---|---|---|
| LEVEL_FORECAST_K12 | 0.0 | 24 | 87056 | 0.093 | -0.990 | 1.135 | 3 | 0 | 0.976 | 5784 |
| LEVEL_FORECAST_K12 | 1.0 | 24 | 87048 | -0.230 | -0.880 | 1.233 | 0 | 0 | 1.138 | 7088 |
| LEVEL_FORECAST_K12 | 2.0 | 24 | 87048 | 0.171 | -1.811 | 1.369 | 1 | 3 | 1.158 | 7056 |
| LEVEL_FORECAST_K12 | 3.0 | 24 | 87032 | 0.539 | -0.548 | 1.522 | 1 | 0 | 1.206 | 6688 |
| LEVEL_FORECAST_K4 | 0.0 | 24 | 87056 | 0.060 | -0.877 | 1.341 | 4 | 0 | 0.995 | 5784 |
| LEVEL_FORECAST_K4 | 1.0 | 24 | 87048 | -0.291 | -1.047 | 0.969 | 0 | 2 | 1.273 | 7088 |
| LEVEL_FORECAST_K4 | 2.0 | 24 | 87048 | 0.143 | -1.412 | 1.440 | 1 | 1 | 1.093 | 7056 |
| LEVEL_FORECAST_K4 | 3.0 | 24 | 87032 | 0.364 | -0.426 | 1.176 | 0 | 0 | 1.169 | 6688 |
| LEVEL_NOW | 0.0 | 24 | 87056 | 0.066 | -1.025 | 1.396 | 1 | 0 | 1.240 | 5784 |
| LEVEL_NOW | 1.0 | 24 | 87048 | -0.260 | -1.257 | 1.539 | 0 | 1 | 1.314 | 7088 |
| LEVEL_NOW | 2.0 | 24 | 87048 | 0.077 | -1.268 | 2.327 | 0 | 0 | 1.241 | 7056 |
| LEVEL_NOW | 3.0 | 24 | 87032 | 0.276 | -1.424 | 1.471 | 1 | 0 | 1.300 | 6688 |
| RANGE_SCALE | 0.0 | 24 | 87056 | 0.033 | -0.895 | 1.268 | 1 | 0 | 1.146 | 5784 |
| RANGE_SCALE | 1.0 | 24 | 87048 | 0.035 | -1.135 | 0.852 | 0 | 1 | 1.109 | 7088 |
| RANGE_SCALE | 2.0 | 24 | 87048 | 0.045 | -1.204 | 0.791 | 0 | 0 | 1.113 | 7056 |
| RANGE_SCALE | 3.0 | 24 | 87032 | 0.259 | -1.938 | 1.476 | 0 | 0 | 1.259 | 6688 |
| SHOCK | 0.0 | 24 | 87056 | 0.093 | -1.564 | 1.948 | 2 | 0 | 1.218 | 5784 |
| SHOCK | 1.0 | 24 | 87048 | -0.443 | -1.191 | 1.396 | 0 | 1 | 1.210 | 7088 |
| SHOCK | 2.0 | 24 | 87048 | -0.109 | -2.217 | 1.343 | 0 | 1 | 1.220 | 7056 |
| SHOCK | 3.0 | 24 | 87032 | 0.146 | -1.636 | 1.748 | 0 | 0 | 1.314 | 6688 |
| SWING_GT_CUR | 0.0 | 24 | 87056 | 0.014 | -1.488 | 2.109 | 4 | 1 | 1.167 | 5784 |
| SWING_GT_CUR | 1.0 | 24 | 87048 | -0.245 | -0.836 | 1.360 | 0 | 2 | 1.276 | 7088 |
| SWING_GT_CUR | 2.0 | 24 | 87048 | -0.016 | -1.696 | 1.450 | 1 | 1 | 1.140 | 7056 |
| SWING_GT_CUR | 3.0 | 24 | 87032 | 0.336 | -1.007 | 2.080 | 0 | 0 | 1.298 | 6688 |
| SWING_SCALE | 0.0 | 24 | 87056 | 0.094 | -0.801 | 1.683 | 1 | 0 | 1.130 | 5784 |
| SWING_SCALE | 1.0 | 24 | 87048 | -0.185 | -0.924 | 0.938 | 0 | 2 | 1.006 | 7088 |
| SWING_SCALE | 2.0 | 24 | 87048 | -0.069 | -1.032 | 1.187 | 0 | 0 | 1.028 | 7056 |
| SWING_SCALE | 3.0 | 24 | 87032 | 0.135 | -1.313 | 1.945 | 1 | 0 | 1.250 | 6688 |
| TAIL_RISK | 0.0 | 24 | 87056 | 0.091 | -0.927 | 1.359 | 2 | 0 | 1.180 | 5784 |
| TAIL_RISK | 1.0 | 24 | 87048 | -0.315 | -1.127 | 1.087 | 0 | 1 | 1.278 | 7088 |
| TAIL_RISK | 2.0 | 24 | 87048 | -0.066 | -1.579 | 0.919 | 0 | 2 | 1.269 | 7056 |
| TAIL_RISK | 3.0 | 24 | 87032 | 0.536 | -1.205 | 2.349 | 1 | 0 | 1.394 | 6688 |
**crypto controls rows=16002**

```text
control                 population                         comparator
FIXED_DEVICE            COMMON_CLOSE_TRADE                 DECLARED_FIXED_DEVICE           1
FIXED_NATIVE_PARAMETER  ELIGIBLE_ORIGIN                    DECLARED_FIXED_NATIVE           1
MAGNITUDE_MATCH         ELIGIBLE_ORIGIN_MAGNITUDE_STRATUM  FIXED_NATIVE_BAND_E_CLOSE    6400
                                                           FIXED_NATIVE_BAND_E_TOUCH    6400
TIME_DERANGEMENT        ELIGIBLE_ORIGIN_TIME_DERANGED      FIXED_NATIVE_BAND_E_CLOSE    1600
                                                           FIXED_NATIVE_BAND_E_TOUCH    1600
```

**-- undefined/pointer rows --**

```text
                  control          population             comparator                      undefined_reason  count
0            FIXED_DEVICE  COMMON_CLOSE_TRADE  DECLARED_FIXED_DEVICE             REPORTED_IN_DEVICE_TABLES    NaN
1  FIXED_NATIVE_PARAMETER     ELIGIBLE_ORIGIN  DECLARED_FIXED_NATIVE  REPORTED_IN_NATIVE_PARAMETER_ORIGINS    NaN
```

**-- crypto / E_TOUCH / TIME_DERANGEMENT by component (+magnitude_bin) --**

| component | bin | rows | count | est med | est min | est max | CI>0 | CI<0 | mde med | eff_count |
|---|---|---|---|---|---|---|---|---|---|---|
| LEVEL_FORECAST_K12 | - | 200 | 1848968 | -0.237 | -39.697 | 8.820 | 2 | 14 | 2.024 | 77096 |
| LEVEL_FORECAST_K4 | - | 200 | 1848968 | -0.252 | -46.251 | 8.077 | 2 | 12 | 1.987 | 77096 |
| LEVEL_NOW | - | 200 | 1848968 | -0.018 | -22.791 | 11.300 | 2 | 6 | 2.061 | 77096 |
| RANGE_SCALE | - | 200 | 1848968 | -0.024 | -42.519 | 9.826 | 2 | 8 | 1.779 | 77096 |
| SHOCK | - | 200 | 1848968 | -0.021 | -41.904 | 8.501 | 2 | 5 | 1.959 | 77096 |
| SWING_GT_CUR | - | 200 | 1848968 | -0.353 | -25.377 | 9.175 | 1 | 5 | 1.906 | 77096 |
| SWING_SCALE | - | 200 | 1848968 | 0.011 | -20.249 | 3.877 | 2 | 7 | 1.827 | 77096 |
| TAIL_RISK | - | 200 | 1848968 | -0.151 | -30.965 | 14.620 | 1 | 8 | 1.962 | 77096 |
**-- crypto / E_CLOSE / TIME_DERANGEMENT by component (+magnitude_bin) --**

| component | bin | rows | count | est med | est min | est max | CI>0 | CI<0 | mde med | eff_count |
|---|---|---|---|---|---|---|---|---|---|---|
| LEVEL_FORECAST_K12 | - | 200 | 1848968 | -0.373 | -4.539 | 23.241 | 3 | 7 | 1.808 | 77096 |
| LEVEL_FORECAST_K4 | - | 200 | 1848968 | -0.444 | -4.564 | 22.790 | 0 | 7 | 1.819 | 77096 |
| LEVEL_NOW | - | 200 | 1848968 | 0.111 | -2.728 | 21.178 | 3 | 0 | 1.711 | 77096 |
| RANGE_SCALE | - | 200 | 1848968 | 0.036 | -4.469 | 14.311 | 1 | 0 | 1.474 | 77096 |
| SHOCK | - | 200 | 1848968 | 0.118 | -5.282 | 19.241 | 1 | 0 | 1.696 | 77096 |
| SWING_GT_CUR | - | 200 | 1848968 | -0.028 | -5.573 | 20.487 | 1 | 0 | 1.757 | 77096 |
| SWING_SCALE | - | 200 | 1848968 | -0.051 | -5.816 | 17.452 | 0 | 0 | 1.577 | 77096 |
| TAIL_RISK | - | 200 | 1848968 | 0.122 | -9.540 | 21.955 | 9 | 0 | 1.695 | 77096 |
**-- crypto / E_TOUCH / MAGNITUDE_MATCH by component (+magnitude_bin) --**

| component | bin | rows | count | est med | est min | est max | CI>0 | CI<0 | mde med | eff_count |
|---|---|---|---|---|---|---|---|---|---|---|
| LEVEL_FORECAST_K12 | 0.0 | 200 | 436760 | -0.611 | -427.975 | 43.255 | 8 | 13 | 6.397 | 28872 |
| LEVEL_FORECAST_K12 | 1.0 | 200 | 436640 | 0.571 | -460.362 | 299.419 | 6 | 4 | 7.596 | 30776 |
| LEVEL_FORECAST_K12 | 2.0 | 200 | 436704 | -0.503 | -256.930 | 529.544 | 1 | 9 | 7.872 | 30480 |
| LEVEL_FORECAST_K12 | 3.0 | 200 | 436592 | 0.081 | -495.463 | 20.508 | 2 | 4 | 10.829 | 27264 |
| LEVEL_FORECAST_K4 | 0.0 | 200 | 436760 | -0.478 | -218.854 | 31.158 | 5 | 9 | 6.305 | 28872 |
| LEVEL_FORECAST_K4 | 1.0 | 200 | 436640 | 0.446 | -276.039 | 206.114 | 8 | 7 | 7.614 | 30776 |
| LEVEL_FORECAST_K4 | 2.0 | 200 | 436704 | 0.136 | -136.232 | 529.544 | 2 | 11 | 7.909 | 30480 |
| LEVEL_FORECAST_K4 | 3.0 | 200 | 436592 | 0.975 | -525.450 | 229.159 | 4 | 12 | 10.292 | 27264 |
| LEVEL_NOW | 0.0 | 200 | 436760 | -0.728 | -467.298 | 33.437 | 7 | 10 | 5.954 | 28872 |
| LEVEL_NOW | 1.0 | 200 | 436640 | 0.017 | -276.039 | 299.419 | 9 | 12 | 8.120 | 30776 |
| LEVEL_NOW | 2.0 | 200 | 436704 | 0.107 | -56.300 | 417.170 | 5 | 9 | 8.335 | 30480 |
| LEVEL_NOW | 3.0 | 200 | 436592 | 0.751 | -391.992 | 108.464 | 6 | 10 | 11.624 | 27264 |
| RANGE_SCALE | 0.0 | 200 | 436760 | -0.468 | -337.467 | 39.342 | 7 | 7 | 6.203 | 28872 |
| RANGE_SCALE | 1.0 | 200 | 436640 | -0.755 | -256.865 | 348.898 | 5 | 8 | 7.351 | 30776 |
| RANGE_SCALE | 2.0 | 200 | 436704 | -0.002 | -158.413 | 405.305 | 4 | 3 | 7.466 | 30480 |
| RANGE_SCALE | 3.0 | 200 | 436592 | 0.853 | -433.187 | 159.435 | 9 | 9 | 11.195 | 27264 |
| SHOCK | 0.0 | 200 | 436760 | -0.041 | -117.677 | 39.342 | 2 | 6 | 6.218 | 28872 |
| SHOCK | 1.0 | 200 | 436640 | -0.008 | -206.563 | 360.866 | 9 | 5 | 8.369 | 30776 |
| SHOCK | 2.0 | 200 | 436704 | -0.264 | -158.413 | 540.154 | 8 | 5 | 8.169 | 30480 |
| SHOCK | 3.0 | 200 | 436592 | 0.049 | -634.732 | 42.720 | 9 | 9 | 11.552 | 27264 |
| SWING_GT_CUR | 0.0 | 200 | 436760 | -0.493 | -272.347 | 44.420 | 3 | 11 | 6.449 | 28872 |
| SWING_GT_CUR | 1.0 | 200 | 436640 | -0.052 | -479.536 | 72.911 | 9 | 15 | 7.834 | 30776 |
| SWING_GT_CUR | 2.0 | 200 | 436704 | -0.535 | -75.761 | 405.305 | 3 | 7 | 8.414 | 30480 |
| SWING_GT_CUR | 3.0 | 200 | 436592 | 0.033 | -409.818 | 87.070 | 3 | 14 | 11.472 | 27264 |
| SWING_SCALE | 0.0 | 200 | 436760 | -0.794 | -209.756 | 9.853 | 3 | 4 | 6.405 | 28872 |
| SWING_SCALE | 1.0 | 200 | 436640 | -0.172 | -91.131 | 23.815 | 5 | 8 | 7.588 | 30776 |
| SWING_SCALE | 2.0 | 200 | 436704 | -0.424 | -35.688 | 55.482 | 12 | 16 | 6.989 | 30480 |
| SWING_SCALE | 3.0 | 200 | 436592 | -1.212 | -131.234 | 23.547 | 3 | 10 | 11.001 | 27264 |
| TAIL_RISK | 0.0 | 200 | 436760 | -0.686 | -425.376 | 49.644 | 6 | 4 | 6.092 | 28872 |
| TAIL_RISK | 1.0 | 200 | 436640 | 0.512 | -449.689 | 74.132 | 8 | 5 | 8.226 | 30776 |
| TAIL_RISK | 2.0 | 200 | 436704 | -0.132 | -256.930 | 421.526 | 5 | 14 | 8.299 | 30480 |
| TAIL_RISK | 3.0 | 200 | 436592 | 1.088 | -495.463 | 29.210 | 4 | 8 | 12.112 | 27264 |
**-- crypto / E_CLOSE / MAGNITUDE_MATCH by component (+magnitude_bin) --**

| component | bin | rows | count | est med | est min | est max | CI>0 | CI<0 | mde med | eff_count |
|---|---|---|---|---|---|---|---|---|---|---|
| LEVEL_FORECAST_K12 | 0.0 | 200 | 436760 | -0.458 | -186.908 | 57.775 | 6 | 11 | 6.196 | 28872 |
| LEVEL_FORECAST_K12 | 1.0 | 200 | 436640 | 0.220 | -97.563 | 549.552 | 6 | 11 | 7.184 | 30776 |
| LEVEL_FORECAST_K12 | 2.0 | 200 | 436704 | -1.024 | -187.975 | 283.198 | 11 | 5 | 7.282 | 30480 |
| LEVEL_FORECAST_K12 | 3.0 | 200 | 436592 | -0.347 | -542.509 | 112.753 | 5 | 13 | 9.584 | 27264 |
| LEVEL_FORECAST_K4 | 0.0 | 200 | 436760 | -0.676 | -170.000 | 25.758 | 5 | 8 | 6.657 | 28872 |
| LEVEL_FORECAST_K4 | 1.0 | 200 | 436640 | 0.341 | -59.434 | 763.788 | 9 | 9 | 7.074 | 30776 |
| LEVEL_FORECAST_K4 | 2.0 | 200 | 436704 | -0.757 | -130.159 | 236.830 | 13 | 5 | 7.775 | 30480 |
| LEVEL_FORECAST_K4 | 3.0 | 200 | 436592 | -0.489 | -934.395 | 115.066 | 4 | 15 | 9.440 | 27264 |
| LEVEL_NOW | 0.0 | 200 | 436760 | -0.387 | -180.568 | 34.343 | 10 | 11 | 6.603 | 28872 |
| LEVEL_NOW | 1.0 | 200 | 436640 | 0.455 | -46.021 | 599.009 | 7 | 8 | 7.829 | 30776 |
| LEVEL_NOW | 2.0 | 200 | 436704 | -0.063 | -163.527 | 167.416 | 5 | 7 | 8.226 | 30480 |
| LEVEL_NOW | 3.0 | 200 | 436592 | -0.367 | -554.200 | 61.314 | 2 | 9 | 10.967 | 27264 |
| RANGE_SCALE | 0.0 | 200 | 436760 | -0.374 | -223.492 | 26.103 | 6 | 8 | 7.014 | 28872 |
| RANGE_SCALE | 1.0 | 200 | 436640 | 0.348 | -96.114 | 581.337 | 13 | 9 | 7.752 | 30776 |
| RANGE_SCALE | 2.0 | 200 | 436704 | -0.376 | -104.346 | 144.197 | 15 | 13 | 7.687 | 30480 |
| RANGE_SCALE | 3.0 | 200 | 436592 | -0.747 | -496.395 | 100.711 | 8 | 10 | 10.725 | 27264 |
| SHOCK | 0.0 | 200 | 436760 | 0.407 | -195.441 | 29.838 | 6 | 10 | 6.642 | 28872 |
| SHOCK | 1.0 | 200 | 436640 | 0.140 | -78.459 | 574.437 | 13 | 8 | 7.733 | 30776 |
| SHOCK | 2.0 | 200 | 436704 | -0.288 | -65.642 | 415.090 | 7 | 11 | 8.798 | 30480 |
| SHOCK | 3.0 | 200 | 436592 | -0.895 | -655.394 | 61.314 | 1 | 13 | 10.850 | 27264 |
| SWING_GT_CUR | 0.0 | 200 | 436760 | -0.676 | -288.838 | 37.984 | 6 | 12 | 6.478 | 28872 |
| SWING_GT_CUR | 1.0 | 200 | 436640 | 0.090 | -90.001 | 438.624 | 11 | 9 | 7.739 | 30776 |
| SWING_GT_CUR | 2.0 | 200 | 436704 | -0.100 | -227.376 | 178.834 | 10 | 8 | 8.156 | 30480 |
| SWING_GT_CUR | 3.0 | 200 | 436592 | -0.007 | -715.424 | 106.619 | 6 | 13 | 10.829 | 27264 |
| SWING_SCALE | 0.0 | 200 | 436760 | -0.262 | -55.855 | 34.721 | 7 | 21 | 6.543 | 28872 |
| SWING_SCALE | 1.0 | 200 | 436640 | 0.211 | -29.242 | 258.325 | 18 | 5 | 7.499 | 30776 |
| SWING_SCALE | 2.0 | 200 | 436704 | -0.680 | -30.507 | 35.424 | 6 | 8 | 8.066 | 30480 |
| SWING_SCALE | 3.0 | 200 | 436592 | 0.051 | -362.671 | 35.870 | 9 | 15 | 10.786 | 27264 |
| TAIL_RISK | 0.0 | 200 | 436760 | -0.020 | -172.321 | 53.037 | 6 | 8 | 6.657 | 28872 |
| TAIL_RISK | 1.0 | 200 | 436640 | 0.001 | -142.307 | 549.552 | 7 | 12 | 7.614 | 30776 |
| TAIL_RISK | 2.0 | 200 | 436704 | -0.574 | -120.207 | 236.830 | 7 | 4 | 8.244 | 30480 |
| TAIL_RISK | 3.0 | 200 | 436592 | -0.052 | -764.691 | 60.067 | 4 | 12 | 11.009 | 27264 |

## A5 — selection checks and state sections

**ctrader selection_checks rows=390**

**-- ctrader / E_TOUCH selection check by component --**

```text
                    rows  payoff_ratio_med  payoff_ratio_min  payoff_ratio_max  sign_share_diff_med  excl_mean_median_gap_med  selected_n  excluded_n
component
LEVEL_FORECAST_K12    24               NaN               NaN               NaN             0.097416                       0.0      206956      150644
LEVEL_FORECAST_K4     24               NaN               NaN               NaN             0.096898                       0.0      207070      150530
LEVEL_NOW             24               NaN               NaN               NaN             0.096795                       0.0      345581       12019
RANGE_SCALE           24               NaN               NaN               NaN             0.097388                       0.0      347426       10174
SHOCK                 24               NaN               NaN               NaN             0.097432                       0.0      346479       11121
SWING_GT_CUR          24               NaN               NaN               NaN             0.097330                       0.0      337917       19683
SWING_SCALE           24               NaN               NaN               NaN             0.097274                       0.0      338499       19101
TAIL_RISK             24               NaN               NaN               NaN             0.096392                       0.0      346965       10635
```

**-- ctrader / E_CLOSE selection check by component --**

```text
                    rows  payoff_ratio_med  payoff_ratio_min  payoff_ratio_max  sign_share_diff_med  excl_mean_median_gap_med  selected_n  excluded_n
component
LEVEL_FORECAST_K12    24               NaN               NaN               NaN             0.093078                       0.0      195305      162295
LEVEL_FORECAST_K4     24               NaN               NaN               NaN             0.092947                       0.0      195415      162185
LEVEL_NOW             24               NaN               NaN               NaN             0.093249                       0.0      326673       30927
RANGE_SCALE           24               NaN               NaN               NaN             0.092919                       0.0      328119       29481
SHOCK                 24               NaN               NaN               NaN             0.093452                       0.0      327537       30063
SWING_GT_CUR          24               NaN               NaN               NaN             0.093627                       0.0      319529       38071
SWING_SCALE           24               NaN               NaN               NaN             0.091509                       0.0      319660       37940
TAIL_RISK             24               NaN               NaN               NaN             0.093797                       0.0      328001       29599
```

**ctrader state_sections rows=3861**

**-- ctrader / E_TOUCH state sections by component x state --**

```text
                                    rows    row_n  mean_outcome_bps_med  mean_outcome_bps_min  mean_outcome_bps_max
component          state
LEVEL_FORECAST_K12 EVENT_UNDECIDED    39      228              0.000000              0.000000              0.000000
                   INCOMPLETE         24      228              0.000000              0.000000              0.000000
                   NO_EVENT           39     6744              0.000000              0.000000              0.000000
                   NO_FEATURE         39   162057              0.000000              0.000000              0.000000
                   ORDER_CREATED      39   411843              0.021615             -0.349684              0.401218
LEVEL_FORECAST_K4  EVENT_UNDECIDED    39      228              0.000000              0.000000              0.000000
                   INCOMPLETE         36      372              0.000000              0.000000              0.000000
                   NO_EVENT           38     6742              0.000000              0.000000              0.000000
                   NO_FEATURE         39   161931              0.000000              0.000000              0.000000
                   ORDER_CREATED      39   411827              0.030105             -0.253004              0.228887
LEVEL_NOW          EVENT_UNDECIDED    39      330              0.000000              0.000000              0.000000
                   INCOMPLETE         39      426              0.000000              0.000000              0.000000
                   NO_EVENT           39    10729              0.000000              0.000000              0.000000
                   NO_FEATURE         39     1632              0.000000              0.000000              0.000000
                   ORDER_CREATED      39   567983             -0.007932             -0.291050              0.179148
RANGE_SCALE        EVENT_UNDECIDED   114      773              0.000000              0.000000              0.000000
                   INCOMPLETE        102     1032              0.000000              0.000000              0.000000
                   NO_EVENT          113    10970              0.000000              0.000000              0.000000
                   NO_FEATURE        114   147130              0.000000              0.000000              0.000000
                   ORDER_CREATED     114  1538695              0.005043             -0.367487              0.358458
SHOCK              EVENT_UNDECIDED    54      436              0.000000              0.000000              0.000000
                   INCOMPLETE         54      576              0.000000              0.000000              0.000000
                   NO_EVENT           54    10893              0.000000              0.000000              0.000000
                   NO_FEATURE         54     1301              0.000000              0.000000              0.000000
                   ORDER_CREATED      54   791394              0.005857             -0.411444              0.301363
SWING_GT_CUR       EVENT_UNDECIDED    30      255              0.000000              0.000000              0.000000
                   INCOMPLETE         30      336              0.000000              0.000000              0.000000
                   NO_EVENT           30    10327              0.000000              0.000000              0.000000
                   NO_FEATURE         30    10596              0.000000              0.000000              0.000000
                   ORDER_CREATED      30   425486              0.000899             -0.332977              0.195639
SWING_SCALE        EVENT_UNDECIDED    42      309              0.000000              0.000000              0.000000
                   INCOMPLETE         42      456              0.000000              0.000000              0.000000
                   NO_EVENT           42     9865              0.000000              0.000000              0.000000
                   NO_FEATURE         42    16478              0.000000              0.000000              0.000000
                   ORDER_CREATED      42   598692              0.000000             -0.612810              0.314131
TAIL_RISK          EVENT_UNDECIDED    33      292              0.000000              0.000000              0.000000
                   INCOMPLETE         33      366              0.000000              0.000000              0.000000
                   NO_EVENT           33    10701              0.000000              0.000000              0.000000
                   NO_FEATURE         33       33              0.000000              0.000000              0.000000
                   ORDER_CREATED      33   480308             -0.024901             -0.365692              0.222794
```

**-- ctrader / E_CLOSE state sections by component x state --**

```text
                                  rows    row_n  mean_outcome_bps_med  mean_outcome_bps_min  mean_outcome_bps_max
component          state
LEVEL_FORECAST_K12 INCOMPLETE       24      228              0.000000              0.000000              0.000000
                   NO_EVENT         39    20791              0.000000              0.000000              0.000000
                   NO_FEATURE       39   162057              0.000000              0.000000              0.000000
                   ORDER_CREATED    39   398024              0.053905             -0.387484              0.350157
LEVEL_FORECAST_K4  CENSORED          1        1              0.000000              0.000000              0.000000
                   INCOMPLETE       36      372              0.000000              0.000000              0.000000
                   NO_EVENT         39    20793              0.000000              0.000000              0.000000
                   NO_FEATURE       39   161931              0.000000              0.000000              0.000000
                   ORDER_CREATED    39   398003              0.063212             -0.165184              0.314668
LEVEL_NOW          CENSORED          1        1              0.000000              0.000000              0.000000
                   INCOMPLETE       39      426              0.000000              0.000000              0.000000
                   NO_EVENT         39    32191              0.000000              0.000000              0.000000
                   NO_FEATURE       39     1632              0.000000              0.000000              0.000000
                   ORDER_CREATED    39   546850              0.058932             -0.179157              0.355391
RANGE_SCALE        CENSORED          2        2              0.000000              0.000000              0.000000
                   INCOMPLETE      102     1032              0.000000              0.000000              0.000000
                   NO_EVENT        114    44291              0.000000              0.000000              0.000000
                   NO_FEATURE      114   147130              0.000000              0.000000              0.000000
                   ORDER_CREATED   114  1506145              0.053905             -0.414868              0.355391
SHOCK              CENSORED          1        1              0.000000              0.000000              0.000000
                   INCOMPLETE       54      576              0.000000              0.000000              0.000000
                   NO_EVENT         54    34940              0.000000              0.000000              0.000000
                   NO_FEATURE       54     1301              0.000000              0.000000              0.000000
                   ORDER_CREATED    54   767782              0.063260             -0.176811              0.276503
SWING_GT_CUR       CENSORED          1        1              0.000000              0.000000              0.000000
                   INCOMPLETE       30      336              0.000000              0.000000              0.000000
                   NO_EVENT         30    29717              0.000000              0.000000              0.000000
                   NO_FEATURE       30    10596              0.000000              0.000000              0.000000
                   ORDER_CREATED    30   406350              0.083640             -0.218949              0.165102
SWING_SCALE        CENSORED          1        1              0.000000              0.000000              0.000000
                   INCOMPLETE       42      456              0.000000              0.000000              0.000000
                   NO_EVENT         42    31650              0.000000              0.000000              0.000000
                   NO_FEATURE       42    16478              0.000000              0.000000              0.000000
                   ORDER_CREATED    42   577215              0.053615             -0.223582              0.283682
TAIL_RISK          CENSORED          1        1              0.000000              0.000000              0.000000
                   INCOMPLETE       33      366              0.000000              0.000000              0.000000
                   NO_EVENT         33    31198              0.000000              0.000000              0.000000
                   NO_FEATURE       33       33              0.000000              0.000000              0.000000
                   ORDER_CREATED    33   460102              0.053568             -0.132037              0.195504
```

**crypto selection_checks rows=3250**

**-- crypto / E_TOUCH selection check by component --**

```text
                    rows  payoff_ratio_med  payoff_ratio_min  payoff_ratio_max  sign_share_diff_med  excl_mean_median_gap_med  selected_n  excluded_n
component
LEVEL_FORECAST_K12   200               NaN               NaN               NaN             0.096379                       0.0     1078958      770010
LEVEL_FORECAST_K4    200               NaN               NaN               NaN             0.096216                       0.0     1079931      769037
LEVEL_NOW            200               NaN               NaN               NaN             0.097191                       0.0     1803430       45538
RANGE_SCALE          200               NaN               NaN               NaN             0.097068                       0.0     1818410       30558
SHOCK                200               NaN               NaN               NaN             0.097498                       0.0     1810940       38028
SWING_GT_CUR         200               NaN               NaN               NaN             0.096798                       0.0     1714065      134903
SWING_SCALE          200               NaN               NaN               NaN             0.097175                       0.0     1703717      145251
TAIL_RISK            200               NaN               NaN               NaN             0.097312                       0.0     1815100       33868
```

**-- crypto / E_CLOSE selection check by component --**

```text
                    rows  payoff_ratio_med  payoff_ratio_min  payoff_ratio_max  sign_share_diff_med  excl_mean_median_gap_med  selected_n  excluded_n
component
LEVEL_FORECAST_K12   200               NaN               NaN               NaN             0.092042                       0.0     1007216      841752
LEVEL_FORECAST_K4    200               NaN               NaN               NaN             0.091572                       0.0     1008132      840836
LEVEL_NOW            200               NaN               NaN               NaN             0.091673                       0.0     1683027      165941
RANGE_SCALE          200               NaN               NaN               NaN             0.091925                       0.0     1695262      153706
SHOCK                200               NaN               NaN               NaN             0.091808                       0.0     1690125      158843
SWING_GT_CUR         200               NaN               NaN               NaN             0.091211                       0.0     1599039      249929
SWING_SCALE          200               NaN               NaN               NaN             0.091674                       0.0     1587223      261745
TAIL_RISK            200               NaN               NaN               NaN             0.091976                       0.0     1694068      154900
```

**crypto state_sections rows=30978**

**-- crypto / E_TOUCH state sections by component x state --**

```text
                                    rows    row_n  mean_outcome_bps_med  mean_outcome_bps_min  mean_outcome_bps_max
component          state
LEVEL_FORECAST_K12 EVENT_UNDECIDED   278    10775              0.000000              0.000000              0.000000
                   INCOMPLETE        214     1900              0.000000              0.000000              0.000000
                   NO_EVENT          279    23540              0.000000              0.000000              0.000000
                   NO_FEATURE        325   841501              0.000000              0.000000              0.000000
                   ORDER_CREATED     325  2126857              0.320552            -37.908949             38.823723
LEVEL_FORECAST_K4  EVENT_UNDECIDED   278    10776              0.000000              0.000000              0.000000
                   INCOMPLETE        295     3100              0.000000              0.000000              0.000000
                   NO_EVENT          280    23543              0.000000              0.000000              0.000000
                   NO_FEATURE        325   840403              0.000000              0.000000              0.000000
                   ORDER_CREATED     325  2126751              0.301501            -49.275598             56.707003
LEVEL_NOW          EVENT_UNDECIDED   299    15284              0.000000              0.000000              0.000000
                   INCOMPLETE        325     3550              0.000000              0.000000              0.000000
                   NO_EVENT          283    35018              0.000000              0.000000              0.000000
                   NO_FEATURE        325    13600              0.000000              0.000000              0.000000
                   ORDER_CREATED     325  2937121              0.421045            -18.749848             28.582013
RANGE_SCALE        EVENT_UNDECIDED   836    35206              0.000000              0.000000              0.000000
                   INCOMPLETE        850     8600              0.000000              0.000000              0.000000
                   NO_EVENT          761    38934              0.000000              0.000000              0.000000
                   NO_FEATURE        950   779592              0.000000              0.000000              0.000000
                   ORDER_CREATED     950  7920266              0.455998            -34.377442             56.707003
SHOCK              EVENT_UNDECIDED   408    20089              0.000000              0.000000              0.000000
                   INCOMPLETE        450     4800              0.000000              0.000000              0.000000
                   NO_EVENT          379    36588              0.000000              0.000000              0.000000
                   NO_FEATURE        450    10902              0.000000              0.000000              0.000000
                   ORDER_CREATED     450  4087799              0.469514            -23.044007             21.316431
SWING_GT_CUR       EVENT_UNDECIDED   227    12056              0.000000              0.000000              0.000000
                   INCOMPLETE        250     2800              0.000000              0.000000              0.000000
                   NO_EVENT          221    33223              0.000000              0.000000              0.000000
                   NO_FEATURE        250   115081              0.000000              0.000000              0.000000
                   ORDER_CREATED     250  2148050              0.236871            -24.407000             52.859745
SWING_SCALE        EVENT_UNDECIDED   297    14332              0.000000              0.000000              0.000000
                   INCOMPLETE        318     3432              0.000000              0.000000              0.000000
                   NO_EVENT          280    30019              0.000000              0.000000              0.000000
                   NO_FEATURE        350   193712              0.000000              0.000000              0.000000
                   ORDER_CREATED     318  2994199              0.327469            -23.063379             24.643208
TAIL_RISK          EVENT_UNDECIDED   253    13396              0.000000              0.000000              0.000000
                   INCOMPLETE        275     3050              0.000000              0.000000              0.000000
                   NO_EVENT          245    34556              0.000000              0.000000              0.000000
                   NO_FEATURE        275      275              0.000000              0.000000              0.000000
                   ORDER_CREATED     275  2491054              0.147962            -17.225402             23.499742
```

**-- crypto / E_CLOSE state sections by component x state --**

```text
                                  rows    row_n  mean_outcome_bps_med  mean_outcome_bps_min  mean_outcome_bps_max
component          state
LEVEL_FORECAST_K12 INCOMPLETE      214     1900              0.000000              0.000000              0.000000
                   NO_EVENT        321   111511              0.000000              0.000000              0.000000
                   NO_FEATURE      325   841501              0.000000              0.000000              0.000000
                   ORDER_CREATED   325  2049661              0.571505            -42.865447             24.818247
LEVEL_FORECAST_K4  CENSORED          4        4              0.000000              0.000000              0.000000
                   INCOMPLETE      295     3100              0.000000              0.000000              0.000000
                   NO_EVENT        325   111571              0.000000              0.000000              0.000000
                   NO_FEATURE      325   840403              0.000000              0.000000              0.000000
                   ORDER_CREATED   325  2049495              0.585407            -42.087575             24.525697
LEVEL_NOW          CENSORED          4        4              0.000000              0.000000              0.000000
                   INCOMPLETE      325     3550              0.000000              0.000000              0.000000
                   NO_EVENT        325   172939              0.000000              0.000000              0.000000
                   NO_FEATURE      325    13600              0.000000              0.000000              0.000000
                   ORDER_CREATED   325  2814480              0.748591            -31.295930             17.552666
RANGE_SCALE        CENSORED          5        5              0.000000              0.000000              0.000000
                   INCOMPLETE      850     8600              0.000000              0.000000              0.000000
                   NO_EVENT        948   256594              0.000000              0.000000              0.000000
                   NO_FEATURE      950   779592              0.000000              0.000000              0.000000
                   ORDER_CREATED   950  7737807              0.544945            -57.571042             23.852170
SHOCK              CENSORED          4        4              0.000000              0.000000              0.000000
                   INCOMPLETE      450     4800              0.000000              0.000000              0.000000
                   NO_EVENT        450   192422              0.000000              0.000000              0.000000
                   NO_FEATURE      450    10902              0.000000              0.000000              0.000000
                   ORDER_CREATED   450  3952050              0.717000            -21.220796             21.521485
SWING_GT_CUR       CENSORED          4        4              0.000000              0.000000              0.000000
                   INCOMPLETE      250     2800              0.000000              0.000000              0.000000
                   NO_EVENT        246   155138              0.000000              0.000000              0.000000
                   NO_FEATURE      250   115081              0.000000              0.000000              0.000000
                   ORDER_CREATED   250  2038187              0.682428            -57.571042             26.779510
SWING_SCALE        CENSORED          2        2              0.000000              0.000000              0.000000
                   INCOMPLETE      318     3432              0.000000              0.000000              0.000000
                   NO_EVENT        312   166817              0.000000              0.000000              0.000000
                   NO_FEATURE      350   193712              0.000000              0.000000              0.000000
                   ORDER_CREATED   318  2871731              0.396017            -22.159185             24.816751
TAIL_RISK          CENSORED          4        4              0.000000              0.000000              0.000000
                   INCOMPLETE      275     3050              0.000000              0.000000              0.000000
                   NO_EVENT        275   166103              0.000000              0.000000              0.000000
                   NO_FEATURE      275      275              0.000000              0.000000              0.000000
                   ORDER_CREATED   275  2372899              0.649237            -19.394277             14.140450
```


## A6 — selected / excluded origin path census

**ctrader selected_excluded rows=5811000**

```text
                                            rows  mean_outcome_bps
entry_variant selection state
E_CLOSE       EXCLUDED  NO_EVENT          212286          0.000000
                        NO_FEATURE        308819          0.000000
              SELECTED  CENSORED               8          0.000000
                        INCOMPLETE          2022          0.000000
                        ORDER_CREATED    2382365          0.072678
E_TOUCH       EXCLUDED  NO_EVENT           75121          0.000000
                        NO_FEATURE        308819          0.000000
              SELECTED  EVENT_UNDECIDED     1539          0.000000
                        INCOMPLETE          2022          0.000000
                        ORDER_CREATED    2517999         -0.026589
```

**-- by arm_class x selection --**

```text
                                               rows  mean_outcome_bps
entry_variant arm_class          selection
E_CLOSE       FIXED_NATIVE       EXCLUDED       544          0.000000
                                 SELECTED     44156          0.053929
              NATIVE             EXCLUDED    233203          0.000000
                                 SELECTED   1197197          0.056254
              NATIVE_COMBINATION EXCLUDED    287358          0.000000
                                 SELECTED   1143042          0.090476
E_TOUCH       FIXED_NATIVE       EXCLUDED        33          0.000000
                                 SELECTED     44667          0.024455
              NATIVE             EXCLUDED    177840          0.000000
                                 SELECTED   1252560         -0.007998
              NATIVE_COMBINATION EXCLUDED    206067          0.000000
                                 SELECTED   1224333         -0.047393
```

**crypto selected_excluded rows=30045730**

```text
                                             rows  mean_outcome_bps
entry_variant selection state
E_CLOSE       EXCLUDED  NO_EVENT          1100525          0.000000
                        NO_FEATURE        1730953          0.000000
              SELECTED  CENSORED               27          0.000000
                        INCOMPLETE          16482          0.000000
                        ORDER_CREATED    12174878          0.591194
E_TOUCH       EXCLUDED  NO_EVENT           236561          0.000000
                        NO_FEATURE        1730953          0.000000
              SELECTED  EVENT_UNDECIDED     73689          0.000000
                        INCOMPLETE          16482          0.000000
                        ORDER_CREATED    12965180          0.374519
```

**-- by arm_class x selection --**

```text
                                               rows  mean_outcome_bps
entry_variant arm_class          selection
E_CLOSE       FIXED_NATIVE       EXCLUDED      3826          0.000000
                                 SELECTED    227295          0.488406
              NATIVE             EXCLUDED   1277001          0.000000
                                 SELECTED   6118871          0.546796
              NATIVE_COMBINATION EXCLUDED   1550651          0.000000
                                 SELECTED   5845221          0.639998
E_TOUCH       FIXED_NATIVE       EXCLUDED       321          0.000000
                                 SELECTED    230800          0.463474
              NATIVE             EXCLUDED    929164          0.000000
                                 SELECTED   6466708          0.428841
              NATIVE_COMBINATION EXCLUDED   1038029          0.000000
                                 SELECTED   6357843          0.310727
```
