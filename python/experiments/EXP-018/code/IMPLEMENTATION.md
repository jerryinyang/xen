# EXP-018 implementation notes (developer, 2026-07-04)

C# refs + conf notes only (no Python analysis here — INFR-001). Strategy runs in
`Mode=NativeOrders` reusing the EXP-014b/c CIS machinery; **no new model class** — new axes on
the existing `cross_instrument_spread_mr` native path.

## DEVIATIONS

None unraised. Four design ambiguities were elicited BEFORE coding and resolved by the
operator — recorded as design.md **Amendment A1** (matched-hold destroy exits; both-leg arm A
= joint form-1 + group time-stop; both-leg reentry=none; NZDUSD extend; 5 live cells).

## Files changed / added

| File | Change |
|---|---|
| `Xen.cs` | `CisExitSet=harvest` (arm A: moving form-2 TP refresh + per-leg ⌈3·HL_entry⌉ cap-48 time-stop, NO SL, NO form-1); `CisEntryDelayBars` (decision-state delay tripwire); `CisSchedulePath` (random-timing arm: CSV schedule, market entries, matched-hold market exits, no TP/SL/form-1); decision state split `_decisionBracket/_decisionLogClose` (== live state at delay 0); run_metadata params (`entry_delay_bars`, `schedule_path`, `schedule_mode`, harvest/schedule `exit_set` strings) |
| `Xen.BothLeg.cs` | `BothLegGroup.HorizonBars` (harvest ⌈3·HL_entry⌉ cap 48 / scheduled matched hold); group time-stop → `CloseBothLegGroup("time_stop"/"matched_hold")`; decision-state used for form-1 test + entries + provenance; `TryOpenScheduledGroup` (schedule both-leg arm) |
| `tools/ctrader-cli/experiments/EXP-018-4h-*.conf` (14) | 5 live + 5 `-rt` + 5 `-delay1` runs + 3 `-shift` runs (see census below) |
| `tools/ctrader-cli/experiments/EXP-018-smoke.conf` | truncated US2000 harvest cell — emission-contract check only |
| `tools/ctrader-cli/experiments/gen_exp018_schedules.py` | seeded (20260704) schedule generator: live episodes as rigid templates placed at random non-warmup TRAIN bars; run AFTER live cells, BEFORE `-rt` |

## Design-clause → code map (QA trace input)

| Design clause | Code location |
|---|---|
| §4 ladder z∈{1.5,2.0,2.5}, one unit/level | `Xen.cs` `_ladderZStars = {z0, z0+.5, z0+1}` with `--CisZStar=1.5` (existing HYP-003 path) |
| §4 R-refresh per bar; extend/allow | existing `RearmBracket` (`_staticArm=false` default; `CisReentry`) |
| §4 arm A: moving TP, no SL, time-stop ⌈3·HL⌉ cap 48, no form-1 | `Xen.cs` exit-set `harvest`: TP init in `OnNativePositionOpened` (`!_frozenExit` branch, `b.ExitPrice`), refresh in `RefreshForm2Targets`; `leg.HorizonBars` set in same branch; `ApplyFrozenTimeStop` gated `(_frozenTimeStop \|\| _harvestExit)`; form-1 gated `!_frozenExit && !_harvestExit` |
| §4 arm B: frozen TP + outward SL 1·D + time-stop | existing `bracket` exit set (HYP-004 E3), unchanged |
| §4 US500 both-leg market, arm A (A1 §2/§3) | `Xen.BothLeg.cs`: joint form-1 (existing) + group `HorizonBars` time-stop (`NewGroup` harvest branch + `ProcessBothLegBar` time-stop block); `--CisBothLeg=true --CisBothLegEntry=market --CisReentry=none` |
| §4 TRAIN fence | conf `ANALYSIS_END`: US2000 2024-09-10T09:33Z; NZDUSD 2024-09-06T05:42Z; US500 2024-09-17T17:26Z (EXP-013/016 49% TRAIN cutoffs); `HoldoutFence` enforces |
| §5 random-timing destroy (A1 §1) | `CisSchedulePath` + `LoadSchedule`/`FireScheduledEntries`/`ApplyMatchedHoldExits` (`Xen.cs`); both-leg `TryOpenScheduledGroup`; generator `gen_exp018_schedules.py` |
| §5 entry-delay +1 tripwire | `CisEntryDelayBars=1`: `_delayQueue` → `_decisionBracket/_decisionLogClose` consumed by `RearmBracket`, `ApplyEventExits`, `RefreshForm2Targets`, `OnNativePositionOpened` provenance, both-leg entry/exit tests |
| §5 phase-shift 60h (disclosure-only) | existing `BasketPhaseShiftHours=60` → `CrossInstrumentBasketFeed` index shift; `-shift` confs |
| §5 NZDUSD negative control | `EXP-018-4h-A-extend.conf` second symbol (A1 §4) |
| §3 emission contract | existing `SignalPositionRecord` (incl. `OpenLegs`, provenance) + `CisTradeRecord` (`RealizedBps`, `Censored`, `LadderLevel`, `LegSymbol`, `EntryZ/EntrySigma/EntryTrendZ/EntryVolRegime`); `run_metadata.json` `analysis_end_utc` |
| §3 no local accounting | no Python analysis code in this dir; estimands via `xen.adjudication` (analyst stage) |
| §9 golden trace | NOT generated here (QA computes from design §9 + emitted provenance columns) |

## Run census (18 engine runs)

| Conf | Cells | Arm |
|---|---|---|
| `EXP-018-4h-A-extend` | US2000 + NZDUSD(neg-ctl) | live A/extend |
| `EXP-018-4h-A-allow` | US2000 | live A/allow |
| `EXP-018-4h-B-extend` | US2000 | live B/extend |
| `EXP-018-4h-blmkt-A` | US500 | live both-leg A |
| `…-delay1` ×4 confs | same 5 cells | entry-delay +1 tripwire |
| `…-rt` ×4 confs | same 5 cells | random-timing destroy (schedules required first) |
| `EXP-018-4h-A-extend-shift`, `EXP-018-4h-B-extend-shift` | US2000×2 + NZDUSD | phase-shift 60h disclosure |

## Run order

1. `./run-experiment.sh EXP-018-4h-A-extend all` (+ the other 3 live confs)
2. `python3 experiments/gen_exp018_schedules.py` (writes `experiments/schedules/EXP-018/*.csv`)
3. the 4 `-rt` confs, the 4 `-delay1` confs, the 2 `-shift` confs
4. estimand gate per cell: `python -m xen.estimand_validation data/strategy_runs/<conf-stem> --expect <symbols> --out python/experiments/EXP-018/results/estimand_validation.json`

## Smoke result

See completion summary / `data/strategy_runs/EXP-018-smoke/` (truncated 2021 US2000 harvest
cell; estimand validation run on it pre-hand-off).
