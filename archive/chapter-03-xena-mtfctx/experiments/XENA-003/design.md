# XENA-003 — MTFCTX-C3: HTF context filters on a NAIVE REVERSION control (CTRL-03)

**Status:** DESIGN (2026-07-11) — awaiting QA pre-exec (fresh context)
**Checkpoint:** 011 (`docs/experiments-docs/checkpoints/2026-07-10-011-mtf-context-xena/`)
**Family group:** CF-MTFCTX-001 (`docs/signal-registry/candidate-families/cf-mtfctx-001.md`)
**Frozen registry:** sha256 `537d691aaf59c19220ac65b922d780e970167e8b71972ea8d864402b36e672a6`
(v3, 2026-07-10) — verified via `xen.xena.calibration.verify_frozen_registry` at ingest and
pasted into qa-review.md. Thresholds NEVER re-derived (X=0.70, F_floor=0.4302, gate=0.0558
GROSS null-P95; cited, not restated as claims).
**Execution contract:** native cTrader limit orders + m1 fills (EXP-013/L-14 carve-out) —
the hardest contract of the three universes; sequenced last per checkpoint 011.

## 1. Idea + mechanism

```
MECHANISM: short-horizon mean reversion — price returning to the trailing 3-bar extreme
(lowest low / highest high) marks a local liquidity point where a passive limit fill is
hypothesised to capture snap-back over 0.5–4× the HTF span, or earlier via a floating
profit exit at 0.5× current HTF ATR. HTF context (trend strength ADX, trend direction ±DI,
volatility regime) is hypothesised to condition the quality of these LTF reversion fills:
fades should be richer when HTF trend is weak/ranging or vol regime favours snap-back.
Event cadence: continuous two-sided trailing quotes while flat; fills when price revisits
the 3-bar extreme (clustered in ranges). P&L-bearing object: the round-trip leg (limit
entry fill → profit-exit or hold-period exit fill), composed chronologically by the
shared-capital oracle.
DERIVED: estimand = oracle log-wealth F over composed legs (xen.xena.oracle, gross at
selection, net informational at gate); null = frozen WS-6 calibration battery + entry-time
block-rotation permutation battery on these emissions (alignment destroy, never P&L
permute — L-14) + XENA-001 live-data null anchor; horizon = hold-period grid {0.5,1,2,4}×
HTF span with the floating 0.5×ATR profit exit (both from the reversion-capture
hypothesis); test = frozen XENA certification + counted gross gate.
```

**Run purpose (declared).** XENA-003 is the family's second informed control universe and
the native-order execution exercise: CTRL-03 entries carry naive reversion information
captured through resting limits, the case StrategyHost self-adjudication cannot fill
honestly (EXP-013). The thesis read stays portfolio-level (cf-mtfctx-001, no A/B claim):
whether the machinery certifies anything, and whether filtered variants (V01–V18) are
systematically selected over baseline (V00), are the informative outputs.

**KB/pitfalls check.**
- **P-10 (passive-limit MR fades banned as capture vehicle)** — acknowledged head-on:
  CTRL-03 is a passive limit at the 3-bar extreme. Not a re-run because (a) it is a
  deliberately naive **control entry engine**, not a registered edge claim — the registered
  thesis is the HTF filter effect, adjudicated by portfolio selection (same framing as the
  P-01 acknowledgment in XENA-002); (b) P-10's mechanism was the **entry-seam mismatch**
  (measured confirmed-breach event ≠ limit-touch fill, adverse selection invisible to the
  measurement) — here the traded object IS the limit fill, executed natively with m1 fills,
  so adverse selection is priced into the emission, not hidden by it; (c) the family was
  registered with this control by operator sign-off 2026-07-10 after the KB read.
- P-14 (HTF-DI sub-cost at 1h/5m) — not a re-run: new family, holds 0.5–4× HTF span
  (≥10× capture-vehicle escape clause), L-21 unit pins §4.
- P-02 not triggered: exits fixed by the family spec (hold-period + floating profit exit),
  no exit optimisation.
- L-19: no RNG in this model — determinism structural; permutation battery supplies nulls.
- L-14 exit-set clause: the proposal names exactly TWO exits (fixed hold-period; floating
  profit exit). §3 implements both; QA must enumerate implemented exits and diff against
  this named set (no silent drop, no adverse target, no live stop).
- EXP-013 carve-out ENGAGED: native cTrader limit orders, engine m1 fills; no OHLC
  self-adjudication of limit touches.

## 2. Object identity

```
OBJECT-IDENTITY:
  measurement object == trading object: YES — oracle-composed round-trip legs of the
    emitted candidates; selection and gate read the same composed portfolio object
    (L-16/L-18). Legs are native-fill legs: entry price = engine limit fill.
  measured conditioning event == traded entry event: YES — capital commits at the LIMIT
    FILL of an order whose resting was filter-approved; filters mask order PLACEMENT
    (re-evaluated every LTF bar open on confirmed bars ≤ t−1, order cancelled if the mask
    turns off), and the emission records the fill that actually happened (B-4: the
    CF-MR-004 seam is closed by trading the measured object natively, not by measuring a
    correlated one).
  effect-splitting windows non-overlapping: YES — search/ranking/gate bands disjoint (§5);
    folds purged ≥ max hold horizon.
```

## 3. Universe manifest (every cell enters; no per-candidate quality gates)

| Axis | Values |
|---|---|
| Model | `MtfCtxReversion` (C# ISignalModel + native-order harness, **entry/model logic written from scratch**; HTF feature logic (ADX/DI, median-TR ATR, hysteresis regime) may be spec-identical to the family implementation per XENA-002 Amendment 2 operator decision — cross-universe comparability; QA verifies spec equivalence) |
| Filter variants | V00 baseline · V01 ADX<25 · V02 ADX≥25 · V03 DI-direction · V04/05/06 vol LOW/MED/HIGH · V07–V12 vol×ADX (6) · V13–V18 vol×ADX+DI (6) — 19 total |
| Hold multipliers | 0.5× 1× 2× 4× HTF span → LTF bars: 1d/1h {12,24,48,96}; 4h/15m {8,16,32,64}; 1h/5m {6,12,24,48} |
| Domain pairs (HTF/LTF) | 1d/1h · 4h/15m · 1h/5m |
| Instruments | USTEC US500 US2000 JP225 AUS200 US30 EU50 GER40 HK50 UK100 XAUUSD BTCUSD |
| **Total candidates** | 19 × 4 × 3 × 12 = **2,736** |

Candidate ID: `C3-<SYM>-<DOM>-H<mult>-V<nn>` (e.g. `C3-USTEC-4H15M-H2X-V07`).
Manifest file: `data/strategy_runs/XENA-003/universe_manifest.json`.

### Model pins (CTRL-03)

- **Quoting (causal derivation, pinned):** at each LTF bar t open, on confirmed bars only,
  while FLAT: maintain a **BUY limit at `min(Low[t−3], Low[t−2], Low[t−1])`** and a
  **SELL limit at `max(High[t−3], High[t−2], High[t−1])`** — two-sided trailing quotes,
  re-priced (amended/re-quoted) at every LTF bar open to the new 3-bar extreme ("reset to
  the new limit price … essentially a trailing limit", proposal verbatim). No trigger
  event: the quote refresh IS the signal cadence.
- **Filters mask quoting per side (HTF, confirmed bars ≤ t−1, `CloseTime` alignment,
  never bar indices):** at each LTF bar open, a side's limit rests only if the variant's
  filters allow that side; a resting order whose mask turns off is cancelled at that bar
  open. Non-directional filters (ADX, vol regime) mask both sides; the DI filter masks by
  side (long allowed iff +DI > −DI; short iff +DI < −DI). Filter values: ADX(14) Wilder,
  threshold 25; vol regime per family pin: **median-TR ATR(14)** (rolling median of true
  ranges, window 14 — not Wilder ATR), percentile-ranked against trailing **250 HTF bars**
  (pinned; matches XENA-001/002), hysteresis HIGH entered >P80 / exited <P65, LOW entered
  <P20 / exited >P35, MID otherwise. Pinned before search, never tuned on outcomes.
- **Fills: ENGINE-NATIVE.** Orders are real cTrader limit orders; the backtester fills
  them against m1 data (our most granular local domain). No model-side fill simulation, no
  OHLC self-adjudication (EXP-013). Intrabar sequencing/gap handling is the engine's
  documented behaviour; disclosed, not re-implemented. On fill of one side, the other
  side's order is cancelled immediately (one position at a time). While holding, no new
  quotes ("if holding period is active, ignore new signals").
- **Crossed-limit rule (operator pin, 2026-07-11 — Amendment 1):** a side quotes only
  when PASSIVE — buy limit strictly below current Bid, sell limit strictly above current
  Ask at the quote refresh; a crossed side simply does not rest that bar (the trailing
  extreme follows price, restoring passivity on subsequent bars). No market-conversion of
  crossed quotes.
- **Exit 1 — fixed hold-period:** market order at the open of LTF bar `fill_bar + hold`,
  where `fill_bar` = the LTF bar during which the entry fill occurred. Hold counted in LTF
  bars per the exploration plane.
- **Exit 2 — floating profit exit (whichever first):** evaluated at each LTF bar t open on
  the latest CONFIRMED close: if `Close[t−1]` is in profit relative to `EntryFill` AND the
  profit distance ≥ **0.5 × current HTF median-TR ATR(14)** (value at the latest confirmed
  HTF bar at time t — the distance **floats with current ATR**, never frozen at entry) →
  market exit at bar t open. No adverse target; no live stop. Exit set = exactly these two
  (L-14 named-exit diff at QA).
- **Warmup:** quoting suppressed until every feature the variant uses is defined (3-bar
  extreme window: 3 confirmed LTF bars; ADX/DI: ~28 HTF bars; vol regime: 264 HTF bars).
  Disclosed: 1d-domain vol variants lose ~10 months of the search band to warmup.
- **Sizing stop (SlPrice):** `SlPrice = EntryFill ∓ 2 × HTF median-TR ATR(14)` (k=2, value
  at latest confirmed HTF bar at fill time). Sizing-only field — **no live stop orders**
  (family lane reconciliation 2026-07-10). Finite on every leg or candidate-gate REJECT.

## 4. Per-candidate cost + unit pins (L-21/L-22)

Costs excluded from selection (gross amendment A-1); charged at the NET informational gate
leg (forced in code). Pins are gate-verdict-bearing. Identical instrument set, data files,
and TRAIN-window FX pins as XENA-001/002 (same pre-gate window, file start → 2024-03-28,
no gate-band contact):

| Symbol | commission (FTMO table) | cost_bps RT (commission-only; +spread once pinned) | spread | money_per_unit (pin source) |
|---|---|---|---|---|
| USTEC US500 US2000 US30 | 0 (cash-CFD) | 0 + spread | **OPERATOR PIN REQUIRED pre-gate** | 1.0 (USD-quoted) |
| XAUUSD | 0.0014%/side | 0.28 bps + spread | operator pin pre-gate | 1.0 |
| BTCUSD | 0.065%/side | 13.0 bps + spread | operator pin pre-gate | 1.0 |
| JP225 | 0 | 0 + spread | operator pin pre-gate | 0.006968 (JPY→USD = 1/143.516; USDJPY median 2023-01-03→2024-03-28) |
| AUS200 | 0 | 0 + spread | operator pin pre-gate | 0.66197 (AUDUSD median, same window) |
| EU50, GER40 | 0 | 0 + spread | operator pin pre-gate | 1.08418 (EURUSD median 2023-01-02→2024-03-28) |
| UK100 | 0 | 0 + spread | operator pin pre-gate | 1.25292 (GBPUSD median, same window) |
| HK50 | 0 | 0 + spread | operator pin pre-gate | 0.128205 (HKD peg mid 7.80; USD-pegged band 7.75–7.85) |

**Spread pins are a BLOCKING precondition for the final-gate NET leg and any deployability
read** — not for emission, candidate gate, search, or certification (all gross). L-22: any
deployability claim cites the `net_informational` block. JP225 `contract_size=10`
disclosed; oracle sizes raw units. Passive-limit entries earn the spread on the entry leg
in live trading; the NET leg still charges the full pinned RT spread (conservative,
disclosed — no maker-rebate assumption).

## 5. Band boundaries (pre-registered, Q1 partition — identical to XENA-001/002)

Same 12 instruments, same data files, same common analysis span: start **2021-06-02T00:01Z**,
end **2024-12-11T08:19Z** (min per-file 70% analysis cutoff; binding instrument GER40).
Per-instrument 70% fences (holdout starts) as registered in XENA-001 design §5:
USTEC 2024-12-11T17:33 · US500 2024-12-19T14:58 · US2000 2024-12-12T14:32 ·
JP225 2024-12-30T00:01 · AUS200 2025-01-07T04:24 · US30 2024-12-11T23:37 ·
EU50 2025-01-29T10:38 · GER40 2024-12-11T08:19 · HK50 2024-12-30T16:50 ·
UK100 2024-12-11T19:27 · XAUUSD 2024-12-12T04:09 · BTCUSD 2025-03-12T19:22.
Final 30% of every file never touched. `AnalysisEndUtc = 2024-12-11T08:19:00Z` for ALL
emissions (uniform fence at the common end).

| Band | Start (UTC) | End (UTC) |
|---|---|---|
| TRAIN search (50%) | 2021-06-02T00:01 | 2023-03-08T00:00 |
| TRAIN ranking (30%) | 2023-03-08T00:00 | 2024-03-28T00:00 |
| TEST gate (20%) | 2024-03-28T00:00 | 2024-12-11T08:19 |

**This table IS the binding band definition**: code constructs `SegmentLayout` directly
from these pre-registered ns timestamps — `from_span` is not re-run at execution time.
Folds: **n=4 contiguous purged folds** in the ranking band, boundaries 2023-06-12 ·
2023-09-16 · 2023-12-22 (00:00 UTC), **purge = 14 calendar days** (covers the measured
worst 96-trading-hour span, 11.375 d, XENA-001 QA run 2). Gate band ≫ block 64 on every
LTF grid.

## 6. Run parameters

Restarts **12**, seeds = restart ids 0–11; search budget from the pre-registered smoke
procedure (3 smoke restarts, budget = iteration where best-F improvement < 1% over
trailing 20% of iterations, then fixed for all 12) — prior universes' realised budgets NOT
inherited blind. Everything else: frozen registry values byte-checked by QA
(`SearchParams()` defaults; gate mechanics fixed in code). `certify_and_rank` /
`run_final_gate` receive `registry_path` (mandatory).

## 7. Controls, tripwires, integrity

```
CONTROL frozen-machinery null calibration (structural, pre-existing):
  question answered: what certification/gate rate does this machinery produce on no-edge
    universes? WS-6 v3 battery: null certification 2/300, end-to-end false passes 0/300
    (FPR ≤1% @95%); power 70% @30 bps gross/trade, 94% @40 bps at 60-trade density —
    restated per live trade density at analysis.
  population: 550 realistic-null synthetic universes — DISJOINT from this emission.
  bite/MDE: the battery's power curve IS the MDE statement; live trade counts (§9) ≫ 60 ⇒
    battery power conservative here.
  non-vacuity: battery exercised the real code paths incl. the A-4 dual gate.
  expected outcome if filters worthless AND reversion worthless: no certification/no pass.
  disclosure: full certification evidence package regardless of outcome.
CONTROL cross-universe null anchor (XENA-001, informative):
  question answered: what does this same manifest grid produce on information-free entries
    on the SAME instruments/bands/machinery? XENA-001's certification evidence package is
    the live-data null anchor for reading XENA-003's.
  population: 2,736 random-entry candidates — disjoint by construction (no shared entries;
    different fill mechanism disclosed alongside).
  disclosure: side-by-side best-F/certification comparison, informative only.
TRIPWIRE permutation-null battery (runs BEFORE any gate spend):
  causal alignment-breaking permutations of the real emitted trade streams — entry-time
  block rotation across candidates within symbol×domain (NEVER P&L permutation — L-14
  mean-invariance). CTRL-03 entries are price-aligned (fills at revisited extremes): IF
  search/certification finds real structure, rotation MUST collapse best-F/P25 toward the
  XENA-001-like null level (expected collapse fraction → ~1 of the above-null excess). A
  certified subset whose F̂ SURVIVES entry-alignment rotation = leak/artifact alarm →
  HARD STOP, operator.
  vacuity check: rotation changes which legs coincide in time and decouples entries from
  the price paths that follow them → moves portfolio F̂/P25, the statistics certification
  reads (composition + alignment are exactly what it destroys).
TRIPWIRE native-fill physicality audit (EXP-013-specific, pre-search):
  for a sample of ≥50 fills per (symbol × domain), verify against raw m1 data that each
  entry fill's limit price was actually touched (m1 Low ≤ buy limit / m1 High ≥ sell
  limit) within the fill minute, and that fill price ∈ [m1 Low, m1 High] of that minute.
  Any fill at an untouched price = execution-contract violation → HARD STOP.
TRIPWIRE oracle determinism: (bitmask, segment, seed) re-run → bit-identical F (raises on
  reconciliation drift; L-18 invariant).
HARD (block): estimand gate (xen.estimand_validation, --expect 12 instruments) before any
  analysis/search read; SlPrice finite per leg (gate_universe); holdout fence; registry
  hash match; permutation-battery alarm; native-fill physicality; operator execution
  approval.
INFORMATIVE (operator judges): all F/P25 readings, certification evidence, net block,
  collapse fractions, filter-structure reads, profit-exit vs hold-exit mix. No
  auto-verdicts.
```

## 8. Interpretation bands (run-level, pre-registered)

```
NO-CERT:            0 certified subsets — machinery-consistent negative for naive reversion
                    + HTF filters at portfolio level on these bands (informative, not a
                    family verdict; family status moves only at checkpoint retro).
CERT-EVIDENCE:      ≥1 certified subset — operator reviews evidence package (plateau,
                    restart dispersion, fold ranking, resim divergence) + permutation
                    battery + native-fill physicality BEFORE any gate consideration.
                    Certification is evidence, never a verdict.
GATE (if spent):    GROSS binding / NET informational (A-4); fail = negative result, no
                    threshold revision (L-23), no re-search on gate segments.
FILTER-STRUCTURE (informative): over-representation of V01–V18 vs V00 among top search
                    subsets and certified finalists — the family-thesis read; reported
                    with composition stats, never as a standalone SUPPORTED claim.
EXIT-MIX (informative): per-candidate profit-exit vs hold-exit fractions disclosed
                    (mechanism read: reversion captured early vs ridden to horizon).
POOLED: all cross-domain/cross-instrument figures disclosure-only.
UNPOWERED strata: none binding — the run object is the portfolio; per-candidate reads are
                    not verdicts in the XENA lane.
```

## 9. Power

Search band ≈ 21.3 months. Fill cadence estimate (two-sided trailing limit at the 3-bar
extreme, when flat): price revisits a trailing 3-bar extreme frequently — estimated fill
within ~1–4 bars of going flat in ranging conditions (order-of-magnitude; empirical
cadence + wait-time distribution disclosed at analysis). Effective cycle ≈ hold + 1–4 bars,
shortened further by the profit exit (exits before hold on captured reversions):
1h LTF (≈11.6k bars): H12 ≈ 700–900, H96 ≈ 115–160 · 15m (≈46k): H8 ≈ 3.5–5k,
H64 ≈ 650–900 · 5m (≈139k): H6 ≈ 13–18k, H48 ≈ 2.6–3.5k. All ≫ the 60-trade density of
the WS-6 power curve; battery power statements conservative here. Filtered variants thin
the cadence — per-variant trade counts disclosed at analysis; the portfolio object, not
per-candidate cells, carries the verdict. Vol-variant candidates on 1d domain:
warmup-reduced band (~11.4 months) disclosed.

## 10. Golden trace (QA derives; developer must NOT generate)

Recipe (fully determined by §3 pins — no RNG): for candidates `C3-USTEC-1D1H-H1X-V00` and
`C3-XAUUSD-1H5M-H2X-V03`: (1) aggregate raw m1 to the LTF grid; (2) walk confirmed LTF
bars from warmup end; while flat compute the trailing quotes: buy limit
`min(Low[t−3..t−1])`, sell limit `max(High[t−3..t−1])` (V03: side rests only if the ±DI
check passes on the latest confirmed HTF bar); (3) scan raw m1 bars within bar t for the
first touch (m1 Low ≤ buy limit → long fill at limit, or m1 Open if it gaps through; m1
High ≥ sell limit → short, symmetric) — expected entry price + side + fill minute; (4)
exit = earlier of (a) first LTF bar open where `Close[t−1]` in profit ≥ 0.5 × current HTF
median-TR ATR(14), (b) open of bar fill_bar+hold; (5)
`SlPrice = entry ∓ 2×HTF median-TR ATR(14)`. QA hand-computes 2–3 events per candidate
(timestamps, side, entry/exit prices from raw m1, SlPrice) and diffs against the emission
before execution sign-off; residual engine-vs-hand fill discrepancies route to the
native-fill physicality tripwire (§7), not silent acceptance.

## 11. Amendments (L-23)

| # | Date | Change | Direction | Running count |
|---|---|---|---|---|
| 1 | 2026-07-11 | Crossed-limit rule pinned (operator elicitation at implementation): passive-only quoting; no market-conversion of crossed quotes | NEUTRAL | 0L/0T/1N |
| 2 | 2026-07-11 | Post-emission integrity fix: censored legs whose entry fill landed inside the never-completed final LTF bar (EntryTime > last grid mark, up to == fence tick) are DROPPED, not booked — candidate gate flagged 28/2,736 for fence/entries-in-grid on exactly these legs (BTCUSD 5m/15m, DE40 15m, UK100 5m); censored legs are NaN-P&L and oracle-invisible, so no selection statistic changes. 4 cells re-emitted under the fixed model. | NEUTRAL | 0L/0T/2N |
| 3 | 2026-07-11 | Physicality tripwire executed against the ENGINE's own m1 feed (zbars cache), 2-bar boundary window: 51/14,400 (0.35%) initial flags, operator-directed investigation root-caused ALL to minute-boundary tick-stamp ambiguity + missing-minute feed gaps (fill = exact touch of last existing bar) — PASS, no untouched-price fill. Local-parquet basis (EU/AP indices ~1 pt, p50 2.4 bps on a minority of bars) recorded as provenance disclosure. Artifact: results/physicality_audit.json | NEUTRAL | 0L/0T/3N |
| 4 | 2026-07-11 | Grid-coverage fix (operator-approved option 1): m1-stamped exits can land after the last interior bar-close of a clipped segment grid (e.g. exit 23:56 vs grid end 23:55 at the search-band edge; gate band 08:01 vs 08:00) — `grid_increments` correctly raised (anti-clamp guard). `clip_grid_covering` (xen.xena.search, also used by certify + final_gate) now appends the first universe bar-close >= segment end, EVENT-DRIVEN: only when the universe's own within-segment fill timestamps exceed the last interior close. Bar-close-fill universes (XENA-001/002) reproduce their original grids exactly — lockstep with the in-flight XENA-001 walk preserved. | NEUTRAL | 0L/0T/4N |

(XENA-001/002 QA-derived pins — binding band table, 14-day purge, TRAIN-only FX pins,
from-scratch clause scoped to entry/model logic with spec-identical shared HTF feature
code — inherited here as design content, not amendments.)

## 12. Gate plan

Ledger state at design: 0/2 slots. Intended spend: **no default gate spend** — a slot is
spent only on operator approval after the certification evidence package + permutation-null
battery + native-fill physicality audit. `new_data_attestation` operator-only, as always.

## 13. Execution + artifacts (deferred)

Execution requires operator approval (and follows XENA-002 sequencing as the operator
directs). When approved: C# batch manifest runner sweeps the manifest through
`tools/ctrader-cli/` in **native-order mode** (real limit orders, engine m1 fills);
emissions → `data/strategy_runs/XENA-003/<candidate_id>/` (fills-based contract,
`positions.parquet` + `cis_trades.parquet`, finite SlPrice). Then: `gate_universe` →
estimand gate → native-fill physicality audit → 12-restart LAHC (search band only) →
`certify_and_rank(registry_path=…)` → operator review. Ledger row at
`docs/signal-registry/xena-runs.md` registered 2026-07-11 (this design); eval_count /
distinct_subsets mandatory at close.

---

## Operational addendum (2026-07-11): EC2 search execution — status + completion runbook

Not a design change. Emission complete (2,736/2,736 incl. Amendment-2 re-emits), candidate
gate PASS, estimand gate PASS (2,777 cells), physicality tripwire PASS (Amendment 3).
Search runs on AWS EC2, shared box with XENA-002 — same instance, IP, SSH, and minimal
loader-payload arrangement as XENA-002's addendum (`i-0a64575c6bfcea2d9`, c7a.8xlarge,
107.20.27.67 at launch).

**Grid-coverage fix (Amendment 4, operator-approved)**: first smoke attempt crashed —
m1-stamped exits land after the last interior bar-close of the segment-clipped grid
(`grid_increments` anti-clamp guard, search.py). Fixed via event-driven
`clip_grid_covering` (search/certify/final_gate); XENA-001/002 grids provably unchanged.
Relaunched clean.

**Status at write (2026-07-11 ~23:30Z)**: 3-restart smoke ladder (rids 100–102) in flight —
8000-leg. F̂@4000: 11.5/13.2/15.4, still climbing steeply (+14–21% over 2000-leg);
acceptance ~50–61% (vs ~9–24% on XENA-001/002) — much richer landscape, note for the
smoke read. Native m1 grids run ~1.6× slower per eval than XENA-002. Production
12-restart LAHC (rids 0–11, budget 16000 default pending operator smoke read) launches
next, in parallel with XENA-002's 12 (24 workers total).

**Monitor**: done count
`ls ~/xen/python/experiments/XENA-003/results/search_restart_*.json | wc -l` (target 12);
smoke logs `~/smoke_XENA-003_r10*.log`.

**When 12/12 done**: same 4-step runbook as XENA-002's addendum (pull → verify
`n_evaluations`/`distinct_subsets`/`charge_costs: false` → terminate the shared box only
after BOTH universes are pulled → local `certify_and_rank` against frozen registry v3
sha256 537d691a…, binding band table folds). Pre-registered reading (§1/§8) applies at
review. Permutation-null battery before any gate consideration; default NO gate spend
(ledger 0/2).

## Operational addendum (2026-07-12): platform migration + budget-procedure restoration

Operator decision. The 2026-07-11 operator-directed 16000 budget cap is **DROPPED**; the
ORIGINAL pre-registered §6 procedure is **restored** (3 smoke restarts on this universe,
budget = iteration where best-F improvement < 1% over the trailing 20% of iterations,
then fixed for the 12 production restarts). This is a restoration, not an amendment.

All prior EC2 search output (c7i/c7a x86, …526 libm lineage) is archived under
`results/archive-ec2-c7i/` and is not comparable to new runs (1-ULP libm caveat,
INFR-007). All three universes rerun from the post-emission stage on ONE new instance —
c8g.12xlarge (Graviton4, aarch64, us-east-1) — which is the sole adjudication platform
for these universes' lifetime (search → certification → permutation battery → final-gate
computation). Pinned parity corpus (`tests/test_xena_fold_parity.py`, pins NOT
regenerated) must PASS on that instance before any search. Rust kernel per INFR-007/008.

**Amendments (2026-07-12, operator-approved after run-1 on c8g):**
1. *Budget read v2*: run-1's literal trailing-20% read fired on transient stalls
   (×1.25 ladder; pinned 767/392 while F̂@34k was ~2.5× higher). Superseded by curve
   read: full ladder to 34k cap; per rid budget = smallest rung with best-F ≥ 99% of
   cap-rung best-F; universe budget = max over the 3 smoke rids. Run-1 search /
   certification / battery artifacts archived as superseded.
2. *L-18 reconciliation tolerance made scale-aware* (`oracle.py` + `xena_fold`):
   `tol = 1e-6 × max(initial_equity, |final_equity|)` — the absolute form cannot hold
   past ~1e12 equity (f64 accumulation; first hit live on XENA-003 smoke, gross
   costless compounding). Numeric outputs unchanged; parity re-proved after rebuild.
3. *Permutation battery v2*: price-coherent re-marking rotation (rotate whole trade
   stream per candidate within the search band, snap to feed mark grid, re-price
   entry/exit from grid opens at new times; EXP-018 random re-timing lineage). Run-1
   rotation kept stale prices → garbled MTM paths → systematically negative permuted
   F̂ even on the RANDOM universe (implementation artifact, not a machinery alarm).
