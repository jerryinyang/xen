# G2 Gate Review — Phase 014-B Conditioned-Surface Adjudication

**Date:** 2026-06-17
**Gate:** G2 — single, terminal gate for Phase 014-B (no intermediate gates;
`014-B-design.md` §4/§8, `014-B-D0-addendum.md` P21). Applied **after the full slate**
(EXP-053–060 + the registered gap-fills EXP-059B, EXP-060B).
**Adjudicated by:** desk review (research-pipeline governance), on operator instruction
2026-06-17 ("G2 review and adjudication next"); routing form ratified by the operator
("Open MA-substrate follow-up").
**Family:** `CF-HA-HARAMI-001` (REGISTERED, OPEN).
**Binding endpoint (P14):** median per-event gross ATR-normalised expectancy, CI_low > 0,
≥ 30 events, composed by P11 (≥ 5 cells over ≥ 3 instruments); mean disclosed.

---

## Verdict

```text
G2 STATUS: NO_PROCEED_TO_SCREEN  —  and FAMILY NOT CLOSED
  • PROCEED_TO_SCREEN ...... NOT met (no combined definition clears P11 vs the P13
                            two-baseline conjunction on the registered ZigZag substrate)
  • SUBSTRATE/METHOD_DEFECT  NOT met (EXP-054 IMMATERIAL; integrity all-pass)
  • INCONCLUSIVE ........... NOT met (99/99 cells powered across the whole slate)
  • CHARACTERISED_NOT_VIABLE criterion text met ON ZIGZAG ONLY — a CLEAN close is
                            forbidden by EXP-060B's predeclared SUBSTRATE_LEAD_FOUND routing
PHASE OUTCOME: 014-B CHARACTERISED_NOT_VIABLE on the ZigZag substrate as configured;
               family carried OPEN on a real, signal-attributable MA-substrate median edge.
CANDIDATE SLOTS SPENT: 0    TEST READS SPENT: 0    HOLDOUTS: sealed (unchanged)
ROUTING (operator-ratified): scoped MA-substrate follow-up — bounded-downside adverse
               geometry, mean as co-primary endpoint. New phase design (own D0/G0).
```

The adjudication is **not** a clean instance of any single §8 outcome. It is the fork the
014-B design (§8 note) and EXP-060B's addendum (§6) predeclared: the mechanical
PROCEED_TO_SCREEN test fails on the registered substrate, but EXP-060B — a registered
gap-fill that runs **before** and feeds G2 — returned `SUBSTRATE_LEAD_FOUND`, which is a
binding prohibition on a clean `CHARACTERISED_NOT_VIABLE` closure.

## Basis — the full conditioned surface (gross, 0 slots, 0 TEST)

The single G2 is adjudicated on the complete slate, not on any one geometry (the
no-early-closure guard, §4):

| Lever | EXP | Mechanical result |
| --- | --- | --- |
| Conditioned-signal efficacy (HYP-006) | EXP-053 | **EVIDENCE_FOR** — 7 viable cells/6 instruments under benchmark barriers; the family's actual hypothesis is non-null. |
| Intrabar fill model (HYP-007) | EXP-054 | **IMMATERIAL** — median Δr 0.010, 0/99 TIE_BREAK_SENSITIVE; the benchmark capture null is *real*, not a worst-case-tie-break artifact (closes the §8 SUBSTRATE/METHOD_DEFECT trigger). P15 adopted as the 014-B fill standard. |
| Lifetime availability (HYP-008) | EXP-055 | **AVAILABILITY_GOOD** — 74 MOVE_AVAILABLE cells/17 instruments; the AVWAP situation (move available, capture missing), not "no move." |
| Favourable-target geometry (HYP-009) | EXP-056 | **EVIDENCE_AGAINST** — 0/8 variants clear P11; benchmark 50% wins. |
| Adverse-target geometry (HYP-010) | EXP-057 | **EVIDENCE_FOR** — `/ADV-NONE` wins P11 (23 cells/15 instruments); the asymmetric lever that moves expectancy. |
| Third-barrier geometry (HYP-011) | EXP-058 | **EVIDENCE_AGAINST** — no variant clears P11; benchmark adaptive cap wins. |
| Position-management exits (HYP-012) | EXP-059 | **EVIDENCE_FOR** — V2A partial-exit arm clears P11 (53 wins/17 instruments); structure trailing detrimental within the cap. |
| Uncapped trailing gap-fill (HYP-012b) | EXP-059B | **EVIDENCE_AGAINST** — 0/2 binding arms clear P11; cap-isolation confirms the cap was not the constraint. `/EXIT-TRAIL-UNCAPPED` closed as a characterized negative. |
| **Combined event system (HYP-013)** | **EXP-060** | **CHARACTERISED_NOT_VIABLE_ELIGIBLE** — champion A3 (V2A × `/ADV-NONE` × benchmark cap) **0/99 champion_wins**: 69/99 individually viable (median CI_low > 0, m ≥ 30), **3/99** beat matched-random, **0/99** beat MA(20,50). Both geometric levers improve expectancy additively (interaction ≈ 0); A3 − BENCH positive 99/99. |
| **MA-substrate gap-fill (HYP-013b)** | **EXP-060B** | **SUBSTRATE_LEAD_FOUND** — on the MA(20,50) substrate the same conditioned harami (M3) is median ≈ **1.16** vs matched-random RM3 ≈ **0.38** and **beats its own-substrate random in 85/99 cells** (reverses ZigZag's 3/99); M3 median-viable 89/99. **But median-only:** M3 gross **mean** median ≈ **−0.065**, mean-viable only **14/99**; ADV-NONE skew gap **1.20 ATR** (vs 0.49 for 1:1). Lead = 14 cells/9 instruments (P11 met), **8/14 low-n 4h**. |

## Why each §8 outcome does / does not apply

1. **PROCEED_TO_SCREEN requires** ≥ 1 combined definition (EXP-060) clearing P11 expectancy
   viability vs the P13 baselines (matched-random **and** MA(20,50)). The binding champion
   A3 fails the MA(20,50) leg of the conjunction in **every** cell (`contrast_ma_low` ∈
   [−0.569, −2.404] ATR). **Not met.** EXP-060B's MA-substrate edge does **not** satisfy this
   either: it is median-only with mean ≈ 0 (not tradeable/screen-ready), and EXP-060B is a
   characterisation read — by P21 it cannot register a candidate; registration occurs only at
   a future MA-substrate scope's gate.
2. **SUBSTRATE/METHOD_DEFECT** would fire if the fill-model read flipped the benchmark or if a
   determinism/causality/invariant failure appeared. EXP-054 is IMMATERIAL; EXP-060/060B
   reconcile exact 99/99 with determinism, causality, and invariants all passing. **Not met.**
3. **INCONCLUSIVE** would fire on coverage/power failure. The slate is fully powered (99/99).
   **Not met.**
4. **CHARACTERISED_NOT_VIABLE** is the criterion the ZigZag surface satisfies in isolation
   (full surface measured; no combined definition clears P11). **But a clean close is
   prohibited:** EXP-060B demonstrated that the harami expresses a genuine, signal-attributable
   median edge on the MA substrate (85/99 vs random, a fair non-degenerate control at 0.38),
   so the EXP-060 "MA dominance is purely a substrate property" reading is **refuted in part**.
   The binding obstacle has moved from "does the signal work" to "does a bounded-downside
   geometry leave a positive mean." Closing the family now would discard an unexhausted lever.

## Net adjudication

**014-B is CHARACTERISED_NOT_VIABLE on the ZigZag substrate as configured, and the family is
carried OPEN.** The combined V2A × `/ADV-NONE` champion cannot reach the MA(20,50) baseline
from a single-point ZigZag-defined reversal entry, but the same conditioned signal *does*
express a real median edge on the MA(20,50) substrate. That edge is **not yet tradeable** —
the capped-upside / uncapped-downside geometry leaves the gross mean at ≈ 0 (skew gap 1.20
ATR), and the P11 lead leans on 8/14 low-n 4h cells. The honest state is **a real but narrow,
median-only MA-substrate edge whose binding constraint is now the skew/mean, not the signal.**

## Consequences

| Item | State |
| --- | --- |
| PROCEED_TO_SCREEN | **NOT triggered.** No candidate branch registered; no first slot consumed. |
| Family `CF-HA-HARAMI-001` | **REGISTERED / OPEN** — not closed. The ZigZag-substrate combined surface is measured-negative and retained; the MA-substrate edge is the open lever. |
| Candidate slots / TEST reads | **0 / 0** this phase and across all of 014-B; `test-read-ledger.md` unchanged; holdouts sealed; no new-universe row read under the HA-harami event definition. |
| Registered branches measured in 014-B | `/STRONG-STAT`, `/STRONG-HA`, `/VPTARGET`, `/MAGTARGET`, `/ADV-EXTREME`, `/ADV-NONE`, `/THIRD-EVENT`, `/THIRD-TIME`, `/EXIT-PARTIAL`, `/EXIT-TRAIL-STRUCT`, `/EXIT-TRAIL-UNCAPPED`, fill-model standard (P15) — all characterised, dispositions in `multiplicity-registry.md` and `candidate-families/harami.md`. Refuted/negative items retained in the file drawer. |
| Phase 014 checkpoint | **CLOSES at G2** with this adjudication; retrospective written (`retrospective.md`, same directory). |

## Routing (operator-ratified 2026-06-17 — "Open MA-substrate follow-up")

The MA-substrate edge is a genuine, unexhausted lever, so the programme does **not** close the
family. A new follow-up phase (own design, own D0, own G0) re-screens the **MA-conditioned
harami** against the skew/mean obstacle:

- **Target the mean, not just the median.** Make the gross **mean** a co-primary endpoint
  alongside the P14 median (EXP-060B W2: the median overstates tradeable expectancy when the
  mean is ≈ 0).
- **Bounded-downside adverse geometry.** Re-screen under **stop-bearing** adverse models
  (registered benchmark 1:1, `/ADV-EXTREME-rr1`) rather than re-running V2A × `/ADV-NONE`,
  which inherits the mean ≈ 0 problem. EXP-060B D1 shows the MA 1:1 skew gap (0.49) is < half
  the ADV-NONE gap (1.20), so a bounded downside may recover the mean at some median cost.
- **Confront the 4h-concentration / low-n caveat (W1).** The lead leans on 8/14 low-n 4h
  cells; the follow-up design must power or down-weight 4h so the verdict is not a 4h artifact.
- **Signal-component attribution on MA** (harami-only / strong-only vs RM3) is a secondary
  question, opened only if the bounded-downside re-screen survives.

Direction-setting detail belongs to the follow-up phase design and its D0, not to this gate.
The MA-substrate follow-up makes **no** TEST or holdout contact and registers a candidate only
at its own PROCEED gate.

---

*Companion documents: the per-experiment cards live in
`../../families/cf-ha-harami-001/INDEX.md`; the Phase 014 synthesis and process lessons live
in `retrospective.md` (this directory); the conditioning category-error record that motivated
014-B is `014-A-conditioning-gap-and-validation-lessons.md`.*
