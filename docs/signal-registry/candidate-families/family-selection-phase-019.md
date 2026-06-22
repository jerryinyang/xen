# Family-Selection Phase 019 — Candidate Families Under Consideration

**Status:** `DRAFT — PENDING-SELECTION` (2026-06-22). This document registers the **slate of entry-side
candidate families competing in the Phase 019 family-selection availability screen**, and the full
discussion behind each. **None is opened**: no candidate slot is consumed and no CF-XXX is promoted to a
governing checkpoint until the Phase 019 screen `ADMITS` its information axis at G-019, at which point the
winning family is promoted to its own `candidate-families/cf-*.md` spec with its own G0/D0. Ranking sets
exploration order; **every `ADMITTED` axis is eventually opened** (Phase 019 design §7).

**Governing phase:** [`../../experiments-docs/checkpoints/2026-06-22-019-family-selection-availability-screen/design.md`](../../experiments-docs/checkpoints/2026-06-22-019-family-selection-availability-screen/design.md)
· gate [`G-019-gate-criteria.md`](../../experiments-docs/checkpoints/2026-06-22-019-family-selection-availability-screen/G-019-gate-criteria.md)
· predeclarations `D0-predeclarations.md`.
**Provenance:** promoted from the three post-Phase-018 reflections —
[cold autopsy](../../experiments-docs/reflections/2026-06-22-cold-autopsy-three-families-next-family.md),
[next-family recommendation](../../experiments-docs/reflections/2026-06-22-next-family-recommendation.md),
and their reconciliation
[`2026-06-22-reconciliation-and-family-selection-phase.md`](../../experiments-docs/reflections/2026-06-22-reconciliation-and-family-selection-phase.md)
— plus the standing two-family retrospective and the Phase 018 retrospective.
**Real-price / holdout discipline (binding for every family below):** all return/range outcomes on real
prices (`RealOpen/High/Low/Close`); HA/Renko brick prices never enter a return/range metric; the final-30%
global holdout is never read in screening or any future readiness/characterization; counted TEST reads are
spent only at a future binding confirmation under the 2-lifetime-per-stratum cap.

---

## 0. The shared diagnosis (why these axes, and why not another price-pattern family)

Three families are closed with the holdout sealed: CF-AVWAP-001 (ANCHOR_MOVE_FLAT), CF-HA-HARAMI-001
(CLOSE_FAMILY), CF-CAPGEO-001 (NOT_CONFIRM). Re-derived from primary evidence, they are **one failure three
times**: *single-instrument, event-driven, price-geometry entries carry no signal-conditional favourable
excursion beyond a matched random control — availability ≈ random.*

| Evidence | Finding |
| --- | --- |
| **EXP-047** (AVWAP, 51 cells) | Event lifetime MFE ≈ matched-control MFE on every domain (1h 24.0 vs 24.9, 2h 35.9 vs 31.6, 4h 64.5 vs 59.1 bps). "The bounce trigger does not access privileged move sizes." Available peak 5–9× the cost floor — but so is the random control's. |
| **EXP-081** (harami/AVWAP, 46 cells, 5-year) | Favourable availability `MFE_med` Δ-over-random −0.140 (real>random **17/46**) for harami, +0.061 (**28/46**, coin-flip) for AVWAP; outcome-median edge ~chance (23–25/46). Adverse `MAE_q90` Δ-over-random −0.719 (9/46) — *typical* range also below random. Only structure = outcome **shape** (median-positive/mean-killed, tail-concentrated). |
| **EXP-084** (portfolio OOS) | **Exit-invariant** NOT_CONFIRM — 0/11 exit arms had a positive OOS CI_low; the apparent edge was selection-region overlap and reversed in the fresh folds. The whole downstream stack (exit, cost, sizing, conditioning) is exonerated as the binding lever. |

**The 2×2 (design §2).** Every family lived in **single-series × directional**, the one dead cell. Three
cells are untested. The families below are the candidates for those cells. **The one thing the evidence
forecloses** is another entry whose distinguishing feature is its single-instrument price-geometry pattern
on a directional target — that cell is dead, twice over, with the holdout still sealed to prove it.

---

## CF-VOLEXP-001 — Single-Series Volatility-Expansion (Magnitude)

**Status:** `DRAFT — PENDING-SELECTION` (gated on Screen M / EXP-086).
**2×2 cell:** single-series × **magnitude**.
**Prior:** **low, tail-concentrated** (see below) — run first because it is the cheapest way to *close the
single-series quadrant*, not because the evidence points here.

**Thesis (one falsifiable sentence):** *A single-series compression / quiet-state signal predicts forward
**realized range / magnitude** (independent of direction) beyond a matched random control — harvestable as a
two-sided breakout/straddle rather than a directional bet.*

**Evidence basis (precise — the prior is low):**
- The recurring **median-positive / mean-killed, heavy-tailed** shape (EXP-068/074/081) is the fingerprint a
  *magnitude* signal leaves when scored as *signed* return — and the harami literally *is* a compression
  pattern (inside bar on HA). The programme measured `E[signed return]` ≈ 0 and concluded "no edge"; the
  structure, if any, lives in `E[|return|]` / realized range. **This cell has never been screened.**
- **But typical range is NOT elevated:** EXP-081 `MAE_q90` Δ-over-random is −0.719 (real>random 9/46) and
  `MFE_med` is −0.140 (17/46) — both below random. So a naive pooled `|move|` endpoint will null out. The
  **only** positive-magnitude evidence is the rare catastrophic tail (`tailmass` 0.0526 vs random 0.0437,
  31/46 cells), and EXP-074's `msofar_atr` q05 adverse-tail separation (rank-biserial 0.68–0.80) — which is a
  *within-sample, adverse-side, conditional* separation, **not** an apples-to-apples "compression predicts
  large two-sided range over random." That number has never been computed; Screen M computes it.

**Fixed first-branch definitions (frozen at Screen M D0; the eventual family inherits these):**
- **Conditioning primitive:** HA-harami inside-bar (the existing detector) **and** a clean NR/inside-bar
  primitive (NR4/NR7 or inside-bar, frozen at D0) — single-series compression states.
- **Availability endpoint (SPLIT — never pooled):** (i) typical-range `max(MFE,MAE)` / `MFE+MAE`,
  ATR-normalised; (ii) tail/bimodality `tailmass` / `q05` / dip-p + the `msofar_atr`-as-magnitude read.
- **Harvest model (BINDING):** any admission is **long-vol** — the predictable component is rare and
  adversely-timed (it is *your own* adverse tail), so the family must clear a **two-sided cost** (round-trip ×
  2 sides + financing) on a straddle/breakout, never a directional claim. A magnitude "pass" is **not** a
  tradable edge; treating it as one would re-run the gross→net trap that ate AVWAP.

**Hypotheses (registered; EXP-IDs assigned at promotion):**
- `CF-VOLEXP-001/HYP-001` — *Screen M availability* (Phase 019, **EXP-086**): does either the typical-range or
  the tail read beat the multiplicity-adjusted admission gate? (admit/exonerate, 0 slots, 0 reads.)
- `CF-VOLEXP-001/HYP-002+` — readiness / characterization / two-sided-cost net screen — **only if admitted**,
  at a future G0/D0.

**Kill / pass:** **EXONERATE** the cell iff *both* the typical-range and tail reads fall in the null band
(EXP-086) → single-series magnitude is dead, single-series row of the 2×2 fully closed. **ADMIT** (tail-only =
long-vol; typical-range = directional/range family) iff a read clears the admission gate.

**Exclusions / deferred:** no exit, sizing, or P&L work until availability is admitted (capture geometry and
sizing are exonerated levers — they return only *after* a first-order availability edge exists); no directional
re-use of a tail-only admission.

---

## CF-XSECT-001 — Cross-Sectional Relative Strength

**Status:** `DRAFT — PENDING-SELECTION` (gated on Screen X / EXP-087).
**2×2 cell:** **cross-sectional** × directional.
**Prior:** the **a-priori favourite on mechanism grounds** (cross-asset relative strength is a demonstrably
non-random anomaly elsewhere) — but it must **earn** first place on the screen like any other axis.

**Thesis (one falsifiable sentence):** *An entry conditioned on cross-sectional relative strength (basket-relative
momentum / divergence rank across the 16-instrument universe) produces signal-conditional favourable excursion
beyond a matched within-instrument random control.*

**Evidence basis (mechanism, not in-programme evidence):**
- Every family so far was **time-series** — "does *this* instrument move after the signal." The programme has
  16 instruments across FX / metals / crypto / indices, 5 years, synchronized, and has **never once asked a
  relative question.** The dead cell is specifically *single-series price geometry*; cross-sectional momentum
  sources its edge from the **relationship between instruments**, a fundamentally different signal from
  anything tested. This is the minimal data-respecting injection of information *not present in the single
  series*, at **zero new collection** (constructible from the existing VAL-005 dataset).
- This is explicitly **a bet, not a finding** — the programme has never tested it. Screen X exists to kill the
  bet cheaply if it is wrong.

**Fixed first-branch definitions (frozen at Screen X D0):**
- **Universe:** the 16 VAL-005 instruments (synchronized 5-year 1m).
- **Cross-sectional conditioning:** basket-relative momentum / divergence **rank** at each timestamp (lookback,
  rank-vs-divergence formulation, rebalance cadence frozen at D0); read per (instrument, domain) cell so the
  cell count matches the single-series screens for like-for-like admission-gate calibration.
- **Availability endpoint:** favourable excursion `MFE_med` Δ-over-random (directional-favourable; the
  cross-sectional anomaly is directional by construction).

**Hypotheses (registered; EXP-IDs at promotion):**
- `CF-XSECT-001/HYP-001` — *Screen X availability* (Phase 019, **EXP-087**): does cross-sectional-conditioned
  favourable availability beat the multiplicity-adjusted admission gate?
- `CF-XSECT-001/HYP-002+` — readiness / characterization / net screen — **only if admitted**, at a future G0/D0.

**Kill / pass:** **EXONERATE** iff it reproduces the ≈-random pattern (cross-sectional price information is then
also exhausted). **ADMIT** iff favourable-availability Δ-over-random clears the gate.

**Multiplicity caution (BINDING):** ranking over 16 instruments manufactures the **most** cells → the
permuted-axis admission gate (D2b) matters most here; a lucky single cell must not admit the axis.

**Exclusions / deferred:** the full pivot to a ranking / rebalance / market-neutral *portfolio* construction
(new infrastructure — the referee suite, separability gate, and per-event expectancy are built for
single-instrument events) is deferred to the family's own post-admission G0/D0; Screen X is the cheap
availability read only, not the portfolio build.

---

## CF-FLOW-001 — Order-Flow / Liquidity-Imbalance (runner-up, reserved-conditional)

**Status:** `DRAFT — PENDING-SELECTION` (gated on Screen F / EXP-088, **reserved-conditional** — run only if
the operator wants a third comparison after M and X).
**2×2 cell:** order-flow information × {directional, magnitude}.
**Prior:** lower than X (EXP-046 found tick-volume-weighted construction inert once; tick volume is
broker-dependent) — but it brings genuinely orthogonal *flow* information that price geometry does not contain.

**Thesis (one falsifiable sentence):** *Entries at significant tick-volume / volume-at-price imbalance extremes
show favourable (and/or magnitude) availability beyond a matched random control.*

**Fixed first-branch definitions (frozen at Screen F D0):** tick-volume / volume-at-price imbalance-extreme
conditioning; availability endpoint = favourable `MFE_med` plus the split magnitude reads (as for M); matched
within-instrument random control.

**Hypotheses:** `CF-FLOW-001/HYP-001` — *Screen F availability* (Phase 019, **EXP-088**, reserved-conditional).

**Kill / pass:** **EXONERATE** iff ≈-random; **ADMIT** iff a read clears the multiplicity-adjusted gate.

**Exclusions / deferred:** broker-dependence of tick volume must be disclosed; any admission's robustness to
the volume proxy is a future-family concern.

---

## EXONERATED reference — Single-Series Directional Price-Geometry (the dead cell)

**Status:** `RETIRED-MEASURED` (not a candidate; recorded so it is not silently reopened).
The CF-AVWAP-001 / CF-HA-HARAMI-001 / CF-CAPGEO-001 surface — single-instrument, event-driven,
price-geometry entries on a directional target — is **empirically exhausted** (availability ≈ random, two
matched-control designs EXP-047/081; exit-invariant OOS NOT_CONFIRM EXP-084). Re-opening this cell requires a
**genuinely new lever** (a different information source or target — i.e., one of the families above), under its
own D0/G0, never a re-parameterization of the exhausted surface.

---

## Selection mechanics (how a family here becomes a real family)

1. **Phase 019 screens** each axis's availability (EXP-086/087/(088)) against the **multiplicity-adjusted
   admission gate** (D2b) — TRAIN-only, 0 slots, 0 counted reads.
2. **G-019** emits a ranked **admit / exonerate / inconclusive** inventory (gate criteria §4).
3. **Each `ADMITTED` axis** is promoted to its own `candidate-families/cf-*.md` spec and opened at its own
   G0/D0, **best-first** by the frozen Δ-over-random metric; the rest queue (ranking orders, never prunes).
4. **If all `EXONERATED`:** price-derived information is exhausted on this dataset → the frontier is non-price
   data acquisition (operator decision), reached at 0 reads / 0 slots.

All outcomes — admit, exonerate, inconclusive — are **retained** in this registry and the
multiplicity-registry Phase 019 batch, never deleted or reused.
