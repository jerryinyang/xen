# Experiment: VAL-001 - Data Architecture Temporal Integrity Validation

## Validation Lineage

`VAL-001` is a baseline infrastructure validation, not a rerun of a prior
experiment. There is no source EXP because no experiment has been registered in
`python/experiments/INDEX.md` yet.

Changes from source EXP: not applicable. This task validates whether the
available data architecture is safe enough to support the next research thesis.

### Pre-execution revision (rev. 2)

Before first execution, an independent review found that the original checks
largely passed *by construction*: the no-look-ahead check re-ran the same
generator loop it was validating, and the resample check compared
`aggregate_ohlc` against a near-verbatim copy of itself. Neither could fail for
the failure mode it claimed to guard against, and the suite had no negative
control proving any check could detect a fault. This revision (still
pre-execution, no results produced) strengthens the methodology so that a PASS
is tangible evidence:

1. **No-look-ahead** is tested by **prefix stability** — an independent property
   comparing two different inputs (full series vs. a truncated prefix), not a
   re-run of the same code.
2. **Resampling correctness** is tested against an **independent oracle**
   (pandas right-closed/right-labelled resampling) plus a hand-anchored golden
   fixture, not a reimplementation of the production bucket formula.
3. **Negative controls** inject look-ahead, future timestamps, unmapped
   timestamps, and corrupted real prices, and require every corresponding check
   to flip to FAIL. An undetected negative control is itself a FAIL.
4. Comparisons are **vectorised** (Polars joins / `equals`, pandas C-resample);
   look-ahead and determinism probes run on a bounded leading window instead of
   pure-Python million-row loops.

### Post-completion revision (rev. 3)

VAL-001 was first executed and approved under rev. 2. A post-completion review
found three detection-power gaps. By explicit governance decision the experiment
is re-run in place (same ID, rev. 3) rather than as a new VAL; pre- and
post-execution governance still apply.

1. **Detection-power coverage (gap 1)** — rev. 2 carried negative controls for
   only 8 of its check types; the base time-bar integrity checks (null /
   strictly-increasing / unique `CloseTime`, OHLC validity, OHLC nullity) and
   several chart/HA/resample alignment sub-checks had no evidence they can fail.
   rev. 3 adds a negative control for every data-integrity and alignment check,
   so each PASS is backed by a matching injected-fault detection. Pure
   availability/IO defensive checks (Parquet readability, file presence,
   non-empty analysis slice) are exercised by their own construction and are
   named as explicit exclusions rather than left silently unguarded.
2. **Determinism control (gap 2)** — rev. 2's determinism control only proved
   `DataFrame.equals` returns False for two different frames; it never ran a
   non-deterministic generator through the determinism check. rev. 3 routes an
   actually non-deterministic generator (output differs between regenerations of
   identical input) through `determinism_failures`, so the control tests the
   check, not the comparison primitive.
3. **Look-ahead coverage (gap 3)** — rev. 2 probed prefix stability only on the
   leading window of each slice. rev. 3 probes head, middle, and tail windows
   with additional cut points, and the hypothesis no longer claims structural
   no-look-ahead for "any scoped row": that claim is scoped to the probe
   windows, while full-output timestamp alignment remains checked on every
   emitted row.

A separate manual review compared the Line Break and Renko implementations
against their `architecture.md` algorithm specifications (gap 4) and found no
correctness defect. Automated generator value-correctness remains out of scope:
the generators are deterministic and the run is reproducible, so downstream
consumers can replicate any result rather than depend on a value oracle here. No
new positive value-correctness check is added.

## Hypothesis

The available Xen data architecture preserves temporal alignment across scoped
time-bar, timeframe, and chart-type views — exhibiting no future-timestamp or
cross-view misalignment in any emitted row, and no structural look-ahead in
prefix-stability probes positioned at the head, middle, and tail of the analysis
slice — when every derived view is generated only from the first 70% of each
chronologically ordered base dataset.

## Question

Can the current data layer be trusted to support future thesis work without
detected temporal alignment failures or look-ahead contamination in any scoped
row?

## Scope Boundaries

- **Data Views**: Base 1-minute time bars; clock-aligned 15-minute and
  60-minute OHLC resamples; Line Break, Renko, and Heiken Ashi views generated
  from each scoped source timeframe.
- **Parameters**: Line Break `level=3`; Renko `atr_period=14`; Heiken Ashi has
  no parameter; timeframe periods are `1`, `15`, and `60` minutes.
- **Instruments**: All available base Parquet files in `data/timebars/` at run
  time, expected to cover BTCUSD, EURUSD, USTEC, and XAUUSD.
- **Time range**: For each base file, sort by `CloseTime` and use only the first
  70% as the analysis set. The validation may report the analysis-set start and
  end timestamps but must not collect or inspect rows past the 70% cutoff.
- **Global holdout**: The final 30% of each chronologically ordered base file is
  excluded from all validation checks and derived-view generation.
- **Train/test split**: A 70/30 chronological split inside the analysis set may
  be reported for auditability, but no model training, parameter selection, or
  outcome optimization is performed.
- **Temporal ordering**: Use `CloseTime` for time bars and resampled timeframes.
  Use `SourceCloseTime` for Line Break and Renko chart-type rows. Use
  `CloseTime` for Heiken Ashi rows.
- **Look-ahead bias prevention (prefix stability)**: For each chart-type
  generator, `generate(source[:k])` must be an exact prefix of
  `generate(source)` at several cut points `k`. A generator that consults any
  future source row produces different rows near the cut, so this property
  falsifies look-ahead by comparing two genuinely different inputs. The probe is
  run on bounded windows positioned at the **head, middle, and tail** of each
  analysis slice (not only the leading rows), each at multiple cut points, so
  positional coverage spans the slice rather than its prefix alone. Full-output
  timestamp-alignment checks (no future `SourceCloseTime`, mapping to source,
  `CloseTime == SourceCloseTime`) still run on every emitted row. Streaming /
  batch API equivalence is already covered by the `xen` package unit tests and
  is not re-run at experiment scale. Determinism (identical output on
  re-generation) is checked separately.
- **Resampling ground truth**: Timeframe resamples are validated against an
  independent pandas resampling oracle and a hand-anchored golden fixture, never
  against a copy of the production bucket logic.
- **Detection power (negative controls)**: Every data-integrity and alignment
  check must have at least one matching negative control: the validation injects
  a deliberately corrupted input and requires that exact check function to report
  a failure. This covers base time-bar integrity (null / non-increasing /
  duplicate `CloseTime`, invalid OHLC, null OHLC), resample oracle agreement and
  the resample output-side checks (future timestamp, strict source-bar count,
  unique `CloseTime`), the sparse-chart alignment checks (missing / null /
  future source time, `CloseTime != SourceCloseTime`, negative and
  first-event-zero `SourceCount`), Heiken Ashi real-price and row/source-count
  checks, the chart schema check, an actually non-deterministic generator routed
  through the determinism check, and the look-ahead generator routed through
  prefix stability. A negative control that is not detected is recorded as a
  FAIL. Pure availability/IO defensive checks (Parquet readability, file
  presence, non-empty analysis slice) are exercised by their own construction and
  are not assigned controls.
- **Duplicate-source event denominator**: Line Break and Renko checks count every
  emitted chart row as a row-level validation denominator. Distinct
  `SourceCloseTime` counts are reported separately. Same-source duplicate rows
  are not silently deduplicated. A `SourceCount` of 0 is legitimate for a
  same-source duplicate brick; only the first event at each `SourceCloseTime`
  must consume at least one source bar, and counts are never negative.
- **Real-price outcome discipline**: No strategy P&L, signal return, excursion,
  stop, or target metric is in scope. Heiken Ashi and Renko construction prices
  are validated only as data-layer outputs, not tradable outcomes.
- **Exclusions**: No tick data, bid/ask spread, trading costs, strategy
  backtests, return forecasting, parameter tuning, randomized tests, or
  persistence of generated chart-type datasets.
- **Checkpoint alignment**: No active checkpoint `design.md` exists. This
  validation is a thesis-readiness gate before proposing a new research
  checkpoint.

## Success / Failure Criteria

- **Evidence FOR**: Every scoped instrument, source timeframe, and chart-type
  view passes all critical checks AND every negative control is detected:
  - base time bars have required columns, valid OHLC relationships, no null
    governing timestamps, and strictly increasing `CloseTime`;
  - 15-minute and 60-minute resamples match the independent pandas oracle
    row-for-row (timestamps and OHLC), and the golden fixture matches a
    hand-computed window;
  - Line Break and Renko rows have non-null `SourceCloseTime` values present in
    the scoped source timeframe, never beyond the analysis-set maximum
    timestamp, with `CloseTime == SourceCloseTime` and valid `SourceCount`;
  - Heiken Ashi rows preserve real OHLC values at the same source `CloseTime`;
  - every chart-type generator satisfies prefix stability (no look-ahead) at the
    head, middle, and tail probe windows, and deterministic regeneration;
  - every data-integrity and alignment check has at least one negative control,
    and every negative control is detected (the corresponding check reports a
    failure on the corrupted input).
- **Evidence AGAINST**: Any critical check fails for any scoped row — timestamp-
  order violations, OHLC integrity failures, resample disagreement with the
  oracle, missing/future/unmapped source-timestamp mappings, a prefix-stability
  divergence (look-ahead), non-deterministic regeneration — OR any negative
  control that the suite fails to detect (which would mean a real fault could
  pass unnoticed).
- **Inconclusive**: A scoped base file is unreadable, a required column is absent
  in a way that prevents validation from running, or a chart-type/timeframe
  combination has insufficient source rows to emit any row-level chart output
  (e.g., a high source timeframe shorter than the Renko ATR warm-up).

## Complexity Budget

- Max statistical tests: 0
- Max visualisations: 2
- Max new code modules: 0

## Data Requirements

The implementation must load each base file with lazy Polars scans, select only
required columns, sort by `CloseTime`, compute the 70% analysis cutoff, and
collect only the analysis slice. Derived timeframes and chart-type views must be
generated from that collected analysis slice only.

### Standard Loading Pattern

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob("timebars/timebars_*.parquet"))[-1]

scan = pl.scan_parquet(path).sort("CloseTime")
total_rows = int(scan.select(pl.len()).collect().item())
analysis_cutoff = int(total_rows * 0.7)
analysis_set = scan.slice(0, analysis_cutoff).collect()
```

## Suggested Direction

Implement deterministic validation checks that produce machine-readable result
tables and two compact plots: one for validation status by view and one for
chart-type event density by instrument/timeframe. Do not run the validation
inside the research pipeline; stop after pre-execution governance approval.
