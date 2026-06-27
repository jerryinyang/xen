# Experiment Report: VAL-003 — New-Universe Data Integrity Validation (INFR-002 Admission)

## Status: SUPPORTED (PASS) — new universe ADMITTED

**Date**: 2026-06-11
**Lineage**: VAL-001 rev. 3 suite, unchanged; file discovery scoped to
new-universe base files (existing universe and analysis-slice exports
excluded). See [scope.md](scope.md).
**Role**: admission gate for the INFR-002 collection (Phase 010 design §5/C1).

---

## Question

Can the INFR-002-collected new-universe 1-minute base data be trusted to
support future research phases without detected temporal-alignment failures or
look-ahead contamination in any scoped row?

## Result

**PASS.** Every discovered instrument passed every check; every negative
control was detected.

| Instrument | Checks | Failures | Inconclusive |
|---|---|---|---|
| AUDJPY, AUDUSD, DE30, EURJPY, GBPJPY, JP225, NZDUSD, US2000, US500, USDCAD, USDCHF, USDJPY | 98 each | 0 | 0 |
| GBPUSD | 196 (two files present at run time; see Disclosures) | 0 | 0 |
| SYNTHETIC (detection-power controls) | 24 | 0 | 0 |

- Negative controls: 24/24 detected (an undetected control would itself be a
  FAIL).
- Checks cover base time-bar integrity, 15m/60m resample agreement with the
  independent pandas oracle + golden fixture, Line Break / Renko / Heiken Ashi
  alignment, prefix-stability look-ahead probes (head/middle/tail), and
  deterministic regeneration — identical to VAL-001 rev. 3.
- Only the first 70% of each file was collected; the final 30% global holdout
  was never read.

## Collected data (realized coverage)

13 instruments, m1, collected via `tools/ctrader-cli/run-infr002-collection.sh`
(Mode=TimeBars). All start 2023-01-03 00:01. Row counts ~1.03–1.28M.

| Instrument | Rows | Data end (CloseTime max) |
|---|---|---|
| GBPUSD | 1,273,657 | 2026-06-11 00:37 |
| USDJPY | 1,274,170 | 2026-06-11 00:58 |
| USDCHF | 1,270,134 | 2026-06-11 00:58 |
| USDCAD | 1,269,870 | 2026-06-11 00:58 |
| AUDUSD | 1,270,486 | 2026-06-11 00:59 |
| NZDUSD | 1,271,158 | 2026-06-11 01:06 |
| EURJPY | 1,279,097 | 2026-06-11 01:06 |
| GBPJPY | 1,278,719 | 2026-06-11 01:07 |
| AUDJPY | 1,277,971 | 2026-06-11 01:07 |
| US500 | 1,187,767 | 2026-06-11 01:14 |
| US2000 | 1,208,112 | 2026-06-11 01:15 |
| JP225 | 1,157,882 | 2026-06-11 01:15 |
| **DE30** | **1,025,743** | **2026-01-16 13:11** ⚠ |

## Disclosures

1. **DE30 coverage truncation.** The broker's m1 history for DE30 ends
   2026-01-16 13:11 — roughly five months short of the other twelve
   instruments. Integrity over the available range is validated; the
   instrument's 70/30/holdout boundaries derive from its own realized
   timeline. Operator option (open): re-collect under an alternative broker
   symbol (e.g. DE40/GER40) before DE30's first analytical use; any
   replacement file requires a fresh VAL-003 run for that instrument.
2. **Duplicate GBPUSD file removed.** The pre-fix collection run (before the
   detach/poll/stop correction to the collection script) left an earlier
   GBPUSD file alongside the retry's file. Both were validated by this run
   (hence 196 GBPUSD checks) and verified row-for-row identical
   (`DataFrame.equals` → True, 1,273,657 rows, identical time range); the
   older file (`...003747.parquet`) was deleted 2026-06-11 after the
   validation run. `results/run_metadata.json` therefore lists one GBPUSD
   file more than remains on disk; the surviving file is fully covered by the
   PASS.

## Consequence

The new-universe data is **admitted** for use by future phases. The final 30%
of each file is sealed global holdout from first touch; the first 70% splits
70/30 TRAIN/TEST on the 1-minute-row timestamp convention. No experiment has
read any new-universe row. The new universe is the programme's confirmation
ground for TEST-capped existing-asset candidates; the confirmation design
(candidates, gates, any holdout sanction) is a future checkpoint.

## Artifacts

| Artifact | Path |
|----------|------|
| Scope | [scope.md](scope.md) |
| Code | [code/run_experiment.py](code/run_experiment.py) |
| Checks | [results/validation_checks.csv](results/validation_checks.csv) |
| Negative controls | [results/negative_controls.csv](results/negative_controls.csv) |
| Summaries | [results/instrument_summary.csv](results/instrument_summary.csv), [results/timeframe_summary.csv](results/timeframe_summary.csv), [results/chart_view_summary.csv](results/chart_view_summary.csv) |
| Run metadata | [results/run_metadata.json](results/run_metadata.json) |
