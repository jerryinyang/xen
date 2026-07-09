# SPDR-001 — Design (Speed-Run: HTF context on random LTF entries)

**Lane:** SPDR (speed-run availability screen) — spec `docs/references/spdr-lane.md`.
**NOT** a cTrader experiment: TRAIN-only, vectorised Python, disposition-only, no read/holdout/family.
**Series:** SPDR-001 = CTRL-01 (RANDOM) only; SPDR-002/003 = CTRL-02 momentum / CTRL-03 reversion.
Source idea `.ignore/temp/new-research/mtf.md`. Operator decisions logged 2026-07-07.

---

## 1. Question + mechanism

**Falsifiable question.** Does conditioning a random-timed LTF position on higher-timeframe
context (trend *direction* via DI, trend *strength* via ADX, *volatility* via ATR) produce a
signal-conditional forward-return lift over the matched unfiltered random baseline, per stratum?

```
MECHANISM: A random LTF entry has an independent symmetric sign s (E[s]=0), so per-trade
E[s·r_fwd] = E[s]·E[r_fwd] = 0 for ANY bar-selection filter. The only way HTF context can move
that expectation is by conditioning the SIGN — i.e. the DI-direction filter, which aligns the
random-timed position to the last-closed HTF trend. So CTRL-01 isolates ONE thing: does HTF
context carry directional value on its own (HTF trend-continuation harvested with random micro-
timing)? Horizon = the hold H (1–4× the HTF period in LTF bars). Event cadence = random entries
gated by regime, active-hold blocks overlaps. P&L object = the single per-trade open-to-open
forward return over H (no multi-leg episode — L-16 N/A here).
DERIVED: estimand=mean per-trade ATR-normalised open-to-open forward return per arm;
         null=matched unfiltered/bar-selection-only twin + HTF phase-shift future-destroy;
         horizon=H (naive HTF/LTF ratio × {1,2,3,4}); test=seed-battery block-bootstrap CI +
         per-instrument family-wise max-stat over the DI-signal cells.
```

**Signal axis vs null sentinel (mechanism-honest, operator-confirmed).**
- **DI-containing variants** (DI alone; ATR+ADX+DI ×6) = the **signal axis** — sign is
  HTF-conditioned; these can carry non-zero edge.
- **Gating-only variants** (ADX-strength ×3; ATR-vol ×3; ATR+ADX ×6) = **built-in null
  sentinels** — bar-selection only, symmetric sign ⇒ expected effect **exactly 0**. They give a
  free empirical FPR floor and a sign↔price leak sentinel; a CI-excludes-zero here is
  multiplicity noise or a bug, not signal.

---

## 2. Object identity

```
OBJECT-IDENTITY:
  measurement object == trading object: YES — both are the single per-trade open-to-open return
    over hold H. Single-leg, no episode structure (L-16 N/A).
  measured conditioning event == traded entry event: YES — availability conditions on exactly the
    bar/state the position is opened at: LTF bar t open, gated by the last fully-closed HTF bar
    (< t) regime label. No band-touch/close-breach seam (B-4 N/A — market entry at bar open).
  effect-splitting windows non-overlapping: N/A — one effect (forward return over H) per trade;
    active-hold prevents overlapping open positions within an arm/seed.
```

**THE causal hazard (MTF bar boundary).** At LTF entry bar `t`, all HTF context (ADX, +DI/−DI,
ATR) must come from the **most recent HTF bar whose CloseTime < Open(t)** — never the
still-forming HTF bar (its OHLC/ADX would incorporate price ≥ t = look-ahead). This is the single
most likely leak in any MTF screen. Enforced in code + checked in the golden trace.

---

## 3. Estimand (availability/lift — no P&L verdict)

- Per trade: `r = s · (Open[t+H] − Open[t]) / Open[t]`, **open-to-open**, `s ∈ {−1,+1}`.
- Normalised: `r_norm = r / ATR_LTF(14)[t−1]` (comparability across instrument/domain; bps also
  reported). `xen.evaluation` toolbox only — **no local accounting** (L-18); this is an
  availability metric, not an `xen.adjudication` P&L object (no estimand-validation gate in this
  lane — the integrity substitute is §7).
- Per-arm statistic: **mean `r_norm`** across that arm's trades, aggregated over the seed battery.
- Reported per stratum: instrument × domain-pair × hold-multiple × filter-variant.

---

## 4. Scope + grid

| Axis | Values | n |
|------|--------|---|
| Instruments (4-core, operator) | EURUSD, XAUUSD, BTCUSD, USTEC | 4 |
| Domain pair (HTF/LTF) | 1d/1h, 4h/1h, 1h/5min | 3 |
| Hold multiple × HTF/LTF ratio | 1d/1h→{24,48,72,96}; 4h/1h→{4,8,12,16}; 1h/5min→{12,24,36,48} | 4 |
| Filter variant | none(baseline)·ADX{<25, 25–75, ≥75}·DI·ATR{L,M,H}·[ATR×ADX{<25,≥25}]₆·[ATR×ADX×DI]₆ | 20 |

- **Cells** = 4×3×4×20 = **960**. Signal (DI) cells = 4×3×4×7 = 336; null-sentinel (gating-only)
  cells = 4×3×4×12 = 576; baseline(none) = 4×3×4 = 48.
- *Doc miscount note:* `mtf.md` labels `ATR×ADX` and `ATR×ADX×DI` as "5 variants"; the full
  3(ATR)×2(ADX) cross is **6** — adopted 6 (complete cross), operator directive to proceed.
- **Seed battery** ≥25 per cell (L-19); aggregated, not per-seed verdicts.
- Params: ADX/ATR period **14**; ADX thresholds **25/75** (fixed, doc); ATR-vol LOW/MED/HIGH =
  **`xen.vol_regime.regime_labels`** — causal trailing rolling-percentile ATR(14) on the HTF
  bars (window 50, cuts 33/66; no future bar enters a label — stronger than global terciles);
  random `λ=2`
  (SELL:NEUTRAL:BUY = 1:2:1 ⇒ draw ≤ −0.5 sell, ≥ +0.5 buy).
- **TRAIN-only fence:** first 70% of the analysis set (itself first 70% of the file) — never TEST,
  never the final-30% holdout. Terciles/normalisers fit on TRAIN only. Asserted in code (§7).
- Data: latest-glob `data/timebars/timebars_<sym>_*.parquet` (INFR-003 5-year). LTF/HTF bars via
  `xen.bar_aggregator` clock-aligned OHLC; ADX/DI/ATR on the HTF bar series.
- Complexity: comparative screen (large grid, vectorised) — within SPDR intent; 2 controls, ≤5
  plot families, 1 screen module.

---

## 5. Controls (each with validity proof)

```
CONTROL A — bar-selection-only twin (matched baseline; isolates DI direction):
  question answered: is a DI-arm's edge from HTF *direction* or merely from *which bars* selected?
  population: each ATR+ADX+DI cell is paired with its ATR+ADX (same regime gate, DI removed) twin;
    DI alone is paired with baseline(none). DISJOINT in construction (sign-conditioned vs symmetric)
    — a different answer is possible whenever the DI alignment carries drift (B-1 satisfied).
  bite/MDE: paired-difference CI over the seed battery; MDE from per-cell n (see §6). Co-designed
    with the metric, not a fixed plant.
  non-vacuity: removing DI re-randomises the sign ⇒ flips E[s·r] from the aligned value to 0 —
    moves the mean directly (B-6 satisfied).
  expected if H true: DI-arm mean > its bar-selection twin (twin ≈ 0). if H false: DI-arm ≈ twin ≈ 0.
  disclosure: collapse fraction = (twin mean / DI-arm mean) reported per cell (B-2).

CONTROL B — HTF phase-shift future-destroy (leak tripwire):
  question answered: does the DI-arm edge depend on the HTF label actually aligning with THIS bar's
    forward window, or is it a spurious/leaked alignment?
  destroy: shift the HTF context stream by a large lag (±K HTF bars, K ≫ max hold) before assigning
    the DI sign — regime label no longer corresponds to the bar's own forward window.
  non-vacuity: the shift re-assigns the DI sign per bar ⇒ moves the mean (not a mean-preserving
    permutation — B-6; contrast EXP-012's vacuous permute).
  MUST collapse the edge; expected collapse fraction ≈ 1 (→ 0 edge). A DI cell whose edge SURVIVES
    the phase-shift is leak/spurious → that cell is REJECTED from any WORTH_EXPLORING claim.
```

Gating-only cells need no separate control — they *are* the CTRL-01 null; their battery should
straddle 0 (empirical FPR read).

---

## 6. Test selection + power

- Per DI-signal cell: seed-battery aggregated **circular block-bootstrap CI** on mean `r_norm`
  (`xen.evaluation.block_bootstrap_ci`, ≥10k resamples × 5-seed inner battery, block capped < n;
  `block_sensitivity` ½×/1×/2× and `trimmed_mean` disclosed — L-20). Report **"CI excludes zero"**,
  not a p-value.
- Per instrument: **family-wise max-stat permutation** over that instrument's 84 DI-signal cells
  (mirrors EXP-021/022 multiplicity discipline) — controls the large grid. FWER-significant cells
  are the WORTH_EXPLORING candidates.
- Gating-only cells: report the empirical fraction crossing zero vs the ~5% chance expectation
  (FPR sentinel); flag any that survive Control B (leak).

```
POWER: expected trades/cell ≈ TRAIN_LTF_bars(regime subset) / (H + gap); dense for 1h/5min &
  4h/1h, thinnest for 1d/1h at H=96 and for the ADX≥75 and HIGH-vol tail regimes.
  MDE at n: reported per cell from the block-bootstrap; ATR-normalised so comparable.
  Predeclared UNPOWERED (never read as negative — B-5): every ADX≥75 cell; ATR×ADX×DI triple-combo
    tails with n below the block-bootstrap floor; 1d/1h H=72/96 on the shorter TRAIN spans.
```

---

## 7. Interpretation bands + integrity split

```
BANDS (per DI-signal stratum):
  SUPPORTED:    mean r_norm ci_low > 0 with a material margin (> MDE) AND exceeds bar-selection
                twin (Control A) AND collapses under phase-shift (Control B).
  WASH:         CI straddles 0 / |effect| < noise — report as ≈0, not a refutation.
  CONTRADICTED: ci_high < 0.
  UNPOWERED:    n < block floor or MDE > plausible effect — excluded from negatives.
POOLED: disclosure-only; per-instrument/per-domain, never a single grid verdict.

DISPOSITION (SPDR vocab, per instrument then overall):
  WORTH_EXPLORING: ≥1 instrument has FWER-significant SUPPORTED DI cell(s) surviving Control B.
  NOT_WORTH:       DI cells WASH/CONTRADICTED across all instruments (gating sentinels ≈0 as expected).
  INCONCLUSIVE:    signal cells dominated by UNPOWERED — not a negative.
A WORTH_EXPLORING routes to a full cTrader-primary EXP + family registration; SPDR-001 itself makes
no tradability claim, spends no read, changes no family status.
```

```
HARD (block/flag): TRAIN-only fence; causal HTF-bar-boundary (< Open(t)); t−1 LTF lag; Control B
  collapse on any admitted DI cell; seed-battery regenerable from seed+bar-calendar.
INFORMATIVE (operator judges): all effect sizes, CIs, family-wise reads, collapse fractions,
  block/trim sensitivity, gating-sentinel FPR. No auto-verdict thresholds.
```

---

## 8. Golden trace (self-check diff target)

Hand-derive before running; the screen script must reproduce each:

```
GOLDEN-TRACE (fill at build from TRAIN data, 3 events):
  G1 (4h/1h, EURUSD): pick an LTF 1h entry bar t; record the last 4h bar with CloseTime < Open(t),
     its ADX/+DI/−DI/ATR(14); expected DI sign = +1 iff +DI>−DI; expected trade r for a given seed;
     verify NO 4h bar with CloseTime ≥ Open(t) was used.
  G2 (1h/5min): a HIGH-ATR-tercile 5min entry; verify tercile boundary came from TRAIN only and the
     HTF(1h) bar is the last closed one; hand-check r_norm = r / ATR_LTF[t−1].
  G3 (1d/1h): an ADX≥75 cell entry near a TRAIN boundary; verify H=96 exit bar is still inside
     TRAIN (no holdout/TEST bar touched by an entry+hold window).
```

## 9. Code-asserted integrity checklist (replaces fresh-context QA in this lane)

The screen script MUST assert, and print PASS/FAIL for, each before emitting results:
1. **TRAIN fence** — max entry+hold CloseTime < TRAIN cutoff; 0 rows read from TEST or holdout.
2. **HTF bar boundary** — for every entry, `HTF.CloseTime < LTF.Open(t)` (no forming HTF bar).
3. **LTF causal lag** — every regime/threshold input uses data ≤ t−1; terciles fit on TRAIN only.
4. **Seed battery** — ≥25 seeds, regenerable byte-identical from (seed, bar-calendar); no seed reads price.
5. **Gating-only sentinel** — report the empirical zero-crossing fraction (expected ≈ chance).
6. **Golden trace** — G1–G3 reproduced within tolerance.
Any FAIL blocks the screen read (integrity is hard even in the lean lane).
```
