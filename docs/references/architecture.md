# Research architecture

**Status:** Binding live architecture

The current Xen architecture is an event-driven, price-primary research system. The engine produces the execution record; Python validates, composes, and analyses that record. No vectorized price backtest, hidden local accounting, or quote-spread claim is part of the live architecture.

## 1. System boundary

```text
materialized catalog
        │
        ▼
fenced catalog read ──► Nautilus event-driven run ──► emission contract
        │                                            │
        └────────────────────────────────────────────┘
                             ▼
                 Python validation and referee analysis
                             ▼
                     operator evidence handoff
```

The stages have distinct responsibilities:

1. The catalog supplies the registered price or diagnostic data.
2. The fence wrapper enforces the authorized chronological band.
3. Nautilus processes events, strategy state, orders, fills, positions, and marks.
4. The emission writer records the run identity and deterministic artifacts.
5. Python checks validity, computes the registered estimand, composes portfolios where required, and produces neutral evidence.
6. The operator assigns the final disposition.

## 2. Engine and execution contract

- The engine pin for the current catalog fence is Nautilus `1.230.0`.
- A strategy receives engine events and uses engine-native order and position state.
- A fill, order, position, or return may enter analysis only through the emitted record or a value explicitly derived from it.
- Python may perform chronological composition and adjudication after emission. It may not invent fills, replace engine account state, or replay prices with a vectorized shortcut.
- `python/src/xen/nautilus/emission.py` provides `EmissionPaths`, `write_emission_v1`, and `load_emission_v1` for the run contract.
- A platform pin, configuration hash, catalog identity, instrument map, output counts, fence attestation, and deterministic event-log hash are part of run identity.

The current clean slate has no materialized run-output directory. An authorized runner supplies a destination to `write_emission_v1`; the writer creates that per-run directory.

## 3. Data layers

The materialized data tree is:

```text
data/
├── catalog/
│   └── data/
│       ├── bar/
│       │   └── <SYMBOL>-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL/
│       │       └── <start>_<end>.parquet
│       └── crypto_perpetual/
│           └── <SYMBOL>-LINEAR.BYBIT/
│               └── <instrument-metadata>.parquet
├── catalog_sigbar/
│   └── train/data/custom_signed_bar/
│       └── <SYMBOL>-LINEAR.BYBIT/<start>_<end>.parquet
└── catalog_ctrader/
    └── data/{bar,currency_pair,cfd}/...
```

### Primary price layer

`data/catalog/` contains 903 structurally readable Bybit linear-perpetual instruments: 894 admitted instruments plus nine specification-incomplete instruments. The admitted-plus-incomplete materialization contains 672,138,742 bars. The data is one-minute public-trade OHLCV; raw trades are not retained.

The standard bar type is `<SYMBOL>-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL`. The bar becomes known at close. A feature used for a decision at `t` must obey the registered lag, normally `t-1` for bar research.

### Signed diagnostic layer

`data/catalog_sigbar/train/` contains five instruments, 3,731,908 rows, and 90 parquet files. It records taker-buy volume, taker-sell volume, exact aggregate delta, participation count, and a quarantined mean-price-skew storage field.

`buy_volume + sell_volume == volume` is exact for each signed bar. `delta` is an exact bar aggregate only; it does not attribute volume to price levels or claim intrabar orderflow knowledge. `python/src/xen/sigbar/access.py` exposes the legacy mean-price-skew field as `MeanPriceSkewBps` with status `UNUSABLE_AS_SPREAD`; it is not quote spread, executable spread, or a cost estimate.

The signed layer is TRAIN-only. It contains no TEST or lifetime-HOLDOUT rows and cannot be used to claim full-universe signed evidence.

### Compatibility layer

`data/catalog_ctrader/` contains three compatibility instruments: `EURUSD.CTrader`, `XAUUSD.CTrader`, and `USTEC.CTrader`. It is compatibility-only and is not the active source for current Bybit research. Its source-specific volume must not be interpreted as Bybit taker-side volume.

### Absent layers

There is no live L2 snapshot store, quote store, orderflow detector store, or feature-store contract. A future implementation of such a layer would require a new registered design; it cannot be inferred from the signed diagnostic catalog.

## 4. Chronological fence

The pinned global boundaries are:

| Boundary | UTC value |
|---|---|
| Analysis start | `2021-06-29T06:53:00Z` |
| TRAIN end / TEST start | `2023-12-18T00:00:00Z` |
| TEST end / lifetime HOLDOUT start | `2025-01-08T00:00:00Z` |
| Catalog data end | `2026-07-14T23:59:00Z` |
| Fence manifest SHA-256 | `35d3375ec5ec18b3c6e4c5eec814ade4d492bd60e3fb694fed19e16bc2c00448` |

The nested split uses 70% of the analysis range and then 70% of that analysis range for TRAIN. A run may use narrower predeclared windows inside the bounds. It may not move a boundary or tune a window after seeing the outcome.

`python/src/xen/nautilus/catalog_fence.py` is the sanctioned access boundary. Use `fenced_bar_query` or `assert_within_fence`. The only valid bands are `TRAIN` and `TEST`; a HOLDOUT query raises a fence violation. TEST access requires operator authorization and is counted in the gate ledger.

## 5. Emission-contract-v1

Each authorized Nautilus run writes a directory with this contract:

```text
<run_dir>/
├── run_metadata.json
├── fills.parquet
├── orders.parquet
├── positions_ledger.parquet
├── bar_marks.parquet
├── event_log.jsonl
├── instrument_id_map.json
└── fence_attestation.json
```

`run_metadata.json` records:

- `emission_contract_version`;
- a stable hash of the run configuration;
- catalog version and path as supplied to the runner;
- Nautilus version and platform;
- instrument map and output counts;
- fence-attestation identity;
- deterministic event-log SHA-256.

The event log strips process-ephemeral identifiers so the same pinned inputs and configuration can be compared across restarts. Differences caused by platform or floating-point behaviour must be declared by the run pin.

The emission is complete only when all required tables and JSON records exist and are non-stub where the design requires them. Reconciliation failures, missing files, empty required observations, or a non-pinned fence invalidate the run.

## 6. Analysis boundary

The referee layer consumes the emission and registered design. It may:

- validate fence, causality, reconciliation, determinism, non-degeneracy, and future-destroy integrity;
- calculate the predeclared effect, uncertainty, counts, sign distribution, and PSR context;
- compose XENA candidates in chronological order using the registered portfolio rule;
- produce neutral tables, diagnostics, and operator-routing metadata.

It may not:

- create local fills or account state that the engine did not emit;
- tune the strategy or comparator using TEST/HOLDOUT outcomes;
- turn a count, PSR, threshold, or score into a machine economic verdict;
- add a spread, commission, swap, funding, or slippage model without a scoped pre-run authorization;
- present gross, cost-free evidence as net performance, tradability, or deployability.

## 7. Cost boundary

The current architecture charges no execution costs:

```text
ZERO-COST-DISCLOSURE
  cost_model: NO_COST_CHARGED
  spread: not modeled
  commissions: not modeled
  swaps/funding: not modeled
  implication: every figure in this document is gross and cost-free; no spread,
    commission, or swap enters any calculation. Realised results would differ
    (likely worse) under any real cost schedule.
  prohibited_claims: fully-net, cost-complete, tradable, deployable
  lifting: only an explicit operator authorization may introduce a cost model
    for a scoped experiment; that authorization and its schedule are recorded
    in the experiment design before execution.
```

If a scoped experiment introduces a nonzero model, its schedule, scope, and effect on the estimand are recorded in the design before execution. The default architecture remains gross and cost-free.
