# INFR-020 — Design: multi-timeframe signed-bar apparatus (Stage-I, for SPDR-009 D6)

**Item:** INFR-020 · **Family:** CF-SIGAUC-001 (apparatus, not a hypothesis) · **Checkpoint:** 015 §D6 · **Lane:** INFR (Stage-I apparatus)
**Status:** **COMPLETE — QA Run 10 APPROVE; operator accepted pin manifest `5f170b71…`
(2026-07-22).**
**Authorised by:** operator decision **D6** (2026-07-21) — `docs/experiments-docs/checkpoints/2026-07-21-015-signed-value-absorption-screen/design.md` §D6.
**Purpose:** supply the apparatus SPDR-009's four-pair grid needs and cannot build for itself — per-timeframe seasonal baselines, per-(symbol, timeframe) class thresholds, 1h/4h session construction, and the generalised initial-balance and contact-zone scale objects. **This prerequisite has landed; SPDR-009 implementation is next.**
**Source (NORMATIVE):** `SIGNAL-SIGNED.md` A5 (seasonal residual normalisation; Δ/V and |Δ| fitted separately), A7 (anchor selection), A8 (the taker split is measured), §2.1 (per-level Δ barred), §2.3 — **as amended by Addendum v1.1** (§2.7 anchor vocabulary binds every anchor this item freezes).
**Predecessor pins consumed:** `INFR-017/results/seasonal_baselines.parquet` `1b7244c8…` · `column_pins.json` `e3b9fd9b…` · `INFR-018/results/instrument_registry.json` `5c386984…` · catalog fence `35d3375e…` · `INFR-011/artifacts/admission-ledger.jsonl`.
**Revision:** 7 (post-implementation QA run 9: AMENDMENT-22 — formation provenance is mandatory
for every level kind, including prior-session levels overlapped by a D4 straddling bar).
Prior: 6 (AMENDMENT-16…21 — shared candidate/availability rules, self-made IB-edge exclusion,
emitting-path assertions, 1m thresholds and full battery).
Prior: 5 (closes QA run 6/7 residuals). Prior: 4 (closes QA run 3 residuals S-1…S-7). Prior: rev 2 zero-fill withdrawn after it manufactured the absorption signature (QA-2 R-2); rev 3 incomplete propagation of that withdrawal. This revision propagates fully, derives gap days from staging, and publishes measured universe coverage + activity conditioning.

---

## §0 Scope fence

| | |
|---|---|
| **Produces** | (W2a) window-integrity classification (`COMPLETE` / `NO_TRADE_PARTIAL` / `GAP_CONTAMINATED`) — **no fabricated bars**; (W2b) a signed-aware LTF bar aggregator; (W1) seasonal baselines per instrument for **5m, 15m, 1h**; (W3) class residual thresholds per (symbol, timeframe); (W4) session/anchor construction for **1h**/**4h** plus the generalised IB rule; (W5) contact-zone scale census, **count-only**. All hash-pinned. |
| **Must NOT produce** | **any forward return, excursion, hold outcome, or contrast.** No P&L, no hypothesis, no verdict. Must not alter the frozen 1-minute baselines or the INFR-018 registry, race or select any anchor, touch TEST or holdout, attribute Δ per level (card ban 2), or define an accounting primitive. |
| **Why the outcome ban is load-bearing** | SPDR-009 freezes its event definition (τ per pair, pool cuts) against artifacts this item emits. If INFR-020 ever computed an outcome, every downstream freeze would be outcome-informed — the defect QA caught at SPDR-009 QA-1 I-15. |
| **Band** | **DESIGN only** `[2021-06-29T06:53Z, 2023-03-01Z)` for every fit, threshold, and census — **including W5** (QA-1 I-1: an undeclared W5 band would let τ be frozen against CONFIRM-informed counts). CONFIRM is read for coverage reporting only, never for fitting or census. TEST/holdout never read. |
| **Counted reads / slots** | 0 / 0 |
| **Universe** | the **194** instruments with a fitted A5 1-minute baseline. Others are reported uncovered, never silently dropped. |

### Applicability of standard design blocks (each N/A justified — QA-1 I-7)

| Block | Status |
|---|---|
| §1 mechanism statement | **N/A with reason — filled as a PURPOSE statement (§1).** A mechanism statement names a market regularity and derives an estimand from it. This item measures no effect and has no estimand; asserting a mechanism here would be false precision. What replaces it: §1 states what SPDR-009 cannot do without this apparatus and why each piece is required. |
| §2 object identity | **APPLIES and is filled (§1.1)** — not N/A. W5's "candidate event bar" must be *the same object* as SPDR-009's event bar, or τ is frozen against a population the screen never sees. |
| §3 estimand | **N/A with reason** — no estimand exists. Nothing here is adjudicated. |
| §5 controls / §4 leak tripwire | **N/A with reason** — a control answers an attribution question about an *effect*; this item measures none. Replaced by the **reproduction battery** (§4): every generalised path must reproduce its frozen predecessor at frozen settings. |
| §6 power | **N/A in the effect sense; replaced by the measured COVERAGE statement (§5).** |
| §8 hard/informative split | **APPLIES and is filled (§3).** |
| §9 conversion pin | **N/A with reason** — this item emits no normalised effect and no money figure, so there is no screen→money seam to pin. SPDR-009 carries it. |
| §10 SPREAD-SCALE-ROUTING / §11 spread leg | **N/A with reason** — no edge, no contrast, no verdict for a spread leg to bind on. |
| §7 golden trace | **APPLIES — one per work item (§6).** |
| §12 amendment ledger | §8. |
| §13 battery rules | F06 (thresholds derived, not asserted) applies to W3; the rest gate reads, and there are none. |

### §1.1 Object identity (the live one)

```
OBJECT-IDENTITY (apparatus → consumer):
  W5's candidate event bar == SPDR-009's event bar: MUST BE, code-asserted.
    Both are: an LTF bar in the DESIGN band whose seasonal volume residual is at/above its
    per-(symbol,timeframe) p90 cut and whose range residual is at/below its p10 cut, on the
    COMPLETE-window LTF series (window_class == COMPLETE; traded_fraction == 1.0), inside a
    session whose HTF anchor and IB are this item's. Zero-fill / reconstruction is WITHDRAWN —
    the predicate must never see a fabricated minute (QA-3 S-1).
    W5 emits the SHARED predicate from one function, `absorb_candidate_predicate()`, which
    SPDR-009 imports rather than reimplements. A divergence would freeze τ against a population
    the screen never sees (QA-1 I-7).
  W5's level set == SPDR-009's level set: MUST BE, and every level price is built from
    1-MINUTE BARS (D6.3), never from LTF bars — traced from the emitted frame's measured
    `level_source_bar_minutes`, not from a declared constant (QA-6 I-2).
    The set is: the PRIOR HTF SESSION'S levels (extremes, POC, VAH, VAL — knowable at this
    session's open) PLUS THIS SESSION'S IB EDGES ONCE THE IB WALL-CLOCK COMPLETES
    (AMENDMENT-17, QA-6 I-1; AMENDMENT-19, QA-7 I7-1/I7-2).
    EVERYTHING IS DECIDED AT THE CANDIDATE BAR'S **CLOSE**, because that is where the
    screen conditions:
      * the candidate's session is the one holding its LAST SOURCE MINUTE
        (`OpenTime + ltf − 1m`), so a bar straddling the anchor belongs to the session it
        ends in; `n_candidates_straddling_anchor` is counted and published;
      * an IB edge is available when `close_time − anchor ≥ ib_minutes`.
    D1/D2/D3 nest into their IB boundary (15×1m, 3×5m, 1×15m). **D4 DOES NOT**: A-USOPEN
    anchors at 13:30 UTC while D4's bars open on the hour, so its IB ends at anchor+60 =
    14:30, mid-bar. An `OpenTime`-based test asks the question 30 minutes early and refuses
    events whose IB completed long before their close (QA-7 I7-1 measured 18 false refusals).
    A candidate whose IB has not completed keeps its place in the census and is measured
    against the levels that DO exist; only the unformed IB EDGE is removed from that bar's
    level set. SPDR-009 §3.2 emits one event per (pair, LTF bar, level kind), so the bar is
    still a real event at an older level — dropping it entirely would freeze τ on a
    distribution shifted wide (operator decision, 2026-07-21). No forward price is ever
    consulted: the unformed edge is excluded, not approximated.
    A level is EXCLUDED from a candidate's set on **either** of two grounds
    (AMENDMENT-21, QA-8 I8-1):
      * NOT-YET-FORMED — `mins_since_close < available_mins_since` (the IB has not completed
        by the bar's close); or
      * SELF-MADE — the level's `formed_ts` falls at or after the bar's own OpenTime, i.e.
        the candidate's **own** minutes made or contributed to the level. Formation provenance
        is mandatory for EVERY level kind: actual edge-setting minute for IB/prior-session
        extrema; last contributing 1m source timestamp for POC/VAH/VAL. This covers D3's
        one-bar IB and D4's anchor-straddling 1h bar, whose first 30 minutes belong to the
        session that becomes its prior session. Missing/null `formed_ts` raises; it never
        defaults to "past-formed".
    This availability rule has ONE implementation — `xen.sigbar.ltf.assign_candidate_sessions`
    + `available_levels_for_candidates` — which both W5 and SPDR-009 import; neither retypes
    it (AMENDMENT-21, QA-8 I8-2).
    W5 counts and publishes `n_candidates_pre_ib`, `n_ib_edge_unavailable`,
    `n_ib_edge_self_made_excluded`, `n_prior_level_self_made_excluded`,
    `n_self_made_level_excluded`, `n_candidates_no_levels`,
    `n_candidates_straddling_anchor`, `n_candidates_measured`, with the identity
    `n_candidates == n_measured + n_no_levels + n_unanchored`.
    `n_ib_edge_unavailable` is the subset whose nearest level over the full set is an IB edge
    unavailable at the candidate close; `n_candidates_pre_ib` is the full pre-IB count.
```

---

## §1 Purpose — what SPDR-009 cannot do without this

Every threshold in this family is a **residual against a fitted seasonal baseline** (A5); "heavy
volume", "no result", "large |Δ|" have no raw meaning. Four verified blockers:

1. **`fit_seasonal_baseline` is hard-wired to a 1440×7 grid.** The raise at `baselines.py:166`
   fires only when the *emitted* grid height ≠ 1440×7 — not when fed coarser bars. Measured on
   BTCUSDT 5m: it returns a full 10,080-cell grid of which **2,016 are populated and 8,064 (80%)
   silently fall back** to the day-of-week marginal (QA-3 S-7). No timeframe parameter exists.
   W1 prevents that silent fallback; VT-4(d) catches a wrong cell count once `bar_minutes` is
   passed. (`diag_fill_bias.py` deliberately relies on the 1m fitter's superset behaviour on
   coarse bars — its numbers remain valid because the 1440-grid contains the 288-grid and no
   coarse bar maps to an unused cell; record that so a later "fix" does not silently change
   the pinned withdrawal evidence.)
2. **`bar_aggregator.aggregate_ohlc` cannot carry the taker split** — chapter-02 legacy requiring
   `Symbol`/`CloseTime`/`TickVolume`, summing `TickVolume` only. `Volume`, `BuyVolume`,
   `SellVolume`, `NTrades` pass through unrepresented. Reusing it would silently destroy the
   measurement this family exists to exploit.
3. **`sessions.py` has no 1h or 4h anchor** (its four candidates are daily or 8-hourly) and
   `session_breaks` takes an IB in minutes with no notion of an LTF bar.
4. **Coarse bars are mostly incomplete under strict retention** — measured, §5. After the
   zero-fill withdrawal this is **accepted by design**, not repaired: D2/D3/D4 are
   liquidity-limited and activity-conditioned on the surviving windows. SPDR-009 declares those
   cells UNPOWERED; it does not fill them in.

### §1.2 The D6.3 invariant (restated here because this is the first item that can violate it)

> **HTF and LTF govern session framing and event detection ONLY. Every price-path and
> volume-at-price measurement stays on 1-minute bars.**

This item is the first to hold aggregated bars next to level construction, so the invariant is
code-asserted here (QA-1 I-5): `assert_levels_from_1m()` raises if any level price is traced to an
aggregated bar. Volume profiles (POC, value-area edges) are built from the prior HTF session's
**1-minute** bars, keeping the frozen **K-UNIFORM** kernel inside its trade-truth-calibrated regime.

---

## §2 Work items

### W2a — Window integrity classification (REPLACES the withdrawn zero-fill)

**The zero-fill proposed at revision 2 is WITHDRAWN from every primary path.** QA run 2 (R-2,
blocking) asked the question revision 2 failed to ask: the fill was measured on *coverage* but never
on the *event population*. Measured (`design_derivations/diag_fill_bias.json`, count-only):

| symbol | tf | bars with range = 0 | candidates raw → filled | of which touch reconstructed minutes | median traded fraction |
|---|---|---|---|---|---|
| ALICEUSDT | 5m | 0.017 → **0.262** | 32 → **89** | 82 (**92%**) | 0.60 |
| ALICEUSDT | 15m | 0.000 → 0.076 | 2 → **16** | 16 (**100%**) | 0.60 |
| SKLUSDT | 5m | 0.006 → **0.228** | 3 → **20** | 18 (**90%**) | 0.60 |
| CRVUSDT | 5m | 0.002 → 0.044 | 170 → 237 | 176 (74%) | 0.80 |
| LTCUSDT | 5m | 0.000 → 0.001 | 9 → 5 | 0 (**0%**) | 1.00 |
| SOLUSDT | 5m | 0.000 → 0.000 | 59 → 57 | 0 (**0%**) | 1.00 |

**The mechanism of the defect.** A mostly-reconstructed window has near-zero range but keeps the
real volume of its few traded minutes. Against a cell median depressed by other filled windows,
that volume residualises high. The window then reads **"heavy volume, no price result" — the
absorption signature itself, manufactured out of minutes in which nothing traded.** It is confined
to the thin tail (liquid names show 0% contamination) — which is precisely where D6 expects breadth
to come from, and precisely where SPDR-009's D2 pool and W5's τ freeze would have consumed it.

**What replaces it.** Every missing minute is *classified*, never fabricated. Gap days are
derived from **staging**, not the ledger (QA-3 S-2: the ledger has no gap timestamps —
`gap_runs` is a length histogram, `unresolved_error_days` an integer count):

| window class | definition | eligible to be an event? | eligible to fit a baseline? |
|---|---|---|---|
| `COMPLETE` | all N source minutes present in staging | **YES** | **YES** |
| `NO_TRADE_PARTIAL` | missing minutes fall inside an otherwise-present UTC day (instrument traded that day; minutes absent) | **NO** | **NO** |
| `GAP_CONTAMINATED` | any source minute falls on a UTC day inside the instrument's DESIGN span with **zero** bars in staging (missing day-file) | **NO** | **NO** |

Only `COMPLETE` windows enter the event population and the seasonal fit. `NO_TRADE_PARTIAL`
windows are retained **for disclosure only**, as the per-instrument thinness metric that travels
with every downstream read; `GAP_CONTAMINATED` windows are excised and counted.

**`GAP_CONTAMINATED` is provably empty at 5/15/60m — say so, do not read its zero as "checked
and clean" (AMENDMENT-16, QA-6 I-4).** A gap day is a *whole* UTC day with zero bars, and
clock-aligned 5/15/60-minute windows never straddle midnight. So a window either lies wholly
inside a gap day — in which case `group_by_dynamic` emits no row at all, which is the correct
excision — or contains no gap-day minute. Measured across 194 instruments × 3 timeframes the
observed class set is `{COMPLETE, NO_TRADE_PARTIAL}` and the `GAP_CONTAMINATED` count is
identically **zero**, including OMGUSDT with 42 gap days. The class stays in the vocabulary
because a sub-day gap rule (or a window longer than a day) would populate it; the *live*
gap disclosure is `gap_excision_report.json`, not this counter. Where the ledger
flags an instrument (`unresolved_error_days > 0`), the staging-derived gap-day count is
**reconciled** and mismatches reported (two of eight in-band instruments — BNXUSDT, GSTUSDT —
show day-holes the ledger does not flag; a ledger-driven rule would have missed them).

**The honest consequence, stated rather than engineered away.** This restores strict retention, so
the coverage cost measured in §5 is real and is **not** recoverable: on a thin instrument most
hourly windows are unusable, and that instrument is simply not measurable at D4. That is the
truthful answer — *you cannot measure "heavy volume with no price result" over an hour in which the
instrument traded twelve minutes.* SPDR-009 declares those cells UNPOWERED; it does not fill them
in. Revision 2 tried to engineer the constraint away and manufactured events instead.

**Every aggregated bar carries `SourceBars`, `n_missing`, `window_class` and `traded_fraction`**
(free — `SourceBars` was already counted), so no downstream consumer can be blind to how much of a
bar is real.

### W2a′ — Collection gaps: staging day-holes, DESIGN-band frame (QA-2 R-1, QA-3 S-2)

Revision 2 asserted `collection_gap_minutes = 0` and `outage_minutes = 0` **for every instrument**.
That was **false and is withdrawn** on the *whole-archive* ledger frame:
- `outage_minutes = 0` **does** hold universally.
- `collection_gap_minutes > 0` for **37 of 194** on the whole archive (up to 138,240 minutes,
  OMGUSDT; ONEUSDT 136,800).

**But this item reads DESIGN only.** Gap days are derived from staging as UTC days with zero bars
inside each instrument's own DESIGN span (`diag_universe_coverage.json`, count-only). Measured:

| symbol | DESIGN gap days / span | ledger `unresolved_error_days` | note |
|---|---|---|---|
| OMGUSDT | 42 / 505 | 96 | worst in band |
| ONEUSDT | 27 / 325 | 95 | |
| BNXUSDT | 11 / 328 | **0** | ledger miss |
| CELOUSDT | 6 / 229 | 6 | |
| TWTUSDT | 5 / 103 | 25 | |
| BCHUSDT | 3 / 229 | 6 | |
| CTSIUSDT | 3 / 343 | 3 | |
| GSTUSDT | 2 / 80 | **0** | ledger miss |

**8 of 194 instruments** have any affected DESIGN day — not 37. **AVAXUSDT** (a SPDR-009 census
instrument) has **zero** DESIGN-band gap days; its 6 ledger error-days fall outside the band.
**OGNUSDT** similarly has out-of-band ledger days only. Whole-archive ledger gap ≠ in-band
contamination; 31 of the 37 ledger-flagged instruments have zero in-band day-holes.

**Contiguity claim corrected.** QA-2 asserted `max_gap_run_min == collection_gap_minutes` implies
single contiguous runs. **False for the worst cases** (OMGUSDT: max run 12,960 vs collection gap
138,240; 13 runs > 60m). It holds only for the 8,640-minute cluster. Remedy is still
**window-level excision of staging day-holes**, not instrument exclusion: dropping whole
instruments would split the four-pair population. Excised spans and dates reported per instrument.

### W2b — Signed-aware LTF aggregation

Clock-aligned N-minute aggregation on the **staging series as recorded** (no fabricated bars):

```
Open  = first 1m Open        Volume     = sum        BuyVolume  = sum
High  = max   1m High        NTrades    = sum        SellVolume = sum
Low   = min   1m Low         SourceBars = count      Delta      = BuyVolume − SellVolume
Close = last  1m Close
```

Strict retention (exactly N source bars, i.e. `window_class == COMPLETE`) is **kept**, and its cost
is real and reported (§5) rather than engineered away. Dropped windows are counted and classified
per (symbol, timeframe) so a coverage loss is always attributable to thinness or to a collection
gap, never unexplained.

**The split survives aggregation exactly (A8).** `BuyVolume`/`SellVolume` are measured taker counts
reconciled bit-exactly to the raw trade archive, hence **additive**. An aggregated bar's Δ is
*measured*, not inferred; coarsening introduces no sign-placement assumption. Asserted per bar:
`BuyVolume + SellVolume == Volume` within float tolerance.

### W1 — Seasonal baselines for 5m / 15m / 1h

Generalise `fit_seasonal_baseline` with an explicit `bar_minutes` parameter; the key becomes
**slot-of-day × day-of-week**, slot = `floor(minute_of_day / bar_minutes)`.

**W1 does not emit a 1-minute baseline** (QA-1 I-10). The frozen `1b7244c8…` pin remains the sole
1m artifact; a second one would create two competing objects. The 1m path is exercised only as the
A1 reproduction assert.

**Cast discipline is inherited, not reinvented.** `dt.hour()`/`dt.minute()` return **Int8**, so
`hour*60` overflows for every hour ≥ 3 and silently aliases the grid. `_with_seasonal_keys` already
casts to Int32 for this reason (INFR-017 QA run 1, Issue 1). The generalised slot key must carry
the same casts, and `assert_seasonal_keys_valid` — which currently hard-codes the range [0, 1439] —
must be generalised to `[0, slots_per_day − 1]` (QA-1 I-2; it was unmentioned in the prior draft).
*This trap was re-triggered while writing this design's own diagnostic, which is why it is called
out rather than assumed.*

Unchanged: robust statistics (median + MAD×1.4826); the A5 metrics with `delta_abs` and
`delta_ratio` fitted **separately**; `MIN_CELL_OBS = 8` with day-of-week-marginal fallback; sparse
disclosure.

### W3 — Class thresholds per (symbol, timeframe)

Apply the **unchanged frozen rule** — `classes.derive_thresholds`, p90/p10 of the DESIGN-bank
residual distribution, plus `abs_high` = p90 of |`delta_ratio_resid`| — to each (symbol, timeframe).
Not re-raced, re-tuned or re-selected: the same estimator, more instruments and timeframes. Emitted
with realised cut values so thresholds are re-derivable rather than trusted (L-24 F06).

### W4 — Sessions for 1h / 4h, and the generalised IB

| anchor | minutes-of-day | sessions/day |
|---|---|---|
| `A-H1` | 0, 60, …, 1380 | 24 |
| `A-H4` | 0, 240, 480, 720, 960, 1200 | 6 |

```
ANCHOR CERTIFICATION (Addendum §2.7) — CORRECTED, QA-1 I-4:
  A-H1 and A-H4 are OPERATIONAL ANCHORS. No breakout-expectancy race is run for them.
  A-H1: selection contrast genuinely UNMEASURED.
  A-H4: NOT unmeasured — the prior draft's claim was FALSE. A-H4's grid is a strict SUPERSET of
    A-FUND (0/8/16 UTC), which INFR-018 DID race at L=15: contrast -0.1627, day-clustered CI
    [-0.259, -0.027] EXCLUDING ZERO, against its own MDE of 0.10. That is a MEASURED, RESOLVED,
    NEGATIVE result — A-FUND's anchored breakouts did WORSE than pseudo-anchor controls.
    SCOPE OF THAT EVIDENCE (QA-2 R-7 — the prior wording overstated it): A-FUND's negative was
    BREAKOUT EXPECTANCY AFTER AN INITIAL BALANCE, which is S1's object, not S9's. It lowers the
    prior on the ANCHOR's quality as a session clock on half of A-H4's instants; it is NOT direct
    evidence against absorption detection at a level. Both halves of that sentence travel together
    in D3's reads and in the SPDR-009 disposition. (The funding-timestamp coincidence is a PROPERTY
    of the clock, never a claim that funding cadence carries expectancy.)
  No downstream read may treat either anchor as edge-bearing.
```

**Generalised initial balance.** IB = **15 minutes of wall-clock**, as the LTF bars covering it,
minimum one bar:

| pair | IB in LTF bars | IB wall-clock | **IB share of session** | note |
|---|---|---|---|---|
| D1 1d/1m | 15 | 15 min | **1.0%** | reproduces the frozen L=15 exactly |
| D2 1h/5m | 3 | 15 min | **25.0%** | |
| D3 4h/15m | 1 | 15 min | **6.3%** | |
| D4 1d/1h | 1 | **60 min** | **4.2%** | **DEVIATES** — smallest whole bar exceeds 15 min |

**Disclosed (QA-1 I-8):** holding wall-clock constant makes the IB's *share of session* vary 1%→25%.
The IB is a different fraction of its session at every pair, so IB-derived objects are **not
cross-pair comparable**, and no read may compare them across pairs without saying so. This is why
D6.4 moved the zone scale off IB width (W5).

### W5 — Contact-zone scale census (count-only input to SPDR-009's τ freeze)

Emits, per (symbol, pair), on **DESIGN only**: the prior-HTF-session range distribution (price and
bps), and the distance from each candidate event bar's close to its nearest structural level in that
scale — **counts and quantiles only**. Candidate bars come from the shared predicate (§1.1); levels
from prior-HTF-session 1-minute bars (§1.2).

**Also emits the D1 `0.25 × ib_width` census** (QA-1 I-6) — without it SPDR-009 cannot run the
retained D1 sensitivity that preserves its QA-approved read.

---

## §3 Integrity split — hard vs informative

```
HARD (raise, never warn):
  - Band fences on EVERY read path (`fences.assert_band`); TEST and holdout unreachable.
  - DESIGN-only fitting AND census: `assert_design_only_fit()` raises on any fit or W5 path
    touching CONFIRM bars.
  - Aggregation introduces NO look-ahead: an N-minute bar closing at t is composed only of
    1-minute bars with OpenTime < t; `assert_bar_causality()` verifies every source window lies
    strictly inside its bar.
  - `assert_windows_complete()` — no `NO_TRADE_PARTIAL` or `GAP_CONTAMINATED` window may reach the
    event population or a seasonal fit (W2a); no bar may be fabricated on any primary path.
  - `assert_levels_from_1m()` — a level priced off an aggregated bar raises (§1.2).
  - `fences.assert_no_per_level_delta` (card ban 2); `check_no_local_accounting`.
  - OUTCOME BAN, two-layer (QA-1 I-1 — the name-based check alone was insufficient):
      (a) schema layer: `check_no_outcome_columns()` rejects known outcome column names;
      (b) PROVENANCE layer: `assert_no_forward_provenance()` — every emitted column carries the
          max source-bar timestamp that fed it, and the assert raises if that exceeds the row's own
          bar close. A forward-derived column cannot pass this by being renamed, which was the hole.
INFORMATIVE (reported, never gating):
  coverage statistics (retention distribution over all 194; usable-universe counts at the
  predeclared floor), sparse-fallback rates, null-scale cell counts, dropped-window fractions
  by class, COMPLETE-vs-partial volume ratios (activity conditioning), zone-scale quantiles.
```

---

## §4 Acceptance — the reproduction battery

No new apparatus is admitted unless it reproduces its frozen predecessor exactly at frozen settings.

| # | Assert | Why it is the right test |
|---|---|---|
| **A1** | `fit_seasonal_baseline(bar_minutes=1)` reproduces `1b7244c8…` **value-identically** over the 194 fitted instruments — every `loc`, `scale`, `n`, `sparse` equal after remapping the generalised `slot` key back to `mod` | Proves the generalisation changed no 1-minute value. **"Byte-identical" was the wrong word** (QA-1 I-2): the key column is renamed by construction, so identity is on values under a declared key mapping. If A1 fails, every existing CF-SIGAUC-001 result is in question. |
| **A1b** | A1 runs **through the generalised code path**, not a preserved legacy branch | A1 alone could pass while the new branch is never exercised (QA-1 I-2). |
| **A2** | `derive_thresholds(1m)` reproduces the **137** threshold blocks in `5c386984…` exactly, **and** the 194-symbol extension is asserted in code to use the identical estimator | Pins both the threshold layer and that the extension is the same rule, not a lookalike (QA-1 I-2). |
| **A3** | 1h/4h session plumbing at `A-USOPEN`, L=15 reproduces `sessions.session_breaks` byte-identically | New anchor/IB plumbing must not perturb the frozen daily object D1 depends on. |
| **A4** | Every aggregated bar: `BuyVolume + SellVolume == Volume` (float tol); OHLC equals an independent recomputation from its source minutes | A8's provenance property must survive aggregation or the signed premise is lost at coarse bars. |
| **A5** | 1m→5m→15m equals 1m→15m directly | Associativity; failure means a misaligned window grid. |
| **A5b** | The new aggregator's **price** columns match `bar_aggregator.aggregate_ohlc` on a fixture where both are defined, or the window-convention difference is explicitly characterised | Nothing cross-checked the new aggregator against the existing one (QA-1 I-2). |
| **A6** | ~~sparse-fallback rate monotone non-increasing in bar size~~ **DELETED — measured false (§5).** Replaced by a **reported** statistic, not an assert: obs/cell and sparse rate per (symbol, timeframe), with the analytic expectation (obs/cell ≈ weeks covered × retention) shown beside the measured value | The deleted assert would have fired on most instruments for a benign structural reason (QA-1 I-3). Its revision-2 replacement was **also** unsound — it assumed the fill and would have fired on the 37 gap instruments, and "equal" is exact where band edges legitimately differ by ±1 (QA-2 R-3). Coverage is a disclosure, not a gate. |
| **A7** | No emitted artifact carries an outcome column **or forward provenance** (§3) | The load-bearing ban. |
| **A8** | No `NO_TRADE_PARTIAL` or `GAP_CONTAMINATED` window enters the event population or any seasonal fit; every aggregated bar carries `window_class`, `n_missing`, `traded_fraction`; excised gap spans emitted per instrument | This is the direct guard against the revision-2 defect: an event may never rest on a minute that was not traded. |
| **A9** | Candidate counts per (symbol, timeframe) reconcile to the `COMPLETE`-window population, and **no candidate has `traded_fraction < 1.0`** | Event-layer tripwire against reintroducing R-2. **Not an independent guard** (QA-3 S-6): given staging's invariant that no zero-volume minute exists (min `NTrades` = 1), `COMPLETE` ⇒ `traded_fraction` = 1.0 identically, so A9 is implied by A8. Kept as a cheap second tripwire that would fire if staging ever admits zero-volume rows — not presented as a second line of defence. |
| **A10** | Range-residual cells whose scale is null or zero are counted and **named** per (symbol, timeframe) | Thin instruments produce degenerate range cells at 5m (QA-2 R-4: ALICEUSDT 9/2016, ANKRUSDT 3/2016); silent holes in the event population must surface as counts. |
| **A11** | A pinned D4 A-USOPEN straddling event proves all seven structural levels carry non-null `formed_ts`; prior profile levels and any extrema set by the candidate's source minutes are excluded; missing provenance raises | Direct regression for QA-9 R9-1. It fails closed on the defect class rather than checking one final distance. |

---

## §5 Coverage — MEASURED, replacing the asserted premise (QA-1 I-3, blocking)

**The prior draft claimed observations per cell rise with bar size (~60 at 1m → ~86 at 1h). That
was wrong, and it was the one premise deciding whether D3 and D4 are viable at all.** A seasonal
cell is (slot-of-day × day-of-week) and recurs **once per week at every timeframe**, so obs/cell is
**constant in bar size** — it equals the number of weeks covered. Worse, under strict retention a
coarse window needs *all* N of its source minutes, so retention falls as roughly `p^(N−1)`: the
reverse of the claim.

Measured on the DESIGN bank (`design_derivations/diag_coverage.json`, count-only). The **raw**
column is now the operative one — the zero-filled column is retained only to show what was
withdrawn and why (W2a):

| symbol | weeks | no-trade min. | 5m ret. | 15m ret. | **60m ret.** | 60m obs/cell | 60m sparse rate |
|---|---|---|---|---|---|---|---|
| BTCUSDT | 32.6 | 0 | 1.000 | 1.000 | **1.000** | 33 | 0.00 |
| ETHUSDT | 32.6 | 3 | 1.000 | 1.000 | **1.000** | 33 | 0.00 |
| SOLUSDT | 32.7 | 365 | 0.995 | 0.987 | **0.961** | 32 | 0.00 |
| LTCUSDT | 32.6 | 13,543 | 0.850 | 0.709 | **0.491** | 15.5 | 0.06 |
| CRVUSDT | 32.6 | 43,539 | 0.630 | 0.424 | **0.204** | 6 | **0.64** |

*(No-trade minutes are whole-archive ledger figures; retention and obs/cell are DESIGN-band —
labelled because revision 2 printed them adjacent and unlabelled, QA-2 R-6. LTCUSDT 60m obs/cell is
15.5, not the 16 previously printed, QA-2 R-9.)*

**Read this plainly, as a scope limit rather than a problem to be solved.** Coverage degrades
sharply with bar size on thin instruments — CRVUSDT keeps only 20% of its hourly windows, and 64%
of its hourly seasonal cells fall back to a day-of-week marginal. **That is a true statement about
the instrument, not an artifact to repair:** an instrument that trades in a fifth of its minutes
genuinely cannot support a "heavy volume, no price result" reading at hourly scale. Revision 2 tried
to recover those windows and manufactured events instead (W2a).

### Universe retention — MEASURED over all 194 (QA-3 S-3)

The five-instrument sample is **unrepresentative**: CRVUSDT 60m retention 0.204 sits near the
**69th percentile** of the universe (higher = better retention: only ~31% of instruments retain
more than CRV), so the sample still flatters the thin tail even though CRV is not among the
worst. Full-universe numbers (`diag_universe_coverage.json`, DESIGN band, raw strict retention):

| pair (LTF) | median retention | ≥0.90 | ≥0.50 usable | <0.20 |
|---|---|---|---|---|
| **D2** 1h/5m | **0.387** | 20 (10%) | **72 (37%)** | 28 (14%) |
| **D3** 4h/15m | **0.202** | 11 (6%) | **47 (24%)** | 95 (49%) |
| **D4** 1d/1h | **0.089** | 6 (3%) | **31 (16%)** | 132 (68%) |

The median instrument keeps **8.9%** of its hourly windows. At a predeclared **0.50 retention
floor** the usable universe is ~72 / ~47 / ~31 against **194 at D1**. **D2 is liquidity-limited
too** — not only D3/D4. This invalidates any SPDR-009 event projection that assumed ~194
instruments at every pair (SPDR-009 §6.3 as written for the 1d/1m-only design).

### Activity conditioning of the surviving population (QA-3 S-4)

Strict retention is not only lost coverage: a `COMPLETE` hour is an hour in which the instrument
traded **every** minute. Surviving windows carry **more** volume than dropped ones, and the
strength varies across the cross-section (`diag_universe_coverage.json`, median COMPLETE/partial
volume ratio at 60m):

| symbol | 1m-proxy ret. 60m | n COMPLETE | n partial | median vol ratio |
|---|---|---|---|---|
| SOLUSDT | 0.961 | 5,302 | 218 | **3.2×** |
| MATICUSDT | 0.779 | 11,396 | 3,238 | **4.4×** |
| LTCUSDT | 0.491 | 2,700 | 2,796 | **3.1×** |
| AAVEUSDT | 0.204 | 1,125 | 4,395 | **3.6×** |
| CRVUSDT | 0.204 | 1,121 | 4,375 | **2.4×** |
| SKLUSDT | 0.026 | 140 | 5,351 | **26.9×** |

Universe median 60m vol-ratio ≈ **6.7×** (n=193 instruments with both COMPLETE and partial;
range 0.3×–187×). So D2/D3/D4 measure **absorption during continuously-traded windows**, and the
conditioning is strongest where coverage is worst. Because the ratio is not constant across
instruments, a pooled coarse-pair read mixes unequally conditioned names — the survivorship
analogue of Addendum §2.9 breadth honesty. **This is not an argument to restore the fill** (the
fill fabricated the other tail). It is a **conditioning disclosure** SPDR-009's disposition needs
alongside the coverage disclosure.

**Consequence carried to SPDR-009 and to D6 (operator scope question, not a machine gate):**
- Coarse pairs are measurable on a liquid/active core (~72 / ~47 / ~31 at the 0.50 floor) with an
  activity-conditioning caveat, **or** D6's breadth ambition is rethought. That call is the
  operator's.
- Complementarity is weaker than previously stated (QA-3 S-5): at D1 **BTCUSDT and ETHUSDT**
  contributed zero signal events; SOL/ADA/MATIC/LINK did contribute. At D3/D4 the deepest names
  are still the ones with full coverage.

Coverage reported per (symbol, timeframe) at run: cells populated / total; median and p10
obs/cell; sparse-fallback rate; null-scale cell counts; retention distribution over all 194;
usable universe at the 0.50 floor, **named**; COMPLETE-vs-partial volume ratio per instrument;
windows dropped **by class** with excised gap-day spans, so every loss is attributable.

**Predeclared as expected-thin:** instruments listed late in the DESIGN bank (~229 days ≈ 33 weeks
for most, per the registry's trailing-cap note) — which is why obs/cell is 33, not 87, on the
sample above.

---

## §6 Verification traces — designer-derived, for QA to diff

**W2b (`design_derivations/agg_trace.py` → `agg_trace.json`), BTCUSDT, window opening 2022-07-15 13:00Z:**

```
VT-1  5m   O 20975.0  H 20999.0  L 20970.0  C 20970.5
           Volume 718.345  Buy 443.107  Sell 275.238  Delta +167.869   SourceBars 5
           Buy+Sell−Volume = 0.0 exactly
VT-2  15m  O 20975.0  H 21094.5  L 20945.0  C 20947.5
           Volume 4653.376  Buy 2550.228  Sell 2103.148  Delta +447.080  SourceBars 15
VT-3  60m  O 20975.0  H 21094.5  L 20790.5  C 20855.5
           Volume 13447.757  Buy 6786.452  Sell 6661.305  Delta +125.147  SourceBars 60
      Nesting: all three share the window Open; High/Low widen monotonically
      (20999.0→21094.5→21094.5 H; 20970.0→20945.0→20790.5 L). Delta does NOT accumulate
      monotonically (+167.9→+447.1→+125.1) — the hour contains offsetting flow, which is the
      measurement behaving correctly.
```

**W2a (`diag_coverage.json`, `diag_fill_bias.json`):** the pinned negative result — reconstructing
43,539 no-trade minutes lifts CRVUSDT 60m retention 0.204 → 1.000, **and** lifts ALICEUSDT 5m
candidates 32 → 89 with 92% of them resting on reconstructed minutes. Both numbers are pinned
together because the second is why the first is refused. **W1:** obs/cell ≈ weeks × retention (33
where retention is 1.0; 6 for CRVUSDT at 60m where retention is 0.204) — reported, not asserted.
**W4:** D1's IB reproduces `ib_high`/`ib_low` from `session_breaks` exactly on **BTCUSDT session
2022-07-15 13:30Z — IB 20833.0 / 21020.5 / width 187.5**. *(Revision 2 mis-cited this as SPDR-009's
GT-1, which is a different session — SOLUSDT 2022-12-28; QA-2 R-5. The values are correct and
independently recomputed from staging; only the citation was wrong.)* **W3/W5** trace values are
emitted at run against A2 and the shared predicate; no hand value is pinned for them here, and that
gap is declared rather than papered over (QA-1 I-9).

```
VT-4  Must RAISE, not warn:
      (a) fitting or W5 census on any bar with OpenTime ≥ 2023-03-01 (DESIGN-only fence);
      (b) any read path reaching ≥ 2023-12-18 (TEST) or ≥ 2025-01-08 (holdout);
      (c) a retained aggregation window with SourceBars ≠ N;
      (d) a fitted grid whose cell count ≠ slots_per_day × 7, or a slot key outside
          [0, slots_per_day − 1];
      (e) an emitted artifact carrying an outcome column OR forward provenance;
      (f) a per-level Δ access (card ban 2);
      (g) **DEMOTED to declared, not enforced (AMENDMENT-20, QA-7 I7-6):** A-H1/A-H4 consumed
          as an edge-bearing anchor. No consumer of an anchor edge exists in this item — W4
          emits `edge_bearing: false` as data and nothing here reads an anchor for edge. The
          enforceable version lives in SPDR-009 GT-5(k), against a consumer that exists;
      (h) a fabricated bar reaching any primary path, or a non-COMPLETE window entering the event
          population or a seasonal fit;
      (i) a level priced off an aggregated bar rather than 1-minute bars;
      (j) a candidate event bar with traded_fraction < 1.0.
```

---

## §7 Artifacts, complexity budget, execution order

| | |
|---|---|
| Statistical reads | **0** — this item tests no hypothesis |
| New/changed modules | `xen.sigbar.baselines` (+`bar_minutes`, back-compatible default 1; generalised `assert_seasonal_keys_valid`), `xen.sigbar.sessions` (+`A-H1`/`A-H4`, +LTF-bar IB rule), **new** `xen.sigbar.ltf` (window classification, signed aggregation, causality + provenance asserts, `absorb_candidate_predicate` on `COMPLETE` windows only), `xen.sigbar.fences` (+`check_no_outcome_columns`, `assert_no_forward_provenance`, `assert_windows_complete`, `assert_levels_from_1m`). `classes.py` and `bar_aggregator.py` **untouched**. |
| Artifacts | `results/{seasonal_baselines_mtf.parquet, class_thresholds_mtf.json, class_thresholds_1m.json, sessions_mtf.json, zone_scale_census.json, zone_scale_census_d1_ibwidth.json, coverage_report.json, gap_excision_report.json, reproduction_battery.json, pins.json}` |
| Plots | ≤3: obs-per-cell by timeframe · retention distribution (all 194) + COMPLETE/partial vol ratio · prior-session-range distribution by pair |

**Execution order is strict.** frozen-input hashes verified → **A1/A1b/A2/A3 run and passing**
(nothing downstream computes until the generalisation is proven inert at frozen settings) →
**W2a classify + A8** (staging day-holes → `GAP_CONTAMINATED`; no fill) → W2b aggregation +
A4/A5/A5b → W1 baselines (5m/15m/1h) → W3 thresholds → W4 sessions → A6-replacement + A7 +
A9/A10/A11 → W5 census (both scales) → coverage + gap-excision reports → hash-pin to `pins.json` →
hand off to SPDR-009, which freezes τ and its pool cuts against these artifacts before any read.

## §8 Amendment ledger (L-23)

```
AMENDMENT-1 (QA-1 I-3, BLOCKING): the coverage premise was ASSERTED and false. Obs/cell is
  CONSTANT in bar size (a seasonal cell recurs weekly at every timeframe), and strict retention
  DEGRADES with bar size (~p^(N-1)), the reverse of the claim. Measured, and W2a no-trade-minute
  reconstruction added as the fix — restoring CRVUSDT 60m retention 0.204 → 1.000 and its sparse
  rate 0.64 → 0.00. A6 deleted and replaced. DIRECTION: TIGHTER (a false premise replaced by a
  measured one plus the correction it demands). Count: 0L/1T/0N.
AMENDMENT-2 (QA-1 I-4): A-H4's certification corrected — its "unmeasured selection contrast" claim
  was FALSE. A-FUND, a strict subset of its grid, was raced by INFR-018 to a resolved NEGATIVE
  contrast (-0.163, CI excludes zero, above MDE). D3's prior is lowered by measurement.
  DIRECTION: TIGHTER (a false claim replaced by adverse evidence). 0L/2T/0N.
AMENDMENT-3 (QA-1 I-1): outcome ban given a PROVENANCE layer — a name-based schema check could be
  defeated by renaming. Every column carries its max source-bar timestamp and raises if it exceeds
  the row's bar close. W5's band declared DESIGN-only. DIRECTION: TIGHTER. 0L/3T/0N.
AMENDMENT-4 (QA-1 I-2): reproduction battery repaired — A1 restated as VALUE-identity under a
  declared key remap (the key column changes by construction, so "byte-identical" was incoherent);
  A1b added so the generalised branch is actually exercised; A2 extended to code-assert the
  137→194 extension; A5b added to cross-check the new aggregator against the legacy one;
  `assert_seasonal_keys_valid`'s hard-coded [0,1439] range flagged for generalisation.
  DIRECTION: TIGHTER. 0L/4T/0N.
AMENDMENT-5 (QA-1 I-5, I-6, I-7, I-8, I-9, I-10): D6.3's one-minute invariant restated and
  code-asserted (§1.2); W5's level provenance pinned to prior-HTF-session 1m bars; the D1
  ib_width sensitivity census added so SPDR-009 can actually run it; the five unfilled mandatory
  blocks either filled (object-identity §1.1, hard/informative §3) or declared N/A with a reason;
  the IB's 1%→25% share-of-session variation disclosed with its cross-pair-comparability
  consequence; W1 no longer emits a competing 1m baseline; the W3/W5 golden-trace gap declared.
  DIRECTION: NEUTRAL (completeness and disclosure). 0L/4T/1N.
```

Third QA pass (run 2, 2026-07-21), still pre-measurement:

```
AMENDMENT-6 (QA-2 R-2, BLOCKING — corrects AMENDMENT-1): the zero-fill is WITHDRAWN from every
  primary path. AMENDMENT-1 measured the fill on COVERAGE and never on the EVENT POPULATION.
  Measured now: on thin instruments the fill MANUFACTURES the absorption signature — a
  mostly-reconstructed window has near-zero range but keeps the real volume of its few traded
  minutes, and residualises as "heavy volume, no result". ALICEUSDT 5m candidates 32 -> 89 with 92%
  touching reconstructed minutes; ALICEUSDT 15m 2 -> 16 at 100%; SKLUSDT 5m 3 -> 20 at 90%; zero
  effect on LTC/SOL. It was confined to exactly the thin tail D6 expects breadth from, and it fed
  SPDR-009's D2 pool and W5's tau freeze. Replaced by window-integrity CLASSIFICATION
  (COMPLETE / NO_TRADE_PARTIAL / GAP_CONTAMINATED); only COMPLETE windows may be events or fit
  baselines; A8/A9/A10 added at the event layer where the damage occurred.
  DIRECTION LABEL CORRECTED: AMENDMENT-1 was booked TIGHTER on coverage grounds; for the EVENT
  POPULATION the fill was **LOOSER** (2-8x more candidates, almost all fabricated). AMENDMENT-1 is
  hereby re-scored **LOOSER**, and this amendment is TIGHTER for withdrawing it (QA-2 R-2).
  Count: 1L/5T/1N.
AMENDMENT-7 (QA-2 R-1): the claim that collection_gap_minutes = 0 "for every instrument" was FALSE
  and is withdrawn. Verified: outage_minutes = 0 holds universally, but 37 of the 194 universe have
  real collection gaps up to 138,240 minutes, including AVAXUSDT — one of SPDR-009's ten census
  instruments. Because max_gap_run_min == collection_gap_minutes, the gaps are single contiguous
  runs, so the remedy is WINDOW-level excision, not instrument exclusion: dropping the 37 would have
  left D1 on 194 and D2-D4 on 157, so the four pairs would not share a population in a design whose
  purpose is cross-pair comparison. DIRECTION: TIGHTER. 1L/6T/1N.
AMENDMENT-8 (QA-2 R-3, R-4, R-5, R-6, R-9): the A6 replacement is demoted from an assert to a
  REPORTED statistic (its revision-2 form assumed the fill and would have fired on the 37 gap
  instruments; "equal" is exact where band edges legitimately differ by +/-1); A10 added to count and
  NAME degenerate range cells on thin instruments at 5m; the W4 trace's mis-citation to SPDR-009
  GT-1 corrected (values were right, the session reference was not); whole-archive no-trade counts
  labelled as such beside DESIGN-band retention; LTCUSDT 60m obs/cell corrected 16 -> 15.5.
  DIRECTION: NEUTRAL (accuracy and disclosure). 1L/6T/2N.
AMENDMENT-9 (QA-2 R-7): the A-H4 prior-lowering is SCOPED. A-FUND's measured negative was
  BREAKOUT EXPECTANCY AFTER AN IB, not absorption detection at a level; it lowers the prior on
  anchor quality, not directly on S9 at D3. The unscoped revision-2 wording overstated it.
  DIRECTION: NEUTRAL (precision of an adverse claim). 1L/6T/3N.
AMENDMENT-10 (QA-2 R-8): the reference `zero_fill` helper in diag_coverage.py left Delta and
  Turnover null on filled rows where the spec said 0. Now moot on the primary path (the fill is
  withdrawn) but corrected in the diagnostic, which remains on disk as the pinned evidence for the
  withdrawal. DIRECTION: NEUTRAL. 1L/6T/4N.
```

Fourth QA pass (run 3, 2026-07-21), withdrawal incomplete + frame errors:

```
AMENDMENT-11 (QA-3 S-1, MAJOR): zero-fill withdrawal not fully propagated. §1.1 OBJECT-IDENTITY
  still defined the shared predicate "on a zero-filled LTF series" — the one line SPDR-009 imports.
  Also stale: §0 Produces, §1 blocker 4, §3 INFORMATIVE fill volumes, §7 modules/artifacts/plots/
  execution order ("W2a fill"). All rewritten onto the COMPLETE-window series. DIRECTION: TIGHTER.
  1L/7T/4N.
AMENDMENT-12 (QA-3 S-2, MAJOR): GAP_CONTAMINATED not computable from ledger (no gap timestamps).
  Derive gap days from staging (UTC day with zero bars in DESIGN span). In-band figure is **8 of
  194**, not 37; AVAXUSDT has zero DESIGN-band gap days (prior headline false); BNXUSDT/GSTUSDT
  are ledger misses. Contiguity claim (max_gap_run == collection_gap ⇒ single run) withdrawn for
  OMGUSDT-class instruments. DIRECTION: TIGHTER (false frame replaced by measured in-band rule).
  1L/8T/4N.
AMENDMENT-13 (QA-3 S-3, S-4, S-5 — operator-facing scope, not a machine gate): §5 understated
  coverage loss and omitted activity conditioning. Full-universe median retention 0.387 / 0.202 /
  0.089 at 5m/15m/1h; usable at 0.50 floor ≈72 / ≈47 / ≈31 vs 194 at D1; D2 is liquidity-limited
  too. Surviving COMPLETE windows carry 2.4×–27× the median volume of partials (universe median
  ~6.7× at 60m) — unequally across the cross-section. D1 complementarity restated: BTC/ETH zero
  signal events, not "the majors". DIRECTION: NEUTRAL (disclosure that changes SPDR-009's power
  projection and the D6 scope question). 1L/8T/5N.
AMENDMENT-14 (QA-3 S-6, S-7): A9 declared non-independent of A8 (staging min NTrades=1); blocker 1
  corrected from "raises otherwise" to the measured silent 80% dow-marginal fallback on coarse bars;
  diag_fill_bias's deliberate reliance on that behaviour recorded. DIRECTION: NEUTRAL. 1L/8T/6N.
AMENDMENT-15 (QA-4 N-1, MINOR): §5 labelled CRVUSDT 60m retention as "32nd percentile"; measured
  rank is ~69th (133/194 instruments retain less). Sample still flatters the thin tail; the rank
  label was inverted. DIRECTION: NEUTRAL. 1L/8T/7N.
AMENDMENT-16 (QA-6 I-4, MODERATE — design defect): GAP_CONTAMINATED presented as an active guard
  while being structurally unreachable for day-aligned windows over whole-day gaps (measured count
  0 across 194×3, incl. OMGUSDT's 42 gap days). §2 W2a now states the class is provably empty at
  5/15/60m and names gap_excision_report.json as the live disclosure. DIRECTION: NEUTRAL (a zero
  that read as "checked" now reads as "unreachable"). 1L/8T/8N.
AMENDMENT-17 (QA-6 I-1, MAJOR): W5's census population and level set diverged from SPDR-009's
  event definition and were forward-looking — the *current* session's IB edges were in every
  candidate's level set regardless of whether the IB had completed (SOLUSDT D2: 15 of 59
  candidates inside their own IB window, 4 with an unformed IB edge as nearest level, p90 0.105
  vs 0.282). §1.1 now defines level availability (prior-session levels at the open; IB edges only
  after the IB wall-clock) and the SPDR-009 refusal rule, both code-enforced in W5, with the
  pre-IB and refusal counts published per (symbol, pair). DIRECTION: TIGHTER. 1L/9T/8N.
AMENDMENT-18 (QA-6 I-2/I-3/I-5, MODERATE): the §3 HARD asserts ran only inside the reproduction
  battery, which the emitting run skipped; assert_levels_from_1m echoed a literal; D1 rested on
  run-local 1m thresholds that were never emitted (57 of 194 symbols had no pinned equivalent);
  the battery covered 5 symbols where A1 requires 194 and A2 137. Now: split-additivity, bar
  causality (vectorised, full frame) and forward provenance run on the emitting path; every JSON
  artifact is key-checked at write; level provenance is measured from the source series and the
  emitted frame; W3b emits and pins `class_thresholds_1m.json` for the full universe with a
  registry-overlap identity check; pins.json refuses to record a full-universe run without a
  passing full battery. DIRECTION: TIGHTER. 1L/10T/8N.
AMENDMENT-19 (QA-7 I7-1/I7-2, MAJOR): the availability test was asked at the candidate's OPEN and
  the design asserted, wrongly, that all four pairs nest into their IB boundary. A-USOPEN anchors
  at 13:30 UTC, so D4's hourly bars do not nest: all 32 D4 "pre-IB" candidates close 30 minutes
  AFTER the IB completes, and 18 were falsely refused. Separately, refusing the whole bar
  contradicted SPDR-009 §3.2 (one event per bar per level kind) and removed 1,109 of 9,497 D2
  candidates — systematically the short-distance ones — freezing τ on a distribution shifted wide.
  Now: session membership and level availability are both decided at the bar's CLOSE, and only the
  unformed IB EDGE is removed from a pre-IB bar's level set (operator decision 2026-07-21).
  DIRECTION: LOOSER-with-a-tightening-leg: pre-IB bars re-enter at non-IB levels (+1,109 D2,
  +11 D4 candidates); D4 also stops discarding valid events. Neither consults a forward price.
  2L/10T/8N.
AMENDMENT-20 (QA-7 I7-3…I7-9, MODERATE): a degenerate IB suppressed that session's prior-session
  levels too, silently dropping 71 candidates across 27 cells; W5 silently refit a run-local
  baseline when a pinned block was missing (the mechanism that hid the 5-symbol contamination);
  `--out-dir` did not cover the battery and `--from-w5` never checked that reused artifacts cover
  the run's universe; VT-4(g) was neither implemented nor demoted; `pins.json` and the battery
  bypassed the artifact key check; `pins.generated_utc` predated its own contents. All closed:
  prior-session levels survive a degenerate IB, `n_candidates_no_levels` makes the count identity
  hold, a missing pinned baseline marks the cell unmeasurable instead of refitting, the universe
  coverage of reused artifacts is asserted by name, VT-4(g) is demoted to declared, every artifact
  goes through the checked writer, and the pin is stamped at write time with the battery's covered
  modules. DIRECTION: TIGHTER. 2L/11T/8N.
AMENDMENT-21 (QA-8 I8-1/I8-2, MAJOR): (I8-1) with availability moved to the bar's close, a
  candidate could be measured against an IB edge its OWN minutes formed — acute at D3, where the
  IB is one 15m bar, so the IB bar's distance-to-edge was a distance to its own high/low
  (self-made distances 3–8× shorter, e.g. D3 p90 0.083 vs 0.656), pulling τ toward zero. Fixed by
  carrying INFR-018's ib_high_ts/ib_low_ts as `formed_ts` and excluding any level with
  `formed_ts ≥ OpenTime`; `n_ib_edge_self_made_excluded` published. (I8-2) the availability rule
  (session-at-close, mins_since_close, straddle, IB-edge filter) lived only in the runner, so
  SPDR-009 would have retyped the exact logic runs 6/7/8 rejected. Extracted to
  `xen.sigbar.ltf.assign_candidate_sessions` + `available_levels_for_candidates`; both consumers
  import it. DIRECTION: TIGHTER. 2L/12T/8N.
```

**Running count: 2 LOOSER / 12 TIGHTER / 8 NEUTRAL.** The first LOOSER is the re-scored
AMENDMENT-1, which AMENDMENT-6 then withdrew; the second is the pre-IB re-entry in AMENDMENT-19.
Both are recorded rather than netted out, so the ledger preserves the population changes.

```
AMENDMENT-22 (QA-9 R9-1, MAJOR): prior-session rows carried null `formed_ts`, so the shared
  availability rule treated them as inherently past-formed. That is false for D4's A-USOPEN-
  straddling hourly bar: its first 30 source minutes contribute to the session that becomes its
  prior session. Every structural level now carries non-null formation provenance; prior extrema
  carry their first edge-setting minute and prior POC/VAH/VAL carry the last contributing source
  minute. Missing/null provenance raises. Separate IB/prior/any self-made candidate counters are
  emitted, both census schemas are asserted before write, and D1 sensitivity cells now carry the
  complete schema including `measurable` and `n_candidates_straddling_anchor`.
  DIRECTION: TIGHTER. 2L/13T/8N.
```

**Running count: 2 LOOSER / 13 TIGHTER / 8 NEUTRAL.**
