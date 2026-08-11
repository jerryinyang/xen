# Dataset reference

**Status:** Binding live dataset facts

This document describes the data materialized in the repository and the rules for using it. It is a snapshot of the pinned research inputs, not a promise that a future download will have the same universe or date range.

## 1. Primary Bybit catalog

The primary catalog is one-minute Bybit linear-perpetual data derived from public trades. Raw trade files are not retained in the repository; the derivation preserves the aggregate volume identity used by the catalog.

The admission snapshot is:

| Item | Count or fact |
|---|---:|
| Initial census | 910 symbols |
| Admitted | 894 |
| Specification-incomplete | 9 |
| Structurally readable | 903 (`894 + 9`) |
| Corrupt and not admitted | 1 |
| No bars | 1 |
| Operator-omitted | 5 |
| Total bars for admitted plus specification-incomplete | 672,138,742 |
| API instrument specifications | 612 |
| Inferred specifications | 282 |

The 903 readable symbols passed structural re-verification. The nine specification-incomplete symbols have readable bars but do not have complete return-level specifications; they are not silently interchangeable with the 894 admitted symbols. The five operator-omitted symbols, the no-bar placeholder, and the corrupt symbol are outside the admitted research universe.

The materialized primary catalog occupies approximately 23 GB. Its layout is:

```text
data/catalog/
└── data/
    ├── bar/
    │   └── <SYMBOL>-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL/
    │       └── <start>_<end>.parquet
    └── crypto_perpetual/
        └── <SYMBOL>-LINEAR.BYBIT/
            └── <instrument-metadata>.parquet
```

The current instrument identifier is `{SYMBOL}-LINEAR.BYBIT`. The bar type is `<SYMBOL>-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL`.

## 2. Bar semantics

- Bars are one-minute aggregates of Bybit public trades.
- The bar timestamp is the close time: a field is usable only after the bar has closed.
- `open`, `high`, `low`, `close`, and aggregate `volume` describe the traded bar; they are not a quote stream.
- `volume` is the sum of the retained aggregate trade sizes. Derivation and re-verification enforce the volume identity.
- Missing minutes and no-trade minutes are data facts. They must be reported or handled by the registered estimator; they must not be silently filled with future information.
- There is no live L2, quote, detector, or orderflow feature-store layer in this dataset contract.

All feature reads obey the registered causal rule. For a decision at bar `t`, the default usable feature boundary is the close of `t-1`.

## 3. Signed-bar diagnostic catalog

The signed catalog is a separate, diagnostic TRAIN input. It is not the primary full-universe catalog.

```text
data/catalog_sigbar/train/
└── data/custom_signed_bar/
    └── <SYMBOL>-LINEAR.BYBIT/
        └── <start>_<end>.parquet
```

The materialized signed catalog contains five instruments, 3,731,908 rows, and 90 parquet files:

- `BTCUSDT-LINEAR.BYBIT`
- `DOGEUSDT-LINEAR.BYBIT`
- `ETHUSDT-LINEAR.BYBIT`
- `SOLUSDT-LINEAR.BYBIT`
- `XRPUSDT-LINEAR.BYBIT`

The signed-catalog tree attestation is:

```text
rows: 3,731,908
symbols: 5
parquet_files: 90
tree_sha256: d4b7bbed7e0c039cc8c74a05e0f8747796c75016957d1e7c5f7c2feb20f7d2b9
```

The signed schema records:

- `buy_volume`: taker-buy volume, where the aggressor lifted the ask;
- `sell_volume`: taker-sell volume, where the aggressor hit the bid;
- `delta = buy_volume - sell_volume`;
- `n_trades`: participation count;
- `spread_feature`: legacy storage for mean buy-print price minus mean sell-print price, in basis points;
- `spread_status` and `pipeline_version`.

`buy_volume + sell_volume == volume` is exact for the bar aggregate. `delta` is an exact bar aggregate, not an estimate of per-level or intrabar orderflow. The signed catalog contains no valid per-level attribution.

The stored mean-price-skew value is `1e4 × (MeanBuy − MeanSell) / ((MeanBuy + MeanSell) / 2)`. It is not quote spread, executable spread, or a liquidity estimate. Analytical access must rename it to `MeanPriceSkewBps` and attach status `UNUSABLE_AS_SPREAD`. No consumer may apply a tick-size floor or interpret it as a tradable cost.

The signed materialization contains TRAIN rows only. It contains no TEST or lifetime-HOLDOUT rows.

## 4. cTrader compatibility catalog

The cTrader catalog is retained only for compatibility with explicitly scoped legacy comparisons. It is not the primary data source for current Bybit research and does not change the programme's event-driven execution or cost boundary.

```text
data/catalog_ctrader/
└── data/
    ├── bar/
    │   ├── EURUSD.CTrader-1-MINUTE-LAST-EXTERNAL/<start>_<end>.parquet
    │   ├── XAUUSD.CTrader-1-MINUTE-LAST-EXTERNAL/<start>_<end>.parquet
    │   └── USTEC.CTrader-1-MINUTE-LAST-EXTERNAL/<start>_<end>.parquet
    ├── currency_pair/EURUSD.CTrader/<instrument-metadata>.parquet
    └── cfd/{XAUUSD,USTEC}.CTrader/<instrument-metadata>.parquet
```

The materialization is approximately 203 MB and contains three instruments. Its bar files begin on 2021-06-02 and end on 2026-06-19, with the exact per-file range encoded in each filename. Its volume field is source-specific and must not be treated as Bybit taker-side volume.

## 5. Chronological fence

All current price-primary reads use these pinned UTC boundaries:

| Boundary | UTC value |
|---|---|
| Analysis start | `2021-06-29T06:53:00Z` |
| TRAIN end / TEST start | `2023-12-18T00:00:00Z` |
| TEST end / lifetime HOLDOUT start | `2025-01-08T00:00:00Z` |
| Catalog data end | `2026-07-14T23:59:00Z` |
| Engine pin | Nautilus `1.230.0` |
| Fence manifest SHA-256 | `35d3375ec5ec18b3c6e4c5eec814ade4d492bd60e3fb694fed19e16bc2c00448` |

The nested analysis split uses a 70% analysis fraction and a 70% TRAIN fraction within analysis. A design may create narrower chronological windows inside these bounds, but it may not move the global boundaries after seeing outcomes.

Use `fenced_bar_query` and `assert_within_fence` from `python/src/xen/nautilus/catalog_fence.py` for catalog access. The sanctioned bands are `TRAIN` and `TEST`; `HOLDOUT` is refused unconditionally. A TEST read is a counted operator-authorized event, not an ordinary exploratory query.

## 6. Emission inputs and outputs

The current clean slate contains no materialized strategy-run output directory. An authorized run creates its own destination and writes the emission contract there. The destination is passed to `write_emission_v1`; it is not inferred from a historical experiment path.

An emission-contract-v1 directory contains:

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

The metadata records the run configuration hash, catalog identity, engine version, platform, instrument map, output counts, fence attestation, and deterministic event-log hash. Missing or stubbed required artifacts invalidate the run.

## 7. Cost and claim boundary

The datasets do not contain spread, commission, swap, funding, or other execution-cost observations suitable for a net-performance claim. Unless a scoped exception is authorized and recorded before execution, every result is gross and cost-free. Therefore dataset presence, coverage, and clean engine reconciliation do not establish tradability, deployability, or cost-complete performance. The disclosure is:

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
