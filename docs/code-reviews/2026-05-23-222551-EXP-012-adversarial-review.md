# Adversarial Review: EXP-012 — ICT Data Readiness and Feasibility

**Timestamp:** 2026-05-23T22:25:51  
**Reviewer role:** Empirical study + code correctness  
**Artifacts reviewed:**
- `python/experiments/EXP-012/scope.md`
- `python/experiments/EXP-012/analysis-plan.md`
- `python/experiments/EXP-012/governance/pre-execution-review.md`
- `python/experiments/EXP-012/code/run_experiment.py`
- `python/experiments/EXP-012/results/results.json`
- `python/experiments/EXP-012/results/numerical_summary.txt`
- `python/experiments/EXP-012/results/inventory_summary.csv`
- `python/experiments/EXP-012/results/macro_family_coverage_summary.csv`
- `python/experiments/EXP-012/results/macro_window_coverage_summary.csv`
- `python/experiments/EXP-012/results/missing_bar_summary.csv`
- `python/experiments/EXP-012/results/active_session_summary.csv`
- `docs/experiments-docs/checkpoints/2026-05-23-003-ict-one-setup-timebar-validation/design.md`

**Active review lens:** Data integrity > statistical methodology > code correctness  
**Content type:** Empirical data-readiness study with accompanying analysis code

---

## Findings

```json
[
  {
    "id": "F01",
    "severity": "Major",
    "title": "INCONCLUSIVE verdict has no downstream decision rule for EXP-013+",
    "evidence": "scope.md: 'EXP-013 and all later macro-window or cost-sensitive experiments must use the timestamp, coverage, and cost-proxy decisions recorded here without changing them after seeing outcomes.' design.md gate: 'Data readiness gate: Verify timestamp coverage, NY-time conversion feasibility, active-session definitions, missing-bar behaviour, and spread/slippage availability.' results.json: verdict = INCONCLUSIVE.",
    "impact": "The experiment is the hard gate for Phase 003. An INCONCLUSIVE verdict is a defined outcome category, but neither the scope, the analysis plan, nor the design.md prescribes a decision procedure for this case: does EXP-013 proceed on the three passing instruments only? Is USTEC excluded from all downstream experiments or just those requiring PM coverage? Does the INCONCLUSIVE gate require human sign-off before EXP-013 is scoped? Without a declared policy, downstream experiments may silently include USTEC (risking inclusion of a sub-threshold instrument) or silently drop it (losing declared H1-H6 coverage). Either choice made ad-hoc after seeing results constitutes undocumented post-hoc selection.",
    "fix": "Amend the results or a governance addendum to declare, before EXP-013 is scoped, one of three explicit policies: (a) proceed with EURUSD/XAUUSD/BTCUSD only and document USTEC's exclusion rationale, (b) proceed with all four instruments and carry USTEC's PM coverage caveat forward as a disclosed limitation, or (c) require a targeted USTEC PM data investigation before EXP-013. The choice itself is a research decision; the absence of a choice is the defect."
  },
  {
    "id": "F02",
    "severity": "Major",
    "title": "BTCUSD train-test coverage gap (88% vs 99.5%) is unacknowledged and may indicate temporal data heterogeneity",
    "evidence": "macro_family_coverage_summary.csv: BTCUSD Train AM = 0.884, Train PM = 0.886; BTCUSD Test AM = 0.997, Test PM = 0.995. No comment on this discrepancy appears in numerical_summary.txt, results.json, or governance/pre-execution-review.md.",
    "impact": "A ~11 percentage-point gap between the training and test coverage epochs for BTCUSD is the largest cross-segment discrepancy in the dataset. It is large enough to indicate that earlier BTCUSD data (approximately 2023-01 to mid-2024, which comprises the training set) consistently had missing macro-window bars that the later test period (mid-2024 to 2025-06) did not. For EXP-013 (H1 macro-window characterization), this means the statistical properties of macro-window bar sequences are not stationary across the train/test boundary for BTCUSD. Event-level statistics on, for example, range or sweep frequency computed on the training set will be systematically diluted by missing bars relative to the test set. This could cause spurious train-test divergence that researchers attribute to signal variation rather than data quality variation. The BTCUSD family-level pass verdict (88% > 80%) conceals this temporal instability.",
    "fix": "Add an explicit note in numerical_summary.txt and results.json flagging the train/test coverage split for BTCUSD. In EXP-013's scope, require any BTCUSD statistics to be reported separately by segment (train/test) so that the coverage differential can be visually confirmed rather than averaged away."
  },
  {
    "id": "F03",
    "severity": "Major",
    "title": "Per-window coverage below 80% threshold is masked by family-level aggregation that passes — downstream window-level experiments will face sub-threshold coverage",
    "evidence": "macro_window_coverage_summary.csv: XAUUSD Test PM2=0.7964, Test PM3=0.7964, Test PM4=0.7964, Train PM4=0.7968. USTEC Test PM1-PM4=0.7848, Train PM4=0.7953. macro_family_coverage_summary.csv: these instruments pass the 80% family threshold (XAUUSD Test PM=0.8024, USTEC Train AM=0.8299). scope.md uses the family-level threshold.",
    "impact": "EXP-013 (macro-window characterization) will produce event samples from individual macro windows, not family aggregates. XAUUSD PM2-PM4 and USTEC PM1-PM4 all fall below the 80% threshold at the individual window level in at least one segment. Event studies on PM2-PM4 for these instruments will be underpowered relative to the threshold that was used to declare data adequacy. For USTEC, all PM windows in Test are at 78.5% — meaning roughly 1 in 5 expected PM events will simply not have data. This will structurally suppress PM-window signal estimates for USTEC and produce an asymmetric comparison between AM (fully populated) and PM (substantially missing) windows. Downstream researchers relying on the SUPPORTED/INCONCLUSIVE verdict without inspecting per-window coverage will not anticipate this asymmetry.",
    "fix": "Add a per-window coverage table to numerical_summary.txt that explicitly flags windows below the 80% threshold. Document in results.json which individual windows are below-threshold and for which segments. EXP-013's scope should predeclare that instruments with below-threshold per-window coverage must report per-window sample sizes before interpreting any PM window statistics."
  },
  {
    "id": "F04",
    "severity": "Minor",
    "title": "Active session output trivially reports 00:00–23:59 for all instruments, providing no actionable session-boundary information",
    "evidence": "numerical_summary.txt: 'EURUSD Test: median NY session 00:00-23:59 across 222 dates', 'USTEC Test: median NY session 00:00-23:59 across 223 dates'. active_session_summary.csv: MedianFirstMinute=0, MedianLastMinute=1439 for all instruments in both segments.",
    "impact": "The active-session summary is one of the declared deliverables in the analysis plan ('observed active-session coverage by instrument'). A uniform 00:00-23:59 result means the summary correctly confirms that FX and CFD instruments provide data across all NY calendar hours, but it provides zero boundary information for EXP-013 session-filter decisions. The design.md phase gate specifically lists 'active-session definitions' as a required deliverable. Researchers planning EXP-013 who rely only on the numerical summary will find no guidance on whether, for example, USTEC has meaningful pre-market coverage before 09:30 ET, or when XAUUSD's typical session gaps occur. The hourly_session_presence.csv contains the granular data but is not surfaced in any human-readable narrative output.",
    "fix": "Add a brief per-instrument summary of hourly presence to numerical_summary.txt (e.g., 'USTEC: hours 09–16 present in 95%+ of days; hours 17–08 present in 40–60% of days'). This does not require any code change to the core experiment, only an additional write step in write_outputs that summarises hourly_session_presence at the ≥90%-presence level."
  },
  {
    "id": "F05",
    "severity": "Minor",
    "title": "CloseTime-based macro-window boundary assignment not documented as an explicit downstream assumption",
    "evidence": "run_experiment.py:128–139: macro_window_expr() uses NYMinuteOfDay derived from CloseTimeNY. scope.md: 'Look-ahead bias prevention: Features and events use only bars with CloseTime at or before the event timestamp.' No explicit statement that window membership is derived from CloseTime rather than OpenTime.",
    "impact": "A 1-minute bar with CloseTime = 07:50 NY represents a bar that opened at 07:49 and closed at 07:50. The macro_window_expr assigns this bar to AM1 (07:50–08:10) because its CloseTimeNY minute equals the window StartMinute. In practice this means the 'first bar of AM1' actually contains price action from 07:49–07:50, one minute before the window nominal start. For EXP-013 (and especially EXP-015/EXP-016 sweep studies), researchers building on this convention without explicit documentation may incorrectly assume the first bar of AM1 opens at 07:50, leading to a one-bar offset when aligning with independently computed macro-window logic or ICT reference definitions. The assumption is internally consistent within the codebase but is not surfaced in any output artifact.",
    "fix": "Add one sentence to numerical_summary.txt and results.json stating: 'Macro window membership is assigned by CloseTimeNY: a bar with CloseTime = 07:50 is treated as the first bar of AM1. Downstream experiments that derive window events from OpenTime will have a 1-minute boundary offset relative to this experiment.'"
  },
  {
    "id": "F06",
    "severity": "Minor",
    "title": "evaluate_readiness silently conflates data-loading failures with coverage failures",
    "evidence": "run_experiment.py:419: `family_pass = (len(subset) == 4 and bool(...))`  — if len(subset) != 4, family_pass is False with no diagnostic output.",
    "impact": "If an instrument's family_summary subset contains 0, 2, or 6 rows (due to a data loading error, a missing segment, or a schema change), evaluate_readiness silently reports MacroFamilyCoveragePass: false for that instrument. The final verdict would be INCONCLUSIVE or AGAINST based on a data-loading problem rather than actual coverage. No warning, no exception, no distinction from a genuine coverage failure in the output. In the current run this is not triggered (all instruments produce exactly 4 rows), but a future re-run with a missing file would produce a misleading verdict.",
    "fix": "Add an assertion or explicit warning inside the loop: `if len(subset) != 4: raise ValueError(f'{instrument}: expected 4 family×segment rows, got {len(subset)}')`. This is a one-line change that turns a silent failure into a loud, actionable error."
  },
  {
    "id": "F07",
    "severity": "Minor",
    "title": "cost_schema_summary uses union of all instrument schemas — schema differences across instruments would yield a false 'available' signal",
    "evidence": "run_experiment.py:396–407: `schema_columns.update(...)` iterates all_input_paths spanning all four instruments and unions their column names. The result is used for a single cost_data_availability table shared across all instruments.",
    "impact": "If one instrument's Parquet file were sourced from a different data provider that includes a 'Spread' column, cost_schema_summary would report AvailableInTimeBarSchema: true for that field, even though only one of four instruments carries it. The single shared cost_data_availability table would silently assert uniform availability. In the current run, all cost fields are absent from all four files, so the output is correct — but the logic is fragile for future data updates. The risk is that an incorrect 'available' verdict for a cost field would cause downstream experiments to skip building a proxy scenario for that instrument, leading to inconsistent cost assumptions across instruments.",
    "fix": "Compute cost schema availability per instrument and write a per-instrument cost_data_availability table (or flag any instrument-level discrepancy). A single cross-instrument union should only be used if the intent is to detect presence of a field in any instrument."
  },
  {
    "id": "F08",
    "severity": "Minor",
    "title": "load_analysis_timebars performs two Parquet scans — one for row count, one for data collection",
    "evidence": "run_experiment.py:107–113: `scan.select(pl.len()).collect()` is called to get total_rows, then `scan.slice(0, analysis_rows).collect()` is called on the same LazyFrame to materialize the analysis data.",
    "impact": "The Parquet files are scanned twice end-to-end: once to count rows and once to collect data. For the current dataset sizes (1.2–1.6 M rows per instrument, 4 instruments) this adds measurable I/O without affecting correctness. This is not a blocking issue for a one-shot data-readiness script, but it is an unnecessary cost if the experiment is re-run iteratively during development or validation.",
    "fix": "Collect once: `full_df = scan.collect(); total_rows = len(full_df); analysis_df = full_df.slice(0, int(total_rows * ANALYSIS_FRACTION))`. This eliminates the double scan and simplifies the function."
  }
]
```

---

## Summary

EXP-012 is structurally sound: holdout exclusion is correctly enforced, the full date-by-window grid prevents zero-observation windows from being dropped from denominators, the timestamp assumption is declared explicitly, and cost-field absence is verified against actual Parquet schemas. The governance artefacts are complete and the code produces internally consistent outputs.

Three issues warrant attention before EXP-013 is scoped. First, the INCONCLUSIVE verdict is correct per the scope rules but the experiment produces no decision record for what happens downstream — USTEC's eligibility for EXP-013 through EXP-028 is left unresolved. Second, BTCUSD's 11-point train-test coverage gap (88% vs 99.5%) is the most notable data-quality signal in the results and is entirely absent from the narrative output; it will cause train-test distributional differences in EXP-013 that researchers may misread as signal non-stationarity. Third, individual PM windows for XAUUSD and USTEC fall below the 80% threshold despite the family-level aggregation passing — EXP-013 PM-window statistics for these instruments will be structurally underpowered relative to the declared threshold.

The five minor findings (active session resolution, CloseTime boundary documentation, silent verdict conflation, union-schema cost check, and double Parquet scan) are low-risk but the first two carry forward as undocumented assumptions into every subsequent macro-window experiment.
