# D0-amendment-007 — TRAIN-design exhaustion-cap follow-up authorized (EXP-075 / HYP-028)

**Date:** 2026-06-19
**Checkpoint:** `2026-06-18-016-harami-candidate-screening`
**Authority:** This amendment extends `D0-predeclarations.md` (as already extended by
amendments 005/006) with one additional in-phase TRAIN-design experiment. It does not edit
or supersede any prior clause.
**Trigger:** Operator direction 2026-06-19, following the **completed** EXP-074 substrate-wide
diagnostic (CHARACTERISATION_DELIVERED, audit CONDITIONAL PASS, post-gov APPROVE). This amendment
was first drafted (2026-06-19, 01:43) *before* EXP-074 ran, gating EXP-075 on a formal
`SEPARATOR_FOUND(exhaustion)` verdict; it is **revised here** to reflect EXP-074's actual outcome and
the methodological subtlety it exposed (§"Status post-EXP-074"). The natural next step remains to
**design and lock**, on TRAIN only, an exhaustion-cap entry filter across the same 99-cell substrate,
before any sealed-holdout look is contemplated.

---

## Status post-EXP-074 (binding — read before ratifying)

**The pre-drafted conditionality (formal `SEPARATOR_FOUND` with H1) was NOT literally met, and is
not silently reinterpreted as met.** EXP-074's binding per-domain verdict returned **no
location-monotone uniform lever** (5m NO_SEPARATOR; 15m/30m/1h SEPARABLE_NO_UNIFORM_LEVER; 2h/4h
INCONCLUSIVE_POWER); the pooled disclosed verdict was NO_SEPARATOR. Under the **letter** of the
original conditionality, EXP-075 would not open.

**However, EXP-074 delivered the substantive trigger the condition was written to capture.** The H1
exhaustion-magnitude lead (`m_sofar/atr`) separates the **extreme q05 loss tail** near-universally —
rank-biserial 0.68–0.80 (AUC ≈ 0.84–0.90), the 0.15 material bar cleared in **100% of powered cells
in every powered domain**, median 0.70–0.79, bootstrap 1σ lower bounds 0.60–0.75 — but collapses to
~0/sign-flipped on the location framings (TA_neg/TB_median/TC). It registered as "no uniform lever"
**solely** because the pre-registered all-framing sign-consistency gate is **structurally blind to
tail-shape effects**: high exhaustion makes outcomes bimodal (work/median-positive vs
catastrophic/q05), so a tail-only separator cannot satisfy a same-sign-across-all-framings rule no
matter how strong or broad. This is exactly the bimodality that broke EXP-071's raw mean while the
median/winsorized mean passed — the feature that explains the mean failure is the one the gate vetoes.

**Resolution (the disciplined, non-goalpost-moving path):**

1. EXP-074's binding verdict **stands as written** and is **not** re-adjudicated. The consistency
   gate is **not** retro-edited on EXP-074.
2. EXP-075 proceeds on the **framing-resolved q05-tail evidence**, with the **tail framing
   pre-registered a priori in this amendment** (§"Pre-registered tail-framing design") — a forward
   design choice in a new experiment with its own D0, transparently declared before any EXP-075 code
   runs, not a post-hoc relaxation of a sealed criterion.
3. This proceed requires **explicit operator ratification of this revised amendment**, made with the
   conflict above in full view. If the operator judges the framing-resolved trigger insufficient,
   EXP-075 does not open and the path routes toward closing CAND-001.

**EXP-075's scope and hypothesis must state this contingency plainly** — present the q05-tail H1
result as the (now obtained) motivating finding *and* its gate-masked status, not as a clean
`SEPARATOR_FOUND`.

## What this authorizes (when the gate above is met)

A single additional Phase 016 experiment:

- **EXP-075 / HYP-028** — TRAIN-design of an exhaustion-cap entry filter on the full 99-cell
  MA-substrate harami matrix. Four design arms: forms **F1** (single upper cap on
  `m_sofar/atr`; the existing `/STRONG-STAT` p75 lower gate is retained, so F1 is itself a
  lower-p75 + upper-cap band) and **F2** (strong-stat-excess normalizer-robustness form — an
  upper cap on `m_sofar/p75_thr` instead of `m_sofar/atr`) ×
  selection methods **M-GLOBAL** (one pre-registered uniform rule, a fixed pooled-TRAIN
  quantile U ∈ {p85, p90, p95}, the **only** deployable arm) and **M-PERCELL** (best U per
  cell, **diagnostic-only overfit ceiling, never deployed**). Headline diagnostic = the
  overfit premium (per-cell gain − global-rule gain). Scope:
  `python/experiments/EXP-075/scope.md`. Registered in `multiplicity-registry.md` (Phase 016
  batch, HYP-028).

## Lessons carried from EXP-074 (binding on EXP-075's design)

EXP-074 surfaced two transferable methodological lessons. Both are **binding requirements** on
EXP-075, not advisory notes.

**Lesson 1 — pooled / unstratified evaluation masks diagnostic structure.** EXP-074's single pooled
verdict (`NO_SEPARATOR`, 67/99) hid the real structure: 15m/30m/1h are the separable core
(per-cell rate 0.88/0.71/0.94), 5m is noisy (0.35), 2h/4h underpowered (0 powered). The binding
read had to be **per-domain**. *Implementation in EXP-075:* (a) the improvement criterion (item 4)
is adjudicated **per domain**, with the band-pooled number disclosed-only; (b) a per-cell disclosure
accompanies it; (c) **the masking risk re-appears one level up and is explicitly guarded** — the
M-GLOBAL cap is a *pooled-quantile* threshold (correct, since a deployable rule must be one rule),
but a single global `U` can help one domain while hurting another, so EXP-075 must report **whether
the global cap helps each domain separately**, never a band-pooled "it helps on average." This makes
the M-GLOBAL-vs-per-domain story explicit, parallel to the M-GLOBAL-vs-M-PERCELL overfit story.

**Lesson 2 — a gate must not be so rigid that it nullifies a worthwhile observation.** EXP-074's
all-framing sign-consistency gate (a valid anti-p-hacking guard for *location* effects) vetoed the
strong, broad, replicated q05-tail H1 signal because that signal is *tail-shaped*, not
location-monotone — it demanded distribution-wide monotonicity a real tail-only mechanism cannot
satisfy. *Implementation in EXP-075:* (a) **no separation / framing-consistency gate is re-run** —
EXP-075's endpoint is the strategy's own legs (item 1); (b) the worthwhile observation H1 is carried
forward via a pre-registered tail framing rather than discarded; (c) the gate's legitimate
anti-p-hacking role is **replaced**, not removed, by pre-registration + fixed grid + global-rule
deployability + holdout confirmation (see "What replaces the gate's anti-p-hacking role" below); and
(d) the bimodality the gate was implicitly worried about is caught by item 4's **joint** criterion,
the economically correct instrument. The general rule recorded for future phases: **when a guard
rejects an observation, check whether the guard is the wrong instrument for the observation's shape
before discarding the observation — and never retro-edit the guard on the experiment it just
judged; re-pose the question a priori in a new design.**

## Pre-registered tail-framing design (locked before any EXP-075 code runs)

Fixed now, to prevent post-hoc selection and to make the gate collapse transparent and a priori:

1. **No separation gate is re-run; the q05 finding is the design rationale, not the endpoint.**
   EXP-075 does **not** re-run a feature-separation screen and therefore re-applies **no**
   framing-consistency gate at all — the all-framing consistency rule was a *characterization*
   construct in EXP-074 (deciding "is this feature a separator"), and it has no place in a
   cap-design experiment whose endpoint is the strategy's own legs. The q05-tail H1 result is used
   only as the **design rationale**: it establishes that high exhaustion drives the catastrophic
   left tail, so an **upper cap on `m_sofar/atr` is the lever** and fixes its direction. The
   threshold `U` is then chosen by the pre-declared mechanical M-GLOBAL rule (pooled-TRAIN quantile
   from {p85,p90,p95}), **not** by any separation statistic. The cap is judged **solely** by the
   direct economic endpoint in item 4. The location framings (TA_neg/TB_median/TC) are reported as
   disclosure, never as gates.
2. **Lead feature only; redundancy and refuted features dropped.** The cap acts on H1
   (`m_sofar/atr`, F1) with F2 as the strong-stat-excess normalizer robustness form. **`favdist_atr`
   is dropped** (EXP-074 W1: `favdist_atr ≡ 0.5·m_sofar/atr` exactly — redundant, identical
   rank-statistics). **H2 (polarity agreement) is not pursued** (EXP-074: refuted — median ≈ 0, 0%
   of cells clear the bar).
3. **Band pre-declared.** Primary = the **15m–1h separable core** (EXP-074 per-cell separability
   0.88/0.71/0.94). **5m disclosed/secondary** (credible — 100% q05 H1 breadth — but noisier under
   the full gate, per-cell rate 0.35). **2h/4h excluded** (0 powered cells, INCONCLUSIVE_POWER).
4. **"Materially improves" criterion (TRAIN-design endpoint, binding) — evaluated PER DOMAIN, never
   pooled.** For the capped `N-PARTIAL-V2A` to count as improving a domain, that domain must
   **lift the raw-mean leg to CI_low > 0** while **retaining** median CI_low > 0 and beats-RM-native
   CI_low > 0, **without** cutting tradable event count below the pre-declared retention floor
   (retain ≥ 70% of the domain's in-band events at the chosen cap). The verdict is reported as a
   **per-domain vector** (15m / 30m / 1h; 5m disclosed) plus a per-cell disclosure; the **band-pooled
   number is disclosed-only and does not bind** (EXP-074 Lesson 1 — see below). Endpoints use the
   frozen EXP-068 moving-block bootstrap machinery.

**Why item 4's *joint* criterion is the correct instrument (and why it, not the consistency gate,
handles the underlying risk).** EXP-074 showed the bimodality directly: high `m_sofar/atr` drives the
q05 catastrophic tail **and** *raises* the typical/median return (TC slightly negative — higher
exhaustion, higher central return). So an upper cap necessarily **trades tail-suppression against
median-erosion**: it removes catastrophic losers but also removes some median-positive winners. The
binding criterion deliberately requires **all** of {raw-mean CI_low > 0 ∧ median CI_low > 0 ∧
beats-RM CI_low > 0 ∧ ≥ 70% event retention} to hold *simultaneously* — precisely so the cap is
credited only if killing the tail lifts the mean by **more** than it costs the median and event
count. A cap that merely trades one leg for another fails. This is the economically correct test the
all-framing consistency gate could never express.

**What replaces the gate's anti-p-hacking role.** Dropping the consistency gate does **not** drop
multiplicity discipline; it moves it to the instruments appropriate for a tail-targeted cap design:
(i) a **single pre-registered lead** (H1) and a single pre-registered tail framing — no feature or
framing search; (ii) a **fixed pre-declared threshold grid** (p85/p90/p95), no finer search or
post-hoc extension; (iii) **M-GLOBAL-only deployability** with M-PERCELL retained purely as the
disclosed overfit ceiling; and (iv) the rule that any locked filter is **non-confirmatory** until a
**separate one-shot sealed-holdout** read on fresh strata. The guard changes from "consistency
across framings" (the wrong instrument for a tail effect) to "pre-registration + fixed grid +
global-rule deployability + holdout confirmation" (the right ones).

## Binding constraints (carried from Phase 016 D0; reaffirmed)

1. **No TEST contact.** EXP-075 reads the **TRAIN** stratum only (`[0, train_cutoff)`) across
   all 99 cells. **0 counted TEST reads.** `test-read-ledger.md` unchanged.
2. **Holdout sealed.** The final-30% global holdout is never loaded.
3. **No candidate slot.** CAND-001 remains the only consumed slot; EXP-075 consumes none.
4. **The only new free parameter is the exhaustion-cap threshold U**, selected by the
   pre-declared M-GLOBAL rule (pooled-TRAIN quantile from the predeclared p85/p90/p95 grid),
   **not** by maximizing per-cell TRAIN performance. M-PERCELL is the overfit ceiling and is
   never promoted to a deployable filter or carried to any holdout.
5. **Frozen machinery.** Reuse the certified EXP-068/074 resolution and `N-PARTIAL-V2A`
   return machinery unchanged in semantics; the cap is an entry-time gate on the existing
   `cond` mask (`cond ∧ exhaustion-within-bound`) — it only removes entries, never reaches
   forward.
6. **Real-price outcomes**; HA used only for harami detection. Detection on HA candles.

## Routing of the outcome (pre-stated)

Routing reads the **per-domain** improvement vector (item 4) jointly — never a band-pooled average
(EXP-074 Lesson 1):

- **FILTER_PROMISING** → under M-GLOBAL the cap meets the item-4 criterion in a band-core **domain**
  (15m/30m/1h) — reported per domain, with a modest overfit premium vs M-PERCELL and a modest
  global-vs-per-domain gap → freeze the global filter (band-restricted to the domains where it holds)
  and route to a **separate** one-shot sealed-holdout-confirm experiment (its own EXP-ID / D0; fresh
  strata only — never the EXP-071-consumed TEST strata).
- **FILTER_OVERFIT** → per-cell/per-domain ceiling gains (M-PERCELL) but M-GLOBAL meets item 4 in few
  or no domains / large overfit premium / global cap helps one domain while hurting another → do not
  spend the holdout; routes toward closing CAND-001 (or a band-restricted re-scope).
- **FILTER_INEFFECTIVE** → even the M-PERCELL ceiling fails item 4 in a meaningful share of cells in
  any domain → exhaustion cap is not a lever; supports closing CAND-001 cleanly.
- **INCONCLUSIVE_POWER** → too few cells clear the retention/event floor in the band core; recorded,
  no routing change.

## Why this is in-scope for Phase 016 rather than a new phase

Like EXP-074, EXP-075 introduces no new TEST contact, no new candidate, and no new registered
variant (it exercises the already-registered exhaustion magnitude conditioning as an entry
gate; the cap threshold is the single new free parameter, TRAIN-selected by a mechanical
rule). It is the **design** step that converts the EXP-074 diagnostic into a frozen candidate
filter, adjudicated at G-016 alongside EXP-071/074. The sealed-holdout confirmation of that
frozen filter is explicitly a **separate** future experiment under its own D0.

## Operator ratification

The manual-execution gate stays closed until the operator ratifies this **revised** amendment with
the §"Status post-EXP-074" conflict in full view — i.e. an explicit decision to proceed on the
framing-resolved q05-tail H1 evidence (the literal formal `SEPARATOR_FOUND` condition was not met).
Recorded here as the binding pre-execution condition. EXP-075's own Stages 1–4 (scope, analysis
plan, pre-execution governance) follow under the standard pipeline before any code runs.
