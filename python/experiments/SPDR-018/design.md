# SPDR-018 — Design: powering sweep over the complete checkpoint-017 residue

- **Family / hypothesis:** `CF-VOLDIR-001` / `HYP-D5`
- **Checkpoint:** `2026-07-25-018-trade-opportunity-capture-geometry`
- **SoT (substance precedence):** `.ignore/what-next/alts/opportunity.md` — this design
  narrows, never thins
- **Lane:** SPDR TRAIN-only · vectorised Python · 0 counted TEST reads · no family action · no XENA
- **Status:** DESIGN — execution unauthorised

```
SPREAD-COST-DISCLOSURE:
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: reported cost understates total cost; reported net performance is overstated
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

---

## §1 What this experiment is

> **Falsifiable question.** For every question checkpoint-017 left **UNPOWERED or INCONCLUSIVE**,
> measured **in its original statement**: can it be resolved to its own target precision using
> legitimate power levers alone — and if it can, what is the answer?

This is a **precision experiment, not a mechanism experiment.** It proposes no new market
regularity. Each arm inherits its parent screen's mechanism, object, and estimand **verbatim**;
the only thing SPDR-018 changes is the amount of data behind each estimate and the rigour of the
uncertainty attached to it.

```
MECHANISM: Not a market regularity — a measurement one. Checkpoint-017 left a large residue of
  cells whose estimates were sample-limited rather than effect-limited: SPDR-014 produced 0
  powered cells of 927; SPDR-013 left 125 positive-mean cells every one unpowered; SPDR-012's
  DESIGN band ran at 99-102 dates against the ~225 its own rule demands; SPDR-015 left transition
  counts below n=50 and never scored its CONFIRM slice. The regularity exploited is that these
  are resolvable by pooling and variance reduction WITHOUT changing what is measured. The
  P&L-bearing object is inherited per arm (per-bar magnitude for A; per-episode expectancy for B;
  post-event residual leg for C; per-origin forecast skill for D) and is NOT re-specified.
DERIVED:
  estimand = each parent's estimand VERBATIM, plus a uniform (p, W, L) decomposition layered on
             every cell that carries a signed return (the axis-B gap; SoT §2)
  null     = each parent's own registered controls, re-run at the new n, PLUS one addition
             mandated by SoT M-3 (a magnitude-matched comparator for magnitude-defined
             conditioners)
  horizon  = each parent's frozen horizons; no new horizon is introduced
  test     = block-bootstrap CIs and dependence-matched MDE (SoT §9 M-1) on every cell; the primary
             read is "resolved / not resolvable on this data", not a new verdict
```

**Why this is not a reused stack.** It is *deliberately* the parents' stacks — that is the
mandate. The anti-pattern L-13 warns against is importing an evaluation vehicle *foreign* to the
mechanism; here each arm's vehicle is the one its own mechanism was designed with. What is new is
uniform: the `(p, W, L)` decomposition, the dependence-matched MDE, and the SoT §9 standing rules.

### 1.1 Scope discipline — the mandate, stated exactly

| Rule | Consequence |
|---|---|
| **Every UNPOWERED / INCONCLUSIVE item from 017 is in scope.** No omissions. | §2 enumerates them; anything absent from §2 that exists in a parent analysis is a design defect |
| **Original statement.** No estimand substitution, no un-nesting a conditioner out of its event, no re-definition to reach power | A cell that cannot be powered in its own form is reported **`NOT_RESOLVABLE`** — a valid answer, not a failure |
| **Only authorised drop: `SPDR-017`** | Closed NOT_WORTH on decisive mechanism grounds (model IC ≈ 0; three destroys indistinguishable). Its strata are unpowered because the *mechanism* is absent, not the sample |
| **Multiplicity is disclosed, not rationed** (operator directive) | These are follow-up confirmations of already-registered open questions, not new candidate mining. Full cell count disclosed; no cell is dropped for budget |
| **Reuse the parents' `screen_code/`** | 012/013/014/015 code is the substrate. 018 re-runs their cells; it does not rebuild their objects |

---

## §2 The four arms — the complete 017 residue

### Arm A — SPDR-012 residue (volatility characterisation power deficit)

| # | Open item | Original statement | Why unpowered |
|---|---|---|---|
| A1 | **V-REGIME-HMM** | 2-state Gaussian HMM, Baum–Welch, causal forward filtering; state-conditional magnitude separation | 76/83 cells UNPOWERED |
| A2 | **V-TAIL at D1** | HIGH−LOW exceedance of the unconditional P90/P95 threshold | CONFIRM D1: 2/21 and 0/21 cells with CI-low > 0 |
| A3 | **DESIGN-band deficit across V-LEVEL / V-REGIME / V-XS** | the frozen §6.3 label rule (`MDE = 1.5/√n_dates > 0.10` ⇒ UNPOWERED below ~225 dates) | median 99–102 dates per cell; catalog history cap predates most of the DESIGN band |
| A4 | **V-CLOCK at D1** | session + day-of-week dummies as incremental OOS R² over V-LEVEL | the D1 penalty is 7 dummies on ~100 daily observations — overfitting, not evidence |
| A5 | **§6.4 clause unsatisfiability + calendar-thirds vacuity** | sign-stability in ≥2 of 3 DESIGN thirds | 42/45 cells have only one powered third; the first third precedes the catalog |

### Arm B — SPDR-013 residue (direction expectancy power deficit)

| # | Open item | Original statement | Why unpowered |
|---|---|---|---|
| B1 | **`stop`-only and `trail`-only exit arms** | expectancy bps under each isolated exit mode | degenerate episode counts, one-tail means; all UNPOWERED |
| B2 | **unpowered `time`-arm cells** | expectancy bps, fixed-horizon exit | MDE / date floors |
| B3 | **the 125 positive-mean cells** | `expectancy_partial` mean > 0 | every one UNPOWERED (MDE > 10 bps and/or < 30 dates and/or thirds-unstable) |
| B4 | **ZZ structural leg, per symbol** | D-ZZ signalflip expectancy per symbol | n ≈ 230–250 but fat-tailed; UNPOWERED via MDE, **not** via trade count |
| B5 | **M15 arms** | all D-SMA and D-ZZ arms on the M15 clock | carried but under-read |

**Arm B is where `W` and `L` are measured on real episodes** — the axis-B gap that SoT §2
exposed. It is the highest-value arm for parameterising SPDR-019/020.

### Arm C — SPDR-014 residue (zone / event / post-event residual)

| # | Open item | Original statement | Why unpowered |
|---|---|---|---|
| C1 | **the residual object itself** | conditional post-event residual ≠ ambient, per symbol × z × H × event × h | **0 of 927 powered cells**; MDE 20 / 172 / 796 bps against a ≤10 floor |
| C2 | **shock-conditioned MOMO** | `\|r_t\|` top-decile on the decision bar, **inside** the z/H/E-TOUCH/h event grid | pooled CI excluded 0 but no per-symbol cell powered |
| C3 | **ordered `last_k` L→H vol-flip, and the `LHL` mirror** | ordered slow-regime label sequence, K ∈ {1,2,3}, **inside** the event grid | thin strata |
| C4 | **E-TOUCH / E-CLOSE asymmetry** | breach-type split of the same residual | never powered |
| C5 | **magnitude scaling** | `mag_high` / `shock` / vol-tercile strata lift residual **magnitude** while the rate stays ≈ 0.50 | strata thin |
| C6 | **z / h dose-response** | low-z + long-hold vs high-z behaviour | tail-driven, unpowered |
| C7 | **DESIGN→CONFIRM sign flip** | 12/17 symbols reversed; pooled +11.3 → −4.3 | cannot distinguish instability from noise at n |
| C8 | **pooled rate lean** | `p_momo` 0.478 pooled vs the 18-vs-7 per-cell count | two weightings disagree; neither powered |
| C9 | **`DA-STRADDLE`** | both-side leg pair at the zone anchor, exit both at H | UNPOWERED. **Characterisation only** — operator exception to the direction-agnostic deferral (SoT §0). No strategy framing, no policy, no graduation path |

**C2/C3/C4 are measured inside the event grammar, as registered.** No un-nesting. If a cell cannot
reach its MDE in that form, it is reported `NOT_RESOLVABLE` with the shortfall quantified.

### Arm D — SPDR-015 residue (conditioner science)

| # | Open item | Original statement | Why unpowered |
|---|---|---|---|
| D1 | **`trans_up` / `trans_dn` transition counts** | directional transition skill vs persistence | n_trans < 50 — rare switches under sticky level regimes |
| D2 | **run-length MAE** | predicted vs realised regime run length | emitted as disclosure only, never powered |
| D3 | **T-GT-MED10** | "next swing > last-10 median", ridge / AR1 / logit | 12/21 SUPPORTED → INCONCLUSIVE |
| D4 | **T-GT-MED5 failing cells** | same at K=5 | 19/21; the 2 failures unexamined |
| D5 | **2a H4 k=1** | ΔBrier vs persistence, H4 clock, 1 bar ahead | 6/16 SUPPORTED, median ≈ +0.0002 |
| D6 | **R-HMM-RV empirical and logistic** | HMM on raw `rv20`, ΔBrier vs persistence | 3/15 and 7/15 |
| D7 | **D1 stickiness** | `P(stay)` on the daily clock | emitted disclosure-only, never scored |
| D8 | **the CONFIRM verify slice** | 2a and 2b scored on CONFIRM separately from DESIGN | **never scored** — SPDR-015 §6 carried this as an explicit follow-up |

### 2.1 Authorised exclusion

`SPDR-017` (HYP-D4) in full. Recorded reason: closed **NOT_WORTH** on mechanism facets that are
decisive independently of power — walk-forward ridge OOS IC ≈ 0 (rank −0.008, linear −0.032), the
DERIVED error-dynamics layer inert (A1−A0 median −5.8 bps, 5/16 symbols improve), three destroy
controls indistinguishable (corr ts–mr 0.985), and M-ZONE ≤ the Z-VOL baseline. Powering an absent
mechanism buys nothing.

---

## §3 Object identity

```
OBJECT-IDENTITY:
  measurement object == trading object: YES, PER ARM, BY INHERITANCE.
    A: next-horizon |move| / state-conditional magnitude — a measurement object, no P&L claim
       (as registered in SPDR-012; explicitly not a traded object)
    B: a signed episode under a declared capture geometry, expectancy in bps — the same episode
       the policy would trade (SPDR-013 §5); episode-level, not per-leg (L-16/L-18)
    C: the post-event residual leg, entry at breach-entry open, exit at open+h (SPDR-014 §4)
    D: per-origin forecast skill — a measurement object, no P&L claim (SPDR-015)
    No arm re-specifies its parent's object. That is the mandate (§1.1).
  measured conditioning event == traded entry event: YES, PER ARM, BY INHERITANCE.
    C is the load-bearing case: the conditioner is evaluated on the decision bar INSIDE the
    z/H event grammar, and the residual is measured from the breach entry that the grammar
    defines — exactly as SPDR-014 registered it. No conditioner is lifted out of its event.
  effect-splitting windows non-overlapping: N/A per row, BUT forward windows of adjacent rows
    overlap by construction in arms A and C. Handled in uncertainty, not design: block bootstrap
    with block >= horizon (§6.2). A library block=5 default is prohibited (Phase-010).
```

**Estimand vehicle.** SPDR lane: no `xen.adjudication` object and no `estimand_validation.json`
(the lane exempts screens). Integrity substitute = code-asserted fence + causal-lag self-check
(§8). **No local accounting primitive may mimic `xen.adjudication` for a verdict** (L-18).

---

## §4 The uniform layer applied to every arm

### 4.1 The `(p, W, L)` decomposition (SoT §2 — the axis-B gap)

Every cell carrying a signed return emits, in addition to its parent's own metrics:

```
p     = P(r > 0 | cell)                      rate
W     = E[  r | r > 0, cell ]   bps          mean win size
L     = E[ -r | r < 0, cell ]   bps          mean loss size
W_L   = W / L                                payoff asymmetry
p_be      = L / (W + L)                      gross break-even rate
p_be_net  = (L + cost) / (W + L)             net break-even rate
edge      = p - p_be_net                     THE quantity of interest
```

`mean r = p·W − (1−p)·L` is exact by definition and is **asserted numerically per cell** in the
self-check (reconstruction residual < 0.01 bps). Cells where `r == 0` are excluded from `p` and
counted (`p_flat`), disclosed.

**κ is a diagnostic, never a multiplicative term** (SoT §2.1). Where a parent emitted MFE, report
`median(r/mfe)` labelled **non-tradable ceiling-relative**; it multiplies nothing.

### 4.2 Cost

`xen.evaluation.bybit_round_trip_cost_bps` — fees + discrete funding + 2.0 bps allowance,
`spread_bps` **absent**. Raw `SpreadBps` is prohibited as a cost input (P-20 / L-36). Net figures
are a disclosure overlay, never a verdict object.

### 4.3 Unit pin (L-21)

```
CONVERSION-PIN:
  divisor object: sigma_t = LTF H1 Parkinson EWMA(lambda=0.94), 60 H1-bar warm-up, causal <= t-1,
                  in bps; horizon-scaled sigma_t*sqrt(h). Identical object to SPDR-014's Z-VOL
                  width; single definition shared across all four arms.
  measured value: TRAIN-median per symbol and pooled, COMPUTED AT RUN -> results/unit_pin.json.
                  Never recalled, never asserted. Covers all 25 symbols or states the gap.
  resulting effect: sigma-unit effects converted back to bps by the pinned value; BOTH forms
                  reported side by side on every cell.
  cost floor:     13.5 bps partial. Spread NOT charged -> the true floor is higher.
                  A sigma-unit effect is NEVER compared to the floor.
```

**bps is primary everywhere.** σ̂-normalisation exists to buy power for pooling; it may never
become a reported headline in its own units (P-15).

---

## §5 Power levers — legitimate, uniform, no estimand substitution

| # | Lever | Applies to |
|---|---|---|
| 1 | **Pool across symbols**, with σ̂-normalisation to make pooling valid across vol scales | all arms |
| 2 | **Use the full TRAIN span** where the parent design permits, rather than the DESIGN sub-band | A3, A5, C1, D8 |
| 3 | **Score CONFIRM explicitly**, not as an afterthought | all arms; D8 by name |
| 4 | **Report effective coverage, not nominal span** (SoT §9 M-4) | all arms |
| 5 | **Quantify the shortfall** where a cell still misses its target MDE | all arms |

**Not levers, and refused:** re-defining an estimand; un-nesting a conditioner out of its event;
dropping thin symbols; pooling upward until a band label changes; substituting the iid MDE to make
a cell look powered.

**`NOT_RESOLVABLE` is a first-class result.** A cell that cannot reach its target MDE in its
original form is reported with: realised `n`, block MDE, target, the multiple short, and the `n`
that *would* be required. That answers the 017 open question.

---

## §6 Uncertainty and tests

### 6.1 Tests (inherited per arm, plus the uniform layer)

| Read | Test |
|---|---|
| `p` vs `p_be_net` | exact binomial + block-bootstrap CI on `edge` |
| mean, median, **10% trimmed mean** | block-bootstrap CI on each — all three always co-reported (this family is fat-tailed; SPDR-013 saw mean −2 vs median −47 on the same cell) |
| `W`, `L`, `W/L` | block-bootstrap CI on each; `W/L` CI by the same resample |
| parent's own metric (IC, ΔBrier, gap, expectancy) | as the parent registered it |
| live vs control | seed-battery percentile + one-sided p + effect size; **never** an `at_or_above_pXX` boolean (L-32) |

Parametric normal-theory tests excluded (fat tails, dependent windows). GARCH / ADF excluded per
methods-catalog.

### 6.2 Dependence-matched uncertainty (BINDING)

- aggregate to **per-calendar-day** sufficient statistics; resample **day-blocks** of `{1,3,7}`
  days; minimum block = 1 day = 24 H1 bars **≥ every horizon in scope**;
- envelope = **min/max over blocks × seeds** (conservative), 5-seed battery,
  `xen.evaluation.block_bootstrap_ci`, effective block capped `< n` (INFR-004 / L-20);
- **the reported MDE is the block MDE (SoT §9 M-1).** The iid `2.8σ/√n` form inherited from SPDR-014
  is emitted **only** as a labelled companion column and may not drive a band label.

### 6.3 Standing corrections M-2 … M-5 (SoT §9)

| ID | Rule |
|---|---|
| **M-2** | `h` is an index offset, not wall-clock. Every horizon read co-reports the **exact-span subset** and the span distribution (median, p95, max, % exceeding `h` hours) |
| **M-3** | Any conditioner **defined on move magnitude** (C2 shock, C5 `mag_high`, A2 tail) additionally gets a **`\|r_t\|`-matched comparator**, not just a side-matched one — otherwise the control cannot separate the state from "this was a big bar" |
| **M-4** | Power plans use **effective** multi-symbol coverage. The DESIGN band is one symbol deep before 2022-07-14; the effective multi-symbol window is materially shorter than the nominal 20 months. Emitted per cell |
| **M-5** | Collapse fraction is **disclosure only** — it is uninterpretable when the live mean is near zero. Percentile + null distribution are the usable objects |

---

## §7 Controls

Each arm re-runs **its parent's own registered controls** at the new `n` — that is what makes this
a powering experiment rather than a new one. Parent control blocks are inherited verbatim from
`SPDR-012/013/014/015` `design.md`. Three uniform additions:

```
CONTROL MAGNITUDE-MATCHED-COMPARATOR   [class: within_sample_attribution -> REPORT LAYER]  (M-3)
  question answered: on a conditioner DEFINED by move magnitude, is the effect the volatility
    state, or merely that the decision bar was large?
  population: bars matched to the live cell on the |r_t| distribution (decile-stratified draw)
    but NOT carrying the state; the live rows and their +-1 bar neighbourhood are EXCLUDED.
  DISJOINT: a different row set, drawn to match on magnitude and differ on state. It CAN show a
    different answer: if the effect is "big bar" the comparator reproduces it, if the effect is
    "state" it does not. (B-1 clean: it is not the signal population relabelled.)
  bite/MDE: MDE CURVE - plant {5,10,20,40} bps on the live rows, report the seed-battery
    percentile at each level; the curve states the smallest plant detectable at realised n.
  non-vacuity: re-selects which rows enter the cell, moving the conditional mean directly.
  expected if H true: live outside the comparator distribution; if H false: inside.
  disclosure: percentile, null distribution, collapse fraction (M-5: disclosure only).
  seeds: >= 2000
```

```
CONTROL SIDE-DERANGEMENT   [class: within_sample_attribution -> REPORT LAYER]
  applies to: every cell carrying a signed return (arms B and C).
  question answered: does the cell tell us WHICH WAY, or is a positive mean this symbol's drift?
  population: same rows, side labels deranged within (symbol x calendar-month); paths, states,
    entries and exits unchanged.
  DISJOINT: zero fixed points; a drifting symbol with unbalanced sides yields a non-zero deranged
    mean while a state-driven cell yields ~0 - the control can differ.
  bite/MDE: same {5,10,20,40} bps plant curve.
  non-vacuity: the metric is the mean of a SIGNED return; deranging sides moves it directly.
    (Contrast the banned pattern: permuting realised P&L preserves the mean - L-14 / EXP-012.)
  disclosure: percentile + null distribution (+ collapse fraction, M-5 disclosure only).
  destroy form: DERANGEMENT (zero fixed points, measured and reported; L-28); seeds >= 2000
```

```
CONTROL AMBIENT-BASE   [class: disclosure -> BASE-CONDITIONAL OBLIGATION, spdr-lane]
  question answered: the cell's OWN conditional effect on the outcome distribution - mean,
    dispersion, sign, and now also W, L and W/L - independent of profitability.
  population: the unconditional distribution over the same eligible rows.
  NOT a lift-vs-baseline read. Per the lane's binding directive, a measured distributional shift
  on a null base is a POSITIVE QUANTIFICATION reported as a magnitude, never qualified away as
  "within noise".
  disclosure: delta on each of mean / median / dispersion / p / W / L / W_L, each with CI.
```

### 7.1 Leak tripwire (HARD — blocking)

```
TRIPWIRE-1 CONSTRUCTION ASSERTIONS  [HARD]
  per-row index assertions per arm: every feature index <= its parent's declared lag; entry
  strictly after the decision bar; exit at the declared offset; expanding statistics use only
  rows strictly before the decision bar. Violation aborts the run.

TRIPWIRE-2 LEAKY-VARIANT DISCRIMINATION  [HARD]
  Per arm, build a deliberately leaky twin whose conditioner threshold is computed over a window
  INCLUDING the forward horizon. Emit both. The legal variant must differ from the leaky twin by
  orders of magnitude on matched cells.
  vacuity check: the leaky threshold selects rows using the outcome, which shifts the conditional
    mean materially. SPDR-012 measured the analogous contrast at ~12 orders of magnitude.
  WHY NOT AN OUTCOME-SIDE DESTROY: SPDR-012 AMENDMENT-T1 established that no outcome-side destroy
    can detect look-ahead for a fixed predictor. A forward-path derangement is therefore a REPORT
    LAYER only and is explicitly NOT the causality claim, which rests on TRIPWIRE-1 and -2.

TRIPWIRE-3 FORWARD-PATH DERANGEMENT  [REPORT LAYER, not the causality claim]
  derange (decision row -> forward path) within symbol x month; zero fixed points; expected
  collapse to ~0; reported as a null distribution, no pass field.
```

---

## §8 Interpretation bands (labels, never gates — INFR-016)

```
BANDS (per cell). Each arm ALSO keeps its parent's own registered bands, reported alongside.

  edge = p - p_be_net   (the uniform read; SoT §2.2 - NOT "p > 0.5")
    SUPPORTED      edge > 0 with ci_low > 0
    WASH           |edge| < block-MDE, CI spanning it   (report as "at break-even")
    CONTRADICTED   edge < 0 with ci_high < 0            (a powered finding, not a failure)
    UNPOWERED      block-MDE > the cell's own target precision
    NOT_RESOLVABLE UNPOWERED after every §5 lever is applied - reported with realised n,
                   block MDE, target, multiple short, and the n that would be required

  mean r (bps)
    SUPPORTED      >= +10 bps with ci_low > 0
    WASH           |mean| < 10 bps with the CI spanning it
    CONTRADICTED   <= -10 bps with ci_high < 0
    UNPOWERED      block-MDE > 10 bps

POOLED: disclosure-only unless homogeneity is shown across symbols.
```

**Labels, not gates.** No `pass` field is emitted anywhere. Each read is an
`observed / ideal / interpretation` triple (`xen.xena.report_layer` shape). Nothing machine-
dropped, no auto-RETIRE, no multi-gate conjunction.

**B-5 is binding and symmetric.** UNPOWERED and NOT_RESOLVABLE are power statements and can never
be reported as negatives; equally, SUGGESTIVE is never reported as SUPPORTED.

**A powered CONTRADICTED is a routing result, not a null** (SoT §10 end-state 3) — a reversal
where continuation was registered, or a `W/L` handle where a rate was expected, opens a
counter-design under new registration.

---

## §9 Power statement

**Target precision is inherited per arm** — each cell is scored against *its parent's own* declared
precision bar, not a single global number:

| Arm | Target precision (parent's own rule) |
|---|---|
| A | SPDR-012 §6.3: `MDE = 1.5/√n_dates ≤ 0.10` ⇒ ≥ ~225 unique dates per cell |
| B | SPDR-013: MDE ≤ 10 bps **and** ≥ 30 dates **and** thirds-stable |
| C | SPDR-014 §8.1: `n_events ≥ 80` **and** `n_dates ≥ 30` **and** MDE ≤ 10 bps |
| D | SPDR-015: `n_origins ≥ 80` **and** `n_dates ≥ 30` |
| uniform | `edge`: block-MDE on `p` below the cell's own `|edge|` |

```
POWER (prospective; RE-ASSERTED against realised n at run):
  MDE reported = BLOCK MDE (SoT §9 M-1). The iid 2.8*sigma/sqrt(n) form is a companion column only.
  For every cell emit: realised n, n_dates, effective multi-symbol coverage (M-4), block MDE,
  target, and - where short - the n that would be required.
```

**Predeclared UNPOWERED / expected NOT_RESOLVABLE** — these can never be read as negatives (B-5):

- **A3, A5** — the DESIGN band cannot reach 225 dates for most cells; the catalog history cap
  predates it. Expected `NOT_RESOLVABLE` on the DESIGN band specifically; the answer to the open
  question is then "this band cannot support the claim", which is what 017 needed to know.
- **B1** — `stop`-only and `trail`-only arms are degenerate by construction (winners run to the
  band edge with no upper exit); pooling may not fix a one-tail estimator.
- **C2, C3, C4** — event-nested strata; original form retained by mandate. Pooling + σ̂ may not
  close the gap. Shortfall quantified.
- **D1** — transitions are rare under sticky regimes; `n_trans` may stay below 50 pooled.
- **cTrader strata** — replication role only; never scored for power (§10).
- **`1000BONK`, `BLUR`, and the warm-up-empty listings** — retained as explicit UNPOWERED rows,
  never silently dropped (no post-outcome universe edit).

**No prospective effect sizes are stated in this design.** Bands and targets are set from each
parent's own registered precision rule (the table above), never from an anticipated result.

---

## §10 Scope

| Item | Freeze |
|---|---|
| Primary catalog | Bybit USDT linear perps, `data/catalog/`, INFR-011 fence |
| Universe | top-25 30d USD volume (AMENDMENT-U1); pin `cf-voldir-001-universe.json`; recompute + assert set equality |
| Clocks | **inherited per arm** — A: H1/H4/D1; B: H1/M15; C: H1 (+H4 co-report); D: H1/H4 (+D1 disclosure). No new clock |
| Horizons | inherited per arm. No new horizon |
| TRAIN fence | `analysis_start 2021-06-29T06:53Z` → `train_end 2023-12-18T00:00Z`; asserted in code |
| DESIGN / CONFIRM | `[2021-06-29, 2023-03-01)` / `[2023-03-01, 2023-12-18)` — as 012/013/014/015. **Both scored explicitly** (D8) |
| Global holdout | `2025-01-08T00:00Z` — **never queried** |
| Replication catalog | `data/catalog_ctrader/` (EURUSD, XAUUSD, USTEC); fence `python/experiments/INFR-021/artifacts/fence-manifest.json`, sha256 `4cdc7b01dd47200710d0d961639d55d52e1129ca89096e841eafd816b6061de0` |
| cTrader holdout | `2024-12-13` onward — **never queried**; fence path passed explicitly |
| cTrader role | **Replication only** (AMENDMENT-C1) — scored and reported separately, **never pooled into `n`** |
| Complexity | 4 arms, each reusing its parent module; 1 uniform metrics layer; 1 control module; ≤ 8 plots |

---

## §11 Golden traces (QA derives the numbers — the developer must not)

Deterministic selection rules, so QA computes expected values independently from the catalog.

```
G1 (Arm A - HMM state + magnitude separation):
  BTCUSDT, H1, DESIGN. First origin where the causal forward-filtered HMM state == HIGH.
  QA computes: fit window end < origin, the state, next |oo| in bps, and the cell's running
  HIGH-LOW gap contribution.

G2 (Arm B - episode expectancy + the (p,W,L) layer):
  SOLUSDT, H1, DESIGN, D-ZZ signalflip. First completed episode.
  QA computes: entry ts/price, exit ts/price/reason, gross bps, cost bps, partial-net bps,
  and whether it contributes to W or to L.

G3 (Arm C - event-nested residual, ORIGINAL form):
  ETHUSDT, DESIGN, Z-VOL, z=1.5, H=12, E-TOUCH, h=12. First decided event whose decision bar
  carries last_k_state_2 == "LH".
  QA computes: band width from sigma_t, the touch bar, breach side, entry open, exit open,
  r_h in bps. This trace exists to prove the conditioner was read INSIDE the event grammar.

G4 (Arm D - CONFIRM verify slice, the never-scored item):
  XRPUSDT, H1, CONFIRM, 2b T-GT-CUR. First scored origin.
  QA computes: features at swing confirmation, prediction, realised next-swing size, hit/miss,
  and the Brier contribution.

G5 (uniform layer - identity reconstruction):
  Any cell from G2 or G3's parent cell. QA computes p, W, L from the emitted rows and asserts
  p*W - (1-p)*L equals the emitted mean to < 0.01 bps.

G6 (leak discrimination): the same rows as G3 under the TRIPWIRE-2 leaky twin; QA confirms a
  material difference and that the legal variant is the one emitted.
```

---

## §12 Integrity checklist (code-asserted; SPDR stage-2 self-check)

| Check | Assertion |
|---|---|
| TRAIN fence | `max(exit_ts) < 2023-12-18T00:00Z`; zero rows at or after it |
| Holdout | zero queries `>= 2025-01-08`; cTrader zero queries `>= 2024-12-13` |
| Causality | per-row index assertions per arm (TRIPWIRE-1); expanding stats exclude the decision bar |
| Universe pin | top-25 recompute == pin file, set equality |
| Fence provenance | cTrader fence sha256 == `4cdc7b01…`; Bybit fence == INFR-011 manifest |
| **Identity reconstruction** | `\|p·W − (1−p)·L − mean\| < 0.01 bps` on **every** signed cell |
| **MDE column** | the band-driving column is the **block** MDE; the iid column is labelled companion-only |
| **Span disclosure** | exact-span subset and span distribution emitted for every horizon cell (M-2) |
| Derangements | fixed-point count == 0, measured and reported |
| Parent parity | each arm reproduces its parent's published cell values on the parent's own band, to a declared tolerance — **the proof that the object was not silently re-specified** |
| Determinism | `--jobs` parallel bit-identical to sequential |
| Golden traces | G1–G6 pass |
| No local accounting | no `xen.adjudication` mimicry; cost is an `xen.evaluation` overlay |
| Code hash | sha256 of `screen_code/` pinned into `results/integrity_selfcheck.json` |

```
HARD (block execution / invalidate emission):
  TRIPWIRE-1, TRIPWIRE-2, TRAIN fence, holdout, universe pin, identity reconstruction,
  parent parity, derangement fixed-point count, golden traces, determinism.
INFORMATIVE (operator judges, no auto-verdict):
  every effect size, control percentile, collapse fraction, band label, dose-response shape,
  cost overlay, cTrader replication.
```

**Parent parity is the anti-drift check.** If arm C cannot reproduce SPDR-014's published cells on
SPDR-014's own band, the object was re-specified — which this design forbids.

---

## §13 What this design refuses

- Re-defining any parent estimand, or un-nesting a conditioner out of its event, to reach power.
- Dropping any 017 open item other than `SPDR-017` (§2.1).
- Using the **iid** MDE to drive a band label.
- Reporting a σ̂-unit effect as a headline, or comparing one to the cost floor (P-15 / L-21).
- Reading UNPOWERED or NOT_RESOLVABLE as a negative; reading SUGGESTIVE as SUPPORTED (B-5).
- Framing `DA-STRADDLE` as anything but characterisation (SoT §0).
- Any expectancy framing of the form `p > 0.5` — the break-even is `p_be_net`, not 0.5 (SoT §2.2).
- Any capture-geometry, exit, or sizing claim — that is SPDR-019/020.
- Any tradability, deployability or cost-complete claim; any family status change; any XENA.

---

## §14 Amendment ledger

```
No amendments. Registered 2026-07-25.
running count: 0 looser / 0 tighter / 0 neutral
```

Checkpoint-level amendments in force: **AMENDMENT-U1** (top-25 universe, NEUTRAL),
**AMENDMENT-S1** (per-symbol sufficiency; multi-symbol = credibility only, NEUTRAL),
**AMENDMENT-C1** (cTrader replication-only, NEUTRAL), **AMENDMENT-C2** (expectancy refusal stated
against `p_be_net`; blended scores carry their term decomposition; spread pin is a Step-2
prerequisite — TIGHTER).

---

## §15 Artifacts

| Path | Content |
|---|---|
| `screen_code/` | 4 arm runners, each importing its parent module; uniform metrics + controls layer |
| `results/arm_A.parquet` … `arm_D.parquet` | per-cell rows, parent metrics + the `(p,W,L)` layer |
| `results/metrics_by_cell.parquet` | every cell: parent metric, `p`/`W`/`L`/`W_L`/`p_be_net`/`edge`, block + iid MDE, span stats, coverage, band label |
| `results/parent_parity.json` | reproduction of each parent's published cells + tolerance |
| `results/controls.json` | inherited + the three uniform controls, plant curves, percentiles, null shapes |
| `results/unit_pin.json` | measured σ̂ medians (computed, not asserted) |
| `results/not_resolvable.json` | every cell that could not be powered: realised n, MDE, target, required n |
| `results/golden_traces.json` | G1–G6 |
| `results/integrity_selfcheck.json` | fence, causality, pin, identity reconstruction, parity, code sha256 |
| `results/ctrader_replication.parquet` | replication arm, scored separately |
| `screen.md` | neutral quantification (subordinate) |
| `analysis.md` | **fresh-context analyst — binding read** (SPDR stage 5, mandatory) |
