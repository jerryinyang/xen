# Phase 015 D0 — Predeclarations (CF-HA-HARAMI-001, MA-Substrate Full Surface)

**Status:** **DRAFT — NOT RATIFIED. G0 PENDING (operator).** These are the proposed frozen
governance parameters for Phase 015. No Phase 015 data contact (no `results/` under any Phase 015
EXP) is permitted before the operator ratifies this file at **G0**. Items flagged
**[OPERATOR-RATIFY]** are genuine discretion points; items flagged **[REC]** are concrete
recommendations the operator accepts or amends.
**Checkpoint:** `2026-06-17-015-ma-substrate-conditioned-harami-full-surface`
**Governing design:** `design.md` (this directory).
**Family:** `CF-HA-HARAMI-001` (REGISTERED, OPEN) — continuation phase.
**Inherits:** Phase 014 `D0-predeclarations.md` (P1–P13), `014-B-D0-addendum.md` (P14–P21), and
the 014-B fill standard (P15). Where a Phase 015 item supersedes an inherited one, it says so.
**Discipline (binding):** gross only (no costs); detection on HA candles; **every outcome metric
on real prices** (`RealOpen/High/Low/Close`), never HA prices; holdouts sealed; no new-universe
row read under the HA-harami event definition; no TEST/holdout contact; nothing tuned against
data; any change after ratification is a new registered branch or a dated amendment.

> **Mandatory-reading precondition (binding, inherited).** No Phase 015 scope is admissible until
> it records, in `scope.md`, that
> `../2026-06-14-014-ha-harami-substrate-and-capture/014-A-conditioning-gap-and-validation-lessons.md`
> was read and that the experiment honours the conditioning / harami-anchor / descriptive-position
> / endpoint rules. Enforced at Stage 4 (REVISE if absent).

---

## P1 — Substrate: MA(20,50) on real close, **fixed** (semantics bound to EXP-060/060B)

The Phase 015 substrate is the **MA(20,50) crossover segmentation on real domain close**, used as
the move / direction / favourable-target-reference / adaptive-cap source for the conditioned
harami's outcome geometry — exactly the `ma_seg_arm` / `ma_segment_moves` construction validated
in EXP-060 and EXP-060B (reconciled 99/99 there).

- **MA(20,50) is ratified, not swept.** The (fast=20, slow=50) parameter is fixed for the phase;
  MA-parameter sensitivity (`/MA-DOMAIN`-analog) is **out of scope** — a later registered branch
  only if the surface earns it.
- **Exact semantics bind to the EXP-060B implementation,** not to prose: the segment definition,
  trade direction `rd`, magnitude-so-far `M_sofar`, favourable-target level (`0.5 · M_sofar` at
  benchmark), and MA-defined adaptive cap are whatever `ma_seg_arm` computed in EXP-060B. **P12
  reconciliation** reproduces EXP-060B's M3 (and BENCH) to full precision before any new read.
- **Causality:** MA crossovers, segment boundaries, `M_sofar`, targets, and caps use only
  information confirmed **at or before** the harami entry bar; no unconfirmed/forward segment
  pivot is referenced. The developer confirms this against the EXP-060B code at Stage 3.

## P2 — Conditioned signal, entry anchor, and the two conditioning objects **[RATIFIED 2026-06-17; AMENDED 2026-06-17 — Amendment 001: both objects parallel full-surface, reported individually]**

> **AMENDED by `D0-amendment-001-dual-parallel-substrate.md` (2026-06-17).** The original P2 made
> hybrid the primary/full-surface object and native a *bounded co-investigation*. That rested on a
> propagated defect: EXP-060B/061's `M`-arms (the supposed hybrid anchor) actually condition on
> MA-segment `/STRONG-STAT` and so **are the native object** (8360 events), while the genuine hybrid
> object (ZZ-conditioned 3202 × MA-geometry) was never computed. Amendment 001 elevates **native to
> a parallel first-class substrate carrying the full surface**, tested and **reported individually**
> beside hybrid (separate arms, separate nulls, separate viability/composition/G-015 inputs — never
> pooled). See the amendment for the root cause and slate.

Entry is anchored at the **harami confirmation-bar real close** in both objects; position-in-move
stays descriptive-only. Phase 015 measures **two conditioning objects, in parallel, on every read,
reported individually** (no aggregation):

- **Hybrid.** Entry events = the EXP-053/060 ZigZag-`/STRONG-STAT`-conditioned haramis,
  **byte-identical** to those reads (population reconciled exact to EXP-053). MA(20,50) supplies only
  the outcome geometry (`rd` / `M_sofar` / target / cap). **This object is genuinely new** (never
  computed before Amendment 001) → **no back-reconciliation anchor** (P12 amended).
- **MA-native.** The `/STRONG-STAT` magnitude filter is **recomputed on confirmed MA segments** — a
  harami qualifies if MA-segment magnitude-so-far ≥ p75 of the trailing-20 *confirmed MA-segment*
  magnitudes (causal: only segments confirmed at/before the harami bar). Different entry population.
  **It carries the full L1–L3 / S1–S3 surface** (no longer bounded). It **reconciles to EXP-060B
  `M0/M3` / EXP-061 `M0` to 1e-9** — the existing `M`-results are this object (P12 amended).

## P3 — Binding viability endpoint: **median** gross per-event expectancy (P14 inherited)

Per event, the rule (entry + barriers/exits) produces a realised **gross** return, direction-signed,
**ATR-normalised** (cell confirmation-bar ATR(14)), on real prices under the P15 fill model.

- **Binding per-cell endpoint:** **median** per-event gross return, with a regime-clustered
  moving-block bootstrap CI (`b = round(m^(1/3))`, `N_BOOT = 10_000`).
- **Per-cell viability:** median **CI_low > 0** and **≥ 30 events**; composed by P11 (with the
  P6 non-4h rule).
- **[REC] Fixed per-cell bootstrap seed** (`seed = hash(cell_id)` or a per-cell constant table)
  so absolute viability counts are stable across Phase 015 scripts (removes the family-index
  BENCH ±1–2-cell drift). This supersedes the context-dependent RNG stream used in 014-B.

## P4 — The **mean** is a *diagnostic* co-primary, **not** a disqualifier **[OPERATOR-RATIFY]**

A negative ATR-normalised per-event mean on a fat-tailed distribution is investigated, not
auto-failed. Every outcome read emits, alongside the median:

- **Raw mean** (bootstrap CI, fixed seed);
- **[REC] Trimmed mean — 10% symmetric trim** (bootstrap CI) — separates outlier-driven from
  structural negativity;  *(operator may set 5% / 10%)*
- **[REC] Tail-share** — the fraction of total negative return contributed by the **worst 5% of
  events**;  *(operator may set k)*
- **Concentration** — negative-mean events by instrument / domain / regime (esp. low-n 4h).

**Closure-on-mean rule (binding):** a median-viable / raw-mean-negative result **does not close the
family.** Closure is well-supported only on a **positive demonstration of structural
irrecoverability** — trimmed mean also negative **and** the negativity persists under bounded-downside
adverse models (P7) **and** it is not removable-tail-driven. A bare raw-mean-CI miss never closes.

## P5 — Matched-random null, **per conditioning object**, in **every** read **[RATIFIED 2026-06-17; AMENDED 2026-06-17 — Amendment 001]**

Reuse EXP-060B's matched-random in-MA-regime entry selection as the null. The null is **matched to
each object's population**, and **every read emits both objects' nulls individually**:
**RM-hybrid** (matched to the hybrid qualifying count/regime) and **RM-native** (matched to the
native qualifying count/regime). Each object reports its own **signal − null** contrast with an
**independent** bootstrap CI (per EXP-060B I2: matched-random events are not paired; no common
subset). Signal-attribution requires beating the **same-object** matched null (contrast CI_low > 0),
not merely clearing zero. **The two objects' contrasts are never pooled.** *(Amendment 001: the null
formerly named `RM3` is the native-object null on the existing `M`-arms; the hybrid object gets its
own `RM-hybrid` drawn from the same in-MA-regime pool, matched to the 3202-class hybrid count.)*

## P6 — Composition: P11 + non-4h rule **[OPERATOR-RATIFY]**

A family-level "robust"/"viable"/"candidate" claim requires P11 (≥ 5 viable cells over ≥ 3
instruments) **with the [REC] additional constraint that ≥ 3 of the qualifying cells are outside
the 4h domain** — so the verdict cannot rest on the low-n 4h cells that carried the EXP-060B lead
(8/14). *(Operator alternative: power-upgrade 4h rather than down-weight — decide at G0.)*

## P7 — Adverse models & causal construction **[OPERATOR-RATIFY on Q5]**

- **Bounded-downside set (binding axis):** **benchmark 1:1** and **`/ADV-EXTREME-rr1`** (registered).
- **`/ADV-NONE`** is retained as the **disclosed unbounded reference** (the EXP-060B champion's
  adverse model), not as a viability candidate — it is the skew source under study.
- **`/ADV-EXTREME-rr1` construction:** the prior-move extreme is the extreme of the **last
  confirmed MA segment** (no look-ahead); the rr1 constraint applies as registered. Confirmed
  against EXP-057/060B code at Stage 3.

## P8 — Favourable / third-barrier / exit grids (OAT, reuse 014-B)

The favourable-target (EXP-056), third-barrier (EXP-058), and position-management-exit (EXP-059)
OAT grids are reused **unchanged** on the MA substrate (registered variants `/VPTARGET`,
`/MAGTARGET`, `/THIRD-TIME`, `/THIRD-EVENT`, `/EXIT-PARTIAL`, `/EXIT-TRAIL-STRUCT`). One-at-a-time
against predeclared MA benchmark defaults; **no new variants** beyond the registered set; **no
post-result variant selection.** A failed geometry is a valid result, not licence to try another.

## P9 — Slate, ordering, and the single terminal gate **[RATIFIED 2026-06-17 — single G-015; AMENDED 2026-06-17 — Amendment 001: dual-object surface, native track collapsed; AMENDED 2026-06-18 — Amendment 002: EXP-067 dropped, Phase 015 slate complete]**

> **AMENDED by Amendment 001.** Every L1–S3 read now emits **both** objects (hybrid + native)
> **individually**. The separate bounded native track (old N1 EXP-068, N2 EXP-069) collapses: native
> efficacy/availability/adverse/geometry are covered by the dual-object L1–S3 reads, so only a single
> native combined champion remains.

- **Surface slate (each read emits hybrid + native individually; planned IDs EXP-061+):**
  L1 = EXP-061 (049+053-analog: MA capture readiness + benchmark efficacy, each object vs its own
  null); L2 = EXP-062 (055-analog: lifetime availability); L3 = EXP-063 (057-analog adverse geometry
  + the P4 mean diagnostic). Surface S1 = EXP-064 (056), S2 = EXP-065 (058), S3 = EXP-066 (059) —
  favourable / third-barrier / exit OAT grids on **both** objects.
- **Combined champions (split by object):** **EXP-068** = **native** combined champion (best per-layer
  native geometry vs `RM-native`; hybrid disclosed) — **merges the old N1+N2**; **COMPLETE 2026-06-18,
  PROCEED_TO_SCREEN-candidate.** **EXP-067** (hybrid combined champion) is **DROPPED by
  `D0-amendment-002-drop-exp067.md` (2026-06-18, operator direction)** — the hybrid object is
  EVIDENCE_AGAINST across the entire individual surface (no per-layer winner to combine), it gates
  nothing (G-015 PROCEED requires ≥1 combined definition on **either** object; native EXP-068 already
  qualifies), and it is adjudicated at G-015 on the disclosed surface reads. Retained in the
  registry/ledger, never deleted/reused. **EXP-069 is DROPPED** (Amendment 001; retained, never
  deleted).
- EXP-050 and EXP-054 are **not** re-run (descriptive / method-invariant).
- **Ordering:** lead (L1–L3) → surface (S1–S3) → combined champion (EXP-068 native; EXP-067 hybrid
  dropped per Amendment 002). All reads run **regardless** of the lead — **no early-closure path**.
  *(Amendment 002 note: dropping EXP-067 is **not** an early closure — it drops a confirmatory read on
  an object already EVIDENCE_AGAINST across the full individual surface; every read on the **native**
  object that carries the live signal was run, and the family is not closed — it advances to G-015 with
  a native PROCEED-candidate.)*
- **Re-run discipline (Amendment 001):** EXP-061/062/063 are re-run under the dual-object design and
  **supersede their prior results in place** (same IDs; prior finding recorded `SUPERSEDED` with a
  defect pointer).
- **Single terminal G-015** after the full slate. Outcome criteria = `design.md` §7, judged **per
  object individually** (PROCEED_TO_SCREEN / CHARACTERISED_NOT_VIABLE / MEAN_RECOVERABLE—FOLLOW-UP /
  SUBSTRATE-METHOD_DEFECT / INCONCLUSIVE). PROCEED registers a candidate branch (first slot), tagged
  with its conditioning object, only at G-015.

## P10 — Power floor

≥ 30 events per cell on the MA-conditioned population. Conditioning + MA-segment qualification will
reduce counts vs the unconditioned base; cells below 30 are **NOT_VIABLE-by-power**, disclosed,
never defaulted to a ratio.

## P11 — Registry items **[RATIFIED 2026-06-17 — register MA-SUBSTRATE + two conditioning modes]**

- **Register `CF-HA-HARAMI-001/MA-SUBSTRATE`** — MA(20,50) crossover segmentation as the
  conditioned harami's move/direction/target/cap substrate — in `multiplicity-registry.md` (new
  Phase 015 batch) and `candidate-families/harami.md`, **before any result-producing code.** In
  Phase 014 MA(20,50) was a P13 *baseline*; as a substrate it is a new countable item.
- **Record two conditioning modes under `MA-SUBSTRATE` as distinct countable arms:** `hybrid`
  (ZigZag-`/STRONG-STAT`-conditioned entries; the EXP-060B object) and `native`
  (`/STRONG-STAT` recomputed on MA segments; new entry population). Both are countable in the
  Phase 015 batch; the native mode is a new countable item.
- The bounded-downside arms (1:1, `/ADV-EXTREME`) and the reused OAT variants are already
  registered (Phase 014/014-B batches); Phase 015 records their MA-substrate reuse.
- **0 candidate slots, 0 TEST reads** for all Phase 015 experiments (characterization/diagnostic).
  A slot is consumed only at a G-015 PROCEED. `test-read-ledger.md` unchanged; holdouts sealed.

## P12 — Reconciliation & determinism regression gate (before any new read) **[AMENDED 2026-06-17 — Amendment 001: reconciliation roles corrected]**

> **AMENDED by Amendment 001 — the anchor was assigned to the wrong object.** EXP-060B's `M`-arms
> condition on MA-segment `/STRONG-STAT`, so they **are the native object**, not the hybrid one. The
> reconciliation roles therefore flip:

- **Native object → reconciles to EXP-060B `M0/M3` (and EXP-061 `M0`) per-cell point estimates to
  full float precision** (`RECON_TOL = 1e-9`) — the existing `M`-results are this object. Plus the
  determinism second-pass and the causality/invariant checks (ADV-NONE fires 0 ADV exits;
  matched-count holds; weights sum to 1.0), and an explicit causality check that the native
  `/STRONG-STAT` filter references only confirmed prior MA segments.
- **Hybrid object → has NO back-reconciliation anchor** (it was never computed before Amendment
  001). It relies on **population reconciliation to EXP-053's ZigZag-`/STRONG-STAT` set (exact
  count, per cell)** + the determinism second-pass + the same causality/invariant checks.

A reconciliation, determinism, or causality failure is a **SUBSTRATE/METHOD_DEFECT** — fix before
reporting.

---

## Slot & ledger accounting (binding)

- All Phase 015 experiments are characterization/diagnostic: **0 candidate slots, 0 TEST reads.**
- The registered variants consume a slot only when a future scope activates one as a screening
  candidate — which, per P9, cannot happen before G-015 PROCEED_TO_SCREEN.
- TEST-read ledger unchanged; holdouts sealed; no new-universe row read under the HA-harami event
  definition.

## D0 question map (for the G0 review)

| D0 item | Design §6 | Predeclaration |
| --- | --- | --- |
| Q1 — register MA substrate as countable item | Q1 | **P11** ([REC] register `MA-SUBSTRATE`) |
| Q2 — non-4h composition rule | Q2 | **P6** ([REC] ≥3 qualifying cells outside 4h) |
| Q3 — mean-diagnostic params | Q3 | **P4** ([REC] 10% trim; worst-5% tail-share) |
| Q4 — gate structure | Q4 | **P9** ([REC] single terminal G-015) |
| Q5 — `/ADV-EXTREME-rr1` causal construction on MA | Q5 | **P7** (last confirmed MA segment, no look-ahead) |
| Q6 — RM3-on-MA reuse | Q6 | **P5** (reuse EXP-060B selection; RM3-native for native reads) |
| — hybrid vs MA-native conditioning | — | **P2** (RATIFIED — hybrid primary + native co-investigated; **AMENDED 2026-06-17 by Amendment 001 → both parallel full-surface, reported individually**) |

## Ratification checklist (operator, at G0)

- [x] P1–P12 reviewed; substrate fixed at MA(20,50); semantics bound to EXP-060B + P12 reconciliation. *(operator agreed Q1–Q6, 2026-06-17)*
- [x] P2 conditioning ruled — **hybrid primary + MA-native co-investigated (bounded)**, 2026-06-17. **AMENDED 2026-06-17 (Amendment 001): both objects parallel first-class full-surface, reported individually.**
- [x] P4 mean-diagnostic posture + parameters ruled (median binding; mean diagnostic; 10% trim; worst-5% tail-share).
- [x] P6 non-4h composition rule ruled (≥3 qualifying cells outside 4h).
- [x] P9 gate structure ruled (single terminal **G-015**).
- [x] P11 `MA-SUBSTRATE` + two conditioning modes registry item ruled.
- [x] **Final operator G0 sign-off on this assembled D0 — G0 PASS 2026-06-17 (operator).** Registry entry + EXP-061 scoping authorized. `MA-SUBSTRATE/native` confirmed as a countable mode under the substrate branch (operator did not object). No Phase 015 data contact occurred before this record.

**Status after this checklist: G0 PASS 2026-06-17.** Pipeline entry point: register the Phase 015
batch in `multiplicity-registry.md` + `candidate-families/harami.md`, then scope EXP-061 (Stage 1)
after the mandatory lessons read.
