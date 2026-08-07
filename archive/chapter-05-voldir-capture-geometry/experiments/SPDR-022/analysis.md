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

| entry_variant | arm_class | estimate_source | state | rows | eligible_origin_n | entry_fill_n | close_n | common_fill_n | common_close_n | eff_origin | eff_trade |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E_CLOSE | FIXED_NATIVE | COMMON_ORIGIN_OCCUPANCY_INCLUSIVE | ALL | 3 | 44700.0000 | 7537 | 7537 | 0.0000 | 0.0000 | 2229.0000 | 0.0000 |
| E_CLOSE | FIXED_NATIVE | COMMON_ORIGIN_OCCUPANCY_INCLUSIVE | ORDER_CREATED | 3 | 44700.0000 | 7537 | 7537 | 0.0000 | 0.0000 | 2229.0000 | 0.0000 |
| E_CLOSE | MANAGEMENT | COMMON_CLOSE_TRADE | ORDER_CREATED | 101 | 0.0000 | 68452 | 68452 | 68486.0000 | 68452.0000 | 0.0000 | 20573.0000 |
| E_CLOSE | MANAGEMENT_COMPONENT_COMBINATION | COMMON_CLOSE_TRADE | ORDER_CREATED | 42 | 0.0000 | 47351 | 47351 | 47360.0000 | 47351.0000 | 0.0000 | 15305.0000 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | COMMON_CLOSE_TRADE | ORDER_CREATED | 9 | 0.0000 | 1526 | 1526 | 1533.0000 | 1526.0000 | 0.0000 | 339.0000 |
| E_CLOSE | NATIVE | COMMON_ORIGIN_OCCUPANCY_INCLUSIVE | ALL | 96 | 1430400.0000 | 214615 | 214608 | 0.0000 | 0.0000 | 71328.0000 | 0.0000 |
| E_CLOSE | NATIVE | COMMON_ORIGIN_OCCUPANCY_INCLUSIVE | ORDER_CREATED | 96 | 1430400.0000 | 214615 | 214608 | 0.0000 | 0.0000 | 71328.0000 | 0.0000 |
| E_CLOSE | NATIVE_COMBINATION | COMMON_ORIGIN_OCCUPANCY_INCLUSIVE | ALL | 96 | 1430400.0000 | 213797 | 213784 | 0.0000 | 0.0000 | 71328.0000 | 0.0000 |
| E_CLOSE | NATIVE_COMBINATION | COMMON_ORIGIN_OCCUPANCY_INCLUSIVE | ORDER_CREATED | 96 | 1430400.0000 | 213797 | 213784 | 0.0000 | 0.0000 | 71328.0000 | 0.0000 |
| E_TOUCH | FIXED_NATIVE | COMMON_ORIGIN_OCCUPANCY_INCLUSIVE | ALL | 3 | 44700.0000 | 8496 | 8496 | 0.0000 | 0.0000 | 2229.0000 | 0.0000 |
| E_TOUCH | FIXED_NATIVE | COMMON_ORIGIN_OCCUPANCY_INCLUSIVE | ORDER_CREATED | 3 | 44700.0000 | 8496 | 8496 | 0.0000 | 0.0000 | 2229.0000 | 0.0000 |
| E_TOUCH | MANAGEMENT | COMMON_CLOSE_TRADE | ORDER_CREATED | 94 | 0.0000 | 72281 | 72281 | 72300.0000 | 72281.0000 | 0.0000 | 19338.0000 |
| E_TOUCH | MANAGEMENT_COMPONENT_COMBINATION | COMMON_CLOSE_TRADE | ORDER_CREATED | 41 | 0.0000 | 49592 | 49592 | 49595.0000 | 49592.0000 | 0.0000 | 14223.0000 |
| E_TOUCH | MANAGEMENT_DEVICE_COMBINATION | COMMON_CLOSE_TRADE | ORDER_CREATED | 6 | 0.0000 | 1667 | 1667 | 1671.0000 | 1667.0000 | 0.0000 | 300.0000 |
| E_TOUCH | NATIVE | COMMON_ORIGIN_OCCUPANCY_INCLUSIVE | ALL | 96 | 1430400.0000 | 242065 | 242058 | 0.0000 | 0.0000 | 71328.0000 | 0.0000 |
| E_TOUCH | NATIVE | COMMON_ORIGIN_OCCUPANCY_INCLUSIVE | ORDER_CREATED | 96 | 1430400.0000 | 242065 | 242058 | 0.0000 | 0.0000 | 71328.0000 | 0.0000 |
| E_TOUCH | NATIVE_COMBINATION | COMMON_ORIGIN_OCCUPANCY_INCLUSIVE | ALL | 96 | 1430400.0000 | 241379 | 241364 | 0.0000 | 0.0000 | 71328.0000 | 0.0000 |
| E_TOUCH | NATIVE_COMBINATION | COMMON_ORIGIN_OCCUPANCY_INCLUSIVE | ORDER_CREATED | 96 | 1430400.0000 | 241379 | 241364 | 0.0000 | 0.0000 | 71328.0000 | 0.0000 |

### 4.2 crypto populations

| entry_variant | arm_class | estimate_source | state | rows | eligible_origin_n | entry_fill_n | close_n | common_fill_n | common_close_n | eff_origin | eff_trade |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E_CLOSE | FIXED_NATIVE | COMMON_ORIGIN_OCCUPANCY_INCLUSIVE | ALL | 25 | 231121.0000 | 38212 | 38211 | 0.0000 | 0.0000 | 9637.0000 | 0.0000 |
| E_CLOSE | FIXED_NATIVE | COMMON_ORIGIN_OCCUPANCY_INCLUSIVE | ORDER_CREATED | 25 | 231121.0000 | 38212 | 38211 | 0.0000 | 0.0000 | 9637.0000 | 0.0000 |
| E_CLOSE | MANAGEMENT | COMMON_CLOSE_TRADE | ORDER_CREATED | 925 | 0.0000 | 361972 | 361972 | 362327.0000 | 361972.0000 | 0.0000 | 103709.0000 |
| E_CLOSE | MANAGEMENT_COMPONENT_COMBINATION | COMMON_CLOSE_TRADE | ORDER_CREATED | 398 | 0.0000 | 237996 | 237996 | 238096.0000 | 237996.0000 | 0.0000 | 73847.0000 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | COMMON_CLOSE_TRADE | ORDER_CREATED | 75 | 0.0000 | 9651 | 9651 | 9719.0000 | 9651.0000 | 0.0000 | 2269.0000 |
| E_CLOSE | NATIVE | COMMON_ORIGIN_OCCUPANCY_INCLUSIVE | ALL | 800 | 7395872.0000 | 1075450 | 1075289 | 0.0000 | 0.0000 | 308384.0000 | 0.0000 |
| E_CLOSE | NATIVE | COMMON_ORIGIN_OCCUPANCY_INCLUSIVE | ORDER_CREATED | 784 | 7380232.0000 | 1075450 | 1075289 | 0.0000 | 0.0000 | 307720.0000 | 0.0000 |
| E_CLOSE | NATIVE_COMBINATION | COMMON_ORIGIN_OCCUPANCY_INCLUSIVE | ALL | 800 | 7395872.0000 | 1070132 | 1069824 | 0.0000 | 0.0000 | 308384.0000 | 0.0000 |
| E_CLOSE | NATIVE_COMBINATION | COMMON_ORIGIN_OCCUPANCY_INCLUSIVE | ORDER_CREATED | 784 | 7380232.0000 | 1070132 | 1069824 | 0.0000 | 0.0000 | 307720.0000 | 0.0000 |
| E_TOUCH | FIXED_NATIVE | COMMON_ORIGIN_OCCUPANCY_INCLUSIVE | ALL | 25 | 231121.0000 | 43077 | 43077 | 0.0000 | 0.0000 | 9637.0000 | 0.0000 |
| E_TOUCH | FIXED_NATIVE | COMMON_ORIGIN_OCCUPANCY_INCLUSIVE | ORDER_CREATED | 25 | 231121.0000 | 43077 | 43077 | 0.0000 | 0.0000 | 9637.0000 | 0.0000 |
| E_TOUCH | MANAGEMENT | COMMON_CLOSE_TRADE | ORDER_CREATED | 927 | 0.0000 | 382031 | 382031 | 382305.0000 | 382031.0000 | 0.0000 | 98075.0000 |
| E_TOUCH | MANAGEMENT_COMPONENT_COMBINATION | COMMON_CLOSE_TRADE | ORDER_CREATED | 385 | 0.0000 | 243374 | 243374 | 243433.0000 | 243374.0000 | 0.0000 | 67210.0000 |
| E_TOUCH | MANAGEMENT_DEVICE_COMBINATION | COMMON_CLOSE_TRADE | ORDER_CREATED | 75 | 0.0000 | 12036 | 12036 | 12097.0000 | 12036.0000 | 0.0000 | 2371.0000 |
| E_TOUCH | NATIVE | COMMON_ORIGIN_OCCUPANCY_INCLUSIVE | ALL | 800 | 7395872.0000 | 1213057 | 1212965 | 0.0000 | 0.0000 | 308384.0000 | 0.0000 |
| E_TOUCH | NATIVE | COMMON_ORIGIN_OCCUPANCY_INCLUSIVE | ORDER_CREATED | 784 | 7380232.0000 | 1213057 | 1212965 | 0.0000 | 0.0000 | 307720.0000 | 0.0000 |
| E_TOUCH | NATIVE_COMBINATION | COMMON_ORIGIN_OCCUPANCY_INCLUSIVE | ALL | 800 | 7395872.0000 | 1208974 | 1208804 | 0.0000 | 0.0000 | 308384.0000 | 0.0000 |
| E_TOUCH | NATIVE_COMBINATION | COMMON_ORIGIN_OCCUPANCY_INCLUSIVE | ORDER_CREATED | 784 | 7380232.0000 | 1208974 | 1208804 | 0.0000 | 0.0000 | 307720.0000 | 0.0000 |

### 4.3 Selected / excluded origin populations

Every eligible origin is retained and classified. `SELECTED` origins carry an outcome;
`EXCLUDED` origins are `NO_EVENT` or `NO_FEATURE` and carry outcome 0.0 by construction (they
are the zero-exposure origins Lens A includes).

ctrader (`native_parameter_selected_excluded.parquet`, 5,811,000 rows):

| entry_variant | selection | state | rows | mean_bps | median_bps |
|---|---|---|---|---|---|
| E_CLOSE | EXCLUDED | NO_EVENT | 212286 | 0.0000 | 0.0000 |
| E_CLOSE | EXCLUDED | NO_FEATURE | 308819 | 0.0000 | 0.0000 |
| E_CLOSE | SELECTED | CENSORED | 8 | 0.0000 | 0.0000 |
| E_CLOSE | SELECTED | INCOMPLETE | 2022 | 0.0000 | 0.0000 |
| E_CLOSE | SELECTED | ORDER_CREATED | 2382365 | -0.0725 | 0.0000 |
| E_TOUCH | EXCLUDED | NO_EVENT | 75121 | 0.0000 | 0.0000 |
| E_TOUCH | EXCLUDED | NO_FEATURE | 308819 | 0.0000 | 0.0000 |
| E_TOUCH | SELECTED | EVENT_UNDECIDED | 1539 | 0.0000 | 0.0000 |
| E_TOUCH | SELECTED | INCOMPLETE | 2022 | 0.0000 | 0.0000 |
| E_TOUCH | SELECTED | ORDER_CREATED | 2517999 | 0.0231 | 0.0000 |

crypto (30,045,730 rows):

| entry_variant | selection | state | rows | mean_bps | median_bps |
|---|---|---|---|---|---|
| E_CLOSE | EXCLUDED | NO_EVENT | 1100525 | 0.0000 | 0.0000 |
| E_CLOSE | EXCLUDED | NO_FEATURE | 1730953 | 0.0000 | 0.0000 |
| E_CLOSE | SELECTED | CENSORED | 27 | 0.0000 | 0.0000 |
| E_CLOSE | SELECTED | INCOMPLETE | 16482 | 0.0000 | 0.0000 |
| E_CLOSE | SELECTED | ORDER_CREATED | 12174878 | -0.5912 | 0.0000 |
| E_TOUCH | EXCLUDED | NO_EVENT | 236561 | 0.0000 | 0.0000 |
| E_TOUCH | EXCLUDED | NO_FEATURE | 1730953 | 0.0000 | 0.0000 |
| E_TOUCH | SELECTED | EVENT_UNDECIDED | 73689 | 0.0000 | 0.0000 |
| E_TOUCH | SELECTED | INCOMPLETE | 16482 | 0.0000 | 0.0000 |
| E_TOUCH | SELECTED | ORDER_CREATED | 12965180 | -0.3837 | 0.0000 |

Censored and incomplete populations are small and carry mean outcome 0.0: ctrader `CENSORED`
8 rows, `INCOMPLETE` 2,022 rows; crypto `CENSORED` 27 rows, `INCOMPLETE` 16,482 rows. They are
retained in the tables above rather than dropped. `EVENT_UNDECIDED` exists only for `E_TOUCH`
(ctrader 1,539 rows, crypto 73,689) — the touch variant can register a band touch whose side is
not yet decided, which the close variant cannot.

### 4.4 State sections

ctrader (`state_sections.parquet`, 3,861 rows):

| entry_variant | state | rows | row_n | mean_outcome_bps |
|---|---|---|---|---|
| E_CLOSE | CENSORED | 8 | 8 | 0.0000 |
| E_CLOSE | INCOMPLETE | 405 | 4242 | 0.0000 |
| E_CLOSE | NO_EVENT | 435 | 253686 | 0.0000 |
| E_CLOSE | NO_FEATURE | 435 | 501203 | 0.0000 |
| E_CLOSE | ORDER_CREATED | 435 | 5722361 | -0.0466 |
| E_TOUCH | EVENT_UNDECIDED | 435 | 3181 | 0.0000 |
| E_TOUCH | INCOMPLETE | 405 | 4242 | 0.0000 |
| E_TOUCH | NO_EVENT | 433 | 77421 | 0.0000 |
| E_TOUCH | NO_FEATURE | 435 | 501203 | 0.0000 |
| E_TOUCH | ORDER_CREATED | 435 | 5895453 | 0.0108 |

crypto (30,978 rows):

| entry_variant | state | rows | row_n | mean_outcome_bps |
|---|---|---|---|---|
| E_CLOSE | CENSORED | 27 | 27 | 0.0000 |
| E_CLOSE | INCOMPLETE | 3352 | 34982 | 0.0000 |
| E_CLOSE | NO_EVENT | 3577 | 1390110 | 0.0000 |
| E_CLOSE | NO_FEATURE | 3625 | 2795441 | 0.0000 |
| E_CLOSE | ORDER_CREATED | 3593 | 29291985 | -0.2597 |
| E_TOUCH | EVENT_UNDECIDED | 3221 | 146299 | 0.0000 |
| E_TOUCH | INCOMPLETE | 3352 | 34982 | 0.0000 |
| E_TOUCH | NO_EVENT | 3013 | 259861 | 0.0000 |
| E_TOUCH | NO_FEATURE | 3625 | 2795441 | 0.0000 |
| E_TOUCH | ORDER_CREATED | 3593 | 30275962 | -0.1217 |

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

| symbol | entry_variant | eligible_origin_n | entry_fill_n | close_n | event_rate | fill_rate | exposure_per_origin | gross_mean_bps | gross_median_bps | gross_trimmed_mean_bps | win_share | win_loss_ratio | breakeven_win_share_net | mfe_bps | mae_bps | effective_origin_blocks | exit_reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD | E_CLOSE | 15422.0000 | 2559 | 2559 | 0.9867 | 0.1659 | 0.0071 | 0.0429 | -0.1877 | -0.0854 | 0.4924 | 1.0324 | 0.4920 | 14.3842 | 14.6798 | 771.0000 | HOLD=1.000000 |
| EURUSD | E_TOUCH | 15422.0000 | 2853 | 2853 | 0.9977 | 0.1850 | -0.0760 | -0.4111 | -0.1896 | -0.3767 | 0.4932 | 0.9672 | 0.5083 | 14.5385 | 14.9452 | 771.0000 | HOLD=1.000000 |
| USTEC | E_CLOSE | 14630.0000 | 2492 | 2492 | 0.9851 | 0.1703 | -0.0531 | -0.3118 | -0.4086 | 0.1354 | 0.4908 | 1.0170 | 0.4958 | 40.1888 | 40.8121 | 729.0000 | HOLD=1.000000 |
| USTEC | E_TOUCH | 14630.0000 | 2834 | 2834 | 0.9979 | 0.1937 | -0.1987 | -1.0257 | 0.0327 | -0.0382 | 0.5000 | 0.9467 | 0.5137 | 39.8111 | 40.3815 | 729.0000 | HOLD=1.000000 |
| XAUUSD | E_CLOSE | 14648.0000 | 2486 | 2486 | 0.9897 | 0.1697 | -0.1185 | -0.6982 | -1.1279 | -1.3183 | 0.4730 | 1.0468 | 0.4886 | 24.4424 | 24.6672 | 729.0000 | HOLD=1.000000 |
| XAUUSD | E_TOUCH | 14648.0000 | 2809 | 2809 | 0.9987 | 0.1918 | 0.1004 | 0.5236 | 0.2248 | 0.4189 | 0.5034 | 1.0282 | 0.4930 | 24.4769 | 24.0234 | 729.0000 | HOLD=1.000000 |

### 5.2 crypto fixed native comparator

| symbol | entry_variant | eligible_origin_n | entry_fill_n | close_n | event_rate | fill_rate | exposure_per_origin | gross_mean_bps | gross_median_bps | gross_trimmed_mean_bps | win_share | win_loss_ratio | breakeven_win_share_net | mfe_bps | mae_bps | effective_origin_blocks | exit_reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1000BONKUSDT | E_CLOSE | 8294.0000 | 1427 | 1427 | 0.9876 | 0.1721 | 0.9099 | 5.2886 | 0.0000 | 0.7195 | 0.4632 | 1.0465 | 0.4886 | 310.6607 | 297.7364 | 346.0000 | HOLD=1.000000 |
| 1000BONKUSDT | E_TOUCH | 8294.0000 | 1599 | 1599 | 0.9731 | 0.1928 | 2.1795 | 11.3050 | 0.0000 | -7.3979 | 0.4515 | 1.1572 | 0.4636 | 314.1877 | 292.0503 | 346.0000 | HOLD=1.000000 |
| 1000LUNCUSDT | E_CLOSE | 11150.0000 | 1866 | 1866 | 0.9778 | 0.1674 | 0.2291 | 1.3688 | -9.5585 | -8.0902 | 0.4512 | 1.1658 | 0.4617 | 163.6125 | 156.4689 | 465.0000 | HOLD=1.000000 |
| 1000LUNCUSDT | E_TOUCH | 11150.0000 | 2125 | 2125 | 0.9885 | 0.1906 | -1.1629 | -6.1016 | -9.4787 | -7.5862 | 0.4527 | 1.0370 | 0.4909 | 156.7900 | 165.1839 | 465.0000 | HOLD=1.000000 |
| 1000PEPEUSDT | E_CLOSE | 5484.0000 | 914 | 914 | 0.9874 | 0.1667 | -2.3179 | -13.9072 | -15.0320 | -14.2034 | 0.4365 | 1.0509 | 0.4876 | 248.0227 | 235.1813 | 229.0000 | HOLD=1.000000 |
| 1000PEPEUSDT | E_TOUCH | 5484.0000 | 1035 | 1035 | 0.9902 | 0.1887 | -3.4776 | -18.4260 | -25.1256 | -20.4941 | 0.4271 | 1.0583 | 0.4858 | 232.4443 | 242.8148 | 229.0000 | HOLD=1.000000 |
| 1000RATSUSDT | E_CLOSE | 614.0000 | 104 | 104 | 0.9788 | 0.1694 | 17.4523 | 103.0359 | 5.2932 | 18.8444 | 0.5096 | 1.3999 | 0.4167 | 682.8144 | 550.7504 | 26.0000 | HOLD=1.000000 |
| 1000RATSUSDT | E_TOUCH | 614.0000 | 115 | 115 | 0.9821 | 0.1873 | -21.3360 | -113.9158 | -64.0569 | -80.0286 | 0.4348 | 0.8777 | 0.5326 | 579.0448 | 705.5673 | 26.0000 | HOLD=1.000000 |
| ADAUSDT | E_CLOSE | 12527.0000 | 2077 | 2077 | 0.9867 | 0.1658 | -1.0612 | -6.4005 | -8.9392 | -9.0751 | 0.4506 | 1.0430 | 0.4895 | 107.4720 | 109.4377 | 522.0000 | HOLD=1.000000 |
| ADAUSDT | E_TOUCH | 12527.0000 | 2335 | 2335 | 0.9954 | 0.1864 | -1.4225 | -7.6314 | -8.1867 | -8.9455 | 0.4548 | 0.9961 | 0.5010 | 106.6214 | 109.8147 | 522.0000 | HOLD=1.000000 |
| AVAXUSDT | E_CLOSE | 12503.0000 | 2105 | 2105 | 0.9865 | 0.1684 | 0.5474 | 3.2516 | -5.4392 | -3.0914 | 0.4708 | 1.1657 | 0.4617 | 130.9921 | 124.1197 | 521.0000 | HOLD=1.000000 |
| AVAXUSDT | E_TOUCH | 12503.0000 | 2349 | 2349 | 0.9931 | 0.1879 | -0.6488 | -3.4535 | -2.9895 | -1.2424 | 0.4806 | 0.9938 | 0.5016 | 128.8090 | 126.1928 | 521.0000 | HOLD=1.000000 |
| BIGTIMEUSDT | E_CLOSE | 1594.0000 | 262 | 262 | 0.9843 | 0.1644 | 0.2303 | 1.4011 | 0.0000 | 3.4353 | 0.4924 | 1.0071 | 0.4982 | 433.7568 | 420.8456 | 67.0000 | HOLD=1.000000 |
| BIGTIMEUSDT | E_TOUCH | 1594.0000 | 295 | 295 | 0.9912 | 0.1851 | 1.0513 | 5.6805 | -9.2851 | -17.0410 | 0.4847 | 1.0820 | 0.4803 | 411.8326 | 420.5708 | 67.0000 | HOLD=1.000000 |
| BLURUSDT | E_CLOSE | 7336.0000 | 1223 | 1223 | 0.9845 | 0.1667 | -1.2280 | -7.3660 | -10.1215 | -14.3978 | 0.4595 | 1.0708 | 0.4829 | 214.4718 | 203.2739 | 306.0000 | HOLD=1.000000 |
| BLURUSDT | E_TOUCH | 7336.0000 | 1377 | 1377 | 0.9935 | 0.1877 | 0.5312 | 2.8302 | -8.9659 | -8.4357 | 0.4641 | 1.1647 | 0.4619 | 219.8958 | 204.4249 | 306.0000 | HOLD=1.000000 |
| BNBUSDT | E_CLOSE | 12503.0000 | 2083 | 2083 | 0.9890 | 0.1666 | -1.0811 | -6.4892 | -6.1977 | -6.7640 | 0.4450 | 0.9893 | 0.5027 | 79.2750 | 81.0773 | 521.0000 | HOLD=1.000000 |
| BNBUSDT | E_TOUCH | 12503.0000 | 2335 | 2335 | 0.9913 | 0.1868 | -0.3763 | -2.0152 | -4.0984 | -4.4209 | 0.4595 | 1.0534 | 0.4870 | 79.2738 | 79.0909 | 521.0000 | HOLD=1.000000 |
| BTCUSDT | E_CLOSE | 12503.0000 | 2041 | 2041 | 0.9695 | 0.1632 | 0.3470 | 2.1255 | -5.4183 | -5.3034 | 0.4483 | 1.3165 | 0.4317 | 73.9452 | 67.9171 | 521.0000 | HOLD=1.000000 |
| BTCUSDT | E_TOUCH | 12503.0000 | 2323 | 2323 | 0.9960 | 0.1858 | 0.0311 | 0.1675 | -3.7619 | -3.2167 | 0.4649 | 1.1528 | 0.4645 | 70.2517 | 69.4004 | 521.0000 | HOLD=1.000000 |
| DOGEUSDT | E_CLOSE | 12503.0000 | 2075 | 2075 | 0.9822 | 0.1660 | -0.9538 | -5.7471 | -6.1416 | -4.5783 | 0.4655 | 0.9988 | 0.5003 | 126.0388 | 124.8716 | 521.0000 | HOLD=1.000000 |
| DOGEUSDT | E_TOUCH | 12503.0000 | 2339 | 2339 | 0.9914 | 0.1871 | -0.3145 | -1.6813 | 0.0000 | -1.3732 | 0.4835 | 0.9937 | 0.5016 | 129.1016 | 123.1279 | 521.0000 | HOLD=1.000000 |
| DYDXUSDT | E_CLOSE | 12503.0000 | 2050 | 2050 | 0.9806 | 0.1640 | 0.3165 | 1.9305 | 0.0000 | -2.5470 | 0.4722 | 1.0541 | 0.4868 | 183.9529 | 173.6289 | 521.0000 | HOLD=1.000000 |
| DYDXUSDT | E_TOUCH | 12503.0000 | 2327 | 2327 | 0.9894 | 0.1861 | -0.1313 | -0.7057 | 0.0000 | -1.9520 | 0.4800 | 0.9903 | 0.5024 | 183.1115 | 174.6178 | 521.0000 | HOLD=1.000000 |
| ETHUSDT | E_CLOSE | 12503.0000 | 2022 | 2022 | 0.9772 | 0.1617 | -0.1743 | -1.0775 | -5.3049 | -5.5734 | 0.4540 | 1.1666 | 0.4616 | 90.0914 | 84.5947 | 521.0000 | HOLD=1.000000 |
| ETHUSDT | E_TOUCH | 12503.0000 | 2317 | 2317 | 0.9975 | 0.1853 | -0.6955 | -3.7533 | -4.3942 | -3.6725 | 0.4743 | 1.0059 | 0.4985 | 89.2852 | 88.9149 | 521.0000 | HOLD=1.000000 |
| GALAUSDT | E_CLOSE | 12503.0000 | 2071 | 2071 | 0.9876 | 0.1656 | -1.3135 | -7.9296 | -14.9813 | -13.3445 | 0.4500 | 1.0778 | 0.4813 | 159.7124 | 158.7866 | 521.0000 | HOLD=1.000000 |
| GALAUSDT | E_TOUCH | 12503.0000 | 2331 | 2331 | 0.9950 | 0.1864 | -0.4736 | -2.5403 | -10.0267 | -8.8540 | 0.4659 | 1.0873 | 0.4791 | 162.7109 | 158.5088 | 521.0000 | HOLD=1.000000 |
| INJUSDT | E_CLOSE | 11704.0000 | 1946 | 1946 | 0.9874 | 0.1663 | -0.3789 | -2.2790 | -6.3545 | -6.5316 | 0.4784 | 1.0371 | 0.4909 | 185.7565 | 178.3732 | 488.0000 | HOLD=1.000000 |
| INJUSDT | E_TOUCH | 11704.0000 | 2168 | 2168 | 0.9977 | 0.1852 | -1.3688 | -7.3893 | -6.6705 | -7.4496 | 0.4797 | 0.9768 | 0.5059 | 185.0671 | 187.0462 | 488.0000 | HOLD=1.000000 |
| LINKUSDT | E_CLOSE | 12503.0000 | 2085 | 2085 | 0.9872 | 0.1668 | -0.9005 | -5.4002 | -4.6882 | -2.7353 | 0.4787 | 0.9783 | 0.5055 | 126.6050 | 123.4958 | 521.0000 | HOLD=1.000000 |
| LINKUSDT | E_TOUCH | 12503.0000 | 2344 | 2344 | 0.9970 | 0.1875 | -0.6729 | -3.5892 | -6.4579 | -4.4395 | 0.4727 | 1.0373 | 0.4909 | 124.7067 | 125.1883 | 521.0000 | HOLD=1.000000 |
| MATICUSDT | E_CLOSE | 21641.0000 | 3506 | 3505 | 0.9781 | 0.1620 | -1.2830 | -7.9218 | -10.0351 | -8.3259 | 0.4645 | 1.0322 | 0.4921 | 156.3673 | 158.5387 | 902.0000 | HOLD=1.000000 |
| MATICUSDT | E_TOUCH | 21641.0000 | 3939 | 3939 | 0.9976 | 0.1820 | -0.2969 | -1.6312 | -6.6308 | -4.7519 | 0.4737 | 1.0803 | 0.4807 | 159.6796 | 155.9739 | 902.0000 | HOLD=1.000000 |
| OPUSDT | E_CLOSE | 12503.0000 | 2112 | 2112 | 0.9921 | 0.1689 | -0.4354 | -2.5777 | -4.6516 | -4.9368 | 0.4848 | 1.0199 | 0.4951 | 187.8969 | 180.3805 | 521.0000 | HOLD=1.000000 |
| OPUSDT | E_TOUCH | 12503.0000 | 2355 | 2355 | 0.9968 | 0.1884 | -0.6724 | -3.5697 | -7.8186 | -6.9240 | 0.4735 | 1.0519 | 0.4874 | 186.8259 | 182.5309 | 521.0000 | HOLD=1.000000 |
| ORDIUSDT | E_CLOSE | 5031.0000 | 827 | 827 | 0.9815 | 0.1644 | -1.3150 | -7.9995 | -18.7441 | -23.8463 | 0.4559 | 1.1002 | 0.4762 | 264.5033 | 252.4821 | 210.0000 | HOLD=1.000000 |
| ORDIUSDT | E_TOUCH | 5031.0000 | 940 | 940 | 0.9952 | 0.1868 | -0.3958 | -2.1183 | -13.6489 | -12.6959 | 0.4702 | 1.1037 | 0.4753 | 261.8676 | 248.7753 | 210.0000 | HOLD=1.000000 |
| PYTHUSDT | E_CLOSE | 640.0000 | 104 | 104 | 0.9750 | 0.1625 | -5.8164 | -35.7935 | -29.0328 | -28.0332 | 0.4423 | 0.9490 | 0.5131 | 314.9880 | 368.9872 | 27.0000 | HOLD=1.000000 |
| PYTHUSDT | E_TOUCH | 640.0000 | 119 | 119 | 0.9812 | 0.1859 | -1.4904 | -8.0155 | -12.5786 | -6.8881 | 0.4958 | 0.9646 | 0.5090 | 319.7234 | 374.8328 | 27.0000 | HOLD=1.000000 |
| SEIUSDT | E_CLOSE | 2971.0000 | 497 | 497 | 0.9852 | 0.1673 | 1.7787 | 10.6329 | 3.4412 | 3.7570 | 0.5070 | 1.1022 | 0.4757 | 204.3759 | 186.9923 | 124.0000 | HOLD=1.000000 |
| SEIUSDT | E_TOUCH | 2971.0000 | 556 | 556 | 0.9960 | 0.1871 | 0.3224 | 1.7226 | -2.8764 | -7.4227 | 0.4874 | 1.0693 | 0.4833 | 200.2196 | 189.3470 | 124.0000 | HOLD=1.000000 |
| SOLUSDT | E_CLOSE | 12527.0000 | 2072 | 2072 | 0.9869 | 0.1654 | 0.2797 | 1.6912 | -4.0684 | -3.2165 | 0.4788 | 1.0779 | 0.4813 | 162.7853 | 151.1506 | 522.0000 | HOLD=1.000000 |
| SOLUSDT | E_TOUCH | 12527.0000 | 2349 | 2349 | 0.9939 | 0.1875 | -0.3227 | -1.7210 | -3.8956 | -4.1644 | 0.4849 | 1.0144 | 0.4964 | 159.0693 | 155.4609 | 522.0000 | HOLD=1.000000 |
| TIAUSDT | E_CLOSE | 1062.0000 | 184 | 184 | 0.9878 | 0.1733 | -0.1466 | -0.8462 | -3.2912 | -8.7890 | 0.5000 | 0.9949 | 0.5013 | 371.9596 | 353.1636 | 46.0000 | HOLD=1.000000 |
| TIAUSDT | E_TOUCH | 1062.0000 | 200 | 200 | 0.9896 | 0.1883 | 1.2528 | 6.6525 | -25.5508 | -25.9067 | 0.4700 | 1.1729 | 0.4602 | 372.7891 | 361.0495 | 46.0000 | HOLD=1.000000 |
| WLDUSDT | E_CLOSE | 3516.0000 | 588 | 588 | 0.9883 | 0.1672 | -0.7134 | -4.2661 | 0.0000 | -0.9988 | 0.4813 | 0.9836 | 0.5041 | 211.8396 | 217.4853 | 147.0000 | HOLD=1.000000 |
| WLDUSDT | E_TOUCH | 3516.0000 | 651 | 651 | 0.9926 | 0.1852 | 1.3950 | 7.5345 | 11.8624 | 6.6583 | 0.5177 | 0.9955 | 0.5011 | 227.7232 | 205.3376 | 147.0000 | HOLD=1.000000 |
| XRPUSDT | E_CLOSE | 12503.0000 | 1971 | 1971 | 0.9606 | 0.1576 | -1.2126 | -7.6924 | -7.9349 | -9.5387 | 0.4475 | 1.0307 | 0.4924 | 110.4107 | 110.4029 | 521.0000 | HOLD=1.000000 |
| XRPUSDT | E_TOUCH | 12503.0000 | 2254 | 2254 | 0.9920 | 0.1803 | -0.5146 | -2.8546 | -6.3412 | -6.4374 | 0.4592 | 1.0873 | 0.4791 | 112.2489 | 108.4641 | 521.0000 | HOLD=1.000000 |

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

| entry_variant | device | setting | state | rows | sym | n_nonnull_est | cfill | cclose | efftr |
|---|---|---|---|---|---|---|---|---|---|
| E_CLOSE | HOLD | B12 | INCOMPLETE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | HOLD | B12 | NO_EVENT | 12 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | HOLD | B12 | NO_FEATURE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | HOLD | B12 | ORDER_CREATED | 12 | 3 | 10 | 13556 | 13552 | 7816 |
| E_CLOSE | HOLD | B2 | INCOMPLETE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | HOLD | B2 | NO_EVENT | 12 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | HOLD | B2 | NO_FEATURE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | HOLD | B2 | ORDER_CREATED | 12 | 3 | 9 | 44340 | 44340 | 8088 |
| E_CLOSE | HOLD | B4 | INCOMPLETE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | HOLD | B4 | NO_EVENT | 12 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | HOLD | B4 | NO_FEATURE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | HOLD | B4 | ORDER_CREATED | 12 | 3 | 9 | 30148 | 30148 | 7896 |
| E_CLOSE | SIZE | UNIT | INCOMPLETE | 12 | 3 | 3 | 0 | 0 | 0 |
| E_CLOSE | SIZE | UNIT | NO_EVENT | 12 | 3 | 3 | 0 | 0 | 0 |
| E_CLOSE | SIZE | UNIT | NO_FEATURE | 12 | 3 | 3 | 0 | 0 | 0 |
| E_CLOSE | SIZE | UNIT | ORDER_CREATED | 12 | 3 | 12 | 30148 | 30148 | 7896 |
| E_CLOSE | STOP | M0.75 | INCOMPLETE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | STOP | M0.75 | NO_EVENT | 12 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | STOP | M0.75 | NO_FEATURE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | STOP | M0.75 | ORDER_CREATED | 12 | 3 | 12 | 2972 | 2960 | 484 |
| E_CLOSE | STOP | M1.00 | INCOMPLETE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | STOP | M1.00 | NO_EVENT | 12 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | STOP | M1.00 | NO_FEATURE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | STOP | M1.00 | ORDER_CREATED | 12 | 3 | 8 | 2152 | 2140 | 444 |
| E_CLOSE | STOP | M1.50 | INCOMPLETE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | STOP | M1.50 | NO_EVENT | 12 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | STOP | M1.50 | NO_FEATURE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | STOP | M1.50 | ORDER_CREATED | 12 | 3 | 8 | 1708 | 1696 | 456 |
| E_CLOSE | TARGET | M0.75 | INCOMPLETE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | TARGET | M0.75 | NO_EVENT | 12 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | TARGET | M0.75 | NO_FEATURE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | TARGET | M0.75 | ORDER_CREATED | 12 | 3 | 12 | 3096 | 3084 | 496 |
| E_CLOSE | TARGET | M1.00 | INCOMPLETE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | TARGET | M1.00 | NO_EVENT | 12 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | TARGET | M1.00 | NO_FEATURE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | TARGET | M1.00 | ORDER_CREATED | 12 | 3 | 12 | 2340 | 2328 | 480 |
| E_CLOSE | TARGET | M1.50 | INCOMPLETE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | TARGET | M1.50 | NO_EVENT | 12 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | TARGET | M1.50 | NO_FEATURE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | TARGET | M1.50 | ORDER_CREATED | 12 | 3 | 12 | 1900 | 1888 | 528 |
| E_CLOSE | TRAIL | M0.75 | INCOMPLETE | 9 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | TRAIL | M0.75 | NO_EVENT | 9 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | TRAIL | M0.75 | NO_FEATURE | 9 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | TRAIL | M0.75 | ORDER_CREATED | 9 | 3 | 9 | 2235 | 2226 | 354 |
| E_CLOSE | TRAIL | M1.00 | INCOMPLETE | 9 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | TRAIL | M1.00 | NO_EVENT | 9 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | TRAIL | M1.00 | NO_FEATURE | 9 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | TRAIL | M1.00 | ORDER_CREATED | 9 | 3 | 9 | 1452 | 1443 | 297 |
| E_CLOSE | TRAIL | M1.50 | INCOMPLETE | 9 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | TRAIL | M1.50 | NO_EVENT | 9 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | TRAIL | M1.50 | NO_FEATURE | 9 | 3 | 0 | 0 | 0 | 0 |
| E_CLOSE | TRAIL | M1.50 | ORDER_CREATED | 9 | 3 | 9 | 1356 | 1350 | 354 |
| E_TOUCH | HOLD | B12 | EVENT_UNDECIDED | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | HOLD | B12 | INCOMPLETE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | HOLD | B12 | NO_EVENT | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | HOLD | B12 | NO_FEATURE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | HOLD | B12 | ORDER_CREATED | 12 | 3 | 11 | 13948 | 13944 | 7752 |
| E_TOUCH | HOLD | B2 | EVENT_UNDECIDED | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | HOLD | B2 | INCOMPLETE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | HOLD | B2 | NO_EVENT | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | HOLD | B2 | NO_FEATURE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | HOLD | B2 | ORDER_CREATED | 12 | 3 | 9 | 52680 | 52680 | 8008 |
| E_TOUCH | HOLD | B4 | EVENT_UNDECIDED | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | HOLD | B4 | INCOMPLETE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | HOLD | B4 | NO_EVENT | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | HOLD | B4 | NO_FEATURE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | HOLD | B4 | ORDER_CREATED | 12 | 3 | 9 | 33984 | 33984 | 7788 |
| E_TOUCH | SIZE | UNIT | EVENT_UNDECIDED | 12 | 3 | 3 | 0 | 0 | 0 |
| E_TOUCH | SIZE | UNIT | INCOMPLETE | 12 | 3 | 3 | 0 | 0 | 0 |
| E_TOUCH | SIZE | UNIT | NO_EVENT | 12 | 3 | 3 | 0 | 0 | 0 |
| E_TOUCH | SIZE | UNIT | NO_FEATURE | 12 | 3 | 3 | 0 | 0 | 0 |
| E_TOUCH | SIZE | UNIT | ORDER_CREATED | 12 | 3 | 12 | 33984 | 33984 | 7788 |
| E_TOUCH | STOP | M0.75 | EVENT_UNDECIDED | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | STOP | M0.75 | INCOMPLETE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | STOP | M0.75 | NO_EVENT | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | STOP | M0.75 | NO_FEATURE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | STOP | M0.75 | ORDER_CREATED | 12 | 3 | 12 | 3672 | 3660 | 512 |
| E_TOUCH | STOP | M1.00 | EVENT_UNDECIDED | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | STOP | M1.00 | INCOMPLETE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | STOP | M1.00 | NO_EVENT | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | STOP | M1.00 | NO_FEATURE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | STOP | M1.00 | ORDER_CREATED | 12 | 3 | 12 | 2144 | 2132 | 372 |
| E_TOUCH | STOP | M1.50 | EVENT_UNDECIDED | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | STOP | M1.50 | INCOMPLETE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | STOP | M1.50 | NO_EVENT | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | STOP | M1.50 | NO_FEATURE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | STOP | M1.50 | ORDER_CREATED | 12 | 3 | 12 | 1480 | 1468 | 316 |
| E_TOUCH | TARGET | M0.75 | EVENT_UNDECIDED | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | TARGET | M0.75 | INCOMPLETE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | TARGET | M0.75 | NO_EVENT | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | TARGET | M0.75 | NO_FEATURE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | TARGET | M0.75 | ORDER_CREATED | 12 | 3 | 8 | 2836 | 2824 | 364 |
| E_TOUCH | TARGET | M1.00 | EVENT_UNDECIDED | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | TARGET | M1.00 | INCOMPLETE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | TARGET | M1.00 | NO_EVENT | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | TARGET | M1.00 | NO_FEATURE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | TARGET | M1.00 | ORDER_CREATED | 12 | 3 | 8 | 2468 | 2456 | 412 |
| E_TOUCH | TARGET | M1.50 | EVENT_UNDECIDED | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | TARGET | M1.50 | INCOMPLETE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | TARGET | M1.50 | NO_EVENT | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | TARGET | M1.50 | NO_FEATURE | 12 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | TARGET | M1.50 | ORDER_CREATED | 12 | 3 | 8 | 1828 | 1816 | 428 |
| E_TOUCH | TRAIL | M0.75 | EVENT_UNDECIDED | 9 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | TRAIL | M0.75 | INCOMPLETE | 9 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | TRAIL | M0.75 | NO_EVENT | 9 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | TRAIL | M0.75 | NO_FEATURE | 9 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | TRAIL | M0.75 | ORDER_CREATED | 9 | 3 | 6 | 2670 | 2661 | 324 |
| E_TOUCH | TRAIL | M1.00 | EVENT_UNDECIDED | 9 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | TRAIL | M1.00 | INCOMPLETE | 9 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | TRAIL | M1.00 | NO_EVENT | 9 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | TRAIL | M1.00 | NO_FEATURE | 9 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | TRAIL | M1.00 | ORDER_CREATED | 9 | 3 | 6 | 2100 | 2091 | 294 |
| E_TOUCH | TRAIL | M1.50 | EVENT_UNDECIDED | 9 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | TRAIL | M1.50 | INCOMPLETE | 9 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | TRAIL | M1.50 | NO_EVENT | 9 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | TRAIL | M1.50 | NO_FEATURE | 9 | 3 | 0 | 0 | 0 | 0 |
| E_TOUCH | TRAIL | M1.50 | ORDER_CREATED | 9 | 3 | 6 | 1383 | 1374 | 306 |

crypto fixed-device population rows by state:

| entry_variant | device | setting | state | rows | sym | n_nonnull_est | cfill | cclose | efftr |
|---|---|---|---|---|---|---|---|---|---|
| E_CLOSE | HOLD | B12 | INCOMPLETE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | HOLD | B12 | NO_EVENT | 100 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | HOLD | B12 | NO_FEATURE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | HOLD | B12 | ORDER_CREATED | 100 | 25 | 81 | 65812 | 65780 | 38512 |
| E_CLOSE | HOLD | B2 | INCOMPLETE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | HOLD | B2 | NO_EVENT | 100 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | HOLD | B2 | NO_FEATURE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | HOLD | B2 | ORDER_CREATED | 100 | 25 | 76 | 228232 | 228232 | 38544 |
| E_CLOSE | HOLD | B4 | INCOMPLETE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | HOLD | B4 | NO_EVENT | 100 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | HOLD | B4 | NO_FEATURE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | HOLD | B4 | ORDER_CREATED | 100 | 25 | 78 | 152848 | 152844 | 38544 |
| E_CLOSE | SIZE | UNIT | INCOMPLETE | 100 | 25 | 25 | 0 | 0 | 0 |
| E_CLOSE | SIZE | UNIT | NO_EVENT | 100 | 25 | 25 | 0 | 0 | 0 |
| E_CLOSE | SIZE | UNIT | NO_FEATURE | 100 | 25 | 25 | 0 | 0 | 0 |
| E_CLOSE | SIZE | UNIT | ORDER_CREATED | 100 | 25 | 100 | 152848 | 152844 | 38544 |
| E_CLOSE | STOP | M0.75 | INCOMPLETE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | STOP | M0.75 | NO_EVENT | 100 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | STOP | M0.75 | NO_FEATURE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | STOP | M0.75 | ORDER_CREATED | 100 | 25 | 100 | 26700 | 26612 | 4828 |
| E_CLOSE | STOP | M1.00 | INCOMPLETE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | STOP | M1.00 | NO_EVENT | 100 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | STOP | M1.00 | NO_FEATURE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | STOP | M1.00 | ORDER_CREATED | 100 | 25 | 100 | 19812 | 19720 | 4116 |
| E_CLOSE | STOP | M1.50 | INCOMPLETE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | STOP | M1.50 | NO_EVENT | 100 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | STOP | M1.50 | NO_FEATURE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | STOP | M1.50 | ORDER_CREATED | 100 | 25 | 100 | 13872 | 13780 | 3520 |
| E_CLOSE | TARGET | M0.75 | INCOMPLETE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | TARGET | M0.75 | NO_EVENT | 100 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | TARGET | M0.75 | NO_FEATURE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | TARGET | M0.75 | ORDER_CREATED | 100 | 25 | 100 | 20720 | 20620 | 4016 |
| E_CLOSE | TARGET | M1.00 | INCOMPLETE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | TARGET | M1.00 | NO_EVENT | 100 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | TARGET | M1.00 | NO_FEATURE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | TARGET | M1.00 | ORDER_CREATED | 100 | 25 | 100 | 13584 | 13484 | 2948 |
| E_CLOSE | TARGET | M1.50 | INCOMPLETE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | TARGET | M1.50 | NO_EVENT | 100 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | TARGET | M1.50 | NO_FEATURE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | TARGET | M1.50 | ORDER_CREATED | 100 | 25 | 100 | 9704 | 9608 | 2516 |
| E_CLOSE | TRAIL | M0.75 | INCOMPLETE | 75 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | TRAIL | M0.75 | NO_EVENT | 75 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | TRAIL | M0.75 | NO_FEATURE | 75 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | TRAIL | M0.75 | ORDER_CREATED | 75 | 25 | 75 | 16170 | 16095 | 3066 |
| E_CLOSE | TRAIL | M1.00 | INCOMPLETE | 75 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | TRAIL | M1.00 | NO_EVENT | 75 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | TRAIL | M1.00 | NO_FEATURE | 75 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | TRAIL | M1.00 | ORDER_CREATED | 75 | 25 | 75 | 11082 | 11007 | 2499 |
| E_CLOSE | TRAIL | M1.50 | INCOMPLETE | 75 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | TRAIL | M1.50 | NO_EVENT | 75 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | TRAIL | M1.50 | NO_FEATURE | 75 | 25 | 0 | 0 | 0 | 0 |
| E_CLOSE | TRAIL | M1.50 | ORDER_CREATED | 75 | 25 | 75 | 7419 | 7347 | 2082 |
| E_TOUCH | HOLD | B12 | EVENT_UNDECIDED | 92 | 23 | 0 | 0 | 0 | 0 |
| E_TOUCH | HOLD | B12 | INCOMPLETE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_TOUCH | HOLD | B12 | NO_EVENT | 76 | 19 | 0 | 0 | 0 | 0 |
| E_TOUCH | HOLD | B12 | NO_FEATURE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_TOUCH | HOLD | B12 | ORDER_CREATED | 100 | 25 | 79 | 69120 | 69108 | 38540 |
| E_TOUCH | HOLD | B2 | EVENT_UNDECIDED | 92 | 23 | 0 | 0 | 0 | 0 |
| E_TOUCH | HOLD | B2 | INCOMPLETE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_TOUCH | HOLD | B2 | NO_EVENT | 76 | 19 | 0 | 0 | 0 | 0 |
| E_TOUCH | HOLD | B2 | NO_FEATURE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_TOUCH | HOLD | B2 | ORDER_CREATED | 100 | 25 | 75 | 275376 | 275376 | 38548 |
| E_TOUCH | HOLD | B4 | EVENT_UNDECIDED | 92 | 23 | 0 | 0 | 0 | 0 |
| E_TOUCH | HOLD | B4 | INCOMPLETE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_TOUCH | HOLD | B4 | NO_EVENT | 76 | 19 | 0 | 0 | 0 | 0 |
| E_TOUCH | HOLD | B4 | NO_FEATURE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_TOUCH | HOLD | B4 | ORDER_CREATED | 100 | 25 | 77 | 172308 | 172308 | 38548 |
| E_TOUCH | SIZE | UNIT | EVENT_UNDECIDED | 92 | 23 | 23 | 0 | 0 | 0 |
| E_TOUCH | SIZE | UNIT | INCOMPLETE | 100 | 25 | 25 | 0 | 0 | 0 |
| E_TOUCH | SIZE | UNIT | NO_EVENT | 76 | 19 | 19 | 0 | 0 | 0 |
| E_TOUCH | SIZE | UNIT | NO_FEATURE | 100 | 25 | 25 | 0 | 0 | 0 |
| E_TOUCH | SIZE | UNIT | ORDER_CREATED | 100 | 25 | 100 | 172308 | 172308 | 38548 |
| E_TOUCH | STOP | M0.75 | EVENT_UNDECIDED | 92 | 23 | 0 | 0 | 0 | 0 |
| E_TOUCH | STOP | M0.75 | INCOMPLETE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_TOUCH | STOP | M0.75 | NO_EVENT | 76 | 19 | 0 | 0 | 0 | 0 |
| E_TOUCH | STOP | M0.75 | NO_FEATURE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_TOUCH | STOP | M0.75 | ORDER_CREATED | 100 | 25 | 100 | 29852 | 29764 | 4280 |
| E_TOUCH | STOP | M1.00 | EVENT_UNDECIDED | 92 | 23 | 0 | 0 | 0 | 0 |
| E_TOUCH | STOP | M1.00 | INCOMPLETE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_TOUCH | STOP | M1.00 | NO_EVENT | 76 | 19 | 0 | 0 | 0 | 0 |
| E_TOUCH | STOP | M1.00 | NO_FEATURE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_TOUCH | STOP | M1.00 | ORDER_CREATED | 100 | 25 | 100 | 18940 | 18848 | 3380 |
| E_TOUCH | STOP | M1.50 | EVENT_UNDECIDED | 92 | 23 | 0 | 0 | 0 | 0 |
| E_TOUCH | STOP | M1.50 | INCOMPLETE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_TOUCH | STOP | M1.50 | NO_EVENT | 76 | 19 | 0 | 0 | 0 | 0 |
| E_TOUCH | STOP | M1.50 | NO_FEATURE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_TOUCH | STOP | M1.50 | ORDER_CREATED | 100 | 25 | 100 | 14116 | 14028 | 3428 |
| E_TOUCH | TARGET | M0.75 | EVENT_UNDECIDED | 92 | 23 | 0 | 0 | 0 | 0 |
| E_TOUCH | TARGET | M0.75 | INCOMPLETE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_TOUCH | TARGET | M0.75 | NO_EVENT | 76 | 19 | 0 | 0 | 0 | 0 |
| E_TOUCH | TARGET | M0.75 | NO_FEATURE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_TOUCH | TARGET | M0.75 | ORDER_CREATED | 100 | 25 | 100 | 25544 | 25444 | 3884 |
| E_TOUCH | TARGET | M1.00 | EVENT_UNDECIDED | 92 | 23 | 0 | 0 | 0 | 0 |
| E_TOUCH | TARGET | M1.00 | INCOMPLETE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_TOUCH | TARGET | M1.00 | NO_EVENT | 76 | 19 | 0 | 0 | 0 | 0 |
| E_TOUCH | TARGET | M1.00 | NO_FEATURE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_TOUCH | TARGET | M1.00 | ORDER_CREATED | 100 | 25 | 100 | 17680 | 17584 | 3128 |
| E_TOUCH | TARGET | M1.50 | EVENT_UNDECIDED | 92 | 23 | 0 | 0 | 0 | 0 |
| E_TOUCH | TARGET | M1.50 | INCOMPLETE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_TOUCH | TARGET | M1.50 | NO_EVENT | 76 | 19 | 0 | 0 | 0 | 0 |
| E_TOUCH | TARGET | M1.50 | NO_FEATURE | 100 | 25 | 0 | 0 | 0 | 0 |
| E_TOUCH | TARGET | M1.50 | ORDER_CREATED | 100 | 25 | 100 | 11080 | 10988 | 2640 |
| E_TOUCH | TRAIL | M0.75 | EVENT_UNDECIDED | 69 | 23 | 0 | 0 | 0 | 0 |
| E_TOUCH | TRAIL | M0.75 | INCOMPLETE | 75 | 25 | 0 | 0 | 0 | 0 |
| E_TOUCH | TRAIL | M0.75 | NO_EVENT | 57 | 19 | 0 | 0 | 0 | 0 |
| E_TOUCH | TRAIL | M0.75 | NO_FEATURE | 75 | 25 | 0 | 0 | 0 | 0 |
| E_TOUCH | TRAIL | M0.75 | ORDER_CREATED | 75 | 25 | 75 | 19089 | 19014 | 2976 |
| E_TOUCH | TRAIL | M1.00 | EVENT_UNDECIDED | 69 | 23 | 0 | 0 | 0 | 0 |
| E_TOUCH | TRAIL | M1.00 | INCOMPLETE | 75 | 25 | 0 | 0 | 0 | 0 |
| E_TOUCH | TRAIL | M1.00 | NO_EVENT | 57 | 19 | 0 | 0 | 0 | 0 |
| E_TOUCH | TRAIL | M1.00 | NO_FEATURE | 75 | 25 | 0 | 0 | 0 | 0 |
| E_TOUCH | TRAIL | M1.00 | ORDER_CREATED | 75 | 25 | 75 | 14457 | 14385 | 2613 |
| E_TOUCH | TRAIL | M1.50 | EVENT_UNDECIDED | 69 | 23 | 0 | 0 | 0 | 0 |
| E_TOUCH | TRAIL | M1.50 | INCOMPLETE | 75 | 25 | 0 | 0 | 0 | 0 |
| E_TOUCH | TRAIL | M1.50 | NO_EVENT | 57 | 19 | 0 | 0 | 0 | 0 |
| E_TOUCH | TRAIL | M1.50 | NO_FEATURE | 75 | 25 | 0 | 0 | 0 | 0 |
| E_TOUCH | TRAIL | M1.50 | ORDER_CREATED | 75 | 25 | 75 | 9735 | 9663 | 2394 |

### 5.4 Fixed-native-parameter comparator pointer

`controls.parquet` carries two pointer rows per universe rather than duplicate estimates:

| control | analysis_stage | population | comparator | undefined_reason |
|---|---|---|---|---|
| FIXED_DEVICE | COMPUTED | COMMON_CLOSE_TRADE | DECLARED_FIXED_DEVICE | REPORTED_IN_DEVICE_TABLES |
| FIXED_NATIVE_PARAMETER | COMPUTED | ELIGIBLE_ORIGIN | DECLARED_FIXED_NATIVE | REPORTED_IN_NATIVE_PARAMETER_ORIGINS |

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

| entry_variant | arm_class | component | parameter | orientation | sym | est_min | est_med | est_max | ci_ex0 | mde_med | elig | fills | closes | eff | ev_rate | fill_rate | occ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E_CLOSE | FIXED_NATIVE |  | BAND_Z+BAND_H | FIXED | 3 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 44700.0000 | 7537 | 7537 | 2229.0000 | 0.9867 | 0.1697 | -0.0531 |
| E_CLOSE | NATIVE | LEVEL_FORECAST_K12 | BAND_H | DIRECT | 3 | -0.0117 | 0.0552 | 0.1043 | 0 | 0.1762 | 44700.0000 | 4450 | 4450 | 2229.0000 | 0.5388 | 0.0999 | -0.0046 |
| E_CLOSE | NATIVE | LEVEL_FORECAST_K12 | BAND_H | REVERSE | 3 | -0.0407 | -0.0312 | 0.0904 | 0 | 0.1708 | 44700.0000 | 4453 | 4453 | 2229.0000 | 0.5220 | 0.0998 | -0.0241 |
| E_CLOSE | NATIVE | LEVEL_FORECAST_K12 | BAND_Z | DIRECT | 3 | -0.1192 | 0.0580 | 0.0736 | 0 | 0.2402 | 44700.0000 | 4551 | 4551 | 2229.0000 | 0.5872 | 0.1023 | -0.0605 |
| E_CLOSE | NATIVE | LEVEL_FORECAST_K12 | BAND_Z | REVERSE | 3 | -0.0100 | 0.0051 | 0.0386 | 0 | 0.2378 | 44700.0000 | 4486 | 4486 | 2229.0000 | 0.5809 | 0.1003 | -0.0145 |
| E_CLOSE | NATIVE | LEVEL_FORECAST_K4 | BAND_H | DIRECT | 3 | -0.0142 | 0.0230 | 0.1219 | 0 | 0.1714 | 44700.0000 | 4458 | 4457 | 2229.0000 | 0.5477 | 0.1001 | -0.0071 |
| E_CLOSE | NATIVE | LEVEL_FORECAST_K4 | BAND_H | REVERSE | 3 | -0.0197 | -0.0092 | 0.0709 | 0 | 0.1850 | 44700.0000 | 4447 | 4447 | 2229.0000 | 0.5173 | 0.0996 | -0.0126 |
| E_CLOSE | NATIVE | LEVEL_FORECAST_K4 | BAND_Z | DIRECT | 3 | -0.0696 | -0.0247 | 0.0405 | 0 | 0.2461 | 44700.0000 | 4570 | 4570 | 2229.0000 | 0.5873 | 0.1030 | -0.0625 |
| E_CLOSE | NATIVE | LEVEL_FORECAST_K4 | BAND_Z | REVERSE | 3 | -0.0526 | 0.0882 | 0.0987 | 0 | 0.2323 | 44700.0000 | 4441 | 4441 | 2229.0000 | 0.5803 | 0.1001 | -0.0303 |
| E_CLOSE | NATIVE | LEVEL_NOW | BAND_H | DIRECT | 3 | -0.0166 | 0.0035 | 0.0500 | 0 | 0.0916 | 44700.0000 | 7461 | 7460 | 2229.0000 | 0.9162 | 0.1681 | -0.0095 |
| E_CLOSE | NATIVE | LEVEL_NOW | BAND_H | REVERSE | 3 | -0.0297 | -0.0212 | 0.0382 | 0 | 0.1134 | 44700.0000 | 7441 | 7441 | 2229.0000 | 0.8725 | 0.1675 | -0.0149 |
| E_CLOSE | NATIVE | LEVEL_NOW | BAND_Z | DIRECT | 3 | -0.0380 | -0.0130 | 0.0655 | 0 | 0.2458 | 44700.0000 | 7629 | 7629 | 2229.0000 | 0.9805 | 0.1716 | -0.0059 |
| E_CLOSE | NATIVE | LEVEL_NOW | BAND_Z | REVERSE | 3 | -0.0548 | 0.0226 | 0.0566 | 0 | 0.2247 | 44700.0000 | 7436 | 7436 | 2229.0000 | 0.9691 | 0.1675 | -0.0477 |
| E_CLOSE | NATIVE | RANGE_SCALE | BAND_H | DIRECT | 3 | -0.0050 | -0.0010 | 0.0353 | 0 | 0.0693 | 44700.0000 | 7528 | 7527 | 2229.0000 | 0.9695 | 0.1692 | -0.0178 |
| E_CLOSE | NATIVE | RANGE_SCALE | BAND_H | REVERSE | 3 | -0.0389 | -0.0149 | 0.0467 | 0 | 0.1282 | 44700.0000 | 7430 | 7430 | 2229.0000 | 0.8141 | 0.1677 | -0.0317 |
| E_CLOSE | NATIVE | RANGE_SCALE | BAND_Z | DIRECT | 3 | -0.0916 | -0.0162 | 0.0047 | 0 | 0.2047 | 44700.0000 | 7847 | 7847 | 2229.0000 | 0.9943 | 0.1753 | -0.0845 |
| E_CLOSE | NATIVE | RANGE_SCALE | BAND_Z | REVERSE | 3 | -0.0514 | -0.0482 | 0.0643 | 0 | 0.1875 | 44700.0000 | 7211 | 7211 | 2229.0000 | 0.9627 | 0.1607 | -0.0443 |
| E_CLOSE | NATIVE | SHOCK | BAND_H | DIRECT | 3 | -0.0103 | -0.0020 | 0.0481 | 0 | 0.1205 | 44700.0000 | 7443 | 7442 | 2229.0000 | 0.8223 | 0.1676 | -0.0050 |
| E_CLOSE | NATIVE | SHOCK | BAND_H | REVERSE | 3 | -0.0434 | -0.0174 | 0.0352 | 0 | 0.0663 | 44700.0000 | 7505 | 7505 | 2229.0000 | 0.9677 | 0.1692 | -0.0362 |
| E_CLOSE | NATIVE | SHOCK | BAND_Z | DIRECT | 3 | -0.0607 | 0.0494 | 0.1691 | 0 | 0.2241 | 44700.0000 | 7237 | 7237 | 2229.0000 | 0.9681 | 0.1630 | -0.0536 |
| E_CLOSE | NATIVE | SHOCK | BAND_Z | REVERSE | 3 | -0.0688 | -0.0145 | 0.0252 | 0 | 0.2361 | 44700.0000 | 7949 | 7949 | 2229.0000 | 0.9871 | 0.1791 | -0.0617 |
| E_CLOSE | NATIVE | SWING_GT_CUR | BAND_H | DIRECT | 3 | -0.0305 | 0.0254 | 0.0521 | 0 | 0.1065 | 44700.0000 | 7282 | 7281 | 2229.0000 | 0.8822 | 0.1638 | -0.0234 |
| E_CLOSE | NATIVE | SWING_GT_CUR | BAND_H | REVERSE | 3 | -0.0148 | -0.0004 | 0.0331 | 0 | 0.1047 | 44700.0000 | 7298 | 7298 | 2229.0000 | 0.8759 | 0.1643 | -0.0535 |
| E_CLOSE | NATIVE | SWING_GT_CUR | BAND_Z | DIRECT | 3 | -0.1105 | -0.0110 | 0.0762 | 0 | 0.2268 | 44700.0000 | 7384 | 7384 | 2229.0000 | 0.9545 | 0.1667 | -0.0641 |
| E_CLOSE | NATIVE | SWING_GT_CUR | BAND_Z | REVERSE | 3 | 0.0085 | 0.0281 | 0.0446 | 0 | 0.2299 | 44700.0000 | 7343 | 7343 | 2229.0000 | 0.9553 | 0.1646 | -0.0085 |
| E_CLOSE | NATIVE | SWING_SCALE | BAND_H | DIRECT | 3 | 0.0054 | 0.0480 | 0.0500 | 0 | 0.0925 | 44700.0000 | 7319 | 7319 | 2229.0000 | 0.9456 | 0.1644 | -0.0051 |
| E_CLOSE | NATIVE | SWING_SCALE | BAND_H | REVERSE | 3 | -0.0457 | 0.0028 | 0.0116 | 0 | 0.1320 | 44700.0000 | 7260 | 7259 | 2229.0000 | 0.7978 | 0.1637 | -0.0503 |
| E_CLOSE | NATIVE | SWING_SCALE | BAND_Z | DIRECT | 3 | -0.0913 | 0.0787 | 0.1564 | 0 | 0.1672 | 44700.0000 | 7614 | 7614 | 2229.0000 | 0.9671 | 0.1694 | -0.0398 |
| E_CLOSE | NATIVE | SWING_SCALE | BAND_Z | REVERSE | 3 | -0.0622 | -0.0434 | 0.0508 | 0 | 0.1754 | 44700.0000 | 7050 | 7050 | 2229.0000 | 0.9409 | 0.1565 | -0.0677 |
| E_CLOSE | NATIVE | TAIL_RISK | BAND_H | DIRECT | 3 | -0.0004 | 0.0037 | 0.0576 | 0 | 0.0906 | 44700.0000 | 7519 | 7519 | 2229.0000 | 0.9710 | 0.1688 | 0.0045 |
| E_CLOSE | NATIVE | TAIL_RISK | BAND_H | REVERSE | 3 | -0.0505 | -0.0284 | 0.0310 | 0 | 0.1118 | 44700.0000 | 7441 | 7440 | 2229.0000 | 0.8140 | 0.1680 | -0.0433 |
| E_CLOSE | NATIVE | TAIL_RISK | BAND_Z | DIRECT | 3 | -0.0563 | -0.0366 | -0.0015 | 0 | 0.2457 | 44700.0000 | 7888 | 7888 | 2229.0000 | 0.9936 | 0.1759 | -0.0546 |
| E_CLOSE | NATIVE | TAIL_RISK | BAND_Z | REVERSE | 3 | -0.0753 | 0.0485 | 0.0665 | 0 | 0.2252 | 44700.0000 | 7244 | 7244 | 2229.0000 | 0.9610 | 0.1606 | -0.0520 |
| E_CLOSE | NATIVE_COMBINATION | LEVEL_FORECAST_K12 | BAND_Z+BAND_H | DIRECT_DIRECT | 3 | -0.1496 | -0.0761 | 0.0872 | 1 | 0.2296 | 44700.0000 | 4483 | 4483 | 2229.0000 | 0.5075 | 0.1007 | -0.1292 |
| E_CLOSE | NATIVE_COMBINATION | LEVEL_FORECAST_K12 | BAND_Z+BAND_H | DIRECT_REVERSE | 3 | -0.0969 | 0.0345 | 0.1083 | 0 | 0.2446 | 44700.0000 | 4520 | 4520 | 2229.0000 | 0.5621 | 0.1017 | -0.0840 |
| E_CLOSE | NATIVE_COMBINATION | LEVEL_FORECAST_K12 | BAND_Z+BAND_H | REVERSE_DIRECT | 3 | -0.0223 | -0.0002 | 0.0346 | 0 | 0.2391 | 44700.0000 | 4478 | 4478 | 2229.0000 | 0.5709 | 0.0999 | -0.0185 |
| E_CLOSE | NATIVE_COMBINATION | LEVEL_FORECAST_K12 | BAND_Z+BAND_H | REVERSE_REVERSE | 3 | -0.0622 | 0.0101 | 0.0359 | 0 | 0.2375 | 44700.0000 | 4416 | 4416 | 2229.0000 | 0.4792 | 0.0987 | -0.0172 |
| E_CLOSE | NATIVE_COMBINATION | LEVEL_FORECAST_K4 | BAND_Z+BAND_H | DIRECT_DIRECT | 3 | -0.1252 | -0.0500 | -0.0112 | 1 | 0.2433 | 44700.0000 | 4508 | 4508 | 2229.0000 | 0.5191 | 0.1016 | -0.1181 |
| E_CLOSE | NATIVE_COMBINATION | LEVEL_FORECAST_K4 | BAND_Z+BAND_H | DIRECT_REVERSE | 3 | -0.0630 | -0.0167 | 0.0303 | 0 | 0.2406 | 44700.0000 | 4559 | 4558 | 2229.0000 | 0.5591 | 0.1030 | -0.0559 |
| E_CLOSE | NATIVE_COMBINATION | LEVEL_FORECAST_K4 | BAND_Z+BAND_H | REVERSE_DIRECT | 3 | -0.0524 | 0.0810 | 0.0820 | 0 | 0.2327 | 44700.0000 | 4437 | 4437 | 2229.0000 | 0.5767 | 0.0999 | -0.0365 |
| E_CLOSE | NATIVE_COMBINATION | LEVEL_FORECAST_K4 | BAND_Z+BAND_H | REVERSE_REVERSE | 3 | -0.0191 | 0.0310 | 0.0803 | 0 | 0.2435 | 44700.0000 | 4356 | 4355 | 2229.0000 | 0.4750 | 0.0980 | -0.0221 |
| E_CLOSE | NATIVE_COMBINATION | LEVEL_NOW | BAND_Z+BAND_H | DIRECT_DIRECT | 3 | -0.0627 | -0.0434 | -0.0253 | 0 | 0.2422 | 44700.0000 | 7535 | 7535 | 2229.0000 | 0.8639 | 0.1697 | -0.0965 |
| E_CLOSE | NATIVE_COMBINATION | LEVEL_NOW | BAND_Z+BAND_H | DIRECT_REVERSE | 3 | -0.0728 | -0.0108 | 0.0668 | 0 | 0.2461 | 44700.0000 | 7606 | 7605 | 2229.0000 | 0.9407 | 0.1714 | -0.0037 |
| E_CLOSE | NATIVE_COMBINATION | LEVEL_NOW | BAND_Z+BAND_H | REVERSE_DIRECT | 3 | -0.0463 | -0.0264 | 0.0425 | 0 | 0.2267 | 44700.0000 | 7430 | 7430 | 2229.0000 | 0.9623 | 0.1673 | -0.0760 |
| E_CLOSE | NATIVE_COMBINATION | LEVEL_NOW | BAND_Z+BAND_H | REVERSE_REVERSE | 3 | -0.0660 | -0.0169 | 0.0622 | 0 | 0.2385 | 44700.0000 | 7300 | 7299 | 2229.0000 | 0.8095 | 0.1646 | -0.0563 |
| E_CLOSE | NATIVE_COMBINATION | RANGE_SCALE | BAND_Z+BAND_H | DIRECT_DIRECT | 3 | -0.0942 | -0.0414 | 0.0116 | 0 | 0.2052 | 44700.0000 | 7815 | 7814 | 2229.0000 | 0.9612 | 0.1749 | -0.0870 |
| E_CLOSE | NATIVE_COMBINATION | RANGE_SCALE | BAND_Z+BAND_H | DIRECT_REVERSE | 3 | -0.0766 | -0.0689 | 0.0120 | 0 | 0.2051 | 44700.0000 | 7794 | 7794 | 2229.0000 | 0.9021 | 0.1744 | -0.0695 |
| E_CLOSE | NATIVE_COMBINATION | RANGE_SCALE | BAND_Z+BAND_H | REVERSE_DIRECT | 3 | -0.0908 | -0.0645 | 0.0229 | 0 | 0.1891 | 44700.0000 | 7209 | 7208 | 2229.0000 | 0.9771 | 0.1610 | -0.0574 |
| E_CLOSE | NATIVE_COMBINATION | RANGE_SCALE | BAND_Z+BAND_H | REVERSE_REVERSE | 3 | -0.0628 | -0.0597 | -0.0381 | 0 | 0.1987 | 44700.0000 | 7028 | 7028 | 2229.0000 | 0.7283 | 0.1560 | -0.0912 |
| E_CLOSE | NATIVE_COMBINATION | SHOCK | BAND_Z+BAND_H | DIRECT_DIRECT | 3 | -0.0527 | -0.0007 | 0.0214 | 0 | 0.2218 | 44700.0000 | 7051 | 7050 | 2229.0000 | 0.7275 | 0.1587 | -0.0538 |
| E_CLOSE | NATIVE_COMBINATION | SHOCK | BAND_Z+BAND_H | DIRECT_REVERSE | 3 | -0.0732 | 0.0488 | 0.1509 | 0 | 0.2403 | 44700.0000 | 7182 | 7182 | 2229.0000 | 0.9846 | 0.1618 | -0.0661 |
| E_CLOSE | NATIVE_COMBINATION | SHOCK | BAND_Z+BAND_H | REVERSE_DIRECT | 3 | -0.0626 | -0.0429 | -0.0362 | 0 | 0.2307 | 44700.0000 | 7931 | 7930 | 2229.0000 | 0.9206 | 0.1787 | -0.0893 |
| E_CLOSE | NATIVE_COMBINATION | SHOCK | BAND_Z+BAND_H | REVERSE_REVERSE | 3 | -0.0688 | -0.0385 | -0.0166 | 0 | 0.2399 | 44700.0000 | 7934 | 7934 | 2229.0000 | 0.9488 | 0.1787 | -0.0697 |
| E_CLOSE | NATIVE_COMBINATION | SWING_GT_CUR | BAND_Z+BAND_H | DIRECT_DIRECT | 3 | -0.1103 | -0.0711 | 0.0414 | 0 | 0.2321 | 44700.0000 | 7247 | 7247 | 2229.0000 | 0.8295 | 0.1636 | -0.1032 |
| E_CLOSE | NATIVE_COMBINATION | SWING_GT_CUR | BAND_Z+BAND_H | DIRECT_REVERSE | 3 | -0.0993 | -0.0205 | 0.0226 | 0 | 0.2223 | 44700.0000 | 7369 | 7369 | 2229.0000 | 0.9309 | 0.1665 | -0.0922 |
| E_CLOSE | NATIVE_COMBINATION | SWING_GT_CUR | BAND_Z+BAND_H | REVERSE_DIRECT | 3 | -0.0339 | 0.0076 | 0.0309 | 0 | 0.2358 | 44700.0000 | 7329 | 7328 | 2229.0000 | 0.9336 | 0.1644 | -0.0870 |
| E_CLOSE | NATIVE_COMBINATION | SWING_GT_CUR | BAND_Z+BAND_H | REVERSE_REVERSE | 3 | -0.0424 | -0.0155 | 0.0226 | 0 | 0.2367 | 44700.0000 | 7221 | 7220 | 2229.0000 | 0.8116 | 0.1619 | -0.0955 |
| E_CLOSE | NATIVE_COMBINATION | SWING_SCALE | BAND_Z+BAND_H | DIRECT_DIRECT | 3 | -0.0775 | 0.0824 | 0.1808 | 0 | 0.1736 | 44700.0000 | 7582 | 7582 | 2229.0000 | 0.9397 | 0.1685 | -0.0361 |
| E_CLOSE | NATIVE_COMBINATION | SWING_SCALE | BAND_Z+BAND_H | DIRECT_REVERSE | 3 | -0.0751 | -0.0011 | 0.0923 | 0 | 0.1797 | 44700.0000 | 7578 | 7577 | 2229.0000 | 0.8773 | 0.1686 | -0.0680 |
| E_CLOSE | NATIVE_COMBINATION | SWING_SCALE | BAND_Z+BAND_H | REVERSE_DIRECT | 3 | -0.0887 | -0.0642 | 0.0701 | 0 | 0.1805 | 44700.0000 | 7036 | 7036 | 2229.0000 | 0.9504 | 0.1565 | -0.0571 |
| E_CLOSE | NATIVE_COMBINATION | SWING_SCALE | BAND_Z+BAND_H | REVERSE_REVERSE | 3 | -0.1264 | -0.0727 | 0.0029 | 0 | 0.2009 | 44700.0000 | 6876 | 6876 | 2229.0000 | 0.7110 | 0.1519 | -0.1156 |
| E_CLOSE | NATIVE_COMBINATION | TAIL_RISK | BAND_Z+BAND_H | DIRECT_DIRECT | 3 | -0.0487 | -0.0310 | 0.0036 | 0 | 0.2378 | 44700.0000 | 7838 | 7838 | 2229.0000 | 0.9555 | 0.1753 | -0.0495 |
| E_CLOSE | NATIVE_COMBINATION | TAIL_RISK | BAND_Z+BAND_H | DIRECT_REVERSE | 3 | -0.0668 | -0.0342 | -0.0170 | 0 | 0.2508 | 44700.0000 | 7862 | 7861 | 2229.0000 | 0.9174 | 0.1753 | -0.0701 |
| E_CLOSE | NATIVE_COMBINATION | TAIL_RISK | BAND_Z+BAND_H | REVERSE_DIRECT | 3 | -0.0735 | 0.0003 | 0.0524 | 0 | 0.2230 | 44700.0000 | 7242 | 7242 | 2229.0000 | 0.9849 | 0.1609 | -0.0661 |
| E_CLOSE | NATIVE_COMBINATION | TAIL_RISK | BAND_Z+BAND_H | REVERSE_REVERSE | 3 | -0.0829 | -0.0778 | 0.0720 | 0 | 0.2377 | 44700.0000 | 7045 | 7044 | 2229.0000 | 0.7145 | 0.1556 | -0.0758 |
| E_TOUCH | FIXED_NATIVE |  | BAND_Z+BAND_H | FIXED | 3 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 44700.0000 | 8496 | 8496 | 2229.0000 | 0.9986 | 0.1918 | -0.0760 |
| E_TOUCH | NATIVE | LEVEL_FORECAST_K12 | BAND_H | DIRECT | 3 | -0.0784 | 0.0034 | 0.1035 | 0 | 0.1600 | 44700.0000 | 5060 | 5060 | 2229.0000 | 0.5785 | 0.1148 | -0.0727 |
| E_TOUCH | NATIVE | LEVEL_FORECAST_K12 | BAND_H | REVERSE | 3 | -0.0717 | 0.0090 | 0.0866 | 0 | 0.1618 | 44700.0000 | 5057 | 5057 | 2229.0000 | 0.5689 | 0.1149 | -0.0671 |
| E_TOUCH | NATIVE | LEVEL_FORECAST_K12 | BAND_Z | DIRECT | 3 | -0.3128 | 0.0693 | 0.2712 | 1 | 0.2498 | 44700.0000 | 5060 | 5060 | 2229.0000 | 0.5960 | 0.1141 | -0.0068 |
| E_TOUCH | NATIVE | LEVEL_FORECAST_K12 | BAND_Z | REVERSE | 3 | -0.0351 | 0.0622 | 0.2200 | 0 | 0.2716 | 44700.0000 | 5050 | 5050 | 2229.0000 | 0.5943 | 0.1147 | 0.0213 |
| E_TOUCH | NATIVE | LEVEL_FORECAST_K4 | BAND_H | DIRECT | 3 | -0.0405 | 0.0199 | 0.1124 | 0 | 0.1649 | 44700.0000 | 5062 | 5062 | 2229.0000 | 0.5817 | 0.1148 | -0.0562 |
| E_TOUCH | NATIVE | LEVEL_FORECAST_K4 | BAND_H | REVERSE | 3 | -0.0760 | 0.0047 | 0.0807 | 0 | 0.1596 | 44700.0000 | 5057 | 5055 | 2229.0000 | 0.5658 | 0.1150 | -0.0713 |
| E_TOUCH | NATIVE | LEVEL_FORECAST_K4 | BAND_Z | DIRECT | 3 | -0.1229 | -0.0131 | 0.3198 | 0 | 0.2586 | 44700.0000 | 5099 | 5099 | 2229.0000 | 0.5957 | 0.1154 | -0.0225 |
| E_TOUCH | NATIVE | LEVEL_FORECAST_K4 | BAND_Z | REVERSE | 3 | -0.1298 | 0.1256 | 0.3437 | 0 | 0.2501 | 44700.0000 | 5016 | 5016 | 2229.0000 | 0.5942 | 0.1127 | 0.0496 |
| E_TOUCH | NATIVE | LEVEL_NOW | BAND_H | DIRECT | 3 | 0.0113 | 0.0128 | 0.0746 | 0 | 0.0626 | 44700.0000 | 8453 | 8453 | 2229.0000 | 0.9708 | 0.1909 | -0.0633 |
| E_TOUCH | NATIVE | LEVEL_NOW | BAND_H | REVERSE | 3 | 0.0016 | 0.0079 | 0.0708 | 0 | 0.0730 | 44700.0000 | 8450 | 8448 | 2229.0000 | 0.9507 | 0.1911 | -0.0745 |
| E_TOUCH | NATIVE | LEVEL_NOW | BAND_Z | DIRECT | 3 | -0.1208 | -0.0346 | 0.4599 | 0 | 0.2652 | 44700.0000 | 8498 | 8498 | 2229.0000 | 0.9933 | 0.1925 | -0.0204 |
| E_TOUCH | NATIVE | LEVEL_NOW | BAND_Z | REVERSE | 3 | -0.0428 | 0.1333 | 0.3726 | 0 | 0.2618 | 44700.0000 | 8405 | 8405 | 2229.0000 | 0.9906 | 0.1892 | 0.0576 |
| E_TOUCH | NATIVE | RANGE_SCALE | BAND_H | DIRECT | 3 | -0.0111 | 0.0087 | 0.1988 | 1 | 0.0613 | 44700.0000 | 8493 | 8493 | 2229.0000 | 0.9904 | 0.1918 | 0.0002 |
| E_TOUCH | NATIVE | RANGE_SCALE | BAND_H | REVERSE | 3 | -0.0022 | 0.0095 | 0.1187 | 0 | 0.0582 | 44700.0000 | 8476 | 8476 | 2229.0000 | 0.9318 | 0.1916 | -0.0783 |
| E_TOUCH | NATIVE | RANGE_SCALE | BAND_Z | DIRECT | 3 | -0.0327 | 0.0973 | 0.2985 | 0 | 0.2385 | 44700.0000 | 8805 | 8805 | 2229.0000 | 0.9990 | 0.1953 | 0.0677 |
| E_TOUCH | NATIVE | RANGE_SCALE | BAND_Z | REVERSE | 3 | -0.2190 | -0.0527 | 0.3586 | 1 | 0.2113 | 44700.0000 | 8139 | 8139 | 2229.0000 | 0.9927 | 0.1839 | -0.1186 |
| E_TOUCH | NATIVE | SHOCK | BAND_H | DIRECT | 3 | -0.0194 | 0.0269 | 0.1085 | 0 | 0.0681 | 44700.0000 | 8471 | 8471 | 2229.0000 | 0.9338 | 0.1915 | -0.0492 |
| E_TOUCH | NATIVE | SHOCK | BAND_H | REVERSE | 3 | 0.0158 | 0.0229 | 0.1085 | 1 | 0.0607 | 44700.0000 | 8474 | 8474 | 2229.0000 | 0.9895 | 0.1914 | -0.0532 |
| E_TOUCH | NATIVE | SHOCK | BAND_Z | DIRECT | 3 | -0.3446 | 0.0653 | 0.5040 | 2 | 0.2463 | 44700.0000 | 8072 | 8072 | 2229.0000 | 0.9925 | 0.1827 | -0.0107 |
| E_TOUCH | NATIVE | SHOCK | BAND_Z | REVERSE | 3 | 0.0974 | 0.1047 | 0.1648 | 0 | 0.2797 | 44700.0000 | 8860 | 8860 | 2229.0000 | 0.9961 | 0.2007 | 0.0888 |
| E_TOUCH | NATIVE | SWING_GT_CUR | BAND_H | DIRECT | 3 | 0.0194 | 0.0386 | 0.1900 | 0 | 0.0645 | 44700.0000 | 8260 | 8260 | 2229.0000 | 0.9423 | 0.1866 | -0.0087 |
| E_TOUCH | NATIVE | SWING_GT_CUR | BAND_H | REVERSE | 3 | 0.0007 | 0.0116 | 0.0147 | 0 | 0.0657 | 44700.0000 | 8268 | 8267 | 2229.0000 | 0.9424 | 0.1870 | -0.0614 |
| E_TOUCH | NATIVE | SWING_GT_CUR | BAND_Z | DIRECT | 3 | -0.2638 | 0.0544 | 0.4192 | 0 | 0.2658 | 44700.0000 | 8272 | 8272 | 2229.0000 | 0.9697 | 0.1881 | -0.0216 |
| E_TOUCH | NATIVE | SWING_GT_CUR | BAND_Z | REVERSE | 3 | -0.0646 | 0.0701 | 0.4409 | 0 | 0.2558 | 44700.0000 | 8255 | 8255 | 2229.0000 | 0.9705 | 0.1854 | 0.0358 |
| E_TOUCH | NATIVE | SWING_SCALE | BAND_H | DIRECT | 3 | -0.0151 | 0.0264 | 0.0345 | 0 | 0.0738 | 44700.0000 | 8267 | 8267 | 2229.0000 | 0.9632 | 0.1867 | -0.0497 |
| E_TOUCH | NATIVE | SWING_SCALE | BAND_H | REVERSE | 3 | -0.0113 | 0.0188 | 0.0331 | 0 | 0.0635 | 44700.0000 | 8260 | 8259 | 2229.0000 | 0.9114 | 0.1869 | -0.0572 |
| E_TOUCH | NATIVE | SWING_SCALE | BAND_Z | DIRECT | 3 | -0.0230 | 0.1344 | 0.3506 | 0 | 0.2230 | 44700.0000 | 8535 | 8535 | 2229.0000 | 0.9724 | 0.1889 | 0.0774 |
| E_TOUCH | NATIVE | SWING_SCALE | BAND_Z | REVERSE | 3 | -0.1524 | -0.0206 | 0.3198 | 0 | 0.1791 | 44700.0000 | 7961 | 7961 | 2229.0000 | 0.9680 | 0.1781 | -0.0520 |
| E_TOUCH | NATIVE | TAIL_RISK | BAND_H | DIRECT | 3 | 0.0178 | 0.0345 | 0.0682 | 0 | 0.0646 | 44700.0000 | 8486 | 8486 | 2229.0000 | 0.9890 | 0.1916 | -0.0582 |
| E_TOUCH | NATIVE | TAIL_RISK | BAND_H | REVERSE | 3 | -0.0350 | -0.0311 | 0.0141 | 0 | 0.0634 | 44700.0000 | 8484 | 8483 | 2229.0000 | 0.9332 | 0.1918 | -0.0619 |
| E_TOUCH | NATIVE | TAIL_RISK | BAND_Z | DIRECT | 3 | -0.0961 | 0.1208 | 0.3674 | 0 | 0.2700 | 44700.0000 | 8790 | 8790 | 2229.0000 | 0.9988 | 0.1945 | 0.0448 |
| E_TOUCH | NATIVE | TAIL_RISK | BAND_Z | REVERSE | 3 | -0.0258 | -0.0256 | 0.4368 | 0 | 0.2799 | 44700.0000 | 8170 | 8170 | 2229.0000 | 0.9923 | 0.1837 | 0.0746 |
| E_TOUCH | NATIVE_COMBINATION | LEVEL_FORECAST_K12 | BAND_Z+BAND_H | DIRECT_DIRECT | 3 | -0.3029 | 0.0834 | 0.2349 | 1 | 0.2528 | 44700.0000 | 5033 | 5033 | 2229.0000 | 0.5576 | 0.1138 | 0.0074 |
| E_TOUCH | NATIVE_COMBINATION | LEVEL_FORECAST_K12 | BAND_Z+BAND_H | DIRECT_REVERSE | 3 | -0.3085 | 0.0626 | 0.3007 | 1 | 0.2416 | 44700.0000 | 5056 | 5056 | 2229.0000 | 0.5914 | 0.1141 | -0.0135 |
| E_TOUCH | NATIVE_COMBINATION | LEVEL_FORECAST_K12 | BAND_Z+BAND_H | REVERSE_DIRECT | 3 | -0.0777 | 0.0825 | 0.1253 | 0 | 0.2776 | 44700.0000 | 5046 | 5046 | 2229.0000 | 0.5937 | 0.1145 | 0.0064 |
| E_TOUCH | NATIVE_COMBINATION | LEVEL_FORECAST_K12 | BAND_Z+BAND_H | REVERSE_REVERSE | 3 | -0.0254 | 0.0729 | 0.1154 | 0 | 0.2726 | 44700.0000 | 5026 | 5026 | 2229.0000 | 0.5358 | 0.1139 | -0.0031 |
| E_TOUCH | NATIVE_COMBINATION | LEVEL_FORECAST_K4 | BAND_Z+BAND_H | DIRECT_DIRECT | 3 | -0.1648 | 0.0179 | 0.2909 | 0 | 0.2664 | 44700.0000 | 5074 | 5074 | 2229.0000 | 0.5634 | 0.1144 | -0.0581 |
| E_TOUCH | NATIVE_COMBINATION | LEVEL_FORECAST_K4 | BAND_Z+BAND_H | DIRECT_REVERSE | 3 | -0.1504 | 0.0056 | 0.3063 | 0 | 0.2592 | 44700.0000 | 5100 | 5098 | 2229.0000 | 0.5906 | 0.1154 | -0.0500 |
| E_TOUCH | NATIVE_COMBINATION | LEVEL_FORECAST_K4 | BAND_Z+BAND_H | REVERSE_DIRECT | 3 | -0.1178 | 0.1093 | 0.2726 | 0 | 0.2382 | 44700.0000 | 5015 | 5015 | 2229.0000 | 0.5949 | 0.1126 | 0.0333 |
| E_TOUCH | NATIVE_COMBINATION | LEVEL_FORECAST_K4 | BAND_Z+BAND_H | REVERSE_REVERSE | 3 | -0.0776 | 0.1247 | 0.2181 | 0 | 0.2487 | 44700.0000 | 4983 | 4982 | 2229.0000 | 0.5306 | 0.1124 | 0.0228 |
| E_TOUCH | NATIVE_COMBINATION | LEVEL_NOW | BAND_Z+BAND_H | DIRECT_DIRECT | 3 | -0.0826 | 0.0096 | 0.4166 | 0 | 0.2736 | 44700.0000 | 8462 | 8462 | 2229.0000 | 0.9387 | 0.1912 | 0.0179 |
| E_TOUCH | NATIVE_COMBINATION | LEVEL_NOW | BAND_Z+BAND_H | DIRECT_REVERSE | 3 | -0.0714 | -0.0280 | 0.4726 | 0 | 0.2687 | 44700.0000 | 8499 | 8497 | 2229.0000 | 0.9861 | 0.1926 | 0.0290 |
| E_TOUCH | NATIVE_COMBINATION | LEVEL_NOW | BAND_Z+BAND_H | REVERSE_DIRECT | 3 | -0.0226 | 0.1349 | 0.3165 | 0 | 0.2676 | 44700.0000 | 8404 | 8404 | 2229.0000 | 0.9920 | 0.1890 | 0.0778 |
| E_TOUCH | NATIVE_COMBINATION | LEVEL_NOW | BAND_Z+BAND_H | REVERSE_REVERSE | 3 | 0.0300 | 0.1156 | 0.2590 | 0 | 0.2777 | 44700.0000 | 8349 | 8348 | 2229.0000 | 0.8972 | 0.1885 | 0.0603 |
| E_TOUCH | NATIVE_COMBINATION | RANGE_SCALE | BAND_Z+BAND_H | DIRECT_DIRECT | 3 | -0.0047 | 0.1201 | 0.3824 | 0 | 0.2405 | 44700.0000 | 8797 | 8796 | 2229.0000 | 0.9849 | 0.1949 | 0.0957 |
| E_TOUCH | NATIVE_COMBINATION | RANGE_SCALE | BAND_Z+BAND_H | DIRECT_REVERSE | 3 | 0.0186 | 0.0761 | 0.3445 | 0 | 0.2485 | 44700.0000 | 8803 | 8802 | 2229.0000 | 0.9819 | 0.1952 | 0.1190 |
| E_TOUCH | NATIVE_COMBINATION | RANGE_SCALE | BAND_Z+BAND_H | REVERSE_DIRECT | 3 | -0.2050 | -0.0331 | 0.4360 | 1 | 0.2020 | 44700.0000 | 8140 | 8140 | 2229.0000 | 0.9942 | 0.1840 | -0.1046 |
| E_TOUCH | NATIVE_COMBINATION | RANGE_SCALE | BAND_Z+BAND_H | REVERSE_REVERSE | 3 | -0.1885 | -0.0107 | 0.3025 | 0 | 0.2062 | 44700.0000 | 8075 | 8075 | 2229.0000 | 0.8673 | 0.1817 | -0.0868 |
| E_TOUCH | NATIVE_COMBINATION | SHOCK | BAND_Z+BAND_H | DIRECT_DIRECT | 3 | -0.3443 | 0.0414 | 0.3577 | 1 | 0.2620 | 44700.0000 | 8007 | 8006 | 2229.0000 | 0.8584 | 0.1814 | -0.0347 |
| E_TOUCH | NATIVE_COMBINATION | SHOCK | BAND_Z+BAND_H | DIRECT_REVERSE | 3 | -0.3654 | 0.0718 | 0.5963 | 2 | 0.2530 | 44700.0000 | 8065 | 8065 | 2229.0000 | 0.9961 | 0.1826 | -0.0043 |
| E_TOUCH | NATIVE_COMBINATION | SHOCK | BAND_Z+BAND_H | REVERSE_DIRECT | 3 | 0.0705 | 0.1151 | 0.1415 | 0 | 0.2827 | 44700.0000 | 8864 | 8864 | 2229.0000 | 0.9866 | 0.2008 | 0.0654 |
| E_TOUCH | NATIVE_COMBINATION | SHOCK | BAND_Z+BAND_H | REVERSE_REVERSE | 3 | 0.0985 | 0.1032 | 0.1440 | 0 | 0.2848 | 44700.0000 | 8853 | 8853 | 2229.0000 | 0.9788 | 0.2006 | 0.0679 |
| E_TOUCH | NATIVE_COMBINATION | SWING_GT_CUR | BAND_Z+BAND_H | DIRECT_DIRECT | 3 | -0.2321 | 0.0695 | 0.4286 | 0 | 0.2584 | 44700.0000 | 8232 | 8231 | 2229.0000 | 0.9059 | 0.1875 | -0.0065 |
| E_TOUCH | NATIVE_COMBINATION | SWING_GT_CUR | BAND_Z+BAND_H | DIRECT_REVERSE | 3 | -0.2630 | 0.0615 | 0.4016 | 1 | 0.2626 | 44700.0000 | 8273 | 8273 | 2229.0000 | 0.9680 | 0.1882 | -0.0145 |
| E_TOUCH | NATIVE_COMBINATION | SWING_GT_CUR | BAND_Z+BAND_H | REVERSE_DIRECT | 3 | -0.0399 | 0.1063 | 0.3629 | 0 | 0.2618 | 44700.0000 | 8251 | 8251 | 2229.0000 | 0.9662 | 0.1853 | 0.0605 |
| E_TOUCH | NATIVE_COMBINATION | SWING_GT_CUR | BAND_Z+BAND_H | REVERSE_REVERSE | 3 | -0.1156 | 0.0641 | 0.4389 | 0 | 0.2605 | 44700.0000 | 8219 | 8219 | 2229.0000 | 0.9040 | 0.1843 | -0.0120 |
| E_TOUCH | NATIVE_COMBINATION | SWING_SCALE | BAND_Z+BAND_H | DIRECT_DIRECT | 3 | 0.0114 | 0.1414 | 0.3445 | 0 | 0.2218 | 44700.0000 | 8523 | 8523 | 2229.0000 | 0.9584 | 0.1886 | 0.1118 |
| E_TOUCH | NATIVE_COMBINATION | SWING_SCALE | BAND_Z+BAND_H | DIRECT_REVERSE | 3 | -0.0081 | 0.1228 | 0.3870 | 0 | 0.2187 | 44700.0000 | 8536 | 8534 | 2229.0000 | 0.9547 | 0.1890 | 0.0923 |
| E_TOUCH | NATIVE_COMBINATION | SWING_SCALE | BAND_Z+BAND_H | REVERSE_DIRECT | 3 | -0.1545 | 0.0082 | 0.3311 | 0 | 0.1794 | 44700.0000 | 7955 | 7955 | 2229.0000 | 0.9665 | 0.1780 | -0.0541 |
| E_TOUCH | NATIVE_COMBINATION | SWING_SCALE | BAND_Z+BAND_H | REVERSE_REVERSE | 3 | -0.1758 | -0.0036 | 0.3432 | 0 | 0.1803 | 44700.0000 | 7903 | 7902 | 2229.0000 | 0.8471 | 0.1763 | -0.0754 |
| E_TOUCH | NATIVE_COMBINATION | TAIL_RISK | BAND_Z+BAND_H | DIRECT_DIRECT | 3 | -0.1089 | 0.1198 | 0.3527 | 0 | 0.2770 | 44700.0000 | 8774 | 8774 | 2229.0000 | 0.9790 | 0.1942 | 0.0437 |
| E_TOUCH | NATIVE_COMBINATION | TAIL_RISK | BAND_Z+BAND_H | DIRECT_REVERSE | 3 | -0.0585 | 0.1231 | 0.3565 | 0 | 0.2645 | 44700.0000 | 8794 | 8793 | 2229.0000 | 0.9880 | 0.1946 | 0.0470 |
| E_TOUCH | NATIVE_COMBINATION | TAIL_RISK | BAND_Z+BAND_H | REVERSE_DIRECT | 3 | -0.0164 | -0.0039 | 0.5144 | 1 | 0.2760 | 44700.0000 | 8164 | 8164 | 2229.0000 | 0.9970 | 0.1836 | 0.0840 |
| E_TOUCH | NATIVE_COMBINATION | TAIL_RISK | BAND_Z+BAND_H | REVERSE_REVERSE | 3 | -0.0562 | -0.0155 | 0.5383 | 1 | 0.2689 | 44700.0000 | 8104 | 8103 | 2229.0000 | 0.8566 | 0.1815 | 0.0849 |

#### crypto (130 rows; per-symbol rows in `tables/native_all_crypto.csv`)

| entry_variant | arm_class | component | parameter | orientation | sym | est_min | est_med | est_max | ci_ex0 | mde_med | elig | fills | closes | eff | ev_rate | fill_rate | occ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E_CLOSE | FIXED_NATIVE |  | BAND_Z+BAND_H | FIXED | 25 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 231121.0000 | 38212 | 38211 | 9637.0000 | 0.9852 | 0.1663 | -0.4354 |
| E_CLOSE | NATIVE | LEVEL_FORECAST_K12 | BAND_H | DIRECT | 25 | -5.5371 | 0.4304 | 1.8591 | 1 | 1.3685 | 231121.0000 | 22548 | 22548 | 9637.0000 | 0.5288 | 0.0979 | -0.0827 |
| E_CLOSE | NATIVE | LEVEL_FORECAST_K12 | BAND_H | REVERSE | 25 | -1.8728 | 0.4843 | 4.5389 | 3 | 1.3127 | 231121.0000 | 22569 | 22569 | 9637.0000 | 0.5449 | 0.0983 | -0.2360 |
| E_CLOSE | NATIVE | LEVEL_FORECAST_K12 | BAND_Z | DIRECT | 25 | -9.7121 | 0.3130 | 2.0336 | 1 | 1.6807 | 231121.0000 | 22653 | 22653 | 9637.0000 | 0.5790 | 0.0982 | -0.3920 |
| E_CLOSE | NATIVE | LEVEL_FORECAST_K12 | BAND_Z | REVERSE | 25 | -23.2408 | 0.3862 | 3.1515 | 1 | 1.7156 | 231121.0000 | 22973 | 22972 | 9637.0000 | 0.5813 | 0.0998 | -0.2792 |
| E_CLOSE | NATIVE | LEVEL_FORECAST_K4 | BAND_H | DIRECT | 25 | -5.8685 | 0.3672 | 2.8415 | 1 | 1.3374 | 231121.0000 | 22591 | 22578 | 9637.0000 | 0.5351 | 0.0980 | -0.2407 |
| E_CLOSE | NATIVE | LEVEL_FORECAST_K4 | BAND_H | REVERSE | 25 | -2.4330 | 0.4906 | 3.6600 | 3 | 1.3407 | 231121.0000 | 22551 | 22540 | 9637.0000 | 0.5379 | 0.0983 | -0.0744 |
| E_CLOSE | NATIVE | LEVEL_FORECAST_K4 | BAND_Z | DIRECT | 25 | -18.2284 | 0.3262 | 2.0839 | 1 | 1.7125 | 231121.0000 | 22781 | 22781 | 9637.0000 | 0.5813 | 0.0990 | -0.3473 |
| E_CLOSE | NATIVE | LEVEL_FORECAST_K4 | BAND_Z | REVERSE | 25 | -14.8819 | 0.5924 | 4.5639 | 0 | 1.7535 | 231121.0000 | 22755 | 22754 | 9637.0000 | 0.5785 | 0.0984 | -0.2988 |
| E_CLOSE | NATIVE | LEVEL_NOW | BAND_H | DIRECT | 25 | -3.6031 | -0.0700 | 1.6387 | 0 | 0.6773 | 231121.0000 | 37699 | 37686 | 9637.0000 | 0.8923 | 0.1636 | -0.8770 |
| E_CLOSE | NATIVE | LEVEL_NOW | BAND_H | REVERSE | 25 | -7.1258 | -0.0080 | 0.8141 | 0 | 0.7303 | 231121.0000 | 37666 | 37656 | 9637.0000 | 0.8976 | 0.1633 | -0.7231 |
| E_CLOSE | NATIVE | LEVEL_NOW | BAND_Z | DIRECT | 25 | -17.5717 | -0.0769 | 1.5995 | 0 | 1.7684 | 231121.0000 | 37961 | 37961 | 9637.0000 | 0.9692 | 0.1643 | -0.7615 |
| E_CLOSE | NATIVE | LEVEL_NOW | BAND_Z | REVERSE | 25 | -6.8899 | -0.2406 | 2.6871 | 1 | 1.9194 | 231121.0000 | 38055 | 38054 | 9637.0000 | 0.9647 | 0.1647 | -0.9584 |
| E_CLOSE | NATIVE | RANGE_SCALE | BAND_H | DIRECT | 25 | -0.7633 | -0.0161 | 0.9836 | 0 | 0.5439 | 231121.0000 | 37943 | 37932 | 9637.0000 | 0.8935 | 0.1654 | -0.5035 |
| E_CLOSE | NATIVE | RANGE_SCALE | BAND_H | REVERSE | 25 | -9.1739 | -0.0428 | 0.7715 | 0 | 0.5931 | 231121.0000 | 37913 | 37903 | 9637.0000 | 0.9211 | 0.1646 | -0.7352 |
| E_CLOSE | NATIVE | RANGE_SCALE | BAND_Z | DIRECT | 25 | -14.3106 | 0.0562 | 2.1984 | 1 | 1.9145 | 231121.0000 | 37556 | 37555 | 9637.0000 | 0.9814 | 0.1640 | -0.2681 |
| E_CLOSE | NATIVE | RANGE_SCALE | BAND_Z | REVERSE | 25 | -11.9744 | -0.0516 | 4.1873 | 1 | 1.6161 | 231121.0000 | 38714 | 38714 | 9637.0000 | 0.9768 | 0.1672 | -0.7668 |
| E_CLOSE | NATIVE | SHOCK | BAND_H | DIRECT | 25 | -3.6039 | -0.0561 | 0.9617 | 1 | 0.7367 | 231121.0000 | 37689 | 37669 | 9637.0000 | 0.8371 | 0.1637 | -0.6911 |
| E_CLOSE | NATIVE | SHOCK | BAND_H | REVERSE | 25 | -6.2418 | -0.0164 | 1.3737 | 0 | 0.4974 | 231121.0000 | 38002 | 37998 | 9637.0000 | 0.9691 | 0.1650 | -0.6150 |
| E_CLOSE | NATIVE | SHOCK | BAND_Z | DIRECT | 25 | -12.7546 | -0.7520 | 3.6556 | 0 | 1.8635 | 231121.0000 | 36259 | 36258 | 9637.0000 | 0.9595 | 0.1587 | -0.7495 |
| E_CLOSE | NATIVE | SHOCK | BAND_Z | REVERSE | 25 | -7.2366 | 0.0109 | 2.0068 | 0 | 2.1339 | 231121.0000 | 40192 | 40192 | 9637.0000 | 0.9882 | 0.1733 | -0.6036 |
| E_CLOSE | NATIVE | SWING_GT_CUR | BAND_H | DIRECT | 25 | -6.5483 | 0.0370 | 3.2018 | 0 | 0.8421 | 231121.0000 | 35787 | 35779 | 9637.0000 | 0.8624 | 0.1561 | -0.6964 |
| E_CLOSE | NATIVE | SWING_GT_CUR | BAND_H | REVERSE | 25 | -12.9524 | 0.0042 | 3.1781 | 1 | 0.9437 | 231121.0000 | 35802 | 35790 | 9637.0000 | 0.8368 | 0.1564 | -0.5608 |
| E_CLOSE | NATIVE | SWING_GT_CUR | BAND_Z | DIRECT | 25 | -19.4079 | -0.0169 | 3.6522 | 0 | 1.8199 | 231121.0000 | 36313 | 36313 | 9637.0000 | 0.9211 | 0.1586 | -0.6916 |
| E_CLOSE | NATIVE | SWING_GT_CUR | BAND_Z | REVERSE | 25 | -7.0264 | 0.1755 | 5.5728 | 0 | 1.7903 | 231121.0000 | 35788 | 35787 | 9637.0000 | 0.9231 | 0.1552 | -0.0923 |
| E_CLOSE | NATIVE | SWING_SCALE | BAND_H | DIRECT | 25 | -17.4523 | 0.0352 | 5.8164 | 0 | 0.7700 | 231121.0000 | 35432 | 35421 | 9637.0000 | 0.8020 | 0.1554 | -0.4010 |
| E_CLOSE | NATIVE | SWING_SCALE | BAND_H | REVERSE | 25 | -17.4523 | -0.0445 | 5.8164 | 0 | 0.8709 | 231121.0000 | 35547 | 35540 | 9637.0000 | 0.8772 | 0.1563 | -0.4267 |
| E_CLOSE | NATIVE | SWING_SCALE | BAND_Z | DIRECT | 25 | -17.4523 | 0.0027 | 5.8164 | 1 | 1.6357 | 231121.0000 | 34895 | 34894 | 9637.0000 | 0.9075 | 0.1509 | -0.1715 |
| E_CLOSE | NATIVE | SWING_SCALE | BAND_Z | REVERSE | 25 | -17.4523 | 0.0276 | 5.8164 | 0 | 1.5671 | 231121.0000 | 36455 | 36455 | 9637.0000 | 0.9355 | 0.1593 | -0.6898 |
| E_CLOSE | NATIVE | TAIL_RISK | BAND_H | DIRECT | 25 | -1.1483 | -0.0318 | 0.9649 | 1 | 0.5860 | 231121.0000 | 37938 | 37923 | 9637.0000 | 0.9011 | 0.1650 | -0.8902 |
| E_CLOSE | NATIVE | TAIL_RISK | BAND_H | REVERSE | 25 | -8.2370 | -0.0785 | 0.5301 | 0 | 0.6939 | 231121.0000 | 37926 | 37918 | 9637.0000 | 0.9089 | 0.1648 | -0.7897 |
| E_CLOSE | NATIVE | TAIL_RISK | BAND_Z | DIRECT | 25 | -21.9546 | -0.1795 | 3.9383 | 0 | 1.9140 | 231121.0000 | 37972 | 37971 | 9637.0000 | 0.9774 | 0.1656 | -0.6473 |
| E_CLOSE | NATIVE | TAIL_RISK | BAND_Z | REVERSE | 25 | -7.4904 | -0.1755 | 4.1289 | 3 | 1.7185 | 231121.0000 | 38525 | 38525 | 9637.0000 | 0.9761 | 0.1664 | -0.9657 |
| E_CLOSE | NATIVE_COMBINATION | LEVEL_FORECAST_K12 | BAND_Z+BAND_H | DIRECT_DIRECT | 25 | -10.4859 | 0.2610 | 1.9578 | 1 | 1.7435 | 231121.0000 | 22237 | 22237 | 9637.0000 | 0.4842 | 0.0965 | -0.4718 |
| E_CLOSE | NATIVE_COMBINATION | LEVEL_FORECAST_K12 | BAND_Z+BAND_H | DIRECT_REVERSE | 25 | -10.1947 | 0.3411 | 2.0529 | 1 | 1.7411 | 231121.0000 | 22551 | 22551 | 9637.0000 | 0.5742 | 0.0979 | -0.2878 |
| E_CLOSE | NATIVE_COMBINATION | LEVEL_FORECAST_K12 | BAND_Z+BAND_H | REVERSE_DIRECT | 25 | -23.2408 | 0.4244 | 3.1107 | 1 | 1.7005 | 231121.0000 | 22913 | 22913 | 9637.0000 | 0.5663 | 0.0995 | -0.2632 |
| E_CLOSE | NATIVE_COMBINATION | LEVEL_FORECAST_K12 | BAND_Z+BAND_H | REVERSE_REVERSE | 25 | -22.4922 | 0.4097 | 3.2099 | 1 | 1.7255 | 231121.0000 | 22712 | 22712 | 9637.0000 | 0.5081 | 0.0986 | -0.2643 |
| E_CLOSE | NATIVE_COMBINATION | LEVEL_FORECAST_K4 | BAND_Z+BAND_H | DIRECT_DIRECT | 25 | -22.7899 | 0.2271 | 2.9577 | 1 | 1.7298 | 231121.0000 | 22437 | 22422 | 9637.0000 | 0.4965 | 0.0971 | -0.4146 |
| E_CLOSE | NATIVE_COMBINATION | LEVEL_FORECAST_K4 | BAND_Z+BAND_H | DIRECT_REVERSE | 25 | -17.2449 | 0.3079 | 1.8418 | 1 | 1.6990 | 231121.0000 | 22691 | 22684 | 9637.0000 | 0.5717 | 0.0985 | -0.2266 |
| E_CLOSE | NATIVE_COMBINATION | LEVEL_FORECAST_K4 | BAND_Z+BAND_H | REVERSE_DIRECT | 25 | -14.3344 | 0.5783 | 4.5639 | 0 | 1.7431 | 231121.0000 | 22747 | 22733 | 9637.0000 | 0.5699 | 0.0988 | -0.3391 |
| E_CLOSE | NATIVE_COMBINATION | LEVEL_FORECAST_K4 | BAND_Z+BAND_H | REVERSE_REVERSE | 25 | -14.1334 | 0.5460 | 4.1437 | 0 | 1.7186 | 231121.0000 | 22439 | 22429 | 9637.0000 | 0.4970 | 0.0976 | -0.4176 |
| E_CLOSE | NATIVE_COMBINATION | LEVEL_NOW | BAND_Z+BAND_H | DIRECT_DIRECT | 25 | -21.1783 | 0.0146 | 2.5331 | 0 | 1.8945 | 231121.0000 | 37354 | 37339 | 9637.0000 | 0.8217 | 0.1614 | -0.7986 |
| E_CLOSE | NATIVE_COMBINATION | LEVEL_NOW | BAND_Z+BAND_H | DIRECT_REVERSE | 25 | -16.5881 | -0.0633 | 1.9107 | 0 | 1.7742 | 231121.0000 | 37817 | 37810 | 9637.0000 | 0.9520 | 0.1639 | -0.6767 |
| E_CLOSE | NATIVE_COMBINATION | LEVEL_NOW | BAND_Z+BAND_H | REVERSE_DIRECT | 25 | -6.0091 | -0.2953 | 2.5235 | 2 | 1.9710 | 231121.0000 | 38030 | 38016 | 9637.0000 | 0.9502 | 0.1647 | -1.0252 |
| E_CLOSE | NATIVE_COMBINATION | LEVEL_NOW | BAND_Z+BAND_H | REVERSE_REVERSE | 25 | -8.8248 | -0.4541 | 2.7285 | 1 | 1.9480 | 231121.0000 | 37545 | 37535 | 9637.0000 | 0.8329 | 0.1624 | -0.8064 |
| E_CLOSE | NATIVE_COMBINATION | RANGE_SCALE | BAND_Z+BAND_H | DIRECT_DIRECT | 25 | -13.5620 | -0.0409 | 3.7024 | 0 | 1.8359 | 231121.0000 | 36905 | 36893 | 9637.0000 | 0.8270 | 0.1612 | -0.1663 |
| E_CLOSE | NATIVE_COMBINATION | RANGE_SCALE | BAND_Z+BAND_H | DIRECT_REVERSE | 25 | -14.2853 | -0.0334 | 1.5402 | 0 | 1.9881 | 231121.0000 | 37401 | 37392 | 9637.0000 | 0.9507 | 0.1632 | -0.3719 |
| E_CLOSE | NATIVE_COMBINATION | RANGE_SCALE | BAND_Z+BAND_H | REVERSE_DIRECT | 25 | -11.0019 | 0.0168 | 4.4694 | 2 | 1.6602 | 231121.0000 | 38639 | 38627 | 9637.0000 | 0.9472 | 0.1664 | -0.6914 |
| E_CLOSE | NATIVE_COMBINATION | RANGE_SCALE | BAND_Z+BAND_H | REVERSE_REVERSE | 25 | -12.7235 | -0.0871 | 4.1785 | 1 | 1.5982 | 231121.0000 | 38229 | 38218 | 9637.0000 | 0.8857 | 0.1653 | -0.7817 |
| E_CLOSE | NATIVE_COMBINATION | SHOCK | BAND_Z+BAND_H | DIRECT_DIRECT | 25 | -19.2407 | -0.5120 | 5.2816 | 0 | 2.0064 | 231121.0000 | 35160 | 35139 | 9637.0000 | 0.7176 | 0.1539 | -0.8223 |
| E_CLOSE | NATIVE_COMBINATION | SHOCK | BAND_Z+BAND_H | DIRECT_REVERSE | 25 | -13.9621 | -0.5327 | 3.7618 | 0 | 1.9230 | 231121.0000 | 36113 | 36110 | 9637.0000 | 0.9812 | 0.1580 | -0.6628 |
| E_CLOSE | NATIVE_COMBINATION | SHOCK | BAND_Z+BAND_H | REVERSE_DIRECT | 25 | -7.3632 | -0.0647 | 1.7984 | 0 | 2.1127 | 231121.0000 | 40113 | 40094 | 9637.0000 | 0.9356 | 0.1733 | -0.6523 |
| E_CLOSE | NATIVE_COMBINATION | SHOCK | BAND_Z+BAND_H | REVERSE_REVERSE | 25 | -7.2758 | 0.0683 | 2.4414 | 0 | 2.0648 | 231121.0000 | 40106 | 40103 | 9637.0000 | 0.9489 | 0.1728 | -0.6367 |
| E_CLOSE | NATIVE_COMBINATION | SWING_GT_CUR | BAND_Z+BAND_H | DIRECT_DIRECT | 25 | -20.4869 | 0.2182 | 3.9347 | 1 | 1.8322 | 231121.0000 | 35676 | 35667 | 9637.0000 | 0.7942 | 0.1560 | -0.5472 |
| E_CLOSE | NATIVE_COMBINATION | SWING_GT_CUR | BAND_Z+BAND_H | DIRECT_REVERSE | 25 | -18.4243 | 0.0249 | 3.6535 | 0 | 1.7841 | 231121.0000 | 36267 | 36257 | 9637.0000 | 0.9048 | 0.1584 | -0.6959 |
| E_CLOSE | NATIVE_COMBINATION | SWING_GT_CUR | BAND_Z+BAND_H | REVERSE_DIRECT | 25 | -6.4789 | 0.1576 | 5.5320 | 0 | 1.8460 | 231121.0000 | 35728 | 35720 | 9637.0000 | 0.9112 | 0.1549 | -0.1558 |
| E_CLOSE | NATIVE_COMBINATION | SWING_GT_CUR | BAND_Z+BAND_H | REVERSE_REVERSE | 25 | -8.8054 | 0.0366 | 4.6490 | 0 | 1.8302 | 231121.0000 | 35179 | 35165 | 9637.0000 | 0.7714 | 0.1516 | -0.4540 |
| E_CLOSE | NATIVE_COMBINATION | SWING_SCALE | BAND_Z+BAND_H | DIRECT_DIRECT | 25 | -17.4523 | 0.1082 | 5.8164 | 0 | 1.7634 | 231121.0000 | 34242 | 34230 | 9637.0000 | 0.7323 | 0.1463 | -0.1901 |
| E_CLOSE | NATIVE_COMBINATION | SWING_SCALE | BAND_Z+BAND_H | DIRECT_REVERSE | 25 | -17.4523 | 0.0749 | 5.8164 | 0 | 1.6916 | 231121.0000 | 34785 | 34779 | 9637.0000 | 0.8980 | 0.1505 | -0.2869 |
| E_CLOSE | NATIVE_COMBINATION | SWING_SCALE | BAND_Z+BAND_H | REVERSE_DIRECT | 25 | -17.4523 | 0.0695 | 5.8164 | 0 | 1.5868 | 231121.0000 | 36321 | 36308 | 9637.0000 | 0.8709 | 0.1589 | -0.5733 |
| E_CLOSE | NATIVE_COMBINATION | SWING_SCALE | BAND_Z+BAND_H | REVERSE_REVERSE | 25 | -17.4523 | -0.2084 | 5.8164 | 0 | 1.6654 | 231121.0000 | 36103 | 36095 | 9637.0000 | 0.8466 | 0.1573 | -0.3558 |
| E_CLOSE | NATIVE_COMBINATION | TAIL_RISK | BAND_Z+BAND_H | DIRECT_DIRECT | 25 | -20.1961 | -0.1340 | 9.5404 | 0 | 1.8545 | 231121.0000 | 37301 | 37285 | 9637.0000 | 0.8287 | 0.1623 | -0.7134 |
| E_CLOSE | NATIVE_COMBINATION | TAIL_RISK | BAND_Z+BAND_H | DIRECT_REVERSE | 25 | -21.4071 | -0.1369 | 4.0906 | 0 | 1.8694 | 231121.0000 | 37841 | 37837 | 9637.0000 | 0.9634 | 0.1656 | -0.6362 |
| E_CLOSE | NATIVE_COMBINATION | TAIL_RISK | BAND_Z+BAND_H | REVERSE_DIRECT | 25 | -7.7688 | -0.2713 | 4.3149 | 3 | 1.7742 | 231121.0000 | 38504 | 38487 | 9637.0000 | 0.9594 | 0.1664 | -0.9443 |
| E_CLOSE | NATIVE_COMBINATION | TAIL_RISK | BAND_Z+BAND_H | REVERSE_REVERSE | 25 | -7.9229 | -0.3121 | 3.0974 | 3 | 1.7710 | 231121.0000 | 38046 | 38037 | 9637.0000 | 0.8397 | 0.1645 | -1.0931 |
| E_TOUCH | FIXED_NATIVE |  | BAND_Z+BAND_H | FIXED | 25 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 231121.0000 | 43077 | 43077 | 9637.0000 | 0.9978 | 0.1868 | -0.3958 |
| E_TOUCH | NATIVE | LEVEL_FORECAST_K12 | BAND_H | DIRECT | 25 | -7.5474 | 0.0501 | 2.8556 | 3 | 1.5143 | 231121.0000 | 25553 | 25553 | 9637.0000 | 0.5832 | 0.1106 | -0.4544 |
| E_TOUCH | NATIVE | LEVEL_FORECAST_K12 | BAND_H | REVERSE | 25 | -8.0111 | 0.1252 | 6.4050 | 1 | 1.5834 | 231121.0000 | 25549 | 25549 | 9637.0000 | 0.5870 | 0.1107 | -0.3894 |
| E_TOUCH | NATIVE | LEVEL_FORECAST_K12 | BAND_Z | DIRECT | 25 | -3.3921 | 0.1746 | 31.4104 | 2 | 2.0426 | 231121.0000 | 25277 | 25277 | 9637.0000 | 0.5930 | 0.1094 | -0.0889 |
| E_TOUCH | NATIVE | LEVEL_FORECAST_K12 | BAND_Z | REVERSE | 25 | -8.5074 | 0.4190 | 13.7550 | 2 | 2.0787 | 231121.0000 | 25689 | 25689 | 9637.0000 | 0.5937 | 0.1114 | -0.2270 |
| E_TOUCH | NATIVE | LEVEL_FORECAST_K4 | BAND_H | DIRECT | 25 | -7.2763 | 0.2247 | 9.3856 | 1 | 1.5791 | 231121.0000 | 25572 | 25564 | 9637.0000 | 0.5854 | 0.1106 | -0.1369 |
| E_TOUCH | NATIVE | LEVEL_FORECAST_K4 | BAND_H | REVERSE | 25 | -8.1616 | 0.2324 | 9.5866 | 1 | 1.5358 | 231121.0000 | 25544 | 25539 | 9637.0000 | 0.5847 | 0.1105 | -0.2625 |
| E_TOUCH | NATIVE | LEVEL_FORECAST_K4 | BAND_Z | DIRECT | 25 | -6.3867 | 0.1990 | 37.5341 | 3 | 2.0435 | 231121.0000 | 25456 | 25456 | 9637.0000 | 0.5938 | 0.1104 | -0.1062 |
| E_TOUCH | NATIVE | LEVEL_FORECAST_K4 | BAND_Z | REVERSE | 25 | -4.0490 | 0.4155 | 6.8559 | 3 | 2.0318 | 231121.0000 | 25501 | 25501 | 9637.0000 | 0.5926 | 0.1104 | 0.0823 |
| E_TOUCH | NATIVE | LEVEL_NOW | BAND_H | DIRECT | 25 | -8.0587 | -0.0392 | 2.7487 | 5 | 0.6658 | 231121.0000 | 42781 | 42773 | 9637.0000 | 0.9787 | 0.1852 | -0.6294 |
| E_TOUCH | NATIVE | LEVEL_NOW | BAND_H | REVERSE | 25 | -3.5190 | -0.0661 | 3.8744 | 0 | 0.6261 | 231121.0000 | 42756 | 42751 | 9637.0000 | 0.9762 | 0.1852 | -0.5369 |
| E_TOUCH | NATIVE | LEVEL_NOW | BAND_Z | DIRECT | 25 | -12.9894 | 0.3341 | 8.2306 | 2 | 2.1712 | 231121.0000 | 42494 | 42494 | 9637.0000 | 0.9906 | 0.1840 | -0.1170 |
| E_TOUCH | NATIVE | LEVEL_NOW | BAND_Z | REVERSE | 25 | -8.8933 | -0.1589 | 20.0649 | 0 | 2.1309 | 231121.0000 | 42679 | 42679 | 9637.0000 | 0.9894 | 0.1846 | -0.3056 |
| E_TOUCH | NATIVE | RANGE_SCALE | BAND_H | DIRECT | 25 | -1.1243 | 0.0145 | 0.3020 | 1 | 0.4993 | 231121.0000 | 43058 | 43051 | 9637.0000 | 0.9854 | 0.1864 | -0.3874 |
| E_TOUCH | NATIVE | RANGE_SCALE | BAND_H | REVERSE | 25 | -0.6261 | -0.0177 | 0.8901 | 0 | 0.4472 | 231121.0000 | 43032 | 43024 | 9637.0000 | 0.9855 | 0.1865 | -0.3734 |
| E_TOUCH | NATIVE | RANGE_SCALE | BAND_Z | DIRECT | 25 | -8.7394 | 0.0585 | 4.0990 | 0 | 1.9731 | 231121.0000 | 42403 | 42403 | 9637.0000 | 0.9969 | 0.1844 | -0.1520 |
| E_TOUCH | NATIVE | RANGE_SCALE | BAND_Z | REVERSE | 25 | -4.3083 | 0.0142 | 33.4722 | 1 | 2.0044 | 231121.0000 | 43360 | 43360 | 9637.0000 | 0.9955 | 0.1877 | -0.4038 |
| E_TOUCH | NATIVE | SHOCK | BAND_H | DIRECT | 25 | -1.8365 | -0.0374 | 5.2051 | 3 | 0.6113 | 231121.0000 | 42959 | 42948 | 9637.0000 | 0.9699 | 0.1861 | -0.5322 |
| E_TOUCH | NATIVE | SHOCK | BAND_H | REVERSE | 25 | -2.6141 | -0.0044 | 4.8759 | 1 | 0.5984 | 231121.0000 | 42941 | 42940 | 9637.0000 | 0.9927 | 0.1858 | -0.4165 |
| E_TOUCH | NATIVE | SHOCK | BAND_Z | DIRECT | 25 | -7.9515 | 0.2375 | 37.6278 | 1 | 2.0960 | 231121.0000 | 40919 | 40919 | 9637.0000 | 0.9909 | 0.1779 | -0.4695 |
| E_TOUCH | NATIVE | SHOCK | BAND_Z | REVERSE | 25 | -3.6402 | 0.3930 | 10.5827 | 0 | 2.1254 | 231121.0000 | 44627 | 44627 | 9637.0000 | 0.9959 | 0.1933 | -0.4962 |
| E_TOUCH | NATIVE | SWING_GT_CUR | BAND_H | DIRECT | 25 | -8.5370 | -0.0354 | 15.2085 | 0 | 0.8500 | 231121.0000 | 40621 | 40617 | 9637.0000 | 0.9363 | 0.1772 | -0.5872 |
| E_TOUCH | NATIVE | SWING_GT_CUR | BAND_H | REVERSE | 25 | -8.5261 | 0.0052 | 15.4095 | 2 | 0.7921 | 231121.0000 | 40653 | 40643 | 9637.0000 | 0.9350 | 0.1773 | -0.6772 |
| E_TOUCH | NATIVE | SWING_GT_CUR | BAND_Z | DIRECT | 25 | -9.9424 | 0.4672 | 10.3504 | 1 | 2.0206 | 231121.0000 | 40634 | 40634 | 9637.0000 | 0.9487 | 0.1776 | -0.2283 |
| E_TOUCH | NATIVE | SWING_GT_CUR | BAND_Z | REVERSE | 25 | -7.3785 | 0.7095 | 22.6504 | 2 | 2.0406 | 231121.0000 | 40280 | 40280 | 9637.0000 | 0.9500 | 0.1752 | 0.0502 |
| E_TOUCH | NATIVE | SWING_SCALE | BAND_H | DIRECT | 25 | -2.1896 | -0.0631 | 21.3360 | 3 | 0.8043 | 231121.0000 | 40305 | 40298 | 9637.0000 | 0.9262 | 0.1772 | -0.4753 |
| E_TOUCH | NATIVE | SWING_SCALE | BAND_H | REVERSE | 25 | -1.9651 | 0.0997 | 21.3360 | 2 | 0.8306 | 231121.0000 | 40288 | 40282 | 9637.0000 | 0.9424 | 0.1773 | -0.3534 |
| E_TOUCH | NATIVE | SWING_SCALE | BAND_Z | DIRECT | 25 | -4.0996 | -0.0168 | 21.3360 | 2 | 1.9905 | 231121.0000 | 39529 | 39529 | 9637.0000 | 0.9482 | 0.1727 | 0.0000 |
| E_TOUCH | NATIVE | SWING_SCALE | BAND_Z | REVERSE | 25 | -1.8308 | -0.1493 | 21.3360 | 2 | 1.8595 | 231121.0000 | 40768 | 40768 | 9637.0000 | 0.9519 | 0.1793 | -0.2922 |
| E_TOUCH | NATIVE | TAIL_RISK | BAND_H | DIRECT | 25 | -0.9121 | 0.1173 | 3.7425 | 1 | 0.5856 | 231121.0000 | 43060 | 43051 | 9637.0000 | 0.9818 | 0.1868 | -0.4015 |
| E_TOUCH | NATIVE | TAIL_RISK | BAND_H | REVERSE | 25 | -1.3647 | -0.0413 | 2.5991 | 2 | 0.5636 | 231121.0000 | 43030 | 43027 | 9637.0000 | 0.9848 | 0.1865 | -0.3258 |
| E_TOUCH | NATIVE | TAIL_RISK | BAND_Z | DIRECT | 25 | -15.3993 | 0.4416 | 7.4380 | 2 | 2.1420 | 231121.0000 | 42579 | 42579 | 9637.0000 | 0.9964 | 0.1854 | -0.1778 |
| E_TOUCH | NATIVE | TAIL_RISK | BAND_Z | REVERSE | 25 | -5.6457 | 0.3526 | 31.7218 | 1 | 2.2300 | 231121.0000 | 43160 | 43160 | 9637.0000 | 0.9962 | 0.1860 | -0.1281 |
| E_TOUCH | NATIVE_COMBINATION | LEVEL_FORECAST_K12 | BAND_Z+BAND_H | DIRECT_DIRECT | 25 | -3.2446 | 0.1420 | 31.4104 | 2 | 2.0697 | 231121.0000 | 25168 | 25168 | 9637.0000 | 0.5601 | 0.1090 | -0.0541 |
| E_TOUCH | NATIVE_COMBINATION | LEVEL_FORECAST_K12 | BAND_Z+BAND_H | DIRECT_REVERSE | 25 | -4.4030 | 0.1747 | 30.9804 | 2 | 2.0153 | 231121.0000 | 25247 | 25247 | 9637.0000 | 0.5939 | 0.1092 | -0.0883 |
| E_TOUCH | NATIVE_COMBINATION | LEVEL_FORECAST_K12 | BAND_Z+BAND_H | REVERSE_DIRECT | 25 | -8.2353 | 0.4370 | 13.7550 | 3 | 2.0724 | 231121.0000 | 25662 | 25662 | 9637.0000 | 0.5939 | 0.1113 | -0.0887 |
| E_TOUCH | NATIVE_COMBINATION | LEVEL_FORECAST_K12 | BAND_Z+BAND_H | REVERSE_REVERSE | 25 | -8.8358 | 0.2474 | 13.2277 | 3 | 2.0548 | 231121.0000 | 25613 | 25613 | 9637.0000 | 0.5669 | 0.1110 | -0.2114 |
| E_TOUCH | NATIVE_COMBINATION | LEVEL_FORECAST_K4 | BAND_Z+BAND_H | DIRECT_DIRECT | 25 | -5.3899 | 0.1313 | 37.8644 | 2 | 2.0585 | 231121.0000 | 25388 | 25378 | 9637.0000 | 0.5655 | 0.1099 | -0.0444 |
| E_TOUCH | NATIVE_COMBINATION | LEVEL_FORECAST_K4 | BAND_Z+BAND_H | DIRECT_REVERSE | 25 | -4.8524 | 0.3135 | 37.2418 | 2 | 2.0578 | 231121.0000 | 25438 | 25436 | 9637.0000 | 0.5939 | 0.1101 | -0.0785 |
| E_TOUCH | NATIVE_COMBINATION | LEVEL_FORECAST_K4 | BAND_Z+BAND_H | REVERSE_DIRECT | 25 | -3.8451 | 0.4872 | 7.4035 | 1 | 2.0639 | 231121.0000 | 25508 | 25503 | 9637.0000 | 0.5942 | 0.1105 | 0.0643 |
| E_TOUCH | NATIVE_COMBINATION | LEVEL_FORECAST_K4 | BAND_Z+BAND_H | REVERSE_REVERSE | 25 | -3.6174 | 0.3812 | 10.6694 | 2 | 2.0615 | 231121.0000 | 25423 | 25418 | 9637.0000 | 0.5631 | 0.1101 | -0.0604 |
| E_TOUCH | NATIVE_COMBINATION | LEVEL_NOW | BAND_Z+BAND_H | DIRECT_DIRECT | 25 | -12.8221 | 0.4426 | 14.7448 | 2 | 2.3015 | 231121.0000 | 42385 | 42375 | 9637.0000 | 0.9423 | 0.1834 | -0.2297 |
| E_TOUCH | NATIVE_COMBINATION | LEVEL_NOW | BAND_Z+BAND_H | DIRECT_REVERSE | 25 | -11.9116 | 0.5311 | 14.1223 | 2 | 2.1987 | 231121.0000 | 42475 | 42473 | 9637.0000 | 0.9908 | 0.1839 | -0.0803 |
| E_TOUCH | NATIVE_COMBINATION | LEVEL_NOW | BAND_Z+BAND_H | REVERSE_DIRECT | 25 | -7.9067 | 0.0626 | 23.0567 | 0 | 2.1526 | 231121.0000 | 42685 | 42680 | 9637.0000 | 0.9902 | 0.1846 | -0.3610 |
| E_TOUCH | NATIVE_COMBINATION | LEVEL_NOW | BAND_Z+BAND_H | REVERSE_REVERSE | 25 | -8.4617 | 0.0473 | 23.8783 | 0 | 2.1497 | 231121.0000 | 42576 | 42571 | 9637.0000 | 0.9402 | 0.1843 | -0.2987 |
| E_TOUCH | NATIVE_COMBINATION | RANGE_SCALE | BAND_Z+BAND_H | DIRECT_DIRECT | 25 | -5.4317 | -0.0881 | 4.0032 | 1 | 1.9772 | 231121.0000 | 42307 | 42300 | 9637.0000 | 0.9579 | 0.1848 | -0.1410 |
| E_TOUCH | NATIVE_COMBINATION | RANGE_SCALE | BAND_Z+BAND_H | DIRECT_REVERSE | 25 | -7.2273 | 0.0915 | 4.0843 | 0 | 1.9835 | 231121.0000 | 42381 | 42376 | 9637.0000 | 0.9942 | 0.1844 | -0.3140 |
| E_TOUCH | NATIVE_COMBINATION | RANGE_SCALE | BAND_Z+BAND_H | REVERSE_DIRECT | 25 | -4.7321 | 0.0543 | 36.6308 | 1 | 2.0296 | 231121.0000 | 43364 | 43355 | 9637.0000 | 0.9935 | 0.1880 | -0.3986 |
| E_TOUCH | NATIVE_COMBINATION | RANGE_SCALE | BAND_Z+BAND_H | REVERSE_REVERSE | 25 | -3.7721 | 0.2123 | 47.1952 | 1 | 2.0318 | 231121.0000 | 43261 | 43253 | 9637.0000 | 0.9625 | 0.1865 | -0.3115 |
| E_TOUCH | NATIVE_COMBINATION | SHOCK | BAND_Z+BAND_H | DIRECT_DIRECT | 25 | -8.8977 | 0.3030 | 37.8422 | 1 | 2.0857 | 231121.0000 | 40744 | 40731 | 9637.0000 | 0.9145 | 0.1775 | -0.4944 |
| E_TOUCH | NATIVE_COMBINATION | SHOCK | BAND_Z+BAND_H | DIRECT_REVERSE | 25 | -9.3390 | 0.1948 | 40.5471 | 2 | 2.0901 | 231121.0000 | 40889 | 40888 | 9637.0000 | 0.9949 | 0.1777 | -0.4736 |
| E_TOUCH | NATIVE_COMBINATION | SHOCK | BAND_Z+BAND_H | REVERSE_DIRECT | 25 | -3.4201 | 0.4386 | 18.4677 | 1 | 2.0845 | 231121.0000 | 44655 | 44643 | 9637.0000 | 0.9943 | 0.1934 | -0.4150 |
| E_TOUCH | NATIVE_COMBINATION | SHOCK | BAND_Z+BAND_H | REVERSE_REVERSE | 25 | -3.6289 | 0.1804 | 9.7083 | 0 | 2.0857 | 231121.0000 | 44594 | 44593 | 9637.0000 | 0.9842 | 0.1933 | -0.4595 |
| E_TOUCH | NATIVE_COMBINATION | SWING_GT_CUR | BAND_Z+BAND_H | DIRECT_DIRECT | 25 | -10.6004 | 0.5036 | 10.6807 | 0 | 2.0389 | 231121.0000 | 40501 | 40496 | 9637.0000 | 0.9042 | 0.1771 | -0.0816 |
| E_TOUCH | NATIVE_COMBINATION | SWING_GT_CUR | BAND_Z+BAND_H | DIRECT_REVERSE | 25 | -9.7859 | 0.4649 | 10.0581 | 1 | 2.0388 | 231121.0000 | 40641 | 40633 | 9637.0000 | 0.9501 | 0.1777 | -0.1059 |
| E_TOUCH | NATIVE_COMBINATION | SWING_GT_CUR | BAND_Z+BAND_H | REVERSE_DIRECT | 25 | -6.5750 | 0.7770 | 23.1980 | 2 | 2.0679 | 231121.0000 | 40263 | 40258 | 9637.0000 | 0.9503 | 0.1751 | 0.0814 |
| E_TOUCH | NATIVE_COMBINATION | SWING_GT_CUR | BAND_Z+BAND_H | REVERSE_REVERSE | 25 | -6.4346 | 0.6746 | 26.4639 | 3 | 2.0230 | 231121.0000 | 40174 | 40165 | 9637.0000 | 0.8995 | 0.1745 | 0.0823 |
| E_TOUCH | NATIVE_COMBINATION | SWING_SCALE | BAND_Z+BAND_H | DIRECT_DIRECT | 25 | -4.1860 | -0.0021 | 21.3360 | 1 | 1.9684 | 231121.0000 | 39419 | 39414 | 9637.0000 | 0.8775 | 0.1724 | -0.0298 |
| E_TOUCH | NATIVE_COMBINATION | SWING_SCALE | BAND_Z+BAND_H | DIRECT_REVERSE | 25 | -3.9479 | 0.0957 | 21.3360 | 1 | 1.9822 | 231121.0000 | 39505 | 39500 | 9637.0000 | 0.9483 | 0.1725 | -0.0356 |
| E_TOUCH | NATIVE_COMBINATION | SWING_SCALE | BAND_Z+BAND_H | REVERSE_DIRECT | 25 | -1.8197 | -0.1447 | 21.3360 | 1 | 1.8406 | 231121.0000 | 40771 | 40766 | 9637.0000 | 0.9457 | 0.1792 | -0.3699 |
| E_TOUCH | NATIVE_COMBINATION | SWING_SCALE | BAND_Z+BAND_H | REVERSE_REVERSE | 25 | -2.9143 | -0.1940 | 21.3360 | 2 | 1.9076 | 231121.0000 | 40696 | 40689 | 9637.0000 | 0.9280 | 0.1791 | -0.3689 |
| E_TOUCH | NATIVE_COMBINATION | TAIL_RISK | BAND_Z+BAND_H | DIRECT_DIRECT | 25 | -15.4904 | 0.3911 | 7.3332 | 2 | 2.1394 | 231121.0000 | 42459 | 42450 | 9637.0000 | 0.9478 | 0.1852 | -0.0976 |
| E_TOUCH | NATIVE_COMBINATION | TAIL_RISK | BAND_Z+BAND_H | DIRECT_REVERSE | 25 | -14.6510 | 0.2928 | 7.6996 | 2 | 2.1586 | 231121.0000 | 42552 | 42550 | 9637.0000 | 0.9962 | 0.1853 | -0.0755 |
| E_TOUCH | NATIVE_COMBINATION | TAIL_RISK | BAND_Z+BAND_H | REVERSE_DIRECT | 25 | -6.1775 | 0.3237 | 41.1176 | 1 | 2.2436 | 231121.0000 | 43172 | 43167 | 9637.0000 | 0.9963 | 0.1859 | -0.0990 |
| E_TOUCH | NATIVE_COMBINATION | TAIL_RISK | BAND_Z+BAND_H | REVERSE_REVERSE | 25 | -5.4925 | 0.2696 | 41.8561 | 1 | 2.1550 | 231121.0000 | 43058 | 43053 | 9637.0000 | 0.9519 | 0.1858 | -0.0906 |

#### Per-trade descriptive companion (same lens, `state = ORDER_CREATED`)

ctrader:

| entry_variant | arm_class | rows | gross_mean | gross_med | gross_trim | win_share | wl | be_win | edge | mfe | mae | trades |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E_CLOSE | FIXED_NATIVE | 3 | -0.3118 | -0.4086 | -0.0854 | 0.4908 | 1.0324 | 0.4920 | -0.4089 | 24.4424 | 24.6672 | 7537 |
| E_CLOSE | NATIVE | 96 | -0.2751 | -0.3509 | -0.2106 | 0.4897 | 1.0144 | 0.4964 | -0.3230 | 24.2692 | 24.6720 | 214608 |
| E_CLOSE | NATIVE_COMBINATION | 96 | -0.4260 | -0.4934 | -0.3010 | 0.4854 | 1.0055 | 0.4986 | -0.4822 | 24.1837 | 24.7837 | 213784 |
| E_TOUCH | FIXED_NATIVE | 3 | -0.4111 | 0.0327 | -0.0382 | 0.5000 | 0.9672 | 0.5083 | -0.4423 | 24.4769 | 24.0234 | 8496 |
| E_TOUCH | NATIVE | 96 | -0.0535 | 0.0000 | 0.1212 | 0.4989 | 0.9915 | 0.5021 | -0.1259 | 24.4409 | 23.9713 | 242058 |
| E_TOUCH | NATIVE_COMBINATION | 96 | 0.2256 | 0.0523 | 0.1698 | 0.5002 | 1.0118 | 0.4971 | 0.1860 | 24.4697 | 23.9500 | 241364 |

crypto:

| entry_variant | arm_class | rows | gross_mean | gross_med | gross_trim | win_share | wl | be_win | edge | mfe | mae | trades |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E_CLOSE | FIXED_NATIVE | 25 | -2.5777 | -5.4392 | -5.5734 | 0.4645 | 1.0465 | 0.4886 | -6.1188 | 183.9529 | 173.6289 | 38211 |
| E_CLOSE | NATIVE | 784 | -3.5422 | -5.8190 | -5.8708 | 0.4646 | 1.0505 | 0.4877 | -6.1007 | 163.7519 | 161.3556 | 1075289 |
| E_CLOSE | NATIVE_COMBINATION | 784 | -3.8357 | -6.5672 | -6.4935 | 0.4648 | 1.0527 | 0.4872 | -6.0779 | 164.1329 | 162.6733 | 1069824 |
| E_TOUCH | FIXED_NATIVE | 25 | -2.1183 | -6.6308 | -6.9240 | 0.4727 | 1.0519 | 0.4874 | -4.0282 | 183.1115 | 174.6178 | 43077 |
| E_TOUCH | NATIVE | 784 | -2.0490 | -5.0662 | -4.8270 | 0.4724 | 1.0497 | 0.4879 | -4.1523 | 164.4512 | 163.5476 | 1212965 |
| E_TOUCH | NATIVE_COMBINATION | 784 | -1.1754 | -4.2632 | -4.2421 | 0.4731 | 1.0552 | 0.4866 | -3.2859 | 164.7262 | 162.1611 | 1208804 |

#### Exit-reason mix

Native arms close only on the four-bar hold; device and combination arms show the competing
exits. ctrader (first 37 rows of the grouping; full mix in `per_stratum_estimates.parquet`):

| entry_variant | arm_class | exit_reason | rows |
|---|---|---|---|
| E_CLOSE | FIXED_NATIVE | HOLD=1.000000 | 6 |
| E_CLOSE | MANAGEMENT | HOLD=1.000000 | 33 |
| E_CLOSE | MANAGEMENT | TARGET=1.000000 | 28 |
| E_CLOSE | MANAGEMENT | TRAIL=1.000000 | 21 |
| E_CLOSE | MANAGEMENT | STOP=1.000000 | 19 |
| E_CLOSE | MANAGEMENT_COMPONENT_COMBINATION | HOLD=1.000000 | 27 |
| E_CLOSE | MANAGEMENT_COMPONENT_COMBINATION | STOP=1.000000 | 6 |
| E_CLOSE | MANAGEMENT_COMPONENT_COMBINATION | TRAIL=1.000000 | 5 |
| E_CLOSE | MANAGEMENT_COMPONENT_COMBINATION | TARGET=1.000000 | 4 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.499394|TARGET=0.479097|HOLD=0.021509 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.509309|TARGET=0.472074|HOLD=0.018617 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.511452|TARGET=0.488548 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.518064|TARGET=0.481936 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | TARGET=0.494945|STOP=0.489295|HOLD=0.015760 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | TARGET=0.503052|STOP=0.496948 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | TRAIL=0.719982|HOLD=0.280018 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | TRAIL=0.722210|HOLD=0.277790 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | TRAIL=0.731148|HOLD=0.268852 | 1 |
| E_CLOSE | NATIVE | HOLD=1.000000 | 192 |
| E_CLOSE | NATIVE_COMBINATION | HOLD=1.000000 | 192 |
| E_TOUCH | FIXED_NATIVE | HOLD=1.000000 | 6 |
| E_TOUCH | MANAGEMENT | HOLD=1.000000 | 33 |
| E_TOUCH | MANAGEMENT | STOP=1.000000 | 26 |
| E_TOUCH | MANAGEMENT | TARGET=1.000000 | 21 |
| E_TOUCH | MANAGEMENT | TRAIL=1.000000 | 14 |
| E_TOUCH | MANAGEMENT_COMPONENT_COMBINATION | HOLD=1.000000 | 27 |
| E_TOUCH | MANAGEMENT_COMPONENT_COMBINATION | TRAIL=1.000000 | 6 |
| E_TOUCH | MANAGEMENT_COMPONENT_COMBINATION | TARGET=1.000000 | 5 |
| E_TOUCH | MANAGEMENT_COMPONENT_COMBINATION | STOP=1.000000 | 3 |
| E_TOUCH | MANAGEMENT_DEVICE_COMBINATION | STOP=0.493788|TARGET=0.484930|HOLD=0.021281 | 1 |
| E_TOUCH | MANAGEMENT_DEVICE_COMBINATION | STOP=0.505472|TARGET=0.494528 | 1 |
| E_TOUCH | MANAGEMENT_DEVICE_COMBINATION | TARGET=0.496577|STOP=0.488073|HOLD=0.015350 | 1 |
| E_TOUCH | MANAGEMENT_DEVICE_COMBINATION | TARGET=0.505196|STOP=0.494804 | 1 |
| E_TOUCH | MANAGEMENT_DEVICE_COMBINATION | TRAIL=0.727692|HOLD=0.272308 | 1 |
| E_TOUCH | MANAGEMENT_DEVICE_COMBINATION | TRAIL=0.739989|HOLD=0.260011 | 1 |
| E_TOUCH | NATIVE | HOLD=1.000000 | 192 |
| E_TOUCH | NATIVE_COMBINATION | HOLD=1.000000 | 192 |

crypto (first 60 rows):

| entry_variant | arm_class | exit_reason | rows |
|---|---|---|---|
| E_CLOSE | FIXED_NATIVE | HOLD=1.000000 | 50 |
| E_CLOSE | MANAGEMENT | HOLD=1.000000 | 275 |
| E_CLOSE | MANAGEMENT | TARGET=1.000000 | 253 |
| E_CLOSE | MANAGEMENT | STOP=1.000000 | 215 |
| E_CLOSE | MANAGEMENT | TRAIL=1.000000 | 172 |
| E_CLOSE | MANAGEMENT | STOP=0.750000|FAILSAFE=0.250000 | 1 |
| E_CLOSE | MANAGEMENT | STOP=0.833333|FAILSAFE=0.166667 | 1 |
| E_CLOSE | MANAGEMENT | STOP=0.842105|FAILSAFE=0.157895 | 1 |
| E_CLOSE | MANAGEMENT | STOP=0.846154|FAILSAFE=0.153846 | 1 |
| E_CLOSE | MANAGEMENT | STOP=0.986842|FAILSAFE=0.013158 | 1 |
| E_CLOSE | MANAGEMENT | STOP=0.991453|FAILSAFE=0.008547 | 1 |
| E_CLOSE | MANAGEMENT | STOP=0.996078|FAILSAFE=0.003922 | 1 |
| E_CLOSE | MANAGEMENT | TRAIL=0.986667|FAILSAFE=0.013333 | 1 |
| E_CLOSE | MANAGEMENT | TRAIL=0.989691|FAILSAFE=0.010309 | 1 |
| E_CLOSE | MANAGEMENT | TRAIL=0.992701|FAILSAFE=0.007299 | 1 |
| E_CLOSE | MANAGEMENT_COMPONENT_COMBINATION | HOLD=1.000000 | 225 |
| E_CLOSE | MANAGEMENT_COMPONENT_COMBINATION | TARGET=1.000000 | 69 |
| E_CLOSE | MANAGEMENT_COMPONENT_COMBINATION | TRAIL=1.000000 | 56 |
| E_CLOSE | MANAGEMENT_COMPONENT_COMBINATION | STOP=1.000000 | 48 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.537012|TARGET=0.462988 | 2 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.560403|TARGET=0.439597 | 2 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.567568|TARGET=0.432432 | 2 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.502485|TARGET=0.494773|HOLD=0.002742 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.503172|TARGET=0.496828 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.504317|TARGET=0.495444|HOLD=0.000240 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.504348|TARGET=0.493217|HOLD=0.002435 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.504556|TARGET=0.495444 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.506001|TARGET=0.493999 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.510383|TARGET=0.488244|HOLD=0.001373 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.511050|TARGET=0.487237|HOLD=0.001713 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.511241|TARGET=0.488759 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.512249|TARGET=0.487751 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.512955|TARGET=0.484979|HOLD=0.002065 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.514463|TARGET=0.485537 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.514623|TARGET=0.481017|HOLD=0.004360 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.515634|TARGET=0.481680|HOLD=0.002686 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.517460|TARGET=0.482540 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.517530|TARGET=0.482470 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.518187|TARGET=0.480090|HOLD=0.001724 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.519221|TARGET=0.480779 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.521155|TARGET=0.478016|HOLD=0.000830 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.521818|TARGET=0.478182 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.522375|TARGET=0.473227|HOLD=0.004398 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.523058|TARGET=0.471380|HOLD=0.005563 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.523952|TARGET=0.473465|HOLD=0.002584 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.524799|TARGET=0.475201 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.525050|TARGET=0.474950 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.525227|TARGET=0.469058|HOLD=0.005715 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.526036|TARGET=0.472547|HOLD=0.001417 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.526307|TARGET=0.471777|HOLD=0.001742|FAILSAFE=0.000174 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.526467|TARGET=0.473533 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.526661|TARGET=0.473339 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.527095|TARGET=0.472730|FAILSAFE=0.000174 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.529087|TARGET=0.470913 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.530263|TARGET=0.469357|HOLD=0.000381 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.530263|TARGET=0.469737 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.535704|TARGET=0.460711|HOLD=0.003585 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.536111|TARGET=0.463194|HOLD=0.000694 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.536806|TARGET=0.463194 | 1 |
| E_CLOSE | MANAGEMENT_DEVICE_COMBINATION | STOP=0.538117|TARGET=0.461883 | 1 |

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

| entry_variant | device | setting | component | metric_name | sym | est_min | est_med | est_max | ci_ex0 | mde_med | cfill | cclose | efftr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K12 | decay_bps | 3 | 7.0881 | 7.6681 | 11.6158 | 3 | 1.5354 | 2197 | 2196 | 998 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K12 | holding_efficiency | 3 |  |  |  | 0 |  | 2197 | 2196 | 998 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K12 | opportunity_duration | 3 | 1.1603 | 1.5913 | 1.7704 | 3 | 0.2333 | 2197 | 2196 | 998 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K12 | outcome_by_time_bps | 3 | -1.8724 | -1.7451 | 2.4458 | 2 | 1.7388 | 2197 | 2196 | 998 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K4 | decay_bps | 3 | 6.3292 | 8.9861 | 12.1426 | 3 | 1.9240 | 2257 | 2257 | 1021 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K4 | holding_efficiency | 3 |  |  |  | 1 |  | 2257 | 2257 | 1021 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K4 | opportunity_duration | 3 | 1.3331 | 1.4194 | 1.6438 | 3 | 0.2136 | 2257 | 2257 | 1021 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K4 | outcome_by_time_bps | 3 | -2.1731 | -2.1620 | 1.3412 | 2 | 2.0834 | 2257 | 2257 | 1021 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_NOW | decay_bps | 3 | 5.4708 | 7.9013 | 12.9742 | 3 | 1.4088 | 3834 | 3834 | 1702 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_NOW | holding_efficiency | 3 |  |  |  | 1 |  | 3834 | 3834 | 1702 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_NOW | opportunity_duration | 3 | 1.2865 | 1.4147 | 1.4609 | 3 | 0.1685 | 3834 | 3834 | 1702 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_NOW | outcome_by_time_bps | 3 | -1.7520 | -1.4451 | -1.0890 | 2 | 1.5903 | 3834 | 3834 | 1702 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | SWING_GT_CUR | decay_bps | 3 | 2.5253 | 6.4513 | 9.1518 | 3 | 1.2821 | 4092 | 4091 | 1668 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | SWING_GT_CUR | holding_efficiency | 3 |  |  |  | 0 |  | 4092 | 4091 | 1668 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | SWING_GT_CUR | opportunity_duration | 3 | 0.8962 | 1.1698 | 1.2751 | 3 | 0.1652 | 4092 | 4091 | 1668 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | SWING_GT_CUR | outcome_by_time_bps | 3 | 0.1052 | 0.2048 | 1.8226 | 0 | 1.4548 | 4092 | 4091 | 1668 |
| E_CLOSE | HOLD | STATE_SHOCK_2 | SHOCK | decay_bps | 3 | -10.4860 | -7.6337 | -3.9455 | 3 | 0.8858 | 5047 | 5047 | 1952 |
| E_CLOSE | HOLD | STATE_SHOCK_2 | SHOCK | holding_efficiency | 3 |  |  |  | 1 |  | 5047 | 5047 | 1952 |
| E_CLOSE | HOLD | STATE_SHOCK_2 | SHOCK | opportunity_duration | 3 | -0.9323 | -0.9028 | -0.8640 | 3 | 0.0551 | 5047 | 5047 | 1952 |
| E_CLOSE | HOLD | STATE_SHOCK_2 | SHOCK | outcome_by_time_bps | 3 | -0.1136 | 0.2367 | 0.9367 | 0 | 1.0836 | 5047 | 5047 | 1952 |
| E_CLOSE | SIZE | SCALE_NORMALISED | RANGE_SCALE | concentration | 3 | -0.0014 | 0.0004 | 0.0008 | 1 | 0.0007 | 7537 | 7537 | 1974 |
| E_CLOSE | SIZE | SCALE_NORMALISED | RANGE_SCALE | drawdown_bps | 3 | 114.5473 | 380.5821 | 1491.0761 | 2 | 751.9600 | 7537 | 7537 | 1974 |
| E_CLOSE | SIZE | SCALE_NORMALISED | RANGE_SCALE | risk_dispersion | 3 | -22.0250 | -7.4163 | -0.2830 | 2 | 1.2085 | 7537 | 7537 | 1974 |
| E_CLOSE | SIZE | SCALE_NORMALISED | RANGE_SCALE | tail_loss_bps | 3 | -54.8091 | -13.8279 | 0.1205 | 2 | 7.3420 | 7537 | 7537 | 1974 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K12 | concentration | 3 | 0.0002 | 0.0005 | 0.0008 | 2 | 0.0006 | 7537 | 7537 | 1974 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K12 | drawdown_bps | 3 | 15.2899 | 72.0815 | 260.6647 | 0 | 353.4192 | 7537 | 7537 | 1974 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K12 | risk_dispersion | 3 | -5.7194 | -3.3238 | -2.8981 | 3 | 0.7802 | 7537 | 7537 | 1974 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K12 | tail_loss_bps | 3 | -14.3146 | -7.9529 | -5.5443 | 3 | 5.8324 | 7537 | 7537 | 1974 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K4 | concentration | 3 | 0.0000 | 0.0007 | 0.0008 | 2 | 0.0006 | 7537 | 7537 | 1974 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K4 | drawdown_bps | 3 | 8.7404 | 127.7831 | 632.5338 | 0 | 787.7878 | 7537 | 7537 | 1974 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K4 | risk_dispersion | 3 | -5.8252 | -3.8630 | -2.9373 | 3 | 0.8561 | 7537 | 7537 | 1974 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K4 | tail_loss_bps | 3 | -14.2087 | -11.3308 | -5.4679 | 3 | 5.3035 | 7537 | 7537 | 1974 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | LEVEL_NOW | concentration | 3 | 0.0006 | 0.0014 | 0.0016 | 1 | 0.0017 | 7537 | 7537 | 1974 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | LEVEL_NOW | drawdown_bps | 3 | 99.2190 | 393.1879 | 454.2486 | 0 | 687.3020 | 7537 | 7537 | 1974 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | LEVEL_NOW | risk_dispersion | 3 | -10.9328 | -7.2944 | -3.9576 | 3 | 1.1406 | 7537 | 7537 | 1974 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | LEVEL_NOW | tail_loss_bps | 3 | -25.9987 | -19.5469 | -6.9731 | 3 | 6.7844 | 7537 | 7537 | 1974 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | SHOCK | concentration | 3 | -0.0001 | 0.0005 | 0.0008 | 2 | 0.0003 | 7537 | 7537 | 1974 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | SHOCK | drawdown_bps | 3 | -133.3755 | 126.5733 | 242.8229 | 0 | 321.2540 | 7537 | 7537 | 1974 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | SHOCK | risk_dispersion | 3 | -6.1828 | -3.2875 | -2.8887 | 3 | 0.7729 | 7537 | 7537 | 1974 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | SHOCK | tail_loss_bps | 3 | -20.9998 | -8.2087 | -5.2231 | 3 | 6.5299 | 7537 | 7537 | 1974 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | TAIL_RISK | concentration | 3 | -0.0006 | 0.0002 | 0.0014 | 0 | 0.0008 | 7537 | 7537 | 1974 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | TAIL_RISK | drawdown_bps | 3 | 297.3170 | 517.1208 | 2230.0591 | 2 | 714.4526 | 7537 | 7537 | 1974 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | TAIL_RISK | risk_dispersion | 3 | -27.6208 | -9.4477 | -7.3252 | 3 | 1.1369 | 7537 | 7537 | 1974 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | TAIL_RISK | tail_loss_bps | 3 | -66.2438 | -19.5469 | -17.3116 | 3 | 4.4335 | 7537 | 7537 | 1974 |
| E_CLOSE | STOP | M0.75 | RANGE_SCALE | adverse_excursion_bps | 3 | -0.0528 | 3.0080 | 5.2896 | 2 | 1.6865 | 350 | 348 | 77 |
| E_CLOSE | STOP | M0.75 | RANGE_SCALE | loss_severity_bps | 3 | -4.9911 | -2.7380 | -0.0471 | 2 | 1.6013 | 350 | 348 | 77 |
| E_CLOSE | STOP | M0.75 | RANGE_SCALE | recovery_after_stop_bps | 3 | -1.5004 | 0.0840 | 0.2123 | 0 | 2.7073 | 350 | 348 | 77 |
| E_CLOSE | STOP | M0.75 | RANGE_SCALE | stop_rate | 3 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 350 | 348 | 77 |
| E_CLOSE | STOP | M0.75 | SWING_SCALE | adverse_excursion_bps | 1 | 147.6162 | 147.6162 | 147.6162 | 1 | 9.0803 | 5 | 5 | 5 |
| E_CLOSE | STOP | M0.75 | SWING_SCALE | loss_severity_bps | 1 | -147.9858 | -147.9858 | -147.9858 | 1 | 10.7610 | 5 | 5 | 5 |
| E_CLOSE | STOP | M0.75 | SWING_SCALE | recovery_after_stop_bps | 1 |  |  |  | 0 |  | 5 | 5 | 5 |
| E_CLOSE | STOP | M0.75 | SWING_SCALE | stop_rate | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 5 | 5 | 5 |
| E_CLOSE | STOP | M1.00 | RANGE_SCALE | adverse_excursion_bps | 2 | 3.8444 | 7.6234 | 11.4023 | 2 | 3.4571 | 165 | 165 | 43 |
| E_CLOSE | STOP | M1.00 | RANGE_SCALE | loss_severity_bps | 2 | -11.5090 | -7.5952 | -3.6815 | 2 | 3.9098 | 165 | 165 | 43 |
| E_CLOSE | STOP | M1.00 | RANGE_SCALE | recovery_after_stop_bps | 2 | -1.2640 | 1.4000 | 4.0640 | 0 | 5.6577 | 165 | 165 | 43 |
| E_CLOSE | STOP | M1.00 | RANGE_SCALE | stop_rate | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 165 | 165 | 43 |
| E_CLOSE | STOP | M1.00 | SWING_SCALE | adverse_excursion_bps | 1 | 181.3744 | 181.3744 | 181.3744 | 1 | 14.4893 | 3 | 3 | 3 |
| E_CLOSE | STOP | M1.00 | SWING_SCALE | loss_severity_bps | 1 | -176.0016 | -176.0016 | -176.0016 | 1 | 16.6708 | 3 | 3 | 3 |
| E_CLOSE | STOP | M1.00 | SWING_SCALE | recovery_after_stop_bps | 1 |  |  |  | 0 |  | 3 | 3 | 3 |
| E_CLOSE | STOP | M1.00 | SWING_SCALE | stop_rate | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 3 | 3 | 3 |
| E_CLOSE | STOP | M1.50 | RANGE_SCALE | adverse_excursion_bps | 2 | 4.0086 | 11.9285 | 19.8485 | 2 | 5.7791 | 126 | 125 | 38 |
| E_CLOSE | STOP | M1.50 | RANGE_SCALE | loss_severity_bps | 2 | -17.5594 | -10.5496 | -3.5398 | 2 | 5.3470 | 126 | 125 | 38 |
| E_CLOSE | STOP | M1.50 | RANGE_SCALE | recovery_after_stop_bps | 2 | -1.1628 | 0.5727 | 2.3081 | 0 | 9.9254 | 126 | 125 | 38 |
| E_CLOSE | STOP | M1.50 | RANGE_SCALE | stop_rate | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 126 | 125 | 38 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | adverse_excursion_bps | 2 | -0.1940 | 0.2522 | 0.6983 | 2 | 0.3431 | 444 | 443 | 88 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | loss_severity_bps | 2 | -0.5447 | -0.1817 | 0.1813 | 1 | 0.3546 | 444 | 443 | 88 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | recovery_after_stop_bps | 2 | -0.0993 | 0.0127 | 0.1246 | 0 | 0.9383 | 444 | 443 | 88 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | stop_rate | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 444 | 443 | 88 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | adverse_excursion_bps | 2 | 0.1089 | 0.3527 | 0.5966 | 1 | 0.2643 | 393 | 392 | 77 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | loss_severity_bps | 2 | -0.4417 | -0.2695 | -0.0974 | 1 | 0.3098 | 393 | 392 | 77 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | recovery_after_stop_bps | 2 | 0.0048 | 0.0228 | 0.0407 | 0 | 0.6430 | 393 | 392 | 77 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | stop_rate | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 393 | 392 | 77 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | LEVEL_NOW | adverse_excursion_bps | 2 | 0.5672 | 1.1810 | 1.7949 | 1 | 0.8615 | 328 | 327 | 73 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | LEVEL_NOW | loss_severity_bps | 2 | -1.2585 | -0.9363 | -0.6140 | 1 | 0.7366 | 328 | 327 | 73 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | LEVEL_NOW | recovery_after_stop_bps | 2 | -0.1196 | 0.1914 | 0.5024 | 0 | 2.4056 | 328 | 327 | 73 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | LEVEL_NOW | stop_rate | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 328 | 327 | 73 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | SHOCK | adverse_excursion_bps | 2 | -0.1913 | 0.2709 | 0.7331 | 1 | 0.6074 | 391 | 390 | 83 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | SHOCK | loss_severity_bps | 2 | -0.3073 | -0.0882 | 0.1309 | 0 | 0.5022 | 391 | 390 | 83 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | SHOCK | recovery_after_stop_bps | 2 | -0.4417 | -0.1243 | 0.1932 | 0 | 1.7005 | 391 | 390 | 83 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | SHOCK | stop_rate | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 391 | 390 | 83 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | TAIL_RISK | adverse_excursion_bps | 2 | 0.3970 | 1.9185 | 3.4399 | 1 | 0.8941 | 314 | 313 | 73 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | TAIL_RISK | loss_severity_bps | 2 | -3.1467 | -1.8051 | -0.4635 | 1 | 0.6942 | 314 | 313 | 73 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | TAIL_RISK | recovery_after_stop_bps | 2 | -0.2636 | 0.2906 | 0.8448 | 0 | 2.3576 | 314 | 313 | 73 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | TAIL_RISK | stop_rate | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 314 | 313 | 73 |
| E_CLOSE | TARGET | M0.75 | RANGE_SCALE | missed_excess_bps | 3 | -5.2200 | -1.6376 | -1.5647 | 2 | 3.0029 | 138 | 137 | 38 |
| E_CLOSE | TARGET | M0.75 | RANGE_SCALE | reach_rate | 3 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 138 | 137 | 38 |
| E_CLOSE | TARGET | M0.75 | RANGE_SCALE | realised_capture_bps | 3 | 0.0724 | 2.0022 | 8.1024 | 2 | 1.5938 | 138 | 137 | 38 |
| E_CLOSE | TARGET | M0.75 | RANGE_SCALE | time_to_target | 3 | -0.9051 | -0.0787 | 218.6289 | 1 | 4.1963 | 138 | 137 | 38 |
| E_CLOSE | TARGET | M1.00 | RANGE_SCALE | missed_excess_bps | 3 | -6.6425 | -0.4824 | 2.3328 | 3 | 0.9338 | 98 | 97 | 23 |
| E_CLOSE | TARGET | M1.00 | RANGE_SCALE | reach_rate | 3 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 98 | 97 | 23 |
| E_CLOSE | TARGET | M1.00 | RANGE_SCALE | realised_capture_bps | 3 | -2.9874 | 0.7827 | 7.8484 | 3 | 0.7211 | 98 | 97 | 23 |
| E_CLOSE | TARGET | M1.00 | RANGE_SCALE | time_to_target | 3 | -1.3683 | 1.5685 | 15.8187 | 3 | 1.4376 | 98 | 97 | 23 |
| E_CLOSE | TARGET | M1.50 | RANGE_SCALE | missed_excess_bps | 3 | -1.8140 | -0.9671 | -0.0431 | 2 | 2.5424 | 208 | 207 | 64 |
| E_CLOSE | TARGET | M1.50 | RANGE_SCALE | reach_rate | 3 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 208 | 207 | 64 |
| E_CLOSE | TARGET | M1.50 | RANGE_SCALE | realised_capture_bps | 3 | 1.0905 | 1.3944 | 2.3228 | 2 | 1.0860 | 208 | 207 | 64 |
| E_CLOSE | TARGET | M1.50 | RANGE_SCALE | time_to_target | 3 | 0.1008 | 9.1454 | 28.5816 | 1 | 12.1475 | 208 | 207 | 64 |
| E_CLOSE | TARGET | M1.50 | SWING_SCALE | missed_excess_bps | 1 | -262.0105 | -262.0105 | -262.0105 | 1 |  | 2 | 1 | 1 |
| E_CLOSE | TARGET | M1.50 | SWING_SCALE | reach_rate | 1 | 0.0000 | 0.0000 | 0.0000 | 0 |  | 2 | 1 | 1 |
| E_CLOSE | TARGET | M1.50 | SWING_SCALE | realised_capture_bps | 1 | 296.7014 | 296.7014 | 296.7014 | 1 |  | 2 | 1 | 1 |
| E_CLOSE | TARGET | M1.50 | SWING_SCALE | time_to_target | 1 | 7.6833 | 7.6833 | 7.6833 | 1 |  | 2 | 1 | 1 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | missed_excess_bps | 3 | -0.0774 | 0.0000 | 0.0827 | 1 | 0.0826 | 334 | 332 | 71 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | reach_rate | 3 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 334 | 332 | 71 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | realised_capture_bps | 3 | -0.0001 | 0.0000 | 0.1070 | 0 | 0.1024 | 334 | 332 | 71 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | time_to_target | 3 | -0.0755 | 0.0000 | 0.4569 | 0 | 0.1847 | 334 | 332 | 71 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | missed_excess_bps | 3 | -0.3386 | -0.1226 | 0.0000 | 0 | 0.3668 | 421 | 418 | 97 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | reach_rate | 3 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 421 | 418 | 97 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | realised_capture_bps | 3 | 0.0000 | 0.2515 | 0.4590 | 1 | 0.4016 | 421 | 418 | 97 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | time_to_target | 3 | -2.3150 | 0.0000 | 0.0109 | 0 | 0.0614 | 421 | 418 | 97 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_NOW | missed_excess_bps | 3 | -0.9775 | -0.7686 | 0.0499 | 0 | 0.8073 | 198 | 196 | 56 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_NOW | reach_rate | 3 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 198 | 196 | 56 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_NOW | realised_capture_bps | 3 | 0.2260 | 0.8817 | 1.0383 | 1 | 0.7602 | 198 | 196 | 56 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_NOW | time_to_target | 3 | -4.9768 | 0.1047 | 6.8471 | 1 | 6.9367 | 198 | 196 | 56 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | SHOCK | missed_excess_bps | 3 | -0.8416 | -0.6079 | 0.3009 | 0 | 0.6079 | 182 | 181 | 41 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | SHOCK | reach_rate | 3 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 182 | 181 | 41 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | SHOCK | realised_capture_bps | 3 | -0.1623 | 0.1742 | 0.9510 | 0 | 0.3438 | 182 | 181 | 41 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | SHOCK | time_to_target | 3 | -1.1433 | -0.0307 | 1.4315 | 0 | 1.1433 | 182 | 181 | 41 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | SWING_GT_CUR | missed_excess_bps | 3 | -1.3008 | 0.0000 | 0.2435 | 1 | 0.8275 | 189 | 188 | 41 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | SWING_GT_CUR | reach_rate | 3 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 189 | 188 | 41 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | SWING_GT_CUR | realised_capture_bps | 3 | -0.0729 | 0.0000 | 1.0133 | 1 | 0.8216 | 189 | 188 | 41 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | SWING_GT_CUR | time_to_target | 3 | 0.0000 | 40.3229 | 106.3038 | 1 | 40.2128 | 189 | 188 | 41 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | TAIL_RISK | missed_excess_bps | 3 | -1.5111 | 0.2533 | 1.2315 | 2 | 0.6746 | 143 | 142 | 32 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | TAIL_RISK | reach_rate | 3 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 143 | 142 | 32 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | TAIL_RISK | realised_capture_bps | 3 | -1.8861 | -0.0789 | 2.1962 | 2 | 0.5232 | 143 | 142 | 32 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | TAIL_RISK | time_to_target | 3 | -1.2100 | -0.1395 | 121.7468 | 2 | 1.1800 | 143 | 142 | 32 |
| E_CLOSE | TRAIL | M0.75 | RANGE_SCALE | favourable_excursion_captured | 3 | -0.0901 | -0.0341 | 0.0602 | 0 | 0.1154 | 128 | 127 | 37 |
| E_CLOSE | TRAIL | M0.75 | RANGE_SCALE | loss_tail_bps | 3 | 0.0000 | 0.0800 | 0.1939 | 0 | 0.1939 | 128 | 127 | 37 |
| E_CLOSE | TRAIL | M0.75 | RANGE_SCALE | peak_giveback_bps | 3 | 0.1390 | 1.1441 | 10.9402 | 1 | 1.2015 | 128 | 127 | 37 |
| E_CLOSE | TRAIL | M1.00 | RANGE_SCALE | favourable_excursion_captured | 3 | -0.0486 | 0.0442 | 0.0599 | 1 | 0.0476 | 100 | 99 | 27 |
| E_CLOSE | TRAIL | M1.00 | RANGE_SCALE | loss_tail_bps | 3 | -0.7022 | 0.4037 | 1.8258 | 2 | 0.5889 | 100 | 99 | 27 |
| E_CLOSE | TRAIL | M1.00 | RANGE_SCALE | peak_giveback_bps | 3 | 0.6389 | 0.7154 | 1.0034 | 1 | 1.7869 | 100 | 99 | 27 |
| E_CLOSE | TRAIL | M1.50 | RANGE_SCALE | favourable_excursion_captured | 3 | -0.0408 | 0.0201 | 0.0365 | 0 | 0.0519 | 204 | 204 | 69 |
| E_CLOSE | TRAIL | M1.50 | RANGE_SCALE | loss_tail_bps | 3 | -1.0970 | -0.2578 | 0.3918 | 0 | 0.8155 | 204 | 204 | 69 |
| E_CLOSE | TRAIL | M1.50 | RANGE_SCALE | peak_giveback_bps | 3 | 0.9447 | 2.1839 | 3.6076 | 2 | 1.6817 | 204 | 204 | 69 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | favourable_excursion_captured | 3 | -0.0024 | 0.0000 | 0.0064 | 0 | 0.0060 | 292 | 290 | 62 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | loss_tail_bps | 3 | -0.2497 | 0.0000 | 0.0000 | 0 | 0.0000 | 292 | 290 | 62 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | peak_giveback_bps | 3 | -0.0044 | 0.0000 | 0.0875 | 0 | 0.0875 | 292 | 290 | 62 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | favourable_excursion_captured | 3 | -0.0024 | 0.0000 | 0.0127 | 0 | 0.0060 | 366 | 363 | 84 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | loss_tail_bps | 3 | -0.2497 | 0.0000 | 0.0000 | 0 | 0.0000 | 366 | 363 | 84 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | peak_giveback_bps | 3 | 0.0000 | 0.0875 | 0.5087 | 1 | 0.0875 | 366 | 363 | 84 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_NOW | favourable_excursion_captured | 3 | -0.0627 | -0.0471 | 0.0130 | 1 | 0.0484 | 200 | 198 | 55 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_NOW | loss_tail_bps | 3 | -0.7544 | -0.0100 | 0.0000 | 1 | 0.7998 | 200 | 198 | 55 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_NOW | peak_giveback_bps | 3 | 0.2148 | 1.2218 | 1.7182 | 2 | 0.8976 | 200 | 198 | 55 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150 | SHOCK | favourable_excursion_captured | 3 | -0.0686 | -0.0335 | -0.0138 | 0 | 0.0651 | 115 | 114 | 30 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150 | SHOCK | loss_tail_bps | 3 | -0.7899 | -0.1833 | 0.0000 | 1 | 0.4914 | 115 | 114 | 30 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150 | SHOCK | peak_giveback_bps | 3 | -0.2061 | 1.0124 | 2.2687 | 1 | 0.5963 | 115 | 114 | 30 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K12 | decay_bps | 3 | 4.9834 | 5.1046 | 10.1764 | 3 | 1.4003 | 1944 | 1944 | 855 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K12 | holding_efficiency | 3 | 0.1438 | 0.1438 | 0.1438 | 0 | 0.3508 | 1944 | 1944 | 855 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K12 | opportunity_duration | 3 | 1.0988 | 1.5280 | 1.6077 | 3 | 0.2547 | 1944 | 1944 | 855 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K12 | outcome_by_time_bps | 3 | 0.3790 | 0.7301 | 3.3564 | 0 | 1.6483 | 1944 | 1944 | 855 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K4 | decay_bps | 3 | 5.1336 | 7.9769 | 10.5494 | 3 | 1.7186 | 1991 | 1991 | 879 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K4 | holding_efficiency | 3 |  |  |  | 0 |  | 1991 | 1991 | 879 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K4 | opportunity_duration | 3 | 1.2925 | 1.3925 | 1.5321 | 3 | 0.2346 | 1991 | 1991 | 879 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K4 | outcome_by_time_bps | 3 | -1.4930 | -1.0288 | 2.2273 | 0 | 1.8634 | 1991 | 1991 | 879 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_NOW | decay_bps | 3 | 4.3649 | 7.2298 | 9.9134 | 3 | 1.2371 | 3447 | 3447 | 1482 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_NOW | holding_efficiency | 3 |  |  |  | 0 |  | 3447 | 3447 | 1482 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_NOW | opportunity_duration | 3 | 1.2666 | 1.3252 | 1.4461 | 3 | 0.1790 | 3447 | 3447 | 1482 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_NOW | outcome_by_time_bps | 3 | -0.9805 | -0.4757 | 1.8423 | 0 | 1.5399 | 3447 | 3447 | 1482 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | SWING_GT_CUR | decay_bps | 3 | 2.2386 | 5.0944 | 8.2271 | 3 | 1.1354 | 3918 | 3918 | 1480 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | SWING_GT_CUR | holding_efficiency | 3 | 0.0991 | 0.0991 | 0.0991 | 0 | 0.3755 | 3918 | 3918 | 1480 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | SWING_GT_CUR | opportunity_duration | 3 | 0.7659 | 1.1051 | 1.2152 | 3 | 0.1589 | 3918 | 3918 | 1480 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | SWING_GT_CUR | outcome_by_time_bps | 3 | 0.0252 | 1.2108 | 1.2363 | 0 | 1.3509 | 3918 | 3918 | 1480 |
| E_TOUCH | HOLD | STATE_SHOCK_2 | SHOCK | decay_bps | 3 | -9.2260 | -6.0672 | -4.1351 | 3 | 0.8569 | 4398 | 4398 | 1930 |
| E_TOUCH | HOLD | STATE_SHOCK_2 | SHOCK | holding_efficiency | 3 |  |  |  | 2 |  | 4398 | 4398 | 1930 |
| E_TOUCH | HOLD | STATE_SHOCK_2 | SHOCK | opportunity_duration | 3 | -0.9032 | -0.8916 | -0.8851 | 3 | 0.0625 | 4398 | 4398 | 1930 |
| E_TOUCH | HOLD | STATE_SHOCK_2 | SHOCK | outcome_by_time_bps | 3 | -0.6661 | 0.0004 | 0.5087 | 0 | 1.1801 | 4398 | 4398 | 1930 |
| E_TOUCH | SIZE | SCALE_NORMALISED | RANGE_SCALE | concentration | 3 | -0.0012 | 0.0002 | 0.0006 | 0 | 0.0008 | 8496 | 8496 | 1947 |
| E_TOUCH | SIZE | SCALE_NORMALISED | RANGE_SCALE | drawdown_bps | 3 | 335.1560 | 360.1668 | 2122.7112 | 2 | 594.4671 | 8496 | 8496 | 1947 |
| E_TOUCH | SIZE | SCALE_NORMALISED | RANGE_SCALE | risk_dispersion | 3 | -22.1089 | -7.1676 | -0.2394 | 2 | 1.1786 | 8496 | 8496 | 1947 |
| E_TOUCH | SIZE | SCALE_NORMALISED | RANGE_SCALE | tail_loss_bps | 3 | -51.5494 | -13.6183 | -2.0472 | 2 | 6.3108 | 8496 | 8496 | 1947 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K12 | concentration | 3 | 0.0004 | 0.0007 | 0.0008 | 2 | 0.0003 | 8496 | 8496 | 1947 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K12 | drawdown_bps | 3 | 190.8281 | 280.3218 | 1581.9497 | 0 | 384.1083 | 8496 | 8496 | 1947 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K12 | risk_dispersion | 3 | -5.0618 | -3.3313 | -2.1601 | 3 | 0.6265 | 8496 | 8496 | 1947 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K12 | tail_loss_bps | 3 | -13.5863 | -6.6453 | -4.3291 | 3 | 4.7621 | 8496 | 8496 | 1947 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K4 | concentration | 3 | 0.0006 | 0.0007 | 0.0008 | 2 | 0.0003 | 8496 | 8496 | 1947 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K4 | drawdown_bps | 3 | 16.7529 | 438.2060 | 1010.2673 | 0 | 505.2084 | 8496 | 8496 | 1947 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K4 | risk_dispersion | 3 | -5.3018 | -3.6125 | -2.9390 | 3 | 0.8351 | 8496 | 8496 | 1947 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K4 | tail_loss_bps | 3 | -11.6697 | -6.9644 | -5.7535 | 3 | 5.2123 | 8496 | 8496 | 1947 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | LEVEL_NOW | concentration | 3 | 0.0011 | 0.0012 | 0.0015 | 2 | 0.0007 | 8496 | 8496 | 1947 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | LEVEL_NOW | drawdown_bps | 3 | -174.9699 | 184.6079 | 1750.2600 | 0 | 368.2719 | 8496 | 8496 | 1947 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | LEVEL_NOW | risk_dispersion | 3 | -10.4562 | -6.5886 | -3.9462 | 3 | 1.0726 | 8496 | 8496 | 1947 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | LEVEL_NOW | tail_loss_bps | 3 | -25.1762 | -13.6661 | -7.0659 | 3 | 6.0967 | 8496 | 8496 | 1947 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | SHOCK | concentration | 3 | 0.0004 | 0.0006 | 0.0007 | 3 | 0.0003 | 8496 | 8496 | 1947 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | SHOCK | drawdown_bps | 3 | 123.8774 | 325.7983 | 1249.2231 | 0 | 434.5892 | 8496 | 8496 | 1947 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | SHOCK | risk_dispersion | 3 | -6.5558 | -2.8946 | -2.6125 | 3 | 0.7985 | 8496 | 8496 | 1947 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | SHOCK | tail_loss_bps | 3 | -17.2338 | -7.3731 | -3.9404 | 3 | 4.7358 | 8496 | 8496 | 1947 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | TAIL_RISK | concentration | 3 | -0.0001 | 0.0003 | 0.0011 | 1 | 0.0004 | 8496 | 8496 | 1947 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | TAIL_RISK | drawdown_bps | 3 | 230.5466 | 475.4730 | 2791.5043 | 2 | 381.5412 | 8496 | 8496 | 1947 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | TAIL_RISK | risk_dispersion | 3 | -27.3981 | -9.3625 | -6.6178 | 3 | 1.0752 | 8496 | 8496 | 1947 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | TAIL_RISK | tail_loss_bps | 3 | -65.5424 | -17.6871 | -13.6661 | 3 | 6.1558 | 8496 | 8496 | 1947 |
| E_TOUCH | STOP | M0.75 | RANGE_SCALE | adverse_excursion_bps | 3 | -0.0935 | 1.2311 | 6.1015 | 3 | 1.0900 | 505 | 503 | 92 |
| E_TOUCH | STOP | M0.75 | RANGE_SCALE | loss_severity_bps | 3 | -6.5877 | -1.2571 | 0.1872 | 3 | 1.0787 | 505 | 503 | 92 |
| E_TOUCH | STOP | M0.75 | RANGE_SCALE | recovery_after_stop_bps | 3 | -1.1642 | 0.0330 | 0.8665 | 1 | 2.7184 | 505 | 503 | 92 |
| E_TOUCH | STOP | M0.75 | RANGE_SCALE | stop_rate | 3 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 505 | 503 | 92 |
| E_TOUCH | STOP | M0.75 | SWING_SCALE | adverse_excursion_bps | 1 | 189.2755 | 189.2755 | 189.2755 | 1 | 68.5281 | 3 | 3 | 3 |
| E_TOUCH | STOP | M0.75 | SWING_SCALE | loss_severity_bps | 1 | -190.9560 | -190.9560 | -190.9560 | 1 | 101.1334 | 3 | 3 | 3 |
| E_TOUCH | STOP | M0.75 | SWING_SCALE | recovery_after_stop_bps | 1 |  |  |  | 0 |  | 3 | 3 | 3 |
| E_TOUCH | STOP | M0.75 | SWING_SCALE | stop_rate | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 3 | 3 | 3 |
| E_TOUCH | STOP | M1.00 | RANGE_SCALE | adverse_excursion_bps | 3 | -0.3272 | 2.8690 | 12.4456 | 3 | 3.6703 | 207 | 206 | 42 |
| E_TOUCH | STOP | M1.00 | RANGE_SCALE | loss_severity_bps | 3 | -12.0940 | -2.8344 | 0.3272 | 3 | 3.6088 | 207 | 206 | 42 |
| E_TOUCH | STOP | M1.00 | RANGE_SCALE | recovery_after_stop_bps | 3 | -0.3273 | 0.4384 | 4.9836 | 1 | 5.6265 | 207 | 206 | 42 |
| E_TOUCH | STOP | M1.00 | RANGE_SCALE | stop_rate | 3 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 207 | 206 | 42 |
| E_TOUCH | STOP | M1.50 | RANGE_SCALE | adverse_excursion_bps | 3 | -1.0635 | 3.8423 | 16.0033 | 3 | 6.7710 | 131 | 130 | 32 |
| E_TOUCH | STOP | M1.50 | RANGE_SCALE | loss_severity_bps | 3 | -14.7302 | -3.3548 | 0.4090 | 3 | 6.0118 | 131 | 130 | 32 |
| E_TOUCH | STOP | M1.50 | RANGE_SCALE | recovery_after_stop_bps | 3 | 0.3273 | 1.0857 | 7.3944 | 1 | 12.3096 | 131 | 130 | 32 |
| E_TOUCH | STOP | M1.50 | RANGE_SCALE | stop_rate | 3 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 131 | 130 | 32 |
| E_TOUCH | STOP | M1.50 | SWING_SCALE | adverse_excursion_bps | 1 | 157.2778 | 157.2778 | 157.2778 | 1 | 18.5348 | 2 | 2 | 2 |
| E_TOUCH | STOP | M1.50 | SWING_SCALE | loss_severity_bps | 1 | -159.3472 | -159.3472 | -159.3472 | 1 | 18.7815 | 2 | 2 | 2 |
| E_TOUCH | STOP | M1.50 | SWING_SCALE | recovery_after_stop_bps | 1 |  |  |  | 0 |  | 2 | 2 | 2 |
| E_TOUCH | STOP | M1.50 | SWING_SCALE | stop_rate | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 2 | 2 | 2 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | adverse_excursion_bps | 3 | -0.1234 | -0.0748 | 0.0000 | 0 | 0.2995 | 425 | 423 | 68 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | loss_severity_bps | 3 | 0.0000 | 0.0082 | 0.1464 | 0 | 0.1199 | 425 | 423 | 68 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | recovery_after_stop_bps | 3 | -0.1409 | 0.0000 | 0.9013 | 0 | 0.5870 | 425 | 423 | 68 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | stop_rate | 3 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 425 | 423 | 68 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | adverse_excursion_bps | 3 | -0.1234 | 0.0000 | 0.4154 | 1 | 0.3944 | 488 | 486 | 83 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | loss_severity_bps | 3 | -0.4222 | 0.0000 | 0.1464 | 1 | 0.2834 | 488 | 486 | 83 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | recovery_after_stop_bps | 3 | -0.1409 | -0.0914 | 0.0000 | 0 | 0.8315 | 488 | 486 | 83 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | stop_rate | 3 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 488 | 486 | 83 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | LEVEL_NOW | adverse_excursion_bps | 3 | 0.0000 | 0.4979 | 0.9961 | 0 | 1.1410 | 283 | 281 | 52 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | LEVEL_NOW | loss_severity_bps | 3 | -0.5695 | -0.0646 | 0.0000 | 0 | 0.8515 | 283 | 281 | 52 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | LEVEL_NOW | recovery_after_stop_bps | 3 | -0.1712 | 0.0000 | 1.3100 | 0 | 2.1363 | 283 | 281 | 52 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | LEVEL_NOW | stop_rate | 3 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 283 | 281 | 52 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | SHOCK | adverse_excursion_bps | 3 | 0.0000 | 0.1455 | 0.5505 | 0 | 1.4444 | 255 | 253 | 45 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | SHOCK | loss_severity_bps | 3 | -0.6241 | 0.0000 | 0.0407 | 0 | 0.9546 | 255 | 253 | 45 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | SHOCK | recovery_after_stop_bps | 3 | -0.0451 | 0.0000 | 0.6253 | 0 | 1.4792 | 255 | 253 | 45 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | SHOCK | stop_rate | 3 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 255 | 253 | 45 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | TAIL_RISK | adverse_excursion_bps | 3 | -0.9817 | 0.2696 | 3.4925 | 2 | 1.6854 | 250 | 248 | 47 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | TAIL_RISK | loss_severity_bps | 3 | -2.5461 | 0.1815 | 0.7363 | 2 | 0.9203 | 250 | 248 | 47 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | TAIL_RISK | recovery_after_stop_bps | 3 | -0.7982 | -0.4132 | 1.3092 | 1 | 1.7160 | 250 | 248 | 47 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | TAIL_RISK | stop_rate | 3 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 250 | 248 | 47 |
| E_TOUCH | TARGET | M0.75 | RANGE_SCALE | missed_excess_bps | 2 | -7.5273 | -2.8802 | 1.7670 | 1 | 3.8070 | 95 | 95 | 18 |
| E_TOUCH | TARGET | M0.75 | RANGE_SCALE | reach_rate | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 95 | 95 | 18 |
| E_TOUCH | TARGET | M0.75 | RANGE_SCALE | realised_capture_bps | 2 | 1.6005 | 5.0389 | 8.4773 | 1 | 3.4678 | 95 | 95 | 18 |
| E_TOUCH | TARGET | M0.75 | RANGE_SCALE | time_to_target | 2 | -1.1978 | 7.3398 | 15.8774 | 1 | 9.2445 | 95 | 95 | 18 |
| E_TOUCH | TARGET | M0.75 | SWING_SCALE | missed_excess_bps | 1 | -90.5309 | -90.5309 | -90.5309 | 1 | 18.2796 | 4 | 4 | 3 |
| E_TOUCH | TARGET | M0.75 | SWING_SCALE | reach_rate | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 4 | 4 | 3 |
| E_TOUCH | TARGET | M0.75 | SWING_SCALE | realised_capture_bps | 1 | 165.4053 | 165.4053 | 165.4053 | 1 | 20.7176 | 4 | 4 | 3 |
| E_TOUCH | TARGET | M0.75 | SWING_SCALE | time_to_target | 1 | 378.8417 | 378.8417 | 378.8417 | 1 | 373.4083 | 4 | 4 | 3 |
| E_TOUCH | TARGET | M1.00 | RANGE_SCALE | missed_excess_bps | 2 | 0.2490 | 0.3121 | 0.3753 | 0 | 0.9544 | 119 | 119 | 30 |
| E_TOUCH | TARGET | M1.00 | RANGE_SCALE | reach_rate | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 119 | 119 | 30 |
| E_TOUCH | TARGET | M1.00 | RANGE_SCALE | realised_capture_bps | 2 | -0.0944 | 0.6038 | 1.3021 | 0 | 1.4766 | 119 | 119 | 30 |
| E_TOUCH | TARGET | M1.00 | RANGE_SCALE | time_to_target | 2 | -142.8716 | -70.6079 | 1.6557 | 1 | 172.8158 | 119 | 119 | 30 |
| E_TOUCH | TARGET | M1.50 | RANGE_SCALE | missed_excess_bps | 2 | -0.3103 | 0.1748 | 0.6599 | 0 | 1.1097 | 41 | 41 | 11 |
| E_TOUCH | TARGET | M1.50 | RANGE_SCALE | reach_rate | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 41 | 41 | 11 |
| E_TOUCH | TARGET | M1.50 | RANGE_SCALE | realised_capture_bps | 2 | -1.5623 | 0.0598 | 1.6818 | 1 | 3.9251 | 41 | 41 | 11 |
| E_TOUCH | TARGET | M1.50 | RANGE_SCALE | time_to_target | 2 | -1.7708 | 9.4700 | 20.7109 | 1 | 13.1769 | 41 | 41 | 11 |
| E_TOUCH | TARGET | M1.50 | SWING_SCALE | missed_excess_bps | 2 | -262.0105 | -132.7131 | -3.4156 | 2 |  | 2 | 2 | 2 |
| E_TOUCH | TARGET | M1.50 | SWING_SCALE | reach_rate | 2 | 0.0000 | 0.0000 | 0.0000 | 0 |  | 2 | 2 | 2 |
| E_TOUCH | TARGET | M1.50 | SWING_SCALE | realised_capture_bps | 2 | 239.6401 | 268.1707 | 296.7014 | 2 |  | 2 | 2 | 2 |
| E_TOUCH | TARGET | M1.50 | SWING_SCALE | time_to_target | 2 | 7.6833 | 364.6833 | 721.6833 | 2 |  | 2 | 2 | 2 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | missed_excess_bps | 2 | -0.5020 | -0.3029 | -0.1038 | 1 | 0.4373 | 438 | 437 | 83 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | reach_rate | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 438 | 437 | 83 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | realised_capture_bps | 2 | 0.1111 | 0.3384 | 0.5658 | 1 | 0.4414 | 438 | 437 | 83 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | time_to_target | 2 | -2.5713 | -1.1611 | 0.2492 | 0 | 2.6265 | 438 | 437 | 83 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | missed_excess_bps | 2 | -0.3374 | -0.0080 | 0.3214 | 0 | 0.4777 | 414 | 414 | 76 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | reach_rate | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 414 | 414 | 76 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | realised_capture_bps | 2 | 0.1494 | 0.2805 | 0.4115 | 0 | 0.4417 | 414 | 414 | 76 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | time_to_target | 2 | -2.5752 | -0.8811 | 0.8130 | 1 | 2.7613 | 414 | 414 | 76 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_NOW | missed_excess_bps | 2 | -0.8462 | -0.8443 | -0.8424 | 0 | 1.0586 | 154 | 154 | 32 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_NOW | reach_rate | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 154 | 154 | 32 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_NOW | realised_capture_bps | 2 | 0.6589 | 1.1310 | 1.6032 | 1 | 1.0172 | 154 | 154 | 32 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_NOW | time_to_target | 2 | -10.0244 | 0.7420 | 11.5085 | 2 | 17.0458 | 154 | 154 | 32 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | SHOCK | missed_excess_bps | 2 | -1.0064 | -0.7131 | -0.4198 | 0 | 0.4992 | 28 | 28 | 5 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | SHOCK | reach_rate | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 28 | 28 | 5 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | SHOCK | realised_capture_bps | 2 | -0.0139 | 0.5567 | 1.1272 | 0 | 0.5682 | 28 | 28 | 5 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | SHOCK | time_to_target | 2 | -3.8750 | -2.5108 | -1.1467 | 0 | 5.4397 | 28 | 28 | 5 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | SWING_GT_CUR | missed_excess_bps | 2 | -0.8934 | -0.8247 | -0.7560 | 1 | 0.9993 | 214 | 213 | 41 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | SWING_GT_CUR | reach_rate | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 214 | 213 | 41 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | SWING_GT_CUR | realised_capture_bps | 2 | 0.7745 | 1.0237 | 1.2730 | 1 | 0.9233 | 214 | 213 | 41 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | SWING_GT_CUR | time_to_target | 2 | 0.3494 | 29.6513 | 58.9532 | 1 | 29.5238 | 214 | 213 | 41 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | TAIL_RISK | missed_excess_bps | 2 | -1.9955 | -0.2592 | 1.4771 | 2 | 0.4831 | 179 | 178 | 35 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | TAIL_RISK | reach_rate | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 179 | 178 | 35 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | TAIL_RISK | realised_capture_bps | 2 | -1.8848 | 0.4786 | 2.8420 | 2 | 0.3540 | 179 | 178 | 35 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | TAIL_RISK | time_to_target | 2 | -0.6229 | 15.6578 | 31.9385 | 1 | 60.4971 | 179 | 178 | 35 |
| E_TOUCH | TRAIL | M0.75 | RANGE_SCALE | favourable_excursion_captured | 2 | -0.0493 | -0.0161 | 0.0172 | 0 | 0.2306 | 125 | 125 | 21 |
| E_TOUCH | TRAIL | M0.75 | RANGE_SCALE | loss_tail_bps | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0343 | 125 | 125 | 21 |
| E_TOUCH | TRAIL | M0.75 | RANGE_SCALE | peak_giveback_bps | 2 | 1.2148 | 5.3078 | 9.4007 | 1 | 3.2601 | 125 | 125 | 21 |
| E_TOUCH | TRAIL | M1.00 | RANGE_SCALE | favourable_excursion_captured | 2 | -0.0112 | -0.0009 | 0.0093 | 0 | 0.0787 | 69 | 69 | 15 |
| E_TOUCH | TRAIL | M1.00 | RANGE_SCALE | loss_tail_bps | 2 | 0.0249 | 0.1410 | 0.2570 | 0 | 0.7400 | 69 | 69 | 15 |
| E_TOUCH | TRAIL | M1.00 | RANGE_SCALE | peak_giveback_bps | 2 | 3.1903 | 4.1397 | 5.0891 | 1 | 3.5475 | 69 | 69 | 15 |
| E_TOUCH | TRAIL | M1.50 | RANGE_SCALE | favourable_excursion_captured | 2 | -0.0517 | 0.0688 | 0.1893 | 2 | 0.1048 | 105 | 105 | 33 |
| E_TOUCH | TRAIL | M1.50 | RANGE_SCALE | loss_tail_bps | 2 | -0.7261 | 0.6918 | 2.1097 | 1 | 1.1991 | 105 | 105 | 33 |
| E_TOUCH | TRAIL | M1.50 | RANGE_SCALE | peak_giveback_bps | 2 | 1.2991 | 2.5461 | 3.7930 | 1 | 2.3370 | 105 | 105 | 33 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | favourable_excursion_captured | 2 | -0.0039 | -0.0037 | -0.0035 | 0 | 0.0079 | 350 | 350 | 52 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | loss_tail_bps | 2 | -0.2680 | -0.1340 | 0.0000 | 0 | 0.2551 | 350 | 350 | 52 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | peak_giveback_bps | 2 | 0.1148 | 0.1262 | 0.1376 | 0 | 0.1262 | 350 | 350 | 52 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | favourable_excursion_captured | 2 | -0.0029 | -0.0013 | 0.0002 | 0 | 0.0045 | 350 | 350 | 52 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | loss_tail_bps | 2 | -0.2126 | -0.1063 | 0.0000 | 0 | 0.2641 | 350 | 350 | 52 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | peak_giveback_bps | 2 | 0.0971 | 0.1015 | 0.1060 | 0 | 0.1015 | 350 | 350 | 52 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_NOW | favourable_excursion_captured | 2 | -0.0548 | -0.0274 | 0.0000 | 1 | 0.0700 | 114 | 113 | 17 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_NOW | loss_tail_bps | 2 | -0.6256 | -0.3128 | 0.0000 | 1 | 1.0455 | 114 | 113 | 17 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_NOW | peak_giveback_bps | 2 | 1.4404 | 1.5131 | 1.5857 | 2 | 1.3741 | 114 | 113 | 17 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150 | SHOCK | favourable_excursion_captured | 2 | -0.0420 | -0.0410 | -0.0400 | 1 | 0.0400 | 276 | 275 | 38 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150 | SHOCK | loss_tail_bps | 2 | -0.5429 | -0.4700 | -0.3972 | 2 | 0.4105 | 276 | 275 | 38 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150 | SHOCK | peak_giveback_bps | 2 | 0.5394 | 1.2190 | 1.8986 | 1 | 0.8780 | 276 | 275 | 38 |

#### crypto individual devices (314 rows)

| entry_variant | device | setting | component | metric_name | sym | est_min | est_med | est_max | ci_ex0 | mde_med | cfill | cclose | efftr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K12 | decay_bps | 25 | 0.0000 | 38.4376 | 141.6551 | 24 | 12.2987 | 11137 | 11135 | 4783 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K12 | holding_efficiency | 25 | -1.2389 | -0.6380 | -0.1214 | 5 | 1.1492 | 11137 | 11135 | 4783 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K12 | opportunity_duration | 25 | 0.0000 | 1.0316 | 1.6296 | 24 | 0.2385 | 11137 | 11135 | 4783 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K12 | outcome_by_time_bps | 25 | -67.4714 | 1.6581 | 12.9578 | 2 | 16.7634 | 11137 | 11135 | 4783 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K4 | decay_bps | 25 | 12.5063 | 39.4862 | 131.1634 | 25 | 11.9682 | 11109 | 11106 | 4754 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K4 | holding_efficiency | 25 | -0.6856 | 0.0856 | 0.0913 | 4 | 1.0835 | 11109 | 11106 | 4754 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K4 | opportunity_duration | 25 | 0.0824 | 1.0863 | 1.6778 | 23 | 0.2240 | 11109 | 11106 | 4754 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K4 | outcome_by_time_bps | 25 | -42.3834 | 1.5105 | 13.8453 | 2 | 17.3267 | 11109 | 11106 | 4754 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_NOW | decay_bps | 25 | 16.6331 | 39.8632 | 162.2840 | 24 | 9.4667 | 18692 | 18689 | 7954 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_NOW | holding_efficiency | 25 | -16.0977 | -0.2557 | 0.0383 | 5 | 0.7093 | 18692 | 18689 | 7954 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_NOW | opportunity_duration | 25 | 0.4557 | 0.9999 | 1.5286 | 25 | 0.1727 | 18692 | 18689 | 7954 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_NOW | outcome_by_time_bps | 25 | -75.3480 | 0.1617 | 19.0394 | 0 | 12.0690 | 18692 | 18689 | 7954 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | SWING_GT_CUR | decay_bps | 25 | 20.0306 | 34.1543 | 1040.4229 | 25 | 8.4840 | 17488 | 17483 | 7449 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | SWING_GT_CUR | holding_efficiency | 25 | -1.5656 | -0.1942 | 1.0673 | 6 | 0.7625 | 17488 | 17483 | 7449 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | SWING_GT_CUR | opportunity_duration | 25 | 0.5724 | 0.9352 | 2.8924 | 24 | 0.1850 | 17488 | 17483 | 7449 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | SWING_GT_CUR | outcome_by_time_bps | 25 | -78.0058 | 1.6963 | 382.5070 | 1 | 10.8233 | 17488 | 17483 | 7449 |
| E_CLOSE | HOLD | STATE_SHOCK_2 | SHOCK | decay_bps | 25 | -153.6083 | -48.9349 | -21.3460 | 25 | 7.2941 | 25064 | 25063 | 9551 |
| E_CLOSE | HOLD | STATE_SHOCK_2 | SHOCK | holding_efficiency | 25 | -0.7844 | 0.1292 | 0.6254 | 4 | 1.3143 | 25064 | 25063 | 9551 |
| E_CLOSE | HOLD | STATE_SHOCK_2 | SHOCK | opportunity_duration | 25 | -0.9659 | -0.8509 | -0.6442 | 25 | 0.0663 | 25064 | 25063 | 9551 |
| E_CLOSE | HOLD | STATE_SHOCK_2 | SHOCK | outcome_by_time_bps | 25 | -46.9725 | 0.1324 | 22.3296 | 3 | 8.7228 | 25064 | 25063 | 9551 |
| E_CLOSE | SIZE | SCALE_NORMALISED | RANGE_SCALE | concentration | 25 | -0.0205 | -0.0004 | 0.0248 | 1 | 0.0037 | 38212 | 38211 | 9636 |
| E_CLOSE | SIZE | SCALE_NORMALISED | RANGE_SCALE | drawdown_bps | 25 | -3658.9816 | 1371.2813 | 7368.4571 | 0 | 4801.0384 | 38212 | 38211 | 9636 |
| E_CLOSE | SIZE | SCALE_NORMALISED | RANGE_SCALE | risk_dispersion | 25 | -270.4773 | 2.7872 | 58.3978 | 13 | 30.9826 | 38212 | 38211 | 9636 |
| E_CLOSE | SIZE | SCALE_NORMALISED | RANGE_SCALE | tail_loss_bps | 25 | -548.8080 | -4.1991 | 85.1927 | 9 | 50.8596 | 38212 | 38211 | 9636 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K12 | concentration | 25 | -0.0148 | 0.0009 | 0.0097 | 11 | 0.0012 | 38212 | 38211 | 9636 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K12 | drawdown_bps | 25 | -1569.4793 | 553.6415 | 5570.7338 | 2 | 2113.8486 | 38212 | 38211 | 9636 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K12 | risk_dispersion | 25 | -111.0623 | -20.4353 | -2.1626 | 24 | 7.8877 | 38212 | 38211 | 9636 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K12 | tail_loss_bps | 25 | -265.4321 | -31.5749 | 0.0000 | 19 | 36.9493 | 38212 | 38211 | 9636 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K4 | concentration | 25 | -0.0136 | 0.0012 | 0.0107 | 12 | 0.0019 | 38212 | 38211 | 9636 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K4 | drawdown_bps | 25 | -818.8754 | 1308.3240 | 6927.5875 | 3 | 2304.4463 | 38212 | 38211 | 9636 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K4 | risk_dispersion | 25 | -131.4778 | -24.4488 | -11.0218 | 25 | 8.4350 | 38212 | 38211 | 9636 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K4 | tail_loss_bps | 25 | -434.2814 | -35.6374 | 0.0000 | 19 | 33.3275 | 38212 | 38211 | 9636 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | LEVEL_NOW | concentration | 25 | -0.0113 | 0.0022 | 0.0236 | 6 | 0.0045 | 38212 | 38211 | 9636 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | LEVEL_NOW | drawdown_bps | 25 | -148.1541 | 2928.7772 | 8725.1393 | 11 | 3076.6725 | 38212 | 38211 | 9636 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | LEVEL_NOW | risk_dispersion | 25 | -163.5535 | -55.8385 | -26.5104 | 25 | 15.8826 | 38212 | 38211 | 9636 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | LEVEL_NOW | tail_loss_bps | 25 | -522.2609 | -93.7023 | -45.4677 | 22 | 45.8212 | 38212 | 38211 | 9636 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | SHOCK | concentration | 25 | -0.0157 | 0.0007 | 0.0163 | 7 | 0.0015 | 38212 | 38211 | 9636 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | SHOCK | drawdown_bps | 25 | -381.3842 | 1587.4388 | 7375.0005 | 3 | 2813.1220 | 38212 | 38211 | 9636 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | SHOCK | risk_dispersion | 25 | -130.7714 | -26.8950 | -6.3278 | 24 | 9.7667 | 38212 | 38211 | 9636 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | SHOCK | tail_loss_bps | 25 | -466.8815 | -51.0193 | 0.0000 | 19 | 42.4499 | 38212 | 38211 | 9636 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | TAIL_RISK | concentration | 25 | -0.0119 | 0.0018 | 0.0132 | 5 | 0.0040 | 38212 | 38211 | 9636 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | TAIL_RISK | drawdown_bps | 25 | 221.5757 | 2508.1002 | 9379.6941 | 11 | 2900.3137 | 38212 | 38211 | 9636 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | TAIL_RISK | risk_dispersion | 25 | -347.4573 | -51.7655 | -23.3056 | 25 | 16.2407 | 38212 | 38211 | 9636 |
| E_CLOSE | SIZE | STATE_HALVE_HIGH | TAIL_RISK | tail_loss_bps | 25 | -522.2609 | -99.2529 | -50.5360 | 23 | 44.7931 | 38212 | 38211 | 9636 |
| E_CLOSE | STOP | M0.75 | RANGE_SCALE | adverse_excursion_bps | 25 | -11.4507 | 11.2734 | 189.6035 | 15 | 10.4458 | 3035 | 3023 | 658 |
| E_CLOSE | STOP | M0.75 | RANGE_SCALE | loss_severity_bps | 25 | -145.0911 | -13.0892 | 6.2309 | 16 | 7.3720 | 3035 | 3023 | 658 |
| E_CLOSE | STOP | M0.75 | RANGE_SCALE | recovery_after_stop_bps | 25 | -648.2439 | -5.9901 | 41.8306 | 5 | 18.8855 | 3035 | 3023 | 658 |
| E_CLOSE | STOP | M0.75 | RANGE_SCALE | stop_rate | 25 | -0.0119 | 0.0000 | 0.0000 | 0 | 0.0000 | 3035 | 3023 | 658 |
| E_CLOSE | STOP | M0.75 | SWING_SCALE | adverse_excursion_bps | 9 | 373.6174 | 653.8633 | 2569.1906 | 9 | 145.9780 | 42 | 38 | 33 |
| E_CLOSE | STOP | M0.75 | SWING_SCALE | loss_severity_bps | 9 | -1373.3681 | -645.2442 | -276.3856 | 9 | 136.2141 | 42 | 38 | 33 |
| E_CLOSE | STOP | M0.75 | SWING_SCALE | recovery_after_stop_bps | 9 | -135.7481 | 14.4168 | 264.9454 | 3 | 54.0989 | 42 | 38 | 33 |
| E_CLOSE | STOP | M0.75 | SWING_SCALE | stop_rate | 9 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 42 | 38 | 33 |
| E_CLOSE | STOP | M1.00 | RANGE_SCALE | adverse_excursion_bps | 25 | -176.4657 | 17.8010 | 248.5391 | 17 | 14.7687 | 2127 | 2110 | 520 |
| E_CLOSE | STOP | M1.00 | RANGE_SCALE | loss_severity_bps | 25 | -190.1106 | -17.2926 | 12.9678 | 18 | 8.8964 | 2127 | 2110 | 520 |
| E_CLOSE | STOP | M1.00 | RANGE_SCALE | recovery_after_stop_bps | 25 | -134.6567 | -7.3032 | 71.8984 | 2 | 26.9764 | 2127 | 2110 | 520 |
| E_CLOSE | STOP | M1.00 | RANGE_SCALE | stop_rate | 25 | -0.5000 | 0.0000 | 0.0000 | 0 | 0.0000 | 2127 | 2110 | 520 |
| E_CLOSE | STOP | M1.00 | SWING_SCALE | adverse_excursion_bps | 7 | 414.3948 | 677.5417 | 1645.1722 | 7 | 530.9990 | 11 | 10 | 9 |
| E_CLOSE | STOP | M1.00 | SWING_SCALE | loss_severity_bps | 7 | -1452.1922 | -677.5417 | -353.3981 | 7 | 387.6877 | 11 | 10 | 9 |
| E_CLOSE | STOP | M1.00 | SWING_SCALE | recovery_after_stop_bps | 7 |  |  |  | 0 |  | 11 | 10 | 9 |
| E_CLOSE | STOP | M1.00 | SWING_SCALE | stop_rate | 7 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 11 | 10 | 9 |
| E_CLOSE | STOP | M1.50 | RANGE_SCALE | adverse_excursion_bps | 25 | -339.8510 | 53.5364 | 422.6849 | 22 | 24.6989 | 1071 | 1063 | 345 |
| E_CLOSE | STOP | M1.50 | RANGE_SCALE | loss_severity_bps | 25 | -437.4780 | -39.5789 | 0.4094 | 22 | 23.0779 | 1071 | 1063 | 345 |
| E_CLOSE | STOP | M1.50 | RANGE_SCALE | recovery_after_stop_bps | 25 | -110.2406 | -3.2485 | 62.4843 | 3 | 58.2708 | 1071 | 1063 | 345 |
| E_CLOSE | STOP | M1.50 | RANGE_SCALE | stop_rate | 25 | -1.0000 | 0.0000 | 0.0000 | 1 | 0.0000 | 1071 | 1063 | 345 |
| E_CLOSE | STOP | M1.50 | SWING_SCALE | adverse_excursion_bps | 6 | 460.7186 | 845.3926 | 2699.7389 | 6 | 149.7603 | 13 | 12 | 12 |
| E_CLOSE | STOP | M1.50 | SWING_SCALE | loss_severity_bps | 6 | -2746.7363 | -801.9534 | -457.4929 | 6 | 175.7010 | 13 | 12 | 12 |
| E_CLOSE | STOP | M1.50 | SWING_SCALE | recovery_after_stop_bps | 6 |  |  |  | 0 |  | 13 | 12 | 12 |
| E_CLOSE | STOP | M1.50 | SWING_SCALE | stop_rate | 6 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 13 | 12 | 12 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | adverse_excursion_bps | 25 | -22.2386 | 0.1349 | 16.3496 | 2 | 2.0105 | 3998 | 3979 | 825 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | loss_severity_bps | 25 | -8.4240 | -0.3167 | 13.9194 | 2 | 2.1845 | 3998 | 3979 | 825 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | recovery_after_stop_bps | 25 | -7.8319 | 0.0000 | 18.6946 | 1 | 2.6528 | 3998 | 3979 | 825 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | stop_rate | 25 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 3998 | 3979 | 825 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | adverse_excursion_bps | 25 | -12.6603 | 0.8826 | 23.5116 | 3 | 2.3200 | 4055 | 4037 | 843 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | loss_severity_bps | 25 | -11.1383 | -1.6004 | 6.4097 | 2 | 2.4450 | 4055 | 4037 | 843 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | recovery_after_stop_bps | 25 | -8.2511 | 0.0000 | 5.7188 | 1 | 2.9416 | 4055 | 4037 | 843 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | stop_rate | 25 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 4055 | 4037 | 843 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | LEVEL_NOW | adverse_excursion_bps | 25 | -9.1122 | 3.6123 | 23.5116 | 6 | 9.5297 | 2490 | 2474 | 555 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | LEVEL_NOW | loss_severity_bps | 25 | -12.4019 | -4.9812 | 8.2818 | 6 | 6.5221 | 2490 | 2474 | 555 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | LEVEL_NOW | recovery_after_stop_bps | 25 | -37.0360 | -2.7491 | 27.0067 | 2 | 14.7432 | 2490 | 2474 | 555 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | LEVEL_NOW | stop_rate | 25 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 2490 | 2474 | 555 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | SHOCK | adverse_excursion_bps | 25 | -12.5830 | -3.0584 | 34.9170 | 7 | 6.7366 | 2872 | 2859 | 610 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | SHOCK | loss_severity_bps | 25 | -24.9810 | 2.3962 | 19.2933 | 8 | 4.5704 | 2872 | 2859 | 610 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | SHOCK | recovery_after_stop_bps | 25 | -49.3617 | 0.7846 | 18.2524 | 2 | 11.7549 | 2872 | 2859 | 610 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | SHOCK | stop_rate | 25 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 2872 | 2859 | 610 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | TAIL_RISK | adverse_excursion_bps | 25 | -31.4143 | 5.2816 | 28.8441 | 12 | 10.9145 | 2318 | 2303 | 504 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | TAIL_RISK | loss_severity_bps | 25 | -34.2739 | -4.0228 | 21.1638 | 11 | 8.2231 | 2318 | 2303 | 504 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | TAIL_RISK | recovery_after_stop_bps | 25 | -40.7724 | -0.3524 | 176.2167 | 4 | 15.5528 | 2318 | 2303 | 504 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150 | TAIL_RISK | stop_rate | 25 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 2318 | 2303 | 504 |
| E_CLOSE | TARGET | M0.75 | RANGE_SCALE | missed_excess_bps | 25 | -155.5140 | -12.9693 | 4.8580 | 13 | 11.2467 | 1571 | 1558 | 363 |
| E_CLOSE | TARGET | M0.75 | RANGE_SCALE | reach_rate | 25 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 1571 | 1558 | 363 |
| E_CLOSE | TARGET | M0.75 | RANGE_SCALE | realised_capture_bps | 25 | 0.5739 | 25.0699 | 218.1241 | 21 | 10.3391 | 1571 | 1558 | 363 |
| E_CLOSE | TARGET | M0.75 | RANGE_SCALE | time_to_target | 25 | -10.6610 | 0.9452 | 367.9758 | 17 | 2.5599 | 1571 | 1558 | 363 |
| E_CLOSE | TARGET | M0.75 | SWING_SCALE | missed_excess_bps | 10 | -704.9381 | -71.2712 | 118.3046 | 8 | 107.4341 | 47 | 42 | 32 |
| E_CLOSE | TARGET | M0.75 | SWING_SCALE | reach_rate | 10 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 47 | 42 | 32 |
| E_CLOSE | TARGET | M0.75 | SWING_SCALE | realised_capture_bps | 10 | 249.8228 | 680.6068 | 1999.7254 | 10 | 132.6744 | 47 | 42 | 32 |
| E_CLOSE | TARGET | M0.75 | SWING_SCALE | time_to_target | 10 | 37.2667 | 271.3856 | 1399.2600 | 10 | 565.3429 | 47 | 42 | 32 |
| E_CLOSE | TARGET | M1.00 | RANGE_SCALE | missed_excess_bps | 25 | -231.6936 | -18.1097 | 33.3305 | 19 | 18.0440 | 1036 | 1026 | 271 |
| E_CLOSE | TARGET | M1.00 | RANGE_SCALE | reach_rate | 25 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 1036 | 1026 | 271 |
| E_CLOSE | TARGET | M1.00 | RANGE_SCALE | realised_capture_bps | 25 | -51.3535 | 33.0521 | 307.8563 | 23 | 15.6382 | 1036 | 1026 | 271 |
| E_CLOSE | TARGET | M1.00 | RANGE_SCALE | time_to_target | 25 | -18.5333 | 2.9611 | 678.1278 | 17 | 3.5259 | 1036 | 1026 | 271 |
| E_CLOSE | TARGET | M1.00 | SWING_SCALE | missed_excess_bps | 9 | -912.6419 | -129.8363 | 183.8735 | 5 | 111.0312 | 28 | 27 | 18 |
| E_CLOSE | TARGET | M1.00 | SWING_SCALE | reach_rate | 9 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 28 | 27 | 18 |
| E_CLOSE | TARGET | M1.00 | SWING_SCALE | realised_capture_bps | 9 | 408.3199 | 876.1070 | 2665.1085 | 9 | 256.5013 | 28 | 27 | 18 |
| E_CLOSE | TARGET | M1.00 | SWING_SCALE | time_to_target | 9 | 8.6167 | 380.9000 | 4212.1833 | 9 | 250.4375 | 28 | 27 | 18 |
| E_CLOSE | TARGET | M1.50 | RANGE_SCALE | missed_excess_bps | 25 | -184.2140 | -19.1190 | 1.7479 | 16 | 17.6889 | 761 | 748 | 232 |
| E_CLOSE | TARGET | M1.50 | RANGE_SCALE | reach_rate | 25 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 761 | 748 | 232 |
| E_CLOSE | TARGET | M1.50 | RANGE_SCALE | realised_capture_bps | 25 | -78.3358 | 48.1045 | 457.7258 | 18 | 13.7027 | 761 | 748 | 232 |
| E_CLOSE | TARGET | M1.50 | RANGE_SCALE | time_to_target | 25 | -18.5500 | 2.6056 | 813.9633 | 16 | 2.9387 | 761 | 748 | 232 |
| E_CLOSE | TARGET | M1.50 | SWING_SCALE | missed_excess_bps | 9 | -694.8919 | -272.5929 | 1205.4753 | 7 | 201.2207 | 19 | 17 | 15 |
| E_CLOSE | TARGET | M1.50 | SWING_SCALE | reach_rate | 9 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 19 | 17 | 15 |
| E_CLOSE | TARGET | M1.50 | SWING_SCALE | realised_capture_bps | 9 | 621.5109 | 1266.1262 | 9779.1072 | 9 | 158.0165 | 19 | 17 | 15 |
| E_CLOSE | TARGET | M1.50 | SWING_SCALE | time_to_target | 9 | 8.7000 | 240.1472 | 6843.1333 | 9 | 193.0444 | 19 | 17 | 15 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | missed_excess_bps | 25 | -16.4802 | 0.0000 | 5.5550 | 3 | 0.9364 | 2707 | 2690 | 593 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | reach_rate | 25 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 2707 | 2690 | 593 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | realised_capture_bps | 25 | -9.7698 | 0.0000 | 16.4802 | 3 | 1.0584 | 2707 | 2690 | 593 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | time_to_target | 25 | -0.9880 | 0.0000 | 12.3880 | 1 | 0.0700 | 2707 | 2690 | 593 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | missed_excess_bps | 25 | -21.4397 | -0.2672 | 9.0633 | 4 | 2.4147 | 2741 | 2724 | 602 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | reach_rate | 25 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 2741 | 2724 | 602 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | realised_capture_bps | 25 | -8.0376 | 0.6836 | 21.4397 | 4 | 1.8054 | 2741 | 2724 | 602 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | time_to_target | 25 | -0.8614 | 0.0000 | 12.4506 | 1 | 0.0664 | 2741 | 2724 | 602 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_NOW | missed_excess_bps | 25 | -37.0205 | -6.2205 | 7.4781 | 6 | 7.8289 | 1503 | 1492 | 355 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_NOW | reach_rate | 25 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 1503 | 1492 | 355 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_NOW | realised_capture_bps | 25 | -7.9973 | 5.8403 | 25.0077 | 10 | 6.4666 | 1503 | 1492 | 355 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_NOW | time_to_target | 25 | -121.7036 | 0.2204 | 16.8711 | 4 | 1.0274 | 1503 | 1492 | 355 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | SHOCK | missed_excess_bps | 25 | -28.5792 | -3.5645 | 14.0948 | 4 | 8.2336 | 1583 | 1571 | 375 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | SHOCK | reach_rate | 25 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 1583 | 1571 | 375 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | SHOCK | realised_capture_bps | 25 | -18.5148 | -1.8032 | 20.9914 | 11 | 5.5891 | 1583 | 1571 | 375 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | SHOCK | time_to_target | 25 | -299.9739 | -2.1083 | 23.0506 | 10 | 9.7173 | 1583 | 1571 | 375 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | SWING_GT_CUR | missed_excess_bps | 25 | -21.4397 | 0.0000 | 9.7450 | 3 | 4.9251 | 1833 | 1821 | 380 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | SWING_GT_CUR | reach_rate | 25 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 1833 | 1821 | 380 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | SWING_GT_CUR | realised_capture_bps | 25 | -11.9002 | 0.0000 | 21.4397 | 4 | 5.0986 | 1833 | 1821 | 380 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | SWING_GT_CUR | time_to_target | 25 | -286.2681 | -0.0684 | 65.4206 | 6 | 0.7224 | 1833 | 1821 | 380 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | TAIL_RISK | missed_excess_bps | 25 | -27.7674 | -5.3084 | 14.1911 | 7 | 10.2243 | 1498 | 1486 | 352 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | TAIL_RISK | reach_rate | 25 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 1498 | 1486 | 352 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | TAIL_RISK | realised_capture_bps | 25 | -19.7063 | 4.9354 | 17.6942 | 9 | 6.8955 | 1498 | 1486 | 352 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150 | TAIL_RISK | time_to_target | 25 | -337.1208 | -0.0004 | 57.8198 | 5 | 1.6728 | 1498 | 1486 | 352 |
| E_CLOSE | TRAIL | M0.75 | RANGE_SCALE | favourable_excursion_captured | 25 | -0.0291 | 0.0723 | 0.2495 | 12 | 0.0653 | 1918 | 1907 | 411 |
| E_CLOSE | TRAIL | M0.75 | RANGE_SCALE | loss_tail_bps | 25 | 0.0000 | -0.0000 | 48.1601 | 3 | 0.0000 | 1918 | 1907 | 411 |
| E_CLOSE | TRAIL | M0.75 | RANGE_SCALE | peak_giveback_bps | 25 | -0.4459 | 20.5021 | 169.3919 | 20 | 13.0429 | 1918 | 1907 | 411 |
| E_CLOSE | TRAIL | M1.00 | RANGE_SCALE | favourable_excursion_captured | 25 | -0.2975 | 0.0313 | 0.1673 | 10 | 0.0584 | 1107 | 1097 | 287 |
| E_CLOSE | TRAIL | M1.00 | RANGE_SCALE | loss_tail_bps | 25 | -53.3091 | 0.4965 | 108.8298 | 9 | 3.4648 | 1107 | 1097 | 287 |
| E_CLOSE | TRAIL | M1.00 | RANGE_SCALE | peak_giveback_bps | 25 | -51.3535 | 29.7437 | 489.3337 | 21 | 12.3735 | 1107 | 1097 | 287 |
| E_CLOSE | TRAIL | M1.50 | RANGE_SCALE | favourable_excursion_captured | 25 | -0.1671 | 0.0071 | 0.7089 | 11 | 0.0712 | 611 | 603 | 196 |
| E_CLOSE | TRAIL | M1.50 | RANGE_SCALE | loss_tail_bps | 25 | -75.7246 | 1.9016 | 1076.0893 | 10 | 12.7389 | 611 | 603 | 196 |
| E_CLOSE | TRAIL | M1.50 | RANGE_SCALE | peak_giveback_bps | 25 | -78.3358 | 42.3967 | 426.1264 | 17 | 13.7782 | 611 | 603 | 196 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | favourable_excursion_captured | 25 | -0.0741 | 0.0000 | 0.0683 | 2 | 0.0237 | 2775 | 2756 | 634 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | loss_tail_bps | 25 | -1.8800 | 0.0000 | 0.3421 | 0 | 0.0000 | 2775 | 2756 | 634 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | peak_giveback_bps | 25 | -13.8259 | 0.9183 | 17.0102 | 5 | 2.4456 | 2775 | 2756 | 634 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | favourable_excursion_captured | 25 | -0.0632 | 0.0000 | 0.0799 | 2 | 0.0193 | 2792 | 2773 | 643 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | loss_tail_bps | 25 | -1.8800 | 0.0000 | 0.0000 | 0 | 0.0000 | 2792 | 2773 | 643 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | peak_giveback_bps | 25 | -13.2675 | 0.9183 | 17.0102 | 7 | 2.5171 | 2792 | 2773 | 643 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_NOW | favourable_excursion_captured | 25 | -0.0724 | 0.0000 | 0.0799 | 2 | 0.0637 | 1500 | 1491 | 361 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_NOW | loss_tail_bps | 25 | -6.5277 | 0.0000 | 0.0000 | 0 | 2.4787 | 1500 | 1491 | 361 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_NOW | peak_giveback_bps | 25 | -21.3560 | 5.7198 | 37.0379 | 7 | 10.1894 | 1500 | 1491 | 361 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150 | SHOCK | favourable_excursion_captured | 25 | -0.1148 | -0.0247 | 0.0915 | 4 | 0.0705 | 1503 | 1493 | 368 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150 | SHOCK | loss_tail_bps | 25 | -3.1146 | 0.0000 | 0.0000 | 0 | 4.0704 | 1503 | 1493 | 368 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150 | SHOCK | peak_giveback_bps | 25 | -25.6953 | -2.3040 | 14.5739 | 7 | 8.1481 | 1503 | 1493 | 368 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K12 | decay_bps | 25 | 0.0000 | 32.1936 | 99.5425 | 22 | 11.4350 | 9183 | 9182 | 3878 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K12 | holding_efficiency | 25 | -0.0716 | 0.1928 | 0.8811 | 6 | 0.5892 | 9183 | 9182 | 3878 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K12 | opportunity_duration | 25 | 0.0000 | 0.9251 | 1.8475 | 22 | 0.2347 | 9183 | 9182 | 3878 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K12 | outcome_by_time_bps | 25 | -39.2121 | 0.3533 | 61.5221 | 0 | 14.6736 | 9183 | 9182 | 3878 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K4 | decay_bps | 25 | -4.0250 | 33.0278 | 114.2716 | 23 | 11.4659 | 9069 | 9068 | 3832 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K4 | holding_efficiency | 25 | -1.3484 | -0.1854 | 0.9588 | 8 | 0.7219 | 9069 | 9068 | 3832 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K4 | opportunity_duration | 25 | 0.3563 | 0.9407 | 1.3348 | 23 | 0.2363 | 9069 | 9068 | 3832 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_FORECAST_K4 | outcome_by_time_bps | 25 | -110.2797 | 2.2228 | 27.7012 | 3 | 15.5336 | 9069 | 9068 | 3832 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_NOW | decay_bps | 25 | 13.5308 | 32.4178 | 216.2041 | 24 | 9.6180 | 15056 | 15055 | 6333 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_NOW | holding_efficiency | 25 | -0.7709 | -0.1008 | 0.7776 | 4 | 0.6026 | 15056 | 15055 | 6333 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_NOW | opportunity_duration | 25 | 0.4998 | 0.9502 | 1.2077 | 25 | 0.1835 | 15056 | 15055 | 6333 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | LEVEL_NOW | outcome_by_time_bps | 25 | -68.9265 | 1.2040 | 11.4197 | 2 | 12.5525 | 15056 | 15055 | 6333 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | SWING_GT_CUR | decay_bps | 25 | -0.5607 | 26.1368 | 130.5122 | 22 | 8.3198 | 15110 | 15107 | 6100 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | SWING_GT_CUR | holding_efficiency | 25 | -1.6915 | -0.5948 | 0.0000 | 3 | 1.3120 | 15110 | 15107 | 6100 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | SWING_GT_CUR | opportunity_duration | 25 | 0.0000 | 0.7991 | 1.1731 | 23 | 0.1873 | 15110 | 15107 | 6100 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | SWING_GT_CUR | outcome_by_time_bps | 25 | -34.3105 | 0.7801 | 45.2022 | 2 | 10.6897 | 15110 | 15107 | 6100 |
| E_TOUCH | HOLD | STATE_SHOCK_2 | SHOCK | decay_bps | 25 | -284.3766 | -49.5094 | -19.0048 | 25 | 8.9388 | 20235 | 20235 | 9491 |
| E_TOUCH | HOLD | STATE_SHOCK_2 | SHOCK | holding_efficiency | 25 | -0.5204 | -0.2464 | 0.0277 | 1 | 2.6600 | 20235 | 20235 | 9491 |
| E_TOUCH | HOLD | STATE_SHOCK_2 | SHOCK | opportunity_duration | 25 | -1.0318 | -0.8412 | -0.6642 | 25 | 0.0762 | 20235 | 20235 | 9491 |
| E_TOUCH | HOLD | STATE_SHOCK_2 | SHOCK | outcome_by_time_bps | 25 | -36.9715 | 0.5702 | 141.7602 | 0 | 10.4387 | 20235 | 20235 | 9491 |
| E_TOUCH | SIZE | SCALE_NORMALISED | RANGE_SCALE | concentration | 25 | -0.0049 | -0.0002 | 0.0244 | 6 | 0.0036 | 43077 | 43077 | 9637 |
| E_TOUCH | SIZE | SCALE_NORMALISED | RANGE_SCALE | drawdown_bps | 25 | -6056.1611 | 531.6415 | 6462.0713 | 2 | 5364.9347 | 43077 | 43077 | 9637 |
| E_TOUCH | SIZE | SCALE_NORMALISED | RANGE_SCALE | risk_dispersion | 25 | -281.8151 | 5.2733 | 92.6486 | 15 | 23.3823 | 43077 | 43077 | 9637 |
| E_TOUCH | SIZE | SCALE_NORMALISED | RANGE_SCALE | tail_loss_bps | 25 | -1037.4374 | -18.3597 | 136.8161 | 10 | 54.7963 | 43077 | 43077 | 9637 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K12 | concentration | 25 | -0.0113 | 0.0010 | 0.0094 | 11 | 0.0009 | 43077 | 43077 | 9637 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K12 | drawdown_bps | 25 | -1828.1295 | 1224.1071 | 8836.9029 | 2 | 2520.2115 | 43077 | 43077 | 9637 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K12 | risk_dispersion | 25 | -78.4906 | -22.3867 | -1.0189 | 24 | 6.9357 | 43077 | 43077 | 9637 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K12 | tail_loss_bps | 25 | -297.2259 | -45.6924 | 0.0000 | 19 | 36.0398 | 43077 | 43077 | 9637 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K4 | concentration | 25 | -0.0110 | 0.0011 | 0.0096 | 12 | 0.0011 | 43077 | 43077 | 9637 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K4 | drawdown_bps | 25 | -2000.1006 | 1571.3126 | 8812.2064 | 4 | 2930.9237 | 43077 | 43077 | 9637 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K4 | risk_dispersion | 25 | -81.5250 | -23.7048 | -9.3628 | 25 | 9.3628 | 43077 | 43077 | 9637 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | LEVEL_FORECAST_K4 | tail_loss_bps | 25 | -297.2259 | -52.7639 | 0.0000 | 19 | 39.1189 | 43077 | 43077 | 9637 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | LEVEL_NOW | concentration | 25 | -0.0145 | 0.0017 | 0.0290 | 3 | 0.0024 | 43077 | 43077 | 9637 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | LEVEL_NOW | drawdown_bps | 25 | -1856.1980 | 2993.2768 | 10334.6131 | 10 | 4066.8592 | 43077 | 43077 | 9637 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | LEVEL_NOW | risk_dispersion | 25 | -164.8973 | -59.0424 | -25.6935 | 25 | 17.7770 | 43077 | 43077 | 9637 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | LEVEL_NOW | tail_loss_bps | 25 | -1058.5292 | -122.0874 | -44.3775 | 22 | 53.5131 | 43077 | 43077 | 9637 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | SHOCK | concentration | 25 | -0.0042 | 0.0006 | 0.0232 | 8 | 0.0014 | 43077 | 43077 | 9637 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | SHOCK | drawdown_bps | 25 | -2224.7427 | 1324.4179 | 6022.0017 | 4 | 2512.7377 | 43077 | 43077 | 9637 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | SHOCK | risk_dispersion | 25 | -168.5062 | -26.9226 | -9.3998 | 25 | 11.1857 | 43077 | 43077 | 9637 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | SHOCK | tail_loss_bps | 25 | -699.8920 | -48.5272 | -6.9153 | 19 | 42.7604 | 43077 | 43077 | 9637 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | TAIL_RISK | concentration | 25 | -0.0130 | 0.0018 | 0.0117 | 6 | 0.0025 | 43077 | 43077 | 9637 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | TAIL_RISK | drawdown_bps | 25 | -1121.7760 | 3468.8788 | 10240.1855 | 14 | 3727.6696 | 43077 | 43077 | 9637 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | TAIL_RISK | risk_dispersion | 25 | -440.3707 | -55.4592 | -29.1588 | 25 | 14.8330 | 43077 | 43077 | 9637 |
| E_TOUCH | SIZE | STATE_HALVE_HIGH | TAIL_RISK | tail_loss_bps | 25 | -1072.1845 | -112.3786 | -52.4442 | 23 | 57.4494 | 43077 | 43077 | 9637 |
| E_TOUCH | STOP | M0.75 | RANGE_SCALE | adverse_excursion_bps | 25 | 0.9795 | 11.7736 | 143.9528 | 15 | 10.4759 | 3899 | 3886 | 659 |
| E_TOUCH | STOP | M0.75 | RANGE_SCALE | loss_severity_bps | 25 | -159.3589 | -10.4227 | -0.2178 | 17 | 8.9729 | 3899 | 3886 | 659 |
| E_TOUCH | STOP | M0.75 | RANGE_SCALE | recovery_after_stop_bps | 25 | -126.9452 | -1.1880 | 13.4114 | 3 | 13.4530 | 3899 | 3886 | 659 |
| E_TOUCH | STOP | M0.75 | RANGE_SCALE | stop_rate | 25 | -0.0036 | 0.0000 | 0.0000 | 0 | 0.0000 | 3899 | 3886 | 659 |
| E_TOUCH | STOP | M0.75 | SWING_SCALE | adverse_excursion_bps | 6 | 495.5823 | 528.0658 | 697.8880 | 6 | 108.1963 | 32 | 31 | 26 |
| E_TOUCH | STOP | M0.75 | SWING_SCALE | loss_severity_bps | 6 | -676.7677 | -524.7828 | -499.6875 | 6 | 115.8458 | 32 | 31 | 26 |
| E_TOUCH | STOP | M0.75 | SWING_SCALE | recovery_after_stop_bps | 6 | -47.5022 | -34.8176 | -22.1330 | 0 | 227.6093 | 32 | 31 | 26 |
| E_TOUCH | STOP | M0.75 | SWING_SCALE | stop_rate | 6 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 32 | 31 | 26 |
| E_TOUCH | STOP | M1.00 | RANGE_SCALE | adverse_excursion_bps | 25 | -78.8729 | 25.3708 | 165.0857 | 19 | 16.6490 | 2265 | 2252 | 467 |
| E_TOUCH | STOP | M1.00 | RANGE_SCALE | loss_severity_bps | 25 | -139.7728 | -16.3486 | 52.0975 | 22 | 15.2233 | 2265 | 2252 | 467 |
| E_TOUCH | STOP | M1.00 | RANGE_SCALE | recovery_after_stop_bps | 25 | -190.1048 | -1.2350 | 349.0502 | 5 | 24.0660 | 2265 | 2252 | 467 |
| E_TOUCH | STOP | M1.00 | RANGE_SCALE | stop_rate | 25 | -0.0065 | 0.0000 | 0.0000 | 0 | 0.0000 | 2265 | 2252 | 467 |
| E_TOUCH | STOP | M1.00 | SWING_SCALE | adverse_excursion_bps | 7 | 525.4118 | 1022.1186 | 2646.5927 | 7 | 279.5188 | 22 | 21 | 19 |
| E_TOUCH | STOP | M1.00 | SWING_SCALE | loss_severity_bps | 7 | -2646.5927 | -1027.6686 | -506.3940 | 7 | 229.4272 | 22 | 21 | 19 |
| E_TOUCH | STOP | M1.00 | SWING_SCALE | recovery_after_stop_bps | 7 | 178.1064 | 178.1064 | 178.1064 | 1 | 126.2805 | 22 | 21 | 19 |
| E_TOUCH | STOP | M1.00 | SWING_SCALE | stop_rate | 7 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 22 | 21 | 19 |
| E_TOUCH | STOP | M1.50 | RANGE_SCALE | adverse_excursion_bps | 25 | -92.7223 | 30.1959 | 416.1232 | 18 | 21.3149 | 1298 | 1285 | 391 |
| E_TOUCH | STOP | M1.50 | RANGE_SCALE | loss_severity_bps | 25 | -428.7772 | -27.5165 | 68.4862 | 19 | 15.8051 | 1298 | 1285 | 391 |
| E_TOUCH | STOP | M1.50 | RANGE_SCALE | recovery_after_stop_bps | 25 | -65.3576 | -0.3262 | 74.3332 | 5 | 26.6517 | 1298 | 1285 | 391 |
| E_TOUCH | STOP | M1.50 | RANGE_SCALE | stop_rate | 25 | -0.0185 | 0.0000 | 0.0000 | 0 | 0.0000 | 1298 | 1285 | 391 |
| E_TOUCH | STOP | M1.50 | SWING_SCALE | adverse_excursion_bps | 8 | 564.8926 | 951.6847 | 3394.3162 | 8 | 346.0523 | 16 | 15 | 14 |
| E_TOUCH | STOP | M1.50 | SWING_SCALE | loss_severity_bps | 8 | -3335.7016 | -888.2660 | -610.0218 | 8 | 583.0340 | 16 | 15 | 14 |
| E_TOUCH | STOP | M1.50 | SWING_SCALE | recovery_after_stop_bps | 8 | -234.8330 | -234.8330 | -234.8330 | 1 | 264.5379 | 16 | 15 | 14 |
| E_TOUCH | STOP | M1.50 | SWING_SCALE | stop_rate | 8 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 16 | 15 | 14 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | adverse_excursion_bps | 25 | -20.5696 | 0.6019 | 34.3409 | 4 | 2.1998 | 3991 | 3973 | 731 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | loss_severity_bps | 25 | -51.8305 | -0.3255 | 14.4815 | 6 | 2.2311 | 3991 | 3973 | 731 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | recovery_after_stop_bps | 25 | -13.8709 | 0.0000 | 54.9157 | 2 | 4.1288 | 3991 | 3973 | 731 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | stop_rate | 25 | 0.0000 | 0.0000 | 0.0035 | 0 | 0.0000 | 3991 | 3973 | 731 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | adverse_excursion_bps | 25 | -10.8813 | 0.6019 | 34.3409 | 5 | 2.4184 | 3920 | 3903 | 715 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | loss_severity_bps | 25 | -51.8305 | -0.3255 | 3.4287 | 5 | 2.7072 | 3920 | 3903 | 715 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | recovery_after_stop_bps | 25 | -12.5498 | 0.0000 | 54.9157 | 2 | 3.6234 | 3920 | 3903 | 715 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | stop_rate | 25 | 0.0000 | 0.0000 | 0.0038 | 0 | 0.0000 | 3920 | 3903 | 715 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | LEVEL_NOW | adverse_excursion_bps | 25 | -30.6067 | 4.8807 | 21.1693 | 4 | 7.7344 | 2465 | 2454 | 456 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | LEVEL_NOW | loss_severity_bps | 25 | -23.9054 | -4.4560 | 3.8662 | 4 | 7.8116 | 2465 | 2454 | 456 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | LEVEL_NOW | recovery_after_stop_bps | 25 | -34.5899 | -2.7991 | 60.5704 | 1 | 16.7248 | 2465 | 2454 | 456 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | LEVEL_NOW | stop_rate | 25 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 2465 | 2454 | 456 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | SHOCK | adverse_excursion_bps | 25 | -29.3798 | -2.0151 | 25.8587 | 10 | 5.9315 | 3054 | 3041 | 559 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | SHOCK | loss_severity_bps | 25 | -17.5019 | 1.6908 | 12.1162 | 9 | 4.7788 | 3054 | 3041 | 559 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | SHOCK | recovery_after_stop_bps | 25 | -46.3610 | -0.7195 | 22.1491 | 1 | 11.6213 | 3054 | 3041 | 559 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | SHOCK | stop_rate | 25 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 3054 | 3041 | 559 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | TAIL_RISK | adverse_excursion_bps | 25 | -47.6374 | 3.5754 | 21.7395 | 11 | 8.4184 | 2231 | 2221 | 419 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | TAIL_RISK | loss_severity_bps | 25 | -26.9158 | -2.9383 | 29.0050 | 12 | 7.7541 | 2231 | 2221 | 419 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | TAIL_RISK | recovery_after_stop_bps | 25 | -46.6306 | -5.0367 | 381.0174 | 6 | 17.0754 | 2231 | 2221 | 419 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150 | TAIL_RISK | stop_rate | 25 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 2231 | 2221 | 419 |
| E_TOUCH | TARGET | M0.75 | RANGE_SCALE | missed_excess_bps | 25 | -279.3296 | -17.8003 | 82.0572 | 15 | 12.8586 | 1581 | 1574 | 309 |
| E_TOUCH | TARGET | M0.75 | RANGE_SCALE | reach_rate | 25 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 1581 | 1574 | 309 |
| E_TOUCH | TARGET | M0.75 | RANGE_SCALE | realised_capture_bps | 25 | -51.2104 | 22.8548 | 135.9399 | 21 | 13.1824 | 1581 | 1574 | 309 |
| E_TOUCH | TARGET | M0.75 | RANGE_SCALE | time_to_target | 25 | -1470.9000 | 1.3830 | 142.0527 | 18 | 2.5791 | 1581 | 1574 | 309 |
| E_TOUCH | TARGET | M0.75 | SWING_SCALE | missed_excess_bps | 11 | -711.9916 | -170.1046 | -78.1612 | 7 | 125.8365 | 46 | 45 | 28 |
| E_TOUCH | TARGET | M0.75 | SWING_SCALE | reach_rate | 11 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 46 | 45 | 28 |
| E_TOUCH | TARGET | M0.75 | SWING_SCALE | realised_capture_bps | 11 | 280.6389 | 789.0442 | 1612.5506 | 11 | 96.6708 | 46 | 45 | 28 |
| E_TOUCH | TARGET | M0.75 | SWING_SCALE | time_to_target | 11 | 38.2444 | 746.6467 | 2126.5833 | 11 | 669.5910 | 46 | 45 | 28 |
| E_TOUCH | TARGET | M1.00 | RANGE_SCALE | missed_excess_bps | 25 | -143.0420 | -17.6365 | 70.0802 | 19 | 15.8941 | 1017 | 1010 | 231 |
| E_TOUCH | TARGET | M1.00 | RANGE_SCALE | reach_rate | 25 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 1017 | 1010 | 231 |
| E_TOUCH | TARGET | M1.00 | RANGE_SCALE | realised_capture_bps | 25 | -51.3535 | 27.0507 | 299.5924 | 21 | 16.2278 | 1017 | 1010 | 231 |
| E_TOUCH | TARGET | M1.00 | RANGE_SCALE | time_to_target | 25 | -18.5333 | 4.4042 | 402.5278 | 18 | 6.5898 | 1017 | 1010 | 231 |
| E_TOUCH | TARGET | M1.00 | SWING_SCALE | missed_excess_bps | 10 | -705.0342 | -215.4745 | 18.6346 | 8 | 98.4366 | 44 | 43 | 26 |
| E_TOUCH | TARGET | M1.00 | SWING_SCALE | reach_rate | 10 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 44 | 43 | 26 |
| E_TOUCH | TARGET | M1.00 | SWING_SCALE | realised_capture_bps | 10 | 345.0920 | 852.7122 | 1535.6804 | 10 | 84.2374 | 44 | 43 | 26 |
| E_TOUCH | TARGET | M1.00 | SWING_SCALE | time_to_target | 10 | 4.8833 | 359.0438 | 1209.2833 | 10 | 272.6118 | 44 | 43 | 26 |
| E_TOUCH | TARGET | M1.50 | RANGE_SCALE | missed_excess_bps | 25 | -207.0773 | -31.3810 | 10.9507 | 14 | 32.6124 | 646 | 639 | 189 |
| E_TOUCH | TARGET | M1.50 | RANGE_SCALE | reach_rate | 25 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 646 | 639 | 189 |
| E_TOUCH | TARGET | M1.50 | RANGE_SCALE | realised_capture_bps | 25 | 0.6996 | 89.1926 | 289.7621 | 21 | 29.8919 | 646 | 639 | 189 |
| E_TOUCH | TARGET | M1.50 | RANGE_SCALE | time_to_target | 25 | -32.6738 | 1.9611 | 197.5500 | 17 | 3.3204 | 646 | 639 | 189 |
| E_TOUCH | TARGET | M1.50 | SWING_SCALE | missed_excess_bps | 10 | -688.0771 | -17.9716 | 374.9709 | 7 | 24.1446 | 18 | 15 | 14 |
| E_TOUCH | TARGET | M1.50 | SWING_SCALE | reach_rate | 10 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 18 | 15 | 14 |
| E_TOUCH | TARGET | M1.50 | SWING_SCALE | realised_capture_bps | 10 | 549.4757 | 1139.8938 | 1986.4857 | 10 | 240.0688 | 18 | 15 | 14 |
| E_TOUCH | TARGET | M1.50 | SWING_SCALE | time_to_target | 10 | 11.8000 | 954.8667 | 6843.1333 | 10 | 1376.2056 | 18 | 15 | 14 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | missed_excess_bps | 25 | -7.8433 | -0.1669 | 9.2830 | 5 | 1.1671 | 3316 | 3302 | 581 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | reach_rate | 25 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 3316 | 3302 | 581 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | realised_capture_bps | 25 | -12.1342 | 0.0630 | 12.0637 | 6 | 1.2933 | 3316 | 3302 | 581 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | time_to_target | 25 | -0.4847 | 0.0000 | 14.4073 | 2 | 0.1900 | 3316 | 3302 | 581 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | missed_excess_bps | 25 | -7.8433 | -0.2384 | 8.8920 | 5 | 1.5928 | 3324 | 3311 | 584 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | reach_rate | 25 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 3324 | 3311 | 584 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | realised_capture_bps | 25 | -5.8604 | 0.2384 | 12.0637 | 5 | 1.3187 | 3324 | 3311 | 584 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | time_to_target | 25 | -0.3575 | 0.0000 | 14.6099 | 3 | 0.1398 | 3324 | 3311 | 584 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_NOW | missed_excess_bps | 25 | -79.7498 | -3.2331 | 21.2474 | 8 | 9.7017 | 1830 | 1823 | 360 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_NOW | reach_rate | 25 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 1830 | 1823 | 360 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_NOW | realised_capture_bps | 25 | -10.5533 | 6.2107 | 29.9212 | 11 | 7.7301 | 1830 | 1823 | 360 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | LEVEL_NOW | time_to_target | 25 | -20.6020 | 0.2326 | 57.2308 | 6 | 2.5536 | 1830 | 1823 | 360 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | SHOCK | missed_excess_bps | 25 | -40.6053 | -1.5917 | 16.2875 | 6 | 6.5798 | 1954 | 1942 | 371 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | SHOCK | reach_rate | 25 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 1954 | 1942 | 371 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | SHOCK | realised_capture_bps | 25 | -12.3594 | 0.0019 | 13.7124 | 4 | 5.6909 | 1954 | 1942 | 371 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | SHOCK | time_to_target | 25 | -83.3586 | -0.0033 | 47.0141 | 7 | 4.2307 | 1954 | 1942 | 371 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | SWING_GT_CUR | missed_excess_bps | 25 | -27.7160 | 0.0000 | 9.6016 | 6 | 5.8405 | 2369 | 2357 | 435 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | SWING_GT_CUR | reach_rate | 25 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 2369 | 2357 | 435 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | SWING_GT_CUR | realised_capture_bps | 25 | -11.1493 | 1.1110 | 42.7498 | 9 | 5.0994 | 2369 | 2357 | 435 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | SWING_GT_CUR | time_to_target | 25 | -76.0559 | 0.1429 | 14.6928 | 9 | 1.1599 | 2369 | 2357 | 435 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | TAIL_RISK | missed_excess_bps | 25 | -19.0501 | -2.4400 | 19.9072 | 9 | 9.8788 | 1489 | 1483 | 295 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | TAIL_RISK | reach_rate | 25 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 1489 | 1483 | 295 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | TAIL_RISK | realised_capture_bps | 25 | -18.6676 | 3.6260 | 26.7492 | 13 | 7.5783 | 1489 | 1483 | 295 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150 | TAIL_RISK | time_to_target | 25 | -44.3372 | 0.0687 | 61.3009 | 10 | 2.3758 | 1489 | 1483 | 295 |
| E_TOUCH | TRAIL | M0.75 | RANGE_SCALE | favourable_excursion_captured | 25 | -0.0928 | 0.0521 | 0.3698 | 14 | 0.0612 | 1727 | 1722 | 331 |
| E_TOUCH | TRAIL | M0.75 | RANGE_SCALE | loss_tail_bps | 25 | -4.0527 | 0.0000 | 53.5498 | 6 | 0.0211 | 1727 | 1722 | 331 |
| E_TOUCH | TRAIL | M0.75 | RANGE_SCALE | peak_giveback_bps | 25 | -339.8510 | 14.7741 | 99.2627 | 18 | 11.7172 | 1727 | 1722 | 331 |
| E_TOUCH | TRAIL | M1.00 | RANGE_SCALE | favourable_excursion_captured | 25 | -0.0308 | 0.0439 | 0.3894 | 10 | 0.0701 | 1046 | 1041 | 232 |
| E_TOUCH | TRAIL | M1.00 | RANGE_SCALE | loss_tail_bps | 25 | -47.0015 | 1.2441 | 81.5504 | 9 | 5.4752 | 1046 | 1041 | 232 |
| E_TOUCH | TRAIL | M1.00 | RANGE_SCALE | peak_giveback_bps | 25 | -51.3535 | 29.5982 | 492.5917 | 20 | 20.4799 | 1046 | 1041 | 232 |
| E_TOUCH | TRAIL | M1.50 | RANGE_SCALE | favourable_excursion_captured | 25 | -0.0848 | 0.0032 | 0.7044 | 8 | 0.0689 | 738 | 730 | 235 |
| E_TOUCH | TRAIL | M1.50 | RANGE_SCALE | loss_tail_bps | 25 | -75.7246 | 0.5733 | 1062.1764 | 9 | 6.7201 | 738 | 730 | 235 |
| E_TOUCH | TRAIL | M1.50 | RANGE_SCALE | peak_giveback_bps | 25 | -78.3358 | 47.1158 | 425.2708 | 19 | 26.0646 | 738 | 730 | 235 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | favourable_excursion_captured | 25 | -0.0843 | -0.0037 | 0.0181 | 3 | 0.0153 | 3714 | 3698 | 654 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | loss_tail_bps | 25 | -2.6610 | 0.0000 | 0.0000 | 0 | 0.0000 | 3714 | 3698 | 654 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K12 | peak_giveback_bps | 25 | -11.4805 | 0.2383 | 39.7346 | 5 | 1.7792 | 3714 | 3698 | 654 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | favourable_excursion_captured | 25 | -0.0669 | -0.0043 | 0.0141 | 2 | 0.0152 | 3675 | 3661 | 637 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | loss_tail_bps | 25 | -2.6610 | 0.0000 | 0.0000 | 0 | 0.0000 | 3675 | 3661 | 637 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_FORECAST_K4 | peak_giveback_bps | 25 | -7.5122 | 0.5331 | 39.7346 | 5 | 1.8800 | 3675 | 3661 | 637 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_NOW | favourable_excursion_captured | 25 | -0.0874 | -0.0142 | 0.0561 | 3 | 0.0557 | 1712 | 1702 | 339 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_NOW | loss_tail_bps | 25 | -5.0444 | 0.0000 | 0.0000 | 0 | 0.7411 | 1712 | 1702 | 339 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150 | LEVEL_NOW | peak_giveback_bps | 25 | -73.2245 | 6.9922 | 39.7346 | 11 | 9.4849 | 1712 | 1702 | 339 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150 | SHOCK | favourable_excursion_captured | 25 | -0.0790 | -0.0141 | 0.0418 | 5 | 0.0581 | 1751 | 1742 | 312 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150 | SHOCK | loss_tail_bps | 25 | -2.5765 | 0.0000 | 2.3024 | 0 | 0.0000 | 1751 | 1742 | 312 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150 | SHOCK | peak_giveback_bps | 25 | -40.8440 | 0.4717 | 27.3049 | 6 | 9.8418 | 1751 | 1742 | 312 |

### 6.3 Lens B — component combinations (`MANAGEMENT_COMPONENT_COMBINATION`)

ctrader:

| entry_variant | device | setting | component | metric_name | sym | est_min | est_med | est_max | ci_ex0 | mde_med | cfill | cclose | efftr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | RANGE_SCALE | decay_bps | 3 | 2.5253 | 7.7847 | 12.9742 | 12 | 1.4762 | 12380 | 12378 | 5389 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | RANGE_SCALE | holding_efficiency | 3 |  |  |  | 2 |  | 12380 | 12378 | 5389 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | RANGE_SCALE | opportunity_duration | 3 | 0.8962 | 1.3739 | 1.7704 | 12 | 0.1759 | 12380 | 12378 | 5389 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | RANGE_SCALE | outcome_by_time_bps | 3 | -2.1731 | -1.2671 | 2.4458 | 6 | 1.7035 | 12380 | 12378 | 5389 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | SHOCK | decay_bps | 3 | 2.5893 | 5.2935 | 7.8094 | 3 | 1.3722 | 4031 | 4031 | 1791 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | SHOCK | holding_efficiency | 3 |  |  |  | 1 |  | 4031 | 4031 | 1791 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | SHOCK | opportunity_duration | 3 | 0.8796 | 0.9354 | 0.9361 | 3 | 0.1537 | 4031 | 4031 | 1791 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | SHOCK | outcome_by_time_bps | 3 | -0.6602 | -0.3733 | -0.2172 | 0 | 1.5569 | 4031 | 4031 | 1791 |
| E_CLOSE | SIZE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | concentration | 3 | -0.0013 | -0.0000 | 0.0023 | 3 | 0.0010 | 22611 | 22611 | 5922 |
| E_CLOSE | SIZE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | drawdown_bps | 3 | 176.6152 | 444.1966 | 1550.0570 | 2 | 817.1912 | 22611 | 22611 | 5922 |
| E_CLOSE | SIZE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | risk_dispersion | 3 | -28.3989 | -7.3764 | -2.9195 | 9 | 1.2539 | 22611 | 22611 | 5922 |
| E_CLOSE | SIZE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | tail_loss_bps | 3 | -66.2398 | -17.5011 | -8.0085 | 9 | 6.1531 | 22611 | 22611 | 5922 |
| E_CLOSE | SIZE | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | concentration | 3 | 0.0011 | 0.0017 | 0.0021 | 1 | 0.0023 | 7537 | 7537 | 1974 |
| E_CLOSE | SIZE | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | drawdown_bps | 3 | 237.8095 | 490.7740 | 511.4337 | 0 | 499.4624 | 7537 | 7537 | 1974 |
| E_CLOSE | SIZE | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | risk_dispersion | 3 | -14.2268 | -8.6965 | -5.2985 | 3 | 1.1578 | 7537 | 7537 | 1974 |
| E_CLOSE | SIZE | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | tail_loss_bps | 3 | -40.3587 | -24.0881 | -11.6164 | 3 | 5.7391 | 7537 | 7537 | 1974 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | adverse_excursion_bps | 2 | 1.7380 | 6.7811 | 19.1199 | 3 | 4.0145 | 142 | 141 | 39 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | loss_severity_bps | 2 | -11.9067 | -6.4118 | -1.8342 | 3 | 2.2918 | 142 | 141 | 39 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | recovery_after_stop_bps | 2 | -4.3972 | -3.0389 | 1.9785 | 0 | 4.5311 | 142 | 141 | 39 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | stop_rate | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 142 | 141 | 39 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | adverse_excursion_bps | 2 | 0.6169 | 1.1877 | 1.7585 | 1 | 1.0908 | 189 | 188 | 46 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | loss_severity_bps | 2 | -1.2462 | -0.9570 | -0.6679 | 1 | 0.9373 | 189 | 188 | 46 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | recovery_after_stop_bps | 2 | -1.0866 | -0.5999 | -0.1133 | 0 | 3.2438 | 189 | 188 | 46 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | stop_rate | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 189 | 188 | 46 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | missed_excess_bps | 2 | -7.5545 | -3.7950 | -0.0355 | 1 | 3.6385 | 43 | 43 | 15 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | reach_rate | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 43 | 43 | 15 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | realised_capture_bps | 2 | 1.2465 | 5.4063 | 9.5661 | 1 | 4.2822 | 43 | 43 | 15 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | time_to_target | 2 | -385.3042 | -182.2682 | 20.7677 | 1 | 413.5936 | 43 | 43 | 15 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | missed_excess_bps | 2 | -0.8548 | -0.3904 | 0.0740 | 0 | 0.9183 | 138 | 136 | 41 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | reach_rate | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 138 | 136 | 41 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | realised_capture_bps | 2 | 0.3351 | 0.7449 | 1.1547 | 1 | 0.7756 | 138 | 136 | 41 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | time_to_target | 2 | -5.5349 | -2.6899 | 0.1552 | 1 | 5.6171 | 138 | 136 | 41 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | favourable_excursion_captured | 2 | -0.1007 | -0.0181 | 0.0645 | 2 | 0.0948 | 132 | 131 | 41 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | loss_tail_bps | 2 | -0.9711 | -0.2441 | 0.4828 | 1 | 2.0208 | 132 | 131 | 41 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | peak_giveback_bps | 2 | 3.7052 | 4.4025 | 5.0997 | 2 | 2.8310 | 132 | 131 | 41 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | favourable_excursion_captured | 3 | -0.2092 | -0.0614 | 0.0148 | 1 | 0.0612 | 157 | 155 | 47 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | loss_tail_bps | 3 | -0.9063 | -0.3720 | 0.0000 | 1 | 1.1968 | 157 | 155 | 47 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | peak_giveback_bps | 3 | 0.7160 | 1.3873 | 2.2370 | 2 | 1.2325 | 157 | 155 | 47 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | RANGE_SCALE | decay_bps | 3 | 2.2386 | 6.1817 | 10.5494 | 12 | 1.3222 | 11300 | 11300 | 4696 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | RANGE_SCALE | holding_efficiency | 3 | 0.0991 | 0.1215 | 0.1438 | 0 | 0.3631 | 11300 | 11300 | 4696 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | RANGE_SCALE | opportunity_duration | 3 | 0.7659 | 1.3088 | 1.6077 | 12 | 0.1943 | 11300 | 11300 | 4696 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | RANGE_SCALE | outcome_by_time_bps | 3 | -1.4930 | 0.5545 | 3.3564 | 0 | 1.6338 | 11300 | 11300 | 4696 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | SHOCK | decay_bps | 3 | 2.2171 | 4.4802 | 6.5350 | 3 | 1.2533 | 3539 | 3539 | 1582 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | SHOCK | holding_efficiency | 3 |  |  |  | 0 |  | 3539 | 3539 | 1582 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | SHOCK | opportunity_duration | 3 | 0.8190 | 0.9573 | 1.0478 | 3 | 0.1591 | 3539 | 3539 | 1582 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | SHOCK | outcome_by_time_bps | 3 | 0.2567 | 0.4813 | 0.4859 | 0 | 1.6105 | 3539 | 3539 | 1582 |
| E_TOUCH | SIZE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | concentration | 3 | -0.0004 | 0.0001 | 0.0017 | 2 | 0.0009 | 25488 | 25488 | 5841 |
| E_TOUCH | SIZE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | drawdown_bps | 3 | 280.7168 | 652.3801 | 3035.5699 | 4 | 711.8685 | 25488 | 25488 | 5841 |
| E_TOUCH | SIZE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | risk_dispersion | 3 | -28.3101 | -7.5038 | -2.0594 | 9 | 1.0924 | 25488 | 25488 | 5841 |
| E_TOUCH | SIZE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | tail_loss_bps | 3 | -68.3299 | -14.6734 | -5.5796 | 9 | 5.6762 | 25488 | 25488 | 5841 |
| E_TOUCH | SIZE | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | concentration | 3 | 0.0013 | 0.0016 | 0.0020 | 3 | 0.0008 | 8496 | 8496 | 1947 |
| E_TOUCH | SIZE | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | drawdown_bps | 3 | -22.8033 | 460.5729 | 2045.1665 | 0 | 519.4642 | 8496 | 8496 | 1947 |
| E_TOUCH | SIZE | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | risk_dispersion | 3 | -13.8948 | -7.6756 | -5.0230 | 3 | 1.0852 | 8496 | 8496 | 1947 |
| E_TOUCH | SIZE | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | tail_loss_bps | 3 | -32.9355 | -17.0484 | -9.4786 | 3 | 6.4592 | 8496 | 8496 | 1947 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | adverse_excursion_bps | 1 | 5.1944 | 5.1944 | 5.1944 | 1 | 3.2781 | 102 | 102 | 19 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | loss_severity_bps | 1 | -4.6618 | -4.6618 | -4.6618 | 1 | 4.1081 | 102 | 102 | 19 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | recovery_after_stop_bps | 1 | 1.3503 | 1.3503 | 1.3503 | 0 | 2.1684 | 102 | 102 | 19 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | stop_rate | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 102 | 102 | 19 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | adverse_excursion_bps | 2 | 0.3263 | 0.4865 | 0.6467 | 0 | 1.1200 | 248 | 247 | 41 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | loss_severity_bps | 2 | -0.1354 | -0.0044 | 0.1265 | 0 | 0.9839 | 248 | 247 | 41 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | recovery_after_stop_bps | 2 | 0.0618 | 0.5523 | 1.0428 | 0 | 1.9622 | 248 | 247 | 41 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | stop_rate | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 248 | 247 | 41 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | missed_excess_bps | 2 | -13.6565 | -0.0341 | 1.1359 | 1 | 1.9977 | 137 | 136 | 33 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | reach_rate | 2 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 137 | 136 | 33 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | realised_capture_bps | 2 | 1.1170 | 1.7145 | 16.1104 | 1 | 2.4334 | 137 | 136 | 33 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | time_to_target | 2 | -255.7579 | 0.7826 | 24.9036 | 1 | 17.5613 | 137 | 136 | 33 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | missed_excess_bps | 1 | -1.1846 | -1.1846 | -1.1846 | 0 | 1.6297 | 40 | 40 | 8 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | reach_rate | 1 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 40 | 40 | 8 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | realised_capture_bps | 1 | 0.9224 | 0.9224 | 0.9224 | 0 | 1.3834 | 40 | 40 | 8 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | time_to_target | 1 | -14.0342 | -14.0342 | -14.0342 | 0 | 37.7114 | 40 | 40 | 8 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | favourable_excursion_captured | 2 | -0.0287 | -0.0028 | 0.0175 | 0 | 0.0655 | 148 | 148 | 41 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | loss_tail_bps | 2 | -0.5708 | -0.0979 | -0.0014 | 1 | 1.3614 | 148 | 148 | 41 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | peak_giveback_bps | 2 | 3.4159 | 8.2641 | 12.9676 | 3 | 2.7637 | 148 | 148 | 41 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | favourable_excursion_captured | 2 | -0.0614 | -0.0307 | 0.0001 | 1 | 0.0922 | 97 | 96 | 15 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | loss_tail_bps | 2 | -0.7086 | -0.7040 | -0.6993 | 2 | 0.8819 | 97 | 96 | 15 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | peak_giveback_bps | 2 | 1.7779 | 1.8252 | 1.8726 | 2 | 1.5371 | 97 | 96 | 15 |

crypto:

| entry_variant | device | setting | component | metric_name | sym | est_min | est_med | est_max | ci_ex0 | mde_med | cfill | cclose | efftr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | RANGE_SCALE | decay_bps | 25 | 0.0000 | 39.3650 | 1040.4229 | 98 | 10.7243 | 58426 | 58413 | 24940 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | RANGE_SCALE | holding_efficiency | 25 | -16.0977 | -0.2913 | 1.0673 | 20 | 0.7730 | 58426 | 58413 | 24940 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | RANGE_SCALE | opportunity_duration | 25 | 0.0000 | 1.0206 | 2.8924 | 96 | 0.2120 | 58426 | 58413 | 24940 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | RANGE_SCALE | outcome_by_time_bps | 25 | -78.0058 | 1.3491 | 382.5070 | 5 | 13.0121 | 58426 | 58413 | 24940 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | SHOCK | decay_bps | 25 | 5.5155 | 17.1656 | 126.8173 | 20 | 9.4359 | 19365 | 19363 | 8340 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | SHOCK | holding_efficiency | 25 | -15.2276 | -0.7094 | -0.2153 | 3 | 1.5463 | 19365 | 19363 | 8340 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | SHOCK | opportunity_duration | 25 | 0.0004 | 0.6817 | 1.0041 | 24 | 0.1545 | 19365 | 19363 | 8340 |
| E_CLOSE | HOLD | STATE_LOW_4_HIGH_12 | SHOCK | outcome_by_time_bps | 25 | -61.7943 | -0.7645 | 40.6181 | 0 | 11.7918 | 19365 | 19363 | 8340 |
| E_CLOSE | SIZE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | concentration | 25 | -0.0209 | 0.0009 | 0.0270 | 22 | 0.0029 | 114636 | 114633 | 28908 |
| E_CLOSE | SIZE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | drawdown_bps | 25 | -3077.6611 | 1430.3938 | 11517.7221 | 6 | 4294.5995 | 114636 | 114633 | 28908 |
| E_CLOSE | SIZE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | risk_dispersion | 25 | -369.5538 | -20.6727 | 37.3187 | 50 | 19.9261 | 114636 | 114633 | 28908 |
| E_CLOSE | SIZE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | tail_loss_bps | 25 | -703.0254 | -49.8314 | 43.0949 | 34 | 50.9476 | 114636 | 114633 | 28908 |
| E_CLOSE | SIZE | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | concentration | 25 | -0.0095 | 0.0020 | 0.0304 | 5 | 0.0037 | 38212 | 38211 | 9636 |
| E_CLOSE | SIZE | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | drawdown_bps | 25 | 435.4882 | 3550.2260 | 10772.7652 | 13 | 2904.2073 | 38212 | 38211 | 9636 |
| E_CLOSE | SIZE | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | risk_dispersion | 25 | -193.5358 | -64.0506 | -28.2219 | 25 | 15.6836 | 38212 | 38211 | 9636 |
| E_CLOSE | SIZE | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | tail_loss_bps | 25 | -625.7462 | -120.6692 | -50.5360 | 23 | 43.8187 | 38212 | 38211 | 9636 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | adverse_excursion_bps | 18 | -5.1813 | 28.1202 | 204.7011 | 17 | 17.2703 | 1560 | 1547 | 413 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | loss_severity_bps | 18 | -200.4728 | -28.3883 | 4.3298 | 20 | 16.7581 | 1560 | 1547 | 413 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | recovery_after_stop_bps | 18 | -115.9592 | -5.4312 | 97.6218 | 5 | 30.7471 | 1560 | 1547 | 413 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | stop_rate | 18 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 1560 | 1547 | 413 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | adverse_excursion_bps | 19 | -32.3989 | 3.2497 | 16.5667 | 5 | 10.0922 | 1536 | 1525 | 372 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | loss_severity_bps | 19 | -14.5158 | -5.0893 | 29.4465 | 5 | 7.6320 | 1536 | 1525 | 372 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | recovery_after_stop_bps | 19 | -55.5067 | -3.0247 | 60.8460 | 3 | 17.4913 | 1536 | 1525 | 372 |
| E_CLOSE | STOP | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | stop_rate | 19 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 1536 | 1525 | 372 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | missed_excess_bps | 22 | -267.6150 | -19.4208 | 59.1825 | 25 | 22.0105 | 1307 | 1287 | 389 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | reach_rate | 22 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 1307 | 1287 | 389 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | realised_capture_bps | 22 | -59.1825 | 32.6929 | 341.0774 | 40 | 19.7994 | 1307 | 1287 | 389 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | time_to_target | 22 | -0.0583 | 2.8592 | 256.9232 | 34 | 2.3661 | 1307 | 1287 | 389 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | missed_excess_bps | 23 | -75.4419 | -9.8652 | 9.1232 | 9 | 10.0413 | 1003 | 993 | 260 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | reach_rate | 23 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 1003 | 993 | 260 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | realised_capture_bps | 23 | -21.8108 | 8.9646 | 45.3844 | 12 | 9.1620 | 1003 | 993 | 260 |
| E_CLOSE | TARGET | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | time_to_target | 23 | -1407.8250 | 0.3484 | 10.2873 | 8 | 1.2944 | 1003 | 993 | 260 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | favourable_excursion_captured | 21 | -0.0864 | 0.0086 | 0.6552 | 9 | 0.0724 | 1013 | 994 | 314 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | loss_tail_bps | 21 | -9.8573 | 0.0000 | 150.1581 | 10 | 7.7091 | 1013 | 994 | 314 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | peak_giveback_bps | 21 | -12.8298 | 37.3687 | 237.1779 | 29 | 19.2170 | 1013 | 994 | 314 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | favourable_excursion_captured | 22 | -0.3176 | 0.0012 | 0.2318 | 6 | 0.0808 | 1038 | 1030 | 275 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | loss_tail_bps | 22 | -60.3242 | 0.0000 | 13.0294 | 4 | 2.0001 | 1038 | 1030 | 275 |
| E_CLOSE | TRAIL | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | peak_giveback_bps | 22 | -58.2437 | 7.1822 | 44.9737 | 10 | 9.0867 | 1038 | 1030 | 275 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | RANGE_SCALE | decay_bps | 25 | -4.0250 | 31.7056 | 216.2041 | 91 | 10.4339 | 48418 | 48412 | 20143 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | RANGE_SCALE | holding_efficiency | 25 | -1.6915 | -0.0571 | 0.9588 | 21 | 0.6531 | 48418 | 48412 | 20143 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | RANGE_SCALE | opportunity_duration | 25 | 0.0000 | 0.9258 | 1.8475 | 93 | 0.2179 | 48418 | 48412 | 20143 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | RANGE_SCALE | outcome_by_time_bps | 25 | -110.2797 | 0.8325 | 61.5221 | 7 | 14.0243 | 48418 | 48412 | 20143 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | SHOCK | decay_bps | 25 | 8.0271 | 17.8707 | 90.6111 | 18 | 10.5555 | 15195 | 15194 | 6757 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | SHOCK | holding_efficiency | 25 | -1.1019 | -0.2095 | 1.1600 | 4 | 1.1101 | 15195 | 15194 | 6757 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | SHOCK | opportunity_duration | 25 | 0.1259 | 0.6295 | 0.8184 | 22 | 0.1741 | 15195 | 15194 | 6757 |
| E_TOUCH | HOLD | STATE_LOW_4_HIGH_12 | SHOCK | outcome_by_time_bps | 25 | -123.1007 | 1.0785 | 12.1411 | 3 | 12.4354 | 15195 | 15194 | 6757 |
| E_TOUCH | SIZE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | concentration | 25 | -0.0148 | 0.0011 | 0.0516 | 25 | 0.0025 | 129231 | 129231 | 28911 |
| E_TOUCH | SIZE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | drawdown_bps | 25 | -5715.8148 | 1846.5658 | 13442.9657 | 13 | 4487.3773 | 129231 | 129231 | 28911 |
| E_TOUCH | SIZE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | risk_dispersion | 25 | -366.5166 | -22.5222 | 15.1731 | 53 | 16.5204 | 129231 | 129231 | 28911 |
| E_TOUCH | SIZE | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | tail_loss_bps | 25 | -1526.7982 | -60.6414 | 43.1951 | 45 | 49.9056 | 129231 | 129231 | 28911 |
| E_TOUCH | SIZE | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | concentration | 25 | -0.0131 | 0.0010 | 0.0359 | 4 | 0.0027 | 43077 | 43077 | 9637 |
| E_TOUCH | SIZE | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | drawdown_bps | 25 | -1470.9673 | 3968.9181 | 10359.6251 | 12 | 4451.8114 | 43077 | 43077 | 9637 |
| E_TOUCH | SIZE | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | risk_dispersion | 25 | -207.3905 | -66.1726 | -27.4676 | 25 | 17.8213 | 43077 | 43077 | 9637 |
| E_TOUCH | SIZE | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | tail_loss_bps | 25 | -1058.5292 | -137.8324 | -44.5106 | 23 | 56.7337 | 43077 | 43077 | 9637 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | adverse_excursion_bps | 17 | -25.9702 | 28.0426 | 93.5417 | 13 | 29.6512 | 1145 | 1134 | 290 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | loss_severity_bps | 17 | -91.4136 | -22.6662 | 12.0757 | 14 | 28.5247 | 1145 | 1134 | 290 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | recovery_after_stop_bps | 17 | -52.7613 | -13.0278 | 132.3148 | 2 | 37.4651 | 1145 | 1134 | 290 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | stop_rate | 17 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 1145 | 1134 | 290 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | adverse_excursion_bps | 19 | -156.4866 | 5.1439 | 15.0736 | 4 | 9.6338 | 1689 | 1681 | 322 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | loss_severity_bps | 19 | -13.1494 | -3.9958 | 28.9962 | 3 | 7.8708 | 1689 | 1681 | 322 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | recovery_after_stop_bps | 19 | -26.7384 | 2.0744 | 79.1091 | 1 | 21.7954 | 1689 | 1681 | 322 |
| E_TOUCH | STOP | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | stop_rate | 19 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 1689 | 1681 | 322 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | missed_excess_bps | 16 | -196.2365 | -17.4221 | 23.3525 | 21 | 17.2929 | 1329 | 1315 | 372 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | reach_rate | 16 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 1329 | 1315 | 372 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | realised_capture_bps | 16 | -21.7332 | 30.2880 | 271.4577 | 33 | 15.7387 | 1329 | 1315 | 372 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | time_to_target | 16 | -42.8333 | 2.4542 | 190.6667 | 27 | 2.2479 | 1329 | 1315 | 372 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | missed_excess_bps | 20 | -837.3733 | -3.4703 | 18.7055 | 8 | 9.9488 | 1310 | 1304 | 274 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | reach_rate | 20 | 0.0000 | 0.0000 | 0.0000 | 0 | 0.0000 | 1310 | 1304 | 274 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | realised_capture_bps | 20 | -21.8102 | 7.4156 | 46.8577 | 12 | 9.1663 | 1310 | 1304 | 274 |
| E_TOUCH | TARGET | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | time_to_target | 20 | -28.4194 | 0.9688 | 84.2417 | 6 | 2.5935 | 1310 | 1304 | 274 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | favourable_excursion_captured | 19 | -0.2323 | 0.0110 | 0.1948 | 6 | 0.0892 | 844 | 838 | 253 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | loss_tail_bps | 19 | -12.1982 | 0.0000 | 305.6905 | 12 | 5.5575 | 844 | 838 | 253 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150_ON_RANGE_SCALE | RANGE_SCALE | peak_giveback_bps | 19 | -5.8259 | 45.3370 | 200.6584 | 23 | 25.8728 | 844 | 838 | 253 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | favourable_excursion_captured | 20 | -0.3514 | -0.0383 | 0.0880 | 6 | 0.0705 | 1195 | 1188 | 251 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | loss_tail_bps | 20 | -27.2171 | 0.0000 | 0.0000 | 3 | 2.0392 | 1195 | 1188 | 251 |
| E_TOUCH | TRAIL | STATE_LOW_075_HIGH_150_ON_SHOCK | SHOCK | peak_giveback_bps | 20 | -768.8576 | 8.1277 | 139.0709 | 11 | 8.9972 | 1195 | 1188 | 251 |

### 6.4 Lens B — device combinations (`MANAGEMENT_DEVICE_COMBINATION`)

`TARGET+STOP`, `TARGET+STOP+HOLD`, `TRAIL+HOLD`, all at `M1.00`.

ctrader:

| entry_variant | device | setting | component | metric_name | sym | est_min | est_med | est_max | ci_ex0 | mde_med | cfill | cclose | efftr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E_CLOSE | TARGET+STOP | M1.00 | RANGE_SCALE | adverse_excursion_bps | 3 | -40.6814 | -36.3269 | -5.7696 | 3 | 27.6039 | 570 | 567 | 120 |
| E_CLOSE | TARGET+STOP | M1.00 | RANGE_SCALE | loss_severity_bps | 3 |  |  |  | 0 |  | 570 | 567 | 120 |
| E_CLOSE | TARGET+STOP | M1.00 | RANGE_SCALE | missed_excess_bps | 3 | 2.6681 | 6.3450 | 6.4021 | 3 | 1.5090 | 570 | 567 | 120 |
| E_CLOSE | TARGET+STOP | M1.00 | RANGE_SCALE | reach_rate | 3 | -0.5714 | -0.5366 | -0.5028 | 3 | 0.0841 | 570 | 567 | 120 |
| E_CLOSE | TARGET+STOP | M1.00 | RANGE_SCALE | realised_capture_bps | 3 | -8.3358 | -7.7245 | -3.7429 | 3 | 1.3910 | 570 | 567 | 120 |
| E_CLOSE | TARGET+STOP | M1.00 | RANGE_SCALE | recovery_after_stop_bps | 3 |  |  |  | 0 |  | 570 | 567 | 120 |
| E_CLOSE | TARGET+STOP | M1.00 | RANGE_SCALE | stop_rate | 3 | 0.5028 | 0.5366 | 0.5714 | 3 | 0.0745 | 570 | 567 | 120 |
| E_CLOSE | TARGET+STOP | M1.00 | RANGE_SCALE | time_to_target | 3 | -76.5402 | -57.3827 | -8.1305 | 3 | 82.5404 | 570 | 567 | 120 |
| E_CLOSE | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | adverse_excursion_bps | 3 | -40.6814 | -36.3790 | -5.7696 | 3 | 27.5705 | 570 | 567 | 120 |
| E_CLOSE | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | decay_bps | 3 | 1.8830 | 5.2585 | 7.4040 | 3 | 1.4920 | 570 | 567 | 120 |
| E_CLOSE | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | holding_efficiency | 3 | -3.0625 | -2.9749 | -2.8872 | 3 | 0.9328 | 570 | 567 | 120 |
| E_CLOSE | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | loss_severity_bps | 3 |  |  |  | 0 |  | 570 | 567 | 120 |
| E_CLOSE | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | missed_excess_bps | 3 | 2.6681 | 6.2597 | 6.5159 | 3 | 1.5090 | 570 | 567 | 120 |
| E_CLOSE | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | opportunity_duration | 3 | -52.1336 | -37.8070 | -6.2861 | 3 | 54.6664 | 570 | 567 | 120 |
| E_CLOSE | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | outcome_by_time_bps | 3 | -8.4962 | -7.6738 | -3.7429 | 3 | 1.3910 | 570 | 567 | 120 |
| E_CLOSE | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | reach_rate | 3 | -0.5714 | -0.5488 | -0.5056 | 3 | 0.0835 | 570 | 567 | 120 |
| E_CLOSE | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | realised_capture_bps | 3 | -8.4962 | -7.6738 | -3.7429 | 3 | 1.3910 | 570 | 567 | 120 |
| E_CLOSE | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | recovery_after_stop_bps | 3 |  |  |  | 0 |  | 570 | 567 | 120 |
| E_CLOSE | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | stop_rate | 3 | 0.4944 | 0.5366 | 0.5714 | 3 | 0.0745 | 570 | 567 | 120 |
| E_CLOSE | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | time_to_target | 3 | -76.7086 | -57.6698 | -8.1305 | 3 | 82.3931 | 570 | 567 | 120 |
| E_CLOSE | TRAIL+HOLD | M1.00 | RANGE_SCALE | decay_bps | 3 | 3.6547 | 13.0107 | 13.6515 | 3 | 4.5207 | 393 | 392 | 99 |
| E_CLOSE | TRAIL+HOLD | M1.00 | RANGE_SCALE | favourable_excursion_captured | 3 | -5.7128 | -4.3479 | -3.4530 | 3 | 2.8800 | 393 | 392 | 99 |
| E_CLOSE | TRAIL+HOLD | M1.00 | RANGE_SCALE | holding_efficiency | 3 | -5.7128 | -4.3479 | -3.4530 | 3 | 2.8800 | 393 | 392 | 99 |
| E_CLOSE | TRAIL+HOLD | M1.00 | RANGE_SCALE | loss_tail_bps | 3 | -72.8439 | -49.9224 | -22.2157 | 3 | 24.7263 | 393 | 392 | 99 |
| E_CLOSE | TRAIL+HOLD | M1.00 | RANGE_SCALE | opportunity_duration | 3 | -161.3198 | -49.1949 | -5.3448 | 3 | 65.8803 | 393 | 392 | 99 |
| E_CLOSE | TRAIL+HOLD | M1.00 | RANGE_SCALE | outcome_by_time_bps | 3 | -16.1722 | -8.2982 | -4.5328 | 3 | 5.5650 | 393 | 392 | 99 |
| E_CLOSE | TRAIL+HOLD | M1.00 | RANGE_SCALE | peak_giveback_bps | 3 | 3.6547 | 13.0107 | 13.6515 | 3 | 4.5207 | 393 | 392 | 99 |
| E_TOUCH | TARGET+STOP | M1.00 | RANGE_SCALE | adverse_excursion_bps | 2 | -42.7052 | -38.6120 | -34.5188 | 2 | 23.6180 | 588 | 586 | 102 |
| E_TOUCH | TARGET+STOP | M1.00 | RANGE_SCALE | loss_severity_bps | 2 |  |  |  | 0 |  | 588 | 586 | 102 |
| E_TOUCH | TARGET+STOP | M1.00 | RANGE_SCALE | missed_excess_bps | 2 | 6.0302 | 6.3964 | 6.7626 | 2 | 1.0703 | 588 | 586 | 102 |
| E_TOUCH | TARGET+STOP | M1.00 | RANGE_SCALE | reach_rate | 2 | -0.5379 | -0.5230 | -0.5081 | 2 | 0.0555 | 588 | 586 | 102 |
| E_TOUCH | TARGET+STOP | M1.00 | RANGE_SCALE | realised_capture_bps | 2 | -8.0502 | -7.6376 | -7.2251 | 2 | 1.1656 | 588 | 586 | 102 |
| E_TOUCH | TARGET+STOP | M1.00 | RANGE_SCALE | recovery_after_stop_bps | 2 |  |  |  | 0 |  | 588 | 586 | 102 |
| E_TOUCH | TARGET+STOP | M1.00 | RANGE_SCALE | stop_rate | 2 | 0.5081 | 0.5230 | 0.5379 | 2 | 0.0508 | 588 | 586 | 102 |
| E_TOUCH | TARGET+STOP | M1.00 | RANGE_SCALE | time_to_target | 2 | -67.8020 | -67.2154 | -66.6287 | 2 | 71.1443 | 588 | 586 | 102 |
| E_TOUCH | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | adverse_excursion_bps | 2 | -42.7412 | -38.6300 | -34.5188 | 2 | 23.5098 | 589 | 587 | 102 |
| E_TOUCH | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | decay_bps | 2 | 5.3840 | 6.1689 | 6.9538 | 2 | 1.0149 | 589 | 587 | 102 |
| E_TOUCH | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | holding_efficiency | 2 | -3.0505 | -3.0505 | -3.0505 | 2 | 0.6155 | 589 | 587 | 102 |
| E_TOUCH | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | loss_severity_bps | 2 |  |  |  | 0 |  | 589 | 587 | 102 |
| E_TOUCH | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | missed_excess_bps | 2 | 6.1160 | 6.4408 | 6.7655 | 2 | 0.9939 | 589 | 587 | 102 |
| E_TOUCH | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | opportunity_duration | 2 | -46.0780 | -44.9666 | -43.8552 | 2 | 47.9879 | 589 | 587 | 102 |
| E_TOUCH | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | outcome_by_time_bps | 2 | -8.1825 | -7.7618 | -7.3410 | 2 | 1.1102 | 589 | 587 | 102 |
| E_TOUCH | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | reach_rate | 2 | -0.5487 | -0.5324 | -0.5161 | 2 | 0.0533 | 589 | 587 | 102 |
| E_TOUCH | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | realised_capture_bps | 2 | -8.1825 | -7.7618 | -7.3410 | 2 | 1.1102 | 589 | 587 | 102 |
| E_TOUCH | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | recovery_after_stop_bps | 2 |  |  |  | 0 |  | 589 | 587 | 102 |
| E_TOUCH | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | stop_rate | 2 | 0.5032 | 0.5206 | 0.5379 | 2 | 0.0494 | 589 | 587 | 102 |
| E_TOUCH | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | time_to_target | 2 | -68.2906 | -67.5340 | -66.7774 | 2 | 71.3469 | 589 | 587 | 102 |
| E_TOUCH | TRAIL+HOLD | M1.00 | RANGE_SCALE | decay_bps | 2 | 10.5746 | 13.1232 | 15.6718 | 2 | 4.4500 | 494 | 494 | 96 |
| E_TOUCH | TRAIL+HOLD | M1.00 | RANGE_SCALE | favourable_excursion_captured | 2 | -4.0968 | -3.5304 | -2.9641 | 2 | 3.1177 | 494 | 494 | 96 |
| E_TOUCH | TRAIL+HOLD | M1.00 | RANGE_SCALE | holding_efficiency | 2 | -4.0968 | -3.5304 | -2.9641 | 2 | 3.1177 | 494 | 494 | 96 |
| E_TOUCH | TRAIL+HOLD | M1.00 | RANGE_SCALE | loss_tail_bps | 2 | -74.2663 | -67.1072 | -59.9482 | 2 | 25.6690 | 494 | 494 | 96 |
| E_TOUCH | TRAIL+HOLD | M1.00 | RANGE_SCALE | opportunity_duration | 2 | -131.4204 | -70.4772 | -9.5340 | 2 | 108.4813 | 494 | 494 | 96 |
| E_TOUCH | TRAIL+HOLD | M1.00 | RANGE_SCALE | outcome_by_time_bps | 2 | -10.3665 | -8.7397 | -7.1129 | 2 | 5.8225 | 494 | 494 | 96 |
| E_TOUCH | TRAIL+HOLD | M1.00 | RANGE_SCALE | peak_giveback_bps | 2 | 10.5746 | 13.1232 | 15.6718 | 2 | 4.4500 | 494 | 494 | 96 |

crypto:

| entry_variant | device | setting | component | metric_name | sym | est_min | est_med | est_max | ci_ex0 | mde_med | cfill | cclose | efftr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E_CLOSE | TARGET+STOP | M1.00 | RANGE_SCALE | adverse_excursion_bps | 25 | -611.7340 | -178.0571 | -44.9732 | 23 | 113.4761 | 3335 | 3311 | 737 |
| E_CLOSE | TARGET+STOP | M1.00 | RANGE_SCALE | loss_severity_bps | 25 |  |  |  | 0 |  | 3335 | 3311 | 737 |
| E_CLOSE | TARGET+STOP | M1.00 | RANGE_SCALE | missed_excess_bps | 25 | 9.8755 | 48.0968 | 155.9518 | 22 | 21.8428 | 3335 | 3311 | 737 |
| E_CLOSE | TARGET+STOP | M1.00 | RANGE_SCALE | reach_rate | 25 | -0.6667 | -0.5541 | -0.3684 | 25 | 0.0772 | 3335 | 3311 | 737 |
| E_CLOSE | TARGET+STOP | M1.00 | RANGE_SCALE | realised_capture_bps | 25 | -173.8006 | -64.4380 | -24.8149 | 24 | 15.5727 | 3335 | 3311 | 737 |
| E_CLOSE | TARGET+STOP | M1.00 | RANGE_SCALE | recovery_after_stop_bps | 25 |  |  |  | 0 |  | 3335 | 3311 | 737 |
| E_CLOSE | TARGET+STOP | M1.00 | RANGE_SCALE | stop_rate | 25 | 0.3684 | 0.5541 | 0.6667 | 25 | 0.0752 | 3335 | 3311 | 737 |
| E_CLOSE | TARGET+STOP | M1.00 | RANGE_SCALE | time_to_target | 25 | -337.6125 | -28.9660 | -1.5626 | 25 | 33.0435 | 3335 | 3311 | 737 |
| E_CLOSE | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | adverse_excursion_bps | 25 | -611.7340 | -178.0571 | -44.9732 | 23 | 113.4761 | 3336 | 3312 | 737 |
| E_CLOSE | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | decay_bps | 25 | 9.0224 | 49.7364 | 150.0267 | 24 | 23.4445 | 3336 | 3312 | 737 |
| E_CLOSE | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | holding_efficiency | 25 | -3.7993 | -2.8754 | -1.8173 | 22 | 1.2302 | 3336 | 3312 | 737 |
| E_CLOSE | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | loss_severity_bps | 25 |  |  |  | 0 |  | 3336 | 3312 | 737 |
| E_CLOSE | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | missed_excess_bps | 25 | 9.8755 | 47.8928 | 155.9518 | 22 | 21.8428 | 3336 | 3312 | 737 |
| E_CLOSE | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | opportunity_duration | 25 | -314.3708 | -22.6458 | -1.4278 | 25 | 26.7161 | 3336 | 3312 | 737 |
| E_CLOSE | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | outcome_by_time_bps | 25 | -173.8006 | -64.4380 | -24.8149 | 24 | 15.5727 | 3336 | 3312 | 737 |
| E_CLOSE | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | reach_rate | 25 | -0.6667 | -0.5584 | -0.3684 | 25 | 0.0772 | 3336 | 3312 | 737 |
| E_CLOSE | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | realised_capture_bps | 25 | -173.8006 | -64.4380 | -24.8149 | 24 | 15.5727 | 3336 | 3312 | 737 |
| E_CLOSE | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | recovery_after_stop_bps | 25 |  |  |  | 0 |  | 3336 | 3312 | 737 |
| E_CLOSE | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | stop_rate | 25 | 0.3684 | 0.5455 | 0.6667 | 25 | 0.0752 | 3336 | 3312 | 737 |
| E_CLOSE | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | time_to_target | 25 | -337.6125 | -28.9660 | -1.5626 | 25 | 33.0024 | 3336 | 3312 | 737 |
| E_CLOSE | TRAIL+HOLD | M1.00 | RANGE_SCALE | decay_bps | 25 | 9.3377 | 67.7521 | 286.2843 | 24 | 35.7760 | 3048 | 3028 | 795 |
| E_CLOSE | TRAIL+HOLD | M1.00 | RANGE_SCALE | favourable_excursion_captured | 25 | -5.9902 | -2.4257 | -1.0084 | 25 | 1.8017 | 3048 | 3028 | 795 |
| E_CLOSE | TRAIL+HOLD | M1.00 | RANGE_SCALE | holding_efficiency | 25 | -5.9902 | -2.4257 | -1.0084 | 25 | 1.8017 | 3048 | 3028 | 795 |
| E_CLOSE | TRAIL+HOLD | M1.00 | RANGE_SCALE | loss_tail_bps | 25 | -1380.0976 | -307.6335 | -99.9384 | 25 | 195.4578 | 3048 | 3028 | 795 |
| E_CLOSE | TRAIL+HOLD | M1.00 | RANGE_SCALE | opportunity_duration | 25 | -189.3569 | -15.8693 | -0.6347 | 21 | 23.6466 | 3048 | 3028 | 795 |
| E_CLOSE | TRAIL+HOLD | M1.00 | RANGE_SCALE | outcome_by_time_bps | 25 | -190.7754 | -57.7531 | 14.3701 | 21 | 47.2900 | 3048 | 3028 | 795 |
| E_CLOSE | TRAIL+HOLD | M1.00 | RANGE_SCALE | peak_giveback_bps | 25 | 9.3377 | 67.7521 | 286.2843 | 24 | 35.7760 | 3048 | 3028 | 795 |
| E_TOUCH | TARGET+STOP | M1.00 | RANGE_SCALE | adverse_excursion_bps | 25 | -614.5980 | -150.8307 | 92.4732 | 23 | 110.5706 | 4285 | 4262 | 782 |
| E_TOUCH | TARGET+STOP | M1.00 | RANGE_SCALE | loss_severity_bps | 25 |  |  |  | 0 |  | 4285 | 4262 | 782 |
| E_TOUCH | TARGET+STOP | M1.00 | RANGE_SCALE | missed_excess_bps | 25 | 7.1734 | 53.5657 | 147.2287 | 22 | 16.9302 | 4285 | 4262 | 782 |
| E_TOUCH | TARGET+STOP | M1.00 | RANGE_SCALE | reach_rate | 25 | -0.6216 | -0.5411 | -0.4000 | 25 | 0.0682 | 4285 | 4262 | 782 |
| E_TOUCH | TARGET+STOP | M1.00 | RANGE_SCALE | realised_capture_bps | 25 | -158.6763 | -69.7819 | -25.9962 | 25 | 14.8877 | 4285 | 4262 | 782 |
| E_TOUCH | TARGET+STOP | M1.00 | RANGE_SCALE | recovery_after_stop_bps | 25 |  |  |  | 0 |  | 4285 | 4262 | 782 |
| E_TOUCH | TARGET+STOP | M1.00 | RANGE_SCALE | stop_rate | 25 | 0.4000 | 0.5411 | 0.6216 | 25 | 0.0636 | 4285 | 4262 | 782 |
| E_TOUCH | TARGET+STOP | M1.00 | RANGE_SCALE | time_to_target | 25 | -85.5487 | -24.0033 | 0.3433 | 24 | 25.1631 | 4285 | 4262 | 782 |
| E_TOUCH | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | adverse_excursion_bps | 25 | -614.5980 | -150.8307 | 92.4732 | 23 | 110.5706 | 4285 | 4262 | 782 |
| E_TOUCH | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | decay_bps | 25 | 11.8115 | 56.3736 | 160.8561 | 22 | 19.8800 | 4285 | 4262 | 782 |
| E_TOUCH | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | holding_efficiency | 25 | -4.4835 | -2.6788 | -0.6884 | 21 | 0.9510 | 4285 | 4262 | 782 |
| E_TOUCH | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | loss_severity_bps | 25 |  |  |  | 0 |  | 4285 | 4262 | 782 |
| E_TOUCH | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | missed_excess_bps | 25 | 7.1734 | 53.4040 | 147.2287 | 22 | 16.9302 | 4285 | 4262 | 782 |
| E_TOUCH | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | opportunity_duration | 25 | -75.8097 | -23.0526 | 0.1917 | 25 | 23.1890 | 4285 | 4262 | 782 |
| E_TOUCH | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | outcome_by_time_bps | 25 | -158.6763 | -70.0117 | -25.9750 | 25 | 14.8877 | 4285 | 4262 | 782 |
| E_TOUCH | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | reach_rate | 25 | -0.6216 | -0.5411 | -0.4000 | 25 | 0.0682 | 4285 | 4262 | 782 |
| E_TOUCH | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | realised_capture_bps | 25 | -158.6763 | -70.0117 | -25.9750 | 25 | 14.8877 | 4285 | 4262 | 782 |
| E_TOUCH | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | recovery_after_stop_bps | 25 |  |  |  | 0 |  | 4285 | 4262 | 782 |
| E_TOUCH | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | stop_rate | 25 | 0.4000 | 0.5385 | 0.6216 | 25 | 0.0636 | 4285 | 4262 | 782 |
| E_TOUCH | TARGET+STOP+HOLD | M1.00 | RANGE_SCALE | time_to_target | 25 | -85.5487 | -24.0033 | 0.3433 | 24 | 25.1631 | 4285 | 4262 | 782 |
| E_TOUCH | TRAIL+HOLD | M1.00 | RANGE_SCALE | decay_bps | 25 | 20.1200 | 70.4097 | 454.0919 | 25 | 30.5884 | 3527 | 3512 | 807 |
| E_TOUCH | TRAIL+HOLD | M1.00 | RANGE_SCALE | favourable_excursion_captured | 25 | -3.9427 | -2.7615 | -0.5410 | 24 | 2.2408 | 3527 | 3512 | 807 |
| E_TOUCH | TRAIL+HOLD | M1.00 | RANGE_SCALE | holding_efficiency | 25 | -3.9427 | -2.7615 | -0.5410 | 24 | 2.2408 | 3527 | 3512 | 807 |
| E_TOUCH | TRAIL+HOLD | M1.00 | RANGE_SCALE | loss_tail_bps | 25 | -1476.4142 | -277.6808 | -130.2016 | 25 | 200.3640 | 3527 | 3512 | 807 |
| E_TOUCH | TRAIL+HOLD | M1.00 | RANGE_SCALE | opportunity_duration | 25 | -91.7829 | -19.3663 | 0.3778 | 20 | 22.0052 | 3527 | 3512 | 807 |
| E_TOUCH | TRAIL+HOLD | M1.00 | RANGE_SCALE | outcome_by_time_bps | 25 | -181.5635 | -48.1402 | -19.8122 | 19 | 40.7757 | 3527 | 3512 | 807 |
| E_TOUCH | TRAIL+HOLD | M1.00 | RANGE_SCALE | peak_giveback_bps | 25 | 20.1200 | 70.4097 | 454.0919 | 25 | 30.5884 | 3527 | 3512 | 807 |

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

| control | entry_variant | magnitude_bin | rows | est_min | est_med | est_max | ci_excl | mde_med | count | eff | identical_to_raw |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MAGNITUDE_MATCH | E_CLOSE | 0.0000 | 192 | -1.7207 | -0.1528 | 1.1040 | 8 | 1.0374 | 696448.0000 | 46272.0000 | 0 |
| MAGNITUDE_MATCH | E_CLOSE | 1.0000 | 192 | -1.0706 | 0.1481 | 1.6469 | 4 | 1.1320 | 696384.0000 | 56704.0000 | 0 |
| MAGNITUDE_MATCH | E_CLOSE | 2.0000 | 192 | -1.7880 | -0.1019 | 2.2472 | 25 | 1.0887 | 696384.0000 | 56448.0000 | 0 |
| MAGNITUDE_MATCH | E_CLOSE | 3.0000 | 192 | -1.6976 | -0.0592 | 2.8782 | 2 | 1.3246 | 696256.0000 | 53504.0000 | 0 |
| MAGNITUDE_MATCH | E_TOUCH | 0.0000 | 192 | -0.9616 | 0.0562 | 1.0240 | 0 | 1.1815 | 696448.0000 | 46272.0000 | 0 |
| MAGNITUDE_MATCH | E_TOUCH | 1.0000 | 192 | -1.4553 | -0.2736 | 0.5356 | 3 | 1.1165 | 696384.0000 | 56704.0000 | 0 |
| MAGNITUDE_MATCH | E_TOUCH | 2.0000 | 192 | -4.4752 | -0.0360 | 1.2091 | 17 | 1.1286 | 696384.0000 | 56448.0000 | 0 |
| MAGNITUDE_MATCH | E_TOUCH | 3.0000 | 192 | -1.4167 | 0.0008 | 2.4001 | 5 | 1.2556 | 696256.0000 | 53504.0000 | 0 |
| TIME_DERANGEMENT | E_CLOSE |  | 192 | -0.1496 | -0.0111 | 0.1808 | 3 | 0.1792 | 2860800.0000 | 142656.0000 | 192 |
| TIME_DERANGEMENT | E_TOUCH |  | 192 | -0.3654 | 0.0400 | 0.5963 | 17 | 0.2161 | 2860800.0000 | 142656.0000 | 192 |

crypto controls:

| control | entry_variant | magnitude_bin | rows | est_min | est_med | est_max | ci_excl | mde_med | count | eff | identical_to_raw |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MAGNITUDE_MATCH | E_CLOSE | 0.0000 | 1600 | -77.3138 | 0.3949 | 207.0935 | 113 | 6.3055 | 3494080.0000 | 230976.0000 | 0 |
| MAGNITUDE_MATCH | E_CLOSE | 1.0000 | 1600 | -763.7878 | 0.4383 | 110.5226 | 138 | 7.5999 | 3493120.0000 | 246208.0000 | 0 |
| MAGNITUDE_MATCH | E_CLOSE | 2.0000 | 1600 | -193.5866 | -0.2751 | 293.0531 | 89 | 8.1217 | 3493632.0000 | 243840.0000 | 0 |
| MAGNITUDE_MATCH | E_CLOSE | 3.0000 | 1600 | -272.6716 | 0.2050 | 717.5251 | 106 | 10.6738 | 3492736.0000 | 218112.0000 | 0 |
| MAGNITUDE_MATCH | E_TOUCH | 0.0000 | 1600 | -110.9980 | 0.1647 | 416.9914 | 76 | 5.9571 | 3494080.0000 | 230976.0000 | 0 |
| MAGNITUDE_MATCH | E_TOUCH | 1.0000 | 1600 | -348.8984 | -1.0284 | 471.0359 | 181 | 8.1681 | 3493120.0000 | 246208.0000 | 0 |
| MAGNITUDE_MATCH | E_TOUCH | 2.0000 | 1600 | -471.9208 | 0.6628 | 206.5347 | 104 | 7.9523 | 3493632.0000 | 243840.0000 | 0 |
| MAGNITUDE_MATCH | E_TOUCH | 3.0000 | 1600 | -286.3440 | -0.0580 | 577.5467 | 102 | 11.3813 | 3492736.0000 | 218112.0000 | 0 |
| TIME_DERANGEMENT | E_CLOSE |  | 1600 | -23.2408 | -0.0065 | 9.5404 | 38 | 1.6843 | 14791744.0000 | 616768.0000 | 1600 |
| TIME_DERANGEMENT | E_TOUCH |  | 1600 | -15.4904 | 0.1323 | 47.1952 | 90 | 1.9339 | 14791744.0000 | 616768.0000 | 1600 |

## 8. Selection checks

`selection_checks.parquet` (390 ctrader / 3,250 crypto rows). `sign_share_difference` sits
tightly around 0.083–0.099 in every component and both variants; `excluded_mean_median_gap` is
0.0 everywhere — consistent with excluded origins carrying outcome 0.0 by construction.
`payoff_scale_ratio` is **null on every row in both universes** (0 non-null of 390 and of 3,250):
an unpopulated field, reported here rather than silently omitted.

ctrader:

| entry_variant | component | rows | selected_n | excluded_n | payoff_scale_ratio_med | sign_share_difference_med | excluded_mean_median_gap_med | payoff_nonnull |
|---|---|---|---|---|---|---|---|---|
| E_CLOSE | LEVEL_FORECAST_K12 | 24 | 195305 | 162295 |  | 0.0882 | 0.0000 | 0 |
| E_CLOSE | LEVEL_FORECAST_K4 | 24 | 195415 | 162185 |  | 0.0882 | 0.0000 | 0 |
| E_CLOSE | LEVEL_NOW | 24 | 326673 | 30927 |  | 0.0882 | 0.0000 | 0 |
| E_CLOSE | RANGE_SCALE | 24 | 328119 | 29481 |  | 0.0874 | 0.0000 | 0 |
| E_CLOSE | SHOCK | 24 | 327537 | 30063 |  | 0.0903 | 0.0000 | 0 |
| E_CLOSE | SWING_GT_CUR | 24 | 319529 | 38071 |  | 0.0885 | 0.0000 | 0 |
| E_CLOSE | SWING_SCALE | 24 | 319660 | 37940 |  | 0.0884 | 0.0000 | 0 |
| E_CLOSE | TAIL_RISK | 24 | 328001 | 29599 |  | 0.0881 | 0.0000 | 0 |
| E_CLOSE |  | 3 | 44156 | 544 |  | 0.0827 | 0.0000 | 0 |
| E_TOUCH | LEVEL_FORECAST_K12 | 24 | 206956 | 150644 |  | 0.0975 | 0.0000 | 0 |
| E_TOUCH | LEVEL_FORECAST_K4 | 24 | 207070 | 150530 |  | 0.0971 | 0.0000 | 0 |
| E_TOUCH | LEVEL_NOW | 24 | 345581 | 12019 |  | 0.0971 | 0.0000 | 0 |
| E_TOUCH | RANGE_SCALE | 24 | 347426 | 10174 |  | 0.0980 | 0.0000 | 0 |
| E_TOUCH | SHOCK | 24 | 346479 | 11121 |  | 0.0990 | 0.0000 | 0 |
| E_TOUCH | SWING_GT_CUR | 24 | 337917 | 19683 |  | 0.0982 | 0.0000 | 0 |
| E_TOUCH | SWING_SCALE | 24 | 338499 | 19101 |  | 0.0977 | 0.0000 | 0 |
| E_TOUCH | TAIL_RISK | 24 | 346965 | 10635 |  | 0.0981 | 0.0000 | 0 |
| E_TOUCH |  | 3 | 44667 | 33 |  | 0.0966 | 0.0000 | 0 |

crypto:

| entry_variant | component | rows | selected_n | excluded_n | payoff_scale_ratio_med | sign_share_difference_med | excluded_mean_median_gap_med | payoff_nonnull |
|---|---|---|---|---|---|---|---|---|
| E_CLOSE | LEVEL_FORECAST_K12 | 200 | 1007216 | 841752 |  | 0.0831 | 0.0000 | 0 |
| E_CLOSE | LEVEL_FORECAST_K4 | 200 | 1008132 | 840836 |  | 0.0829 | 0.0000 | 0 |
| E_CLOSE | LEVEL_NOW | 200 | 1683027 | 165941 |  | 0.0828 | 0.0000 | 0 |
| E_CLOSE | RANGE_SCALE | 200 | 1695262 | 153706 |  | 0.0838 | 0.0000 | 0 |
| E_CLOSE | SHOCK | 200 | 1690125 | 158843 |  | 0.0840 | 0.0000 | 0 |
| E_CLOSE | SWING_GT_CUR | 200 | 1599039 | 249929 |  | 0.0828 | 0.0000 | 0 |
| E_CLOSE | SWING_SCALE | 200 | 1587223 | 261745 |  | 0.0838 | 0.0000 | 0 |
| E_CLOSE | TAIL_RISK | 200 | 1694068 | 154900 |  | 0.0828 | 0.0000 | 0 |
| E_CLOSE |  | 25 | 227295 | 3826 |  | 0.0786 | 0.0000 | 0 |
| E_TOUCH | LEVEL_FORECAST_K12 | 200 | 1078958 | 770010 |  | 0.0890 | 0.0000 | 0 |
| E_TOUCH | LEVEL_FORECAST_K4 | 200 | 1079931 | 769037 |  | 0.0895 | 0.0000 | 0 |
| E_TOUCH | LEVEL_NOW | 200 | 1803430 | 45538 |  | 0.0888 | 0.0000 | 0 |
| E_TOUCH | RANGE_SCALE | 200 | 1818410 | 30558 |  | 0.0896 | 0.0000 | 0 |
| E_TOUCH | SHOCK | 200 | 1810940 | 38028 |  | 0.0905 | 0.0000 | 0 |
| E_TOUCH | SWING_GT_CUR | 200 | 1714065 | 134903 |  | 0.0887 | 0.0000 | 0 |
| E_TOUCH | SWING_SCALE | 200 | 1703717 | 145251 |  | 0.0892 | 0.0000 | 0 |
| E_TOUCH | TAIL_RISK | 200 | 1815100 | 33868 |  | 0.0894 | 0.0000 | 0 |
| E_TOUCH |  | 25 | 230800 | 321 |  | 0.0880 | 0.0000 | 0 |

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

