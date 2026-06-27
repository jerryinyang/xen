# Analysis Plan: Experiment EXP-005

## Objective

Determine whether the frozen Phase 001 gate stack detects a predeclared imperfect realistic candidate when that candidate carries a known expected net edge near each domain's EXP-003 gate-stack MDE.

## Methodology

### Step 1: Dependency and Freeze Gate

- **Method**: Require EXP-001 `run_metadata.json` `overall_status == "PASS"`; require EXP-003 `run_metadata.json` `overall_status == "COMPLETE"` (EXP-003 is a measurement run and never records `"PASS"`) plus an artifact gate that loads EXP-003 `mde_summary.csv` and confirms finite gate-stack MDE at `alpha=0.05` per domain; and require a pre-execution confirmation record for `D-nearMDE`, `D-lenientL5`, and `D-loss` from `design.md` before any EXP-005 measurement is produced. The per-domain target grid is built from the artifact MDE (× {0.5, 1.0, 1.5, 2.0}), not hardcoded.
- **Why this method**: EXP-005 is the Phase 002 spine and explicitly depends on the validated substrate and calibrated MDE map.
- **Simpler alternative considered**: Proceeding directly to simulation would be simpler, but would violate the Phase 002 predeclaration freeze.
- **Assumptions**: The EXP-001 PASS verdict and the EXP-003 finite-MDE artifact are the approved dependency signals (EXP-003's overall status is `"COMPLETE"`, not `"PASS"`); a domain whose gate MDE is missing or non-finite is reported inconclusive rather than forced to a verdict.
- **Expected output**: Dependency and freeze status in `run_metadata.json`.

### Step 2: Holdout-Safe Domain Construction

- **Method**: Use the existing `xen.referee_calibration` loading and domain helpers to load only the first 70% chronological analysis slice, then build 5m, 1h, and 4h domains.
- **Why this method**: It preserves comparability with EXP-003 and keeps the final 30% global holdout untouched.
- **Simpler alternative considered**: Loading full data then slicing would be shorter code, but governance forbids materializing the holdout.
- **Assumptions**: `CloseTime` ordering is authoritative; 1h and 4h use `min_coverage=0.90`; the domain split inherits the 1-minute train/test timestamp.
- **Expected output**: `analysis_metadata.csv` with source rows, analysis rows, train/test rows, and domain row counts.

### Step 3: Realistic Candidate Sanity Check

- **Method**: Generate the predeclared latent state and noisy candidate for every draw, then verify active rate, active match rate, up/down episode counts, and expected-edge calibration.
- **Why this method**: The design requires the candidate to be neither oracle-adjacent nor too noisy; these diagnostics make that precondition measurable.
- **Simpler alternative considered**: Trusting the RNG parameters without reporting diagnostics would hide implementation mistakes.
- **Assumptions**: The seeded Bernoulli construction is independent of market returns under null draws; expected-edge calibration is closed-form before sampling noise.
- **Expected output**: `candidate_sanity.csv` and candidate-construction fields in `run_metadata.json`.

### Step 4: Paired Null and Positive Verdict Evaluation

- **Method**: Evaluate the minimal baseline and gate stack on paired null and positive draws via the frozen `evaluate_referees` harness. Null draws use unmodified and bar-permuted real returns with a return-independent candidate. Positive draws plant latent-state drift `delta_bps = (target + p_active·cost_bps)/(p_active·(2·q_match−1))`, computed per instrument with the frozen `cost_bps_for` and injected in fractional units (`delta_bps/10_000`), so the noisy candidate's expected all-eligible-row net edge equals the target grid value under the harness per-active-bar cost model.
- **Why this method**: Paired draws reduce comparison noise and directly measure FPR and TPR on the candidate class named by the checkpoint.
- **Simpler alternative considered**: One positive edge per domain would test only a point and would not reveal whether failures are near-boundary or broad.
- **Assumptions**: Wilson intervals are appropriate for pass/reject rates; block-bootstrap CIs are computed on real-price strategy returns with block length estimated on train only.
- **Expected output**: `realistic_candidate_draws.csv`, `fpr_summary.csv`, and `tpr_summary.csv`.

### Step 5: Detection-Floor Classification

- **Method**: For each domain, classify the gate stack at `alpha0=0.05` using the predeclared FPR and TPR criteria. Report pooled-domain verdicts as headline and per-instrument verdicts as a masking check where precision permits.
- **Why this method**: EXP-003 MDEs were pooled over instruments, so pooled-domain detection is the comparable headline; per-instrument rows test the design's pooling caveat.
- **Simpler alternative considered**: Per-instrument-only classification would answer a different question than the EXP-003 map.
- **Assumptions**: A cell with insufficient Wilson precision is inconclusive, not negative evidence.
- **Expected output**: `detection_summary.csv` and `per_instrument_detection.csv`.

## Visualisations

1. TPR by target-edge multiplier and domain at `alpha=0.05` - shows whether detection crosses 0.80 at `1.0 x` MDE.
2. FPR by domain/referee at `alpha=0.05` - shows whether the gate holds the false-positive constraint.
3. Candidate active-rate and match-rate diagnostics by domain/instrument - verifies the realistic-candidate construction.
4. Pooled vs per-instrument TPR heatmap - shows whether pooled success masks weak instruments.
5. Effect CI distribution at the `1.0 x` MDE grid point - shows whether detection failures are near-boundary or far below threshold.

## Interpretation Guide

- If pooled FPR is `<= 0.05` and pooled TPR is `>= 0.80` at `1.0 x` MDE with usable precision, the EXP-003 map is supported as an honest detection floor for that domain.
- If pooled FPR is controlled but pooled TPR is below `0.80` at `1.0 x` MDE with usable precision, the frozen gate is structurally blind to this realistic candidate class on that domain.
- If only the `1.5 x` or `2.0 x` grid points pass, report the domain as requiring a higher realistic-candidate edge than the oracle-calibrated MDE.
- If per-instrument cells disagree with a pooled pass, report the pooled verdict as headline and the instrument disagreement as a masking caveat.
- If candidate sanity or Wilson precision fails, classify the affected cell as inconclusive.

## Complexity Check

- Statistical tests: 4 / 4
- Visualisations: 5 / 5
- New modules: 1 / 1 maximum; prefer experiment-local helpers

## Data-View Comparison Considerations

### Cross-View Alignment

- The only data views are time-bar domains derived from the first-70% 1-minute analysis slice.
- Domains inherit the shared 1-minute `CloseTime` train/test boundary.
- No chart-type events are in scope, so `SourceCloseTime` alignment is not used.

### Implementation Safety and Performance

- Use lazy Polars scans, project required columns, compute row counts, and slice to the first 70% before collection.
- Use `tqdm` over instrument/domain/draw loops; this experiment has many bootstrap verdicts.
- Keep per-bar simulated returns out of persisted outputs unless required for audit sampling; store verdict-level rows and bounded diagnostics.
- Do not optimize by changing sample membership, temporal ordering, draw counts, candidate parameters, denominators, or referee logic.
- Bootstrap block length is estimated on train returns only and reused for the corresponding test verdict.
- The realistic-candidate construction lives in an experiment-local helper under `EXP-005/code/`; `xen.referee_calibration` is imported and reused unchanged (no edit to the frozen harness, per design D-reuse).

### Real-Price Outcome Discipline

- Compute strategy returns from real domain `Close` returns plus the predeclared known-positive drift.
- No Heiken Ashi, Renko, Line Break, or synthetic chart prices are in scope.
- Costs use frozen `ROUND_TRIP_COST_BPS` from `xen.referee_calibration`.

### Denominators and Zero-Baseline Behavior

- FPR and TPR are absolute pass-rate proportions over draw verdict counts; report Wilson intervals and do not compute percentage improvement from a zero baseline.
- Active rate uses `active_bars / eligible_rows`; if active bars are zero for any draw, the draw is invalid and the cell is inconclusive.
- MDE-related comparisons use absolute bps and grid multipliers, not relative percentage gains where the baseline is zero or missing.
