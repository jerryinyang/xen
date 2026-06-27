# EXP-042 — Audit Report (Stage 5)

**Date:** 2026-06-11
**Artifacts audited:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`,
modified module `python/src/xen/avwap.py`, regression suite
`python/tests/test_avwap_band_param.py`, `results/` (4 files), `plots/` (3 files).
**Method:** independent re-implementation of the selection rule from
`band_scan.parquet`; full end-to-end regeneration of one cell from the raw
1-minute file; structural/integrity checks over all 255 rows.

## Verdict: PASS (no Critical, no Warning findings)

## Checks performed

### Holdout / TRAIN-only discipline (F01 fix verified) — PASS

- `load_train_slice` collects the first `train_rows` file-order rows with no
  full-file sort (row count from Parquet metadata via `select(pl.len())`);
  sortedness is hard-asserted on the collected TRAIN slice. Verified by
  source inspection and by reproducing the loader path in the spot-check.
- Boundary arithmetic recomputed for all 17 instruments from
  `run_metadata.json`: `train = floor(0.7 × floor(0.7 × total))` and
  `test = analysis − train` hold exactly (17/17).
- No `analysis70`/derivative file matched any source (17/17 full files);
  DE30 boundaries derive from its own truncated timeline
  (train_end_ts 2024-06-28, consistent with history ending 2026-01-16).
- TEST counts in the power statement are arithmetic only; no TEST bar
  content read anywhere.

### Selection-rule correctness — PASS

- Independent re-implementation (separate code path, `statistics.median`)
  over all 51 cells reproduces every `rank_table.csv` rank (0 mismatches),
  the median ranks {1.0: 2.0, others: 5.0}, the floor-imputed fractions
  (0.412/0.647/0.882/0.980/1.0), and the selection (band 1.0).
- Floor imputation (n_h8 < 30 → rank 5.0) and within-cell average-rank tie
  handling verified against the recorded table.
- Tie-break (wider band) not exercised by this data (unique minimum); its
  correctness is covered by the committed unit test.

### Forward-return math and denominators — PASS

- Full end-to-end regeneration of AUDJPY-1h @ band 1.0 from the raw
  1-minute file (loader → aggregator → generator → H=8 mean) reproduces the
  recorded row exactly: 69 events, n_h8 = 69, mean −2.844719 bps.
- Denominator monotonicity holds on all 255 rows
  (`n_events ≥ n_h4 ≥ n_h8 ≥ n_h16`; 0 violations) — consistent with
  events near the TRAIN end dropping out of longer horizons only.
- 4 zero-event band-cells exist; all carry NaN means (explicit, never
  averaged; floor rule absorbs them). No division by zero anywhere.
- Mean range across populated cells (−282 to +207 bps) is plausible for
  small-n gross domain-bar returns (extremes sit in n < 30 floored cells).

### Determinism and lineage — PASS

- Generator replay on identical input produced an identical event frame.
- `band_scan.parquet` SHA-256 matches `run_metadata.json`.
- Regression suite `python/tests/test_avwap_band_param.py` passes (5/5;
  project suite 20/20): baseline anchor (69 fixture events,
  multiplier-invariant in baseline mode), determinism, band-count
  monotonicity, bull/bear adverse-band arm semantics.

### Scope/plan compliance and code standards — PASS

- 0 statistical tests, exactly 3 scoped plots (all present), 0 new modules
  (one backward-compatible parameterization of `xen.avwap`).
- No extra analyses; grid, horizons, floor, `min_coverage`, domains all
  match the frozen predeclarations.
- DEGENERATE_FLOOR adjudication path implemented as amended: condition
  (>50% floor-imputed at every band ≥ 1.5) evaluates True on this data
  (0.647/0.882/0.980/1.0), and the emitted verdict is
  `BAND_SELECTED_DEGENERATE_FLOOR_PENDING_ADJUDICATION` — the band freeze is
  correctly withheld.
- Sequential state machine kept explicit; vectorized forward returns
  causally equivalent; no import-time side effects; tqdm on the outer loop;
  bounded memory (1-minute frame dropped per instrument).

## Findings

| ID | Severity | Finding |
|----|----------|---------|
| A1 | Info | The ~2 s wall time for 255 runs is legitimate: TRAIN slices are ~0.5–0.6M 1-minute rows per instrument, domain frames are 2.6k–10.4k bars, and the state machine is O(bars) per band. No work was skipped (spot-check reproduces results exactly). |
| A2 | Info | `n_h4 = n_h8 = n_h16 = n_events` in many cells simply means no event sits within 16 bars of the TRAIN end — expected for sparse populations. |
| A3 | Info | Band 1.0 is itself floor-imputed in 41% of cells; even the winning band's per-cell event rates are thin. This is interpretation-relevant (Stage 6) and central to the pending DEGENERATE_FLOOR adjudication, not a code defect. |

## Reproduction notes

All numerical checks in this audit are reproducible from the repo root
(`python/` venv): re-run the independent rule re-implementation against
`results/band_scan.parquet`, and the AUDJPY-1h end-to-end regeneration via
the loader/aggregator/generator path with `band_multiplier=1.0,
arm_at_adverse_band=True`.
