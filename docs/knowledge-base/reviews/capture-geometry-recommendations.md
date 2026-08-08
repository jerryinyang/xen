# Capture Geometry — Diagnosis & Design Recommendations

> **HISTORICAL (pre-INFR-022).** Cost-floor language below is chapter-01/02 apparatus. Live
> programme is **zero-cost** (L-62); do not re-introduce cost floors as disposition rules.

**Purpose.** Independent-review brief: what is proven to work (and the unifying concepts
behind it), what is proven ineffective, and the genuine unexplored gaps — so new capture
designs are built on residual conversion, not exit rescue.

**Companion.** [capture-geometry-review.md](capture-geometry-review.md) (modality extraction,
per-arc observations, mechanism catalogue).

**Status.** Diagnosis and recommendations only. No new claims; no new experiments. Distilled
from Chapters 01–03 knowledge base and archives (2026-07-16).

---

## 1. Diagnosis

The programme did not mainly fail at “picking the wrong stop.” It failed at **treating
capture as a rescue layer**. Across chapters, three different problems were repeatedly
mislabelled as one “capture geometry” problem:

| Mode | What is actually broken | What exit design can do |
| --- | --- | --- |
| **A. No conditional availability** | Signal path ≈ random path | Nothing. Exits reallocate noise. |
| **B. Availability without residual** | Peak exists; net after cost/horizon ≤ 0 | At best reshuffle losses; cannot raise first-order edge |
| **C. Spurious capture** | Look-ahead, print, entry-seam mismatch | Looks like success until causality/controls are honest |

**The unifying error:** building or retuning exits before proving Mode A is cleared *and*
the traded fill event matches the measured object.

**The unifying success condition** (never fully assembled into a tradable system, but
consistently predictive):

> Capture works only as **conversion of a *conditional, cost-relative, causally fillable*
> residual** — not as conversion of raw MFE, and not as repair of a dead entry.

That residual has four necessary properties:

1. **Conditional** — Δ over matched random / oscillation / phase-shift control
2. **Cost-relative** — capturable move large vs round-trip *at the chosen horizon*
3. **Object-matched** — entry fill event = measured availability event
4. **Causal** — exit levels from `≤ t−1` only; no vectorized favourable-index look-ahead

Whenever any one of these was missing, every exit family looked “flat,” “exit-invariant,”
“cost-dominated,” or “fake.”

### 1.1 Where this diagnosis came from

| Stage | Belief | What moved it |
| --- | --- | --- |
| Early AVWAP | Edge weak / params wrong | Gross bounce real; net cost-dominated |
| Phases 010–011 | Exit choice can rescue absolute net | EXIT_FLAT; per-instrument training empty membership |
| EXP-047 | “Move is too small” | Refuted: MFE ≈ 5–9× cost floor; event MFE ≈ control |
| Naming | Binding wall = capture geometry | Phase 013 → CF-CAPGEO-001 thesis |
| Phase 018 | Capture geometry is *the* lever | Exit-invariant NOT_CONFIRM; availability ≈ random |
| Re-frame | Bottleneck upstream for price-geometry entries | P-01 / P-02; availability-first |
| Ch. 02–03 | Same abstract wall, new vehicles | Cost/horizon, entry-seam, structure, print artifact |

Full modality extraction: [capture-geometry-review.md](capture-geometry-review.md).

---

## 2. What is proven to work (and the core concepts)

These are not “winning strategies.” They are **design truths that repeatedly moved the
reading in the right direction**.

### 2.1 Fail-cheap order: availability → residual → capture → OOS

**Evidence.** CAPGEO ~98% of candidates died at the gross screen for 0 counted reads;
CF-MR-003 availability-admit then powered NOT-TRADABLE; CF-CSRR-001 retired at availability
before exit work.

**Core concept.** *Capture is a second-order operator.*  
Design the sequence so Mode A dies before you invent barriers.

### 2.2 Cost–horizon co-geometry is often the real “exit”

**Evidence.** Same ~0.28 ATR gross looks lethal on 15m and cleaner on 4h because RT/ATR
fraction changes, not because the signal is stronger (CF-MR-001 domain geometry). CF-MR-003:
faster TF multiplies episodes and shrinks capturable move against **fixed** RT cost.

**Core concept.** *The binding barrier is frequently the cost floor projected onto hold time,
not the stop you drew.*  
Any serious capture design must treat **(horizon, cost unit, ATR unit)** as one object.

### 2.3 Simple, parameter-light exits dominate creative ones under power constraints

**Evidence.** AVWAP E1–E5 flat vs fixed-horizon reference; FH recovered ~+16 bps vs BTC on
EURUSD-4h TEST; CAPGEO data-derived D1/D2/D3 earned no distinctive TRAIN support;
parameterless HA trail was closest to FH (within noise).

**Core concept.** *Capture efficiency beats capture sophistication when n is small and the
residual is thin.*  
Prefer fixed-horizon / single-level proactive targets over multi-parameter trails and “smart”
structure exits — *after* residual exists.

### 2.4 Asymmetric geometry and partials change shape, not magic expectancy

**Evidence.** Harami: PARTIAL-V2A and `/ADV-NONE` improved median; trails / fav-target alts /
third-barrier did not; `/ADV-NONE` maximized median and manufactured a mean-killing left tail.

**Core concept.** *Exit geometry is a distribution operator (mean / median / tail / hit-rate),
not a scalar “make it green” knob.*  
Design for joint (expectancy, median, tail), with separability: if fixing the tail kills the
median, you have no tradeable object.

### 2.5 Proactive, path-native targets beat reactive close-rules *as a vehicle class*

**Evidence.** EXIT-RCT ≫ RSI-revert-on-close on the contaminated engine; causalized RCT still
net-negative absolute; form-1/form-2 exit-set fidelity mattered for honesty (L-14) though not
for rescue of CF-MR-004.

**Core concept.** *Exit should be the mechanism’s completion event (reversion to target,
segment end, episode clear), not a generic trailing decoration.*  
Mechanism-native ≠ edge-creating. Causal provenance is non-negotiable (L-01).

### 2.6 Entry–exit object identity

**Evidence.** CF-MR-004: faithful exits still fail because limit-touch ≠ confirmed-breach;
XENA-003: “edge” is passive-limit print; CF-VOLHARV-001: inventory censoring is the capture
failure.

**Core concept.** *You capture what you conditioned on.*  
If measurement conditions on confirmed depth, trade confirmed depth. If harvest needs free
inventory, do not hard-cap the structure.

### 2.7 Exit-invariance as a diagnostic, not a disappointment

**Evidence.** EXP-084: 0/11 exit arms positive OOS CI_low → exit lever exonerated; upstream
was empty.

**Core concept.** *If sweeping exits does not move the verdict, stop sweeping exits.*  
That is a positive scientific result: the lever is empty.

---

## 3. What is proven ineffective

Group by *why*, not by family name.

### 3.1 Ineffective as rescue of a dead or random-availability entry

- Per-instrument exit grids (FH, MAD, RR, trail, partial, VP, data-derived)
- Anchor / band / conditioning / sizing retunes to “unlock” net
- CAPGEO reverse-engineered barriers from non-conditional return structure

**Why.** Mode A or B. Exits cannot manufacture Cov(signal, future residual).  
**Pitfall.** P-02 — never tune the downstream stack on a dead entry.

### 3.2 Ineffective as sophistication without residual

| Class | Status |
| --- | --- |
| Structure trails (HA, Last-X, ZigZag ratchet, uncapped) | Systematically weak vs benchmark |
| Third-barrier time/event variants | Powerless lever on both harami substrates |
| Fancy favourable targets (VP / magnitude ladders) | Helps ambient substrate drift as much as signal |
| Data-derived triple-barrier from MFE/MAE quantiles | Collapses to wide MAE_q90 stop; re-derives trap geometry when catastrophe is continuous not modal |
| `m_anti` / antimode “cut the minority catastrophe” | Dormant almost always; continuous tail, not separable mode |
| Vol-adjusted sizing as capture | Near-global rescale; no sign creation |

### 3.3 Ineffective as vehicle forms (even when residual or gross exists)

| Vehicle | Why dead |
| --- | --- |
| Passive limit at the measured band for MR fades | Adverse selection / print artifact (P-10) |
| Monthly-capped / hard inventory harvest | Cap-lock + censored inventory erases harvest (P-12) |
| Contaminated proactive limits (`rct[di]`) | Mode C false positive (P-05 / L-01) |
| Ladder scale-in read via per-leg CI | Form reproducible by random timing (P-11) |
| HTF-DI exit tier after sub-cost entry | Trail cannot manufacture a 10× magnitude gap (P-14) |

### 3.4 Ineffective evaluation habits

- First-hit `r` on symmetric barriers for asymmetric/partial systems
- Median-only ranking of asymmetric geometries
- Pooled NET_POS across low-n deferred cells
- Gross “pass” as tradability
- Building nulls around signal-derived targets
- Trusting numeric re-derivation without causal-provenance audit

---

## 4. Recommendations: design capture around the proven cores

### 4.1 Operating principles

1. **Gate Mode A first** — TRAIN-only Δ MFE/path residual vs matched control; multiplicity-aware.
2. **Then Mode B budget** — define *minimum capturable residue*:

   \[
   R^* = \text{capturable move at horizon } H - \text{RT cost in same unit}
   \]

   If \(R^*\) is not clearly positive under conservative cost *before* exit search, do not
   search exits.
3. **Then object match** — write the entry fill definition and the availability event as one
   sealed pair.
4. **Then causal mechanism-native exit** — one primary completion event + one simple fallback.
5. **Then shape co-primary** — expectancy ∧ median ∧ explicit tail; separability gate before
   any TEST.
6. **Exit-invariance battery as audit** — 3–5 simple arms; if all fail together, stop
   (upstream). If one family separates, that is the only arm worth costing OOS.

### 4.2 Recommended capture stack (when residual is real)

Use this order, not a combinatorial surface:

| Stage | Design | Rationale from evidence |
| --- | --- | --- |
| **C0 Primary** | Mechanism completion target (proactive, causal, `≤t−1`), single level | RCT-class idea without look-ahead; form-1 class for moving anchors |
| **C1 Fallback** | Fixed-horizon / adaptive time-cap calibrated to mechanism tempo | FH beat clever trails under power; third-barrier alts didn’t help |
| **C2 Risk** | Bound downside to protect mean (not `/ADV-NONE` as default) | ADV-NONE median trap |
| **C3 Optional scale-out** | At most one partial schedule (e.g. even thirds of *measured residual*, not fantasy RR) | PARTIAL-V2A only clear positive surface lever |
| **C4 Ban by default** | Structure trails, VP targets, multi-param time-stop grids, data-derived MAE_q90 monsters, sizing “fixes” | Proven low-yield |

**Explicit ban list for new designs** (unless a new D0 claims a genuinely new mechanism):

- Exit rescue on non-admitted availability
- Passive-limit entry on MR fade measured as confirmed-breach
- Cap-locked multi-week inventory harvest
- Re-deriving barriers from train quantiles of a random-like MFE
- Any favourable limit using same-bar close information
- Resurrecting EXIT-RCT result numbers (P-05)

### 4.3 How to design the primary exit (concrete recipe)

When (and only when) Mode A + \(R^*\) clear:

1. **Define the completion event in price space from the mechanism**
   - Reversion → causal equilibrium / completion price
   - Continuation → measured target level frozen at entry from `≤t−1` structure
   - Harvest → *within-episode* clear (rolling anchor, no hard monthly lock)

2. **Size the target from residual, not from aesthetic RR**
   - Target ≤ median *conditional* favourable path under the same fill object
   - Stop / adverse bound sized so mean is not hostage to continuous left tail
   - Prefer modest fav / bounded adv over wide-stop modest-target trap (~9 ATR MAE_q90 lesson)

3. **Co-design H with cost**
   - Choose the coarsest domain where \(R^*\) clears power floors
   - Do not “go 15m for more trades” without recomputing capturable move
   - Pin money units at every screen→graduation seam (L-21)

4. **Fill model**
   - Market / next-open for confirmed events
   - Native m1 for limit/stop claims
   - Discriminating control for any limit vehicle (re-price to adjacent open)

5. **Audit**
   - Exit ablation (C0 vs C1 vs random-hold vs no-stop)
   - Collapse fraction under destroy controls
   - Per-fold freshness if any selection window exists
   - Causal-provenance pass on every verdict-bearing exit column

### 4.4 Four-layer contract (write this at D0, not after)

```text
Layer 0  Availability object     (what residual? vs which control?)
Layer 1  Fill object             (what event is traded? ≡ Layer 0?)
Layer 2  Cost-horizon budget     (R* at H*; unit pin; RT on binding leg)
Layer 3  Capture operator        (C0 completion + C1 time + C2 bound + optional C3 partial)
Audit    Shape + separability + exit-invariance + causal tripwire
```

**Default Layer-3 stack when Layers 0–2 pass:**

1. Causal mechanism-completion target (one level)
2. Mechanism-tempo time stop
3. Bounded adverse (mean-protecting)
4. At most one simple partial schedule
5. Hard ban: trails, VP, quantile-MAE monsters, ADV-NONE default, passive band limits

### 4.5 Success criteria for a new capture design (reviewer-facing)

- Clears Mode A with power
- \(R^* > 0\) under conservative cost before any exit search
- Primary exit is mechanism-native and causal
- Joint shape co-primary passes separability
- Exit-invariance battery does **not** all fail (or if it does, you stop and report Mode A/B)
- OOS with freshness disclosure; no selection-overlap story
- No counted TEST read until separability + cost residual clear

---

## 5. Genuine unexplored gaps

These are open **because** the programme correctly killed adjacent dead ends — not because
they were never mentioned.

### Gap 1 — Capture of a *true* conditional residual

Everything exit-related on AVWAP / harami / CAPGEO was largely Mode A or thin residual.

**Unexplored:** apply the C0–C3 stack to a signal that first clears availability on a **new
information source** (Bybit universe, orderflow, cross-asset, non-price).

**Built from:** availability-first + “exit only after residual.”

### Gap 2 — Cost-optimal horizon as the capture object

Horizons were often chosen first; cost geometry measured after.

**Unexplored:** treat \(H^* = \arg\max R^*(H)\) as the primary design variable, with exit
secondary.

**Built from:** CF-MR-003 / RCT domain cost lessons.

### Gap 3 — Object-matched confirmed-breach vehicles

CF-MR-004 closed limit-touch (P-10).

**Unexplored:** trade the **open after confirmed close-breach** (or stop-through) with form-1
completion exit — no resting limit at the band.

**Built from:** entry-seam identity + form-1/2 fidelity.

### Gap 4 — Within-episode, uncensorable harvest structure

CF-VOLHARV-001 failed on caps/inventory, not on VR substrate.

**Unexplored:** rolling-anchor, episode-clearing, no hard monthly inventory lock; harvest ends
when residual mean-reverts.

**Built from:** structure-failure diagnosis — not a re-grid of bands.

### Gap 5 — Shape-separable capture (joint mean/median without median trap)

Harami: partials help median; unbounded downside kills mean. CAPGEO: continuous tails defeat
antimode stops.

**Unexplored:** capture rules that **explicitly optimize a constrained objective**:

- maximize median (or expectancy)
- s.t. worst-q05 or left-tail mass bound
- s.t. separability (tail fix must not zero the median)

Not “ADV-NONE vs 1:1 grid,” but a **constrained shape program** with predeclared acceptance.

### Gap 6 — Capture-ratio estimand (when Mode A passes)

Most adjudication used absolute net expectancy.

**Unexplored primary estimand when residual exists:**

\[
\text{capture ratio} = \frac{\text{realized exit PnL}}{\text{path MFE (or residual MFE)}}
\]

plus net expectancy. This asks the real capture question AVWAP named after EXP-047, without
pretending MFE is tradable.

### Gap 7 — Causal proactive completion with tripwired provenance

The *class* (mechanism completion limit) remains the best native MR vehicle conceptually; the
EXIT-RCT *instance* was contaminated and is banned as a result (P-05).

**Unexplored:** same class under cTrader/Nautilus causal engine, with future-destroy tripwire,
on a residual-admitted MR object that is **not** bare RSI-2 on the exhausted dataset.

**Built from:** proactive > reactive vehicle lesson + L-01 fix + P-05 ban.

### Gap 8 — Two-sided / magnitude capture (not directional)

Directional single-series is dead (P-01). CF-VOLEXP-001 had only a tail hint.

**Unexplored:** capture geometry for **range / vol expansion** endpoints (two-sided cost
model), where “favourable” is |move| not sign.

**Built from:** availability 2×2 open cell + harvest cost model.

### Gap 9 — Portfolio-level capture

Portfolio work (EXP-095 MTM, XENA binders) was mostly risk/selection.

**Unexplored:** whether **exit timing** under concurrent positions (de-risk, flatten correlated
residuals) improves *portfolio* capture when per-trade residual is thin but diversified.

**Built from:** MTM lesson + “sizing can’t create edge” (portfolio exit ≠ position sizing).

### Gap 10 — Explicit non-gaps (do not re-open)

These are **closed negative space**, not unexplored space:

- Another AVWAP / harami exit grid
- Another data-derived barrier from non-conditional MFE
- Another passive-limit MR fade
- Trail parameter sweeps
- Sizing / vol-adjust “to make net positive”
- Reopening EXIT-RCT numbers or CF-CAPGEO-001 as a rescue of frozen dead entries

---

## 6. Bottom line

| | Content |
| --- | --- |
| **Proven** | Capture is a **conditional residual converter** under **cost–horizon geometry**, with **object-matched fills** and **causal, mechanism-native completion**. Simple exits and shape-aware partials are the only surface levers that ever behaved coherently. |
| **Proven ineffective** | Exit creativity; trail/VP/third-barrier sophistication; data-derived barriers on non-conditional entries; passive-limit “capture”; cap-locked harvest; any downstream tune on Mode A failure. |
| **Genuine next work** | Not a better trail. It is (1) a real residual on a new information frontier or object-matched vehicle, (2) \(H^*\) chosen by \(R^*\), (3) constrained shape capture, (4) capture-ratio as estimand, (5) within-episode harvest structures — each as a **new D0**, never as re-opening CAPGEO / AVWAP / EXIT-RCT. |

**Default C3 stack when Layers 0–2 pass:** causal completion target → mechanism-tempo time stop
→ bounded adverse → optional one partial schedule. Ban trails, VP, quantile-MAE monsters,
ADV-NONE default, and passive band limits unless a new mechanism D0 justifies them.

---

## 7. Source pointers

| Need | Where |
| --- | --- |
| Full modality extraction | [capture-geometry-review.md](capture-geometry-review.md) |
| Family dispositions | [../families-explored.md](../families-explored.md) |
| Dead ends | [../pitfalls-ledger.md](../pitfalls-ledger.md) |
| Lessons with mechanism | [../lessons-and-amendments.md](../lessons-and-amendments.md) |
| Methods that earned keep | [../methodology-canon.md](../methodology-canon.md) |
| Phase 018 CAPGEO close | `archive/chapter-01-…/checkpoints/2026-06-20-018-capgeo-exit-geometry/retrospective.md` |
| Two-family retrospective | `archive/chapter-01-…/reflections/2026-06-19-two-family-retrospective-reflections.md` |

---

*Document written 2026-07-16. Append-merge at future rollovers if a Gap 1–9 design is tested
under a genuine availability-admitted residual.*
