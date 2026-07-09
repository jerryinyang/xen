# EXP-025 — QA review (append-only)

## QA run 1 — 2026-07-08T20:02:51Z — mode: subagent — HEAD 546336b
Reviewed state: HEAD `546336bf0ea56e39252de0aaf8b16fc9ee3deec8` + uncommitted EXP-025 work
(dirty: `StrategyHost/SignalRecords.cs`, `StrategyHost/StrategyRunParquetWriter.cs`, `Xen.cs`;
untracked: `StrategyHost/WilderHtfState.cs`, `StrategyHost/HtfDiBreakoutModel.cs`,
`Xen.HtfDiNative.cs`, `tools/ctrader-cli/experiments/EXP-025-*.conf`, `gen_exp025_confs.py`,
`tools/HtfDiSmoke/`, `python/experiments/EXP-025/`).
Design reviewed: `python/experiments/EXP-025/design.md` incl. the dated 2026-07-08
pre-measurement amendments in §6/§7/§8/§11 (treated as binding).

**Verdict: APPROVE** — ready for the operator's execution gate (T1 + controls).
One pre-T2 decision item (Issue 4 / deviation D3) must be resolved by operator/designer
before T2 confs are generated; it does not block T1/controls/battery/shift execution.

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §3 LTF signal `Close[t] > max(High[t−X..t−1])` / `< min(Low[…])`, confirmed bars, act at Open(t+1) | `HtfDiBreakoutModel.cs:182–189` (channel from prior-X queues), `:226–257` (decision on closed bar), `:144–165` (pending entry fills at next bar Open), `:259–262` (queues folded AFTER use — signal bar excluded) | MATCHES | Prior-X channel verified independently vs raw data (golden trace, exact) |
| §3 HTF gate long iff +DI>−DI (mirror short); HTF state = most recent 1h bar with CloseTime < Open(t+1); never forming bar | `WilderHtfState.cs:79–122` (snapshots only on CLOSED 1h bars; Snapshot(shift)), `HtfDiBreakoutModel.cs:235–239` (gate), `:146–151` (hard leak assert at fill) | MATCHES | Assert uses `CloseTime > bar.OpenTime → throw` (allows equality) — see Issue 3; equality unreachable with ordered bars; 0 equality rows in smoke |
| §3 Wilder ADX/±DI/ATR(14) on 1h, frozen; warmup ≥ 28 closed 1h bars | `WilderHtfState.cs:39–40` (`DmiPeriod=14`, `MinClosedBars=28`), `:124–185` (classic Wilder seed+smoothing), `:112–122` (Snapshot null until warmup, counted on the SHIFTED stream) | MATCHES | DI stream verified vs independent derivation to 3.6e-14 over 5,486 trades |
| §3 X grid {2,3,4,5,8} predeclared | `gen_exp025_confs.py:42` (`X_GRID`); 20 T1 confs present | MATCHES | |
| §3 holds {12,24,36,48}, E0 exit at bar open, held exactly H | `gen_exp025_confs.py:43`; `HtfDiBreakoutModel.cs:194–198` (barsHeld incl. decision bar; staged at close of entry+H−1, fills at open of entry+H) | MATCHES | Smoke: `BarsHeld=24` uniformly, open-to-open |
| §3 variants = analysis-side ATR strata of one `di` stream; regime emitted per trade | `HtfDiBreakoutModel.cs:339` (`EntryVolRegime`), `:283` (per-bar `VolRegime`); no separate engine vehicles | MATCHES | |
| §3 ATR regime trailing 2016 closed 1h bars, causal, UNSET until full (excluded from strata, in `di`) | `WilderHtfState.cs:41` (`RegimeWindow=2016`), `:194–199` (window of closed-bar ATRs incl. the just-closed bar — causal at decision time), `:33` (−1 UNSET) | MATCHES | Smoke early trades carry `EntryVolRegime=-1` as expected |
| §3 one position per run; signals ignored while open; fixed 1-unit | `HtfDiBreakoutModel.cs:226` (`_position==0` precondition — no decision while open); native arm `_hdLeg is null` (`Xen.HtfDiNative.cs:221`); min-volume units native (`:108`) | MATCHES | Verified empirically: sim with one-position rule reproduces smoke trade stream exactly |
| §3 22-symbol universe, 1h/5min only | confs `SYMBOLS` (22, matches design list; STOXX50/DE40 broker names per dataset-reference); `Xen.cs:643–645` + `Xen.HtfDiNative.cs:82–84` (`DomainMinutes==5` guards) | MATCHES | |
| §3 AnalysisEndUtc fence at per-symbol 70% cutoff | confs `ANALYSIS_END`; `Xen.cs:536–537,552` (fence before processing; `ReadBefore`); native `:131–136,181–186` | MATCHES | Cutoffs independently recomputed (see Governance) |
| §3 E0/E2/E3/E5/E6 decide on closed bars, act next open | `HtfDiBreakoutModel.cs:191–221` (switch stages exit; executes at next bar open `:136–142`) | MATCHES | E3 uses last CLOSED HA bar (`_haOpen/_haClose` folded in step 5 after use); P&L on real prices |
| §3 E1/E4 native stop/limit, m1 fills, never self-fill (L-14); TP 3.0×/SL 1.5× entry-frozen 1h ATR; 96-bar backstop | `Xen.cs:646–649` + `HtfDiBreakoutModel` refusal of e1/e4; `Xen.HtfDiNative.cs:33–35` (mults/backstop), `:240–243` (`ExecuteMarketOrder` with sl/tp pips from frozen snapshot ATR), `:199–205` (backstop) | MATCHES | Gate=di only enforced (`:93`); StrictCoverage required (`:98`); own strict 5min bucketer gives signal parity with StrategyHost arm |
| §4 estimand per-leg; reconciliation; no local accounting | `cis_trades` rows (`RealizedBps`, `Censored`); smoke `estimand_validation.json` BLOCKING_PASS=true, `abs_diff_bps=0.0` | MATCHES | `check_no_local_accounting` PASS (see Governance) |
| §5 staged T1 440 / T2 ≤ 60 / battery / shift | `gen_exp025_confs.py` stages `t1|controls|t2|battery|shift`; 20 T1 confs × 22 symbols = 440 | MATCHES | T2/battery/shift confs generated post-T1 by design |
| §6 battery seeds 1001–1025, matched-cadence, Bernoulli(0.5) | `gen_exp025_confs.py:44`; `HtfDiBreakoutModel.cs:106–107` (seed required), `:114` (`Random(seed)`), `:239` (eligibility = DI gate — same event timestamps), `:245–246` (one draw per gated staged event) | MATCHES | Determinism: fixed seed + deterministic event stream + E0 direction-independent busy windows → byte-identical regenerable (code inspection; .NET `Random(seed)` deterministic under the pinned runtime). See Issue 5 on D5's E5 note |
| §6 reference arm seed 2001 | `HtfDiGateMode.StateOnly` per-bar HTF-state emission (`EXP-025-ref.conf`); seed-2001 sampling analysis-side (deviation D4) | MATCHES (as amended by D4) | Seed 2001 NOT engine-side — analyst must pin it (Issue 6) |
| §6 null sentinel ADX-only, symmetric-sign | `HtfDiGateMode.AdxSentinel`: gate = `ADX > trailing-2016 median` (`WilderHtfState.cs:201–210`), direction = breakout side (no DI read); `EXP-025-sent.conf` | MATCHES (D1 window operator-resolved) | |
| §6 tripwire +60-bar HTF phase-shift, whole stream, cadence preserved | `HtfShiftBars` → `WilderHtfState.Snapshot(60)`; the SAME shifted snap feeds entry gate, E5 exit, per-bar emission, and per-trade columns (`HtfDiBreakoutModel.cs:172–173,214,270,329–349`); native `:191` | MATCHES | Shift = lagged (older) context — causal; warmup counted on the shifted stream (`WilderHtfState.cs:117–120`); blocking criterion itself is analysis-side per §6 |
| §8 TEST family E0×4 holds + exit* single stat | design amendment (D2) — analysis-side; no engine surface | N/A (analysis) | Recorded; nothing to trace in code |
| §13 golden trace | emission columns `BreakoutRef/SignalX/HtfPlusDi/HtfMinusDi/HtfAdx/HtfAtr/HtfBarCloseTime` (`SignalRecords.cs:142–148`, `StrategyRunParquetWriter.cs:307–313,351–357`); developer did NOT generate the trace | MATCHES | QA derivation below |
| §14 hard splits: leak asserts, fence, censored rows | asserts both arms; fence host+native; `FlushOpenAsCensored` → `open_at_end` censored row drained in `OnStop` (`Xen.cs:376–382`); native `FlushHtfDiNativeCensored` (`Xen.cs:362–363`) | MATCHES | Smoke: exactly 1 censored row, `RealizedBps=NaN` |
| §15 exclusions (no 1d/1h, no 4h/1h, no ADX variant axis, no sizing) | no code path for other domains (`DomainMinutes==5` throws); no sizing parameters | MATCHES | ADX appears only as the sentinel gate + disclosure column, not a variant axis |
| Registration: enum ordinal / params / factory / provenance | `Xen.cs:24–43` (`HtfDiBreakout` = ordinal 9 = conf `STRATEGY_VALUE="9"`), `:217–245` (params), `:641–679` (factory + e1/e4 refusal + gate parse), `:806–821` (run_metadata provenance incl. `phase_shift_bars`, warmup, regime window) | MATCHES | `MODE=0` = StrategyHost; t2 native cells get `mode=3` = NativeOrders (enum verified) |

Checked against the three shipped failure shapes: no frozen computation (HTF state and channel
update every bar; E5 re-reads the live shifted snapshot), no anchor drift (entry-frozen values —
`_entrySnapshot`, `_entryBreakoutRef`, E1/E4 barrier ATR — are captured once at entry and never
recomputed), no confounded comparator (battery shares the exact DI-gated event timestamps; sentinel
and reference arms are separate labeled runs, populations disclosed).

### Golden-trace diff (design §13)

Independent derivation (QA's own code, `scratchpad/qa025_golden.py`; developer code not reused):
USTEC m1 `timebars_ustec_20210602_000000_20260621_190833.parquet` (1,784,619 rows), TRAIN = first
70%×70% of m1 rows (874,463 rows, end 2023-11-20 23:15 UTC — matches design §13's stated cutoff),
strict clock-aligned 5min buckets (exactly 5 m1 bars, engine parity), 1h buckets keyed
`(closeSecs−1)/3600` with no coverage floor, Wilder DI(14) per the classic construction, X=3
prior channel excluding the signal bar, warmup 28 closed 1h bars, one-position E0 H=24 replay.

| # | Design event | QA derivation | Smoke emission | Verdict |
|---|---|---|---|---|
| 1 | sig 2021-07-01 00:05 short, 14562.8 < LL₃ 14563.1, HTF close 00:00, DI 16.241/19.002, entry 00:10 @14562.9 | sig 00:05 short, close 14562.8, ref 14563.1, HTF close 00:00, DI **16.220/18.978** — gated event confirmed | no trade (position-suppressed: short entered 2021-06-30 23:05 still open under H24 — expected one-position behavior; see Issue 2) | MATCHES (timestamps/side/ref/price exact; DI Δ≈0.02 — Issue 1) |
| 2 | sig 01:15 long, 14583.3 > HH₃ 14581.6, HTF close 01:00, DI 18.867/17.914, entry 01:20 @14583.2 | sig 01:15 long, ref 14581.6, HTF close 01:00, DI **18.844/17.892**, entry 01:20 @14583.2 | trade: EntryTime 01:20, dir +1, fill 14583.2, BreakoutRef 14581.6, HtfPlusDi 18.8444, HtfMinusDi 17.8918, HtfBarCloseTime 01:00, BarsHeld 24 | MATCHES (price exact; DI matches QA derivation to 1e-3, design table off ~0.02 — Issue 1) |
| 3 | sig 01:55 long, 14579.9 > HH₃ 14578.4, HTF close 01:00, same DI, entry 02:00 @14580.0±0.1 | sig 01:55 long, close 14579.9, ref 14578.4, HTF close 01:00, DI 18.844/17.892 — gated event confirmed | no trade (position-suppressed by event-2's open trade — expected) | MATCHES (event level) |

**Full-stream diff (beyond the 3 pinned events):** QA's one-position replay produced 5,486 TRAIN
trades; the smoke emission's first 5,486 realized trades agree with **0 entry-timestamp
mismatches, max |entry px| diff 0.0, 0 direction mismatches, max |DI-gap| diff 3.6e-14,
0 HTF-bar-CloseTime mismatches, max |BreakoutRef| diff 0.0**.

**Leak-guard audit over the WHOLE smoke emission (7,855 rows):** rows with
`HtfBarCloseTime >= EntryTime` (entry bar Open): **0**; rows with equality: **0**. Every trade's
conditioning HTF bar closed strictly before the entry bar open.

### Governance & boundary

| Check | Result | Evidence |
|---|---|---|
| Mandatory declaration blocks in design.md | PASS | MECHANISM (§1), OBJECT-IDENTITY (§2), named controls w/ population/bite/non-vacuity (§6), quantified tripwire (§6), SEL-NEIGHBOR (§7), multiplicity math + read cap (§8), POWER (§9), BANDS (§11), golden trace (§13), HARD/INFORMATIVE split (§14) |
| `check_no_local_accounting("python/experiments/EXP-025")` | PASS | `{'ok': True, 'banned_defs_found': []}` (PYTHONPATH=python/src) |
| No Python analysis/backtest in experiment | PASS | `code/` contains only `README.md`; no `.py` anywhere under EXP-025; strategy runs in cTrader engine |
| Registry preconditions | PASS | `CF-HTFDI-001/HYP-A` row → EXP-025 in multiplicity-registry (0 slots, 0 reads); `SEL-NEIGHBOR` registered in `global-techniques.md` §Neighbour-Stability Selection + registry pre-measurement note |
| Holdout fence | PASS | Independently recomputed 70%-row CloseTime of the canonical 20210602 files: USTEC 2024-12-11T17:34, EURUSD 2024-12-12T15:11, BTCUSD 2025-03-12T19:23, STOXX50 2025-01-29T10:39 — all equal conf `ANALYSIS_END`; `BACKTEST_END` = cutoff + 1 min; engine reads only bars before the fence (`ReadBefore` + per-bar stop); smoke fence check PASS |
| Registered seeds | PASS (engine side) | Battery 1001–1025 in `gen_exp025_confs.py:44` = design §6/§12; reference seed 2001 analysis-side per D4 (Issue 6) |
| Battery regenerability | PASS (by inspection) | Fixed `Random(seed)`, one draw per DI-gated staged event; event stream deterministic; E0 busy windows direction-independent → same seed ⇒ identical direction sequence and timestamps |
| Deviations D1–D5 recorded + operator-resolved | PASS | `code/README.md` DEVIATIONS block, all dated 2026-07-08 operator-resolved; D2 amended into design §8 in place; D3 assessed below (Issue 4) |
| Estimand gate on smoke | PASS | `exp025-smoke/estimand_validation.json`: blocking_pass=true, reconciliation abs_diff 0.0 bps, fence ok, schema ok, 7,855 legs / 1 censored |
| TEST quarantine | PASS (structural) | Emission covers full analysis window; quarantine is an analyst-stage control (§5) — nothing in the engine reads TEST separately; counted-read cap ≤ 5 + eligibility in design §8 |

### Deviations review

- **D1** (sentinel ADX median window = trailing 2016): reasonable, same window as the regime; symmetric, no DI read. ACCEPTABLE.
- **D2** (TEST family = E0×4 + exit* single stat): design §8 amended in place, dated, operator-resolved. ACCEPTABLE.
- **D3** (E2 ≡ E6): **verified — the equivalence claim is TRUE as implemented.** E2 (trail lookback = entry X, close-confirmed breach of the trailing prior-X channel) and E6 (opposite X-breakout, ungated) reduce for a long to the identical predicate `Close[t] < min(Low[t−X..t−1])` (mirror short); the code shares one branch (`HtfDiBreakoutModel.cs:200–203`) with distinct labels. The equivalence holds only under the UNGATED reading of "opposite X-breakout signal"; if the designer intended the opposite signal to carry the HTF-DI gate (§1 defines the *event* as the gated breakout), E6 would be a strictly rarer exit and NOT equivalent. See Issue 4 — resolve before T2.
- **D4** (reference arm = state emission + analysis-side seed-2001 sampling): matches the EXP-019 D1 precedent; entries carry no price info, estimand is dir_gap on forward returns. ACCEPTABLE; regenerability shifts to the analyst (Issue 6).
- **D5** (battery cadence exact under E0, approximate under direction-dependent exits): correct in substance; note E5's exit predicate (HTF-DI flip vs entry state) is itself direction-independent, so E5 batteries also preserve timestamps exactly — D5 overstates the approximate set (Issue 5, harmless).

### Issues

1. **MINOR (design-table numerics, informative)** — design §13 DI values are off by ≈0.02 vs both QA's independent derivation and the emission (event 1: 16.241/19.002 vs 16.220/18.978; events 2–3: 18.867/17.914 vs 18.844/17.892). QA's recipe-faithful derivation (strict 5-of-5 m1 coverage on 5min buckets — the engine's parity semantics) agrees with the emission to 3.6e-14 across all 5,486 TRAIN trades, so the discrepancy is in the designer's derivation (likely a coverage-floor difference in the 5min resample), not the implementation. Gate decisions, sides, timestamps, refs, and prices are identical everywhere. No action required for execution; designer may annotate §13 for the record.
2. **MINOR (expected behavior, disclosed)** — golden events 1 and 3 do not appear as trades in an H24 `di` emission: event 1 is blocked by a short entered 2021-06-30 23:05 (still open), event 3 by event 2's own trade — exactly the design's one-position-at-a-time rule. QA verified them on the position-blind gated-event stream instead. The §13 table implicitly assumes a flat book per event; future golden traces should pin flat-book events.
3. **NOTE (assert bound)** — the StrategyHost leak assert (`HtfDiBreakoutModel.cs:148`) throws on `snapshot.CloseTime > bar.OpenTime`, permitting equality, while design §3 requires strict `<`. Equality is unreachable (snapshot CloseTime ≤ decision-bar OpenTime < entry-bar Open for ordered bars) and the emission contains 0 equality rows; the native-arm assert (`Xen.HtfDiNative.cs:231`) is bound at the signal close, which is strictly earlier than the fill. No change required; recorded so a future refactor doesn't weaken it.
4. **PRE-T2 DECISION (route: operator + quant-designer)** — D3: running both E2 and E6 in T2 produces byte-identical trade streams under the implemented (ungated) reading — up to ~10 duplicate engine runs and a duplicate column in the exit-selection table. Before generating T2 confs, either (a) drop E6 from the T2 exit list (`--exits e1,e2,e3,e4,e5`), or (b) amend design §3 to define E6 as the DI-gated opposite breakout and have the developer split the predicate. Not blocking T1/controls/battery/shift.
5. **NOTE** — D5's "approximate under E2/E3/E5/E6" overstates: E5's flip exit is direction-independent, so E5 batteries preserve candidate timestamps exactly. Analyst should still disclose realized-cadence deltas per D5 for E2/E3/E6.
6. **NOTE (analyst obligation)** — reference-arm seed 2001 is not engine-side (D4): the analyst's sampling code must pin seed 2001 and be regenerable; the estimand-gate/analysis stage should verify this (QA verified engine-side battery seeds only).

### Verdict

**APPROVE.** Design-to-code fidelity verified clause-by-clause; golden trace independently
re-derived and byte-consistent with the smoke emission over the full TRAIN trade stream; leak
guard holds on every emitted trade; governance checks (accounting boundary, holdout fence,
seeds, registry preconditions, deviations) all pass. Issue 4 (E2/E6 duplication) must be
resolved by the operator/designer before the T2 stage; Issues 1–3, 5–6 are informative.
Execution remains the operator's gate.
