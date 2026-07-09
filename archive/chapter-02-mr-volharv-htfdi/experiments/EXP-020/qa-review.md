# EXP-020 QA review (append-only)

## QA run 1 — 2026-07-05T17:16:17Z — mode: subagent — HEAD a2bce28 (dirty: EXP-020 files uncommitted)
Verdict: **APPROVE** (notes 1–3 for the operator at the execution gate; no code change required)

Reviewed: `design.md` (incl. A1 + dated 2026-07-05 §3 clarifications), `Xen.StructureHarvest.cs`,
`Xen.cs` wiring, `StrategyHost/SignalRecords.cs` + `StrategyRunParquetWriter.cs` diffs,
6 confs `tools/ctrader-cli/experiments/EXP-020-{R,R-twin,G,G-invert,R-delay1,G-delay1}.conf`,
`code/derive_exp020_params.py` + `code/README.md` clause map. Build verified independently:
`dotnet build Xen.csproj -c Debug` → 0 errors.

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §3R virtual 50/50 constant-mix, unit notional | Xen.StructureHarvest.cs:133–147 (init buy, cash leg = asset leg at fill; V0=2·cash) | MATCHES | Real position + virtual cash; scale cancels in log-return path (README sizing note) |
| §3R trigger \|w−w*\|≥b at t−1 close, trade at open t | :150–160 (decision on completed bar `effIdx=i−ShDelayBars` close; market order fills first tick of forming bar) | MATCHES | Code uses ≥ (boundary-inclusive) vs design "outside [w*−b,w*+b]" — measure-zero difference (note 3) |
| §3R restore to w*=0.5 | :160 `deltaUnits = 0.5·v/c − units` | MATCHES | Target computed at decision close; sell path caveat in note 2 |
| §3R twin never rebalances, identical init | :150 `!ShTwin` guard; init path shared (:133) | MATCHES | |
| §3R emission: per-bar path + every trade | :211–233 `EmitRebBar` (PortWeight/PortUnits/PortCash, MtmBps vs V0) + :204 `RebBookTrade` → trade_blotter | MATCHES | cis_trades intentionally empty — consistent with §2 (path object, not legs) |
| §3G anchor = prev-calendar-month close, monthly reset, inventory carried | :323–341 boundary via forming-bar month change; `_gridAnchor=Close[boundary]`; `CancelGridEntryOrders` (:436) cancels label-matched PENDING orders only — TPs are position attributes, untouched | MATCHES | Causal: anchor is a completed bar's close; reset applies at month's first bar (delay=0) |
| §3G levels A±k·g, k=1..4, 1 unit, native pending | :48–49 consts; :376–413 `ArmGridLevels`; min-volume units; `PlaceLimitOrder`/`PlaceStopOrder` | MATCHES | Placement-validity skip (`arm_skip_breach`, :396–405) is an added broker-constraint guard, disclosed via events, symmetric across twin (note 3) |
| §3G MR unwind: buy A−k·g → sell A−(k−1)·g (k=1 at A); mirrored sells | :360–367 `GridLevel` MR branch; TP set at fill (:464) | MATCHES | T2 arithmetic exactly as clarified |
| §3G inverted twin: STOP entries, unwind one level AWAY (2026-07-05 clarification) | :368–373 twin branch (buy stop A+k·g, TP A+(k+1)·g; mirrored) | MATCHES | Same width g, same cost structure, opposite conditioning — B-6 satisfied |
| §3G no SL | :410–412 (SL args null); no SL anywhere | MATCHES | |
| §3G/§10 T3 cap 8: order NOT placed, logged | :388–392 (`legs + pending ≥ 8` → `cap_skip` event, order skipped) | MATCHES | Counts pending entries toward cap — the only reading that hard-guarantees inventory ≤ 8 with resting orders (conservative superset of "8 legs") |
| §3G month-end/fence censoring disclosed, never dropped (VAL-006) | :549–565 `FlushGridCensored` → `open_at_end`, Censored=1, marked to last close | MATCHES | Monthly reset never force-closes inventory (only entry orders cancelled) |
| §2 fills = m1 touch, native orders (Mode=3) | Confs `MODE=3`; Xen.cs:239–250 NativeOrders routing; :557–558 hard-throws if run under StrategyHost | MATCHES | Tripwire 3 substrate is the native m1 backtester; post-run verification columns present (EntryTime/ExitTime, fill prices) |
| §7 tripwire 1 (+1 delay, both arms, NZDUSD+USDCAD) | `ShDelayBars` shifts decision close (:152), boundary reset (:330), arm validity close (:378–381); Xen.cs:67–68 range-guarded 0/1; confs R-delay1/G-delay1 `--ShDelayBars=1`, SYMBOLS=(NZDUSD USDCAD) | MATCHES | See note 1 on the design's internal "+2 vs 4" count |
| §7 tripwire 2 (param provenance) | Rerun executed by QA (below) | MATCHES | BYTE_DIFF_CLEAN + all conf values match CSV `repr()` exactly |
| §4 b_w = 0.25·σ12/1e4, g = σ12, from EXP-019 artifacts only | derive_exp020_params.py:69–99 (reads only EXP-019 `legs_live.parquet` + `costs.csv`; deterministic) | MATCHES | Candidate-blind; no tuning grid |
| §5 fence = EXP-019 AnalysisEndUtc per instrument, TRAIN only | All 6 confs' ANALYSIS_END/BACKTEST_END blocks byte-identical to EXP-019.conf (verified per-conf, incl. delay confs' NZDUSD/USDCAD rows); `HoldoutFence.ShouldStopBeforeProcessing` per bar (:125, :302) | MATCHES | |
| §5 runs: 16 R + 16 R-twin + 16 G + 16 G-invert + 4 delay = 68 cells | 6 confs, symbol counts 16/16/16/16/2/2; STRATEGY_VALUE 7/8 match enum positions (Xen.cs:24–39) | MATCHES | |
| §5 sizing fixed, no compounding | ARM G min volume (:280); ARM R fixed u0 sized for band granularity (:113–119), sub-min-vol trades skipped + logged `min_vol_skip` (:163–166) | MATCHES | Disclosure event present |
| run_metadata provenance | Xen.cs:712–737 (arm, band_w/grid_bps, delay, trigger/unwind strings) | MATCHES | Unwind string encodes the twin clarification |

### Golden-trace diff (§10 feasibility — expected values from design; none computed from implementation)

- **T1 (ARM R, NZDUSD first rebalance):** feasible. Per-bar `PortWeight/PortUnits/PortCash` + OHLC let QA rebuild w drift from the 50/50 init; first bar with |w−0.5| ≥ b_w (conf: 0.0015159458982731892) must be followed by a trade_blotter row at the next open with PositionDelta = restoring amount. Columns suffice.
- **T2 (ARM G, USDCAD first k=1 round trip):** feasible. Anchor emitted per bar (`SignalValue`) and at `grid_anchor_reset` events; cis_trades rows carry EntryFillPrice, ExitFillPrice, EntryAnchorPrice, FixedExitPrice (=unwind), LadderLevel, Direction, EntryTime/ExitTime → QA checks entry = A−g, unwind = A, m1 Low/High touch against timebars data, RealizedBps ≈ +g gross. Columns suffice.
- **T3 (cap):** feasible. `cap_skip` events (value = k·dir) + per-bar OpenLegs. Columns suffice.

### Governance & boundary

- [x] Mandatory declaration blocks present in design.md: MECHANISM/DERIVED (§1), OBJECT-IDENTITY (§2), CONTROL proofs ×3 with B-1/B-5/B-6/B-2 (§6), TRIPWIRE (§7), POWER (§8), BANDS (§9), GOLDEN-TRACE (§10), hard/informative split (§7).
- [x] Tripwire 2 executed by QA: `python/.venv/bin/python code/derive_exp020_params.py` rerun → `results/exp020_params.csv` **byte-diff clean**; every `--ShBandW`/`--ShGridBps` value in all 6 confs matches the CSV at full float precision (scripted check, 0 mismatches, 68 param entries).
- [x] `check_no_local_accounting("python/experiments/EXP-020/code")` → `{'ok': True, 'banned_defs_found': []}`.
- [x] No Python strategy backtest: EXP-020 code dir contains only the param-derivation script (reads EXP-019 result artifacts, no price-path simulation).
- [x] Registry: CF-VOLHARV-001 registered (`docs/signal-registry/candidate-families/cf-volharv-001.md`); gate lifted per checkpoint-007; checkpoint-008 dir exists. Counted TEST reads: 0 (TRAIN only) — consistent.
- [x] Holdout: fence asserted at start (explicit AnalysisEndUtc required, :65–66); `ShouldStopBeforeProcessing` before any bar processing in both arms; conf fences identical to EXP-019 lineage. No code path loads post-fence data.
- [x] Shared-code boundary: SignalRecords/writer changes are strictly additive — 3 new trailing columns `PortWeight/PortUnits/PortCash` with `double.NaN` defaults; all other models' emissions unchanged (positional record fields appended last; writer appends columns 39–41). Verified via git diff.
- [x] Domain guard: 4h-only assert (:62–64); delay param range-guarded 0/1.
- [x] Build: `dotnet build Xen.csproj -c Debug` → 0 errors (QA rerun).
- [x] Smoke/estimand validation correctly deferred to post-gate (execution is operator-gated); README names the exact first-action command.
- [x] Elicitation hygiene: open items (spread pin, D2 ratification) stated plainly.

**Developer deviations judged:**
- **D1 conf packaging (6 multi-symbol confs, not 68 single-symbol):** ACCEPTED — follows the operator-approved EXP-019 D6 precedent, same 68 cells, one family root per arm which is what `xen.estimand_validation` wants. No semantic content.
- **D2 pre-implementation dated design clarifications (T2 unwind arithmetic; inverted-twin stop entries + unwind-one-level-AWAY):** ACCEPTED pending operator ratification at the execution gate (as the developer already flags). Both are dated in design.md §3 before implementation, resolve genuine ambiguity rather than change the estimand, and the twin construction is the only non-degenerate mirror satisfying control B-6 (limit entries with unwind-away would be degenerate; unwind-toward would duplicate the MR grid). Correctly recorded in the model-file DEVIATIONS block and README.

### Issues

1. **INFORMATIVE (design typo, quant-designer):** design §5 Runs row says "(+2 delay twins §7)" but §7 (both arms × NZDUSD+USDCAD) and §11.2 ("4 delay-twin confs") give 4; the implementation runs 4 (68 cells total). Recommend a one-line design fix at the gate; no code change.
2. **MINOR (ARM R sell path, Xen.StructureHarvest.cs:180–193):** a sell rebalance closes only the first label-matched position, `closeVol = min(vol, position volume)`. Once inventory is split across multiple positions (init + later buy fills create separate positions in a hedging backtest), a large sell may execute partially in that bar; the band check re-triggers on subsequent bars so w converges over 1–2 bars. The ledger books the ACTUAL fill (accounting stays exact; the emitted path is the estimand), and any bias is against the hypothesis (slightly fewer perfect crossings). Not verdict-material; disclose in the report. Optional hardening: loop over all label-matched positions.
3. **INFORMATIVE:** (a) band trigger uses ≥ (boundary-inclusive) vs design's "outside" — measure-zero; (b) `arm_skip_breach` placement-validity skip is an implementation-added broker-constraint guard, event-logged and symmetric across MR/twin — acceptable, should be counted in the analysis disclosure.
4. **CARRIED BLOCKER (not a QA failure):** live-session spread re-snapshot still outstanding (operator, Monday) and EURJPY weekend spread UNPINNED — execution/emission may proceed on TRAIN; binding net reads remain blocked by design (`xen.evaluation` raises).

---

## Post-run-1 addendum (orchestrator, 2026-07-05)

QA run-1 findings actioned before the execution gate:
- Finding 1 (design §5 "+2 delay twins" typo) — fixed to "+4 delay twins (NZDUSD/USDCAD × both arms)".
- Finding 2 (ARM R sell closes only first position) — hardened: sell now iterates ALL label-matched
  positions until the target volume is exhausted (`Xen.StructureHarvest.cs`, "QA run-1 M2" comment);
  ledger unchanged (books actual fills). `dotnet build` green.
Both changes are within the reviewed design semantics; operator may order a QA re-run at the gate.
