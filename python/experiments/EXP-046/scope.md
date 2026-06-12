# Experiment: EXP-046 — Entry-Side Gross Screen (`/ALPHA` × `/MA-DOMAIN` OAT, 37-Cell Grid)

**Phase:** 012 (`docs/experiments-docs/checkpoints/2026-06-12-012-entry-side-gross-screen/design.md`)
**Registry:** `CF-AVWAP-001/ENTRY-GROSS` — 0 slots, 0 TEST reads (TRAIN-only diagnostic)
**Predeclarations:** all binding values frozen in the Phase 012 `D0-predeclarations.md` (RATIFIED 2026-06-12, G0 PASS); this scope restates them and adds nothing data-derived.

## Hypothesis

At least one predeclared one-at-a-time entry-parameter variant of the frozen
AVWAP bounce substrate — tick-volume exponent α ∈ {0.0, 0.375, 1.0} or MA
pair ∈ {(10,25), (40,100), (60,150)} — raises TRAIN gross per-event
expectancy at H=8 domain bars to ≥ the frozen per-cell cost floor + 1×SE,
with positive gross at H=4 and H=16, in ≥5 cells spanning ≥3 instruments of
the 37-cell COVERED grid.

## Question

Can any single entry-parameter lever raise the gross bounce edge enough to
pay frozen CONSERVATIVE costs somewhere meaningful — before any net/exit
machinery is rebuilt?

## Scope Boundaries

- **Data Views**: 1-minute time bars aggregated to 1h/2h/4h domain bars via
  the frozen `xen.bar_aggregator` conventions (2h: `period_minutes=120`,
  `min_coverage=0.90` — Phase 011 P7). AVWAP bounce events via the frozen
  `xen.avwap` machinery, parameterized for α and MA inputs (defaults must
  reproduce the Phases 004–011 baseline bit-for-bit — Phase 012 P8).
- **Parameters** (all frozen at D0):
  - Variants (7 incl. baseline, OAT around baseline α=0.75, MA=(20,50)):
    α ∈ {0.0, 0.375, 0.75, 1.0} at MA=(20,50); MA ∈ {(10,25), (20,50),
    (40,100), (60,150)} at α=0.75. All other substrate elements frozen:
    arm/trigger at the AVWAP line, MAD-band definition, anchor rule,
    pyramid handling.
  - Reference horizons H ∈ {4, 8, 16} domain bars; **H=8 binding**.
  - Cost floor: `floor_i,d = RT_i + financing_i × days(8, d)`,
    `days(H,d) = H × hours(d)/24` → 1/3, 2/3, 4/3 days on 1h/2h/4h; RT and
    financing verbatim from the Phase 011 P2 CONSERVATIVE table.
  - Clearance margin: gross(H=8) ≥ floor + 1×SE (bootstrap SE of the cell's
    H=8 gross mean, frozen EXP-027 resampling layer, descriptive).
  - Event floor: ≥30 TRAIN events per cell×variant (below → BELOW_FLOOR,
    descriptive only, ineligible to clear).
- **Instruments / cells**: the Phase 011 **37-cell COVERED grid** verbatim
  (EXP-044 `coverage_map.csv` is the authoritative cell list). The 14
  excluded cells (JP225-2h readiness; 13 calibration NOT_COVERED) remain
  excluded and are not loaded.
- **Time range**: TRAIN only — first 70% of the first-70% analysis set per
  instrument, R1.3 1-minute-row timestamp boundary (`train_end_ts`),
  identical to EXP-043/044/045. TEST rows are never read; **0 TEST-read
  ledger entries by construction** (prior counted reads per stratum:
  EURUSD-4h 2 [AT CAP], USTEC-4h 1, XAUUSD-4h 1, all others 0 — disclosed,
  untouched).
- **Global holdout**: the final 30% of each instrument file is never
  loaded, inspected, or used.
- **Look-ahead bias prevention**: events use only data at or before the
  event timestamp; generators run sequentially; temporal ordering by
  `CloseTime`.
- **Real-price outcome discipline**: all gross returns from real domain-bar
  OHLC prices, direction-signed. No synthetic prices in scope.
- **Exclusions**: exit training or selection; any net expectancy, cost- or
  financing-adjusted return columns (the floor enters only as a comparison
  threshold against gross); structural `/ENTRY` arm/trigger changes;
  `/ALPHA`×`/MA-DOMAIN` combinations; grid extension; TEST/holdout contact;
  5m; the 14 excluded cells; cross-instrument pooling for clearance
  verdicts; any binding p-value or significance claim.

## Success / Failure Criteria

Per cell×variant, a cell **CLEARS** iff (all four, mechanical):
1. gross(H=8) ≥ floor + 1×SE;
2. gross(H=4) > 0 and gross(H=16) > 0;
3. ≥30 TRAIN events;
4. determinism replay passes for that cell×variant event set.

Phase-level (G1, adjudicated in the checkpoint's `G1-gate-review.md`, not
inside this experiment):
- **ENTRY_GROSS_VIABLE (Evidence FOR)**: ≥1 non-baseline variant clears in
  ≥5 cells spanning ≥3 distinct instruments.
- **ENTRY_GROSS_FLAT (Evidence AGAINST)**: no non-baseline variant meets
  the composition threshold. (A complete, routable outcome → substrate
  pivot per the operator pre-commitment.)
- **Inconclusive**: only if integrity failures (determinism, baseline
  reconciliation, event-floor collapse across most of the grid) prevent the
  mechanical count — partial-grid results do not soften the threshold.

Integrity anchor (blocking, three legs per cell on the regenerated baseline
events): (1) event-count identity vs EXP-043 realized counts; (2) FH net
mean at θ ∈ {4,8,16} vs the persisted EXP-045 `score_curves.csv` values,
recomputed under EXP-045's own full-population/forced-clip conventions
identically on both sides (the only persisted external anchor); (3) an
internal cross-check that the binding gross/evaluable code path matches an
independently indexed recomputation. Tolerance float-precision (1e-9 bps);
any discrepancy is a blocking integrity finding, not a result, and
suppresses the mechanical G1 readout.

## Metric Denominators and Zero-Baseline Behavior

- Denominator: per-event — each cell×variant×horizon mean is over that
  cell×variant's TRAIN events (count always reported alongside).
- Event populations differ across variants by construction (MA changes move
  anchors; α changes move the AVWAP line). No variant-vs-baseline matched
  comparison is made; each variant is compared only to the fixed cost
  floor. No ratio/percentage-improvement metrics; no zero baselines arise.
- Cells with zero events under a variant report `n=0, BELOW_FLOOR` (no NaN
  propagation; means undefined → not computed).

## Complexity Budget

- Max statistical tests: 0 binding (bootstrap SEs are descriptive; the G1
  count is mechanical, not a test)
- Max visualisations: 4 (two gross-vs-floor margin heatmaps, one per variant
  axis at the binding horizon; horizon-robustness panel; event-count map —
  reconciliation is reported as CSV only)
- Max new code modules: 1 (entry-variant sweep utilities; the `xen.avwap`
  α/MA parameterization extension lives in the existing module behind
  default-preserving parameters)

## Data Requirements

- 17 instrument 1-minute Parquet files (only instruments appearing in the
  37-cell grid are loaded; only TRAIN file-order rows collected, EXP-045
  F01 pattern: row count from Parquet metadata, first `0.49N` rows
  file-order, sortedness re-asserted on the collected slice).
- Domain aggregation 1h/2h/4h per frozen conventions; DE30 carries its
  truncated-history disclosure verbatim in every artifact.
- **P8 gate (precondition for any TRAIN read):** the Phase 011 regression
  suite extended with baseline-fixture invariance at default α/MA,
  parameter-effect smoke tests, and determinism replay — all green first.

### Standard Loading Pattern

Per instrument (lazy, TRAIN-only, no full-file sort — EXP-045 F01 pattern):

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob(f"timebars/timebars_{symbol}_*.parquet"))[-1]

total_rows = pl.scan_parquet(path).select(pl.len()).collect().item()
train_rows = int(int(total_rows * 0.7) * 0.7)
bars = pl.scan_parquet(path).slice(0, train_rows).collect()
# assert sorted by CloseTime (validated source order, VAL-001 rev. 3 / VAL-003)
```

## Suggested Direction

One sweep loop: variant (7) × instrument×domain cell (37) → generate events
on TRAIN, record n, determinism hash, gross at H ∈ {4,8,16}, bootstrap SE
at H=8, floor, margin, CLEAR/NO_CLEAR/BELOW_FLOOR. Single results table +
the four plots; baseline row reconciled against EXP-045 gross proxy before
any non-baseline row is interpreted. `tqdm` over the outer variant×cell
loop; no per-helper printing.
