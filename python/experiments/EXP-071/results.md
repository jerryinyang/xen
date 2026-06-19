# EXP-071 — Results & Interpretation (Stage 6)

**Verdict: `TEST_NOT_CONFIRMED`** (Evidence AGAINST, on this scope)
**Family:** CF-HA-HARAMI-001 / CAND-001 (MA-native, `N-PARTIAL-V2A` lead) · **HYP-024**
**Posture:** gross only (no costs) · **Date:** 2026-06-19 · **Audit:** PASS (0C/1W/3I)

This is the harami family's **first counted TEST contact**. Six counted TEST reads consumed
(one per binding stratum); the shot is one-shot and irrevocable regardless of outcome (D0 P6).

---

## 1. Headline

On the TEST stratum of the predeclared 6-cell `N-PARTIAL-V2A` G-015 passing family, the
MA(20,50)-native `/STRONG-STAT`-conditioned HA harami **does not** clear the predeclared
composition threshold. **0 of 6 cells** satisfy the full conjunction (median CI_low>0 Holm ∧
raw-mean CI_low>0 ∧ beats-RM CI_low>0 Holm ∧ median > calibrated margin); the threshold required
≥3 cells over ≥2 instruments with ≥2 non-4h. **4 of 6 cells have one-sided median CI_low ≤ 0**
— a majority directional failure, not a power shortfall — so the mechanical D0 P9 rule returns
`TEST_NOT_CONFIRMED`, not `TEST_INCONCLUSIVE`.

All 6 cells were powered (≥30 events; m = 3843/376/287/129/554/75); none below floor. P12
reconciliation exact (0.0), determinism PASS.

## 2. Per-cell read (binding arm `N-PARTIAL-V2A`)

| Cell | n | median (CI_low 1s) | raw-mean (CI_low) | beats-RM Holm | median>margin | temporal | **clears?** |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **GBPUSD-5m** | 3843 | **0.761 (0.428)** ✓Holm | 0.090 (**−0.086**) ✗ | **✓** | ✓ | GROWING | **no** — raw-mean fails (▲ yellow-flag) |
| GBPUSD-1h | 376 | 0.130 (−0.851) | −0.187 (−0.669) | ✗ | ✓ | DECAYING | no |
| NZDUSD-1h | 287 | 0.597 (−0.056) | −0.100 (−0.656) | ✗ | ✓ | DECAYING | no |
| NZDUSD-2h | 129 | 0.503 (−1.309) | −0.192 (−0.849) | ✗ | ✓ | STABLE | no |
| GBPJPY-30m | 554 | 1.056 (≈0⁺) ✗Holm | 0.359 (**0.063**) ✓ | ✗ | ✓ | DECAYING | no — both Holm legs fail |
| US2000-4h | 75 | 0.932 (−1.132) | 0.010 (−0.788) | ✗ | ✓ | STABLE | no |

Reading the conjunction structure:

- **No single cell passes all four legs.** The two cells with any positive signal each fail a
  *different* leg: GBPUSD-5m is the only Holm-significant median and beats-RM cell, but its raw
  mean is dragged negative; GBPJPY-30m is the only raw-mean-positive cell, but neither of its
  Holm-adjusted legs survives the family correction.
- **`margin_clear` passes in all 6** — every median point estimate exceeds its small EXP-070
  calibrated margin (0.05–0.17 ATR). This leg is non-discriminating here: the medians are
  positive-tilted, but the CIs are wide, so the margin pass carries no weight without the
  CI-based legs. This is the conjunction working as designed (a point estimate above a margin
  is necessary, not sufficient).
- **Holm cost is decisive.** Both GBPUSD-5m and GBPJPY-30m have raw (unadjusted) positive median
  CI_low; after the 6-cell Holm step-down only GBPUSD-5m survives the median leg and only it
  survives the beats-RM leg. The family-wise correction, predeclared at D0, is what collapses
  the borderline cells — exactly its purpose.

## 3. Why NOT_CONFIRMED rather than INCONCLUSIVE

The portfolio composite median CI is strictly positive (`composite_median = 0.774`,
CI_low 1s = 0.496). Taken alone this looks like a positive family signal — but it is **not**, and
the verdict is correctly the negative one, for two reasons:

1. **The composite is event-pooled and GBPUSD-5m-dominated** (audit WARNING-1). The pool is
   5264 per-event returns, of which GBPUSD-5m contributes 3843 (73%). The composite median is
   essentially GBPUSD-5m's median re-expressed at family scale; it is **not** a cell-balanced
   read and must not be interpreted as breadth. The composite is a non-binding D0 P10 disclosure,
   not a gate, precisely so it cannot rescue a per-cell failure.
2. **The per-cell evidence is a majority directional negative.** 4/6 cells have median CI_low ≤ 0;
   the binding `N-PARTIAL-V2A` raw means are negative in 4/6 cells (only GBPUSD-5m and GBPJPY-30m
   positive). This is the systematic-negative signature the D0 P9 rule maps to NOT_CONFIRMED.

**Caveat (audit INFO-1):** part of the negative is genuinely power-limited — NZDUSD-1h's median
CI_low is −0.056 (a hair below zero) and US2000-4h is a single thin 4h cell (n=75). So the read
is "majority directional negative with two near-zero/under-powered cells," not "uniformly,
strongly negative across the family." This does not change the predeclared verdict, but it
shapes the follow-up: the family is **not** refuted as a concept, only this candidate definition
on this scope.

## 4. Disclosed arms (non-binding)

- **`N-V2A×ADV-NONE`** (TAIL_DRIVEN companion): medians larger across the board (0.85–1.32) but
  raw means negative in 4/6 cells (GBPUSD-5m −? positive 0.074; GBPJPY-30m +0.573; the rest
  negative). No cell is flagged `mean_recoverable` (winsorm+ ∧ mean−) under the ≥30-event rule —
  the ADV-NONE winsorized means do not cleanly sit positive while the raw mean is negative in a
  way that isolates a tail-filter candidate here. This weakens, but does not eliminate, the
  EXP-072 tail-filter thesis for this scope.
- **`N-BENCH`** (signal-check anchor): medians positive in 5/6 cells (US2000-4h negative −0.378),
  raw means mixed — consistent with a weak, geometry-independent positive median tilt that does
  not survive the full inferential conjunction.
- **`RM-native`** medians are near zero (0.016–0.192), confirming the matched-random attribution
  reference behaves as a ~null and that the binding arm's failure is not an artifact of an
  inflated null.

## 5. Yellow-flag cell — GBPUSD-5m (the one real signal)

GBPUSD-5m is the family's single positive cell and carries the predeclared yellow flag
(median+ ∧ beats-RM+ ∧ winsorm+ `0.163` ∧ raw-mean− `−0.086`). The signature is textbook
PARTIAL_RECOVERY tail-drag: a positive bulk pulled to a negative raw mean by a small number of
large adverse outcomes. It is GROWING on TRAIN (the cleanest temporal flag), high-n (3843), and
the only cell to survive both Holm legs. **This is the natural seed for a TRAIN-only diagnostic**:
if the raw-mean drag is a small identifiable loss tail (e.g. an exhaustion-magnitude upper bound
or harami-polarity↔reversal-direction disagreement), the cell may be conditionally recoverable.
That diagnostic is already registered as HYP-027 / EXP-074 (TRAIN-only, no candidate slot, no
TEST contact) — see §7.

## 6. Temporal-flag retrospective

The three DECAYING cells (GBPUSD-1h severe, NZDUSD-1h mild, GBPJPY-30m severe) all fail in TEST,
consistent with their measured TRAIN-period decay — not independent evidence against the family,
but coherent with the decay trajectory. The two STABLE cells (NZDUSD-2h, US2000-4h) also fail
(NZDUSD-2h with a wide negative CI; US2000-4h power-limited). The single GROWING cell (GBPUSD-5m)
is the only one that carries positive signal into TEST. The pattern — only the GROWING cell holds
up — is mild corroboration that EXP-070's temporal flags were informative, though n=6 is far too
small to claim the flags predicted the TEST outcome.

## 7. Consequences (D0 P9 / family routing)

- **CAND-001 is retired on this scope.** The MA-native `N-PARTIAL-V2A` candidate, as defined and
  on the predeclared 6-cell family, does not confirm. The **family stays OPEN** — the result is
  a candidate-definition negative, not a family refutation (the median tilt and the GBPUSD-5m
  survivor argue against closure).
- **Six counted TEST reads consumed** (GBPUSD-5m/1h, NZDUSD-1h/2h, GBPJPY-30m, US2000-4h), one
  per stratum, recorded in `test-read-ledger.md` in the same change as this result. Each stratum
  now stands at 1/2 lifetime counted reads. The portfolio composite is entered as a **disclosure**
  against all 6 strata, not a counted read.
- **No EXP-072 / EXP-073 activation** — those are conditional on TEST_CONFIRMED.
- **Routing to EXP-074 (HYP-027), already registered** as the TRAIN-only diagnostic follow-up on
  the GBPUSD-5m large-loss tail (primary) and the 5 disclosed family cells. No candidate slot,
  no TEST contact; requires the Phase 016 D0 addendum before execution. This is the principled
  next step: understand *why* the one high-quality cell's mean is tail-dragged before deciding
  whether a bounded-downside or tail-filtered re-scope is warranted.

## 8. Limitations

1. **Gross only.** No costs; even a hypothetical confirmation would have been necessary-not-
   sufficient for tradability (EXP-072 scope). The negative is therefore conservative — costs
   would only worsen it.
2. **First TEST read on a 2-read cap.** The strata are now half-consumed; a future
   stratum-specific harami confirmation has one read left each. Effect sizes reported as observed,
   no shrinkage.
3. **Composite is single-cell-dominated** (§3) — explicitly not a breadth statement.
4. **n=6 family** is small; the Holm correction is strict at this size, and two cells are
   near-zero/under-powered. The verdict is robust to this (0 cells clear even before Holm on the
   conjunction, since no cell passes all four legs on raw CIs either), but the INCONCLUSIVE/
   NOT_CONFIRMED boundary is the genuinely debatable margin — resolved mechanically by D0 P9.
