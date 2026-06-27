# Phase 013 — D0 Predeclarations

**Status:** **RATIFIED 2026-06-12 — G0 PASS.** All items below are FROZEN
for Phase 013; no amendment after this point. All values declared **before
any data contact** under any `/ANCHOR` definition; none derives from Phase
013 data. The two flagged research choices were operator-ratified: ATR
prominence multiple **`k = 1.0`** (P1) and floor headroom multiple **`M = 2`**
(P5).
**Date drafted:** 2026-06-12. **Date ratified:** 2026-06-12.

## P1 — `/ANCHOR` ATR-prominence pivot rule (design §5.1) **[RATIFY]**

Replace the baseline running-extreme anchor with an **ATR-prominence
significant pivot**, computed from completed bars only and selectable at the
regime-confirmation bar (look-ahead safe). For a confirmed regime change:

- **Candidate:** the segment extreme since the prior confirmed regime change
  (lowest `Low` for an incoming bull regime; highest `High` for bear) — the
  same point the baseline uses.
- **Prominence test:** the candidate qualifies as a significant pivot iff a
  counter-move of **≥ `k × ATR(ATR_period)`** away from it has *already
  completed* by the regime-confirmation bar (ATR on the same domain bars,
  completed bars only).
- **Parameters (proposed):** `ATR_period = 14` (project Renko default; a
  single fixed value, **not** swept — sweeping would be anchor tuning);
  prominence multiple **`k = 1.0`** (parsimony; mirrors the 1.0 MAD-band
  multiplier convention). `k` is the definition of "significant" and is the
  primary ratification question.
- **Tie-break:** if several segment pivots clear `k × ATR`, take the **most
  price-extreme** (lowest low / highest high); exact ties → most recent.
- **Fallback:** if no pivot in the segment clears `k × ATR` before regime
  confirmation, anchor at the **running extreme** (baseline) and tag the
  event `anchor_fallback = true` (fallback rate is a disclosure column — a
  high fallback rate means `/ANCHOR` collapses toward baseline and is itself
  an informative read).
- Everything else frozen to baseline: MA(20,50) regime, typical-price source,
  `TickVolume**0.75` weight, 1.0-MAD band, arm/trigger-at-AVWAP-line event
  rule, pyramid handling.

## P2 — `/ANCHOR` readiness criteria (design §5.1, §8.2)

A cell is **READY** iff, on TRAIN: 0 invariant violations (EXP-020 invariant
set, anchor-adapted), determinism replay drift = 0, no look-ahead-safety
failure (anchor selectable from bars ≤ regime-confirmation bar; ATR causal),
and ≥ 30 TRAIN `/ANCHOR` events. NOT_READY cells are excluded from the
move-size comparison with the failing check recorded. Readiness is the
EXP-020 analog required because `/ANCHOR` is a new event definition (design
§1.4).

## P3 — Move-size statistics (design §5.2) **[RATIFY floor multiple in P5]**

Per cell × anchor, TRAIN events only, gross, real prices:

- **Primary — MFE:** max favorable direction-signed real-price excursion from
  the trigger close over the event lifetime; lifetime = to MA(20,50)
  trend-change or analysis-set end (EXP-022 boundary). Unfinished events
  counted and disclosed, not dropped. Report **median MFE** + IQR + bootstrap
  SE of the median (frozen EXP-027 resampling layer, descriptive).
- **Companion — MAE:** matching max adverse excursion; median + SE.
- **Context — matched-control MFE:** same MFE on matched non-event bars
  (instrument/domain/regime-direction; EXP-021/027 matching), descriptive.

No fixed-horizon expectancy headline (Phase 012 measured gross(H), flat);
this is the horizon-independent ceiling read.

## P4 — Cost-floor reference (design §5.3)

`floor_i,d = RT_i + financing_i × days(L_i,d, d)`, frozen Phase 011 P2
CONSERVATIVE table (RT_i, financing_i verbatim), where `L_i,d` is the cell's
**median lifetime holding time in domain bars** and
`days(L, d) = L × hours(d) / 24`, hours(d) ∈ {1, 2, 4}. The floor is a
**reference line only — never subtracted** from any move-size value.

## P5 — Per-cell shift classification (design §5.4) **[RATIFY]**

A cell is **SHIFTED_VIABLE** iff **all** hold:

1. `median_MFE(/ANCHOR) ≥ median_MFE(baseline) + 1 × SE_diff` (material
   rightward shift; SE of the median difference, bootstrap; 1×SE = the
   Phase 011 P4 / Phase 012 P5 noise-guard convention), and
2. `median_MFE(/ANCHOR) ≥ M × floor_i,d` with floor multiple **`M = 2`
   (proposed)** — the available peak move must be at least twice the cost
   floor to leave room for partial capture net of cost, and
3. `Δ median_MAE ≤ Δ median_MFE` (the adverse-side shift does not erase the
   favorable gain), and
4. ≥ 30 TRAIN `/ANCHOR` events (P2), and
5. determinism replay passes.

`M = 2` is a judgment about how much headroom over the floor makes a
viability phase worth opening; it is the second ratification question.
Otherwise **NOT_SHIFTED**.

## P6 — G1b composition threshold (design §5.4, §8.3)

**ANCHOR_MOVE_VIABLE** iff the SHIFTED_VIABLE set spans **≥5 cells over ≥3
distinct instruments** (Phase 011 P5 / Phase 012 P6 breadth convention).
Otherwise **ANCHOR_MOVE_FLAT** → route to a new candidate family (operator
pre-commitment, design §1.5).

## P7 — Cell universe and event floor (design §4, §5.4)

- Cell universe: the **full 17-instrument × {1h, 2h, 4h} grid** (EXP-043
  grid). Membership is defined by `/ANCHOR` **readiness** (P2), not inherited
  from the old-anchor 37-cell COVERED map. DE30 truncation (VAL-003) carried
  as a per-cell disclosure.
- Event floor ≥ 30 TRAIN events per cell for both readiness and shift
  eligibility; below-floor cells report descriptively, marked BELOW_FLOOR.
- Both anchors generated on the identical TRAIN slice (1-minute-row
  `train_end_ts` boundary, Phase 008 R1.3); TEST/holdout untouched.

## P8 — Substrate integrity requirement (design §7)

`xen.avwap` gains a parameterized anchor rule with **the baseline
running-extreme anchor reproducing Phases 004–012 bit-for-bit** at default
parameters. The Phase 011/012 regression suite
(`python/tests/test_avwap_band_param.py` conventions) is extended with:
baseline-anchor fixture invariance at defaults, `/ANCHOR` ATR-prominence
look-ahead-safety + determinism smoke tests, and the running-extreme fallback
path — all green before the first TRAIN read.

## G0 checklist (design §8.1)

| Item | State |
|---|---|
| P1 `/ANCHOR` ATR-prominence rule + params (`ATR_period=14`, `k=1.0`) | RATIFIED |
| P2 readiness criteria | RATIFIED |
| P3 MFE/MAE/matched-control statistics | RATIFIED |
| P4 cost-floor reference | RATIFIED |
| P5 per-cell shift classification (floor multiple `M=2`) | RATIFIED |
| P6 G1b composition threshold | RATIFIED |
| P7 cell universe + event floor | RATIFIED |
| P8 regression-suite extension | RATIFIED (suite extension must be green before first TRAIN read) |
| Registry amended (Phase 013 batch) | DONE (`docs/signal-registry/multiplicity-registry.md`) |

**G0: PASS (2026-06-12).** EXP-047 TRAIN data contact is authorized once the
P8 regression-suite extension (baseline-anchor invariance + `/ANCHOR`
look-ahead-safety/determinism smoke + fallback path) is green.

## Ratification record

- 2026-06-12 — Operator ratified P1–P8. The two flagged research choices were
  decided: ATR prominence multiple `k = 1.0` (P1) and floor headroom multiple
  `M = 2` (P5); the remaining items inherit the Phase 011/012 conventions as
  drafted. No value changed between draft and ratification; no data contact
  occurred before ratification. G0 PASS recorded here and in the multiplicity
  registry (Phase 013 batch).
