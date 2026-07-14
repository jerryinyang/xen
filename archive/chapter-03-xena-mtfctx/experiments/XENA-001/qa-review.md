# QA Review — XENA-001 (append-only)

## QA run 1 — 2026-07-10T22:20:40Z — mode: subagent — HEAD ae5a2bf784d05e582030a0bc4fc46c8ff7b5ffbb (dirty: pipeline-config, xena-lane.md, xena-runs.md, INDEX.md modified; XENA-001/, checkpoint-011, cf-mtfctx-001 untracked)

Verdict: **REVISE**

**Scope note:** this is a pre-implementation DESIGN review. No implementation exists yet
(model "written from scratch" pending; C# batch runner is a checkpoint-011 deliverable; no
emissions, no `xena_candidate_gate.json`, no `universe_manifest.json`). The design-fidelity
trace below is therefore design-vs-governing-documents and design-vs-data; the
design-vs-code trace and the golden-trace numeric diff are DEFERRED and BLOCKING for
execution sign-off — a second QA run is mandatory after implementation.

### Design-fidelity trace (design vs governing docs + data)

| Design clause (§ref) | Checked against | Verdict | Notes |
|---|---|---|---|
| Frozen registry sha256 537d691a… (header) | `verify_frozen_registry` run by QA on `python/experiments/INFR-006/results/xena_frozen_registry.json` | MATCHES | Verify passed (no raise); embedded canonical-blob sha = 537d691aaf59…e672a6, identical to design, lane spec, ledger. Note: raw-file sha256 is 437bdf5c… — the pin is the embedded canonical hash, which is what the code checks. |
| X=0.70, F_floor=0.4302, gate=0.0558 GROSS null-P95 (header) | registry contents | MATCHES | X=0.7, F_floor=0.4301969674…, gate_pass_threshold=0.05580535791…, gate_rule "max(0, P95 of GROSS null gate bootstrap P25s) — A-4". Cited, not re-derived. |
| WS-6 power claims §7 (70% @30bps, 94% @40bps, FPR ≤1%@95%) | registry battery_summary | MATCHES | end_to_end 0.70 @30, 0.94 @40, rule_of_three_fpr_bound_95 = 0.01, null cert 2/300. |
| Universe grid §3: 19×4×3×12 = 2,736 | arithmetic + cf-mtfctx-001 | MATCHES | Variant count 1+2+1+3+6+6 = 19 ✓ (combo blocks = 6 each per locked decision). 12 instruments = family basket ✓. |
| Hold-bar mappings §3 | cf-mtfctx-001 shared plane | MATCHES | 1d/1h 24→{12,24,48,96}; 4h/15m 16→{8,16,32,64}; 1h/5m 12→{6,12,24,48} — matches the corrected (non-slip) arithmetic. |
| Vol-regime pin §3 (median-TR ATR(14), window 250, P80/P65, P20/P35) | cf-mtfctx-001 + checkpoint-011 | MATCHES | 250 ∈ [200,300] pinned; hysteresis verbatim; median-TR (not Wilder ATR) ✓. |
| ADX/DI §3 (ADX(14) Wilder, threshold 25, ±DI direction, confirmed ≤t−1, CloseTime) | family + checkpoint | MATCHES | |
| SlPrice §3 (synthetic, k=2, HTF median-TR ATR(14), no live stops) | family locked decision + lane carve-out clarification | MATCHES | Finite-or-REJECT stated; sizing-only. |
| Entry timing §3 vs golden-trace §10 | internal consistency | **DEVIATES (ambiguous)** | §3: "at each LTF bar open … BUY/SELL" (fill at the draw's own bar open). §10: "first draw with \|u\| ≥ 0.5 while flat ⇒ entry at NEXT bar open". Two implementations possible. Issue 1. |
| RNG pin §3 (splitmix64, FNV-1a-64 seed string, u formula, shared stream per SYM×DOM) | L-19 D1 | MATCHES | Regenerable; 36 streams = 12×3 ✓. Note: checkpoint says "per-candidate fixed seeds"; design shares one stream across the 19×4 variants/holds of a cell — deterministic per candidate, and deliberate (variant comparability), so accepted as compliant, disclosed here. |
| Bands §5: common span start 2021-06-02T00:01, end 2024-12-11T08:19 = min 70% fence | data/timebars parquet, computed by QA | MATCHES | Row-count 70% boundaries recomputed with polars on 6/12 instruments: USTEC 2024-12-11T17:33 ✓, GER40 2024-12-11T08:19 ✓ (binding min ✓), BTCUSD 2025-03-12T19:22 ✓, XAUUSD 2024-12-12T04:09 ✓, JP225 2024-12-30T00:01 ✓, EU50 2025-01-29T10:38 ✓. All exact to the minute. Remaining 6 fences all claimed > common end. |
| 50/30/20 interior boundaries §5 | recomputed: exact 50% = 2023-03-08T04:10, 80% = 2024-03-28T16:15 | **DEVIATES (ambiguous)** | Design pre-registers midnight-rounded 2023-03-08T00:00 / 2024-03-28T00:00 ("NEUTRAL, pre-registered"). But frozen layout shape is `SegmentLayout.from_span` — which yields the exact (unrounded) boundaries. Whether code consumes the rounded pins or from_span output is unspecified. Issue 2. |
| Folds §5: n=4 purged, purge 5 calendar days ≥ max hold (96×1h "= 4 days") | arithmetic vs market calendar | **DEVIATES** | 96 one-hour BARS ≠ 96 calendar hours: index CFDs trade ~5 days/week (~22–23h/day), so an H96 1d/1h leg entered late-week spans ≈ 6+ calendar days across a weekend > 5-day purge → fold purge insufficient for the largest hold; §2 "effect-splitting windows non-overlapping" claim not guaranteed. Issue 3. |
| Gate band ≫ block 64 §5 | ~4.6k 1h / ~56k 5m bars | MATCHES | Non-degenerate. |
| money_per_unit pins §4 | recomputed from own m1 timebars | **DEVIATES** | Claimed "TRAIN-median 2023-01→2024-12". QA recomputation: USDJPY median over 2023-01→2024-12 = 147.392 (≠ 147.189 claimed); over 2023-01→2024-12-11T08:19 (analysis end) = 147.193 ≈ claim. So the actual window is 2023-01→analysis-end, mislabeled twice: (a) it is not the stated calendar window, (b) it is not a TRAIN median — it spans TRAIN+ranking+GATE bands (true TRAIN-band median is materially different: 143.5 from 2023 data, 134.8 over the full 2021-06→2024-03 band). AUDUSD/GBPUSD/EURUSD claims are each ~4–5 pips off my 2023-01→2024-12 recomputation, consistent with the same window discrepancy. Issue 4. |
| HK50 pin 0.128205 = 1/7.80 §4 | arithmetic | MATCHES | Peg mid, band disclosed. |
| USD-quoted whitelist §4 (money_per_unit 1.0) | `xen.xena.ingest.USD_QUOTED_CFDS` | MATCHES | USTEC, US500, US2000, US30, XAUUSD, BTCUSD all in {BTCUSD, US2000, US30, US500, USTEC, XAGUSD, XAUUSD}. |
| Commission claims §4 | `xen.evaluation.FTMO_COSTS` | MATCHES | Indices 0 ✓; XAUUSD 0.0014 percent/side ✓; BTCUSD 0.065 percent/side ✓; JP225 contract_size 10 disclosed ✓. `spread_pips` is None for all 12 — consistent with the design's "operator pin required pre-gate" blocker. |
| cost_bps RT column (template §3) | xena-run-design-template.md | MISSING | Template's cost table has a `cost_bps RT` column; design omits it (spreads unpinned so RT cost is incomputable — but the commission-only component could be stated). Issue 5 (minor). |
| Restarts 12, seeds = restart ids, budget from smoke flattening §6 | template §5 (10–15) + lane spec | MATCHES | Budget procedure pre-registered (3 smoke restarts, <1% improvement over trailing 20%). registry_path mandatory stated ✓. |
| Power §9 trade counts | recomputed: P(\|u\|≥.5)=0.5 ✓; 11.6k/(12+2)≈830, /98≈118; 46.4k/10≈4.6k, /66≈700; 139k/8≈17.4k, /50≈2.8k | MATCHES | All ≫ 60-trade WS-6 density; restatement-at-analysis promised. 1d-domain vol-variant warmup (264 HTF bars) disclosed. |
| Gate plan §12: 0/2 slots, default no spend, attestation operator-only | xena-runs.md + lane §gate ledger | MATCHES | No `xena_gate_ledger.json` exists (nothing spent) ✓. |
| Ledger row | docs/signal-registry/xena-runs.md | MATCHES | Registered 2026-07-10, 2,736 cands, sha 537d691a, bands identical to §5, 0/2, OPEN(design). Registration-before-search honored. |

### Golden-trace diff

DEFERRED — no implementation or emission exists. §10 supplies a recipe (correct posture:
developer must not generate expectations) but **zero hand-derived numeric events**.
design-requirements §7 requires 2–3 concrete events; producing them requires walking the
pinned RNG against raw bars, which QA will do at the post-implementation run and diff
against the emission. Execution sign-off is conditional on that diff — and on Issue 1
being resolved first (the trace's entry timestamps depend on which entry-timing reading is
correct).

### Governance & boundary

- Mandatory blocks (design-requirements): MECHANISM+DERIVED ✓ (derived from the random-entry
  object, not a reused stack); OBJECT-IDENTITY ✓; CONTROL block ✓ (universe-is-null, with
  population disjointness, bite via WS-6 MDE curve, non-vacuity via P25/F̂); TRIPWIRE ✓
  (entry-time block rotation — causal alignment-breaking, NOT P&L permutation, honors
  L-14/EXP-012 mean-invariance; vacuity argument stated); HARD/INFORMATIVE split ✓; POWER ✓;
  AMENDMENTS table ✓ (empty, 0L/0T/0N); interpretation bands present as run-level
  MACHINERY-CLEAN/ALARM/FILTER-STRUCTURE — an adaptation of the per-stratum
  SUPPORTED/WASH template, acceptable because the XENA lane's registered object is the run
  and no SUPPORTED claim is constructible from random entries (pre-registered as alarm-only).
- L-21 CONVERSION-PIN: N/A as a screen-conversion (no SPDR screen effect is converted into
  the target; power uses the WS-6 bps curve). money_per_unit pins are the L-21 surface here
  and carry Issue 4.
- L-22: no SUPPORTED/tradability band exists; NET/deployability read explicitly blocked on
  operator spread pins (FTMO_COSTS spread_pips=None confirmed). Compliant with the blocker
  declared. A commission-only deployability read would be a violation — the design forbids it.
- L-23: no amendments; no directional streak. L-24: no per-candidate battery/eligibility
  gates exist by lane principle (every cell enters); the certification battery is the frozen
  WS-6 — clauses N/A at run level, noted.
- Holdout: common AnalysisEndUtc 2024-12-11T08:19 = minimum 70% fence (GER40, verified);
  every per-instrument fence spot-checked sits at or after it → no emission, band, or fold
  can touch any instrument's final 30% ✓. Uniform fence is conservative.
- KB/pitfalls: P-14 escape clause satisfied (new family, holds 0.5–4× HTF span, unit pins
  at design); P-15/L-21 no screen-unit seam; L-19 addressed (2,736-candidate battery, no
  single-seed read); EXP-013 carve-out correctly N/A (market orders). Not a re-run of any
  ledger dead end.
- XENA clauses (a–e): (a) registry verified by QA, thresholds byte-match, never re-derived ✓;
  (b) SlPrice finite-per-leg pinned; candidate-gate artifact pending emission (must exist and
  pass before search) — PENDING, execution-gate condition; (c) bands pre-registered, folds
  confined to ranking band, disjoint from search ✓ (subject to Issues 2–3); (d)
  new_data_attestation operator-only, stated twice ✓, none authored; (e) ledger 0/2, no
  failed subsets, no gate approval sought ✓.
- No Python strategy backtest anywhere in the design ✓. `check_no_local_accounting`: N/A —
  no `python/experiments/XENA-001/code` exists yet; must be run at the post-implementation
  QA pass.
- No DEVIATIONS block present and none needed yet.

### What was NOT checked (honest limits)

- No code exists: design-to-code fidelity, golden-trace numeric diff, local-accounting scan,
  candidate gate, and manifest consistency are all deferred to QA run 2 (post-implementation,
  pre-execution — mandatory).
- 6 of 12 per-instrument 70% fences recomputed (USTEC, GER40, BTCUSD, XAUUSD, JP225, EU50);
  the other 6 accepted on the verified pattern (same row-count convention, all > common end).
- Operator spread pins do not exist yet (by design; blocking for NET/deployability only).

### Issues

1. **[REVISE — quant-designer] Entry-fill timing ambiguity.** design.md §3 ("at each LTF bar
   open, if flat: draw … BUY/SELL") vs §10 ("first draw with |u| ≥ 0.5 while flat ⇒ entry at
   next bar open"). A developer can implement fill-at-draw-bar-open or fill-at-next-bar-open;
   both are causal but they produce different traces and different filter-mask alignment.
   Required: one sentence pinning the exact bar of the fill (and confirming the filter mask is
   evaluated against the HTF state confirmed as of that same decision bar).
2. **[REVISE — quant-designer] Band-boundary source ambiguity.** §5 pre-registers
   midnight-rounded interior boundaries (2023-03-08T00:00 / 2024-03-28T00:00) while the frozen
   layout shape is `SegmentLayout.from_span` 50/30/20, whose exact outputs on this span are
   2023-03-08T04:10 and 2024-03-28T16:15. Required: state explicitly whether the code consumes
   the rounded pinned timestamps (as an explicit-boundaries layout) or `from_span` (in which
   case the pinned table must be corrected to the exact values). Two implementations currently
   possible; the rounding itself is NEUTRAL and fine — the ambiguity is not.
3. **[REVISE — quant-designer] Purge < max hold in calendar time.** §5 claims purge
   "5 calendar days ≥ max hold horizon (96 × 1h = 4 days)". 96 hourly bars on a ~5-day/week
   index CFD spans up to ~6+ calendar days across a weekend, so an H96 leg opened near a fold
   boundary can straddle the 5-day purge → ranking-fold overlap for the largest-hold
   candidates, contradicting §2's non-overlap declaration. Required: raise the purge to the
   maximum CALENDAR span of 96 LTF bars (≈ 7 calendar days is safe for all domains), or
   justify with the actual bar calendar.
4. **[REVISE — quant-designer] money_per_unit pin window mislabeled and not reproducible as
   stated.** §4 labels the FX pins "TRAIN-median 2023-01→2024-12". Recomputed from the named
   m1 data: median(2023-01→2024-12) = 147.392 ≠ 147.189 (USDJPY); the claimed value matches
   median(2023-01→2024-12-11T08:19) = 147.193. So (a) the stated window is not the window
   used, (b) the window used is not TRAIN — it includes the ranking and GATE bands (mild
   forward information in a gate-verdict-bearing pin; the true TRAIN-band median differs
   materially, 134.8–143.5), (c) AUDUSD/GBPUSD/EURUSD pins show the same ~4–5-pip
   discrepancy pattern. These pins are deployability-verdict-bearing (L-21: wrong pin = wrong
   informational block). Required: pre-register the exact window and data file per pin,
   recompute all four from data, and either use a genuinely pre-gate window or declare why a
   through-analysis-end conversion rate is acceptable for a static unit conversion (with the
   TRAIN-only value disclosed alongside).
5. **[Minor — quant-designer] Template deviation: `cost_bps RT` column omitted** from §4
   (xena-run-design-template §3). State at least the commission-only RT bps per instrument
   now; complete with spread once the operator pins land.
6. **[Blocking condition, not a defect] Post-implementation QA run required** before
   execution sign-off: design-to-code trace, hand-computed golden-trace events (2–3 per named
   candidate, from the pinned RNG + raw bars) diffed against a smoke emission,
   `check_no_local_accounting`, candidate-gate artifact passing and non-stale, manifest =
   2,736 rows matching §3.

### Why REVISE and not APPROVE/REJECT

No holdout contact, no causality violation, no registry tampering, no agent-authored
attestation, no re-run of a closed dead end — nothing REJECT-shaped. But Issues 1–4 are
verdict- or integrity-adjacent (fold non-overlap is an integrity declaration; unit pins are
deployability-verdict-bearing; two clauses admit dual implementations), so this cannot be
approved as-is. All four are small, surgical design edits; re-QA after amendment (each edit
must land in §11 with a LOOSER/TIGHTER/NEUTRAL tag — all four look NEUTRAL/TIGHTER).

## QA run 2 — 2026-07-10T22:27:13Z — mode: subagent — HEAD ae5a2bf784d05e582030a0bc4fc46c8ff7b5ffbb (dirty: pipeline-config, xena-lane.md, xena-runs.md, experiments-docs/INDEX.md modified; XENA-001/, checkpoint-011, cf-mtfctx-001 untracked)

Verdict: **REVISE** (one remaining issue — purge arithmetic; all other run-1 findings resolved)

**Scope:** re-review of design.md after the run-1 REVISE (amendments 1–4, §11). Still a
pre-implementation DESIGN review; run-1 Issue 6 (mandatory post-implementation QA run)
remains in force regardless of the verdict here.

### Run-1 finding resolution trace

| Run-1 issue | Amendment | Verdict | Evidence (recomputed by QA, not recalled) |
|---|---|---|---|
| 1. Entry-fill timing ambiguity (§3 vs §10) | #2 (NEUTRAL) | **RESOLVED** | §3: "market order fills at that SAME bar's open (the decision bar's open … no extra one-bar delay)"; §10 step (3): "entry at THAT bar's open (same-bar-open fill, §3)". One reading only; filters pinned to confirmed bars ≤ t−1 at the same decision bar — causal and internally consistent. |
| 2. Band-boundary source ambiguity | #3 (NEUTRAL) | **RESOLVED** | §5: "The table above IS the binding band definition … `SegmentLayout` constructed directly from these pre-registered ns timestamps … `from_span` is not re-run at execution time." Rounded 00:00 interior boundaries are now the single source; no dual implementation remains. |
| 3. Purge < max hold | #1 (TIGHTER, 5→10 days) | **NOT RESOLVED** | §5 claims 10 calendar days "covers the 96 trading-hour max hold across weekends/holidays". QA recomputed the calendar span of 96 consecutive trading hours on GER40 m1-derived hourly bars over the ranking band (2023-03-08→2024-03-28): **max = 11.375 calendar days** (entries 2023-12-22 → exit 2024-01-03, Christmas/New-Year closure) and 10.33 days around Easter 2023 (2023-03-31→2023-04-11); **40 hourly entry slots exceed 10 days**. The declared coverage claim is arithmetically false in the holiday tail. (Run 1's own "≈7 days is safe" estimate was also wrong — measured, not estimated, this time.) Issue 1 below. |
| 4. money_per_unit pins mislabeled / not reproducible | #4 (NEUTRAL) | **RESOLVED** | Recomputed with polars, median Close, file start → 2024-03-28T00:00 (strict, matching the binding 00:00 boundary): USDJPY (`timebars_usdjpy_20230103_…`) = **143.516** → 1/143.516 = 0.0069679 ≈ pinned 0.006968 ✓; GBPUSD (`timebars_gbpusd_20230103_…`) = **1.25292** ✓ exact; AUDUSD = **0.66197** ✓ exact; EURUSD (`timebars_eurusd_20230102_…`, start 2023-01-02 as stated) = **1.08418** ✓ exact. Window is genuinely pre-gate (ends at ranking-band end, no gate contact); files named per pin; fully reproducible. |
| 5. `cost_bps RT` column missing | #4 | **RESOLVED** | Column present in §4. XAUUSD: FTMO_COSTS commission 0.0014 percent per_side → RT 0.0028% = **0.28 bps** ✓; BTCUSD: 0.065 percent per_side → RT 0.13% = **13.0 bps** ✓; indices 0 + spread ✓. Values checked against `xen.evaluation` FTMO_COSTS directly. |

### Whole-document rescan (new-inconsistency check)

- Revisions touched §3, §4, §5, §10, §11 only; re-read against
  `docs/references/xena-run-design-template.md` and `quant-designer/references/design-requirements.md`
  structure: all mandatory blocks still present and unchanged from run 1's verified state
  (mechanism/derived, object-identity, control, tripwires, hard/informative, power, bands,
  gate plan, golden-trace recipe).
- §4 window label ("file start → 2024-03-28, end of ranking band, no gate-band contact") is
  now consistent with §5's binding 2024-03-28T00:00 boundary and with the recomputation ✓.
- §10 recipe now cites §3's same-bar-open pin explicitly — no drift reintroduced ✓.
- Minor note (informational, no action forced): FTMO_COSTS code comment for BTCUSD reads
  "0.065% of notional per trade" while the machine-readable fields say
  `commission_basis: per_side`; the design follows the fields (13 bps RT). Pre-existing code
  comment ambiguity, not a design defect.
- Minor note: §5 pins n=4 contiguous purged folds but not the fold-boundary convention
  (equal-bar vs equal-calendar split of the ranking band). Under an equal split the third
  boundary lands ≈ mid-December 2023 — inside the measured worst-case purge-violation zone,
  which sharpens Issue 1. Recommend pinning the fold boundaries (or the split convention)
  in the same amendment.

### Amendment ledger (L-23)

Entries 1–4 present, dated, each tagged: 0L/1T/3N running counts verified correct at each
row (1T; 1T1N; 1T2N; 1T3N). Direction tags plausible: #1 TIGHTER (purge widened) ✓; #2/#3
NEUTRAL (disambiguations, no gate-surface movement) ✓; #4 NEUTRAL (pin window corrected to
pre-gate; arguably TIGHTER, NEUTRAL acceptable) ✓. No LOOSER entries; no one-directional
loosening streak — nothing to flag at the execution gate.

### Issues

1. **[REVISE — quant-designer] Purge still < max hold in calendar time (holiday tail).**
   §5 "purge = 10 calendar days (covers the 96 trading-hour max hold across
   weekends/holidays; Amendment-1)". Measured on GER40 hourly trading bars in the ranking
   band: max calendar span of a 96-bar 1h hold = 11.375 days (Christmas/New Year 2023),
   10.33 days (Easter 2023); 40 entry slots exceed 10 days. Required: raise the purge to
   ≥ 12 calendar days, or (cleaner and exact for all domains) define the purge in BAR time
   as ≥ 96 LTF bars, and re-verify §2's non-overlap claim. Recommend also pinning the fold
   boundary convention (see minor note). Log as Amendment-5 with direction tag.

### Standing condition (restated from run 1)

Any APPROVE on this design remains **design-stage only**. A post-implementation QA run is
mandatory before execution sign-off: clause-by-clause design-to-code trace, hand-derived
golden-trace events (2–3 per named candidate from the pinned RNG + raw bars) diffed against
a smoke emission, `check_no_local_accounting`, passing non-stale `xena_candidate_gate.json`,
and a 2,736-row manifest matching §3.

### Why REVISE

Findings 1, 2, 4, 5 of run 1 are genuinely resolved — verified by recomputation, not by
reading the amendment table. Finding 3's fix is directionally right but empirically short:
the design's own coverage claim is false for ~40 holiday-adjacent entry windows, and the
integrity declaration in §2 ("windows non-overlapping") inherits that falsity. One surgical
edit (purge ≥ 12 calendar days or ≥ 96 LTF bars, + Amendment-5) and this is APPROVE-ready
at design stage.

## QA run 3 — 2026-07-10T22:35:57Z — mode: subagent — HEAD ae5a2bf784d05e582030a0bc4fc46c8ff7b5ffbb (dirty: pipeline-config, xena-lane.md, xena-runs.md, experiments-docs/INDEX.md modified; XENA-001/, checkpoint-011, cf-mtfctx-001 untracked)

Verdict: **APPROVE (design-stage only)**

**Scope:** re-review after the run-2 REVISE (Amendment-5, §11). Still a pre-implementation
DESIGN review; the post-implementation QA run (run-1 Issue 6 / run-2 standing condition)
remains mandatory before execution sign-off.

### Run-2 finding resolution trace

| Run-2 issue | Amendment | Verdict | Evidence (recomputed by QA, not recalled) |
|---|---|---|---|
| 1. Purge < max hold (holiday tail) | #5 (TIGHTER, 10→14 days; fold boundaries pinned 2023-06-12 / 2023-09-16 / 2023-12-22) | **RESOLVED** | Re-derived on GER40 (`timebars_de40_20210602_…`), m1 truncated to distinct trading hours, ranking band 2023-03-08→2024-03-28: max calendar span of 96 consecutive 1h trading bars = **11.375 days**, worst window starting 2023-12-22 (year-end closure) — reproduces run 2's measurement exactly; **0 entry slots exceed 14 days**. 14-day purge covers the measured worst case with 2.6 days of margin. |
| (run-2 minor note) fold-boundary convention unpinned | #5 | **RESOLVED** | Boundaries now pinned explicitly at 00:00 UTC; spacing check: 386-day ranking band, boundaries at +96/+192/+289 days — consistent with the declared "equal calendar quarters". No convention ambiguity remains. |

### Independent purge/fold checks (scope items a–c)

- **(a) 14 days ≥ worst 96-trading-hour span:** verified above (11.375 d, re-measured with
  polars, not taken from run 2's text).
- **(b) Fold non-degeneracy** with pinned boundaries + 14-day post-boundary purges, GER40
  1h bars in-band: fold 1 (2023-03-08→2023-06-12) = **1,478** bars; fold 2 (2023-06-26→
  2023-09-16) = **1,358**; fold 3 (2023-09-30→2023-12-22) = **1,341**; fold 4 (2024-01-05→
  2024-03-28) = **1,345**. Every fold ≫ block 64 (and ≈12× larger on the 5m grid) —
  non-degenerate for scoring.
- **(c) §2 non-overlap declaration:** a max-hold (H96 1h) leg entered at the last bar
  before any fold boundary exits ≤ 11.375 calendar days later, strictly inside the 14-day
  purge (worst case: entries just before 2023-12-22 exit ~2024-01-03; fold-4 scoring starts
  2024-01-05). "Folds purged ≥ max hold horizon" now holds as measured, not merely claimed.

### Amendment ledger (L-23)

5 entries, dated, each direction-tagged; running counts verified row-by-row:
0L/1T/0N → 0L/1T/1N → 0L/1T/2N → 0L/1T/3N → **0L/2T/3N** — arithmetic correct.
#5 TIGHTER is the right tag (purge widened, boundaries pinned; no gate-surface loosening).
No LOOSER entries; no one-directional loosening streak — nothing to flag at the execution
gate.

### Whole-document consistency scan

- Amendment-5 touched §5 and §11 only; §2's non-overlap declaration, §3 pins, §4 pins,
  §6–§10, §12–§13 unchanged from the run-2-verified state — re-read, no drift introduced.
- §5 purge text ("14 calendar days … measured worst 96-trading-hour span at 11.375 d …
  Amendment-5") is internally consistent and matches this run's independent measurement.
- All run-1 findings (1, 2, 4, 5) remain resolved as verified in run 2; run-2's single
  finding and its minor note are resolved above. **No open findings from runs 1–2 remain.**
- Registry pin, band table, ledger row, gate plan (0/2, default no spend, attestation
  operator-only): unchanged and previously verified — not re-litigated.

### Issues

None.

### Standing condition (restated — binding)

This APPROVE is **design-stage only** and does not authorize execution. A
post-implementation QA run is mandatory before execution sign-off, covering:
clause-by-clause design-to-code trace; hand-derived golden-trace events (2–3 per named
candidate from the pinned RNG + raw bars, expectations from the design, never from the
implementation) diffed against a smoke emission; `check_no_local_accounting` on the
experiment code; a passing, non-stale `xena_candidate_gate.json`; and a 2,736-row
`universe_manifest.json` matching §3. Operator spread pins remain a blocking precondition
for the final-gate NET leg and any deployability read (L-22). Execution remains the
operator's gate.

### Why APPROVE

Every prior finding is closed by independent recomputation, not by reading the amendment
table: the purge now exceeds the measured (not estimated) worst-case hold span with margin,
the pinned folds are non-degenerate, §2's integrity declaration is true as measured, and
the amendment ledger is arithmetically and directionally correct with no loosening streak.
Nothing REJECT-shaped exists (no holdout contact, no causality violation, no registry
tampering, no agent-authored attestation). Design is ready for implementation.

## QA run 4 — 2026-07-10T23:32:25Z — mode: subagent — HEAD ae5a2bf784d05e582030a0bc4fc46c8ff7b5ffbb (dirty: Xen.cs, pipeline-config, xena-lane.md, xena-runs.md, experiments-docs/INDEX.md modified; MtfCtxRandomModel.cs, XENA-001.conf, gen_xena001_manifest.py, XENA-001/, checkpoint-011, cf-mtfctx-001 untracked)

Verdict: **APPROVE (implementation-stage — clears the way to the operator execution gate; execution itself remains operator-approved)**

**Scope:** POST-IMPLEMENTATION review required by the run-3 standing condition. Artifacts:
`StrategyHost/MtfCtxRandomModel.cs`, `Xen.cs` wiring, `tools/ctrader-cli/experiments/XENA-001.conf`,
`tools/ctrader-cli/experiments/gen_xena001_manifest.py` + `data/strategy_runs/XENA-001/universe_manifest.json`,
and the XAUUSD 1h smoke emission (76 candidate dirs, analysis70 slice, fence 2024-12-11T08:19Z).
All expectations derived from design.md; RNG/feature reference values reimplemented in
independent Python from the design's constants, never from the C# file.

### Design-fidelity trace (design §3 pins → MtfCtxRandomModel.cs)

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| RNG: FNV-1a-64 seed of `XENA-001/C1/<SYM>/<DOM>` (§3) | MtfCtxRandomModel.cs:129-130, 400-409 | MATCHES | Offset 14695981039346656037 / prime 1099511628211 verbatim; seed string format exact (ctor + metadata line 466); ASCII-only inputs so the `(byte)ch` cast is lossless. |
| RNG: splitmix64 + u formula (§3) | :411-420 | MATCHES | 0x9E3779B97F4A7C15 / 0xBF58476D1CE4E5B9 / 0x94D049BB133111EB, shifts 30/27/31; u = ((x>>11)·2⁻⁵³)·2−1. Bit-identical to my independent Python stream (golden trace below). |
| One draw per LTF bar, always consumed; shared stream per (SYM,DOM) feed (§3) | :160-162 | MATCHES | `NextUniform()` unconditional per OnBar, single `_rngState` shared by all 76 candidates. |
| lambda=2 cutoff: SELL u≤−0.5, BUY u≥+0.5 (§3) | :42, :162 | MATCHES | |
| Same-bar-open fill (Amendment-2) (§3/§10) | :170-177 | MATCHES | `EntryFill = bar.Open` on the decision bar; no delay. |
| Hold exit: market at open after hold bars; exit before entry decision (§3) | :167-171 | MATCHES | `_barIndex − EntryBarIndex == HoldBars` → exit at bar.Open, processed before the same bar's entry. Same-bar re-entry possible — see Interpretations (i). |
| Hold grids per domain (§3) | :115-125 | MATCHES | 60→1440 ⇒ {12,24,48,96}; 15→240 ⇒ {8,16,32,64}; 5→60 ⇒ {6,12,24,48}; other domains throw. |
| 19 variant filters (§3) | :204-233 | MATCHES | V00 pass-all; V01 ADX<25; V02 ADX≥25; V03 DI (long iff +DI>−DI, short iff +DI<−DI); V04–06 vol LOW/MID/HIGH; V07–12 vol×ADX; V13–18 +DI. All gated on their own feature readiness. Combo ordering — see Interpretations (iv). |
| median-TR ATR(14), mean of two middles (§3) | :281-291 | MATCHES | Sorted 14-window, (s[6]+s[7])/2; verified numerically (golden trace, 6+ dp). |
| Vol percentile: 250 prior values, strictly-below count (§3) | :44, :336-372 | MATCHES | History excludes current (enqueue after ranking); strict `<`; window 250. |
| Vol hysteresis + initial label (§3) | :346-367 | MATCHES | Initial: >P80 HIGH / <P20 LOW / else MID; HIGH exits <P65, LOW exits >P35, MID enters at P80/P20; HIGH→LOW only via <P20 (and symmetric). Reproduced independently: label sequence consistent with emitted V04–V06 trade pattern. |
| Wilder ADX/DI, period 14, threshold 25 (§3) | :293-331 | MATCHES | 14-sum init then Wilder smoothing; DI = 100·smDM/smTR; ADX = 14-DX average then Wilder. First ADX at ~29th HTF bar ≈ design's "~28". Verified to 6 dp in V03 trace. |
| SlPrice = entry ∓ 2×HTF medATR, sizing-only, finite (§3) | :41, :177 | MATCHES | `bar.Open − side·2·_medAtr`; no stop orders exist anywhere in the model; entry blocked until `_medAtrReady` ⇒ finite on every leg (gate stop_contract passed on all 5 sampled candidates). |
| Warmup suppression per variant (§3) | :170-171, :207-226 | MATCHES | All entries require `_medAtrReady` (SlPrice finiteness); ADX/DI variants add `_adxReady`; vol variants add `_volReady`. Vol warmup 15+250 = first label at HTF bar 265 — measured: 570 daily bars → 306 labelled = 570−264, matching §3's "264 HTF bars" exactly. |
| Censoring at fence (§13) | :423-449 + StrategyHostRunner.cs:27,45 + HoldoutFence.cs | MATCHES | Runner stops feeding at CloseTime ≥ fence (last grid bar 2024-12-11T08:00 < 08:19); open legs censored at Dispose with exit mark = last bar's open, RealizedBps NaN, `censored_end`, Censored=1 (1 censored leg observed in V00-H1X). |
| Registration/disposal (§13) | Xen.cs:24, 357-360, 143 | MATCHES | Enum ordinal 2; model constructed with SymbolName/DomainMinutes/output root/fence; `(_strategyModel as IDisposable)?.Dispose()` triggers per-candidate emission. |

### Causality audit

- **HTF bucketing (stock aggregator bypassed):** bucket key `(CloseTime_seconds − 1) / (htfMinutes·60)`
  (:151) is byte-identical to `BarAggregator.BucketKey` (BarAggregator.cs:101-110) — same
  boundary-labelling convention, no off-by-one. Features are updated ONLY on key change and
  ONLY from the completed bucket (:152-156); the current bar is appended AFTER the update
  (:158), so a bucket containing the current bar can never reach features before that bar's
  decision. The bypass rationale (BarAggregator's strict m1 source-count assumption discards
  LTF-built HTF buckets; sessions <24h never reach strict count) is real — verified against
  BarAggregator.cs:75-76.
- **No forming-bar read:** decision at bar t uses the exogenous draw, HTF state confirmed
  ≤ t−1, and past candidate state; bar t's OHLC is touched only as `bar.Open` for fills and
  as grid storage after decisions. Entry features (:178-182) copied from confirmed HTF state.
- **Fence:** runner-side `ShouldStopBeforeProcessing` on both source and domain bars +
  `AssertCanEmit` on every emitted record; model-side grid ends before fence; ingest gate's
  fence check passes.
- gate_candidate causality check (marks monotone, entries in grid, entry≤exit): pass on all
  sampled candidates.

### Golden-trace diff (QA-derived; RNG + features reimplemented from design constants)

`C1-XAUUSD-1D1H-H1X-V00`, smoke feed (grid 10,416 1h bars, 2023-01-03→2024-12-11T08:00):

| # | Expected (derived) | Emitted | Verdict |
|---|---|---|---|
| 1 | ENTRY 2023-01-24T03:00 SELL @1935.80, SlPrice 1986.84 (medATR 25.52), exit 2023-01-25T06:00 @1928.49, 24 bars | identical | MATCH (float-exact) |
| 2 | ENTRY 2023-01-25T06:00 BUY @1928.49, SlPrice 1879.08 (medATR 24.705), exit 2023-01-26T09:00 @1942.96 | identical | MATCH (float-exact) |
| 3 | ENTRY 2023-01-26T16:00 SELL @1932.82, SlPrice 1982.23, exit 2023-01-27T19:00 @1928.60 | identical | MATCH (float-exact) |

Extension (DI/ADX numeric coverage): `C1-XAUUSD-1D1H-H1X-V03` first 3 entries derived with an
independent Wilder DI/ADX implementation — 2023-02-10T01:00 / 02-13T04:00 / 02-14T10:00, all
SELL (masked: −DI>+DI throughout), fills 1862.56/1861.66/1860.23, SlPrice 1916.04/1915.14/1907.96,
+DI/−DI/ADX match emitted `HtfPlusDi/HtfMinusDi/HtfAdx` to 6 decimal places. **6/6 events exact;
no mismatch in timestamp, side, fill, SlPrice, or features.**

### Gates & governance

- **gate_candidate** (5 candidates: V00, V03 DI, V04 vol, V07 combo, V13 combo+DI on H1X/H2X):
  V00 + V03 blocking_pass=true (404/364 trades, fence/causality/stop/fill-consistency/oracle-smoke
  all pass, oracle deterministic). V04/V07/V13 FAIL non_empty with **0 trades** — see V07 analysis.
- **V07 zero-trade behaviour = legitimate masking, not a bug.** Independent recomputation of the
  vol label over the smoke grid (design pins: 250-prior strict-below rank, hysteresis): 306
  labelled daily bars, label counts {HIGH 161, MID 145, LOW 0}; minimum percentile 0.22 — the
  LOW entry threshold (<0.20) is never crossed on this slice (2024 gold-rally vol regime, and the
  analysis70 slice starts 2023-01 so vol warmup consumes ~1 year). Exactly the five LOW-conditioned
  variants (V04, V07, V08, V13, V14) are empty across all 4 holds; every other variant trades with
  monotone masking (V00 ≥ V01/V02, etc.). Consistent, causal, correct.
- **estimand_validation.validate_run** on V00 + V03: schema ok, fence ok, per-bar vs per-leg
  reconciliation |diff| ≈ 7e-13 bps (tol 1.0) — pass.
- **check_no_local_accounting("python/experiments/XENA-001")**: ok, no banned defs. No Python
  strategy backtest anywhere in the experiment.
- **Manifest**: 2,736 rows ✓; IDs unique ✓; run_dir = lowercase ID ✓; per-symbol
  (cost_bps, money_per_unit) match §4 exactly (0.28 XAUUSD, 13.0 BTCUSD, 0 indices; JPY 0.006968,
  AUD 0.66197, EUR 1.08418 on STOXX50+DE40, GBP 1.25292, HK50 0.128205, USD-quoted 1.0);
  registry_sha256 = 537d691a…e672a6 = design pin ✓; analysis_end_utc = 2024-12-11T08:19:00Z ✓.
- **Conf**: 12 symbols ✓ / 3 domains (1h, 15m, 5m) ✓; ANALYSIS_END uniform 2024-12-11T08:19:00Z
  for all 12 = §5 ✓ (BACKTEST_END 08:20, just past fence — fence enforcement is runner-side);
  STRATEGY_VALUE="2" = XenStrategy.MtfCtxRandom ordinal (MaCrossover 0, Donchian20 1) ✓.
- **Frozen registry re-verified this run**: `verify_frozen_registry` passes; X=0.7,
  F_floor=0.43019696…, gate=0.05580535… byte-match the design header; thresholds nowhere
  re-derived in the new code (grepped: model and generator contain no threshold math).
- Gate ledger: still 0/2, no spend, no agent-authored attestation anywhere in new artifacts ✓.

### Interpretations declared in the model header (classification)

1. **Hold-exit-before-entry (same-bar re-entry possible)** — FAITHFUL implementation choice.
   §3 says exit "at bar open after hold-period bars" and entry "if flat"; processing exit first
   makes the candidate flat for that bar's draw. Only observable consequence: measured cycle ≈
   hold+1 bars vs §9's estimate ≈ hold+2 (V00-H1X: 404 trades ≈ (10416−360)/404 ≈ 24.9 bars/cycle)
   → slightly MORE trades than the power section assumed — power statement stays conservative.
   No sign-off required.
2. **HTF map 60→1440 / 15→240 / 5→60** — FAITHFUL; these are exactly the three registered
   domain pairs (§3, family doc); any other domain throws.
3. **Session-tolerant in-model HTF buckets** — FAITHFUL and necessary (stock BarAggregator
   assumes m1 sources and strict counts; it would discard every LTF-built HTF bucket). Same
   bucket-key convention as the aggregator, completed-buckets-only, deterministic. Verified
   numerically end-to-end via both golden traces. No sign-off required.
4. **V07–V12 combo ordering** (LOW,<25)(LOW,≥25)(MID,<25)(MID,≥25)(HIGH,<25)(HIGH,≥25) —
   the code comment at :214 attributes this to "design §3", but §3 does NOT pin an ordering
   (nor does the family doc or checkpoint). This is a developer labeling choice within the
   pinned 6-combo block: benign (all 6 combos present once; V13–18 mirror it; semantics
   recoverable from code + emissions), but the attribution is inaccurate. Recorded here as the
   authoritative ordering pin; not verdict-bearing; no code change required.

### Issues

None blocking. Two notes for the operator at the execution gate:

1. **[Note — operator, execution gate] Zero-trade candidates vs the universe gate.**
   `gate_universe` requires EVERY manifest candidate non-empty (`blocking_pass` only if all
   pass; ingest.py:259-288), while design §3 declares "every cell enters". If, on the FULL
   band (2021-06 start — the smoke used the shorter analysis70 slice), any LOW-conditioned
   candidate legitimately never trades on some instrument, the universe gate will fail
   blocking. The documented resolution (remove the candidate from the manifest, rerun
   gate_universe — never silent thinning) is a universe change: it must be logged as a design
   amendment (L-23, direction tag) with the legitimacy evidence (vol-label occupancy recompute,
   as done here for the smoke). Fail-safe direction; nothing to fix pre-emptively.
2. **[Note — record] Candidate IDs use broker symbols** (DE40, STOXX50) rather than the
   design §3 display names (GER40, EU50). Consistent across conf, model emissions, and
   manifest, with the correct EUR money_per_unit on both; design §5 already aliases
   GER40/DE40. Naming interpretation only.

Standing preconditions unchanged from run 3: operator spread pins before any NET/deployability
read (L-22); full-run `xena_candidate_gate.json` must pass (and be non-stale) before search;
`new_data_attestation` operator-only; execution remains the operator's gate.

### Why APPROVE

Every mandatory check was performed independently: 6/6 golden-trace events (two candidates,
two filter classes) match float-exactly against expectations derived solely from the design's
pinned constants and raw emitted bars; the clause-by-clause trace found no DEVIATES/MISSING
against §3; the HTF-bucketing bypass is causally clean and key-convention-identical to the
stock aggregator; zero-trade variants are proven (not assumed) to be legitimate masking;
manifest, conf, registration, accounting boundary, and frozen-registry checks all pass. The
three shipped failure shapes (frozen computation, anchor drift, confounded comparator) were
looked for specifically and are absent — features roll per HTF bucket, the fence and band
pins are consumed as registered, and all 76 candidates share one draw stream by construction.
