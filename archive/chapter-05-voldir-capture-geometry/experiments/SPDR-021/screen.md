# SPDR-021 — Screen record

- **Experiment:** `SPDR-021` — Volatility-adaptive management on a fixed breakout benchmark
- **Family / registration:** `CF-VOLDIR-001/HYP-D8`
- **Checkpoint:** `2026-07-25-018-trade-opportunity-capture-geometry`
- **Band:** TRAIN
- **Vehicle:** NautilusTrader 1.230.0
- **Run stamp:** `20260803T140238Z` (two universes: cTrader, crypto)
- **Entry substrate:** breakout only — a single entry variant (`BREAKOUT`). `E-TOUCH` / `E-CLOSE` do not apply to this experiment.
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
| Run id | `SPDR-021-ctrader-train-20260803T140238Z` |
| Absolute path | `/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/data/nautilus_runs/SPDR-021-ctrader-train-20260803T140238Z` |
| Catalog path | `/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/data/catalog_ctrader` |
| Manifest path | `/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/python/experiments/INFR-021/artifacts/fence-manifest.json` |
| Manifest sha256 | `4cdc7b01dd47200710d0d961639d55d52e1129ca89096e841eafd816b6061de0` |
| Band | TRAIN |
| `train_start_utc` | `2021-06-02T00:01:00Z` |
| `train_end_utc` | `2023-11-22T00:00:00Z` |
| Symbols | EURUSD, XAUUSD, USTEC (3) |
| Work units | 3 declared, 3 completed |
| `native_arms` | 65 |
| `native_adaptive_arms` | 64 |
| `management_arms` | 84 |
| `base_size_increments` | 1,000 |
| Execution workers | 1 |
| Execution wall time | 493 s |
| Raw output size | 733,256 KiB |

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

Canonical estimand gate: `blocking_pass: true` over 3 per-instrument cells. Determinism: `pass: true` (mode `IMMEDIATE_REHASH`). Row accounting: `pass: true` (native 1,303,965 rows, management 1,604,880 rows, 20,061 origins, no missing, extra or duplicate key).

### Emission counts

| Count | Value |
| --- | --- |
| Eligible origins | 20,061 |
| Orders | 649,071 |
| Fills | 316,942 |
| Positions (opened) | 158,547 |
| Native episode rows | 1,303,965 |
| Management policy rows | 1,604,880 |
| State-ledger rows | 3,686,502 |

### Device populations from the canonical analysis

Counts are population-labelled exactly as emitted. `eligible_origin_n` counts scheduled opportunities, `entry_fill_n` counts actual fills, `close_n` counts confirmed closes.

| Device | rows | eligible_origin_n | entry_fill_n | close_n |
| --- | ---: | ---: | ---: | ---: |
| TARGET | 528 | null | 49,048 | 48,820 |
| STOP | 480 | null | 34,032 | 33,840 |
| TRAIL | 270 | null | 27,573 | 27,456 |
| HOLD | 360 | null | 77,732 | 77,700 |
| SIZE | 264 | null | 74,712 | 74,712 |

Episode-state sections present in this universe (state as emitted by the state ledger):

| State | rows |
| --- | ---: |
| `NO_EVENT` | 1,924,156 |
| `NO_FEATURE` | 224,090 |
| `ORDER_CREATED` | 760,599 |

### Native lattice and lenses

- Entry variants present: `BREAKOUT`
- Arm classes present: `FIXED_NATIVE`, `NATIVE`, `NATIVE_COMBINATION`
- Orientation pairs present: `DIRECT_DIRECT`, `DIRECT_REVERSE`, `REVERSE_DIRECT`, `REVERSE_REVERSE`
- Estimand lenses present: `COMMON_CLOSE_TRADE`, `COMMON_ORIGIN_OCCUPANCY_INCLUSIVE`
- `native_parameter_origins.parquet` rows: 729; paired trade rows: 174; block length: 24 bars; interpretation field: `DESCRIPTIVE_ONLY`

### Control availability

| Control | rows | stage | rows with an estimate | rows null with a reason |
| --- | ---: | --- | ---: | ---: |
| `FIXED_DEVICE` | 1 | `COMPUTED` | 0 | 1 |
| `FIXED_NATIVE_PARAMETER` | 1 | `COMPUTED` | 0 | 1 |
| `MAGNITUDE_MATCH` | 768 | `COMPUTED` | 768 | 0 |
| `TIME_DERANGEMENT` | 192 | `COMPUTED` | 192 | 0 |

Engine-side control inputs recorded in `controls.json`: time derangement 44,703 rows, seed 240730, `zero_fixed_points: true`; magnitude match 19,542 rows (9,772 selected, 9,770 excluded). Controls are informative and gate nothing.

### Analysis artifacts

- Directory: `python/experiments/SPDR-021/results/analysis/ctrader/`
- Artifacts: 13 of 13 declared
- Production pass: 376.868 s / 2.771 GB
- Independent reproduction pass: 312.691 s / 2.650 GB
- Reproduction evidence: `python/experiments/SPDR-021/results/analysis/reproduction-hashes.json`

---

## Universe 2 — crypto

### Run identity

| Field | Value |
| --- | --- |
| Run id | `SPDR-021-crypto-train-20260803T140238Z` |
| Absolute path | `/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/data/nautilus_runs/SPDR-021-crypto-train-20260803T140238Z` |
| Catalog path | `/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/data/catalog` |
| Manifest path | `/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-011/artifacts/fence-manifest.json` |
| Manifest sha256 | `35d3375ec5ec18b3c6e4c5eec814ade4d492bd60e3fb694fed19e16bc2c00448` |
| Band | TRAIN |
| `train_start_utc` | `2021-06-29T06:53:00Z` |
| `train_end_utc` | `2023-12-18T00:00:00Z` |
| Symbols | BTCUSDT, ETHUSDT, SOLUSDT, AVAXUSDT, ORDIUSDT, 1000BONKUSDT, TIAUSDT, DOGEUSDT, XRPUSDT, LINKUSDT, ADAUSDT, BIGTIMEUSDT, BLURUSDT, 1000PEPEUSDT, 1000LUNCUSDT, MATICUSDT, INJUSDT, SEIUSDT, BNBUSDT, WLDUSDT, PYTHUSDT, DYDXUSDT, GALAUSDT, OPUSDT, 1000RATSUSDT (25) |
| Work units | 25 declared, 25 completed |
| `native_arms` | 65 |
| `native_adaptive_arms` | 64 |
| `management_arms` | 84 |
| `base_size_increments` | 1,000 |
| Execution workers | 2 |
| Execution wall time | 1,167 s |
| Raw output size | 3,596,712 KiB |

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

Canonical estimand gate: `blocking_pass: true` over 25 per-instrument cells. Determinism: `pass: true` (mode `IMMEDIATE_REHASH`). Row accounting: `pass: true` (native 6,640,400 rows, management 8,172,800 rows, 102,160 origins, no missing, extra or duplicate key).

### Emission counts

| Count | Value |
| --- | --- |
| Eligible origins | 102,160 |
| Orders | 3,031,022 |
| Fills | 1,541,313 |
| Positions (opened) | 771,135 |
| Native episode rows | 6,640,400 |
| Management policy rows | 8,172,800 |
| State-ledger rows | 18,473,611 |

### Device populations from the canonical analysis

Counts are population-labelled exactly as emitted. `eligible_origin_n` counts scheduled opportunities, `entry_fill_n` counts actual fills, `close_n` counts confirmed closes.

| Device | rows | eligible_origin_n | entry_fill_n | close_n |
| --- | ---: | ---: | ---: | ---: |
| TARGET | 4,400 | null | 207,292 | 206,020 |
| STOP | 4,000 | null | 209,676 | 208,224 |
| TRAIL | 2,250 | null | 112,113 | 111,507 |
| HOLD | 3,000 | null | 382,276 | 382,224 |
| SIZE | 2,200 | null | 372,680 | 372,636 |

Episode-state sections present in this universe (state as emitted by the state ledger):

| State | rows |
| --- | ---: |
| `NO_EVENT` | 10,057,294 |
| `NO_FEATURE` | 1,242,894 |
| `ORDER_CREATED` | 3,513,012 |

### Native lattice and lenses

- Entry variants present: `BREAKOUT`
- Arm classes present: `FIXED_NATIVE`, `NATIVE`, `NATIVE_COMBINATION`
- Orientation pairs present: `DIRECT_DIRECT`, `DIRECT_REVERSE`, `REVERSE_DIRECT`, `REVERSE_REVERSE`
- Estimand lenses present: `COMMON_CLOSE_TRADE`, `COMMON_ORIGIN_OCCUPANCY_INCLUSIVE`
- `native_parameter_origins.parquet` rows: 6,011; paired trade rows: 1,536; block length: 24 bars; interpretation field: `DESCRIPTIVE_ONLY`

### Control availability

| Control | rows | stage | rows with an estimate | rows null with a reason |
| --- | ---: | --- | ---: | ---: |
| `FIXED_DEVICE` | 1 | `COMPUTED` | 0 | 1 |
| `FIXED_NATIVE_PARAMETER` | 1 | `COMPUTED` | 0 | 1 |
| `MAGNITUDE_MATCH` | 6,400 | `COMPUTED` | 6,400 | 0 |
| `TIME_DERANGEMENT` | 1,600 | `COMPUTED` | 1,600 | 0 |

Engine-side control inputs recorded in `controls.json`: time derangement 231,146 rows, seed 240730, `zero_fixed_points: true`; magnitude match 96,305 rows (48,158 selected, 48,147 excluded). Controls are informative and gate nothing.

### Analysis artifacts

- Directory: `python/experiments/SPDR-021/results/analysis/crypto/`
- Artifacts: 13 of 13 declared
- Production pass: 1,987.793 s / 3.070 GB
- Independent reproduction pass: 2,054.076 s / 3.052 GB
- Reproduction evidence: `python/experiments/SPDR-021/results/analysis/reproduction-hashes.json`

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
