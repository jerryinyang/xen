# XENA-HTFCAP-001 — design clause → code map (post QA-2 REVISE)

| Design clause | Code location |
|---|---|
| §1 mechanism: DI×VOL / DI_ADX×VOL gate, fixed hold H, market legs | `htfcap_strategy.py` `HtfCapStrategy` |
| §2 object identity: market-order leg, greedy non-overlap (no pyramiding) | `htfcap_strategy.py` `_on_ltf_complete` greedy gate + `_open_legs`/`_next_allowed_ns` |
| §3 estimand: emission v1 + finite synthetic SlPrice | `run_batch.py` `write_emission_v1` + `anchor_ledger_open_to_open` + `materialize_xena` |
| §3 SlPrice = Entry − side × 1.0 × HTF ATR(14) | `htfcap_strategy.py` `on_position_opened`; re-anchored in `run_batch.anchor_ledger_open_to_open` |
| §3 RealizedBps via canonical shim (no local accounting, QA-2 #13) | `run_batch.py` `positions_ledger_to_cis_trades(anchored_ledger)` |
| §3 L-29 EntryFill = next 15m RealOpen | `htfcap_strategy.py` complete LTF on **last 1m** of window → market fills next 1m open; `run_batch.anchor_ledger_open_to_open` floors to 15m grid |
| §4.1 BTC+SOL binding, ETH disclosure | `build_universe.py` |
| §4.2 108-cell grid | `build_universe.py` `build_candidates` (assert n=108) |
| §4.3 feature defs SPDR-006 (no retune) | `features.py` |
| §4.3 clock-aligned 4h HTF (aggregate_ohlc buckets) | `htfcap_strategy.py` `_agg_bucket_id` / HTF roll on bucket change |
| §4.3 gate confirmed HTF only (strict map timing) | finalize HTF on **new** HTF bucket, not closing LTF |
| §4.3 greedy re-entry = SPDR `greedy_entries` (next entry ≥ prev entry + H) | `htfcap_strategy.py` `_next_allowed_ns = t + H·15m`; re-entry AT exit bar (D3) |
| §4.4 LOW cadence attestation | `cadence_attestation.py` → `results/cadence_attestation.json` |
| §5 stage bands frozen fracs | `build_universe.py` `stage_bands_from_fence` |
| §5 pin body-hash abbb1842… verified | `build_universe.py` `pin_body_sha256` + artifact check |
| §5 cost stack + funding | `build_universe.py` `cost_bps_for_hold` |
| §5 multi_instrument_single_node, L-30, L-31 | `run_batch.py` `run_param_group` |
| §6 pre-search gross floor | `emit_pre_search_floor.py` |
| §7 RAND-sign 25-seed battery | `analysis_code/controls.py` `rand_sign_battery` |
| §8 gate-schedule derangement, 15m grid, block ≥64 LTF=16h (L-28 hard-block) | `analysis_code/controls.py` `_build_15m_open_grid` + `gate_derangement` |
| §13 golden-trace | QA derives; developer does not generate |

## DEVIATIONS

| ID | Sev | Note |
|---|---|---|
| D2 | NEUTRAL | Nautilus L1 bar matching fills market at **close** (VAL-008 same). `run_batch.anchor_ledger_open_to_open` sets emission Entry/Exit to catalog **15m RealOpen** for L-29. Engine remains causal schedule source. |
| D3 | operator-approved 2026-07-18 (QA-2 #11) | Venue OMS = **HEDGING** (not NETTING). Greedy back-to-back re-entry needs leg_{k+1} to OPEN at the same 15m open where leg_k CLOSES; NETTING would net a coincident close+open. Each leg = distinct position id; legs non-overlapping (next entry = prev exit) so no true concurrency. Differs from NETTING topology in INFR-014 S1 — re-smoked clean (multi-instrument BTC+SOL+ETH). |

## QA-2 fixes (this revision)

- **#10 (HARD, §8):** `gate_derangement` reworked to the **15m LTF open grid** (`_build_15m_open_grid`). Blocks now ≥ 64×15m = **16h ≥ max hold H**; deranged exit offset in **15m** steps → matched entry/exit horizon. Smoke: `n_grid_15m=5856`, `n_blocks=91`, `block_hours=16.0` (was 1-min grid: 1372 blocks, 1.07h).
- **#11 (operator: align to greedy):** strategy rewritten to timestamp-driven greedy legs; re-entry AT exit bar via HEDGING (D3). Smoke BTC DI×VOL v1.25 H16 = **41 legs = SPDR greedy** (was 39); first leg 2023-06-21T04:15 @ 28680.50 unchanged; entries 04:15/08:15/12:15/16:15 back-to-back.
- **#13 (low):** `RealizedBps` now shim-derived from the anchored ledger (`anchor_ledger_open_to_open` → `positions_ledger_to_cis_trades`); no local bps recompute.

**Design note for QA-3 / designer:** §4.3 wording "re-entry allowed at first gate-ON after exit" should be updated to state **greedy back-to-back (SPDR `greedy_entries`, next entry ≥ prev entry + H)** per the operator's #11 decision — recorded here, design.md text not edited by developer.

Pin body-hash `abbb1842…` PASS via registry body digest.

## How to run

```bash
cd python
uv run python experiments/XENA-HTFCAP-001/code/build_universe.py
uv run python experiments/XENA-HTFCAP-001/code/run_batch.py --smoke
uv run python experiments/XENA-HTFCAP-001/code/cadence_attestation.py
uv run python experiments/XENA-HTFCAP-001/code/emit_pre_search_floor.py
uv run python experiments/XENA-HTFCAP-001/analysis_code/controls.py \
  --candidate BTCUSDT__DI_VOL_HI__v1.25__adxna__H16 \
  --out experiments/XENA-HTFCAP-001/results/controls_smoke.json
# full TRAIN (operator execution gate):
# uv run python experiments/XENA-HTFCAP-001/code/run_batch.py --all
```
