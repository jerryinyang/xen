# Phase 014-A — Conditioning Gap & Validation Lessons

**Date:** 2026-06-15
**Status:** Companion to `G1-gate-review.md`. Authoritative record of *what 014-A
actually measured vs what the `CF-HA-HARAMI-001` thesis requires*, why the gap was
missed during review, and the reasoning trail (desk pushbacks + operator clarifications)
that surfaced it. Written so the same category errors are not repeated in 014-B or in
future families.
**Inputs:** EXP-048–052 (all complete, audits PASS, post-experiment governance APPROVE);
`docs/signal-registry/candidate-families/harami.md`; `design.md`; `D0-predeclarations.md`.

> **One-line takeaway.** 014-A validated *primitives* and characterised *unconditioned*
> behaviour. It never ran the family's **actual signal** — a strong-move-qualified harami,
> anchored at the harami — through any capture/efficacy read. The benchmark capture null
> (EXP-049 `r≈0.50`) and the front-loading result (EXP-050) are therefore **not** evidence
> against the family hypothesis; they are evidence about objects the hypothesis does not
> claim anything about. Closure at G1 is unjustified.

---

## 1. What the family thesis actually claims

From `candidate-families/harami.md` §Thesis (lines 19–24):

> "A Heiken Ashi (HA) harami **observed at the exhaustion of a strong impulsive move**
> marks a confirmed trend reversal with **enough lead over the trend-change confirmation**
> to be tradable. The harami is the family **core**; the trend substrate, strong-move
> filter, signal-confirmation variant, and 3-barrier reversal framework exist only to
> **qualify**, contextualize, or capture the reversal the harami predicts."

Three load-bearing clauses, each of which 014-A left untested as a *conjunction*:

1. **Conditioned signal** — the tradable signal is a harami that occurs *at the exhaustion
   of a strong impulsive move*, not a raw harami. The strong-move filter is part of the
   signal definition ("to qualify … the reversal"), not an optional overlay.
2. **Lead over confirmation** — the harami's only edge is detecting the turn *earlier* than
   the ZigZag's own `ATR_MULT × ATR` giveback (doc lines 145–149). The operative entry is
   therefore **the harami**, not the ZigZag trend-change confirmation bar.
3. **Capture** — the 3-barrier framework exists to convert the predicted reversal into
   realizable P&L.

## 2. The causality insight — "end of move" is a *live* condition, and position-in-move is not

This is the crux, and it was clarified by the operator after an incorrect desk framing
(see §5). The family doc's causality discipline (lines 137–149) is binding:

> "A ZigZag pivot is confirmed only **retroactively** … so the pivot location is **future
> information** relative to the bars between it and the prior confirmed pivot. Signal
> detection, 'end of trend' judgments, and entry/confirmation logic use **only data
> available at that timestamp**. Never reference an unconfirmed pivot."

Consequences:

- **Position-in-move (EXP-050's metric, P9 ≥0.67) cannot be a live signal condition.** It
  needs the move's *end* pivot, which is future information for an in-progress move. The doc
  states this directly (lines 113–118): P9 is "permitted **because HYP-003 is descriptive
  characterization of completed moves, not a live signal.**" EXP-050 is a *post-hoc lens*.
- **The live operationalization of "end of move" is the magnitude-percentile test.** What
  *is* computable at the harami timestamp is the move's **magnitude-so-far**: distance from
  the known move-start (last *confirmed* pivot) to the current price. Compared against the
  LOOKBACK distribution of completed-move magnitudes, a current move already in the upper
  tail (≥ X-percentile, e.g. p75) has **statistically** travelled as far as moves usually
  travel — i.e. it is probably near exhaustion (tail-exceedance is rare). **This percentile
  test is `/STRONG-STAT`.**
- Therefore there is **one** live conditioning mechanism (magnitude-percentile = the
  real-time "exhaustion-of-a-strong-move" detector), reinforced by the harami pattern itself
  (a small inside-body candle = momentum stall). There is **not** a separate, independently
  required "position" filter. (A correctly-stated residual caveat: "upper-tail magnitude" is
  a *probabilistic* proxy — a trending regime can blow through p75 and keep going. Whether
  the conditioned harami reverses or gets run over is exactly the empirical question 014-B
  must answer; it is not settled by 014-A.)

## 3. What each 014-A experiment actually measured (and the gap)

| EXP | Mechanical result (factual) | Filter state | Entry anchor | What it does **not** test |
| --- | --- | --- | --- | --- |
| **EXP-048** READINESS_DELIVERED | 99/102 cells READY (86 + 13 flagged), 3 COVERAGE_EXCLUDED; 0 invariant violations, 0 determinism failures; move rates 170–207/1k, harami 230–261/1k | n/a (readiness) | n/a | Nothing — primitives validated, scope-correct. |
| **EXP-049** CAPTURE_READINESS_DELIVERED | barriers constructible 99/99; G1 (distance) `r ∈ [0.4545, 0.5343]`, **0/99 VIABLE**; G2 (retrace) `r ∈ [0.33, 0.44]`, 0/99; all cells resolved ≥30 (min 128); P4 cap bound at 6-bar floor in 96/99; **conservative (worst-case) tie-break** | **`/STRONG` OFF; no position cond.** | **ZigZag confirmation bar — *no harami at all*** | The signal's capture. Measures the *substrate's* reversal capture, unconditioned, short-horizon, symmetric barriers, worst-case fills. |
| **EXP-050** CONTEXT_CHARACTERISATION_DELIVERED | **0/99 CLUSTERED**; FT ∈ [0.21, 0.31] vs FT_rand ∈ [0.33, 0.43]; Δ uniformly −0.12 to −0.18; MA(20,50) Δ ≈ 0 (front-loading is ZigZag-specific) | `/STRONG` OFF | harami | Whether the *conditioned* subset reverses. Measures the **base-rate position of raw haramis** using a **non-live** (completed-move) metric. |
| **EXP-051** STRONG_FILTER_CHARACTERISATION_DELIVERED | **99/99 MATERIAL** both forms; `/STRONG-STAT` ρ med 1.92, f med 0.27; `/STRONG-HA` ρ med 1.80, f med 0.20; 0 flips; P11-clear, 17/17 instruments | the filters themselves | — | **Efficacy.** Proves the live filter selects a materially different (larger) population, then feeds it into **no outcome read**. |
| **EXP-052** CONFIRM_CHARACTERISATION_DELIVERED | **99/99 negative shift**; paired Δ (CONFIRM−DIRECT) median **−0.62 ATR**; DIRECT (MFE−MAE)/ATR ≈ **0.00**; CONFIRM ≈ −0.58; fill rate ~33% | **`/STRONG` OFF; no position cond.** | harami | The conditioned signal. Measures **raw** harami excursion (DIRECT) and a structurally-adverse stop variant (CONFIRM). |

**The gap, stated precisely:** the family's live signal = **`/STRONG`-conditioned harami,
anchored at the harami**. Of the five experiments, the two efficacy/capture reads
(EXP-049, EXP-052) ran with `/STRONG` **OFF**, and EXP-049 did not use the harami at all.
EXP-051 built the exact filter the signal needs but never measured its outcomes. So the
central family hypothesis — *does a strong-move-qualified harami reverse, with lead?* — has
**not been tested at all.** This is by the design's own build-from-primitives intent
(P6 default OFF = characterise the unconditioned base first; conditioned-efficacy is 014-B
combined-event work), not a defect in any single experiment.

## 4. Why the unconditioned nulls do not refute the hypothesis

- **`r≈0.50` (EXP-049)** is the *expected* value for 1:1 symmetric equidistant barriers on a
  near-random path from a ZigZag-confirmation entry. It confirms barrier symmetry and a
  symmetric local path on the **unconditioned substrate**; it says nothing about a
  conditioned, harami-anchored entry under asymmetric geometry. Additional reasons it is not
  decisive even for the substrate: the P4 cap bound at the **6-bar floor in 96/99 cells**
  (only ~6 bars of horizon measured — AVWAP's edge lived in the *lifetime* MFE), and the
  **worst-case tie-break** can push cells sitting exactly at 0.50 down to <0.50, manufacturing
  part of the `BELOW_R` readout.
- **Front-loading (EXP-050)** is (a) the **unconditioned** base rate and (b) measured with a
  **non-live** metric the live signal cannot use. A low base rate of end-of-move *raw*
  haramis is fully consistent with the *conditioned* subset reversing. Treating EXP-050 as a
  premise refutation was a **category error** (see §5).
- **CONFIRM worse than DIRECT (EXP-052)** is a real, clean negative — but about a specific
  stop-order construction (stop at the rejected signal-bar extreme), not about the
  conditioned signal. The DIRECT arm's ≈0 excursion is, again, the **unconditioned** harami.

## 5. Reasoning trail — desk pushbacks and operator clarifications (kept verbatim in substance)

Recorded so the *path* to the correct conclusion is auditable, not just the conclusion.

1. **Desk error #1 — "premise strike."** Desk review initially framed EXP-050 (haramis
   front-loaded, not at exhaustion) as the strongest argument *for* closing the family,
   calling it a premise that "no barrier variant repairs."
   **Operator correction:** the thesis only considers haramis *conditioned* on the
   end-of-move / strong-move criteria; EXP-050 measured raw haramis, so it shows raw haramis
   aren't clustered at exhaustion — it does **not** disprove "haramis *at* exhaustion may
   signal reversal." Also asked: did the efficacy experiments apply the conditioning?
   **Resolution:** No — verified `/STRONG` OFF in EXP-049/050/052 and that EXP-049 used no
   harami. Desk conceded; "premise strike" withdrawn.

2. **Desk error #2 — "two orthogonal conditions, both required."** Desk review then claimed
   the family has two separate live filters — magnitude (`/STRONG-STAT`) and position
   (P9 ≥0.67) — and that the conjunction must be applied.
   **Operator correction:** this is not a conflation on the operator's part. Position-in-move
   is **not computable live** (the end pivot is future information); the *only* way to detect
   "end of move" in real time is the lookback-magnitude-percentile test. A move that has not
   reached the X-percentile magnitude is simply **not a valid signal**. So the
   percentile-magnitude condition **is** the operational "end of move," and there is one live
   condition, not two.
   **Resolution:** Desk verified against the doc's causality discipline (lines 113–118,
   137–149) and conceded — position-in-move is descriptive-only; `/STRONG-STAT` is the live
   exhaustion detector. (See §2.)

3. **Standing desk points the operator did not contest (carried as valid):**
   - The mechanical benchmark verdict (EXP-049 0/99 VIABLE) is factual and stands — as a
     statement about the **unconditioned** object only.
   - The conservative tie-break is a real measurement-method risk on an `r≈0.50` substrate
     and warrants an intrabar fill-model audit before any closure (operator added the
     fill-order path assumption: green `O→L→H→C`, red `O→H→L→C`).
   - No AVWAP-style **lifetime move-availability** diagnostic (EXP-047 analog) was run, so the
     "good availability, bad capture" comparison to AVWAP is **unestablished** (see §7).

## 6. Implications for 014-B (what *must* be tested before any closure)

1. **Conditioned-signal efficacy read (the actual hypothesis).** `/STRONG`-conditioned
   haramis (the live magnitude-percentile filter; `/STRONG-HA` as the registered alternative),
   **anchored at the harami** (to capture the lead over the ZigZag giveback), run through a
   capture/excursion read. This is the conjunction EXP-049/050/051/052 never tested.
2. **Binding endpoint that the family's mechanism can express.** First-hit `r` cannot show
   the value of partial exits or trailing stops; a **gross per-event expectancy** (MFE/MAE /
   path-based) endpoint is needed, with `r` kept as a disclosed secondary. *(open question —
   §8 Q1.)*
3. **Intrabar fill realism.** Replace the blanket-adverse tie-break with a path model
   (green `O→L→H→C`, red `O→H→L→C`); re-read the benchmark capture under it to bound how much
   of `r≈0.50` is the tie-break.
4. **Long-horizon move-availability diagnostic (EXP-047 analog).** Lifetime favourable MFE vs
   adverse MAE over the full move, to settle AVWAP's situation (move available, capture
   missing → keep iterating exits) vs a worse one (no move → closure well-supported).
5. **Full barrier-model + new exit/position-management surface** (operator draft
   `.ignore/temp/exit.md`): registered variants `/ADV-EXTREME`, `/ADV-NONE`, `/VPTARGET`,
   `/MAGTARGET`, `/THIRD-EVENT`, `/THIRD-TIME`, plus **new** branches to register —
   `/EXIT-PARTIAL` (scaled favourable exits: first-profitable-close + target + reversal-event;
   percentage-to-target, ≤3 splits) and `/EXIT-TRAIL-STRUCT` (smaller-ATR ZigZag structure
   trailing: new pivot high → trail to recent low for longs, mirror for shorts).
   Used individually or combined.

Position-in-move (EXP-050) stays a **descriptive** lens in 014-B; it is never used as a live
filter.

## 7. Side question — does this family show good move availability + bad capture, like AVWAP?

**Unestablished.** AVWAP closed only after EXP-047 *explicitly* measured lifetime peak MFE
≈ 5–9× the cost floor (availability good, capture bad). Phase 014 ran **no** equivalent
long-horizon read. The two relevant 014-A signals — EXP-049 `r≈0.50` (≤6-bar horizon) and
EXP-052 DIRECT excursion ≈ 0 — *hint* this could be **worse** than AVWAP (no clean favourable
move even gross), but the 6-bar cap means lifetime availability is genuinely **unmeasured**,
and both reads are unconditioned. The apples-to-apples comparison requires the §6.4
diagnostic, run on the conditioned signal. Until then the AVWAP parallel is a hypothesis, not
a finding.

## 8. Process lessons (to prevent recurrence)

1. **Never let an unconditioned characterisation stand in for a conditioned hypothesis.**
   Before citing a null as evidence against a family, confirm the experiment applied the
   family's *defining* conditions. Here, three reads ran `/STRONG` OFF and one used no harami;
   none tested the signal the thesis claims.
2. **Check the entry anchor against the thesis.** EXP-049 anchored on the ZigZag confirmation;
   the thesis edge is the harami's *lead over* that confirmation. An efficacy read anchored
   downstream of the claimed edge cannot test it.
3. **"Live-computable?" is a gate on every proposed signal condition.** Position-in-move reads
   as an intuitive "exhaustion" filter but is non-causal for an in-progress move. The
   real-time proxy (lookback-magnitude-percentile) is a *different* quantity. Distinguish
   descriptive metrics (completed moves) from tradable conditions (point-in-time) explicitly
   in scope.
4. **A symmetric-barrier first-hit rate near 0.50 is a near-tautology, not a finding.** It
   mostly re-states that the barriers are symmetric. Don't read it as "no edge"; it cannot
   see asymmetric geometry, longer horizons, or conditioned populations.
5. **Worst-case tie-breaks bias borderline substrates.** On an `r≈0.50` substrate a blanket-
   adverse fill assumption can manufacture a sub-threshold readout. Audit the fill model
   before closing on a near-boundary null.
6. **Match the metric to the mechanism.** First-hit `r` is blind to partial exits and trailing
   stops; testing exit models under it would foreordain a null. Pick the endpoint the
   mechanism can express *before* implementing.
7. **Closure standard = full, conditioned surface.** AVWAP got nine phases of lever
   exhaustion. A new family is not closed on one symmetric, unconditioned, short-horizon read.

---

*Companion document. The mechanical G1 verdict and routing decision live in
`G1-gate-review.md`; the per-experiment cards live in
`../../families/cf-ha-harami-001/INDEX.md`.*
