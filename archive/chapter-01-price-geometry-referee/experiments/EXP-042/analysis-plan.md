# EXP-042 — Analysis Plan (Track A0 Band-Selection Scan)

**Scope:** `python/experiments/EXP-042/scope.md` (Stage 1, 2026-06-11)
**Mode:** descriptive, TRAIN-only, 0 statistical tests; mechanical predeclared
selection rule (design §5.2 + D0 P3). Nothing in this plan is data-dependent;
all parameters are frozen by G0.

## 1. Question

Apply the frozen rank rule over 5 bands × 51 cells (17 instruments × {1h, 2h,
4h}, TRAIN only) and report: (a) the selected global band, (b) the selected
band's per-cell event rates and projected TEST counts (power statement).

## 2. Method selection

| Step | Method | Why sufficient | Simpler alternative considered |
|---|---|---|---|
| Per-cell measurement | Summary statistics only: event count `n(b,cell)` and arithmetic mean of direction-signed log forward return (bps, real domain Close) at H ∈ {4, 8, 16} | The selection rule consumes only the H=8 mean and the event count; no uncertainty quantification is scoped (CIs explicitly excluded by design §5.2) | None simpler exists |
| Band selection | Mechanical rank aggregation: within-cell rank at H=8 (rank 1 = best, average-rank on exact ties within a cell), floor imputation (`n < 30` at the H=8 denominator → worst rank 5), median rank across 51 cells, wider-band tie-break | Predeclared, scale-free, unit-free; rationale fixed in design §5.2 | Raw cross-cell median of bps (rejected at design time — volatility-dominated) |
| Power statement | Deterministic projection: TRAIN event rate × (TEST 1-minute-row count / TRAIN 1-minute-row count), per cell, selected band only | Row counts are metadata of the split boundary; no TEST bar content is read | — |

**Assumptions and fit:** no distributional assumptions are made anywhere —
means and ranks only. Time-ordering is respected by construction (forward
windows only, contained in TRAIN). The known weakness — per-cell means at
small n are noisy — is handled by the floor rule, not by inference, and is
acceptable because the output is a single global selection averaged over 51
cells, not a per-cell claim.

## 3. Computation specification

Per instrument (tqdm outer loop), per domain, per band:

1. Lazy-scan newest 1-minute parquet, sort `CloseTime`, compute
   `train_end_ts` (70% × 70% 1-minute-row boundary, R1.3); slice **before**
   collect; TEST/holdout rows never materialized (TEST row *count* is taken
   from the boundary arithmetic only).
2. Aggregate to domain bars (`aggregate_ohlc`, `min_coverage=0.90`).
3. Run the frozen EXP-020 substrate state machine with band multiplier b;
   collect event trigger bar indices/timestamps (pyramid events independent,
   identical convention for every band).
4. For each H ∈ {4, 8, 16}: forward return = `10000 × direction ×
   ln(Close[t+H] / Close[t])` on real domain Close, only for events with
   `t+H` inside the TRAIN bar range; record per-horizon denominator.

Then assemble the rank table and apply the selection rule exactly as scoped.

## 4. Plots (≤3, budget-compliant; inputs returned from the analysis pass)

1. **Rank heatmap** — 51 cells × 5 bands, cell rank at H=8, floor-imputed
   cells hatched/annotated. Answers: is the selection broad-based or driven
   by a subset?
2. **Event count vs band** — per domain, lines per instrument (log y).
   Answers: how fast does the floor bite as the band widens?
3. **Mean gross bps vs band by domain** — per-domain median (across
   instruments) of cell means at each horizon. Answers: does wider band →
   larger per-event gross, as the design conjectures? (Context only; not a
   selection input.)

## 5. Interpretation criteria (fixed before results)

- **BAND_SELECTED:** the rule yields a unique band; report it with the full
  rank table and power statement. The selection is *adopted regardless of
  which band wins* — including 1.0 (then `/BAND` consumes no slot and the
  prior power analyses remain partially relevant; still re-stated from this
  scan).
- **DEGENERATE_FLOOR disclosure:** if > 50% of cells are floor-imputed at
  every band ≥ 1.5, state it prominently; selection still stands.
- No inconclusive verdict exists; no re-ranking, re-parameterization, or
  grid extension after results are seen. Per-cell means are never quoted as
  edge claims (gross, descriptive, selection-internal only).

## 6. Implementation safety constraints (for experiment-developer)

- Holdout/TEST: lazy slicing by 1-minute-row count before collect; assert
  the last loaded 1-minute `CloseTime` ≤ `train_end_ts`; record boundaries
  in `run_metadata.json`.
- Temporal: sort by `CloseTime` before splitting; event alignment by bar
  index *within a single domain frame only* (cross-view alignment not in
  scope); forward windows bounded by the TRAIN bar range (no spill).
- Denominators: per-horizon per-band per-cell event counts written
  explicitly; means emitted only where n ≥ 1; floor evaluated on the H=8
  denominator. No division by zero; no silent NaN propagation (qualifying-
  event masks explicit).
- Determinism: substrate is deterministic (no randomness anywhere in this
  scan); emit a content hash of `band_scan.parquet` in metadata.
- Bounded iteration: 17 × 3 × 5 = 255 substrate runs; tqdm on the
  instrument loop with domain/band postfix; concise logging (helpers return
  data, no helper-level prints).
- Vectorization: bar aggregation and forward-return computation vectorized
  (Polars/NumPy); the substrate state machine remains an explicit sequential
  loop (causal semantics must not be vectorized away).
- Memory: process one instrument at a time; never hold all instruments'
  1-minute frames simultaneously; plot inputs are the bounded aggregate
  tables, no reloads.

## 7. Outputs

As scoped: `results/band_scan.parquet`, `results/rank_table.csv`,
`results/power_statement.csv`, `results/run_metadata.json`, plots under
`plots/`.

## 8. Budget check

0 statistical tests (✓ scope), 3 plots (✓ ≤3), ≤1 new module — prefer
extending the existing substrate generator with a band-multiplier parameter
if it is not already parameterized (✓).
