# Results: Experiment EXP-043

**Phase 011 Track A Substrate Readiness (Baseline Entry, 51 Cells)**
**Date:** 2026-06-11 · **Audit:** PASS (0 Critical / 0 Warning / 4 Info)

## Summary

The frozen baseline AVWAP event substrate is constructible, invariant-clean,
and deterministic across essentially the whole 17-instrument × {1h, 2h, 4h}
grid: **50 of 51 cells are READY**, with **zero invariant violations**
(across all events in all cells), **zero determinism failures** (full second
regeneration frame-identical everywhere; the audit's independent third pass
confirms two cells exactly), and **no substrate-level alert**. The single
NOT_READY cell — **JP225-2h** — fails only the frozen dropped-window-fraction
gate (0.2566 > 0.25); its events and invariants are otherwise clean. The
experiment verdict under the predeclared guide is **READINESS_DELIVERED**,
and the per-cell event-rate table now replaces the design §7.4 planning
figures as the authoritative power basis for Track B.

## Detailed Findings

### 1. Substrate readiness: 50/51 READY, no systematic failure

- **Observation**: every construction predicate (OHLC consistency, strict
  chronology, clock alignment, coverage bounds, TRAIN fence) passes on all 51
  cells except the JP225-2h dropped-fraction gate; all 7 invariant families
  show 0 violations on every cell; determinism passes 51/51.
- **Evidence**: `results/readiness_map.csv`, `results/per_cell_checks.parquet`
  (verdict re-derivation 0 mismatches — audit §Cross-table);
  `run_metadata.json` `substrate_alert: false` (frozen threshold: same
  invariant on ≥3 instruments, or any non-determinism — neither occurred).
- **Interpretation**: the frozen Phase-004 baseline generator and the
  clock-aligned aggregation transfer cleanly to the new universe and to the
  first-ever 2h domain. There is no evidence of a substrate or aggregation
  bug; gate G1 (design §8.2) can be applied per cell directly from the map.

### 2. JP225-2h NOT_READY — a coverage outcome, not a generator defect

- **Observation**: JP225-2h drops 25.66% of candidate 2h windows at
  `min_coverage=0.90`, breaching the frozen >25% FAIL threshold. Its 96
  events, 89 regimes, and all invariants are otherwise clean and recorded.
- **Evidence**: `power_statement.csv` row JP225-2h; audit Info-3 (independent
  recomputation reproduces 0.256632 exactly).
- **Interpretation**: JP225's session structure interacts worst with 2h
  clock-grid windows. Per design §8.2 the cell is excluded from Track B
  (16 instruments remain at 2h). Any revisit (e.g., a JP225-specific
  `min_coverage` study) is a new scoped experiment, not a rerun.

### 3. Event rates are scale-stable; realized counts supersede §7.4

- **Observation**: events per 1,000 TRAIN domain bars sit in a narrow band
  (16.5–34.0) across all domains and instruments — the bounce definition
  yields roughly constant per-bar event density regardless of timeframe.
  Realized TRAIN counts: 1h 151–273, 2h 86–143, 4h 32–86 per cell.
- **Evidence**: `power_statement.csv`; plot `event_rate_by_domain.png`;
  heatmap `train_event_count_heatmap.png`.
- **Interpretation**: 1h counts come in *below* the design's "~350–400"
  planning figure (151–273), while 4h counts (32–86) bracket "~90" at the low
  side. 2h delivers its intended middle ground (~2× the 4h counts). **No cell
  falls below the 30-TRAIN-event reporting floor** (min 32, JP225-4h), so
  Track B exit training is power-feasible everywhere, but 4h stability planes
  will be noisy in the thin cells (32–55 events for 11 of 17 instruments).
- **Power caveat (predeclared heuristic)**: projected TEST counts
  (`TRAIN × 30/70`, a uniformity heuristic, not an estimate) land at ~14–37
  events for 4h cells — most 4h cells project *below* 30 TEST events, which
  bears on eventual Track D candidate affordability (Track D verdicts need
  R1.2 small-n margins regardless).

### 4. 2h construction quality: clean for forex, flagged for indices

- **Observation**: 2h dropped fractions are 0.02–0.05 for forex; three index
  cells sit in the flagged 10–25% disclosure band — US2000-2h 0.103,
  DE30-2h 0.163, US500-2h 0.196 — all READY-eligible per the frozen rule.
  The 2h/1h bar-count ratio is 0.475–0.498 on every instrument (none outside
  the [0.45, 0.55] disclosure band).
- **Evidence**: `power_statement.csv` (`dropped_window_fraction`,
  `dropped_fraction_flagged`, `bar_ratio_2h_over_1h`); plot
  `dropped_fraction_2h.png`.
- **Interpretation**: 2h construction at `min_coverage=0.90` behaves; the
  retention loss concentrates where session gaps make 2h windows hard to
  fill. Audit Info-1 extends this: *4h* index retention (un-gated by
  predeclaration) reaches 0.20–0.30 (JP225 0.297, US500 0.286), above the
  old-universe historical range — Track B should treat index 4h bars as
  sitting on thinner window retention (partial windows understate High/Low).

### 5. DE30 disclosures travel with the data

- **Observation**: DE30 is READY on all three domains (47–189 TRAIN events)
  with its truncation column and power note on every row: projected counts
  optimistic by ~15–20% vs full-span instruments (history ends 2026-01-16).
- **Evidence**: `power_statement.csv` DE30 rows (`de30_truncated`,
  `power_note`); `run_metadata.json` P8 disclosure.

## Verdict

**READINESS_DELIVERED** (predeclared experiment-level criterion: the 51-cell
READY/NOT_READY map plus the event-rate/power table is produced).

- Cell-level: **50 READY, 1 NOT_READY (JP225-2h), 0 CONSTRUCTED_EMPTY**.
- Evidence AGAINST (substrate-level): **not triggered** — 0 determinism
  failures, no invariant violated on ≥3 instruments (none violated anywhere).
- G1 input: the 50 READY cells proceed to Track B, subject to the
  EXP-027-analog calibration coverage (a separate Track A item, not this
  experiment); JP225-2h is excluded with its failure recorded.

## Limitations

- This experiment certifies *construction, invariants, determinism, and event
  rates only* — it carries no information about edge, tradability, or exit
  quality (no return metric of any kind was computed, by scope).
- Projected TEST counts are a uniformity heuristic; regime-dependent event
  clustering can shift realized TEST counts materially in either direction.
- The 30-event floor is a TRAIN-side reporting convention; it does not
  guarantee TEST-side power for any future per-cell confirmation.
- DE30 figures derive from a ~5-months-shorter history; its disclosures must
  be carried into every downstream artifact that uses its cells.
- Determinism was verified within and across processes on the same machine
  and library versions; cross-platform reproducibility was not in scope
  (C#/Python parity is the EXP-029-analog, a separate Track A item).

## Alternative Explanations

- None bearing on the readiness verdict: the checks are exact predicates, and
  the audit independently reproduced them. The only judgment-bearing outcome
  (JP225-2h) follows a threshold frozen before any data contact.

## Recommended Next Steps

1. **EXP-027-analog (Track A, design §5.3)**: event-level inference-method
   calibration covering the 50 READY cells' event populations — required by
   G1 before Track B reads them.
2. **EXP-029-analog (Track A, design §5.3)**: C#/Python parity
   re-verification for the 2h domain and the new universe.
3. **Track B exit training (design §5.4)** on the READY map, using this
   power table (not §7.4) for per-cell expectations; treat thin 4h cells
   (32–55 events) and flagged index 2h cells with the disclosed caution.
4. Optional new scope if 2h JP225 matters to the portfolio: a JP225-specific
   2h construction study (`min_coverage` sensitivity) — explicitly out of
   scope here (no tuning of `min_coverage` permitted).
