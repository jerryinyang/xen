# SPDR-023 — Screen record

- **Experiment:** `SPDR-023` — Volatility-adaptive management on a fixed mean-reversion-breach benchmark
- **Family / registration:** `CF-VOLDIR-001/HYP-D8`
- **Checkpoint:** `2026-07-25-018-trade-opportunity-capture-geometry`
- **Band:** TRAIN
- **Vehicle:** NautilusTrader 1.230.0
- **Run stamp:** `20260803T140238Z` (two universes: cTrader, crypto)
- **Entry substrate:** breach with two separate entry variants kept separate throughout: `E-TOUCH` and `E-CLOSE`.
- **Date of this record:** 2026-08-04

**Status.** This is the amended rerun authorised on 2026-08-03. The earlier first pass was
invalidated and hard-removed; its identifiers are listed only in the invalidation record, see
`docs/superpowers/plans/2026-08-03-spdr-021-023-first-pass-invalidation.md`. Both universes of this
experiment ran to completion, passed every hard integrity check, and produced 13 analysis artifacts
per universe that reproduce exactly on an independent second pass
(13/13 SHA-256 equality in both universes: `all_equal = true`).

**NO disposition is taken here.** This document is a neutral record of what ran and what exists. It
contains no interpretation, no effect values, no ranking of arms, and no verdict. The interpretive
read is `analysis.md`; the combined interpretation across the three experiments belongs to the
operator.

---

## Spread limitation

Reproduced from the run's own disclosure block (`config.json`, `run_summary.json`):

```text
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: reported cost understates total cost; reported net performance is overstated
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

Plainly: **cost in this run is partial.** Only fees and funding are charged. Spread is not charged
at all. Every cost-bearing field in every artifact therefore **understates cost**, and any
net-of-cost figure derived from them is correspondingly overstated.

Recording defect, all six cells: the mirrored `spread_cost_status`, `spread_rt_bps` and
`cost_scope` columns on `per_stratum_estimates.parquet` are null, because the analysis reads those
keys at the top level of the run config while the run nests them under `spread_cost_disclosure`.
The disclosure itself is intact in `config.json` and `run_summary.json`, no estimate is affected,
and the limitation is stated here and in `analysis.md` instead.

---

## Universe 1 — ctrader

### Run identity

| Field | Value |
| --- | --- |
| Run id | `SPDR-023-ctrader-train-20260803T140238Z` |
| Absolute path | `/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/data/nautilus_runs/SPDR-023-ctrader-train-20260803T140238Z` |
| Catalog path | `/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/data/catalog_ctrader` |
| Manifest path | `/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/python/experiments/INFR-021/artifacts/fence-manifest.json` |
| Manifest sha256 | `4cdc7b01dd47200710d0d961639d55d52e1129ca89096e841eafd816b6061de0` |
| Band | TRAIN |
| `train_start_utc` | `2021-06-02T00:01:00Z` |
| `train_end_utc` | `2023-11-22T00:00:00Z` |
| Symbols | EURUSD, XAUUSD, USTEC (3) |
| Work units | 3 declared, 3 completed |
| `native_arms` | 130 |
| `native_adaptive_arms` | 128 |
| `management_arms` | 84 |
| `base_size_increments` | 1,000 |
| Execution workers | 1 |
| Execution wall time | 1,933 s |
| Raw output size | 4,290,136 KiB |

**Spread limitation (repeated):** cost here is fees and funding only; spread is not charged, so every cost-bearing figure in this universe's artifacts understates cost.

### Integrity status

`integrity_selfcheck.json` — `blocking_pass: true`. **14 hard checks, 14 `true`:**

| Hard check | Result |
| --- | --- |
| `causality` | `true` |
| `deterministic_replay` | `true` |
| `entry_parity` | `true` |
| `fence` | `true` |
| `future_shift_changed_mapping` | `true` |
| `golden_traces` | `true` |
| `management_lattice` | `true` |
| `management_lifecycle` | `true` |
| `native_lattice` | `true` |
| `no_native_management_cross` | `true` |
| `order_fill_position_reconciliation` | `true` |
| `provenance` | `true` |
| `row_accounting` | `true` |
| `unique_result_keys` | `true` |

Canonical estimand gate: `blocking_pass: true` over 3 per-instrument cells. Determinism: `pass: true` (mode `IMMEDIATE_REHASH`). Row accounting: `pass: true` (native 5,811,000 rows, management 7,152,000 rows, 44,700 origins, no missing, extra or duplicate key).

### Emission counts

| Count | Value |
| --- | --- |
| Eligible origins | 44,700 |
| Orders | 3,004,756 |
| Fills | 2,897,498 |
| Positions (opened) | 1,448,928 |
| Native episode rows | 5,811,000 |
| Management policy rows | 7,152,000 |
| State-ledger rows | 17,141,863 |

### Device populations from the canonical analysis

Counts are population-labelled exactly as emitted. `eligible_origin_n` counts scheduled opportunities, `entry_fill_n` counts actual fills, `close_n` counts confirmed closes.

| Device | rows | eligible_origin_n | entry_fill_n | close_n |
| --- | ---: | ---: | ---: | ---: |
| TARGET | 2,040 | null | 465,504 | 465,032 |
| STOP | 1,848 | null | 454,416 | 453,984 |
| TRAIL | 1,053 | null | 134,523 | 134,271 |
| HOLD | 1,284 | null | 921,940 | 921,916 |
| SIZE | 1,188 | null | 705,452 | 705,452 |

Episode-state sections present in this universe (state as emitted by the state ledger):

| State | rows |
| --- | ---: |
| `CENSORED` | 8 |
| `EVENT_UNDECIDED` | 3,181 |
| `INCOMPLETE` | 8,484 |
| `NO_EVENT` | 331,107 |
| `NO_FEATURE` | 1,002,406 |
| `ORDER_CREATED` | 11,617,814 |

### Native lattice and lenses

- Entry variants present: `E_CLOSE`, `E_TOUCH`
- Arm classes present: `FIXED_NATIVE`, `NATIVE`, `NATIVE_COMBINATION`
- Orientation pairs present: `DIRECT_DIRECT`, `DIRECT_REVERSE`, `REVERSE_DIRECT`, `REVERSE_REVERSE`
- Estimand lenses present: `COMMON_CLOSE_TRADE`, `COMMON_ORIGIN_OCCUPANCY_INCLUSIVE`
- `native_parameter_origins.parquet` rows: 2,121; paired trade rows: 292; block length: 24 bars; interpretation field: `DESCRIPTIVE_ONLY`

### Control availability

| Control | rows | stage | rows with an estimate | rows null with a reason |
| --- | ---: | --- | ---: | ---: |
| `FIXED_DEVICE` | 1 | `COMPUTED` | 0 | 1 |
| `FIXED_NATIVE_PARAMETER` | 1 | `COMPUTED` | 0 | 1 |
| `MAGNITUDE_MATCH` | 1,536 | `COMPUTED` | 1,536 | 0 |
| `TIME_DERANGEMENT` | 384 | `COMPUTED` | 384 | 0 |

Engine-side control inputs recorded in `controls.json`: time derangement 44,703 rows, seed 240730, `zero_fixed_points: true`; magnitude match 43,523 rows (21,763 selected, 21,760 excluded). Controls are informative and gate nothing.

### Analysis artifacts

- Directory: `python/experiments/SPDR-023/results/analysis/ctrader/`
- Artifacts: 13 of 13 declared
- Production pass: 1,056.134 s / 4.084 GB
- Independent reproduction pass: 849.041 s / 3.897 GB
- Reproduction evidence: `python/experiments/SPDR-023/results/analysis/reproduction-hashes.json`

---

## Universe 2 — crypto

### Run identity

| Field | Value |
| --- | --- |
| Run id | `SPDR-023-crypto-train-20260803T140238Z` |
| Absolute path | `/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/data/nautilus_runs/SPDR-023-crypto-train-20260803T140238Z` |
| Catalog path | `/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/data/catalog` |
| Manifest path | `/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-011/artifacts/fence-manifest.json` |
| Manifest sha256 | `35d3375ec5ec18b3c6e4c5eec814ade4d492bd60e3fb694fed19e16bc2c00448` |
| Band | TRAIN |
| `train_start_utc` | `2021-06-29T06:53:00Z` |
| `train_end_utc` | `2023-12-18T00:00:00Z` |
| Symbols | BTCUSDT, ETHUSDT, SOLUSDT, AVAXUSDT, ORDIUSDT, 1000BONKUSDT, TIAUSDT, DOGEUSDT, XRPUSDT, LINKUSDT, ADAUSDT, BIGTIMEUSDT, BLURUSDT, 1000PEPEUSDT, 1000LUNCUSDT, MATICUSDT, INJUSDT, SEIUSDT, BNBUSDT, WLDUSDT, PYTHUSDT, DYDXUSDT, GALAUSDT, OPUSDT, 1000RATSUSDT (25) |
| Work units | 25 declared, 25 completed |
| `native_arms` | 130 |
| `native_adaptive_arms` | 128 |
| `management_arms` | 84 |
| `base_size_increments` | 1,000 |
| Execution workers | 1 |
| Execution wall time | 9,149 s |
| Raw output size | 22,292,148 KiB |

**Spread limitation (repeated):** cost here is fees and funding only; spread is not charged, so every cost-bearing figure in this universe's artifacts understates cost.

### Integrity status

`integrity_selfcheck.json` — `blocking_pass: true`. **14 hard checks, 14 `true`:**

| Hard check | Result |
| --- | --- |
| `causality` | `true` |
| `deterministic_replay` | `true` |
| `entry_parity` | `true` |
| `fence` | `true` |
| `future_shift_changed_mapping` | `true` |
| `golden_traces` | `true` |
| `management_lattice` | `true` |
| `management_lifecycle` | `true` |
| `native_lattice` | `true` |
| `no_native_management_cross` | `true` |
| `order_fill_position_reconciliation` | `true` |
| `provenance` | `true` |
| `row_accounting` | `true` |
| `unique_result_keys` | `true` |

Canonical estimand gate: `blocking_pass: true` over 25 per-instrument cells. Determinism: `pass: true` (mode `IMMEDIATE_REHASH`). Row accounting: `pass: true` (native 30,045,730 rows, management 36,979,360 rows, 231,121 origins, no missing, extra or duplicate key).

### Emission counts

| Count | Value |
| --- | --- |
| Eligible origins | 231,121 |
| Orders | 15,427,798 |
| Fills | 14,868,649 |
| Positions (opened) | 7,435,982 |
| Native episode rows | 30,045,730 |
| Management policy rows | 36,979,360 |
| State-ledger rows | 88,319,749 |

### Device populations from the canonical analysis

Counts are population-labelled exactly as emitted. `eligible_origin_n` counts scheduled opportunities, `entry_fill_n` counts actual fills, `close_n` counts confirmed closes.

| Device | rows | eligible_origin_n | entry_fill_n | close_n |
| --- | ---: | ---: | ---: | ---: |
| TARGET | 16,232 | null | 2,634,416 | 2,630,644 |
| STOP | 14,704 | null | 2,546,068 | 2,542,564 |
| TRAIL | 8,391 | null | 822,000 | 820,029 |
| HOLD | 10,140 | null | 4,704,332 | 4,703,952 |
| SIZE | 9,548 | null | 3,576,716 | 3,576,672 |

Episode-state sections present in this universe (state as emitted by the state ledger):

| State | rows |
| --- | ---: |
| `CENSORED` | 27 |
| `EVENT_UNDECIDED` | 146,299 |
| `INCOMPLETE` | 69,964 |
| `NO_EVENT` | 1,649,971 |
| `NO_FEATURE` | 5,590,882 |
| `ORDER_CREATED` | 59,567,947 |

### Native lattice and lenses

- Entry variants present: `E_CLOSE`, `E_TOUCH`
- Arm classes present: `FIXED_NATIVE`, `NATIVE`, `NATIVE_COMBINATION`
- Orientation pairs present: `DIRECT_DIRECT`, `DIRECT_REVERSE`, `REVERSE_DIRECT`, `REVERSE_REVERSE`
- Estimand lenses present: `COMMON_CLOSE_TRADE`, `COMMON_ORIGIN_OCCUPANCY_INCLUSIVE`
- `native_parameter_origins.parquet` rows: 17,176; paired trade rows: 2,780; block length: 24 bars; interpretation field: `DESCRIPTIVE_ONLY`

### Control availability

| Control | rows | stage | rows with an estimate | rows null with a reason |
| --- | ---: | --- | ---: | ---: |
| `FIXED_DEVICE` | 1 | `COMPUTED` | 0 | 1 |
| `FIXED_NATIVE_PARAMETER` | 1 | `COMPUTED` | 0 | 1 |
| `MAGNITUDE_MATCH` | 12,800 | `COMPUTED` | 12,800 | 0 |
| `TIME_DERANGEMENT` | 3,200 | `COMPUTED` | 3,200 | 0 |

Engine-side control inputs recorded in `controls.json`: time derangement 231,146 rows, seed 240730, `zero_fixed_points: true`; magnitude match 218,337 rows (109,175 selected, 109,162 excluded). Controls are informative and gate nothing.

### Analysis artifacts

- Directory: `python/experiments/SPDR-023/results/analysis/crypto/`
- Artifacts: 13 of 13 declared
- Production pass: not persisted (session interrupted after atomic publication)
- Independent reproduction pass: not persisted (session interrupted after atomic publication)
- Reproduction evidence: `python/experiments/SPDR-023/results/analysis/reproduction-hashes.json`

---

## Populations to keep separate when reading the artifacts

- `eligible_origin_n` — scheduled opportunities, including origins with no exposure because the arm
  was occupied. Per-origin intervals and MDEs are built from these.
- `entry_fill_n` — actual entry fills recorded by the engine.
- `close_n` — confirmed closes.
- `common_fill_n` / `common_close_n` — origins filled, or closed, on both comparison sides.
- `effective_origin_blocks` / `effective_trade_blocks` — resampled blocks behind the matching
  interval. A scheduled row never inflates a trade-level count.

The two native lenses (`COMMON_ORIGIN_OCCUPANCY_INCLUSIVE` and `COMMON_CLOSE_TRADE`) answer
different questions and must never be merged.

---

## What is not in this record

No effect value, no comparison of arms, no power judgement, no `SUPPORTED`/`REFUTED` label, no
winner, no tradability or deployability statement, and no TEST or holdout contact of any kind.
