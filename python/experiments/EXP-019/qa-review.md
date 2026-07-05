# EXP-019 QA review (append-only)

## QA run 1 — 2026-07-04T22:59:53Z (completed 2026-07-05 UTC) — mode: subagent — HEAD a2bce28
Reviewed state: HEAD a2bce28 + dirty tree (Xen.cs, Xen.RandomHold.cs, run-experiment.sh,
gen_exp019_schedules.py, EXP-019*.conf, run-exp019-all.sh, evaluation.py — all uncommitted).
Fresh context confirmed: this session contains no EXP-019 implementation work.

Verdict: **APPROVE**

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §4 unconditional market entry at scheduled bar open | Xen.RandomHold.cs:198-224 `FireRhScheduledEntries` | MATCHES | Fires rows whose `open_time_utc` == forming bar open; `ExecuteMarketOrder(..., null, null, ...)` — no SL/TP attached. Verified against emission: 727/727 legs pair 1:1 with schedule rows, 0 dir/hold mismatches. |
| §4 exit = market at open of entry-bar+H, nothing else | Xen.RandomHold.cs:167-180 | MATCHES | `EntryH4Index` = decision bar (fill at open of idx+1); close staged when completed bar i − EntryH4Index ≥ H → fill at open(i+1) = open(fill-bar+H). Exit-time audit: 619/727 exact, rest first-tick lag, all ≥ scheduled time. All 727 exits `matched_hold`. |
| §4 NO TP / NO SL / no refresh / no ladder (L-14) | whole partial | MATCHES | grep: zero `ModifyPosition`/`StopLoss`/`TakeProfit`/`PlaceLimitOrder`/`PlaceStopOrder` in Xen.RandomHold.cs. Only order calls: ExecuteMarketOrder (entry, null SL/TP) + ClosePosition (matched_hold). `unstaged_close` fallback reason exists but is unreachable absent broker-forced closure (balance 1e8, min volume); smoke shows 0. Exactly ONE exit path. |
| §4 inventory cap 6, skip + `cap_skip`, never deferred | Xen.RandomHold.cs:212-218 | MATCHES | Deterministic skip (`continue`, cursor already advanced — never deferred); event + Print. Exits processed before entries on the same bar (line 167 block precedes line 187), so freed capacity counts. cTrader backtest fills synchronously → `_rhLegs.Count` correct within the loop. |
| §4 fixed 1-unit sizing | Xen.RandomHold.cs:115 | MATCHES | `NormalizeVolumeInUnits(VolumeInUnitsMin)`, never varied; metadata `sizing=fixed_min_volume_never_varied`. |
| §4 fence / TRAIN band (A1) | Xen.RandomHold.cs:98,110,146-151; EXP-019*.conf ANALYSIS_END/BACKTEST_END | MATCHES | 11 shared instruments byte-match EXP-013.conf; 5 new values byte-match A1 (XAUUSD 2024-08-26T09:56Z, BTCUSD 2024-10-31T14:05Z, EURJPY 15:12Z, GBPJPY 15:28Z, AUDJPY 14:39Z). `HoldoutFence.ShouldStopBeforeProcessing` → Stop(); BACKTEST_END caps data load at the fence. Estimand gate confirms last bar 2024-09-06 05:00 ≤ fence 05:42. |
| §4/A2 drop can't-complete entries | gen_exp019_schedules.py:88 | MATCHES | `fill_idx + hold > n - 2 → continue` = A2 rule; smoke 0 censored; RR counter `k` increments before the drop test so hold phase is preserved (twin stays the same draw). |
| §4/A3 warmup 50 bars, gap U[4,12] | gen_exp019_schedules.py:35-36,78-81 | MATCHES | `WARMUP_BARS=50`, `rng.integers(4, 13)` inclusive, mean 8. 744 rows / ~5900 bars ≈ 1/7.9 cadence. |
| §4/§7/A4 schedule data-independence | gen_exp019_schedules.py:61-66 | MATCHES | `pl.read_parquet(..., columns=["SourceCloseTime"])` — the ONLY data read; no price column anywhere in the generator. Seeds: BASE 20260705, seed_i = base+i, i∈1..25 (design §4). |
| §4 seed grid / hold RR {6,12,24,48} | gen_exp019_schedules.py:33-37,85 | MATCHES | Round-robin in schedule order; smoke holds {6:182, 12:182, 24:182, 48:181}. |
| §3 estimand emission contract | Xen.RandomHold.cs:280-329 | MATCHES | Per-bar SignalPositionRecord (real OHLC, OpenLegs, MtmBps) + per-leg CisTradeRecord (RealizedBps gross, Censored, HorizonBars=hold). `xen.estimand_validation` ran unchanged: blocking_pass true, per-bar↔per-leg reconciliation diff 2.3e-12 bps. |
| §3 engine emission gross-of-cost (A5/D5) | Xen.RandomHold.cs:308-320 | MATCHES | RealizedBps = dir·(exit−entry)/entry·1e4; re-derived for all 727 legs, 0 formula mismatches. Costs live only in analysis layer (evaluation.py). |
| §7 tripwire 1 (regeneration byte-diff) | executed by QA | PASS | See below. |
| §7 tripwire 2 (fill causality) | executed by QA | PASS (with disclosure) | See below. |
| §7 tripwire 3 (+1-bar twin) | gen_exp019_schedules.py:69-91 shift=1; EXP-019-delay1.conf | MATCHES | `fill_idx = idx + shift`, dir/hold unchanged → same draw displaced wholesale; twin conf NZDUSD-only, same fence, `..._seed<i>_shift1.csv`. 25 shift1 CSVs present. |
| §11/A6 conf packaging | EXP-019-cal.conf / EXP-019.conf / EXP-019-delay1.conf; run-exp019-all.sh | MATCHES | One multi-symbol conf per arm, seed via `EXP019_SEED` (guarded `:?`), single family root per arm. STRATEGY_VALUE=6 == enum RandomHold (7th member, appended — existing values unshifted). MODE=3 = NativeOrders; StrategyHost factory throws for RandomHold (Xen.cs:519). |
| §12 A1–A6 vs DEVIATIONS D1–D6 | Xen.RandomHold.cs:20-41 | MATCHES | D1↔A4, D2↔A1, D3↔A2, D4↔A3, D5↔A5, D6↔A6 — every deviation is a dated §12 amendment in the binding design (operator-resolved 2026-07-04), not a silent drift. |

### Tripwire 1 — schedule regeneration byte-diff (HARD)

Copied all 50 consumed NZDUSD CSVs (25 live + 25 shift1) aside, reran
`python3 tools/ctrader-cli/experiments/gen_exp019_schedules.py --symbols NZDUSD`, byte-compared
(`cmp`) every file: **ALL 50 BYTE-IDENTICAL**. git status confirms no schedule file changed.
Determinism from (seed, calendar emission) verified. PASS.

### Golden-trace diff (§10 — expectations derived from design + seed-1 CSV + calendar, never from the implementation)

Seed-1 CSV = seed 20260706 (base+1), 744 rows; 17 rows precede the 2021 m1 feed start
(stale-skipped, disclosed); 727 consumed rows ↔ 727 emitted legs, 1:1 in order.

- **T1** first fired entry — expected (CSV row 18 + calendar): open 2021-01-04 10:00Z, dir +1,
  hold 12, fill = bar RealOpen 0.72195. Emitted: EntryTime 2021-01-04 10:00, dir +1, hold 12,
  EntryFill 0.72195 (0.0 pips off open); exit at 2021-01-06 10:00 = open of entry-bar+12,
  BarsHeld 12. **MATCH.**
- **T2** mid-schedule hold-6 leg — expected: entry 2022-11-01 17:00Z dir −1, exit open
  2022-11-02 17:00Z (entry-bar+6), entry_open 0.58368, exit_open 0.58621,
  P&L = −1·(0.58621−0.58368)/0.58368·1e4 = −43.3457 bps. Emitted: identical timestamps and
  fills, RealizedBps −43.34566885964968, BarsHeld 6, matched_hold. **MATCH to 1e-9.**
- **T3** cap behavior — this seed's densest cluster: independent inventory simulation over the
  CSV (exits freed before same-bar entries, matching code order) gives max concurrent = 5,
  expected cap_skips = 0. Emission: max OpenLegs = 5, zero cap_skip events. Cap code path
  verified by inspection (Xen.RandomHold.cs:212-218): deterministic skip with logged event,
  cursor advanced, never deferred; `RhMaxOpenLegs` default 6 and validated ≥1. **MATCH**
  (skip branch not exercised on this seed — logic verified by inspection + simulation
  agreement on the ≤6 invariant).

Whole-population extensions: dir/hold match on all 727 pairs; RealizedBps formula re-derived
on all 727 legs with 0 mismatches; exit reasons 100% matched_hold; 0 censored.

### Fill-causality audit (§7 tripwire 2)

Entry lag (fill − scheduled open): 620/727 exact 0s, 92 at +60s, 15 > 60s (max 3600s).
Exit lag (fill − open of entry-bar+H): 619 exact, 96 at +60s, 12 > 60s (max 7200s).
**No fill is ever EARLY (min lag 0 — no lookahead).** All >60s lags sit at session boundaries
(Sunday 21:00 opens, one 2023-03-12 DST switch = exactly 1h): first-tick-of-session fills where
the m1 feed has no tick at the nominal open. Deterministic market mechanics, seed-independent,
direction-neutral; fills and P&L are honest (fill price = actual tick). Not a systematic
early/late pattern in the design's REJECT sense. Disclosed; post-run re-audit across all 16
instruments recommended (indices have daily session gaps → larger lag tails expected).

### Governance & boundary

- Declaration blocks: MECHANISM/DERIVED (§1), OBJECT-IDENTITY (§2), CONTROL ×2 with bite/MDE +
  non-vacuity (§5), TRIPWIRE (§7), POWER + UNPOWERED rules (§8), BANDS (§9), golden trace (§10),
  hard/informative split (§7) — all present. ✓
- `check_no_local_accounting("experiments/EXP-019")` → `{'ok': True, 'banned_defs_found': []}`. ✓
- No Python strategy backtest anywhere; experiment code dir contains only README.md + the FTMO
  snapshot JSON. ✓
- Estimand gate: `results/smoke_estimand_validation.json` → blocking_pass true, schema ok,
  fence ok, reconciliation 2.3e-12 bps. ✓
- Family registered (CF-VOLHARV-001, 2026-07-04); 0 counted reads, TRAIN only — no TEST tally
  needed. ✓
- Holdout: BACKTEST_END = ANALYSIS_END = 49% TRAIN fence per instrument; engine fence stops
  before processing any bar closing past it; TEST band (49–70%) and final-30% holdout never
  emitted. ✓
- Schedule data-independence: generator reads exactly one timestamp column; provable by
  construction + tripwire-1 byte-diff. ✓
- DEVIATIONS D1–D6: each is a dated operator-resolved amendment in binding design §12
  (evidence: A1–A6 table, operator-locked parameters header). ✓
- No scope expansion: model partial + wiring + generator + 3 confs + driver + harness fix +
  A5 cost table — all trace to design + §12. ✓
- Shared-code boundary:
  - `run-experiment.sh` `run_complete` baseline-aware change: all call sites updated in-file;
    for fresh cells baseline is empty and behavior is identical; for repeated same-cell runs it
    fixes a genuine premature-stop bug (previous seed's finished dir satisfied the old check).
    Backward-compatible for every other experiment conf. ✓
  - Xen.cs EXP-019 touches: enum append (existing values unshifted), OnStart/OnBar/OnStop
    dispatch guarded by `_rhReady` (set only when Strategy==RandomHold), BuildStrategyParameters
    new case, StrategyHost-factory throw. `LoadSchedule`/`ScheduledEntry`/`ClosingPriceOf`
    reused read-only. CIS code paths untouched by EXP-019 (the harvest/delay/schedule-mode
    edits in the same dirty tree are EXP-018 scope, previously reviewed). ✓
  - `evaluation.py` is a new shared analysis module (INFR-001 WS-7) that also carries the A5
    `FTMO_COSTS`/`round_trip_cost_bps` table — informative-only by design, never gating; no
    engine or adjudication contact. ✓

### Issues (all informative — none blocking execution)

1. INFO — FTMO `spread_pips` is None for all 16 instruments; `round_trip_cost_bps` raises until
   pinned (guard verified in code, evaluation.py:238-241). Must be pinned from the live FTMO
   page BEFORE the binding cost read (analysis-stage blocker, not execution). Developer's own
   open item — operator should be aware it gates deliverable 2.
2. INFO — FTMO commission ambiguity (per-side vs round-turn; XAUUSD percent vs USD figures
   mutually inconsistent) is recorded verbatim with an explicit `commission_events` multiplier —
   adequate disclosure; analyst must state which reading was used.
3. INFO — 17/744 NZDUSD schedule rows are stale (pre-2021 m1 feed vs 2020-11 4h calendar
   start), uniform across seeds, engine-logged. Expect similar small head-loss on other
   instruments; stale counts should be disclosed per run in analysis (cadence unaffected;
   hold strata stayed balanced 182/182/182/181).
4. INFO — session-boundary fill lags (≤1–2h at Sunday opens/DST, ~2% of fills, never early).
   Re-run the fill-causality audit on all instruments post-execution; indices will show larger
   tails from daily session gaps.
5. INFO — smoke seed-1 NZDUSD gross total is +3697 bps over 727 legs (~+5.1 bps/leg): a single
   draw, consistent with the analytic null at per-seed SE ≈ 8–25 bps — no pre-read concern;
   noted so the battery read is not anchored on it.

### Verdict

**APPROVE** — ready for the operator's execution gate (441 runs: 16 cal + 400 live + 25 twin).
Execution remains the operator's decision; this approval launches nothing.
