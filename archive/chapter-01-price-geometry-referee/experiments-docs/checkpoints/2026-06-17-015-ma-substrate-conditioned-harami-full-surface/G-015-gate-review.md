# G-015 Gate Review — Phase 015 MA-Substrate Conditioned-Harami Full-Surface Adjudication

**Date:** 2026-06-18
**Gate:** G-015 — single, terminal gate for Phase 015 (no intermediate gates;
`design.md` §7, `D0-predeclarations.md` P9). Applied **after the full dual-object slate**
(EXP-061–066 + the native combined champion EXP-068; EXP-067 dropped per
`D0-amendment-002-drop-exp067.md`).
**Adjudicated by:** desk review (research-pipeline governance); routing **operator-ratified
2026-06-18** ("PROCEED_TO_SCREEN; register both native arms").
**Family:** `CF-HA-HARAMI-001` (REGISTERED, OPEN → first candidate slot consumed here).
**Binding endpoint (P3/P14):** median per-event gross ATR-normalised expectancy, CI_low > 0,
≥ 30 events. **Mean co-primary (P4):** raw mean CI_low > 0, with trimmed-mean / worst-5%
tail-share diagnostics. **Attribution (P5):** beats same-object matched-random (`RM-native` /
`RM-hybrid`), contrast CI_low > 0. **Composition (P6):** P11 (≥ 5 cells / ≥ 3 instruments) with
≥ 3 qualifying cells outside the 4h domain. Objects judged individually, never pooled.

---

## Verdict

```text
G-015 STATUS: PROCEED_TO_SCREEN  (native object) ; CHARACTERISED_NOT_VIABLE (hybrid object)
PHASE OUTCOME: PROCEED_TO_SCREEN — the strongest object governs (design §7).
  • NATIVE  (EXP-068) .... PROCEED_TO_SCREEN — both predeclared champion arms compose the
                          full G-015 conjunction (median ∧ raw-mean ∧ beats-RM-native) at P11+P6.
  • HYBRID  (EXP-061–066). CHARACTERISED_NOT_VIABLE on the disclosed surface (EVIDENCE_AGAINST
                          dominant; INCONCLUSIVE at S2; no per-layer winner to combine).
                          EXP-067 dropped (Amendment 002); inferential disposition, not a
                          dedicated measurement.
  • SUBSTRATE/METHOD_DEFECT  NOT met (99/99 reconciliation @1e-9; determinism / causality /
                          invariants all pass on both objects).
  • INCONCLUSIVE ......... NOT met for native (fully powered, 99/99); recorded for the hybrid
                          S2 layer only (power-limited), immaterial to the phase outcome.
ROUTING (operator-ratified 2026-06-18): register the MA-SUBSTRATE / native candidate branch
  (BOTH champion arms — `N-PARTIAL-V2A` and `N-V2A×ADV-NONE`), tagged conditioning-object = native.
  FIRST CANDIDATE SLOT CONSUMED. Next: EXP-027-analog event-level method calibration (TRAIN-only),
  then a one-shot TEST confirmation of the non-4h FX core.
CANDIDATE SLOTS SPENT: 1 (first) AT THIS GATE   TEST READS SPENT: 0   HOLDOUTS: sealed (unchanged)
```

This is a clean instance of the design §7 `PROCEED_TO_SCREEN` outcome on the **native** object:
the predeclared mechanical conjunction is satisfied by both champion arms. The phase outcome is the
strongest object's outcome (§7), so the hybrid object's `CHARACTERISED_NOT_VIABLE` disposition does
**not** gate the phase — the two objects are judged individually and never pooled.

## Basis — the full dual-object surface (gross, 0 TEST)

The single terminal gate is adjudicated on the complete slate, not on any one geometry (the
no-early-closure guard, §5/P9). Every L1–S3 read emitted both objects with its own matched-random
null; the combined champion was measured on native (EXP-068), and the hybrid combined champion was
dropped after the individual surface returned no positive lever to combine (Amendment 002).

### Native object (binding for PROCEED)

| Lever | EXP | Native mechanical result |
| --- | --- | --- |
| Capture readiness + benchmark efficacy (L1) | EXP-061 `M0` | **EVIDENCE_FOR** — 8 cells / 6 instruments, all non-4h; reconciles EXP-060B 99/99 @1e-9. |
| Lifetime availability (L2) | EXP-062 | **AVAILABILITY_GOOD** — 91/99 MOVE_AVAILABLE, but only 4/99 signal-attributable (room is a generic MA-segment property). |
| Adverse geometry + mean (L3) | EXP-063 | **EVIDENCE_FOR (nuanced)** — V-BENCH generalises (8 cells), mean_viable composes (10 cells), but `recovery_positive=0` (formal bounded-vs-NONE contrast never crosses zero). |
| Favourable-target (S1) | EXP-064 | **EVIDENCE_AGAINST** — 0/7 variants compose; benchmark 50% wins (replicates EXP-056). |
| Third-barrier (S2) | EXP-065 | **EVIDENCE_AGAINST** — 0/4 variants compose; benchmark adaptive cap wins (replicates EXP-058). |
| Position-management exits (S3) | EXP-066 | **EVIDENCE_FOR** — `N-PARTIAL-V2A` clears P11 (21 cells / 13 instruments), also raw-mean-positive in 11 cells. |
| **Combined champion (S4/native)** | **EXP-068** | **PROCEED_TO_SCREEN-candidate** — both champion arms compose the full G-015 conjunction (below). |

**EXP-068 conjunction (per cell: median CI_low>0 ∧ raw-mean CI_low>0 ∧ (arm−`RM-native`) CI_low>0;
composed at P11+P6):**

| Arm | g015 cells | instruments | non-4h | P4 closure | Read |
| --- | --- | --- | --- | --- | --- |
| `N-PARTIAL-V2A` (S3 winner; PARTIAL-V2A + 1:1 stop) | 9 | 5 | **7** | **PARTIAL_RECOVERY** (1 structural, 0 tail-driven) | clean, bounded-downside |
| `N-V2A×ADV-NONE` (EXP-060B champion geom + partial scaling; `adv_count=0`) | 14 | 9 | **6** | **TAIL_DRIVEN** (63/99; 8/14 composing cells 4h) | broader but tail-driven |
| `BENCH` (single-leg 0.50·M_sofar / 1:1 / MA cap) — *disclosed* | 6 | 4 | 6 | — | signal present without partial/ADV-NONE machinery |

Both champion arms clear P11 (≥5 cells / ≥3 instruments) **and** the P6 non-4h rule (≥3 cells
outside 4h). The mean-positive, RM-beating edge is present even at the **single-leg BENCH** (6
non-4h FX cells), so it is not an artifact of the partial-exit / ADV-NONE machinery — those broaden
it. The geometry-independent robust core is ~5 non-4h FX cells (GBPUSD / NZDUSD / GBPJPY, 4 of which
also pass at BENCH). No DE30-truncated cell appears in any G-015-passing set.

### Hybrid object (disclosed; CHARACTERISED_NOT_VIABLE, never pooled)

| Lever | EXP | Hybrid result |
| --- | --- | --- |
| L1 benchmark efficacy | EXP-061 `H0` | EVIDENCE_AGAINST (1 cell, NZDUSD-5m; powered grid ⇒ genuine negative) |
| L2 availability | EXP-062 | only 4/99 signal-attributable (generic MA-segment property) |
| S1 favourable | EXP-064 | EVIDENCE_AGAINST (0/7 variants; max 3 wins) |
| S2 third-barrier | EXP-065 | INCONCLUSIVE_POWER_LIMITED (max 4 powered cells < quorum) |
| S3 exits | EXP-066 | EVIDENCE_AGAINST (0 arms compose) |
| S4 combined champion | ~~EXP-067~~ | **DROPPED (Amendment 002)** — no per-layer winner to combine; adjudicated here on the disclosed surface |

The hybrid object is **EVIDENCE_AGAINST across the entire individual surface**, INCONCLUSIVE only at
the power-limited S2 layer. A combined champion can only assemble per-layer winners and the hybrid
object has none that compose; the levers are additive-not-synergistic (EXP-060). The disclosed-surface
disposition is `CHARACTERISED_NOT_VIABLE` for the hybrid object — a documented **inference** (Amendment
002 §4 caveat: the hybrid combined-champion efficacy is, strictly, unmeasured), not a dedicated
measurement. It does not affect the phase outcome (native governs) and the family is not closed.

## Why each §7 outcome does / does not apply

1. **PROCEED_TO_SCREEN requires** ≥ 1 combined definition — on either object, judged individually —
   that is median-viable AND raw-mean-positive (CI_low > 0), beats its same-object matched null, and
   clears P11 with non-4h breadth. The native object satisfies this with **two** champion arms.
   **Met (native).** Honoring the predeclared mechanical criterion is binding: denying PROCEED while
   the conjunction composes would be exactly the post-result goalpost-move the programme's
   no-reselection discipline forbids. The caveats (§ below) are routed into the *screening scope's
   definition*, not into the gate verdict.
2. **CHARACTERISED_NOT_VIABLE requires** the negative mean shown **structural and
   geometry-irrecoverable on both objects** (P4 closure-on-mean rule). On the native object the mean
   is **not structural** — `N-PARTIAL-V2A` is PARTIAL_RECOVERY (1 structural / 0 tail-driven). The
   closure rule is therefore **not** satisfied for the family; CHARACTERISED_NOT_VIABLE applies only
   to the hybrid object in isolation, which does not govern. **Not met (family).**
3. **MEAN_RECOVERABLE — FOLLOW-UP** would apply if the mean were tail-driven / partially recovered
   but **not yet cleanly mean-positive at composition**. Here the raw-mean co-primary **does** compose
   at CI_low > 0 (P11+P6) on both champion arms — the mechanical bar for PROCEED is met, so the
   weaker MEAN_RECOVERABLE routing does not fit the facts. (The narrowness of the mean breadth is a
   real caveat — see below — but it is a *screening-scope* concern, not grounds to down-route a
   composing conjunction.) **Not met.**
4. **SUBSTRATE/METHOD_DEFECT** would fire on determinism / causality / invariant / reconciliation
   failure. EXP-068 reconciles 99/99 to EXP-061 M0/H0 and EXP-066 native PARTIAL-V2A @1e-9;
   determinism second pass, causality (native `/STRONG-STAT` references only confirmed prior MA
   segments), and the ADV-NONE zero-stopout invariant (`adv_count=0`) all pass. **Not met.**
5. **INCONCLUSIVE** would fire on coverage / power failure on a conditioned population. The native
   slate is fully powered (99/99). Recorded for the hybrid S2 layer only; immaterial to the outcome.
   **Not met (native).**

## Caveats carried into the screening scope (binding context, not gate blockers)

The PROCEED verdict is correct on the predeclared criterion, but the edge is **genuine and narrow**.
The screening scope inherits these as binding context:

- **Thin mean breadth.** Mean-positive composes in 11–14 / 99 cells vs median-viable 45–89. The
  family's broad strength is the median; the mean co-primary — the most cost-sensitive endpoint — is
  thin. (Disclosed post-hoc: winsorized-mean-positive is far broader, 46–73 cells, confirming the raw
  mean is tail-suppressed.)
- **`N-V2A×ADV-NONE` is TAIL_DRIVEN and 4h-concentrated** (8/14 composing cells are 4h; only 6
  non-4h). It buys mean-positive cells by accepting fat negative tails. **`N-PARTIAL-V2A` is the
  cleaner, bounded-downside definition** (PARTIAL_RECOVERY, 7 non-4h). Both are registered per the
  operator's "both arms" ruling; the screening scope should treat `N-PARTIAL-V2A` as the lead
  definition and `N-V2A×ADV-NONE` as the disclosed broad-but-tail-driven companion.
- **Gross / TRAIN-only.** A thin mean edge is unverified out-of-sample by design; the first counted
  TEST read is the decisive confirmation, not a formality.
- **The defensible signal is a ~5-cell non-4h FX core** (GBPUSD / NZDUSD / GBPJPY, ± EURUSD), present
  even at single-leg BENCH. This is the screening target, not the full 99-cell grid.
- **TEST-stratum eligibility (flag for the screening scope, not a G-015 input).** EURUSD is
  TEST-capped instrument-wide (holdout-contaminated, EXP-032); EURUSD-15m/30m appear in the native
  BENCH/PARTIAL sets but are **ineligible for stratum-specific TEST confirmation**. The load-bearing
  FX core (GBPUSD / NZDUSD / GBPJPY) strata are all open (0 counted reads). The 5m/15m/30m strata are
  not yet materialized in `test-read-ledger.md` (Phase 014 new domains) — the screening scope must
  materialize them before any binding read. **No TEST read is spent at G-015.**

## On the post-hoc winsorized-mean diagnostic (gate-level question raised by EXP-068)

The EXP-068 results.md records a **non-predeclared, post-hoc** 10% winsorized-mean diagnostic and
explicitly defers its interpretation to this gate ("a gate-level adjudication question, not an EXP-068
conclusion"). The finding: the winsorized mean is positive in **46 / 57 / 73** cells (BENCH /
N-PARTIAL-V2A / N-V2A×ADV-NONE) versus **10 / 11 / 14** for the raw mean — a ~4–5× shift,
concentrated in the same cells already passing median viability and beats-RM. The gate resolves it
as follows:

1. **The raw mean remains the binding co-primary; the winsorized mean does not enter the verdict.**
   P4 predeclares the raw-mean bootstrap CI as the mean co-primary and the 10% **trimmed** mean +
   worst-5% tail-share as the *diagnostics*. The winsorized mean was added after the run. Substituting
   it — or any tail-robust estimator — for the raw-mean test to broaden the PROCEED basis would be
   precisely the post-result metric redefinition the programme forbids (P8 / no-reselection). PROCEED
   stands on the **raw-mean** conjunction (11 / 14 composing cells), exactly as predeclared. The
   winsorized read changes **no** binding count, G-015 flag, or candidate registration.
2. **What it legitimately establishes: the mean is not structural.** This is a diagnostic in the
   service of the P4 closure-on-mean rule, which asks whether a median-viable / raw-mean-negative
   result is *structural* (→ close) or *removable-tail-driven* (→ not close). The winsorized result
   corroborates the P4 `PARTIAL_RECOVERY` / `TAIL_DRIVEN` classification from an independent angle: in
   the majority of cells the central tendency (median **and** winsorized mean) is positive while the
   raw mean is dragged negative by a fat worst-5% tail. That is the positive demonstration that the
   negativity is **not** geometry-irrecoverable — which is what licenses keeping the family OPEN and
   routing to PROCEED rather than CHARACTERISED_NOT_VIABLE. It strengthens the verdict's *direction*;
   it does not widen its *basis*.
3. **It sharpens the screening-scope guidance, it does not change the gate.** Because the raw-mean
   co-primary is effectively acting as a **tail-sensitivity filter** (passing benign-tail cells,
   failing median-and-winsorized-positive cells with fat tails), the bounded-downside `N-PARTIAL-V2A`
   — which truncates the tail at source — is confirmed as the correct lead candidate definition, and a
   targeted **tail-filter / capped-downside** treatment of the `N-V2A×ADV-NONE` TAIL_DRIVEN cells is
   the concrete **MEAN_RECOVERABLE follow-up lever** named in the routing. Whether a tail-robust mean
   is a more informative *predeclared* endpoint for the family is a question for the **screening
   scope's D0**, not a retroactive edit to this gate.

**Net:** the winsorized diagnostic is decision-relevant and is recorded here as such — it underwrites
"mean not structural" — but it is held strictly to its diagnostic role; the binding PROCEED test is
the predeclared raw mean, unchanged.

## Net adjudication

**Phase 015 is PROCEED_TO_SCREEN on the MA-native conditioned harami.** The MA-substrate edge that
EXP-060B found at a single geometry generalises into a robust, signal-attributable, **mean-positive**
candidate across the full surface — the first Phase 015 native read where the mean co-primary
composes — and it does so only when `/STRONG-STAT` is computed on the same MA segment that defines the
outcome geometry (the hybrid object, which conditions on the ZigZag move, is EVIDENCE_AGAINST across
the surface). The Phase 015 mean question is answered for the native object: the MA mean ≈ 0 is **not
structural** and is recoverable in a bounded-downside subset. The edge is genuine but narrow; the
screening scope confirms the non-4h FX core under the bounded-downside `N-PARTIAL-V2A` definition.

## Consequences

| Item | State |
| --- | --- |
| PROCEED_TO_SCREEN | **TRIGGERED (native).** `CF-HA-HARAMI-001/MA-SUBSTRATE` native candidate branch registered — **both** arms (`N-PARTIAL-V2A`, `N-V2A×ADV-NONE`), conditioning-object = native. |
| Candidate slots | **1 (first) consumed at this gate.** Recorded in `multiplicity-registry.md` (Phase 015 batch) and `candidate-families/harami.md`. |
| Family `CF-HA-HARAMI-001` | **REGISTERED / OPEN — first candidate active.** Hybrid object measured-negative and retained; native object promoted. |
| TEST reads | **0 spent.** `test-read-ledger.md` unchanged; holdouts sealed; no new-universe row read under the HA-harami event definition. The first counted TEST read occurs at the screening scope's confirmation, not here. |
| Hybrid object | `CHARACTERISED_NOT_VIABLE` on the disclosed surface (inferential; EXP-067 dropped, retained in ledger, never reused). Reinstatable as its own scope only if a future gate judges the inference insufficient. |
| Registered branches measured in Phase 015 | `/MA-SUBSTRATE` (+ `hybrid`/`native` modes), `/VPTARGET`, `/MAGTARGET`, `/THIRD-TIME`, `/THIRD-EVENT`, `/EXIT-PARTIAL`, `/EXIT-TRAIL-STRUCT`, `/ADV-EXTREME-rr1`, `/ADV-NONE` (disclosed reference) — dispositions in `multiplicity-registry.md` and `candidate-families/harami.md`. Negative/inconclusive items retained in the file drawer. |
| Phase 015 checkpoint | **CLOSES at G-015** with this adjudication; retrospective written (`retrospective.md`, this directory). |

## Routing (operator-ratified 2026-06-18 — "PROCEED_TO_SCREEN; register both native arms")

The MA-native candidate branch advances to candidate screening under the established pipeline
(`candidate-families/harami.md` §Implementation Path):

1. **Event-level method calibration (EXP-027-analog), TRAIN-only.** Calibrate the event-level
   evaluation method (FPR control, finite MDE, determinism) on the MA-native conditioned population
   before any TEST contact — mirrors EXP-027 for AVWAP.
2. **One-shot TEST confirmation of the non-4h FX core**, under the bounded-downside `N-PARTIAL-V2A`
   lead definition (with `N-V2A×ADV-NONE` disclosed). Materialize the 5m/15m/30m FX-core strata in
   `test-read-ledger.md` first; honor the 2-lifetime-counted-reads cap; EURUSD ineligible
   (TEST-capped instrument-wide).
3. **Cost-aware / tail-filter follow-up (if warranted).** Re-read the mean co-primary on the FX core
   under costs; a targeted capped-downside / tail-filter for the `N-V2A×ADV-NONE` TAIL_DRIVEN cells is
   the MEAN_RECOVERABLE lever, opened only if the bounded-downside confirmation survives.

Direction-setting detail belongs to the screening scope's own design and D0, not to this gate. No
TEST or holdout contact occurs until the screening scope predeclares it.

---

*Companion documents: per-experiment cards in `../../families/cf-ha-harami-001/INDEX.md`; the Phase
015 synthesis and process lessons in `retrospective.md` (this directory); the dual-object design
correction in `D0-amendment-001-dual-parallel-substrate.md`; the EXP-067 drop in
`D0-amendment-002-drop-exp067.md`. The native PROCEED-candidate measurement is `python/experiments/EXP-068/`.*
