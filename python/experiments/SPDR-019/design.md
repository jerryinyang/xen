# SPDR-019 — Design: naive signed breakout + opportunity-modulated capture geometry

- **Family / hypothesis:** `CF-VOLDIR-001` / `HYP-D6`
- **Checkpoint:** `2026-07-25-018-trade-opportunity-capture-geometry`
- **SoT (substance precedence):** `.ignore/what-next/alts/opportunity.md` §6.1 / §6.3 — this design
  narrows, never thins
- **Binding reflection inputs:** `docs/experiments-docs/checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/reflection-mid-volatility-model.md`
  §2 (evidence inventory + classes), §5.2 (the five layers), §5.4 (the residual target),
  §5.4a (cost exclusion), §5.9 (the layer protocol)
- **Governing amendments:** **AMENDMENT-C5** (gross-only measurement), **AMENDMENT-C6** (layer
  protocol), plus standing **C1** (cTrader replication-only), **C2** (claim refusals — unchanged)
- **Lane:** SPDR TRAIN-only · vectorised Python · 0 counted TEST reads · no family action · no XENA
- **Status:** DESIGN — **execution unauthorised**

```
SPREAD-COST-DISCLOSURE:
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: reported cost understates total cost; reported net performance is overstated
  prohibited_claims: fully-net, cost-complete, tradable, deployable
  NOTE (AMENDMENT-C5): cost enters NO estimand, threshold or comparison in this design.
    p_be_net and the cost floor are emitted per cell as a DISCLOSED REFERENCE only.
```

---

## §1 What this experiment is

> **Falsifiable question.** On a fixed, non-predictive, signed breakout entry, does any layer of the
> opportunity model — scale, volatility state, swing gate, or capture parameters — move the payoff
> residual `log R = log(W/L) − log((1−p)/p)` reliably above zero, relative to the unmodulated
> baseline?

`log R > 0` is exactly `p > p_be`, which is exactly `E[gross] > 0`. It is an identity, not an
approximation, and it contains no cost term — which is why AMENDMENT-C5 costs nothing in rigour.

**This is a capture-geometry experiment, not a direction experiment.** The entry is fixed and is not
the research subject. No entry parameter is tuned to improve `p`; direction is **measured, not
targeted** (SoT §1.2). A zero baseline residual is a **predeclared, acceptable, and expected**
outcome — SPDR-018 measured five exit geometries spanning a 5.3× powered `W/L` range, all on the
zero line.

```
MECHANISM: A three-bar pivot-plus-momentum breakout commits capital when price trades through the
  extreme of the momentum bar. Its P&L-bearing object is a single signed EPISODE (one entry, one
  exit, no scaling). The regularity under test is NOT that this entry predicts direction - SPDR-013
  established that unconditional/trend direction has no exploitable edge, and this design assumes
  p sits at its own break-even. The regularity under test is that FORECASTABLE MOVE SCALE, which
  SPDR-012/013/015 established at rank IC ~0.33 (H1/H4) and which rescales the entire magnitude
  distribution (top/bottom decile 3.71x, P90 ratio matching the mean ratio to two decimals), can be
  used to place the exit boundaries of that episode so that the realised payoff sits OFF the
  driftless mirror W/L = (1-p)/p. Event cadence: pivot events; the realised signal rate is
  MEASURED and EMITTED per delta level, never assumed. The falsifier is log R indistinguishable
  from zero under every layer at a stated MDE.
DERIVED:
  estimand = per-EPISODE signed gross return in bps, decomposed per cell into
             (p, W, L, W_L, p_be, log R); log R is the primary read. Episode-level because the
             traded object is an episode, not a bar (L-16/L-18).
  null     = the DRIFTLESS MIRROR log R = 0, derived from the mechanism's own identity
             (E[gross]=0 forces W/L=(1-p)/p). NOT "zero P&L" - 32.5% of SPDR-018's powered cells
             clear gross break-even, so a zero-P&L null would re-discover that and call it an
             effect. Plus a side-derangement and an entry-timing derangement (SS7).
  horizon  = the Active Hold Period, swept over the measured regime run-length scale
             (E[run] 18.9-23.1 H1 bars, MAE ~12); no horizon outside that scale is introduced.
  test     = block-bootstrap CI on log R with block >= holding horizon; dependence-matched block
             MDE (M-1) stated in LOG UNITS per cell before the run.
```

**Why this is not a reused stack.** The estimand is the identity residual of *this* episode object;
the null is that object's own arithmetic zero line; the horizon is set by the *measured* regime
run-length of the conditioning variable. None of the three would transfer to a different mechanism:
a mean-reversion or carry candidate has a different P&L object, a different zero line (carry is not
driftless), and no regime-run horizon. What is deliberately inherited is the `(p, W, L)` layer,
because that is the checkpoint's organising identity.

---

## §2 The entry — fixed, frozen, not the research subject

Verbatim from SoT §6.1. Index `[0]` = the decision bar (most recent **confirmed** bar), `[1]`,
`[2]` its predecessors. All state is `≤ t−1` relative to the order being live.

```
LONG:  low[1]  <  min(low[0],  low[2])   AND  ( (close[0] - close[1]) / ATR20) >  deltaThreshold
SHORT: high[1] >  max(high[0], high[2])  AND  (-(close[0] - close[1]) / ATR20) >  deltaThreshold

ENTRY:  LONG  = buy  stop at high[0];   SHORT = sell stop at low[0]
        order expires unfilled after `inactiveHold` periods
EXIT:   close after `activeHold` periods (Layer-4 variants replace this; L0 does not)
```

`ATR20` = **Wilder ATR(20) on the decision clock, evaluated at `[0]`, causal `≤ t−1`.** Single
definition, shared by every arm (see the CONVERSION-PIN, §7).

**`deltaThreshold` is FROZEN as a swept axis, not calibrated** (QA finding). It takes exactly three
values — **`δ ∈ {0.25, 0.5, 1.0}`** — and **all three are reported side by side**. There is no
calibration step, no selection of a "best" δ, and no tuning against any outcome: δ selects how
extreme the momentum bar must be, which is an entry property, and tuning it would be researching
direction (SoT §1.2). The realised **signal rate at each δ is emitted** so the population is
visible. `δ = 0.5` is the golden-trace anchor and carries no privileged status.

**Fill rule (declared; resolved causally, not approximated).** Stop-order fills are resolved on the
**1-minute bar stream** (`data/catalog/`, T1 lane), never on the decision clock's OHLC:

| Case | Fill |
|---|---|
| An M1 bar within the pending window trades through the stop price | Fill **at the stop price** |
| An M1 bar **opens** beyond the stop price (gap) | Fill **at that M1 open** — the adverse case, never improved |
| No M1 bar reaches the stop before `inactiveHold` elapses | **Expire unfilled**; the signal is recorded as an unfilled event, not dropped |

Unfilled signals are emitted and counted. **Fill rate is a reported quantity per cell**, because a
capture variant that changes the fill rate changes the population and would otherwise silently
re-select it.

**Exit fill rule (declared; the L4 devices need it and the entry rule does not cover them).** All
exits are resolved on the same **M1 stream**, causally:

| Exit | Fill |
|---|---|
| **Profit target** | first M1 bar trading through the target → fill **at the target price**; if an M1 bar **opens beyond** it, fill at that open |
| **Trailing stop** | the trail ratchets **once per M1 bar, on that bar's close**, and never intra-bar; it triggers on the first M1 bar trading through the trail level, filling **at the trail level** (or at the open if gapped through) |
| **Time exit** | at the **open of the first decision-clock bar at or after `activeHold`** — an open-to-open exit, matching the entry convention |
| **Precedence within one M1 bar** | if target and trail/stop are both reachable in the same M1 bar, the **adverse one fills** (trail/stop). Never assume the favourable ordering |
| **Precedence with the time exit** | a target or trail triggering **at or before** the time-exit bar's open takes precedence |

The adverse-precedence rule is deliberate: intrabar ordering is unknowable at M1 resolution, so the
screen takes the pessimistic branch every time rather than manufacturing a favourable path.

**No slippage model, no queue model, no partial fills.** This is a screen; SoT §6.1 is explicit that
booked P&L requires a native execution vehicle. Nothing here is a tradability claim.

---

## §3 Object identity

```
OBJECT-IDENTITY:
  measurement object == trading object: YES. Both are the signed EPISODE: fill at the stop price
    (or gap open) -> exit at the variant's exit rule. p, W, L are computed over episodes, never
    over bars, and never over an aggregate of bars belonging to one episode (L-16/L-18, B-8).
  measured conditioning event == traded entry event: YES. Every layer conditions on state known at
    the DECISION BAR CLOSE `[0]`, which is the bar whose extreme becomes the stop price - the exact
    state at which capital is committed. No layer conditions on the fill bar, the pivot bar `[1]`
    alone, or on any post-decision quantity (B-4).
  effect-splitting windows non-overlapping: YES. One episode occupies [fill_ts, exit_ts). A symbol
    holds at most ONE open episode at a time; a signal arriving while an episode is open is
    recorded as SUPPRESSED and counted, never silently dropped. Overlapping-window dependence
    between consecutive episodes is handled by block bootstrap with block >= the holding horizon
    (B-9, spdr-lane dependence rule).
```

**Flat legs.** `r == 0` episodes are excluded from `p` and counted as `p_flat` (SPDR-018 §6 item 7).
Immaterial at scale, but reported, and their existence is disclosed in every cell.

---

## §4 The layer protocol (AMENDMENT-C6 — BINDING)

### 4.1 Phase (a) — sequential characterisation, run in full

Every stage emits the full `(p, W, L, W_L, p_be, log R)` decomposition with block CIs, its own MDE
in log units, its evidence class, its fill rate, and its episode count. **No stage is skipped
because an earlier one read flat.**

| Stage | What runs | Variants | Read |
|---|---|---|---|
| **L0** | The entry with a **fixed** capture policy: `activeHold` = 1 period, `inactiveHold` = 2 periods, no target, no stop, no selection | 1 | The baseline `(p, W, L, log R)` and κ. **Mandatory first** — the entry carries a momentum prior, so without it every later change is misattributed |
| **L1** | **Scale alone.** ŝ = H1/H4 Parkinson-EWMA vol forecast, used ONLY to set `deltaThreshold` as a ŝ-decile rather than a constant | 4 (decile cuts d≥5, d≥7, d≥9, and the ŝ-continuous rank) | Δ`log R` vs L0; the full decomposition |
| **L2** | **State alone**, three cells, not one: **(i)** shock axis (HMM HIGH/LOW label), **(ii)** level axis (R-MARKOV k=4 and k=12 state), **(iii)** both jointly | 5 | Δ`log R` per axis **and the interaction term**. Their near-independence (51–62% agreement, V9/V10) is a pre-registered prediction under test |
| **L3** | **Swing gate alone.** `T-GT-CUR` fires / does not fire; parameters left at L0 values | 2 (+ T-GT-MED5 co-report) | Δ`log R`; **plus the mandatory L-51 three-number selection check** on every powered subset |
| **L4** | **Capture devices, one at a time.** Each device runs **twice**: unmodulated (a fixed ATR multiple) and modulated (the same multiple × ŝ) | see 4.2 | Δ`log R` per device; the unmodulated run is the comparator that separates the device from the information |
| **L5** | The small combination the L1–L4 reads justify | ≤ 4 | Term-level decomposition **alongside** any blended score. **L5 is evidence-selected and shares a sample with the reads that chose it — it does not and cannot substitute for phase (b)** |

### 4.2 The L4 device grid (SoT §6.3, all four devices)

| Device | Unmodulated | Modulated | What it moves |
|---|---|---|---|
| **Dynamic profit target** | `a × ATR20`, `a ∈ {1, 2, 3}` | `a × ŝ(h)` | `W` up, `p` down |
| **Trailing stop** | `b × ATR20`, `b ∈ {1, 2}` | `b × ŝ(h)` | `W` and `L` jointly, path-dependently |
| **Holding period** | `activeHold ∈ {1, 4, 12, 20}` periods | `activeHold` scaled to the state's `E[run]` | the horizon over which `W`, `L`, `p` are realised |
| **Position sizing** | fixed notional | `c / ŝ` | **variance and comparability ONLY.** Reported on dispersion, never on the mean (SoT §4.4). A sizing cell may not carry a `log R` claim |

Hold values are bounded by the **measured** regime run-length scale (`E[run]` 18.9–23.1 H1 bars,
MAE ~12 — evidence class `[D]`, so it sets a *scale*, never a timer). Nothing outside that scale is
swept.

### 4.3 Phase (b) — the full cross

> **Phase (a) determines WHETHER phase (b) runs. It does NOT determine WHAT is in it.**

**Trigger: the operator decides, on the full phase-(a) report.** No numeric cutoff is written here.
An earlier draft made phase (b) conditional on a cell's CI clearing zero on CONFIRM — that was
another invented gate, and the wrong shape for the same reason as the rest (INFR-016: machines gate
integrity, the operator judges value).

**What IS pre-declared, and what actually prevents the overfitting, is the SCOPE — not the
trigger.** Phase (a) may inform *whether* the operator authorises phase (b); it may never shrink
what phase (b) contains. That is the protection, and it survives the trigger being a judgement
call.

**Scope, fixed and independent of the (a) outcome:** the complete {L1, L2, L3} × {target, trail,
hold, sizing} cross on the same episode population. **Individually-flat layers stay in the grid on
equal footing** — a layer can be flat alone and productive in combination, and pruning makes that
permanently undiscoverable. **Estimand:** the **interaction**,
`Δlog R(combined) − Σ Δlog R(individual)`, not the combined main effect.

Phase (b) requires **its own operator execution authority** and a design amendment recording the
final cell count and per-cell MDE. It is not authorised by this document.

---

## §5 Estimand and the primary read

```
Per episode:  r = signed gross return in bps, from the ENTRY FILL price to the EXIT FILL price,
              both defined in SS2. (The time exit is open-to-open; target and trail exits fill at
              their own trigger prices. 'Open-to-open' describes the TIME exit only - it is not a
              blanket statement about every exit, and an earlier draft's wording implied it was.)
Per cell:     p     = P(r > 0)                    W = E[ r | r>0]     L = E[-r | r<0]
              W_L   = W/L                         p_be = L/(W+L)
              log R = log(W_L) - log((1-p)/p)     <-- THE PRIMARY READ
              identity assertion: |p*W - (1-p)*L - mean(r)| < 0.01 bps, EVERY cell
DISCLOSED REFERENCE ONLY (never a threshold, never a comparison, AMENDMENT-C5):
              cost, p_be_net = (L+cost)/(W+L), net mean, and the distance to the cost floor
```

**The mirror is exact, not fitted.** `log R = 0` ⟺ `W/L = (1−p)/p` ⟺ `p = p_be` ⟺ `E[gross] = 0`.
**The fitted-slope form (0.9408) is refused as a target**: its residual is centred at zero by
construction and no policy can beat it on average (reflection §A / audit A1).

κ = `median(r / mfe)` is reported as a **non-tradable, ceiling-relative diagnostic**. It multiplies
nothing (SoT §2.1).

---

## §6 Controls

```
CONTROL MIRROR-NULL (primary):
  question answered: is this cell's payoff distinguishable from the arithmetic zero line its own
    rate forces?
  population: the cell's own episodes. NOT disjoint by construction - and it does not need to be,
    because this is a POINT null (log R = 0), not a two-population comparison. The disjointness
    requirement (B-1) applies to matched-control designs; stated here explicitly so QA does not
    read its absence as an omission.
  bite/MDE: block-bootstrap CI on log R, block >= holding horizon. Per-cell MDE in log units is
    emitted BEFORE the read (see SS8), together with the control's own sensitivity ladder. No
    adequacy cutoff is applied; the reader judges resolution from the ladder.
  non-vacuity: log R is a function of p, W and L jointly; the null perturbs none of them - it is
    an analytic reference value, so vacuity does not arise. What could refute it: any cell whose
    CI excludes 0.
  expected outcome if H true: log R CI-low > 0 on some cell. If H false: CI covers 0 (the
    SPDR-018 result, where the centre sat at -0.0301).
  disclosure: the distance in log units and the implied bps, both reported.

CONTROL SIDE-DERANGEMENT (within_sample_attribution - REPORT LAYER):
  question answered: does the entry's SIDE carry information, or would random sides produce the
    same payoff geometry?
  population: the same episodes with sides deranged; DISJOINT in labelling from the live series -
    every episode's side differs from its own (zero fixed points).
  bite/MDE: >= 2000 seeds; plant curve co-designed - inject +5/+10/+20/+40 bps of true side
    information and report the detection rate at each. The control is reported UNUSABLE for any
    effect below its own plant-curve resolution.
  non-vacuity: deranging the side flips the sign of r, which moves the MEAN, p, W and L - the
    exact sufficient statistics of log R. It is not mean-preserving (B-6 satisfied).
  expected outcome if H true: live log R above the null distribution. If H false: inside it.
  disclosure: percentile + the null's own mean, sd and quantiles (P-24), never a bare percentile.
  destroy form: DERANGEMENT (zero fixed points, asserted and counted; L-28).

CONTROL ENTRY-TIMING DERANGEMENT (within_sample_attribution - REPORT LAYER):
  question answered: is the payoff geometry a property of the SIGNAL's timing, or of the ambient
    return distribution at matched holding length?
  population: episodes whose entry timestamps are deranged within symbol, holding length and side
    preserved. Disjoint in timing from the live series (zero fixed points).
  bite/MDE: >= 2000 seeds; same plant curve.
  non-vacuity: re-timing changes which returns are realised -> moves p, W, L (B-6 satisfied).
  expected outcome if H true: live log R above the deranged null. If H false: inside it.
  disclosure: percentile + null mean/sd/quantiles.
  destroy form: DERANGEMENT (L-28).

CONTROL MAGNITUDE-MATCHED COMPARATOR (M-3 - MANDATORY for L1 and L3):
  question answered: for any layer defined on move SIZE, is the effect "the volatility state" or
    merely "this was a big bar"? SPDR-018 measured mag_high at percentile 0.46 against exactly
    this comparator - the distinction is real and it has bitten before.
  population: episodes NOT selected by the layer, matched on realised |decision-bar move| decile.
    DISJOINT from the selected population by construction; disjointness asserted per decile.
  bite/MDE: plant curve per decile; the comparator is reported UNUSABLE where its own plant curve
    is blind.
  non-vacuity: it substitutes a different episode population at matched magnitude - p, W, L all
    move.
  expected outcome if H true: selected log R above matched. If H false: equal.
  disclosure: MANDATORY per P-24 - the comparator's OWN mean, its null quantiles, AND its plant
    curve are emitted with every percentile. A percentile alone is uninterpretable and is refused.
```

### 6.1 Leak tripwire (HARD — blocking)

```
TRIPWIRE-1 (causal misalignment):
  form: rebuild every layer's conditioning state from bar `[+1]` (one bar into the future) instead
    of `[0]`, and re-run the identical pipeline.
  must materially change the edge; expected direction: the leaky twin's log R is HIGHER.
  vacuity check: the leaky state changes which episodes are selected and how their exits are
    placed -> it moves p, W and L, the sufficient statistics of log R. A destroy that could not
    move them would be vacuous; this one does.
  if permutation-based: N/A (not a permutation - a deliberate index shift).
  HARD: if the legal and leaky variants are INDISTINGUISHABLE, the causal construction is
    unproven and the emission is invalid. Recorded as a count, never a vacuous pass (P-23/L-52).

TRIPWIRE-2 (fill-rule look-ahead):
  form: re-resolve stop fills using the decision-clock bar's OHLC instead of the M1 stream.
  must differ; a screen that cannot tell these apart is not resolving fills causally.
  HARD.
```

---

## §7 Unit pin (L-21 / P-15)

```
CONVERSION-PIN:
  divisor object 1: Wilder ATR(20) on the decision clock, evaluated at bar [0], causal <= t-1.
                    This is the deltaThreshold and unmodulated-device normaliser. Verbatim from
                    SoT 6.1; single definition shared by every arm.
  divisor object 2: s_hat = LTF H1 Parkinson EWMA(lambda=0.94), 60 H1-bar warm-up, causal <= t-1,
                    in bps, horizon-scaled s_hat*sqrt(h). IDENTICAL object to SPDR-014's Z-VOL
                    width and SPDR-018's unit pin - reused, not redefined.
  measured value:   TRAIN-median of BOTH objects, per symbol and pooled, COMPUTED AT RUN ->
                    results/unit_pin.json. Never recalled, never asserted. Covers all 25 symbols
                    or states the gap explicitly.
  resulting effect: every effect reported in BOTH bps and sigma units, side by side, on every cell.
  cost floor:       13.1-16.1 bps partial (fees + discrete funding + allowance); spread NOT
                    charged, so the true floor is strictly higher. Emitted as a DISCLOSED
                    REFERENCE only - no read in this design is compared against it (AMENDMENT-C5).
                    A sigma-unit effect is NEVER compared to the floor (P-15).
```

**bps is primary everywhere.** σ̂-normalisation buys pooling power; it never becomes a headline in
its own units.

---

## §8 Resolution statement — sensitivity across a range, not a single bar

Derived from SPDR-018's emitted cells, **computed not asserted**
(`results/analyst_per_cell_magnitudes.parquet`, 1,413 powered cells):

```
mean = (1-p)*L*(R-1)   =>   Delta log R ~= Delta mean / ((1-p)*L)
median (1-p)*L on powered cells = 48.54 bps
median block MDE on the mean    =  6.51 bps
=> a typical SPDR-018 powered cell resolves Delta log R ~= 0.123 (IQR 0.099 - 0.151)
```

**That is 2–4× coarser than the effect this experiment is looking for.** Required episode counts,
scaling MDE ∝ 1/√n from a median powered cell of n = 3,427 episodes:

| Target `Δlog R` | n multiple needed | Implied episodes per cell |
|---|---:|---:|
| 0.07 | **3.1×** | ~10,800 |
| 0.05 | **6.0×** | ~21,200 |
| 0.03 | **16.8×** | ~58,800 |

**The available population, read from the artifact — not from date arithmetic.**
`SPDR-018/results/unit_pin.json` records the actual TRAIN bar count:

```
pooled H1 bars, 25 symbols, full TRAIN = 229,646     <-- NOT 25 x 21,648 = 541,200
  only MATICUSDT (21,582) spans the window; median symbol = 12,444; smallest = 555
  catalog history cap: the panel is one symbol deep before 2022-07-14 (M-4)
```

*(An earlier draft assumed ~541k bars from the TRAIN date range. That was wrong by 2.35× and the
correct figure was in the file this section already cited. Corrected here against the artifact.)*

**Two power levers are applied, both for power alone** (operator directive 2026-07-28):

| Lever | Effect on `n` | Cost |
|---|---|---|
| **Full TRAIN is the primary read**; DESIGN/CONFIRM scored as verification | **~2×** | The band split becomes a stability check rather than the primary object. SPDR-018's own power lever 2 |
| **M15 added as a capture clock**, with the scale forecast ŝ still computed on **H1** | **~4×** | Multiplicity: two clocks reported separately, never pooled. Legitimate because the capture question is about exit geometry, not intraday forecast skill — V4's "no within-day skill" constrains the *forecast*, which stays on H1 |

```
RESOLUTION (replaces the pass/fail POWER block; operator mandate 2026-07-28):
  Every cell emits a SENSITIVITY LADDER instead of a powered/unpowered verdict. For a fixed
  ladder of candidate effect sizes, the cell reports the fraction of block-bootstrap replicates
  in which a PLANTED effect of that size would have been detected at its own realised n:

      ladder = { 0.02, 0.03, 0.05, 0.075, 0.10, 0.15 }  log units

  Emitted per cell:  realised n | block MDE | CI width | detection rate at each ladder rung |
                     the n that WOULD be required at each rung.
  The ladder is a PRESENTATION grid, not a set of thresholds: no rung admits, excludes, labels or
  ranks any cell. It exists so the reader sees WHERE a cell's resolution falls rather than being
  handed a boolean.
  No cell is flagged powered, unpowered or NOT_RESOLVABLE. A cell with poor resolution reports
  poor resolution, in numbers, and is still reported in full.
  MDE is always the dependence-matched BLOCK form (M-1, block >= the holding horizon); the iid
  form is companion-only and may never be presented as the cell's resolution.
```

**What this changes and what it does not.** The conversion `Δlog R ≈ Δmean / ((1−p)·L)` and the
`n`-scaling below are **derivations** and stand unchanged — they are how resolution is computed. What
is removed is the single canonical bar that used to turn them into a verdict.

```
EXPECTED RESOLUTION (a prediction, never a result - realised values are emitted per cell):
  H1  pooled, full TRAIN: 229,646 bars (artifact-grounded)
  M15 pooled, full TRAIN: ~4x the H1 count; COMPUTED AT RUN, never assumed
  signal rate: MEASURED and EMITTED per delta level. Indicative measurement at delta = 0.5 puts
    it near 10% of bars - an earlier draft's "1-5%" was wrong.
  fill rate:   MEASURED and EMITTED per cell (stop orders do not all fill).
  => indicative baseline episode counts, full TRAIN, pooled across symbols:
       H1  ~13k-16k    -> resolution lands around the 0.07 rung
       M15 ~50k-60k    -> around the 0.05 rung, approaching 0.03
     Narrow selections (top-decile s_hat) cut n ~10x and land several rungs coarser; coarse
     selections (halves, state labels) land close to the baseline. Per-symbol cells land at the
     coarse end of the ladder throughout.
  Sizing cells are reported on DISPERSION only and carry no log R resolution read at all.
```

**Consequence, stated plainly:** the primary reads live on **M15, full TRAIN, pooled across
symbols**, because that is where resolution is finest. H1 is the co-report and the clock-effect
check; per-symbol is heterogeneity disclosure. None of these is an admissibility rule — every cell
is reported with its own resolution attached, and the reader weighs them.

---

## §9 Interpretation bands — CI-relative, with no adequacy label (operator mandate 2026-07-28)

**Precision-first.** No cell carries a `powered` / `unpowered` / `NOT_RESOLVABLE` flag. Every cell
reports its **effect, its block-bootstrap CI, its CI width, its block MDE, and its resolution curve**
(§8), and the reader judges adequacy. Powering is left to later verification, not asserted here.

```
BANDS (per cell, on log R - defined by the CI's relation to the mirror, NOT by any magnitude):
  ABOVE THE MIRROR:  ci_low  > 0     the residual is resolvably positive on this cell's own data
  COVERS THE MIRROR: ci spans 0      report the point estimate, the CI WIDTH and the MDE together,
                     so a wide-CI cell and a genuinely-null cell are visibly different. This is
                     NEVER a refutation and NEVER a negative.
  BELOW THE MIRROR:  ci_high < 0     the residual is resolvably negative - itself a finding
                     (SPDR-018's centre sat at -0.0301)
No magnitude threshold appears in any band. An earlier draft used +-0.03 and a 0.07 adequacy
cutoff; both were anchored on sd(log R)=0.0729 and median log R=-0.0301, which are DISPERSION and
LOCATION of the observed residual - neither is a statement about what effect size matters. Removed
by operator mandate.

POOLED: pooled-across-symbol figures are the PRIMARY read by construction (SS8), reported WITH a
  homogeneity statistic (I^2 across symbols) so pooling is justified rather than assumed.
  Per-symbol figures are disclosure.
EVIDENCE CLASS: rows still carry [S] scored / [D] disclosure per reflection SS2.0 - these describe
  WHAT KIND of read a row is, not whether it is adequate. The [P]/[U] adequacy classes are
  RETIRED for this experiment; adequacy is read off the MDE and resolution curve.
```

**No band is a gate, and no band is an adequacy claim.** Every value/quality read is a report layer;
the operator authorises what advances (INFR-016). Nothing is machine-dropped between layers.

**The B-5 protection is strengthened, not weakened.** B-5 exists so a thin cell is never read as a
negative. A boolean `UNPOWERED` flag delivered that with an invented cutoff; **binding every effect
to its own MDE and CI width on the same row delivers it without one** — no effect can be quoted
without its precision travelling alongside it, which is a stricter constraint than a label that can
be dropped in summary.

---

## §10 Scope

| Item | Freeze |
|---|---|
| Primary catalog | Bybit USDT linear perps, `data/catalog/`, INFR-011 fence |
| Fill resolution | **M1 (T1 lane) bars**, causal, no intrabar look-ahead |
| Universe | top-25 30d USD volume (AMENDMENT-U1); pin `cf-voldir-001-universe.json`; recompute + assert set equality |
| Clocks | **M15 primary** (power), **H1 co-report** (the clock-effect check). The scale forecast ŝ stays on **H1** — V4's no-within-day-skill finding constrains the forecast, not the trade clock. No D1. Clocks reported separately, **never pooled** |
| TRAIN fence | `analysis_start 2021-06-29T06:53Z` → `train_end 2023-12-18T00:00Z`; asserted in code |
| Primary band | **Full TRAIN** (power lever 2). DESIGN `[2021-06-29, 2023-03-01)` / CONFIRM `[2023-03-01, 2023-12-18)` both scored as **verification**, `n`-weighted |
| Global holdout | `2025-01-08T00:00Z` — **never queried** |
| cTrader | **Not in phase (a).** Replication is a separate leg under AMENDMENT-C1 if the operator authorises it; never pooled into `n` |
| Complexity | 1 entry module, 1 layer module, 4 device modules, 1 metrics layer, 1 control module; ≤ 8 plots |
| `deltaThreshold` | **frozen**: `{0.25, 0.5, 1.0}`, all reported, none selected (§2) |
| Cell count | phase (a): **≤ 60 cells** (L0 1 + L1 4 + L2 5 + L3 3 + L4 ~44 + L5 ≤4) × 2 clocks × 3 δ, on full TRAIN, + the two verification bands. Disclosed, not rationed (AMENDMENT-C3 precedent) |

---

## §11 Golden traces (QA derives the numbers — the developer must not)

Deterministic selection rules, so QA computes expected values independently from the catalog.

```
G1 (entry + fill, the L0 baseline):
  BTCUSDT, H1, DESIGN. The FIRST bar satisfying the LONG condition at deltaThreshold = 0.5.
  QA computes: the three bar OHLCs, the pivot test, the ATR20 value at [0], the momentum ratio,
  the stop price (= high[0]), the first M1 bar that trades through it, the fill price, the exit
  timestamp at activeHold = 1, the exit price, and r in bps.

G2 (expiry path):
  ETHUSDT, H1, DESIGN. The first SHORT signal whose stop is NOT reached within inactiveHold = 2.
  QA confirms: the order expires, the signal is EMITTED as unfilled, and it contributes to the
  fill-rate denominator but to no (p, W, L) term.

G3 (suppression, the B-9 guard):
  Any symbol, H1, DESIGN. The first signal arriving while an episode is already open.
  QA confirms: it is recorded SUPPRESSED and counted, and does NOT open a second episode.

G4 (the identity, and the primary read):
  The L0 pooled H1 CONFIRM cell. QA computes p, W, L from the emitted episode rows and asserts
  |p*W - (1-p)*L - mean| < 0.01 bps, then recomputes log R = log(W/L) - log((1-p)/p) from those
  same three numbers and asserts it equals the emitted log R exactly.

G5 (the mirror null is the exact one):
  The same cell. QA asserts that the emitted null reference is 0 for log R defined with SLOPE 1,
  and that NO fitted-slope residual appears anywhere in the emission. This trace exists solely to
  make audit item A1 non-repeatable.

G6 (leak discrimination):
  The G1 rows under TRIPWIRE-1's leaky twin. QA confirms a material difference and that the legal
  variant is the one emitted.
```

---

## §12 Integrity checklist (code-asserted; SPDR stage-2 self-check)

| Check | Assertion |
|---|---|
| **Check count** | the self-check asserts the **expected NUMBER** of HARD checks and reconciles them **by name** against this table (P-23 / L-52) |
| TRAIN fence | `max(exit_ts) < 2023-12-18T00:00Z`; zero rows at or after it |
| Holdout | zero queries `>= 2025-01-08` |
| Causality | every layer's state index `<= [0]`; ATR20 and ŝ exclude the decision bar's own forward information; TRIPWIRE-1 |
| Fill causality | every fill's M1 timestamp `>` its decision-bar close; TRIPWIRE-2 |
| Universe pin | top-25 recompute == pin file, set equality |
| **Identity reconstruction** | `\|p·W − (1−p)·L − mean\| < 0.01 bps` on **every** cell |
| **`log R` definition** | asserted equal to `log(W/L) − log((1−p)/p)` with **slope 1**; a fitted-slope residual appearing anywhere is a **hard failure** |
| **Cost isolation** | no cost term enters any estimand, threshold, band or comparison; `p_be_net` present and flagged `DISCLOSURE_ONLY` (AMENDMENT-C5) |
| **MDE column** | the reported resolution column is the **block** MDE in log units; the iid column is labelled companion-only (M-1) |
| **No adequacy flag** | asserted that **no** `powered` / `unpowered` / `at_target` / `NOT_RESOLVABLE` column is emitted anywhere, and that no single canonical MDE threshold appears in code (operator mandate 2026-07-28) |
| **Ladder emitted** | the sensitivity ladder is present on **every** cell, with its detection rates and required-`n` values |
| **Span disclosure** | exact-span subset and span distribution per horizon cell (M-2) |
| Episode exclusivity | at most one open episode per symbol; suppression count emitted |
| Fill rate | emitted per cell; unfilled and suppressed signals counted, never dropped |
| Derangements | fixed-point count == 0, measured and reported (L-28) |
| Determinism | runs **unconditionally** whenever `--jobs > 1`, independent of `--resume`; parallel bit-identical to sequential (P-23) |
| Golden traces | G1–G6 pass |
| No local accounting | screen metrics are availability/residual bps, not booked P&L; no `xen.adjudication` mimicry |
| Code hash | sha256 of `screen_code/` pinned into `results/integrity_selfcheck.json` |

```
HARD (block execution / invalidate emission):
  check-count reconciliation, TRIPWIRE-1, TRIPWIRE-2, TRAIN fence, holdout, causality,
  fill causality, universe pin, identity reconstruction, log R definition, cost isolation,
  derangement fixed-point count, golden traces, determinism.
INFORMATIVE (operator judges, no auto-verdict):
  every effect size, control percentile, collapse fraction, band label, dose-response shape,
  fill rate, kappa, cost overlay, heterogeneity statistic.
```

Every check depends on an **emitted artifact** — missing or empty is a **failure**, never a vacuous
pass (P-23). No required check lives in a manual post-step (L-52).

---

## §13 What this design refuses

- **Any cost term in any estimand, threshold or comparison** (AMENDMENT-C5). Cost is disclosure.
- **Any expectancy, tradability, deployability or cost-complete claim** (AMENDMENT-C2, unchanged).
- **The fitted-slope residual as a target** — it is centred at zero by construction (audit A1).
- **Scoring any capture variant against zero P&L** rather than against the mirror.
- **Any rule, band or gate phrased against `p > 0.5`** — the reference is `p_be` (SoT §2.2).
- **Researching direction prediction**: no new entry model, no trend filter, no tuning of any entry
  parameter to improve `p`. `deltaThreshold` is calibrated for **sample size**, not for `p` — and
  its calibration is emitted so QA can verify which was optimised.
- **Combining layers before characterising them individually** (AMENDMENT-C6).
- **Pruning phase (b) to phase (a)'s winners** — the scope is fixed and includes flat layers.
- **Reading a coarse-resolution cell as a negative** (B-5), or reading a CI that covers the mirror as a refutation.
- **Emitting any `powered` / `unpowered` / `NOT_RESOLVABLE` flag, or any single canonical adequacy threshold** — retired by operator mandate 2026-07-28; resolution is reported as a ladder and adequacy is the reader's judgement.
- **A per-symbol `log R` conclusion carried without its resolution ladder** — per-symbol cells resolve coarsely (§8) and are heterogeneity disclosure.
- **A blended score without its term-level decomposition** (SoT §7).
- **A sizing cell reported as improving expectancy** (SoT §4.4).
- Any family status change; any XENA; any TEST or holdout contact.

---

## §14 Amendment ledger

```
AMENDMENT-1: full TRAIN becomes the primary read; DESIGN/CONFIRM scored as verification.
  - DIRECTION: LOOSER (more n per cell; the band split stops halving the primary read)
  - Operator directive 2026-07-28, for POWER. SPDR-018's own power lever 2.
AMENDMENT-2: add M15 as the primary capture clock; H1 becomes co-report. The scale forecast
  s_hat REMAINS on H1.
  - DIRECTION: LOOSER (~4x the bars)
  - Operator directive 2026-07-28, for POWER. V4's no-within-day-skill result constrains the
    FORECAST clock, which is unchanged; the trade clock is a separate object.
AMENDMENT-3: freeze deltaThreshold as a swept axis {0.25, 0.5, 1.0}, all reported, none selected.
  - DIRECTION: TIGHTER (removes an unpinned parameter that swung power ~7x)
  - QA finding, run 1.
AMENDMENT-4: specify exit fill resolution for target / trail / time, with ADVERSE precedence
  inside an M1 bar; correct the SS5 open-to-open wording to apply to the time exit only.
  - DIRECTION: TIGHTER (pessimistic branch taken every time; a specification gap closed)
  - QA finding, run 1.
AMENDMENT-5: correct the SS8 population figure to the artifact value (229,646 pooled H1 bars,
  not the ~541k implied by the TRAIN date range) and the signal rate to a measured quantity.
  - DIRECTION: NEUTRAL (a factual correction; it makes the power statement harsher, not looser)
  - QA finding, run 1.

AMENDMENT-6: retire the powered/unpowered adequacy label and the +-0.03 / 0.07 magnitude
  thresholds; report a SENSITIVITY LADDER per cell and define bands by the CI's relation to the
  mirror instead.
  - DIRECTION: NEUTRAL (nothing is admitted or excluded either way; a boolean is replaced by the
    numbers behind it, and every effect is now bound to its own MDE and CI width on the same row)
  - Operator mandate 2026-07-28. The retired thresholds were anchored on sd(log R)=0.0729 and
    median log R=-0.0301 - the DISPERSION and LOCATION of the observed residual, neither of which
    is a statement about what effect size matters. Powering is left to later verification.

running count: 2 looser / 2 tighter / 2 neutral
NOTE per L-23: no one-directional streak. Neither loosening touches an integrity check, fence,
causality rule or claim boundary - both act only on population size. Both tightenings close real
specification gaps.
```

Checkpoint/family amendments in force: **U1** (top-25 universe, NEUTRAL), **S1** (per-symbol
sufficiency, NEUTRAL), **C1** (cTrader replication-only, NEUTRAL), **C2** (claim refusals, TIGHTER),
**C5** (gross-only measurement, NARROWING), **C6** (layer protocol, TIGHTER).

---

## §15 Artifacts

| Path | Content |
|---|---|
| `screen_code/` | entry module, layer module, 4 device modules, metrics layer, control module |
| `results/episodes.parquet` | every episode: signal ts, decision state, stop price, fill ts/price, exit ts/price/reason, `r` bps, layer tags |
| `results/signals.parquet` | every signal incl. **unfilled** and **suppressed**, with reason |
| `results/metrics_by_cell.parquet` | per cell: `p`,`W`,`L`,`W_L`,`p_be`,**`log R`**, block + iid MDE in log units, CIs, CI width, ladder detection rates, band label (CI-relative), evidence class, fill rate, `p_flat`, κ, `n`, homogeneity, cost overlay flagged `DISCLOSURE_ONLY` |
| `results/layer_deltas.parquet` | Δ`log R` per stage vs L0, with the L2 interaction term |
| `results/controls.json` | all four controls: percentiles, **null means and quantiles**, **plant curves** (P-24), derangement fixed-point counts |
| `results/selection_check.json` | the L-51 three-number check on every powered subset (P-22) |
| `results/unit_pin.json` | measured ATR20 and σ̂ medians (computed, not asserted) |
| `results/resolution_ladder.parquet` | per cell: realised n, block MDE, CI width, detection rate at each ladder rung, and the n required at each rung. **No adequacy flag** |
| `results/golden_traces.json` | G1–G6 |
| `results/integrity_selfcheck.json` | check-count reconciliation, fences, causality, pin, identity, `log R` definition, cost isolation, code sha256 |
| `screen.md` | neutral quantification (subordinate) |
| `analysis.md` | **fresh-context analyst — binding read** (SPDR stage 5, mandatory) |
