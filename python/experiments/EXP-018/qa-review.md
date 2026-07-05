# EXP-018 — QA / compliance review (append-only)

## QA run 1 — 2026-07-04T19:27:20Z — mode: subagent — HEAD a2bce28
Reviewed state: HEAD `a2bce2822bded0b064cf5b2a7e6714051708a145` + dirty working tree
(implementation is uncommitted: `Xen.cs`, `Xen.BothLeg.cs` modified; `python/experiments/EXP-018/`,
`tools/ctrader-cli/experiments/EXP-018-*.conf`, `gen_exp018_schedules.py`,
`python/src/xen/evaluation.py` untracked). Fresh context confirmed: this session contains no
implementation work. Build check: `dotnet build` — 0 warnings, 0 errors.

**Verdict: APPROVE** — ready for the operator's execution gate. One registry-hygiene item
(Issue 1) flagged for the operator; no design-to-code drift found; all hard gates traceable.

### Design-fidelity trace

Expected behaviour was derived from design.md (incl. Amendment A1) first, then checked
against code. Line numbers refer to the dirty working-tree files.

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §4 trigger: S8 basket-relative anchor, frozen EXP-014b construction (w_z=200, w_a=200, median_w=90, per-instrument mates) | `Xen.cs:792` planner (unchanged), `Xen.cs:1526-1596` feed (unchanged); confs pass `--CisSeries=S8_RVINDEX` + mates | MATCHES | Mates byte-identical to EXP-014b confs: US2000→USTEC;US500;JP225, US500→USTEC;US2000;JP225, NZDUSD→EURUSD;GBPUSD;USDJPY;USDCHF;USDCAD;AUDUSD |
| §4 ladder z∈{1.5,2.0,2.5}, one unit/level, R-refresh, extend/allow | `Xen.cs:820-821` (`_ladderZStars={z0,z0+.5,z0+1}` with CisZStar=1.5), `Xen.cs:1044-1084` `RearmBracket` (unchanged levels/one-per-level logic) | MATCHES | Smoke: max one leg per level per episode confirmed by LadderLevel census (142/116/53) |
| §4 arm A "harvest": per-leg TP at current (moving) anchor mean | `Xen.cs:799-804` exit-set parse incl. `harvest`; initial TP `Xen.cs:1154-1166` (`!_frozenExit` branch, `b.ExitPrice`); per-bar refresh `Xen.cs:943-945` → `RefreshForm2Targets` 1387-1406 | MATCHES | Smoke GT2: RefreshedTp tracks Anchor to ≤0.024 bps (price rounding), changes on 783/784 bars — the TP MOVES. Favorable-assert retained (inherited E0 semantics, disclosed in run_metadata `favorable_asserted`) — see Issue 5 |
| §4 arm A: NO stop-loss | harvest never enters the `_frozenSl` branch (`Xen.cs:805-807`: `_frozenExit=false` for harvest) | MATCHES | Smoke: 0 legs with finite SlPrice; ExitReason census has no `sl_outward` |
| §4 arm A: NO form-1 (L-14 exit-set diff) | form-1 gate `Xen.cs:927`: `!_frozenExit && !_harvestExit && !_scheduleMode` | MATCHES | Smoke ExitReason census: form2_favorable_limit 248 / time_stop 61 / open_at_end 2 — **no form1_reversion row exists**. Exit set is exactly {moving TP, time-stop} as §4 names |
| §4 arm A: time-stop ⌈3·HL_entry⌉ cap 48 per leg | `Xen.cs:1167-1172` (HorizonBars at fill from decision-state Hl), `Xen.cs:931-934` gate `(_frozenTimeStop \|\| _harvestExit)`, `ApplyFrozenTimeStop` 1309-1317 | MATCHES | Smoke GT3: 61/61 time_stop legs have HorizonBars == min(48,⌈3·Hl_entry⌉) with Hl re-derived by QA from the positions row at the entry decision bar, and BarsHeld == HorizonBars; 0 legs overran their horizon |
| §4 arm B "braked": frozen TP at entry-time anchor + outward SL 1·D + time-stop | pre-existing `bracket` exit set `Xen.cs:1176-1200` — git diff shows this branch unchanged except decision-state aliasing (identity at delay 0) | MATCHES | No arm-B smoke; verified by code trace + the branch being the EXP-016-validated path (Issue 6) |
| §4/A1-2 US500 both-leg arm A = joint form-1 + group time-stop, market entry | `Xen.BothLeg.cs:141-151` joint form-1 (existing), `Xen.BothLeg.cs:153-157` group time-stop, `NewGroup` harvest HorizonBars `Xen.BothLeg.cs:516-520`; conf `--CisBothLeg=true --CisBothLegEntry=market --CisExitSet=harvest` | MATCHES | `CloseBothLegGroup("time_stop")` closes ALL legs at next open; harvest+bothLeg permitted (`Xen.cs:808` throw is `_frozenExit`-only, harvest is not frozen). No per-leg price TPs anywhere in the both-leg path |
| A1-3 US500 both-leg reentry = none | conf `--CisReentry=none`; `Xen.cs:618` forces none in metadata; group singleton `_group` (≤1 open) | MATCHES | Faithful to the VAL-006 residue object |
| A1-4 NZDUSD negative control = arm A / extend / z-ladder | `EXP-018-4h-A-extend.conf` second symbol with identical harvest/extend/z15 args | MATCHES | Mirrors the US2000 primary as A1 requires |
| §5/A1-1 random-timing destroy: seeded schedule, market entries, matched-hold market exits, NO TP/SL/form-1 (L-08) | `Xen.cs:812-819` (`CisSchedulePath` → `_scheduleMode`), `LoadSchedule` 1351-1383 (validates dir ±1, hold ≥1, time-sorted), `FireScheduledEntries` 1335-1346, `ApplyMatchedHoldExits` 1322-1330, open-path `Xen.cs:1147-1153` (schedule legs get HorizonBars=hold, no TP modify — `if/else if` structure means the exit set is fully overridden); both-leg `TryOpenScheduledGroup` `Xen.BothLeg.cs:527-560` | MATCHES | RearmBracket never called in schedule mode (`Xen.cs:951-956`); form-1/TP-refresh/time-stop all gated `!_scheduleMode`. B-extend-rt (exit set `bracket` + schedule): schedule branch wins at the fill — no frozen TP/SL attached. run_metadata reports `random_timing_matched_hold_market_exit_only` |
| §5/A1-1 schedule generator: live episodes as rigid templates at seeded random non-warmup TRAIN bars, seed 20260704 | `gen_exp018_schedules.py:27` SEED=20260704; templates preserve per-level counts, relative offsets, dirs, realized holds (`leg_templates`); placement over `~Warmup` grid; both-leg episodes collision-free, single-leg may overlap (matches live concurrency) | MATCHES | Reads only EntryTime/LadderLevel/Direction/BarsHeld/Censored/ExitTime — no P&L columns (no local accounting). Two informative notes: Issue 4 |
| §5 entry-delay +1 tripwire: all decisions delayed one bar | `Xen.cs:157-158` param; `Xen.cs:887-907` decision-state queue; consumers: `RearmBracket` (1046), `ApplyEventExits` (929/1293), `RefreshForm2Targets` (1389), leg provenance (1127), both-leg form-1/entries/NewGroup (`Xen.BothLeg.cs:144,176-178,186,223-226,504`) | MATCHES | Delay applies to the FULL decision state (arming + exits + TP refresh + provenance) per the A1 developer note recorded in design.md; conditioners stay t-1 (not decision inputs), also as recorded. Schedule+delay combination rejected (`Xen.cs:816-818`) |
| §5 delay=0 ⇒ decision state == live state (regression identity) | `Xen.cs:888-892`: direct assignment, queue untouched | MATCHES | See shared-code boundary section |
| §5 phase-shift 60h, disclosure-only, extend cells | existing `BasketPhaseShiftHours` → `CrossInstrumentBasketFeed` index shift (`Xen.cs:1583`); `-shift` confs pass 60; 3 shift runs (US2000 A + NZDUSD A + US2000 B) | MATCHES | Conf headers state ATTRIBUTION DISCLOSURE ONLY, non-binding (B-3/L-15) |
| §3 emission contract: positions (OpenLegs, provenance), cis_trades (RealizedBps, Censored, LadderLevel, LegSymbol, EntryZ/EntrySigma/EntryTrendZ/EntryVolRegime), run_metadata analysis_end_utc | verified in the smoke emission's actual parquet schemas + run_metadata | MATCHES | All named columns present; `analysis_end_utc` present; new provenance params `entry_delay_bars`/`schedule_path`/`schedule_mode` and harvest/schedule `exit_set` strings emitted (`Xen.cs:590-613`) |
| §3 estimand gate hard block on smoke | `python/experiments/EXP-018/results/estimand_validation_smoke.json` | MATCHES | `blocking_pass: true`; reconciliation abs diff 7.3e-12 bps; fence ok (last bar 2021-12-30 22:00 < 2021-12-31); schema ok; one physicality sanity flag disclosed (non-blocking, truncated smoke window) |
| §4 TRAIN fence per instrument | confs: US2000 2024-09-10T09:33Z, NZDUSD 2024-09-06T05:42Z, US500 2024-09-17T17:26Z; BACKTEST_END matches each | MATCHES | Independently verified against `EXP-016/code/adjudicate.py` TRAIN_FENCE (US2000/NZDUSD) and EXP-013 confs (US500). Note the EXP-016 *conf* ANALYSIS_END values are the TEST fences — EXP-018 correctly uses the 49% TRAIN fences, so TEST band is never emitted |
| §4 complexity budget: 5 live cells (A1), 18 runs ≤ 21 | 14 confs = 4 live confs (5 cells: A-extend carries US2000+NZDUSD) + 4 `-rt` (5 cells) + 4 `-delay1` (5 cells) + 2 `-shift` (3 cells) + smoke | MATCHES | 5+5+5+3 = 18 engine runs; A1 records §4's "7" as an operator-corrected typo |
| §4 schedule CSV paths | confs reference `/workspace/tools/ctrader-cli/experiments/schedules/EXP-018/<stem>_<SYMBOL>.csv`; generator writes `SCRIPT_DIR/schedules/EXP-018/` | MATCHES | `run-experiment.sh:127` bind-mounts repo root at `/workspace` in the container — paths resolve. Engine throws if the CSV is missing (`LoadSchedule`), so running `-rt` before the generator fails loudly, not silently |

### Golden-trace diff (design §9 — expected values computed by QA from the design + emitted provenance; the developer generated none)

Evidence base: the EXP-018-smoke emission (US2000 harvest/extend/z15, 2021 window,
`data/strategy_runs/EXP-018-smoke/cross_instrument_spread_mr_us2000_4h_20260704_192455/`),
which covers the design's named golden bar.

**GT1 — bar 2021-01-04 18:00 (emitted row SourceCloseTime 2021-01-04 22:00).**
Emitted Anchor=1995.154112, Sigma=0.01423738. Hand-computed levels `Anchor·exp(∓zσ)`:
z=1.5 buy 1953.00/sell 2038.22; z=2.0 buy 1939.14/sell 2052.78; z=2.5 buy 1925.39/sell 2067.45.
Emitted ArmBuyPrice/ArmSellPrice = 1953.00/2038.22 — |diff| < 1e-6. **PASS.**
No fill in the following bar: correct — the bar's own low (1935.28) breached the buy level vs
the ≤t-1 close, so BreachSkipBuy=true and the buy side was not armed (the frozen EXP-014b
skip-don't-chase policy, part of the §4 "identical construction" trigger); 3 legs already open.
Population-level fill check across all 311 smoke legs: every fill is at or favorable to its
hand-computed level `EntryAnchorPrice·exp(−dir·z_lv·EntrySigma)` (0 worse-than-level fills;
3 favorable gap-throughs of 27–38 bps). **PASS.**
EntryZ: |EntryZ| medians 1.26/1.78/2.13 vs level z* 1.5/2.0/2.5 — approximately the level z but
systematically below it, because EntryZ is the ≤t-1 decision-close z (per §2 OBJECT-IDENTITY),
not the intra-bar touch z. Consistent with §2; §9's "≈" holds loosely. **PASS with note (Issue 3).**

**GT2 — arm A moving TP.** RefreshedTp emitted on 785 bars; |RefreshedTp − Anchor| ≤ 0.024 bps
(price-rounding only); the value changes on 783/784 consecutive-bar pairs — the TP re-rests at
the MOVING anchor mean each bar, exactly the §4/§9 arm-A semantics. **PASS.**
Arm B divergence (frozen TP at `exp(anchor_entry)` + SL at `entry±D`): no arm-B smoke emission;
verified by code trace — the `bracket` branch (`Xen.cs:1176-1200`) is unchanged from the
EXP-016-validated code except the delay-0-identity decision-state alias. **PASS by trace (Issue 6).**

**GT3 — time-stop arithmetic.** For all 61 time_stop legs: QA re-derived the entry decision
bar's Hl from positions.parquet and computed min(48, ⌈3·Hl⌉); emitted HorizonBars matches
61/61, and BarsHeld == HorizonBars 61/61 (exit at the next bar open after the horizon bar,
fill-bar-counts-as-bar-1 convention); 0 legs of any exit reason overran their horizon. **PASS.**

### Governance & boundary

- **Mandatory declaration blocks**: mechanism (§1), OBJECT-IDENTITY (§2), control validity
  proofs with non-vacuity + bite/MDE (§5), tripwire (§5 entry-delay, REJECT-class on
  discontinuity), bands (§7), power (§8), golden trace (§9), hard/informative split (§10) —
  all present. PASS.
- **`check_no_local_accounting("python/experiments/EXP-018/code")`**: run by QA →
  `{'ok': True, 'banned_defs_found': []}`. The experiment dir contains only design.md,
  code/IMPLEMENTATION.md, results/estimand_validation_smoke.json, and this review — **no
  Python analysis code, no Python strategy backtest anywhere**. The schedule generator lives
  in tools/ and reads no P&L columns. PASS.
- **Registry preconditions**: CF-MR-005 registered (2026-07-03, operator D2), currently OPEN;
  0 counted TEST reads planned (TRAIN only — §10); checkpoint-006 names EXP-018 as the
  operator-sanctioned disposition probe. PARTIAL — the family file carries no HYP-003/EXP-018
  hypothesis row yet (Issue 1).
- **Holdout / fence**: all confs fence at the per-instrument 49% TRAIN cutoff (verified against
  EXP-013/EXP-016 sources above); `HoldoutFence.ShouldStopBeforeProcessing` stops the engine
  before any bar at/after the fence and `FlushOpenLegsAsCensored` marks stragglers censored;
  smoke fence check passed. No code path touches TEST or the final-30% holdout. PASS.
- **DEVIATIONS**: IMPLEMENTATION.md declares "None unraised"; the four pre-coding ambiguities
  were operator-resolved and recorded as design.md Amendment A1 (evidence: the amendment text
  itself, dated, with resolutions) — the silent-deviation rule was followed. PASS.
- **Elicitation hygiene**: A1 questions and resolutions are plain-language. PASS.
- **Scope**: no features beyond design+A1 found in the diff — the Xen.cs/Xen.BothLeg.cs delta
  is exactly {harvest exit set, decision-state delay, schedule arm, metadata provenance,
  both-leg HorizonBars/time-stop/scheduled-group}. PASS.

**Shared-code boundary (regression safety for prior exit sets).** Verified from the git diff
of the dirty tree vs HEAD:
- Defaults: `CisExitSet="moving"`, `CisEntryDelayBars=0`, `CisSchedulePath=""` — all new axes
  off unless a conf sets them; no existing conf does.
- Delay 0: `_decisionBracket/_decisionLogClose` are assigned directly from the just-observed
  state (`Xen.cs:888-892`); the queue is never touched — every consumer that moved from
  `_lastBracket`/`logClose` to the decision state is bit-identical at delay 0.
- Gating deltas: `_frozenExit` is now `_exitSet != "moving" && !_harvestExit` (identical for
  the four legacy sets); form-1 gate adds `&& !_harvestExit && !_scheduleMode` (both false on
  legacy paths); time-stop gate `(_frozenTimeStop || _harvestExit) && !_scheduleMode`
  (reduces to `_frozenTimeStop` on legacy paths); form-2 refresh adds `!_scheduleMode`.
- Both-leg: new `HorizonBars` defaults to 0 (= no time exit) for the legacy moving arm
  (`NewGroup` sets it only under `_harvestExit`/schedule); form-1 logic itself unchanged.
- Build: 0 errors / 0 warnings.
PASS — a legacy conf replays the pre-EXP-018 behaviour exactly.

### Issues

1. **Low (governance, operator action, non-code).** CF-MR-005's Discipline clause
   (`docs/signal-registry/candidate-families/cf-mr-005.md:79-80`) requires "a registered
   hypothesis + EXP-ID here first" for every future screen, but the family file has no
   HYP-003/EXP-018 row (the design defers the *evidence* row to documentation, which is fine —
   the *registration* row is the gap). Required change: append a one-line HYP-003/EXP-018
   registration row to cf-mr-005.md at or before the operator execution gate (documenter or
   operator; no developer action). Does not block APPROVE: the operator-signed checkpoint-006
   already names EXP-018 as this family's sanctioned probe, so intent is on record.
2. **Informative (recorded for the retrospective, no action).** Family "first-branch"
   constraint 1 (basket-free trigger) does not bind EXP-018: the checkpoint-006 operator
   decision sanctions re-specifying the residue clusters faithfully, and the residue was
   produced under the S8 trigger; design §5 carries the phase-shift attribution disclosure
   for exactly this dependence.
3. **Informative (analyst note).** `EntryZ` is the ≤t-1 decision-close z, not the intra-bar
   touch z (smoke: |EntryZ| median 1.26/1.78/2.13 for levels z*=1.5/2.0/2.5; min 0.09).
   Consistent with §2's conditioning contract; but any analysis stratifying on EntryZ must not
   treat it as the level z — `LadderLevel` is the level identifier.
4. **Low (destroy-arm fidelity nuance, no change required).** `gen_exp018_schedules.py`
   maps a leg to `searchsorted(open_times, EntryTime) − 1`, which for intra-bar limit fills is
   the FILL bar, not the arm bar (the docstring says "bar BEFORE its entry fill") — up to 1
   bar of jitter in template offsets. Per-level counts, directions, and realized holds are
   preserved exactly; for a random-timing exposure-matched null the jitter is immaterial.
   Censored live legs enter templates with holds capped at 48 (exposure-conservative).
5. **Informative.** The arm-A moving TP keeps the favorable-assert guard (a TP is left stale
   rather than moved adverse) — the inherited EXP-014b/E0 semantics the design's §4 arm A
   builds on, disclosed in run_metadata (`favorable_asserted`); smoke shows the TP moving on
   783/784 bars, so the guard bites rarely. The analyst should treat `form2_favorable_limit`
   exits as fills at the (near-)current anchor.
6. **Informative.** Arm B (`bracket`) and the phase-shift feed have no EXP-018 smoke
   emission; both are unchanged, previously-validated code paths (EXP-016/EXP-014b), verified
   here by git-diff trace. If the operator wants belt-and-braces, a truncated B-extend smoke
   is cheap — not required.

### Verdict rationale

Every §4/§5/A1 clause traces to implementing code with no deviation; the L-14 exit-set diff is
evidenced by the smoke ExitReason census (no form-1, no SL in arm A); all three golden-trace
items pass with QA-computed expectations; fences verified against their upstream sources;
schedule/delay arms are loud-fail and cannot contaminate live cells; legacy exit sets are
regression-safe at the defaults; the estimand hard gate passed on the smoke cell. The single
open item is a one-line registry row (Issue 1), which is an operator/documenter action, not
implementation drift. **APPROVE** — execution remains the operator's gate.
