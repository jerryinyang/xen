# XENA-EPSOSC-001 — design clause → code map

| Design clause | Code location |
|---|---|
| §1 mechanism: VOLARM armed-stretch fade; STRETCH×1h disclosure | `epsosc_strategy.py` `EpsoscStrategy`; `features.py` |
| §1 VOLARM arm ATR14/ATR56 ≥ 1.25 fixed | `features.py` `VOLARM_RATIO`; `StreamingLtfState.armed` |
| §1 stretch ≥ k · ATR; fade direction | `features.py` `event_side` |
| §2 object identity: market-order episode; no re-entry while open | `epsosc_strategy.py` `_submit_entry` / gate skip while open |
| §2 clear RET_ANCHOR / HYBRID H=W; no TIME-only | `epsosc_strategy.py` `_on_ltf_complete`; config rejects TIME |
| §3 estimand: emission v1 + finite SlPrice | `run_batch.py` `write_emission_v1` + `attach_sl_price` + `materialize_xena` |
| §3 SlPrice = Entry − side × 1.0 × k·ATR14[t−1] | `epsosc_strategy.py` `on_order_filled` |
| §3 segment-end censoring + fraction disclosure | `run_batch.py` `censored_fraction` → `censoring.json` + `censoring_disclosure.json` |
| §3 L-16 episode-native; no local accounting | shim only (`adjudication_shim`); no accounting in `code/` |
| §4.1 causal top-10 membership, daily 00:00 UTC, `trailing_volume` pin | `build_universe.py` `build_membership_delisted_inclusive` + strategy day-set gate |
| §4.1 symbol axis ≥90 TRAIN membership-days, delisted incl. | `build_universe.py` default path (`include_delisted=True`) |
| §4.2 16 binding variants/symbol + STRETCH **8**/symbol disclosure | `build_universe.py` `build_candidates` |
| §4.3 cadence + F\*=16 + true_α≤0.06 attestation | `emit_pre_search_floor.py` → `cadence_fstar_attestation.json` |
| §5 stage bands frozen fracs on TRAIN | `build_universe.py` `stage_bands_from_fence` → `stage_bands.json` |
| §5 content pin sha abbb1842… (not file-bytes) | `build_universe.py` `content_pin_sha256` |
| §5 cost stack + funding × episode duration | `build_universe.py` `cost_bps_for_hold_hours`; floor script |
| §5 multi_instrument_single_node, L-30, L-31 | `run_batch.py` `run_param_group` |
| §6 pre-search gross floor | `emit_pre_search_floor.py` → `pre_search_gross_floor.*` |
| §7–§8 controls / tripwire | analysis stage only (`analysis_code/` later) |
| §13 golden trace | QA derives; developer does not generate |

## DEVIATIONS

| ID | Severity | Note |
|---|---|---|
| — | — | **None open.** QA run-1 D1 false alarm fixed (content pin). QA run-1 D2 fixed (delisted-inclusive default). Escape hatch `--reuse-spdr-membership` remains but is non-production without operator approval. |

## QA run-1 fix map

| QA issue | Resolution |
|---|---|
| #1 MEDIUM D2 membership listed-only | Default `build_universe.py` recomputes ADMITTED+delisted via pin trailing_volume |
| #2 LOW false D1 pin hash | `content_pin_sha256` = artifact content pin abbb1842…; file-bytes audit-only |
| #3 LOW USDT-notional wording | design.md §4.1 cites pin `trailing_volume` |
| #4 LOW STRETCH 16/symbol | design.md §4.2 → **8/symbol** |
| #6 INFO true_α | `true_alpha_priced_le: 0.06` on manifest registry + cadence attestation |

## How to run (implementation only)

```bash
cd python
# Production membership (delisted-inclusive) + manifest + stage bands
uv run python experiments/XENA-EPSOSC-001/code/build_universe.py

# Pre-search floor + cadence/F*=16 + true_α attestation
uv run python experiments/XENA-EPSOSC-001/code/emit_pre_search_floor.py

# smoke emission (re-run after membership recompute — prior smoke used SPDR membership)
uv run python experiments/XENA-EPSOSC-001/code/run_batch.py --smoke
```

Do **not** run `xen.xena.search` / `gate_universe` / `run_final_gate` until QA APPROVE + operator execution gate.
