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

**This remains a grid extension, not an estimand substitution.** `z` is a registered parameter of
the 014 object; the object, its anchor, its event types and its residual definition are untouched.
SPDR-014's frozen grid was `{1.0, 1.5, 2.0}`; this design **drops 1.0 and adds 2.5 and 3.0**, which
is disclosed here, in the cell count (§10) and in the amendment ledger (§14).

**Parent parity is asserted:** at `z = 1.5, H = 12, h = 12, E-TOUCH, Z-VOL, DESIGN`, this screen must
reproduce SPDR-014's published per-symbol cells to a **declared numeric tolerance** (stated in
`results/parent_parity.json`, not left implicit). That is the proof the object was not silently
re-specified.

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

**Flat legs** (`r == 0`) are excluded from `p`, counted as `p_flat`, and disclosed per cell.

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
  KNOWN NON-VACUOUS ON THIS OBJECT: SPDR-018 ran it on arm C and measured live -12.221 bps at
  percentile 0.0065, ~2.4 null sd below the null mean - the strongest single control result in
  that run. It establishes that this object's SIDES carry real directional information AND that
  it points against the registered direction. That prior is stated here so the read is
  interpreted, not rediscovered.
  destroy form: DERANGEMENT (zero fixed points, counted; L-28). >= 2000 seeds. Plant curve
  co-designed at +5/+10/+20/+40 bps.
  disclosure: percentile + the null's OWN mean, sd and quantiles (P-24).

CONTROL AMBIENT-BASE (disclosure layer, [D]):
  question answered: what does the EVENT select, relative to unconditional bars at matched hold?
  population: matched-hold ambient episodes, DISJOINT from the event population.
  KNOWN PRIOR: on arm C the event selected a higher-rate, smaller-win, MORE SYMMETRIC
  distribution (rate +0.0255, W -33.7, W/L -0.124) whose net effect on the mean was ~zero because
  the terms offset. A MEAN-ONLY read called this "nothing happened" and was wrong. This control is
  therefore emitted on (p, W, L, W_L) SEPARATELY, never on the mean alone.
  bite/MDE: mean CI ~+-10 bps on the parent's n; reported as disclosure, never as a gate.

CONTROL MAGNITUDE-MATCHED (M-3) - MANDATORY, and it has bitten here before:
  SPDR-018 measured `mag_high` at percentile 0.46 against this comparator - i.e. the "magnitude
  state" effect on this very object was "the bar was large", not "the volatility state". Any L1/L3
  layer defined on move size MUST carry it, with the comparator's own mean, null quantiles and
  plant curve emitted alongside every percentile (P-24). A percentile alone is refused.
```

### 6.1 Leak tripwire (HARD — blocking)

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

Same derivation as `SPDR-019` §8, computed from SPDR-018's emitted cells:

```
Delta log R ~= Delta mean / ((1-p)*L);  arm C: p 0.467, L 124.5 -> (1-p)*L ~= 66.4 bps
=> a cell resolves Delta log R ~= its block MDE in bps / 66.4
```

| Target `Δlog R` | Required mean-MDE | Required episodes (from arm C's MDE-vs-n scaling) |
|---|---:|---:|
| 0.07 | 4.6 bps | ~10,800 |
| 0.05 | 3.3 bps | ~21,200 |
| 0.03 | 2.0 bps | ~58,800 |

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
  Population is artifact-grounded above. Pooled across 25 symbols on full TRAIN, a low-z Z-VOL
  cell is expected in the 20k-45k range -> resolution around the 0.05 rung, approaching 0.03.
  The z = 3.0 tail, the Z-MAG and Z-MAG-SENS sources (223 and 876 rows at the parent's primary
  cell) and every per-symbol cell (parent n ran 10-517) land at the coarse end of the ladder.
  Sizing cells are reported on DISPERSION only and carry no log R resolution read at all.
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
| Universe | top-25 30d USD volume (AMENDMENT-U1); pin `cf-voldir-001-universe.json`; recompute + assert set equality |
| Clock | **H1 primary** (SPDR-014's own clock), **H4 co-report** |
| Sources | `Z-VOL` primary; `Z-MAG`, `Z-MAG-SENS` completeness (expected to resolve coarsely; still reported in full) |
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

running count: 2 looser / 0 tighter / 2 neutral
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
| `results/resolution_ladder.parquet` | per cell: realised n, block MDE, CI width, detection rate at each ladder rung, and the n required at each rung. **No adequacy flag** |
| `results/golden_traces.json` | G1–G7 |
| `results/integrity_selfcheck.json` | check-count reconciliation, fences, causality, parity, pin, identity, `log R` definition, cost isolation, code sha256 |
| `screen.md` | neutral quantification (subordinate) |
| `analysis.md` | **fresh-context analyst — binding read** (SPDR stage 5, mandatory) |
