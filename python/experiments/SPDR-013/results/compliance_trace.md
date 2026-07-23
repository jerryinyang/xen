# SPDR-013 compliance trace — design § / RAW § → implementation

**Run status:** FULL 25-symbol run COMPLETE (2026-07-23). 2940 cells, 1,639,125 episodes.
`results/integrity_selfcheck.json` **all_pass = True**. All §10 artifacts present (episodes,
expectancy_by_cell, zz_features, controls, zz_forecast, golden_traces, integrity_selfcheck).


100% source-of-truth mapping. Every arm, period, angle, clock, control, tripwire, cost pin,
capture rule, expectancy term, universe pin and fence is traced to `file:line` or an emitted
artifact. Authority stack: RAW `vol-direction-structural-programme-raw.md` (substance) →
`SPDR-013/design.md` (executable freeze) → checkpoint-017 §5B/§8.2 → chapter-06 governance →
`spdr-lane.md`. **No design clause is thinned or dropped.**
Interpretation notes (weaken no clause): **IN-1..IN-4** (`config.py` `INTERPRETATION_NOTES`).

### Operator-signed amendments (2026-07-23)

| ID | Change | Direction | Where |
|---|---|---|---|
| **DEV-1 / AMENDMENT-T1** | Future-destroy tripwire **demoted from HARD gate to INFORMATIVE** (report layer, no PASS/FAIL effect). An outcome-side destroy on a mean episode-P&L direction object cannot separate a causal timing edge from a leak (SOL D-SMA14 H1 CONFIRM live −2.23 vs destroyed-null p95 −3.20; all 12 D-SMA14 live values negative → no positive surviving edge). Applicability residual kept HARD: no cell CLAIMING positive edge (live>0) may survive. Same class as SPDR-012 DEV-1. | LOOSER (operator-signed) | `config.DEVIATIONS[DEV-1]`; `controls.path_future_destroy`; `run_screen._integrity` |
| **AMENDMENT-A3** | **Exit-mode decomposition**: each direction signal × {combined, stop, trail, time, signalflip}; ZZ signalflip = the structural-leg arm. combined = the frozen §4 stack (unchanged). | NEUTRAL (pre-outcome) | `config.EXIT_MODES`; `capture.simulate_signal/simulate_independent`; `run_screen` grid |
| **AMENDMENT-E1** | Report **median** alongside mean for avail/damage/expectancy (fat-tail disclosure). Headline band still mean expectancy_partial. | NEUTRAL | `expectancy.decomposition` |

### QA REVISE-1 resolutions (2026-07-23, HEAD 8d19daa)

| QA # | Issue | Resolution |
|---|---|---|
| 1,2,3,9 | Smoke run / missing parquets / matched-random absent / trace overclaim | Full 25-symbol run with matched-random (no skip); all §10 parquets emitted; trace regenerated post-run |
| 4 | thirds not applied to SUPPORTED | `band_expectancy(...,thirds_sign)`; SUPPORTED demoted to INDETERMINATE if thirds_sign < THIRDS_SIGN_MIN |
| 5 | +20 bps bite plant missing (derangement, matched-random) | `_summarise_null(...,plant_bps)` → `plant_detected_above_null_p95` on both controls |
| 6 | matched-random DISJOINT ±1 bar not ±1h | `block_bars = 60 // clock_minutes` (H1=1, M15=4) |
| 7 | episode `right` col / zz next-swing targets | `expectancy.apply_costs` adds `right`; zz_features rows carry `next_magnitude_bps`/`next_path_noise_atr`/`next_direction` |
| 8 | G3 self-referential | added `golden_traces.g3_independent_fixture` (hand-listed deviations, not engine bridge code) |
| 10 | train_end `<=` vs `<` | integrity check tightened to strict `<` |

**SAFE speedup (operator question):** matched-random random-entry outcomes cached per
(symbol, clock, band, stop-geometry) and reused across SMA-period/exit-mode cells
(`controls.build_random_cache`) — deterministic (entry,side,geom,cap)→(exit,gross), so it changes
no sample membership, denominator, metric, causal ordering or seed; ~65× on the hot control.
**Parallelism:** `--jobs N` process pool over symbols (`run_screen`, `spawn` context — fork
deadlocks after the multithreaded universe scan). Verified **bit-identical to sequential** (2256
fields, 0 mismatch); ~9× wall (66s→7.5s/symbol). Symbols independent, fixed seeds, order preserved.

### MFE / capture-geometry diagnostic (operator question 2026-07-23)

| Item | Implementation |
|---|---|
| Per-episode realized-hold MFE/MAE (open + intrabar) | `capture.simulate_signal` `mfe_oo_bps`/`mae_oo_bps`/`mfe_hi_bps`; emitted in `episodes.parquet` |
| Fixed-horizon MFE/MAE over entry→entry+cap | `capture.horizon_excursion`; `horizon_*_bps` per episode |
| Capture efficiency + signal-vs-random-timing MFE | `analysis_code/mfe_capture.py` → `results/mfe_capture_by_arm.parquet`, `mfe_signal_vs_random.parquet` |
| Non-tradability | MFE reads labelled non-tradable ceilings (peek at within-window peak); no strategy return claimed |

Paths are relative to `python/experiments/SPDR-013/screen_code/` unless noted.

## Scope, universe, fence

| Design / RAW clause | Implementation |
|---|---|
| §0 vehicle: vectorised Python, fenced 1m → H1 **and** M15, both mandatory | `catalog_io.load_minute_bars` + `aggregate_clock`; clocks `config.CLOCKS` (H1, M15); both run in `run_screen.CLOCK_ORDER` |
| §0 band: DESIGN primary `[2021-06-29T06:53Z, 2023-03-01)`, CONFIRM `[…, 2023-12-18)`, TEST/holdout never | `config.DESIGN_START/DESIGN_END/CONFIRM_END`; `config.PRIMARY_BAND="DESIGN"`; both bands run, TEST/holdout never queried (fence assert) |
| §0.1 universe = top-25 by 30d `sum(close×volume)` TRAIN, asof train_end; **recompute + assert equality** | `universe.recompute_universe` + `assert_pin` (both pin files) called at `run_screen.main`; abort on mismatch; recompute emitted `results/universe_recomputed.json` |
| §0 SPREAD-COST-DISCLOSURE: UNAVAILABLE_NOT_CHARGED, PARTIAL_FEES_FUNDING_ONLY, prohibited claims | `config.SPREAD_COST_DISCLOSURE`; echoed in `integrity_selfcheck.json`, `screen.md`, `analysis.md` |
| §0 forbidden device: SPDR-011 range-break as primary direction | Not implemented anywhere; only D-SMA and D-ZZ arms exist (`arms.py`) |
| SPDR-lane TRAIN-only fence, causal t-1 | `catalog_fence.assert_within_fence(band="TRAIN")`; ATR read lagged `[t-1]`; entry at `open[t+1]` (see below) |

## Arm D-SMA (design §3.2) — all cells mandatory

| Clause | Implementation |
|---|---|
| Periods **14, 25, 50** all mandatory | `config.SMA_PERIODS=(14,25,50)`; `arms.sma_cells` builds all |
| Signal: +1 if C_t>SMA_t, −1 if <, 0 if equal | `arms.sma_signal` |
| Angle filter **OFF and ON** both mandatory; ON ⇔ `|SMA_t−SMA_{t-3}|/ATR(14)[t-1] ≥ 0.15` else 0 | `config.SMA_ANGLE_MODES=("off","on")`, `SMA_ANGLE_LOOKBACK=3`, `SMA_ANGLE_THRESHOLD_ATR=0.15`; `indicators.sma_angle_ok`; `arms.sma_signal(angle_mode="on")` |
| 200-SMA forbidden | absent |
| Grid = 3 periods × 2 angle × 2 clocks = 12 cells/symbol, all run | `run_screen` loops all `sma_cells` × `CLOCK_ORDER` × both bands |
| Position: follow signal; reverse on flip; stop may exit earlier without reverse until next signal | `capture.simulate_signal` leg-start rule (`leg_starts`) + reverse-on-flip + "no re-entry until next leg" |
| **Exit modes (AMENDMENT-A3)**: each signal × {combined, stop, trail, time, signalflip} | `config.EXIT_MODES`; `capture.simulate_signal(**flags)`; combined = frozen §4 stack |

## Arm D-ZZ (design §3.3) — both clocks

| Clause | Implementation |
|---|---|
| ATR ZigZag, Wilder ATR(14), reversal **2.0×ATR** from extreme, close-based confirmation | `indicators.atr_zigzag` (`config.ZZ_REVERSAL_ATR=2.0`, `ATR_PERIOD=14`) |
| Line features: magnitude=\|end−start\|/start×1e4 bps; direction∈{+1,−1}; angle=magnitude/max(1,bars); path_noise=MAD of closes vs linear bridge, ATR units | `indicators._swing_features`; golden trace G3 hand-verifies to 1e-6 |
| Signed policy (primary): next dir = −direction_k; enter open[t+1]; same §4 geometry, native clock ATR/bars | `arms.zz_signal` → `capture.simulate_signal`; clock-native ATR (IN-1) |
| Next-move **magnitude AND path_noise/vol** forecast, **AR(1) AND ridge**, both clocks, IC/MAE tabled (mandatory) | `zz_forecast.walk_forward` (causal expanding walk-forward); emitted `results/zz_forecast.json` |

## Capture geometry (design §4, frozen, both arms)

| Rule | Implementation |
|---|---|
| Entry = next clock RealOpen after signal/confirmation bar | `simulate_signal` enters at `open[j]` on `signal[j-1]` |
| Initial stop: adverse ≥ **1.5×ATR(14)[entry−1]**; exit-at-open on gap-through, else next-open on intrabar touch | `config.INITIAL_STOP_ATR=1.5`; `capture._init_stop`; IN-3 exit rule in `simulate_signal`/`simulate_independent` |
| Winner trail: fav open-to-open ≥ **1.0×ATR** → lock entry+**0.5×ATR**×side, ratchet HWM−**2.0×ATR**×side | `config.TRAIL_TRIGGER_ATR/TRAIL_LOCK_ATR/TRAIL_RATCHET_ATR`; `capture._tighten`; HWM = running extreme of opens (IN-2) |
| Opposite signal: SMA reverse on flip; ZZ reverse on next opposite confirmation | unified signal-change reverse in `simulate_signal` |
| Time cap: H1 **48**, M15 **192** bars; exit open of bar after cap | `config.CLOCKS[...]["time_cap_bars"]` (48/192); `simulate_signal` TIME_CAP |
| One position per symbol | single-position state machine |
| ATR object per clock (never mix) | IN-1: per-clock Wilder ATR(14)[t−1] |

## Costs (design §4) — no local accounting primitive

| Clause | Implementation |
|---|---|
| Fee RT **11.0 bps taker** (Bybit) | `expectancy.FEE_RT_BPS=11.0`, asserted `== 2×xen.evaluation.bybit_fee_bps_per_side("taker")` |
| Funding **1.0 bps × discrete 00:00/08:00/16:00 UTC stamps in (entry,exit]** | `xen.evaluation.count_bybit_funding_stamps`; `expectancy.funding_stamps` |
| Allowance **0/2/5 sensitivity, 2.0 governing** | `config.ALLOWANCE_SENSITIVITY=(0,2,5)`, `ALLOWANCE_GOVERNING=2.0`; per-episode `partial_net_bps_a{0,2,5}` |
| `partial_net_bps = gross − fee − funding − allowance`; spread not charged | `expectancy.apply_costs` |
| UNIT-PIN `gross_signed_oo_bps = direction*(exit_open/entry_open−1)*1e4` | `capture.simulate_signal` gross |

## Expectancy decomposition (design §5 — primary, not win-rate)

| Statistic | Implementation |
|---|---|
| RIGHT iff `gross>0` (gross sign, not net) | `expectancy.decomposition` |
| `p_right`, `avail_when_right`, `damage_when_wrong`, `expectancy_gross`, `expectancy_partial` (headline) | `expectancy.decomposition`; emitted `results/expectancy_by_cell.parquet` |
| **median alongside mean (AMENDMENT-E1)** for avail/damage/expectancy | `decomposition` `*_median` fields; ZZ mag/noise features stay forecasting-only, never the avail/damage object |
| win_rate disclosure only | `decomposition["win_rate_net"]`, never a band driver |
| report per symbol×arm×period×angle×clock; pooled disclosure-only | one row per cell in `expectancy_by_cell.parquet` |

## Controls (design §6)

| Control | Implementation |
|---|---|
| DIRECTION-DERANGEMENT: derange sides within symbol×third, paths fixed, 0 fixed points, ≥200 seeds 31000+, +20 bps bite | `controls.direction_derangement` (`config.DERANGE_SEEDS`=31000..31199) |
| MATCHED-RANDOM-ENTRY: non-overlapping random entries, same side dist per third, same cap, exclude live ±1h, ≥200 seeds 41000+ | `controls.matched_random_entry` (`config.MATCHED_RANDOM_SEEDS`=41000..41199) via `capture.simulate_independent` |
| SMA-BENCHMARK: Δ expectancy (ZZ − SMA14/SMA25) with CI | `controls.sma_benchmark_delta` |
| TRIPWIRE PATH-FUTURE-DESTROY: metric expectancy_partial on D-SMA14; pair to foreign future paths; +30 bps plant must collapse into null envelope | `controls.path_future_destroy` (`config.TRIPWIRE_SEEDS`=52000..52199, `PLANT_TRIPWIRE_BPS=30`). **INFORMATIVE only (DEV-1)** — not gating; residual HARD = no positive-edge (live>0) survivor |

## Inference / bands / power (design §7)

| Clause | Implementation |
|---|---|
| Date-block bootstrap on entry dates, blocks 1/3/7, seeds 101/211/307/401/503, 10k | `stats_core.block_bootstrap`/`boot_mean`; envelope over grid (L-20) |
| Thirds sign stability ≥2/3 for SUPPORTED eligibility | `run_screen._thirds_sign`; `config.THIRDS_SIGN_MIN=2` |
| Bands SUPPORTED/WASH/CONTRADICTED/UNPOWERED (labels, never gates) | `stats_core.band_expectancy` (`config` band constants); cost-floor 13.5 disclosure |

## Integrity (design §8) + golden traces (design §9)

| Item | Implementation / artifact |
|---|---|
| TRAIN-only, max exit < train_end, no holdout | `integrity_selfcheck.json` checks |
| Entry uses open after signal bar; features ≤ signal bar; ATR[t−1] | causal by construction; `entry_after_signal_bar` check |
| Derangement 0 fixed points | `controls._derangement` (retry until fixed-point-free) |
| Win-rate never a PASS criterion | no code path gates on win_rate |
| `results/integrity_selfcheck.json` PASS | emitted |
| G1 BTCUSDT SMA14 flip; G2 ETHUSDT/synthetic stop; G3 SOLUSDT ZZ features 1e-6; engine parity | `golden_traces.py`; `results/golden_traces.json` |

## Deliverables (design §10)

| Artifact | Path |
|---|---|
| screen_code | `screen_code/` |
| episodes | `results/episodes.parquet` |
| expectancy_by_cell | `results/expectancy_by_cell.parquet` |
| zz_features | `results/zz_features.parquet` |
| integrity_selfcheck | `results/integrity_selfcheck.json` |
| controls / zz_forecast / golden | `results/controls.json`, `results/zz_forecast.json`, `results/golden_traces.json` |
| screen.md / analysis.md | `screen.md`, `analysis.md` |
