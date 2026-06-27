# G1 Gate Review — Phase 012 Screen Adjudication

**Date:** 2026-06-12
**Gate:** G1 — screen adjudication (mechanical), design §8.2
**Adjudicated by:** desk review (research-pipeline governance); operator ratification pending
**Inputs:** EXP-046 (`python/experiments/EXP-046/`: report.md, results.md,
results/clearance_table.csv, results/variant_rollup.csv,
results/reconciliation.csv, results/run_metadata.json, audit.md PASS
0C/0W/3 Info, post-experiment governance APPROVE)

---

## Verdict

```text
G1 STATUS: ENTRY_GROSS_FLAT
PHASE 012: CLOSES — programme pivots to substrate revision (operator
pre-commitment, design §1.4.2)
```

Design §8.2 makes G1 a mechanical count: ENTRY_GROSS_VIABLE iff ≥1
non-baseline variant's clearing set meets the P6 composition threshold
(≥5 cells over ≥3 instruments). No variant meets it; the readout is FLAT.

## Mechanical count (from `variant_rollup.csv`)

| Variant | Axis | Clearing cells | Distinct instruments | Composition met |
| --- | --- | --- | --- | --- |
| baseline | (reference row) | 3 | 3 | n/a |
| alpha_0.0 | /ALPHA | 2 | 2 | NO |
| alpha_0.375 | /ALPHA | 2 | 2 | NO |
| alpha_1.0 | /ALPHA | 3 | 3 | NO |
| ma_10_25 | /MA-DOMAIN | 0 | 0 | NO |
| ma_40_100 | /MA-DOMAIN | 3 | 2 | NO |
| ma_60_150 | /MA-DOMAIN | 1 | 1 | NO |

Best non-baseline clearing set is 3 cells (alpha_1.0, ma_40_100) against
the ≥5/≥3 threshold — not a near miss. No non-baseline variant exceeds the
baseline's own 3 clearing cells, so the levers add no breadth over the
substrate they perturb. The full 259-row gross-vs-floor decomposition is
carried in the EXP-046 report per design §6.

## Integrity preconditions (all satisfied — the FLAT readout is valid)

- **Baseline reconciliation:** 259/259 legs PASS at 1e-9 bps — 37 EXP-043
  event-count identities, 111 EXP-045 FH-net anchors (θ ∈ {4, 8, 16}, full
  population, forced-clip convention), 111 internal gross-path
  cross-checks.
- **Determinism:** 259/259 cell×variant replays frame-identical.
- **Event floor:** no wholesale collapse — 10/259 rows BELOW_FLOOR, all
  slow-MA 4h cells (attrition, not integrity).
- **P8 regression gate:** green before first TRAIN read (24/24 tests incl.
  baseline-fixture invariance at default α/MA); audit re-ran it green.
- **Budget discipline:** 0 TEST reads, ledger unchanged (EURUSD-4h AT CAP 2,
  USTEC-4h 1, XAUUSD-4h 1, all others 0); holdouts sealed; no scope or
  threshold change after data contact.

## Adjudication notes (caveats carried, none alters the count)

1. **Predeclared false-positive channel confirmed, cuts against the 14
   observed clearances:** 12/14 CLEAR rows are 4h cells, 8 involve US index
   CFDs (US2000-4h clears under five variants incl. baseline), with SEs
   6–28 bps at n = 33–66. Cross-cell noise correlation (correlated index
   bloc) and the calendar-day floor understatement (largest for 4h index
   cells; binding on sub-5-bps margins such as DE30-4h alpha_1.0 at
   +0.85 bps) both inflate, not deflate, the observed clearance count —
   they reinforce FLAT.
2. **Effect-size context:** variant H=8 cross-cell medians span −2.35 to
   +0.28 bps around the baseline's −1.15 bps, against floors of ~5–20 bps.
   The full sampled range of both levers moves typical gross by ~1–2 bps —
   an order of magnitude short. The gross shortfall is a substrate
   property, not a parameterization property.
3. **OAT sufficiency:** `/ALPHA`×`/MA-DOMAIN` interactions were excluded at
   D0; given note 2, an interaction closing the gap is implausible, and no
   second entry-parameter phase exists on this substrate (pre-commitment).
4. **US2000-4h repeated clearance** is recorded as hypothesis-generating
   only (notes 1–2); it confers no routing weight.

## Operator decision record

Design §1.4.2 (ratified pre-data, 2026-06-12): *"if the screen returns
ENTRY_GROSS_FLAT, the programme pivots to substrate-level revision — no
second entry-parameter phase on this substrate."* The routing is therefore
pre-decided; this review applies it. Per design §9, no further routing
discussion is needed.

## Consequences

| Item | State |
| --- | --- |
| Phase 012 | CLOSES — ENTRY_GROSS_FLAT; retrospective records the hand-off (design §10) |
| `CF-AVWAP-001` entry-parameter lever (`/ALPHA`, `/MA-DOMAIN`) | Measured and exhausted on this substrate (joins the exit lever, Phases 010–011) |
| Phase 013 | Substrate revision: starts from the Stage-C registered branches (`/LB` `/MB` `/ATR` `/ANCHOR`, deferred since Phase 005) and the Phase 011 gross decomposition; any new event definition requires new readiness/calibration/parity passes (EXP-020/027/029 analogs) under its own design/D0 |
| EXP-046 harness | Available for re-use against a revised substrate (dependency gates, 1e-9 reconciliation pattern, mechanical clearance) |
| TEST budget | Untouched (0 of ≤6 reads spent); ledger unchanged; holdouts sealed |
