# Experiment Report: EXP-057 — Adverse-Target Geometry (Conditioned HA Harami; `/ADV-EXTREME`, `/ADV-NONE` vs Benchmark 1:1)

**Status**: COMPLETED — EVIDENCE_FOR
**Date**: 2026-06-16
**Phase / checkpoint**: 2026-06-14-014-ha-harami-substrate-and-capture (014-B surface read 2)
**Family / candidate**: `CF-HA-HARAMI-001` (REGISTERED, OPEN) · `CF-HA-HARAMI-001/HYP-010` — EXP-057
**Instruments**: all 17 (BTCUSD, EURUSD, USTEC, XAUUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, US500, US2000, DE30, JP225); 99 member cells
**Data Views / Feature Categories**: 5m/15m/30m/1h/2h/4h real domain OHLC; HA candles for harami detection only; ATR-ZigZag substrate (Wilder ATR 14/1.0); `/STRONG-STAT` live magnitude-percentile filter (p75, trailing 20); benchmark 3-barrier system (P2 50%/P3 1:1/P4 adaptive time-cap) re-anchored at the harami entry; P15 path-ordered intrabar fills; P14 median per-event ATR-normalised gross return endpoint
**0 candidate slots, 0 TEST reads, TRAIN-only, gross.**

---

## Question

For the live `/STRONG-STAT`-conditioned HA harami (anchored at the harami confirmation-bar close, faded against the in-progress strong move, favourable target held at benchmark 50%-of-`M_sofar`), does changing **only the adverse target** — from the benchmark 1:1 (`adv_dist = 0.50 × M_sofar`) to a faded-move extreme stop (`/ADV-EXTREME`, raw and ≥1:1-constrained) or to no stop at all (`/ADV-NONE`) — improve gross per-event median expectancy (ATR-normalised, P15 fills, real prices) vs the benchmark?

## Hypothesis

At least one alternative adverse-target geometry (`/ADV-EXTREME` raw or ≥1:1-constrained; `/ADV-NONE`) produces higher gross per-event median expectancy (P14, ATR-normalised, P15 fills, real prices) than the benchmark 1:1 adverse target (P3), on the binding `/STRONG-STAT` arm, with the favourable target (50%-of-`M_sofar`) and third barrier (adaptive time cap) held at benchmark (OAT on adverse geometry). Falsifiable: if no alternative variant clears P11 quorum (≥5 cells over ≥3 instruments with CI_low > 0 on its own expectancy) *and* beats the benchmark (paired contrast CI_low > 0 in the quorum), then the hypothesis fails.

## Method

TRAIN-only (first 49%), gross, 0 candidate slots, 0 TEST reads. For each of 99 member cells: reproduce the EXP-053 conditioned population byte-identically (live `/STRONG-STAT`-filtered HA haramis anchored at the harami confirmation-bar close, faded against the in-progress strong move), then vary **only** the adverse target over 4 predeclared variants — BENCH (1:1 reference), ADV-EXTREME-raw (buffered faded-move extreme, R:R free), ADV-EXTREME-rr1 (extreme widened to ≥1:1), ADV-NONE (no stop, fav-or-timecap only). Favourable target (50%-of-`M_sofar`) and third barrier (adaptive cap) and P15 fills held at benchmark. Per-cell median gross ATR-normalised expectancy via regime-clustered moving-block bootstrap (10,000 draws, fixed seed b=20260615). Paired variant−benchmark contrast on common qualifying subset (binding). Two P13 baselines per variant (matched-random, MA(20,50)-seg; disclosed). P11 composition for WIN = viable (CI_low > 0 on its own expectancy, n≥30) + beats-benchmark (paired CI_low > 0 in quorum).

## Results

### Finding 1: ADV-NONE wins — removing the adverse barrier improves expectancy

- **Verdict**: EVIDENCE_FOR. **Passing variant**: ADV-NONE.
- **23 WIN cells over 15 instruments** (P11 quorum ≥5 cells/≥3 instruments — not fragile). n_pass = 1, fragile_passes = [].
- BTCUSD-5m: ADV-NONE median = +0.163 ATR (benchmark +0.057), paired contrast CI_low = +0.083 > 0. FAV count rises from 745 to 802. Removing the stop lets more events reach the favourable target, and the positive tail dominates the larger negative timecap tail.

### Finding 2: ADV-EXTREME-raw (tight stop) destroys expectancy

- **0 viable cells, 0 WIN cells** — median negative in every cell.
- BTCUSD-5m: median = −0.368 ATR (benchmark +0.057); FAV=627, ADV=1631 — 2.6× more stop-outs than wins.
- First-hit r ≈ 0.28 (well below 0.50 as predicted). The tight extreme-anchored stop converts winners to stop-outs.

### Finding 3: ADV-EXTREME-rr1 (extreme-anchored, ≥1:1) ties the benchmark

- **8 viable cells (7 instruments), 0 WIN cells** — never beats the benchmark.
- BTCUSD-5m: median = +0.059 (benchmark +0.057), contrast CI_low ≈ 0.0.
- Extreme-anchoring alone at equal R:R does not outperform the mid-anchored 1:1 benchmark. This isolates the mechanism: ADV-NONE's improvement comes from **removing the stop entirely**, not from repositioning it.

### Finding 4: The r narrative is confirmed as disclosed secondary

- ADV-EXTREME-raw pushes r well below 0.50; ADV-NONE produces degenerate r = 1.0 (no ADV possible by sentinel construction). The median expectancy endpoint captures the timecap tail that r misses — confirming P14's design rationale.

## Audit Summary

- **Verdict**: PASS — 0 Critical, 0 Warning, 2 Info (duplicated `_zero_reasons` helper; TickVolume loaded for aggregation parity pre-approved).
- All 4 predeclared invariant checks pass (BENCH matches EXP-053 exactly 99/99 cells, raw ≤ rr1 adv_dist event-wise, ADV-NONE 0 ADV outcomes, adverse-side ordering correct).
- Determinism: 17/17 cells byte-identical.
- Causality: 0 violations across all cells and variants.
- Reconciliation: 99/99 cells PASS — diff = 0.0 on m and median vs EXP-053.

## Interpretation

**EVIDENCE_FOR** — `/ADV-NONE` (removing the adverse barrier) produces higher gross per-event median expectancy than the benchmark 1:1 adverse target for the conditioned HA harami, in 23 cells over 15 instruments — robustly above the P11 quorum. ADV-EXTREME-raw is destructive (0 viable). ADV-EXTREME-rr1 ties the benchmark (0 WIN). The improvement comes from removing the stop entirely, not relocating it.

The r-expectancy divergence is the headline lesson: ADV-EXTREME-raw pushes r well below 0.50 yet expectancy is negative; ADV-NONE produces degenerate r=1.0 yet expectancy is positive. The median endpoint (P14) correctly captures what r misses. The lever is structural, not parametric — the raw/rr1 pair shows extreme-anchoring itself does not matter when R:R is equated.

The result is a characterization readout feeding the single 014-B G2; no candidate registration here.

## Registry Disposition

**registry: relevant characterization readout.** Family `CF-HA-HARAMI-001` stays **REGISTERED**, **OPEN**. Branches `/ADV-EXTREME` and `/ADV-NONE` stay **REGISTERED** — EXP-057 exercises both but does not promote any branch to screening candidate status (that is the 014-B G2 decision). The multiplicity-registry entry for HYP-010 (EXP-057) updated from PLANNED to CHARACTERISED — EVIDENCE_FOR (2026-06-16). 0 candidate slots consumed, 0 TEST reads spent, global holdout sealed; no `test-read-ledger.md` entry.

## Limitations

1. **Gross only.** No costs (spread, slippage, commission) modelled. A no-stop strategy may incur large adverse fills in practice.
2. **P15 fill approximation.** Path-ordered fills over 1-minute bars are a documented approximation of unobserved intrabar motion.
3. **DE30 truncated history.** Broker m1 history ends 2026-01-16; counts from own timeline, not span-comparable (VAL-003 disclosure).
4. **TRAIN-only.** No TEST or holdout validation. The EVIDENCE_FOR label reflects pre-registered mechanical criteria, not a generalization claim.
5. **ADV-NONE r = 1.0 is degenerate**, reported with caveat as planned.

## Implications

1. ADV-NONE is the strongest lever identified in the 014-B surface so far — removing the stop, not repositioning it.
2. Cost-model follow-up (EXP-061 or within G2) warranted before desk application — the negative timecap tail may be expensive in slippage.
3. Combined system (EXP-060) should test whether ADV-NONE + optimal favourable target (EXP-056) is additive or redundant.
4. Cross-instrument heterogeneity (7 cells where ADV-NONE does not beat benchmark) could be investigated.

## Artifacts

| Artifact | Path |
|----------|------|
| Scope | [scope.md](scope.md) |
| Analysis Plan | [analysis-plan.md](analysis-plan.md) |
| Code | [code/](code/) |
| Audit | [audit.md](audit.md) |
| Results | [results.md](results.md) |
| Governance (Pre-Exec) | [governance/pre-execution-review.md](governance/pre-execution-review.md) |
| Composition Readout | [results/composition_readout.json](results/composition_readout.json) |
| Run Metadata | [results/run_metadata.json](results/run_metadata.json) |
