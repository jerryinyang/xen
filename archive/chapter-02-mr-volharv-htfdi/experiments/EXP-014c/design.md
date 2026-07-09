# EXP-014c — CF-MR-004/HYP-004: lean bracket exit-set (trade the measured two-barrier object)

**Family:** CF-MR-004 (REGISTERED, HYP-004 recorded) · **Phase:** 004 · **Type:** tradability screen,
TRAIN. **Classification:** **PRICE-PRIMARY** (native cTrader orders, m1 fills; L-01/P-09).
**Slots/reads:** 0 candidate slots, **0 counted TEST reads** · **Holdout:** final-30% sealed;
fence = EXP-013 first-49% TRAIN cutoffs verbatim. Frozen 4h referee — never tuned (L-12).
**Origin:** `checkpoints/2026-07-01-004-cross-domain-mr-renewal/amendment-004-lean-bracket-redesign.md`
(operator-locked change-set, incl. the 2026-07-03 pushback: exit rules decomposed as variants vs the
faithful baseline; reentry + z\* axes retained). Availability is **not** re-run — EXP-014b
`mr_characterisation.json` stands (symmetry two-barrier, audited, re-derived exactly).

**P-02 gate note (explicit).** This is *not* exit-tuning on a dead entry. The entry's information is
availability-**confirmed** (collapse-verified vs the peer-feed phase-shift) at 4h JP225 (p_inward
0.696, ci_low 0.638; replicated at z1.5) and weakly 4h EURUSD; EXP-014b showed the traded exits were
a *different object* than the measured one (moving target = loss engine). HYP-004 aligns the traded
object with the measured object once, decomposed, with the same frozen referee — then the family
retires if it fails.

## 1. Falsifiable question

*On S8 at 4h, does the exit-set that reproduces the measured two-barrier race — TP frozen at the
entry-time anchor, SL at the symmetric outward barrier, time-stop ⌈3·HL⌉ — extract a net-positive
per-stratum edge under the frozen referee on the availability-confirmed cells (JP225, EURUSD),
and which of the three rules (frozen target / outward stop / time-stop) moves the outcome, across
reentry and z\* characterisation axes? If it fails powered and non-vacuous, the CF-MR-004
fixed-parameter thesis retires.*

## 2. Scope

| Field | Value |
|---|---|
| Series | S8_RVINDEX only (basket−Median₉₀, W=90; WZ=200) — identical construction/constants to EXP-014b. |
| Cells | 11: FX {EURUSD,GBPUSD,USDJPY,USDCHF,USDCAD,AUDUSD,NZDUSD}, IDX {USTEC,US500,US2000,JP225}; same basket mates + min-mate rule. |
| Domain | **4h only** (1h retired — EXP-014b: basket dilutes own-price MR; every 1h raw pass leaked). m1 fill resolution. |
| Entry | Unchanged from EXP-014b: resting band limits at exp(anchorLog ± z\*·σ) armed from ≤t-1 confirmed bars; breach-skip; refresh-R. Keeps E1-E3 comparable with the reused E0 baseline. |
| Time range | Full 5y; `AnalysisEndUtc` = EXP-013 first-49% cutoffs verbatim. Final-30% never loaded. |
| Exclusions | 1h/15m/5m/1D; both-leg (tail-failure settled 014b); S recalc arm; no availability re-run; no counted TEST read; no holdout. |

## 3. Configuration matrix

| Axis | Values | Notes |
|---|---|---|
| **EXIT (new object)** | **E0** moving-mean baseline — **reused EXP-014b 4h single-leg emissions** (form-1 + refreshing form-2; no new runs). **E1** TP frozen at the entry-time anchor `a_entry` per leg, set at fill, never modified; no SL, no time-stop, **form-1 disabled**. **E2** = E1 + SL frozen at the outward barrier `o ± D` (o = entry fill, D = \|o − a_entry\|, opposite side to the TP). **E3** = E2 + hard time-stop ⌈3·HL_entry⌉ domain bars (cap 48) → market exit at next bar open. | E3 = the exact object the availability read measured. |
| Reentry | none / allow / extend (R refresh; ladder {z\*, z\*+0.5, z\*+1.0} for extend) | characterisation |
| z\* | 2.0 / 1.5 | characterisation |
| Cells | 11 | per-cell strata |

New emissions = 3 exits (E1-E3) × 3 reentry × 2 z\* = 18 confs × 11 cells = **198 native 4h runs**,
+ **PRIMARY phase-shift twin** (1 conf, 11 runs). E0 = 6 existing 014b conf-families (4h
none/allow/extend × z20/z15), loaded read-only.

**Binding PRIMARY = (none, z\*=2.0, E3) on JP225 and EURUSD** (prespecified from 014b
collapse-verified availability — the selection-bias defense: all 11 cells still emitted and
Holm-adjudicated; the two primaries are named *before* any 014c data exists). Everything else —
E1/E2, reentry≠none, z15, non-primary cells — is disclosure/characterisation. A disclosure admit
that matters becomes a follow-up primary with its own multiplicity booking (never promoted in-run).

## 4. Tradability adjudication (frozen, identical seam to EXP-014b)

Per (cell, exit, reentry, z\*): engine-realized per-bar NET series (`assemble_realized_bps`:
open-to-open, entry/exit fills substituted, intra-position MTM L-09, frozen per-instrument 4h RT
cost once per entry L-02) → frozen `referee_pstar.gate_stack_pstar` (domain=4h, q\*=0.75,
min_state=8, min_effective_n per DOMAIN_SPECS). `powered` = referee l1 AND episodes ≥ 8.
**Cross-cell Holm over the 11 cells within each (exit, reentry, z\*) family** (each family booked
separately; the binding family is (E3, none, z2.0)). Per-stratum binding verdicts (L-03); pooled
figures disclosure-only. Statuses use the **post-C1 label logic** (audited EXP-014b
`cell_status`): NOT_TRADABLE only when powered AND bite-non-vacuous; per-cell tripwire verdicts;
absent binding control ⇒ UNVERIFIED, never a pass (L-01).

## 5. Leak tripwire (binding) + bite

- **Peer-feed phase-shift** (`BasketPhaseShiftHours=60`): twin runs of the PRIMARY conf
  (E3/none/z20, 11 cells). Binding on any Holm-admitting cell: its **own** shift net must collapse
  (per-cell, C1b discipline). Survival ⇒ REJECT_LEAK for that stratum. Shift twins for admitting
  *disclosure* arms generated on demand (Stage 4) before any such arm could be promoted.
- **Bite-check** per admitting cell: +8 bps/active-bar plant must pass the frozen referee
  (non-vacuity); fail ⇒ that cell cannot clear the leak gate (and negative reads in bite-blind
  cells are labeled UNPOWERED_TRADABILITY, not NOT_TRADABLE).

## 6. Analysis plan (methods; simplest-sufficient)

| # | Question | Method | Why sufficient |
|---|---|---|---|
| M1 | Net edge per stratum? | Frozen referee (bootstrap ci_low, block seed frozen) + Holm over 11 cells per family | The programme's binding instrument; untuned (L-12) |
| M2 | Which exit rule moves the outcome? | **Attribution table** E0→E1→E2→E3 per (cell, none, z20): net/gross mean bps, ci_low, episodes, exit-reason mix, MAE/MFE. Paired deltas descriptive only (different fills ⇒ different trades; no significance claimed) | Descriptive decomposition answers the design question without new inference machinery |
| M3 | Does E3 trading reproduce the measured availability? | Consistency check: per primary cell, share of decided E3 legs (tp/sl only) exiting at TP vs `p_inward` from 014b (JP225 0.696 / EURUSD 0.589); binomial CI overlap, disclosure | Direct one-line validation that the traded object = measured object |
| M4 | Session structure? | **All cells**: histogram of entry + exit hours (server time) and per-hour decided-leg P&L for E3 legs — full session characterisation, not just a flag. Binding-adjacent read on JP225: >50% of decided P&L in a 4-bar session window ⇒ session-artifact flag | The Asia-vs-US structure risk is strongest for JP225 but session clustering informs every cell's mechanism |
| M4b | Same-bar TP+SL races | Count legs where both frozen barriers lie inside one bar's [Low,High]; disclose their m1-resolved outcome split (TP-first vs SL-first) and compare with the availability read's ambiguous rate (~0). The engine resolves them on the real m1 path — they are **kept, never dropped** (the analysis-side drop was a measurement necessity, not a trading rule) | The m1 path is strictly more information than the domain-bar race; disclosure quantifies how much the ambiguity mattered |
| M5 | Where does P&L live? | Per-exit-reason split (tp_anchor / sl_outward / time_stop / open_at_end): n, mean bps, bars held; censored survival disclosed | Mirrors the 014b forensic lens that exposed the moving-mean loss engine |
| M6 | Regime dependence? | with-trend / vol_low slices of E3 leg P&L (entry-time conditioners, emitted per bar) — informative only, never gates | 014b found the strongest availability pockets there |

Zero-baseline behavior: cells with 0 completed round-trips report episodes=0 → UNPOWERED (never
FAIL); denominators = active bars (referee) and completed legs (per-reason splits), stated per
table. NaN RealizedBps (censored) excluded from realized stats, disclosed as counts.

## 7. Power / multiplicity

- Frozen 4h floor: min_state=8 episodes; l1 effective-n floor governs (L-12). Expected episodes
  (from 014b none/z20 4h fills): ~40-60 entries per FX cell, ~60-270 per IDX cell → E3's time-stop
  increases completed round-trips vs E0 (no indefinite holds) — power should improve.
- Families: 24 (exit×reentry×z\*) × 11 cells; each family Holm-corrected internally; only the
  (E3,none,z20) family is binding. Cross-family comparisons are disclosure (attribution), never
  admission. z15/reentry/E1/E2 admits do not create claims — they route to follow-up primaries.
- UNPOWERED never FAIL (per-stratum labels per post-C1 logic).

## 8. Cost (binding, L-02)

Frozen per-instrument per-domain `cost_bps` (referee map) once per completed round-trip;
disclosure {0.5,1,2}× sensitivity on the primaries only.

## 9. Emission

Reuse the EXP-014b schema (SignalPositionRecord + cis_trades). New/changed per-leg fields:
`FixedExitPrice` = frozen TP (E1-E3), `SlPrice` (E2-E3; add column or reuse an existing slot —
developer's choice, documented), `HorizonBars` = ⌈3·HL_entry⌉ (E3). **ExitReason values:**
`tp_anchor` / `sl_outward` / `time_stop` / `open_at_end`. All decision inputs ≤ t-1; fills m1;
`CloseTime`/`SourceCloseTime` alignment; forming bar never read; `HoldoutFence.AssertCanEmit` on
every row.

## 10. Interpretation criteria (frozen before outcome contact)

| Outcome | Condition |
|---|---|
| **Tradable-on-TRAIN** (per primary cell) | (E3,none,z20) JP225 or EURUSD: referee net ci_low>0 (Holm/11) AND own-cell shift net collapses AND bite passes → **operator-gated counted TEST read**. |
| **Credible negative → RETIRE thesis** | Both primaries powered + bite-non-vacuous and net fails → availability is real but not extractable by the measurement-matched bracket → retire CF-MR-004 fixed-parameter thesis (family had its best shot). |
| **REJECT_LEAK** | An admitting cell's own shift net survives. |
| **UNPOWERED** | Episodes<8 or bite-blind on the primaries → no verdict; report why (fill starvation vs censoring). |
| **Attribution reads (disclosure)** | E0→E1 isolates frozen-vs-moving target; E1→E2 the outward stop; E2→E3 the time-stop; reentry×exit crosses test whether extend's own-price harvest persists with a frozen TP (per-cell shift behavior). M3 consistency: E3 TP-share ≈ p_inward supports "traded=measured"; large deviation → execution slippage vs the race (report where: same-bar TP+SL races, gap-throughs). |
| **Session artifact (JP225)** | M4 concentration flag → JP225's availability may be session-structural; downgrade any JP225 admit to UNVERIFIED pending a session-controlled follow-up (no in-run gate change). |

## 11. Complexity budget

Tests: frozen referee + Holm + phase-shift + bite = 4 (all existing machinery). Plots ≤5:
attribution net/gross per cell (E0-E3); exit-reason P&L split; E3 TP-share vs p_inward; JP225
session histogram; primary-cell net vs gross. Code: C# = one new exit block (frozen TP/SL/horizon
per leg + ExitReason values; form-1 bypass for E1-E3) + conf generator; Python = reuse EXP-014b
lib (post-C1/C2) with an exit-axis dimension + attribution/consistency tables. Within envelope.

## 12. Implementation safety (for experiment-developer)

- **Per-leg frozen state at fill:** on each entry fill capture `o` (fill price), `a_entry`
  (= exp(anchorLog) of the arm bar, ≤t-1), `D=|o−a_entry|`, `HL_entry` (≤t-1 bracket Hl),
  `HorizonBars=min(48,⌈3·HL_entry⌉)`. TP/SL placed as native orders (TP limit at `a_entry`, SL
  stop at `o±D` outward) **immediately on fill and never modified** (no refresh path may touch
  E1-E3 legs). Time-stop: at each completed bar, legs with `barsHeld ≥ HorizonBars` → market close
  (exit at next open), reason `time_stop`.
- **Same-bar fills are REQUIRED, not a defect:** TP/SL attach at the entry fill tick (native
  SL/TP on the position or orders placed in the same event handler), so a leg may enter AND exit
  within one domain bar on the m1 path. Do **not** introduce any artificial next-bar activation
  lag — live orders rest from the first tick and the backtest must mirror that. Same-bar TP+SL
  races are resolved by the engine's m1 sequence and disclosed (M4b), never suppressed.
- **No moving targets in E1-E3:** `RefreshForm2Targets` and `ApplyEventExits` (form-1) must be
  fully bypassed for these arms — assert per run that no E1/E2 leg ever emits
  `form1_reversion`/`form2_favorable_limit`.
- **E1 open-ended holds:** no SL/time-stop ⇒ legs may survive to the fence → censored
  `open_at_end` (RealizedBps NaN, disclosed). Expect higher censoring; do not "fix" it.
- **Reentry interplay:** `none` = no new arm while any leg open (unchanged); `extend` ladder legs
  each carry their own frozen (o, D, HL) bracket.
- **Causality:** all decisions from completed bars (`Count-2`), fills next bar via m1; ≤ t-1
  inputs for arming; forming-bar OHLC never read; open-to-open conventions unchanged.
- **Determinism/perf:** streaming O(1) per bar; bounded buffers; append-only parquet; frozen seeds
  in Python; no perf shortcut may alter sample membership, denominators, or temporal alignment.
- **E0 reuse:** analysis loads `EXP-014b-4h-s8-{none,allow,extend}-{z20,z15}` read-only; never
  rewrite or re-emit those dirs.

## GATE: APPROVE (orchestrator inline pre-exec, 2026-07-03)

**Single question ✓** — does the measurement-matched bracket extract the confirmed 4h availability;
the exit decomposition + reentry/z\* axes are characterisation of that one question, predeclared
disclosure (no compound claims; a disclosure admit routes to a follow-up primary, §3/§7).
**Scope/boundaries ✓** — 4h only, S8 only, single-leg, 11 cells; E0 reuse read-only; exclusions
explicit; 209 new native runs, operator-approved breadth (2026-07-03).
**Registry precondition ✓** — CF-MR-004 REGISTERED, HYP-004 recorded pre-execution; 0 slots,
0 counted TEST reads; no TEST-stratum read.
**Pitfalls ✓** — P-02 addressed head-on (§P-02 gate note): entry availability is collapse-verified,
so this is object-alignment, not exit-rescue of a dead entry; P-09/L-01 honored (price-primary,
native engine, analysis-only Python on emissions).
**Leak tripwire ✓** — peer-feed phase-shift twin binding per-cell on admits (C1b discipline);
bite-check per admitting cell; absent control ⇒ UNVERIFIED (never a pass).
**Methods ✓** — frozen referee + Holm (untuned, L-12); attribution/consistency/session reads are
descriptive, non-parametric, denominators stated, zero-baseline (UNPOWERED never FAIL, post-C1
labels). Real prices, m1 fills, timestamp alignment, open-to-open.
**Holdout ✓** — EXP-013 first-49% cutoffs verbatim; final-30% sealed.
**Same-bar fills pinned ✓** — TP/SL attach at the entry fill tick, no artificial t+1 lag; same-bar
races engine-resolved and disclosed (M4b) — matches live order mechanics.
**Budget ✓** — 4 tests (existing machinery), ≤5 plots + session/attribution tables, one C# exit
block + conf generator + lib exit-axis extension.

**Status:** READY for Stage 2 (Implement). Credentialed cTrader-CLI launch (209 runs) remains
operator-gated at Stage 3.
