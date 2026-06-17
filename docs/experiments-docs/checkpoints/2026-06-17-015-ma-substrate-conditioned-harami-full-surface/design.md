# Phase 015 — MA(20,50)-Substrate Conditioned Harami: Full-Surface Characterisation

**Status:** **ACTIVE — G0 PASS 2026-06-17 (operator).** D0 predeclarations ratified
(`D0-predeclarations.md`, P1–P12; Q1–Q6 + hybrid/native scope ruled). Pipeline entry point:
register the Phase 015 batch, then scope EXP-061 (Stage 1). All work gross, 0 candidate slots,
0 TEST reads, holdouts sealed; no data contact before each experiment's own pipeline pass.
**Date:** 2026-06-17.
**Family:** `CF-HA-HARAMI-001` (REGISTERED, OPEN). Continuation phase — *not* a new family.
**Opened by:** Phase 014 G2 routing (`../2026-06-14-014-ha-harami-substrate-and-capture/G2-gate-review.md`,
operator "Open MA-substrate follow-up"); Phase 014 `retrospective.md` §5; operator scope direction
2026-06-17 (full surface, fixed MA(20,50), mean as a *diagnostic* not a disqualifier).
**Discipline (carried, binding):** gross only; detection on HA candles; **every outcome metric on
real prices** (`RealOpen/High/Low/Close`); holdouts sealed; no new-universe row read under the
HA-harami event definition; no TEST/holdout contact; 0 candidate slots until a PROCEED gate.

> **Mandatory reading (carried from 014-B).** Every Phase 015 scope must first read
> `../2026-06-14-014-ha-harami-substrate-and-capture/014-A-conditioning-gap-and-validation-lessons.md`
> and confirm conditioning / harami-anchor / descriptive-position / endpoint discipline.

---

## 1. Why Phase 015 exists, and why it is a *full surface*

Phase 014 mapped the entire capture/exit surface — but **every read used the ZigZag substrate**,
where the conditioned harami is redundant vs random (3/99). EXP-060B then showed the signal is
real on the **MA(20,50) substrate** (beats own-substrate matched-random **85/99**), but at exactly
**one geometry** (V2A partial × `/ADV-NONE` × benchmark cap). So the programme has a complete
surface map on the substrate where the signal is *dead* and a single-point probe on the substrate
where it is *alive*.

Optimising the downside of that one champion geometry would repeat the **mirror of the 014-A
error** the programme logged: never let a narrow read stand in for the family hypothesis. The
correct move is to **re-derive the full 014-B surface on the MA substrate**, so we learn whether
the MA edge is a robust substrate property or a single-geometry artifact — *and*, integrated into
the same slate, why the MA mean is ≈0 and whether any geometry recovers it.

**The single question:** *On the MA(20,50)-substrate conditioned `/STRONG-STAT` HA harami, is there
a capture geometry that is a robust (median-viable, broadly composed, signal-attributable vs
matched-random) **and** mean-positive candidate — and if the mean is negative, is that negativity
structural or a removable-tail artifact?*

**Two conditioning objects (operator direction 2026-06-17).** The substrate swap raises a second
question: *should the strong-move filter be computed on the ZigZag move (as in 014-B) or on the MA
segment we actually trade?* Phase 015 measures both:

> **AMENDED 2026-06-17 — `D0-amendment-001-dual-parallel-substrate.md`.** The two objects below were
> originally hybrid-primary / native-bounded. A propagated defect (EXP-060B/061 `M`-arms condition on
> MA-segment `/STRONG-STAT` and so **are the native object**, while the genuine hybrid object was
> never computed) led to elevating **native to a parallel first-class substrate carrying the full
> surface**, **measured and reported individually** beside hybrid — never pooled. Read both bullets
> as parallel; see the amendment for the corrected slate and reconciliation roles.

- **Hybrid.** Entry events = the EXP-053/060 ZigZag-`/STRONG-STAT`-conditioned haramis (the
  byte-identical EXP-053 population); MA(20,50) supplies only the outcome geometry
  (`rd` / `M_sofar` / target / cap). **Genuinely new object** (never computed before Amendment 001):
  it reconciles to EXP-053's population exactly, but has **no outcome-metric back-reconciliation
  anchor**. Carries the **full** surface.
- **MA-native.** The `/STRONG-STAT` magnitude filter is **recomputed on MA segments** — a harami
  qualifies if the MA-segment magnitude-so-far ≥ p75 of the trailing-20 *confirmed MA-segment*
  magnitudes. Different **entry population** (the "strong move on the substrate you trade"). **The
  existing EXP-060B `M`-arms / EXP-061 `M0` are this object** (the 85/99 edge was native), so it
  **reconciles to them to 1e-9**. Also carries the **full** surface (favourable/third/exit OAT grids
  included).

## 2. Binding inheritances from the G2 / EXP-060B (apply to every read)

1. **Fixed substrate: MA(20,50) on real close.** The substrate parameter is *ratified, not swept*
   (it is what showed signal). MA-parameter sensitivity (`/MA-DOMAIN`-analog) is out of scope for
   Phase 015 — a later registered branch only if the surface earns it. Reuses the EXP-060/060B
   `ma_segment_moves` harness (reconciled 99/99).
2. **Median is the binding viability endpoint (P14, inherited);** **the mean is a *diagnostic*
   co-primary, not a blind disqualifier** (§4). Every read emits raw mean + trimmed/winsorised mean
   + tail-share decomposition, each CI'd, alongside the median.
3. **Matched-random-on-MA null (RM3-analog) in every read.** Signal-attribution requires beating
   the own-substrate random control, not just clearing zero — this is the test that disentangled
   signal from substrate in 060B and must be present everywhere (else "MA wins" is unattributable).
4. **Composition must not rest on 4h-only cells.** The 060B lead leaned on 8/14 low-n 4h cells; the
   P11 quorum rule is tightened so 4h cannot carry a verdict (exact rule a D0 item, §6 Q2).
5. **Fixed per-cell bootstrap seed.** Removes the family-index BENCH-viability ±1–2-cell drift so
   absolute viability counts are stable across the slate's scripts.
6. **Reuse the exact 014-B code; swap the substrate.** Implementation is re-instrumentation, not new
   algorithms — same scripts, substrate set to MA(20,50), plus the mean/trim/tail and RM3 emits.

## 3. Objective

Re-derive the full 014-B capture/exit surface on the MA(20,50) substrate for the conditioned
`/STRONG-STAT` HA harami (entry anchored at the harami confirmation-bar real close) — **hybrid and
MA-native conditioning as parallel first-class substrates, both carrying the full surface, measured
and reported individually (§5; Amendment 001)** — measuring per cell the median (binding) and the
mean + its tail decomposition
(diagnostic), each vs the matched-random null, across the 99-cell member grid — so a single
terminal **G-015** can decide, on the *complete* MA surface, whether the family yields a robust
mean-positive candidate
(→ register + screen), is a structurally un-tradable median-only artifact (→ closure
well-supported), or has a tail-driven recoverable mean needing a targeted follow-up.

## 4. The mean: diagnostic posture (operator direction 2026-06-17)

A negative ATR-normalised per-event **mean** on a fat-tailed distribution is not, by itself, a
verdict — it can be a thin tail of large adverse excursions rather than broad un-tradability
(EXP-060B D1: the MA skew is uncapped-downside-driven, gap 1.20 ATR under `/ADV-NONE` vs 0.49
under a 1:1 stop). Phase 015 therefore **investigates why the mean is negative** before any
disqualification:

- **Tail-share decomposition:** what fraction of total negative contribution comes from the worst
  k% of events? A thin, removable tail ⇒ geometry-recoverable; a broadly negative distribution ⇒
  structural.
- **Trimmed / winsorised mean (CI'd):** if a 5–10% trimmed mean crosses positive while the raw
  mean does not, the negativity is outlier-driven (bound the downside); if the trimmed mean is
  *also* negative, it is structural.
- **Bounded-downside recovery test:** does replacing `/ADV-NONE` with a stop-bearing adverse model
  (1:1, `/ADV-EXTREME-rr1`) truncate the tail and move the raw mean positive? This is the
  mechanistic "can we fix it" read (EXP-065 below).
- **Concentration:** are negative-mean events concentrated in specific instruments/domains/regimes
  (esp. the low-n 4h cells)?

**Closure on the mean is only well-supported if the negativity is shown structural and
geometry-irrecoverable** — trimmed mean also negative, persists under bounded-downside adverse
models, not removable-tail-driven. A bare raw-mean-CI miss never closes the family.

## 5. Experiment slate — full 014-B re-run on MA (gross; 0 slots; 0 TEST)

EXP-IDs assigned at Stage-1 scoping (next free per `python/experiments/INDEX.md`; EXP-061+ at
draft time). Ordering is **lead-then-surface**: the lead front-loads the most decisive reads
(does the signal generalise beyond the champion / is there lifetime room / is the mean
recoverable); the surface runs **regardless** of the lead (no early-closure — symmetric to not
*opening* on a narrow read). All reads carry the §2 inheritances (median binding, mean+trim+tail
diagnostic, RM3 null, non-4h composition, fixed seed).

### Lead (most decisive)

| Order | EXP (planned) | 014-B analog | Question on MA(20,50) |
| --- | --- | --- | --- |
| L1 | EXP-061 | EXP-049 + EXP-053 | **Capture readiness + benchmark efficacy.** MA-segment 3-barrier construction is causal/deterministic/covered; the benchmark-geometry conditioned harami's gross median expectancy vs RM3 — does the signal generalise *beyond* the V2A×ADV-NONE champion? (lightweight readiness — harness already reconciled 99/99.) |
| L2 | EXP-062 | EXP-055 | **Lifetime availability (AVWAP-analog).** MA-segment lifetime favourable MFE vs adverse MAE, gross, ATR-normalised — MA segments are longer (the reason MA "wins"); is there room to bound the downside while keeping favourable capture? |
| L3 | EXP-063 | EXP-057 + mean diagnostic | **Adverse geometry + the mean investigation.** Bounded-downside adverse models (benchmark 1:1, `/ADV-EXTREME-rr1`) vs `/ADV-NONE`, with the §4 tail-share / trimmed-mean / recovery decomposition — the decisive "why is the mean negative, and does bounding fix it" read. |

### Surface (runs regardless; feeds the single gate)

| Order | EXP (planned) | 014-B analog | Question on MA(20,50) |
| --- | --- | --- | --- |
| S1 | EXP-064 | EXP-056 | **Favourable-target geometry.** Benchmark 50%-of-MA-segment vs `/VPTARGET`, `/MAGTARGET`. |
| S2 | EXP-065 | EXP-058 | **Third-barrier geometry.** MA-defined adaptive cap vs `/THIRD-TIME`, `/THIRD-EVENT`. |
| S3 | EXP-066 | EXP-059 | **Position-management exits.** `/EXIT-PARTIAL` (V2A and the other partial arms), `/EXIT-TRAIL-STRUCT`, individually and combined, on MA. |

*(S1–S3 each emit both objects individually — Amendment 001. The combined champions S4/EXP-067 and
EXP-068 are split by object; see "Combined champions" below.)*

### Dual-object surface (Amendment 001) — both objects, every read, reported individually

**AMENDED 2026-06-17 (`D0-amendment-001-dual-parallel-substrate.md`).** Every L1–S3 read above emits
**both** conditioning objects (hybrid and native) **individually** — separate arms, separate
matched-random nulls (`RM-hybrid`, `RM-native`), separate per-cell viability, separate P11, separate
G-015 inputs. **No pooling.** The native object now carries the **full** favourable/third/exit OAT
surface (no longer "bounded"). Reconciliation roles (corrected, P12): the **native** arm reconciles
to EXP-060B `M0/M3` to 1e-9 (the existing `M`-results are native); the **hybrid** arm is a new object
with no outcome anchor (population reconciliation to EXP-053 + determinism + causality + invariants).

### Combined champions (split by object)

| Order | EXP (planned) | Mirrors | Question |
| --- | --- | --- | --- |
| S4 | EXP-067 | EXP-060 | **Hybrid combined champion.** Best per-layer MA geometry on the **hybrid** object vs `RM-hybrid`; native + ZigZag champion disclosed. |
| — | EXP-068 | EXP-060 | **Native combined champion** *(merges the old N1+N2)*. Best per-layer MA geometry on the **native** object vs `RM-native`; hybrid champion disclosed. |
| ~~N2~~ | ~~EXP-069~~ | — | **DROPPED** — native efficacy/availability/adverse/geometry are covered by the dual-object L1–S3 reads; retained in the registry/ledger, never deleted. |

*(EXP-050 position-in-move and EXP-054 fill-model are **not** re-run: 050 is a descriptive,
substrate-attenuating base rate, and 054/P15 is a substrate-invariant method standard already
adopted. EXP-048/049 readiness is folded into L1 as a confirmation, not a fresh readiness phase.)*

## 6. D0 decisions required before G0

1. **Q1 — Register the MA substrate as a countable variant.** In Phase 014 MA(20,50) was a P13
   *baseline*; as the signal's substrate it is a new countable item. **Recommendation: register
   `CF-HA-HARAMI-001/MA-SUBSTRATE`** (MA(20,50) segmentation as the move/direction/target substrate)
   in `multiplicity-registry.md` and `candidate-families/harami.md` at D0, before any read.
2. **Q2 — The non-4h composition rule, exactly.** Draft: a "robust" claim needs ≥5 viable cells over
   ≥3 instruments **with ≥3 cells outside 4h**. Operator to fix (down-weight 4h vs power-upgrade it).
3. **Q3 — Mean diagnostic parameters.** Trim fraction (e.g. 5% / 10%), tail-share definition (worst
   k% of events, k=?), and the mean-CI method (moving-block bootstrap on raw + trimmed). Predeclared,
   no post-result switching.
4. **Q4 — Gate structure.** Recommendation: **single terminal G-015** after the full slate (014-B
   style; the no-early-closure rationale applies again). Operator to confirm vs a lenient-G1/strict-G2.
5. **Q5 — `/ADV-EXTREME-rr1` causal construction on MA** — the prior-move extreme is *MA-segment*
   defined here; confirm extreme of the last *confirmed* MA segment, no look-ahead.
6. **Q6 — RM3-on-MA control reuse** — confirm the matched-random-in-MA-regime selection from
   EXP-060B is reused unchanged as the null in every read.

## 7. G-015 outcome criteria (mechanical, predeclared; adjudicated after the full slate)

All gross; per-cell first, composed by P11 with the §2.4 non-4h rule; median binding (P14), mean
diagnostic (§4); each contrast vs RM3.

The criteria span **both conditioning objects, judged individually** (hybrid EXP-067, MA-native
EXP-068 — Amendment 001; never pooled); the phase outcome is the strongest object's outcome.

| Outcome | Criteria | Consequence |
| --- | --- | --- |
| **PROCEED_TO_SCREEN** | ≥1 MA combined definition — on **either** the hybrid (EXP-067) **or** MA-native (EXP-068) object, judged individually — is **median-viable AND raw-mean-positive** (CI_low>0), beats its same-object matched null, and clears P11 with non-4h breadth. | Register that MA definition (with its conditioning object) as a candidate branch (first slot); begin event-level method calibration (EXP-027-analog). If MA-native is the winner, its full geometry surface is the first promotion scope. |
| **CHARACTERISED_NOT_VIABLE** | Full surface measured on **both** objects (Amendment 001); median-viable in places but the negative mean is shown **structural and geometry-irrecoverable on both objects** (trimmed mean also negative, persists under bounded-downside, not removable-tail-driven). | Last open lever exhausted → family closure well-supported (adjudicated at G-015). |
| **MEAN_RECOVERABLE — FOLLOW-UP** | On either object: median-viable, beats RM3, and diagnostics show the negative mean is **tail-driven / partially recovered** under bounded-downside but not yet cleanly mean-positive at composition (power- or geometry-limited). | Record; family stays OPEN; scope a targeted capped-downside (and/or cost-aware) follow-up — or, if MA-native is the promising-but-incomplete object, its full geometry surface. |
| **SUBSTRATE/METHOD_DEFECT / INCONCLUSIVE** | Determinism/causality/invariant failure (either object); or coverage/power insufficient on a conditioned population with no correctness failure. | Fix / re-baseline; or record and re-scope. |

## 8. Guardrails (carried)

Final-30% global holdout excluded; no new stratum opened (population reuses the EXP-053/060
conditioned `/STRONG-STAT` events; substrate reuses EXP-060/060B `ma_segment_moves`); gross only;
detection on HA candles, all outcome metrics on real prices; MA crossovers, segments, targets, and
caps use only pre-entry confirmed information; matched-random entries constructed causally; no
tuning, no post-result variant selection beyond the predeclared OAT grid; **fixed per-cell
bootstrap seed**; `tqdm`, lazy Polars, per-cell bounded memory over the 99-cell grid; deterministic
(second full pass).

## 9. Immediate next steps

1. **Operator D0** — rule on Q1–Q6 (§6); draft + ratify `D0-predeclarations.md` (substrate fixed at
   MA(20,50); median binding + mean diagnostic posture; RM3 null; non-4h composition; mean-diagnostic
   parameters; gate structure; the `MA-SUBSTRATE` registry item). **G0 gate.**
2. Register the Phase 015 batch (the re-run HYPs, the `MA-SUBSTRATE` variant, the bounded-downside
   arms) in `multiplicity-registry.md` and `candidate-families/harami.md` — before any
   result-producing code.
3. Scope EXP-061 (Stage 1) after the mandatory lessons read; proceed lead → surface under the
   pipeline; single G-015 after the full slate.

---

*Draft companion to the Phase 014 G2 close. The MA-substrate edge that opened this phase is
specified in `../2026-06-14-014-ha-harami-substrate-and-capture/014-B-EXP-060B-ma-substrate-dominance-addendum.md`
and `python/experiments/EXP-060B/`.*
