# Phase 018 Retrospective — CF-CAPGEO-001 Data-Derived Exit / Capture Geometry

**Phase:** 2026-06-20-018-capgeo-exit-geometry
**Status:** **CLOSED at G-018 (2026-06-22) — HYP-004 `NOT_CONFIRM`. Family CF-CAPGEO-001 RETIRED (SCREENED — no net-tradable OOS capture geometry found).**
**Outcome:** the first **exit/capture-geometry-first** screen ran its full registered slate (HYP-001→004) and returned a clean negative: with the entries frozen and the exit made the sole open lever, **no exit produced a net edge out-of-sample, and the result is exit-invariant.** The binding constraint was never on the exit side.
**Discipline held:** 6 experiments (EXP-080–085), all post-governance **APPROVE**; **0 candidate slots, 0 counted TEST reads, global holdout never built/sliced/folded; determinism byte-identical throughout.**
**Companions:** family spec [`../../../signal-registry/candidate-families/cf-capgeo-001.md`](../../../signal-registry/candidate-families/cf-capgeo-001.md); [`design.md`](design.md); [`D0-predeclarations.md`](D0-predeclarations.md); amendments [001](D0-amendment-001-split-exp083-train-screen.md) / [002](D0-amendment-002-train-cost-readgate.md) / [003](D0-amendment-003-exp084-portfolio-read.md).

---

## 1. Objective vs outcome

Phase 018 asked one question (design §1): with entries **frozen** to four known substrates and the **exit as the only open axis** — derived in reverse from each system's realized return structure, then benchmarked against the conventional exits — **does exit/capture geometry contain a net-tradable edge the prior families missed?**

**Answer: no.** The exit lever is empty, and — more strongly — it is *demonstrably not the binding constraint.* The phase ran the full inverted-inference pipeline (readiness → characterize → derive → screen → cost gate → one OOS confirmation) and the edge died, with the final read showing the death is independent of exit choice. The two prior families closed because *the lever that removes the binding obstacle also removes the edge*; Phase 018 sharpens that into a cleaner statement: **when the exit is the only lever and the result is still flat and exit-invariant, the lever itself is exonerated — the obstacle is upstream, in the entry's signal-conditional favourable availability.**

The phase changed no holdout verdict and spent no counted read. It closed a research axis.

## 2. Experiment slate (as run)

| EXP | HYP | Role | Result | One-line |
| --- | --- | --- | --- | --- |
| **EXP-080** | 001 readiness | substrate/exit readiness on 5-year data | **READINESS_DELIVERED** | 184/192 substrate-cells READY; US500-4h + JP225-4h `COVERAGE_EXCLUDED` (4h index sparsity) → **46-cell member set**; D7 192/192 IN_BRACKET; null-FPR controlled n≥120. Initial SUBSTRATE_REFUTED on 2 audit defects → fixed, re-audit PASS. |
| **EXP-081** | 002 characterize | per-substrate realized return structure (TRAIN, gross) | **CHARACTERISATION_DELIVERED** | **Gross favourable availability ≈ random** (harami MFE below random 17/46, AVWAP coin-flip 28/46) — move availability is *not* the differentiator. Only structure = outcome **shape**: harami median +0.135 / mean ≈ 0.000 (CF-HA-HARAMI-001 signature on disjoint 5-year data); AVWAP roughly symmetric. |
| **EXP-082** | 003 derive | mechanical exit derivation (freeze the rule) | **DERIVATION_DELIVERED** | 552/552 valid triple-barrier exits; `derive_barriers` sha256-pinned. 3 candidates → 2 distinct definitions (D1≡D2 184/184); the catastrophe-engaging `m_anti` dormant 549/552 (continuous tail) → adverse leg reverts to a generic ~9 ATR stop sitting *at* the catastrophe edge = the trap geometry reproduced → **S2 is the crux.** |
| **EXP-083** | 004a screen | TRAIN candidate screen behind the separability gate (D0-amend-001) | **SCREEN_DELIVERED** | n_valid=26 = **4 S2-PASS (AUDUSD-1h harami, n=988, conventional arms) + 22 S2-DEFERRED (AVWAP-4h, n<120)**; 98.2% died at the cheap gross screen. **The data-derived D1/D2/D3 earned no distinctive TRAIN support.** Audit C1 (verdict-material) fix-and-rerun → re-audit PASS. |
| **EXP-085** | 004 cost gate | TRAIN gross→net cost read-gate on all 26 survivors (D0-amend-002) | **NET_SURVIVES** (per-stratum-masked) | 21/26 NET_POS — but the pooled count **masks heterogeneity**: all 21 are S2-DEFERRED low-n AVWAP-4h cells; the only well-powered S2-PASS stratum (AUDUSD-1h harami) is **NET_INCONCLUSIVE** (expectancy +, median −). Authorizes nothing — read-gate input to G-018. |
| **EXP-084** | 004b confirm | single sanctioned OOS confirmation, portfolio unit (D0-amend-003) | **NOT_CONFIRM** | AVWAP-4h basket (NZDUSD+USDCAD+USTEC, pinned `AVWAP-FH`, NET): **separates on TRAIN** (S2 finally adjudicated at pooled n=152 and PASSES) **but all three economic OOS legs FAIL**; the apparent edge is **selection-region overlap and reverses in the fresh folds**; **exit-invariant** (no arm clears zero). 0 counted reads (portfolio-aggregate disclosure). |

The slate ran in pipeline order; HYP-004 was split by D0-amendment-001 (TRAIN screen / counted-read confirm) and re-gated by D0-amendment-002 (TRAIN cost read-gate before any read) and D0-amendment-003 (portfolio reframing of the confirmation). All six carry post-experiment governance **APPROVE**.

## 3. The decision (why the family RETIRES, mechanically)

HYP-004 — the only slot/read-bearing hypothesis — closed `NOT_CONFIRM` at G-018. The registered slate (HYP-001→004) is complete; no further hypothesis is registered. The family retires on a three-link mechanical chain, each link independently established:

1. **There is nothing to capture (EXP-081).** Gross signal-conditional favourable excursion ≈ random. The raw material an exit would harvest is absent at the entry, so no exit can manufacture it.
2. **The exit lever is empty on TRAIN (EXP-083).** The data-derived exits earned no distinctive support; the only survivors were conventional arms on shape-unadjudicated low-n cells. The "data-derived beats conventional" thesis is unsupported on TRAIN.
3. **The edge does not survive OOS and is exit-invariant (EXP-084).** Pooled to finally adjudicate S2 — which **passed** (the geometry is well-behaved, the catastrophe tail genuinely non-residual for `AVWAP-FH`) — the basket still failed all three economic OOS legs; the only positive folds were the [50–70%] selection-overlap region and reversed in the genuinely held-back [70–100%] folds; **none of the 11 exit arms had a positive OOS CI_low.**

Exit-invariance is the decisive observation: if capture geometry were the unsolved lever, varying the exit would move the verdict. It moved nothing. The capture-geometry layer is therefore **exonerated, not solved** — ruled out as the binding constraint *for these signals*, not proven irrelevant in general.

## 4. Lessons learned

1. **Exit/capture geometry was not the binding constraint — the entry is.** The cleanest evidence the programme has produced that the bottleneck sits upstream. A capture-geometry-first phase was the right way to falsify the exit hypothesis cheaply, and it did.
2. **The strong-move filter is already the entry's best form, and it isn't a missing lever.** The harami substrates were the `/STRONG-STAT`-conditioned, `retained_p75` finals (EXP-068 lineage). Even strong-filtered, harami showed median-positive/mean-killed with no tradable move-edge. "Add a strength filter" is not an untried idea here.
3. **ATR-normalised returns are already fixed-risk sizing; risk-sizing is second-order.** Because the adverse stop was a near-constant ~9 ATR quantile, sizing-by-adverse-target reduces to a near-global rescale — it changes no sign or ordering. Sizing *amplifies* an existing conditional edge; it cannot *create* one (would require `Cov(1/stop, outcome) > 0`, absent here). Tail-capping via an enforced stop is an *exit*, already in the tested space, already exit-invariant.
4. **The separability gate did its job as the binding shape-guard.** With `ASS` demoted to discovery-only (G-017), S2 was the shape-guard, and it worked: it deferred honestly at per-cell n<120, was made adjudicable by pooling (n=152), passed on a genuine continuous tail, and never re-admitted the CF-HA-HARAMI minority-catastrophe shape. The negative is "no OOS edge," not "a shape the gate couldn't see."
5. **Disclose per-fold freshness whenever the WF initial-train window overlaps the selection region.** The frozen §D5 schedule tests [50–100%] while selection was on [0–70%]; the per-fold freshness flag is what exposed that the entire apparent edge lived in the overlap folds. Without it, a CONFIRM driven by selection-overlap would have been over-claimed. Carry this as a standing WF-disclosure requirement.
6. **"Unadjudicable" must not collapse into "failed" (governance catch).** Stage-4 caught a verdict-material defect: an S2 below its operating floor was being folded into a binding `NOT_CONFIRM`. The fix (HALT-to-operator) preserves the distinction between a leg that *fails with power* and one that *cannot be evaluated*. The floor held (n=152) so it did not fire, but the principle is general.
7. **Portfolio-aggregate disclosure answered the question at 0 counted reads.** Reframing the confirmation to a portfolio unit made S2 adjudicable *and* cost 0 reads (basket claim, disclosure against the 3 strata, caps preserved). A clean way to spend a phase's terminal question without burning the irreplaceable read budget — at the cost of a basket-only (not per-instrument) claim.

## 5. Carry-forward (binding into the next family / phase)

- **The next family is entry-side.** Its hypothesis must be: *a signal with demonstrable signal-conditional favourable excursion (a real move-edge), measured before any exit or sizing work.* Capture geometry and risk-sizing return as levers only **after** a first-order edge exists. New family ⇒ new G0/D0 — this is **not** a reopening of CF-CAPGEO-001's exhausted surface.
- **The single least-dead thread is AUDUSD-1h strong-filtered harami (n=988):** the only well-powered S2-PASS stratum in the whole phase, cost-gated to NET_INCONCLUSIVE (expectancy `exp_lo +0.057…+0.081`, median `med_lo −0.020…−0.047`) and **never carried to a binding read.** It is the closest any existing signal came to an edge without confirming. If revisited, it is a **new hypothesis with fresh registration** (the harami surface is closed; a counted read on AUDUSD-1h would spend read #1 of 2 on that stratum).
- **Methodology assets validated in live use:** the inverted-inference fail-cheaply pipeline (98.2% died at the gross screen for 0 reads); S2-as-binding-shape-guard with honest n<120 deferral; pooling-to-reach-the-floor (makes a portfolio claim); per-fold freshness disclosure; the cost read-gate sequenced before any TEST read; hash-pin-before-OOS legitimacy.
- **`ASS` stays discovery-only** (G-017 `DISCOVERY_ONLY`); no future binding decision rests on it without an EXP-079-style re-validation that adds a shape leg seeing the minority-catastrophe shape.

## 6. Integrity ledger

- **Experiments:** EXP-080, 081, 082, 083, 085, 084 — all post-experiment governance **APPROVE**.
- **Candidate slots:** 0 spent beyond the registered Phase-018 batch; **no new countable item.** All refuted/inconclusive items retained in `multiplicity-registry.md` (never deleted).
- **Counted TEST reads:** **0.** EXP-080–083/085 were TRAIN-only/synthetic disclosures; EXP-084 was a portfolio-aggregate **disclosure** against NZDUSD-4h/USDCAD-4h/USTEC-4h. **All 48 new-dataset strata remain 0/2 counted, open.** The three AVWAP-4h basket strata are now *disclosed* (basket-claim-only; future clean per-instrument read mildly weakened, EXP-032 precedent).
- **Holdout:** the final-30% global holdout was **never built, sliced, inspected, or made a WF fold** at any point in the phase. Not released.
- **Determinism:** byte-identical replay on every experiment.

## 7. Proposed next direction (operator decision, outside this gate)

Open a **new entry-side candidate family** at its own G0/D0, whose registered first hypothesis is a signal carrying real signal-conditional favourable excursion — the first-order edge the last three families never had. Seeds recorded in the EXP-084 report (regime/availability-conditioned entry; a clean AUDUSD-1h harami read under fresh registration; a cost-vs-selection fragility characterization) are starting points, not commitments. Capture geometry and risk-sizing are deferred until such a signal exists — at which point, for the first time, they would be live levers rather than empty ones.

CF-CAPGEO-001 is retired: screened, closed at G-018, no net-tradable out-of-sample capture geometry found.
