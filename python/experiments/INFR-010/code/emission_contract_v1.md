# Nautilus emission contract v1

**Version string:** `nautilus-emission-v1`  
**Root:** `data/nautilus_runs/<run_id>/`  
**Role:** Nautilus equivalent of `data/strategy_runs/<ID>/`; input to
`xen.estimand_validation` v2 (Phase C) and `xen.nautilus.adjudication_shim`.

## Files

| File | Required | Contents |
|------|----------|----------|
| `run_metadata.json` | yes | config hash, catalog version/path, nautilus pin + platform, instrument map ref, event_log_sha256, n_* counts |
| `fills.parquet` | yes | order fills (economic) |
| `orders.parquet` | yes | order lifecycle rows |
| `positions_ledger.parquet` | yes | closed/open legs → `cis_trades` via shim |
| `bar_marks.parquet` | yes | bar OHLC marks → adjudication `positions` |
| `event_log.jsonl` | yes | UUID-stripped deterministic log (fills/orders/positions) |
| `instrument_id_map.json` | yes | `{archive_symbol: "SYM-LINEAR.BYBIT"}` |
| `fence_attestation.json` | yes | analysis fence; **STUB** until INFR-011 A6 |

## `run_metadata.json` (minimum)

```json
{
  "emission_contract_version": "nautilus-emission-v1",
  "config_hash": "<sha256 of run_config>",
  "run_config": {},
  "catalog_version": null,
  "catalog_path": null,
  "nautilus_version": "1.230.0",
  "platform": "<platform.platform()>",
  "instrument_id_map": {"XRPUSDT": "XRPUSDT-LINEAR.BYBIT"},
  "event_log_sha256": "<sha256 of event_log.jsonl>",
  "fence_attestation_path": "fence_attestation.json"
}
```

## Deterministic event log

`event_log.jsonl` excludes process-ephemeral UUIDs (`init_id`). Kept fields:
client_order_id, instrument_id, side, quantity, filled_qty, avg_px, status,
liquidity_side, ts_*, commissions (joined). Identical config + data →
byte-identical log (verified 3× fresh processes, Phase B).

## Shim → `xen.adjudication`

| Emission | Adjudication |
|----------|--------------|
| `bar_marks` (`SourceCloseTime`, `RealOpen`, …) | `positions` |
| `positions_ledger` (entry, avg_px_open/close, ts_opened/closed) | `cis_trades` |

```
RealizedBps = Direction * (ExitFillPrice - EntryFillPrice) / EntryFillPrice * 1e4
```

API: `xen.nautilus.adjudication_shim.adjudicate_emission(run_dir)`.

## What estimand_validation v2 will gate (Phase C)

- schema (required cols; monotonic `SourceCloseTime`)
- fence (`analysis_end_utc` vs last bar — needs INFR-011 fence pin)
- reconciliation (`assemble_multileg_bps` vs leg `RealizedBps`)
- manifest (expected instruments)
- catalog version + config hash attestation
