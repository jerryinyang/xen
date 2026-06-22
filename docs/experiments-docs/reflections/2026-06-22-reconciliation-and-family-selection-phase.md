# Reconciliation & Proposed Family-Selection Phase (2026-06-22)

**Status:** Reflective synthesis + a proposed next-phase shape. **Predeclares nothing binding, reads no data,
touches no holdout, spends no slot or counted read.** The actual screens, controls, and pass/kill thresholds
are frozen later at the phase's own G0/D0. This document merges two independent analyses into one starting
point for the next chat, and records the operator's directive on how to proceed.

**Reconciles:**
- [`2026-06-22-next-family-recommendation.md`](2026-06-22-next-family-recommendation.md) — the assistant's recommendation (lead: *magnitude / non-directional* reframe; runner-up: cross-sectional).
- [`2026-06-22-cold-autopsy-three-families-next-family.md`](2026-06-22-cold-autopsy-three-families-next-family.md) — the independent cold review (lead: *cross-sectional*; runner-up: order-flow; red-teams the older synthesis).
- Background: [`2026-06-19-two-family-retrospective-reflections.md`](2026-06-19-two-family-retrospective-reflections.md); [Phase 018 retrospective](../checkpoints/2026-06-20-018-capgeo-exit-geometry/retrospective.md).

---

## 1. What both analyses agree on (the converged core)

Independently derived, both land on the same diagnosis and the same method — strong corroboration:

- **Invariant failure mode:** single-instrument, event-driven, price-geometry entries carry **no
  signal-conditional favourable price excursion beyond a matched random control** (availability ≈ random).
  Established twice with matched-control designs: EXP-047 (AVWAP event MFE ≈ control MFE on every domain) and
  EXP-081 (harami `MFE_med` Δ −0.140, real>random 17/46; AVWAP +0.061, 28/46 — coin-flip).
- **The downstream stack is exhausted** on these entries: exit/capture geometry (EXP-084 exit-invariant, 0/11
  arms positive OOS CI_low), costs, conditioning, anchors, and **sizing** (ATR-normalised returns are already
  fixed-risk; sizing is a near-global rescale — it amplifies an edge, cannot create one).
- **Method for what's next:** run the **availability screen *first*** — the cheap, TRAIN-only, 0-read
  Δ-over-random read (an EXP-081 clone) — *before* committing a slot to any family. The programme's historical
  mistake was measuring availability *last*, after building a whole family around a pattern.

## 2. Red-teams adopted from the cold autopsy (binding corrections to the synthesis)

The autopsy is the better document and these three corrections are adopted wholesale:

1. **"Both families had a real edge" is a soft-pedal.** On the fresh 5-year disjoint data the harami's
   separation from random is **≈ chance (25/46 cells; median +0.135 vs random +0.085)** with favourable
   availability *below* random. The old-data 85/99 (EXP-060B) was a different dataset *and* a different exit
   geometry, partly 4h-underpowered. Honest read: *a real edge on old data under one geometry that is
   marginal-to-absent on fresh data and reverses OOS* — which pushes the decisive call further toward "no
   effect" than the prose admitted.
2. **The whole "nothing works" verdict rests on exactly two OOS reads** — EXP-032 (n=27, INCONCLUSIVE) and
   EXP-084 (n=151, NOT_CONFIRM). Each is clean, but two reads is a thin empirical floor; keep this caveat
   visible in any forward claim.
3. **The ruled-out vs never-tested split is the right frame:** the programme exhaustively killed the
   *downstream stack* on two price-pattern entries and has **never varied the entry's information source.**

## 3. The correction the autopsy still needed (directional vs magnitude availability)

The autopsy frames the invariant as "availability ≈ random," but every metric establishing it — `MFE_med`,
outcome-median — is **directional / favourable-side.** What is proven with power is *directional favourable
availability ≈ random.* It never separately screens the orthogonal axis: **non-directional magnitude** — does
the signal predict a *large move in either direction* (total realized range / |move|), independent of sign?

This is a genuine untested cell — but the prior on it is **low, and the hint is tail-only, not typical-range.**
The evidence has to be read precisely (recalibration adopted from the review's point 1):

- **Typical range is NOT elevated.** EXP-081 already measured the adverse side: `MAE_q90` Δ-over-random is
  **−0.719 ATR, real>random in only 9/46 cells** (harami; AVWAP −0.554, 18/46). Both the favourable (`MFE_med`,
  17/46) and the typical-adverse excursions sit *below* random, so *typical* total realized range is not
  elevated either. A naive `MFE+MAE > random` endpoint will likely null out.
- **The only positive-magnitude evidence is the rare catastrophic tail,** and it is modest: `tailmass` 0.0526
  vs random 0.0437 (31/46 cells). The EXP-074 `msofar_atr` q05 separation at **rank-biserial 0.68–0.80** is
  real but is *not* an apples-to-apples "strongest effect in the programme": it is a **within-sample,
  adverse-side, conditional** separation of the q05 loss tail *inside* the harami population — a different
  baseline from the 17/46 and 28/46 *cells-beat-random* counts. It establishes "exhaustion predicts adverse
  blow-ups in harami entries," **not** "compression predicts large two-sided range over random." Nobody has
  computed that latter number; Screen M exists to go get it, with the prior set **low**.

So the correct reading is the *opposite* of "the data is screaming magnitude": the data says typical range is
flat and only the rare adverse tail carries structure. Screen M is worth running because it closes the
single-series magnitude cell for one experiment's cost — **not** because the evidence already points there.

**Harvest model (the autopsy's tradability point, made binding — review point 3).** What EXP-074 says is
predictable is *your own adverse tail*. Harvesting it means abandoning the harami-as-directional-entry and using
high-exhaustion moments as a **volatility-timing trigger for a two-sided bracket** (straddle/breakout) — a
larger conceptual shift than swapping an endpoint column: the exit, the P&L accounting, and the
separability/referee machinery all change, and the harvestable part is **rare and adversely-timed.** Therefore
any magnitude "pass" must clear a **two-sided cost** on a move whose predictable component is tail-concentrated.
Screen M must (i) report a **magnitude-budget** check (is the predictable range large enough to clear two-sided
cost?) and (ii) **separate typical-range structure from tail/bimodality structure**, never pool them into one
`|move|` number (EXP-081 shows the pooled number is null; the signal, if any, is tail-only). A magnitude "pass"
is **not** a tradable edge — treating it as one would re-run the gross→net trap that ate AVWAP.

## 4. The reconciled framing: the availability 2×2

The next decision is not "magnitude *or* cross-sectional." It's a 2×2 over **{information source} × {target}**,
of which the programme has tested exactly one cell — and found it dead:

```
                    DIRECTIONAL target            MAGNITUDE / range target
single-series   │  TESTED → dead (EXP-047/081/084) │  UNTESTED — low prior; typical range flat
                │                                   │   (EXP-081 MAE_q90 9/46), tail-only hint
cross-sectional │  UNTESTED (autopsy's lead bet)    │  UNTESTED
```

All three remaining cells are untested, and **all three are cheaply screenable with the same EXP-081-clone
availability read** (0 slots, 0 OOS reads, TRAIN-only). So the disciplined move is to *screen, then commit* —
let the Δ-over-random numbers select the family rather than picking blind.

**The selection is a cascade, and the high-stakes decision is the in/out kill gate, not the winner-pick
(review point 2, reframed).** Under rank-then-explore-all (§5), the metric only sets *order*; the multiplicity
risk lives at the threshold that admits an axis to the explore-list at all. Run three axes × many cells and a
**pure-noise** axis can clear a single-axis-calibrated band *somewhere* (cross-sectional ranking over 16
instruments manufactures the most cells, so it is the worst offender). Therefore the **admission gate** must be
calibrated against a **multiplicity-adjusted / permuted-axis null at the realized cell count** (the EXP-077 /
`m_cell` calibration pattern), not the single-axis ≈17/46–28/46 band. The ordering metric among admitted
survivors is the lower-stakes part. This is non-negotiable: a selection phase whose method is "screen many,
keep the best" must inherit the programme's own file-drawer/multiplicity discipline into the screening method
itself, or it re-imports the exact selection bias 16 phases were spent avoiding.

## 5. Reconciled decision (operator-directed)

**The next phase is a family-agnostic, idea-screening, family-selection phase** — its deliverable is *a decision
about which family to open next (and in what order)*, backed by cheap Δ-over-random availability numbers,
**not** a tradable strategy. This directly institutionalises the fix for the programme's historical "measure
availability last" mistake: here, availability is the **selection gate**, measured first, family-agnostically.

**Operator directive on sequencing and emphasis (revised 2026-06-22 — supersedes the earlier "full focus on
cross-sectional regardless"):** the phase is **genuinely numbers-driven**, not a pre-committed bet on any one
axis.
1. **The Δ-over-random metric sets exploration order.** Whichever admitted axis scores best on the frozen
   availability metric is opened first (at its own future G0/D0); the rest follow best-first.
2. **Every axis that clears the (multiplicity-adjusted) admission gate is *eventually* explored** — nothing
   admitted is discarded. Selection orders the queue; it does not prune it. The admission gate (§4, review
   point 2) is the decision that matters; the ranking only sequences scarce TEST reads, which still matters
   because the first family opened gets the freshest reads and could end the search if it confirms.
3. The governing principle: **"run the availability screens before committing a single slot, gate admission on
   a multiplicity-adjusted null, and let the Δ-over-random numbers choose the order — explore every admitted
   family eventually, best-first."**

(Operator note: cross-sectional remains the *a-priori favourite* on mechanism grounds — cross-asset relative
strength is a demonstrably non-random anomaly elsewhere — but it must *earn* first place on the screen like any
other axis. Screen M is run not because magnitude is favoured but because it closes the single-series quadrant
for a tenth of the work; if it lights up against its low prior, that changes the order honestly.)

## 6. The screens (concrete; each is an EXP-081 clone, TRAIN-only, 0 slots, 0 reads)

Each screen: take a candidate *information axis*, generate its conditioned entries, and compute per-cell
paired Δ-over-**matched within-substrate/within-instrument random control** on the chosen availability endpoint,
on the TRAIN sub-split only. Report the per-cell Δ and the cells-beat-random count — the EXP-081 Finding-3
table re-pointed at the new axis.

**Two pre-declared thresholds, frozen before any screen runs (inverted-inference):**
- **Per-cell null band** — the established random-looking baseline (≈17/46–28/46 cells-beat-random), used for
  descriptive per-cell reporting only.
- **Admission gate (binding) — a multiplicity-adjusted / permuted-axis null at the realized cell count.** An
  axis is admitted to the explore-list only if its cells-beat-random (or Δ aggregate) exceeds what a
  *label-permuted / shuffled-axis* control produces across the **same number of cells** at a frozen FWER (the
  EXP-077 / `m_cell` calibration pattern). This is the leg that prevents a noise axis (esp. cross-sectional,
  which manufactures many cells) from being admitted on a lucky cell. Calibrated before outcome contact;
  routing shown invariant across a pre-registered sensitivity band.

- **Screen M — magnitude / non-directional (closes the single-series quadrant; cheapest, run first).**
  Endpoint must **separate two distinct magnitude reads, never pooled** (review point 1; EXP-081 shows the
  pooled `|move|` is null): **(i) typical-range** — forward realized range / symmetric excursion
  `max(MFE,MAE)` or `MFE+MAE` (ATR-normalised) vs matched random; and **(ii) tail/bimodality** — `tailmass`,
  `q05`, dip-test, and a direct re-examination of EXP-074's `msofar_atr` adverse-tail separation as
  *predictable magnitude* (the only place the prior is non-trivial). Conditioned on existing compression
  primitives (HA-harami inside-bar; a clean NR/inside-bar primitive) vs matched random. **Plus the
  magnitude-budget check** (does the predictable range clear a **two-sided** cost? — the harvest model in §3).
  **Kill** if *both* typical-range and tail reads fall in the null band (Δ ≤ 0 or beats random in ≤ half of
  cells, ≈17/46–28/46) → magnitude on single-series price geometry is exonerated too; the single-series row of
  the 2×2 is fully dead. **A "pass" on the tail read alone is a *long-vol* finding, not a tradable edge** —
  it routes to a properly-scoped volatility-expansion family at its own G0/D0 under the §3 harvest model, never
  to a directional claim.
- **Screen X — cross-sectional relative strength (the lead bet; the main thrust).**
  Endpoint: signal-conditional favourable excursion of entries conditioned on **basket-relative
  momentum/divergence rank across the 16-instrument universe** vs matched within-instrument random control.
  Constructible from the existing 16×1m dataset with **zero new collection.** **Kill** if it reproduces the
  ≈-random pattern → cross-sectional price information is exonerated too. **Pass** → open the cross-sectional
  family at its own G0/D0.
- **Screen F — order-flow / liquidity imbalance (optional runner-up).**
  Endpoint: availability at tick-volume / volume-at-price imbalance extremes vs matched random. **Lower
  priority** (EXP-046 found tick-volume-weighted construction inert once; tick volume is broker-dependent) but
  brings genuinely orthogonal *flow* information. Run only if M and X both warrant a third comparison.

## 7. Discipline & what this phase is NOT

- **Family-agnostic:** it compares candidate *information axes / targets*, not candidates within a family. The
  output is a family-selection recommendation, not a tradability or edge claim.
- **0 candidate slots, 0 counted TEST reads, TRAIN-only, holdout never touched.** These are descriptive
  availability disclosures (the EXP-080/081 readiness/characterization convention) — no strategy estimand, no
  stratum-specific binding inference — so they cost **0 reads** by construction. Per-cell / per-stratum
  reporting, never pooled-as-verdict (LESSON-001).
- **Not a candidate family** (like Phase 017 was a qualifier-validation phase, not a CF-XXX). It *selects* the
  next family; it does not screen a candidate within one.
- **Availability-first, pre-declared thresholds:** the kill/pass band is frozen before the screens run
  (inverted-inference), so a near-miss cannot be argued up after the fact.

## 8. Confidence, terminal branches, what falsifies

- **High confidence:** single-series *directional* price-pattern entries are dead (availability ≈ random,
  two matched-control designs); exit/capture geometry is not the binding lever (EXP-084 exit-invariance); the
  one well-powered OOS read is a true negative.
- **Explicitly a bet, not a finding:** that cross-sectional *or* magnitude *will* beat random is a **prior**,
  not yet evidence — the screens exist precisely to kill the wrong bet cheaply. The data tells us decisively
  what does *not* work far more strongly than what *will*.
- **Terminal branch (state it now, honestly):** if **all** screens reproduce ≈-random (single-series
  magnitude, cross-sectional, and flow all in the null band), then *price-derived information — single or
  relational — is exhausted on this dataset*, and the real frontier is **non-price data acquisition** (order
  book, cross-asset, fundamentals), which is a data decision, not a modelling one. The screens are designed so
  the programme reaches that conclusion, if true, having spent **zero** reads and zero slots.
- **The one thing the evidence already forecloses:** another entry whose distinguishing feature is its
  single-instrument price-geometry *pattern* on a *directional* target. That cell is dead, twice over, with
  the holdout still sealed to prove it when something finally clears the availability screen.

## 9. Next action (for the new chat)

Open the family-selection screening phase at a G0/D0 that: (i) fixes the matched-random control and the
per-cell Δ-over-random endpoints for Screens M and X (and optionally F), with Screen M's typical-range and
tail/bimodality reads kept **separate**; (ii) pre-declares **both** thresholds — the descriptive per-cell null
band *and* the binding **multiplicity-adjusted admission gate** (permuted-axis null at the realized cell
count); (iii) confirms the 0-slot / 0-read / TRAIN-only / holdout-sealed disclosure status in the registry and
ledger; (iv) is **numbers-driven**: the Δ-over-random metric sets exploration order over all admitted axes
(best-first), Screen M run first only because it is the cheapest way to close the single-series quadrant — not
a pre-commitment. First concrete experiment = Screen M as an EXP-081 clone with the endpoint swapped from
favourable `MFE_med` to the **split** non-directional range + tail reads, plus the magnitude-budget check.
