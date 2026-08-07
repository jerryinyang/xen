# SPDR-024 — Breakout baseline characterisation on estimands that can see the effect

- **Family / registration:** `CF-VOLDIR-001` — checkpoint-018 **item 7b / Step 3b**, operator amendment 2026-08-05
- **Checkpoint:** `2026-07-25-018-trade-opportunity-capture-geometry`
- **Status:** `DESIGN DRAFT — NOT QA-REVIEWED, NOT AUTHORISED`
- **Vehicle:** NautilusTrader `BacktestNode`; SPDR TRAIN-only characterisation (operator Nautilus override, precedent SPDR-021/022/023)
- **Binding specification:** `next-experiment-shape.md` (D1–D11, E1–E6, M1–M7, H1–H3) in the checkpoint directory — binding in full
- **Evidence base:** `confirmation-extraction-021-023.md` (11-item artifact-traced ledger)
- **Programme contract:** `adaptive-management-design.md` remains binding except where `next-experiment-shape.md` supersedes it

```text
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: reported cost understates total cost; reported net performance is overstated
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

---

## 0. Operator directives discharged by this design

The binding register is `next-experiment-shape.md` §0 (**OD-1 … OD-24**). That table is the
authority; this design elaborates it and may not contradict it. Map from directive to clause:

| Directive | Discharged in |
|---|---|
| OD-1 breakout is the model; OD-5 Nautilus, realistic fills, no vectorisation; OD-6 retain optimised code; OD-7 breadth | §4 Scope |
| OD-2 H1 and H4 independently | §4 Scope; §7 (cap rule applied per domain); §10 (H4 predeclared unpowered pending preflight) |
| OD-3 characterise the baseline alone first | §6 arm A |
| OD-4 no cost at all | disclosure block; §12 (break-even spread emitted instead of charging cost) |
| OD-8 keep and validate the admission filter; OD-13 the two blocked questions | §1; §5 E2; §6 arm D; §8 CONTROL COUNTERFACTUAL-REJECT |
| OD-9 pool-filter per-symbol and report-level; OD-10 symbol-specific analysis | §6E (fixed three-step ladder); §11 POOLED rule |
| OD-11 skip refuted devices; OD-15 SIZE only; OD-16 drop REVERSE | §4 Scope; §15 amendments 1–2 |
| OD-12 keep the near-null components | §4 Scope (all eight retained) |
| OD-14 continuous **and** discrete sizing | §6C |
| OD-17 remove time-derangement | §8 (removed as a within-sample layer; §9 future-destroy tripwire explicitly retained) |
| OD-18 regime labels per origin and per trade | §5 E1; §10.1 V-C |
| OD-19 measure sizing expectancy; unbiased critical analysis | §3 PRIMARY estimand; §5 E6; §10; §11 direction-vs-magnitude rule |
| OD-20 three variance treatments; OD-21 regime blocks must be episodal | §10.1 and its V-C RULES block |
| OD-23 all cells carry the magnitude question | §10 POWER |

**Scope note on OD-19 (carried verbatim from the register):** OD-19 names capture geometry among the
effects to measure; OD-11/OD-15 remove the capture-geometry *devices*. Resolution — the four devices
are not re-run as arms (refuted 6/6 cells); capture geometry is still **measured** as a property of
the baseline and the SIZE arms via exit composition (E4), realised hold distribution (E5), the decay
curve (H3) and the per-episode excursion diagnostics. This run cannot say whether a *differently
constructed* capture device would help — that is a new mechanism and a new experiment.

---

## 1. Question and mechanism

**One falsifiable question:** *On the fixed candlestick-breakout substrate, does any confirmed
volatility component change the capital-normalised outcome of an episode — and does it do so
conditional on the realised volatility regime?*

SPDR-021/022/023 could not put this question. Three structural reasons, each measured:

| Blocked question | Structural cause (measured) |
|---|---|
| Does the admission filter select *better* trades? | Rejected origins carry `outcome_bps = 0.0`, not a counterfactual — 14,323–695,139 rows per component, both universes |
| Is any effect regime-conditional? | Arms are *gated by* volatility state; outcomes are never *labelled* with it. No `vol_state` column exists in any of the six cells |
| Does sizing change expectancy? | Per-trade **bps** is per unit of notional; scaling the position cannot move it. Paired SIZE outcome delta is exactly `0.000000` on **1,400/1,400 rows in all six cells** |

```text
MECHANISM:
  The candlestick pattern supplies direction; it is fixed and is never tuned. Confirmed volatility
  objects supply only expected move scale (RANGE_SCALE, SWING_SCALE), slow state (LEVEL_NOW),
  forecast state at k bars (LEVEL_FORECAST_K4/K12), short shock state (SHOCK), next-swing
  opportunity (SWING_GT_CUR) and tail risk (TAIL_RISK). A volatility object can act on an episode
  through exactly two channels: (a) SELECTION — it changes which origins become orders, altering the
  composition of the traded set without altering any shared trade's price path; (b) SCALE — it
  changes the capital committed per episode, altering the capital-weighted return and the drawdown
  path without altering any per-notional price outcome. Channel (a) is measurable only against the
  counterfactual outcome of the origins it rejects. Channel (b) is measurable only on a
  capital-normalised estimand. No volatility object is treated as a direction forecast.
  Falsifiable: if neither channel moves the capital-normalised episode return beyond its own
  dependence-matched noise floor, on an emission that can resolve it, the volatility-management
  thesis is refuted at power on this substrate rather than unresolved.

DERIVED:
  estimand = capital-normalised episode return (xen.adjudication episode object), gross, paired
             adaptive-minus-fixed on common-closed episodes; per-origin occupancy-inclusive form
             for the selection channel
  null     = the same origins under the fixed arm (selection channel: the SAME origins' emitted
             counterfactual outcomes); the same filled episodes under the fixed device (scale
             channel); magnitude-matched comparator for magnitude-defined conditioners
  horizon  = native 1-minute execution inside the signal domain's own bar; H1 and H4 domains run
             as SEPARATE cells, never pooled — the forecast components K4/K12 are only horizon-
             matched to a hold of 4 / 12 domain bars, which H1 alone cannot supply
  test     = direct estimate with uncertainty computed THREE ways and all three reported
             (unchunked / fixed-time-block / regime-episode-block, §10.1); MDE stated in
             sigma-hat units per cell; per-stratum descriptive map, no binary verdict
```

**Why this is not the SPDR-021 stack re-pointed (L-13).** The estimand changed from per-notional
bps to capital-normalised episode return *because the mechanism's scale channel is invisible in
bps* — a change forced by the mechanism, not imported. The null for the selection channel is the
rejected origins' counterfactual, an object SPDR-021 did not emit. Neither would transfer to a
direction-forecast mechanism.

---

## 2. Object identity declarations

```text
OBJECT-IDENTITY:
  measurement object == trading object: YES — the estimand is the xen.adjudication EPISODE
    (entry fill -> final close, all legs), which is exactly the object the strategy commits capital
    to. Per-leg reads are diagnostic only (L-16/L-18). Capital normalisation is applied at the
    episode, not the leg.
  measured conditioning event == traded entry event: YES — the completed-bar pattern plus the
    declared threshold creates a STOP order; capital is committed at the stop fill, and every
    availability/selection measure conditions on that same stop-fill state. All feature state is
    frozen at <= t-1 of the signal domain bar.
  effect-splitting windows non-overlapping: YES — one live order or position per instrument per
    domain; the SELECTION channel is measured per-origin (occupancy-inclusive) and the SCALE
    channel per common-closed episode. These are reported as two lenses and are NEVER summed,
    differenced, or merged into one effect (F2 of the evidence base).
  H1 and H4 domains: SEPARATE cells. A position opened in one domain is never measured in the other.
```

---

## 3. Primary estimand (resolves M3)

**Single pre-declared primary estimand:**

```text
PRIMARY: capital_normalised_episode_return
  object   : xen.adjudication episode
  numerator: gross episode P&L (fees/funding only; NO spread — see disclosure)
  denominator: a FIXED UNIT-CAPITAL REFERENCE BASE (see AMENDMENT-4, unsigned).
               The original text read "capital committed to that episode at entry (risk_size x
               notional at fill)". That quantity divides the size change straight back out and
               is identically the per-notional bps estimand, which is blind to sizing by
               construction; §14 trace 1 requires a non-zero delta and therefore settles the
               reading. The implemented form is outcome_bps x risk_size.
  returns  : open-to-open; real prices only
  paired   : adaptive arm minus fixed arm, on COMMON-CLOSED episodes only
  aggregation: un-nest -> sigma-hat-normalise -> pool, with a SYMBOL-CLUSTERED interval (M1)
```

**What this estimand cannot do, stated where it is defined.** The paired difference for a SIZE
arm is exactly `(risk_size - 1) x baseline_outcome`, so its mean decomposes into an EXPOSURE
term `(E[size] - 1) x E[outcome]` and a SELECTIVITY term `Cov(size, outcome)`. The exposure term
is arithmetic: on a positive-mean population any size reduction must lower the measure, and on a
negative-mean population must raise it, whatever the component is doing. **A component-level
claim therefore rests on the SELECTIVITY term and on the gate-permutation control (§8), never on
the raw paired difference**, which would otherwise report the same component as helpful wherever
the baseline loses money and harmful wherever it earns.

**Everything else is a diagnostic**, explicitly including:

| Diagnostic | Retained for | Barred from |
|---|---|---|
| `outcome_bps` (per-notional, per-trade) | price-path effects: selection composition, exit geometry | **Any sizing/scale claim, in either direction** — blind by construction (§1) |
| `drawdown_bps`, `risk_dispersion`, `tail_loss_bps`, `concentration` | risk-shape reads | Expectancy claims |
| device-native metrics | device behaviour attestation | Cross-device comparison on one universal score |

**Binding report rule.** A per-notional bps figure may never be cited to support **or** refute a
sizing-expectancy claim. Citing the structural zeros in either direction is a measurement error,
not a finding. (Checkpoint-018 §7, as narrowed 2026-08-05.)

---

## 4. Scope

| Item | Decision |
|---|---|
| Substrate | SPDR-021 fixed candlestick breakout, unchanged. Direction logic frozen; never tuned (checkpoint-018 §7 refusal) |
| Signal domains | **H1 and H4, run independently as separate cells, never pooled** (D2) |
| Universes | crypto (Bybit top-25, pin `cf-voldir-001-universe.json`) and cTrader (EURUSD/XAUUSD/USTEC, INFR-021 fence) — **separate, never pooled** |
| Cells | 2 domains × 2 universes = **4 cells** |
| Band | **TRAIN only.** TEST and the global 30% holdout are never loaded |
| Cost | **None charged** (D9). Gross throughout |
| Components | All **eight** retained: `RANGE_SCALE`, `SWING_SCALE`, `LEVEL_NOW`, `LEVEL_FORECAST_K4`, `LEVEL_FORECAST_K12`, `SHOCK`, `SWING_GT_CUR`, `TAIL_RISK`. No new components (O1 closed) |
| Devices | **SIZE only** (continuous `SCALE_NORMALISED` + discrete `STATE_HALVE_HIGH`, head to head — D7). The four Step-3-refuted devices (hold length, stop distance, trail width, recovery-after-stop) are **excluded** |
| Orientation | `REVERSE` arms **dropped** (M5) — DIRECT/REVERSE medians overlap completely; halving the grid funds the breadth |
| Vehicle | NautilusTrader `BacktestNode`, realistic fills, **no vectorisation** (D10) |
| Complexity budget | Comparative across universes/domains: 2–4 statistical constructions, 3–5 visualisations, 1–2 new code modules |
| Performance | Retain the SPDR-021/022/023 optimised implementations (D11; L-54/L-55) — exact-parity required before any further optimisation |

**Refusals honoured:** no direction research; no entry-parameter tuning; no expectancy claim from a
blind estimand; no pooled headline without homogeneity; no family action; no verdict.

---

## 5. Emission requirements (E1–E6) — the design's actual deliverable

Without these the arms below are unreadable no matter how well powered.

| # | Requirement | Blocks which read |
|---|---|---|
| **E1** | Realised regime label per **origin** and per **episode**, assigned causally at `<= t-1` | Regime conditioning (§8) |
| **E2** | **Counterfactual outcome for rejected origins** — what the episode would have returned had the origin been admitted, on the fixed arm's own management | Selection channel; pool-filter reads |
| **E3** | A TARGET metric not monotone in target distance | TARGET falsifiability (carried for completeness; TARGET is not an arm here) |
| **E4** | `exit_reason` plumbed into the analysis artifacts (internal `_exit_reason` is already populated). **Also `entry_ts`, which is null on 72,477/72,477 rows while `_entry_ns` is fully populated** — the same plumbing break | Exit composition; any time-ordered read (including the V-C regime blocks) |
| **E5** | Realised hold duration per position in signal-domain bars + the cap-bind flag | H1–H3, M4 |
| **E6** | **Capital-normalised outcome alongside per-notional bps** | The PRIMARY estimand itself |

Also: carry the cost-scope block **into** the analysis artifacts (currently null on 903–19,961 rows
per cell); populate or remove `payoff_scale_ratio` (NaN on all 9,100 rows).

---

## 6. Arms

Run in this order; the two grids are **not** crossed.

**A. Baseline characterisation (D3 — first-class, not a preamble).**
Fixed breakout, unit size, no adaptive component. Reports its own level: exposure per origin, fill
rate, gross mean, `win_share` against `breakeven_win_share_net`, exit composition, and the realised
hold distribution. Run in **both** domains — H4 has never been run.

**B. Uncapped-hold arm (H1 of the hold procedure).**
Exit by strategy logic only, plus the safety ceiling in §7. Produces the first non-circular exit
distribution and the decay curve. **Its decay curve sets no cap in this run** (H3).

**C. SIZE arms — the magnitude question.**
Each component × {continuous `SCALE_NORMALISED`, discrete `STATE_HALVE_HIGH`} against
`FIXED_SIZE_UNIT`, on the PRIMARY estimand plus the risk-shape diagnostics.

**D. Selection arms.**
Each component's admission rule, read on the origin lens against the rejected origins'
**counterfactual** outcomes (E2). Never read on the trade lens — the paired delta is exactly zero
by identity for admission rules (F2).

**E. Pool-filter reads — report-level, per-symbol, NOT arms.**
`drop-worst`, `drop-best`, and both, applied **per symbol** to the reporting, never to entry.
Fixed reporting ladder, all three always shown, none substituting for another:

```text
(i)   every cell reported individually
(ii)  pooled
(iii) pooled with each drop applied
```

This is a concentration diagnostic of the same shape as the SPDR-021 XAUUSD leave-one-out (which
flipped the pooled sign: −0.00851 → +0.01910). It is not a strategy branch and makes no claim.

---

## 7. Hold horizon (resolves O3 / O4)

**Why no cap can be read off the completed runs.** The native comparison population exits after
exactly one H1 bar on 100% of rows (`hold_bars = 1`, `_exit_reason = 'HOLD'`; median = p99 = max =
60.0 min). The spread that appears across all arms (p90 240 min, p95 720) **is the `B2`/`B4`/`B12`
caps already imposed** — setting a percentile on it calibrates against the previous arbitrary
choice. Circular; refused.

```text
SAFETY-CEILING (O4):
  value    : 120 signal-domain bars (5 days at H1; 20 days at H4)
  criterion: 10x the largest declared comparison cap (B12), so the ceiling CANNOT act as a
             de facto exit or shape the distribution it exists to reveal
  class    : OPERATIONAL SAFETY VALVE, not a design parameter, not an arm
  hard     : no position may span the TRAIN fence; positions open at the fence are reported
             CENSORED and excluded from paired reads (never silently closed)
  reported : bind rate per arm per cell; a bind rate > 2% invalidates the ceiling as "safe" and
             is flagged to the operator rather than reinterpreted

CAP-RULE (H2):
  grid     : {2, 4, 8, 12, 24, 48} signal-domain bars — declared here, before execution
  rule     : the smallest bar count on the grid that binds <= 5% of arm B's uncapped CLOSED
             positions, computed per (universe x domain), applied mechanically after arm B
  basis    : the DURATION distribution only. Never the outcome distribution — selecting a cap on
             outcomes is selection on the estimand and would void the run
  reported : the chosen value, the realised bind rate, and the full duration distribution
```

**Horizon pairing (binding read rule).** `LEVEL_FORECAST_K4`/`K12` forecast the volatility state 4
and 12 bars ahead; the baseline holds one bar, so the forecast describes a state the episode never
reaches. Their Step-3 near-null (bottom two of six components in 5 of 6 cells) is a **horizon
mismatch, not evidence that volatility is unforecastable.** Therefore: the forecast components are
read **per domain, never pooled across H1 and H4**, and hold horizon and forecast horizon are
treated as one paired parameter. If `K4` resolves at a 4-bar hold and stays dark at a 1-bar hold,
horizon-matching is confirmed — a structural result, reported as such.

---

## 8. Controls (each with its validity proof)

```text
CONTROL FIXED-COMPARATOR:
  question answered: does the adaptive arm differ from its own unconditioned form?
  population: the same origins/episodes under the fixed arm. DISJOINT: not a disjoint pool by
    design — this is a PAIRED comparator, not an attribution control; its validity rests on common
    -closed pairing, and it is declared here so it is never mistaken for an attribution null.
  bite/MDE: per-cell MDE table, §10
  non-vacuity: moves the mean of the paired difference directly
  expected if H true: non-zero paired difference on the PRIMARY estimand
  expected if H false: paired difference within its dependence-matched noise floor
  disclosure: effect and CI reported per stratum
  class: report layer

CONTROL COUNTERFACTUAL-REJECT (new; the selection channel's null):
  question answered: are admitted origins better than the ones the rule rejected?
  population: REJECTED origins with their emitted counterfactual outcomes (E2).
    DISJOINT from the signal population by construction — no origin is in both sets (B-1 satisfied:
    the rejected set can show a HIGHER mean than the admitted set, which is precisely the outcome
    that would refute the filter).
  bite/MDE: MDE curve over admitted:rejected split ratios, co-designed with the band, computed at
    preflight from arm A's realised rejection rate; NOT a fixed plant
  non-vacuity: moves the mean and the sign-share of the admitted-minus-rejected contrast — the
    exact statistics the selection claim rests on
  expected if H true: admitted mean > rejected mean, beyond the cell's MDE
  expected if H false: admitted ~ rejected (a powered null on selection quality — a first-class
    result, and the one SPDR-021 could not produce)
  disclosure: collapse fraction vs the raw admitted-only figure
  class: report layer

CONTROL MAGNITUDE-MATCH:
  question answered: is a magnitude-defined conditioner's effect attributable to magnitude alone?
  population: magnitude-matched non-signal origins, binned. DISJOINT: bins are drawn from origins
    the conditioner did not select at the same magnitude.
  bite/MDE: per-bin MDE reported with the comparator's OWN mean and null quantiles alongside every
    percentile (P-24 — a percentile without its comparator's mean and plant curve is uninterpretable)
  non-vacuity: moves the conditional mean within magnitude bin
  expected if H true: effect survives magnitude matching; if H false: effect collapses into the bin
  disclosure: collapse fraction + comparator mean + null quantiles + plant curve, always together
  class: report layer
  IMPLEMENTED AS (2026-08-06): regime-stratified matching, `_regime_matched_contrast` in
    `xen.adaptive_management.spdr024_analysis`. Every admission rule in this run IS a volatility
    gate, so the admitted and declined populations differ by realised regime BY CONSTRUCTION
    (TAIL_RISK cTrader H1: 3 HIGH / 213 LOW among declined origins). The contrast is recomputed
    inside each realised state and reported with the collapse fraction against the unmatched
    figure, each stratum's own comparator mean, its count and its MDE. The regime is the
    coarsest magnitude this emission carries; a continuous-magnitude binning would need a
    per-component magnitude column the emission does not have, and is recorded as a successor
    item rather than approximated here.

CONTROL GATE-PERMUTATION (added 2026-08-06; the SIZE channel's non-vacuity control):
  question answered: is the gate applied to WORSE trades, or merely applied?
  population: the arm's own paired episodes, with each symbol's risk_size vector permuted
    against its own outcomes. DISJOINT: not a disjoint pool — it is a within-arm permutation
    null, and it is declared as such so it is never mistaken for an attribution control.
  bite/MDE: the observed effect's percentile within its own permutation null, two-sided;
    the cell's own MDE still governs the magnitude read
  non-vacuity: it preserves the gate rate and the exact multiplier distribution — so the
    EXPOSURE term is identical under the null — while destroying the gate-to-outcome
    association, which is the SELECTIVITY term. It is NOT mean-preserving on the paired
    difference, so unlike TIME-DERANGEMENT it can move the statistic it exists to destroy.
  expected if H true: the observed effect sits in the tail of its own null
  expected if H false: the observed effect sits mid-distribution — the component gates, but not
    selectively, and the measured difference is exposure arithmetic
  disclosure: observed, null mean, component-specific difference, percentile and two-sided p
  class: report layer

CONTROL TIME-DERANGEMENT: REMOVED (D8).
  Basis: identical to its paired real estimate on 100% of rows in all six Step-3 cells
  (max |delta| 1.1e-16). A mean over origins is invariant to permuting time labels, so it cannot
  destroy the quantity it exists to destroy (B-6 vacuity). It is not a control that passed; it is a
  control that was not there. Operator decision: this class of robustness test belongs later, at
  strategy level, under XENA's future-destroy controls.
  NOTE FOR QA: this removes a WITHIN-SAMPLE-ATTRIBUTION report layer. It does NOT remove the
  future-destroy tripwire, which is retained and HARD (§9).
```

---

## 9. Leak tripwire (HARD)

```text
TRIPWIRE FUTURE-SHIFT:
  form: shift every volatility component's availability FORWARD by +1 signal-domain bar, so each
        arm conditions on information it could not have had; re-run the full arm set.
  must collapse the edge; expected collapse fraction ~ 1.0 (the shifted arm must not outperform
        its causal twin beyond noise). A SURVIVING edge under the shift is an acausal leak -> REJECT.
  vacuity check: the shift changes WHICH origins each arm admits and WHAT capital it commits —
        both sufficient statistics of the primary estimand. Unlike a label permutation, it is not
        mean-preserving.
  if permutation-based: N/A — this is a causal shift, not a permutation. No fixed-point concern.
  class: future_destroy — HARD VALIDITY. Failure means the emission is invalid (fix the data),
         never "no edge".
```

Additional HARD checks: TRAIN/holdout fence attestation; `<= t-1` causal provenance; Nautilus
order/fill reconciliation; deterministic rerun whenever `--jobs > 1`, **unconditional on
`--resume`** (L-52); **the expected NUMBER of HARD checks is itself asserted and reconciled against
this list by name** (P-23 — four checks silently did not run in one prior build); every check
depends on an **emitted artifact**, so missing or empty fails rather than vacuously passing.

---

## 10. Power (resolves M2)

**The true sample is small, and it is nearly independent.** Both facts are measured, not assumed.

*Sample size.* `native_parameter_shared_trades.parquet` carries one row **per arm per trade** — each
fixed baseline trade appears a median of 40 times (max 64) across 64 arms. Deduplicating on
`(symbol, fixed_entry_ns)`:

| Cell | rows in table | **distinct baseline trades** | per symbol (min / median / max) |
|---|---|---|---|
| cTrader H1 | 72,477 | **1,698** | 502 / 570 / 626 |
| crypto H1 | 346,894 | **8,469** | 25 / 420 / 850 |

*Dependence — tested, not assumed* (per-trade `fixed_outcome_bps`, ordered by entry time, per symbol):

| Cell | autocorrelation, lags 1–20 (median) | max abs | 95% noise band | variance ratio, b = 2…25 |
|---|---|---|---|---|
| cTrader | −0.029 … +0.036 | 0.071 | ±0.082 | 0.83 – 1.14 |
| crypto | −0.005 … +0.038 | 0.153 | ±0.093 | 0.95 – 1.05 |

**There is no detectable serial dependence in this strategy's trade series.** Every autocorrelation
sits inside its own noise band, and the variance-ratio diagnostic (iid ⇒ 1.0) stays within ±17% of
1.0 at every block length tested. The mechanism is transparent: the strategy holds **one** bar and
fires sporadically, so consecutive trades are typically days apart — none of the usual sources of
block dependence (overlapping holding windows, persistent within-position exposure) is present.

**Consequence:** the fixed 24-bar block used in Step-3 was inherited, not derived, and it costs
resolution for a dependence that is not there — the emitted effective-block counts (cTrader 405 from
570 trades; crypto 287 from 420) impose a ~0.7× discount the data does not justify. The standing
requirement to derive such thresholds from measured autocorrelation rather than assert them
(design-requirements §13 F06) was not honoured for block length in Step-3. It is honoured here.

**Two dependence axes remain untested and are NOT covered by the above:** (i) the **paired
difference** between arms may have a different dependence structure than the baseline series;
(ii) **cross-symbol contemporaneous** correlation (crypto symbols co-moving) is not a time-series
dependence at all and is never addressed by time blocking — it is the reason the interval stays
**symbol-clustered** (M1) regardless of which treatment below is used.

### 10.1 Three variance treatments, all reported (operator decision 2026-08-06)

The uncertainty on every headline estimate is computed **three ways** and all three are always
printed side by side. This is an analysis-side choice on one emission — it costs no extra engine
run, and each treatment is independently informative.

| # | Treatment | What it assumes | What it is informative about |
|---|---|---|---|
| **V-A** | **Unchunked** — trade count as the sample size | trades independent | The measurement above says this is *supported* for this strategy. The efficient read if it holds |
| **V-B** | **Fixed-length time blocks** — the Step-3 form, block ≥ H | dependence is a function of clock time | Comparability with SPDR-021/022/023; the conservative bound |
| **V-C** | **Regime-episode blocks** — block boundaries at volatility-regime transitions | dependence lives in **regime persistence**, not the clock | The mechanism-native form: if trades cluster in dependence at all, the volatility state is where this family expects it |

**Reading rule, pre-declared:** agreement across V-A/V-B/V-C is **convergent evidence** and is
reported as such. Divergence is a **diagnostic about where dependence lives**, not a menu — the
**most conservative** of the three governs every band label in §11, and the divergence itself is
reported as a finding. No treatment may be selected after seeing which one favours a result.

**V-C validity constraints (binding).** Regime blocks are legitimate only because a regime episode
is *contiguous in time* — block resampling still preserves within-block dependence and resamples
across independent stretches. They are also **data-derived**, so:

```text
V-C RULES:
  regime label   : from volatility only, causal at <= t-1 (E1). NEVER from outcomes — an
                   outcome-derived block definition is selection on the estimand and voids the read
  block          : one contiguous regime EPISODE (entry into a state -> exit from it)
  minimum length : episodes shorter than 4 signal-domain bars merge into the preceding episode;
                   declared here, before execution, and applied mechanically
  reported       : episode count, episode-length distribution, and the realised block count per
                   cell — so the reader can see whether V-C had more or less resolution than V-B
  pre-declared   : this rule is frozen at design time; it is not tuned after seeing the estimates
```

**MDE / detection-floor apparatus (AMENDMENT-7 — R1–R5).** Power remains **context only**. No
result or power label classifies a row (`CLEARS_FLOOR`, `WASH`, `UNPOWERED`, `FULLY_RESOLVING`,
`NOT_RESOLVABLE_*`, `CARRIES_MAGNITUDE_*`, or synonyms). MDE units stay sigma-hat for scale when
sigma-hat is the estimate's unit (L-50 / P-21); selection uses its own declared units (R4).

```text
# --- R1: SIZE mechanism ceiling (baseline-only; per cell) ---
SIZE_MECHANISM_CEILING:
  sharpe_per_trade := |gross_mean_bps| / gross_sigma_bps
                      # from FIXED baseline fills only (no adaptive arm)
  ceiling_sigma(p) := sqrt(p) * sharpe_per_trade
  # p = design gate rate for planning (e.g. STATE_HALVE_HIGH on HIGH ≈ 0.5);
  #     report realised gate rates beside estimates post-run
  # soft ceiling: selectivity / continuous size > 1 may exceed; still the planning scale
  FORBIDDEN as yardstick: STEP3 0.022 / 0.150 (historical context only, never a gate)

# --- R2: row floor shares the CI's SE family ---
ROW_FLOOR (if mde_* columns remain):
  SE := SE of the same estimator as the CI on that row
       (bootstrap SE of the clustered interval draws preferred;
        (ci_high - ci_low) / (2 * z_0.975) only if documented as interval-implied SE
        and used consistently for that row)
  mde := MDE_Z * SE
  FORBIDDEN: mde := MDE_Z / sqrt(effective_blocks) as the row floor
             when the row's CI is bootstrap / clustered

# --- R3: MDE_Z is planning only ---
MDE_Z := 2.8
  USE: sample-size planning for future designs / preflight descriptive capacity
  DO NOT USE: pass mark on realised |estimate| (no |est| ≥ MDE resolve language)

# --- R5: preflight M2 (fills + same endpoint as post-run context) ---
PREFLIGHT M2:
  n_basis := FILLS (preferred) or orders * measured_fill_rate with
             count_basis labelled PROVISIONAL_FILL_RATE_ADJUSTED
             or PROVISIONAL_DOMAIN_BAR_SIMULATED_FILLS (baseline-only micro-pass
             stop-touch + one-domain-bar hold; reconcile to engine fills post-run)
  endpoint := mechanism ceiling / descriptive rule from R1 (same as post-run context)
  planning_floor (preflight only, no bootstrap yet):
             MDE_Z / sqrt(n_basis) under each variance treatment's block count;
             most conservative reported as context
  descriptive label (frozen vocabulary; not a result band):
    DESCRIPTIVE_SIZE_MAGNITUDE_FLOOR_ABOVE_CEILING
        when planning_floor > ceiling_sigma(p)
    CONTEXT_FLOOR_AT_OR_BELOW_MECHANISM_CEILING
        when planning_floor <= ceiling_sigma(p)
    INSUFFICIENT_FILLS_FOR_PREFLIGHT
        when n_basis < 30
  FORBIDDEN: gate on STEP3 0.022 or 0.150
  FORBIDDEN: CARRIES_MAGNITUDE on pure order counts while noting optimism
  Cells marked DESCRIPTIVE for SIZE magnitude still RUN (breadth); they do not
  support magnitude claims. Blind breadth is rejected by the descriptive label,
  not by skipping the engine.
```

**Historical design-time counts (still true for sample size; floors above are superseded):**
per-symbol cTrader n~570 / crypto n~420; pooled cTrader n~1,698 / crypto n~8,469 under
order-level baselines. H4 remains thinner (~1/4 of H1 origins) pending measured preflight.
Step-3's 0.022–0.150 σ̂ range is **historical context only** — never a resolve or preflight bar.

**M2 before execution:** compute fill-based (or provisional fill-rate-adjusted) planning floors
under all three variance treatments (§10.1), take the most conservative, compare to the R1
mechanism ceiling, and emit the frozen descriptive label. No cell is "passed" for magnitude on
order counts alone.

---

## 11. Reporting rule (no result labels — superseded 2026-08-07, AMENDMENT-6)

**This section previously declared `SUPPORTED` / `WASH` / `CONTRADICTED` / `UNPOWERED` bands. They
are withdrawn.** The binding contract does not permit them, and no operator directive superseded
the clauses that forbid them:

- `adaptive-management-design.md` §1: *"Event count, uncertainty and MDE are reported as context;
  **power labels do not decide which rows are shown or how they are described**."*
- `adaptive-management-design.md` §9: *"Emit event count, effective count, CI and MDE for every
  row. These are informative diagnostics, **not verdict labels or pruning rules**."*
- The SPDR-021/022/023 execution standard: *"**Power is context only**"*; report MDE *"without
  making power a gate"*; *"no verdict, winner, **pass/fail-value** or top-N field exists."*

```text
REPORTING (every row, both channels, every stratum) — AMENDMENT-6 + AMENDMENT-7:
  estimate            in the channel's declared units (see CHANNELS)
  uncertainty         ci_low / ci_high under ALL THREE variance treatments (§10.1);
                      governing = most conservative by fewest blocks / highest coherent
                      floor under R2
  population count    eligible_origin_n, entry_fill_n, close_n, common_fill_n,
                      common_close_n — NULL where one does not apply, NEVER filled in
                      from a different population
  effective count     effective_origin_blocks for an origin-lens read,
                      effective_trade_blocks for a paired trade-lens read; the other is NULL
  optional context    mde from R2 (same SE family as that row's CI), est/SE, exposure /
                      selectivity terms, control fields

  and NOTHING else that classifies the row. No band, no class, no verdict, no pass field,
  no ranking, no top-N.

NEVER emit or narrate as resolve/unresolve:
  band, resolution_class, WASH, UNPOWERED, NOT_RESOLVABLE_*, DIRECTION_RESOLVED_*,
  SUPPORTED, CONTRADICTED, CLEARS_FLOOR, FULLY_RESOLVING, CARRIES_MAGNITUDE_*,
  or prose that means the same (including |est| ≥ MDE as a resolve rule)

CHANNELS (R4 — denominators declared; no silent dual-σ̂ ladder):
  SCALE: estimate is sigma-hat of the paired difference
         (values / sd(paired Δ)); sigma_denominator = "paired_delta"
         optional mde_sigma = MDE_Z × bootstrap_SE of that same paired estimator
  SELECTION: contrasts are in bps (raw) with their own interval in bps;
             sigma_denominator = "outcome_level_bps" when a sigma-hat form is also shown
             (sd of pooled outcome levels, NOT sd of paired Δ). Do not claim the same
             numeric 0.022–0.150 ladder as scale. Optional mde_bps = MDE_Z × bootstrap_SE
             of the contrast in bps.
  If both channels report a sigma-hat number, each row names its denominator object in a
  column — never one silent shared ladder.

READING:
  the reader compares the estimate with its own interval (and optional est/SE). Tallies are
  counts of intervals excluding zero on each side, beside median estimate and optional
  median floor — never counts of labels. Power / MDE is context only; it does not demote
  a row. Step-3's 0.022–0.150 range may appear only as historical family context, never as
  a resolve bar (B-5: thin cells are not negatives).

POOLED: disclosure-only unless symbol homogeneity is shown; the per-symbol ladder (§6E) is always
  printed alongside it.

STRUCTURAL ZEROS: reported as the measured `exact_zero_delta_share`, not as a label. A share of
  1.0 on the per-notional lens is the metric's blindness to size; a share of 1.0 on the PRIMARY
  lens is an arm that never gated in that stratum. The lens, the gate rate and the counts are all
  on the row, so the reader distinguishes them without the emission asserting which it is.
```

## 12. Conversion pin (L-21 — this design cites SPDR evidence)

```text
CONVERSION-PIN:
  divisor object: ATR(20) on the signal-domain bar, lagged [t-1]
                  (SPDR-021 fixed comparator threshold = 0.50 x ATR(20);
                   python/experiments/SPDR-021/design.md:52)
  measured value: TO BE COMPUTED AT PREFLIGHT from TRAIN data per instrument and per domain, in
                  bps. NEVER recalled or asserted. QA traces this as a clause.
  resulting effect: screen effect x measured value, computed at preflight, not here
  cost floor:     NOT APPLICABLE AS A GATE — no cost is charged (D9). Every effect instead emits
                  breakeven_spread_rt_bps = |effect| / round-trips, at THAT ARM's own turnover
                  (cost does not cancel in a paired difference when arms differ in trade count),
                  labelled NON-EMITTED SCENARIO (M7).
  framing:        this experiment is APPARATUS AND CHARACTERISATION, never tradability.
```

---

## 13. Integrity vs informative split

```text
HARD (block; failure = emission invalid, fix the data):
  future-shift tripwire collapse; TRAIN/holdout fence; causal <= t-1 provenance; Nautilus
  order/fill reconciliation; estimand reconciliation (xen.estimand_validation blocking_pass);
  deterministic rerun; asserted HARD-check COUNT reconciled by name against §9.

INFORMATIVE (operator judges; no auto-verdict anywhere):
  every effect size, CI, MDE, band label, collapse fraction, regime contrast, magnitude-matched
  comparison, selection-quality read, concentration ladder, and breakeven-spread scenario.
```

---

## 14. Golden traces (for QA — hand-derived from this design)

Synthetic UTC fixtures. The developer must not generate these.

1. **Capital normalisation makes sizing visible.** `2023-01-01T02:00Z` H1 origin, long stop fills at
   `100`, closes at `101` = `+100 bps` per notional. Arm `FIXED_SIZE_UNIT` commits 1 unit; arm
   `STATE_HALVE_HIGH` in state `HIGH` commits 0.5 unit. **Expected:** `outcome_bps` delta = exactly
   `0.0` (the Step-3 structural zero, reproduced as an attestation); PRIMARY
   `capital_normalised_episode_return` delta = **non-zero**, with the halved arm committing half the
   capital for the same per-notional move. If the PRIMARY delta is also zero, E6 is not implemented.
2. **Rejected-origin counterfactual.** `2023-01-02T02:00Z`, `ATR20 = 2`: the fixed arm admits the
   origin; component arm `TAIL_RISK` rejects it. The minute path after the would-be stop level
   reaches `+40 bps` then closes `+25 bps`. **Expected:** the rejected origin emits
   `counterfactual_outcome = +25 bps` under the fixed arm's own management — **not** `0.0`. A `0.0`
   here means E2 is not implemented and every selection read is void.
3. **Safety ceiling and censoring.** A position opened 119 domain bars before the TRAIN fence, still
   open at bar 120. **Expected:** closed by the safety ceiling at bar 120, `exit_reason =
   SAFETY_CEILING`, bind flag set. A position opened 3 bars before the fence and still open at the
   fence: **expected** `state = CENSORED`, excluded from paired reads, **never** silently closed at
   the fence price.

---

## 15. Amendment ledger

```text
AMENDMENT-0: initial design — DIRECTION: N/A (baseline registration)
  running count: 0 looser / 0 tighter / 0 neutral

AMENDMENT-1 (2026-08-06, operator): drop REVERSE orientation arms — DIRECTION: NEUTRAL
  Basis: DIRECT/REVERSE result distributions overlap almost entirely (cTrader E_TOUCH BAND_Z:
  DIRECT -0.134..+0.038 vs REVERSE -0.116..+0.030). Halves the grid at no information cost.
  Not LOOSER: removes arms, does not relax any threshold or admission rule.
  running count: 0 looser / 0 tighter / 1 neutral

AMENDMENT-2 (2026-08-06, operator): devices restricted to SIZE — DIRECTION: TIGHTER
  Basis: hold length, stop distance, trail width and recovery-after-stop refuted 6/6 cells in
  Step-3. Narrows scope; concentrates budget on the one live question.
  running count: 0 looser / 1 tighter / 1 neutral

AMENDMENT-3 (2026-08-06, operator): three variance treatments V-A/V-B/V-C, most conservative
  governs — DIRECTION: TIGHTER
  Basis: the Step-3 fixed 24-bar block was inherited, not derived; the dependence it assumes is
  not detectable in the data (§10). Reporting all three with the conservative one binding is
  strictly stricter than picking one.
  running count: 0 looser / 2 tighter / 1 neutral

AMENDMENT-4 (2026-08-06, DRAFTED BY THE IMPLEMENTER — **UNSIGNED, AWAITING OPERATOR**):
  the PRIMARY estimand's denominator is a FIXED UNIT-CAPITAL REFERENCE BASE — DIRECTION: NEUTRAL
  Basis: §3 writes the denominator as "capital committed to that episode at entry (risk_size x
  notional at fill)". Taken literally that denominator scales with risk_size exactly as the
  numerator does, the two cancel, and the estimand collapses to per-notional bps — reproducing
  the structural zero (1,400/1,400 rows, six cells) that this experiment exists to escape.
  §14 golden trace 1 settles the intended reading: it requires the halved arm to show a
  NON-ZERO primary delta for the same per-notional move, and states "if the PRIMARY delta is
  also zero, E6 is not implemented". Implemented as
  capital_normalised_return_bps = outcome_bps x risk_size, i.e. the episode's contribution
  measured against a fixed unit-capital base.
  Not LOOSER: no threshold, admission rule or band is relaxed; it changes which quantity is
  measured, in the only direction that makes OD-19 answerable at all.
  WHAT THE OPERATOR IS RATIFYING, stated plainly: under this estimand, reducing exposure can
  only improve the measure where gross expectancy is negative, and can only worsen it where
  gross expectancy is positive. That arithmetic is why §10.1 of this ledger's companion
  analysis reports the EXPOSURE and SELECTIVITY terms separately, and why a component-level
  claim rests on the gate-permutation control rather than on the raw paired difference.
  running count: 0 looser / 2 tighter / 2 neutral

AMENDMENT-5 (2026-08-07, POST-REVIEW CORRECTION — **UNSIGNED, AWAITING OPERATOR**):
  §11 gains an explicit RESOLUTION LADDER, and admission is read at the FILL —
  DIRECTION: TIGHTER
  Basis: a review of the first build's artifacts found three defects that all pushed the same
  way, toward reading unresolvable cells as measured nulls.
   (a) The band rule compared each cell's floor to the TOP of the family's observed effect
       range (0.150 sigma-hat) alone. cTrader H1's governing floor is 0.084 sigma-hat, so it is
       blind to more than half the range, yet every sub-floor result in it was banded `WASH`.
   (b) The SELECTION channel had no power guard of any kind — only a 30-row minimum. All 64
       selection contrasts across the four cells sat 3-20x BELOW their own detection floor
       (crypto H4: contrasts 1.2-23.0 bps against floors of 35.9-51.8 bps) and all 64 were
       banded `WASH`, i.e. reported as measured nulls.
   (c) `admitted` was read at ORDER CREATION, not at the stop fill that §2 OBJECT-IDENTITY
       binds it to. The eight `PENDING_EXPIRY` arms act on a pending order's lifetime, so they
       create exactly the comparator's order set and were banded
       `NOT_APPLICABLE_NO_REJECTION_SEMANTICS` — "empty by construction". Measured, they are
       not empty: `TAIL_RISK PENDING_EXPIRY` fills 1,808 against the comparator's 1,695
       (+6.7%), and on the fill event all eight carry 35-68 declined origins with real
       counterfactuals.
  Also in this amendment, each narrowing what may be called a result rather than widening it:
  the selection channel's floor now comes from the same governing treatment as its interval
  (it took the interval from the block bootstrap and the floor from unblocked row counts); the
  gate-permutation band is computed through the §11 rule on the control's own null envelope
  instead of a fixed `p >= 0.05` cut; the future-shift tripwire now records whether any arm had
  a causal edge to collapse at all, and its pass requires every arm that HAD one to collapse
  into the cell's own noise floor (design §9's "expected collapse fraction ~ 1.0"), rather than
  only that no shifted edge exceeded its twin.
  Not LOOSER: every change removes a label that asserted more than the data supports. No
  threshold is relaxed, no admission rule widened, no arm added.
  running count: 0 looser / 3 tighter / 2 neutral
  L-23 CHECK: the last three amendments are TIGHTER, NEUTRAL, TIGHTER — no one-directional
  streak of 3, so no operator flag is raised by the ledger itself. The amendment is
  nevertheless UNSIGNED, because it changes what the run may call a null.
  SUPERSEDED IN PART by AMENDMENT-6: the band taxonomy this amendment introduced
  (NOT_RESOLVABLE_AT_THIS_FLOOR, MAGNITUDE_RESOLVED_DIRECTION_UNRESOLVED,
  INERT_ARM_NO_GATE_FIRED_IN_STRATUM, the resolution ladder) is withdrawn with the rest of §11.
  Its three FINDINGS stand and are retained: the admission-at-fill correction, the selection
  channel's missing floor comparison, and the tripwire collapse criterion.

AMENDMENT-6 (2026-08-07, POST-REVIEW CORRECTION — **UNSIGNED, AWAITING OPERATOR**):
  §11 withdraws ALL result labels; every row is estimate + uncertainty + population count +
  effective count + MDE — DIRECTION: TIGHTER
  Basis: §11 declared SUPPORTED/WASH/CONTRADICTED bands, and AMENDMENT-5 extended rather than
  removed them. Both are non-compliant with clauses that no operator directive superseded:
    `adaptive-management-design.md` §1 — "power labels do not decide which rows are shown or how
      they are described";
    `adaptive-management-design.md` §9 — "Emit event count, effective count, CI and MDE for every
      row. These are informative diagnostics, not verdict labels or pruning rules";
    the SPDR-021/022/023 execution standard — "Power is context only", report MDE "without making
      power a gate", "no verdict, winner, pass/fail-value or top-N field exists".
  The precedent bears this out: SPDR-021/022/023 `analysis.md` contain zero occurrences of
  UNPOWERED, WASH, CONTRADICTED or NOT_RESOLVABLE; SUPPORTED and REFUTED appear once each, inside
  SPDR-021's boundary statement declining to use them.
  `UNPOWERED` was the sharpest violation: it describes a row BY ITS POWER, which is the precise
  thing §1 forbids, and AMENDMENT-5 made it worse by computing the class from the floor BEFORE
  the estimate was read.
  Also in this amendment: the seven separately-named populations (`eligible_origin_n`,
  `entry_fill_n`, `close_n`, `common_fill_n`, `common_close_n`, `effective_origin_blocks`,
  `effective_trade_blocks`) are emitted on every row, null where one does not apply and never
  filled in from another population — the population-conflation defect that invalidated the
  SPDR-021/022/023 first pass (handoff defects 4 and 5).
  Not LOOSER: it removes every assertion the emission was making beyond the measurement. No
  threshold is relaxed, no admission rule widened, no arm added, no row pruned.
  running count: 0 looser / 4 tighter / 2 neutral
  L-23 CHECK: the last three amendments are NEUTRAL, TIGHTER, TIGHTER — no one-directional
  streak of 3. UNSIGNED, because it changes the emitted schema and the reporting contract.

AMENDMENT-7 (2026-08-07, **SIGNED by operator decision §13** in
  docs/experiments-docs/checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/
  mde-floor-defect-spdr024.md — independent validation §12; operator decision 2026-08-07):
  detection-floor / MDE apparatus R1–R5 in one coherent package — DIRECTION: TIGHTER
  on honesty of power and preflight; NEUTRAL on strategy admission, arm grid, cost, TRAIN fence.
  Basis (defect doc §2–§6; all five defects graded PROVEN in §12.2):
    D1 floor often above SIZE mechanism ceiling (σ̂ ≈ √gate × baseline Sharpe);
    D2 Step-3 unresolved 0.022–0.150 used as yardstick;
    D3.1 MDE_Z=2.8 used as pass mark on realised |est|;
    D3.2 row floor = 2.8/√blocks ignoring bootstrap SE;
    D4 scale vs selection silent dual-σ̂ ladder;
    D5 preflight on orders + 0.150 gate, post-run fills.
  Remedies (exact formulae in §10 / §11 above):
    R1 mechanism ceiling baseline-only; retire 0.022/0.150 as gate;
    R2 mde = MDE_Z × SE_CI (bootstrap / clustered), forbid 2.8/√blocks as row floor;
    R3 MDE_Z planning only; no clears-floor / |est|≥MDE resolve;
    R4 scale sigma_denominator=paired_delta; selection outcome_level_bps or raw bps;
    R5 preflight fills or PROVISIONAL_FILL_RATE_ADJUSTED; same R1 endpoint; no order-only
       magnitude-carrying pass.
  Pre-fix emission under results/ + analysis.md + screen.md is **invalid for MDE-based
  resolution claims**; prose rewalk of that emission is **refused** (§13.1). Required path:
  implement R1–R5 → Claude review gate → purge generated artefacts → four-cell re-emission.
  Arms, components, domains, universes, PRIMARY estimand, cost disclosure, TRAIN fence:
  **unchanged**.

  Prior unsigned findings — still in force / superseded:

  | Prior | In force | Superseded |
  |---|---|---|
  | A4 unit-capital PRIMARY | yes | — |
  | A5 admission-at-fill; selection floor vs block treatment alignment intent | yes (fill identity; coherent SE under R2) | resolution ladder / band names |
  | A6 no result labels; seven populations | yes | any residual Step-3 0.022–0.150 as resolve/preflight bar; 2.8/√n as row floor |

  running count: 0 looser / 5 tighter / 2 neutral
  L-23 CHECK: last three amendments A5/A6/A7 are TIGHTER, TIGHTER, TIGHTER — one-directional
  streak of 3. **Operator flag raised by the ledger rule; cleared for execution by defect-doc
  §13** (2026-08-07), which explicitly authorises this R1–R5 package + purge + re-run.
  Status: **SIGNED by operator decision §13 / 2026-08-07** (content authorisation for R1–R5
  and the purge/re-emission path). No arm/grid/cost/TEST change.
```

L-23 streak of 3 on TIGHTER is flagged above and **cleared by defect-doc §13** for this package only.

Every pre-measurement amendment appends here with its direction (L-23). A one-directional streak of
3 is an explicit operator flag at the execution gate.

---

## 16. Open items carried into implementation

| # | Item | Resolution point |
|---|---|---|
| **P-1** | The per-cell MDE table must be recomputed at preflight from **realised** counts under all three variance treatments; §10's figures are SPDR-021-derived design-time estimates | Preflight, before execution |
| **P-5** | Two dependence axes are untested (§10): whether the **paired arm-difference** series carries dependence the baseline series does not, and the size of **cross-symbol contemporaneous** correlation. Measure both; neither is addressed by any time-blocking treatment | Preflight |
| **P-2** | H4 origin counts are estimated at ~1/4 of H1 and must be measured | Preflight |
| **P-3** | `CONVERSION-PIN` measured value | Preflight, computed from data |
| **P-4** | Arm B's realised duration distribution → the H2 cap value | After arm B, applied mechanically by the §7 rule |

---

## 17. Claim boundary

This experiment characterises the breakout substrate on H1 and H4 under TRAIN-only, gross,
no-cost-charged conditions. It issues **no** family verdict, opens or retires **no** candidate
family, spends **no** counted TEST read, touches **no** holdout, and makes **no** tradability or
deployability claim. It does not gate XENA. The operator interprets the resulting map and decides
the next research action; the experiment produces the map, not the decision.
