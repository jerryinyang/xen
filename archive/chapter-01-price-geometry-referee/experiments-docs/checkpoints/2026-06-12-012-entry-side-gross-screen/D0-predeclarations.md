# Phase 012 — D0 Predeclarations

**Status:** **RATIFIED 2026-06-12 — G0 PASS.** All items below are FROZEN
for Phase 012; no amendment after this point. All values declared **before
any TRAIN read under any variant definition**; none derives from Phase 012
data.
**Date drafted:** 2026-06-12. **Date ratified:** 2026-06-12.

## P1 — `/ALPHA` variant grid (design §5.1)

Tick-volume exponent α ∈ **{0.0, 0.375, 0.75, 1.0}**; baseline 0.75.
- 0.0 = unweighted (TWAP-like) anchor — the structural lower edge.
- 0.375 = midpoint of {0, 0.75} on the exponent scale.
- 1.0 = full volume weighting (classical VWAP) — the structural upper edge.
- Run with `/MA-DOMAIN` at baseline (20,50). No interior-point eligibility
  rule applies (this is a screen over a bounded structural range, not a
  stability-plane selection); all four points report.

## P2 — `/MA-DOMAIN` variant grid (design §5.1)

MA crossover (fast, slow) ∈ **{(10,25), (20,50), (40,100), (60,150)}**;
baseline (20,50). Ratio fast:slow fixed at 1:2.5 throughout (isolates the
*scale* of the regime detector; ratio variation is a different lever, not
scoped). Geometric-ish scale ladder ×2/×4/×6 around baseline fast period.
Run with `/ALPHA` at baseline 0.75.

## P3 — Reference horizons and binding horizon (design §5.2)

Gross per-event expectancy at H ∈ **{4, 8, 16} domain bars**; **H=8
binding** for clearance; H=4/16 sign-robustness disclosures. Direction-
signed, real prices, gross (no costs, no financing). Bootstrap SE at H=8
via the frozen EXP-027 resampling layer, descriptive only.

## P4 — Cost-floor formula (design §5.3)

`floor_i,d = RT_i + financing_i × days(8, d)` with the frozen Phase 011 P2
CONSERVATIVE table (RT_i, financing_i unchanged, verbatim) and

`days(H, d) = H × hours(d) / 24`, hours(d) ∈ {1, 2, 4}

→ days(8, 1h) = 1/3, days(8, 2h) = 2/3, days(8, 4h) = 4/3. (Calendar-day
approximation; deterministic, declared here, identical across variants so
floor comparisons are variant-invariant within a cell.)

## P5 — Clearance margin (design §5.3)

A cell clears for a variant iff **gross(H=8) ≥ floor + 1 × SE** and
gross(H=4) > 0 and gross(H=16) > 0. The 1×SE multiplier is fixed here
(matches the Phase 011 P4 convention of one-SE guards; a noise guard, not
an error-rate claim).

## P6 — G1 composition threshold (design §5.4, §8.2)

**ENTRY_GROSS_VIABLE** iff ≥1 non-baseline variant clears in **≥5 cells
spanning ≥3 distinct instruments** (echoes Phase 011 P5; the follow-on
phase needs at least this much breadth for its portfolio endpoint to be
worth building). Otherwise **ENTRY_GROSS_FLAT** → substrate pivot
(operator pre-commitment, design §1.4.2).

## P7 — Event floor and cell universe (design §5.3, §1.3)

- Cell universe: the Phase 011 **37-cell COVERED grid** verbatim
  (EXP-044 `coverage_map.csv`); the 14 excluded cells stay excluded.
- Per cell × variant: ≥ **30 TRAIN events** required for clearance
  eligibility (below-floor cells report descriptively, marked
  BELOW_FLOOR).
- Determinism replay required per cell × variant; any failure excludes the
  cell×variant pair with the failure recorded.

## P8 — Substrate integrity requirement (design §7)

`xen.avwap` is parameterized for α and MA inputs with **defaults
reproducing the frozen baseline bit-for-bit**; the Phase 011 regression
suite (`python/tests/test_avwap_band_param.py` conventions) is extended
with: baseline-anchor fixture invariance at default parameters, α/MA
parameter-effect smoke tests, and determinism replay — all green before
the first TRAIN read.

## G0 checklist (design §8.1)

| Item | State |
|---|---|
| P1 `/ALPHA` grid | RATIFIED |
| P2 `/MA-DOMAIN` grid | RATIFIED |
| P3 horizons + binding horizon | RATIFIED |
| P4 cost-floor formula | RATIFIED |
| P5 clearance margin | RATIFIED |
| P6 G1 composition threshold | RATIFIED |
| P7 event floor + cell universe | RATIFIED |
| P8 regression-suite extension | RATIFIED (suite extension must be green before first TRAIN read) |
| Registry amended (Phase 012 batch) | DONE (`docs/signal-registry/multiplicity-registry.md`) |

**G0: PASS (2026-06-12).** Track A (EXP-046) TRAIN data contact is
authorized once the P8 regression-suite extension is green.

## Ratification record

- 2026-06-12 — Operator ratified P1–P8 as drafted (go-ahead recorded on the
  full draft package: design.md + this document; no value changed between
  draft and ratification; no data contact occurred before ratification).
  G0 PASS recorded here and in the multiplicity registry.
