# SPDR-002 — Design (Speed-Run leg 2/3: HTF context on naive-momentum LTF entries)

**Lane:** SPDR (TRAIN-only availability quantification) — spec `docs/references/spdr-lane.md`.
**Series:** leg 2/3 (CTRL-01 random = SPDR-001 done; CTRL-03 reversion = SPDR-003). **Candidate
disposition deferred to the post-SPDR-003 series verdict** — this is characterisation only.
NOT a cTrader experiment. Source `.ignore/temp/new-research/mtf.md` (CTRL-02 NAIVE MOMENTUM).

**Stage-5 mandatory (per lane spec):** a fresh-context data-analyst quantification pass
(`analysis.md`) runs before the operator sees results; `screen.md` stays neutral, subordinate to
it. **This design is analysed independently — no SPDR-001 result is imported; only the
methodology (causal primitives, control structure, quantify-not-qualify framing) is replicated.**

---

## 1. Question + mechanism

**Falsifiable question.** Does higher-timeframe context (ADX strength, DI direction, ATR vol
regime) measurably change the forward-return **distribution** of a naive LTF momentum-breakout
signal, relative to the unfiltered momentum baseline — in magnitude and shape, per stratum?

```
MECHANISM: A naive LTF momentum breakout (close breaks the last-3-bar extreme) is a real,
directional, informative signal (unlike CTRL-01's coin flip). HTF context can modulate it two
ways: (i) GATING — momentum's forward edge/dispersion may differ across HTF trend-strength (ADX)
or vol (ATR) regimes; (ii) CONFIRMATION — keeping only momentum trades whose direction agrees
with the last-closed HTF trend (DI). Horizon = hold H (1-4× the HTF/LTF ratio in LTF bars). Event
cadence = breakout events, active-hold blocks overlaps. P&L object = single per-trade open-to-open
forward return over H (single-leg; L-16 N/A).
DERIVED: estimand = per-trade ATR-normalised forward return distribution (mean + dispersion +
  hit-rate + tails) of the HTF-filtered momentum arm vs the unfiltered momentum baseline;
  null = unfiltered-momentum baseline (HTF-filter contribution) + matched-random-timing twin
  (momentum-vs-random availability) + HTF phase-shift future-destroy; horizon = H;
  test = block-bootstrap CI on the time-ordered trade series (+ seed battery for the random twin).
```

**Mechanism note (why every variant is a real test here).** Because the momentum breakout is a
directional, informative signal (not a symmetric coin flip), **every filter variant is a genuine
test** — gating asks "does momentum pay differently in this HTF regime", DI asks "does
HTF-direction confirmation change the momentum outcome". The HTF filter's contribution is measured
directly as the incremental effect over the unfiltered-momentum baseline (filtered − baseline).

**P-01 is NOT re-run.** Single-instrument directional price-geometry is a twice-dead *standalone
candidate* (P-01). Here naive momentum is a **control baseline being modulated by HTF context**,
not a standalone tradability candidate — the object under study is the HTF→momentum interaction,
and no disposition/tradability claim is made. State kept explicit.

---

## 2. Object identity

```
OBJECT-IDENTITY:
  measurement object == trading object: YES — both the single per-trade open-to-open return over H.
  measured conditioning event == traded entry event: YES — availability conditions on exactly the
    entry: bar t OPEN, given (a) a momentum breakout CONFIRMED on the last closed LTF bar t-1
    [Close(t-1) breaks the max-High / min-Low of bars t-2..t-4], and (b) the last fully-closed HTF
    bar (CloseTime < Open(t)) regime label. No close-execution, no band-touch seam (B-4 clean).
  effect-splitting windows non-overlapping: N/A — one forward-return effect per trade; active-hold
    prevents overlapping open positions within an arm.
```

**Causal breakout (anti-lookahead).** The breakout uses only CLOSED LTF bars ≤ t-1; the trade
executes at Open(t); HTF context from the last HTF bar closed strictly before Open(t) (reuse
`map_htf_to_ltf`). No forming bar — LTF or HTF — enters any decision. Golden-trace anchor.

---

## 3. Estimand (availability/lift — no P&L verdict)

- Per trade: `r = sig · (Open[t+H] − Open[t]) / ATR_LTF(14)[t−1]`, open-to-open, ATR-normalised
  (bps also reported; report a **raw-bps and a fixed-long-window-ATR** dispersion read alongside
  the ATR[t-1]-normalised one, so a normaliser artifact cannot be mistaken for genuine forward-vol
  conditioning — a standing methodological guard). `sig ∈ {−1,+1}` = momentum
  direction (DI-confirmation arm keeps only trades where `sig == htf_dir`).
- Per-arm distribution statistics (the "quantify not qualify" core): **mean, std, hit-rate
  (P[r>0]), skew, tail mass**, per stratum (instrument × domain-pair × hold-multiple × variant).
- **HTF-filter lift** = filtered arm − unfiltered momentum baseline, per stratum (paired).
- `xen.evaluation` toolbox only — **no local accounting** (L-18); availability metric, no
  `xen.adjudication` object, no estimand-validation gate in this lane (integrity substitute = §7).

---

## 4. Scope + grid

| Axis | Values | n |
|------|--------|---|
| Instruments (4-core) | EURUSD, XAUUSD, BTCUSD, USTEC | 4 |
| Domain pair (HTF/LTF) | 1d/1h, 4h/1h, 1h/5min | 3 |
| Hold × HTF/LTF ratio | 1d/1h→{24,48,72,96}; 4h/1h→{4,8,12,16}; 1h/5min→{12,24,36,48} | 4 |
| Filter variant | none(baseline)·ADX{<25,25–75,≥75}·DI·ATR{L,M,H}·[ATR×ADX{<25,≥25}]₆·[ATR×ADX×DI]₆ | 20 |

- **Cells** = 4×3×4×20 = **960**. All variants are real tests (no null-sentinel class).
  `none` = unfiltered momentum baseline (48 cells); DI-confirm variants (7×48=336) test HTF-
  direction agreement; gating variants test regime subsetting.
- **Momentum signal:** at entry bar `t`, using last closed bar `t-1`: LONG if
  `Close[t-1] > max(High[t-2], High[t-3], High[t-4])`; SHORT if
  `Close[t-1] < min(Low[t-2], Low[t-3], Low[t-4])`; else no signal. Active-hold blocks new signals.
  (Breakout of the **prior** 3 bars — exclusive of the breakout bar.)
- **Matched-random-timing twin:** ≥25-seed battery (L-19), same regime-eligible bar pool, matched
  entry count + hold, random entry timing — the no-timing-signal floor. Percentile/rank read.
- Params: ADX/ATR period 14; ADX thresholds 25/75; ATR-vol via `xen.vol_regime.regime_labels`
  (causal trailing-percentile, window 50, cuts 33/66). Reuse SPDR-001 causal primitives verbatim.
- **TRAIN-only fence:** first 70% of first 70%; terciles/normalisers TRAIN-only; entry+hold end
  < TRAIN cutoff. Never TEST/holdout. Data: INFR-003 5-year latest-glob (collection-timestamp
  select, exclude `analysis70_*`).
- Complexity: comparative screen (vectorised); 3 controls, ≤6 plot families, 1 screen module +
  analyst emissions.

---

## 5. Controls (each with validity proof)

```
CONTROL A — unfiltered-momentum baseline (isolates the HTF-filter contribution):
  question: what does the HTF filter ADD to (or subtract from) naive momentum?
  population: the `none` arm = all momentum breakouts, no HTF condition. Each HTF-filter arm is a
    subset selected on HTF state; DISJOINT selection rule (HTF-conditioned vs unconditioned) → the
    filtered arm can differ from baseline (B-1 ok). Degeneracy guard: a filter that admits ~all
    breakouts (e.g. ADX<25 in a low-ADX instrument) ≈ baseline by construction — flagged, its lift
    is trivially ~0, not evidence.
  bite/MDE: paired lift CI (filtered − baseline) via block bootstrap on the trade series; MDE per
    cell from n (see §6).
  non-vacuity: HTF conditioning changes the trade set (and, for DI, drops sign-disagreeing trades)
    → moves mean/dispersion/hit-rate (B-6 ok).
  expected if H true: filtered arm's mean/hit-rate/dispersion differs from baseline with CI clear.
    if H false: filtered ≈ baseline (lift CI straddles 0).
  disclosure: collapse fraction = baseline / filtered, per cell (B-2).

CONTROL B — matched-random-timing twin (momentum-vs-random availability; L-19 battery):
  question: does the (filtered) momentum TIMING beat random entries of matched regime/exposure?
  population: ≥25 seeded random-timing schedules in the same regime-eligible pool, matched entry
    count + hold. DISJOINT from the momentum-selected bars. Binding read = momentum arm's percentile
    within the seed distribution (rank), never a single twin.
  non-vacuity: random timing changes which bars are entered → moves the mean.
  expected if H true: momentum arm above the battery's upper percentile. if H false: inside it.

CONTROL C — HTF phase-shift future-destroy (leak tripwire on HTF-filter arms):
  destroy: roll the HTF context stream ±K HTF bars (K ≫ max hold) before applying the filter.
  non-vacuity: re-assigns which momentum trades pass the DI/gating filter → moves the mean.
  MUST collapse any HTF-alignment claim: a filtered arm whose lift over baseline SURVIVES the shift
    is not an HTF effect (the "filter" is picking up something contemporaneous) → REJECT that cell's
    HTF claim. Report collapse fraction per cell.
```

---

## 6. Test selection + power

- Per cell: **circular block-bootstrap CI** (`xen.evaluation.block_bootstrap_ci`, ≥10k × 5-seed,
  block capped < n; `block_sensitivity` ½×/1×/2×; `trimmed_mean`/median disclosed — L-20) on the
  time-ordered trade series, for **mean and dispersion**; report "CI excludes zero", not a p-value.
- HTF-filter **lift** (filtered − baseline): paired block-bootstrap CI on the difference.
- Random-timing twin (Control B): momentum-arm percentile within the ≥25-seed battery.
- Per instrument: **family-wise max-stat** over that instrument's HTF-filter cells (multiplicity
  disclosure over the large grid; EXP-021/022 discipline).
- Dose-response: ADX and ATR-percentile as continuous conditioners of the
  momentum outcome (mean + dispersion), rank-based, with CIs.

```
POWER: expected trades/cell ≈ breakout_rate × TRAIN_LTF_bars(regime subset) / (H + gap). Breakout
  cadence is sparser than CTRL-01's random draw (only 3-bar-extreme breaks) → thinner cells,
  especially under DI-confirmation + regime gating + long holds.
  MDE at n: reported per cell (ATR-normalised, comparable).
  Predeclared UNPOWERED (never a negative — B-5): ADX≥75 cells; ATR×ADX×DI triple-combo tails with
    n below the block floor; 1d/1h H72/96 sparse corners.
```

---

## 7. Interpretation bands + integrity split

```
BANDS (per stratum — quantification, no disposition):
  MATERIAL-SHIFT: filtered arm's mean/dispersion/hit-rate differs from baseline with CI clear of 0
                  AND (for an HTF-alignment claim) collapses under Control C.
  WASH:           lift CI straddles 0 — report as filtered ≈ baseline, not a refutation (L-11).
  ADVERSE:        HTF filter measurably worsens the momentum outcome (CI clear, opposite sign) —
                  reported as a magnitude, not a verdict.
  UNPOWERED:      n < block floor or MDE > plausible effect — excluded from negatives (B-5).
POOLED: disclosure-only; per-instrument/per-domain; heterogeneity expected (L-03), do not average.

NO DISPOSITION. SPDR-002 outputs magnitudes; the CTRL-01/02/03 candidate verdict is taken once,
after SPDR-003 (operator).
```

```
HARD (block/flag): TRAIN-only fence; causal LTF-breakout (≤ t-1) + HTF-bar-boundary (< Open(t));
  Control C collapse on any HTF-alignment claim; seed-battery regenerable.
INFORMATIVE (operator judges): all effect sizes, dispersion/hit-rate shifts, lift CIs, dose-response,
  collapse fractions, random-twin percentiles. No auto-verdict thresholds.
```

---

## 8. Golden trace (self-check diff target)

```
GOLDEN-TRACE (fill at build from TRAIN data, 3 events):
  G1 (4h/1h, EURUSD): a LONG breakout — find bar t-1 with Close[t-1] > max(High[t-2..t-4]); verify
     entry at Open(t), the last 4h bar with CloseTime < Open(t), its ADX/±DI/ATR; hand-check
     r = +(Open[t+8]−Open[t])/ATR_LTF[t-1].
  G2 (1h/5min): a SHORT breakout in a HIGH-ATR HTF regime; verify tercile from TRAIN only, HTF bar
     is last closed, DI-confirm arm keeps it only if htf_dir == −1.
  G3 (1d/1h): a breakout near the TRAIN boundary at H=96; verify exit bar t+96 still inside TRAIN
     (no holdout/TEST bar touched).
```

## 9. Code-asserted integrity checklist (replaces fresh-context QA; §7 HARD items)

Screen script asserts + prints PASS/FAIL before emitting:
1. **TRAIN fence** — max entry+hold CloseTime < TRAIN cutoff; 0 TEST/holdout rows read.
2. **HTF bar boundary** — every entry `HTF.CloseTime < LTF.Open(t)`.
3. **LTF breakout causal** — breakout uses only bars ≤ t-1; no forming-bar High/Low/Close.
4. **Seed battery** (Control B) — ≥25 seeds, regenerable byte-identical from (seed, bar-calendar).
5. **Baseline degeneracy flag** — report per filter arm the fraction of baseline breakouts it
   admits; flag arms admitting ~all (lift trivially ~0).
6. **Golden trace** — G1–G3 reproduced within tolerance.
Any FAIL blocks the screen read.
