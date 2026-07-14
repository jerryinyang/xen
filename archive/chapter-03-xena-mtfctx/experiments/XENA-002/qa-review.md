# QA Review — XENA-002 (append-only)

## QA run 1 — design-stage review — 2026-07-11 — 2026-07-11T12:01:45Z — mode: subagent — HEAD ae5a2bf784d05e582030a0bc4fc46c8ff7b5ffbb (dirty: pipeline-config, Xen.cs, xena-lane.md, xena-runs.md, INDEX.md modified; XENA-001/, XENA-002/, checkpoint-011, cf-mtfctx-001, MtfCtxRandomModel.cs, XENA-001.conf untracked)

Verdict: **APPROVE** (design stage)

**Scope note:** pre-implementation DESIGN review, mirroring XENA-001 QA run 1's pattern.
No implementation exists (model pending; no emissions, no `xena_candidate_gate.json`, no
`universe_manifest.json`). Trace is design-vs-governing-documents and design-vs-data. The
design-vs-code trace and the golden-trace numeric diff are DEFERRED and BLOCKING — a
post-implementation QA run is mandatory before execution sign-off. Execution is
additionally HARD-blocked on the XENA-001 retrospective read (operator sequencing
2026-07-11), correctly declared in design §1/§7/§13.

### Design-fidelity trace (design vs governing docs + data)

| Design clause (§ref) | Checked against | Verdict | Notes |
|---|---|---|---|
| Frozen registry sha256 537d691a… (header) | `verify_frozen_registry` logic re-run by QA on `python/experiments/INFR-006/results/xena_frozen_registry.json` | MATCHES | Canonical-blob sha256 recomputed = 537d691aaf59c19220ac65b922d780e970167e8b71972ea8d864402b36e672a6, identical to design header, lane spec, ledger row. (Raw-file sha is 437bdf5c…; the pin is the embedded canonical hash the code checks — same as XENA-001 QA note.) |
| X=0.70, F_floor=0.4302, gate=0.0558 (header) | registry contents | MATCHES | plateau_threshold=0.7, f_floor=0.4301969674088667, gate_pass_threshold=0.05580535791613938. Cited, not re-derived — INFR-006 clause (a) satisfied. |
| Mechanism block §1 | design-requirements §1 | MATCHES | Regularity (short-horizon continuation), horizon (0.5–4× HTF span), cadence (~0.2–0.3/bar, disclosed as estimate), P&L object (oracle-composed round-trip leg) all stated. DERIVED estimand/null/horizon/test each traceable to the mechanism; NOT a blind reuse of XENA-001's null (adds the informed-entry permutation expectation, drops the "run-is-null" clause that only applied to random entries) — L-13 satisfied. |
| Object identity §2 | design-requirements §2, B-4 | MATCHES | Breakout evaluated on latest confirmed bar at the same bar-open the market order fires; filters mask that same decision. Windows disjoint; folds purged ≥ max hold. |
| CTRL-02 entry definition §3 | cf-mtfctx-001 "long: close > highest high of last 3 bars; short: close < lowest low of last 3 bars; ignore while holding" | MATCHES (see Finding 2) | Design pins Close[t−1] vs High/Low[t−4..t−2], strict, ties=no-signal, evaluate-at-open. QA independently verified the uniqueness claim: an inclusive window (bars t−3..t−1) is degenerate under strict inequality — Close[t−1] > High[t−1] and Close[t−1] < Low[t−1] are both impossible — so the 3 bars strictly before the signal close is the only non-degenerate causal reading. Defensible; no operator sign-off required; recorded here as the QA derivation. |
| Entry execution: same-bar-open fill, flat-only, filter-masked §3 | XENA-001 Amendment 2 pattern; family "ignore signals while holding" | MATCHES | Faithful inheritance of the QA-derived fill pin. No RNG; L-19 correctly N/A for the model (permutation battery supplies null draws). |
| Exit: market at bar open after hold §3 | family spec (fixed hold only for CTRL-02) | MATCHES | No other exits; P-02 non-trigger correctly argued (no exit tuning). |
| Filter variants (19) + hold grid + domains + instruments = 2,736 §3 | cf-mtfctx-001 shared plane + locked decisions (combo blocks 6 each; hold arithmetic) | MATCHES | 1+2+1+3+6+6=19; LTF-bar grids {12,24,48,96}/{8,16,32,64}/{6,12,24,48} exact; 12 instruments exact; 19×4×3×12=2,736 arithmetic checked. |
| Vol-regime pin §3 | checkpoint-011 mandatory block + family appendix | MATCHES | median-TR ATR(14) (not Wilder), window 250 (inside registered [200,300], matches XENA-001 for comparability), hysteresis HIGH >P80/<P65, LOW <P20/>P35, MID otherwise; pinned before search, never tuned. |
| Feature causality §3 | checkpoint-011 (confirmed HTF bars, ≤ t−1, CloseTime alignment, never bar indices) | MATCHES | Stated verbatim in the filter pin. DI direction rule identical to XENA-001 (+DI>−DI long / +DI<−DI short). |
| Warmup §3 | XENA-001 §3 + new entry feature | MATCHES | Adds the 4-confirmed-LTF-bar breakout window to XENA-001's ADX ~28 / vol 264 (=250+14) HTF-bar warmup; 1d-domain vol-variant band loss (~10 months) disclosed. |
| SlPrice k=2 sizing-only §3 | family locked decision + lane carve-out clarification | MATCHES | EntryFill ∓ 2×HTF median-TR ATR(14) at latest confirmed HTF bar; sizing-only field, NO live stop orders; finite-or-REJECT. Identical k to XENA-001. |
| From-scratch clause §3 | family locked decision "no reuse of / reference to prior model-specific implementations" | MATCHES (see Finding 1) | Declared; the carve-out phrase "beyond shared-feature spec compliance" needs a one-line pin at implementation (Finding 1, MINOR). |
| Cost/unit pins §4 | XENA-001 §4 (inherited) + L-21/L-22 | MATCHES | Table value-for-value identical to XENA-001 Amendment-4 pins (JPY 0.006968, AUD 0.66197, EUR 1.08418, GBP 1.25292, HK 0.128205; XAUUSD 0.28 bps, BTCUSD 13.0 bps commission); TRAIN-only FX window (file start → 2024-03-28, no gate contact) inherited explicitly; spread = operator pin, BLOCKING for NET/deployability only. JP225 contract_size=10 disclosed. No screen-derived money claim anywhere in the design ⇒ §9 CONVERSION-PIN block N/A (verified: no SPDR/screen effect cited in money units). |
| Band boundaries §5 | XENA-001 §5 (registered boundaries) | MATCHES | Byte-checked: common span 2021-06-02T00:01Z → 2024-12-11T08:19Z (binding GER40); all 12 per-instrument 70% fences identical; band table identical (search →2023-03-08, ranking →2024-03-28, gate →2024-12-11T08:19); AnalysisEndUtc uniform; binding-table clause (no from_span rerun) inherited; folds 2023-06-12/09-16/12-22, purge 14 d with its XENA-001 QA-run-2 derivation cited; gate band ≫ block 64. Ledger row band string matches. |
| Run parameters §6 | lane frozen registry + XENA-001 §6 | MATCHES | SearchParams() registry defaults; 12 restarts, seeds 0–11; smoke budget procedure RE-RUN on this universe (XENA-001's 16000 explicitly NOT inherited blind — correct); registry_path mandatory on certify/gate. |
| Controls §7 | design-requirements §3 (B-1/B-5/B-6) | MATCHES | WS-6 battery control: disjoint population (550 synthetic nulls), MDE = battery power curve restated at live density, non-vacuity (real code paths incl. A-4 dual gate), expected outcomes both ways, disclosure pinned. Cross-universe XENA-001 anchor: disjoint by construction, informative-only — correctly not carrying a verdict (and correctly dependent on XENA-001 completing first, which the sequencing gate enforces). |
| Permutation tripwire non-vacuity §7 | design-requirements §4, L-14 | MATCHES | Entry-time block rotation within symbol×domain — causal alignment destroy, not P&L permutation (L-14 mean-invariance respected). Non-vacuity argued and QA-checked: rotation decouples entries from the price paths that follow them and changes leg coincidence, moving composed F̂/P25 — the exact statistics certification reads. Crucially the expected direction is INVERTED vs XENA-001 (informed entries ⇒ rotation MUST collapse the above-null excess toward the XENA-001-like level; survival = leak alarm → HARD STOP). This is a genuine per-run derivation, not a copied block. |
| Oracle determinism tripwire, HARD/INFORMATIVE split §7 | design-requirements §8, L-18 | MATCHES | HARD set includes estimand gate (--expect 12), SlPrice finite, holdout fence, registry hash, permutation alarm, plus the run-specific XENA-001-retro sequencing gate. No auto-verdicts. |
| Interpretation bands §8 | design-requirements §5, lane semantics | MATCHES | Run-level, no binaries, no SUPPORTED/tradability band anywhere (⇒ L-22 §10 binding-spread leg not triggered; deployability reads cite net_informational with spread pins BLOCKING — consistent). FILTER-STRUCTURE read informative-only with composition stats; family status moves only at checkpoint retro. GATE band: gross binding / net informational, fail = negative, no threshold revision — matches A-4/L-23. |
| Power §9 | design-requirements §6 | MATCHES (see Finding 3) | Cadence is an order-of-magnitude estimate (0.2–0.3/bar), disclosed as such with empirical cadence pinned for analysis; even at 3× lower the counts stay ≫ the 60-trade battery density, so the conservativeness claim is robust. Thin filtered variants correctly absorbed by the portfolio-object framing (no per-candidate verdicts). 1d vol-variant warmup loss disclosed. |
| Golden trace §10 | design-requirements §7 | MATCHES | Recipe fully determined by §3 pins (deterministic, no RNG — simpler than XENA-001); two candidates spanning domains and a DI-filtered variant (V03); QA-derives/developer-must-not-generate clause present. Adequate spec; numeric diff DEFERRED to post-implementation QA. |
| Amendment ledger §11 | design-requirements §11, L-23 | MATCHES | Empty ledger 0L/0T/0N is correct for a fresh design; inherited XENA-001 QA pins folded in as initial design content (not amendments) is the right accounting — they were amendments to XENA-001, and here they are pre-registration content. No streak; nothing to flag at the execution gate yet. |
| Gate plan §12 | lane ledger rules, INFR-006 clauses (d)/(e) | MATCHES | Ledger state 0/2 verified in `docs/signal-registry/xena-runs.md` (row registered 2026-07-11, DESIGN status, band string consistent); no default gate spend; `new_data_attestation` operator-only. |
| L-24 §12 rules (design-requirements) | this design's structure | N/A (traced) | No per-candidate eligibility batteries, no path-dependent exit selection (fixed holds), no phase-shift tripwire, no per-cell TEST-read floors — every cell enters unconditionally and the verdict object is the portfolio under the frozen machinery. The four F02/F04/F06/F07 clauses have no attachment point; the frozen WS-6 battery + permutation battery carry the null/eligibility burden. Traced clause-by-clause, none applicable. |
| Registry preconditions | cf-mtfctx-001 status | MATCHES | Family REGISTERED 2026-07-10; ledger row added at design time per ledger rule; gate reads counted (cap 2) with tally stated (0/2). |
| Holdout | §5 + lane | MATCHES | Final 30% of every file untouched; uniform AnalysisEndUtc fence at the common 70% minimum; per-instrument fences listed. Conf fence check DEFERRED to post-implementation QA (no conf exists). |

### Golden-trace diff

DEFERRED — no implementation or emission exists. §10 recipe is adequate for QA to
hand-derive events independently (all inputs pinned: m1 aggregation, warmup end, breakout
rule, V03 DI check, same-bar-open fill, hold exit, SlPrice formula). The numeric diff
against the emission is BLOCKING at the post-implementation QA run.

### Governance & boundary

- Mandatory declaration blocks: mechanism ✓, object identity ✓, control validity ✓,
  tripwire (+non-vacuity) ✓, bands ✓, power ✓, golden trace ✓, hard/informative ✓,
  CONVERSION-PIN N/A (no screen-money citation) ✓, L-22 (no tradability band; spread
  blocking for NET) ✓, L-23 ledger present ✓, L-24 traced N/A ✓.
- `check_no_local_accounting`: N/A — `python/experiments/XENA-002/code/` does not exist
  yet; check at post-implementation QA.
- No Python strategy backtest anywhere in the design ✓ (C# emission → oracle composition).
- INFR-006 clauses: (a) registry verified + byte-matched ✓; (b) SlPrice finite pinned,
  candidate-gate JSON pending implementation (deferred) ✓; (c) bands pre-registered,
  folds disjoint from search band ✓; (d) attestation operator-only ✓; (e) ledger 0/2 ✓.
- Deviations block: none present; none needed.
- Elicitation hygiene: the single open operator item (spread pins pre-gate) is stated in
  plain language with its blocking scope ✓.

### Issues

1. **MINOR (design clarity — pin at implementation)** — design §3 Model axis: the
   from-scratch carve-out phrase "no reuse … incl. MtfCtxRandom internals **beyond
   shared-feature spec compliance**" is ambiguous against the family's locked decision
   ("no reuse of / reference to prior model-specific implementations"). Whether the HTF
   feature computations (ADX/DI, median-TR ATR, vol-regime hysteresis) may be shared code
   or must be re-implemented must be pinned in one line before the developer starts;
   otherwise the post-implementation QA cannot adjudicate a reuse finding. Does not block
   design approval.
2. **NOTE (verified, no action)** — CTRL-02 entry reading: QA independently confirms the
   design's uniqueness claim. Under strict inequality, including the signal bar in the
   3-bar window is impossible on both sides (Close[t−1] ≤ High[t−1]; Close[t−1] ≥
   Low[t−1]), so Close[t−1] vs High/Low[t−4..t−2] is the only non-degenerate causal
   reading of the family text. Defensible unique reading; operator sign-off NOT required;
   this note serves as the recorded derivation.
3. **LOW (informational)** — §9 entry cadence (~0.2–0.3/bar) is asserted at
   order-of-magnitude, unlike XENA-001's analytic 0.5/bar. The power conclusion is robust
   to a 3× overestimate and empirical cadence is pinned for disclosure at analysis; no
   change required. If realised unfiltered cadence falls below ~0.05/bar on any domain,
   the analyst should restate battery power at the realised density before any read.
4. **DEFERRED-BLOCKING (carry to QA run 2)** — post-implementation QA must cover:
   design-to-code clause trace, golden-trace numeric diff, conf holdout fence,
   `check_no_local_accounting`, `xena_candidate_gate.json` pass + freshness, and the
   ingest-time `verify_frozen_registry` paste. Execution additionally requires the
   XENA-001 retrospective read (operator) and operator spread pins before any NET/gate
   read.

**Verdict: APPROVE** — the design is ready as-registered; approval is design-stage only
and does not authorize implementation-skip, execution, or gate spend.

## QA run 2 — post-implementation review — 2026-07-11 — 2026-07-11T12:22:54Z — mode: subagent — HEAD ae5a2bf784d05e582030a0bc4fc46c8ff7b5ffbb (dirty: pipeline-config, Xen.cs, xena-lane.md, xena-runs.md, INDEX.md modified; MtfCtxMomentumModel.cs, MtfCtxRandomModel.cs, XENA-001/, XENA-002/, checkpoint-011, cf-mtfctx-001, XENA-00{1,2}.conf, gen_xena00{1,2}_manifest.py untracked)

Verdict: **REVISE** (one item — Amendment-1 from-scratch declaration requires operator
adjudication; every technical, fidelity, golden-trace, and governance check PASSES)

**Scope:** post-implementation review closing QA run 1's DEFERRED-BLOCKING items:
design-to-code clause trace, independent golden-trace numeric diff (smoke emission,
USTEC 1h cell), conf/manifest/registration checks, `check_no_local_accounting`,
candidate-gate + frozen-registry verification, causality audit, from-scratch /
spec-equivalence adjudication.

### Design-fidelity trace (design §3 pins → MtfCtxMomentumModel.cs)

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §3 entry signal: LONG Close[t−1] > max(High[t−4..t−2]); SHORT Close[t−1] < min(Low[t−4..t−2]); strict; ties = none | MtfCtxMomentumModel.cs:167–186 (`_ltfWindow` 4 confirmed bars, front=oldest; `window[3].Close` vs max/min over `window[0..2]`; strict `>`/`<`) | MATCHES | Window pushed AFTER decisions (:219–221) so it holds t−4..t−1 at decision time. Numerically confirmed by golden trace. |
| §3 same-bar-open fill, flat-only, filter-masked | :194–207 (`cand.Direction == 0 && signalSide != 0 … EntryFill = bar.Open`) | MATCHES | Market fill at decision bar's Open; signal ignored while holding (flat check) or when `VariantAllows` false. |
| §3 exit: market at open after hold bars; no other exits | :191–192 (`_barIndex − EntryBarIndex == HoldBars` → `CloseLeg(exitFill: bar.Open)`) | MATCHES | Exact-equality trigger checked every bar ⇒ never skipped. Only other exit is fence censoring (Dispose :441–453, Censored=1, RealizedBps NaN) — contract, not a strategy exit. |
| §3 hold grid {12,24,48,96}/{8,16,32,64}/{6,12,24,48} | :124–134 (`baseSpan = htfMinutes/ltfMinutes`; holds {½,1,2,4}×) | MATCHES | 1440/60=24, 240/15=16, 60/5=12 → exact grids. Registered pairs only; anything else throws. |
| §3 filter variants V00–V18 incl. combo order pin | :234–258 `VariantAllows` | MATCHES | V00 pass-all; V01 ADX<25; V02 ADX≥25; V03 DI; V04/05/06 vol LOW/MID/HIGH (`variant−4` = label 0/1/2); V07–V12 k=variant−7: volTarget=k/2, highADX=k odd → (LOW,<25)(LOW,≥25)(MID,<25)(MID,≥25)(HIGH,<25)(HIGH,≥25) = design combo order; V13–V18 same + `DiAllows`. Hand-enumerated all 19. |
| §3 ADX(14) Wilder, threshold 25 | :320–358 (14-bar DM/TR sums → Wilder `sm − sm/14 + x`; DI=100·smDM/smTR; DX; ADX = mean of first 14 DX then Wilder) | MATCHES | Standard Wilder construction; threshold 25 at :51. DI values byte-matched emission in golden trace (Wilder-converged region). |
| §3 ±DI direction rule (long iff +DI>−DI; short iff +DI<−DI) | :260 `DiAllows` | MATCHES | Strict inequalities; tie blocks both sides (conservative, consistent with strict-tie convention). |
| §3 median-TR ATR(14), not Wilder | :306–317 (queue of last 14 TRs; sort; mean of two middle order stats) | MATCHES | Rolling median, even-window = mean of 7th/8th order statistics. Family-spec conformant. Numerically confirmed (HtfAtr matched to 1e-6). |
| §3 vol regime: rank vs trailing 250; hysteresis >P80/<P65, <P20/>P35 | :366–401 `UpdateVolRegime` | MATCHES | Percentile = strict-less count over 250 PRIOR medATR values (current excluded — trailing history per family spec); initial label P80/P20; hysteresis transitions exact, incl. direct HIGH↔LOW jumps. Identical convention to XENA-001 model ⇒ cross-universe comparability holds. |
| §3 filters use confirmed HTF bars ≤ t−1, CloseTime alignment | :157–165 (bucket key `(closeSec−1)/(HTF·60)`; features updated only on bucket ROLL, i.e. completed buckets, before decisions) + :89/:295 `_lastHtfCloseTime` | MATCHES | Epoch-seconds bucketing from CloseTime, never bar indices. See causality audit. |
| §3 warmup suppression | :194 (`_medAtrReady` required for ALL entries), :171 (4 confirmed LTF bars), variants self-gate via `_adxReady`/`_volReady` (:239–249) | MATCHES | ADX ready ≈ 29 HTF bars (design "~28"); vol ready at 265th medATR-bearing HTF bar (design "264") — ±1 bar on a "~" pin, immaterial. V03 gated on `_adxReady` (DI shares the Wilder warmup) — matches design's "ADX/DI: ~28 HTF bars". |
| §3 SlPrice = EntryFill ∓ 2×HTF medATR(14), sizing-only, no live stops | :201 (`bar.Open − side·2·_medAtr`), :53 k=2 | MATCHES | `_medAtr` is the latest COMPLETED HTF bucket's value. No stop-order code path exists anywhere in the file. Entry requires `_medAtrReady` ⇒ SlPrice finite on every leg (gate stop_contract 76/76 pass). |
| §3 no RNG, deterministic | whole file | MATCHES | No Random/GUID/time-dependent branching (only `generated_utc` metadata string). |
| §3 candidate IDs C2-SYM-DOM-Hx-Vnn, 76/feed | :139–147 | MATCHES | `C2-{SYM}-{1D1H|4H15M|1H5M}-{H05X,H1X,H2X,H4X}-V{00..18}`; broker symbol names (STOXX50/DE40) — same broker-name convention as XENA-001 and the manifest. |
| §5 AnalysisEndUtc uniform fence | XENA-002.conf:20–33 (all 12 = 2024-12-11T08:19:00Z); harness fence via `_strategyFence.AnalysisEndUtc` (Xen.cs:375–377) | MATCHES | Smoke emission max ts 2024-12-11T08:00 < fence (gate `fence` pass 76/76). BACKTEST_END 11/12/2024 08:20 (dd/MM) consistent. |
| Registration | Xen.cs:20–26 (enum: MaCrossover=0, Donchian20=1, MtfCtxRandom=2, **MtfCtxMomentum=3**), :375–377 CreateStrategyModel, :405–409 BuildStrategyParameters (run=XENA-002, breakout_lookback=3, candidates_per_feed=76) | MATCHES | conf `STRATEGY_VALUE="3"` = enum position. Constructor args (symbol, domain minutes, output root, fence) correct. |
| §4 cost/unit pins → manifest | gen_xena002_manifest.py:28–41 | MATCHES | Value-for-value vs design §4: indices 0 bps; XAUUSD 0.28; BTCUSD 13.0; mpu JP225 0.006968, AUS200 0.66197, STOXX50/DE40 1.08418, HK50 0.128205, UK100 1.25292, USD-quoted 1.0. Commission-only noted; spread = operator pre-gate item declared in `cost_note`. |
| §3 manifest 2,736 | universe_manifest.json | MATCHES | 2,736 unique C2- ids, 12 symbols × 3 domains × 4 holds × 19 variants; registry_sha256 = 537d691a…e672a6; analysis_end_utc = 2024-12-11T08:19:00Z. run_dir = lowercase candidate id = model's emitted dir names (deterministic, no timestamp). |
| Emission contract | :458–583 (run_metadata.json + positions.parquet + cis_trades.parquet per candidate) | MATCHES | Fills-based cis_trades with finite SlPrice; shared real-OHLC grid; feed-level sentinel dir is inert (not in manifest; gate reads manifest only). Contract-level sharing — explicitly not a from-scratch violation per Amendment 1 carve-out. |
| Amendment 1 from-scratch | see Issue 1 | **CANNOT VERIFY** | Spec equivalence CONFIRMED independently; "never copied" provenance claim not verifiable — see Issue 1. |

Three shipped failure shapes checked: no frozen computation (medATR/ADX/DI/vol all
recomputed per completed HTF bucket; entry snapshot fields are per-leg records, not live
state), no anchor drift (EntryFill/SlPrice fixed at entry; hold count anchored to
EntryBarIndex), no confounded comparator (no in-model control; controls are XENA-001 +
WS-6 battery per design §7).

### Golden-trace diff (independent, QA-derived from raw m1)

Derivation: raw `data/timebars/timebars_ustec_20210602_000000_20260621_190833.parquet`
aggregated by QA to 1h and 1d grids (bucket key `(closeSec−1)//period`), features
(median-TR ATR(14), Wilder ADX/±DI) recomputed from scratch in Python; expectations
derived from design §10 recipe only, never from the C# code. Developer did not generate
these values (README contains no trace numbers).

- **Grid integrity:** 20,783 common 1h bars (parquet window ∩ emission) — max |diff| on
  Open/High/Low/Close = **0.0**. Emission convention: SourceCloseTime = bucket's last m1
  CloseTime; identical to QA aggregation.
- **C2-USTEC-1D1H-H1X-V00** — 6 consecutive events from 2021-08-01 (first
  parquet-verifiable region past HTF warmup): entries 2021-08-02T00:00 (+1),
  2021-08-03T02:00 (+1), 2021-08-04T07:00 (+1), 2021-08-05T08:00 (−1), 2021-08-06T14:00
  (−1), 2021-08-09T20:00 (+1). All 6: breakout condition holds on QA bars ✓; EntryFill =
  decision-bar Open ✓ (exact); exit at Open of bar t+24, ExitTime matches ✓; SlPrice =
  EntryFill ∓ 2×QA-medATR ✓ (1e-6); HtfAtr matches ✓. **Chain continuity:** no missed
  signal bar between consecutive V00 exits/entries (first-signal-when-flat verified) ✓.
- **C2-USTEC-1D1H-H1X-V03** (DI-filtered) — 4 events from 2023-02-01 (Wilder-converged):
  entries 2023-02-01T21:00, 2023-02-03T13:00, 2023-02-06T16:00, 2023-02-07T18:00 (all +1).
  All: breakout + fills + SlPrice ✓; DI direction rule (+DI>−DI for longs) holds on
  QA-computed values ✓; emitted HtfPlusDi/HtfMinusDi match QA values to <0.05 (e.g.
  30.068/23.584 exact) ✓.
- Design §10's second named candidate `C2-XAUUSD-1H5M-H2X-V03` has no emission yet (smoke
  = USTEC 1h cell only) — substituted USTEC V03 for the DI spot-check; the XAUUSD 5m trace
  is carried as a pre-analysis condition (Issue 3).
- Verdict: **PASS** — 10/10 events + grid + chain, zero discrepancies.

### Governance & boundary

- `check_no_local_accounting("python/experiments/XENA-002/")`: **{ok: true, banned_defs_found: []}** ✓.
- No Python strategy backtest in the experiment dir (code/ holds README only) ✓.
- `verify_frozen_registry` re-run at this QA: passes; plateau_threshold=0.7,
  f_floor=0.4301969674088667, gate_pass_threshold=0.05580535791613938,
  block_bars=64 — byte-match design header pins (X=0.70, F_floor=0.4302, gate=0.0558) ✓.
- `xena_candidate_gate.json`: blocking_pass=true, 76/76 (files, schema, non_empty, fence,
  causality, stop_contract finite-SlPrice, fill_consistency 0.0000 bps, oracle_smoke);
  fresh (2026-07-11 13:14, post-smoke). Covers the smoke cell only — full-universe gate
  re-run required after full emission (design §13 flow, Issue 3) ✓/carried.
- Causality audit (mandatory check 7): OnBar order is (a) HTF bucket ROLL first — features
  update only from buckets completed strictly before bar t's bucket (key from CloseTime−1s;
  current bar added to bucket only AFTER the roll check consumes prior bars? — the roll
  fires when the key CHANGES, using only previously-buffered bars; bar t is appended
  after), (b) breakout read from `_ltfWindow` = confirmed bars t−4..t−1 (bar t enqueued at
  :219, AFTER decisions), (c) exits then entries at bar t Open — bar t's High/Low/Close
  never read pre-fill. **No lookahead path found** ✓. Confirmed empirically: gate
  causality 76/76 + golden-trace DI/ATR values equal QA's strictly-prior-bucket values.
- Holdout: fence uniform 2024-12-11T08:19Z; smoke max emitted ts 08:00 ✓; final 30%
  untouched (analysis-side bands from §5 registered timestamps, unchanged from run 1) ✓.
- INFR-006 clauses: (a) registry verified + byte-matched ✓; (b) SlPrice finite +
  candidate gate passing/fresh (smoke scope) ✓; (c) bands pre-registered, unchanged ✓;
  (d) no attestation authored ✓; (e) ledger 0/2, no gate spend ✓.
- L-23 ledger: Amendment 1 NEUTRAL, count 0L/0T/1N — no streak ✓.
- Execution remains **HARD-BLOCKED**: XENA-001 retrospective read (operator) not yet done;
  operator spread pins still pending (pre-gate NET blocker). Both correctly declared in
  conf header + design §1/§4/§13 ✓.
- DEVIATIONS: developer declares none; three recorded interpretations (hold-exit-before-
  entry same bar; HTF pair map; entry requires medATR ready + 4 LTF bars) are all either
  design-implied (SlPrice finiteness forces medATR readiness; warmup pin forces the 4-bar
  window) or inherited family/XENA-001 convention (same-bar re-entry) — none verdict-
  material, none a silent deviation ✓. Exception: from-scratch declaration, Issue 1.

### Issues

1. **MEDIUM (operator adjudication required before execution sign-off)** — Amendment 1
   (design §3/§11) pins the model as "written from scratch … HTF feature logic
   reimplemented fresh … never copied", and the developer README repeats "no code
   imported from MtfCtxRandomModel". QA diffed the two files: `UpdateHtfFeatures` and
   `UpdateVolRegime` are **textually near-identical** to MtfCtxRandomModel.cs (same
   variable names `_smTr`/`_medAtrHistory`, same expressions, same idiosyncratic choices
   — strict-less percentile count, `pct < 0.20 ? 0 : 1` collapse — and the identical
   comment "percentile window (design pin, 200-300)"); the diff of the feature block is
   comments-only plus one counter line. QA cannot distinguish copying from same-author
   convergence on the same spec, so the "never copied" provenance claim is CANNOT-VERIFY
   and plausibly breached. Substantively: **spec equivalence is independently CONFIRMED**
   (clause trace + numeric golden trace vs the family spec), and textual identity actually
   guarantees the cross-universe comparability the design wants — the epistemic risk the
   pin guarded (unadjudicable reuse) is closed by this QA. Required action (one of):
   (a) operator accepts shared spec-identical feature code via a dated NEUTRAL Amendment 2
   superseding the "never copied" wording; or (b) developer attests independent
   implementation and the operator accepts the attestation on record; or (c) operator
   orders genuine reimplementation. No code change is technically required — behaviour is
   verified correct either way.
2. **NOTE (verified, no action)** — smoke emission (and any full run) starts at the
   cTrader backtest start (grid begins 2021-01-04), before the registered common span
   start 2021-06-02 and before the repo parquet coverage. Pre-span bars only extend
   warmup; §5's binding band table (analysis-side SegmentLayout from registered
   timestamps) excludes pre-span trades from search/ranking/gate. Trades dated Jan–May
   2021 are not independently verifiable from repo data — analysts should treat them as
   out-of-band by construction.
3. **CARRIED CONDITIONS (pre-analysis / pre-gate, already in design flow)** — after full
   emission and before any search read: full-universe `gate_universe` re-run (2,736) +
   estimand gate (`--expect` 12 instruments) + golden-trace repeat on the design-named
   `C2-XAUUSD-1H5M-H2X-V03` cell. Before execution: XENA-001 retro read (operator).
   Before any NET/gate read: operator spread pins + manifest regeneration with spread.
4. **NOTE (informational)** — smoke filter-masking monotonicity (V00 874 ≥ V03 737 ≥
   V06 201 trades on H1X) is consistent with mask-only filtering (QA recomputed V00=874
   trade count independently via the emitted file row count).

**Verdict: REVISE** — solely Issue 1 (operator adjudication of the from-scratch
declaration; resolvable by amendment or attestation, no technical rework identified).
Every fidelity, golden-trace, causality, governance, and configuration check passes.
On resolution of Issue 1 this review supports execution sign-off, subject to the
already-registered operator gates (XENA-001 retro read; spread pins pre-gate).

---

## QA run 2 resolution — 2026-07-11

**Issue 1 (MEDIUM, from-scratch provenance) — RESOLVED via option (a).** The operator
recorded a dated NEUTRAL Amendment 2 in design.md §11 (2026-07-11, running count 0L/0T/2N)
accepting spec-identical shared HTF feature code across family universes (cross-universe
comparability), and scoping the from-scratch clause to entry/model logic. The developer
disclosed on record that the feature code is not clean-room (an emission-contract read of
MtfCtxRandomModel preceded writing). QA verified the amendment text against design.md §11;
it matches the adjudication. Spec equivalence remains independently CONFIRMED by this
review's clause trace and 10/10 golden trace, so the substantive risk the pin guarded is
closed.

**Updated verdict: APPROVE (post-implementation).** Standing conditions unchanged:

1. Execution remains blocked on the XENA-001 retrospective read + explicit operator
   execution approval.
2. After full emission, before any search/analysis read: full-universe candidate gate
   (`gate_universe`, 2,736) + estimand gate (`--expect` 12 instruments) + golden-trace
   repeat on `C2-XAUUSD-1H5M-H2X-V03`.
3. Operator spread pins (+ manifest regeneration with spread) before any NET/gate read.

## QA run 2 addendum — full-emission golden-trace repeat — 2026-07-11 (mode: subagent, same reviewer/HEAD as QA run 2)

Carried condition from QA run 2 Issue 3: golden-trace diff on the design-named second
candidate `C2-XAUUSD-1H5M-H2X-V03`, now emitted in the full 36-cell run. Coordinator
context noted: operator execution approval recorded; full-universe candidate gate
2736/2736 blocking_pass; estimand gate blocking_pass=true (broker aliases STOXX50/DE40 =
EU50/GER40, same as XENA-001). (The tasking message's "exit at entry+32" is a slip — the
design §3 grid pins 1h/5m H2X = 2×12 = **24** LTF bars; the emission's HorizonBars=24
matches the design and the trace was run against 24.)

Method (independent, from raw m1): `data/timebars/timebars_xauusd_20210602_000000_
20260621_190824.parquet` aggregated by QA to 5m LTF and 1h HTF (bucket key
`(closeSec−1)//period`); medATR(14) and Wilder ±DI recomputed from scratch; expectations
from the design §10 recipe only.

- **Grid integrity:** 248,242 common 5m bars (parquet ∩ emission) — max |OHLC diff| =
  **0.0**.
- **Feed composition finding (contract, not a model defect):** the harness LTF feed
  omits 96 sparse session-edge 5m bars over the 2021-06→08 window (all ~20:57/22:05
  session-close minutes; harness coverage filtering — `strict_coverage`/`min_coverage`
  parameters). Emitted-not-in-parquet bars: **0** (no fabricated data). An all-minutes QA
  aggregation therefore reproduces medATR/SlPrice exactly but leaves a small persistent
  Wilder-DI offset (≲0.35, decaying at the Wilder rate; DI direction rule unaffected —
  margins ≫ offset). Recomputing HTF features on the harness bar set — whose bar VALUES
  were first verified bar-for-bar equal to raw m1 — closes the gap exactly.
- **Event diff — 3 consecutive events from 2021-08-02** (first parquet-verifiable region):
  entries 2021-08-02T01:15 (−1, SL 1821.35), 03:15 (−1, SL 1818.77), 05:20 (−1, SL
  1817.49). All 3 × 9 checks PASS: breakout condition on QA bars ✓; V03 −DI>+DI on the
  latest completed HTF bucket ✓ (QA ±DI equals emitted HtfPlusDi/HtfMinusDi to 4 decimals,
  e.g. 12.3637/26.8298); EntryFill = decision-bar Open (exact) ✓; exit at Open of bar
  t+24, ExitTime matches ✓; SlPrice = EntryFill + 2×QA-medATR ✓ (1e-6); HtfAtr ✓;
  HtfBarCloseTime = QA's latest completed 1h bucket ✓.

**Result: PASS — 0 discrepancies (3/3 events × 9 checks; grid 0.0).** Both design-named
golden-trace candidates are now traced (USTEC 1D1H V00 + V03 in QA run 2; XAUUSD 1H5M
H2X V03 here). This closes QA run 2 Issue 3's golden-trace leg; remaining before verdict-
bearing reads: Issue 1 (from-scratch adjudication) and operator spread pins (pre-gate NET
blocker). The QA run 2 verdict line (REVISE, Issue 1 only) is unchanged by this addendum.
