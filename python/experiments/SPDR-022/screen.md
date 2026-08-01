# SPDR-022 — screen record

- **Experiment id:** SPDR-022
- **Title:** Volatility-adaptive management after MOMO breach entries
- **Family / registration:** `CF-VOLDIR-001/HYP-D9`
- **Checkpoint:** `2026-07-25-018-trade-opportunity-capture-geometry`
- **Band:** TRAIN
- **Vehicle:** NautilusTrader
- **Run stamp:** `20260731T004708Z`
- **Date of this record:** 2026-07-31

**Status.** The screen executed in both universes (cTrader and crypto) and the 13 declared analysis
artifacts exist for each cell. **No disposition is taken here.** This document is a neutral
bookkeeping record of what ran and what exists. It is subordinate to `analysis.md`, which a
separate fresh-context analyst will write and which is the binding interpretive read.

This experiment describes MOMO only. Its two entry variants, `E_TOUCH` and `E_CLOSE`, are kept
strictly separate throughout: neither is presented as the other's fallback and no variant-level
count is aggregated across them.

---

## Spread limitation

Reproduced verbatim from `design.md`:

```text
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: reported cost understates total cost; reported net performance is overstated
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

Plainly: the cost recorded in this run is **partial**. Only fees and funding are charged. Spread is
not charged at all. Any figure in this run that bears a cost therefore **understates cost**, and any
cost-bearing performance figure is correspondingly overstated. The same disclosure block is carried
in each run's `config.json` and `run_summary.json`, and each `per_stratum_estimates.parquet` carries
`spread_cost_status`, `spread_rt_bps` and `cost_scope` columns per row.

---

# Universe: cTrader

### Spread limitation (repeat)

Cost in the cTrader run is partial — fees and funding only, spread not charged
(`spread_cost_status: UNAVAILABLE_NOT_CHARGED`, `cost_scope: PARTIAL_FEES_FUNDING_ONLY`). Any
cost-bearing figure understates cost.

## Run identity — cTrader

| Field | Value |
|---|---|
| Run id | `SPDR-022-ctrader-train-20260731T004708Z` |
| Absolute path | `/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/data/nautilus_runs/SPDR-022-ctrader-train-20260731T004708Z` |
| Catalog path | `/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/data/catalog_ctrader` |
| Catalog version | `INFR-021` |
| Manifest path | `python/experiments/INFR-021/artifacts/fence-manifest.json` |
| Manifest sha256 | `4cdc7b01dd47200710d0d961639d55d52e1129ca89096e841eafd816b6061de0` |
| Config hash | `620736932e62769ca2eb2c779f6f973264221b520212edf017c5a48386b8e9aa` |
| Fence status | `PINNED` |
| `train_start_utc` | `2021-06-02T00:01:00Z` |
| `train_end_utc` | `2023-11-22T00:00:00Z` |
| `analysis_end_utc` | `2024-12-13T00:00:00Z` |
| `holdout_start_utc` | `2024-12-13T00:00:00Z` |
| Symbols (3) | EURUSD, XAUUSD, USTEC |
| Instrument ids | `EURUSD.CTrader` (CurrencyPair), `XAUUSD.CTrader` (Cfd), `USTEC.CTrader` (Cfd) |
| Work units | 3 declared, 3 completed |
| `native_arms` | 130 |
| `native_adaptive_arms` | 128 |
| `management_arms` | 84 |
| `base_size_increments` | 1000 |

Software pins: NautilusTrader `1.230.0`, Python `3.13.1`, polars `1.41.2`.
Run environment: `dry_run` false, `jobs` 1, platform `macOS-26.5.2-arm64-arm-64bit-Mach-O`.

Per-instrument emissions exist under `cells/<SYMBOL>/` for each of EURUSD, XAUUSD, USTEC — eight
files per cell: `bar_marks.parquet`, `event_log.jsonl`, `fence_attestation.json`, `fills.parquet`,
`instrument_id_map.json`, `orders.parquet`, `positions_ledger.parquet`, `run_metadata.json`.

## Integrity status — cTrader

`integrity_selfcheck.json`: `blocking_pass = true`. Thirteen hard checks, each recorded individually:

| Hard check | Result |
|---|---|
| `causality` | true |
| `deterministic_replay` | true |
| `entry_parity` | true |
| `fence` | true |
| `future_shift_changed_mapping` | true |
| `golden_traces` | true |
| `management_lattice` | true |
| `native_lattice` | true |
| `no_native_management_cross` | true |
| `order_fill_position_reconciliation` | true |
| `provenance` | true |
| `row_accounting` | true |
| `unique_result_keys` | true |

`row_accounting.json`: `pass = true`, `native_complete = true`, `management_complete = true`,
`native_rows = 5,811,000`, `management_rows = 7,152,000`, `origin_count = 44,700`.

`golden_traces.json`: `pass = true`; traces `expiry_ordering` true, `strict_threshold_boundary`
true, `target_precedes_later_stop` true.

`determinism.json`: `mode = IMMEDIATE_REHASH`, `pass = true`; the 43 replay hashes match the 43
expected replay hashes exactly.

Controls inventory (`controls.json`): `effect_quality_is_blocking = false`; `ledger_rows =
15,263,724`; `magnitude_match` rows 43,523 (selected 21,763 / excluded 21,760); `time_derangement`
rows 44,703, seed 240730, `zero_fixed_points = true`. The analysis-side `controls.parquet` lists
four controls: `FIXED_DEVICE` (COMPUTED), `FIXED_NATIVE_PARAMETER` (COMPUTED), `TIME_DERANGEMENT`
(DEFERRED_TO_STAGE_8), `MAGNITUDE_MATCH` (DEFERRED_TO_STAGE_8).

**Known artifact-labelling defect.** `run_summary.json` still carries the stale literal
`"hard_integrity": "NOT_YET_RUN_TASK_8"`. `integrity_selfcheck.json` is authoritative and reports
`blocking_pass = true` with all thirteen hard checks true. The stale field is a labelling defect in
`run_summary.json`, not an integrity failure.

## Counts — cTrader

Top-level emission counts (verified by row count on each parquet; identical to `run_summary.json`):

| Object | Rows |
|---|---|
| origins | 44,700 |
| episodes (native parameter schedule) | 5,811,000 |
| policy rows (management schedule) | 7,152,000 |
| orders | 1,641,007 |
| fills | 1,582,643 |
| positions | 791,630 |
| ledger rows (`episode_results.parquet`) | 15,263,724 |
| features | 44,703 |
| calibration | 3 |

`episodes.parquet` and `native_parameter_schedule.parquet` carry the same sha256
(`1fb9851b…`) — they are the same content under two names.

### Native schedule — complete `arm_class` tabulation (5,811,000 rows)

| `arm_class` | rows | E_TOUCH | E_CLOSE |
|---|---|---|---|
| FIXED_NATIVE | 89,400 | 44,700 | 44,700 |
| NATIVE | 2,860,800 | 1,430,400 | 1,430,400 |
| NATIVE_COMBINATION | 2,860,800 | 1,430,400 | 1,430,400 |
| **total** | **5,811,000** | **2,905,500** | **2,905,500** |

### Native schedule — complete `state` tabulation (5,811,000 rows)

| `state` | rows | E_TOUCH | E_CLOSE |
|---|---|---|---|
| CENSORED | 8 | 0 | 8 |
| EVENT_UNDECIDED | 1,539 | 1,539 | 0 |
| INCOMPLETE | 4,044 | 2,022 | 2,022 |
| NO_EVENT | 287,407 | 75,121 | 212,286 |
| NO_FEATURE | 617,638 | 308,819 | 308,819 |
| ORDER_CREATED | 4,900,364 | 2,517,999 | 2,382,365 |
| **total** | **5,811,000** | **2,905,500** | **2,905,500** |

### Policy schedule — complete `arm_class` tabulation (7,152,000 rows)

| `arm_class` | rows | E_TOUCH | E_CLOSE |
|---|---|---|---|
| FIXED_MANAGEMENT | 1,251,600 | 625,800 | 625,800 |
| MANAGEMENT | 3,665,400 | 1,832,700 | 1,832,700 |
| MANAGEMENT_COMPONENT_COMBINATION | 1,966,800 | 983,400 | 983,400 |
| MANAGEMENT_DEVICE_COMBINATION | 268,200 | 134,100 | 134,100 |
| **total** | **7,152,000** | **3,576,000** | **3,576,000** |

### Policy schedule — complete `state` tabulation (7,152,000 rows)

| `state` | rows | E_TOUCH | E_CLOSE |
|---|---|---|---|
| EVENT_UNDECIDED | 1,760 | 1,760 | 0 |
| INCOMPLETE | 4,800 | 2,400 | 2,400 |
| NO_EVENT | 45,680 | 2,400 | 43,280 |
| NO_FEATURE | 480 | 240 | 240 |
| ORDER_CREATED | 7,099,280 | 3,569,200 | 3,530,080 |
| **total** | **7,152,000** | **3,576,000** | **3,576,000** |

All four tabulations above are complete: every observed level of `arm_class` and `state` is listed,
nothing is filtered, and nothing is sorted by any outcome.

## Analysis artifacts — cTrader

Directory: `results/analysis/ctrader/` — 13 artifacts.

| Artifact | rows | columns |
|---|---|---|
| `per_stratum_estimates.parquet` | 3,903 | 50 |
| `native_parameter_origins.parquet` | 2,121 | 25 |
| `native_parameter_shared_trades.parquet` | 4,792,565 | 76 |
| `native_parameter_selected_excluded.parquet` | 5,811,000 | 11 |
| `device_target.parquet` | 2,376 | 20 |
| `device_stop.parquet` | 2,160 | 20 |
| `device_trail.parquet` | 1,215 | 20 |
| `device_hold.parquet` | 1,620 | 20 |
| `device_size.parquet` | 1,188 | 20 |
| `state_sections.parquet` | 3,891 | 9 |
| `selection_checks.parquet` | 390 | 11 |
| `controls.parquet` | 4 | 4 |
| `analysis_summary.json` | — | — |

`native_parameter_selected_excluded.parquet` has exactly as many rows as the native schedule
(5,811,000).

`per_stratum_estimates.parquet` carries the fields `estimate`, `ci_low`, `ci_high`, `mde` and
`effective_n`. All 3,903 rows carry a non-null value in each of those five fields. **No values from
those fields are quoted in this record.**

`analysis_summary.json` contents:

```json
{
  "artifacts": [
    "per_stratum_estimates.parquet", "native_parameter_origins.parquet",
    "native_parameter_shared_trades.parquet", "native_parameter_selected_excluded.parquet",
    "device_target.parquet", "device_stop.parquet", "device_trail.parquet",
    "device_hold.parquet", "device_size.parquet", "state_sections.parquet",
    "selection_checks.parquet", "controls.parquet", "analysis_summary.json"
  ],
  "band": "TRAIN",
  "block_bars": 24,
  "experiment_id": "SPDR-022",
  "interpretation": "DESCRIPTIVE_ONLY",
  "native_rows": 2121,
  "paired_rows": 1782,
  "universe": "ctrader"
}
```

All 13 artifacts for this cell were re-derived in an independent second pass to a temporary
directory and sha256-hashed; the two passes were identical for all 13.

## Execution record — cTrader

From the analysis execution record: 2 jobs; primary pass 471 s wall clock; reproduction pass 483 s;
reproduction result "13 artifacts identical".

---

# Universe: crypto

### Spread limitation (repeat)

Cost in the crypto run is partial — fees and funding only, spread not charged
(`spread_cost_status: UNAVAILABLE_NOT_CHARGED`, `cost_scope: PARTIAL_FEES_FUNDING_ONLY`). Any
cost-bearing figure understates cost.

## Run identity — crypto

**The raw emission for this universe lives on an external volume**, not in the repository data
directory.

| Field | Value |
|---|---|
| Run id | `SPDR-022-crypto-train-20260731T004708Z` |
| Absolute path (external volume) | `/Volumes/SSID/Xen/data/nautilus_runs/SPDR-022-crypto-train-20260731T004708Z` |
| Catalog path | `/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/data/catalog` |
| Catalog version | `INFR-011-A6` |
| Manifest path | `archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-011/artifacts/fence-manifest.json` |
| Manifest sha256 | `35d3375ec5ec18b3c6e4c5eec814ade4d492bd60e3fb694fed19e16bc2c00448` |
| Config hash | `ba92d1ba79f04e16f9525cb73d9fd39debaa92f53cb99f4167274c6aa82cb8ea` |
| Fence status | `PINNED` |
| `train_start_utc` | `2021-06-29T06:53:00Z` |
| `train_end_utc` | `2023-12-18T00:00:00Z` |
| `analysis_end_utc` | `2025-01-08T00:00:00Z` |
| `holdout_start_utc` | `2025-01-08T00:00:00Z` |
| Symbols | 25 (all Bybit linear `CryptoPerpetual`) |
| Work units | 25 declared, 25 completed |
| `native_arms` | 130 |
| `native_adaptive_arms` | 128 |
| `management_arms` | 84 |
| `base_size_increments` | 1000 |

The 25 symbols: BTCUSDT, ETHUSDT, SOLUSDT, AVAXUSDT, ORDIUSDT, 1000BONKUSDT, TIAUSDT, DOGEUSDT,
XRPUSDT, LINKUSDT, ADAUSDT, BIGTIMEUSDT, BLURUSDT, 1000PEPEUSDT, 1000LUNCUSDT, MATICUSDT, INJUSDT,
SEIUSDT, BNBUSDT, WLDUSDT, PYTHUSDT, DYDXUSDT, GALAUSDT, OPUSDT, 1000RATSUSDT.

Software pins: NautilusTrader `1.230.0`, Python `3.13.1`, polars `1.41.2`.
Run environment: `dry_run` false, `jobs` 1, platform `macOS-26.5.2-arm64-arm-64bit-Mach-O`.

Per-instrument emissions exist under `cells/<SYMBOL>/` for all 25 symbols, eight files per cell, the
same file set as the cTrader cells.

**AppleDouble sidecars.** Because the run sits on an external (non-APFS-native) volume, macOS has
written 247 sidecar files named `._*` across the run tree (22 at the run root, the rest inside
`cells/`). These are filesystem metadata shadows of real files. They are excluded from the replay
hashes, they are **not** instrument cells and **not** artifacts, and they are not counted anywhere
in this record as symbols or files.

## Integrity status — crypto

`integrity_selfcheck.json`: `blocking_pass = true`. Thirteen hard checks, each recorded individually:

| Hard check | Result |
|---|---|
| `causality` | true |
| `deterministic_replay` | true |
| `entry_parity` | true |
| `fence` | true |
| `future_shift_changed_mapping` | true |
| `golden_traces` | true |
| `management_lattice` | true |
| `native_lattice` | true |
| `no_native_management_cross` | true |
| `order_fill_position_reconciliation` | true |
| `provenance` | true |
| `row_accounting` | true |
| `unique_result_keys` | true |

`row_accounting.json`: `pass = true`, `native_complete = true`, `management_complete = true`,
`native_rows = 30,045,730`, `management_rows = 36,979,360`, `origin_count = 231,121`.

`golden_traces.json`: `pass = true`; traces `expiry_ordering` true, `strict_threshold_boundary`
true, `target_precedes_later_stop` true.

`determinism.json`: `mode = IMMEDIATE_REHASH`, `pass = true`; the 216 replay hashes match the 216
expected replay hashes exactly.

Controls inventory (`controls.json`): `effect_quality_is_blocking = false`; `ledger_rows =
78,691,344`; `magnitude_match` rows 218,337 (selected 109,175 / excluded 109,162);
`time_derangement` rows 231,146, seed 240730, `zero_fixed_points = true`. The analysis-side
`controls.parquet` lists the same four controls: `FIXED_DEVICE` (COMPUTED),
`FIXED_NATIVE_PARAMETER` (COMPUTED), `TIME_DERANGEMENT` (DEFERRED_TO_STAGE_8), `MAGNITUDE_MATCH`
(DEFERRED_TO_STAGE_8).

**Known artifact-labelling defect.** As in the cTrader run, `run_summary.json` still carries the
stale literal `"hard_integrity": "NOT_YET_RUN_TASK_8"`. `integrity_selfcheck.json` is authoritative
and reports `blocking_pass = true` with all thirteen hard checks true. The stale field is a
labelling defect, not an integrity failure.

## Counts — crypto

| Object | Rows |
|---|---|
| origins | 231,121 |
| episodes (native parameter schedule) | 30,045,730 |
| policy rows (management schedule) | 36,979,360 |
| orders | 8,369,810 |
| fills | 8,052,651 |
| positions | 4,028,998 |
| ledger rows (`episode_results.parquet`) | 78,691,344 |
| features | 231,146 |
| calibration | 25 |

### Native schedule — complete `arm_class` tabulation (30,045,730 rows)

| `arm_class` | rows | E_TOUCH | E_CLOSE |
|---|---|---|---|
| FIXED_NATIVE | 462,242 | 231,121 | 231,121 |
| NATIVE | 14,791,744 | 7,395,872 | 7,395,872 |
| NATIVE_COMBINATION | 14,791,744 | 7,395,872 | 7,395,872 |
| **total** | **30,045,730** | **15,022,865** | **15,022,865** |

### Native schedule — complete `state` tabulation (30,045,730 rows)

| `state` | rows | E_TOUCH | E_CLOSE |
|---|---|---|---|
| CENSORED | 27 | 0 | 27 |
| EVENT_UNDECIDED | 73,689 | 73,689 | 0 |
| INCOMPLETE | 32,964 | 16,482 | 16,482 |
| NO_EVENT | 1,337,086 | 236,561 | 1,100,525 |
| NO_FEATURE | 3,461,906 | 1,730,953 | 1,730,953 |
| ORDER_CREATED | 25,140,058 | 12,965,180 | 12,174,878 |
| **total** | **30,045,730** | **15,022,865** | **15,022,865** |

### Policy schedule — complete `arm_class` tabulation (36,979,360 rows)

| `arm_class` | rows | E_TOUCH | E_CLOSE |
|---|---|---|---|
| FIXED_MANAGEMENT | 6,471,388 | 3,235,694 | 3,235,694 |
| MANAGEMENT | 18,951,922 | 9,475,961 | 9,475,961 |
| MANAGEMENT_COMPONENT_COMBINATION | 10,169,324 | 5,084,662 | 5,084,662 |
| MANAGEMENT_DEVICE_COMBINATION | 1,386,726 | 693,363 | 693,363 |
| **total** | **36,979,360** | **18,489,680** | **18,489,680** |

### Policy schedule — complete `state` tabulation (36,979,360 rows)

| `state` | rows | E_TOUCH | E_CLOSE |
|---|---|---|---|
| EVENT_UNDECIDED | 76,720 | 76,720 | 0 |
| INCOMPLETE | 40,000 | 20,000 | 20,000 |
| NO_EVENT | 327,760 | 23,680 | 304,080 |
| NO_FEATURE | 4,000 | 2,000 | 2,000 |
| ORDER_CREATED | 36,530,880 | 18,367,280 | 18,163,600 |
| **total** | **36,979,360** | **18,489,680** | **18,489,680** |

All four tabulations above are complete: every observed level is listed, nothing filtered, nothing
ordered by outcome.

## Analysis artifacts — crypto

Directory: `results/analysis/crypto/` — 13 artifacts.

| Artifact | rows | columns |
|---|---|---|
| `per_stratum_estimates.parquet` | 31,498 | 50 |
| `native_parameter_origins.parquet` | 17,176 | 25 |
| `native_parameter_shared_trades.parquet` | 24,543,794 | 76 |
| `native_parameter_selected_excluded.parquet` | 30,045,730 | 11 |
| `device_target.parquet` | 19,096 | 20 |
| `device_stop.parquet` | 17,360 | 20 |
| `device_trail.parquet` | 9,765 | 20 |
| `device_hold.parquet` | 13,020 | 20 |
| `device_size.parquet` | 9,548 | 20 |
| `state_sections.parquet` | 31,286 | 9 |
| `selection_checks.parquet` | 3,250 | 11 |
| `controls.parquet` | 4 | 4 |
| `analysis_summary.json` | — | — |

`native_parameter_selected_excluded.parquet` has exactly as many rows as the native schedule
(30,045,730).

`per_stratum_estimates.parquet` carries the fields `estimate`, `ci_low`, `ci_high`, `mde` and
`effective_n`. All 31,498 rows carry a non-null value in each of those five fields. **No values from
those fields are quoted in this record.**

`analysis_summary.json` contents:

```json
{
  "artifacts": [
    "per_stratum_estimates.parquet", "native_parameter_origins.parquet",
    "native_parameter_shared_trades.parquet", "native_parameter_selected_excluded.parquet",
    "device_target.parquet", "device_stop.parquet", "device_trail.parquet",
    "device_hold.parquet", "device_size.parquet", "state_sections.parquet",
    "selection_checks.parquet", "controls.parquet", "analysis_summary.json"
  ],
  "band": "TRAIN",
  "block_bars": 24,
  "experiment_id": "SPDR-022",
  "interpretation": "DESCRIPTIVE_ONLY",
  "native_rows": 17176,
  "paired_rows": 14322,
  "universe": "crypto"
}
```

All 13 artifacts for this cell were re-derived in an independent second pass to a temporary
directory and sha256-hashed; the two passes were identical for all 13.

## Execution record — crypto

From the analysis execution record: 3 jobs; primary pass 1,719 s wall clock; reproduction pass
1,761 s; reproduction result "13 artifacts identical". The same record notes peak memory of 8.03 GB
across parent process and symbol workers for this cell.

---

## Links

Raw run directories:

- cTrader — [`../../../data/nautilus_runs/SPDR-022-ctrader-train-20260731T004708Z/`](../../../data/nautilus_runs/SPDR-022-ctrader-train-20260731T004708Z/)
- crypto — external volume, absolute path only:
  `/Volumes/SSID/Xen/data/nautilus_runs/SPDR-022-crypto-train-20260731T004708Z/` (no repository-relative
  path exists; the volume must be mounted to read it)

Analysis directories:

- [`results/analysis/ctrader/`](results/analysis/ctrader/)
- [`results/analysis/crypto/`](results/analysis/crypto/)

Design:

- [`design.md`](design.md)

Interpretive read:

- `analysis.md` — **not yet written.** When written by the fresh-context analyst it is the binding
  interpretive read for SPDR-022. This screen record is subordinate to it.

---

## Boundary statement

- TRAIN band only. No TEST data was read.
- No contact with the global holdout. The fence is `PINNED` in both universes and the holdout starts
  after the analysis end in each (`2024-12-13T00:00:00Z` cTrader, `2025-01-08T00:00:00Z` crypto).
- No family status change. `CF-VOLDIR-001` is untouched by this record.
- No XENA action of any kind.
- No verdict, disposition or recommendation is taken here.
- This experiment describes MOMO only. It does **not** gate SPDR-021 and does **not** gate SPDR-023,
  and it makes no comparison between `E_TOUCH` and `E_CLOSE`.
- Reported cost is partial (fees and funding only, spread not charged); no cost-complete or
  tradability reading is available from this run.
- The operator takes any disposition only after reading `analysis.md`.
