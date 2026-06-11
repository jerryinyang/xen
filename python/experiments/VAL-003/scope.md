# Experiment: VAL-003 - New-Universe Data Integrity Validation (INFR-002 Admission)

## Validation Lineage

`VAL-003` is a VAL-series rerun of **VAL-001 (rev. 3)** — the data-architecture
temporal-integrity validation that admitted the existing universe (BTCUSD,
EURUSD, USTEC, XAUUSD) — applied to the **new-universe** base files collected
by INFR-002 (Phase 010 design §5/C1; registry: Phase 010 Batch, INFR-002 row).

**Changes from source (VAL-001 rev. 3):**

1. **File discovery only.** Validation covers base 1-minute files under
   `data/timebars/` whose inferred instrument is **not** in the
   already-validated existing universe `{BTCUSD, EURUSD, USTEC, XAUUSD}`,
   excluding pre-sliced analysis exports (stems containing `analysis70`,
   `analysis_slice`, or `first70`). Exclusion-based discovery is deliberate:
   broker-specific symbol names for the index CFDs (e.g. `DE30` vs `GER40`)
   must not silently drop a collected file from validation.
2. **Identity everywhere else.** All check logic, negative controls, probe
   bounds (`PREFIX_WINDOW_ROWS=150_000`, head/middle/tail positions, fractions
   {0.34, 0.67, 0.95}, `DETERMINISM_ROWS=50_000`), source timeframes
   {1, 15, 60}, chart parameters (Line Break level 3, Renko ATR 14), output
   schema, and pass/fail semantics are byte-identical to the approved VAL-001
   rev. 3 suite. No check was added, removed, or re-tuned.

**Role (binding, per Phase 010 design §5/C1 and the registry):** the
new-universe data is admissible to experiments **only after** VAL-003 passes.
A FAIL or INCONCLUSIVE on any instrument blocks that instrument's admission
(not the others').

## Hypothesis

The INFR-002-collected new-universe base data preserves temporal alignment
across scoped time-bar, timeframe, and chart-type views — exhibiting no
future-timestamp or cross-view misalignment in any emitted row, and no
structural look-ahead in prefix-stability probes at the head, middle, and tail
of each analysis slice — when every derived view is generated only from the
first 70% of each chronologically ordered base dataset.

## Question

Can the new-universe data files (expected: GBPUSD, USDJPY, USDCHF, USDCAD,
AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, US500, US2000, DE30, JP225, under
whatever broker-specific names they land) be trusted to support future
research phases without detected temporal-alignment failures or look-ahead
contamination in any scoped row?

## Scope Boundaries

Identical to VAL-001 rev. 3 except instrument coverage:

- **Instruments**: all new-universe base files present in `data/timebars/` at
  run time (exclusion-based discovery, see Lineage §1). The run records which
  expected instruments are present; missing instruments are reported, not
  failed — collection may legitimately be partial when the validation runs.
- **Data views**: base 1-minute bars; 15-minute and 60-minute clock-aligned
  resamples; Line Break (level 3), Renko (ATR 14), Heiken Ashi from each
  scoped source timeframe.
- **Time range / holdout**: for each base file, sort by `CloseTime` and use
  only the first 70% as the analysis set. **The final 30% is sealed global
  holdout from first touch (Phase 010 design §5/C1) and is never collected or
  inspected.** The 70/30 train/test split inside the analysis set may be
  reported for auditability only.
- **Detection power**: every data-integrity and alignment check carries its
  VAL-001 rev. 3 negative control; an undetected control is a FAIL.
- **Exclusions**: no tick data, costs, strategy metrics, return analysis,
  parameter tuning, persistence of generated chart views, or any read of
  existing-universe files (already validated; nothing here re-opens them).

## Success / Failure Criteria

- **Evidence FOR (ADMIT)**: every discovered new-universe instrument passes
  all critical checks and every negative control is detected — same criteria
  as VAL-001 rev. 3.
- **Evidence AGAINST (BLOCK)**: any critical check fails for any scoped row of
  an instrument, or any negative control goes undetected. Admission is blocked
  per failing instrument.
- **Inconclusive**: a discovered file is unreadable, a required column is
  missing, or a chart/timeframe combination cannot emit rows (e.g. ATR warm-up
  exceeds available source rows). The affected instrument is not admitted.

## Complexity Budget

- Max statistical tests: 0
- Max visualisations: 2 (inherited VAL-001 plots)
- Max new code modules: 0 (suite reused; discovery-only patch)

## Execution Notes

- Collection precedes validation: `tools/ctrader-cli/run-infr002-collection.sh`
  (Mode=TimeBars, 02/01/2023 → registered end date). VAL-003 may be run after
  any subset of instruments lands and re-run as later instruments arrive;
  each run validates whatever is present.
- Run from `python/`: `python experiments/VAL-003/code/run_experiment.py`.
  Exit 0 = PASS, 1 = FAIL, 2 = INCONCLUSIVE.
- Results land in `python/experiments/VAL-003/results/` (checks, densities,
  negative controls, per-instrument summaries, run metadata) and
  `python/experiments/VAL-003/plots/`.
