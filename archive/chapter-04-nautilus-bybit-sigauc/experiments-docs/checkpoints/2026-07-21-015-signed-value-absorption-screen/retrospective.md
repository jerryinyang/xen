# Checkpoint-015 Retrospective — Signed Value Where Price Is Blind: the Absorption Screen

> **STATUS: CLOSED — operator-directed 2026-07-22.** The S9 absorption screen (SPDR-009) ran on all
> four domain pairs and returned a **powered null at D1 (1d/1m)** with the three coarser pairs
> **inconclusive by event supply**. **Family CF-SIGAUC-001 is CLOSED** (§4) on the operator's D8
> decision, which amends the D7 closure rule from "powered null on D1 **and** D2" to "powered null
> at D1, with every pair's power state named". S14 (SPDR-010) and the tick-floored spread
> (INFR-019) were **not run** — recorded as untested, not as negative. 0 counted TEST reads;
> holdout SEALED throughout.

**Checkpoint:** 015 · **Opened:** 2026-07-21 (design SIGNED D1–D6; D7 SIGNED 2026-07-22) · **CLOSED:** 2026-07-22
**Family in scope:** CF-SIGAUC-001 (Signed Auction Structure) — **REGISTERED → CLOSED**
**Lane:** INFR (apparatus) → SPDR (screen); XENA never opened
**Source:** `.ignore/what-next/orderflow/ohlc/SIGNAL-SIGNED.md` as amended by Addendum v1.1 (governing)
**One-line outcome:** the family's flagship claim — that the exact taker split pays **where price is
blind** — was tested at its cleanest point and **does not reproduce**: on identical
location-qualified events the signed absorption signature adds **+1.8 bps against an MDE of 5.5 and
a cost floor of 11.3**, its dose-response is **ρ = +0.008**, and the into-level and away-from-level
tails are the **same size** (311 vs 325) and behave alike. Two TRAIN-only items, zero reads.

---

## 1. Objectives vs outcomes (checkpoint design §Objectives)

| Checkpoint objective | Outcome |
|---|---|
| 1. Run the S9 absorption marginal-value screen as the master go/no-go | **DONE** — SPDR-009, four pairs, one frozen design, money floor first. Disposition `NOT_WORTH`. |
| 2. Run the S14 divergence screen as a memo-gated rider | **NOT DONE** — the operator closed the family on the S9 result. S14 is recorded **untested**, its memo never written. See §5. |
| 3. Stand up the tick-floored spread reconstruction (INFR-019) | **NOT DONE** — never opened. The "no net breadth claim" constraint therefore still stands over anything this family produced. |
| 4. Resolve the family at this retrospective | **DONE** — family **CLOSED** (§4), under the D8 amendment to the closure rule. |
| (unlisted, delivered) Multi-timeframe apparatus | **DONE** — INFR-020, pin `5f170b71…`, a durable asset independent of this family's fate. |

Objectives 2 and 3 were designed as insurance against exactly the situation that arose — a null on
S9 — and neither was exercised. That is the honest shape of this close and §5 states its cost.

## 2. The experiment arc

| ID | Role | Outcome |
|---|---|---|
| **INFR-020** | D6 prerequisite — multi-timeframe apparatus | **COMPLETE 2026-07-22**, pin `5f170b71…` accepted. A5 baselines + p90/p10 cuts at 5m/15m/1h, operational hour/4-hour anchors, generalised IB, causal 1m level sets, shared candidate predicate, coverage census. QA runs 1–9 REVISE → run 10 APPROVE. Apparatus only — no outcomes. **Its coverage census is itself a finding:** median COMPLETE-window retention **0.385 / 0.202 / 0.089** at 5m/15m/1h → usable universes **194 / 72 / 47 / 31**, and surviving windows carry 2.4×–27× the volume of partials. |
| **SPDR-009** | Phase 6′ — S9 signed-absorption marginal value, master go/no-go | **COMPLETE 2026-07-22 — operator disposition `NOT_WORTH`.** D1 powered null on both pools at both holds; T2, T4, T5 all WASH; S9 median return **0.0 bps** vs an **11.3–13.0 bps** floor; both zone sensitivities agree (the *tighter* pool is more negative); D2/D3/D4 UNPOWERED at 16 / 2 / 0 signal events. Tripwire `NO_MATERIAL_EDGE` ×4 with bite passing, CF\* UNDERIVABLE. Report `python/experiments/SPDR-009/report.md`. |
| **SPDR-010** | Phase 6′b — S14 CVD divergence rider | **NOT RUN.** Memo never written, screen never designed. Untested. |
| **INFR-019** | tick-floored per-symbol spread | **NOT RUN.** Spread remains reconstructible-in-principle only; `SpreadBps` stays UNUSABLE. |

## 3. Reads + holdout state

- **Global 30% holdout (≥ 2025-01-08): SEALED.** Never queried on any item in this checkpoint.
- **Counted TEST reads: 0.** SPDR spends none; the reserved TEST band was untouched. `test-read-ledger.md` unchanged.
- **CONFIRM band: not exercised.** The design allowed one verify pass on SPDR-009; the operator closed on the DESIGN-band powered null without spending it.
- **Bands used:** DESIGN only, `2021-06-29 → 2023-03-01`, code-asserted.
- **Registry:** evidence rows appended to the family card §10; the status transition in §4 is this retrospective's act, not the screen's.
- **Apparatus produced (durable, survives the close):** multi-timeframe baselines/thresholds/sessions/levels (`5f170b71…`), `xen.sigbar.absorb` + its tests, and everything carried from ckpt-014 (signed-bar catalog lane, 1m baselines, acceptance/trap modules, frozen instrument registry).

## 4. Family-status decision — **CLOSED** (operator-directed)

**Decision: CF-SIGAUC-001 moves `REGISTERED` → `CLOSED`.**

### 4.1 D8 — the closure-rule amendment this required (SIGNED 2026-07-22)

The rule in force (D7) was: *a powered null on every pair that reaches power at realised n, and at
minimum on D1 and D2.* The run delivered a powered null at **D1** and left **D2 unpowered**
(16 signal events after τ, refractory and the arm split). The rule as written was therefore not met.

| # | Question (plain) | Operator decision (2026-07-22) |
|---|---|---|
| **D8** | D1 returned a powered null; D2/D3/D4 are unpowered by event supply. Close the family on D1 alone, or hold it open pending a D2 that may never be powerable? | **CLOSE.** The D7 minimum is amended from "D1 and D2" to **"D1, with every pair's power state named in the closure statement."** Rationale: D2's shortfall is a **structural event-rate fact** on this venue and band, not a sampling accident — no additional DESIGN-band data changes it, so the D2 condition made the family unclosable by construction, which is the same defect D7 itself corrected for D4. |

### 4.2 The closure statement (binding wording — "closed" is not "tested everywhere")

> CF-SIGAUC-001 is closed on the evidence of **three independent powered nulls**: the price-only
> session spine (SPDR-007, a P-01 confirmation), the S3 measured trap-load monotonicity (SPDR-008,
> powered null on three boundaries), and the S9 signed-absorption marginal value (SPDR-009,
> **powered null at D1 1d/1m only**). Power states at close: **D1 POWERED-NULL · D2 INCONCLUSIVE
> (16 events) · D3 INCONCLUSIVE (2 events) · D4 INCONCLUSIVE (0 events, pre-declared power-limited).**
> **S14 (CVD–price divergence) was never run.** The structural and funding-cadence horizons were
> never screened. The close is a decision on where to stop spending, not a claim that every
> mechanism in the source document has been tested.

### 4.3 Why this close is defensible on the evidence

1. **The flagship claim was tested at its cleanest point and failed under power.** S9 is the purest
   statement of "the measured split pays where price cannot see" — a flat-price, high-volume bar at
   a qualified level, where every price-derived sign estimator goes flat by construction. The
   marginal contrast is +1.8 bps with an MDE of 5.5 on 311 signal events across 162 symbols and
   169 days.
2. **The direction operator itself looks empty.** MIRROR (325) is *larger* than S9 (311) and behaves
   identically. The mechanism's core assertion is that the split **names the losing side**; the
   event census shows two symmetric tails. This is stronger than a wash on a contrast — it is
   absence of the asymmetry the mechanism requires.
3. **Every escape hatch was pre-registered and checked.** A tighter contact zone is *more* negative;
   the original ib-width zone reproduces the null; the mid-range control behaves as predicted; the
   dose-response is inside a 2000-seed derangement null; the effect is not hiding in a chronological
   third (the one positive third has three events).
4. **The economics are not marginal.** The signal arm's median return is **exactly 0.0 bps** against
   a fee-dominated floor of 11.3–13.0. Even a real effect of the observed size would be market
   science, not strategy.
5. **The coarse-scale rescue was measured and failed for a structural reason.** Coarsening detection
   to buy wall-clock against a hold-invariant fee destroys the event population two orders of
   magnitude (95,836 → 162 candidates on the liquid cores). That is a property of the venue's
   trading density, and it will not improve with more of this band.

### 4.4 What the close costs — stated, not minimised

- **S14 dies untested.** The Addendum's design was that S9 *and* S14 nulling together kills the
  mechanism family cleanly and non-reformulably. Closing on S9 alone leaves the "cumulative delta
  decoupling from price" object unexamined. Any future reopening should treat S14 as **open**, not
  as covered by this close.
- **Two horizons were never screened** (structural multi-session, funding-cadence), so Addendum
  §2.10's horizon-menu clause is only partially satisfied — micro (this checkpoint) and session
  (ckpt-014) are covered.
- **No net claim was ever admissible** — INFR-019 never ran, so `SpreadBps` remains UNUSABLE and
  every figure in this family stays gross-with-a-modelled-floor.

### 4.5 Signal-level state at close (carried onto the family card)

| Grade | Item |
|---|---|
| **DELETED** (binary-mechanism rule — no re-parameterisation) | S3 Δ+ trap load (ckpt-014) · **S9 signed absorption marginal value** (this checkpoint, D1-powered) |
| **DEMOTED** | S1 (operational anchor only) · A7 (stable ≠ edge-bearing) · §2.5 spread layer (UNAVAILABLE) |
| **CONFIRMED as measurement/characterisation** (never a strategy edge) | A8 provenance · S2 excursion object · S3-base unsigned failed-break geometry · A6 discriminator · Appendix B path |
| **UNTESTED at close** | **S14** · S4–S6 · S8 · S10/S11/S13/S15/S16 · M1–M5 · structural and funding-cadence horizons |

## 5. Lessons (ratify into the KB at the next boundary)

**L-a — A fixed-bar micro horizon can be dead air.** 16.3% of D1 pool-P events return *exactly*
0.0 bps at five minutes. When the conditioning event is defined by *absence of range*, a horizon
counted in bars can measure a period in which price is structurally incapable of moving. Horizons
for effort-without-result events should be defined in units where movement is possible (a range or
ATR multiple, a first-touch event), not a bar count.

**L-b — Coarsening the detection bar is not a free scale sweep.** Detection scale and hold length
were coupled in this design because the economic motive (a hold-invariant fee needs wall-clock)
was expressed through the detection bar. The result was a 2-order-of-magnitude collapse in event
supply. **Decouple them:** detect at the finest calibrated scale, hold for the wall-clock the cost
structure requires.

**L-c — On a 24/7 venue with illiquid names, outcome-path availability is a conditioning variable.**
78% of located D1 events had no contiguous 1-minute outcome path. The surviving read is conditioned
on continuously-traded windows and on **post-entry** activity. It hits both arms alike so marginal
contrasts survive, but absolute returns and floor comparisons are conditioned figures and must be
labelled as such.

**L-d — A necessity prediction needs a companion positive control.** The source's T3 prediction
("unqualified mid-range absorption ≈ 0") came true and carried no information, because the located
contrast was also ≈ 0. Any framework claim of the form "X is necessary" should name, in advance,
the cell that must be non-null if the mechanism is real.

**L-e — A leak threshold can be underivable, and that is a reportable state.** CF\* required
planting a causal effect at 1× the published MDE; at D1 no seed produced a material contrast at
1×, and the 2×/3× values spread 1.12 → 0.70. Report `UNDERIVABLE` with the plant curve rather than
falling back on an inherited constant — and never read `NO_MATERIAL_EDGE` as a clean bill of health.

**L-f — Count both tails at the event level, not only in the cell grid.** ckpt-014 learned this for
multiplicity (mirror cells outnumbering winners). ckpt-015 shows the sharper version: when the
*mirror arm itself* is as large as the signal arm and behaves identically, the direction operator
is empty and no amount of contrast machinery will rescue it.

## 6. What happens next

- **No successor checkpoint is opened by this retrospective.** The family is closed; the signed-flow
  arc ends here unless the operator reopens it deliberately.
- **If it is ever reopened**, the two live entry points are **S14** (untested, needs its
  mechanism-differentiation memo written first — and that memo now has to explain why cumulative
  delta carries information when both the failed-break Δ tag and the flat-bar Δ split do not) and
  the **unscreened horizons** (structural, funding-cadence).
- **INFR-019** (tick-floored spread) remains an unbuilt prerequisite for any net breadth claim in
  this programme, not just this family — worth carrying forward on its own merits.
- **Chapter-04 rollover** remains DEFERRED INDEFINITELY (checkpoint D5); this close does not trigger it.
- **Designer handoff** for the source author: `source-designer-handoff.md` in this directory.

---

## 7. Artifacts

| Item | Path |
|---|---|
| Checkpoint design (D1–D8) | `design.md` (this directory) |
| Designer handoff | `source-designer-handoff.md` (this directory) |
| ckpt-014 retrospective | `../2026-07-20-014-signed-auction-structure/retrospective.md` |
| Family card | `../../../signal-registry/candidate-families/cf-sigauc-001.md` |
| Apparatus | `python/experiments/INFR-020/report.md` (pin `5f170b71…`) |
| The screen | `python/experiments/SPDR-009/report.md` + `design.md`, `qa-review.md`, `results/` |
| Shared module | `python/src/xen/sigbar/absorb.py` |

**Provenance caveat carried from the screen:** SPDR-009's reported layers come from the 2026-07-22
06:33 UTC emission; a later re-run was stopped after the D1 event build, so three count-only result
files carry later timestamps than the layers. Re-run end to end before re-quoting the figures
externally. The disposition does not depend on it.
