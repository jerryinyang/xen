# SPDR-021 — Screen record

- **Experiment:** `SPDR-021` — Volatility-adaptive management on a fixed breakout benchmark
- **Family / registration:** `CF-VOLDIR-001/HYP-D8`
- **Checkpoint:** `2026-07-25-018-trade-opportunity-capture-geometry`
- **Band:** TRAIN
- **Vehicle:** NautilusTrader
- **Run stamp:** `20260731T004708Z` (two universes: cTrader, crypto)
- **Entry substrate:** breakout only — a single entry variant (`BREAKOUT`). `E-TOUCH` / `E-CLOSE`
  do not apply to this experiment.
- **Date of this record:** 2026-07-31

**Status.** The screen ran to completion in both universes and the analysis artifacts exist
(13 per universe cell). **NO disposition is taken here.** This document is a neutral record of what
ran and what exists. It contains no interpretation, no effect values, no ranking of arms, and no
verdict. The binding interpretive read is `analysis.md`, which is not yet written.

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

Plainly: **cost in this run is partial.** Only fees and funding are charged. Spread is not charged
at all. Every cost-bearing field in every artifact of this run therefore **understates cost**, and
any net-of-cost figure derived from them is correspondingly overstated. The same disclosure block is
carried inside `config.json` and `run_summary.json` in both universes, and the columns
`spread_cost_status`, `spread_rt_bps` and `cost_scope` are carried on every row of
`per_stratum_estimates.parquet`.

---

## Universe 1 — cTrader

### Run identity

| Field | Value |
| --- | --- |
| Run id | `SPDR-021-ctrader-train-20260731T004708Z` |
| Absolute path | `/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/data/nautilus_runs/SPDR-021-ctrader-train-20260731T004708Z` |
| Catalog path | `/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/data/catalog_ctrader` |
| Catalog version | `INFR-021` |
| Manifest path | `python/experiments/INFR-021/artifacts/fence-manifest.json` |
| Manifest sha256 | `4cdc7b01dd47200710d0d961639d55d52e1129ca89096e841eafd816b6061de0` |
| Config hash | `170d986234acfba48de7b45d08c2b92687ef364bb3f4e0ee77f70653e1d3d21a` |
| Fence status | `PINNED` |
| `train_start_utc` | `2021-06-02T00:01:00Z` |
| `train_end_utc` | `2023-11-22T00:00:00Z` |
| `analysis_end_utc` | `2024-12-13T00:00:00Z` |
| `holdout_start_utc` | `2024-12-13T00:00:00Z` |
| Band | TRAIN |
| Symbols | EURUSD, XAUUSD, USTEC (3) |
| Work units | 3 declared, 3 completed |
| `native_arms` | 65 |
| `native_adaptive_arms` | 64 |
| `management_arms` | 84 |
| `base_size_increments` | 1000 |
| Per-instrument emissions | `cells/EURUSD/`, `cells/USTEC/`, `cells/XAUUSD/` |

Software pins: NautilusTrader `1.230.0`, polars `1.41.2`, Python `3.13.1`.
Run environment: `dry_run: false`, `jobs: 2`, platform `macOS-26.5.2-arm64-arm-64bit-Mach-O`.

**Spread limitation (repeated):** cost here is fees/funding only; spread is not charged, so every
cost-bearing figure in this universe's artifacts understates cost.

### Integrity status

`integrity_selfcheck.json` — `blocking_pass: true`. **13 hard checks, all `true`:**

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

`row_accounting.json`: `pass: true`, `native_complete: true`, `management_complete: true`,
`native_rows: 1303965`, `management_rows: 1604880`, `origin_count: 20061`.

`golden_traces.json`: `pass: true`; traces `expiry_ordering: true`,
`strict_threshold_boundary: true`, `target_precedes_later_stop: true`.

`determinism.json`: `pass: true`, `mode: IMMEDIATE_REHASH`; the replay hash set matches the expected
hash set for all 42 tracked artifacts.

Controls inventory (`controls.json` plus the `informative` block of `integrity_selfcheck.json`):

- `effect_quality_is_blocking: false`
- `ledger_rows: 3493624`
- `time_derangement`: 44,703 rows, seed `240730`, `zero_fixed_points: true`
- `magnitude_match`: 19,542 rows — 9,772 selected, 9,770 excluded
- `controls.parquet` (analysis side) enumerates 4 controls: `FIXED_DEVICE` (COMPUTED),
  `FIXED_NATIVE_PARAMETER` (COMPUTED), `TIME_DERANGEMENT` (`DEFERRED_TO_STAGE_8`),
  `MAGNITUDE_MATCH` (`DEFERRED_TO_STAGE_8`).

**Known artifact-labelling defect.** `run_summary.json` still carries the stale literal
`"hard_integrity": "NOT_YET_RUN_TASK_8"`. That string is a leftover placeholder from an earlier
stage of the emission chain and was never rewritten. The **authoritative integrity source is
`integrity_selfcheck.json`**, which records `blocking_pass: true` with all 13 hard checks passing.
This is a labelling defect in `run_summary.json`, **not** an integrity failure.

### Counts

| Quantity | Count |
| --- | --- |
| Origins (`origins.parquet`) | 20,061 |
| Episodes (`episodes.parquet`) | 1,303,965 |
| Policy rows (`policy_schedule.parquet`) | 1,604,880 |
| Orders (`orders.parquet`) | 485,491 |
| Fills (`fills.parquet`) | 236,158 |
| Positions (`positions.parquet`) | 118,187 |
| Ledger rows (`controls.json`) | 3,493,624 |

Complete arm accounting — every row of both run schedules, by `arm_class` (no selection, no
ordering by outcome):

| `arm_class` | Source schedule | Rows |
| --- | --- | --- |
| `FIXED_NATIVE` | native | 20,061 |
| `NATIVE` | native | 641,952 |
| `NATIVE_COMBINATION` | native | 641,952 |
| `FIXED_MANAGEMENT` | policy | 280,854 |
| `MANAGEMENT` | policy | 822,501 |
| `MANAGEMENT_COMPONENT_COMBINATION` | policy | 441,342 |
| `MANAGEMENT_DEVICE_COMBINATION` | policy | 60,183 |
| **Total** | both | **2,908,845** |

Complete state accounting over the same rows:

| `state` | Native schedule | Policy schedule | Total |
| --- | --- | --- | --- |
| `ORDER_CREATED` | 326,294 | 459,040 | 785,334 |
| `NO_EVENT` | 839,559 | 1,145,840 | 1,985,399 |
| `NO_FEATURE` | 138,112 | 0 | 138,112 |
| **Total** | 1,303,965 | 1,604,880 | 2,908,845 |

### Analysis artifacts

Directory: `python/experiments/SPDR-021/results/analysis/ctrader/` — 13 artifacts.

| Artifact | Rows | Columns |
| --- | --- | --- |
| `per_stratum_estimates.parquet` | 1,125 | 50 |
| `native_parameter_origins.parquet` | 729 | 25 |
| `native_parameter_shared_trades.parquet` | 0 | 62 |
| `native_parameter_selected_excluded.parquet` | 1,303,965 | 11 |
| `device_target.parquet` | 528 | 20 |
| `device_stop.parquet` | 480 | 20 |
| `device_trail.parquet` | 270 | 20 |
| `device_hold.parquet` | 360 | 20 |
| `device_size.parquet` | 264 | 20 |
| `state_sections.parquet` | 1,014 | 9 |
| `selection_checks.parquet` | 195 | 11 |
| `controls.parquet` | 4 | 4 |
| `analysis_summary.json` | — | — |

`analysis_summary.json` contents:

```json
{
  "artifacts": ["per_stratum_estimates.parquet", "native_parameter_origins.parquet",
    "native_parameter_shared_trades.parquet", "native_parameter_selected_excluded.parquet",
    "device_target.parquet", "device_stop.parquet", "device_trail.parquet",
    "device_hold.parquet", "device_size.parquet", "state_sections.parquet",
    "selection_checks.parquet", "controls.parquet", "analysis_summary.json"],
  "band": "TRAIN",
  "block_bars": 24,
  "experiment_id": "SPDR-021",
  "interpretation": "DESCRIPTIVE_ONLY",
  "native_rows": 729,
  "paired_rows": 396,
  "universe": "ctrader"
}
```

Complete `arm_class` tabulation of `per_stratum_estimates.parquet` (all 1,125 rows accounted for):
`NATIVE` 360, `NATIVE_COMBINATION` 360, `MANAGEMENT` 246, `MANAGEMENT_COMPONENT_COMBINATION` 132,
`MANAGEMENT_DEVICE_COMBINATION` 18, `FIXED_NATIVE` 9. `entry_variant` takes the single value
`BREAKOUT` on every row.

Fields present but **not quoted here**: `per_stratum_estimates.parquet` carries `estimate`,
`ci_low`, `ci_high`, `mde` and `effective_n` populated on all 1,125 rows, `trade_count` on all
1,125 rows, and `paired_n` on 396 rows. Their values are for `analysis.md` to read.

**Reproduction.** Every one of the 13 artifacts was re-derived in an independent second pass to a
temporary directory and sha256-hashed; all 13 hashed identically to the published pass.

### Execution record

From the analysis execution record (2026-07-31): `jobs: 3`, primary pass 117 s, reproduction pass
117 s, reproduction result "13 artifacts identical".

---

## Universe 2 — crypto

### Run identity

| Field | Value |
| --- | --- |
| Run id | `SPDR-021-crypto-train-20260731T004708Z` |
| Absolute path | `/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/data/nautilus_runs/SPDR-021-crypto-train-20260731T004708Z` |
| Catalog path | `/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/data/catalog` |
| Catalog version | `INFR-011-A6` |
| Manifest path | `archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-011/artifacts/fence-manifest.json` |
| Manifest sha256 | `35d3375ec5ec18b3c6e4c5eec814ade4d492bd60e3fb694fed19e16bc2c00448` |
| Config hash | `f3b86cef99740e023c965aee74a69c6dc4b7cf853bb3ac3712e2b5606c5347c6` |
| Fence status | `PINNED` |
| `train_start_utc` | `2021-06-29T06:53:00Z` |
| `train_end_utc` | `2023-12-18T00:00:00Z` |
| `analysis_end_utc` | `2025-01-08T00:00:00Z` |
| `holdout_start_utc` | `2025-01-08T00:00:00Z` |
| Band | TRAIN |
| Symbols | 25 — BTCUSDT, ETHUSDT, SOLUSDT, AVAXUSDT, ORDIUSDT, 1000BONKUSDT, TIAUSDT, DOGEUSDT, XRPUSDT, LINKUSDT, ADAUSDT, BIGTIMEUSDT, BLURUSDT, 1000PEPEUSDT, 1000LUNCUSDT, MATICUSDT, INJUSDT, SEIUSDT, BNBUSDT, WLDUSDT, PYTHUSDT, DYDXUSDT, GALAUSDT, OPUSDT, 1000RATSUSDT |
| Work units | 25 declared, 25 completed |
| `native_arms` | 65 |
| `native_adaptive_arms` | 64 |
| `management_arms` | 84 |
| `base_size_increments` | 1000 |
| Per-instrument emissions | `cells/<SYMBOL>/` for all 25 symbols listed above |

Software pins: NautilusTrader `1.230.0`, polars `1.41.2`, Python `3.13.1`.
Run environment: `dry_run: false`, `jobs: 2`, platform `macOS-26.5.2-arm64-arm-64bit-Mach-O`.

**Spread limitation (repeated):** cost here is fees/funding only; spread is not charged, so every
cost-bearing figure in this universe's artifacts understates cost.

### Integrity status

`integrity_selfcheck.json` — `blocking_pass: true`. **13 hard checks, all `true`:**

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

`row_accounting.json`: `pass: true`, `native_complete: true`, `management_complete: true`,
`native_rows: 6640400`, `management_rows: 8172800`, `origin_count: 102160`.

`golden_traces.json`: `pass: true`; traces `expiry_ordering: true`,
`strict_threshold_boundary: true`, `target_precedes_later_stop: true`.

`determinism.json`: `pass: true`, `mode: IMMEDIATE_REHASH`; replay hashes match expected hashes
across the tracked artifact set.

Controls inventory:

- `effect_quality_is_blocking: false`
- `ledger_rows: 17532470`
- `time_derangement`: 231,146 rows, seed `240730`, `zero_fixed_points: true`
- `magnitude_match`: 96,305 rows — 48,158 selected, 48,147 excluded
- `controls.parquet` (analysis side) enumerates 4 controls: `FIXED_DEVICE` (COMPUTED),
  `FIXED_NATIVE_PARAMETER` (COMPUTED), `TIME_DERANGEMENT` (`DEFERRED_TO_STAGE_8`),
  `MAGNITUDE_MATCH` (`DEFERRED_TO_STAGE_8`).

**Known artifact-labelling defect.** As in the cTrader universe, `run_summary.json` carries the
stale literal `"hard_integrity": "NOT_YET_RUN_TASK_8"`. The authoritative source is
`integrity_selfcheck.json` (`blocking_pass: true`, 13/13 hard checks true). Labelling defect, not an
integrity failure.

### Counts

| Quantity | Count |
| --- | --- |
| Origins (`origins.parquet`) | 102,160 |
| Episodes (`episodes.parquet`) | 6,640,400 |
| Policy rows (`policy_schedule.parquet`) | 8,172,800 |
| Orders (`orders.parquet`) | 2,238,340 |
| Fills (`fills.parquet`) | 1,133,337 |
| Positions (`positions.parquet`) | 567,523 |
| Ledger rows (`controls.json`) | 17,532,470 |

Complete arm accounting — every row of both run schedules, by `arm_class`:

| `arm_class` | Source schedule | Rows |
| --- | --- | --- |
| `FIXED_NATIVE` | native | 102,160 |
| `NATIVE` | native | 3,269,120 |
| `NATIVE_COMBINATION` | native | 3,269,120 |
| `FIXED_MANAGEMENT` | policy | 1,430,240 |
| `MANAGEMENT` | policy | 4,188,560 |
| `MANAGEMENT_COMPONENT_COMBINATION` | policy | 2,247,520 |
| `MANAGEMENT_DEVICE_COMBINATION` | policy | 306,480 |
| **Total** | both | **14,813,200** |

Complete state accounting over the same rows:

| `state` | Native schedule | Policy schedule | Total |
| --- | --- | --- | --- |
| `ORDER_CREATED` | 1,490,840 | 2,147,920 | 3,638,760 |
| `NO_EVENT` | 4,379,536 | 6,024,880 | 10,404,416 |
| `NO_FEATURE` | 770,024 | 0 | 770,024 |
| **Total** | 6,640,400 | 8,172,800 | 14,813,200 |

### Analysis artifacts

Directory: `python/experiments/SPDR-021/results/analysis/crypto/` — 13 artifacts.

| Artifact | Rows | Columns |
| --- | --- | --- |
| `per_stratum_estimates.parquet` | 9,311 | 50 |
| `native_parameter_origins.parquet` | 6,011 | 25 |
| `native_parameter_shared_trades.parquet` | 0 | 62 |
| `native_parameter_selected_excluded.parquet` | 6,640,400 | 11 |
| `device_target.parquet` | 4,400 | 20 |
| `device_stop.parquet` | 4,000 | 20 |
| `device_trail.parquet` | 2,250 | 20 |
| `device_hold.parquet` | 3,000 | 20 |
| `device_size.parquet` | 2,200 | 20 |
| `state_sections.parquet` | 8,386 | 9 |
| `selection_checks.parquet` | 1,625 | 11 |
| `controls.parquet` | 4 | 4 |
| `analysis_summary.json` | — | — |

`analysis_summary.json` contents:

```json
{
  "artifacts": ["per_stratum_estimates.parquet", "native_parameter_origins.parquet",
    "native_parameter_shared_trades.parquet", "native_parameter_selected_excluded.parquet",
    "device_target.parquet", "device_stop.parquet", "device_trail.parquet",
    "device_hold.parquet", "device_size.parquet", "state_sections.parquet",
    "selection_checks.parquet", "controls.parquet", "analysis_summary.json"],
  "band": "TRAIN",
  "block_bars": 24,
  "experiment_id": "SPDR-021",
  "interpretation": "DESCRIPTIVE_ONLY",
  "native_rows": 6011,
  "paired_rows": 3300,
  "universe": "crypto"
}
```

Complete `arm_class` tabulation of `per_stratum_estimates.parquet` (all 9,311 rows accounted for):
`NATIVE` 2,968, `NATIVE_COMBINATION` 2,968, `MANAGEMENT` 2,050,
`MANAGEMENT_COMPONENT_COMBINATION` 1,100, `MANAGEMENT_DEVICE_COMBINATION` 150, `FIXED_NATIVE` 75.
`entry_variant` takes the single value `BREAKOUT` on every row.

Fields present but **not quoted here**: `estimate`, `ci_low`, `ci_high`, `mde`, `effective_n` and
`trade_count` are populated on all 9,311 rows; `paired_n` on 3,300 rows.

**Reproduction.** All 13 artifacts were re-derived in an independent second pass and hashed
identically to the published pass.

### Execution record

From the analysis execution record (2026-07-31): `jobs: 4`, primary pass 494 s, reproduction pass
494 s, reproduction result "13 artifacts identical".

---

## Cross-universe post-publication verification

Recorded in the analysis execution record and applying to both cells above:

- every declared artifact present (13 per cell);
- reporting keys unique in every keyed artifact;
- `native_parameter_selected_excluded` row count equals the native schedule row count exactly
  (cTrader 1,303,965; crypto 6,640,400 — confirmed independently here);
- `state_sections` `row_n` total equals native + policy schedule rows exactly;
- each `analysis_summary.json` carries its own experiment id, `band=TRAIN`,
  `interpretation=DESCRIPTIVE_ONLY`.

Analyser version: `xen.adaptive_management.analysis` at commit `639f804` plus the `_read_available`
fix for breach origin ledgers carrying no `entry_variant` column.

---

## Observations on artifact consistency (bookkeeping only)

These are recorded as facts about the artifacts, with no interpretation attached:

1. `run_summary.json` in both universes carries the stale literal
   `"hard_integrity": "NOT_YET_RUN_TASK_8"` while `integrity_selfcheck.json` records
   `blocking_pass: true` with 13/13 hard checks true. Authoritative source is
   `integrity_selfcheck.json`; the stale string is an artifact-labelling defect.
2. In both universes `episodes.parquet` and `native_parameter_schedule.parquet` carry the **same**
   sha256 in `row_accounting.json` / `determinism.json` (cTrader
   `4a2940381812f4dc29721c0117a4a10ab9696fc9c1690a17bb1fedd9bb5e1a90`), i.e. the two file names
   point at byte-identical content.
3. `native_parameter_shared_trades.parquet` has 0 rows (62 columns) in both universes.
4. `FIXED_MANAGEMENT` appears in the policy schedule (cTrader 280,854 rows; crypto 1,430,240 rows)
   but is not among the `arm_class` values present in `per_stratum_estimates.parquet`, where the
   fixed-device comparator is instead surfaced through `controls.parquet`
   (`FIXED_DEVICE`, COMPUTED) and the per-row `comparator_id`.
5. `controls.parquet` marks `TIME_DERANGEMENT` and `MAGNITUDE_MATCH` as
   `DEFERRED_TO_STAGE_8`, while the run-side `controls.json` already records their row counts,
   seed and `zero_fixed_points` result.

---

## Links

Raw run directories:
- cTrader — [`../../../data/nautilus_runs/SPDR-021-ctrader-train-20260731T004708Z/`](../../../data/nautilus_runs/SPDR-021-ctrader-train-20260731T004708Z/)
- crypto — [`../../../data/nautilus_runs/SPDR-021-crypto-train-20260731T004708Z/`](../../../data/nautilus_runs/SPDR-021-crypto-train-20260731T004708Z/)

Analysis directories:
- cTrader — [`results/analysis/ctrader/`](results/analysis/ctrader/)
- crypto — [`results/analysis/crypto/`](results/analysis/crypto/)

Design: [`design.md`](design.md)

Binding interpretive read: [`analysis.md`](analysis.md) — **not yet written.** A fresh-context
analyst produces it. Anything resembling a finding, an effect magnitude, a comparison between arms,
or a disposition belongs there, not here. This screen record is subordinate to it.

---

## Boundary statement

- **TRAIN only.** Both universes ran inside a `PINNED` fence with `blocking_pass: true`.
- **No TEST read.** No TEST data was read, and no read was spent.
- **No holdout contact.** The holdout boundaries (`2024-12-13T00:00:00Z` cTrader,
  `2025-01-08T00:00:00Z` crypto) were not approached or touched.
- **No family status change.** `CF-VOLDIR-001` is unchanged by this record.
- **No XENA action.** Nothing under XENA was read, written, or triggered.
- **No verdict.** No disposition (`WORTH_EXPLORING` / `NOT_WORTH` / `INCONCLUSIVE`) is taken here,
  and none is implied. Per the SPDR characterisation contract this experiment produces a map, not a
  decision.
- **No tradability or deployability claim.** Cost is partial (fees/funding only, spread not
  charged); the claims `fully-net`, `cost-complete`, `tradable` and `deployable` are prohibited.
- **Claim boundary from `design.md` stands:** this characterises the breakout substrate only; it
  does not gate `SPDR-022` or `SPDR-023`.
- The **operator** takes any disposition, after reading `analysis.md`.
