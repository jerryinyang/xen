# SPDR-003 — Design (Speed-Run leg 3/3: HTF context on naive-reversion LTF limit entries)

**Lane:** SPDR (TRAIN-only per-stratum magnitude quantification) — spec `docs/references/spdr-lane.md`.
**Series:** leg 3/3, FINAL (CTRL-01 random = SPDR-001; CTRL-02 momentum = SPDR-002). **After this
leg the operator takes the combined CTRL-01/02/03 series verdict** — this leg is characterisation
only, no disposition. NOT a cTrader experiment. Source `.ignore/temp/new-research/mtf.md`
(CTRL-03 NAIVE REVERSION). Analysed **independently — only SPDR-001/002 methodology is replicated,
no findings imported.**

**Stage-5 mandatory (lane spec):** fresh-context data-analyst pass (`analysis.md`), base-conditional
+ granular per-stratum + quantify-not-qualify. `screen.md` neutral, subordinate.

---

## 1. Question + mechanism

**Falsifiable question.** Per stratum, what is the measured magnitude by which higher-timeframe
context (ADX strength, DI direction, ATR vol regime) changes the forward-return **distribution**
of a naive LTF limit-reversion entry — measured as HTF's own conditional effect, independent of the
base strategy's viability?

```
MECHANISM: A naive LTF reversion control rests a LIMIT at the recent extreme (buy-limit at the
last-3-bar low, sell-limit at the last-3-bar high), betting price reverts after touching the
extreme. Unlike CTRL-01/02 (market-at-open, no fill model), the entry is a RESTING LIMIT filled by
intrabar price on the 1-minute base bars — so the traded event is the FILL (limit touch), not the
signal bar. HTF context can modulate the post-fill reversion two ways: (i) GATING — reversion may
pay/disperse differently across HTF trend-strength (ADX) or vol (ATR) regime; (ii) CONFIRMATION —
keep only reversion trades whose side agrees with the last-closed HTF trend (DI). Horizon = hold H
(1-4× HTF/LTF ratio, LTF bars) measured FROM FILL. Event cadence = limit fills. P&L object = single
per-trade open-to-open forward return from the FILL price over H (single-leg; L-16 N/A — no multi-
leg episode, no moving-target exit; the exit is a fixed H-bar horizon, so L-14's moving-anchor trap
does not arise).
DERIVED: estimand = per-trade ATR-normalised forward return distribution from fill (mean/std/hit/
  tails) of the HTF-filtered reversion arm; null = unfiltered-reversion baseline (HTF contribution)
  + matched-random-timing twin WITH THE SAME FILL SIM + HTF phase-shift; horizon = H from fill;
  test = block-bootstrap CI on the time-ordered fill series (+ seed battery for the random twin).
```

**Base-conditional frame (binding, lane spec).** The naive reversion base is a *control baseline,
not a viable strategy*; its own failure is uncharacterised. So stage-5 reports two facets, NOT just
lift-over-baseline (which is confounded by the base's own failure):
- **Facet A** — the base reversion arm's OWN failure per stratum: location (mean ATR + raw bps, CI;
  median vs mean), directional accuracy (hit-rate; does the reversion side predict), shape (std,
  skew, ±2-ATR tail mass), availability-vs-random percentile (does reversion-limit timing beat a
  random-timed limit of matched fill-cadence), named failure-mode {(a) no edge / (b) tail-eaten /
  (c) horizon-decay / (d) loss-concentration}, horizon profile.
- **Facet B** — HTF's OWN conditional effect on the LTF outcome distribution per stratum,
  independent of base viability: between-HTF-state conditional-mean spread (e.g. `E[m|+DI]−E[m|−DI]`,
  across ADX buckets, across ATR-percentile), dispersion modulation (normaliser-guarded: raw-bps +
  fixed-long-window-ATR alongside ATR[t-1]-norm), sign-prediction excess (hit−0.5). Magnitudes + CIs.

**P-01 NOT re-run.** Naive reversion is a control baseline *modulated by HTF context*, not a
standalone directional-price-geometry tradability candidate — the object under study is the
HTF→reversion interaction; no tradability/disposition claim is made. Stated explicitly.

---

## 2. Object identity

```
OBJECT-IDENTITY:
  measurement object == trading object: YES — both the single per-trade open-to-open forward return
    from the FILL price over H bars, ATR[t-1]-normalised. Single-leg; fixed-horizon exit (no moving
    anchor, no scale-in) → L-14 / L-16 traps do not arise.
  measured conditioning event == traded entry event: YES — availability conditions on the FILL
    (limit touch) event, NOT the signal bar (B-4 — critical for a resting-limit strategy). HTF
    context is read from the last HTF bar closed strictly before the FILL bar's open. The forward
    return and all HTF/regime labels are anchored at fill.
  effect-splitting windows non-overlapping: N/A — one forward-return effect per fill; active-hold
    blocks a new signal while a position is open.
```

**Causal chain (three lags, all anti-lookahead):**
1. **Signal** — the limit price = extreme of CLOSED LTF bars ≤ t-1 (last 3 prior bars, exclusive of
   the forming bar). Trailing: each new signal before fill resets the resting limit to the new price.
2. **Fill (the new heavy piece)** — walk the **1-minute base bars** forward from the LTF entry-bar
   open; the limit fills at the first m1 bar that crosses it. Buy-limit fills when m1 `Low ≤ limit`;
   sell when m1 `High ≥ limit`. **Fill price:** at the limit if `Low ≤ limit ≤ Open` (buy) /
   `High ≥ limit ≥ Open` (sell); if the m1 bar **gaps through** (Open already past the limit), fill
   at the **m1 Open** (conservative — never a better-than-market fill). No intrabar look-ahead: a m1
   bar fills only on its own Low/High.
3. **Horizon** — H starts at the FILL bar. Exit at Open of (fill-LTF-bar + H). HTF label from last
   HTF bar with CloseTime < fill-LTF-bar Open.

**Expiry (operator-confirmed):** the trailing limit rests and resets on each new signal; if unfilled,
it expires when the resting window reaches **H LTF bars** (no trade). Expired = no fill = excluded
(counted as an availability/fill-rate statistic, not a return).

---

## 3. Estimand (availability/lift — no P&L verdict)

- Per fill: `r = side · (Open[fill_bar + H] − FillPrice) / ATR_LTF(14)[fill_bar − 1]`, ATR-normalised
  (raw bps + fixed-long-window-ATR also, for the dispersion normaliser guard). `side ∈ {−1,+1}` =
  reversion side (buy-limit → long, side=+1). DI-confirm arm keeps a fill only if `side == htf_dir`.
- **Note the entry base is FillPrice, not the signal-bar open** — the reversion is measured from
  where capital actually commits (B-4). Open-to-open on the exit leg.
- Per-arm distribution stats: mean, std, hit-rate, skew, ±2-ATR tail mass; **fill-rate** (fills /
  signals) as an availability statistic per stratum.
- `xen.evaluation` only — no local accounting (L-18); no `xen.adjudication` object; no
  estimand-validation gate in this lane (integrity substitute = §7/§9).

---

## 4. Scope + grid

| Axis | Values | n |
|------|--------|---|
| Instruments (4-core) | EURUSD, XAUUSD, BTCUSD, USTEC | 4 |
| Domain pair (HTF/LTF) | 1d/1h, 4h/1h, 1h/5min | 3 |
| Hold × HTF/LTF ratio (from fill) | 1d/1h→{24,48,72,96}; 4h/1h→{4,8,12,16}; 1h/5min→{12,24,36,48} | 4 |
| Filter variant | none(baseline)·ADX{<25,25–75,≥75}·DI·ATR{L,M,H}·[ATR×ADX{<25,≥25}]₆·[ATR×ADX×DI]₆ | 20 |

- **Cells** = 4×3×4×20 = **960**. `none` = unfiltered reversion baseline (48); every variant is a
  real test.
- **Reversion signal:** at LTF bar `t`, buy-limit = `min(Low[t-2], Low[t-3], Low[t-4])`, sell-limit
  = `max(High[t-2], High[t-3], High[t-4])` (extreme of the 3 bars prior to t-1). Both sides may be
  live; whichever fills first on the m1 walk is the trade (if both, the earlier m1 timestamp wins).
- **1-minute fill data:** the SAME TRAIN 1-minute base bars the LTF/HTF bars are aggregated from
  (`load_train_1m`); the fill walk is on m1 rows between the entry-bar open and the expiry.
- **Random-timing twin (Control B):** ≥25-seed battery; a random-timed resting limit at a random
  prior-bar extreme, run through the IDENTICAL fill sim, matched fill-count + hold. Percentile read.
- Params: ADX/ATR 14; ADX 25/75; ATR regime via `xen.vol_regime.regime_labels` (causal, win 50,
  cuts 33/66). Reuse SPDR-001 causal primitives verbatim.
- **TRAIN-only fence:** first 70% of first 70%; signal, fill walk, and exit all < TRAIN cutoff;
  a fill+H that would exit at/after the cutoff is dropped. Never TEST/holdout.
- Complexity: comparative screen; 3 controls, ≤6 plot families, 1 screen module + analyst emissions.

---

## 5. Controls (each with validity proof)

```
CONTROL A — unfiltered-reversion baseline (isolates the HTF-filter contribution):
  question: what does the HTF filter add to / subtract from naive reversion?
  population: `none` = all reversion fills, no HTF condition; each HTF arm is an HTF-state subset;
    DISJOINT selection rule → filtered arm can differ (B-1). Degeneracy guard: a filter admitting
    ~all fills ≈ baseline — flagged via admit_frac, lift trivially ~0.
  bite/MDE: paired lift CI (filtered − baseline) block bootstrap; MDE per cell from n (§6).
  non-vacuity: HTF conditioning changes the fill set (DI drops side-disagreeing fills) → moves
    mean/dispersion/hit (B-6).
  disclosure: collapse fraction = baseline / filtered per cell (B-2). FRAMED AS ONE LENS — it is
    confounded by the base's own failure (Facet A); Facet B is the unconfounded read.

CONTROL B — matched-random-timing twin, SAME fill sim (reversion-timing-vs-random; L-19 battery):
  question: does the reversion-limit TIMING beat a random-timed limit of matched fill-cadence?
  population: ≥25 seeded schedules resting a limit at a random prior-bar extreme in the same regime
    pool, filled by the identical m1 sim, matched fill count + hold. DISJOINT from the reversion
    fills. Binding read = reversion arm percentile within the battery (rank), never a single twin.
  non-vacuity: random placement changes which fills occur → moves the mean.

CONTROL C — HTF phase-shift future-destroy (leak tripwire on HTF-filter arms):
  destroy: roll the HTF context stream ±K HTF bars (K ≫ max hold) before applying the filter.
  non-vacuity: re-assigns which fills pass the DI/gating filter → moves the mean.
  MUST collapse any HTF-alignment claim; a surviving filtered-lift = not an HTF effect → REJECT that
  cell's HTF claim. Collapse fraction per cell.
```

---

## 6. Test selection + power

- Per cell: circular block-bootstrap CI (`xen.evaluation.block_bootstrap_ci`, seed battery, block
  capped < n; `block_sensitivity` ½×/1×/2×; `trimmed_mean`/median — L-20) on the time-ordered fill
  series, for mean AND dispersion; "CI excludes zero", not a p-value.
- HTF-filter **lift** (filtered − baseline): paired block-bootstrap CI (one lens, base-confounded).
- **Facet B conditional-effect**: between-HTF-state conditional-mean spread + CI (the unconfounded
  read); dose-response (ADX, ATR-percentile continuous), rank-based, CIs.
- Control B: reversion-arm percentile within the ≥25-seed random-limit battery.
- Per instrument: family-wise max-stat over HTF cells (multiplicity disclosure; EXP-021/022).

```
POWER: expected fills/cell ≈ fill_rate × signal_rate × TRAIN_LTF_bars(regime subset) / (H + gap).
  A resting-limit at a 3-bar extreme fills often on the m1 walk, but DI-confirm + regime gating +
  long holds thin cells; the fill model can also DROP signals (expiry) → generally sparser than
  CTRL-02's market entries. Report fill-rate per stratum.
  MDE at n: per cell, ATR-normalised.
  Predeclared UNPOWERED (never a negative — B-5): ADX≥75 cells; ATR×ADX×DI triple-combo tails below
    the block floor; 1d/1h H72/96 sparse corners; any cell with < ~30 fills.
```

---

## 7. Interpretation bands + integrity split

```
BANDS (per stratum — quantification, no disposition, no qualifier language):
  Report the measured Δ and CI per stratum. A stratum with a between-HTF-state conditional-mean
  spread whose CI is clear of 0 is a MAGNITUDE for that stratum (surface it named), not a "pass".
  UNPOWERED: n < floor or MDE > plausible effect — a power statement, excluded from negatives (B-5).
POOLED: disclosure-only (L-03); never a headline count.

NO DISPOSITION. SPDR-003 outputs per-stratum magnitudes for Facet A (base failure) and Facet B
(HTF conditional effect); the CTRL-01/02/03 series verdict is the operator's, after this leg.
```

```
HARD (block/flag): TRAIN-only fence; causal signal (≤ t-1) + causal m1 fill (no intrabar look-ahead,
  gap-through fills at m1 Open) + HTF-bar-boundary (< fill-bar Open); Control C collapse on any HTF
  claim; seed-battery regenerable; expiry/fill-rate emitted.
INFORMATIVE (operator judges): all effect sizes, dispersion/hit/tail shifts, lift CIs, Facet-B
  conditional spreads, dose-response, collapse fractions, random-twin percentiles, fill-rates.
```

---

## 8. Golden trace (self-check diff target)

```
GOLDEN-TRACE (fill at build from TRAIN data, 3 events):
  G1 (4h/1h, EURUSD): a buy-limit — limit = min(Low[t-2..t-4]); walk m1 from Open(t); verify fill at
     the first m1 with Low ≤ limit, fill price = limit (Low≤limit≤Open) or m1 Open (gap-through);
     verify H=8 measured from the FILL bar; HTF ctx from the last 4h bar with CloseTime < fill Open.
  G2 (1h/5min): a sell-limit that GAPS through on the fill m1 bar → assert fill at m1 Open (worse
     than the limit), not the limit price.
  G3 (1d/1h): a limit that never fills within H LTF bars → assert it EXPIRES (no trade, counted in
     fill-rate), and that no exit bar crosses the TRAIN cutoff.
```

## 9. Code-asserted integrity checklist (replaces fresh-context QA; §7 HARD items)

Screen asserts + prints PASS/FAIL before emitting:
1. **TRAIN fence** — signal, m1 fill walk, and fill+H exit all < TRAIN cutoff; 0 TEST/holdout rows.
2. **Signal causal** — limit price from bars ≤ t-1 only; no forming-bar extreme.
3. **Fill causal** — fill timestamp ≥ entry-bar open; fill on a m1 bar's own Low/High; gap-through
   fills at m1 Open (never better than market); no m1 bar after the exit consulted.
4. **HTF bar boundary** — HTF context CloseTime < fill-bar Open (anchored at FILL, not signal).
5. **Seed battery** (Control B) — ≥25 seeds, same fill sim, regenerable byte-identical.
6. **Fill-rate / expiry** — emitted per stratum; expired signals excluded from returns.
7. **Golden trace** — G1–G3 reproduced within tolerance.
Any FAIL blocks the screen read.
