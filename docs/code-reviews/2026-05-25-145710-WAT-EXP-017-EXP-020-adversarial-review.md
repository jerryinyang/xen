# Adversarial Review: EXP-017 through EXP-020

**Date:** 2026-05-25 14:57:10 WAT
**Scope:** Stage-4 artefacts and result tables for EXP-017, EXP-018, EXP-019, EXP-020
**Phase context:** `2026-05-23-003-ict-one-setup-timebar-validation/design.md`
**Active lenses:** statistical methodology > scope-fidelity > reproducibility (empirical-study lens; the four artefacts implement hypothesis tests against an active research design)

This review reads the scope, analysis plan, implementation code, pre-execution
governance, and numerical result summaries for each experiment, plus the shared
`python/src/ict_timebar.py` helpers. It is grounded in those files. Where a
finding cites a line number, that line was inspected directly.

---

```json
[
  {
    "id": "F01",
    "severity": "Critical",
    "title": "EXP-019 verdict declares FOR despite confidence intervals that span zero on every instrument",
    "evidence": "results/numerical_summary.txt: EURUSD return_diff=0.252 CI=[-7.542, 7.186]; XAUUSD return_diff=0.630 CI=[-16.675, 16.508]; BTCUSD return_diff=1.477 CI=[-4.046, 9.320]; USTEC return_diff=18.153 CI=[-4.626, 58.993]. Bootstrap CIs include zero for all four instruments on the primary return outcome; three of four also include zero for matched MAE. Yet `evaluate_verdict` (code/run_experiment.py:450-519) reports `FOR (4/4 instruments)`.",
    "impact": "The 'FOR' verdict promotes the H3 swing-break variant to downstream experiments (EXP-021, EXP-022, ablation) on the basis of point estimates only. With CIs 13R-63R wide that all include zero, there is no statistical support for the claim. Subsequent component-ablation and full-model experiments will inherit an unsubstantiated baseline, and the phase will conclude that H3 'works' when the data does not show it.",
    "fix": "Require the success criterion to test interval-based evidence (e.g., CI95 strictly above 0 or above the 0.25R threshold) before flipping `ReturnCriterionMet` / `MAECriterionMet` to True. The scope text says 'improves by >= 0.25R'; that should be implemented as 'bootstrap CI95 low >= 0.25R', not 'point estimate >= 0.25R'. Re-run interpretation; the honest verdict on these numbers is INCONCLUSIVE at best."
  },
  {
    "id": "F02",
    "severity": "Critical",
    "title": "EXP-019 measures MAE by paired *mean* but the scope and analysis plan demand *median*",
    "evidence": "Scope: 'lowers median 60-minute MAE by >= 0.25R on at least 3 instruments' (scope.md:24). Analysis plan: 'lowers median 60-minute MAE' (analysis-plan.md:42). Implementation uses `paired_bootstrap_diff` which computes `point = float(np.mean(diffs))` (code/run_experiment.py:343). Same function is used for the MAE call at code/run_experiment.py:415-419.",
    "impact": "MAE distributions are heavy-tailed; mean is dominated by a small number of large adverse excursions, so the reported MAE improvement (e.g., USTEC mae_impr=35.074, XAUUSD=4.122) is not a median statement and is not what the scope predeclared. The verdict logic therefore evaluates a different metric than the criterion, producing a false 'pass' on MAE for at least USTEC and BTCUSD.",
    "fix": "Add a median variant of `paired_bootstrap_diff` (or parameterise it on `stat_fn`) and call the median version for MAE comparisons in EXP-019. Re-run and re-interpret. If only the mean variant is run, the scope criterion is not actually tested."
  },
  {
    "id": "F03",
    "severity": "Major",
    "title": "EXP-018 'sweep vs displacement' comparison is paired on a self-selected subset, not against sweep-only outcomes",
    "evidence": "`detect_confirmed_entries` (code/run_experiment.py:182-238) only emits SweepClose/DisplacementClose/NextOpen entry rows when `confirmation['Confirmed']` is True. `compute_primary_effects` (code/run_experiment.py:332-398) then paired-bootstraps DisplacementClose vs SweepClose on exactly those rows. The scope question is 'Does adding deterministic displacement improve sweep-only outcomes?' (scope.md:8).",
    "impact": "The actual comparison measures the *delay penalty* of waiting N bars to enter, conditional on a displacement eventually appearing. It does not measure whether the displacement filter itself selects better sweeps. A null or negative paired delta (which is exactly what the results show across all four instruments) is consistent with either 'displacement adds no information' or 'displacement helps, but waiting hurts'; the design cannot distinguish them. The pre-execution review marked 'Statistical method | PASS' without flagging this.",
    "fix": "Either (a) reframe the scope/criteria to explicitly state the question is delay-cost on displacement-confirmed sweeps and reword the report accordingly, or (b) add an unpaired baseline that compares displacement-confirmed sweep outcomes (DisplacementClose proxy) against the full EXP-015 sweep-close population, with the retention cost reported alongside (as EXP-017 does). Choose one — the current write-up implies (b) but only computes (a)."
  },
  {
    "id": "F04",
    "severity": "Major",
    "title": "EXP-019 retention floor counts unmatched swing-break events but the analysis uses only the matched subset",
    "evidence": "`summarize_counts` (code/run_experiment.py:287-328) defines `SwingBreakN` and `EventFloorMet = swing_n >= 50` from raw detections. `build_baseline_comparison` (code/run_experiment.py:358-388) does an `inner` join on sweep key, dropping any swing-break event whose sweep did not also confirm displacement in EXP-018. `compute_primary_effects` operates on the matched `comparison` frame (code/run_experiment.py:400-403). `evaluate_verdict` reads `EventFloorMet` from `summarize_counts` rather than `MatchedN` from `compute_primary_effects` (code/run_experiment.py:456-461).",
    "impact": "An instrument can show `swing_n >= 50` and pass the floor, while the actual paired bootstrap uses far fewer matched pairs. The scope criterion is '>= 50 *confirmed swing-break events* per train/test segment' — but the inference is over matched-pair events, not the raw count. The reported `matched=77/112/81/132` happens to be >= 50 here, but the floor check itself does not enforce that. This is fragile and will silently break when EXP-018 confirmation rates drop.",
    "fix": "Compute the retention floor from `MatchedN` (the actual sample feeding the bootstrap), not from raw `SwingBreakN`. Add an assertion that `MatchedN >= MIN_CONFIRMED_EVENTS` before `ReturnCriterionMet` can be True."
  },
  {
    "id": "F05",
    "severity": "Major",
    "title": "EXP-019 swing detection cannot use swings from the Train segment when scanning Test sweeps",
    "evidence": "`_latest_usable_swing` filters `swings['Segment'] == segment` (code/run_experiment.py:166-173) and `find_swing_break_for_sweep` halts when `candidate['Segment'] != segment` (code/run_experiment.py:192-193). Segment is assigned to a swing at its `UsableIndex` (code/run_experiment.py:140/153).",
    "impact": "(1) At the start of the Test segment, no usable swing exists for the first ~minutes/hours of Test, so early-Test sweeps are systematically denied confirmation. This biases Train vs Test comparability of detection rates. (2) A swing whose pivot is in Train and whose confirmation is in Test could be considered Test-segment in the labelling — coupled with the segment-cut on candidates, the rule is inconsistent. (3) The segmentation barrier was never declared in the scope or analysis plan; it is an undocumented analytical choice. In a production setting, the algorithm would happily use any prior swing.",
    "fix": "Either remove the segment filter in `_latest_usable_swing` (use any prior usable swing regardless of which segment it formed in) and document the choice in scope, or explicitly carry a 'warm-up swings from prior data' window. Re-run if changed. If the segmentation barrier is intentional, document it in scope.md and justify why production parity is not required."
  },
  {
    "id": "F06",
    "severity": "Major",
    "title": "EXP-020 'reproducibility' check is a same-process rerun and cannot detect real reproducibility risks",
    "evidence": "`verify_reproducibility` (code/run_experiment.py:291-317) calls `detect_fvgs` a second time on the same in-memory `bars_by_instrument` and compares SHA-256 digests of the FVG identity columns. Since `detect_fvgs` is deterministic NumPy on identical inputs, the digests will trivially match.",
    "impact": "The 'FOR' verdict on EXP-020 is largely driven by `Reproducible == True` for all four instruments (run_experiment.py:368-372, 396-406). That check guarantees-passes by construction; it does not exercise the cases that matter for EXP-021's claim of 'stable timestamps' — different Python/NumPy versions, different file ordering, partial recomputation, persisted-then-reloaded datasets, parallel chunking. The scope intent ('EXP-021 depends on deterministic IFVG events') is not actually validated.",
    "fix": "Replace the in-process rerun with at least one meaningful invariance check: (a) shuffle the input row order before recompute and assert that post-sort detection matches, (b) cast `Close` through pandas->parquet->polars round-trip before recompute, or (c) compare against an independently-implemented spot-check on a small subset. At minimum, document that the current check is a smoke test for code-path determinism, not for cross-environment reproducibility."
  },
  {
    "id": "F07",
    "severity": "Major",
    "title": "EXP-020 sample-size floor is so low relative to detected counts that the readiness gate is meaningless",
    "evidence": "Floors: `MIN_FVG_PER_SEGMENT = 100`, `MIN_IFVG_PER_SEGMENT = 50` (code/run_experiment.py:40-41). Observed counts per instrument/segment from results/numerical_summary.txt are in the 60k-195k range for FVGs and 50k-165k for IFVGs (e.g., EURUSD Train FVG=167956, IFVG=142897; ratio 85%).",
    "impact": "Two problems. (1) The scope floor is three orders of magnitude smaller than observed counts; the gate cannot fail and therefore validates nothing about sample adequacy for EXP-021. (2) IFVG rate of ~85% within a 120-bar window suggests that on 1-minute time bars, virtually every gap-formation event closes back through within ~2 hours. Under that base rate, 'IFVG inversion' is close to a statistical tautology rather than a discriminating event — undermining the spec's role for IFVG as a selective confirmation signal in EXP-021.",
    "fix": "(a) Tighten the floors to reflect what EXP-021 actually needs after sub-segmentation (e.g., per-day, per-macro-window). (b) Report the IFVG base rate (IFVG_N / FVG_N) per instrument/segment in the result tables and discuss whether the high rate calls for parameter changes to the size filter or lifecycle window before proceeding to EXP-021. Without this, EXP-021 will inherit a degenerate event class."
  },
  {
    "id": "F08",
    "severity": "Major",
    "title": "EXP-017 verdict logic over-uses the INCONCLUSIVE 'wide positive' escape on essentially null evidence",
    "evidence": "`evaluate_verdict` flags an instrument as `WidePositiveSignal` when point estimate > 0 and CI does not clear the threshold (code/run_experiment.py:429-444), and downgrades AGAINST to INCONCLUSIVE if any instrument is wide-positive (code/run_experiment.py:462-465). Result: with USTEC mae_impr=0.185 (point estimate well below 0.25R threshold, CI=[-0.672, 0.591]), the wide-positive trigger fires and the verdict becomes INCONCLUSIVE rather than AGAINST.",
    "impact": "All four instruments showed negative or near-zero point estimates on Hit1R and small MAE improvements with CIs straddling zero. The honest conclusion under the predeclared 'Evidence FOR / AGAINST' criteria is AGAINST. The logic creates a one-sided ratchet: any positive blip on any instrument blocks an AGAINST verdict and protects the hypothesis from refutation.",
    "fix": "Restrict 'wide positive' to cases where the point estimate is at least somewhere in the neighbourhood of the threshold (e.g., >= 0.5 * threshold) and the CI overlaps the threshold. As written, the rule fires on noise and biases the phase against negative findings, which is the opposite of the design's stated goal of being willing to document neutral or harmful components."
  },
  {
    "id": "F09",
    "severity": "Major",
    "title": "EXP-018 verdict logic similarly escapes to INCONCLUSIVE on train-only positive instruments while test-side evidence is clearly negative",
    "evidence": "`evaluate_verdict` (code/run_experiment.py:401-448): `if floor_count < 3 or train_only > 0: INCONCLUSIVE`. Results show 4/4 instruments with negative test-segment return_diff and three with hit_diff CIs fully below zero — strong refutation evidence — but the verdict is INCONCLUSIVE because some Train rows met the (mis-specified, see F03) criterion.",
    "impact": "The rule converts 'train-positive, test-negative' into INCONCLUSIVE rather than treating it as the canonical sign of an overfit / unstable filter (which should weigh against H3). Combined with F08, the Phase-003 verdict machinery has a systematic anti-AGAINST bias. The design.md explicitly states 'Negative component results change interpretation and priority; they do not justify post-hoc deletion' — but the verdict rules make it hard to record an unambiguous negative.",
    "fix": "Allow AGAINST when test-segment effect sizes are net-negative with CI excluding the improvement threshold on >= 3 instruments, regardless of train-segment behaviour. Train-positive / test-negative should map to AGAINST (overfit), not INCONCLUSIVE."
  },
  {
    "id": "F10",
    "severity": "Minor",
    "title": "EXP-018 and EXP-019 invoke `add_ny_time_features` despite no NY/macro logic being used downstream",
    "evidence": "`load_instrument_bars` in EXP-018 calls `add_bar_diagnostics(add_ny_time_features(loaded.frame, train_end))` (run_experiment.py:94). Same in EXP-019 (run_experiment.py:112). Neither script reads `NYDate`, `NYMinuteOfDay`, `MacroWindow`, or `WindowFamily` — sweep keys are joined from EXP-015's already-labelled CSV. EXP-020's pre-execution review explicitly notes it 'avoids unused NY/macro-window feature generation' (governance/pre-execution-review.md:33).",
    "impact": "Wasted CPU/memory at experiment start, and an inconsistency in code conventions across sibling experiments that may confuse future audit. Not a correctness issue.",
    "fix": "Replace `add_ny_time_features(...)` calls in EXP-018 and EXP-019 with a minimal Segment-only labelling (as EXP-020 does, run_experiment.py:90-100). Drop unused columns before the `.to_pandas()` collect."
  },
  {
    "id": "F11",
    "severity": "Minor",
    "title": "Pre-execution governance reviews for EXP-018/019/020 are markedly thinner than EXP-017 and missed the issues above",
    "evidence": "EXP-017 pre-execution review is ~140 lines with row-by-row code citations including the nested-bootstrap correctness check. EXP-018/019/020 reviews are 50/49/50 lines and contain table rows like 'Statistical method | PASS | Paired bootstrap compares confirmed-event entry proxies against the same sweep-close events' (EXP-018/governance/pre-execution-review.md:32) without engaging with what 'same sweep-close events' actually means for the scope question (F03), without checking the median vs mean discrepancy (F02), and without flagging the verdict-logic asymmetry (F08, F09).",
    "impact": "Stage-4 governance is the project's defined gate against scope drift and stat-method errors. When it produces uniform APPROVE verdicts on three different scripts within minutes, it loses its function as an independent check. The findings in this review (F01-F09) are within scope of governance and should have surfaced before manual execution.",
    "fix": "Treat the EXP-017 review as the template; require Stage-4 reviews to (a) restate the scope's success metric and trace it to a specific line in code, (b) cite at least one numerical sanity check, and (c) include at least one 'tried to falsify' note even when the verdict is APPROVE."
  }
]
```

---

## Summary

The biggest concerns concentrate in EXP-019 and EXP-020, where the FOR
verdicts are produced by criteria that either ignore confidence intervals
(F01), compute a different statistic than the scope predeclared (F02), or
test something the scope did not actually pose (F03, F06, F07).

EXP-017 and EXP-018 are scope-faithful in code, but their verdict-logic
asymmetries (F08, F09) and EXP-018's paired-comparison framing (F03)
combine to make a clean AGAINST verdict almost impossible. Given the
phase design.md's explicit instruction to allow negative component
findings, this asymmetry is a meaningful threat to the phase's
falsification discipline.

The Stage-4 reviews for EXP-018/019/020 (F11) did not catch any of these
issues and should be strengthened before any downstream experiment
(EXP-021+) reuses these artefacts as baselines.
