# Retrospective Reflections — The First Two Closed Candidate Families

**Date:** 2026-06-19
**Author:** Research-pipeline retrospective synthesis
**Scope:** `CF-AVWAP-001` (Phases 004–013, EXP-020–047) and `CF-HA-HARAMI-001`
(Phases 014–016, EXP-048–075), plus the framework-and-referee era
(Phases 001–003b, EXP-001–019) and INFR-001/002 that made them possible.
**Sources:** every checkpoint `retrospective.md`, the per-phase `D0-predeclarations.md`
and `D0-amendment-*` files, the `014-A-conditioning-gap-and-validation-lessons.md`
companion, the master `INDEX.md` synthesis tables, and the candidate-family registry.
**Status:** reflective synthesis only — predeclares nothing, reads no data, touches no
holdout. Intended as the standing reference for designing the next family.

---

## 0. One-paragraph verdict

Two candidate families were taken from first principles to closure with the global
holdout still sealed and the TEST budget almost entirely intact (6 of a large lifetime
cap spent, all on one harami screen). **Neither produced a tradable candidate, and that
is the programme working as designed, not failing.** Both families had a *real* edge —
AVWAP's was relative-not-absolute and cost-dominated; the harami's was a genuine,
replicated *median* edge on the MA substrate. Both died for the same deep reason
expressed two different ways: **the favourable signal and the binding economic obstacle
were driven by the same unseparable mechanism.** AVWAP enters moves 5–9× the cost floor
but no deterministic exit converts the peak into a net-of-cost capture (capture geometry).
The harami's median edge and its mean-killing loss tail share one driver — entry
exhaustion bimodality — so no entry filter lifts the mean without erasing the median. The
single most valuable infrastructure asset built across both families is the **gate +
file-drawer + frozen-rule discipline** that let a fully negative phase cost zero
irreversible reads and produce honest, debate-free closures.

---

## 1. The two families at a glance

| | CF-AVWAP-001 | CF-HA-HARAMI-001 |
| --- | --- | --- |
| Phases | 004–013 (10) | 014–016 (3) |
| Experiments | EXP-020–047 (~28) | EXP-048–075 (~24) |
| Thesis | Anchored-VWAP bounce at regime pivots is a tradable reaction | HA harami at the exhaustion of a strong move is a tradable reversal with lead |
| Best real signal found | Conditional event edge real on all 3 domains (EXP-021/022/028); EURUSD-4h TEST-pass +40.56 bps (EXP-037) | MA-native conditioned harami: median edge beats own-substrate random 85/99 (EXP-060B); mean-positive champion composed at G-015 (EXP-068) |
| TEST contact | 4 reads (EXP-037/038 pass; EXP-032 holdout INCONCLUSIVE, spent) | 6 reads (EXP-071, all binding strata 1/2) |
| Closing outcome | **ANCHOR_MOVE_FLAT** — every registered lever measured flat | **CLOSE_FAMILY** — median edge not convertible to a confirmable mean |
| The binding wall | **Capture geometry** — available move 5–9× floor, no exit realizes it net of cost | **Entry bimodality** — exhaustion magnitude separates the q05 loss tail but high-exhaustion entries are bimodal (big winners + catastrophic losers) |
| Holdout at close | sealed (one unrelated shot spent, INCONCLUSIVE) | sealed (never touched) |

**The symmetry is the headline.** AVWAP closed on the *exit* side (can't capture an
available move); the harami closed on the *entry* side (can't filter a contaminated
signal). Stated abstractly both are the same failure: *the lever that would fix the
binding obstacle also destroys the edge.* That recurrence is the programme's most
important empirical generalisation so far (see §4.1).

---

## 2. Infrastructure & pipeline lessons

These are lessons about the *test framework, gates, governance, and experiment process* —
the machinery, independent of any strategy.

### 2.1 The gate/file-drawer/frozen-rule stack is the crown jewel

- **Inverted-inference structure makes a negative phase free.** Phases 011, 012, 013 each
  closed fully negative for **zero TEST reads** because the gross/TRAIN screens were
  designed to *fail cheaply before* any net machinery or holdout contact. A negative result
  costs almost nothing; only a positive earns the right to spend an irreversible read. This
  is the single most important structural decision in the whole programme.
- **Freeze the rule, not the story.** Phase 013's pre-committed routing survived even
  though its *narrative premise* ("move is capped near the cost floor") was refuted by the
  data — the move was 5–9× the floor. Because the mechanical SHIFTED_VIABLE composition rule
  was frozen, the close was clean and debate-free regardless. **Predeclare mechanical
  verdicts; never predeclare explanations.**
- **Predeclared gates resist post-result goalpost-moving — in both directions.** At G-015 a
  thin mean breadth made the discretionary "MEAN_RECOVERABLE down-route" tempting, but the
  raw-mean co-primary mechanically composed, so PROCEED was the honest verdict (Phase 015 L1).
  At EXP-074 the all-framing consistency gate *vetoed a real q05-tail signal*; the
  disciplined resolution was to let the verdict stand, **not** retro-edit the guard, and
  re-pose the question a priori in a new design (EXP-075). The rule: *never edit a guard on
  the experiment it just judged* (Phase 016 L2).
- **Two-speed gating works.** Lenient gates to keep exploring, strict gates to spend the
  one-shot holdout (Phase 008). Nothing closed on a wide CI; nothing was promoted on one.

### 2.2 Calibrate the verdict rule to the realized data layout *before* outcome contact

- The Phase 009 holdout read returned INCONCLUSIVE specifically because the **calibration
  margin** (`m_cell`) did its job: the frozen bootstrap's uncorrected dual rule had a
  *measured* null FPR of 0.0715 at that exact 16-cluster layout — an uncalibrated read would
  have over-claimed CONFIRMED. The margin kept the books honest on the single most expensive
  read in programme history.
- Small-n bootstrap p-values are meaningless without their measured calibration at the
  realized cell structure. R1.2-style margins flipped XAUUSD (Phase 008) and later saved the
  holdout (Phase 009). **Never quote a small-n `boot_p` without its calibration.**

### 2.3 Match the metric — and the guard — to the mechanism's *shape*

This recurred at three levels and is the deepest methodological thread:

- **First-hit `r` is blind to partial exits and trailing stops.** Testing exit models under a
  symmetric first-hit rate would foreordain a null (014-A lesson #6). A symmetric-barrier
  first-hit rate near 0.50 is a near-tautology — it restates that the barriers are symmetric;
  it cannot see asymmetric geometry, longer horizons, or conditioned populations (014-A #4).
- **An anti-p-hacking guard tuned for *location* effects is structurally blind to
  *tail-shape* effects.** EXP-074's consistency gate vetoed the q05-tail separator that was
  the actual explanation for EXP-071's mean failure (Phase 016 L2).
- **A bimodal mechanism must be judged on the full joint economic net, never a separation
  screen.** EXP-075's four-leg `improved` criterion (raw-mean ∧ median ∧ beats-RM ∧
  retention) correctly returned negative; a q05-separation screen would have looked promising
  because the cap *does* suppress the tail — while also stripping the winners (Phase 016 L3).
- Generalisation: **pick the endpoint the mechanism can express, and the guard that can see
  the effect's shape, *before* implementing.** Mismatches manufacture false negatives.

### 2.4 Never let an unconditioned (or narrow) characterisation stand in for the hypothesis

This is the most dangerous near-miss the programme caught, twice:

- **014-A almost closed the harami family on experiments that never ran its signal.** Three
  of five 014-A reads had `/STRONG` OFF and one used no harami at all — the *conditioned,
  harami-anchored* signal the thesis actually claims was untested. The unconditioned nulls
  (`r≈0.50`, front-loading) were evidence about objects the hypothesis says nothing about.
  Closing there would have been a category error (014-A lessons #1, #2).
- **The same error nearly recurred at the object level in Phase 015**: the EXP-060B/061
  `M`-arms measured a *native* MA-segment object but were *labelled* hybrid, so the genuine
  signal object was almost never computed. D0-amendment-001 (dual parallel substrates) caught
  it before the surface re-run. Had the original hybrid-primary framing stood, the real edge
  would have been mislabelled and under-measured (Phase 015 L3).
- Rule: **before citing any null as evidence against a family, confirm the experiment applied
  the family's defining conditions and anchored on the claimed edge.** "Live-computable?" is a
  gate on every proposed signal condition — position-in-move read as intuitive "exhaustion"
  but is non-causal for an in-progress move; the real-time proxy (lookback-magnitude
  percentile) is a *different quantity* (014-A #3).

### 2.5 Pooled evaluation assumes an unproven generalisation across cells

This is stronger than "pooling masks structure" — **a pooled or equal-weight verdict
silently asserts that the parameter/effect is the same across domains and instruments, a
relationship that is almost never established and was repeatedly false.** EXP-074's single
pooled verdict hid that 15m/30m/1h were the separable core while 5m was noisy and 2h/4h
underpowered; the masking recurred one level up in EXP-075's pooled-quantile M-GLOBAL rule
and was caught only by reporting per domain (Phase 016 L1). The AVWAP analogue: equal-weight
aggregation let one high-cost instrument (BTCUSD, 16 bps RT) veto a whole domain (Phase 007),
and a pooled MDE map was systematically *conservative* vs per-instrument MDEs (EXP-008). A
pooled number is only legitimate once cross-cell homogeneity is itself a tested, supported
claim. **Default to per-stratum adjudication; treat any pooled statistic as a disclosure, not
a verdict, until homogeneity is demonstrated.**

### 2.6 Cheap diagnostics keep relocating the binding constraint

The screen-before-machinery ordering was validated three consecutive times (011→012→013) and
repeatedly *moved* the diagnosis: Phase 013's TRAIN-only move-size read overturned nine
phases of "move too small" narrative in a single pass (the move is 5–9× the floor; the
problem is the exit). **A few seconds of gross TRAIN compute can redirect a whole family.**
Run the cheapest decisive read first.

### 2.7 Pre-execution governance and amendments are load-bearing, not ceremony

- The **framework era (001–003b) is itself an infrastructure lesson**: the keystone
  portfolio-fitness referee was *refuted* (EXP-015), repaired via adversarial review
  (amendment A1: L2 standalone-significance leg driven by BTCUSD), and only the validated
  two-referee suite shipped, with the incremental unit deferred to a follow-up (003b). The
  programme spent ~5 phases hardening the *yardstick* before measuring any real signal — and
  it paid off: every subsequent verdict rode a calibrated, dogfood-tested gate.
- **Amendments that catch a framing error before data contact are wins, not debt.** A1
  (incremental unit), the EXP-042 FRAMING_ERROR set aside with 0 slots (Phase 011),
  D0-amendment-001 (dual-object), D0-amendment-005/006/007 (the EXP-074/075 follow-up routing)
  each corrected the experiment *before* it could contaminate a decision. The discipline is:
  registry branch definitions are the authority; a mislabelled object is set aside, not
  reinterpreted post-hoc.
- **A "faithful re-screen" must state its execution path explicitly in scope** (Python
  re-analysis vs cTrader per-bar) — the EXP-028 omission (a per-bar streaming gap) was a
  Stage-4 governance lesson (Phase 006).

### 2.8 Reproducibility and external anchoring caught real bugs

- INFR-001/002 (cTrader branch + new-universe collection) established 1e-9-bps external
  anchoring and 108/108 C# transcription parity. The cTrader confirmation of EXP-028
  (|Δeffect| ≤ 0.054 bps across domains) is what upgraded a Python-only positive to
  production-confirmed.
- The **fixed per-cell bootstrap seed** (Phase 015 P3) removed the ±1–2-cell BENCH viability
  drift the 014-B G2 had to caveat. Determinism is not optional polish; it changes whether a
  marginal cell is "viable."

---

## 3. Strategy-modelling lessons

These are lessons about *what the market actually did* — what works, what moves performance,
what produced signal vs noise, and where the information was.

### 3.1 What worked (produced real signal)

- **Conditional event evidence was repeatedly real.** AVWAP bounce reaction was EVIDENCE_FOR
  on all three domains (EXP-021 +3.8/+9.1/+37.6 bps; EXP-022 completion +23.9/+21.9/+26.4 pp,
  Holm p=0.0003; EXP-028 +5.78/+23.38/+69.02 bps). The harami conditioned signal was non-null
  (EXP-053) with an MA-substrate median edge beating own-substrate random **85/99** (EXP-060B)
  and a mean-positive champion that composed at G-015 (EXP-068). **The signals were there.**
  Detection was never the problem.
- **Capture efficiency was the one AVWAP lever that delivered** — and only on EURUSD-4h.
  EXP-033/037 (the FH H\*=12 fixed-horizon exit) turned a cost-dominated edge into a
  TEST-pass (+40.56 bps, Holm adj_p≈0.004). Of the three admissible levers for a
  cost-dominated edge — selectivity, instrument selection, capture efficiency — **only capture
  efficiency moved the needle** (Phase 008). Selectivity was empty (0/9 conditioning cells,
  EXP-035); instrument selection alone was necessary-but-not-sufficient.
- **Substrate choice is a first-class signal lever, not a detail.** The harami expresses a
  real median edge on MA(20,50) that it does **not** express on ZigZag (85/99 vs 3/99,
  EXP-060B). The *same signal* is viable or dead depending on the substrate the move is
  defined against. This was the single highest-information finding in the harami family and
  the reason closure was (correctly) refused at the Phase 014 G2.
- **Bounded-downside / position-management exits were the strongest harami lever.**
  `/EXIT-PARTIAL` (scaled favourable exits, V2A arm) was EVIDENCE_FOR repeatedly (EXP-059
  53 wins/17 instruments; EXP-066 PARTIAL-V2A 21 cells, mean-positive in 11). Trailing-stop
  structure (`/EXIT-TRAIL-STRUCT`) was detrimental within the cap.

### 3.2 What did not work (consistent negatives = information)

- **Untuned/baseline overlays never qualify.** EXP-023 (AVWAP baseline) REFUTED through the
  frozen suite; this recurs as "the events, not the exits, are the problem" on 1h (triply
  confirmed, EXP-030/033/039). A real event edge does **not** imply a tradable strategy.
- **Favourable-target and third-barrier levers are empty on both substrates.** Harami:
  EXP-056 (0/8 favourable variants), EXP-058 (0 third-barrier), replicated on MA in EXP-064/065.
  These levers are *measured and closed*, not untested — high-value negatives.
- **Entry-parameter tuning does not move a gross edge that isn't there.** AVWAP α∈{0…1} and
  MA(10,25)…(60,150) moved typical-cell gross ~1–2 bps against 5–20 bps floors (EXP-046).
  Exit training *reallocates* gross edge; it cannot *raise* it (Phase 011: 31/37 cells
  gross-positive, all net −5 to −7 bps).
- **The anchor lever was inert at the ratified parameter.** k=1.0 ATR-prominence coincided
  with the baseline running extreme 94.6–98.5% of the time (EXP-047) — the rule didn't bite.

### 3.3 Where the performance actually lives (highest-impact factors, ranked)

1. **Exit / capture geometry.** AVWAP's entire fate hinged on it — available move 5–9× the
   floor, but no deterministic exit converts the peak to net capture. The next family "must be
   chosen for how it *exits*, not how it enters" (Phase 013 §8).
2. **Substrate the move is defined against.** Flipped the harami from dead (ZigZag) to
   median-viable (MA). Larger effect than any entry or exit parameter within a substrate.
3. **The entry distribution's *shape* (tails/bimodality), not its mean.** The harami's mean
   was sunk by an exhaustion-driven bimodal loss tail; winsorized mean was positive in 46–73
   cells vs raw-mean-positive in 10–14 (EXP-068 post-hoc). Tail structure dominated the
   tradability verdict.
4. **Costs.** The binding constraint in the entire AVWAP family was gross-edge-vs-cost-floor,
   not signal. "The fair fight was held; costs won" (Phase 011). Frozen CONSERVATIVE costs
   consumed every few-bps gross edge.
5. **Instrument/domain heterogeneity.** EURUSD-4h carried AVWAP; BTCUSD's 16 bps RT vetoed
   equal-weighted domains; the harami's defensible core was ~5 non-4h FX cells. Edges were
   narrow and instrument-specific, never broad.

### 3.4 Signal-to-noise: what produced clean reads vs mush

- **Highest S/N:** TRAIN-only gross diagnostics with a frozen cost floor and a per-cell
  matched-random null (EXP-047, EXP-060B, EXP-074). Cheap, decisive, no multiplicity spend.
- **Highest S/N per TEST dollar:** the one-shot, freeze-before-outcome confirmation with a
  calibrated margin (EXP-037 pass; EXP-032 honest INCONCLUSIVE).
- **Lowest S/N (avoid):** 4h reads at 32–86 events (SEs 7–30 bps) — the power wall blinded
  every substrate-bound exit comparison (Phase 010); pooled/equal-weight aggregations that let
  one cell dominate; symmetric first-hit `r` on a near-random path (~0.50 tautology).
- **Power must be checked against the estimand at scope time.** 4h INCONCLUSIVE was
  near-foreordained in several phases (Phase 007). Don't spend design effort where the data
  cannot resolve the question.

### 3.5 Where the information was gained (what we now *know* vs assumed)

- We **know** the AVWAP-bounce substrate cannot pay frozen conservative costs under *any*
  registered lever, and that its binding constraint is capture geometry, not move
  availability — a corrected diagnosis, not an assumption.
- We **know** the conditioned harami carries a real but median-only MA-substrate edge whose
  mean is unfixable at entry because the favourable signal and the loss tail share one driver
  (exhaustion bimodality).
- We **know** the reusable infrastructure works end-to-end: data layer, event-level method
  calibration (EXP-027/070), the frozen referee suite, cTrader parity, the TEST-read ledger,
  and the file drawer all held across 16 phases with the holdout intact.

---

## 4. Cross-cutting meta-lessons (the generalisations worth carrying)

### 4.1 The recurring death pattern: edge and obstacle share one mechanism

Both families produced a real edge and both died because **the lever that would remove the
binding obstacle also removes the edge.** AVWAP: the move is available but the exit that
would capture it net-of-cost does not exist on this geometry. Harami: the median edge is
real but the entry filter that would lift the mean strips the winners with the losers.
**Design implication (the single most actionable lesson):** for any future candidate,
establish *early — before any TEST read —* that the binding outcome leg (net mean) and the
favourable signal are **not driven by the same unfilterable mechanism** (Phase 016 L4). Add a
pre-TEST "separability check" to the standard scope: can the obstacle be moved without moving
the edge? If not, the candidate is a median-only artifact, however real.

### 4.2 Robust metrics are the better-rounded story — *and* a median edge is not a candidate

Two truths that must be held together, not traded off:

- **Make robust/median-based metrics the primary KPI lens.** The raw mean is fragile to
  exactly the tail the harami family was killed by; on its own it misleads. The *shape* of the
  family's failure was only diagnosed properly because the programme looked at the **median
  first, then the winsorized mean, and only then** read the gap to the raw mean as evidence of
  left-tail skew (EXP-068 winsorized-mean diagnostic: positive in 46–73 cells vs raw-mean
  positive in 10–14). A raw-mean-only screen would have returned a flat negative with no
  explanation. **Lead with median + a tail-robust mean + an explicit tail diagnostic; the
  spread between robust and raw is itself the highest-information signal.**
- **But a median edge is still not a candidate.** CF-HA-HARAMI-001 proves a replicated, clean
  median edge can yield zero tradable candidate. Median viability is *necessary, nowhere near
  sufficient.* The resolution of the apparent tension: use robust metrics as the primary
  *analytical* lens to understand the distribution, while keeping the binding *economic*
  endpoint (raw mean, net of cost) emitted from the **start** when the signal sits over
  asymmetric/bimodal geometry — so the robust-vs-raw gap is a diagnostic input to a separability
  decision (§4.1), not a late surprise (014-A #6, Phase 014/016 carry-forward). The mistake is
  not "using robust metrics"; it is letting *either* metric stand alone.

### 4.3 Closure standard = the full conditioned surface, never one read

AVWAP got nine phases of lever exhaustion before closing; the harami was explicitly *not*
closed at 014-A (one unconditioned read) nor at the Phase 014 G2 (one geometry), because
EXP-060B's gap-fill showed the wall was substrate-specific. "No early closure on one
geometry" produced the accurate two-sided verdict both times (014-A #7). A new family is
never closed on a single symmetric, unconditioned, short-horizon read.

### 4.4 The programme's integrity held completely

Across 16 phases, ~52 experiments, two full families: holdout never improperly touched (one
sanctioned shot, INCONCLUSIVE, spent honestly); 6 of a large TEST budget used; every refuted/
inconclusive item retained in the file drawer (never deleted or reused); no goalpost-moving,
no post-result cell selection, no parameter tuning beyond pre-registered mechanical selection.
**This is the asset that makes every negative result trustworthy and the eventual positive —
when it comes — credible.**

---

## 5. Pipeline weaknesses & required process changes (needs immediate attention)

§2 records what the framework did *well*. This section records process changes worth making.
**Evidence note (after verification + operator clarification):** the first two items were first
written as blunt "the audit never does X" failures; that overstated it. Reading the artifacts
shows the audit *can* and *did* produce deep why-diagnosis (EXP-074) and the pipeline *did* force
a fix-and-rerun (A1). **But in every instance the behaviour was operator-triggered, not
autonomous** — EXP-074's audit opens "the operator's caution is well-founded" (the masking was
raised by the operator first, then confirmed), and the A1 rerun came from operator-driven
adversarial review. Absent the operator catching it, the pooled verdict and the conditional pass
would have stood. So the gap is real and is precisely **reliability/autonomy**: the pipeline does
not self-trigger these checks. That is a genuine hardening target, not cosmetic. Items 5.3/5.4
are evidenced directly from the artifacts.

### 5.1 Make per-stratum "why"-diagnosis a *mandatory, uniform* audit deliverable

**What the evidence shows.** The audit *can* produce the diagnosis — EXP-074's audit makes the
pooled-masking finding its **explicit headline** (W2: `msofar_atr` separates the q05 tail in
100% of powered cells; "no uniform lever" must not be read as H1 refuted; reading it literally
would misroute CAND-001), with a per-domain Statistical-Sanity table and an Assumption-Validation
row stating the consistency gate "DOES NOT HOLD for tail-shape effects." But it produced this
**only because the operator raised it first**: the audit's own words are "the operator's caution
is well-founded and is the headline of this audit." The masking was *operator-originated,
audit-confirmed.* There is no instance in the record of the audit autonomously flagging a pooled
verdict as masking structure. So the concern is correct as a matter of **autonomy**: left to
itself, the pipeline ships the pooled headline.

**The hardening.** Encode a **standing, non-optional audit requirement** that fires on *every*
verdict regardless of whether anyone questioned it: (a) a per-stratum re-derivation that must
affirmatively confirm the pooled headline is not masking heterogeneity; (b) an explicit
mechanism statement for the SUPPORTED/REJECTED result; (c) a check on whether the binding gate
is the wrong instrument for the effect's shape (§2.3). The EXP-074 audit is the proof this is
*achievable*; the requirement is what makes it happen *without* the operator. Candidate
implementation: extend `experiment-auditor` (or add a dedicated "results-forensics" pipeline
skill) and make Stage 8 governance reject any audit lacking the per-stratum masking check.
*Priority: immediate — this is the gap that put a real signal one operator-comment away from
being buried.*

### 5.2 Keep (and codify) the materiality-gated fix-and-rerun rule that already operates

**What the evidence shows.** Fix-and-rerun *has* happened — the A1 amendment forced a **code
re-run and full re-audit** of EXP-013/014/015 — but, like §5.1, it was **operator/adversarial-
review-triggered, not an autonomous audit action.** Separately, the CONDITIONAL-PASS warnings I
first cited as "documented but not fixed" were in fact assessed and found **verdict-immaterial**
by the auditor (EXP-074 W1 a structural identity "no verdict changes"; W2 "not a code bug";
EXP-075's Warning a missing disclosure *column*, "Impact: none on the verdict"), so those are not
examples of a buried bug. The honest position: I found **no** case of a verdict-moving bug
documented-and-ignored, *and* I found **no** case of the audit autonomously *forcing* a rerun —
every rerun traces to operator intervention.

**The hardening.** Give the audit stage **explicit, autonomous blocking authority**, written
into the skill: any finding that could change sample membership, a denominator, a metric value,
temporal/causal validity, or the verdict itself **must** force a fix + re-execution before
Stage 6 — the auditor decides this itself, not after an operator flags it. "Document-and-proceed"
is permitted *only* for findings the audit explicitly shows are verdict-immaterial (the EXP-074/075
materiality assessments are the model for *how* to clear that bar). The point is to remove the
dependence on the operator noticing. *Priority: high. If you recall a specific verdict-moving bug
that was documented but not rerun, name it and I'll fold it in as the anchoring example — I did
not find one in the audits sampled (read EXP-074/075 fully, verdict lines of all 70, A1 history).*

### 5.3 Magic-number gate thresholds are not robust — calibrate or adapt them

**The defect.** Several binding gates rest on **arbitrary constants** that do not adjust to the
hypothesis, data, or strategy in front of them: the `≥5 cells over ≥3 instruments` composition
bar, the EXP-075 `+0.15` improvement bar (and its `0.10` robustness twin), percentile cutoffs
like p75/p85/p90/p95, the 6-bar horizon floor. A fixed constant that bites hard in one cell and
not at all in another (the k=1.0 anchor that was 94.6–98.5% inert, EXP-047) is a gate in name
only, and an over-strict constant can **veto a real effect** (the EXP-074 all-framing
consistency gate rejecting the genuine q05-tail separator, §2.1/§2.3).

**The contrast that shows the right pattern.** The programme already has the antidote: the
**calibrated margin** `m_cell`, fit to the realized cell layout before outcome contact
(Phase 009), and the **mechanically-selected** EXP-075 `U`. These adapt to the data and held the
books honest. The fixed constants did not.

**Required change.** Treat every gate constant as a liability to be justified. Prefer
**calibrated thresholds** (fit to the realized layout, like `m_cell`), **data-derived**
thresholds (mechanically selected, disclosed), or at minimum a **pre-registered sensitivity
band** with the routing shown to be invariant across it (as EXP-075 did at 0.10/0.15). Before
ratifying any new constant at G0, run the cheap **fixture/bite check** Phase 013 L2 already
prescribes — measure whether the threshold actually discriminates on synthetic data — and
re-anchor it if it does not. A gate must be robust to the nuance of the specific
hypothesis/data/strategy, or it is measuring the threshold, not the signal. *Priority: high.*

### 5.4 Gates that are too strict for an effect's shape need an a-priori escape hatch

Beyond magic numbers, the deeper issue (§2.3) is that a guard built for one effect *shape*
(location) can be **structurally blind** to another (tail/bimodal) and veto a real finding. The
EXP-074 audit *did* catch this (W2; an Assumption-Validation row states the consistency guard
"DOES NOT HOLD for tail-shape effects"), so it is not an undetected failure. The disciplined
resolution the programme already used — let the verdict stand, do **not** retro-edit the guard,
re-pose the question a priori in a new design (EXP-074→075) — is correct but *expensive*
(a whole extra experiment). The process change: when a scope's hypothesis admits a
known non-location effect shape (tails, bimodality, asymmetry), **predeclare the shape-aware
read alongside the standard guard at D0**, so a shape effect is caught in-experiment rather than
forcing a follow-up. Build the escape hatch before the guard fires, not after.

## 6. Where to focus next (recommendations, operator-decided)

1. **Select the next family for its *exit/capture geometry*, not its entry signal.** Both
   closed families had real entries; both died downstream. The highest-leverage unknown is the
   peak→realizable-net-capture conversion. Prefer mechanisms with structurally asymmetric,
   bounded-downside geometry where a deterministic exit can express the edge.
2. **Add a pre-TEST separability gate to the standard scope** (§4.1): demonstrate that the
   binding net-mean leg and the favourable signal do not share one unfilterable driver, before
   spending any counted read. This directly targets the failure mode that killed both families.
3. **Treat substrate as a primary design axis,** with its own matched-random null on the same
   substrate that defines the outcome geometry (the harami's MA-vs-ZigZag lesson; a baseline
   that changes the move definition needs its own control).
4. **Reuse the validated stack wholesale.** Data layer, EXP-020-analog readiness,
   EXP-027/070-analog event-level calibration, the frozen two-referee suite, cTrader parity,
   the TEST-read ledger, the file drawer — all proven across 16 phases. The new family inherits
   process, not signal.
5. **Keep running the cheapest decisive TRAIN-only gross diagnostic first** (011→012→013
   pattern). Most of the highest-information findings in both families came from a few seconds
   of gross compute with a frozen floor and a per-cell null — long before any net machinery.
6. **The harami family is reopenable only by a genuinely new lever** off the exhausted
   registered surface (a different conditioning object, a non-entry mechanism for the
   bimodality, or a new substrate) under its own scope/D0/G0 — a deliberately high bar.

---

## 7. Source map

| Theme | Primary sources |
| --- | --- |
| Pooled-verdict masking / per-stratum requirement | Phase 016 L1; EXP-074/075; Phase 007 equal-weight veto; EXP-008 pooled-vs-per-instrument MDE |
| Gate over-strictness / wrong-shape guard | EXP-074 consistency-gate veto; D0-amendment-005/006/007 |
| Magic-number vs calibrated thresholds | EXP-075 audit ("the 0.15… not a calibrated value"); EXP-047 (k=1.0 inert); Phase 009 m_cell margin; Phase 013 L2 fixture-bite check |
| Audit why-diagnosis & rerun present but **operator-triggered, not autonomous** | EXP-074 audit ("the operator's caution is well-founded and is the headline"); A1 operator-driven adversarial review forced EXP-013/014/015 rerun; EXP-075 materiality assessment |
| Framework / referee hardening | Phases 001–003b retrospectives; amendment A1; INDEX retrospective table rows 62–65 |
| cTrader / new-universe infra | INFR-001, INFR-002 / VAL-002 / VAL-003 |
| AVWAP closure & capture-geometry diagnosis | Phase 013 retrospective §§3–5; Phase 008/009/011 retrospectives |
| Conditioning-gap / unconditioned-null category error | `014-A-conditioning-gap-and-validation-lessons.md` (8 lessons) |
| Substrate as signal lever | EXP-060B (SUBSTRATE_LEAD_FOUND); Phase 014 G2; Phase 015 retrospective |
| Dual-object correction; goalpost discipline | D0-amendment-001/002; Phase 015 retrospective §4 |
| Entry bimodality / median-not-candidate | Phase 016 retrospective L1–L4; EXP-071/074/075; D0-amendment-003–007 |

*Reflective document. Mechanical verdicts, per-experiment cards, and gate records live in the
cited checkpoints and family indexes; this file synthesises their lessons and adds no new
measurement.*
