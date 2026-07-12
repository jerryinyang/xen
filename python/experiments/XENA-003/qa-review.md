# XENA-003 — QA Review (append-only)

## QA run 1 — design review — 2026-07-11 — mode: subagent — HEAD ae5a2bf (dirty: xena-runs.md, pipeline-config, INDEX files, xena-lane.md; XENA-003/ contains design.md only)

**Scope:** DESIGN-stage pre-exec review (no implementation exists — correct precondition;
same pattern as XENA-001 run 3 / XENA-002 run 1). Design-fidelity trace is design-vs-spec
(checkpoint 011 / cf-mtfctx-001 / proposal CTRL-03 / design-requirements), not design-vs-code.
A second QA run is required post-implementation before execution sign-off.

**Verdict: APPROVE** (design stage). No REVISE items. Informative notes below.

### Clause trace — checkpoint-011 mandatory blocks

| Clause | Design § | Verdict | Notes |
|---|---|---|---|
| L-21 unit pin (ATR units, cost_bps, money_per_unit per instrument) | §4 table | MATCHES | Identical to approved XENA-001/002 pins; TRAIN-only FX medians (file start → 2024-03-28, no gate contact); JP225 contract_size=10 disclosed; spread = operator pin pre-gate, correctly declared BLOCKING for NET leg only |
| Band pin (exact boundaries, common span, per-instrument fences, pre-registered) | §5 | MATCHES | Byte-identical to XENA-001/002: span 2021-06-02T00:01Z → 2024-12-11T08:19Z (GER40 binding), 50/30/20 table declared binding (no from_span re-run), all 12 holdout fences listed, uniform AnalysisEndUtc |
| Vol-regime pin (median-TR ATR(14), window in [200,300], hysteresis) | §3 pins | MATCHES | Window 250 (matches 001/002 for comparability); HIGH >P80/<P65, LOW <P20/>P35, MID otherwise; pinned before search |
| Feature causality (confirmed HTF bars ≤ t−1, CloseTime alignment) | §3 pins | MATCHES | Filters re-evaluated at LTF bar open on confirmed bars; CloseTime alignment, never bar indices; warmup suppresses undefined features (264 HTF bars for vol) |
| Sizing stop k pinned, sizing-only, finite | §3 pins | MATCHES | SlPrice = EntryFill ∓ 2× HTF median-TR ATR(14), k=2 (same as 001/002); NO live stop orders; finite or candidate-gate REJECT |
| CTRL-03 profit-exit spec (≥0.5× CURRENT HTF median-TR ATR, floats, no adverse target) | §3 Exit 2 | MATCHES | Close[t−1] in profit AND distance ≥ 0.5× ATR at latest confirmed HTF bar at time t → market exit at bar t open; explicitly "floats with current ATR, never frozen at entry" (L-14 moving-target rule honoured); evaluate-at-open convention correctly applied to the family's "at any LTF bar close" wording |
| From-scratch clause | §3 Model row | MATCHES | Entry/model logic from scratch; HTF feature code may be spec-identical per XENA-002 Amendment 2 operator decision — correctly scoped, QA spec-equivalence check flagged for run 2 |
| CTRL-01 seed pin | — | N/A | No RNG in CTRL-03; L-19 addressed structurally (§1 KB check) |

### Clause trace — design-requirements mandatory blocks

| Block | Design § | Verdict | Notes |
|---|---|---|---|
| 1 Mechanism + DERIVED | §1 | MATCHES | Reversion mechanism, cadence, P&L object (round-trip leg) stated; estimand/null/horizon/test each derived from the mechanism, not reused blind (horizon grid + profit exit tied to reversion-capture hypothesis) |
| 2 Object identity (B-8/B-4/B-9) | §2 | MATCHES | B-4 handled precisely: capital commits at the LIMIT FILL; filters mask placement; emission records the actual fill — the CF-MR-004 seam closed by trading the measured object natively |
| 3 Control validity proofs | §7 | MATCHES | Two controls, all fields (question/population-disjoint/bite-MDE/non-vacuity/expected/disclosure). WS-6 battery power curve as MDE; XENA-001 as live-data null anchor (different fill mechanism disclosed) |
| 4 Leak tripwire + vacuity | §7 | MATCHES | Entry-time block rotation (alignment destroy, never P&L permute — L-14 mean-invariance); vacuity check states the statistic moved (portfolio F̂/P25 via composition+alignment); survive = HARD STOP. Plus EXP-013-specific native-fill physicality tripwire (≥50 fills/symbol×domain vs raw m1) — appropriate addition for the hardest execution contract |
| 5 Interpretation bands | §8 | MATCHES | Run-level bands (XENA-lane form, per 001/002 precedent); no auto-verdicts; POOLED disclosure-only; EXIT-MIX read added (mechanism-appropriate) |
| 6 Power | §9 | MATCHES | Per-domain fill-count estimates ≫ 60-trade battery density; order-of-magnitude caveat + empirical cadence disclosed at analysis; 1d vol-variant warmup loss disclosed |
| 7 Golden trace | §10 | MATCHES | Recipe only, QA derives, developer must NOT generate; deterministic (no RNG); residual fill discrepancies routed to physicality tripwire, not silent acceptance |
| 8 Hard/informative split | §7 | MATCHES | Hard = integrity-only (estimand gate, SlPrice, holdout, registry hash, permutation alarm, physicality, operator approval); all value reads informative |
| 9 CONVERSION-PIN (L-21 screen seam) | — | N/A | No SPDR/screen money-unit conversion cited as a target; P-14 bps figures are prior-evidence context only; unit pins handled in §4 (same treatment approved in 001/002) |
| 10 Spread verdict leg (L-22) | §4 | MATCHES | Spread pin blocking for NET/deployability; any deployability claim cites net_informational; passive-limit spread-earn NOT credited (conservative, disclosed) |
| 11 Amendment ledger (L-23) | §11 | MATCHES | Empty ledger 0L/0T/0N; XENA-001/002 QA-derived pins correctly inherited as design content, not amendments |
| 12 Battery/null rules (L-24) | §7 | MATCHES | Nulls exit-matched by construction (permutations act on real emitted streams incl. both exits); no per-candidate eligibility (XENA principle); read floors portfolio-level (battery power curve); collapse expectation stated, final numeric threshold from XENA-001 null level (derived, not asserted) |

### Clause trace — family binding constraints (cf-mtfctx-001) + XENA lane

| Constraint | Design § | Verdict | Notes |
|---|---|---|---|
| Native cTrader limit orders + m1 fills (EXP-013 carve-out) | §1, §3, §13 | MATCHES | Engine-native fills, no OHLC self-adjudication, no model-side fill simulation; native-order mode in batch runner; physicality audit pre-search |
| Finite SlPrice every leg | §3, §7 | MATCHES | gate_universe REJECT clause |
| Frozen registry v3 cited, never re-derived | header, §6 | MATCHES | sha256 537d691a…e672a6 matches xena-lane.md active pin; X=0.70 / F_floor=0.4302 / gate=0.0558 match v3; verify_frozen_registry at ingest; registry_path mandatory to certify_and_rank/run_final_gate |
| Bands = common analysis span, holdout untouched | §5 | MATCHES | Final 30% never touched; TEST gate ends at common 70% cutoff; folds (4, purge 14d) inside ranking band, disjoint from search band |
| Manifest arithmetic 19 × 4 × 3 × 12 = 2,736 | §3 | MATCHES | Variant count 1+2+1+3+6+6=19 (typo-corrected 6s per locked decision); hold grids {12,24,48,96}/{8,16,32,64}/{6,12,24,48} match true-HTF-span arithmetic (corrected slip) |
| No per-candidate quality gates | §3 header | MATCHES | "every cell enters"; candidate gate is integrity-only (SlPrice) |
| Gate ledger / attestation | §12 | MATCHES | 0/2 slots; no default spend; new_data_attestation operator-only; ledger row registered 2026-07-11 (verified: docs/signal-registry/xena-runs.md line 26, DESIGNED, bands + hash pinned) |
| No threshold re-derivation | §8 GATE band | MATCHES | fail = negative, no revision (L-23), no re-search on gate segments |

### L-14 exit-set diff (proposal `.ignore/temp/new-referee/mtf.md` CTRL-03 vs design)

| Proposal-named exit | Design | Verdict |
|---|---|---|
| Fixed hold-period ({0.5,1,2,4}× HTF span in LTF bars) | §3 Exit 1: market at open of fill_bar + hold | MATCHES |
| First close in profit beyond 0.5× HTF ATR from entry (no adverse target) | §3 Exit 2: floating, current-ATR, whichever-first | MATCHES |
| — (no third exit) | Design exit set = exactly these two; "no adverse target; no live stop" explicit | MATCHES — no silent drop, no substitution |
| Trailing re-quote pre-fill ("reset to the new limit price") | §3 Quoting: re-priced every LTF bar open to new 3-bar extreme; ignore signals while holding; cancel opposite side on fill | MATCHES (proposal quoted verbatim) |

### Golden-trace check (design-stage)

Recipe §10 hand-derivable from §3 pins alone (aggregation → confirmed-bar walk → two-sided
quotes → m1 first-touch → whichever-first exit → SlPrice); expected values will come from
this design at run 2, never from the implementation. PASS as a specification.

### Issues

1. **INFO (no fix required in this design):** `_pipeline-config.md` §XENA Lane cites stale
   registry values (F_floor=0.1811, gate=0.0046) vs the active v3 pin (0.4302 / 0.0558) in
   `docs/references/xena-lane.md`. XENA-003 correctly cites v3. Doc-drift outside this
   experiment; flag to operator for cleanup.
2. **INFO:** Golden trace step (3) hand-models the engine's gap-through fill (m1 Open) while
   §3 declares engine intrabar behaviour "disclosed, not re-implemented" — acceptable since
   §10 explicitly routes residual engine-vs-hand fill discrepancies to the physicality
   tripwire rather than silent acceptance; run-2 QA must apply that routing.
3. **OPEN PRECONDITION (correctly declared, not a defect):** index spread pins are
   "OPERATOR PIN REQUIRED pre-gate" — blocking for the final-gate NET leg and any
   deployability read only; emission/search/certification unaffected (all gross).

### Required before execution

- Implementation (MtfCtxReversion model, native-order harness, conf, manifest) → QA run 2
  (post-implementation fidelity trace + golden-trace diff vs emission + spec-equivalence
  check on shared HTF feature code per XENA-002 Amendment 2).
- Operator execution approval (and XENA-001/002 sequencing per checkpoint 011).

## QA run 2 — post-implementation review — 2026-07-11 — 2026-07-11T15:12Z — mode: subagent — HEAD ae5a2bf (dirty: Xen.cs, pipeline-config, INDEX/lane/ledger docs; untracked: MtfCtxReversionModel.cs, Xen.NativeReversion.cs, XENA-003.conf, gen_xena003_manifest.py, XENA-003/)

**Scope:** POST-IMPLEMENTATION design-to-code fidelity review (fresh context — this
session did not produce the implementation). Golden trace derived independently from
design §3/§10 pins against raw m1 parquet; developer's clause→code map verified, not
trusted.

**Verdict: APPROVE** — ready for the operator's execution gate. No REVISE items.
Informative notes 1–5 below; note 3 routes to the §7 native-fill physicality tripwire
(pre-search HARD gate), per design §10's explicit routing.

### Design-fidelity trace (design §3 pins → code)

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §3 two-sided trailing quotes at min(Low)/max(High) of last 3 CONFIRMED LTF bars, re-priced every bar open, while flat only | MtfCtxReversionModel.cs:258-317 (`_ltfWindow` maxlen 3 of completed bars; `rangeLow`/`rangeHigh`; quotes only when `flat`) | MATCHES | Window holds bars t−3..t−1 only (enqueued on completion); `ExtremeLookback=3` (line 74) |
| §3 Amendment 1 crossed-limit rule (passive-only: buy strictly < Bid, sell strictly > Ask at refresh; crossed side does not rest; no market conversion) | MtfCtxReversionModel.cs:303-305 (`rangeLow < bid` / `rangeHigh > ask`); Xen.NativeReversion.cs:85-88 (rejected order simply absent, re-quote next bar) | MATCHES | Strict inequalities; bid/ask sampled at the first m1 of the forming bar = quote refresh |
| §3 per-side filter masking; resting order cancelled on mask-off; DI masks by side, ADX/vol both sides | MtfCtxReversionModel.cs:303-317 (`VariantAllows(v, side)`; masked side → null → `SyncQuote` cancels); Xen.NativeReversion.cs:61-69 (null cancels) | MATCHES | V00–V18 map verified against family spec (lines 378-404); combo order (LOW,<25)…(HIGH,≥25); V13–V18 add `DiAllows` |
| §3 filters on confirmed HTF bars ≤ t−1, CloseTime alignment, never bar indices | MtfCtxReversionModel.cs:239-247 (bucket key `(closeSeconds−1)/(htfMinutes·60)`; features updated only when a bucket COMPLETES, before decisions) | MATCHES | Identical bucket-roll convention to XENA-002 |
| §3 engine-native fills; no self-adjudication; one position at a time; opposite side cancelled on fill; no quoting while holding | Xen.NativeReversion.cs:79-88 (`PlaceLimitOrder`), 218-230 (`OnNativePositionOpened` → `Forget` + `CancelSide(-side)` → `OnEntryFilled`); MtfCtxReversionModel.cs:299,316-317 (flat=false → both sides null → cancel); OnBar throws (369-371) | MATCHES | `PlaceLimitOrder(type, symbol, minVolume, price, label)` — NO SL/TP arguments on any order |
| §3 Exit 1: market at open of LTF bar fill_bar+hold | MtfCtxReversionModel.cs:197-211 (`EntryBarIndex` = forming-bar index at fill), 278-287 (`held = formingIndex − EntryBarIndex; held >= HoldBars` → market close) | MATCHES | Verified in emission: ALL 556+ hold exits have BarsHeld == 24 exactly (H1X), exit at first m1 of the bar (minute :01) |
| §3 Exit 2: floating profit exit — Close[t−1] in profit AND distance ≥ 0.5 × CURRENT HTF median-TR ATR → market at bar t open; never entry-frozen (L-14); no adverse target | MtfCtxReversionModel.cs:281,288-294 (`profitDist = dir·(bar.Close − EntryFill)`; `profitDist > 0 && profitDist >= 0.5·_medAtr`; `_medAtr` = live field updated on every completed HTF bucket) | MATCHES | `_medAtr` is the model-level field, re-computed per HTF bar — floats, not captured at entry (anchor-drift failure shape checked: absent). Emission: all profit exits BarsHeld < 24 and RealizedBps > 0 |
| §3 warmup: quoting suppressed until features defined | MtfCtxReversionModel.cs:301 (`haveWindow && _medAtrReady`); variant features self-gate via `_adxReady`/`_volReady` (383-399); Warmup grid flag = `!_medAtrReady` (256) | MATCHES | medATR ready after 15 HTF bars (~15 trading days on 1d) — matches task-stated warmup |
| §3 SlPrice = EntryFill ∓ 2×ArmedAtr, finite every leg, sizing-only, NO live stops | MtfCtxReversionModel.cs:79 (k=2.0), 204 (`fillPrice − side·2·ArmedAtr`); ArmedAtr captured at the arming quote refresh (309-313), finite by the `_medAtrReady` quote gate | MATCHES | Emission: SlPrice ≡ EntryFill − Direction·2·HtfAtr exact on all 972 in-coverage trades; 0 non-finite across all 76 candidates; no StopLoss/TakeProfit anywhere in the partial |
| §5 fence + §7 censoring | Xen.NativeReversion.cs:187-191, 206-210 (fence checked at m1 AND per aggregated LTF bar, `ShouldStopBeforeProcessing`); 256-277 (`FinalizeNativeRun`: censor FIRST, then cancel/flatten with `_nativeStopping` suppressing event booking); MtfCtxReversionModel.cs:331-347 (censored leg: last mark = final bar OPEN, NaN P&L, Censored=1) | MATCHES | Smoke: max ExitTime 2024-12-10 21:01 < fence 2024-12-11T08:19; 1 censored leg, NaN P&L confirmed |
| Emission schema (positions grid + cis_trades, fills contract) | MtfCtxReversionModel.cs:560-687 | MATCHES | Schema identical shape to XENA-001/002 (EntryTime/ExitTime/Direction/fills/ExitReason/BarsHeld/RealizedBps/Censored/SlPrice/HorizonBars/Htf* context); developer's smoke `gate_universe` 76/76 blocking_pass claim consistent with independent checks here |
| §3 hold grids {12,24,48,96}/{8,16,32,64}/{6,12,24,48} | MtfCtxReversionModel.cs:158-168 (baseSpan = htf/ltf; ×{0.5,1,2,4}) | MATCHES | 60→1440, 15→240, 5→60 — the three registered pairs only; anything else throws |

### L-14 exit-set diff

Implemented exit reasons across ALL 76 smoke candidates (21,241 trades):
`{hold_period, profit_exit, censored_end}` — exactly the design's named set {Exit 1,
Exit 2} + fence censoring. No adverse target, no live stop (no SL/TP on any order; no
stop-triggered close path exists), no silent additions or drops. PASS.

### EXP-013 contract

- `OnBar` throws unconditionally (MtfCtxReversionModel.cs:369-371) — self-adjudicated
  replay impossible. PASS.
- Every entry/exit in the ledger originates from `Positions.Opened`/`Positions.Closed`
  engine events (Xen.NativeReversion.cs:161-162, 218-254); exit price from deal-history
  `ClosingPrice`. No model-side fill simulation. PASS.
- Double-book impossible: `OnExitFilled` returns when `Direction == 0` (already
  censored, MtfCtxReversionModel.cs:217-218); `_nativeStopping` set BEFORE the
  fence flatten suppresses both position events (Xen.NativeReversion.cs:220, 234,
  260); censoring precedes the engine flatten. 0 overlapping legs in 21,241 smoke
  trades. PASS.
- `FinalizeNativeRun` idempotent (`_nativeStopping` guard) — safe on OnStop fallback. PASS.

### HTF feature block — spec equivalence vs MtfCtxMomentumModel (XENA-002 Amendment 2)

`diff` of the full block (`BuildHtfBar`/`UpdateHtfFeatures`/`UpdateVolRegime`,
momentum:276-405 vs reversion:420-545) and the filter block (`VariantAllows`/`DiAllows`,
momentum:232-262 vs reversion:373-404): **byte-identical except comments**. Wilder
ADX/DI(14) threshold 25, median-TR ATR(14) (even-window middle-pair mean), 250-bar
percentile with 80/65/20/35 hysteresis, `(closeSeconds−1)/(htfMinutes·60)` bucket-roll —
all identical. Spec equivalence: PASS (strictly stronger — code equality).

### Golden-trace diff (derived by QA from design §10 pins; expected values from the design, never the implementation)

Independent hand-simulation of `C3-USTEC-1D1H-H1X-V00` written in this session from §3
pins only (m1→1h clock-aligned aggregation, 3-bar-extreme two-sided passive quotes, m1
first-touch/gap-through fills, whichever-first exits) against
`data/timebars/timebars_ustec_20210602_000000_20260621_190833.parquet`, diffed vs
`data/strategy_runs/XENA-003/c3-ustec-1d1h-h1x-v00/cis_trades.parquet`:

- **Bucket alignment + ATR:** hand-computed daily median-TR ATR values match the
  emission's `HtfAtr` exactly (143.55 / 155.35 / 158.15 / 177.00 …) — HTF bucketing and
  the feature pipeline are correct in UTC.
- **Matched events:** where the fill chains coincide the emission agrees with the hand
  trace on side, fill bar, and limit level (e.g. 2021-07-19 20:00 short: both sims,
  hand limit 14544.1 vs engine 14562.2 — the 18-pt gap traces to the engine's 3-bar
  High differing from our parquet's, i.e., feed difference, not logic).
- **Chain divergence explained:** the engine's price feed (cTrader server data) differs
  from the local parquet by a few points on some bars; a limit touched in one feed but
  not the other flips the flat/held state and desynchronises subsequent entries. This is
  exactly the "residual engine-vs-hand fill discrepancy" §10 pre-routes to the
  physicality tripwire — applied below.
- **Physicality audit (all 972 in-coverage entries, not just 2–3):** 954/972 (98.1%)
  fill prices lie inside the local m1 [Low, High] of the exact fill minute (offset 0 —
  emission timestamps are UTC-aligned to raw m1); 13 lie outside by ≤ 4.4 pts (~3 bps;
  10 sell-above-High / 3 buy-below-Low — bid/ask-basis + feed-vintage differences); 5
  fill minutes are absent from the local parquet. No fill is at a price wildly
  untouched; see note 3.
- **Exit mechanics:** hold exits all at exactly BarsHeld = 24, at the first m1 of the
  exit bar (minute :01); profit-exit condition (confirmed 1h close in profit ≥
  0.5×HtfAtr) verified against local-feed closes on 195/200 sampled events (5 misfits
  ≤ feed tolerance); entries at m1 granularity across all 60 minutes-of-hour — real
  limit fills, not bar-open self-fills.
- **SlPrice:** exact `EntryFill − Direction·2·HtfAtr` on every trade.

Golden trace verdict: **PASS** — mechanism, timing, exits, and SlPrice reproduce the
design recipe; residual per-fill price deltas are feed-level and routed per §10.

### Governance & boundary

- Frozen registry (XENA clause a): `verify_frozen_registry('python/experiments/INFR-006/results/xena_frozen_registry.json')`
  re-run this session — hash `537d691a…e672a6` verifies; X=0.70, F_floor=0.4301969674,
  gate=0.0558053579 match the design header byte-for-byte. PASS.
- SlPrice finite every leg (clause b): 0 non-finite across all 76 smoke candidates;
  full-universe `gate_universe` re-run required after full emission (already a §7 HARD
  block). PASS at smoke scope.
- Bands (clause c): conf pins uniform `AnalysisEndUtc = 2024-12-11T08:19:00Z` for all
  12 symbols; BACKTEST_END 08:20; search/ranking/gate table is design content, folds
  inside ranking band. PASS.
- `new_data_attestation` (clause d): operator-only per §12; none authored. PASS.
- Gate ledger (clause e): 0/2 slots, no default spend (§12; xena-runs.md row 26). PASS.
- `check_no_local_accounting("python/experiments/XENA-003/code")` → `{'ok': True}`. PASS.
- No Python strategy backtest anywhere in the experiment (code/ contains README only;
  the QA hand-sim above is this reviewer's scratch derivation, not experiment code). PASS.
- Conf/manifest arithmetic: manifest = 2,736 candidates (12×3×4×19, asserted);
  `MODE="3"` = `XenMode.NativeOrders` (enum ordinal verified in Xen.cs:13-22);
  `STRATEGY_VALUE="4"` = `XenStrategy.MtfCtxReversion` (ordinal verified, Xen.cs:24-31);
  cost_bps (0 / 0.28 XAUUSD / 13.0 BTCUSD) and money_per_unit pins match §4 exactly;
  registry sha256 embedded in manifest matches. Broker symbol names STOXX50/DE40 = EU50/
  GER40 per XENA-001 precedent. PASS.
- Holdout: fence enforced at m1 and LTF level; smoke max ExitTime < fence; no code path
  reads beyond `AnalysisEndUtc`. PASS.
- DEVIATIONS: none declared; the four header "interpretations" (bar-open ≙ first m1
  tick; hold-exit-before-requote; domain-pair map; medATR-ready quote gate) are faithful
  operationalisations, and the crossed-limit rule is design Amendment 1
  (operator-pinned, NEUTRAL, 0L/0T/1N — ledger consistent). PASS.
- Three shipped failure shapes: frozen-exit — absent (`_medAtr` live); anchor drift —
  absent (EntryFill fixed at engine fill; extremes correctly trail by design); confounded
  placebo — N/A (controls are the frozen battery + XENA-001 anchor, unchanged). PASS.

### Issues

1. **INFO — pre-span trades (no fix required):** the conf pins only BACKTEST_END, so the
   engine starts at broker data start; the USTEC smoke ledger contains 101/1,087 trades
   with EntryTime before the common span start 2021-06-02. Inert: the oracle excludes
   entries outside the segment (`oracle.py:216`) and the pre-registered §5 band table is
   binding at analysis. Flag so the analyst does not read raw ledgers as band-scoped.
2. **INFO — same-bar exit tie labeling:** if hold expiry and the profit condition
   trigger on the same bar open, the code labels the single market exit `hold_period`
   (else-if priority, MtfCtxReversionModel.cs:282-294). Economically identical single
   exit; affects only the informative EXIT-MIX read. Design's "whichever first" leaves
   the tie unspecified — no change required; disclosed for the analyst.
3. **INFO → routed to §7 tripwire (HARD, pre-search):** 13/972 smoke fills sit ≤4.4 pts
   (~3 bps) outside the local m1 minute range and 5 fill minutes are absent locally —
   consistent with bid/ask-basis and feed-vintage differences between the cTrader
   backtest feed and the local parquet, not with self-adjudication. The pre-search
   native-fill physicality audit (≥50 fills per symbol×domain) must run as designed and
   HARD STOP on any genuinely untouched-price fill; it should state its price-basis
   tolerance explicitly.
4. **INFO — theoretical same-m1 double fill:** if one m1 tick sequence touched both
   extremes before the Opened event cancels the opposite side, a second same-label
   position could open and overwrite the candidate ledger entry. Not observed (0
   overlapping legs in 21,241 smoke trades); `gate_universe` fill_consistency and the
   physicality audit would surface it at full scale. Watch item only.
5. **INFO — carried from run 1:** stale registry values in `_pipeline-config.md` (doc
   drift, outside this experiment); index spread pins remain an operator pre-gate
   blocker for the NET leg only.

### Required before execution

- Operator execution approval (design §13; XENA sequencing per checkpoint 011).
- After full emission: `gate_universe` (2,736), estimand gate (`--expect` 12
  instruments), native-fill physicality audit (issue 3 routing) — all §7 HARD blocks,
  before any search read.
