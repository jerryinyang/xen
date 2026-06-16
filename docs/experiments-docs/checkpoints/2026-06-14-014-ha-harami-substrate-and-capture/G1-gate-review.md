# G1 Gate Review — Phase 014-A Substrate, Capture & Characterisation Adjudication

**Date:** 2026-06-15
**Gate:** G1 — adjudicated after Phase 014-A (design §10), mechanical, per cell then
composed by P11 (≥5 cells over ≥3 instruments).
**Adjudicated by:** desk review (research-pipeline governance); **operator ratification
of the routing decision pending** (§10 reserves routing to the operator — it is *not*
pre-committed).
**Inputs (all complete, audits PASS, post-experiment governance APPROVE):**
- EXP-048 `python/experiments/EXP-048/` — READINESS_DELIVERED (audit PASS 0C/1W/2I)
- EXP-049 `python/experiments/EXP-049/` — CAPTURE_READINESS_DELIVERED (audit PASS 0C/0W/4I)
- EXP-050 `python/experiments/EXP-050/` — CONTEXT_CHARACTERISATION_DELIVERED
- EXP-051 `python/experiments/EXP-051/` — STRONG_FILTER_CHARACTERISATION_DELIVERED
- EXP-052 `python/experiments/EXP-052/` — CONFIRM_CHARACTERISATION_DELIVERED (audit PASS 0C/0W/3I)
- D0 predeclarations `D0-predeclarations.md` (RATIFIED, G0 PASS 2026-06-14)
- **Companion:** `014-A-conditioning-gap-and-validation-lessons.md` (what 014-A measured vs
  what the thesis requires; reasoning trail; process lessons) — read alongside this verdict

---

## Verdict

```text
LEG (a) — primitives READY (EXP-048):            SATISFIED  (99 cells / 17 instruments)
LEG (b) — capture geometry VIABLE (EXP-049):     FAILS      (0/99 VIABLE; composition_met = false)
SUBSTRATE_REFUTED criteria:                       UNMET
INCONCLUSIVE criteria:                            UNMET (power sufficient)

G1 MECHANICAL OUTCOME (design §10): CHARACTERISED_NOT_VIABLE
  — primitives READY, benchmark capture geometry fails P12 over P11.
  — "the AVWAP failure mode in a new dress: signal real but capture geometry not viable."

ROUTING: the benchmark-capture null does NOT justify family closure. The registered
  variant/model surface is ~2/3 unexplored, the capture read was short-horizon (P4 cap
  bound at the 6-bar floor in 96/99 cells) and symmetric by construction, the tie-break
  is worst-case, and no AVWAP-style lifetime move-availability diagnostic was run.
  Proceed to a scoped 014-B (operator-directed). See "Routing" below.
```

Design §10 makes the full **PROCEED_TO_SCREEN** outcome unreachable at G1: its leg (c)
("≥1 014-B combined event definition clears the same P11/P12 composition") is by
construction 014-B work. At G1 the achievable outcomes are SUBSTRATE_REFUTED,
CHARACTERISED_NOT_VIABLE, or INCONCLUSIVE. The mechanical readout selects
CHARACTERISED_NOT_VIABLE.

## Leg (a) — substrate & detector readiness (EXP-048, mechanical)

| Item | Reading |
| --- | --- |
| Cells READY ∪ READY_FLAGGED | **99 / 102** (86 READY + 13 READY_FLAGGED) across all 17 instruments — ≫ P11 quorum |
| COVERAGE_EXCLUDED | 3 (US500-4h 0.286, JP225-2h 0.257, JP225-4h 0.297) — coverage outcomes, not primitive defects |
| Invariant violations (12 keys, both batteries) | **0 / every cell** |
| Determinism failures | **0 / 102** (frame-identical replay) |
| Move rates (ZigZag confirmed / 1k bars) | 170.2–207.0; all ≥30 (min 336) |
| Harami event rates (/ 1k HA candles) | 229.6–261.4; all ≥30 (min 401) |

Leg (a) **SATISFIED**: both primitives mechanically valid on 99 cells; the substrate
and detector gate for EXP-049 is met with breadth far above P11.

## Leg (b) — capture geometry (EXP-049, mechanical — the binding leg)

| P12 component | G1 primary (distance-based) | G2 secondary (retracement-level) |
| --- | --- | --- |
| `r = P(fav before adv \| resolved)` | **[0.4545, 0.5343]**, tightly around the 0.50 null | [0.3257, 0.4389] |
| Cells with r ≥ 0.55 ∧ CI_low > 0.50 ∧ resolved ≥ 30 | **0 / 99** (all BELOW_R) | **0 / 99** |
| `composition_met` (≥5 cells / ≥3 instruments) | **false** (0 cells, 0 instruments) | false |
| Sensitivity at relaxed bars | false | false |
| NOT_VIABLE_BY_POWER cells | 0 (all resolved ≥30, min 128) | — |
| Construction integrity | 0 causality / 0 fence / 0 NaN / 0 G1 fav_dist; 0 non-deterministic | 52–60% degenerate (entry through midpoint), correctly excluded & disclosed |

Leg (b) **FAILS** P12 over P11 in both geometries. The benchmark capture geometry
(P2 50% favourable retrace, P3 1:1 adverse, P4 adaptive time cap, P5 LOOKBACK=1)
produces **no favourable-before-adverse bias above 0.55 in any cell** of the 17×6 grid.

## Characterisation readouts (EXP-050/051/052 — inform routing, not the leg count)

| EXP | Result | Bearing on routing |
| --- | --- | --- |
| EXP-050 (HYP-003, timing) | **0/99 CLUSTERED.** FT ∈ [0.210, 0.312] vs FT_rand ∈ [0.334, 0.432]; Δ uniformly **−0.12 to −0.18** (haramis are *front-loaded*, not near-exhaustion). MA(20,50) secondary Δ ≈ 0 → front-loading is ZigZag-specific. | **Undercuts the family thesis** ("harami at trend *exhaustion*"). Position-in-move cannot serve as a timing/selection filter; a filter must shift the distribution rightward ~22–28pp just to reach materiality. |
| EXP-051 (HYP-004, strong-move) | **99/99 MATERIAL**, both forms P11-clear (/STRONG-STAT ρ med 1.92, f med 0.27; /STRONG-HA ρ med 1.80, f med 0.20); 0 flips. | The **one surviving lever**. But it is a move-*magnitude* selector. See routing note: it does not by itself move the symmetric-barrier r off 0.50. |
| EXP-052 (HYP-005, confirm) | **99/99 negative shift.** Paired Δ (CONFIRM−DIRECT) median **−0.62 ATR**; DIRECT (MFE−MAE)/ATR ≈ 0.00 (replicates EXP-049 null), CONFIRM ≈ −0.58. p11_neg_readout true. | **Confirmation lever is dead** on this substrate — structurally adverse (stop derived from the rejected signal-bar extreme). |

## Integrity preconditions (all satisfied — the readout is valid)

- **Determinism:** 0 failures across EXP-048 (102/102), EXP-049 (99/99), EXP-050 (99/99),
  EXP-051 (99/99), EXP-052 (99/99) — full second-pass frame-identical replay everywhere.
- **Invariant batteries:** 0 violations across all five experiments (substrate, detector,
  barrier, position-in-move, confirm).
- **Power:** EXP-049 all member cells resolved ≥30 (min 128) — the 0/99 null is a genuine
  measurement, not a power failure (cf. EXP-049 observation: r≈0.50 is consistent with a
  near-random-walk path under symmetric barriers).
- **Budget discipline:** **0 candidate slots, 0 TEST reads, ledger unchanged**; final-30%
  global holdout sealed; no new-universe row read under the HA-harami event definition;
  TRAIN-only throughout; all work gross (no costs), per D0.
- **Audits:** all PASS — EXP-048 0C/1W (latent /BARCFG null guard, not exercised), 049 0C/0W,
  050/051 PASS, 052 0C/0W. No Critical anywhere; no warning bears on the leg counts.

## Adjudication notes (carried; none alters the mechanical count)

1. **The r≈0.50 null is structural, not incidental.** EXP-049's symmetric 1:1 barriers
   (50% favourable retrace, equal-distance adverse) on a ZigZag-confirmation entry yield
   the near-random-walk expectation. This is the central finding: under the benchmark
   geometry the substrate carries no favourable-before-adverse asymmetry.

2. **The strong-move filter (EXP-051) cannot rescue *symmetric*-barrier capture.**
   Selecting larger moves scales both barriers proportionally; the conditional r on a
   bigger-move subset is still ~0.50 absent a barrier *asymmetry*. The lever that can
   move r off the null is **asymmetric target geometry** (the registered 014-B variants
   `/ADV-EXTREME`, `/ADV-NONE`, `/VPTARGET`, `/MAGTARGET`, `/THIRD-EVENT`), and any such
   shift trades capture rate against payoff — so the genuine open question is *expectancy
   structure*, which EXP-049 did not measure (it measured r under one symmetric geometry only).

3. **Two of three selection levers closed within 014-A.** EXP-050 shows the timing premise
   is empirically inverted (haramis front-loaded, not exhaustion-clustered) and EXP-052
   shows confirmation is structurally adverse. Only EXP-051 (magnitude) survives, and per
   note 2 it does not address the binding constraint.

4. **Mechanical outcome vs phase routing are distinct.** The mechanical G1 outcome is
   CHARACTERISED_NOT_VIABLE *on the benchmark geometry*. Per §10 this does not force
   closure; the operator routing decision (2026-06-15) is to **proceed to a scoped 014-B**
   rather than close, because the geometry/exit surface that bears on capture is largely
   unexplored (see Routing). Closure would be reconsidered at G2 on the full surface.

## Routing — closure is NOT justified at G1; proceed to a scoped 014-B

§10 (CHARACTERISED_NOT_VIABLE consequence): "Family carried as measured-negative; routing
decision at retrospective; no candidate branch registered." On review, the mechanical
benchmark-capture null does **not** warrant family closure, for four reasons:

1. **The registered surface is ~2/3 unexplored.** 014-A measured the *symmetric benchmark*
   barrier + `/STRONG-STAT` + `/STRONG-HA` + `/CONFIRM`. Untested: `/ADV-EXTREME`,
   `/ADV-NONE`, `/VPTARGET`, `/MAGTARGET`, `/THIRD-EVENT`, `/THIRD-TIME`, `/ATRMULT`,
   `/LOOKBACK`, `/BARCFG` — i.e. the entire 014-B barrier-model comparison, which is the
   part of the design that actually *varies capture geometry*. Closure now closes on the
   simplest possible model.
2. **The capture read was short-horizon and symmetric by construction.** `r≈0.50` is the
   *expected* null for 1:1 equidistant barriers on a near-random path — it confirms barrier
   symmetry, not absence of edge under asymmetric geometry. The P4 adaptive cap bound at the
   **6-bar floor in 96/99 cells**, so only ~6 bars ahead were measured; AVWAP's edge lived
   in the *lifetime* MFE, which a 6-bar window would hide.
3. **The tie-break is worst-case (measurement-method risk).** `xen.capture_barriers`
   resolves bars that span both targets adversely. On a substrate sitting exactly at 0.50,
   a systematic adverse tie-break can move cells from ~0.50 to <0.50 — i.e. it can
   manufacture part of the `BELOW_R` readout. An intrabar fill model (O→L→H→C / O→H→L→C
   path assumption) must be audited before any closure on `r<0.55`.
4. **No AVWAP-style availability diagnostic was run.** AVWAP closed only after EXP-047
   measured lifetime MFE ≈ 5–9× the cost floor (availability good, capture bad). Phase 014
   has no equivalent long-horizon move-availability read, so the apples-to-apples comparison
   is missing.

**The conditioned family hypothesis is untested (the binding gap).** The thesis
(`candidate-families/harami.md` §Thesis) conditions on a harami **"at the exhaustion of a
strong impulsive move"** — the strong-move filter and position condition exist "to *qualify*
… the reversal the harami predicts." Per the design's build-from-primitives intent the
strong-move filter ran **OFF** (P6 default) in every 014-A read, so **no efficacy/capture
experiment applied the family's defining conditioning**:

- EXP-049 (`r≈0.50`) anchored on the **ZigZag confirmation bar with no harami and filter OFF** —
  it measures the *substrate's* reversal capture, not the signal's.
- EXP-052 (excursion ≈0) used the **raw harami, filter OFF, no position condition**.
- EXP-050 (front-loading) measured the **base-rate position of raw haramis** — it shows
  selection has work to do, but it does **not** test whether the *conditioned* subset
  (strong move ∧ near-exhaustion) reverses. A low base rate is consistent with a reversing
  conditioned subset; treating EXP-050 as a premise refutation was a category error.
- EXP-051 proved the strong-move filters select a **materially different** population but
  fed it into **no** outcome read.

**There is one *live* conditioning mechanism, not two.** "End of move" cannot be detected by
position-in-move (P9 ≥0.67, EXP-050's metric): the move's end pivot is **future information**
for an in-progress move, so position is **descriptive-only** by the doc's own causality
discipline (lines 113–118, 137–149). The real-time "exhaustion-of-a-strong-move" detector is
the **lookback-magnitude-percentile** test — the move's magnitude-so-far (known start →
current price) reaching the upper tail of completed-move magnitudes — i.e. **`/STRONG-STAT`**.
A move that has not reached the percentile is not a valid signal. EXP-051 built exactly this
filter and proved it carves a materially different population, but fed it into **no** outcome
read. **The conditioned signal's efficacy is therefore unmeasured — the family's central
hypothesis has not been tested at all.** Full reasoning trail and per-experiment gap analysis:
[`014-A-conditioning-gap-and-validation-lessons.md`](014-A-conditioning-gap-and-validation-lessons.md).

The fair closure condition: if the **conditioned** signal (strong-move filter ON — the live
magnitude-percentile end-of-move detector — anchored at the harami to capture its lead over
the ZigZag giveback) + expanded barrier geometry + new exit/position-management models + a
corrected fill model + a long-horizon availability read **still** produce null, closure is
then well-supported (a G2 CHARACTERISED_NOT_VIABLE on the full, conditioned surface).

### Directed 014-B scope (operator, 2026-06-15)

Proceed to 014-B. All work remains gross, 0 candidate slots, 0 TEST reads, holdouts sealed.
The 014-B design + D0 addendum (and any newly registered branches) are written before any
result-producing code. Scope elements directed by the operator:

- **Conditioned-signal efficacy read (lead element — the actual family hypothesis).**
  Run the *conditioned* harami — strong-move filter ON (`/STRONG-STAT` percentile, the live
  end-of-move detector; `/STRONG-HA` as the registered alternative) — through a
  capture/excursion read, **anchored at the harami** (not the ZigZag confirmation) to capture
  its lead over the `ATR_MULT×ATR` giveback. This is the conditioned object EXP-049/050/051/052
  never ran through an outcome read. Position-in-move (EXP-050) stays a descriptive lens, never
  a live filter.
- **Full barrier-model comparison** across the registered variants (favourable: `/VPTARGET`,
  `/MAGTARGET`; adverse: `/ADV-EXTREME`, `/ADV-NONE`; third: `/THIRD-EVENT`, `/THIRD-TIME`),
  measured as **gross expectancy** (not first-hit `r` alone).
- **New position-management / exit models** from the operator draft
  (`.ignore/temp/exit.md`) — to be registered as new family branches:
  partial/scaled favourable exits (first-profitable-close + target + reversal-event;
  percentage-to-target, ≤3 splits) and a **structure-based trailing adverse exit**
  (smaller-ATR ZigZag pivots: new pivot high → trail to recent low for longs, and the
  mirror for shorts). Usable individually or combined.
- **Intrabar fill realism** as a methodology correction: simulate fill order under the
  green O→L→H→C / red O→H→L→C path assumption rather than the blanket-adverse tie-break;
  re-read the benchmark capture under it to bound how much of the `r≈0.50` null is the
  tie-break.
- **Long-horizon move-availability diagnostic** (EXP-047 analog): lifetime favourable MFE
  vs adverse MAE over the full move, to settle whether this family is AVWAP's situation
  (move available, capture missing) or worse (no move).

## Consequences (conditional on the routing decision)

| Item | State |
| --- | --- |
| G1 mechanical outcome | **CHARACTERISED_NOT_VIABLE on the benchmark geometry** (primitives READY; benchmark capture 0/99 VIABLE) — a benchmark-only finding, not a family verdict |
| `CF-HA-HARAMI-001` candidate family | **OPEN** — carried as benchmark-capture-negative with HYP-002 unresolved at the family level; no candidate branch registered; closure reconsidered at G2 on the full surface |
| 014-A primitives (`xen.zigzag`, `xen.ha_harami`, `xen.capture_barriers`, `xen.strong_move`, `xen.confirm_entry`) | RETAINED, construction- & determinism-validated; reusable by any 014-B variant without re-validation |
| Phase 014 | **PROCEEDS to 014-B** (operator decision 2026-06-15): full barrier-model comparison + new exit/position-management branches (`.ignore/temp/exit.md`) + intrabar fill correction + long-horizon availability diagnostic. 014-B design + D0 addendum + new branch registrations precede any result-producing code |
| Budget | **0 candidate slots, 0 TEST reads spent; ledger unchanged; holdouts sealed** |
| Registry disposition | HYP-002 recorded as **benchmark-capture negative, family-level OPEN**; new exit/position-management branches to be added to `candidate-families/harami.md` and `multiplicity-registry.md` (Phase 014-B batch) before measurement |
```

**Routing ratified by operator 2026-06-15: proceed to scoped 014-B (see Routing).**
```
