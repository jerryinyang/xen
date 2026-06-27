# Cold Autopsy — Xen Research Programme (Phases 004–018)

**Date:** 2026-06-22
**Author:** Cold-review synthesis (independent re-derivation from primary evidence)
**Status:** Reflective synthesis only — predeclares nothing, reads no data, touches no holdout. Intended as an independent autopsy and next-family recommendation, to be read alongside (and partly red-teaming) the [2026-06-19 two-family reflection](2026-06-19-two-family-retrospective-reflections.md) and the [Phase 018 retrospective](../checkpoints/2026-06-20-018-capgeo-exit-geometry/retrospective.md).

**Scope reviewed:** master INDEX, multiplicity-registry, test-read-ledger, the 2026-06-19 two-family reflection, the Phase 018 retrospective, the CF-CAPGEO-001 / CF-HA-HARAMI-001 family specs, and primary experiment artifacts EXP-047, EXP-060B, EXP-081, EXP-083, EXP-084 (plus registry-level numbers for EXP-021/028/030/068/071/074). Three families taken to closure: **CF-AVWAP-001** (closed ANCHOR_MOVE_FLAT), **CF-HA-HARAMI-001** (closed CLOSE_FAMILY), **CF-CAPGEO-001** (retired NOT_CONFIRM, 2026-06-22).

Up front: **the programme's discipline is real and the artifacts are honest.** Holdout never released (one spent shot, INCONCLUSIVE), 0 counted TEST reads in the entire last family, every negative retained. The job of this review was to find where the *narrative* overreaches the *numbers*. It found one material soft-pedal and several places where the most recent evidence (Phase 018) has already corrected the older synthesis (2026-06-19) — which itself is a tell.

---

## 1. The invariant failure mode

**Falsifiable claim:** *Across all three closed families, the entry signal does not produce signal-conditional favourable price excursion beyond a matched random/control baseline. Every "edge" the programme found was a second-order distributional artifact (a relative directional reaction, or a median-location shift) that does not survive the conversion to a net, directional, out-of-sample mean.*

The families did **not** fail for different reasons — and notably, they failed for a *deeper* common reason than the 2026-06-19 reflection claimed. That document's headline invariant (§4.1) is *"edge and obstacle share one unfilterable mechanism."* The Phase 018 evidence sharpens and partly **overturns** that: the more fundamental fact is that **there was no first-order move-edge to filter in the first place.**

The two independent, matched-control measurements that establish this:

- **AVWAP (EXP-047, Finding 4):** event lifetime median MFE ≈ matched-control MFE on every domain — 1h 24.0 vs 24.9, 2h 35.9 vs 31.6, 4h 64.5 vs 59.1 bps. Verbatim: *"the bounce trigger does not access privileged move sizes."* The available peak is 5–9× the cost floor (51/51 cells) — but so is the random control's.
- **Harami (EXP-081, Finding 3, 5-year disjoint data):** per-cell paired difference (real − within-cell random) for favourable availability `MFE_med` is **−0.140 ATR, real>random in only 17/46 cells** for harami, and **+0.061, 28/46 (coin-flip)** for AVWAP. Outcome-median edge over random: **23–25/46 ≈ chance.**

So the binding constraint that Phase 018 located by exonerating the exit (EXP-084 exit-invariance: none of 11 exit arms had a positive OOS CI_low) is upstream: **signal-conditional favourable availability ≈ random.** There is nothing for any exit, cost model, or sizing rule to harvest because the entry never accessed a privileged move.

What the "real edges" actually were, and why they don't contradict the invariant:
- **AVWAP's edge was *relative-directional, not availability*:** a matched-control reaction excess (EXP-021/028: +5.78/+23.38/+69.02 bps gross) — real, but tiny and **cost-dominated** (EXP-030 net: 5m −6.74, 1h −6.04, 4h +2.60 spans zero). A 5–69 bps gross reaction against a ~16 bps round trip on BTC, ~5–7 bps floors elsewhere.
- **Harami's edge was *median-location, not availability*:** real on **old** data (EXP-060B: M3 1.158 vs RM3 0.380, beats random 85/99) but **mean-killed by a shared exhaustion-bimodal tail** (EXP-068: winsorized-mean positive in 46–73 cells vs raw-mean positive in only 10–14; EXP-074: `msofar_atr` separates the q05 loss tail at rank-biserial 0.68–0.80).

---

## 2. Ruled-out vs never-tested

| **Empirically ruled out (measured, with power)** | **Never tested at all** |
|---|---|
| AVWAP bounce as a net strategy under *any* registered lever (selectivity EXP-035 0/9; instrument-selection necessary-not-sufficient; exit EXP-037/039; anchor EXP-047) — triply-confirmed cost-dominated | Any entry **screened first for a real availability/move-edge** (both families' entries were chosen for pattern logic; availability was only measured *retrospectively*, and found ≈ random) |
| Exit / capture geometry as the binding lever (EXP-084 **exit-invariant**: 0/11 arms positive OOS CI_low) | **Non-price information**: order flow, microstructure/liquidity imbalance, term structure, carry, cross-asset lead-lag. Everything tested is single-instrument OHLCV |
| Data-derived exits beating conventional (EXP-083: D1/D2/D3 earn **no** distinctive TRAIN support; absent from the only S2-PASS cell) | **Cross-sectional / relative-value** signals. Every edge measured was single-instrument time-series |
| Favourable-target & third-barrier levers on both substrates (EXP-056/058/064/065 — empty) | **Regime/liquidity-conditioned entry selection** (named as a seed in EXP-084 §7, never run) |
| Entry-parameter tuning lifting a gross edge (EXP-046: ~1–2 bps vs 5–20 bps floors) | **Directional forecasting / ML / multi-feature entry models** — untouched |
| Anchor placement (EXP-047: k=1.0 coincides with running extreme 94.6–98.5%) | **The global holdout** — never released on any family (one INCONCLUSIVE shot on old EURUSD-4h, EXP-032) |
| Conditioning by %completion / session / vol (EXP-035: 0 qualified dims) | **AUDUSD-1h strong-harami at a counted read** (n=988; the single well-powered S2-PASS cell, cost-gated to NET_INCONCLUSIVE, never carried) |
| Risk-sizing as a creator of edge (Phase 018 L3: ATR-normalised returns are already fixed-risk; sizing is a near-global rescale, changes no sign/ordering) | |

The asymmetry is stark: the programme has **exhaustively** ruled out the entire downstream stack (exits, costs, conditioning, anchors, sizing, substrate-within-family) on two price-pattern entries, and has **never** varied the one axis the invariant implicates — the entry's information source.

---

## 3. The decisive read: (a) / (b) / (c)?

**For the two entries carried to closure, on the economic (net directional mean) endpoint: this is (a) — no effect — and it is now established *with power*, not assumed.** EXP-084 returned `NOT_CONFIRM` at n_oos=151 (explicitly **not** INCONCLUSIVE), with the cleanest possible mechanism: positive only in the [50–70%] selection-overlap folds (+1.866/+0.068), negative in **all three** genuinely held-back folds (−1.002/−1.250/−0.754). Availability ≈ random is independently confirmed across 46 cells (EXP-081) and on the AVWAP family (EXP-047).

**The real effects that exist are (b) — right effect, wrong (non-economic) endpoint:** AVWAP's relative-directional reaction and the harami's median-location shift are genuine, but they are *relative/median/shape* effects scored against a *directional-mean* tradability bar they structurally cannot clear. The programme has, to its credit, looked at directional, median, tail, and availability endpoints — so (b) is not "they never measured the right thing"; it is "the thing that's real isn't economically convertible."

**At the programme/family-selection level, the forward question is (c) — untested:** the entire class of "entry with a *demonstrated* availability edge / non-price / cross-sectional information" has never been touched.

**The one substantive red-team disagreement with the written synthesis.** The 2026-06-19 reflection (§0, §3.1, §3.5) and the family specs repeatedly assert *"both families had a real edge"* and *"the harami carries a real median edge reproduced on 5-year data."* The primary artifact is more careful than its own summary: EXP-081 Finding 3/4 shows that on the 5-year disjoint data, under the exit-agnostic geometry, the harami's separation from random is **25/46 cells ≈ chance** (median +0.135 vs random's +0.085 — a +0.05 ATR gap), and favourable availability is *below* random. That is a long way from EXP-060B's 85/99. The drop is confounded (different dataset **and** different exit geometry, so it cannot be cleanly called a non-replication), but **either way the new-data evidence does not support a robust median edge over random.** The reflection rounds a marginal, geometry-dependent, partly-underpowered (8/14 lead cells were 4h, n=108–194; EXP-060B W1) old-data result up to "a real, replicated edge." The honest read is closer to: *a real edge on old data under one geometry that is marginal-to-absent on fresh data and reverses OOS.* This matters because it pushes the decisive call further toward (a) than the synthesis admits.

---

## 4. Recommended next family

### Primary — change the entry's *information source*, not its pattern

**Hypothesis (one falsifiable sentence):** *An entry conditioned on cross-sectional relative strength (a basket-relative momentum/divergence rank across the 16-instrument universe) produces signal-conditional favourable excursion that beats a matched within-instrument random control by ≥1×SE in ≥5 cells over ≥3 instruments on TRAIN.*

**Why the evidence points here (not a generic prior):** the invariant in §1 is specifically that *single-series price-pattern conditioning yields ≈-random availability* — proven twice with matched controls (EXP-047, EXP-081). The data does not say "price is unpredictable"; it says "the information in one instrument's own OHLCV geometry does not concentrate favourable moves." The minimal, data-respecting move is to inject **information not present in the single series** while reusing the entire validated stack. Cross-sectional rank is the cheapest such injection: it is constructible from the existing 16×1m dataset with **zero new collection**, and it is the one orthogonal axis the programme has never spent a single experiment on.

**Cheapest first diagnostic (mirrors EXP-081/047/060B exactly; 0 slots, 0 OOS reads, TRAIN-only):** run the **availability screen first** — the very read that, in hindsight, would have killed both prior families for a few seconds of gross compute. Compute lifetime MFE/MAE for the cross-sectional-conditioned entries vs the **same matched-random control on the same substrate**, paired per cell, on the TRAIN sub-split. Report the per-cell `MFE_med` Δ-over-random and the cells-beat-random count — the EXP-081 Finding 3 table, re-pointed at the new entry. **This inverts the programme's historical mistake of measuring availability last.**

**What falsifies the recommendation:** if the cross-sectional entry reproduces the ≈-random pattern (median `MFE_med` Δ ≤ 0, or real>random in ≤ half of cells — i.e., it looks like the 17/46 or 28/46 results), cross-sectional price information is exonerated too, and the programme routes to the runner-up *without spending a read*.

### Runner-up — order-flow / liquidity-imbalance conditioned entry

**Hypothesis:** *Entries at significant tick-volume / volume-at-price imbalance extremes show favourable availability beyond a matched-random control.* Same cheap availability screen as the first diagnostic. **Lower priority** because (i) the programme already found tick-volume-weighted construction inert once (EXP-046 α-exponent), and (ii) tick volume is broker-dependent — but it brings genuinely orthogonal *flow* information, which price-geometry does not contain.

**Explicitly de-prioritized:** the Phase 018 carry-forward's "AUDUSD-1h harami fresh read" thread. It is the least-dead *existing* signal (n=988, the one well-powered S2-PASS cell), but EXP-083's own advisory is right — spending read #1 there tests *conventional exits on one cell of an already-exhausted substrate* whose median edge is known-marginal and mean-≈0. Low expected information for an irreplaceable read. It belongs in the file drawer as a characterized near-miss, not as the next family.

---

## 5. Confidence and blind spots

**Strong (high confidence):**
- *Availability ≈ random* — two independent families, two independent matched-control designs (EXP-047 Finding 4; EXP-081 Finding 3). This is the most robust finding in the programme.
- *Exit/capture geometry is not the binding lever for these signals* — EXP-084 exit-invariance (0/11 arms positive OOS CI_low) is direct and clean.
- *The one well-powered OOS read is a true negative* — EXP-084's selection-overlap-vs-fresh-fold reversal is unambiguous and correctly adjudicated NOT_CONFIRM, not INCONCLUSIVE.

**Thin (flag as weak):**
- **The OOS evidence base is tiny in absolute count.** The entire programme rests on exactly **two** out-of-sample reads — EXP-032 (n=27, INCONCLUSIVE) and EXP-084 (n=151, NOT_CONFIRM). Each is clean, but two reads is a thin foundation for "nothing works."
- **The harami-edge "replication" is confounded** (EXP-060B old/V2A vs EXP-081 new/exit-agnostic) — the new-data median edge can be called marginal, but the drop *cannot* be cleanly attributed to data vs geometry.
- **4h strata are chronically underpowered** (n 32–194 throughout); much of the *apparent* harami edge lived in exactly these cells (EXP-060B W1: 8/14 lead cells 4h). The (c)-underpowered component in the harami's old-data story is real.

**Where this review is extrapolating (explicit):** the §4 recommendation that cross-sectional or flow information *will* beat random availability is a **prior, not a finding** — the programme has never tested it. The data tells us decisively what *does not* work (single-series price-pattern entries → ≈-random availability) far more strongly than it tells us what *will*. The honest framing for the operator: the next family is a **bet on a new information axis justified by the elimination of the old one**, and the first diagnostic is explicitly designed to kill that bet cheaply if it's wrong. The one thing the evidence does *not* support is another entry whose distinguishing feature is its price-geometry entry pattern — that lever is exhausted, twice over, with the holdout still sealed to prove it when something finally clears the availability screen.

---

## 6. Source map

| Claim | Primary source |
| --- | --- |
| Availability ≈ random (AVWAP) | EXP-047 Finding 4 (`python/experiments/EXP-047/report.md`); event MFE ≈ control MFE all domains |
| Availability ≈ random (harami, 5y) | EXP-081 Finding 3 (`python/experiments/EXP-081/results.md`); `MFE_med` Δ −0.140 (17/46), AVWAP +0.061 (28/46) |
| Harami median edge over random (old data) | EXP-060B (`python/experiments/EXP-060B/report.md`); M3 1.158 vs RM3 0.380, 85/99 |
| Harami median ≈ chance on 5y / outcome shape | EXP-081 Finding 4; median +0.135 vs random +0.085, 25/46; 33/46 median>mean |
| AVWAP gross reaction & cost-domination | EXP-021/028 (gross +5.78/+23.38/+69.02 bps); EXP-030 (net 5m −6.74 / 1h −6.04 / 4h +2.60 spans zero) — multiplicity-registry |
| Harami mean-kill / tail driver | EXP-068 (winsorized 46–73 vs raw 10–14); EXP-074 (`msofar_atr` q05 rank-biserial 0.68–0.80) — INDEX |
| Data-derived exits unsupported on TRAIN | EXP-083 (`python/experiments/EXP-083/results.md`); 4 S2-PASS all conventional, 98.2% died at gross screen |
| Exit-invariant OOS reversal | EXP-084 (`python/experiments/EXP-084/results.md`); 0/11 arms positive OOS CI_low; fresh-fold reversal |
| Sizing second-order; exit exonerated | Phase 018 retrospective §3–4 (`../checkpoints/2026-06-20-018-capgeo-exit-geometry/retrospective.md`) |
| Prior synthesis (red-teamed here) | `2026-06-19-two-family-retrospective-reflections.md` §0/§3.1/§3.5/§4.1/§6 |

*Reflective document. Mechanical verdicts, per-experiment cards, and gate records live in the cited checkpoints, family indexes, and experiment artifacts; this file re-derives their numbers independently and adds no new measurement.*
