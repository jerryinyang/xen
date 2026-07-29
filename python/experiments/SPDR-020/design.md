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
  test     = block-bootstrap CI on log R. H1 inherits SPDR-018's complete {1,3,7}-day rule
             verbatim; H4 uses the horizon-scaled {4,12,28}-day co-report rule (§8.1).
             Dependence-matched block MDE (M-1) in LOG UNITS per cell; realised EFFECTIVE sample
             size and realised c emitted per cell alongside n.
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

**Pre-registered expectation — all five of reflection §5.6's predictions, carried in full.** A
prediction made before the run is the strongest B-5 protection available and it costs nothing, so
none is dropped:

1. **ŝ-scaling every capture parameter leaves `log R` unchanged.** If a ŝ-scaled policy shifts the
   residual, the mirror is not the whole story — and that is a finding. This is the direct
   predeclared expectation for the **L1** layer.
2. **Selection on `T-GT-CUR` raises `W` and `L` together**, with `W/L` moving less than ~0.3 (the C5
   signature, V21). A materially larger `W/L` move under selection means selection is doing
   something the C5 read did not capture. Predeclared for **L3**.
3. **A hold of ~`E[run]` sits closer to `W/L` ≈ 1 and `p` ≈ 0.5 than a short hold does** (V26
   extrapolated). If not, the hold axis is not behaving like the measured dose-response.
   Predeclared for **L4**'s holding-period device.
4. **Shock-gated and level-gated selections are near-independent** (51–62% agreement, V9/V10), so
   their effects on the identity should be close to **additive**. Strong interaction is new
   information. Predeclared for **L2**'s interaction term.
5. **On cTrader every magnitude lands at roughly σ̂-ratio scale** (~1/5.6 of crypto, V28). A cTrader
   result that does not scale that way is either a portability defect (P-21) or a genuine
   asset-class difference, and the check distinguishes them. Applies only if the AMENDMENT-C1
   replication leg is authorised; it is not part of phase (a).

A result contrary to any of these is a finding; a result matching them is the expected outcome.

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
| **The parent's own stop, and why it is absent here** | SPDR-014's signed policies exit at `min(h, stop)` with a stop at adverse excursion ≥ **1.5 × ATR(14) Wilder H1** at entry−1 (its `design.md:246`). **This design's P&L object is the UNSTOPPED `r_h`**, the parent's own residual column, so no ATR stop is inherited and §7's ban on Wilder ATR as an exit boundary stands. Parity (§2.2) is asserted only on `mean_r_h`, `p_momo`, `p_mr` and `n_decided`, which are computed from `r_h` and are therefore stop-independent — the parent emits the same `r_h` for an event under every policy arm. Stated because the parent's stop governs a large share of its signed episodes, and silence would read as an oversight |
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
never as a filter. Nothing filters, excludes, weights, labels or ranks a row or cell on
`p_event`.** It is a *dose-response axis*: breach rate varies across the `z` grid, and
reading `log R` against it is strictly more informative than a pass/fail line would have been. The
checkpoint's binding carry-forward requirement — *the band's selectivity must be visible rather than
assumed* — is satisfied by measuring and reporting it, which is what SPDR-014 failed to do.

**Reconciliation with registered `HYP-D7`.** The operator clarified the registry and checkpoint
wording on 2026-07-29: band selectivity is measured and reported on every cell; `p_event` is a
covariate and never an eligibility filter. This matches the 2026-07-28 no-gate directive and the
checkpoint's actual defect — hidden selectivity — without optimising the entry.

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

### 2.2a Exit fill resolution for the L4 devices (QA run 6)

The parent exits at `open[entry+h]` and needs no fill rule. **This design adds a profit target and
a trailing stop, which are path-dependent and therefore do need one**, and the two candidate
parents disagree — SPDR-014 fills at the next bar open after a touch, SPDR-019 fills on the M1
stream at the level. A design that leaves this open makes the developer choose the exit price,
which is the most consequential single number in a payoff-geometry experiment.

**This design inherits SPDR-019 §2's rule, with the time exit re-expressed on this object's own
inherited `h`** (bars from entry, not hours from fill), so the two experiments' capture devices are
the same object and their `log R` values are comparable:

| Exit | Fill |
|---|---|
| **Profit target** | first **M1** bar trading through the target → fill **at the target price**; if an M1 bar **opens beyond** it, fill at that open |
| **Trailing stop** | the trail ratchets **once per M1 bar, on that bar's close**, never intra-bar; it triggers on the first M1 bar trading through the trail level, filling **at the trail level** (or at the open if gapped through) |
| **Time exit** | at the **open of the first H1/H4 bar at or after `entry + h`** — the parent's own open-to-open exit, unchanged |
| **Precedence inside one M1 bar** | if target and trail are both reachable, the **adverse one fills**. Intrabar ordering is unknowable at M1 resolution, so the pessimistic branch is taken every time |
| **Precedence with the time exit** | a target or trail triggering **at or before** the time-exit bar's open takes precedence |

**The entry is untouched:** it remains the parent's `open[j+1]`, resolved on the decision clock.
Only the L4 exit legs read M1. **The parent-parity cell (§2.2) uses the parent's fixed exit and is
therefore unaffected by this clause** — parity would break if it were not.

**No slippage, queue or partial-fill model.** This is a screen.

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
    window). Residual dependence handled by block bootstrap under SPDR-018's inherited block rule
    (min 1 day = 24 H1 bars, envelope over blocks x seeds, 5-seed battery; SS1, SS8.1; B-9).
```

**Flat legs** use **SPDR-014's own 5 bps deadband**, not an `r == 0` test: `|r| < 5 bps` is FLAT,
excluded from `p`, counted as `p_flat` and disclosed per cell. **UNDECIDED-side events** are the
parent's second exclusion and are handled the same way: an event whose side cannot be resolved
(§2.1) is **excluded from the signed cells and from `p`**, **counted per cell and per `z`**, and
emitted — never silently dropped. Its incidence rises with `z`, i.e. across exactly the extended
grid this design adds, so the count is reported on every `z` level and asserted in §12.

*(An earlier draft wrote `r == 0`, silently narrowing the parent's deadband, and carried UNDECIDED
in §2.2's prose only — not in the exclusion rule and not in any integrity check. Both are corrected
here, in the clauses that actually govern `p`.)*

---

## §4 The layer protocol (AMENDMENT-C6 — BINDING)

Identical protocol to `SPDR-019`, applied to this entry. Every stage emits the full decomposition
with block CIs, its MDE in log units, its evidence class, its `p_event`, and its episode count.
**No stage is skipped because an earlier one read flat.**

| Stage | What runs | Variants | Read |
|---|---|---|---|
| **L0** | The event entry with the **parent's** fixed exit (`open[entry+h]`), no selection, no modulation. Both MOMO and MR sides | 6 (3 event types × 2 sides) at the primary `z` | The baseline `(p, W, L, log R)` and κ. **Mandatory first** |
| **L1** | **Scale alone, on the fixed L0 entry.** The event keys, breach bar, side and entry fill are bit-identical to L0. At the central setting of each payoff-bearing L4 device — target `a=2`, trail `b=1`, hold `h=12` — compare the ŝ-modulated parameter with its TRAIN-median-ŝ unmodulated twin. These three pairs are generated here and reused, not duplicated, in L4 | 3 paired reads (6 physical rows, already included in L4's 18) | paired Δ`log R` modulated minus unmodulated; the full decomposition. Position sizing is excluded from this mean read because it may move dispersion only |
| **L2** | **State alone**, three cells: **(i)** shock (HMM HIGH/LOW at the breach bar), **(ii)** level (R-MARKOV k=4/k=12), **(iii)** both jointly | 5 | Δ`log R` per axis **and the interaction term** |
| **L3** | **Swing gate alone.** `T-GT-CUR` at the breach bar; parameters at L0 values | 2 | Δ`log R`; **plus the mandatory L-51 three-number selection check** |
| **L4** | **Capture devices, one at a time**, each run **twice** — unmodulated (a fixed multiple of the TRAIN-median σ̂ per symbol) and modulated (× ŝ) | **18** — target 3+3, trail 2+2, hold 3+3 (the parent's frozen `h`), sizing 1+1 | Δ`log R` per device; the unmodulated run is the comparator that separates the device from the information |
| **L5** | The small combination L1–L4 justify | ≤ 4 | Term decomposition alongside any blend. **Evidence-selected; cannot substitute for phase (b)** |

**L4 device grid** is the SPDR-019 grid unchanged (dynamic target, trailing stop, holding period,
sizing), with holds bounded by the parent's frozen `h ∈ {4, 12, 24}` rather than by regime run-length
— because this object's horizon is inherited, not chosen.

**L1 fixed-entry assertion.** L1 may change only the capture parameter named by the pair. It may
not alter `z`, band width, event eligibility, event index, side, entry index or entry price. The
three paired reads are the central target, trail and hold rows of L4, so L1 tests prediction 1
without adding a second entry population or double-counting those rows in the multiplicity total.
This restores AMENDMENT-C6's single-entry protocol. Any ŝ-conditioned entry arm is withdrawn.

**The `E-TOUCH > E-HORIZON > E-CLOSE` ordering** (≈3–4 bps crypto, ~1/5 that on cTrader, replicated
in sign — V27, evidence class `[P]`) is a **design input**: event types are reported separately and
never pooled. It is **not** an edge and carries no expectancy claim.

### 4.1 Phase (b) — the full cross

> **Phase (a) determines WHETHER phase (b) runs. It does NOT determine WHAT is in it.**

**TRIGGER — pre-declared here, before phase (a) runs (registered AMENDMENT-C6; reflection
§5.9.1).** The condition is stated on the phase-(a) reads themselves:

```
Phase (b) MAY run only if, in the phase-(a) emission on the primary read, AT LEAST ONE of:
  (i)  some layer/device cell has  Delta log R vs L0  with ci_low > 0, or
  (ii) some layer/device cell has  absolute log R     with ci_low > 0.
Otherwise phase (b) DOES NOT RUN, and that is the pre-declared outcome.
```

It uses the §9 CI-relative band vocabulary and introduces **no magnitude**: nothing is admitted,
excluded, labelled or ranked by it, no cell is dropped, and every phase-(a) cell is reported in
full either way (INFR-016 intact). It is a stopping rule on a phase, not a value gate on a cell.

The condition is **necessary, not sufficient**: phase (b) additionally requires its own operator
execution authority and its own design amendment, and the operator may decline a fired trigger.
What the operator may not do is decide after seeing (a) what "promising" meant — the
optional-stopping hole C6 exists to close.

*(AMENDMENT-15, now superseded, replaced this with post-(a) operator judgement and carried a
standing execution blocker. The condition is restored, so the blocker is discharged.)*

**The SCOPE is pre-declared too, and is what prevents the overfitting.** Phase (a) may inform
*whether* phase (b) runs; it may never shrink what phase (b) contains.

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
  bite/MDE: block-bootstrap CI on log R under SPDR-018's inherited block rule (SS8.1). Per-cell
    MDE in log units emitted BEFORE the read (SS8), with the effective sample size, the realised c
    and the control's own sensitivity ladder. No adequacy cutoff is applied; the reader judges
    from the ladder.
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
  bite/MDE: >= 2000 seeds; plant curve at +5/+10/+20/+40 bps, stated ALSO in sigma-hat units
    (0.068 / 0.137 / 0.274 / 0.548 sigma at the measured pooled sigma-hat = 73.00 bps) and
    RE-DERIVED per universe at run, never carried as an absolute bps bar across a universe
    boundary (L-50 / P-21). Reported per cell class. The control is declared UNUSABLE for any
    effect below its own plant-curve resolution.
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
  bite/MDE: >= 2000 seeds; plant curve co-designed at +5/+10/+20/+40 bps, stated ALSO in sigma-hat
    units (0.068 / 0.137 / 0.274 / 0.548 sigma at sigma-hat = 73.00 bps) and RE-DERIVED per
    universe at run (L-50 / P-21); detection rate reported per rung. The control is declared
    UNUSABLE for any effect below its own plant resolution.
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
  bite/MDE: mean CI ~+-10 bps at the parent's n (~0.137 sigma at sigma-hat = 73.00 bps; re-derived
    per universe at run, L-50/P-21); emitted with the same ladder as every other cell. Reported as
    disclosure, never as a gate.
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

COLLAPSE FRACTION (B-2), all five controls: each control emits its collapse fraction as a
  DISCLOSURE quantity with its percentile and null quantiles. Per governance's standing rule M-5,
  collapse fraction is DISCLOSURE-ONLY NEAR A ZERO MEAN - which is exactly this object's regime,
  measured at gross break-even (p 0.0007 from its own break-even) - so no collapse fraction is a
  gate, a threshold or a pass condition anywhere in this design, and none appears in the HARD list.
```

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
L-24.3 NO EFFECT-SIZE TRIPWIRE THRESHOLD (F06): the tripwires use prospective structural
  inequalities stated below, not a developer-chosen payoff magnitude. Their payoff deltas and CIs
  are disclosed, never asserted.
```

### 6.2 Leak tripwire (HARD — blocking)

```
TRIPWIRE-1 (causal misalignment):
  form: rebuild the band width and every layer's conditioning state from bar [t+1] instead of
    [<= t], and re-run identically.
  emitted statistics: `changed_conditioning_rows`, `event_key_symmetric_difference_count`, and
    paired deltas in p, W, L and log R with CIs.
  HARD PASS, fixed before the run:
    `changed_conditioning_rows > 0`
    AND `event_key_symmetric_difference_count > 0`.
  The first inequality proves the illegal input actually differs; the second proves the event
  pipeline is sensitive to that difference. No sign or magnitude of a payoff delta is required.

TRIPWIRE-2 (breach-detection look-ahead):
  illegal form: at the anchor, inspect the complete future event window
    `[anchor_idx, anchor_idx+H]`. If any later bar touches the band, assign the touch to
    `leaky_event_idx = anchor_idx` and enter at `open[anchor_idx+1]`. The legal detector remains
    sequential and assigns the actual earliest touch `legal_event_idx = j`, entering at
    `open[j+1]`. No phrase such as "bars after j" is part of the detector.
  emitted statistics: `future_touch_zones`, `early_entry_count`, event-index pairs, and paired
    deltas in p_event, p, W, L and log R with CIs.
  HARD PASS, fixed before the run:
    `future_touch_zones > 0`
    AND `early_entry_count > 0`
    AND for every counted early entry,
        `leaky_event_idx = anchor_idx < legal_event_idx`.
  These assertions test the exact look-ahead failure shape. No payoff-effect threshold is used.
```

---

## §7 Unit pin (L-21 / P-15)

```
CONVERSION-PIN:
  divisor object: sigma_bps(t) = s_symbol * EWMA_park(t)
                  EWMA_park = LTF H1 Parkinson EWMA(lambda=0.94), 60 H1-bar warm-up, causal
                  <= t-1. EWMA_park ALONE IS DIMENSIONLESS - `s_symbol`, the parent's frozen
                  per-symbol scale factor, is the ENTIRE bps conversion and may never be omitted.
                  Horizon-scaled sigma_bps*sqrt(h) with h in HOURS on both clocks.
                  IDENTICAL object to SPDR-014's Z-VOL width and SPDR-018's unit pin - reused
                  verbatim, never redefined.
  s_symbol source: SPDR-014/results/zvol_scale.json, READ from the artifact and asserted against
                  it in code; never recalled, never re-fitted. Measured range across the 17
                  covered symbols is ~4,606-7,338 (e.g. BTCUSDT 6,384.3, ETHUSDT 6,547.2,
                  SOLUSDT 6,215.6). It is NaN for 8 symbols (ORDI, TIA, BIGTIME, 1000PEPE, SEI,
                  WLD, PYTH, 1000RATS - insufficient DESIGN warm-up), which is the SAME gap as
                  SS10's 17-of-25 coverage row and is restated here rather than cross-referenced.
                  P-15 exists because EXP-025 inflated a target 4.1x by asserting a divisor from
                  memory at exactly this seam; a pin that omits the scale factor is not a pin.
  unmodulated L4 arms: a fixed multiple of the TRAIN-MEDIAN sigma_bps PER SYMBOL - the SAME
                  estimator, unit and clock as the modulated arm, differing ONLY in whether the
                  boundary responds to the forecast. Per-symbol medians port across symbols
                  (L-50/P-21). Wilder ATR(20) is NOT used to set any exit boundary: pairing an ATR
                  arm against a Parkinson arm is two different estimators (Wilder ATR ~ mean true
                  range, Parkinson sigma ~ 0.6 x range), which is a ~1.5-1.7x level shift on top of
                  the information effect - the EXP-025 seam (L-21) the L4 comparison exists to
                  avoid.
  measured value: TRAIN-median of both, per symbol and pooled, COMPUTED AT RUN ->
                  results/unit_pin.json, together with the s_symbol actually used per symbol.
                  Never recalled, never asserted. THE GAP IS STATED: 17 of 25 symbols carry a
                  Z-VOL value; the 8 above do not, and every "pooled" Z-VOL figure in this design
                  is pooled over 17, with M-4 effective coverage applied to that figure.
  resulting effect: every effect reported in BOTH bps and sigma units, side by side, per cell.
  cost floor:     13.1-16.1 bps partial; spread NOT charged. DISCLOSED REFERENCE only - no read
                  in this design is compared against it (AMENDMENT-C5). A sigma-unit effect is
                  NEVER compared to the floor (P-15).
```

---

## §8 Resolution statement — sensitivity across a range, not a single bar

Same derivation as `SPDR-019` §8. **No resolution figure is typed into this document.** Every one is
computed by `xen.resolution_basis` from SPDR-018's emitted cells and pinned to
`results/resolution_basis.json`; this section states the METHOD and the artifact, and the numbers
live in the artifact.

```
DEFINITION (xen.resolution_basis):
    mde_log = block_mde_bps / ((1-p)*L)          MDE in log-residual units
    c       = mde_log * sqrt(n)                  dimensionless; reusable only under the same
                                                 CI construction (L-50)
    required n at target D = (c/D)^2             mde50 at size n = c/sqrt(n)
c is FLAT across horizons (block_mde_bps and (1-p)*L both rise with h and cancel) and RISES with n,
which is the block-dependence penalty. Both facts are measured, not assumed.

WHY THIS IS A FUNCTION AND NOT PROSE: four successive drafts of this section typed four different
constants, each pairing a numerator and a denominator from DIFFERENT populations, and the fourth
mixed row counts across policy arms. Every one of those errors was arithmetic in prose, where
nothing could check it. Resolution figures are now emitted, versioned and diffable.

BASIS PROVENANCE AND ITS LIMIT (recorded because reusing c across CI rules is unsound):
  c was measured on SPDR-018 H1 cells under the complete rule quoted in §8.1. This design adopts
  that rule unchanged for H1. H4 has a horizon-scaled block sweep and therefore receives no
  transported c prior: its expected-resolution rows remain null until the realised H4 c is
  measured. Reusing the H1 c under H4's different sweep is forbidden.

POPULATION - ONE, DECLARED AND ENFORCED: the basis is computed on SPDR-018 ARM C ONLY and the
  artifact pins the filter, the row accounting and the exclusions by reason - 24,098 source rows
  -> 18,988 matched by `arm == 'C'` -> 18,479 retained, 509 excluded, all 509 for a missing
  required value. It also carries `horizon_summaries` per band, because c is NOT asserted flat
  across horizons: in the 15,000+ band the arm-C horizon medians are 11.855 / 8.363 / 11.744.

THINNESS IS DISCLOSED, NOT FLATTERED (the artifact carries `cells` AND `distinct_n` per band):
  the 15,000+ band - the band this design's E-TOUCH strata land in - holds 26 rows but only
  8 DISTINCT sample sizes across 3 bases. Its interquartile spread (c 8.36-12.09) is therefore
  NOISE, not a defensible range, and NO "range across bases" claim is made from it. Where a band
  is thin the design says so and reports the wider uncertainty rather than picking a favourable
  end. An earlier draft treated 26 rows as 26 independent observations and quoted anchors of
  c = 7.5 / 9 / 11.9 that were picked rather than measured; those are withdrawn.
```

**The direct check, computed the same way.** In SPDR-018's own emission, arm-C pooled cells with
`n ≥ 10,000` realise 0.053–0.107 log units, and the three largest realise 0.073–0.094 at every
horizon — flat, as `c` predicts. **0 of the 18,479 retained arm-C cells reach 0.03** (`row_counts.retained` in the basis artifact), other than three degenerate
`n = 2`, `p = 0` cells which carry no information. Any prediction that this design will "approach
0.03" is refuted by the parent's own data before it runs.

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

**Removing the selectivity gate is what gives this experiment a usable population.** The
`p_event ≤ 0.60` gate would have discarded the large majority of Z-VOL events. *(An earlier draft
quantified this as "41,739 of 511,350 rows, 91.8% discarded". That denominator sums `n_events`
across overlapping `h` and `H` cells, so it double-counts events: the figure is reproducible and
meaningless. The gate's effect is recomputed at run at a single grain and reported then.)*

**Population must be counted at the SIGNED-ARM grain, and the parent supplies it for only one
cell.** This is the grain error that broke the previous draft, so it is stated explicitly. In
`SPDR-014/results/post_event.parquet`, at `Z-VOL`, H1, `H`=12, `h`=12, the `policy` column separates
the unsigned pass (`P-NONE`) from the signed arms (`P-MOMO` / `P-MR`), and the parent ran the signed
arms at **exactly one cell**:

| `z`, event type | parent unsigned `n` | parent signed MOMO / MR `n` |
|---|---:|---:|
| **1.5, E-TOUCH** *(the parity anchor)* | 6,861 | **15,041 / 15,331** |
| 1.5, E-CLOSE | 6,484 | **not run by the parent** |
| 1.5, E-HORIZON | 4,485 | **not run by the parent** |
| 2.0 / 1.0, all event types | 4,284 – 6,994 | **not run by the parent** |

Pinned in full to `results/expected_resolution_prior.json`. That artifact expands the complete
declared base grain — source(3) × clock(2) × H(3) × h(3) × z(4) × event(3) × policy(2) =
**1,296 rows** — and carries signed counts only for the two parent cells above. All other rows are
explicit nulls, not omitted and not imputed.

*(An earlier draft quoted "E-TOUCH 40,178 / E-CLOSE 6,484 / E-HORIZON 4,485". 40,178 is a ROW count
summing three policy arms across two clocks; the other two are unsigned-only counts. That table
mixed two grains in three rows and overstated the headline cell by **~2.7×** — in the optimistic
direction, which is the expensive one for a table whose whole purpose is to stop a thin result being
read as "no effect". Withdrawn.)*

**Consequently the signed-arm `n` for every cell except the parity anchor is NOT KNOWN before the
run and is COMPUTED AT RUN.** This design emits both side arms for every event type, so the parent's
unsigned counts are a disclosed lower-bound prior at a different grain — never a substitute. Saying
"unknown until measured" is the honest predeclaration here; inventing a number is what failed.

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
  MDE is always the dependence-matched BLOCK form (M-1): SPDR-018's complete rule verbatim on H1,
  and §8.1's horizon-scaled rule on H4. The iid form is companion-only and may never be presented
  as the cell's resolution.

  B-5 ENFORCEMENT (QA runs 2 and 3 - the label was categorical and therefore countable; these
  restore that property without a threshold, and are HARD schema checks, not conventions):
    1. No `log R` value ships in ANY artifact without `ci_low`, `ci_high`, `ci_width` and
       `block_mde` present on the SAME ROW. Asserted over metrics_by_cell, layer_deltas and the
       resolution ladder alike.
    2. Any AGGREGATE statement over cells ("N of M covered the mirror") must carry the
       resolution distribution of those cells - median mde50 and the count below each rung.
       An aggregate without it is a negative-by-omission, which B-5 forbids as squarely as a
       dropped label does.
    3. The expected-resolution table (below) is PREDECLARED per stratum, at the granularity the
       design reports - which on this design means PER EVENT TYPE. Predeclaration was the real
       content of the retired POWER block and is orthogonal to the label; it is retained.
    4. PREDECLARED vs REALISED on the same row (QA run 3). Each stratum's predeclared expected n
       and expected mde50 ship alongside its realised n and realised mde50 in
       resolution_ladder.parquet. With the adequacy label retired, the reader calibrates against
       the predeclared table, so the predeclaration IS the B-5 protection and must be checkable
       after the fact. Nothing is admitted, excluded, labelled or ranked by the comparison.
```

**What this changes and what it does not.** The conversion `Δlog R ≈ Δmean / ((1−p)·L)` and the
`n`-scaling below are **derivations** and stand unchanged — they are how resolution is computed. What
is removed is the single canonical bar that used to turn them into a verdict.

```
EXPECTED RESOLUTION, PER STRATUM - PREDECLARED BY GENERATION, NOT BY TYPING.
  Predeclaration is required (design-requirements SS6, B-5) and is retained in full. What changes
  is that it is COMPUTED and PINNED rather than hand-written:

    results/expected_resolution_prior.json   the parent's per-cell counts at the SIGNED-ARM grain,
                                             with the "not run by the parent" cells marked as such
    results/resolution_basis.json            the c bands, with `cells` and `distinct_n` per band
    -> results/expected_resolution.json      expected n and expected mde50 per stratum, generated
                                             from those two by xen.resolution_basis BEFORE the run,
                                             committed and dated. This IS the predeclaration.

  Deterministic generator API:
    xen.resolution_basis.write_expected_resolution(
        prior_path, basis_path, output_path,
        generated_at_utc="2026-07-29T00:00:00Z",
        source_hashes=<the six SHA-256 pins embedded in the output>)
  Expected output SHA-256: f174eaf655be0ef7bcf376618d1d82ff49bed2b49cc1cca1f6ab9e4f95b19341.

  The generated artifact already exists, is dated, and pins the SHA-256 of both JSON inputs, the
  shared module, and every parent artifact used. Implementation must verify those hashes before
  consuming it; regeneration after implementation begins is a design change requiring a new QA
  review.

  WHAT IT SAYS TODAY, in words rather than a table that would rot:
    - both parity-anchor signed arms (15,041 and 15,331) are in the 15,000+ band. The artifact
      applies that band's median c separately to each exact n. It makes no range claim from the
      thin band (26 rows, 8 distinct sample sizes).
    - every other signed cell is UNKNOWN until run and is emitted with its realised n and c.
    - no unmeasured cell receives a resolution claim. The withdrawn claims that a cell reaches
      0.05 or approaches 0.03 are not replaced.

  STATED PLAINLY: a covering CI must read as "we could not see an effect this small here", never as
  "there is no effect" (B-5). Forecast error is disclosed symmetrically as signed
  `(realised_mde50 - expected_mde50)` where a prior exists. Inference uses the realised CI and MDE
  only. Nothing is discarded or promoted because the forecast was optimistic or pessimistic.

  RESOLUTION IS MEASURED, NOT FORECAST (HARD, the permanent fix): every cell emits its OWN realised
  c alongside its realised n and mde50, and the predeclared expected n / expected mde50 ship on the
  SAME ROW, together with the signed forecast error. Nothing acts on the comparison: all
  interpretation and every aggregate use the realised CI/MDE. The comparison is a calibration
  audit, while clauses 1-3 above are the operative B-5 protection.
```

**Consequence, stated plainly:** like `SPDR-019`, this is a **pooled** experiment — that is where
resolution is finest. Per-symbol cells are heterogeneity disclosure, reported in full with their own
resolution attached rather than excluded.

### 8.1 Block rule

```
H1 BLOCK RULE (binding, code-asserted) — SPDR-018 §6.2 verbatim:
  - aggregate to per-calendar-day sufficient statistics; resample day-blocks of {1,3,7}
    days; minimum block = 1 day = 24 H1 bars >= every horizon in scope;
  - envelope = min/max over blocks x seeds (conservative), 5-seed battery,
    xen.evaluation.block_bootstrap_ci, effective block capped < n (INFR-004 / L-20);
  - the reported MDE is the block MDE. The iid 2.8sigma/sqrt(n) form inherited from SPDR-014
    is emitted only as a labelled companion column and may not drive a band label.

H4 CO-REPORT RULE (binding, code-asserted):
  h is inherited from SPDR-014 in BARS, so h={4,12,24} on H4 spans {16,48,96} hours. Aggregate
  per-calendar-day sufficient statistics and resample day-blocks of {4,12,28} days — the same
  {1x,3x,7x} sweep relative to the 4-day maximum horizon. Use the same 5-seed min/max envelope,
  xen.evaluation.block_bootstrap_ci, effective block < n, and block-MDE/iid-companion rule.
  This clock-specific sweep preserves the parent h object; it does not reinterpret h as hours.

The SPDR-018 c basis transports to H1 only. H4 rows have no expected c prior and report their own
realised c. Realised effective sample size is emitted per cell on both clocks. The withdrawn
`max(h in hours, 20 hours)` form is not a live rule.
```

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

POOLED: the lane default is that a pooled figure is DISCLOSURE-ONLY (spdr-lane L-03). This design
  proposes pooled-across-symbol as the PRIMARY read, because that is where resolution is finest
  (SS8), and it may hold that status only conditionally:
    - every pooled figure is reported WITH a homogeneity statistic (I^2 across symbols) and the
      per-symbol spread behind it, and is stated as pooled over the 17 Z-VOL symbols, not 25;
    - if the emitted homogeneity statistic does NOT support pooling, the pooled line REVERTS to
      the lane default and is reported as disclosure-only, with the per-symbol table as the read.
    - The OPERATOR judges that on the emitted value. No cutoff is written here and nothing is
      machine-dropped (INFR-016) - what is pre-declared is the CONSEQUENCE, so the lane default is
      the fallback rather than something this design discards a priori.
  Per-symbol figures are disclosure in either case.
EVIDENCE CLASS: rows still carry [S] scored / [D] disclosure per reflection SS2.0 - these describe
  WHAT KIND of read a row is, not whether it is adequate. The [P]/[U] adequacy classes are
  RETIRED for this experiment; adequacy is read off the MDE and resolution curve.
```

**No band is a gate, and no band is an adequacy claim.** Every value/quality read is a report layer;
the operator authorises what advances (INFR-016). Nothing is machine-dropped between layers.

**The B-5 protection: strengthened on emission, and conditional on §8 on inference.** B-5 exists so
a thin cell is never read as a negative. A boolean `UNPOWERED` flag delivered that with an invented
cutoff; **binding every effect to its own MDE and CI width on the same row (a HARD schema check,
§12) delivers it without one**, and the §13 refusal on aggregates lacking the resolution
distribution closes the negative-by-aggregation route a boolean left open. On the **emission** axis
the protection is genuinely stronger.

**What B-5 does and does not protect.** An optimistic forecast can help a thin covering CI be
misread as evidence of no effect; that is the primary B-5 harm. A pessimistic forecast is a
calibration error too, but it is not symmetric in consequence because it cannot erase a realised
CI/MDE from the emission. The operative protections are therefore the same-row realised CI/MDE,
the aggregate-resolution requirement and the ban on negative-by-omission. The expected/realised
comparison audits the forecast; it does not referee inference, and nothing acts on it.

---

## §10 Scope

| Item | Freeze |
|---|---|
| Primary catalog | Bybit USDT linear perps, `data/catalog/`, INFR-011 fence |
| Universe | top-25 30d USD volume (AMENDMENT-U1); pin `cf-voldir-001-universe.json`; recompute + assert set equality. **Z-VOL resolves on 17 of the 25** — see the coverage row below |
| Clock | **H1 primary** (SPDR-014's own clock), **H4 co-report** |
| Fill resolution | entries on the decision clock at `open[j+1]` (parent, unchanged); **L4 target and trail exits on M1 (T1 lane) bars**, causal, no intrabar look-ahead (§2.2a) |
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
| Cell count | **Counted out, not capped** (multiplicity disclosure, `spdr-lane.md` L-03). *Primary grid* = `Z-VOL` × H1 × `H`=12: `z`(4) × `h`(3) × event(3) × side(2) = **72 base points**. Non-L4 layer rows per base point = L0 1 + L2 5 + L3 2 + L5 ≤4 = **12** → 864. L1 reuses six central paired rows already inside L4, so it adds zero physical rows. *L4 devices*: target 6 + trail 4 + sizing 2 = 12 variants × 72 = 864, plus hold 6 variants × 24 (`h`-free) points = 144 → **1,008**. **Primary maximum = 1,872 cells.** The declared clock(2) × source(3) × H(3) expansion is exactly 18 primary-shaped grids: **33,696 cells before DESIGN/CONFIRM verification-band rows**. These are multiplicity disclosures, not independent discoveries. The report is frozen at ≤8 plots; the full grid ships in tables. *(The withdrawn “≈13,000” did not multiply the named axes; the earlier “≤120” counted only one partial point.)* |

---

## §11 Golden traces (QA derives the numbers — the developer must not)

```
G1 (parent parity - the anti-drift proof). HAND-DERIVED VALUES, stated here so the trace is
  falsifiable BEFORE the run rather than authored at run time:
  ETHUSDT, H1, DESIGN, Z-VOL, z=1.5, H=12, E-TOUCH, h=12, **policy P-MR**.
  The FIRST decided event.
  Source artifact (named, not "the published values"): SPDR-014/results/post_event.parquet for the
  per-event values, SPDR-014/results/expectancy_by_cell.parquet for the cell aggregates.

    anchor_idx   61          event_idx  61          entry_idx  62      exit_idx  74
    entry_ts     2022-07-17T14:00:00Z               exit_ts    2022-07-18T02:00:00Z
    side         -1          label      MR          exit_reason  time
    r_h          -157.371411 bps

  QA computes independently: the band width from s_symbol * EWMA_park, the anchor open, the touch
  bar, the breach side, the entry open[j+1], the exit open[entry+12] and r_h in bps - and asserts
  each equals the value above to |d| <= 1e-9 (SS2.2). A mismatch on ANY of them means the object
  was re-specified.

G2 (p_event is measured, and measured correctly). HAND-DERIVED VALUES:
  ETHUSDT, Z-VOL, E-TOUCH, H=12, **policy P-NONE**, at z=1.5 and at z=3.0.
  Expected at z=1.5, from SPDR-014/results/expectancy_by_cell.parquet:
      DESIGN  p_event = 0.994872  (n_events 194, n_decided 194)
      CONFIRM p_event = 1.000000  (n_events 249, n_decided 249)
  QA computes p_event at BOTH z levels from the emitted zones and confirms (a) the z=1.5 values
  equal the two figures above, (b) p_event FALLS as z rises to 3.0 (a NEW cell, computed at run -
  the direction is the prediction, not the value), and (c) NO code path uses p_event to filter,
  exclude, weight, rank or label any cell. This trace exists to prove the covariate is measured
  and not applied.

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

G8 (exit fill precedence - the clauses most likely to invert in code):
  Any symbol, H1, full TRAIN, Z-VOL, z=1.5, E-TOUCH, P-MOMO, target a=2 with trail b=1. The FIRST
  episode in which BOTH the target and the trailing stop are reachable inside the SAME M1 bar.
  QA computes: which fills under SS2.2a's ADVERSE precedence rule, the fill price and r in bps -
  and separately confirms (a) the trail ratcheted on M1 CLOSES only, never intra-bar, and (b) a
  time-exit episode fills at the open of the first decision-clock bar at or after `entry + h`.

G7 (leak discrimination):
  The G1 rows under TRIPWIRE-1's leaky twin; QA asserts `changed_conditioning_rows > 0` and
  `event_key_symmetric_difference_count > 0`, and confirms that only the legal variant enters
  the research emission. Payoff deltas are reported but carry no pass magnitude.
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
| **Exit fill causality** | every L4 target/trail fill's M1 timestamp is `>` its entry bar's open; the trail level updates only on M1 **closes**; where target and trail are reachable in one M1 bar the **adverse** one is recorded; asserted per episode (§2.2a) |
| **Parent parity** | reproduces SPDR-014's published cells at `z=1.5` on the parent's band, to a declared tolerance — **the proof the object was not re-specified** |
| **`p_event` emitted** | on every cell, per event type, as a **reported covariate**. Asserted not to filter, exclude, gate, weight, label or rank any row or cell (INFR-016 / L-32) |
| Universe pin | top-25 recompute == pin file, set equality |
| **Identity reconstruction** | `\|p·W − (1−p)·L − mean\| < 0.01 bps` on **every** cell |
| **`log R` definition** | asserted equal to `log(W/L) − log((1−p)/p)` with **slope 1**; a fitted-slope residual anywhere is a **hard failure** |
| **Cost isolation** | no cost term in any estimand, threshold, band or comparison; `p_be_net` present, flagged `DISCLOSURE_ONLY` (AMENDMENT-C5) |
| **MDE column** | the reported resolution column is the **block** MDE in log units; iid is companion-only (M-1) |
| **Block rule** | H1 uses SPDR-018's complete rule verbatim: per-calendar-day sufficient statistics, `{1,3,7}`-day blocks, 5-seed min/max envelope, `xen.evaluation.block_bootstrap_ci`, effective block `< n`. H4 uses the explicit `{4,12,28}`-day horizon-scaled co-report rule (§8.1) and may not consume the H1 c prior. A missing sweep/seed, wrong clock rule, or live `max(h hours,20 hours)` form is HARD |
| **`s_symbol` provenance** | the Z-VOL divisor is asserted equal to `s_symbol × EWMA_park`, with `s_symbol` **read from** `SPDR-014/results/zvol_scale.json` and asserted against it; the 8 NaN symbols are emitted by name (§7, L-21/P-15) |
| **UNDECIDED** | the UNDECIDED count is emitted per cell and per `z`, asserted **excluded** from the signed cells and from `p`, and **never dropped** (parent rule, §2.1/§3) |
| **L-51 selection check** | the three-number check runs on **every selected subset the design or analysis reports separately** — L2's state cells, L3's gate, L5's combination, each event type against the others, and cells above vs below median `mde50` — each against its own complement, emitted to `results/selection_check.json`. HARD means the file, required rows, three named statistics and complement keys are present; no statistic has a pass value and no result gates a cell (INFR-016) |
| **M-4 effective coverage** | every pooled Z-VOL figure is asserted pooled over the **17** covered symbols, not 25; effective-vs-nominal coverage emitted; no pooled count is a date-range or nominal-universe product |
| **Predeclared vs realised resolution** | each stratum's predeclared expected `n` and expected `mde50` (§8), including explicit nulls, ships beside realised `n`, realised `mde50`, and signed `(realised-expected)` error. All inference and aggregates use realised CI/MDE. The comparison gates and ranks nothing |
| **`log R` never unaccompanied** | HARD schema check: no `log R` ships in **any** artifact without `ci_low`, `ci_high`, `ci_width` and `block_mde` on the **same row** — asserted over `metrics_by_cell`, `layer_deltas` and the resolution ladder alike (B-5 enforcement, QA run 2) |
| **Ladder plant operator** | both plant operators (via `W/L` at fixed `p`; via `p` at fixed `W/L`) computed and emitted per rung; neither omitted |
| **No adequacy flag** | asserted that **no** `powered` / `unpowered` / `at_target` / `NOT_RESOLVABLE` column is emitted anywhere, and that no single canonical MDE threshold appears in code (operator mandate 2026-07-28) |
| **Ladder emitted** | the sensitivity ladder is present on **every** cell, with its detection rates and required-`n` values |
| **Span disclosure** | exact-span subset and span distribution per horizon cell (M-2) |
| Episode exclusivity | one open episode per symbol; suppression count emitted |
| Derangements | fixed-point count == 0, measured and reported (L-28) |
| Determinism | runs **unconditionally** whenever `--jobs > 1`, independent of `--resume`; parallel bit-identical to sequential (P-23) |
| Golden traces | G1–G8 pass |
| No local accounting | availability/residual bps, not booked P&L; no `xen.adjudication` mimicry |
| Code hash | sha256 of `screen_code/` pinned into `results/integrity_selfcheck.json` |

```
HARD (block execution / invalidate emission):
  EVERY SS12 ROW IS CLASSIFIED - a row with no class is a row nobody has to run (QA run 6).
  HARD, EXPECTED COUNT = 29, reconciled BY NAME by the check-count assertion (P-23 / L-52),
  against THIS TABLE AND SS6.2 - the two tripwires are specified in SS6.2 and are HARD there:
    1  check-count reconciliation     2  TRIPWIRE-1                3  TRIPWIRE-2
    4  TRAIN fence                    5  holdout                   6  causality
    7  breach detection               8  EXIT FILL CAUSALITY       9  parent parity
    10 universe pin                   11 identity reconstruction   12 log R definition
    13 cost isolation                 14 MDE column (block, not iid)
    15 BLOCK RULE (H1 verbatim + H4 co-report)                     16 s_symbol PROVENANCE
    17 UNDECIDED accounting           18 M-4 effective coverage    19 `p_event` NON-APPLICATION
    20 NO ADEQUACY FLAG               21 LADDER EMITTED            22 LADDER PLANT OPERATOR
    23 L-51 SELECTION CHECK           24 `log R` never unaccompanied
    25 PREDECLARED vs REALISED resolution                          26 NO LOCAL ACCOUNTING
    27 derangement fixed-point count  28 golden traces G1-G8       29 determinism
  (Rows 19-26 are HARD on PRESENCE and FORM: they assert the check ran, the required columns
  exist, and no prohibited column exists. None adjudicates a value; no cell is admitted or
  excluded by any of them. `p_event` non-application and `no adequacy flag` are HARD precisely
  because they are the INFR-016 and C7 protections - a protection nobody verifies is a comment.
  L-51 is HARD because governance SS1b makes it mandatory, and a selection check that is silently
  skipped is indistinguishable from one that passed.)
  INFORMATIVE, and never a pass condition: episode exclusivity counts, code hash, span
  disclosure values, every effect size, control percentile, collapse fraction, band label,
  p_event VALUE, dose-response shape, kappa, cost overlay, heterogeneity statistic, event-type
  ordering. (Episode exclusivity and code hash are emitted and checked, but a violation is
  reported rather than blocking: the first is a population disclosure, the second a provenance
  record.)
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
- **An aggregate over strata whose predeclared-vs-realised discrepancy distribution is not reported.** `analysis.md` must carry the full signed `(realised_mde50 − expected_mde50)` distribution for the strata any aggregate spans; a calibration audit nobody is required to read is not an audit.
- **A blended score without its term-level decomposition**; **a sizing cell reported as expectancy**.
- Any family status change; any XENA; any TEST or holdout contact.

---

## §14 Amendment ledger

```
AMENDMENT-1: remove the p_event <= 0.60 selectivity gate entirely; z grid set to
  {1.5, 2.0, 2.5, 3.0} (1.0 dropped as not an outlier band); every signal taken; p_event retained
  as an emitted covariate and dose-response axis, never a filter.
  - DIRECTION: LOOSER (no cell is excluded; the population grows)
  - Operator directive 2026-07-28. Rationale in 2.2: the threshold was invented, was the wrong
    SHAPE for this programme (INFR-016/L-32 retired arbitrary value-gates), and contradicted the
    purpose of a capture-geometry experiment, which is not to find better-selecting signals.
  - Registry/checkpoint wording clarified by the operator 2026-07-29: selectivity must be visible
    on every cell; `p_event` is a covariate, never an eligibility filter. No departure remains.
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

AMENDMENT-7: replace SS8's required-n arithmetic with the dimensionless constant
  c = mde_log * sqrt(n), stratified by n band, which removes the horizon split entirely (c is flat
  across h); report the basis range with an invariance statement per P-25; predeclare expected
  resolution PER EVENT TYPE; bind predeclared and realised resolution to the same emitted row;
  WITHDRAW the claim that a 20k-45k cell "reaches 0.05 and approaches 0.03".
  - DIRECTION: NEUTRAL (a correction and a finer predeclaration; nothing admitted or excluded)
  - QA run 3. The withdrawn table's twelve printed values implied a divisor of 47.7-47.9 against
    the 66.4 stated beside them - carried over from SPDR-019's powered-subset basis rather than
    recomputed - and the withdrawn sentence was contradicted by the required-n table above it, the
    predeclared table below it, and the "0 of 18,632 cells reach 0.03" two paragraphs earlier
    (that cell count was itself wrong: the retained arm-C population is 18,479).
AMENDMENT-8: state the block-bootstrap block in CALENDAR TIME, matched across clocks
  (block >= max(h in hours, 20 hours)); emit the realised effective sample size per cell.
  - DIRECTION: TIGHTER (a bar-stated block understates dependence and narrows CIs; c was measured
    on H1 cells where bars and hours coincide, so it transports only under this rule)
  - QA run 3. **SUPERSEDED by AMENDMENT-13; the `max(h in hours, 20 hours)` rule is withdrawn.**
AMENDMENT-9: complete the CONVERSION-PIN - the Z-VOL divisor is s_symbol * EWMA_park, with
  s_symbol read from SPDR-014/results/zvol_scale.json and the 8 NaN symbols named in the same
  block; add an s_symbol provenance assertion to SS12.
  - DIRECTION: TIGHTER (EWMA_park alone is dimensionless; a pin that omits the scale factor is
    not a pin, and P-15 exists because EXP-025 inflated a target 4.1x at exactly this seam)
  - QA runs 2 and 3.
AMENDMENT-10: L1 becomes a DISTINCT-ENTRY arm with its own L0 baseline; its delta is measured
  against that baseline, never against the SS4 L0.
  - DIRECTION: TIGHTER (removes a confound: a s_hat-conditioned band changes WHICH zones breach,
    so the old form mixed an entry-population change with a capture effect - the one comparison
    the layer protocol exists to prevent)
  - QA runs 2 and 3. **SUPERSEDED by AMENDMENT-16.**
AMENDMENT-11: count the cell grid out rather than capping it (~2,160 primary, ~13,000 including
  declared co-reports, against an earlier "<= 120") - **those two counts are SUPERSEDED BY
  AMENDMENT-16's 1,872 primary / 33,696 with the declared co-report axes; the rest of this row
  stands**; re-anchor the L-51 selection check to every
  SELECTED subset and make it HARD; add M-4 effective coverage, UNDECIDED accounting, the block
  rule and the predeclared-vs-realised check to SS12; make the pooled-primary read revert to the
  lane default if homogeneity does not support it; state collapse fraction as disclosure-only near
  a zero mean (B-2 / M-5); state every plant curve in sigma-hat units as well as bps (L-50/P-21);
  give G1 and G2 hand-derived values and name their source artifacts.
  - DIRECTION: TIGHTER (six checks added or promoted; a lane default restored as the fallback;
    two golden traces made falsifiable before the run)
  - QA runs 1, 2 and 3.

AMENDMENT-12: replace SS8's hand-computed resolution tables with generation by
  `xen.resolution_basis`, pinned to results/resolution_basis.json and
  results/expected_resolution_prior.json -> results/expected_resolution.json; emit realised c per
  cell; disclose band thinness (cells AND distinct_n); withdraw the 40,178 population figure (a
  row count spanning three policy arms and two clocks, optimistic ~2.7x), the picked c anchors
  7.5/9/11.9, and the double-counting 511,350 gate denominator.
  - DIRECTION: TIGHTER (the headline population falls ~2.7x; no cell's resolution improves)
  - QA run 4. Four drafts typed four different constants; the numbers are now emitted, not typed.
AMENDMENT-13: adopt SPDR-018's block rule VERBATIM (blocks in days, min 1 day = 24 H1 bars,
  min/max envelope over a block sweep, 5-seed battery) in place of the invented
  `max(h in hours, 20 hours)` single-block rule.
  - DIRECTION: TIGHTER (restores the INFR-004/L-20 sweep and seed battery; the withdrawn rule was
    LOOSER than the parent's and was mislabelled a tightening in an earlier ledger entry)
  - QA run 4.
AMENDMENT-14: record the L1 re-specification as a departure from AMENDMENT-C6's single-entry layer
  protocol. C6 specifies L0 -> L1 -> ... -> L5 on ONE fixed entry; L1's s_hat-conditioned band
  changes which zones breach, so it is given its own L0 (SS4).
  - DIRECTION: NEUTRAL (a confound is removed and one baseline cell is added; nothing is admitted
    or excluded, and the reflection SS5.6 prediction #1 assigned to L1 is now tested against L1's
    OWN baseline rather than against a different entry population)
  - QA runs 3 and 4. **SUPERSEDED by AMENDMENT-16; disclosure was not authority to depart.**
AMENDMENT-15: record the phase-(b) trigger as operator judgement on the full phase-(a) report,
  departing from registered AMENDMENT-C6 ("the (b) trigger is pre-declared before (a) runs").
  - DIRECTION: LOOSER (an optional-stopping guard is given up)
  - **SUPERSEDED BY AMENDMENT-17.** Disclosure was not authority: a design cannot amend a
    registered family amendment by recording that it disagrees with it. The pre-declared
    condition is restored in SS4.1 and this row's EXECUTION BLOCKER is DISCHARGED.
  - QA runs 4 and 5. SS4.1's scope protection (phase (a) may not shrink phase (b)) is intact.
  - SEPARATE STANDING EXECUTION BLOCKER: `reflection-mid.md` §9 was unsigned when this row was
    written. **It was SIGNED 2026-07-29 (option B), so that blocker is DISCHARGED.**

AMENDMENT-16: restore L1 to AMENDMENT-C6's single-entry protocol; remove the ŝ-conditioned entry
  and its private L0. L1 is now the three central fixed-entry modulated/unmodulated capture pairs
  already contained in L4. Specify deterministic tripwire inequalities, the exact H1 rule and
  horizon-scaled H4 rule, generate the complete 1,296-row expected-resolution prior, and correct
  the full multiplicity count to 33,696 before verification-band rows.
  - DIRECTION: TIGHTER (removes an unauthorised entry-population change and makes four integrity
    requirements executable; no cell is excluded)
  - QA run 5 remediation. Supersedes AMENDMENT-10 and AMENDMENT-14; AMENDMENT-13 already
    superseded AMENDMENT-8.

AMENDMENT-17: restore the pre-declared phase-(b) trigger of registered AMENDMENT-C6 and
  reflection SS5.9.1 (SS4.1), superseding AMENDMENT-15 and discharging its execution blocker; and
  re-pin the resolution artifacts after the shared basis was regenerated with its arm-C filter,
  row accounting and per-horizon summaries made explicit (SS8, SS15).
  - DIRECTION: TIGHTER (a loosening is withdrawn; the basis population and its exclusions become
    checkable; nothing is admitted or excluded)
  - QA run 5.

AMENDMENT-18: specify L4 exit fill resolution (SS2.2a: M1 target/trail fills, ratchet on M1
  closes, ADVERSE precedence, parent time exit unchanged), declare the M1 lane in SS10, add golden
  trace G8 and an exit-fill causality row to SS12; classify every SS12 row HARD or INFORMATIVE and
  state the expected HARD count; correct the retained arm-C cell count to 18,479; require
  `analysis.md` to report the predeclared-vs-realised discrepancy distribution; re-pin the
  resolution artifacts after the shared basis was regenerated so its `source_ci_rule` quotes
  SPDR-018 SS6.2's own text and nothing else.
  - DIRECTION: TIGHTER (the exit price stops being the developer's choice; four checks added or
    classified; no cell is admitted or excluded)
  - QA run 6.

historical row count: 3 looser / 11 tighter / 4 neutral
ACTIVE rows after supersessions (AMENDMENT-8 by -13, -10 and -14 by -16, -15 by -17):
2 looser / 9 tighter / 3 neutral.
L-23 STREAK FLAG (clause 3, and it applies to the conservative direction too): AMENDMENTS 8-13
are SIX consecutive TIGHTER rows, and 16-18 add three more. A one-directional streak is flagged
for the operator at the execution gate regardless of its sign - a design that only ever tightens
after review is a design whose first draft was systematically under-specified, which is exactly
what this ledger shows and what the operator should weigh.
NOTE per L-23: LOOSER now stands at 2 (AMENDMENT-1 gate removal, -2 full TRAIN) and is FLAGGED for
the operator at the execution gate. Both act only on population size. Neither
loosening touches an integrity check, a fence, a causality rule or a claim boundary; both act ONLY
on population size, and the second is a power lever SPDR-018 already used. No band label, control
or refusal is relaxed. Superseded rows remain in the historical tally and are named above. Under
AMENDMENT-C7 the false-qualifier count is **N/A / zero machine qualifiers**: no powered,
unpowered, at-target or NOT_RESOLVABLE field exists.
```

Checkpoint/family amendments in force: **U1** (NEUTRAL), **S1** (NEUTRAL), **C1** (NEUTRAL),
**C2** (TIGHTER), **C5** (**NARROWING** — transcribed from the family ledger's own label at
`cf-voldir-001.md`; TIGHTER in L-23's three-way vocabulary), **C6** (TIGHTER), **C7** (retire the
canonical power threshold, NEUTRAL — the authority for §8, §9 and AMENDMENT-4; omitted from this
list in an earlier draft). **C7 supersedes ONE clause of C6**: C6's instruction to book an
unresolvable grid as `NOT_RESOLVABLE` is retired, because C7 forbids emitting that flag anywhere.
The obligation behind it survives — the phase-(b) amendment states the expected resolution of its
grid at every ladder rung before it runs (§4.1) — so what C7 removed is the label, not the duty.

---

## §15 Artifacts

| Path | Content |
|---|---|
| `python/src/xen/resolution_basis.py` | shared, tested basis and deterministic expected-resolution generator |
| `screen_code/` | inherited SPDR-014 event module, layer module, 4 device modules, metrics layer, control module |
| `results/resolution_basis.json` | arm-C `c` bands derived from SPDR-018: `cells`, `distinct_n`, `horizon_summaries`, `input_filter`, `row_counts` incl. exclusions by reason, the complete `source_ci_rule` (SPDR-018 §6.2's own text), generator + source SHA-256 |
| `results/expected_resolution_prior.json` | complete 1,296-row base-grain declaration inputs; two known signed parent cells and explicit unknowns elsewhere |
| `results/expected_resolution.json` | dated pre-implementation expansion with input/source SHA-256 pins; null expected n/MDE where no parent signed arm exists |
| `results/zones.parquet` | every zone: anchor, width, source, `z`, `H`, breach outcome |
| `results/episodes.parquet` | every episode: event type, side arm, breach bar, entry ts/price, exit ts/price/reason, `r` bps, layer tags |
| `results/metrics_by_cell.parquet` | per cell: `p`,`W`,`L`,`W_L`,`p_be`,**`log R`**, block + iid MDE in log units, CIs, CI width, ladder detection rates, band label (CI-relative), evidence class, **`p_event`** (covariate, never a filter), `p_flat`, κ, `n`, homogeneity, cost overlay flagged `DISCLOSURE_ONLY` |
| `results/layer_deltas.parquet` | Δ`log R` per stage vs L0, with the L2 interaction term |
| `results/parent_parity.json` | reproduction of SPDR-014's published cells + tolerance |
| `results/controls.json` | all controls: percentiles, **null means and quantiles**, **plant curves** (P-24), derangement fixed-point counts |
| `results/selection_check.json` | L-51 rows for every reported selected subset (L2, L3, L5, event type, above/below median mde50), each with complement key, payoff-scale ratio, sign-share differential and excluded-set mean-minus-median gap. HARD schema only; no pass value |
| `results/unit_pin.json` | measured σ̂ and ATR20 medians (computed, not asserted) |
| `results/resolution_ladder.parquet` | per cell: realised `n`, **realised effective sample size**, block MDE, CI width, detection rate at each rung **per plant operator**, `mde50`/`mde80`/`mde95`, the `n` required at each rung, and — on the **same row** — the stratum's **predeclared expected `n` and expected `mde50`** from §8. **No adequacy flag** |
| `results/golden_traces.json` | G1–G8 |
| `results/integrity_selfcheck.json` | check-count reconciliation, fences, causality, parity, pin, identity, `log R` definition, cost isolation, code sha256 |
| `screen.md` | neutral quantification (subordinate) |
| `analysis.md` | **fresh-context analyst — binding read** (SPDR stage 5, mandatory) |
