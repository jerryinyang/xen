# SPDR-023 — analysis (fresh-context data analyst)

**Experiment:** Volatility-adaptive management after MR (mean-reversion) breach entries,
`CF-VOLDIR-001/HYP-D10`, checkpoint `2026-07-25-018-trade-opportunity-capture-geometry`.
**Run stamp:** `20260731T004708Z`, two universes, TRAIN only.
**Analyst artifacts:** `analysis_code/x1_census.py`, `x2_native_paired.py`, `x3_device_census.py`,
`x4_crypto_provenance.py`, `x5_device_outcomes.py`; full tables under `results/analyst/<universe>/`.
The canonical `analyse.py` was **not** modified and was **not** imported for any number here.

---

## 0. Standing declarations (binding on every number below)

```text
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: reported cost understates total cost; reported net performance is overstated
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

Spread is **not charged anywhere in this run**. Every cost-bearing figure understates cost.
The words *fully-net*, *cost-complete*, *tradable* and *deployable* are prohibited and are not used.

**There is no verdict in this document.** Per the approved design this experiment produces no
verdict, no recommended verdict and no disposition. What follows is observations for, observations
against, anomalies and open questions. The operator decides.

Further standing rules honoured throughout: crypto and cTrader are kept separate; **E-TOUCH and
E-CLOSE are kept separate and are never compared, aggregated or ranked against each other**;
per-stratum UNPOWERED is a power statement and never a negative; pooled grid-wide counts appear
only as disclosure, never as a headline; no comparison is made to SPDR-021 or SPDR-022.

**Normaliser / unit pin.** Native band geometry uses the SPDR-014 Z-VOL band at **H1**, width from
**EWMA Parkinson range (`park_ewma`, H1, lagged to `t-1`)**, fixed `z = 1.5`, fixed `H = 12` bars.
Device distances are multiples of **`range_scale_bps`** (H1, `t-1`), whose TRAIN median per symbol
is pinned in `calibration.parquet` (`median_range_scale_bps`). All outcomes are in **bps of entry
price**.

---

## 1. Integrity gate

| Check | Evidence | Result |
|---|---|---|
| Integrity self-check | `integrity_selfcheck.json` both universes: `blocking_pass: true`, 13/13 hard checks true (`causality`, `deterministic_replay`, `entry_parity`, `fence`, `future_shift_changed_mapping`, `golden_traces`, `management_lattice`, `native_lattice`, `no_native_management_cross`, `order_fill_position_reconciliation`, `provenance`, `row_accounting`, `unique_result_keys`) | PASS |
| Stale field | `run_summary.json` carries `"hard_integrity": "NOT_YET_RUN_TASK_8"` in **both** universes. `integrity_selfcheck.json` is authoritative and post-dates it (06:25 vs 06:24 file mtime, ctrader; 15:24 vs 15:20, crypto). | Stale string only — **not** reported as an integrity failure |
| TRAIN fence | ctrader `fence_attestation.json`: `status PINNED`, `train_end_utc 2023-11-22T00:00:00Z`, `holdout_start_utc 2024-12-13T00:00:00Z`, manifest `4cdc7b01…`. crypto: `train_end_utc 2023-12-18T00:00:00Z`, `holdout_start_utc 2025-01-08T00:00:00Z`, manifest `35d3375e…`. Max `decision_ts` observed = `2023-11-21 23:00:00Z` (ctrader), inside the fence. | PASS |
| Holdout | No holdout path read by any script in `analysis_code/x*.py`; all inputs are the two TRAIN run directories and `results/analysis/`. | No contact |
| Row accounting | See §2. Native rows = origins × arms **exactly**; policy rows = origins × arms × variants **exactly**; keys unique. | PASS |
| Shared-code boundary | No experiment-local accounting was imported. The only library import is `xen.evaluation.block_bootstrap_ci` (canonical). | PASS |

**Estimand-validation artifact.** There is no `results/estimand_validation.json` and none is
required: SPDR legs carry no estimand gate (`docs/references/spdr-lane.md`, *Artifacts*). The
integrity substitute — code-asserted fence + causal-lag self-check — is present and passing.

---

## 2. Row-key audit (pass condition)

**Method.** For each universe I counted `origins.parquet`; counted the native and policy schedules;
counted distinct composite keys; and checked the row count equals the exact Cartesian product of
origins × arms (× variants for the policy lattice). A pass requires *identity*, not sampling — if
rows equal the product and keys are unique, then every full-table row is uniquely addressed and
nothing can be hidden behind a top-N presentation.

| Quantity | cTrader | crypto |
|---|---|---|
| `origins.parquet` rows | 44,700 | 231,121 |
| native arms | 130 | 130 |
| native schedule rows | 5,811,000 | 30,045,730 |
| origins × arms | 5,811,000 | 30,045,730 |
| rows == product | **true** | **true** |
| distinct `(origin_id, native_arm_id)` | 5,811,000 | 30,045,730 |
| key unique | **true** | **true** |
| distinct origins covered | 44,700 (all) | 231,121 (all) |
| policy arms | 80 | 80 |
| policy schedule rows | 7,152,000 | 36,979,360 |
| origins × arms × 2 variants | 7,152,000 | 36,979,360 |
| rows == product / key unique | **true / true** | **true / true** |

**Result: PASS.** Every row of both full tables is represented exactly once under a unique
composite key, and every origin is covered by every arm. No top-N presentation is used anywhere in
this document: the complete per-stratum tables are emitted to
`results/analyst/<universe>/native_paired_per_stratum.csv` (384 ctrader / 3,136 crypto strata),
`arm_rates.csv` (390 / 3,250 rows), `device_arm_ledger_census.csv` (480 / 4,000 rows),
`device_reported_vs_ledger.csv` (498 / 4,120 rows) and
`device_outcomes_both_comparators.csv` (62 / 560 rows). Tables shown inline are *summaries of*
those files, never substitutes for them.

Emitted at `results/analyst/<universe>/row_key_audit.json`.

---

## 3. The seven items put to me — how each resolved

### Item 1 — `EVENT_UNDECIDED` is 100% E-TOUCH; `CENSORED` is 100% E-CLOSE. **CONFIRMED, and the mechanism is structural.**

Counts re-derived from the raw native schedule (`state_asymmetry_by_variant.csv`):

| state | cTrader E-TOUCH | cTrader E-CLOSE | crypto E-TOUCH | crypto E-CLOSE |
|---|---|---|---|---|
| `EVENT_UNDECIDED` | **1,539** (57 origins, 65 arms) | 0 | **73,689** (2,735 origins, 65 arms) | 0 |
| `CENSORED` | 0 | **8** (1 origin, 8 arms) | 0 | **27** (3 origins, 19 arms) |
| `NO_EVENT` | 75,121 | 212,286 | 236,561 | 1,100,525 |
| `NO_FEATURE` | 308,819 | 308,819 | 1,730,953 | 1,730,953 |
| `INCOMPLETE` | 2,022 | 2,022 | 16,482 | 16,482 |
| `ORDER_CREATED` | 2,517,999 | 2,382,365 | 12,965,180 | 12,174,878 |

Numbers match the bookkeeping claim exactly. **Mechanism, established from the data, not asserted:**

*`EVENT_UNDECIDED` is an E-TOUCH-only possibility.* Every one of the 1,539 / 73,689 rows carries
`side = 0` and `event_type = E_TOUCH`. An E-TOUCH event is a band touch by the H1 bar's high or low.
Within a single H1 bar **both** the upper and the lower band can be touched, and bar OHLC does not
say which came first. Resolving it would require intrabar order, which the `t-1` causal rule forbids.
The engine therefore books the event as occurring but the breach side as undecidable. An E-CLOSE
event is defined on the bar's *close*, which lies on exactly one side of the band by construction —
so `EVENT_UNDECIDED` is **structurally impossible** for E-CLOSE, not merely absent.

*`CENSORED` is an E-CLOSE-only possibility.* All 8 cTrader rows are one origin,
`USTEC-+0-e331bdd9d94809ab`, `decision_ts 2023-11-21 20:00Z`, `event_ts 2023-11-22 00:00:00Z` — which
is exactly `train_end_utc`. The two variants stamp events differently: max `event_ts` is
`2023-11-21 23:00Z` for E-TOUCH (bar-**open** stamp) and `2023-11-22 00:00Z` for E-CLOSE (bar-**close**
stamp, one hour later). An E-CLOSE event on the last TRAIN bar therefore lands *on* the fence and its
next real open falls outside TRAIN, so no entry can be made and the row is censored. E-TOUCH's
one-hour-earlier stamp means its next open is still `00:00Z`, inside the fence. Same structure in
crypto (3 origins, 19 arms).

**Bearing on the eligible population.** This is a boundary effect and a side-ambiguity effect, both
tiny: `EVENT_UNDECIDED` is 0.053% of E-TOUCH native rows (cTrader) and 0.49% (crypto); `CENSORED` is
0.00034% and 0.00022% of E-CLOSE rows. Neither materially changes any variant-level denominator.
The one substantive consequence is that **the two variants do not have identical eligible
populations by construction**, which is a further reason they are reported separately and never
substituted for one another. Note separately that the large `NO_EVENT` asymmetry (E-CLOSE 2.8×
E-TOUCH in cTrader, 4.7× in crypto) is the expected direction: a touch is easier to achieve than an
outside close.

### Item 2 — control row counts exceed origin counts. **CONFIRMED; they track `features.parquet`.**

| | cTrader | crypto |
|---|---|---|
| `origins.parquet` rows | 44,700 | 231,121 |
| `features.parquet` rows | 44,703 | 231,146 |
| `time_derangement.rows` (`controls.json`) | **44,703** | **231,146** |
| difference | +3 | +25 |

The derangement row count equals the **features** row count exactly in both universes, and the
excess over origins equals the **symbol count** exactly (3 and 25) — one extra feature row per
symbol, consistent with a terminal bar that has a feature vector but no usable forward window and
therefore no origin. `magnitude_match.rows` is a different population again (43,523 ctrader /
218,337 crypto, split 21,763 selected / 21,760 excluded and 109,175 / 109,162).

**Implication for control interpretation.** The time-derangement control was run over the feature
grid, not the traded-origin grid. It is therefore a valid statement about the *feature-to-time
mapping* (and the zero-fixed-point property is meaningful at that level), but it is **not** a
one-to-one derangement of the origins that produced trades, and its row count must not be read as an
episode count. Three surplus rows in cTrader cannot matter numerically; the point is definitional.

### Item 3 — `controls.parquet` says `DEFERRED_TO_STAGE_8` while `controls.json` carries computed values. **CONFIRMED. Both are true; use the run-side evidence.**

`results/analysis/<universe>/controls.parquet` (4 rows, identical in both universes):

| control | analysis_stage |
|---|---|
| `FIXED_DEVICE` | COMPUTED |
| `FIXED_NATIVE_PARAMETER` | COMPUTED |
| `TIME_DERANGEMENT` | DEFERRED_TO_STAGE_8 |
| `MAGNITUDE_MATCH` | DEFERRED_TO_STAGE_8 |

Run-side `controls.json` **already carries the computed result** for both "deferred" controls:

| | cTrader | crypto |
|---|---|---|
| `time_derangement.rows` | 44,703 | 231,146 |
| `time_derangement.seed` | 240730 | 240730 |
| `time_derangement.zero_fixed_points` | **true** | **true** |
| `magnitude_match.rows` | 43,523 | 218,337 |
| `magnitude_match.selected / excluded` | 21,763 / 21,760 | 109,175 / 109,162 |
| `ledger_rows` | 15,282,003 | 78,627,279 |
| `effect_quality_is_blocking` | false | false |

The two files are **not in conflict**: the parquet records that the *analysis stage* did not consume
these controls, while the JSON records that the *run stage* computed them. The controls evidence
that exists is therefore: (a) a time derangement with **zero fixed points** at seed 240730 over the
full feature grid — the derangement is genuine, no element maps to itself; (b) a magnitude-matched
split that is balanced to within 3 rows in cTrader and 13 rows in crypto. What does **not** exist is
any effect estimate computed *under* those controls. So there is presently **no control-based
collapse fraction for any stratum** — the derangement and magnitude-match controls are constructed
and attested but not yet exercised against an effect. This is a real gap in the evidence and is
carried into §7 as an open question, not scored as a failure.

`FIXED_DEVICE` and `FIXED_NATIVE_PARAMETER` are computed, and they are the comparators the estimates
in §5 and §6 actually rest on.

### Item 4 — `native_parameter_shared_trades.parquet` row counts. **CONFIRMED exactly; population established.**

| | cTrader | crypto |
|---|---|---|
| rows | **4,792,565** | **24,543,794** |
| distinct origins | 44,615 E-TOUCH / 44,126 E-CLOSE | — |
| `analysis_state` | `ALL` (single value) | `ALL` |
| `state` | `ORDER_CREATED` (single value) | `ORDER_CREATED` |

The claim that SPDR-021's file is empty is outside this experiment's scope and I did not read it;
the SPDR-023 counts are confirmed against the artifacts.

**Population it covers.** These are adaptive-arm rows (`NATIVE` + `NATIVE_COMBINATION`, never
`FIXED_NATIVE`) in schedule state `ORDER_CREATED`, joined to the fixed comparator on the **same
origin and same entry variant**, retained only where the fixed comparator was also `ORDER_CREATED`.
Arithmetic: adaptive `ORDER_CREATED` = 4,811,623; fixed-arm `ORDER_CREATED` origin-variant pairs =
88,741 of 89,400; residual 19,058 adaptive rows are dropped for having no fixed twin.
`paired_outcome_delta_bps = outcome_bps − fixed_outcome_bps` holds to 1e-9 on **all 4,792,565 rows**
(0 mismatches).

**Which paired reads it supports — and which it does not.** It supports common-origin paired native
geometry reads for `BAND_Z`, `BAND_H` and `BAND_Z+BAND_H` across all four orientation pairs, for
both variants, all symbols. It supports **no device read at all**: `device` is present but the file
holds only native arms. And its cost columns are empty — see §4.

### Item 5 — `episodes.parquet` and `native_parameter_schedule.parquet` byte-identical. **CONFIRMED, both universes.**

sha256 computed by me over the files on disk:

| universe | episodes.parquet | native_parameter_schedule.parquet | identical |
|---|---|---|---|
| cTrader | `adc5828d757a35f7d1c01881bb273df99a1e0cc73951b19820f79dfde8093425` | same | **yes** |
| crypto | `4fdf1bf453cf9c35becabcf2d4823d178b1758d06072a8a78eb1f93f2d11b938` | same | **yes** |

Independently reproduces the values in `integrity_selfcheck.json` / `row_accounting.json`.
**Double-counting avoided:** every episode figure in this document is drawn from
`native_parameter_schedule.parquet` (native lattice) or `episode_results.parquet` (the ledger).
`episodes.parquet` was never opened as a second source. Note that `run_summary.json`'s
`n_episodes` (5,811,000 / 30,045,730) is the *schedule row count under a second name*, not a count
of episodes that traded — the traded count is three orders of magnitude smaller (§4).

### Item 6 — crypto engine memory-release change between symbol groups. **CHECKED. No observable discontinuity.**

Group A = first 13 symbols in `config.json` order (BTCUSDT, ETHUSDT, SOLUSDT, AVAXUSDT, ORDIUSDT,
1000BONKUSDT, TIAUSDT, DOGEUSDT, XRPUSDT, LINKUSDT, ADAUSDT, BIGTIMEUSDT, BLURUSDT).
Group B = remaining 12 (1000PEPEUSDT, 1000LUNCUSDT, MATICUSDT, INJUSDT, SEIUSDT, BNBUSDT, WLDUSDT,
PYTHUSDT, DYDXUSDT, GALAUSDT, OPUSDT, 1000RATSUSDT).

| measure | A (pre-change, 13) | B (post-change, 12) |
|---|---|---|
| native rows | 16,040,570 | 14,005,160 |
| arms per symbol-variant (min/max) | 65 / 65 | 65 / 65 |
| ledger fill rate, mean (sd across symbols) | 0.05121 (0.00127) | 0.05189 (0.00210) |
| `EXIT_DENIED` total | 3,124 | 2,946 |
| `OPEN_AT_FENCE_END` total | 488 | 436 |
| state set observed | identical | identical |

The fill-rate difference is +0.00068 against a pooled cross-symbol sd of ≈0.0017 on n = 13 / 12
(≈0.4 sd, well inside symbol-to-symbol scatter). Arm counts, column schema and the set of observed
states are identical. The visible spread in per-symbol `order_created_share` (e.g. PYTHUSDT 0.62 vs
1000BONKUSDT 0.83) tracks each symbol's listing history length, and symbols with short histories
appear in **both** groups. **Conclusion: no discontinuity is observable in row shapes, state mixes or
fill rates.** One caveat on the check itself: the per-cell `run_metadata.json` timestamps are all
15:18–15:20 in alphabetical order, i.e. assembly time, not per-symbol execution time — so the A/B
split is taken from the declared config order and cannot be independently confirmed from file
metadata. Emitted at `crypto_provenance_per_symbol.csv` and `crypto_provenance_group_summary.csv`.

### Item 7 — stale `hard_integrity` string. **CONFIRMED stale; not reported as a failure.** See §1.

---

## 4. The two structural facts that condition everything below

These were not on the list. Both were found in the raw emissions and both change how every estimate
must be read, so they are stated before any effect.

### 4A. Most scheduled arm-origin candidates never became a trade — and non-trades are scored as **0.0 bps**, not excluded

The engine permits one open episode per instrument per entry variant *per arm*. The ledger
(`episode_results.parquet`) records the outcome:

| ledger state | cTrader rows |
|---|---|
| `BLOCKED_ACTIVE` | **11,202,554** (73.3%) |
| `ORDER_CREATED` | 797,090 |
| `FILLED` | 797,063 |
| `CLOSED` | 796,444 |
| `HOLD_DUE` | 725,011 |
| `NO_FEATURE` | 618,118 |
| `NO_EVENT` | 333,087 |
| `INCOMPLETE` | 8,844 |
| `EVENT_UNDECIDED` | 3,299 |
| `EXIT_DENIED` | 430 |
| `OPEN_AT_FENCE_END` | 28 |
| `DENIED` | 27 |
| `CENSORED` | 8 |
| total ledger rows | 15,282,003 (crypto: 78,627,279) |

In `native_parameter_shared_trades.parquet`, a row whose episode never became a position still
carries `outcome_bps = 0.0` (all 4,135,238 such cTrader rows have `_entry_ns` null, `_exit_reason`
null and `outcome_bps` exactly 0.0). The same imputation applies to `fixed_outcome_bps`. So the
emitted paired delta mixes two different things.

Composition of the paired population, decided by joining the ledger's `FIXED_NATIVE`/`FILLED` set:

| | cTrader rows | share | crypto rows | share |
|---|---|---|---|---|
| **neither** arm traded — delta identically 0 | 3,643,942 | **76.0%** | 19,133,761 | **78.0%** |
| only the **fixed** arm traded — delta = −fixed | 491,296 | 10.3% | — | — |
| only the **adaptive** arm traded — delta = +adaptive | 432,169 | 9.0% | — | — |
| **both** traded — genuine like-for-like | **225,158** | **4.7%** | **920,307** | **3.7%** |
| adaptive traded (any) | 657,327 | 13.7% | 3,247,990 | 13.2% |
| fixed traded (any) | 716,454 | 15.0% | 3,082,350 | 12.6% |

Group means on the cTrader composition: both-traded +0.159 bps; adaptive-only −0.096; fixed-only
−0.305; neither 0.000.

**Two consequences, both directional.** (i) The point estimate is shrunk toward zero by a 76–78%
mass of structural zeros. (ii) The *variance* is deflated by the same zero mass, so the bootstrap CI
is narrower and the MDE smaller than the traded evidence supports — an MDE computed on 12,480 rows
of which 592 are trades is not a 12,480-trade MDE. Because of (i) and (ii) together, I report every
native stratum under **three lenses** and never one: `L1_ALL` (as emitted), `L2_EITHER`, `L3_BOTH`.
`L1_ALL` reproduces the emitted estimand and is the occupancy-inclusive read; `L3_BOTH` is the only
like-for-like per-trade read.

### 4B. The management-device matrix has almost no episodes, while its emitted power columns describe the origin population

For each management arm I counted what the ledger actually recorded
(`device_arm_ledger_census.csv`) and set it beside the `episode_n` / `effective_n` in the canonical
`device_*.parquet` (`device_reported_vs_ledger.csv`).

cTrader, by arm class (480 arm-strata = arm × variant × symbol):

| arm_class | filled episodes | blocked | exit_denied | **median filled per stratum** |
|---|---|---|---|---|
| `FIXED_MANAGEMENT` | 43,437 | 1,198,937 | 62 | **1** |
| `MANAGEMENT` | 2,118 | 3,636,263 | 133 | **1** |
| `MANAGEMENT_COMPONENT_COMBINATION` | 132 | 1,952,170 | 0 | **1** |
| `MANAGEMENT_DEVICE_COMBINATION` | 78,530 | 187,693 | 96 | 4,916.5 |

crypto, same census (4,000 arm-strata):

| arm_class | filled | blocked | exit_denied | median filled per stratum |
|---|---|---|---|---|
| `FIXED_MANAGEMENT` | 226,000 | 6,166,344 | 487 | **1** |
| `MANAGEMENT` | 34,158 | 18,687,398 | 1,030 | **1** |
| `MANAGEMENT_COMPONENT_COMBINATION` | 1,100 | 10,044,892 | 0 | **1** |
| `MANAGEMENT_DEVICE_COMBINATION` | 426,810 | 942,978 | 380 | 2,199 |

Distribution of the 498 cTrader device strata by episodes actually filled, against what the device
tables report for the same stratum:

| filled episodes | strata | median reported `episode_n` | median reported `effective_n` |
|---|---|---|---|
| **< 10** | **438** (88%) | 14,614 | 728 |
| 10–99 | 11 | ~14,500 | 727 |
| 100–999 | 6 | ~14,497 | 727 |
| ≥ 1,000 | 43 | 14,614 | 728 |

Median reported `episode_n` = 14,614 against a median actual filled count of **1**.

**Mechanism, traced to a single named arm.** `FIXED_TARGET_M1.00` (E-TOUCH) shows: `FILLED` 3,
`EXIT_DENIED` 3 (reason `TARGET`), `CLOSED` **0**, `BLOCKED_ACTIVE` 44,612. It filled once per
symbol, its target exit was denied, the position never closed, and the arm sat blocked for the
remaining 44,612 origins. `ADP_LEVEL_FORECAST_K12_TRAIL_STATE_LOW_075_HIGH_150` (E-TOUCH): `FILLED`
7, `CLOSED` 4 by `TRAIL`, `EXIT_DENIED` 3, then `BLOCKED_ACTIVE` 44,608. By contrast every arm
carrying a **time cap** kept cycling: `FIXED_HOLD_B4` 4,038 fills / 4,036 closes;
`FIXED_BASELINE_PLAIN` 5,723 / 5,722; `DC_TARGET_STOP_HOLD` 28,841 fills, closing 14,207 by STOP,
14,132 by TARGET, 502 by HOLD.

So: **an arm whose exit set is purely price-triggered (target / stop / trail, no hold) hit an
`EXIT_DENIED` on its first episode and was blocked for the remainder of TRAIN.** Total
`EXIT_DENIED` is only 430 rows in cTrader — a small number of denials was sufficient to disable most
of the 160 management arms permanently, because each denial is absorbing.

The pure `SIZE` device family produced **no closed episode at all** in cTrader; it does not appear in
the reconstructed outcome table. `TARGET+STOP` appears only in crypto.

**Consequence.** The `episode_n` and `effective_n` columns in `device_target/stop/trail/hold/size
.parquet`, and the `mde` derived from them (medians ≈0.02–0.12 bps), describe the *eligible origin*
population, not the device episodes observed. They should not be read as trade-level power for any
stratum where the ledger shows fewer than ~100 filled episodes — which is 88% of cTrader device
strata. This is a measurement-availability statement, not an effect statement, and it is not a
negative about any device.

---

## 5. Native geometry — every component, orientation and combination, per stratum

Estimand: **common-origin paired change, adaptive minus fixed, in bps of entry price**, on the same
origin and same entry variant. Comparator: `FIXED_NATIVE_BAND_<variant>` (`z = 1.5`, `H = 12`) —
this is the **fixed-device / fixed-parameter comparison**. Uncertainty: circular block bootstrap,
**block = 24 H1 bars ≥ the maximum native horizon of 24**, 5-seed battery, 400 replicates per seed,
median of the per-seed bounds; the per-seed low band is retained so MC fragility near zero is
visible. `effective_n` = number of dependence blocks = ⌈n/24⌉. `MDE = 2.8 · sd / √effective_n`.

Strata: **384 cTrader** (3 symbols × 2 variants × 8 components × 8 orientations) and
**3,136 crypto** (25 symbols × 2 variants × 8 components × 8 orientations, 64 short of the 3,200
product where a component produced no shared row). Complete tables — every stratum, every lens, with
estimate, interval, count, effective count and MDE together — are at
`results/analyst/<universe>/native_paired_per_stratum.csv`.

### 5.1 All eight components are present and separately visible

`LEVEL_NOW`, `LEVEL_FORECAST_K4`, `LEVEL_FORECAST_K12`, `RANGE_SCALE`, `SWING_SCALE`,
`SWING_GT_CUR`, `SHOCK`, `TAIL_RISK` — each appears in the native schedule with exactly 715,200
cTrader rows (= 44,700 origins × 16 arms), plus 89,400 rows for the fixed arm (`component` null).
Every component × parameter × orientation cell is populated: 64 cells (8 × 8), verified by direct
group-by on the shared-trades table.

### 5.2 All four native orientation pairs, and both single-parameter orientations, are visible

| arm class | parameter | orientation(s) | cTrader schedule rows |
|---|---|---|---|
| `FIXED_NATIVE` | `BAND_Z+BAND_H` | `FIXED` | 89,400 |
| `NATIVE` | `BAND_Z` | `DIRECT` | 715,200 |
| `NATIVE` | `BAND_Z` | `REVERSE` | 715,200 |
| `NATIVE` | `BAND_H` | `DIRECT` | 715,200 |
| `NATIVE` | `BAND_H` | `REVERSE` | 715,200 |
| `NATIVE_COMBINATION` | `BAND_Z+BAND_H` | `DIRECT_DIRECT` | 715,200 |
| `NATIVE_COMBINATION` | `BAND_Z+BAND_H` | `DIRECT_REVERSE` | 715,200 |
| `NATIVE_COMBINATION` | `BAND_Z+BAND_H` | `REVERSE_DIRECT` | 715,200 |
| `NATIVE_COMBINATION` | `BAND_Z+BAND_H` | `REVERSE_REVERSE` | 715,200 |

Fixed, direct, reverse and all four pairs are each present for z and H. **The individual z-only and
H-only strata are reported below before any combination stratum is interpreted**, as the
characterisation contract requires.

### 5.3 Component before combination — cTrader (summary of the 384-row table)

Medians across the 24 strata in each cell (3 symbols × 8 components). `L1` = as emitted;
`L3` = both-traded only. `ci≠0` counts strata whose bootstrap 95% CI excludes zero, disclosure only.

**E-TOUCH** (never compared with E-CLOSE):

| parameter | orientation | strata | L1 median est (bps) | L1 ci≠0 | L3 median n | L3 median est (bps) | L3 max abs est | L3 ci≠0 |
|---|---|---|---|---|---|---|---|---|
| BAND_Z | DIRECT | 24 | −0.0144 | 2 | 418 | +0.287 | 3.083 | 4 |
| BAND_Z | REVERSE | 24 | −0.0133 | 0 | 380 | +0.559 | 7.985 | 5 |
| BAND_H | DIRECT | 24 | −0.0025 | 0 | 1,060 | **0.000** | 2.763 | 0 |
| BAND_H | REVERSE | 24 | −0.0007 | 0 | 1,058 | **0.000** | 2.763 | 0 |
| BAND_Z+BAND_H | DIRECT_DIRECT | 24 | −0.0337 | 2 | 542 | +0.197 | 1.964 | 4 |
| BAND_Z+BAND_H | DIRECT_REVERSE | 24 | −0.0122 | 4 | 510 | +0.331 | 2.294 | 4 |
| BAND_Z+BAND_H | REVERSE_DIRECT | 24 | −0.0204 | 0 | 385 | +0.305 | 4.822 | 2 |
| BAND_Z+BAND_H | REVERSE_REVERSE | 24 | −0.0017 | 0 | 394 | +0.252 | 2.766 | 2 |

**E-CLOSE** (never compared with E-TOUCH):

| parameter | orientation | strata | L1 median est (bps) | L1 ci≠0 | L3 median n | L3 median est (bps) | L3 max abs est | L3 ci≠0 |
|---|---|---|---|---|---|---|---|---|
| BAND_Z | DIRECT | 24 | +0.0134 | 1 | 565 | −0.064 | 2.421 | 4 |
| BAND_Z | REVERSE | 24 | −0.0002 | 0 | 389 | +0.640 | 3.261 | 6 |
| BAND_H | DIRECT | 24 | −0.0206 | 1 | 852 | **0.000** | 0.000 | 0 |
| BAND_H | REVERSE | 24 | −0.0197 | 3 | 846 | **0.000** | 0.000 | 0 |
| BAND_Z+BAND_H | DIRECT_DIRECT | 24 | +0.0357 | 1 | 404 | −0.303 | 3.279 | 6 |
| BAND_Z+BAND_H | DIRECT_REVERSE | 24 | −0.0325 | 0 | 435 | +0.156 | 8.848 | 8 |
| BAND_Z+BAND_H | REVERSE_DIRECT | 24 | −0.0306 | 0 | 327 | +0.056 | 6.835 | 4 |
| BAND_Z+BAND_H | REVERSE_REVERSE | 24 | −0.0382 | 0 | 399 | −0.032 | 3.071 | 2 |

### 5.4 Component before combination — crypto (summary of the 3,136-row table)

**E-TOUCH:**

| parameter | orientation | strata | L1 median est | L1 ci≠0 | L3 median n | L3 median est | L3 median MDE | L3 ci≠0 |
|---|---|---|---|---|---|---|---|---|
| BAND_Z | DIRECT | 196 | −0.0007 | 28 | 68 | +1.116 | 140.7 | 28 |
| BAND_Z | REVERSE | 196 | −0.0480 | 36 | 60 | +3.670 | 129.9 | 36 |
| BAND_H | DIRECT | 196 | +0.1098 | 2 | 315 | **0.000** | 0.0 | 2 |
| BAND_H | REVERSE | 196 | +0.0942 | 1 | 284 | **0.000** | 0.0 | 1 |
| BAND_Z+BAND_H | DIRECT_DIRECT | 196 | +0.0470 | 36 | 68 | +0.890 | 116.5 | 36 |
| BAND_Z+BAND_H | DIRECT_REVERSE | 196 | +0.0297 | 29 | 78 | +1.510 | 119.9 | 29 |
| BAND_Z+BAND_H | REVERSE_DIRECT | 196 | −0.0113 | 42 | 59 | +1.621 | 115.2 | 42 |
| BAND_Z+BAND_H | REVERSE_REVERSE | 196 | +0.0087 | 38 | 82 | +2.468 | 106.8 | 38 |

**E-CLOSE:**

| parameter | orientation | strata | L1 median est | L1 ci≠0 | L3 median n | L3 median est | L3 median MDE | L3 ci≠0 |
|---|---|---|---|---|---|---|---|---|
| BAND_Z | DIRECT | 196 | −0.0121 | 36 | 202 | +0.663 | 123.3 | 36 |
| BAND_Z | REVERSE | 196 | +0.0474 | 42 | 194 | +2.353 | 106.6 | 42 |
| BAND_H | DIRECT | 196 | −0.0129 | 1 | 427 | **0.000** | 0.0 | 1 |
| BAND_H | REVERSE | 196 | +0.0110 | 3 | 419 | **0.000** | 0.0 | 3 |
| BAND_Z+BAND_H | DIRECT_DIRECT | 196 | +0.0630 | 36 | 175 | +0.422 | 129.4 | 36 |
| BAND_Z+BAND_H | DIRECT_REVERSE | 196 | +0.0243 | 34 | 200 | +1.403 | 135.0 | 34 |
| BAND_Z+BAND_H | REVERSE_DIRECT | 196 | +0.0181 | 40 | 197 | +2.573 | 111.1 | 40 |
| BAND_Z+BAND_H | REVERSE_REVERSE | 196 | +0.2361 | 33 | 199 | +1.007 | 103.7 | 33 |

Crypto L3 MDEs of 100–140 bps against median estimates of 0.4–3.7 bps say plainly that the crypto
both-traded strata are **UNPOWERED at the per-trade level** — a power statement about the
measurement, carrying no sign and no implication about the effect. The crypto `L3 max abs est`
reaches 1,322–1,629 bps in some strata, which is a heavy-tail warning, not a finding (§7).

### 5.5 A clean mechanistic result: H alone moves availability, not per-trade outcome

Restricting to rows where **both** arms traded:

| universe | both-traded BAND_H rows | rows with non-zero delta | share of rows with **identical entry timestamp** |
|---|---|---|---|
| cTrader | 92,257 | **9** (0.010%) | **100.000%** |
| crypto | 425,909 | **110** (0.026%) | **100.000%** |

When an H-only arm and the fixed arm both trade the same origin, the entry timestamp is identical in
every single case, and the realised P&L delta is exactly zero in 99.97–99.99% of rows. This is
mechanically coherent: `H` sets the window within which a breach must occur, so it changes *whether*
an event exists, never *where* the entry lands or *when* the 4-bar exit falls. Across the full
adaptive-traded population (both traded or not) the H-only exact-zero delta share is 53.9% (cTrader)
and 51.1% (crypto), the remainder being rows where the fixed twin did not trade.

**Read carefully:** this does not say H does nothing. It localises H's entire measured effect to the
availability / selection channel, where §5.6 shows it does move numbers. It is also why any
combined `BAND_Z+BAND_H` L3 estimate is, on the both-traded subset, effectively a z estimate — a
point the operator should weigh before reading the combination rows as a joint effect.

### 5.6 Band-event rate, decided-side rate and selectivity — every arm, separately by variant

Per the design these are emitted for every arm. Full tables: `results/analyst/<universe>/arm_rates.csv`
(390 cTrader / 3,250 crypto rows = arm × symbol × variant). Definitions used, stated explicitly:
**band-event rate** = rows with a non-null `event_type` ÷ eligible origins;
**decided-side rate** = rows with an event and `side ≠ 0` ÷ rows with an event;
**selectivity** = filled rows ÷ eligible origins.

cTrader:

| variant | arm class | n | band-event rate (median) | decided-side rate (median / min / max) | selectivity (median / min) |
|---|---|---|---|---|---|
| E-TOUCH | FIXED_NATIVE | 3 | 1.0000 | 0.99795 / 0.99767 / 0.99870 | 0.9979 / 0.9977 |
| E-TOUCH | NATIVE | 96 | 1.0000 | 0.96489 / 0.56411 / 0.99870 | 0.9649 / 0.5641 |
| E-TOUCH | NATIVE_COMBINATION | 96 | 1.0000 | 0.94976 / 0.52989 / 0.99679 | 0.9498 / 0.5299 |
| E-CLOSE | FIXED_NATIVE | 3 | 1.0000 | 0.98671 / 0.98510 / 0.98969 | 0.9867 / 0.9851 |
| E-CLOSE | NATIVE | 96 | 1.0000 | 0.91678 / 0.51388 / 0.99630 | 0.9168 / 0.5138 |
| E-CLOSE | NATIVE_COMBINATION | 96 | 1.0000 | 0.86724 / 0.47382 / 0.98787 | 0.8672 / 0.4738 |

crypto:

| variant | arm class | n | band-event rate (median) | decided-side rate (median / min / max) | selectivity (median / min) |
|---|---|---|---|---|---|
| E-TOUCH | FIXED_NATIVE | 25 | 1.0000 | 0.99312 / 0.97311 / 0.99769 | 0.9931 / 0.9731 |
| E-TOUCH | NATIVE | 800 | 1.0000 | 0.95355 / 0.00000 / 0.99786 | 0.9536 / 0.0000 |
| E-TOUCH | NATIVE_COMBINATION | 800 | 1.0000 | 0.93228 / 0.00000 / 0.99667 | 0.9323 / 0.0000 |
| E-CLOSE | FIXED_NATIVE | 25 | 1.0000 | 0.98519 / 0.96065 / 0.99208 | 0.9852 / 0.9606 |
| E-CLOSE | NATIVE | 800 | 1.0000 | 0.89076 / 0.00000 / 0.99304 | 0.8908 / 0.0000 |
| E-CLOSE | NATIVE_COMBINATION | 800 | 1.0000 | 0.83096 / 0.00000 / 0.98920 | 0.8310 / 0.0000 |

Three things are visible and each is a magnitude, not a qualifier. (a) **Band-event rate is ~1.0 for
every arm in the grid** — essentially every eligible origin produces a band event regardless of the
volatility component or orientation, so the z/H band is not an event-level filter in this
configuration. (b) **Decided-side rate is where the two variants genuinely separate**: E-CLOSE arms
sit lower (median 0.917 / 0.867 cTrader) than E-TOUCH arms (0.965 / 0.950) — reported side by side
as separate facts, not as a preference. (c) **Selectivity spans 0.47–1.00** across adaptive arms and
falls to 0.00 for some crypto strata; that spread, not the event rate, is the channel the native
arms actually move.

---

## 6. Management devices — every device before any combination

Device-native measures, never a shared universal score. The emitted canonical tables carry, per
device family:

| device family | device-native metrics emitted | cTrader rows |
|---|---|---|
| TARGET | `reach_rate`, `realised_capture_bps`, `missed_excess_bps`, `time_to_target` | 2,376 |
| STOP | `stop_rate`, `loss_severity_bps`, `adverse_excursion_bps`, `recovery_after_stop_bps` | 2,160 |
| TRAIL | `peak_giveback_bps`, `favourable_excursion_captured`, `loss_tail_bps` | 1,215 |
| HOLD | `outcome_by_time_bps`, `decay_bps`, `holding_efficiency`, `opportunity_duration` | 1,620 |
| SIZE | `drawdown_bps`, `tail_loss_bps`, `concentration`, `risk_dispersion` | 1,188 |

Settings present, per device, before any combination: TARGET `M0.75 / M1.00 / M1.50 /
STATE_LOW_075_HIGH_150 / …_ON_RANGE_SCALE / …_ON_SHOCK`; STOP the same five; TRAIL the same five;
HOLD `B2 / B4 / B12 / STATE_LOW_4_HIGH_12 / STATE_SHOCK_2`; SIZE `UNIT / SCALE_NORMALISED /
STATE_HALVE_HIGH / STATE_LOW_075_HIGH_150_ON_RANGE_SCALE / …_ON_SHOCK`. Device **combinations**
(`TARGET+STOP`, `TARGET+STOP+HOLD`, `TRAIL+HOLD`) are separately labelled and are reported after the
singles, never in place of them.

Observed states retained in the device tables: `ORDER_CREATED`, `NO_EVENT`, `NO_FEATURE`,
`INCOMPLETE`, `EVENT_UNDECIDED`. `EVENT_UNDECIDED` device rows number exactly half the other states'
rows in every family (264 of 528 for TARGET, 240 of 480 for STOP, …) — the E-TOUCH half only, which
is §3 item 1 propagating correctly. `CENSORED` does **not** appear in any device table, so the 8/27
censored E-CLOSE rows are absent from the device layer; that is an omission the operator should note.

### 6.1 What is measurable, and what is not

Because of §4B, I rebuilt device outcomes independently from the ledger's own `FILLED` and `CLOSED`
price rows (signed by `side`, in bps of entry price), which is **gross of all cost** — fees and
funding are not recoverable from those two rows, so this measure is *not* the canonical
cost-bearing figure and is labelled `realised_outcome_bps_gross_of_all_cost`.

Traded management episodes: **123,764** (cTrader), **684,309** (crypto). Of 480 cTrader management
arm-strata, only **62** produced any closed episode at all.

cTrader, by device, with **both** comparators tested for availability:

| device | arm-strata with ≥1 closed episode | median traded episodes | fixed-device comparator available | plain-baseline comparator available |
|---|---|---|---|---|
| HOLD | 18 | 1,166.5 | **18** | 18 |
| NONE (plain baseline) | 6 | 2,525.5 | n/a | 6 |
| STOP | 10 | 61.5 | **0** | 10 |
| TARGET | 8 | 3.0 | **0** | 8 |
| TRAIL | 8 | 3.0 | **0** | 8 |
| TARGET+STOP+HOLD | 6 | 8,084.0 | **0** | 6 |
| TRAIL+HOLD | 6 | 4,916.5 | **0** | 6 |
| SIZE | **0** | — | — | — |

crypto:

| device | arm-strata with ≥1 closed episode | median traded episodes | fixed-device comparator available | plain-baseline comparator available |
|---|---|---|---|---|
| HOLD | 150 | 853.0 | 150 | 147 |
| NONE | 49 | 1,223.0 | n/a | 49 |
| STOP | 50 | 70.0 | 32 | 46 |
| TARGET | 128 | 116.5 | 48 | 122 |
| TRAIL | 73 | 114.0 | 28 | 69 |
| TARGET+STOP | 10 | 675.5 | 8 | 9 |
| TARGET+STOP+HOLD | 50 | 5,605.5 | 8 | 49 |
| TRAIL+HOLD | 50 | 3,615.0 | 7 | 49 |
| SIZE | **0** | — | — | — |

**Stated plainly, as required: where a measure is unavailable I say so rather than substituting a
common score.**
- **SIZE device: UNAVAILABLE in both universes** — no closed episode, so no outcome, no interval,
  no MDE. The canonical `device_size.parquet` nevertheless reports `episode_n ≈ 14,614` on 66
  cTrader strata, all of which have <10 filled episodes.
- **Fixed-device comparison for TARGET / STOP / TRAIL: UNAVAILABLE in cTrader** — the fixed
  comparators `FIXED_TARGET_M1.00`, `FIXED_STOP_M1.00`, `FIXED_TRAIL_M1.00` each closed **zero**
  episodes, so there is nothing to pair against. It is partially available in crypto (28–48 of the
  strata).
- **Plain-baseline comparison: AVAILABLE** for every stratum with any closed episode (62 / 62
  cTrader; 542 / 560 crypto). This is the comparison the operator can actually use for
  TARGET / STOP / TRAIL in cTrader.
- **`partial_cost_bps` on the native shared-trades table: 100% NULL** in both universes
  (4,792,565 / 24,543,794 rows). Likewise `time_to_target` and `recovery_after_stop_bps`. The
  excursion family (`mfe_bps`, `mae_bps`, `adverse_excursion_bps`, `peak_giveback_bps`, `decay_bps`,
  `holding_efficiency`, `opportunity_duration`, `realised_capture_bps`, `missed_excess_bps`) is
  86.3% / 86.8% NULL — populated only on the rows that actually traded. **So no cost-bearing native
  figure exists in this run at all**; the partial-cost caveat is doubly binding there.

### 6.2 A caution on the plain baseline

On every origin where both traded, `FIXED_BASELINE_PLAIN` and `FIXED_HOLD_B4` produce an **exactly
identical** outcome (delta 0.000, CI [0.000, 0.000], n = 2,559 EURUSD E-CLOSE; n = 79 EURUSD
E-TOUCH). This is consistent with the design's baseline ("no target, stop or trail, exits after four
H1 bars") being the same policy as the B4 hold under a second arm id. The two are therefore **not
independent comparators**; a device compared against both has effectively been compared once. Their
*occupancy* histories do differ (5,723 vs 4,038 fills, E-TOUCH cTrader), so their episode sets are
not identical even though their per-episode policy is.

Full per-stratum device results with both comparators, each carrying estimate, interval, count,
effective count and MDE, are at `results/analyst/<universe>/device_outcomes_both_comparators.csv`.
Illustrative EURUSD rows (magnitudes with uncertainty, no adjudication):
`FIXED_HOLD_B12` E-CLOSE vs plain, n = 19, −2.216 bps, CI [−5.493, +0.894];
`FIXED_HOLD_B2` E-CLOSE vs plain, n = 1,688, −0.223 bps, CI [−0.841, +0.372];
`DC_TARGET_STOP_HOLD` E-CLOSE vs plain, n = 2,493, +0.213 bps, CI [−0.448, +0.908];
`DC_TRAIL_HOLD` E-CLOSE vs plain, n = 2,019, +0.250 bps, CI [−0.431, +0.915];
`DC_TRAIL_HOLD` E-TOUCH vs plain, n = 54, −2.577 bps, CI [−5.403, +0.089];
`ADP_LEVEL_FORECAST_K12_TARGET_…` E-TOUCH vs plain, **n = 1**, −8.099 bps, interval degenerate —
UNPOWERED, reported as a power statement only.

---

## 7. Observations FOR (the volatility components do move measurable quantities)

Each is a magnitude with uncertainty on a named stratum set, not a verdict.

1. **The components move selectivity substantially.** Adaptive native arms span a selectivity of
   0.47–1.00 (cTrader) and 0.00–1.00 (crypto) against fixed-arm selectivity of 0.985–0.998. That is
   a change of up to half the traded population, driven entirely by the volatility component, on a
   base whose event rate is pinned at ~1.0. Under the base-conditional directive this is a positive
   quantification of volatility context in its own right, independent of whether any arm is
   profitable.
2. **Decided-side rate responds to the component.** E-TOUCH adaptive arms range 0.564–0.999
   (cTrader) around a fixed value of 0.998; E-CLOSE adaptive arms range 0.514–0.996 around 0.987.
   Some component/orientation choices leave nearly half of E-TOUCH events side-undecidable.
3. **H's channel is cleanly identified.** Entry timestamps are identical in 100% of both-traded
   H-only rows and the P&L delta is exactly zero in 99.97–99.99% of them (92,257 and 425,909 rows).
   H is an availability lever with a measured, essentially exact null on per-trade outcome — a
   sharp, reproducible mechanical fact across both universes.
4. **Some both-traded z and z+H strata carry intervals excluding zero.** cTrader: 4–8 of 24 strata
   per cell for the z and combination orientations (e.g. E-CLOSE `DIRECT_REVERSE` 8/24, median
   +0.156 bps, max |est| 8.85 bps). crypto: 28–42 of 196 per cell. Disclosure of counts only; the
   binding per-stratum magnitudes are in the emitted CSVs.
5. **Device combinations that include a time cap are genuinely measurable and show non-trivial
   episode counts.** `DC_TARGET_STOP_HOLD` closed 14,207 by STOP, 14,132 by TARGET and 502 by HOLD
   in cTrader — the target and stop devices *do* fire and *are* measurable when paired with a hold.
6. **The paired construction itself is sound where it applies.** `paired_outcome_delta_bps` equals
   `outcome_bps − fixed_outcome_bps` on all 4,792,565 rows to 1e-9; keys are unique; every origin is
   covered by every arm. The join is not the problem anywhere in this run.

## 8. Observations AGAINST (reasons to distrust or narrow the above)

1. **76–78% of every native paired estimate is structural zeros.** Both arms failed to trade on
   3,643,942 of 4,792,565 cTrader rows and 19,133,761 of 24,543,794 crypto rows. Those rows have a
   delta of exactly 0 by imputation, not by measurement. They shrink the point estimate toward zero
   *and* deflate the variance, so the emitted `L1` intervals are narrower and the MDEs smaller than
   the traded evidence supports. Any `L1` interval that excludes zero should be re-read against its
   `L3` counterpart before it is believed.
2. **The pairing is asymmetric in a way that biases sign.** A pair is formed on *scheduled* fixed
   `ORDER_CREATED`, not on the fixed arm having traded. Consequently 10.3% of cTrader rows contribute
   `−fixed` with the adaptive arm scored 0, and 9.0% contribute `+adaptive` with the fixed arm scored
   0. Group means differ by direction (fixed-only −0.305, adaptive-only −0.096, both +0.159), so the
   `L1` estimate is partly a statement about *relative occupancy*, not about the geometry.
3. **The whole external management device matrix is close to unmeasurable in cTrader.** 438 of 498
   device strata (88%) have fewer than 10 filled episodes; the median is **1**. Every one of them
   reports `episode_n ≈ 14,614` and `effective_n ≈ 728`. Point 5 of §7 applies only to the ~43 strata
   with ≥1,000 episodes.
4. **The failure is absorbing and asymmetric across device families.** Arms with a purely
   price-triggered exit were disabled by an `EXIT_DENIED` on their first episode and blocked for the
   rest of TRAIN (`FIXED_TARGET_M1.00`: 3 fills, 3 denials, 0 closes, 44,612 blocked). This is not
   uniform noise — it removes the target, stop, trail and size families preferentially while leaving
   the hold family and the hold-containing combinations intact. Any cross-device reading of this run
   is reading a survivorship pattern.
5. **Crypto per-trade power is absent.** Both-traded MDEs are 100–140 bps against median estimates of
   0.4–3.7 bps. These strata are UNPOWERED — again, a power statement, never a negative.
6. **Extreme both-traded values in crypto.** `L3` max |estimate| reaches 1,322 and 1,629 bps in some
   strata against median estimates near 1 bps. Mean-based reads on those strata are outlier-exposed;
   the medians are emitted alongside in the CSV for exactly this reason.
7. **No control-conditioned effect exists.** `TIME_DERANGEMENT` and `MAGNITUDE_MATCH` are constructed
   and attested but were not exercised against any estimate (§3 item 3), so there is **no collapse
   fraction and no leak-tripwire read for any stratum in this analysis**. The design's `HARD`
   requirement of a zero-fixed-point derangement is met as a construction; its evidentiary use is not.
8. **The two comparators are not two.** Plain baseline ≡ `FIXED_HOLD_B4` on shared origins (§6.2).
9. **Costs are absent twice over.** Spread is never charged (standing disclosure), and on the native
   layer `partial_cost_bps` is 100% NULL, so fees and funding are also not attached to any native
   figure. No cost-bearing native number exists in this run.

## 9. Anomalies

| # | Anomaly | Evidence |
|---|---|---|
| A1 | 430 cTrader / 1,517 crypto `EXIT_DENIED` rows are absorbing: after a denial the position never closes and the arm is blocked permanently. | `FIXED_TARGET_M1.00` E-TOUCH: FILLED 3, EXIT_DENIED 3 (TARGET), CLOSED 0, BLOCKED_ACTIVE 44,612 |
| A2 | 9 cTrader / 110 crypto both-traded `BAND_H` rows carry a non-zero delta despite an identical entry timestamp and an identical 4-bar exit rule. | §5.5; 0.010% and 0.026% of rows |
| A3 | `CENSORED` rows exist in the native lattice and in `native_parameter_origins.parquet` (8 rows) but appear in **no** device table. | device state census, §6 |
| A4 | `MANAGEMENT_COMPONENT_COMBINATION` recorded **zero** `EXIT_DENIED` in both universes yet has the lowest fill totals of any class (132 cTrader / 1,100 crypto fills against ~2M / ~10M blocked). Its blocking has a different cause from A1 and I could not determine it. | §4B census |
| A5 | `run_summary.json` `n_episodes` is the schedule row count, not an episode count; it overstates traded episodes by ~7,300× in cTrader (5,811,000 vs 797,063 fills). | §3 item 5 |
| A6 | crypto native `band_event_rate` computed against feature-ready rows exceeds 1.0 for some arms, i.e. some rows carry a non-null `event_type` while being counted `NO_FEATURE`. Reported here against the eligible-origin denominator to avoid the artefact; the underlying overlap is unexplained. | `arm_rates.csv` |
| A7 | 2,022 cTrader / 16,482 crypto `INCOMPLETE` rows appear identically in **both** variants (same 66 / 550 origins, 63 arms), unlike every other state. | §3 item 1 table |

## 10. Open questions for the operator

1. **Which estimand does the operator want?** The emitted `L1` (occupancy-inclusive, blocked scored
   0) and my `L3` (like-for-like both-traded) answer different questions and can differ in sign. I
   have supplied both for all 3,520 strata; the choice is a design question, not an analysis one.
2. **Is the absorbing `EXIT_DENIED` behaviour (A1) intended?** If not, the target / stop / trail /
   size device families were not measured in cTrader and a re-run would be required to measure them.
3. **Should `episode_n` / `effective_n` / `mde` in the device tables be re-derived on the device
   episode population?** As emitted they describe eligible origins and overstate device power by
   ~4 orders of magnitude on the median stratum.
4. **Should the derangement and magnitude-match controls be exercised against the estimates?** They
   exist and are attested but no stratum currently carries a control-conditioned read.
5. **Should the pairing be re-formed on fixed *traded* rather than fixed *scheduled*?** That would
   remove the asymmetry in §8.2 at the cost of reducing the paired population to 4.7% / 3.7%.
6. **Does the operator want a distinct plain baseline?** It is currently identical to `FIXED_HOLD_B4`.
7. **A2, A4, A6 and A7 are unexplained** and I could not resolve them from the emissions alone.

## 11. What this document does not do

No verdict, no recommended verdict, no disposition — by design. No E-TOUCH-vs-E-CLOSE preference is
expressed or implied. No universal-effect, tradability, deployability, winner or best claim is made.
No comparison is drawn to SPDR-021 or SPDR-022. No family status is changed, no TEST or holdout data
was read, no XENA artifact was touched, and nothing was committed, staged or pushed. `design.md`,
`screen.md` and the canonical `analyse.py` were not modified.
