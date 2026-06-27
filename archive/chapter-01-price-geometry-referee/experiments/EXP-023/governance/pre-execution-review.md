# EXP-023 Pre-Execution Governance Review

**Stage:** 4 (pre-execution, consolidated pipeline governance)
**Date:** 2026-06-08
**Review type:** Focused re-review (prior verdict was REVISE with 7 issues; revision implemented).
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`,
`code/run_experiment.py`, `StrategyHost/AvwapBounceModel.cs`,
`StrategyHost/DonchianBreakoutModel.cs`, `StrategyHost/TimeBarParquetReader.cs`,
`StrategyHost/StrategyHostParityExporter.cs`,
`StrategyHost/StrategyRunParquetWriter.cs`, `Xen.cs`,
`python/src/xen/signals/ingestion.py`.

```text
VERDICT: APPROVE
```

## Resolution of the 7 prior REVISE issues

1. **Dependency/suite validation is now value-based, not presence-only.**
   `check_dependencies()` validates the scoped gate values via `_expect(...)`:
   EXP-020 `SUPPORTED_FULL` + `invariants_ok` + `invariant_failure_count == 0` +
   `determinism_pass` + `holdout_violation_count == 0` + ready domains
   `{5m,1h,4h}`; EXP-021/022 `SUPPORTED` + reportable domains; VAL-002 `PASS` +
   `holdout_fence_ok` + `cells_screened == 12`; EXP-019 reference
   `decision_status == CONFIRMED`, `reference_family == donchian_20`, lookback 20;
   registry `CF-AVWAP-001/HYP-004`+`EXP-023`+frozen-suite section; family spec
   HYP-004 strategy-screen path (`run_experiment.py` 293-343). The hardcoded
   `STRICT/LOOSE/INCREMENTAL_MDE_BPS` constants are gone; `load_suite_settings()`
   derives strict (EXP-003), ratified-loose τ/MDE (EXP-012 adoption +
   fresh-MDE cross-check), and revised-incremental MDE (EXP-018) from artifacts
   and blocks on any missing/non-PASS/non-finite/incomplete-domain case
   (346-444). **Satisfiability verified** against the present artifacts: strict
   1/4/12, loose τ 0.375/0.375/1.5 with MDE 0.5/2/8 (adoption == fresh, no
   mismatch), incremental 12/16/32 with `failing_cells == 0` and
   `SUPPORTED_WITH_UNDERPOWERED_CELLS` accepted by the `startswith("SUPPORTED")`
   check — the gate populates all three domains and does not spuriously block.

2. **Partial run admission can no longer yield a market verdict.**
   `_assert_admission_floor()` adds a blocker unless all 12 cells and all 4
   instruments per domain are admitted (744-752); `overall_status()` returns
   `BLOCKED` on `blockers.any or len(admitted) != expected_cells`, and
   `INCONCLUSIVE` when reportable cells `!= 12` (1207-1221). Missing dirs, load
   errors, empty positions, missing `analysis_end_utc`, contract violations, fence
   violations, and same-feed mismatch each add a blocker (661-722). No
   `SUPPORTED_*`/`REFUTED` is reachable from a partial set.

3. **Same-feed reference identity is verified, not just timestamp alignment.**
   `_same_feed_check()` requires identical height, identical `SourceCloseTime`
   sequence, and row-by-row `RealOpen/High/Low/Close` agreement within
   `atol=1e-9/rtol=1e-12` (604-633); admission requires `same_feed_ok` (720).
   Reference metadata is validated (`_validate_run_metadata` for the reference
   strategy incl. lookback 20, domain, coverage, `analysis_end_utc`),
   candidate/reference `analysis_end_utc` equality is asserted (688-690), and
   duplicate `SourceCloseTime` is rejected in `_validate_position_contract`
   (532-533). The incremental aligner then left-joins on the already-verified
   identical timestamps and requires `n_missing == 0` (926-943).

4. **Fixed-Parquet holdout-load risk closed on both sides.**
   C# `TimeBarParquetReader.ReadBefore()` calls `AssertPreSlicedAnalysisInput()`
   and throws unless the filename carries a first-70% marker
   (`analysis70`/`analysis_slice`/`first70`), so the replay/parity reader cannot
   open a full source file (`TimeBarParquetReader.cs` 16, 60-70). The Python smoke
   independently requires the recorded `input_path` to carry the same marker and
   FAILs+blocks otherwise (`run_experiment.py` 803-807, `_is_analysis_slice_path`
   265-268). The robot live/backtest path additionally fences via
   `HoldoutFence.AssertCanEmit` in `StrategyRunParquetWriter.Append` (51-64).

5. **Missing/absent AVWAP smoke now blocks.**
   Every `PENDING` branch of `run_avwap_smoke()` adds a blocker (no parity export,
   missing `export_metadata.json`, missing source parquet, missing per-domain
   parity CSV, and the aggregate PENDING), alongside the FAIL branches
   (775-826). With Stage-4 `BLOCKED`-on-any-blocker semantics, an unran or
   incomplete transcription smoke prevents a market verdict.

6. **Screen status now respects metric-book finiteness.**
   `validate_metric_book()` blocks on wrong row count and on any non-finite
   `model_net_bps`, `raw_return_bps`, `model_robust_ratio`, `raw_robust_ratio`
   per cell (1110-1119), invoked before status resolution (1441).
   `lifetime_expectancy_bps` is correctly excluded from the mandatory-finite set
   (legitimately null when a cell has no completed target move), matching the
   scope's separate completed-move denominator.

7. **Deterministic trade-pairing tie-break implemented.**
   C# emits a monotonic `TradeSequence` (`NextTradeSequence()`,
   `AvwapBounceModel.cs` 483/497/538) written as a `long` column to
   `trade_blotter.parquet` (`StrategyRunParquetWriter.cs` 152, 168).
   `_entry_exit_pairs()` sorts by `[SourceCloseTime, TradeSequence, _file_order]`
   when `TradeSequence` is present and `[SourceCloseTime, _file_order]` otherwise,
   where `_file_order` is the preserved Parquet row order
   (`run_experiment.py` 1020-1040). Same-bar exit-then-reopen is ordered
   deterministically because completion (`MaybeCompletePosition`) sets
   `_position = 0` before the bounce handler can enter, so the exit always
   receives the lower sequence.

## Other governance checks (all pass)

- **Holdout discipline:** no code path loads the final 30%; only holdout-fenced
  cTrader run dirs are read and the fence is re-asserted; the smoke requires a
  pre-sliced first-70% file.
- **Real-price / no-regeneration discipline:** all returns derive from emitted
  `RealClose`; Python ingests and validates only and never regenerates the
  candidate signal for screening — `xen.avwap` runs solely in the explicitly
  scoped transcription smoke.
- **Timestamp alignment:** `SourceCloseTime` is the temporal authority
  throughout; same-feed and incremental alignment join by timestamp, never bar
  index.
- **Ingestion contract:** the Step 3/4 calls match
  `xen.signals.ingestion` signatures; `screen_emitted_positions(..., train_end_utc=None)`
  uses the frozen referee 70% chronological row split (VAL-002 path), and
  `returns_and_positions` returns the `aligned` frame with the `CloseTime`
  column the incremental aligner consumes.
- **Scope/plan/code consistency & budget:** 4 statistical procedures, 5 plots, 3
  new modules — within the scoped budget; the implemented plots now include
  incremental effects + incremental floors (`plot_effect_forest`) and the
  raw/traditional cumulative comparison (`plot_model_vs_raw`).
- **Phase alignment:** EXP-023 is the planned terminal screen of the Phase 004
  baseline chain (checkpoint `design.md` §5). The PROCEED_TO_SCREEN criterion
  (§8) is met — EXP-020 `SUPPORTED_FULL`, EXP-021 benchmarked bounce reaction
  `SUPPORTED` against matched controls, EXP-022 lifetime `SUPPORTED`. No phase
  misalignment to flag.
- **Static build:** prior review recorded clean Python byte-compile, `ruff`, and
  `dotnet build`; this re-review changed no build surface.

## Residual Info notes (non-blocking; for the Stage-5 audit)

- No automated unit test asserts `_entry_exit_pairs` behavior on a synthetic
  same-bar close/reopen sequence. The determinism is structurally guaranteed
  (preserved Parquet row order + monotonic `TradeSequence`), so this is an audit
  recommendation, not a pre-execution blocker.
- `overall_status()` collapses several distinct failure modes to `BLOCKED` via
  the blocker channel; this is faithful fail-closed behavior, and
  `run_metadata.json.blockers` records each reason so the distinction remains
  traceable in the results.

The harness now fails closed on dependency/status mismatch, incomplete run
admission, same-feed reference mismatch, missing/failed smoke validation,
metric-book non-finiteness, and the fixed-Parquet holdout-load risk. The
implementation is approved for the manual execution gate.

---

## Post-execution addendum (2026-06-08): focused code REVISE

The approved code was executed at the manual gate. It produced
`overall_status=BLOCKED` from 12 identical blockers: `model_robust_ratio`
non-finite in every cell. Diagnosis from the emitted results:

- The screen ran completely: 12/12 cells admitted, holdout fence OK, same-feed
  OK, and the **C# AVWAP transcription smoke PASSED on all 3 domains** (0 field
  mismatch, `max_abs_price_diff=0.0`, event counts 5978/421/109 identical).
- The suite produced a clean result: `pass_tally = {strict:0, loose:0,
  incremental:0, suite_pass:0, reportable:12}` — i.e. an **Evidence-AGAINST /
  REFUTED** signature, with model net expectancy ~0-to-negative in every cell
  (e.g. BTCUSD/5m −0.74 bps; EURUSD/4h marginally +0.08).
- The block is an artifact of a degenerate descriptive metric, not the data:
  the AVWAP baseline is flat the large majority of bars (e.g. 4,920 entries over
  216,713 rows), so >50% of the model net-return series is exactly 0 →
  `median=0`, `MAD=0` → `model_robust_ratio = mean/MAD = NaN`. The mean/std
  diagnostic (`model_sharpe_diag`) is finite; `raw_robust_ratio` is finite.

```text
VERDICT: REVISE
FAILING_ARTIFACT: python/experiments/EXP-023/code/run_experiment.py
REQUIRED_SKILL: experiment-developer
ISSUES:
- validate_metric_book() over-gates on model_robust_ratio. The scope's gating
  requirement is "finite, non-missing strategy expectancy and raw-return
  risk-adjusted comparison for every reportable cell" (model_net_bps and
  raw_robust_ratio — both finite), and the scope's zero-baseline rule states
  "Any zero denominator is null/non-reportable, never a zero effect." A
  structurally-zero MAD on a sparse position series is exactly that null case
  and must not hard-block the screen. Remove model_robust_ratio from the
  hard-required finiteness set (keep model_net_bps, raw_return_bps,
  raw_robust_ratio); continue recording model_robust_ratio as null where MAD~0.
- The scoped model-vs-raw risk-adjusted comparison (metric book + risk-adjusted
  heatmap) is left vacuous on the model side because the primary robust mean/MAD
  ratio is undefined for the sparse series. Repoint the comparison/heatmap to
  the already-computed, finite mean/std pair (model_sharpe_diag vs
  raw_sharpe_diag), clearly labeled, noting the robust mean/MAD ratio is
  undefined for the mostly-flat position series. No scope amendment required
  (operator selected the minimal, scope-faithful option).
```

This is a metric-implementation defect surfaced at execution, not a data,
dependency, holdout, look-ahead, same-feed, or smoke failure (all of which
passed). After the fix, re-run at the manual gate; the expected resolution is
`REFUTED` (12/12 reportable, 0 suite passes). Then resume at Stage 5 (audit).
