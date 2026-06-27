# Phase 011 — D0 Predeclarations

**Status:** **RATIFIED 2026-06-11 — G0 PASS.** All items below are FROZEN for
Phase 011; no amendment after this point. The EXP-018 threshold (P1) was
fixed first, before any TRAIN read. All values declared **before any TRAIN
read**; none derives from Phase 011 data.
**Date drafted:** 2026-06-11. **Date ratified:** 2026-06-11.

## P1 — EXP-018 portfolio-fitness go/no-go threshold (PRIMARY ENDPOINT; design §8.5 item 1, §5.5)

- **Estimand:** portfolio-level incremental **net** per-event expectancy of
  the candidate portfolio C (each member cell at its TRAIN-selected exit)
  over the reference book R = Donchian(20) run on the same member
  instrument×domain cells, equal-weight across member cells, under the frozen
  CONSERVATIVE cost model (P2) + per-instrument financing, evaluated **once**
  on the TEST stratum.
- **Inference:** frozen EXP-027 regime-cluster bootstrap machinery
  (per-instrument calibration per Track A); one-sided test at α = 0.05.
- **R1.2 calibration:** pre-TEST matched-structure synthetic-null calibration
  of the bootstrap at the realized portfolio cluster structure; mechanical
  margin `m = max(0, Q95 of null ci_low_1s)`.
- **Verdict rule (binding, one read):**
  **PORTFOLIO_PASS** iff `ci_low_1s > m` **and** `boot_p < 0.05`
  (one-sided, incremental excess > 0). Otherwise **PORTFOLIO_FAIL**.
  No materiality floor beyond the calibrated margin; no second read; no
  post-hoc re-weighting or member re-selection.
- Ledgered as a disclosure against every member stratum (§7.1).

## P2 — Cost model, all 17 instruments (design §8.5 item 2, §7.3)

Structure identical to EXP-030 (frozen): per-side `c_i` covers half-spread +
commission + slippage; `RT_i = 2 × c_i` per realized position; BASE
diagnostic-only; **CONSERVATIVE = 2 × BASE is binding**. Financing charged
per calendar day held, adverse-side (Phase 008 layer). Values are
operator-declared constants (the dataset carries no bid/ask); frozen at G0,
no post-result iteration.

**Correction recorded:** design §7.3 lists EURUSD RT as 1.2 bps; the EXP-030
frozen CONSERVATIVE value is **3.0 bps** (and USTEC 5.0 / XAUUSD 6.0, listed
as TBD in §7.3). The EXP-030 table is authoritative; §7.3's 1.2 was a
transcription error.

| Instrument | `c_i` one-way (bps) | CONSERVATIVE RT (bps) | Financing (bps/day) | Source |
|---|---:|---:|---:|---|
| EURUSD | 0.75 | 3.0 | 0.6 | EXP-030 / Phase 008 (frozen) |
| USTEC | 1.25 | 5.0 | 1.2 | EXP-030 / Phase 008 (frozen) |
| XAUUSD | 1.50 | 6.0 | 1.2 | EXP-030 / Phase 008 (frozen) |
| BTCUSD | 4.00 | 16.0 | 10.0 | EXP-030 / Phase 008 (frozen) |
| GBPUSD | 1.00 | 4.0 | 0.8 | typical raw-spread cTrader retail all-in |
| USDJPY | 0.90 | 3.6 | 0.7 | as above |
| USDCHF | 1.10 | 4.4 | 0.7 | as above |
| USDCAD | 1.10 | 4.4 | 0.7 | as above |
| AUDUSD | 1.00 | 4.0 | 0.7 | as above |
| NZDUSD | 1.30 | 5.2 | 0.8 | as above |
| EURJPY | 1.10 | 4.4 | 0.8 | as above |
| GBPJPY | 1.40 | 5.6 | 1.0 | as above |
| AUDJPY | 1.30 | 5.2 | 0.9 | as above |
| US500 | 0.80 | 3.2 | 1.2 | index CFD spread + financing (USTEC-class) |
| US2000 | 1.50 | 6.0 | 1.2 | as above (wider small-cap spread) |
| DE30 | 1.00 | 4.0 | 1.2 | as above |
| JP225 | 1.20 | 4.8 | 1.2 | as above |

## P3 — Track A0 scan parameters (design §8.5 item 3, §5.2)

> **MOOT 2026-06-11:** Track A0 removed (FRAMING_ERROR — the band is an
> exit parameter; design §11 amendment;
> `docs/code-reviews/2026-06-11-band-multiplier-framing-error.md`). EXP-042
> executed under this predeclaration and was set aside. Retained unaltered
> as the frozen record; no Phase 011 decision uses it.

- **Reference horizons:** H ∈ {4, 8, 16} domain bars; the middle horizon
  (H = 8) is the binding rank statistic.
- **Minimum event-count floor:** ≥ **30 TRAIN events** per cell per band.
  A band failing the floor in a cell is imputed that cell's worst rank.
  Rationale: below ~30 events a per-event mean is too unstable to rank
  (EXP-032's n = 27 read was margin-bound); 30 also matches the smallest
  usable 4h TRAIN populations seen at band = 1.0.
- The selection statistic (within-cell band ranks → best median rank across
  cells; wider-band tie-break) is fixed in design §5.2.

## P4 — Stability-score floor for portfolio membership (design §8.5 item 4, §5.4)

A tunable cell joins the candidate portfolio iff its leading family's
stability score at θ\* clears:

> **S(θ\*) ≥ +1 × SE**, where SE is the bootstrap standard error of the
> cell's TRAIN net mean (the same SE used in the tunability separation rule).

i.e., the 3-point stability-neighbourhood net expectancy must be positive by
at least one SE. This excludes noise-dominated cells whose plateau is
indistinguishable from zero, without introducing a new reference quantity.

## P5 — G2 composition threshold (design §8.5 item 5, §8.3)

Track C is authorized iff the membership set contains **≥ 5 member cells
spanning ≥ 3 distinct instruments**. Below that, the phase closes
FOUNDATION_NON-TUNABLE with no TEST read spent.

## P6 — MAD-band-multiplier exit grid (design §8.5 item 6, §5.4)

m ∈ **{0.5, 0.7, 1.0, 1.4, 2.0, 2.8, 4.0, 5.7}** — geometric, ratio ≈ √2,
8 points (matches the FH grid geometry). Edge rules identical to FH:
endpoints ineligible as θ\*; stability argmax on an endpoint → non-tunable
for the family. Trend-change leg unchanged (MA(20,50) regime flip).

## P7 — 2h domain construction (design §8.5 item 7, §5.3)

`xen.bar_aggregator.aggregate_ohlc(period_minutes=120, min_coverage=0.90)`,
clock-aligned — the exact convention already frozen for 1h/4h
(EXP-001/003/012 onward). Determinism, event rates, and domain artifacts
verified by the EXP-020-analog before Track B.

## P8 — DE30 disposition (design §8.5 item 8, §7.2)

**Use as-is**, with the truncated-history disclosure (broker history ends
2026-01-16; ~5 months short; 70/30/holdout boundaries from its own realized
timeline) carried verbatim in every result artifact that includes DE30.
Re-collection under an alternative broker symbol remains available later but
does not gate Phase 011.

## G0 checklist (design §8.1)

| Item | State |
|---|---|
| TEST-read ledger materialized with §7.1 backfill | DONE (`docs/signal-registry/test-read-ledger.md`) |
| Cost model covers all 17 instruments | P2 — RATIFIED |
| EXP-018 go/no-go threshold fixed | P1 — RATIFIED (fixed first) |
| A0 reference horizons + event-count floor fixed | P3 — RATIFIED |
| MAD-band grid fixed | P6 — RATIFIED |
| Stability floor fixed | P4 — RATIFIED |
| G2 composition, 2h construction, DE30 | P5/P7/P8 — RATIFIED |

**G0: PASS (2026-06-11).** Tracks A0/A/B data contact is now authorized.

## Ratification record

- 2026-06-11 — Operator ratified P1 (EXP-018 threshold as drafted, no extra
  materiality floor), P2 (full 17-instrument cost table as drafted, incl. the
  §7.3 EURUSD RT transcription-error correction), P4/P5 (stability floor
  S(θ\*) ≥ +1×SE; G2 composition ≥5 cells over ≥3 instruments), P8 (DE30
  as-is with truncated-history disclosure). P3/P6/P7 ratified as part of the
  document. G0 PASS recorded here and in the multiplicity registry.
