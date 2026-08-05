# SPDR-021/022/023 — implementation design checklist (Task 5, Step 5)

Recorded 2026-07-31. Every row carries a code location, a test location and observed evidence.
Smoke evidence is either the synthetic device smoke or the bounded real-catalog smoke
(SPDR-021, cTrader, EURUSD, TRAIN window 2023-08-24 → 2023-11-22, `/private/tmp/spdr-smoke-real`,
hard integrity `blocking_pass=true`, estimand validation `true`). Smoke artifacts stay under
`/private/tmp` and are not research results.

| # | Declared item | Observed | Code | Test | Smoke evidence |
|---|---|---|---|---|---|
| 1 | 8 executable component IDs | 8 | `contracts.Component` | `test_adaptive_management_contracts.py` | 8 component IDs across the smoke schedule |
| 2 | 64 / 128 / 128 adaptive native arms | 64 / 128 / 128 | `contracts.build_native_lattice` | `test_adaptive_management_runner.py::test_dry_run_reads_metadata_only_and_creates_no_results` | six dry runs print 64 / 128 / 128 |
| 3 | Fixed plus direct and reverse per native parameter | 1 fixed (021) / 2 fixed (022, 023) + DIRECT and REVERSE per parameter | `contracts.build_native_lattice`, `native_parameters` | `test_adaptive_management_runner.py::test_real_scheduler_materialises_complete_native_grid` | `native_parameter_schedule.parquet` carries `FIXED_NATIVE` plus both orientations |
| 4 | 4 orientation pairs per component | 4 per component per entry variant (8 across both variants in 022/023) | `contracts.build_native_lattice` | `test_adaptive_management_policies.py::test_breach_native_combination_materialises_all_four_z_h_pairs` | `NATIVE_COMBINATION` rows present in the smoke |
| 5 | All common origins incl. no-event / no-fill / blocked | 692 origins; states `NO_EVENT` 12 803, `BLOCKED_ACTIVE` 7 192, `EXPIRED` 4 563, `NO_FEATURE` 4 902, `REJECTED` 35, `ORDER_CREATED` 3 338, `FILLED` 63 488, `CLOSED` 4 502 | `entries`, `strategy._act_on_origin` | `test_adaptive_management_strategy.py::test_no_event_origin_is_recorded_not_dropped`, `::test_second_origin_while_arm_is_active_is_blocked_not_dropped` | smoke `episode_results.parquet` |
| 6 | 5 external devices | TARGET, STOP, TRAIL, HOLD, SIZE | `contracts.Device` | `test_adaptive_management_policies.py` | synthetic smoke closes one episode per device with the matching `exit_reason`; SIZE halves the entry quantity (50 vs 100) |
| 7 | Individual rows before combinations | 68 adaptive management arms, individual rows materialised before any combination | `policies.materialise_policy`, `runner._management_schedules` | `test_adaptive_management_policies.py` | `MANAGEMENT` 28 372 rows vs `MANAGEMENT_COMPONENT_COMBINATION` 2 076 |
| 8 | 5 allowed component combinations | 5 | `contracts.build_management_lattice` | `test_adaptive_management_contracts.py` | `MANAGEMENT_COMPONENT_COMBINATION` rows only |
| 9 | 3 allowed device combinations | 3: `DC_TARGET_STOP`, `DC_TRAIL_HOLD`, `DC_TARGET_STOP_HOLD` | `contracts.build_management_lattice`, `runner._device_combination_schedule` | `test_adaptive_management_contracts.py` | smoke device labels `TARGET+STOP`, `TRAIL+HOLD`, `TARGET+STOP+HOLD` |
| 10 | No other combinations | none observed | `contracts.build_management_lattice` | `test_adaptive_management_contracts.py` | smoke `arm_class` set is exactly the declared five classes |
| 11 | No native × management cross | 0 crossed rows | `policies.materialise_policy` raises; `integrity._check_no_cross` | `test_adaptive_management_integrity.py::test_each_hard_integrity_failure_is_named[no_native_management_cross-cross]` | `native_arm_id` non-null in `policy_schedule.parquet`: 0; hard check `no_native_management_cross` true |
| 12 | Size absent from exit combinations | SIZE appears in no device combination | `contracts.build_management_lattice` | `test_adaptive_management_contracts.py` | smoke device-combination labels contain no `SIZE` |
| 13 | E-TOUCH and E-CLOSE separate in 022/023 | `E_TOUCH` / `E_CLOSE` kept separate; 021 has one variant | `contracts.ENTRY_VARIANTS`, `entries.breach_origins` | `test_adaptive_management_strategy.py::test_touch_and_close_variants_do_not_block_each_other` | dry runs: 021 = 64 adaptive (one variant), 022/023 = 128 (two variants) |
| 14 | crypto and cTrader separate | separate catalog, manifest, symbols | `runner.universe_config` | `test_adaptive_management_runner.py::test_universe_configs_never_cross_catalogs_or_manifests` | six dry runs: no crypto plan mentions cTrader and no cTrader plan mentions Bybit |
| 15 | No verdict / value labels | none | `integrity.run_integrity_checks` (hard checks only), `analysis` report layers | `test_adaptive_management_integrity.py::test_valid_run_passes_and_writes_complete_integrity_package` | no verdict/quality column in any smoke artifact; `effect_quality_is_blocking: false` |

## Defects found by the smokes and fixed

1. **Two-sided origins rejected.** One H1 bar can qualify on both the long and the short shape
   (documented in `entries.breakout_origins`), which the strategy refused as an overlap. The
   overlap key is now the origin, not the timestamp; the single-slot rule resolves the tie as
   `BLOCKED_ACTIVE`. (`strategy.py`; `test_two_sided_origins_on_one_bar_are_scheduled_and_resolved_by_the_slot_rule`)
2. **NaN treated as a present feature.** An unwarmed component or a median fitted on too few
   bars yields NaN, which passed the null check and reached the engine as a NaN price, aborting
   the run. NaN is now `NO_FEATURE`, parameters are nulled, and a NaN schedule is refused before
   the run. (`policies.py`, `native_parameters.py`, `strategy.py`;
   `test_nan_component_is_no_feature_not_an_eligible_nan_parameter`,
   `test_nan_distance_in_a_schedule_is_rejected_before_the_run`)
3. **Bar volume sliced entries.** Bar volume is a venue tick count, not tradable size, and the
   simulated exchange capped fills by it, splitting one entry into several fills and re-arming
   the hold timer. A fill-capacity floor is applied and repeat entry fills are handled without
   re-recording the episode. (`engine.py`, `strategy.py`;
   `test_thin_bar_volume_does_not_slice_one_entry_into_several_episodes`)
4. **Actionable times without a traded minute.** H1 labels fall on minutes the venue never
   traded (session close, weekend), stranding 5 510 schedule rows. Rows now act on the first
   minute at or after their time, never before; rows after the final bar are recorded as
   `CENSORED`; anything left at or before the final bar is still a hard failure. (`strategy.py`;
   `test_actionable_time_without_a_traded_minute_acts_on_the_next_bar`)
5. **Ledger and report typing.** The state ledger mistyped columns whose first values are null,
   and stringified timestamps made the emission unparseable by the adjudication shim.
   (`engine.py`; covered by the real-catalog smoke reaching a passing estimand gate)
6. **Golden-trace key too narrow.** One episode carries one CLOSED row per management arm by
   design; the check keyed on the episode alone and failed every real run. The key is now
   episode + policy + arm. (`integrity.py`;
   `test_two_arms_closing_one_episode_is_not_a_golden_trace_failure`)

## Open observation for the operator (not fixed)

A protective exit whose trigger is already through the market at submission is rejected by the
venue and recorded as `EXIT_REJECTED`: 35 of 4 502 closed legs (0.8%) in the bounded smoke. The
episode keeps its other legs and the state is explicit, never silent, but those legs ran without
that protective exit. Treating a through-market stop as an immediate exit instead would be a
design change, so it is left as declared behaviour for the analysis to account for.

## 2026-08-03 amended acceptance checklist

The first pass exposed lifecycle and reporting-population defects, so the observation above is
superseded by the dated common amendment. Prose alone does not accept any amended clause. Tasks 2–4
must fill the evidence cells below before first-pass deletion or production execution.

| Amended clause | Intended code | Focused test | Smoke evidence | Accepted |
|---|---|---|---|:---:|
| Entry-fill identity: actual `_entry_ns` on both adaptive and fixed sides | `analysis.py` shared-fill assembly | `test_shared_fill_uses_actual_breakout_fills_not_planned_entry_time`, breach non-fill and duplicate-identity tests | v9 common-fill rows: 966 / 6,407 / 6,394; every row had both actual fills | [x] |
| SIZE inherits strategy-fixed close: 1 H1 bar in SPDR-021, 4 H1 bars in SPDR-022/023 | `policies.py`, `strategy.py` | `test_size_inherits_the_strategy_fixed_horizon`; amended five-case synthetic trace | v9 SIZE filled/closed: 319/319, 3,388/3,388, 3,388/3,388 | [x] |
| Pure TARGET/STOP/TRAIL remain price-only; adaptive HOLD keeps its own duration | `policies.py`, `strategy.py` | `test_only_time_based_devices_materialise_a_horizon`; declared-combination hold tests | v9 device census showed multiple fills and explicit price-only fence censoring | [x] |
| Exit submission waits for a visible position and uses the intended `position_id` | `strategy.py` lifecycle state | `test_protective_exits_wait_until_the_filled_position_is_visible`; confirmed-position-ID test | v9 repeated breach episodes passed lifecycle integrity | [x] |
| Rejected/denied protective exit gets exactly one reduce-only market fail-safe | `strategy.py` failure path | denied-leg, successful-fail-safe and denied-fail-safe tests | v9 had one exit failure and zero absorbing failures; later synthetic episode executed | [x] |
| Filled/closed lifecycle completeness is hard integrity; pure price-only fence censoring remains explicit | `integrity.py` | missing SIZE close, explicit price-only fence and fail-safe-close tests | all three v9 `blocking_pass=true` | [x] |
| Populations named separately: eligible origins, entry fills, closes, common fills, common closes | `analysis.py`, `integrity.py` | scheduled-nonfill and ineligible-device-population tests | v9 row accounting passed in all three cells | [x] |
| Per-origin uncertainty uses origin blocks; per-trade uncertainty uses actual common fill/close blocks | `analysis.py` bootstrap routes | exact block-kernel reference and scheduled-nonfill count tests | 21-day clean/resume/two-scratch canonical hash `7834a5cd…5c71` | [x] |
| Time derangement and magnitude matching carry outcome estimates per declared stratum | `analysis.py` control tables | zero-fixed-point and named-strata integrity tests | v9 computed control rows: 320 / 640 / 640; none deferred | [x] |
| Research grid remains unchanged | `contracts.py`, experiment wrappers | `test_real_scheduler_materialises_complete_native_grid` | v9 full row accounting passed for 371 / 839 / 839 origins | [x] |
