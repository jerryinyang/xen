# SPDR-020 — Design: E-TOUCH / E-CLOSE event grammar under direction-aware capture geometry

- **Family / hypothesis:** `CF-VOLDIR-001` / `HYP-D7`
- **Checkpoint:** `2026-07-25-018-trade-opportunity-capture-geometry`
- **SoT (substance precedence):** `.ignore/what-next/alts/opportunity.md` §6.2 / §6.3 — this design
  narrows, never thins
- **Parent object:** `SPDR-014` (`HYP-D1`) — the zone → breach-event → post-event residual grammar,
  **inherited, not re-specified**
- **Binding reflection inputs:** `docs/experiments-docs/checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/reflection-mid-volatility-model.md`
  §2, §5.2, §5.4, §5.4a, §5.9
- **Governing amendments:** **AMENDMENT-C5** (gross-only measurement), **AMENDMENT-C6** (layer
  protocol), plus standing **C1**, **C2**
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

> **Falsifiable question.** On the SPDR-014 breach-event entry, taken as it comes, does any layer
> of the opportunity model move the payoff residual `log R = log(W/L) − log((1−p)/p)` reliably
> above zero, relative to the unmodulated baseline?

Same question as `SPDR-019`, same protocol, **different entry object**. SPDR-019's entry is a
price-pattern breakout with a momentum prior; this one is a volatility-band breach with an explicit
MOMO/MR side rule. Running both is what separates "this capture policy works" from "this entry
happens to suit this capture policy".

```
MECHANISM: A forecast-width band is drawn around an anchor from the proven volatility scale
  (Parkinson-EWMA) or the proven ZigZag next-swing magnitude forecast. Price BREACHES that band -
  by intrabar touch (E-TOUCH), by sustained close beyond it (E-CLOSE), or only at the horizon's
  last bar (E-HORIZON). Capital is committed at the breach, signed in the breach direction (MOMO)
  or against it (MR); both arms are emitted and NEITHER is assumed. The P&L-bearing object is the
  single signed post-event EPISODE. SPDR-014 established the event cadence and the residual's
  existence; SPDR-018 powered it (121 cells at median block MDE 7.87 bps against the parent's
  0 of 927) and measured its terms: p 0.467, W 142.1, L 124.5, W/L 1.136 - a near-coin-flip,
  near-symmetric object whose rate sits 0.0007 from its own gross break-even. The regularity under
  test here is NOT that the breach predicts direction - it is that the SAME forecast that sets the
  band can also place the exit boundaries so the realised payoff sits OFF the driftless mirror.
  The falsifier is log R indistinguishable from zero under every layer at a stated MDE.
DERIVED:
  estimand = per-EPISODE signed gross return in bps (side-signed r_h, SPDR-014's own residual
             object), decomposed per cell into (p, W, L, W_L, p_be, log R). log R is primary.
  null     = the DRIFTLESS MIRROR log R = 0 - the object's own arithmetic zero line. NOT zero P&L.
             Plus SPDR-014's inherited side-derangement, whose live read on this object was
             -12.221 bps at percentile 0.0065 and which is therefore known non-vacuous HERE.
  horizon  = SPDR-014's frozen h in {4, 12, 24} bars, inherited. No new horizon.
  test     = block-bootstrap CI on log R with block >= h; dependence-matched block MDE (M-1) in
             LOG UNITS per cell, stated before the run.
```

**Why this is not a reused stack.** The estimand is this event object's own residual episode; the
null is that object's own zero line; the horizon is the parent's frozen post-event window. The one
thing deliberately inherited whole is SPDR-014's event grammar — which is the point: the checkpoint
requires this object measured under *designed* capture rather than the parent's incidental exits.

### 1.1 The named mechanism for `R > 1` — required before any capture design (SoT §10)

Governance demands the mechanism, not a search: *"any 019/020 proposal must NAME the mechanism that
puts `R > 1`, because five distinct exit devices spanning a 5.3× powered `W/L` range did not."*
This design names one, and it is falsifiable:

> **Claim.** The driftless mirror binds when the exit boundaries are placed *independently of the
> conditional dispersion of the path*. A breach event is a state in which the forward dispersion is
> both **elevated and forecastable** (V1, V11, V20). If the exit boundaries are placed as multiples
> of that *conditional* forecast rather than as constants, the truncation points sit at a fixed
> quantile of the actual forward distribution rather than at a drifting one — and a fixed-quantile
> truncation does not have to reproduce the unconditional `(1−p)/p` relation.

**Why this may still be nothing, stated up front (P-02, and the reflection's own finding).** The same
argument would have predicted a lift for SPDR-018's `stop` and `trail` modes, and it did not appear:
`W/L` moved 5.3× across powered cells with the mean pinned on the zero line, on two asset classes.
The mechanism above is therefore a **hypothesis with a known prior against it**, not a rationale. It
survives only in the specific form "boundaries scaled to a *forecast* of conditional dispersion",
which the parents' incidental geometries never tested — that gap, and nothing broader, is what this
design probes.

**Pre-registered expectation (reflection §5.6).** The predictions this design commits to in advance:
ŝ-scaling every boundary leaves `log R` unchanged; selection raises `W` and `L` together with `W/L`
moving less than ~0.3; shock- and level-gated selections are close to additive. A result contrary to
any of these is a finding; a result matching them is the expected outcome.

---

## §2 The entry — inherited from SPDR-014

### 2.1 The inherited grammar (unchanged)

| Element | Definition (SPDR-014, verbatim) |
|---|---|
| **Band width source** | `Z-VOL` = LTF H1 Parkinson EWMA(λ=0.94) × frozen `s_symbol`; `Z-MAG` = ZigZag next-swing magnitude forecast; `Z-MAG-SENS` = Z-MAG at half width |
| **Anchor** | `open[t+1]`, causal |
| **Band half-width** | `z × width`, `z` swept (see 2.2) |
| **Event window** | `H` bars from the anchor |
| **Event types** | **E-TOUCH** (intrabar pierce, earliest) · **E-CLOSE** (bar closes outside, sustained) · **E-HORIZON** (outside only at the last bar) |
| **Entry** | breach bar `j` → fill at `open[j+1]` |
| **Exit (parent)** | `open[entry + h]`, `h ∈ {4, 12, 24}` — **this is what the L4 devices replace** |
| **Side** | **MOMO** (with the breach) and **MR** (against it) both emitted; neither assumed |
| **UNDECIDED side** | SPDR-014's rule inherited verbatim: an event whose side cannot be resolved is marked **UNDECIDED**, excluded from the signed cells, and **counted and reported** — never silently dropped |

### 2.2 The `z` grid, and why there is no selectivity gate (operator directive 2026-07-28)

`z ∈ {1.5, 2.0, 2.5, 3.0}`. `z = 1.0` is dropped — it is not an outlier band. **Every signal the
grid produces is taken.**

**There is no selectivity threshold, and this is deliberate.** An earlier draft of this design gated
the primary grid on `p_event ≤ 0.60`. That gate is **removed entirely**, for three reasons:

1. **It was an invented number.** No source document specifies 0.60; it appeared in no SoT, no
   checkpoint design and no registered hypothesis.
2. **It is the wrong shape.** A hard cutoff deciding which cells may carry a conclusion is exactly
   the class of arbitrary value-gate the programme retired under **INFR-016 / L-32** — value and
   quality reads are **report layers**, and the operator decides what advances. Nothing is
   machine-dropped.
3. **It contradicts the purpose of this experiment.** This is a **capture-geometry** experiment. It
   is not searching for the best-selecting signal — the opposite: the entry is fixed and
   deliberately unimpressive, and the research variable is the geometry wrapped around it. A gate
   that deletes cells for being unselective is optimising the entry, which this checkpoint forbids
   (SoT §1.2, direction is measured, not targeted).

**`p_event` is still computed and emitted on every cell, per event type — as a reported covariate,
never as a filter.** It is a *dose-response axis*: breach rate varies across the `z` grid, and
reading `log R` against it is strictly more informative than a pass/fail line would have been. The
checkpoint's binding carry-forward requirement — *the band's selectivity must be visible rather than
assumed* — is satisfied by measuring and reporting it, which is what SPDR-014 failed to do.

**Reconciliation with the registered `HYP-D7` wording.** `HYP-D7` is registered as the capture
question *"…with a band that actually selects"*. This design satisfies the **intent** of that clause
— SPDR-014's defect was that selectivity was **invisible**, not that it was high — by measuring and
reporting `p_event` on every cell and reading `log R` against it. It does **not** satisfy a literal
reading in which unselective cells are excluded, and the operator directive of 2026-07-28 removes
that reading deliberately (an exclusion rule would be optimising the entry, which the checkpoint
forbids). **This departure is disclosed here and in the amendment ledger**; it narrows nothing and
excludes nothing.

**This remains a grid extension, not an estimand substitution.** `z` is a registered parameter of
the 014 object; the object, its anchor, its event types and its residual definition are untouched.
SPDR-014's frozen grid was `{1.0, 1.5, 2.0}`; this design **drops 1.0 and adds 2.5 and 3.0**, which
is disclosed here, in the cell count (§10) and in the amendment ledger (§14).

**Parent parity is asserted:** at `z = 1.5, H = 12, h = 12, E-TOUCH, Z-VOL, DESIGN`, this screen must
reproduce SPDR-014's published per-symbol cells to a **declared numeric tolerance: |Δ| ≤ 1e-9 on
`mean_r_h`, `p_momo`, `p_mr` and `n_decided`, per cell**. SPDR-018 achieved 9.1e-13 on this same
arm-C object, so 1e-9 is loose enough to absorb float ordering and tight enough that any real
re-specification fails it. Emitted to `results/parent_parity.json`. That is the proof the object
was not silently re-specified.

**Two parent rules are restored, not replaced** (QA finding): SPDR-014's **UNDECIDED-side rule** and
its **5 bps flat deadband** are inherited verbatim. The `r == 0` flat test in an earlier draft
silently changed the parent's deadband and is withdrawn.

### 2.3 Carry-forward fix 2 — the DESIGN→CONFIRM sign flip is **discharged**

SPDR-014 flagged a 12/17-symbol sign flip between bands. **SPDR-018 resolved it (C7):** 2,714 pairs,
**44.14% flip — below a coin flip**; only 6.63% exceed the two-band MDE; `n`-weighted the bands agree
to **0.33 bps**. Replicated on cTrader (40.99%, 0.65 bps). It was a thin-cell equal-weighting
artifact.

**Consequence for this design:** the flip is **not re-litigated**. Both bands are scored explicitly
and reported `n`-weighted; equal-weighted medians across thin cells are refused as a headline.

---

## §3 Object identity

```
OBJECT-IDENTITY:
  measurement object == trading object: YES. Both are the signed post-event EPISODE: fill at
    open[j+1] -> exit at the variant's exit rule. p, W, L are computed over episodes, never over
    bars and never over zones (L-16/L-18, B-8).
  measured conditioning event == traded entry event: YES, and this is the fix that cost CF-MR-004
    its availability leg. The strategy commits at the BREACH; therefore every layer conditions on
    state known at the BREACH BAR CLOSE (bar j), not at the zone's anchor and not on a
    close-breach when the traded event is a touch. E-TOUCH, E-CLOSE and E-HORIZON are kept as
    SEPARATE event types precisely because they are different commitment states (B-4).
  effect-splitting windows non-overlapping: YES. One episode occupies [entry, entry+h). A symbol
    holds at most ONE open episode; a breach arriving while an episode is open is recorded
    SUPPRESSED and counted. Zones are non-overlapping by construction (one zone per anchor, H-bar
    window). Residual dependence handled by block bootstrap with block >= h (B-9).
```

**Flat legs** use **SPDR-014's own 5 bps deadband**, not an `r == 0` test: `|r| < 5 bps` is FLAT,
excluded from `p`, counted as `p_flat` and disclosed per cell. (An earlier draft wrote `r == 0`,
silently narrowing the parent's rule; withdrawn per QA run 1 and corrected here in the one place
that still carried it.)

---

## §4 The layer protocol (AMENDMENT-C6 — BINDING)

Identical protocol to `SPDR-019`, applied to this entry. Every stage emits the full decomposition
with block CIs, its MDE in log units, its evidence class, its `p_event`, and its episode count.
**No stage is skipped because an earlier one read flat.**

| Stage | What runs | Variants | Read |
|---|---|---|---|
| **L0** | The event entry with the **parent's** fixed exit (`open[entry+h]`), no selection, no modulation. Both MOMO and MR sides | 6 (3 event types × 2 sides) at the primary `z` | The baseline `(p, W, L, log R)` and κ. **Mandatory first** |
| **L1** | **Scale alone.** ŝ used only to set the band width `z` as a ŝ-conditioned quantity rather than a constant multiple | 3 | Δ`log R` vs L0 |
| **L2** | **State alone**, three cells: **(i)** shock (HMM HIGH/LOW at the breach bar), **(ii)** level (R-MARKOV k=4/k=12), **(iii)** both jointly | 5 | Δ`log R` per axis **and the interaction term** |
| **L3** | **Swing gate alone.** `T-GT-CUR` at the breach bar; parameters at L0 values | 2 | Δ`log R`; **plus the mandatory L-51 three-number selection check** |
| **L4** | **Capture devices, one at a time**, each run **twice** — unmodulated (fixed ATR/σ̂ multiple) and modulated (× ŝ) | ~44 | Δ`log R` per device |
| **L5** | The small combination L1–L4 justify | ≤ 4 | Term decomposition alongside any blend. **Evidence-selected; cannot substitute for phase (b)** |

**L4 device grid** is the SPDR-019 grid unchanged (dynamic target, trailing stop, holding period,
sizing), with holds bounded by the parent's frozen `h ∈ {4, 12, 24}` rather than by regime run-length
— because this object's horizon is inherited, not chosen.

**The `E-TOUCH > E-HORIZON > E-CLOSE` ordering** (≈3–4 bps crypto, ~1/5 that on cTrader, replicated
in sign — V27, evidence class `[P]`) is a **design input**: event types are reported separately and
never pooled. It is **not** an edge and carries no expectancy claim.

### 4.1 Phase (b) — the full cross

> **Phase (a) determines WHETHER phase (b) runs. It does NOT determine WHAT is in it.**

**Trigger: the operator decides, on the full phase-(a) report.** No numeric cutoff is written here
(same reasoning as §2.2 — invented thresholds are the wrong shape; INFR-016).

**What IS pre-declared, and what actually prevents the overfitting, is the SCOPE — not the
trigger.** Phase (a) may inform *whether* the operator authorises phase (b); it may never shrink
what phase (b) contains.

**Scope, fixed and independent of the (a) outcome:** the complete {L1, L2, L3} × {target, trail,
hold, sizing} cross on the same episode population, with **individually-flat layers retained on equal
footing**. **Estimand:** the interaction, `Δlog R(combined) − Σ Δlog R(individual)`.

Phase (b) requires **its own operator execution authority** and a design amendment. Not authorised
here.

---

## §5 Estimand and the primary read

Identical to `SPDR-019` §5:

```
Per episode:  r = side-signed gross open-to-open return, bps (SPDR-014's r_h object)
Per cell:     p, W, L, W_L, p_be, and  log R = log(W_L) - log((1-p)/p)   <-- PRIMARY
              identity assertion: |p*W - (1-p)*L - mean(r)| < 0.01 bps, EVERY cell
DISCLOSED REFERENCE ONLY: cost, p_be_net, net mean, distance to the cost floor
ALSO EMITTED PER CELL: p_event (a reported covariate and dose-response axis, NEVER a filter),
              event type, side arm
```

**The mirror is exact, not fitted** (slope 1, intercept 0). The fitted-slope form is refused as a
target (reflection §A / audit A1). κ is a non-tradable ceiling-relative diagnostic and multiplies
nothing.

---

## §6 Controls

Five controls, each with its own validity proof. The forms mirror `SPDR-019` §6; the populations,
priors and known bites below are **specific to this object** and are what QA traces.

```
CONTROL MIRROR-NULL (primary):
  question answered: is this cell's payoff distinguishable from the arithmetic zero line its own
    rate forces?
  population: the cell's own episodes. NOT disjoint by construction - and it does not need to be,
    because this is a POINT null (log R = 0), not a two-population comparison. The B-1
    disjointness requirement applies to matched-control designs; stated explicitly so QA does not
    read its absence as an omission.
  bite/MDE: block-bootstrap CI on log R, block >= h. Per-cell MDE in log units emitted BEFORE the
    read (SS8), together with the control's own sensitivity ladder. No adequacy cutoff is applied;
    the reader judges from the ladder.
  non-vacuity: log R is a joint function of p, W and L; the null perturbs none of them - it is an
    analytic reference value, so vacuity does not arise. What could refute it: any cell whose CI
    excludes 0.
  expected outcome if H true: log R CI-low > 0 on some cell. If H false: CI covers 0
    (arm C's SPDR-018 centre sat at log R < 0 with p 0.0007 from its own gross break-even).
  disclosure: distance in log units AND the implied bps, both reported.

CONTROL ENTRY-TIMING DERANGEMENT (within_sample_attribution - REPORT LAYER):
  question answered: is the payoff geometry a property of the BREACH's timing, or of the ambient
    return distribution at matched holding length?
  population: episodes whose entry timestamps are deranged within symbol, with hold length h and
    side preserved. DISJOINT in timing from the live series (zero fixed points).
  bite/MDE: >= 2000 seeds; plant curve at +5/+10/+20/+40 bps, reported per cell class. The control
    is declared UNUSABLE for any effect below its own plant-curve resolution.
  non-vacuity: re-timing changes which returns are realised -> moves p, W and L, the sufficient
    statistics of log R (B-6 satisfied).
  expected outcome if H true: live log R above the deranged null. If H false: inside it.
  disclosure: percentile + the null's OWN mean, sd and quantiles (P-24).
  destroy form: DERANGEMENT (zero fixed points, asserted and counted; L-28).
```

Object-specific controls and their known priors on **this** object:

```
CONTROL SIDE-DERANGEMENT (within_sample_attribution - REPORT LAYER):
  question answered: does the entry's SIDE carry information, or would random sides produce the
    same payoff geometry?
  population: the same episodes with sides deranged; DISJOINT in labelling from the live series -
    every episode's side differs from its own (zero fixed points).
  bite/MDE: >= 2000 seeds; plant curve co-designed at +5/+10/+20/+40 bps, detection rate reported
    per rung. The control is declared UNUSABLE for any effect below its own plant resolution.
  non-vacuity: deranging the side flips the sign of r, moving the mean, p, W and L - the
    sufficient statistics of log R. Not mean-preserving (B-6 satisfied).
  expected outcome if H true: live log R above the null distribution. If H false: inside it.
  disclosure: percentile + the null's OWN mean, sd and quantiles (P-24), never a bare percentile.
  destroy form: DERANGEMENT (zero fixed points, asserted and counted; L-28).
  KNOWN PRIOR ON THIS OBJECT: SPDR-018 ran it on arm C and measured live -12.221 bps at percentile
    0.0065, ~2.4 null sd below the null mean - the strongest single control result in that run. It
    establishes that this object's SIDES carry real directional information AND that it points
    against the registered direction. Stated so the read is interpreted, not rediscovered.

CONTROL AMBIENT-BASE (disclosure layer, [D]):
  question answered: what does the EVENT select, relative to unconditional bars at matched hold?
  population: matched-hold ambient episodes drawn from bars carrying NO breach in their window.
    DISJOINT from the event population by construction; disjointness asserted in code.
  bite/MDE: mean CI ~+-10 bps at the parent's n; emitted with the same ladder as every other cell.
    Reported as disclosure, never as a gate.
  non-vacuity: it substitutes a different episode population entirely - p, W and L all move.
  expected outcome if H true: the event population's log R differs from ambient. If H false: equal.
  disclosure: reported on (p, W, L, W_L) SEPARATELY, never on the mean alone.
  destroy form: N/A (a matched comparator, not a permutation).
  KNOWN PRIOR: on arm C the event selected a higher-rate, smaller-win, MORE SYMMETRIC distribution
    (rate +0.0255, W -33.7, W/L -0.124) whose net effect on the mean was ~zero because the terms
    offset. A MEAN-ONLY read called this "nothing happened" and was wrong.

CONTROL MAGNITUDE-MATCHED (M-3) - MANDATORY for any layer defined on move size:
  question answered: is the effect "the volatility state" or merely "this bar was large"?
  population: episodes NOT selected by the layer, matched on realised |decision-bar move| decile.
    DISJOINT from the selected population by construction; disjointness asserted PER DECILE.
  bite/MDE: plant curve per decile, emitted; the comparator is declared UNUSABLE in any decile
    where its own plant curve is blind.
  non-vacuity: it substitutes a different episode population at matched magnitude - p, W, L move.
  expected outcome if H true: selected log R above matched. If H false: equal.
  disclosure: MANDATORY per P-24 - the comparator's OWN mean, its null quantiles AND its plant
    curve accompany every percentile. A percentile alone is uninterpretable and is refused.
  destroy form: N/A (a matched comparator).
  KNOWN PRIOR: SPDR-018 measured `mag_high` at percentile 0.46 against this comparator on this very
    object - the "magnitude state" effect was "the bar was large", not "the volatility state".

### 6.1 Battery / eligibility / null rules (L-24 — all three clauses)

```
L-24.1 TIME-STABILITY ELIGIBILITY (F02): a seed battery prices side-randomisation only. Every
  cell additionally reports its log R computed on each of THREE CHRONOLOGICAL THIRDS of full
  TRAIN, with the sign agreement across thirds emitted. This is REQUIRED because full TRAIN is
  now the primary read (AMENDMENT-2) - promoting it removed the DESIGN/CONFIRM split that used to
  supply the stability signal, so the thirds read replaces it rather than being optional.
  It is a REPORTED quantity, never a gate.
L-24.2 EXIT-MATCHED NULLS (F04): the L4 devices are PATH-DEPENDENT, so every derangement seed is
  re-run UNDER THE SAME EXIT RULE as the live arm it is refereeing. A null that exits on the
  parent's fixed horizon cannot referee a trailing stop. Where a device's null cannot be
  exit-matched, that device's control is demoted to DISCLOSURE and labelled as such.
L-24.3 DERIVED TRIPWIRE THRESHOLDS (F06): TRIPWIRE-1's expected separation is COMPUTED from the
  realised autocorrelation of the shifted conditioning stream on TRAIN, with a CI - never
  asserted. The tripwire is HARD on DISCRIMINATION (legal vs leaky must be distinguishable), not
  on a magnitude someone picked.
```

### 6.2 Leak tripwire (HARD — blocking)

```
TRIPWIRE-1 (causal misalignment):
  form: rebuild the band width and every layer's conditioning state from bar [t+1] instead of
    [<= t], and re-run identically.
  must materially change the edge; the leaky twin's log R is expected HIGHER.
  vacuity check: the leaky width changes which zones breach and when -> it moves p, W, L, the
    sufficient statistics of log R. Non-vacuous.
  HARD: legal and leaky INDISTINGUISHABLE => causal construction unproven => emission invalid.
    Recorded as a count, never a vacuous pass (P-23/L-52).

TRIPWIRE-2 (breach-detection look-ahead):
  form: detect E-TOUCH using the breach bar's own full OHLC range including bars after j.
  must differ. HARD.
```

---

## §7 Unit pin (L-21 / P-15)

```
CONVERSION-PIN:
  divisor object: s_hat = LTF H1 Parkinson EWMA(lambda=0.94), 60 H1-bar warm-up, causal <= t-1,
                  in bps, horizon-scaled s_hat*sqrt(h). IDENTICAL object to SPDR-014's Z-VOL width
                  and SPDR-018's unit pin - reused verbatim, never redefined.
  secondary:      Wilder ATR(20) on the decision clock at the breach bar, causal <= t-1, for the
                  unmodulated L4 device arms (so "unmodulated" means a fixed ATR multiple, not a
                  fixed bps constant that would not port across symbols - L-50/P-21).
  measured value: TRAIN-median of both, per symbol and pooled, COMPUTED AT RUN ->
                  results/unit_pin.json. Never recalled, never asserted. All 25 symbols or the
                  gap is stated.
  resulting effect: every effect reported in BOTH bps and sigma units, side by side, per cell.
  cost floor:     13.1-16.1 bps partial; spread NOT charged. DISCLOSED REFERENCE only - no read
                  in this design is compared against it (AMENDMENT-C5). A sigma-unit effect is
                  NEVER compared to the floor (P-15).
```

---

## §8 Resolution statement — sensitivity across a range, not a single bar

Same derivation as `SPDR-019` §8, computed from SPDR-018's emitted cells — **with the scaling
constant taken from the FULL population, not the powered subset** (QA run 2):

```
Delta log R ~= Delta mean / ((1-p)*L);  arm C: p 0.467, L 124.5 -> (1-p)*L ~= 66.4 bps
MDE scales as k/sqrt(n).  Measured k = MDE * sqrt(n) on SPDR-018's emitted cells:

    powered subset (1,413 cells) : k = 370      <-- WRONG BASIS. Cells enter this subset
                                                    BECAUSE their MDE is small; using it is
                                                    the P-22 selection bias, committed inside
                                                    a power derivation. An earlier draft did
                                                    exactly this.
    FULL population (23,700)     : k = 948      <-- 2.56x larger
    by horizon                   : h=4 -> 569   h=12 -> 955   h=24 -> 1,384

k is HORIZON-DEPENDENT, so a single required-n table is invalid on a design whose block rule is
block >= h. Required n is computed PER HORIZON at run.
```

| Target `Δlog R` | required `n`, h=4 | h=12 | h=24 |
|---|---:|---:|---:|
| 0.15 | ~6,300 | ~17,700 | ~37,100 |
| 0.10 | ~14,200 | ~39,900 | ~83,400 |
| 0.075 | ~25,300 | ~70,800 | ~148,000 |
| 0.05 | ~57,000 | ~159,000 | ~333,000 |

*(`n ≈ (k / (Δ·66.4))²`. An earlier draft's "~21,200 at the 0.05 rung" used the powered-subset
`k` and no horizon split; it understated the requirement by roughly 6.6× at h=12.)*

**The direct check agrees with the arithmetic, and is the more convincing evidence.** In
SPDR-018's own emission the largest pooled arm-C cells (n ≈ 21k) realise **0.08–0.16 log units**,
and **0 of 18,632 arm-C cells reach 0.03**. Any prediction that this design will "approach 0.03"
is refuted by the parent's own data before it runs.

**Population, read from the parent's emission — not from its report's headline.** Counts below come
from `SPDR-014/results/zones.parquet` and `post_event.parquet` directly:

| `z` | zones | post-event rows |
|---|---:|---:|
| 1.0 *(dropped)* | 234,785 | 190,467 |
| **1.5** | **261,305** | **211,872** |
| **2.0** | **253,366** | **158,313** |
| **2.5 / 3.0** | new — computed at run; expected to continue the decline | — |

*(An earlier draft attributed the parent's whole-grid total of 749,456 zones to `z = 1.5` alone.
That was wrong; 749,456 spans all three `z` levels. Corrected here against the artifact.)*

**Removing the selectivity gate is what makes this experiment powered.** The gated draft would have
discarded most of the event population; taking every signal retains it. At `z = 1.5`, `Z-VOL`,
`h = 12`, the parent emitted ~86.8k post-event rows across event types — so a pooled cell at one
`(z, event, h, source, side)` combination lands in the **20k–45k** range depending on how the band
split is handled, which reaches `Δlog R = 0.05` and approaches 0.03.

**Full TRAIN is the primary read; DESIGN and CONFIRM are scored as verification.** This is
SPDR-018's own power lever 2, applied here for the same reason: splitting the band halves `n` on a
read that needs every episode. Both bands are still emitted and compared — the split is a stability
check, not the primary object.

```
RESOLUTION (replaces the pass/fail POWER block; operator mandate 2026-07-28):
  Every cell emits a SENSITIVITY LADDER instead of a powered/unpowered verdict. For a fixed
  ladder of candidate effect sizes, the cell reports the fraction of block-bootstrap replicates
  in which a PLANTED effect of that size would have been detected at its own realised n:

      ladder = { 0.02, 0.03, 0.05, 0.075, 0.10, 0.15 }  log units

  PLANT OPERATOR (must be stated, or the ladder is ambiguous - QA run 2):
    PRIMARY: plant delta on the residual by scaling W/L by exp(delta) with p HELD FIXED. This is
      the operator a capture policy actually acts through - exits move payoff asymmetry.
    CO-REPORT: the same delta planted through p at fixed W/L. Detection rates differ between the
      two, and BOTH are emitted per rung. Neither is privileged; the pair shows how
      operator-dependent the cell's resolution is.

  CURVE SUMMARY, replacing a single bar (three points, none canonical):
      mde50 / mde80 / mde95 = the effect size detectable in 50% / 80% / 95% of replicates,
      interpolated from the ladder.
    These are DESCRIPTIVE re-parameterisations of the same curve. They restore separability -
    cells can be counted, sorted and compared - WITHOUT any rung or rate being the admission
    bar. No cell is admitted, excluded, labelled or ranked by them.
    (QA run 2 proposed a `finest_rung_detected` field; that requires picking a privileged
    detection rate, which would reintroduce exactly the cutoff this mandate removed. Reporting
    three points of the curve achieves the same separability with no privileged value.)

  Emitted per cell:  realised n | block MDE | CI width | detection rate at each rung, per plant
                     operator | mde50/mde80/mde95 | the n required at each rung.
  No cell is flagged powered, unpowered or NOT_RESOLVABLE. A cell with coarse resolution reports
  coarse resolution, in numbers, and is still reported in full.
  MDE is always the dependence-matched BLOCK form (M-1, block >= the holding horizon); the iid
  form is companion-only and may never be presented as the cell's resolution.

  B-5 ENFORCEMENT (QA run 2 - the label was categorical and therefore countable; these restore
  that property without a threshold, and are HARD schema checks, not conventions):
    1. No `log R` value ships in ANY artifact without `ci_low`, `ci_high`, `ci_width` and
       `block_mde` present on the SAME ROW. Asserted over metrics_by_cell, layer_deltas and the
       resolution ladder alike.
    2. Any AGGREGATE statement over cells ("N of M covered the mirror") must carry the
       resolution distribution of those cells - median mde50 and the count below each rung.
       An aggregate without it is a negative-by-omission, which B-5 forbids as squarely as a
       dropped label does.
    3. The expected-resolution table (below) is PREDECLARED per stratum. Predeclaration was the
       real content of the retired POWER block and is orthogonal to the label; it is retained.
```

**What this changes and what it does not.** The conversion `Δlog R ≈ Δmean / ((1−p)·L)` and the
`n`-scaling below are **derivations** and stand unchanged — they are how resolution is computed. What
is removed is the single canonical bar that used to turn them into a verdict.

```
EXPECTED RESOLUTION, PER STRATUM (predeclared; a prediction, never a result):
  Population is artifact-grounded above. Pooled across symbols on full TRAIN:

    stratum                          expected n      expected resolution (mde50)
    Z-VOL, low z, h=4                20k-45k         ~0.09 - 0.13
    Z-VOL, low z, h=12               20k-45k         ~0.14 - 0.21
    Z-VOL, low z, h=24               20k-45k         ~0.21 - 0.31
    Z-VOL, z=3.0                     materially less coarser still
    Z-MAG / Z-MAG-SENS               223 / 876 rows at the parent's primary cell -> very coarse
    per-symbol (any stratum)         parent n ran 10-517 -> very coarse throughout
    sizing cells                     DISPERSION only; no log R resolution read at all

  STATED PLAINLY: on this population NO stratum is expected to resolve 0.05, and the finest
  expected resolution is around 0.09-0.13 at the shortest horizon. This is a PREDICTION about
  precision, not a prediction about the effect, and it is emitted so that a covering CI is read
  as "we could not see an effect this small here" rather than as "there is no effect" (B-5).
```

**Consequence, stated plainly:** like `SPDR-019`, this is a **pooled** experiment — that is where
resolution is finest. Per-symbol cells are heterogeneity disclosure, reported in full with their own
resolution attached rather than excluded.

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
| Universe | top-25 30d USD volume (AMENDMENT-U1); pin `cf-voldir-001-universe.json`; recompute + assert set equality. **Z-VOL resolves on 17 of the 25** — see the coverage row below |
| Clock | **H1 primary** (SPDR-014's own clock), **H4 co-report** |
| Sources | `Z-VOL` primary; `Z-MAG`, `Z-MAG-SENS` completeness (expected to resolve coarsely; still reported in full) |
| **Z-VOL symbol coverage** | **17 of 25 symbols.** 8 carry no `s_symbol` in the parent (ORDI, TIA, BIGTIME, 1000PEPE, SEI, WLD, PYTH, 1000RATS — empty on warm-up). Every 'pooled' figure in this design is pooled over **17**, and the effective-coverage rule (M-4) is applied to that figure, not to 25 |
| `z` | `{1.5, 2.0, 2.5, 3.0}` — 1.0 dropped (not an outlier band); 1.5 doubles as the parent-parity anchor. **No selectivity gate; every signal is taken** |
| `H` (event window) | inherited: 12 primary, parent's alternatives co-reported |
| `h` (hold) | inherited: `{4, 12, 24}` |
| Events | E-TOUCH, E-CLOSE, E-HORIZON — separate, never pooled |
| Sides | MOMO and MR both emitted; **neither assumed** |
| TRAIN fence | `analysis_start 2021-06-29T06:53Z` → `train_end 2023-12-18T00:00Z`; asserted in code |
| Primary band | **Full TRAIN** (power lever 2). DESIGN `[2021-06-29, 2023-03-01)` / CONFIRM `[2023-03-01, 2023-12-18)` both scored as **verification**, `n`-weighted |
| Global holdout | `2025-01-08T00:00Z` — **never queried** |
| cTrader | **Not in phase (a)**; separate leg under C1 if authorised; never pooled into `n` |
| Complexity | 1 inherited event module (from `SPDR-014/screen_code/`), 1 layer module, 4 device modules, 1 metrics layer, 1 control module; ≤ 8 plots |
| Cell count | phase (a): **≤ 120 cells** on full TRAIN, + the two verification bands. **Disclosed, not rationed** |

---

## §11 Golden traces (QA derives the numbers — the developer must not)

```
G1 (parent parity - the anti-drift proof):
  ETHUSDT, H1, DESIGN, Z-VOL, z=1.5, H=12, E-TOUCH, h=12. The first decided event.
  QA computes: the band width from s_hat, the anchor open, the touch bar, the breach side, the
  entry open[j+1], the exit open[entry+12], r_h in bps - and asserts these equal SPDR-014's
  published values for the same cell to the declared tolerance.

G2 (p_event is measured, and measured correctly):
  The same symbol and source at z=1.5 and at z=3.0. QA computes p_event at BOTH from the emitted
  zones and confirms (a) the z=1.5 value reproduces SPDR-014's published 0.995-1.000 for that
  cell, (b) p_event FALLS as z rises, and (c) NO code path uses p_event to filter, exclude or
  label any cell. This trace exists to prove the covariate is measured and not applied.

G3 (event-type distinctness, the B-4 guard):
  A zone that produces BOTH an E-TOUCH and a later E-CLOSE. QA confirms two DISTINCT events with
  distinct entry bars, that each conditions on ITS OWN breach bar, and that they are never merged.

G4 (suppression, the B-9 guard):
  The first breach arriving while an episode is already open. QA confirms SUPPRESSED + counted,
  and that no second episode opens.

G5 (the identity, and the primary read):
  The L0 pooled H1 CONFIRM E-TOUCH MOMO cell. QA computes p, W, L from the emitted episode rows,
  asserts |p*W - (1-p)*L - mean| < 0.01 bps, then recomputes log R = log(W/L) - log((1-p)/p) and
  asserts it equals the emitted value exactly.

G6 (the mirror null is the exact one):
  The same cell. QA asserts the emitted null reference is 0 for log R at SLOPE 1, and that NO
  fitted-slope residual appears anywhere in the emission (audit A1, non-repeatable by construction).

G7 (leak discrimination):
  The G1 rows under TRIPWIRE-1's leaky twin; QA confirms a material difference and that the legal
  variant is the one emitted.
```

---

## §12 Integrity checklist (code-asserted; SPDR stage-2 self-check)

| Check | Assertion |
|---|---|
| **Check count** | the self-check asserts the **expected NUMBER** of HARD checks and reconciles them **by name** against this table (P-23 / L-52) |
| TRAIN fence | `max(exit_ts) < 2023-12-18T00:00Z`; zero rows at or after it |
| Holdout | zero queries `>= 2025-01-08` |
| Causality | band width `≤ t`; anchor `open[t+1]`; breach entry `open[j+1]`; exit `open[entry+h]`; every layer's state at the **breach bar**; TRIPWIRE-1 |
| Breach detection | no post-`j` information used to detect the event at `j`; TRIPWIRE-2 |
| **Parent parity** | reproduces SPDR-014's published cells at `z=1.5` on the parent's band, to a declared tolerance — **the proof the object was not re-specified** |
| **`p_event` emitted** | on every cell, per event type, as a **reported covariate**. Asserted **not** to filter, gate or label any cell (INFR-016 / L-32) |
| Universe pin | top-25 recompute == pin file, set equality |
| **Identity reconstruction** | `\|p·W − (1−p)·L − mean\| < 0.01 bps` on **every** cell |
| **`log R` definition** | asserted equal to `log(W/L) − log((1−p)/p)` with **slope 1**; a fitted-slope residual anywhere is a **hard failure** |
| **Cost isolation** | no cost term in any estimand, threshold, band or comparison; `p_be_net` present, flagged `DISCLOSURE_ONLY` (AMENDMENT-C5) |
| **MDE column** | the reported resolution column is the **block** MDE in log units; iid is companion-only (M-1) |
| **`log R` never unaccompanied** | HARD schema check: no `log R` ships in **any** artifact without `ci_low`, `ci_high`, `ci_width` and `block_mde` on the **same row** — asserted over `metrics_by_cell`, `layer_deltas` and the resolution ladder alike (B-5 enforcement, QA run 2) |
| **Ladder plant operator** | both plant operators (via `W/L` at fixed `p`; via `p` at fixed `W/L`) computed and emitted per rung; neither omitted |
| **No adequacy flag** | asserted that **no** `powered` / `unpowered` / `at_target` / `NOT_RESOLVABLE` column is emitted anywhere, and that no single canonical MDE threshold appears in code (operator mandate 2026-07-28) |
| **Ladder emitted** | the sensitivity ladder is present on **every** cell, with its detection rates and required-`n` values |
| **Span disclosure** | exact-span subset and span distribution per horizon cell (M-2) |
| Episode exclusivity | one open episode per symbol; suppression count emitted |
| Derangements | fixed-point count == 0, measured and reported (L-28) |
| Determinism | runs **unconditionally** whenever `--jobs > 1`, independent of `--resume`; parallel bit-identical to sequential (P-23) |
| Golden traces | G1–G7 pass |
| No local accounting | availability/residual bps, not booked P&L; no `xen.adjudication` mimicry |
| Code hash | sha256 of `screen_code/` pinned into `results/integrity_selfcheck.json` |

```
HARD (block execution / invalidate emission):
  check-count reconciliation, TRIPWIRE-1, TRIPWIRE-2, TRAIN fence, holdout, causality, breach
  detection, parent parity, universe pin, identity reconstruction, log R definition, cost
  isolation, derangement fixed-point count, golden traces, determinism.
INFORMATIVE (operator judges, no auto-verdict):
  every effect size, control percentile, collapse fraction, band label, p_event, dose-response,
  kappa, cost overlay, heterogeneity statistic, event-type ordering.
```

Every check depends on an **emitted artifact** — missing or empty is a **failure**, never a vacuous
pass (P-23). No required check lives in a manual post-step (L-52).

---

## §13 What this design refuses

- **Any cost term in any estimand, threshold or comparison** (AMENDMENT-C5). Cost is disclosure.
- **Any expectancy, tradability, deployability or cost-complete claim** (AMENDMENT-C2, unchanged).
- **The fitted-slope residual as a target** (audit A1).
- **Scoring any capture variant against zero P&L** rather than against the mirror.
- **Any selectivity gate, breach-rate cutoff, or cell exclusion on `p_event`** — removed by operator directive 2026-07-28 (§2.2). `p_event` is measured and reported, never applied.
- **Re-litigating the DESIGN→CONFIRM sign flip** — discharged by SPDR-018 C7 (§2.3).
- **Pooling event types with each other**, or pooling MOMO with MR.
- **Assuming a side.** Both arms are emitted; the registered direction is not privileged.
- **Any rule, band or gate phrased against `p > 0.5`** — the reference is `p_be`.
- **Researching direction prediction**: no new entry model, no side-selection rule tuned to lift `p`.
- **Combining layers before characterising them individually** (AMENDMENT-C6).
- **Pruning phase (b) to phase (a)'s winners.**
- **Reading a coarse-resolution cell as a negative** (B-5), or reading a CI that covers the mirror as a refutation.
- **Any aggregate statement over cells** ("N of M covered the mirror") **without the resolution distribution of those cells** — median `mde50` and the count below each rung. An aggregate without it is a negative-by-omission, which B-5 forbids exactly as it forbids a dropped label (QA run 2).
- **Emitting any `powered` / `unpowered` / `NOT_RESOLVABLE` flag, or any single canonical adequacy threshold** — retired by operator mandate 2026-07-28; resolution is reported as a ladder and adequacy is the reader's judgement.
- **A per-symbol `log R` conclusion carried without its resolution ladder** — per-symbol cells resolve coarsely (§8) and are heterogeneity disclosure.
- **A blended score without its term-level decomposition**; **a sizing cell reported as expectancy**.
- Any family status change; any XENA; any TEST or holdout contact.

---

## §14 Amendment ledger

```
No amendments to this design. Registered 2026-07-28.
running count: 0 looser / 0 tighter / 0 neutral

AMENDMENT-1: remove the p_event <= 0.60 selectivity gate entirely; z grid set to
  {1.5, 2.0, 2.5, 3.0} (1.0 dropped as not an outlier band); every signal taken; p_event retained
  as an emitted covariate and dose-response axis, never a filter.
  - DIRECTION: LOOSER (no cell is excluded; the population grows)
  - Operator directive 2026-07-28. Rationale in 2.2: the threshold was invented, was the wrong
    SHAPE for this programme (INFR-016/L-32 retired arbitrary value-gates), and contradicted the
    purpose of a capture-geometry experiment, which is not to find better-selecting signals.
AMENDMENT-2: full TRAIN becomes the primary read; DESIGN/CONFIRM scored as verification.
  - DIRECTION: LOOSER (more n per cell; the band split stops halving the primary read)
  - SPDR-018 power lever 2, applied for power.
AMENDMENT-3: restore SPDR-014's UNDECIDED-side rule and its 5 bps flat deadband, both of which an
  earlier draft silently replaced.
  - DIRECTION: NEUTRAL (parent fidelity restored)

AMENDMENT-4: retire the powered/unpowered adequacy label and the +-0.03 / 0.07 magnitude
  thresholds; report a SENSITIVITY LADDER per cell and define bands by the CI's relation to the
  mirror instead.
  - DIRECTION: NEUTRAL (a boolean is replaced by the numbers behind it; every effect is bound to
    its own MDE and CI width on the same row)
  - Operator mandate 2026-07-28. Same rationale as SPDR-019 AMENDMENT-6.

AMENDMENT-5: correct the required-n scaling constant from the powered-subset basis (k=370) to
  the full-population, horizon-split basis (k = 569 / 955 / 1384 at h = 4 / 12 / 24); add the
  per-stratum predeclared resolution table; disclose Z-VOL's 17-of-25 symbol coverage.
  - DIRECTION: TIGHTER (the requirement rises ~6.6x at h=12; no cell's status improves)
  - QA run 2. The old basis was the P-22 selection bias committed inside a power derivation.
AMENDMENT-6: fill the three thin control blocks; add the three L-24 clauses (thirds stability,
  exit-matched nulls, derived tripwire threshold); declare the parent-parity tolerance
  numerically (|d| <= 1e-9); restore the 5 bps deadband and the UNDECIDED rule in the grammar
  table and SS3; name the mechanism for R > 1 in SS1.1 with its prior-against stated.
  - DIRECTION: TIGHTER (adds required checks and a falsifiable mechanism claim)
  - QA runs 1 and 2.

running count: 2 looser / 2 tighter / 2 neutral
NOTE: a 2-looser streak is disclosed here per L-23. Neither loosening touches an integrity check,
a fence, a causality rule or a claim boundary; both act ONLY on population size, and the second is
a power lever SPDR-018 already used. No band label, control or refusal is relaxed.
```

Checkpoint/family amendments in force: **U1** (NEUTRAL), **S1** (NEUTRAL), **C1** (NEUTRAL),
**C2** (TIGHTER), **C5** (NARROWING), **C6** (TIGHTER).

---

## §15 Artifacts

| Path | Content |
|---|---|
| `screen_code/` | inherited SPDR-014 event module, layer module, 4 device modules, metrics layer, control module |
| `results/zones.parquet` | every zone: anchor, width, source, `z`, `H`, breach outcome |
| `results/episodes.parquet` | every episode: event type, side arm, breach bar, entry ts/price, exit ts/price/reason, `r` bps, layer tags |
| `results/metrics_by_cell.parquet` | per cell: `p`,`W`,`L`,`W_L`,`p_be`,**`log R`**, block + iid MDE in log units, CIs, CI width, ladder detection rates, band label (CI-relative), evidence class, **`p_event`** (covariate, never a filter), `p_flat`, κ, `n`, homogeneity, cost overlay flagged `DISCLOSURE_ONLY` |
| `results/layer_deltas.parquet` | Δ`log R` per stage vs L0, with the L2 interaction term |
| `results/parent_parity.json` | reproduction of SPDR-014's published cells + tolerance |
| `results/controls.json` | all controls: percentiles, **null means and quantiles**, **plant curves** (P-24), derangement fixed-point counts |
| `results/selection_check.json` | the L-51 three-number check on every powered subset (P-22) |
| `results/unit_pin.json` | measured σ̂ and ATR20 medians (computed, not asserted) |
| `results/resolution_ladder.parquet` | per cell: realised n, block MDE, CI width, detection rate at each rung **per plant operator**, `mde50`/`mde80`/`mde95`, and the n required at each rung. **No adequacy flag** |
| `results/golden_traces.json` | G1–G7 |
| `results/integrity_selfcheck.json` | check-count reconciliation, fences, causality, parity, pin, identity, `log R` definition, cost isolation, code sha256 |
| `screen.md` | neutral quantification (subordinate) |
| `analysis.md` | **fresh-context analyst — binding read** (SPDR stage 5, mandatory) |
