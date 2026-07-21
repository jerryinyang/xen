# Checkpoint 015 — Signed Value Where Price Is Blind: the Absorption Screen (design)

**Opened:** 2026-07-21 · **Status:** **DESIGN SIGNED — D1–D6 approved; INFR-020 apparatus
FROZEN 2026-07-22** (§Operator decisions; rollover DEFERRED INDEFINITELY). Execution proceeds
item-by-item under the §3/§4 gates: SPDR-009 enters developer implementation next. No status
transitions (retrospective acts only).
**Container for:** SPDR-009 (S9 signed-absorption marginal-value screen — **master go/no-go**),
SPDR-010 (S14 CVD-divergence screen — rides along, memo-gated), INFR-019 (tick-floored per-symbol
spread reconstruction — parallel, non-blocking), plus a cheap analysis follow-up (trimmed/median
re-read of the SPDR-008 unsigned bounce).
**Family:** CF-SIGAUC-001 — `docs/signal-registry/candidate-families/cf-sigauc-001.md` (**REGISTERED**,
carried from ckpt-014; kept at the ckpt-014 retrospective, no transition).
**Source methodology:** base doc `.ignore/what-next/orderflow/ohlc/SIGNAL-SIGNED.md` **as amended by
`../2026-07-20-014-signed-auction-structure/signed_bar_framework_addendum_v1_1.md` (Addendum v1.1,
which GOVERNS where it conflicts)**. This checkpoint implements the addendum's Part 3 (the revised
experimental path, superseding Appendix B Phase 6 onward). Signal definitions stay normative to the
source; the addendum reframes grades, protocol, and sequence.
**Lane:** SPDR (TRAIN-only screens) → XENA (deferred, only if soil is found).

## Why this checkpoint exists (one paragraph)

Checkpoint-014 killed the two cheapest, most price-adjacent arms of the family: the price-only session
spine (P-01, no conditional skill, dies after cost) and the S3 signed trap-load refinement (a **powered
null** on three boundaries). What both share is that they ride on **price-visible geometry**. The
family's actual thesis — the whole reason exact taker delta was worth building — is that signed value
pays **where price is blind**: heavy aggression that produces no price result (absorption), and
cumulative delta that decouples from price (divergence). Neither was tested. This checkpoint runs the
**single cheapest test of that flagship claim** and lets it decide the family's fate: soil ⇒ the depth
spend is justified; a third independent powered null ⇒ close the family on the session horizon with its
audited stack and its characterisations intact (§7).

## Preconditions (verified on disk — carried from ckpt-014)

| Item | State |
|---|---|
| Checkpoint-014 | **CLOSED 2026-07-21** (operator-directed retrospective); Phases 0–5 complete; family KEPT REGISTERED |
| Instrument registry | **FROZEN** `pin_sha256 5c386984…` — anchor A-USOPEN·L=15, A6 D4-t50-w30·δ=0, kernel K-UNIFORM, class residual thresholds. **S1 is now an operational anchor only** (Addendum §2.7), never an edge-bearing gate |
| A5 seasonal baselines | **FROZEN** `1b7244c8…` (194 instruments, DESIGN-bank fit) — the residual normaliser for absorption reads |
| Signed-bar lane | `SignedBar` + `data/catalog_sigbar/` — Δ engine-readable, round-trip + causality asserted |
| Spread | **`SpreadBps` UNUSABLE** (Addendum §2.5 / §1.2) — §2.5 spread layer suspended; no net breadth claim admissible until INFR-019 (§3) rebuilds it |
| Holdout | SEALED (≥ 2025-01-08); TEST band reserved; **no TEST contact anywhere in this checkpoint** |
| CAL / XENA pin | sparse-session CAL **not built** — a ckpt-015 depth prerequisite *only if soil is found*, not a screen blocker |

## Objectives

1. Run the **S9 absorption marginal-value screen** (framework-falsifier #3) — the master go/no-go for
   the signed thesis — under the addendum's hardened protocol (§4).
2. Run the **S14 divergence screen** (framework-falsifier #4) as a memo-gated rider, so the signed
   mechanism family dies cleanly if both null, rather than being endlessly reformulable.
3. Stand up the **tick-floored spread reconstruction** (INFR-019) so that any surviving edge can be
   read net — in parallel, blocking nothing at the screen stage.
4. Resolve the family at the ckpt-015 retrospective: **soil ⇒ depth spend authorised; third powered
   null ⇒ close on the session horizon** (§7), with the horizon-menu scoping clause (§4 rule 10) applied.

---

## §1 Phase mapping — Addendum v1.1 Part 3 → Xen items

| Addendum phase | Nature | Xen item | In this checkpoint |
|---|---|---|---|
| **6′** — S9 absorption marginal value (falsifier #3) | hypothesis — **master go/no-go** | **SPDR-009** | ✅ |
| **6′b** — S14 CVD divergence (falsifier #4), memo-gated | hypothesis | **SPDR-010** | ✅ (rides along) |
| §3.4 — tick-floored spread reconstruction | data engineering | **INFR-019** | ✅ (parallel, non-blocking) |
| §3.4 — trimmed/median re-read of the unsigned bounce | analysis follow-up | folded into SPDR-009 analysis or a light VAL-style re-read of SPDR-008 | ✅ (cheap) |
| Depth remainder — S10/S11/S13/S16, S15 last; M3/M5 first, M2 router vs outcomes | hypothesis | XENA universe(s) | ⛔ **only if §7 finds soil** — ckpt-016+ |
| Horizon menu — micro / structural / funding-cadence | screening | future SPDR screens | ⛔ required before a *whole-family* close (§4 rule 10), not before the S9 screen |

**Boundary rationale (Addendum §3.5).** The order preserves the property that made Phases 0–5 cost four
items and zero reads: *the cheapest test of the largest remaining claim goes first.* S9 is the purest
available statement of "exact delta pays where price is blind." One screen carries the family honestly.

## §2 The master question + mechanism (SPDR-009)

**Falsifiable question (framework-falsifier #3):** on identical location-qualified events, does the
**signed** absorption signature (S9) add marginal reversal/continuation information **over the unsigned
Climax-hold class** — measured as *signed minus unsigned on the same events*, not "the signed version
fires"?

**Mechanism (source S9, normative):** heavy measured aggression that produces **no price result at a
level** (effort without result) marks the aggressor as absorbed at a defended shelf; the level then
holds and resolves away from the absorbed side. This is definitionally **invisible to price alone** —
a price-derived sign estimator goes flat exactly where price does. That is the distinction from the
deleted S3 arm (a Δ tag on a *visible* failed break).

**Design commitments (from Addendum §3.1, binding on the SPDR-009 experiment design):**
- **Gate-free, location-qualified.** Events qualify by *location context only* — balance edges,
  prior-value edges, defended bands (S13 detection), completed-profile HVN edges — **never** the
  demoted S1 session gate. This is both the honest design and the mechanism's predicted habitat.
- **Marginal framing (source Part 6.5).** The read is `signed-S9 − unsigned-class` on identical events.
  A bare "signed absorption reverts" is not a result.
- **Money floor first** (as SPDR-007) — but note the net term is spread-blind until INFR-019; the screen
  is a **gross/marginal availability read**, disposition-only, never a tradability claim (SPDR law).

The exact S9 operationalisation (absorption threshold on Δ-vs-result residual, hold, level construction)
is pinned in the **SPDR-009 experiment design.md** via quant-designer, normative to source + addendum;
this checkpoint fixes scope and protocol, not signal content.

## §3 Planned experiment sequence

| Seq | ID | What | Gate to start | Depends on |
|---|---|---|---|---|
| 1 | **SPDR-009** | **S9 absorption marginal-value screen (Phase 6′)** — master go/no-go | own design.md → QA APPROVE → operator execution approval | frozen registry `5c386984…` + baselines `1b7244c8…` |
| 2 | **SPDR-010** | **S14 CVD-divergence screen (Phase 6′b)** — rider | SPDR-009 disposition recorded **+ mechanism-differentiation memo written before the run** (§4 rule below) | 1 (shares the signed lane) |
| — | **INFR-019** | Tick-floored per-symbol spread reconstruction | own design.md → QA → approval | signed-lane data; **runs in parallel, gates nothing at screen stage** |
| — | analysis | Trimmed/median re-read of the SPDR-008 unsigned bounce | light analyst pass | SPDR-008 emissions |

**Sequencing note.** SPDR-009 is the master item and runs first. SPDR-010 may only run once the
**S14 mechanism-differentiation memo** exists (one paragraph, written *before* the run: why integration
across bars, location anchoring at held levels, and multi-bar structure create information that
bar-level trap load did not). The memo is a hard precondition — running S14 without it is "S3-null
laundering through a new name" (Addendum §3.2). INFR-019 is orthogonal and may proceed anytime.

## §4 Protocol hardening carried in (Addendum v1.1 Part 2 — binding on every item)

Each is a binding design constraint, not a suggestion. QA checks conformance clause-by-clause.

1. **§2.1 Master-gate conjunction** — a promote requires **all three**: calibrates AND beats a matched
   unconditional control AND clears the measured cost floor. Reproduction alone never passes.
2. **§2.2 Mirror-tail multiplicity** — count both tails; the positive tail must **materially exceed its
   anti-monotone mirror**, not merely exceed null expectation. Single-tail "≥k winners" is retired.
3. **§2.3 Per-symbol census** — every pooled effect co-reports its reproduces/drifted/broken census;
   claims inherit the census, not the pool.
4. **§2.4 Control-family declaration** — each event class declares its control up front: matched
   random-timing (availability), matched unconditional (conditioning skill; cross-session if
   within-session infeasible — say so), derangement (sign/side). **Sparse-session events need blocks
   wider than the calendar day** or a different null. Unpowered ≠ negative and is reported as unpowered.
5. **§2.5 Finite-value guards** — every correlation/regression guards `is_finite` explicitly (the
   SPDR-007 NaN-through-`drop_nulls` sign-flip is a known live bug class).
6. **§2.6 Robust excursion stats** — every excursion effect co-reports median + trimmed; a mean-only
   excursion claim is an upper bound, labelled as such.
7. **§2.7 Anchor vocabulary** — S1 is an **operational anchor** only; no read may treat it as
   edge-bearing.
8. **§2.8 Leak-tripwire interpretation** — NO_MATERIAL_EDGE on a null means "teeth, nothing to bite";
   it is **not** evidence a live edge is leak-free.
9. **§2.9 Breadth honesty + net prerequisite** — "full cross-section" = listings with readable history
   (survivorship note binding); **no net (post-cost) breadth claim is admissible until INFR-019 exists.**
10. **§2.10 Horizon-menu closure** — a whole-family close needs either ≥1 screen per untested horizon
    (micro; structural; funding-cadence) or an explicit "close applies to the session horizon only"
    scoping statement. This checkpoint's kills/closes are session-horizon-scoped.

**Also carried (ckpt-014 KB):** destroys are derangements (L-28); fill-ts = decision-bar close, anchor
check mandatory (L-29); `dispose_on_completion=False` (L-30); one BacktestNode per process (L-31);
value/quality reads are report layers, not gates (L-32/INFR-016); block ≥ H on overlapping windows;
per-bar Δ exact, **per-level Δ barred** (card ban 2); no local accounting primitives; mechanisms binary
(a refuted mechanism is deleted, not re-tuned — card ban 8, and §1.3 already deleted S3 Δ+).

## §5 Holdout mapping (unchanged from ckpt-014 §5 D3)

Same TRAIN-internal bank split, code-asserted; **no redesign**.

| Band | Range | Use |
|---|---|---|
| DESIGN bank | `2021-06-29 → 2023-03-01` | all screen fitting/estimation |
| CONFIRM bank | `2023-03-01 → 2023-12-18` | one verify per screen; never used to re-select |
| TEST band | `2023-12-18 → 2025-01-08` | **reserved** — a counted XENA gate only if soil is found (ckpt-016+); untouched here |
| Global holdout | `≥ 2025-01-08` | **never queried** |

CONFIRM is TRAIN-INTERNAL, labelled as such; not programme out-of-sample. **0 counted TEST reads.**

## §6 Universe rules

| Item | Universe | Rationale |
|---|---|---|
| SPDR-009 / SPDR-010 | The signed-lane admitted set with readable TRAIN data — **296 breadth denominator / 194 A5-fitted** (survivorship caveat binding, §2.9) | Absorption is a located cross-sectional event; breadth is the tier's advantage |
| INFR-019 | All signed-lane symbols | Spread is per-instrument apparatus |

Point-in-time, delisted included, anti-survivorship binding project-wide. Every breadth read states the
296 denominator and carries the survivorship note (the covered set is older listings, not the live board).

## §7 Family closure rule (the decision this checkpoint forces)

Per Addendum §3.3, decided at the ckpt-015 retrospective, operator-signed:

- **Third independent powered null** — S9 marginal ≈ 0 under §2's design, powered (MDE small at the event
  n), no cluster surviving the mirror-tail rule ⇒ **close CF-SIGAUC-001 on the session horizon** (§4 rule
  10 scoping). Residual value retained: the audited stack (signed-bar lane, baselines, acceptance/trap
  modules, frozen registry) and the market-science characterisations (S2's object; S3's unsigned bounce,
  trimmed-confirmed or killed). Whether to *also* exercise the horizon menu before a whole-programme close
  is a separate operator call.
- **Soil found** — S9 (and/or S14) shows a powered, mirror-clean marginal signed edge ⇒ the sparse-session
  CAL spend is warranted, then the surviving depth remainder in revised order (Addendum §3.3): S10/S11
  marginal, S13 races, S16 boxes, **S15 strictly last**, then Phase-7 models with a live direction layer
  (**M3/M5 first**, M2 router vs outcomes). This routes to ckpt-016+, not this checkpoint.

S14's memo (§3) ensures that if both S9 and S14 null, the **signed mechanism family is cleanly dead**,
not reformulable.

---

## Success criteria (checkpoint level)

- SPDR-009 ends in an operator-signed disposition on the S9 marginal-value master gate, money floor
  computed first, under the §4 hardened protocol. A powered null is a clean outcome.
- SPDR-010 runs only with its mechanism-differentiation memo on the record; ends in an operator-signed
  disposition.
- INFR-019 ends with a tick-floored per-symbol spread pin (hash-pinned) or a recorded blocker — enabling
  future net reads; blocks nothing here.
- Every item: 0 counted TEST reads, holdout SEALED, per-stratum reads with pooled disclosure-only,
  mirror-tail promotes, per-symbol census, finite guards, robust excursion stats — report layers not gates.
- Family close/keep decided only at the ckpt-015 retrospective, operator-signed, with §7's rule and the
  §4 rule-10 horizon scoping applied.

## Constraints carried in

Holdout sealed · no TEST contact · registration already done (ckpt-014) · per-stratum reads, pooled
disclosure-only · no scope expansion after QA APPROVE · no auto-verdicts (report layers, INFR-016) ·
integrity gates hard (future-destroy, holdout, causal ≤t−1, estimand reconciliation) · SPDR never touches
TEST, spends no reads, registers nothing by itself · per-level Δ barred · mechanisms binary (S3 Δ+ already
deleted — no re-parameterisation) · Addendum v1.1 governs the base document · chapter-03 XENA pins remain
VOID on Bybit · **no net breadth claim until INFR-019** · S1 operational-anchor-only.

---

## Operator decisions — SIGNED 2026-07-21

| # | Question (plain) | Operator decision (2026-07-21) |
|---|---|---|
| **D1** | Open checkpoint-015 with this scope (S9 absorption screen as master, S14 rider, INFR-019 parallel)? | **APPROVED (a)** — Addendum Part-3 path is the active plan; SPDR-009 proceeds to its own design → QA |
| **D2** | Confirm the family closure rule: **third powered null (S9) closes the family** on the session horizon; **soil ⇒ depth spend**? | **APPROVED (a)** — S9 is the decisive read; §7 rule binds the ckpt-015 retrospective |
| **D3** | Require the S14 mechanism-differentiation memo *before* SPDR-010 runs (gate the rider)? | **APPROVED (a)** — S14 cannot launder the S3 null; both nulling kills the mechanism family cleanly |
| **D4** | Stand up INFR-019 (tick-floored spread) in parallel now, non-blocking? | **APPROVED (a)** — proceeds in parallel; no net breadth claim admissible until it lands |
| **D5** | Chapter-04 rollover — defer or roll now? | **DEFERRED INDEFINITELY** — not tied to the S9 screen; the operator will call it separately, not at this checkpoint boundary |

**SIGNED.** SPDR-009 enters Stage 1 (quant-designer) under this container as the next act.

---

## D6 — Multi-timeframe widening of SPDR-009 — SIGNED 2026-07-21

**Operator directive.** SPDR-009 must not test the S9 mechanism at one scale only. In addition to
the original **1d/1m** pair it tests **1h/5m, 4h/15m, 1d/1h**, all in a single run, with the pairs
compared internally under one frozen design. Sequencing route **A**: the 1d/1m execution approval
(granted, then held) is **suspended** until the multi-timeframe apparatus exists; nothing runs until
all four pairs can run together.

### D6.1 Rationale (operator's, recorded as given)

The 1d/1m pair is *"too large and too frequent to find trades and signals"*. That is a correct
reading of a real defect in the original scope, and it is confirmed by this design's own numbers:

- **Scale mismatch.** 1,440 detection bars sit inside one level-building session. The object that
  names the level and the object that detects the event are three orders of magnitude apart.
- **The cost floor does not shrink with the hold.** The ~11–13 bps round trip is ~85% exchange fee,
  which is hold-invariant. A 10-minute hold must clear it in 10 minutes; a 10-bar hold at 4h/15m
  has 2.5 hours to clear the *same* floor. The coarser pairs are strictly better on economics, and
  this is the strongest argument for the widening.
- **Event scarcity.** The measured 1d/1m census (SPDR-009 §6.3) yields 19 signal events across ten
  deep instruments, making INCONCLUSIVE the most likely outcome. Coarser detection changes the
  event population, not just its count.

### D6.2 The four pre-registered domain pairs

| pair | HTF — session + level construction | LTF — detection bar + hold unit | LTF bars/session | holds H=5/10 |
|---|---|---|---|---|
| **D1** | 1d (A-USOPEN, frozen) | 1m | 1440 | 5 / 10 min |
| **D2** | 1h (clock-aligned UTC) | 5m | 12 | 25 / 50 min |
| **D3** | 4h (00/04/08/12/16/20 UTC) | 15m | 16 | 75 / 150 min |
| **D4** | 1d (A-USOPEN, frozen) | 1h | 24 | 5 / 10 h |

All four are **pre-registered, not searched**. Multiplicity is 4 pairs × 2 event pools × 2 holds =
**16 primary cells**, declared up front and governed by the Addendum §2.2 mirror-tail rule.

### D6.3 The invariant that makes the pairs comparable (adopted from the operator's framing)

The operator's assumption — *"the engine would use the 1-minute bars regardless to simulate fills as
granular as possible"* — is **factually wrong for this lane** (SPDR is vectorised Python; there is
no engine and no fill simulation; Nautilus enters only at graduation). **The underlying principle is
nonetheless correct and is adopted as binding:**

> **HTF and LTF govern session framing and event detection ONLY. Every price-path and
> volume-at-price measurement stays on 1-minute bars in all four pairs.**

Consequences, each load-bearing:
- **Outcomes** (forward return, MFE/MAE) are measured minute by minute regardless of detection
  timeframe — no intrabar ambiguity, and the excursion is honest at every pair.
- **Volume profiles** (POC, value-area edges) are built from the **1-minute bars of the prior HTF
  session**, never from LTF bars. This keeps the frozen **K-UNIFORM** kernel inside the regime it
  was trade-truth-calibrated in, and preserves the full seven-kind level set at every pair. A
  profile built from 12–24 coarse bars would have been a different, unvalidated object.

### D6.4 Apparatus this requires (prerequisite, blocking)

Not a parameter change. A new INFR item must land first:

1. **Seasonal baselines per LTF timeframe.** `xen.sigbar.baselines` is hard-wired to a 1440×7
   minute-of-day grid and raises on anything else. Refit per instrument per timeframe
   (5m→288×7, 15m→96×7, 1h→24×7), frozen and hash-pinned as Stage-I apparatus.
2. **Class thresholds per (symbol, timeframe)** by the unchanged frozen p90/p10 rule.
3. **Session/anchor construction for 1h and 4h.** Clock-aligned UTC. **No anchor race is run** —
   these are asserted **operational anchors** (Addendum §2.7), their selection contrast is
   unmeasured, and no read may treat them as edge-bearing. The 4h grid coincides with Bybit funding
   timestamps (00/08/16 UTC), which source A7 names as a candidate anchor family — recorded as a
   property, not a claim.
4. **A generalised initial-balance rule.** The IB is **15 minutes of wall-clock in every pair**,
   expressed as the LTF bars covering it, minimum one bar: D1 = 15×1m, D2 = 3×5m, D3 = 1×15m,
   D4 = 1×1h. D1 reproduces the frozen 15-minute IB exactly. **D4 deviates**: its minimum bar is 60
   minutes, not 15 — disclosed, not smoothed.
5. **A re-picked contact-zone scale.** The zone is currently τ × IB width; at coarse pairs the IB is
   a single bar and that scale collapses. The zone scale becomes the **prior HTF session's range**,
   with τ re-picked per pair on **event counts only, never on outcomes**, and frozen before any
   read. D1's original `0.25 × ib_width` definition is retained as a pre-registered sensitivity so
   the QA-approved 1d/1m read is not lost.

### D6.5 The consequence the operator flagged — recorded as a live trigger

> *"If these domain pairs show better results than the 1d/1m pair, it might warrant a rerun of the
> previous checkpoint SPDR experiments."*

**Adopted.** SPDR-007 (price-only spine) and SPDR-008 (signed trap load) are both `NOT_WORTH`, and
**both were run exclusively on daily-anchored objects**. If a coarser pair carries signal where
1d/1m does not, those two nulls become **candidates for scale artifacts rather than absent
mechanisms**, and re-running them across the domain-pair grid is warranted. This is not a
speculative aside — it is exactly the **horizon-menu clause (Addendum §2.10 / ckpt-015 §4 rule 10)**,
which requires either one screen per untested horizon class or an explicit session-horizon-only
scoping before any whole-family close.

**Binding on the ckpt-015 §7 closure rule:** with D6 in force, a third powered null that is null
**across all four pairs** is a materially stronger close than the session-horizon-scoped one §7
contemplated. Conversely, **a null at 1d/1m alone can no longer close the family** — the widening
is precisely the test of whether that null was scale-bound.

| # | Question (plain) | Operator decision (2026-07-21) |
|---|---|---|
| **D6** | Widen SPDR-009 across four HTF/LTF domain pairs, building the apparatus first and running all pairs at once (route A)? | **APPROVED (A)** — all four pairs run together under one frozen design; 1d/1m execution approval suspended until the apparatus lands; SPDR-007/008 re-run trigger recorded per D6.5 |

**D6 prerequisite COMPLETE (operator freeze, 2026-07-22).** INFR-020 QA Run 10 APPROVE;
operator accepted pin manifest `5f170b71…`. SPDR-009's four-pair design now carries the exact
consumer hashes. Next: developer implementation → fresh-context design-to-code QA → operator
execution gate.
