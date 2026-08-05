# SPDR-021/022/023 First-Pass Invalidation

- **Invalidated:** 2026-08-03
- **Run stamp:** `20260731T004708Z`
- **Scope:** all six TRAIN cells and every analysis/report derived from them
- **Disposition:** invalid for interpretation; full amended six-cell rerun required
- **Authority:** operator selected engine fix plus full rerun on 2026-08-03

No economic result, effect table, experiment verdict or family decision from this stamp is retained.
The defects below concern execution lifecycle and reporting populations.

## Six confirmed defects

1. **Exit lifecycle.** A breach market entry could fill before Nautilus exposed its position to
   the entry-fill callback. Protective exits submitted there could be denied or rejected, while
   the arm and position remained open. The callback timing and absorbing `EXIT_DENIED` behavior
   are confirmed. A through-market trigger is one observed venue response, but is not established
   as the sole cause.
2. **SIZE horizon.** SIZE changed quantity but inherited no strategy-level closing horizon. It
   closed zero episodes in every cell. It must use the strategy-fixed hold: one H1 bar in
   SPDR-021 and four H1 bars in SPDR-022/023. Pure TARGET/STOP/TRAIL arms remain price-only.
3. **Shared-fill identity.** `native_parameter_shared_trades.parquet` used planned `entry_ts`
   rather than engine-recorded `_entry_ns`. It therefore omitted filled breakout stop entries and
   retained scheduled breach entries that did not fill.
4. **Population mixing.** Common-origin zero-exposure rows are valid for the occupancy-inclusive
   per-opportunity estimand, but are not trades. The first-pass analysis did not separately expose
   actual common fills and common closes with matching uncertainty.
5. **Ambiguous counts.** Device `episode_n`/`effective_n` could describe scheduled opportunities
   where the label read as filled or closed episodes. Eligible origins, fills, closes, common fills
   and common closes were not separately named.
6. **Deferred controls.** The required time-derangement and magnitude-matched controls were only
   inventoried. All six `controls.parquet` files marked both rows
   `DEFERRED_TO_STAGE_8`; no outcome-bearing control estimate was produced.

## Raw lifecycle evidence

Counts below were independently read from each root `run_summary.json` and projected scans of
`episode_results.parquet`. `filled`/`closed` are ledger states. `exit denied` excludes ordinary
entry denials. SIZE is shown as `filled/closed`; every denominator is the raw state ledger, not an
analysis summary.

| Run | Origins | Episodes | Policy rows | Filled | Closed | Exit denied | Exit rejected | Open at fence | SIZE filled/closed | SIZE incomplete |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SPDR-021 cTrader | 20,061 | 1,303,965 | 1,604,880 | 118,187 | 117,971 | 0 | 178 | 1 | 33 / 0 | 0 |
| SPDR-021 crypto | 102,160 | 6,640,400 | 8,172,800 | 567,523 | 565,814 | 0 | 1,097 | 53 | 275 / 0 | 0 |
| SPDR-022 cTrader | 44,700 | 5,811,000 | 7,152,000 | 791,630 | 791,013 | 423 | 0 | 25 | 66 / 0 | 660 |
| SPDR-022 crypto | 231,121 | 30,045,730 | 36,979,360 | 4,028,998 | 4,023,653 | 3,055 | 25 | 470 | 550 / 0 | 5,500 |
| SPDR-023 cTrader | 44,700 | 5,811,000 | 7,152,000 | 797,063 | 796,444 | 430 | 0 | 28 | 66 / 0 | 660 |
| SPDR-023 crypto | 231,121 | 30,045,730 | 36,979,360 | 4,011,621 | 4,006,274 | 3,035 | 51 | 462 | 550 / 0 | 5,500 |

The first-pass shared-trade outputs reinforce the identity defect: SPDR-021 emitted zero rows in
both universes despite filled stop entries, while SPDR-022 and SPDR-023 each emitted 4,792,565
cTrader and 24,543,794 crypto rows from the planned-entry route. These counts are evidence of the
population error, not valid trade populations.

## Exact invalid raw runs and source pins

All six paths were local and non-symlink directories before deletion. The complete per-artifact
SHA-256 maps remain embedded in each `integrity_selfcheck.json` until Task 5 removes the run. The
compact pins below identify the root config, state ledger and complete hash manifest.

| Exact path | KiB | config SHA-256 | episode-results SHA-256 | integrity manifest SHA-256 |
|---|---:|---|---|---|
| `data/nautilus_runs/SPDR-021-ctrader-train-20260731T004708Z` | 624,820 | `6d90d71b499509cb3cc634f3fb5ef9d2b94c8db3fa6a142f2c36817fd7658821` | `c142c2ed049c6bc67e49759e86a10084fed128dbce5d8932bc785b29675205f5` | `549b3a93e4a89a229b5f9762ab2fdd42b932b08c565812c72e748d6737193a7d` |
| `data/nautilus_runs/SPDR-021-crypto-train-20260731T004708Z` | 3,025,056 | `68dffaf458fb3c965aa6011088a32e2c835781b2485d4de025a59557b40bd4e6` | `3f2b575c5cfa66b0d9c95614963d8241af32eb9cd8937276595a9ab24200e02c` | `09a2093b0cac75524d5fb3a1956fd4480c320c984f7c678c6a555025bff82b5a` |
| `data/nautilus_runs/SPDR-022-ctrader-train-20260731T004708Z` | 2,881,760 | `7b5b2622a8bed619f36d0a639e36458f7cc0684335905696ce8606e12cafa78a` | `b22c3a24e423fa049d404ca90255ed263c88be112df45b7aa77a61f4cb1e7ec5` | `fb8a797e23d17867cea86169200ddc98c9c04d6bd1d55532fda6df64b45236ff` |
| `data/nautilus_runs/SPDR-022-crypto-train-20260731T004708Z` | 15,165,360 | `914e8ea4d01a4bdba617424b0210bf6270680d13e7726b1a1d104d4465796d76` | `9605b637b596bcbdd019c69aebb662d0dca99ec4c4d22395df4e9cd9b67b9323` | `33cb598091917f2c6ea146df4cfc6a2cbd78cf08ef928673ae6bddbf9aeadcf8` |
| `data/nautilus_runs/SPDR-023-ctrader-train-20260731T004708Z` | 2,893,972 | `582abc6b947948aaea892142788486e60d132b3b30864fb71db40ad94366d849` | `58e33934cfafa39e3e44eb4591446373634b2bacd35f8025e6be39cad2bdd23a` | `46e6432cb64d8bdba50c897893a22941fbf5229ca5f600ec87f54ebf1dad6e02` |
| `data/nautilus_runs/SPDR-023-crypto-train-20260731T004708Z` | 14,878,824 | `c8d6ba4463b6f7e290de018b6c9e0743e69ad9623b7eb0b6ad532c89aae1b9b1` | `6c7ea73a191146749e4f619c162c8e7f7dbd056b19c15132d7140dac1745107c` | `4c6b6b53ac469e726d57a3e4f0009b00e509011867d6cd1e15db52939b06eac2` |

The pinned universe manifests remain `4cdc7b01dd47200710d0d961639d55d52e1129ca89096e841eafd816b6061de0`
for cTrader and `35d3375ec5ec18b3c6e4c5eec814ade4d492bd60e3fb694fed19e16bc2c00448`
for crypto.

## Invalid derived artifacts

Task 5 removes the six raw paths above plus each SPDR-021/022/023 `results/analysis/`,
`results/analyst/`, `screen.md` and `analysis.md`. Provisional scripts are reconciled there:
generic methods are retained only if corrected and tested; stamp-specific or defect-explainer-only
scripts are removed. No first-pass effect table is copied into the corrected record.

### Provisional-script reconciliation

Retained only the three tested canonical wrappers:

- `python/experiments/SPDR-021/analysis_code/analyse.py`
- `python/experiments/SPDR-022/analysis_code/analyse.py`
- `python/experiments/SPDR-023/analysis_code/analyse.py`

Removed the first-pass-only analyst scripts because their only inputs were the invalid raw stamp or
its derived `results/analysis`/`results/analyst` tables, and the tested corrected implementation in
`python/src/xen/adaptive_management/analysis.py` supersedes them:

- SPDR-021: `decompose.py`, `devices.py`, `interrogate.py`, `report_tables.py`,
  `nan_safe_summaries.py`
- SPDR-022: `a1_populations.py`, `a2_native_arms.py`, `a3_devices.py`,
  `a4_report_tables.py`, `a5_device_paired.py`, `a6_finalise_tables.py`
- SPDR-023: `x1_census.py`, `x2_native_paired.py`, `x3_device_census.py`,
  `x4_crypto_provenance.py`, `x5_device_outcomes.py`

## Boundary

This invalidation changes no arm, component, combination, date, universe, entry side, orientation
or estimand. It authorises no TEST/holdout read, XENA action, deployment, family-status transition
or experiment verdict.
