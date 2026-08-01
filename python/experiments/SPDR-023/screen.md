# SPDR-023 — screen record (neutral)

- **Experiment id:** `SPDR-023`
- **Title:** Volatility-adaptive management after MR breach entries
- **Family / registration:** `CF-VOLDIR-001/HYP-D10`
- **Checkpoint:** `2026-07-25-018-trade-opportunity-capture-geometry`
- **Band:** TRAIN
- **Vehicle:** NautilusTrader
- **Run stamp:** `20260731T004708Z` (both universes)
- **Date of this record:** 2026-07-31

**Status.** The screen ran to completion in both universes and the analysis artifacts exist
(13 per cell, 26 total). **No disposition is taken here.** This document is a quantification-first
bookkeeping record of what ran and what exists. It is subordinate to `analysis.md`, which a
separate fresh-context analyst will write and which is the binding interpretive read.

**Entry variants.** The model enters against the breach side (MR). `E-TOUCH` and `E-CLOSE` are
kept strictly separate throughout this record. Neither is the other's fallback and their counts are
never aggregated.

**Structural relation to SPDR-022.** SPDR-022 and SPDR-023 share one zone-origin clock, so the two
experiments carry the same origin and episode counts in a given universe (cTrader: 44,700 origins,
5,811,000 episodes in both `run_summary.json` files). This is recorded as a structural fact about
the shared clock only. No outcome of the two experiments is compared here.

---

## Spread limitation (applies to the whole document)

Reproduced verbatim from `design.md`:

```text
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: reported cost understates total cost; reported net performance is overstated
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

Plainly: the cost recorded in this run is **partial** — fees and funding only. **Spread is not
charged.** Every cost-bearing figure in the emissions therefore understates cost. The same block is
carried verbatim in both `config.json` files and in every `per_stratum_estimates.parquet` row
(`spread_cost_status`, `spread_rt_bps`, `cost_scope` columns).

---

# cTrader universe

## 1. Run identity — cTrader

| Field | Value |
| --- | --- |
| Run id | `SPDR-023-ctrader-train-20260731T004708Z` |
| Absolute path | `/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/data/nautilus_runs/SPDR-023-ctrader-train-20260731T004708Z` |
| Catalog path | `/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/data/catalog_ctrader` |
| Catalog version | `INFR-021` |
| Manifest path | `python/experiments/INFR-021/artifacts/fence-manifest.json` |
| Manifest sha256 | `4cdc7b01dd47200710d0d961639d55d52e1129ca89096e841eafd816b6061de0` |
| Config hash | `1078a52185c4e6fb2901d933acea6e640aa683dcf9923caa75810ac28d08f023` |
| Fence status | `PINNED` |
| `train_start_utc` | `2021-06-02T00:01:00Z` |
| `train_end_utc` | `2023-11-22T00:00:00Z` |
| `analysis_end_utc` | `2024-12-13T00:00:00Z` |
| `holdout_start_utc` | `2024-12-13T00:00:00Z` |
| Symbols (3) | EURUSD, XAUUSD, USTEC |
| Work units | 3 declared, 3 completed |
| `native_arms` | 130 |
| `native_adaptive_arms` | 128 |
| `management_arms` | 84 |
| `base_size_increments` | 1000 |

Software pins: NautilusTrader `1.230.0`, Python `3.13.1`, polars `1.41.2`.
Platform `macOS-26.5.2-arm64-arm-64bit-Mach-O`; `jobs = 1`; `dry_run = false`.

Per-instrument emissions exist under `cells/<SYMBOL>/` for EURUSD, USTEC, XAUUSD — each with
`bar_marks.parquet`, `event_log.jsonl`, `fence_attestation.json`, `fills.parquet`,
`instrument_id_map.json`, `orders.parquet`, `positions_ledger.parquet`, `run_metadata.json`
(8 files × 3 symbols).

Spread reminder for this universe: cost is partial (fees/funding only), spread is not charged, so
any cost-bearing figure understates cost.

## 2. Integrity status — cTrader

`integrity_selfcheck.json`: `blocking_pass = true`. Thirteen hard checks, all `true`:

| Hard check | Result |
| --- | --- |
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

`golden_traces.json`: `pass = true`; traces `expiry_ordering = true`,
`strict_threshold_boundary = true`, `target_precedes_later_stop = true`.

`determinism.json`: `pass = true`, `mode = IMMEDIATE_REHASH`, 40 replay hashes recorded and
matching the 40 expected replay hashes.

`controls.json` inventory: `effect_quality_is_blocking = false`; `ledger_rows = 15,282,003`;
`magnitude_match` = 43,523 rows (21,763 selected / 21,760 excluded); `time_derangement` = 44,703
rows, seed `240730`, `zero_fixed_points = true`.

**Known artifact-labelling defect.** `run_summary.json` still carries the stale literal
`"hard_integrity": "NOT_YET_RUN_TASK_8"`. `integrity_selfcheck.json` is the authoritative integrity
record and reports `blocking_pass = true` with all 13 hard checks passing. The stale field is a
labelling defect in the summary file, not an integrity failure.

## 3. Counts — cTrader

Top-level counts (from `run_summary.json`, each verified against the parquet row counts):

| Quantity | Count |
| --- | --- |
| Origins | 44,700 |
| Episodes | 5,811,000 |
| Policy rows | 7,152,000 |
| Orders | 1,651,782 |
| Fills | 1,593,507 |
| Positions | 797,063 |
| Ledger rows | 15,282,003 |

### 3a. Native parameter schedule — complete tabulation (5,811,000 rows)

By `arm_class`:

| `arm_class` | Rows | E-TOUCH | E-CLOSE |
| --- | --- | --- | --- |
| FIXED_NATIVE | 89,400 | 44,700 | 44,700 |
| NATIVE | 2,860,800 | 1,430,400 | 1,430,400 |
| NATIVE_COMBINATION | 2,860,800 | 1,430,400 | 1,430,400 |
| **Total** | **5,811,000** | **2,905,500** | **2,905,500** |

By `state`:

| `state` | Rows | E-TOUCH | E-CLOSE |
| --- | --- | --- | --- |
| CENSORED | 8 | 0 | 8 |
| EVENT_UNDECIDED | 1,539 | 1,539 | 0 |
| INCOMPLETE | 4,044 | 2,022 | 2,022 |
| NO_EVENT | 287,407 | 75,121 | 212,286 |
| NO_FEATURE | 617,638 | 308,819 | 308,819 |
| ORDER_CREATED | 4,900,364 | 2,517,999 | 2,382,365 |
| **Total** | **5,811,000** | **2,905,500** | **2,905,500** |

### 3b. Policy (management) schedule — complete tabulation (7,152,000 rows)

By `arm_class`:

| `arm_class` | Rows | E-TOUCH | E-CLOSE |
| --- | --- | --- | --- |
| FIXED_MANAGEMENT | 1,251,600 | 625,800 | 625,800 |
| MANAGEMENT | 3,665,400 | 1,832,700 | 1,832,700 |
| MANAGEMENT_COMPONENT_COMBINATION | 1,966,800 | 983,400 | 983,400 |
| MANAGEMENT_DEVICE_COMBINATION | 268,200 | 134,100 | 134,100 |
| **Total** | **7,152,000** | **3,576,000** | **3,576,000** |

By `state`:

| `state` | Rows | E-TOUCH | E-CLOSE |
| --- | --- | --- | --- |
| EVENT_UNDECIDED | 1,760 | 1,760 | 0 |
| INCOMPLETE | 4,800 | 2,400 | 2,400 |
| NO_EVENT | 45,680 | 2,400 | 43,280 |
| NO_FEATURE | 480 | 240 | 240 |
| ORDER_CREATED | 7,099,280 | 3,569,200 | 3,530,080 |
| **Total** | **7,152,000** | **3,576,000** | **3,576,000** |

## 4. Analysis artifacts — cTrader

Directory: `python/experiments/SPDR-023/results/analysis/ctrader/` — 13 artifacts.

| Artifact | Rows | Columns |
| --- | --- | --- |
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
| `analysis_summary.json` | — (JSON) | — |

Variant split of the keyed artifacts (E-TOUCH / E-CLOSE): `per_stratum_estimates` 2,143 / 1,760;
`native_parameter_origins` 1,153 / 968; `device_target` 1,320 / 1,056; `device_stop` 1,200 / 960;
`device_trail` 675 / 540; `device_hold` 900 / 720; `device_size` 660 / 528; `state_sections`
2,158 / 1,733; `selection_checks` 195 / 195.

`per_stratum_estimates.parquet` carries the power and effect fields required by the design
(`estimate`, `ci_low`, `ci_high`, `mde`, `effective_n`): all 3,903 rows carry a non-null value in
each of those five fields; 1,782 rows carry a non-null `paired_n`. Their values are not reported
here — they are the analyst's read.

`controls.parquet` (4 rows): `FIXED_DEVICE` = COMPUTED, `FIXED_NATIVE_PARAMETER` = COMPUTED,
`TIME_DERANGEMENT` = DEFERRED_TO_STAGE_8, `MAGNITUDE_MATCH` = DEFERRED_TO_STAGE_8.

`analysis_summary.json`:

```json
{
  "artifacts": ["per_stratum_estimates.parquet", "native_parameter_origins.parquet",
    "native_parameter_shared_trades.parquet", "native_parameter_selected_excluded.parquet",
    "device_target.parquet", "device_stop.parquet", "device_trail.parquet",
    "device_hold.parquet", "device_size.parquet", "state_sections.parquet",
    "selection_checks.parquet", "controls.parquet", "analysis_summary.json"],
  "band": "TRAIN",
  "block_bars": 24,
  "experiment_id": "SPDR-023",
  "interpretation": "DESCRIPTIVE_ONLY",
  "native_rows": 2121,
  "paired_rows": 1782,
  "universe": "ctrader"
}
```

All 13 artifacts were re-derived in an independent second pass to a temporary directory and
sha256-hashed; the two passes hashed identically.

## 5. Execution record — cTrader

- Engine run: `jobs = 1`.
- Analysis: 2 jobs; primary pass 487 s; reproduction pass 486 s; result "13 artifacts identical".
- Analyser version: `xen.adaptive_management.analysis` at commit `639f804` plus the
  `_read_available` fix for breach origin ledgers that carry no `entry_variant` column.

---

# Crypto universe

## 6. Run identity — crypto

| Field | Value |
| --- | --- |
| Run id | `SPDR-023-crypto-train-20260731T004708Z` |
| Absolute path | `/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/data/nautilus_runs/SPDR-023-crypto-train-20260731T004708Z` |
| Catalog path | `/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/data/catalog` |
| Catalog version | `INFR-011-A6` |
| Manifest path | `archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-011/artifacts/fence-manifest.json` |
| Manifest sha256 | `35d3375ec5ec18b3c6e4c5eec814ade4d492bd60e3fb694fed19e16bc2c00448` |
| Config hash | `eeb8bb05cc176424693e83fd0642db9e12459bef498137c5194fead4f3fcdbab` |
| Fence status | `PINNED` |
| `train_start_utc` | `2021-06-29T06:53:00Z` |
| `train_end_utc` | `2023-12-18T00:00:00Z` |
| `analysis_end_utc` | `2025-01-08T00:00:00Z` |
| `holdout_start_utc` | `2025-01-08T00:00:00Z` |
| Symbols (25) | BTCUSDT, ETHUSDT, SOLUSDT, AVAXUSDT, ORDIUSDT, 1000BONKUSDT, TIAUSDT, DOGEUSDT, XRPUSDT, LINKUSDT, ADAUSDT, BIGTIMEUSDT, BLURUSDT, 1000PEPEUSDT, 1000LUNCUSDT, MATICUSDT, INJUSDT, SEIUSDT, BNBUSDT, WLDUSDT, PYTHUSDT, DYDXUSDT, GALAUSDT, OPUSDT, 1000RATSUSDT |
| Work units | 25 declared, 25 completed |
| `native_arms` | 130 |
| `native_adaptive_arms` | 128 |
| `management_arms` | 84 |
| `base_size_increments` | 1000 |

Software pins: NautilusTrader `1.230.0`, Python `3.13.1`, polars `1.41.2`.
Platform `macOS-26.5.2-arm64-arm-64bit-Mach-O`; `jobs = 2`; `dry_run = false`.

Per-instrument emissions exist under `cells/<SYMBOL>/` for all 25 symbols, each with the same
8 files as the cTrader cells (216 hashed source artifacts in total for this run).

Spread reminder for this universe: cost is partial (fees/funding only), spread is not charged, so
any cost-bearing figure understates cost.

## 7. Integrity status — crypto

`integrity_selfcheck.json`: `blocking_pass = true`. The same thirteen hard checks, all `true`:

| Hard check | Result |
| --- | --- |
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

`golden_traces.json`: `pass = true`; traces `expiry_ordering = true`,
`strict_threshold_boundary = true`, `target_precedes_later_stop = true`.

`determinism.json`: `pass = true`, `mode = IMMEDIATE_REHASH`, 216 replay hashes recorded and
matching the 216 expected replay hashes.

`controls.json` inventory: `effect_quality_is_blocking = false`; `ledger_rows = 78,627,279`;
`magnitude_match` = 218,337 rows (109,175 selected / 109,162 excluded); `time_derangement` =
231,146 rows, seed `240730`, `zero_fixed_points = true`.

**Known artifact-labelling defect.** As in the cTrader run, `run_summary.json` carries the stale
literal `"hard_integrity": "NOT_YET_RUN_TASK_8"`. `integrity_selfcheck.json` is authoritative and
reports `blocking_pass = true` with all 13 hard checks passing. Labelling defect, not an integrity
failure.

## 8. Counts — crypto

| Quantity | Count |
| --- | --- |
| Origins | 231,121 |
| Episodes | 30,045,730 |
| Policy rows | 36,979,360 |
| Orders | 8,335,422 |
| Fills | 8,017,895 |
| Positions | 4,011,621 |
| Ledger rows | 78,627,279 |

### 8a. Native parameter schedule — complete tabulation (30,045,730 rows)

By `arm_class`:

| `arm_class` | Rows | E-TOUCH | E-CLOSE |
| --- | --- | --- | --- |
| FIXED_NATIVE | 462,242 | 231,121 | 231,121 |
| NATIVE | 14,791,744 | 7,395,872 | 7,395,872 |
| NATIVE_COMBINATION | 14,791,744 | 7,395,872 | 7,395,872 |
| **Total** | **30,045,730** | **15,022,865** | **15,022,865** |

By `state`:

| `state` | Rows | E-TOUCH | E-CLOSE |
| --- | --- | --- | --- |
| CENSORED | 27 | 0 | 27 |
| EVENT_UNDECIDED | 73,689 | 73,689 | 0 |
| INCOMPLETE | 32,964 | 16,482 | 16,482 |
| NO_EVENT | 1,337,086 | 236,561 | 1,100,525 |
| NO_FEATURE | 3,461,906 | 1,730,953 | 1,730,953 |
| ORDER_CREATED | 25,140,058 | 12,965,180 | 12,174,878 |
| **Total** | **30,045,730** | **15,022,865** | **15,022,865** |

### 8b. Policy (management) schedule — complete tabulation (36,979,360 rows)

By `arm_class`:

| `arm_class` | Rows | E-TOUCH | E-CLOSE |
| --- | --- | --- | --- |
| FIXED_MANAGEMENT | 6,471,388 | 3,235,694 | 3,235,694 |
| MANAGEMENT | 18,951,922 | 9,475,961 | 9,475,961 |
| MANAGEMENT_COMPONENT_COMBINATION | 10,169,324 | 5,084,662 | 5,084,662 |
| MANAGEMENT_DEVICE_COMBINATION | 1,386,726 | 693,363 | 693,363 |
| **Total** | **36,979,360** | **18,489,680** | **18,489,680** |

By `state`:

| `state` | Rows | E-TOUCH | E-CLOSE |
| --- | --- | --- | --- |
| EVENT_UNDECIDED | 76,720 | 76,720 | 0 |
| INCOMPLETE | 40,000 | 20,000 | 20,000 |
| NO_EVENT | 327,760 | 23,680 | 304,080 |
| NO_FEATURE | 4,000 | 2,000 | 2,000 |
| ORDER_CREATED | 36,530,880 | 18,367,280 | 18,163,600 |
| **Total** | **36,979,360** | **18,489,680** | **18,489,680** |

## 9. Analysis artifacts — crypto

Directory: `python/experiments/SPDR-023/results/analysis/crypto/` — 13 artifacts.

| Artifact | Rows | Columns |
| --- | --- | --- |
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
| `analysis_summary.json` | — (JSON) | — |

Variant split of the keyed artifacts (E-TOUCH / E-CLOSE): `per_stratum_estimates` 16,965 / 14,533;
`native_parameter_origins` 9,243 / 7,933; `device_target` 10,296 / 8,800; `device_stop`
9,360 / 8,000; `device_trail` 5,265 / 4,500; `device_hold` 7,020 / 6,000; `device_size`
5,148 / 4,400; `state_sections` 16,978 / 14,308; `selection_checks` 1,625 / 1,625.

All 31,498 `per_stratum_estimates` rows carry a non-null `estimate`, `ci_low`, `ci_high`, `mde` and
`effective_n`; 14,322 rows carry a non-null `paired_n`. Values are not reported here.

`controls.parquet` (4 rows): `FIXED_DEVICE` = COMPUTED, `FIXED_NATIVE_PARAMETER` = COMPUTED,
`TIME_DERANGEMENT` = DEFERRED_TO_STAGE_8, `MAGNITUDE_MATCH` = DEFERRED_TO_STAGE_8.

`analysis_summary.json`:

```json
{
  "artifacts": ["per_stratum_estimates.parquet", "native_parameter_origins.parquet",
    "native_parameter_shared_trades.parquet", "native_parameter_selected_excluded.parquet",
    "device_target.parquet", "device_stop.parquet", "device_trail.parquet",
    "device_hold.parquet", "device_size.parquet", "state_sections.parquet",
    "selection_checks.parquet", "controls.parquet", "analysis_summary.json"],
  "band": "TRAIN",
  "block_bars": 24,
  "experiment_id": "SPDR-023",
  "interpretation": "DESCRIPTIVE_ONLY",
  "native_rows": 17176,
  "paired_rows": 14322,
  "universe": "crypto"
}
```

All 13 artifacts were re-derived in an independent second pass to a temporary directory and
sha256-hashed; the two passes hashed identically.

## 10. Execution record — crypto

- Engine run: `jobs = 2`.
- Analysis: 3 jobs; primary pass 1,450 s; reproduction pass 1,410 s; result "13 artifacts
  identical". Peak memory across parent and symbol workers for this cell: 7.17 GB.
- Analyser version: `xen.adaptive_management.analysis` at commit `639f804` plus the
  `_read_available` fix for breach origin ledgers that carry no `entry_variant` column.

**Mid-run engine-change provenance note.** The first 13 of the 25 crypto symbols were produced
before an engine memory-release change; the remaining 12 were produced after it. The change was
memory-only and the emission is unchanged, so the cell is internally consistent. Recorded as
provenance, not as a defect. Row accounting, determinism replay and all 13 hard checks pass across
the whole cell.

---

## 11. Links

Relative to `python/experiments/SPDR-023/`:

- Design: [`design.md`](design.md)
- cTrader raw run: [`../../../data/nautilus_runs/SPDR-023-ctrader-train-20260731T004708Z/`](../../../data/nautilus_runs/SPDR-023-ctrader-train-20260731T004708Z/)
- crypto raw run: [`../../../data/nautilus_runs/SPDR-023-crypto-train-20260731T004708Z/`](../../../data/nautilus_runs/SPDR-023-crypto-train-20260731T004708Z/)
- cTrader analysis artifacts: [`results/analysis/ctrader/`](results/analysis/ctrader/)
- crypto analysis artifacts: [`results/analysis/crypto/`](results/analysis/crypto/)
- Screen code: [`screen_code/`](screen_code/) · Analysis code: [`analysis_code/`](analysis_code/)
- **Forward reference:** `analysis.md` — the binding interpretive read. **Not yet written.**
  Nothing in this file substitutes for it.

## 12. Boundary statement

- TRAIN band only. No TEST data was read. No holdout contact of any kind.
- No family status change; `CF-VOLDIR-001` is untouched by this record.
- No XENA action, no XENA read, no registry change.
- No verdict, disposition, effect claim or economic conclusion is made here. Per the SPDR lane,
  a disposition (`WORTH_EXPLORING` / `NOT_WORTH` / `INCONCLUSIVE`) is not taken in `screen.md`.
- This experiment describes MR only. It does **not** gate SPDR-021 or SPDR-022, and it makes no
  choice between E-TOUCH and E-CLOSE.
- Reported cost is partial (fees/funding only); spread is not charged. The prohibited claims are
  fully-net, cost-complete, tradable, deployable.
- The operator takes any disposition after reading `analysis.md`.
